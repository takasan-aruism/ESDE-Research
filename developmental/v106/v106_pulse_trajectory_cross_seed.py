#!/usr/bin/env python3
"""v10.6 per-pulse trajectory cross-seed analysis.

24 seeds の per-pulse alignment を統合し、

1. rank_1 atom 出現分布 (per-pulse vs per-window 比較)
2. trigger 別 atom alignment (動学的特徴)
3. step 区間別 dominant atom (pulse 単位の発展段階)
4. trajectory_class 分布 (per-pulse 解像度)
5. n_core 別 trajectory_class
6. 動学 atom emergence (window 解析と比較して新規/消失)

を集計、CSV 出力。
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = REPO_ROOT / "developmental" / "v106"
PULSE_TRAJ = V106_ROOT / "outputs" / "main" / "pulse_trajectory"
WINDOW_TRAJ = V106_ROOT / "outputs" / "main" / "window_trajectory"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import safe_write_csv  # noqa: E402

SEEDS = list(range(24))

STEP_BIN_SIZE = 1000  # 25 bins for 25,000 steps


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
            "n_pulse_records": int(cnt),
            "ratio_overall": cnt / len(df),
            "n_seeds_appeared": int(sub["seed"].nunique()),
            "n_unique_cids": int(sub["cognitive_id"].nunique()),
            "rank_1_sim_mean": float(sub["rank_1_sim"].mean()),
            "rank_1_sim_max": float(sub["rank_1_sim"].max()),
        })
    return pd.DataFrame(rows).sort_values("n_pulse_records", ascending=False)


def cross_seed_trigger_atom(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for trigger, sub in df.groupby("trigger"):
        n_pulses = len(sub)
        atom_counts = sub["rank_1_atom"].value_counts()
        for atom, cnt in atom_counts.head(10).items():
            rows.append({
                "trigger": trigger,
                "n_pulses_total": n_pulses,
                "rank_1_atom": atom,
                "category": atom.split(".")[0],
                "count": int(cnt),
                "ratio_within_trigger": cnt / n_pulses,
                "n_seeds_appeared": int(sub[sub["rank_1_atom"] == atom]["seed"].nunique()),
            })
    return pd.DataFrame(rows)


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
            "n_pulses": int(len(sub)),
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
    rows = []
    for cls, cnt in counts.items():
        rows.append({
            "trajectory_class": cls,
            "n_cids_total_24seeds": int(cnt),
            "ratio": cnt / total if total else 0,
            "n_cids_mean_per_seed": cnt / 24,
        })
    return pd.DataFrame(rows).sort_values("n_cids_total_24seeds", ascending=False)


def cross_seed_traj_class_by_ncore(df_traj: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    n_core_lookup = (
        df.dropna(subset=["n_core_member"])
        [["seed", "cognitive_id", "n_core_member"]]
        .drop_duplicates(["seed", "cognitive_id"])
    )
    n_core_lookup["n_core_member"] = pd.to_numeric(
        n_core_lookup["n_core_member"], errors="coerce"
    )
    merged = df_traj.merge(n_core_lookup, on=["seed", "cognitive_id"], how="left")
    merged["n_core_int"] = merged["n_core_member"].fillna(-1).astype(int)
    rows = []
    for nc in sorted(merged["n_core_int"].unique()):
        sub = merged[merged["n_core_int"] == nc]
        for cls, cnt in sub["trajectory_class"].value_counts().items():
            rows.append({
                "n_core_member": nc if nc > 0 else "unknown",
                "trajectory_class": cls,
                "n_cids": int(cnt),
                "ratio_within_n_core": cnt / len(sub) if len(sub) else 0,
            })
    return pd.DataFrame(rows)


def compare_pulse_vs_window_atom(df_pulse: pd.DataFrame,
                                   df_window: pd.DataFrame) -> pd.DataFrame:
    p_counts = df_pulse["rank_1_atom"].value_counts()
    w_counts = df_window["rank_1_atom"].value_counts() if not df_window.empty else pd.Series()
    all_atoms = sorted(set(p_counts.index) | set(w_counts.index))
    rows = []
    for atom in all_atoms:
        p_cnt = int(p_counts.get(atom, 0))
        w_cnt = int(w_counts.get(atom, 0))
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "pulse_rank1_count": p_cnt,
            "window_rank1_count": w_cnt,
            "pulse_only": p_cnt > 0 and w_cnt == 0,
            "window_only": p_cnt == 0 and w_cnt > 0,
            "delta_pulse_minus_window": p_cnt - w_cnt,
        })
    return pd.DataFrame(rows).sort_values("delta_pulse_minus_window", ascending=False)


def main() -> None:
    print("v10.6 per-pulse trajectory cross-seed analysis")
    df_p = load_concat("pulse_cid_alignment", PULSE_TRAJ)
    df_t = load_concat("pulse_trajectory_patterns", PULSE_TRAJ)
    df_w = load_concat("window_cid_alignment", WINDOW_TRAJ)

    print(f"  total pulse records: {len(df_p)}")
    print(f"  total cid trajectories (per-pulse): {len(df_t)}")
    print(f"  total window pairs (for comparison): {len(df_w)}")

    PULSE_TRAJ.mkdir(parents=True, exist_ok=True)

    df_atom = cross_seed_atom_distribution(df_p)
    safe_write_csv(df_atom, PULSE_TRAJ / "cross_seed_pulse_atom_distribution.csv")

    df_trig = cross_seed_trigger_atom(df_p)
    safe_write_csv(df_trig, PULSE_TRAJ / "cross_seed_trigger_atom.csv")

    df_step = cross_seed_step_evolution(df_p)
    safe_write_csv(df_step, PULSE_TRAJ / "cross_seed_step_evolution.csv")

    df_cls = cross_seed_trajectory_class(df_t)
    safe_write_csv(df_cls, PULSE_TRAJ / "cross_seed_trajectory_class_summary.csv")

    df_nc = cross_seed_traj_class_by_ncore(df_t, df_p)
    safe_write_csv(df_nc, PULSE_TRAJ / "cross_seed_trajectory_class_by_ncore.csv")

    df_cmp = compare_pulse_vs_window_atom(df_p, df_w)
    safe_write_csv(df_cmp, PULSE_TRAJ / "cross_seed_pulse_vs_window_atom.csv")

    print()
    print("=== top 20 rank_1 atoms (per-pulse, 24 seeds 統合) ===")
    print(df_atom.head(20).to_string(index=False))
    print()
    print("=== trigger summary (24 seeds 統合) ===")
    for trigger, sub in df_trig.groupby("trigger"):
        total = sub["n_pulses_total"].iloc[0]
        top = sub.head(3)
        atoms = ", ".join(f"{r['rank_1_atom']}({r['ratio_within_trigger']:.0%})"
                            for _, r in top.iterrows())
        print(f"  {trigger:18s} n={total:6d}: {atoms}")
    print()
    print("=== step evolution (1000-step bins、24 seeds 統合) ===")
    print(df_step[["step_bin", "step_low", "n_pulses", "dominant_category",
                    "dominant_category_seed_unanimity",
                    "dominant_atom", "dominant_atom_count",
                    "rank_1_sim_mean"]].to_string(index=False))
    print()
    print("=== trajectory class (per-pulse) ===")
    print(df_cls.to_string(index=False))
    print()
    print("=== top 10 atoms more frequent in per-pulse than per-window ===")
    print(df_cmp.head(10).to_string(index=False))
    print()
    print("=== top 10 atoms more frequent in per-window than per-pulse ===")
    print(df_cmp.tail(10).iloc[::-1].to_string(index=False))

    print(f"\nDONE  output = {PULSE_TRAJ}")


if __name__ == "__main__":
    main()
