#!/usr/bin/env python3
"""v10.10 n_core 層化解析 (Step H+: Taka リクエスト).

各 condition × n_core_bin で sensitivity を再計算、
全 gate 平均で見えなかった構造を n_core 層化で抽出。

n_core_bin:
  bin_2:   n_core = 2 (ペア、76% of cids)
  bin_3_4: n_core = 3-4 (小 cluster、12%)
  bin_5+:  n_core >= 5 (中 cluster、12%)

各 condition の atom_event に source_cid の n_core を attach、
excess_change_adjusted で event_id 経由で n_core 別集計、
3 種比較 (gate_effect / v110_vs_v108re / timing_axis) を n_core_bin 別に出力。

出力:
  developmental/v110/outputs/main/cross_seed/
    n_core_stratified_sensitivity.parquet
    n_core_stratified_summary.parquet
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()

V110_MAIN = V110_ROOT / "outputs" / "main"
CROSS_SEED = V110_MAIN / "cross_seed"
V108RE_MAIN = V110_ROOT / "v108_re" / "outputs" / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V110_ROOT))
from v107_baseline_constructor import _cid_meta_table  # noqa: E402
from v110_atom_event_generator import CONDITIONS  # noqa: E402
from v110_sensitivity_evaluator import build_comparisons, cohens_d  # noqa: E402

SEEDS = list(range(24))
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


def n_core_to_bin(n: int) -> str:
    if n <= 2:
        return "bin_2"
    if n <= 4:
        return "bin_3_4"
    return "bin_5plus"


def excess_path_for(condition_id: str, seed: int) -> Path:
    if condition_id == "v108_re":
        return V108RE_MAIN / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
    return V110_MAIN / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"


def atom_path_for(condition_id: str, seed: int) -> Path:
    if condition_id == "v108_re":
        return V108RE_MAIN / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"
    return V110_MAIN / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"


def load_excess_with_n_core(condition_id: str, seed: int) -> pd.DataFrame:
    """excess_change_adjusted に source_cid → n_core_bin を attach."""
    p = excess_path_for(condition_id, seed)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    a = pd.read_parquet(atom_path_for(condition_id, seed))
    if a.empty or df.empty:
        return pd.DataFrame()
    m = _cid_meta_table(seed)
    nc_lookup = dict(zip(m["cognitive_id"].astype(int),
                            m["n_core_member"].fillna(0).astype(int)))
    a["n_core"] = a["source_cid"].astype(int).map(nc_lookup).fillna(0).astype(int)
    a["n_core_bin"] = a["n_core"].apply(n_core_to_bin)
    a_sub = a[["event_id", "n_core", "n_core_bin"]].drop_duplicates("event_id")
    return df.merge(a_sub, on="event_id", how="inner")


def evaluate_seed_stratified(seed: int) -> pd.DataFrame:
    """seed × comparison × n_core_bin × path × window × metric の cohens_d."""
    comps = build_comparisons()
    cond_dfs: dict[str, pd.DataFrame] = {}
    rows = []
    for comp in comps:
        for cond in (comp["cond_a"], comp["cond_b"]):
            if cond not in cond_dfs:
                cond_dfs[cond] = load_excess_with_n_core(cond, seed)
        df_a = cond_dfs[comp["cond_a"]]
        df_b = cond_dfs[comp["cond_b"]]
        if df_a.empty or df_b.empty:
            continue
        for nc_bin in ["bin_2", "bin_3_4", "bin_5plus"]:
            df_a_bin = df_a[df_a["n_core_bin"] == nc_bin]
            df_b_bin = df_b[df_b["n_core_bin"] == nc_bin]
            if df_a_bin.empty or df_b_bin.empty:
                continue
            for path in ALL_PATHS:
                sub_a = df_a_bin[df_a_bin["relation_path_type"] == path]
                sub_b = df_b_bin[df_b_bin["relation_path_type"] == path]
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
                            "n_core_bin": nc_bin,
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


def main():
    CROSS_SEED.mkdir(parents=True, exist_ok=True)
    print(f"v10.10 n_core 層化解析 (Multi-gate × timing × n_core_bin)")
    t0 = time.time()

    from multiprocessing import Pool
    with Pool(processes=24) as pool:
        dfs = pool.map(evaluate_seed_stratified, SEEDS)

    df_all = pd.concat([d for d in dfs if not d.empty], ignore_index=True)
    print(f"  total rows: {len(df_all)}")
    safe_write_parquet_v110(df_all, CROSS_SEED / "n_core_stratified_sensitivity.parquet")

    # Summary 集計 (24 seeds 集計、comparison_type × n_core_bin × metric)
    summary = df_all.groupby(["comparison_type", "n_core_bin", "metric"]).agg(
        n_records=("cohens_d", "size"),
        cohens_d_abs_mean=("cohens_d", lambda x: x.abs().mean()),
        cohens_d_abs_max=("cohens_d", lambda x: x.abs().max()),
        cohens_d_mean=("cohens_d", "mean"),
        n_large=("cohens_d", lambda x: (x.abs() >= 0.5).sum()),
    ).reset_index()
    safe_write_parquet_v110(summary, CROSS_SEED / "n_core_stratified_summary.parquet")

    # 主要 metric (mean_delta_C × medium) の comparison_type × n_core_bin マップ
    print(f"\n=== mean_delta_C × medium の comparison_type × n_core_bin ===")
    sub = df_all[(df_all["metric"] == "mean_delta_C") &
                       (df_all["observation_window"] == "medium")]
    piv = sub.pivot_table(
        index=["comparison_type"], columns="n_core_bin",
        values="cohens_d", aggfunc="mean"
    ).round(3)
    print(piv.to_string())

    # 同じ metric × window で abs_mean
    print(f"\n=== mean_delta_C × medium の abs_mean ===")
    piv_abs = sub.pivot_table(
        index=["comparison_type"], columns="n_core_bin",
        values="cohens_d", aggfunc=lambda x: round(x.abs().mean(), 3)
    )
    print(piv_abs.to_string())

    # mean_n_pulses_in_window × short (v10.9 で大効果量だった metric)
    print(f"\n=== mean_n_pulses_in_window × short の cohens_d_mean ===")
    sub2 = df_all[(df_all["metric"] == "mean_n_pulses_in_window") &
                       (df_all["observation_window"] == "short")]
    piv2 = sub2.pivot_table(
        index=["comparison_type"], columns="n_core_bin",
        values="cohens_d", aggfunc="mean"
    ).round(3)
    print(piv2.to_string())

    # gate_effect の n_core_bin 別、path 別の cohens_d
    print(f"\n=== gate_effect (vs all_pass) × n_core_bin × path (mean_delta_C × medium) ===")
    ge = df_all[(df_all["comparison_type"] == "gate_effect") &
                       (df_all["metric"] == "mean_delta_C") &
                       (df_all["observation_window"] == "medium")]
    piv3 = ge.pivot_table(
        index="relation_path_type", columns="n_core_bin",
        values="cohens_d", aggfunc="mean"
    ).round(3)
    print(piv3.to_string())

    # timing_axis の n_core_bin 別、path 別の cohens_d
    print(f"\n=== timing_axis (t200 vs t500) × n_core_bin × path (mean_delta_C × medium) ===")
    ta = df_all[(df_all["comparison_type"] == "timing_axis") &
                       (df_all["metric"] == "mean_delta_C") &
                       (df_all["observation_window"] == "medium")]
    piv4 = ta.pivot_table(
        index="relation_path_type", columns="n_core_bin",
        values="cohens_d", aggfunc="mean"
    ).round(3)
    print(piv4.to_string())

    # v110_vs_v108re の n_core_bin 別 (mean_n_pulses_in_window × short)
    print(f"\n=== v110_vs_v108re × n_core_bin × path (mean_n_pulses_in_window × short) ===")
    vv = df_all[(df_all["comparison_type"] == "v110_vs_v108re") &
                       (df_all["metric"] == "mean_n_pulses_in_window") &
                       (df_all["observation_window"] == "short")]
    piv5 = vv.pivot_table(
        index="relation_path_type", columns="n_core_bin",
        values="cohens_d", aggfunc="mean"
    ).round(3)
    print(piv5.to_string())

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
