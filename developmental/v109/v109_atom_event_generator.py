#!/usr/bin/env python3
"""v10.9 atom_introduction_event generator (3 新条件: A2 / B3 / C2).

v10.8 に対する v10.9 の差分:
- condition_id 列追加 (A2 / B3 / C2)
- A2: Q -2 / C +2 (top_k 100、timing は v10.8 と同じ)
- B3: Q -1 / C +1、cid 選定を seed 内全 cid から random 100、再現性 rng seed
- C2: Step F (bimodal 結果) 後に分岐実装、本ファイルでは枠のみ

A1 (= v10.8 baseline) は v10.8 出力を流用、本ファイルでは生成しない。
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V109_ROOT = (REPO_ROOT / "developmental" / "v109").resolve()

V106_MAIN = V106_ROOT / "outputs" / "main"

OUT_ROOT = V109_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v107_event_aggregator import attach_pre_event_state  # noqa: E402
from v107_baseline_constructor import _cid_meta_table  # noqa: E402
from v108_atom_event_generator import (  # noqa: E402
    TARGET_ATOMS,
    RESERVED_ATOM,
    RESERVED_LABEL,
    RUN_END_STEP,
    EVENTS_PER_ATOM,
    ATOM_INDEX_STEP_OFFSET,
    schedule_atom_event_timestamps,
    extract_top_k_cids,
)

SEEDS = list(range(24))
TOP_K = 100

# 条件設定 (即決事項確定 §2.1 案 c + Step F 判定 Q1-Q4)
CONDITIONS = {
    "A2": {
        "Q_cost": 2, "C_gain": 2,
        "cid_selection": "top_k_100",
        "timing": "uniform_atom_offset",
        "description": "Q -2 / C +2 (コスト感度評価、cid/timing は A1 と同じ)",
    },
    "B3": {
        "Q_cost": 1, "C_gain": 1,
        "cid_selection": "random_100",
        "timing": "uniform_atom_offset",
        "description": "random cid (seed 内全 cid から random 100、cid 選定感度)",
    },
    "C2": {
        "Q_cost": 1, "C_gain": 1,
        "cid_selection": "top_k_100",
        "timing": "lifecycle_synced",
        "age_target": 200,
        "description": "リズム同調 (top_k 100、各 cid age=200 で発火、Step F 分岐 1 採用)",
    },
}

# B3 random 用 seed (再現性担保、即決 §2.3)
B3_RNG_SEED_OFFSET = 1_090_000_300


def assert_output_under_v109(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")


def safe_write_parquet_v109(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v109(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def extract_random_cids(seed: int, atoms: list[str], n: int = TOP_K) -> pd.DataFrame:
    """seed 内全 cid から random n 個を atom 別に選定 (B3 用、再現性 rng seed).

    Returns:
        DataFrame with (atom_id, atom_index, top_k_rank=-1, source_cid, sim_score=NaN)
    """
    sim_path = V106_MAIN / f"cid_atom_sim_matrix_seed{seed}.parquet"
    df_sim = pd.read_parquet(sim_path)
    all_cids = df_sim["cid"].astype(int).tolist()
    rng = np.random.default_rng(B3_RNG_SEED_OFFSET + seed)
    rows = []
    for atom_idx, atom in enumerate(atoms):
        if len(all_cids) >= n:
            random_cids = rng.choice(all_cids, size=n, replace=False)
        else:
            random_cids = np.array(all_cids, dtype=int)
        for rank, cid in enumerate(random_cids, start=1):
            rows.append({
                "atom_id": atom,
                "atom_index": atom_idx,
                "top_k_rank": -1,
                "source_cid": int(cid),
                "sim_score": float("nan"),
            })
    return pd.DataFrame(rows)


def select_cids_for_condition(seed: int, atoms: list[str], condition_id: str) -> pd.DataFrame:
    cfg = CONDITIONS[condition_id]
    if cfg["cid_selection"] == "top_k_100":
        return extract_top_k_cids(seed, atoms, top_k=TOP_K)
    if cfg["cid_selection"] == "random_100":
        return extract_random_cids(seed, atoms, n=TOP_K)
    raise ValueError(f"Unknown cid_selection: {cfg['cid_selection']}")


def _build_cid_birth_lookup(seed: int) -> dict[int, int]:
    """seed 内の cognitive_id -> birth_step の lookup dict を構築 (C2 用)."""
    cid_meta = _cid_meta_table(seed)
    return dict(zip(
        cid_meta["cognitive_id"].astype(int),
        cid_meta["birth_step"].astype(int),
    ))


def generate_atom_events_for_condition(seed: int, cid_df: pd.DataFrame,
                                          condition_id: str) -> pd.DataFrame:
    """condition_id 列付きで event を生成。timing 別に分岐."""
    cfg = CONDITIONS[condition_id]
    timing = cfg["timing"]
    rows = []

    if timing == "lifecycle_synced":
        # C2: 各 cid の birth_step + age_target で発火
        cid_birth = _build_cid_birth_lookup(seed)
        age_target = cfg["age_target"]
        for atom_idx in cid_df["atom_index"].unique():
            atom_sub = cid_df[cid_df["atom_index"] == atom_idx].sort_values("top_k_rank")
            for _, r in atom_sub.iterrows():
                cid = int(r["source_cid"])
                if cid not in cid_birth:
                    continue
                ts = cid_birth[cid] + age_target
                if ts >= RUN_END_STEP:
                    continue
                atom_id = r["atom_id"]
                reserved_label = RESERVED_LABEL if atom_id == RESERVED_ATOM else ""
                rows.append({
                    "event_source_type": "atom_introduction_event",
                    "condition_id": condition_id,
                    "source_cid": cid,
                    "timestamp": int(ts),
                    "atom_id": atom_id,
                    "atom_index": int(atom_idx),
                    "top_k_rank": int(r["top_k_rank"]),
                    "atom_sim_score": float(r["sim_score"]) if pd.notna(r["sim_score"]) else float("nan"),
                    "reserved_label": reserved_label,
                })
    else:
        # A2 / B3: uniform_atom_offset (v10.8 と同じ)
        for atom_idx in cid_df["atom_index"].unique():
            atom_sub = cid_df[cid_df["atom_index"] == atom_idx].sort_values("top_k_rank")
            timestamps = schedule_atom_event_timestamps(int(atom_idx))
            for (_, r), t in zip(atom_sub.iterrows(), timestamps):
                atom_id = r["atom_id"]
                reserved_label = RESERVED_LABEL if atom_id == RESERVED_ATOM else ""
                rows.append({
                    "event_source_type": "atom_introduction_event",
                    "condition_id": condition_id,
                    "source_cid": int(r["source_cid"]),
                    "timestamp": int(t),
                    "atom_id": atom_id,
                    "atom_index": int(atom_idx),
                    "top_k_rank": int(r["top_k_rank"]),
                    "atom_sim_score": float(r["sim_score"]) if pd.notna(r["sim_score"]) else float("nan"),
                    "reserved_label": reserved_label,
                })

    df = pd.DataFrame(rows)
    df["seed"] = seed
    df = df.sort_values(["timestamp", "atom_index"]).reset_index(drop=True)
    df["event_id"] = [f"{seed}_{condition_id}_atom_{i}" for i in range(len(df))]
    return df


def attach_states_for_condition(df: pd.DataFrame, seed: int, condition_id: str) -> pd.DataFrame:
    """v10.7 attach_pre_event_state を流用、post_event_state を計算的に追加."""
    cfg = CONDITIONS[condition_id]
    df_with_pre = attach_pre_event_state(df, seed)
    df_with_pre["Q_after_atom_intro"] = df_with_pre["Q_pre"] - cfg["Q_cost"]
    df_with_pre["C_after_atom_intro"] = df_with_pre["C_pre"] + cfg["C_gain"]
    return df_with_pre


def generate_seed_atom_events(seed: int, condition_id: str,
                                atoms: list[str] | None = None) -> pd.DataFrame:
    if atoms is None:
        atoms = TARGET_ATOMS
    cid_df = select_cids_for_condition(seed, atoms, condition_id)
    df = generate_atom_events_for_condition(seed, cid_df, condition_id)
    df = attach_states_for_condition(df, seed, condition_id)
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--conditions", default="A2,B3",
                       help="Comma-separated condition ids (default: A2,B3)")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conditions:
        if c not in CONDITIONS:
            raise SystemExit(f"Unknown condition: {c} (valid: {list(CONDITIONS)})")

    print(f"v10.9 atom_event_generator - mode={args.mode}, seeds={seeds}, conditions={conditions}")
    print(f"  TARGET_ATOMS: {len(TARGET_ATOMS)} (incl. WLD.artless reserved)")
    print(f"  TOP_K: {TOP_K}, EVENTS_PER_ATOM: {EVENTS_PER_ATOM}")
    for cid in conditions:
        cfg = CONDITIONS[cid]
        print(f"  [{cid}] {cfg['description']}: Q-{cfg['Q_cost']}, C+{cfg['C_gain']}, "
              f"cid_selection={cfg['cid_selection']}")
    print()

    summaries = []
    t0 = time.time()
    for seed in seeds:
        for condition_id in conditions:
            ts = time.time()
            df = generate_seed_atom_events(seed, condition_id)
            out = out_root / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"
            safe_write_parquet_v109(df, out)
            elapsed = time.time() - ts
            size_mb = round(out.stat().st_size / 1024 / 1024, 3)
            n_reserved = (df["reserved_label"] == RESERVED_LABEL).sum()
            unique_cids = int(df["source_cid"].nunique())
            summary = {
                "seed": seed, "condition_id": condition_id,
                "n_events": int(len(df)),
                "n_atoms": int(df["atom_id"].nunique()),
                "n_unique_cids": unique_cids,
                "timestamp_min": int(df["timestamp"].min()),
                "timestamp_max": int(df["timestamp"].max()),
                "size_mb": size_mb, "elapsed_sec": round(elapsed, 2),
            }
            print(f"  seed={seed} cond={condition_id}: events={summary['n_events']}, "
                  f"atoms={summary['n_atoms']}, unique_cids={unique_cids}, "
                  f"reserved={n_reserved}, "
                  f"t_range={summary['timestamp_min']}-{summary['timestamp_max']}, "
                  f"size={size_mb}MB, elapsed={elapsed:.2f}s")
            summaries.append(summary)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v109(df_sum, out_root / "atom_event_run_summary.parquet")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
