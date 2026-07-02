# v1304a Stage 3 smoke — lift-profile × per-cid composition（注意が「どの子が生まれるか」を決める）
# Stage 1(初期θ washout)/Stage 2(scalar knob mean-collapse)の板挟みを composition で解く:
#   profile を lift=mean_t(p_select×eligible_count)(露出補正)に置換し、lift 比例で cid を M 体サンプル、
#   各子は v1302 実証チャネル plb←自分の s_avg(per-cid・±15%)。k_sync canonical 固定(幻チャネル交絡切る)・初期θ既定(効かないと確定済)。
# 旧候補B(分析時重み付け)と違い注意が生成前に子集団を決める。read-only・親へfeedbackなし・物理非書込・smoke→停止・#12。
# sparsity: 45はセンターの選別でなく記録の疎性。lift を45支持に制限し外れ質量を eye 別報告。

import sys, os, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304a_stage2_smoke import run_child          # (theta_init, plb, k_sync, seed) 再利用
from v1304a_smoke import tbin, FORMAL_EYES, OUT, SEED, REPO

PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"
SCHEMA = REPO / "unified" / "v1303" / "outputs" / "v1303j" / f"v1303_final_attention_output_seed{SEED}.parquet"
M = 30                 # 群×eye あたり子数(smoke・縮小M)
KSYNC_CANON = 0.1
GROUPS = ["canon", "parent", "shuffle"]   # uniform は canon と同一につき統合・other-parent は full run で


def log(m): print(f"[v1304a-s3] {m}", flush=True)


def load_lift_and_plb():
    sch = pd.read_parquet(SCHEMA)
    sch["pe"] = sch["p_select_given_eye_t"] * sch["eligible_count"]
    lift = sch.groupby(["eye_id", "cid"])["pe"].mean()   # (eye,cid)
    ps = pd.read_csv(PS)
    s_avg = pd.Series(pd.to_numeric(ps["v11_m_c_s_avg"], errors="coerce").values, index=ps["cognitive_id"]).dropna()
    z = (s_avg - s_avg.mean()) / (s_avg.std() + 1e-9)
    plb = 0.007 * (1 + 0.15 * np.tanh(z))                # per-cid plb(cw_run 変換)・45 支持
    return lift, plb


def group_weights(lift_eye, support, group, rng):
    w = lift_eye.reindex(support).fillna(0.0).clip(lower=0)
    if group == "canon":
        w = pd.Series(1.0, index=support)
    elif group == "shuffle":
        w = pd.Series(rng.permutation(w.values), index=support)
    return w / w.sum()


def main():
    t0 = time.time()
    lift, plb = load_lift_and_plb()
    support = np.array(plb.index)     # 45 s_avg 支持
    cov_rows, rows, comp_rows = [], [], []

    for eye in FORMAL_EYES:
        le = lift.loc[eye]
        cov = float(le.reindex(support).fillna(0).sum() / le.sum())
        cov_rows.append(dict(eye=eye, lift_mass_on_45=round(cov, 3), off_mass=round(1 - cov, 3)))
        for group in GROUPS:
            grng = np.random.default_rng(hash(("s3comp", eye, group)) % (2**32))
            w = group_weights(le, support, group, grng)
            drawn = grng.choice(support, size=M, p=w.to_numpy())     # 構成サンプル(重複可)
            for j, cid in enumerate(drawn):
                pl = float(plb.loc[cid])
                comp_rows.append(dict(eye=eye, group=group, child=j, sampled_cid=int(cid), plb=round(pl, 5)))
                for s in run_child(None, pl, KSYNC_CANON, seed=1304000 + j):   # θ既定・k_sync固定
                    rows.append(dict(eye=eye, group=group, child=j, **s, tbin=tbin(s["t"])))
        log(f"eye {eye} done ({time.time()-t0:.0f}s) lift_cov={cov:.2f}")

    df = pd.DataFrame(rows); cov = pd.DataFrame(cov_rows); comp = pd.DataFrame(comp_rows)
    df.to_parquet(OUT / f"v1304a_stage3_signatures_seed{SEED}.parquet")
    cov.to_parquet(OUT / f"v1304a_stage3_lift_seed{SEED}.parquet")
    comp.to_parquet(OUT / f"v1304a_stage3_composition_seed{SEED}.parquet")

    # 個体群署名の群別分布(平均で潰さず・parent-canon/parent-shuffle を noise床=canon の SE と比較)
    sig_cols = ["link_density", "R_density", "sync_order", "n_labels", "label_density", "mean_label_ncore"]
    out = []
    for tb in ["t_mid", "t_late"]:
        g = df[df.tbin == tb]
        for eye in FORMAL_EYES:
            sub = g[g.eye == eye]
            for c in sig_cols:
                mean = sub.groupby("group")[c].mean()
                cstd = sub[sub.group == "canon"][c].std()
                se = cstd / np.sqrt(M)
                out.append(dict(tbin=tb, eye=eye, sig=c,
                                canon=round(float(mean.get("canon", np.nan)), 4),
                                parent=round(float(mean.get("parent", np.nan)), 4),
                                shuffle=round(float(mean.get("shuffle", np.nan)), 4),
                                parent_minus_canon=round(float(mean.get("parent", np.nan) - mean.get("canon", np.nan)), 4),
                                parent_minus_shuffle=round(float(mean.get("parent", np.nan) - mean.get("shuffle", np.nan)), 4),
                                canon_child_std=round(float(cstd), 4), canon_SE=round(float(se), 4)))
    spread = pd.DataFrame(out); spread.to_parquet(OUT / f"v1304a_stage3_spread_seed{SEED}.parquet")

    # plb 分布が群で違うか(composition が per-cid 変動を保っているか＝Stage2 collapse の回避確認)
    plbdist = comp.groupby(["eye", "group"])["plb"].agg(["mean", "std", "min", "max"]).reset_index()

    (OUT / f"v1304a_stage3_summary_seed{SEED}.json").write_text(json.dumps(dict(
        design="v1304a_stage3_composition_smoke", M=M, groups=GROUPS, eyes=FORMAL_EYES,
        n_child=len(FORMAL_EYES)*len(GROUPS)*M, total_s=round(time.time()-t0, 1)), indent=2, ensure_ascii=False))
    log(f"DONE {len(FORMAL_EYES)*len(GROUPS)*M} children {round(time.time()-t0,1)}s")
    return cov, spread, plbdist


if __name__ == "__main__":
    cov, spread, plbdist = main()
    pd.set_option("display.width", 240)
    print("\n=== lift の 45支持内質量(構成に使える割合)・外れ質量 ===")
    print(cov.to_string(index=False))
    print("\n=== plb 分布が群で違うか(composition が per-cid 変動を保つか・Stage2 collapse 回避確認) ===")
    print(plbdist.round(5).to_string(index=False))
    print("\n=== 個体群署名: parent-canon / parent-shuffle vs canon SE(noise床)・t_mid(本体) ===")
    print("  (|parent-canon| や |parent-shuffle| が canon_SE を超えれば noise 以上・分離幅に期待値置かず記述のみ)")
    print(spread[spread.tbin=="t_mid"][["eye","sig","canon","parent","shuffle","parent_minus_canon","parent_minus_shuffle","canon_SE"]].round(4).to_string(index=False))
