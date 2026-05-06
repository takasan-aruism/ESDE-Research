#!/usr/bin/env python3
"""v10.6 per-event trajectory cross-seed analysis + baseline z-score."""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V106_ROOT = REPO_ROOT / "developmental" / "v106"
EVENT_TRAJ = V106_ROOT / "outputs" / "main" / "event_trajectory"
STEP10_TRAJ = V106_ROOT / "outputs" / "main" / "step10_trajectory"
PULSE_TRAJ = V106_ROOT / "outputs" / "main" / "pulse_trajectory"
WINDOW_TRAJ = V106_ROOT / "outputs" / "main" / "window_trajectory"
MAIN_ROOT = V106_ROOT / "outputs" / "main"

sys.path.insert(0, str(Path(__file__).parent))
from v106_post_process import safe_write_csv  # noqa: E402
from v106_baseline_analysis import generate_uniform_cid_vector, cosine_matrix  # noqa: E402

SEEDS = list(range(24))
BASELINE_SEED = 1106
STEP_BIN_SIZE = 1000


def load_concat(prefix: str, root: Path) -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        p = root / f"{prefix}_seed{s}.csv"
        if p.exists():
            dfs.append(pd.read_csv(p))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def cross_seed_atom(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["rank_1_atom"].value_counts()
    rows = []
    for atom, cnt in counts.items():
        sub = df[df["rank_1_atom"] == atom]
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "n_records": int(cnt), "ratio_overall": cnt / len(df),
            "n_seeds_appeared": int(sub["seed"].nunique()),
            "n_unique_cids": int(sub["cognitive_id"].nunique()),
            "rank_1_sim_mean": float(sub["rank_1_sim"].mean()),
            "rank_1_sim_max": float(sub["rank_1_sim"].max()),
        })
    return pd.DataFrame(rows).sort_values("n_records", ascending=False)


def cross_seed_source_atom(df: pd.DataFrame) -> pd.DataFrame:
    """source 別の rank_1 atom 集計 (24 seeds 統合)."""
    rows = []
    for source, sub in df.groupby("source"):
        n = len(sub)
        atom_cnt = sub["rank_1_atom"].value_counts()
        for atom, cnt in atom_cnt.head(10).items():
            rows.append({
                "source": source, "n_pulses_total": int(n),
                "rank_1_atom": atom, "category": atom.split(".")[0],
                "count": int(cnt), "ratio_within_source": cnt / n,
                "n_seeds_appeared": int(sub[sub["rank_1_atom"] == atom]["seed"].nunique()),
            })
    return pd.DataFrame(rows)


def cross_seed_step_evolution(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["step_bin"] = (df["t"] // STEP_BIN_SIZE).astype(int)
    rows = []
    for sb, sub in df.groupby("step_bin"):
        cat_counts = Counter(sub["top_category"])
        atom_counts = Counter(sub["rank_1_atom"])
        most_cat, most_cat_n = cat_counts.most_common(1)[0]
        most_atom, most_atom_n = atom_counts.most_common(1)[0]
        seed_unanimity = sum(
            1 for s in SEEDS
            if (sub[sub["seed"] == s]["top_category"] == most_cat).any()
        )
        rows.append({
            "step_bin": int(sb),
            "step_low": int(sb * STEP_BIN_SIZE),
            "n_records": int(len(sub)),
            "dominant_category": most_cat,
            "dominant_category_count": most_cat_n,
            "dominant_category_seed_unanimity": seed_unanimity,
            "dominant_atom": most_atom,
            "dominant_atom_count": most_atom_n,
            "rank_1_sim_mean": float(sub["rank_1_sim"].mean()),
        })
    return pd.DataFrame(rows).sort_values("step_bin")


def all_resolution_compare(df_event: pd.DataFrame, df_step10: pd.DataFrame,
                              df_pulse: pd.DataFrame, df_window: pd.DataFrame) -> pd.DataFrame:
    e_counts = df_event["rank_1_atom"].value_counts()
    s_counts = df_step10["rank_1_atom"].value_counts() if not df_step10.empty else pd.Series()
    p_counts = df_pulse["rank_1_atom"].value_counts() if not df_pulse.empty else pd.Series()
    w_counts = df_window["rank_1_atom"].value_counts() if not df_window.empty else pd.Series()
    all_atoms = sorted(set(e_counts.index) | set(s_counts.index) |
                         set(p_counts.index) | set(w_counts.index))
    e_total = len(df_event)
    s_total = len(df_step10) if not df_step10.empty else 1
    p_total = len(df_pulse) if not df_pulse.empty else 1
    w_total = len(df_window) if not df_window.empty else 1
    rows = []
    for atom in all_atoms:
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "event_count": int(e_counts.get(atom, 0)),
            "event_ratio": e_counts.get(atom, 0) / e_total,
            "step10_count": int(s_counts.get(atom, 0)),
            "step10_ratio": s_counts.get(atom, 0) / s_total,
            "pulse_count": int(p_counts.get(atom, 0)),
            "pulse_ratio": p_counts.get(atom, 0) / p_total,
            "window_count": int(w_counts.get(atom, 0)),
            "window_ratio": w_counts.get(atom, 0) / w_total,
        })
    return pd.DataFrame(rows).sort_values("event_count", ascending=False)


def event_baseline_z_score(df_event: pd.DataFrame, atom_names: list[str],
                             atom_profiles: np.ndarray, atom_valid: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(BASELINE_SEED)
    per_seed_dfs = []
    for s in SEEDS:
        df_obs = df_event[df_event["seed"] == s]
        n_records = len(df_obs)
        if n_records == 0:
            continue
        uni_mat = np.vstack([generate_uniform_cid_vector(rng) for _ in range(n_records)])
        valid_idx = np.where(atom_valid)[0]
        sim = np.full((n_records, atom_profiles.shape[0]), np.nan, dtype=np.float32)
        sim[:, valid_idx] = cosine_matrix(uni_mat, atom_profiles[valid_idx]).astype(np.float32)
        rank1 = np.argmax(np.where(np.isnan(sim), -np.inf, sim), axis=1)
        uni_atoms = [atom_names[i] for i in rank1]

        obs_counts = df_obs["rank_1_atom"].value_counts().to_dict()
        uni_counts = pd.Series(uni_atoms).value_counts().to_dict()

        rows = []
        for i, atom in enumerate(atom_names):
            if not atom_valid[i]:
                continue
            obs_cnt = int(obs_counts.get(atom, 0))
            uni_cnt = int(uni_counts.get(atom, 0))
            rows.append({
                "seed": s, "atom": atom, "category": atom.split(".")[0],
                "n_records_seed": n_records,
                "obs_rank1_ratio": obs_cnt / n_records,
                "uni_baseline_rank1_ratio": uni_cnt / n_records,
            })
        per_seed_dfs.append(pd.DataFrame(rows))

    df_all = pd.concat(per_seed_dfs, ignore_index=True)
    rows_z = []
    for atom, sub in df_all.groupby("atom"):
        obs = sub["obs_rank1_ratio"].to_numpy()
        uni = sub["uni_baseline_rank1_ratio"].to_numpy()
        obs_mean = float(obs.mean())
        uni_mean = float(uni.mean())
        uni_std = float(uni.std(ddof=0))
        delta = obs_mean - uni_mean
        z = delta / uni_std if uni_std > 0 else (
            np.inf if delta > 0 else (-np.inf if delta < 0 else 0)
        )
        rows_z.append({
            "atom": atom, "category": atom.split(".")[0],
            "obs_rank1_ratio_mean": obs_mean,
            "uni_baseline_rank1_ratio_mean": uni_mean,
            "delta_ratio": delta, "z_score_uniform": z,
            "n_seeds_obs_appeared": int((obs > 0).sum()),
        })
    df_atom_z = pd.DataFrame(rows_z).sort_values("z_score_uniform", ascending=False)

    rows_cat = []
    for cat, sub in df_atom_z.groupby("category"):
        obs_total = float(sub["obs_rank1_ratio_mean"].sum())
        uni_total = float(sub["uni_baseline_rank1_ratio_mean"].sum())
        delta = obs_total - uni_total
        n_above = int((sub["delta_ratio"] > 0).sum())
        n_below = int((sub["delta_ratio"] < 0).sum())
        rows_cat.append({
            "category": cat, "n_atoms": int(len(sub)),
            "obs_total_ratio_mean": obs_total,
            "uni_baseline_total_ratio_mean": uni_total,
            "delta_ratio": delta,
            "n_atoms_above_baseline": n_above,
            "n_atoms_below_baseline": n_below,
        })
    df_cat_z = pd.DataFrame(rows_cat).sort_values("delta_ratio", ascending=False)
    return df_atom_z, df_cat_z


def main() -> None:
    print("v10.6 per-event trajectory cross-seed + baseline z-score")
    df_e = load_concat("event_cid_alignment", EVENT_TRAJ)
    df_s = load_concat("step10_cid_alignment", STEP10_TRAJ)
    df_p = load_concat("pulse_cid_alignment", PULSE_TRAJ)
    df_w = load_concat("window_cid_alignment", WINDOW_TRAJ)

    print(f"  event records: {len(df_e)}, step10: {len(df_s)}, "
          f"pulse: {len(df_p)}, window: {len(df_w)}")

    cache = np.load(MAIN_ROOT / "atom_profiles_cache.npz", allow_pickle=False)
    atom_names = [str(s) for s in cache["atom_names"]]
    atom_profiles = cache["profiles"].astype(np.float32)
    atom_valid = cache["valid_mask"].astype(bool)

    EVENT_TRAJ.mkdir(parents=True, exist_ok=True)

    df_atom = cross_seed_atom(df_e)
    safe_write_csv(df_atom, EVENT_TRAJ / "cross_seed_event_atom_distribution.csv")

    df_src = cross_seed_source_atom(df_e)
    safe_write_csv(df_src, EVENT_TRAJ / "cross_seed_source_atom.csv")

    df_step = cross_seed_step_evolution(df_e)
    safe_write_csv(df_step, EVENT_TRAJ / "cross_seed_event_step_evolution.csv")

    df_cmp = all_resolution_compare(df_e, df_s, df_p, df_w)
    safe_write_csv(df_cmp, EVENT_TRAJ / "cross_seed_all_resolution_compare.csv")

    print("\n=== top 25 atoms (per-event, 24 seeds 統合) ===")
    print(df_atom.head(25).to_string(index=False))

    print("\n=== source 別 atom 比率 (top 3 per source) ===")
    for src, sub in df_src.groupby("source"):
        n = sub["n_pulses_total"].iloc[0]
        top = sub.head(3)
        atoms = ", ".join(f"{r['rank_1_atom']}({r['ratio_within_source']:.0%})"
                            for _, r in top.iterrows())
        print(f"  {src:30s} n={n:6d}: {atoms}")

    print("\n=== step evolution (1000-step bins) ===")
    print(df_step.to_string(index=False))

    df_atom_z, df_cat_z = event_baseline_z_score(df_e, atom_names, atom_profiles, atom_valid)
    safe_write_csv(df_atom_z, EVENT_TRAJ / "cross_seed_event_atom_z_score.csv")
    safe_write_csv(df_cat_z, EVENT_TRAJ / "cross_seed_event_category_z_score.csv")

    print("\n=== category z-score (per-event vs uniform baseline) ===")
    print(df_cat_z.to_string(index=False))

    print("\n=== top 25 atoms above baseline (per-event z-score) ===")
    print(df_atom_z.head(25)[["atom", "category", "obs_rank1_ratio_mean",
                                  "uni_baseline_rank1_ratio_mean", "delta_ratio",
                                  "z_score_uniform"]].to_string(index=False))

    print("\n=== top 15 atoms below baseline ===")
    print(df_atom_z.tail(15).iloc[::-1][["atom", "category", "obs_rank1_ratio_mean",
                                                "uni_baseline_rank1_ratio_mean",
                                                "delta_ratio", "z_score_uniform"]].to_string(index=False))

    print(f"\nDONE  output = {EVENT_TRAJ}")


if __name__ == "__main__":
    main()
