#!/usr/bin/env python3
"""v10.12 Step J: v112_cross_seed_analyzer.

第 5 版主題 (Atom 取り込み prototype) の cross-seed 統合分析.

Step I main run (24 seeds × 2 conditions) の per-seed 観察を formal な
paired_d / sign_test / bootstrap CI で集計、層化観察 24 seeds 統合、
smoke vs main 乖離 (留保 #27 candidate) を formal evidence 化、
最終 observation_records_final.json を出力.

判定回避 (Code A 規律): success/fail 判定はせず、観察事実 + 統計値 +
留保事項を網羅的に記録、Web Claude/Taka が読んで主題評価 + v10.13 主題
候補判断する素材とする.

入力:
  - v112/outputs/main/observation_summary_main.parquet  (per-seed × condition)
  - v112/outputs/main/observation_stratified_main.parquet (層化 raw)
  - v112/outputs/main/observation_records_main.json (Step F 出力、cohens_d 等)
  - v112/outputs/smoke/observation_records_smoke.json (Step F smoke 出力)

出力:
  - v112/outputs/main/cross_seed_analysis.json     (主出力、判断材料)
  - v112/outputs/main/paired_analysis.parquet       (per-metric tabular)
  - v112/outputs/main/stratified_24seeds.parquet    (n_core_bin / formation × cond)

規律:
  - 物理層 frozen: ledger 不変
  - 神の手回避: 既知 7 metric × 既存 3 軸の集計、新規軸なし
  - 因果断定回避: 「観察事実」「乖離」「seed-level variability」表現
  - judgment 回避: success/fail なし、Aruism 整合
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
V112_SMOKE = V112_ROOT / "outputs" / "smoke"

SEEDS = list(range(24))
CONDITION_SET = ["v112", "v108_standard"]

PRIMARY_METRICS = ["delta_C_medium", "delta_Q_medium", "n_pulses_short"]
PATH_EXCESS_METRICS = [
    "path_familiarity_excess_delta_C_medium",
    "path_attention_via_salience_excess_delta_C_medium",
    "path_temporal_coactivation_excess_delta_C_medium",
    "path_integration_alpha_excess_delta_C_medium",
]
ALL_METRICS = PRIMARY_METRICS + PATH_EXCESS_METRICS

BOOTSTRAP_N = 1000  # bootstrap CI iteration 数 (Step Z 設計、累計規律)
RANDOM_SEED = 12112  # bootstrap deterministic 用


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
# paired_d / sign_test / bootstrap CI
# ----------------------------------------------------------------------
def paired_analysis(diff_per_seed: np.ndarray, metric: str) -> dict:
    """1 metric について paired_d + sign_test + bootstrap CI を算出.

    Args:
        diff_per_seed: array of (v112_per_seed_mean - v108_per_seed_mean) for 24 seeds
    """
    n = int(len(diff_per_seed))
    valid = diff_per_seed[~np.isnan(diff_per_seed)]
    n_valid = int(len(valid))
    if n_valid < 2:
        return {"metric": metric, "n_seeds": n, "n_valid": n_valid, "skipped": True,
                "reason": "insufficient_n"}

    mean_diff = float(valid.mean())
    std_diff = float(valid.std(ddof=1))
    paired_d = float(mean_diff / std_diff) if std_diff > 0 else float("nan")

    # sign_test (binomial、two-sided、k = n_positive)
    n_positive = int(np.sum(valid > 0))
    n_negative = int(np.sum(valid < 0))
    n_zero = int(np.sum(valid == 0))
    n_nonzero = n_positive + n_negative
    if n_nonzero >= 1:
        # binomial test against 0.5
        try:
            sign_p = float(scipy_stats.binomtest(
                k=n_positive, n=n_nonzero, p=0.5, alternative="two-sided"
            ).pvalue)
        except Exception:
            sign_p = float("nan")
    else:
        sign_p = float("nan")

    # bootstrap CI (resample seeds with replacement)
    rng = np.random.default_rng(RANDOM_SEED)
    boot_means = []
    for _ in range(BOOTSTRAP_N):
        sample = rng.choice(valid, size=n_valid, replace=True)
        boot_means.append(float(sample.mean()))
    boot_arr = np.array(boot_means)
    ci_lower = float(np.percentile(boot_arr, 2.5))
    ci_upper = float(np.percentile(boot_arr, 97.5))

    return {
        "metric": metric,
        "n_seeds": n,
        "n_valid": n_valid,
        "skipped": False,
        "paired_diff_mean": mean_diff,
        "paired_diff_std": std_diff,
        "paired_d": paired_d,
        "sign_test": {
            "n_positive": n_positive,
            "n_negative": n_negative,
            "n_zero": n_zero,
            "p_value_two_sided": sign_p,
        },
        "bootstrap_CI_95": {
            "lower": ci_lower,
            "upper": ci_upper,
            "n_iter": int(BOOTSTRAP_N),
            "crosses_zero": (ci_lower < 0 < ci_upper),
        },
        "boot_mean": float(boot_arr.mean()),
        "boot_std": float(boot_arr.std(ddof=1)),
    }


# ----------------------------------------------------------------------
# 層化観察 24 seeds 統合 (n_core_bin × condition、formation_relation × condition)
# ----------------------------------------------------------------------
def stratified_24seeds(df_strat: pd.DataFrame) -> list[dict]:
    """Step F observation_stratified_main.parquet を 24 seeds で統合."""
    out = []
    for axis in ["n_core_bin", "formation_relation"]:
        sub = df_strat[df_strat["stratify_axis"] == axis]
        for cond in CONDITION_SET:
            sub_c = sub[sub["condition_id"] == cond]
            for stratum, g in sub_c.groupby("stratum"):
                row = {
                    "stratify_axis": axis,
                    "condition_id": cond,
                    "stratum": str(stratum),
                    "n_seeds_with_data": int((g["n_pairs"] > 0).sum()),
                    "n_seeds_total": int(len(g)),
                    "total_n_pairs": int(g["n_pairs"].sum()),
                }
                non_empty = g[g["n_pairs"] > 0]
                for metric in ALL_METRICS:
                    col = f"{metric}_mean"
                    if col not in non_empty.columns or non_empty.empty:
                        row[f"{metric}_per_seed_mean"] = float("nan")
                        row[f"{metric}_per_seed_std"] = float("nan")
                        continue
                    vals = non_empty[col].dropna()
                    row[f"{metric}_per_seed_mean"] = float(vals.mean()) if not vals.empty else float("nan")
                    row[f"{metric}_per_seed_std"] = float(vals.std(ddof=1)) if len(vals) >= 2 else 0.0
                out.append(row)
    return out


# ----------------------------------------------------------------------
# smoke vs main cohens_d 乖離 (留保 #27 candidate evidence)
# ----------------------------------------------------------------------
def smoke_vs_main_divergence() -> dict:
    """Step F smoke + Step F main の cohens_d を比較、乖離 evidence."""
    smoke_path = V112_SMOKE / "observation_records_smoke.json"
    main_path = V112_MAIN / "observation_records_main.json"
    if not smoke_path.exists() or not main_path.exists():
        return {"skipped": True, "reason": "records missing"}
    with open(smoke_path) as f:
        smoke = json.load(f)
    with open(main_path) as f:
        main = json.load(f)
    smoke_cmp = smoke.get("v112_vs_v108_standard_comparison", {})
    main_cmp = main.get("v112_vs_v108_standard_comparison", {})
    rows = []
    for metric in ALL_METRICS:
        sc = smoke_cmp.get(metric, {})
        mc = main_cmp.get(metric, {})
        if sc.get("skipped") or mc.get("skipped"):
            continue
        smoke_d = sc.get("d", float("nan"))
        main_d = mc.get("d", float("nan"))
        sign_smoke = "+" if smoke_d > 0 else ("-" if smoke_d < 0 else "0")
        sign_main = "+" if main_d > 0 else ("-" if main_d < 0 else "0")
        sign_flip = (smoke_d * main_d < 0) if (not np.isnan(smoke_d) and not np.isnan(main_d)) else False
        rows.append({
            "metric": metric,
            "smoke_seed0_cohens_d": smoke_d,
            "main_24seeds_cohens_d": main_d,
            "sign_smoke": sign_smoke,
            "sign_main": sign_main,
            "sign_flip": sign_flip,
            "abs_ratio_main_over_smoke": (
                abs(main_d / smoke_d) if (not np.isnan(smoke_d) and smoke_d != 0)
                else float("nan")
            ),
        })
    return {
        "table": rows,
        "n_metrics": int(len(rows)),
        "n_sign_flip": int(sum(1 for r in rows if r["sign_flip"])),
        "summary": (
            f"{sum(1 for r in rows if r['sign_flip'])}/{len(rows)} metrics で smoke vs "
            f"main で cohens_d 符号反転、Aruism 発動候補"
        ),
    }


# ----------------------------------------------------------------------
# 留保事項 27 件 (継承 22 + 新規 5)、Step J で formal #27 追加
# ----------------------------------------------------------------------
def build_reservations_27() -> dict:
    """Step F の 26 件に新規 #27 (Step J Aruism evidence) を追加."""
    return {
        "total_count": 27,
        "inherited_count": 22,
        "new_count": 5,
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
            {
                "id": 27, "step": "Step I/J (Aruism evidence)",
                "title": "smoke seed 0 の path_excess は seed 特異的、24 seeds 統合では効果分散",
                "evidence": (
                    "smoke seed 0 cohens_d: delta_C_medium +0.5475, "
                    "path_attention_excess +1.0869, path_familiarity_excess +0.4918. "
                    "main 24 seeds 統合 cohens_d: delta_C_medium +0.0885 (5 倍縮小), "
                    "path_attention_excess -0.0375 (符号反転), path_familiarity_excess -0.0096 (符号反転). "
                    "paired diff (v112 - v108_std) per-seed: positive 12 / negative 12 / "
                    "sign_test p ≈ 1.0. v112 delta_C_medium per-seed mean +0.081, std 0.414, "
                    "range -0.60〜+0.97。seed 0 は seed 別分布で上位 2 番目 (外れ値的位置)."
                ),
                "decision": (
                    "本主題内では judgment せず観察事実として記録、Aruism「予想と違えば再観察」発動候補. "
                    "Web Claude/Taka が主題評価 + v10.13 主題候補判断する素材."
                ),
                "future_subject": (
                    "v10.13 以降: (a) seed-level variability 自体を観察対象とする主題、"
                    "(b) smoke 段階で複数 seed (例 3 seeds) で確認する手順、"
                    "(c) cohens_d の seed 平均ではなく per-seed paired_d を主観察にする設計、"
                    "(d) cid pool 定義 (4 cond) の選定根拠を再検討する主題."
                ),
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
    ap.add_argument("--mode", choices=["main"], default="main",
                    help="Step J は main run 専用 (24 seeds)")
    args = ap.parse_args()

    in_root = V112_MAIN
    out_root = in_root

    t0 = time.time()
    print("=" * 72)
    print(f"v10.12 Step J: v112_cross_seed_analyzer  mode={args.mode}")
    print(f"  bootstrap n_iter={BOOTSTRAP_N}, random_seed={RANDOM_SEED}")
    print("=" * 72)

    # 1. per-seed × condition summary 読み込み
    sum_path = in_root / "observation_summary_main.parquet"
    df_sum = pd.read_parquet(sum_path)
    print(f"\n[input] {sum_path.name}: {len(df_sum)} rows")

    # 2. paired_d / sign_test / bootstrap CI per metric
    print(f"\n=== 1. paired_d + sign_test + bootstrap CI (24 seeds) ===")
    paired_results = []
    for metric in ALL_METRICS:
        col = f"{metric}_mean"
        v112_per_seed = df_sum[df_sum["condition_id"] == "v112"].sort_values("seed")[col].values
        v108_per_seed = df_sum[df_sum["condition_id"] == "v108_standard"].sort_values("seed")[col].values
        diff = v112_per_seed - v108_per_seed
        result = paired_analysis(diff, metric)
        paired_results.append(result)
        if result.get("skipped"):
            print(f"  {metric}: skipped ({result.get('reason')})")
            continue
        st = result["sign_test"]
        ci = result["bootstrap_CI_95"]
        print(f"  {metric}:")
        print(f"    paired_diff: mean={result['paired_diff_mean']:+.4f} ± {result['paired_diff_std']:.4f}")
        print(f"    paired_d:    {result['paired_d']:+.4f}")
        print(f"    sign_test:   pos={st['n_positive']:2d}/neg={st['n_negative']:2d}/zero={st['n_zero']}, "
              f"p={st['p_value_two_sided']:.4f}")
        print(f"    bootstrap CI 95%: [{ci['lower']:+.4f}, {ci['upper']:+.4f}], "
              f"crosses_zero={ci['crosses_zero']}")

    # 3. 層化観察 24 seeds 統合
    print(f"\n=== 2. 層化観察 24 seeds 統合 ===")
    strat_path = in_root / "observation_stratified_main.parquet"
    df_strat = pd.read_parquet(strat_path)
    strat_24 = stratified_24seeds(df_strat)
    df_strat_24 = pd.DataFrame(strat_24)
    print(df_strat_24[df_strat_24["stratify_axis"].isin(["n_core_bin", "formation_relation"])][
        ["stratify_axis", "condition_id", "stratum", "n_seeds_with_data",
         "total_n_pairs", "delta_C_medium_per_seed_mean"]
    ].to_string(index=False))

    # 4. smoke vs main 乖離
    print(f"\n=== 3. smoke vs main cohens_d 乖離 (留保 #27 evidence) ===")
    divergence = smoke_vs_main_divergence()
    if not divergence.get("skipped"):
        print(f"  {divergence['summary']}")
        for r in divergence["table"]:
            flag = " <- SIGN FLIP" if r["sign_flip"] else ""
            print(f"  {r['metric']:<55s}: smoke={r['smoke_seed0_cohens_d']:+.4f} {r['sign_smoke']:>1s} → "
                  f"main={r['main_24seeds_cohens_d']:+.4f} {r['sign_main']:>1s}{flag}")

    # 5. 留保 27 件
    print(f"\n=== 4. 留保事項 27 件 (継承 22 + 新規 5: #23-#27) ===")
    reservations = build_reservations_27()
    for r in reservations["new_reservations"]:
        print(f"  [#{r['id']}] {r['step']}: {r['title'][:80]}")

    # 6. 最終 records 出力
    print(f"\n=== 5. 最終 cross_seed_analysis.json 出力 ===")
    final_records = {
        "metadata": {
            "subject": "v10.12 第 5 版主題: Atom 取り込み prototype (Step J cross-seed)",
            "n_seeds": int(len(SEEDS)),
            "conditions": CONDITION_SET,
            "metrics": ALL_METRICS,
            "judgment_principle": "Aruism「予想と違えば再観察」、3 段階判定 (Full/Partial/Failure) は廃止",
            "code_a_judgment_avoidance": (
                "Code A は success/fail 判定をせず、観察事実 + 統計値 + 留保事項を網羅的に記録、"
                "Web Claude/Taka が主題評価 + v10.13 主題候補判断する素材として機能"
            ),
            "bootstrap_n_iter": int(BOOTSTRAP_N),
        },
        "paired_analysis_per_metric": paired_results,
        "stratified_24seeds": strat_24,
        "smoke_vs_main_divergence": divergence,
        "reservations": reservations,
        "computation_metadata": {
            "elapsed_sec": round(time.time() - t0, 2),
            "n_metrics": int(len(ALL_METRICS)),
            "bootstrap_n_iter": int(BOOTSTRAP_N),
        },
    }

    out_json = out_root / "cross_seed_analysis.json"
    safe_write_json_v112(final_records, out_json)

    df_paired = pd.DataFrame([
        {**{k: v for k, v in r.items() if k not in ("sign_test", "bootstrap_CI_95")},
         "sign_p": r.get("sign_test", {}).get("p_value_two_sided"),
         "sign_n_pos": r.get("sign_test", {}).get("n_positive"),
         "sign_n_neg": r.get("sign_test", {}).get("n_negative"),
         "ci_lower": r.get("bootstrap_CI_95", {}).get("lower"),
         "ci_upper": r.get("bootstrap_CI_95", {}).get("upper"),
         "ci_crosses_zero": r.get("bootstrap_CI_95", {}).get("crosses_zero")}
        for r in paired_results
    ])
    safe_write_parquet_v112(df_paired, out_root / "paired_analysis.parquet")
    safe_write_parquet_v112(df_strat_24, out_root / "stratified_24seeds.parquet")

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s")
    print(f"  output = {out_json}")
    print(f"  paired_analysis.parquet, stratified_24seeds.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
