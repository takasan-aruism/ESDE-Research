#!/usr/bin/env python3
"""
v9.11 Genesis Budget (B_gen) 実分布の計測
==========================================
v9.10 long run と同じエンジン構成で走らせ、
label birth の瞬間に S_avg, r_core を計測して B_gen を算出する。

出力: stdout に集計結果を表示 + CSV を primitive/v911/ に保存
"""

import sys, math, time, csv, argparse
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
from v19g_canon import BASE_PARAMS, BIAS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


def measure_birth_stats(engine_state, label_nodes):
    """Birth 時点の S_avg と r_core を計測する。"""
    alive_nodes = [n for n in label_nodes if n in engine_state.alive_n]
    n_core = len(alive_nodes)
    if n_core == 0:
        return 0, 0.0, 0.0

    # S_avg: ラベル内ノード間のリンク強度平均
    s_values = []
    nodes_set = set(alive_nodes)
    for lk in engine_state.alive_l:
        if lk[0] in nodes_set and lk[1] in nodes_set:
            s_values.append(engine_state.S[lk])

    if not s_values:
        # ノード間にリンクがない場合 (R>0 ペアでも S が小さい可能性)
        # ラベルのノードに接続する全リンクから、ラベル内リンクを探す
        # → 既に探索済み、本当にない
        s_avg = 0.0
    else:
        s_avg = sum(s_values) / len(s_values)

    # r_core: Kuramoto order parameter = |1/N Σ exp(i θ_j)|
    if n_core == 1:
        r_core = 1.0
    else:
        sin_sum = sum(math.sin(float(engine_state.theta[n])) for n in alive_nodes)
        cos_sum = sum(math.cos(float(engine_state.theta[n])) for n in alive_nodes)
        r_core = math.sqrt(sin_sum**2 + cos_sum**2) / n_core

    return n_core, s_avg, r_core


def run_measure(seed, maturation_windows=20, tracking_windows=50,
                window_steps=500):
    """1 seed 分を走らせて birth 時 B_gen データを収集する。"""
    N = V82_N
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    bg_prob = BASE_PARAMS["background_injection_prob"]
    engine.run_injection()

    birth_records = []

    def detect_births_and_measure(prev_lids, curr_lids, w, phase):
        """prev/curr の差分から birth を検出し、S_avg, r_core を計測"""
        for lid in (curr_lids - prev_lids):
            lab = engine.virtual.labels[lid]
            n_core, s_avg, r_core = measure_birth_stats(
                engine.state, lab["nodes"])
            if n_core == 0:
                continue
            b_gen = n_core * s_avg * r_core
            birth_records.append({
                "seed": seed,
                "window": w,
                "phase": phase,
                "lid": lid,
                "n_core": n_core,
                "s_avg": round(s_avg, 6),
                "r_core": round(r_core, 6),
                "b_gen": round(b_gen, 6),
                "phase_sig": round(lab["phase_sig"], 6),
                "links_total": len(engine.state.alive_l),
            })

    # Maturation
    for w in range(maturation_windows):
        macro_set = set(engine.virtual.macro_nodes)
        prev_lids = set(engine.virtual.labels.keys()) - macro_set
        engine.step_window(steps=window_steps)
        macro_set = set(engine.virtual.macro_nodes)
        curr_lids = set(engine.virtual.labels.keys()) - macro_set
        detect_births_and_measure(prev_lids, curr_lids, w, "maturation")

    print(f"  seed={seed} mat done. births_so_far={len(birth_records)}")

    # Tracking
    for tw in range(tracking_windows):
        w = maturation_windows + tw
        macro_set = set(engine.virtual.macro_nodes)
        prev_lids = set(engine.virtual.labels.keys()) - macro_set

        # Run window steps with background injection (v910 と同一)
        for step in range(window_steps):
            engine.realizer.step(engine.state)
            engine.physics.step_pre_chemistry(engine.state)
            engine.chem.step(engine.state)
            engine.physics.step_resonance(engine.state)

            engine._g_scores[:] = 0
            engine.grower.step(engine.state)
            agr = engine.grower.params.auto_growth_rate
            for k in engine.state.alive_l:
                r = engine.state.R.get(k, 0.0)
                if r > 0:
                    a = min(agr * r,
                            max(engine.state.get_latent(k[0], k[1]), 0))
                    if a > 0:
                        engine._g_scores[k[0]] += a
                        engine._g_scores[k[1]] += a
            gz = float(engine._g_scores.sum())

            engine.intruder.step(engine.state)
            engine.physics.step_decay_exclusion(engine.state)

            al = list(engine.state.alive_n)
            na = len(al)
            if na > 0:
                aa = np.array(al)
                if BIAS > 0 and gz > 0:
                    ga = engine._g_scores[aa]
                    gs = ga.sum()
                    if gs > 0:
                        pg = ga / gs
                        pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
                        pd /= pd.sum()
                    else:
                        pd = np.ones(na) / na
                else:
                    pd = np.ones(na) / na
                mk = engine.state.rng.random(na) < bg_prob
                for idx in range(na):
                    if mk[idx]:
                        t = int(engine.state.rng.choice(aa, p=pd))
                        if t in engine.state.alive_n:
                            engine.state.E[t] = min(
                                1.0, engine.state.E[t] + 0.3)
                            if engine.state.Z[t] == 0 and \
                               engine.state.rng.random() < 0.5:
                                engine.state.Z[t] = 1 if \
                                    engine.state.rng.random() < 0.5 else 2

        # VL step (label 生死)
        isl_m = find_islands_sets(engine.state, 0.20)

        class _Isl:
            pass
        islands_dict = {}
        for i, isl in enumerate(isl_m):
            obj = _Isl()
            obj.nodes = isl
            islands_dict[i] = obj

        vs = engine.virtual.step(engine.state, engine.window_count,
                                  islands=islands_dict,
                                  substrate=engine.substrate)
        engine.virtual_stats = vs
        engine.window_count += 1

        macro_set = set(engine.virtual.macro_nodes)
        curr_lids = set(engine.virtual.labels.keys()) - macro_set
        detect_births_and_measure(prev_lids, curr_lids, w, "tracking")

    print(f"  seed={seed} done. total_births={len(birth_records)}")
    return birth_records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--mat", type=int, default=20)
    parser.add_argument("--track", type=int, default=50)
    parser.add_argument("--window-steps", type=int, default=500)
    args = parser.parse_args()

    all_records = []
    for seed in args.seeds:
        t0 = time.time()
        records = run_measure(seed, args.mat, args.track, args.window_steps)
        all_records.extend(records)
        print(f"  seed={seed} elapsed={time.time()-t0:.0f}s")

    # Save CSV
    outpath = _SCRIPT_DIR / "v911_genesis_budget_raw.csv"
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "seed", "window", "phase", "lid", "n_core",
            "s_avg", "r_core", "b_gen", "phase_sig", "links_total"])
        w.writeheader()
        w.writerows(all_records)
    print(f"\nSaved {len(all_records)} records to {outpath}")

    # Summary
    if not all_records:
        print("No birth records found.")
        return

    b_vals = [r["b_gen"] for r in all_records]
    b_arr = np.array(b_vals)
    print(f"\n=== B_gen distribution (all births, n={len(b_arr)}) ===")
    print(f"  min={b_arr.min():.4f}  p10={np.percentile(b_arr,10):.4f}"
          f"  p50={np.percentile(b_arr,50):.4f}"
          f"  p90={np.percentile(b_arr,90):.4f}  max={b_arr.max():.4f}")
    print(f"  mean={b_arr.mean():.4f}  std={b_arr.std():.4f}")

    # Per n_core
    by_nc = defaultdict(list)
    for r in all_records:
        by_nc[r["n_core"]].append(r["b_gen"])
    print(f"\n=== B_gen by n_core ===")
    for nc in sorted(by_nc):
        vals = np.array(by_nc[nc])
        print(f"  n_core={nc}: n={len(vals):4d}  "
              f"min={vals.min():.4f} p50={np.median(vals):.4f} "
              f"max={vals.max():.4f} mean={vals.mean():.4f}")

    # S_avg vs r_core correlation
    s_vals = np.array([r["s_avg"] for r in all_records])
    r_vals = np.array([r["r_core"] for r in all_records])
    if len(s_vals) > 2:
        corr = np.corrcoef(s_vals, r_vals)[0, 1]
        print(f"\n=== S_avg vs r_core ===")
        print(f"  corr(S_avg, r_core) = {corr:.4f}")
        print(f"  S_avg: mean={s_vals.mean():.4f} std={s_vals.std():.4f}")
        print(f"  r_core: mean={r_vals.mean():.4f} std={r_vals.std():.4f}")

    # PI trial (clamp 10..200)
    print(f"\n=== PI trial: PI = clamp(alpha * B_gen, 10, 200) ===")
    for alpha in [0.5, 1.0, 2.0, 5.0]:
        pi_vals = np.clip(alpha * b_arr, 10, 200)
        at_10 = np.sum(pi_vals == 10) / len(pi_vals) * 100
        at_200 = np.sum(pi_vals == 200) / len(pi_vals) * 100
        print(f"  alpha={alpha:.1f}: "
              f"p10={np.percentile(pi_vals,10):.1f} "
              f"p50={np.median(pi_vals):.1f} "
              f"p90={np.percentile(pi_vals,90):.1f} "
              f"clamp@10={at_10:.1f}% clamp@200={at_200:.1f}%")


if __name__ == "__main__":
    main()
