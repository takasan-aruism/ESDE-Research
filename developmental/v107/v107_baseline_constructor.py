#!/usr/bin/env python3
"""v10.7 baseline constructor + delta aggregator.

5 種 baseline (緩和定義) の cid 群を抽出し、relation_paths と同一 schema で
出力。さらに各 (event, target_cid, window) で 6 量 delta を集計、
baseline_excess_change を計算。

5 種 baseline (即決事項 §2.5 + §4 緩和定義):
  - unrelated_baseline                          : 弱関係 cid
  - same_step_random_baseline                   : 同 step 動いてる cid
  - matched_baseline                            : 同 n_core/age/final_state
  - same_integration_low_familiarity_baseline   : 同 α/β + fam 下位 25%
  - high_familiarity_outside_integration        : fam 上位 25% + 同 α/β なし

delta 集計:
  - 6 量: delta_Q / delta_C / delta_R_familiarity / delta_n_alphas /
           delta_n_observed / n_pulses_in_window
  - 3 windows: immediate (1-10) / short (10-100) / medium (100-1000)

出力:
  developmental/v107/outputs/{smoke,main}/baselines_with_delta_seed{N}.parquet
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
NET_DIR = DIAG_ROOT / "network"
SAL_DIR = DIAG_ROOT / "salience"

OUT_ROOT = V107_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V106_ROOT))
from v106_post_process import safe_read_csv  # noqa: E402

SEEDS = list(range(24))
TOP_N_PER_BASELINE = 20
WINDOW_DEFS = [
    ("immediate", 1, 10),
    ("short", 10, 100),
    ("medium", 100, 1000),
]
FAM_LOW_THRESHOLD = 5.0  # unrelated 緩和定義


def assert_output_under_v107(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V107_ROOT not in abs_path.parents and abs_path != V107_ROOT:
        raise ValueError(f"Output path {path} not under v107/")


def safe_write_parquet_v107(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v107(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _build_alpha_beta_membership(seed: int) -> dict[int, set[int]]:
    """各 cid の所属 α/β set (run 全体で 1 度でも所属したもの)."""
    out: dict[int, set[int]] = {}
    for fname in ["alpha_lifecycle_log", "beta_lifecycle_log"]:
        df = safe_read_csv(INT_DIR / f"{fname}_seed{seed}.csv")
        df_b = df[df["event_type"] == "birth"]
        for _, r in df_b.iterrows():
            m = str(r.get("member_cids") or "")
            if not m:
                continue
            members = [int(c) for c in m.split("|") if c]
            for c in members:
                out.setdefault(c, set()).update(members)
                out[c].discard(c)
    return out


def _build_fam_strength_table(seed: int) -> pd.DataFrame:
    df = safe_read_csv(NET_DIR / f"fam_edges_seed{seed}.csv")
    if df.empty:
        return pd.DataFrame(columns=["cid_a", "cid_b", "familiarity"])
    a = df[["from", "to", "familiarity"]].rename(
        columns={"from": "cid_a", "to": "cid_b"}
    )
    b = df[["to", "from", "familiarity"]].rename(
        columns={"to": "cid_a", "from": "cid_b"}
    )
    return pd.concat([a, b], ignore_index=True)


def _build_salience_pairs(seed: int) -> set[tuple[int, int]]:
    df = safe_read_csv(SAL_DIR / f"salience_event_log_seed{seed}.csv")
    if df.empty:
        return set()
    df = df.dropna(subset=["observer_cid", "candidate_cid"])
    pairs = set(zip(df["observer_cid"].astype(int),
                      df["candidate_cid"].astype(int)))
    return pairs


def _cid_meta_table(seed: int) -> pd.DataFrame:
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    first_t = df_pulse.groupby("cid")["t"].min().reset_index().rename(
        columns={"cid": "cognitive_id", "t": "birth_step"}
    )
    n_core = df_audit[["cid", "n_core_member"]].rename(
        columns={"cid": "cognitive_id"}
    )
    df = df_subj[["cognitive_id", "final_state", "host_lost_step",
                    "reaped_step", "last_familiarity_max"]].merge(
        n_core, on="cognitive_id", how="left"
    ).merge(first_t, on="cognitive_id", how="left")
    df["birth_step"] = df["birth_step"].fillna(0).astype(int)
    return df


# ----------------------------------------------------------------------
# 5 種 baseline 構築
# ----------------------------------------------------------------------
def build_baselines(seed: int, source_events: pd.DataFrame) -> pd.DataFrame:
    cid_meta = _cid_meta_table(seed)
    all_cids = cid_meta["cognitive_id"].astype(int).tolist()
    membership = _build_alpha_beta_membership(seed)
    fam_table = _build_fam_strength_table(seed)
    fam_strong_neighbors: dict[int, set[int]] = {}
    if not fam_table.empty:
        for cid, sub in fam_table[fam_table["familiarity"] >= FAM_LOW_THRESHOLD].groupby("cid_a"):
            fam_strong_neighbors[int(cid)] = set(sub["cid_b"].astype(int))
    salience_pairs = _build_salience_pairs(seed)

    fam_high = cid_meta["last_familiarity_max"].quantile(0.75)
    fam_low = cid_meta["last_familiarity_max"].quantile(0.25)

    high_fam_set = set(cid_meta[cid_meta["last_familiarity_max"] >= fam_high]["cognitive_id"].astype(int))
    low_fam_set = set(cid_meta[cid_meta["last_familiarity_max"] <= fam_low]["cognitive_id"].astype(int))

    rng = np.random.default_rng(20250507)

    rows = []
    for _, ev in source_events[["event_id", "source_cid", "timestamp"]].iterrows():
        s_cid = int(ev["source_cid"])
        s_ts = int(ev["timestamp"])
        s_meta = cid_meta[cid_meta["cognitive_id"] == s_cid]
        if s_meta.empty:
            continue
        s_n_core = s_meta["n_core_member"].iloc[0] if not pd.isna(
            s_meta["n_core_member"].iloc[0]
        ) else None
        s_final = s_meta["final_state"].iloc[0]
        s_birth = int(s_meta["birth_step"].iloc[0])
        s_age = max(s_ts - s_birth, 1)

        s_strong_fam = fam_strong_neighbors.get(s_cid, set())
        s_groups = membership.get(s_cid, set())

        # 1. unrelated_baseline (緩和定義)
        unrelated = []
        for c in all_cids:
            if c == s_cid:
                continue
            if c in s_strong_fam:  # familiarity 強度 >= 5
                continue
            if c in s_groups:  # 同 α/β 内
                continue
            if (s_cid, c) in salience_pairs or (c, s_cid) in salience_pairs:
                continue
            unrelated.append(c)
        unrelated_top = list(rng.permutation(unrelated))[:TOP_N_PER_BASELINE] if unrelated else []
        for tcid in unrelated_top:
            rows.append({
                "event_id": ev["event_id"], "source_cid": s_cid, "timestamp": s_ts,
                "target_cid": int(tcid), "relation_path_type": "unrelated_baseline",
                "relation_strength": 0.0, "hop_distance": -1,
            })

        # 2. same_step_random_baseline (同 window で動いてる任意 cid)
        s_window = (s_ts // 500) + 19
        same_step_candidates = cid_meta[
            (cid_meta["birth_step"] // 500 + 19 <= s_window) &
            ((cid_meta["host_lost_step"].isna()) |
             (cid_meta["host_lost_step"] // 500 + 19 >= s_window)) &
            (cid_meta["cognitive_id"] != s_cid)
        ]["cognitive_id"].astype(int).tolist()
        same_step_top = list(rng.permutation(same_step_candidates))[:TOP_N_PER_BASELINE] \
            if same_step_candidates else []
        for tcid in same_step_top:
            rows.append({
                "event_id": ev["event_id"], "source_cid": s_cid, "timestamp": s_ts,
                "target_cid": int(tcid), "relation_path_type": "same_step_random_baseline",
                "relation_strength": 0.0, "hop_distance": -1,
            })

        # 3. matched_baseline (同 n_core / age ±20% / 同 final_state)
        if s_n_core is not None:
            age_low = s_age * 0.8
            age_high = s_age * 1.2
            matched = cid_meta[
                (cid_meta["n_core_member"] == s_n_core) &
                (cid_meta["final_state"] == s_final) &
                (cid_meta["cognitive_id"] != s_cid)
            ].copy()
            # age を s_ts 時点で計算
            matched["age_at_event"] = (s_ts - matched["birth_step"]).clip(lower=1)
            matched = matched[(matched["age_at_event"] >= age_low) &
                                (matched["age_at_event"] <= age_high)]
            # 関係なし条件 (緩和)
            matched_clean = []
            for _, m in matched.iterrows():
                c = int(m["cognitive_id"])
                if c in s_strong_fam:
                    continue
                if c in s_groups:
                    continue
                matched_clean.append(c)
            matched_top = list(rng.permutation(matched_clean))[:TOP_N_PER_BASELINE] \
                if matched_clean else []
            for tcid in matched_top:
                rows.append({
                    "event_id": ev["event_id"], "source_cid": s_cid, "timestamp": s_ts,
                    "target_cid": int(tcid), "relation_path_type": "matched_baseline",
                    "relation_strength": 0.0, "hop_distance": -1,
                })

        # 4. same_integration_low_familiarity (同 α/β + fam 下位 25%)
        si_low = [c for c in s_groups if c in low_fam_set]
        si_top = list(rng.permutation(si_low))[:TOP_N_PER_BASELINE] if si_low else []
        for tcid in si_top:
            rows.append({
                "event_id": ev["event_id"], "source_cid": s_cid, "timestamp": s_ts,
                "target_cid": int(tcid),
                "relation_path_type": "same_integration_low_familiarity_baseline",
                "relation_strength": 0.0, "hop_distance": -1,
            })

        # 5. high_familiarity_outside_integration (fam 上位 25% + α/β なし)
        hf_out = [c for c in high_fam_set if c not in s_groups and c != s_cid]
        hf_top = list(rng.permutation(hf_out))[:TOP_N_PER_BASELINE] if hf_out else []
        for tcid in hf_top:
            rows.append({
                "event_id": ev["event_id"], "source_cid": s_cid, "timestamp": s_ts,
                "target_cid": int(tcid),
                "relation_path_type": "high_familiarity_outside_integration_baseline",
                "relation_strength": 0.0, "hop_distance": -1,
            })

    if not rows:
        return pd.DataFrame(columns=[
            "event_id", "source_cid", "timestamp", "target_cid",
            "relation_path_type", "relation_strength", "hop_distance", "seed",
        ])
    df = pd.DataFrame(rows)
    df["seed"] = seed
    return df


# ----------------------------------------------------------------------
# delta 集計
# ----------------------------------------------------------------------
def _build_pulse_window_counts(seed: int) -> pd.DataFrame:
    df = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    return df[["cid", "t"]].rename(columns={"cid": "target_cid", "t": "pulse_t"})


def _build_state_lookups(seed: int):
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_bd = safe_read_csv(BAL_DIR / f"balance_decisions_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_sal = safe_read_csv(SAL_DIR / f"salience_event_log_seed{seed}.csv")

    # cid 単位 sorted timeseries
    pulse_r = df_pulse[["cid", "t", "R_familiarity"]].rename(
        columns={"cid": "target_cid", "t": "ts", "R_familiarity": "R_familiarity"}
    ).sort_values(["target_cid", "ts"]).reset_index(drop=True)

    bd_q = df_bd[["observer_cid", "step", "Q_at_decision", "C_at_decision"]].rename(
        columns={"observer_cid": "target_cid", "step": "ts"}
    ).sort_values(["target_cid", "ts"]).reset_index(drop=True)

    audit_q0 = df_audit[["cid", "v14_q0"]].rename(columns={"cid": "target_cid"})

    # cumulative alpha
    pairs = []
    for _, r in df_alpha[df_alpha["event_type"] == "birth"].iterrows():
        m = str(r.get("member_cids") or "")
        for c in m.split("|"):
            try:
                pairs.append({"target_cid": int(c), "ts": int(r["step"])})
            except ValueError:
                continue
    if pairs:
        df_a_pairs = pd.DataFrame(pairs).sort_values(
            ["target_cid", "ts"]
        ).reset_index(drop=True)
        df_a_pairs["cum_n_alphas"] = df_a_pairs.groupby("target_cid").cumcount() + 1
    else:
        df_a_pairs = pd.DataFrame(columns=["target_cid", "ts", "cum_n_alphas"])

    # cumulative salience observer
    df_sal_clean = df_sal.dropna(subset=["observer_cid"])[["observer_cid", "step"]].rename(
        columns={"observer_cid": "target_cid", "step": "ts"}
    ).copy()
    df_sal_clean["target_cid"] = df_sal_clean["target_cid"].astype(int)
    df_sal_clean["ts"] = df_sal_clean["ts"].astype(int)
    df_sal_clean = df_sal_clean.sort_values(["target_cid", "ts"]).reset_index(drop=True)
    df_sal_clean["cum_n_observed"] = df_sal_clean.groupby("target_cid").cumcount() + 1

    return pulse_r, bd_q, audit_q0, df_a_pairs, df_sal_clean


def _merge_asof_get(left: pd.DataFrame, right: pd.DataFrame, ts_col: str,
                      cols_to_pull: list[str]) -> pd.DataFrame:
    """left の (target_cid, ts_col) に対し right から direction='backward' で取得."""
    if right.empty:
        for c in cols_to_pull:
            left[c] = np.nan
        return left
    left = left.copy()
    left["_orig_idx"] = np.arange(len(left))
    left_sorted = left.sort_values(ts_col, kind="mergesort").reset_index(drop=True)
    right_sub = right[["target_cid", "ts"] + cols_to_pull].rename(
        columns={"ts": ts_col}
    ).sort_values(ts_col, kind="mergesort").reset_index(drop=True)
    merged = pd.merge_asof(left_sorted, right_sub, on=ts_col, by="target_cid",
                              direction="backward")
    merged = merged.sort_values("_orig_idx").reset_index(drop=True)
    return merged.drop(columns=["_orig_idx"])


def _attach_state_at_t(df: pd.DataFrame, ts_col: str, lookups, audit_q0) -> pd.DataFrame:
    pulse_r, bd_q, _, df_a_pairs, df_sal_clean = lookups
    # R_familiarity
    df = _merge_asof_get(df, pulse_r, ts_col, ["R_familiarity"])
    df = df.rename(columns={"R_familiarity": f"R_fam_at_{ts_col}"})
    df[f"R_fam_at_{ts_col}"] = df[f"R_fam_at_{ts_col}"].fillna(0.0)
    # Q, C from balance_decisions
    df = _merge_asof_get(df, bd_q, ts_col, ["Q_at_decision", "C_at_decision"])
    df = df.rename(columns={"Q_at_decision": f"Q_at_{ts_col}",
                              "C_at_decision": f"C_at_{ts_col}"})
    df[f"Q_at_{ts_col}"] = df[f"Q_at_{ts_col}"].fillna(0.0)
    df[f"C_at_{ts_col}"] = df[f"C_at_{ts_col}"].fillna(0.0)
    # n_alphas cumulative
    df = _merge_asof_get(df, df_a_pairs, ts_col, ["cum_n_alphas"])
    df = df.rename(columns={"cum_n_alphas": f"n_alphas_at_{ts_col}"})
    df[f"n_alphas_at_{ts_col}"] = df[f"n_alphas_at_{ts_col}"].fillna(0).astype(int)
    # n_observed cumulative
    df = _merge_asof_get(df, df_sal_clean, ts_col, ["cum_n_observed"])
    df = df.rename(columns={"cum_n_observed": f"n_observed_at_{ts_col}"})
    df[f"n_observed_at_{ts_col}"] = df[f"n_observed_at_{ts_col}"].fillna(0).astype(int)
    return df


def compute_deltas(seed: int, df_targets: pd.DataFrame) -> pd.DataFrame:
    """各 (event_id, target_cid, window) で 6 量 delta を集計."""
    lookups = _build_state_lookups(seed)
    pulse_r, bd_q, audit_q0, df_a_pairs, df_sal_clean = lookups
    df_pulse_min = _build_pulse_window_counts(seed)
    df_pulse_min["pulse_t"] = df_pulse_min["pulse_t"].astype(int)
    df_pulse_min["target_cid"] = df_pulse_min["target_cid"].astype(int)

    df = df_targets.copy()
    df["target_cid"] = df["target_cid"].astype(int)

    # pre state at timestamp
    df["pre_ts"] = df["timestamp"]
    df = _attach_state_at_t(df, "pre_ts", lookups, audit_q0)

    # post state at each window boundary
    for win_name, low, high in WINDOW_DEFS:
        df[f"post_ts_{win_name}"] = df["timestamp"] + high
        df = _attach_state_at_t(df, f"post_ts_{win_name}", lookups, audit_q0)
        # delta 計算
        df[f"delta_R_familiarity_{win_name}"] = (
            df[f"R_fam_at_post_ts_{win_name}"] - df["R_fam_at_pre_ts"]
        )
        df[f"delta_Q_{win_name}"] = (
            df[f"Q_at_post_ts_{win_name}"] - df["Q_at_pre_ts"]
        )
        df[f"delta_C_{win_name}"] = (
            df[f"C_at_post_ts_{win_name}"] - df["C_at_pre_ts"]
        )
        df[f"delta_n_alphas_{win_name}"] = (
            df[f"n_alphas_at_post_ts_{win_name}"] - df["n_alphas_at_pre_ts"]
        )
        df[f"delta_n_observed_{win_name}"] = (
            df[f"n_observed_at_post_ts_{win_name}"] - df["n_observed_at_pre_ts"]
        )

    # n_pulses_in_window: 各 window で target が発火した pulse 数を集計
    pulse_sorted = df_pulse_min.sort_values(["target_cid", "pulse_t"]).reset_index(drop=True)
    pulse_grouped = pulse_sorted.groupby("target_cid")
    pulse_arrays = {cid: g["pulse_t"].to_numpy() for cid, g in pulse_grouped}

    for win_name, low, high in WINDOW_DEFS:
        col = f"n_pulses_in_window_{win_name}"
        counts = []
        for tcid, ts in zip(df["target_cid"].to_numpy(), df["timestamp"].to_numpy()):
            arr = pulse_arrays.get(int(tcid))
            if arr is None or arr.size == 0:
                counts.append(0)
                continue
            cnt = int(((arr > ts + low - 1) & (arr <= ts + high)).sum())
            counts.append(cnt)
        df[col] = counts

    # drop 補助列
    drop_cols = [c for c in df.columns
                 if c.startswith(("R_fam_at_", "Q_at_", "C_at_",
                                    "n_alphas_at_", "n_observed_at_",
                                    "post_ts_", "pre_ts"))]
    df = df.drop(columns=drop_cols)
    return df


# ----------------------------------------------------------------------
# Excess change 集計 (per source_event x relation_path_type)
# ----------------------------------------------------------------------
def compute_baseline_excess_change(df_with_delta: pd.DataFrame) -> pd.DataFrame:
    delta_cols = [c for c in df_with_delta.columns if c.startswith("delta_")
                    or c.startswith("n_pulses_in_window_")]
    grouped = df_with_delta.groupby(["seed", "event_id", "relation_path_type"])
    rows = []
    for (sd, eid, rpt), sub in grouped:
        row = {"seed": int(sd), "event_id": eid, "relation_path_type": rpt,
               "n_targets": int(len(sub))}
        for col in delta_cols:
            row[f"mean_{col}"] = float(sub[col].mean())
        rows.append(row)
    return pd.DataFrame(rows)


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
    print(f"v10.7 baseline + delta - mode={args.mode}, seeds={seeds}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        if args.mode == "smoke":
            ev_path = SMOKE_ROOT / f"source_events_seed{seed}.parquet"
            rp_path = SMOKE_ROOT / f"relation_paths_seed{seed}.parquet"
        else:
            ev_path = MAIN_ROOT / "source_events" / f"source_events_seed{seed}.parquet"
            rp_path = MAIN_ROOT / "relation_paths" / f"relation_paths_seed{seed}.parquet"
        if not (ev_path.exists() and rp_path.exists()):
            print(f"  WARN: prerequisite outputs missing for seed {seed}")
            continue

        src_ev = pd.read_parquet(ev_path)
        rp = pd.read_parquet(rp_path)

        # 5 種 baseline 構築
        bl = build_baselines(seed, src_ev)
        # relation_paths と統合
        df_all = pd.concat([rp, bl], ignore_index=True, sort=False)

        # delta 集計
        df_with_delta = compute_deltas(seed, df_all)
        out_a = out_root / f"baselines_with_delta_seed{seed}.parquet"
        if args.mode == "main":
            out_a = MAIN_ROOT / "baselines_with_delta" / f"baselines_with_delta_seed{seed}.parquet"
        safe_write_parquet_v107(df_with_delta, out_a)

        # baseline_excess_change 集計
        df_excess = compute_baseline_excess_change(df_with_delta)
        out_b = out_root / f"excess_change_seed{seed}.parquet"
        if args.mode == "main":
            out_b = MAIN_ROOT / "excess_change" / f"excess_change_seed{seed}.parquet"
        safe_write_parquet_v107(df_excess, out_b)

        elapsed = time.time() - ts
        path_counts = df_all["relation_path_type"].value_counts().to_dict()
        size_a = round(out_a.stat().st_size / 1024 / 1024, 2)
        size_b = round(out_b.stat().st_size / 1024 / 1024, 2)
        summary = {
            "seed": seed,
            "n_path_records": int(len(rp)),
            "n_baseline_records": int(len(bl)),
            "n_total_records": int(len(df_all)),
            "n_excess_rows": int(len(df_excess)),
            **{f"n_{k}": int(v) for k, v in path_counts.items()},
            "size_with_delta_mb": size_a,
            "size_excess_mb": size_b,
            "elapsed_sec": round(elapsed, 2),
        }
        print(f"  seed={seed}: total_records={summary['n_total_records']:,} "
              f"(rp={summary['n_path_records']:,}, bl={summary['n_baseline_records']:,}), "
              f"excess_rows={summary['n_excess_rows']:,}, "
              f"size_dat={size_a}MB, size_exc={size_b}MB, elapsed={elapsed:.1f}s")
        summaries.append(summary)

    df_sum = pd.DataFrame(summaries)
    sum_path = out_root / "step_e_run_summary.parquet"
    if args.mode == "main":
        sum_path = MAIN_ROOT / "step_e_run_summary.parquet"
    safe_write_parquet_v107(df_sum, sum_path)
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
