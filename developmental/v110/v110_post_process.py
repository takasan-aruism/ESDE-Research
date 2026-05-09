#!/usr/bin/env python3
"""v10.10 post-process orchestrator (28 conditions、Multi-gate × timing).

Steps:
  C: atom_event_generator (28 conditions × N seeds)
  D: baseline_recalculator (28 conditions × N seeds)
  E: sensitivity_evaluator (per seed)
  bit-identity 層 A: 同 seed 2 回実行 MD5 一致
  bit-identity 層 B: v107/v108/v109 既存出力不変
  bit-identity 層 C: 出力先 v110/ 配下強制
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
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()

V107_MAIN = V107_ROOT / "outputs" / "main"
V108_MAIN = V108_ROOT / "outputs" / "main"
V109_MAIN = V109_ROOT / "outputs" / "main"

OUT_ROOT = V110_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V110_ROOT))
from v110_atom_event_generator import (  # noqa: E402
    CONDITIONS, generate_seed_atom_events, out_path_for, safe_write_parquet_v110,
)
from v110_baseline_recalculator import recalculate_for_condition  # noqa: E402
from v110_sensitivity_evaluator import (  # noqa: E402
    build_comparisons, evaluate_seed as eval_sensitivity,
)

SEEDS = list(range(24))


def compute_baseline_md5(root: Path) -> dict[str, str]:
    md5_dict: dict[str, str] = {}
    for ext in ("*.csv", "*.parquet", "*.npz", "*.json"):
        for path in root.rglob(ext):
            with open(path, "rb") as f:
                md5_dict[str(path.relative_to(root))] = hashlib.md5(f.read()).hexdigest()
    return md5_dict


def verify_unchanged(label: str, baseline: dict, current: dict) -> tuple[bool, list[str]]:
    diffs = []
    if set(baseline) != set(current):
        added = set(current) - set(baseline)
        removed = set(baseline) - set(current)
        diffs.extend([f"{label} ADDED: {p}" for p in added])
        diffs.extend([f"{label} REMOVED: {p}" for p in removed])
    for k in baseline:
        if k in current and baseline[k] != current[k]:
            diffs.append(f"{label} MODIFIED: {k}")
    return (len(diffs) == 0, diffs)


def run_seed_pipeline(seed: int, mode: str, conditions: list[str]) -> dict:
    summary = {"seed": seed, "mode": mode}
    t_start = time.time()

    # Step C: atom_event_generator
    t = time.time()
    for cond in conditions:
        df = generate_seed_atom_events(seed, cond)
        out = out_path_for(cond, seed, mode)
        safe_write_parquet_v110(df, out)
    summary["t_atom_events"] = round(time.time() - t, 2)

    # Step D: baseline_recalculator
    t = time.time()
    for cond in conditions:
        recalculate_for_condition(seed, cond, mode)
    summary["t_baseline"] = round(time.time() - t, 2)

    # Step E: sensitivity_evaluator
    t = time.time()
    comps = build_comparisons()
    df_sens = eval_sensitivity(seed, mode, comps)
    out_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    if not df_sens.empty:
        safe_write_parquet_v110(df_sens, out_root / f"sensitivity_evaluation_seed{seed}.parquet")
    summary["t_sensitivity"] = round(time.time() - t, 2)
    summary["n_sensitivity_rows"] = int(len(df_sens))

    summary["t_total"] = round(time.time() - t_start, 2)
    return summary


def _worker(args):
    seed, mode, conditions = args
    return run_seed_pipeline(seed, mode, conditions)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--n_workers", type=int, default=24)
    ap.add_argument("--no_layer_a", action="store_true")
    ap.add_argument("--no_layer_b", action="store_true")
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS
    conditions = list(CONDITIONS.keys())
    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    print(f"v10.10 post-process - mode={args.mode}, seeds={len(seeds)}, "
          f"conditions={len(conditions)}, n_workers={args.n_workers}")

    # 層 B baseline MD5 取得
    layer_b: dict[str, dict] = {}
    if not args.no_layer_b:
        print(f"\n=== bit-identity 層 B: baseline MD5 取得 ===")
        for label, root in [("v107", V107_MAIN), ("v108", V108_MAIN), ("v109", V109_MAIN)]:
            layer_b[label] = compute_baseline_md5(root)
            print(f"  {label} files tracked: {len(layer_b[label])}")

    n_workers = max(1, min(args.n_workers, len(seeds)))
    t0 = time.time()
    if n_workers > 1 and len(seeds) > 1:
        print(f"\n=== 並列実行 ({n_workers} workers、24 seeds 単一バッチ) ===")
        with Pool(processes=n_workers) as pool:
            summaries = pool.map(_worker, [(s, args.mode, conditions) for s in seeds])
        summaries = sorted(summaries, key=lambda s: s["seed"])
    else:
        print(f"\n=== 順次実行 ===")
        summaries = [run_seed_pipeline(s, args.mode, conditions) for s in seeds]

    for s in summaries:
        print(f"  seed={s['seed']:>2}: t_atom={s['t_atom_events']}s, "
              f"t_baseline={s['t_baseline']}s, t_sens={s['t_sensitivity']}s, "
              f"sens_rows={s['n_sensitivity_rows']}, total={s['t_total']}s")

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v110(df_sum, out_root / "post_process_run_summary.parquet")

    # 層 A 検証 (seed 0 で 2 回目実行)
    if not args.no_layer_a:
        print(f"\n=== bit-identity 層 A 検証 (seed 0 で 2 回目実行) ===")
        target_files = []
        for cond in conditions:
            target_files.append(out_path_for(cond, seeds[0], args.mode))
            if cond == "v108_re":
                base = V110_ROOT / "v108_re" / "outputs" / args.mode
            else:
                base = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
            for kind in ("baselines_with_delta", "excess_change_adjusted"):
                target_files.append(base / f"{kind}_{cond}_seed{seeds[0]}.parquet")
        target_files.append(out_root / f"sensitivity_evaluation_seed{seeds[0]}.parquet")
        target_files = [f for f in target_files if f.exists()]
        md5_before = {f.name: hashlib.md5(open(f, "rb").read()).hexdigest() for f in target_files}
        run_seed_pipeline(seeds[0], args.mode, conditions)
        diffs = []
        for f in target_files:
            now = hashlib.md5(open(f, "rb").read()).hexdigest()
            if md5_before[f.name] != now:
                diffs.append(f.name)
        if diffs:
            print(f"  FAIL: {len(diffs)} mismatches")
            for d in diffs[:10]:
                print(f"    {d}")
            return 1
        print(f"  PASS: {len(target_files)} files 全て MD5 一致")

    # 層 B 検証
    if not args.no_layer_b:
        print(f"\n=== bit-identity 層 B 検証 ===")
        all_pass = True
        for label, root in [("v107", V107_MAIN), ("v108", V108_MAIN), ("v109", V109_MAIN)]:
            ok, diffs = verify_unchanged(label, layer_b[label], compute_baseline_md5(root))
            if ok:
                print(f"  PASS {label}: {len(layer_b[label])} files 全て不変")
            else:
                print(f"  FAIL {label}: {len(diffs)} differences")
                for d in diffs[:5]:
                    print(f"    {d}")
                all_pass = False
        if not all_pass:
            return 1

    # storage 実測 (seed 0)
    print(f"\n=== storage 実測 (seed {seeds[0]} / {args.mode}) ===")
    sz_total = 0.0
    for cond in conditions:
        if cond == "v108_re":
            base = V110_ROOT / "v108_re" / "outputs" / args.mode
        else:
            base = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
        for kind in ("atom_introduction_events", "baselines_with_delta", "excess_change_adjusted"):
            f = base / f"{kind}_{cond}_seed{seeds[0]}.parquet"
            if f.exists():
                sz_total += f.stat().st_size / 1024 / 1024
    sens_f = out_root / f"sensitivity_evaluation_seed{seeds[0]}.parquet"
    if sens_f.exists():
        sz_total += sens_f.stat().st_size / 1024 / 1024
    print(f"  per seed total: {sz_total:.2f} MB")
    print(f"  24 seeds 推定:  {sz_total * 24:.0f} MB ({sz_total * 24 / 1024:.2f} GB)")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
