#!/usr/bin/env python3
"""
ESDE v9.7 — Feedback Results Aggregator (+ v96 baseline comparison)
====================================================================
Combines per-seed CSVs and JSONs into unified summaries.
If ../v96/diag_v96_baseline_{tag}/ exists, also runs the same
aggregation on v96 baseline and prints a side-by-side delta block.

USAGE (from primitive/v97):
  python v97_aggregate.py --tag short
  python v97_aggregate.py --tag long

Layout assumed:
  primitive/v96/diag_v96_baseline_{tag}/   ← v96 baseline (optional)
  primitive/v97/diag_v97_feedback_{tag}/   ← v97 feedback (required)
  primitive/v97/v97_aggregate.py           ← THIS FILE
"""

import json, csv, argparse, glob
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict


# ════════════════════════════════════════════════════════════════
# Single-directory aggregation (returns metrics dict for comparison)
# ════════════════════════════════════════════════════════════════
def _aggregate_one(base: Path, label: str, verbose: bool = True) -> dict:
    """Aggregate one diag directory. Returns metrics dict (or {} on missing)."""
    if not base.exists():
        if verbose:
            print(f"  ERROR: {base} not found")
        return {}

    if verbose:
        print(f"\n{'='*65}")
        print(f"  {label}")
        print(f"  Source: {base}")
        print(f"{'='*65}\n")

    metrics = {"label": label, "base": str(base)}

    # ── 1. per_window CSVs ──
    window_files = sorted(glob.glob(str(base / "aggregates" / "per_window_seed*.csv")))
    all_window_rows = []
    for f in window_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_window_rows.append(row)

    n_seeds = len(window_files)
    if verbose:
        print(f"  Window CSVs: {n_seeds} seeds, {len(all_window_rows)} total rows")
    metrics["n_seeds"] = n_seeds
    metrics["n_window_rows"] = len(all_window_rows)

    if all_window_rows:
        # Save combined
        combined_w = base / "aggregates" / "combined_window_summary.csv"
        with open(combined_w, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_window_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_window_rows)

        # Per-window cross-seed summary
        by_window = defaultdict(list)
        for row in all_window_rows:
            w = int(row["window"])
            by_window[w].append(row)

        if verbose:
            print(f"\n  --- Per-Window Cross-Seed Summary ---\n")
            print(f"  {'win':>4} {'seeds':>5} {'social':>7} {'stabil':>7} "
                  f"{'spread':>7} {'famil':>7} {'recip':>6} {'asymm':>6} "
                  f"{'att_ov':>6} {'labels':>6}")
            print(f"  {'-'*65}")

        per_window_summary = {}
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
            per_window_summary[w] = {
                "social": ms, "stability": mst, "spread": msp,
                "familiarity": mf, "recip": mr, "asymm": ma,
                "att_overlap": mo, "labels": ml,
            }
            if verbose:
                print(f"  {w:>4} {ns:>5} {ms:>7.3f} {mst:>7.3f} "
                      f"{msp:>7.4f} {mf:>7.2f} {mr:>6.1f} {ma:>6.1f} "
                      f"{mo:>6.1f} {ml:>6.1f}")

        metrics["per_window"] = per_window_summary

        # Era deltas (first → last window)
        ws = sorted(by_window.keys())
        if len(ws) >= 2:
            first_w, last_w = ws[0], ws[-1]
            metrics["era"] = {
                "first_w": first_w, "last_w": last_w,
                "social_first": per_window_summary[first_w]["social"],
                "social_last": per_window_summary[last_w]["social"],
                "recip_first": per_window_summary[first_w]["recip"],
                "recip_last": per_window_summary[last_w]["recip"],
                "att_ov_first": per_window_summary[first_w]["att_overlap"],
                "att_ov_last": per_window_summary[last_w]["att_overlap"],
                "labels_first": per_window_summary[first_w]["labels"],
                "labels_last": per_window_summary[last_w]["labels"],
                "famil_first": per_window_summary[first_w]["familiarity"],
                "famil_last": per_window_summary[last_w]["familiarity"],
            }

    # ── 2. per_label CSVs ──
    label_files = sorted(glob.glob(str(base / "labels" / "per_label_seed*.csv")))
    all_label_rows = []
    for f in label_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_label_rows.append(row)

    if verbose:
        print(f"\n  Label CSVs: {len(label_files)} seeds, "
              f"{len(all_label_rows)} total labels")

    if all_label_rows:
        combined_l = base / "labels" / "combined_label_summary.csv"
        with open(combined_l, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_label_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_label_rows)

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

        metrics["n_labels"] = len(all_label_rows)
        metrics["n_alive"] = alive_count
        metrics["n_dead"] = dead_count
        metrics["mean_lifespan"] = float(np.mean(lifespans)) if lifespans else 0.0
        metrics["dist_social_mean"] = float(np.mean(socials)) if socials else 0.0
        metrics["dist_stability_mean"] = float(np.mean(stabilities)) if stabilities else 0.0
        metrics["dist_spread_mean"] = float(np.mean(spreads)) if spreads else 0.0
        metrics["dist_familiarity_mean"] = float(np.mean(familiarities)) if familiarities else 0.0

        if verbose:
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

        metrics["trajectory_types"] = dict(type_counter)

        if verbose:
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
            if verbose:
                print(f"\n  --- Death vs Disposition ---\n")
            death_disposition = {}
            for field in ["last_social", "last_stability", "last_spread",
                          "last_familiarity", "last_partners"]:
                d_vals = [float(r[field]) for r in dead_rows if r[field]]
                a_vals = [float(r[field]) for r in alive_rows if r[field]]
                if d_vals and a_vals:
                    a_mean = float(np.mean(a_vals))
                    d_mean = float(np.mean(d_vals))
                    death_disposition[field] = {
                        "alive": a_mean, "dead": d_mean, "diff": a_mean - d_mean
                    }
                    if verbose:
                        print(f"    {field:>18}: alive={a_mean:>7.3f} "
                              f"dead={d_mean:>7.3f} "
                              f"diff={a_mean-d_mean:>+7.3f}")
            metrics["death_disposition"] = death_disposition

    # ── 3. Convergence bias ──
    bias_files = sorted(glob.glob(str(base / "aggregates" / "conv_bias_seed*.json")))
    ratios, conv_means, div_means = [], [], []

    for f in bias_files:
        with open(f) as fh:
            data = json.load(fh)
            if data.get("ratio") is not None:
                ratios.append(data["ratio"])
            if data.get("conv_near_mean") is not None:
                conv_means.append(data["conv_near_mean"])
            if data.get("div_near_mean") is not None:
                div_means.append(data["div_near_mean"])

    if verbose:
        print(f"\n  --- Convergence Near-Phase Bias ({len(bias_files)} seeds) ---\n")
    if ratios:
        metrics["conv_ratio_mean"] = float(np.mean(ratios))
        metrics["conv_ratio_std"] = float(np.std(ratios))
        metrics["conv_ratio_min"] = float(min(ratios))
        metrics["conv_ratio_max"] = float(max(ratios))
        metrics["conv_near_mean"] = float(np.mean(conv_means))
        metrics["div_near_mean"] = float(np.mean(div_means))
        metrics["conv_seeds_above_1"] = sum(1 for r in ratios if r > 1.0)
        metrics["conv_seeds_total"] = len(ratios)
        if verbose:
            print(f"    conv/div ratio: mean={np.mean(ratios):.2f} "
                  f"std={np.std(ratios):.2f} "
                  f"min={min(ratios):.2f} max={max(ratios):.2f}")
            print(f"    conv near_phase: mean={np.mean(conv_means):.4f}")
            print(f"    div near_phase:  mean={np.mean(div_means):.4f}")
            above_1 = metrics["conv_seeds_above_1"]
            print(f"    Seeds with ratio > 1.0: {above_1}/{len(ratios)} "
                  f"({above_1/len(ratios)*100:.0f}%)")

    # ── 4. Familiarity network ──
    net_files = sorted(glob.glob(str(base / "network" / "fam_edges_seed*.csv")))
    edge_counts, fam_vals = [], []

    for f in net_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            edges = list(reader)
            edge_counts.append(len(edges))
            for e in edges:
                fam_vals.append(float(e["familiarity"]))

    if verbose:
        print(f"\n  --- Familiarity Network ({len(net_files)} seeds) ---\n")
    if edge_counts:
        metrics["edges_per_seed_mean"] = float(np.mean(edge_counts))
        metrics["edge_strength_mean"] = float(np.mean(fam_vals)) if fam_vals else 0.0
        metrics["edge_strength_max"] = float(max(fam_vals)) if fam_vals else 0.0
        if verbose:
            print(f"    Edges per seed: mean={np.mean(edge_counts):.0f} "
                  f"std={np.std(edge_counts):.0f} "
                  f"min={min(edge_counts)} max={max(edge_counts)}")
            print(f"    Edge strength: mean={np.mean(fam_vals):.2f} "
                  f"std={np.std(fam_vals):.2f} "
                  f"max={max(fam_vals):.2f}")

    # ── 5. Representative JSONs ──
    repr_files = sorted(glob.glob(str(base / "representatives" / "seed*_label*.json")))
    metrics["n_representatives"] = len(repr_files)
    if verbose:
        print(f"\n  Representative JSONs: {len(repr_files)} files")

        print(f"\n{'='*65}")
        print(f"  AGGREGATION COMPLETE: {label}")
        print(f"  Saved: {base}/aggregates/combined_window_summary.csv")
        print(f"  Saved: {base}/labels/combined_label_summary.csv")
        print(f"{'='*65}\n")

    return metrics


# ════════════════════════════════════════════════════════════════
# Side-by-side v96 vs v97 comparison
# ════════════════════════════════════════════════════════════════
def _format_delta(v97_val, v96_val, fmt=".4f"):
    """Format 'v96 → v97 (Δ)' string."""
    if v96_val is None or v97_val is None:
        return "n/a"
    delta = v97_val - v96_val
    sign = "+" if delta >= 0 else ""
    return f"{v96_val:{fmt}} → {v97_val:{fmt}} ({sign}{delta:{fmt}})"


def _compare(v97_metrics: dict, v96_metrics: dict, tag: str):
    """Print side-by-side comparison block."""
    print(f"\n{'='*70}")
    print(f"  v96 BASELINE  vs  v97 FEEDBACK   ({tag})")
    print(f"{'='*70}\n")

    # Sample sizes
    print(f"  --- Sample Sizes ---")
    print(f"    seeds:        v96={v96_metrics.get('n_seeds','?'):>5}  "
          f"v97={v97_metrics.get('n_seeds','?'):>5}")
    print(f"    window rows:  v96={v96_metrics.get('n_window_rows','?'):>5}  "
          f"v97={v97_metrics.get('n_window_rows','?'):>5}")
    print(f"    labels total: v96={v96_metrics.get('n_labels','?'):>5}  "
          f"v97={v97_metrics.get('n_labels','?'):>5}")
    print(f"    alive:        v96={v96_metrics.get('n_alive','?'):>5}  "
          f"v97={v97_metrics.get('n_alive','?'):>5}")
    print(f"    dead:         v96={v96_metrics.get('n_dead','?'):>5}  "
          f"v97={v97_metrics.get('n_dead','?'):>5}")

    if v96_metrics.get('n_seeds') != v97_metrics.get('n_seeds'):
        print(f"\n  NOTE: seed counts differ. "
              f"Comparison is across-population, not paired-by-seed.")

    # Convergence bias (the structural-property check)
    print(f"\n  --- Convergence Near-Phase Bias (structural property) ---")
    print(f"    conv/div ratio mean: "
          f"{_format_delta(v97_metrics.get('conv_ratio_mean'), v96_metrics.get('conv_ratio_mean'), '.3f')}")
    print(f"    conv near_phase:     "
          f"{_format_delta(v97_metrics.get('conv_near_mean'), v96_metrics.get('conv_near_mean'), '.4f')}")
    print(f"    div near_phase:      "
          f"{_format_delta(v97_metrics.get('div_near_mean'), v96_metrics.get('div_near_mean'), '.4f')}")
    print(f"    seeds ratio>1.0:     "
          f"v96={v96_metrics.get('conv_seeds_above_1','?')}/{v96_metrics.get('conv_seeds_total','?')}  "
          f"v97={v97_metrics.get('conv_seeds_above_1','?')}/{v97_metrics.get('conv_seeds_total','?')}")

    # Disposition distributions
    print(f"\n  --- Disposition Distributions (mean across all labels) ---")
    for key, name, fmt in [("dist_social_mean", "social", ".4f"),
                           ("dist_stability_mean", "stability", ".4f"),
                           ("dist_spread_mean", "spread", ".4f"),
                           ("dist_familiarity_mean", "familiarity", ".2f")]:
        print(f"    {name:>12}: "
              f"{_format_delta(v97_metrics.get(key), v96_metrics.get(key), fmt)}")
    print(f"    {'lifespan':>12}: "
          f"{_format_delta(v97_metrics.get('mean_lifespan'), v96_metrics.get('mean_lifespan'), '.2f')}")

    # Death vs disposition (the "social→survival" gap)
    v97_dd = v97_metrics.get("death_disposition", {})
    v96_dd = v96_metrics.get("death_disposition", {})
    if v97_dd and v96_dd:
        print(f"\n  --- Alive vs Dead Disposition Gap (alive - dead) ---")
        for field in ["last_social", "last_stability", "last_spread",
                      "last_familiarity", "last_partners"]:
            v97_diff = v97_dd.get(field, {}).get("diff")
            v96_diff = v96_dd.get(field, {}).get("diff")
            print(f"    {field:>18}: "
                  f"{_format_delta(v97_diff, v96_diff, '.3f')}")

    # Era deltas (first → last window growth)
    v97_era = v97_metrics.get("era", {})
    v96_era = v96_metrics.get("era", {})
    if v97_era and v96_era:
        print(f"\n  --- Era Growth (first → last window, Δ within run) ---")
        print(f"    {'metric':>14}  {'v96 Δ':>14}  {'v97 Δ':>14}  {'v97-v96':>10}")
        print(f"    {'-'*60}")
        for key_first, key_last, name, fmt in [
            ("social_first", "social_last", "social", ".3f"),
            ("recip_first", "recip_last", "recip", ".1f"),
            ("att_ov_first", "att_ov_last", "att_overlap", ".1f"),
            ("labels_first", "labels_last", "labels", ".1f"),
            ("famil_first", "famil_last", "familiarity", ".2f"),
        ]:
            v96_d = v96_era.get(key_last, 0) - v96_era.get(key_first, 0)
            v97_d = v97_era.get(key_last, 0) - v97_era.get(key_first, 0)
            diff = v97_d - v96_d
            print(f"    {name:>14}  {v96_d:>+14{fmt}}  {v97_d:>+14{fmt}}  "
                  f"{diff:>+10{fmt}}")

    # Trajectory types comparison
    v97_tt = v97_metrics.get("trajectory_types", {})
    v96_tt = v96_metrics.get("trajectory_types", {})
    if v97_tt and v96_tt:
        print(f"\n  --- Trajectory Type Counts ---")
        all_types = sorted(set(v97_tt.keys()) | set(v96_tt.keys()))
        for t in all_types:
            v96_c = v96_tt.get(t, 0)
            v97_c = v97_tt.get(t, 0)
            v96_pct = v96_c / max(1, v96_metrics.get("n_labels", 1)) * 100
            v97_pct = v97_c / max(1, v97_metrics.get("n_labels", 1)) * 100
            delta_pct = v97_pct - v96_pct
            sign = "+" if delta_pct >= 0 else ""
            print(f"    {t:>20}: v96={v96_c:>5} ({v96_pct:>5.1f}%)  "
                  f"v97={v97_c:>5} ({v97_pct:>5.1f}%)  "
                  f"Δ={sign}{delta_pct:>5.1f}pp")

    print(f"\n{'='*70}")
    print(f"  COMPARISON COMPLETE")
    print(f"{'='*70}\n")


# ════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════
def run(tag="short"):
    # v97 (required)
    v97_base = Path(f"diag_v97_feedback_{tag}")
    v97_metrics = _aggregate_one(
        v97_base, f"ESDE v9.7 — Feedback Aggregation ({tag})")

    if not v97_metrics:
        return

    # v96 (optional, sibling directory)
    v96_base = Path(f"../v96/diag_v96_baseline_{tag}")
    if v96_base.exists():
        v96_metrics = _aggregate_one(
            v96_base, f"ESDE v9.6 — Baseline Aggregation ({tag})")
        if v96_metrics:
            _compare(v97_metrics, v96_metrics, tag)
    else:
        print(f"\n  NOTE: v96 baseline not found at {v96_base}")
        print(f"        Skipping comparison block.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.7 Feedback Results Aggregator (+ v96 comparison)")
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()
    run(tag=args.tag)
