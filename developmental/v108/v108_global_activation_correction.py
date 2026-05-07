#!/usr/bin/env python3
"""v10.8 global activation correction + v10.7 natural baseline aggregator.

Step E の 2 機能:
1. global_activation_factor 計算 (natural events のみ、atom_intro 除外)
   - 100 step bin で count、normalize
   - excess_change に adjusted_excess 列を追加
2. v10.7 natural source_event baseline の集計
   - v10.7 excess_change から source_event 別 mean delta を抽出
   - atom_introduction_event の delta と差分計算 (Level 3.5 判定基盤)

入力: v10.8 source_events / excess_change + v10.7 excess_change
出力: developmental/v108/outputs/{smoke,main}/
  - global_activation_factor_seed*.parquet
  - excess_change_adjusted_seed*.parquet
  - natural_baseline_diff_seed*.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()

DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"
V107_MAIN_OUT = V107_ROOT / "outputs" / "main"

OUT_ROOT = V108_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

SEEDS = list(range(24))
RUN_END_STEP = 25000
STEP_BIN_SIZE = 100  # global_activation_factor の bin


def assert_output_under_v108(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V108_ROOT not in abs_path.parents and abs_path != V108_ROOT:
        raise ValueError(f"Output path {path} not under v108/")


def safe_write_parquet_v108(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v108(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def safe_read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


# ----------------------------------------------------------------------
# 1. global_activation_factor (natural events のみ)
# ----------------------------------------------------------------------
def compute_global_activation_factor(seed: int) -> pd.DataFrame:
    """100 step bin で natural events をカウント、正規化."""
    df_pulse = safe_read_csv(DIAG_ROOT / f"pulse/pulse_log_seed{seed}.csv")
    df_ing = safe_read_csv(DIAG_ROOT / f"ingestion/ingestion_events_seed{seed}.csv")
    df_alpha = safe_read_csv(DIAG_ROOT / f"integration/alpha_lifecycle_log_seed{seed}.csv")
    df_beta = safe_read_csv(DIAG_ROOT / f"integration/beta_lifecycle_log_seed{seed}.csv")
    df_bd = safe_read_csv(DIAG_ROOT / f"balance/balance_decisions_seed{seed}.csv")

    # 各 source の step を取得
    pulse_steps = df_pulse["t"].astype(int)
    ing_steps = df_ing.dropna(subset=["step"])["step"].astype(int)
    alpha_steps = df_alpha[df_alpha["event_type"] == "birth"]["step"].astype(int)
    beta_steps = df_beta[df_beta["event_type"] == "birth"]["step"].astype(int)
    cons_steps = df_bd[df_bd["decision"] == "consciousness"]["step"].astype(int)

    # 100 step bin
    bins = np.arange(0, RUN_END_STEP + STEP_BIN_SIZE + 1, STEP_BIN_SIZE)
    pulse_counts, _ = np.histogram(pulse_steps, bins=bins)
    ing_counts, _ = np.histogram(ing_steps, bins=bins)
    alpha_counts, _ = np.histogram(alpha_steps, bins=bins)
    beta_counts, _ = np.histogram(beta_steps, bins=bins)
    cons_counts, _ = np.histogram(cons_steps, bins=bins)

    total = pulse_counts + ing_counts + alpha_counts + beta_counts + cons_counts
    # 正規化 (mean 0, std 1)
    if total.std() > 0:
        normalized = (total - total.mean()) / total.std()
    else:
        normalized = np.zeros_like(total, dtype=float)

    df = pd.DataFrame({
        "seed": seed,
        "step_bin_start": bins[:-1],
        "step_bin_end": bins[1:],
        "pulse_count": pulse_counts,
        "ingestion_count": ing_counts,
        "alpha_birth_count": alpha_counts,
        "beta_birth_count": beta_counts,
        "consciousness_count": cons_counts,
        "global_activation_factor": total,
        "normalized_factor": normalized,
    })
    return df


def lookup_factor_at_step(df_factor: pd.DataFrame, step: int) -> float:
    """各 step に対応する step_bin の normalized_factor を取得."""
    bin_idx = step // STEP_BIN_SIZE
    if bin_idx < 0 or bin_idx >= len(df_factor):
        return 0.0
    return float(df_factor.iloc[bin_idx]["normalized_factor"])


# ----------------------------------------------------------------------
# 2. excess_change に adjusted 列を追加
# ----------------------------------------------------------------------
def add_adjusted_excess(df_excess: pd.DataFrame, df_src: pd.DataFrame,
                          df_factor: pd.DataFrame) -> pd.DataFrame:
    """excess_change の各行 (event_id) に対して source の timestamp で
    global_activation_factor を取得、adjusted 列を追加."""
    src_ts = df_src[["event_id", "timestamp"]].drop_duplicates("event_id")
    df = df_excess.merge(src_ts, on="event_id", how="left")
    df["normalized_factor_at_event"] = df["timestamp"].apply(
        lambda t: lookup_factor_at_step(df_factor, int(t))
    )
    # delta 列に対して adjusted を計算
    delta_cols = [c for c in df.columns if c.startswith("mean_delta_")
                    or c.startswith("mean_n_pulses_in_window_")]
    for col in delta_cols:
        df[f"adjusted_{col}"] = df[col] - df["normalized_factor_at_event"] * df[col].std()
    return df


# ----------------------------------------------------------------------
# 3. v10.7 natural source_event baseline (Level 3.5 判定基盤)
# ----------------------------------------------------------------------
def compute_natural_baseline_diff(df_excess_v108: pd.DataFrame,
                                     seed: int) -> pd.DataFrame:
    """v10.8 atom_introduction_event の excess を v10.7 natural source_event
    の同 path での mean excess と比較."""
    v107_excess_path = V107_MAIN_OUT / f"excess_change_seed{seed}.parquet"
    if not v107_excess_path.exists():
        return pd.DataFrame()
    df_v107 = pd.read_parquet(v107_excess_path)
    # v10.7 source_events から各 event の type を取得
    v107_src_path = V107_MAIN_OUT / f"source_events_seed{seed}.parquet"
    df_v107_src = pd.read_parquet(v107_src_path)
    v107_src_type = df_v107_src[["event_id", "event_source_type"]].drop_duplicates("event_id")
    df_v107_with_type = df_v107.merge(v107_src_type, on="event_id", how="left")

    # natural source_type 別 path 別の mean delta を集計
    delta_cols = [c for c in df_v107_with_type.columns if c.startswith("mean_")]
    natural_mean = df_v107_with_type.groupby(
        ["event_source_type", "relation_path_type"]
    )[delta_cols].mean().reset_index()
    natural_mean["seed"] = seed
    return natural_mean


# ----------------------------------------------------------------------
# Per-seed pipeline
# ----------------------------------------------------------------------
def run_seed_step_e(seed: int, in_root: Path, out_root: Path) -> dict:
    summary = {"seed": seed}
    t0 = time.time()

    # 1. global_activation_factor
    t = time.time()
    df_factor = compute_global_activation_factor(seed)
    safe_write_parquet_v108(df_factor,
                              out_root / f"global_activation_factor_seed{seed}.parquet")
    summary["t_factor"] = round(time.time() - t, 2)
    summary["n_step_bins"] = len(df_factor)
    summary["factor_mean"] = float(df_factor["global_activation_factor"].mean())
    summary["factor_max"] = float(df_factor["global_activation_factor"].max())

    # 2. excess_change に adjusted 列追加
    t = time.time()
    df_excess = pd.read_parquet(in_root / f"excess_change_seed{seed}.parquet")
    df_src = pd.read_parquet(in_root / f"source_events_seed{seed}.parquet")
    df_excess_adj = add_adjusted_excess(df_excess, df_src, df_factor)
    safe_write_parquet_v108(
        df_excess_adj, out_root / f"excess_change_adjusted_seed{seed}.parquet"
    )
    summary["t_adjusted"] = round(time.time() - t, 2)
    summary["n_excess_rows"] = len(df_excess_adj)

    # 3. v10.7 natural baseline
    t = time.time()
    df_natural = compute_natural_baseline_diff(df_excess, seed)
    safe_write_parquet_v108(
        df_natural, out_root / f"natural_baseline_diff_seed{seed}.parquet"
    )
    summary["t_natural"] = round(time.time() - t, 2)
    summary["n_natural_rows"] = len(df_natural)

    summary["t_total"] = round(time.time() - t0, 2)
    return summary


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    in_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root = in_root  # 同じディレクトリに追加保存
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.8 global activation correction + natural baseline - "
          f"mode={args.mode}, seeds={seeds}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        s = run_seed_step_e(seed, in_root, out_root)
        print(f"  seed={s['seed']}: factor_mean={s['factor_mean']:.1f}, "
              f"factor_max={s['factor_max']:.0f}, "
              f"step_bins={s['n_step_bins']}, "
              f"excess_rows={s['n_excess_rows']}, natural_rows={s['n_natural_rows']}, "
              f"t={s['t_total']}s "
              f"(factor={s['t_factor']}, adj={s['t_adjusted']}, nat={s['t_natural']})")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v108(df_sum, out_root / "step_e_run_summary.parquet")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
