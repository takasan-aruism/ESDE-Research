#!/usr/bin/env python3
"""v10.6 per-event cid trajectory analysis.

step10 (10 step interpolation) では pulse 間冗長サンプリングが発生する。
per-event は **cid 状態が変化する瞬間 (pulse + ingestion + spend + α/β
birth) のみ** を抽出して trajectory を構築。step1 の代わりに event 駆動の
新規 atom 表面化を効率的に検証。

入力:
  - pulse_log_seed{N}.csv          (pulse、cid 状態の主変化)
  - ingestion_events_seed{N}.csv   (observer_cid 単位の ingestion)
  - per_event_audit_seed{N}.csv    (cid 単位の v14_spend_flag=True event)
  - alpha_lifecycle_log_seed{N}.csv (birth event の member_cids 加入)
  - beta_lifecycle_log_seed{N}.csv  (同)
  - per_subject + audit + balance/c_trajectory (補完)

出力: outputs/main/event_trajectory{,_smoke}/
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
EVENT_TRAJ = MAIN_ROOT / "event_trajectory"
SMOKE_EVENT = MAIN_ROOT / "event_trajectory_smoke"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import (  # noqa: E402
    safe_read_csv,
    safe_write_csv,
    list_atoms_from_a1_batch,
)
from v106_pulse_trajectory import (  # noqa: E402
    temporal_vec, scale_vec, epistemological_vec, ontological_vec,
    interconnection_vec, resonance_vec, symmetry_vec_pulse,
    lawfulness_vec, experience_vec, value_generation_vec,
    _expand_alpha_membership_to_events, _cumulative_events_by_cid_step,
)
from v106_step10_trajectory import _merge_asof_by_cid  # noqa: E402

WIN_LEN = 500
RUN_END_STEP = 25000
SEEDS = list(range(24))


def _collect_event_points(seed: int) -> pd.DataFrame:
    """全 event source から (cognitive_id, t, source) を統合."""
    rows: list[pd.DataFrame] = []

    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    if not df_pulse.empty:
        rows.append(df_pulse[["cid", "t"]].rename(columns={"cid": "cognitive_id"}).assign(source="pulse"))

    df_ing = safe_read_csv(ING_DIR / f"ingestion_events_seed{seed}.csv")
    if not df_ing.empty and "observer_cid" in df_ing.columns:
        sub = df_ing.dropna(subset=["observer_cid"])[["observer_cid", "step"]]
        sub = sub.rename(columns={"observer_cid": "cognitive_id", "step": "t"})
        sub["cognitive_id"] = sub["cognitive_id"].astype(int)
        sub["source"] = "ingestion"
        rows.append(sub)

    df_audit_e = safe_read_csv(AUDIT_DIR / f"per_event_audit_seed{seed}.csv")
    if not df_audit_e.empty:
        df_qe = df_audit_e[df_audit_e.get("v14_spend_flag", False) == True]
        if not df_qe.empty:
            sub = df_qe[["cid", "step"]].rename(columns={"cid": "cognitive_id", "step": "t"})
            sub["source"] = "spend"
            rows.append(sub)

    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_b_alpha = df_alpha[df_alpha["event_type"] == "birth"]
    for _, r in df_b_alpha.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                rows.append(pd.DataFrame([{
                    "cognitive_id": int(c), "t": int(r["step"]), "source": "alpha_birth"
                }]))
            except ValueError:
                continue

    df_beta = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    df_b_beta = df_beta[df_beta["event_type"] == "birth"]
    for _, r in df_b_beta.iterrows():
        m = str(r.get("member_cids") or "")
        if not m:
            continue
        for c in m.split("|"):
            try:
                rows.append(pd.DataFrame([{
                    "cognitive_id": int(c), "t": int(r["step"]), "source": "beta_birth"
                }]))
            except ValueError:
                continue

    if not rows:
        return pd.DataFrame(columns=["cognitive_id", "t", "source"])
    df_all = pd.concat(rows, ignore_index=True)
    df_all["cognitive_id"] = df_all["cognitive_id"].astype(int)
    df_all["t"] = df_all["t"].astype(int)

    grouped = df_all.groupby(["cognitive_id", "t"])["source"].agg(
        lambda s: "|".join(sorted(set(s)))
    ).reset_index()
    return grouped.sort_values(["cognitive_id", "t"]).reset_index(drop=True)


def build_event_table(seed: int) -> pd.DataFrame:
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_ctraj = safe_read_csv(BAL_DIR / f"c_trajectory_seed{seed}.csv")
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_beta = safe_read_csv(INT_DIR / f"beta_lifecycle_log_seed{seed}.csv")
    df_ing = safe_read_csv(ING_DIR / f"ingestion_events_seed{seed}.csv")
    df_audit_e = safe_read_csv(AUDIT_DIR / f"per_event_audit_seed{seed}.csv")

    base = _collect_event_points(seed)
    if base.empty:
        return base

    cid_meta = df_subj[[
        "cognitive_id", "birth_window", "final_state",
        "host_lost_step", "reaped_step",
    ]].copy()
    cid_n = df_audit[["cid", "n_core_member", "v14_q0"]].rename(
        columns={"cid": "cognitive_id"}
    )
    cid_meta = cid_meta.merge(cid_n, on="cognitive_id", how="left")
    first_pulse_t = (df_pulse.groupby("cid")["t"].min().reset_index()
                       .rename(columns={"cid": "cognitive_id", "t": "first_pulse_t"}))
    cid_meta = cid_meta.merge(first_pulse_t, on="cognitive_id", how="left")
    cid_meta["birth_step"] = cid_meta["first_pulse_t"].fillna(0).astype(int)

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


def build_event_cid_vector(row: pd.Series, seed_max: dict) -> np.ndarray:
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
        raise RuntimeError(f"event vec dim != 48: {len(parts)}")
    return np.array(parts, dtype=np.float32)


def compute_seed_max(df: pd.DataFrame) -> dict:
    return {
        "cumulative_pulse_max": float(df["cumulative_pulse_count"].max() or 1),
        "cumulative_n_alphas_max": float(df["cumulative_n_alphas"].max() or 1),
        "cumulative_n_betas_max": float(df["cumulative_n_betas"].max() or 1),
        "cumulative_n_ingestions_max": float(df["cumulative_n_ingestions"].max() or 1),
        "C_max_seed": float(df["C_at_window_end"].max() or 1),
    }


def run_seed_event(seed: int, atom_names: list[str], atom_profiles: np.ndarray,
                     atom_valid: np.ndarray, out_root: Path) -> dict:
    df = build_event_table(seed)
    if df.empty:
        return {"seed": seed, "n_records": 0}
    seed_max = compute_seed_max(df)

    vecs = np.empty((len(df), 48), dtype=np.float32)
    for i, (_, r) in enumerate(df.iterrows()):
        vecs[i] = build_event_cid_vector(r, seed_max)

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
        "source": df["source"].tolist(),
        "window": df["window"].astype(int).tolist(),
        "lifespan_so_far": df["lifespan_so_far"].tolist(),
        "n_core_member": df["n_core_member"].astype(str).tolist(),
        "C_at_window_end": df["C_at_window_end"].tolist(),
        "Q_remaining_at_window_end": df["Q_remaining_at_window_end"].tolist(),
        "R_familiarity": df["R_familiarity"].tolist(),
        "cumulative_n_ingestions": df["cumulative_n_ingestions"].tolist(),
        "cumulative_n_alphas": df["cumulative_n_alphas"].tolist(),
        "cumulative_n_betas": df["cumulative_n_betas"].tolist(),
        "rank_1_atom": rank1_atoms,
        "rank_1_sim": rank1_sims,
        "top_category": [a.split(".")[0] for a in rank1_atoms],
    })
    safe_write_csv(df_out, out_root / f"event_cid_alignment_seed{seed}.csv")

    src_rows = []
    for src, sub in df_out.groupby("source"):
        cnt = sub["rank_1_atom"].value_counts()
        for atom, c in cnt.head(10).items():
            src_rows.append({
                "seed": seed, "source": src, "rank_1_atom": atom,
                "count": int(c), "ratio_within_source": c / len(sub),
            })
    df_src = pd.DataFrame(src_rows)
    safe_write_csv(df_src, out_root / f"event_source_atom_distribution_seed{seed}.csv")

    return {
        "seed": seed,
        "n_records": int(len(df_out)),
        "n_alive_cids": int(df_out["cognitive_id"].nunique()),
        "rank_1_sim_mean": float(df_out["rank_1_sim"].mean()),
        "n_unique_rank1_atoms": int(df_out["rank_1_atom"].nunique()),
        "n_distinct_sources": int(df_out["source"].nunique()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_EVENT if args.mode == "smoke" else EVENT_TRAJ
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.6 per-event trajectory - mode={args.mode}, seeds={seeds}")

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)
    print(f"  atoms: total={len(atom_names)}, valid={int(atom_valid.sum())}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        s = run_seed_event(seed, atom_names, atom_profiles, atom_valid, out_root)
        s["elapsed_sec"] = round(time.time() - ts, 2)
        print(f"  seed={seed}: records={s['n_records']}, "
              f"alive_cids={s.get('n_alive_cids', 0)}, "
              f"rank1_sim_mean={s.get('rank_1_sim_mean', 0):.4f}, "
              f"unique_rank1={s.get('n_unique_rank1_atoms', 0)}, "
              f"sources={s.get('n_distinct_sources', 0)}, "
              f"elapsed={s['elapsed_sec']}s")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_csv(df_sum, out_root / "event_trajectory_run_summary.csv")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
