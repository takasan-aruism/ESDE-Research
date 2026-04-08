#!/usr/bin/env python3
"""
ESDE v9.8b — Minimal Introspection (builds on v9.8a Subject Reversal)
======================================================================
GPT 監査メモ ESDE_v9_8_Design_Audit_Memo (Phase v9.8b) に基づく実装。
v9.8a の Subject Reversal の上に、最小の内省機構を乗せる。

目的:
  各 hosted cid が window 末に「前時点の自己」と「現時点の自己」を比較し、
  構造的中立タグ (gain_social, loss_social, gain_stability, ...) を生成する。
  タグは観測のみ。torque / action への feedback はしない。

含むもの (v9.8b 範囲):
  - prev_disposition の保持 (SubjectLayer に追加)
  - window 末での delta 計算
  - 固定閾値による構造的中立タグの生成 (Stage 1: simple fixed thresholds)
  - per_subject CSV への prev/current/delta/tags/state カラム追加
  - introspection_log.csv (window 単位のタグ生成履歴)

含まないもの (v9.8b 範囲外):
  - 個体別移動平均 / relative surprise (Stage 2 予定)
  - 強い感情語 (joy, betrayal, fear, etc.) — v9.9 以降の解釈層
  - 内省タグの torque / action への feedback
  - ghost の内省 (hosted only; ghost は inert 原則維持)
  - 再宿主化 (v9.8c 予定)
  - v9.7 の z-score torque modulation

GPT 監査の三原則 (provisional thresholds の許容条件):
  1. provisional と明記 (コード / ドキュメント / レポート全て)
  2. feedback に使わない (観測のみ)
  3. 結果を見てタグ頻度を報告 (Run 後に必ず分析)

親バージョン: primitive/v98a/v98a_subject_reversal.py
変更箇所:
  - SubjectLayer に prev_disposition, introspection_state, _tag_history 追加
  - SubjectLayer.generate_introspection_tags() メソッド追加
  - SubjectLayer.commit_disposition() メソッド追加 (prev <- current)
  - main loop の window 末で generate_introspection_tags 呼び出し
  - per_subject CSV に prev/current/delta/tags/state_at_window カラム追加
  - introspection_log.csv の新規出力

USAGE:
  # Smoke test (必須、本格 Run の前に)
  python v98b_introspection.py --seed 0 --maturation-windows 5 --tracking-windows 2 --window-steps 100 --tag smoke

  # Run A: 48 seeds × 10 windows
  seq 0 47 | parallel -j24 python v98b_introspection.py --seed {} --tracking-windows 10

  # Run B: 5 seeds × 50 windows
  seq 0 4 | parallel -j5 python v98b_introspection.py --seed {} --tracking-windows 50 --tag long
"""

import sys, math, time, json, csv, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline" / "v43"
_V41_DIR = _V43_DIR.parent / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V82_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from esde_v82_engine import (V82Engine, V82EncapsulationParams, V82_N,
                              find_islands_sets)
from v19g_canon import BASE_PARAMS, BIAS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


# ================================================================
# CONSTANTS
# ================================================================
ATTENTION_DECAY = 0.99
FAMILIARITY_DECAY = 0.998
EPS = 1e-6
CONVERGENCE_THRESHOLD = 0.3
N_REPRESENTATIVES = 8

# Ghost retention limit.
# This is a PROVISIONAL engineering value for memory/runtime control.
# It is NOT a theoretical claim. v9.8a observes ghost duration distribution
# and the value will be revisited based on data.
GHOST_TTL = 10

# ─────────────────────────────────────────────────────────────────
# Introspection thresholds (v9.8b, Stage 1)
# ─────────────────────────────────────────────────────────────────
# PROVISIONAL ENGINEERING VALUES for observational tagging only.
# These are NOT truth values about "meaningful change".
# They are the initial marker-detection thresholds for the first observation.
#
# Rules (GPT audit):
#   1. provisional — subject to revision after v9.8b output review
#   2. observational only — NEVER fed back into torque / action
#   3. tag frequency will be reported; if distribution is degenerate
#      (too sparse / too dense / single-axis biased), Stage 2 moves to
#      individual moving-average sensitivity
#
# Rationale:
#   social / stability / spread are disposition values in [0, 1].
#   |Δ| > 0.1 = 10% of full scale. Larger than noise, not extreme.
#   familiarity is in [0, ~120] range with unit scale. Absolute |Δ| > 2.0
#   picks up changes of "about one additional contact worth of memory".
INTROSPECTION_THRESHOLD_SOCIAL = 0.1
INTROSPECTION_THRESHOLD_STABILITY = 0.1
INTROSPECTION_THRESHOLD_SPREAD = 0.1
INTROSPECTION_THRESHOLD_FAMILIARITY = 2.0


# ================================================================
# TORUS
# ================================================================
def build_torus_substrate(N):
    side = int(math.ceil(math.sqrt(N)))
    adj = {}
    for i in range(N):
        r, c = i // side, i % side
        nbs = []
        nbs.append(((r - 1) % side) * side + c)
        nbs.append(((r + 1) % side) * side + c)
        nbs.append(r * side + ((c - 1) % side))
        nbs.append(r * side + ((c + 1) % side))
        adj[i] = [nb for nb in nbs if nb < N]
    return adj


# ================================================================
# SUBJECT LAYER  (v9.8a 主役: 旧 CognitiveLayer の置き換え)
# ================================================================
class SubjectLayer:
    """
    認知層の主体管理。

    cognitive_id (cid) を主キーとし、label_id (lid) は
    キャラクターが現在宿っている宿主の参照として扱う。

    Lifecycle:
        birth(lid) -> 新 cid 発番、current_lid[cid] = lid
        detach(lid) -> current_lid[cid] = None (ghost 化)、cog データは保持
        reap_ghosts() -> TTL 超過した ghost cid を完全削除

    Ghost 状態の cid は inert:
        - update_phi/update_attention/update_familiarity は呼ばれない
        - torque 影響なし (元々この層からは torque を出さない)
        - ただし他の hosted cid の familiarity dict には残る
          (= 死んだ人を覚えている)

    旧 CognitiveLayer との互換:
        - 旧 API (init_label, ensure_label, remove_label) は廃止
        - 代わりに birth/detach/reap_ghosts
        - update_phi 等は cid を引数に取る (lid ではなく)
    """

    def __init__(self):
        # cid 発番カウンタ。単調増加。再利用しない。
        self._next_cid = 0

        # cid <-> lid マッピング (active のみ)
        # NOTE: lid は vl.labels の int ID。frozenset ではない。
        # frozenset は label["nodes"] の中身であり、それは存在層内部の話。
        self.cid_of_lid = {}      # lid (int) -> cid (int)
        self.current_lid = {}     # cid -> lid (int) or None

        # ライフサイクル記録
        self.born_at = {}         # cid -> window
        self.host_lost_at = {}    # cid -> window or None (None なら host 中)
        self.original_phase_sig = {}  # cid -> 初代 lid の phase_sig

        # 認知データ (cid キー)
        self.phi = {}             # cid -> float
        self.prev_phi = {}        # cid -> float
        self.attention = {}       # cid -> {node_id: float}
        self.familiarity = {}     # cid -> {other_cid: float}

        # ──────────────────────────────────────────────
        # v9.8b: Introspection state
        # ──────────────────────────────────────────────
        # prev_disposition: 前 window 末の disposition vector (比較用)
        # current_disposition: 現 window 末の disposition vector
        # introspection_tags: この window で生成されたタグのリスト
        #
        # ライフサイクル:
        #   1. window 末で current_disposition を外部から set する
        #      (メインループが disposition を計算した後)
        #   2. generate_introspection_tags() を呼ぶ
        #      → prev と current を比較してタグ生成
        #   3. commit_disposition() を呼ぶ
        #      → prev <- current、current をクリア
        #
        # 初出 cid では prev が None なので、初回 window ではタグは出ない
        # (前時点が存在しないので比較不能、これは正しい挙動)
        self.prev_disposition = {}       # cid -> {social, stability, spread, familiarity}
        self.current_disposition = {}    # cid -> {social, stability, spread, familiarity}
        self.introspection_tags = {}     # cid -> [tag strings]

        # 統計用
        self._reaped_history = []  # [{cid, born, host_lost, reaped, ghost_dur}]
        self._tag_history = []     # [{cid, window, prev, current, delta, tags, state}]

    # ──────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────
    def birth(self, lid, phase_sig, current_window):
        """新しい label が生まれた時に呼ぶ。新 cid を発番する。
        既存 lid なら何もしない (重複呼び出し対応)。"""
        if lid in self.cid_of_lid:
            return self.cid_of_lid[lid]
        cid = self._next_cid
        self._next_cid += 1
        self.cid_of_lid[lid] = cid
        self.current_lid[cid] = lid
        self.born_at[cid] = current_window
        self.host_lost_at[cid] = None
        self.original_phase_sig[cid] = phase_sig
        self.phi[cid] = phase_sig
        self.prev_phi[cid] = phase_sig
        self.attention[cid] = {}
        self.familiarity[cid] = {}
        # v9.8b: introspection state
        # prev = None → 初回 window では比較不能、タグ生成されない
        self.prev_disposition[cid] = None
        self.current_disposition[cid] = None
        self.introspection_tags[cid] = []
        return cid

    def detach(self, lid, current_window):
        """label が cull された時に呼ぶ。cid データは消さない。
        cog データはそのまま残り、current_lid[cid] = None になる。"""
        cid = self.cid_of_lid.pop(lid, None)
        if cid is None:
            return None
        self.current_lid[cid] = None
        self.host_lost_at[cid] = current_window
        return cid

    def reap_ghosts(self, current_window):
        """TTL 超過した ghost cid を完全削除する。
        Returns: 削除された cid のリスト。"""
        reaped = []
        for cid in list(self.host_lost_at.keys()):
            lost_w = self.host_lost_at[cid]
            if lost_w is None:
                continue  # まだ host 中
            if current_window - lost_w >= GHOST_TTL:
                # 完全削除 (provisional retention limit)
                ghost_dur = current_window - lost_w
                self._reaped_history.append({
                    "cid": cid,
                    "born": self.born_at.get(cid),
                    "host_lost": lost_w,
                    "reaped": current_window,
                    "ghost_duration": ghost_dur,
                })
                self.current_lid.pop(cid, None)
                self.host_lost_at.pop(cid, None)
                self.born_at.pop(cid, None)
                self.original_phase_sig.pop(cid, None)
                self.phi.pop(cid, None)
                self.prev_phi.pop(cid, None)
                self.attention.pop(cid, None)
                self.familiarity.pop(cid, None)
                # v9.8b: clean up introspection state
                self.prev_disposition.pop(cid, None)
                self.current_disposition.pop(cid, None)
                self.introspection_tags.pop(cid, None)
                reaped.append(cid)
        return reaped

    # ──────────────────────────────────────────────────────
    # State queries
    # ──────────────────────────────────────────────────────
    def is_hosted(self, cid):
        return self.current_lid.get(cid) is not None

    def is_ghost(self, cid):
        if cid not in self.current_lid:
            return False
        return self.current_lid[cid] is None

    def cid_for_lid(self, lid):
        return self.cid_of_lid.get(lid)

    def all_hosted_cids(self):
        return [cid for cid, lid in self.current_lid.items()
                if lid is not None]

    def all_ghost_cids(self):
        return [cid for cid, lid in self.current_lid.items()
                if lid is None]

    def get_n_partners(self, cid):
        return len(self.familiarity.get(cid, {}))

    def get_attention_entropy(self, cid):
        att = self.attention.get(cid, {})
        if not att:
            return 0.0
        vs = list(att.values())
        s = sum(vs)
        if s <= 0:
            return 0.0
        ps = [v / s for v in vs if v > 0]
        if not ps:
            return 0.0
        H = -sum(p * math.log(p) for p in ps)
        max_H = math.log(len(ps)) if len(ps) > 1 else 1.0
        return H / max_H if max_H > 0 else 0.0

    def get_familiarity_mean(self, cid):
        fam = self.familiarity.get(cid, {})
        if not fam:
            return 0.0
        return float(np.mean(list(fam.values())))

    def get_familiarity_max(self, cid):
        fam = self.familiarity.get(cid, {})
        if not fam:
            return 0.0
        return float(max(fam.values()))

    # ──────────────────────────────────────────────────────
    # Updates (only callable on hosted cids)
    # ──────────────────────────────────────────────────────
    def update_phi(self, cid, mean_theta, mean_S):
        if cid not in self.phi:
            return
        if not self.is_hosted(cid):
            return  # ghost: no perception update
        self.prev_phi[cid] = self.phi[cid]
        alpha = 0.1 * (1.0 - max(0.0, min(1.0, mean_S)))
        self.phi[cid] += alpha * math.sin(mean_theta - self.phi[cid])
        while self.phi[cid] > math.pi:
            self.phi[cid] -= 2 * math.pi
        while self.phi[cid] < -math.pi:
            self.phi[cid] += 2 * math.pi

    def update_attention(self, cid, struct_set, core):
        if cid not in self.attention:
            return
        if not self.is_hosted(cid):
            return  # ghost: no perception update
        att = self.attention[cid]
        # decay
        for k in list(att.keys()):
            att[k] *= ATTENTION_DECAY
            if att[k] < 0.01:
                del att[k]
        # add (excluding core nodes — v96/v97 と同じ)
        # core ノードは BFS の起点なので毎 step structural set に含まれる。
        # attention map に入れると core が attention max を独占し、
        # 他のノードへの偏りが見えなくなる。Phase 2 review (v95) で確定。
        for n in struct_set:
            if n in core:
                continue
            att[n] = att.get(n, 0.0) + 1.0

    def update_familiarity(self, cid, struct_set, core,
                            node_to_lid, macro_lids):
        """familiarity を更新。other は cid ベースで保持する。
        node_to_lid 経由で接触相手を特定し、SubjectLayer 内で
        cid に変換してから familiarity dict に積む。"""
        if cid not in self.familiarity:
            return
        if not self.is_hosted(cid):
            return  # ghost: no perception update
        fam = self.familiarity[cid]
        # decay
        for k in list(fam.keys()):
            fam[k] *= FAMILIARITY_DECAY
            if fam[k] < 0.01:
                del fam[k]
        # add: 相手 lid → 相手 cid に変換
        my_lid = self.current_lid[cid]
        seen_others = set()
        for n in struct_set:
            other_lid = node_to_lid.get(n)
            if other_lid is None:
                continue
            if other_lid in macro_lids:
                continue
            if other_lid == my_lid:
                continue
            other_cid = self.cid_of_lid.get(other_lid)
            if other_cid is None:
                continue
            if other_cid in seen_others:
                continue
            seen_others.add(other_cid)
            fam[other_cid] = fam.get(other_cid, 0.0) + 1.0

    # ──────────────────────────────────────────────────────
    # v9.8b: Introspection
    # ──────────────────────────────────────────────────────
    def set_current_disposition(self, cid, social, stability, spread, familiarity):
        """外部 (メインループ) が window 末の disposition を計算したら
        この関数で SubjectLayer に登録する。ghost は無視する。"""
        if not self.is_hosted(cid):
            return
        if cid not in self.current_disposition:
            return
        self.current_disposition[cid] = {
            "social": float(social),
            "stability": float(stability),
            "spread": float(spread),
            "familiarity": float(familiarity),
        }

    def generate_introspection_tags(self, cid, current_window):
        """Stage 1: 固定閾値による構造的中立タグ生成。

        prev_disposition と current_disposition を比較して
        delta を計算し、閾値を超えた軸に gain/loss タグを付ける。

        PROVISIONAL ENGINEERING VALUES (GPT audit):
          - 神の手問題を最小化するため、固定閾値は observational only
          - feedback に使わない (torque / action は変更しない)
          - 結果を見てタグ頻度を報告し、必要なら Stage 2 へ移行

        初回 window (prev=None) ではタグ生成されず、_tag_history にも
        追加されない (比較不能なので)。2 回目以降の window では、
        タグがゼロでも entry を _tag_history に追加する
        (「タグ頻度の偏りを報告する」ための分母を確保する)。

        ghost は無視 (is_hosted チェック)。

        Returns: 生成されたタグのリスト (empty list 可)
        """
        tags = []
        if not self.is_hosted(cid):
            return tags
        if cid not in self.prev_disposition:
            return tags

        prev = self.prev_disposition[cid]
        curr = self.current_disposition.get(cid)

        if prev is None or curr is None:
            # 初回 window: 比較対象なし、履歴にも記録しない
            self.introspection_tags[cid] = []
            return tags

        # Delta 計算
        d_social = curr["social"] - prev["social"]
        d_stability = curr["stability"] - prev["stability"]
        d_spread = curr["spread"] - prev["spread"]
        d_familiarity = curr["familiarity"] - prev["familiarity"]

        # 閾値判定 (Stage 1: fixed thresholds, strict >)
        if d_social > INTROSPECTION_THRESHOLD_SOCIAL:
            tags.append("gain_social")
        elif d_social < -INTROSPECTION_THRESHOLD_SOCIAL:
            tags.append("loss_social")

        if d_stability > INTROSPECTION_THRESHOLD_STABILITY:
            tags.append("gain_stability")
        elif d_stability < -INTROSPECTION_THRESHOLD_STABILITY:
            tags.append("loss_stability")

        if d_spread > INTROSPECTION_THRESHOLD_SPREAD:
            tags.append("gain_spread")
        elif d_spread < -INTROSPECTION_THRESHOLD_SPREAD:
            tags.append("loss_spread")

        if d_familiarity > INTROSPECTION_THRESHOLD_FAMILIARITY:
            tags.append("gain_familiarity")
        elif d_familiarity < -INTROSPECTION_THRESHOLD_FAMILIARITY:
            tags.append("loss_familiarity")

        self.introspection_tags[cid] = tags

        # Log entry for analysis (prev / current / delta / tags / state)
        # ゼロタグでも entry を追加する (GPT 監査: タグ頻度分布の分母確保)
        state = "hosted" if self.is_hosted(cid) else "ghost"
        self._tag_history.append({
            "cid": cid,
            "window": current_window,
            "prev_social": round(prev["social"], 4),
            "prev_stability": round(prev["stability"], 4),
            "prev_spread": round(prev["spread"], 4),
            "prev_familiarity": round(prev["familiarity"], 4),
            "current_social": round(curr["social"], 4),
            "current_stability": round(curr["stability"], 4),
            "current_spread": round(curr["spread"], 4),
            "current_familiarity": round(curr["familiarity"], 4),
            "delta_social": round(d_social, 4),
            "delta_stability": round(d_stability, 4),
            "delta_spread": round(d_spread, 4),
            "delta_familiarity": round(d_familiarity, 4),
            "tags": "|".join(tags) if tags else "",
            "n_tags": len(tags),
            "state": state,
        })

        return tags

    def commit_disposition(self, cid):
        """window 末にタグ生成が終わったら呼ぶ。
        prev <- current に移す。次の window の比較準備。
        ghost は無視 (hosted のみが内省する)。"""
        if not self.is_hosted(cid):
            return
        if cid not in self.current_disposition:
            return
        curr = self.current_disposition[cid]
        if curr is not None:
            # dict copy (参照共有を避ける)
            self.prev_disposition[cid] = dict(curr)


# ================================================================
# STRUCTURAL HELPERS  (v96 と同じ)
# ================================================================
def compute_structural(core, max_hops, link_adj, alive_n):
    if not core:
        return set()
    visited = set(core)
    frontier = set(n for n in core if n in alive_n)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in link_adj.get(n, set()):
                if nb not in visited and nb in alive_n:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited


def build_link_adj(state):
    adj = defaultdict(set)
    for lk in state.alive_l:
        adj[lk[0]].add(lk[1])
        adj[lk[1]].add(lk[0])
    return adj


def structural_stats(state, struct_set, phase_sig):
    if len(struct_set) < 2:
        return phase_sig, 0.0
    thetas = [float(state.theta[n]) for n in struct_set]
    sin_s = sum(math.sin(t) for t in thetas)
    cos_s = sum(math.cos(t) for t in thetas)
    mean_theta = math.atan2(sin_s, cos_s)
    n_links = 0
    s_sum = 0.0
    for lk in state.alive_l:
        if lk[0] in struct_set and lk[1] in struct_set:
            n_links += 1
            s_sum += state.S.get(lk, 0.0)
    return mean_theta, s_sum / max(1, n_links)


def compute_spatial(state, label, torus_sub, max_hops):
    core = frozenset(n for n in label["nodes"] if n in state.alive_n)
    if not core:
        return set(), core
    visited = set(core)
    frontier = set(core)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in torus_sub.get(n, []):
                if nb not in visited and nb in state.alive_n:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited, core


def circular_diff(a, b):
    d = a - b
    while d > math.pi:
        d -= 2 * math.pi
    while d < -math.pi:
        d += 2 * math.pi
    return d


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=10,
        window_steps=500, tag="short"):

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    outdir = Path(f"diag_v98b_introspection_{tag}")
    outdir.mkdir(exist_ok=True)
    for sub in ["aggregates", "labels", "subjects",
                "representatives", "network", "introspection"]:
        (outdir / sub).mkdir(exist_ok=True)

    # Engine
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    # NOTE: v9.7 の torque_factor 機構は使わない。
    # virtual_layer_v9 の apply_torque_only は label.get("torque_factor", 1.0)
    # で参照するため、torque_factor を一切設定しなければ v9.6 と同じ挙動になる。

    cog = SubjectLayer()

    engine.run_injection()

    # ── Maturation ──
    # maturation 中も label の生死は起きる。birth/detach を呼ぶ。
    # ただし disposition 計算と per_window 出力はしない。
    for w in range(maturation_windows):
        macro_set = set(engine.virtual.macro_nodes)
        prev_lids = set(engine.virtual.labels.keys()) - macro_set
        engine.step_window(steps=window_steps)
        macro_set = set(engine.virtual.macro_nodes)
        curr_lids = set(engine.virtual.labels.keys()) - macro_set

        # Detach culled
        for lid in (prev_lids - curr_lids):
            cog.detach(lid, w)
        # Birth new
        for lid in (curr_lids - prev_lids):
            lab = engine.virtual.labels[lid]
            cog.birth(lid, lab["phase_sig"], w)
        # Ensure existing (in case of init edge cases)
        for lid in curr_lids:
            if lid not in cog.cid_of_lid:
                lab = engine.virtual.labels[lid]
                cog.birth(lid, lab["phase_sig"], w)

        # Reap ghosts every window (provisional TTL)
        cog.reap_ghosts(w)

    vl = engine.virtual
    print(f"  seed={seed} mat done. labels={len(vl.labels)} "
          f"links={len(engine.state.alive_l)} "
          f"cids_total={cog._next_cid} "
          f"hosted={len(cog.all_hosted_cids())} "
          f"ghosts={len(cog.all_ghost_cids())}")

    # Track ALL non-macro labels (現存 hosted のみ)
    tracked_lids = set()
    for lid in vl.labels:
        if lid not in vl.macro_nodes:
            tracked_lids.add(lid)
            if lid not in cog.cid_of_lid:
                # safety: maturation で見落としたものを救出
                cog.birth(lid, vl.labels[lid]["phase_sig"], maturation_windows - 1)

    # Storage
    bg_prob = BASE_PARAMS["background_injection_prob"]
    window_rows = []
    repr_timelines = {}      # cid -> [entries]
    all_deaths = []
    all_births_after_mat = []

    # Convergence bias (seed-level)
    conv_near_ratios = []
    div_near_ratios = []

    # Per-label accumulator (v96/v97 比較ブリッジ用、lid キー)
    label_meta = {}
    for lid in tracked_lids:
        lab = vl.labels[lid]
        label_meta[lid] = {
            "birth_w": lab["born"],
            "death_w": None,
            "lifespan": 0,
            "phase_sig": lab["phase_sig"],
            "n_core": len([n for n in lab["nodes"]
                           if n in engine.state.alive_n]),
            "cognitive_id": cog.cid_for_lid(lid),
            "became_ghost_w": None,
        }

    # Per-subject accumulator (cid キー、v9.8a 新設)
    subject_meta = {}
    for cid in cog.all_hosted_cids():
        subject_meta[cid] = {
            "birth_window": cog.born_at[cid],
            "host_lost_window": None,
            "reaped_window": None,
            "final_state": "hosted",
            "ghost_duration": 0,
            "last_lid_when_alive": cog.current_lid[cid],
            "original_phase_sig": cog.original_phase_sig[cid],
            "last_n_partners": 0,
            "last_familiarity_max": 0.0,
            "last_attention_size": 0,
        }

    # ── Tracking Phase ──
    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # node → lid mapping
        node_to_lid = {}
        for lid, lab in vl.labels.items():
            if lid not in vl.macro_nodes:
                for n in lab["nodes"]:
                    node_to_lid[n] = lid

        # Spatial fields (lid キー、physics と同じ世界)
        spatial_fields = {}
        for lid in tracked_lids:
            if lid not in vl.labels:
                continue
            label = vl.labels[lid]
            core_alive = sum(1 for n in label["nodes"]
                             if n in engine.state.alive_n)
            if core_alive == 0:
                continue
            sp_set, core = compute_spatial(
                engine.state, label, torus_sub, core_alive)
            spatial_fields[lid] = (sp_set, core, core_alive)

        window_st_sizes = defaultdict(list)  # cid -> [sizes]

        for step in range(window_steps):
            # Physics canon
            engine.realizer.step(engine.state)
            engine.physics.step_pre_chemistry(engine.state)
            engine.chem.step(engine.state)
            engine.physics.step_resonance(engine.state)

            engine._g_scores[:] = 0
            engine.grower.step(engine.state)
            agr = engine.grower.params.auto_growth_rate
            for k in engine.state.alive_l:
                r = engine.state.R.get(k, 0.0)
                if r > 0:
                    a = min(agr * r,
                            max(engine.state.get_latent(k[0], k[1]), 0))
                    if a > 0:
                        engine._g_scores[k[0]] += a
                        engine._g_scores[k[1]] += a
            gz = float(engine._g_scores.sum())

            engine.intruder.step(engine.state)
            engine.physics.step_decay_exclusion(engine.state)

            al = list(engine.state.alive_n)
            na = len(al)
            if na > 0:
                aa = np.array(al)
                if BIAS > 0 and gz > 0:
                    ga = engine._g_scores[aa]
                    gs = ga.sum()
                    if gs > 0:
                        pg = ga / gs
                        pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
                        pd /= pd.sum()
                    else:
                        pd = np.ones(na) / na
                else:
                    pd = np.ones(na) / na
                mk = engine.state.rng.random(na) < bg_prob
                for idx in range(na):
                    if mk[idx]:
                        t = int(engine.state.rng.choice(aa, p=pd))
                        if t in engine.state.alive_n:
                            engine.state.E[t] = min(
                                1.0, engine.state.E[t] + 0.3)
                            if engine.state.Z[t] == 0 and \
                               engine.state.rng.random() < 0.5:
                                engine.state.Z[t] = 1 if \
                                    engine.state.rng.random() < 0.5 else 2

            # Cognitive update (hosted only)
            link_adj = build_link_adj(engine.state)

            for lid in list(spatial_fields.keys()):
                if lid not in vl.labels:
                    continue
                cid = cog.cid_for_lid(lid)
                if cid is None:
                    continue
                sp_set, core, max_hops = spatial_fields[lid]
                label = vl.labels[lid]

                struct_set = compute_structural(
                    core, max_hops, link_adj, engine.state.alive_n)

                mean_theta, mean_S = structural_stats(
                    engine.state, struct_set, label["phase_sig"])

                cog.update_phi(cid, mean_theta, mean_S)
                cog.update_attention(cid, struct_set, core)
                cog.update_familiarity(
                    cid, struct_set, core,
                    node_to_lid, vl.macro_nodes)

                window_st_sizes[cid].append(len(struct_set))

                # Convergence bias (sample every 10 steps)
                if step % 10 == 0 and len(struct_set) >= 2:
                    phase_sig = label["phase_sig"]
                    delta = circular_diff(phase_sig, mean_theta)
                    thetas = [float(engine.state.theta[n])
                              for n in struct_set]
                    near = sum(1 for t in thetas
                               if abs(circular_diff(phase_sig, t)) < math.pi/4)
                    near_ratio = near / len(struct_set)

                    if abs(delta) < CONVERGENCE_THRESHOLD:
                        conv_near_ratios.append(near_ratio)
                    elif abs(delta) > 2.5:
                        div_near_ratios.append(near_ratio)

        # ── End of window: disposition + aggregates ──
        # hosted cids only
        hosted_cids = [cid for cid in cog.all_hosted_cids()
                       if cid in cog.phi]
        max_partners = max(
            (cog.get_n_partners(cid) for cid in hosted_cids),
            default=1)
        max_partners = max(max_partners, 1)

        socials = []
        stabilities = []
        spreads = []
        familiarities = []
        n_social = 0
        n_isolated = 0
        n_deeply = 0

        for cid in hosted_cids:
            st_sizes = window_st_sizes.get(cid, [])
            st_mean = np.mean(st_sizes) if st_sizes else 0
            st_std = np.std(st_sizes) if st_sizes else 0

            d_social = cog.get_n_partners(cid) / max_partners
            d_stability = 1.0 / (1.0 + st_std / (st_mean + EPS))
            d_spread = cog.get_attention_entropy(cid)
            d_fam = cog.get_familiarity_mean(cid)

            socials.append(d_social)
            stabilities.append(d_stability)
            spreads.append(d_spread)
            familiarities.append(d_fam)

            if d_social > 0.5:
                n_social += 1
            elif d_social < 0.15:
                n_isolated += 1
            if d_fam > 10:
                n_deeply += 1

            # Update label_meta (lid 経由、v96/v97 ブリッジ用)
            lid = cog.current_lid[cid]
            if lid in label_meta:
                label_meta[lid]["last_social"] = d_social
                label_meta[lid]["last_stability"] = d_stability
                label_meta[lid]["last_spread"] = d_spread
                label_meta[lid]["last_familiarity"] = d_fam
                label_meta[lid]["last_partners"] = cog.get_n_partners(cid)
                label_meta[lid]["last_st_mean"] = float(st_mean)
                label_meta[lid]["last_st_std"] = float(st_std)
                label_meta[lid]["last_fam_max"] = cog.get_familiarity_max(cid)
                label_meta[lid]["last_att_nodes"] = len(cog.attention.get(cid, {}))
                label_meta[lid]["lifespan"] = w - label_meta[lid]["birth_w"] + 1

            # Update subject_meta
            if cid not in subject_meta:
                subject_meta[cid] = {
                    "birth_window": cog.born_at[cid],
                    "host_lost_window": None,
                    "reaped_window": None,
                    "final_state": "hosted",
                    "ghost_duration": 0,
                    "last_lid_when_alive": cog.current_lid[cid],
                    "original_phase_sig": cog.original_phase_sig[cid],
                    "last_n_partners": 0,
                    "last_familiarity_max": 0.0,
                    "last_attention_size": 0,
                }
            subject_meta[cid]["last_n_partners"] = cog.get_n_partners(cid)
            subject_meta[cid]["last_familiarity_max"] = cog.get_familiarity_max(cid)
            subject_meta[cid]["last_attention_size"] = len(cog.attention.get(cid, {}))
            subject_meta[cid]["last_lid_when_alive"] = cog.current_lid[cid]

            # v9.8b: Register current disposition for introspection
            cog.set_current_disposition(cid, d_social, d_stability, d_spread, d_fam)

        # v9.8b: Generate introspection tags (hosted only, after disposition set)
        # prev <- current の commit はタグ生成の後で行う
        window_tags_summary = {}  # cid -> tags
        for cid in hosted_cids:
            tags = cog.generate_introspection_tags(cid, w)
            window_tags_summary[cid] = tags

        # Aggregate tag statistics for per_window CSV
        tag_counter = Counter()
        n_cids_with_tags = 0
        for cid, tags in window_tags_summary.items():
            if tags:
                n_cids_with_tags += 1
                for t in tags:
                    tag_counter[t] += 1

        # Familiarity reciprocity (cid ベース)
        reciprocal_count = 0
        asymmetric_count = 0
        symmetry_vals = []
        hosted_set = set(hosted_cids)
        for cid_a in hosted_cids:
            fam_a = cog.familiarity.get(cid_a, {})
            for cid_b in hosted_cids:
                if cid_b <= cid_a:
                    continue
                fa = fam_a.get(cid_b, 0.0)
                fb = cog.familiarity.get(cid_b, {}).get(cid_a, 0.0)
                if fa > 1.0 and fb > 1.0:
                    reciprocal_count += 1
                    sym = min(fa, fb) / max(fa, fb)
                    symmetry_vals.append(sym)
                elif fa > 1.0 or fb > 1.0:
                    asymmetric_count += 1

        # Attention overlap
        att_overlaps = []
        att_hotspots = {}
        for cid in hosted_cids:
            att = cog.attention.get(cid, {})
            if len(att) >= 5:
                median_val = np.median(list(att.values()))
                att_hotspots[cid] = {n for n, v in att.items()
                                      if v > median_val}
        for cid_a in list(att_hotspots.keys()):
            for cid_b in list(att_hotspots.keys()):
                if cid_b <= cid_a:
                    continue
                inter = len(att_hotspots[cid_a] & att_hotspots[cid_b])
                if inter > 0:
                    att_overlaps.append(inter)

        # Ghost statistics
        hosted_n = len(hosted_cids)
        ghost_n = len(cog.all_ghost_cids())
        ghost_durations = []
        for cid in cog.all_ghost_cids():
            lost_w = cog.host_lost_at[cid]
            ghost_durations.append(w - lost_w)
        ghost_dur_mean = float(np.mean(ghost_durations)) if ghost_durations else 0.0

        # Layer A: window row (v96/v97 互換 + v9.8a 新規列)
        window_rows.append({
            # v96/v97 互換
            "seed": seed,
            "window": w,
            "links": len(engine.state.alive_l),
            "v_labels": len(vl.labels),
            "alive_tracked": hosted_n,
            "mean_social": round(np.mean(socials), 4) if socials else 0,
            "mean_stability": round(np.mean(stabilities), 4) if stabilities else 0,
            "mean_spread": round(np.mean(spreads), 4) if spreads else 0,
            "mean_familiarity": round(np.mean(familiarities), 4) if familiarities else 0,
            "count_social": n_social,
            "count_isolated": n_isolated,
            "count_deeply_connected": n_deeply,
            "reciprocal_pairs": reciprocal_count,
            "asymmetric_pairs": asymmetric_count,
            "fam_symmetry_mean": round(np.mean(symmetry_vals), 4) if symmetry_vals else 0,
            "fam_symmetry_std": round(np.std(symmetry_vals), 4) if symmetry_vals else 0,
            "att_overlap_mean": round(np.mean(att_overlaps), 1) if att_overlaps else 0,
            "att_overlap_pairs": len(att_overlaps),
            # v9.8a 新規列
            "subject_count_total": cog._next_cid,
            "subject_hosted": hosted_n,
            "subject_ghost": ghost_n,
            "ghost_duration_mean": round(ghost_dur_mean, 2),
            # v9.8b 新規列 (内省タグ集計)
            "n_cids_with_tags": n_cids_with_tags,
            "n_tags_total": sum(tag_counter.values()),
            "tag_gain_social": tag_counter.get("gain_social", 0),
            "tag_loss_social": tag_counter.get("loss_social", 0),
            "tag_gain_stability": tag_counter.get("gain_stability", 0),
            "tag_loss_stability": tag_counter.get("loss_stability", 0),
            "tag_gain_spread": tag_counter.get("gain_spread", 0),
            "tag_loss_spread": tag_counter.get("loss_spread", 0),
            "tag_gain_familiarity": tag_counter.get("gain_familiarity", 0),
            "tag_loss_familiarity": tag_counter.get("loss_familiarity", 0),
        })

        # v9.8b: Commit disposition (prev <- current) for next window's comparison
        # VL step の前に行う (この window 終了時点の値を次 window の比較基準にする)
        for cid in hosted_cids:
            cog.commit_disposition(cid)

        # VL step (label の生死がここで起きる)
        macro_set = set(vl.macro_nodes)
        prev_lids = set(vl.labels.keys()) - macro_set
        isl_m = find_islands_sets(engine.state, 0.20)
        class _Isl:
            pass
        islands_dict = {}
        for i, isl in enumerate(isl_m):
            obj = _Isl()
            obj.nodes = isl
            islands_dict[i] = obj
        vs = vl.step(engine.state, engine.window_count,
                      islands=islands_dict, substrate=engine.substrate)
        engine.virtual_stats = vs
        engine.window_count += 1
        macro_set = set(vl.macro_nodes)
        curr_lids = set(vl.labels.keys()) - macro_set

        # Birth new labels → 新 cid
        ghost_births_this_window = 0
        for lid in (curr_lids - prev_lids):
            lab = vl.labels[lid]
            new_cid = cog.birth(lid, lab["phase_sig"], w)
            if lid not in tracked_lids:
                tracked_lids.add(lid)
                all_births_after_mat.append({"lid": lid,
                                             "cid": new_cid, "w": w})
                label_meta[lid] = {
                    "birth_w": w,
                    "death_w": None,
                    "lifespan": 0,
                    "phase_sig": lab["phase_sig"],
                    "n_core": len([n for n in lab["nodes"]
                                   if n in engine.state.alive_n]),
                    "cognitive_id": new_cid,
                    "became_ghost_w": None,
                }

        # Detach culled labels → ghost
        for lid in (prev_lids - curr_lids):
            cid = cog.cid_for_lid(lid)
            cog.detach(lid, w)
            ghost_births_this_window += 1
            if lid in label_meta:
                label_meta[lid]["death_w"] = w
                label_meta[lid]["became_ghost_w"] = w
                all_deaths.append({"lid": lid,
                                   "cid": cid, "w": w})
            if cid is not None and cid in subject_meta:
                subject_meta[cid]["host_lost_window"] = w
                subject_meta[cid]["final_state"] = "ghost"

        # Reap ghosts (TTL)
        reaped_cids = cog.reap_ghosts(w)
        for cid in reaped_cids:
            if cid in subject_meta:
                subject_meta[cid]["reaped_window"] = w
                subject_meta[cid]["final_state"] = "reaped"
                lost_w = subject_meta[cid].get("host_lost_window")
                if lost_w is not None:
                    subject_meta[cid]["ghost_duration"] = w - lost_w

        # Update window row with reap count
        window_rows[-1]["ghost_births"] = ghost_births_this_window
        window_rows[-1]["ghost_reaped"] = len(reaped_cids)

        sec = time.time() - t0
        print(f"  seed={seed} w={w} vLb={len(vl.labels)} "
              f"hosted={hosted_n} ghost={ghost_n} "
              f"births={ghost_births_this_window} reaped={len(reaped_cids)} "
              f"cids_total={cog._next_cid} "
              f"recip={reciprocal_count} {sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # SAVE Layer A: per_window CSV
    # ════════════════════════════════════════════════════════
    csv_a = outdir / "aggregates" / f"per_window_seed{seed}.csv"
    if window_rows:
        with open(csv_a, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=window_rows[0].keys())
            writer.writeheader()
            writer.writerows(window_rows)

    # ════════════════════════════════════════════════════════
    # SAVE Layer B (旧): per_label CSV (v96/v97 比較ブリッジ)
    # ════════════════════════════════════════════════════════
    label_rows = []
    for lid, meta in label_meta.items():
        traits = []
        ls = meta.get("last_social", 0)
        lst = meta.get("last_stability", 0)
        lsp = meta.get("last_spread", 0)
        lf = meta.get("last_familiarity", 0)
        if ls > 0.5: traits.append("social")
        elif ls < 0.15: traits.append("isolated")
        if lst > 0.5: traits.append("stable")
        if lsp > 0.85: traits.append("wide_att")
        elif lsp < 0.8: traits.append("focused_att")
        if lf > 10: traits.append("deep_conn")
        if meta["death_w"] is not None: traits.append("dead")

        label_rows.append({
            "seed": seed,
            "label_id": meta.get("cognitive_id", -1),  # v98a: 互換のため cid を入れる
            "birth_window": meta["birth_w"],
            "death_window": meta.get("death_w", "") if meta.get("death_w") is not None else "",
            "lifespan": meta.get("lifespan", 0),
            "alive": meta["death_w"] is None,
            "phase_sig": round(meta.get("phase_sig", 0), 4),
            "n_core": meta.get("n_core", 0),
            "last_social": round(meta.get("last_social", 0), 4),
            "last_stability": round(meta.get("last_stability", 0), 4),
            "last_spread": round(meta.get("last_spread", 0), 4),
            "last_familiarity": round(meta.get("last_familiarity", 0), 4),
            "last_partners": meta.get("last_partners", 0),
            "last_st_mean": round(meta.get("last_st_mean", 0), 2),
            "last_st_std": round(meta.get("last_st_std", 0), 2),
            "last_fam_max": round(meta.get("last_fam_max", 0), 4),
            "last_att_nodes": meta.get("last_att_nodes", 0),
            "trajectory_type": "|".join(traits),
            # v9.8a 新規列
            "cognitive_id": meta.get("cognitive_id", -1),
            "became_ghost_w": meta.get("became_ghost_w", "") if meta.get("became_ghost_w") is not None else "",
        })

    csv_b_label = outdir / "labels" / f"per_label_seed{seed}.csv"
    if label_rows:
        with open(csv_b_label, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=label_rows[0].keys())
            writer.writeheader()
            writer.writerows(label_rows)

    # ════════════════════════════════════════════════════════
    # SAVE Layer B (新): per_subject CSV (v9.8a + v9.8b columns)
    # ════════════════════════════════════════════════════════
    # v9.8b: 各 cid の最後の _tag_history entry を取り出して
    # prev/current/delta/tags/state カラムを追加する (GPT 修正提案 B)
    last_tag_entry = {}  # cid -> last _tag_history entry
    for entry in cog._tag_history:
        last_tag_entry[entry["cid"]] = entry

    subject_rows = []
    for cid, meta in subject_meta.items():
        # 現在の状態を再判定
        if cid in cog.current_lid:
            if cog.current_lid[cid] is not None:
                final_state = "hosted"
            else:
                final_state = "ghost"
        else:
            final_state = "reaped"

        # ghost duration を最新化
        if final_state == "ghost":
            lost_w = cog.host_lost_at.get(cid)
            current_w = maturation_windows + tracking_windows - 1
            ghost_dur = current_w - lost_w if lost_w is not None else 0
        elif final_state == "reaped":
            ghost_dur = meta.get("ghost_duration", 0)
        else:
            ghost_dur = 0

        # v9.8b: 最後の tag entry からの情報 (生存中に get_introspection が呼ばれた最終回)
        tag_entry = last_tag_entry.get(cid, {})

        subject_rows.append({
            "seed": seed,
            "cognitive_id": cid,
            "birth_window": meta["birth_window"],
            "host_lost_window": meta.get("host_lost_window", "")
                if meta.get("host_lost_window") is not None else "",
            "reaped_window": meta.get("reaped_window", "")
                if meta.get("reaped_window") is not None else "",
            "final_state": final_state,
            "ghost_duration": ghost_dur,
            "original_phase_sig": round(meta.get("original_phase_sig", 0), 4),
            "last_n_partners": meta.get("last_n_partners", 0),
            "last_familiarity_max": round(meta.get("last_familiarity_max", 0), 4),
            "last_attention_size": meta.get("last_attention_size", 0),
            # v9.8b: introspection columns (GPT 修正提案 B)
            "last_tag_window": tag_entry.get("window", ""),
            "prev_social": tag_entry.get("prev_social", ""),
            "prev_stability": tag_entry.get("prev_stability", ""),
            "prev_spread": tag_entry.get("prev_spread", ""),
            "prev_familiarity": tag_entry.get("prev_familiarity", ""),
            "current_social": tag_entry.get("current_social", ""),
            "current_stability": tag_entry.get("current_stability", ""),
            "current_spread": tag_entry.get("current_spread", ""),
            "current_familiarity": tag_entry.get("current_familiarity", ""),
            "delta_social": tag_entry.get("delta_social", ""),
            "delta_stability": tag_entry.get("delta_stability", ""),
            "delta_spread": tag_entry.get("delta_spread", ""),
            "delta_familiarity": tag_entry.get("delta_familiarity", ""),
            "generated_tags": tag_entry.get("tags", ""),
            "state_at_window": tag_entry.get("state", ""),
        })

    csv_b_subject = outdir / "subjects" / f"per_subject_seed{seed}.csv"
    if subject_rows:
        with open(csv_b_subject, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=subject_rows[0].keys())
            writer.writeheader()
            writer.writerows(subject_rows)

    # ════════════════════════════════════════════════════════
    # SAVE: Convergence bias
    # ════════════════════════════════════════════════════════
    conv_data = {
        "conv_near_mean": float(np.mean(conv_near_ratios))
            if conv_near_ratios else None,
        "div_near_mean": float(np.mean(div_near_ratios))
            if div_near_ratios else None,
        "ratio": (float(np.mean(conv_near_ratios)) / float(np.mean(div_near_ratios)))
            if conv_near_ratios and div_near_ratios
            and np.mean(div_near_ratios) > 0 else None,
        "n_conv": len(conv_near_ratios),
        "n_div": len(div_near_ratios),
    }
    with open(outdir / "aggregates" / f"conv_bias_seed{seed}.json", "w") as f:
        json.dump(conv_data, f, indent=2)

    # ════════════════════════════════════════════════════════
    # SAVE: Familiarity network (cid ベース)
    # ════════════════════════════════════════════════════════
    fam_edges = []
    for cid_a in cog.all_hosted_cids():
        fam_a = cog.familiarity.get(cid_a, {})
        for other_cid, val in fam_a.items():
            if val > 1.0:
                fam_edges.append({
                    "seed": seed,
                    "from": cid_a,
                    "to": other_cid,
                    "familiarity": round(val, 4),
                })
    if fam_edges:
        with open(outdir / "network" / f"fam_edges_seed{seed}.csv",
                  "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fam_edges[0].keys())
            writer.writeheader()
            writer.writerows(fam_edges)

    # ════════════════════════════════════════════════════════
    # SAVE: Subject lifecycle history (reaped log)
    # ════════════════════════════════════════════════════════
    if cog._reaped_history:
        with open(outdir / "subjects" / f"reaped_seed{seed}.csv",
                  "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cog._reaped_history[0].keys())
            writer.writeheader()
            writer.writerows(cog._reaped_history)

    # ════════════════════════════════════════════════════════
    # SAVE: Introspection log (v9.8b 新規)
    # ════════════════════════════════════════════════════════
    # 全 hosted cid × tracking_windows の内省ログ。
    # 初回 window (prev=None) では空タグで entry 自体は無い。
    # 2 回目以降の window から entry が出る。
    if cog._tag_history:
        intro_path = outdir / "introspection" / f"introspection_log_seed{seed}.csv"
        with open(intro_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cog._tag_history[0].keys())
            writer.writeheader()
            writer.writerows(cog._tag_history)

    # ════════════════════════════════════════════════════════
    # Print summary
    # ════════════════════════════════════════════════════════
    elapsed = time.time() - t_start

    # v9.8b: Tag frequency summary
    all_tags = Counter()
    for entry in cog._tag_history:
        tags_str = entry.get("tags", "")
        if tags_str:
            for t in tags_str.split("|"):
                all_tags[t] += 1

    print(f"\n  seed={seed} DONE in {elapsed:.0f}s")
    print(f"    cids total:    {cog._next_cid}")
    print(f"    hosted now:    {len(cog.all_hosted_cids())}")
    print(f"    ghosts now:    {len(cog.all_ghost_cids())}")
    print(f"    reaped:        {len(cog._reaped_history)}")
    print(f"    label rows:    {len(label_rows)}")
    print(f"    subject rows:  {len(subject_rows)}")
    print(f"    tag entries:   {len(cog._tag_history)}")
    print(f"    total tags:    {sum(all_tags.values())}")
    if all_tags:
        print(f"    tag dist:")
        for tag in ["gain_social", "loss_social",
                    "gain_stability", "loss_stability",
                    "gain_spread", "loss_spread",
                    "gain_familiarity", "loss_familiarity"]:
            n = all_tags.get(tag, 0)
            print(f"      {tag:>18}: {n}")
    print(f"    conv ratio:    {conv_data.get('ratio')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.8b Minimal Introspection "
                    "(Subject Reversal + fixed-threshold introspection tags, "
                    "no feedback)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=10)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()

    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        tag=args.tag)
