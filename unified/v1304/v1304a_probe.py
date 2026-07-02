# v1304a probe — 「管に書ける動的な珍しさ」は有るか（子 run なし・相関スキャン・read-only・#12）
# 出口一点: s_avg(v1302実証チャネル plb←s_avg)と相関する動的珍しさが有るか無いか。
#   有→eye候補(採用はTaka・Stage3b同型検証が別途必須)・無→(iii)feedbackが事実で残る。
# Part1: 既存3動的eye lift × dense per-cid量 の相関地形図。Part2(Taka案): step毎物理量に-log10珍しさ(global/ncore)
#   を掛けて動的bgen候補を作り s_avg相関を bgen較正点|0.55|併記で測る。新run/新ledger禁止・スキャンのみで停止。
# 多重スキャンの自覚: 候補は候補止まり(採用前にStage3b同型composition検証が必須)・閾値置かず・2 lift定義併記。

import numpy as np, pandas as pd
from pathlib import Path

REPO = Path("/home/takasan/esde/ESDE-Research")
OUT = REPO / "unified/v1304/outputs"
SEED = 0
LED = REPO / "unified/v1303/outputs/v1303_ledger_seed0.parquet"
SCHEMA = REPO / f"unified/v1303/outputs/v1303j/v1303_final_attention_output_seed{SEED}.parquet"
PS = REPO / "developmental/v105/diag_v105_main_v2/subjects/per_subject_seed0.csv"
BGEN_CALIB = 0.545   # 分離が実測された相関水準(較正点・カットオフでない)


def log(m): print(f"[probe] {m}", flush=True)


def eye_lift(sch, eye, kind):
    e = sch[sch.eye_id == eye].copy()
    e["pe"] = e["p_select_given_eye_t"] * e["eligible_count"]
    if kind == "eligible":
        e = e[e["p_select_given_eye_t"] > 0]
    return e.groupby("cid")["pe"].mean()


def dyn_rarity_lift(led, valcol, scope, kind):
    """step毎物理量valの-log10珍しさ(scope=global/ncore)をlift化(kind=eligible/alive)。"""
    d = led[["cid", "t", "n_core", valcol]].dropna(subset=[valcol]).copy()
    grp = d.groupby("t") if scope == "global" else d.groupby(["t", "n_core"])
    pct = grp[valcol].rank(pct=True)
    n = grp[valcol].transform("count")
    two = (2 * np.minimum(pct, 1 - pct)).clip(lower=1.0 / (2 * n))   # 両側tail・floor
    d["rar"] = -np.log10(two)
    # 各tでalive内正規化 → lift
    s = d.groupby("t")["rar"].transform("sum")
    cnt = d.groupby("t")["cid"].transform("size")
    d["pe"] = (d["rar"] / s) * cnt
    if kind == "eligible":
        d = d[d["rar"] > 0]   # 珍しさ0(=中央)を除くeligible的絞り
    return d.groupby("cid")["pe"].mean()


def corr_on(a, b):
    idx = a.index.intersection(b.index)
    x, y = a.reindex(idx).values, b.reindex(idx).values
    m = ~(np.isnan(x) | np.isnan(y))
    return (float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 3 and np.std(x[m]) > 0 and np.std(y[m]) > 0 else np.nan, int(m.sum()))


def main():
    sch = pd.read_parquet(SCHEMA)
    led = pd.read_parquet(LED)
    ps = pd.read_csv(PS)
    def col(c): return pd.Series(pd.to_numeric(ps[c], errors="coerce").values, index=ps["cognitive_id"])
    s_avg = col("v11_m_c_s_avg").dropna()   # 45支持・実証チャネル

    # ---- Part 1: 既存3動的eye lift × dense per-cid量 ----
    dyn_eyes = ["now_theta", "archive_theta_percentile", "link_rarity"]
    dense_q = ["v11_m_c_s_avg", "original_phase_sig", "v18_v_unified_concentration_birth",
               "v18_v_unified_concentration_final", "v18_cognitive_gain_final", "v18_theta_distance_from_birth_final",
               "v10_R_social_last", "v10_R_stability_last", "v10_R_spread_last", "v10_R_familiarity_last",
               "last_attention_size", "last_n_partners", "last_familiarity_max", "final_residual_Q",
               "C_at_run_end", "total_q_digested", "n_observed_as_target"]
    rows1 = []
    for eye in dyn_eyes:
        for kind in ["eligible", "alive"]:
            L = eye_lift(sch, eye, kind)
            for q in dense_q:
                r, n = corr_on(L, col(q).dropna())
                rows1.append(dict(eye=eye, lift_def=kind, dense_q=q, corr=round(r, 3) if not np.isnan(r) else np.nan, n=n))
    p1 = pd.DataFrame(rows1)
    p1.to_parquet(OUT / "v1304a_probe_scan_part1.parquet")
    log("Part1 done")

    # ---- Part 2: Taka案 動的bgen(step毎物理量の珍しさ) × s_avg ----
    phys = {"E_mean": "core_node_E_mean", "S_mean": "core_internal_S_mean", "R_mean": "core_internal_R_mean",
            "R_positive": "core_internal_R_positive_count", "link_count": "core_internal_link_count",
            "theta_resultant": "core_node_theta_resultant_length", "C": "C_at_window_end", "Q": "Q_remaining_at_window_end"}
    rows2 = []
    for name, vc in phys.items():
        if vc not in led.columns:
            continue
        for scope in ["global", "ncore"]:
            for kind in ["eligible", "alive"]:
                L = dyn_rarity_lift(led, vc, scope, kind)
                r, n = corr_on(L, s_avg)
                rows2.append(dict(dyn_bgen_of=name, scope=scope, lift_def=kind,
                                  corr_with_s_avg=round(r, 3) if not np.isnan(r) else np.nan,
                                  n_support=n, bgen_calib=BGEN_CALIB,
                                  reaches_calib=(abs(r) >= BGEN_CALIB) if not np.isnan(r) else False))
    p2 = pd.DataFrame(rows2)
    p2.to_parquet(OUT / "v1304a_probe_dynbgen_part2.parquet")
    log("Part2 done")
    return p1, p2


if __name__ == "__main__":
    p1, p2 = main()
    pd.set_option("display.width", 200)
    print("\n===== Part 1: 動的eye lift × dense per-cid量 相関(|corr|降順 top20) =====")
    p1["ac"] = p1["corr"].abs()
    print(p1.sort_values("ac", ascending=False).drop(columns="ac").head(20).to_string(index=False))
    print("\n===== Part 2: 動的bgen(step毎物理量の珍しさ) × s_avg 相関(|corr|降順) =====")
    print("  (較正点 bgen |0.545| = 小さいが robust な分離が実測された水準・カットオフでない)")
    p2["ac"] = p2["corr_with_s_avg"].abs()
    print(p2.sort_values("ac", ascending=False).drop(columns="ac").to_string(index=False))
    m = p2["corr_with_s_avg"].abs().max()
    print(f"\n  Part2 最大 |corr(動的bgen, s_avg)| = {m:.3f}  (bgen較正点 0.545)")
