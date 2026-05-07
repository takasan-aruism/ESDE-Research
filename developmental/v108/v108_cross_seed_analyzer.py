#!/usr/bin/env python3
"""v10.8 cross-seed analyzer (Step J).

Level 1/2/3 + Level 3.5 (introduced vs natural) + 副次観察集計を実施。

入力: developmental/v108/outputs/main/{name}_seed*.parquet
出力: developmental/v108/outputs/main/cross_seed/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
MAIN_ROOT = V108_ROOT / "outputs" / "main"
CROSS_ROOT = MAIN_ROOT / "cross_seed"

SEEDS = list(range(24))
LEVEL_1_THRESHOLD = 0.01
LEVEL_2_THRESHOLD = 0.01
LEVEL_3_5_THRESHOLD = 0.01
WLD_RESERVED = "WLD.artless"

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


def load_concat(prefix: str) -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        p = MAIN_ROOT / f"{prefix}_seed{s}.parquet"
        if p.exists():
            dfs.append(pd.read_parquet(p))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def safe_write_parquet(df: pd.DataFrame, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 各 (event_id) に source_event_type と atom_id をマッピング
# ----------------------------------------------------------------------
def merge_event_metadata(df_excess: pd.DataFrame,
                            df_src: pd.DataFrame) -> pd.DataFrame:
    meta = df_src[["event_id", "event_source_type", "atom_id",
                     "reserved_label"]].drop_duplicates("event_id")
    return df_excess.merge(meta, on="event_id", how="left")


# ----------------------------------------------------------------------
# Level 1: atom co-occurrence (atom_introduction_event 後の変化)
# ----------------------------------------------------------------------
def compute_level_1_atom(df_excess_with_meta: pd.DataFrame) -> pd.DataFrame:
    df_atom = df_excess_with_meta[
        df_excess_with_meta["event_source_type"] == "atom_introduction_event"
    ]
    rows = []
    for (atom_id, path), sub in df_atom.groupby(["atom_id", "relation_path_type"]):
        if path not in RELATION_PATHS:
            continue
        for field in DELTA_FIELDS:
            if field not in sub.columns:
                continue
            seed_means = sub.groupby("seed")[field].mean()
            overall_mean = float(seed_means.mean())
            if abs(overall_mean) < LEVEL_1_THRESHOLD:
                continue
            n_pos = int((seed_means > 0).sum())
            n_neg = int((seed_means < 0).sum())
            n_seeds = int(len(seed_means))
            consistent = (n_pos == n_seeds) or (n_neg == n_seeds)
            reserved_label = ("wld_artless_pending" if atom_id == WLD_RESERVED else "")
            rows.append({
                "atom_id": atom_id, "relation_path_type": path,
                "delta_field": field, "overall_mean": overall_mean,
                "n_seeds": n_seeds, "n_positive": n_pos, "n_negative": n_neg,
                "direction_consistent_24": consistent,
                "is_level_1_finding": (
                    abs(overall_mean) >= LEVEL_1_THRESHOLD and consistent
                    and atom_id != WLD_RESERVED
                ),
                "reserved_label": reserved_label,
            })
    return pd.DataFrame(rows).sort_values("overall_mean", key=abs, ascending=False)


# ----------------------------------------------------------------------
# Level 2: atom path-enriched (vs unrelated_baseline)
# ----------------------------------------------------------------------
def compute_level_2_atom(df_excess_with_meta: pd.DataFrame) -> pd.DataFrame:
    df_atom = df_excess_with_meta[
        df_excess_with_meta["event_source_type"] == "atom_introduction_event"
    ]
    df_unrelated = df_atom[df_atom["relation_path_type"] == "unrelated_baseline"]
    if df_unrelated.empty:
        return pd.DataFrame()
    unrelated_means = df_unrelated.groupby(["atom_id", "seed"]).agg(
        {f: "mean" for f in DELTA_FIELDS if f in df_unrelated.columns}
    )

    rows = []
    for path in RELATION_PATHS:
        sub = df_atom[df_atom["relation_path_type"] == path]
        if sub.empty:
            continue
        path_means = sub.groupby(["atom_id", "seed"]).agg(
            {f: "mean" for f in DELTA_FIELDS if f in sub.columns}
        )
        for atom_id in sub["atom_id"].dropna().unique():
            if atom_id not in unrelated_means.index.get_level_values(0):
                continue
            for field in DELTA_FIELDS:
                if field not in path_means.columns:
                    continue
                try:
                    p_seeds = path_means.loc[atom_id, field]
                    u_seeds = unrelated_means.loc[atom_id, field]
                except KeyError:
                    continue
                common = p_seeds.index.intersection(u_seeds.index)
                if len(common) == 0:
                    continue
                diff = p_seeds.loc[common] - u_seeds.loc[common]
                overall_diff = float(diff.mean())
                if abs(overall_diff) < LEVEL_2_THRESHOLD:
                    continue
                n_pos = int((diff > 0).sum())
                n_neg = int((diff < 0).sum())
                consistent = (n_pos == len(common)) or (n_neg == len(common))
                reserved_label = ("wld_artless_pending" if atom_id == WLD_RESERVED else "")
                rows.append({
                    "atom_id": atom_id, "relation_path_type": path,
                    "delta_field": field,
                    "path_minus_unrelated": overall_diff,
                    "n_seeds_compared": int(len(common)),
                    "n_positive": n_pos, "n_negative": n_neg,
                    "direction_consistent_24": consistent,
                    "is_level_2_finding": (
                        abs(overall_diff) >= LEVEL_2_THRESHOLD and consistent
                        and atom_id != WLD_RESERVED
                    ),
                    "reserved_label": reserved_label,
                })
    return pd.DataFrame(rows).sort_values(
        "path_minus_unrelated", key=abs, ascending=False
    )


# ----------------------------------------------------------------------
# Level 3: atom source-specific (25 atom 間で systematic な差)
# ----------------------------------------------------------------------
def compute_level_3_atom(df_excess_with_meta: pd.DataFrame) -> pd.DataFrame:
    df_atom = df_excess_with_meta[
        df_excess_with_meta["event_source_type"] == "atom_introduction_event"
    ]
    rows = []
    for path in RELATION_PATHS:
        sub = df_atom[df_atom["relation_path_type"] == path]
        if sub.empty:
            continue
        for field in DELTA_FIELDS:
            if field not in sub.columns:
                continue
            groups = []
            atoms = []
            for atom_id, atom_sub in sub.groupby("atom_id"):
                if atom_id == WLD_RESERVED:
                    continue
                vals = atom_sub[field].dropna().values
                if len(vals) >= 5:
                    groups.append(vals)
                    atoms.append(atom_id)
            if len(groups) < 2:
                continue
            try:
                stat, pval = kruskal(*groups)
            except ValueError:
                continue
            group_means = [float(g.mean()) for g in groups]
            effect_size = float(max(group_means) - min(group_means))
            rows.append({
                "relation_path_type": path, "delta_field": field,
                "kruskal_stat": float(stat), "p_value": float(pval),
                "n_atoms": len(groups),
                "max_atom_mean": float(max(group_means)),
                "min_atom_mean": float(min(group_means)),
                "effect_size": effect_size,
                "is_level_3_finding": (pval < 0.05 and effect_size >= 0.01),
            })
    return pd.DataFrame(rows).sort_values("p_value")


# ----------------------------------------------------------------------
# Level 3.5: introduced (atom) vs natural (5 種 source) profile diff
# ----------------------------------------------------------------------
def compute_level_3_5_introduced_vs_natural(df_excess_with_meta: pd.DataFrame) -> pd.DataFrame:
    df_atom = df_excess_with_meta[
        df_excess_with_meta["event_source_type"] == "atom_introduction_event"
    ]
    df_natural = df_excess_with_meta[
        df_excess_with_meta["event_source_type"].isin(
            ["pulse", "ingestion", "alpha_formation", "beta_formation",
             "c_conversion"]
        )
    ]
    rows = []
    for path in RELATION_PATHS:
        atom_sub = df_atom[df_atom["relation_path_type"] == path]
        nat_sub = df_natural[df_natural["relation_path_type"] == path]
        if atom_sub.empty or nat_sub.empty:
            continue
        for field in DELTA_FIELDS:
            if field not in atom_sub.columns:
                continue
            atom_seed_mean = atom_sub.groupby("seed")[field].mean()
            nat_seed_mean = nat_sub.groupby("seed")[field].mean()
            common = atom_seed_mean.index.intersection(nat_seed_mean.index)
            if len(common) == 0:
                continue
            diff = atom_seed_mean.loc[common] - nat_seed_mean.loc[common]
            overall_diff = float(diff.mean())
            if abs(overall_diff) < LEVEL_3_5_THRESHOLD:
                continue
            n_pos = int((diff > 0).sum())
            n_neg = int((diff < 0).sum())
            consistent = (n_pos == len(common)) or (n_neg == len(common))
            rows.append({
                "relation_path_type": path, "delta_field": field,
                "atom_mean": float(atom_seed_mean.loc[common].mean()),
                "natural_mean": float(nat_seed_mean.loc[common].mean()),
                "introduced_minus_natural": overall_diff,
                "n_seeds": int(len(common)),
                "n_positive": n_pos, "n_negative": n_neg,
                "direction_consistent_24": consistent,
                "is_level_3_5_finding": (
                    abs(overall_diff) >= LEVEL_3_5_THRESHOLD and consistent
                ),
            })
    return pd.DataFrame(rows).sort_values(
        "introduced_minus_natural", key=abs, ascending=False
    )


# ----------------------------------------------------------------------
# 副次観察集計 (24 seeds)
# ----------------------------------------------------------------------
def cross_seed_subsidiary_summary() -> dict:
    out = {}
    df_white = load_concat("whiteout_monitor")
    if not df_white.empty:
        out["whiteout"] = {
            "total_pairs": int(len(df_white)),
            "flagged": int(df_white["whiteout_flag"].sum()),
            "max_corr": float(df_white["correlation_coefficient"].abs().max()),
            "mean_corr": float(df_white["correlation_coefficient"].abs().mean()),
        }
    df_sw = load_concat("smallworld_comparison")
    if not df_sw.empty:
        out["smallworld"] = {
            "n_seeds": int(len(df_sw)),
            "all_maintained": bool(df_sw["maintenance_flag_overall"].all()),
            "v107_loop_2_total": int(df_sw["v107_loop_2_hop"].sum()),
            "v108_loop_2_total": int(df_sw["v108_loop_2_hop"].sum()),
            "v107_loop_3_total": int(df_sw["v107_loop_3_hop"].sum()),
            "v108_loop_3_total": int(df_sw["v108_loop_3_hop"].sum()),
        }
    df_err = load_concat("error_distribution")
    if not df_err.empty:
        out["error_distribution"] = {
            "total_rows": int(len(df_err)),
            "shape_counts": df_err["distribution_shape_label"].value_counts().to_dict(),
        }
    return out


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print("v10.8 cross-seed analyzer (Level 1/2/3 + Level 3.5 + 副次観察)")
    CROSS_ROOT.mkdir(parents=True, exist_ok=True)

    df_excess = load_concat("excess_change")
    df_src = load_concat("source_events")
    print(f"  excess_change: {len(df_excess):,}, source_events: {len(df_src):,}")

    df_excess_with_meta = merge_event_metadata(df_excess, df_src)

    df_l1 = compute_level_1_atom(df_excess_with_meta)
    safe_write_parquet(df_l1, CROSS_ROOT / "level_1_atom_co_occurrence.parquet")
    n_l1 = int(df_l1["is_level_1_finding"].sum() if not df_l1.empty else 0)
    print(f"  Level 1 candidates: {len(df_l1):,} (findings={n_l1})")

    df_l2 = compute_level_2_atom(df_excess_with_meta)
    safe_write_parquet(df_l2, CROSS_ROOT / "level_2_atom_path_enriched.parquet")
    n_l2 = int(df_l2["is_level_2_finding"].sum() if not df_l2.empty else 0)
    print(f"  Level 2 candidates: {len(df_l2):,} (findings={n_l2})")

    df_l3 = compute_level_3_atom(df_excess_with_meta)
    safe_write_parquet(df_l3, CROSS_ROOT / "level_3_atom_source_specific.parquet")
    n_l3 = int(df_l3["is_level_3_finding"].sum() if not df_l3.empty else 0)
    print(f"  Level 3 candidates: {len(df_l3):,} (findings={n_l3})")

    df_l3_5 = compute_level_3_5_introduced_vs_natural(df_excess_with_meta)
    safe_write_parquet(df_l3_5, CROSS_ROOT / "level_3_5_introduced_vs_natural.parquet")
    n_l3_5 = int(df_l3_5["is_level_3_5_finding"].sum() if not df_l3_5.empty else 0)
    print(f"  Level 3.5 candidates: {len(df_l3_5):,} (findings={n_l3_5})")

    sub = cross_seed_subsidiary_summary()
    print(f"  副次観察 summary: {sub}")
    import json
    with open(CROSS_ROOT / "subsidiary_summary.json", "w") as f:
        json.dump(sub, f, indent=2, default=str)

    print(f"\nDONE  output = {CROSS_ROOT}")


if __name__ == "__main__":
    main()
