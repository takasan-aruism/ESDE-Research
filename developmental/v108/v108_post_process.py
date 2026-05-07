#!/usr/bin/env python3
"""v10.8 post-process orchestrator (Step D).

v10.7 5 機構を流用し、source_event 第 6 種 (atom_introduction_event) を
統合した完全パイプライン。各 seed で:
  Step C (natural + atom_introduction) → Step D (path) → Step E (baseline + delta)
  → Step F (multi-hop + peak_lag + loop) → 出力。

実行例:
  python3 v108_post_process.py --mode smoke
  python3 v108_post_process.py --mode main --n_workers 24
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V107_MAIN_OUT = V107_ROOT / "outputs" / "main"

OUT_ROOT = V108_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v107_event_aggregator import aggregate_source_events  # noqa: E402
from v107_path_analyzer import build_all_paths  # noqa: E402
from v107_baseline_constructor import (  # noqa: E402
    build_baselines, compute_deltas, compute_baseline_excess_change,
)
from v107_avalanche_monitor import (  # noqa: E402
    build_multi_hop_paths, compute_decay_rate, detect_resonance_loops,
    compute_peak_lag_curve, compute_peak_lag_per_path, classify_wave_patterns,
)
from v108_atom_event_generator import generate_seed_atom_events  # noqa: E402

SEEDS = list(range(24))


def assert_output_under_v108(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V108_ROOT not in abs_path.parents and abs_path != V108_ROOT:
        raise ValueError(f"Output path {path} not under v108/")


def safe_write_parquet_v108(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v108(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# bit-identity 層 B: v10.7 baseline MD5 取得 (v10.8 では v10.7 出力を不変検証)
# ----------------------------------------------------------------------
def compute_v107_baseline_md5() -> dict[str, str]:
    md5_dict: dict[str, str] = {}
    for ext in ("*.csv", "*.parquet", "*.npz", "*.json"):
        for path in V107_MAIN_OUT.rglob(ext):
            with open(path, "rb") as f:
                md5_dict[str(path.relative_to(V107_MAIN_OUT))] = hashlib.md5(
                    f.read()
                ).hexdigest()
    return md5_dict


def verify_v107_baseline_unchanged(baseline_md5: dict[str, str]) -> tuple[bool, list[str]]:
    current = compute_v107_baseline_md5()
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
# Source event 統合 (5 種 natural + 1 種 atom_introduction)
# ----------------------------------------------------------------------
ATOM_META_COLS = ["atom_id", "atom_index", "top_k_rank", "atom_sim_score",
                    "reserved_label"]
POST_EVENT_COLS = ["Q_after_atom_intro", "C_after_atom_intro"]


def integrate_source_events(seed: int) -> pd.DataFrame:
    """5 種 natural + 1 種 atom_introduction を統合し、共通スキーマで返す."""
    # 5 種 natural (v10.7 流用)
    src_nat = aggregate_source_events(seed)
    # 1 種 atom_introduction
    src_atom = generate_seed_atom_events(seed)

    # natural 側に atom メタ + post_event 列を空で追加
    src_nat = src_nat.copy()
    src_nat["atom_id"] = ""
    src_nat["atom_index"] = -1
    src_nat["top_k_rank"] = -1
    src_nat["atom_sim_score"] = 0.0
    src_nat["reserved_label"] = ""
    # natural は計算的減算なし (Q_after = Q_pre)
    src_nat["Q_after_atom_intro"] = src_nat.get("Q_pre", 0.0)
    src_nat["C_after_atom_intro"] = src_nat.get("C_pre", 0.0)

    # atom 側のスキーマを natural に合わせる (列順統一)
    common_cols = list(src_nat.columns)
    for col in common_cols:
        if col not in src_atom.columns:
            src_atom[col] = np.nan
    src_atom = src_atom[common_cols]

    df = pd.concat([src_nat, src_atom], ignore_index=True, sort=False)
    df = df.sort_values(["timestamp", "event_source_type"]).reset_index(drop=True)
    return df


# ----------------------------------------------------------------------
# Per-seed full pipeline
# ----------------------------------------------------------------------
def run_seed_full_pipeline_v108(seed: int, out_root: Path) -> dict:
    summary = {"seed": seed}
    t_start = time.time()

    # Step C: source_events 統合 (5 natural + 1 atom_introduction)
    src_ev = integrate_source_events(seed)
    safe_write_parquet_v108(src_ev, out_root / f"source_events_seed{seed}.parquet")
    summary["t_step_c"] = round(time.time() - t_start, 2)
    summary["n_source_events"] = len(src_ev)
    type_counts = src_ev["event_source_type"].value_counts().to_dict()
    summary["n_natural"] = sum(v for k, v in type_counts.items()
                                  if k != "atom_introduction_event")
    summary["n_atom_intro"] = type_counts.get("atom_introduction_event", 0)

    # Step D: relation_paths (5 種、v10.7 流用)
    t = time.time()
    rp = build_all_paths(seed, src_ev)
    safe_write_parquet_v108(rp, out_root / f"relation_paths_seed{seed}.parquet")
    summary["t_step_d"] = round(time.time() - t, 2)
    summary["n_relation_paths"] = len(rp)

    # Step E: baselines + delta (v10.7 流用)
    t = time.time()
    bl = build_baselines(seed, src_ev)
    df_all = pd.concat([rp, bl], ignore_index=True, sort=False)
    df_with_delta = compute_deltas(seed, df_all)
    safe_write_parquet_v108(
        df_with_delta, out_root / f"baselines_with_delta_seed{seed}.parquet"
    )
    df_excess = compute_baseline_excess_change(df_with_delta)
    safe_write_parquet_v108(df_excess, out_root / f"excess_change_seed{seed}.parquet")
    summary["t_step_e"] = round(time.time() - t, 2)
    summary["n_baselines"] = len(bl)
    summary["n_excess_rows"] = len(df_excess)

    # Step F: avalanche + peak_lag (v10.7 流用)
    t = time.time()
    df_mh = build_multi_hop_paths(seed, src_ev)
    safe_write_parquet_v108(df_mh, out_root / f"multi_hop_paths_seed{seed}.parquet")
    df_excess_for_decay = df_excess.copy()
    df_excess_for_decay.loc[
        df_excess_for_decay["relation_path_type"] == "familiarity",
        "relation_path_type",
    ] = "familiarity_hop1"
    df_decay = compute_decay_rate(df_excess_for_decay, df_mh)
    safe_write_parquet_v108(df_decay, out_root / f"decay_rate_seed{seed}.parquet")
    df_loops = detect_resonance_loops(seed)
    safe_write_parquet_v108(df_loops, out_root / f"resonance_loops_seed{seed}.parquet")
    df_curve = compute_peak_lag_curve(seed, df_with_delta)
    safe_write_parquet_v108(df_curve, out_root / f"peak_lag_curve_seed{seed}.parquet")
    df_peak = compute_peak_lag_per_path(df_curve)
    df_wave = classify_wave_patterns(df_peak, df_curve)
    df_wave["seed"] = seed
    safe_write_parquet_v108(df_wave, out_root / f"wave_patterns_seed{seed}.parquet")
    summary["t_step_f"] = round(time.time() - t, 2)
    summary["n_multi_hop"] = len(df_mh)
    summary["n_loops_2"] = (
        int((df_loops.get("loop_type") == "loop_2_hop").sum())
        if not df_loops.empty else 0
    )
    summary["n_loops_3"] = (
        int((df_loops.get("loop_type") == "loop_3_hop").sum())
        if not df_loops.empty else 0
    )

    summary["t_total"] = round(time.time() - t_start, 2)
    return summary


def _run_seed_pipeline_worker_v108(args):
    seed, out_root = args
    return run_seed_full_pipeline_v108(seed, out_root)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--no_layer_b", action="store_true",
                      help="bit-identity 層 B 検証をスキップ")
    ap.add_argument("--n_workers", type=int, default=24,
                      help="並列 worker 数 (1=順次、24=full parallel)")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.8 post-process orchestrator - mode={args.mode}, seeds={seeds}")

    # bit-identity 層 B: smoke 前に v10.7 baseline MD5 を取得
    layer_b_baseline = None
    if not args.no_layer_b:
        print(f"\n=== bit-identity 層 B: v10.7 baseline MD5 取得 ===")
        layer_b_baseline = compute_v107_baseline_md5()
        print(f"  v10.7 files tracked: {len(layer_b_baseline)}")

    summaries = []
    t0 = time.time()
    n_workers = max(1, min(args.n_workers, len(seeds)))
    if n_workers > 1 and len(seeds) > 1:
        print(f"\n=== 並列実行 ({n_workers} workers、24 seeds 単一バッチ) ===")
        worker_args = [(s, out_root) for s in seeds]
        with Pool(processes=n_workers) as pool:
            summaries = pool.map(_run_seed_pipeline_worker_v108, worker_args)
        summaries = sorted(summaries, key=lambda s: s["seed"])
    else:
        print(f"\n=== 順次実行 ===")
        for seed in seeds:
            s = run_seed_full_pipeline_v108(seed, out_root)
            summaries.append(s)
    for s in summaries:
        print(f"  seed={s['seed']:>2}: events={s['n_source_events']} "
              f"(nat={s['n_natural']}+atom={s['n_atom_intro']}), "
              f"paths={s['n_relation_paths']}, baselines={s['n_baselines']}, "
              f"excess={s['n_excess_rows']}, mh={s['n_multi_hop']}, "
              f"loops_2={s['n_loops_2']}, loops_3={s['n_loops_3']}, "
              f"t={s['t_total']}s")

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v108(df_sum, out_root / "post_process_run_summary.parquet")

    if not args.no_layer_b and layer_b_baseline is not None:
        print(f"\n=== bit-identity 層 B: v10.7 baseline 不変性検証 ===")
        ok, diffs = verify_v107_baseline_unchanged(layer_b_baseline)
        if ok:
            print(f"  PASS: v10.7 baseline {len(layer_b_baseline)} files 全て不変")
        else:
            print(f"  FAIL: {len(diffs)} differences:")
            for d in diffs[:10]:
                print(f"    {d}")
            return 1

    print(f"\n=== storage 実測 (seed {seeds[0]} / {args.mode}) ===")
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
