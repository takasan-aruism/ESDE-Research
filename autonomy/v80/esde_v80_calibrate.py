#!/usr/bin/env python3
"""
ESDE v8.0 — Large-Scale Autonomy Calibration
===============================================
N=10000, 200 steps/window, multi-seed.

USAGE
-----
  # Single seed
  python esde_v80_calibrate.py --seed 42 --windows 200

  # Use run_parallel.sh for multi-seed
  bash run_parallel.sh
"""

import sys, csv, json, time, argparse, os
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V4_PIPELINE = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v80_engine import V80Engine, V80EncapsulationParams, V80_WINDOW, V80_N

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
    # v8.0 lifecycle columns
    "v_oldest_age", "v_mean_age",
    "v_mean_share_5node", "v_share_std",
    "v_births_5node", "v_deaths_5node",
]


def run(seed, n_windows, window_steps, output_dir, encap_params, N):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tags = []
    if encap_params.stress_enabled: tags.append("stress")
    if encap_params.virtual_enabled: tags.append("metab")
    if not tags: tags.append("baseline")
    tag_str = "+".join(tags)

    print(f"\n  ESDE v8.0 — Large-Scale Autonomy")
    print(f"  N={N} seed={seed} windows={n_windows} "
          f"steps/win={window_steps} [{tag_str}]")
    print(f"  Injection...", flush=True)

    t_start = time.time()
    engine = V80Engine(seed=seed, N=N, encap_params=encap_params)
    engine.run_injection()
    t_inj = time.time() - t_start
    print(f"  Injection done ({t_inj:.0f}s). Starting windows.\n")

    tag = f"v80_N{N}_seed{seed}_{tag_str.replace('+','_')}"
    csv_path = output_dir / f"{tag}.csv"
    status_path = output_dir / f"{tag}_status.txt"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    # Header
    print(f"  {'win':>4} {'clst':>4} {'R+':>5} {'sI':>5} "
          f"{'vLb':>4} {'topS':>6} {'rR+':>6} "
          f"{'lnks':>6} {'M':>1} {'sec':>5} {'ETA':>6}")
    print(f"  {'-'*68}")

    times = []

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0
        times.append(sec)

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
            # v8.0 lifecycle
            "v_oldest_age": vl.get("v_oldest_age", 0),
            "v_mean_age": vl.get("v_mean_age", 0),
            "v_mean_share_5node": vl.get("v_mean_share_5node", 0),
            "v_share_std": vl.get("v_share_std", 0),
            "v_births_5node": vl.get("v_births_5node", 0),
            "v_deaths_5node": vl.get("v_deaths_5node", 0),
        }
        writer.writerow(row)
        f.flush()

        # ETA calculation
        avg_sec = np.mean(times[-10:])  # last 10 windows
        remaining = (n_windows - w - 1) * avg_sec
        if remaining > 3600:
            eta_str = f"{remaining/3600:.1f}h"
        else:
            eta_str = f"{remaining/60:.0f}m"

        print(f"  {frame.window:>4} "
              f"{isum.get('n_clusters',0):>4} "
              f"{rplus:>5} "
              f"{ss.get('stress_intensity',1.0):>5.3f} "
              f"{vl.get('labels_active',0):>4} "
              f"{vl.get('top_share',0):>6.4f} "
              f"{vl.get('label_rplus_rate',0):>6.1f} "
              f"{frame.alive_links:>6} "
              f"{frame.milestone:>1} "
              f"{sec:>5.0f} "
              f"{eta_str:>6}")

        # Status file for monitoring from another terminal
        with open(status_path, "w") as sf:
            elapsed = time.time() - t_start
            sf.write(f"seed={seed} N={N} w={frame.window}/{n_windows} "
                     f"links={frame.alive_links} R+={rplus} "
                     f"vLb={vl.get('labels_active',0)} "
                     f"sI={ss.get('stress_intensity',1.0):.3f} "
                     f"sec/win={avg_sec:.0f} ETA={eta_str} "
                     f"elapsed={elapsed/3600:.1f}h\n")

    f.close()
    t_total = time.time() - t_start

    # JSON summary
    json_path = output_dir / f"{tag}_detail.json"
    detail = {
        "meta": {
            "version": "v8.0", "N": N,
            "seed": seed, "n_windows": n_windows,
            "window_steps": window_steps,
            "stress_enabled": bool(encap_params.stress_enabled),
            "virtual_enabled": bool(encap_params.virtual_enabled),
            "final_alive_links": frame.alive_links,
            "total_seconds": round(t_total, 0),
            "mean_sec_per_window": round(np.mean(times), 1),
        },
        "virtual_summary": engine.virtual.summary(),
        "lifecycle_log": engine.virtual.lifecycle_log,
    }
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    # Clean up status
    os.remove(status_path)

    print(f"\n  DONE: seed={seed} N={N} "
          f"links={frame.alive_links} R+={rplus} "
          f"vLb={vl.get('labels_active',0)} "
          f"total={t_total/3600:.1f}h ({np.mean(times):.0f}s/win)")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v8.0 Large-Scale Autonomy")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V80_WINDOW)
    parser.add_argument("--N", type=int, default=V80_N)
    parser.add_argument("--output", type=str, default="calibration_v80")
    parser.add_argument("--no-stress", action="store_true")
    parser.add_argument("--no-virtual", action="store_true")
    parser.add_argument("--profile", action="store_true",
                        help="Run 3 windows with cProfile, print top 30 bottlenecks")
    args = parser.parse_args()

    params = V80EncapsulationParams(
        stress_enabled=not args.no_stress,
        virtual_enabled=not args.no_virtual,
    )

    if args.profile:
        import cProfile, pstats, io
        print(f"\n  PROFILING MODE: N={args.N}, 3 windows, {args.window_steps} steps/win")
        engine = V80Engine(seed=args.seed, N=args.N, encap_params=params)
        engine.run_injection()
        pr = cProfile.Profile()
        pr.enable()
        for _ in range(3):
            engine.step_window(steps=args.window_steps)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(30)
        print(s.getvalue())
        return

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params, N=args.N)


if __name__ == "__main__":
    main()
