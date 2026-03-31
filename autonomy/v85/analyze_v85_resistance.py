#!/usr/bin/env python3
"""
ESDE v8.5 — Label Individual Resistance Pattern Analysis
==========================================================
Reads existing tracking_log from v8.5 48-seed mass test.
No new run needed. Analysis only.

Outputs:
  1. Per-label time series summary (resistance pattern classification)
  2. Size-stratified individual profiles
  3. Death pattern analysis (which side collapses first)

USAGE
-----
  python analyze_v85_resistance.py --dir diag_v85_tracking_A0.3
"""

import json, glob, argparse, math
import numpy as np
from collections import defaultdict
from pathlib import Path


def analyze_label_timeseries(entries):
    """Analyze a single label's tracking entries across windows.
    Returns a resistance profile dict.
    """
    if len(entries) < 3:
        return None

    windows = [e["window"] for e in entries]
    lifespan = max(windows) - min(windows) + 1

    # C-light time series
    link_ratios = [e.get("link_ratio", 0) for e in entries]
    oasis_alive_ts = [e.get("oasis_alive", 0) for e in entries]
    penalty_alive_ts = [e.get("penalty_alive", 0) for e in entries]
    oasis_links_ts = [e.get("oasis_links", 0) for e in entries]
    penalty_links_ts = [e.get("penalty_links", 0) for e in entries]

    # D-light time series
    terr_skew_ts = [e.get("terr_skew", 0) for e in entries]

    # Share time series
    share_ts = [e.get("share", 0) for e in entries]

    # ── Stability metrics ──
    # Link ratio stability (low CV = stable)
    lr_mean = np.mean(link_ratios) if link_ratios else 0
    lr_std = np.std(link_ratios) if link_ratios else 0
    lr_cv = lr_std / max(lr_mean, 0.001)

    # Terr skew stability
    ts_mean = np.mean(terr_skew_ts)
    ts_std = np.std(terr_skew_ts)

    # ── Trend detection ──
    # Is penalty side getting weaker over time?
    if len(penalty_alive_ts) >= 5:
        first_half = penalty_alive_ts[:len(penalty_alive_ts)//2]
        second_half = penalty_alive_ts[len(penalty_alive_ts)//2:]
        penalty_trend = np.mean(second_half) - np.mean(first_half)
    else:
        penalty_trend = 0

    if len(oasis_alive_ts) >= 5:
        first_half = oasis_alive_ts[:len(oasis_alive_ts)//2]
        second_half = oasis_alive_ts[len(oasis_alive_ts)//2:]
        oasis_trend = np.mean(second_half) - np.mean(first_half)
    else:
        oasis_trend = 0

    # ── Classification ──
    # Based on mean link_ratio and stability
    mean_oa = np.mean(oasis_alive_ts)
    mean_pa = np.mean(penalty_alive_ts)
    mean_ol = np.mean(oasis_links_ts)
    mean_pl = np.mean(penalty_links_ts)

    # Penalty fraction of time where penalty_alive = 0
    penalty_dead_frac = sum(1 for p in penalty_alive_ts if p < 0.5) / max(1, len(penalty_alive_ts))

    # Classification
    if penalty_dead_frac > 0.8:
        pattern = "penalty_collapsed"
    elif mean_pa > mean_oa and lr_cv < 0.5:
        pattern = "penalty_dominant"
    elif lr_cv < 0.3 and abs(ts_mean) < 0.05:
        pattern = "balanced_stable"
    elif lr_cv < 0.3 and ts_mean > 0.05:
        pattern = "oasis_stable"
    elif penalty_trend < -0.3:
        pattern = "penalty_eroding"
    elif lr_cv > 0.8:
        pattern = "volatile"
    else:
        pattern = "mixed"

    return {
        "label_id": entries[0]["label_id"],
        "nodes": entries[0]["nodes"],
        "lifespan": lifespan,
        "n_observations": len(entries),
        # C-light summary
        "mean_link_ratio": round(lr_mean, 3),
        "link_ratio_cv": round(lr_cv, 3),
        "mean_oasis_alive": round(mean_oa, 2),
        "mean_penalty_alive": round(mean_pa, 2),
        "mean_oasis_links": round(mean_ol, 2),
        "mean_penalty_links": round(mean_pl, 2),
        "penalty_dead_frac": round(penalty_dead_frac, 3),
        # D-light summary
        "mean_terr_skew": round(ts_mean, 4),
        "terr_skew_std": round(ts_std, 4),
        # Trends
        "penalty_trend": round(penalty_trend, 3),
        "oasis_trend": round(oasis_trend, 3),
        # Share
        "mean_share": round(np.mean(share_ts), 6),
        # Pattern
        "pattern": pattern,
    }


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v8.5 Label Resistance Pattern Analysis")
    parser.add_argument("--dir", required=True,
                        help="Directory with v8.5 detail.json files")
    args = parser.parse_args()

    d = args.dir
    jsons = sorted(glob.glob(str(Path(d) / "*_detail.json")))
    print(f"Seeds: {len(jsons)}")

    # Collect all tracking entries, grouped by (seed, label_id)
    all_profiles = []
    pattern_counts = defaultdict(lambda: defaultdict(int))
    size_profiles = defaultdict(list)

    for jf in jsons:
        with open(jf) as fh:
            data = json.load(fh)

        seed = data["meta"]["seed"]
        tracking = data.get("tracking_log", [])
        if not tracking:
            continue

        # Group by label_id
        by_label = defaultdict(list)
        for entry in tracking:
            by_label[entry["label_id"]].append(entry)

        for lid, entries in by_label.items():
            # Sort by window
            entries.sort(key=lambda e: e["window"])
            profile = analyze_label_timeseries(entries)
            if profile is None:
                continue
            profile["seed"] = seed
            all_profiles.append(profile)
            size_profiles[profile["nodes"]].append(profile)
            pattern_counts[profile["nodes"]][profile["pattern"]] += 1

    print(f"Total label profiles: {len(all_profiles)}")

    # ── §1: Pattern distribution by size ──
    print(f"\n{'='*72}")
    print(f"1. RESISTANCE PATTERN DISTRIBUTION BY SIZE")
    print(f"{'='*72}\n")

    all_patterns = set()
    for size_patterns in pattern_counts.values():
        all_patterns.update(size_patterns.keys())
    all_patterns = sorted(all_patterns)

    header = f"  {'size':>5}"
    for p in all_patterns:
        header += f" {p[:12]:>12}"
    header += f" {'total':>7}"
    print(header)
    print(f"  {'-'*(len(header)-2)}")

    for size in sorted(pattern_counts.keys()):
        row = f"  {size:>5}"
        total = sum(pattern_counts[size].values())
        for p in all_patterns:
            count = pattern_counts[size].get(p, 0)
            pct = count / max(1, total)
            row += f" {pct:>11.0%}" if count > 0 else f" {'—':>12}"
            #row += f" {count:>5}({pct:.0%})"
        row += f" {total:>7}"
        print(row)

    # ── §2: Per-size summary ──
    print(f"\n{'='*72}")
    print(f"2. PER-SIZE PROFILE SUMMARY")
    print(f"{'='*72}\n")

    print(f"  {'size':>5} {'n':>5} {'lifespan':>9} {'lr_mean':>8} {'lr_cv':>7} "
          f"{'oa_alive':>9} {'pn_alive':>9} {'pn_dead%':>9} {'skew':>7}")
    print(f"  {'-'*70}")

    for size in sorted(size_profiles.keys()):
        profs = size_profiles[size]
        print(f"  {size:>5} {len(profs):>5} "
              f"{np.mean([p['lifespan'] for p in profs]):>9.1f} "
              f"{np.mean([p['mean_link_ratio'] for p in profs]):>8.3f} "
              f"{np.mean([p['link_ratio_cv'] for p in profs]):>7.3f} "
              f"{np.mean([p['mean_oasis_alive'] for p in profs]):>9.2f} "
              f"{np.mean([p['mean_penalty_alive'] for p in profs]):>9.2f} "
              f"{np.mean([p['penalty_dead_frac'] for p in profs]):>8.1%} "
              f"{np.mean([p['mean_terr_skew'] for p in profs]):>7.4f}")

    # ── §3: Individual highlights ──
    print(f"\n{'='*72}")
    print(f"3. INDIVIDUAL LABEL HIGHLIGHTS")
    print(f"{'='*72}\n")

    # Most penalty-resistant (highest penalty_alive for their size)
    print(f"  --- Most penalty-resistant labels ---\n")
    for size in sorted(size_profiles.keys()):
        profs = size_profiles[size]
        if not profs:
            continue
        best = max(profs, key=lambda p: p["mean_penalty_alive"])
        print(f"  {size}-node: seed={best['seed']} label={best['label_id']} "
              f"pn_alive={best['mean_penalty_alive']:.2f} "
              f"lr={best['mean_link_ratio']:.3f} "
              f"skew={best['mean_terr_skew']:.4f} "
              f"pattern={best['pattern']} "
              f"lifespan={best['lifespan']}")

    # Most oasis-dependent (lowest penalty_alive)
    print(f"\n  --- Most oasis-dependent labels ---\n")
    for size in sorted(size_profiles.keys()):
        profs = size_profiles[size]
        if not profs:
            continue
        worst = min(profs, key=lambda p: p["mean_penalty_alive"])
        print(f"  {size}-node: seed={worst['seed']} label={worst['label_id']} "
              f"pn_alive={worst['mean_penalty_alive']:.2f} "
              f"lr={worst['mean_link_ratio']:.3f} "
              f"skew={worst['mean_terr_skew']:.4f} "
              f"pattern={worst['pattern']} "
              f"lifespan={worst['lifespan']}")

    # ── §4: Penalty erosion ──
    print(f"\n{'='*72}")
    print(f"4. PENALTY EROSION PATTERNS")
    print(f"{'='*72}\n")

    print(f"  {'size':>5} {'pn_trend':>9} {'oa_trend':>9} {'eroding%':>9}")
    print(f"  {'-'*35}")
    for size in sorted(size_profiles.keys()):
        profs = size_profiles[size]
        pn_trend = np.mean([p["penalty_trend"] for p in profs])
        oa_trend = np.mean([p["oasis_trend"] for p in profs])
        eroding = sum(1 for p in profs if p["penalty_trend"] < -0.3) / max(1, len(profs))
        print(f"  {size:>5} {pn_trend:>+9.3f} {oa_trend:>+9.3f} {eroding:>8.1%}")

    # ── §5: 2-node focus ──
    print(f"\n{'='*72}")
    print(f"5. 2-NODE INDIVIDUAL ANALYSIS")
    print(f"{'='*72}\n")

    profs_2 = size_profiles.get(2, [])
    if profs_2:
        for p in profs_2:
            print(f"  seed={p['seed']} label={p['label_id']} "
                  f"lifespan={p['lifespan']} "
                  f"oa_alive={p['mean_oasis_alive']:.2f} "
                  f"pn_alive={p['mean_penalty_alive']:.2f} "
                  f"pn_dead%={p['penalty_dead_frac']:.0%} "
                  f"lr={p['mean_link_ratio']:.3f} "
                  f"pattern={p['pattern']}")
    else:
        print(f"  No 2-node representative labels tracked.")


if __name__ == "__main__":
    main()
