#!/usr/bin/env python3
"""v10.12 追加調査: window 単位ごとの paired_d / sign_test / bootstrap CI.

Web Claude → Code A 調査依頼書 (2026-05-11) 対応.

v10.12 既存 main run データ (excess_change_adjusted_*) には 3 window
(immediate=1-10, short=10-100, medium=100-1000) × {delta_C, delta_Q, n_pulses_in_window}
の集計値が既に保存されている。本スクリプトは main run 再実行せず post-process
集計のみで、各 (window × metric) で v112 vs v108_standard paired_d を formal
算出する。

主目的 (Taka 記憶 verification):
  「10 step が一番差が出た」観察事実が v10.12 データに当てはまるか確認。
  Step J は delta_C/Q を medium、n_pulses を short のみで集計したため
  window 単位の比較が抜けていた (主題盲点)。

入力:
  - v112/outputs/main/excess_change_adjusted_v112_seed{N}.parquet
  - v112/outputs/main/excess_change_adjusted_v108_standard_seed{N}.parquet

出力:
  - v112/outputs/main/window_post_process_analysis.json
  - v112/outputs/main/window_paired_analysis.parquet (window × metric × condition)

規律:
  - 物理層 frozen: ledger 不変、post-process 集計のみ
  - 主題範囲外: v10.12 主題は完了 (Step K commit 238a145)、本書は v10.13 主題選定の
    事前調査として実施、観察軸増加転換ではない
  - 神の手回避: 既存 v107 WINDOW_DEFS の immediate/short/medium をそのまま集計
  - main run 再実行なし
  - judgment 回避 (Aruism 整合)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
V112_MAIN = V112_ROOT / "outputs" / "main"

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]
WINDOWS = ["immediate", "short", "medium"]  # v107 WINDOW_DEFS
WINDOW_STEP_RANGES = {
    "immediate": "1-10 step",
    "short": "10-100 step",
    "medium": "100-1000 step",
}

RELATION_PATHS = [
    "familiarity",
    "attention_via_salience",
    "integration_alpha",
    "integration_beta",
    "temporal_coactivation",
]
EXCESS_REFERENCE = "unrelated_baseline"
PATH_EXCESS_TARGETS = [
    "familiarity", "attention_via_salience",
    "temporal_coactivation", "integration_alpha",
]

BOOTSTRAP_N = 1000
RANDOM_SEED = 12112


def assert_output_under_v112(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V112_ROOT not in abs_path.parents and abs_path != V112_ROOT:
        raise ValueError(f"Output path {path} not under v112/")


def safe_write_parquet_v112(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def safe_write_json_v112(obj, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------
# per-event 集計 (relation paths 全体の mean、path_excess vs unrelated_baseline)
# ----------------------------------------------------------------------
def compute_per_event_for_window(df_excess: pd.DataFrame, window: str) -> pd.DataFrame:
    """1 seed × 1 condition の excess_change_adjusted を per-event 集計.

    Returns DataFrame columns:
      event_id, delta_C_{window}, delta_Q_{window}, n_pulses_{window},
      path_{X}_excess_delta_C_{window} for X in PATH_EXCESS_TARGETS
    """
    dc_col = f"mean_delta_C_{window}"
    dq_col = f"mean_delta_Q_{window}"
    np_col = f"mean_n_pulses_in_window_{window}"

    rows = []
    for event_id, sub in df_excess.groupby("event_id"):
        row = {"event_id": event_id}
        rp_sub = sub[sub["relation_path_type"].isin(RELATION_PATHS)]
        if not rp_sub.empty:
            row[f"delta_C_{window}"] = float(rp_sub[dc_col].mean())
            row[f"delta_Q_{window}"] = float(rp_sub[dq_col].mean())
            row[f"n_pulses_{window}"] = float(rp_sub[np_col].mean())
        else:
            row[f"delta_C_{window}"] = np.nan
            row[f"delta_Q_{window}"] = np.nan
            row[f"n_pulses_{window}"] = np.nan

        ref_row = sub[sub["relation_path_type"] == EXCESS_REFERENCE]
        ref_dc = float(ref_row[dc_col].iloc[0]) if not ref_row.empty else np.nan
        for path in PATH_EXCESS_TARGETS:
            path_row = sub[sub["relation_path_type"] == path]
            if not path_row.empty and not np.isnan(ref_dc):
                row[f"path_{path}_excess_delta_C_{window}"] = (
                    float(path_row[dc_col].iloc[0]) - ref_dc
                )
            else:
                row[f"path_{path}_excess_delta_C_{window}"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# per-seed 集計 (全 window × 全 metric)
# ----------------------------------------------------------------------
def collect_per_seed_means(condition_id: str) -> pd.DataFrame:
    """24 seeds × 1 condition × 3 window で per-event 集計 → per-seed mean.

    Returns: DataFrame with columns [seed, condition_id, {metric}_per_seed_mean]
    """
    rows = []
    for seed in SEEDS:
        excess_path = V112_MAIN / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
        df_excess = pd.read_parquet(excess_path)
        row = {"seed": int(seed), "condition_id": condition_id}
        for window in WINDOWS:
            df_pe = compute_per_event_for_window(df_excess, window)
            for metric in [f"delta_C_{window}", f"delta_Q_{window}", f"n_pulses_{window}"]:
                row[f"{metric}_per_seed_mean"] = float(df_pe[metric].mean())
            for path in PATH_EXCESS_TARGETS:
                col = f"path_{path}_excess_delta_C_{window}"
                row[f"{col}_per_seed_mean"] = float(df_pe[col].mean()) if col in df_pe.columns else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# paired_d / sign_test / bootstrap CI 95%
# ----------------------------------------------------------------------
def paired_analysis(diff_per_seed: np.ndarray, metric: str, window: str) -> dict:
    n = int(len(diff_per_seed))
    valid = diff_per_seed[~np.isnan(diff_per_seed)]
    n_valid = int(len(valid))
    if n_valid < 2:
        return {"window": window, "metric": metric, "n_seeds": n, "n_valid": n_valid,
                "skipped": True}

    mean_diff = float(valid.mean())
    std_diff = float(valid.std(ddof=1))
    paired_d = float(mean_diff / std_diff) if std_diff > 0 else float("nan")

    n_positive = int(np.sum(valid > 0))
    n_negative = int(np.sum(valid < 0))
    n_zero = int(np.sum(valid == 0))
    n_nonzero = n_positive + n_negative
    if n_nonzero >= 1:
        try:
            sign_p = float(scipy_stats.binomtest(
                k=n_positive, n=n_nonzero, p=0.5, alternative="two-sided"
            ).pvalue)
        except Exception:
            sign_p = float("nan")
    else:
        sign_p = float("nan")

    rng = np.random.default_rng(RANDOM_SEED)
    boot_means = []
    for _ in range(BOOTSTRAP_N):
        sample = rng.choice(valid, size=n_valid, replace=True)
        boot_means.append(float(sample.mean()))
    boot_arr = np.array(boot_means)
    ci_lower = float(np.percentile(boot_arr, 2.5))
    ci_upper = float(np.percentile(boot_arr, 97.5))

    return {
        "window": window,
        "metric": metric,
        "n_seeds": n,
        "n_valid": n_valid,
        "skipped": False,
        "paired_diff_mean": mean_diff,
        "paired_diff_std": std_diff,
        "paired_d": paired_d,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "n_zero": n_zero,
        "sign_p_two_sided": sign_p,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "crosses_zero": (ci_lower < 0 < ci_upper),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    args = ap.parse_args()

    t0 = time.time()
    print("=" * 72)
    print("v10.12 追加調査: window 単位ごとの paired_d post-process")
    print("依頼: Web Claude/Taka (2026-05-11)、v10.13 主題選定の事前調査")
    print("=" * 72)

    print(f"\n[input] excess_change_adjusted_*_seed[0-23].parquet "
          f"(3 windows × 9 metric per condition)")

    # 1. per-seed mean を 2 condition × 3 window × 7 metric で集計
    print(f"\n=== 1. per-seed mean 集計 (24 seeds × 2 conditions × 3 windows × 7 metric) ===")
    df_v112 = collect_per_seed_means("v112")
    df_v108 = collect_per_seed_means("v108_standard")
    print(f"  v112: {len(df_v112)} rows, v108_standard: {len(df_v108)} rows")

    # 2. paired_d / sign_test / bootstrap CI per (window × metric)
    print(f"\n=== 2. paired analysis per (window × metric) ===")
    paired_results = []
    base_metrics = ["delta_C", "delta_Q", "n_pulses"]
    path_metrics = [f"path_{p}_excess_delta_C" for p in PATH_EXCESS_TARGETS]
    all_metrics = base_metrics + path_metrics

    for window in WINDOWS:
        for metric in all_metrics:
            col = f"{metric}_{window}_per_seed_mean"
            if col not in df_v112.columns or col not in df_v108.columns:
                continue
            v112_per_seed = df_v112.sort_values("seed")[col].values
            v108_per_seed = df_v108.sort_values("seed")[col].values
            diff = v112_per_seed - v108_per_seed
            r = paired_analysis(diff, metric, window)
            paired_results.append(r)

    df_paired = pd.DataFrame(paired_results)

    # 3. 結果出力 (window × metric テーブル)
    print(f"\n=== 3. paired_d × bootstrap CI (window 別、base metrics) ===")
    print(f"{'metric':<12s} {'window':<10s} {'paired_d':>9s} {'sign_p':>8s} {'CI_lower':>10s} {'CI_upper':>10s} {'crosses_zero':>14s}")
    for metric in base_metrics:
        for window in WINDOWS:
            r = df_paired[(df_paired["metric"] == metric) & (df_paired["window"] == window)]
            if r.empty: continue
            r = r.iloc[0]
            mark = " 0!" if not r["crosses_zero"] else "   "
            print(f"  {metric:<10s} {window:<10s} {r['paired_d']:+9.4f} {r['sign_p_two_sided']:>8.4f}  "
                  f"[{r['ci_lower']:+9.4f}, {r['ci_upper']:+9.4f}] {mark}")

    print(f"\n=== 4. paired_d × bootstrap CI (window 別、path_excess metrics) ===")
    print(f"{'path':<25s} {'window':<10s} {'paired_d':>9s} {'sign_p':>8s} {'CI_lower':>10s} {'CI_upper':>10s} {'crosses_zero':>14s}")
    for path in PATH_EXCESS_TARGETS:
        metric = f"path_{path}_excess_delta_C"
        for window in WINDOWS:
            r = df_paired[(df_paired["metric"] == metric) & (df_paired["window"] == window)]
            if r.empty: continue
            r = r.iloc[0]
            mark = " 0!" if not r["crosses_zero"] else "   "
            print(f"  {path:<23s} {window:<10s} {r['paired_d']:+9.4f} {r['sign_p_two_sided']:>8.4f}  "
                  f"[{r['ci_lower']:+9.4f}, {r['ci_upper']:+9.4f}] {mark}")

    # 4. window 別 effect_size 最大値ランキング
    print(f"\n=== 5. CI が 0 を跨がない (= 頑健) cells (window × metric × condition pair) ===")
    robust = df_paired[~df_paired["crosses_zero"]]
    if not robust.empty:
        for _, r in robust.iterrows():
            print(f"  {r['metric']:<55s} ({r['window']:<10s}): "
                  f"paired_d={r['paired_d']:+.4f}, sign_p={r['sign_p_two_sided']:.4f}, "
                  f"CI=[{r['ci_lower']:+.4f}, {r['ci_upper']:+.4f}]")
    else:
        print(f"  (頑健 cells なし)")

    # 5. 出力
    safe_write_parquet_v112(df_paired,
                              V112_MAIN / "window_paired_analysis.parquet")
    safe_write_parquet_v112(df_v112,
                              V112_MAIN / "window_per_seed_v112.parquet")
    safe_write_parquet_v112(df_v108,
                              V112_MAIN / "window_per_seed_v108_standard.parquet")

    out = {
        "metadata": {
            "subject_context": "v10.12 主題完了 (commit 238a145、Step K)、本書は v10.13 主題選定の事前調査",
            "request_source": "Web Claude → Code A (2026-05-11)、Taka 整理: pulse にこだわる理由はない、10 step が差を出した記憶",
            "method": "v10.12 既存 main run データの post-process のみ (main run 再実行なし、層 B/C 不変)",
            "windows": WINDOWS,
            "window_step_ranges": WINDOW_STEP_RANGES,
            "v107_window_defs": "WINDOW_DEFS = [(immediate, 1, 10), (short, 10, 100), (medium, 100, 1000)]",
            "missing_window_units": [
                "1 step (single step) - 既存データに含まれない、compute_deltas 再計算が必要",
                "50 step - 既存データに含まれない、compute_deltas 拡張で算出可",
                "long (1000-5000 step) - 既存データに含まれない (v10.10 で集計対象外明示済)",
            ],
            "bootstrap_n_iter": int(BOOTSTRAP_N),
            "code_a_discipline": "judgment 回避 (success/fail 判定なし)、観察事実のみ記録、Web Claude/Taka 主題評価素材",
        },
        "paired_analysis_table": paired_results,
        "robust_cells_count": int(len(robust)),
        "robust_cells": robust.to_dict(orient="records") if not robust.empty else [],
        "computation_metadata": {
            "elapsed_sec": round(time.time() - t0, 2),
            "n_paired_analyses": int(len(paired_results)),
            "n_windows": int(len(WINDOWS)),
            "n_base_metrics": int(len(base_metrics)),
            "n_path_metrics": int(len(path_metrics)),
        },
    }
    safe_write_json_v112(out, V112_MAIN / "window_post_process_analysis.json")

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s")
    print(f"  output = window_post_process_analysis.json + window_paired_analysis.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
