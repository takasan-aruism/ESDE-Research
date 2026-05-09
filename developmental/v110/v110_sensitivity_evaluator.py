#!/usr/bin/env python3
"""v10.10 sensitivity evaluator (Multi-gate × timing 二次元).

3 種比較:
  1. gate 効果: 各 v110_{gate}_t{age} vs v110_all_pass_t{age}
  2. v10.10 vs v10.8: 各 v110_{gate}_t200 vs v108_re
  3. timing 軸: 各 v110_{gate}_t200 vs v110_{gate}_t500

Cohen's d で評価、24 seeds 方向一致集計を後段 (Step H) で実施。
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
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()

OUT_ROOT = V110_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"
V108RE_ROOT = V110_ROOT / "v108_re" / "outputs"

SEEDS = list(range(24))
GATES = ["ABC", "ABc", "AB", "B", "Bc", "AC", "BC", "A", "all_pass"]
AGE_TARGETS = [200, 300, 500]
WINDOWS = ["immediate", "short", "medium"]
DELTA_METRICS = [
    "mean_delta_R_familiarity", "mean_delta_Q", "mean_delta_C",
    "mean_delta_n_alphas", "mean_delta_n_observed", "mean_n_pulses_in_window",
]
ALL_PATHS = [
    "familiarity", "attention_via_salience", "integration_alpha",
    "integration_beta", "temporal_coactivation",
    "unrelated_baseline", "same_step_random_baseline", "matched_baseline",
    "same_integration_low_familiarity_baseline",
    "high_familiarity_outside_integration_baseline",
]


def assert_output_under_v110(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V110_ROOT not in abs_path.parents and abs_path != V110_ROOT:
        raise ValueError(f"Output path {path} not under v110/")


def safe_write_parquet_v110(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v110(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def build_comparisons() -> list[dict]:
    """3 種比較を組み立てる。"""
    comps = []
    # 1. gate 効果 (各 gate × timing vs all_pass × 同 timing)
    for at in AGE_TARGETS:
        for g in GATES:
            if g == "all_pass":
                continue
            comps.append({
                "comparison_type": "gate_effect",
                "name": f"{g}_t{at}_vs_all_pass_t{at}",
                "cond_a": f"v110_all_pass_t{at}",
                "cond_b": f"v110_{g}_t{at}",
            })
    # 2. v110 vs v108_re (各 gate × t200)
    for g in GATES:
        comps.append({
            "comparison_type": "v110_vs_v108re",
            "name": f"{g}_t200_vs_v108re",
            "cond_a": "v108_re",
            "cond_b": f"v110_{g}_t200",
        })
    # 3. timing 軸 (各 gate × t200 vs t500)
    for g in GATES:
        comps.append({
            "comparison_type": "timing_axis",
            "name": f"{g}_t200_vs_t500",
            "cond_a": f"v110_{g}_t200",
            "cond_b": f"v110_{g}_t500",
        })
    return comps


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    var_a = float(np.var(a, ddof=1))
    var_b = float(np.var(b, ddof=1))
    pooled = (var_a * (len(a) - 1) + var_b * (len(b) - 1)) / (len(a) + len(b) - 2)
    if pooled <= 0:
        return 0.0
    return float((np.mean(b) - np.mean(a)) / np.sqrt(pooled))


def _excess_path_for(condition_id: str, seed: int, mode: str) -> Path:
    if condition_id == "v108_re":
        return V108RE_ROOT / mode / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
    root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    return root / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"


def evaluate_seed(seed: int, mode: str, comparisons: list[dict]) -> pd.DataFrame:
    """seed 別に各 comparison × path × window × metric の cohens_d を出力."""
    cond_dfs: dict[str, pd.DataFrame] = {}
    rows = []
    for comp in comparisons:
        for cond in (comp["cond_a"], comp["cond_b"]):
            if cond in cond_dfs:
                continue
            p = _excess_path_for(cond, seed, mode)
            if p.exists():
                cond_dfs[cond] = pd.read_parquet(p)
            else:
                cond_dfs[cond] = pd.DataFrame()

        df_a = cond_dfs[comp["cond_a"]]
        df_b = cond_dfs[comp["cond_b"]]
        if df_a.empty or df_b.empty:
            continue
        for path in ALL_PATHS:
            sub_a = df_a[df_a["relation_path_type"] == path]
            sub_b = df_b[df_b["relation_path_type"] == path]
            for win in WINDOWS:
                for metric in DELTA_METRICS:
                    col = f"{metric}_{win}"
                    if col not in df_a.columns or col not in df_b.columns:
                        continue
                    a_vals = sub_a[col].dropna().values
                    b_vals = sub_b[col].dropna().values
                    if len(a_vals) == 0 or len(b_vals) == 0:
                        continue
                    rows.append({
                        "seed": int(seed),
                        "comparison_type": comp["comparison_type"],
                        "comparison_name": comp["name"],
                        "cond_a": comp["cond_a"], "cond_b": comp["cond_b"],
                        "relation_path_type": path,
                        "observation_window": win,
                        "metric": metric,
                        "n_a": int(len(a_vals)), "n_b": int(len(b_vals)),
                        "mean_a": float(a_vals.mean()),
                        "mean_b": float(b_vals.mean()),
                        "delta_mean": float(b_vals.mean() - a_vals.mean()),
                        "cohens_d": cohens_d(a_vals, b_vals),
                    })
    return pd.DataFrame(rows)


def _worker(args):
    seed, mode, comparisons = args
    return evaluate_seed(seed, mode, comparisons)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS
    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    comps = build_comparisons()
    print(f"v10.10 sensitivity evaluator - mode={args.mode}, "
          f"seeds={len(seeds)}, comparisons={len(comps)}, n_workers={args.n_workers}")

    n_workers = max(1, min(args.n_workers, len(seeds)))
    t0 = time.time()
    if n_workers > 1 and len(seeds) > 1:
        with Pool(processes=n_workers) as pool:
            dfs = pool.map(_worker, [(s, args.mode, comps) for s in seeds])
    else:
        dfs = [_worker((s, args.mode, comps)) for s in seeds]

    for s, df in zip(seeds, dfs):
        if not df.empty:
            safe_write_parquet_v110(df, out_root / f"sensitivity_evaluation_seed{s}.parquet")
        print(f"  seed={s:>2}: rows={len(df)}")

    df_all = pd.concat([d for d in dfs if not d.empty], ignore_index=True)
    if not df_all.empty:
        safe_write_parquet_v110(df_all, out_root / "sensitivity_evaluation_all.parquet")
        print(f"\n=== summary by comparison_type ===")
        for t in df_all["comparison_type"].unique():
            sub = df_all[df_all["comparison_type"] == t]
            print(f"  {t:<20s}: rows={len(sub)}, "
                  f"abs_mean={sub['cohens_d'].abs().mean():.3f}, "
                  f"abs_max={sub['cohens_d'].abs().max():.3f}")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
