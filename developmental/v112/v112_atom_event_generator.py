#!/usr/bin/env python3
"""v10.12 Step D: v112_atom_event_generator.

第 5 版主題 (Atom 取り込み prototype) の atom_introduction_events 生成器.

v112 仕様 (主観察対象):
  - Step C で抽出された受容 cid pool (4 条件複合、24 seeds total 420 cid) に対し、
    各 cid が 25 atom 全てを target_step + atom_index × 10 で受容する compact burst.
  - 24 seeds total events = 420 × 25 = 10,500 events
  - 各 event は cid.target_step (= birth + 200) を基準に 240 step 窓内で発火

v108_standard 仕様 (副次比較対象、DC-A3 既存出力流用):
  - v10.8 main 出力 (atom_introduction_events_seed*.parquet) を読み込み
  - Step C v108_standard cid pool (target_step < death PASS) で filter
  - Step C metadata (n_core_bin, formation_relation, target_step) を inner-join 付与

attach_pre_event_state は v107_event_aggregator を共通利用.
Q_after_atom_intro = Q_pre - 1, C_after_atom_intro = C_pre + 1 (計算的減算、ledger 不変).

規律:
- 物理層 frozen: 本ファイルは ledger 不変、events 生成のみ
- 神の手回避: Step C 4 条件複合 + 25 atom 全展開、ハンドチューニングなし
- 因果断定回避: 「受容 cid」「字面に揺れる」表現
- 層 B 不変: v108 main 出力は読み込みのみ (v108/outputs/main/ は不変)
- 層 C: 出力は v112/outputs/{smoke,main}/ 配下のみ
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()

# v108 atom_introduction_events は実体として v110/v108_re/outputs/{mode}/ に存在
# (v10.10 で v108_re として再実行、層 B 不変保証のため v108 出力と bit-identical)
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()
V108_RE_MAIN = V110_ROOT / "v108_re" / "outputs" / "main"
V108_RE_SMOKE = V110_ROOT / "v108_re" / "outputs" / "smoke"
STEP_C_ROOT = V112_ROOT / "outputs" / "step_c"
SMOKE_ROOT = V112_ROOT / "outputs" / "smoke"
MAIN_ROOT = V112_ROOT / "outputs" / "main"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v107_event_aggregator import attach_pre_event_state  # noqa: E402
from v108_atom_event_generator import (  # noqa: E402
    TARGET_ATOMS, RESERVED_ATOM, RESERVED_LABEL,
    RUN_END_STEP,
)

SEEDS = list(range(24))
ATOM_INDEX_STEP_OFFSET = 10  # cid 内 atom 間 step ずらし (v10.8 と同値)
Q_COST = 1
C_GAIN = 1
N_ATOMS = 25  # TARGET_ATOMS 数


def assert_output_under_v112(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V112_ROOT not in abs_path.parents and abs_path != V112_ROOT:
        raise ValueError(f"Output path {path} not under v112/")


def safe_write_parquet_v112(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# 共通 metadata (両 condition_set で利用可能)
STEP_C_META_COLS_COMMON = [
    "source_cid", "target_step", "death_step",
    "n_core", "n_core_bin", "formation_relation",
    "lifespan", "fam_max",
]
# v112 専用 (cond4 由来)
STEP_C_META_COLS_V112_ONLY = ["top_50_threshold"]


# ----------------------------------------------------------------------
# v112 events 生成: 420 cid × 25 atom = 10,500 events (24 seeds total)
# ----------------------------------------------------------------------
def generate_v112_events_for_seed(seed: int) -> pd.DataFrame:
    """Step C v112 受容 cid に対し 25 atom × cid burst を生成.

    各 cid: target_step + atom_index × 10 で 25 event (240 step 窓内、cond2 lifespan ≥ 977 で安全)
    attach_pre_event_state が birth_step 等の cid 属性を自動付与するため、Step C metadata は
    attach 後に merge する (重複列回避).
    """
    cid_path = STEP_C_ROOT / f"receptive_cids_v112_seed{seed}.parquet"
    if not cid_path.exists():
        raise FileNotFoundError(f"Step C output not found: {cid_path}")
    cids_df = pd.read_parquet(cid_path)

    rows = []
    for _, cid_row in cids_df.iterrows():
        cid = int(cid_row["source_cid"])
        target_step = int(cid_row["target_step"])
        death = int(cid_row["death_step"])
        # 安全境界: target_step + 24*10 = target_step+240、cond2 で lifespan ≥ 977 だが念のため
        for atom_idx, atom_id in enumerate(TARGET_ATOMS):
            t_event = target_step + atom_idx * ATOM_INDEX_STEP_OFFSET
            if t_event >= RUN_END_STEP or t_event >= death:
                continue
            reserved_label = RESERVED_LABEL if atom_id == RESERVED_ATOM else ""
            rows.append({
                "event_source_type": "atom_introduction_event",
                "condition_id": "v112",
                "source_cid": cid,
                "timestamp": int(t_event),
                "atom_id": atom_id,
                "atom_index": int(atom_idx),
                "top_k_rank": -1,  # v112 は 4 条件複合、top_k_rank 概念なし
                "atom_sim_score": float("nan"),
                "reserved_label": reserved_label,
            })

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["seed"] = seed
    df = df.sort_values(["timestamp", "source_cid", "atom_index"]).reset_index(drop=True)
    df["event_id"] = [f"{seed}_v112_atom_{i}" for i in range(len(df))]

    # attach_pre_event_state (Q_pre, C_pre, R_familiarity_pre, birth_step, etc.)
    df = attach_pre_event_state(df, seed)
    # 計算的減算 (ledger 不変)
    df["Q_after_atom_intro"] = df["Q_pre"] - Q_COST
    df["C_after_atom_intro"] = df["C_pre"] + C_GAIN

    # Step C metadata (cid-level 層化軸) を attach 後に左 join
    meta_cols = STEP_C_META_COLS_COMMON + STEP_C_META_COLS_V112_ONLY
    meta_df = cids_df[meta_cols].copy()
    df = df.merge(meta_df, on="source_cid", how="left")
    return df


# ----------------------------------------------------------------------
# v108_standard events 生成: v108 既存 main 出力流用 + Step C metadata 付与
# ----------------------------------------------------------------------
def generate_v108_standard_events_for_seed(seed: int) -> pd.DataFrame:
    """v108 main 出力を読み込み、Step C v108_standard cid pool で filter + metadata 付与.

    層 B 不変: v108 main 出力は読み込みのみ (書き込みなし).
    結果は v112/outputs/ 配下に書き込み.
    """
    # v108_re (v10.10 で v108 出力を再現したもの) を流用 (DC-A3 既存出力)
    v108_events_path = V108_RE_MAIN / f"atom_introduction_events_v108_re_seed{seed}.parquet"
    if not v108_events_path.exists():
        raise FileNotFoundError(f"v108_re main events not found: {v108_events_path}")
    df_v108 = pd.read_parquet(v108_events_path)
    df_v108 = df_v108.copy()  # 読み取り元と切り離し (層 B 保護)
    df_v108["condition_id"] = "v108_standard"

    cid_path = STEP_C_ROOT / f"receptive_cids_v108_standard_seed{seed}.parquet"
    cids_df = pd.read_parquet(cid_path)
    # Step C metadata (cid-level 層化軸)、v108 既存の birth_step / death_step 等と
    # 列名衝突しないよう、共通 columns のみ inner-join 対象。
    # ただし v108 既存に target_step / n_core_bin 等は無いので衝突なし。
    # death_step は v108 既存に host_lost_step / reaped_step として存在するので、
    # 名前は death_step として独立保持。
    meta_df = cids_df[STEP_C_META_COLS_COMMON].copy()

    # inner-join: v108_standard pool に存在する cid のみ (target_step < death PASS した cid)
    df = df_v108.merge(meta_df, on="source_cid", how="inner")
    df = df.sort_values(["timestamp", "atom_index"]).reset_index(drop=True)
    # event_id は v108_re 既存値を保持 (Step E で v108_re baselines を event_id で流用するため)
    return df


# ----------------------------------------------------------------------
# Per-seed full pipeline
# ----------------------------------------------------------------------
def process_seed(seed: int, mode: str) -> dict:
    out_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    df_v112 = generate_v112_events_for_seed(seed)
    t_v112 = time.time() - t0

    t1 = time.time()
    df_v108 = generate_v108_standard_events_for_seed(seed)
    t_v108 = time.time() - t1

    out_v112 = out_root / f"atom_introduction_events_v112_seed{seed}.parquet"
    out_v108 = out_root / f"atom_introduction_events_v108_standard_seed{seed}.parquet"
    safe_write_parquet_v112(df_v112, out_v112)
    safe_write_parquet_v112(df_v108, out_v108)

    # bit-identity 用 hash
    def df_hash(df):
        return hashlib.sha256(
            pd.util.hash_pandas_object(df, index=False).values.tobytes()
        ).hexdigest()[:16]

    return {
        "seed": seed,
        "v112_n_events": int(len(df_v112)),
        "v112_n_unique_cids": int(df_v112["source_cid"].nunique()) if not df_v112.empty else 0,
        "v112_t_min": int(df_v112["timestamp"].min()) if not df_v112.empty else 0,
        "v112_t_max": int(df_v112["timestamp"].max()) if not df_v112.empty else 0,
        "v112_Q_pre_mean": float(df_v112["Q_pre"].mean()) if not df_v112.empty else 0.0,
        "v112_C_pre_mean": float(df_v112["C_pre"].mean()) if not df_v112.empty else 0.0,
        "v112_n_reserved": int((df_v112["reserved_label"] == RESERVED_LABEL).sum()) if not df_v112.empty else 0,
        "v108_n_events": int(len(df_v108)),
        "v108_n_unique_cids": int(df_v108["source_cid"].nunique()) if not df_v108.empty else 0,
        "v108_n_reserved": int((df_v108["reserved_label"] == RESERVED_LABEL).sum()) if not df_v108.empty else 0,
        "v112_size_mb": round(out_v112.stat().st_size / 1024 / 1024, 4),
        "v108_size_mb": round(out_v108.stat().st_size / 1024 / 1024, 4),
        "v112_hash": df_hash(df_v112),
        "v108_hash": df_hash(df_v108),
        "v112_elapsed_sec": round(t_v112, 2),
        "v108_elapsed_sec": round(t_v108, 2),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke",
                    help="smoke = seed 0 のみ、main = 24 seeds")
    ap.add_argument("--seeds", default=None,
                    help="Comma-separated seed list (override mode default)")
    args = ap.parse_args()

    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",")]
    else:
        seeds = [0] if args.mode == "smoke" else SEEDS

    t0 = time.time()
    print("=" * 72)
    print(f"v10.12 Step D: v112_atom_event_generator  mode={args.mode}")
    print(f"  v112: 受容 cid × 25 atom (target_step + atom_idx × 10 burst)")
    print(f"  v108_standard: v108 既存 main 流用 + Step C metadata 付与")
    print(f"  Q_COST={Q_COST}, C_GAIN={C_GAIN}, ATOM_OFFSET={ATOM_INDEX_STEP_OFFSET}")
    print("=" * 72)

    summaries = []
    for seed in seeds:
        s = process_seed(seed, args.mode)
        summaries.append(s)
        print(f"  seed={seed:2d}: v112={s['v112_n_events']:5d} events "
              f"({s['v112_n_unique_cids']:3d} cids), "
              f"v108_std={s['v108_n_events']:5d} events "
              f"({s['v108_n_unique_cids']:3d} cids), "
              f"v112_hash={s['v112_hash']}, "
              f"v112_t={s['v112_elapsed_sec']}s, v108_t={s['v108_elapsed_sec']}s")

    df_sum = pd.DataFrame(summaries)
    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    df_sum.to_parquet(out_root / f"atom_event_run_summary_{args.mode}.parquet", index=False)

    # 集計
    print(f"\n=== events 集計 ({args.mode}) ===")
    print(f"  v112       total: {df_sum['v112_n_events'].sum():>6d} events / "
          f"{df_sum['v112_n_unique_cids'].sum():>4d} unique cids")
    print(f"  v108_std   total: {df_sum['v108_n_events'].sum():>6d} events / "
          f"{df_sum['v108_n_unique_cids'].sum():>4d} unique cids")

    if args.mode == "smoke":
        print(f"\n=== smoke 期待値検証 (seed 0) ===")
        # Step C: seed 0 v112=16 cid, v108_standard=224 cid
        # v112 期待 events = 16 × 25 = 400 (death 制限なしの場合)
        # v108 期待 events = v108 60,000/24 ≈ 2,500、Step C filter で減少
        expected_v112 = 16 * 25
        actual_v112 = df_sum.iloc[0]["v112_n_events"]
        print(f"  v112 期待 (16 × 25): {expected_v112}, 実測: {actual_v112}, "
              f"delta: {actual_v112 - expected_v112}")
        print(f"  v108_std 実測: {df_sum.iloc[0]['v108_n_events']} "
              f"(v108 main 60000/24 = ~2500、Step C filter 後)")

    # メタ情報
    meta = {
        "mode": args.mode,
        "seeds": list(seeds),
        "v112_total_events": int(df_sum["v112_n_events"].sum()),
        "v108_standard_total_events": int(df_sum["v108_n_events"].sum()),
        "Q_COST": Q_COST,
        "C_GAIN": C_GAIN,
        "ATOM_INDEX_STEP_OFFSET": ATOM_INDEX_STEP_OFFSET,
        "N_ATOMS": N_ATOMS,
        "per_seed_summaries": summaries,
    }
    with open(out_root / f"atom_event_run_summary_{args.mode}.json", "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
