#!/usr/bin/env python3
"""v10.7 post-process orchestrator (Step G).

Step C-F を順次実行する統合スクリプト。bit-identity 層 A/B 検証、
storage 実測も同時実施。

実行例:
  python3 v107_post_process.py --mode smoke
  python3 v107_post_process.py --mode main

Step F の Step G 修正点:
  - echo 判定閾値: 0.001 → 0.01
  - integration_alpha/beta は no_signal でフラグ
  - event 終端除外 (timestamp + max_lag > RUN_END_STEP は peak_lag から除外)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V106_MAIN_OUT = V106_ROOT / "outputs" / "main"

OUT_ROOT = V107_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(Path(__file__).parent))
from v107_event_aggregator import aggregate_source_events  # noqa: E402
from v107_path_analyzer import build_all_paths  # noqa: E402
from v107_baseline_constructor import (  # noqa: E402
    build_baselines, compute_deltas, compute_baseline_excess_change,
)
from v107_avalanche_monitor import (  # noqa: E402
    build_multi_hop_paths, compute_decay_rate, detect_resonance_loops,
    compute_peak_lag_curve, compute_peak_lag_per_path, classify_wave_patterns,
)

SEEDS = list(range(24))


def assert_output_under_v107(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V107_ROOT not in abs_path.parents and abs_path != V107_ROOT:
        raise ValueError(f"Output path {path} not under v107/")


def safe_write_parquet_v107(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v107(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# bit-identity 層 B: v10.6 出力の MD5 hash 取得
# ----------------------------------------------------------------------
def compute_v106_baseline_md5() -> dict[str, str]:
    md5_dict: dict[str, str] = {}
    for ext in ("*.csv", "*.parquet", "*.npz", "*.json"):
        for path in V106_MAIN_OUT.rglob(ext):
            with open(path, "rb") as f:
                md5_dict[str(path.relative_to(V106_MAIN_OUT))] = hashlib.md5(
                    f.read()
                ).hexdigest()
    return md5_dict


def verify_v106_baseline_unchanged(baseline_md5: dict[str, str]) -> tuple[bool, list[str]]:
    current = compute_v106_baseline_md5()
    diffs = []
    if set(baseline_md5.keys()) != set(current.keys()):
        added = set(current.keys()) - set(baseline_md5.keys())
        removed = set(baseline_md5.keys()) - set(current.keys())
        diffs.extend([f"ADDED: {p}" for p in added])
        diffs.extend([f"REMOVED: {p}" for p in removed])
    for k in baseline_md5:
        if k in current and baseline_md5[k] != current[k]:
            diffs.append(f"MODIFIED: {k}")
    return (len(diffs) == 0, diffs)


# ----------------------------------------------------------------------
# orchestrator (1 seed)
# ----------------------------------------------------------------------
def run_seed_full_pipeline(seed: int, out_root: Path) -> dict:
    summary = {"seed": seed}
    t_start = time.time()

    # Step C: source_events
    src_ev = aggregate_source_events(seed)
    safe_write_parquet_v107(src_ev, out_root / f"source_events_seed{seed}.parquet")
    summary["t_step_c"] = round(time.time() - t_start, 2)
    summary["n_source_events"] = len(src_ev)

    # Step D: relation_paths (4 種 + Integration α/β = 5)
    t = time.time()
    rp = build_all_paths(seed, src_ev)
    safe_write_parquet_v107(rp, out_root / f"relation_paths_seed{seed}.parquet")
    summary["t_step_d"] = round(time.time() - t, 2)
    summary["n_relation_paths"] = len(rp)

    # Step E: baselines + delta
    t = time.time()
    bl = build_baselines(seed, src_ev)
    df_all = pd.concat([rp, bl], ignore_index=True, sort=False)
    df_with_delta = compute_deltas(seed, df_all)
    safe_write_parquet_v107(df_with_delta,
                              out_root / f"baselines_with_delta_seed{seed}.parquet")
    df_excess = compute_baseline_excess_change(df_with_delta)
    safe_write_parquet_v107(df_excess, out_root / f"excess_change_seed{seed}.parquet")
    summary["t_step_e"] = round(time.time() - t, 2)
    summary["n_baselines"] = len(bl)
    summary["n_excess_rows"] = len(df_excess)

    # Step F: avalanche + peak_lag
    t = time.time()
    df_mh = build_multi_hop_paths(seed, src_ev)
    safe_write_parquet_v107(df_mh, out_root / f"multi_hop_paths_seed{seed}.parquet")

    # Step F 修正: Step E excess_change を multi_hop hop 1 と互換にして decay 集計
    df_excess_for_decay = df_excess.copy()
    df_excess_for_decay.loc[df_excess_for_decay["relation_path_type"] == "familiarity",
                              "relation_path_type"] = "familiarity_hop1"
    df_decay = compute_decay_rate(df_excess_for_decay, df_mh)
    safe_write_parquet_v107(df_decay, out_root / f"decay_rate_seed{seed}.parquet")

    df_loops = detect_resonance_loops(seed)
    safe_write_parquet_v107(df_loops, out_root / f"resonance_loops_seed{seed}.parquet")

    df_curve = compute_peak_lag_curve(seed, df_with_delta)
    safe_write_parquet_v107(df_curve, out_root / f"peak_lag_curve_seed{seed}.parquet")

    df_peak = compute_peak_lag_per_path(df_curve)
    df_wave = classify_wave_patterns(df_peak, df_curve)
    df_wave["seed"] = seed
    safe_write_parquet_v107(df_wave, out_root / f"wave_patterns_seed{seed}.parquet")

    summary["t_step_f"] = round(time.time() - t, 2)
    summary["n_multi_hop"] = len(df_mh)
    summary["n_loops_2"] = int((df_loops.get("loop_type") == "loop_2_hop").sum()) \
        if not df_loops.empty else 0
    summary["n_loops_3"] = int((df_loops.get("loop_type") == "loop_3_hop").sum()) \
        if not df_loops.empty else 0

    summary["t_total"] = round(time.time() - t_start, 2)
    return summary


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--no_layer_b", action="store_true",
                      help="bit-identity 層 B 検証をスキップ")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.7 post-process orchestrator - mode={args.mode}, seeds={seeds}")

    # bit-identity 層 B: smoke 前に v10.6 baseline MD5 を取得
    layer_b_baseline = None
    if not args.no_layer_b:
        print(f"\n=== bit-identity 層 B: v10.6 baseline MD5 取得 ===")
        layer_b_baseline = compute_v106_baseline_md5()
        print(f"  v10.6 files tracked: {len(layer_b_baseline)}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        s = run_seed_full_pipeline(seed, out_root)
        print(f"  seed={s['seed']}: events={s['n_source_events']}, "
              f"paths={s['n_relation_paths']}, baselines={s['n_baselines']}, "
              f"excess={s['n_excess_rows']}, mh={s['n_multi_hop']}, "
              f"loops_2={s['n_loops_2']}, loops_3={s['n_loops_3']}, "
              f"t_total={s['t_total']}s "
              f"(C={s['t_step_c']}, D={s['t_step_d']}, E={s['t_step_e']}, "
              f"F={s['t_step_f']})")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v107(df_sum, out_root / "post_process_run_summary.parquet")

    # bit-identity 層 B: smoke 後に v10.6 baseline 不変性検証
    if not args.no_layer_b and layer_b_baseline is not None:
        print(f"\n=== bit-identity 層 B: v10.6 baseline 不変性検証 ===")
        ok, diffs = verify_v106_baseline_unchanged(layer_b_baseline)
        if ok:
            print(f"  PASS: v10.6 baseline {len(layer_b_baseline)} files 全て不変")
        else:
            print(f"  FAIL: {len(diffs)} differences:")
            for d in diffs[:10]:
                print(f"    {d}")
            return 1

    # storage 実測
    print(f"\n=== storage 実測 (seed 0 / {args.mode}) ===")
    total_size = 0
    for f in sorted(out_root.glob(f"*seed{seeds[0]}*")):
        size_mb = f.stat().st_size / 1024 / 1024
        total_size += size_mb
        print(f"  {f.name:55s} {size_mb:>7.2f} MB")
    print(f"  {'TOTAL':55s} {total_size:>7.2f} MB")
    print(f"\n  24 seeds 推定: {total_size * 24:.0f} MB ({total_size * 24 / 1024:.2f} GB)")
    print(f"  上限 6 GB との比: {total_size * 24 / 1024 / 6 * 100:.0f}%")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
