#!/usr/bin/env python3
"""
ESDE v4.3 — Encapsulation & Inner Topology Calibration
========================================================
Role  : Claude (Implementation)

Runs N windows of steady physics + semantic pressure.
Tracks milestone progression toward encapsulation + inner motifs.

USAGE
-----
  # Quick sanity (5 windows)
  python esde_v43_calibrate.py --windows 5 --seed 42

  # Standard run (25 windows = 1 full quiet phase equivalent)
  python esde_v43_calibrate.py --windows 25 --seed 42

  # Multi-seed sweep
  parallel -j 6 python esde_v43_calibrate.py --windows 25 --seed {1} \
    ::: 42 123 456 789 2024 7
"""

import sys, csv, json, time, argparse
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v43_engine import (
    V43Engine, V43StateFrame,
    SemanticPressureParams, EncapsulationParams, MotifParams,
    WINDOW,
)

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "n_encapsulated", "n_candidates",
    "mean_cluster_size", "max_cluster_size",
    "mean_density_ratio", "max_density_ratio",
    "encap_events_total", "dissolve_events_total",
    "mean_inner_entropy", "max_inner_entropy",
    "total_inner_triangles", "motif_recurrence_count",
    "pressure_events", "nodes_shielded",
    "hardened_links_count", "mean_hardening",
    "k_star", "entropy", "entropy_delta",
    "milestone", "physics_seconds",
]


def run_calibration(seed, n_windows, window_steps, output_dir,
                    pressure_params=None, encap_params=None,
                    motif_params=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.3 Encapsulation Calibration")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")

    engine = V43Engine(
        seed=seed,
        pressure_params=pressure_params,
        encap_params=encap_params,
        motif_params=motif_params,
    )
    print(f"  Injection...", flush=True)
    engine.run_injection()

    csv_path = output_dir / f"v43_seed{seed}.csv"
    csv_file = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=LOG_FIELDS)
    writer.writeheader()

    print(f"\n  {'win':>4} {'clust':>5} {'encap':>5} {'cand':>4} "
          f"{'maxSz':>5} {'maxDR':>6} {'inEnt':>6} {'tri':>4} "
          f"{'motif':>5} {'links':>5} {'M':>2} {'sec':>5}")
    print(f"  {'-'*68}")

    max_milestone = 0

    for w in range(n_windows):
        frame = engine.step_window(steps=window_steps)

        if frame.milestone > max_milestone:
            max_milestone = frame.milestone

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": frame.n_clusters,
            "n_encapsulated": frame.n_encapsulated,
            "n_candidates": frame.n_candidates,
            "mean_cluster_size": frame.mean_cluster_size,
            "max_cluster_size": frame.max_cluster_size,
            "mean_density_ratio": frame.mean_density_ratio,
            "max_density_ratio": frame.max_density_ratio,
            "encap_events_total": frame.encap_events_total,
            "dissolve_events_total": frame.dissolve_events_total,
            "mean_inner_entropy": frame.mean_inner_entropy,
            "max_inner_entropy": frame.max_inner_entropy,
            "total_inner_triangles": frame.total_inner_triangles,
            "motif_recurrence_count": frame.motif_recurrence_count,
            "pressure_events": frame.pressure_events,
            "nodes_shielded": frame.nodes_shielded,
            "hardened_links_count": frame.hardened_links_count,
            "mean_hardening": frame.mean_hardening,
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "entropy_delta": round(frame.entropy_delta, 4),
            "milestone": frame.milestone,
            "physics_seconds": frame.physics_seconds,
        }
        writer.writerow(row)
        csv_file.flush()

        flag = " ★" if frame.milestone > (
            engine.frames[-2].milestone if len(engine.frames) > 1 else 0) else ""
        print(f"  {frame.window:>4} {frame.n_clusters:>5} "
              f"{frame.n_encapsulated:>5} {frame.n_candidates:>4} "
              f"{frame.max_cluster_size:>5} {frame.max_density_ratio:>6.1f} "
              f"{frame.mean_inner_entropy:>6.3f} "
              f"{frame.total_inner_triangles:>4} "
              f"{frame.motif_recurrence_count:>5} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>2}{flag} "
              f"{frame.physics_seconds:>5.0f}")

    csv_file.close()

    # Summary
    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed}, {n_windows} windows)")
    print(f"  {'='*60}")
    print(f"  Max milestone reached: M{max_milestone}")
    print(f"  Final clusters:     {engine.frames[-1].n_clusters}")
    print(f"  Final encapsulated: {engine.frames[-1].n_encapsulated}")
    print(f"  Total encap events: {engine.frames[-1].encap_events_total}")
    print(f"  Total dissolve:     {engine.frames[-1].dissolve_events_total}")
    print(f"  Final alive_links:  {engine.frames[-1].alive_links}")
    print(f"  Final inner tri:    {engine.frames[-1].total_inner_triangles}")
    print(f"  Motif recurrence:   {engine.frames[-1].motif_recurrence_count}")
    print(f"  CSV: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.3 Encapsulation Calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=25)
    parser.add_argument("--window-steps", type=int, default=WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v43")
    # Encapsulation
    parser.add_argument("--ratio-thr", type=float, default=3.0)
    parser.add_argument("--dissolve-thr", type=float, default=1.5)
    parser.add_argument("--min-persist", type=int, default=3)
    # Pressure
    parser.add_argument("--pressure-prob", type=float, default=0.005)
    parser.add_argument("--pressure-strength", type=float, default=0.03)
    args = parser.parse_args()

    pp = SemanticPressureParams(
        pressure_prob=args.pressure_prob,
        pressure_strength=args.pressure_strength,
    )
    ep = EncapsulationParams(
        ratio_threshold=args.ratio_thr,
        dissolution_threshold=args.dissolve_thr,
        min_persistence=args.min_persist,
    )

    run_calibration(
        seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        pressure_params=pp, encap_params=ep,
    )


if __name__ == "__main__":
    main()
