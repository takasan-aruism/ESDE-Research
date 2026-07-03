# v1304b full — feedback loop 本番(レプリカ null で primary を閉じる)
# 指示: Web Claude v1304b full(2026-07-03)。read-only・親物理 hash 検証継続・書込 unified/v1304/outputs 配下・判定なし#12。
#
# 核=レプリカ null(子ゼロ追加の算術):
#   各 R 系列で K 本の shuffle レプリカを feedback の同一世界(drawn/子/salience)に相乗り・別 permutation rng で対応破壊・各自 weight。
#   D_fb   = mean_k mean_round L1(w_feedback, w_shuffle_k)
#   D_null = mean_{i<j} mean_round L1(w_shuffle_i, w_shuffle_j)      ← 対応なし同士の発散床
#   primary(事前固定1本) = 系列ごと paired 差 (D_fb - D_null) を R 系列で 1標本t。base0/1 再現・符号一貫性。結果を見て指標/検定を変えない。
# secondary(primary と混ぜない): entropy差 / 独立composition shuffle(別の問い=閉ループ同士の世界分岐・1系統) / 世界応答descriptive / g=0.5参考
# smoke から継続: 親物理 hash 前後・provenance 全保存・raw/rank 両保存(rankは監査のみ)・eps floor 正規化前・cid単位平均・undrawn factor=1・round0 support ログ
# 成果表現: primary が立っても「対応が weight 軌跡を方向づけた(レプリカ床超え)」まで(L型: 学習/自律と言わない)。立たねば「対応の効きはレプリカ床内」。

import sys, os, json, time, hashlib, warnings
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304a_smoke import signature, OUT, SEED, REPO
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

PS = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / f"per_subject_seed{SEED}.csv"
SCHEMA = REPO / "unified" / "v1303" / "outputs" / "v1303j" / f"v1303_final_attention_output_seed{SEED}.parquet"

T = int(os.environ.get("V1304B_T", 8))
M = int(os.environ.get("V1304B_M", 20))
K = int(os.environ.get("V1304B_K", 10))     # shuffle レプリカ本数
N_WORKERS = int(os.environ.get("V1304B_W", 24))
EPS = 1e-6
LENS = "link_density"
INIT_EYE = "now_theta"
N_CHILD, KSYNC_CANON, STEPS, WIN = 150, 0.1, 300, 50
SIG_COLS = ["link_density", "R_density", "sync_order", "n_labels", "label_density", "mean_label_ncore"]
# 本線 + g=0.5 参考(R5 base0)
CONFIGS = [dict(g=1.0, base=0, R=12), dict(g=1.0, base=1, R=12), dict(g=0.5, base=0, R=5)]


def log(m): print(f"[v1304b-full] {m}", flush=True)
def md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()
def entropy(w):
    w = np.asarray(w, float); w = w[w > 0]; return float(-(w * np.log(w)).sum())


def rarity(vals):
    v = pd.Series(np.asarray(vals, float)); n = len(v)
    pct = v.rank(pct=True).values
    two = np.clip(2 * np.minimum(pct, 1 - pct), 1.0 / (2 * n), None)
    return -np.log10(two)


def load_init():
    sch = pd.read_parquet(SCHEMA)
    sch["pe"] = sch["p_select_given_eye_t"] * sch["eligible_count"]
    lift = sch[sch["p_select_given_eye_t"] > 0].groupby(["eye_id", "cid"])["pe"].mean().loc[INIT_EYE]
    ps = pd.read_csv(PS)
    s_avg = pd.Series(pd.to_numeric(ps["v11_m_c_s_avg"], errors="coerce").values, index=ps["cognitive_id"]).dropna()
    z = (s_avg - s_avg.mean()) / (s_avg.std() + 1e-9)
    plb = 0.007 * (1 + 0.15 * np.tanh(z))
    support = np.array(sorted(plb.index))
    w0 = lift.reindex(support).fillna(0.0).clip(lower=0).to_numpy()
    w0 = w0 / w0.sum()
    return support, plb, w0


def _child_task(args):
    plb, seed = args
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N_CHILD, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [("torque_order", "age"), ("deviation_enabled", True), ("semantic_gravity_enabled", True)]:
        if hasattr(eng.virtual, a): setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = KSYNC_CANON
    eng.pressure_params.pressure_prob = 0.0
    eng.run_injection()
    sigs = []
    for _ in range(STEPS // WIN):
        eng.step_window(steps=WIN); sigs.append(signature(eng))
    return {c: float(np.mean([s[c] for s in sigs])) for c in SIG_COLS}


def eng_seed(base, r, t, j): return base * 10_000_000 + r * 100_000 + t * 1_000 + j


def update_factor(drawn, sal_eff, support_idx, g, permute_rng=None):
    """cid単位平均→round正規化。factor=(cid_sal/round_mean)^g・undrawn=1。permute_rng で drawn cid 間の対応を破壊。"""
    df = pd.DataFrame({"cid": drawn, "sal": sal_eff})
    cid_sal = df.groupby("cid")["sal"].mean()
    distinct = cid_sal.index.to_numpy(); vals = cid_sal.to_numpy().copy()
    if permute_rng is not None:
        vals = vals[permute_rng.permutation(len(vals))]
    round_mean = float(np.mean(cid_sal.to_numpy()))
    factor = np.ones(len(support_idx))
    for c, v in zip(distinct, vals):
        factor[support_idx[c]] = (v / round_mean) ** g
    return factor, len(distinct), round_mean


def run_config(cfg, support, plb, w0, support_idx, pool):
    g, base, R = cfg["g"], cfg["base"], cfg["R"]
    n_sup = len(support)
    # 軌跡: fb / K reps / indep(独立composition) / no_feedback(固定)
    w_fb_tr = np.zeros((R, T, n_sup)); w_shuf_tr = np.zeros((R, K, T, n_sup)); w_indep_tr = np.zeros((R, T, n_sup))
    SAL, COV, CSIG = [], [], []
    for r in range(R):
        w_fb = w0.copy(); w_shuf = [w0.copy() for _ in range(K)]; w_indep = w0.copy()
        for t in range(T):
            # --- composition(fb / no_fb / indep 全 M 子を1バッチで並列) ---
            drawn_fb = np.random.default_rng((base, r, t, 101)).choice(support, size=M, p=w_fb)
            drawn_nof = np.random.default_rng((base, r, t, 202)).choice(support, size=M, p=w0)      # 固定 weight
            drawn_ind = np.random.default_rng((base, r, t, 404)).choice(support, size=M, p=w_indep)
            tasks = ([(float(plb.loc[drawn_fb[j]]), eng_seed(base, r, t, j)) for j in range(M)] +
                     [(float(plb.loc[drawn_nof[j]]), eng_seed(base, r, t, j)) for j in range(M)] +
                     [(float(plb.loc[drawn_ind[j]]), eng_seed(base, r, t, j)) for j in range(M)])
            res = list(pool.map(_child_task, tasks, chunksize=1))
            sig_fb, sig_nof, sig_ind = res[:M], res[M:2 * M], res[2 * M:]
            # --- feedback: 珍しさ→cid単位平均→更新(正しい対応) ---
            lens_fb = [s[LENS] for s in sig_fb]
            sal_raw = rarity(lens_fb); sal_eff = np.maximum(sal_raw, EPS)
            sal_rank = pd.Series(lens_fb).rank(method="average").to_numpy()
            for j in range(M):
                SAL.append(dict(g=g, base=base, r=r, t=t, j=j, drawn_cid=int(drawn_fb[j]), lens=lens_fb[j],
                                salience_raw=float(sal_raw[j]), salience_eff=float(sal_eff[j]), salience_rank=float(sal_rank[j])))
            f_fb, ndist, rmean = update_factor(drawn_fb, sal_eff, support_idx, g)
            w_fb = w_fb * f_fb; w_fb /= w_fb.sum(); w_fb_tr[r, t] = w_fb
            # --- K shuffle レプリカ: 同一世界(sal_eff)に相乗り・別 permutation・各自 weight(子ゼロ追加) ---
            for k in range(K):
                srng = np.random.default_rng((base, r, t, 303, k))
                f_k, _, _ = update_factor(drawn_fb, sal_eff, support_idx, g, permute_rng=srng)
                w_shuf[k] = w_shuf[k] * f_k; w_shuf[k] /= w_shuf[k].sum(); w_shuf_tr[r, k, t] = w_shuf[k]
            # --- 独立 composition shuffle(secondary2・別の問い): 自群 weight で引き・自群子・対応破壊 ---
            lens_ind = [s[LENS] for s in sig_ind]
            sal_ind = np.maximum(rarity(lens_ind), EPS)
            irng = np.random.default_rng((base, r, t, 505))
            f_ind, ndist_ind, _ = update_factor(drawn_ind, sal_ind, support_idx, g, permute_rng=irng)
            w_indep = w_indep * f_ind; w_indep /= w_indep.sum(); w_indep_tr[r, t] = w_indep
            # --- ログ: coverage / 子集団署名(fb/no_fb/indep 世界応答) ---
            COV.append(dict(g=g, base=base, r=r, t=t, group="feedback", drawn_distinct=ndist,
                            undrawn_rate=round((n_sup - ndist) / n_sup, 4), round_mean_salience=round(rmean, 5)))
            COV.append(dict(g=g, base=base, r=r, t=t, group="indep_shuffle", drawn_distinct=int(ndist_ind),
                            undrawn_rate=round((n_sup - ndist_ind) / n_sup, 4), round_mean_salience=None))
            for gg, sgs in [("feedback", sig_fb), ("no_feedback", sig_nof), ("indep_shuffle", sig_ind)]:
                row = dict(g=g, base=base, r=r, t=t, group=gg)
                for c in SIG_COLS: row[c] = float(np.mean([s[c] for s in sgs]))
                CSIG.append(row)
        log(f"  cfg(g={g},base={base}) R series {r} done")
    # --- primary: D_fb, D_null 系列ごと ---
    prim = []
    for r in range(R):
        # mean_round L1 は round 平均
        d_fb = np.mean([np.mean([np.abs(w_fb_tr[r, t] - w_shuf_tr[r, k, t]).sum() for t in range(T)]) for k in range(K)])
        pair = [np.mean([np.abs(w_shuf_tr[r, i, t] - w_shuf_tr[r, j, t]).sum() for t in range(T)])
                for i in range(K) for j in range(i + 1, K)]
        d_null = np.mean(pair)
        # secondary1: entropy 差(最終 round・shuffle平均 − feedback)
        h_shuf = np.mean([entropy(w_shuf_tr[r, k, T - 1]) for k in range(K)])
        ent_diff = h_shuf - entropy(w_fb_tr[r, T - 1])
        prim.append(dict(g=g, base=base, r=r, D_fb=float(d_fb), D_null=float(d_null),
                         primary_diff=float(d_fb - d_null), sec_entropy_diff=float(ent_diff),
                         L1_fb_indep_finalT=float(np.abs(w_fb_tr[r, T - 1] - w_indep_tr[r, T - 1]).sum())))
    return dict(g=g, base=base, R=R), prim, SAL, COV, CSIG, (w_fb_tr, w_shuf_tr, w_indep_tr)


def ttest(x):
    x = np.asarray(x, float)
    if len(x) >= 3 and np.std(x) > 0:
        tstat, p = stats.ttest_1samp(x, 0.0)
        sign = float(np.mean(np.sign(x) == np.sign(np.mean(x))))
        return round(float(tstat), 3), float(p), round(sign, 3)
    return np.nan, np.nan, np.nan


def main():
    t0 = time.time()
    ph_pre = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    support, plb, w0 = load_init()
    support_idx = {c: i for i, c in enumerate(support)}
    round0_log = dict(support_n=len(support), sum_weight=float(w0.sum()), entropy=entropy(w0),
                      cid_hash=hashlib.md5(",".join(map(str, support)).encode()).hexdigest())
    log(f"round0 support: {round0_log} / workers={N_WORKERS}")

    ALL_PRIM, ALL_SAL, ALL_COV, ALL_CSIG = [], [], [], []
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=N_WORKERS, mp_context=ctx) as pool:
        for cfg in CONFIGS:
            meta, prim, sal, cov, csig, _ = run_config(cfg, support, plb, w0, support_idx, pool)
            ALL_PRIM += prim; ALL_SAL += sal; ALL_COV += cov; ALL_CSIG += csig
            log(f"cfg g={cfg['g']} base={cfg['base']} done ({time.time()-t0:.0f}s)")

    prim = pd.DataFrame(ALL_PRIM)
    prim.to_parquet(OUT / "v1304b_full_primary.parquet")
    pd.DataFrame(ALL_SAL).to_parquet(OUT / "v1304b_full_salience.parquet")
    pd.DataFrame(ALL_COV).to_parquet(OUT / "v1304b_full_coverage.parquet")
    pd.DataFrame(ALL_CSIG).to_parquet(OUT / "v1304b_full_childsig.parquet")

    # primary 検定(事前固定): 各(g,base)で paired (D_fb-D_null) を R系列 1標本t
    tests = []
    for (g, base), sub in prim.groupby(["g", "base"]):
        t_p, p_p, sc_p = ttest(sub["primary_diff"].values)
        t_e, p_e, sc_e = ttest(sub["sec_entropy_diff"].values)
        tests.append(dict(g=g, base=base, R=len(sub), role="primary" if g == 1.0 else "g0.5_ref",
                          D_fb_mean=round(float(sub.D_fb.mean()), 5), D_null_mean=round(float(sub.D_null.mean()), 5),
                          primary_diff_mean=round(float(sub.primary_diff.mean()), 5), t=t_p, p_raw=round(p_p, 5) if not np.isnan(p_p) else None,
                          sign_consistency=sc_p, sec_entropy_diff_mean=round(float(sub.sec_entropy_diff.mean()), 5),
                          entropy_t=t_e, entropy_p=round(p_e, 5) if not np.isnan(p_e) else None,
                          L1_fb_indep_finalT_mean=round(float(sub.L1_fb_indep_finalT.mean()), 5)))
    tests = pd.DataFrame(tests); tests.to_parquet(OUT / "v1304b_full_tests.parquet")

    ph_post = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    summary = dict(design="v1304b_full_replica_null", T=T, M=M, K=K, configs=CONFIGS,
                   round0_support=round0_log, parent_physics_hash=ph_pre,
                   parent_hash_unchanged=bool(ph_pre == ph_post),
                   n_child=int(sum(3 * M * T * c["R"] for c in CONFIGS)),
                   primary_note="feedback が立つ = (D_fb - D_null) > 0 が R系列で有意・base0/1 再現・符号一貫",
                   tests=tests.to_dict("records"), total_s=round(time.time() - t0, 1))
    (OUT / "v1304b_full_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    log(f"DONE {summary['n_child']} children {round(time.time()-t0,1)}s / parent_hash_unchanged={summary['parent_hash_unchanged']}")
    print("\n=== primary: (D_fb - D_null) を R系列 1標本t(事前固定・g=1 が primary / g=0.5 は参考) ===")
    print(tests.to_string(index=False))
    return summary


if __name__ == "__main__":
    main()
