#!/usr/bin/env python3
"""v10.9 post-process orchestrator (Step J).

3 新条件 (A2 / B3 / C2) で:
  Step C: atom_event_generator (atom_introduction_events_{cond}_seed{N}.parquet)
  Step D/H: baseline_recalculator (baselines_with_delta + excess_change_adjusted)
  Step I: sensitivity_evaluator (vs A1 baseline)
を 1 コマンドで実行。

bit-identity 検証:
  - 層 A: 同 seed 同 condition で 2 回回して MD5 一致
  - 層 B: v10.7/v10.8 main 出力の MD5 不変
  - 層 C: 出力パス v109/ 配下強制

実行例:
  python3 v109_post_process.py --mode smoke
  python3 v109_post_process.py --mode main --n_workers 24
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
V109_ROOT = (REPO_ROOT / "developmental" / "v109").resolve()

V107_MAIN_OUT = V107_ROOT / "outputs" / "main"
V108_MAIN_OUT = V108_ROOT / "outputs" / "main"

OUT_ROOT = V109_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V109_ROOT))
from v109_atom_event_generator import (  # noqa: E402
    CONDITIONS, generate_seed_atom_events, safe_write_parquet_v109,
)
from v109_baseline_recalculator import recalculate_for_condition  # noqa: E402
from v109_sensitivity_evaluator import evaluate_seed as eval_sensitivity  # noqa: E402

SEEDS = list(range(24))
DEFAULT_CONDITIONS = ["A2", "B3", "C2"]


def assert_output_under_v109(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")


# ----------------------------------------------------------------------
# bit-identity 層 B: v10.7/v10.8 main MD5 不変性検証
# ----------------------------------------------------------------------
def compute_baseline_md5(root: Path) -> dict[str, str]:
    md5_dict: dict[str, str] = {}
    for ext in ("*.csv", "*.parquet", "*.npz", "*.json"):
        for path in root.rglob(ext):
            with open(path, "rb") as f:
                md5_dict[str(path.relative_to(root))] = hashlib.md5(f.read()).hexdigest()
    return md5_dict


def verify_baseline_unchanged(label: str, baseline_md5: dict[str, str],
                                  current_md5: dict[str, str]) -> tuple[bool, list[str]]:
    diffs = []
    if set(baseline_md5.keys()) != set(current_md5.keys()):
        added = set(current_md5.keys()) - set(baseline_md5.keys())
        removed = set(baseline_md5.keys()) - set(current_md5.keys())
        diffs.extend([f"{label} ADDED: {p}" for p in added])
        diffs.extend([f"{label} REMOVED: {p}" for p in removed])
    for k in baseline_md5:
        if k in current_md5 and baseline_md5[k] != current_md5[k]:
            diffs.append(f"{label} MODIFIED: {k}")
    return (len(diffs) == 0, diffs)


# ----------------------------------------------------------------------
# Per-seed full pipeline (3 conditions)
# ----------------------------------------------------------------------
def run_seed_pipeline(seed: int, mode: str, conditions: list[str]) -> dict:
    out_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    summary = {"seed": seed, "mode": mode}
    t_start = time.time()

    # Step C: atom_event_generator (各 condition)
    t = time.time()
    for cond in conditions:
        df = generate_seed_atom_events(seed, cond)
        out = out_root / f"atom_introduction_events_{cond}_seed{seed}.parquet"
        safe_write_parquet_v109(df, out)
    summary["t_atom_events"] = round(time.time() - t, 2)

    # Step D/H: baseline_recalculator (各 condition)
    t = time.time()
    for cond in conditions:
        recalculate_for_condition(seed, cond, mode)
    summary["t_baseline"] = round(time.time() - t, 2)

    # Step I: sensitivity_evaluator (per seed)
    t = time.time()
    df_sens = eval_sensitivity(seed, mode)
    out = out_root / f"sensitivity_evaluation_seed{seed}.parquet"
    safe_write_parquet_v109(df_sens, out)
    summary["t_sensitivity"] = round(time.time() - t, 2)
    summary["n_sensitivity_rows"] = int(len(df_sens))

    summary["t_total"] = round(time.time() - t_start, 2)
    return summary


def _worker(args):
    seed, mode, conditions = args
    return run_seed_pipeline(seed, mode, conditions)


# ----------------------------------------------------------------------
# Layer A: same-seed twice MD5 reproducibility
# ----------------------------------------------------------------------
def verify_layer_a(seed: int, mode: str, conditions: list[str]) -> tuple[bool, list[str]]:
    """seed 0 で 1 回目の出力 MD5 を取り、2 回目を回して一致を確認."""
    out_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    target_files = []
    for cond in conditions:
        target_files.extend([
            out_root / f"atom_introduction_events_{cond}_seed{seed}.parquet",
            out_root / f"baselines_with_delta_{cond}_seed{seed}.parquet",
            out_root / f"excess_change_adjusted_{cond}_seed{seed}.parquet",
        ])
    target_files.append(out_root / f"sensitivity_evaluation_seed{seed}.parquet")

    md5_before = {}
    for f in target_files:
        with open(f, "rb") as fp:
            md5_before[f.name] = hashlib.md5(fp.read()).hexdigest()

    run_seed_pipeline(seed, mode, conditions)

    diffs = []
    for f in target_files:
        with open(f, "rb") as fp:
            now = hashlib.md5(fp.read()).hexdigest()
        if md5_before[f.name] != now:
            diffs.append(f"MISMATCH: {f.name}")
    return (len(diffs) == 0, diffs)


# ----------------------------------------------------------------------
# Storage 実測
# ----------------------------------------------------------------------
def measure_storage(seed: int, mode: str, conditions: list[str]) -> dict:
    out_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    by_kind = {"atom_events": 0.0, "baselines": 0.0, "excess": 0.0, "sensitivity": 0.0}
    for cond in conditions:
        for kind, prefix in [("atom_events", "atom_introduction_events"),
                                ("baselines", "baselines_with_delta"),
                                ("excess", "excess_change_adjusted")]:
            f = out_root / f"{prefix}_{cond}_seed{seed}.parquet"
            if f.exists():
                by_kind[kind] += f.stat().st_size / 1024 / 1024
    f = out_root / f"sensitivity_evaluation_seed{seed}.parquet"
    if f.exists():
        by_kind["sensitivity"] += f.stat().st_size / 1024 / 1024
    by_kind["total"] = sum(by_kind.values())
    return by_kind


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    ap.add_argument("--n_workers", type=int, default=24)
    ap.add_argument("--no_layer_a", action="store_true")
    ap.add_argument("--no_layer_b", action="store_true")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conditions:
        if c not in CONDITIONS:
            raise SystemExit(f"Unknown condition: {c}")

    print(f"v10.9 post-process orchestrator - mode={args.mode}, "
          f"seeds={len(seeds)}, conditions={conditions}, n_workers={args.n_workers}")

    # 層 B baseline MD5 取得
    layer_b_v107 = layer_b_v108 = None
    if not args.no_layer_b:
        print(f"\n=== bit-identity 層 B baseline MD5 取得 ===")
        layer_b_v107 = compute_baseline_md5(V107_MAIN_OUT)
        layer_b_v108 = compute_baseline_md5(V108_MAIN_OUT)
        print(f"  v107 main files tracked: {len(layer_b_v107)}")
        print(f"  v108 main files tracked: {len(layer_b_v108)}")

    # メインパイプライン (24 seeds 単一バッチ)
    n_workers = max(1, min(args.n_workers, len(seeds)))
    t0 = time.time()
    if n_workers > 1 and len(seeds) > 1:
        print(f"\n=== 並列実行 ({n_workers} workers、24 seeds 単一バッチ) ===")
        worker_args = [(s, args.mode, conditions) for s in seeds]
        with Pool(processes=n_workers) as pool:
            summaries = pool.map(_worker, worker_args)
        summaries = sorted(summaries, key=lambda s: s["seed"])
    else:
        print(f"\n=== 順次実行 ===")
        summaries = [run_seed_pipeline(s, args.mode, conditions) for s in seeds]

    for s in summaries:
        print(f"  seed={s['seed']:>2}: t_atom={s['t_atom_events']}s, "
              f"t_baseline={s['t_baseline']}s, t_sens={s['t_sensitivity']}s, "
              f"sens_rows={s['n_sensitivity_rows']}, total={s['t_total']}s")

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v109(df_sum, out_root / "post_process_run_summary.parquet")

    # 層 A 検証 (seed 0 のみ、smoke / main 両方で実施可)
    if not args.no_layer_a:
        print(f"\n=== bit-identity 層 A 検証 (seed 0 で 2 回目実行) ===")
        ok_a, diffs_a = verify_layer_a(seeds[0], args.mode, conditions)
        if ok_a:
            print(f"  PASS: 全出力が 2 回目で MD5 完全一致")
        else:
            print(f"  FAIL: {len(diffs_a)} mismatches:")
            for d in diffs_a[:10]:
                print(f"    {d}")
            return 1

    # 層 B 検証 (v107/v108 baseline 不変)
    if not args.no_layer_b:
        print(f"\n=== bit-identity 層 B 検証 (v10.7/v10.8 main 不変性) ===")
        ok_b1, diffs_b1 = verify_baseline_unchanged(
            "v107", layer_b_v107, compute_baseline_md5(V107_MAIN_OUT)
        )
        ok_b2, diffs_b2 = verify_baseline_unchanged(
            "v108", layer_b_v108, compute_baseline_md5(V108_MAIN_OUT)
        )
        if ok_b1:
            print(f"  PASS v107: {len(layer_b_v107)} files 全て不変")
        else:
            print(f"  FAIL v107: {len(diffs_b1)} differences")
            for d in diffs_b1[:5]:
                print(f"    {d}")
        if ok_b2:
            print(f"  PASS v108: {len(layer_b_v108)} files 全て不変")
        else:
            print(f"  FAIL v108: {len(diffs_b2)} differences")
            for d in diffs_b2[:5]:
                print(f"    {d}")
        if not (ok_b1 and ok_b2):
            return 1

    # Storage 実測 (seed 0)
    print(f"\n=== storage 実測 (seed {seeds[0]} / {args.mode}) ===")
    sz = measure_storage(seeds[0], args.mode, conditions)
    print(f"  atom_events:      {sz['atom_events']:>7.3f} MB")
    print(f"  baselines:        {sz['baselines']:>7.3f} MB")
    print(f"  excess:           {sz['excess']:>7.3f} MB")
    print(f"  sensitivity:      {sz['sensitivity']:>7.3f} MB")
    print(f"  TOTAL (per seed): {sz['total']:>7.3f} MB")
    print(f"  24 seeds 推定:    {sz['total'] * 24:>7.0f} MB ({sz['total'] * 24 / 1024:.2f} GB)")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
