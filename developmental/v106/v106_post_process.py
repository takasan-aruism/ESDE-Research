#!/usr/bin/env python3
"""v10.6 atom_alignment_observer post-process.

Genesis 系 v10.5 出力の cid 5,224 個を 48 次元構造ベクトルに写像し、
Language 系 Atom 326 個 (FND.spaceless 欠で 325 個有効) のプロファイルとの
cosine 類似度を計算する。物理層 frozen は path 縛りで保証 (v105/ は読込専用)。

実装指示書 v106_implementation_brief.md + 差分パッチ #1 反映。
事前分布確認 (2026-05-05) で判明した実態に合わせて以下を調整済:
  - n_core ソースを v11_m_c_n_core (80% 'unformed') から
    audit/per_subject_audit の n_core_member (int) に変更
  - alpha_lifecycle_log.event_type は 'birth' (指示書の 'created' は不在)
  - last_familiarity_max boundaries を実分布 (median 41, max 500) に合わせて
    [10, 30, 60, 150] へ変更
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# ----------------------------------------------------------------------
# Paths (read-only on v105/, write to v106/)
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
OUTPUT_ROOT = V106_ROOT / "outputs"
SMOKE_ROOT = OUTPUT_ROOT / "smoke"
MAIN_ROOT = OUTPUT_ROOT / "main"

DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"
SUBJ_DIR = DIAG_ROOT / "subjects"
WIN_DIR = DIAG_ROOT / "aggregates"
AUDIT_DIR = DIAG_ROOT / "audit"
BAL_DIR = DIAG_ROOT / "balance"
NET_DIR = DIAG_ROOT / "network"
INT_DIR = DIAG_ROOT / "integration"
PULSE_DIR = DIAG_ROOT / "pulse"

LANG_ROOT = REPO_ROOT / "language"
A1_BATCH_DIR = LANG_ROOT / "atoms" / "a1_batch"
MAPPER_DIR = LANG_ROOT / "lexicon" / "data" / "mapper_output"
AXES_DEF = LANG_ROOT / "lexicon" / "data" / "definitions" / "axes_levels_v1.json"

WIN_LEN = 500
RUN_END_STEP = 25000
SEEDS = list(range(24))


def assert_input_under_v105(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V105_ROOT not in abs_path.parents and abs_path != V105_ROOT:
        raise ValueError(f"Input path {path} not under v105/")


def assert_output_under_v106(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V106_ROOT not in abs_path.parents and abs_path != V106_ROOT:
        raise ValueError(f"Output path {path} not under v106/")


def safe_read_csv(path: Path, **kwargs) -> pd.DataFrame:
    assert_input_under_v105(path)
    return pd.read_csv(path, **kwargs)


def safe_write_csv(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v106(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def safe_write_parquet(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v106(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def safe_write_json(obj, path: Path) -> None:
    assert_output_under_v106(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------
# Axes definition (10 axes × 48 levels)
# ----------------------------------------------------------------------
AXES_ORDER: list[tuple[str, list[str]]] = [
    ("temporal",         ["emergence", "indication", "influence", "transformation",
                          "establishment", "continuation", "permanence"]),
    ("scale",            ["individual", "community", "society", "ecosystem",
                          "stellar", "cosmic"]),
    ("epistemological",  ["perception", "identification", "understanding",
                          "experience", "creation"]),
    ("ontological",      ["material", "informational", "relational",
                          "structural", "semantic"]),
    ("interconnection",  ["independent", "catalytic", "chained",
                          "synchronous", "resonant"]),
    ("resonance",        ["superficial", "structural", "essential", "existential"]),
    ("symmetry",         ["destructive", "inclusive", "transformative",
                          "generative", "cyclical"]),
    ("lawfulness",       ["predictable", "emergent", "contingent", "necessary"]),
    ("experience",       ["discovery", "creation", "comprehension"]),
    ("value_generation", ["functional", "aesthetic", "ethical", "sacred"]),
]
N_DIMS = sum(len(levs) for _, levs in AXES_ORDER)
assert N_DIMS == 48, f"Expected 48 dims, got {N_DIMS}"


def axis_dim_ranges() -> dict[str, tuple[int, int]]:
    ranges: dict[str, tuple[int, int]] = {}
    cursor = 0
    for axis, levels in AXES_ORDER:
        ranges[axis] = (cursor, cursor + len(levels))
        cursor += len(levels)
    return ranges


def slot_keys() -> list[str]:
    return [f"{axis}.{lvl}" for axis, levels in AXES_ORDER for lvl in levels]


def verify_axes_match(axes_def_path: Path = AXES_DEF) -> None:
    with open(axes_def_path) as f:
        defs = json.load(f)
    axes_in_file = defs.get("axes", {})
    for axis_name, level_names in AXES_ORDER:
        if axis_name not in axes_in_file:
            raise ValueError(f"Axis '{axis_name}' not in axes_levels_v1.json")
        actual_levels = list(axes_in_file[axis_name].get("levels", {}).keys())
        if actual_levels != level_names:
            raise ValueError(
                f"Axis '{axis_name}' levels mismatch: "
                f"expected {level_names}, got {actual_levels}"
            )
    total = sum(len(v.get("levels", {})) for v in axes_in_file.values())
    if total != 48:
        raise ValueError(f"axes_levels_v1.json total levels = {total}, not 48")
    print("OK  axes_levels_v1.json matches AXES_ORDER (10 axes, 48 levels)")


# ----------------------------------------------------------------------
# Atom enumeration
# ----------------------------------------------------------------------
def list_atoms_from_a1_batch(a1_batch_dir: Path = A1_BATCH_DIR) -> list[str]:
    atoms: list[str] = []
    for fname in sorted(os.listdir(a1_batch_dir)):
        if not fname.endswith(".json") or fname == "_summary.json":
            continue
        stem = fname[:-len(".json")]
        atoms.append(stem.replace("_", ".", 1))
    if len(atoms) != 326:
        raise ValueError(f"Expected 326 atoms in a1_batch/, got {len(atoms)}")
    return atoms


def list_atoms_observed(mapper_dir: Path = MAPPER_DIR) -> list[str]:
    atoms: list[str] = []
    for fname in sorted(os.listdir(mapper_dir)):
        if not fname.endswith("_a1.jsonl"):
            continue
        stem = fname[:-len("_a1.jsonl")]
        atoms.append(stem.replace("_", ".", 1))
    return atoms


def get_unobserved_atoms() -> list[str]:
    return sorted(set(list_atoms_from_a1_batch()) - set(list_atoms_observed()))


# ----------------------------------------------------------------------
# Atom profile (mean-of-normalized over per-word, error rows skipped)
# ----------------------------------------------------------------------
def load_atom_profile(atom_name: str, mapper_dir: Path = MAPPER_DIR) -> Optional[np.ndarray]:
    fname = atom_name.replace(".", "_", 1) + "_a1.jsonl"
    fpath = mapper_dir / fname
    if not fpath.exists():
        return None
    keys = slot_keys()
    word_vecs: list[list[float]] = []
    with open(fpath) as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("status") == "error":
                continue
            normalized = entry.get("normalized_scores")
            if not normalized:
                continue
            vec = [float(normalized.get(k, 0.0)) for k in keys]
            if len(vec) != 48:
                raise ValueError(f"{atom_name}: word vec dim != 48")
            word_vecs.append(vec)
    if not word_vecs:
        return None
    return np.mean(word_vecs, axis=0).astype(np.float32)


def build_atom_cache(cache_path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    if cache_path.exists():
        d = np.load(cache_path, allow_pickle=False)
        names = [str(s) for s in d["atom_names"]]
        return names, d["profiles"].astype(np.float32), d["valid_mask"].astype(bool)

    atom_names = list_atoms_from_a1_batch()
    profiles = np.full((len(atom_names), 48), np.nan, dtype=np.float32)
    valid = np.zeros(len(atom_names), dtype=bool)
    for i, atom in enumerate(atom_names):
        prof = load_atom_profile(atom)
        if prof is not None:
            profiles[i] = prof
            valid[i] = True
    assert_output_under_v106(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        cache_path,
        atom_names=np.array(atom_names),
        profiles=profiles,
        valid_mask=valid,
    )
    return atom_names, profiles, valid


# ----------------------------------------------------------------------
# Gradient distribute
# ----------------------------------------------------------------------
def _gradient_distribute(value: float, boundaries: list[float], n_levels: int) -> list[float]:
    assert len(boundaries) == n_levels - 1
    levels = [0.0] * n_levels
    if value < boundaries[0]:
        levels[0] = 1.0
        return levels
    for i in range(len(boundaries)):
        if value < boundaries[i]:
            prev_b = boundaries[i - 1]
            curr_b = boundaries[i]
            ratio = (value - prev_b) / max(curr_b - prev_b, 1e-9)
            levels[i - 1] = 1.0 - ratio
            levels[i] = ratio
            return levels
    levels[-1] = 1.0
    return levels


def test_gradient_distribute() -> None:
    r = _gradient_distribute(300, [100, 500], 3)
    assert abs(r[1] - 0.5) < 1e-6
    r = _gradient_distribute(50, [100, 500], 3)
    assert r == [1.0, 0.0, 0.0]
    r = _gradient_distribute(1000, [100, 500], 3)
    assert r == [0.0, 0.0, 1.0]
    r = _gradient_distribute(100, [100, 500], 3)
    assert abs(sum(r) - 1.0) < 1e-6
    r = _gradient_distribute(15000, [100, 500, 2000, 5000, 10000, 15000], 7)
    assert r[-1] == 1.0
    r = _gradient_distribute(7500, [100, 500, 2000, 5000, 10000, 15000], 7)
    assert abs(sum(r) - 1.0) < 1e-6
    print("OK  _gradient_distribute unit test passed")


# ----------------------------------------------------------------------
# Per-axis cid vector builders
# ----------------------------------------------------------------------
def temporal_vector(lifespan_steps: float) -> list[float]:
    return _gradient_distribute(lifespan_steps, [100, 500, 2000, 5000, 10000, 15000], 7)


def scale_vector(n_core: int) -> list[float]:
    levels = [0.0] * 6
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


# Adjusted boundaries based on actual distribution (median 41, max 500)
EPISTEMOLOGICAL_BOUNDARIES = [10, 30, 60, 150]


def epistemological_vector(familiarity_max: float) -> list[float]:
    val = familiarity_max if familiarity_max is not None and not pd.isna(familiarity_max) else 0.0
    return _gradient_distribute(float(val), EPISTEMOLOGICAL_BOUNDARIES, 5)


def ontological_vector(row: pd.Series, seed_max: dict[str, float]) -> list[float]:
    q0 = max(float(row.get("v14_q0", 0) or 0), 1.0)
    material = float(row.get("v14_q_remaining", 0) or 0) / q0

    informational = float(row.get("v14_virtual_familiarity_entries", 0) or 0) / max(
        seed_max.get("virt_fam_entries_max", 1), 1
    )
    relational = float(row.get("n_alphas_currently", 0) or 0) / max(
        seed_max.get("n_alphas_max", 1), 1
    )
    n_core = row.get("n_core_member")
    if pd.isna(n_core):
        n_core = 0
    structural = float(n_core) / 7.0
    semantic = float(row.get("C_at_run_end", 0) or 0) / max(
        seed_max.get("C_max_seed", 1), 1
    )

    raw = [material, informational, relational, structural, semantic]
    raw = [max(0.0, min(1.0, v)) for v in raw]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [0.2] * 5


def interconnection_vector(n_alphas: float) -> list[float]:
    val = n_alphas if not pd.isna(n_alphas) else 0
    return _gradient_distribute(float(val), [1.5, 5.5, 20.5, 50.5], 5)


def resonance_vector(c_value: float) -> list[float]:
    val = c_value if not pd.isna(c_value) else 0
    return _gradient_distribute(float(val), [5, 15, 30], 4)


def symmetry_vector(row: pd.Series) -> list[float]:
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


def lawfulness_vector(row: pd.Series, lifespan_steps: float) -> list[float]:
    pulse_count = float(row.get("v10_pulse_count", 0) or 0)
    density = pulse_count / max(lifespan_steps, 1.0)
    return _gradient_distribute(density, [0.005, 0.02, 0.05], 4)


def experience_vector(row: pd.Series) -> list[float]:
    discovery = float(row.get("n_ingestions_as_eater", 0) or 0) + float(
        row.get("n_phantom_contacts_as_eater", 0) or 0
    )
    creation = float(row.get("n_ingested_as_ghost_food", 0) or 0) + (
        1.0 if (row.get("ghost_duration_steps", 0) or 0) > 0 else 0.0
    )
    comprehension = float(row.get("v10_n_normal", 0) or 0) + float(
        row.get("v10_n_major", 0) or 0
    )
    raw = [discovery, creation, comprehension]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]


def value_generation_vector(row: pd.Series, seed_max: dict[str, float]) -> list[float]:
    q0 = max(float(row.get("v14_q0", 0) or 0), 1.0)
    functional = float(row.get("v14_q_spent", 0) or 0) / q0
    aesthetic = float(row.get("n_observed_as_target", 0) or 0) / max(
        seed_max.get("n_observed_max", 1), 1
    )
    ethical = (
        float(row.get("q_received_from_beta", 0) or 0)
        + float(row.get("c_received_from_beta", 0) or 0)
    ) / max(seed_max.get("received_max", 1), 1)
    sacred = float(row.get("n_betas_joined", 0) or 0) / max(
        seed_max.get("n_betas_joined_max", 1), 1
    )
    raw = [functional, aesthetic, ethical, sacred]
    raw = [max(0.0, min(1.0, v)) for v in raw]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [0.25] * 4


# ----------------------------------------------------------------------
# Per-cid lifespan
# ----------------------------------------------------------------------
def calc_lifespan(row: pd.Series) -> float:
    birth_w = row.get("birth_window")
    if pd.isna(birth_w):
        birth_w = 0
    birth_step = float(birth_w) * WIN_LEN
    final_state = row.get("final_state")
    reaped_step = row.get("reaped_step")
    host_lost = row.get("host_lost_step")
    if final_state == "reaped":
        end_step = reaped_step if not pd.isna(reaped_step) else host_lost
        if pd.isna(end_step):
            end_step = RUN_END_STEP
    elif final_state == "ghost":
        end_step = reaped_step if not pd.isna(reaped_step) else RUN_END_STEP
    else:  # hosted
        end_step = RUN_END_STEP
    return max(float(end_step) - birth_step, 1.0)


# ----------------------------------------------------------------------
# Build seed-level cid vectors
# ----------------------------------------------------------------------
def load_seed_cid_table(seed: int) -> pd.DataFrame:
    df_subj = safe_read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
    df_audit = safe_read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
    audit_cols = [
        "cid", "n_core_member", "v14_q0", "v14_q_remaining", "v14_q_spent",
        "v14_q_exhausted", "v14_virtual_attention_entries", "v14_virtual_attention_sum",
        "v14_virtual_familiarity_entries", "v14_virtual_familiarity_sum",
    ]
    df_audit = df_audit[[c for c in audit_cols if c in df_audit.columns]].copy()
    df = df_subj.merge(
        df_audit, how="left", left_on="cognitive_id", right_on="cid",
        suffixes=("", "_audit"),
    )
    df["seed"] = seed
    df["lifespan_steps"] = df.apply(calc_lifespan, axis=1)
    return df


def compute_seed_max(df: pd.DataFrame) -> dict[str, float]:
    def _maxnum(col):
        if col not in df.columns:
            return 1.0
        s = pd.to_numeric(df[col], errors="coerce")
        m = s.max()
        return float(m) if m and m > 0 else 1.0

    return {
        "virt_fam_entries_max": _maxnum("v14_virtual_familiarity_entries"),
        "n_alphas_max": _maxnum("n_alphas_currently"),
        "C_max_seed": _maxnum("C_at_run_end"),
        "n_observed_max": _maxnum("n_observed_as_target"),
        "received_max": float(
            max(
                pd.to_numeric(df.get("q_received_from_beta", 0), errors="coerce").fillna(0).max() or 0,
                pd.to_numeric(df.get("c_received_from_beta", 0), errors="coerce").fillna(0).max() or 0,
                1.0,
            )
        ),
        "n_betas_joined_max": _maxnum("n_betas_joined"),
    }


def build_cid_vector(row: pd.Series, seed_max: dict[str, float]) -> np.ndarray:
    lifespan = float(row.get("lifespan_steps", 1.0))
    n_core = row.get("n_core_member")
    if pd.isna(n_core):
        n_core = 0
    parts: list[float] = []
    parts.extend(temporal_vector(lifespan))
    parts.extend(scale_vector(int(n_core)))
    parts.extend(epistemological_vector(row.get("last_familiarity_max", 0)))
    parts.extend(ontological_vector(row, seed_max))
    parts.extend(interconnection_vector(row.get("n_alphas_currently", 0)))
    parts.extend(resonance_vector(row.get("C_at_run_end", 0)))
    parts.extend(symmetry_vector(row))
    parts.extend(lawfulness_vector(row, lifespan))
    parts.extend(experience_vector(row))
    parts.extend(value_generation_vector(row, seed_max))
    if len(parts) != 48:
        raise RuntimeError(f"cid vector dim {len(parts)} != 48")
    return np.array(parts, dtype=np.float32)


# ----------------------------------------------------------------------
# 5-pattern (size 3 alpha) classification
# ----------------------------------------------------------------------
PATTERN_5 = {
    "5,5,5": "core",
    "4,5,5": "near_core",
    "2,5,5": "capture",
    "2,4,5": "bridge",
    "2,2,5": "peripheral",
}


def classify_size3_alphas(seed: int, df_cid: pd.DataFrame) -> pd.DataFrame:
    df_alpha = safe_read_csv(INT_DIR / f"alpha_lifecycle_log_seed{seed}.csv")
    df_birth = df_alpha[df_alpha["event_type"] == "birth"].copy()
    df_birth = df_birth[df_birth["member_cids"].notna()]

    n_core_lookup = dict(zip(df_cid["cognitive_id"], df_cid["n_core_member"]))

    rows = []
    for _, r in df_birth.iterrows():
        cids_str = str(r["member_cids"])
        if not cids_str:
            continue
        try:
            members = [int(x) for x in cids_str.split("|") if x]
        except ValueError:
            continue
        if len(members) != 3:
            continue
        n_cores = []
        ok = True
        for c in members:
            v = n_core_lookup.get(c)
            if v is None or pd.isna(v):
                ok = False
                break
            n_cores.append(int(v))
        if not ok:
            continue
        n_cores.sort()
        pat_raw = ",".join(str(n) for n in n_cores)
        rows.append({
            "seed": seed,
            "alpha_id": r["alpha_id"],
            "birth_step": r["step"],
            "trigger_type": r["trigger_type"],
            "member_cids": cids_str,
            "n_cores_sorted": pat_raw,
            "pattern_class": PATTERN_5.get(pat_raw, "other"),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Top-K extraction
# ----------------------------------------------------------------------
def cid_atom_topk(sim: np.ndarray, atom_names: list[str], cids: list[int], seed: int,
                  k: int = 10) -> pd.DataFrame:
    rows = []
    for i, cid in enumerate(cids):
        sim_row = sim[i]
        valid_mask = ~np.isnan(sim_row)
        sim_valid = sim_row.copy()
        sim_valid[~valid_mask] = -np.inf
        order = np.argsort(-sim_valid)
        out = {"seed": seed, "cid": cid}
        for r in range(k):
            idx = order[r]
            if not valid_mask[idx]:
                out[f"rank_{r+1}_atom"] = None
                out[f"rank_{r+1}_sim"] = np.nan
            else:
                out[f"rank_{r+1}_atom"] = atom_names[idx]
                out[f"rank_{r+1}_sim"] = float(sim_valid[idx])
        valid_vals = sim_row[valid_mask]
        out["max_sim"] = float(valid_vals.max()) if valid_vals.size else np.nan
        out["mean_sim"] = float(valid_vals.mean()) if valid_vals.size else np.nan
        out["min_sim"] = float(valid_vals.min()) if valid_vals.size else np.nan
        out["n_unmatched_below_03"] = int((valid_vals < 0.3).sum())
        top_atom = out["rank_1_atom"]
        out["top_atom_category"] = top_atom.split(".")[0] if top_atom else None
        rows.append(out)
    return pd.DataFrame(rows)


def atom_cid_topk(sim: np.ndarray, atom_names: list[str], cids: list[int],
                  atom_valid: np.ndarray, seed: int, k: int = 10) -> pd.DataFrame:
    rows = []
    sim_T = sim.T
    for j, atom in enumerate(atom_names):
        if not atom_valid[j]:
            continue
        col = sim_T[j]
        valid_mask = ~np.isnan(col)
        col_valid = col.copy()
        col_valid[~valid_mask] = -np.inf
        order = np.argsort(-col_valid)
        out = {"seed": seed, "atom": atom}
        for r in range(k):
            idx = order[r]
            if not valid_mask[idx]:
                out[f"rank_{r+1}_cid"] = None
                out[f"rank_{r+1}_sim"] = np.nan
            else:
                out[f"rank_{r+1}_cid"] = int(cids[idx])
                out[f"rank_{r+1}_sim"] = float(col_valid[idx])
        rows.append(out)
    return pd.DataFrame(rows)


def hub_cid_atom_bias(df_cid: pd.DataFrame, sim: np.ndarray, atom_names: list[str],
                      seed: int, top_q: float = 0.99) -> pd.DataFrame:
    threshold = df_cid["n_alphas_currently"].quantile(top_q)
    if not threshold or threshold <= 0:
        threshold = max(df_cid["n_alphas_currently"].max() * 0.5, 1)
    hub_mask = df_cid["n_alphas_currently"] >= threshold
    hub_idx = np.where(hub_mask.to_numpy())[0]
    if hub_idx.size == 0:
        return pd.DataFrame([{"seed": seed, "n_hub_cids": 0, "threshold": threshold}])

    hub_sim = sim[hub_idx]
    rank_atoms: list[str] = []
    cat_counts: dict[str, int] = {}
    for row in hub_sim:
        order = np.argsort(-np.where(np.isnan(row), -np.inf, row))
        if order.size == 0:
            continue
        top_idx = order[0]
        if np.isnan(row[top_idx]):
            continue
        atom = atom_names[top_idx]
        rank_atoms.append(atom)
        cat = atom.split(".")[0]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    atom_counts: dict[str, int] = {}
    for a in rank_atoms:
        atom_counts[a] = atom_counts.get(a, 0) + 1
    top10 = sorted(atom_counts.items(), key=lambda x: -x[1])[:10]
    out = {
        "seed": seed,
        "n_hub_cids": int(hub_idx.size),
        "threshold": float(threshold),
        "category_distribution": json.dumps(cat_counts, ensure_ascii=False),
    }
    for r in range(10):
        if r < len(top10):
            out[f"top_atom_{r+1}"] = top10[r][0]
            out[f"top_atom_{r+1}_count"] = int(top10[r][1])
        else:
            out[f"top_atom_{r+1}"] = None
            out[f"top_atom_{r+1}_count"] = 0
    return pd.DataFrame([out])


def five_pattern_atom_bias(df_pat: pd.DataFrame, df_cid: pd.DataFrame,
                           sim: np.ndarray, atom_names: list[str],
                           atom_profiles: np.ndarray, atom_valid: np.ndarray,
                           seed: int) -> pd.DataFrame:
    cid_idx = {cid: i for i, cid in enumerate(df_cid["cognitive_id"].tolist())}
    rows = []
    for pat_class, sub in df_pat.groupby("pattern_class"):
        member_vecs = []
        for _, r in sub.iterrows():
            for c in str(r["member_cids"]).split("|"):
                try:
                    cidi = int(c)
                except ValueError:
                    continue
                idx = cid_idx.get(cidi)
                if idx is None:
                    continue
                member_vecs.append(sim[idx])
        if not member_vecs:
            continue
        stack = np.vstack(member_vecs)
        if np.all(np.isnan(stack)):
            continue
        with np.errstate(all="ignore"):
            mean_sim_row = np.nanmean(stack, axis=0)
        order = np.argsort(-np.where(np.isnan(mean_sim_row), -np.inf, mean_sim_row))
        top_atom = atom_names[order[0]] if order.size else None
        top_sim = float(mean_sim_row[order[0]]) if order.size else np.nan
        rows.append({
            "seed": seed,
            "pattern_class": pat_class,
            "n_alphas": int(len(sub)),
            "top_atom": top_atom,
            "top_atom_sim": top_sim,
            "top5_atoms": ",".join(atom_names[i] for i in order[:5]),
        })
    return pd.DataFrame(rows)


def beta_atom_aggregate(seed: int, df_cid: pd.DataFrame, sim: np.ndarray,
                        atom_names: list[str]) -> pd.DataFrame:
    df_b_mem = safe_read_csv(INT_DIR / f"beta_membership_log_seed{seed}.csv")
    last_step = df_b_mem["step"].max() if "step" in df_b_mem.columns else None
    if last_step is None:
        return pd.DataFrame()
    snap = df_b_mem[df_b_mem["step"] == last_step].copy()
    cid_idx = {cid: i for i, cid in enumerate(df_cid["cognitive_id"].tolist())}
    rows = []
    for _, r in snap.iterrows():
        members_str = str(r.get("member_cids", "") or "")
        if not members_str:
            continue
        try:
            members = [int(c) for c in members_str.split("|") if c]
        except ValueError:
            continue
        vecs = []
        for c in members:
            idx = cid_idx.get(c)
            if idx is None:
                continue
            vecs.append(sim[idx])
        if not vecs:
            continue
        stack = np.vstack(vecs)
        if np.all(np.isnan(stack)):
            continue
        with np.errstate(all="ignore"):
            mean_row = np.nanmean(stack, axis=0)
        order = np.argsort(-np.where(np.isnan(mean_row), -np.inf, mean_row))
        top5 = [atom_names[i] for i in order[:5]]
        rows.append({
            "seed": seed,
            "beta_id": r["beta_id"],
            "n_member_cids": int(r.get("n_member_cids_active", 0) or 0),
            "n_member_alphas": int(r.get("n_member_alphas_active", 0) or 0),
            "top_atom": top5[0],
            "top5_atoms": ",".join(top5),
            "max_atom_sim": float(mean_row[order[0]]) if order.size else np.nan,
        })
    return pd.DataFrame(rows)


def unmatched_structures(df_cid: pd.DataFrame, sim: np.ndarray,
                         atom_names: list[str], atom_valid: np.ndarray,
                         seed: int) -> pd.DataFrame:
    rows = []
    cids = df_cid["cognitive_id"].tolist()
    for i, cid in enumerate(cids):
        row = sim[i]
        valid = row[~np.isnan(row)]
        if valid.size == 0:
            continue
        m = float(valid.max())
        if m < 0.3:
            cls = "genesis_unique"
        elif m < 0.5:
            cls = "partial_match"
        else:
            continue
        rows.append({
            "seed": seed, "classification": cls, "entity_type": "cid",
            "entity_id": int(cid), "max_sim": m,
            "description": f"final_state={df_cid.iloc[i].get('final_state')}",
        })
    sim_T = sim.T
    for j, atom in enumerate(atom_names):
        if not atom_valid[j]:
            continue
        col = sim_T[j]
        valid = col[~np.isnan(col)]
        if valid.size == 0:
            continue
        m = float(valid.max())
        if m < 0.3:
            rows.append({
                "seed": seed, "classification": "language_specific",
                "entity_type": "atom", "entity_id": atom, "max_sim": m,
                "description": "no cid matched above 0.3",
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Per-seed orchestration
# ----------------------------------------------------------------------
def run_seed(seed: int, atom_names: list[str], atom_profiles: np.ndarray,
             atom_valid: np.ndarray, out_root: Path) -> dict:
    df_cid = load_seed_cid_table(seed)
    seed_max = compute_seed_max(df_cid)

    cid_vecs = np.vstack([build_cid_vector(r, seed_max) for _, r in df_cid.iterrows()])
    cids = df_cid["cognitive_id"].astype(int).tolist()

    profile_records = []
    dim_cols = [f"dim_{i}" for i in range(48)]
    for cid, vec in zip(cids, cid_vecs):
        rec = {"seed": seed, "cid": int(cid)}
        rec.update({c: float(v) for c, v in zip(dim_cols, vec)})
        profile_records.append(rec)
    df_profile = pd.DataFrame(profile_records)
    safe_write_csv(df_profile, out_root / f"cid_structure_profile_seed{seed}.csv")

    sim = np.full((cid_vecs.shape[0], atom_profiles.shape[0]), np.nan, dtype=np.float32)
    valid_atom_idx = np.where(atom_valid)[0]
    if valid_atom_idx.size:
        sim_valid = cosine_similarity(cid_vecs, atom_profiles[valid_atom_idx])
        sim[:, valid_atom_idx] = sim_valid.astype(np.float32)

    df_topk_cid = cid_atom_topk(sim, atom_names, cids, seed)
    safe_write_csv(df_topk_cid, out_root / f"cid_atom_topk_seed{seed}.csv")

    df_topk_atom = atom_cid_topk(sim, atom_names, cids, atom_valid, seed)
    safe_write_csv(df_topk_atom, out_root / f"atom_cid_topk_seed{seed}.csv")

    df_sim_matrix = pd.DataFrame(sim, index=cids, columns=atom_names)
    df_sim_matrix.index.name = "cid"
    df_sim_matrix.reset_index(inplace=True)
    df_sim_matrix.insert(0, "seed", seed)
    safe_write_parquet(df_sim_matrix, out_root / f"cid_atom_sim_matrix_seed{seed}.parquet")

    df_hub = hub_cid_atom_bias(df_cid, sim, atom_names, seed)
    safe_write_csv(df_hub, out_root / f"hub_cid_atom_bias_seed{seed}.csv")

    df_pat = classify_size3_alphas(seed, df_cid)
    safe_write_csv(df_pat, out_root / f"five_pattern_classification_seed{seed}.csv")
    df_pat_bias = five_pattern_atom_bias(df_pat, df_cid, sim, atom_names,
                                          atom_profiles, atom_valid, seed)
    safe_write_csv(df_pat_bias, out_root / f"five_pattern_atom_bias_seed{seed}.csv")

    df_beta = beta_atom_aggregate(seed, df_cid, sim, atom_names)
    safe_write_csv(df_beta, out_root / f"beta_atom_aggregate_seed{seed}.csv")

    df_un = unmatched_structures(df_cid, sim, atom_names, atom_valid, seed)
    safe_write_csv(df_un, out_root / f"unmatched_structures_seed{seed}.csv")

    return {
        "seed": seed,
        "n_cid": int(len(df_cid)),
        "n_alphas_size3": int(len(df_pat)),
        "n_hub_cid": int(df_hub.iloc[0]["n_hub_cids"]) if len(df_hub) else 0,
        "n_unmatched": int(len(df_un)),
        "mean_max_sim": float(df_topk_cid["max_sim"].mean()) if len(df_topk_cid) else np.nan,
        "median_max_sim": float(df_topk_cid["max_sim"].median()) if len(df_topk_cid) else np.nan,
    }


# ----------------------------------------------------------------------
# Shadow audit (path enforcement + idempotency)
# ----------------------------------------------------------------------
def shadow_audit(atom_names, atom_profiles, atom_valid) -> None:
    sample = SUBJ_DIR / "per_subject_seed0.csv"
    if not sample.exists():
        raise RuntimeError(f"v10.5 input missing: {sample}")
    df_test = safe_read_csv(sample)
    print(f"OK  v10.5 input accessible: {len(df_test)} rows from seed 0")

    test_out = SMOKE_ROOT / "shadow_audit_test.csv"
    safe_write_csv(pd.DataFrame({"test": [1]}), test_out)
    test_out.unlink()
    print(f"OK  v10.6 output writeable: {SMOKE_ROOT}")

    audit_a = SMOKE_ROOT / "audit_run_a"
    audit_b = SMOKE_ROOT / "audit_run_b"
    s_a = run_seed(0, atom_names, atom_profiles, atom_valid, audit_a)
    s_b = run_seed(0, atom_names, atom_profiles, atom_valid, audit_b)
    if s_a != s_b:
        raise RuntimeError(f"idempotency mismatch: {s_a} vs {s_b}")
    df_a = pd.read_csv(audit_a / "cid_atom_topk_seed0.csv")
    df_b = pd.read_csv(audit_b / "cid_atom_topk_seed0.csv")
    pd.testing.assert_frame_equal(df_a, df_b)
    print("OK  idempotency test passed (seed 0 written twice, identical)")
    print("OK  shadow audit PASS")


# ----------------------------------------------------------------------
# Axes metadata writer
# ----------------------------------------------------------------------
def write_axes_metadata(out_root: Path) -> None:
    ranges = axis_dim_ranges()
    meta = {
        "axes_order": [
            {
                "name": axis,
                "n_levels": len(levels),
                "dim_start": ranges[axis][0],
                "dim_end": ranges[axis][1],
                "level_names": levels,
            }
            for axis, levels in AXES_ORDER
        ],
        "value_generation_levels": [
            {"index": 44, "name": "functional",
             "indicator": "v14_q_spent / v14_q0"},
            {"index": 45, "name": "aesthetic",
             "indicator": "n_observed_as_target / max(seed)"},
            {"index": 46, "name": "ethical",
             "indicator": "(q_received_from_beta + c_received_from_beta) / max(seed)"},
            {"index": 47, "name": "sacred",
             "indicator": "n_betas_joined / max(seed)"},
        ],
        "n_core_source": "audit/per_subject_audit_seed{N}.csv .n_core_member (int64, fully populated)",
        "alpha_lifecycle_event_filter": "event_type == 'birth'",
        "epistemological_boundaries": EPISTEMOLOGICAL_BOUNDARIES,
        "win_len": WIN_LEN,
        "run_end_step": RUN_END_STEP,
    }
    safe_write_json(meta, out_root / "axes_metadata.json")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--seeds", type=str, default=None,
                    help="Comma-separated seeds (default: 0 for smoke, 0-23 for main)")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT

    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    elif args.mode == "smoke":
        seeds = [0]
    else:
        seeds = SEEDS

    print(f"v10.6 atom_alignment_observer - mode={args.mode}, seeds={seeds}")
    print(f"  V105_ROOT = {V105_ROOT}")
    print(f"  V106_ROOT = {V106_ROOT}")
    print(f"  out_root  = {out_root}")
    print()

    test_gradient_distribute()
    verify_axes_match()
    all_atoms = list_atoms_from_a1_batch()
    observed = list_atoms_observed()
    unobs = get_unobserved_atoms()
    print(f"OK  atom enumeration: total={len(all_atoms)}, observed={len(observed)}, unobserved={unobs}")

    cache_path = out_root / "atom_profiles_cache.npz"
    atom_names, atom_profiles, atom_valid = build_atom_cache(cache_path)
    print(f"OK  atom cache: {atom_profiles.shape}, valid={int(atom_valid.sum())}")

    write_axes_metadata(out_root)

    if args.mode == "smoke":
        shadow_audit(atom_names, atom_profiles, atom_valid)

    summary_rows = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        s = run_seed(seed, atom_names, atom_profiles, atom_valid, out_root)
        s["elapsed_sec"] = round(time.time() - ts, 2)
        print(f"  seed={seed}: n_cid={s['n_cid']}, n_alphas_size3={s['n_alphas_size3']}, "
              f"n_hub_cid={s['n_hub_cid']}, mean_max_sim={s['mean_max_sim']:.3f}, "
              f"elapsed={s['elapsed_sec']}s")
        summary_rows.append(s)
    df_summary = pd.DataFrame(summary_rows)
    safe_write_csv(df_summary, out_root / "run_summary.csv")
    total = round(time.time() - t0, 2)
    print(f"\nDONE  total elapsed = {total}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
