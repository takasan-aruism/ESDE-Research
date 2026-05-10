#!/usr/bin/env python3
"""v10.12 Step Z: 事前調査フェーズ (実装なし、実測のみ).

Q-Z1: 4 条件複合の母集団実測 (per-seed × 各条件)
Q-Z2: Q3_threshold (lifespan の Q3) 実測
Q-Z3: top_quartile_threshold (familiarity_max) 実測
Q-Z4: formation_relation の時点判定の実現性
Q-Z5: v10.5 機構との整合確認 (Code A 視点、文書読解 + 実装確認)
Q-Z6: cid pool 重なり実測 (v112 4 条件複合 vs v108 top_k_100)
Q-Z7: 規模見積もり

target_step の仮定: cid.birth + 200 (age=200 timing、v10.9/v10.11 慣例)
※ 主題ドキュメント第 3 版が現作業環境に未配置のため、慣例値を仮置き。
   主題ドキュメントで別の target_step が指定されている場合は要 Web Claude 確認。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
DIAG = V105_ROOT / "diag_v105_main_v2"

OUT = V112_ROOT / "outputs" / "step_z"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(V107_ROOT))
from v107_baseline_constructor import _cid_meta_table  # noqa: E402

SEEDS = list(range(24))
RUN_END = 25000
AGE_TARGET = 200  # 仮置き、主題で別値なら要差し替え


def safe_read_csv(p):
    return pd.read_csv(p, low_memory=False)


def build_beta_intervals(seed: int) -> dict[int, list[tuple[int, int]]]:
    """各 cid の (in_step, out_step) 区間 = β member 期間.

    v10.5 機構 A での扱い: cid が β member の間、ghost 化時に Q/C 100% を β に継承。
    本主題の条件 1 「β member ではない (formation_relation in [before, no_alpha])」は
    target_step 時点で cid がいずれの β にも所属していないこと。
    """
    cid_intervals: dict[int, list[tuple[int, int]]] = {}
    for fname in ["alpha_lifecycle_log", "beta_lifecycle_log"]:
        df = safe_read_csv(DIAG / f"integration/{fname}_seed{seed}.csv")
        if df.empty: continue
        id_col = "alpha_id" if "alpha_id" in df.columns else (
            "beta_id" if "beta_id" in df.columns else None)
        if id_col is None: continue
        for aid, sub in df.groupby(id_col):
            births = sub[sub["event_type"] == "birth"]
            deaths = sub[sub["event_type"] == "death"] if "death" in sub["event_type"].values else pd.DataFrame()
            # active_to_recorded を「閉じる時刻」相当として扱う
            recorded = sub[sub["event_type"] == "active_to_recorded"] if "active_to_recorded" in sub["event_type"].values else pd.DataFrame()
            if births.empty: continue
            t_in = int(births.iloc[0]["step"])
            if not deaths.empty:
                t_out = int(deaths.iloc[0]["step"])
            elif not recorded.empty:
                t_out = int(recorded.iloc[0]["step"])
            else:
                t_out = RUN_END
            mems_str = str(births.iloc[0].get("member_cids") or "")
            for c_str in mems_str.split("|"):
                if not c_str.strip(): continue
                try: c = int(c_str)
                except: continue
                cid_intervals.setdefault(c, []).append((t_in, t_out))
    return cid_intervals


def is_beta_member_at(cid: int, t: int, intervals: dict) -> bool:
    for (t_in, t_out) in intervals.get(cid, []):
        if t_in <= t < t_out:
            return True
    return False


def collect_cid_features(seed: int):
    """各 cid の n_core / lifespan / familiarity_max / birth_step / death_step を取得."""
    m = _cid_meta_table(seed)
    death = pd.concat([
        m["host_lost_step"].fillna(RUN_END),
        m["reaped_step"].fillna(RUN_END),
    ], axis=1).min(axis=1)
    m = m.copy()
    m["lifespan"] = (death - m["birth_step"]).clip(lower=0)
    m["death_step"] = death
    m["n_core"] = m["n_core_member"].fillna(0).astype(int)
    m["fam_max"] = m["last_familiarity_max"].fillna(0)
    return m


# ----------------------------------------------------------------------
# Q-Z2: Q3_threshold (lifespan、24 seeds 集計)
# ----------------------------------------------------------------------
def q_z2_lifespan_quartiles():
    all_lifespans = []
    for seed in SEEDS:
        m = collect_cid_features(seed)
        all_lifespans.extend(m["lifespan"].tolist())
    arr = np.array(all_lifespans)
    return {
        "n": int(len(arr)),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "Q1": float(np.percentile(arr, 25)),
        "Q2_median": float(np.percentile(arr, 50)),
        "Q3": float(np.percentile(arr, 75)),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
    }


# ----------------------------------------------------------------------
# Q-Z3: top_quartile (familiarity_max)
# ----------------------------------------------------------------------
def q_z3_familiarity_quartile():
    all_fam = []
    per_seed = {}
    for seed in SEEDS:
        m = collect_cid_features(seed)
        all_fam.extend(m["fam_max"].tolist())
        per_seed[seed] = float(np.percentile(m["fam_max"], 75))
    arr = np.array(all_fam)
    global_q3 = float(np.percentile(arr, 75))
    per_seed_arr = np.array(list(per_seed.values()))
    return {
        "global_q3": global_q3,
        "per_seed_q3_mean": float(per_seed_arr.mean()),
        "per_seed_q3_std": float(per_seed_arr.std()),
        "per_seed_q3_min": float(per_seed_arr.min()),
        "per_seed_q3_max": float(per_seed_arr.max()),
        "per_seed_q3": per_seed,
        "std_to_global_ratio": float(per_seed_arr.std() / global_q3) if global_q3 > 0 else 0,
    }


# ----------------------------------------------------------------------
# Q-Z1: 4 条件複合の母集団 (per-seed)
# ----------------------------------------------------------------------
def q_z1_population(q3_lifespan: float, fam_q3_per_seed: dict, fam_q3_global: float):
    rows = []
    for seed in SEEDS:
        m = collect_cid_features(seed)
        intervals = build_beta_intervals(seed)
        fam_thresh = fam_q3_per_seed[seed]  # per-seed 採用
        n_total = len(m)

        # target_step = birth + AGE_TARGET、ただし t_event >= death なら除外
        cond_results = {
            "cond1_not_beta_member": 0,
            "cond2_long_lifespan": 0,
            "cond3_high_n_core": 0,
            "cond4_high_fam": 0,
            "AND_1_2": 0,
            "AND_1_2_3": 0,
            "AND_all": 0,
        }
        for _, row in m.iterrows():
            cid = int(row["cognitive_id"])
            birth = int(row["birth_step"])
            t_target = birth + AGE_TARGET
            death = int(row["death_step"])
            if t_target >= RUN_END: continue
            if t_target >= death: continue  # death 前に target_step に到達できない

            c1 = not is_beta_member_at(cid, t_target, intervals)
            c2 = row["lifespan"] >= q3_lifespan
            c3 = row["n_core"] >= 5
            c4 = row["fam_max"] >= fam_thresh
            if c1: cond_results["cond1_not_beta_member"] += 1
            if c2: cond_results["cond2_long_lifespan"] += 1
            if c3: cond_results["cond3_high_n_core"] += 1
            if c4: cond_results["cond4_high_fam"] += 1
            if c1 and c2: cond_results["AND_1_2"] += 1
            if c1 and c2 and c3: cond_results["AND_1_2_3"] += 1
            if c1 and c2 and c3 and c4: cond_results["AND_all"] += 1
        rows.append({"seed": seed, "n_total": n_total, **cond_results})
    df = pd.DataFrame(rows)
    return df


# ----------------------------------------------------------------------
# Q-Z4: formation_relation 時点判定の実現性
# ----------------------------------------------------------------------
def q_z4_formation_realizability():
    """既存実装の有無 + 新規実装の規模見積もり."""
    # 既存実装の所在
    existing_impl = []
    for fname, desc in [
        ("developmental/v110/v110_environment_check.py", "build_alpha_beta_intervals (v10.10)"),
        ("developmental/v110/v110_multi_axis_stratified_analyzer.py", "build_cid_features + integration_layer (v10.10)"),
        ("developmental/v111/v111_q_c_inherited_observer.py", "q_c_inherited 起点の within-cid 観察 (v10.11)"),
    ]:
        p = REPO_ROOT / fname
        if p.exists():
            existing_impl.append({"file": fname, "desc": desc, "exists": True})
        else:
            existing_impl.append({"file": fname, "desc": desc, "exists": False})
    return {
        "existing_implementations": existing_impl,
        "data_sources": [
            "alpha_lifecycle_log_seed*.csv (event_type birth / member_ghosted / active_to_recorded)",
            "beta_lifecycle_log_seed*.csv (event_type birth / alpha_added / beta_merged / q_c_inherited / active_to_recorded)",
        ],
        "implementation_scale": "本 Q-Z1 の build_beta_intervals + is_beta_member_at で 30 行程度、既存規約に整合",
        "judgment": "(a) v10.10/v10.11 既存実装を流用、新規実装規模 30 行 → 整合、進める",
    }


# ----------------------------------------------------------------------
# Q-Z5: v10.5 機構との整合 (Code A 視点)
# ----------------------------------------------------------------------
def q_z5_v105_mechanism_check():
    return {
        "v105_mechanism_a": {
            "source": "developmental/v105/v105_integration.py:1035 'β 側: Q/C 100% 継承'",
            "definition": "cid が ghost 化時、その cid が β member なら β が Q/C を 100% 継承。"
                          "α 側はメンバー除外と recorded 化のみ (Q/C 継承なし)",
        },
        "v105_mechanism_c": {
            "source": "v10.5 §85.1 (推定) 'Recorded 永続' / β は death event なし",
            "definition": "active_to_recorded で β は永続化、death events 0 件、"
                          "member_ghosted で α member 除外",
            "note": "「ε=1 漏れ」の具体的実装は本 Step Z で未確認、要主題ドキュメント参照",
        },
        "code_a_view_on_redundancy": {
            "v10_11_already_observed": (
                "v10.11 q_c_inherited 観察で β member cid の C 値が "
                "24 seeds 一貫して正方向に動くことを確認 (delta_C +0.097〜+0.497、 "
                "全 12 cells)、留保 21: ESDE β 機能 (Q/C 継承) の直接観察可能性"
            ),
            "v10_12_condition_1_overlap": (
                "v10.12 条件 1 (β member 除外) は v10.11 結論の実装適用。"
                "atom event 効果と β 継承効果の混在を回避する観点では新規だが、"
                "「β member は C 増加で鈍感化する」という観察は既知"
            ),
            "judgment_candidate": (
                "(b) 部分的に重なる: 条件 1 単独では v10.11 既知の延長、"
                "ただし「4 条件複合 cid (β 非member + 長寿 + n_core 5+ + 高 fam) で "
                "atom event 効果が v108 top_k_100 (β member 含む) より強いか」の比較は v10.12 で初めて。"
                "Web Claude/Taka 判断: 留保事項として「条件 1 は v10.11 既知」を明記して進めるか、主題変更か"
            ),
        },
    }


# ----------------------------------------------------------------------
# Q-Z6: cid pool 重なり (v112 4 条件複合 vs v108 top_k_100)
# ----------------------------------------------------------------------
def q_z6_cid_pool_overlap(q3_lifespan: float, fam_q3_per_seed: dict):
    rows = []
    for seed in SEEDS:
        m = collect_cid_features(seed)
        intervals = build_beta_intervals(seed)
        fam_thresh = fam_q3_per_seed[seed]

        # v112 pool: 4 条件複合
        v112_pool = set()
        for _, row in m.iterrows():
            cid = int(row["cognitive_id"])
            birth = int(row["birth_step"])
            t_target = birth + AGE_TARGET
            death = int(row["death_step"])
            if t_target >= RUN_END or t_target >= death: continue
            if (not is_beta_member_at(cid, t_target, intervals)
                and row["lifespan"] >= q3_lifespan
                and row["n_core"] >= 5
                and row["fam_max"] >= fam_thresh):
                v112_pool.add(cid)

        # v108 pool: top_k_100 by atom_similarity (cid_atom_sim_matrix)
        sim_path = V106_ROOT / "outputs" / "main" / f"cid_atom_sim_matrix_seed{seed}.parquet"
        if not sim_path.exists():
            v108_pool = set()
        else:
            df_sim = pd.read_parquet(sim_path)
            # v10.8 で使われた 25 atom 各々で top_100 cid → unique 集合
            from v108_atom_event_generator import TARGET_ATOMS
            v108_pool = set()
            for atom in TARGET_ATOMS:
                if atom not in df_sim.columns: continue
                top100 = df_sim[["cid", atom]].dropna().sort_values(atom, ascending=False).head(100)
                v108_pool.update(top100["cid"].astype(int).tolist())

        n_v112 = len(v112_pool)
        n_v108 = len(v108_pool)
        overlap = v112_pool & v108_pool
        n_overlap = len(overlap)
        ratio = n_overlap / min(n_v112, n_v108) if min(n_v112, n_v108) > 0 else 0
        rows.append({
            "seed": seed,
            "n_v112_4cond": n_v112,
            "n_v108_top_k_100": n_v108,
            "n_overlap": n_overlap,
            "overlap_ratio_min": float(ratio),
            "overlap_ratio_v112": float(n_overlap / n_v112) if n_v112 > 0 else 0,
            "overlap_ratio_v108": float(n_overlap / n_v108) if n_v108 > 0 else 0,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Q-Z7: 規模見積もり
# ----------------------------------------------------------------------
def q_z7_scale_estimate(q_z1_df, q_z6_df):
    n_v112_total = q_z1_df["AND_all"].sum()
    n_v108_total = q_z6_df["n_v108_top_k_100"].sum()
    # 3 conditions × 25 atoms × cid pool
    # v112: AND_all × 25 atom (循環または atom 別個別 = 主題依存)
    # 仮: 1 cid に 1 atom (循環) とすると events = AND_all 程度
    # baseline 計算は v10.9/v10.10 と同規模 (per-seed ~17 秒) → 24 並列で約 1 分
    return {
        "n_v112_events_estimate_low": int(n_v112_total),  # 1 cid 1 atom
        "n_v112_events_estimate_high": int(n_v112_total * 25),  # 25 atom 全展開
        "n_v108_events": int(n_v108_total),  # v10.8 既存 60,000 events 規模
        "main_run_time_estimate_minutes": "1-3 分 (v10.10/v10.11 相当の 24 並列、events 規模次第)",
        "storage_estimate_mb": "200-400 MB (主題想定、v10.9-v10.11 累計 1.52 GB から +0.2-0.4 GB)",
        "cumulative_storage_estimate_gb": "1.7-1.9 GB / 上限 6 GB (28-32%)、打ち切り 50% に余裕",
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 60)
    print("v10.12 Step Z 事前調査 (実装なし、実測のみ)")
    print("target_step 仮定: cid.birth + 200 (age=200 timing)")
    print("=" * 60)

    print("\n=== Q-Z2: lifespan の Q3 ===")
    qz2 = q_z2_lifespan_quartiles()
    for k, v in qz2.items():
        print(f"  {k}: {v}")
    q3_lifespan = qz2["Q3"]

    print("\n=== Q-Z3: familiarity_max top_quartile ===")
    qz3 = q_z3_familiarity_quartile()
    print(f"  global_q3: {qz3['global_q3']:.2f}")
    print(f"  per_seed_q3 mean: {qz3['per_seed_q3_mean']:.2f}")
    print(f"  per_seed_q3 std: {qz3['per_seed_q3_std']:.2f}")
    print(f"  std_to_global_ratio: {qz3['std_to_global_ratio']:.3f}")
    print(f"  → seed 別採用が妥当 (std/global = {qz3['std_to_global_ratio']:.2f})"
          if qz3['std_to_global_ratio'] > 0.10 else
          f"  → global 共通可 (std/global = {qz3['std_to_global_ratio']:.2f} ≤ 0.10)")

    print("\n=== Q-Z1: 4 条件複合の母集団 (per-seed) ===")
    qz1 = q_z1_population(q3_lifespan, qz3["per_seed_q3"], qz3["global_q3"])
    print(qz1.to_string(index=False))
    print()
    print(f"  AND_all 24 seeds 集計: total={qz1['AND_all'].sum()}, "
          f"mean={qz1['AND_all'].mean():.1f}, "
          f"min={qz1['AND_all'].min()}, "
          f"max={qz1['AND_all'].max()}, "
          f"std={qz1['AND_all'].std():.1f}")
    n_below_30 = (qz1["AND_all"] < 30).sum()
    n_below_10 = (qz1["AND_all"] < 10).sum()
    print(f"  AND_all < 30 seeds (paired_d 信頼性懸念): {n_below_30}/24")
    print(f"  AND_all < 10 seeds (設計破綻判定): {n_below_10}/24")

    print("\n=== Q-Z4: formation_relation 時点判定の実現性 ===")
    qz4 = q_z4_formation_realizability()
    for impl in qz4["existing_implementations"]:
        print(f"  - {impl['file']}: exists={impl['exists']}, {impl['desc']}")
    print(f"  judgment: {qz4['judgment']}")

    print("\n=== Q-Z5: v10.5 機構との整合 (Code A 視点) ===")
    qz5 = q_z5_v105_mechanism_check()
    print(f"  機構 A: {qz5['v105_mechanism_a']['definition']}")
    print(f"  機構 C: {qz5['v105_mechanism_c']['definition']}")
    print(f"\n  Code A 視点 (留保):")
    print(f"  - v10.11 既知: {qz5['code_a_view_on_redundancy']['v10_11_already_observed']}")
    print(f"  - 重複度: {qz5['code_a_view_on_redundancy']['v10_12_condition_1_overlap']}")
    print(f"  - 判断候補: {qz5['code_a_view_on_redundancy']['judgment_candidate']}")

    print("\n=== Q-Z6: cid pool 重なり (v112 vs v108 top_k_100) ===")
    qz6 = q_z6_cid_pool_overlap(q3_lifespan, qz3["per_seed_q3"])
    print(qz6.to_string(index=False))
    print()
    print(f"  overlap_ratio_v112 mean: {qz6['overlap_ratio_v112'].mean():.3f} "
          f"(v112 pool のうち v108 にも含まれる率)")
    print(f"  overlap_ratio_v108 mean: {qz6['overlap_ratio_v108'].mean():.3f} "
          f"(v108 pool のうち v112 にも含まれる率)")

    print("\n=== Q-Z7: 規模見積もり ===")
    qz7 = q_z7_scale_estimate(qz1, qz6)
    for k, v in qz7.items():
        print(f"  {k}: {v}")

    # 出力
    qz1.to_parquet(OUT / "q_z1_population.parquet", index=False)
    pd.DataFrame([qz2]).to_parquet(OUT / "q_z2_lifespan.parquet", index=False)
    pd.DataFrame([{
        "global_q3": qz3["global_q3"],
        "per_seed_q3_mean": qz3["per_seed_q3_mean"],
        "per_seed_q3_std": qz3["per_seed_q3_std"],
        "std_to_global_ratio": qz3["std_to_global_ratio"],
    }]).to_parquet(OUT / "q_z3_familiarity.parquet", index=False)
    qz6.to_parquet(OUT / "q_z6_cid_overlap.parquet", index=False)
    import json
    with open(OUT / "q_z4_5_7_qualitative.json", "w") as f:
        json.dump({"q_z4": qz4, "q_z5": qz5, "q_z7": qz7}, f, indent=2, ensure_ascii=False)

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    print(f"Output: {OUT}")


if __name__ == "__main__":
    sys.exit(main())
