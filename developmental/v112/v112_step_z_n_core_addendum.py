#!/usr/bin/env python3
"""v10.12 Step Z 補完: n_core 別層化解析 (Taka 指摘 2026-05-10).

規律 §34 #37 (n_core 別層化解析必須) の遵守。
本 Step Z で漏らしていたため、補完として全 Q-Z 項目を n_core_bin 別に再集計。

bin_2 (ペア、76%) / bin_3_4 (小 cluster、12%) / bin_5+ (中 cluster、12%)

cond3 (n_core ≥ 5) が 4 条件複合に含まれるため、AND_all は必然的に bin_5+ のみ。
→ cond3 を含めない 3 条件 AND (cond1 ∧ cond2 ∧ cond4) を n_core 別に集計、
  v10.10 finding (delta_C 系は bin_5+、pulse 系は bin_2 で大) との対応を観察素材として提供。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
DIAG = V105_ROOT / "diag_v105_main_v2"

OUT = V112_ROOT / "outputs" / "step_z"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v112_step_z_environment_check import (  # noqa: E402
    build_beta_intervals, is_beta_member_at, collect_cid_features,
    SEEDS, RUN_END, AGE_TARGET,
)

N_CORE_BINS = ["bin_2", "bin_3_4", "bin_5plus"]


def n_core_bin(n: int) -> str:
    if n <= 2:
        return "bin_2"
    if n <= 4:
        return "bin_3_4"
    return "bin_5plus"


# ----------------------------------------------------------------------
# 補完 Q-Z1: 4 条件複合 + 3 条件 (cond3 除外) の n_core 別集計
# ----------------------------------------------------------------------
def q_z1_n_core_breakdown(q3_lifespan: float, fam_q3_per_seed: dict) -> pd.DataFrame:
    """各 seed × 各 n_core_bin で各条件 / 複合条件の母集団."""
    rows = []
    for seed in SEEDS:
        m = collect_cid_features(seed)
        intervals = build_beta_intervals(seed)
        fam_thresh = fam_q3_per_seed[seed]
        for nc_bin in N_CORE_BINS:
            cond_results = {
                "n_total_in_bin": 0,
                "cond1_not_beta": 0,
                "cond2_long": 0,
                "cond3_n_core_5plus": 0,
                "cond4_high_fam": 0,
                "AND_1_2": 0,
                "AND_1_4": 0,
                "AND_1_2_4_no_cond3": 0,  # cond3 除外
                "AND_all_4cond": 0,
            }
            for _, row in m.iterrows():
                cid = int(row["cognitive_id"])
                birth = int(row["birth_step"])
                t_target = birth + AGE_TARGET
                death = int(row["death_step"])
                if t_target >= RUN_END or t_target >= death:
                    continue
                this_bin = n_core_bin(int(row["n_core"]))
                if this_bin != nc_bin:
                    continue
                cond_results["n_total_in_bin"] += 1

                c1 = not is_beta_member_at(cid, t_target, intervals)
                c2 = row["lifespan"] >= q3_lifespan
                c3 = row["n_core"] >= 5
                c4 = row["fam_max"] >= fam_thresh

                if c1: cond_results["cond1_not_beta"] += 1
                if c2: cond_results["cond2_long"] += 1
                if c3: cond_results["cond3_n_core_5plus"] += 1
                if c4: cond_results["cond4_high_fam"] += 1
                if c1 and c2: cond_results["AND_1_2"] += 1
                if c1 and c4: cond_results["AND_1_4"] += 1
                if c1 and c2 and c4: cond_results["AND_1_2_4_no_cond3"] += 1
                if c1 and c2 and c3 and c4: cond_results["AND_all_4cond"] += 1
            rows.append({"seed": seed, "n_core_bin": nc_bin, **cond_results})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 補完 Q-Z6: cid pool 重なりの n_core 別
# ----------------------------------------------------------------------
def q_z6_n_core_breakdown(q3_lifespan: float, fam_q3_per_seed: dict) -> pd.DataFrame:
    from v108_atom_event_generator import TARGET_ATOMS
    rows = []
    for seed in SEEDS:
        m = collect_cid_features(seed)
        intervals = build_beta_intervals(seed)
        fam_thresh = fam_q3_per_seed[seed]

        # n_core lookup
        nc_lookup = dict(zip(m["cognitive_id"].astype(int),
                                  m["n_core"].astype(int)))

        # v112 pool (4 条件)
        v112_pool_4cond = set()
        v112_pool_3cond_no_c3 = set()
        for _, row in m.iterrows():
            cid = int(row["cognitive_id"])
            birth = int(row["birth_step"])
            t_target = birth + AGE_TARGET
            death = int(row["death_step"])
            if t_target >= RUN_END or t_target >= death:
                continue
            c1 = not is_beta_member_at(cid, t_target, intervals)
            c2 = row["lifespan"] >= q3_lifespan
            c3 = row["n_core"] >= 5
            c4 = row["fam_max"] >= fam_thresh
            if c1 and c2 and c3 and c4:
                v112_pool_4cond.add(cid)
            if c1 and c2 and c4:  # cond3 除外
                v112_pool_3cond_no_c3.add(cid)

        # v108 pool
        sim_path = V106_ROOT / "outputs" / "main" / f"cid_atom_sim_matrix_seed{seed}.parquet"
        v108_pool = set()
        if sim_path.exists():
            df_sim = pd.read_parquet(sim_path)
            for atom in TARGET_ATOMS:
                if atom not in df_sim.columns: continue
                top100 = df_sim[["cid", atom]].dropna().sort_values(atom, ascending=False).head(100)
                v108_pool.update(top100["cid"].astype(int).tolist())

        # n_core_bin 別の集計
        for nc_bin in N_CORE_BINS:
            v112_4cond_in_bin = {c for c in v112_pool_4cond if n_core_bin(nc_lookup.get(c, 0)) == nc_bin}
            v112_3cond_in_bin = {c for c in v112_pool_3cond_no_c3 if n_core_bin(nc_lookup.get(c, 0)) == nc_bin}
            v108_in_bin = {c for c in v108_pool if n_core_bin(nc_lookup.get(c, 0)) == nc_bin}
            overlap_4 = v112_4cond_in_bin & v108_in_bin
            overlap_3 = v112_3cond_in_bin & v108_in_bin
            rows.append({
                "seed": seed, "n_core_bin": nc_bin,
                "n_v112_4cond": len(v112_4cond_in_bin),
                "n_v112_3cond_no_c3": len(v112_3cond_in_bin),
                "n_v108_top_k_100": len(v108_in_bin),
                "n_overlap_4cond_v108": len(overlap_4),
                "n_overlap_3cond_v108": len(overlap_3),
                "overlap_ratio_4cond_to_v108": (len(overlap_4) / len(v108_in_bin))
                                                  if len(v108_in_bin) > 0 else 0,
                "overlap_ratio_3cond_to_v108": (len(overlap_3) / len(v108_in_bin))
                                                  if len(v108_in_bin) > 0 else 0,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 補完: v108 top_k_100 cid pool の n_core 分布
# ----------------------------------------------------------------------
def v108_pool_n_core_distribution() -> pd.DataFrame:
    from v108_atom_event_generator import TARGET_ATOMS
    rows = []
    for seed in SEEDS:
        m = collect_cid_features(seed)
        nc_lookup = dict(zip(m["cognitive_id"].astype(int),
                                  m["n_core"].astype(int)))
        sim_path = V106_ROOT / "outputs" / "main" / f"cid_atom_sim_matrix_seed{seed}.parquet"
        if not sim_path.exists(): continue
        df_sim = pd.read_parquet(sim_path)
        v108_pool = set()
        for atom in TARGET_ATOMS:
            if atom not in df_sim.columns: continue
            top100 = df_sim[["cid", atom]].dropna().sort_values(atom, ascending=False).head(100)
            v108_pool.update(top100["cid"].astype(int).tolist())
        bin_counts = {nb: 0 for nb in N_CORE_BINS}
        for c in v108_pool:
            bin_counts[n_core_bin(nc_lookup.get(c, 0))] += 1
        rows.append({"seed": seed, "n_v108_total": len(v108_pool), **bin_counts})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 60)
    print("v10.12 Step Z 補完: n_core 別層化解析 (Taka 指摘)")
    print("=" * 60)

    # 既存実測値読み込み
    qz2 = pd.read_parquet(OUT / "q_z2_lifespan.parquet").iloc[0]
    q3_lifespan = float(qz2["Q3"])
    qz4_5_7 = json.load(open(OUT / "q_z4_5_7_qualitative.json"))
    # per_seed_q3 を再計算 (json に含まれていないため)
    fam_q3_per_seed = {}
    for seed in SEEDS:
        m = collect_cid_features(seed)
        fam_q3_per_seed[seed] = float(np.percentile(m["fam_max"], 75))

    print(f"\n=== Q-Z1 補完: 4 条件 + 3 条件 (cond3 除外) の n_core 別集計 ===")
    qz1_nc = q_z1_n_core_breakdown(q3_lifespan, fam_q3_per_seed)
    qz1_nc.to_parquet(OUT / "q_z1_n_core_breakdown.parquet", index=False)

    # 集計 (n_core_bin 別の 24 seeds 合計 + per-seed mean)
    print(f"\n--- 24 seeds 合計 (n_core_bin × 各条件) ---")
    summary = qz1_nc.groupby("n_core_bin").agg(
        n_total_in_bin=("n_total_in_bin", "sum"),
        cond1_not_beta=("cond1_not_beta", "sum"),
        cond2_long=("cond2_long", "sum"),
        cond3_n_core_5plus=("cond3_n_core_5plus", "sum"),
        cond4_high_fam=("cond4_high_fam", "sum"),
        AND_1_2=("AND_1_2", "sum"),
        AND_1_4=("AND_1_4", "sum"),
        AND_1_2_4_no_cond3=("AND_1_2_4_no_cond3", "sum"),
        AND_all_4cond=("AND_all_4cond", "sum"),
    )
    print(summary.to_string())

    print(f"\n--- per-seed mean (各 cell の seed あたり平均) ---")
    summary_mean = qz1_nc.groupby("n_core_bin").agg(
        AND_all_4cond_mean=("AND_all_4cond", "mean"),
        AND_1_2_4_no_cond3_mean=("AND_1_2_4_no_cond3", "mean"),
        AND_1_2_mean=("AND_1_2", "mean"),
        AND_1_4_mean=("AND_1_4", "mean"),
    ).round(2)
    print(summary_mean.to_string())

    print(f"\n=== Q-Z6 補完: cid pool 重なりの n_core 別 ===")
    qz6_nc = q_z6_n_core_breakdown(q3_lifespan, fam_q3_per_seed)
    qz6_nc.to_parquet(OUT / "q_z6_n_core_breakdown.parquet", index=False)
    summary6 = qz6_nc.groupby("n_core_bin").agg(
        n_v112_4cond_total=("n_v112_4cond", "sum"),
        n_v112_3cond_no_c3_total=("n_v112_3cond_no_c3", "sum"),
        n_v108_total=("n_v108_top_k_100", "sum"),
        overlap_4cond=("n_overlap_4cond_v108", "sum"),
        overlap_3cond=("n_overlap_3cond_v108", "sum"),
        overlap_ratio_4cond=("overlap_ratio_4cond_to_v108", "mean"),
        overlap_ratio_3cond=("overlap_ratio_3cond_to_v108", "mean"),
    )
    print(summary6.to_string())

    print(f"\n=== 補完: v108 top_k_100 pool の n_core 分布 ===")
    v108_dist = v108_pool_n_core_distribution()
    v108_dist.to_parquet(OUT / "v108_pool_n_core_dist.parquet", index=False)
    summary_v108 = v108_dist[["n_v108_total"] + N_CORE_BINS].agg(["sum", "mean", "min", "max"]).round(1)
    print(summary_v108.to_string())
    # 比率
    v108_total = v108_dist["n_v108_total"].sum()
    print(f"\n  v108 pool 全体 (24 seeds): {v108_total}")
    for nb in N_CORE_BINS:
        n = v108_dist[nb].sum()
        print(f"    {nb}: {n} ({n/v108_total*100:.1f}%)")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    sys.exit(main())
