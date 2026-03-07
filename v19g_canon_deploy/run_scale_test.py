#!/usr/bin/env python3
"""
ESDE Genesis — Scale Expansion Experiment Runner
=================================================
Phase : Post v1.9g Canonical Validation
Role  : Claude (Implementation)
Arch  : Taka / Gemini
Audit : GPT

PURPOSE
-------
Automated scale validation from N=200 to N=5000.
All physics / chemistry / observer logic is inherited verbatim from v19g_canon.
Only N changes between runs.

SCALE GRID
----------
  N    : [200, 500, 1000, 2000, 5000]
  plb  : [0.007]        (canonical — configurable via --plb)
  rate : [0.001, 0.002] (intrusion rate — configurable via --rate)
  seeds: 10 per config  (configurable via --seeds)

NOTE on "plb values 0.001, 0.002" in the audit spec:
  Those values correspond to the intrusion *rate* axis used in prior
  N=200/500/1000 experiments, not p_link_birth. This script maps them
  to --rate accordingly. plb (p_link_birth) remains 0.007 by default.

USAGE
-----
  # Sanity check (quiet=500)
  python run_scale_test.py --N 200 --sanity
  python run_scale_test.py --N 5000 --sanity

  # Single config
  python run_scale_test.py --N 2000 --plb 0.007 --rate 0.001 --seed 42

  # Full sweep for one N (GNU parallel, 48-thread Ryzen)
  parallel -j 20 python run_scale_test.py --N {1} --plb 0.007 --rate {2} --seed {3} \\
    ::: 2000 5000 \\
    ::: 0.001 0.002 \\
    ::: 42 123 456 789 2024 7 314 999 55 1337

  # Aggregate all N (reads outputs_scale_N* directories)
  python run_scale_test.py --aggregate
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, time, argparse
from collections import Counter
from pathlib import Path

# ================================================================
# All canonical logic imported — zero duplication
# ================================================================
from v19g_canon import (
    run_canonical,
    OBSERVER_POLICY, HYST_THRESHOLD,
    K_LEVELS, WINDOW, QUIET_STEPS,
    BASE_PARAMS, ALL_SEEDS,
)

# ================================================================
# SCALE EXPERIMENT CONSTANTS
# ================================================================
SCALE_N_VALUES = [200, 500, 1000, 2000, 5000]
DEFAULT_PLB    = [0.007]
DEFAULT_RATES  = [0.001, 0.002]
DEFAULT_SEEDS  = ALL_SEEDS   # 10 seeds

OUTPUT_ROOT    = Path("outputs_scale")   # outputs_scale/N200/, N500/, ...


def outdir(N: int) -> Path:
    return OUTPUT_ROOT / f"N{N}"


# ================================================================
# AGGREGATE — reads all N outputs, produces scale_summary.csv + plot
# ================================================================
def aggregate():
    results = []

    for N_val in SCALE_N_VALUES:
        d = outdir(N_val)
        if not d.exists():
            continue
        for sub in sorted(d.iterdir()):
            if not sub.is_dir():
                continue
            for f in sorted(sub.glob("seed_*.json")):
                if "_switches" in f.name:
                    continue
                with open(f) as fh:
                    results.append(json.load(fh))

    if not results:
        print("  No results found. Run experiments first.")
        return

    found_N = sorted(set(r["N"] for r in results))
    print(f"  Loaded {len(results)} runs across N={found_N}")

    # ---- Flat CSV ----
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    flat = [{k: (v if not isinstance(v, dict) else json.dumps(v))
             for k, v in r.items()} for r in results]
    with open(OUTPUT_ROOT / "scale_summary_flat.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=flat[0].keys())
        w.writeheader(); w.writerows(flat)

    # ---- Aggregate by (N, plb, rate) ----
    plb_present  = sorted(set(r["plb"]  for r in results))
    rate_present = sorted(set(r["rate"] for r in results))
    agg = []

    for N_val in found_N:
        for plb in plb_present:
            for rate in rate_present:
                sub = [r for r in results
                       if r["N"] == N_val
                       and abs(r["plb"]  - plb)  < 1e-7
                       and abs(r["rate"] - rate) < 1e-7]
                if not sub:
                    continue
                doms = [r["dominant_k"] for r in sub]
                maj  = Counter(doms).most_common(1)[0]
                agg.append({
                    "N":                   N_val,
                    "plb":                 plb,
                    "rate":                rate,
                    "n_seeds":             len(sub),
                    "policy":              OBSERVER_POLICY,
                    "dominant_k":          maj[0],
                    "agree_pct":           round(maj[1] / len(sub) * 100, 0),
                    "med_sw_100":          round(np.median([r["switches_per_100"] for r in sub]), 1),
                    "med_dom_frac":        round(np.median([r["dominant_k_fraction"] for r in sub]), 3),
                    "time_stable_count":   sum(1 for r in sub if r["time_stable"]),
                    "mean_margin":         round(np.mean([r["mean_margin"] for r in sub]), 4),
                    "mean_islands_strong": round(np.mean([r["mean_islands_strong"] for r in sub]), 2),
                    "mean_islands_mid":    round(np.mean([r["mean_islands_mid"] for r in sub]), 2),
                    "mean_none_ratio":     round(np.mean([r["mean_none_ratio"] for r in sub]), 4),
                    "mean_n_C":            round(np.mean([r["mean_n_C"] for r in sub]), 1),
                })

    with open(OUTPUT_ROOT / "scale_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=agg[0].keys())
        w.writeheader(); w.writerows(agg)

    # ---- Print table ----
    print(f"\n{'='*95}")
    print(f"  ESDE Genesis — Scale Validation Summary (policy={OBSERVER_POLICY})")
    print(f"  N values found: {found_N}")
    print(f"{'='*95}")
    print(f"\n  {'N':>5} {'plb':>5} {'rate':>7} | "
          f"{'k*':>3} {'agree':>6} {'sw/100':>7} {'stable':>7} | "
          f"{'isl_s':>5} {'isl_m':>5} {'none':>6} {'n_C':>5}")
    print(f"  {'-'*90}")
    for a in agg:
        print(f"  {a['N']:>5} {a['plb']:>5.3f} {a['rate']:>7.4f} | "
              f"k={a['dominant_k']} {a['agree_pct']:>5.0f}% {a['med_sw_100']:>7.1f} "
              f"{a['time_stable_count']:>4}/{a['n_seeds']} | "
              f"{a['mean_islands_strong']:>5.1f} {a['mean_islands_mid']:>5.1f} "
              f"{a['mean_none_ratio']:>6.3f} {a['mean_n_C']:>5.1f}")

    # ---- Plot: 4-panel scale comparison ----
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        f"ESDE Genesis v1.9g — Scale Expansion "
        f"(N={' → '.join(map(str, found_N))})",
        fontsize=14, fontweight="bold",
    )

    markers    = ['o', 's', '^', 'D', 'v', 'P']
    linestyles = ['-', '--', ':', '-.', '-', '--']

    for ri, rate in enumerate(rate_present):
        for ni, N_val in enumerate(found_N):
            sub = [a for a in agg
                   if a["N"] == N_val and abs(a["rate"] - rate) < 1e-7]
            if not sub:
                continue
            sub.sort(key=lambda a: a["plb"])
            xs  = [a["plb"] for a in sub]
            lbl = f"N={N_val} rate={rate}"
            sty = markers[ni % len(markers)]
            ls  = linestyles[ri % len(linestyles)]
            fmt = f"{sty}{ls}"

            axes[0][0].plot(xs, [a["agree_pct"]      for a in sub], fmt, label=lbl, ms=6, lw=1.5)
            axes[0][1].plot(xs, [a["med_sw_100"]      for a in sub], fmt, label=lbl, ms=6, lw=1.5)
            axes[1][0].plot(xs, [a["dominant_k"]      for a in sub], fmt, label=lbl, ms=8, lw=2)
            axes[1][1].plot(xs, [a["mean_none_ratio"] for a in sub], fmt, label=lbl, ms=6, lw=1.5)

    axes[0][0].axhline(y=80, color="red", ls="--", alpha=0.4, label="80% threshold")
    axes[0][0].set_title("Seed Agreement (%)");     axes[0][0].legend(fontsize=6); axes[0][0].grid(True, alpha=0.2)
    axes[0][1].set_title("Switch Rate (/100 win)"); axes[0][1].legend(fontsize=6); axes[0][1].grid(True, alpha=0.2)
    axes[1][0].set_title("Dominant k*");            axes[1][0].set_yticks(K_LEVELS)
    axes[1][0].legend(fontsize=6);                  axes[1][0].grid(True, alpha=0.2)
    axes[1][1].set_title("None Ratio (C nodes)");   axes[1][1].legend(fontsize=6); axes[1][1].grid(True, alpha=0.2)

    plt.tight_layout()
    plot_path = OUTPUT_ROOT / "scale_expansion_plot.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {plot_path}")

    # ---- N vs metric summary plot (single-axis trend) ----
    fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))
    fig2.suptitle("ESDE Genesis — Observer Stability vs System Size",
                  fontsize=13, fontweight="bold")

    for ri, rate in enumerate(rate_present):
        for plb in plb_present:
            sub = [a for a in agg if abs(a["rate"] - rate) < 1e-7
                   and abs(a["plb"] - plb) < 1e-7]
            if not sub:
                continue
            sub.sort(key=lambda a: a["N"])
            ns   = [a["N"] for a in sub]
            lbl  = f"plb={plb} rate={rate}"
            ls   = linestyles[ri % len(linestyles)]

            axes2[0].plot(ns, [a["agree_pct"]    for a in sub], f"o{ls}", label=lbl, ms=6, lw=1.5)
            axes2[1].plot(ns, [a["med_sw_100"]    for a in sub], f"o{ls}", label=lbl, ms=6, lw=1.5)
            axes2[2].plot(ns, [a["mean_none_ratio"] for a in sub], f"o{ls}", label=lbl, ms=6, lw=1.5)

    axes2[0].axhline(y=80, color="red", ls="--", alpha=0.4)
    axes2[0].set_title("Seed Agreement (%) vs N"); axes2[0].set_xlabel("N"); axes2[0].legend(fontsize=7); axes2[0].grid(True, alpha=0.2)
    axes2[1].set_title("Switch Rate vs N");        axes2[1].set_xlabel("N"); axes2[1].legend(fontsize=7); axes2[1].grid(True, alpha=0.2)
    axes2[2].set_title("None Ratio vs N");         axes2[2].set_xlabel("N"); axes2[2].legend(fontsize=7); axes2[2].grid(True, alpha=0.2)

    for ax in axes2:
        ax.set_xscale("log")
        ax.set_xticks(SCALE_N_VALUES)
        ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())

    plt.tight_layout()
    trend_path = OUTPUT_ROOT / "scale_trend_plot.png"
    plt.savefig(trend_path, dpi=150, bbox_inches="tight")
    print(f"  Trend plot: {trend_path}")
    print(f"  Summary CSV: {OUTPUT_ROOT / 'scale_summary.csv'}")

    # ---- Branch interpretation per N ----
    print(f"\n  Branch interpretations:")
    for N_val in found_N:
        rows = [a for a in agg if a["N"] == N_val]
        k4_all   = all(a["dominant_k"] == 4 for a in rows)
        k3_any   = any(a["dominant_k"] == 3 for a in rows)
        unstable = any(a["agree_pct"]  < 80  for a in rows)
        if k4_all and not unstable:
            tag = "A: k=4 dominant, agree ≥80%"
        elif k3_any:
            tag = "B: k=3 re-emerges"
        else:
            tag = "C: k=4 but agree <80% (size instability)"
        print(f"    N={N_val:>4}: Branch {tag}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE Genesis v1.9g — Scale Expansion N=200 to N=5000"
    )
    parser.add_argument("--N",           type=int,   default=None,
                        help=f"System size. Choices: {SCALE_N_VALUES}")
    parser.add_argument("--plb",         type=float, default=None,
                        help="p_link_birth. Default: 0.007")
    parser.add_argument("--rate",        type=float, default=None,
                        help="Intrusion rate. Default: sweep [0.001, 0.002]")
    parser.add_argument("--seed",        type=int,   default=None,
                        help="Single seed. Default: all 10 canonical seeds")
    parser.add_argument("--seeds",       type=int,   default=None,
                        help="Number of seeds (takes first N from canonical list)")
    parser.add_argument("--quiet-steps", type=int,   default=QUIET_STEPS)
    parser.add_argument("--aggregate",   action="store_true",
                        help="Aggregate all existing results and produce plots")
    parser.add_argument("--sanity",      action="store_true",
                        help="Quick sanity run (quiet=500)")
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    if args.aggregate:
        aggregate()
        return

    # Resolve N
    N = args.N
    if N is None:
        parser.error("--N is required for run mode (e.g. --N 2000)")
    if N not in SCALE_N_VALUES:
        print(f"  WARNING: N={N} not in standard grid {SCALE_N_VALUES}. Proceeding anyway.")

    if args.sanity:
        plb  = args.plb  if args.plb  is not None else DEFAULT_PLB[0]
        rate = args.rate if args.rate is not None else DEFAULT_RATES[0]
        print(f"  SANITY: N={N} plb={plb} rate={rate} seed=42 quiet=500")
        r, _ = run_canonical(42, N, plb, rate, quiet_steps=500)
        print(f"  k*={r['dominant_k']} sw={r['switches_per_100']} "
              f"stable={r['time_stable']} policy={r['policy']}")
        print(f"  n_C={r['mean_n_C']:.1f} isl_mid={r['mean_islands_mid']:.1f} "
              f"none={r['mean_none_ratio']:.3f} margin={r['mean_margin']:.4f} "
              f"elapsed={r['elapsed']:.1f}s")
        print("  SANITY OK")
        return

    # Resolve experiment grid
    plbs  = [args.plb]  if args.plb  is not None else DEFAULT_PLB
    rates = [args.rate] if args.rate is not None else DEFAULT_RATES
    if args.seed is not None:
        seeds = [args.seed]
    elif args.seeds is not None:
        seeds = DEFAULT_SEEDS[:args.seeds]
    else:
        seeds = DEFAULT_SEEDS

    qs = args.quiet_steps
    od_base = outdir(N)

    for plb in plbs:
        for rate in rates:
            for seed in seeds:
                tag = f"plb{plb:.3f}_rate{rate:.4f}"
                od  = od_base / tag
                od.mkdir(parents=True, exist_ok=True)
                rf  = od / f"seed_{seed}.json"

                if rf.exists():
                    print(f"  N={N} {tag} s={seed}: skip (exists)")
                    continue

                print(f"  N={N} {tag} s={seed}...", flush=True)
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
