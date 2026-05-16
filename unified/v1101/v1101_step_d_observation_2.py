#!/usr/bin/env python3
"""v1101 Step D — 観察 2「取り込み点中心の波及」

Taka 確定:
  観察 2 中心 = (a) v10.12 受容 cid pool 420 (atom_introduction_events_v112 由来)
  (b) atom 濃度近接 cid: 不採用
  周辺 cid = (Code A 仮所見) 同 seed 全 cid (~228)

時間グリッド:
  step10 解像度 (10 step 間隔均一、t=10..25000)
  Δt ∈ {-100, -90, ..., 0, +10, ..., +100} = 21 points (±100 step window)
  t0 (event timestamp) は最寄 step10 t (round(t0/10)*10) に整列

入力 (read-only):
  developmental/v112/outputs/main/atom_introduction_events_v112_seed{0..23}.parquet
  developmental/v106/outputs/main/step10_trajectory/step10_cid_alignment_seed{0..23}.csv

出力:
  unified/v1101/outputs/main/observation_2_events.parquet (取り込み点一覧)
  unified/v1101/outputs/main/observation_2_propagation.parquet (per event × Δt 集計)
  unified/v1101/outputs/main/observation_2_summary.parquet (per atom × Δt 集計)
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
DELTA_TS = list(range(-100, 101, 10))   # 21 points covering ±100 step window
STEP10_STEP = 10


def step_d1_enumerate_events() -> pd.DataFrame:
    """v112 atom_introduction_events を 24 seeds から列挙。"""
    parts = []
    for seed in SEEDS:
        p = V112_MAIN / f"atom_introduction_events_v112_seed{seed}.parquet"
        df = pd.read_parquet(
            p,
            columns=["seed", "event_id", "source_cid", "timestamp",
                     "atom_id", "atom_index", "target_step",
                     "Q_pre", "C_pre", "Q_after_atom_intro", "C_after_atom_intro",
                     "n_core_bin", "formation_relation", "lifespan"],
        )
        parts.append(df)
    events = pd.concat(parts, ignore_index=True)
    # Align timestamp to nearest step10 grid (round to nearest 10)
    events["t0_aligned"] = ((events["timestamp"] + STEP10_STEP // 2) // STEP10_STEP) * STEP10_STEP
    events.to_parquet(V1101_OUT / "observation_2_events.parquet", index=False)
    return events


def _load_step10_trajectory(seed: int) -> pd.DataFrame:
    p = V106_MAIN / "step10_trajectory" / f"step10_cid_alignment_seed{seed}.csv"
    df = pd.read_csv(
        p,
        usecols=["seed", "cognitive_id", "t", "rank_1_atom", "rank_1_sim",
                 "n_core_member", "lifespan_so_far", "final_state"],
    )
    return df


def step_d2_d3_compute_propagation(events: pd.DataFrame) -> pd.DataFrame:
    """per (event, Δt) で 同 seed 全 cid の atom 状態を集計。

    出力: per (event_id, delta_t) で 11 列の集計。
    """
    rows = []
    for seed in SEEDS:
        df_traj = _load_step10_trajectory(seed)
        # Pre-index by t for fast slicing
        traj_by_t: dict[int, pd.DataFrame] = {t: g for t, g in df_traj.groupby("t")}
        events_seed = events[events["seed"] == seed]

        for _, ev in events_seed.iterrows():
            event_id = ev["event_id"]
            source_cid = int(ev["source_cid"])
            atom_intro = ev["atom_id"]
            t0 = int(ev["t0_aligned"])

            for dt in DELTA_TS:
                t = t0 + dt
                grp = traj_by_t.get(t)
                if grp is None or grp.empty:
                    rows.append({
                        "seed": seed,
                        "event_id": event_id,
                        "source_cid": source_cid,
                        "atom_intro": atom_intro,
                        "t0_aligned": t0,
                        "delta_t": dt,
                        "t": t,
                        "n_cids_alive": 0,
                        "n_cids_matching_atom_intro": 0,
                        "match_fraction": float("nan"),
                        "n_unique_atoms": 0,
                        "atom_entropy_bits": float("nan"),
                        "mean_rank_1_sim": float("nan"),
                        "center_alive": False,
                        "center_rank_1_atom": None,
                        "center_rank_1_sim": float("nan"),
                        "center_atom_matches_intro": False,
                    })
                    continue

                n_alive = len(grp)
                matches_mask = grp["rank_1_atom"] == atom_intro
                n_match = int(matches_mask.sum())
                match_frac = n_match / n_alive
                # atom entropy (Shannon, bits)
                atom_counts = grp["rank_1_atom"].value_counts()
                p_atoms = atom_counts.to_numpy(dtype=float) / n_alive
                ent = float(-(p_atoms * np.log2(p_atoms + 1e-12)).sum())
                mean_sim = float(grp["rank_1_sim"].mean())

                # Center cid status
                center_row = grp[grp["cognitive_id"] == source_cid]
                if center_row.empty:
                    center_alive = False
                    c_atom = None
                    c_sim = float("nan")
                    c_match = False
                else:
                    center_alive = True
                    c_atom = str(center_row["rank_1_atom"].iloc[0])
                    c_sim = float(center_row["rank_1_sim"].iloc[0])
                    c_match = (c_atom == atom_intro)

                rows.append({
                    "seed": seed,
                    "event_id": event_id,
                    "source_cid": source_cid,
                    "atom_intro": atom_intro,
                    "t0_aligned": t0,
                    "delta_t": dt,
                    "t": t,
                    "n_cids_alive": n_alive,
                    "n_cids_matching_atom_intro": n_match,
                    "match_fraction": match_frac,
                    "n_unique_atoms": int(atom_counts.shape[0]),
                    "atom_entropy_bits": ent,
                    "mean_rank_1_sim": mean_sim,
                    "center_alive": center_alive,
                    "center_rank_1_atom": c_atom,
                    "center_rank_1_sim": c_sim,
                    "center_atom_matches_intro": c_match,
                })

    df = pd.DataFrame(rows)
    df.to_parquet(V1101_OUT / "observation_2_propagation.parquet", index=False)
    return df


def step_d4_summary(prop_df: pd.DataFrame) -> pd.DataFrame:
    """per atom × Δt の集約 (波及プロファイル)."""
    grp = prop_df.groupby(["atom_intro", "delta_t"])
    summary = grp.agg(
        n_events=("event_id", "count"),
        match_fraction_mean=("match_fraction", "mean"),
        match_fraction_median=("match_fraction", "median"),
        match_fraction_std=("match_fraction", "std"),
        n_cids_alive_mean=("n_cids_alive", "mean"),
        n_cids_matching_mean=("n_cids_matching_atom_intro", "mean"),
        atom_entropy_mean=("atom_entropy_bits", "mean"),
        mean_rank_1_sim_mean=("mean_rank_1_sim", "mean"),
        center_match_rate=("center_atom_matches_intro", "mean"),
        center_alive_rate=("center_alive", "mean"),
    ).reset_index()
    summary.to_parquet(V1101_OUT / "observation_2_summary.parquet", index=False)
    return summary


def main():
    V1101_OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("[D-1] enumerate atom_introduction_events_v112 (24 seeds)")
    events = step_d1_enumerate_events()
    print(f"  -> {len(events)} events")

    print("[D-2/D-3] per (event × delta_t) propagation metrics")
    prop = step_d2_d3_compute_propagation(events)
    print(f"  -> {len(prop)} (event × delta_t) rows")

    print("[D-4] per (atom × delta_t) summary")
    summary = step_d4_summary(prop)
    print(f"  -> {len(summary)} (atom × delta_t) summary rows")

    dt = time.time() - t0
    print(f"Step D-1..D-4 done in {dt:.1f}s")


if __name__ == "__main__":
    main()
