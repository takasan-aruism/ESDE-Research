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

# ── in-memory 計装ストア（READ-ONLY 捕捉） ───────────────────────────────────
class Capture:
    def __init__(self):
        self.maturation_step_windows = 0   # step_window 呼び出し回数（maturation=N）
        self.maturation_done = False
        self.track_counter = 0             # tracking 物理 step カウンタ（= pulse t と整合）
        self.snaps = {}                    # t -> {"members":{cid:frozenset},"E":{n:..},"theta":,"Z":,"S":,"R":}
        self.cog = None                    # SubjectLayer instance（live cid<->lid）
        self.engine = None                 # V82Engine instance（engine.virtual=vl）

CAP = Capture()


def _snapshot_members(state, cog, vl):
    """その瞬間の hosted cid -> member_nodes を cog.current_lid + vl.labels から直接取得し、
       member union の物理(E/θ/Z, member 内 link S/R)だけを read-only で控える。
       window カウンタの再構成はしない（live 参照ゆえ厳密）。"""
    members = {}
    union = set()
    for cid, lid in cog.current_lid.items():
        if lid is None:            # ghost（host_lost）→ 第一段階は hosted のみ
            continue
        lab = vl.labels.get(lid)
        if lab is None:
            continue
        nodes = frozenset(int(n) for n in lab["nodes"])
        members[int(cid)] = nodes
        union |= nodes
    alive_n = state.alive_n
    E, th, Z = {}, {}, {}
    for n in union:
        if n in alive_n:           # member だが死んだ node は除外（E dict に無い）
            E[n] = float(state.E[n])
            th[n] = float(state.theta[n])
            Z[n] = int(state.Z[n])
    S, R = {}, {}
    for k in state.alive_l:
        if k[0] in union and k[1] in union:
            kk = (int(k[0]), int(k[1]))
            S[kk] = float(state.S[k])
            R[kk] = float(state.R.get(k, 0.0))
    return {"members": members, "E": E, "theta": th, "Z": Z, "S": S, "R": R}


def install_instrumentation():
    """v105 import 後に呼ぶ。READ-ONLY な monkey-patch のみ（state/RNG 不書込）。"""
    import esde_v82_engine as eng_mod
    import v105_memory_readout as ro
    from realization import RealizationOperator

    # (S1) engine / cog の live 参照を stash（snapshot 時に cid->member_nodes を厳密取得するため）
    _orig_eng_init = eng_mod.V82Engine.__init__
    def patched_eng_init(self, *a, **kw):
        _orig_eng_init(self, *a, **kw)
        CAP.engine = self
    eng_mod.V82Engine.__init__ = patched_eng_init

    _orig_cog_init = ro.SubjectLayer.__init__
    def patched_cog_init(self, *a, **kw):
        _orig_cog_init(self, *a, **kw)
        CAP.cog = self
    ro.SubjectLayer.__init__ = patched_cog_init

    # (A1) step_window: maturation 完了検出（tracking は step_window を使わない）
    _orig_step_window = eng_mod.V82Engine.step_window
    def patched_step_window(self, steps=eng_mod.V82_WINDOW):
        r = _orig_step_window(self, steps=steps)
        CAP.maturation_step_windows += 1
        return r
    eng_mod.V82Engine.step_window = patched_step_window

    # (A2) RealizationOperator.step: tracking 物理 step の先頭で live snapshot。
    #   先頭で控える = state は「直前 step 完了後（bg seeding 込み）」= pulse t と整合。
    #   maturation 中は maturation_done=False ゆえ計上しない。
    _orig_real_step = RealizationOperator.step
    def patched_real_step(self, state):
        if CAP.maturation_done:
            t = CAP.track_counter
            if t % SNAP_EVERY == 0 and CAP.cog is not None and CAP.engine is not None:
                CAP.snaps[t] = _snapshot_members(state, CAP.cog, CAP.engine.virtual)
            CAP.track_counter += 1
        return _orig_real_step(self, state)
    RealizationOperator.step = patched_real_step

    return ro


def run_instrumented(seed, maturation_windows, tracking_windows, window_steps, tag, N=None):
    """v105 run() を計装付きで実行。物理 snapshot と cid<->lid / lid->nodes を捕捉。
       N は plumbing 高速化用の上書きのみ（本 smoke/本番は N=None=V82_N=5000 で alignment と一致）。"""
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
               tracking_windows=tracking_windows, window_steps=window_steps,
               tag=tag, N=N)
    finally:
        os.chdir(cwd0)
    return scratch


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


def build_ledger(seed, window_steps, align=None, subj=None):
    if align is None:
        align = pd.read_csv(ALIGN_DIR / f"step10_cid_alignment_seed{seed}.csv")
    if subj is None:
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

        member_nodes = None
        snap = None
        if status_base == "hosted_available":
            snap = CAP.snaps.get(t)
            if snap is None:
                status_base = "no_snapshot"
            else:
                # snapshot 時に live で控えた cid->member_nodes を厳密 lookup（推測なし）
                member_nodes = snap["members"].get(cid)

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
    ap.add_argument("--mode", choices=["plumbing", "selftest", "smoke"], default="smoke")
    ap.add_argument("--N", type=int, default=None,
                    help="plumbing 高速化用の N 上書きのみ。smoke/本番は未指定(=V82_N=5000)で alignment と一致")
    args = ap.parse_args()

    if args.mode == "smoke" and args.N is not None:
        raise SystemExit("[v1303] smoke モードで --N 上書きは禁止（alignment=N5000 と CID 宇宙不一致 F型）")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[v1303] re-run seed={args.seed} mat={args.maturation_windows} "
          f"track={args.tracking_windows} win={args.window_steps} N={args.N} mode={args.mode}", flush=True)

    run_instrumented(args.seed, args.maturation_windows, args.tracking_windows,
                     args.window_steps, args.tag, N=args.N)

    print(f"[v1303] capture: snaps={len(CAP.snaps)} "
          f"track_steps={CAP.track_counter} cog={'set' if CAP.cog else 'none'} "
          f"engine={'set' if CAP.engine else 'none'}", flush=True)

    if args.mode == "plumbing":
        # 計装が動いたかの最小確認のみ（join しない）
        keys = sorted(CAP.snaps.keys())
        print(f"[plumbing] snap t range: {keys[:5]} ... {keys[-3:] if keys else []}")
        if CAP.snaps:
            anyt = keys[len(keys) // 2]
            s = CAP.snaps[anyt]
            print(f"[plumbing] snap[{anyt}]: cids={len(s['members'])} "
                  f"member_nodes={len(s['E'])} internal_links={len(s['S'])}")
            # 健全性の事前確認: no_internal_link != R0 が両方出るか
            samp = list(s["members"].items())[:3]
            for c, mn in samp:
                il = [k for k in s["S"] if k[0] in mn and k[1] in mn]
                print(f"[plumbing]   cid={c} n_member={len(mn)} internal_links={len(il)}")
        print("[plumbing] OK")
        return

    if args.mode == "selftest":
        # join/lens③/health/欠損判定のコード経路を小N捕捉で offline 検証（~3h run 前のバグ出し）。
        # alignment を CAP.snaps の (cid,t) から合成、static は scratch の per_subject(同じ小N run)を使う。
        scratch = Path(os.environ.get("V1303_SCRATCH", "/tmp/v1303_scratch"))
        subj = pd.read_csv(scratch / f"diag_v105_{args.tag}" / "subjects" / f"per_subject_seed{args.seed}.csv")
        synth = []
        for t, s in sorted(CAP.snaps.items()):
            for cid in s["members"]:
                synth.append({"cognitive_id": cid, "t": t, "n_core_member": len(s["members"][cid]),
                              "C_at_window_end": 0.0, "Q_remaining_at_window_end": 0.0,
                              "rank_1_atom": "SELFTEST", "rank_1_sim": 0.0})
        # ghost/reaped 経路も踏むため、各 cid の host_lost 以降の t も少し混ぜる
        align = pd.DataFrame(synth)
        print(f"[selftest] synthesized alignment rows={len(align)} from {len(CAP.snaps)} snaps")
        df = build_ledger(args.seed, args.window_steps, align=align, subj=subj)
        hc = health_checks(df)
        sc = df["phys_core_status"].value_counts().to_dict()
        nli = int(df["no_internal_link"].sum())
        r0 = int(((df["core_internal_link_count"].fillna(-1) > 0)
                  & (df["core_internal_R_positive_count"].fillna(-1) == 0)).sum())
        rpos = int((df["core_internal_R_positive_count"].fillna(0) > 0).sum())
        print(f"[selftest] ledger rows={len(df)} cols={len(df.columns)}")
        print(f"[selftest] phys_core_status: {sc}")
        print(f"[selftest] no_internal_link rows={nli} | internal_link_R0 rows={r0} | R_positive rows={rpos}")
        print(f"[selftest] E_mean notna={int(df['core_node_E_mean'].notna().sum())} "
              f"theta_rl notna={int(df['core_node_theta_resultant_length'].notna().sum())}")
        print(f"[selftest] health: {hc}")
        print("[selftest] OK")
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
