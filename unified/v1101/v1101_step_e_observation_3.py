#!/usr/bin/env python3
"""v1101 Step E — 観察 3「補助平均統計」CID / Integration / ESDE の 3 単位

Taka 確定: 観察 3 は補助、観察 1・2 が主役。Integration は平均化せず分布で示す。

入力 (read-only):
  developmental/v106/outputs/main/cid_atom_sim_matrix_seed{0..23}.parquet
  developmental/v106/outputs/main/beta_atom_aggregate_seed{0..23}.csv
  developmental/v106/outputs/main/stratified/alpha_atom_aggregate_stratified_seed{0..23}.csv
  developmental/v106/outputs/main/{event,pulse,step10,window}_trajectory/cross_seed_*.csv

齟齬発見 (Step E):
  Integration の member_cids 個別 cid id list は v10.x outputs に persistence されていない
  (beta_atom_aggregate は n_member_cids 個数のみ、cid id 列なし)
  → 段階 1 では top-K 集約 + Integration size 分布 + atom popularity に範囲調整
  → member_cids 完全 atom ベクトル分布は段階 2 (新規 main run 不要、要再生)

出力:
  unified/v1101/outputs/main/observation_3_cid_atom_distribution.parquet
  unified/v1101/outputs/main/observation_3_integration_summary.parquet
  unified/v1101/outputs/main/observation_3_esde_aggregate.parquet
"""
from __future__ import annotations
import time
from pathlib import Path

import numpy as np
import pandas as pd

V106_MAIN = Path("/home/takasan/esde/ESDE-Research/developmental/v106/outputs/main")
V1101_OUT = Path("/home/takasan/esde/ESDE-Research/unified/v1101/outputs/main")
SEEDS = list(range(24))
SIM_THRESHOLDS = [0.3, 0.4, 0.5, 0.6]


def step_e1_cid_atom_distribution() -> pd.DataFrame:
    """CID 単位: 24 seeds × ~228 cids × 326 atoms cosine 類似度分布の per-atom 集計."""
    parts = []
    for seed in SEEDS:
        p = V106_MAIN / f"cid_atom_sim_matrix_seed{seed}.parquet"
        df = pd.read_parquet(p)
        # df: rows = cids, cols = ['seed', 'cid', atom1, atom2, ..., atomN]
        atom_cols = [c for c in df.columns if c not in ("seed", "cid")]
        # Melt to long form: (seed, cid, atom, sim)
        long = df.melt(id_vars=["seed", "cid"], value_vars=atom_cols,
                       var_name="atom", value_name="sim")
        parts.append(long)
    big = pd.concat(parts, ignore_index=True)

    # Per-atom statistics across all (seed, cid)
    agg = big.groupby("atom")["sim"].agg(
        n_obs="count",
        sim_mean="mean",
        sim_std="std",
        sim_min="min",
        sim_q25=lambda s: s.quantile(0.25),
        sim_median="median",
        sim_q75=lambda s: s.quantile(0.75),
        sim_q90=lambda s: s.quantile(0.90),
        sim_q99=lambda s: s.quantile(0.99),
        sim_max="max",
    ).reset_index()
    # Cids with sim > threshold counts
    for th in SIM_THRESHOLDS:
        agg[f"n_cids_sim_gt_{th}"] = big.groupby("atom")["sim"].apply(lambda s: (s > th).sum()).values
    # category extraction (atom = "CAT.tag")
    agg["category"] = agg["atom"].str.split(".").str[0]
    agg = agg.sort_values("sim_mean", ascending=False).reset_index(drop=True)
    agg.to_parquet(V1101_OUT / "observation_3_cid_atom_distribution.parquet", index=False)
    return agg


def step_e2_integration_summary() -> pd.DataFrame:
    """Integration 単位: β/α top-K 集約 + Integration size 分布 + atom popularity (cross-seed)."""
    # 1) β集計: per Integration の top_atom 分布 (cross-seed)
    beta_parts = []
    for seed in SEEDS:
        p = V106_MAIN / f"beta_atom_aggregate_seed{seed}.csv"
        df = pd.read_csv(p)
        beta_parts.append(df)
    beta_all = pd.concat(beta_parts, ignore_index=True)
    # Per top_atom: how many Integration β's have it as top, across 24 seeds
    beta_atom_pop = beta_all.groupby("top_atom").agg(
        n_betas_as_top=("beta_id", "count"),
        n_seeds_appeared=("seed", "nunique"),
        n_member_cids_mean=("n_member_cids", "mean"),
        n_member_cids_max=("n_member_cids", "max"),
        n_member_alphas_mean=("n_member_alphas", "mean"),
        max_atom_sim_mean=("max_atom_sim", "mean"),
        max_atom_sim_max=("max_atom_sim", "max"),
    ).reset_index().rename(columns={"top_atom": "atom"})
    beta_atom_pop["unit"] = "beta"

    # 2) α集計: per (seed, pattern_class) の dominant_atom 分布
    alpha_parts = []
    for seed in SEEDS:
        p = V106_MAIN / "stratified" / f"alpha_atom_aggregate_stratified_seed{seed}.csv"
        df = pd.read_csv(p)
        alpha_parts.append(df)
    alpha_all = pd.concat(alpha_parts, ignore_index=True)
    alpha_atom_pop = alpha_all.groupby("dominant_atom").agg(
        n_alpha_groups_as_dominant=("pattern_class", "count"),
        n_seeds_appeared=("seed", "nunique"),
        n_alphas_mean=("n_alphas", "mean"),
        n_member_cid_observations_mean=("n_member_cid_observations", "mean"),
        dominant_atom_sim_mean=("dominant_atom_sim", "mean"),
        dominant_atom_sim_max=("dominant_atom_sim", "max"),
    ).reset_index().rename(columns={"dominant_atom": "atom"})
    alpha_atom_pop["unit"] = "alpha_stratified"

    # Combine: long form per (unit, atom)
    rows = []
    for _, r in beta_atom_pop.iterrows():
        rows.append({
            "unit": "beta",
            "atom": r["atom"],
            "n_appearances_as_top": int(r["n_betas_as_top"]),
            "n_seeds_appeared": int(r["n_seeds_appeared"]),
            "size_mean": float(r["n_member_cids_mean"]),
            "size_max": int(r["n_member_cids_max"]),
            "sim_mean": float(r["max_atom_sim_mean"]),
            "sim_max": float(r["max_atom_sim_max"]),
        })
    for _, r in alpha_atom_pop.iterrows():
        rows.append({
            "unit": "alpha_stratified",
            "atom": r["atom"],
            "n_appearances_as_top": int(r["n_alpha_groups_as_dominant"]),
            "n_seeds_appeared": int(r["n_seeds_appeared"]),
            "size_mean": float(r["n_member_cid_observations_mean"]),
            "size_max": int(alpha_all.loc[alpha_all["dominant_atom"] == r["atom"], "n_member_cid_observations"].max()),
            "sim_mean": float(r["dominant_atom_sim_mean"]),
            "sim_max": float(r["dominant_atom_sim_max"]),
        })
    summary = pd.DataFrame(rows).sort_values(["unit", "n_appearances_as_top"], ascending=[True, False])
    summary.to_parquet(V1101_OUT / "observation_3_integration_summary.parquet", index=False)

    # Integration size 分布 (β)
    size_dist = beta_all["n_member_cids"].describe(percentiles=[.25, .5, .75, .9, .99]).to_frame().T
    size_dist["unit"] = "beta"
    size_dist["total_integrations"] = len(beta_all)
    size_dist["n_seeds"] = beta_all["seed"].nunique()

    return summary


def step_e3_esde_aggregate() -> pd.DataFrame:
    """ESDE 単位: cross_seed_* を統合した 4 解像度 atom 隆盛集約."""
    # event resolution
    f_event = V106_MAIN / "event_trajectory" / "cross_seed_event_atom_distribution.csv"
    df_event = pd.read_csv(f_event).rename(columns={"n_records": "n_records_event"})
    df_event["resolution"] = "event"
    # pulse resolution
    f_pulse = V106_MAIN / "pulse_trajectory" / "cross_seed_pulse_atom_distribution.csv"
    df_pulse = pd.read_csv(f_pulse).rename(columns={"n_pulse_records": "n_records_event"})
    df_pulse["resolution"] = "pulse"
    # step10 resolution
    f_step10 = V106_MAIN / "step10_trajectory" / "cross_seed_step10_atom_distribution.csv"
    df_step10 = pd.read_csv(f_step10).rename(columns={"n_records": "n_records_event"})
    df_step10["resolution"] = "step10"
    # window resolution (dynamic_atom_emergence has different schema, use first_window/last_window)
    f_window = V106_MAIN / "window_trajectory" / "cross_seed_dynamic_atom_emergence.csv"
    df_window = pd.read_csv(f_window).rename(columns={"n_rank1_appearances": "n_records_event"})
    df_window["resolution"] = "window"

    common_cols = ["atom", "category", "resolution", "n_records_event", "n_seeds_appeared", "n_unique_cids"]
    parts = []
    for d in (df_event, df_pulse, df_step10, df_window):
        keep = [c for c in common_cols if c in d.columns]
        # Add rank_1_sim_mean / rank_1_sim_max if available
        for opt in ("rank_1_sim_mean", "rank_1_sim_max", "n_windows_appeared", "first_window", "last_window"):
            if opt in d.columns:
                keep.append(opt)
        parts.append(d[keep])
    esde = pd.concat(parts, ignore_index=True)
    # Add ratio per resolution
    esde["ratio_within_res"] = esde.groupby("resolution")["n_records_event"].transform(lambda s: s / s.sum())
    esde = esde.sort_values(["resolution", "n_records_event"], ascending=[True, False]).reset_index(drop=True)
    esde.to_parquet(V1101_OUT / "observation_3_esde_aggregate.parquet", index=False)
    return esde


def main():
    V1101_OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("[E-1] CID 単位: 24 seeds × ~228 cids × 326 atoms cosine sim distribution")
    cid_dist = step_e1_cid_atom_distribution()
    print(f"  -> {len(cid_dist)} atoms × 14 stats cols")

    print("[E-2] Integration 単位: β/α top-K aggregation + size distribution")
    int_sum = step_e2_integration_summary()
    print(f"  -> {len(int_sum)} (unit × atom) rows")

    print("[E-3] ESDE 単位: 4 解像度 atom emergence aggregation")
    esde = step_e3_esde_aggregate()
    print(f"  -> {len(esde)} (resolution × atom) rows")

    dt = time.time() - t0
    print(f"Step E-1..E-3 done in {dt:.1f}s")


if __name__ == "__main__":
    main()
