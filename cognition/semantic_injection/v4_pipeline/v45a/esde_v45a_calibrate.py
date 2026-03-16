#!/usr/bin/env python3
"""
ESDE v4.5a — Local Observer Logging Calibration
==================================================
Observation sweep with deformation-tolerant identity tracking,
personality signatures, boundary resonance logging, and P/D
paradox monitoring.

ZERO PHYSICS CHANGES. Logging-only upgrade over v4.4.

USAGE
-----
  # Quick sanity (10 windows)
  python esde_v45a_calibrate.py --seed 42 --windows 10

  # Standard sweep (10 seeds × 200 windows)
  parallel -j 5 python esde_v45a_calibrate.py --seed {1} --windows 200 \
    ::: 42 7 123 314 456 610 77 789 999 2024

  # Aggregate
  python esde_v45a_calibrate.py --aggregate --output calibration_v45a
"""

import sys, csv, json, time, argparse, glob
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v45a_engine import (
    V45aEngine, V45aEncapsulationParams, V45A_WINDOW,
)

# ================================================================
# CSV FIELDS
# ================================================================
# All v4.4 fields preserved + v4.5a additions
LOG_FIELDS = [
    # v4.4 baseline
    "window", "alive_nodes", "alive_links",
    "n_clusters", "n_encapsulated", "n_candidates",
    "max_size", "max_density_ratio", "max_seen_count",
    "mean_inner_entropy", "max_inner_entropy",
    "total_inner_triangles", "motif_recurrence_count",
    "encap_events_total", "dissolve_events_total",
    "hardened_links_count", "k_star", "entropy", "entropy_delta",
    "milestone", "physics_seconds",
    # v4.5a: Deformation
    "max_lifespan", "mean_continuity", "max_continuity",
    "mean_turnover_rate",
    # v4.5a: Boundary resonance
    "resonant_incorporations", "dissonant_incorporations",
    "resonant_rejections", "dissonant_rejections",
    "resonance_total_events", "resonance_ratio",
    # v4.5a: P/D paradox
    "pd_p_count", "pd_d_count", "pd_both_count",
    # v4.5a: Personality
    "personalities_recorded",
]


# ================================================================
# RUN
# ================================================================
def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.5a Local Observer Logging Calibration")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  resonance_thr={encap_params.resonance_threshold:.4f} "
          f"personality_trigger={encap_params.personality_trigger_seen} "
          f"whirlpool_hops={encap_params.whirlpool_hops}")
    print(f"  Injection...", flush=True)

    engine = V45aEngine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    csv_path = output_dir / f"v45a_seed{seed}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    # Header
    print(f"\n  {'win':>4} {'clust':>5} {'seen':>4} {'maxDR':>6} "
          f"{'cont':>5} {'life':>4} "
          f"{'resIn':>5} {'disIn':>5} {'ratio':>5} "
          f"{'P':>2} {'D':>2} {'PD':>2} "
          f"{'pers':>4} "
          f"{'links':>5} {'M':>1} {'sec':>5}")
    print(f"  {'-'*85}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.island_tracker._summary()
        max_ms = max(max_ms, frame.milestone)
        hc = len(engine.hardening)

        row = {
            # v4.4 baseline
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
            # v4.5a: Deformation
            "max_lifespan": isum["max_lifespan"],
            "mean_continuity": isum["mean_continuity"],
            "max_continuity": isum["max_continuity"],
            "mean_turnover_rate": isum["mean_turnover_rate"],
            # v4.5a: Resonance
            "resonant_incorporations": isum["resonant_incorporations"],
            "dissonant_incorporations": isum["dissonant_incorporations"],
            "resonant_rejections": isum["resonant_rejections"],
            "dissonant_rejections": isum["dissonant_rejections"],
            "resonance_total_events": isum["resonance_total_events"],
            "resonance_ratio": isum["resonance_ratio"],
            # v4.5a: P/D
            "pd_p_count": isum["pd_p_count"],
            "pd_d_count": isum["pd_d_count"],
            "pd_both_count": isum["pd_both_count"],
            # v4.5a: Personality
            "personalities_recorded": isum["personalities_recorded"],
        }
        writer.writerow(row)
        f.flush()

        # Console output
        print(f"  {frame.window:>4} {isum['n_clusters']:>5} "
              f"{isum['max_seen_count']:>4} "
              f"{isum['max_density_ratio']:>6.2f} "
              f"{isum['mean_continuity']:>5.2f} "
              f"{isum['max_lifespan']:>4} "
              f"{isum['resonant_incorporations']:>5} "
              f"{isum['dissonant_incorporations']:>5} "
              f"{isum['resonance_ratio']:>5.2f} "
              f"{isum['pd_p_count']:>2} "
              f"{isum['pd_d_count']:>2} "
              f"{isum['pd_both_count']:>2} "
              f"{isum['personalities_recorded']:>4} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>5.0f}")

    f.close()

    # ── JSON detailed report ──
    json_path = output_dir / f"v45a_seed{seed}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "seed": seed,
        "n_windows": n_windows,
        "window_steps": window_steps,
        "final_alive_links": engine.frames[-1].alive_links if engine.frames else 0,
        "max_milestone": max_ms,
        "max_seen_count": isum["max_seen_count"],
    }
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    # ── Summary ──
    print(f"\n  {'='*55}")
    print(f"  SUMMARY (seed={seed})")
    print(f"  {'='*55}")
    print(f"  Highest milestone:        M{max_ms}")
    print(f"  Max seen_count:           {isum['max_seen_count']}")
    print(f"  Max lifespan (deform):    {isum['max_lifespan']}")
    print(f"  Mean continuity:          {isum['mean_continuity']:.4f}")
    print(f"  Personalities recorded:   {isum['personalities_recorded']}")
    print(f"  Resonance events:         {isum['resonance_total_events']}")
    print(f"  Resonance ratio (in):     {isum['resonance_ratio']:.4f}")
    print(f"  P/D both (cumulative):    "
          f"{sum(1 for e in engine.island_tracker.pd_events if e['is_P'] and e['is_D'])}")
    print(f"  Final alive_links:        "
          f"{engine.frames[-1].alive_links if engine.frames else 0}")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


# ================================================================
# AGGREGATE
# ================================================================
def aggregate(output_dir):
    output_dir = Path(output_dir)
    csv_files = sorted(output_dir.glob("v45a_seed*.csv"))
    json_files = sorted(output_dir.glob("v45a_seed*_detail.json"))

    if not csv_files:
        print(f"  No v4.5a CSV files found in {output_dir}")
        return

    print(f"\n  {'='*65}")
    print(f"  ESDE v4.5a — Aggregate Summary ({len(csv_files)} seeds)")
    print(f"  {'='*65}")

    all_seeds = []
    for jf_path in json_files:
        with open(jf_path) as jf:
            detail = json.load(jf)
        seed = detail.get("meta", {}).get("seed", "?")
        max_seen = detail.get("meta", {}).get("max_seen_count", 0)
        final_links = detail.get("meta", {}).get("final_alive_links", 0)

        pd_summary = detail.get("pd_convergence_summary", {})
        n_both = pd_summary.get("total_both_events", 0)
        unique_both = pd_summary.get("unique_both_islands", 0)

        # Per-seed resonance aggregate
        res_all = detail.get("resonance_per_island", {})
        total_res_in = sum(v.get("resonant_in", 0) for v in res_all.values())
        total_dis_in = sum(v.get("dissonant_in", 0) for v in res_all.values())
        total_in = total_res_in + total_dis_in
        res_ratio = total_res_in / total_in if total_in > 0 else 0.0

        # Deformation
        deform = detail.get("deformation", {})
        lifespans = [v.get("lifespan_windows", 0) for v in deform.values()]
        continuities = [v.get("mean_continuity", 0) for v in deform.values()]

        # Personality
        n_pers = len(detail.get("personalities", {}))

        all_seeds.append({
            "seed": seed,
            "max_seen": max_seen,
            "final_links": final_links,
            "n_both": n_both,
            "unique_both": unique_both,
            "res_ratio": res_ratio,
            "total_incorporations": total_in,
            "max_lifespan": max(lifespans) if lifespans else 0,
            "mean_continuity": round(float(np.mean(continuities)), 4)
            if continuities else 0.0,
            "personalities": n_pers,
        })

    # Print table
    print(f"\n  {'seed':>6} {'seen':>4} {'links':>5} {'PD':>3} {'uPD':>3} "
          f"{'resR':>5} {'incorp':>6} {'life':>4} {'cont':>5} {'pers':>4}")
    print(f"  {'-'*55}")
    for s in all_seeds:
        print(f"  {s['seed']:>6} {s['max_seen']:>4} {s['final_links']:>5} "
              f"{s['n_both']:>3} {s['unique_both']:>3} "
              f"{s['res_ratio']:>5.2f} {s['total_incorporations']:>6} "
              f"{s['max_lifespan']:>4} {s['mean_continuity']:>5.2f} "
              f"{s['personalities']:>4}")

    # System-level summary
    print(f"\n  System-level:")
    all_res = [s["res_ratio"] for s in all_seeds if s["total_incorporations"] > 0]
    if all_res:
        print(f"    Mean resonance ratio:       "
              f"{np.mean(all_res):.4f} ± {np.std(all_res):.4f}")
    all_both = [s["n_both"] for s in all_seeds]
    print(f"    Seeds with P/D convergence: "
          f"{sum(1 for b in all_both if b > 0)}/{len(all_seeds)}")
    all_pers = [s["personalities"] for s in all_seeds]
    print(f"    Seeds with personality:     "
          f"{sum(1 for p in all_pers if p > 0)}/{len(all_seeds)}")
    all_life = [s["max_lifespan"] for s in all_seeds]
    print(f"    Max lifespan (deform):      {max(all_life) if all_life else 0}")
    all_cont = [s["mean_continuity"] for s in all_seeds
                if s["mean_continuity"] > 0]
    if all_cont:
        print(f"    Mean continuity:            "
              f"{np.mean(all_cont):.4f} ± {np.std(all_cont):.4f}")
    print()


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.5a Local Observer Logging Calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V45A_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v45a")
    # v4.4 inherited
    parser.add_argument("--whirlpool-hops", type=int, default=2)
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    # v4.5a specific
    parser.add_argument("--resonance-thr", type=float, default=0.7854,
                        help="Phase difference threshold for resonance (π/4)")
    parser.add_argument("--personality-trigger", type=int, default=3,
                        help="Record personality at seen_count >= N")
    # Aggregate mode
    parser.add_argument("--aggregate", action="store_true",
                        help="Aggregate results from output dir")
    args = parser.parse_args()

    if args.aggregate:
        aggregate(args.output)
        return

    params = V45aEncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        whirlpool_hops=args.whirlpool_hops,
        resonance_threshold=args.resonance_thr,
        personality_trigger_seen=args.personality_trigger,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()
