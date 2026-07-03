# v1304b 別 lens 再現 — 自己確認外し(lens=R_density で primary 再現)
# 指示: Web Claude 2026-07-03。機構・統計・規模は full と完全同一・lens だけ差し替え(#5 新観察軸を足さない)。
# read-only・親物理 hash 検証・書込 unified/v1304/outputs 配下・判定なし#12。
#
# 変える = primary lens のみ: link_density → R_density(率・link数で正規化済・plb の機械的濃淡から一段遠い)。
# 変えない = ループ機構(composition/両側-log10/cid単位平均/round正規化/α/eps floor)・K=10 レプリカnull・
#            primary(D_fb-D_null 系列paired 1標本t・事前固定)・R12・T8・M20・base0/1・g1・初期weight(now_theta lift)・停止条件・親hash。
# §3 診断(必須付帯・新観察軸でない): 同一 feedback draws 上で両 lens(link_density/R_density)の per-cid salience 持続性
#   (前半round vs 後半round の split 相関)を primary と並べて報告。判定は Taka。
# 解釈は事前固定(§2): (a)立つ→対応の効きは lens 非依存=ループの機構的性質 / (b)立たない→per-cid持続的個体差のある観察量に限る(=条件の特定・発見)。

import sys, os, json, time, hashlib, warnings
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# full の実装をそのまま流用(機構同一を保証・言い換え再実装しない)
from v1304b_full import (load_init, rarity, update_factor, _child_task, eng_seed, entropy, md5,
                         PS, SCHEMA, T, M, K, SIG_COLS, OUT)

LENS = os.environ.get("V1304B_LENS", "R_density")      # 差し替える primary lens
DIAG_LENSES = ["link_density", "R_density"]            # 持続性を並べる2 lens(同一 draws 上)
N_WORKERS = int(os.environ.get("V1304B_W", 24))
EPS = 1e-6
CONFIGS = [dict(g=1.0, base=0, R=12), dict(g=1.0, base=1, R=12)]  # g0.5 は full で参考済(再実施不要)


def log(m): print(f"[v1304b-lens] {m}", flush=True)


def run_config(cfg, support, plb, w0, support_idx, pool, spread_state):
    g, base, R = cfg["g"], cfg["base"], cfg["R"]
    n_sup = len(support)
    w_fb_tr = np.zeros((R, T, n_sup)); w_shuf_tr = np.zeros((R, K, T, n_sup)); w_indep_tr = np.zeros((R, T, n_sup))
    PRIM, COV, CIDSAL = [], [], []   # CIDSAL: 診断用 per-(r,t,cid,lens) cid_salience
    for r in range(R):
        w_fb = w0.copy(); w_shuf = [w0.copy() for _ in range(K)]; w_indep = w0.copy()
        for t in range(T):
            drawn_fb = np.random.default_rng((base, r, t, 101)).choice(support, size=M, p=w_fb)
            drawn_nof = np.random.default_rng((base, r, t, 202)).choice(support, size=M, p=w0)
            drawn_ind = np.random.default_rng((base, r, t, 404)).choice(support, size=M, p=w_indep)
            tasks = ([(float(plb.loc[drawn_fb[j]]), eng_seed(base, r, t, j)) for j in range(M)] +
                     [(float(plb.loc[drawn_nof[j]]), eng_seed(base, r, t, j)) for j in range(M)] +
                     [(float(plb.loc[drawn_ind[j]]), eng_seed(base, r, t, j)) for j in range(M)])
            res = list(pool.map(_child_task, tasks, chunksize=1))
            sig_fb, sig_ind = res[:M], res[2 * M:]
            # --- primary lens(=R_density)で feedback 更新 ---
            lens_fb = [s[LENS] for s in sig_fb]
            # spread ガード(最初の系列・最初の round): 子間 spread が潰れて珍しさ未定義でないか
            if spread_state["checked"] is False:
                sp = float(np.std(lens_fb))
                spread_state.update(checked=True, first_std=sp, first_vals_n_unique=int(len(set(np.round(lens_fb, 6)))))
                log(f"spread check lens={LENS}: std={sp:.5f} n_unique={spread_state['first_vals_n_unique']}/{M}")
                if sp < 1e-6:
                    raise RuntimeError(f"{LENS} child spread collapsed (std={sp}) — 珍しさ未定義。停止。")
            sal_eff = np.maximum(rarity(lens_fb), EPS)
            f_fb, ndist, rmean = update_factor(drawn_fb, sal_eff, support_idx, g)
            w_fb = w_fb * f_fb; w_fb /= w_fb.sum(); w_fb_tr[r, t] = w_fb
            # --- K レプリカ(同一世界に相乗り・別permutation・子ゼロ追加) ---
            for k in range(K):
                srng = np.random.default_rng((base, r, t, 303, k))
                f_k, _, _ = update_factor(drawn_fb, sal_eff, support_idx, g, permute_rng=srng)
                w_shuf[k] = w_shuf[k] * f_k; w_shuf[k] /= w_shuf[k].sum(); w_shuf_tr[r, k, t] = w_shuf[k]
            # --- 独立 composition shuffle(secondary・別の問い) ---
            sal_ind = np.maximum(rarity([s[LENS] for s in sig_ind]), EPS)
            irng = np.random.default_rng((base, r, t, 505))
            f_ind, _, _ = update_factor(drawn_ind, sal_ind, support_idx, g, permute_rng=irng)
            w_indep = w_indep * f_ind; w_indep /= w_indep.sum(); w_indep_tr[r, t] = w_indep
            # --- 診断: 同一 feedback draws 上で両 lens の per-cid salience(公平比較) ---
            for dl in DIAG_LENSES:
                dvals = [s[dl] for s in sig_fb]
                dsal = np.maximum(rarity(dvals), EPS)
                cs = pd.DataFrame({"cid": drawn_fb, "sal": dsal}).groupby("cid")["sal"].mean()
                for c, v in cs.items():
                    CIDSAL.append(dict(g=g, base=base, r=r, t=t, lens=dl, cid=int(c), cid_salience=float(v)))
            COV.append(dict(g=g, base=base, r=r, t=t, group="feedback", lens=LENS,
                            drawn_distinct=int(ndist), undrawn_rate=round((n_sup - ndist) / n_sup, 4)))
        log(f"  cfg(g={g},base={base}) R series {r} done")
    for r in range(R):
        d_fb = np.mean([np.mean([np.abs(w_fb_tr[r, t] - w_shuf_tr[r, k, t]).sum() for t in range(T)]) for k in range(K)])
        pair = [np.mean([np.abs(w_shuf_tr[r, i, t] - w_shuf_tr[r, j, t]).sum() for t in range(T)])
                for i in range(K) for j in range(i + 1, K)]
        d_null = np.mean(pair)
        h_shuf = np.mean([entropy(w_shuf_tr[r, k, T - 1]) for k in range(K)])
        PRIM.append(dict(g=g, base=base, r=r, lens=LENS, D_fb=float(d_fb), D_null=float(d_null),
                         primary_diff=float(d_fb - d_null), sec_entropy_diff=float(h_shuf - entropy(w_fb_tr[r, T - 1])),
                         L1_fb_indep_finalT=float(np.abs(w_fb_tr[r, T - 1] - w_indep_tr[r, T - 1]).sum())))
    return PRIM, COV, CIDSAL


def ttest(x):
    x = np.asarray(x, float)
    if len(x) >= 3 and np.std(x) > 0:
        tstat, p = stats.ttest_1samp(x, 0.0)
        return round(float(tstat), 3), float(p), round(float(np.mean(np.sign(x) == np.sign(np.mean(x)))), 3)
    return np.nan, np.nan, np.nan


def persistence(cidsal):
    """§3: per-cid salience の前半round vs 後半round split 相関(lens×base ごと・cid 跨ぎ Pearson)。高い=持続的個体差。"""
    rows = []
    half = T // 2
    for (g, base, lens), sub in cidsal.groupby(["g", "base", "lens"]):
        early = sub[sub.t < half].groupby("cid")["cid_salience"].mean()
        late = sub[sub.t >= half].groupby("cid")["cid_salience"].mean()
        idx = early.index.intersection(late.index)
        if len(idx) >= 4 and early.loc[idx].std() > 0 and late.loc[idx].std() > 0:
            rr = float(np.corrcoef(early.loc[idx].values, late.loc[idx].values)[0, 1])
        else:
            rr = np.nan
        rows.append(dict(g=g, base=base, lens=lens, n_cid=int(len(idx)),
                         split_half_corr=round(rr, 4) if not np.isnan(rr) else None))
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    ph_pre = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    support, plb, w0 = load_init()
    support_idx = {c: i for i, c in enumerate(support)}
    round0_log = dict(support_n=len(support), sum_weight=float(w0.sum()), entropy=entropy(w0),
                      cid_hash=hashlib.md5(",".join(map(str, support)).encode()).hexdigest())
    log(f"round0 support: {round0_log} / lens={LENS} / workers={N_WORKERS}")

    ALL_PRIM, ALL_COV, ALL_CIDSAL = [], [], []
    spread_state = dict(checked=False)
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=N_WORKERS, mp_context=ctx) as pool:
        for cfg in CONFIGS:
            prim, cov, cidsal = run_config(cfg, support, plb, w0, support_idx, pool, spread_state)
            ALL_PRIM += prim; ALL_COV += cov; ALL_CIDSAL += cidsal
            log(f"cfg g={cfg['g']} base={cfg['base']} done ({time.time()-t0:.0f}s)")

    prim = pd.DataFrame(ALL_PRIM); prim.to_parquet(OUT / f"v1304b_lens_{LENS}_primary.parquet")
    cidsal = pd.DataFrame(ALL_CIDSAL); cidsal.to_parquet(OUT / f"v1304b_lens_{LENS}_cidsalience.parquet")
    pd.DataFrame(ALL_COV).to_parquet(OUT / f"v1304b_lens_{LENS}_coverage.parquet")

    tests = []
    for (g, base), sub in prim.groupby(["g", "base"]):
        t_p, p_p, sc_p = ttest(sub["primary_diff"].values)
        t_e, p_e, sc_e = ttest(sub["sec_entropy_diff"].values)
        tests.append(dict(g=g, base=base, lens=LENS, R=len(sub),
                          D_fb_mean=round(float(sub.D_fb.mean()), 5), D_null_mean=round(float(sub.D_null.mean()), 5),
                          primary_diff_mean=round(float(sub.primary_diff.mean()), 5), t=t_p,
                          p_raw=round(p_p, 6) if not np.isnan(p_p) else None, sign_consistency=sc_p,
                          all_series_pos=bool((sub.primary_diff > 0).all()),
                          sec_entropy_diff_mean=round(float(sub.sec_entropy_diff.mean()), 5), entropy_t=t_e,
                          L1_fb_indep_finalT_mean=round(float(sub.L1_fb_indep_finalT.mean()), 5)))
    tests = pd.DataFrame(tests); tests.to_parquet(OUT / f"v1304b_lens_{LENS}_tests.parquet")
    pers = persistence(cidsal); pers.to_parquet(OUT / f"v1304b_lens_{LENS}_persistence.parquet")

    ph_post = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    summary = dict(design="v1304b_lens_reproduction", primary_lens=LENS, diag_lenses=DIAG_LENSES,
                   T=T, M=M, K=K, configs=CONFIGS, round0_support=round0_log,
                   parent_hash_unchanged=bool(ph_pre == ph_post), spread_check=spread_state,
                   n_child=int(sum(3 * M * T * c["R"] for c in CONFIGS)),
                   tests=tests.to_dict("records"), persistence=pers.to_dict("records"),
                   total_s=round(time.time() - t0, 1))
    (OUT / f"v1304b_lens_{LENS}_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    log(f"DONE {summary['n_child']} children {round(time.time()-t0,1)}s / parent_hash_unchanged={summary['parent_hash_unchanged']}")
    print(f"\n=== primary(lens={LENS}・D_fb-D_null 系列paired 1標本t・事前固定・g=1) ===")
    print(tests.to_string(index=False))
    print("\n=== §3 診断: per-cid salience 持続性(前半vs後半 split 相関・同一feedback draws上・両lens) ===")
    print(pers.to_string(index=False))
    return summary


if __name__ == "__main__":
    main()
