#!/usr/bin/env python3
"""v10.11 q_c_inherited observer (within-cid design、Step B/C 実装).

q_c_inherited event を起点とした member cid の応答性プロファイル取得:
  - 主軸: q_c_inherited 前後の delta_C (within-cid 前後比較)
  - 条件軸 1: n_core_bin (bin_2 / bin_3_4 / bin_5+)
  - 条件軸 2: β 累積 c_inherited 分位 (Q1: <3 / Q2: 3-6 / Q3: 6-9 / Q4: ≥10)
  - 観察対象: q_c_inherited を受けた cid のみ (within-cid design)
  - 観察解像度: t_offset 5 step 刻み、±50 step (21 samples)

機構: post-process、ledger 改変なし、物理層 frozen 維持。
v10.7 既存 source_event を read のみ、v107 lookup 機構を最小流用。

出力:
  developmental/v111/outputs/{smoke,main}/
    q_c_inherited_response_profile_seed{N}.parquet
    q_c_inherited_events_seed{N}.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V111_ROOT = (REPO_ROOT / "developmental" / "v111").resolve()
DIAG = V105_ROOT / "diag_v105_main_v2"

OUT_ROOT = V111_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V107_ROOT))
from v107_baseline_constructor import _cid_meta_table  # noqa: E402

SEEDS = list(range(24))
T_OFFSETS = list(range(-50, 51, 5))  # -50, -45, ..., +50 (21 samples)
RUN_END = 25000


def assert_output_under_v111(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V111_ROOT not in abs_path.parents and abs_path != V111_ROOT:
        raise ValueError(f"Output path {path} not under v111/")


def safe_write_parquet_v111(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v111(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def n_core_bin(n: int) -> str:
    if n <= 2:
        return "bin_2"
    if n <= 4:
        return "bin_3_4"
    return "bin_5plus"


def cumc_q(c: float) -> str:
    if c < 3:
        return "Q1"
    if c < 6:
        return "Q2"
    if c < 9:
        return "Q3"
    return "Q4"


def build_c_value_lookup(seed: int) -> pd.DataFrame:
    """balance_decisions を global_step ベースで結合し、cid 別の C 値時系列を構築."""
    bd = pd.read_csv(DIAG / f"balance/balance_decisions_seed{seed}.csv", low_memory=False)
    df = bd[["observer_cid", "global_step", "C_at_decision", "Q_at_decision"]].copy()
    df = df.rename(columns={"observer_cid": "cid", "global_step": "ts"})
    df = df.dropna(subset=["cid", "ts"])
    df["cid"] = df["cid"].astype(int)
    df["ts"] = df["ts"].astype(int)
    df = df.sort_values(["cid", "ts"]).reset_index(drop=True)
    return df


def build_pulse_lookup(seed: int) -> pd.DataFrame:
    """pulse_log を cid 別 sorted で構築 (time-window count に使う)."""
    pl = pd.read_csv(DIAG / f"pulse/pulse_log_seed{seed}.csv")
    df = pl[["cid", "t"]].copy()
    df["cid"] = df["cid"].astype(int)
    df["t"] = df["t"].astype(int)
    return df.sort_values(["cid", "t"]).reset_index(drop=True)


def get_c_at_step(c_lookup: pd.DataFrame, cid: int, t: int) -> float:
    """cid の C 値を時刻 t で取得 (merge_asof backward 相当)."""
    sub = c_lookup[c_lookup["cid"] == cid]
    if sub.empty:
        return float("nan")
    # backward direction: ts <= t の最後の行
    idx = sub["ts"].searchsorted(t, side="right") - 1
    if idx < 0:
        return 0.0  # t 以前にレコードなし、初期値 0 とする
    return float(sub.iloc[idx]["C_at_decision"])


def count_pulses_in_window(p_lookup: pd.DataFrame, cid: int, t_start: int, t_end: int) -> int:
    """cid の pulse 数を [t_start, t_end] で集計."""
    sub = p_lookup[p_lookup["cid"] == cid]
    if sub.empty:
        return 0
    return int(((sub["t"] >= t_start) & (sub["t"] <= t_end)).sum())


def observe_seed(seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """seed 別に q_c_inherited events と response profile を生成."""
    # 1. q_c_inherited events 抽出
    b = pd.read_csv(DIAG / f"integration/beta_lifecycle_log_seed{seed}.csv")
    qci = b[b["event_type"] == "q_c_inherited"].copy()
    if qci.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 2. β 別累積 c_inherited 計算 (event 順)
    qci = qci.sort_values(["beta_id", "step"]).reset_index(drop=True)
    qci["cumulative_c_before_event"] = qci.groupby("beta_id")["c_inherited_delta"].cumsum().shift(fill_value=0)
    # shift で「event 直前まで」の累積、最初の event は 0
    # ただし groupby + shift の組み合わせは β を跨いで shift されないように要注意
    qci["cumulative_c_before_event"] = qci.groupby("beta_id")["c_inherited_delta"].apply(
        lambda x: x.cumsum().shift(fill_value=0)
    ).reset_index(drop=True)
    qci["cumulative_c_after_event"] = qci.groupby("beta_id")["c_inherited_delta"].cumsum()
    qci["c_q_partition"] = qci["cumulative_c_before_event"].apply(cumc_q)
    qci["event_id"] = [f"{seed}_qci_{i}" for i in range(len(qci))]

    # 3. cid features (n_core_bin)
    m = _cid_meta_table(seed)
    nc_lookup = dict(zip(m["cognitive_id"].astype(int),
                            m["n_core_member"].fillna(0).astype(int)))

    # 4. 観察対象 (event, member_cid) ペア生成
    pairs = []
    for _, ev in qci.iterrows():
        mems_str = str(ev.get("member_cids") or "")
        if not mems_str or mems_str == "nan":
            continue
        for c_str in mems_str.split("|"):
            if not c_str.strip():
                continue
            try:
                cid = int(c_str)
            except ValueError:
                continue
            pairs.append({
                "event_id": ev["event_id"],
                "beta_id": int(ev["beta_id"]),
                "step": int(ev["step"]),
                "cid": cid,
                "c_inherited_delta": int(ev["c_inherited_delta"]),
                "cumulative_c_before": int(ev["cumulative_c_before_event"]),
                "c_q_partition": ev["c_q_partition"],
                "n_core": nc_lookup.get(cid, 0),
                "n_core_bin": n_core_bin(nc_lookup.get(cid, 0)),
            })
    df_pairs = pd.DataFrame(pairs)

    # 5. C 値 / pulse 数の lookup 構築
    c_lookup = build_c_value_lookup(seed)
    p_lookup = build_pulse_lookup(seed)

    # 6. each (event, cid) × t_offset で snapshot
    snapshots = []
    for _, p in df_pairs.iterrows():
        T = p["step"]
        cid = p["cid"]
        for offset in T_OFFSETS:
            t_obs = T + offset
            if t_obs < 0 or t_obs >= RUN_END:
                continue
            c_val = get_c_at_step(c_lookup, cid, t_obs)
            # pulse は [t_obs, t_obs+5) で count (正方向ウィンドウ)
            pulse_n = count_pulses_in_window(p_lookup, cid, t_obs, t_obs + 4)
            snapshots.append({
                "event_id": p["event_id"], "beta_id": p["beta_id"],
                "cid": cid, "T": T, "t_offset": offset, "t_obs": t_obs,
                "C_value": c_val, "pulse_count": pulse_n,
                "n_core": p["n_core"], "n_core_bin": p["n_core_bin"],
                "cumulative_c_before": p["cumulative_c_before"],
                "c_q_partition": p["c_q_partition"],
                "c_inherited_delta": p["c_inherited_delta"],
            })
    df_snapshots = pd.DataFrame(snapshots)
    df_snapshots["seed"] = seed
    qci["seed"] = seed
    return qci, df_snapshots


def _worker(args):
    seed, mode = args
    qci, snap = observe_seed(seed)
    out_root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    if not qci.empty:
        safe_write_parquet_v111(qci, out_root / f"q_c_inherited_events_seed{seed}.parquet")
    if not snap.empty:
        safe_write_parquet_v111(snap, out_root / f"q_c_inherited_response_profile_seed{seed}.parquet")
    return {
        "seed": seed,
        "n_qci_events": int(len(qci)),
        "n_qci_with_member": int(qci["member_cids"].notna().sum()) if not qci.empty else 0,
        "n_snapshots": int(len(snap)),
        "n_unique_cids": int(snap["cid"].nunique()) if not snap.empty else 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS
    n_workers = max(1, min(args.n_workers, len(seeds)))

    print(f"v10.11 q_c_inherited observer - mode={args.mode}, "
          f"seeds={len(seeds)}, n_workers={n_workers}")
    print(f"  T_OFFSETS: {T_OFFSETS} (21 samples, ±50 step, 5 step 刻み)")

    t0 = time.time()
    if n_workers > 1 and len(seeds) > 1:
        with Pool(processes=n_workers) as pool:
            results = pool.map(_worker, [(s, args.mode) for s in seeds])
    else:
        results = [_worker((s, args.mode)) for s in seeds]

    df_sum = pd.DataFrame(results)
    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    safe_write_parquet_v111(df_sum, out_root / "q_c_inherited_run_summary.parquet")

    print(f"\n=== summary ===")
    print(df_sum.to_string(index=False))
    print(f"\n  total qci events: {df_sum['n_qci_events'].sum()}")
    print(f"  total events with member_cids: {df_sum['n_qci_with_member'].sum()}")
    print(f"  total snapshots: {df_sum['n_snapshots'].sum()}")
    print(f"  total unique cids: {df_sum['n_unique_cids'].sum()}")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
