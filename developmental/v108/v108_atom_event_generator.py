#!/usr/bin/env python3
"""v10.8 atom_introduction_event generator (案 Q + 案 α).

25 atom × top 100 cid × 24 seeds = 60,000 atom_introduction_events を生成。
v10.7 source_event スキーマ互換 + atom メタ情報 (atom_id, atom_index,
top_k_rank, reserved_label)。

入力:
  - v10.6 cid_atom_sim_matrix_seed*.parquet (top_k cid 抽出)
  - v10.6 step10_baseline/step10_atom_z_score.csv (25 atom 確認用)
  - v10.5 各種 (pre_event_state 取得用、v10.7 流用)

出力:
  developmental/v108/outputs/{smoke,main}/
    atom_introduction_events_seed{N}.parquet
"""
from __future__ import annotations

import argparse
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

V106_MAIN = V106_ROOT / "outputs" / "main"
DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"

OUT_ROOT = V108_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V106_ROOT))
sys.path.insert(0, str(V107_ROOT))
from v106_post_process import safe_read_csv  # noqa: E402
from v107_event_aggregator import attach_pre_event_state  # noqa: E402

SEEDS = list(range(24))
RUN_END_STEP = 25000
TOP_K = 100
EVENTS_PER_ATOM = 100
ATOM_INDEX_STEP_OFFSET = 10  # atom_index × 10 step ずらし

# 25 確定 atom (Step B 環境チェック報告)
TARGET_ATOMS = [
    "BOD.ear",
    "COG.learn",
    "COM.silence",
    "EXS.being",
    "EXS.nonbeing",
    "FND.timeless",
    "FND.transformation",
    "PER.feel",
    "PER.fragrance",
    "PER.hear",
    "PER.see",
    "PER.smell",
    "PER.sound",
    "PER.soundless",
    "PER.taste",
    "PRP.bright",
    "PRP.deep",
    "PRP.sharp",
    "SOC.city",
    "SOC.nation",
    "SOC.public",
    "TIM.appear",
    "WLD.artless",      # 留保ラベル付き、集計から除外
    "WLD.culture",
    "WLD.technique",
]
RESERVED_ATOM = "WLD.artless"
RESERVED_LABEL = "wld_artless_pending"

# Q/C コスト (即決 §2.3 確定: balance_decisions.cognition 固定値)
ATOM_INTRO_Q_COST = 1   # Q を 1 消費
ATOM_INTRO_C_GAIN = 1   # C を 1 獲得


def assert_output_under_v108(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V108_ROOT not in abs_path.parents and abs_path != V108_ROOT:
        raise ValueError(f"Output path {path} not under v108/")


def safe_write_parquet_v108(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v108(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 1. top_k cid 抽出 (cid_atom_sim_matrix から)
# ----------------------------------------------------------------------
def extract_top_k_cids(seed: int, atoms: list[str], top_k: int = TOP_K) -> pd.DataFrame:
    """各 atom について top_k cid を sim 上位順に抽出.

    Returns:
        DataFrame with (atom_id, atom_index, top_k_rank, source_cid, sim_score)
    """
    sim_path = V106_MAIN / f"cid_atom_sim_matrix_seed{seed}.parquet"
    df_sim = pd.read_parquet(sim_path)
    rows = []
    for atom_idx, atom in enumerate(atoms):
        if atom not in df_sim.columns:
            print(f"  WARN: {atom} not in sim_matrix for seed {seed}")
            continue
        sub = df_sim[["cid", atom]].dropna().sort_values(atom, ascending=False).head(top_k)
        for rank, (cid, sim) in enumerate(zip(sub["cid"].astype(int).tolist(),
                                                  sub[atom].tolist()), start=1):
            rows.append({
                "atom_id": atom,
                "atom_index": atom_idx,
                "top_k_rank": rank,
                "source_cid": int(cid),
                "sim_score": float(sim),
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 2. timestamp 均等分散発火 (案 α)
# ----------------------------------------------------------------------
def schedule_atom_event_timestamps(atom_index: int,
                                      n_events: int = EVENTS_PER_ATOM) -> list[int]:
    """atom_index ごとに 100 events を 25000 step に均等分散.
    atom_index × 10 step ずらしで同時刻発火を最小化.

    Returns: list of int timestamps (例: [100, 350, 600, ..., 24850] for atom_idx=0)
    """
    base_offset = 100 + (atom_index * ATOM_INDEX_STEP_OFFSET)
    interval = (RUN_END_STEP - base_offset) // n_events
    return [base_offset + i * interval for i in range(n_events)]


# ----------------------------------------------------------------------
# 3. atom_introduction_event 生成
# ----------------------------------------------------------------------
def generate_atom_events(seed: int, top_k_df: pd.DataFrame) -> pd.DataFrame:
    """各 (atom, top_k_rank) ペアに timestamp を割当てて event 生成."""
    rows = []
    for atom_idx in top_k_df["atom_index"].unique():
        atom_sub = top_k_df[top_k_df["atom_index"] == atom_idx].sort_values("top_k_rank")
        timestamps = schedule_atom_event_timestamps(int(atom_idx))
        for (_, r), t in zip(atom_sub.iterrows(), timestamps):
            atom_id = r["atom_id"]
            reserved_label = RESERVED_LABEL if atom_id == RESERVED_ATOM else ""
            rows.append({
                "event_source_type": "atom_introduction_event",
                "source_cid": int(r["source_cid"]),
                "timestamp": int(t),
                "atom_id": atom_id,
                "atom_index": int(atom_idx),
                "top_k_rank": int(r["top_k_rank"]),
                "atom_sim_score": float(r["sim_score"]),
                "reserved_label": reserved_label,
            })
    df = pd.DataFrame(rows)
    df["seed"] = seed
    df = df.sort_values(["timestamp", "atom_index"]).reset_index(drop=True)
    df["event_id"] = [f"{seed}_atom_{i}" for i in range(len(df))]
    return df


# ----------------------------------------------------------------------
# 4. pre/post_event_state 添付 (post = Q-1, C+1 の計算的減算)
# ----------------------------------------------------------------------
def attach_atom_event_states(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """v10.7 attach_pre_event_state を流用、post_event_state を計算的に追加."""
    df_with_pre = attach_pre_event_state(df, seed)
    # post_event_state: 計算的減算 (実 ledger 不変、post-process 上のみ)
    df_with_pre["Q_after_atom_intro"] = df_with_pre["Q_pre"] - ATOM_INTRO_Q_COST
    df_with_pre["C_after_atom_intro"] = df_with_pre["C_pre"] + ATOM_INTRO_C_GAIN
    return df_with_pre


# ----------------------------------------------------------------------
# Per-seed full pipeline
# ----------------------------------------------------------------------
def generate_seed_atom_events(seed: int, atoms: list[str] = None) -> pd.DataFrame:
    if atoms is None:
        atoms = TARGET_ATOMS
    top_k_df = extract_top_k_cids(seed, atoms, top_k=TOP_K)
    df = generate_atom_events(seed, top_k_df)
    df = attach_atom_event_states(df, seed)
    return df


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.8 atom_event_generator - mode={args.mode}, seeds={seeds}")
    print(f"  TARGET_ATOMS: {len(TARGET_ATOMS)} (incl. WLD.artless reserved)")
    print(f"  TOP_K: {TOP_K}, EVENTS_PER_ATOM: {EVENTS_PER_ATOM}")
    print(f"  Q cost: {ATOM_INTRO_Q_COST}, C gain: {ATOM_INTRO_C_GAIN}")
    print()

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        df = generate_seed_atom_events(seed)
        out = out_root / f"atom_introduction_events_seed{seed}.parquet"
        safe_write_parquet_v108(df, out)
        elapsed = time.time() - ts
        size_mb = round(out.stat().st_size / 1024 / 1024, 2)
        summary = {
            "seed": seed, "n_events": int(len(df)),
            "n_atoms": int(df["atom_id"].nunique()),
            "n_unique_cids": int(df["source_cid"].nunique()),
            "timestamp_min": int(df["timestamp"].min()),
            "timestamp_max": int(df["timestamp"].max()),
            "size_mb": size_mb, "elapsed_sec": round(elapsed, 2),
        }
        n_reserved = (df["reserved_label"] == RESERVED_LABEL).sum()
        print(f"  seed={seed}: events={summary['n_events']}, "
              f"atoms={summary['n_atoms']}, unique_cids={summary['n_unique_cids']}, "
              f"reserved={n_reserved}, t_range={summary['timestamp_min']}-{summary['timestamp_max']}, "
              f"size={size_mb}MB, elapsed={elapsed:.2f}s")
        summaries.append(summary)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v108(df_sum, out_root / "atom_event_run_summary.parquet")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
