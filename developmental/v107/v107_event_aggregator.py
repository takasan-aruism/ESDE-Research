#!/usr/bin/env python3
"""v10.7 source_event aggregator.

5 種 source_event (pulse / ingestion / alpha_formation / beta_formation /
c_conversion) を統合した DataFrame を構築し、各 event 時点の pre_event_state
を merge_asof で添付する。

設計:
  - 1 source_event = 1 行 (alpha/beta_formation は member_cids 展開で複数行)
  - event_id は (seed, event_source_type, sub_index) で auto-increment
  - pre_event_state は merge_asof による直近値の取得 (forward fill)

入力:
  - pulse/pulse_log_seed*.csv
  - ingestion/ingestion_events_seed*.csv
  - integration/alpha_lifecycle_log_seed*.csv (event_type='birth')
  - integration/beta_lifecycle_log_seed*.csv (event_type='birth')
  - balance/balance_decisions_seed*.csv (decision='consciousness')
  - balance/c_trajectory_seed*.csv (window-level C, Q)
  - audit/per_event_audit_seed*.csv
  - salience/salience_event_log_seed*.csv (n_observed 累積用)

出力 (smoke):
  developmental/v107/outputs/smoke/source_events_seed0.parquet
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
SUBJ_DIR = DIAG_ROOT / "subjects"
AUDIT_DIR = DIAG_ROOT / "audit"
BAL_DIR = DIAG_ROOT / "balance"
PULSE_DIR = DIAG_ROOT / "pulse"
INT_DIR = DIAG_ROOT / "integration"
ING_DIR = DIAG_ROOT / "ingestion"
SAL_DIR = DIAG_ROOT / "salience"

OUT_ROOT = V107_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main" / "source_events"

sys.path.insert(0, str(V106_ROOT))
from v106_post_process import (  # noqa: E402
    safe_read_csv, safe_write_parquet,
    assert_input_under_v105, assert_output_under_v106,
)

SEEDS = list(range(24))


def assert_output_under_v107(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V107_ROOT not in abs_path.parents and abs_path != V107_ROOT:
        raise ValueError(f"Output path {path} not under v107/")


def safe_write_parquet_v107(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v107(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# Read 5 source_event types
# ----------------------------------------------------------------------
def _read_pulse_events(seed: int) -> pd.DataFrame:
    df = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    out = pd.DataFrame({
        "event_source_type": "pulse",
        "source_cid": df["cid"].astype(int),
        "timestamp": df["t"].astype(int),
        "ref_index": df.index,
    })
    return out


def _read_ingestion_events(seed: int) -> pd.DataFrame:
    df = safe_read_csv(ING_DIR / f"ingestion_events_seed{seed}.csv")
    df = df.dropna(subset=["observer_cid"])
    out = pd.DataFrame({
        "event_source_type": "ingestion",
        "source_cid": df["observer_cid"].astype(int),
        "timestamp": df["step"].astype(int),
        "ref_index": df.index,
    })
    return out


def _expand_alpha_birth_events(seed: int) -> pd.DataFrame:
    df = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df = df[df["event_type"] == "birth"].copy()
    rows = []
    for _, r in df.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                rows.append({
                    "event_source_type": "alpha_formation",
                    "source_cid": int(c),
                    "timestamp": int(r["step"]),
                    "ref_index": int(r["alpha_id"]),
                })
            except ValueError:
                continue
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["event_source_type", "source_cid", "timestamp", "ref_index"]
    )


def _expand_beta_birth_events(seed: int) -> pd.DataFrame:
    df = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    df = df[df["event_type"] == "birth"].copy()
    rows = []
    for _, r in df.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                rows.append({
                    "event_source_type": "beta_formation",
                    "source_cid": int(c),
                    "timestamp": int(r["step"]),
                    "ref_index": int(r["beta_id"]),
                })
            except ValueError:
                continue
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["event_source_type", "source_cid", "timestamp", "ref_index"]
    )


def _read_c_conversion_events(seed: int) -> pd.DataFrame:
    df = safe_read_csv(BAL_DIR / f"balance_decisions_seed{seed}.csv")
    df = df[df["decision"] == "consciousness"].copy()
    out = pd.DataFrame({
        "event_source_type": "c_conversion",
        "source_cid": df["observer_cid"].astype(int),
        "timestamp": df["step"].astype(int),
        "ref_index": df.index,
    })
    return out


# ----------------------------------------------------------------------
# pre_event_state attachment via merge_asof
# ----------------------------------------------------------------------
def _merge_asof_by_cid(left: pd.DataFrame, right: pd.DataFrame,
                         right_subset: list[str]) -> pd.DataFrame:
    """left の (source_cid, timestamp) に対し right から direction='backward' で取得."""
    if right.empty:
        for c in right_subset:
            if c not in left.columns and c not in ("source_cid", "timestamp"):
                left[c] = np.nan
        return left
    left = left.copy()
    left["_orig_idx"] = np.arange(len(left))
    left_sorted = left.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    right_sorted = right[right_subset].sort_values(
        "timestamp", kind="mergesort"
    ).reset_index(drop=True)
    merged = pd.merge_asof(
        left_sorted, right_sorted,
        on="timestamp", by="source_cid", direction="backward",
    )
    merged = merged.sort_values("_orig_idx").reset_index(drop=True)
    return merged.drop(columns=["_orig_idx"])


def attach_pre_event_state(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """各 source_event 時点の pre_event_state を merge_asof で取得."""
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_ctraj = safe_read_csv(BAL_DIR / f"c_trajectory_seed{seed}.csv")
    df_bd = safe_read_csv(BAL_DIR / f"balance_decisions_seed{seed}.csv")
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_sal = safe_read_csv(SAL_DIR / f"salience_event_log_seed{seed}.csv")

    # birth_step from pulse_log の最初 t (v10.6 step10 で確立した方法)
    first_pulse_t = (df_pulse.groupby("cid")["t"].min().reset_index()
                       .rename(columns={"cid": "source_cid", "t": "birth_step"}))
    df = df.merge(first_pulse_t, on="source_cid", how="left")
    df["birth_step"] = df["birth_step"].fillna(0).astype(int)
    df["lifespan_so_far"] = (df["timestamp"] - df["birth_step"]).clip(lower=1)

    # n_core_member, v14_q0 from audit
    df_n = df_audit[["cid", "n_core_member", "v14_q0"]].rename(
        columns={"cid": "source_cid"}
    )
    df = df.merge(df_n, on="source_cid", how="left")

    # final_state from per_subject
    df_fs = df_subj[["cognitive_id", "final_state", "host_lost_step", "reaped_step"]].rename(
        columns={"cognitive_id": "source_cid"}
    )
    df = df.merge(df_fs, on="source_cid", how="left")

    # R_familiarity_pre: 直近 pulse の R_familiarity
    df_pulse_r = df_pulse[["cid", "t", "R_familiarity"]].rename(
        columns={"cid": "source_cid", "t": "timestamp"}
    )
    df = _merge_asof_by_cid(df, df_pulse_r,
                              ["source_cid", "timestamp", "R_familiarity"])
    df = df.rename(columns={"R_familiarity": "R_familiarity_pre"})
    df["R_familiarity_pre"] = df["R_familiarity_pre"].fillna(0.0)

    # Q_pre from balance_decisions Q_at_decision (per-event)
    df_bd_q = df_bd[["observer_cid", "step", "Q_at_decision"]].rename(
        columns={"observer_cid": "source_cid", "step": "timestamp"}
    )
    df = _merge_asof_by_cid(df, df_bd_q,
                              ["source_cid", "timestamp", "Q_at_decision"])
    df = df.rename(columns={"Q_at_decision": "Q_pre"})
    df["Q_pre"] = df["Q_pre"].fillna(df["v14_q0"]).fillna(0)

    # C_pre from balance_decisions C_at_decision (per-event)
    df_bd_c = df_bd[["observer_cid", "step", "C_at_decision"]].rename(
        columns={"observer_cid": "source_cid", "step": "timestamp"}
    )
    df = _merge_asof_by_cid(df, df_bd_c,
                              ["source_cid", "timestamp", "C_at_decision"])
    df = df.rename(columns={"C_at_decision": "C_pre"})
    df["C_pre"] = df["C_pre"].fillna(0.0)

    # window-level C (補完: per-cid x window)
    df["window_value"] = ((df["timestamp"] // 500) + 19).astype(int)
    df_ct = df_ctraj.rename(columns={"cid": "source_cid", "window": "window_value"})[
        ["source_cid", "window_value", "C_at_window_end", "Q_remaining_at_window_end"]
    ]
    df = df.merge(df_ct, on=["source_cid", "window_value"], how="left")
    df["C_at_window_end"] = df["C_at_window_end"].fillna(0)
    df["Q_remaining_at_window_end"] = df["Q_remaining_at_window_end"].fillna(df["v14_q0"])

    # n_alphas_pre: alpha_lifecycle event-by-event 累積 (v10.6 流用と同じロジック)
    df_a_birth = df_alpha[df_alpha["event_type"] == "birth"].copy()
    pairs = []
    for _, r in df_a_birth.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                pairs.append({"source_cid": int(c), "timestamp": int(r["step"])})
            except ValueError:
                continue
    if pairs:
        df_a_pairs = pd.DataFrame(pairs).sort_values(
            ["source_cid", "timestamp"]
        ).reset_index(drop=True)
        df_a_pairs["cumulative_n_alphas"] = df_a_pairs.groupby("source_cid").cumcount() + 1
        df = _merge_asof_by_cid(df, df_a_pairs,
                                  ["source_cid", "timestamp", "cumulative_n_alphas"])
    else:
        df["cumulative_n_alphas"] = 0
    df["cumulative_n_alphas"] = df["cumulative_n_alphas"].fillna(0).astype(int)
    df = df.rename(columns={"cumulative_n_alphas": "n_alphas_pre"})

    # n_observed_pre: salience event observer 累積
    df_sal_obs = df_sal[["observer_cid", "step"]].rename(
        columns={"observer_cid": "source_cid", "step": "timestamp"}
    ).copy()
    df_sal_obs["source_cid"] = df_sal_obs["source_cid"].astype(int)
    df_sal_obs["timestamp"] = df_sal_obs["timestamp"].astype(int)
    df_sal_obs = df_sal_obs.sort_values(["source_cid", "timestamp"]).reset_index(drop=True)
    df_sal_obs["cumulative_n_observed"] = df_sal_obs.groupby("source_cid").cumcount() + 1
    df = _merge_asof_by_cid(df, df_sal_obs,
                              ["source_cid", "timestamp", "cumulative_n_observed"])
    df["cumulative_n_observed"] = df["cumulative_n_observed"].fillna(0).astype(int)
    df = df.rename(columns={"cumulative_n_observed": "n_observed_pre"})

    return df


# ----------------------------------------------------------------------
# Aggregate all source events for one seed
# ----------------------------------------------------------------------
def aggregate_source_events(seed: int) -> pd.DataFrame:
    parts = [
        _read_pulse_events(seed),
        _read_ingestion_events(seed),
        _expand_alpha_birth_events(seed),
        _expand_beta_birth_events(seed),
        _read_c_conversion_events(seed),
    ]
    df = pd.concat(parts, ignore_index=True, sort=False)
    df["seed"] = seed
    df = df.sort_values(["timestamp", "event_source_type"]).reset_index(drop=True)
    df["event_id"] = np.arange(len(df))
    df["event_id"] = df["seed"].astype(str) + "_" + df["event_id"].astype(str)
    df = attach_pre_event_state(df, seed)
    return df


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--seeds", type=str, default=None)
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    elif args.mode == "smoke":
        seeds = [0]
    else:
        seeds = SEEDS

    print(f"v10.7 source_event aggregator - mode={args.mode}, seeds={seeds}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        df = aggregate_source_events(seed)
        out = out_root / f"source_events_seed{seed}.parquet"
        safe_write_parquet_v107(df, out)
        elapsed = time.time() - ts
        type_counts = df["event_source_type"].value_counts().to_dict()
        summary = {
            "seed": seed, "n_events_total": int(len(df)),
            **{f"n_{k}": int(v) for k, v in type_counts.items()},
            "n_columns": int(len(df.columns)),
            "size_mb": round(out.stat().st_size / 1024 / 1024, 2),
            "elapsed_sec": round(elapsed, 2),
        }
        print(f"  seed={seed}: total={summary['n_events_total']:6d}, "
              f"pulse={summary.get('n_pulse', 0)}, ing={summary.get('n_ingestion', 0)}, "
              f"a_birth={summary.get('n_alpha_formation', 0)}, "
              f"b_birth={summary.get('n_beta_formation', 0)}, "
              f"c_conv={summary.get('n_c_conversion', 0)}, "
              f"size={summary['size_mb']:.2f}MB, elapsed={summary['elapsed_sec']}s")
        summaries.append(summary)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v107(df_sum, out_root / "source_events_run_summary.parquet")
    print(f"\nDONE  total elapsed = {time.time() - t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
