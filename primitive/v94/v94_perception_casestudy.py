#!/usr/bin/env python3
"""
ESDE v9.4 — Perception Field Case Study + Map
================================================
3 labels: 87 (social/alien), 101 (small/familiar), 112 (huge/isolated)
Outputs grid maps + correlation analysis.

USAGE:
  python v94_perception_casestudy.py --seed 42
"""

import json, math, csv, sys
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent

def load_data(seed):
    d = Path(f"diag_v94_perception_seed{seed}")
    with open(d / "per_label_perception.json") as f:
        perceptions = json.load(f)
    overlaps = []
    ov_path = d / "pairwise_overlap.csv"
    if ov_path.exists():
        with open(ov_path) as f:
            overlaps = list(csv.DictReader(f))
    return perceptions, overlaps


def build_torus_substrate(N):
    side = int(math.ceil(math.sqrt(N)))
    adj = {}
    for i in range(N):
        r, c = i // side, i % side
        nbs = []
        nbs.append(((r - 1) % side) * side + c)
        nbs.append(((r + 1) % side) * side + c)
        nbs.append(r * side + ((c - 1) % side))
        nbs.append(r * side + ((c + 1) % side))
        adj[i] = [nb for nb in nbs if nb < N]
    return adj


def bfs_perception(core_nodes, max_hops, torus_sub, alive_n):
    visited = {}
    for n in core_nodes:
        if n in alive_n:
            visited[n] = 0
    frontier = set(n for n in core_nodes if n in alive_n)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in torus_sub.get(n, []):
                if nb not in visited and nb in alive_n:
                    visited[nb] = hop
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited


def print_grid_map(label_id, perc, all_perceptions, N=5000):
    """Print ASCII grid showing label's perception field."""
    side = int(math.ceil(math.sqrt(N)))

    # Rebuild visible set via BFS
    torus_sub = build_torus_substrate(N)

    # We need alive_n - approximate from perception data
    # For grid map, we just show the structure
    core_nodes = set()
    other_cores = {}
    for p in all_perceptions:
        if p["label_id"] == label_id:
            # We don't have the raw node list, so reconstruct from grid position
            pass

    # Instead, use the JSON data to show statistics
    print(f"\n{'='*65}")
    print(f"  CASE STUDY: Label {label_id}")
    print(f"{'='*65}")
    print(f"  Core nodes: {perc['n_core']}")
    print(f"  Max hops: {perc['max_hops']}")
    print(f"  Visible total: {perc['visible_total']}")
    print(f"  Wild: {perc['wild_count']} ({perc['wild_count']/max(1,perc['visible_total'])*100:.0f}%)")
    print(f"  Other label cores: {perc['other_label_core_count']}")
    print(f"  Other labels seen: {perc['n_other_labels_seen']}")
    if perc.get("other_labels_visible"):
        print(f"  Who they see:")
        for other_lid, count in sorted(perc["other_labels_visible"].items(),
                                         key=lambda x: x[1], reverse=True):
            print(f"    Label {other_lid}: {count} core nodes visible")
    print(f"\n  Phase character:")
    print(f"    phase_sig: {perc['phase_sig']:.4f}")
    print(f"    mean_theta of visible: {perc['mean_theta']:.4f}")
    print(f"    theta_variance: {perc['theta_variance']:.4f}")
    print(f"    mean_phase_diff: {perc['mean_phase_diff']:.4f}")
    print(f"    near_phase_ratio: {perc['near_phase_ratio']*100:.1f}%")
    print(f"    far_phase_count: {perc['far_phase_count']}")
    print(f"\n  Physical:")
    print(f"    mean_link_S: {perc['mean_link_strength']:.4f}")
    print(f"    visible_links: {perc['visible_links']}")
    print(f"    share: {perc['share']:.6f}")
    print(f"    born: {perc['born']}")

    # Hop shell distribution
    print(f"\n  Hop shell distribution:")
    shells = perc.get("hop_shell_sizes", {})
    cumul = 0
    for hop in sorted(shells.keys(), key=int):
        count = shells[hop]
        cumul += count
        bar = "█" * min(count // 2, 40)
        print(f"    hop {hop:>2}: {count:>4} nodes (cumul {cumul:>4}) {bar}")


def print_overlap_analysis(label_id, overlaps, all_perceptions):
    """Show overlap details for a specific label."""
    print(f"\n  Overlap with others:")
    my_overlaps = [o for o in overlaps
                   if int(o["label_a"]) == label_id or int(o["label_b"]) == label_id]

    if not my_overlaps:
        print(f"    No overlaps.")
        return

    for o in sorted(my_overlaps, key=lambda x: int(x["overlap_count"]), reverse=True):
        a, b = int(o["label_a"]), int(o["label_b"])
        other = b if a == label_id else a
        ov = int(o["overlap_count"])
        cv_ab = int(o["core_visible_a_to_b"])
        cv_ba = int(o["core_visible_b_to_a"])
        if a == label_id:
            my_ratio = float(o["overlap_ratio_a"])
            sees_core = cv_ab
            seen_by = cv_ba
        else:
            my_ratio = float(o["overlap_ratio_b"])
            sees_core = cv_ba
            seen_by = cv_ab

        print(f"    ↔ Label {other:>4}: overlap={ov:>3} "
              f"({my_ratio:.0%} of my world) "
              f"I see {sees_core} of their core, "
              f"they see {seen_by} of mine")


def print_correlations(perceptions):
    """Print correlation matrix between key metrics."""
    print(f"\n{'='*65}")
    print(f"  CORRELATION ANALYSIS")
    print(f"{'='*65}\n")

    metrics = {
        "n_core": [],
        "visible_total": [],
        "n_seen": [],
        "near_phase_ratio": [],
        "theta_variance": [],
        "share": [],
        "mean_phase_diff": [],
    }

    for p in perceptions:
        metrics["n_core"].append(p["n_core"])
        metrics["visible_total"].append(p["visible_total"])
        metrics["n_seen"].append(p["n_other_labels_seen"])
        metrics["near_phase_ratio"].append(p["near_phase_ratio"])
        metrics["theta_variance"].append(p["theta_variance"])
        metrics["share"].append(p["share"])
        metrics["mean_phase_diff"].append(p["mean_phase_diff"])

    keys = list(metrics.keys())
    print(f"  {'':>18}", end="")
    for k in keys:
        print(f" {k[:8]:>8}", end="")
    print()
    print(f"  {'-'*18}" + "-" * (9 * len(keys)))

    for k1 in keys:
        print(f"  {k1:>18}", end="")
        for k2 in keys:
            r = np.corrcoef(metrics[k1], metrics[k2])[0, 1]
            print(f" {r:>8.3f}", end="")
        print()

    # Key findings
    print(f"\n  Key correlations:")
    pairs = []
    for i, k1 in enumerate(keys):
        for j, k2 in enumerate(keys):
            if j > i:
                r = np.corrcoef(metrics[k1], metrics[k2])[0, 1]
                pairs.append((abs(r), r, k1, k2))

    for _, r, k1, k2 in sorted(pairs, reverse=True)[:5]:
        sign = "+" if r > 0 else ""
        print(f"    {k1} × {k2}: r={sign}{r:.3f}")


def main(seed=42):
    perceptions, overlaps = load_data(seed)

    # Case studies
    cases = [87, 101, 112]
    for lid in cases:
        perc = next((p for p in perceptions if p["label_id"] == lid), None)
        if perc is None:
            print(f"\n  Label {lid} not found!")
            continue
        print_grid_map(lid, perc, perceptions)
        print_overlap_analysis(lid, overlaps, perceptions)

    # Compare the 3
    print(f"\n\n{'='*65}")
    print(f"  3-WAY COMPARISON")
    print(f"{'='*65}\n")

    header = f"  {'metric':<25}"
    for lid in cases:
        header += f" {'L'+str(lid):>8}"
    print(header)
    print(f"  {'-'*25}" + "-" * (9 * len(cases)))

    compare_fields = [
        ("n_core", "Core nodes"),
        ("max_hops", "Perception hops"),
        ("visible_total", "Visible total"),
        ("wild_count", "Wild nodes"),
        ("other_label_core_count", "Other cores seen"),
        ("n_other_labels_seen", "Other labels seen"),
        ("theta_variance", "θ variance"),
        ("mean_phase_diff", "Mean Δφ"),
        ("near_phase_ratio", "Near-phase %"),
        ("mean_link_strength", "Mean link S"),
        ("share", "Share"),
        ("born", "Born window"),
    ]

    case_percs = {}
    for lid in cases:
        case_percs[lid] = next((p for p in perceptions if p["label_id"] == lid), {})

    for field, label in compare_fields:
        row = f"  {label:<25}"
        for lid in cases:
            val = case_percs[lid].get(field, "—")
            if isinstance(val, float):
                if field == "near_phase_ratio":
                    row += f" {val*100:>7.1f}%"
                elif field == "share":
                    row += f" {val:>8.4f}"
                else:
                    row += f" {val:>8.4f}"
            else:
                row += f" {val:>8}"
        print(row)

    # Correlation analysis
    print_correlations(perceptions)

    print(f"\n{'='*65}")
    print(f"  END Case Study")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.seed)
