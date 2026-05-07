#!/usr/bin/env python3
"""v10.9 sensitivity evaluator (Step I).

3 候補の感度評価:
  - 候補 1 (Q/C コスト):  A1 (v10.8 atom-only) vs A2 (Q-2/C+2)
  - 候補 2 (cid 選定):    A1 vs B3 (random cid)
  - 候補 3 (タイミング):  A1 vs C2 (lifecycle_synced age=200)

各 (path × window × metric) で:
  - mean_a / mean_b / delta_mean
  - Cohen's d 効果量

入力:
  - v108 main excess_change_adjusted_seed*.parquet (A1 = atom-only)
  - v109 main/smoke excess_change_adjusted_{cond}_seed*.parquet (A2/B3/C2)
  - v108 main source_events_seed*.parquet (A1 を atom-only に絞るため)

出力:
  developmental/v109/outputs/{smoke,main}/
    sensitivity_evaluation_seed{N}.parquet
    sensitivity_evaluation_all.parquet (cross-seed concat)
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
V109_ROOT = (REPO_ROOT / "developmental" / "v109").resolve()

V108_MAIN = V108_ROOT / "outputs" / "main"

OUT_ROOT = V109_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

SEEDS = list(range(24))

COMPARISONS = {
    "QC_cost":       {"a": "A1", "b": "A2"},
    "cid_selection": {"a": "A1", "b": "B3"},
    "timing":        {"a": "A1", "b": "C2"},
}

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


def assert_output_under_v109(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")


def safe_write_parquet_v109(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v109(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    var_a = float(np.var(a, ddof=1))
    var_b = float(np.var(b, ddof=1))
    pooled_var = (var_a * (len(a) - 1) + var_b * (len(b) - 1)) / (len(a) + len(b) - 2)
    if pooled_var <= 0:
        return 0.0
    return float((np.mean(b) - np.mean(a)) / np.sqrt(pooled_var))


def load_a1_atom_excess(seed: int) -> pd.DataFrame:
    """v10.8 main の excess_change_adjusted から atom_introduction_event のみを抽出."""
    df = pd.read_parquet(V108_MAIN / f"excess_change_adjusted_seed{seed}.parquet")
    src = pd.read_parquet(V108_MAIN / f"source_events_seed{seed}.parquet")
    atom_eids = set(src[src["event_source_type"] == "atom_introduction_event"]["event_id"])
    return df[df["event_id"].isin(atom_eids)].copy()


def load_v109_cond_excess(seed: int, cond: str, mode: str) -> pd.DataFrame:
    in_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    return pd.read_parquet(in_root / f"excess_change_adjusted_{cond}_seed{seed}.parquet")


def evaluate_seed(seed: int, mode: str = "main") -> pd.DataFrame:
    df_a1 = load_a1_atom_excess(seed)
    cond_dfs: dict[str, pd.DataFrame] = {}
    for cfg in COMPARISONS.values():
        cb = cfg["b"]
        if cb not in cond_dfs:
            cond_dfs[cb] = load_v109_cond_excess(seed, cb, mode)

    rows = []
    for cmp_name, cfg in COMPARISONS.items():
        df_other = cond_dfs[cfg["b"]]
        for path in ALL_PATHS:
            sub_a = df_a1[df_a1["relation_path_type"] == path]
            sub_b = df_other[df_other["relation_path_type"] == path]
            for win in WINDOWS:
                for metric in DELTA_METRICS:
                    col = f"{metric}_{win}"
                    if col not in df_a1.columns or col not in df_other.columns:
                        continue
                    a_vals = sub_a[col].dropna().values
                    b_vals = sub_b[col].dropna().values
                    if len(a_vals) == 0 or len(b_vals) == 0:
                        continue
                    rows.append({
                        "seed": int(seed), "comparison": cmp_name,
                        "cond_a": cfg["a"], "cond_b": cfg["b"],
                        "relation_path_type": path, "observation_window": win,
                        "metric": metric,
                        "n_a": int(len(a_vals)), "n_b": int(len(b_vals)),
                        "mean_a": float(a_vals.mean()),
                        "mean_b": float(b_vals.mean()),
                        "std_a": float(a_vals.std()),
                        "std_b": float(b_vals.std()),
                        "delta_mean": float(b_vals.mean() - a_vals.mean()),
                        "cohens_d": cohens_d(a_vals, b_vals),
                    })
    return pd.DataFrame(rows)


def _worker(args):
    seed, mode = args
    return evaluate_seed(seed, mode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS

    print(f"v10.9 sensitivity evaluator - mode={args.mode}, seeds={len(seeds)}, "
          f"comparisons={list(COMPARISONS)}")

    n_workers = max(1, min(args.n_workers, len(seeds)))
    t0 = time.time()
    if n_workers > 1 and len(seeds) > 1:
        with Pool(processes=n_workers) as pool:
            dfs = pool.map(_worker, [(s, args.mode) for s in seeds])
    else:
        dfs = [_worker((s, args.mode)) for s in seeds]

    for s, df in zip(seeds, dfs):
        out = out_root / f"sensitivity_evaluation_seed{s}.parquet"
        if not df.empty:
            safe_write_parquet_v109(df, out)
        print(f"  seed={s:>2}: rows={len(df)}")

    df_all = pd.concat([d for d in dfs if not d.empty], ignore_index=True)
    if not df_all.empty:
        safe_write_parquet_v109(df_all, out_root / "sensitivity_evaluation_all.parquet")
        print(f"\n=== cross-seed summary ===")
        print(f"  total rows: {len(df_all)}")
        # 主要 metric (mean_delta_C_medium) の各 comparison の path 別 effect_size 中央値
        print(f"\n  cohens_d (metric=mean_delta_C, win=medium) by comparison × path:")
        sub = df_all[(df_all["metric"] == "mean_delta_C") & (df_all["observation_window"] == "medium")]
        piv = sub.pivot_table(index="relation_path_type", columns="comparison",
                                  values="cohens_d", aggfunc="mean")
        print(piv.round(3).to_string())

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
