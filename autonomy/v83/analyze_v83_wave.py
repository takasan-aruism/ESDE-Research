#!/usr/bin/env python3
"""
ESDE v8.3 — External Wave Response Analysis
================================================
Analyzes how label ecology responds to bg_prob wave.

1. Wave sanity: bg_prob oscillation confirmed
2. Physical layer response (links, stress)
3. Label ecology response by wave phase (peak vs trough)
4. Size-specific response: which sizes thrive in boom/bust?
5. Survivor profile under wave vs baseline

Usage:
  python analyze_v83_wave.py \
      --baseline ../v82/diag_v82_baseline \
      --wave diag_v83_wave_A0.3_T50

  For multi-period comparison:
  python analyze_v83_wave.py \
      --baseline ../v82/diag_v82_baseline \
      --wave diag_v83_wave_A0.3_T10 \
      --wave2 diag_v83_wave_A0.3_T50 \
      --wave3 diag_v83_wave_A0.3_T100
"""

import json, glob, csv, argparse, numpy as np, math
from collections import defaultdict, Counter
from pathlib import Path


def load_details(d):
    """Load all detail.json from a directory."""
    seeds = {}
    for g in sorted(glob.glob(str(Path(d) / "*_detail.json"))):
        with open(g) as f:
            data = json.load(f)
        if data.get("lifecycle_log"):
            seeds[data["meta"]["seed"]] = data
    return seeds


def load_csvs(d):
    """Load all CSV from a directory."""
    csvs = {}
    for g in sorted(glob.glob(str(Path(d) / "*.csv"))):
        with open(g) as f:
            reader = list(csv.DictReader(f))
        # Extract seed from filename
        fname = Path(g).stem
        for part in fname.split("_"):
            if part.startswith("seed"):
                seed = int(part[4:])
                csvs[seed] = reader
                break
    return csvs


def get_wave_phase(bg_prob, bg_base=0.003):
    """Classify wave phase. Returns 'peak', 'trough', or 'mid'."""
    if bg_base == 0:
        return "mid"
    ratio = bg_prob / bg_base
    if ratio > 1.15:
        return "peak"
    elif ratio < 0.85:
        return "trough"
    return "mid"


def build_label_data(data):
    """Build per-label info from lifecycle_log."""
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


def analyze_dir(d, label, csv_dir=None):
    """Full analysis of one directory."""
    seeds = load_details(d)
    csvs = load_csvs(csv_dir or d)

    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"  Seeds: {len(seeds)}  Dir: {d}")
    print(f"{'=' * 72}")

    if not seeds:
        print(f"  No detail.json found!")
        return {}

    # ── §1: CSV-level summary ──
    print(f"\n--- 1. Physical Layer (CSV, w100-200) ---\n")

    all_links = []; all_vlabels = []; all_born = []; all_died = []
    all_bg = []
    peak_links = []; trough_links = []
    peak_vlabels = []; trough_vlabels = []

    for seed, rows in csvs.items():
        for r in rows[99:]:  # w100-200
            links = int(r["alive_links"])
            vl = int(r["v_labels"])
            born = int(r["v_born"])
            died = int(r["v_died"])
            bg = float(r.get("bg_prob_effective", 0.003))

            all_links.append(links)
            all_vlabels.append(vl)
            all_born.append(born)
            all_died.append(died)
            all_bg.append(bg)

            phase = get_wave_phase(bg)
            if phase == "peak":
                peak_links.append(links); peak_vlabels.append(vl)
            elif phase == "trough":
                trough_links.append(links); trough_vlabels.append(vl)

    print(f"  bg_prob range: {min(all_bg):.5f} - {max(all_bg):.5f}")
    print(f"  alive_links: mean={np.mean(all_links):.0f} std={np.std(all_links):.0f}")
    print(f"  v_labels:    mean={np.mean(all_vlabels):.1f} std={np.std(all_vlabels):.1f}")
    print(f"  born/win:    mean={np.mean(all_born):.2f}")
    print(f"  died/win:    mean={np.mean(all_died):.2f}")

    if peak_links and trough_links:
        print(f"\n  Peak vs Trough:")
        print(f"    {'':>12} {'peak':>10} {'trough':>10} {'diff':>8}")
        print(f"    {'-'*44}")
        print(f"    {'links':>12} {np.mean(peak_links):>10.0f} {np.mean(trough_links):>10.0f} "
              f"{np.mean(peak_links)-np.mean(trough_links):>+8.0f}")
        print(f"    {'v_labels':>12} {np.mean(peak_vlabels):>10.1f} {np.mean(trough_vlabels):>10.1f} "
              f"{np.mean(peak_vlabels)-np.mean(trough_vlabels):>+8.1f}")

    # ── §2: Size-specific response ──
    print(f"\n--- 2. Size-Specific Response ---\n")

    # Collect birth/death by wave phase and size
    size_births_peak = Counter()  # {nodes: count}
    size_births_trough = Counter()
    size_deaths_peak = Counter()
    size_deaths_trough = Counter()
    size_survivors = Counter()
    size_total = Counter()

    # Per-seed analysis
    for seed, data in sorted(seeds.items()):
        labels, max_win = build_label_data(data)
        csv_rows = csvs.get(seed, [])

        # Build window → bg_prob mapping
        win_bg = {}
        for r in csv_rows:
            win_bg[int(r["window"])] = float(r.get("bg_prob_effective", 0.003))

        for lid, info in labels.items():
            nodes = min(info["nodes"], 6)  # 6+ grouped
            size_total[nodes] += 1
            if info["survived"]:
                size_survivors[nodes] += 1

            # Birth phase
            born_bg = win_bg.get(info["born"], 0.003)
            born_phase = get_wave_phase(born_bg)
            if born_phase == "peak":
                size_births_peak[nodes] += 1
            elif born_phase == "trough":
                size_births_trough[nodes] += 1

            # Death phase
            if not info["survived"] and info["died"] <= max_win:
                died_bg = win_bg.get(info["died"], 0.003)
                died_phase = get_wave_phase(died_bg)
                if died_phase == "peak":
                    size_deaths_peak[nodes] += 1
                elif died_phase == "trough":
                    size_deaths_trough[nodes] += 1

    sizes = sorted(set(list(size_total.keys())))

    print(f"  Survival by size:")
    print(f"  {'size':>6} {'total':>7} {'surv':>6} {'rate':>8}")
    print(f"  {'-'*30}")
    for s in sizes:
        t = size_total[s]
        sv = size_survivors[s]
        print(f"  {s:>6} {t:>7} {sv:>6} {sv/max(1,t):>8.2%}")

    print(f"\n  Births by wave phase:")
    print(f"  {'size':>6} {'peak':>7} {'trough':>8} {'ratio':>8}")
    print(f"  {'-'*32}")
    for s in sizes:
        p = size_births_peak[s]
        t = size_births_trough[s]
        ratio = p / max(t, 1)
        print(f"  {s:>6} {p:>7} {t:>8} {ratio:>7.2f}×")

    print(f"\n  Deaths by wave phase:")
    print(f"  {'size':>6} {'peak':>7} {'trough':>8} {'ratio':>8}")
    print(f"  {'-'*32}")
    for s in sizes:
        p = size_deaths_peak[s]
        t = size_deaths_trough[s]
        ratio = p / max(t, 1)
        print(f"  {s:>6} {p:>7} {t:>8} {ratio:>7.2f}×")

    # ── §3: Born-in-peak vs born-in-trough survival ──
    print(f"\n--- 3. Born-in-Peak vs Born-in-Trough Survival ---\n")

    born_peak_surv = defaultdict(lambda: {"total": 0, "surv": 0})
    born_trough_surv = defaultdict(lambda: {"total": 0, "surv": 0})

    for seed, data in sorted(seeds.items()):
        labels, max_win = build_label_data(data)
        csv_rows = csvs.get(seed, [])
        win_bg = {}
        for r in csv_rows:
            win_bg[int(r["window"])] = float(r.get("bg_prob_effective", 0.003))

        for lid, info in labels.items():
            if info["born"] <= 10:
                continue
            nodes = min(info["nodes"], 6)
            born_bg = win_bg.get(info["born"], 0.003)
            born_phase = get_wave_phase(born_bg)

            if born_phase == "peak":
                born_peak_surv[nodes]["total"] += 1
                if info["survived"]:
                    born_peak_surv[nodes]["surv"] += 1
            elif born_phase == "trough":
                born_trough_surv[nodes]["total"] += 1
                if info["survived"]:
                    born_trough_surv[nodes]["surv"] += 1

    print(f"  {'size':>6} {'peak_rate':>10} {'trough_rate':>12} {'ratio':>8}")
    print(f"  {'-'*40}")
    for s in sorted(set(list(born_peak_surv.keys()) + list(born_trough_surv.keys()))):
        p = born_peak_surv[s]
        t = born_trough_surv[s]
        pr = p["surv"] / max(1, p["total"])
        tr = t["surv"] / max(1, t["total"])
        ratio = pr / max(tr, 0.0001) if tr > 0 else 0
        print(f"  {s:>6} {pr:>8.2%}({p['total']:>5}) {tr:>8.2%}({t['total']:>5}) {ratio:>7.2f}×")

    # ── §4: 5-node density independence under wave ──
    print(f"\n--- 4. 5-node Density Independence Under Wave ---\n")

    five_peak_surv = 0; five_peak_total = 0
    five_trough_surv = 0; five_trough_total = 0

    for seed, data in sorted(seeds.items()):
        labels, max_win = build_label_data(data)
        csv_rows = csvs.get(seed, [])
        win_bg = {}
        for r in csv_rows:
            win_bg[int(r["window"])] = float(r.get("bg_prob_effective", 0.003))

        for lid, info in labels.items():
            if info["nodes"] != 5 or info["born"] <= 10:
                continue
            born_bg = win_bg.get(info["born"], 0.003)
            born_phase = get_wave_phase(born_bg)

            if born_phase == "peak":
                five_peak_total += 1
                if info["survived"]:
                    five_peak_surv += 1
            elif born_phase == "trough":
                five_trough_total += 1
                if info["survived"]:
                    five_trough_surv += 1

    if five_peak_total > 0 and five_trough_total > 0:
        pr = five_peak_surv / five_peak_total
        tr = five_trough_surv / five_trough_total
        print(f"  5-node born in peak:   {pr:.2%} ({five_peak_surv}/{five_peak_total})")
        print(f"  5-node born in trough: {tr:.2%} ({five_trough_surv}/{five_trough_total})")
        print(f"  Ratio: {pr/max(tr,0.0001):.2f}×")
        if abs(pr - tr) / max(pr, tr, 0.001) < 0.15:
            print(f"  → 5-node is WAVE-INDEPENDENT (density independence holds under wave)")
        else:
            direction = "peak" if pr > tr else "trough"
            print(f"  → 5-node responds to wave ({direction} is better)")

    # ── §5: Share retention by wave phase ──
    print(f"\n--- 5. Share Retention Under Wave ---\n")

    retain_peak = defaultdict(list)
    retain_trough = defaultdict(list)

    for seed, data in sorted(seeds.items()):
        labels, max_win = build_label_data(data)
        csv_rows = csvs.get(seed, [])
        win_bg = {}
        for r in csv_rows:
            win_bg[int(r["window"])] = float(r.get("bg_prob_effective", 0.003))

        for lid, info in labels.items():
            if not info["survived"] or info["age"] < 10:
                continue
            nodes = min(info["nodes"], 6)
            born_bg = win_bg.get(info["born"], 0.003)
            born_phase = get_wave_phase(born_bg)
            retain = info["share_last"] / max(info["share_birth"], 0.0001)

            if born_phase == "peak":
                retain_peak[nodes].append(retain)
            elif born_phase == "trough":
                retain_trough[nodes].append(retain)

    print(f"  {'size':>6} {'peak_retain':>12} {'trough_retain':>14} {'diff':>8}")
    print(f"  {'-'*44}")
    for s in sorted(set(list(retain_peak.keys()) + list(retain_trough.keys()))):
        pr = np.mean(retain_peak[s]) if retain_peak[s] else 0
        tr = np.mean(retain_trough[s]) if retain_trough[s] else 0
        np_ = len(retain_peak[s])
        nt = len(retain_trough[s])
        if np_ >= 3 and nt >= 3:
            print(f"  {s:>6} {pr:>10.3f}({np_:>3}) {tr:>10.3f}({nt:>3}) {pr-tr:>+8.3f}")

    # Return summary for cross-comparison
    return {
        "label": label,
        "n_seeds": len(seeds),
        "links_mean": np.mean(all_links) if all_links else 0,
        "vlabels_mean": np.mean(all_vlabels) if all_vlabels else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="../v82/diag_v82_baseline")
    parser.add_argument("--wave", default=None)
    parser.add_argument("--wave2", default=None)
    parser.add_argument("--wave3", default=None)
    args = parser.parse_args()

    results = []

    # Baseline
    r = analyze_dir(args.baseline, "BASELINE (no wave)")
    results.append(r)

    # Wave conditions
    for wave_dir, wave_label in [
        (args.wave, "WAVE"),
        (args.wave2, "WAVE 2"),
        (args.wave3, "WAVE 3"),
    ]:
        if wave_dir:
            r = analyze_dir(wave_dir, f"{wave_label}: {wave_dir}")
            results.append(r)

    # Cross-comparison
    if len(results) > 1:
        print(f"\n{'=' * 72}")
        print(f"CROSS-COMPARISON")
        print(f"{'=' * 72}\n")

        print(f"  {'condition':>30} {'links':>8} {'labels':>8}")
        print(f"  {'-'*50}")
        for r in results:
            print(f"  {r['label']:>30} {r['links_mean']:>8.0f} {r['vlabels_mean']:>8.1f}")


if __name__ == "__main__":
    main()
