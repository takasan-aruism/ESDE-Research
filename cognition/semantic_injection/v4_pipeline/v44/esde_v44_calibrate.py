#!/usr/bin/env python3
"""
ESDE v4.4 — Whirlpool Identity Calibration
=============================================
High-speed observation (50-step windows) with spatial identity tracking.

USAGE
-----
  python esde_v44_calibrate.py --seed 42
  parallel -j 5 python esde_v44_calibrate.py --seed {1} ::: 42 123 456 789 2024
"""

import sys, csv, time, argparse
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v44_engine import V44Engine, V44_WINDOW, EncapsulationParams

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "n_encapsulated", "n_candidates",
    "max_size", "max_density_ratio", "max_seen_count",
    "mean_inner_entropy", "max_inner_entropy",
    "total_inner_triangles", "motif_recurrence_count",
    "encap_events_total", "dissolve_events_total",
    "hardened_links_count", "k_star", "entropy", "entropy_delta",
    "milestone", "physics_seconds",
]


def run(seed, n_windows, window_steps, output_dir, island_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.4 Whirlpool Identity Calibration")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  whirlpool_hops={island_params.whirlpool_hops}")
    print(f"  Injection...", flush=True)

    engine = V44Engine(seed=seed, island_params=island_params)
    engine.run_injection()

    csv_path = output_dir / f"v44_seed{seed}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    print(f"\n  {'win':>4} {'clust':>5} {'encap':>5} {'cand':>4} "
          f"{'maxSz':>5} {'maxDR':>6} {'seen':>4} "
          f"{'inEnt':>5} {'tri':>3} {'motif':>5} "
          f"{'links':>5} {'M':>1} {'sec':>5}")
    print(f"  {'-'*72}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        # Get tracker summary for v4.4-specific fields
        isum = engine.island_tracker._summary()
        max_ms = max(max_ms, frame.milestone)
        hc = len(engine.hardening)

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": isum["n_clusters"],
            "n_encapsulated": isum["n_encapsulated"],
            "n_candidates": isum["n_candidates"],
            "max_size": isum["max_size"],
            "max_density_ratio": isum["max_density_ratio"],
            "max_seen_count": isum["max_seen_count"],
            "mean_inner_entropy": isum["mean_inner_entropy"],
            "max_inner_entropy": isum["max_inner_entropy"],
            "total_inner_triangles": isum["total_inner_tri"],
            "motif_recurrence_count": isum["motif_recurrence"],
            "encap_events_total": isum["encap_events"],
            "dissolve_events_total": isum["dissolve_events"],
            "hardened_links_count": hc,
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "entropy_delta": round(frame.entropy_delta, 4),
            "milestone": frame.milestone,
            "physics_seconds": round(sec, 1),
        }
        writer.writerow(row)
        f.flush()

        print(f"  {frame.window:>4} {isum['n_clusters']:>5} "
              f"{isum['n_encapsulated']:>5} {isum['n_candidates']:>4} "
              f"{isum['max_size']:>5} "
              f"{isum['max_density_ratio']:>6.2f} "
              f"{isum['max_seen_count']:>4} "
              f"{isum['mean_inner_entropy']:>5.2f} "
              f"{isum['total_inner_tri']:>3} "
              f"{isum['motif_recurrence']:>5} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>5.0f}")

    f.close()

    print(f"\n  {'='*50}")
    print(f"  SUMMARY (seed={seed})")
    print(f"  {'='*50}")
    frames = engine.frames
    print(f"  Highest milestone:    M{max_ms}")
    print(f"  Total encap events:   {engine.island_tracker.encapsulation_events}")
    print(f"  Total dissolutions:   {engine.island_tracker.dissolution_events}")
    print(f"  Max seen_count:       {isum['max_seen_count']}")
    print(f"  Final alive_links:    {frames[-1].alive_links}")
    print(f"  CSV: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.4 Whirlpool Calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=100)
    parser.add_argument("--window-steps", type=int, default=V44_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v44")
    parser.add_argument("--whirlpool-hops", type=int, default=2)
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    args = parser.parse_args()

    params = EncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        whirlpool_hops=args.whirlpool_hops,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        island_params=params)


if __name__ == "__main__":
    main()
