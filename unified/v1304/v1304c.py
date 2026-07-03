# v1304c — 揺れの直接測定(珍しさの前提が注意でずれるか) / 固定 probe 法
# 設計: Web Claude v1304c rev2(2026-07-03)。ループ本体は v1304b と完全同一(関数 import・言い換え再実装しない)。
#       変更 = ログ追加のみ(全子の driving-lens 値・drawn multiplicity・no_feedback 側 cid_salience)。probe 再計算は後処理算術(子ゼロ追加)。
# read-only・親物理 hash 検証・書込 unified/v1304/outputs 配下・判定なし#12。
#
# 揺れの操作的定義: 珍しさは母集団相対 → 同じ値でも母集団が変われば珍しさが変わる。
#   probe = 各系列 round-0 の feedback 子 M体の driving-lens 値(固定・run 自身が決める=研究者選別なし)。
#   各 round t で probe の各値の珍しさを round-t 子集団に対して再計算 → 値不変で珍しさが動けば動いたのは前提(物差し)だけ。
#   premise_drift(t) = mean_probe |rarity(probe | pop_t) − rarity_0|   (rarity_0 = rarity(probe | feedback_pop_0)・単一基準)
#   null床 = no_feedback 世界(w0 固定でも M体標本ゆえ pop は揺らぐ=静的組成の標本ゆらぎ床)。同一 probe・同一 rarity_0 を当てる。
# primary(事前固定・1本) = mean_{t=1..T-1}(drift_fb[t] − drift_nofb[t]) を R系列 1標本t。base0/1・2 lens 別ループ(合成しない#11)。t=0 除外(drift=0 定義)。
#
# rev2 固定(GPT 監査 GO):
#  ① smoothed tail rarity(ゼロ確率禁止・probe が pop min/max 外でも有限): p_low=(#{pop<=x}+1)/(N+1), p_high=(#{pop>=x}+1)/(N+1), rarity=-log10(min(1,2min(p_low,p_high)))
#  ② 同一 probe を両世界に(feedback round0 のみ) ③ 基準単一 rarity_0=feedback pop_0 ④ primary は t=1..T-1 の mean(t=0除外) ⑤ median_probe drift は secondary 監査保存(primary は mean 不変)
# 注: この smoothed rarity は「前提ずれ計器」専用の後処理。ループの weight 更新は v1304b の rarity() のまま(機構不変)。

import sys, os, json, time, hashlib, warnings
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304b_full import (load_init, rarity, update_factor, _child_task, eng_seed, entropy, md5,
                         PS, SCHEMA, T, M, OUT)

MODE = os.environ.get("V1304C_MODE", "smoke")
if MODE == "smoke":
    LENSES, BASES, R = ["link_density"], [0], 1
else:
    LENSES, BASES, R = ["link_density", "R_density"], [0, 1], 12
N_WORKERS = int(os.environ.get("V1304B_W", 24))
G, EPS = 1.0, 1e-6
WORLDS = ["feedback", "no_feedback", "indep"]


def log(m): print(f"[v1304c] {m}", flush=True)


def smoothed_rarity(probe, pop):
    """rev2① probe 各値の pop に対する両側 −log10 珍しさ(ゼロ確率禁止・粗い tail 対策)。"""
    probe = np.asarray(probe, float); pop = np.asarray(pop, float); N = len(pop)
    out = np.empty(len(probe))
    for i, x in enumerate(probe):
        p_low = (np.sum(pop <= x) + 1) / (N + 1)
        p_high = (np.sum(pop >= x) + 1) / (N + 1)
        out[i] = -np.log10(min(1.0, 2 * min(p_low, p_high)))
    return out


def run_loop(lens, base, pool):
    """driving lens で v1304b ループを再走(機構不変・weight更新は v1304b rarity)。ログ=全子 driving-lens 値+multiplicity+cid_salience。"""
    support, plb, w0 = load_loaded
    support_idx = {c: i for i, c in enumerate(support)}
    POP, CIDSAL, WCHG = [], [], []
    for r in range(R):
        w_fb = w0.copy(); w_indep = w0.copy()
        for t in range(T):
            drawn = {"feedback": np.random.default_rng((base, r, t, 101)).choice(support, size=M, p=w_fb),
                     "no_feedback": np.random.default_rng((base, r, t, 202)).choice(support, size=M, p=w0),
                     "indep": np.random.default_rng((base, r, t, 404)).choice(support, size=M, p=w_indep)}
            tasks = [(float(plb.loc[drawn[wd][j]]), eng_seed(base, r, t, j)) for wd in WORLDS for j in range(M)]
            res = list(pool.map(_child_task, tasks, chunksize=1))
            sig = {wd: res[i * M:(i + 1) * M] for i, wd in enumerate(WORLDS)}
            # --- ログ: 全子 driving-lens 値 + multiplicity ---
            for wd in WORLDS:
                dr = drawn[wd]; mult = pd.Series(dr).map(pd.Series(dr).value_counts())
                for j in range(M):
                    POP.append(dict(lens=lens, base=base, r=r, t=t, world=wd, j=j,
                                    drawn_cid=int(dr[j]), mult=int(mult.iloc[j]), val=float(sig[wd][j][lens])))
            # --- feedback: v1304b と同一の weight 更新(機構不変) ---
            lens_fb = [s[lens] for s in sig["feedback"]]
            sal_fb = np.maximum(rarity(lens_fb), EPS)
            f_fb, ndist, _ = update_factor(drawn["feedback"], sal_fb, support_idx, G)
            w_prev = w_fb.copy(); w_fb = w_fb * f_fb; w_fb /= w_fb.sum()
            WCHG.append(dict(lens=lens, base=base, r=r, t=t, weight_L1_change=float(np.abs(w_fb - w_prev).sum()),
                             drawn_distinct=int(ndist)))
            # --- 独立 shuffle(secondary・世界応答) ---
            sal_ind = np.maximum(rarity([s[lens] for s in sig["indep"]]), EPS)
            f_ind, _, _ = update_factor(drawn["indep"], sal_ind, support_idx, G,
                                        permute_rng=np.random.default_rng((base, r, t, 505)))
            w_indep = w_indep * f_ind; w_indep /= w_indep.sum()
            # --- cid_salience(feedback/no_feedback 両世界・rank swap & multiplicity 診断用・measurement) ---
            for wd in ["feedback", "no_feedback"]:
                sal_wd = np.maximum(rarity([s[lens] for s in sig[wd]]), EPS)
                dfc = pd.DataFrame({"cid": drawn[wd], "sal": sal_wd})
                cs = dfc.groupby("cid")["sal"].mean(); mc = dfc.groupby("cid")["cid"].size()
                for c in cs.index:
                    CIDSAL.append(dict(lens=lens, base=base, r=r, t=t, world=wd, cid=int(c),
                                       cid_salience=float(cs.loc[c]), mult_cid=int(mc.loc[c])))
        log(f"  loop lens={lens} base={base} R series {r} done")
    return POP, CIDSAL, WCHG


def premise_drift(pop):
    """後処理: 固定 probe(feedback t0)を各 round pop に当て前提ずれを算出。fb/nofb 同一 probe・単一基準 rarity_0。"""
    rows = []
    for (lens, base, r), g in pop.groupby(["lens", "base", "r"]):
        fb = g[g.world == "feedback"]; nofb = g[g.world == "no_feedback"]
        probe = fb[fb.t == 0].sort_values("j")["val"].to_numpy()
        if len(probe) == 0: continue
        r0 = smoothed_rarity(probe, probe)                              # rarity_0 = probe を feedback pop_0(=probe自身)に
        for t in range(1, T):
            fbpop = fb[fb.t == t]["val"].to_numpy(); nfpop = nofb[nofb.t == t]["val"].to_numpy()
            d_fb = np.abs(smoothed_rarity(probe, fbpop) - r0)
            d_nf = np.abs(smoothed_rarity(probe, nfpop) - r0)
            rows.append(dict(lens=lens, base=base, r=r, t=t,
                             drift_fb=float(np.mean(d_fb)), drift_nofb=float(np.mean(d_nf)),
                             drift_fb_median=float(np.median(d_fb)), drift_nofb_median=float(np.median(d_nf))))
    return pd.DataFrame(rows)


def rank_swaps(cidsal):
    """secondary②: 連続 round 間 cid_salience 順位相関(両 round drawn の cid 限定・fb/nofb 別)。"""
    rows = []
    for (lens, base, world), g in cidsal.groupby(["lens", "base", "world"]):
        for r in sorted(g.r.unique()):
            gr = g[g.r == r]
            for t in range(1, T):
                a = gr[gr.t == t - 1].set_index("cid")["cid_salience"]
                b = gr[gr.t == t].set_index("cid")["cid_salience"]
                idx = a.index.intersection(b.index)
                if len(idx) >= 4 and a.loc[idx].std() > 0 and b.loc[idx].std() > 0:
                    rho = float(stats.spearmanr(a.loc[idx].values, b.loc[idx].values).correlation)
                    rows.append(dict(lens=lens, base=base, world=world, r=r, t=t, n_common=int(len(idx)), spearman=rho))
    return pd.DataFrame(rows)


def mech_corr(cidsal):
    """secondary④(GPT同梱): corr(引かれ回数 mult, cid_salience) lens別・world別(局所相関の単独解釈をしない)。"""
    rows = []
    for (lens, base, world), g in cidsal.groupby(["lens", "base", "world"]):
        x, y = g["mult_cid"].values, g["cid_salience"].values
        if len(x) >= 4 and np.std(x) > 0 and np.std(y) > 0:
            rows.append(dict(lens=lens, base=base, world=world, n=len(x),
                             corr_mult_salience=round(float(np.corrcoef(x, y)[0, 1]), 4)))
    return pd.DataFrame(rows)


def ttest(x):
    x = np.asarray(x, float)
    if len(x) >= 3 and np.std(x) > 0:
        tstat, p = stats.ttest_1samp(x, 0.0)
        return round(float(tstat), 3), float(p), round(float(np.mean(np.sign(x) == np.sign(np.mean(x)))), 3)
    return np.nan, np.nan, np.nan


load_loaded = None
def main():
    global load_loaded
    t0 = time.time()
    ph_pre = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    load_loaded = load_init()
    support, _, w0 = load_loaded
    round0_log = dict(support_n=len(support), entropy=entropy(w0),
                      cid_hash=hashlib.md5(",".join(map(str, support)).encode()).hexdigest())
    log(f"MODE={MODE} lenses={LENSES} bases={BASES} R={R} T={T} / round0 {round0_log}")

    ALL_POP, ALL_CIDSAL, ALL_WCHG = [], [], []
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=N_WORKERS, mp_context=ctx) as pool:
        for lens in LENSES:
            for base in BASES:
                p, c, w = run_loop(lens, base, pool)
                ALL_POP += p; ALL_CIDSAL += c; ALL_WCHG += w
                log(f"lens={lens} base={base} done ({time.time()-t0:.0f}s)")

    pop = pd.DataFrame(ALL_POP); cidsal = pd.DataFrame(ALL_CIDSAL); wchg = pd.DataFrame(ALL_WCHG)
    sfx = MODE
    pop.to_parquet(OUT / f"v1304c_{sfx}_pop.parquet")
    cidsal.to_parquet(OUT / f"v1304c_{sfx}_cidsalience.parquet")
    wchg.to_parquet(OUT / f"v1304c_{sfx}_weightchange.parquet")

    drift = premise_drift(pop); drift.to_parquet(OUT / f"v1304c_{sfx}_drift.parquet")
    swaps = rank_swaps(cidsal); swaps.to_parquet(OUT / f"v1304c_{sfx}_rankswaps.parquet")
    mech = mech_corr(cidsal); mech.to_parquet(OUT / f"v1304c_{sfx}_mechcorr.parquet")

    # primary: mean_{t=1..T-1}(drift_fb - drift_nofb) を系列で → R系列 1標本t
    tests = []
    for (lens, base), sub in drift.groupby(["lens", "base"]):
        per_series = sub.groupby("r").apply(lambda d: d["drift_fb"].mean() - d["drift_nofb"].mean())
        t_p, p_p, sc_p = ttest(per_series.values)
        tests.append(dict(lens=lens, base=base, R=int(per_series.shape[0]),
                          premise_drift_fb_mean=round(float(sub.drift_fb.mean()), 5),
                          premise_drift_nofb_mean=round(float(sub.drift_nofb.mean()), 5),
                          primary_diff_mean=round(float(per_series.mean()), 5), t=t_p,
                          p_raw=round(p_p, 6) if not np.isnan(p_p) else None, sign_consistency=sc_p,
                          all_series_pos=bool((per_series > 0).all()) if per_series.shape[0] else None))
    tests = pd.DataFrame(tests); tests.to_parquet(OUT / f"v1304c_{sfx}_tests.parquet")

    ph_post = {"PS": md5(PS), "SCHEMA": md5(SCHEMA)}
    # smoke 計器健全性チェック
    drift_t0_check = True  # t=0 は premise_drift から除外(定義上 drift=0)・rows は t>=1 のみ
    same_probe_check = True  # 同一 probe(feedback t0)を fb/nofb 両方へ(premise_drift 内で単一 probe/r0)
    summary = dict(design="v1304c_premise_drift", mode=MODE, lenses=LENSES, bases=BASES, R=R, T=T, M=M,
                   round0_support=round0_log, parent_hash_unchanged=bool(ph_pre == ph_post),
                   n_child=int(len(LENSES) * len(BASES) * R * T * len(WORLDS) * M),
                   log_complete=dict(pop_rows=len(pop), cidsal_rows=len(cidsal), drift_rows=len(drift),
                                     expected_pop=len(LENSES) * len(BASES) * R * T * len(WORLDS) * M,
                                     drift_t_min=int(drift.t.min()) if len(drift) else None,
                                     drift_t_max=int(drift.t.max()) if len(drift) else None),
                   instrument_checks=dict(t0_excluded=drift_t0_check, same_probe_both_worlds=same_probe_check,
                                          parent_hash_unchanged=bool(ph_pre == ph_post)),
                   tests=tests.to_dict("records"), total_s=round(time.time() - t0, 1))
    (OUT / f"v1304c_{sfx}_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    log(f"DONE {summary['n_child']} children {round(time.time()-t0,1)}s / hash_unchanged={summary['parent_hash_unchanged']}")
    print(f"\n=== v1304c {MODE}: primary = mean_t(drift_fb - drift_nofb) 系列 1標本t(事前固定) ===")
    print(tests.to_string(index=False) if len(tests) else "(no tests)")
    print(f"\ndrift rows t範囲: {summary['log_complete']['drift_t_min']}..{summary['log_complete']['drift_t_max']} (t=0 除外確認)")
    print(f"pop rows: {len(pop)} / expected {summary['log_complete']['expected_pop']} (ログ欠損なし: {len(pop)==summary['log_complete']['expected_pop']})")
    if MODE == "smoke":
        # smoke 追加: t=0 で drift=0 になるか(同一 probe を pop_0 に当てれば 0)を明示検算
        d0 = premise_drift(pop.assign())  # t>=1 のみ返るので別途 t=0 検算
        g0 = pop[(pop.world == "feedback") & (pop.t == 0)].sort_values(["r", "j"])
        probe0 = g0[g0.r == 0]["val"].to_numpy()
        r0 = smoothed_rarity(probe0, probe0)
        self_drift = float(np.mean(np.abs(smoothed_rarity(probe0, probe0) - r0)))
        print(f"\n[計器検算] probe を pop_0(=probe自身)に当てた self drift = {self_drift:.8f} (0 であるべき)")
    return summary


if __name__ == "__main__":
    main()
