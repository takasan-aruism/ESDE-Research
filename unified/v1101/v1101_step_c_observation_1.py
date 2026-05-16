#!/usr/bin/env python3
"""v1101 Step C — 観察 1 一点を捉える (中心 cid + ランダム比較対照)

Taka 確定:
  観察 1 主 = (c) n_pulses_short 最大 cid
  観察 1 副 = (d) ランダム比較対照
  cid pool  = v112 + v108_standard 両方併記 (Code A 仮所見)
  ランダム数 = 5 (Code A 仮所見)

入力 (read-only):
  developmental/v112/outputs/main/propagation_profile_v112_seed{0..23}.parquet
  developmental/v112/outputs/main/propagation_profile_v108_standard_seed{0..23}.parquet
  developmental/v106/outputs/main/{event,pulse,step10,window}_trajectory/*_cid_alignment_seed{0..23}.csv

出力:
  unified/v1101/outputs/main/observation_1_center_cids.parquet
  unified/v1101/outputs/main/observation_1_random_cids.parquet
  unified/v1101/outputs/main/observation_1_trajectory.parquet
  unified/v1101/outputs/main/observation_1_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path

import numpy as np
import pandas as pd

V106_MAIN = Path("/home/takasan/esde/ESDE-Research/developmental/v106/outputs/main")
V112_MAIN = Path("/home/takasan/esde/ESDE-Research/developmental/v112/outputs/main")
V1101_OUT = Path("/home/takasan/esde/ESDE-Research/unified/v1101/outputs/main")
SEEDS = list(range(24))
CONDITIONS = ["v112", "v108_standard"]
N_RANDOM = 5
RANDOM_SEED = 42

RESOLUTIONS = [
    ("event",  "event_trajectory",  "event_cid_alignment_seed{}.csv",  "t"),
    ("pulse",  "pulse_trajectory",  "pulse_cid_alignment_seed{}.csv",  "t"),
    ("step10", "step10_trajectory", "step10_cid_alignment_seed{}.csv", "t"),
    ("window", "window_trajectory", "window_cid_alignment_seed{}.csv", "step_at_window_end"),
]


def step_c1_select_center_cids() -> pd.DataFrame:
    rows = []
    for seed in SEEDS:
        for cond in CONDITIONS:
            p = V112_MAIN / f"propagation_profile_{cond}_seed{seed}.parquet"
            df = pd.read_parquet(p, columns=["source_cid", "n_pulses_short"])
            agg = df.groupby("source_cid")["n_pulses_short"].agg(["max", "mean", "count"]).reset_index()
            top = agg.nlargest(1, "max").iloc[0]
            rows.append({
                "seed": seed,
                "condition": cond,
                "center_cid": int(top["source_cid"]),
                "n_pulses_short_max": float(top["max"]),
                "n_pulses_short_mean": float(top["mean"]),
                "n_events_for_center": int(top["count"]),
                "cid_pool_size": int(agg.shape[0]),
            })
    df_centers = pd.DataFrame(rows)
    df_centers.to_parquet(V1101_OUT / "observation_1_center_cids.parquet", index=False)
    return df_centers


def step_c3_select_random_cids(centers_df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    for seed in SEEDS:
        for cond in CONDITIONS:
            p = V112_MAIN / f"propagation_profile_{cond}_seed{seed}.parquet"
            df = pd.read_parquet(p, columns=["source_cid"])
            cid_pool = df["source_cid"].unique()
            center = int(centers_df[(centers_df.seed == seed) & (centers_df.condition == cond)]["center_cid"].iloc[0])
            candidates = np.array([c for c in cid_pool if c != center])
            n = min(N_RANDOM, len(candidates))
            sampled = rng.choice(candidates, size=n, replace=False)
            for i, cid in enumerate(sampled):
                rows.append({
                    "seed": seed,
                    "condition": cond,
                    "rank": int(i),
                    "random_cid": int(cid),
                })
    df_random = pd.DataFrame(rows)
    df_random.to_parquet(V1101_OUT / "observation_1_random_cids.parquet", index=False)
    return df_random


def step_c2_extract_trajectories(centers_df: pd.DataFrame, random_df: pd.DataFrame) -> pd.DataFrame:
    """Extract 4-resolution trajectories for all center + random cids.

    Each (seed, cid) may belong to multiple (role, condition) pairs.
    The trajectory rows are tagged with all applicable labels."""
    all_parts = []
    for seed in SEEDS:
        # Build {cid: [(role, condition), ...]} for this seed
        cid_labels: dict[int, list[tuple[str, str]]] = {}
        for cond in CONDITIONS:
            cc = int(centers_df[(centers_df.seed == seed) & (centers_df.condition == cond)]["center_cid"].iloc[0])
            cid_labels.setdefault(cc, []).append(("center", cond))
            rcs = random_df[(random_df.seed == seed) & (random_df.condition == cond)]["random_cid"].tolist()
            for rc in rcs:
                cid_labels.setdefault(int(rc), []).append(("random", cond))
        target_cids = set(cid_labels.keys())

        for res_name, subdir, fname_tpl, t_col in RESOLUTIONS:
            p = V106_MAIN / subdir / fname_tpl.format(seed)
            df = pd.read_csv(p)
            # Common columns we care about
            keep = ["seed", "cognitive_id", "rank_1_atom", "rank_1_sim", "top_category"]
            for opt in ("n_core_member", "lifespan_so_far",
                        "C_at_window_end", "Q_remaining_at_window_end", "R_familiarity"):
                if opt in df.columns:
                    keep.append(opt)
            df_target = df[df["cognitive_id"].isin(target_cids)].copy()
            if df_target.empty:
                continue
            df_target = df_target[[c for c in keep if c in df_target.columns] + [t_col]].copy()
            df_target = df_target.rename(columns={t_col: "t"})
            df_target["resolution"] = res_name
            # Expand by role/condition labels
            rows = []
            for cid, labels in cid_labels.items():
                sub = df_target[df_target["cognitive_id"] == cid]
                if sub.empty:
                    continue
                for role, cond in labels:
                    s = sub.copy()
                    s["role"] = role
                    s["condition_pool"] = cond
                    rows.append(s)
            if rows:
                all_parts.append(pd.concat(rows, ignore_index=True))

    big = pd.concat(all_parts, ignore_index=True)
    big.to_parquet(V1101_OUT / "observation_1_trajectory.parquet", index=False)
    return big


def step_c4_summary(trajectory_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_keys = ["seed", "condition_pool", "role", "cognitive_id", "resolution"]
    for keys, grp in trajectory_df.groupby(group_keys, sort=False):
        seed, cond, role, cid, res = keys
        grp_sorted = grp.sort_values("t")
        atoms = grp_sorted["rank_1_atom"].tolist()
        sims = grp_sorted["rank_1_sim"].astype(float).to_numpy()
        n_obs = len(atoms)
        n_atom_changes = sum(1 for i in range(1, n_obs) if atoms[i] != atoms[i - 1])
        # dominant atom
        if n_obs:
            mode = pd.Series(atoms).mode()
            dom = mode.iloc[0] if len(mode) else ""
            dom_frac = (pd.Series(atoms) == dom).sum() / n_obs
        else:
            dom = ""
            dom_frac = float("nan")
        rows.append({
            "seed": int(seed),
            "condition_pool": cond,
            "role": role,
            "cid": int(cid),
            "resolution": res,
            "n_observations": int(n_obs),
            "n_atom_changes": int(n_atom_changes),
            "atom_change_rate": (n_atom_changes / (n_obs - 1)) if n_obs > 1 else float("nan"),
            "n_unique_atoms": int(len(set(atoms))),
            "dominant_atom": dom,
            "dominant_atom_fraction": float(dom_frac),
            "rank_1_sim_mean": float(sims.mean()) if n_obs else float("nan"),
            "rank_1_sim_std":  float(sims.std(ddof=0)) if n_obs > 1 else float("nan"),
            "rank_1_sim_min":  float(sims.min()) if n_obs else float("nan"),
            "rank_1_sim_max":  float(sims.max()) if n_obs else float("nan"),
            "t_min": float(grp_sorted["t"].min()) if n_obs else float("nan"),
            "t_max": float(grp_sorted["t"].max()) if n_obs else float("nan"),
        })
    summary_df = pd.DataFrame(rows)
    summary_df.to_parquet(V1101_OUT / "observation_1_summary.parquet", index=False)
    return summary_df


def main():
    V1101_OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("[C-1] center cid selection (n_pulses_short max per seed × condition)")
    centers = step_c1_select_center_cids()
    print(f"  -> {len(centers)} rows (24 seeds × 2 conditions)")

    print("[C-3] random comparison cids (rng seed=42)")
    randoms = step_c3_select_random_cids(centers)
    print(f"  -> {len(randoms)} rows (24 seeds × 2 conditions × {N_RANDOM})")

    print("[C-2] 4-resolution trajectory extraction")
    traj = step_c2_extract_trajectories(centers, randoms)
    print(f"  -> {len(traj)} trajectory rows")

    print("[C-4] summary aggregation")
    summary = step_c4_summary(traj)
    print(f"  -> {len(summary)} summary rows")

    dt = time.time() - t0
    print(f"Step C-1..C-4 done in {dt:.1f}s")


if __name__ == "__main__":
    main()
