# v1304c 測定方法の自己監査(Taka 指示: 計器そのものを疑う) — 既存全子ログの再解析・子ゼロ追加・新run なし
# 3つの疑い:
#  ① 構造(ICC): lens 値は「どの cid か」でどれだけ決まるか。決めない=組成変化で母集団は動かず前提ずれは構造的にゼロ(計器の失敗でない)。
#  ② 検出力(Wasserstein): M=20 tail は極ノイジー。系列 pool(240標本)の分布距離で fb が nofb より動くか(probe 法が見落とした本物のずれの有無)。
#  ③ pooled 参照 premise drift: 参照母集団を leave-one-series-out の 220 標本に広げ paired 検定を再実行(検出力を上げても結論が変わるか)。
# read-only・親物理非書込・書込 unified/v1304/outputs 配下・判定なし#12。

import sys, os, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1304b_full import OUT, T

pop = pd.read_parquet(OUT / "v1304c_full_pop.parquet")
LENSES = ["link_density", "R_density"]; BASES = [0, 1]


def smoothed_rarity(probe, popv):
    probe = np.asarray(probe, float); popv = np.asarray(popv, float); N = len(popv)
    out = np.empty(len(probe))
    for i, x in enumerate(probe):
        pl = (np.sum(popv <= x) + 1) / (N + 1); ph = (np.sum(popv >= x) + 1) / (N + 1)
        out[i] = -np.log10(min(1.0, 2 * min(pl, ph)))
    return out


# ---- ① 構造 ICC: lens 値の分散のうち cid 間が占める割合 ----
print("=== ① 構造(ICC): between-cid var / total var (drawn_cid で層化・feedback世界・全round pool) ===")
icc_rows = []
for lens in LENSES:
    for base in BASES:
        d = pop[(pop.lens == lens) & (pop.base == base) & (pop.world == "feedback")]
        grand = d.val.var()
        cid_means = d.groupby("drawn_cid")["val"].mean()
        cid_n = d.groupby("drawn_cid")["val"].size()
        between = np.average((cid_means - d.val.mean())**2, weights=cid_n)
        within = d.groupby("drawn_cid")["val"].var().mean()
        icc = between / (between + within) if (between + within) > 0 else np.nan
        icc_rows.append(dict(lens=lens, base=base, icc=round(icc, 4), between=round(between, 6),
                             within=round(within, 6), n_cid=int(d.drawn_cid.nunique())))
        print(f"  {lens:13s} base{base}: ICC={icc:.4f}  (between={between:.5f} within={within:.5f})")
icc_df = pd.DataFrame(icc_rows)

# ---- ② Wasserstein: pop_t vs pop_0 を系列 pool(240標本)で・fb vs nofb ----
print("\n=== ② 検出力(Wasserstein-1・系列pool ~240標本): dist(pop_t, pop_0) の round推移 fb vs nofb ===")
wass_rows = []
for lens in LENSES:
    for base in BASES:
        for wd in ["feedback", "no_feedback"]:
            sub = pop[(pop.lens == lens) & (pop.base == base) & (pop.world == wd)]
            pop0 = sub[sub.t == 0]["val"].values
            for t in range(1, T):
                popt = sub[sub.t == t]["val"].values
                w = stats.wasserstein_distance(popt, pop0)
                wass_rows.append(dict(lens=lens, base=base, world=wd, t=t, wass=w, n0=len(pop0), nt=len(popt)))
wass = pd.DataFrame(wass_rows)
for lens in LENSES:
    for base in BASES:
        fb = wass[(wass.lens == lens) & (wass.base == base) & (wass.world == "feedback")].set_index("t")["wass"]
        nf = wass[(wass.lens == lens) & (wass.base == base) & (wass.world == "no_feedback")].set_index("t")["wass"]
        print(f"  {lens:13s} base{base}: fb   t1..7 = {' '.join(f'{v:.4f}' for v in fb.values)}")
        print(f"  {' ':13s}      : nofb t1..7 = {' '.join(f'{v:.4f}' for v in nf.values)}   | fb-nofb末round={fb.iloc[-1]-nf.iloc[-1]:+.4f}")

# ---- ③ pooled-reference premise drift: 参照を leave-one-series-out の他11系列 pool(~220標本)に ----
print("\n=== ③ pooled参照 premise drift: 参照=他系列pool(~220)・probe=自系列t0(20)・paired t 再検定 ===")
pooled_rows = []
for lens in LENSES:
    for base in BASES:
        fb = pop[(pop.lens == lens) & (pop.base == base) & (pop.world == "feedback")]
        nf = pop[(pop.lens == lens) & (pop.base == base) & (pop.world == "no_feedback")]
        R = sorted(fb.r.unique())
        per_series = []
        for r in R:
            probe = fb[(fb.r == r) & (fb.t == 0)].sort_values("j")["val"].values
            # 参照(round0): 他系列 fb の t0 を pool
            ref0_fb = fb[(fb.r != r) & (fb.t == 0)]["val"].values
            r0 = smoothed_rarity(probe, ref0_fb)
            dfb, dnf = [], []
            for t in range(1, T):
                ref_fb = fb[(fb.r != r) & (fb.t == t)]["val"].values
                ref_nf = nf[(nf.r != r) & (nf.t == t)]["val"].values
                dfb.append(np.mean(np.abs(smoothed_rarity(probe, ref_fb) - r0)))
                dnf.append(np.mean(np.abs(smoothed_rarity(probe, ref_nf) - r0)))
            per_series.append(np.mean(dfb) - np.mean(dnf))
        per_series = np.array(per_series)
        tstat, p = stats.ttest_1samp(per_series, 0.0)
        sign = np.mean(np.sign(per_series) == np.sign(per_series.mean()))
        pooled_rows.append(dict(lens=lens, base=base, R=len(R), diff_mean=round(float(per_series.mean()), 5),
                                t=round(float(tstat), 3), p_raw=round(float(p), 5),
                                sign_consistency=round(float(sign), 3), all_pos=bool((per_series > 0).all())))
        print(f"  {lens:13s} base{base}: diff={per_series.mean():+.5f} t={tstat:.3f} p={p:.4f} 符号一貫={sign:.2f} 全系列正={bool((per_series>0).all())}")
pooled = pd.DataFrame(pooled_rows)

# ---- ③b 進行性の直接確認: fb/nofb pooled母集団 mean の per-round 軌跡 + drift[t] の t依存 ----
# (前提が「時間で進行的にずれる」か。round-shuffle は primary=mean_t のため no-op でありニセ null=不使用。母集団の実移動を直接見る)
print("\n=== ③b 進行性: pooled母集団 mean の per-round 軌跡(fb 上昇/nofb 平坦か) + drift[t] の t依存 ===")
prog_rows = []
for lens in LENSES:
    for base in BASES:
        fb = pop[(pop.lens == lens) & (pop.base == base) & (pop.world == "feedback")]
        nf = pop[(pop.lens == lens) & (pop.base == base) & (pop.world == "no_feedback")]
        fbm = [float(fb[fb.t == t].val.mean()) for t in range(T)]
        nfm = [float(nf[nf.t == t].val.mean()) for t in range(T)]
        R = sorted(fb.r.unique()); dt = []
        for t in range(1, T):
            per = []
            for r in R:
                probe = fb[(fb.r == r) & (fb.t == 0)].sort_values("j")["val"].values
                r0 = smoothed_rarity(probe, fb[(fb.r != r) & (fb.t == 0)]["val"].values)
                per.append(np.mean(np.abs(smoothed_rarity(probe, fb[(fb.r != r) & (fb.t == t)]["val"].values) - r0)) -
                           np.mean(np.abs(smoothed_rarity(probe, nf[(nf.r != r) & (nf.t == t)]["val"].values) - r0)))
            dt.append(float(np.mean(per)))
        prog_rows.append(dict(lens=lens, base=base, fb_mean_shift=round(fbm[-1] - fbm[0], 4),
                              nofb_mean_shift=round(nfm[-1] - nfm[0], 4), fb_mean_max_shift=round(max(fbm) - fbm[0], 4),
                              driftT_early=round(float(np.mean(dt[:3])), 4), driftT_late=round(float(np.mean(dt[3:])), 4)))
        print(f"  {lens:13s} base{base}: fb mean shift(末-初)={fbm[-1]-fbm[0]:+.4f}(max {max(fbm)-fbm[0]:+.4f}) nofb={nfm[-1]-nfm[0]:+.4f} "
              f"| diff[t] early(t1-3)={np.mean(dt[:3]):+.4f} late(t4-7)={np.mean(dt[3:]):+.4f}")
prog = pd.DataFrame(prog_rows); prog.to_parquet(OUT / "v1304c_audit_progression.parquet")

# 保存
icc_df.to_parquet(OUT / "v1304c_audit_icc.parquet")
wass.to_parquet(OUT / "v1304c_audit_wasserstein.parquet")
pooled.to_parquet(OUT / "v1304c_audit_pooled_drift.parquet")
summary = dict(icc=icc_df.to_dict("records"), pooled_drift=pooled.to_dict("records"),
               wass_final_fb_minus_nofb={f"{l}_base{b}": round(float(
                   wass[(wass.lens==l)&(wass.base==b)&(wass.world=="feedback")&(wass.t==T-1)]["wass"].iloc[0] -
                   wass[(wass.lens==l)&(wass.base==b)&(wass.world=="no_feedback")&(wass.t==T-1)]["wass"].iloc[0]), 5)
                   for l in LENSES for b in BASES})
(OUT / "v1304c_audit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
print("\n[保存] v1304c_audit_{icc,wasserstein,pooled_drift}.parquet + summary.json")
