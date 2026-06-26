#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303 Step B — CID 索引 read-only multi-view ledger（3レンズ同居）
#
# 規律宣言（Code A / 失敗記録12型・最低限規律）
#  1. 読/書: READ-ONLY で読むもの = 既存 v105 main_v2 出力
#       (developmental/v105/diag_v105_main_v2/subjects/per_subject_seed{N}.csv = レンズ①static),
#       (developmental/v106/outputs/main/step10_trajectory/step10_cid_alignment_seed{N}.csv
#        = レンズ②rank_1 + レンズ①dynamic C/Q, 既算出 join),
#       および v105 main run の再現(engine.state を read-only 吸い出し = レンズ③)。
#     書き込みは unified/v1303/ 配下のみ。canonical 再走の副産物(per_subject 等)は
#     scratch cwd に出し、親 diag_v105_main_v2 を一切上書きしない。
#  2. 使う LIVE 機構: v105 run()(V82Engine+VirtualLayerV9)・engine.state read・
#       step10 alignment join・per_subject static。
#     使わない FROZEN/別系: v918 系(F型/E型: anchor は v105_v2 に統一)・torque/lambda/
#       注意センター/関係計算(L型)・rank_1_margin/disposition per-t/residual_phys(J型・第二段階退避)。
#  3. 接触しうる失敗型と回避:
#       B型(物理介入) → engine.state は read-only 吸い出しのみ。RNG を引かない。state 不書込。
#                       親 physics/inject/ledger/state/per_subject 非書込。in-memory 計装。
#       E型/F型(層/異系混同) → anchor=v105_v2 統一。cognitive_id を主語に。別 seed を繋がない。
#       L型(意味盛り) → 列名は乾いた名前。operator を足さない。素の値のみ。
#       J型(運用) → 観察を増やさない。(a)/(b)判定しない。smoke 後は止まる。
#  4. 実装ガード:
#       - anchor = developmental/v105/diag_v105_main_v2（v918 混ぜない）。
#       - no_internal_link(member 内 link が alive_l に無い)と internal_link_R0(link あり R=0)を
#         区別。no link は S/R を null(NaN)で記録、0 で埋めない（n_core=2 偽ゼロ埋め防止）。
#       - final per_subject 値を step10 全行に雑貼りしない。static(誕生時固定)のみ全 t 定数貼り。
#         dynamic は per-t(step10 alignment)。disposition は per-t 源が無く欠損フラグのみ。
#       - 計装は read-only hook（state 不書込・RNG 不使用）→ bit-identity 不変（Step E で検証）。
#  判定は Web Claude / Taka。本スクリプトは観察事実(ledger + 欠損構造)のみ生成する。
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
V105_DIR = REPO / "developmental" / "v105"
ALIGN_DIR = REPO / "developmental" / "v106" / "outputs" / "main" / "step10_trajectory"
SUBJ_DIR = V105_DIR / "diag_v105_main_v2" / "subjects"
OUT_DIR = REPO / "unified" / "v1303" / "outputs"

# v105 が import する兄弟モジュール群の所在を path に通す（v105 ディレクトリから回す前提のコード）
for p in [
    V105_DIR,
    REPO / "autonomy" / "v82",
    REPO / "autonomy" / "v90",
    REPO / "cognition" / "semantic_injection" / "v4_pipeline" / "v43",
    REPO / "ecology" / "engine",
    REPO / "primitive" / "v918",
    REPO / "primitive" / "v911",
]:
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

SNAP_EVERY = 10           # tracking step10 grid（alignment STEP_GRAIN=10 と一致）
WINDOW_STEPS = 500        # main_v2

# ── in-memory 計装ストア（READ-ONLY 捕捉） ───────────────────────────────────
class Capture:
    def __init__(self):
        self.maturation_step_windows = 0   # step_window 呼び出し回数（maturation=20）
        self.maturation_done = False
        self.track_counter = 0             # tracking 物理 step カウンタ（= pulse t と整合）
        self.snaps = {}                    # t -> {"E":{n:..},"theta":{..},"Z":{..},"S":{(i,j):..},"R":{..}}
        self.birth_log = []                # (window_count_at_birth, cid, lid)
        self.detach_log = []               # (window, cid, lid)
        self.labels_by_window = {}         # window_count -> {lid: frozenset(nodes)}
        self.cid_of_lid_birth = {}         # lid -> cid（birth 時点で確定）

CAP = Capture()


def _snapshot_state(state):
    alive_n = list(state.alive_n)
    E = {int(n): float(state.E[n]) for n in alive_n}
    th = {int(n): float(state.theta[n]) for n in alive_n}
    Z = {int(n): int(state.Z[n]) for n in alive_n}
    S = {}
    R = {}
    for k in state.alive_l:
        kk = (int(k[0]), int(k[1]))
        S[kk] = float(state.S[k])
        R[kk] = float(state.R.get(k, 0.0))
    return {"E": E, "theta": th, "Z": Z, "S": S, "R": R}


def install_instrumentation():
    """v105 import 後に呼ぶ。READ-ONLY な monkey-patch のみ。"""
    import esde_v82_engine as eng_mod
    import v105_memory_readout as ro
    from realization import RealizationOperator
    from virtual_layer_v9 import VirtualLayer

    # (A1) step_window: maturation 完了検出（tracking は step_window を使わない）
    _orig_step_window = eng_mod.V82Engine.step_window
    def patched_step_window(self, steps=eng_mod.V82_WINDOW):
        r = _orig_step_window(self, steps=steps)
        CAP.maturation_step_windows += 1
        return r
    eng_mod.V82Engine.step_window = patched_step_window

    # (A2) RealizationOperator.step: tracking 物理 step の先頭で全 node/link を snapshot
    #   現状 RealizationOperator.step は engine_accel が高速版に差し替え済の場合がある。
    #   実行時に有効な step を包む（その上で read-only 観測のみ追加）。
    _orig_real_step = RealizationOperator.step
    def patched_real_step(self, state):
        # maturation_done は run() 側の「20 step_window 完了」で立てる（下の run ラッパで設定）
        if CAP.maturation_done:
            t = CAP.track_counter
            if t % SNAP_EVERY == 0:
                CAP.snaps[t] = _snapshot_state(state)
            CAP.track_counter += 1
        return _orig_real_step(self, state)
    RealizationOperator.step = patched_real_step

    # (B) SubjectLayer.birth / detach: cid<->lid 遷移を window 付きで記録
    _orig_birth = ro.SubjectLayer.birth
    def patched_birth(self, lid, phase_sig, current_window):
        cid = _orig_birth(self, lid, phase_sig, current_window)
        CAP.cid_of_lid_birth[lid] = cid
        CAP.birth_log.append((int(current_window), int(cid), int(lid)))
        return cid
    ro.SubjectLayer.birth = patched_birth

    _orig_detach = ro.SubjectLayer.detach
    def patched_detach(self, lid, current_window, residual_Q=0, current_step=None):
        cid = self.cid_of_lid.get(lid)
        r = _orig_detach(self, lid, current_window,
                         residual_Q=residual_Q, current_step=current_step)
        if cid is not None:
            CAP.detach_log.append((int(current_window), int(cid), int(lid)))
        return r
    ro.SubjectLayer.detach = patched_detach

    # (C) VirtualLayer.step: 各 window の lid->member_nodes を記録（tracking 境界で呼ばれる）
    _orig_vl_step = VirtualLayer.step
    def patched_vl_step(self, state, window_count, **kw):
        r = _orig_vl_step(self, state, window_count, **kw)
        macro = set(self.macro_nodes)
        CAP.labels_by_window[int(window_count)] = {
            int(lid): frozenset(int(n) for n in lab["nodes"])
            for lid, lab in self.labels.items() if lid not in macro
        }
        return r
    VirtualLayer.step = patched_vl_step

    return ro


def run_instrumented(seed, maturation_windows, tracking_windows, window_steps, tag):
    """v105 run() を計装付きで実行。物理 snapshot と cid<->lid / lid->nodes を捕捉。"""
    ro = install_instrumentation()

    # maturation_done を「step_window が maturation_windows 回完了した瞬間」に立てる。
    # run() は maturation で step_window を maturation_windows 回呼ぶ → tracking 開始前に成立。
    import esde_v82_engine as eng_mod
    _sw = eng_mod.V82Engine.step_window
    def gated_step_window(self, steps=eng_mod.V82_WINDOW):
        r = _sw(self, steps=steps)
        if CAP.maturation_step_windows >= maturation_windows:
            CAP.maturation_done = True
        return r
    eng_mod.V82Engine.step_window = gated_step_window

    # canonical 副産物は scratch cwd に出す（親 diag を汚さない）
    scratch = Path(os.environ.get("V1303_SCRATCH", "/tmp/v1303_scratch"))
    scratch.mkdir(parents=True, exist_ok=True)
    cwd0 = os.getcwd()
    os.chdir(scratch)
    try:
        ro.run(seed=seed, maturation_windows=maturation_windows,
               tracking_windows=tracking_windows, window_steps=window_steps, tag=tag)
    finally:
        os.chdir(cwd0)
    return scratch


def reconstruct_cid_member_nodes(cid, t, window_steps):
    """tracking step t における cid の member_nodes(frozenset)と存在状態を返す。
       cid->lid は birth/detach ログから、lid->nodes は labels_by_window から。"""
    # t は tracking step。labels_by_window の window_count は maturation 込みの絶対 window。
    # tracking step t が属する絶対 window:
    tw = t // window_steps
    # birth/detach の window は run() の current_window 引数（maturation 末で birth → maturation-1、
    # tracking 中の birth は絶対 window）。最も近い window スナップを使う。
    abs_window = None
    if CAP.labels_by_window:
        # tracking window の vl.step は window_count = maturation + tw 付近で呼ばれる。
        cand = [w for w in CAP.labels_by_window.keys()]
        # tw に対応する最大の window_count（その window 終了時のラベル状態）を選ぶ
        target = max(cand)  # 既定: 最新
        # tw に最も近い（超えない最大）window を選ぶ
        le = [w for w in cand if w <= max(cand)]
        # 絶対 window 推定: 最小 window_count を maturation 相当とみなし tw を足す
        base = min(cand)
        guess = base + tw
        target = min(cand, key=lambda w: abs(w - guess))
        abs_window = target
    labels = CAP.labels_by_window.get(abs_window, {}) if abs_window is not None else {}

    # cid の現在 lid（birth/detach を window 順に畳んで t 時点の現在 lid を求める）
    cur_lid = None
    for (w, c, lid) in sorted(CAP.birth_log):
        if c == cid and w <= (min(CAP.labels_by_window or [0]) + tw):
            cur_lid = lid
    for (w, c, lid) in sorted(CAP.detach_log):
        if c == cid and lid == cur_lid and w <= (min(CAP.labels_by_window or [0]) + tw):
            cur_lid = None
    nodes = labels.get(cur_lid) if cur_lid is not None else None
    return cur_lid, nodes


def circular_mean(theta_vals):
    if len(theta_vals) == 0:
        return float("nan"), float("nan")
    c = np.mean(np.cos(theta_vals))
    s = np.mean(np.sin(theta_vals))
    return float(math.atan2(s, c)), float(math.hypot(c, s))


def lens3_row(cid, t, member_nodes, snap, status_base):
    """レンズ③ phys_core を「乾かして」計算。no_internal_link != internal_link_R0 を厳守。"""
    out = dict(
        core_node_E_mean=np.nan, core_node_E_std=np.nan,
        core_node_theta_circular_mean=np.nan, core_node_theta_resultant_length=np.nan,
        core_node_Z_counts="", n_member_nodes=0, n_member_alive=0,
        core_internal_link_count=np.nan, core_internal_S_mean=np.nan,
        core_internal_S_max=np.nan, core_internal_R_mean=np.nan,
        core_internal_R_max=np.nan, core_internal_R_positive_count=np.nan,
        no_internal_link=False, phys_core_status=status_base,
    )
    if status_base != "hosted_available":
        return out
    if not member_nodes:
        out["phys_core_status"] = "missing_member_nodes"
        return out
    if snap is None:
        out["phys_core_status"] = "no_snapshot"
        return out

    E, TH, Z = snap["E"], snap["theta"], snap["Z"]
    alive = [n for n in member_nodes if n in E]
    out["n_member_nodes"] = len(member_nodes)
    out["n_member_alive"] = len(alive)
    if not alive:
        out["phys_core_status"] = "missing_member_nodes"
        return out

    e_vals = np.array([E[n] for n in alive], dtype=float)
    th_vals = np.array([TH[n] for n in alive], dtype=float)
    out["core_node_E_mean"] = float(np.mean(e_vals))
    out["core_node_E_std"] = float(np.std(e_vals))
    cm, rl = circular_mean(th_vals)
    out["core_node_theta_circular_mean"] = cm
    out["core_node_theta_resultant_length"] = rl
    zc = defaultdict(int)
    for n in alive:
        zc[int(Z[n])] += 1
    out["core_node_Z_counts"] = ";".join(f"{k}:{zc[k]}" for k in sorted(zc))

    # member 内 link（両端 member）
    mset = set(member_nodes)
    Sd, Rd = snap["S"], snap["R"]
    internal = [(k, Sd[k], Rd.get(k, 0.0)) for k in Sd
                if k[0] in mset and k[1] in mset]
    if len(internal) == 0:
        # no_internal_link: S/R は null のまま（0 で埋めない）。count は 0 を明示。
        out["core_internal_link_count"] = 0
        out["no_internal_link"] = True
        return out
    s_arr = np.array([x[1] for x in internal], dtype=float)
    r_arr = np.array([x[2] for x in internal], dtype=float)
    out["core_internal_link_count"] = len(internal)
    out["core_internal_S_mean"] = float(np.mean(s_arr))
    out["core_internal_S_max"] = float(np.max(s_arr))
    out["core_internal_R_mean"] = float(np.mean(r_arr))
    out["core_internal_R_max"] = float(np.max(r_arr))
    out["core_internal_R_positive_count"] = int(np.sum(r_arr > 0))
    return out


def build_ledger(seed, window_steps):
    align = pd.read_csv(ALIGN_DIR / f"step10_cid_alignment_seed{seed}.csv")
    subj = pd.read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")

    static_cols = ["cognitive_id", "v11_b_gen", "v11_m_c_n_core", "v11_m_c_s_avg",
                   "v11_m_c_r_core", "v11_m_c_phase_sig", "original_phase_sig",
                   "birth_window", "host_lost_step", "reaped_step", "final_state"]
    static = subj[[c for c in static_cols if c in subj.columns]].copy()

    rows = []
    for _, a in align.iterrows():
        cid = int(a["cognitive_id"])
        t = int(a["t"])
        srow = static[static["cognitive_id"] == cid]
        srow = srow.iloc[0] if len(srow) else None

        host_lost = srow["host_lost_step"] if srow is not None else np.nan
        reaped = srow["reaped_step"] if srow is not None else np.nan
        # cid_status at t
        if not pd.isna(reaped) and t >= reaped:
            cid_status = "reaped"
        elif not pd.isna(host_lost) and t >= host_lost:
            cid_status = "ghost"
        else:
            cid_status = "hosted"

        # 第一段階 = hosted_phys_core のみ
        if cid_status == "reaped":
            status_base = "reaped"
        elif cid_status == "ghost":
            status_base = "ghost_host_lost"
        else:
            status_base = "hosted_available"

        lid, member_nodes = (None, None)
        snap = None
        if status_base == "hosted_available":
            lid, member_nodes = reconstruct_cid_member_nodes(cid, t, window_steps)
            snap = CAP.snaps.get(t)
            if snap is None:
                status_base = "no_snapshot"

        l3 = lens3_row(cid, t, member_nodes, snap, status_base)

        row = dict(
            seed=seed, cid=cid, t=t, t_unit="tracking_step",
            window_id=t // window_steps, step=t, cid_status=cid_status,
            # 必須列 source_granularity は per-lens で持つ
            # レンズ① static（誕生時固定 → 全 t 定数貼り可）
            static_source_granularity="birth_fixed",
            v11_b_gen=(srow["v11_b_gen"] if srow is not None else np.nan),
            v11_m_c_n_core=(srow["v11_m_c_n_core"] if srow is not None else np.nan),
            v11_m_c_s_avg=(srow["v11_m_c_s_avg"] if srow is not None else np.nan),
            v11_m_c_r_core=(srow["v11_m_c_r_core"] if srow is not None else np.nan),
            v11_m_c_phase_sig=(srow["v11_m_c_phase_sig"] if srow is not None else np.nan),
            original_phase_sig=(srow["original_phase_sig"] if srow is not None else np.nan),
            birth_window=(srow["birth_window"] if srow is not None else np.nan),
            n_core=int(a["n_core_member"]) if not pd.isna(a.get("n_core_member")) else np.nan,
            # レンズ① dynamic（per-t = step10 alignment）
            dynamic_source_granularity="step10_window",
            C_at_window_end=a.get("C_at_window_end", np.nan),
            Q_remaining_at_window_end=a.get("Q_remaining_at_window_end", np.nan),
            disposition_pt_status="no_per_t_source",  # §0.3: per-t 源なし。final 貼り禁止
            # レンズ② rank_1（既算出 join）
            lens2_source_granularity="step10",
            rank_1_atom=a.get("rank_1_atom"),
            rank_1_sim=a.get("rank_1_sim", np.nan),
            cid48_source_id=f"{seed}:{cid}:{t}",
            # レンズ③ phys_core（再走吸い出し）
            lens3_source_granularity="rerun_step10",
            current_lid=lid,
        )
        row.update(l3)
        rows.append(row)

    return pd.DataFrame(rows)


def health_checks(df):
    out = {}
    # 健全性1: ghost 境界で phys_core が一斉欠損へ反転（is_ghost XOR is_phys_missing == 0）
    is_ghost = df["cid_status"].isin(["ghost", "reaped"])
    is_phys_missing = df["phys_core_status"] != "hosted_available"
    xor = (is_ghost ^ is_phys_missing)
    out["health1_xor_violations"] = int(xor.sum())
    out["health1_total_rows"] = int(len(df))
    # 健全性2: n_core=2 vs 5 で R_positive 生存率が分離するか（生データ行から直接）
    h = df[df["phys_core_status"] == "hosted_available"].copy()
    for nc in [2, 5]:
        sub = h[h["n_core"] == nc]
        if len(sub):
            frac = float((sub["core_internal_R_positive_count"].fillna(0) > 0).mean())
            out[f"health2_n{nc}_Rpos_frac"] = round(frac, 4)
            out[f"health2_n{nc}_rows"] = int(len(sub))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--maturation-windows", type=int, default=20)
    ap.add_argument("--tracking-windows", type=int, default=50)
    ap.add_argument("--window-steps", type=int, default=500)
    ap.add_argument("--tag", type=str, default="v1303smoke")
    ap.add_argument("--mode", choices=["plumbing", "smoke"], default="smoke")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[v1303] re-run seed={args.seed} mat={args.maturation_windows} "
          f"track={args.tracking_windows} win={args.window_steps} mode={args.mode}", flush=True)

    run_instrumented(args.seed, args.maturation_windows, args.tracking_windows,
                     args.window_steps, args.tag)

    print(f"[v1303] capture: snaps={len(CAP.snaps)} births={len(CAP.birth_log)} "
          f"detaches={len(CAP.detach_log)} label_windows={len(CAP.labels_by_window)} "
          f"track_steps={CAP.track_counter}", flush=True)

    if args.mode == "plumbing":
        # 計装が動いたかの最小確認のみ（join しない）
        sample_t = sorted(CAP.snaps.keys())[:5]
        print(f"[plumbing] sample snap t: {sample_t}")
        if CAP.snaps:
            anyt = next(iter(CAP.snaps))
            s = CAP.snaps[anyt]
            print(f"[plumbing] snap[{anyt}]: nodes={len(s['E'])} links={len(s['S'])}")
        if CAP.labels_by_window:
            w = max(CAP.labels_by_window)
            print(f"[plumbing] labels_by_window[{w}]: {len(CAP.labels_by_window[w])} labels")
        print("[plumbing] OK")
        return

    df = build_ledger(args.seed, args.window_steps)
    ledger_path = OUT_DIR / f"v1303_ledger_seed{args.seed}.parquet"
    df.to_parquet(ledger_path, index=False)

    hc = health_checks(df)
    n_all3 = int(((df["phys_core_status"] == "hosted_available")
                  & df["rank_1_atom"].notna()
                  & df["v11_b_gen"].notna()).sum())
    status_counts = df["phys_core_status"].value_counts().to_dict()

    print(f"[v1303] ledger rows={len(df)} -> {ledger_path}")
    print(f"[v1303] 3-lens hosted+rank1+static rows={n_all3}")
    print(f"[v1303] phys_core_status: {status_counts}")
    print(f"[v1303] health: {hc}")


if __name__ == "__main__":
    main()
