#!/usr/bin/env python3
"""
ESDE v8.2 — Deep Relation Analysis
======================================
GPT audit items for relation layer exploration:
1. Long co-existence pairs: phase distance clustering
2. Displacement direction: which size pushes out which
3. 3-body co-existence motifs (stable trios)
4. Stable trio/quartet persistence
5. Size-role differentiation in relations

Usage:
  python analyze_relations_deep.py --dir diag_v82_baseline
"""

import json, glob, argparse, numpy as np, math
from collections import defaultdict, Counter
from pathlib import Path


def main(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data

    print(f"{'='*72}")
    print(f"DEEP RELATION ANALYSIS")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'='*72}")

    # ═══════════════════════════════════════════
    # BUILD PER-SEED STRUCTURES
    # ═══════════════════════════════════════════

    all_disp_size = []       # displacement: (dead_size, killer_size)
    all_stable_trios = []    # persistent 3-label groups
    all_stable_quads = []    # persistent 4-label groups
    all_long_pairs = []      # pairs coexisting > 80 windows
    all_cluster_info = []    # cluster membership info

    for seed_id, (seed, data) in enumerate(sorted(seeds.items())):
        log = data["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)

        max_win = max(e["window"] for e in log)

        # Build label info
        label_info = {}
        alive_per_win = defaultdict(set)

        for lid, entries in traj.items():
            births = [e for e in entries if e["event"] == "birth"]
            deaths = [e for e in entries if e["event"] == "death"]
            alives = [e for e in entries if e["event"] in ("birth", "alive")]
            if not births:
                continue

            born_win = births[0]["window"]
            died_win = deaths[0]["window"] if deaths else max_win + 1
            phase_sig = births[0].get("phase_sig", 0)
            nodes = births[0]["nodes"]

            label_info[lid] = {
                "phase_sig": phase_sig,
                "nodes": nodes,
                "born": born_win,
                "died": died_win,
            }
            for e in alives:
                alive_per_win[e["window"]].add(lid)

        survivors = [lid for lid in label_info
                     if label_info[lid]["died"] > max_win]

        # ── 1. Displacement direction ──
        for lid, info in label_info.items():
            if info["died"] > max_win:
                continue
            died_win = info["died"]
            dead_phase = info["phase_sig"]
            dead_size = info["nodes"]

            # Find nearest alive label at death window
            best_dist = 999
            best_size = 0
            for other_lid in alive_per_win.get(died_win, set()):
                if other_lid == lid:
                    continue
                oi = label_info.get(other_lid)
                if oi is None:
                    continue
                pdist = abs(dead_phase - oi["phase_sig"])
                if pdist > math.pi:
                    pdist = 2 * math.pi - pdist
                if pdist < best_dist:
                    best_dist = pdist
                    best_size = oi["nodes"]

            if best_dist < 0.1:
                all_disp_size.append((dead_size, best_size))

        # ── 2. Long co-existence pairs ──
        if len(survivors) >= 2:
            surv_list = sorted(survivors)
            for i in range(min(len(surv_list), 100)):
                for j in range(i+1, min(len(surv_list), 100)):
                    a, b = surv_list[i], surv_list[j]
                    ia, ib = label_info[a], label_info[b]
                    overlap = min(ia["died"], ib["died"]) - max(ia["born"], ib["born"])
                    if overlap > 80:
                        pdist = abs(ia["phase_sig"] - ib["phase_sig"])
                        if pdist > math.pi:
                            pdist = 2 * math.pi - pdist
                        all_long_pairs.append({
                            "overlap": overlap,
                            "phase_dist": pdist,
                            "nodes_a": ia["nodes"],
                            "nodes_b": ib["nodes"],
                        })

        # ── 3. Stable trios and quads ──
        # Find groups of 3/4 labels that coexist for > 50 windows
        if len(survivors) >= 3 and len(survivors) <= 150:
            surv_list = sorted(survivors)
            # Phase-sort for neighbor detection
            surv_by_phase = sorted(surv_list,
                key=lambda x: label_info[x]["phase_sig"])

            # Find phase-neighbors (within 0.2 rad)
            def phase_near(a, b):
                d = abs(label_info[a]["phase_sig"] - label_info[b]["phase_sig"])
                if d > math.pi:
                    d = 2 * math.pi - d
                return d < 0.2

            # Check all triplets of phase-neighbors
            n_surv = len(surv_by_phase)
            trio_count = 0
            quad_count = 0

            for i in range(min(n_surv, 80)):
                a = surv_by_phase[i]
                ia = label_info[a]
                for j in range(i+1, min(n_surv, 80)):
                    b = surv_by_phase[j]
                    if not phase_near(a, b):
                        continue
                    ib = label_info[b]
                    overlap_ab = min(ia["died"], ib["died"]) - max(ia["born"], ib["born"])
                    if overlap_ab < 50:
                        continue

                    for k in range(j+1, min(n_surv, 80)):
                        c = surv_by_phase[k]
                        if not phase_near(a, c) and not phase_near(b, c):
                            continue
                        ic = label_info[c]
                        overlap_ac = min(ia["died"], ic["died"]) - max(ia["born"], ic["born"])
                        overlap_bc = min(ib["died"], ic["died"]) - max(ib["born"], ic["born"])
                        min_overlap = min(overlap_ab, overlap_ac, overlap_bc)
                        if min_overlap >= 50:
                            trio_count += 1
                            all_stable_trios.append({
                                "min_overlap": min_overlap,
                                "sizes": sorted([ia["nodes"], ib["nodes"], ic["nodes"]]),
                                "seed": seed,
                            })

                            # Check for quad extension
                            for m in range(k+1, min(n_surv, 80)):
                                e_lid = surv_by_phase[m]
                                if not (phase_near(a, e_lid) or phase_near(b, e_lid) or phase_near(c, e_lid)):
                                    continue
                                ie = label_info[e_lid]
                                ov_ae = min(ia["died"], ie["died"]) - max(ia["born"], ie["born"])
                                ov_be = min(ib["died"], ie["died"]) - max(ib["born"], ie["born"])
                                ov_ce = min(ic["died"], ie["died"]) - max(ic["born"], ie["born"])
                                if min(ov_ae, ov_be, ov_ce) >= 50:
                                    quad_count += 1
                                    all_stable_quads.append({
                                        "min_overlap": min(min_overlap, ov_ae, ov_be, ov_ce),
                                        "sizes": sorted([ia["nodes"], ib["nodes"], ic["nodes"], ie["nodes"]]),
                                    })

        if (seed_id + 1) % 10 == 0:
            print(f"  ... processed {seed_id+1}/{len(seeds)} seeds", flush=True)

    # ═══════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════

    # ── 1. Displacement direction ──
    print(f"\n{'='*72}")
    print(f"1. DISPLACEMENT DIRECTION (who kills whom)")
    print(f"{'='*72}\n")

    if all_disp_size:
        # dead_size → killer_size
        disp_matrix = defaultdict(lambda: defaultdict(int))
        for dead_s, killer_s in all_disp_size:
            disp_matrix[dead_s][killer_s] += 1

        sizes = sorted(set(s for s, _ in all_disp_size) | set(s for _, s in all_disp_size))
        sizes = [s for s in sizes if s <= 7]

        print(f"  Rows = dead, Cols = nearest alive (killer)")
        print(f"  {'dead':>6}", end="")
        for ks in sizes:
            print(f"  k={ks:>2}", end="")
        print(f"  {'total':>7}")
        print(f"  {'-'*(8 + 7*len(sizes) + 7)}")

        for ds in sizes:
            total = sum(disp_matrix[ds].values())
            print(f"  {ds:>6}", end="")
            for ks in sizes:
                c = disp_matrix[ds].get(ks, 0)
                pct = c / max(1, total) * 100
                print(f"  {pct:>5.0f}%", end="")
            print(f"  {total:>7}")

        # Summary: who is displaced by whom most?
        print(f"\n  Key patterns:")
        for ds in [2, 3, 4, 5]:
            if ds in disp_matrix:
                top_killer = max(disp_matrix[ds].items(), key=lambda x: x[1])
                total = sum(disp_matrix[ds].values())
                print(f"    {ds}-node killed most by: {top_killer[0]}-node "
                      f"({top_killer[1]/total*100:.0f}%)")

    # ── 2. Long co-existence pairs ──
    print(f"\n{'='*72}")
    print(f"2. LONG CO-EXISTENCE PAIRS (overlap > 80 windows)")
    print(f"{'='*72}\n")

    if all_long_pairs:
        print(f"  Total long pairs: {len(all_long_pairs)}")
        dists = [p["phase_dist"] for p in all_long_pairs]
        print(f"  Phase distance: mean={np.mean(dists):.4f} std={np.std(dists):.4f}")

        close = sum(1 for d in dists if d < 0.1)
        mid = sum(1 for d in dists if 0.1 <= d < 0.3)
        far = sum(1 for d in dists if d >= 0.3)
        print(f"  Distribution: close(<0.1)={close} mid(0.1-0.3)={mid} far(>0.3)={far}")

        # Size combinations
        size_combos = Counter()
        for p in all_long_pairs:
            combo = tuple(sorted([p["nodes_a"], p["nodes_b"]]))
            size_combos[combo] += 1

        print(f"\n  Size combinations (top 10):")
        for combo, count in size_combos.most_common(10):
            print(f"    {combo[0]}-{combo[1]}: {count}")

    # ── 3. Stable trios ──
    print(f"\n{'='*72}")
    print(f"3. STABLE TRIOS (3 labels, mutual overlap > 50 windows, phase < 0.2)")
    print(f"{'='*72}\n")

    print(f"  Total stable trios: {len(all_stable_trios)}")
    if all_stable_trios:
        overlaps = [t["min_overlap"] for t in all_stable_trios]
        print(f"  Min overlap: mean={np.mean(overlaps):.1f} max={max(overlaps)}")

        trio_sizes = Counter()
        for t in all_stable_trios:
            trio_sizes[tuple(t["sizes"])] += 1
        print(f"\n  Size compositions (top 10):")
        for sizes, count in trio_sizes.most_common(10):
            print(f"    {sizes}: {count}")

        seeds_with_trios = len(set(t["seed"] for t in all_stable_trios))
        print(f"\n  Seeds with trios: {seeds_with_trios}/{len(seeds)}")

    # ── 4. Stable quads ──
    print(f"\n{'='*72}")
    print(f"4. STABLE QUADS (4 labels, mutual overlap > 50 windows)")
    print(f"{'='*72}\n")

    print(f"  Total stable quads: {len(all_stable_quads)}")
    if all_stable_quads:
        overlaps = [q["min_overlap"] for q in all_stable_quads]
        print(f"  Min overlap: mean={np.mean(overlaps):.1f} max={max(overlaps)}")

        quad_sizes = Counter()
        for q in all_stable_quads:
            quad_sizes[tuple(q["sizes"])] += 1
        print(f"\n  Size compositions (top 10):")
        for sizes, count in quad_sizes.most_common(10):
            print(f"    {sizes}: {count}")

    # ── 5. Size role differentiation ──
    print(f"\n{'='*72}")
    print(f"5. SIZE ROLE IN RELATIONS")
    print(f"{'='*72}\n")

    if all_disp_size:
        # For each size: how often does it displace vs get displaced?
        displaced_by = defaultdict(int)  # size → times displaced
        displaces = defaultdict(int)     # size → times it displaces others

        for dead_s, killer_s in all_disp_size:
            displaced_by[dead_s] += 1
            displaces[killer_s] += 1

        all_sizes = sorted(set(displaced_by.keys()) | set(displaces.keys()))
        print(f"  {'size':>5} {'displaced':>10} {'displaces':>10} {'ratio':>8} {'role':>12}")
        print(f"  {'-'*50}")
        for s in all_sizes:
            if s > 9:
                continue
            db = displaced_by.get(s, 0)
            dp = displaces.get(s, 0)
            ratio = dp / max(1, db)
            role = "predator" if ratio > 2 else "prey" if ratio < 0.5 else "neutral"
            print(f"  {s:>5} {db:>10} {dp:>10} {ratio:>7.2f}× {role:>12}")

    # ── 6. Summary ──
    print(f"\n{'='*72}")
    print(f"SUMMARY")
    print(f"{'='*72}")

    print(f"\n  Displacement: {'directional' if all_disp_size else 'no data'}")
    if all_disp_size:
        # Is displacement size-dependent?
        big_kills_small = sum(1 for ds, ks in all_disp_size if ks > ds)
        small_kills_big = sum(1 for ds, ks in all_disp_size if ks < ds)
        same_kills_same = sum(1 for ds, ks in all_disp_size if ks == ds)
        total = len(all_disp_size)
        print(f"    bigger kills smaller: {big_kills_small/total*100:.1f}%")
        print(f"    smaller kills bigger: {small_kills_big/total*100:.1f}%")
        print(f"    same size: {same_kills_same/total*100:.1f}%")

    print(f"\n  Stable groups:")
    print(f"    Trios: {len(all_stable_trios)}")
    print(f"    Quads: {len(all_stable_quads)}")
    if all_stable_trios:
        print(f"    → Upper structure candidates exist")
    else:
        print(f"    → No stable multi-label groups found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
