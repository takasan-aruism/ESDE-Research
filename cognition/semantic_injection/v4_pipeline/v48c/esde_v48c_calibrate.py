#!/usr/bin/env python3
"""
ESDE v4.8c — Axiomatic Parameter Discovery Calibration
=========================================================
Phase 1: Two gradient-relaxation loops (compound_restore, inert_penalty).
No target values. Update every 3 windows.

USAGE
-----
  # Sanity
  python esde_v48c_calibrate.py --seed 42 --windows 10

  # Standard
  parallel -j 2 python esde_v48c_calibrate.py --seed {1} --windows 200 \
    ::: 42 123

  # Ablation (drift disabled = static v4.8b)
  python esde_v48c_calibrate.py --seed 42 --windows 200 --no-drift

  # Aggregate
  python esde_v48c_calibrate.py --aggregate --output calibration_v48c
"""

import sys, csv, json, time, argparse
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v48c_engine import V48cEngine, V48cEncapsulationParams, V48C_WINDOW

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
    # v4.5a
    "max_lifespan", "mean_continuity", "max_continuity",
    "mean_turnover_rate",
    "pd_p_count", "pd_d_count", "pd_both_count",
    "resonant_incorporations", "dissonant_incorporations",
    "resonant_rejections", "dissonant_rejections",
    "resonance_total_events", "resonance_ratio",
    "personalities_recorded",
    # v4.6
    "max_relaxed_lifespan", "max_strict_lifespan",
    "identity_stable", "identity_drift",
    "identity_new", "identity_reformation",
    "mean_jaccard",
    "motif_alpha", "motif_beta", "motif_gamma",
    # v4.8
    "cooled_nodes", "mean_cooling_factor",
    # v4.8b
    "z_hardened", "z_softened", "z_tensioned",
    # v4.8c (axiomatic drift)
    "compound_restore", "inert_penalty",
    "delta_L", "delta_Z0", "drift_applied",
]


def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    drift_mode = "drift" if encap_params.drift_enabled else "static"
    init_restore = encap_params.z_decay_compound_restore
    init_inert = encap_params.z_decay_inert_penalty

    print(f"\n  ESDE v4.8c Axiomatic Parameter Discovery")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  mode={drift_mode} alpha={encap_params.drift_alpha} "
          f"interval={encap_params.drift_interval}")
    print(f"  init: restore={init_restore} inert={init_inert}")
    print(f"  Injection...", flush=True)

    engine = V48cEngine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    tag = f"v48c_seed{seed}_{drift_mode}"
    csv_path = output_dir / f"{tag}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    print(f"\n  {'win':>4} {'clst':>4} {'mxSz':>4} {'rLif':>4} "
          f"{'mxDR':>5} {'drft':>4} "
          f"{'rest':>7} {'iPen':>6} {'dL':>6} {'dZ0':>6} "
          f"{'gM':>2} {'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*80}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.last_isum
        assert isum, f"last_isum empty at window {w+1}"
        cs = engine.cooling_stats
        zs = engine.z_stats
        max_ms = max(max_ms, frame.milestone)
        hc = len(engine.hardening)

        # Current drift state
        traj = engine.drift_trajectory
        cur = traj[-1] if traj else {}
        cur_restore = cur.get("compound_restore", init_restore)
        cur_inert = cur.get("inert_penalty", init_inert)
        cur_dL = cur.get("delta_L", 0)
        cur_dZ0 = cur.get("delta_Z0", 0)
        cur_applied = cur.get("applied", False)

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
            # v4.8b
            "z_hardened": zs.get("hardened", 0),
            "z_softened": zs.get("softened", 0),
            "z_tensioned": zs.get("tensioned", 0),
            # v4.8c
            "compound_restore": cur_restore,
            "inert_penalty": cur_inert,
            "delta_L": cur_dL,
            "delta_Z0": cur_dZ0,
            "drift_applied": 1 if cur_applied else 0,
        }
        writer.writerow(row)
        f.flush()

        applied_mark = "*" if cur_applied else " "
        print(f"  {frame.window:>4} {isum['n_clusters']:>4} "
              f"{isum['max_size']:>4} "
              f"{isum['max_relaxed_lifespan']:>4} "
              f"{isum['max_density_ratio']:>5.2f} "
              f"{isum['identity_drift']:>4} "
              f"{cur_restore:>7.4f} {cur_inert:>6.4f} "
              f"{cur_dL:>6} {cur_dZ0:>6} "
              f"{isum['motif_gamma']:>2} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}{applied_mark}")

    f.close()

    # JSON
    json_path = output_dir / f"{tag}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "seed": seed, "n_windows": n_windows,
        "window_steps": window_steps,
        "drift_mode": drift_mode,
        "drift_alpha": encap_params.drift_alpha,
        "drift_interval": encap_params.drift_interval,
        "init_restore": init_restore,
        "init_inert": init_inert,
        "final_restore": cur_restore,
        "final_inert": cur_inert,
        "final_alive_links": frame.alive_links,
        "max_milestone": max_ms,
        "max_relaxed_lifespan": isum["max_relaxed_lifespan"],
        "max_cluster_size": max(int(fr.max_cluster_size) for fr in engine.frames),
    }
    detail["drift_trajectory"] = engine.drift_trajectory
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed}, {drift_mode})")
    print(f"  {'='*60}")
    print(f"  Init:  restore={init_restore}  inert={init_inert}")
    print(f"  Final: restore={cur_restore:.6f}  inert={cur_inert:.6f}")
    print(f"  Max relaxed lifespan:   {isum['max_relaxed_lifespan']}")
    print(f"  Max cluster size:       {max(int(fr.max_cluster_size) for fr in engine.frames)}")
    print(f"  Max milestone:          {max_ms}")
    print(f"  Final alive_links:      {frame.alive_links}")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


def aggregate(output_dir):
    output_dir = Path(output_dir)
    json_files = sorted(output_dir.glob("v48c_*_detail.json"))
    if not json_files:
        print(f"  No v4.8c JSON files in {output_dir}")
        return

    print(f"\n  {'='*80}")
    print(f"  ESDE v4.8c — Aggregate ({len(json_files)} runs)")
    print(f"  {'='*80}")

    print(f"\n  {'seed':>6} {'mode':>6} {'initR':>6} {'finR':>7} "
          f"{'initI':>6} {'finI':>7} "
          f"{'rLife':>5} {'mxSz':>5} {'links':>5} {'mxM':>3}")
    print(f"  {'-'*70}")
    for jf in json_files:
        with open(jf) as fh:
            d = json.load(fh)
        m = d["meta"]
        print(f"  {m['seed']:>6} {m['drift_mode']:>6} "
              f"{m['init_restore']:>6.3f} {m['final_restore']:>7.4f} "
              f"{m['init_inert']:>6.3f} {m['final_inert']:>7.4f} "
              f"{m['max_relaxed_lifespan']:>5} "
              f"{m['max_cluster_size']:>5} "
              f"{m['final_alive_links']:>5} "
              f"{m.get('max_milestone',0):>3}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.8c Axiomatic Parameter Discovery")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V48C_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v48c")
    # v4.8c drift
    parser.add_argument("--drift-alpha", type=float, default=0.0001)
    parser.add_argument("--drift-interval", type=int, default=3)
    parser.add_argument("--init-restore", type=float, default=0.5)
    parser.add_argument("--init-inert", type=float, default=0.02)
    parser.add_argument("--no-drift", action="store_true")
    # v4.8b inherited
    parser.add_argument("--cooling-strength", type=float, default=1.0)
    parser.add_argument("--no-cooling", action="store_true")
    parser.add_argument("--no-z-coupling", action="store_true")
    parser.add_argument("--z-hetero-dampen", type=float, default=0.3)
    # v4.6/v4.4
    parser.add_argument("--jaccard-thr", type=float, default=0.3)
    parser.add_argument("--whirlpool-hops", type=int, default=2)
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    # Aggregate
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()

    if args.aggregate:
        aggregate(args.output)
        return

    params = V48cEncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        whirlpool_hops=args.whirlpool_hops,
        jaccard_threshold=args.jaccard_thr,
        cooling_strength=args.cooling_strength,
        cooling_enabled=not args.no_cooling,
        z_coupling_enabled=not args.no_z_coupling,
        z_decay_compound_restore=args.init_restore,
        z_decay_inert_penalty=args.init_inert,
        z_phase_hetero_dampen=args.z_hetero_dampen,
        drift_alpha=args.drift_alpha,
        drift_interval=args.drift_interval,
        drift_enabled=not args.no_drift,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()
