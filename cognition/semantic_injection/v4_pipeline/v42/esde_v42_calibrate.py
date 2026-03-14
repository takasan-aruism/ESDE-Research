#!/usr/bin/env python3
"""
ESDE v4.2 — Adaptive Dynamics Calibration
===========================================
Phase : v4.2 Calibration
Role  : Claude (Implementation)

Two sweep modes:

  1. SINGLE-WAVE (v4.1 compatible baseline):
     Fresh engine per amplitude, single wave, measure response.

  2. MULTI-WAVE (v4.2 core test):
     Single engine, repeated waves at same amplitude.
     Tests: Does plasticity → rewiring → hardening → resistance emerge?

Key metrics to watch:
  - n_clusters: Should increase from 1 (v4.1 baseline stuck at 1)
  - cluster_reformations: Should become > 0
  - hardened_links_count: Should accumulate across waves
  - resistance_mean: Should rise for surviving clusters

USAGE
-----
  # Single-wave baseline (like v4.1)
  python esde_v42_calibrate.py --mode single

  # Multi-wave adaptive dynamics test
  python esde_v42_calibrate.py --mode multi --waves 10 --amplitude 1.0

  # Full sweep
  python esde_v42_calibrate.py --mode multi --waves 10 \
    --amplitudes 0.5 1.0 1.5 2.0 --seeds 42 123 456
"""

import sys, csv, json, time, argparse, math
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v42_engine import (
    V42Engine, V42StateFrame,
    PlasticityParams,
)
from esde_v41_engine import WaveParams, WINDOW


# ================================================================
# LOG FIELDS
# ================================================================
SINGLE_FIELDS = [
    "amplitude", "origin_node",
    "reached", "max_hop", "severed", "activated",
    "entropy", "entropy_delta",
    "n_clusters", "cluster_mean_size",
    "cluster_births", "cluster_deaths", "cluster_reformations",
    "homeostatic", "proto_memory",
    "plastic_nodes", "rewire_attempts", "rewire_successes",
    "hardened_links", "hardened_formed",
    "resistance_mean", "resistance_max", "resistance_rising",
    "alive_nodes", "alive_links",
    "k_star", "physics_seconds",
]

MULTI_FIELDS = [
    "wave_number", "amplitude",
    "reached", "max_hop", "severed", "activated",
    "n_clusters", "cluster_births", "cluster_deaths", "cluster_reformations",
    "homeostatic", "proto_memory",
    "plastic_nodes", "mean_plasticity",
    "rewire_attempts", "rewire_successes",
    "hardened_links", "hardened_formed", "mean_hardening",
    "resistance_mean", "resistance_max", "resistance_rising",
    "alive_links", "entropy",
    "k_star", "physics_seconds",
]


# ================================================================
# SINGLE-WAVE CALIBRATION (v4.1-compatible baseline)
# ================================================================
def run_single_calibration(seed, amplitudes, wave_params, plasticity_params,
                           window_steps, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.2 Single-Wave Calibration")
    print(f"  seed={seed} amplitudes={amplitudes}")
    print(f"  plasticity_factor={plasticity_params.plasticity_factor}")
    print(f"  hardening_bonus={plasticity_params.hardening_bonus}\n")

    csv_path = output_dir / f"single_seed{seed}.csv"
    csv_file = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=SINGLE_FIELDS)
    writer.writeheader()

    for i, amp in enumerate(amplitudes):
        print(f"  [{i+1}/{len(amplitudes)}] A0={amp:.2f}", flush=True)

        engine = V42Engine(seed=seed, wave_params=wave_params,
                           plasticity_params=plasticity_params)
        print(f"    Injection...", flush=True)
        engine.run_injection()

        side = int(math.ceil(math.sqrt(engine.N)))
        center = (side // 2) * side + (side // 2)
        origin = [center]

        t0 = time.time()
        frame = engine.step_window(amp, origin_nodes=origin, steps=window_steps)
        phys_sec = time.time() - t0

        row = {
            "amplitude": amp, "origin_node": origin[0],
            "reached": frame.wave_nodes_reached,
            "max_hop": frame.wave_max_hop,
            "severed": frame.wave_links_severed,
            "activated": frame.wave_links_activated,
            "entropy": round(frame.entropy, 4),
            "entropy_delta": round(frame.entropy_delta, 4),
            "n_clusters": frame.n_clusters,
            "cluster_mean_size": frame.cluster_mean_size,
            "cluster_births": frame.cluster_births,
            "cluster_deaths": frame.cluster_deaths,
            "cluster_reformations": frame.cluster_reformations,
            "homeostatic": frame.homeostatic_count,
            "proto_memory": frame.proto_memory_count,
            "plastic_nodes": frame.plastic_nodes_count,
            "rewire_attempts": frame.rewire_attempts,
            "rewire_successes": frame.rewire_successes,
            "hardened_links": frame.hardened_links_count,
            "hardened_formed": frame.hardened_links_formed_this_window,
            "resistance_mean": round(frame.resistance_mean, 6),
            "resistance_max": round(frame.resistance_max, 6),
            "resistance_rising": frame.resistance_rising_count,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "k_star": frame.k_star,
            "physics_seconds": round(phys_sec, 1),
        }
        writer.writerow(row)
        csv_file.flush()

        print(f"    sev={frame.wave_links_severed} "
              f"plastic={frame.plastic_nodes_count} "
              f"rewire={frame.rewire_successes} "
              f"hardened={frame.hardened_links_count} "
              f"clusters={frame.n_clusters} "
              f"resist={frame.resistance_mean:.4f} "
              f"({phys_sec:.0f}s)")

    csv_file.close()
    print(f"\n  CSV: {csv_path}\n")


# ================================================================
# MULTI-WAVE CALIBRATION (v4.2 core test)
# ================================================================
def run_multi_calibration(seed, amplitude, n_waves, wave_params,
                          plasticity_params, window_steps, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.2 Multi-Wave Adaptive Dynamics Test")
    print(f"  seed={seed} amplitude={amplitude} waves={n_waves}")
    print(f"  plasticity_factor={plasticity_params.plasticity_factor}")
    print(f"  hardening_bonus={plasticity_params.hardening_bonus}")
    print(f"  hardening_decay={plasticity_params.hardening_decay}\n")

    engine = V42Engine(seed=seed, wave_params=wave_params,
                       plasticity_params=plasticity_params)
    print(f"  Injection...", flush=True)
    engine.run_injection()

    csv_path = output_dir / f"multi_seed{seed}_A{amplitude}.csv"
    csv_file = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=MULTI_FIELDS)
    writer.writeheader()

    print(f"\n  {'wave':>4} {'sev':>4} {'plast':>5} {'rewire':>6} "
          f"{'harden':>6} {'h_new':>5} {'clust':>5} {'reform':>6} "
          f"{'resist':>7} {'r_rise':>6} {'links':>5}")
    print(f"  {'-'*72}")

    for w in range(n_waves):
        t0 = time.time()
        frame = engine.step_window(amplitude, steps=window_steps)
        phys_sec = time.time() - t0

        row = {
            "wave_number": w + 1, "amplitude": amplitude,
            "reached": frame.wave_nodes_reached,
            "max_hop": frame.wave_max_hop,
            "severed": frame.wave_links_severed,
            "activated": frame.wave_links_activated,
            "n_clusters": frame.n_clusters,
            "cluster_births": frame.cluster_births,
            "cluster_deaths": frame.cluster_deaths,
            "cluster_reformations": frame.cluster_reformations,
            "homeostatic": frame.homeostatic_count,
            "proto_memory": frame.proto_memory_count,
            "plastic_nodes": frame.plastic_nodes_count,
            "mean_plasticity": round(frame.mean_plasticity, 4),
            "rewire_attempts": frame.rewire_attempts,
            "rewire_successes": frame.rewire_successes,
            "hardened_links": frame.hardened_links_count,
            "hardened_formed": frame.hardened_links_formed_this_window,
            "mean_hardening": round(frame.mean_hardening, 4),
            "resistance_mean": round(frame.resistance_mean, 6),
            "resistance_max": round(frame.resistance_max, 6),
            "resistance_rising": frame.resistance_rising_count,
            "alive_links": frame.alive_links,
            "entropy": round(frame.entropy, 4),
            "k_star": frame.k_star,
            "physics_seconds": round(phys_sec, 1),
        }
        writer.writerow(row)
        csv_file.flush()

        print(f"  {w+1:>4} {frame.wave_links_severed:>4} "
              f"{frame.plastic_nodes_count:>5} "
              f"{frame.rewire_successes:>6} "
              f"{frame.hardened_links_count:>6} "
              f"{frame.hardened_links_formed_this_window:>5} "
              f"{frame.n_clusters:>5} "
              f"{frame.cluster_reformations:>6} "
              f"{frame.resistance_mean:>7.4f} "
              f"{frame.resistance_rising_count:>6} "
              f"{frame.alive_links:>5}")

    csv_file.close()

    # Summary
    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed}, A0={amplitude}, {n_waves} waves)")
    print(f"  {'='*60}")
    frames = engine.frames
    print(f"  Total links severed:  {sum(f.wave_links_severed for f in frames)}")
    print(f"  Total rewire success: {sum(f.rewire_successes for f in frames)}")
    print(f"  Total hardened formed:{sum(f.hardened_links_formed_this_window for f in frames)}")
    print(f"  Final hardened links: {frames[-1].hardened_links_count}")
    print(f"  Final clusters:       {frames[-1].n_clusters}")
    print(f"  Total reformations:   {sum(f.cluster_reformations for f in frames)}")
    print(f"  Final resistance:     {frames[-1].resistance_mean:.6f}")
    print(f"  Resistance trend:     "
          f"{frames[0].resistance_mean:.6f} → {frames[-1].resistance_mean:.6f}")
    print(f"  Final alive_links:    {frames[-1].alive_links}")
    print(f"  CSV: {csv_path}\n")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.2 Adaptive Dynamics Calibration")
    parser.add_argument("--mode", choices=["single", "multi"],
                        default="multi")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--seeds", type=int, nargs="+", default=None,
                        help="Multiple seeds (multi mode)")
    parser.add_argument("--amplitude", type=float, default=1.0,
                        help="Wave amplitude for multi mode")
    parser.add_argument("--amplitudes", type=float, nargs="+",
                        default=[0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
                        help="Amplitude sweep for single mode")
    parser.add_argument("--waves", type=int, default=10,
                        help="Number of waves for multi mode")
    parser.add_argument("--window-steps", type=int, default=WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v42")

    # Wave params
    parser.add_argument("--decay-lambda", type=float, default=0.5)
    parser.add_argument("--destruct-thr", type=float, default=0.3)
    parser.add_argument("--activ-thr", type=float, default=0.05)

    # Plasticity params
    parser.add_argument("--plasticity-factor", type=float, default=1.3)
    parser.add_argument("--hardening-bonus", type=float, default=0.15)
    parser.add_argument("--hardening-decay", type=float, default=0.005)
    parser.add_argument("--rewire-radius", type=int, default=2)

    args = parser.parse_args()

    wave_params = WaveParams(
        decay_lambda=args.decay_lambda,
        destruction_threshold=args.destruct_thr,
        activation_threshold=args.activ_thr,
    )
    plasticity_params = PlasticityParams(
        plasticity_factor=args.plasticity_factor,
        hardening_bonus=args.hardening_bonus,
        hardening_decay=args.hardening_decay,
        rewire_radius=args.rewire_radius,
    )

    if args.mode == "single":
        run_single_calibration(
            seed=args.seed,
            amplitudes=args.amplitudes,
            wave_params=wave_params,
            plasticity_params=plasticity_params,
            window_steps=args.window_steps,
            output_dir=args.output,
        )
    else:
        seeds = args.seeds or [args.seed]
        for seed in seeds:
            run_multi_calibration(
                seed=seed,
                amplitude=args.amplitude,
                n_waves=args.waves,
                wave_params=wave_params,
                plasticity_params=plasticity_params,
                window_steps=args.window_steps,
                output_dir=args.output,
            )


if __name__ == "__main__":
    main()
