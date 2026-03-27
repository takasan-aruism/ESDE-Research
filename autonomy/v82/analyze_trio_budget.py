#!/usr/bin/env python3
"""
ESDE v8.2 — Trio Local Budget Analysis
==========================================
GPT audit: Trio近傍suppressionの機構切り分け

Q: Trio近傍で新参labelが死にやすいのは、
   Trioが固有の関係作用を持っているからか、
   それともTrioの3 labelが局所share/occupancyを消費して
   単に資源不足を作っているだけか？

1. Trioのshare合計と分布
2. Trio周辺のlocal occupancy vs non-trio領域
3. Trio近傍で生まれたlabelの初期条件
4. Trio近傍で死ぬlabelのshare推移
5. Trio suppressionの説明可能性（share消費で何%説明できるか）

Usage:
  python analyze_trio_budget.py --dir diag_v82_baseline
  python analyze_trio_budget.py --dir diag_v82_alpha0.05
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
    log = data["lifecycle_log"]
    traj = defaultdict(list)
    for e in log:
        traj[e["label_id"]].append(e)

    max_win = max(e["window"] for e in log)

    label_info = {}
    alive_per_win = defaultdict(set)
    share_at = defaultdict(dict)
    territory_at = defaultdict(dict)
    bin_occ_at = defaultdict(dict)
    bin_vac_at = defaultdict(dict)

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
            bin_occ_at[lid][w] = e.get("bin_occupancy", 0)
            bin_vac_at[lid][w] = e.get("bin_vacancy", 0)

    survivors = {lid for lid in label_info if label_info[lid]["died"] > max_win}

    return {
        "label_info": label_info, "alive_per_win": alive_per_win,
        "share_at": share_at, "territory_at": territory_at,
        "bin_occ_at": bin_occ_at, "bin_vac_at": bin_vac_at,
        "survivors": survivors, "max_win": max_win, "traj": traj,
    }


def find_trios(survivors, label_info, threshold=0.2):
    trios = []
    surv_list = sorted(survivors, key=lambda x: label_info[x]["phase_sig"])
    n = len(surv_list)
    for i in range(n):
        a = surv_list[i]
        pa = label_info[a]["phase_sig"]
        for j in range(i + 1, n):
            b = surv_list[j]
            if phase_dist(pa, label_info[b]["phase_sig"]) > threshold:
                continue
            ba, bb = label_info[a]["born"], label_info[b]["born"]
            da, db = label_info[a]["died"], label_info[b]["died"]
            if min(da, db) - max(ba, bb) < 50:
                continue
            for k in range(j + 1, n):
                c = surv_list[k]
                pc = label_info[c]["phase_sig"]
                if phase_dist(pa, pc) > threshold:
                    continue
                if phase_dist(label_info[b]["phase_sig"], pc) > threshold:
                    continue
                bc = label_info[c]["born"]
                dc = label_info[c]["died"]
                if min(da, db, dc) - max(ba, bb, bc) >= 50:
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
    print(f"TRIO LOCAL BUDGET ANALYSIS (GPT directive)")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'=' * 72}")

    PROXIMITY = 0.2

    # ═══════════════════════════════════════════════════════════
    # ACCUMULATORS
    # ═══════════════════════════════════════════════════════════

    # §1 Trio share totals
    trio_share_totals = []         # combined share of 3 members at midpoint
    trio_share_per_member = []     # individual member shares

    # §2 Local occupancy comparison
    trio_region_occ = []           # bin_occupancy in trio regions
    nontrio_region_occ = []        # bin_occupancy in non-trio regions

    # §3 Birth initial conditions near/far from trio
    birth_near = []                # {share, occ, vac, terr, survived}
    birth_far = []

    # §4 Death share trajectory near/far
    death_near_slopes = []         # share slope before death, near trio
    death_far_slopes = []          # share slope before death, far trio
    death_near_final_share = []
    death_far_final_share = []

    # §5 Regression: can local trio share explain survival?
    regression_data = []           # {local_trio_share, local_occ, survived}

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
        traj = sd["traj"]

        if len(survivors) < 3:
            continue

        trios = find_trios(survivors, li)
        if not trios:
            continue

        trio_member_ids = set()
        trio_centroids = []
        for trio in trios:
            phases = [li[m]["phase_sig"] for m in trio]
            centroid = circular_mean(phases)
            trio_centroids.append((centroid, trio))
            trio_member_ids.update(trio)

        def near_any_trio(phase):
            for tc, _ in trio_centroids:
                if phase_dist(phase, tc) < PROXIMITY:
                    return True
            return False

        def local_trio_share(phase, window):
            """Sum of trio member shares within PROXIMITY at given window."""
            total = 0.0
            for tm_id in trio_member_ids:
                if tm_id in li and phase_dist(phase, li[tm_id]["phase_sig"]) < PROXIMITY:
                    total += share_at[tm_id].get(window, 0)
            return total

        # ── §1: Trio share totals ──
        mid_win = 150
        for trio in trios[:50]:
            members = list(trio)
            shares = [share_at[m].get(mid_win, 0) for m in members]
            if all(s > 0 for s in shares):
                trio_share_totals.append(sum(shares))
                trio_share_per_member.extend(shares)

        # ── §2: Local occupancy comparison ──
        # Sample w100-200, every 10th window
        for w in range(100, min(max_win + 1, 201), 10):
            for lid in alive_pw.get(w, set()):
                if lid not in li:
                    continue
                occ = bin_occ_at[lid].get(w, 0)
                if near_any_trio(li[lid]["phase_sig"]):
                    if lid not in trio_member_ids:
                        trio_region_occ.append(occ)
                else:
                    nontrio_region_occ.append(occ)

        # ── §3: Birth initial conditions ──
        for lid, info in li.items():
            if lid in trio_member_ids:
                continue
            if info["born"] <= 10:
                continue

            bw = info["born"]
            near = near_any_trio(info["phase_sig"])
            survived = lid in survivors

            entry = {
                "share": share_at[lid].get(bw, 0),
                "occ": bin_occ_at[lid].get(bw, 0),
                "vac": bin_vac_at[lid].get(bw, 0),
                "terr": territory_at[lid].get(bw, 0),
                "survived": survived,
                "local_trio_share": local_trio_share(info["phase_sig"], bw),
            }
            if near:
                birth_near.append(entry)
            else:
                birth_far.append(entry)

        # ── §4: Death share trajectory ──
        for lid, info in li.items():
            if lid in trio_member_ids:
                continue
            if info["died"] > max_win:
                continue
            if info["born"] <= 10:
                continue

            entries = sorted(traj[lid], key=lambda x: x["window"])
            alive_entries = [e for e in entries if e["event"] in ("birth", "alive")]
            if len(alive_entries) < 3:
                continue

            # Share slope over last 3 entries
            last_shares = [e["share"] for e in alive_entries[-3:]]
            slope = last_shares[-1] - last_shares[0]
            final_share = alive_entries[-1]["share"]

            near = near_any_trio(info["phase_sig"])
            if near:
                death_near_slopes.append(slope)
                death_near_final_share.append(final_share)
            else:
                death_far_slopes.append(slope)
                death_far_final_share.append(final_share)

        # ── §5: Regression data ──
        for lid, info in li.items():
            if lid in trio_member_ids:
                continue
            if info["born"] <= 10:
                continue

            bw = info["born"]
            lts = local_trio_share(info["phase_sig"], bw)
            occ = bin_occ_at[lid].get(bw, 0)
            survived = lid in survivors

            regression_data.append({
                "local_trio_share": lts,
                "local_occ": occ,
                "survived": survived,
            })

        if (seed_idx + 1) % 10 == 0:
            print(f"  ... processed {seed_idx + 1}/{len(seeds)} seeds",
                  flush=True)

    # ═══════════════════════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════════════════════

    # ── §1: Trio share totals ──
    print(f"\n{'=' * 72}")
    print(f"1. TRIO SHARE TOTALS")
    print(f"{'=' * 72}\n")

    if trio_share_totals:
        print(f"  Trio combined share (3 members):")
        print(f"    mean={np.mean(trio_share_totals):.6f}")
        print(f"    median={np.median(trio_share_totals):.6f}")
        print(f"    std={np.std(trio_share_totals):.6f}")
        print(f"    min={min(trio_share_totals):.6f}")
        print(f"    max={max(trio_share_totals):.6f}")
        print(f"    n={len(trio_share_totals)}")

        print(f"\n  Per-member share:")
        print(f"    mean={np.mean(trio_share_per_member):.6f}")

        # What fraction of budget=1 does a trio consume?
        mean_total = np.mean(trio_share_totals)
        print(f"\n  Trio as fraction of budget=1: {mean_total:.4f} "
              f"({mean_total * 100:.2f}%)")

    # ── §2: Local occupancy ──
    print(f"\n{'=' * 72}")
    print(f"2. LOCAL OCCUPANCY: TRIO REGION vs NON-TRIO")
    print(f"{'=' * 72}\n")

    if trio_region_occ and nontrio_region_occ:
        tr_occ = np.mean(trio_region_occ)
        nt_occ = np.mean(nontrio_region_occ)
        print(f"  Trio region (non-members only): {tr_occ:.6f} (n={len(trio_region_occ)})")
        print(f"  Non-trio region:                {nt_occ:.6f} (n={len(nontrio_region_occ)})")
        print(f"  Ratio: {tr_occ / max(nt_occ, 0.000001):.2f}×")
        print(f"\n  → Trio regions are {'MORE' if tr_occ > nt_occ * 1.1 else 'equally'} occupied")

    # ── §3: Birth initial conditions ──
    print(f"\n{'=' * 72}")
    print(f"3. BIRTH CONDITIONS: NEAR TRIO vs FAR")
    print(f"{'=' * 72}\n")

    if birth_near and birth_far:
        print(f"  {'':>20} {'near_trio':>12} {'far':>12} {'ratio':>8}")
        print(f"  {'-' * 56}")

        metrics = [
            ("n", len(birth_near), len(birth_far)),
            ("birth share", np.mean([b["share"] for b in birth_near]),
             np.mean([b["share"] for b in birth_far])),
            ("birth occupancy", np.mean([b["occ"] for b in birth_near]),
             np.mean([b["occ"] for b in birth_far])),
            ("birth vacancy", np.mean([b["vac"] for b in birth_near]),
             np.mean([b["vac"] for b in birth_far])),
            ("birth territory", np.mean([b["terr"] for b in birth_near]),
             np.mean([b["terr"] for b in birth_far])),
            ("local trio share", np.mean([b["local_trio_share"] for b in birth_near]),
             np.mean([b["local_trio_share"] for b in birth_far])),
            ("survival rate",
             sum(1 for b in birth_near if b["survived"]) / max(1, len(birth_near)),
             sum(1 for b in birth_far if b["survived"]) / max(1, len(birth_far))),
        ]
        for name, near_val, far_val in metrics:
            if name == "n":
                print(f"  {name:>20} {near_val:>12} {far_val:>12}")
            else:
                ratio = near_val / max(far_val, 0.000001)
                print(f"  {name:>20} {near_val:>12.6f} {far_val:>12.6f} {ratio:>7.2f}×")

    # ── §4: Death share trajectory ──
    print(f"\n{'=' * 72}")
    print(f"4. DEATH TRAJECTORY: NEAR TRIO vs FAR")
    print(f"{'=' * 72}\n")

    if death_near_slopes and death_far_slopes:
        print(f"  Share slope before death (last 3 windows):")
        print(f"    Near trio: mean={np.mean(death_near_slopes):+.6f} "
              f"(n={len(death_near_slopes)})")
        print(f"    Far:       mean={np.mean(death_far_slopes):+.6f} "
              f"(n={len(death_far_slopes)})")

    if death_near_final_share and death_far_final_share:
        print(f"\n  Final share before death:")
        print(f"    Near trio: mean={np.mean(death_near_final_share):.6f}")
        print(f"    Far:       mean={np.mean(death_far_final_share):.6f}")

        near_fs = np.mean(death_near_final_share)
        far_fs = np.mean(death_far_final_share)
        if near_fs < far_fs * 0.8:
            print(f"    → Near-trio labels die with LESS share (squeezed out)")
        elif near_fs > far_fs * 1.2:
            print(f"    → Near-trio labels die with MORE share (killed despite resources)")
        else:
            print(f"    → Similar final share (same death mechanism)")

    # ── §5: Suppression explanation ──
    print(f"\n{'=' * 72}")
    print(f"5. CAN LOCAL TRIO SHARE EXPLAIN SUPPRESSION?")
    print(f"{'=' * 72}\n")

    if regression_data:
        # Bin by local_trio_share AND local_occ independently
        # Then see which predicts survival better

        # 5a: Local trio share bins
        share_bins = [
            (0.0, 0.001, "zero"),
            (0.001, 0.02, "low"),
            (0.02, 0.05, "medium"),
            (0.05, 1.0, "high"),
        ]
        print(f"  --- 5a. Survival by local trio share ---\n")
        print(f"  {'trio_share':>15} {'total':>6} {'surv':>5} {'rate':>8}")
        print(f"  {'-' * 38}")

        for lo, hi, label in share_bins:
            in_bin = [x for x in regression_data if lo <= x["local_trio_share"] < hi]
            surv = sum(1 for x in in_bin if x["survived"])
            rate = surv / max(1, len(in_bin))
            print(f"  {label:>15} {len(in_bin):>6} {surv:>5} {rate:>8.4f}")

        # 5b: Local occupancy bins
        occ_bins = [
            (0.0, 0.02, "very low"),
            (0.02, 0.05, "low"),
            (0.05, 0.10, "medium"),
            (0.10, 1.0, "high"),
        ]
        print(f"\n  --- 5b. Survival by local occupancy ---\n")
        print(f"  {'occupancy':>15} {'total':>6} {'surv':>5} {'rate':>8}")
        print(f"  {'-' * 38}")

        for lo, hi, label in occ_bins:
            in_bin = [x for x in regression_data if lo <= x["local_occ"] < hi]
            surv = sum(1 for x in in_bin if x["survived"])
            rate = surv / max(1, len(in_bin))
            print(f"  {label:>15} {len(in_bin):>6} {surv:>5} {rate:>8.4f}")

        # 5c: 2×2 split: trio share × occupancy
        print(f"\n  --- 5c. 2×2: trio share × occupancy ---\n")

        med_ts = np.median([x["local_trio_share"] for x in regression_data])
        med_occ = np.median([x["local_occ"] for x in regression_data])
        print(f"  Median trio share: {med_ts:.6f}")
        print(f"  Median occupancy:  {med_occ:.6f}\n")

        cats = {
            "low_ts + low_occ":  {"n": 0, "s": 0},
            "low_ts + high_occ": {"n": 0, "s": 0},
            "high_ts + low_occ": {"n": 0, "s": 0},
            "high_ts + high_occ": {"n": 0, "s": 0},
        }
        for x in regression_data:
            ts_key = "high_ts" if x["local_trio_share"] > med_ts else "low_ts"
            occ_key = "high_occ" if x["local_occ"] > med_occ else "low_occ"
            key = f"{ts_key} + {occ_key}"
            cats[key]["n"] += 1
            if x["survived"]:
                cats[key]["s"] += 1

        print(f"  {'category':>25} {'total':>6} {'surv':>5} {'rate':>8}")
        print(f"  {'-' * 48}")
        for cat, vals in cats.items():
            rate = vals["s"] / max(1, vals["n"])
            print(f"  {cat:>25} {vals['n']:>6} {vals['s']:>5} {rate:>8.4f}")

        # Marginal effect sizes
        low_ts_rate = sum(v["s"] for k, v in cats.items() if "low_ts" in k) / \
                      max(1, sum(v["n"] for k, v in cats.items() if "low_ts" in k))
        high_ts_rate = sum(v["s"] for k, v in cats.items() if "high_ts" in k) / \
                       max(1, sum(v["n"] for k, v in cats.items() if "high_ts" in k))
        low_occ_rate = sum(v["s"] for k, v in cats.items() if "low_occ" in k) / \
                       max(1, sum(v["n"] for k, v in cats.items() if "low_occ" in k))
        high_occ_rate = sum(v["s"] for k, v in cats.items() if "high_occ" in k) / \
                        max(1, sum(v["n"] for k, v in cats.items() if "high_occ" in k))

        ts_effect = low_ts_rate / max(high_ts_rate, 0.0001)
        occ_effect = high_occ_rate / max(low_occ_rate, 0.0001)

        print(f"\n  Marginal rates:")
        print(f"    Low trio share: {low_ts_rate:.4f}  High: {high_ts_rate:.4f}  "
              f"(trio share effect: {ts_effect:.1f}× — low is better)")
        print(f"    Low occupancy:  {low_occ_rate:.4f}  High: {high_occ_rate:.4f}  "
              f"(occupancy effect: {occ_effect:.1f}× — high is better)")

        # ── VERDICT ──
        print(f"\n  --- 5d. VERDICT ---\n")

        if ts_effect > occ_effect * 1.5:
            print(f"  Trio share consumption is the DOMINANT mechanism.")
            print(f"  → Case A: Trio = high-density resource occupation pattern")
        elif occ_effect > ts_effect * 1.5:
            print(f"  Occupancy (non-trio) is the DOMINANT mechanism.")
            print(f"  → Suppression is NOT trio-specific. It's density-driven.")
            print(f"  → Trio share consumption alone does NOT explain suppression")
        elif ts_effect > 1.3 and occ_effect > 1.3:
            print(f"  Both trio share and occupancy contribute.")
            print(f"  → Partial Case A: Trio consumes resources AND density matters")
        else:
            print(f"  Neither factor strongly explains suppression.")
            print(f"  → Possible Case B: Trio has a relation-specific effect")
            print(f"  → Or: death mechanism is not share-mediated")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"SUMMARY")
    print(f"{'=' * 72}")

    if trio_share_totals:
        print(f"\n  Trio budget footprint: {np.mean(trio_share_totals)*100:.2f}% of budget=1")

    if trio_region_occ and nontrio_region_occ:
        print(f"  Trio region occupancy: {np.mean(trio_region_occ):.6f} "
              f"(non-trio: {np.mean(nontrio_region_occ):.6f})")

    if birth_near and birth_far:
        near_surv = sum(1 for b in birth_near if b["survived"]) / max(1, len(birth_near))
        far_surv = sum(1 for b in birth_far if b["survived"]) / max(1, len(birth_far))
        print(f"  Birth survival: near={near_surv:.4f} far={far_surv:.4f}")
        near_lts = np.mean([b["local_trio_share"] for b in birth_near])
        far_lts = np.mean([b["local_trio_share"] for b in birth_far])
        print(f"  Local trio share at birth: near={near_lts:.6f} far={far_lts:.6f}")

    if regression_data:
        print(f"\n  Mechanism verdict:")
        print(f"    Trio share effect: {ts_effect:.1f}×")
        print(f"    Occupancy effect:  {occ_effect:.1f}×")
        if ts_effect > occ_effect * 1.5:
            print(f"    → TRIO SHARE is primary (Case A)")
        elif occ_effect > ts_effect * 1.5:
            print(f"    → OCCUPANCY is primary (density-driven)")
        else:
            print(f"    → Both contribute")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
