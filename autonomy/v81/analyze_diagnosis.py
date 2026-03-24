#!/usr/bin/env python3
"""
ESDE v8.1c — 48-Seed Compression Diagnosis Analysis
=====================================================
GPT Audit Requirements:
  - 9 observation targets
  - Distribution analysis (not just means)
  - Seed-level diff direction count
  - Outlier detection
  - Root cause separation (A/B/C/D)

Usage:
  python analyze_diagnosis.py --baseline diag_baseline --compressed diag_compressed
"""

import json, glob, csv, numpy as np, argparse, math
from collections import defaultdict
from pathlib import Path


def load_seed_data(directory):
    """Load all seed results from a directory."""
    seeds = {}
    for g in sorted(glob.glob(str(Path(directory) / "*_detail.json"))):
        with open(g) as f:
            d = json.load(f)
        if d.get("lifecycle_log"):
            seed = d["meta"]["seed"]
            seeds[seed] = d
    return seeds


def csv_summary(directory, seed):
    """Load CSV and compute per-phase summaries."""
    for g in glob.glob(str(Path(directory) / f"*seed{seed}*.csv")):
        with open(g) as f:
            rows = list(csv.DictReader(f))
        return rows
    return []


def analyze(baseline_dir, compressed_dir):
    base = load_seed_data(baseline_dir)
    comp = load_seed_data(compressed_dir)

    common_seeds = sorted(set(base.keys()) & set(comp.keys()))
    print(f"{'='*72}")
    print(f"ESDE v8.1c — 48-SEED COMPRESSION DIAGNOSIS")
    print(f"Baseline seeds: {len(base)}")
    print(f"Compressed seeds: {len(comp)}")
    print(f"Common seeds: {len(common_seeds)}")
    print(f"{'='*72}")

    # ================================================================
    # 1. Per-seed metrics extraction
    # ================================================================
    metrics = defaultdict(lambda: {"base": [], "comp": [], "diff": [], "diff_pct": []})

    for seed in common_seeds:
        b_csv = csv_summary(baseline_dir, seed)
        c_csv = csv_summary(compressed_dir, seed)
        if not b_csv or not c_csv:
            continue

        # Use w100-200 for stable phase comparison
        b_stable = b_csv[99:] if len(b_csv) >= 100 else b_csv[50:]
        c_stable = c_csv[99:] if len(c_csv) >= 100 else c_csv[50:]

        def mean_metric(rows, key):
            vals = [float(r[key]) for r in rows]
            return np.mean(vals) if vals else 0

        # 9 observation targets
        for key in ['alive_links', 'stress_intensity', 'total_rplus',
                    'v_labels', 'v_top_share', 'v_label_rplus_rate']:
            bv = mean_metric(b_stable, key)
            cv = mean_metric(c_stable, key)
            diff = cv - bv
            diff_pct = diff / max(abs(bv), 0.001) * 100
            metrics[key]["base"].append(bv)
            metrics[key]["comp"].append(cv)
            metrics[key]["diff"].append(diff)
            metrics[key]["diff_pct"].append(diff_pct)

        # Survivor count (from lifecycle log)
        b_log = base[seed]["lifecycle_log"]
        c_log = comp[seed]["lifecycle_log"]
        b_dead = set(e["label_id"] for e in b_log if e["event"] == "death")
        c_dead = set(e["label_id"] for e in c_log if e["event"] == "death")
        b_all = set(e["label_id"] for e in b_log)
        c_all = set(e["label_id"] for e in c_log)
        b_surv = len(b_all - b_dead)
        c_surv = len(c_all - c_dead)
        metrics["survivor_count"]["base"].append(b_surv)
        metrics["survivor_count"]["comp"].append(c_surv)
        metrics["survivor_count"]["diff"].append(c_surv - b_surv)
        metrics["survivor_count"]["diff_pct"].append(
            (c_surv - b_surv) / max(b_surv, 1) * 100)

        # Macro-node counts
        c_compressed = [e for e in c_log if e["event"] == "compressed"]
        c_macro_alive = [e for e in c_log if e["event"] == "macro_alive"]
        c_macro_dead = [e for e in c_log if e["event"] == "macro_death"]
        mn_created = len(c_compressed)
        mn_survived = mn_created - len(c_macro_dead)
        metrics["macro_created"]["base"].append(0)
        metrics["macro_created"]["comp"].append(mn_created)
        metrics["macro_created"]["diff"].append(mn_created)
        metrics["macro_created"]["diff_pct"].append(0)
        metrics["macro_survived"]["base"].append(0)
        metrics["macro_survived"]["comp"].append(mn_survived)
        metrics["macro_survived"]["diff"].append(mn_survived)
        metrics["macro_survived"]["diff_pct"].append(0)

        # Runtime
        b_time = sum(float(r['physics_seconds']) for r in b_csv)
        c_time = sum(float(r['physics_seconds']) for r in c_csv)
        metrics["runtime_seconds"]["base"].append(b_time)
        metrics["runtime_seconds"]["comp"].append(c_time)
        metrics["runtime_seconds"]["diff"].append(c_time - b_time)
        metrics["runtime_seconds"]["diff_pct"].append(
            (c_time - b_time) / max(b_time, 1) * 100)

    # ================================================================
    # 2. Distribution analysis (GPT requirement)
    # ================================================================
    print(f"\n{'='*72}")
    print(f"DISTRIBUTION ANALYSIS — baseline vs compressed (w100-200)")
    print(f"{'='*72}\n")

    print(f"  {'metric':>22} {'base_mean':>10} {'comp_mean':>10} "
          f"{'diff_mean':>10} {'diff_std':>9} {'same_dir':>8} {'outliers':>8}")
    print(f"  {'-'*78}")

    for key in ['alive_links', 'stress_intensity', 'total_rplus',
                'v_labels', 'v_top_share', 'survivor_count',
                'macro_created', 'macro_survived', 'runtime_seconds']:
        m = metrics[key]
        if not m["diff"]:
            continue
        base_mean = np.mean(m["base"])
        comp_mean = np.mean(m["comp"])
        diff_mean = np.mean(m["diff"])
        diff_std = np.std(m["diff"])

        # Same direction: how many seeds show diff in same direction as mean
        if diff_mean > 0:
            same_dir = sum(1 for d in m["diff"] if d > 0)
        elif diff_mean < 0:
            same_dir = sum(1 for d in m["diff"] if d < 0)
        else:
            same_dir = len(m["diff"])
        n_seeds = len(m["diff"])

        # Outliers: > 2 std from mean diff
        outliers = sum(1 for d in m["diff"]
                       if abs(d - diff_mean) > 2 * max(diff_std, 0.001))

        print(f"  {key:>22} {base_mean:>10.2f} {comp_mean:>10.2f} "
              f"{diff_mean:>+10.2f} {diff_std:>9.2f} "
              f"{same_dir:>5}/{n_seeds:<2} {outliers:>8}")

    # ================================================================
    # 3. v_labels deep dive (the main concern)
    # ================================================================
    print(f"\n{'='*72}")
    print(f"v_labels DEEP DIVE — label count reduction analysis")
    print(f"{'='*72}\n")

    vl_diffs = metrics["v_labels"]["diff_pct"]
    print(f"  Label count change (%): "
          f"mean={np.mean(vl_diffs):+.1f}% std={np.std(vl_diffs):.1f}%")
    print(f"  Seeds with FEWER labels:  {sum(1 for d in vl_diffs if d < -5)}/48")
    print(f"  Seeds with SAME labels:   {sum(1 for d in vl_diffs if -5 <= d <= 5)}/48")
    print(f"  Seeds with MORE labels:   {sum(1 for d in vl_diffs if d > 5)}/48")

    # Histogram of diff%
    hist_bins = [(-100,-50), (-50,-30), (-30,-15), (-15,-5), (-5,5),
                 (5,15), (15,30), (30,50), (50,100)]
    print(f"\n  Label count diff% distribution:")
    for lo, hi in hist_bins:
        count = sum(1 for d in vl_diffs if lo <= d < hi)
        bar = '█' * count
        print(f"    {lo:>+4}% to {hi:>+4}%: {bar} ({count})")

    # ================================================================
    # 4. Lifecycle comparison — birth vs death rates
    # ================================================================
    print(f"\n{'='*72}")
    print(f"BIRTH/DEATH RATE COMPARISON (w50-200)")
    print(f"{'='*72}\n")

    birth_diffs = []
    death_diffs = []
    for seed in common_seeds:
        b_csv = csv_summary(baseline_dir, seed)
        c_csv = csv_summary(compressed_dir, seed)
        if not b_csv or not c_csv:
            continue
        b_sl = b_csv[49:min(200, len(b_csv))]
        c_sl = c_csv[49:min(200, len(c_csv))]

        b_born = sum(int(r['v_born']) for r in b_sl)
        c_born = sum(int(r['v_born']) for r in c_sl)
        b_died = sum(int(r['v_died']) for r in b_sl)
        c_died = sum(int(r['v_died']) for r in c_sl)
        birth_diffs.append(c_born - b_born)
        death_diffs.append(c_died - b_died)

    print(f"  Birth diff (compressed - baseline):")
    print(f"    mean={np.mean(birth_diffs):+.1f} std={np.std(birth_diffs):.1f}")
    print(f"    fewer births: {sum(1 for d in birth_diffs if d < 0)}/48")
    print(f"  Death diff (compressed - baseline):")
    print(f"    mean={np.mean(death_diffs):+.1f} std={np.std(death_diffs):.1f}")
    print(f"    fewer deaths: {sum(1 for d in death_diffs if d < 0)}/48")

    if birth_diffs and death_diffs:
        # Is it a birth problem or death problem?
        birth_effect = abs(np.mean(birth_diffs))
        death_effect = abs(np.mean(death_diffs))
        print(f"\n  Birth effect magnitude: {birth_effect:.1f}")
        print(f"  Death effect magnitude: {death_effect:.1f}")
        if birth_effect > death_effect * 1.5:
            print(f"  → BIRTH SUPPRESSION is dominant cause")
        elif death_effect > birth_effect * 1.5:
            print(f"  → EXCESS DEATH is dominant cause")
        else:
            print(f"  → BOTH birth and death are affected")

    # ================================================================
    # 5. Root cause separation (GPT requirement A/B/C/D)
    # ================================================================
    print(f"\n{'='*72}")
    print(f"ROOT CAUSE SEPARATION")
    print(f"{'='*72}\n")

    # A. Share fixation
    print(f"  A. Share fixation hypothesis:")
    ts_diffs = metrics["v_top_share"]["diff_pct"]
    print(f"     top_share change: mean={np.mean(ts_diffs):+.1f}%")
    print(f"     Seeds with higher top_share in compressed: "
          f"{sum(1 for d in ts_diffs if d > 0)}/48")

    # B. Compression timing (only w50 in this test)
    print(f"\n  B. Compression timing:")
    print(f"     This test uses w50 only. w50/w100 comparison from")
    print(f"     equivalence test showed similar final states.")

    # C. Macro-node existence effect
    print(f"\n  C. Macro-node existence effect:")
    mn_created = metrics["macro_created"]["comp"]
    mn_survived = metrics["macro_survived"]["comp"]
    print(f"     Created per seed: mean={np.mean(mn_created):.1f} "
          f"std={np.std(mn_created):.1f}")
    print(f"     Survived per seed: mean={np.mean(mn_survived):.1f} "
          f"std={np.std(mn_survived):.1f}")

    # Correlation: more macro-nodes → more label reduction?
    vl_diff = metrics["v_labels"]["diff"]
    if mn_created and vl_diff and len(mn_created) == len(vl_diff):
        corr = np.corrcoef(mn_created, vl_diff)[0,1]
        print(f"     corr(macro_created, label_diff) = {corr:.3f}")

    # D. R+ / phase partition secondary effects
    print(f"\n  D. R+ / phase partition effects:")
    rp_diffs = metrics["total_rplus"]["diff_pct"]
    print(f"     R+ change: mean={np.mean(rp_diffs):+.1f}% "
          f"std={np.std(rp_diffs):.1f}%")
    print(f"     Seeds with lower R+: {sum(1 for d in rp_diffs if d < -5)}/48")

    # ================================================================
    # 6. Summary
    # ================================================================
    print(f"\n{'='*72}")
    print(f"SUMMARY")
    print(f"{'='*72}\n")

    print(f"  物理層 (alive_links):  "
          f"diff = {np.mean(metrics['alive_links']['diff_pct']):+.1f}%")
    print(f"  動的平衡 (sI):         "
          f"diff = {np.mean(metrics['stress_intensity']['diff_pct']):+.2f}%")
    print(f"  仮想層 (v_labels):     "
          f"diff = {np.mean(metrics['v_labels']['diff_pct']):+.1f}%")
    print(f"  R+ (total_rplus):      "
          f"diff = {np.mean(metrics['total_rplus']['diff_pct']):+.1f}%")
    print(f"  生存者 (survivors):    "
          f"diff = {np.mean(metrics['survivor_count']['diff_pct']):+.1f}%")
    print(f"  速度 (runtime):        "
          f"diff = {np.mean(metrics['runtime_seconds']['diff_pct']):+.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="diag_baseline")
    parser.add_argument("--compressed", default="diag_compressed")
    args = parser.parse_args()
    analyze(args.baseline, args.compressed)
