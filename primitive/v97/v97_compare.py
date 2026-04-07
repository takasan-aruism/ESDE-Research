#!/usr/bin/env python3
"""
ESDE v9.6 vs v9.7 — Baseline vs Feedback Comparison
======================================================
Direct comparison: same seeds, same windows, before/after feedback.

Compares:
  diag_v96_baseline_{tag}/  vs  diag_v97_feedback_{tag}/

USAGE:
  python v97_compare.py --tag short
  python v97_compare.py --tag long
"""

import csv, json, glob, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict


def sf(v, d=0.0):
    try: return float(v) if v else d
    except: return d

def si(v, d=0):
    try: return int(v) if v else d
    except: return d


def load_csv(base, sub, prefix):
    rows = []
    for fp in sorted(glob.glob(str(base / sub / f"{prefix}*.csv"))):
        with open(fp) as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows


def load_json_files(base, sub, prefix):
    out = []
    for fp in sorted(glob.glob(str(base / sub / f"{prefix}*.json"))):
        with open(fp) as f:
            out.append(json.load(f))
    return out


def aggregate_window(rows):
    """Group by window number, return per-window stats."""
    by_w = defaultdict(list)
    for r in rows:
        by_w[int(r["window"])].append(r)
    out = {}
    for w, rs in by_w.items():
        out[w] = {
            "n": len(rs),
            "social": np.mean([sf(r.get("mean_social")) for r in rs]),
            "stability": np.mean([sf(r.get("mean_stability")) for r in rs]),
            "spread": np.mean([sf(r.get("mean_spread")) for r in rs]),
            "familiarity": np.mean([sf(r.get("mean_familiarity")) for r in rs]),
            "reciprocal": np.mean([si(r.get("reciprocal_pairs")) for r in rs]),
            "asymm": np.mean([si(r.get("asymmetric_pairs")) for r in rs]),
            "isolated": np.mean([si(r.get("count_isolated")) for r in rs]),
            "deeply": np.mean([si(r.get("count_deeply_connected")) for r in rs]),
            "att_overlap": np.mean([sf(r.get("att_overlap_mean")) for r in rs]),
            "links": np.mean([si(r.get("links")) for r in rs]),
            "labels": np.mean([si(r.get("v_labels")) for r in rs]),
            "alive": np.mean([si(r.get("alive_tracked")) for r in rs]),
        }
    return out


def aggregate_labels(rows):
    """Population statistics from per_label CSVs."""
    socials = [sf(r.get("last_social")) for r in rows]
    fams = [sf(r.get("last_familiarity")) for r in rows]
    parts = [si(r.get("last_partners")) for r in rows]
    lifespans = [si(r.get("lifespan")) for r in rows]
    spreads = [sf(r.get("last_spread")) for r in rows]
    sts = [sf(r.get("last_st_mean")) for r in rows]

    alive = [r for r in rows if r.get("alive") == "True"]
    dead = [r for r in rows if r.get("alive") == "False"]

    type_counter = defaultdict(int)
    for r in rows:
        for t in r.get("trajectory_type", "").split("|"):
            if t:
                type_counter[t] += 1

    return {
        "total": len(rows),
        "alive": len(alive),
        "dead": len(dead),
        "alive_pct": len(alive) / max(1, len(rows)) * 100,
        "social_mean": np.mean(socials) if socials else 0,
        "social_std": np.std(socials) if socials else 0,
        "fam_mean": np.mean(fams) if fams else 0,
        "fam_std": np.std(fams) if fams else 0,
        "fam_max": max(fams) if fams else 0,
        "partners_mean": np.mean(parts) if parts else 0,
        "partners_max": max(parts) if parts else 0,
        "lifespan_mean": np.mean(lifespans) if lifespans else 0,
        "lifespan_max": max(lifespans) if lifespans else 0,
        "spread_mean": np.mean(spreads) if spreads else 0,
        "st_max": max(sts) if sts else 0,
        "alive_social_mean": np.mean([sf(r.get("last_social")) for r in alive]) if alive else 0,
        "dead_social_mean": np.mean([sf(r.get("last_social")) for r in dead]) if dead else 0,
        "alive_partners_mean": np.mean([si(r.get("last_partners")) for r in alive]) if alive else 0,
        "dead_partners_mean": np.mean([si(r.get("last_partners")) for r in dead]) if dead else 0,
        "alive_fam_mean": np.mean([sf(r.get("last_familiarity")) for r in alive]) if alive else 0,
        "dead_fam_mean": np.mean([sf(r.get("last_familiarity")) for r in dead]) if dead else 0,
        "type_counter": dict(type_counter),
    }


def aggregate_conv_bias(jsons):
    ratios = [j.get("ratio") for j in jsons if j.get("ratio") is not None]
    convs = [j.get("conv_near_mean") for j in jsons if j.get("conv_near_mean") is not None]
    divs = [j.get("div_near_mean") for j in jsons if j.get("div_near_mean") is not None]
    return {
        "ratio_mean": np.mean(ratios) if ratios else None,
        "ratio_std": np.std(ratios) if ratios else None,
        "ratio_min": min(ratios) if ratios else None,
        "ratio_max": max(ratios) if ratios else None,
        "conv_mean": np.mean(convs) if convs else None,
        "div_mean": np.mean(divs) if divs else None,
        "n_seeds": len(ratios),
    }


def fmt_diff(b, f, fmt="{:.3f}"):
    """Format with delta arrow."""
    diff = f - b
    arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
    sign = "+" if diff >= 0 else ""
    return f"{fmt.format(b)} → {fmt.format(f)} ({sign}{fmt.format(diff)}) {arrow}"


def run(tag="short"):
    base_v96 = Path(f"diag_v96_baseline_{tag}")
    base_v97 = Path(f"diag_v97_feedback_{tag}")

    if not base_v96.exists():
        print(f"  ERROR: {base_v96} not found")
        return
    if not base_v97.exists():
        print(f"  ERROR: {base_v97} not found")
        return

    print(f"\n{'='*70}")
    print(f"  ESDE v9.6 vs v9.7 — BASELINE vs FEEDBACK ({tag})")
    print(f"{'='*70}")

    # Load
    v96_w = load_csv(base_v96, "aggregates", "per_window_seed")
    v97_w = load_csv(base_v97, "aggregates", "per_window_seed")
    v96_l = load_csv(base_v96, "labels", "per_label_seed")
    v97_l = load_csv(base_v97, "labels", "per_label_seed")
    v96_b = load_json_files(base_v96, "aggregates", "conv_bias_seed")
    v97_b = load_json_files(base_v97, "aggregates", "conv_bias_seed")

    print(f"\n  v96 baseline: {len(v96_w)} window rows, {len(v96_l)} labels")
    print(f"  v97 feedback: {len(v97_w)} window rows, {len(v97_l)} labels")

    # ════════════════════════════════════════════════════════
    # 1. Convergence bias (sanity check: should not collapse)
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  1. CONVERGENCE BIAS (structural sanity)")
    print(f"{'='*70}\n")

    cb_v96 = aggregate_conv_bias(v96_b)
    cb_v97 = aggregate_conv_bias(v97_b)

    if cb_v96["ratio_mean"] and cb_v97["ratio_mean"]:
        print(f"  conv/div ratio: {fmt_diff(cb_v96['ratio_mean'], cb_v97['ratio_mean'], '{:.2f}')}")
        print(f"  conv near%:     {fmt_diff(cb_v96['conv_mean'], cb_v97['conv_mean'], '{:.4f}')}")
        print(f"  div near%:      {fmt_diff(cb_v96['div_mean'], cb_v97['div_mean'], '{:.4f}')}")
        print(f"  std (v96/v97):  {cb_v96['ratio_std']:.3f} / {cb_v97['ratio_std']:.3f}")
        print(f"  range (v96):    [{cb_v96['ratio_min']:.2f}, {cb_v96['ratio_max']:.2f}]")
        print(f"  range (v97):    [{cb_v97['ratio_min']:.2f}, {cb_v97['ratio_max']:.2f}]")

    # ════════════════════════════════════════════════════════
    # 2. Population health
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  2. POPULATION HEALTH")
    print(f"{'='*70}\n")

    pop_v96 = aggregate_labels(v96_l)
    pop_v97 = aggregate_labels(v97_l)

    print(f"  Total labels:   {pop_v96['total']:>6} → {pop_v97['total']:>6} "
          f"({'+' if pop_v97['total']-pop_v96['total']>=0 else ''}{pop_v97['total']-pop_v96['total']})")
    print(f"  Alive labels:   {pop_v96['alive']:>6} → {pop_v97['alive']:>6} "
          f"({'+' if pop_v97['alive']-pop_v96['alive']>=0 else ''}{pop_v97['alive']-pop_v96['alive']})")
    print(f"  Survival %:     {fmt_diff(pop_v96['alive_pct'], pop_v97['alive_pct'], '{:.1f}')}")
    print(f"  Mean lifespan:  {fmt_diff(pop_v96['lifespan_mean'], pop_v97['lifespan_mean'], '{:.2f}')}")
    print(f"  Max lifespan:   {pop_v96['lifespan_max']} → {pop_v97['lifespan_max']}")

    # ════════════════════════════════════════════════════════
    # 3. Disposition distributions
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  3. DISPOSITION DISTRIBUTIONS")
    print(f"{'='*70}\n")

    print(f"  social mean:    {fmt_diff(pop_v96['social_mean'], pop_v97['social_mean'], '{:.4f}')}")
    print(f"  social std:     {fmt_diff(pop_v96['social_std'], pop_v97['social_std'], '{:.4f}')}")
    print(f"  familiarity m:  {fmt_diff(pop_v96['fam_mean'], pop_v97['fam_mean'], '{:.2f}')}")
    print(f"  familiarity std:{fmt_diff(pop_v96['fam_std'], pop_v97['fam_std'], '{:.2f}')}")
    print(f"  fam max:        {fmt_diff(pop_v96['fam_max'], pop_v97['fam_max'], '{:.2f}')}")
    print(f"  partners mean:  {fmt_diff(pop_v96['partners_mean'], pop_v97['partners_mean'], '{:.2f}')}")
    print(f"  partners max:   {pop_v96['partners_max']} → {pop_v97['partners_max']}")
    print(f"  spread mean:    {fmt_diff(pop_v96['spread_mean'], pop_v97['spread_mean'], '{:.4f}')}")
    print(f"  st_max:         {fmt_diff(pop_v96['st_max'], pop_v97['st_max'], '{:.1f}')}")

    # ════════════════════════════════════════════════════════
    # 4. Survival vs disposition (the key signal)
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  4. ALIVE vs DEAD (does feedback reshape selection?)")
    print(f"{'='*70}\n")

    print(f"  ALIVE social:    {fmt_diff(pop_v96['alive_social_mean'], pop_v97['alive_social_mean'], '{:.4f}')}")
    print(f"  DEAD  social:    {fmt_diff(pop_v96['dead_social_mean'], pop_v97['dead_social_mean'], '{:.4f}')}")
    print(f"  ALIVE partners:  {fmt_diff(pop_v96['alive_partners_mean'], pop_v97['alive_partners_mean'], '{:.2f}')}")
    print(f"  DEAD  partners:  {fmt_diff(pop_v96['dead_partners_mean'], pop_v97['dead_partners_mean'], '{:.2f}')}")
    print(f"  ALIVE familiar:  {fmt_diff(pop_v96['alive_fam_mean'], pop_v97['alive_fam_mean'], '{:.2f}')}")
    print(f"  DEAD  familiar:  {fmt_diff(pop_v96['dead_fam_mean'], pop_v97['dead_fam_mean'], '{:.2f}')}")

    # ════════════════════════════════════════════════════════
    # 5. Trajectory archetypes
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  5. ARCHETYPE COUNTS")
    print(f"{'='*70}\n")

    all_types = set(pop_v96["type_counter"].keys()) | set(pop_v97["type_counter"].keys())
    print(f"  {'archetype':>20} {'v96':>8} {'v97':>8} {'diff':>8}")
    print(f"  {'-'*48}")
    for t in sorted(all_types,
                     key=lambda x: -(pop_v96["type_counter"].get(x, 0) +
                                      pop_v97["type_counter"].get(x, 0))):
        c96 = pop_v96["type_counter"].get(t, 0)
        c97 = pop_v97["type_counter"].get(t, 0)
        diff = c97 - c96
        sign = "+" if diff >= 0 else ""
        print(f"  {t:>20} {c96:>8} {c97:>8} {sign}{diff:>7}")

    # ════════════════════════════════════════════════════════
    # 6. Per-window growth comparison
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  6. PER-WINDOW EVOLUTION")
    print(f"{'='*70}\n")

    w_v96 = aggregate_window(v96_w)
    w_v97 = aggregate_window(v97_w)

    common = sorted(set(w_v96.keys()) & set(w_v97.keys()))
    print(f"  {'win':>4} {'recip(v96)':>12} {'recip(v97)':>12} {'diff':>8} "
          f"{'social(v96)':>12} {'social(v97)':>12} {'diff':>8}")
    print(f"  {'-'*70}")
    for w in common:
        a, b = w_v96[w], w_v97[w]
        rd = b["reciprocal"] - a["reciprocal"]
        sd = b["social"] - a["social"]
        sign_r = "+" if rd >= 0 else ""
        sign_s = "+" if sd >= 0 else ""
        print(f"  {w:>4} {a['reciprocal']:>12.1f} {b['reciprocal']:>12.1f} "
              f"{sign_r}{rd:>7.1f} "
              f"{a['social']:>12.4f} {b['social']:>12.4f} "
              f"{sign_s}{sd:>7.4f}")

    # ════════════════════════════════════════════════════════
    # 7. Reciprocal growth rate
    # ════════════════════════════════════════════════════════
    if len(common) >= 2:
        first, last = common[0], common[-1]
        v96_growth = w_v96[last]["reciprocal"] - w_v96[first]["reciprocal"]
        v97_growth = w_v97[last]["reciprocal"] - w_v97[first]["reciprocal"]
        n_win = last - first

        print(f"\n  Reciprocal growth (w{first} → w{last}):")
        print(f"    v96: +{v96_growth:.1f} ({v96_growth/n_win:.1f}/win)")
        print(f"    v97: +{v97_growth:.1f} ({v97_growth/n_win:.1f}/win)")
        print(f"    feedback acceleration: {v97_growth/max(0.1, v96_growth):.2f}x")

    # ════════════════════════════════════════════════════════
    # 8. Torque factor stats (v97 only)
    # ════════════════════════════════════════════════════════
    if v97_w and "tf_mean" in v97_w[0]:
        print(f"\n{'='*70}")
        print(f"  7. TORQUE FACTOR DISTRIBUTION (v97 only)")
        print(f"{'='*70}\n")

        tf_means = [sf(r.get("tf_mean")) for r in v97_w]
        tf_stds = [sf(r.get("tf_std")) for r in v97_w]
        tf_maxs = [sf(r.get("tf_max")) for r in v97_w]
        tf_mins = [sf(r.get("tf_min")) for r in v97_w]

        print(f"  tf mean across all windows:  {np.mean(tf_means):.4f} (±{np.std(tf_means):.4f})")
        print(f"  tf std (population spread):  {np.mean(tf_stds):.4f}")
        print(f"  tf max observed:             {max(tf_maxs):.4f}")
        print(f"  tf min observed:             {min(tf_mins):.4f}")

        # Per-window evolution of tf
        print(f"\n  TF evolution (per window):")
        by_w_v97 = defaultdict(list)
        for r in v97_w:
            by_w_v97[int(r["window"])].append(r)
        print(f"  {'win':>4} {'tf_mean':>9} {'tf_std':>9} {'tf_min':>9} {'tf_max':>9}")
        for w in sorted(by_w_v97.keys()):
            rs = by_w_v97[w]
            print(f"  {w:>4} "
                  f"{np.mean([sf(r.get('tf_mean')) for r in rs]):>9.4f} "
                  f"{np.mean([sf(r.get('tf_std')) for r in rs]):>9.4f} "
                  f"{np.mean([sf(r.get('tf_min')) for r in rs]):>9.4f} "
                  f"{np.mean([sf(r.get('tf_max')) for r in rs]):>9.4f}")

    print(f"\n{'='*70}")
    print(f"  END COMPARISON")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.6 vs v9.7 Comparison")
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()
    run(tag=args.tag)
