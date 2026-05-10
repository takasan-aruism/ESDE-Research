#!/usr/bin/env python3
"""v10.12 Step E (Part 2): v112_propagation_analyzer.

第 5 版主題 (Atom 取り込み prototype) の per-event 波及プロファイル算出.

入力:
  - v112/outputs/{mode}/excess_change_adjusted_{condition_id}_seed{N}.parquet
    (compute_baseline_excess_change + add_adjusted_excess の出力、(event, path) 行)
  - v112/outputs/step_c/receptive_cids_{condition_id}_seed{N}.parquet (Step C metadata)
  - v112/outputs/{mode}/atom_introduction_events_{condition_id}_seed{N}.parquet (event metadata)

per-event 波及プロファイル列 (主題 §11、Step A v2 §3.3):
  - delta_C_medium       : relation paths 全体の mean (medium window)
  - delta_Q_medium       : 同上
  - n_pulses_short       : relation paths 全体の mean (short window)
  - path_familiarity_excess_delta_C_medium       : familiarity - unrelated_baseline
  - path_attention_excess_delta_C_medium         : attention_via_salience - unrelated_baseline
  - path_temporal_excess_delta_C_medium          : temporal_coactivation - unrelated_baseline
  - path_integration_alpha_excess_delta_C_medium : integration_alpha - unrelated_baseline

層化軸 (per-event 行に同梱、Step F observation_recorder で集計):
  - n_core_bin           : bin_5_plus / bin_2 / bin_3_4
  - formation_relation   : before / no_alpha / during / after
  - source_cid, target_step, atom_id, atom_index

出力:
  v112/outputs/{mode}/propagation_profile_{condition_id}_seed{N}.parquet

規律:
  - 物理層 frozen: post-process 集計のみ
  - 神の手回避: 主題 §11 に明示された 7 列のみ算出、観察軸増加なし
  - 因果断定回避: 「波及」「字面に揺れる」表現
"""
from __future__ import annotations

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
STEP_C_ROOT = V112_ROOT / "outputs" / "step_c"
V112_SMOKE = V112_ROOT / "outputs" / "smoke"
V112_MAIN = V112_ROOT / "outputs" / "main"

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]

# v107 path_analyzer / baseline_constructor で生成される 10 種
RELATION_PATHS = [
    "familiarity",
    "attention_via_salience",
    "integration_alpha",
    "integration_beta",
    "temporal_coactivation",
]
BASELINES = [
    "unrelated_baseline",
    "same_step_random_baseline",
    "matched_baseline",
    "same_integration_low_familiarity_baseline",
    "high_familiarity_outside_integration_baseline",
]
# excess の reference: unrelated_baseline (最も中立、Step A v2 §3.3 設計)
EXCESS_REFERENCE = "unrelated_baseline"

# excess プロファイル対象 path 4 種 (Step A v2 §3.3)
PROFILE_PATHS = ["familiarity", "attention_via_salience",
                 "temporal_coactivation", "integration_alpha"]


def assert_output_under_v112(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V112_ROOT not in abs_path.parents and abs_path != V112_ROOT:
        raise ValueError(f"Output path {path} not under v112/")


def safe_write_parquet_v112(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# per-event 波及プロファイル算出
# ----------------------------------------------------------------------
def compute_propagation_profile(df_excess: pd.DataFrame,
                                  df_events: pd.DataFrame) -> pd.DataFrame:
    """(event_id) × (relation_path_type) の excess 行を per-event 行にピボット.

    delta_C_medium / delta_Q_medium / n_pulses_short は relation paths 5 種の mean.
    path_X_excess_delta_C_medium = path X - unrelated_baseline.
    """
    # event-level metadata (atom_id, atom_index, source_cid, timestamp, Step C 由来軸)
    event_meta_cols = [
        "event_id", "source_cid", "timestamp", "atom_id", "atom_index",
        "n_core_bin", "formation_relation", "n_core", "lifespan", "fam_max",
        "target_step", "death_step",
    ]
    available_cols = [c for c in event_meta_cols if c in df_events.columns]
    df_meta = df_events[available_cols].drop_duplicates("event_id").copy()

    # excess を pivot: index=event_id, columns=relation_path_type
    metrics = ["mean_delta_C_medium", "mean_delta_Q_medium",
               "mean_n_pulses_in_window_short"]
    rows = []
    grouped = df_excess.groupby("event_id")
    for event_id, sub in grouped:
        path_lookup = dict(zip(sub["relation_path_type"], range(len(sub))))
        # relation paths 内の mean
        rp_mask = sub["relation_path_type"].isin(RELATION_PATHS)
        rp_sub = sub[rp_mask]
        row = {"event_id": event_id}
        if not rp_sub.empty:
            row["delta_C_medium"] = float(rp_sub["mean_delta_C_medium"].mean())
            row["delta_Q_medium"] = float(rp_sub["mean_delta_Q_medium"].mean())
            row["n_pulses_short"] = float(rp_sub["mean_n_pulses_in_window_short"].mean())
        else:
            row["delta_C_medium"] = np.nan
            row["delta_Q_medium"] = np.nan
            row["n_pulses_short"] = np.nan

        # path-level excess vs unrelated_baseline
        ref_row = sub[sub["relation_path_type"] == EXCESS_REFERENCE]
        ref_dc = float(ref_row["mean_delta_C_medium"].iloc[0]) if not ref_row.empty else np.nan
        for path in PROFILE_PATHS:
            path_row = sub[sub["relation_path_type"] == path]
            if not path_row.empty and not np.isnan(ref_dc):
                row[f"path_{path}_excess_delta_C_medium"] = (
                    float(path_row["mean_delta_C_medium"].iloc[0]) - ref_dc
                )
            else:
                row[f"path_{path}_excess_delta_C_medium"] = np.nan

        # 観察補助: 各 path の raw mean_delta_C_medium も保持 (post-process 検査用)
        for path in RELATION_PATHS:
            path_row = sub[sub["relation_path_type"] == path]
            row[f"raw_{path}_delta_C_medium"] = (
                float(path_row["mean_delta_C_medium"].iloc[0]) if not path_row.empty else np.nan
            )
        row[f"raw_{EXCESS_REFERENCE}_delta_C_medium"] = ref_dc

        rows.append(row)

    df_profile = pd.DataFrame(rows)
    # event metadata 付与 (層化軸 + source_cid 等)
    df_profile = df_profile.merge(df_meta, on="event_id", how="left")
    return df_profile


# ----------------------------------------------------------------------
# Per-seed pipeline
# ----------------------------------------------------------------------
def process_seed_condition(seed: int, condition_id: str, mode: str) -> dict:
    in_root = V112_SMOKE if mode == "smoke" else V112_MAIN
    out_root = in_root

    t0 = time.time()
    excess_path = in_root / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
    events_path = in_root / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"

    if not excess_path.exists():
        raise FileNotFoundError(f"excess_change missing: {excess_path}")
    if not events_path.exists():
        raise FileNotFoundError(f"atom events missing: {events_path}")

    df_excess = pd.read_parquet(excess_path)
    df_events = pd.read_parquet(events_path)

    df_profile = compute_propagation_profile(df_excess, df_events)
    df_profile["seed"] = seed
    df_profile["condition_id"] = condition_id

    out_path = out_root / f"propagation_profile_{condition_id}_seed{seed}.parquet"
    safe_write_parquet_v112(df_profile, out_path)

    return {
        "seed": seed, "condition_id": condition_id,
        "n_events": int(len(df_profile)),
        "delta_C_medium_mean": float(df_profile["delta_C_medium"].mean()),
        "delta_C_medium_std": float(df_profile["delta_C_medium"].std()),
        "delta_Q_medium_mean": float(df_profile["delta_Q_medium"].mean()),
        "n_pulses_short_mean": float(df_profile["n_pulses_short"].mean()),
        "path_familiarity_excess_mean": float(
            df_profile["path_familiarity_excess_delta_C_medium"].mean()),
        "path_attention_excess_mean": float(
            df_profile["path_attention_via_salience_excess_delta_C_medium"].mean()),
        "path_temporal_excess_mean": float(
            df_profile["path_temporal_coactivation_excess_delta_C_medium"].mean()),
        "path_integration_alpha_excess_mean": float(
            df_profile["path_integration_alpha_excess_delta_C_medium"].mean()),
        "size_mb": round(out_path.stat().st_size / 1024 / 1024, 4),
        "t_total": round(time.time() - t0, 2),
    }


def _worker(args):
    seed, condition_id, mode = args
    return process_seed_condition(seed, condition_id, mode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--conditions", default="all")
    ap.add_argument("--n_workers", type=int, default=12)
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS
    if args.conditions == "all":
        conds = list(CONDITION_SET)
    else:
        conds = [c.strip() for c in args.conditions.split(",") if c.strip()]

    t0 = time.time()
    print("=" * 72)
    print(f"v10.12 Step E (Part 2): v112_propagation_analyzer  mode={args.mode}")
    print(f"  seeds={len(seeds)}, conditions={conds}, n_workers={args.n_workers}")
    print(f"  per-event 波及プロファイル: delta_C/Q_medium, n_pulses_short,")
    print(f"    path_excess × 4 (familiarity/attention/temporal/integration_alpha)")
    print("=" * 72)

    jobs = [(s, c, args.mode) for s in seeds for c in conds]
    n_workers = max(1, min(args.n_workers, len(jobs)))
    if n_workers > 1 and len(jobs) > 1:
        with Pool(processes=n_workers) as pool:
            results = pool.map(_worker, jobs)
    else:
        results = [_worker(j) for j in jobs]

    df_sum = pd.DataFrame(results).sort_values(["condition_id", "seed"]).reset_index(drop=True)
    out_root = V112_SMOKE if args.mode == "smoke" else V112_MAIN
    safe_write_parquet_v112(df_sum,
                              out_root / f"propagation_profile_run_summary_{args.mode}.parquet")

    print(f"\n=== completed jobs: {len(results)} ===")
    for _, r in df_sum.iterrows():
        print(f"  {r['condition_id']:<15s} seed={r['seed']:2d}: "
              f"n_events={r['n_events']:>5d}, "
              f"delta_C_med={r['delta_C_medium_mean']:+.4f}, "
              f"delta_Q_med={r['delta_Q_medium_mean']:+.4f}, "
              f"path_fam_excess={r['path_familiarity_excess_mean']:+.4f}, "
              f"path_attn_excess={r['path_attention_excess_mean']:+.4f}, "
              f"t={r['t_total']:.1f}s")
    print(f"\n  total size: {df_sum['size_mb'].sum():.2f} MB")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
