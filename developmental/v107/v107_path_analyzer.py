#!/usr/bin/env python3
"""v10.7 relation_path constructor.

各 source_event について 4 種 relation_path で target_cid を抽出。
matched_baseline は §3.1.5 で baseline 兼用、Step E (baseline_constructor) に
分離する。

4 種 relation_path (Step D 範囲):
  - familiarity            : network/fam_edges_seed*.csv (1-hop)
  - attention_via_salience : salience/salience_event_log_seed*.csv
  - integration            : alpha_lifecycle / beta_lifecycle event-by-event
                             で source_cid 加入時の同 α / β 内 cid
  - temporal_coactivation  : pulse_log time-window (lag ≤ 100 step)

各 path で 1 source_event あたり上位 20 target_cid (relation_strength 順)。
1-hop のみ (multi-hop は Step F)。

入力:
  - 上記の v10.5 出力 + source_events_seed*.parquet (Step C 出力)

出力:
  developmental/v107/outputs/{smoke,main}/relation_paths/
    relation_paths_seed{N}.parquet
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

DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"
PULSE_DIR = DIAG_ROOT / "pulse"
INT_DIR = DIAG_ROOT / "integration"
NET_DIR = DIAG_ROOT / "network"
SAL_DIR = DIAG_ROOT / "salience"

OUT_ROOT = V107_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V106_ROOT))
from v106_post_process import safe_read_csv  # noqa: E402

SEEDS = list(range(24))
TOP_N_PER_PATH = 20
TEMPORAL_LAG_BACKWARD = 100  # source_event 直前 100 step 内に pulse
TEMPORAL_LAG_FORWARD = 100   # 直後 100 step 内


def assert_output_under_v107(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V107_ROOT not in abs_path.parents and abs_path != V107_ROOT:
        raise ValueError(f"Output path {path} not under v107/")


def safe_write_parquet_v107(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v107(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 1. familiarity 経路
# ----------------------------------------------------------------------
def build_familiarity_targets(seed: int, source_events: pd.DataFrame) -> pd.DataFrame:
    df_fam = safe_read_csv(NET_DIR / f"fam_edges_seed{seed}.csv")
    if df_fam.empty:
        return _empty_path_df()
    # from-to を双方向に展開 (familiarity edge は無向グラフ的に扱う)
    fam_a = df_fam.rename(columns={"from": "source_cid", "to": "target_cid"})
    fam_b = df_fam.rename(columns={"to": "source_cid", "from": "target_cid"})
    fam_all = pd.concat([fam_a, fam_b], ignore_index=True)
    fam_all["source_cid"] = fam_all["source_cid"].astype(int)
    fam_all["target_cid"] = fam_all["target_cid"].astype(int)
    # source_cid ごとに strength 上位 N
    fam_all["rank"] = fam_all.groupby("source_cid")["familiarity"].rank(
        method="first", ascending=False
    )
    fam_top = fam_all[fam_all["rank"] <= TOP_N_PER_PATH].copy()
    # source_events と inner join (source_cid 一致)
    src = source_events[["event_id", "source_cid", "timestamp"]]
    out = src.merge(fam_top[["source_cid", "target_cid", "familiarity"]],
                      on="source_cid", how="inner")
    out = out[out["target_cid"] != out["source_cid"]].copy()
    out["relation_path_type"] = "familiarity"
    out["relation_strength"] = out["familiarity"].astype(float)
    out["hop_distance"] = 1
    return out[["event_id", "source_cid", "timestamp", "target_cid",
                  "relation_path_type", "relation_strength", "hop_distance"]]


# ----------------------------------------------------------------------
# 2. attention_via_salience 経路
# ----------------------------------------------------------------------
def build_attention_via_salience_targets(seed: int,
                                            source_events: pd.DataFrame) -> pd.DataFrame:
    df_sal = safe_read_csv(SAL_DIR / f"salience_event_log_seed{seed}.csv")
    if df_sal.empty:
        return _empty_path_df()
    df_sal = df_sal[["observer_cid", "candidate_cid", "step", "candidate_mass"]].dropna()
    df_sal["observer_cid"] = df_sal["observer_cid"].astype(int)
    df_sal["candidate_cid"] = df_sal["candidate_cid"].astype(int)
    df_sal["step"] = df_sal["step"].astype(int)
    # source_cid → candidate_cid の mass 累積 (run 全体の attention 重みとして)
    agg = df_sal.groupby(["observer_cid", "candidate_cid"])["candidate_mass"].sum().reset_index()
    agg = agg.rename(columns={"observer_cid": "source_cid",
                                "candidate_cid": "target_cid",
                                "candidate_mass": "salience_mass_sum"})
    agg["rank"] = agg.groupby("source_cid")["salience_mass_sum"].rank(
        method="first", ascending=False
    )
    agg_top = agg[agg["rank"] <= TOP_N_PER_PATH].copy()

    src = source_events[["event_id", "source_cid", "timestamp"]]
    out = src.merge(agg_top[["source_cid", "target_cid", "salience_mass_sum"]],
                      on="source_cid", how="inner")
    out = out[out["target_cid"] != out["source_cid"]].copy()
    out["relation_path_type"] = "attention_via_salience"
    out["relation_strength"] = out["salience_mass_sum"].astype(float)
    out["hop_distance"] = 1
    return out[["event_id", "source_cid", "timestamp", "target_cid",
                  "relation_path_type", "relation_strength", "hop_distance"]]


# ----------------------------------------------------------------------
# 3. integration 経路
# ----------------------------------------------------------------------
def _expand_birth_event_membership(df_lifecycle: pd.DataFrame,
                                       group_id_col: str) -> pd.DataFrame:
    df_b = df_lifecycle[df_lifecycle["event_type"] == "birth"].copy()
    rows = []
    for _, r in df_b.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        members = [int(c) for c in m.split("|") if c]
        gid = int(r[group_id_col])
        step = int(r["step"])
        for c in members:
            rows.append({"group_id": gid, "cid": c, "step": step,
                          "members_in_group": tuple(members)})
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["group_id", "cid", "step", "members_in_group"]
    )


def build_integration_targets(seed: int, source_events: pd.DataFrame) -> pd.DataFrame:
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_beta = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    a_mem = _expand_birth_event_membership(df_alpha, "alpha_id")
    b_mem = _expand_birth_event_membership(df_beta, "beta_id")
    if a_mem.empty and b_mem.empty:
        return _empty_path_df()
    a_mem["integration_type"] = "alpha"
    b_mem["integration_type"] = "beta"
    mem_all = pd.concat([a_mem, b_mem], ignore_index=True)

    rows = []
    for _, r in source_events[["event_id", "source_cid", "timestamp"]].iterrows():
        joined = mem_all[(mem_all["cid"] == r["source_cid"]) &
                           (mem_all["step"] <= r["timestamp"])]
        for _, gr in joined.iterrows():
            for tcid in gr["members_in_group"]:
                if tcid == r["source_cid"]:
                    continue
                rows.append({
                    "event_id": r["event_id"],
                    "source_cid": r["source_cid"],
                    "timestamp": r["timestamp"],
                    "target_cid": int(tcid),
                    "relation_path_type": f"integration_{gr['integration_type']}",
                    "relation_strength": 1.0,
                    "hop_distance": 1,
                    "integration_group_id": int(gr["group_id"]),
                })
    if not rows:
        return _empty_path_df()
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(["event_id", "target_cid", "relation_path_type"])
    grouped = df.groupby(["event_id", "relation_path_type"])
    df["rank"] = grouped["relation_strength"].rank(method="first", ascending=False)
    df = df[df["rank"] <= TOP_N_PER_PATH].drop(columns=["rank", "integration_group_id"])
    return df[["event_id", "source_cid", "timestamp", "target_cid",
                 "relation_path_type", "relation_strength", "hop_distance"]]


# ----------------------------------------------------------------------
# 4. temporal_coactivation 経路
# ----------------------------------------------------------------------
def build_temporal_coactivation_targets(seed: int,
                                            source_events: pd.DataFrame) -> pd.DataFrame:
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    if df_pulse.empty:
        return _empty_path_df()
    df_pulse_min = df_pulse[["cid", "t"]].rename(
        columns={"cid": "target_cid", "t": "pulse_t"}
    )
    df_pulse_min["target_cid"] = df_pulse_min["target_cid"].astype(int)
    df_pulse_min["pulse_t"] = df_pulse_min["pulse_t"].astype(int)
    df_pulse_min = df_pulse_min.sort_values("pulse_t").reset_index(drop=True)

    rows = []
    src = source_events[["event_id", "source_cid", "timestamp"]].copy()
    src = src.sort_values("timestamp").reset_index(drop=True)
    for _, r in src.iterrows():
        t0 = r["timestamp"] - TEMPORAL_LAG_BACKWARD
        t1 = r["timestamp"] + TEMPORAL_LAG_FORWARD
        # cid != source_cid の pulse を時間窓内で集計
        cand = df_pulse_min[(df_pulse_min["pulse_t"] >= t0) &
                              (df_pulse_min["pulse_t"] <= t1) &
                              (df_pulse_min["target_cid"] != r["source_cid"])].copy()
        if cand.empty:
            continue
        cand["lag"] = cand["pulse_t"] - r["timestamp"]
        cand["abs_lag"] = cand["lag"].abs()
        # cid 単位で min |lag| を取得
        cand_uniq = cand.sort_values("abs_lag").drop_duplicates("target_cid")
        # 上位 N (lag 小さい順)
        cand_top = cand_uniq.head(TOP_N_PER_PATH)
        for _, c in cand_top.iterrows():
            rows.append({
                "event_id": r["event_id"],
                "source_cid": r["source_cid"],
                "timestamp": r["timestamp"],
                "target_cid": int(c["target_cid"]),
                "relation_path_type": "temporal_coactivation",
                "relation_strength": float(1.0 / (1 + c["abs_lag"])),
                "hop_distance": 1,
            })
    if not rows:
        return _empty_path_df()
    return pd.DataFrame(rows)[
        ["event_id", "source_cid", "timestamp", "target_cid",
         "relation_path_type", "relation_strength", "hop_distance"]
    ]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _empty_path_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "event_id", "source_cid", "timestamp", "target_cid",
        "relation_path_type", "relation_strength", "hop_distance",
    ])


def build_all_paths(seed: int, source_events: pd.DataFrame) -> pd.DataFrame:
    fam = build_familiarity_targets(seed, source_events)
    sal = build_attention_via_salience_targets(seed, source_events)
    integ = build_integration_targets(seed, source_events)
    temp = build_temporal_coactivation_targets(seed, source_events)
    df = pd.concat([fam, sal, integ, temp], ignore_index=True)
    df["seed"] = seed
    return df


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT / "relation_paths"
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.7 relation_path constructor - mode={args.mode}, seeds={seeds}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        # source_events を Step C smoke 出力 (seed 0) または Step C main から読む
        if args.mode == "smoke":
            ev_path = SMOKE_ROOT / f"source_events_seed{seed}.parquet"
        else:
            ev_path = MAIN_ROOT / "source_events" / f"source_events_seed{seed}.parquet"
        if not ev_path.exists():
            print(f"  WARN: source_events not found for seed {seed}: {ev_path}")
            continue
        src_ev = pd.read_parquet(ev_path)
        df = build_all_paths(seed, src_ev)
        out = out_root / f"relation_paths_seed{seed}.parquet"
        safe_write_parquet_v107(df, out)
        elapsed = time.time() - ts
        path_counts = df["relation_path_type"].value_counts().to_dict()
        size_mb = round(out.stat().st_size / 1024 / 1024, 2)
        summary = {
            "seed": seed, "n_events": int(len(src_ev)),
            "n_path_records": int(len(df)),
            **{f"n_{k}": int(v) for k, v in path_counts.items()},
            "unique_targets": int(df["target_cid"].nunique()),
            "size_mb": size_mb, "elapsed_sec": round(elapsed, 2),
        }
        print(f"  seed={seed}: events={summary['n_events']}, "
              f"path_records={summary['n_path_records']:,}, "
              f"fam={path_counts.get('familiarity', 0):,} "
              f"att={path_counts.get('attention_via_salience', 0):,} "
              f"i_a={path_counts.get('integration_alpha', 0):,} "
              f"i_b={path_counts.get('integration_beta', 0):,} "
              f"temp={path_counts.get('temporal_coactivation', 0):,}, "
              f"size={size_mb:.2f}MB, elapsed={elapsed:.2f}s")
        summaries.append(summary)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v107(df_sum, out_root / "relation_paths_run_summary.parquet")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
