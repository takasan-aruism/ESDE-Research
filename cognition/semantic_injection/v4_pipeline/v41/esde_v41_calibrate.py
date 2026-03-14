#!/usr/bin/env python3
"""
ESDE v4.1 — Wave Response Calibration
=======================================
Phase : v4.1 Calibration (GPT Audit Task §3)
Role  : Claude (Implementation)

Sweep wave amplitude at fixed seed / fixed origin node to produce
the wave response curve before behavioral experiments.

Records per-amplitude: reached, severed, activated, entropy_delta,
cluster_birth, cluster_death, reformation, homeostasis.

Also logs pre/post topology snapshots per GPT §5.

USAGE
-----
  python esde_v41_calibrate.py
  python esde_v41_calibrate.py --seed 1 --amplitudes 0.1 0.5 1.0 2.0
  python esde_v41_calibrate.py --window-steps 100
"""

import sys, csv, json, time, argparse
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v41_engine import V41Engine, WaveParams, WINDOW


# ================================================================
# METRIC DEFINITIONS (GPT Audit §2)
# ================================================================
METRIC_DEFINITIONS = {
    "reached":      "Number of alive nodes that received the wave arrival event (BFS visited).",
    "max_hop":      "Maximum graph hop distance reached by the wave from origin.",
    "severed":      "Number of active links broken because A_eff exceeded destruction_threshold.",
    "activated":    "Number of inactive (latent) links whose binding probability was boosted "
                    "because A_eff was in [activation_threshold, destruction_threshold].",
    "clusters":     "Number of connected components with >= 3 nodes at S >= 0.20.",
    "cluster_birth":"Number of new clusters that appeared this window (no overlap with prior clusters).",
    "cluster_death":"Number of prior clusters that vanished this window (no overlap with current).",
    "reformation":  "Number of clusters that died in a previous window but reappeared (overlap >= 50%).",
    "homeostasis":  "Number of active clusters with reformation_count >= 2.",
    "proto_memory": "Number of active clusters persisting >= 2x average cluster lifetime or >= 5 windows.",
    "entropy":      "Shannon entropy of chemistry-3 node distribution across 4 observer regions.",
    "entropy_delta":"Change in entropy from previous window.",
}


# ================================================================
# CALIBRATION SWEEP
# ================================================================
DEFAULT_AMPLITUDES = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]

LOG_FIELDS = [
    "amplitude", "origin_node",
    "reached", "max_hop", "severed", "activated",
    "entropy", "entropy_delta",
    "n_clusters", "cluster_mean_size",
    "cluster_births", "cluster_deaths",
    "cluster_reformations", "homeostatic", "proto_memory",
    "alive_nodes", "alive_links",
    "k_star", "divergence",
    "physics_seconds",
]


def run_calibration(seed, amplitudes, window_steps, output_dir,
                    wave_params=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.1 Wave Response Calibration")
    print(f"  seed={seed} amplitudes={amplitudes}")
    print(f"  window_steps={window_steps}")
    print(f"  output={output_dir}/\n")

    # Print metric definitions
    print(f"  {'='*60}")
    print(f"  METRIC DEFINITIONS")
    print(f"  {'='*60}")
    for name, defn in METRIC_DEFINITIONS.items():
        print(f"    {name:16s}: {defn}")
    print()

    # Initialize engine ONCE — fresh per amplitude
    # (each amplitude gets its own engine to isolate effects)
    csv_path = output_dir / f"calibration_seed{seed}.csv"
    csv_file = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=LOG_FIELDS)
    writer.writeheader()

    snapshots = {}

    for i, amp in enumerate(amplitudes):
        print(f"  [{i+1}/{len(amplitudes)}] A0={amp:.2f}", flush=True)

        # Fresh engine per amplitude (isolation)
        engine = V41Engine(seed=seed, wave_params=wave_params or WaveParams())
        print(f"    Injection...", flush=True)
        engine.run_injection()

        # Fix origin: first alive node (deterministic for given seed)
        origin = [sorted(engine.state.alive_n)[0]]
        print(f"    Origin node: {origin[0]}")

        # Pre-wave snapshot
        pre_alive_n = len(engine.state.alive_n)
        pre_alive_l = len(engine.state.alive_l)

        # Step
        print(f"    Physics + wave...", flush=True)
        t0 = time.time()
        frame = engine.step_window(amp, origin_nodes=origin, steps=window_steps)
        phys_sec = time.time() - t0

        # Log
        row = {
            "amplitude": amp,
            "origin_node": origin[0],
            "reached": frame.wave_nodes_reached,
            "max_hop": frame.wave_max_hop,
            "severed": frame.wave_links_severed,
            "activated": frame.wave_links_activated,
            "entropy": frame.entropy,
            "entropy_delta": frame.entropy_delta,
            "n_clusters": frame.n_clusters,
            "cluster_mean_size": frame.cluster_mean_size,
            "cluster_births": frame.cluster_births,
            "cluster_deaths": frame.cluster_deaths,
            "cluster_reformations": frame.cluster_reformations,
            "homeostatic": frame.homeostatic_count,
            "proto_memory": frame.proto_memory_count,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "k_star": frame.k_star,
            "divergence": int(frame.divergence),
            "physics_seconds": round(phys_sec, 1),
        }
        writer.writerow(row)
        csv_file.flush()

        # Snapshot (GPT §5)
        snapshots[amp] = {
            "pre": {"alive_nodes": pre_alive_n, "alive_links": pre_alive_l},
            "post": {"alive_nodes": frame.alive_nodes, "alive_links": frame.alive_links},
            "wave": {
                "origin": origin[0],
                "amplitude": amp,
                "reached": frame.wave_nodes_reached,
                "max_hop": frame.wave_max_hop,
                "severed": frame.wave_links_severed,
                "activated": frame.wave_links_activated,
            },
            "clusters": {
                "n": frame.n_clusters,
                "births": frame.cluster_births,
                "deaths": frame.cluster_deaths,
                "reformations": frame.cluster_reformations,
            },
        }

        print(f"    reached={frame.wave_nodes_reached} "
              f"severed={frame.wave_links_severed} "
              f"activated={frame.wave_links_activated} "
              f"clusters={frame.n_clusters} "
              f"ent={frame.entropy:.4f} "
              f"({phys_sec:.0f}s)")

    csv_file.close()

    # Save snapshots
    snap_path = output_dir / f"snapshots_seed{seed}.json"
    with open(snap_path, "w") as f:
        json.dump(snapshots, f, indent=2)

    # Print summary table
    print(f"\n  {'='*80}")
    print(f"  WAVE RESPONSE CURVE (seed={seed})")
    print(f"  {'='*80}")
    print(f"  {'A0':>6} {'reach':>6} {'hop':>4} {'sever':>6} {'activ':>6} "
          f"{'clust':>6} {'birth':>6} {'death':>6} {'reform':>6} "
          f"{'ent':>7} {'Δent':>7} {'links':>6}")

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            print(f"  {float(r['amplitude']):>6.2f} "
                  f"{r['reached']:>6} {r['max_hop']:>4} "
                  f"{r['severed']:>6} {r['activated']:>6} "
                  f"{r['n_clusters']:>6} {r['cluster_births']:>6} "
                  f"{r['cluster_deaths']:>6} {r['cluster_reformations']:>6} "
                  f"{float(r['entropy']):>7.4f} {float(r['entropy_delta']):>+7.4f} "
                  f"{r['alive_links']:>6}")

    print(f"\n  CSV: {csv_path}")
    print(f"  Snapshots: {snap_path}")
    print(f"  Done.\n")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.1 Wave Response Calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--amplitudes", type=float, nargs="+",
                        default=DEFAULT_AMPLITUDES)
    parser.add_argument("--window-steps", type=int, default=WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v41")
    # Wave params
    parser.add_argument("--decay-lambda", type=float, default=0.5)
    parser.add_argument("--destruct-thr", type=float, default=0.3)
    parser.add_argument("--activ-thr", type=float, default=0.05)
    args = parser.parse_args()

    wave_params = WaveParams(
        decay_lambda=args.decay_lambda,
        destruction_threshold=args.destruct_thr,
        activation_threshold=args.activ_thr,
    )

    run_calibration(
        seed=args.seed,
        amplitudes=args.amplitudes,
        wave_params=wave_params,
        window_steps=args.window_steps,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
