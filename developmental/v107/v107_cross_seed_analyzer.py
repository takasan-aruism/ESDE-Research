#!/usr/bin/env python3
"""v10.7 cross-seed analyzer (Step J 用、main run 完了後に実行).

24 seeds の per-seed 出力を統合し、Level 1/2/3 finding を集計。

Level 1 (co-occurrence): |baseline_excess_change| > 1% かつ 24 seeds direction 一貫
Level 2 (path-enriched): mean(target_delta on relation_path)
                          - mean(target_delta on unrelated_baseline) > 1%
                          かつ 24 seeds direction 一貫
Level 3 (source-specific): source 別 path-enriched profile の差
                            (Kruskal-Wallis 検定)

入力: developmental/v107/outputs/main/{name}_seed*.parquet
出力: developmental/v107/outputs/main/cross_seed/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
MAIN_ROOT = V107_ROOT / "outputs" / "main"
CROSS_ROOT = MAIN_ROOT / "cross_seed"

sys.path.insert(0, str(Path(__file__).parent))
from v107_post_process import safe_write_parquet_v107  # noqa: E402

SEEDS = list(range(24))
LEVEL_1_THRESHOLD = 0.01  # 1%
LEVEL_2_THRESHOLD = 0.01  # 1%
DELTA_FIELDS = [
    "mean_delta_R_familiarity_immediate", "mean_delta_R_familiarity_short",
    "mean_delta_R_familiarity_medium",
    "mean_delta_Q_immediate", "mean_delta_Q_short", "mean_delta_Q_medium",
    "mean_delta_C_immediate", "mean_delta_C_short", "mean_delta_C_medium",
    "mean_delta_n_alphas_immediate", "mean_delta_n_alphas_short",
    "mean_delta_n_alphas_medium",
    "mean_delta_n_observed_immediate", "mean_delta_n_observed_short",
    "mean_delta_n_observed_medium",
    "mean_n_pulses_in_window_immediate", "mean_n_pulses_in_window_short",
    "mean_n_pulses_in_window_medium",
]
RELATION_PATHS = [
    "familiarity", "attention_via_salience",
    "integration_alpha", "integration_beta", "temporal_coactivation",
]
BASELINES = [
    "unrelated_baseline", "same_step_random_baseline", "matched_baseline",
    "same_integration_low_familiarity_baseline",
    "high_familiarity_outside_integration_baseline",
]


def load_concat(prefix: str) -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        p = MAIN_ROOT / f"{prefix}_seed{s}.parquet"
        if p.exists():
            dfs.append(pd.read_parquet(p))
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


# ----------------------------------------------------------------------
# Level 1: co-occurrence
# ----------------------------------------------------------------------
def compute_level_1_co_occurrence(df_excess: pd.DataFrame) -> pd.DataFrame:
    """各 (relation_path_type, delta_field) について |mean_delta| > 1%
    かつ 24 seeds direction 一貫を判定."""
    rows = []
    for path, sub in df_excess.groupby("relation_path_type"):
        for field in DELTA_FIELDS:
            if field not in sub.columns:
                continue
            seed_means = sub.groupby("seed")[field].mean()
            overall_mean = float(seed_means.mean())
            if abs(overall_mean) < LEVEL_1_THRESHOLD:
                continue
            n_pos = int((seed_means > 0).sum())
            n_neg = int((seed_means < 0).sum())
            n_zero = int((seed_means == 0).sum())
            n_seeds = int(len(seed_means))
            consistent = (n_pos == n_seeds) or (n_neg == n_seeds)
            rows.append({
                "relation_path_type": path, "delta_field": field,
                "overall_mean": overall_mean,
                "n_seeds": n_seeds, "n_positive": n_pos,
                "n_negative": n_neg, "n_zero": n_zero,
                "direction_consistent_24": consistent,
                "is_level_1_finding": (
                    abs(overall_mean) >= LEVEL_1_THRESHOLD and consistent
                ),
            })
    return pd.DataFrame(rows).sort_values("overall_mean", key=abs, ascending=False)


# ----------------------------------------------------------------------
# Level 2: path-enriched (relation_path - unrelated_baseline)
# ----------------------------------------------------------------------
def compute_level_2_path_enriched(df_excess: pd.DataFrame) -> pd.DataFrame:
    """mean(target_delta on path) - mean(target_delta on unrelated_baseline)
    > 1% を判定."""
    rows = []
    unrelated = df_excess[df_excess["relation_path_type"] == "unrelated_baseline"]
    if unrelated.empty:
        return pd.DataFrame()
    unrelated_seed_means = unrelated.groupby("seed").agg({
        f: "mean" for f in DELTA_FIELDS if f in unrelated.columns
    })
    for path in RELATION_PATHS + ["familiarity_hop2", "familiarity_hop3"]:
        sub = df_excess[df_excess["relation_path_type"] == path]
        if sub.empty:
            continue
        path_seed_means = sub.groupby("seed").agg({
            f: "mean" for f in DELTA_FIELDS if f in sub.columns
        })
        common_seeds = path_seed_means.index.intersection(unrelated_seed_means.index)
        for field in DELTA_FIELDS:
            if field not in path_seed_means.columns:
                continue
            diff_per_seed = (path_seed_means.loc[common_seeds, field]
                              - unrelated_seed_means.loc[common_seeds, field])
            overall_diff = float(diff_per_seed.mean())
            if abs(overall_diff) < LEVEL_2_THRESHOLD:
                continue
            n_pos = int((diff_per_seed > 0).sum())
            n_neg = int((diff_per_seed < 0).sum())
            n_seeds = int(len(diff_per_seed))
            consistent = (n_pos == n_seeds) or (n_neg == n_seeds)
            rows.append({
                "relation_path_type": path, "delta_field": field,
                "path_minus_unrelated": overall_diff,
                "n_seeds_compared": n_seeds,
                "n_positive": n_pos, "n_negative": n_neg,
                "direction_consistent_24": consistent,
                "is_level_2_finding": (
                    abs(overall_diff) >= LEVEL_2_THRESHOLD and consistent
                ),
            })
    return pd.DataFrame(rows).sort_values(
        "path_minus_unrelated", key=abs, ascending=False
    )


# ----------------------------------------------------------------------
# Level 3: source-specific (Kruskal-Wallis)
# ----------------------------------------------------------------------
def compute_level_3_source_specific(df_excess: pd.DataFrame,
                                       df_source_events: pd.DataFrame) -> pd.DataFrame:
    """source_event_type 別の path-enriched profile が異なるか検定."""
    df_with_source = df_excess.merge(
        df_source_events[["event_id", "event_source_type"]],
        on="event_id", how="left",
    )
    rows = []
    for path in RELATION_PATHS:
        sub = df_with_source[df_with_source["relation_path_type"] == path]
        if sub.empty:
            continue
        for field in DELTA_FIELDS:
            if field not in sub.columns:
                continue
            groups = []
            source_types = []
            for src_type, src_sub in sub.groupby("event_source_type"):
                vals = src_sub[field].dropna().values
                if len(vals) >= 5:  # 検定の最低サンプル
                    groups.append(vals)
                    source_types.append(src_type)
            if len(groups) < 2:
                continue
            try:
                stat, pval = kruskal(*groups)
            except ValueError:
                continue
            # 効果サイズ (group 間の delta range)
            group_means = [float(g.mean()) for g in groups]
            effect_size = float(max(group_means) - min(group_means))
            rows.append({
                "relation_path_type": path, "delta_field": field,
                "kruskal_stat": float(stat), "p_value": float(pval),
                "n_groups": len(groups),
                "source_types": ",".join(source_types),
                "max_group_mean": float(max(group_means)),
                "min_group_mean": float(min(group_means)),
                "effect_size_max_minus_min": effect_size,
                "is_level_3_finding": (pval < 0.05 and effect_size >= 0.01),
            })
    return pd.DataFrame(rows).sort_values("p_value")


# ----------------------------------------------------------------------
# Wave pattern + decay summary
# ----------------------------------------------------------------------
def compute_wave_pattern_summary(df_wave: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for path, sub in df_wave.groupby("relation_path_type"):
        cls_counts = sub["wave_pattern_class"].value_counts().to_dict()
        peak_lag_mean = float(sub["peak_lag"].mean())
        abs_peak_mean = float(sub["abs_peak_value"].mean())
        rows.append({
            "relation_path_type": path,
            "n_seeds": int(len(sub)),
            "peak_lag_mean": peak_lag_mean,
            "peak_lag_std": float(sub["peak_lag"].std(ddof=0)),
            "abs_peak_mean": abs_peak_mean,
            "wave_class_distribution": str(cls_counts),
            "dominant_class": max(cls_counts.items(), key=lambda x: x[1])[0],
        })
    return pd.DataFrame(rows)


def compute_resonance_loop_summary(df_loops: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (loop_type), sub in df_loops.groupby("loop_type"):
        rows.append({
            "loop_type": loop_type,
            "n_loops_total_24seeds": int(len(sub)),
            "mean_loops_per_seed": float(len(sub) / 24),
            "mean_min_strength": float(sub["min_strength"].mean()),
            "max_min_strength": float(sub["min_strength"].max()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print("v10.7 cross-seed analyzer (Level 1/2/3 + summaries)")
    CROSS_ROOT.mkdir(parents=True, exist_ok=True)

    df_excess = load_concat("excess_change")
    df_src = load_concat("source_events")
    df_wave = load_concat("wave_patterns")
    df_loops = load_concat("resonance_loops")
    df_decay = load_concat("decay_rate")

    print(f"  excess_change rows (24 seeds): {len(df_excess):,}")
    print(f"  source_events rows: {len(df_src):,}")
    print(f"  wave_patterns rows: {len(df_wave):,}")
    print(f"  resonance_loops rows: {len(df_loops):,}")

    df_l1 = compute_level_1_co_occurrence(df_excess)
    safe_write_parquet_v107(df_l1, CROSS_ROOT / "level_1_co_occurrence.parquet")
    print(f"  Level 1 candidates: {len(df_l1):,} "
          f"(findings={int(df_l1['is_level_1_finding'].sum() if not df_l1.empty else 0)})")

    df_l2 = compute_level_2_path_enriched(df_excess)
    safe_write_parquet_v107(df_l2, CROSS_ROOT / "level_2_path_enriched.parquet")
    print(f"  Level 2 candidates: {len(df_l2):,} "
          f"(findings={int(df_l2['is_level_2_finding'].sum() if not df_l2.empty else 0)})")

    df_l3 = compute_level_3_source_specific(df_excess, df_src)
    safe_write_parquet_v107(df_l3, CROSS_ROOT / "level_3_source_specific.parquet")
    print(f"  Level 3 candidates: {len(df_l3):,} "
          f"(findings={int(df_l3['is_level_3_finding'].sum() if not df_l3.empty else 0)})")

    df_wave_sum = compute_wave_pattern_summary(df_wave)
    safe_write_parquet_v107(df_wave_sum, CROSS_ROOT / "wave_pattern_summary.parquet")
    df_loops_sum = compute_resonance_loop_summary(df_loops)
    safe_write_parquet_v107(df_loops_sum,
                              CROSS_ROOT / "resonance_loop_summary.parquet")

    print(f"\nDONE  output = {CROSS_ROOT}")


if __name__ == "__main__":
    main()
