#!/usr/bin/env python3
"""
v9.11 Genesis Budget — 高速版 (step_window 利用)
birth 時点で S_avg, r_core を計測。
step_window() を使うため物理層は v910 long run と bit-identical。
ただし tracking 中の背景注入の growth bias 計算が step_window 内部版になる。
"""

import sys, math, time, csv, json
import numpy as np
from pathlib import Path
from collections import defaultdict

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline" / "v43"
_V41_DIR = _V43_DIR.parent / "v41"
_V910_DIR = _REPO_ROOT / "primitive" / "v910"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V910_DIR), str(_V82_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from esde_v82_engine import (V82Engine, V82EncapsulationParams, V82_N,
                              find_islands_sets)
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


def measure_birth_stats(state, label_nodes):
    alive_nodes = [n for n in label_nodes if n in state.alive_n]
    n_core = len(alive_nodes)
    if n_core == 0:
        return 0, 0.0, 0.0

    nodes_set = set(alive_nodes)
    s_values = []
    for lk in state.alive_l:
        if lk[0] in nodes_set and lk[1] in nodes_set:
            s_values.append(state.S[lk])
    s_avg = sum(s_values) / len(s_values) if s_values else 0.0

    if n_core == 1:
        r_core = 1.0
    else:
        sin_sum = sum(math.sin(float(state.theta[n])) for n in alive_nodes)
        cos_sum = sum(math.cos(float(state.theta[n])) for n in alive_nodes)
        r_core = math.sqrt(sin_sum**2 + cos_sum**2) / n_core

    return n_core, s_avg, r_core


def run_one_seed(seed):
    N = V82_N
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    engine.run_injection()

    birth_records = []
    total_windows = 70  # 20 mat + 50 track

    for w in range(total_windows):
        macro_set = set(engine.virtual.macro_nodes)
        prev_lids = set(engine.virtual.labels.keys()) - macro_set

        engine.step_window(steps=500)

        macro_set = set(engine.virtual.macro_nodes)
        curr_lids = set(engine.virtual.labels.keys()) - macro_set

        for lid in (curr_lids - prev_lids):
            lab = engine.virtual.labels[lid]
            n_core, s_avg, r_core = measure_birth_stats(
                engine.state, lab["nodes"])
            if n_core == 0:
                continue
            b_gen = n_core * s_avg * r_core
            birth_records.append({
                "seed": seed, "window": w, "lid": lid,
                "n_core": n_core,
                "s_avg": round(s_avg, 6),
                "r_core": round(r_core, 6),
                "b_gen": round(b_gen, 6),
                "phase_sig": round(lab["phase_sig"], 6),
                "links_total": len(engine.state.alive_l),
                "n_intra_links": sum(1 for lk in engine.state.alive_l
                    if lk[0] in lab["nodes"] and lk[1] in lab["nodes"]),
            })

    # Write per-seed CSV
    outpath = _SCRIPT_DIR / f"v911_gb_seed{seed}.csv"
    with open(outpath, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=[
            "seed", "window", "lid", "n_core",
            "s_avg", "r_core", "b_gen", "phase_sig",
            "links_total", "n_intra_links"])
        wr.writeheader()
        wr.writerows(birth_records)

    print(json.dumps({"seed": seed, "births": len(birth_records),
                       "file": str(outpath)}), flush=True)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("seed", type=int)
    args = p.parse_args()
    run_one_seed(args.seed)
