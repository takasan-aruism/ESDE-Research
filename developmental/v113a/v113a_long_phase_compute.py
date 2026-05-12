#!/usr/bin/env python3
"""v10.13.a Step H: long phase (>1000 step) post-process 算出.

v107 baseline_constructor.WINDOW_DEFS を monkey-patch で [("long", 1000, 25000)]
に変更、compute_deltas を呼んで v112 / v108_standard の long phase delta を算出.

ledger 再走査が発生するが、層 B 不変 (v107/v108/v112 既存出力には書き込まない).
出力先は v113a/outputs/main/excess_change_long_*.parquet.

注意:
- timestamp + 25000 が cid death を超える event は NaN として記録 (構造的判定)
- 集計対象は v112 events (10,500) + v108_standard events (60,000) = 約 70K events

規律:
- 物理層 frozen: 既存出力 read-only、書き込みは v113a/ 配下のみ
- 神の手回避: WINDOW_DEFS 拡張は構造的延長 (v107 既存設計の自然な延長)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = REPO_ROOT / "developmental" / "v107"
V107_MAIN = V107_ROOT / "outputs" / "main"
V108_ROOT = REPO_ROOT / "developmental" / "v108"
V108_MAIN = V108_ROOT / "outputs" / "main"
V110_ROOT = REPO_ROOT / "developmental" / "v110"
V110_V108RE_MAIN = V110_ROOT / "v108_re" / "outputs" / "main"
V112_MAIN = REPO_ROOT / "developmental" / "v112" / "outputs" / "main"
V113A_ROOT = (REPO_ROOT / "developmental" / "v113a").resolve()
V113A_OUT = V113A_ROOT / "outputs" / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))

import v107_baseline_constructor as v107_bc  # noqa: E402
import v107_path_analyzer as v107_pa  # noqa: E402
from v108_global_activation_correction import add_adjusted_excess  # noqa: E402

# WINDOW_DEFS を long phase 用に書き換え (monkey-patch)
ORIGINAL_WINDOW_DEFS = list(v107_bc.WINDOW_DEFS)
v107_bc.WINDOW_DEFS = [("long", 1000, 25000)]

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]
RUN_END = 25000
INT_COLS = ["source_cid", "timestamp", "target_cid", "hop_distance", "seed"]


def assert_output_under_v113a(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V113A_ROOT not in abs_path.parents and abs_path != V113A_ROOT:
        raise ValueError(f"Output path {path} not under v113a/")


def safe_write_parquet_v113a(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v113a(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def _force_int_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    for col in INT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(-1).astype(int)
    return df


def compute_long_phase_for_seed(args) -> dict:
    """1 seed × 1 condition の long phase delta を算出."""
    seed, condition = args
    t0 = time.time()

    if condition == "v112":
        atom_path = V112_MAIN / f"atom_introduction_events_v112_seed{seed}.parquet"
    elif condition == "v108_standard":
        # v108_re/outputs/main/ を流用 (v10.12 Step D で確定済)
        atom_path = V110_V108RE_MAIN / f"atom_introduction_events_v108_re_seed{seed}.parquet"
    else:
        raise ValueError(f"Unknown condition: {condition}")

    df_atom = pd.read_parquet(atom_path)
    if condition == "v108_standard":
        # Step C v108_standard pool で filter (v10.12 Step E と同じ手順)
        step_c_path = REPO_ROOT / "developmental" / "v112" / "outputs" / "step_c" / f"receptive_cids_v108_standard_seed{seed}.parquet"
        df_v108std_cids = pd.read_parquet(step_c_path)
        keep_cids = set(df_v108std_cids["source_cid"].astype(int).tolist())
        df_atom = df_atom[df_atom["source_cid"].astype(int).isin(keep_cids)].copy()

    if df_atom.empty:
        return {"seed": seed, "condition": condition, "n_events": 0,
                "elapsed": round(time.time() - t0, 2), "skipped": True}

    # 1. build_all_paths (v107) + build_baselines (v107)
    rp = v107_pa.build_all_paths(seed, df_atom)
    bl = v107_bc.build_baselines(seed, df_atom)
    rp = _force_int_cols(rp)
    bl = _force_int_cols(bl)

    # 2. concat + compute_deltas (long phase のみ、WINDOW_DEFS 書き換え済)
    df_all = pd.concat([rp, bl], ignore_index=True, sort=False)
    df_all = _force_int_cols(df_all)
    df_with_delta = v107_bc.compute_deltas(seed, df_all)
    df_with_delta["condition_id"] = condition

    # 3. compute_baseline_excess_change
    df_excess = v107_bc.compute_baseline_excess_change(df_with_delta)
    df_excess["condition_id"] = condition

    # 4. add_adjusted_excess (global_activation_factor は v108 既存出力流用)
    factor_path = V108_MAIN / f"global_activation_factor_seed{seed}.parquet"
    df_factor = pd.read_parquet(factor_path)
    df_excess_adj = add_adjusted_excess(df_excess, df_atom, df_factor)
    df_excess_adj["condition_id"] = condition

    # 出力
    out_with_delta = V113A_OUT / f"baselines_with_delta_long_{condition}_seed{seed}.parquet"
    out_excess = V113A_OUT / f"excess_change_long_{condition}_seed{seed}.parquet"
    safe_write_parquet_v113a(df_with_delta, out_with_delta)
    safe_write_parquet_v113a(df_excess_adj, out_excess)

    return {
        "seed": seed, "condition": condition,
        "n_events": int(df_atom["event_id"].nunique()),
        "n_with_delta": int(len(df_with_delta)),
        "n_excess": int(len(df_excess_adj)),
        "size_with_delta_mb": round(out_with_delta.stat().st_size / 1024 / 1024, 3),
        "size_excess_mb": round(out_excess.stat().st_size / 1024 / 1024, 3),
        "elapsed": round(time.time() - t0, 2),
        "skipped": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_workers", type=int, default=8)
    args = ap.parse_args()

    t0 = time.time()
    print("=" * 72)
    print("v10.13.a Step H: long phase (1000-25000 step) post-process 算出")
    print(f"  WINDOW_DEFS (modified): {v107_bc.WINDOW_DEFS}")
    print(f"  ORIGINAL WINDOW_DEFS: {ORIGINAL_WINDOW_DEFS}")
    print("=" * 72)

    jobs = [(s, c) for s in SEEDS for c in CONDITION_SET]
    print(f"\n[jobs] {len(jobs)} seed × condition jobs, n_workers={args.n_workers}")
    with Pool(processes=args.n_workers) as pool:
        results = pool.map(compute_long_phase_for_seed, jobs)

    df_sum = pd.DataFrame(results)
    safe_write_parquet_v113a(df_sum, V113A_OUT / "step_h_long_phase_summary.parquet")

    print(f"\n[summary]")
    for _, r in df_sum.iterrows():
        if r["skipped"]:
            print(f"  seed={r['seed']:2d} {r['condition']:<14s}: SKIPPED")
        else:
            print(f"  seed={r['seed']:2d} {r['condition']:<14s}: "
                  f"events={r['n_events']:>5d}, with_delta={r['n_with_delta']:>6d}, "
                  f"excess={r['n_excess']:>5d}, t={r['elapsed']:.1f}s, "
                  f"size={r['size_with_delta_mb']+r['size_excess_mb']:.1f} MB")

    print(f"\n  total size: {df_sum['size_with_delta_mb'].sum() + df_sum['size_excess_mb'].sum():.1f} MB")
    print(f"  per-job mean t: {df_sum['elapsed'].mean():.2f}s")

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s")

    # サマリ JSON
    summary = {
        "step": "H",
        "method": "v107 WINDOW_DEFS monkey-patch to ('long', 1000, 25000) + compute_deltas",
        "n_seeds": len(SEEDS),
        "n_conditions": len(CONDITION_SET),
        "n_jobs": len(jobs),
        "original_window_defs": str(ORIGINAL_WINDOW_DEFS),
        "modified_window_defs": str(v107_bc.WINDOW_DEFS),
        "elapsed_sec": round(elapsed, 2),
        "total_size_mb": float(df_sum["size_with_delta_mb"].sum() + df_sum["size_excess_mb"].sum()),
    }
    with open(V113A_OUT / "step_h_summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
