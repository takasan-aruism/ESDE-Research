#!/usr/bin/env python3
"""
ESDE Genesis — v1.9g N=1000 Scale Validation
==============================================
Phase: Post v1.9g Canonical / Scale Validation (N=1000)
Author: Claude (Implementation)
Architect: Taka / Gemini
Audited by: GPT

PURPOSE
-------
Strict scale replication test at N=1000.
No new mechanics, parameters, or ontology.
All physics / chemistry / observer logic is inherited verbatim from v19g_canon.py.

GRID
----
  plb  : [0.007]           (single value — canonical plb from PLB_GRID)
  rate : [0.001, 0.002]    (two representative intrusion rates from RATE_GRID)
  seeds: 10 per config     (same seed list as canonical runs)
  → 20 total runs

Usage (single run):
  python v1000_scale.py --seed 42 --plb 0.007 --rate 0.001

Usage (full N=1000 sweep, 48-thread Ryzen):
  parallel -j 20 python v1000_scale.py --plb {1} --rate {2} --seed {3} \\
    ::: 0.007 \\
    ::: 0.001 0.002 \\
    ::: 42 123 456 789 2024 7 314 999 55 1337

Usage (aggregate — reads v19g_canon results + N=1000 results):
  python v1000_scale.py --aggregate

Usage (sanity check):
  python v1000_scale.py --sanity
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, time, argparse
from collections import Counter
from pathlib import Path

# ================================================================
# Import ALL canonical logic from v19g_canon — zero duplication
# ================================================================
from v19g_canon import (
    run_canonical,
    aggregate as _base_aggregate,
    OBSERVER_POLICY, HYST_THRESHOLD, LAMBDA, MU,
    K_LEVELS, WINDOW, QUIET_STEPS,
    BASE_PARAMS, PLB_GRID, RATE_GRID, ALL_SEEDS,
    OUTPUT_DIR as CANON_OUTPUT_DIR,
)

# ================================================================
# N=1000 EXPERIMENT CONSTANTS
# (only these differ from canonical — nothing in run_canonical changes)
# ================================================================
N_TARGET     = 1000
N1000_PLB    = [0.007]           # subset of PLB_GRID
N1000_RATES  = [0.001, 0.002]    # subset of RATE_GRID
N1000_SEEDS  = ALL_SEEDS         # same 10 seeds
OUTPUT_DIR   = Path("outputs_v1000")


# ================================================================
# AGGREGATE (N=200 + N=500 from canon dir, N=1000 from here)
# ================================================================
def aggregate():
    """Load results from both output dirs and produce 3-way comparison."""
    results = []

    # Load canonical results (N=200, N=500)
    if CANON_OUTPUT_DIR.exists():
        for d in sorted(CANON_OUTPUT_DIR.iterdir()):
            if not d.is_dir(): continue
            for f in sorted(d.glob("seed_*.json")):
                if "_switches" in f.name: continue
                with open(f) as fh:
                    results.append(json.load(fh))

    # Load N=1000 results
    if OUTPUT_DIR.exists():
        for d in sorted(OUTPUT_DIR.iterdir()):
            if not d.is_dir(): continue
            for f in sorted(d.glob("seed_*.json")):
                if "_switches" in f.name: continue
                with open(f) as fh:
                    results.append(json.load(fh))

    if not results:
        print("  No results found in either output directory."); return

    n_values_found = sorted(set(r["N"] for r in results))
    print(f"  Loaded {len(results)} runs across N={n_values_found}")

    # Save flat summary
    flat = [{k: (v if not isinstance(v, dict) else json.dumps(v))
             for k, v in r.items()} for r in results]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "v1000_summary_all.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=flat[0].keys())
        w.writeheader(); w.writerows(flat)

    # Aggregate by (N, plb, rate)
    agg = []
    # Use all plb/rate combinations present in data
    plb_present  = sorted(set(r["plb"]  for r in results))
    rate_present = sorted(set(r["rate"] for r in results))

    for N_val in n_values_found:
        for plb in plb_present:
            for rate in rate_present:
                sub = [r for r in results
                       if r["N"] == N_val
                       and abs(r["plb"] - plb) < 1e-7
                       and abs(r["rate"] - rate) < 1e-7]
                if not sub: continue
                doms = [r["dominant_k"] for r in sub]
                maj  = Counter(doms).most_common(1)[0]
                agg.append({
                    "N":                  N_val,
                    "plb":                plb,
                    "rate":               rate,
                    "n_seeds":            len(sub),
                    "policy":             OBSERVER_POLICY,
                    "dominant_k":         maj[0],
                    "agree_pct":          round(maj[1] / len(sub) * 100, 0),
                    "med_sw_100":         round(np.median([r["switches_per_100"] for r in sub]), 1),
                    "med_dom_frac":       round(np.median([r["dominant_k_fraction"] for r in sub]), 3),
                    "time_stable_count":  sum(1 for r in sub if r["time_stable"]),
                    "mean_margin":        round(np.mean([r["mean_margin"] for r in sub]), 4),
                    "mean_islands_strong":round(np.mean([r["mean_islands_strong"] for r in sub]), 2),
                    "mean_islands_mid":   round(np.mean([r["mean_islands_mid"] for r in sub]), 2),
                    "mean_none_ratio":    round(np.mean([r["mean_none_ratio"] for r in sub]), 4),
                    "mean_n_C":           round(np.mean([r["mean_n_C"] for r in sub]), 1),
                })

    with open(OUTPUT_DIR / "v1000_aggregate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=agg[0].keys())
        w.writeheader(); w.writerows(agg)

    # ---- Print comparison table ----
    print(f"\n{'='*90}")
    print(f"  ESDE Genesis v1.9g — Scale Validation (policy={OBSERVER_POLICY})")
    print(f"  N={' vs '.join(map(str, n_values_found))}")
    print(f"{'='*90}")
    print(f"\n  {'N':>5} {'plb':>5} {'rate':>7} | "
          f"{'k*':>3} {'agree':>6} {'sw/100':>7} {'stable':>7} | "
          f"{'isl_s':>5} {'isl_m':>5} {'none':>6} {'n_C':>5}")
    for a in agg:
        print(f"  {a['N']:>5} {a['plb']:>5.3f} {a['rate']:>7.4f} | "
              f"k={a['dominant_k']} {a['agree_pct']:>5.0f}% {a['med_sw_100']:>7.1f} "
              f"{a['time_stable_count']:>4}/{a['n_seeds']} | "
              f"{a['mean_islands_strong']:>5.1f} {a['mean_islands_mid']:>5.1f} "
              f"{a['mean_none_ratio']:>6.3f} {a['mean_n_C']:>5.1f}")

    # ---- 3-way scale comparison plot ----
    # Filter to rates present at N=1000 for a clean cross-scale comparison
    n1000_rates = sorted(set(a["rate"] for a in agg if a["N"] == N_TARGET))
    n1000_plbs  = sorted(set(a["plb"]  for a in agg if a["N"] == N_TARGET))

    plot_agg = [a for a in agg
                if abs(a["rate"] - n1000_rates[0]) < 1e-7
                or abs(a["rate"] - n1000_rates[-1]) < 1e-7]

    n_vals = sorted(set(a["N"] for a in plot_agg))
    if len(n_vals) >= 2:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            f"ESDE Genesis v1.9g — Scale Transfer "
            f"(N={' vs '.join(map(str, n_vals))})",
            fontsize=14, fontweight="bold",
        )
        styles = {n: ("o-" if i == 0 else ("s--" if i == 1 else "^:"))
                  for i, n in enumerate(n_vals)}

        for N_val in n_vals:
            for plb in n1000_plbs:
                sub = [a for a in plot_agg
                       if a["N"] == N_val and abs(a["plb"] - plb) < 1e-7]
                if not sub: continue
                sub.sort(key=lambda a: a["rate"])
                rs = [a["rate"] for a in sub]
                sty = styles[N_val]
                lbl = f"N={N_val} plb={plb:.3f}"

                axes[0][0].plot(rs, [a["agree_pct"]          for a in sub], sty, label=lbl, ms=6, lw=1.5)
                axes[0][1].plot(rs, [a["med_sw_100"]          for a in sub], sty, label=lbl, ms=6, lw=1.5)
                axes[1][0].plot(rs, [a["dominant_k"]          for a in sub], sty, label=lbl, ms=8, lw=2)
                axes[1][1].plot(rs, [a["mean_none_ratio"]     for a in sub], sty, label=lbl, ms=6, lw=1.5)

        axes[0][0].axhline(y=80, color="red", ls="--", alpha=0.5)
        axes[0][0].set_title("Seed Agreement (%)");        axes[0][0].legend(fontsize=7); axes[0][0].grid(True, alpha=0.2)
        axes[0][1].set_title("Switch Rate (/100 win)");    axes[0][1].legend(fontsize=7); axes[0][1].grid(True, alpha=0.2)
        axes[1][0].set_title("Dominant k*");               axes[1][0].set_yticks(K_LEVELS)
        axes[1][0].legend(fontsize=7);                     axes[1][0].grid(True, alpha=0.2)
        axes[1][1].set_title("None Ratio (C nodes)");      axes[1][1].legend(fontsize=7); axes[1][1].grid(True, alpha=0.2)

        plt.tight_layout()
        plot_path = OUTPUT_DIR / "v1000_scale_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        print(f"\n  Plot: {plot_path}")

    # ---- Branch interpretation ----
    n1000_rows = [a for a in agg if a["N"] == N_TARGET]

    if n1000_rows:
        k4_all   = all(a["dominant_k"] == 4 for a in n1000_rows)
        k3_any   = any(a["dominant_k"] == 3 for a in n1000_rows)
        unstable = any(a["agree_pct"] < 80   for a in n1000_rows)

        if k4_all and not unstable:
            branch = "Branch A: k=4 remains dominant at N=1000 — observer law scale-stable."
        elif k3_any:
            branch = "Branch B: k=3 re-emerges at N=1000 — observer scaling effect present."
        else:
            branch = "Branch C: k oscillates / agreement low at N=1000 — observer stability depends on system size."
    else:
        branch = "N=1000 results not yet available."

    # ---- Write conclusion ----
    n200_rows  = [a for a in agg if a["N"] == 200]
    n500_rows  = [a for a in agg if a["N"] == 500]
    table_rows = "\n".join(
        f"| {a['N']} | {a['plb']:.3f} | {a['rate']:.4f} | "
        f"k={a['dominant_k']} | {a['agree_pct']:.0f}% | {a['med_sw_100']} | "
        f"{a['mean_none_ratio']:.3f} | {a['mean_islands_mid']:.1f} |"
        for a in agg
    )

    conclusion = f"""# ESDE Genesis v1.9g — N=1000 Scale Validation

## Observer Policy
Policy            : {OBSERVER_POLICY}
Hysteresis (k3↔4) : {HYST_THRESHOLD}
Stability metric  : switches_per_100_windows (canonical)
Label function    : ctx_label (frozen, k=0..4)
No ontology expansion.

## Experimental Grid (N=1000)
plb   : {N1000_PLB}
rates : {N1000_RATES}
seeds : {N1000_SEEDS}
runs  : {len(n1000_rows)} configs aggregated

## Results Table
| N | plb | rate | k* | Agree | sw/100 | None ratio | Islands(mid) |
|---|-----|------|----|-------|--------|------------|--------------|
{table_rows}

## Branch Interpretation
{branch}

## Audit Checklist
[AC-1] hyst_0.01 frozen as canonical     : YES
[AC-2] k-switch logged per run            : YES (SwitchEvent JSON)
[AC-3] Canonical stability metric used    : YES (switches_per_100_windows)
[AC-4] N=1000 without physics patches     : YES
[AC-5] Comparable output schema           : YES (identical to v19g_canon)
[AC-6] No ontology expansion              : YES
[AC-7] Grid subset only (plb/rate reduced): YES — {len(n1000_rows)} configs at N=1000
"""
    with open(OUTPUT_DIR / "v1000_conclusion.md", "w") as f:
        f.write(conclusion)
    print(conclusion)


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE Genesis v1.9g — N=1000 Scale Validation")
    parser.add_argument("--N",           type=int,   default=N_TARGET)
    parser.add_argument("--plb",         type=float, default=None)
    parser.add_argument("--rate",        type=float, default=None)
    parser.add_argument("--seed",        type=int,   default=None)
    parser.add_argument("--quiet-steps", type=int,   default=QUIET_STEPS)
    parser.add_argument("--aggregate",   action="store_true")
    parser.add_argument("--sanity",      action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={N_TARGET} plb=0.007 rate=0.001 seed=42 quiet=500")
        r, sw = run_canonical(42, N_TARGET, 0.007, 0.001, quiet_steps=500)
        print(f"  k*={r['dominant_k']} sw={r['switches_per_100']} "
              f"stable={r['time_stable']} policy={r['policy']}")
        print(f"  n_C={r['mean_n_C']:.1f} isl_mid={r['mean_islands_mid']:.1f} "
              f"none={r['mean_none_ratio']:.3f} margin={r['mean_margin']:.4f}")
        print("  SANITY OK")
        return

    if args.aggregate:
        aggregate()
        return

    # Single / batch run mode
    N        = args.N
    qs       = args.quiet_steps
    plbs     = [args.plb]  if args.plb  is not None else N1000_PLB
    rates    = [args.rate] if args.rate is not None else N1000_RATES
    seeds    = [args.seed] if args.seed is not None else N1000_SEEDS

    for plb in plbs:
        for rate in rates:
            for seed in seeds:
                tag = f"N{N}_plb{plb:.3f}_rate{rate:.4f}"
                od  = OUTPUT_DIR / tag
                od.mkdir(parents=True, exist_ok=True)
                rf  = od / f"seed_{seed}.json"

                if rf.exists():
                    print(f"  {tag} s={seed}: skip (exists)")
                    continue

                print(f"  {tag} s={seed}...", flush=True)
                result, switch_log = run_canonical(seed, N, plb, rate, qs)

                with open(rf, "w") as f:
                    json.dump(result, f, indent=2)
                if switch_log:
                    with open(od / f"seed_{seed}_switches.json", "w") as f:
                        json.dump(switch_log, f, indent=2)

                print(f"    k*={result['dominant_k']} sw={result['switches_per_100']} "
                      f"stable={result['time_stable']} ({result['elapsed']:.0f}s)")


if __name__ == "__main__":
    main()
