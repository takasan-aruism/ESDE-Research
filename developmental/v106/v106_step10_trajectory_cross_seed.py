#!/usr/bin/env python3
"""v10.6 10-step trajectory cross-seed analysis."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = REPO_ROOT / "developmental" / "v106"
STEP10_TRAJ = V106_ROOT / "outputs" / "main" / "step10_trajectory"
PULSE_TRAJ = V106_ROOT / "outputs" / "main" / "pulse_trajectory"
WINDOW_TRAJ = V106_ROOT / "outputs" / "main" / "window_trajectory"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import safe_write_csv  # noqa: E402

SEEDS = list(range(24))
STEP_BIN_SIZE = 1000


def load_concat(prefix: str, root: Path) -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        p = root / f"{prefix}_seed{s}.csv"
        if p.exists():
            dfs.append(pd.read_csv(p))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def cross_seed_atom_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["rank_1_atom"].value_counts()
    rows = []
    for atom, cnt in counts.items():
        sub = df[df["rank_1_atom"] == atom]
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "n_records": int(cnt),
            "ratio_overall": cnt / len(df),
            "n_seeds_appeared": int(sub["seed"].nunique()),
            "n_unique_cids": int(sub["cognitive_id"].nunique()),
            "rank_1_sim_mean": float(sub["rank_1_sim"].mean()),
            "rank_1_sim_max": float(sub["rank_1_sim"].max()),
        })
    return pd.DataFrame(rows).sort_values("n_records", ascending=False)


def cross_seed_step_evolution(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["step_bin"] = (df["t"] // STEP_BIN_SIZE).astype(int)
    rows = []
    for sb, sub in df.groupby("step_bin"):
        cat_counts = Counter(sub["top_category"])
        atom_counts = Counter(sub["rank_1_atom"])
        most_cat, most_cat_n = cat_counts.most_common(1)[0]
        most_atom, most_atom_n = atom_counts.most_common(1)[0]
        seed_unanimity = sum(
            1 for s in SEEDS
            if (sub[sub["seed"] == s]["top_category"] == most_cat).any()
        )
        rows.append({
            "step_bin": int(sb),
            "step_low": int(sb * STEP_BIN_SIZE),
            "step_high": int((sb + 1) * STEP_BIN_SIZE),
            "n_records": int(len(sub)),
            "dominant_category": most_cat,
            "dominant_category_count": most_cat_n,
            "dominant_category_seed_unanimity": seed_unanimity,
            "dominant_atom": most_atom,
            "dominant_atom_count": most_atom_n,
            "rank_1_sim_mean": float(sub["rank_1_sim"].mean()),
        })
    return pd.DataFrame(rows).sort_values("step_bin")


def cross_seed_trajectory_class(df_traj: pd.DataFrame) -> pd.DataFrame:
    counts = df_traj["trajectory_class"].value_counts()
    total = len(df_traj)
    return pd.DataFrame([{
        "trajectory_class": c, "n_cids_total_24seeds": int(n),
        "ratio": n / total if total else 0,
        "n_cids_mean_per_seed": n / 24,
    } for c, n in counts.items()]).sort_values("n_cids_total_24seeds", ascending=False)


def cross_seed_resolution_compare(df_step10: pd.DataFrame, df_pulse: pd.DataFrame,
                                     df_window: pd.DataFrame) -> pd.DataFrame:
    s_counts = df_step10["rank_1_atom"].value_counts()
    p_counts = df_pulse["rank_1_atom"].value_counts() if not df_pulse.empty else pd.Series()
    w_counts = df_window["rank_1_atom"].value_counts() if not df_window.empty else pd.Series()
    all_atoms = sorted(set(s_counts.index) | set(p_counts.index) | set(w_counts.index))
    s_total = len(df_step10)
    p_total = len(df_pulse) if not df_pulse.empty else 1
    w_total = len(df_window) if not df_window.empty else 1
    rows = []
    for atom in all_atoms:
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "step10_count": int(s_counts.get(atom, 0)),
            "step10_ratio": s_counts.get(atom, 0) / s_total,
            "pulse_count": int(p_counts.get(atom, 0)),
            "pulse_ratio": p_counts.get(atom, 0) / p_total,
            "window_count": int(w_counts.get(atom, 0)),
            "window_ratio": w_counts.get(atom, 0) / w_total,
        })
    return pd.DataFrame(rows).sort_values("step10_count", ascending=False)


def main() -> None:
    print("v10.6 10-step trajectory cross-seed analysis")
    df_s = load_concat("step10_cid_alignment", STEP10_TRAJ)
    df_t = load_concat("step10_trajectory_patterns", STEP10_TRAJ)
    df_p = load_concat("pulse_cid_alignment", PULSE_TRAJ)
    df_w = load_concat("window_cid_alignment", WINDOW_TRAJ)

    print(f"  total step10 records: {len(df_s)}")
    print(f"  total cid trajectories (step10): {len(df_t)}")
    print(f"  pulse records (compare): {len(df_p)}")
    print(f"  window pairs (compare): {len(df_w)}")

    STEP10_TRAJ.mkdir(parents=True, exist_ok=True)

    df_atom = cross_seed_atom_distribution(df_s)
    safe_write_csv(df_atom, STEP10_TRAJ / "cross_seed_step10_atom_distribution.csv")

    df_step = cross_seed_step_evolution(df_s)
    safe_write_csv(df_step, STEP10_TRAJ / "cross_seed_step10_step_evolution.csv")

    df_cls = cross_seed_trajectory_class(df_t)
    safe_write_csv(df_cls, STEP10_TRAJ / "cross_seed_step10_trajectory_class_summary.csv")

    df_cmp = cross_seed_resolution_compare(df_s, df_p, df_w)
    safe_write_csv(df_cmp, STEP10_TRAJ / "cross_seed_resolution_compare.csv")

    print()
    print("=== top 20 atoms (step10, 24 seeds 統合) ===")
    print(df_atom.head(20).to_string(index=False))
    print()
    print("=== step evolution (1000-step bins, 24 seeds 統合) ===")
    print(df_step[["step_bin", "step_low", "n_records", "dominant_category",
                    "dominant_category_seed_unanimity",
                    "dominant_atom", "dominant_atom_count",
                    "rank_1_sim_mean"]].to_string(index=False))
    print()
    print("=== trajectory class (step10) ===")
    print(df_cls.to_string(index=False))
    print()
    print("=== resolution compare top 20 (by step10_count) ===")
    print(df_cmp.head(20).to_string(index=False))

    print(f"\nDONE  output = {STEP10_TRAJ}")


if __name__ == "__main__":
    main()
