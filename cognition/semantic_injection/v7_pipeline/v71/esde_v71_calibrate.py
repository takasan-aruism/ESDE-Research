#!/usr/bin/env python3
"""
ESDE v7.1 — Genesis + World Induction Calibration
====================================================
Genesis canon (V43) + VirtualLayer. No brittleness, void, history,
Z-coupling, or transition field.

USAGE
-----
  python esde_v71_calibrate.py --seed 42 --windows 50
  python esde_v71_calibrate.py --seed 42 --windows 50 --no-virtual  # pure V43 baseline
  parallel -j 2 python esde_v71_calibrate.py --seed {1} --windows 200 ::: 42 123
"""

import sys, csv, json, time, argparse
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
_SEMANTIC_DIR = _PIPELINE_DIR.parent
_V4_PIPELINE = _SEMANTIC_DIR / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_REPO_ROOT = _SEMANTIC_DIR.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_PIPELINE_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v71_engine import V71Engine, V71EncapsulationParams, V71_WINDOW

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "n_encapsulated", "n_candidates",
    "max_size", "max_density_ratio", "max_seen_count",
    "mean_inner_entropy", "max_inner_entropy",
    "total_inner_triangles", "motif_recurrence_count",
    "encap_events_total", "dissolve_events_total",
    "hardened_links_count",
    "k_star", "entropy", "entropy_delta",
    "milestone", "physics_seconds",
    # Virtual layer
    "total_rplus",
    "v_energy", "v_recurrence_n", "v_motifs",
    "v_labels", "v_born", "v_died",
    "v_torque_n", "v_torque_mean", "v_torque_success",
]


def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    virt_tag = "virtual" if encap_params.virtual_enabled else "novirt"
    print(f"\n  ESDE v7.1 — Genesis + World Induction")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  virtual={encap_params.virtual_enabled}")
    print(f"  Injection...", flush=True)

    engine = V71Engine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    tag = f"v71_seed{seed}_{virt_tag}"
    csv_path = output_dir / f"{tag}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    print(f"\n  {'win':>4} {'clst':>4} {'mxSz':>4} {'rLif':>4} "
          f"{'R+':>4} "
          f"{'vE':>6} {'vLb':>3} {'vDd':>3} "
          f"{'torq':>5} "
          f"{'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*65}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        # V43's island_tracker doesn't have step_summary.
        # Extract from frame fields + tracker state.
        isum = {
            "n_clusters": frame.n_clusters,
            "n_encapsulated": frame.n_encapsulated,
            "n_candidates": frame.n_candidates,
            "max_size": int(frame.max_cluster_size),
            "max_density_ratio": frame.max_density_ratio,
            "max_seen_count": getattr(frame, 'max_seen_count', 0),
            "mean_inner_entropy": frame.mean_inner_entropy,
            "max_inner_entropy": frame.max_inner_entropy,
            "total_inner_tri": frame.total_inner_triangles,
            "motif_recurrence": frame.motif_recurrence_count,
            "encap_events": frame.encap_events_total,
            "dissolve_events": frame.dissolve_events_total,
            "max_relaxed_lifespan": 0,
        }
        # Compute max lifespan from tracker
        for iid, info in engine.island_tracker.islands.items():
            life = info.seen_count
            if life > isum["max_relaxed_lifespan"]:
                isum["max_relaxed_lifespan"] = life
        vl = engine.virtual_stats
        max_ms = max(max_ms, frame.milestone)

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": isum.get("n_clusters", 0),
            "n_encapsulated": isum.get("n_encapsulated", 0),
            "n_candidates": isum.get("n_candidates", 0),
            "max_size": isum.get("max_size", 0),
            "max_density_ratio": isum.get("max_density_ratio", 0),
            "max_seen_count": isum.get("max_seen_count", 0),
            "mean_inner_entropy": isum.get("mean_inner_entropy", 0),
            "max_inner_entropy": isum.get("max_inner_entropy", 0),
            "total_inner_triangles": isum.get("total_inner_tri", 0),
            "motif_recurrence_count": isum.get("motif_recurrence", 0),
            "encap_events_total": isum.get("encap_events", 0),
            "dissolve_events_total": isum.get("dissolve_events", 0),
            "hardened_links_count": len(engine.hardening),
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "entropy_delta": round(frame.entropy_delta, 4),
            "milestone": frame.milestone,
            "physics_seconds": round(sec, 1),
            "total_rplus": sum(1 for lk in engine.state.alive_l
                              if engine.state.R.get(lk, 0.0) > 0),
            "v_energy": vl.get("virtual_energy_total", 0),
            "v_recurrence_n": vl.get("recurrence_entries", 0),
            "v_motifs": vl.get("motifs_detected", 0),
            "v_labels": vl.get("labels_active", 0),
            "v_born": vl.get("labels_born", 0),
            "v_died": vl.get("labels_died", 0),
            "v_torque_n": vl.get("torque_events", 0),
            "v_torque_mean": vl.get("mean_torque", 0),
            "v_torque_success": vl.get("torque_success", 0),
        }
        writer.writerow(row)
        f.flush()

        rlife = isum.get("max_relaxed_lifespan",
                         isum.get("max_lifespan", 0))

        rplus = sum(1 for lk in engine.state.alive_l
                    if engine.state.R.get(lk, 0.0) > 0)

        print(f"  {frame.window:>4} {isum.get('n_clusters',0):>4} "
              f"{isum.get('max_size',0):>4} "
              f"{rlife:>4} "
              f"{rplus:>4} "
              f"{vl.get('virtual_energy_total',0):>6.1f} "
              f"{vl.get('labels_active',0):>3} "
              f"{vl.get('labels_died',0):>3} "
              f"{vl.get('torque_events',0):>5} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}")

    f.close()

    json_path = output_dir / f"{tag}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "version": "v7.1",
        "seed": seed, "n_windows": n_windows,
        "window_steps": window_steps,
        "virtual_enabled": bool(encap_params.virtual_enabled),
        "final_alive_links": frame.alive_links,
        "max_milestone": max_ms,
    }
    detail["virtual_layer_summary"] = engine.virtual.summary()
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed})")
    print(f"  {'='*60}")
    vlsum = engine.virtual.summary()
    print(f"  Physical: links={frame.alive_links} M={max_ms}")
    print(f"  Virtual: energy={vlsum['virtual_energy_total']:.2f} "
          f"labels={vlsum['labels_active']}")
    for lb in vlsum.get("label_details", [])[:5]:
        print(f"    Label#{lb['id']}: nodes={lb['nodes']} "
              f"str={lb['strength']:.3f} born=w{lb['born']}")
    if len(vlsum.get("label_details", [])) > 5:
        print(f"    ... and {len(vlsum['label_details'])-5} more")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v7.1 Genesis + World Induction")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=50)
    parser.add_argument("--window-steps", type=int, default=V71_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v71")
    parser.add_argument("--no-virtual", action="store_true")
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    args = parser.parse_args()

    params = V71EncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        virtual_enabled=not args.no_virtual,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()