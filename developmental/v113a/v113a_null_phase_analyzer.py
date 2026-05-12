#!/usr/bin/env python3
"""v10.13.a Step G: Map 5 (null phase、cell-based 案 X-1).

Web Claude 即決事項 #1, #2 (2026-05-12): null absorption は cell-level で判定.

集計単位: phase × condition × n_core_bin × atom_id
  - n_events_in_cell: 該当 events 数
  - per-cell bootstrap で path 5 種 (atom_related 3 + layer5_structural 2) の CI を算出
  - is_null_cell_candidate の 3 条件:
    1. path 5 種全て CI が 0 を跨ぐ
    2. 24 seeds 中 |delta_C| > 0 の seed が過半数 (12 以上)
    3. n_events_in_cell >= 3

規律:
  - 物理層 frozen + 層 C
  - 神の手回避 (絶対格言 #9): 効果サイズ閾値なし、構造的判定のみ
  - 概念単位を雑に扱わない (絶対格言 #11): atom_related と layer5_structural 分離
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
V112_MAIN = REPO_ROOT / "developmental" / "v112" / "outputs" / "main"
V113A_ROOT = (REPO_ROOT / "developmental" / "v113a").resolve()
V113A_OUT = V113A_ROOT / "outputs" / "main"

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]
PHASES = ["immediate", "short", "mid"]
PHASE_TO_V107_WIN = {"immediate": "immediate", "short": "short", "mid": "medium"}
N_CORE_BINS = ["bin_2", "bin_3_4", "bin_5_plus"]

RELATION_PATHS_ATOM = ["familiarity", "attention_via_salience", "temporal_coactivation"]
RELATION_PATHS_LAYER5 = ["integration_alpha", "integration_beta"]
RELATION_PATHS_NULL = RELATION_PATHS_ATOM + RELATION_PATHS_LAYER5  # 5 paths
EXCESS_REFERENCE = "unrelated_baseline"

# 25 atoms (v108_atom_event_generator から)
TARGET_ATOMS = [
    "BOD.ear", "COG.learn", "COM.silence", "EXS.being", "EXS.nonbeing",
    "FND.timeless", "FND.transformation", "PER.feel", "PER.fragrance", "PER.hear",
    "PER.see", "PER.smell", "PER.sound", "PER.soundless", "PER.taste",
    "PRP.bright", "PRP.deep", "PRP.sharp", "SOC.city", "SOC.nation",
    "SOC.public", "TIM.appear", "WLD.artless", "WLD.culture", "WLD.technique",
]
ATOM_CATEGORY_MAP = {a: a.split(".")[0] for a in TARGET_ATOMS}

BOOTSTRAP_N = 1000
RANDOM_SEED = 13013

NULL_CONDITION_3_MIN_EVENTS = 3
NULL_CONDITION_2_MIN_SEEDS_WITH_SIGNAL = 12


def assert_output_under_v113a(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V113A_ROOT not in abs_path.parents and abs_path != V113A_ROOT:
        raise ValueError(f"Output path {path} not under v113a/")


def safe_write_parquet_v113a(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v113a(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def load_per_event_with_path_excess(seed: int, condition: str,
                                       phase: str) -> pd.DataFrame:
    """per-event の path_excess 5 種 + delta_C + metadata を取得."""
    excess_path = V112_MAIN / f"excess_change_adjusted_{condition}_seed{seed}.parquet"
    profile_path = V112_MAIN / f"propagation_profile_{condition}_seed{seed}.parquet"
    df_excess = pd.read_parquet(excess_path)
    df_profile = pd.read_parquet(profile_path)

    v107_win = PHASE_TO_V107_WIN[phase]
    dc_col = f"mean_delta_C_{v107_win}"

    # 各 event の unrelated_baseline delta_C
    ref_df = df_excess[df_excess["relation_path_type"] == EXCESS_REFERENCE][
        ["event_id", dc_col]
    ].rename(columns={dc_col: "ref_delta_C"})

    # event metadata
    df_meta = df_profile[["event_id", "n_core_bin", "atom_id"]].drop_duplicates("event_id")

    # 各 event について relation paths の delta_C と path_excess を集計
    rp_only = df_excess[df_excess["relation_path_type"].isin(RELATION_PATHS_NULL)][
        ["event_id", "relation_path_type", dc_col]
    ].rename(columns={dc_col: "path_delta_C"})

    # pivot で event × path のテーブルを作成
    pivot = rp_only.pivot_table(
        index="event_id", columns="relation_path_type",
        values="path_delta_C", aggfunc="first"
    )
    pivot = pivot.reset_index()
    pivot = pivot.merge(ref_df, on="event_id", how="left")
    pivot = pivot.merge(df_meta, on="event_id", how="left")

    # delta_C (relation paths mean、null 判定の駆動条件)
    pivot["delta_C_mean_paths"] = pivot[
        [p for p in RELATION_PATHS_NULL if p in pivot.columns]
    ].mean(axis=1)

    # path_excess (各 path - reference)
    for path in RELATION_PATHS_NULL:
        if path in pivot.columns:
            pivot[f"{path}_excess"] = pivot[path] - pivot["ref_delta_C"]
        else:
            pivot[f"{path}_excess"] = np.nan

    pivot["seed"] = seed
    pivot["condition"] = condition
    pivot["phase"] = phase
    return pivot


def compute_cell_stats(cell_df: pd.DataFrame, rng_seed_base: int = RANDOM_SEED) -> dict:
    """cell 単位 (24 seeds 集計済) の bootstrap CI + null 判定.

    Args:
        cell_df: 該当 cell の per-event row (24 seeds 混在)
    """
    n_events = int(len(cell_df))
    if n_events == 0:
        return None

    # path 5 種の CI 算出 (path_excess の bootstrap)
    rng = np.random.default_rng(rng_seed_base + n_events)
    n_paths_with_no_signal = 0
    path_ci_details = {}
    for path in RELATION_PATHS_NULL:
        col = f"{path}_excess"
        if col not in cell_df.columns:
            path_ci_details[path] = {"n": 0, "crosses_zero": True}
            n_paths_with_no_signal += 1
            continue
        vals = cell_df[col].dropna().values
        n_valid = len(vals)
        if n_valid < 2:
            path_ci_details[path] = {"n": n_valid, "crosses_zero": True,
                                        "reason": "n<2"}
            n_paths_with_no_signal += 1
            continue
        # bootstrap CI 95%
        boot = []
        for _ in range(BOOTSTRAP_N):
            sample = rng.choice(vals, size=n_valid, replace=True)
            boot.append(float(sample.mean()))
        boot_arr = np.array(boot)
        ci_lower = float(np.percentile(boot_arr, 2.5))
        ci_upper = float(np.percentile(boot_arr, 97.5))
        crosses = (ci_lower < 0 < ci_upper)
        path_ci_details[path] = {
            "n": int(n_valid),
            "mean": float(vals.mean()),
            "ci_lower": ci_lower, "ci_upper": ci_upper,
            "crosses_zero": crosses,
        }
        if crosses:
            n_paths_with_no_signal += 1

    # 条件 2: 24 seeds 中 |delta_C| > 0 の seed 数
    if "seed" in cell_df.columns and "delta_C_mean_paths" in cell_df.columns:
        per_seed_dc = cell_df.groupby("seed")["delta_C_mean_paths"].mean()
        n_seeds_with_signal = int(np.sum(np.abs(per_seed_dc) > 0))
    else:
        n_seeds_with_signal = 0

    # null cell 判定 (3 条件 全充足)
    cond_1 = (n_paths_with_no_signal == 5)
    cond_2 = (n_seeds_with_signal >= NULL_CONDITION_2_MIN_SEEDS_WITH_SIGNAL)
    cond_3 = (n_events >= NULL_CONDITION_3_MIN_EVENTS)
    is_null = cond_1 and cond_2 and cond_3

    return {
        "n_events_in_cell": n_events,
        "delta_C_cell_mean": float(cell_df["delta_C_mean_paths"].mean()) if "delta_C_mean_paths" in cell_df.columns else float("nan"),
        "delta_C_cell_std": float(cell_df["delta_C_mean_paths"].std(ddof=1)) if len(cell_df) >= 2 else 0.0,
        "n_paths_with_no_signal": n_paths_with_no_signal,
        "n_seeds_with_signal": n_seeds_with_signal,
        "cond_1_all_paths_no_signal": cond_1,
        "cond_2_majority_seeds_signal": cond_2,
        "cond_3_min_events": cond_3,
        "is_null_cell_candidate": is_null,
        "path_ci_details": path_ci_details,
    }


def _load_all_seeds_phase(args):
    condition, phase = args
    dfs = []
    for seed in SEEDS:
        df = load_per_event_with_path_excess(seed, condition, phase)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def main() -> int:
    t0 = time.time()
    print("=" * 72)
    print("v10.13.a Step G: Map 5 (null phase、cell-based 案 X-1)")
    print("=" * 72)

    # phase × condition で 24 seeds データを load
    print(f"\n[load] all seeds × 2 conditions × 3 phases データ取得...")
    jobs = [(c, p) for c in CONDITION_SET for p in PHASES]
    with Pool(processes=6) as pool:
        loaded = pool.map(_load_all_seeds_phase, jobs)
    all_data = {}
    for (c, p), df in zip(jobs, loaded):
        all_data[(c, p)] = df
    print(f"  loaded {sum(len(d) for d in all_data.values())} total event-rows")

    # cell-level 集計: phase × condition × n_core_bin × atom_id
    print(f"\n[map5] cell-level 集計 (phase × condition × n_core_bin × atom_id)")
    rows = []
    for condition in CONDITION_SET:
        for phase in PHASES:
            df = all_data[(condition, phase)]
            for n_core_bin in N_CORE_BINS:
                for atom_id in TARGET_ATOMS:
                    sub = df[(df["n_core_bin"] == n_core_bin) & (df["atom_id"] == atom_id)]
                    if sub.empty:
                        # 空セルも記録 (構造把握用)
                        rows.append({
                            "condition": condition,
                            "phase": phase,
                            "n_core_bin": n_core_bin,
                            "atom_id": atom_id,
                            "atom_category": ATOM_CATEGORY_MAP[atom_id],
                            "n_events_in_cell": 0,
                            "is_null_cell_candidate": False,
                            "reason_empty": True,
                        })
                        continue
                    stats = compute_cell_stats(sub)
                    if stats is None:
                        continue
                    row = {
                        "condition": condition,
                        "phase": phase,
                        "n_core_bin": n_core_bin,
                        "atom_id": atom_id,
                        "atom_category": ATOM_CATEGORY_MAP[atom_id],
                        "n_events_in_cell": stats["n_events_in_cell"],
                        "delta_C_cell_mean": stats["delta_C_cell_mean"],
                        "delta_C_cell_std": stats["delta_C_cell_std"],
                        "n_paths_with_no_signal": stats["n_paths_with_no_signal"],
                        "n_seeds_with_signal": stats["n_seeds_with_signal"],
                        "cond_1_all_paths_no_signal": stats["cond_1_all_paths_no_signal"],
                        "cond_2_majority_seeds_signal": stats["cond_2_majority_seeds_signal"],
                        "cond_3_min_events": stats["cond_3_min_events"],
                        "is_null_cell_candidate": stats["is_null_cell_candidate"],
                        "reason_empty": False,
                    }
                    rows.append(row)

    df_map5 = pd.DataFrame(rows)
    safe_write_parquet_v113a(df_map5, V113A_OUT / "map5_null_phase_per_cell.parquet")

    # サマリ集計
    non_empty = df_map5[df_map5["reason_empty"] == False]
    null_candidates = non_empty[non_empty["is_null_cell_candidate"] == True]
    print(f"\n[summary]")
    print(f"  total cells: {len(df_map5)}")
    print(f"  non-empty cells: {len(non_empty)}")
    print(f"  null cell candidates: {len(null_candidates)}")
    print()
    print(f"[cell counts by (condition × phase × n_core_bin)]")
    counts = non_empty.groupby(["condition", "phase", "n_core_bin"]).size().unstack(fill_value=0)
    print(counts.to_string())
    print()
    print(f"[null candidates by (condition × phase × n_core_bin)]")
    if not null_candidates.empty:
        null_counts = null_candidates.groupby(
            ["condition", "phase", "n_core_bin"]
        ).size().unstack(fill_value=0)
        print(null_counts.to_string())
    else:
        print(f"  (null candidates なし)")
    print()
    print(f"[null candidates by (condition × phase)]")
    if not null_candidates.empty:
        nc_phase = null_candidates.groupby(["condition", "phase"]).size().unstack(fill_value=0)
        print(nc_phase.to_string())

    # 全 cell の null 条件達成内訳
    print(f"\n[non-empty cell の null 条件達成内訳]")
    cond_summary = non_empty.groupby(["condition", "phase"]).agg(
        n_cells=("is_null_cell_candidate", "size"),
        n_cond1_pass=("cond_1_all_paths_no_signal", "sum"),
        n_cond2_pass=("cond_2_majority_seeds_signal", "sum"),
        n_cond3_pass=("cond_3_min_events", "sum"),
        n_all_pass=("is_null_cell_candidate", "sum"),
    )
    print(cond_summary.to_string())

    # サマリ JSON
    summary = {
        "step": "G",
        "method": "cell-based 案 X-1 (Web Claude 即決事項 #1)",
        "cell_unit": "phase × condition × n_core_bin × atom_id",
        "null_conditions": {
            "1_all_paths_no_signal": "5 paths (atom_related 3 + layer5_structural 2) 全て CI 0 を跨ぐ",
            "2_majority_seeds_signal": f"24 seeds 中 |delta_C| > 0 の seed が {NULL_CONDITION_2_MIN_SEEDS_WITH_SIGNAL} 以上",
            "3_min_events": f"n_events_in_cell >= {NULL_CONDITION_3_MIN_EVENTS}",
        },
        "n_total_cells": int(len(df_map5)),
        "n_non_empty_cells": int(len(non_empty)),
        "n_null_candidates": int(len(null_candidates)),
        "bootstrap_n_iter": BOOTSTRAP_N,
        "random_seed_base": RANDOM_SEED,
        "elapsed_sec": round(time.time() - t0, 2),
    }
    with open(V113A_OUT / "step_g_summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - t0
    print(f"\nDONE  elapsed = {elapsed:.2f}s")
    print(f"  output: map5_null_phase_per_cell.parquet, step_g_summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
