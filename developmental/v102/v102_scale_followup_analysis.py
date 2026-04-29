"""v10.2 スケールテスト follow-up 解析 (7 項目)

7 項目を 5 スケール × 24 seeds で一括実行:
  1. lifespan × n_core × N
  2. repeated activation bins (0/1/2-4/5+)
  3. n_core ≥ 6 大型 coalition の空間分析
  4. C_max 帰属
  5. ghost residual_Q 時系列
  6. seed CV
  8. k* = 2L/N の N 依存

出力:
  developmental/v102/followup/
    followup_1_lifespan.csv
    followup_2_repeated.csv
    followup_3_large_coalition.csv
    followup_4_cmax.csv
    followup_4_cmax_summary.csv
    followup_5_ghost_timeline.csv
    followup_6_seed_cv.csv
    followup_8_kstar.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
OUT = ROOT / "followup"
OUT.mkdir(exist_ok=True)

SCALES = [
    (500, "diag_v102_main_n500"),
    (1000, "diag_v102_main_n1000"),
    (2500, "diag_v102_main_n2500"),
    (5000, "diag_v102_main"),
    (10000, "diag_v102_main_n10000"),
]

TRACKING_START_WINDOW = 20
WINDOW_STEPS = 500
TRACKING_TOTAL_STEPS = 50 * WINDOW_STEPS  # 25000
SEEDS = list(range(24))


def torus_dist(a: int, b: int, side: int) -> float:
    """torus 上の 2 ノードの距離"""
    ra, ca = a // side, a % side
    rb, cb = b // side, b % side
    dr = min(abs(ra - rb), side - abs(ra - rb))
    dc = min(abs(ca - cb), side - abs(ca - cb))
    return float(np.sqrt(dr * dr + dc * dc))


def load_seed_data(N: int, dirname: str, seed: int) -> dict:
    base = ROOT / dirname
    out = {}
    out["ps"] = pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv")
    out["psa"] = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")
    out["pl"] = pd.read_csv(base / f"labels/per_label_seed{seed}.csv")
    out["lmp"] = pd.read_csv(
        base / f"persistence/label_member_persistence_seed{seed}.csv")
    out["lll"] = pd.read_csv(
        base / f"persistence/link_life_log_seed{seed}.csv")
    out["bd"] = pd.read_csv(base / f"balance/balance_decisions_seed{seed}.csv")
    out["cj"] = pd.read_csv(base / f"balance/c_trajectory_seed{seed}.csv")
    out["bs"] = pd.read_csv(base / f"balance/balance_summary_seed{seed}.csv")
    out["ie"] = pd.read_csv(
        base / f"ingestion/ingestion_events_seed{seed}.csv")
    out["pw"] = pd.read_csv(base / f"aggregates/per_window_seed{seed}.csv")
    return out


# =========================================================================
# 1. lifespan × n_core × N
# =========================================================================
def analysis_1(all_scales: dict) -> pd.DataFrame:
    rows = []
    for N, scale_data in all_scales.items():
        for seed_data in scale_data["seeds"]:
            ps = seed_data["ps"].rename(columns={"cognitive_id": "cid"})
            psa = seed_data["psa"][["cid", "n_core_member",
                                    "registered_window", "registered_step"]]
            m = ps.merge(psa, on="cid", how="left")

            # tracking-relative birth/death step
            m["registered_global_step"] = (
                (m["registered_window"] - TRACKING_START_WINDOW) * WINDOW_STEPS
                + m["registered_step"]
            )
            m["death_global_step"] = m["host_lost_step"].fillna(
                TRACKING_TOTAL_STEPS)
            m["lifespan"] = (m["death_global_step"]
                             - m["registered_global_step"]).clip(lower=0)
            m["N"] = N
            rows.append(m[["N", "cid", "n_core_member",
                          "lifespan", "final_state"]])
    df = pd.concat(rows, ignore_index=True).rename(
        columns={"n_core_member": "n_core"})

    # 集計
    summary_rows = []
    for N in sorted(df["N"].unique()):
        for n_core in sorted(df[df["N"] == N]["n_core"].dropna().unique()):
            sub = df[(df["N"] == N) & (df["n_core"] == n_core)]
            if len(sub) < 2:
                continue
            summary_rows.append({
                "N": N,
                "n_core": int(n_core),
                "n_cid": len(sub),
                "lifespan_mean": float(sub["lifespan"].mean()),
                "lifespan_median": float(sub["lifespan"].median()),
                "lifespan_p25": float(sub["lifespan"].quantile(0.25)),
                "lifespan_p75": float(sub["lifespan"].quantile(0.75)),
            })
    return pd.DataFrame(summary_rows)


# =========================================================================
# 2. repeated activation bins
# =========================================================================
def analysis_2(all_scales: dict) -> pd.DataFrame:
    rows = []
    for N, scale_data in all_scales.items():
        for seed_data in scale_data["seeds"]:
            ps = seed_data["ps"].rename(columns={"cognitive_id": "cid"})
            psa = seed_data["psa"][["cid", "n_core_member"]]
            m = ps.merge(psa, on="cid", how="left")
            m["N"] = N
            m["n_consciousness"] = m["n_consciousness_decisions"].fillna(0).astype(int)
            rows.append(m[["N", "cid", "n_core_member", "n_consciousness"]])
    df = pd.concat(rows, ignore_index=True).rename(
        columns={"n_core_member": "n_core"})

    def bin_count(n):
        if n == 0:
            return "bin_0"
        elif n == 1:
            return "bin_1"
        elif 2 <= n <= 4:
            return "bin_2_4"
        else:
            return "bin_5plus"

    df["bin"] = df["n_consciousness"].apply(bin_count)

    summary_rows = []
    for N in sorted(df["N"].unique()):
        for n_core in sorted(df[df["N"] == N]["n_core"].dropna().unique()):
            sub = df[(df["N"] == N) & (df["n_core"] == n_core)]
            counts = sub["bin"].value_counts().to_dict()
            total = len(sub)
            row = {"N": N, "n_core": int(n_core), "n_total": total}
            for b in ["bin_0", "bin_1", "bin_2_4", "bin_5plus"]:
                cnt = counts.get(b, 0)
                row[b] = int(cnt)
                row[f"{b}_share"] = cnt / total if total else 0
            summary_rows.append(row)
    return pd.DataFrame(summary_rows)


# =========================================================================
# 3. n_core ≥ 6 大型 coalition の空間分析
# =========================================================================
def analysis_3(all_scales: dict) -> pd.DataFrame:
    """label_member_persistence (v9.13 audit 由来) で n_core ≥ 6 の coalition を抽出し
    link_life_log で node 座標を resolve、torus 距離で空間広がりを計算する。

    注意: label_member_persistence は v9.13 persistence_birth が検出した label のみ。
    runtime label tracker (per_label) とは別系統。両者で n_core ≥ 6 が検出される
    label の集合は異なる場合がある (本解析は前者のみを対象)。
    """
    rows = []
    for N, scale_data in all_scales.items():
        side = int(np.ceil(np.sqrt(N)))
        for seed_idx, seed_data in enumerate(scale_data["seeds"]):
            seed = seed_idx
            lmp = seed_data["lmp"]
            lll = seed_data["lll"]

            # link_id → (node1, node2) マップ (link は再誕生しうるが同 id は同 ペア)
            lll_uniq = lll.drop_duplicates(subset=["link_id"], keep="first")
            link_map = lll_uniq.set_index("link_id")[["node1", "node2"]].to_dict("index")

            # n_core ≥ 6 の label を抽出 (label_member_persistence ベース)
            big_lmp = lmp[lmp["n_core"] >= 6]
            if len(big_lmp) == 0:
                continue

            for label_id, sub in big_lmp.groupby("label_id"):
                # member ノード集合
                nodes = set()
                for lid in sub["link_id"]:
                    if lid in link_map:
                        nodes.add(int(link_map[lid]["node1"]))
                        nodes.add(int(link_map[lid]["node2"]))
                nodes = sorted(nodes)
                if len(nodes) < 2:
                    continue
                # pairwise torus 距離
                dists = []
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        dists.append(torus_dist(nodes[i], nodes[j], side))
                if not dists:
                    continue

                rows.append({
                    "N": N,
                    "seed": seed,
                    "label_id": int(label_id),
                    "n_core": int(sub["n_core"].iloc[0]),
                    "n_member_nodes": len(nodes),
                    "n_links": len(sub),
                    "dist_median": float(np.median(dists)),
                    "dist_max": float(max(dists)),
                    "dist_mean": float(np.mean(dists)),
                    "dist_max_normalized":
                        float(max(dists) / (side / np.sqrt(2))),
                })
    return pd.DataFrame(rows)


# =========================================================================
# 4. C_max 帰属
# =========================================================================
def analysis_4(all_scales: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail_rows = []
    summary_rows = []

    for N, scale_data in all_scales.items():
        for seed_data in scale_data["seeds"]:
            cj = seed_data["cj"]
            ps = seed_data["ps"].rename(columns={"cognitive_id": "cid"})
            psa = seed_data["psa"][["cid", "n_core_member"]]

            # 各 cid の C_max
            c_max = (cj.groupby("cid")["C_at_window_end"].max()
                     .rename("c_max").reset_index())

            m = c_max.merge(ps, on="cid", how="left").merge(psa, on="cid",
                                                             how="left")
            m["N"] = N
            m["n_core"] = m["n_core_member"]
            m["lifespan"] = (
                (m["host_lost_step"].fillna(TRACKING_TOTAL_STEPS)).clip(
                    lower=0)
            )
            m["n_consciousness"] = m["n_consciousness_decisions"].fillna(
                0).astype(int)
            m["n_ingestions"] = m["n_ingestions_as_eater"].fillna(0).astype(int)

            detail_rows.append(m[[
                "N", "cid", "n_core", "lifespan", "c_max",
                "n_consciousness", "n_ingestions"
            ]])

    detail = pd.concat(detail_rows, ignore_index=True)
    detail.to_csv(OUT / "followup_4_cmax.csv", index=False)

    # サマリ: 各 N で C_max 達成 cid + 高 C cid 数
    for N in sorted(detail["N"].unique()):
        sub = detail[detail["N"] == N]
        c_top = sub.nlargest(1, "c_max").iloc[0]
        summary_rows.append({
            "N": N,
            "C_max_overall": int(c_top["c_max"]),
            "C_max_cid_n_core": int(c_top["n_core"]) if pd.notna(c_top["n_core"]) else None,
            "C_max_cid_lifespan": int(c_top["lifespan"]),
            "C_max_cid_n_consciousness": int(c_top["n_consciousness"]),
            "C_max_cid_n_ingestions": int(c_top["n_ingestions"]),
            "n_cid_C_ge_50": int((sub["c_max"] >= 50).sum()),
            "n_cid_C_ge_60": int((sub["c_max"] >= 60).sum()),
            "n_cid_C_ge_70": int((sub["c_max"] >= 70).sum()),
            "n_cid_C_ge_80": int((sub["c_max"] >= 80).sum()),
            "n_cid_total": len(sub),
        })

    return detail, pd.DataFrame(summary_rows)


# =========================================================================
# 5. ghost residual_Q 時系列
# =========================================================================
def analysis_5(all_scales: dict) -> pd.DataFrame:
    rows = []
    for N, scale_data in all_scales.items():
        for seed_idx, seed_data in enumerate(scale_data["seeds"]):
            seed = seed_idx
            ps = seed_data["ps"].rename(columns={"cognitive_id": "cid"})
            ie = seed_data["ie"]

            # 各 ghost cid の incoming food (initial residual_Q) と
            # 消費 (received + digested) を集計
            ghosts = ps[ps["initial_residual_Q"].notna()
                        & (ps["initial_residual_Q"] > 0)].copy()

            # ghost ごとの window 別累積消費
            ie_agg = ie.groupby(["ghost_cid", "window"]).agg(
                consumed=("received", "sum"),
                digested=("digested", "sum")
            ).reset_index()
            ie_agg["total_consumed"] = ie_agg["consumed"] + ie_agg["digested"]

            # ghost 別: cumulative consumed up to each window
            cum = (ie_agg.sort_values(["ghost_cid", "window"])
                   .groupby("ghost_cid")["total_consumed"]
                   .cumsum().rename("cum_consumed"))
            ie_agg = ie_agg.assign(cum_consumed=cum)

            # ghost ごとの host_lost_window と reaped_window (= lifecycle)
            ghost_meta = ghosts.set_index("cid")[
                ["initial_residual_Q", "host_lost_window", "reaped_step"]
            ].to_dict("index")

            # 各 window で alive な ghost を集計
            for w in range(20, 70):
                total_q = 0.0
                ghost_count = 0
                for gcid, meta in ghost_meta.items():
                    hlw = meta["host_lost_window"]
                    if pd.isna(hlw) or hlw > w:
                        continue
                    # reaped 判定
                    rs = meta["reaped_step"]
                    if pd.notna(rs):
                        reaped_w = int(rs / WINDOW_STEPS) + TRACKING_START_WINDOW - 1
                        if w >= reaped_w:
                            continue
                    init_q = meta["initial_residual_Q"]
                    # 累積消費 (この window までの)
                    sub = ie_agg[(ie_agg["ghost_cid"] == gcid)
                                 & (ie_agg["window"] <= w)]
                    if len(sub) > 0:
                        cum_c = sub["cum_consumed"].max()
                    else:
                        cum_c = 0
                    res_q = max(0, init_q - cum_c)
                    total_q += res_q
                    ghost_count += 1

                rows.append({
                    "N": N,
                    "seed": seed,
                    "window": w,
                    "ghost_count": ghost_count,
                    "ghost_residual_Q_total": total_q,
                })
    return pd.DataFrame(rows)


# =========================================================================
# 6. seed CV
# =========================================================================
def analysis_6(all_scales: dict) -> pd.DataFrame:
    rows = []
    for N, scale_data in all_scales.items():
        # per-seed values
        per_seed = []
        for seed_idx, seed_data in enumerate(scale_data["seeds"]):
            bs = seed_data["bs"].iloc[0]
            ps = seed_data["ps"]
            psa = seed_data["psa"]

            n_subjects = len(ps)
            total_d = bs["total_decisions"]
            cog_rate = (bs["n_cognition_won"] / total_d
                        if total_d > 0 else 0)
            con_rate = (bs["n_consciousness_won"] / total_d
                        if total_d > 0 else 0)

            # 意識発動経験率
            n_activated = (ps["n_consciousness_decisions"].fillna(0) > 0).sum()
            activation_rate = (n_activated / n_subjects
                               if n_subjects > 0 else 0)

            per_seed.append({
                "seed": seed_idx,
                "n_subjects": n_subjects,
                "cog_rate": cog_rate,
                "con_rate": con_rate,
                "activation_rate": activation_rate,
            })

        df = pd.DataFrame(per_seed)
        for col in ["n_subjects", "cog_rate", "con_rate", "activation_rate"]:
            mean_v = df[col].mean()
            std_v = df[col].std()
            cv = std_v / mean_v if mean_v != 0 else None
            rows.append({
                "N": N,
                "indicator": col,
                "n_seeds": len(df),
                "mean": float(mean_v),
                "std": float(std_v),
                "cv": float(cv) if cv is not None else None,
            })
    return pd.DataFrame(rows)


# =========================================================================
# 8. k* = 2L/N の N 依存
# =========================================================================
def analysis_8(all_scales: dict) -> pd.DataFrame:
    rows = []
    for N, scale_data in all_scales.items():
        per_seed_means = []
        for seed_data in scale_data["seeds"]:
            pw = seed_data["pw"]
            mean_links = pw["links"].mean()
            per_seed_means.append(mean_links)
        per_seed_arr = np.array(per_seed_means)
        rows.append({
            "N": N,
            "links_mean_overall": float(per_seed_arr.mean()),
            "links_std_seeds": float(per_seed_arr.std()),
            "kstar_mean": 2 * float(per_seed_arr.mean()) / N,
            "kstar_std_seeds": 2 * float(per_seed_arr.std()) / N,
        })
    return pd.DataFrame(rows)


# =========================================================================
# main
# =========================================================================
def main():
    print("Loading 5 scales × 24 seeds...")
    all_scales = {}
    for N, dirname in SCALES:
        print(f"  N={N} ({dirname})...")
        seeds_data = []
        for seed in SEEDS:
            try:
                d = load_seed_data(N, dirname, seed)
                seeds_data.append(d)
            except FileNotFoundError as e:
                print(f"    [warn] seed {seed}: {e}")
        all_scales[N] = {"dirname": dirname, "seeds": seeds_data}
        print(f"    loaded {len(seeds_data)} seeds")

    print("\n## Analysis 1: lifespan × n_core × N")
    df1 = analysis_1(all_scales)
    df1.to_csv(OUT / "followup_1_lifespan.csv", index=False)
    print(df1.to_string(index=False))

    print("\n## Analysis 2: repeated activation bins")
    df2 = analysis_2(all_scales)
    df2.to_csv(OUT / "followup_2_repeated.csv", index=False)
    print(df2.to_string(index=False))

    print("\n## Analysis 3: 大型 coalition (n_core ≥ 6) 空間分析")
    df3 = analysis_3(all_scales)
    df3.to_csv(OUT / "followup_3_large_coalition.csv", index=False)
    if len(df3) > 0:
        # Summary by N
        s3 = df3.groupby("N").agg(
            n_coalitions=("label_id", "count"),
            n_cores_max=("n_core", "max"),
            n_cores_mean=("n_core", "mean"),
            n_member_nodes_median=("n_member_nodes", "median"),
            dist_max_norm_median=("dist_max_normalized", "median"),
            dist_max_norm_mean=("dist_max_normalized", "mean"),
        ).reset_index()
        print(s3.to_string(index=False))
        s3.to_csv(OUT / "followup_3_large_coalition_summary.csv", index=False)

    print("\n## Analysis 4: C_max 帰属")
    df4_detail, df4_summary = analysis_4(all_scales)
    df4_summary.to_csv(OUT / "followup_4_cmax_summary.csv", index=False)
    print(df4_summary.to_string(index=False))

    print("\n## Analysis 5: ghost residual_Q 時系列")
    df5 = analysis_5(all_scales)
    df5.to_csv(OUT / "followup_5_ghost_timeline.csv", index=False)
    # Summary: per N × window 平均
    s5 = df5.groupby(["N", "window"]).agg(
        ghost_count_mean=("ghost_count", "mean"),
        ghost_residual_Q_mean=("ghost_residual_Q_total", "mean"),
    ).reset_index()
    s5.to_csv(OUT / "followup_5_ghost_timeline_summary.csv", index=False)
    print("(time series: see followup_5_ghost_timeline_summary.csv)")
    print(f"  rows: per (seed, window) = {len(df5)}, summary rows = {len(s5)}")

    print("\n## Analysis 6: seed CV")
    df6 = analysis_6(all_scales)
    df6.to_csv(OUT / "followup_6_seed_cv.csv", index=False)
    print(df6.to_string(index=False))

    print("\n## Analysis 8: k* = 2L/N")
    df8 = analysis_8(all_scales)
    df8.to_csv(OUT / "followup_8_kstar.csv", index=False)
    print(df8.to_string(index=False))

    print(f"\nDone. Outputs in {OUT}")


if __name__ == "__main__":
    main()
