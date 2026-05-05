#!/usr/bin/env python3
"""v10.6 per-pulse cid trajectory analysis.

window 単位 trajectory (500 step/window) より 10x 細かい解像度で
cid のライフサイクル中の atom alignment を追跡する。

pulse_log を主データソース、各 pulse 行から (cid, t) の cid 状態を
直接抽出し 48 次元ベクトルを生成。pulse は cid 状態が変化する瞬間そのもの。

軸 7 symmetry は per-pulse の delta_* sign で動学化 (window 版の run-level
共用簡略を解消)。

入力:
  - pulse/pulse_log_seed*.csv          per-pulse (theta_*, R_*, delta_*, v11_*)
  - subjects/per_subject_seed*.csv     cid meta (birth_window, final_state)
  - audit/per_subject_audit_seed*.csv  n_core_member, v14_q0
  - balance/c_trajectory_seed*.csv     window-level C, Q_remaining (補完)
  - integration/{alpha,beta}_lifecycle_log_seed*.csv  累積 membership
  - ingestion/ingestion_events_seed*.csv               累積 ingestion

出力: outputs/main/pulse_trajectory{,_smoke}/
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
PULSE_TRAJ = MAIN_ROOT / "pulse_trajectory"
SMOKE_PULSE = MAIN_ROOT / "pulse_trajectory_smoke"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import (  # noqa: E402
    safe_read_csv,
    safe_write_csv,
    list_atoms_from_a1_batch,
    _gradient_distribute,
    EPISTEMOLOGICAL_BOUNDARIES,
)

WIN_LEN = 500
SEEDS = list(range(24))
DELTA_EPS = 1e-3


# ----------------------------------------------------------------------
# Build (cid, pulse) wide table via merge_asof
# ----------------------------------------------------------------------
def _expand_alpha_membership_to_events(df_alpha: pd.DataFrame) -> pd.DataFrame:
    df_b = df_alpha[df_alpha["event_type"] == "birth"].copy()
    rows: list[dict] = []
    for _, r in df_b.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                rows.append({"cognitive_id": int(c), "t": int(r["step"])})
            except ValueError:
                continue
    if not rows:
        return pd.DataFrame(columns=["cognitive_id", "t", "cum_count"])
    df = pd.DataFrame(rows).sort_values(["cognitive_id", "t"]).reset_index(drop=True)
    df["cum_count"] = df.groupby("cognitive_id").cumcount() + 1
    return df


def _cumulative_events_by_cid_step(df: pd.DataFrame, cid_col: str,
                                     step_col: str) -> pd.DataFrame:
    if df.empty or cid_col not in df.columns or step_col not in df.columns:
        return pd.DataFrame(columns=["cognitive_id", "t", "cum_count"])
    sub = df[[cid_col, step_col]].dropna().copy()
    if sub.empty:
        return pd.DataFrame(columns=["cognitive_id", "t", "cum_count"])
    sub.columns = ["cognitive_id", "t"]
    sub["cognitive_id"] = sub["cognitive_id"].astype(int)
    sub["t"] = sub["t"].astype(int)
    sub = sub.sort_values(["cognitive_id", "t"]).reset_index(drop=True)
    sub["cum_count"] = sub.groupby("cognitive_id").cumcount() + 1
    return sub


def _merge_cumulative(base: pd.DataFrame, cum: pd.DataFrame,
                       new_col_name: str) -> pd.DataFrame:
    if cum.empty:
        base[new_col_name] = 0
        return base
    base = base.copy()
    base["_orig_idx"] = np.arange(len(base))
    base_sorted = base.sort_values("t", kind="mergesort").reset_index(drop=True)
    cum_sorted = cum.sort_values("t", kind="mergesort").reset_index(drop=True)
    cum_sorted = cum_sorted.rename(columns={"cum_count": new_col_name})
    merged = pd.merge_asof(
        base_sorted, cum_sorted, on="t", by="cognitive_id", direction="backward",
    )
    merged = merged.sort_values("_orig_idx").reset_index(drop=True)
    merged = merged.drop(columns=["_orig_idx"])
    merged[new_col_name] = merged[new_col_name].fillna(0).astype(int)
    return merged


def build_pulse_table(seed: int) -> pd.DataFrame:
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_ctraj = safe_read_csv(BAL_DIR / f"c_trajectory_seed{seed}.csv")
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_beta = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    df_ing = safe_read_csv(ING_DIR / f"ingestion_events_seed{seed}.csv")
    df_audit_e = safe_read_csv(AUDIT_DIR / f"per_event_audit_seed{seed}.csv")

    base = df_pulse.rename(columns={"cid": "cognitive_id"}).copy()

    cid_meta = df_subj[["cognitive_id", "birth_window", "final_state",
                         "host_lost_step", "reaped_step"]]
    cid_n = df_audit[["cid", "n_core_member", "v14_q0"]].rename(
        columns={"cid": "cognitive_id"}
    )
    base = base.merge(cid_meta, on="cognitive_id", how="left")
    base = base.merge(cid_n, on="cognitive_id", how="left")
    base["birth_step"] = base["birth_window"] * WIN_LEN
    base["lifespan_so_far"] = (base["t"] - base["birth_step"]).clip(lower=1)

    # window 単位 C, Q_remaining を pulse の window で merge
    ctraj_subset = df_ctraj.rename(columns={"cid": "cognitive_id"})[
        ["cognitive_id", "window", "C_at_window_end", "Q_remaining_at_window_end"]
    ]
    base = base.merge(ctraj_subset, on=["cognitive_id", "window"], how="left")

    # ffill within cid (前 window までの最新値で補完)
    base = base.sort_values(["cognitive_id", "t"]).reset_index(drop=True)
    base["C_at_window_end"] = base.groupby("cognitive_id")["C_at_window_end"].ffill().fillna(0)
    base["Q_remaining_at_window_end"] = base.groupby("cognitive_id")["Q_remaining_at_window_end"].ffill()
    base["Q_remaining_at_window_end"] = base["Q_remaining_at_window_end"].fillna(base["v14_q0"])
    base["q_spent_so_far"] = (base["v14_q0"] - base["Q_remaining_at_window_end"]).clip(lower=0)

    # cumulative pulse count (= pulse_n column already)
    base["cumulative_pulse_count"] = base["pulse_n"]
    base["pulse_density_so_far"] = base["cumulative_pulse_count"] / base["lifespan_so_far"]

    # cumulative ingestion (observer_cid)
    ing_cum = _cumulative_events_by_cid_step(df_ing, "observer_cid", "step")
    base = _merge_cumulative(base, ing_cum, "cumulative_n_ingestions")

    # cumulative q_spend events
    df_qe = df_audit_e[df_audit_e.get("v14_spend_flag", False) == True]
    qe_cum = _cumulative_events_by_cid_step(df_qe, "cid", "step")
    base = _merge_cumulative(base, qe_cum, "cumulative_q_spend_events")

    # cumulative alpha / beta membership
    alpha_cum = _expand_alpha_membership_to_events(df_alpha)
    base = _merge_cumulative(base, alpha_cum, "cumulative_n_alphas")
    beta_cum = _expand_alpha_membership_to_events(df_beta)
    base = _merge_cumulative(base, beta_cum, "cumulative_n_betas")

    base["seed"] = seed
    return base


# ----------------------------------------------------------------------
# Per-pulse vector builders
# ----------------------------------------------------------------------
def temporal_vec(lifespan: float) -> list[float]:
    return _gradient_distribute(lifespan, [100, 500, 2000, 5000, 10000, 15000], 7)


def scale_vec(n_core: float) -> list[float]:
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


def epistemological_vec(r_familiarity: float) -> list[float]:
    val = float(r_familiarity) if not pd.isna(r_familiarity) else 0.0
    return _gradient_distribute(val, EPISTEMOLOGICAL_BOUNDARIES, 5)


def ontological_vec(row: pd.Series, seed_max: dict) -> list[float]:
    q0 = max(float(row.get("v14_q0", 0) or 0), 1.0)
    material = float(row.get("Q_remaining_at_window_end", 0) or 0) / q0
    informational = float(row.get("cumulative_pulse_count", 0) or 0) / max(
        seed_max.get("cumulative_pulse_max", 1), 1
    )
    relational = float(row.get("cumulative_n_alphas", 0) or 0) / max(
        seed_max.get("cumulative_n_alphas_max", 1), 1
    )
    n_core = row.get("n_core_member")
    structural = float(0 if pd.isna(n_core) else n_core) / 7.0
    semantic = float(row.get("C_at_window_end", 0) or 0) / max(
        seed_max.get("C_max_seed", 1), 1
    )
    raw = [material, informational, relational, structural, semantic]
    raw = [max(0.0, min(1.0, v)) for v in raw]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [0.2] * 5


def interconnection_vec(n_alphas_so_far: float) -> list[float]:
    return _gradient_distribute(float(n_alphas_so_far or 0), [1.5, 5.5, 20.5, 50.5], 5)


def resonance_vec(c_value: float) -> list[float]:
    return _gradient_distribute(float(c_value or 0), [5, 15, 30], 4)


def symmetry_vec_pulse(row: pd.Series) -> list[float]:
    """この pulse の delta_* 直接利用、動学的 symmetry."""
    axes = ["social", "stability", "spread", "familiarity"]
    deltas = [row.get(f"delta_{ax}", 0) for ax in axes]
    deltas = [0.0 if pd.isna(d) else float(d) for d in deltas]
    pos = sum(1 for d in deltas if d > DELTA_EPS)
    neg = sum(1 for d in deltas if d < -DELTA_EPS)
    neu = 4 - pos - neg
    if pos + neg + neu == 0:
        return [0.0, 0.0, 1.0, 0.0, 0.0]
    pos_ratio = pos / 4.0
    neg_ratio = neg / 4.0
    neu_ratio = neu / 4.0
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


def lawfulness_vec(pulse_density: float) -> list[float]:
    return _gradient_distribute(float(pulse_density or 0), [0.005, 0.02, 0.05], 4)


def experience_vec(row: pd.Series) -> list[float]:
    discovery = float(row.get("cumulative_n_ingestions", 0) or 0)
    creation = float(row.get("cumulative_q_spend_events", 0) or 0)
    comprehension = float(row.get("cumulative_pulse_count", 0) or 0)
    raw = [discovery, creation, comprehension]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]


def value_generation_vec(row: pd.Series, seed_max: dict) -> list[float]:
    q0 = max(float(row.get("v14_q0", 0) or 0), 1.0)
    functional = float(row.get("q_spent_so_far", 0) or 0) / q0
    aesthetic = float(row.get("cumulative_n_ingestions", 0) or 0) / max(
        seed_max.get("cumulative_n_ingestions_max", 1), 1
    )
    ethical = float(row.get("cumulative_n_alphas", 0) or 0) / max(
        seed_max.get("cumulative_n_alphas_max", 1), 1
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


def build_pulse_cid_vector(row: pd.Series, seed_max: dict) -> np.ndarray:
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
        raise RuntimeError(f"pulse vec dim != 48: {len(parts)}")
    return np.array(parts, dtype=np.float32)


def compute_seed_max(df: pd.DataFrame) -> dict:
    return {
        "cumulative_pulse_max": float(df["cumulative_pulse_count"].max() or 1),
        "cumulative_n_alphas_max": float(df["cumulative_n_alphas"].max() or 1),
        "cumulative_n_betas_max": float(df["cumulative_n_betas"].max() or 1),
        "cumulative_n_ingestions_max": float(df["cumulative_n_ingestions"].max() or 1),
        "C_max_seed": float(df["C_at_window_end"].max() or 1),
    }


# ----------------------------------------------------------------------
# Per-seed orchestration
# ----------------------------------------------------------------------
def run_seed_pulse(seed: int, atom_names: list[str], atom_profiles: np.ndarray,
                    atom_valid: np.ndarray, out_root: Path) -> dict:
    df_p = build_pulse_table(seed)
    seed_max = compute_seed_max(df_p)

    # Build vectors via vectorized routes where possible (per-row apply for clarity)
    vecs = np.empty((len(df_p), 48), dtype=np.float32)
    for i, (_, r) in enumerate(df_p.iterrows()):
        vecs[i] = build_pulse_cid_vector(r, seed_max)

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
        "cognitive_id": df_p["cognitive_id"].astype(int).tolist(),
        "t": df_p["t"].astype(int).tolist(),
        "window": df_p["window"].astype(int).tolist(),
        "pulse_n": df_p["pulse_n"].astype(int).tolist(),
        "trigger": df_p["trigger"].astype(str).tolist(),
        "v11_captured": df_p["v11_captured"].astype(str).tolist(),
        "n_core_member": df_p["n_core_member"].astype(str).tolist(),
        "lifespan_so_far": df_p["lifespan_so_far"].tolist(),
        "C_at_window_end": df_p["C_at_window_end"].tolist(),
        "Q_remaining_at_window_end": df_p["Q_remaining_at_window_end"].tolist(),
        "R_familiarity": df_p["R_familiarity"].tolist(),
        "cumulative_n_alphas": df_p["cumulative_n_alphas"].tolist(),
        "cumulative_n_betas": df_p["cumulative_n_betas"].tolist(),
        "rank_1_atom": rank1_atoms,
        "rank_1_sim": rank1_sims,
        "top_category": [a.split(".")[0] for a in rank1_atoms],
    })

    safe_write_csv(df_out, out_root / f"pulse_cid_alignment_seed{seed}.csv")

    # per-cid trajectory pattern (atoms across pulses)
    pat_rows = []
    for cid, sub in df_out.groupby("cognitive_id"):
        sub = sub.sort_values("pulse_n")
        n_pulses = len(sub)
        atoms_seq = sub["rank_1_atom"].tolist()
        cats_seq = sub["top_category"].tolist()
        n_unique_atoms = len(set(atoms_seq))
        n_unique_cats = len(set(cats_seq))
        if n_pulses == 1:
            traj_class = "single_pulse"
        elif n_unique_atoms == 1:
            traj_class = "stable_atom"
        elif n_unique_cats == 1:
            traj_class = "stable_category"
        elif n_unique_atoms <= 3:
            traj_class = "few_attractors"
        elif n_unique_atoms / n_pulses > 0.7:
            traj_class = "fully_drifting"
        else:
            traj_class = "wandering"
        pat_rows.append({
            "seed": seed, "cognitive_id": cid, "n_pulses": n_pulses,
            "n_unique_atoms": n_unique_atoms, "n_unique_categories": n_unique_cats,
            "trajectory_class": traj_class,
            "first_atom": atoms_seq[0], "last_atom": atoms_seq[-1],
            "first_category": cats_seq[0], "last_category": cats_seq[-1],
            "rank1_sim_mean": float(sub["rank_1_sim"].mean()),
            "rank1_sim_max": float(sub["rank_1_sim"].max()),
            "rank1_sim_min": float(sub["rank_1_sim"].min()),
        })
    df_traj = pd.DataFrame(pat_rows)
    safe_write_csv(df_traj, out_root / f"pulse_trajectory_patterns_seed{seed}.csv")

    # trigger-by-atom rank_1 distribution
    trig_rows = []
    for trigger, sub in df_out.groupby("trigger"):
        cnt = sub["rank_1_atom"].value_counts()
        for atom, c in cnt.head(10).items():
            trig_rows.append({"seed": seed, "trigger": trigger,
                               "rank_1_atom": atom, "count": int(c),
                               "ratio_within_trigger": c / len(sub)})
    df_trig = pd.DataFrame(trig_rows)
    safe_write_csv(df_trig, out_root / f"pulse_trigger_atom_distribution_seed{seed}.csv")

    return {
        "seed": seed,
        "n_pulse_records": int(len(df_out)),
        "n_alive_cids": int(df_out["cognitive_id"].nunique()),
        "rank_1_sim_mean": float(df_out["rank_1_sim"].mean()),
        "n_unique_rank1_atoms": int(df_out["rank_1_atom"].nunique()),
        "n_distinct_triggers": int(df_out["trigger"].nunique()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_PULSE if args.mode == "smoke" else PULSE_TRAJ
    out_root.mkdir(parents=True, exist_ok=True)

    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.6 per-pulse trajectory - mode={args.mode}, seeds={seeds}")

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)
    print(f"  atoms: total={len(atom_names)}, valid={int(atom_valid.sum())}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        s = run_seed_pulse(seed, atom_names, atom_profiles, atom_valid, out_root)
        s["elapsed_sec"] = round(time.time() - ts, 2)
        print(f"  seed={seed}: pulses={s['n_pulse_records']}, "
              f"alive_cids={s['n_alive_cids']}, "
              f"rank1_sim_mean={s['rank_1_sim_mean']:.4f}, "
              f"unique_rank1={s['n_unique_rank1_atoms']}, "
              f"triggers={s['n_distinct_triggers']}, "
              f"elapsed={s['elapsed_sec']}s")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_csv(df_sum, out_root / "pulse_trajectory_run_summary.csv")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
