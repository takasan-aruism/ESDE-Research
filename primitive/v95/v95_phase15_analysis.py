#!/usr/bin/env python3
"""
ESDE v9.4+ — Phase 1.5: Symmetric Dual-Side Analysis
======================================================
Analyzes self-side (phase_sig) vs world-side (mean_theta_structural)
from existing phi_log.json. No new experiment needed.

USAGE:
  python v95_phase15_analysis.py --seed 42
"""

import json, math, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict


def circular_diff(a, b):
    """Circular difference in [-π, π]."""
    d = a - b
    while d > math.pi: d -= 2 * math.pi
    while d < -math.pi: d += 2 * math.pi
    return d


def run(seed=42, case_labels=None):
    if case_labels is None:
        case_labels = [87, 101, 112]

    indir = Path(f"diag_v94_phase1_seed{seed}")
    if not indir.exists():
        # Try v95
        indir = Path(f"diag_v95_phase1_seed{seed}")
    with open(indir / "phi_log.json") as f:
        phi_log = json.load(f)

    print(f"\n{'='*65}")
    print(f"  ESDE v9.4+ — Phase 1.5: Self vs World Symmetric Analysis")
    print(f"  Source: {indir}/phi_log.json")
    print(f"{'='*65}")

    # ════════════════════════════════════════════════════════
    # Per-label: Δ_phase = circular_diff(phase_sig, mean_theta_structural)
    # ════════════════════════════════════════════════════════

    label_stats = {}

    for lid_str, entries in phi_log.items():
        lid = int(lid_str)
        if len(entries) < 10:
            continue

        phase_sig = entries[0]["phase_sig"]
        deltas = []
        abs_deltas = []
        st_sizes = []
        st_mean_S_list = []

        for e in entries:
            world_theta = e["st_mean_theta"]
            delta = circular_diff(phase_sig, world_theta)
            deltas.append(delta)
            abs_deltas.append(abs(delta))
            st_sizes.append(e["st_total"])
            st_mean_S_list.append(e["st_mean_S"])

        # Δ stability: how much does Δ_phase change step-to-step?
        delta_diffs = [abs(deltas[i] - deltas[i-1])
                       for i in range(1, len(deltas))]
        # Normalize large jumps
        for i in range(len(delta_diffs)):
            if delta_diffs[i] > math.pi:
                delta_diffs[i] = 2 * math.pi - delta_diffs[i]

        # Correlation: |Δ_phase| vs structural size
        if len(abs_deltas) >= 10:
            corr_delta_size = np.corrcoef(abs_deltas, st_sizes)[0, 1]
        else:
            corr_delta_size = 0.0

        label_stats[lid] = {
            "phase_sig": phase_sig,
            "n_samples": len(entries),
            "delta_mean": round(np.mean(abs_deltas), 4),
            "delta_std": round(np.std(abs_deltas), 4),
            "delta_min": round(min(abs_deltas), 4),
            "delta_max": round(max(abs_deltas), 4),
            "delta_volatility": round(np.mean(delta_diffs), 4) if delta_diffs else 0,
            "st_size_mean": round(np.mean(st_sizes), 1),
            "st_mean_S_mean": round(np.mean(st_mean_S_list), 4),
            "corr_delta_size": round(corr_delta_size, 4),
            "deltas": deltas,
            "abs_deltas": abs_deltas,
            "st_sizes": st_sizes,
        }

    # ════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════

    print(f"\n  --- Δ_phase Summary (|self - world|) ---\n")
    print(f"  {'lid':>5} {'n':>5} {'Δ_mean':>7} {'Δ_std':>7} "
          f"{'Δ_min':>7} {'Δ_max':>7} {'volat':>7} "
          f"{'st_sz':>6} {'corr':>7}")
    print(f"  {'-'*62}")

    for lid in sorted(label_stats.keys()):
        s = label_stats[lid]
        print(f"  {lid:>5} {s['n_samples']:>5} "
              f"{s['delta_mean']:>7.4f} {s['delta_std']:>7.4f} "
              f"{s['delta_min']:>7.4f} {s['delta_max']:>7.4f} "
              f"{s['delta_volatility']:>7.4f} "
              f"{s['st_size_mean']:>6.0f} "
              f"{s['corr_delta_size']:>7.4f}")

    # ════════════════════════════════════════════════════════
    # KEY QUESTIONS
    # ════════════════════════════════════════════════════════

    print(f"\n{'='*65}")
    print(f"  KEY OBSERVATIONS")
    print(f"{'='*65}")

    # Q1: Who has small vs large Δ?
    sorted_by_delta = sorted(label_stats.items(),
                              key=lambda x: x[1]["delta_mean"])
    print(f"\n  Q1: Labels with smallest |self - world| gap:")
    for lid, s in sorted_by_delta[:3]:
        print(f"    L{lid}: Δ={s['delta_mean']:.4f} "
              f"(sig={s['phase_sig']:.4f}, st_sz={s['st_size_mean']:.0f})")
    print(f"\n  Labels with largest |self - world| gap:")
    for lid, s in sorted_by_delta[-3:]:
        print(f"    L{lid}: Δ={s['delta_mean']:.4f} "
              f"(sig={s['phase_sig']:.4f}, st_sz={s['st_size_mean']:.0f})")

    # Q2: Δ volatility vs structural size
    print(f"\n  Q2: Δ volatility vs structural size:")
    vols = [s["delta_volatility"] for s in label_stats.values()]
    sizes = [s["st_size_mean"] for s in label_stats.values()]
    if len(vols) >= 3:
        corr = np.corrcoef(vols, sizes)[0, 1]
        print(f"    Correlation: r={corr:.4f}")
        if corr > 0.3:
            print(f"    → Larger structural world = MORE volatile Δ")
        elif corr < -0.3:
            print(f"    → Larger structural world = LESS volatile Δ")
        else:
            print(f"    → No strong relationship")

    # Q3: Does Δ correlate with structural size within each label?
    print(f"\n  Q3: Does |Δ| correlate with structural size (per label)?")
    for lid in sorted(label_stats.keys()):
        s = label_stats[lid]
        r = s["corr_delta_size"]
        if abs(r) > 0.2:
            direction = "bigger world → bigger gap" if r > 0 else "bigger world → smaller gap"
            print(f"    L{lid}: r={r:+.4f} ({direction})")

    # ════════════════════════════════════════════════════════
    # CASE STUDY TIMELINES
    # ════════════════════════════════════════════════════════

    print(f"\n{'='*65}")
    print(f"  CASE STUDY: Self vs World Timelines")
    print(f"{'='*65}")

    for lid in case_labels:
        lid_str = str(lid)
        if lid_str not in phi_log:
            print(f"\n  Label {lid}: NOT FOUND")
            continue

        entries = phi_log[lid_str]
        if not entries:
            continue

        phase_sig = entries[0]["phase_sig"]
        print(f"\n  --- Label {lid} (phase_sig={phase_sig:.4f}) ---")
        print(f"  {'step':>5} {'self':>8} {'world':>8} {'Δ':>8} "
              f"{'|Δ|':>6} {'st':>4} {'st_S':>6}")
        print(f"  {'-'*50}")

        prev_w = None
        shown = 0
        for e in entries:
            if e["w"] != prev_w:
                prev_w = e["w"]
                shown = 0
                print(f"  {'--- window ' + str(e['w']) + ' ---':^50}")
            if shown < 20:
                world = e["st_mean_theta"]
                delta = circular_diff(phase_sig, world)
                print(f"  {e['step']:>5} {phase_sig:>8.4f} {world:>8.4f} "
                      f"{delta:>8.4f} {abs(delta):>6.4f} "
                      f"{e['st_total']:>4} {e['st_mean_S']:>6.4f}")
                shown += 1

    # ════════════════════════════════════════════════════════
    # ΔPHASE DISTRIBUTION
    # ════════════════════════════════════════════════════════

    print(f"\n{'='*65}")
    print(f"  Δ_phase DISTRIBUTION (all labels)")
    print(f"{'='*65}\n")

    all_abs_deltas = []
    for s in label_stats.values():
        all_abs_deltas.extend(s["abs_deltas"])

    if all_abs_deltas:
        bins = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.15]
        hist, _ = np.histogram(all_abs_deltas, bins=bins)
        total = len(all_abs_deltas)
        for i in range(len(bins)-1):
            bar = "█" * int(hist[i] / total * 100)
            print(f"  [{bins[i]:.1f}, {bins[i+1]:.1f}): "
                  f"{hist[i]:>6} ({hist[i]/total*100:>5.1f}%) {bar}")
        print(f"\n  mean={np.mean(all_abs_deltas):.4f} "
              f"median={np.median(all_abs_deltas):.4f}")

    # ════════════════════════════════════════════════════════
    # MOMENTS OF CONVERGENCE
    # ════════════════════════════════════════════════════════

    print(f"\n{'='*65}")
    print(f"  MOMENTS OF CONVERGENCE (|Δ| < 0.3)")
    print(f"{'='*65}\n")

    for lid in case_labels:
        s = label_stats.get(lid)
        if not s:
            continue
        entries = phi_log[str(lid)]
        convergences = []
        for i, e in enumerate(entries):
            delta = abs(circular_diff(e["phase_sig"], e["st_mean_theta"]))
            if delta < 0.3:
                convergences.append({
                    "w": e["w"], "step": e["step"],
                    "delta": round(delta, 4),
                    "st_total": e["st_total"],
                    "st_mean_S": e["st_mean_S"],
                })

        print(f"  Label {lid}: {len(convergences)} convergence moments "
              f"out of {len(entries)} samples "
              f"({len(convergences)/max(1,len(entries))*100:.1f}%)")
        if convergences:
            for c in convergences[:10]:
                print(f"    w={c['w']} step={c['step']} "
                      f"|Δ|={c['delta']:.4f} "
                      f"st={c['st_total']} st_S={c['st_mean_S']:.4f}")

    print(f"\n{'='*65}")
    print(f"  END Phase 1.5 Analysis")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4+ Phase 1.5: Symmetric Dual-Side Analysis")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--case-labels", type=str, default="87,101,112")
    args = parser.parse_args()
    cases = [int(x) for x in args.case_labels.split(",")]
    run(seed=args.seed, case_labels=cases)
