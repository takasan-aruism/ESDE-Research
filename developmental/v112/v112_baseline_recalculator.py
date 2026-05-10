#!/usr/bin/env python3
"""v10.12 Step E: v112_baseline_recalculator.

v107 build_all_paths + build_baselines + compute_deltas +
compute_baseline_excess_change + v108 add_adjusted_excess を共通利用し、
v112 condition について baseline 再計算を実行する.

v108_standard は v110/v108_re/outputs/{mode}/ 既存出力 (DC-A3 流用) を
event_id で filter し、v112/outputs/{mode}/ 下に同名 schema で再書き出し
(層 B 不変: v108_re main は読み込みのみ).

条件:
  - v112: 新規計算 (Step C cid pool × 25 atom burst)
  - v108_standard: 既存出力流用 + Step C v108_standard pool で event_id filter

出力:
  - baselines_with_delta_v112_seed{N}.parquet           (新規)
  - excess_change_adjusted_v112_seed{N}.parquet         (新規)
  - baselines_with_delta_v108_standard_seed{N}.parquet  (v108_re 既存流用 + filter)
  - excess_change_adjusted_v108_standard_seed{N}.parquet (v108_re 既存流用 + filter)

規律:
  - 物理層 frozen: ledger 不変、baseline 計算のみ
  - 層 B 不変: v108_re/outputs/main/ + v108/outputs/main/ は読み込みのみ
  - 層 C: 出力は v112/outputs/{smoke,main}/ 配下のみ
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()

V108_MAIN = V108_ROOT / "outputs" / "main"  # global_activation_factor の所在
V108RE_MAIN = V110_ROOT / "v108_re" / "outputs" / "main"
V108RE_SMOKE = V110_ROOT / "v108_re" / "outputs" / "smoke"

V112_SMOKE = V112_ROOT / "outputs" / "smoke"
V112_MAIN = V112_ROOT / "outputs" / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v107_path_analyzer import build_all_paths  # noqa: E402
from v107_baseline_constructor import (  # noqa: E402
    build_baselines, compute_deltas, compute_baseline_excess_change,
)
from v108_global_activation_correction import add_adjusted_excess  # noqa: E402

SEEDS = list(range(24))
INT_COLS = ["source_cid", "timestamp", "target_cid", "hop_distance", "seed"]
CONDITION_SET = ["v112", "v108_standard"]


def assert_output_under_v112(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V112_ROOT not in abs_path.parents and abs_path != V112_ROOT:
        raise ValueError(f"Output path {path} not under v112/")


def safe_write_parquet_v112(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def _force_int_cols(df: pd.DataFrame) -> pd.DataFrame:
    """build_all_paths 内の空 sub-df concat による object 化対策 (v10.10 規約).

    INT_COLS の列を強制 cast、欠損は -1.
    """
    if df.empty:
        return df
    for col in INT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(-1).astype(int)
    return df


# ----------------------------------------------------------------------
# v112 baseline 計算 (新規)
# ----------------------------------------------------------------------
def recalculate_v112_for_seed(seed: int, mode: str) -> dict:
    """v112 condition の baseline_recalculator パイプライン.

    入力: v112/outputs/{mode}/atom_introduction_events_v112_seed{N}.parquet
    出力: v112/outputs/{mode}/baselines_with_delta_v112_seed{N}.parquet
           v112/outputs/{mode}/excess_change_adjusted_v112_seed{N}.parquet
    """
    in_root = V112_SMOKE if mode == "smoke" else V112_MAIN
    out_root = in_root

    t0 = time.time()
    atom_path = in_root / f"atom_introduction_events_v112_seed{seed}.parquet"
    if not atom_path.exists():
        raise FileNotFoundError(f"Step D output missing: {atom_path}")
    df_atom = pd.read_parquet(atom_path)

    if df_atom.empty:
        return {
            "seed": seed, "condition_id": "v112",
            "n_relation_paths": 0, "n_baselines": 0,
            "n_with_delta": 0, "n_excess": 0,
            "size_with_delta_mb": 0.0, "size_excess_adj_mb": 0.0,
            "t_total": round(time.time() - t0, 2),
            "skipped": True,
        }

    # 1. build_all_paths + build_baselines
    rp = build_all_paths(seed, df_atom)
    bl = build_baselines(seed, df_atom)
    rp = _force_int_cols(rp)
    bl = _force_int_cols(bl)

    # 2. concat + compute_deltas
    df_all = pd.concat([rp, bl], ignore_index=True, sort=False)
    df_all = _force_int_cols(df_all)
    df_with_delta = compute_deltas(seed, df_all)
    df_with_delta["condition_id"] = "v112"
    out_a = out_root / f"baselines_with_delta_v112_seed{seed}.parquet"
    safe_write_parquet_v112(df_with_delta, out_a)

    # 3. compute_baseline_excess_change
    df_excess = compute_baseline_excess_change(df_with_delta)

    # 4. add_adjusted_excess (global_activation_factor、v108 既存出力流用、層 B 不変)
    factor_path = V108_MAIN / f"global_activation_factor_seed{seed}.parquet"
    if not factor_path.exists():
        raise FileNotFoundError(f"v108 global_activation_factor missing: {factor_path}")
    df_factor = pd.read_parquet(factor_path)
    df_excess_adj = add_adjusted_excess(df_excess, df_atom, df_factor)
    df_excess_adj["condition_id"] = "v112"
    out_b = out_root / f"excess_change_adjusted_v112_seed{seed}.parquet"
    safe_write_parquet_v112(df_excess_adj, out_b)

    return {
        "seed": seed, "condition_id": "v112",
        "n_relation_paths": int(len(rp)),
        "n_baselines": int(len(bl)),
        "n_with_delta": int(len(df_with_delta)),
        "n_excess": int(len(df_excess_adj)),
        "size_with_delta_mb": round(out_a.stat().st_size / 1024 / 1024, 4),
        "size_excess_adj_mb": round(out_b.stat().st_size / 1024 / 1024, 4),
        "t_total": round(time.time() - t0, 2),
        "skipped": False,
    }


# ----------------------------------------------------------------------
# v108_standard baseline 流用 (v108_re 既存出力 + Step C pool filter)
# ----------------------------------------------------------------------
def recalculate_v108_standard_for_seed(seed: int, mode: str) -> dict:
    """v108_re/outputs/{mode}/ 既存 baselines を読み込み、Step C v108_standard
    pool で event_id filter して v112/outputs/{mode}/ 下に書き出し.

    層 B 不変: v108_re 既存出力は読み込みのみ.
    """
    in_root = V112_SMOKE if mode == "smoke" else V112_MAIN
    v108re_root = V108RE_SMOKE if mode == "smoke" else V108RE_MAIN
    out_root = in_root

    t0 = time.time()
    # v108_standard events (Step D 流用、event_id は v108_re と同形式)
    v108std_path = in_root / f"atom_introduction_events_v108_standard_seed{seed}.parquet"
    df_v108std = pd.read_parquet(v108std_path)
    keep_event_ids = set(df_v108std["event_id"].astype(str).tolist())

    # v108_re 既存 baselines + excess を読み込み
    bl_path = v108re_root / f"baselines_with_delta_v108_re_seed{seed}.parquet"
    ex_path = v108re_root / f"excess_change_adjusted_v108_re_seed{seed}.parquet"
    if not bl_path.exists() or not ex_path.exists():
        raise FileNotFoundError(f"v108_re baseline/excess missing: {bl_path} / {ex_path}")
    df_bl = pd.read_parquet(bl_path).copy()
    df_ex = pd.read_parquet(ex_path).copy()

    # Step C v108_standard pool で event_id filter
    df_bl_f = df_bl[df_bl["event_id"].astype(str).isin(keep_event_ids)].copy()
    df_ex_f = df_ex[df_ex["event_id"].astype(str).isin(keep_event_ids)].copy()
    df_bl_f["condition_id"] = "v108_standard"
    df_ex_f["condition_id"] = "v108_standard"

    out_a = out_root / f"baselines_with_delta_v108_standard_seed{seed}.parquet"
    out_b = out_root / f"excess_change_adjusted_v108_standard_seed{seed}.parquet"
    safe_write_parquet_v112(df_bl_f, out_a)
    safe_write_parquet_v112(df_ex_f, out_b)

    return {
        "seed": seed, "condition_id": "v108_standard",
        "n_with_delta": int(len(df_bl_f)),
        "n_excess": int(len(df_ex_f)),
        "n_with_delta_v108re_total": int(len(df_bl)),
        "n_excess_v108re_total": int(len(df_ex)),
        "filter_ratio": round(len(df_bl_f) / max(len(df_bl), 1), 4),
        "size_with_delta_mb": round(out_a.stat().st_size / 1024 / 1024, 4),
        "size_excess_adj_mb": round(out_b.stat().st_size / 1024 / 1024, 4),
        "t_total": round(time.time() - t0, 2),
        "skipped": False,
    }


# ----------------------------------------------------------------------
# Per-seed pipeline (v112 + v108_standard 両方)
# ----------------------------------------------------------------------
def _process_one(args):
    seed, condition_id, mode = args
    if condition_id == "v112":
        return recalculate_v112_for_seed(seed, mode)
    if condition_id == "v108_standard":
        return recalculate_v108_standard_for_seed(seed, mode)
    raise ValueError(f"Unknown condition: {condition_id}")


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
    print(f"v10.12 Step E: v112_baseline_recalculator  mode={args.mode}")
    print(f"  seeds={len(seeds)}, conditions={conds}, n_workers={args.n_workers}")
    print(f"  v112: build_all_paths + build_baselines + compute_deltas + excess")
    print(f"  v108_standard: v108_re/outputs/{{mode}}/ 既存流用 + Step C pool filter")
    print("=" * 72)

    jobs = [(s, c, args.mode) for s in seeds for c in conds]
    n_workers = max(1, min(args.n_workers, len(jobs)))
    if n_workers > 1 and len(jobs) > 1:
        with Pool(processes=n_workers) as pool:
            results = pool.map(_process_one, jobs)
    else:
        results = [_process_one(j) for j in jobs]

    df_sum = pd.DataFrame(results).sort_values(["condition_id", "seed"]).reset_index(drop=True)
    out_root = V112_SMOKE if args.mode == "smoke" else V112_MAIN
    safe_write_parquet_v112(df_sum, out_root / f"baseline_recalc_run_summary_{args.mode}.parquet")

    print(f"\n=== completed jobs: {len(results)} ===")
    for _, r in df_sum.iterrows():
        print(f"  {r['condition_id']:<15s} seed={r['seed']:2d}: "
              f"n_with_delta={r['n_with_delta']:>6d}, "
              f"n_excess={r['n_excess']:>5d}, "
              f"t={r['t_total']:>5.1f}s, "
              f"size={r['size_with_delta_mb']:>5.2f}+{r['size_excess_adj_mb']:>5.2f} MB")
    total_size = df_sum["size_with_delta_mb"].sum() + df_sum["size_excess_adj_mb"].sum()
    print(f"\n  total size: {total_size:.2f} MB")
    print(f"  per condition mean t: {df_sum['t_total'].mean():.2f}s")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
