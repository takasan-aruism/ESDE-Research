#!/usr/bin/env python3
"""
ESDE v9.6 — Deep Analysis from Existing Baseline Data
========================================================
Extracts answers to Gemini/GPT requests from per_label CSV
and representative JSONs. No re-execution needed.

Items:
  1. Death spiral patterns (last windows before death)
  2. Emperor-type analysis (largest structural world labels)
  3. Deep familiarity → death causation breakdown
  4. Social-survival threshold analysis
  5. Dead label legacy (what happens after a label dies)
  6. Reciprocal pairs and birth proximity
  7. Archetype cross-tabulation

USAGE:
  python v96_deep_analysis.py --tag short
  python v96_deep_analysis.py --tag long
"""

import csv, json, glob, argparse, math
import numpy as np
from pathlib import Path
from collections import defaultdict


def safe_float(v, d=0.0):
    try: return float(v) if v else d
    except: return d

def safe_int(v, d=0):
    try: return int(v) if v else d
    except: return d


def load_labels(tag):
    rows = []
    for t in ([tag] if tag != "both" else ["short", "long"]):
        base = Path(f"diag_v96_baseline_{t}")
        for fp in sorted(glob.glob(str(base / "labels" / "per_label_seed*.csv"))):
            with open(fp) as f:
                for r in csv.DictReader(f):
                    r["_tag"] = t
                    rows.append(r)
    return rows


def load_representatives(tag):
    reps = []
    for t in ([tag] if tag != "both" else ["short", "long"]):
        base = Path(f"diag_v96_baseline_{t}")
        for fp in sorted(glob.glob(str(base / "representatives" / "seed*_label*.json"))):
            with open(fp) as f:
                data = json.load(f)
                data["_tag"] = t
                data["_file"] = fp
                reps.append(data)
    return reps


def load_windows(tag):
    rows = []
    for t in ([tag] if tag != "both" else ["short", "long"]):
        base = Path(f"diag_v96_baseline_{t}")
        for fp in sorted(glob.glob(str(base / "aggregates" / "per_window_seed*.csv"))):
            with open(fp) as f:
                for r in csv.DictReader(f):
                    r["_tag"] = t
                    rows.append(r)
    return rows


def load_network(tag):
    rows = []
    for t in ([tag] if tag != "both" else ["short", "long"]):
        base = Path(f"diag_v96_baseline_{t}")
        for fp in sorted(glob.glob(str(base / "network" / "fam_edges_seed*.csv"))):
            with open(fp) as f:
                for r in csv.DictReader(f):
                    r["_tag"] = t
                    rows.append(r)
    return rows


def run(tag="short"):
    labels = load_labels(tag)
    reps = load_representatives(tag)
    windows = load_windows(tag)
    edges = load_network(tag)

    if not labels:
        print(f"  No data for tag={tag}")
        return

    print(f"\n{'='*70}")
    print(f"  ESDE v9.6 — DEEP ANALYSIS ({tag})")
    print(f"  {len(labels)} labels, {len(reps)} representatives")
    print(f"{'='*70}")

    # ════════════════════════════════════════════════════════
    # 1. DEATH SPIRAL PATTERNS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  1. DEATH SPIRAL — Last windows before death")
    print(f"{'='*70}\n")

    dead_reps = [r for r in reps if r.get("meta", {}).get("death_w") is not None]
    print(f"  Dead representatives with trajectories: {len(dead_reps)}")

    # Collect last-2-window deltas
    social_deltas = []
    stability_deltas = []
    spread_deltas = []
    fam_deltas = []

    for rep in dead_reps:
        traj = rep.get("trajectory", [])
        if len(traj) < 2:
            continue
        last = traj[-1]
        prev = traj[-2]

        ds = last.get("d_social", 0) - prev.get("d_social", 0)
        dst = last.get("d_stability", 0) - prev.get("d_stability", 0)
        dsp = last.get("d_spread", 0) - prev.get("d_spread", 0)
        df = last.get("d_familiarity", 0) - prev.get("d_familiarity", 0)

        social_deltas.append(ds)
        stability_deltas.append(dst)
        spread_deltas.append(dsp)
        fam_deltas.append(df)

    if social_deltas:
        print(f"\n  Disposition change in final window (dead labels):")
        print(f"    Δsocial:    mean={np.mean(social_deltas):>+7.4f} "
              f"std={np.std(social_deltas):.4f}")
        print(f"    Δstability: mean={np.mean(stability_deltas):>+7.4f} "
              f"std={np.std(stability_deltas):.4f}")
        print(f"    Δspread:    mean={np.mean(spread_deltas):>+7.4f} "
              f"std={np.std(spread_deltas):.4f}")
        print(f"    Δfamil:     mean={np.mean(fam_deltas):>+7.4f} "
              f"std={np.std(fam_deltas):.4f}")

        # Did social drop before death?
        social_dropped = sum(1 for d in social_deltas if d < -0.05)
        social_rose = sum(1 for d in social_deltas if d > 0.05)
        social_flat = len(social_deltas) - social_dropped - social_rose
        print(f"\n    Social before death: dropped={social_dropped} "
              f"rose={social_rose} flat={social_flat}")

    # Show specific death spirals
    print(f"\n  Sample death trajectories:")
    shown = 0
    for rep in dead_reps[:8]:
        traj = rep.get("trajectory", [])
        if len(traj) < 2:
            continue
        lid = rep.get("label_id", "?")
        meta = rep.get("meta", {})
        seed = meta.get("birth_w", "?")

        print(f"\n    Label {lid} (death_w={meta.get('death_w')}, "
              f"lifespan={meta.get('lifespan')}):")
        print(f"    {'w':>4} {'social':>7} {'stabil':>7} "
              f"{'spread':>7} {'famil':>7} {'part':>5}")
        for e in traj[-4:]:  # last 4 windows
            print(f"    {e.get('w','?'):>4} {e.get('d_social',0):>7.3f} "
                  f"{e.get('d_stability',0):>7.3f} "
                  f"{e.get('d_spread',0):>7.4f} "
                  f"{e.get('d_familiarity',0):>7.2f} "
                  f"{e.get('n_partners',0):>5}")
        shown += 1

    # ════════════════════════════════════════════════════════
    # 2. EMPEROR-TYPE ANALYSIS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  2. EMPEROR-TYPE — Largest structural world labels")
    print(f"{'='*70}\n")

    by_st = sorted(labels, key=lambda r: safe_float(r.get("last_st_mean")),
                    reverse=True)
    emperors = by_st[:20]

    alive_emp = sum(1 for e in emperors if e.get("alive") == "True")
    dead_emp = sum(1 for e in emperors if e.get("alive") == "False")
    print(f"  Top 20 by st_mean: alive={alive_emp} dead={dead_emp}")

    emp_lifespans = [safe_int(e.get("lifespan")) for e in emperors]
    emp_partners = [safe_int(e.get("last_partners")) for e in emperors]
    emp_fam = [safe_float(e.get("last_familiarity")) for e in emperors]

    all_lifespans = [safe_int(r.get("lifespan")) for r in labels]
    all_partners = [safe_int(r.get("last_partners")) for r in labels]

    print(f"  Emperor avg lifespan: {np.mean(emp_lifespans):.1f} "
          f"(population: {np.mean(all_lifespans):.1f})")
    print(f"  Emperor avg partners: {np.mean(emp_partners):.1f} "
          f"(population: {np.mean(all_partners):.1f})")
    print(f"  Emperor avg familiarity: {np.mean(emp_fam):.1f}")

    print(f"\n  Emperor details:")
    print(f"  {'seed':>4} {'lid':>5} {'st_m':>6} {'st_s':>6} "
          f"{'social':>7} {'part':>5} {'life':>5} {'status':>6}")
    for e in emperors[:10]:
        status = "ALIVE" if e.get("alive") == "True" else "DEAD"
        print(f"  {e['seed']:>4} {e['label_id']:>5} "
              f"{safe_float(e.get('last_st_mean')):>6.1f} "
              f"{safe_float(e.get('last_st_std')):>6.1f} "
              f"{safe_float(e.get('last_social')):>7.3f} "
              f"{safe_int(e.get('last_partners')):>5} "
              f"{safe_int(e.get('lifespan')):>5} {status:>6}")

    # ════════════════════════════════════════════════════════
    # 3. DEEP FAMILIARITY → DEATH CAUSATION
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  3. WHY DEEP FAMILIARITY → DEATH")
    print(f"{'='*70}\n")

    # Bin labels by familiarity
    fam_bins = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 200)]
    for lo, hi in fam_bins:
        subset = [r for r in labels
                  if lo <= safe_float(r.get("last_familiarity")) < hi]
        if not subset:
            continue
        alive = sum(1 for r in subset if r.get("alive") == "True")
        dead = sum(1 for r in subset if r.get("alive") == "False")
        total = len(subset)
        survival_rate = alive / total * 100 if total > 0 else 0
        avg_partners = np.mean([safe_int(r.get("last_partners")) for r in subset])
        avg_social = np.mean([safe_float(r.get("last_social")) for r in subset])

        print(f"  fam [{lo:>3}-{hi:>3}): n={total:>4} "
              f"alive={alive:>4} ({survival_rate:>5.1f}%) "
              f"avg_partners={avg_partners:>5.1f} avg_social={avg_social:.3f}")

    # Twin-type analysis (partner=1, high familiarity)
    twins = [r for r in labels
             if safe_int(r.get("last_partners")) == 1
             and safe_float(r.get("last_familiarity")) > 30]
    twin_alive = sum(1 for r in twins if r.get("alive") == "True")
    print(f"\n  Twin-type (1 partner, fam>30): {len(twins)} labels, "
          f"alive={twin_alive} ({twin_alive/max(1,len(twins))*100:.0f}%)")

    # Does partner count matter more than depth?
    partner_bins = [(0, 3), (3, 10), (10, 25), (25, 50), (50, 100)]
    print(f"\n  Partner count vs survival:")
    for lo, hi in partner_bins:
        subset = [r for r in labels
                  if lo <= safe_int(r.get("last_partners")) < hi]
        if not subset:
            continue
        alive = sum(1 for r in subset if r.get("alive") == "True")
        total = len(subset)
        sr = alive / total * 100
        avg_fam = np.mean([safe_float(r.get("last_familiarity")) for r in subset])
        print(f"  partners [{lo:>2}-{hi:>2}): n={total:>4} "
              f"survival={sr:>5.1f}% avg_fam={avg_fam:>6.2f}")

    # ════════════════════════════════════════════════════════
    # 4. SOCIAL-SURVIVAL THRESHOLD
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  4. SOCIAL-SURVIVAL THRESHOLD (linear or step?)")
    print(f"{'='*70}\n")

    social_bins = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4),
                   (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8),
                   (0.8, 0.9), (0.9, 1.01)]

    print(f"  {'social':>12} {'n':>5} {'alive':>5} {'surv%':>6} {'bar'}")
    for lo, hi in social_bins:
        subset = [r for r in labels
                  if lo <= safe_float(r.get("last_social")) < hi]
        if not subset:
            continue
        alive = sum(1 for r in subset if r.get("alive") == "True")
        total = len(subset)
        sr = alive / total * 100
        bar = "█" * int(sr / 2)
        print(f"  [{lo:.1f}-{hi:.1f}) {total:>5} {alive:>5} "
              f"{sr:>5.1f}% {bar}")

    # ════════════════════════════════════════════════════════
    # 5. DEAD LABEL LEGACY
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  5. DEAD LABEL LEGACY")
    print(f"{'='*70}\n")

    # Group windows by seed, look at mean_familiarity trend
    # after deaths occur
    by_seed = defaultdict(list)
    for w in windows:
        by_seed[w["seed"]].append(w)

    # For each seed, track if familiarity drops after a death-heavy window
    fam_after_death = []
    fam_no_death = []

    for seed, wlist in by_seed.items():
        wlist.sort(key=lambda x: int(x["window"]))
        for i in range(1, len(wlist)):
            curr = wlist[i]
            prev = wlist[i-1]
            fam_change = safe_float(curr.get("mean_familiarity")) - \
                         safe_float(prev.get("mean_familiarity"))

            # Check if deaths occurred in previous window
            # (deaths_this_window not in CSV, approximate by alive_tracked drop)
            alive_curr = safe_int(curr.get("alive_tracked"))
            alive_prev = safe_int(prev.get("alive_tracked"))
            if alive_prev > alive_curr + 1:  # significant deaths
                fam_after_death.append(fam_change)
            else:
                fam_no_death.append(fam_change)

    if fam_after_death and fam_no_death:
        print(f"  Mean familiarity change after death-heavy windows: "
              f"{np.mean(fam_after_death):>+.3f} (n={len(fam_after_death)})")
        print(f"  Mean familiarity change after normal windows:      "
              f"{np.mean(fam_no_death):>+.3f} (n={len(fam_no_death)})")

    # Do dead labels leave high-familiarity partners behind?
    # Check if labels with high familiarity have dead partners
    dead_set = set()
    for r in labels:
        if r.get("alive") == "False":
            dead_set.add((r["seed"], r["label_id"]))

    # From network edges, find edges pointing to dead labels
    orphan_edges = []
    living_edges = []
    for e in edges:
        target = (e["seed"], e["to"])
        if target in dead_set:
            orphan_edges.append(safe_float(e.get("familiarity")))
        else:
            living_edges.append(safe_float(e.get("familiarity")))

    if orphan_edges:
        print(f"\n  Familiarity edges pointing to dead labels: {len(orphan_edges)}")
        print(f"    mean strength: {np.mean(orphan_edges):.2f}")
        print(f"  Familiarity edges pointing to alive labels: {len(living_edges)}")
        print(f"    mean strength: {np.mean(living_edges):.2f}")
        print(f"  → Dead labels leave {'stronger' if np.mean(orphan_edges) > np.mean(living_edges) else 'weaker'}"
              f" memory traces in survivors")

    # ════════════════════════════════════════════════════════
    # 6. RECIPROCAL PAIRS & BIRTH PROXIMITY
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  6. RECIPROCAL PAIRS & NEW LABEL BIRTH")
    print(f"{'='*70}\n")

    # Track reciprocal pair growth and births
    # From window data
    for seed, wlist in sorted(by_seed.items())[:5]:  # first 5 seeds
        wlist.sort(key=lambda x: int(x["window"]))
        print(f"  Seed {seed}:")
        print(f"    {'win':>4} {'labels':>6} {'recip':>6} {'asymm':>6} "
              f"{'fam_mean':>8}")
        for w in wlist[:10]:  # first 10 windows
            print(f"    {int(w['window']):>4} {int(w['v_labels']):>6} "
                  f"{int(w['reciprocal_pairs']):>6} "
                  f"{int(w['asymmetric_pairs']):>6} "
                  f"{safe_float(w.get('mean_familiarity')):>8.2f}")
        print()

    # ════════════════════════════════════════════════════════
    # 7. ARCHETYPE CROSS-TAB
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  7. ARCHETYPE CROSS-TABULATION")
    print(f"{'='*70}\n")

    # Define archetypes from disposition
    archetypes = defaultdict(list)
    for r in labels:
        s = safe_float(r.get("last_social"))
        f = safe_float(r.get("last_familiarity"))
        p = safe_int(r.get("last_partners"))
        st = safe_float(r.get("last_st_mean"))
        sp = safe_float(r.get("last_spread"))
        alive = r.get("alive") == "True"
        life = safe_int(r.get("lifespan"))

        if st > 80 and p > 30:
            atype = "Emperor"
        elif s > 0.8 and p > 30 and life > 15:
            atype = "Elder"
        elif s > 0.8 and not alive:
            atype = "Fallen Social"
        elif s > 0.5 and alive:
            atype = "Social"
        elif p == 1 and f > 30:
            atype = "Twin"
        elif s < 0.15 and p <= 3:
            atype = "Hermit"
        elif sp < 0.75 and not alive:
            atype = "Focused Dead"
        elif life == 0 and not alive:
            atype = "Stillborn"
        elif alive and life > 20:
            atype = "Survivor"
        else:
            atype = "Other"

        archetypes[atype].append(r)

    print(f"  {'Archetype':>15} {'count':>6} {'alive%':>7} "
          f"{'life':>5} {'social':>7} {'fam':>7} {'part':>5}")
    print(f"  {'-'*58}")

    for atype in ["Emperor", "Elder", "Social", "Survivor",
                   "Other", "Twin", "Hermit", "Focused Dead",
                   "Fallen Social", "Stillborn"]:
        group = archetypes.get(atype, [])
        if not group:
            continue
        n = len(group)
        alive_pct = sum(1 for r in group if r.get("alive") == "True") / n * 100
        avg_life = np.mean([safe_int(r.get("lifespan")) for r in group])
        avg_social = np.mean([safe_float(r.get("last_social")) for r in group])
        avg_fam = np.mean([safe_float(r.get("last_familiarity")) for r in group])
        avg_part = np.mean([safe_int(r.get("last_partners")) for r in group])

        print(f"  {atype:>15} {n:>6} {alive_pct:>6.1f}% "
              f"{avg_life:>5.1f} {avg_social:>7.3f} "
              f"{avg_fam:>7.2f} {avg_part:>5.1f}")

    print(f"\n{'='*70}")
    print(f"  END DEEP ANALYSIS")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.6 Deep Analysis")
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()
    run(tag=args.tag)
