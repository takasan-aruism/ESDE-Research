#!/usr/bin/env python3
"""v10.10 第二弾 多軸層化解析 (Web Claude 案 A、4 タスク並列).

タスク D: path × n_core_bin × 全 metric × 全 comparison (1,620 cells)
タスク A-4: Integration 形成タイミング × n_core (formation_relation × n_core_bin)
タスク B-2: 寿命 × n_core 交差 (詳細集計)
タスク C-4: atom × n_core 交差 (n_b 不足併記必須)

中心問い: 成熟度軸 (n_core / Integration / 寿命) が単一軸の別表現か独立 3 軸か。
判定なし、観察記述のみ、events 数 / n_b 不足併記必須。
"""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool
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
from v110_atom_event_generator import CONDITIONS  # noqa: E402
from v110_sensitivity_evaluator import build_comparisons, cohens_d  # noqa: E402
from v110_multi_axis_stratified_analyzer import (  # noqa: E402
    build_cid_features, load_excess_with_features,
    integration_layer, n_core_bin, lifespan_q, RUN_END,
)

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
MIN_N = 3


def assert_output_under_v110(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V110_ROOT not in abs_path.parents and abs_path != V110_ROOT:
        raise ValueError(f"Output path {path} not under v110/")


def safe_write_parquet_v110(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v110(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# タスク D: path × n_core_bin × 全 metric × 全 comparison (既存 parquet pivot)
# ----------------------------------------------------------------------
def task_d():
    """既存 v110_window_n_core_cross.parquet を 24 seeds 集計."""
    df = pd.read_parquet(CROSS_SEED / "v110_window_n_core_cross.parquet")
    g = df.groupby(["comparison_type", "n_core_bin", "relation_path_type",
                       "observation_window", "metric"])
    rows = []
    for keys, sub in g:
        d = sub["cohens_d"].values
        rows.append({
            "comparison_type": keys[0],
            "n_core_bin": keys[1],
            "relation_path_type": keys[2],
            "observation_window": keys[3],
            "metric": keys[4],
            "n_seeds_evaluable": int(len(d)),
            "cohens_d_mean": float(np.mean(d)),
            "cohens_d_std": float(np.std(d)),
            "cohens_d_abs_mean": float(np.abs(d).mean()),
            "n_b_min": int(sub["n_b"].min()),
            "n_b_mean": float(sub["n_b"].mean()),
        })
    out = pd.DataFrame(rows)
    safe_write_parquet_v110(out, CROSS_SEED / "v110_path_n_core_full_cross.parquet")
    return out


# ----------------------------------------------------------------------
# タスク A-4: 形成タイミング × n_core (新規集計)
# ----------------------------------------------------------------------
def evaluate_formation_per_seed(args):
    seed, q1, q2, q3 = args
    features = build_cid_features(seed)
    comps = build_comparisons()
    cond_dfs = {}
    rows = []
    for comp in comps:
        for cond in (comp["cond_a"], comp["cond_b"]):
            if cond not in cond_dfs:
                cond_dfs[cond] = load_excess_with_features(cond, seed, features, q1, q2, q3)
        df_a = cond_dfs[comp["cond_a"]]
        df_b = cond_dfs[comp["cond_b"]]
        if df_a.empty or df_b.empty:
            continue
        # 主軸 metric × window のみ
        for metric, win in [("mean_delta_C", "medium"),
                                ("mean_n_pulses_in_window", "short")]:
            col = f"{metric}_{win}"
            if col not in df_a.columns or col not in df_b.columns:
                continue
            for fr in ["before_formation", "after_formation_0_100",
                          "after_formation_100plus", "no_alpha"]:
                for nc_bin in ["bin_2", "bin_3_4", "bin_5plus", "all"]:
                    mask_a = (df_a["formation_relation"] == fr)
                    mask_b = (df_b["formation_relation"] == fr)
                    if nc_bin != "all":
                        mask_a &= (df_a["n_core_bin"] == nc_bin)
                        mask_b &= (df_b["n_core_bin"] == nc_bin)
                    a_vals = df_a[mask_a][col].dropna().values
                    b_vals = df_b[mask_b][col].dropna().values
                    if len(a_vals) < 1 or len(b_vals) < 1:
                        continue
                    d = cohens_d(a_vals, b_vals)
                    rows.append({
                        "seed": int(seed),
                        "comparison_type": comp["comparison_type"],
                        "comparison_name": comp["name"],
                        "formation_relation": fr,
                        "n_core_bin": nc_bin,
                        "metric": metric,
                        "observation_window": win,
                        "n_a": int(len(a_vals)),
                        "n_b": int(len(b_vals)),
                        "n_b_insufficient": int(len(b_vals) < MIN_N),
                        "cohens_d": d,
                    })
    return pd.DataFrame(rows)


def task_a4():
    # 寿命分位
    all_lifespans = []
    from v107_baseline_constructor import _cid_meta_table
    for seed in SEEDS:
        m = _cid_meta_table(seed)
        death = pd.concat([
            m["host_lost_step"].fillna(RUN_END),
            m["reaped_step"].fillna(RUN_END),
        ], axis=1).min(axis=1)
        all_lifespans.extend((death - m["birth_step"]).clip(lower=0).tolist())
    ls = pd.Series(all_lifespans)
    q1, q2, q3 = float(ls.quantile(0.25)), float(ls.quantile(0.5)), float(ls.quantile(0.75))

    with Pool(processes=24) as pool:
        dfs = pool.map(evaluate_formation_per_seed, [(s, q1, q2, q3) for s in SEEDS])
    df_all = pd.concat([d for d in dfs if not d.empty], ignore_index=True)

    # 24 seeds 集計
    g = df_all.groupby(["comparison_type", "formation_relation", "n_core_bin",
                            "metric", "observation_window"])
    rows = []
    for keys, sub in g:
        d = sub["cohens_d"].values
        rows.append({
            "comparison_type": keys[0],
            "formation_relation": keys[1],
            "n_core_bin": keys[2],
            "metric": keys[3],
            "observation_window": keys[4],
            "n_seeds_evaluable": int(len(d)),
            "cohens_d_mean": float(np.mean(d)),
            "cohens_d_std": float(np.std(d)),
            "n_b_min": int(sub["n_b"].min()),
            "n_b_mean": float(sub["n_b"].mean()),
            "n_b_insufficient_seeds": int(sub["n_b_insufficient"].sum()),
        })
    out = pd.DataFrame(rows)
    safe_write_parquet_v110(out, CROSS_SEED / "v110_formation_relation_stratified.parquet")
    return out, df_all


# ----------------------------------------------------------------------
# タスク B-2: 寿命 × n_core 交差 (既存 parquet pivot)
# ----------------------------------------------------------------------
def task_b2():
    df = pd.read_parquet(CROSS_SEED / "v110_lifespan_stratified.parquet")
    # 主軸 metric × window のみ
    sub = df[df["metric"].isin(["mean_delta_C", "mean_n_pulses_in_window"])]
    sub = sub[((sub["metric"] == "mean_delta_C") & (sub["observation_window"] == "medium")) |
                ((sub["metric"] == "mean_n_pulses_in_window") & (sub["observation_window"] == "short"))]
    g = sub.groupby(["comparison_type", "lifespan_q", "n_core_bin", "metric"])
    rows = []
    for keys, sub2 in g:
        d = sub2["cohens_d"].values
        rows.append({
            "comparison_type": keys[0],
            "lifespan_q": keys[1],
            "n_core_bin": keys[2],
            "metric": keys[3],
            "n_seeds_evaluable": int(len(d)),
            "cohens_d_mean": float(np.mean(d)),
            "cohens_d_std": float(np.std(d)),
            "n_b_min": int(sub2["n_b"].min()),
            "n_b_mean": float(sub2["n_b"].mean()),
            "n_b_insufficient_seeds": int(sub2["n_b_insufficient"].sum()),
        })
    out = pd.DataFrame(rows)
    safe_write_parquet_v110(out, CROSS_SEED / "v110_lifespan_n_core_cross_summary.parquet")
    return out


# ----------------------------------------------------------------------
# タスク C-4: atom × n_core (既存 parquet pivot、n_b 不足併記)
# ----------------------------------------------------------------------
def task_c4():
    df = pd.read_parquet(CROSS_SEED / "v110_atom_individual.parquet")
    # 主軸 metric (mean_delta_C × medium / mean_n_pulses_in_window × short)
    sub = df[((df["metric"] == "mean_delta_C") & (df["observation_window"] == "medium")) |
                ((df["metric"] == "mean_n_pulses_in_window") & (df["observation_window"] == "short"))]
    # path 別に膨大なので、主要 path のみ集計 (Code A 判断: high_fam_out / matched / familiarity / temporal / attention)
    KEY_PATHS = [
        "high_familiarity_outside_integration_baseline",
        "matched_baseline", "familiarity",
        "temporal_coactivation", "attention_via_salience",
    ]
    sub2 = sub[sub["relation_path_type"].isin(KEY_PATHS)]
    g = sub2.groupby(["comparison_type", "atom_id", "atom_category",
                          "n_core_bin", "relation_path_type", "metric"])
    rows = []
    for keys, sub3 in g:
        d = sub3["cohens_d"].values
        n_b_vals = sub3["n_b"].values
        n_eval = int((n_b_vals >= MIN_N).sum())
        n_seeds = int(len(d))
        rows.append({
            "comparison_type": keys[0],
            "atom_id": keys[1],
            "atom_category": keys[2],
            "n_core_bin": keys[3],
            "relation_path_type": keys[4],
            "metric": keys[5],
            "n_seeds_evaluable": n_seeds,
            "n_seeds_with_sufficient_b": n_eval,
            "n_seeds_b_insufficient": int(n_seeds - n_eval),
            "cohens_d_mean": float(np.mean(d)),
            "cohens_d_std": float(np.std(d)),
            "n_b_min": int(n_b_vals.min()),
            "n_b_mean": float(n_b_vals.mean()),
        })
    out = pd.DataFrame(rows)
    safe_write_parquet_v110(out, CROSS_SEED / "v110_atom_n_core_cross_summary.parquet")
    return out


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    print(f"v10.10 第二弾 多軸層化解析 (4 タスク)")
    t0 = time.time()

    print("\n=== タスク D: path × n_core_bin × 全 metric × 全 comparison ===")
    d_out = task_d()
    print(f"  rows: {len(d_out)}")

    print("\n=== タスク A-4: Integration 形成タイミング × n_core ===")
    a4_out, _ = task_a4()
    print(f"  rows: {len(a4_out)}")

    print("\n=== タスク B-2: 寿命 × n_core 交差 ===")
    b2_out = task_b2()
    print(f"  rows: {len(b2_out)}")

    print("\n=== タスク C-4: atom × n_core 交差 ===")
    c4_out = task_c4()
    print(f"  rows: {len(c4_out)}")

    # 主要観察値の表示
    print("\n=== タスク D 主要観察 (mean_delta_C × medium、cohens_d_mean) ===")
    sub = d_out[(d_out["metric"] == "mean_delta_C") &
                       (d_out["observation_window"] == "medium")]
    for cmp_type in ["timing_axis", "v110_vs_v108re", "gate_effect"]:
        s2 = sub[sub["comparison_type"] == cmp_type]
        piv = s2.pivot_table(index="relation_path_type", columns="n_core_bin",
                                values="cohens_d_mean", aggfunc="mean").round(3)
        print(f"\n--- {cmp_type} ---")
        print(piv.to_string())

    print("\n=== タスク A-4 主要観察 (mean_delta_C × medium、cohens_d_mean) ===")
    sub = a4_out[a4_out["metric"] == "mean_delta_C"]
    for cmp_type in ["timing_axis", "v110_vs_v108re"]:
        s2 = sub[sub["comparison_type"] == cmp_type]
        piv = s2.pivot_table(index="formation_relation", columns="n_core_bin",
                                values="cohens_d_mean", aggfunc="mean").round(3)
        print(f"\n--- {cmp_type} ---")
        print(piv.to_string())
        # n_b 情報
        piv_n = s2.pivot_table(index="formation_relation", columns="n_core_bin",
                                  values="n_b_mean", aggfunc="mean").round(0)
        print(f"  n_b_mean:")
        print(piv_n.to_string())

    print("\n=== タスク B-2 主要観察 (mean_delta_C × medium) ===")
    sub = b2_out[b2_out["metric"] == "mean_delta_C"]
    for cmp_type in ["timing_axis", "v110_vs_v108re", "gate_effect"]:
        s2 = sub[sub["comparison_type"] == cmp_type]
        piv = s2.pivot_table(index="lifespan_q", columns="n_core_bin",
                                values="cohens_d_mean", aggfunc="mean").round(3)
        print(f"\n--- {cmp_type} (cohens_d_mean) ---")
        print(piv.to_string())
        piv_n = s2.pivot_table(index="lifespan_q", columns="n_core_bin",
                                  values="n_b_mean", aggfunc="mean").round(0)
        print(f"  n_b_mean:")
        print(piv_n.to_string())

    print("\n=== タスク C-4 主要観察 (mean_delta_C × medium、v110_vs_v108re) ===")
    sub = c4_out[(c4_out["metric"] == "mean_delta_C") &
                       (c4_out["comparison_type"] == "v110_vs_v108re")]
    # category 別 × n_core_bin の集計 (high_fam_out のみ表示)
    s2 = sub[sub["relation_path_type"] == "high_familiarity_outside_integration_baseline"]
    piv = s2.pivot_table(index="atom_category", columns="n_core_bin",
                            values="cohens_d_mean", aggfunc="mean").round(3)
    print(f"\n--- v110_vs_v108re × high_fam_out (cohens_d_mean) ---")
    print(piv.to_string())
    print(f"  n_seeds_b_insufficient (mean across atoms):")
    piv_ins = s2.pivot_table(index="atom_category", columns="n_core_bin",
                                  values="n_seeds_b_insufficient", aggfunc="mean").round(1)
    print(piv_ins.to_string())

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
