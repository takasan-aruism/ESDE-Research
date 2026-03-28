#!/usr/bin/env python3
"""
ESDE v8.3 — Collapse Threshold Analysis
==========================================
GPT directive: 動的崩壊がどのように起こるかを追う

Compares A=0.3/0.5/0.7/1.0 at T=100.
Baseline = ../v82/diag_v82_baseline (no wave).

Collapse indicators (GPT §2):
  1. 5-node survival の急減
  2. v_labels 全体の急減
  3. 6+ の消失
  4. share_retain 3相構造の崩壊
  5. occupancy/vacancy 構造差の消失
  6. size間応答差が潰れること
  7. links/label の関係が単純死滅へ移ること

Usage:
  python analyze_v83_collapse.py
"""

import json, glob, csv, argparse, numpy as np, math
from collections import defaultdict, Counter
from pathlib import Path


def load_details(d):
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data
    return seeds


def load_csvs(d):
    csvs = {}
    for g in sorted(glob.glob(str(Path(d) / "*.csv"))):
        with open(g) as f:
            reader = list(csv.DictReader(f))
        fname = Path(g).stem
        for part in fname.split("_"):
            if part.startswith("seed"):
                csvs[int(part[4:])] = reader
                break
    return csvs


def get_phase(bg, base=0.003):
    ratio = bg / base if base > 0 else 1
    if ratio > 1.15:
        return "peak"
    elif ratio < 0.85:
        return "trough"
    return "mid"


def build_labels(data):
    log = data["lifecycle_log"]
    traj = defaultdict(list)
    for e in log:
        traj[e["label_id"]].append(e)
    max_win = max(e["window"] for e in log)
    dead_ids = set(e["label_id"] for e in log
                   if e["event"] in ("death", "macro_death"))
    labels = {}
    for lid, entries in traj.items():
        births = [e for e in entries if e["event"] == "birth"]
        alives = [e for e in entries if e["event"] in ("birth", "alive")]
        if not births:
            continue
        b = births[0]
        last = alives[-1] if alives else b
        labels[lid] = {
            "nodes": b["nodes"],
            "born": b["window"],
            "died": max_win + 1 if lid not in dead_ids else
                    next((e["window"] for e in traj[lid]
                          if e["event"] == "death"), max_win + 1),
            "survived": lid not in dead_ids,
            "age": len(alives),
            "share_birth": b["share"],
            "share_last": last["share"],
        }
    return labels, max_win


def analyze_condition(d, csv_dir=None):
    """Analyze one condition. Returns summary dict."""
    seeds = load_details(d)
    csvs = load_csvs(csv_dir or d)

    if not seeds:
        return None

    # CSV-level
    all_links = []; all_vl = []
    peak_vl = []; trough_vl = []
    peak_links = []; trough_links = []

    for seed, rows in csvs.items():
        for r in rows[99:]:
            links = int(r["alive_links"])
            vl = int(r["v_labels"])
            bg = float(r.get("bg_prob_effective", 0.003))
            all_links.append(links)
            all_vl.append(vl)
            phase = get_phase(bg)
            if phase == "peak":
                peak_links.append(links); peak_vl.append(vl)
            elif phase == "trough":
                trough_links.append(links); trough_vl.append(vl)

    # Label-level
    size_total = Counter()
    size_surv = Counter()
    retain_by_size = defaultdict(list)
    peak_surv_5 = 0; peak_total_5 = 0
    trough_surv_5 = 0; trough_total_5 = 0
    peak_death_by_size = Counter()
    trough_death_by_size = Counter()

    for seed, data in seeds.items():
        labels, max_win = build_labels(data)
        csv_rows = csvs.get(seed, [])
        win_bg = {int(r["window"]): float(r.get("bg_prob_effective", 0.003))
                  for r in csv_rows}

        for lid, info in labels.items():
            sg = min(info["nodes"], 6)
            size_total[sg] += 1
            if info["survived"]:
                size_surv[sg] += 1
                if info["age"] >= 10:
                    ret = info["share_last"] / max(info["share_birth"], 0.0001)
                    retain_by_size[sg].append(ret)

            # 5-node wave response
            if info["nodes"] == 5 and info["born"] > 10:
                born_bg = win_bg.get(info["born"], 0.003)
                bp = get_phase(born_bg)
                if bp == "peak":
                    peak_total_5 += 1
                    if info["survived"]:
                        peak_surv_5 += 1
                elif bp == "trough":
                    trough_total_5 += 1
                    if info["survived"]:
                        trough_surv_5 += 1

            # Death by phase
            if not info["survived"] and info["died"] <= max_win:
                died_bg = win_bg.get(info["died"], 0.003)
                dp = get_phase(died_bg)
                if dp == "peak":
                    peak_death_by_size[sg] += 1
                elif dp == "trough":
                    trough_death_by_size[sg] += 1

    # Compile
    result = {
        "n_seeds": len(seeds),
        "links_mean": np.mean(all_links) if all_links else 0,
        "links_std": np.std(all_links) if all_links else 0,
        "vl_mean": np.mean(all_vl) if all_vl else 0,
        "peak_vl": np.mean(peak_vl) if peak_vl else 0,
        "trough_vl": np.mean(trough_vl) if trough_vl else 0,
        "peak_links": np.mean(peak_links) if peak_links else 0,
        "trough_links": np.mean(trough_links) if trough_links else 0,
    }

    for sg in [2, 3, 4, 5, 6]:
        t = size_total[sg]
        s = size_surv[sg]
        result[f"surv_{sg}"] = s / max(1, t) if t > 0 else 0
        result[f"n_{sg}"] = t
        ret = retain_by_size.get(sg, [])
        result[f"retain_{sg}"] = np.mean(ret) if ret else 0

    result["five_peak_surv"] = peak_surv_5 / max(1, peak_total_5)
    result["five_trough_surv"] = trough_surv_5 / max(1, trough_total_5)
    result["five_wave_ratio"] = (result["five_peak_surv"] /
                                  max(result["five_trough_surv"], 0.0001))

    # Death ratio 2-node
    pd2 = peak_death_by_size.get(2, 0)
    td2 = trough_death_by_size.get(2, 0)
    result["death_ratio_2"] = pd2 / max(td2, 1)

    # Death ratio 5-node
    pd5 = peak_death_by_size.get(5, 0)
    td5 = trough_death_by_size.get(5, 0)
    result["death_ratio_5"] = pd5 / max(td5, 1)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="../v82/diag_v82_baseline")
    args = parser.parse_args()

    conditions = [
        ("baseline", args.baseline),
        ("A=0.3", "diag_v83_wave_A0.3_T100"),
        ("A=0.5", "diag_v83_wave_A0.5_T100"),
        ("A=0.7", "diag_v83_wave_A0.7_T100"),
        ("A=1.0", "diag_v83_wave_A1.0_T100"),
    ]

    results = {}
    for label, d in conditions:
        p = Path(d)
        if not p.exists():
            print(f"  {label}: {d} not found, skipping")
            continue
        print(f"  Processing {label} ({d})...", flush=True)
        r = analyze_condition(d)
        if r:
            results[label] = r

    if not results:
        print("No data found!")
        return

    # ═══════════════════════════════════════════
    # OUTPUT 1: Comparison Table
    # ═══════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"COLLAPSE THRESHOLD SWEEP (T=100)")
    print(f"{'=' * 72}")

    # Physical layer
    print(f"\n--- Physical Layer ---\n")
    print(f"  {'cond':>10} {'links':>7} {'std':>5} {'pk_lnk':>7} {'tr_lnk':>7} {'diff':>6}")
    print(f"  {'-' * 46}")
    for label, r in results.items():
        diff = r["peak_links"] - r["trough_links"]
        print(f"  {label:>10} {r['links_mean']:>7.0f} {r['links_std']:>5.0f} "
              f"{r['peak_links']:>7.0f} {r['trough_links']:>7.0f} {diff:>+6.0f}")

    # Label ecology
    print(f"\n--- Label Ecology ---\n")
    print(f"  {'cond':>10} {'vl':>6} {'pk_vl':>6} {'tr_vl':>6} {'diff':>6}")
    print(f"  {'-' * 42}")
    for label, r in results.items():
        diff = r["peak_vl"] - r["trough_vl"]
        print(f"  {label:>10} {r['vl_mean']:>6.1f} {r['peak_vl']:>6.1f} "
              f"{r['trough_vl']:>6.1f} {diff:>+6.1f}")

    # Survival by size
    print(f"\n--- Survival by Size ---\n")
    print(f"  {'cond':>10}", end="")
    for sg in [2, 3, 4, 5, 6]:
        name = f"{sg}n" if sg < 6 else "6+"
        print(f"  {name:>8}", end="")
    print()
    print(f"  {'-' * 54}")
    for label, r in results.items():
        print(f"  {label:>10}", end="")
        for sg in [2, 3, 4, 5, 6]:
            val = r[f"surv_{sg}"]
            print(f"  {val:>7.1%}", end="")
        print()

    # 5-node wave response
    print(f"\n--- 5-node Wave Response ---\n")
    print(f"  {'cond':>10} {'peak':>8} {'trough':>8} {'ratio':>7}")
    print(f"  {'-' * 36}")
    for label, r in results.items():
        print(f"  {label:>10} {r['five_peak_surv']:>7.1%} "
              f"{r['five_trough_surv']:>7.1%} {r['five_wave_ratio']:>6.2f}×")

    # Share retain
    print(f"\n--- Share Retain (survivors, age>=10) ---\n")
    print(f"  {'cond':>10}", end="")
    for sg in [2, 3, 4, 5, 6]:
        name = f"{sg}n" if sg < 6 else "6+"
        print(f"  {name:>8}", end="")
    print()
    print(f"  {'-' * 54}")
    for label, r in results.items():
        print(f"  {label:>10}", end="")
        for sg in [2, 3, 4, 5, 6]:
            val = r[f"retain_{sg}"]
            if val > 0:
                print(f"  {val:>8.3f}", end="")
            else:
                print(f"  {'---':>8}", end="")
        print()

    # Death ratio (peak/trough)
    print(f"\n--- Death Ratio peak/trough ---\n")
    print(f"  {'cond':>10} {'2-node':>8} {'5-node':>8}")
    print(f"  {'-' * 30}")
    for label, r in results.items():
        print(f"  {label:>10} {r['death_ratio_2']:>7.2f}× {r['death_ratio_5']:>7.2f}×")

    # ═══════════════════════════════════════════
    # COLLAPSE INDICATORS
    # ═══════════════════════════════════════════

    print(f"\n{'=' * 72}")
    print(f"COLLAPSE INDICATORS")
    print(f"{'=' * 72}\n")

    bl = results.get("baseline")
    if not bl:
        print("  No baseline for comparison!")
        return

    for label, r in results.items():
        if label == "baseline":
            continue

        print(f"  --- {label} ---")
        indicators = []

        # 1. 5-node survival drop
        drop_5 = (bl["surv_5"] - r["surv_5"]) / bl["surv_5"]
        if drop_5 > 0.30:
            indicators.append(f"5-node survival -{drop_5:.0%} (SEVERE)")
        elif drop_5 > 0.15:
            indicators.append(f"5-node survival -{drop_5:.0%} (moderate)")
        else:
            indicators.append(f"5-node survival -{drop_5:.0%} (stable)")

        # 2. v_labels drop
        vl_drop = (bl["vl_mean"] - r["vl_mean"]) / bl["vl_mean"]
        if vl_drop > 0.30:
            indicators.append(f"v_labels -{vl_drop:.0%} (SEVERE)")
        elif vl_drop > 0.15:
            indicators.append(f"v_labels -{vl_drop:.0%} (moderate)")
        else:
            indicators.append(f"v_labels -{vl_drop:.0%} (stable)")

        # 3. 6+ survival
        s6 = r["surv_6"]
        n6 = r["n_6"]
        if n6 == 0:
            indicators.append("6+ ABSENT (collapse?)")
        elif s6 < 0.5:
            indicators.append(f"6+ survival {s6:.0%} (SEVERE)")
        else:
            indicators.append(f"6+ survival {s6:.0%} n={n6} (present)")

        # 4. share_retain 3-phase structure
        r4 = r["retain_4"]
        r5 = r["retain_5"]
        r6 = r["retain_6"]
        if r4 > 0 and r5 > 0:
            if r5 < r4 and (r6 == 0 or r6 > r5):
                indicators.append("3-phase structure: INTACT")
            else:
                indicators.append("3-phase structure: DISRUPTED")
        else:
            indicators.append("3-phase structure: insufficient data")

        # 5. size response differentiation
        s2 = r["surv_2"]
        s5 = r["surv_5"]
        if s5 > 0 and s2 < s5:
            diff_ratio = s5 / max(s2, 0.0001)
            if diff_ratio > 10:
                indicators.append(f"size differentiation: STRONG ({diff_ratio:.0f}×)")
            elif diff_ratio > 3:
                indicators.append(f"size differentiation: moderate ({diff_ratio:.0f}×)")
            else:
                indicators.append(f"size differentiation: COLLAPSED ({diff_ratio:.1f}×)")

        # 6. 5-node wave ratio
        wr = r["five_wave_ratio"]
        if wr > 0.85:
            indicators.append(f"5-node wave independence: {wr:.2f}× (maintained)")
        elif wr > 0.60:
            indicators.append(f"5-node wave independence: {wr:.2f}× (degraded)")
        else:
            indicators.append(f"5-node wave independence: {wr:.2f}× (LOST)")

        for ind in indicators:
            print(f"    {ind}")

        # Overall judgment
        severe = sum(1 for i in indicators if "SEVERE" in i or "ABSENT" in i
                     or "COLLAPSED" in i or "LOST" in i)
        if severe >= 3:
            print(f"    → COLLAPSE")
        elif severe >= 1:
            print(f"    → STRESS (partial degradation)")
        else:
            print(f"    → STABLE (ecology intact)")
        print()


if __name__ == "__main__":
    main()
