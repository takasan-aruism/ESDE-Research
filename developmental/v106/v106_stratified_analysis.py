#!/usr/bin/env python3
"""v10.6 stratified analysis (post-post-process).

集団平均の罠を回避するための層化解析。既存 main run 出力を再利用。

5 層化軸 (n_core / lifespan / familiarity / integration / final_state) +
2 cross-tab (B×D, A×B) + ハブ層化 + α/β 層化 +
attack-related atom seed 跨ぎ検証 + cross-seed 集計 = 12 種 CSV を生成。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
MAIN_ROOT = V106_ROOT / "outputs" / "main"
STRAT_ROOT = MAIN_ROOT / "stratified"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import (  # noqa: E402
    AUDIT_DIR,
    SUBJ_DIR,
    INT_DIR,
    AXES_ORDER,
    assert_input_under_v105,
    assert_output_under_v106,
    safe_read_csv,
    safe_write_csv,
    safe_write_json,
    load_seed_cid_table,
    list_atoms_from_a1_batch,
)

SEEDS = list(range(24))


# ----------------------------------------------------------------------
# Stratum class assignments
# ----------------------------------------------------------------------
def lifespan_class(x: float) -> str:
    if pd.isna(x):
        return "unknown"
    if x < 1000:
        return "short"
    if x < 10000:
        return "medium"
    return "long"


def familiarity_class(x: float) -> str:
    if pd.isna(x):
        return "unknown"
    if x < 30:
        return "weak"
    if x < 150:
        return "medium"
    return "strong"


def integration_class(x: float) -> str:
    if pd.isna(x):
        return "isolated"
    if x <= 1:
        return "isolated"
    if x <= 5:
        return "catalytic"
    if x <= 50:
        return "chained"
    return "hub"


def n_core_class(x) -> str:
    if pd.isna(x):
        return "unknown"
    return f"n={int(x)}"


def beta_size_class(n_member_cids: int) -> str:
    if n_member_cids <= 3:
        return "small"
    if n_member_cids <= 10:
        return "medium"
    if n_member_cids <= 19:
        return "large"
    return "hub"


# ----------------------------------------------------------------------
# Attack-related atom set (curated, with rationale)
# ----------------------------------------------------------------------
ATTACK_RELATED_ATOMS = [
    "ACT.destroy",
    "CHG.decay",
    "COM.conflict",
    "ECO.loss",
    "EMO.despair",
    "EMO.fear",
    "EMO.hate",
    "EXS.death",
    "LOG.unreason",
    "SOC.attack",
    "STA.danger",
    "STA.pain",
    "STA.war",
    "STA.wound",
    "VAL.evil",
]


# ----------------------------------------------------------------------
# Per-seed: load & augment
# ----------------------------------------------------------------------
def load_seed_for_strata(seed: int) -> pd.DataFrame:
    df_cid = load_seed_cid_table(seed)
    df_topk = pd.read_csv(MAIN_ROOT / f"cid_atom_topk_seed{seed}.csv")
    df_topk = df_topk.rename(columns={"cid": "cognitive_id"})
    df = df_cid.merge(df_topk, on=["seed", "cognitive_id"], how="left")
    df["n_core_class"] = df["n_core_member"].apply(n_core_class)
    df["lifespan_class"] = df["lifespan_steps"].apply(lifespan_class)
    df["familiarity_class"] = df["last_familiarity_max"].apply(familiarity_class)
    df["integration_class"] = df["n_alphas_currently"].apply(integration_class)
    df["final_state_class"] = df["final_state"].fillna("unknown")
    df["top_category"] = df["rank_1_atom"].astype(str).str.split(".").str[0]
    df["match_class"] = pd.cut(
        df["max_sim"], bins=[-np.inf, 0.3, 0.5, np.inf],
        labels=["unmatched", "partial", "matched"],
    )
    return df


# ----------------------------------------------------------------------
# 1. stratified_atom_distribution
# ----------------------------------------------------------------------
def stratified_atom_distribution(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rows = []
    axes = [
        ("n_core", "n_core_class"),
        ("lifespan", "lifespan_class"),
        ("familiarity", "familiarity_class"),
        ("integration", "integration_class"),
        ("final_state", "final_state_class"),
    ]
    for axis_name, col in axes:
        for klass, sub in df.groupby(col, dropna=False):
            n = len(sub)
            counts = sub["rank_1_atom"].value_counts()
            top5 = counts.head(5).items()
            sims = sub["max_sim"].dropna()
            row = {
                "seed": seed,
                "stratum_axis": axis_name,
                "stratum_class": klass,
                "n_cids": n,
                "max_sim_mean": float(sims.mean()) if len(sims) else np.nan,
                "max_sim_median": float(sims.median()) if len(sims) else np.nan,
                "max_sim_std": float(sims.std()) if len(sims) > 1 else np.nan,
                "max_sim_p25": float(sims.quantile(0.25)) if len(sims) else np.nan,
                "max_sim_p75": float(sims.quantile(0.75)) if len(sims) else np.nan,
                "max_sim_p95": float(sims.quantile(0.95)) if len(sims) else np.nan,
                "unmatched_ratio": float((sub["max_sim"] < 0.3).sum() / n) if n else 0,
                "partial_ratio": float(((sub["max_sim"] >= 0.3) & (sub["max_sim"] < 0.5)).sum() / n) if n else 0,
                "matched_ratio": float((sub["max_sim"] >= 0.5).sum() / n) if n else 0,
            }
            for i, (atom, cnt) in enumerate(top5, start=1):
                row[f"top_{i}_atom"] = atom
                row[f"top_{i}_count"] = int(cnt)
                row[f"top_{i}_ratio"] = float(cnt) / n if n else 0
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 2. stratified_category_distribution
# ----------------------------------------------------------------------
ALL_CATEGORIES_CACHE: list[str] | None = None


def get_all_categories() -> list[str]:
    global ALL_CATEGORIES_CACHE
    if ALL_CATEGORIES_CACHE is None:
        cats = sorted({a.split(".")[0] for a in list_atoms_from_a1_batch()})
        ALL_CATEGORIES_CACHE = cats
    return ALL_CATEGORIES_CACHE


def stratified_category_distribution(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rows = []
    cats = get_all_categories()
    axes = [
        ("n_core", "n_core_class"),
        ("lifespan", "lifespan_class"),
        ("familiarity", "familiarity_class"),
        ("integration", "integration_class"),
        ("final_state", "final_state_class"),
    ]
    for axis_name, col in axes:
        for klass, sub in df.groupby(col, dropna=False):
            n = len(sub)
            cat_counts = sub["top_category"].value_counts().to_dict()
            row = {"seed": seed, "stratum_axis": axis_name,
                   "stratum_class": klass, "n_cids": n}
            for cat in cats:
                c = int(cat_counts.get(cat, 0))
                row[f"{cat}_count"] = c
                row[f"{cat}_ratio"] = float(c) / n if n else 0
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 3. cross_tab_lifespan_integration (B × D)
# ----------------------------------------------------------------------
def cross_tab_lifespan_integration(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rows = []
    for ls in ["short", "medium", "long"]:
        for ic in ["isolated", "catalytic", "chained", "hub"]:
            sub = df[(df["lifespan_class"] == ls) & (df["integration_class"] == ic)]
            n = len(sub)
            counts = sub["rank_1_atom"].value_counts()
            dom = counts.head(1)
            rows.append({
                "seed": seed, "lifespan_class": ls, "integration_class": ic,
                "n_cids": n,
                "dominant_atom": dom.index[0] if len(dom) else None,
                "dominant_atom_count": int(dom.iloc[0]) if len(dom) else 0,
                "dominant_atom_ratio": float(dom.iloc[0] / n) if len(dom) and n else 0,
                "max_sim_mean": float(sub["max_sim"].mean()) if n else np.nan,
                "max_sim_median": float(sub["max_sim"].median()) if n else np.nan,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 4. cross_tab_ncore_lifespan (A × B)
# ----------------------------------------------------------------------
def cross_tab_ncore_lifespan(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rows = []
    for nc in sorted(df["n_core_class"].dropna().unique()):
        for ls in ["short", "medium", "long"]:
            sub = df[(df["n_core_class"] == nc) & (df["lifespan_class"] == ls)]
            n = len(sub)
            counts = sub["rank_1_atom"].value_counts()
            dom = counts.head(1)
            rows.append({
                "seed": seed, "n_core_class": nc, "lifespan_class": ls,
                "n_cids": n,
                "dominant_atom": dom.index[0] if len(dom) else None,
                "dominant_atom_count": int(dom.iloc[0]) if len(dom) else 0,
                "dominant_atom_ratio": float(dom.iloc[0] / n) if len(dom) and n else 0,
                "max_sim_mean": float(sub["max_sim"].mean()) if n else np.nan,
                "max_sim_median": float(sub["max_sim"].median()) if n else np.nan,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 5. stratified_unmatched_atoms (atom-side, per stratum)
# ----------------------------------------------------------------------
def stratified_unmatched_atoms(df: pd.DataFrame, seed: int,
                                atom_names: list[str]) -> pd.DataFrame:
    sim_path = MAIN_ROOT / f"cid_atom_sim_matrix_seed{seed}.parquet"
    df_mat = pd.read_parquet(sim_path)
    df_mat = df_mat.set_index("cid")
    if "seed" in df_mat.columns:
        df_mat = df_mat.drop(columns=["seed"])
    rows = []
    axes = [
        ("n_core", "n_core_class"),
        ("lifespan", "lifespan_class"),
        ("familiarity", "familiarity_class"),
        ("integration", "integration_class"),
        ("final_state", "final_state_class"),
    ]
    for axis_name, col in axes:
        for klass, sub in df.groupby(col, dropna=False):
            cids = sub["cognitive_id"].astype(int).tolist()
            cids_in_mat = [c for c in cids if c in df_mat.index]
            if not cids_in_mat:
                continue
            sub_mat = df_mat.loc[cids_in_mat]
            atom_max = sub_mat.max(axis=0)
            unmatched = atom_max[atom_max < 0.3]
            for atom, m in unmatched.items():
                rows.append({
                    "seed": seed, "stratum_axis": axis_name,
                    "stratum_class": klass, "atom": atom,
                    "max_sim_in_stratum": float(m),
                    "n_cids_in_stratum": len(cids_in_mat),
                })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 6. hub_cid_stratified
# ----------------------------------------------------------------------
def hub_cid_stratified(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    threshold = df["n_alphas_currently"].quantile(0.99)
    if not threshold or threshold <= 0:
        threshold = max(df["n_alphas_currently"].max() * 0.5, 1)
    df_hub = df[df["n_alphas_currently"] >= threshold].copy()
    if df_hub.empty:
        return pd.DataFrame([{"seed": seed, "n_hub_cids": 0, "threshold": threshold}])
    rows = []
    grouped = df_hub.groupby(["n_core_class", "lifespan_class", "final_state_class"],
                              dropna=False)
    for (nc, ls, fs), sub in grouped:
        n = len(sub)
        counts = sub["rank_1_atom"].value_counts()
        dom = counts.head(1)
        rows.append({
            "seed": seed,
            "threshold_n_alphas": float(threshold),
            "n_core_class": nc, "lifespan_class": ls, "final_state_class": fs,
            "n_hub_cids": n,
            "dominant_atom": dom.index[0] if len(dom) else None,
            "dominant_atom_count": int(dom.iloc[0]) if len(dom) else 0,
            "max_sim_mean": float(sub["max_sim"].mean()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 7. alpha_atom_aggregate_stratified (by 5 pattern + size 3)
# ----------------------------------------------------------------------
def alpha_atom_aggregate_stratified(df: pd.DataFrame, seed: int,
                                     atom_names: list[str]) -> pd.DataFrame:
    df_pat = pd.read_csv(MAIN_ROOT / f"five_pattern_classification_seed{seed}.csv")
    if df_pat.empty:
        return pd.DataFrame()
    sim_path = MAIN_ROOT / f"cid_atom_sim_matrix_seed{seed}.parquet"
    df_mat = pd.read_parquet(sim_path).set_index("cid")
    if "seed" in df_mat.columns:
        df_mat = df_mat.drop(columns=["seed"])
    rows = []
    for pat_class, pat_sub in df_pat.groupby("pattern_class"):
        n_alpha = len(pat_sub)
        member_sims = []
        for _, r in pat_sub.iterrows():
            for c in str(r["member_cids"]).split("|"):
                try:
                    cid = int(c)
                except ValueError:
                    continue
                if cid in df_mat.index:
                    member_sims.append(df_mat.loc[cid].values)
        if not member_sims:
            continue
        stack = np.vstack(member_sims)
        with np.errstate(all="ignore"):
            mean_row = np.nanmean(stack, axis=0)
        order = np.argsort(-np.where(np.isnan(mean_row), -np.inf, mean_row))
        cols = list(df_mat.columns)
        top5 = [cols[i] for i in order[:5]]
        rows.append({
            "seed": seed, "pattern_class": pat_class,
            "n_alphas": n_alpha,
            "n_member_cid_observations": int(stack.shape[0]),
            "dominant_atom": top5[0],
            "dominant_atom_sim": float(mean_row[order[0]]),
            "top5_atoms": ",".join(top5),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 8. beta_atom_aggregate_stratified (by β size class)
# ----------------------------------------------------------------------
def beta_atom_aggregate_stratified(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    path = MAIN_ROOT / f"beta_atom_aggregate_seed{seed}.csv"
    if not path.exists():
        return pd.DataFrame()
    df_b = pd.read_csv(path)
    if df_b.empty:
        return pd.DataFrame()
    df_b["size_class"] = df_b["n_member_cids"].apply(beta_size_class)
    rows = []
    for sc, sub in df_b.groupby("size_class"):
        atom_counts = sub["top_atom"].value_counts()
        dom = atom_counts.head(1)
        rows.append({
            "seed": seed, "beta_size_class": sc,
            "n_betas": len(sub),
            "n_betas_with_atom": int(sub["top_atom"].notna().sum()),
            "dominant_atom": dom.index[0] if len(dom) else None,
            "dominant_atom_count": int(dom.iloc[0]) if len(dom) else 0,
            "max_atom_sim_mean": float(sub["max_atom_sim"].mean())
                if sub["max_atom_sim"].notna().any() else np.nan,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Cross-seed aggregations
# ----------------------------------------------------------------------
def cross_seed_stratified_summary(all_atom_dist: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grp = all_atom_dist.groupby(["stratum_axis", "stratum_class"])
    for (axis, klass), sub in grp:
        n_seeds = len(sub)
        n_cid_total = int(sub["n_cids"].sum())
        n_cid_mean = float(sub["n_cids"].mean())
        all_top1_atoms = sub["top_1_atom"].dropna()
        consistency = (all_top1_atoms.value_counts().iloc[0] / len(all_top1_atoms)) if len(all_top1_atoms) else 0
        most_common_top1 = all_top1_atoms.value_counts().head(1)
        rows.append({
            "stratum_axis": axis, "stratum_class": klass,
            "n_seeds": n_seeds,
            "n_cid_total_24seeds": n_cid_total,
            "n_cid_mean_per_seed": n_cid_mean,
            "max_sim_mean_overall": float(sub["max_sim_mean"].mean()),
            "max_sim_mean_std_across_seeds": float(sub["max_sim_mean"].std()),
            "top1_atom_most_common": most_common_top1.index[0] if len(most_common_top1) else None,
            "top1_atom_consistency_24seeds": float(consistency),
            "unmatched_ratio_mean": float(sub["unmatched_ratio"].mean()),
            "partial_ratio_mean": float(sub["partial_ratio"].mean()),
            "matched_ratio_mean": float(sub["matched_ratio"].mean()),
        })
    return pd.DataFrame(rows)


def unmatched_atoms_consistency() -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        p = MAIN_ROOT / f"unmatched_structures_seed{s}.csv"
        if p.exists():
            df = pd.read_csv(p)
            dfs.append(df[df["entity_type"] == "atom"])
    if not dfs:
        return pd.DataFrame()
    df_all = pd.concat(dfs, ignore_index=True)
    rows = []
    for atom, sub in df_all.groupby("entity_id"):
        seeds_unmatched = sub["seed"].unique()
        n_un = int(len(seeds_unmatched))
        rows.append({
            "atom": atom,
            "category": str(atom).split(".")[0],
            "total_unmatched_seeds": n_un,
            "consistency_24_24": n_un == 24,
            "max_sim_overall": float(sub["max_sim"].max()),
            "max_sim_min": float(sub["max_sim"].min()),
        })
    return pd.DataFrame(rows).sort_values(
        ["total_unmatched_seeds", "atom"], ascending=[False, True]
    )


def five_pattern_counts_per_seed() -> pd.DataFrame:
    rows = []
    for s in SEEDS:
        p = MAIN_ROOT / f"five_pattern_classification_seed{s}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        counts = df["pattern_class"].value_counts().to_dict()
        rows.append({
            "seed": s,
            "core_count": int(counts.get("core", 0)),
            "near_core_count": int(counts.get("near_core", 0)),
            "capture_count": int(counts.get("capture", 0)),
            "bridge_count": int(counts.get("bridge", 0)),
            "peripheral_count": int(counts.get("peripheral", 0)),
            "other_count": int(counts.get("other", 0)),
            "total_size3_alphas": int(len(df)),
        })
    return pd.DataFrame(rows)


def attack_related_atoms_analysis() -> pd.DataFrame:
    rows = []
    for atom in ATTACK_RELATED_ATOMS:
        seeds_unmatched = []
        max_sim_per_seed = []
        nearest_cid_categories = []
        for s in SEEDS:
            sim_path = MAIN_ROOT / f"cid_atom_sim_matrix_seed{s}.parquet"
            if not sim_path.exists():
                continue
            df_mat = pd.read_parquet(sim_path).set_index("cid")
            if "seed" in df_mat.columns:
                df_mat = df_mat.drop(columns=["seed"])
            if atom not in df_mat.columns:
                continue
            col = df_mat[atom]
            mx = col.max()
            max_sim_per_seed.append(float(mx))
            if mx < 0.3:
                seeds_unmatched.append(s)
            nearest_cid = int(col.idxmax())
            df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{s}.csv")
            df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{s}.csv")
            ncm = df_audit[df_audit["cid"] == nearest_cid]["n_core_member"]
            ncm_v = int(ncm.iloc[0]) if len(ncm) else None
            sub = df_subj[df_subj["cognitive_id"] == nearest_cid]
            fs = sub["final_state"].iloc[0] if len(sub) else None
            nearest_cid_categories.append(f"n={ncm_v}|{fs}")
        rows.append({
            "atom": atom,
            "category": atom.split(".")[0],
            "seeds_unmatched": len(seeds_unmatched),
            "consistency_24_24": len(seeds_unmatched) == 24,
            "max_sim_overall": max(max_sim_per_seed) if max_sim_per_seed else np.nan,
            "max_sim_mean": float(np.mean(max_sim_per_seed)) if max_sim_per_seed else np.nan,
            "max_sim_min": min(max_sim_per_seed) if max_sim_per_seed else np.nan,
            "nearest_cid_top_category_examples": ",".join(nearest_cid_categories[:5]),
        })
    return pd.DataFrame(rows).sort_values("seeds_unmatched", ascending=False)


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def run() -> None:
    print(f"v10.6 stratified analysis - 24 seeds (single batch, post-post-process)")
    print(f"  MAIN_ROOT  = {MAIN_ROOT}")
    print(f"  STRAT_ROOT = {STRAT_ROOT}")
    print()

    if not MAIN_ROOT.exists():
        raise RuntimeError(f"main run output missing: {MAIN_ROOT}")

    atom_names = list_atoms_from_a1_batch()
    STRAT_ROOT.mkdir(parents=True, exist_ok=True)

    all_atom_dist: list[pd.DataFrame] = []

    import time
    t0 = time.time()
    for seed in SEEDS:
        ts = time.time()
        df = load_seed_for_strata(seed)

        df_a = stratified_atom_distribution(df, seed)
        safe_write_csv(df_a, STRAT_ROOT / f"stratified_atom_distribution_seed{seed}.csv")
        all_atom_dist.append(df_a)

        df_c = stratified_category_distribution(df, seed)
        safe_write_csv(df_c, STRAT_ROOT / f"stratified_category_distribution_seed{seed}.csv")

        df_xt1 = cross_tab_lifespan_integration(df, seed)
        safe_write_csv(df_xt1, STRAT_ROOT / f"cross_tab_lifespan_integration_seed{seed}.csv")

        df_xt2 = cross_tab_ncore_lifespan(df, seed)
        safe_write_csv(df_xt2, STRAT_ROOT / f"cross_tab_ncore_lifespan_seed{seed}.csv")

        df_un = stratified_unmatched_atoms(df, seed, atom_names)
        safe_write_csv(df_un, STRAT_ROOT / f"stratified_unmatched_atoms_seed{seed}.csv")

        df_hub = hub_cid_stratified(df, seed)
        safe_write_csv(df_hub, STRAT_ROOT / f"hub_cid_stratified_seed{seed}.csv")

        df_alpha = alpha_atom_aggregate_stratified(df, seed, atom_names)
        safe_write_csv(df_alpha, STRAT_ROOT / f"alpha_atom_aggregate_stratified_seed{seed}.csv")

        df_beta = beta_atom_aggregate_stratified(df, seed)
        safe_write_csv(df_beta, STRAT_ROOT / f"beta_atom_aggregate_stratified_seed{seed}.csv")

        elapsed = time.time() - ts
        print(f"  seed={seed}: n_cid={len(df)}, "
              f"strata_rows={len(df_a)}, unmatched_rows={len(df_un)}, "
              f"elapsed={elapsed:.2f}s")

    df_all_atom_dist = pd.concat(all_atom_dist, ignore_index=True)
    df_summary = cross_seed_stratified_summary(df_all_atom_dist)
    safe_write_csv(df_summary, STRAT_ROOT / "stratified_summary_cross_seed.csv")
    print(f"  cross_seed summary: {len(df_summary)} rows")

    df_un_cons = unmatched_atoms_consistency()
    safe_write_csv(df_un_cons, STRAT_ROOT / "unmatched_atoms_consistency.csv")
    print(f"  unmatched consistency: {len(df_un_cons)} atoms")

    df_5p_count = five_pattern_counts_per_seed()
    safe_write_csv(df_5p_count, STRAT_ROOT / "five_pattern_counts_per_seed.csv")
    print(f"  five_pattern counts: {len(df_5p_count)} seeds")

    df_attack = attack_related_atoms_analysis()
    safe_write_csv(df_attack, STRAT_ROOT / "attack_related_atoms_analysis.csv")
    print(f"  attack-related: {len(df_attack)} atoms (curated set)")

    safe_write_json(
        {
            "attack_related_atoms": ATTACK_RELATED_ATOMS,
            "rationale": (
                "Curated based on (a) name keywords (destroy/conflict/decay/danger/"
                "war/despair/fear/hate/loss/evil/attack/death/pain/wound/unreason), "
                "(b) overlap with 24/24-unmatched atoms from prior main run, "
                "(c) categories COM/CHG/EMO/ECO/STA/VAL/ACT/SOC/EXS/LOG with "
                "explicit destructive/negative semantics. Excluded: PRP.single, "
                "WLD.unskilled, ELM.darkness (ambiguous), ACT.fall, ACT.sink "
                "(neutral motion verbs)."
            ),
        },
        STRAT_ROOT / "attack_related_atoms_definition.json",
    )

    total = time.time() - t0
    print(f"\nDONE  total elapsed = {total:.2f}s, output = {STRAT_ROOT}")


if __name__ == "__main__":
    run()
