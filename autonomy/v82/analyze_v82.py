#!/usr/bin/env python3
"""
ESDE v8.2 — 48-Seed Diagnosis Analysis
========================================
Part 1: v8.1d verification (label count parity)
Part 2: Phase A observation (O/H/V correlation with label dynamics)
Part 3: Parameter derivation (α, β for Phase B)

Usage:
  python analyze_v82.py --baseline diag_v82_baseline --compressed diag_v82_compressed
"""

import json, glob, csv, numpy as np, argparse, math
from collections import defaultdict
from pathlib import Path


def load_seeds(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data
    return seeds


def load_csv(d, seed):
    for g in glob.glob(str(Path(d) / f"*seed{seed}*.csv")):
        with open(g) as f:
            return list(csv.DictReader(f))
    return []


def analyze(base_dir, comp_dir):
    base = load_seeds(base_dir)
    comp = load_seeds(comp_dir)
    common = sorted(set(base.keys()) & set(comp.keys()))

    print(f"{'='*72}")
    print(f"ESDE v8.2 — 48-SEED DIAGNOSIS")
    print(f"Baseline: {len(base)} seeds | Compressed: {len(comp)} seeds | Common: {len(common)}")
    print(f"{'='*72}")

    # ==============================================================
    # PART 1: v8.1d VERIFICATION
    # ==============================================================
    print(f"\n{'='*72}")
    print(f"PART 1: v8.1d VERIFICATION (label count parity)")
    print(f"{'='*72}")

    metrics = defaultdict(lambda: {"base": [], "comp": [], "diff": [], "diff_pct": []})

    for seed in common:
        b_csv = load_csv(base_dir, seed)
        c_csv = load_csv(comp_dir, seed)
        if not b_csv or not c_csv:
            continue

        b_sl = b_csv[99:] if len(b_csv) >= 100 else b_csv[50:]
        c_sl = c_csv[99:] if len(c_csv) >= 100 else c_csv[50:]

        def mm(rows, key):
            return np.mean([float(r[key]) for r in rows]) if rows else 0

        for key in ['alive_links', 'stress_intensity', 'total_rplus',
                    'v_labels', 'v_top_share']:
            bv, cv = mm(b_sl, key), mm(c_sl, key)
            metrics[key]["base"].append(bv)
            metrics[key]["comp"].append(cv)
            metrics[key]["diff"].append(cv - bv)
            metrics[key]["diff_pct"].append((cv - bv) / max(abs(bv), 0.001) * 100)

        # Survivors
        b_log, c_log = base[seed]["lifecycle_log"], comp[seed]["lifecycle_log"]
        b_dead = set(e["label_id"] for e in b_log if e["event"] in ("death", "macro_death"))
        c_dead = set(e["label_id"] for e in c_log if e["event"] in ("death", "macro_death"))
        b_all = set(e["label_id"] for e in b_log)
        c_all = set(e["label_id"] for e in c_log)
        bs, cs = len(b_all - b_dead), len(c_all - c_dead)
        metrics["survivors"]["base"].append(bs)
        metrics["survivors"]["comp"].append(cs)
        metrics["survivors"]["diff"].append(cs - bs)
        metrics["survivors"]["diff_pct"].append((cs - bs) / max(bs, 1) * 100)

        # Macro counts
        c_mn = [e for e in c_log if e["event"] == "compressed"]
        c_mn_dead = [e for e in c_log if e["event"] == "macro_death"]
        metrics["macro_created"]["comp"].append(len(c_mn))
        metrics["macro_survived"]["comp"].append(len(c_mn) - len(c_mn_dead))

        # Runtime
        bt = sum(float(r['physics_seconds']) for r in b_csv)
        ct = sum(float(r['physics_seconds']) for r in c_csv)
        metrics["runtime"]["base"].append(bt)
        metrics["runtime"]["comp"].append(ct)
        metrics["runtime"]["diff"].append(ct - bt)
        metrics["runtime"]["diff_pct"].append((ct - bt) / max(bt, 1) * 100)

    print(f"\n  {'metric':>18} {'base':>8} {'comp':>8} {'diff':>8} "
          f"{'std':>7} {'same':>6} {'out':>4}")
    print(f"  {'-'*62}")
    for key in ['alive_links', 'stress_intensity', 'total_rplus',
                'v_labels', 'v_top_share', 'survivors', 'runtime']:
        m = metrics[key]
        if not m["diff"]:
            continue
        dm = np.mean(m["diff"])
        ds = np.std(m["diff"])
        sd = sum(1 for d in m["diff"] if (d > 0) == (dm > 0)) if dm != 0 else len(m["diff"])
        out = sum(1 for d in m["diff"] if abs(d - dm) > 2 * max(ds, 0.001))
        print(f"  {key:>18} {np.mean(m['base']):>8.1f} {np.mean(m['comp']):>8.1f} "
              f"{dm:>+8.2f} {ds:>7.2f} {sd:>3}/{len(m['diff']):<2} {out:>4}")

    # v8.1d key metric
    vl = metrics["v_labels"]["diff_pct"]
    print(f"\n  v_labels diff: mean={np.mean(vl):+.1f}% std={np.std(vl):.1f}%")
    print(f"  v8.1c was: -16.3%")
    print(f"  v8.1d target: ±5%")
    print(f"  Result: {'PASS' if abs(np.mean(vl)) < 5 else 'FAIL'}")

    fewer = sum(1 for d in vl if d < -5)
    same = sum(1 for d in vl if -5 <= d <= 5)
    more = sum(1 for d in vl if d > 5)
    print(f"  Distribution: fewer={fewer} same={same} more={more}")

    if metrics["macro_created"]["comp"]:
        print(f"\n  Macro-nodes: created={np.mean(metrics['macro_created']['comp']):.1f}/seed "
              f"survived={np.mean(metrics['macro_survived']['comp']):.1f}/seed")

    # ==============================================================
    # PART 2: PHASE A OBSERVATION (O/H/V)
    # ==============================================================
    print(f"\n{'='*72}")
    print(f"PART 2: PHASE A OBSERVATION")
    print(f"{'='*72}")

    # 2a. CSV-level O/H/V summary
    print(f"\n--- 2a. Phase Space Summary (baseline, w100-200) ---\n")
    occ_keys = ['occ_max', 'occ_mean', 'occ_nonzero', 'vacancy_mean',
                'history_max', 'history_gini']
    for key in occ_keys:
        vals = []
        for seed in common:
            b_csv = load_csv(base_dir, seed)
            if not b_csv:
                continue
            sl = b_csv[99:] if len(b_csv) >= 100 else b_csv[50:]
            vals.append(np.mean([float(r.get(key, 0)) for r in sl]))
        if vals:
            print(f"  {key:>16}: mean={np.mean(vals):.4f} std={np.std(vals):.4f}")

    # 2b. Vacancy vs birth correlation
    print(f"\n--- 2b. Vacancy vs Birth Correlation ---\n")

    birth_vac = []  # (vacancy at birth bin, survived?)
    for seed in common[:20]:  # sample 20 seeds for speed
        log = base[seed]["lifecycle_log"]
        dead_ids = set(e["label_id"] for e in log if e["event"] == "death")
        for e in log:
            if e["event"] == "birth" and "bin_vacancy" in e:
                birth_vac.append({
                    "vacancy": e["bin_vacancy"],
                    "survived": e["label_id"] not in dead_ids,
                })

    if birth_vac:
        surv = [x for x in birth_vac if x["survived"]]
        dead = [x for x in birth_vac if not x["survived"]]
        sv = np.mean([x["vacancy"] for x in surv]) if surv else 0
        dv = np.mean([x["vacancy"] for x in dead]) if dead else 0
        print(f"  Survivor birth vacancy: {sv:.4f} (n={len(surv)})")
        print(f"  Dead birth vacancy:     {dv:.4f} (n={len(dead)})")
        if sv > 0 and dv > 0:
            print(f"  Ratio: {sv/dv:.2f}×")
            print(f"  → {'Vacancy correlates with survival' if sv > dv * 1.1 else 'Weak or no correlation'}")

    # 2c. History concentration
    print(f"\n--- 2c. History Concentration ---\n")

    gini_vals = []
    nonzero_vals = []
    for seed in common:
        b_csv = load_csv(base_dir, seed)
        if not b_csv:
            continue
        last = b_csv[-1]
        gini_vals.append(float(last.get('history_gini', 0)))
        nonzero_vals.append(int(float(last.get('occ_nonzero', 0))))

    if gini_vals:
        print(f"  History Gini (final): mean={np.mean(gini_vals):.3f} std={np.std(gini_vals):.3f}")
        print(f"  Occupied bins (final): mean={np.mean(nonzero_vals):.1f}/64")
        print(f"  → {'Concentrated' if np.mean(gini_vals) > 0.3 else 'Spread'} occupancy")

    # 2d. Occupancy vs nearest_dist
    print(f"\n--- 2d. Occupancy at Birth vs Survival ---\n")

    birth_occ = []
    for seed in common[:20]:
        log = base[seed]["lifecycle_log"]
        dead_ids = set(e["label_id"] for e in log if e["event"] == "death")
        for e in log:
            if e["event"] == "birth" and "bin_occupancy" in e:
                birth_occ.append({
                    "occ": e["bin_occupancy"],
                    "survived": e["label_id"] not in dead_ids,
                })

    if birth_occ:
        surv = [x for x in birth_occ if x["survived"]]
        dead = [x for x in birth_occ if not x["survived"]]
        so = np.mean([x["occ"] for x in surv]) if surv else 0
        do_ = np.mean([x["occ"] for x in dead]) if dead else 0
        print(f"  Survivor birth occupancy: {so:.6f} (n={len(surv)})")
        print(f"  Dead birth occupancy:     {do_:.6f} (n={len(dead)})")
        if so > 0 and do_ > 0:
            print(f"  Ratio: {do_/so:.2f}× (dead born in MORE occupied bins)")

    # ==============================================================
    # PART 3: PARAMETER DERIVATION (for Phase B)
    # ==============================================================
    print(f"\n{'='*72}")
    print(f"PART 3: PARAMETER DERIVATION")
    print(f"{'='*72}")

    # 3a. α (maturation): age vs survival
    print(f"\n--- 3a. Maturation (α): age vs survival ---\n")

    all_labels = []
    for seed in common:
        log = base[seed]["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)
        dead_ids = set(e["label_id"] for e in log if e["event"] == "death")

        for lid in traj:
            entries = [e for e in traj[lid] if e["event"] in ("birth", "alive")]
            if not entries:
                continue
            all_labels.append({
                "age": len(entries),
                "survived": lid not in dead_ids,
                "nodes": entries[0]["nodes"],
            })

    age_bins = [(1, 5), (5, 10), (10, 20), (20, 40), (40, 80), (80, 201)]
    print(f"  {'age':>8} {'total':>6} {'surv':>5} {'rate':>7}")
    for lo, hi in age_bins:
        in_bin = [l for l in all_labels if lo <= l["age"] < hi]
        sv = [l for l in in_bin if l["survived"]]
        rate = len(sv) / max(1, len(in_bin))
        print(f"  {f'{lo}-{hi}':>8} {len(in_bin):>6} {len(sv):>5} {rate:>7.2%}")

    # 3b. β (rigidity): age vs alignment change
    print(f"\n--- 3b. Rigidity (β): age vs alignment ---\n")

    age_align = defaultdict(list)
    for seed in common[:20]:
        log = base[seed]["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)
        for lid in traj:
            entries = [e for e in traj[lid] if e["event"] in ("birth", "alive")]
            if len(entries) < 5:
                continue
            for i, e in enumerate(entries):
                age_align[i].append(abs(e.get("alignment", 0)))

    print(f"  {'window_age':>10} {'mean_alignment':>15} {'n':>6}")
    for age in [0, 2, 5, 10, 20, 50]:
        if age in age_align and age_align[age]:
            print(f"  {age:>10} {np.mean(age_align[age]):>15.4f} {len(age_align[age]):>6}")

    # 3c. snap death analysis
    print(f"\n--- 3c. Snap Death: share drop at death ---\n")

    death_deltas = []
    for seed in common[:20]:
        log = base[seed]["lifecycle_log"]
        traj = defaultdict(list)
        for e in log:
            traj[e["label_id"]].append(e)
        for lid in traj:
            entries = sorted(traj[lid], key=lambda x: x["window"])
            death = [e for e in entries if e["event"] == "death"]
            alive = [e for e in entries if e["event"] in ("birth", "alive")]
            if death and len(alive) >= 2:
                last_share = alive[-1]["share"]
                prev_share = alive[-2]["share"] if len(alive) >= 2 else last_share
                delta = last_share - prev_share
                death_deltas.append({
                    "delta": delta,
                    "age": len(alive),
                    "share_at_death": death[0].get("share_at_death", last_share),
                })

    if death_deltas:
        deltas = [d["delta"] for d in death_deltas]
        ages = [d["age"] for d in death_deltas]
        print(f"  Share delta before death: mean={np.mean(deltas):+.6f} std={np.std(deltas):.6f}")
        print(f"  Age at death: mean={np.mean(ages):.1f} median={np.median(ages):.0f}")

        # Snap deaths: large negative delta
        snaps = [d for d in death_deltas if d["delta"] < -0.01]
        print(f"  Snap deaths (Δshare < -0.01): {len(snaps)}/{len(death_deltas)} "
              f"({len(snaps)/max(1,len(death_deltas))*100:.0f}%)")
        if snaps:
            snap_ages = [d["age"] for d in snaps]
            print(f"  Snap death age: mean={np.mean(snap_ages):.1f} median={np.median(snap_ages):.0f}")

    # ==============================================================
    # SUMMARY
    # ==============================================================
    print(f"\n{'='*72}")
    print(f"SUMMARY")
    print(f"{'='*72}")

    vl_diff = np.mean(metrics["v_labels"]["diff_pct"])
    print(f"\n  v8.1d verification:")
    print(f"    v_labels diff: {vl_diff:+.1f}% ({'PASS' if abs(vl_diff) < 5 else 'FAIL'})")
    print(f"    alive_links diff: {np.mean(metrics['alive_links']['diff_pct']):+.1f}%")
    print(f"    sI diff: {np.mean(metrics['stress_intensity']['diff_pct']):+.2f}%")

    print(f"\n  Phase A observation:")
    if birth_vac:
        sv = np.mean([x["vacancy"] for x in birth_vac if x["survived"]]) if [x for x in birth_vac if x["survived"]] else 0
        dv = np.mean([x["vacancy"] for x in birth_vac if not x["survived"]]) if [x for x in birth_vac if not x["survived"]] else 0
        print(f"    vacancy-survival correlation: surv={sv:.4f} dead={dv:.4f}")
    if gini_vals:
        print(f"    history concentration (Gini): {np.mean(gini_vals):.3f}")

    print(f"\n  Next steps:")
    if abs(vl_diff) < 5:
        print(f"    v8.1d: PASSED → proceed to Phase B")
    else:
        print(f"    v8.1d: FAILED → investigate before Phase B")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="diag_v82_baseline")
    parser.add_argument("--compressed", default="diag_v82_compressed")
    args = parser.parse_args()
    analyze(args.baseline, args.compressed)
