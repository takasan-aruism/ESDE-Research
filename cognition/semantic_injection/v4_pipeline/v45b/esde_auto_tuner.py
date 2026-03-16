#!/usr/bin/env python3
"""
ESDE v4.5b — Adaptive Parameter Tuner
========================================
Category A: Orchestrator Layer (no physics changes)

Automates parameter exploration for boundary metabolism by running
independent v4.5b simulations and narrowing the search space toward
the Goldilocks Zone where incorporation emerges without collapse.

ALGORITHM: Adaptive Grid Search
  Phase 1 (Wide): Coarse grid across full parameter bounds
  Phase 2 (Narrow): Refine around top-scoring region
  Phase 3 (Fine): Final convergence on optimal zone

Each run is fully independent (clean engine init, fresh RNG).
The tuner never intervenes during physics execution.

TUNABLE PARAMETERS (approved by GPT audit):
  - accretion_boost:   [0.1, 1.0]   latent field magnitude
  - accretion_lambda:  [0.5, 4.0]   resonance selectivity

FROZEN PARAMETERS (NOT tunable):
  - link_decay, semantic pressure, phase diffusion, RealizationOperator

FITNESS FUNCTION:
  score = (incorporations * W1) + (max_lifespan * W2)
        + (turnover_rate * W3) - (collapse_penalty)

USAGE
-----
  # Default: 3-phase search, 2 seeds per config, 50 windows each
  python esde_auto_tuner.py

  # Quick test (1 seed, 20 windows)
  python esde_auto_tuner.py --seeds 1 --windows 20

  # Custom bounds
  python esde_auto_tuner.py --boost-min 0.3 --boost-max 0.8 \
    --lambda-min 1.0 --lambda-max 3.0

  # Resume from previous results
  python esde_auto_tuner.py --resume tuner_results/tuner_log.csv
"""

import sys, csv, json, time, argparse, itertools
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v45b_engine import V45bEngine, V45bEncapsulationParams


# ================================================================
# FITNESS FUNCTION
# ================================================================
def compute_fitness(metrics, weights):
    """
    Score = (incorporations * W1) + (max_lifespan * W2)
          + (turnover_rate * W3) - (collapse_penalty)

    All components logged separately for transparency.
    """
    incorp = metrics["total_incorporations"]
    lifespan = metrics["max_lifespan"]
    turnover = metrics["mean_turnover_rate"]
    collapse = metrics["collapse_events"]

    # Bonus for accretion activity (even without incorporation)
    accretion_bonus = min(metrics["total_accretion_boosts"], 50) / 50.0

    components = {
        "incorp_score": incorp * weights["W1"],
        "lifespan_score": lifespan * weights["W2"],
        "turnover_score": turnover * weights["W3"],
        "accretion_bonus": accretion_bonus * weights.get("W4", 5.0),
        "collapse_penalty": collapse * weights["collapse"],
    }
    score = (components["incorp_score"]
             + components["lifespan_score"]
             + components["turnover_score"]
             + components["accretion_bonus"]
             - components["collapse_penalty"])
    return round(score, 4), components


# ================================================================
# INJECTION CACHE
# ================================================================
import copy

_injection_cache = {}  # {seed: deep-copied engine (post-injection, pre-quiet)}

def get_injected_engine(seed, params):
    """
    Return a fresh engine with injection complete.
    Caches per seed — injection is deterministic, only accretion
    params differ between runs. Deep-copy ensures full isolation.
    """
    if seed not in _injection_cache:
        # Build with default params (accretion doesn't affect injection)
        engine = V45bEngine(seed=seed, encap_params=params)
        engine.run_injection()
        _injection_cache[seed] = engine
    # Deep-copy: each run gets isolated state
    cloned = copy.deepcopy(_injection_cache[seed])
    # Apply run-specific accretion params
    cloned.island_tracker.params = params
    return cloned


# ================================================================
# SINGLE RUN
# ================================================================
def run_single(seed, n_windows, window_steps, params):
    """
    Execute one independent v4.5b run. Returns metrics dict.
    Fully isolated via deep-copy of cached post-injection state.
    """
    engine = get_injected_engine(seed, params)

    for w in range(n_windows):
        engine.step_window(steps=window_steps)

    # Extract metrics
    isum = engine.island_tracker._summary()
    frames = engine.frames

    # Collapse detection
    collapse = 0
    if frames:
        final_links = frames[-1].alive_links
        if final_links < 100:
            collapse = 1
        # Super-cluster check (>50 nodes)
        max_size = max((int(f.max_cluster_size) for f in frames), default=0)
        if max_size > 50:
            collapse += 1

    # Turnover rate from deformation data
    turnover_rates = []
    for d in engine.island_tracker.deformation.values():
        if d["lifespan_windows"] >= 2 and d["cumulative_turnover"] > 0:
            turnover_rates.append(
                d["cumulative_turnover"] / max(d["lifespan_windows"], 1))

    # Incorporation count from resonance observer
    total_incorp = (isum.get("resonant_incorporations", 0)
                    + isum.get("dissonant_incorporations", 0))

    metrics = {
        "seed": seed,
        "n_windows": n_windows,
        "final_links": frames[-1].alive_links if frames else 0,
        "max_seen_count": isum.get("max_seen_count", 0),
        "max_lifespan": isum.get("max_lifespan", 0),
        "max_cluster_size": max((int(f.max_cluster_size) for f in frames), default=0),
        "total_incorporations": total_incorp,
        "total_accretion_boosts": engine.total_accretion_boosts,
        "total_accretion_contacts": engine.total_accretion_contacts,
        "mean_turnover_rate": round(float(np.mean(turnover_rates)), 4)
        if turnover_rates else 0.0,
        "deforming_islands": len(turnover_rates),
        "personalities_recorded": isum.get("personalities_recorded", 0),
        "pd_both_count": sum(
            1 for e in engine.island_tracker.pd_events
            if e["is_P"] and e["is_D"]),
        "collapse_events": collapse,
    }
    return metrics


# ================================================================
# GRID GENERATION
# ================================================================
def generate_grid(boost_range, lambda_range, n_boost, n_lambda):
    """Generate parameter grid as list of (boost, lambda) tuples."""
    boosts = np.linspace(boost_range[0], boost_range[1], n_boost)
    lambdas = np.linspace(lambda_range[0], lambda_range[1], n_lambda)
    return [(round(float(b), 4), round(float(l), 4))
            for b, l in itertools.product(boosts, lambdas)]


# ================================================================
# ADAPTIVE TUNER
# ================================================================
def run_tuner(args):
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "tuner_log.csv"

    weights = {
        "W1": args.w1,    # incorporation (high priority)
        "W2": args.w2,    # lifespan
        "W3": args.w3,    # turnover
        "W4": args.w4,    # accretion bonus
        "collapse": args.w_collapse,
    }

    seeds = list(range(42, 42 + args.seeds))
    all_results = []

    # Resume support
    if args.resume and Path(args.resume).exists():
        with open(args.resume) as f:
            for r in csv.DictReader(f):
                all_results.append(r)
        print(f"  Resumed {len(all_results)} previous results from {args.resume}")

    # CSV header
    LOG_FIELDS = [
        "phase", "run_id", "seed", "boost", "lam",
        "n_windows", "final_links", "max_seen", "max_lifespan",
        "max_cluster_size", "incorporations", "accretion_boosts",
        "accretion_contacts", "mean_turnover", "deforming_islands",
        "personalities", "pd_both", "collapse",
        "score", "incorp_s", "life_s", "turn_s", "accr_s", "coll_s",
    ]
    write_header = not Path(log_path).exists() or not args.resume
    log_f = open(log_path, "a" if args.resume else "w", newline="")
    writer = csv.DictWriter(log_f, fieldnames=LOG_FIELDS)
    if write_header:
        writer.writeheader()

    run_id = len(all_results)

    # ── Phase definitions ──
    phases = [
        {
            "name": "WIDE",
            "boost_range": (args.boost_min, args.boost_max),
            "lambda_range": (args.lambda_min, args.lambda_max),
            "n_boost": args.grid_wide,
            "n_lambda": args.grid_wide,
        },
    ]

    def run_phase(phase_def, phase_name):
        nonlocal run_id
        grid = generate_grid(
            phase_def["boost_range"], phase_def["lambda_range"],
            phase_def["n_boost"], phase_def["n_lambda"])

        print(f"\n  {'='*65}")
        print(f"  PHASE: {phase_name}")
        print(f"  boost: [{phase_def['boost_range'][0]}, {phase_def['boost_range'][1]}] "
              f"x lambda: [{phase_def['lambda_range'][0]}, {phase_def['lambda_range'][1]}]")
        print(f"  Grid: {len(grid)} configs x {len(seeds)} seeds = {len(grid)*len(seeds)} runs")
        print(f"  {'='*65}")

        phase_scores = []

        for gi, (boost, lam) in enumerate(grid):
            seed_scores = []
            for si, seed in enumerate(seeds):
                run_id += 1
                params = V45bEncapsulationParams(
                    accretion_boost=boost,
                    accretion_lambda=lam,
                    accretion_dr_gate=args.accretion_dr,
                    accretion_seen_gate=args.accretion_seen,
                )

                t0 = time.time()
                metrics = run_single(seed, args.windows, args.window_steps, params)
                elapsed = time.time() - t0

                score, components = compute_fitness(metrics, weights)
                seed_scores.append(score)

                row = {
                    "phase": phase_name,
                    "run_id": run_id,
                    "seed": seed,
                    "boost": boost,
                    "lam": lam,
                    "n_windows": metrics["n_windows"],
                    "final_links": metrics["final_links"],
                    "max_seen": metrics["max_seen_count"],
                    "max_lifespan": metrics["max_lifespan"],
                    "max_cluster_size": metrics["max_cluster_size"],
                    "incorporations": metrics["total_incorporations"],
                    "accretion_boosts": metrics["total_accretion_boosts"],
                    "accretion_contacts": metrics["total_accretion_contacts"],
                    "mean_turnover": metrics["mean_turnover_rate"],
                    "deforming_islands": metrics["deforming_islands"],
                    "personalities": metrics["personalities_recorded"],
                    "pd_both": metrics["pd_both_count"],
                    "collapse": metrics["collapse_events"],
                    "score": score,
                    "incorp_s": components["incorp_score"],
                    "life_s": components["lifespan_score"],
                    "turn_s": components["turnover_score"],
                    "accr_s": components["accretion_bonus"],
                    "coll_s": components["collapse_penalty"],
                }
                writer.writerow(row)
                log_f.flush()
                all_results.append(row)

                status = (f"  [{run_id:>3}] boost={boost:.2f} λ={lam:.1f} "
                          f"seed={seed} → score={score:>6.2f} "
                          f"incorp={metrics['total_incorporations']} "
                          f"boost={metrics['total_accretion_boosts']} "
                          f"life={metrics['max_lifespan']} "
                          f"turn={metrics['mean_turnover_rate']:.3f} "
                          f"links={metrics['final_links']} "
                          f"({elapsed:.0f}s)")
                print(status)

            mean_score = round(float(np.mean(seed_scores)), 4)
            phase_scores.append((boost, lam, mean_score))

        return phase_scores

    # ── Phase 1: WIDE ──
    wide_scores = run_phase(phases[0], "WIDE")

    # Sort by score, take top quartile for NARROW phase
    wide_scores.sort(key=lambda x: x[2], reverse=True)
    top_n = max(2, len(wide_scores) // 4)
    top = wide_scores[:top_n]

    boost_lo = max(args.boost_min, min(t[0] for t in top) - 0.05)
    boost_hi = min(args.boost_max, max(t[0] for t in top) + 0.05)
    lam_lo = max(args.lambda_min, min(t[1] for t in top) - 0.3)
    lam_hi = min(args.lambda_max, max(t[1] for t in top) + 0.3)

    print(f"\n  WIDE phase best: {wide_scores[0]}")
    print(f"  Narrowing → boost=[{boost_lo:.2f}, {boost_hi:.2f}] "
          f"lambda=[{lam_lo:.1f}, {lam_hi:.1f}]")

    # ── Phase 2: NARROW ──
    narrow_def = {
        "boost_range": (boost_lo, boost_hi),
        "lambda_range": (lam_lo, lam_hi),
        "n_boost": args.grid_narrow,
        "n_lambda": args.grid_narrow,
    }
    narrow_scores = run_phase(narrow_def, "NARROW")

    narrow_scores.sort(key=lambda x: x[2], reverse=True)
    top_n2 = max(2, len(narrow_scores) // 4)
    top2 = narrow_scores[:top_n2]

    boost_lo2 = max(args.boost_min, min(t[0] for t in top2) - 0.02)
    boost_hi2 = min(args.boost_max, max(t[0] for t in top2) + 0.02)
    lam_lo2 = max(args.lambda_min, min(t[1] for t in top2) - 0.15)
    lam_hi2 = min(args.lambda_max, max(t[1] for t in top2) + 0.15)

    print(f"\n  NARROW phase best: {narrow_scores[0]}")
    print(f"  Refining → boost=[{boost_lo2:.3f}, {boost_hi2:.3f}] "
          f"lambda=[{lam_lo2:.2f}, {lam_hi2:.2f}]")

    # ── Phase 3: FINE ──
    fine_def = {
        "boost_range": (boost_lo2, boost_hi2),
        "lambda_range": (lam_lo2, lam_hi2),
        "n_boost": args.grid_fine,
        "n_lambda": args.grid_fine,
    }
    fine_scores = run_phase(fine_def, "FINE")

    fine_scores.sort(key=lambda x: x[2], reverse=True)

    log_f.close()

    # ── Final summary ──
    print(f"\n  {'='*65}")
    print(f"  TUNER COMPLETE — {run_id} total runs")
    print(f"  {'='*65}")
    print(f"\n  TOP 5 CONFIGURATIONS:")
    print(f"  {'boost':>6} {'lambda':>6} {'score':>7}")
    print(f"  {'-'*22}")
    for b, l, s in fine_scores[:5]:
        print(f"  {b:>6.3f} {l:>6.2f} {s:>7.2f}")

    best = fine_scores[0]
    print(f"\n  BEST: boost={best[0]:.4f}, lambda={best[1]:.2f}, score={best[2]:.4f}")
    print(f"  Log: {log_path}")

    # Save summary JSON
    summary = {
        "best_boost": best[0],
        "best_lambda": best[1],
        "best_score": best[2],
        "total_runs": run_id,
        "phases": {
            "wide_best": wide_scores[0] if wide_scores else None,
            "narrow_best": narrow_scores[0] if narrow_scores else None,
            "fine_best": fine_scores[0] if fine_scores else None,
        },
        "weights": weights,
        "config": {
            "seeds": seeds,
            "windows": args.windows,
            "window_steps": args.window_steps,
            "accretion_dr_gate": args.accretion_dr,
            "accretion_seen_gate": args.accretion_seen,
        },
    }
    with open(output_dir / "tuner_summary.json", "w") as sf:
        json.dump(summary, sf, indent=2, default=str)

    print(f"  Summary: {output_dir / 'tuner_summary.json'}\n")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.5b Adaptive Parameter Tuner")

    # Run config
    parser.add_argument("--seeds", type=int, default=1,
                        help="Seeds per config (default 1; tuner is directional, not statistical)")
    parser.add_argument("--windows", type=int, default=20,
                        help="Windows per run (default 20; signal detection only)")
    parser.add_argument("--window-steps", type=int, default=50,
                        help="Steps per window (default 50)")
    parser.add_argument("--output", type=str, default="tuner_results")

    # Parameter bounds
    parser.add_argument("--boost-min", type=float, default=0.1)
    parser.add_argument("--boost-max", type=float, default=1.0)
    parser.add_argument("--lambda-min", type=float, default=0.5)
    parser.add_argument("--lambda-max", type=float, default=4.0)

    # Grid sizes per phase
    parser.add_argument("--grid-wide", type=int, default=4,
                        help="Grid points per axis in WIDE phase (default 4)")
    parser.add_argument("--grid-narrow", type=int, default=3,
                        help="Grid points per axis in NARROW phase (default 3)")
    parser.add_argument("--grid-fine", type=int, default=3,
                        help="Grid points per axis in FINE phase (default 3)")

    # Fixed accretion gates
    parser.add_argument("--accretion-dr", type=float, default=1.0)
    parser.add_argument("--accretion-seen", type=int, default=2)

    # Fitness weights
    parser.add_argument("--w1", type=float, default=20.0,
                        help="Weight for incorporation events")
    parser.add_argument("--w2", type=float, default=3.0,
                        help="Weight for max lifespan")
    parser.add_argument("--w3", type=float, default=10.0,
                        help="Weight for turnover rate")
    parser.add_argument("--w4", type=float, default=5.0,
                        help="Weight for accretion bonus")
    parser.add_argument("--w-collapse", type=float, default=50.0,
                        help="Collapse penalty")

    # Resume
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to existing tuner_log.csv to resume from")

    args = parser.parse_args()
    run_tuner(args)


if __name__ == "__main__":
    main()
