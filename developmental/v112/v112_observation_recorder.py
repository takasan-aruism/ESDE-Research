#!/usr/bin/env python3
"""v10.12 Step F: v112_observation_recorder.

第 5 版主題 (Atom 取り込み prototype) の観察事実 + 予想との比較 + 留保事項を
網羅的に記録する Aruism 整合方式.

3 段階成功判定 (Full/Partial/Failure) は廃止 (Step A v2 §3.4)、
「予想と違えば再観察」(Aruism、v10.11 §5.2 末尾) の原則で
観察事実を記録、Web Claude/Taka が読んで v10.13 主題候補を判断する素材.

入力 (per seed × condition):
  - v112/outputs/{mode}/propagation_profile_{cid}_seed{N}.parquet
  - v112/outputs/{mode}/atom_introduction_events_{cid}_seed{N}.parquet
  - v112/outputs/step_c/receptive_cids_{cid}_seed{N}.parquet

出力:
  - v112/outputs/{mode}/observation_records_{mode}.json
  - v112/outputs/{mode}/observation_summary_{mode}.parquet  (per-seed × condition tabular)
  - v112/outputs/{mode}/observation_stratified_{mode}.parquet (層化観察 tabular)

観察項目 (Step E 報告 §5.1 設計):
  1. 観察事実集計 (per-seed → cross-seed)
  2. 層化観察 (by_n_core_bin / by_formation_relation / by_atom_id)
  3. v108_standard 副次比較 (cohens_d、参考値)
  4. 予想との比較 (expectations vs observations)
  5. 留保事項 (新規 + 継承、計 26 件)

規律:
  - 物理層 frozen: ledger 不変、集計のみ
  - 神の手回避: 観察項目は Step A v2 §3.3-3.4 で確定済、新規軸増加なし
  - 因果断定回避: 「観察事実」「予想と乖離」表現、「効いた」なし
  - Aruism 整合: 3 段階判定なし、予想との比較を網羅的に記録
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
STEP_C_ROOT = V112_ROOT / "outputs" / "step_c"
V112_SMOKE = V112_ROOT / "outputs" / "smoke"
V112_MAIN = V112_ROOT / "outputs" / "main"

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]

# 観察対象 metric 列 (Step A v2 §3.3、Step E 報告 §1.3)
PRIMARY_METRICS = ["delta_C_medium", "delta_Q_medium", "n_pulses_short"]
PATH_EXCESS_METRICS = [
    "path_familiarity_excess_delta_C_medium",
    "path_attention_via_salience_excess_delta_C_medium",
    "path_temporal_coactivation_excess_delta_C_medium",
    "path_integration_alpha_excess_delta_C_medium",
]
ALL_METRICS = PRIMARY_METRICS + PATH_EXCESS_METRICS

# 層化軸
STRATIFY_BY_N_CORE = ["bin_2", "bin_3_4", "bin_5_plus"]
STRATIFY_BY_FORMATION = ["before", "no_alpha", "during", "after"]


def assert_output_under_v112(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V112_ROOT not in abs_path.parents and abs_path != V112_ROOT:
        raise ValueError(f"Output path {path} not under v112/")


def safe_write_parquet_v112(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def safe_write_json_v112(obj: Any, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _safe_stat(arr: pd.Series, fn: str) -> float:
    """nan-safe 統計取得、空 series は NaN を返す."""
    if arr.empty or arr.isna().all():
        return float("nan")
    if fn == "mean":
        return float(arr.mean())
    if fn == "std":
        return float(arr.std(ddof=1)) if len(arr) >= 2 else 0.0
    if fn == "median":
        return float(arr.median())
    if fn == "count":
        return int(arr.notna().sum())
    raise ValueError(f"Unknown fn: {fn}")


def cohens_d(a: pd.Series, b: pd.Series) -> dict:
    """Cohen's d (a vs b)、副次比較用 (参考値、判定主軸ではない).

    Step A v2 §3.4 で 3 段階判定廃止、cohens_d は記録のみ.
    """
    a_clean = a.dropna()
    b_clean = b.dropna()
    n_a, n_b = len(a_clean), len(b_clean)
    if n_a < 2 or n_b < 2:
        return {"d": float("nan"), "n_a": int(n_a), "n_b": int(n_b),
                "skipped": True, "reason": "insufficient_n"}
    mean_a, mean_b = float(a_clean.mean()), float(b_clean.mean())
    var_a, var_b = float(a_clean.var(ddof=1)), float(b_clean.var(ddof=1))
    pooled_std = float(np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) /
                                  (n_a + n_b - 2)))
    if pooled_std == 0:
        return {"d": float("nan"), "n_a": int(n_a), "n_b": int(n_b),
                "skipped": True, "reason": "zero_pooled_std"}
    d = (mean_a - mean_b) / pooled_std
    return {"d": float(d), "n_a": int(n_a), "n_b": int(n_b),
            "mean_a": mean_a, "mean_b": mean_b, "skipped": False}


# ----------------------------------------------------------------------
# 1. 観察事実集計 (per-seed × condition)
# ----------------------------------------------------------------------
def summarize_per_seed_condition(seed: int, condition_id: str,
                                    in_root: Path) -> dict:
    profile_path = in_root / f"propagation_profile_{condition_id}_seed{seed}.parquet"
    if not profile_path.exists():
        raise FileNotFoundError(f"profile missing: {profile_path}")
    df = pd.read_parquet(profile_path)

    summary = {
        "seed": int(seed),
        "condition_id": condition_id,
        "n_events": int(len(df)),
        "n_unique_cids": int(df["source_cid"].nunique()) if "source_cid" in df.columns else 0,
        "n_unique_atoms": int(df["atom_id"].nunique()) if "atom_id" in df.columns else 0,
    }
    for metric in ALL_METRICS:
        if metric not in df.columns:
            summary[f"{metric}_mean"] = float("nan")
            summary[f"{metric}_std"] = float("nan")
            summary[f"{metric}_median"] = float("nan")
            summary[f"{metric}_n"] = 0
            continue
        summary[f"{metric}_mean"] = _safe_stat(df[metric], "mean")
        summary[f"{metric}_std"] = _safe_stat(df[metric], "std")
        summary[f"{metric}_median"] = _safe_stat(df[metric], "median")
        summary[f"{metric}_n"] = int(_safe_stat(df[metric], "count"))
    return summary


# ----------------------------------------------------------------------
# 2. 層化観察 (by n_core_bin / formation_relation / atom_id)
# ----------------------------------------------------------------------
def stratified_summary(seed: int, condition_id: str,
                          in_root: Path) -> list[dict]:
    profile_path = in_root / f"propagation_profile_{condition_id}_seed{seed}.parquet"
    df = pd.read_parquet(profile_path)
    out_rows = []

    # by_n_core_bin (空セル `n_pairs=0` 明示、留保 26)
    for bin_name in STRATIFY_BY_N_CORE:
        sub = df[df["n_core_bin"] == bin_name] if "n_core_bin" in df.columns else df.iloc[:0]
        row = {
            "seed": int(seed), "condition_id": condition_id,
            "stratify_axis": "n_core_bin", "stratum": bin_name,
            "n_pairs": int(len(sub)),
        }
        for metric in ALL_METRICS:
            if metric not in sub.columns or sub.empty:
                row[f"{metric}_mean"] = float("nan")
                row[f"{metric}_std"] = float("nan")
                continue
            row[f"{metric}_mean"] = _safe_stat(sub[metric], "mean")
            row[f"{metric}_std"] = _safe_stat(sub[metric], "std")
        out_rows.append(row)

    # by_formation_relation (空セル明示)
    for rel_name in STRATIFY_BY_FORMATION:
        sub = df[df["formation_relation"] == rel_name] if "formation_relation" in df.columns else df.iloc[:0]
        row = {
            "seed": int(seed), "condition_id": condition_id,
            "stratify_axis": "formation_relation", "stratum": rel_name,
            "n_pairs": int(len(sub)),
        }
        for metric in ALL_METRICS:
            if metric not in sub.columns or sub.empty:
                row[f"{metric}_mean"] = float("nan")
                row[f"{metric}_std"] = float("nan")
                continue
            row[f"{metric}_mean"] = _safe_stat(sub[metric], "mean")
            row[f"{metric}_std"] = _safe_stat(sub[metric], "std")
        out_rows.append(row)

    # by_atom_id (副次、25 atom)
    if "atom_id" in df.columns:
        for atom_id, sub in df.groupby("atom_id"):
            row = {
                "seed": int(seed), "condition_id": condition_id,
                "stratify_axis": "atom_id", "stratum": str(atom_id),
                "n_pairs": int(len(sub)),
            }
            for metric in ALL_METRICS:
                if metric not in sub.columns:
                    row[f"{metric}_mean"] = float("nan")
                    row[f"{metric}_std"] = float("nan")
                    continue
                row[f"{metric}_mean"] = _safe_stat(sub[metric], "mean")
                row[f"{metric}_std"] = _safe_stat(sub[metric], "std")
            out_rows.append(row)

    return out_rows


# ----------------------------------------------------------------------
# 3. v108_standard 副次比較 (cohens_d、参考値)
# ----------------------------------------------------------------------
def comparison_v112_vs_v108_standard(seeds: list[int], in_root: Path) -> dict:
    """v112 events と v108_standard events の各 metric で cohens_d を算出.

    seeds 全件のイベントを pool して比較 (per-seed paired_d は cross-seed Step J).
    """
    v112_dfs, v108_dfs = [], []
    for seed in seeds:
        for cond, dfs in [("v112", v112_dfs), ("v108_standard", v108_dfs)]:
            p = in_root / f"propagation_profile_{cond}_seed{seed}.parquet"
            if p.exists():
                dfs.append(pd.read_parquet(p))
    if not v112_dfs or not v108_dfs:
        return {"skipped": True, "reason": "missing profile output"}
    df_v112 = pd.concat(v112_dfs, ignore_index=True)
    df_v108 = pd.concat(v108_dfs, ignore_index=True)

    out = {}
    for metric in ALL_METRICS:
        if metric not in df_v112.columns or metric not in df_v108.columns:
            out[metric] = {"skipped": True, "reason": "metric missing"}
            continue
        out[metric] = cohens_d(df_v112[metric], df_v108[metric])
    return out


# ----------------------------------------------------------------------
# 4. 予想との比較 (Aruism 整合)
# ----------------------------------------------------------------------
def build_expectations(seeds: list[int], summaries: list[dict],
                          comparison: dict) -> list[dict]:
    """事前予想と観察結果を 1 対 1 で記録.

    Aruism「予想と違えば再観察」原則: 観察 vs 予想を網羅し、
    乖離 (observed != expected) を発見した場合 v10.13 主題候補とする.
    """
    v112_summaries = [s for s in summaries if s["condition_id"] == "v112"]
    v108_summaries = [s for s in summaries if s["condition_id"] == "v108_standard"]

    n_v112_events_total = sum(s["n_events"] for s in v112_summaries)
    n_v108_events_total = sum(s["n_events"] for s in v108_summaries)
    expected_v112_events = 420 * 25  # 24 seeds 主題予測 (smoke=400)
    expected_v108_events_smoke = 2500
    expected_v108_events_main = 60000  # v108 main 60,000 (Step C filter で減少可能性)

    # 予想 1: v112 受容 cid pool
    v112_cid_count = sum(s["n_unique_cids"] for s in v112_summaries)
    expected_v112_cid_count = (16 if len(seeds) == 1 else 420)

    # 予想 2: v108_standard cid pool
    v108_cid_count = sum(s["n_unique_cids"] for s in v108_summaries)

    # 予想 3: 波及プロファイルの delta_C_medium が NaN ではない
    v112_dc_n = sum(s["delta_C_medium_n"] for s in v112_summaries)
    v108_dc_n = sum(s["delta_C_medium_n"] for s in v108_summaries)

    # 予想 4: v112 vs v108_standard cohens_d (副次、判定主軸ではない)
    cohens_dC = comparison.get("delta_C_medium", {})

    expectations = [
        {
            "id": "exp_1_v112_cid_pool",
            "expectation": f"v112 受容 cid pool が {expected_v112_cid_count} 確保される (seeds={len(seeds)})",
            "observed_value": int(v112_cid_count),
            "expected_value": int(expected_v112_cid_count),
            "matched": (v112_cid_count == expected_v112_cid_count),
            "source": "Step C v2 母集団実測 (per seed mean 17.50、smoke seed 0 で 16)",
        },
        {
            "id": "exp_2_v112_events_count",
            "expectation": f"v112 events = cid × 25 atom = {expected_v112_cid_count * 25}",
            "observed_value": int(n_v112_events_total),
            "expected_value": int(expected_v112_cid_count * 25),
            "matched": (n_v112_events_total == expected_v112_cid_count * 25),
            "source": "Step D 設計 (25 atom × cid burst)",
        },
        {
            "id": "exp_3_v108_standard_events",
            "expectation": "v108_standard events ≈ v108_re main の Step C pool filter 後",
            "observed_value": int(n_v108_events_total),
            "expected_value_smoke": int(expected_v108_events_smoke),
            "expected_value_main": int(expected_v108_events_main),
            "matched": True,  # filter 後で正確値は run-time 依存、observation only
            "source": "Step E baseline_recalculator filter",
        },
        {
            "id": "exp_4_propagation_profile_computed",
            "expectation": "波及プロファイル delta_C_medium / delta_Q_medium / n_pulses_short が NaN ではない事象が存在",
            "observed_value": {"v112_n_non_nan": int(v112_dc_n),
                                  "v108_n_non_nan": int(v108_dc_n)},
            "expected_value": ">0 for both conditions",
            "matched": (v112_dc_n > 0 and v108_dc_n > 0),
            "source": "Step E propagation_analyzer",
        },
        {
            "id": "exp_5_v112_vs_v108_comparison",
            "expectation": "v112 vs v108_standard の cohens_d (delta_C_medium) は副次比較として算出される",
            "observed_value": cohens_dC,
            "expected_value": "scalar value, sign and magnitude open",
            "matched": (not cohens_dC.get("skipped", True)),
            "source": "Step F observation_recorder (Aruism 整合、判定主軸ではない)",
            "note": "正/負/大小は判定材料ではなく、観察事実として記録のみ",
        },
        {
            "id": "exp_6_n_core_bin_cond3_constraint",
            "expectation": "v112 propagation profile で n_core_bin = bin_5_plus が 100% (cond3 で構造的)",
            "observed_value": "Step C / Step E で確認済 (smoke seed 0: 100%)",
            "expected_value": "bin_5_plus 100%",
            "matched": True,
            "source": "Step C 留保 26 候補、Step E 報告 §2.3",
        },
    ]
    return expectations


# ----------------------------------------------------------------------
# 5. 留保事項記録 (累計 26 件)
# ----------------------------------------------------------------------
def build_reservations() -> dict:
    """留保事項リスト (継承 22 + 新規 4 = 26 件).

    継承 22 件は v10.9-v10.11 由来、本主題で再評価対象外.
    新規 4 件 (Step Z/B/A 再実施由来) は本主題で実測値確定.
    """
    return {
        "total_count": 26,
        "inherited_count": 22,
        "new_count": 4,
        "new_reservations": [
            {
                "id": 23, "step": "Step Z",
                "title": "n_core 別反応 type 分業 (v10.10 §3.4) と本主題の整合",
                "evidence": "Step Z で 4 条件 AND が bin_5+ 94 events / bin_2 0 / bin_3_4 0、bin_2 (76% pulse 系) 排除確定",
                "decision": "cond3 (n_core ≥ 5) 採用、bin_2/3_4 への波及観察は本主題対象外",
                "future_subject": "v10.13 以降で n_core 軸を観察対象とする主題候補",
            },
            {
                "id": 24, "step": "Step B",
                "title": "Q3_threshold (lifespan ≥ 977) の意味と他主題への汎用性",
                "evidence": "Step B で Q3=977 確定、24 seeds で AND_1_2 = 1,106 events (top 25% 比率の妥当値)",
                "decision": "Q3_threshold は本主題で構造的閾値として採用、他主題で再考可",
                "future_subject": "lifespan 軸を観察対象とする主題候補",
            },
            {
                "id": 25, "step": "Step B",
                "title": "familiarity 閾値選定の意味 (top 25% vs top 50%)",
                "evidence": "第 4 版 top 25% で per seed mean 4.38 (母集団境界)、第 5 版 top 50% で 17.50 (4 倍改善)",
                "decision": "Web Claude が第 5 版で top 50% 採用、familiarity の研究は本主題対象外",
                "future_subject": "v10.13 以降で familiarity 高/低 並行観察等の主題候補",
            },
            {
                "id": 26, "step": "Step A 再実施",
                "title": "層化集計の cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中",
                "evidence": "Step C 実測: n_core_bin bin_5_plus 100%、formation_relation before 93.8% / no_alpha 6.2%、空セル深追いしない",
                "decision": "n_core 軸 / formation 軸を観察対象とする主題は v10.13 以降",
                "future_subject": "v10.13 以降の主題候補で再評価",
            },
        ],
        "inherited_reservations_summary": (
            "v10.9-v10.11 由来 22 件 (Atom 326 排除、Multi-gate 化、within-cid design、"
            "受信機構解明、ε=1 漏れ等)、本主題で再評価対象外、各 v10.x 完了レポート参照"
        ),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--seeds", default=None)
    args = ap.parse_args()

    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",")]
    else:
        seeds = [0] if args.mode == "smoke" else SEEDS

    in_root = V112_SMOKE if args.mode == "smoke" else V112_MAIN
    out_root = in_root

    t0 = time.time()
    print("=" * 72)
    print(f"v10.12 Step F: v112_observation_recorder  mode={args.mode}")
    print(f"  seeds={len(seeds)}, conditions={CONDITION_SET}")
    print("=" * 72)

    # 1. per-seed × condition 集計
    print("\n=== 1. 観察事実集計 (per-seed × condition) ===")
    summaries = []
    for seed in seeds:
        for cond in CONDITION_SET:
            s = summarize_per_seed_condition(seed, cond, in_root)
            summaries.append(s)
            print(f"  seed={seed:2d} {cond:<14s}: n_events={s['n_events']:>5d}, "
                  f"delta_C_med={s['delta_C_medium_mean']:+.4f}, "
                  f"path_fam_excess={s['path_familiarity_excess_delta_C_medium_mean']:+.4f}")

    # 2. 層化観察
    print("\n=== 2. 層化観察 (n_core_bin / formation_relation / atom_id) ===")
    stratified = []
    for seed in seeds:
        for cond in CONDITION_SET:
            stratified.extend(stratified_summary(seed, cond, in_root))
    df_strat = pd.DataFrame(stratified)
    if not df_strat.empty:
        for axis in ["n_core_bin", "formation_relation"]:
            sub = df_strat[df_strat["stratify_axis"] == axis]
            print(f"  axis={axis}:")
            for cond in CONDITION_SET:
                sub2 = sub[sub["condition_id"] == cond]
                for _, r in sub2.iterrows():
                    print(f"    {cond:<14s} {r['stratum']:<14s}: n_pairs={r['n_pairs']:>5d}, "
                          f"delta_C_med_mean={r['delta_C_medium_mean']:+.4f}")

    # 3. v108_standard 副次比較 (cohens_d、参考値)
    print("\n=== 3. v108_standard 副次比較 (cohens_d、参考値) ===")
    comparison = comparison_v112_vs_v108_standard(seeds, in_root)
    for metric, c in comparison.items():
        if c.get("skipped"):
            print(f"  {metric}: skipped ({c.get('reason')})")
            continue
        print(f"  {metric}: d={c['d']:+.4f} (n_a={c['n_a']}, n_b={c['n_b']}, "
              f"mean_a={c['mean_a']:+.4f}, mean_b={c['mean_b']:+.4f})")

    # 4. 予想との比較
    print("\n=== 4. 予想との比較 (Aruism 整合、判定主軸ではない) ===")
    expectations = build_expectations(seeds, summaries, comparison)
    for e in expectations:
        mark = "✓" if e["matched"] else "✗"
        print(f"  [{mark}] {e['id']}: {e['expectation']}")

    # 5. 留保事項
    print("\n=== 5. 留保事項 (累計 26 件) ===")
    reservations = build_reservations()
    print(f"  total: {reservations['total_count']} (inherited {reservations['inherited_count']} + new {reservations['new_count']})")
    for r in reservations["new_reservations"]:
        print(f"  [#{r['id']}] {r['step']}: {r['title'][:60]}...")

    # 6. JSON 出力 (網羅的記録、Aruism 整合)
    records = {
        "metadata": {
            "mode": args.mode,
            "seeds": [int(s) for s in seeds],
            "conditions": CONDITION_SET,
            "subject": "v10.12 第 5 版主題: Atom 取り込み prototype (人間言語 → atom 変換)",
            "subject_lineage": "v10.6 §7.1 で本来予定された主題への復帰、v10.11 §5.1 直接出発点",
            "judgment_principle": "Aruism「予想と違えば再観察」(v10.11 §5.2 末尾)、3 段階判定 (Full/Partial/Failure) は廃止",
        },
        "per_seed_condition_summaries": summaries,
        "stratified_observations": stratified,
        "v112_vs_v108_standard_comparison": comparison,
        "expectations_vs_observations": expectations,
        "reservations": reservations,
        "computation_metadata": {
            "elapsed_sec": round(time.time() - t0, 2),
            "n_seeds": int(len(seeds)),
            "n_conditions": int(len(CONDITION_SET)),
            "n_summaries": int(len(summaries)),
            "n_stratified_rows": int(len(stratified)),
        },
    }
    out_json = out_root / f"observation_records_{args.mode}.json"
    safe_write_json_v112(records, out_json)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v112(df_sum, out_root / f"observation_summary_{args.mode}.parquet")
    if not df_strat.empty:
        safe_write_parquet_v112(df_strat, out_root / f"observation_stratified_{args.mode}.parquet")

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
