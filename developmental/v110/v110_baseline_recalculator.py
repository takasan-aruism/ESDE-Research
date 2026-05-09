#!/usr/bin/env python3
"""v10.10 baseline recalculator (28 conditions、v10.9 流用拡張).

各 condition の atom events に対して:
  1. v107 build_all_paths
  2. v107 build_baselines (5 種)
  3. v107 compute_deltas
  4. v107 compute_baseline_excess_change
  5. v108 add_adjusted_excess (global_activation 補正、natural のみで計算)

natural events 部分は不変なので global_activation_factor は v108 出力流用。

v110: developmental/v110/outputs/{mode}/baselines_with_delta_{cond}_seed{N}.parquet
v108_re: developmental/v110/v108_re/outputs/{mode}/...
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
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()

V108_MAIN = V108_ROOT / "outputs" / "main"

OUT_ROOT = V110_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"
V108RE_ROOT = V110_ROOT / "v108_re" / "outputs"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
sys.path.insert(0, str(V110_ROOT))
from v107_path_analyzer import build_all_paths  # noqa: E402
from v107_baseline_constructor import (  # noqa: E402
    build_baselines, compute_deltas, compute_baseline_excess_change,
)
from v108_global_activation_correction import add_adjusted_excess  # noqa: E402
from v110_atom_event_generator import CONDITIONS  # noqa: E402

SEEDS = list(range(24))


def assert_output_under_v110(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V110_ROOT not in abs_path.parents and abs_path != V110_ROOT:
        raise ValueError(f"Output path {path} not under v110/")


def safe_write_parquet_v110(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v110(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def _io_root_for(condition_id: str, mode: str) -> Path:
    if condition_id == "v108_re":
        return V108RE_ROOT / mode
    return SMOKE_ROOT if mode == "smoke" else MAIN_ROOT


def recalculate_for_condition(seed: int, condition_id: str, mode: str) -> dict:
    in_root = _io_root_for(condition_id, mode)
    out_root = in_root

    summary = {"seed": seed, "condition_id": condition_id}
    t_start = time.time()

    atom_path = in_root / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"
    if not atom_path.exists():
        raise FileNotFoundError(f"Step C output missing: {atom_path}")
    df_atom = pd.read_parquet(atom_path)

    if df_atom.empty:
        # 空でも summary 返す (downstream が merge できるように)
        summary.update({
            "n_relation_paths": 0, "n_baselines": 0,
            "n_with_delta": 0, "n_excess": 0,
            "size_with_delta_mb": 0.0, "size_excess_adj_mb": 0.0,
            "t_total": round(time.time() - t_start, 2),
        })
        return summary

    rp = build_all_paths(seed, df_atom)
    bl = build_baselines(seed, df_atom)
    # 空要素 concat (build_all_paths 内の familiarity/sal/integ/temp 結合) で
    # 全列が object 化する不具合への対策: 整数列を強制 cast
    INT_COLS = ["source_cid", "timestamp", "target_cid", "hop_distance", "seed"]
    for df_x in (rp, bl):
        if df_x.empty:
            continue
        for col in INT_COLS:
            if col in df_x.columns:
                df_x[col] = pd.to_numeric(df_x[col], errors="coerce").fillna(-1).astype(int)
    summary["n_relation_paths"] = len(rp)
    summary["n_baselines"] = len(bl)

    df_all = pd.concat([rp, bl], ignore_index=True, sort=False)
    for col in INT_COLS:
        if col in df_all.columns:
            df_all[col] = pd.to_numeric(df_all[col], errors="coerce").fillna(-1).astype(int)
    df_with_delta = compute_deltas(seed, df_all)
    df_with_delta["condition_id"] = condition_id
    out_a = out_root / f"baselines_with_delta_{condition_id}_seed{seed}.parquet"
    safe_write_parquet_v110(df_with_delta, out_a)
    summary["n_with_delta"] = len(df_with_delta)
    summary["size_with_delta_mb"] = round(out_a.stat().st_size / 1024 / 1024, 4)

    df_excess = compute_baseline_excess_change(df_with_delta)
    factor_path = V108_MAIN / f"global_activation_factor_seed{seed}.parquet"
    df_factor = pd.read_parquet(factor_path)
    df_excess_adj = add_adjusted_excess(df_excess, df_atom, df_factor)
    df_excess_adj["condition_id"] = condition_id
    out_b = out_root / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
    safe_write_parquet_v110(df_excess_adj, out_b)
    summary["n_excess"] = len(df_excess_adj)
    summary["size_excess_adj_mb"] = round(out_b.stat().st_size / 1024 / 1024, 4)

    summary["t_total"] = round(time.time() - t_start, 2)
    return summary


def _worker(args):
    seed, condition_id, mode = args
    return recalculate_for_condition(seed, condition_id, mode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--conditions", default="all")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS
    if args.conditions == "all":
        conds = list(CONDITIONS.keys())
    else:
        conds = [c.strip() for c in args.conditions.split(",") if c.strip()]

    print(f"v10.10 baseline recalculator - mode={args.mode}, "
          f"seeds={len(seeds)}, conditions={len(conds)}, n_workers={args.n_workers}")

    jobs = [(s, c, args.mode) for s in seeds for c in conds]
    n_workers = max(1, min(args.n_workers, len(jobs)))
    t0 = time.time()
    if n_workers > 1:
        with Pool(processes=n_workers) as pool:
            results = pool.map(_worker, jobs)
    else:
        results = [_worker(j) for j in jobs]

    df_sum = pd.DataFrame(results).sort_values(["condition_id", "seed"]).reset_index(drop=True)
    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    safe_write_parquet_v110(df_sum, out_root / "baseline_recalc_run_summary.parquet")

    print(f"\n=== completed jobs: {len(results)} ===")
    skipped = df_sum[df_sum["n_with_delta"] == 0]
    print(f"  skipped (empty atom events): {len(skipped)}")
    if len(skipped) > 0:
        print(f"    {skipped['condition_id'].unique().tolist()[:5]}...")
    print(f"  per condition mean t_total: {df_sum['t_total'].mean():.2f}s, "
          f"max={df_sum['t_total'].max():.2f}s")
    total_size = df_sum["size_with_delta_mb"].sum() + df_sum["size_excess_adj_mb"].sum()
    print(f"  total size: {total_size:.2f} MB")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
