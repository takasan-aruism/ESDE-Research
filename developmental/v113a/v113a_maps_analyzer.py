#!/usr/bin/env python3
"""v10.13.a Step C-F: Map 1-4 統合実装.

5 phase (immediate/short/mid、long は Step H 別) × 各軸で集計:
- Map 1: phase × n_core_bin
- Map 2: phase × relation_path × path_category (atom_related/layer5_structural/baseline)
- Map 3: phase × formation_relation
- Map 4: phase × event 種別 (v107 source_events join)

主入力 (Web Claude 即決事項 #3):
- excess_change_adjusted_*.parquet (3 window 完全保持)
- propagation_profile_*.parquet (metadata = n_core_bin/formation_relation/atom_id merge)
- v107 source_events_*.parquet (Map 4 で event_id → event_source_type join)

規律:
- 物理層 frozen: 既存出力 read-only、書き込み v113a/ 配下のみ
- n_core 別層化 default (絶対格言 #4)
- path_category 分離 (絶対格言 #11)
- judgment 回避 (絶対格言 #12)
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_MAIN = REPO_ROOT / "developmental" / "v107" / "outputs" / "main"
V112_MAIN = REPO_ROOT / "developmental" / "v112" / "outputs" / "main"
V113A_ROOT = (REPO_ROOT / "developmental" / "v113a").resolve()
V113A_OUT = V113A_ROOT / "outputs" / "main"

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]
PHASES = ["immediate", "short", "mid"]  # v107 WINDOW_DEFS (mid = medium 改名)
PHASE_TO_V107_WIN = {"immediate": "immediate", "short": "short", "mid": "medium"}

RELATION_PATHS_ATOM = ["familiarity", "attention_via_salience", "temporal_coactivation"]
RELATION_PATHS_LAYER5 = ["integration_alpha", "integration_beta"]
RELATION_PATHS_ALL = RELATION_PATHS_ATOM + RELATION_PATHS_LAYER5
BASELINES = [
    "unrelated_baseline", "same_step_random_baseline", "matched_baseline",
    "same_integration_low_familiarity_baseline",
    "high_familiarity_outside_integration_baseline",
]

PATH_CATEGORY_MAP = {p: "atom_related" for p in RELATION_PATHS_ATOM}
PATH_CATEGORY_MAP.update({p: "layer5_structural" for p in RELATION_PATHS_LAYER5})
PATH_CATEGORY_MAP.update({b: "baseline" for b in BASELINES})

EXCESS_REFERENCE = "unrelated_baseline"

N_CORE_BINS = ["bin_2", "bin_3_4", "bin_5_plus"]
FORMATION_RELATIONS = ["before", "during", "after", "no_alpha"]


def assert_output_under_v113a(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V113A_ROOT not in abs_path.parents and abs_path != V113A_ROOT:
        raise ValueError(f"Output path {path} not under v113a/")


def safe_write_parquet_v113a(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v113a(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 主データ取得 (excess_change_adjusted + propagation_profile metadata merge)
# ----------------------------------------------------------------------
def load_seed_data(seed: int, condition: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """excess (3 window 含む) + metadata (n_core_bin / formation_relation / atom_id) を取得.

    Returns:
        df_excess: per-(event_id, relation_path_type) の delta 値、3 window
        df_meta: per-event_id の metadata
    """
    excess_path = V112_MAIN / f"excess_change_adjusted_{condition}_seed{seed}.parquet"
    profile_path = V112_MAIN / f"propagation_profile_{condition}_seed{seed}.parquet"

    df_excess = pd.read_parquet(excess_path)

    # metadata は propagation_profile から取得
    df_profile = pd.read_parquet(profile_path)
    meta_cols = ["event_id", "source_cid", "atom_id", "atom_index",
                 "n_core_bin", "formation_relation", "n_core", "lifespan",
                 "fam_max", "target_step", "death_step"]
    available = [c for c in meta_cols if c in df_profile.columns]
    df_meta = df_profile[available].drop_duplicates("event_id").copy()

    return df_excess, df_meta


def compute_per_event_delta_by_phase(df_excess: pd.DataFrame, phase: str,
                                       paths: list[str] = None) -> pd.DataFrame:
    """per-event の delta (relation_paths の mean) を phase 別に算出.

    Args:
        df_excess: excess_change_adjusted の DataFrame
        phase: "immediate" / "short" / "mid"
        paths: 集計対象 path (default = RELATION_PATHS_ALL の 5 種)

    Returns:
        DataFrame columns: event_id, delta_C_{phase}, delta_Q_{phase}, n_pulses_{phase}
    """
    if paths is None:
        paths = RELATION_PATHS_ALL

    v107_win = PHASE_TO_V107_WIN[phase]
    dc_col = f"mean_delta_C_{v107_win}"
    dq_col = f"mean_delta_Q_{v107_win}"
    np_col = f"mean_n_pulses_in_window_{v107_win}"

    rp_only = df_excess[df_excess["relation_path_type"].isin(paths)]
    grouped = rp_only.groupby("event_id").agg(
        **{
            f"delta_C_{phase}": (dc_col, "mean"),
            f"delta_Q_{phase}": (dq_col, "mean"),
            f"n_pulses_{phase}": (np_col, "mean"),
            "n_paths_present": ("relation_path_type", "nunique"),
        }
    ).reset_index()
    return grouped


# ----------------------------------------------------------------------
# Map 1: phase × n_core_bin
# ----------------------------------------------------------------------
def compute_map1_for_seed(seed: int, condition: str) -> pd.DataFrame:
    """Map 1: phase × n_core_bin の集計 (per seed × condition)."""
    df_excess, df_meta = load_seed_data(seed, condition)
    rows = []
    for phase in PHASES:
        df_pe = compute_per_event_delta_by_phase(df_excess, phase)
        df_pe = df_pe.merge(df_meta, on="event_id", how="left")
        for n_core_bin in N_CORE_BINS:
            sub = df_pe[df_pe["n_core_bin"] == n_core_bin]
            row = {
                "seed": int(seed),
                "condition": condition,
                "phase": phase,
                "n_core_bin": n_core_bin,
                "n_events": int(len(sub)),
                "delta_C_mean": float(sub[f"delta_C_{phase}"].mean()) if not sub.empty else float("nan"),
                "delta_C_std": float(sub[f"delta_C_{phase}"].std(ddof=1)) if len(sub) >= 2 else 0.0,
                "delta_Q_mean": float(sub[f"delta_Q_{phase}"].mean()) if not sub.empty else float("nan"),
                "n_pulses_mean": float(sub[f"n_pulses_{phase}"].mean()) if not sub.empty else float("nan"),
                "n_pulses_std": float(sub[f"n_pulses_{phase}"].std(ddof=1)) if len(sub) >= 2 else 0.0,
            }
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Map 2: phase × relation_path × path_category
# ----------------------------------------------------------------------
def compute_map2_for_seed(seed: int, condition: str) -> pd.DataFrame:
    """Map 2: phase × relation_path × path_category の集計 (per seed × condition).

    path_excess = path delta_C - unrelated_baseline delta_C
    """
    df_excess, df_meta = load_seed_data(seed, condition)
    rows = []
    for phase in PHASES:
        v107_win = PHASE_TO_V107_WIN[phase]
        dc_col = f"mean_delta_C_{v107_win}"

        # 各 event の unrelated_baseline delta_C を取得
        ref_df = df_excess[df_excess["relation_path_type"] == EXCESS_REFERENCE][
            ["event_id", dc_col]
        ].rename(columns={dc_col: "ref_delta_C"})

        # 各 path について path_excess を算出
        for path in RELATION_PATHS_ALL:
            path_df = df_excess[df_excess["relation_path_type"] == path][
                ["event_id", dc_col]
            ].rename(columns={dc_col: "path_delta_C"})
            merged = path_df.merge(ref_df, on="event_id", how="inner")
            merged["path_excess"] = merged["path_delta_C"] - merged["ref_delta_C"]

            n_events = int(len(merged))
            if n_events > 0:
                mean = float(merged["path_excess"].mean())
                std = float(merged["path_excess"].std(ddof=1)) if n_events >= 2 else 0.0
                mean_path = float(merged["path_delta_C"].mean())
            else:
                mean = std = mean_path = float("nan")

            rows.append({
                "seed": int(seed),
                "condition": condition,
                "phase": phase,
                "path_category": PATH_CATEGORY_MAP.get(path, "unknown"),
                "path_name": path,
                "n_events": n_events,
                "path_excess_mean": mean,
                "path_excess_std": std,
                "path_delta_C_mean": mean_path,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Map 3: phase × formation_relation
# ----------------------------------------------------------------------
def compute_map3_for_seed(seed: int, condition: str) -> pd.DataFrame:
    """Map 3: phase × formation_relation の集計 (per seed × condition)."""
    df_excess, df_meta = load_seed_data(seed, condition)
    rows = []
    for phase in PHASES:
        df_pe = compute_per_event_delta_by_phase(df_excess, phase)
        df_pe = df_pe.merge(df_meta, on="event_id", how="left")
        for fr in FORMATION_RELATIONS:
            sub = df_pe[df_pe["formation_relation"] == fr]
            row = {
                "seed": int(seed),
                "condition": condition,
                "phase": phase,
                "formation_relation": fr,
                "n_events": int(len(sub)),
                "delta_C_mean": float(sub[f"delta_C_{phase}"].mean()) if not sub.empty else float("nan"),
                "delta_C_std": float(sub[f"delta_C_{phase}"].std(ddof=1)) if len(sub) >= 2 else 0.0,
                "n_pulses_mean": float(sub[f"n_pulses_{phase}"].mean()) if not sub.empty else float("nan"),
                "n_pulses_std": float(sub[f"n_pulses_{phase}"].std(ddof=1)) if len(sub) >= 2 else 0.0,
            }
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Map 4: phase × event 種別 (v107 source_events join + v10.12 atom_introduction)
# ----------------------------------------------------------------------
def compute_map4_for_seed(seed: int) -> pd.DataFrame:
    """Map 4: phase × event 種別 の集計.

    v107 5 種 (pulse / ingestion / alpha_formation / beta_formation / c_conversion)
    + v10.12 atom_introduction_event (v112 / v108_standard)
    """
    rows = []
    # v107 natural source_event 5 種
    src_path = V107_MAIN / f"source_events_seed{seed}.parquet"
    excess_path = V107_MAIN / f"excess_change_seed{seed}.parquet"
    df_src = pd.read_parquet(src_path)
    df_excess = pd.read_parquet(excess_path)
    type_map = df_src[["event_id", "event_source_type"]].drop_duplicates("event_id")
    df_excess_typed = df_excess.merge(type_map, on="event_id", how="left")

    for phase in PHASES:
        v107_win = PHASE_TO_V107_WIN[phase]
        dc_col = f"mean_delta_C_{v107_win}"
        np_col = f"mean_n_pulses_in_window_{v107_win}"

        rp_only = df_excess_typed[df_excess_typed["relation_path_type"].isin(RELATION_PATHS_ALL)]
        for event_type in rp_only["event_source_type"].dropna().unique():
            sub = rp_only[rp_only["event_source_type"] == event_type]
            # per event_id で path mean
            per_ev = sub.groupby("event_id").agg(
                delta_C=(dc_col, "mean"),
                n_pulses=(np_col, "mean"),
            ).reset_index()
            rows.append({
                "seed": int(seed),
                "condition": "v107_natural",
                "phase": phase,
                "event_source_type": event_type,
                "n_events": int(len(per_ev)),
                "delta_C_mean": float(per_ev["delta_C"].mean()) if not per_ev.empty else float("nan"),
                "delta_C_std": float(per_ev["delta_C"].std(ddof=1)) if len(per_ev) >= 2 else 0.0,
                "n_pulses_mean": float(per_ev["n_pulses"].mean()) if not per_ev.empty else float("nan"),
            })

    # v10.12 atom_introduction_event (v112 + v108_standard)
    for condition in CONDITION_SET:
        df_excess_v112, _ = load_seed_data(seed, condition)
        for phase in PHASES:
            v107_win = PHASE_TO_V107_WIN[phase]
            dc_col = f"mean_delta_C_{v107_win}"
            np_col = f"mean_n_pulses_in_window_{v107_win}"
            rp_only = df_excess_v112[df_excess_v112["relation_path_type"].isin(RELATION_PATHS_ALL)]
            per_ev = rp_only.groupby("event_id").agg(
                delta_C=(dc_col, "mean"),
                n_pulses=(np_col, "mean"),
            ).reset_index()
            rows.append({
                "seed": int(seed),
                "condition": condition,
                "phase": phase,
                "event_source_type": "atom_introduction_event",
                "n_events": int(len(per_ev)),
                "delta_C_mean": float(per_ev["delta_C"].mean()) if not per_ev.empty else float("nan"),
                "delta_C_std": float(per_ev["delta_C"].std(ddof=1)) if len(per_ev) >= 2 else 0.0,
                "n_pulses_mean": float(per_ev["n_pulses"].mean()) if not per_ev.empty else float("nan"),
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# cross-seed 集計 (24 seeds 統合、paired_d 算出)
# ----------------------------------------------------------------------
def cross_seed_paired_d(df: pd.DataFrame, group_cols: list[str],
                          metric: str, condition_pair=("v112", "v108_standard")) -> pd.DataFrame:
    """24 seeds で paired_d 算出 (cell-level).

    Args:
        df: per-seed × per-cell の集計値 (列に condition / seed / group_cols / metric)
        group_cols: 集計セル列 (e.g. ["phase", "n_core_bin"])
        metric: 集計対象 metric 列名 (e.g. "delta_C_mean")
    """
    cond_a, cond_b = condition_pair
    rows = []
    # group_cols でユニークセル取得 (condition と seed を除く)
    cell_keys = df[group_cols].drop_duplicates().to_dict(orient="records")
    for cell in cell_keys:
        sub_a = df[(df["condition"] == cond_a)].copy()
        sub_b = df[(df["condition"] == cond_b)].copy()
        for k, v in cell.items():
            sub_a = sub_a[sub_a[k] == v]
            sub_b = sub_b[sub_b[k] == v]
        sub_a = sub_a.set_index("seed")[metric]
        sub_b = sub_b.set_index("seed")[metric]
        common = sub_a.index.intersection(sub_b.index)
        if len(common) < 2:
            continue
        diff = (sub_a.loc[common] - sub_b.loc[common]).dropna()
        if len(diff) < 2:
            continue
        mean_d = float(diff.mean())
        std_d = float(diff.std(ddof=1))
        paired_d = mean_d / std_d if std_d > 0 else float("nan")
        n_pos = int(np.sum(diff > 0))
        n_neg = int(np.sum(diff < 0))

        # bootstrap CI
        rng = np.random.default_rng(13013)
        boot = []
        for _ in range(1000):
            sample = rng.choice(diff.values, size=len(diff), replace=True)
            boot.append(float(sample.mean()))
        boot_arr = np.array(boot)
        ci_lower = float(np.percentile(boot_arr, 2.5))
        ci_upper = float(np.percentile(boot_arr, 97.5))

        row = {**cell, "metric": metric,
               "paired_diff_mean": mean_d, "paired_diff_std": std_d,
               "paired_d": paired_d, "n_seeds": int(len(diff)),
               "n_positive": n_pos, "n_negative": n_neg,
               "ci_lower": ci_lower, "ci_upper": ci_upper,
               "crosses_zero": (ci_lower < 0 < ci_upper)}
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def _worker_seed(args):
    seed, condition, map_id = args
    if map_id == "map1":
        return compute_map1_for_seed(seed, condition)
    if map_id == "map2":
        return compute_map2_for_seed(seed, condition)
    if map_id == "map3":
        return compute_map3_for_seed(seed, condition)
    raise ValueError(f"Unknown map_id: {map_id}")


def _worker_map4(seed):
    return compute_map4_for_seed(seed)


def main() -> int:
    t0 = time.time()
    print("=" * 72)
    print("v10.13.a Step C-F: Map 1-4 統合実装 (3 phase: immediate/short/mid)")
    print("=" * 72)

    # Map 1: phase × n_core_bin
    print(f"\n=== Map 1: phase × n_core_bin (24 seeds × 2 conditions) ===")
    t1 = time.time()
    jobs = [(s, c, "map1") for s in SEEDS for c in CONDITION_SET]
    with Pool(processes=12) as pool:
        results = pool.map(_worker_seed, jobs)
    map1 = pd.concat(results, ignore_index=True)
    safe_write_parquet_v113a(map1, V113A_OUT / "map1_phase_x_ncore_per_seed.parquet")
    print(f"  per-seed rows: {len(map1)}, elapsed: {time.time()-t1:.2f}s")

    # cross-seed paired_d (Map 1)
    map1_cs = cross_seed_paired_d(map1, ["phase", "n_core_bin"], "delta_C_mean")
    safe_write_parquet_v113a(map1_cs, V113A_OUT / "map1_phase_x_ncore_cross_seed.parquet")
    print(f"  cross-seed (delta_C): {len(map1_cs)} cells")
    map1_cs_np = cross_seed_paired_d(map1, ["phase", "n_core_bin"], "n_pulses_mean")
    safe_write_parquet_v113a(map1_cs_np, V113A_OUT / "map1_phase_x_ncore_cross_seed_npulses.parquet")
    print(f"  cross-seed (n_pulses): {len(map1_cs_np)} cells")

    # Map 2: phase × relation_path × path_category
    print(f"\n=== Map 2: phase × relation_path × path_category ===")
    t2 = time.time()
    jobs = [(s, c, "map2") for s in SEEDS for c in CONDITION_SET]
    with Pool(processes=12) as pool:
        results = pool.map(_worker_seed, jobs)
    map2 = pd.concat(results, ignore_index=True)
    safe_write_parquet_v113a(map2, V113A_OUT / "map2_phase_x_path_per_seed.parquet")
    print(f"  per-seed rows: {len(map2)}, elapsed: {time.time()-t2:.2f}s")

    map2_cs = cross_seed_paired_d(map2, ["phase", "path_category", "path_name"],
                                     "path_excess_mean")
    safe_write_parquet_v113a(map2_cs, V113A_OUT / "map2_phase_x_path_cross_seed.parquet")
    print(f"  cross-seed (path_excess): {len(map2_cs)} cells")

    # Map 3: phase × formation_relation
    print(f"\n=== Map 3: phase × formation_relation ===")
    t3 = time.time()
    jobs = [(s, c, "map3") for s in SEEDS for c in CONDITION_SET]
    with Pool(processes=12) as pool:
        results = pool.map(_worker_seed, jobs)
    map3 = pd.concat(results, ignore_index=True)
    safe_write_parquet_v113a(map3, V113A_OUT / "map3_phase_x_formation_per_seed.parquet")
    print(f"  per-seed rows: {len(map3)}, elapsed: {time.time()-t3:.2f}s")

    map3_cs = cross_seed_paired_d(map3, ["phase", "formation_relation"], "delta_C_mean")
    safe_write_parquet_v113a(map3_cs, V113A_OUT / "map3_phase_x_formation_cross_seed.parquet")
    print(f"  cross-seed (delta_C): {len(map3_cs)} cells")

    # Map 4: phase × event 種別 (v107 natural + v10.12 atom)
    print(f"\n=== Map 4: phase × event 種別 (v107 natural + v10.12 atom) ===")
    t4 = time.time()
    with Pool(processes=12) as pool:
        results = pool.map(_worker_map4, SEEDS)
    map4 = pd.concat(results, ignore_index=True)
    safe_write_parquet_v113a(map4, V113A_OUT / "map4_phase_x_event_per_seed.parquet")
    print(f"  per-seed rows: {len(map4)}, elapsed: {time.time()-t4:.2f}s")

    # cross-seed for Map 4: condition / event_source_type 別の per-seed mean
    map4_cs_rows = []
    for phase in PHASES:
        for cond in map4["condition"].unique():
            for ev_type in map4["event_source_type"].unique():
                sub = map4[(map4["phase"] == phase) &
                           (map4["condition"] == cond) &
                           (map4["event_source_type"] == ev_type)]
                if sub.empty:
                    continue
                vals = sub["delta_C_mean"].dropna()
                if len(vals) < 2:
                    continue
                map4_cs_rows.append({
                    "phase": phase,
                    "condition": cond,
                    "event_source_type": ev_type,
                    "n_seeds": int(len(vals)),
                    "delta_C_mean_cross_seed": float(vals.mean()),
                    "delta_C_std_cross_seed": float(vals.std(ddof=1)),
                    "total_n_events": int(sub["n_events"].sum()),
                })
    map4_cs = pd.DataFrame(map4_cs_rows)
    safe_write_parquet_v113a(map4_cs, V113A_OUT / "map4_phase_x_event_cross_seed.parquet")
    print(f"  cross-seed: {len(map4_cs)} cells")

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s")
    print(f"  output = {V113A_OUT}")

    # サマリ JSON
    summary = {
        "step": "C-F",
        "phases": PHASES,
        "n_seeds": len(SEEDS),
        "conditions": CONDITION_SET,
        "elapsed_sec": round(elapsed, 2),
        "map1_n_cells": int(len(map1_cs)),
        "map2_n_cells": int(len(map2_cs)),
        "map3_n_cells": int(len(map3_cs)),
        "map4_n_cells": int(len(map4_cs)),
    }
    with open(V113A_OUT / "step_cf_summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
