#!/usr/bin/env python3
"""
ESDE v9.6 — Top-10 Rankings from Full Dataset
================================================
Extracts remarkable labels and patterns from combined CSVs.

USAGE:
  python v96_rankings.py --tag short
  python v96_rankings.py --tag long
  python v96_rankings.py --tag both   # combines short + long
"""

import csv, json, glob, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict


def load_labels(tag):
    rows = []
    for t in ([tag] if tag != "both" else ["short", "long"]):
        base = Path(f"diag_v97_feedback_{t}")
        p = base / "labels" / f"combined_label_summary.csv"
        if p.exists():
            with open(p) as f:
                for r in csv.DictReader(f):
                    r["_tag"] = t
                    rows.append(r)
        else:
            # Try individual files
            for fp in sorted(glob.glob(str(base / "labels" / "per_label_seed*.csv"))):
                with open(fp) as f:
                    for r in csv.DictReader(f):
                        r["_tag"] = t
                        rows.append(r)
    return rows


def load_network(tag):
    rows = []
    for t in ([tag] if tag != "both" else ["short", "long"]):
        base = Path(f"diag_v97_feedback_{t}")
        for fp in sorted(glob.glob(str(base / "network" / "fam_edges_seed*.csv"))):
            with open(fp) as f:
                for r in csv.DictReader(f):
                    r["_tag"] = t
                    rows.append(r)
    return rows


def safe_float(val, default=0.0):
    try:
        return float(val) if val else default
    except:
        return default


def safe_int(val, default=0):
    try:
        return int(val) if val else default
    except:
        return default


def run(tag="short"):
    labels = load_labels(tag)
    edges = load_network(tag)

    if not labels:
        print(f"  No data found for tag={tag}")
        return

    print(f"\n{'='*70}")
    print(f"  ESDE v9.7 — TOP-10 RANKINGS ({tag})")
    print(f"  {len(labels)} labels from {len(set(r['seed'] for r in labels))} seeds")
    print(f"{'='*70}")

    def print_ranking(title, sorted_rows, fields, n=10):
        print(f"\n  ══ {title} ══\n")
        header = f"  {'#':>3} {'seed':>4} {'lid':>5}"
        for fname, width in fields:
            header += f" {fname:>{width}}"
        header += f" {'type':>20} {'status':>8}"
        print(header)
        print(f"  {'-'*(len(header))}")
        for i, r in enumerate(sorted_rows[:n]):
            row_str = f"  {i+1:>3} {r['seed']:>4} {r['label_id']:>5}"
            for fname, width in fields:
                val = r.get(fname, "")
                try:
                    fv = float(val)
                    row_str += f" {fv:>{width}.2f}"
                except:
                    row_str += f" {str(val):>{width}}"
            tt = r.get("trajectory_type", "")[:20]
            alive = "ALIVE" if r.get("alive") == "True" else f"DEAD"
            row_str += f" {tt:>20} {alive:>8}"
            print(row_str)

    # ════════════════════════════════════════════════════════
    # 1. Most Social (highest last_social)
    # ════════════════════════════════════════════════════════
    by_social = sorted(labels, key=lambda r: safe_float(r.get("last_social")),
                        reverse=True)
    print_ranking("MOST SOCIAL LABELS", by_social,
                  [("last_social", 8), ("last_partners", 8),
                   ("lifespan", 8)])

    # ════════════════════════════════════════════════════════
    # 2. Most Isolated (lowest social, alive)
    # ════════════════════════════════════════════════════════
    alive_labels = [r for r in labels if r.get("alive") == "True"
                    and safe_float(r.get("last_social")) > 0]
    by_isolated = sorted(alive_labels,
                          key=lambda r: safe_float(r.get("last_social")))
    print_ranking("MOST ISOLATED (alive) LABELS", by_isolated,
                  [("last_social", 8), ("last_partners", 8),
                   ("lifespan", 8)])

    # ════════════════════════════════════════════════════════
    # 3. Deepest Relationships (highest last_familiarity)
    # ════════════════════════════════════════════════════════
    by_fam = sorted(labels,
                     key=lambda r: safe_float(r.get("last_familiarity")),
                     reverse=True)
    print_ranking("DEEPEST RELATIONSHIPS", by_fam,
                  [("last_familiarity", 10), ("last_partners", 8),
                   ("last_fam_max", 10)])

    # ════════════════════════════════════════════════════════
    # 4. Longest Survivors
    # ════════════════════════════════════════════════════════
    by_life = sorted(labels,
                      key=lambda r: safe_int(r.get("lifespan")),
                      reverse=True)
    print_ranking("LONGEST SURVIVORS", by_life,
                  [("lifespan", 8), ("last_social", 8),
                   ("last_partners", 8), ("last_familiarity", 10)])

    # ════════════════════════════════════════════════════════
    # 5. Shortest Lives (died quickly after birth)
    # ════════════════════════════════════════════════════════
    dead_labels = [r for r in labels if r.get("alive") == "False"]
    by_short = sorted(dead_labels,
                       key=lambda r: safe_int(r.get("lifespan")))
    print_ranking("SHORTEST LIVES (died)", by_short,
                  [("lifespan", 8), ("last_social", 8),
                   ("last_partners", 8)])

    # ════════════════════════════════════════════════════════
    # 6. Most Focused Attention (lowest entropy)
    # ════════════════════════════════════════════════════════
    has_spread = [r for r in labels
                  if safe_float(r.get("last_spread")) > 0]
    by_focused = sorted(has_spread,
                         key=lambda r: safe_float(r.get("last_spread")))
    print_ranking("MOST FOCUSED ATTENTION", by_focused,
                  [("last_spread", 8), ("last_att_nodes", 8),
                   ("last_social", 8)])

    # ════════════════════════════════════════════════════════
    # 7. Widest Attention (highest entropy)
    # ════════════════════════════════════════════════════════
    by_wide = sorted(has_spread,
                      key=lambda r: safe_float(r.get("last_spread")),
                      reverse=True)
    print_ranking("WIDEST ATTENTION", by_wide,
                  [("last_spread", 8), ("last_att_nodes", 8),
                   ("last_social", 8)])

    # ════════════════════════════════════════════════════════
    # 8. Most Partners (absolute count)
    # ════════════════════════════════════════════════════════
    by_partners = sorted(labels,
                          key=lambda r: safe_int(r.get("last_partners")),
                          reverse=True)
    print_ranking("MOST PARTNERS (absolute)", by_partners,
                  [("last_partners", 8), ("last_social", 8),
                   ("last_familiarity", 10), ("lifespan", 8)])

    # ════════════════════════════════════════════════════════
    # 9. Strongest Single Relationship (highest fam_max)
    # ════════════════════════════════════════════════════════
    by_fam_max = sorted(labels,
                         key=lambda r: safe_float(r.get("last_fam_max")),
                         reverse=True)
    print_ranking("STRONGEST SINGLE RELATIONSHIP", by_fam_max,
                  [("last_fam_max", 10), ("last_partners", 8),
                   ("last_familiarity", 10)])

    # ════════════════════════════════════════════════════════
    # 10. Social but Died (high social + dead)
    # ════════════════════════════════════════════════════════
    social_dead = [r for r in dead_labels
                   if safe_float(r.get("last_social")) > 0.5]
    social_dead_sorted = sorted(social_dead,
                                 key=lambda r: safe_float(r.get("last_social")),
                                 reverse=True)
    print_ranking("SOCIAL BUT DIED (social>0.5, dead)", social_dead_sorted,
                  [("last_social", 8), ("last_partners", 8),
                   ("lifespan", 8), ("last_familiarity", 10)])

    # ════════════════════════════════════════════════════════
    # 11. Largest Structural World (highest st_mean)
    # ════════════════════════════════════════════════════════
    by_st = sorted(labels,
                    key=lambda r: safe_float(r.get("last_st_mean")),
                    reverse=True)
    print_ranking("LARGEST STRUCTURAL WORLD", by_st,
                  [("last_st_mean", 8), ("last_st_std", 8),
                   ("last_social", 8), ("lifespan", 8)])

    # ════════════════════════════════════════════════════════
    # 12. Most Turbulent (highest st_std relative to st_mean)
    # ════════════════════════════════════════════════════════
    has_st = [r for r in labels if safe_float(r.get("last_st_mean")) > 1]
    for r in has_st:
        r["_volatility"] = (safe_float(r.get("last_st_std"))
                             / (safe_float(r.get("last_st_mean")) + 0.01))
    by_turb = sorted(has_st, key=lambda r: r.get("_volatility", 0),
                      reverse=True)
    print_ranking("MOST TURBULENT (st_std/st_mean)", by_turb,
                  [("last_st_mean", 8), ("last_st_std", 8),
                   ("last_stability", 8)])

    # ════════════════════════════════════════════════════════
    # STRONGEST MUTUAL PAIRS (from network edges)
    # ════════════════════════════════════════════════════════
    if edges:
        print(f"\n  ══ STRONGEST MUTUAL RELATIONSHIPS ══\n")

        # Build bidirectional lookup
        pair_fam = {}  # {(seed, a, b): (a→b, b→a)}
        for e in edges:
            seed = e["seed"]
            a, b = int(e["from"]), int(e["to"])
            key_ab = (seed, min(a, b), max(a, b))
            if key_ab not in pair_fam:
                pair_fam[key_ab] = [0.0, 0.0]
            fa = float(e["familiarity"])
            if a < b:
                pair_fam[key_ab][0] = max(pair_fam[key_ab][0], fa)
            else:
                pair_fam[key_ab][1] = max(pair_fam[key_ab][1], fa)

        # Compute mutual = min(a→b, b→a)
        mutual_pairs = []
        for (seed, a, b), (fab, fba) in pair_fam.items():
            mutual = min(fab, fba)
            if mutual > 0:
                symmetry = mutual / max(fab, fba) if max(fab, fba) > 0 else 0
                mutual_pairs.append({
                    "seed": seed, "a": a, "b": b,
                    "a_to_b": round(fab, 2), "b_to_a": round(fba, 2),
                    "mutual": round(mutual, 2),
                    "symmetry": round(symmetry, 3),
                })

        mutual_pairs.sort(key=lambda x: x["mutual"], reverse=True)

        print(f"  {'#':>3} {'seed':>4} {'A':>5} {'B':>5} "
              f"{'A→B':>7} {'B→A':>7} {'mutual':>7} {'symm':>6}")
        print(f"  {'-'*50}")
        for i, p in enumerate(mutual_pairs[:15]):
            print(f"  {i+1:>3} {p['seed']:>4} {p['a']:>5} {p['b']:>5} "
                  f"{p['a_to_b']:>7.1f} {p['b_to_a']:>7.1f} "
                  f"{p['mutual']:>7.1f} {p['symmetry']:>6.3f}")

        # Most asymmetric
        asym_pairs = sorted(mutual_pairs,
                             key=lambda x: x["symmetry"])
        print(f"\n  ══ MOST ASYMMETRIC RELATIONSHIPS ══\n")
        print(f"  {'#':>3} {'seed':>4} {'A':>5} {'B':>5} "
              f"{'A→B':>7} {'B→A':>7} {'mutual':>7} {'symm':>6}")
        print(f"  {'-'*50}")
        for i, p in enumerate(asym_pairs[:15]):
            print(f"  {i+1:>3} {p['seed']:>4} {p['a']:>5} {p['b']:>5} "
                  f"{p['a_to_b']:>7.1f} {p['b_to_a']:>7.1f} "
                  f"{p['mutual']:>7.1f} {p['symmetry']:>6.3f}")

    # ════════════════════════════════════════════════════════
    # SEED-LEVEL SUMMARY
    # ════════════════════════════════════════════════════════
    print(f"\n  ══ SEED-LEVEL DIVERSITY ══\n")

    seeds = defaultdict(list)
    for r in labels:
        seeds[r["seed"]].append(r)

    seed_stats = []
    for s, rows in seeds.items():
        alive = [r for r in rows if r.get("alive") == "True"]
        dead = [r for r in rows if r.get("alive") == "False"]
        socials = [safe_float(r.get("last_social")) for r in rows]
        seed_stats.append({
            "seed": s,
            "total": len(rows),
            "alive": len(alive),
            "dead": len(dead),
            "social_mean": round(np.mean(socials), 3) if socials else 0,
            "social_std": round(np.std(socials), 3) if socials else 0,
        })

    seed_stats.sort(key=lambda x: x["social_std"], reverse=True)
    print(f"  {'seed':>4} {'total':>6} {'alive':>6} {'dead':>6} "
          f"{'soc_mean':>8} {'soc_std':>8}")
    print(f"  {'-'*42}")
    for s in seed_stats[:10]:
        print(f"  {s['seed']:>4} {s['total']:>6} {s['alive']:>6} "
              f"{s['dead']:>6} {s['social_mean']:>8.3f} "
              f"{s['social_std']:>8.3f}")

    print(f"\n{'='*70}")
    print(f"  END RANKINGS")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.7 Top-10 Rankings")
    parser.add_argument("--tag", type=str, default="short",
                        help="short, long, or both")
    args = parser.parse_args()
    run(tag=args.tag)
