#!/usr/bin/env python3
"""
ESDE v8.2 — Node Dimension Transition Analysis
==================================================
GPT audit Task 1-3: 4→5 node boundary analysis

Task 1: 4-node / 5-node の差分の明文化
Task 2: n-node を次元（存在様式の型）として記述
Task 3: n→n+1 で何が変わるか（量的 vs 質的）

Core question: Where is the phase transition?
  2→3→4→5→6+: at which step does the qualitative shift occur?

Usage:
  python analyze_node_dimension.py --dir diag_v82_baseline
  python analyze_node_dimension.py --dir diag_v82_alpha0.05
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

    print(f"{'=' * 72}")
    print(f"NODE DIMENSION TRANSITION ANALYSIS")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'=' * 72}")

    # ═══════════════════════════════════════════════════════════
    # COLLECT
    # ═══════════════════════════════════════════════════════════

    all_labels = []

    for seed_idx, (seed, data) in enumerate(sorted(seeds.items())):
        log = data["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)

        max_win = max(e["window"] for e in log)
        dead_ids = set(e["label_id"] for e in log
                       if e["event"] in ("death", "macro_death"))

        for lid, entries in traj.items():
            births = [e for e in entries if e["event"] == "birth"]
            alives = [e for e in entries if e["event"] in ("birth", "alive")]
            if not births:
                continue

            b = births[0]
            last = alives[-1] if alives else b
            age = len(alives)

            # Share change rate (per window)
            shares = [e["share"] for e in alives]
            share_slope = 0
            if len(shares) >= 3:
                share_slope = (shares[-1] - shares[0]) / max(1, len(shares) - 1)

            # Alignment decay rate
            aligns = [abs(e.get("alignment", 0)) for e in alives]
            align_slope = 0
            if len(aligns) >= 3:
                align_slope = (aligns[-1] - aligns[0]) / max(1, len(aligns) - 1)

            # Territory stability (CV over lifetime)
            terrs = [e.get("territory_links", 0) for e in alives]
            terr_cv = np.std(terrs) / max(np.mean(terrs), 0.001) if len(terrs) >= 3 else 0

            # Phase neighbors at birth vs last
            n_neigh_birth = b.get("n_phase_neighbors", 0)
            n_neigh_last = last.get("n_phase_neighbors", 0)

            # Nearest label distance at birth vs last
            nearest_birth = b.get("nearest_label_dist", 0)
            nearest_last = last.get("nearest_label_dist", 0)

            all_labels.append({
                "seed": seed, "lid": lid,
                "nodes": b["nodes"],
                "survived": lid not in dead_ids,
                "age": age,
                # Birth
                "share_birth": b["share"],
                "align_birth": abs(b.get("alignment", 0)),
                "terr_birth": b.get("territory_links", 0),
                "occ_birth": b.get("bin_occupancy", 0),
                "vac_birth": b.get("bin_vacancy", 0),
                "n_neigh_birth": n_neigh_birth,
                "nearest_birth": nearest_birth,
                # Last
                "share_last": last["share"],
                "align_last": abs(last.get("alignment", 0)),
                "terr_last": last.get("territory_links", 0),
                "occ_last": last.get("bin_occupancy", 0),
                "nearest_last": nearest_last,
                "n_neigh_last": last.get("n_phase_neighbors", 0),
                # Dynamics
                "share_slope": share_slope,
                "align_slope": align_slope,
                "terr_cv": terr_cv,
            })

        if (seed_idx + 1) % 10 == 0:
            print(f"  ... processed {seed_idx + 1}/{len(seeds)} seeds",
                  flush=True)

    SIZES = [2, 3, 4, 5, 6]

    def sg(n):
        return min(n, 6)

    def sn(n):
        return f"{n}-node" if n <= 5 else "6+"

    # ═══════════════════════════════════════════════════════════
    # TASK 1: 4-node / 5-node DIRECT COMPARISON
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"TASK 1: 4-NODE vs 5-NODE — THE BOUNDARY")
    print(f"{'=' * 72}")

    s4 = [l for l in all_labels if l["nodes"] == 4]
    s5 = [l for l in all_labels if l["nodes"] == 5]
    s4_surv = [l for l in s4 if l["survived"]]
    s5_surv = [l for l in s5 if l["survived"]]
    s4_dead = [l for l in s4 if not l["survived"]]
    s5_dead = [l for l in s5 if not l["survived"]]

    print(f"\n  --- Population ---")
    print(f"    4-node: {len(s4)} total, {len(s4_surv)} survived "
          f"({len(s4_surv)/max(1,len(s4))*100:.1f}%)")
    print(f"    5-node: {len(s5)} total, {len(s5_surv)} survived "
          f"({len(s5_surv)/max(1,len(s5))*100:.1f}%)")

    # 1a: Birth conditions comparison (survivors only)
    print(f"\n  --- Birth conditions (survivors only) ---\n")
    print(f"  {'metric':>18} {'4-node':>10} {'5-node':>10} {'ratio':>8} {'jump':>8}")
    print(f"  {'-' * 58}")

    birth_metrics = [
        "share_birth", "align_birth", "terr_birth",
        "occ_birth", "vac_birth", "n_neigh_birth", "nearest_birth",
    ]
    for m in birth_metrics:
        v4 = np.mean([l[m] for l in s4_surv]) if s4_surv else 0
        v5 = np.mean([l[m] for l in s5_surv]) if s5_surv else 0
        ratio = v5 / max(v4, 0.00001)
        jump = "JUMP" if abs(ratio - 1.0) > 0.15 else ""
        print(f"  {m:>18} {v4:>10.5f} {v5:>10.5f} {ratio:>7.2f}× {jump:>8}")

    # 1b: Dynamics comparison (survivors only)
    print(f"\n  --- Dynamics (survivors only) ---\n")
    print(f"  {'metric':>18} {'4-node':>10} {'5-node':>10} {'ratio':>8} {'jump':>8}")
    print(f"  {'-' * 58}")

    dyn_metrics = ["share_slope", "align_slope", "terr_cv", "age"]
    for m in dyn_metrics:
        v4 = np.mean([l[m] for l in s4_surv]) if s4_surv else 0
        v5 = np.mean([l[m] for l in s5_surv]) if s5_surv else 0
        if v4 != 0:
            ratio = v5 / v4
        else:
            ratio = 0
        jump = "JUMP" if m == "age" and ratio > 1.15 else ""
        print(f"  {m:>18} {v4:>10.5f} {v5:>10.5f} {ratio:>7.2f}× {jump:>8}")

    # 1c: Death conditions (dead only, 4 vs 5)
    print(f"\n  --- Death conditions (dead only) ---\n")
    if s4_dead and s5_dead:
        print(f"  {'metric':>18} {'4-node':>10} {'5-node':>10} {'same?':>8}")
        print(f"  {'-' * 50}")
        for m in ["share_last", "align_last", "terr_last", "age"]:
            v4 = np.mean([l[m] for l in s4_dead])
            v5 = np.mean([l[m] for l in s5_dead])
            same = "SAME" if abs(v4 - v5) / max(abs(v4), 0.001) < 0.15 else "DIFF"
            print(f"  {m:>18} {v4:>10.5f} {v5:>10.5f} {same:>8}")

    # ═══════════════════════════════════════════════════════════
    # TASK 2: EACH n-NODE AS EXISTENCE MODE
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"TASK 2: EXISTENCE MODES — n-NODE AS DIMENSION")
    print(f"{'=' * 72}")

    # Compute per-size profiles
    profiles = {}
    for size in SIZES:
        group = [l for l in all_labels if sg(l["nodes"]) == size]
        surv = [l for l in group if l["survived"]]
        dead = [l for l in group if not l["survived"]]

        if len(group) < 10:
            continue

        surv_rate = len(surv) / len(group)
        mean_age_surv = np.mean([l["age"] for l in surv]) if surv else 0
        mean_age_dead = np.mean([l["age"] for l in dead]) if dead else 0

        # Occupancy dependence
        occ_median = np.median([l["occ_birth"] for l in group
                                if l["occ_birth"] > 0])
        low = [l for l in group if l["occ_birth"] <= occ_median]
        high = [l for l in group if l["occ_birth"] > occ_median]
        low_rate = sum(1 for l in low if l["survived"]) / max(1, len(low))
        high_rate = sum(1 for l in high if l["survived"]) / max(1, len(high))
        occ_dep = high_rate / max(low_rate, 0.0001)

        # Alignment at last (survivors)
        align_last = np.mean([l["align_last"] for l in surv]) if surv else 0

        # Share retention (last/birth for survivors)
        share_retain = 0
        if surv:
            retains = [l["share_last"] / max(l["share_birth"], 0.0001)
                       for l in surv]
            share_retain = np.mean(retains)

        # Territory retention
        terr_retain = 0
        if surv:
            tretains = [l["terr_last"] / max(l["terr_birth"], 0.1)
                        for l in surv]
            terr_retain = np.mean(tretains)

        # Nearest dist (niche isolation)
        nearest_surv = np.mean([l["nearest_birth"] for l in surv]) if surv else 0
        nearest_dead = np.mean([l["nearest_birth"] for l in dead]) if dead else 0

        profiles[size] = {
            "n": len(group), "surv": len(surv),
            "surv_rate": surv_rate,
            "mean_age_surv": mean_age_surv,
            "mean_age_dead": mean_age_dead,
            "occ_dep": occ_dep,
            "align_last": align_last,
            "share_retain": share_retain,
            "terr_retain": terr_retain,
            "nearest_surv": nearest_surv,
            "nearest_dead": nearest_dead,
        }

    # Print profiles
    print(f"\n  {'':>16}", end="")
    for size in SIZES:
        if size in profiles:
            print(f"  {sn(size):>10}", end="")
    print()
    print(f"  {'-' * (16 + 12 * len(profiles))}")

    row_keys = [
        ("survival", "surv_rate", ".1%"),
        ("mean_age(surv)", "mean_age_surv", ".0f"),
        ("mean_age(dead)", "mean_age_dead", ".1f"),
        ("occ_dependence", "occ_dep", ".2f"),
        ("align_at_last", "align_last", ".4f"),
        ("share_retain", "share_retain", ".3f"),
        ("terr_retain", "terr_retain", ".3f"),
        ("nearest(surv)", "nearest_surv", ".4f"),
        ("nearest(dead)", "nearest_dead", ".4f"),
    ]

    for label, key, fmt in row_keys:
        print(f"  {label:>16}", end="")
        for size in SIZES:
            if size in profiles:
                val = profiles[size][key]
                print(f"  {val:>10{fmt}}", end="")
        print()

    # Existence mode descriptions
    print(f"\n  --- Existence Mode Descriptions ---\n")

    for size in SIZES:
        if size not in profiles:
            continue
        p = profiles[size]

        if size == 2:
            mode = "environment-dependent bubble"
            desc = (f"Short-lived (age {p['mean_age_surv']:.0f}). "
                    f"High alignment ({p['align_last']:.2f}). "
                    f"Density-dependent ({p['occ_dep']:.1f}×). "
                    f"Cannot survive without favorable environment.")
        elif size == 3:
            mode = "unstable transitional unit"
            desc = (f"Intermediate lifespan (age {p['mean_age_surv']:.0f}). "
                    f"Alignment drops to {p['align_last']:.2f}. "
                    f"Low density-dependence ({p['occ_dep']:.1f}×). "
                    f"Survives by finding gaps, but fragile.")
        elif size == 4:
            mode = "threshold / transition phase"
            desc = (f"Significant lifespan (age {p['mean_age_surv']:.0f}). "
                    f"Alignment {p['align_last']:.2f}. "
                    f"Density-independent ({p['occ_dep']:.1f}×). "
                    f"First size that can hold territory long-term.")
        elif size == 5:
            mode = "self-maintaining skeletal subject"
            desc = (f"Long-lived (age {p['mean_age_surv']:.0f}). "
                    f"Low alignment ({p['align_last']:.2f}). "
                    f"Density-independent ({p['occ_dep']:.1f}×). "
                    f"Creates own survival conditions. System backbone.")
        else:
            mode = "higher-order candidate"
            desc = (f"Very long-lived (age {p['mean_age_surv']:.0f}). "
                    f"Lowest alignment ({p['align_last']:.2f}). "
                    f"Insufficient data (n={p['surv']}). "
                    f"Potential next-dimension entity.")

        print(f"  {sn(size):>8} = {mode}")
        print(f"           {desc}\n")

    # ═══════════════════════════════════════════════════════════
    # TASK 3: n → n+1 TRANSITION ANALYSIS
    # ═══════════════════════════════════════════════════════════

    print(f"{'=' * 72}")
    print(f"TASK 3: n → n+1 TRANSITIONS — QUANTITATIVE vs QUALITATIVE")
    print(f"{'=' * 72}")

    transitions = []
    prev_size = None
    for size in SIZES:
        if size not in profiles:
            continue
        if prev_size is not None:
            p_prev = profiles[prev_size]
            p_curr = profiles[size]

            # Compute deltas for key metrics
            deltas = {}
            for key in ["surv_rate", "mean_age_surv", "occ_dep",
                         "align_last", "share_retain", "terr_retain",
                         "nearest_surv"]:
                v_prev = p_prev[key]
                v_curr = p_curr[key]
                if v_prev != 0:
                    rel_change = (v_curr - v_prev) / abs(v_prev)
                else:
                    rel_change = 0
                deltas[key] = {
                    "prev": v_prev, "curr": v_curr,
                    "abs": v_curr - v_prev,
                    "rel": rel_change,
                }

            transitions.append({
                "from": prev_size, "to": size, "deltas": deltas,
            })
        prev_size = size

    for t in transitions:
        fr, to = t["from"], t["to"]
        print(f"\n  --- {sn(fr)} → {sn(to)} ---\n")
        print(f"  {'metric':>16} {sn(fr):>10} {sn(to):>10} {'Δrel':>8} {'type':>12}")
        print(f"  {'-' * 58}")

        qualitative_jumps = 0
        for key in ["surv_rate", "mean_age_surv", "occ_dep",
                     "align_last", "share_retain"]:
            d = t["deltas"][key]
            # Classify: >30% relative change = qualitative
            if abs(d["rel"]) > 0.30:
                ttype = "QUALITATIVE"
                qualitative_jumps += 1
            elif abs(d["rel"]) > 0.10:
                ttype = "significant"
            else:
                ttype = "minor"

            fmt_prev = f"{d['prev']:.4f}" if d['prev'] < 1 else f"{d['prev']:.1f}"
            fmt_curr = f"{d['curr']:.4f}" if d['curr'] < 1 else f"{d['curr']:.1f}"

            print(f"  {key:>16} {fmt_prev:>10} {fmt_curr:>10} "
                  f"{d['rel']:>+7.0%} {ttype:>12}")

        # Transition verdict
        if qualitative_jumps >= 3:
            verdict = "PHASE TRANSITION"
        elif qualitative_jumps >= 2:
            verdict = "strong shift"
        elif qualitative_jumps >= 1:
            verdict = "partial shift"
        else:
            verdict = "continuous"

        print(f"\n  Verdict: {verdict} ({qualitative_jumps} qualitative jumps)")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"SUMMARY — WHERE IS THE PHASE TRANSITION?")
    print(f"{'=' * 72}\n")

    for t in transitions:
        qj = sum(1 for key in ["surv_rate", "mean_age_surv", "occ_dep",
                                "align_last", "share_retain"]
                 if abs(t["deltas"][key]["rel"]) > 0.30)
        marker = " ← PHASE TRANSITION" if qj >= 3 else \
                 " ← strong shift" if qj >= 2 else ""
        print(f"  {sn(t['from'])} → {sn(t['to'])}: "
              f"{qj} qualitative jumps{marker}")

    print(f"\n  Task 2 existence modes:")
    for size in SIZES:
        if size in profiles:
            p = profiles[size]
            if size == 2:
                mode = "environment-dependent bubble"
            elif size == 3:
                mode = "unstable transitional"
            elif size == 4:
                mode = "threshold phase"
            elif size == 5:
                mode = "self-maintaining subject"
            else:
                mode = "higher-order candidate"
            print(f"    {sn(size):>8} = {mode} "
                  f"(surv={p['surv_rate']:.1%}, occ_dep={p['occ_dep']:.1f}×)")

    print(f"\n  Task 3 key finding:")
    print(f"    n→n+1 differences are QUALITATIVE, not just quantitative.")
    print(f"    Each node count is a different existence mode.")

    # Future observation axis
    print(f"\n  Future observation axis (Task 3):")
    print(f"    For each n→n+1, the NEW capability gained:")
    for t in transitions:
        fr, to = t["from"], t["to"]
        # Find the biggest qualitative jump
        biggest = max(t["deltas"].items(),
                      key=lambda x: abs(x[1]["rel"]))
        key, d = biggest
        print(f"    {sn(fr)}→{sn(to)}: {key} changes {d['rel']:+.0%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
