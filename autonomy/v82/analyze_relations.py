#!/usr/bin/env python3
"""
ESDE v8.2 — Label Relationship Analysis
==========================================
Observes relationships between fixed labels.
Does any pair behave as a unit? Competition? Co-occurrence?

Usage:
  python analyze_relations.py --dir diag_v82_baseline
"""

import json, glob, argparse, numpy as np
from collections import defaultdict
from pathlib import Path


def main(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data

    print(f"{'='*72}")
    print(f"LABEL RELATIONSHIP ANALYSIS")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'='*72}")

    # ── Per-seed analysis, then aggregate ──
    all_coexist = []       # co-existence durations
    all_competition = []   # competitive displacement events
    all_cooccur = []       # co-occurrence at birth
    all_phase_dist = []    # phase distance between coexisting pairs
    all_bridge = []        # R>0 bridges between territories
    seed_summaries = []

    for seed, data in sorted(seeds.items()):
        log = data["lifecycle_log"]

        # Build per-window snapshots: which labels are alive
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)

        # Get alive set per window
        max_win = max(e["window"] for e in log)
        alive_per_win = defaultdict(set)
        label_info = {}  # lid → {phase_sig, nodes, born, died_at}

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
                "lifespan": died_win - born_win,
            }

            for e in alives:
                alive_per_win[e["window"]].add(lid)

        # ── 1. Co-existence: how many windows do pairs overlap? ──
        label_ids = sorted(label_info.keys())
        survivors = [lid for lid in label_ids
                     if label_info[lid]["died"] > max_win]

        # Sample: only survivor pairs (too many total pairs)
        if len(survivors) > 2:
            pair_overlap = {}
            for i in range(len(survivors)):
                for j in range(i+1, len(survivors)):
                    a, b = survivors[i], survivors[j]
                    info_a = label_info[a]
                    info_b = label_info[b]
                    overlap_start = max(info_a["born"], info_b["born"])
                    overlap_end = min(info_a["died"], info_b["died"])
                    overlap = max(0, overlap_end - overlap_start)

                    # Phase distance
                    da = info_a["phase_sig"]
                    db = info_b["phase_sig"]
                    pdist = abs(da - db)
                    if pdist > 3.14159:
                        pdist = 6.28318 - pdist

                    pair_overlap[(a,b)] = {
                        "overlap": overlap,
                        "phase_dist": pdist,
                        "nodes_a": info_a["nodes"],
                        "nodes_b": info_b["nodes"],
                    }

            overlaps = [p["overlap"] for p in pair_overlap.values()]
            pdists = [p["phase_dist"] for p in pair_overlap.values()]
            all_coexist.extend(overlaps)
            all_phase_dist.extend(pdists)

        # ── 2. Birth co-occurrence: labels born in same window ──
        birth_wins = defaultdict(list)
        for lid, info in label_info.items():
            birth_wins[info["born"]].append(lid)

        coborn_count = 0
        coborn_surv_both = 0
        coborn_surv_one = 0
        coborn_surv_none = 0

        for win, lids in birth_wins.items():
            if len(lids) < 2:
                continue
            for i in range(len(lids)):
                for j in range(i+1, len(lids)):
                    a, b = lids[i], lids[j]
                    sa = label_info[a]["died"] > max_win
                    sb = label_info[b]["died"] > max_win
                    coborn_count += 1
                    if sa and sb:
                        coborn_surv_both += 1
                    elif sa or sb:
                        coborn_surv_one += 1
                    else:
                        coborn_surv_none += 1

        all_cooccur.append({
            "total": coborn_count,
            "both_surv": coborn_surv_both,
            "one_surv": coborn_surv_one,
            "none_surv": coborn_surv_none,
        })

        # ── 3. Competitive displacement: one dies, neighbor gains ──
        displacements = 0
        for lid, info in label_info.items():
            if info["died"] > max_win:
                continue  # survivor, skip
            died_win = info["died"]
            dead_phase = info["phase_sig"]

            # Check if a nearby label gained share when this one died
            for other_lid in alive_per_win.get(died_win, set()):
                if other_lid == lid:
                    continue
                other_info = label_info.get(other_lid)
                if other_info is None:
                    continue
                pdist = abs(dead_phase - other_info["phase_sig"])
                if pdist > 3.14159:
                    pdist = 6.28318 - pdist
                if pdist < 0.1:  # phase-near
                    displacements += 1
                    break

        all_competition.append(displacements)

        # ── 4. Cluster analysis: do survivors form groups? ──
        if len(survivors) > 3:
            surv_phases = [(lid, label_info[lid]["phase_sig"]) for lid in survivors]
            surv_phases.sort(key=lambda x: x[1])

            # Find gaps in phase space
            gaps = []
            for i in range(len(surv_phases)):
                j = (i + 1) % len(surv_phases)
                d = surv_phases[j][1] - surv_phases[i][1]
                if j == 0:
                    d += 6.28318
                gaps.append(d)

            mean_gap = np.mean(gaps)
            max_gap = max(gaps)
            min_gap = min(gaps)

            seed_summaries.append({
                "seed": seed,
                "n_survivors": len(survivors),
                "mean_gap": mean_gap,
                "max_gap": max_gap,
                "min_gap": min_gap,
                "gap_ratio": max_gap / max(min_gap, 0.001),
                "displacements": displacements,
            })

    # ════════════════════════════════════════════
    # AGGREGATE RESULTS
    # ════════════════════════════════════════════

    # ── 1. Co-existence ──
    print(f"\n{'='*72}")
    print(f"1. CO-EXISTENCE (survivor pairs)")
    print(f"{'='*72}\n")

    if all_coexist:
        print(f"  Pairs analyzed: {len(all_coexist)}")
        print(f"  Overlap (windows): mean={np.mean(all_coexist):.1f} "
              f"median={np.median(all_coexist):.0f} "
              f"std={np.std(all_coexist):.1f}")
        print(f"  Phase distance: mean={np.mean(all_phase_dist):.4f} "
              f"std={np.std(all_phase_dist):.4f}")

        # Overlap vs phase distance correlation
        if len(all_coexist) > 10:
            corr = np.corrcoef(all_coexist, all_phase_dist)[0,1]
            print(f"  corr(overlap, phase_dist) = {corr:.3f}")

        # Phase distance distribution
        close = sum(1 for d in all_phase_dist if d < 0.1)
        mid = sum(1 for d in all_phase_dist if 0.1 <= d < 0.5)
        far = sum(1 for d in all_phase_dist if d >= 0.5)
        print(f"  Phase distance: close(<0.1)={close} mid(0.1-0.5)={mid} far(>0.5)={far}")

    # ── 2. Birth co-occurrence ──
    print(f"\n{'='*72}")
    print(f"2. BIRTH CO-OCCURRENCE")
    print(f"{'='*72}\n")

    if all_cooccur:
        total = sum(c["total"] for c in all_cooccur)
        both = sum(c["both_surv"] for c in all_cooccur)
        one = sum(c["one_surv"] for c in all_cooccur)
        none_ = sum(c["none_surv"] for c in all_cooccur)
        print(f"  Co-born pairs: {total}")
        print(f"  Both survive: {both} ({both/max(1,total)*100:.1f}%)")
        print(f"  One survives: {one} ({one/max(1,total)*100:.1f}%)")
        print(f"  None survive: {none_} ({none_/max(1,total)*100:.1f}%)")

        if total > 0:
            # Expected: if independent, P(both) = P(surv)^2
            p_surv = (both*2 + one) / max(1, total * 2)
            p_both_independent = p_surv * p_surv
            p_both_observed = both / max(1, total)
            print(f"\n  P(survive) ≈ {p_surv:.3f}")
            print(f"  P(both survive | independent) = {p_both_independent:.4f}")
            print(f"  P(both survive | observed)    = {p_both_observed:.4f}")
            ratio = p_both_observed / max(p_both_independent, 0.0001)
            print(f"  Ratio: {ratio:.2f}×")
            if ratio > 1.5:
                print(f"  → Co-born labels survive TOGETHER more than expected")
            elif ratio < 0.5:
                print(f"  → Co-born labels COMPETE (one kills the other)")
            else:
                print(f"  → Roughly independent")

    # ── 3. Competitive displacement ──
    print(f"\n{'='*72}")
    print(f"3. COMPETITIVE DISPLACEMENT")
    print(f"{'='*72}\n")

    if all_competition:
        print(f"  Displacement events/seed: mean={np.mean(all_competition):.1f} "
              f"std={np.std(all_competition):.1f}")
        total_deaths = sum(1 for s in seeds.values()
                          for e in s["lifecycle_log"]
                          if e["event"] == "death")
        total_disp = sum(all_competition)
        print(f"  Total deaths: {total_deaths}")
        print(f"  Deaths near another label: {total_disp} "
              f"({total_disp/max(1,total_deaths)*100:.1f}%)")

    # ── 4. Spatial clustering of survivors ──
    print(f"\n{'='*72}")
    print(f"4. SURVIVOR SPATIAL DISTRIBUTION")
    print(f"{'='*72}\n")

    if seed_summaries:
        mean_gaps = [s["mean_gap"] for s in seed_summaries]
        max_gaps = [s["max_gap"] for s in seed_summaries]
        min_gaps = [s["min_gap"] for s in seed_summaries]
        gap_ratios = [s["gap_ratio"] for s in seed_summaries]
        n_survs = [s["n_survivors"] for s in seed_summaries]

        print(f"  Survivors/seed: mean={np.mean(n_survs):.1f}")
        print(f"  Mean gap (phase): {np.mean(mean_gaps):.4f}")
        print(f"  Max gap: mean={np.mean(max_gaps):.4f}")
        print(f"  Min gap: mean={np.mean(min_gaps):.4f}")
        print(f"  Gap ratio (max/min): mean={np.mean(gap_ratios):.1f}")
        print(f"  → {'Clustered' if np.mean(gap_ratios) > 5 else 'Uniform'} "
              f"distribution")

    # ── 5. Size-pair analysis: do specific size combos coexist? ──
    print(f"\n{'='*72}")
    print(f"5. SIZE-PAIR CO-EXISTENCE")
    print(f"{'='*72}\n")

    size_pair_counts = defaultdict(int)
    size_pair_close = defaultdict(int)  # phase_dist < 0.2

    for seed, data in sorted(seeds.items()):
        log = data["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)

        max_win = max(e["window"] for e in log)
        survivors = []
        for lid, entries in traj.items():
            births = [e for e in entries if e["event"] == "birth"]
            deaths = [e for e in entries if e["event"] == "death"]
            if births and (not deaths or deaths[0]["window"] > max_win):
                survivors.append({
                    "lid": lid,
                    "nodes": births[0]["nodes"],
                    "phase_sig": births[0].get("phase_sig", 0),
                })

        for i in range(len(survivors)):
            for j in range(i+1, len(survivors)):
                a = survivors[i]
                b = survivors[j]
                na, nb = min(a["nodes"], b["nodes"]), max(a["nodes"], b["nodes"])
                size_pair_counts[(na, nb)] += 1

                pdist = abs(a["phase_sig"] - b["phase_sig"])
                if pdist > 3.14159:
                    pdist = 6.28318 - pdist
                if pdist < 0.2:
                    size_pair_close[(na, nb)] += 1

    print(f"  {'pair':>8} {'total':>8} {'close':>8} {'close%':>8}")
    print(f"  {'-'*36}")
    for pair in sorted(size_pair_counts.keys()):
        t = size_pair_counts[pair]
        c = size_pair_close.get(pair, 0)
        pct = c / max(1, t) * 100
        if t >= 10:
            print(f"  {f'{pair[0]}-{pair[1]}':>8} {t:>8} {c:>8} {pct:>7.1f}%")

    # ── 6. Summary ──
    print(f"\n{'='*72}")
    print(f"SUMMARY")
    print(f"{'='*72}")

    print(f"\n  Key questions:")
    print(f"  - Do labels co-exist as independent units or as groups?")
    if all_coexist:
        mean_ov = np.mean(all_coexist)
        print(f"    → Mean overlap: {mean_ov:.1f} windows "
              f"({'long co-existence' if mean_ov > 50 else 'short'})")
    if all_cooccur:
        ratio_val = p_both_observed / max(p_both_independent, 0.0001)
        print(f"    → Co-born survival ratio: {ratio_val:.2f}× "
              f"({'correlated' if ratio_val > 1.5 else 'independent' if ratio_val > 0.5 else 'competitive'})")
    print(f"  - Is there competitive displacement?")
    if all_competition:
        disp_pct = total_disp / max(1, total_deaths) * 100
        print(f"    → {disp_pct:.1f}% of deaths near another label")
    print(f"  - Are survivors clustered or uniform in phase space?")
    if seed_summaries:
        print(f"    → Gap ratio: {np.mean(gap_ratios):.1f}× "
              f"({'clustered' if np.mean(gap_ratios) > 5 else 'uniform'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
