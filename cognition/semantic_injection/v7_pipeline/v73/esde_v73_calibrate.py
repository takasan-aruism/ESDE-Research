#!/usr/bin/env python3
"""
ESDE v7.3 — Stress + Metabolism Calibration
==============================================
USAGE
-----
  python esde_v73_calibrate.py --seed 42 --windows 200
  python esde_v73_calibrate.py --seed 42 --windows 50 --no-virtual
  python esde_v73_calibrate.py --seed 42 --windows 50 --no-stress --no-virtual  # pure V43
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

from esde_v73_engine import V73Engine, V73EncapsulationParams, V73_WINDOW

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "max_size",
    "k_star", "entropy", "milestone", "physics_seconds",
    "stressed", "calcified", "mean_omega",
    "stress_intensity", "link_ema",
    "total_rplus",
    "budget", "v_labels", "v_born", "v_died",
    "v_torque_n", "v_mean_torque", "v_top_share",
    "v_label_rplus_rate",
]


def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tags = []
    if encap_params.stress_enabled: tags.append("stress")
    if encap_params.virtual_enabled: tags.append("metab")
    if not tags: tags.append("baseline")
    tag_str = "+".join(tags)

    print(f"\n  ESDE v7.3 — Stress + Metabolism")
    print(f"  seed={seed} windows={n_windows} [{tag_str}]")
    print(f"  Injection...", flush=True)

    engine = V73Engine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    tag = f"v73_seed{seed}_{tag_str.replace('+','_')}"
    csv_path = output_dir / f"{tag}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    print(f"\n  {'win':>4} {'clst':>4} {'mxSz':>4} "
          f"{'R+':>4} {'sI':>5} "
          f"{'str':>4} {'cal':>4} "
          f"{'vLb':>4} {'topS':>6} {'rR+':>5} "
          f"{'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*72}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.last_isum
        vl = engine.virtual_stats
        ss = engine.stress_stats

        rplus = sum(1 for lk in engine.state.alive_l
                    if engine.state.R.get(lk, 0.0) > 0)

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": isum.get("n_clusters", 0),
            "max_size": isum.get("max_size", 0),
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "milestone": frame.milestone,
            "physics_seconds": round(sec, 1),
            "stressed": ss.get("stressed", 0),
            "calcified": ss.get("calcified", 0),
            "mean_omega": ss.get("mean_omega", 0),
            "stress_intensity": ss.get("stress_intensity", 1.0),
            "link_ema": ss.get("link_ema", 0),
            "total_rplus": rplus,
            "budget": vl.get("budget", 0),
            "v_labels": vl.get("labels_active", 0),
            "v_born": vl.get("labels_born", 0),
            "v_died": vl.get("labels_died", 0),
            "v_torque_n": vl.get("torque_events", 0),
            "v_mean_torque": vl.get("mean_torque", 0),
            "v_top_share": vl.get("top_share", 0),
            "v_label_rplus_rate": vl.get("label_rplus_rate", 0),
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
              f"{vl.get('labels_active',0):>4} "
              f"{vl.get('top_share',0):>6.4f} "
              f"{vl.get('label_rplus_rate',0):>5.2f} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}")

    f.close()

    json_path = output_dir / f"{tag}_detail.json"
    detail = {
        "meta": {
            "version": "v7.3",
            "seed": seed, "n_windows": n_windows,
            "stress_enabled": bool(encap_params.stress_enabled),
            "virtual_enabled": bool(encap_params.virtual_enabled),
            "final_alive_links": frame.alive_links,
        },
        "virtual_summary": engine.virtual.summary(),
    }
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    print(f"\n  SUMMARY: links={frame.alive_links} R+={rplus} "
          f"vLb={vl.get('labels_active',0)} "
          f"topShare={vl.get('top_share',0):.4f}")
    print(f"  CSV: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V73_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v73")
    parser.add_argument("--no-stress", action="store_true")
    parser.add_argument("--no-virtual", action="store_true")
    args = parser.parse_args()

    params = V73EncapsulationParams(
        stress_enabled=not args.no_stress,
        virtual_enabled=not args.no_virtual,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()