#!/usr/bin/env python3
"""v10.11 Step F: cross-seed 解析 + 4 階層 reports (within-cid design).

q_c_inherited 起点の within-cid 前後比較 (T-50 vs T+50) を 12 cells
(n_core_bin × c_q_partition) × 24 seeds で集計、4 段階方向一致観察。

主題ドキュメント第三稿 §4.0 within-cid design + §4.1-4.5 階層に準拠。

達成条件 §0.2: v10.12 入力ルーティング条件 1 本以上抽出。

出力 (cross_seed/):
  - within_cid_delta_summary.parquet (12 cells × 24 seeds)
  - direction_consistency_24seeds.parquet (4 段階観察)
  - level_1_mechanism_check.json
  - level_2_3_3_5_reports.parquet
  - four_observations_v111.md
  - v110_v111_routing_conditions.md (達成条件 §0.2 抽出)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V111_ROOT = (REPO_ROOT / "developmental" / "v111").resolve()
V111_MAIN = V111_ROOT / "outputs" / "main"
CROSS_SEED = V111_MAIN / "cross_seed"

SEEDS = list(range(24))
N_CORE_BINS = ["bin_2", "bin_3_4", "bin_5plus"]
C_Q_PARTITIONS = ["Q1", "Q2", "Q3", "Q4"]


def assert_output_under_v111(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V111_ROOT not in abs_path.parents and abs_path != V111_ROOT:
        raise ValueError(f"Output path {path} not under v111/")


def safe_write_parquet_v111(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v111(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def load_all_profiles() -> pd.DataFrame:
    """24 seeds の response_profile を concat."""
    dfs = []
    for seed in SEEDS:
        p = V111_MAIN / f"q_c_inherited_response_profile_seed{seed}.parquet"
        if p.exists():
            dfs.append(pd.read_parquet(p))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def compute_within_cid_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """各 (seed, event_id, cid) について T-50 と T+50 の C 値・pulse_count から
    within-cid delta を計算."""
    pivot_C = df.pivot_table(
        index=["seed", "event_id", "cid", "n_core_bin", "c_q_partition", "T", "beta_id",
                  "cumulative_c_before", "n_core"],
        columns="t_offset", values="C_value", aggfunc="first"
    ).reset_index()
    pivot_pulse = df.pivot_table(
        index=["seed", "event_id", "cid"],
        columns="t_offset", values="pulse_count", aggfunc="first"
    ).reset_index()

    # T-50, T+50 列を取り出す
    if -50 not in pivot_C.columns or 50 not in pivot_C.columns:
        raise ValueError("T-50 or T+50 columns missing in pivot")

    out = pivot_C[["seed", "event_id", "cid", "n_core_bin", "c_q_partition",
                       "T", "beta_id", "cumulative_c_before", "n_core"]].copy()
    out["C_at_minus_50"] = pivot_C[-50].values
    out["C_at_plus_50"] = pivot_C[50].values
    out["delta_C_within"] = out["C_at_plus_50"] - out["C_at_minus_50"]

    # pulse 集計 (T-50 と T+50 で各々 +5 step ウィンドウ pulse 数)
    pulse_lookup = pivot_pulse.set_index(["seed", "event_id", "cid"])
    out_pulse_minus = []
    out_pulse_plus = []
    for _, r in out.iterrows():
        key = (int(r["seed"]), r["event_id"], int(r["cid"]))
        if key in pulse_lookup.index:
            row = pulse_lookup.loc[key]
            pm = row.get(-50, 0) if hasattr(row, "get") else row[-50] if -50 in row else 0
            pp = row.get(50, 0) if hasattr(row, "get") else row[50] if 50 in row else 0
        else:
            pm, pp = 0, 0
        out_pulse_minus.append(pm)
        out_pulse_plus.append(pp)
    out["pulse_at_minus_50"] = out_pulse_minus
    out["pulse_at_plus_50"] = out_pulse_plus
    out["delta_pulse_within"] = out["pulse_at_plus_50"] - out["pulse_at_minus_50"]

    return out


def build_level_1(df_all: pd.DataFrame, df_within: pd.DataFrame) -> dict:
    """Level 1: 機構動作確認."""
    return {
        "n_seeds": int(df_all["seed"].nunique()),
        "all_24_seeds_covered": int(df_all["seed"].nunique()) == 24,
        "n_total_snapshots": int(len(df_all)),
        "n_event_cid_pairs": int(len(df_within)),
        "n_unique_cids": int(df_all["cid"].nunique()),
        "n_unique_events": int(df_all["event_id"].nunique()),
        "n_unique_betas": int(df_all["beta_id"].nunique()),
        "t_offsets": sorted(df_all["t_offset"].unique().tolist()),
        "n_core_bins": sorted(df_all["n_core_bin"].unique().tolist()),
        "c_q_partitions": sorted(df_all["c_q_partition"].unique().tolist()),
    }


def build_level_2_3(df_within: pd.DataFrame) -> pd.DataFrame:
    """Level 2-3: 12 cells × 24 seeds の delta_C / delta_pulse 集計."""
    rows = []
    for nc in N_CORE_BINS:
        for cq in C_Q_PARTITIONS:
            for seed in SEEDS:
                sub = df_within[(df_within["n_core_bin"] == nc)
                                  & (df_within["c_q_partition"] == cq)
                                  & (df_within["seed"] == seed)]
                if sub.empty:
                    rows.append({
                        "n_core_bin": nc, "c_q_partition": cq, "seed": seed,
                        "n_pairs": 0,
                        "delta_C_mean": 0.0, "delta_C_std": 0.0,
                        "delta_pulse_mean": 0.0, "delta_pulse_std": 0.0,
                    })
                    continue
                rows.append({
                    "n_core_bin": nc, "c_q_partition": cq, "seed": seed,
                    "n_pairs": int(len(sub)),
                    "delta_C_mean": float(sub["delta_C_within"].mean()),
                    "delta_C_std": float(sub["delta_C_within"].std()) if len(sub) > 1 else 0.0,
                    "delta_pulse_mean": float(sub["delta_pulse_within"].mean()),
                    "delta_pulse_std": float(sub["delta_pulse_within"].std()) if len(sub) > 1 else 0.0,
                })
    return pd.DataFrame(rows)


def build_direction_consistency(df_l23: pd.DataFrame) -> pd.DataFrame:
    """24 seeds 方向一致 4 段階観察 (主題 §4.3)."""
    rows = []
    for nc in N_CORE_BINS:
        for cq in C_Q_PARTITIONS:
            sub = df_l23[(df_l23["n_core_bin"] == nc) & (df_l23["c_q_partition"] == cq)]
            for metric in ["delta_C_mean", "delta_pulse_mean"]:
                evaluable = sub[sub["n_pairs"] > 0]
                if evaluable.empty:
                    rows.append({
                        "n_core_bin": nc, "c_q_partition": cq, "metric": metric,
                        "n_seeds_evaluable": 0,
                        "n_positive": 0, "n_negative": 0, "n_zero": 0,
                        "consistency_label": "no_data",
                        "mean_across_seeds": 0.0,
                        "std_across_seeds": 0.0,
                    })
                    continue
                vals = evaluable[metric].values
                n = len(vals)
                n_pos = int((vals > 0).sum())
                n_neg = int((vals < 0).sum())
                n_zero = int((vals == 0).sum())
                if n_pos == n or n_neg == n or n_zero == n:
                    label = "complete_consistent"
                elif n_pos >= 14 or n_neg >= 14:
                    label = "majority_consistent"
                elif n_zero >= 14:
                    label = "majority_zero"
                else:
                    label = "tied"
                rows.append({
                    "n_core_bin": nc, "c_q_partition": cq, "metric": metric,
                    "n_seeds_evaluable": n,
                    "n_positive": n_pos, "n_negative": n_neg, "n_zero": n_zero,
                    "consistency_label": label,
                    "mean_across_seeds": float(np.mean(vals)),
                    "std_across_seeds": float(np.std(vals)),
                })
    return pd.DataFrame(rows)


def build_routing_conditions(df_consistency: pd.DataFrame, df_l23: pd.DataFrame) -> str:
    """達成条件 §0.2: v10.12 入力ルーティング条件 1 本以上抽出."""
    lines = []
    lines.append("# v10.12 入力ルーティング条件 (達成条件 §0.2)\n")
    lines.append("*抽出元*: v10.11 within-cid design (q_c_inherited 起点、12 cells)\n")
    lines.append("*規律*: 観察事実 / 整理仮説 / 未解明 を分離 (§3 ラベル規律)\n\n")

    lines.append("## 観察事実\n")
    sub_C = df_consistency[df_consistency["metric"] == "delta_C_mean"]
    lines.append("\n### delta_C_within (T+50 - T-50) の n_core_bin × c_q_partition × 24 seeds 方向一致\n\n")
    lines.append("| n_core_bin | Q1 | Q2 | Q3 | Q4 |\n")
    lines.append("|---|---|---|---|---|\n")
    for nc in N_CORE_BINS:
        row = f"| {nc} "
        for cq in C_Q_PARTITIONS:
            r = sub_C[(sub_C["n_core_bin"] == nc) & (sub_C["c_q_partition"] == cq)]
            if r.empty:
                row += "| - "
            else:
                rr = r.iloc[0]
                row += f"| {rr['mean_across_seeds']:+.3f} ({rr['consistency_label'][:8]}) "
        row += "|\n"
        lines.append(row)

    lines.append("\n### delta_pulse_within の n_core_bin × c_q_partition\n\n")
    lines.append("| n_core_bin | Q1 | Q2 | Q3 | Q4 |\n")
    lines.append("|---|---|---|---|---|\n")
    sub_P = df_consistency[df_consistency["metric"] == "delta_pulse_mean"]
    for nc in N_CORE_BINS:
        row = f"| {nc} "
        for cq in C_Q_PARTITIONS:
            r = sub_P[(sub_P["n_core_bin"] == nc) & (sub_P["c_q_partition"] == cq)]
            if r.empty:
                row += "| - "
            else:
                rr = r.iloc[0]
                row += f"| {rr['mean_across_seeds']:+.3f} ({rr['consistency_label'][:8]}) "
        row += "|\n"
        lines.append(row)

    lines.append("\n## 整理仮説 (構造的根拠は本主題で確定せず留保継承)\n\n")
    # Q1 で正方向、Q2-Q4 で 0 のパターンが観察されれば C 値飽和仮説と整合
    q1_C = sub_C[sub_C["c_q_partition"] == "Q1"]
    q4_C = sub_C[sub_C["c_q_partition"] == "Q4"]
    q1_pos = (q1_C["mean_across_seeds"] > 0.05).sum()
    q4_zero = ((q4_C["mean_across_seeds"].abs() < 0.05)).sum()
    lines.append(f"- Q1 (累積 c < 3) で delta_C_mean > 0.05 の cells: {q1_pos}/3 (n_core_bin)\n")
    lines.append(f"- Q4 (累積 c ≥ 10) で delta_C_mean ≈ 0 (|x|<0.05) の cells: {q4_zero}/3\n")
    if q1_pos >= 2 and q4_zero >= 2:
        lines.append("- 観察パターン: 「Q1 で delta_C 正、Q4 で delta_C ≈ 0」 → C 値飽和仮説と整合 (整理仮説、留保: 構造的根拠は本主題で未確定)\n")
    else:
        lines.append("- 観察パターンは仮説 2 (C 値飽和) と部分的に整合、または別パターン (留保事項として記録)\n")

    lines.append("\n## v10.12 入力ルーティング条件候補\n\n")
    # 条件 1: Q1 群の cohens_d_mean が最大の n_core_bin
    q1_max = q1_C.loc[q1_C["mean_across_seeds"].idxmax()] if not q1_C.empty else None
    if q1_max is not None and q1_max["mean_across_seeds"] > 0:
        lines.append(f"### 条件 1: 概念取り込み (delta_C 系)\n\n")
        lines.append(f"**「β 累積 c_inherited が 3 未満 (Q1) の状態の cid を狙う」**\n\n")
        lines.append(f"- 最大効果 n_core_bin: {q1_max['n_core_bin']} (delta_C mean {q1_max['mean_across_seeds']:+.3f}、{q1_max['consistency_label']})\n")
        lines.append(f"- 全 n_core_bin で Q1 が他の Q を上回る場合、入力対象を「累積 c_inherited < 3 の cid」に絞る\n")

    # 条件 2: pulse 系で大効果のセル
    p_max = sub_P.loc[sub_P["mean_across_seeds"].abs().idxmax()] if not sub_P.empty else None
    if p_max is not None and abs(p_max["mean_across_seeds"]) > 0.1:
        lines.append(f"\n### 条件 2: 行動活性化 (pulse 系)\n\n")
        lines.append(f"**「{p_max['n_core_bin']} × {p_max['c_q_partition']} の cid は q_c_inherited 前後で pulse 活動 {p_max['mean_across_seeds']:+.3f}」**\n\n")
        lines.append(f"- 観察: delta_pulse_mean = {p_max['mean_across_seeds']:+.3f} ({p_max['consistency_label']})\n")
        lines.append(f"- 行動活性化目的の cid 選定基準として使用可能\n")

    return "".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["main"], default="main")
    args = ap.parse_args()

    CROSS_SEED.mkdir(parents=True, exist_ok=True)
    print(f"v10.11 Step F: cross-seed 解析 (within-cid design)")
    t0 = time.time()

    df_all = load_all_profiles()
    print(f"  loaded snapshots: {len(df_all)} (24 seeds 集計)")

    # within-cid delta 計算
    df_within = compute_within_cid_deltas(df_all)
    safe_write_parquet_v111(df_within, CROSS_SEED / "within_cid_deltas.parquet")
    print(f"  within-cid (event, cid) pairs: {len(df_within)}")

    # Level 1
    lv1 = build_level_1(df_all, df_within)
    with open(CROSS_SEED / "level_1_mechanism_check.json", "w") as f:
        json.dump(lv1, f, indent=2, ensure_ascii=False)
    print(f"  Level 1: {lv1['n_total_snapshots']} snapshots, "
          f"{lv1['n_event_cid_pairs']} pairs, all_24_seeds_covered={lv1['all_24_seeds_covered']}")

    # Level 2-3 (12 cells × 24 seeds)
    df_l23 = build_level_2_3(df_within)
    safe_write_parquet_v111(df_l23, CROSS_SEED / "within_cid_delta_summary.parquet")
    print(f"  Level 2-3: {len(df_l23)} rows (12 cells × 24 seeds)")

    # Direction consistency 4 段階観察
    df_consistency = build_direction_consistency(df_l23)
    safe_write_parquet_v111(df_consistency, CROSS_SEED / "direction_consistency_24seeds.parquet")

    # 主要観察値
    print(f"\n=== delta_C_within (T+50 - T-50) の cell × 24 seeds 平均 + 4 段階一致 ===")
    sub_C = df_consistency[df_consistency["metric"] == "delta_C_mean"]
    piv_C = sub_C.pivot_table(index="n_core_bin", columns="c_q_partition",
                                  values="mean_across_seeds", aggfunc="first").round(3)
    print(piv_C.to_string())
    print(f"\n--- consistency_label by cell ---")
    piv_lab = sub_C.pivot_table(index="n_core_bin", columns="c_q_partition",
                                  values="consistency_label", aggfunc="first")
    print(piv_lab.to_string())

    print(f"\n=== delta_pulse_within の cell × 24 seeds 平均 ===")
    sub_P = df_consistency[df_consistency["metric"] == "delta_pulse_mean"]
    piv_P = sub_P.pivot_table(index="n_core_bin", columns="c_q_partition",
                                  values="mean_across_seeds", aggfunc="first").round(3)
    print(piv_P.to_string())

    # ルーティング条件抽出 (達成条件 §0.2)
    routing_md = build_routing_conditions(df_consistency, df_l23)
    with open(CROSS_SEED / "v10_12_routing_conditions.md", "w") as f:
        f.write(routing_md)
    print(f"\n  v10_12_routing_conditions.md saved")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
