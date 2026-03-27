#!/usr/bin/env python3
"""
ESDE v8.2 — Subject Size Qualitative Difference Analysis
============================================================
GPT audit directive: 単体サイズ差の非還元的差分を特定する

Q: 5-nodeが持っていて2-nodeが持っていない差分は何か？
   それはoccupancy/vacancy構造とどう関係するか？

1. size別 birth occupancy/vacancy（生存者 vs 死亡者）
2. size別 survival を occupancy帯で分解
3. size別 alignment/territory/share の推移（birth→mid→last）
4. size別 displacement role（× occupancy条件）
5. size別 occupancy dependence の強さ

Usage:
  python analyze_size_quality.py --dir diag_v82_baseline
  python analyze_size_quality.py --dir diag_v82_alpha0.05
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
    print(f"SUBJECT SIZE QUALITATIVE ANALYSIS")
    print(f"Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'=' * 72}")

    # ═══════════════════════════════════════════════════════════
    # COLLECT ALL LABELS
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

        # Build per-window alive set for displacement analysis
        alive_per_win = defaultdict(set)
        label_info_local = {}

        for lid, entries in traj.items():
            births = [e for e in entries if e["event"] == "birth"]
            alives = [e for e in entries if e["event"] in ("birth", "alive")]
            if not births:
                continue

            b = births[0]
            last = alives[-1] if alives else b
            mid_idx = len(alives) // 2
            mid = alives[mid_idx] if alives else b

            for e in alives:
                alive_per_win[e["window"]].add(lid)

            label_info_local[lid] = {
                "phase_sig": b.get("phase_sig", 0),
                "nodes": b["nodes"],
                "born": b["window"],
                "died": max_win + 1 if lid not in dead_ids else
                        next((e["window"] for e in traj[lid]
                              if e["event"] == "death"), max_win + 1),
            }

            shares = [e["share"] for e in alives]
            alignments = [abs(e.get("alignment", 0)) for e in alives]
            territories = [e.get("territory_links", 0) for e in alives]

            all_labels.append({
                "seed": seed,
                "lid": lid,
                "nodes": b["nodes"],
                "survived": lid not in dead_ids,
                "age": len(alives),
                # Birth conditions
                "share_birth": b["share"],
                "occ_birth": b.get("bin_occupancy", 0),
                "vac_birth": b.get("bin_vacancy", 0),
                "terr_birth": b.get("territory_links", 0),
                "align_birth": abs(b.get("alignment", 0)),
                # Mid conditions
                "share_mid": mid["share"],
                "occ_mid": mid.get("bin_occupancy", 0),
                "terr_mid": mid.get("territory_links", 0),
                "align_mid": abs(mid.get("alignment", 0)),
                # Last conditions
                "share_last": last["share"],
                "occ_last": last.get("bin_occupancy", 0),
                "terr_last": last.get("territory_links", 0),
                "align_last": abs(last.get("alignment", 0)),
                # Aggregates
                "share_mean": np.mean(shares) if shares else 0,
                "align_mean": np.mean(alignments) if alignments else 0,
                "terr_mean": np.mean(territories) if territories else 0,
            })

        # Displacement: who kills who? (near-phase death)
        for lid, info in label_info_local.items():
            if info["died"] > max_win:
                continue
            if info["born"] <= 5:
                continue
            dead_phase = info["phase_sig"]
            dead_size = info["nodes"]
            died_win = info["died"]

            # Find nearest alive label at death window
            for other in alive_per_win.get(died_win, set()):
                if other == lid or other not in label_info_local:
                    continue
                oi = label_info_local[other]
                if phase_dist(dead_phase, oi["phase_sig"]) < 0.15:
                    # Found killer candidate
                    # Get occupancy of the dead label at death
                    dead_entries = [e for e in traj[lid]
                                   if e["event"] in ("birth", "alive")]
                    occ_at_death = dead_entries[-1].get("bin_occupancy", 0) \
                        if dead_entries else 0

                    all_labels[-1] if all_labels and all_labels[-1]["lid"] == lid \
                        else None  # not needed, just context

                    # Store displacement event on the dead label entry
                    for lab in all_labels:
                        if lab["lid"] == lid and lab["seed"] == seed:
                            lab["killer_size"] = oi["nodes"]
                            lab["occ_at_death"] = occ_at_death
                            break
                    break

        if (seed_idx + 1) % 10 == 0:
            print(f"  ... processed {seed_idx + 1}/{len(seeds)} seeds",
                  flush=True)

    # Size groups
    SIZES = [2, 3, 4, 5]  # 6+ grouped separately
    SIZE_LABELS = {2: "2-node", 3: "3-node", 4: "4-node", 5: "5-node"}

    def size_group(n):
        if n <= 5:
            return n
        return 6  # 6+

    def size_name(n):
        if n <= 5:
            return f"{n}-node"
        return "6+"

    # ═══════════════════════════════════════════════════════════
    # §1: BIRTH CONDITIONS BY SIZE (survivor vs dead)
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"1. BIRTH CONDITIONS BY SIZE")
    print(f"{'=' * 72}")

    for sg in [2, 3, 4, 5, 6]:
        group = [l for l in all_labels if size_group(l["nodes"]) == sg]
        surv = [l for l in group if l["survived"]]
        dead = [l for l in group if not l["survived"]]

        if len(surv) < 3 or len(dead) < 10:
            continue

        print(f"\n  --- {size_name(sg)} (n={len(group)}, surv={len(surv)}) ---\n")
        print(f"  {'metric':>18} {'survivor':>10} {'dead':>10} {'ratio':>8}")
        print(f"  {'-' * 50}")

        for metric in ["occ_birth", "vac_birth", "share_birth",
                        "align_birth", "terr_birth"]:
            sv = np.mean([l[metric] for l in surv])
            dv = np.mean([l[metric] for l in dead])
            ratio = sv / max(dv, 0.000001)
            print(f"  {metric:>18} {sv:>10.5f} {dv:>10.5f} {ratio:>7.2f}×")

    # ═══════════════════════════════════════════════════════════
    # §2: SURVIVAL BY SIZE × OCCUPANCY BAND
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"2. SURVIVAL BY SIZE × OCCUPANCY BAND")
    print(f"{'=' * 72}\n")

    occ_bands = [
        (0.0, 0.02, "very low"),
        (0.02, 0.05, "low"),
        (0.05, 0.10, "medium"),
        (0.10, 1.0, "high"),
    ]

    # Header
    print(f"  {'occ_band':>12}", end="")
    for sg in [2, 3, 4, 5, 6]:
        print(f"  {size_name(sg):>10}", end="")
    print(f"  {'ALL':>10}")
    print(f"  {'-' * 72}")

    for lo, hi, band_name in occ_bands:
        print(f"  {band_name:>12}", end="")
        for sg in [2, 3, 4, 5, 6]:
            in_band = [l for l in all_labels
                       if size_group(l["nodes"]) == sg
                       and lo <= l["occ_birth"] < hi]
            surv = sum(1 for l in in_band if l["survived"])
            total = len(in_band)
            rate = surv / max(1, total)
            if total >= 5:
                print(f"  {rate:>8.3f}({total:>1})", end="") if total < 100 \
                    else print(f"  {rate:>6.1%}{total:>4}", end="")
            else:
                print(f"  {'---':>10}", end="")
        # ALL sizes
        in_band_all = [l for l in all_labels if lo <= l["occ_birth"] < hi]
        surv_all = sum(1 for l in in_band_all if l["survived"])
        total_all = len(in_band_all)
        rate_all = surv_all / max(1, total_all)
        print(f"  {rate_all:>6.1%}{total_all:>4}")

    # ═══════════════════════════════════════════════════════════
    # §3: TRAJECTORY BY SIZE (birth → mid → last, survivors only)
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"3. SURVIVOR TRAJECTORY BY SIZE (birth → mid → last)")
    print(f"{'=' * 72}")

    for sg in [2, 3, 4, 5, 6]:
        surv = [l for l in all_labels
                if size_group(l["nodes"]) == sg and l["survived"]]
        if len(surv) < 3:
            continue

        print(f"\n  --- {size_name(sg)} survivors (n={len(surv)}, "
              f"mean age={np.mean([l['age'] for l in surv]):.0f}) ---\n")

        for metric_base in ["share", "align", "terr", "occ"]:
            b_key = f"{metric_base}_birth"
            m_key = f"{metric_base}_mid"
            l_key = f"{metric_base}_last"

            # Check keys exist
            if b_key not in surv[0]:
                continue

            b_val = np.mean([l[b_key] for l in surv])
            m_val = np.mean([l[m_key] for l in surv])
            l_val = np.mean([l[l_key] for l in surv])

            direction = "↑" if l_val > b_val * 1.1 else \
                        "↓" if l_val < b_val * 0.9 else "→"

            print(f"  {metric_base:>8}: "
                  f"birth={b_val:.5f}  mid={m_val:.5f}  last={l_val:.5f}  {direction}")

    # ═══════════════════════════════════════════════════════════
    # §4: DISPLACEMENT ROLE × SIZE × OCCUPANCY
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"4. DISPLACEMENT: WHO KILLS WHO? (× occupancy)")
    print(f"{'=' * 72}\n")

    disp_events = [l for l in all_labels if "killer_size" in l]

    if disp_events:
        print(f"  Total displacement events: {len(disp_events)}\n")

        # Size × size matrix
        print(f"  {'dead↓ killer→':>14}", end="")
        for ks in [2, 3, 4, 5, 6]:
            print(f"  {size_name(ks):>8}", end="")
        print()
        print(f"  {'-' * 58}")

        for ds in [2, 3, 4, 5, 6]:
            print(f"  {size_name(ds):>14}", end="")
            for ks in [2, 3, 4, 5, 6]:
                count = sum(1 for e in disp_events
                            if size_group(e["nodes"]) == ds
                            and size_group(e.get("killer_size", 0)) == ks)
                print(f"  {count:>8}", end="")
            print()

        # Displacement by occupancy condition
        print(f"\n  Displacement by occupancy at death:\n")
        med_occ = np.median([e.get("occ_at_death", 0) for e in disp_events
                             if e.get("occ_at_death", 0) > 0])
        print(f"  Median occupancy at death: {med_occ:.6f}\n")

        for occ_label, occ_filter in [
            ("low occ", lambda x: x.get("occ_at_death", 0) <= med_occ),
            ("high occ", lambda x: x.get("occ_at_death", 0) > med_occ),
        ]:
            filtered = [e for e in disp_events if occ_filter(e)]
            big_kills_small = sum(1 for e in filtered
                                  if size_group(e.get("killer_size", 0)) >
                                  size_group(e["nodes"]))
            same = sum(1 for e in filtered
                       if size_group(e.get("killer_size", 0)) ==
                       size_group(e["nodes"]))
            small_kills_big = sum(1 for e in filtered
                                  if size_group(e.get("killer_size", 0)) <
                                  size_group(e["nodes"]))
            total = len(filtered)
            if total > 0:
                print(f"  {occ_label:>10}: n={total}  "
                      f"big>small={big_kills_small / total:.0%}  "
                      f"same={same / total:.0%}  "
                      f"small>big={small_kills_big / total:.0%}")

    # ═══════════════════════════════════════════════════════════
    # §5: OCCUPANCY DEPENDENCE BY SIZE
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"5. OCCUPANCY DEPENDENCE BY SIZE")
    print(f"{'=' * 72}\n")

    print(f"  How much does occupancy matter for each size?\n")

    print(f"  {'size':>8} {'low_occ_surv':>14} {'high_occ_surv':>15} "
          f"{'occ_effect':>12} {'n_low':>7} {'n_high':>7}")
    print(f"  {'-' * 68}")

    occ_median = np.median([l["occ_birth"] for l in all_labels
                            if l["occ_birth"] > 0])

    occ_effects = {}
    for sg in [2, 3, 4, 5, 6]:
        group = [l for l in all_labels if size_group(l["nodes"]) == sg]
        low = [l for l in group if l["occ_birth"] <= occ_median]
        high = [l for l in group if l["occ_birth"] > occ_median]

        if len(low) < 10 or len(high) < 10:
            print(f"  {size_name(sg):>8} {'---':>14} {'---':>15}")
            continue

        low_rate = sum(1 for l in low if l["survived"]) / len(low)
        high_rate = sum(1 for l in high if l["survived"]) / len(high)
        effect = high_rate / max(low_rate, 0.0001)
        occ_effects[sg] = effect

        print(f"  {size_name(sg):>8} {low_rate:>14.4f} {high_rate:>15.4f} "
              f"{effect:>11.1f}× {len(low):>7} {len(high):>7}")

    # Interpretation
    if occ_effects:
        print(f"\n  Interpretation:")
        most_dependent = max(occ_effects, key=occ_effects.get)
        least_dependent = min(occ_effects, key=occ_effects.get)

        print(f"    Most occ-dependent:  {size_name(most_dependent)} "
              f"({occ_effects[most_dependent]:.1f}×)")
        print(f"    Least occ-dependent: {size_name(least_dependent)} "
              f"({occ_effects[least_dependent]:.1f}×)")

        if occ_effects.get(5, 0) < occ_effects.get(2, 999):
            print(f"\n    → 5-node is LESS density-dependent than 2-node")
            print(f"    → 5-node can survive in low-density environments")
            print(f"    → This IS a qualitative difference (not just more of the same)")
        else:
            print(f"\n    → All sizes are similarly density-dependent")
            print(f"    → Size advantage is quantitative, not qualitative")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"SUMMARY — QUALITATIVE SIZE DIFFERENCES")
    print(f"{'=' * 72}")

    for sg in [2, 3, 4, 5, 6]:
        surv = [l for l in all_labels
                if size_group(l["nodes"]) == sg and l["survived"]]
        dead = [l for l in all_labels
                if size_group(l["nodes"]) == sg and not l["survived"]]
        total = len(surv) + len(dead)
        if total < 10:
            continue

        rate = len(surv) / total
        mean_age = np.mean([l["age"] for l in surv]) if surv else 0
        occ_dep = occ_effects.get(sg, 0)

        print(f"\n  {size_name(sg)}:")
        print(f"    survival={rate:.2%} ({len(surv)}/{total})  "
              f"mean_age={mean_age:.0f}  occ_dep={occ_dep:.1f}×")

        if surv:
            print(f"    share: birth={np.mean([l['share_birth'] for l in surv]):.5f} "
                  f"→ last={np.mean([l['share_last'] for l in surv]):.5f}")
            print(f"    align: birth={np.mean([l['align_birth'] for l in surv]):.4f} "
                  f"→ last={np.mean([l['align_last'] for l in surv]):.4f}")
            print(f"    terr:  birth={np.mean([l['terr_birth'] for l in surv]):.1f} "
                  f"→ last={np.mean([l['terr_last'] for l in surv]):.1f}")

    print(f"\n  Key question: What does 5-node have that 2-node doesn't?")
    if occ_effects:
        dep_2 = occ_effects.get(2, 0)
        dep_5 = occ_effects.get(5, 0)
        if dep_5 < dep_2 * 0.7:
            print(f"    → 5-node is less density-dependent ({dep_5:.1f}× vs {dep_2:.1f}×)")
            print(f"    → 5-node creates its own survival conditions")
            print(f"    → This is a NON-REDUCIBLE difference")
        elif dep_5 > dep_2 * 1.3:
            print(f"    → 5-node is MORE density-dependent ({dep_5:.1f}× vs {dep_2:.1f}×)")
            print(f"    → 5-node succeeds BECAUSE of density, not despite it")
        else:
            print(f"    → Similar density dependence ({dep_5:.1f}× vs {dep_2:.1f}×)")
            print(f"    → Difference may be in alignment, territory, or share dynamics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="diag_v82_baseline")
    args = parser.parse_args()
    main(args.dir)
