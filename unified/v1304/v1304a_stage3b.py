# v1304a Stage 3b — Stage 3 の統計的やり直し（inconclusive の解消・新観察軸は足さない #5）
# 修正: (1) lift 2定義併記(eligible-only=primary / alive=参考) (2) R回composition リサンプル・draw単位paired
#       (3) primary contrast=parent-shuffle 事前固定 + Holm補正 + 符号一貫性 (4) 子側 draw毎seed変化(seed変動を内包)
# 変えない: 問い(親特異②)・写像(lift×per-cid composition・plb←s_avg・k_sync固定・θ既定)・群(canon/parent/shuffle)
# 親profileは v1303 final(seed0)のみ→「親seed0に条件付けた結論」と明記。read-only・親へfeedbackなし・物理非書込・#12。

import sys, os, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304a_smoke import signature, tbin, FORMAL_EYES, OUT, SEED, REPO
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"
SCHEMA = REPO / "unified" / "v1303" / "outputs" / "v1303j" / f"v1303_final_attention_output_seed{SEED}.parquet"
R = int(os.environ.get("S3B_R", 20))      # composition リサンプル回数(分析単位=draw)
M = int(os.environ.get("S3B_M", 30))      # draw あたり子数
BASE = int(os.environ.get("S3B_BASE", 0)) # base seed series
N_CHILD, KSYNC_CANON, STEPS, WIN = 150, 0.1, 300, 50
GROUPS = ["canon", "parent", "shuffle"]
SIG_COLS = ["link_density", "R_density", "sync_order", "n_labels", "label_density", "mean_label_ncore"]
EYE_IDX = {e: i for i, e in enumerate(FORMAL_EYES)}
GRP_IDX = {g: i for i, g in enumerate(GROUPS)}


def log(m): print(f"[s3b] {m}", flush=True)


def load():
    sch = pd.read_parquet(SCHEMA)
    sch["pe"] = sch["p_select_given_eye_t"] * sch["eligible_count"]
    lift_alive = sch.groupby(["eye_id", "cid"])["pe"].mean()                       # 参考(露出混入)
    lift_elig = sch[sch["p_select_given_eye_t"] > 0].groupby(["eye_id", "cid"])["pe"].mean()  # primary
    ps = pd.read_csv(PS)
    s_avg = pd.Series(pd.to_numeric(ps["v11_m_c_s_avg"], errors="coerce").values, index=ps["cognitive_id"]).dropna()
    z = (s_avg - s_avg.mean()) / (s_avg.std() + 1e-9)
    plb = 0.007 * (1 + 0.15 * np.tanh(z))
    return lift_elig, lift_alive, s_avg, plb


def weights(lift_eye, support, group, rng):
    w = lift_eye.reindex(support).fillna(0.0).clip(lower=0)
    if group == "canon":
        w = pd.Series(1.0, index=support)
    elif group == "shuffle":
        w = pd.Series(rng.permutation(w.values), index=support)
    return (w / w.sum()).to_numpy()


def run_child(plb, seed):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N_CHILD, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [("torque_order", "age"), ("deviation_enabled", True), ("semantic_gravity_enabled", True)]:
        if hasattr(eng.virtual, a): setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = KSYNC_CANON
    eng.pressure_params.pressure_prob = 0.0
    eng.run_injection()                       # θ既定・shapingしない
    out = {}
    for w in range(STEPS // WIN):
        eng.step_window(steps=WIN)
        t = (w + 1) * WIN; tb = tbin(t)
        if tb in ("t_mid", "t_late"):
            out.setdefault(tb, []).append(signature(eng))
    # window 平均で t区分代表
    return {tb: {c: float(np.mean([s[c] for s in v])) for c in SIG_COLS} for tb, v in out.items()}


def main():
    t0 = time.time()
    lift_elig, lift_alive, s_avg, plb = load()
    support = np.array(plb.index)
    # corr(lift, s_avg) 両定義(profile レベル・定義依存の開示)
    corr_rows = []
    for eye in FORMAL_EYES:
        for name, L in [("eligible", lift_elig), ("alive", lift_alive)]:
            le = L.loc[eye].reindex(support)
            v = le.notna()
            r = float(np.corrcoef(le[v].values, s_avg.loc[support][v].values)[0, 1]) if v.sum() > 3 else np.nan
            corr_rows.append(dict(eye=eye, lift_def=name, corr_lift_savg=round(r, 4), n_support=int(v.sum())))
    pd.DataFrame(corr_rows).to_parquet(OUT / f"v1304a_stage3b_liftcorr_seed{SEED}.parquet")

    # 本体: R draws × 群 × M子。primary composition weight = lift_eligible。
    # draw内で engine seed を群間 match（paired）、draw間で変える（seed変動）。
    draw_means = []   # (eye, draw, group, tbin, sig) の population mean
    for eye in FORMAL_EYES:
        le = lift_elig.loc[eye]
        for r in range(R):
            # 群間で同じ engine seed 集合（matched）・comp rng は群別・draw別に決定論
            eng_seeds = [BASE * 10_000_000 + r * 10_000 + j for j in range(M)]
            gw = {}
            for g in GROUPS:
                crng = np.random.default_rng((BASE, EYE_IDX[eye], GRP_IDX[g], r, 777))
                gw[g] = crng.choice(support, size=M, p=weights(le, support, g, crng))
            for g in GROUPS:
                acc = {"t_mid": {c: [] for c in SIG_COLS}, "t_late": {c: [] for c in SIG_COLS}}
                for j in range(M):
                    res = run_child(float(plb.loc[gw[g][j]]), eng_seeds[j])
                    for tb in acc:
                        if tb in res:
                            for c in SIG_COLS: acc[tb][c].append(res[tb][c])
                for tb in acc:
                    row = dict(eye=eye, draw=r, group=g, tbin=tb)
                    for c in SIG_COLS: row[c] = float(np.mean(acc[tb][c])) if acc[tb][c] else np.nan
                    draw_means.append(row)
        log(f"eye {eye} done ({time.time()-t0:.0f}s)")
    dm = pd.DataFrame(draw_means)
    dm.to_parquet(OUT / f"v1304a_stage3b_drawmeans_seed{SEED}_base{BASE}.parquet")

    # draw単位 paired 差 → R個の分布で検定(1標本t)。primary=parent-shuffle。
    def contrast(dm, a, b):
        pa = dm[dm.group == a].set_index(["eye", "draw", "tbin"])[SIG_COLS]
        pb = dm[dm.group == b].set_index(["eye", "draw", "tbin"])[SIG_COLS]
        return (pa - pb).reset_index()
    tests = []
    for cname, (a, b) in {"parent_minus_shuffle": ("parent", "shuffle"),
                          "parent_minus_canon": ("parent", "canon"),
                          "shuffle_minus_canon": ("shuffle", "canon")}.items():
        d = contrast(dm, a, b)
        for tb in ["t_mid", "t_late"]:
            for eye in FORMAL_EYES:
                sub = d[(d.eye == eye) & (d.tbin == tb)]
                for c in SIG_COLS:
                    x = sub[c].dropna().values
                    if len(x) >= 3 and np.std(x) > 0:
                        tstat, p = stats.ttest_1samp(x, 0.0)
                        sign_consist = float(np.mean(np.sign(x) == np.sign(np.mean(x))))
                    else:
                        tstat, p, sign_consist = np.nan, np.nan, np.nan
                    tests.append(dict(contrast=cname, tbin=tb, eye=eye, sig=c, R=len(x),
                                      mean_diff=round(float(np.mean(x)), 5) if len(x) else np.nan,
                                      t=round(float(tstat), 3), p_raw=float(p) if not np.isnan(p) else np.nan,
                                      sign_consistency=round(sign_consist, 3) if not np.isnan(sign_consist) else np.nan))
    tests = pd.DataFrame(tests)
    # Holm 補正: primary family = parent_minus_shuffle × t_mid（本体）× 6sig × 4eye = 24
    fam = tests[(tests.contrast == "parent_minus_shuffle") & (tests.tbin == "t_mid") & tests.p_raw.notna()].copy()
    fam = fam.sort_values("p_raw").reset_index(drop=True)
    m = len(fam); holm = np.full(m, np.nan)
    for i in range(m):
        holm[i] = min(1.0, (m - i) * fam.loc[i, "p_raw"])
    holm = np.maximum.accumulate(holm)  # 単調化
    fam["p_holm"] = holm.round(4)
    fam["sig_holm_.05"] = fam["p_holm"] < 0.05
    tests = tests.merge(fam[["contrast", "tbin", "eye", "sig", "p_holm", "sig_holm_.05"]],
                        on=["contrast", "tbin", "eye", "sig"], how="left")
    tests["p_raw"] = tests["p_raw"].round(4)
    tests.to_parquet(OUT / f"v1304a_stage3b_tests_seed{SEED}_base{BASE}.parquet")
    (OUT / f"v1304a_stage3b_summary_seed{SEED}_base{BASE}.json").write_text(json.dumps(dict(
        design="v1304a_stage3b_paired_resample", R=R, M=M, base=BASE, lift_primary="eligible",
        parent_profile="v1303_final_seed0_only", n_child=len(FORMAL_EYES)*R*len(GROUPS)*M,
        total_s=round(time.time()-t0, 1)), indent=2, ensure_ascii=False))
    log(f"DONE {len(FORMAL_EYES)*R*len(GROUPS)*M} children {round(time.time()-t0,1)}s")
    return pd.DataFrame(corr_rows), tests, fam


if __name__ == "__main__":
    corr, tests, fam = main()
    pd.set_option("display.width", 240)
    print("\n=== corr(lift,s_avg) 両定義(定義依存の開示) ===")
    print(corr.to_string(index=False))
    print("\n=== primary: parent-shuffle @ t_mid（Holm補正・符号一貫性・生t併記） ===")
    print(fam.sort_values("p_raw")[["eye","sig","mean_diff","t","p_raw","p_holm","sig_holm_.05","sign_consistency"]].to_string(index=False))
    print("\n=== 参考: shuffle-canon(null-null床) と parent-canon @ t_mid ===")
    for cn in ["shuffle_minus_canon","parent_minus_canon"]:
        s=tests[(tests.contrast==cn)&(tests.tbin=="t_mid")].sort_values("p_raw")
        print(f"\n[{cn}] 上位:")
        print(s.head(6)[["eye","sig","mean_diff","t","p_raw","sign_consistency"]].to_string(index=False))
