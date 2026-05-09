#!/usr/bin/env python3
"""v10.10 第一弾 多軸層化解析 (Web Claude 依頼、5 軸並列).

軸 A: Integration α/β 4 層化 + 形成タイミング × atom event timestamp
軸 B: cid 寿命 4 分位 + 寿命×n_core 交差 + timing 反転と寿命の関係
軸 C: 25 atom 個別 + category 別 + atom × n_core 交差
軸 E: window × n_core_bin × 全 metric
軸 F: seed 別 n_core 分布 + tied 20% セル内訳 + seed 別事件

すべて v10.10 main run 既存データの再集計 (物理層 frozen 維持)。
観察記述のみ、判定なし、因果断定回避規律継承。
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()
DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"

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
RUN_END = 25000
MIN_N_FOR_COHENS = 3  # n_b 不足判定閾値


def assert_output_under_v110(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V110_ROOT not in abs_path.parents and abs_path != V110_ROOT:
        raise ValueError(f"Output path {path} not under v110/")


def safe_write_parquet_v110(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v110(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# cid features 取得 (5 軸共通)
# ----------------------------------------------------------------------
def build_cid_features(seed: int) -> pd.DataFrame:
    """各 cid の n_core / lifespan / in_alpha / in_beta / t_alpha_first / t_beta_first."""
    m = _cid_meta_table(seed)
    death = pd.concat([
        m["host_lost_step"].fillna(RUN_END),
        m["reaped_step"].fillna(RUN_END),
    ], axis=1).min(axis=1)
    m = m.copy()
    m["lifespan"] = (death - m["birth_step"]).clip(lower=0)
    m["n_core"] = m["n_core_member"].fillna(0).astype(int)

    # alpha / beta 所属
    cid_in_alpha, cid_in_beta = set(), set()
    cid_alpha_first, cid_beta_first = {}, {}
    for fname, target_set, target_first in [
        ("alpha_lifecycle_log", cid_in_alpha, cid_alpha_first),
        ("beta_lifecycle_log", cid_in_beta, cid_beta_first),
    ]:
        df = pd.read_csv(DIAG_ROOT / f"integration/{fname}_seed{seed}.csv")
        if df.empty:
            continue
        births = df[df["event_type"] == "birth"]
        for _, r in births.iterrows():
            t_birth = int(r["step"])
            mems = str(r.get("member_cids") or "")
            for c_str in mems.split("|"):
                if not c_str.strip():
                    continue
                try:
                    c = int(c_str)
                except ValueError:
                    continue
                target_set.add(c)
                if c not in target_first or target_first[c] > t_birth:
                    target_first[c] = t_birth

    m["in_alpha"] = m["cognitive_id"].astype(int).isin(cid_in_alpha).astype(int)
    m["in_beta"] = m["cognitive_id"].astype(int).isin(cid_in_beta).astype(int)
    m["t_alpha_first"] = m["cognitive_id"].astype(int).map(cid_alpha_first).fillna(-1).astype(int)
    m["t_beta_first"] = m["cognitive_id"].astype(int).map(cid_beta_first).fillna(-1).astype(int)
    return m[["cognitive_id", "n_core", "lifespan", "birth_step",
                  "in_alpha", "in_beta", "t_alpha_first", "t_beta_first",
                  "last_familiarity_max", "final_state"]]


def integration_layer(in_a: int, in_b: int) -> str:
    if in_a == 1 and in_b == 1:
        return "both"
    if in_a == 1 and in_b == 0:
        return "only_alpha"
    if in_a == 0 and in_b == 1:
        return "only_beta"
    return "none"


def n_core_bin(n: int) -> str:
    if n <= 2:
        return "bin_2"
    if n <= 4:
        return "bin_3_4"
    return "bin_5plus"


def lifespan_q(lifespan: int, q1: float, q2: float, q3: float) -> str:
    if lifespan < q1: return "Q1"
    if lifespan < q2: return "Q2"
    if lifespan < q3: return "Q3"
    return "Q4"


def excess_path_for(condition_id: str, seed: int) -> Path:
    if condition_id == "v108_re":
        return V108RE_MAIN / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"
    return V110_MAIN / f"excess_change_adjusted_{condition_id}_seed{seed}.parquet"


def atom_path_for(condition_id: str, seed: int) -> Path:
    if condition_id == "v108_re":
        return V108RE_MAIN / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"
    return V110_MAIN / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"


def load_excess_with_features(condition_id: str, seed: int, features: pd.DataFrame,
                                  q1: float, q2: float, q3: float) -> pd.DataFrame:
    """excess_change_adjusted に source_cid → cid_features を attach."""
    p = excess_path_for(condition_id, seed)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    a = pd.read_parquet(atom_path_for(condition_id, seed))
    if a.empty or df.empty:
        return pd.DataFrame()
    feat_lookup = features.set_index("cognitive_id")
    a = a.copy()
    a["source_cid"] = a["source_cid"].astype(int)
    a["n_core"] = a["source_cid"].map(feat_lookup["n_core"]).fillna(0).astype(int)
    a["n_core_bin"] = a["n_core"].apply(n_core_bin)
    a["lifespan"] = a["source_cid"].map(feat_lookup["lifespan"]).fillna(0).astype(int)
    a["lifespan_q"] = a["lifespan"].apply(lambda l: lifespan_q(l, q1, q2, q3))
    a["in_alpha"] = a["source_cid"].map(feat_lookup["in_alpha"]).fillna(0).astype(int)
    a["in_beta"] = a["source_cid"].map(feat_lookup["in_beta"]).fillna(0).astype(int)
    a["integ_layer"] = a.apply(lambda r: integration_layer(r["in_alpha"], r["in_beta"]), axis=1)
    a["t_alpha_first"] = a["source_cid"].map(feat_lookup["t_alpha_first"]).fillna(-1).astype(int)
    a["t_beta_first"] = a["source_cid"].map(feat_lookup["t_beta_first"]).fillna(-1).astype(int)
    # Integration 形成タイミングと event の関係
    def _form_rel(row):
        ts = row["timestamp"]
        ta = row["t_alpha_first"]
        if ta < 0:
            return "no_alpha"
        diff = ts - ta
        if diff < 0:
            return "before_formation"
        if diff <= 100:
            return "after_formation_0_100"
        return "after_formation_100plus"
    a["formation_relation"] = a.apply(_form_rel, axis=1)
    a_sub = a[["event_id", "atom_id", "atom_index", "n_core", "n_core_bin",
                "lifespan", "lifespan_q", "in_alpha", "in_beta", "integ_layer",
                "formation_relation"]].drop_duplicates("event_id")
    return df.merge(a_sub, on="event_id", how="inner")


def cohens_d_with_n(a_vals, b_vals):
    return cohens_d(a_vals, b_vals), int(len(a_vals)), int(len(b_vals))


# ----------------------------------------------------------------------
# 軸別解析関数
# ----------------------------------------------------------------------
def evaluate_axis_a_integration(seed: int, q1: float, q2: float, q3: float,
                                     features: pd.DataFrame) -> pd.DataFrame:
    """軸 A: Integration α/β 4 層化 (lifetime ベース) + 形成タイミング."""
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
        for layer in ["only_alpha", "only_beta", "both", "none"]:
            for path in ALL_PATHS:
                for win in WINDOWS:
                    for metric in DELTA_METRICS:
                        col = f"{metric}_{win}"
                        if col not in df_a.columns or col not in df_b.columns:
                            continue
                        sub_a = df_a[(df_a["integ_layer"] == layer)
                                       & (df_a["relation_path_type"] == path)]
                        sub_b = df_b[(df_b["integ_layer"] == layer)
                                       & (df_b["relation_path_type"] == path)]
                        a_vals = sub_a[col].dropna().values
                        b_vals = sub_b[col].dropna().values
                        if len(a_vals) < 1 or len(b_vals) < 1:
                            continue
                        d, na, nb = cohens_d_with_n(a_vals, b_vals)
                        rows.append({
                            "seed": int(seed),
                            "comparison_type": comp["comparison_type"],
                            "comparison_name": comp["name"],
                            "integ_layer": layer,
                            "relation_path_type": path,
                            "observation_window": win,
                            "metric": metric,
                            "n_a": na, "n_b": nb,
                            "n_b_insufficient": int(nb < MIN_N_FOR_COHENS),
                            "cohens_d": d,
                        })
    return pd.DataFrame(rows)


def evaluate_axis_b_lifespan(seed: int, q1: float, q2: float, q3: float,
                                  features: pd.DataFrame) -> pd.DataFrame:
    """軸 B: cid 寿命 4 分位 + 寿命×n_core 交差."""
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
        for lq in ["Q1", "Q2", "Q3", "Q4"]:
            for nc_bin in ["bin_2", "bin_3_4", "bin_5plus", "all"]:
                for path in ALL_PATHS:
                    for win in WINDOWS:
                        for metric in DELTA_METRICS:
                            col = f"{metric}_{win}"
                            if col not in df_a.columns or col not in df_b.columns:
                                continue
                            mask_a = (df_a["lifespan_q"] == lq) & (df_a["relation_path_type"] == path)
                            mask_b = (df_b["lifespan_q"] == lq) & (df_b["relation_path_type"] == path)
                            if nc_bin != "all":
                                mask_a &= (df_a["n_core_bin"] == nc_bin)
                                mask_b &= (df_b["n_core_bin"] == nc_bin)
                            a_vals = df_a[mask_a][col].dropna().values
                            b_vals = df_b[mask_b][col].dropna().values
                            if len(a_vals) < 1 or len(b_vals) < 1:
                                continue
                            d, na, nb = cohens_d_with_n(a_vals, b_vals)
                            rows.append({
                                "seed": int(seed),
                                "comparison_type": comp["comparison_type"],
                                "comparison_name": comp["name"],
                                "lifespan_q": lq, "n_core_bin": nc_bin,
                                "relation_path_type": path,
                                "observation_window": win, "metric": metric,
                                "n_a": na, "n_b": nb,
                                "n_b_insufficient": int(nb < MIN_N_FOR_COHENS),
                                "cohens_d": d,
                            })
    return pd.DataFrame(rows)


def evaluate_axis_c_atom(seed: int, q1: float, q2: float, q3: float,
                              features: pd.DataFrame) -> pd.DataFrame:
    """軸 C: 25 atom 個別 + category 別 + atom × n_core 交差."""
    comps = build_comparisons()
    # 主軸 metric × window のみ (events 数を考慮、評価対象を絞る)
    target_metrics = [("mean_delta_C", "medium"), ("mean_n_pulses_in_window", "short")]

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
        # atom 個別 + category + atom×n_core
        for atom_id in df_a["atom_id"].unique():
            if pd.isna(atom_id): continue
            cat = str(atom_id).split(".")[0]  # category prefix
            for nc_bin in ["bin_2", "bin_3_4", "bin_5plus", "all"]:
                for path in ALL_PATHS:
                    for metric, win in target_metrics:
                        col = f"{metric}_{win}"
                        mask_a = (df_a["atom_id"] == atom_id) & (df_a["relation_path_type"] == path)
                        mask_b = (df_b["atom_id"] == atom_id) & (df_b["relation_path_type"] == path)
                        if nc_bin != "all":
                            mask_a &= (df_a["n_core_bin"] == nc_bin)
                            mask_b &= (df_b["n_core_bin"] == nc_bin)
                        a_vals = df_a[mask_a][col].dropna().values
                        b_vals = df_b[mask_b][col].dropna().values
                        if len(a_vals) < 1 or len(b_vals) < 1:
                            continue
                        d, na, nb = cohens_d_with_n(a_vals, b_vals)
                        rows.append({
                            "seed": int(seed),
                            "comparison_type": comp["comparison_type"],
                            "comparison_name": comp["name"],
                            "atom_id": atom_id, "atom_category": cat,
                            "n_core_bin": nc_bin,
                            "relation_path_type": path,
                            "observation_window": win, "metric": metric,
                            "n_a": na, "n_b": nb,
                            "n_b_insufficient": int(nb < MIN_N_FOR_COHENS),
                            "cohens_d": d,
                        })
    return pd.DataFrame(rows)


def evaluate_axis_e_window_n_core(seed: int, q1: float, q2: float, q3: float,
                                       features: pd.DataFrame) -> pd.DataFrame:
    """軸 E: window × n_core_bin × 全 metric (既存 n_core 層化を window 軸で展開)."""
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
        for nc_bin in ["bin_2", "bin_3_4", "bin_5plus"]:
            df_a_bin = df_a[df_a["n_core_bin"] == nc_bin]
            df_b_bin = df_b[df_b["n_core_bin"] == nc_bin]
            for path in ALL_PATHS:
                sub_a_p = df_a_bin[df_a_bin["relation_path_type"] == path]
                sub_b_p = df_b_bin[df_b_bin["relation_path_type"] == path]
                for win in WINDOWS:
                    for metric in DELTA_METRICS:
                        col = f"{metric}_{win}"
                        if col not in df_a.columns or col not in df_b.columns:
                            continue
                        a_vals = sub_a_p[col].dropna().values
                        b_vals = sub_b_p[col].dropna().values
                        if len(a_vals) < 1 or len(b_vals) < 1:
                            continue
                        d, na, nb = cohens_d_with_n(a_vals, b_vals)
                        rows.append({
                            "seed": int(seed),
                            "comparison_type": comp["comparison_type"],
                            "comparison_name": comp["name"],
                            "n_core_bin": nc_bin,
                            "relation_path_type": path,
                            "observation_window": win, "metric": metric,
                            "n_a": na, "n_b": nb,
                            "cohens_d": d,
                        })
    return pd.DataFrame(rows)


def _eval_seed_all_axes(args):
    """並列ワーカー: seed 別に 4 軸 (A/B/C/E) を評価."""
    seed, q1, q2, q3 = args
    features = build_cid_features(seed)
    a_df = evaluate_axis_a_integration(seed, q1, q2, q3, features)
    b_df = evaluate_axis_b_lifespan(seed, q1, q2, q3, features)
    c_df = evaluate_axis_c_atom(seed, q1, q2, q3, features)
    e_df = evaluate_axis_e_window_n_core(seed, q1, q2, q3, features)
    return a_df, b_df, c_df, e_df


# ----------------------------------------------------------------------
# 軸 F: seed 別構造ばらつき (集計のみ、既存 sensitivity から)
# ----------------------------------------------------------------------
def evaluate_axis_f(df_sens_all: pd.DataFrame) -> dict:
    """seed 別 n_core 分布、tied 内訳、seed 別事件."""
    out = {}

    # F-1: seed 別 n_core 分布
    seed_dist = []
    for seed in SEEDS:
        m = _cid_meta_table(seed)
        nc = m["n_core_member"].fillna(0).astype(int)
        seed_dist.append({
            "seed": seed,
            "n_cids": int(len(m)),
            "n_core_2": int((nc == 2).sum()),
            "n_core_3_4": int(((nc >= 3) & (nc <= 4)).sum()),
            "n_core_5plus": int((nc >= 5).sum()),
            "n_core_max": int(nc.max()),
            "lifespan_median": float(_cid_meta_table(seed)["birth_step"].max()),  # placeholder
        })
    out["seed_distribution"] = pd.DataFrame(seed_dist)

    # F-2: tied 20% セルの内訳 (既存 Level 3 の direction_consistency を再利用)
    lv3_path = CROSS_SEED / "direction_consistency_24seeds.parquet"
    if lv3_path.exists():
        lv3 = pd.read_parquet(lv3_path)
        tied = lv3[lv3["consistency_label"] == "tied"]
        tied_breakdown = tied.groupby(["comparison_type", "metric"]).size().reset_index(name="n_tied")
        tied_by_path = tied.groupby("relation_path_type").size().reset_index(name="n_tied")
        out["tied_by_comparison_metric"] = tied_breakdown
        out["tied_by_path"] = tied_by_path

    # F-3: seed 別事件 (seed 7 / 18 / その他外れ値)
    # main run のみ (smoke 除外)
    if not df_sens_all.empty:
        # mean_delta_C × medium で seed 別 cohens_d 平均
        sub = df_sens_all[(df_sens_all["metric"] == "mean_delta_C")
                              & (df_sens_all["observation_window"] == "medium")]
        seed_summary = sub.groupby(["seed", "comparison_type"])["cohens_d"].agg(
            ["mean", "std", "count"]
        ).reset_index()
        out["seed_event_summary"] = seed_summary

    return out


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    CROSS_SEED.mkdir(parents=True, exist_ok=True)
    print(f"v10.10 第一弾 多軸層化解析 (5 軸並列)")
    t0 = time.time()

    # 寿命 4 分位 (24 seeds 集計の値)
    print("  computing lifespan quartiles (24 seeds)...")
    all_lifespans = []
    for seed in SEEDS:
        m = _cid_meta_table(seed)
        death = pd.concat([
            m["host_lost_step"].fillna(RUN_END),
            m["reaped_step"].fillna(RUN_END),
        ], axis=1).min(axis=1)
        all_lifespans.extend((death - m["birth_step"]).clip(lower=0).tolist())
    ls = pd.Series(all_lifespans)
    q1, q2, q3 = float(ls.quantile(0.25)), float(ls.quantile(0.5)), float(ls.quantile(0.75))
    print(f"    Q1={q1:.0f}, Q2={q2:.0f}, Q3={q3:.0f}")

    print("  running axes A/B/C/E across 24 seeds (parallel)...")
    with Pool(processes=24) as pool:
        results = pool.map(_eval_seed_all_axes,
                              [(s, q1, q2, q3) for s in SEEDS])

    a_df = pd.concat([r[0] for r in results if not r[0].empty], ignore_index=True)
    b_df = pd.concat([r[1] for r in results if not r[1].empty], ignore_index=True)
    c_df = pd.concat([r[2] for r in results if not r[2].empty], ignore_index=True)
    e_df = pd.concat([r[3] for r in results if not r[3].empty], ignore_index=True)
    print(f"  axis A: {len(a_df):,} rows")
    print(f"  axis B: {len(b_df):,} rows")
    print(f"  axis C: {len(c_df):,} rows")
    print(f"  axis E: {len(e_df):,} rows")

    safe_write_parquet_v110(a_df, CROSS_SEED / "v110_integration_layer_stratified.parquet")
    safe_write_parquet_v110(b_df, CROSS_SEED / "v110_lifespan_stratified.parquet")
    safe_write_parquet_v110(c_df, CROSS_SEED / "v110_atom_individual.parquet")
    safe_write_parquet_v110(e_df, CROSS_SEED / "v110_window_n_core_cross.parquet")

    # 軸 F
    print("  running axis F (seed distribution, tied breakdown)...")
    df_sens_all = pd.read_parquet(V110_MAIN / "sensitivity_evaluation_all.parquet")
    f_out = evaluate_axis_f(df_sens_all)
    safe_write_parquet_v110(f_out["seed_distribution"], CROSS_SEED / "v110_seed_distribution.parquet")
    if "tied_by_comparison_metric" in f_out:
        safe_write_parquet_v110(f_out["tied_by_comparison_metric"],
                                  CROSS_SEED / "v110_tied_by_comparison_metric.parquet")
        safe_write_parquet_v110(f_out["tied_by_path"],
                                  CROSS_SEED / "v110_tied_by_path.parquet")
    safe_write_parquet_v110(f_out["seed_event_summary"],
                              CROSS_SEED / "v110_seed_event_summary.parquet")

    # 主要観察値の表示
    print("\n=== 軸 A サマリ: integ_layer × comparison_type (mean_delta_C × medium) ===")
    sub = a_df[(a_df["metric"] == "mean_delta_C") & (a_df["observation_window"] == "medium")]
    piv = sub.pivot_table(index="integ_layer", columns="comparison_type",
                            values="cohens_d", aggfunc="mean").round(3)
    print(piv.to_string())
    print("  layer 別 events:")
    print(sub.groupby("integ_layer")["n_b"].agg(["mean", "min", "max"]).to_string())

    print("\n=== 軸 B サマリ: lifespan_q × comparison_type (mean_delta_C × medium、n_core_bin=all) ===")
    sub = b_df[(b_df["metric"] == "mean_delta_C") & (b_df["observation_window"] == "medium")
                  & (b_df["n_core_bin"] == "all")]
    piv = sub.pivot_table(index="lifespan_q", columns="comparison_type",
                            values="cohens_d", aggfunc="mean").round(3)
    print(piv.to_string())

    print("\n=== 軸 C サマリ: atom_category × comparison_type (mean_delta_C × medium、n_core_bin=all) ===")
    sub = c_df[(c_df["metric"] == "mean_delta_C") & (c_df["n_core_bin"] == "all")]
    piv = sub.pivot_table(index="atom_category", columns="comparison_type",
                            values="cohens_d", aggfunc="mean").round(3)
    print(piv.to_string())

    print("\n=== 軸 E サマリ: window × n_core_bin (timing_axis、mean_delta_C のみ) ===")
    sub = e_df[(e_df["comparison_type"] == "timing_axis") & (e_df["metric"] == "mean_delta_C")]
    piv = sub.pivot_table(index="observation_window", columns="n_core_bin",
                            values="cohens_d", aggfunc="mean").round(3)
    print(piv.to_string())

    print("\n=== 軸 F サマリ: seed 別 n_core 分布 ===")
    print(f_out["seed_distribution"][["seed", "n_cids", "n_core_2",
                                              "n_core_3_4", "n_core_5plus"]].to_string(index=False))

    if "tied_by_comparison_metric" in f_out:
        print("\n=== 軸 F: tied 20% セルの内訳 (comparison × metric) ===")
        print(f_out["tied_by_comparison_metric"].sort_values("n_tied", ascending=False).to_string(index=False))

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
