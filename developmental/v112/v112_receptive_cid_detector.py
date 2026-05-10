#!/usr/bin/env python3
"""v10.12 Step C: receptive_cid_detector_v112.

第 5 版主題 (Atom 取り込み prototype、v10.11 §5.1 直接出発点) の受容 cid 検出器.

入力 cond セット:
- "v112"           : cond1 ¬β + cond2 lifespan ≥ Q3=977 + cond3 n_core ≥ 5
                     + cond4 fam_max ≥ per-seed top 50% (median)
- "v108_standard"  : 既存 v108 出力流用 (top_k_100 by atom_similarity per atom、副次比較対象)

出力:
- per-seed receptive_cids_v112_seed{N}.parquet    (cid + metadata)
- per-seed receptive_cids_v108_standard_seed{N}.parquet (cid + metadata)
- run_summary.json (per-seed events 数 + Step B 補完値整合確認)

target_step = cid.birth + 200 (v10.9/v10.11 慣例、age=200 timing)
Q3_THRESHOLD = 977 (Step Z 実測、v10.10 §3.2 整合)

規律:
- §35 #9 上位資料読了済 (v10.11 §5.1, v10.10 §3, v10.5 §7, v10.7 §87, v10.8 §6.8)
- §35 #10 駆動要因 = Atom 取り込み prototype 動作確認、観察軸増加なし
- §34 #37 n_core_bin / formation_relation を metadata 列で同梱、層化集計可
- 物理層 frozen (本ファイルは ledger 不変、cid 抽出のみ)
- 神の手回避 (cond1-4 構造的判定、ハンドチューニングなし)

Step B 補完値 (v112_code_recognition_check_v2.md §2.1):
- v112 cond4 top 50% per seed mean = 17.50 / total = 420 / min/max = 13/23
- top_50_threshold per-seed mean = 41.40, std = 2.43, std/mean = 0.06
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
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
DIAG = V105_ROOT / "diag_v105_main_v2"

OUT_ROOT = V112_ROOT / "outputs" / "step_c"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(V108_ROOT))
sys.path.insert(0, str(V112_ROOT))
from v112_step_z_environment_check import (  # noqa: E402
    build_beta_intervals, is_beta_member_at, collect_cid_features,
    SEEDS, RUN_END, AGE_TARGET,
)
from v108_atom_event_generator import TARGET_ATOMS  # noqa: E402

Q3_THRESHOLD = 977          # Step Z 実測、v10.10 §3.2 整合
N_CORE_THRESHOLD = 5        # cond3
DEFAULT_AGE_TARGET = AGE_TARGET  # 200
DEFAULT_FAM_PERCENTILE = 50  # cond4 top 50% (median)、第 5 版主題

V108_TOP_K = 100  # v108_standard 副次比較対象 (v10.8 既存)


# ----------------------------------------------------------------------
# n_core_bin 分類 (v10.10 §3.4 反応 type 分業に整合)
# ----------------------------------------------------------------------
def classify_n_core_bin(n_core: int) -> str:
    if n_core == 2:
        return "bin_2"
    if 3 <= n_core <= 4:
        return "bin_3_4"
    if n_core >= 5:
        return "bin_5_plus"
    return "bin_lt_2"  # n_core < 2 (例外)


# ----------------------------------------------------------------------
# formation_relation 分類 (cid と β 形成の時系列関係、target_step 時点)
# ----------------------------------------------------------------------
def classify_formation_relation(cid: int, target_step: int,
                                 intervals: dict) -> str:
    """target_step 時点での cid の β との時系列関係を分類.

    - "before"           : target_step 時点で cid は β に未参加 (初参加が target_step より後)
    - "no_alpha"         : cid は α/β に一度も参加していない (intervals に存在しない)
    - "during"           : target_step 時点で cid は β member 中
    - "after"            : target_step 時点で cid は β を抜けた後 (active_to_recorded 後等)
    """
    if cid not in intervals or not intervals[cid]:
        return "no_alpha"
    ivs = intervals[cid]
    is_member_now = any(t_in <= target_step < t_out for t_in, t_out in ivs)
    if is_member_now:
        return "during"
    first_in = min(t_in for t_in, _ in ivs)
    if target_step < first_in:
        return "before"
    return "after"


# ----------------------------------------------------------------------
# v112 受容 cid 検出 (4 条件複合、cond4 top 50% per-seed)
# ----------------------------------------------------------------------
def detect_v112_receptive_cids(seed: int,
                                fam_threshold: float,
                                age_target: int = DEFAULT_AGE_TARGET) -> pd.DataFrame:
    """4 条件 (¬β + lifespan ≥ Q3 + n_core ≥ 5 + fam_max ≥ top 50%) を満たす cid 抽出.

    Returns:
        DataFrame columns: seed, source_cid, target_step, n_core, n_core_bin,
                           formation_relation, lifespan, fam_max,
                           cond1_not_beta, cond2_long, cond3_n_core, cond4_high_fam,
                           top_50_threshold
    """
    m = collect_cid_features(seed)
    intervals = build_beta_intervals(seed)
    rows = []
    for _, row in m.iterrows():
        cid = int(row["cognitive_id"])
        birth = int(row["birth_step"])
        t_target = birth + age_target
        death = int(row["death_step"])
        if t_target >= RUN_END:
            continue
        if t_target >= death:
            continue
        c1 = not is_beta_member_at(cid, t_target, intervals)
        c2 = row["lifespan"] >= Q3_THRESHOLD
        c3 = row["n_core"] >= N_CORE_THRESHOLD
        c4 = row["fam_max"] >= fam_threshold
        if not (c1 and c2 and c3 and c4):
            continue
        rows.append({
            "seed": seed,
            "source_cid": cid,
            "target_step": int(t_target),
            "birth_step": birth,
            "death_step": death,
            "n_core": int(row["n_core"]),
            "n_core_bin": classify_n_core_bin(int(row["n_core"])),
            "formation_relation": classify_formation_relation(cid, int(t_target), intervals),
            "lifespan": int(row["lifespan"]),
            "fam_max": float(row["fam_max"]),
            "cond1_not_beta": True,
            "cond2_long": True,
            "cond3_n_core": True,
            "cond4_high_fam": True,
            "top_50_threshold": float(fam_threshold),
            "condition_set": "v112",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# v108_standard 受容 cid 取得 (既存 cid_atom_sim_matrix top_k_100、副次比較)
# ----------------------------------------------------------------------
def detect_v108_standard_receptive_cids(seed: int,
                                          atoms: list[str] = TARGET_ATOMS,
                                          top_k: int = V108_TOP_K,
                                          age_target: int = DEFAULT_AGE_TARGET) -> pd.DataFrame:
    """v10.8 既存 top_k_100 cid pool (atom 別) を流用、副次比較対象.

    本検出器では cid pool だけを返す (events 生成は Step D で実施).
    metadata は v112 と同形式で揃える (n_core_bin / formation_relation 含む).
    """
    sim_path = V106_ROOT / "outputs" / "main" / f"cid_atom_sim_matrix_seed{seed}.parquet"
    if not sim_path.exists():
        return pd.DataFrame()
    df_sim = pd.read_parquet(sim_path)
    m = collect_cid_features(seed)
    m_lookup = m.set_index("cognitive_id")
    intervals = build_beta_intervals(seed)

    # atom 別 top_k_100 を unique 集合にまとめる (v10.8 と同じ pool 構成)
    cid_set = set()
    cid_to_atom_ranks = {}  # cid → list of (atom, rank, sim)
    for atom_idx, atom in enumerate(atoms):
        if atom not in df_sim.columns:
            continue
        sub = df_sim[["cid", atom]].dropna().sort_values(atom, ascending=False).head(top_k)
        for rank, (cid, sim) in enumerate(zip(sub["cid"].astype(int).tolist(),
                                                  sub[atom].tolist()), start=1):
            cid = int(cid)
            cid_set.add(cid)
            cid_to_atom_ranks.setdefault(cid, []).append((atom, rank, float(sim)))

    rows = []
    for cid in sorted(cid_set):
        if cid not in m_lookup.index:
            continue
        row = m_lookup.loc[cid]
        birth = int(row["birth_step"])
        t_target = birth + age_target
        death = int(row["death_step"])
        if t_target >= RUN_END:
            continue
        if t_target >= death:
            continue
        n_core = int(row["n_core"])
        rows.append({
            "seed": seed,
            "source_cid": cid,
            "target_step": int(t_target),
            "birth_step": birth,
            "death_step": death,
            "n_core": n_core,
            "n_core_bin": classify_n_core_bin(n_core),
            "formation_relation": classify_formation_relation(cid, int(t_target), intervals),
            "lifespan": int(row["lifespan"]),
            "fam_max": float(row["fam_max"]),
            "n_atoms_top_k": len(cid_to_atom_ranks[cid]),
            "condition_set": "v108_standard",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# top_50_threshold per-seed (cond4)
# ----------------------------------------------------------------------
def compute_top_50_threshold_per_seed(seeds: list[int]) -> dict:
    """各 seed の familiarity_max top 50% (= median) を算出."""
    out = {}
    for seed in seeds:
        m = collect_cid_features(seed)
        out[seed] = float(np.percentile(m["fam_max"], DEFAULT_FAM_PERCENTILE))
    return out


# ----------------------------------------------------------------------
# Per-seed full pipeline
# ----------------------------------------------------------------------
def detect_seed(seed: int, fam_threshold: float) -> dict:
    """seed 1 つを処理、v112 + v108_standard 両方検出."""
    df_v112 = detect_v112_receptive_cids(seed, fam_threshold)
    df_v108 = detect_v108_standard_receptive_cids(seed)

    out_v112 = OUT_ROOT / f"receptive_cids_v112_seed{seed}.parquet"
    out_v108 = OUT_ROOT / f"receptive_cids_v108_standard_seed{seed}.parquet"
    df_v112.to_parquet(out_v112, index=False)
    df_v108.to_parquet(out_v108, index=False)

    return {
        "seed": seed,
        "v112_n_cids": int(len(df_v112)),
        "v108_standard_n_cids": int(len(df_v108)),
        "v112_n_core_bin_dist": df_v112["n_core_bin"].value_counts().to_dict() if not df_v112.empty else {},
        "v112_formation_dist": df_v112["formation_relation"].value_counts().to_dict() if not df_v112.empty else {},
        "v108_n_core_bin_dist": df_v108["n_core_bin"].value_counts().to_dict() if not df_v108.empty else {},
        "v108_formation_dist": df_v108["formation_relation"].value_counts().to_dict() if not df_v108.empty else {},
        "v108_n_core_bin_5plus_count": int((df_v108["n_core_bin"] == "bin_5_plus").sum()) if not df_v108.empty else 0,
        "fam_threshold_used": float(fam_threshold),
    }


# ----------------------------------------------------------------------
# Step B 補完値との整合検証
# ----------------------------------------------------------------------
def verify_against_step_b_addendum(summaries_df: pd.DataFrame) -> dict:
    """Step B 補完 cond4_top50_population.parquet と一致するか検証."""
    addendum_path = V112_ROOT / "outputs" / "step_b" / "cond4_top50_population.parquet"
    if not addendum_path.exists():
        return {"verified": False, "reason": "Step B addendum not found"}
    add_df = pd.read_parquet(addendum_path)
    # n_4cond_top50 と v112_n_cids が一致するか
    merged = summaries_df.merge(add_df[["seed", "n_4cond_top50", "top_50_threshold"]],
                                on="seed", how="inner")
    delta_pop = (merged["v112_n_cids"] - merged["n_4cond_top50"]).abs()
    delta_thresh = (merged["fam_threshold_used"] - merged["top_50_threshold"]).abs()
    return {
        "verified": bool((delta_pop == 0).all() and (delta_thresh < 1e-6).all()),
        "n_seeds_compared": int(len(merged)),
        "max_delta_population": int(delta_pop.max()) if not merged.empty else 0,
        "max_delta_threshold": float(delta_thresh.max()) if not merged.empty else 0.0,
        "step_b_addendum_total": int(add_df["n_4cond_top50"].sum()),
        "step_c_total": int(summaries_df["v112_n_cids"].sum()),
        "match_per_seed": (delta_pop == 0).sum() == len(merged),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="main",
                    help="smoke = seed 0 のみ、main = 24 seeds")
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS

    t0 = time.time()
    print("=" * 72)
    print(f"v10.12 Step C: receptive_cid_detector_v112  mode={args.mode}")
    print(f"Q3_THRESHOLD={Q3_THRESHOLD}, N_CORE_THRESHOLD={N_CORE_THRESHOLD}, "
          f"FAM_PERCENTILE={DEFAULT_FAM_PERCENTILE}")
    print(f"AGE_TARGET={DEFAULT_AGE_TARGET} (target_step = birth + 200)")
    print("=" * 72)

    # 1. top_50_threshold per-seed
    print(f"\n=== 1. top_50_threshold per-seed ===")
    fam_thresholds = compute_top_50_threshold_per_seed(seeds)
    arr = np.array(list(fam_thresholds.values()))
    print(f"  per-seed mean={arr.mean():.3f}, std={arr.std():.3f}, "
          f"std/mean={arr.std()/arr.mean():.4f}")
    print(f"  per-seed min={arr.min():.3f}, max={arr.max():.3f}")

    # 2. per-seed 検出
    print(f"\n=== 2. per-seed receptive cid detection ===")
    summaries = []
    for seed in seeds:
        ts = time.time()
        s = detect_seed(seed, fam_thresholds[seed])
        elapsed = time.time() - ts
        summaries.append({**s, "elapsed_sec": round(elapsed, 2)})
        print(f"  seed={seed:2d}: v112={s['v112_n_cids']:3d}, "
              f"v108_std={s['v108_standard_n_cids']:4d} "
              f"(bin_5+={s['v108_n_core_bin_5plus_count']}), "
              f"elapsed={elapsed:.2f}s")

    df_sum = pd.DataFrame(summaries)

    # 3. v112 全体集計
    print(f"\n=== 3. v112 母集団集計 ===")
    print(f"  total events: {df_sum['v112_n_cids'].sum()}")
    print(f"  per seed mean: {df_sum['v112_n_cids'].mean():.2f}")
    print(f"  per seed std:  {df_sum['v112_n_cids'].std():.2f}")
    print(f"  per seed min/max: {df_sum['v112_n_cids'].min()}/{df_sum['v112_n_cids'].max()}")
    n_below_5 = (df_sum["v112_n_cids"] < 5).sum()
    n_below_10 = (df_sum["v112_n_cids"] < 10).sum()
    print(f"  < 5 events seeds: {n_below_5}/{len(df_sum)}")
    print(f"  < 10 events seeds: {n_below_10}/{len(df_sum)} (paired_d 信頼ライン)")

    # 4. v108_standard 集計
    print(f"\n=== 4. v108_standard 副次集計 ===")
    print(f"  total cids: {df_sum['v108_standard_n_cids'].sum()}")
    print(f"  per seed mean: {df_sum['v108_standard_n_cids'].mean():.1f}")
    print(f"  bin_5+ in v108_standard total: {df_sum['v108_n_core_bin_5plus_count'].sum()}")

    # 5. n_core_bin / formation_relation 分布 (v112)
    if args.mode == "main":
        print(f"\n=== 5. v112 cid 属性分布 (24 seeds 合計) ===")
        all_v112 = []
        for seed in seeds:
            p = OUT_ROOT / f"receptive_cids_v112_seed{seed}.parquet"
            all_v112.append(pd.read_parquet(p))
        all_v112_df = pd.concat(all_v112, ignore_index=True)
        print(f"  n_core_bin:")
        for b, c in all_v112_df["n_core_bin"].value_counts().items():
            print(f"    {b}: {c} ({c/len(all_v112_df)*100:.1f}%)")
        print(f"  formation_relation:")
        for f, c in all_v112_df["formation_relation"].value_counts().items():
            print(f"    {f}: {c} ({c/len(all_v112_df)*100:.1f}%)")

    # 6. Step B 補完値整合検証
    if args.mode == "main":
        print(f"\n=== 6. Step B 補完値との整合検証 ===")
        ver = verify_against_step_b_addendum(df_sum)
        for k, v in ver.items():
            print(f"  {k}: {v}")

    # 出力
    df_sum.to_parquet(OUT_ROOT / f"detector_run_summary_{args.mode}.parquet", index=False)
    with open(OUT_ROOT / f"detector_run_summary_{args.mode}.json", "w") as f:
        out = {
            "mode": args.mode,
            "seeds": seeds,
            "fam_thresholds_per_seed": {int(k): float(v) for k, v in fam_thresholds.items()},
            "v112_total_events": int(df_sum["v112_n_cids"].sum()),
            "v112_per_seed_mean": float(df_sum["v112_n_cids"].mean()),
            "v112_per_seed_min": int(df_sum["v112_n_cids"].min()),
            "v112_per_seed_max": int(df_sum["v112_n_cids"].max()),
            "v108_standard_total_cids": int(df_sum["v108_standard_n_cids"].sum()),
            "summaries": summaries,
        }
        if args.mode == "main":
            out["step_b_addendum_verification"] = verify_against_step_b_addendum(df_sum)
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    elapsed_total = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed_total:.2f}s, output = {OUT_ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
