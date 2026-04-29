"""v10.2 N-sweep 追加 3 解析

A. N=5000 主役プール 270 cid の内訳
B. N=10000 で n_core ≥ 6 coalition が消える条件の再点検 (shadow_component_log)
C. n_core=2 / 5 の比較表 (寿命 / 意識発動 / 反復発動)

出力:
  developmental/v102/followup/
    extra_A_main_pool_n5000.csv
    extra_A_main_pool_n5000_summary.csv
    extra_B_component_distribution.csv
    extra_C_n2_vs_n5_comparison.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
OUT = ROOT / "followup"

SCALES = [
    (500, "diag_v102_main_n500"),
    (1000, "diag_v102_main_n1000"),
    (2500, "diag_v102_main_n2500"),
    (5000, "diag_v102_main"),
    (10000, "diag_v102_main_n10000"),
]

TRACKING_START_WINDOW = 20
WINDOW_STEPS = 500
TRACKING_TOTAL_STEPS = 50 * WINDOW_STEPS
SEEDS = list(range(24))


# =========================================================================
# A. N=5000 主役プール 270 cid の内訳
# =========================================================================
def analysis_A() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for seed in SEEDS:
        base = ROOT / "diag_v102_main"
        ps = pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv")
        ps = ps.rename(columns={"cognitive_id": "cid"})
        psa = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")
        cj = pd.read_csv(base / f"balance/c_trajectory_seed{seed}.csv")

        m = ps.merge(psa[["cid", "n_core_member", "v14_q0",
                          "registered_window", "registered_step"]],
                     on="cid", how="left")
        m["n_core"] = m["n_core_member"]
        m["registered_global_step"] = (
            (m["registered_window"] - TRACKING_START_WINDOW) * WINDOW_STEPS
            + m["registered_step"]
        )
        m["death_global_step"] = m["host_lost_step"].fillna(
            TRACKING_TOTAL_STEPS)
        m["lifespan"] = (m["death_global_step"]
                         - m["registered_global_step"]).clip(lower=0)
        m["n_consciousness"] = m["n_consciousness_decisions"].fillna(
            0).astype(int)
        m["n_cognition"] = m["n_cognition_decisions"].fillna(0).astype(int)
        m["n_skip"] = m["n_balance_skipped"].fillna(0).astype(int)
        m["n_ingestions"] = m["n_ingestions_as_eater"].fillna(0).astype(int)

        # C_max from c_trajectory
        c_max = cj.groupby("cid")["C_at_window_end"].max().rename("c_max")
        m = m.merge(c_max, on="cid", how="left")

        # 主役プール: n_core >= 4 かつ n_consciousness >= 5
        pool = m[(m["n_core"] >= 4) & (m["n_consciousness"] >= 5)].copy()
        pool["seed"] = seed
        rows.append(pool[[
            "seed", "cid", "n_core", "v14_q0", "lifespan",
            "n_cognition", "n_consciousness", "n_skip",
            "n_ingestions", "c_max", "C_at_run_end", "final_state",
        ]])

    df = pd.concat(rows, ignore_index=True)

    # サマリ: n_core × consciousness bin
    def n_con_bin(n):
        if n < 5: return "< 5"
        elif n < 10: return "5-9"
        elif n < 20: return "10-19"
        elif n < 50: return "20-49"
        else: return "50+"

    df["n_con_bin"] = df["n_consciousness"].apply(n_con_bin)

    summary_rows = []
    for n_core in sorted(df["n_core"].unique()):
        for bin_label in ["5-9", "10-19", "20-49", "50+"]:
            sub = df[(df["n_core"] == n_core) & (df["n_con_bin"] == bin_label)]
            if len(sub) == 0:
                continue
            summary_rows.append({
                "n_core": int(n_core),
                "n_consciousness_bin": bin_label,
                "n_cid": len(sub),
                "lifespan_median": float(sub["lifespan"].median()),
                "lifespan_p25": float(sub["lifespan"].quantile(0.25)),
                "lifespan_p75": float(sub["lifespan"].quantile(0.75)),
                "c_max_median": float(sub["c_max"].median()),
                "C_at_run_end_median": float(sub["C_at_run_end"].median()),
                "n_ingestions_median": float(sub["n_ingestions"].median()),
                "Q0_median": float(sub["v14_q0"].median()),
                "alive_at_run_end": int(
                    (sub["final_state"] == "hosted").sum()),
                "ghost_at_run_end": int(
                    (sub["final_state"] == "ghost").sum()),
                "reaped": int((sub["final_state"] == "reaped").sum()),
            })
    summary = pd.DataFrame(summary_rows)
    return df, summary


# =========================================================================
# B. N=10000 で n_core ≥ 6 が消える条件の再点検
#    (shadow_component_log: persistence threshold 通過候補のサイズ分布)
# =========================================================================
def analysis_B() -> pd.DataFrame:
    rows = []
    for N, dirname in SCALES:
        base = ROOT / dirname
        for seed in SEEDS:
            f = base / f"persistence/shadow_component_log_seed{seed}.csv"
            if not f.exists():
                continue
            df = pd.read_csv(f)
            df["N"] = N
            df["seed"] = seed
            rows.append(df)

    all_df = pd.concat(rows, ignore_index=True)

    # 集計: per (N, threshold) × comp_size の頻度
    agg_rows = []
    for N in sorted(all_df["N"].unique()):
        for thr in sorted(all_df[all_df["N"] == N]["threshold"].unique()):
            sub = all_df[(all_df["N"] == N) & (all_df["threshold"] == thr)]
            for size in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
                count = (sub["comp_size"] == size).sum()
                agg_rows.append({
                    "N": N,
                    "threshold": int(thr),
                    "comp_size": size,
                    "n_components_observed": int(count),
                })
            # >= 11 もカウント
            count_ge11 = (sub["comp_size"] >= 11).sum()
            agg_rows.append({
                "N": N,
                "threshold": int(thr),
                "comp_size": "11+",
                "n_components_observed": int(count_ge11),
            })

    return pd.DataFrame(agg_rows)


# =========================================================================
# C. n_core=2 / 5 比較表
# =========================================================================
def analysis_C() -> pd.DataFrame:
    rows = []
    for N, dirname in SCALES:
        base = ROOT / dirname
        per_seed = []
        for seed in SEEDS:
            ps = pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv")
            ps = ps.rename(columns={"cognitive_id": "cid"})
            psa = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")
            psa_keys = psa[["cid", "n_core_member",
                            "registered_window", "registered_step"]]
            m = ps.merge(psa_keys, on="cid", how="left")
            m["n_core"] = m["n_core_member"]
            m["registered_global_step"] = (
                (m["registered_window"] - TRACKING_START_WINDOW) * WINDOW_STEPS
                + m["registered_step"]
            )
            m["death_global_step"] = m["host_lost_step"].fillna(
                TRACKING_TOTAL_STEPS)
            m["lifespan"] = (m["death_global_step"]
                             - m["registered_global_step"]).clip(lower=0)
            m["n_consciousness"] = m["n_consciousness_decisions"].fillna(
                0).astype(int)
            m["n_ingestions"] = m["n_ingestions_as_eater"].fillna(0).astype(int)
            m["seed"] = seed
            per_seed.append(m[[
                "seed", "cid", "n_core", "lifespan",
                "n_consciousness", "n_ingestions", "C_at_run_end",
            ]])
        df = pd.concat(per_seed, ignore_index=True)

        # n_core 2 と 5 のみ抽出
        for nc in [2, 5]:
            sub = df[df["n_core"] == nc]
            n_total = len(sub)
            n_activated = (sub["n_consciousness"] > 0).sum()
            n_repeated = (sub["n_consciousness"] >= 5).sum()
            rows.append({
                "N": N,
                "n_core": nc,
                "n_cid": n_total,
                "lifespan_median": float(sub["lifespan"].median()),
                "lifespan_p25": float(sub["lifespan"].quantile(0.25)),
                "lifespan_p75": float(sub["lifespan"].quantile(0.75)),
                "lifespan_max": float(sub["lifespan"].max()),
                "n_activated": int(n_activated),
                "activation_rate": float(n_activated / n_total)
                                   if n_total else 0,
                "n_repeated_5plus": int(n_repeated),
                "repeated_5plus_rate": float(n_repeated / n_total)
                                       if n_total else 0,
                "n_ingestions_median": float(sub["n_ingestions"].median()),
                "n_ingestions_mean": float(sub["n_ingestions"].mean()),
                "n_consciousness_median": float(sub["n_consciousness"].median()),
                "n_consciousness_mean": float(sub["n_consciousness"].mean()),
                "C_at_run_end_mean": float(sub["C_at_run_end"].mean()),
            })
    return pd.DataFrame(rows)


# =========================================================================
# main
# =========================================================================
def main():
    print("## A. N=5000 主役プール 内訳")
    a_detail, a_summary = analysis_A()
    a_detail.to_csv(OUT / "extra_A_main_pool_n5000.csv", index=False)
    a_summary.to_csv(OUT / "extra_A_main_pool_n5000_summary.csv", index=False)
    print(f"  per cid 行数: {len(a_detail)}")
    print(a_summary.to_string(index=False))

    print("\n## B. N=10000 で n_core ≥ 6 が消える条件 (shadow_component_log)")
    b_df = analysis_B()
    b_df.to_csv(OUT / "extra_B_component_distribution.csv", index=False)
    # 表示: threshold=50 のみ
    print("--- threshold=50 (= persistence 通過候補) ---")
    pivot = b_df[b_df["threshold"] == 50].pivot_table(
        index="N", columns="comp_size",
        values="n_components_observed", fill_value=0)
    print(pivot.to_string())

    print("\n## C. n_core=2 / 5 比較表")
    c_df = analysis_C()
    c_df.to_csv(OUT / "extra_C_n2_vs_n5_comparison.csv", index=False)
    print(c_df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
