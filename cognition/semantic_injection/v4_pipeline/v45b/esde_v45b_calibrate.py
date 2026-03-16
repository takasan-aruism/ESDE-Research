#!/usr/bin/env python3
"""
ESDE v4.5b — Boundary Metabolism Calibration
===============================================
Resonance-biased boundary accretion with full v4.5a observation.

USAGE
-----
  # Quick sanity (10 windows)
  python esde_v45b_calibrate.py --seed 42 --windows 10

  # Default gates (DR>=1.0, seen>=2)
  parallel -j 5 python esde_v45b_calibrate.py --seed {1} --windows 200 \
    ::: 42 7 123 314 456 610 77 789 999 2024

  # Strict gates per spec (DR>=1.5, seen>=3)
  python esde_v45b_calibrate.py --seed 42 --windows 200 --strict

  # Custom accretion parameters
  python esde_v45b_calibrate.py --seed 42 --accretion-lambda 3.0 \
    --accretion-boost 0.4 --accretion-dr 1.0 --accretion-seen 1

  # Aggregate
  python esde_v45b_calibrate.py --aggregate --output calibration_v45b
"""

import sys, csv, json, time, argparse
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v45b_engine import (
    V45bEngine, V45bEncapsulationParams, V45B_WINDOW,
)

# ================================================================
# CSV FIELDS — v4.5a baseline + v4.5b accretion
# ================================================================
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
    # v4.5a: Boundary resonance (observation)
    "resonant_incorporations", "dissonant_incorporations",
    "resonant_rejections", "dissonant_rejections",
    "resonance_total_events", "resonance_ratio",
    # v4.5a: P/D paradox
    "pd_p_count", "pd_d_count", "pd_both_count",
    # v4.5a: Personality
    "personalities_recorded",
    # v4.5b: Accretion (NEW)
    "accretion_qualified", "accretion_contacts",
    "accretion_boosts", "accretion_boosted_nodes",
    "accretion_mean_resonance", "accretion_total_boosts_cum",
]


# ================================================================
# RUN
# ================================================================
def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v4.5b Boundary Metabolism Calibration")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  accretion: lambda={encap_params.accretion_lambda} "
          f"boost={encap_params.accretion_boost} "
          f"dr_gate={encap_params.accretion_dr_gate} "
          f"seen_gate={encap_params.accretion_seen_gate}")
    print(f"  whirlpool_hops={encap_params.whirlpool_hops} "
          f"resonance_thr={encap_params.resonance_threshold:.4f}")
    print(f"  Injection...", flush=True)

    engine = V45bEngine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    csv_path = output_dir / f"v45b_seed{seed}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    # Header
    print(f"\n  {'win':>4} {'clst':>4} {'seen':>4} {'mxDR':>5} "
          f"{'cont':>5} {'life':>4} "
          f"{'qCls':>4} {'aCon':>4} {'aBst':>4} {'mRes':>5} "
          f"{'resI':>4} {'disI':>4} "
          f"{'P':>2} {'D':>2} {'PD':>2} "
          f"{'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*90}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.island_tracker._summary()
        astats = engine.accretion_stats
        max_ms = max(max_ms, frame.milestone)
        hc = len(engine.hardening)

        # Accretion resonance stats
        rf = astats.get("resonance_factors", [])
        mean_res = round(float(np.mean(rf)), 4) if rf else 0.0

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
            # v4.5a: Resonance (observation)
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
            # v4.5b: Accretion
            "accretion_qualified": astats.get("qualified_clusters", 0),
            "accretion_contacts": astats.get("contact_events", 0),
            "accretion_boosts": astats.get("boosts_applied", 0),
            "accretion_boosted_nodes": astats.get("unique_boosted_nodes", 0),
            "accretion_mean_resonance": mean_res,
            "accretion_total_boosts_cum": engine.total_accretion_boosts,
        }
        writer.writerow(row)
        f.flush()

        # Console output
        print(f"  {frame.window:>4} {isum['n_clusters']:>4} "
              f"{isum['max_seen_count']:>4} "
              f"{isum['max_density_ratio']:>5.2f} "
              f"{isum['mean_continuity']:>5.2f} "
              f"{isum['max_lifespan']:>4} "
              f"{astats.get('qualified_clusters',0):>4} "
              f"{astats.get('contact_events',0):>4} "
              f"{astats.get('boosts_applied',0):>4} "
              f"{mean_res:>5.2f} "
              f"{isum['resonant_incorporations']:>4} "
              f"{isum['dissonant_incorporations']:>4} "
              f"{isum['pd_p_count']:>2} "
              f"{isum['pd_d_count']:>2} "
              f"{isum['pd_both_count']:>2} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}")

    f.close()

    # ── JSON detailed report ──
    json_path = output_dir / f"v45b_seed{seed}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "seed": seed,
        "n_windows": n_windows,
        "window_steps": window_steps,
        "final_alive_links": engine.frames[-1].alive_links if engine.frames else 0,
        "max_milestone": max_ms,
        "max_seen_count": isum["max_seen_count"],
        "total_accretion_boosts": engine.total_accretion_boosts,
        "total_accretion_contacts": engine.total_accretion_contacts,
    }
    detail["accretion_params"] = {
        "lambda": encap_params.accretion_lambda,
        "boost": encap_params.accretion_boost,
        "dr_gate": encap_params.accretion_dr_gate,
        "seen_gate": encap_params.accretion_seen_gate,
        "use_substrate": encap_params.accretion_use_substrate,
    }
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    # ── Summary ──
    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed})")
    print(f"  {'='*60}")
    print(f"  Highest milestone:        M{max_ms}")
    print(f"  Max seen_count:           {isum['max_seen_count']}")
    print(f"  Max lifespan (deform):    {isum['max_lifespan']}")
    print(f"  Personalities recorded:   {isum['personalities_recorded']}")
    print(f"  Resonance ratio (obs):    {isum['resonance_ratio']:.4f}")
    print(f"  Accretion boosts (cum):   {engine.total_accretion_boosts}")
    print(f"  Accretion contacts (cum): {engine.total_accretion_contacts}")
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
    csv_files = sorted(output_dir.glob("v45b_seed*.csv"))
    json_files = sorted(output_dir.glob("v45b_seed*_detail.json"))

    if not csv_files:
        print(f"  No v4.5b CSV files found in {output_dir}")
        return

    print(f"\n  {'='*70}")
    print(f"  ESDE v4.5b — Aggregate Summary ({len(csv_files)} seeds)")
    print(f"  {'='*70}")

    all_seeds = []
    for cf in csv_files:
        rows = []
        with open(cf) as fh:
            for r in csv.DictReader(fh):
                rows.append(r)
        if not rows:
            continue

        last = rows[-1]
        seed = cf.stem.replace("v45b_seed", "")

        max_seen = max(int(r.get("max_seen_count", "0")) for r in rows)
        max_dr = max(float(r.get("max_density_ratio", "0")) for r in rows)
        res_in = int(last.get("resonant_incorporations", "0"))
        dis_in = int(last.get("dissonant_incorporations", "0"))
        total_boosts = int(last.get("accretion_total_boosts_cum", "0"))
        total_contacts_list = [int(r.get("accretion_contacts", "0")) for r in rows]
        total_contacts = sum(total_contacts_list)
        pd_both_list = [int(r.get("pd_both_count", "0")) for r in rows]
        max_pd_both = max(pd_both_list) if pd_both_list else 0
        pers = int(last.get("personalities_recorded", "0"))
        max_life = max(int(r.get("max_lifespan", "0")) for r in rows)
        links = int(last.get("alive_links", "0"))
        max_size = max(int(r.get("max_size", "0")) for r in rows)

        all_seeds.append({
            "seed": seed, "windows": len(rows), "links": links,
            "max_seen": max_seen, "max_dr": max_dr,
            "max_size": max_size, "max_life": max_life,
            "res_in": res_in, "dis_in": dis_in,
            "total_boosts": total_boosts, "total_contacts": total_contacts,
            "max_pd_both": max_pd_both, "pers": pers,
        })

    print(f"\n  {'seed':>6} {'wins':>4} {'links':>5} {'seen':>4} {'mxDR':>5} "
          f"{'mxSz':>4} {'life':>4} {'boost':>5} {'cont':>5} "
          f"{'rIn':>3} {'dIn':>3} {'PD':>2} {'pers':>4}")
    print(f"  {'-'*70}")
    for s in all_seeds:
        print(f"  {s['seed']:>6} {s['windows']:>4} {s['links']:>5} "
              f"{s['max_seen']:>4} {s['max_dr']:>5.2f} "
              f"{s['max_size']:>4} {s['max_life']:>4} "
              f"{s['total_boosts']:>5} {s['total_contacts']:>5} "
              f"{s['res_in']:>3} {s['dis_in']:>3} "
              f"{s['max_pd_both']:>2} {s['pers']:>4}")

    # System summary
    print(f"\n  System-level:")
    total_boosts = sum(s["total_boosts"] for s in all_seeds)
    total_contacts = sum(s["total_contacts"] for s in all_seeds)
    total_in = sum(s["res_in"] + s["dis_in"] for s in all_seeds)
    print(f"    Total accretion boosts:     {total_boosts}")
    print(f"    Total contacts:             {total_contacts}")
    print(f"    Total incorporations (obs): {total_in}")
    print(f"    Seeds with P/D both:        "
          f"{sum(1 for s in all_seeds if s['max_pd_both'] > 0)}/{len(all_seeds)}")
    print(f"    Seeds with personality:     "
          f"{sum(1 for s in all_seeds if s['pers'] > 0)}/{len(all_seeds)}")
    print(f"    Max cluster size:           "
          f"{max(s['max_size'] for s in all_seeds)}")
    print(f"    Max lifespan:               "
          f"{max(s['max_life'] for s in all_seeds)}")
    print()


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.5b Boundary Metabolism Calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V45B_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v45b")
    # v4.4 inherited
    parser.add_argument("--whirlpool-hops", type=int, default=2)
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    # v4.5a inherited
    parser.add_argument("--resonance-thr", type=float, default=0.7854)
    parser.add_argument("--personality-trigger", type=int, default=3)
    # v4.5b accretion
    parser.add_argument("--accretion-lambda", type=float, default=2.0,
                        help="Resonance selectivity (default 2.0)")
    parser.add_argument("--accretion-boost", type=float, default=0.25,
                        help="Latent field boost magnitude (default 0.25)")
    parser.add_argument("--accretion-dr", type=float, default=1.0,
                        help="DR gate for accretion (default 1.0)")
    parser.add_argument("--accretion-seen", type=int, default=2,
                        help="seen_count gate for accretion (default 2)")
    parser.add_argument("--strict", action="store_true",
                        help="Use spec-strict gates: DR>=1.5, seen>=3")
    # Aggregate
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()

    if args.aggregate:
        aggregate(args.output)
        return

    # Apply strict mode if requested
    dr_gate = 1.5 if args.strict else args.accretion_dr
    seen_gate = 3 if args.strict else args.accretion_seen

    params = V45bEncapsulationParams(
        # v4.4
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        whirlpool_hops=args.whirlpool_hops,
        # v4.5a
        resonance_threshold=args.resonance_thr,
        personality_trigger_seen=args.personality_trigger,
        # v4.5b
        accretion_dr_gate=dr_gate,
        accretion_seen_gate=seen_gate,
        accretion_lambda=args.accretion_lambda,
        accretion_boost=args.accretion_boost,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()
