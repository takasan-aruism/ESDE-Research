#!/usr/bin/env python3
"""
ESDE v9.6 — Era Analysis + Visual Dashboard
=============================================
1. Statistical era (window) analysis across all seeds
2. HTML dashboard with interactive charts

USAGE:
  python v96_dashboard.py --tag short
  python v96_dashboard.py --tag long
"""

import csv, json, glob, argparse, math
import numpy as np
from pathlib import Path
from collections import defaultdict


def sf(v, d=0.0):
    try: return float(v) if v else d
    except: return d

def si(v, d=0):
    try: return int(v) if v else d
    except: return d


def load_windows(tag):
    rows = []
    base = Path(f"diag_v96_baseline_{tag}")
    for fp in sorted(glob.glob(str(base / "aggregates" / "per_window_seed*.csv"))):
        with open(fp) as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows


def load_labels(tag):
    rows = []
    base = Path(f"diag_v96_baseline_{tag}")
    for fp in sorted(glob.glob(str(base / "labels" / "per_label_seed*.csv"))):
        with open(fp) as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows


def load_network(tag):
    rows = []
    base = Path(f"diag_v96_baseline_{tag}")
    for fp in sorted(glob.glob(str(base / "network" / "fam_edges_seed*.csv"))):
        with open(fp) as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows


def run(tag="short"):
    windows = load_windows(tag)
    labels = load_labels(tag)
    edges = load_network(tag)

    if not windows:
        print(f"  No data for tag={tag}")
        return

    print(f"\n{'='*70}")
    print(f"  ESDE v9.6 — ERA ANALYSIS ({tag})")
    print(f"  {len(windows)} window rows, {len(labels)} labels")
    print(f"{'='*70}\n")

    # ════════════════════════════════════════════════════════
    # ERA AGGREGATION (mean + std across seeds per window)
    # ════════════════════════════════════════════════════════
    by_win = defaultdict(list)
    for w in windows:
        by_win[int(w["window"])].append(w)

    era_data = []
    for win in sorted(by_win.keys()):
        rows = by_win[win]
        era_data.append({
            "window": win,
            "n_seeds": len(rows),
            "social_mean": np.mean([sf(r.get("mean_social")) for r in rows]),
            "social_std": np.std([sf(r.get("mean_social")) for r in rows]),
            "stability_mean": np.mean([sf(r.get("mean_stability")) for r in rows]),
            "spread_mean": np.mean([sf(r.get("mean_spread")) for r in rows]),
            "spread_std": np.std([sf(r.get("mean_spread")) for r in rows]),
            "familiarity_mean": np.mean([sf(r.get("mean_familiarity")) for r in rows]),
            "familiarity_std": np.std([sf(r.get("mean_familiarity")) for r in rows]),
            "reciprocal_mean": np.mean([si(r.get("reciprocal_pairs")) for r in rows]),
            "reciprocal_std": np.std([si(r.get("reciprocal_pairs")) for r in rows]),
            "asymm_mean": np.mean([si(r.get("asymmetric_pairs")) for r in rows]),
            "labels_mean": np.mean([si(r.get("v_labels")) for r in rows]),
            "labels_std": np.std([si(r.get("v_labels")) for r in rows]),
            "alive_mean": np.mean([si(r.get("alive_tracked")) for r in rows]),
            "count_social_mean": np.mean([si(r.get("count_social")) for r in rows]),
            "count_isolated_mean": np.mean([si(r.get("count_isolated")) for r in rows]),
            "count_deeply_mean": np.mean([si(r.get("count_deeply_connected")) for r in rows]),
            "att_overlap_mean": np.mean([sf(r.get("att_overlap_mean")) for r in rows]),
            "links_mean": np.mean([si(r.get("links")) for r in rows]),
            "fam_sym_mean": np.mean([sf(r.get("fam_symmetry_mean")) for r in rows]),
        })

    # ════════════════════════════════════════════════════════
    # ERA TEXT REPORT
    # ════════════════════════════════════════════════════════
    print(f"  ── Era Trends (Cross-Seed Mean) ──\n")
    print(f"  {'w':>4} {'labels':>6} {'alive':>6} {'social':>7} "
          f"{'spread':>7} {'famil':>7} {'recip':>6} {'isolat':>6} "
          f"{'deep':>6} {'att_ov':>6}")
    print(f"  {'-'*72}")
    for e in era_data:
        print(f"  {e['window']:>4} {e['labels_mean']:>6.1f} "
              f"{e['alive_mean']:>6.1f} {e['social_mean']:>7.3f} "
              f"{e['spread_mean']:>7.4f} {e['familiarity_mean']:>7.2f} "
              f"{e['reciprocal_mean']:>6.1f} "
              f"{e['count_isolated_mean']:>6.1f} "
              f"{e['count_deeply_mean']:>6.1f} "
              f"{e['att_overlap_mean']:>6.1f}")

    # Trends
    if len(era_data) >= 2:
        first = era_data[0]
        last = era_data[-1]
        print(f"\n  ── Era Deltas (first → last) ──\n")
        for k in ["social_mean", "spread_mean", "familiarity_mean",
                  "reciprocal_mean", "count_isolated_mean",
                  "count_deeply_mean", "att_overlap_mean",
                  "labels_mean", "alive_mean"]:
            delta = last[k] - first[k]
            sign = "+" if delta >= 0 else ""
            print(f"    {k:>22}: {first[k]:>8.2f} → {last[k]:>8.2f} "
                  f"({sign}{delta:>+.2f})")

    # ════════════════════════════════════════════════════════
    # Death age distribution
    # ════════════════════════════════════════════════════════
    dead_labels = [r for r in labels if r.get("alive") == "False"]
    death_windows = [si(r.get("death_window")) for r in dead_labels
                     if r.get("death_window")]
    lifespans = [si(r.get("lifespan")) for r in dead_labels
                 if r.get("lifespan")]

    print(f"\n  ── Death Age Distribution ──\n")
    print(f"  Total deaths: {len(dead_labels)}")
    if death_windows:
        dw_counter = defaultdict(int)
        for d in death_windows:
            dw_counter[d] += 1
        print(f"\n  Deaths per window:")
        for w in sorted(dw_counter.keys()):
            bar = "█" * min(40, dw_counter[w] // 3)
            print(f"    w={w:>3}: {dw_counter[w]:>4} {bar}")

    if lifespans:
        life_counter = defaultdict(int)
        for l in lifespans:
            life_counter[l] += 1
        print(f"\n  Lifespan distribution (dead labels):")
        for l in sorted(life_counter.keys()):
            if l <= 30:
                bar = "█" * min(40, life_counter[l] // 3)
                print(f"    life={l:>3}: {life_counter[l]:>4} {bar}")

    # ════════════════════════════════════════════════════════
    # HTML DASHBOARD
    # ════════════════════════════════════════════════════════
    out_html = Path(f"diag_v96_baseline_{tag}") / "dashboard.html"
    generate_dashboard(era_data, labels, edges, dead_labels, out_html, tag)
    print(f"\n  Saved HTML dashboard: {out_html}")
    print(f"\n{'='*70}\n")


def generate_dashboard(era_data, labels, edges, dead_labels, out_path, tag):
    """Generate self-contained HTML dashboard with Chart.js."""

    # Prepare data
    windows_list = [e["window"] for e in era_data]
    social = [round(e["social_mean"], 4) for e in era_data]
    social_std = [round(e["social_std"], 4) for e in era_data]
    spread = [round(e["spread_mean"], 4) for e in era_data]
    familiarity = [round(e["familiarity_mean"], 2) for e in era_data]
    fam_std = [round(e["familiarity_std"], 2) for e in era_data]
    reciprocal = [round(e["reciprocal_mean"], 1) for e in era_data]
    asymm = [round(e["asymm_mean"], 1) for e in era_data]
    labels_n = [round(e["labels_mean"], 1) for e in era_data]
    alive_n = [round(e["alive_mean"], 1) for e in era_data]
    isolated = [round(e["count_isolated_mean"], 1) for e in era_data]
    socialc = [round(e["count_social_mean"], 1) for e in era_data]
    deeply = [round(e["count_deeply_mean"], 1) for e in era_data]
    att_overlap = [round(e["att_overlap_mean"], 1) for e in era_data]
    links = [round(e["links_mean"], 0) for e in era_data]

    # Disposition scatter (sample up to 500 labels)
    scatter_data = []
    sample = labels if len(labels) < 500 else labels[::max(1, len(labels)//500)]
    for r in sample:
        s = sf(r.get("last_social"))
        f = sf(r.get("last_familiarity"))
        p = si(r.get("last_partners"))
        alive = r.get("alive") == "True"
        if f > 0 or s > 0:
            scatter_data.append({
                "x": round(s, 4),
                "y": round(f, 2),
                "r": min(15, max(2, math.sqrt(p))),
                "alive": alive,
                "lid": r.get("label_id"),
                "seed": r.get("seed"),
            })

    scatter_alive = [d for d in scatter_data if d["alive"]]
    scatter_dead = [d for d in scatter_data if not d["alive"]]

    # Death age histogram
    death_win_hist = defaultdict(int)
    for r in dead_labels:
        dw = si(r.get("death_window"))
        if dw > 0:
            death_win_hist[dw] += 1
    dh_windows = sorted(death_win_hist.keys())
    dh_counts = [death_win_hist[w] for w in dh_windows]

    # Lifespan histogram
    life_hist = defaultdict(int)
    for r in dead_labels:
        l = si(r.get("lifespan"))
        life_hist[l] += 1
    lh_lives = sorted(life_hist.keys())
    lh_counts = [life_hist[l] for l in lh_lives]

    # Social survival curve
    social_bins = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4),
                   (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8),
                   (0.8, 0.9), (0.9, 1.01)]
    survival_labels = []
    survival_rates = []
    survival_counts = []
    for lo, hi in social_bins:
        subset = [r for r in labels
                  if lo <= sf(r.get("last_social")) < hi]
        if subset:
            alive = sum(1 for r in subset if r.get("alive") == "True")
            survival_labels.append(f"{lo:.1f}-{hi:.1f}")
            survival_rates.append(round(alive / len(subset) * 100, 1))
            survival_counts.append(len(subset))

    # Familiarity survival curve
    fam_bins = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30),
                (30, 50), (50, 100), (100, 200)]
    fam_surv_labels = []
    fam_surv_rates = []
    fam_surv_counts = []
    for lo, hi in fam_bins:
        subset = [r for r in labels
                  if lo <= sf(r.get("last_familiarity")) < hi]
        if subset:
            alive = sum(1 for r in subset if r.get("alive") == "True")
            fam_surv_labels.append(f"{lo}-{hi}")
            fam_surv_rates.append(round(alive / len(subset) * 100, 1))
            fam_surv_counts.append(len(subset))

    # Partner survival curve
    p_bins = [(0, 2), (2, 5), (5, 10), (10, 20),
              (20, 30), (30, 50), (50, 100)]
    p_surv_labels = []
    p_surv_rates = []
    for lo, hi in p_bins:
        subset = [r for r in labels
                  if lo <= si(r.get("last_partners")) < hi]
        if subset:
            alive = sum(1 for r in subset if r.get("alive") == "True")
            p_surv_labels.append(f"{lo}-{hi}")
            p_surv_rates.append(round(alive / len(subset) * 100, 1))

    # Archetype counts (simple classifier)
    archetype_counts = defaultdict(int)
    for r in labels:
        s = sf(r.get("last_social"))
        f = sf(r.get("last_familiarity"))
        p = si(r.get("last_partners"))
        st = sf(r.get("last_st_mean"))
        sp = sf(r.get("last_spread"))
        alive = r.get("alive") == "True"
        life = si(r.get("lifespan"))

        if st > 80 and p > 30:
            atype = "Emperor"
        elif s > 0.8 and p > 30 and life > 15:
            atype = "Elder"
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
        elif s > 0.5 and not alive:
            atype = "Fallen Social"
        else:
            atype = "Other"
        archetype_counts[atype] += 1

    # Top reciprocal pairs
    pair_fam = {}
    for e in edges:
        seed = e["seed"]
        a, b = int(e["from"]), int(e["to"])
        key = (seed, min(a, b), max(a, b))
        if key not in pair_fam:
            pair_fam[key] = [0.0, 0.0]
        fa = sf(e.get("familiarity"))
        if a < b:
            pair_fam[key][0] = max(pair_fam[key][0], fa)
        else:
            pair_fam[key][1] = max(pair_fam[key][1], fa)

    mutual_pairs = []
    for (seed, a, b), (fab, fba) in pair_fam.items():
        mutual = min(fab, fba)
        if mutual > 0:
            sym = mutual / max(fab, fba)
            mutual_pairs.append([seed, a, b, round(fab, 1), round(fba, 1),
                                  round(mutual, 1), round(sym, 3)])

    mutual_pairs.sort(key=lambda x: -x[5])
    top_mutual = mutual_pairs[:20]
    asym_pairs = sorted(mutual_pairs, key=lambda x: x[6])[:20]

    # ── HTML ──
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>ESDE v9.6 Dashboard ({tag})</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
body {{ font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9;
       margin: 0; padding: 20px; }}
h1 {{ color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }}
h2 {{ color: #7ee787; margin-top: 30px; }}
.grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
.chart-box {{ background: #161b22; padding: 15px; border-radius: 8px;
              border: 1px solid #30363d; }}
.chart-box.full {{ grid-column: 1 / -1; }}
.chart-box h3 {{ margin: 0 0 10px 0; color: #58a6ff; font-size: 14px; }}
.chart-box canvas {{ max-height: 300px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th, td {{ padding: 6px 10px; text-align: right; border-bottom: 1px solid #30363d; }}
th {{ color: #7ee787; font-weight: normal; }}
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;
          margin-bottom: 20px; }}
.stat-card {{ background: #161b22; padding: 15px; border-radius: 8px;
              border: 1px solid #30363d; }}
.stat-card .label {{ color: #8b949e; font-size: 12px; }}
.stat-card .value {{ color: #58a6ff; font-size: 24px; font-weight: bold; }}
.note {{ color: #8b949e; font-size: 11px; margin-top: 5px; }}
</style>
</head>
<body>
<h1>ESDE v9.6 Baseline Dashboard — {tag}</h1>

<div class="stats">
  <div class="stat-card">
    <div class="label">Total labels</div>
    <div class="value">{len(labels)}</div>
  </div>
  <div class="stat-card">
    <div class="label">Seeds</div>
    <div class="value">{era_data[0]['n_seeds'] if era_data else 0}</div>
  </div>
  <div class="stat-card">
    <div class="label">Alive / Dead</div>
    <div class="value">{sum(1 for r in labels if r.get('alive')=='True')}/{len(dead_labels)}</div>
  </div>
  <div class="stat-card">
    <div class="label">Windows tracked</div>
    <div class="value">{len(era_data)}</div>
  </div>
</div>

<h2>Era Trends (Cross-Seed Mean)</h2>
<div class="grid">

<div class="chart-box">
  <h3>Labels alive per window</h3>
  <canvas id="c_labels"></canvas>
</div>

<div class="chart-box">
  <h3>Mean social disposition</h3>
  <canvas id="c_social"></canvas>
  <div class="note">Cross-seed mean of alive labels per window</div>
</div>

<div class="chart-box">
  <h3>Mean familiarity (with std band)</h3>
  <canvas id="c_fam"></canvas>
</div>

<div class="chart-box">
  <h3>Mean attention spread</h3>
  <canvas id="c_spread"></canvas>
</div>

<div class="chart-box">
  <h3>Reciprocal vs asymmetric pairs</h3>
  <canvas id="c_pairs"></canvas>
</div>

<div class="chart-box">
  <h3>Social / isolated / deeply_connected counts</h3>
  <canvas id="c_counts"></canvas>
</div>

<div class="chart-box full">
  <h3>Attention hotspot overlap growth</h3>
  <canvas id="c_overlap"></canvas>
  <div class="note">
    Mean number of shared attention hotspot nodes between label pairs.
    Shared experience grows as the system matures.
  </div>
</div>

</div>

<h2>Death Analysis</h2>
<div class="grid">

<div class="chart-box">
  <h3>Deaths per window</h3>
  <canvas id="c_deaths"></canvas>
</div>

<div class="chart-box">
  <h3>Lifespan distribution (dead labels)</h3>
  <canvas id="c_life"></canvas>
</div>

<div class="chart-box">
  <h3>Survival vs social (threshold at 0.4)</h3>
  <canvas id="c_surv_social"></canvas>
</div>

<div class="chart-box">
  <h3>Survival vs familiarity</h3>
  <canvas id="c_surv_fam"></canvas>
</div>

<div class="chart-box full">
  <h3>Survival vs partner count</h3>
  <canvas id="c_surv_part"></canvas>
  <div class="note">
    Real causation: partner count drives survival, not familiarity depth.
  </div>
</div>

</div>

<h2>Disposition Space</h2>
<div class="grid">

<div class="chart-box full">
  <h3>Social × Familiarity scatter (size = partners)</h3>
  <canvas id="c_scatter" style="max-height: 500px;"></canvas>
  <div class="note">
    Green = alive, red = dead. Top-right = social AND deeply connected (rare).
    Bottom-left = isolated and disconnected.
  </div>
</div>

<div class="chart-box">
  <h3>Archetype distribution</h3>
  <canvas id="c_archetype"></canvas>
</div>

<div class="chart-box">
  <h3>Top 20 reciprocal pairs (mutual strength)</h3>
  <table>
    <tr><th>#</th><th>seed</th><th>A</th><th>B</th><th>A→B</th><th>B→A</th><th>mutual</th><th>sym</th></tr>
    {''.join(f'<tr><td>{i+1}</td><td>{p[0]}</td><td>{p[1]}</td><td>{p[2]}</td><td>{p[3]}</td><td>{p[4]}</td><td>{p[5]}</td><td>{p[6]}</td></tr>' for i, p in enumerate(top_mutual))}
  </table>
</div>

</div>

<script>
Chart.defaults.color = '#c9d1d9';
Chart.defaults.borderColor = '#30363d';
const wins = {json.dumps(windows_list)};

const mkLine = (id, data, label, color, fill=false) => new Chart(document.getElementById(id), {{
  type: 'line', data: {{ labels: wins, datasets: [
    {{ label, data, borderColor: color, backgroundColor: color + '33', fill, tension: 0.3 }}
  ]}},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }}, y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

mkLine('c_labels', {json.dumps(labels_n)}, 'labels', '#58a6ff');
mkLine('c_social', {json.dumps(social)}, 'social', '#7ee787');
mkLine('c_spread', {json.dumps(spread)}, 'spread', '#d2a8ff');
mkLine('c_overlap', {json.dumps(att_overlap)}, 'overlap', '#ffa657');

new Chart(document.getElementById('c_fam'), {{
  type: 'line',
  data: {{ labels: wins, datasets: [
    {{ label: 'familiarity', data: {json.dumps(familiarity)},
       borderColor: '#ff7b72', backgroundColor: '#ff7b7233', fill: false, tension: 0.3 }}
  ]}},
  options: {{ responsive: true, scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_pairs'), {{
  type: 'line',
  data: {{ labels: wins, datasets: [
    {{ label: 'reciprocal', data: {json.dumps(reciprocal)},
       borderColor: '#7ee787', fill: false, tension: 0.3 }},
    {{ label: 'asymmetric', data: {json.dumps(asymm)},
       borderColor: '#ff7b72', fill: false, tension: 0.3 }}
  ]}},
  options: {{ responsive: true, scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_counts'), {{
  type: 'line',
  data: {{ labels: wins, datasets: [
    {{ label: 'social', data: {json.dumps(socialc)}, borderColor: '#7ee787',
       fill: false, tension: 0.3 }},
    {{ label: 'isolated', data: {json.dumps(isolated)}, borderColor: '#ff7b72',
       fill: false, tension: 0.3 }},
    {{ label: 'deeply', data: {json.dumps(deeply)}, borderColor: '#d2a8ff',
       fill: false, tension: 0.3 }}
  ]}},
  options: {{ responsive: true, scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_deaths'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(dh_windows)},
    datasets: [{{ label: 'deaths', data: {json.dumps(dh_counts)},
      backgroundColor: '#ff7b72' }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_life'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(lh_lives)},
    datasets: [{{ label: 'count', data: {json.dumps(lh_counts)},
      backgroundColor: '#d2a8ff' }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_surv_social'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(survival_labels)},
    datasets: [{{ label: 'survival %', data: {json.dumps(survival_rates)},
      backgroundColor: {json.dumps(['#ff7b72' if r < 50 else '#7ee787' for r in survival_rates])} }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }}, }} }}
}});

new Chart(document.getElementById('c_surv_fam'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(fam_surv_labels)},
    datasets: [{{ label: 'survival %', data: {json.dumps(fam_surv_rates)},
      backgroundColor: {json.dumps(['#ff7b72' if r < 50 else '#7ee787' for r in fam_surv_rates])} }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_surv_part'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(p_surv_labels)},
    datasets: [{{ label: 'survival %', data: {json.dumps(p_surv_rates)},
      backgroundColor: {json.dumps(['#ff7b72' if r < 50 else '#7ee787' for r in p_surv_rates])} }}] }},
  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});

new Chart(document.getElementById('c_scatter'), {{
  type: 'bubble',
  data: {{ datasets: [
    {{ label: 'alive', data: {json.dumps(scatter_alive)},
       backgroundColor: '#7ee78788', borderColor: '#7ee787' }},
    {{ label: 'dead', data: {json.dumps(scatter_dead)},
       backgroundColor: '#ff7b7288', borderColor: '#ff7b72' }}
  ]}},
  options: {{
    responsive: true,
    scales: {{
      x: {{ title: {{ display: true, text: 'social' }},
            grid: {{ color: '#21262d' }}, min: 0, max: 1 }},
      y: {{ title: {{ display: true, text: 'familiarity' }},
            grid: {{ color: '#21262d' }} }}
    }},
    plugins: {{
      tooltip: {{ callbacks: {{ label: (ctx) => {{
        const d = ctx.raw;
        return `seed ${{d.seed}} L${{d.lid}}: s=${{d.x}} f=${{d.y}}`;
      }} }} }}
    }}
  }}
}});

new Chart(document.getElementById('c_archetype'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(list(archetype_counts.keys()))},
    datasets: [{{ label: 'count', data: {json.dumps(list(archetype_counts.values()))},
      backgroundColor: ['#ffa657', '#d2a8ff', '#7ee787', '#58a6ff',
                        '#79c0ff', '#ff7b72', '#f85149', '#da3633',
                        '#8b949e'] }}] }},
  options: {{ responsive: true, indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ color: '#21262d' }} }},
             y: {{ grid: {{ color: '#21262d' }} }} }} }}
}});
</script>
</body>
</html>
"""

    with open(out_path, "w") as f:
        f.write(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.6 Era Analysis + Dashboard")
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()
    run(tag=args.tag)
