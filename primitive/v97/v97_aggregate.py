#!/usr/bin/env python3
"""
ESDE v9.7 — Feedback Results Aggregator
=========================================
Combines per-seed CSVs and JSONs into unified summaries.

USAGE:
  python v96_aggregate.py --tag short
  python v96_aggregate.py --tag long
"""

import json, csv, argparse, glob
import numpy as np
from pathlib import Path
from collections import Counter


def run(tag="short"):
    base = Path(f"diag_v97_feedback_{tag}")
    if not base.exists():
        print(f"  ERROR: {base} not found")
        return

    print(f"\n{'='*65}")
    print(f"  ESDE v9.7 — Feedback Aggregation ({tag})")
    print(f"{'='*65}\n")

    # ════════════════════════════════════════════════════════
    # 1. Aggregate per_window CSVs
    # ════════════════════════════════════════════════════════
    window_files = sorted(glob.glob(str(base / "aggregates" / "per_window_seed*.csv")))
    all_window_rows = []
    for f in window_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_window_rows.append(row)

    n_seeds = len(window_files)
    print(f"  Window CSVs: {n_seeds} seeds, {len(all_window_rows)} total rows")

    if all_window_rows:
        # Save combined
        combined_w = base / "aggregates" / "combined_window_summary.csv"
        with open(combined_w, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_window_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_window_rows)

        # Cross-seed summary per window
        from collections import defaultdict
        by_window = defaultdict(list)
        for row in all_window_rows:
            w = int(row["window"])
            by_window[w].append(row)

        print(f"\n  --- Per-Window Cross-Seed Summary ---\n")
        print(f"  {'win':>4} {'seeds':>5} {'social':>7} {'stabil':>7} "
              f"{'spread':>7} {'famil':>7} {'recip':>6} {'asymm':>6} "
              f"{'att_ov':>6} {'labels':>6}")
        print(f"  {'-'*65}")

        for w in sorted(by_window.keys()):
            rows = by_window[w]
            ns = len(rows)
            ms = np.mean([float(r["mean_social"]) for r in rows])
            mst = np.mean([float(r["mean_stability"]) for r in rows])
            msp = np.mean([float(r["mean_spread"]) for r in rows])
            mf = np.mean([float(r["mean_familiarity"]) for r in rows])
            mr = np.mean([int(r["reciprocal_pairs"]) for r in rows])
            ma = np.mean([int(r["asymmetric_pairs"]) for r in rows])
            mo = np.mean([float(r["att_overlap_mean"]) for r in rows])
            ml = np.mean([int(r["v_labels"]) for r in rows])
            print(f"  {w:>4} {ns:>5} {ms:>7.3f} {mst:>7.3f} "
                  f"{msp:>7.4f} {mf:>7.2f} {mr:>6.1f} {ma:>6.1f} "
                  f"{mo:>6.1f} {ml:>6.1f}")

    # ════════════════════════════════════════════════════════
    # 2. Aggregate per_label CSVs
    # ════════════════════════════════════════════════════════
    label_files = sorted(glob.glob(str(base / "labels" / "per_label_seed*.csv")))
    all_label_rows = []
    for f in label_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_label_rows.append(row)

    print(f"\n  Label CSVs: {len(label_files)} seeds, "
          f"{len(all_label_rows)} total labels")

    if all_label_rows:
        combined_l = base / "labels" / "combined_label_summary.csv"
        with open(combined_l, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_label_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_label_rows)

        # Distribution analysis
        socials = [float(r["last_social"]) for r in all_label_rows
                   if r["last_social"]]
        stabilities = [float(r["last_stability"]) for r in all_label_rows
                       if r["last_stability"]]
        spreads = [float(r["last_spread"]) for r in all_label_rows
                   if r["last_spread"]]
        familiarities = [float(r["last_familiarity"]) for r in all_label_rows
                         if r["last_familiarity"]]
        lifespans = [int(r["lifespan"]) for r in all_label_rows
                     if r["lifespan"]]
        alive_count = sum(1 for r in all_label_rows if r["alive"] == "True")
        dead_count = sum(1 for r in all_label_rows if r["alive"] == "False")

        print(f"\n  --- Label Population Summary ---\n")
        print(f"  Total labels: {len(all_label_rows)}")
        print(f"  Alive: {alive_count}  Dead: {dead_count}")
        print(f"  Mean lifespan: {np.mean(lifespans):.1f} windows "
              f"(std={np.std(lifespans):.1f})")

        print(f"\n  Disposition distributions:")
        for name, vals in [("social", socials), ("stability", stabilities),
                           ("spread", spreads), ("familiarity", familiarities)]:
            if vals:
                print(f"    {name:>12}: mean={np.mean(vals):.4f} "
                      f"std={np.std(vals):.4f} "
                      f"min={min(vals):.4f} max={max(vals):.4f}")

        # Trajectory type distribution
        type_counter = Counter()
        for r in all_label_rows:
            tt = r.get("trajectory_type", "")
            for t in tt.split("|"):
                if t:
                    type_counter[t] += 1

        print(f"\n  Trajectory type frequency:")
        for t, c in type_counter.most_common():
            pct = c / len(all_label_rows) * 100
            bar = "█" * int(pct / 2)
            print(f"    {t:>20}: {c:>5} ({pct:>5.1f}%) {bar}")

        # Death vs disposition
        dead_rows = [r for r in all_label_rows if r["alive"] == "False"
                     and r["last_social"]]
        alive_rows = [r for r in all_label_rows if r["alive"] == "True"
                      and r["last_social"]]

        if dead_rows and alive_rows:
            print(f"\n  --- Death vs Disposition ---\n")
            for field in ["last_social", "last_stability", "last_spread",
                          "last_familiarity", "last_partners"]:
                d_vals = [float(r[field]) for r in dead_rows if r[field]]
                a_vals = [float(r[field]) for r in alive_rows if r[field]]
                if d_vals and a_vals:
                    print(f"    {field:>18}: alive={np.mean(a_vals):>7.3f} "
                          f"dead={np.mean(d_vals):>7.3f} "
                          f"diff={np.mean(a_vals)-np.mean(d_vals):>+7.3f}")

    # ════════════════════════════════════════════════════════
    # 3. Aggregate convergence bias
    # ════════════════════════════════════════════════════════
    bias_files = sorted(glob.glob(str(base / "aggregates" / "conv_bias_seed*.json")))
    ratios = []
    conv_means = []
    div_means = []

    for f in bias_files:
        with open(f) as fh:
            data = json.load(fh)
            if data.get("ratio") is not None:
                ratios.append(data["ratio"])
            if data.get("conv_near_mean") is not None:
                conv_means.append(data["conv_near_mean"])
            if data.get("div_near_mean") is not None:
                div_means.append(data["div_near_mean"])

    print(f"\n  --- Convergence Near-Phase Bias ({len(bias_files)} seeds) ---\n")
    if ratios:
        print(f"    conv/div ratio: mean={np.mean(ratios):.2f} "
              f"std={np.std(ratios):.2f} "
              f"min={min(ratios):.2f} max={max(ratios):.2f}")
        print(f"    conv near_phase: mean={np.mean(conv_means):.4f}")
        print(f"    div near_phase:  mean={np.mean(div_means):.4f}")
        above_1 = sum(1 for r in ratios if r > 1.0)
        print(f"    Seeds with ratio > 1.0: {above_1}/{len(ratios)} "
              f"({above_1/len(ratios)*100:.0f}%)")

    # ════════════════════════════════════════════════════════
    # 4. Familiarity network summary
    # ════════════════════════════════════════════════════════
    net_files = sorted(glob.glob(str(base / "network" / "fam_edges_seed*.csv")))
    edge_counts = []
    fam_vals = []

    for f in net_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            edges = list(reader)
            edge_counts.append(len(edges))
            for e in edges:
                fam_vals.append(float(e["familiarity"]))

    print(f"\n  --- Familiarity Network ({len(net_files)} seeds) ---\n")
    if edge_counts:
        print(f"    Edges per seed: mean={np.mean(edge_counts):.0f} "
              f"std={np.std(edge_counts):.0f} "
              f"min={min(edge_counts)} max={max(edge_counts)}")
    if fam_vals:
        print(f"    Edge strength: mean={np.mean(fam_vals):.2f} "
              f"std={np.std(fam_vals):.2f} "
              f"max={max(fam_vals):.2f}")

    # ════════════════════════════════════════════════════════
    # 5. Representative label stats
    # ════════════════════════════════════════════════════════
    repr_files = sorted(glob.glob(str(base / "representatives" / "seed*_label*.json")))
    print(f"\n  Representative JSONs: {len(repr_files)} files")

    print(f"\n{'='*65}")
    print(f"  AGGREGATION COMPLETE")
    print(f"  Saved: {base}/aggregates/combined_window_summary.csv")
    print(f"  Saved: {base}/labels/combined_label_summary.csv")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.6 Baseline Results Aggregator")
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()
    run(tag=args.tag)
