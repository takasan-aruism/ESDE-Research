#!/usr/bin/env python3
"""v10.6 10-step trajectory analysis.

per-pulse (~50 step 周期) より 5x 細解像度の **10 step 単位** で alive cid の
状態を interpolation 取得、Atom alignment を追跡。

cid 状態は pulse 発生時点で disposition / R が更新され、pulse 間は実質凍結。
ただし event (ingestion / spend / alpha 加入) は連続的に発生するため、
10 step 単位 sampling では「pulse 直後の disposition + 累積 event 増加」
の動学が見える。

入力: pulse_log + per_subject + audit + balance/c_trajectory + alpha/beta_lifecycle
出力: outputs/main/step10_trajectory{,_smoke}/
"""
from __future__ import annotations

import argparse
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
STEP10_TRAJ = MAIN_ROOT / "step10_trajectory"
SMOKE_STEP10 = MAIN_ROOT / "step10_trajectory_smoke"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import (  # noqa: E402
    safe_read_csv,
    safe_write_csv,
    list_atoms_from_a1_batch,
    _gradient_distribute,
    EPISTEMOLOGICAL_BOUNDARIES,
)
from v106_pulse_trajectory import (  # noqa: E402
    temporal_vec, scale_vec, epistemological_vec, ontological_vec,
    interconnection_vec, resonance_vec, symmetry_vec_pulse,
    lawfulness_vec, experience_vec, value_generation_vec,
    _expand_alpha_membership_to_events, _cumulative_events_by_cid_step,
)

WIN_LEN = 500
RUN_END_STEP = 25000
STEP_GRAIN = 10
SEEDS = list(range(24))


def _merge_asof_by_cid(left: pd.DataFrame, right: pd.DataFrame,
                         left_t_col: str = "t",
                         right_t_col: str = "t",
                         right_subset: list[str] | None = None) -> pd.DataFrame:
    """left の (cognitive_id, t) に対し right から direction='backward' で取得."""
    if right.empty:
        return left
    left = left.copy()
    left["_orig_idx"] = np.arange(len(left))
    left_sorted = left.sort_values(left_t_col, kind="mergesort").reset_index(drop=True)
    if right_subset is None:
        right_subset = list(right.columns)
    right_sorted = right[right_subset].sort_values(right_t_col, kind="mergesort").reset_index(drop=True)
    if left_t_col != right_t_col:
        right_sorted = right_sorted.rename(columns={right_t_col: left_t_col})
    merged = pd.merge_asof(
        left_sorted, right_sorted, on=left_t_col, by="cognitive_id",
        direction="backward",
    )
    merged = merged.sort_values("_orig_idx").reset_index(drop=True)
    return merged.drop(columns=["_orig_idx"])


def build_step10_table(seed: int) -> pd.DataFrame:
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_ctraj = safe_read_csv(BAL_DIR / f"c_trajectory_seed{seed}.csv")
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_beta = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    df_ing = safe_read_csv(ING_DIR / f"ingestion_events_seed{seed}.csv")
    df_audit_e = safe_read_csv(AUDIT_DIR / f"per_event_audit_seed{seed}.csv")

    cid_meta = df_subj[[
        "cognitive_id", "birth_window", "final_state",
        "host_lost_step", "reaped_step",
    ]].copy()
    cid_n = df_audit[["cid", "n_core_member", "v14_q0"]].rename(
        columns={"cid": "cognitive_id"}
    )
    cid_meta = cid_meta.merge(cid_n, on="cognitive_id", how="left")
    # birth_step: pulse_log の最初 pulse t を採用 (per_subject.birth_window は
    # window_value の特殊エンコードで誤算しやすいため、実 step から取得)
    first_pulse_t = (df_pulse.groupby("cid")["t"].min().reset_index()
                       .rename(columns={"cid": "cognitive_id", "t": "first_pulse_t"}))
    cid_meta = cid_meta.merge(first_pulse_t, on="cognitive_id", how="left")
    cid_meta["birth_step"] = cid_meta["first_pulse_t"].fillna(0).astype(int)

    def _end_step(row):
        if row["final_state"] == "reaped" and not pd.isna(row.get("reaped_step")):
            return int(row["reaped_step"])
        if row["final_state"] == "ghost":
            v = row.get("reaped_step")
            return int(v) if not pd.isna(v) else RUN_END_STEP
        if not pd.isna(row.get("host_lost_step")):
            return int(row["host_lost_step"])
        return RUN_END_STEP

    cid_meta["end_step"] = cid_meta.apply(_end_step, axis=1)

    rows = []
    for _, r in cid_meta.iterrows():
        birth = int(r["birth_step"])
        end = int(r["end_step"])
        if end <= birth:
            continue
        first_t = ((birth + STEP_GRAIN - 1) // STEP_GRAIN) * STEP_GRAIN
        if first_t == birth:
            first_t = birth + STEP_GRAIN
        for t in range(first_t, end + 1, STEP_GRAIN):
            rows.append({"cognitive_id": int(r["cognitive_id"]), "t": int(t)})
    base = pd.DataFrame(rows)
    if base.empty:
        return base

    base = base.merge(cid_meta[["cognitive_id", "birth_step", "n_core_member",
                                  "v14_q0", "final_state"]],
                        on="cognitive_id", how="left")
    base["window"] = ((base["t"] // WIN_LEN) + 19).astype(int)
    base["lifespan_so_far"] = (base["t"] - base["birth_step"]).clip(lower=1)

    pulse_subset = ["cid", "t", "R_familiarity",
                     "delta_social", "delta_stability", "delta_spread", "delta_familiarity",
                     "trigger", "v11_captured"]
    df_pulse_renamed = df_pulse[pulse_subset].rename(columns={"cid": "cognitive_id"})
    base = _merge_asof_by_cid(base, df_pulse_renamed, "t", "t",
                                right_subset=list(df_pulse_renamed.columns))
    base["R_familiarity"] = base["R_familiarity"].fillna(0)
    for d in ["delta_social", "delta_stability", "delta_spread", "delta_familiarity"]:
        base[d] = base[d].fillna(0)

    ctraj_w = df_ctraj.rename(columns={"cid": "cognitive_id"})[
        ["cognitive_id", "window", "C_at_window_end", "Q_remaining_at_window_end"]
    ]
    base = base.merge(ctraj_w, on=["cognitive_id", "window"], how="left")
    base = base.sort_values(["cognitive_id", "t"]).reset_index(drop=True)
    base["C_at_window_end"] = base.groupby("cognitive_id")["C_at_window_end"].ffill().fillna(0)
    base["Q_remaining_at_window_end"] = base.groupby("cognitive_id")["Q_remaining_at_window_end"].ffill()
    base["Q_remaining_at_window_end"] = base["Q_remaining_at_window_end"].fillna(base["v14_q0"])
    base["q_spent_so_far"] = (base["v14_q0"] - base["Q_remaining_at_window_end"]).clip(lower=0)

    pulse_count_cum = df_pulse[["cid", "t", "pulse_n"]].rename(
        columns={"cid": "cognitive_id", "pulse_n": "cumulative_pulse_count"}
    )
    base = _merge_asof_by_cid(base, pulse_count_cum, "t", "t",
                                right_subset=["cognitive_id", "t",
                                                "cumulative_pulse_count"])
    base["cumulative_pulse_count"] = base["cumulative_pulse_count"].fillna(0).astype(int)
    base["pulse_density_so_far"] = base["cumulative_pulse_count"] / base["lifespan_so_far"]

    ing_cum = _cumulative_events_by_cid_step(df_ing, "observer_cid", "step")
    if not ing_cum.empty:
        ing_cum_r = ing_cum.rename(columns={"cum_count": "cumulative_n_ingestions"})
        base = _merge_asof_by_cid(base, ing_cum_r, "t", "t",
                                    right_subset=["cognitive_id", "t",
                                                    "cumulative_n_ingestions"])
    base["cumulative_n_ingestions"] = base.get(
        "cumulative_n_ingestions", pd.Series([0]*len(base))
    ).fillna(0).astype(int)

    df_qe = df_audit_e[df_audit_e.get("v14_spend_flag", False) == True]
    qe_cum = _cumulative_events_by_cid_step(df_qe, "cid", "step")
    if not qe_cum.empty:
        qe_cum_r = qe_cum.rename(columns={"cum_count": "cumulative_q_spend_events"})
        base = _merge_asof_by_cid(base, qe_cum_r, "t", "t",
                                    right_subset=["cognitive_id", "t",
                                                    "cumulative_q_spend_events"])
    base["cumulative_q_spend_events"] = base.get(
        "cumulative_q_spend_events", pd.Series([0]*len(base))
    ).fillna(0).astype(int)

    alpha_cum = _expand_alpha_membership_to_events(df_alpha)
    if not alpha_cum.empty:
        alpha_cum_r = alpha_cum.rename(columns={"cum_count": "cumulative_n_alphas"})
        base = _merge_asof_by_cid(base, alpha_cum_r, "t", "t",
                                    right_subset=["cognitive_id", "t",
                                                    "cumulative_n_alphas"])
    base["cumulative_n_alphas"] = base.get(
        "cumulative_n_alphas", pd.Series([0]*len(base))
    ).fillna(0).astype(int)

    beta_cum = _expand_alpha_membership_to_events(df_beta)
    if not beta_cum.empty:
        beta_cum_r = beta_cum.rename(columns={"cum_count": "cumulative_n_betas"})
        base = _merge_asof_by_cid(base, beta_cum_r, "t", "t",
                                    right_subset=["cognitive_id", "t",
                                                    "cumulative_n_betas"])
    base["cumulative_n_betas"] = base.get(
        "cumulative_n_betas", pd.Series([0]*len(base))
    ).fillna(0).astype(int)

    base["seed"] = seed
    return base


def build_step10_cid_vector(row: pd.Series, seed_max: dict) -> np.ndarray:
    parts: list[float] = []
    parts.extend(temporal_vec(row["lifespan_so_far"]))
    parts.extend(scale_vec(row["n_core_member"]))
    parts.extend(epistemological_vec(row.get("R_familiarity", 0)))
    parts.extend(ontological_vec(row, seed_max))
    parts.extend(interconnection_vec(row.get("cumulative_n_alphas", 0)))
    parts.extend(resonance_vec(row.get("C_at_window_end", 0)))
    parts.extend(symmetry_vec_pulse(row))
    parts.extend(lawfulness_vec(row.get("pulse_density_so_far", 0)))
    parts.extend(experience_vec(row))
    parts.extend(value_generation_vec(row, seed_max))
    if len(parts) != 48:
        raise RuntimeError(f"step10 vec dim != 48: {len(parts)}")
    return np.array(parts, dtype=np.float32)


def compute_seed_max(df: pd.DataFrame) -> dict:
    return {
        "cumulative_pulse_max": float(df["cumulative_pulse_count"].max() or 1),
        "cumulative_n_alphas_max": float(df["cumulative_n_alphas"].max() or 1),
        "cumulative_n_betas_max": float(df["cumulative_n_betas"].max() or 1),
        "cumulative_n_ingestions_max": float(df["cumulative_n_ingestions"].max() or 1),
        "C_max_seed": float(df["C_at_window_end"].max() or 1),
    }


def run_seed_step10(seed: int, atom_names: list[str], atom_profiles: np.ndarray,
                      atom_valid: np.ndarray, out_root: Path) -> dict:
    df = build_step10_table(seed)
    if df.empty:
        return {"seed": seed, "n_records": 0}
    seed_max = compute_seed_max(df)

    vecs = np.empty((len(df), 48), dtype=np.float32)
    for i, (_, r) in enumerate(df.iterrows()):
        vecs[i] = build_step10_cid_vector(r, seed_max)

    valid_idx = np.where(atom_valid)[0]
    sim = np.full((vecs.shape[0], atom_profiles.shape[0]), np.nan, dtype=np.float32)
    if valid_idx.size:
        sim_valid = cosine_similarity(vecs, atom_profiles[valid_idx])
        sim[:, valid_idx] = sim_valid.astype(np.float32)

    rank1 = np.argmax(np.where(np.isnan(sim), -np.inf, sim), axis=1)
    rank1_atoms = [atom_names[i] for i in rank1]
    rank1_sims = sim[np.arange(sim.shape[0]), rank1]

    df_out = pd.DataFrame({
        "seed": seed,
        "cognitive_id": df["cognitive_id"].astype(int).tolist(),
        "t": df["t"].astype(int).tolist(),
        "window": df["window"].astype(int).tolist(),
        "lifespan_so_far": df["lifespan_so_far"].tolist(),
        "n_core_member": df["n_core_member"].astype(str).tolist(),
        "final_state": df["final_state"].astype(str).tolist(),
        "C_at_window_end": df["C_at_window_end"].tolist(),
        "Q_remaining_at_window_end": df["Q_remaining_at_window_end"].tolist(),
        "R_familiarity": df["R_familiarity"].tolist(),
        "cumulative_pulse_count": df["cumulative_pulse_count"].tolist(),
        "cumulative_n_alphas": df["cumulative_n_alphas"].tolist(),
        "cumulative_n_betas": df["cumulative_n_betas"].tolist(),
        "cumulative_n_ingestions": df["cumulative_n_ingestions"].tolist(),
        "rank_1_atom": rank1_atoms,
        "rank_1_sim": rank1_sims,
        "top_category": [a.split(".")[0] for a in rank1_atoms],
    })

    safe_write_csv(df_out, out_root / f"step10_cid_alignment_seed{seed}.csv")

    pat_rows = []
    for cid, sub in df_out.groupby("cognitive_id"):
        sub = sub.sort_values("t")
        n_records = len(sub)
        atoms_seq = sub["rank_1_atom"].tolist()
        n_unique_atoms = len(set(atoms_seq))
        n_unique_cats = len(set(sub["top_category"]))
        if n_records == 1:
            traj_class = "single_step"
        elif n_unique_atoms == 1:
            traj_class = "stable_atom"
        elif n_unique_cats == 1:
            traj_class = "stable_category"
        elif n_unique_atoms <= 3:
            traj_class = "few_attractors"
        elif n_unique_atoms / n_records > 0.5:
            traj_class = "fully_drifting"
        else:
            traj_class = "wandering"
        pat_rows.append({
            "seed": seed, "cognitive_id": cid, "n_records": n_records,
            "n_unique_atoms": n_unique_atoms, "n_unique_categories": n_unique_cats,
            "trajectory_class": traj_class,
            "first_atom": atoms_seq[0], "last_atom": atoms_seq[-1],
            "rank1_sim_mean": float(sub["rank_1_sim"].mean()),
        })
    df_traj = pd.DataFrame(pat_rows)
    safe_write_csv(df_traj, out_root / f"step10_trajectory_patterns_seed{seed}.csv")

    return {
        "seed": seed,
        "n_records": int(len(df_out)),
        "n_alive_cids": int(df_out["cognitive_id"].nunique()),
        "rank_1_sim_mean": float(df_out["rank_1_sim"].mean()),
        "n_unique_rank1_atoms": int(df_out["rank_1_atom"].nunique()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_STEP10 if args.mode == "smoke" else STEP10_TRAJ
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.6 10-step trajectory - mode={args.mode}, seeds={seeds}")

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)
    print(f"  atoms: total={len(atom_names)}, valid={int(atom_valid.sum())}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        s = run_seed_step10(seed, atom_names, atom_profiles, atom_valid, out_root)
        s["elapsed_sec"] = round(time.time() - ts, 2)
        print(f"  seed={seed}: records={s['n_records']}, "
              f"alive_cids={s.get('n_alive_cids', 0)}, "
              f"rank1_sim_mean={s.get('rank_1_sim_mean', 0):.4f}, "
              f"unique_rank1={s.get('n_unique_rank1_atoms', 0)}, "
              f"elapsed={s['elapsed_sec']}s")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_csv(df_sum, out_root / "step10_trajectory_run_summary.csv")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
