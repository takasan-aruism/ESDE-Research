#!/usr/bin/env python3
"""
ESDE v8.2 — Trio Genesis & Dynamics Analysis
================================================
GPT 5 questions + old-Claude insights:

Q1. How do trios form? (formation conditions)
Q2. How do trios die? (stress signals at w200)
Q3. Do trios compete with each other? (inter-trio displacement)
Q4. What mechanism causes birth suppression near trios?
    - Old Claude: combined share budget pressure?
    - Old Claude: vacancy vs "far from trio" distinction
Q5. Does role differentiation emerge over time? (early vs late)

Bonus: Is trio an artifact of maturation α? (α-sensitivity proxy)

Usage:
  python analyze_trio_genesis.py --dir diag_v82_baseline
"""

import json, glob, argparse, numpy as np, math
from collections import defaultdict, Counter
from pathlib import Path


def phase_dist(a, b):
    d = abs(a - b)
    if d > math.pi:
        d = 2 * math.pi - d
    return d


def circular_mean(phases):
    sx = sum(math.cos(p) for p in phases) / len(phases)
    sy = sum(math.sin(p) for p in phases) / len(phases)
    return math.atan2(sy, sx) % (2 * math.pi)


def build_seed_data(data):
    """Build label trajectories from lifecycle_log."""
    log = data["lifecycle_log"]
    traj = defaultdict(list)
    for e in log:
        traj[e["label_id"]].append(e)

    max_win = max(e["window"] for e in log)

    label_info = {}
    alive_per_win = defaultdict(set)
    share_at = defaultdict(dict)
    territory_at = defaultdict(dict)
    rplus_at = defaultdict(dict)
    bin_occ_at = defaultdict(dict)
    bin_vac_at = defaultdict(dict)
    n_neighbors_at = defaultdict(dict)

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
            w = e["window"]
            alive_per_win[w].add(lid)
            share_at[lid][w] = e["share"]
            territory_at[lid][w] = e.get("territory_links", 0)
            rplus_at[lid][w] = e.get("territory_rplus", 0)
            bin_occ_at[lid][w] = e.get("bin_occupancy", 0)
            bin_vac_at[lid][w] = e.get("bin_vacancy", 0)
            n_neighbors_at[lid][w] = e.get("n_phase_neighbors", 0)

    survivors = {lid for lid in label_info if label_info[lid]["died"] > max_win}

    return {
        "label_info": label_info, "alive_per_win": alive_per_win,
        "share_at": share_at, "territory_at": territory_at,
        "rplus_at": rplus_at, "bin_occ_at": bin_occ_at,
        "bin_vac_at": bin_vac_at, "n_neighbors_at": n_neighbors_at,
        "survivors": survivors, "max_win": max_win, "traj": traj,
    }


def find_trios(survivors, label_info, threshold=0.2):
    """Find trios: 3 survivors with all pairwise phase_dist < threshold,
    co-existing >= 50 windows."""
    trios = []
    surv_list = sorted(survivors, key=lambda x: label_info[x]["phase_sig"])
    n = len(surv_list)
    for i in range(n):
        a = surv_list[i]
        pa = label_info[a]["phase_sig"]
        for j in range(i + 1, n):
            b = surv_list[j]
            pb = label_info[b]["phase_sig"]
            if phase_dist(pa, pb) > threshold:
                continue
            ba = label_info[a]["born"]
            bb = label_info[b]["born"]
            da = label_info[a]["died"]
            db = label_info[b]["died"]
            if min(da, db) - max(ba, bb) < 50:
                continue
            for k in range(j + 1, n):
                c = surv_list[k]
                pc = label_info[c]["phase_sig"]
                if phase_dist(pa, pc) > threshold:
                    continue
                if phase_dist(pb, pc) > threshold:
                    continue
                bc = label_info[c]["born"]
                dc = label_info[c]["died"]
                ov = min(da, db, dc) - max(ba, bb, bc)
                if ov >= 50:
                    trios.append((a, b, c))
    return trios


def main(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data

    print(f"{'=' * 72}")
    print(f"TRIO GENESIS & DYNAMICS (GPT 5 questions)")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'=' * 72}")

    # ═══════════════════════════════════════════════════════════
    # ACCUMULATORS
    # ═══════════════════════════════════════════════════════════

    # Q1: formation conditions
    formation_windows = []          # when trio completes
    formation_vacancy = []          # vacancy at formation
    formation_occupancy = []        # occupancy at formation
    formation_member_ages = []      # ages of members at formation
    formation_member_sizes = []     # node counts at formation

    # Q2: stress signals at end (last 20 windows)
    end_share_trends = []           # per-trio: share slope in last 20 win
    end_territory_trends = []       # per-trio: territory slope
    end_min_shares = []             # minimum share among trio members at w200

    # Q3: trio-trio competition
    trio_pair_distances = []        # phase distance between trio centroids
    close_trio_pair_events = []     # displacement near close trio pairs

    # Q4: birth suppression mechanism
    #   Old Claude: is it combined share pressure?
    region_share_vs_birth_survival = []  # (combined_share, birth_survived)
    #   Old Claude: vacancy vs far-from-trio distinction
    vacancy_categories = []  # (vacancy_val, near_trio, survived)

    # Q5: role differentiation over time
    early_center_share = []         # center share at formation+10
    late_center_share = []          # center share at w150+
    early_edge_share = []
    late_edge_share = []
    early_center_terr = []
    late_center_terr = []
    early_edge_terr = []
    late_edge_terr = []

    # Bonus: α-sensitivity proxy
    # If trio is α artifact, young trios should be less stable
    trio_age_vs_share_stability = []

    for seed_idx, (seed, data) in enumerate(sorted(seeds.items())):
        sd = build_seed_data(data)
        li = sd["label_info"]
        survivors = sd["survivors"]
        share_at = sd["share_at"]
        territory_at = sd["territory_at"]
        bin_occ_at = sd["bin_occ_at"]
        bin_vac_at = sd["bin_vac_at"]
        alive_pw = sd["alive_per_win"]
        max_win = sd["max_win"]

        if len(survivors) < 3:
            continue

        trios = find_trios(survivors, li)
        if not trios:
            continue

        # Build trio member set and centroid map
        trio_member_ids = set()
        trio_centroids = []  # (centroid_phase, trio_tuple)
        for trio in trios:
            phases = [li[m]["phase_sig"] for m in trio]
            centroid = circular_mean(phases)
            trio_centroids.append((centroid, trio))
            trio_member_ids.update(trio)

        # ── Q1: Formation conditions ──
        for trio in trios[:50]:  # cap per seed
            members = list(trio)
            borns = [li[m]["born"] for m in members]
            formation_win = max(borns)  # trio completes when last member born
            formation_windows.append(formation_win)

            # Conditions at formation window
            for m in members:
                age_at_form = formation_win - li[m]["born"]
                formation_member_ages.append(age_at_form)
                formation_member_sizes.append(li[m]["nodes"])
                vac = bin_vac_at[m].get(formation_win, 0)
                occ = bin_occ_at[m].get(formation_win, 0)
                formation_vacancy.append(vac)
                formation_occupancy.append(occ)

        # ── Q2: Stress signals at end ──
        for trio in trios[:50]:
            members = list(trio)
            # Share trend in last 20 windows
            for m in members:
                shares_late = []
                for w in range(max(1, max_win - 19), max_win + 1):
                    s = share_at[m].get(w, 0)
                    if s > 0:
                        shares_late.append(s)
                if len(shares_late) >= 10:
                    # Simple linear slope
                    x = np.arange(len(shares_late))
                    slope = np.polyfit(x, shares_late, 1)[0]
                    end_share_trends.append(slope)

            # Min share at final window
            final_shares = [share_at[m].get(max_win, 0) for m in members]
            if all(s > 0 for s in final_shares):
                end_min_shares.append(min(final_shares))

        # ── Q3: Trio-trio competition ──
        if len(trio_centroids) >= 2:
            for i in range(min(len(trio_centroids), 60)):
                ci, ti = trio_centroids[i]
                for j in range(i + 1, min(len(trio_centroids), 60)):
                    cj, tj = trio_centroids[j]
                    dist = phase_dist(ci, cj)
                    trio_pair_distances.append(dist)

                    # Do close trio pairs have more displacement between them?
                    if dist < 0.3:
                        # Count non-survivor deaths between the two centroids
                        mid_phase = circular_mean([ci, cj])
                        deaths_between = 0
                        for lid, info in li.items():
                            if lid in trio_member_ids:
                                continue
                            if info["died"] <= max_win:
                                if phase_dist(info["phase_sig"], mid_phase) < dist / 2:
                                    deaths_between += 1
                        close_trio_pair_events.append({
                            "dist": dist,
                            "deaths_between": deaths_between,
                        })

        # ── Q4: Birth suppression mechanism ──
        # For each non-trio label born after w10:
        # measure combined trio share in its phase bin at birth
        for lid, info in li.items():
            if lid in trio_member_ids:
                continue
            if info["born"] <= 10:
                continue

            birth_win = info["born"]
            birth_phase = info["phase_sig"]
            survived = lid in survivors

            # Combined share of all trio members within 0.2 rad
            combined_trio_share = 0.0
            for tm_id in trio_member_ids:
                if tm_id in li and phase_dist(birth_phase, li[tm_id]["phase_sig"]) < 0.2:
                    combined_trio_share += share_at[tm_id].get(birth_win, 0)

            region_share_vs_birth_survival.append({
                "combined_share": combined_trio_share,
                "survived": survived,
            })

            # Vacancy distinction (old Claude's point)
            birth_vac = bin_vac_at[lid].get(birth_win, 0)
            near_trio = any(
                phase_dist(birth_phase, c) < 0.2
                for c, _ in trio_centroids
            )
            vacancy_categories.append({
                "vacancy": birth_vac,
                "near_trio": near_trio,
                "survived": survived,
            })

        # ── Q5: Role differentiation over time ──
        for trio in trios[:50]:
            members = list(trio)
            phases = [li[m]["phase_sig"] for m in members]

            # Center = most phase-central
            centrality = []
            for m in members:
                mean_d = np.mean([phase_dist(li[m]["phase_sig"], li[o]["phase_sig"])
                                  for o in members if o != m])
                centrality.append((m, mean_d))
            centrality.sort(key=lambda x: x[1])
            center = centrality[0][0]
            edges = [centrality[1][0], centrality[2][0]]

            formation_win = max(li[m]["born"] for m in members)

            # Early: formation + 10 windows
            early_win = min(formation_win + 10, max_win)
            cs_early = share_at[center].get(early_win, 0)
            ct_early = territory_at[center].get(early_win, 0)
            es_early = np.mean([share_at[e].get(early_win, 0) for e in edges])
            et_early = np.mean([territory_at[e].get(early_win, 0) for e in edges])

            if cs_early > 0:
                early_center_share.append(cs_early)
                early_edge_share.append(es_early)
                early_center_terr.append(ct_early)
                early_edge_terr.append(et_early)

            # Late: w150+
            late_win = max(150, formation_win + 50)
            if late_win <= max_win:
                cs_late = share_at[center].get(late_win, 0)
                ct_late = territory_at[center].get(late_win, 0)
                es_late = np.mean([share_at[e].get(late_win, 0) for e in edges])
                et_late = np.mean([territory_at[e].get(late_win, 0) for e in edges])

                if cs_late > 0:
                    late_center_share.append(cs_late)
                    late_edge_share.append(es_late)
                    late_center_terr.append(ct_late)
                    late_edge_terr.append(et_late)

        # Bonus: share stability by trio age
        for trio in trios[:30]:
            members = list(trio)
            formation_win = max(li[m]["born"] for m in members)
            trio_age = max_win - formation_win

            # Share CV (coefficient of variation) over last 30 windows
            share_series = []
            for w in range(max(1, max_win - 29), max_win + 1):
                total = sum(share_at[m].get(w, 0) for m in members)
                if total > 0:
                    share_series.append(total)
            if len(share_series) >= 10:
                cv = np.std(share_series) / np.mean(share_series)
                trio_age_vs_share_stability.append({
                    "age": trio_age,
                    "cv": cv,
                })

        if (seed_idx + 1) % 10 == 0:
            print(f"  ... processed {seed_idx + 1}/{len(seeds)} seeds",
                  flush=True)

    # ═══════════════════════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════════════════════

    # ── Q1: How do trios form? ──
    print(f"\n{'=' * 72}")
    print(f"Q1. HOW DO TRIOS FORM?")
    print(f"{'=' * 72}\n")

    if formation_windows:
        print(f"  Formation window: mean={np.mean(formation_windows):.1f} "
              f"median={np.median(formation_windows):.0f} "
              f"std={np.std(formation_windows):.1f}")
        # Distribution by quartile
        q_bins = [(0, 25), (25, 50), (50, 100), (100, 201)]
        for lo, hi in q_bins:
            n = sum(1 for w in formation_windows if lo <= w < hi)
            print(f"    w{lo}-{hi}: {n} ({n / len(formation_windows) * 100:.0f}%)")

    if formation_member_ages:
        print(f"\n  Member age at formation: mean={np.mean(formation_member_ages):.1f} "
              f"median={np.median(formation_member_ages):.0f}")
        # How many are age=0 (born at formation window)?
        newborns = sum(1 for a in formation_member_ages if a == 0)
        print(f"    Newborn at formation: {newborns}/{len(formation_member_ages)} "
              f"({newborns / len(formation_member_ages) * 100:.0f}%)")

    if formation_member_sizes:
        sc = Counter(formation_member_sizes)
        print(f"\n  Member size at formation:")
        for size, count in sc.most_common():
            print(f"    {size}-node: {count} ({count / len(formation_member_sizes) * 100:.0f}%)")

    if formation_vacancy:
        print(f"\n  Vacancy at formation: mean={np.mean(formation_vacancy):.4f}")
        print(f"  Occupancy at formation: mean={np.mean(formation_occupancy):.6f}")

    # ── Q2: How do trios die? ──
    print(f"\n{'=' * 72}")
    print(f"Q2. HOW DO TRIOS DIE? (stress signals)")
    print(f"{'=' * 72}\n")

    print(f"  Note: 100% intact at w200. Looking for pre-death signals.\n")

    if end_share_trends:
        slopes = end_share_trends
        declining = sum(1 for s in slopes if s < 0)
        print(f"  Share slope (last 20 win): mean={np.mean(slopes):.8f} "
              f"std={np.std(slopes):.8f}")
        print(f"  Declining: {declining}/{len(slopes)} ({declining / len(slopes) * 100:.0f}%)")

    if end_min_shares:
        print(f"\n  Min member share at w200: mean={np.mean(end_min_shares):.6f} "
              f"std={np.std(end_min_shares):.6f}")
        at_risk = sum(1 for s in end_min_shares if s < 0.005)
        print(f"  Near death threshold (<0.005): {at_risk}/{len(end_min_shares)}")
        if at_risk == 0:
            print(f"  → No trios near death. 200 windows insufficient to see trio death.")
            print(f"  → Recommend: 500-window run")

    # ── Q3: Trio-trio competition ──
    print(f"\n{'=' * 72}")
    print(f"Q3. DO TRIOS COMPETE WITH EACH OTHER?")
    print(f"{'=' * 72}\n")

    if trio_pair_distances:
        dists = trio_pair_distances
        print(f"  Trio-pair distances: n={len(dists)}")
        print(f"    mean={np.mean(dists):.4f} median={np.median(dists):.4f}")
        close = sum(1 for d in dists if d < 0.1)
        medium = sum(1 for d in dists if 0.1 <= d < 0.3)
        far = sum(1 for d in dists if d >= 0.3)
        total = len(dists)
        print(f"    Close (<0.1): {close} ({close / total * 100:.0f}%)")
        print(f"    Medium (0.1-0.3): {medium} ({medium / total * 100:.0f}%)")
        print(f"    Far (>0.3): {far} ({far / total * 100:.0f}%)")

    if close_trio_pair_events:
        deaths = [e["deaths_between"] for e in close_trio_pair_events]
        print(f"\n  Close trio pairs (<0.3 rad): {len(close_trio_pair_events)}")
        print(f"  Deaths between close pairs: mean={np.mean(deaths):.1f} "
              f"total={sum(deaths)}")
        if sum(deaths) > 0:
            print(f"  → Close trios create kill zones between them")
        else:
            print(f"  → No inter-trio kill zone detected")

    # ── Q4: Birth suppression mechanism ──
    print(f"\n{'=' * 72}")
    print(f"Q4. WHAT CAUSES BIRTH SUPPRESSION NEAR TRIOS?")
    print(f"{'=' * 72}\n")

    # 4a: Combined share pressure
    print(f"  --- 4a. Combined trio share vs birth survival ---\n")

    if region_share_vs_birth_survival:
        # Bin by combined share
        share_bins = [
            (0.0, 0.01, "no trio share"),
            (0.01, 0.03, "low trio share"),
            (0.03, 0.06, "medium trio share"),
            (0.06, 1.0, "high trio share"),
        ]
        print(f"  {'share_range':>20} {'total':>6} {'surv':>5} {'rate':>8}")
        print(f"  {'-' * 44}")
        for lo, hi, label in share_bins:
            in_bin = [x for x in region_share_vs_birth_survival
                      if lo <= x["combined_share"] < hi]
            surv = sum(1 for x in in_bin if x["survived"])
            rate = surv / max(1, len(in_bin))
            print(f"  {label:>20} {len(in_bin):>6} {surv:>5} {rate:>8.4f}")

    # 4b: Vacancy distinction (old Claude's point)
    print(f"\n  --- 4b. Vacancy × trio proximity (old Claude insight) ---\n")
    print(f"  Phase A vacancy = 'no label here' (death zone)")
    print(f"  Far from trio = 'no trio here' (may have solo labels)\n")

    if vacancy_categories:
        # 2×2 table: (near_trio, high_vacancy) → survival rate
        categories = {
            "near_trio + low_vac":  {"n": 0, "s": 0},
            "near_trio + high_vac": {"n": 0, "s": 0},
            "far_trio + low_vac":   {"n": 0, "s": 0},
            "far_trio + high_vac":  {"n": 0, "s": 0},
        }
        median_vac = np.median([x["vacancy"] for x in vacancy_categories])

        for x in vacancy_categories:
            near = "near_trio" if x["near_trio"] else "far_trio"
            vac = "high_vac" if x["vacancy"] > median_vac else "low_vac"
            key = f"{near} + {vac}"
            categories[key]["n"] += 1
            if x["survived"]:
                categories[key]["s"] += 1

        print(f"  Vacancy median: {median_vac:.4f}\n")
        print(f"  {'category':>25} {'total':>6} {'surv':>5} {'rate':>8}")
        print(f"  {'-' * 48}")
        for cat, vals in categories.items():
            rate = vals["s"] / max(1, vals["n"])
            print(f"  {cat:>25} {vals['n']:>6} {vals['s']:>5} {rate:>8.4f}")

        # Which factor dominates?
        near_low = categories["near_trio + low_vac"]
        near_high = categories["near_trio + high_vac"]
        far_low = categories["far_trio + low_vac"]
        far_high = categories["far_trio + high_vac"]

        near_rate = (near_low["s"] + near_high["s"]) / max(1, near_low["n"] + near_high["n"])
        far_rate = (far_low["s"] + far_high["s"]) / max(1, far_low["n"] + far_high["n"])
        low_vac_rate = (near_low["s"] + far_low["s"]) / max(1, near_low["n"] + far_low["n"])
        high_vac_rate = (near_high["s"] + far_high["s"]) / max(1, near_high["n"] + far_high["n"])

        print(f"\n  Marginal rates:")
        print(f"    Near trio: {near_rate:.4f}    Far: {far_rate:.4f}  "
              f"(trio effect: {far_rate / max(near_rate, 0.0001):.1f}× — far is better)")
        print(f"    Low vac:   {low_vac_rate:.4f}  High vac: {high_vac_rate:.4f}  "
              f"(vacancy effect: {low_vac_rate / max(high_vac_rate, 0.0001):.1f}× — low vac is better)")

        # Both expressed as favorable/unfavorable ratio (>1 = stronger effect)
        trio_effect = far_rate / max(near_rate, 0.0001)
        vac_effect = low_vac_rate / max(high_vac_rate, 0.0001)

        if trio_effect > vac_effect * 1.5:
            print(f"\n  → TRIO PROXIMITY is the dominant factor")
        elif vac_effect > trio_effect * 1.5:
            print(f"\n  → VACANCY is the dominant factor")
        else:
            print(f"\n  → Both factors contribute comparably")

    # ── Q5: Role differentiation over time ──
    print(f"\n{'=' * 72}")
    print(f"Q5. DOES ROLE DIFFERENTIATION EMERGE OVER TIME?")
    print(f"{'=' * 72}\n")

    if early_center_share and late_center_share:
        print(f"  Share (center vs edge):")
        print(f"    Early:  center={np.mean(early_center_share):.6f}  "
              f"edge={np.mean(early_edge_share):.6f}  "
              f"ratio={np.mean(early_center_share) / max(np.mean(early_edge_share), 0.000001):.3f}×")
        print(f"    Late:   center={np.mean(late_center_share):.6f}  "
              f"edge={np.mean(late_edge_share):.6f}  "
              f"ratio={np.mean(late_center_share) / max(np.mean(late_edge_share), 0.000001):.3f}×")

        early_ratio = np.mean(early_center_share) / max(np.mean(early_edge_share), 0.000001)
        late_ratio = np.mean(late_center_share) / max(np.mean(late_edge_share), 0.000001)
        print(f"\n    Ratio change: {early_ratio:.3f} → {late_ratio:.3f}")

        if abs(late_ratio - early_ratio) > 0.05:
            print(f"    → Differentiation {'INCREASES' if late_ratio > early_ratio else 'DECREASES'} over time")
        else:
            print(f"    → No significant differentiation change")

    if early_center_terr and late_center_terr:
        print(f"\n  Territory (center vs edge):")
        print(f"    Early:  center={np.mean(early_center_terr):.1f}  "
              f"edge={np.mean(early_edge_terr):.1f}  "
              f"ratio={np.mean(early_center_terr) / max(np.mean(early_edge_terr), 0.1):.2f}×")
        print(f"    Late:   center={np.mean(late_center_terr):.1f}  "
              f"edge={np.mean(late_edge_terr):.1f}  "
              f"ratio={np.mean(late_center_terr) / max(np.mean(late_edge_terr), 0.1):.2f}×")

    # ── Bonus: α-sensitivity proxy ──
    print(f"\n{'=' * 72}")
    print(f"BONUS: IS TRIO AN ARTIFACT OF MATURATION α?")
    print(f"{'=' * 72}\n")

    if trio_age_vs_share_stability:
        # Split by trio age
        young = [x for x in trio_age_vs_share_stability if x["age"] < 100]
        old = [x for x in trio_age_vs_share_stability if x["age"] >= 100]

        if young and old:
            print(f"  Young trios (age<100): n={len(young)} "
                  f"share CV={np.mean([x['cv'] for x in young]):.4f}")
            print(f"  Old trios (age>=100):  n={len(old)} "
                  f"share CV={np.mean([x['cv'] for x in old]):.4f}")
            y_cv = np.mean([x["cv"] for x in young])
            o_cv = np.mean([x["cv"] for x in old])
            if y_cv > o_cv * 1.3:
                print(f"  → Young trios are LESS stable. Consistent with maturation effect")
                print(f"  → But does NOT prove trio is purely α-artifact")
                print(f"  → Need: rerun with α=0.05 and α=0.15 to test directly")
            else:
                print(f"  → Young and old trios equally stable")
                print(f"  → Trio stability may be structural, not maturation-dependent")
    else:
        print(f"  Insufficient data for α-sensitivity analysis")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'=' * 72}")
    print(f"SUMMARY")
    print(f"{'=' * 72}")

    print(f"\n  Q1 (formation):")
    if formation_windows:
        print(f"    Trios form at w{np.median(formation_windows):.0f} (median)")
        newborn_pct = sum(1 for a in formation_member_ages if a == 0) / max(1, len(formation_member_ages))
        print(f"    {newborn_pct:.0%} of members are newborn at formation")

    print(f"\n  Q2 (death):")
    if end_min_shares:
        at_risk = sum(1 for s in end_min_shares if s < 0.005)
        print(f"    {at_risk}/{len(end_min_shares)} trios near death threshold")
        print(f"    Need 500-window run to observe trio death")

    print(f"\n  Q3 (competition):")
    if trio_pair_distances:
        close_pct = sum(1 for d in trio_pair_distances if d < 0.1) / len(trio_pair_distances) * 100
        print(f"    {close_pct:.0f}% of trio pairs within 0.1 rad")

    print(f"\n  Q4 (suppression mechanism):")
    if vacancy_categories:
        print(f"    Trio effect: {trio_effect:.1f}×  Vacancy effect: {vac_effect:.1f}×")
        if trio_effect > vac_effect * 1.5:
            print(f"    → Trio proximity dominates")
        elif vac_effect > trio_effect * 1.5:
            print(f"    → Vacancy dominates")
        else:
            print(f"    → Both contribute")

    print(f"\n  Q5 (differentiation):")
    if early_center_share and late_center_share:
        print(f"    Early ratio: {early_ratio:.3f}  Late: {late_ratio:.3f}")

    print(f"\n  Next steps:")
    print(f"    - 500-window run to observe trio death (Q2)")
    print(f"    - α=0.05/0.15 sensitivity test (Bonus)")
    print(f"    - trio share budget analysis: do 3 labels × ~0.016 = 0.048")
    print(f"      consume local budget and block newcomers? (Q4)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
