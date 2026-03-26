#!/usr/bin/env python3
"""
ESDE v8.2 — Subject Size Difference Analysis
================================================
Runs on Ryzen. Outputs text summary only.
Analyzes how node count (2,3,4,5) affects label behavior.

Usage:
  python analyze_size_diff.py --dir diag_v82_baseline
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
    print(f"SUBJECT SIZE DIFFERENCE ANALYSIS")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'='*72}")

    # Collect all labels
    all_labels = []
    for seed, data in seeds.items():
        log = data["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)

        dead_ids = set(e["label_id"] for e in log if e["event"] in ("death", "macro_death"))

        for lid, entries in traj.items():
            births = [e for e in entries if e["event"] == "birth"]
            alives = [e for e in entries if e["event"] in ("birth", "alive")]
            if not births:
                continue

            b = births[0]
            last = alives[-1] if alives else b

            shares = [e["share"] for e in alives]
            alignments = [e.get("alignment", 0) for e in alives]
            torques = [e.get("torque_applied", 0) for e in alives]

            all_labels.append({
                "seed": seed,
                "lid": lid,
                "nodes": b["nodes"],
                "survived": lid not in dead_ids,
                "age": len(alives),
                "share_birth": b["share"],
                "share_mean": np.mean(shares) if shares else 0,
                "share_last": last["share"],
                "alignment_birth": b.get("alignment", 0),
                "alignment_last": last.get("alignment", 0),
                "torque_mean": np.mean(torques) if torques else 0,
                "nearest_birth": b.get("nearest_label_dist", 0),
                "nearest_last": last.get("nearest_label_dist", 0),
                "bin_occ_birth": b.get("bin_occupancy", 0),
                "bin_vac_birth": b.get("bin_vacancy", 0),
                "bin_hist_birth": b.get("bin_history", 0),
                "territory_birth": b.get("territory_links", 0),
                "territory_last": last.get("territory_links", 0),
            })

    # ── 1. Survival by size ──
    print(f"\n{'='*72}")
    print(f"1. SURVIVAL BY NODE COUNT")
    print(f"{'='*72}\n")

    print(f"  {'nodes':>5} {'total':>7} {'surv':>6} {'rate':>8} {'mean_age':>9} {'surv_age':>9}")
    print(f"  {'-'*50}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        rate = len(sv) / max(1, len(group))
        mean_age = np.mean([l["age"] for l in group])
        surv_age = np.mean([l["age"] for l in sv]) if sv else 0
        print(f"  {n:>5} {len(group):>7} {len(sv):>6} {rate:>7.2%} {mean_age:>9.1f} {surv_age:>9.1f}")

    # ── 2. Share by size ──
    print(f"\n{'='*72}")
    print(f"2. SHARE DISTRIBUTION BY NODE COUNT")
    print(f"{'='*72}\n")

    print(f"  {'nodes':>5} {'share_birth':>12} {'share_mean':>12} {'share_last':>12} {'share_last(surv)':>17}")
    print(f"  {'-'*62}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        sb = np.mean([l["share_birth"] for l in group])
        sm = np.mean([l["share_mean"] for l in group])
        sl = np.mean([l["share_last"] for l in group])
        sl_sv = np.mean([l["share_last"] for l in sv]) if sv else 0
        print(f"  {n:>5} {sb:>12.6f} {sm:>12.6f} {sl:>12.6f} {sl_sv:>17.6f}")

    # ── 3. Torque by size ──
    print(f"\n{'='*72}")
    print(f"3. TORQUE (INFLUENCE) BY NODE COUNT")
    print(f"{'='*72}\n")

    print(f"  {'nodes':>5} {'torque_mean':>12} {'torque(surv)':>13} {'torque_ratio':>13}")
    print(f"  {'-'*48}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        dead = [l for l in group if not l["survived"]]
        t_all = np.mean([l["torque_mean"] for l in group])
        t_sv = np.mean([l["torque_mean"] for l in sv]) if sv else 0
        t_dead = np.mean([l["torque_mean"] for l in dead]) if dead else 0
        ratio = t_sv / max(t_dead, 0.00001)
        print(f"  {n:>5} {t_all:>12.6f} {t_sv:>13.6f} {ratio:>13.2f}×")

    # ── 4. Isolation by size ──
    print(f"\n{'='*72}")
    print(f"4. ISOLATION (NEAREST_DIST) BY NODE COUNT")
    print(f"{'='*72}\n")

    print(f"  {'nodes':>5} {'near_birth':>11} {'near(surv)':>12} {'near(dead)':>12} {'ratio':>8}")
    print(f"  {'-'*50}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        dead = [l for l in group if not l["survived"]]
        nb = np.mean([l["nearest_birth"] for l in group])
        ns = np.mean([l["nearest_birth"] for l in sv]) if sv else 0
        nd = np.mean([l["nearest_birth"] for l in dead]) if dead else 0
        r = ns / max(nd, 0.001)
        print(f"  {n:>5} {nb:>11.4f} {ns:>12.4f} {nd:>12.4f} {r:>7.2f}×")

    # ── 5. Territory by size ──
    print(f"\n{'='*72}")
    print(f"5. TERRITORY (LINKS) BY NODE COUNT")
    print(f"{'='*72}\n")

    print(f"  {'nodes':>5} {'terr_birth':>11} {'terr_last':>11} {'terr(surv)':>12} {'terr(dead)':>12}")
    print(f"  {'-'*55}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        dead = [l for l in group if not l["survived"]]
        tb = np.mean([l["territory_birth"] for l in group])
        tl = np.mean([l["territory_last"] for l in group])
        ts = np.mean([l["territory_last"] for l in sv]) if sv else 0
        td = np.mean([l["territory_last"] for l in dead]) if dead else 0
        print(f"  {n:>5} {tb:>11.1f} {tl:>11.1f} {ts:>12.1f} {td:>12.1f}")

    # ── 6. Occupancy by size ──
    print(f"\n{'='*72}")
    print(f"6. PHASE SPACE OCCUPANCY BY NODE COUNT")
    print(f"{'='*72}\n")

    print(f"  {'nodes':>5} {'occ_birth':>10} {'vac_birth':>10} {'occ(surv)':>11} {'occ(dead)':>11}")
    print(f"  {'-'*50}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        dead = [l for l in group if not l["survived"]]
        ob = np.mean([l["bin_occ_birth"] for l in group])
        vb = np.mean([l["bin_vac_birth"] for l in group])
        os = np.mean([l["bin_occ_birth"] for l in sv]) if sv else 0
        od = np.mean([l["bin_occ_birth"] for l in dead]) if dead else 0
        print(f"  {n:>5} {ob:>10.6f} {vb:>10.4f} {os:>11.6f} {od:>11.6f}")

    # ── 7. Size transition: do survivors change size over time? ──
    print(f"\n{'='*72}")
    print(f"7. AGE-SIZE CROSS-TAB (survivors only)")
    print(f"{'='*72}\n")

    surv = [l for l in all_labels if l["survived"]]
    age_bins = [(1,5), (5,10), (10,20), (20,40), (40,80), (80,201)]
    print(f"  {'age':>8}", end="")
    for n in [2,3,4,5]:
        print(f"  {f'{n}-node':>8}", end="")
    print()
    print(f"  {'-'*42}")
    for lo, hi in age_bins:
        in_bin = [l for l in surv if lo <= l["age"] < hi]
        print(f"  {f'{lo}-{hi}':>8}", end="")
        for n in [2,3,4,5]:
            c = sum(1 for l in in_bin if l["nodes"] == n)
            print(f"  {c:>8}", end="")
        print()

    # ── 8. Key question: is there a qualitative difference? ──
    print(f"\n{'='*72}")
    print(f"8. QUALITATIVE DIFFERENCE: 5-node vs 2-node survivors")
    print(f"{'='*72}\n")

    sv5 = [l for l in surv if l["nodes"] == 5]
    sv2 = [l for l in surv if l["nodes"] == 2]

    if sv5 and sv2:
        metrics = [
            ("survival rate", None, None),  # already shown
            ("mean age", np.mean([l["age"] for l in sv5]), np.mean([l["age"] for l in sv2])),
            ("share_mean", np.mean([l["share_mean"] for l in sv5]), np.mean([l["share_mean"] for l in sv2])),
            ("torque_mean", np.mean([l["torque_mean"] for l in sv5]), np.mean([l["torque_mean"] for l in sv2])),
            ("nearest_birth", np.mean([l["nearest_birth"] for l in sv5]), np.mean([l["nearest_birth"] for l in sv2])),
            ("territory_last", np.mean([l["territory_last"] for l in sv5]), np.mean([l["territory_last"] for l in sv2])),
            ("alignment_last", np.mean([l["alignment_last"] for l in sv5]), np.mean([l["alignment_last"] for l in sv2])),
            ("bin_occ_birth", np.mean([l["bin_occ_birth"] for l in sv5]), np.mean([l["bin_occ_birth"] for l in sv2])),
        ]

        print(f"  {'metric':>18} {'5-node':>10} {'2-node':>10} {'ratio':>8}")
        print(f"  {'-'*50}")
        for name, v5, v2 in metrics:
            if v5 is not None and v2 is not None:
                r = v5 / max(v2, 0.00001)
                print(f"  {name:>18} {v5:>10.4f} {v2:>10.4f} {r:>7.2f}×")

    print(f"\n  5-node survivors: {len(sv5)}")
    print(f"  2-node survivors: {len(sv2)}")

    # ── 9. Summary ──
    print(f"\n{'='*72}")
    print(f"SUMMARY")
    print(f"{'='*72}")
    print(f"\n  Total labels: {len(all_labels)}")
    print(f"  Total survivors: {sum(1 for l in all_labels if l['survived'])}")
    for n in sorted(set(l["nodes"] for l in all_labels)):
        group = [l for l in all_labels if l["nodes"] == n]
        sv = [l for l in group if l["survived"]]
        print(f"  {n}-node: {len(group)} total, {len(sv)} survived ({len(sv)/max(1,len(group))*100:.1f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
