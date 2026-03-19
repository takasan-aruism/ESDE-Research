#!/usr/bin/env python3
"""
ESDE v7.2 — Stress Equilibrium + World Induction Calibration
===============================================================
USAGE
-----
  python esde_v72_calibrate.py --seed 42 --windows 50
  python esde_v72_calibrate.py --seed 42 --windows 50 --no-stress    # V43 + virtual only
  python esde_v72_calibrate.py --seed 42 --windows 50 --no-virtual   # V43 + stress only
  python esde_v72_calibrate.py --seed 42 --windows 50 --no-stress --no-virtual  # pure V43
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

from esde_v72_engine import V72Engine, V72EncapsulationParams, V72_WINDOW

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "n_encapsulated", "n_candidates",
    "max_size", "max_density_ratio",
    "mean_inner_entropy", "max_inner_entropy",
    "total_inner_triangles", "motif_recurrence_count",
    "k_star", "entropy", "entropy_delta",
    "milestone", "physics_seconds",
    # Stress
    "stressed", "calcified", "suppressed", "mean_omega",
    "stress_intensity", "link_ema",
    # R+
    "total_rplus",
    # Virtual
    "v_energy", "v_labels", "v_born", "v_died",
    "v_torque_n", "v_torque_mean",
]


def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tags = []
    if encap_params.stress_enabled: tags.append("stress")
    if encap_params.virtual_enabled: tags.append("virtual")
    if not tags: tags.append("baseline")
    tag_str = "+".join(tags)

    print(f"\n  ESDE v7.2 — Stress Equilibrium + World Induction")
    print(f"  seed={seed} windows={n_windows} [{tag_str}]")
    print(f"  Injection...", flush=True)

    engine = V72Engine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    tag = f"v72_seed{seed}_{tag_str.replace('+','_')}"
    csv_path = output_dir / f"{tag}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    print(f"\n  {'win':>4} {'clst':>4} {'mxSz':>4} "
          f"{'R+':>4} {'sI':>5} "
          f"{'str':>4} {'cal':>4} "
          f"{'vE':>6} {'vLb':>3} "
          f"{'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*65}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.last_isum
        vl = engine.virtual_stats
        ss = engine.stress_stats
        max_ms = max(max_ms, frame.milestone)

        rplus = sum(1 for lk in engine.state.alive_l
                    if engine.state.R.get(lk, 0.0) > 0)

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": isum.get("n_clusters", 0),
            "n_encapsulated": isum.get("n_encapsulated", 0),
            "n_candidates": isum.get("n_candidates", 0),
            "max_size": isum.get("max_size", 0),
            "max_density_ratio": isum.get("max_density_ratio", 0),
            "mean_inner_entropy": isum.get("mean_inner_entropy", 0),
            "max_inner_entropy": isum.get("max_inner_entropy", 0),
            "total_inner_triangles": isum.get("total_inner_tri", 0),
            "motif_recurrence_count": isum.get("motif_recurrence", 0),
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "entropy_delta": round(frame.entropy_delta, 4),
            "milestone": frame.milestone,
            "physics_seconds": round(sec, 1),
            "stressed": ss.get("stressed", 0),
            "calcified": ss.get("calcified", 0),
            "suppressed": ss.get("suppressed", 0),
            "mean_omega": ss.get("mean_omega", 0),
            "stress_intensity": ss.get("stress_intensity", 1.0),
            "link_ema": ss.get("link_ema", 0),
            "total_rplus": rplus,
            "v_energy": vl.get("virtual_energy_total", 0),
            "v_labels": vl.get("labels_active", 0),
            "v_born": vl.get("labels_born", 0),
            "v_died": vl.get("labels_died", 0),
            "v_torque_n": vl.get("torque_events", 0),
            "v_torque_mean": vl.get("mean_torque", 0),
        }
        writer.writerow(row)
        f.flush()

        print(f"  {frame.window:>4} "
              f"{isum.get('n_clusters',0):>4} "
              f"{isum.get('max_size',0):>4} "
              f"{rplus:>4} "
              f"{ss.get('stress_intensity',1.0):>5.3f} "
              f"{ss.get('stressed',0):>4} "
              f"{ss.get('calcified',0):>4} "
              f"{vl.get('virtual_energy_total',0):>6.1f} "
              f"{vl.get('labels_active',0):>3} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}")

    f.close()

    json_path = output_dir / f"{tag}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "version": "v7.2",
        "seed": seed, "n_windows": n_windows,
        "stress_enabled": bool(encap_params.stress_enabled),
        "virtual_enabled": bool(encap_params.virtual_enabled),
        "final_alive_links": frame.alive_links,
        "max_milestone": max_ms,
    }
    detail["virtual_layer_summary"] = engine.virtual.summary()
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    print(f"\n  SUMMARY: links={frame.alive_links} R+={rplus} "
          f"vE={vl.get('virtual_energy_total',0):.1f} "
          f"vLb={vl.get('labels_active',0)} M={max_ms}")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v7.2 Stress + World Induction")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=50)
    parser.add_argument("--window-steps", type=int, default=V72_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v72")
    parser.add_argument("--no-stress", action="store_true")
    parser.add_argument("--no-virtual", action="store_true")
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    args = parser.parse_args()

    params = V72EncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        stress_enabled=not args.no_stress,
        virtual_enabled=not args.no_virtual,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()
