#!/usr/bin/env python3
"""v10.10 atom_event_generator (Multi-gate × timing 二次元設計).

28 conditions:
  - 主軸 5 × 3 timing = 15: ABC/ABc/AB/B/Bc × t200/t300/t500
  - 観察用 2 × 3 = 6: AC/BC × t200/t300/t500
  - controls 2 × 3 = 6: A/all_pass × t200/t300/t500
  - bit-identity 1: v108_re (v10.8 標準再実行)

各 v110 condition は gate 別判定 + age_target で発火 timing 決定。
v108_re は v10.8 既存実装をそのまま流用。
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
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()
DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"

sys.path.insert(0, str(V107_ROOT))
sys.path.insert(0, str(V108_ROOT))
from v107_event_aggregator import attach_pre_event_state  # noqa: E402
from v107_baseline_constructor import _cid_meta_table  # noqa: E402
from v108_atom_event_generator import (  # noqa: E402
    TARGET_ATOMS, RESERVED_ATOM, RESERVED_LABEL,
    RUN_END_STEP, EVENTS_PER_ATOM,
    generate_seed_atom_events as v108_generate_seed_atom_events,
)

OUT_ROOT = V110_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"
V108RE_ROOT = V110_ROOT / "v108_re" / "outputs"

SEEDS = list(range(24))
GATES = ["ABC", "ABc", "AB", "B", "Bc", "AC", "BC", "A", "all_pass"]
AGE_TARGETS = [200, 300, 500]
AGE_UPPER_LIMIT = 560  # A 軸の上限 (age <= 560)

# 28 conditions
CONDITIONS: dict[str, dict] = {}
for g in GATES:
    for at in AGE_TARGETS:
        CONDITIONS[f"v110_{g}_t{at}"] = {
            "gate": g, "age_target": at, "Q_cost": 1, "C_gain": 1,
        }
CONDITIONS["v108_re"] = {"gate": "v108_standard", "age_target": "uniform",
                            "Q_cost": 1, "C_gain": 1}


def assert_output_under_v110(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V110_ROOT not in abs_path.parents and abs_path != V110_ROOT:
        raise ValueError(f"Output path {path} not under v110/")


def safe_write_parquet_v110(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v110(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def safe_read_csv(p: Path) -> pd.DataFrame:
    return pd.read_csv(p)


def build_alpha_beta_intervals(seed: int) -> dict[int, list[tuple[int, int]]]:
    """各 cid の (in_step, out_step) 区間 (timestamp 別 in_integration 判定用)."""
    cid_intervals: dict[int, list[tuple[int, int]]] = {}
    for fname in ["alpha_lifecycle_log", "beta_lifecycle_log"]:
        df = safe_read_csv(DIAG_ROOT / f"integration/{fname}_seed{seed}.csv")
        if df.empty:
            continue
        if "alpha_id" in df.columns:
            id_col = "alpha_id"
        elif "beta_id" in df.columns:
            id_col = "beta_id"
        else:
            id_col = None
        if id_col:
            for aid, sub in df.groupby(id_col):
                births = sub[sub["event_type"] == "birth"]
                deaths = sub[sub["event_type"] == "death"]
                if births.empty:
                    continue
                t_in = int(births.iloc[0]["step"])
                t_out = int(deaths.iloc[0]["step"]) if not deaths.empty else RUN_END_STEP
                mems_str = str(births.iloc[0].get("member_cids") or "")
                for c_str in mems_str.split("|"):
                    if not c_str.strip():
                        continue
                    try:
                        c = int(c_str)
                    except ValueError:
                        continue
                    cid_intervals.setdefault(c, []).append((t_in, t_out))
        else:
            births = df[df["event_type"] == "birth"]
            for _, r in births.iterrows():
                mems = str(r.get("member_cids") or "")
                t_in = int(r["step"])
                for c_str in mems.split("|"):
                    if not c_str.strip():
                        continue
                    try:
                        c = int(c_str)
                    except ValueError:
                        continue
                    cid_intervals.setdefault(c, []).append((t_in, RUN_END_STEP))
    return cid_intervals


def cid_in_integration_at(cid: int, t: int, intervals: dict) -> bool:
    for (t_in, t_out) in intervals.get(cid, []):
        if t_in <= t < t_out:
            return True
    return False


def is_receptive(gate: str, age_target: int, t_event: int,
                    in_integ: bool, fam_v: float, p75: float, p50: float) -> bool:
    """gate 別の receptive 判定。
    A: age_target <= AGE_UPPER_LIMIT (560、age_target<=500 で常に true)
    B: not in_integration (timestamp 別)
    C: fam_v >= p75 (top 25%)
    c: fam_v >= p50 (top 50%)
    """
    age_ok = (age_target <= AGE_UPPER_LIMIT)
    out_integ = not in_integ
    fam_C = (fam_v >= p75)
    fam_c = (fam_v >= p50)
    if gate == "ABC": return age_ok and out_integ and fam_C
    if gate == "ABc": return age_ok and out_integ and fam_c
    if gate == "AB":  return age_ok and out_integ
    if gate == "AC":  return age_ok and fam_C
    if gate == "BC":  return out_integ and fam_C
    if gate == "B":   return out_integ
    if gate == "Bc":  return out_integ and fam_c
    if gate == "A":   return age_ok
    if gate == "all_pass": return True
    raise ValueError(f"Unknown gate: {gate}")


def generate_v110_seed_events(seed: int, condition_id: str) -> pd.DataFrame:
    """v110 condition の atom_introduction_events 生成。
    各 cid について t = birth + age_target で gate 評価、PASS なら 25 atom 循環で発火。
    """
    cfg = CONDITIONS[condition_id]
    gate = cfg["gate"]
    age_target = cfg["age_target"]
    Q_cost = cfg["Q_cost"]
    C_gain = cfg["C_gain"]

    m = _cid_meta_table(seed)
    intervals = build_alpha_beta_intervals(seed)
    fam = m["last_familiarity_max"].fillna(0)
    p75 = float(fam.quantile(0.75))
    p50 = float(fam.quantile(0.50))
    death = pd.concat([
        m["host_lost_step"].fillna(RUN_END_STEP),
        m["reaped_step"].fillna(RUN_END_STEP),
    ], axis=1).min(axis=1)

    # gate PASS 順に cid を birth_step 順で並べる (同 birth は cid 順)
    rows = []
    sorted_m = m.sort_values(["birth_step", "cognitive_id"]).reset_index(drop=True)
    death_lookup = dict(zip(m["cognitive_id"].astype(int).values,
                                death.values.astype(int)))
    event_seq = 0
    for _, row in sorted_m.iterrows():
        cid = int(row["cognitive_id"])
        birth = int(row["birth_step"])
        t_event = birth + age_target
        if t_event >= RUN_END_STEP:
            continue
        if t_event >= death_lookup[cid]:
            continue
        in_integ = cid_in_integration_at(cid, t_event, intervals)
        fam_v = float(row["last_familiarity_max"]) if pd.notna(row["last_familiarity_max"]) else 0.0
        if not is_receptive(gate, age_target, t_event, in_integ, fam_v, p75, p50):
            continue
        atom_idx = event_seq % 25
        atom_id = TARGET_ATOMS[atom_idx]
        reserved_label = RESERVED_LABEL if atom_id == RESERVED_ATOM else ""
        rows.append({
            "event_source_type": "atom_introduction_event",
            "condition_id": condition_id,
            "source_cid": cid,
            "timestamp": t_event,
            "atom_id": atom_id,
            "atom_index": atom_idx,
            "top_k_rank": -1,  # gate-filtered: top_k 概念なし
            "atom_sim_score": float("nan"),
            "reserved_label": reserved_label,
        })
        event_seq += 1

    if not rows:
        return pd.DataFrame(columns=[
            "event_source_type", "condition_id", "source_cid", "timestamp",
            "atom_id", "atom_index", "top_k_rank", "atom_sim_score",
            "reserved_label", "seed", "event_id",
        ])
    df = pd.DataFrame(rows)
    df["seed"] = seed
    df = df.sort_values(["timestamp", "atom_index"]).reset_index(drop=True)
    df["event_id"] = [f"{seed}_{condition_id}_atom_{i}" for i in range(len(df))]
    # post_event_state
    df = attach_pre_event_state(df, seed)
    df["Q_after_atom_intro"] = df["Q_pre"] - Q_cost
    df["C_after_atom_intro"] = df["C_pre"] + C_gain
    return df


def generate_v108re_seed_events(seed: int) -> pd.DataFrame:
    """v108 atom_event_generator を直接呼んで v110/v108_re/ に出力するための DataFrame."""
    df = v108_generate_seed_atom_events(seed)
    df["condition_id"] = "v108_re"
    return df


def generate_seed_atom_events(seed: int, condition_id: str) -> pd.DataFrame:
    if condition_id == "v108_re":
        return generate_v108re_seed_events(seed)
    return generate_v110_seed_events(seed, condition_id)


def out_path_for(condition_id: str, seed: int, mode: str) -> Path:
    """v108_re は v110/v108_re/outputs/{mode}/、それ以外は v110/outputs/{mode}/."""
    if condition_id == "v108_re":
        root = V108RE_ROOT / mode
    else:
        root = SMOKE_ROOT if mode == "smoke" else MAIN_ROOT
    return root / f"atom_introduction_events_{condition_id}_seed{seed}.parquet"


def _worker(args):
    seed, condition_id, mode = args
    df = generate_seed_atom_events(seed, condition_id)
    out = out_path_for(condition_id, seed, mode)
    safe_write_parquet_v110(df, out)
    return {
        "seed": seed, "condition_id": condition_id,
        "n_events": int(len(df)),
        "n_unique_cids": int(df["source_cid"].nunique()) if not df.empty else 0,
        "size_mb": round(out.stat().st_size / 1024 / 1024, 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--conditions", default="all",
                       help="Comma-separated condition ids or 'all'")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    seeds = [0] if args.mode == "smoke" else SEEDS
    if args.conditions == "all":
        conds = list(CONDITIONS.keys())
    else:
        conds = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conds:
        if c not in CONDITIONS:
            raise SystemExit(f"Unknown condition: {c}")

    print(f"v10.10 atom_event_generator - mode={args.mode}, "
          f"seeds={len(seeds)}, conditions={len(conds)}, n_workers={args.n_workers}")

    jobs = [(s, c, args.mode) for s in seeds for c in conds]
    n_workers = max(1, min(args.n_workers, len(jobs)))
    t0 = time.time()
    if n_workers > 1 and len(jobs) > 1:
        print(f"=== 並列実行 ({n_workers} workers、{len(jobs)} jobs) ===")
        with Pool(processes=n_workers) as pool:
            results = pool.map(_worker, jobs)
    else:
        results = [_worker(j) for j in jobs]

    df_sum = pd.DataFrame(results).sort_values(["condition_id", "seed"]).reset_index(drop=True)
    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    safe_write_parquet_v110(df_sum, out_root / "atom_event_run_summary.parquet")

    # 集計表 (condition 別 events 合計)
    print(f"\n=== events / condition (24 seeds 合計、smoke=seed 0) ===")
    cond_sum = df_sum.groupby("condition_id")["n_events"].agg(["sum", "min", "max", "mean"]).round(1)
    cond_sum.columns = ["total", "min/seed", "max/seed", "mean/seed"]
    print(cond_sum.to_string())
    total_events = df_sum["n_events"].sum()
    print(f"\n  total events all conditions: {total_events}")
    print(f"  total size all conditions: {df_sum['size_mb'].sum():.2f} MB")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
