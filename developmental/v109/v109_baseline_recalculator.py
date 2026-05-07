#!/usr/bin/env python3
"""v10.9 baseline recalculator (各 condition で 5+1 種 baseline 再計算).

各 atom event 条件 (A2 / B3 / 後続 C2) で:
  1. atom_introduction_events_{cond}_seed{N}.parquet を入力
  2. v107 build_all_paths でこの条件の atom events に対する relation_paths
  3. v107 build_baselines で 5 種 baseline cid 群を構築
  4. v107 compute_deltas で 6 量 × 3 windows の delta 計算
  5. v107 compute_baseline_excess_change で per (event, path) excess
  6. v108 global_activation_factor (natural events のみ、conditions 不変) を流用
  7. v108 add_adjusted_excess で adjusted_excess 列追加

natural events 部分は条件で変わらないため再計算しない (v108 既存出力流用)。
condition_id 列を付与して保存。

出力:
  developmental/v109/outputs/{smoke,main}/
    baselines_with_delta_{cond}_seed{N}.parquet
    excess_change_adjusted_{cond}_seed{N}.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V109_ROOT = (REPO_ROOT / "developmental" / "v109").resolve()

V108_MAIN = V108_ROOT / "outputs" / "main"

OUT_ROOT = V109_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v107_path_analyzer import build_all_paths  # noqa: E402
from v107_baseline_constructor import (  # noqa: E402
    build_baselines, compute_deltas, compute_baseline_excess_change,
)
from v108_global_activation_correction import add_adjusted_excess  # noqa: E402

SEEDS = list(range(24))
CONDITIONS_DEFAULT = ["A2", "B3"]


def assert_output_under_v109(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")


def safe_write_parquet_v109(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v109(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def recalculate_for_condition(seed: int, condition_id: str, mode: str) -> dict:
    """condition 単位で baseline 再計算 + excess + adjusted を保存."""
    in_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    out_root = in_root

    summary = {"seed": seed, "condition_id": condition_id}
    t_start = time.time()

    atom_path = in_root / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"
    if not atom_path.exists():
        raise FileNotFoundError(f"Step C output missing: {atom_path}")
    df_atom = pd.read_parquet(atom_path)

    # 1. relation_paths (atom events 限定)
    t = time.time()
    rp = build_all_paths(seed, df_atom)
    summary["t_relation_paths"] = round(time.time() - t, 2)
    summary["n_relation_paths"] = len(rp)

    # 2. baselines (atom events 限定)
    t = time.time()
    bl = build_baselines(seed, df_atom)
    summary["t_baselines"] = round(time.time() - t, 2)
    summary["n_baselines"] = len(bl)

    # 3. compute_deltas
    t = time.time()
    df_all = pd.concat([rp, bl], ignore_index=True, sort=False)
    df_with_delta = compute_deltas(seed, df_all)
    df_with_delta["condition_id"] = condition_id
    out_a = out_root / f"baselines_with_delta_{condition_id}_seed{seed}.parquet"
    safe_write_parquet_v109(df_with_delta, out_a)
    summary["t_deltas"] = round(time.time() - t, 2)
    summary["n_with_delta"] = len(df_with_delta)
    summary["size_with_delta_mb"] = round(out_a.stat().st_size / 1024 / 1024, 3)

    # 4. excess_change
    t = time.time()
    df_excess = compute_baseline_excess_change(df_with_delta)

    # 5. global_activation 補正 (v10.8 出力流用)
    factor_path = V108_MAIN / f"global_activation_factor_seed{seed}.parquet"
    if not factor_path.exists():
        raise FileNotFoundError(f"v108 global_activation_factor missing: {factor_path}")
    df_factor = pd.read_parquet(factor_path)
    df_excess_adj = add_adjusted_excess(df_excess, df_atom, df_factor)
    df_excess_adj["condition_id"] = condition_id
    out_b = out_root / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
    safe_write_parquet_v109(df_excess_adj, out_b)
    summary["t_excess_adjusted"] = round(time.time() - t, 2)
    summary["n_excess"] = len(df_excess_adj)
    summary["size_excess_adj_mb"] = round(out_b.stat().st_size / 1024 / 1024, 3)

    summary["t_total"] = round(time.time() - t_start, 2)
    return summary


def _worker(args):
    seed, condition_id, mode = args
    return recalculate_for_condition(seed, condition_id, mode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--conditions", default=",".join(CONDITIONS_DEFAULT),
                       help="Comma-separated condition ids (default: A2,B3)")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    print(f"v10.9 baseline recalculator - mode={args.mode}, "
          f"seeds={len(seeds)}, conditions={conditions}, n_workers={args.n_workers}")

    jobs = [(s, c, args.mode) for s in seeds for c in conditions]
    n_workers = max(1, min(args.n_workers, len(jobs)))

    t0 = time.time()
    if n_workers > 1 and len(jobs) > 1:
        print(f"=== 並列実行 ({n_workers} workers、24 seeds × {len(conditions)} conditions 単一バッチ) ===")
        with Pool(processes=n_workers) as pool:
            summaries = pool.map(_worker, jobs)
    else:
        print(f"=== 順次実行 ===")
        summaries = [_worker(j) for j in jobs]

    summaries = sorted(summaries, key=lambda s: (s["condition_id"], s["seed"]))
    for s in summaries:
        print(f"  seed={s['seed']:>2} cond={s['condition_id']}: "
              f"rp={s['n_relation_paths']:,}, bl={s['n_baselines']:,}, "
              f"with_delta={s['n_with_delta']:,}, excess={s['n_excess']:,}, "
              f"size={s['size_with_delta_mb']}+{s['size_excess_adj_mb']}MB, "
              f"t={s['t_total']}s")

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v109(df_sum, out_root / "baseline_recalc_run_summary.parquet")

    total_size = sum(s["size_with_delta_mb"] + s["size_excess_adj_mb"] for s in summaries)
    print(f"\n=== storage 実測 ===")
    print(f"  total ({len(summaries)} jobs) = {total_size:.2f} MB")
    if args.mode == "smoke":
        print(f"  main 推定: {total_size * 24 / len(seeds):.0f} MB / cond × {len(conditions)} cond")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
