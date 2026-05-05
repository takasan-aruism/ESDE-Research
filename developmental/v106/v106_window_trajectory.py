#!/usr/bin/env python3
"""v10.6 window-level cid trajectory analysis.

Taka 指摘 (2026-05-06) を受け、cid 構造ベクトルを **(cid, window) ペア単位**
で生成し、ライフサイクル中の atom alignment 軌跡を追跡する。

各 (cid, alive window) で 48 次元ベクトルを生成、Atom 325 との cosine 類似度を
計算、各 window で何の atom が rank_1 になるかを軌跡として記録。

時系列ソース:
  - balance/c_trajectory_seed*.csv      C_at_window_end, Q_remaining_at_window_end (alive cid のみ)
  - pulse/pulse_log_seed*.csv           per-pulse の R_familiarity (window 内 max を取る)
  - integration/alpha_lifecycle_log     birth event の member_cids から累積 alpha 加入数
  - integration/beta_lifecycle_log      birth event の member_cids から累積 beta 加入数
  - ingestion/ingestion_events          observer_cid 単位累積
  - audit/per_event_audit               v14_spend_flag 累積 (cumulative q spend events)

軸 7 symmetry のみ run-level 値を全 window で使用 (window 単位 drift 集計が
introspection_log でしか取れず、timestep mapping が必要なため smoke 簡略化)。

出力: outputs/main/window_trajectory/ 配下。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"
SUBJ_DIR = DIAG_ROOT / "subjects"
AUDIT_DIR = DIAG_ROOT / "audit"
BAL_DIR = DIAG_ROOT / "balance"
PULSE_DIR = DIAG_ROOT / "pulse"
INT_DIR = DIAG_ROOT / "integration"
ING_DIR = DIAG_ROOT / "ingestion"

MAIN_ROOT = V106_ROOT / "outputs" / "main"
TRAJ_ROOT = MAIN_ROOT / "window_trajectory"
SMOKE_TRAJ = MAIN_ROOT / "window_trajectory_smoke"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import (  # noqa: E402
    AXES_ORDER,
    safe_read_csv,
    safe_write_csv,
    safe_write_json,
    list_atoms_from_a1_batch,
    _gradient_distribute,
    EPISTEMOLOGICAL_BOUNDARIES,
)

WIN_LEN = 500
RUN_END_STEP = 25000
WINDOW_OFFSET = 19  # window value = step / 500 + 19 (確認済 in c_trajectory)
SEEDS = list(range(24))


def step_to_window(step: float) -> int:
    return int(step // WIN_LEN + WINDOW_OFFSET)


def window_to_step_end(window: int) -> int:
    return int((window - WINDOW_OFFSET) * WIN_LEN)


# ----------------------------------------------------------------------
# Build (cid, window) wide table
# ----------------------------------------------------------------------
def _cumulative_count_by_step(df: pd.DataFrame, cid_col: str, step_col: str,
                                value_name: str) -> pd.DataFrame:
    if df.empty or cid_col not in df.columns or step_col not in df.columns:
        return pd.DataFrame(columns=["cognitive_id", "window", value_name])
    sub = df[[cid_col, step_col]].dropna().copy()
    if sub.empty:
        return pd.DataFrame(columns=["cognitive_id", "window", value_name])
    sub["window"] = sub[step_col].astype(float).floordiv(WIN_LEN).astype(int) + WINDOW_OFFSET
    sub = sub.rename(columns={cid_col: "cognitive_id"})
    grouped = sub.groupby(["cognitive_id", "window"]).size().reset_index(name="_in")
    grouped = grouped.sort_values(["cognitive_id", "window"])
    grouped[value_name] = grouped.groupby("cognitive_id")["_in"].cumsum()
    return grouped[["cognitive_id", "window", value_name]]


def _cumulative_alpha_membership(df_alpha: pd.DataFrame) -> pd.DataFrame:
    df_b = df_alpha[df_alpha["event_type"] == "birth"].copy()
    if df_b.empty:
        return pd.DataFrame(columns=["cognitive_id", "window", "cumulative_n_alphas"])
    df_b["window"] = df_b["step"].astype(float).floordiv(WIN_LEN).astype(int) + WINDOW_OFFSET
    rows: list[dict] = []
    for _, r in df_b.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                rows.append({"cognitive_id": int(c), "window": int(r["window"])})
            except ValueError:
                continue
    if not rows:
        return pd.DataFrame(columns=["cognitive_id", "window", "cumulative_n_alphas"])
    df_pairs = pd.DataFrame(rows)
    grouped = df_pairs.groupby(["cognitive_id", "window"]).size().reset_index(name="_in")
    grouped = grouped.sort_values(["cognitive_id", "window"])
    grouped["cumulative_n_alphas"] = grouped.groupby("cognitive_id")["_in"].cumsum()
    return grouped[["cognitive_id", "window", "cumulative_n_alphas"]]


def build_window_table(seed: int) -> pd.DataFrame:
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_ctraj = safe_read_csv(BAL_DIR / f"c_trajectory_seed{seed}.csv")
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_beta = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    df_ing = safe_read_csv(ING_DIR / f"ingestion_events_seed{seed}.csv")
    df_audit_e = safe_read_csv(AUDIT_DIR / f"per_event_audit_seed{seed}.csv")

    base = df_ctraj.rename(columns={"cid": "cognitive_id"})[
        ["cognitive_id", "window", "step_at_window_end",
         "C_at_window_end", "Q_remaining_at_window_end",
         "n_cognition_in_window", "n_consciousness_in_window"]
    ].copy()

    cid_meta = df_subj[[
        "cognitive_id", "birth_window", "final_state", "host_lost_window",
        "reaped_step", "v99_drift_social_positive", "v99_drift_social_negative",
        "v99_drift_social_neutral", "v99_drift_stability_positive",
        "v99_drift_stability_negative", "v99_drift_stability_neutral",
        "v99_drift_spread_positive", "v99_drift_spread_negative",
        "v99_drift_spread_neutral", "v99_drift_familiarity_positive",
        "v99_drift_familiarity_negative", "v99_drift_familiarity_neutral",
    ]].copy()
    cid_n = df_audit[["cid", "n_core_member", "v14_q0"]].rename(
        columns={"cid": "cognitive_id"}
    )
    base = base.merge(cid_meta, on="cognitive_id", how="left")
    base = base.merge(cid_n, on="cognitive_id", how="left")

    # window 内 max R_familiarity (pulse から)
    fam_w = df_pulse.groupby(["cid", "window"])["R_familiarity"].max().reset_index()
    fam_w = fam_w.rename(columns={"cid": "cognitive_id", "R_familiarity": "window_fam_max"})
    base = base.merge(fam_w, on=["cognitive_id", "window"], how="left")
    base["window_fam_max"] = base["window_fam_max"].fillna(0.0)

    # 累積 pulse_count
    pulse_cum = df_pulse.groupby(["cid", "window"]).size().reset_index(name="_in")
    pulse_cum = pulse_cum.sort_values(["cid", "window"])
    pulse_cum["cumulative_pulse_count"] = pulse_cum.groupby("cid")["_in"].cumsum()
    pulse_cum = pulse_cum.rename(columns={"cid": "cognitive_id"})
    base = base.merge(pulse_cum[["cognitive_id", "window", "cumulative_pulse_count"]],
                       on=["cognitive_id", "window"], how="left")
    base["cumulative_pulse_count"] = base["cumulative_pulse_count"].fillna(method="ffill").fillna(0)

    # 累積 ingestion (observer_cid)
    ing_cum = _cumulative_count_by_step(df_ing, "observer_cid", "step",
                                          "cumulative_n_ingestions")
    base = base.merge(ing_cum, on=["cognitive_id", "window"], how="left")
    base["cumulative_n_ingestions"] = base["cumulative_n_ingestions"].fillna(method="ffill").fillna(0)

    # 累積 q spend events
    df_qe = df_audit_e[df_audit_e.get("v14_spend_flag", False) == True].copy()
    qspend_cum = _cumulative_count_by_step(df_qe, "cid", "step",
                                              "cumulative_q_spend_events")
    base = base.merge(qspend_cum, on=["cognitive_id", "window"], how="left")
    base["cumulative_q_spend_events"] = base["cumulative_q_spend_events"].fillna(method="ffill").fillna(0)

    # 累積 alpha membership
    alpha_cum = _cumulative_alpha_membership(df_alpha)
    base = base.merge(alpha_cum, on=["cognitive_id", "window"], how="left")
    base["cumulative_n_alphas"] = base["cumulative_n_alphas"].fillna(method="ffill").fillna(0)

    # 累積 beta membership
    beta_cum = _cumulative_alpha_membership(df_beta)
    beta_cum = beta_cum.rename(columns={"cumulative_n_alphas": "cumulative_n_betas"})
    base = base.merge(beta_cum, on=["cognitive_id", "window"], how="left")
    base["cumulative_n_betas"] = base["cumulative_n_betas"].fillna(method="ffill").fillna(0)

    # 派生
    base["birth_step"] = base["birth_window"] * WIN_LEN
    base["lifespan_so_far"] = (base["step_at_window_end"] - base["birth_step"]).clip(lower=1)
    base["q_spent_so_far"] = (base["v14_q0"] - base["Q_remaining_at_window_end"]).clip(lower=0)
    base["q_remaining_ratio"] = base["Q_remaining_at_window_end"] / base["v14_q0"].clip(lower=1)
    base["pulse_density_so_far"] = base["cumulative_pulse_count"] / base["lifespan_so_far"]
    base["seed"] = seed
    return base


# ----------------------------------------------------------------------
# Per-axis vectors (window-level)
# ----------------------------------------------------------------------
def temporal_vector_w(lifespan_so_far: float) -> list[float]:
    return _gradient_distribute(lifespan_so_far,
                                  [100, 500, 2000, 5000, 10000, 15000], 7)


def scale_vector_w(n_core: float) -> list[float]:
    levels = [0.0] * 6
    if pd.isna(n_core):
        levels[0] = 1.0
        return levels
    n = int(round(n_core))
    if n <= 2:
        levels[0] = 1.0
    elif n == 3:
        levels[1] = 1.0
    elif n == 4:
        levels[2] = 1.0
    elif n == 5:
        levels[3] = 1.0
    elif n == 6:
        levels[4] = 1.0
    else:
        levels[5] = 1.0
    return levels


def epistemological_vector_w(window_fam_max: float) -> list[float]:
    val = window_fam_max if not pd.isna(window_fam_max) else 0.0
    return _gradient_distribute(float(val), EPISTEMOLOGICAL_BOUNDARIES, 5)


def ontological_vector_w(row: pd.Series, seed_max: dict) -> list[float]:
    q0 = max(float(row.get("v14_q0", 0) or 0), 1.0)
    material = float(row.get("Q_remaining_at_window_end", 0) or 0) / q0
    informational = float(row.get("cumulative_pulse_count", 0) or 0) / max(
        seed_max.get("cumulative_pulse_max", 1), 1
    )
    relational = float(row.get("cumulative_n_alphas", 0) or 0) / max(
        seed_max.get("cumulative_n_alphas_max", 1), 1
    )
    n_core = row.get("n_core_member")
    if pd.isna(n_core):
        n_core = 0
    structural = float(n_core) / 7.0
    semantic = float(row.get("C_at_window_end", 0) or 0) / max(
        seed_max.get("C_max_seed", 1), 1
    )
    raw = [material, informational, relational, structural, semantic]
    raw = [max(0.0, min(1.0, v)) for v in raw]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [0.2] * 5


def interconnection_vector_w(n_alphas_so_far: float) -> list[float]:
    return _gradient_distribute(float(n_alphas_so_far or 0), [1.5, 5.5, 20.5, 50.5], 5)


def resonance_vector_w(c_value: float) -> list[float]:
    return _gradient_distribute(float(c_value or 0), [5, 15, 30], 4)


def symmetry_vector_w(row: pd.Series) -> list[float]:
    """run-level v99_drift_* を全 window で共用 (smoke 簡略)."""
    axes = ["social", "stability", "spread", "familiarity"]

    def _to_int(v):
        if pd.isna(v) or v == "unformed":
            return 0
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    pos_count = sum(_to_int(row.get(f"v99_drift_{ax}_positive")) for ax in axes)
    neg_count = sum(_to_int(row.get(f"v99_drift_{ax}_negative")) for ax in axes)
    neu_count = sum(_to_int(row.get(f"v99_drift_{ax}_neutral")) for ax in axes)
    total = pos_count + neg_count + neu_count
    if total == 0:
        return [0.0, 0.0, 1.0, 0.0, 0.0]
    pos_ratio = pos_count / total
    neg_ratio = neg_count / total
    neu_ratio = neu_count / total
    cyclical = min(pos_ratio, neg_ratio) * 2.0
    levels = [
        max(0.0, neg_ratio - 0.5) * 2.0,
        max(0.0, neg_ratio - 0.3) * 0.5,
        neu_ratio,
        max(0.0, pos_ratio - 0.3) * 0.5,
        cyclical,
    ]
    s = sum(levels)
    if s > 0:
        return [v / s for v in levels]
    return [0.0, 0.0, 1.0, 0.0, 0.0]


def lawfulness_vector_w(pulse_density: float) -> list[float]:
    return _gradient_distribute(float(pulse_density or 0),
                                  [0.005, 0.02, 0.05], 4)


def experience_vector_w(row: pd.Series) -> list[float]:
    discovery = float(row.get("cumulative_n_ingestions", 0) or 0)
    creation = float(row.get("n_consciousness_in_window", 0) or 0)
    comprehension = float(row.get("cumulative_pulse_count", 0) or 0)
    raw = [discovery, creation, comprehension]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]


def value_generation_vector_w(row: pd.Series, seed_max: dict) -> list[float]:
    q0 = max(float(row.get("v14_q0", 0) or 0), 1.0)
    functional = float(row.get("q_spent_so_far", 0) or 0) / q0
    aesthetic = float(row.get("cumulative_n_ingestions", 0) or 0) / max(
        seed_max.get("cumulative_n_ingestions_max", 1), 1
    )
    ethical = float(row.get("cumulative_n_betas", 0) or 0) / max(
        seed_max.get("cumulative_n_betas_max", 1), 1
    )
    sacred = float(row.get("cumulative_n_betas", 0) or 0) / max(
        seed_max.get("cumulative_n_betas_max", 1), 1
    )
    raw = [functional, aesthetic, ethical, sacred]
    raw = [max(0.0, min(1.0, v)) for v in raw]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [0.25] * 4


def build_window_cid_vector(row: pd.Series, seed_max: dict) -> np.ndarray:
    parts: list[float] = []
    parts.extend(temporal_vector_w(row["lifespan_so_far"]))
    parts.extend(scale_vector_w(row["n_core_member"]))
    parts.extend(epistemological_vector_w(row["window_fam_max"]))
    parts.extend(ontological_vector_w(row, seed_max))
    parts.extend(interconnection_vector_w(row["cumulative_n_alphas"]))
    parts.extend(resonance_vector_w(row["C_at_window_end"]))
    parts.extend(symmetry_vector_w(row))
    parts.extend(lawfulness_vector_w(row["pulse_density_so_far"]))
    parts.extend(experience_vector_w(row))
    parts.extend(value_generation_vector_w(row, seed_max))
    if len(parts) != 48:
        raise RuntimeError(f"window vec dim != 48: {len(parts)}")
    return np.array(parts, dtype=np.float32)


def compute_seed_max_w(df: pd.DataFrame) -> dict:
    return {
        "cumulative_pulse_max": float(df["cumulative_pulse_count"].max() or 1),
        "cumulative_n_alphas_max": float(df["cumulative_n_alphas"].max() or 1),
        "cumulative_n_betas_max": float(df["cumulative_n_betas"].max() or 1),
        "cumulative_n_ingestions_max": float(df["cumulative_n_ingestions"].max() or 1),
        "C_max_seed": float(df["C_at_window_end"].max() or 1),
    }


# ----------------------------------------------------------------------
# Trajectory analysis per seed
# ----------------------------------------------------------------------
def run_seed_trajectory(seed: int, atom_names: list[str],
                          atom_profiles: np.ndarray, atom_valid: np.ndarray,
                          out_root: Path) -> dict:
    df_w = build_window_table(seed)
    seed_max = compute_seed_max_w(df_w)

    vectors = np.vstack([build_window_cid_vector(r, seed_max) for _, r in df_w.iterrows()])

    valid_idx = np.where(atom_valid)[0]
    sim = np.full((vectors.shape[0], atom_profiles.shape[0]), np.nan, dtype=np.float32)
    if valid_idx.size:
        sim_valid = cosine_similarity(vectors, atom_profiles[valid_idx])
        sim[:, valid_idx] = sim_valid.astype(np.float32)

    cids = df_w["cognitive_id"].astype(int).tolist()
    windows = df_w["window"].astype(int).tolist()

    rank1_idx = np.argmax(np.where(np.isnan(sim), -np.inf, sim), axis=1)
    rank1_atoms = [atom_names[i] for i in rank1_idx]
    rank1_sims = sim[np.arange(sim.shape[0]), rank1_idx]
    valid_max = np.where(np.isnan(sim), -np.inf, sim).max(axis=1)
    valid_mean = np.nanmean(sim, axis=1)

    df_out = pd.DataFrame({
        "seed": seed,
        "cognitive_id": cids,
        "window": windows,
        "step_at_window_end": df_w["step_at_window_end"].tolist(),
        "lifespan_so_far": df_w["lifespan_so_far"].tolist(),
        "n_core_member": df_w["n_core_member"].tolist(),
        "final_state": df_w["final_state"].tolist(),
        "C_at_window_end": df_w["C_at_window_end"].tolist(),
        "Q_remaining_at_window_end": df_w["Q_remaining_at_window_end"].tolist(),
        "cumulative_n_alphas": df_w["cumulative_n_alphas"].tolist(),
        "cumulative_n_betas": df_w["cumulative_n_betas"].tolist(),
        "window_fam_max": df_w["window_fam_max"].tolist(),
        "rank_1_atom": rank1_atoms,
        "rank_1_sim": rank1_sims,
        "max_sim": valid_max,
        "mean_sim": valid_mean,
        "top_category": [a.split(".")[0] for a in rank1_atoms],
    })

    safe_write_csv(df_out, out_root / f"window_cid_alignment_seed{seed}.csv")

    # Per-cid trajectory pattern
    pat_rows = []
    for cid, sub in df_out.groupby("cognitive_id"):
        sub = sub.sort_values("window")
        n_windows = len(sub)
        atoms_seq = sub["rank_1_atom"].tolist()
        cats_seq = sub["top_category"].tolist()
        n_unique_atoms = len(set(atoms_seq))
        n_unique_cats = len(set(cats_seq))
        if n_windows == 1:
            traj_class = "snapshot_only"
        elif n_unique_atoms == 1:
            traj_class = "stable_atom"
        elif n_unique_cats == 1:
            traj_class = "stable_category"
        elif n_unique_atoms == n_windows:
            traj_class = "fully_drifting"
        elif n_unique_atoms <= 3:
            traj_class = "few_attractors"
        else:
            traj_class = "wandering"
        pat_rows.append({
            "seed": seed, "cognitive_id": cid, "n_windows": n_windows,
            "n_unique_atoms": n_unique_atoms, "n_unique_categories": n_unique_cats,
            "trajectory_class": traj_class,
            "first_atom": atoms_seq[0], "last_atom": atoms_seq[-1],
            "first_category": cats_seq[0], "last_category": cats_seq[-1],
            "all_atoms_seq": "|".join(atoms_seq),
            "max_sim_max": float(sub["max_sim"].max()),
            "max_sim_mean": float(sub["max_sim"].mean()),
            "max_sim_min": float(sub["max_sim"].min()),
        })
    df_traj = pd.DataFrame(pat_rows)
    safe_write_csv(df_traj, out_root / f"trajectory_patterns_seed{seed}.csv")

    # Window-level rank_1 atom distribution
    win_rows = []
    for w, sub in df_out.groupby("window"):
        atom_counts = sub["rank_1_atom"].value_counts()
        cat_counts = sub["top_category"].value_counts()
        top5 = atom_counts.head(5).items()
        row = {
            "seed": seed, "window": int(w),
            "step_at_window_end": int(window_to_step_end(int(w))),
            "n_alive_cids": len(sub),
            "max_sim_mean": float(sub["max_sim"].mean()),
            "max_sim_median": float(sub["max_sim"].median()),
            "top_category": cat_counts.index[0] if len(cat_counts) else None,
            "top_category_count": int(cat_counts.iloc[0]) if len(cat_counts) else 0,
        }
        for i, (atom, cnt) in enumerate(top5, start=1):
            row[f"rank_{i}_atom"] = atom
            row[f"rank_{i}_count"] = int(cnt)
        win_rows.append(row)
    df_win = pd.DataFrame(win_rows)
    safe_write_csv(df_win, out_root / f"window_rank1_distribution_seed{seed}.csv")

    return {
        "seed": seed,
        "n_window_cid_pairs": int(len(df_out)),
        "n_alive_cids": int(df_out["cognitive_id"].nunique()),
        "n_windows_observed": int(df_out["window"].nunique()),
        "max_sim_mean": float(df_out["max_sim"].mean()),
        "n_unique_rank1_atoms": int(df_out["rank_1_atom"].nunique()),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_TRAJ if args.mode == "smoke" else TRAJ_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.6 window trajectory - mode={args.mode}, seeds={seeds}")

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)
    print(f"  atoms: total={len(atom_names)}, valid={int(atom_valid.sum())}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        s = run_seed_trajectory(seed, atom_names, atom_profiles, atom_valid, out_root)
        s["elapsed_sec"] = round(time.time() - ts, 2)
        print(f"  seed={seed}: pairs={s['n_window_cid_pairs']}, "
              f"alive_cids={s['n_alive_cids']}, windows={s['n_windows_observed']}, "
              f"max_sim_mean={s['max_sim_mean']:.4f}, "
              f"unique_rank1={s['n_unique_rank1_atoms']}, "
              f"elapsed={s['elapsed_sec']}s")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_csv(df_sum, out_root / "trajectory_run_summary.csv")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
