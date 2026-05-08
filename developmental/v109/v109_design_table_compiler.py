#!/usr/bin/env python3
"""v10.9 design table compiler (Step M).

Step F + Step L 結果を統合し、v10.10 主題決定の素材として 4 種設計表 +
4 階層 reports + 構造的統合解析を生成。

入力:
  - v109 main sensitivity_evaluation_all.parquet (Step L)
  - v109 main bimodal_analysis_all.parquet (Step F)
  - v108 main natural_baseline_diff_seed*.parquet (v10.7 natural baseline)
  - v108 main excess_change_adjusted_seed*.parquet (A1 baseline)

出力 (developmental/v109/outputs/main/cross_seed/):
  4 種設計表:
    - design_table_1_sensitivity.parquet
    - design_table_2_receptivity.parquet
    - design_table_3_routing.parquet
    - design_table_4_naturalness.parquet
  4 階層 reports:
    - level_1_mechanism_check.parquet
    - level_2_condition_diff.parquet
    - level_3_sensitivity.parquet
    - level_3_5_structural_integration.parquet
  構造的統合:
    - structural_integration_path_bimodal_timing.parquet
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V109_ROOT = (REPO_ROOT / "developmental" / "v109").resolve()

V108_MAIN = V108_ROOT / "outputs" / "main"
V109_MAIN = V109_ROOT / "outputs" / "main"
CROSS_SEED = V109_MAIN / "cross_seed"

SEEDS = list(range(24))
WINDOWS = ["immediate", "short", "medium"]
DELTA_METRICS = [
    "mean_delta_R_familiarity", "mean_delta_Q", "mean_delta_C",
    "mean_delta_n_alphas", "mean_delta_n_observed", "mean_n_pulses_in_window",
]
NATURAL_PATHS = [
    "familiarity", "attention_via_salience", "integration_alpha",
    "integration_beta", "temporal_coactivation",
]
BASELINE_PATHS = [
    "unrelated_baseline", "same_step_random_baseline", "matched_baseline",
    "same_integration_low_familiarity_baseline",
    "high_familiarity_outside_integration_baseline",
]


def assert_output_under_v109(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")


def safe_write_parquet_v109(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v109(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 表 1: sensitivity_summary
# ----------------------------------------------------------------------
def build_table_1_sensitivity(df_sens: pd.DataFrame) -> pd.DataFrame:
    """24 seeds で comparison × metric × path × window 別の cohens_d (mean ± std)."""
    g = df_sens.groupby(["comparison", "cond_a", "cond_b", "metric",
                            "relation_path_type", "observation_window"])
    rows = []
    for keys, sub in g:
        rows.append({
            "comparison": keys[0],
            "cond_a": keys[1], "cond_b": keys[2],
            "metric": keys[3],
            "relation_path_type": keys[4],
            "observation_window": keys[5],
            "n_seeds": int(len(sub)),
            "cohens_d_mean": float(sub["cohens_d"].mean()),
            "cohens_d_std": float(sub["cohens_d"].std()),
            "cohens_d_abs_mean": float(sub["cohens_d"].abs().mean()),
            "delta_mean_avg": float(sub["delta_mean"].mean()),
        })
    df_t1 = pd.DataFrame(rows)
    df_t1["effect_size_label"] = df_t1["cohens_d_abs_mean"].apply(
        lambda d: "negligible" if d < 0.1 else
                  "small" if d < 0.3 else
                  "medium" if d < 0.5 else
                  "large"
    )
    return df_t1


# ----------------------------------------------------------------------
# 表 2: receptivity_detection_criteria
# ----------------------------------------------------------------------
def build_table_2_receptivity(df_bim: pd.DataFrame, df_sens: pd.DataFrame) -> pd.DataFrame:
    """Step F (cid age<=500) + Step L (Integration 外 + 高 familiarity) 統合.

    各 cid 属性候補について「受信可能状態」スコアを定義。
    """
    gen = df_bim[df_bim["subtype"] == "genuine_bimodal"]
    h3 = gen[gen["best_hypothesis"] == "H3_lifecycle"]

    # 主属性: H3 の高 delta 群 cid age 平均 = 受信可能状態の中心 age
    age_target_mean = float(h3["h3_high_age_mean"].mean())
    age_target_median = float(h3["h3_high_age_mean"].median())
    age_off_mean = float(h3["h3_low_age_mean"].mean())

    # 副属性: H1 (n_core)
    h1 = gen[gen["best_hypothesis"] == "H1_n_core"]
    n_core_target = float(h1["h1_high_mean"].mean()) if len(h1) > 0 else float("nan")
    n_core_off = float(h1["h1_low_mean"].mean()) if len(h1) > 0 else float("nan")

    # path 軸: high_fam_out_integ が timing 感度最強 (Step L)
    sens_cm = df_sens[(df_sens["comparison"] == "timing")
                       & (df_sens["metric"] == "mean_delta_C")
                       & (df_sens["observation_window"] == "medium")]
    sens_by_path = sens_cm.groupby("relation_path_type")["cohens_d"].agg(
        ["mean", "std", "count"]
    ).reset_index()

    high_fam_out_d = (
        float(sens_by_path[sens_by_path["relation_path_type"]
                              == "high_familiarity_outside_integration_baseline"]["mean"].iloc[0])
        if "high_familiarity_outside_integration_baseline" in sens_by_path["relation_path_type"].values
        else float("nan")
    )
    rows = [
        {"criterion": "cid_age", "operator": "<=",
         "value_str": str(int(age_target_mean * 2.5)),
         "central_value_str": str(int(age_target_median)),
         "evidence_source": "Step F H3_lifecycle (high delta age)",
         "evidence_effect_size": float(h3["best_effect_size"].mean()),
         "evidence_n_cells": int(len(h3)),
         "rationale": f"高 delta cid age mean {age_target_mean:.0f}, median {age_target_median:.0f} vs 低 delta {age_off_mean:.0f}"},
        {"criterion": "in_integration", "operator": "==",
         "value_str": "0",
         "central_value_str": "0",
         "evidence_source": "Step L high_fam_out_integ timing 感度",
         "evidence_effect_size": high_fam_out_d,
         "evidence_n_cells": 24,
         "rationale": "Integration 外の cid が timing 感度最強 (high_fam_out_integ baseline 0.222)"},
        {"criterion": "familiarity_max", "operator": ">=",
         "value_str": "top_quartile",
         "central_value_str": "top 25%",
         "evidence_source": "Step L high_fam_out_integ baseline",
         "evidence_effect_size": high_fam_out_d,
         "evidence_n_cells": 24,
         "rationale": "high_familiarity_outside_integration baseline (top 25% fam) で最強感度"},
        {"criterion": "n_core_member (副)", "operator": ">=",
         "value_str": f"{n_core_target:.2f}" if not np.isnan(n_core_target) else "nan",
         "central_value_str": f"{n_core_target:.2f}" if not np.isnan(n_core_target) else "nan",
         "evidence_source": "Step F H1_n_core (副次 26.3%)",
         "evidence_effect_size": float(h1["best_effect_size"].mean()) if len(h1) > 0 else float("nan"),
         "evidence_n_cells": int(len(h1)),
         "rationale": f"H1 仮説で高 delta cid n_core mean {n_core_target:.2f} vs 低 delta {n_core_off:.2f}"},
    ]
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 表 3: input_routing_criteria
# ----------------------------------------------------------------------
def build_table_3_routing(df_sens: pd.DataFrame) -> pd.DataFrame:
    """timing × path 別の routing 推奨 (high_fam_out 優先、attention 回避)."""
    sens = df_sens[(df_sens["comparison"] == "timing")
                       & (df_sens["metric"] == "mean_delta_C")
                       & (df_sens["observation_window"] == "medium")]
    g = sens.groupby("relation_path_type")["cohens_d"].agg(
        ["mean", "std", "count"]
    ).reset_index()
    g.columns = ["relation_path_type", "cohens_d_mean", "cohens_d_std", "n_seeds"]
    g["abs_mean"] = g["cohens_d_mean"].abs()
    g = g.sort_values("abs_mean", ascending=False).reset_index(drop=True)
    g["routing_rank"] = range(1, len(g) + 1)
    g["routing_recommendation"] = g.apply(
        lambda r: "PREFER" if r["cohens_d_mean"] >= 0.15 else
                  "USE_IF_AVAILABLE" if r["cohens_d_mean"] >= 0.05 else
                  "NEUTRAL" if abs(r["cohens_d_mean"]) < 0.05 else
                  "AVOID" if r["cohens_d_mean"] <= -0.10 else "MARGINAL",
        axis=1,
    )
    return g


# ----------------------------------------------------------------------
# 表 4: natural_likeness_design_criteria
# ----------------------------------------------------------------------
def build_table_4_naturalness(df_sens: pd.DataFrame) -> pd.DataFrame:
    """v10.7 natural baseline (5 source events) と C2 atom_intro の比較.

    各 (path, window, metric) で:
      - natural mean delta (5 source 平均)
      - A1 mean delta (atom_intro v10.8)
      - C2 mean delta (atom_intro lifecycle 同調)
      - introduced_vs_natural_ratio_A1 = A1 / natural
      - introduced_vs_natural_ratio_C2 = C2 / natural
      - C2_closer_to_natural = (|C2-natural| < |A1-natural|)
    """
    # natural baseline 集計 (24 seeds)
    nat_dfs = []
    for s in SEEDS:
        p = V108_MAIN / f"natural_baseline_diff_seed{s}.parquet"
        if p.exists():
            nat_dfs.append(pd.read_parquet(p))
    df_nat = pd.concat(nat_dfs, ignore_index=True)
    nat_mean = df_nat.groupby(["event_source_type", "relation_path_type"])[
        [f"{m}_{w}" for m in DELTA_METRICS for w in WINDOWS
            if f"{m}_{w}" in df_nat.columns]
    ].mean().reset_index()

    # natural の 5 source の平均 (per path × col)
    nat_avg_path = df_nat.groupby("relation_path_type")[
        [f"{m}_{w}" for m in DELTA_METRICS for w in WINDOWS
            if f"{m}_{w}" in df_nat.columns]
    ].mean().reset_index()

    # A1 と C2 の delta 値 (sensitivity_evaluator から逆算)
    sens_t = df_sens[df_sens["comparison"] == "timing"]
    sens_t_avg = sens_t.groupby(["relation_path_type", "metric", "observation_window"])[
        ["mean_a", "mean_b"]
    ].mean().reset_index()  # mean_a = A1, mean_b = C2

    rows = []
    for _, r in sens_t_avg.iterrows():
        path = r["relation_path_type"]
        metric = r["metric"]
        win = r["observation_window"]
        col = f"{metric}_{win}"
        if path not in nat_avg_path["relation_path_type"].values:
            continue
        if col not in nat_avg_path.columns:
            continue
        nat_v = float(nat_avg_path[nat_avg_path["relation_path_type"] == path][col].iloc[0])
        a1_v = float(r["mean_a"])
        c2_v = float(r["mean_b"])
        ratio_a1 = a1_v / nat_v if nat_v != 0 else float("nan")
        ratio_c2 = c2_v / nat_v if nat_v != 0 else float("nan")
        a1_dist = abs(a1_v - nat_v)
        c2_dist = abs(c2_v - nat_v)
        rows.append({
            "relation_path_type": path,
            "metric": metric,
            "observation_window": win,
            "natural_mean": nat_v,
            "A1_mean": a1_v,
            "C2_mean": c2_v,
            "ratio_A1_over_natural": ratio_a1,
            "ratio_C2_over_natural": ratio_c2,
            "A1_distance_from_natural": a1_dist,
            "C2_distance_from_natural": c2_dist,
            "C2_closer_to_natural": bool(c2_dist < a1_dist),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Level 1-3.5 reports
# ----------------------------------------------------------------------
def build_level_1_mechanism(df_sens: pd.DataFrame, df_bim: pd.DataFrame) -> dict:
    """機構動作確認."""
    return {
        "n_seeds": int(df_sens["seed"].nunique()),
        "n_conditions": int(df_sens["cond_b"].nunique()),
        "n_sensitivity_rows": int(len(df_sens)),
        "n_bimodal_cells": int(len(df_bim)),
        "n_genuine_bimodal": int((df_bim["subtype"] == "genuine_bimodal").sum()),
        "n_sparse_outlier": int((df_bim["subtype"] == "sparse_outlier").sum()),
        "all_24_seeds_covered": int(df_sens["seed"].nunique()) == 24,
        "all_3_conditions_covered": int(df_sens["cond_b"].nunique()) == 3,
        "expected_sens_rows_per_seed": 540,
        "actual_sens_rows_per_seed_min": int(df_sens.groupby("seed").size().min()),
        "actual_sens_rows_per_seed_max": int(df_sens.groupby("seed").size().max()),
        "all_seeds_complete": bool(df_sens.groupby("seed").size().min() == 540),
    }


def build_level_2_condition_diff(df_sens: pd.DataFrame) -> pd.DataFrame:
    """条件差確認 (per comparison × metric)."""
    rows = []
    for cmp in df_sens["comparison"].unique():
        sub = df_sens[df_sens["comparison"] == cmp]
        for metric in DELTA_METRICS:
            ms = sub[sub["metric"] == metric]
            if ms.empty:
                continue
            rows.append({
                "comparison": cmp,
                "metric": metric,
                "n_records": int(len(ms)),
                "cohens_d_abs_mean": float(ms["cohens_d"].abs().mean()),
                "cohens_d_max_abs": float(ms["cohens_d"].abs().max()),
                "delta_mean_avg": float(ms["delta_mean"].mean()),
            })
    return pd.DataFrame(rows)


def build_level_3_sensitivity(df_sens: pd.DataFrame) -> pd.DataFrame:
    """寄与候補感度評価のサマリ."""
    rows = []
    for cmp in df_sens["comparison"].unique():
        sub = df_sens[df_sens["comparison"] == cmp]
        all_d = sub["cohens_d"].values
        rows.append({
            "comparison": cmp,
            "abs_mean": float(np.abs(all_d).mean()),
            "abs_max": float(np.abs(all_d).max()),
            "n_large_effect (|d|>=0.5)": int((np.abs(all_d) >= 0.5).sum()),
            "n_medium_effect (0.3<=|d|<0.5)": int(((np.abs(all_d) >= 0.3) & (np.abs(all_d) < 0.5)).sum()),
            "n_small_effect (0.1<=|d|<0.3)": int(((np.abs(all_d) >= 0.1) & (np.abs(all_d) < 0.3)).sum()),
            "n_negligible (|d|<0.1)": int((np.abs(all_d) < 0.1).sum()),
            "n_total": int(len(all_d)),
            "evaluable_in_v10_9": cmp != "QC_cost",
            "limit_note": "post-process 計算的減算のみ、実 ledger 不変" if cmp == "QC_cost" else "",
        })
    return pd.DataFrame(rows)


def build_level_3_5_structural_integration(df_bim: pd.DataFrame,
                                                df_sens: pd.DataFrame) -> pd.DataFrame:
    """Level 3.5: 構造 (bimodal) と感度 (timing) の統合解析."""
    gen = df_bim[df_bim["subtype"] == "genuine_bimodal"]
    sens_t = df_sens[(df_sens["comparison"] == "timing")
                          & (df_sens["metric"] == "mean_delta_C")
                          & (df_sens["observation_window"] == "medium")]

    rows = []
    for path in sens_t["relation_path_type"].unique():
        gen_p = gen[gen["relation_path_type"] == path]
        sens_p = sens_t[sens_t["relation_path_type"] == path]
        if gen_p.empty:
            bimodal_dom = "n/a"
            bimodal_dom_pct = 0.0
            n_bimodal = 0
            mean_eff = float("nan")
        else:
            best_counts = gen_p["best_hypothesis"].value_counts()
            bimodal_dom = best_counts.index[0]
            bimodal_dom_pct = float(best_counts.iloc[0] / len(gen_p) * 100)
            n_bimodal = int(len(gen_p))
            mean_eff = float(gen_p["best_effect_size"].mean())
        rows.append({
            "relation_path_type": path,
            "n_bimodal_genuine": n_bimodal,
            "bimodal_dominant_hypothesis": bimodal_dom,
            "bimodal_dominant_pct": bimodal_dom_pct,
            "bimodal_mean_effect_size": mean_eff,
            "timing_sensitivity_mean": float(sens_p["cohens_d"].mean()),
            "timing_sensitivity_std": float(sens_p["cohens_d"].std()),
            "timing_sensitivity_abs_mean": float(sens_p["cohens_d"].abs().mean()),
        })
    df = pd.DataFrame(rows)
    df["structural_consistency_label"] = df.apply(
        lambda r: "consistent" if r["bimodal_dominant_hypothesis"] == "H3_lifecycle"
                                  and abs(r["timing_sensitivity_mean"]) >= 0.05 else
                  "structure_strong_sensitivity_weak"
                                  if r["bimodal_dominant_hypothesis"] == "H3_lifecycle"
                                  and abs(r["timing_sensitivity_mean"]) < 0.05 else
                  "sensitivity_strong_structure_weak"
                                  if abs(r["timing_sensitivity_mean"]) >= 0.15
                                  and r["n_bimodal_genuine"] < 50 else
                  "marginal",
        axis=1,
    )
    return df.sort_values("timing_sensitivity_abs_mean", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["main"], default="main")
    args = ap.parse_args()

    CROSS_SEED.mkdir(parents=True, exist_ok=True)
    print(f"v10.9 design table compiler - mode={args.mode}")
    t0 = time.time()

    df_sens = pd.read_parquet(V109_MAIN / "sensitivity_evaluation_all.parquet")
    df_bim = pd.read_parquet(V109_MAIN / "bimodal_analysis_all.parquet")
    print(f"  loaded: sensitivity={df_sens.shape}, bimodal={df_bim.shape}")

    # 4 種設計表
    print("\n=== Step M-1: 4 種設計表生成 ===")
    df_t1 = build_table_1_sensitivity(df_sens)
    safe_write_parquet_v109(df_t1, CROSS_SEED / "design_table_1_sensitivity.parquet")
    print(f"  Table 1 sensitivity:    {df_t1.shape} -> design_table_1_sensitivity.parquet")

    df_t2 = build_table_2_receptivity(df_bim, df_sens)
    safe_write_parquet_v109(df_t2, CROSS_SEED / "design_table_2_receptivity.parquet")
    print(f"  Table 2 receptivity:    {df_t2.shape} -> design_table_2_receptivity.parquet")

    df_t3 = build_table_3_routing(df_sens)
    safe_write_parquet_v109(df_t3, CROSS_SEED / "design_table_3_routing.parquet")
    print(f"  Table 3 routing:        {df_t3.shape} -> design_table_3_routing.parquet")

    df_t4 = build_table_4_naturalness(df_sens)
    safe_write_parquet_v109(df_t4, CROSS_SEED / "design_table_4_naturalness.parquet")
    print(f"  Table 4 naturalness:    {df_t4.shape} -> design_table_4_naturalness.parquet")

    # 4 階層 reports
    print("\n=== Step M-2: 4 階層 reports ===")
    lv1 = build_level_1_mechanism(df_sens, df_bim)
    with open(CROSS_SEED / "level_1_mechanism_check.json", "w") as f:
        json.dump(lv1, f, indent=2, ensure_ascii=False)
    print(f"  Level 1 mechanism:      keys={list(lv1)} -> level_1_mechanism_check.json")

    lv2 = build_level_2_condition_diff(df_sens)
    safe_write_parquet_v109(lv2, CROSS_SEED / "level_2_condition_diff.parquet")
    print(f"  Level 2 condition diff: {lv2.shape} -> level_2_condition_diff.parquet")

    lv3 = build_level_3_sensitivity(df_sens)
    safe_write_parquet_v109(lv3, CROSS_SEED / "level_3_sensitivity.parquet")
    print(f"  Level 3 sensitivity:    {lv3.shape} -> level_3_sensitivity.parquet")

    lv35 = build_level_3_5_structural_integration(df_bim, df_sens)
    safe_write_parquet_v109(lv35, CROSS_SEED / "level_3_5_structural_integration.parquet")
    print(f"  Level 3.5 structural:   {lv35.shape} -> level_3_5_structural_integration.parquet")

    # Step M-3: 構造的統合 (Level 3.5 と同じ、別名で保存)
    safe_write_parquet_v109(lv35, CROSS_SEED / "structural_integration_path_bimodal_timing.parquet")

    # Step M-4: 留保事項
    print("\n=== Step M-4: 留保事項記録 ===")
    reservations = {
        "v10_9_reservations": [
            {
                "id": 1, "title": "bimodal 解析の手法的限界",
                "summary": "KDE find_peaks で 2 ピーク捕捉できたのは 0 件、全件 median_split 代替",
                "impact": "主結果 (H3_lifecycle 60.2%) の信頼性は維持",
                "v10_10_action": "v10.8 bimodal の真の正体を再評価する素材として残す",
            },
            {
                "id": 2, "title": "QC_cost (Q/C コスト) は v10.9 で評価不能",
                "summary": "A1 vs A2 の cohens_d max=0.05、abs_mean=0.005 で評価不能",
                "impact": "post-process 計算的減算のみで実 ledger 不変、QC_cost は寄与候補としてはノブにならない暫定結論",
                "v10_10_action": "実 simulation 再回しまたは A1 vs A3 比較 (event 有無) を試す",
            },
            {
                "id": 3, "title": "high_fam_out_integ 経路が最強の理由は構造的に未解明",
                "summary": "Step L で timing 感度 0.222 (最強) と判明したが構造的根拠は仮説段階",
                "impact": "v10.9 主結果の中心は維持、解釈は v10.10 に持ち越し",
                "v10_10_action": "Integration 外を主軸にした解析を試す素材として残す",
            },
        ],
    }
    with open(CROSS_SEED / "v109_reservations.json", "w") as f:
        json.dump(reservations, f, indent=2, ensure_ascii=False)
    print(f"  v109_reservations.json saved ({len(reservations['v10_9_reservations'])} items)")

    # 主要結果プリント
    print("\n=== Level 3 sensitivity summary ===")
    print(lv3.to_string(index=False))

    print("\n=== Level 3.5 structural integration (top 5) ===")
    print(lv35.head(5).to_string(index=False))

    print("\n=== Table 3 routing recommendation ===")
    print(df_t3[["relation_path_type", "cohens_d_mean", "abs_mean",
                    "routing_rank", "routing_recommendation"]].to_string(index=False))

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
