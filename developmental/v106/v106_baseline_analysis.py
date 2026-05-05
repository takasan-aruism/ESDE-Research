#!/usr/bin/env python3
"""v10.6 random-baseline analysis (post-post-post-process).

Web Claude 依頼書 v106_baseline_analysis_brief.md に基づくベースライン比較。

軸内 L1 正規化 48 次元 cosine 類似度はランダムでも mean ~0.76 を達成する性質があるため、
v10.6 観察値 (mean_max_sim ≈ 0.608) を **ランダムベースラインと比較** して
真の finding (|z| > 2.0 かつ 24 seeds 一貫の偏り) を統計的に同定する。

実装する 2 種ベースライン:
  - uniform: 各軸ごとに [0,1] uniform 抽出 → 軸内 L1 正規化
  - shuffled: 実 cid ベクトルの各軸内要素をシャッフル (軸間対応関係を破壊)

入力: outputs/main/atom_profiles_cache.npz, atom_cid_topk_seed*.csv,
      cid_structure_profile_seed*.csv (shuffled 用)
出力: outputs/main/baseline/ 配下、24 + 5 + 1 = 30 ファイル
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = REPO_ROOT / "developmental" / "v106"
MAIN_ROOT = V106_ROOT / "outputs" / "main"
BASELINE_ROOT = MAIN_ROOT / "baseline"
REPORT_ROOT = V106_ROOT / "reports"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import (  # noqa: E402
    AXES_ORDER,
    SUBJ_DIR,
    assert_output_under_v106,
    safe_read_csv,
    safe_write_csv,
    safe_write_json,
)

SEEDS = list(range(24))
BASELINE_SEED = 106
N_BASELINE_RUNS_PER_SEED = 1
SIM_STRONG = 0.5
SIM_WEAK = 0.3


# ----------------------------------------------------------------------
# Random-cid generation
# ----------------------------------------------------------------------
def generate_uniform_cid_vector(rng: np.random.Generator) -> np.ndarray:
    parts: list[float] = []
    for _, levels in AXES_ORDER:
        n = len(levels)
        raw = rng.random(n)
        s = raw.sum()
        if s > 0:
            parts.extend((raw / s).tolist())
        else:
            parts.extend([1.0 / n] * n)
    arr = np.array(parts, dtype=np.float32)
    assert arr.shape == (48,)
    return arr


def shuffle_cid_vector_within_axes(real_vec: np.ndarray,
                                     rng: np.random.Generator) -> np.ndarray:
    out = real_vec.copy()
    cursor = 0
    for _, levels in AXES_ORDER:
        n = len(levels)
        section = out[cursor:cursor + n].copy()
        rng.shuffle(section)
        out[cursor:cursor + n] = section
        cursor += n
    return out


# ----------------------------------------------------------------------
# Per-seed baseline run
# ----------------------------------------------------------------------
def cosine_matrix(cids_mat: np.ndarray, atoms_mat: np.ndarray) -> np.ndarray:
    cn = np.linalg.norm(cids_mat, axis=1, keepdims=True)
    an = np.linalg.norm(atoms_mat, axis=1, keepdims=True)
    cn_safe = np.where(cn == 0, 1, cn)
    an_safe = np.where(an == 0, 1, an)
    cids_norm = cids_mat / cn_safe
    atoms_norm = atoms_mat / an_safe
    return cids_norm @ atoms_norm.T


def run_baseline_for_seed(seed: int, atom_names: list[str], atom_profiles: np.ndarray,
                           atom_valid: np.ndarray, rng: np.random.Generator,
                           method: str = "uniform") -> pd.DataFrame:
    n_cid = len(safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv"))

    if method == "uniform":
        cid_mat = np.vstack([generate_uniform_cid_vector(rng) for _ in range(n_cid)])
    elif method == "shuffled":
        df_prof = pd.read_csv(MAIN_ROOT / f"cid_structure_profile_seed{seed}.csv")
        dim_cols = [f"dim_{i}" for i in range(48)]
        real_vecs = df_prof[dim_cols].to_numpy(dtype=np.float32)
        cid_mat = np.vstack([shuffle_cid_vector_within_axes(v, rng) for v in real_vecs])
    else:
        raise ValueError(f"unknown method: {method}")

    valid_idx = np.where(atom_valid)[0]
    sim = np.full((cid_mat.shape[0], atom_profiles.shape[0]), np.nan, dtype=np.float32)
    if valid_idx.size:
        sim_valid = cosine_matrix(cid_mat, atom_profiles[valid_idx])
        sim[:, valid_idx] = sim_valid

    rows = []
    for j, atom in enumerate(atom_names):
        if not atom_valid[j]:
            continue
        col = sim[:, j]
        rows.append({
            "seed": seed, "method": method, "atom": atom,
            "category": atom.split(".")[0],
            "rank_1_sim": float(col.max()),
            "mean_sim": float(col.mean()),
            "median_sim": float(np.median(col)),
            "p99_sim": float(np.quantile(col, 0.99)),
            "n_cid": int(cid_mat.shape[0]),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Aggregate atom-level summary across 24 seeds
# ----------------------------------------------------------------------
def aggregate_atom_baseline(all_seeds_df: pd.DataFrame, method: str) -> pd.DataFrame:
    sub = all_seeds_df[all_seeds_df["method"] == method]
    rows = []
    for atom, g in sub.groupby("atom"):
        sims = g["rank_1_sim"].to_numpy()
        n_strong = int((sims >= SIM_STRONG).sum())
        n_partial = int(((sims >= SIM_WEAK) & (sims < SIM_STRONG)).sum())
        n_weak = int((sims < SIM_WEAK).sum())
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "method": method,
            "baseline_rank1_sim_mean": float(sims.mean()),
            "baseline_rank1_sim_std": float(sims.std(ddof=0)),
            "baseline_rank1_sim_min": float(sims.min()),
            "baseline_rank1_sim_max": float(sims.max()),
            "baseline_n_strong_seeds": n_strong,
            "baseline_n_partial_seeds": n_partial,
            "baseline_n_weak_seeds": n_weak,
            "baseline_strong_ratio_24": n_strong / 24.0,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Aggregate observed atom data from existing outputs
# ----------------------------------------------------------------------
def load_observed_atom_table() -> pd.DataFrame:
    sims_per_atom: dict[str, list[float]] = defaultdict(list)
    for s in SEEDS:
        df = pd.read_csv(MAIN_ROOT / f"atom_cid_topk_seed{s}.csv")
        for atom, sim in zip(df["atom"], df["rank_1_sim"]):
            sims_per_atom[atom].append(float(sim))
    rows = []
    for atom, sims_list in sims_per_atom.items():
        if len(sims_list) != 24:
            continue
        sims = np.array(sims_list)
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "observed_rank1_sim_mean": float(sims.mean()),
            "observed_rank1_sim_std": float(sims.std(ddof=0)),
            "observed_rank1_sim_min": float(sims.min()),
            "observed_rank1_sim_max": float(sims.max()),
            "observed_n_strong_seeds": int((sims >= SIM_STRONG).sum()),
            "observed_n_partial_seeds": int(((sims >= SIM_WEAK) & (sims < SIM_STRONG)).sum()),
            "observed_n_weak_seeds": int((sims < SIM_WEAK).sum()),
            "observed_strong_ratio_24": float((sims >= SIM_STRONG).mean()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Build observed_vs_baseline atom CSV (with z-score)
# ----------------------------------------------------------------------
def build_observed_vs_baseline_atom(observed: pd.DataFrame,
                                     baseline_uniform: pd.DataFrame,
                                     baseline_shuffled: pd.DataFrame) -> pd.DataFrame:
    df = observed.merge(
        baseline_uniform[[
            "atom", "baseline_rank1_sim_mean", "baseline_rank1_sim_std",
            "baseline_n_strong_seeds", "baseline_strong_ratio_24",
        ]].rename(columns={
            "baseline_rank1_sim_mean": "uniform_baseline_mean",
            "baseline_rank1_sim_std": "uniform_baseline_std",
            "baseline_n_strong_seeds": "uniform_baseline_n_strong",
            "baseline_strong_ratio_24": "uniform_baseline_strong_ratio",
        }), on="atom", how="left",
    ).merge(
        baseline_shuffled[[
            "atom", "baseline_rank1_sim_mean", "baseline_rank1_sim_std",
            "baseline_n_strong_seeds", "baseline_strong_ratio_24",
        ]].rename(columns={
            "baseline_rank1_sim_mean": "shuffled_baseline_mean",
            "baseline_rank1_sim_std": "shuffled_baseline_std",
            "baseline_n_strong_seeds": "shuffled_baseline_n_strong",
            "baseline_strong_ratio_24": "shuffled_baseline_strong_ratio",
        }), on="atom", how="left",
    )

    df["delta_uniform"] = df["observed_rank1_sim_mean"] - df["uniform_baseline_mean"]
    df["delta_shuffled"] = df["observed_rank1_sim_mean"] - df["shuffled_baseline_mean"]
    df["z_score_uniform"] = df["delta_uniform"] / df["uniform_baseline_std"].replace(0, np.nan)
    df["z_score_shuffled"] = df["delta_shuffled"] / df["shuffled_baseline_std"].replace(0, np.nan)

    df["direction_consistency_24"] = (
        ((df["observed_rank1_sim_mean"] > df["uniform_baseline_mean"]) &
         (df["observed_rank1_sim_min"] > df["uniform_baseline_mean"]))
        | ((df["observed_rank1_sim_mean"] < df["uniform_baseline_mean"]) &
           (df["observed_rank1_sim_max"] < df["uniform_baseline_mean"]))
    )
    df["true_finding_uniform"] = (df["z_score_uniform"].abs() > 2.0) & df["direction_consistency_24"]
    df["true_finding_shuffled"] = (df["z_score_shuffled"].abs() > 2.0) & df["direction_consistency_24"]
    df["true_finding_either"] = df["true_finding_uniform"] | df["true_finding_shuffled"]
    df["true_finding_both"] = df["true_finding_uniform"] & df["true_finding_shuffled"]
    return df.sort_values("z_score_uniform")


# ----------------------------------------------------------------------
# Category-level
# ----------------------------------------------------------------------
def build_category_summary(observed_vs_baseline: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, sub in observed_vs_baseline.groupby("category"):
        n_total = len(sub)
        obs_strong = int((sub["observed_n_strong_seeds"] == 24).sum())
        obs_strong_ratio = obs_strong / n_total
        unif_strong_expected = float(sub["uniform_baseline_strong_ratio"].mean()) * n_total
        unif_strong_atoms = float((sub["uniform_baseline_n_strong"] == 24).sum())
        shuf_strong_atoms = float((sub["shuffled_baseline_n_strong"] == 24).sum())
        obs_unmatched_atoms = int((sub["observed_n_weak_seeds"] == 24).sum())
        unif_unmatched_atoms = float((sub["uniform_baseline_n_strong"] == 0).sum())
        shuf_unmatched_atoms = float((sub["shuffled_baseline_n_strong"] == 0).sum())
        cat_z_uniform = (
            (sub["observed_rank1_sim_mean"].mean() - sub["uniform_baseline_mean"].mean())
            / sub["uniform_baseline_std"].mean()
        )
        cat_z_shuffled = (
            (sub["observed_rank1_sim_mean"].mean() - sub["shuffled_baseline_mean"].mean())
            / sub["shuffled_baseline_std"].mean()
        )
        rows.append({
            "category": cat, "n_atoms": n_total,
            "observed_strong_24/24_atoms": obs_strong,
            "observed_strong_ratio": obs_strong_ratio,
            "uniform_strong_24/24_atoms": int(unif_strong_atoms),
            "uniform_strong_atoms_expected_mean": unif_strong_expected,
            "shuffled_strong_24/24_atoms": int(shuf_strong_atoms),
            "delta_strong_atoms_uniform": obs_strong - unif_strong_atoms,
            "delta_strong_atoms_shuffled": obs_strong - shuf_strong_atoms,
            "observed_always_unmatched_atoms": obs_unmatched_atoms,
            "uniform_always_unmatched_atoms": int(unif_unmatched_atoms),
            "shuffled_always_unmatched_atoms": int(shuf_unmatched_atoms),
            "category_z_score_uniform": cat_z_uniform,
            "category_z_score_shuffled": cat_z_shuffled,
            "observed_sim_mean_avg": float(sub["observed_rank1_sim_mean"].mean()),
            "uniform_sim_mean_avg": float(sub["uniform_baseline_mean"].mean()),
            "shuffled_sim_mean_avg": float(sub["shuffled_baseline_mean"].mean()),
        })
    return pd.DataFrame(rows).sort_values("category_z_score_uniform")


# ----------------------------------------------------------------------
# True-finding atoms output
# ----------------------------------------------------------------------
def build_true_finding(observed_vs_baseline: pd.DataFrame) -> pd.DataFrame:
    df = observed_vs_baseline[
        observed_vs_baseline["true_finding_either"]
    ].copy()
    df["finding_direction"] = np.where(
        df["delta_uniform"] > 0, "above_baseline", "below_baseline"
    )
    df = df[[
        "atom", "category", "finding_direction",
        "observed_rank1_sim_mean", "observed_n_strong_seeds", "observed_n_weak_seeds",
        "uniform_baseline_mean", "uniform_baseline_std",
        "shuffled_baseline_mean", "shuffled_baseline_std",
        "delta_uniform", "delta_shuffled",
        "z_score_uniform", "z_score_shuffled",
        "direction_consistency_24",
        "true_finding_uniform", "true_finding_shuffled", "true_finding_both",
    ]]
    return df.sort_values(["finding_direction", "z_score_uniform"], ascending=[True, True])


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------
def write_report(observed_vs_baseline: pd.DataFrame, category_df: pd.DataFrame,
                  true_finding_df: pd.DataFrame, baseline_uniform: pd.DataFrame,
                  baseline_shuffled: pd.DataFrame) -> None:
    L: list[str] = []
    L.append("# v10.6 random-baseline analysis report")
    L.append("")
    L.append("*生成*: v106_baseline_analysis.py、Code A")
    L.append(f"*baseline 設定*: 一様分布 + 軸内 L1 正規化 (uniform) と 実 cid 軸内シャッフル (shuffled) の 2 種、numpy seed = {BASELINE_SEED}")
    L.append("")

    L.append("## 1. ランダムベースライン分布 (24 seeds 集計)")
    L.append("")
    for method, df in [("uniform", baseline_uniform), ("shuffled", baseline_shuffled)]:
        sims = df["baseline_rank1_sim_mean"]
        L.append(f"### {method}")
        L.append("")
        L.append(f"- 全 atom × 24 seeds の rank_1_sim mean: **{sims.mean():.4f}** (std {sims.std():.4f})")
        L.append(f"- 25%/50%/75% quantile: {sims.quantile(0.25):.4f} / {sims.quantile(0.5):.4f} / {sims.quantile(0.75):.4f}")
        L.append(f"- min={sims.min():.4f}, max={sims.max():.4f}")
        n_strong24 = int((df["baseline_n_strong_seeds"] == 24).sum())
        n_un24 = int((df["baseline_n_weak_seeds"] == 24).sum())
        L.append(f"- baseline で strong_24/24 達成 atom: **{n_strong24}** / {len(df)}")
        L.append(f"- baseline で 24/24 unmatched atom: **{n_un24}** / {len(df)}")
        L.append("")

    L.append("## 2. 観察値 vs ベースライン (atom-level)")
    L.append("")
    obs_mean = observed_vs_baseline["observed_rank1_sim_mean"].mean()
    unif_mean = observed_vs_baseline["uniform_baseline_mean"].mean()
    shuf_mean = observed_vs_baseline["shuffled_baseline_mean"].mean()
    L.append(f"- 全 325 atom 平均 observed rank_1_sim: **{obs_mean:.4f}**")
    L.append(f"- 全 325 atom 平均 uniform baseline rank_1_sim: **{unif_mean:.4f}**")
    L.append(f"- 全 325 atom 平均 shuffled baseline rank_1_sim: **{shuf_mean:.4f}**")
    L.append("")
    L.append(f"→ 観察値 - uniform = {obs_mean - unif_mean:+.4f}")
    L.append(f"→ 観察値 - shuffled = {obs_mean - shuf_mean:+.4f}")
    L.append("")

    n_obs_strong = int((observed_vs_baseline["observed_n_strong_seeds"] == 24).sum())
    n_unif_strong = int((observed_vs_baseline["uniform_baseline_n_strong"] == 24).sum())
    n_shuf_strong = int((observed_vs_baseline["shuffled_baseline_n_strong"] == 24).sum())
    n_obs_unmatched = int((observed_vs_baseline["observed_n_weak_seeds"] == 24).sum())
    n_unif_unmatched = int((observed_vs_baseline["uniform_baseline_n_strong"] == 0).sum())
    n_shuf_unmatched = int((observed_vs_baseline["shuffled_baseline_n_strong"] == 0).sum())
    L.append("### strong_24/24 atom 数の比較")
    L.append("")
    L.append(f"- observed: **{n_obs_strong}** atoms")
    L.append(f"- uniform baseline: **{n_unif_strong}** atoms")
    L.append(f"- shuffled baseline: **{n_shuf_strong}** atoms")
    L.append("")
    L.append("### 24/24 unmatched atom 数の比較 (max_sim < 0.3 を全 24 seeds で達成)")
    L.append("")
    L.append(f"- observed: **{n_obs_unmatched}** atoms")
    L.append(f"- uniform baseline strong-rate=0 atom 数: **{n_unif_unmatched}** atoms")
    L.append(f"- shuffled baseline strong-rate=0 atom 数: **{n_shuf_unmatched}** atoms")
    L.append("")

    L.append("## 3. category-level z-score")
    L.append("")
    L.append("| category | n_atoms | obs_strong | uniform_strong | shuf_strong | obs - unif (atoms) | z_uniform | z_shuffled |")
    L.append("|---|---|---|---|---|---|---|---|")
    for _, r in category_df.iterrows():
        L.append(
            f"| {r['category']} | {r['n_atoms']} | {r['observed_strong_24/24_atoms']} | "
            f"{r['uniform_strong_24/24_atoms']} | {r['shuffled_strong_24/24_atoms']} | "
            f"{int(r['delta_strong_atoms_uniform']):+d} | "
            f"{r['category_z_score_uniform']:+.2f} | {r['category_z_score_shuffled']:+.2f} |"
        )
    L.append("")

    L.append("## 4. 真の finding atom (|z| > 2.0 かつ direction 24-seed 一貫)")
    L.append("")
    above = true_finding_df[true_finding_df["finding_direction"] == "above_baseline"]
    below = true_finding_df[true_finding_df["finding_direction"] == "below_baseline"]
    L.append(f"- above_baseline (= ESDE が ランダムよりも特定 atom と接地): **{len(above)}** atoms")
    L.append(f"- below_baseline (= ESDE が ランダムよりも特定 atom と非接地、構造的盲点): **{len(below)}** atoms")
    L.append("")

    L.append("### above_baseline (上位 z-score、ESDE 構造の真の偏り)")
    L.append("")
    L.append("| atom | obs_mean | unif_baseline_mean | z_uniform | z_shuffled | both? |")
    L.append("|---|---|---|---|---|---|")
    for _, r in above.sort_values("z_score_uniform", ascending=False).head(40).iterrows():
        L.append(
            f"| {r['atom']} | {r['observed_rank1_sim_mean']:.3f} | "
            f"{r['uniform_baseline_mean']:.3f} | {r['z_score_uniform']:+.2f} | "
            f"{r['z_score_shuffled']:+.2f} | {'Y' if r['true_finding_both'] else 'N'} |"
        )
    L.append("")

    L.append("### below_baseline (下位 z-score、構造的盲点)")
    L.append("")
    L.append("| atom | obs_mean | unif_baseline_mean | z_uniform | z_shuffled | both? |")
    L.append("|---|---|---|---|---|---|")
    for _, r in below.sort_values("z_score_uniform", ascending=True).head(40).iterrows():
        L.append(
            f"| {r['atom']} | {r['observed_rank1_sim_mean']:.3f} | "
            f"{r['uniform_baseline_mean']:.3f} | {r['z_score_uniform']:+.2f} | "
            f"{r['z_score_shuffled']:+.2f} | {'Y' if r['true_finding_both'] else 'N'} |"
        )
    L.append("")

    L.append("## 5. v106_phase_report.md 修正提案")
    L.append("")
    L.append("- 「mean_max_sim 0.608」を主結果から外す。 baseline (uniform) の rank_1_sim mean が同等以上の値を取り得るため、絶対値としては finding ではない。")
    L.append("- 真の finding は **観察値 - baseline の方向と大きさ**:")
    if obs_mean < unif_mean:
        L.append(f"  - ESDE 観察値 ({obs_mean:.3f}) < uniform baseline ({unif_mean:.3f}) → ESDE 構造ベクトルは Atom と **ランダム期待値より低い類似度** を持つ。これ自体が観察。")
    else:
        L.append(f"  - ESDE 観察値 ({obs_mean:.3f}) > uniform baseline ({unif_mean:.3f}) → ESDE 構造ベクトルは Atom と **ランダム期待値より高い類似度** を持つ。")
    L.append(f"- カテゴリ別 z-score 上位は: {', '.join(category_df.tail(5)['category'].tolist())}")
    L.append(f"- カテゴリ別 z-score 下位は: {', '.join(category_df.head(5)['category'].tolist())}")
    L.append(f"- 真の finding atom (|z|>2 一貫): above {len(above)} 件、below {len(below)} 件")
    L.append("")
    L.append("## 6. 出力ファイル一覧")
    L.append("")
    L.append("```")
    L.append("outputs/main/baseline/")
    L.append("├── baseline_atom_alignment_seed{0..23}.csv (uniform + shuffled 統合)")
    L.append("├── baseline_atom_summary.csv               (atom × method × 24-seed 集計)")
    L.append("├── baseline_category_summary.csv           (category × method)")
    L.append("├── observed_vs_baseline_atom.csv           (atom レベル z-score 比較)")
    L.append("├── observed_vs_baseline_category.csv       (= category_summary)")
    L.append("├── true_finding_atoms.csv                  (|z|>2 かつ一貫した atom)")
    L.append("└── baseline_summary.json                   (実行メタ情報)")
    L.append("```")
    L.append("")

    out_path = REPORT_ROOT / "baseline_analysis_report.md"
    assert_output_under_v106(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L), encoding="utf-8")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print(f"v10.6 random-baseline analysis (24 seeds, single batch)")
    print(f"  MAIN_ROOT     = {MAIN_ROOT}")
    print(f"  BASELINE_ROOT = {BASELINE_ROOT}")
    print()

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)
    n_valid = int(atom_valid.sum())
    print(f"  atoms: total={len(atom_names)}, valid={n_valid}")

    BASELINE_ROOT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(BASELINE_SEED)

    all_seeds: list[pd.DataFrame] = []
    t0 = time.time()
    for seed in SEEDS:
        ts = time.time()
        df_uni = run_baseline_for_seed(seed, atom_names, atom_profiles, atom_valid,
                                         rng, method="uniform")
        df_shf = run_baseline_for_seed(seed, atom_names, atom_profiles, atom_valid,
                                         rng, method="shuffled")
        df_seed = pd.concat([df_uni, df_shf], ignore_index=True)
        safe_write_csv(df_seed, BASELINE_ROOT / f"baseline_atom_alignment_seed{seed}.csv")
        all_seeds.append(df_seed)
        print(f"  seed={seed}: n_cid={df_uni['n_cid'].iloc[0]}, "
              f"uniform_mean={df_uni['rank_1_sim'].mean():.4f}, "
              f"shuffled_mean={df_shf['rank_1_sim'].mean():.4f}, "
              f"elapsed={time.time()-ts:.2f}s")

    df_all = pd.concat(all_seeds, ignore_index=True)
    baseline_uniform = aggregate_atom_baseline(df_all, "uniform")
    baseline_shuffled = aggregate_atom_baseline(df_all, "shuffled")
    safe_write_csv(
        pd.concat([baseline_uniform, baseline_shuffled], ignore_index=True),
        BASELINE_ROOT / "baseline_atom_summary.csv",
    )

    observed = load_observed_atom_table()
    obs_vs_base = build_observed_vs_baseline_atom(observed, baseline_uniform, baseline_shuffled)
    safe_write_csv(obs_vs_base, BASELINE_ROOT / "observed_vs_baseline_atom.csv")

    cat_df = build_category_summary(obs_vs_base)
    safe_write_csv(cat_df, BASELINE_ROOT / "baseline_category_summary.csv")
    safe_write_csv(cat_df, BASELINE_ROOT / "observed_vs_baseline_category.csv")

    true_df = build_true_finding(obs_vs_base)
    safe_write_csv(true_df, BASELINE_ROOT / "true_finding_atoms.csv")

    safe_write_json(
        {
            "baseline_seed": BASELINE_SEED,
            "n_seeds": len(SEEDS),
            "sim_strong_threshold": SIM_STRONG,
            "sim_weak_threshold": SIM_WEAK,
            "z_score_threshold": 2.0,
            "n_atoms_total": len(atom_names),
            "n_atoms_valid": n_valid,
            "elapsed_total_sec": round(time.time() - t0, 2),
        },
        BASELINE_ROOT / "baseline_summary.json",
    )

    write_report(obs_vs_base, cat_df, true_df, baseline_uniform, baseline_shuffled)
    n_above = int((true_df["finding_direction"] == "above_baseline").sum())
    n_below = int((true_df["finding_direction"] == "below_baseline").sum())
    print(f"\n  observed mean: {observed['observed_rank1_sim_mean'].mean():.4f}")
    print(f"  uniform baseline mean: {baseline_uniform['baseline_rank1_sim_mean'].mean():.4f}")
    print(f"  shuffled baseline mean: {baseline_shuffled['baseline_rank1_sim_mean'].mean():.4f}")
    print(f"  true finding atoms: {len(true_df)} (above {n_above}, below {n_below})")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
