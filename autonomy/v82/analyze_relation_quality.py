#!/usr/bin/env python3
"""
ESDE v8.2 — Relation Quality Analysis
========================================
GPT audit §6: Dig into the "quality" of relations.

1. Trio/quad persistence and dissolution patterns
2. Role differentiation within trio/quad
3. Displacement directionality over time
4. Relation cluster phase-space spread
5. Relation unit's physical layer influence (territory, R+)
6. 5-node vs 6+ node role in relations

Usage:
  python analyze_relation_quality.py --dir diag_v82_baseline
"""

import json, glob, argparse, numpy as np, math
from collections import defaultdict, Counter
from pathlib import Path


def phase_dist(a, b):
    d = abs(a - b)
    if d > math.pi:
        d = 2 * math.pi - d
    return d


def main(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data

    print(f"{'='*72}")
    print(f"RELATION QUALITY ANALYSIS")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'='*72}")

    # ═══════════════════════════════════════════
    # PER-SEED ANALYSIS
    # ═══════════════════════════════════════════

    all_trio_lifespans = []
    all_trio_dissolution = []  # how trios end
    all_trio_roles = []        # center vs edge
    all_trio_territory = []    # territory stats per trio
    all_trio_spread = []       # phase-space spread of trio
    all_temporal_disp = []     # displacement over time windows
    all_sixplus_roles = []     # 6+ in relations

    for seed_id, (seed, data) in enumerate(sorted(seeds.items())):
        log = data["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)

        max_win = max(e["window"] for e in log)

        # Build label info with per-window share
        label_info = {}
        label_share_at = defaultdict(dict)  # lid → {win: share}
        label_territory_at = defaultdict(dict)  # lid → {win: territory}

        for lid, entries in traj.items():
            births = [e for e in entries if e["event"] == "birth"]
            deaths = [e for e in entries if e["event"] == "death"]
            alives = [e for e in entries if e["event"] in ("birth", "alive")]
            if not births:
                continue

            born_win = births[0]["window"]
            died_win = deaths[0]["window"] if deaths else max_win + 1

            label_info[lid] = {
                "phase_sig": births[0].get("phase_sig", 0),
                "nodes": births[0]["nodes"],
                "born": born_win,
                "died": died_win,
            }
            for e in alives:
                label_share_at[lid][e["window"]] = e["share"]
                label_territory_at[lid][e["window"]] = e.get("territory_links", 0)

        survivors = [lid for lid in label_info
                     if label_info[lid]["died"] > max_win]

        if len(survivors) < 3:
            continue

        # Sort survivors by phase
        surv_by_phase = sorted(survivors,
            key=lambda x: label_info[x]["phase_sig"])

        # ── 1. Find trios and analyze internals ──
        n_surv = len(surv_by_phase)
        seed_trios = []

        for i in range(min(n_surv, 80)):
            a = surv_by_phase[i]
            ia = label_info[a]
            for j in range(i+1, min(n_surv, 80)):
                b = surv_by_phase[j]
                if phase_dist(ia["phase_sig"], label_info[b]["phase_sig"]) > 0.2:
                    continue
                ib = label_info[b]
                overlap_ab = min(ia["died"], ib["died"]) - max(ia["born"], ib["born"])
                if overlap_ab < 50:
                    continue

                for k in range(j+1, min(n_surv, 80)):
                    c = surv_by_phase[k]
                    ic = label_info[c]
                    d_ac = phase_dist(ia["phase_sig"], ic["phase_sig"])
                    d_bc = phase_dist(ib["phase_sig"], ic["phase_sig"])
                    if d_ac > 0.2 and d_bc > 0.2:
                        continue

                    overlap_ac = min(ia["died"], ic["died"]) - max(ia["born"], ic["born"])
                    overlap_bc = min(ib["died"], ic["died"]) - max(ib["born"], ic["born"])
                    min_overlap = min(overlap_ab, overlap_ac, overlap_bc)

                    if min_overlap >= 50:
                        trio = (a, b, c)
                        trio_start = max(ia["born"], ib["born"], ic["born"])
                        trio_end = min(ia["died"], ib["died"], ic["died"])

                        # Phase spread
                        phases = [ia["phase_sig"], ib["phase_sig"], ic["phase_sig"]]
                        dists = [phase_dist(phases[x], phases[y])
                                 for x in range(3) for y in range(x+1, 3)]
                        spread = max(dists)

                        # Who is center? (most phase-central)
                        centrality = []
                        for idx, lid in enumerate(trio):
                            mean_dist = np.mean([phase_dist(
                                label_info[lid]["phase_sig"],
                                label_info[other]["phase_sig"])
                                for other in trio if other != lid])
                            centrality.append((lid, mean_dist))
                        centrality.sort(key=lambda x: x[1])
                        center = centrality[0][0]
                        edges = [centrality[1][0], centrality[2][0]]

                        # Territory comparison (at midpoint of overlap)
                        mid_win = (trio_start + trio_end) // 2
                        terr = {}
                        share = {}
                        for lid in trio:
                            terr[lid] = label_territory_at[lid].get(mid_win, 0)
                            share[lid] = label_share_at[lid].get(mid_win, 0)

                        seed_trios.append({
                            "members": trio,
                            "sizes": sorted([ia["nodes"], ib["nodes"], ic["nodes"]]),
                            "start": trio_start,
                            "end": trio_end,
                            "lifespan": trio_end - trio_start,
                            "spread": spread,
                            "center": label_info[center]["nodes"],
                            "center_share": share.get(center, 0),
                            "center_terr": terr.get(center, 0),
                            "edge_shares": [share.get(e, 0) for e in edges],
                            "edge_terrs": [terr.get(e, 0) for e in edges],
                            "all_survived": all(label_info[lid]["died"] > max_win for lid in trio),
                        })

        # Aggregate trio stats
        for t in seed_trios[:50]:  # cap per seed
            all_trio_lifespans.append(t["lifespan"])
            all_trio_spread.append(t["spread"])
            all_trio_roles.append({
                "center_size": t["center"],
                "center_share": t["center_share"],
                "center_terr": t["center_terr"],
                "edge_share_mean": np.mean(t["edge_shares"]) if t["edge_shares"] else 0,
                "edge_terr_mean": np.mean(t["edge_terrs"]) if t["edge_terrs"] else 0,
            })
            all_trio_territory.append({
                "center_terr": t["center_terr"],
                "edge_terr_mean": np.mean(t["edge_terrs"]) if t["edge_terrs"] else 0,
                "total_terr": t["center_terr"] + sum(t["edge_terrs"]),
            })

            # Dissolution: did the trio survive intact?
            if t["all_survived"]:
                all_trio_dissolution.append("intact")
            else:
                all_trio_dissolution.append("partial_loss")

        # ── 2. Temporal displacement ──
        # Split time into quarters, count displacement by size
        quarter_size = max_win // 4
        for q in range(4):
            q_start = q * quarter_size
            q_end = (q + 1) * quarter_size
            q_disps = defaultdict(int)

            for lid, info in label_info.items():
                if info["died"] > max_win or info["died"] < q_start or info["died"] >= q_end:
                    continue
                dead_phase = info["phase_sig"]
                dead_size = info["nodes"]

                # Find nearest alive at death
                for other_lid in label_info:
                    if other_lid == lid:
                        continue
                    oi = label_info[other_lid]
                    if oi["born"] > info["died"] or oi["died"] < info["died"]:
                        continue
                    if phase_dist(dead_phase, oi["phase_sig"]) < 0.1:
                        q_disps[(dead_size, oi["nodes"])] += 1
                        break

            all_temporal_disp.append({"quarter": q, "disps": dict(q_disps)})

        # ── 3. 6+ node in relations ──
        sixplus = [lid for lid in survivors if label_info[lid]["nodes"] >= 6]
        for lid in sixplus:
            info = label_info[lid]
            # Count how many other survivors are within 0.2 rad
            neighbors = [other for other in survivors if other != lid
                        and phase_dist(info["phase_sig"],
                                       label_info[other]["phase_sig"]) < 0.2]
            neighbor_sizes = [label_info[n]["nodes"] for n in neighbors]

            mid_win = (info["born"] + min(info["died"], max_win)) // 2
            terr = label_territory_at[lid].get(mid_win, 0)
            share_val = label_share_at[lid].get(mid_win, 0)

            all_sixplus_roles.append({
                "nodes": info["nodes"],
                "n_neighbors": len(neighbors),
                "neighbor_sizes": neighbor_sizes,
                "territory": terr,
                "share": share_val,
                "age": min(info["died"], max_win) - info["born"],
            })

        if (seed_id + 1) % 10 == 0:
            print(f"  ... processed {seed_id+1}/{len(seeds)} seeds", flush=True)

    # ═══════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════

    # ── 1. Trio persistence ──
    print(f"\n{'='*72}")
    print(f"1. TRIO PERSISTENCE AND DISSOLUTION")
    print(f"{'='*72}\n")

    if all_trio_lifespans:
        print(f"  Trios analyzed: {len(all_trio_lifespans)}")
        print(f"  Lifespan: mean={np.mean(all_trio_lifespans):.1f} "
              f"median={np.median(all_trio_lifespans):.0f} "
              f"max={max(all_trio_lifespans)}")

        intact = sum(1 for d in all_trio_dissolution if d == "intact")
        partial = sum(1 for d in all_trio_dissolution if d == "partial_loss")
        total = len(all_trio_dissolution)
        print(f"  Intact at w200: {intact}/{total} ({intact/max(1,total)*100:.1f}%)")
        print(f"  Partial loss:   {partial}/{total} ({partial/max(1,total)*100:.1f}%)")

    # ── 2. Role differentiation within trios ──
    print(f"\n{'='*72}")
    print(f"2. ROLE DIFFERENTIATION WITHIN TRIOS")
    print(f"{'='*72}\n")

    if all_trio_roles:
        center_sizes = Counter(r["center_size"] for r in all_trio_roles)
        print(f"  Center node size distribution:")
        for size, count in center_sizes.most_common():
            print(f"    {size}-node: {count} ({count/len(all_trio_roles)*100:.1f}%)")

        center_shares = [r["center_share"] for r in all_trio_roles if r["center_share"] > 0]
        edge_shares = [r["edge_share_mean"] for r in all_trio_roles if r["edge_share_mean"] > 0]
        if center_shares and edge_shares:
            print(f"\n  Center share: mean={np.mean(center_shares):.6f}")
            print(f"  Edge share:   mean={np.mean(edge_shares):.6f}")
            ratio = np.mean(center_shares) / max(np.mean(edge_shares), 0.00001)
            print(f"  Ratio: {ratio:.2f}×")

        center_terrs = [r["center_terr"] for r in all_trio_roles if r["center_terr"] > 0]
        edge_terrs = [r["edge_terr_mean"] for r in all_trio_roles if r["edge_terr_mean"] > 0]
        if center_terrs and edge_terrs:
            print(f"\n  Center territory: mean={np.mean(center_terrs):.1f}")
            print(f"  Edge territory:   mean={np.mean(edge_terrs):.1f}")
            ratio = np.mean(center_terrs) / max(np.mean(edge_terrs), 0.1)
            print(f"  Ratio: {ratio:.2f}×")

    # ── 3. Phase-space spread ──
    print(f"\n{'='*72}")
    print(f"3. TRIO PHASE-SPACE SPREAD")
    print(f"{'='*72}\n")

    if all_trio_spread:
        print(f"  Max internal distance:")
        print(f"    mean={np.mean(all_trio_spread):.4f}")
        print(f"    std={np.std(all_trio_spread):.4f}")
        print(f"    max={max(all_trio_spread):.4f}")

        tight = sum(1 for s in all_trio_spread if s < 0.05)
        medium = sum(1 for s in all_trio_spread if 0.05 <= s < 0.1)
        wide = sum(1 for s in all_trio_spread if s >= 0.1)
        total = len(all_trio_spread)
        print(f"  Tight (<0.05): {tight} ({tight/total*100:.0f}%)")
        print(f"  Medium (0.05-0.1): {medium} ({medium/total*100:.0f}%)")
        print(f"  Wide (>0.1): {wide} ({wide/total*100:.0f}%)")

    # ── 4. Territory of trios as units ──
    print(f"\n{'='*72}")
    print(f"4. TRIO TERRITORY (as a unit)")
    print(f"{'='*72}\n")

    if all_trio_territory:
        totals = [t["total_terr"] for t in all_trio_territory if t["total_terr"] > 0]
        centers = [t["center_terr"] for t in all_trio_territory if t["center_terr"] > 0]
        if totals:
            print(f"  Total territory (3 labels): mean={np.mean(totals):.1f}")
            print(f"  Center territory alone:     mean={np.mean(centers):.1f}")
            print(f"  Center fraction: {np.mean(centers)/np.mean(totals)*100:.0f}%")

    # ── 5. Temporal displacement patterns ──
    print(f"\n{'='*72}")
    print(f"5. DISPLACEMENT OVER TIME (quarters)")
    print(f"{'='*72}\n")

    quarter_totals = [defaultdict(int) for _ in range(4)]
    for td in all_temporal_disp:
        q = td["quarter"]
        for (ds, ks), count in td["disps"].items():
            quarter_totals[q][(ds, ks)] += count

    for q in range(4):
        total = sum(quarter_totals[q].values())
        big_kills_small = sum(v for (ds, ks), v in quarter_totals[q].items() if ks > ds)
        same = sum(v for (ds, ks), v in quarter_totals[q].items() if ks == ds)
        small_kills_big = sum(v for (ds, ks), v in quarter_totals[q].items() if ks < ds)
        if total > 0:
            print(f"  Q{q+1} (w{q*50}-{(q+1)*50}): "
                  f"total={total}  big>small={big_kills_small/total*100:.0f}%  "
                  f"same={same/total*100:.0f}%  small>big={small_kills_big/total*100:.0f}%")

    # ── 6. 6+ node roles ──
    print(f"\n{'='*72}")
    print(f"6. 6+ NODE ROLE IN RELATIONS")
    print(f"{'='*72}\n")

    if all_sixplus_roles:
        print(f"  Total 6+ survivors: {len(all_sixplus_roles)}")
        for r in all_sixplus_roles[:15]:
            ns = Counter(r["neighbor_sizes"])
            ns_str = ", ".join(f"{s}n×{c}" for s, c in sorted(ns.items()))
            print(f"    {r['nodes']}-node: neighbors={r['n_neighbors']} "
                  f"[{ns_str}] terr={r['territory']} share={r['share']:.4f} "
                  f"age={r['age']}")

        # Aggregate
        if len(all_sixplus_roles) >= 3:
            n_neigh = [r["n_neighbors"] for r in all_sixplus_roles]
            terrs = [r["territory"] for r in all_sixplus_roles]
            shares = [r["share"] for r in all_sixplus_roles]
            ages = [r["age"] for r in all_sixplus_roles]
            print(f"\n  Aggregate:")
            print(f"    neighbors: mean={np.mean(n_neigh):.1f}")
            print(f"    territory: mean={np.mean(terrs):.1f}")
            print(f"    share: mean={np.mean(shares):.4f}")
            print(f"    age: mean={np.mean(ages):.0f}")
    else:
        print(f"  No 6+ survivors found")

    # ── SUMMARY ──
    print(f"\n{'='*72}")
    print(f"SUMMARY")
    print(f"{'='*72}")

    print(f"\n  Trio persistence:")
    if all_trio_lifespans:
        print(f"    Mean lifespan: {np.mean(all_trio_lifespans):.0f} windows")
        intact_pct = sum(1 for d in all_trio_dissolution if d == "intact") / max(1, len(all_trio_dissolution)) * 100
        print(f"    Intact at end: {intact_pct:.0f}%")

    print(f"\n  Role differentiation:")
    if all_trio_roles:
        top_center = center_sizes.most_common(1)[0]
        print(f"    Most common center: {top_center[0]}-node ({top_center[1]/len(all_trio_roles)*100:.0f}%)")

    print(f"\n  Key question: Are trios 'upper subjects' or just proximity coincidence?")
    if all_trio_spread:
        mean_spread = np.mean(all_trio_spread)
        print(f"    Phase spread: {mean_spread:.4f} rad")
        if mean_spread < 0.1:
            print(f"    → Tight clustering. Could be proximity artifact")
            print(f"    → Need: do trios ACT differently from random label triples?")
        else:
            print(f"    → Wide spread. Less likely to be proximity artifact")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
