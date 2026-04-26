#!/usr/bin/env python3
"""
ESDE v9.15 — Memory Readout (CID Self-Buffer, builds on v9.14 Probabilistic Expenditure)
=========================================================================================
v9.14 (primitive/v914/v914_probabilistic_expenditure.py) を丸ごとコピーして
以下を「追加のみ」で実装 (Layer C = CID self-read, additive-only):
  - CidSelfBuffer (CID 専用メモリ領域、メンバーノード/リンクの snapshot + 一致判定)
  - Fetch Operations (event 駆動の read_on_event 呼び出し、Lazy Registration)
  - A observer (per_subject CSV への v915_* 13 列追加、per_cid_self CSV 新規出力)
  - Self-Divergence Tracker (同クラス cid ペアの theta_current 乖離、class_divergence CSV)

v9.15 段階 2 差分:
  - Fetch は v9.14 Layer B の event 発火 (E1/E2/E3) トリガ (50 step 駆動は廃止)
  - Match Ratio 集約を廃止、3 点セット (any_mismatch_ever / count / last_step) +
    event 種別ごとの fetch / mismatch カウントを per_subject CSV に追加
  - divergence_log に event_type_full / event_type_coarse 列を追加

v9.14 既存ロジック・出力には 1 バイトも変更を加えない
(baseline per_window / per_subject の v914 列 / pulse_log / per_label / audit/* CSV は bit-identical)。
Layer A / Layer B を完全維持、Layer C は CID 主体の read-only 観測。
engine.rng / capture_rng への touch 禁止、物理層・存在層への介入禁止、
CID の Q_remaining を Layer C は参照しない。

A/B 分離: [B] = CID 主体ファイル (他の B のみ import 可), [A] = 研究者観察ファイル
(B を read-only でのみ参照)。v917_cid_self_buffer.py は [B]、
v917_a_observer.py / v917_divergence_tracker.py は [A]。

出力ディレクトリ: diag_v917_{tag}/
  aggregates/  (v9.14 既存、per_subject は v915_* 列を追加)
  audit/       (v9.14 既存、改変不可)
  selfread/    (v9.15 新規、per_cid_self / divergence_log / class_divergence)

USAGE:
  # smoke
  python v917_memory_readout.py --seed 0 --maturation-windows 5 \\
      --tracking-windows 2 --window-steps 100 --tag smoke

  # 本番 (24 seeds)
  seq 0 23 | parallel -j24 python v917_memory_readout.py \\
      --seed {} --maturation-windows 20 --tracking-windows 50 \\
      --window-steps 500 --tag main

設計書: v915_段階1_実装草案.md, v9.15 実装指示書 (Code A 向け)

以下、v9.14 オリジナルの docstring:
------------------------------------------------------

ESDE v9.14 — Probabilistic Expenditure Audit (builds on v9.13 Persistence Audit)
=================================================================================
v9.13 (primitive/v913/v913_persistence_audit.py) を丸ごとコピーして
以下を「追加のみ」で実装 (Layer B = spend audit ledger, audit-only):
  - SpendAuditLedger (cid 単位の仮想原資 Q / virtual attention / virtual familiarity)
  - Event emitter (E1 core link death/birth, E2 core link R-state change,
    E3 familiarity contact onset)
  - Event 発生時の spend packet (E_t 読み出し → 差分 Δ 計算 → virtual_*
    更新 → Q_remaining 減算 → audit 記録)
  - audit CSV 出力 (per_event_audit, run_level_audit_summary) を
    diag_v914_{tag}/audit/ 配下に配置

v9.13 既存ロジック・出力には 1 バイトも変更を加えない
(baseline per_window / per_subject / pulse_log / per_label CSV は bit-identical)。
Layer A (既存 50-step 固定 pulse) を完全維持、Layer B は audit-only。
engine.rng / capture_rng への touch 禁止、物理層・存在層への介入禁止。

設計書: v914_implementation_instructions.md (present doc),
        ESDE_v9_14_Claude_Implementation_Memo_EN.txt (GPT memo, source of truth)

USAGE:
  # smoke
  python v914_probabilistic_expenditure.py --seed 0 --maturation-windows 5 \\
      --tracking-windows 2 --window-steps 100 --tag smoke

  # short (48 seeds × 10 windows)
  seq 0 47 | parallel -j24 python v914_probabilistic_expenditure.py \\
      --seed {} --maturation-windows 20 --tracking-windows 10 \\
      --window-steps 500 --tag short

  # long (5 seeds × 50 windows)
  seq 0 4 | parallel -j5 python v914_probabilistic_expenditure.py \\
      --seed {} --maturation-windows 20 --tracking-windows 50 \\
      --window-steps 500 --tag long

以下、v9.13 オリジナルの docstring:
------------------------------------------------------

ESDE v9.13 Step 0 — Persistence Audit (builds on v9.11 Cognitive Capture)
==========================================================================
v9.11 (primitive/v911/v911_cognitive_capture.py) を丸ごとコピーして以下を「追加のみ」で実装:
  - age_r (連続 R>0 step 数) / max_age_r カウンタ追加
  - alive_l 差分検出による link birth/death 追跡
  - Resonance 直後の age_r 更新
  - label birth 時のメンバーリンク persistence 記録
  - window 末の shadow component 分析
  - 4 種の persistence CSV 出力 (link_life_log / link_snapshot_log /
    label_member_persistence / shadow_component_log)

v9.11 既存ロジック・出力には 1 バイトも変更を加えない (per_window/v99_/v10_/v11_ 完全保持)。
物理層 (v19g_canon, esde_v82_engine), VL (virtual_layer_v9), pickup 機構には介入しない。

設計書: v913_step0_persistence_audit_design_rev2.md

USAGE:
  # smoke
  python v913_persistence_audit.py --seed 0 --maturation-windows 5 \\
      --tracking-windows 2 --window-steps 100 --tag smoke

  # 本実行 (1 seed × 40 windows)
  python v913_persistence_audit.py --seed 0 --maturation-windows 20 \\
      --tracking-windows 20 --window-steps 500 --tag audit

以下、v9.11 オリジナルの docstring:
------------------------------------------------------

ESDE v9.11 — Cognitive Capture (builds on v9.10 Pulse Model)
=============================================================
v9.10 (primitive/v910/v910_pulse_model.py) を丸ごとコピーして以下を「追加のみ」で実装:
  - Birth 時に B_Gen (Genesis Budget) と M_c (Memory Core, 4 要素) を固定記録
  - Pulse 時に E_t (現在経験) を抽出
  - 差分分解型 Weighted L1 で Δ を計算 (n / S / r / phase 4 軸、phase は circular)
  - p_capture = V11_P_MAX × exp(-V11_LAMBDA × Δ) で捕捉確率
  - 独立 RNG (capture_rng = default_rng(seed ^ 0xC0FFEE)) で TRUE/FALSE 判定
  - cold_start (pulse <= 3) は判定保留、Δ / p_capture は記録、集計除外
  - pulse_log.csv と per_subject CSV に v11_ prefix で列追加 (既存列は触らない)

v9.10 既存ロジック・出力には 1 バイトも変更を加えない (per_window/v99_/v10_ 完全保持)。
物理層 (v19g_canon, esde_v82_engine), VL (virtual_layer_v9), pickup 機構には介入しない。

USAGE:
  # smoke
  python v911_cognitive_capture.py --seed 0 --maturation-windows 5 \\
      --tracking-windows 2 --window-steps 100 --tag smoke

  # 本番 short (48 seeds × 10 windows)
  seq 0 47 | parallel -j24 python v911_cognitive_capture.py --seed {} \\
      --tracking-windows 10 --tag short

  # 本番 long (5 seeds × 50 windows)
  seq 0 4 | parallel -j5 python v911_cognitive_capture.py --seed {} \\
      --tracking-windows 50 --tag long

V11_NORM_N は Step 0 norm audit (v911_norm_audit_result.md) で 86 (p95 floor) に決定済み。
V11_LAMBDA は smoke 後に Δ 実分布から再決定する (v911_capture_param_audit.md に根拠記載)。

以下、v9.10 オリジナルの docstring:
------------------------------------------------------

ESDE v9.8c — Information Pickup (builds on v9.8b Minimal Introspection)
========================================================================
GPT 監査メモ (ESDE_v9_8c_Updated_Design_Audit_Memo) と
Gemini アーキテクチャ裁定 (排他的競争モデル) に基づく実装。
v9.8a の Subject Reversal、v9.8b の Introspection の上に、
情報拾得機構 (Information Pickup) を乗せる。

目的:
  hosted cid が、死んだ label の情報を死亡情報プールから拾得する。
  拾得は排他的競争 (1 record = 1 cid)。
  競争は phase 距離で決まる (近い者が勝つ)。
  拾得効果は ghost 化後の TTL 延長のみ。物理層には触れない。

設計の根拠 (Taka との議論で確定):
  - Aruism: 物理層はランダムで不可侵 (「ここをいじり倒すと ESDE が死ぬ」)
  - 量子的オンソロジー: 死亡情報プールは空間構造を持たない (非局所)
  - 食う/喰われる: 情報は有限資源、複数 cid が同じ record を共有しない
  - 主体は hosted cid (能動)、ghost は inert (受動)

含むもの (v9.8c 範囲):
  - SubjectLayer.death_pool (グローバルな死亡情報プール)
  - SubjectLayer.cid_ttl_bonus (cid ごとの TTL 延長)
  - 排他的競争による拾得 (winner = phase 距離最近)
  - reap_ghosts での effective_ttl = GHOST_TTL + ttl_bonus
  - pickup_log.csv (全拾得イベント、勝者+敗者)
  - death_pool_log.csv (全 record の出生〜消滅)
  - per_subject CSV への ttl_bonus, n_pickups, effective_ttl カラム追加

含まないもの (v9.8c 範囲外):
  - disposition / familiarity ベースの親和性 (phase only)
  - 並行拾得 (排他的のみ)
  - ghost からの拾得 (hosted only)
  - TTL 以外の効果 (familiarity merge / attention merge / disposition shift)
  - 物理層への干渉 (engine.state には 1 bit も触れない)
  - 「魂」「肉体」「憑依」「再生」などの語彙 (構造的記述語のみ)

GPT 監査の三原則 (provisional values の許容条件):
  1. provisional と明記 (コード / ドキュメント / レポート全て)
  2. feedback に使わない (TTL 延長のみ、torque/action は触らない)
  3. 結果を見て頻度・競争・効果を報告

親バージョン: primitive/v98b/v98b_introspection.py
変更箇所:
  - SubjectLayer に death_pool, cid_ttl_bonus, _pickup_log, _death_pool_log 追加
  - SubjectLayer.record_death() メソッド追加 (label cull 時)
  - SubjectLayer.attempt_pickup_round() メソッド追加 (window 末の競争解決)
  - SubjectLayer.cleanup_death_pool() メソッド追加 (LIFETIME 切れ削除)
  - SubjectLayer.reap_ghosts() で effective_ttl を使う
  - main loop に record_death / attempt_pickup_round / cleanup_death_pool 呼び出し
  - per_window CSV に v9.8c 6 列追加 (拾得統計)
  - per_subject CSV に v9.8c 4 列追加 (ttl_bonus, n_pickups, effective_ttl)
  - pickup_log.csv 新規出力
  - death_pool_log.csv 新規出力

USAGE:
  # Smoke test (必須)
  python v98c_information_pickup.py --seed 0 --maturation-windows 5 --tracking-windows 2 --window-steps 100 --tag smoke

  # Run A: 48 seeds × 10 windows
  seq 0 47 | parallel -j24 python v98c_information_pickup.py --seed {} --tracking-windows 10

  # Run B: 5 seeds × 50 windows
  seq 0 4 | parallel -j5 python v98c_information_pickup.py --seed {} --tracking-windows 50 --tag long
"""

import sys, math, time, json, csv, argparse
import numpy as np
import networkx as nx  # v9.13 Step 0: shadow component analysis
from pathlib import Path
from collections import defaultdict, Counter, deque

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline" / "v43"
_V41_DIR = _V43_DIR.parent / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"
_V910_DIR = _REPO_ROOT / "primitive" / "v910"   # for virtual_layer_v9 (frozen)
_V911_DIR = _REPO_ROOT / "primitive" / "v911"   # v9.13 Step 0: for v911_genesis_budget_measure
# v10.1: v9.17 deps are vendored locally (v917_*.py copied into v101/),
# so we don't need _V917_DIR on sys.path. Without removal, v917's older
# v914_spend_audit_ledger.py shadowed v101's modified copy (重要 bug fix)。

# Insert SCRIPT_DIR LAST so it ends up FIRST after the loop, ensuring
# local v101/v914_*/v917_* copies win over older versions on disk.
for p in [str(_V82_DIR), str(_V43_DIR), str(_V41_DIR),
          str(_ENGINE_DIR), str(_V910_DIR), str(_V911_DIR),
          str(_SCRIPT_DIR)]:
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

# v9.11: Birth 時 M_c 計測ヘルパ (既存スクリプトから再利用、コピーしない)
from v911_genesis_budget_measure import measure_birth_stats

# v9.14: Spend Audit Ledger (Layer B, audit-only)
from v914_spend_audit_ledger import SpendAuditLedger

# v9.15-v9.18: Layer C (CID self-buffer, additive-only, read-only observation)
# v9.18: fetch_operations を v918 版に差し替え (CidSelfBuffer サブクラスを生成)
from v101_fetch_operations import ensure_cid_registered as v915_ensure_cid_registered
# v9.15 段階 2: 50 step 駆動の pulse_fetch は廃止 (event 駆動 Fetch に置換)。
# pulse_fetch 関数自体は v918_fetch_operations.py に残置 (将来の Paired Audit 用)。
# v9.15-v9.17: A-side observer (read-only view of CidSelfBuffer)
# v917_* の a_observer は v918 CidSelfBuffer (v917 のサブクラス) に対しても動作
from v917_a_observer import (
    build_v915_subject_columns as v915_build_subject_columns,
    write_per_cid_self_csv as v915_write_per_cid_self_csv,
    write_observation_log_csv as v917_write_observation_log_csv,
    # v9.17 段階 4 新規
    build_v917_subject_columns as v917_build_subject_columns,
    write_other_records_csv as v917_write_other_records_csv,
    write_interaction_log_csv as v917_write_interaction_log_csv,
)
# v9.15: Self-Divergence Tracker (A-side, read-only)
from v917_divergence_tracker import (
    compute_class_divergence as v915_compute_class_divergence,
    write_class_divergence_csv as v915_write_class_divergence_csv,
    write_divergence_log_csv as v915_write_divergence_log_csv,
)
# v9.17 段階 4 新規: CidView (B-side) + InteractionLog (A-side、外部記録器)
from v917_cid_view import build_cid_view as v917_build_cid_view
from v917_interaction_log import InteractionLog as V917InteractionLog

# v9.18 段階 5 新規: per_step orchestrator + window CSV writer
from v101_orchestrator import (
    v918_update_per_step,
    v918_snapshot_window,
    v918_finalize_all_at_tracking_end,
    build_v918_subject_columns,
    write_v18_window_trajectory_csv,
)


# ================================================================
# CONSTANTS
# ================================================================
ATTENTION_DECAY = 0.99
FAMILIARITY_DECAY = 0.998
EPS = 1e-6
CONVERGENCE_THRESHOLD = 0.3
N_REPRESENTATIVES = 8

# v10.1 Minimal Ingestion: GHOST_TTL is removed.
# Ghost lifetime is now Q-based: ghost is reaped when residual_Q == 0.
# residual_Q is inherited from cid.Q_remaining at detach time, then decremented
# by ingestion events. See SubjectLayer.attempt_ingestion / reap_ghosts_step.

# ─────────────────────────────────────────────────────────────────
# v9.10 Pulse Model constants (exploration build, fixed values)
# ─────────────────────────────────────────────────────────────────
# spec 2.1 / 2.3 / 2.5: deterministic pulse timing, K=20 history,
# MAD-DT with R threshold 1.0, cold start for first 3 pulses.
# All values fixed; do not vary per cid.
PULSE_INTERVAL = 50       # spec 2.1
K_PULSE = 20              # spec 2.3
R_THRESHOLD = 1.0         # spec 2.4
EPS_PULSE = 1e-6          # spec 2.3
COLD_START_PULSES = 3     # spec 2.5 (pulses <=3 → unformed, >=4 → active)

V10_AXES = ("social", "stability", "spread", "familiarity")


# ─────────────────────────────────────────────────────────────────
# v9.11 Cognitive Capture constants (exploration build)
# 指示書 §2 / Rev 2 §3, §5, §6 + Taka §12 確定 (2026-04-14)
# ─────────────────────────────────────────────────────────────────
# capture probability (GPT 補正 1: Variant A, p = p_max * exp(-λ Δ))
V11_P_MAX = 0.9             # 最大捕捉確率 (<1.0, 「取りこぼしあり」)
V11_LAMBDA = 2.724          # Δ p50 基準で再決定 (smoke n=150 eval pulses)
                            # 根拠: v911_capture_param_audit.md
                            # 履歴: 2.0 (暫定) → 2.724 (p50 基準、2026-04-14 Taka 承認)

# similarity 重み (GPT 補正 3: 均等初期値、合計 1.0)
V11_W_N = 0.25
V11_W_S = 0.25
V11_W_R = 0.25
V11_W_PHASE = 0.25

# 正規化定数 (Taka §12-3 確定 + Step 0 norm audit 結果)
# V11_NORM_N: norm audit (seed=0, 20mat × 5track × 500step) で n_local 実測 p95 = 86.05
#   → floor(p95) = 86 を採用 (v911_norm_audit_result.md に根拠)
V11_NORM_N = 86             # Step 0 audit で確定 (元: None ガード)
V11_NORM_S = 1.0            # 固定 (S_avg ∈ [0,1] 前提)
V11_NORM_R = 1.0            # 固定 (r_core ∈ [0,1] 前提)
# Δ_phase は circular_diff / π で正規化 (§4.2、[0,1])

# Perception Field (Rev 2 §6.5)
V11_PF_HOPS_FACTOR = 1      # max_hops = n_core × factor
                            # = 1 で v9.10 既存 struct_set と同一条件
                            # 実装では既存 struct_set を流用 (二重計算回避)

# Cold start: pulse <=3 は E_t 抽出・Δ計算・p_capture 計算は実行するが
# capture 判定は保留し、pulse_log には "cold_start" で記録、
# per_subject の集計 (n_pulses_eval / n_captured) には含めない。
# B_Gen / M_c は birth 時固定なので cold_start と無関係に記録される。
# COLD_START_PULSES = 3 は v9.10 から継承 (上記の COLD_START_PULSES 定数)。
V11_CAPTURE_COLD_START_SKIP = True

# ═══════════════════════════════════════════════════════════════════════
# v9.13 Step 0: Persistence Audit constants
# ═══════════════════════════════════════════════════════════════════════

# Shadow component 分析用の候補閾値 (step 単位)
# 各 window 末に「age_r >= τ のリンクで連結成分を作ったら何が出るか」を
# 仮想的に計算する (実 birth 判定には影響しない)
V913_SHADOW_THRESHOLDS = [50, 100, 200, 300, 400, 500]

# Shadow 分析で記録する最小 component サイズ (2 ノード未満は集計しない)
V913_SHADOW_MIN_SIZE = 2

# Step 0 audit 完了前に実装を走らせないガード (実装中の凡ミス防止)
if V11_NORM_N is None:
    raise RuntimeError(
        "V11_NORM_N is not set. Run Step 0 audit (v911_norm_audit.py) first "
        "and update the constant based on n_local p95.")


def v10_is_pulse(t, cid, interval=PULSE_INTERVAL):
    """v9.10 deterministic pulse test (spec 2.1).
    No RNG. No per-cid override. t is the cumulative tracking step."""
    return (t % interval) == (cid % interval)


# ─────────────────────────────────────────────────────────────────
# Introspection thresholds (v9.8b, Stage 1)
# ─────────────────────────────────────────────────────────────────
# v9.8b 機能を v9.8c でも維持するため、ここで定義する。
# PROVISIONAL ENGINEERING VALUES.
INTROSPECTION_THRESHOLD_SOCIAL = 0.1
INTROSPECTION_THRESHOLD_STABILITY = 0.1
INTROSPECTION_THRESHOLD_SPREAD = 0.1
INTROSPECTION_THRESHOLD_FAMILIARITY = 2.0

# ─────────────────────────────────────────────────────────────────
# v10.1 Minimal Ingestion: pickup mechanism (v9.8c) is fully retired.
# INFORMATION_LIFETIME / AFFINITY_THRESHOLD / TTL_BONUS_PER_PICKUP all
# removed. record_death / attempt_pickup_round / cleanup_death_pool
# methods are likewise removed from SubjectLayer. Ghost lifetime is now
# governed by residual_Q, not by TTL bonus accumulation.
# ─────────────────────────────────────────────────────────────────
# v10.1 RNG seed magic for ingestion (1 CID : 多 ghost ランダム選定)
# Convention follows v9.11 capture_rng (seed ^ 0xC0FFEE).
INGESTION_RNG_SEED_MAGIC = 0x1A7E57   # seed ^ this for ingestion RNG


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
        self.prev_disposition = {}       # cid -> {social, stability, spread, familiarity}
        self.current_disposition = {}    # cid -> {social, stability, spread, familiarity}
        self.introspection_tags = {}     # cid -> [tag strings]

        # ──────────────────────────────────────────────
        # v10.1 Minimal Ingestion: ghost residual_Q
        # ──────────────────────────────────────────────
        # ghost_residual_Q[cid]: 残存 Q (ingestion で減る、0 で reap 対象)
        # ghost_residual_Q_initial[cid]: ghost 化時点の Q_remaining (不変、観察用)
        # ghost_q_lost_at_step[cid]: ghost 化した cumulative_step (寿命統計用)
        # 全 dict は detach 時に登録、reap_ghosts_step で pop。
        self.ghost_residual_Q = {}
        self.ghost_residual_Q_initial = {}
        self.ghost_q_lost_at_step = {}

        # 統計用
        # reaped_history は v10.1 で項目を改訂:
        #   ghost_dur_steps (step 単位、step 末 reap)、initial_residual_Q、
        #   final_residual_Q (常に 0)、reason ("residual_Q_zero")
        self._reaped_history = []
        self._tag_history = []     # [{cid, window, prev, current, delta, tags, state}]
        # v10.1 摂食ログ (raw)
        self._ingestion_log = []   # [{step, observer, ghost, gain, received, digested, was_empty, was_phantom, q_remaining_before, q_remaining_after, residual_Q_before, residual_Q_after}]

        # ──────────────────────────────────────────────
        # v9.9: 内的基準軸の骨格 (構造語のみ、GPT 監査確定事項)
        # ──────────────────────────────────────────────
        # cid は履歴を読まない、書き込みのみ。loop は閉じない。
        # すべて SubjectLayer 内部の dict 操作、engine.state には触れない。
        self.recent_tags = {}             # cid -> deque[frozenset], maxlen=5
        self.recent_dispositions = {}     # cid -> deque[dict], maxlen=5
        self.personal_range = {}          # cid -> {axis: {min,max,mean,std}} | {}
        self.drift = {}                   # cid -> {axis: {positive_count,negative_count,neutral_count}} | {}
        self.formation_status = {}        # cid -> "unformed" | "formed"
        self.lowest_std_axis = {}                   # cid -> str
        self.dominant_positive_drift_axis = {}      # cid -> str
        self.dominant_negative_drift_axis = {}      # cid -> str

        # ──────────────────────────────────────────────
        # v9.10: Pulse Model & Subjective Surprise (MAD-DT)
        # ──────────────────────────────────────────────
        # All v10_ state is independent from v99_/v98b state.
        # Never touch v99_* dicts here; they are frozen (spec 3.1).
        # re-host: do NOT reset history (spec 2.6).
        # reap: pop all v10_* dicts (below, in reap_ghosts).
        # ghost: pulse判定スキップ、履歴そのまま保持 (spec 2.6).
        self.v10_pulse_count = {}               # cid -> int (total pulses fired)
        self.v10_last_disp = {}                 # cid -> {axis: float} last pulse snapshot
        self.v10_delta_history = {}             # cid -> {axis: deque[float] maxlen=K}
        self.v10_R_history = {}                 # cid -> {axis: deque[float] maxlen=K}
        self.v10_theta_last = {}                # cid -> {axis: float} (mean|delta|)
        self.v10_R_last = {}                    # cid -> {axis: float} (last R)
        self.v10_R_max_seen = {}                # cid -> {axis: float} (running max over K window)
        self.v10_R_min_seen = {}                # cid -> {axis: float} (running min over K window)
        self.v10_pulse_tags = {}                # cid -> deque[frozenset] maxlen=K
        self.v10_pulse_dispositions = {}        # cid -> deque[dict] maxlen=K
        self.v10_tag_trigger_last = {}          # cid -> str
        self.v10_n_normal = {}                  # cid -> int (cumulative normal tags emitted)
        self.v10_n_major = {}                   # cid -> int (cumulative major tags emitted)

        # ──────────────────────────────────────────────
        # v9.11: Cognitive Capture state (指示書 §3)
        # B_Gen と M_c は birth 時固定。E_t / Δ / capture は pulse 時更新。
        # 集計は cold_start 除く判定済み pulse のみ。
        # 既存 v10_/v99_ 状態には触れない。reap で全削除。
        # ──────────────────────────────────────────────
        # birth 時固定 (cid 単位、1 回のみ記録)
        self.v11_b_gen = {}              # cid -> float ("inf" 含む) or "unformed"
        self.v11_m_c = {}                # cid -> dict {n_core, s_avg, r_core, phase_sig}
        self.v11_born_links_total = {}   # cid -> int (birth 時 links_total、参考値)

        # pulse 時更新 (cid 単位、pulse ごとに上書き)
        self.v11_last_e_t = {}           # cid -> dict {n_local, s_avg_local, r_local, theta_avg_local}
        self.v11_last_delta = {}         # cid -> float
        self.v11_last_delta_axes = {}    # cid -> dict {n, s, r, phase}
        self.v11_last_p_capture = {}     # cid -> float
        self.v11_last_captured = {}      # cid -> "TRUE" / "FALSE" / "cold_start"

        # 集計 (cid 単位、per_subject CSV 用、cold_start 除く)
        self.v11_n_pulses_eval = {}      # cid -> int
        self.v11_n_captured = {}         # cid -> int
        self.v11_sum_delta = {}          # cid -> float
        self.v11_sum_delta_axes = {}     # cid -> dict {n, s, r, phase}

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
        # v10.1 Minimal Ingestion: pickup state は廃止 (cid_ttl_bonus 削除)。
        # ghost_residual_Q は detach 時に登録 (birth では未登録)。

        # v9.9: 内的基準軸
        self.recent_tags[cid] = deque(maxlen=5)
        self.recent_dispositions[cid] = deque(maxlen=5)
        self.personal_range[cid] = {}
        self.drift[cid] = {}
        self.formation_status[cid] = "unformed"
        self.lowest_std_axis[cid] = "unformed"
        self.dominant_positive_drift_axis[cid] = "unformed"
        self.dominant_negative_drift_axis[cid] = "unformed"

        # v9.10: Pulse Model state
        self.v10_pulse_count[cid] = 0
        self.v10_last_disp[cid] = None
        self.v10_delta_history[cid] = {a: deque(maxlen=K_PULSE) for a in V10_AXES}
        self.v10_R_history[cid] = {a: deque(maxlen=K_PULSE) for a in V10_AXES}
        self.v10_theta_last[cid] = {a: 0.0 for a in V10_AXES}
        self.v10_R_last[cid] = {a: 0.0 for a in V10_AXES}
        self.v10_R_max_seen[cid] = {a: float("-inf") for a in V10_AXES}
        self.v10_R_min_seen[cid] = {a: float("inf") for a in V10_AXES}
        self.v10_pulse_tags[cid] = deque(maxlen=K_PULSE)
        self.v10_pulse_dispositions[cid] = deque(maxlen=K_PULSE)
        self.v10_tag_trigger_last[cid] = "unformed"
        self.v10_n_normal[cid] = 0
        self.v10_n_major[cid] = 0

        # v9.11: Cognitive Capture state
        # B_Gen / M_c は main ループ側で measure_birth_stats を呼んで記録 (§3.4)
        # ここでは集計用 dict を初期化しておく (n_core < 2 で B_Gen 未記録でも安全)
        self.v11_n_pulses_eval[cid] = 0
        self.v11_n_captured[cid] = 0
        self.v11_sum_delta[cid] = 0.0
        self.v11_sum_delta_axes[cid] = {"n": 0.0, "s": 0.0, "r": 0.0, "phase": 0.0}

        return cid

    def detach(self, lid, current_window, residual_Q=0, current_step=None):
        """label が cull された時に呼ぶ。cid データは消さない。
        cog データはそのまま残り、current_lid[cid] = None になる。

        v10.1 Minimal Ingestion:
          residual_Q: ghost 化時点の Q_remaining (Layer B から caller が読む)。
                      この値が ghost_residual_Q / _initial に登録される。
                      0 を渡せば "認知層既に枯渇" の ghost として扱われ
                      次 step 末に即 reap される (空 ghost、先食いされない)。
          current_step: ghost 化した cumulative_step (寿命統計用)。
                        None なら window 末 step として current_window を使う。
        """
        cid = self.cid_of_lid.pop(lid, None)
        if cid is None:
            return None
        self.current_lid[cid] = None
        self.host_lost_at[cid] = current_window
        # v10.1: residual_Q snapshot
        rq = int(residual_Q)
        self.ghost_residual_Q[cid] = rq
        self.ghost_residual_Q_initial[cid] = rq
        self.ghost_q_lost_at_step[cid] = (
            int(current_step) if current_step is not None else int(current_window))
        return cid

    def reap_ghosts_step(self, current_step):
        """v10.1 Minimal Ingestion: residual_Q == 0 の ghost cid を完全削除。
        毎 step (per-step orchestrator ループ末尾) で呼ぶ。

        Returns: 削除された cid のリスト。
        """
        reaped = []
        for cid in list(self.ghost_residual_Q.keys()):
            if self.ghost_residual_Q[cid] != 0:
                continue
            # 防御的: ghost でない場合は触らない (残存 cid は ingestion ロジックの bug)
            if self.current_lid.get(cid) is not None:
                continue
            lost_w = self.host_lost_at.get(cid)
            lost_step = self.ghost_q_lost_at_step.get(cid)
            initial_q = self.ghost_residual_Q_initial.get(cid, 0)
            ghost_dur_steps = (
                (current_step - lost_step) if lost_step is not None else None)
            self._reaped_history.append({
                "cid": cid,
                "born": self.born_at.get(cid),
                "host_lost_window": lost_w,
                "host_lost_step": lost_step,
                "reaped_step": current_step,
                "ghost_duration_steps": ghost_dur_steps,
                "initial_residual_Q": initial_q,
                "final_residual_Q": 0,
                "reap_reason": "residual_Q_zero",
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
            # v9.9: 内的基準軸のクリーンアップ
            self.recent_tags.pop(cid, None)
            self.recent_dispositions.pop(cid, None)
            self.personal_range.pop(cid, None)
            self.drift.pop(cid, None)
            self.formation_status.pop(cid, None)
            self.lowest_std_axis.pop(cid, None)
            self.dominant_positive_drift_axis.pop(cid, None)
            self.dominant_negative_drift_axis.pop(cid, None)
            # v9.10: Pulse Model state cleanup (reap = 履歴破棄)
            self.v10_pulse_count.pop(cid, None)
            self.v10_last_disp.pop(cid, None)
            self.v10_delta_history.pop(cid, None)
            self.v10_R_history.pop(cid, None)
            self.v10_theta_last.pop(cid, None)
            self.v10_R_last.pop(cid, None)
            self.v10_R_max_seen.pop(cid, None)
            self.v10_R_min_seen.pop(cid, None)
            self.v10_pulse_tags.pop(cid, None)
            self.v10_pulse_dispositions.pop(cid, None)
            self.v10_tag_trigger_last.pop(cid, None)
            self.v10_n_normal.pop(cid, None)
            self.v10_n_major.pop(cid, None)
            # v10.1: ghost residual_Q state cleanup
            self.ghost_residual_Q.pop(cid, None)
            self.ghost_residual_Q_initial.pop(cid, None)
            self.ghost_q_lost_at_step.pop(cid, None)
            # v9.11: Cognitive Capture state cleanup
            self.v11_b_gen.pop(cid, None)
            self.v11_m_c.pop(cid, None)
            self.v11_born_links_total.pop(cid, None)
            self.v11_last_e_t.pop(cid, None)
            self.v11_last_delta.pop(cid, None)
            self.v11_last_delta_axes.pop(cid, None)
            self.v11_last_p_capture.pop(cid, None)
            self.v11_last_captured.pop(cid, None)
            self.v11_n_pulses_eval.pop(cid, None)
            self.v11_n_captured.pop(cid, None)
            self.v11_sum_delta.pop(cid, None)
            self.v11_sum_delta_axes.pop(cid, None)
            reaped.append(cid)
        return reaped

    # ──────────────────────────────────────────────────────
    # v10.1 Minimal Ingestion: 摂食実行本体
    # ──────────────────────────────────────────────────────
    def attempt_ingestion(self, observer_cid, ghost_cid, ledger):
        """observer_cid (hosted) が ghost_cid を摂食する試行。

        前提:
          - observer_cid は hosted、ghost_cid は ghost (caller が保証)
          - observer_cid と ghost_cid のペアは E3 onset を発火済み (caller 保証)
          - ledger は SpendAuditLedger (Layer B)、observer の Q_remaining 更新先

        段階 1 仕様 (v10.1):
          - gain = ghost.residual_Q (1 step に 1 ghost を食べきる)
          - received = min(gain, Q0_observer - Q_remaining_observer) (Q0 上限)
          - digested = gain - received (Q0 で頭打ちした分、消える)
          - ghost.residual_Q -= gain (常に減る、消化分含む)
          - 飢餓判定なし (Q_remaining_observer < Q0 の判定撤廃、満腹でも摂食可)

        Returns: dict {gain, received, digested, was_empty,
                       residual_Q_before, residual_Q_after,
                       q_remaining_before, q_remaining_after} or None
                 None が返るのは ghost_cid が ghost_residual_Q に居ないケース
                 (= phantom contact、reap 済または未登録)。
                 caller (Layer B observe_step) で phantom log を別途記録。
        """
        if ghost_cid not in self.ghost_residual_Q:
            # phantom: 認知層では既に消滅した cid への接触
            return None
        residual_before = self.ghost_residual_Q[ghost_cid]
        gain = int(residual_before)
        # observer の Q0 / Q_remaining を ledger から読む
        received, q_before, q_after = ledger.add_q(observer_cid, gain)
        digested = gain - received
        # ghost の residual_Q を gain 全分減らす (消化分含む、常に減る)
        residual_after = residual_before - gain
        self.ghost_residual_Q[ghost_cid] = residual_after
        return {
            "gain": gain,
            "received": int(received),
            "digested": int(digested),
            "was_empty": (gain == 0),
            "residual_Q_before": int(residual_before),
            "residual_Q_after": int(residual_after),
            "q_remaining_before": int(q_before),
            "q_remaining_after": int(q_after),
        }

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

    # ──────────────────────────────────────────────────────
    # v9.10 Pulse Model — MAD-DT subjective surprise
    # ──────────────────────────────────────────────────────
    def on_pulse(self, cid, d_social, d_stability, d_spread, d_familiarity, t, window):
        """v9.10: pulse 発火時に呼ぶ。4 軸の値は呼び出し側で
        既に計算済み (v9.8b と同じ式、愚直計算)。
        ghost: 呼び出し側で is_hosted ガード、ここには来ない。
        re-host: 履歴はそのまま (dict 初期化は birth のみ)。
        Returns: pulse_event dict or None (unformed でログ不要なら)
        """
        if not self.is_hosted(cid):
            return None  # spec 2.6: ghost は pulse 判定スキップ

        self.v10_pulse_count[cid] += 1
        pulse_n = self.v10_pulse_count[cid]

        curr = {"social": float(d_social),
                "stability": float(d_stability),
                "spread": float(d_spread),
                "familiarity": float(d_familiarity)}

        self.v10_pulse_dispositions[cid].append(dict(curr))

        last = self.v10_last_disp.get(cid)
        deltas = {a: 0.0 for a in V10_AXES}
        if last is not None:
            for a in V10_AXES:
                deltas[a] = curr[a] - last[a]
                self.v10_delta_history[cid][a].append(abs(deltas[a]))
        self.v10_last_disp[cid] = curr

        # spec 2.5: pulse <=3 は unformed、タグ生成・R 計算なし
        # pulse_tags に push しない (spec 2.5 明記)
        # delta_history は積む (3 回目以降 theta 計算可能にするため)
        if pulse_n <= COLD_START_PULSES:
            self.v10_tag_trigger_last[cid] = "unformed"
            return {
                "pulse_n": pulse_n, "t": t, "window": window,
                "curr": curr, "deltas": deltas,
                "theta": {a: 0.0 for a in V10_AXES},
                "R": {a: 0.0 for a in V10_AXES},
                "tags": [], "trigger": "unformed",
            }

        # spec 2.3: theta = mean(|delta|), R = delta / (theta + EPS)
        theta = {}
        R = {}
        for a in V10_AXES:
            dh = self.v10_delta_history[cid][a]
            if len(dh) == 0:
                theta[a] = 0.0
            else:
                theta[a] = sum(dh) / len(dh)
            R[a] = deltas[a] / (theta[a] + EPS_PULSE)

        self.v10_theta_last[cid] = theta
        self.v10_R_last[cid] = R

        # spec 2.4: Normal と Major を併存判定
        tags = []
        is_normal = False
        is_major = False
        for a in V10_AXES:
            r = R[a]
            # Normal
            if r > R_THRESHOLD:
                tags.append("gain_" + a)
                is_normal = True
            elif r < -R_THRESHOLD:
                tags.append("loss_" + a)
                is_normal = True
            # Major (R_max/R_min update detection)
            # Compare BEFORE pushing current R to R_history,
            # so "update" means beating previous K window's extremes.
            # Skip Major check when R_history is empty (first active pulse
            # has nothing to beat against → no spurious Major).
            if len(self.v10_R_history[cid][a]) > 0:
                prev_max = self.v10_R_max_seen[cid][a]
                prev_min = self.v10_R_min_seen[cid][a]
                if r > prev_max:
                    tags.append("major_gain_" + a)
                    is_major = True
                if r < prev_min:
                    tags.append("major_loss_" + a)
                    is_major = True

        # Update R history and running max/min over the K=20 window
        for a in V10_AXES:
            self.v10_R_history[cid][a].append(R[a])
            # recompute running max/min from the current K window
            rh = self.v10_R_history[cid][a]
            self.v10_R_max_seen[cid][a] = max(rh)
            self.v10_R_min_seen[cid][a] = min(rh)

        # Compose trigger label
        if is_normal and is_major:
            trig = "both"
        elif is_normal:
            trig = "MAD_DT_Normal"
        elif is_major:
            trig = "MAD_DT_Major"
        else:
            trig = "none"
        self.v10_tag_trigger_last[cid] = trig

        if is_normal:
            self.v10_n_normal[cid] += 1
        if is_major:
            self.v10_n_major[cid] += 1

        self.v10_pulse_tags[cid].append(frozenset(tags))

        return {
            "pulse_n": pulse_n, "t": t, "window": window,
            "curr": curr, "deltas": deltas,
            "theta": theta, "R": R,
            "tags": tags, "trigger": trig,
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

        # ──────────────────────────────────────────────
        # v9.9: 内的基準軸の骨格更新 (hook point)
        # GPT 監査確定事項:
        #   1. drift は累積禁止、毎回 recent_tags から再構築
        #   2. deterministic rules (tie / unformed / none)
        #   3. 一次出力は構造語のみ
        # ghost / prev None は関数先頭で早期 return 済み
        # ──────────────────────────────────────────────
        self.recent_tags[cid].append(frozenset(tags))
        self.recent_dispositions[cid].append({
            "social": curr["social"],
            "stability": curr["stability"],
            "spread": curr["spread"],
            "familiarity": curr["familiarity"],
        })

        n = len(self.recent_dispositions[cid])

        # Rule 1: len < 3 は unformed
        if n < 3:
            self.formation_status[cid] = "unformed"
            self.lowest_std_axis[cid] = "unformed"
            self.dominant_positive_drift_axis[cid] = "unformed"
            self.dominant_negative_drift_axis[cid] = "unformed"
            self.personal_range[cid] = {}
            self.drift[cid] = {}
            return tags

        self.formation_status[cid] = "formed"

        # personal_range 再計算 (毎 window 末)
        axes = ("social", "stability", "spread", "familiarity")
        pr = {}
        for axis in axes:
            vals = [d[axis] for d in self.recent_dispositions[cid]]
            mean = sum(vals) / len(vals)
            var = sum((v - mean) ** 2 for v in vals) / len(vals)
            pr[axis] = {
                "min": min(vals),
                "max": max(vals),
                "mean": mean,
                "std": var ** 0.5,
            }
        self.personal_range[cid] = pr

        # drift の再構築 (★累積禁止: ゼロリセット)
        dr = {axis: {"positive_count": 0, "negative_count": 0, "neutral_count": 0}
              for axis in axes}
        for tag_set in self.recent_tags[cid]:
            for axis in axes:
                if ("gain_" + axis) in tag_set:
                    dr[axis]["positive_count"] += 1
                elif ("loss_" + axis) in tag_set:
                    dr[axis]["negative_count"] += 1
                else:
                    dr[axis]["neutral_count"] += 1
        self.drift[cid] = dr

        # Rule 2: lowest_std_axis (epsilon 判定)
        EPS = 1e-9
        stds = [(a, pr[a]["std"]) for a in axes]
        min_std = min(s for _, s in stds)
        min_axes = [a for a, s in stds if abs(s - min_std) < EPS]
        self.lowest_std_axis[cid] = min_axes[0] if len(min_axes) == 1 else "tie"

        # Rule 3: dominant_positive_drift_axis (整数厳密一致)
        pos = [(a, dr[a]["positive_count"]) for a in axes]
        mp = max(c for _, c in pos)
        mpa = [a for a, c in pos if c == mp]
        if mp == 0:
            self.dominant_positive_drift_axis[cid] = "none"
        elif len(mpa) == 1:
            self.dominant_positive_drift_axis[cid] = mpa[0]
        else:
            self.dominant_positive_drift_axis[cid] = "tie"

        neg = [(a, dr[a]["negative_count"]) for a in axes]
        mn = max(c for _, c in neg)
        mna = [a for a, c in neg if c == mn]
        if mn == 0:
            self.dominant_negative_drift_axis[cid] = "none"
        elif len(mna) == 1:
            self.dominant_negative_drift_axis[cid] = mna[0]
        else:
            self.dominant_negative_drift_axis[cid] = "tie"

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

    # ──────────────────────────────────────────────────────
    # v10.1 Minimal Ingestion: pickup 機構 (v9.8c) は完全廃止。
    # record_death / cleanup_death_pool / attempt_pickup_round は削除。
    # GHOST_TTL / cid_ttl_bonus / death_pool / pickup_log も削除。
    # ──────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────
# Helper: circular phase distance
# ────────────────────────────────────────────────────────────────
def _circular_diff(a, b):
    """円位相の差を [-π, π] に正規化して返す。
    abs(returned) が真の距離。"""
    diff = a - b
    while diff > math.pi:
        diff -= 2 * math.pi
    while diff < -math.pi:
        diff += 2 * math.pi
    return diff


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


# ─────────────────────────────────────────────────────────────────
# v9.11: Cognitive Capture helpers (指示書 §3.4, §4)
# ─────────────────────────────────────────────────────────────────
def v11_compute_b_gen(n_core, s_avg, r_core, links_total, n_total):
    """B_Gen = -log10(Pbirth) を計算。
    n_core < 2 や Pbirth=0 のケースは float('inf') 相当の扱い。
    指示書 §3.4 の式: Pbirth = (1/C(N,n)) * rho^(n-1) * r^(n-1) * s^(n-1)
    """
    if n_core < 2:
        return float("inf"), None  # unformed
    rho = links_total / (n_total * (n_total - 1) / 2)
    exp = n_core - 1
    c_n_nc = math.comb(n_total, n_core)
    if c_n_nc == 0 or rho <= 0 or r_core <= 0 or s_avg <= 0:
        pbirth = 0.0
    else:
        pbirth = (1.0 / c_n_nc) * (rho ** exp) * (r_core ** exp) * (s_avg ** exp)
    if pbirth <= 0:
        return float("inf"), pbirth
    return -math.log10(pbirth), pbirth


def v11_record_birth_metrics(cog, engine_state, lab, lid):
    """Birth 直後に呼び、B_Gen と M_c を cog に記録 (cid 単位、1 回のみ)。
    重複呼び出し対応: 既に記録済みの cid はスキップ。
    n_core < 2 の場合は v11_b_gen=float('inf') を記録 (Pbirth 計算不能)。
    指示書 §3.4 の処理を関数化したもの (4 ヶ所の cog.birth() 後で呼ぶ)。
    """
    cid = cog.cid_of_lid.get(lid)
    if cid is None:
        return
    if cid in cog.v11_b_gen:
        return  # 既に記録済み (重複呼び出し対応)
    n_core, s_avg, r_core = measure_birth_stats(engine_state, lab["nodes"])
    links_total = len(engine_state.alive_l)
    b_gen, _pbirth = v11_compute_b_gen(
        n_core, s_avg, r_core, links_total, V82_N)
    cog.v11_b_gen[cid] = b_gen
    cog.v11_m_c[cid] = {
        "n_core": int(n_core),
        "s_avg": float(s_avg),
        "r_core": float(r_core),
        "phase_sig": float(lab["phase_sig"]),
    }
    cog.v11_born_links_total[cid] = int(links_total)


def v917_q0_from_cog(cog, cid) -> int:
    """v9.16 段階 3: cid の生誕時 Q0 = floor(B_Gen) を返す。
    v11_record_birth_metrics 後の cog.v11_b_gen から取得。
    b_gen=inf / <=0 / 欠損の cid は Q0=0 (age_factor 常に 0)。
    """
    if cid is None:
        return 0
    b_gen = cog.v11_b_gen.get(cid)
    if b_gen is None or not math.isfinite(b_gen) or b_gen <= 0:
        return 0
    return int(math.floor(b_gen))


def v917_parse_contacted_cid(link_id: str):
    """
    v9.17 段階 4: Layer B の E3_contact event の link_id 文字列から
    相手 cid_id を抽出する。

    link_id format (v914_spend_audit_ledger.py:210 参照):
        E1 / E2: "(i,j)"  — 物理リンク文字列
        E3_contact: "cid<ID>|(i,j)" — 相手 cid + 物理リンク

    Returns
    -------
    int または None:
      E3 形式でなければ (あるいは parse 失敗) None。
      呼び出し側は None を skip する前提。

    Layer B は frozen copy のため、link_id 文字列を介して相手 cid を取得する
    (Q4 Taka 回答 2026-04-22)。B 側 (v917_cid_self_buffer) に parsing を
    持ち込まず、main loop 側 ([A] 寄り) に閉じる。
    """
    if not isinstance(link_id, str) or not link_id.startswith("cid"):
        return None
    pipe_idx = link_id.find("|")
    if pipe_idx < 4:  # "cid" + at least 1 digit + "|"
        return None
    try:
        return int(link_id[3:pipe_idx])
    except ValueError:
        return None


def v11_compute_e_t(state, struct_set, phase_sig):
    """Pulse 時の現在経験 E_t を抽出 (n_local, s_avg_local, r_local, theta_avg_local)。
    既存 struct_set を流用 (V11_PF_HOPS_FACTOR=1 なので同一)。
    structural_stats は len(struct_set)<2 で (phase_sig, 0.0) を返す。
    """
    n_local = len(struct_set)
    mean_theta_local, s_avg_local = structural_stats(state, struct_set, phase_sig)
    if n_local >= 2:
        sin_s = sum(math.sin(float(state.theta[n])) for n in struct_set)
        cos_s = sum(math.cos(float(state.theta[n])) for n in struct_set)
        r_local = math.sqrt(sin_s ** 2 + cos_s ** 2) / n_local
    elif n_local == 1:
        r_local = 1.0
    else:
        r_local = 0.0
    return {
        "n_local": n_local,
        "s_avg_local": float(s_avg_local),
        "r_local": float(r_local),
        "theta_avg_local": float(mean_theta_local),
    }


def v11_compute_delta(m_c, e_t):
    """差分分解型 Weighted L1 Δ を計算。phase は circular distance / π で正規化。
    Returns: (delta_total, axes_dict)
    """
    d_n = abs(m_c["n_core"] - e_t["n_local"]) / V11_NORM_N
    d_s = abs(m_c["s_avg"] - e_t["s_avg_local"]) / V11_NORM_S
    d_r = abs(m_c["r_core"] - e_t["r_local"]) / V11_NORM_R
    d_phase_raw = circular_diff(m_c["phase_sig"], e_t["theta_avg_local"])
    d_phase = abs(d_phase_raw) / math.pi
    delta = (V11_W_N * d_n + V11_W_S * d_s
             + V11_W_R * d_r + V11_W_PHASE * d_phase)
    return delta, {"n": d_n, "s": d_s, "r": d_r, "phase": d_phase}


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=10,
        window_steps=500, tag="short", disable_e3=False):

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    outdir = Path(f"diag_v101_{tag}")
    outdir.mkdir(exist_ok=True)
    for sub in ["aggregates", "labels", "subjects",
                "representatives", "network", "introspection", "pickup",
                "pulse",
                "persistence",  # v9.13 Step 0: persistence CSV output
                "selfread"]:    # v9.15: CID self-buffer output
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

    # v9.11: capture 専用 RNG (engine.rng と分離。
    # per_window CSV の bit identical を壊さないため独立 seed)
    capture_rng = np.random.default_rng(seed ^ 0xC0FFEE)

    engine.run_injection()

    # ═══════════════════════════════════════════════════════════════════════
    # v9.13 Step 0: Persistence tracking state
    # ═══════════════════════════════════════════════════════════════════════
    v913_age_r = {}                 # link -> 連続 R>0 step 数 (R=0 でリセット)
    v913_max_age_r = {}             # link -> 生涯最大 age_r (単調増加)
    v913_birth_step_of_link = {}    # link -> 初めて alive_l に加わった step
    v913_prev_alive_l = set()       # 前 step の alive_l (差分検出用)
    v913_link_life_log = []         # リンク死亡時に append
    v913_link_snapshot_log = []     # window 末に append
    v913_label_member_persistence = []  # label birth 時に append
    v913_shadow_component_log = []  # window 末に append
    v913_global_step = 0            # maturation + tracking を通じた step カウンタ

    # v10.1 Minimal Ingestion: ingestion 用 RNG (engine.rng / capture_rng と分離)
    # 1 CID : 多 ghost のランダム選定にのみ使用。bit-identity 維持のため
    # 既存 RNG ストリームは一切 touch しない。
    ingestion_rng = np.random.default_rng(seed ^ INGESTION_RNG_SEED_MAGIC)

    # v9.14 Step 1-3: Layer B ledger (audit-only, Layer A を一切触らない)
    # delta 計算は v11_compute_delta を注入 (Layer A と同じ 4-軸 weighted L1)
    # v10.1: cog / ingestion_rng を渡して摂食機構を有効化
    v914_ledger = SpendAuditLedger(
        delta_fn=v11_compute_delta, disable_e3=disable_e3,
        cog=cog, ingestion_rng=ingestion_rng)

    # v9.15: Layer C (CID self-buffer registry)
    # cid -> CidSelfBuffer。Lazy Registration で cid birth 直後に生成、
    # 段階 2 では v9.14 Layer B の event 発火直後に read_on_event を呼ぶ。
    # 既存 Layer A / Layer B / baseline CSV への影響はゼロ (additive-only)。
    v915_self_buffers: dict = {}

    # v9.17 段階 4: Interaction Log (接触体候補の外部記録器、seed ごとに 1 個)
    # CID は本インスタンスを参照しない。main loop が E3_contact pair に対して
    # canonical ordering dedup (observer_cid < contacted_cid) のときだけ
    # record_contact を呼ぶ (Q3 Taka 回答 2026-04-22)。
    # 既存 Layer A / Layer B / v9.15 / v9.16 baseline への影響はゼロ。
    v917_interaction_log = V917InteractionLog()

    # v9.18 段階 5: per_cid × per_window の v18_* 軌跡 accumulator
    # window 末に v918_snapshot_window が append、最終 CSV に出力。
    v918_window_accumulator: list = []

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
            # v9.11: Birth 時 B_Gen / M_c 固定記録 (§3.4)
            v11_record_birth_metrics(cog, engine.state, lab, lid)
            # v9.15: Lazy Registration for self-buffer (Layer C)
            v915_ensure_cid_registered(
                v915_self_buffers, cog.cid_of_lid.get(lid),
                lab["nodes"], engine.state, v913_global_step,
                Q0=v917_q0_from_cog(cog, cog.cid_of_lid.get(lid)))
        # Ensure existing (in case of init edge cases)
        for lid in curr_lids:
            if lid not in cog.cid_of_lid:
                lab = engine.virtual.labels[lid]
                cog.birth(lid, lab["phase_sig"], w)
                # v9.11
                v11_record_birth_metrics(cog, engine.state, lab, lid)
                # v9.15
                v915_ensure_cid_registered(
                    v915_self_buffers, cog.cid_of_lid.get(lid),
                    lab["nodes"], engine.state, v913_global_step,
                    Q0=v917_q0_from_cog(cog, cog.cid_of_lid.get(lid)))

        # v10.1: maturation 中の reap (ledger 未登録 cid は detach で
        # residual_Q=0 になり、即 reap 対象)
        cog.reap_ghosts_step(w)

    # v9.13 Step 0: maturation 完了後に alive_l スナップショットを初期化
    # maturation 中は engine.step_window() 内で物理ステップが走るため
    # per-step の age_r 追跡はできない。tracking 開始時点を基準とする。
    v913_prev_alive_l = set(engine.state.alive_l)
    for k in v913_prev_alive_l:
        v913_birth_step_of_link[k] = v913_global_step  # maturation 末時点で birth と見なす

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
                # v9.11
                v11_record_birth_metrics(
                    cog, engine.state, vl.labels[lid], lid)
                # v9.15
                v915_ensure_cid_registered(
                    v915_self_buffers, cog.cid_of_lid.get(lid),
                    vl.labels[lid]["nodes"], engine.state, v913_global_step,
                    Q0=v917_q0_from_cog(cog, cog.cid_of_lid.get(lid)))

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

    # v9.10: cumulative tracking step counter (for pulse timing)
    # starts at 0 at the beginning of tracking phase
    cumulative_step = 0
    v10_pulse_log = []   # list of flattened pulse event dicts for CSV output

    # v9.11: per-step stash of struct_set per cid (for pulse-time E_t extraction).
    # 認知更新ループで書き込み、同一 step の pulse 発火ループで読む。
    v11_current_struct_set = {}   # cid -> set

    # ── Tracking Phase ──
    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # v10.1: 毎 step reap の累積カウンタを window 開始時にリセット
        _reaped_per_window_count = 0
        # window 開始時の ingestion / phantom event index (差分で window 単位の集計)
        _ingestion_count_at_window_start = len(v914_ledger.ingestion_events)
        _phantom_count_at_window_start = len(v914_ledger.phantom_contacts)

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

            # ═══════════════════════════════════════════════════════════════
            # v9.13 Step 0: age_r update (Resonance 直後 / Auto-Growth 前)
            # ═══════════════════════════════════════════════════════════════
            for k in engine.state.alive_l:
                if engine.state.R.get(k, 0.0) > 0:
                    v913_age_r[k] = v913_age_r.get(k, 0) + 1
                else:
                    v913_age_r[k] = 0
                v913_max_age_r[k] = max(v913_max_age_r.get(k, 0), v913_age_r[k])

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

            # ═══════════════════════════════════════════════════════════════
            # v9.13 Step 0: alive_l 差分検出 (decay_exclusion 直後)
            # ═══════════════════════════════════════════════════════════════
            v913_curr_alive_l = set(engine.state.alive_l)
            # 新規リンク検出
            for k in (v913_curr_alive_l - v913_prev_alive_l):
                v913_birth_step_of_link[k] = v913_global_step
            # 死亡リンク検出
            for k in (v913_prev_alive_l - v913_curr_alive_l):
                v913_link_life_log.append({
                    "link_id": f"({k[0]},{k[1]})",
                    "node1": k[0],
                    "node2": k[1],
                    "birth_step": v913_birth_step_of_link.get(k, 0),
                    "death_step": v913_global_step,
                    "lifetime_steps": v913_global_step - v913_birth_step_of_link.get(k, 0),
                    "max_age_r_lifetime": v913_max_age_r.get(k, 0),
                    "age_r_at_death": v913_age_r.get(k, 0),
                })
            v913_prev_alive_l = v913_curr_alive_l
            v913_global_step += 1

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

                # v9.11: stash struct_set for later pulse-time E_t extraction.
                # 同一 step 内なので二重計算を避ける (V11_PF_HOPS_FACTOR=1 で同条件)
                v11_current_struct_set[cid] = struct_set

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

            # ──────────────────────────────────────────────
            # v9.10 Pulse Model (spec 2.1): per-step pulse firing
            # Pulses fire at cumulative_step % 50 == cid % 50.
            # 4 axes are computed on-demand with v9.8b formulas
            # using the current in-progress window_st_sizes buffer.
            # Ghost cids are skipped (freeze, spec 2.6).
            # Physics / VL / pickup / engine.state は一切触らない。
            # ──────────────────────────────────────────────
            t_cum = cumulative_step
            t_mod = t_cum % PULSE_INTERVAL
            # iterate hosted cids whose offset matches this step
            for cid_p in list(cog.all_hosted_cids()):
                if (cid_p % PULSE_INTERVAL) != t_mod:
                    continue
                if cid_p not in cog.phi:
                    continue

                # ──────────────────────────────────────────────
                # v9.15 段階 2: 50 step 駆動 Fetch は廃止。
                # Fetch は Layer B observe_step 直後に event 駆動で実行される。
                # ──────────────────────────────────────────────

                # current-time 4 axes (v9.8b formulas, faithful)
                st_sizes_p = window_st_sizes.get(cid_p, [])
                if st_sizes_p:
                    st_mean_p = float(np.mean(st_sizes_p))
                    st_std_p = float(np.std(st_sizes_p))
                else:
                    st_mean_p = 0.0
                    st_std_p = 0.0
                # max_partners at this pulse instant (across hosted cids)
                max_n_p = 1
                for _c in cog.all_hosted_cids():
                    n_p = cog.get_n_partners(_c)
                    if n_p > max_n_p:
                        max_n_p = n_p
                d_soc_p = cog.get_n_partners(cid_p) / max_n_p
                d_sta_p = 1.0 / (1.0 + st_std_p / (st_mean_p + EPS))
                d_spr_p = cog.get_attention_entropy(cid_p)
                d_fam_p = cog.get_familiarity_mean(cid_p)

                ev = cog.on_pulse(cid_p, d_soc_p, d_sta_p, d_spr_p, d_fam_p,
                                  t_cum, w)
                if ev is not None:
                    row = {
                        "seed": seed,
                        "cid": cid_p,
                        "t": ev["t"],
                        "window": ev["window"],
                        "pulse_n": ev["pulse_n"],
                        "trigger": ev["trigger"],
                        "tags": "|".join(ev["tags"]) if ev["tags"] else "",
                    }
                    for a in V10_AXES:
                        row[f"d_{a}"] = round(ev["curr"][a], 6)
                        row[f"delta_{a}"] = round(ev["deltas"][a], 6)
                        row[f"theta_{a}"] = round(ev["theta"][a], 6)
                        row[f"R_{a}"] = round(ev["R"][a], 6)

                    # ──────────────────────────────────────────────
                    # v9.11: Cognitive Capture (指示書 §4)
                    # E_t 抽出 → Δ 計算 → p_capture → cold_start 判定/集計
                    # M_c が未記録 (n_core<2 等で v11_b_gen に inf も入ってない異常)
                    # の cid は v11_ 列を unformed で埋めて続行。
                    # ──────────────────────────────────────────────
                    m_c = cog.v11_m_c.get(cid_p)
                    struct_set_p = v11_current_struct_set.get(cid_p)
                    if m_c is not None and struct_set_p is not None:
                        e_t = v11_compute_e_t(
                            engine.state, struct_set_p, m_c["phase_sig"])
                        delta, delta_axes = v11_compute_delta(m_c, e_t)
                        p_capture = V11_P_MAX * math.exp(
                            -V11_LAMBDA * delta)

                        cog.v11_last_e_t[cid_p] = e_t
                        cog.v11_last_delta[cid_p] = delta
                        cog.v11_last_delta_axes[cid_p] = delta_axes
                        cog.v11_last_p_capture[cid_p] = p_capture

                        pulse_n_now = ev["pulse_n"]
                        if (V11_CAPTURE_COLD_START_SKIP
                                and pulse_n_now <= COLD_START_PULSES):
                            captured_str = "cold_start"
                        else:
                            drew = capture_rng.random()
                            captured_bool = bool(drew < p_capture)
                            captured_str = "TRUE" if captured_bool else "FALSE"
                            # 集計 (cold_start 除く)
                            cog.v11_n_pulses_eval[cid_p] += 1
                            if captured_bool:
                                cog.v11_n_captured[cid_p] += 1
                            cog.v11_sum_delta[cid_p] += delta
                            for k in ("n", "s", "r", "phase"):
                                cog.v11_sum_delta_axes[cid_p][k] += \
                                    delta_axes[k]
                        cog.v11_last_captured[cid_p] = captured_str

                        b_gen_v = cog.v11_b_gen.get(cid_p, float("inf"))
                        b_gen_str = ("inf" if b_gen_v == float("inf")
                                     else round(b_gen_v, 6))
                        row["v11_b_gen"] = b_gen_str
                        row["v11_delta"] = round(delta, 6)
                        row["v11_d_n"] = round(delta_axes["n"], 6)
                        row["v11_d_s"] = round(delta_axes["s"], 6)
                        row["v11_d_r"] = round(delta_axes["r"], 6)
                        row["v11_d_phase"] = round(delta_axes["phase"], 6)
                        row["v11_p_capture"] = round(p_capture, 6)
                        row["v11_captured"] = captured_str
                        row["v11_n_local"] = e_t["n_local"]
                        row["v11_s_avg_local"] = round(e_t["s_avg_local"], 6)
                        row["v11_r_local"] = round(e_t["r_local"], 6)
                        row["v11_theta_avg_local"] = round(
                            e_t["theta_avg_local"], 6)
                    else:
                        # M_c 未記録 (異常ケース): v11_ 列は unformed 埋め
                        row["v11_b_gen"] = "unformed"
                        row["v11_delta"] = "unformed"
                        row["v11_d_n"] = "unformed"
                        row["v11_d_s"] = "unformed"
                        row["v11_d_r"] = "unformed"
                        row["v11_d_phase"] = "unformed"
                        row["v11_p_capture"] = "unformed"
                        row["v11_captured"] = "unformed"
                        row["v11_n_local"] = "unformed"
                        row["v11_s_avg_local"] = "unformed"
                        row["v11_r_local"] = "unformed"
                        row["v11_theta_avg_local"] = "unformed"

                    v10_pulse_log.append(row)

            # v9.14 Step 2-3: Layer B observe (audit-only, Layer A は touch しない)
            # 各 hosted cid に対して context (e_t, m_c, attn_nodes, other_cids) を
            # precompute してから observe_step に渡す。ledger は cid_ctx だけを見て
            # event 検知 + spend packet を実行する。
            v914_cid_ctx = {}
            for v914_cid in cog.all_hosted_cids():
                v914_lid = cog.current_lid.get(v914_cid)
                if v914_lid is None or v914_lid not in vl.labels:
                    continue
                v914_b_gen = cog.v11_b_gen.get(v914_cid, float("inf"))
                if not math.isfinite(v914_b_gen) or v914_b_gen <= 0:
                    continue
                v914_m_c = cog.v11_m_c.get(v914_cid)
                if v914_m_c is None:
                    continue
                v914_struct = v11_current_struct_set.get(v914_cid)
                if v914_struct is None:
                    continue
                v914_label_nodes = frozenset(vl.labels[v914_lid]["nodes"])
                v914_e_t = v11_compute_e_t(
                    engine.state, v914_struct, v914_m_c["phase_sig"])
                # attn_nodes = struct_set - core (v9.11 update_attention と同じ除外)
                v914_attn_nodes = frozenset(
                    n for n in v914_struct if n not in v914_label_nodes)
                # other_cids: struct_set の node が属する他の cid (v9.11 update_familiarity と同じ)
                v914_other_cids = set()
                for _n in v914_struct:
                    _olid = node_to_lid.get(_n)
                    if (_olid is None or _olid in vl.macro_nodes
                            or _olid == v914_lid):
                        continue
                    _ocid = cog.cid_of_lid.get(_olid)
                    if _ocid is not None:
                        v914_other_cids.add(_ocid)
                v914_cid_ctx[v914_cid] = {
                    "b_gen": v914_b_gen,
                    "member_nodes": v914_label_nodes,
                    "e_t": v914_e_t,
                    "m_c": v914_m_c,
                    "attn_nodes": v914_attn_nodes,
                    "other_cids": frozenset(v914_other_cids),
                }
            # v9.15 段階 2: observe_step 前の event 数を記録
            # (新規 event の差分から event 駆動 Fetch を発行)。
            v915_ev_count_before = len(v914_ledger.events)
            v914_ledger.observe_step(
                window=w, step=step, global_step=cumulative_step,
                alive_l_set=engine.state.alive_l,
                state_r=engine.state.R,
                cid_ctx=v914_cid_ctx,
            )

            # v9.15 段階 2 / v9.16 段階 3: event 駆動 Fetch
            # (Layer B spend → Layer C fetch の順)
            # Layer B が append した新規 event に対して、該当 cid の self-buffer が
            # あれば read_on_event を呼ぶ。E3_contact は両 cid 視点で 2 event が
            # 記録されるため、両 buffer が自然に Fetch される。
            # disable_e3=True のとき Layer B は E3 event を append しないため
            # Fetch も走らない (再現性維持)。
            #
            # v9.16 段階 3 追加:
            #   Q_remaining = v14_q_remaining (spend_packet 実行後の値、
            #                                  Layer B ledger を read-only で読む)
            #   seed        = run の seed (local RNG 構築のみ、engine.rng は
            #                              touch しない)
            #
            # v9.17 段階 4 追加 (E3_contact のみ):
            #   下層: 両 cid で read_other_on_e3_contact を呼ぶ
            #         (observer が contacted の M_c を部分取得)
            #   上層: canonical ordering (observer_cid < contacted_cid) の
            #         event のみ InteractionLog.record_contact を呼ぶ
            #         (Q3 Taka 回答 2026-04-22、pair ごと 1 row)
            #   event_id: seed 内 0-based、v914_ledger.events の absolute index
            #             (Q2 Taka 回答 2026-04-22)
            for _idx_offset, v915_ev in enumerate(
                v914_ledger.events[v915_ev_count_before:]
            ):
                _event_id_v917 = v915_ev_count_before + _idx_offset
                _observer_cid = v915_ev.get("cid")
                v915_buf = v915_self_buffers.get(_observer_cid)
                if v915_buf is None:
                    continue
                v915_buf.read_on_event(
                    state=engine.state,
                    alive_l=engine.state.alive_l,
                    current_step=cumulative_step,
                    event_type_full=v915_ev["v14_event_type"],
                    Q_remaining=int(v915_ev["v14_q_remaining"]),
                    seed=int(seed),
                )

                # v9.17 段階 4: E3_contact のみ、下層/上層を追加処理
                if v915_ev["v14_event_type"] != "E3_contact":
                    continue

                _contacted_cid = v917_parse_contacted_cid(v915_ev["link_id"])
                if _contacted_cid is None:
                    continue
                _contacted_buf = v915_self_buffers.get(_contacted_cid)
                if _contacted_buf is None:
                    continue

                # 下層: observer が contacted の CidView を読む。
                # CidView は v914_ledger + CidSelfBuffer + cog から組み立てた
                # read-only snapshot (v917_cid_view.py)。
                _contacted_view = v917_build_cid_view(
                    cid_id=_contacted_cid,
                    self_buffer=_contacted_buf,
                    v914_ledger=v914_ledger,
                    cog=cog,
                )
                if _contacted_view is not None:
                    v915_buf.read_other_on_e3_contact(
                        other_cid_view=_contacted_view,
                        current_step=cumulative_step,
                        event_id=_event_id_v917,
                        seed=int(seed),
                    )

                # 上層: canonical ordering dedup。observer_cid < contacted_cid
                # のときだけ接触体候補を InteractionLog に記録する。
                # Layer B は pair ごと 2 event 発行するが、InteractionLog は
                # pair ごと 1 row になる (§10 §4.1 件数制約)。
                if _observer_cid < _contacted_cid:
                    _observer_view = v917_build_cid_view(
                        cid_id=_observer_cid,
                        self_buffer=v915_buf,
                        v914_ledger=v914_ledger,
                        cog=cog,
                    )
                    if (_observer_view is not None
                            and _contacted_view is not None):
                        v917_interaction_log.record_contact(
                            step=cumulative_step,
                            cid_a=_observer_view,     # 小さい id 側を a
                            cid_b=_contacted_view,    # 大きい id 側を b
                            event_id=_event_id_v917,
                        )

            # v9.18 段階 5: per_step orchestrator
            # event Fetch ループ後、cumulative_step += 1 直前に呼ぶ。
            # 全 hosted CID の v18_* を更新 (ghost 化検出で _finalize)。
            # v18_* は run 中の分岐条件に使わない (GPT §8.2)。
            v918_update_per_step(
                self_buffers=v915_self_buffers,
                cog=cog,
                vl=vl,
                engine=engine,
                v914_ledger=v914_ledger,
                current_step=cumulative_step,
            )

            # v10.1 Minimal Ingestion: step 末 reap (Q ベース)
            # ingestion 処理は v914_ledger.observe_step 内で実行済 (E3 検知直後)。
            # この時点で residual_Q == 0 になった ghost を一括 reap する。
            # window 末ではなく毎 step reap するのが v10.1 仕様 (Taka 確定 2026-04-26)。
            _reaped_step = cog.reap_ghosts_step(cumulative_step)
            if _reaped_step:
                _reaped_per_window_count += len(_reaped_step)

            cumulative_step += 1

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
            # v10.1 Minimal Ingestion: pickup 列廃止、ingestion 列に置換
            "ghost_births": 0,
            "ghost_reaped": 0,
            "n_ingestions": 0,
            "n_empty_ingestions": 0,
            "total_gain_transferred": 0,
            "total_received": 0,
            "total_digested": 0,
            "n_phantom_contacts": 0,
            "ghosts_remaining": 0,
            "mean_ghost_residual_Q": 0.0,
        })

        # v9.8b: Commit disposition (prev <- current) for next window's comparison
        # VL step の前に行う (この window 終了時点の値を次 window の比較基準にする)
        for cid in hosted_cids:
            cog.commit_disposition(cid)

        # ═══════════════════════════════════════════════════════════════════
        # v9.13 Step 0: window 末 link snapshot + shadow component 分析 (§9)
        # ═══════════════════════════════════════════════════════════════════
        # 9.1 生存リンクスナップショット
        for k in engine.state.alive_l:
            v913_link_snapshot_log.append({
                "window": w,
                "link_id": f"({k[0]},{k[1]})",
                "age_r_current": v913_age_r.get(k, 0),
                "max_age_r_so_far": v913_max_age_r.get(k, 0),
            })

        # 9.2 Shadow component 計算
        for tau in V913_SHADOW_THRESHOLDS:
            filtered_edges = [
                (k[0], k[1]) for k in engine.state.alive_l
                if v913_age_r.get(k, 0) >= tau
            ]
            if not filtered_edges:
                continue
            G = nx.Graph()
            G.add_edges_from(filtered_edges)
            for comp_idx, comp_nodes in enumerate(nx.connected_components(G)):
                comp_size = len(comp_nodes)
                if comp_size < V913_SHADOW_MIN_SIZE:
                    continue
                comp_edges = [
                    k for k in engine.state.alive_l
                    if k[0] in comp_nodes and k[1] in comp_nodes
                    and v913_age_r.get(k, 0) >= tau
                ]
                age_rs = [v913_age_r.get(e, 0) for e in comp_edges]
                if not age_rs:
                    continue
                v913_shadow_component_log.append({
                    "window": w,
                    "threshold": tau,
                    "comp_id": f"w{w}_t{tau}_c{comp_idx}",
                    "comp_size": comp_size,
                    "comp_n_links": len(comp_edges),
                    "comp_age_r_min": min(age_rs),
                    "comp_age_r_mean": round(sum(age_rs) / len(age_rs), 2),
                })

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
            # v9.11: Birth 時 B_Gen / M_c 固定記録 (§3.4)
            v11_record_birth_metrics(cog, engine.state, lab, lid)
            # v9.15: Lazy Registration for self-buffer (Layer C)
            v915_ensure_cid_registered(
                v915_self_buffers, new_cid,
                lab["nodes"], engine.state, v913_global_step,
                Q0=v917_q0_from_cog(cog, new_cid))

            # ═══════════════════════════════════════════════════════════════
            # v9.13 Step 0: label メンバーリンクの persistence を記録 (§8)
            # ═══════════════════════════════════════════════════════════════
            v913_label_nodes = set(lab["nodes"])
            v913_n_core = len(v913_label_nodes)
            for k in engine.state.alive_l:
                if k[0] in v913_label_nodes and k[1] in v913_label_nodes:
                    v913_label_member_persistence.append({
                        "label_id": lid,
                        "birth_window": w,
                        "n_core": v913_n_core,
                        "link_id": f"({k[0]},{k[1]})",
                        "age_r_at_birth": v913_age_r.get(k, 0),
                        "max_age_r_so_far": v913_max_age_r.get(k, 0),
                    })

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
        # v10.1 Minimal Ingestion: detach 時に Layer B から Q_remaining を読み、
        # ghost_residual_Q として継承させる。
        for lid in (prev_lids - curr_lids):
            cid = cog.cid_for_lid(lid)
            # ledger から Q_remaining 読み取り (未登録 cid は 0)
            _residual_q = (v914_ledger.get_q_remaining(cid)
                           if cid is not None else 0)
            cog.detach(lid, w,
                       residual_Q=_residual_q,
                       current_step=cumulative_step)
            ghost_births_this_window += 1
            if lid in label_meta:
                label_meta[lid]["death_w"] = w
                label_meta[lid]["became_ghost_w"] = w
                all_deaths.append({"lid": lid,
                                   "cid": cid, "w": w})
                # v10.1: pickup 機構廃止。record_death / death_pool は使わない。
            if cid is not None and cid in subject_meta:
                subject_meta[cid]["host_lost_window"] = w
                subject_meta[cid]["host_lost_step"] = cumulative_step
                subject_meta[cid]["initial_residual_Q"] = _residual_q
                subject_meta[cid]["final_state"] = "ghost"

        # v10.1: pickup 機構は廃止 (attempt_pickup_round / cleanup_death_pool 削除)
        # window 末でも Q ベース reap を 1 回呼ぶ (残った 0-Q ghost を一掃)。
        # これは「detach 直後で residual_Q=0 だった ghost」を取り逃がさないため。
        # step 末 reap は per-step ループ内で既に呼んでいるが、window 末の
        # detach 直後の ghost はまだ reap されていない。
        _reaped_at_window_end = cog.reap_ghosts_step(cumulative_step)
        _reaped_per_window_count += len(_reaped_at_window_end)
        for cid in _reaped_at_window_end:
            if cid in subject_meta:
                subject_meta[cid]["reaped_step"] = cumulative_step
                subject_meta[cid]["final_state"] = "reaped"
                lost_step = subject_meta[cid].get("host_lost_step")
                if lost_step is not None:
                    subject_meta[cid]["ghost_duration_steps"] = (
                        cumulative_step - lost_step)

        # Update window row: ghost reap + v10.1 ingestion 集計
        window_rows[-1]["ghost_births"] = ghost_births_this_window
        window_rows[-1]["ghost_reaped"] = _reaped_per_window_count
        # v10.1 ingestion stats (per-window)
        _ing_slice = v914_ledger.ingestion_events[
            _ingestion_count_at_window_start:]
        _ph_slice = v914_ledger.phantom_contacts[
            _phantom_count_at_window_start:]
        window_rows[-1]["n_ingestions"] = len(_ing_slice)
        window_rows[-1]["n_empty_ingestions"] = sum(
            1 for e in _ing_slice if e["was_empty"])
        window_rows[-1]["total_gain_transferred"] = sum(
            e["gain"] for e in _ing_slice)
        window_rows[-1]["total_received"] = sum(
            e["received"] for e in _ing_slice)
        window_rows[-1]["total_digested"] = sum(
            e["digested"] for e in _ing_slice)
        window_rows[-1]["n_phantom_contacts"] = len(_ph_slice)
        # ghost residual_Q 分布スナップショット
        _ghost_q_values = list(cog.ghost_residual_Q.values())
        window_rows[-1]["ghosts_remaining"] = len(_ghost_q_values)
        window_rows[-1]["mean_ghost_residual_Q"] = (
            float(np.mean(_ghost_q_values)) if _ghost_q_values else 0.0
        )

        # v9.18 段階 5: window 末の v18_* snapshot を accumulator に追加
        # (hosted cid のみ、ghost 化済の cid は _final で別途捕捉)
        v918_snapshot_window(
            self_buffers=v915_self_buffers,
            cog=cog,
            vl=vl,
            window_idx=w,
            cumulative_step=cumulative_step,
            accumulator=v918_window_accumulator,
        )

        sec = time.time() - t0
        _ing_n = window_rows[-1]["n_ingestions"]
        _ing_empty = window_rows[-1]["n_empty_ingestions"]
        _ph_n = window_rows[-1]["n_phantom_contacts"]
        print(f"  seed={seed} w={w} vLb={len(vl.labels)} "
              f"hosted={hosted_n} ghost={ghost_n} "
              f"births={ghost_births_this_window} "
              f"reaped={_reaped_per_window_count} "
              f"ing={_ing_n}({_ing_empty}empty) "
              f"phantom={_ph_n} "
              f"cids_total={cog._next_cid} "
              f"recip={reciprocal_count} {sec:.0f}s")

    # v9.18 段階 5: tracking 終了時に未 _final の CID を tracking_end で確定
    _v918_n_finalized = v918_finalize_all_at_tracking_end(
        self_buffers=v915_self_buffers,
        cumulative_step=cumulative_step,
    )
    print(f"  v9.18 Layer C: finalized at tracking_end: "
          f"{_v918_n_finalized} cids")

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
    # SAVE Layer B (新): per_subject CSV (v9.8a + v9.8b + v9.8c columns)
    # ════════════════════════════════════════════════════════
    # v9.8b: 各 cid の最後の _tag_history entry を取り出して
    # prev/current/delta/tags/state カラムを追加する (GPT 修正提案 B)
    last_tag_entry = {}  # cid -> last _tag_history entry
    for entry in cog._tag_history:
        last_tag_entry[entry["cid"]] = entry

    # v10.1 Minimal Ingestion: per_subject 用の摂食統計を集計
    # 各 cid が「食べた側」「食べられた側」「空摂食」「幻接触に遭った側」「消化した量」
    cid_n_ingestions_eater = Counter()       # 食べる側として何回摂食したか
    cid_n_ingestions_eater_empty = Counter() # うち空摂食 (gain=0) の回数
    cid_total_q_received = Counter()         # 食べた量の累計 (Q_remaining 増加分)
    cid_total_q_digested = Counter()         # 消化分 (Q0 上限超過で消えた分) の累計
    cid_n_ingested_as_ghost = Counter()      # 食べられる側として何回 ingestion された
    cid_total_q_lost_as_ghost = Counter()    # 食べられて失った量 (gain 累計)
    for ev in v914_ledger.ingestion_events:
        observer = ev["observer_cid"]
        ghost = ev["ghost_cid"]
        cid_n_ingestions_eater[observer] += 1
        if ev["was_empty"]:
            cid_n_ingestions_eater_empty[observer] += 1
        cid_total_q_received[observer] += ev["received"]
        cid_total_q_digested[observer] += ev["digested"]
        cid_n_ingested_as_ghost[ghost] += 1
        cid_total_q_lost_as_ghost[ghost] += ev["gain"]
    cid_n_phantom_eater = Counter()          # 幻接触に遭った側 (期待していったら居なかった)
    for ph in v914_ledger.phantom_contacts:
        cid_n_phantom_eater[ph["observer_cid"]] += 1

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

        # ghost duration を最新化 (v10.1: step 単位に変更)
        if final_state == "ghost":
            lost_step = cog.ghost_q_lost_at_step.get(cid)
            ghost_dur_steps = (cumulative_step - lost_step
                               if lost_step is not None else 0)
        elif final_state == "reaped":
            ghost_dur_steps = meta.get("ghost_duration_steps", 0) or 0
        else:
            ghost_dur_steps = 0

        # v9.8b: 最後の tag entry からの情報 (生存中に get_introspection が呼ばれた最終回)
        tag_entry = last_tag_entry.get(cid, {})

        # v10.1: ingestion 統計
        n_ing_eater = cid_n_ingestions_eater.get(cid, 0)
        n_ing_empty = cid_n_ingestions_eater_empty.get(cid, 0)
        q_received = cid_total_q_received.get(cid, 0)
        q_digested = cid_total_q_digested.get(cid, 0)
        n_ing_as_ghost = cid_n_ingested_as_ghost.get(cid, 0)
        q_lost_as_ghost = cid_total_q_lost_as_ghost.get(cid, 0)
        n_phantom = cid_n_phantom_eater.get(cid, 0)
        # 初期 / 最終 residual_Q
        initial_residual_Q = meta.get("initial_residual_Q", "")
        if final_state == "ghost":
            final_residual_Q = cog.ghost_residual_Q.get(cid, 0)
        elif final_state == "reaped":
            final_residual_Q = 0
        else:
            final_residual_Q = ""

        subject_rows.append({
            "seed": seed,
            "cognitive_id": cid,
            "birth_window": meta["birth_window"],
            "host_lost_window": meta.get("host_lost_window", "")
                if meta.get("host_lost_window") is not None else "",
            "host_lost_step": meta.get("host_lost_step", "")
                if meta.get("host_lost_step") is not None else "",
            "reaped_step": meta.get("reaped_step", "")
                if meta.get("reaped_step") is not None else "",
            "final_state": final_state,
            "ghost_duration_steps": ghost_dur_steps,
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
            # v10.1 Minimal Ingestion: 摂食統計 (pickup 列を全廃の上、入れ替え)
            "initial_residual_Q": initial_residual_Q,
            "final_residual_Q": final_residual_Q,
            "n_ingestions_as_eater": n_ing_eater,
            "n_empty_ingestions_as_eater": n_ing_empty,
            "total_q_received": q_received,
            "total_q_digested": q_digested,
            "n_ingested_as_ghost_food": n_ing_as_ghost,
            "total_q_lost_as_ghost": q_lost_as_ghost,
            "n_phantom_contacts_as_eater": n_phantom,
            # ──────────────────────────────────────────────
            # v9.9: 内的基準軸 (構造語のみ、v99_ prefix、33 列)
            # ──────────────────────────────────────────────
            "v99_formation_status": cog.formation_status.get(cid, "unformed"),
            "v99_trace_len": len(cog.recent_dispositions.get(cid, [])),
            # personal_range (4 軸 × 4 統計 = 16 列)
            **{f"v99_range_{a}_{s}":
               cog.personal_range.get(cid, {}).get(a, {}).get(s, "unformed")
               for a in ("social", "stability", "spread", "familiarity")
               for s in ("min", "max", "mean", "std")},
            # drift (4 軸 × 3 = 12 列)
            **{f"v99_drift_{a}_{k}":
               cog.drift.get(cid, {}).get(a, {}).get(f"{k}_count", "unformed")
               for a in ("social", "stability", "spread", "familiarity")
               for k in ("positive", "negative", "neutral")},
            # 派生量 (構造語のみ、3 列)
            "v99_lowest_std_axis": cog.lowest_std_axis.get(cid, "unformed"),
            "v99_dominant_positive_drift_axis": cog.dominant_positive_drift_axis.get(cid, "unformed"),
            "v99_dominant_negative_drift_axis": cog.dominant_negative_drift_axis.get(cid, "unformed"),
            # ──────────────────────────────────────────────
            # v9.10 Pulse Model summary (exploration build)
            # v9.9 の window 基準系と併存、独立系統
            # ──────────────────────────────────────────────
            "v10_pulse_count": cog.v10_pulse_count.get(cid, 0),
            "v10_tag_trigger_last": cog.v10_tag_trigger_last.get(cid, "unformed"),
            "v10_n_normal": cog.v10_n_normal.get(cid, 0),
            "v10_n_major": cog.v10_n_major.get(cid, 0),
            # theta_last per axis (4 列)
            **{f"v10_theta_{a}_last":
               round(cog.v10_theta_last.get(cid, {}).get(a, 0.0), 6)
               for a in V10_AXES},
            # R_last per axis (4 列)
            **{f"v10_R_{a}_last":
               round(cog.v10_R_last.get(cid, {}).get(a, 0.0), 6)
               for a in V10_AXES},
            # R_max / R_min per axis (8 列)
            **{f"v10_R_max_{a}":
               round(cog.v10_R_max_seen.get(cid, {}).get(a, 0.0), 6)
                   if cog.v10_R_max_seen.get(cid, {}).get(a, float("-inf")) != float("-inf")
                   else "unformed"
               for a in V10_AXES},
            **{f"v10_R_min_{a}":
               round(cog.v10_R_min_seen.get(cid, {}).get(a, 0.0), 6)
                   if cog.v10_R_min_seen.get(cid, {}).get(a, float("inf")) != float("inf")
                   else "unformed"
               for a in V10_AXES},
            # ──────────────────────────────────────────────
            # v9.11: Cognitive Capture summary (指示書 §5.2)
            # B_Gen / M_c は birth 時固定。集計は cold_start 除く。
            # 計算不能・未記録は "unformed"。
            # ──────────────────────────────────────────────
            **(lambda _bg=cog.v11_b_gen.get(cid),
                      _mc=cog.v11_m_c.get(cid),
                      _ne=cog.v11_n_pulses_eval.get(cid, 0),
                      _nc=cog.v11_n_captured.get(cid, 0),
                      _sd=cog.v11_sum_delta.get(cid, 0.0),
                      _sda=cog.v11_sum_delta_axes.get(cid, None): {
                "v11_b_gen": (
                    "unformed" if _bg is None
                    else "inf" if _bg == float("inf")
                    else round(_bg, 6)),
                "v11_m_c_n_core": (_mc["n_core"] if _mc else "unformed"),
                "v11_m_c_s_avg": (round(_mc["s_avg"], 6) if _mc else "unformed"),
                "v11_m_c_r_core": (round(_mc["r_core"], 6) if _mc else "unformed"),
                "v11_m_c_phase_sig": (round(_mc["phase_sig"], 6) if _mc else "unformed"),
                "v11_n_pulses_eval": _ne,
                "v11_n_captured": _nc,
                "v11_capture_rate": (
                    round(_nc / _ne, 6) if _ne > 0 else "unformed"),
                "v11_mean_delta": (
                    round(_sd / _ne, 6) if _ne > 0 else "unformed"),
                "v11_mean_d_n": (
                    round(_sda["n"] / _ne, 6) if (_ne > 0 and _sda) else "unformed"),
                "v11_mean_d_s": (
                    round(_sda["s"] / _ne, 6) if (_ne > 0 and _sda) else "unformed"),
                "v11_mean_d_r": (
                    round(_sda["r"] / _ne, 6) if (_ne > 0 and _sda) else "unformed"),
                "v11_mean_d_phase": (
                    round(_sda["phase"] / _ne, 6) if (_ne > 0 and _sda) else "unformed"),
            })(),
            # ──────────────────────────────────────────────
            # v9.15 段階 2 / v9.16 段階 3: CID self-buffer summary
            # (末尾 20 列 = 段階 2 の 13 列 + 段階 3 の 7 列、既存列は改変しない)
            # ──────────────────────────────────────────────
            **v915_build_subject_columns(v915_self_buffers, cid),
            # ──────────────────────────────────────────────
            # v9.17 段階 4: 他者読み / 接触体観察 (末尾 5 列、指示書 §6.1)
            # ──────────────────────────────────────────────
            **v917_build_subject_columns(v915_self_buffers, cid),
            # ──────────────────────────────────────────────
            # v9.18 段階 5: 認知増加 + V_unified + theta_distance (末尾 9 列)
            # per_subject は _final 値 (ghost 化時点 or tracking 終了時)。
            # ──────────────────────────────────────────────
            **build_v918_subject_columns(v915_self_buffers, cid),
        })

    csv_b_subject = outdir / "subjects" / f"per_subject_seed{seed}.csv"
    if subject_rows:
        with open(csv_b_subject, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=subject_rows[0].keys())
            writer.writeheader()
            writer.writerows(subject_rows)

    # ════════════════════════════════════════════════════════
    # SAVE (v9.15): per_cid_self CSV — 1 cid = 1 row, registry 全体
    # ════════════════════════════════════════════════════════
    v915_selfread_path = outdir / "selfread" / f"per_cid_self_seed{seed}.csv"
    v915_n_rows = v915_write_per_cid_self_csv(
        v915_self_buffers, seed, v915_selfread_path)
    print(f"  v9.15 Layer C: per_cid_self: {v915_n_rows} rows "
          f"-> {v915_selfread_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.15): divergence_log CSV — 全 cid の Fetch ごとのログ集約
    # ════════════════════════════════════════════════════════
    v915_divlog_path = outdir / "selfread" / f"divergence_log_seed{seed}.csv"
    v915_n_divlog = v915_write_divergence_log_csv(
        v915_self_buffers, seed, v915_divlog_path)
    print(f"  v9.15 Layer C: divergence_log: {v915_n_divlog} rows "
          f"-> {v915_divlog_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.16 段階 3): observation_log CSV — event 発火時の
    #                      サンプリング結果 (cid × event 単位)
    # ════════════════════════════════════════════════════════
    v917_obslog_path = outdir / "selfread" / f"observation_log_seed{seed}.csv"
    v917_n_obslog = v917_write_observation_log_csv(
        v915_self_buffers, seed, v917_obslog_path)
    print(f"  v9.16 Layer C: observation_log: {v917_n_obslog} rows "
          f"-> {v917_obslog_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.17 段階 4): other_records CSV — 各 cid の他者接触ログ
    #                       (cid × E3_contact event 単位、指示書 §6.2)
    # ════════════════════════════════════════════════════════
    v917_otherrec_path = outdir / "selfread" / f"other_records_seed{seed}.csv"
    v917_n_otherrec = v917_write_other_records_csv(
        v915_self_buffers, seed, v917_otherrec_path)
    print(f"  v9.17 Layer C: other_records: {v917_n_otherrec} rows "
          f"-> {v917_otherrec_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.17 段階 4): interaction_log CSV — 接触体候補の外部記録
    #                       (pair × 発火ごと 1 row、canonical dedup 済み、
    #                       指示書 §6.3)
    # ════════════════════════════════════════════════════════
    v917_ilog_path = outdir / "selfread" / f"interaction_log_seed{seed}.csv"
    v917_n_ilog = v917_write_interaction_log_csv(
        v917_interaction_log, seed, v917_ilog_path)
    print(f"  v9.17 Layer C: interaction_log: {v917_n_ilog} rows "
          f"-> {v917_ilog_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.15): class_divergence CSV — 同クラス cid ペアの theta 乖離
    # ════════════════════════════════════════════════════════
    v915_classdiv_rows = v915_compute_class_divergence(
        v915_self_buffers, cog.original_phase_sig, seed)
    v915_classdiv_path = outdir / "selfread" / f"class_divergence_seed{seed}.csv"
    v915_n_classdiv = v915_write_class_divergence_csv(
        v915_classdiv_rows, v915_classdiv_path)
    print(f"  v9.15 Layer C: class_divergence: {v915_n_classdiv} rows "
          f"-> {v915_classdiv_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.18 段階 5): v18_window_trajectory CSV —
    #                       per_cid × per_window の v18_* 軌跡
    # ════════════════════════════════════════════════════════
    v918_window_traj_path = (
        outdir / "selfread" / f"v18_window_trajectory_seed{seed}.csv"
    )
    v918_n_window_rows = write_v18_window_trajectory_csv(
        v918_window_accumulator, seed, v918_window_traj_path,
    )
    print(f"  v9.18 Layer C: v18_window_trajectory: {v918_n_window_rows} rows "
          f"-> {v918_window_traj_path}")

    # ════════════════════════════════════════════════════════
    # SAVE (v9.10): Pulse log — per pulse event, one row
    # ════════════════════════════════════════════════════════
    pulse_dir = outdir / "pulse"
    pulse_dir.mkdir(parents=True, exist_ok=True)
    csv_pulse = pulse_dir / f"pulse_log_seed{seed}.csv"
    if v10_pulse_log:
        with open(csv_pulse, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=v10_pulse_log[0].keys())
            writer.writeheader()
            writer.writerows(v10_pulse_log)
    else:
        # empty stub to mark the run did write (for sanity)
        with open(csv_pulse, "w", newline="") as f:
            f.write("seed,cid,t,window,pulse_n,trigger,tags\n")

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
    # v10.1 Minimal Ingestion: SAVE ingestion + phantom logs
    # ════════════════════════════════════════════════════════
    # 全摂食イベント (raw)。空摂食 (gain=0) も含む。当てが外れた場合は phantom 側。
    if v914_ledger.ingestion_events:
        ing_path = outdir / "ingestion" / f"ingestion_events_seed{seed}.csv"
        ing_path.parent.mkdir(exist_ok=True)
        # seed 列を追加するため fieldnames を明示
        ing_fieldnames = ["seed"] + list(v914_ledger.ingestion_events[0].keys())
        with open(ing_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ing_fieldnames)
            writer.writeheader()
            for ev in v914_ledger.ingestion_events:
                row = {"seed": seed}
                row.update(ev)
                writer.writerow(row)

    # 幻接触ログ (期待していったら居なかった = phantom_contact)。
    # 認知層では既に reap 済みの ghost_cid に対する E3 onset。
    # cog._node_to_cids は cid retire 後も保持されるため発生しうる。
    if v914_ledger.phantom_contacts:
        ph_path = outdir / "ingestion" / f"phantom_contacts_seed{seed}.csv"
        ph_path.parent.mkdir(exist_ok=True)
        ph_fieldnames = ["seed"] + list(v914_ledger.phantom_contacts[0].keys())
        with open(ph_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ph_fieldnames)
            writer.writeheader()
            for ev in v914_ledger.phantom_contacts:
                row = {"seed": seed}
                row.update(ev)
                writer.writerow(row)

    # 集計サマリ (run-level)
    ing_summary_path = outdir / "ingestion" / f"ingestion_summary_seed{seed}.csv"
    ing_summary_path.parent.mkdir(exist_ok=True)
    n_ing_total = len(v914_ledger.ingestion_events)
    n_ing_empty = sum(1 for e in v914_ledger.ingestion_events if e["was_empty"])
    n_phantom_total = len(v914_ledger.phantom_contacts)
    total_gain = sum(e["gain"] for e in v914_ledger.ingestion_events)
    total_received = sum(e["received"] for e in v914_ledger.ingestion_events)
    total_digested = sum(e["digested"] for e in v914_ledger.ingestion_events)
    n_unique_eaters = len({e["observer_cid"] for e in v914_ledger.ingestion_events})
    n_unique_ghosts = len({e["ghost_cid"] for e in v914_ledger.ingestion_events})
    with open(ing_summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "seed", "n_ingestion_events", "n_empty_ingestions",
            "empty_ratio", "n_phantom_contacts",
            "total_gain", "total_received", "total_digested",
            "n_unique_eaters", "n_unique_ghosts",
        ])
        writer.writeheader()
        writer.writerow({
            "seed": seed,
            "n_ingestion_events": n_ing_total,
            "n_empty_ingestions": n_ing_empty,
            "empty_ratio": round(n_ing_empty / n_ing_total, 4) if n_ing_total else 0.0,
            "n_phantom_contacts": n_phantom_total,
            "total_gain": total_gain,
            "total_received": total_received,
            "total_digested": total_digested,
            "n_unique_eaters": n_unique_eaters,
            "n_unique_ghosts": n_unique_ghosts,
        })

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

    # v10.1 Minimal Ingestion: summary stats
    _all_residual_initial = []
    for r in cog._reaped_history:
        _all_residual_initial.append(r.get("initial_residual_Q", 0))
    for cid, q in cog.ghost_residual_Q_initial.items():
        _all_residual_initial.append(q)

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
    # v10.1 Minimal Ingestion summary
    print(f"    --- v10.1 Ingestion ---")
    print(f"    ingestion events: {n_ing_total}")
    print(f"      empty (gain=0): {n_ing_empty} "
          f"({100*n_ing_empty/max(1,n_ing_total):.1f}%)")
    print(f"      total gain:     {total_gain}")
    print(f"      total received: {total_received}")
    print(f"      total digested: {total_digested}")
    print(f"      unique eaters:  {n_unique_eaters}")
    print(f"      unique ghosts:  {n_unique_ghosts}")
    print(f"    phantom contacts: {n_phantom_total}")
    if _all_residual_initial:
        print(f"    initial residual_Q stats:")
        print(f"      mean: {np.mean(_all_residual_initial):.2f}")
        print(f"      max:  {max(_all_residual_initial)}")
        print(f"      >0:   "
              f"{sum(1 for q in _all_residual_initial if q > 0)}/"
              f"{len(_all_residual_initial)}")
    print(f"    conv ratio:    {conv_data.get('ratio')}")

    # ════════════════════════════════════════════════════════════════════
    # v9.13 Step 0: Persistence CSV output (§10)
    # ════════════════════════════════════════════════════════════════════
    persist_dir = outdir / "persistence"

    # 10.1 link_life_log
    csv_ll = persist_dir / f"link_life_log_seed{seed}.csv"
    if v913_link_life_log:
        ll_fields = ["link_id", "node1", "node2", "birth_step", "death_step",
                      "lifetime_steps", "max_age_r_lifetime", "age_r_at_death"]
        with open(csv_ll, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ll_fields)
            writer.writeheader()
            writer.writerows(v913_link_life_log)
        print(f"  v913: link_life_log: {len(v913_link_life_log)} rows -> {csv_ll}")

    # 10.2 link_snapshot_log
    csv_ls = persist_dir / f"link_snapshot_log_seed{seed}.csv"
    if v913_link_snapshot_log:
        ls_fields = ["window", "link_id", "age_r_current", "max_age_r_so_far"]
        with open(csv_ls, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ls_fields)
            writer.writeheader()
            writer.writerows(v913_link_snapshot_log)
        print(f"  v913: link_snapshot_log: {len(v913_link_snapshot_log)} rows -> {csv_ls}")

    # 10.3 label_member_persistence
    csv_lmp = persist_dir / f"label_member_persistence_seed{seed}.csv"
    if v913_label_member_persistence:
        lmp_fields = ["label_id", "birth_window", "n_core", "link_id",
                       "age_r_at_birth", "max_age_r_so_far"]
        with open(csv_lmp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=lmp_fields)
            writer.writeheader()
            writer.writerows(v913_label_member_persistence)
        print(f"  v913: label_member_persistence: {len(v913_label_member_persistence)} rows -> {csv_lmp}")

    # 10.4 shadow_component_log
    csv_sc = persist_dir / f"shadow_component_log_seed{seed}.csv"
    if v913_shadow_component_log:
        sc_fields = ["window", "threshold", "comp_id", "comp_size",
                      "comp_n_links", "comp_age_r_min", "comp_age_r_mean"]
        with open(csv_sc, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sc_fields)
            writer.writeheader()
            writer.writerows(v913_shadow_component_log)
        print(f"  v913: shadow_component_log: {len(v913_shadow_component_log)} rows -> {csv_sc}")

    print(f"  v913 Step 0 persistence audit done. Output: {persist_dir}")

    # ────────────────────────────────────────────────────────────────
    # v9.14 Layer B: audit event summary
    # ────────────────────────────────────────────────────────────────
    v914_event_counts = Counter()
    v914_spend_counts = Counter()  # event_type -> spend 成立回数
    for ev in v914_ledger.events:
        v914_event_counts[ev["v14_event_type"]] += 1
        if ev["v14_spend_flag"]:
            v914_spend_counts[ev["v14_event_type"]] += 1
    v914_q_zero_cids = sum(
        1 for e in v914_ledger.ledger.values()
        if e["v14_q_remaining"] == 0)
    v914_q_neg_cids = sum(
        1 for e in v914_ledger.ledger.values()
        if e["v14_q_remaining"] < 0)
    v914_spent_cids = sum(
        1 for e in v914_ledger.ledger.values()
        if e["v14_q_remaining"] < e["v14_q0"])
    print(f"  v914 Layer B: {len(v914_ledger.ledger)} cid registered, "
          f"{len(v914_ledger.events)} events, "
          f"{v914_spent_cids} cids have spent, "
          f"{v914_q_zero_cids} cids hit Q=0, "
          f"{v914_q_neg_cids} cids Q<0 (MUST be 0)")
    for etype in sorted(v914_event_counts.keys()):
        print(f"    {etype}: {v914_event_counts[etype]} events "
              f"({v914_spend_counts[etype]} spent)")
    if v914_ledger.events:
        v914_deltas = [ev["v14_delta_norm"] for ev in v914_ledger.events]
        print(f"    delta_norm: min={min(v914_deltas):.4f}, "
              f"max={max(v914_deltas):.4f}, "
              f"mean={sum(v914_deltas)/len(v914_deltas):.4f}")
    # Debug: member link R 状態サマリ
    v914_n_r_pos = 0
    v914_n_member_links = 0
    v914_max_links = 0
    v914_cids_with_links = 0
    for e in v914_ledger.ledger.values():
        v914_n_r_pos += len(e["v14_prev_member_r"])
        v914_n_member_links += len(e["v14_prev_member_alive_links"])
        if len(e["v14_prev_member_alive_links"]) > 0:
            v914_cids_with_links += 1
        v914_max_links = max(
            v914_max_links, len(e["v14_prev_member_alive_links"]))
    print(f"    [debug] last step: cids_with_alive_member_links="
          f"{v914_cids_with_links}, total alive member links="
          f"{v914_n_member_links}, max per cid={v914_max_links}, "
          f"R>0 entries={v914_n_r_pos}")
    # Member node size distribution
    v914_node_counts = Counter()
    for e in v914_ledger.ledger.values():
        v914_node_counts[len(e["member_nodes"])] += 1
    print(f"    [debug] member_nodes size distribution: "
          f"{sorted(v914_node_counts.items())}")

    # v9.14 Step 6: audit CSV 出力 (baseline に 1 列も追加しない、§5.3、§8.3)
    v914_ledger.flush_run(outdir, seed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.8c Information Pickup "
                    "(Subject Reversal + Introspection + "
                    "exclusive-competition death-pool pickup, "
                    "TTL-only effect, no feedback)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=10)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--tag", type=str, default="short")
    parser.add_argument(
        "--disable-e3", action="store_true",
        help="§6.4 ablation: E3_contact event の発行を抑止 (E1/E2 は不変、"
             "contacted_pairs 登録は維持、Layer A / baseline CSV は bit-identical)"
    )
    args = parser.parse_args()

    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        tag=args.tag,
        disable_e3=args.disable_e3)
