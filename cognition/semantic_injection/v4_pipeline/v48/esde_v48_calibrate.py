#!/usr/bin/env python3
"""
ESDE v4.8 — Terrain Genesis Calibration
==========================================
Density-dependent cooling + v4.6 dynamic identity + motif scanner.
No accretion. Focus on macro-structure emergence.

USAGE
-----
  # Sanity
  python esde_v48_calibrate.py --seed 42 --windows 10

  # Standard
  parallel -j 2 python esde_v48_calibrate.py --seed {1} --windows 200 \
    ::: 42 123

  # Cooling sweep
  parallel -j 3 python esde_v48_calibrate.py --seed 42 --windows 100 \
    --cooling-strength {1} ::: 0.5 1.0 2.0 5.0

  # Aggregate
  python esde_v48_calibrate.py --aggregate --output calibration_v48
"""

import sys, csv, json, time, argparse
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v48_engine import V48Engine, V48EncapsulationParams, V48_WINDOW

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
    # v4.5a: P/D
    "pd_p_count", "pd_d_count", "pd_both_count",
    # v4.5a: Boundary resonance (retained for observability under cooling)
    "resonant_incorporations", "dissonant_incorporations",
    "resonant_rejections", "dissonant_rejections",
    "resonance_total_events", "resonance_ratio",
    # v4.5a: Personality
    "personalities_recorded",
    # v4.6: Dynamic identity
    "max_relaxed_lifespan", "max_strict_lifespan",
    "identity_stable", "identity_drift",
    "identity_new", "identity_reformation",
    "mean_jaccard",
    # v4.6: Motifs
    "motif_alpha", "motif_beta", "motif_gamma",
    # v4.8: Cooling (NEW)
    "cooled_nodes", "mean_cooling_factor",
]


def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.8 Terrain Genesis Calibration")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  cooling: strength={encap_params.cooling_strength} "
          f"s_thr={encap_params.cooling_s_threshold} "
          f"enabled={encap_params.cooling_enabled}")
    print(f"  jaccard_thr={encap_params.jaccard_threshold}")
    print(f"  Injection...", flush=True)

    engine = V48Engine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    csv_path = output_dir / f"v48_seed{seed}_c{encap_params.cooling_strength}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    print(f"\n  {'win':>4} {'clst':>4} {'mxSz':>4} {'rLif':>4} "
          f"{'mxDR':>5} {'drft':>4} {'mJac':>5} "
          f"{'cool':>4} {'mCF':>5} "
          f"{'aM':>2} {'bM':>2} {'gM':>2} "
          f"{'PD':>2} {'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*80}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.last_isum  # cached from step_window, no redundant _summary()
        cs = engine.cooling_stats
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
            # v4.5a
            "max_lifespan": isum["max_lifespan"],
            "mean_continuity": isum["mean_continuity"],
            "max_continuity": isum["max_continuity"],
            "mean_turnover_rate": isum["mean_turnover_rate"],
            "pd_p_count": isum["pd_p_count"],
            "pd_d_count": isum["pd_d_count"],
            "pd_both_count": isum["pd_both_count"],
            # v4.5a resonance (retained for observability)
            "resonant_incorporations": isum["resonant_incorporations"],
            "dissonant_incorporations": isum["dissonant_incorporations"],
            "resonant_rejections": isum["resonant_rejections"],
            "dissonant_rejections": isum["dissonant_rejections"],
            "resonance_total_events": isum["resonance_total_events"],
            "resonance_ratio": isum["resonance_ratio"],
            "personalities_recorded": isum["personalities_recorded"],
            # v4.6
            "max_relaxed_lifespan": isum["max_relaxed_lifespan"],
            "max_strict_lifespan": isum["max_strict_lifespan"],
            "identity_stable": isum["identity_stable"],
            "identity_drift": isum["identity_drift"],
            "identity_new": isum["identity_new"],
            "identity_reformation": isum["identity_reformation"],
            "mean_jaccard": isum["mean_jaccard"],
            "motif_alpha": isum["motif_alpha"],
            "motif_beta": isum["motif_beta"],
            "motif_gamma": isum["motif_gamma"],
            # v4.8
            "cooled_nodes": cs.get("cooled_nodes", 0),
            "mean_cooling_factor": cs.get("mean_cooling_factor", 1.0),
        }
        writer.writerow(row)
        f.flush()

        print(f"  {frame.window:>4} {isum['n_clusters']:>4} "
              f"{isum['max_size']:>4} "
              f"{isum['max_relaxed_lifespan']:>4} "
              f"{isum['max_density_ratio']:>5.2f} "
              f"{isum['identity_drift']:>4} "
              f"{isum['mean_jaccard']:>5.2f} "
              f"{cs.get('cooled_nodes',0):>4} "
              f"{cs.get('mean_cooling_factor',1.0):>5.3f} "
              f"{isum['motif_alpha']:>2} "
              f"{isum['motif_beta']:>2} "
              f"{isum['motif_gamma']:>2} "
              f"{isum['pd_both_count']:>2} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}")

    f.close()

    # JSON
    json_path = output_dir / f"v48_seed{seed}_c{encap_params.cooling_strength}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "seed": seed, "n_windows": n_windows,
        "window_steps": window_steps,
        "cooling_strength": encap_params.cooling_strength,
        "final_alive_links": engine.frames[-1].alive_links if engine.frames else 0,
        "max_milestone": max_ms,
        "max_relaxed_lifespan": isum["max_relaxed_lifespan"],
        "max_strict_lifespan": isum["max_strict_lifespan"],
        "max_cluster_size": max(int(fr.max_cluster_size) for fr in engine.frames),
    }
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed}, cooling={encap_params.cooling_strength})")
    print(f"  {'='*60}")
    print(f"  Max relaxed lifespan:   {isum['max_relaxed_lifespan']}")
    print(f"  Max strict lifespan:    {isum['max_strict_lifespan']}")
    print(f"  Max cluster size:       {max(int(fr.max_cluster_size) for fr in engine.frames)}")
    print(f"  Cooled nodes (last):    {cs.get('cooled_nodes', 0)}")
    print(f"  Mean cooling factor:    {cs.get('mean_cooling_factor', 1.0):.4f}")
    print(f"  Personalities:          {isum['personalities_recorded']}")
    print(f"  Motifs (last): a={isum['motif_alpha']} b={isum['motif_beta']} g={isum['motif_gamma']}")
    print(f"  P/D both (cum):         "
          f"{sum(1 for e in engine.island_tracker.pd_events if e['is_P'] and e['is_D'])}")
    print(f"  Final alive_links:      "
          f"{engine.frames[-1].alive_links if engine.frames else 0}")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


def aggregate(output_dir):
    output_dir = Path(output_dir)
    json_files = sorted(output_dir.glob("v48_seed*_detail.json"))
    if not json_files:
        print(f"  No v4.8 JSON files in {output_dir}")
        return

    print(f"\n  {'='*75}")
    print(f"  ESDE v4.8 — Aggregate ({len(json_files)} runs)")
    print(f"  {'='*75}")

    print(f"\n  {'seed':>6} {'cool':>5} {'rLife':>5} {'sLife':>5} "
          f"{'mxSize':>6} {'links':>5} {'pers':>4} {'PD':>3}")
    print(f"  {'-'*50}")
    for jf in json_files:
        with open(jf) as fh:
            d = json.load(fh)
        m = d["meta"]
        pd = d.get("pd_convergence_summary", {})
        print(f"  {m['seed']:>6} {m['cooling_strength']:>5.1f} "
              f"{m['max_relaxed_lifespan']:>5} "
              f"{m['max_strict_lifespan']:>5} "
              f"{m['max_cluster_size']:>6} "
              f"{m['final_alive_links']:>5} "
              f"{len(d.get('personalities',{})):>4} "
              f"{pd.get('total_both_events',0):>3}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.8 Terrain Genesis Calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V48_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v48")
    # v4.8 cooling
    parser.add_argument("--cooling-strength", type=float, default=1.0)
    parser.add_argument("--cooling-s-thr", type=float, default=0.20)
    parser.add_argument("--no-cooling", action="store_true")
    # v4.6 identity
    parser.add_argument("--jaccard-thr", type=float, default=0.3)
    # v4.4 inherited
    parser.add_argument("--whirlpool-hops", type=int, default=2)
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    # Aggregate
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()

    if args.aggregate:
        aggregate(args.output)
        return

    params = V48EncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        whirlpool_hops=args.whirlpool_hops,
        jaccard_threshold=args.jaccard_thr,
        cooling_strength=args.cooling_strength,
        cooling_s_threshold=args.cooling_s_thr,
        cooling_enabled=not args.no_cooling,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()
