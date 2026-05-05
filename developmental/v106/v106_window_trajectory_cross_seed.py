#!/usr/bin/env python3
"""v10.6 window trajectory cross-seed analysis.

24 seeds の (cid, window) trajectory データを統合、以下を集計:

1. ESDE 発展段階の cross-seed 検証 (window × dominant atom/category × seed 一致数)
2. trajectory_class 分布の cross-seed 集計 (135 cid × 24 seeds = 約 3000 cid)
3. window-level 動学的 atom 検出 (静的解析で消えていた atom が一時的に rank_1 になるか)
4. cid の軌跡シグネチャ (first → last atom の遷移パターン)
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = REPO_ROOT / "developmental" / "v106"
TRAJ_ROOT = V106_ROOT / "outputs" / "main" / "window_trajectory"
REPORT_ROOT = V106_ROOT / "reports"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import safe_write_csv  # noqa: E402

SEEDS = list(range(24))


def load_concat(prefix: str) -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        p = TRAJ_ROOT / f"{prefix}_seed{s}.csv"
        if p.exists():
            dfs.append(pd.read_csv(p))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def cross_seed_window_dominant(df_win: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w, sub in df_win.groupby("window"):
        cat_counts = Counter(sub["top_category"].dropna())
        atom_top1 = sub["rank_1_atom"].dropna()
        rank1_counts = Counter(atom_top1)
        most_cat, most_cat_n = cat_counts.most_common(1)[0] if cat_counts else (None, 0)
        most_atom, most_atom_n = rank1_counts.most_common(1)[0] if rank1_counts else (None, 0)
        seed_unanimity_cat = sum(1 for s in SEEDS if (sub[sub["seed"] == s]["top_category"] == most_cat).any())
        rows.append({
            "window": int(w),
            "step_at_window_end": int(sub["step_at_window_end"].iloc[0]) if len(sub) else None,
            "n_seeds_observed": int(sub["seed"].nunique()),
            "n_total_alive_cids": int(len(sub)),
            "dominant_category": most_cat,
            "dominant_category_count": most_cat_n,
            "dominant_category_seed_unanimity": seed_unanimity_cat,
            "dominant_atom": most_atom,
            "dominant_atom_count": most_atom_n,
            "max_sim_mean_overall": float(sub["max_sim_mean"].mean()) if "max_sim_mean" in sub.columns else np.nan,
        })
    return pd.DataFrame(rows).sort_values("window")


def cross_seed_window_top_categories(df_win: pd.DataFrame) -> pd.DataFrame:
    """各 window で全 seed の top_category 出現数を集計、wide format."""
    rows = []
    all_cats = sorted(df_win["top_category"].dropna().unique())
    for w, sub in df_win.groupby("window"):
        row = {"window": int(w),
               "step_at_window_end": int(sub["step_at_window_end"].iloc[0]) if len(sub) else None}
        cat_counts = Counter(sub["top_category"].dropna())
        for cat in all_cats:
            row[f"{cat}_count"] = int(cat_counts.get(cat, 0))
        row["total_alive"] = int(len(sub))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("window")


def cross_seed_trajectory_class(df_traj: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cls_counts = df_traj["trajectory_class"].value_counts().to_dict()
    total = len(df_traj)
    for cls, cnt in cls_counts.items():
        rows.append({
            "trajectory_class": cls, "n_cids_total_24seeds": cnt,
            "ratio_24seeds": cnt / total if total else 0,
            "n_cids_mean_per_seed": cnt / 24,
        })
    return pd.DataFrame(rows).sort_values("n_cids_total_24seeds", ascending=False)


def cross_seed_first_last_atom(df_traj: pd.DataFrame) -> pd.DataFrame:
    """軌跡の最初の atom と最後の atom の遷移パターン."""
    rows = []
    df_long = df_traj[df_traj["n_windows"] >= 2].copy()
    transitions = Counter(
        zip(df_long["first_category"].astype(str), df_long["last_category"].astype(str))
    )
    for (first, last), cnt in transitions.most_common():
        rows.append({"first_category": first, "last_category": last,
                     "count": cnt, "is_diagonal": first == last})
    return pd.DataFrame(rows)


def dynamic_atom_emergence(df_win: pd.DataFrame, df_traj: pd.DataFrame) -> pd.DataFrame:
    """trajectory で 1 時点でも rank_1 になった atom リストと、静的解析との比較."""
    atoms_in_traj = set(df_win["rank_1_atom"].dropna().unique())
    rows = []
    for atom in sorted(atoms_in_traj):
        sub = df_win[df_win["rank_1_atom"] == atom]
        n_total = len(sub)
        n_seeds = sub["seed"].nunique()
        n_unique_cids = sub["cognitive_id"].nunique()
        windows = sub["window"].unique()
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "n_rank1_appearances": n_total,
            "n_seeds_appeared": n_seeds,
            "n_unique_cids": n_unique_cids,
            "n_windows_appeared": int(len(windows)),
            "first_window": int(min(windows)),
            "last_window": int(max(windows)),
            "median_window": float(np.median(windows)),
            "max_sim_max": float(sub["max_sim"].max()),
            "max_sim_mean": float(sub["max_sim"].mean()),
        })
    return pd.DataFrame(rows).sort_values("n_rank1_appearances", ascending=False)


def trajectory_class_by_n_core(df_traj: pd.DataFrame, df_win: pd.DataFrame) -> pd.DataFrame:
    n_core_lookup = (
        df_win.dropna(subset=["n_core_member"])
        .drop_duplicates(["seed", "cognitive_id"])
        [["seed", "cognitive_id", "n_core_member"]]
    )
    df = df_traj.merge(n_core_lookup, on=["seed", "cognitive_id"], how="left")
    df["n_core_int"] = df["n_core_member"].fillna(-1).astype(int)
    rows = []
    for nc in sorted(df["n_core_int"].unique()):
        sub = df[df["n_core_int"] == nc]
        for cls, cnt in sub["trajectory_class"].value_counts().items():
            rows.append({
                "n_core_member": nc if nc > 0 else "unknown",
                "trajectory_class": cls,
                "n_cids": int(cnt),
                "ratio_within_n_core": cnt / len(sub) if len(sub) else 0,
            })
    return pd.DataFrame(rows)


def main() -> None:
    print("v10.6 window trajectory cross-seed analysis")
    df_win = load_concat("window_cid_alignment")
    df_traj = load_concat("trajectory_patterns")
    df_rank = load_concat("window_rank1_distribution")

    print(f"  total (cid, window) pairs: {len(df_win)}")
    print(f"  total cid trajectories: {len(df_traj)}")
    print(f"  total window snapshots: {len(df_rank)}")

    out = TRAJ_ROOT
    out.mkdir(parents=True, exist_ok=True)

    df_win_dom = cross_seed_window_dominant(df_win)
    safe_write_csv(df_win_dom, out / "cross_seed_window_dominant.csv")

    df_win_cats = cross_seed_window_top_categories(df_win)
    safe_write_csv(df_win_cats, out / "cross_seed_window_categories.csv")

    df_cls = cross_seed_trajectory_class(df_traj)
    safe_write_csv(df_cls, out / "cross_seed_trajectory_class_summary.csv")

    df_trans = cross_seed_first_last_atom(df_traj)
    safe_write_csv(df_trans, out / "cross_seed_first_last_transitions.csv")

    df_dyn = dynamic_atom_emergence(df_win, df_traj)
    safe_write_csv(df_dyn, out / "cross_seed_dynamic_atom_emergence.csv")

    df_nc = trajectory_class_by_n_core(df_traj, df_win)
    safe_write_csv(df_nc, out / "cross_seed_trajectory_class_by_ncore.csv")

    print()
    print("=== trajectory_class summary (24 seeds) ===")
    for _, r in df_cls.iterrows():
        print(f"  {r['trajectory_class']:18s}  n={r['n_cids_total_24seeds']:4d}  ratio={r['ratio_24seeds']:.1%}")

    print()
    print("=== ESDE window-level dominant trajectory (24 seeds 集計) ===")
    print(f"{'window':6s}{'step':6s}{'dom_cat':10s}{'cat_cnt':8s}{'unanim':8s}{'dom_atom':22s}{'atom_cnt':8s}")
    for _, r in df_win_dom.iterrows():
        print(f"{r['window']:6d}{r['step_at_window_end']:6d}  {str(r['dominant_category']):8s}  "
              f"{r['dominant_category_count']:6d}  {r['dominant_category_seed_unanimity']:6d}  "
              f"{str(r['dominant_atom']):20s}  {r['dominant_atom_count']:6d}")

    print()
    print("=== top 20 dynamic rank_1 atoms (24 seeds, by trajectory appearance count) ===")
    for _, r in df_dyn.head(20).iterrows():
        print(f"  {r['atom']:25s} cat={r['category']:4s}  count={r['n_rank1_appearances']:5d}  "
              f"seeds={r['n_seeds_appeared']:2d}/24  windows={r['n_windows_appeared']:2d}/50  "
              f"max={r['max_sim_max']:.3f}")

    print(f"\nDONE  output = {out}")


if __name__ == "__main__":
    main()
