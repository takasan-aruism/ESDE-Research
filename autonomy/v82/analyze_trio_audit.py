#!/usr/bin/env python3
"""
ESDE v8.2 — Trio Additional Audit
=====================================
GPT audit directive: trio は単体 label の和ではない作用を持つか？

1. trio 周辺で birth / death が偏るか
2. trio があると R+ / bridge が増えるか
3. trio 単位で displacement が起きるか
4. trio の存在が他 label の survival を変えるか
5. 6+ node 観測強化（母数拡大）

Runs on Ryzen: python analyze_trio_audit.py --dir diag_v82_baseline

Data source: *_detail.json (lifecycle_log)
"""

import json, glob, argparse, numpy as np, math
from collections import defaultdict, Counter
from pathlib import Path


def phase_dist(a, b):
    """Circular distance on [0, 2π)."""
    d = abs(a - b)
    if d > math.pi:
        d = 2 * math.pi - d
    return d


def find_trios(survivors, label_info, phase_threshold=0.4):
    """Find all trio groups among survivors.
    A trio = 3 survivors where all pairwise phase_dist < threshold.
    Returns list of frozenset(lid, lid, lid)."""
    trios = []
    surv_list = sorted(survivors, key=lambda x: label_info[x]["phase_sig"])
    n = len(surv_list)
    for i in range(n):
        a = surv_list[i]
        pa = label_info[a]["phase_sig"]
        for j in range(i + 1, n):
            b = surv_list[j]
            pb = label_info[b]["phase_sig"]
            if phase_dist(pa, pb) > phase_threshold:
                continue
            for k in range(j + 1, n):
                c = surv_list[k]
                pc = label_info[c]["phase_sig"]
                if phase_dist(pa, pc) > phase_threshold:
                    continue
                if phase_dist(pb, pc) > phase_threshold:
                    continue
                trios.append(frozenset([a, b, c]))
    return trios


def build_seed_data(data):
    """Build label_info, per-window alive sets, per-window share/territory."""
    log = data["lifecycle_log"]
    traj = defaultdict(list)
    for e in log:
        traj[e["label_id"]].append(e)

    max_win = max(e["window"] for e in log)

    label_info = {}
    alive_per_win = defaultdict(set)
    share_at = defaultdict(dict)       # lid → {win: share}
    territory_at = defaultdict(dict)   # lid → {win: territory}
    rplus_at = defaultdict(dict)       # lid → {win: territory_rplus}

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

    survivors = {lid for lid in label_info if label_info[lid]["died"] > max_win}

    return {
        "label_info": label_info,
        "alive_per_win": alive_per_win,
        "share_at": share_at,
        "territory_at": territory_at,
        "rplus_at": rplus_at,
        "survivors": survivors,
        "max_win": max_win,
        "traj": traj,
    }


def main(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data

    print(f"{'=' * 72}")
    print(f"TRIO ADDITIONAL AUDIT (GPT directive)")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'=' * 72}")

    # ═══════════════════════════════════════════════════════════
    # ACCUMULATORS
    # ═══════════════════════════════════════════════════════════

    # §1 birth/death bias near trios
    birth_near_trio = []     # labels born near trio phase region
    birth_far_trio = []      # labels born far from trio
    death_near_trio = []     # labels died near trio
    death_far_trio = []      # labels died far from trio

    # §2 R+ / bridge near trios
    rplus_trio_region = []   # R+ per window in trio phase region
    rplus_nontrio_region = []

    # §3 trio-unit displacement
    trio_unit_displacements = []  # did a trio as a whole push out a neighbor?

    # §4 trio effect on other label survival
    # Compare: labels born near trio vs far from trio → survival rate
    surv_near_trio = []
    surv_far_trio = []

    # §5 6+ node extended
    all_sixplus = []

    # §6 size breakdown: trio member vs solo (from vs_solo §4)
    trio_member_by_size = Counter()
    solo_by_size = Counter()

    # Also: trio count per seed for context
    trio_counts = []

    TRIO_PROXIMITY = 0.2  # rad: "near a trio" threshold
    TRIO_PHASE_THRESHOLD = 0.2  # for trio detection (matches Phase A/B analysis)

    for seed_idx, (seed, data) in enumerate(sorted(seeds.items())):
        sd = build_seed_data(data)
        li = sd["label_info"]
        survivors = sd["survivors"]
        alive_pw = sd["alive_per_win"]
        share_at = sd["share_at"]
        territory_at = sd["territory_at"]
        rplus_at = sd["rplus_at"]
        max_win = sd["max_win"]

        if len(survivors) < 3:
            continue

        trios = find_trios(survivors, li, phase_threshold=TRIO_PHASE_THRESHOLD)
        trio_counts.append(len(trios))

        # Compute trio phase centers
        trio_centers = []
        trio_member_ids = set()
        for trio in trios:
            members = list(trio)
            phases = [li[m]["phase_sig"] for m in members]
            # Circular mean
            sx = sum(math.cos(p) for p in phases) / 3
            sy = sum(math.sin(p) for p in phases) / 3
            center = math.atan2(sy, sx) % (2 * math.pi)
            trio_centers.append(center)
            trio_member_ids.update(members)

        # §6: count trio members vs solo by size
        solo_survivors = survivors - trio_member_ids
        for lid in trio_member_ids:
            if lid in li:
                trio_member_by_size[li[lid]["nodes"]] += 1
        for lid in solo_survivors:
            if lid in li:
                solo_by_size[li[lid]["nodes"]] += 1

        def near_any_trio(phase):
            """Is this phase within TRIO_PROXIMITY of any trio center?"""
            for tc in trio_centers:
                if phase_dist(phase, tc) < TRIO_PROXIMITY:
                    return True
            return False

        # ── §1: Birth/death bias near trios ──
        # Only count non-trio-member labels (to avoid self-correlation)
        for lid, info in li.items():
            if lid in trio_member_ids:
                continue
            near = near_any_trio(info["phase_sig"])

            if info["born"] > 10:  # skip initial burst
                entry = {
                    "age": min(info["died"], max_win) - info["born"],
                    "survived": lid in survivors,
                    "nodes": info["nodes"],
                }
                if near:
                    birth_near_trio.append(entry)
                else:
                    birth_far_trio.append(entry)

            if info["died"] <= max_win:  # died
                if near:
                    death_near_trio.append(info["died"] - info["born"])
                else:
                    death_far_trio.append(info["died"] - info["born"])

        # ── §2: R+ in trio vs non-trio phase regions ──
        # Sample windows w100-200 (steady state)
        for w in range(100, min(max_win + 1, 201), 5):  # every 5th window
            alive_this_win = alive_pw.get(w, set())
            trio_rplus = 0
            trio_count = 0
            nontrio_rplus = 0
            nontrio_count = 0
            for lid in alive_this_win:
                if lid not in li:
                    continue
                rp = rplus_at[lid].get(w, 0)
                if near_any_trio(li[lid]["phase_sig"]):
                    trio_rplus += rp
                    trio_count += 1
                else:
                    nontrio_rplus += rp
                    nontrio_count += 1
            if trio_count > 0:
                rplus_trio_region.append(trio_rplus / trio_count)
            if nontrio_count > 0:
                rplus_nontrio_region.append(nontrio_rplus / nontrio_count)

        # ── §3: Trio-unit displacement ──
        # Does the trio as a unit push out nearby non-members?
        # For each trio, count deaths of non-members within proximity
        # vs deaths of non-members far from all trios
        for trio in trios:
            members = list(trio)
            trio_phase = [li[m]["phase_sig"] for m in members]
            sx = sum(math.cos(p) for p in trio_phase) / 3
            sy = sum(math.sin(p) for p in trio_phase) / 3
            center = math.atan2(sy, sx) % (2 * math.pi)

            # Trio formation window (latest born among members)
            trio_born = max(li[m]["born"] for m in members)

            # Count non-member deaths near this trio after formation
            near_deaths = 0
            far_deaths = 0
            for lid, info in li.items():
                if lid in trio_member_ids:
                    continue
                if info["died"] <= max_win and info["died"] > trio_born:
                    if phase_dist(info["phase_sig"], center) < TRIO_PROXIMITY:
                        near_deaths += 1
                    else:
                        far_deaths += 1

            trio_unit_displacements.append({
                "near_deaths": near_deaths,
                "far_deaths": far_deaths,
                "trio_size": sum(li[m]["nodes"] for m in members),
            })

        # ── §4: Survival rate near vs far from trio ──
        for lid, info in li.items():
            if lid in trio_member_ids:
                continue
            if info["born"] <= 10:
                continue
            near = near_any_trio(info["phase_sig"])
            survived = lid in survivors
            if near:
                surv_near_trio.append(survived)
            else:
                surv_far_trio.append(survived)

        # ── §5: 6+ node extended ──
        for lid in survivors:
            info = li[lid]
            if info["nodes"] < 6:
                continue
            # Gather richer data
            age = min(info["died"], max_win) - info["born"]
            mid_win = (info["born"] + min(info["died"], max_win)) // 2
            share_val = share_at[lid].get(mid_win, 0)
            terr = territory_at[lid].get(mid_win, 0)
            rp = rplus_at[lid].get(mid_win, 0)

            # Share trajectory (birth → mid → last)
            share_birth = share_at[lid].get(info["born"], 0)
            share_last_win = max(share_at[lid].keys()) if share_at[lid] else info["born"]
            share_last = share_at[lid].get(share_last_win, 0)

            # Neighbors (other survivors within 0.3 rad)
            neighbors = []
            for other in survivors:
                if other == lid:
                    continue
                if phase_dist(info["phase_sig"], li[other]["phase_sig"]) < 0.3:
                    neighbors.append(li[other]["nodes"])

            # In a trio?
            in_trio = lid in trio_member_ids

            all_sixplus.append({
                "seed": seed,
                "nodes": info["nodes"],
                "age": age,
                "share_birth": share_birth,
                "share_mid": share_val,
                "share_last": share_last,
                "territory": terr,
                "rplus": rp,
                "n_neighbors": len(neighbors),
                "neighbor_sizes": neighbors,
                "in_trio": in_trio,
            })

        if (seed_idx + 1) % 10 == 0:
            print(f"  ... processed {seed_idx + 1}/{len(seeds)} seeds",
                  flush=True)

    # ═══════════════════════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════════════════════

    print(f"\n  Trios per seed: mean={np.mean(trio_counts):.1f} "
          f"median={np.median(trio_counts):.0f} "
          f"min={min(trio_counts)} max={max(trio_counts)}")

    # ── §1: Birth/death bias ──
    print(f"\n{'=' * 72}")
    print(f"1. BIRTH/DEATH BIAS NEAR TRIOS")
    print(f"{'=' * 72}\n")

    print(f"  Labels born near trio:  {len(birth_near_trio)}")
    print(f"  Labels born far:        {len(birth_far_trio)}")

    if birth_near_trio and birth_far_trio:
        near_ages = [b["age"] for b in birth_near_trio]
        far_ages = [b["age"] for b in birth_far_trio]
        print(f"\n  Mean lifespan near trio:  {np.mean(near_ages):.1f} windows")
        print(f"  Mean lifespan far:        {np.mean(far_ages):.1f} windows")

        near_surv = sum(1 for b in birth_near_trio if b["survived"])
        far_surv = sum(1 for b in birth_far_trio if b["survived"])
        near_rate = near_surv / max(1, len(birth_near_trio))
        far_rate = far_surv / max(1, len(birth_far_trio))
        print(f"\n  Survival rate near trio:  {near_rate:.4f} "
              f"({near_surv}/{len(birth_near_trio)})")
        print(f"  Survival rate far:        {far_rate:.4f} "
              f"({far_surv}/{len(birth_far_trio)})")
        if far_rate > 0:
            print(f"  Ratio (near/far): {near_rate / far_rate:.2f}×")

        # Death age distribution
        if death_near_trio and death_far_trio:
            print(f"\n  Death age near trio: mean={np.mean(death_near_trio):.1f} "
                  f"median={np.median(death_near_trio):.0f}")
            print(f"  Death age far:       mean={np.mean(death_far_trio):.1f} "
                  f"median={np.median(death_far_trio):.0f}")

    # ── §2: R+ near trios ──
    print(f"\n{'=' * 72}")
    print(f"2. R+ / BRIDGE NEAR TRIOS")
    print(f"{'=' * 72}\n")

    if rplus_trio_region and rplus_nontrio_region:
        tr = np.mean(rplus_trio_region)
        nr = np.mean(rplus_nontrio_region)
        print(f"  R+ per label (trio region):     {tr:.4f} "
              f"(n={len(rplus_trio_region)})")
        print(f"  R+ per label (non-trio region):  {nr:.4f} "
              f"(n={len(rplus_nontrio_region)})")
        if nr > 0:
            print(f"  Ratio: {tr / nr:.2f}×")
        print(f"\n  → {'Trio regions have MORE R+' if tr > nr * 1.1 else 'No significant R+ difference'}")

    # ── §3: Trio-unit displacement ──
    print(f"\n{'=' * 72}")
    print(f"3. TRIO-UNIT DISPLACEMENT")
    print(f"{'=' * 72}\n")

    if trio_unit_displacements:
        near_d = [t["near_deaths"] for t in trio_unit_displacements]
        far_d = [t["far_deaths"] for t in trio_unit_displacements]
        print(f"  Trios analyzed: {len(trio_unit_displacements)}")
        print(f"  Non-member deaths NEAR trio: mean={np.mean(near_d):.1f} "
              f"total={sum(near_d)}")
        print(f"  Non-member deaths FAR:       mean={np.mean(far_d):.1f} "
              f"total={sum(far_d)}")

        # Normalize by phase space coverage
        # Trio proximity covers ~0.2 rad out of 2π ≈ 3.2% of phase space
        # So if deaths are uniform, near should be ~3.2% of total
        total_d = sum(near_d) + sum(far_d)
        if total_d > 0:
            near_frac = sum(near_d) / total_d
            expected_frac = TRIO_PROXIMITY / math.pi  # fraction of phase space
            print(f"\n  Near-death fraction:  {near_frac:.3f}")
            print(f"  Expected (uniform):   {expected_frac:.3f}")
            print(f"  Enrichment: {near_frac / max(expected_frac, 0.001):.1f}×")
            if near_frac > expected_frac * 1.5:
                print(f"  → Trios ACTIVELY displace nearby labels")
            elif near_frac > expected_frac * 1.1:
                print(f"  → Mild displacement effect")
            else:
                print(f"  → No displacement above background")

    # ── §4: Trio effect on other label survival ──
    print(f"\n{'=' * 72}")
    print(f"4. TRIO EFFECT ON OTHER LABEL SURVIVAL")
    print(f"{'=' * 72}\n")

    if surv_near_trio and surv_far_trio:
        near_rate = sum(surv_near_trio) / len(surv_near_trio)
        far_rate = sum(surv_far_trio) / len(surv_far_trio)
        print(f"  Labels near trio:  n={len(surv_near_trio)} "
              f"survival={near_rate:.4f}")
        print(f"  Labels far:        n={len(surv_far_trio)} "
              f"survival={far_rate:.4f}")
        if far_rate > 0:
            ratio = near_rate / far_rate
            print(f"  Ratio: {ratio:.2f}×")
            if ratio < 0.8:
                print(f"  → Trio SUPPRESSES nearby label survival")
            elif ratio > 1.2:
                print(f"  → Trio ENHANCES nearby label survival")
            else:
                print(f"  → No significant effect on nearby survival")

    # ── §5: 6+ node extended observation ──
    print(f"\n{'=' * 72}")
    print(f"5. 6+ NODE EXTENDED OBSERVATION")
    print(f"{'=' * 72}\n")

    print(f"  Total 6+ survivors across all seeds: {len(all_sixplus)}")

    if all_sixplus:
        # By size
        by_size = defaultdict(list)
        for s in all_sixplus:
            by_size[s["nodes"]].append(s)

        print(f"\n  {'size':>4} {'count':>5} {'age':>5} {'share_mid':>10} "
              f"{'terr':>5} {'R+':>4} {'neigh':>5} {'in_trio':>8}")
        print(f"  {'-' * 55}")
        for size in sorted(by_size):
            items = by_size[size]
            print(f"  {size:>4} {len(items):>5} "
                  f"{np.mean([s['age'] for s in items]):>5.0f} "
                  f"{np.mean([s['share_mid'] for s in items]):>10.4f} "
                  f"{np.mean([s['territory'] for s in items]):>5.1f} "
                  f"{np.mean([s['rplus'] for s in items]):>4.1f} "
                  f"{np.mean([s['n_neighbors'] for s in items]):>5.1f} "
                  f"{sum(1 for s in items if s['in_trio']):>5}/{len(items)}")

        # Share trajectory: do 6+ grow?
        print(f"\n  Share trajectory (6+ only):")
        births = [s["share_birth"] for s in all_sixplus if s["share_birth"] > 0]
        mids = [s["share_mid"] for s in all_sixplus if s["share_mid"] > 0]
        lasts = [s["share_last"] for s in all_sixplus if s["share_last"] > 0]
        if births and mids and lasts:
            print(f"    Birth: {np.mean(births):.5f}")
            print(f"    Mid:   {np.mean(mids):.5f}")
            print(f"    Last:  {np.mean(lasts):.5f}")
            if np.mean(lasts) > np.mean(births) * 1.1:
                print(f"    → 6+ labels GROW over time")
            elif np.mean(lasts) < np.mean(births) * 0.9:
                print(f"    → 6+ labels SHRINK over time")
            else:
                print(f"    → 6+ labels remain STABLE")

        # Neighbor composition
        all_neigh_sizes = []
        for s in all_sixplus:
            all_neigh_sizes.extend(s["neighbor_sizes"])
        if all_neigh_sizes:
            nc = Counter(all_neigh_sizes)
            print(f"\n  Neighbor size distribution of 6+:")
            for size, count in nc.most_common():
                print(f"    {size}-node: {count} ({count / len(all_neigh_sizes) * 100:.0f}%)")

    # ── §6: Size breakdown: trio member vs solo ──
    print(f"\n{'=' * 72}")
    print(f"6. SIZE BREAKDOWN: TRIO MEMBER vs SOLO SURVIVOR")
    print(f"{'=' * 72}\n")

    all_sizes = sorted(set(list(trio_member_by_size.keys()) +
                           list(solo_by_size.keys())))
    if all_sizes:
        print(f"  {'size':>5} {'trio':>6} {'solo':>6} {'total':>6} {'trio%':>7}")
        print(f"  {'-' * 34}")
        for n in all_sizes:
            t = trio_member_by_size.get(n, 0)
            s = solo_by_size.get(n, 0)
            total = t + s
            if total >= 3:
                pct = t / total * 100
                print(f"  {n:>5} {t:>6} {s:>6} {total:>6} {pct:>6.0f}%")
        t_all = sum(trio_member_by_size.values())
        s_all = sum(solo_by_size.values())
        print(f"  {'ALL':>5} {t_all:>6} {s_all:>6} {t_all + s_all:>6} "
              f"{t_all / max(1, t_all + s_all) * 100:>6.0f}%")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"SUMMARY — KEY QUESTIONS")
    print(f"{'=' * 72}")

    # Track scores for auto-judgment
    evidence_for = 0   # count of Q1-Q4 supporting "more than proximity"
    evidence_against = 0

    print(f"\n  Q1: Does trio suppress nearby birth/extend death?")
    if birth_near_trio and birth_far_trio:
        nr = sum(1 for b in birth_near_trio if b["survived"]) / max(1, len(birth_near_trio))
        fr = sum(1 for b in birth_far_trio if b["survived"]) / max(1, len(birth_far_trio))
        if nr < fr * 0.8:
            print(f"    → YES. Near survival {nr:.4f} < far {fr:.4f}")
            evidence_for += 1
        else:
            print(f"    → NO clear suppression. Near={nr:.4f} Far={fr:.4f}")
            evidence_against += 1

    print(f"\n  Q2: Does trio increase R+?")
    if rplus_trio_region and rplus_nontrio_region:
        tr = np.mean(rplus_trio_region)
        nr = np.mean(rplus_nontrio_region)
        if tr > nr * 1.1:
            print(f"    → YES. Trio R+={tr:.4f} > non-trio {nr:.4f}")
            evidence_for += 1
        else:
            print(f"    → NO. Trio R+={tr:.4f} ≈ non-trio {nr:.4f}")
            evidence_against += 1

    print(f"\n  Q3: Does trio displace as a unit?")
    if trio_unit_displacements:
        total_d = sum(t["near_deaths"] + t["far_deaths"]
                      for t in trio_unit_displacements)
        near_total = sum(t["near_deaths"] for t in trio_unit_displacements)
        if total_d > 0:
            enrichment = (near_total / total_d) / max(TRIO_PROXIMITY / math.pi, 0.001)
            if enrichment > 1.5:
                print(f"    → YES. {enrichment:.1f}× enrichment of deaths near trios")
                evidence_for += 1
            else:
                print(f"    → WEAK. {enrichment:.1f}× enrichment")
                evidence_against += 1

    print(f"\n  Q4: Does trio affect other label survival?")
    if surv_near_trio and surv_far_trio:
        nr = sum(surv_near_trio) / len(surv_near_trio)
        fr = sum(surv_far_trio) / len(surv_far_trio)
        diff = nr - fr
        if abs(diff) > 0.001:
            direction = "suppresses" if diff < 0 else "enhances"
            print(f"    → Trio {direction} nearby survival: "
                  f"{nr:.4f} vs {fr:.4f} (Δ={diff:+.4f})")
            evidence_for += 1  # any measurable effect = non-additive
        else:
            print(f"    → No measurable effect")
            evidence_against += 1

    print(f"\n  Q5: Are 6+ nodes upper subject candidates?")
    if all_sixplus:
        in_trio_pct = sum(1 for s in all_sixplus if s["in_trio"]) / len(all_sixplus)
        mean_age = np.mean([s["age"] for s in all_sixplus])
        print(f"    → n={len(all_sixplus)}, "
              f"in_trio={in_trio_pct:.0%}, "
              f"mean_age={mean_age:.0f}")
        if len(all_sixplus) < 50:
            print(f"    → INSUFFICIENT DATA. Need more windows or seeds")
        elif in_trio_pct > 0.7:
            print(f"    → 6+ are trio members, not independent upper subjects")
        else:
            print(f"    → 6+ show independent existence")

    # Auto-judgment from Q1-Q4
    total_qs = evidence_for + evidence_against
    if total_qs >= 3:
        if evidence_for >= 3:
            verdict = "MORE than proximity — trio has non-additive effects"
        elif evidence_for >= 2:
            verdict = "LIKELY more than proximity — partial non-additive signal"
        elif evidence_for == 1:
            verdict = "WEAK — mostly proximity, one non-additive signal"
        else:
            verdict = "JUST proximity — no non-additive effects detected"
    else:
        verdict = "INSUFFICIENT — too few questions answered"

    print(f"\n  Overall: {evidence_for}/{total_qs} questions support non-additive effects")
    print(f"  Verdict: {verdict}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
