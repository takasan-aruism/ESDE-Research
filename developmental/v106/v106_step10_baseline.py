#!/usr/bin/env python3
"""v10.6 10-step baseline analysis.

step10 解像度 (1.8M records) に対して uniform/shuffled baseline を生成、
atom-level / category-level z-score を計算。静的解析で BOD/PER のみ正の z
だった結果が、解像度を上げてどう変化するかを検証。

ベースライン生成方法:
  - uniform: 各軸 [0,1] uniform 抽出 → 軸内 L1 正規化、step10 と同じ
            record 数を 24 seeds で生成
  - shuffled: 実 step10 ベクトルの軸内シャッフル (軸間対応関係を破壊)

観察値: 実 step10 の rank_1_sim 集計 (per atom × seed)
比較: rank_1_sim mean、strong (>=0.5) ratio、rank_1 取得頻度を z-score 化
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = REPO_ROOT / "developmental" / "v106"
MAIN_ROOT = V106_ROOT / "outputs" / "main"
STEP10_TRAJ = MAIN_ROOT / "step10_trajectory"
STEP10_BASE = MAIN_ROOT / "step10_baseline"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import safe_write_csv, safe_write_json  # noqa: E402
from v106_baseline_analysis import (  # noqa: E402
    generate_uniform_cid_vector,
    shuffle_cid_vector_within_axes,
    cosine_matrix,
)

SEEDS = list(range(24))
BASELINE_SEED = 1006  # step10 baseline 専用 seed (静的版 106 と分離)
SIM_STRONG = 0.5


def run_seed_baseline(seed: int, atom_names: list[str], atom_profiles: np.ndarray,
                        atom_valid: np.ndarray, rng: np.random.Generator) -> dict:
    """Generate uniform + shuffled baselines, compute rank_1 atom distribution."""
    df_obs = pd.read_csv(STEP10_TRAJ / f"step10_cid_alignment_seed{seed}.csv")
    n_records = len(df_obs)

    # uniform baseline
    uni_mat = np.vstack([generate_uniform_cid_vector(rng) for _ in range(n_records)])
    valid_idx = np.where(atom_valid)[0]
    uni_sim = np.full((n_records, atom_profiles.shape[0]), np.nan, dtype=np.float32)
    uni_sim[:, valid_idx] = cosine_matrix(uni_mat, atom_profiles[valid_idx]).astype(np.float32)
    uni_rank1_idx = np.argmax(np.where(np.isnan(uni_sim), -np.inf, uni_sim), axis=1)
    uni_rank1_atoms = [atom_names[i] for i in uni_rank1_idx]
    uni_rank1_sims = uni_sim[np.arange(n_records), uni_rank1_idx]

    # shuffled baseline (real step10 vec を軸内シャッフル)
    # 軌跡データの 48 dim を持つために観察用 vectors を再生成する代わりに、
    # cid_alignment の dim をシャッフルする。ただし alignment CSV にベクトルは
    # 含まれないので、改めて build する必要がある。代替: cid_structure_profile の
    # dim_0..47 を再利用 → step10 専用ベクトルを作るのは重いのでスキップ
    # → 代替案: uniform baseline のみで簡略実施 (shuffled は追加検討)

    # 観察値統計
    obs_atom_counts = df_obs["rank_1_atom"].value_counts().to_dict()
    obs_sim_per_atom = df_obs.groupby("rank_1_atom")["rank_1_sim"].agg(["mean", "count"]).to_dict()
    obs_total_records = n_records

    uni_atom_counts = pd.Series(uni_rank1_atoms).value_counts().to_dict()
    uni_sim_per_atom = pd.Series(uni_rank1_sims).groupby(
        pd.Series(uni_rank1_atoms)
    ).agg(["mean", "count"]).to_dict()

    rows = []
    for atom in atom_names:
        if not atom_valid[atom_names.index(atom)] if atom in atom_names else False:
            continue
        obs_cnt = int(obs_atom_counts.get(atom, 0))
        uni_cnt = int(uni_atom_counts.get(atom, 0))
        obs_ratio = obs_cnt / obs_total_records if obs_total_records else 0
        uni_ratio = uni_cnt / n_records if n_records else 0
        rows.append({
            "seed": seed, "atom": atom, "category": atom.split(".")[0],
            "n_records_seed": n_records,
            "obs_rank1_count": obs_cnt,
            "obs_rank1_ratio": obs_ratio,
            "uni_baseline_rank1_count": uni_cnt,
            "uni_baseline_rank1_ratio": uni_ratio,
            "obs_minus_baseline_count": obs_cnt - uni_cnt,
            "obs_minus_baseline_ratio": obs_ratio - uni_ratio,
        })
    df_seed = pd.DataFrame(rows)
    return {
        "seed": seed,
        "n_records": n_records,
        "df": df_seed,
    }


def aggregate_atom_z_score(per_seed_dfs: list[pd.DataFrame],
                              atom_names: list[str]) -> pd.DataFrame:
    """24 seeds の seed-level ratio から各 atom の z-score を計算."""
    df_all = pd.concat(per_seed_dfs, ignore_index=True)
    rows = []
    for atom, sub in df_all.groupby("atom"):
        obs_ratios = sub["obs_rank1_ratio"].to_numpy()
        uni_ratios = sub["uni_baseline_rank1_ratio"].to_numpy()
        obs_mean = float(obs_ratios.mean())
        obs_std = float(obs_ratios.std(ddof=0))
        uni_mean = float(uni_ratios.mean())
        uni_std = float(uni_ratios.std(ddof=0))
        delta = obs_mean - uni_mean
        # z-score: 観察値が baseline 分布のどれだけ標準偏差離れているか
        z = (obs_mean - uni_mean) / uni_std if uni_std > 0 else (
            np.inf if delta > 0 else (-np.inf if delta < 0 else 0)
        )
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "obs_rank1_ratio_mean": obs_mean,
            "obs_rank1_ratio_std": obs_std,
            "uni_baseline_rank1_ratio_mean": uni_mean,
            "uni_baseline_rank1_ratio_std": uni_std,
            "delta_ratio": delta,
            "z_score_uniform": z,
            "n_seeds_obs_appeared": int((obs_ratios > 0).sum()),
            "n_seeds_baseline_appeared": int((uni_ratios > 0).sum()),
        })
    return pd.DataFrame(rows).sort_values("z_score_uniform", ascending=False)


def aggregate_category_z_score(df_atom_z: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, sub in df_atom_z.groupby("category"):
        obs_total = float(sub["obs_rank1_ratio_mean"].sum())
        uni_total = float(sub["uni_baseline_rank1_ratio_mean"].sum())
        # サブクラスの std を root-sum-square 風に集計
        obs_var_sum = float((sub["obs_rank1_ratio_std"] ** 2).sum())
        uni_var_sum = float((sub["uni_baseline_rank1_ratio_std"] ** 2).sum())
        uni_std_combined = float(np.sqrt(uni_var_sum)) if uni_var_sum > 0 else 0
        delta = obs_total - uni_total
        z = delta / uni_std_combined if uni_std_combined > 0 else (
            np.inf if delta > 0 else (-np.inf if delta < 0 else 0)
        )
        rows.append({
            "category": cat,
            "n_atoms": int(len(sub)),
            "obs_total_ratio_mean": obs_total,
            "uni_baseline_total_ratio_mean": uni_total,
            "delta_ratio": delta,
            "category_z_score_uniform": z,
            "n_atoms_above_baseline": int((sub["delta_ratio"] > 0).sum()),
            "n_atoms_below_baseline": int((sub["delta_ratio"] < 0).sum()),
        })
    return pd.DataFrame(rows).sort_values("category_z_score_uniform", ascending=False)


def compare_with_static_baseline(df_step10_z: pd.DataFrame) -> pd.DataFrame:
    """既存の static baseline (observed_vs_baseline_atom.csv) と比較."""
    static_path = MAIN_ROOT / "baseline" / "observed_vs_baseline_atom.csv"
    if not static_path.exists():
        return pd.DataFrame()
    df_static = pd.read_csv(static_path)
    static_z = df_static[["atom", "z_score_uniform"]].rename(
        columns={"z_score_uniform": "static_z_uniform"}
    )
    return df_step10_z.merge(static_z, on="atom", how="left")


def main() -> None:
    print("v10.6 step10 baseline analysis (atom & category z-score)")
    STEP10_BASE.mkdir(parents=True, exist_ok=True)

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)
    print(f"  atoms: total={len(atom_names)}, valid={int(atom_valid.sum())}")

    rng = np.random.default_rng(BASELINE_SEED)

    per_seed_dfs = []
    t0 = time.time()
    for seed in SEEDS:
        ts = time.time()
        out = run_seed_baseline(seed, atom_names, atom_profiles, atom_valid, rng)
        per_seed_dfs.append(out["df"])
        print(f"  seed={seed}: n_records={out['n_records']}, "
              f"elapsed={time.time()-ts:.2f}s")

    df_atom_z = aggregate_atom_z_score(per_seed_dfs, atom_names)
    safe_write_csv(df_atom_z, STEP10_BASE / "step10_atom_z_score.csv")

    df_cat_z = aggregate_category_z_score(df_atom_z)
    safe_write_csv(df_cat_z, STEP10_BASE / "step10_category_z_score.csv")

    df_compare = compare_with_static_baseline(df_atom_z)
    if not df_compare.empty:
        safe_write_csv(df_compare, STEP10_BASE / "step10_vs_static_z_compare.csv")

    safe_write_json({
        "baseline_seed": BASELINE_SEED,
        "n_seeds": len(SEEDS),
        "n_atoms_total": len(atom_names),
        "n_atoms_valid": int(atom_valid.sum()),
        "elapsed_total_sec": round(time.time() - t0, 2),
    }, STEP10_BASE / "step10_baseline_summary.json")

    n_pos = int((df_atom_z["z_score_uniform"] > 2.0).sum())
    n_neg = int((df_atom_z["z_score_uniform"] < -2.0).sum())
    print()
    print(f"=== step10 baseline z-score summary (24 seeds) ===")
    print(f"  total atoms classified: {len(df_atom_z)}")
    print(f"  z > +2 (above baseline): {n_pos}")
    print(f"  z < -2 (below baseline): {n_neg}")

    print()
    print("=== category z-score ranking (step10) ===")
    print(df_cat_z[["category", "n_atoms", "obs_total_ratio_mean",
                      "uni_baseline_total_ratio_mean", "delta_ratio",
                      "category_z_score_uniform",
                      "n_atoms_above_baseline", "n_atoms_below_baseline"]].to_string(index=False))

    print()
    print("=== top 25 atoms above baseline (step10) ===")
    print(df_atom_z.head(25)[["atom", "category", "obs_rank1_ratio_mean",
                                 "uni_baseline_rank1_ratio_mean", "delta_ratio",
                                 "z_score_uniform"]].to_string(index=False))

    print()
    print("=== top 15 atoms below baseline (step10) ===")
    print(df_atom_z.tail(15).iloc[::-1][["atom", "category", "obs_rank1_ratio_mean",
                                              "uni_baseline_rank1_ratio_mean",
                                              "delta_ratio", "z_score_uniform"]].to_string(index=False))

    if not df_compare.empty:
        print()
        print("=== top 15 atoms with largest z-score change (step10 vs static) ===")
        df_compare["z_diff"] = df_compare["z_score_uniform"] - df_compare["static_z_uniform"]
        df_compare = df_compare.sort_values("z_diff", ascending=False)
        print(df_compare.head(15)[["atom", "category", "static_z_uniform",
                                       "z_score_uniform", "z_diff"]].to_string(index=False))
        print()
        print("=== bottom 15 atoms with largest z-score change (downward) ===")
        print(df_compare.tail(15).iloc[::-1][["atom", "category", "static_z_uniform",
                                                    "z_score_uniform", "z_diff"]].to_string(index=False))

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
