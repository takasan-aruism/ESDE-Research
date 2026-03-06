#!/usr/bin/env python3
"""
ESDE Genesis v1.9b — Adaptive Resolution Observer (Revised)
==============================================================
Fixes from GPT audit:
  1) k=3 revived: uses WEAK-threshold island membership for size
     (3-bin: None / WeakOnly / Mid+)
  2) Drift stats stabilized: Δdrift (difference) primary, guarded ratio secondary

k=0: C
k=1: C + Resonance (High/Mid/Low)
k=2: k1 + Boundary (Core/Edge)
k=3: k2 + Island_Scale (None/WeakOnly/Mid+)  ← REVISED
k=4: k3 + Intrusion (0/1+)

Usage:
  python v19b_postprocess.py --input-dir outputs_v18O2
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, argparse
from collections import Counter, defaultdict
from pathlib import Path

LAMBDA = 1.0; MU = 0.5
K_LEVELS = [0, 1, 2, 3, 4]
OUTPUT_DIR = Path("outputs_v19b")
RATE_GRID = [0.0, 0.0005, 0.001, 0.002, 0.005]
R_BITS_KEYS = ["000","001","010","011","100","101","110","111"]
DRIFT_EPS = 1e-3  # guard for ratio computation


def shannon(counts):
    t = sum(counts)
    if t == 0: return 0.0
    ps = [c/t for c in counts if c > 0]
    return -sum(p * np.log2(p) for p in ps)


def ctx_to_label(ctx, k):
    """Convert raw context to label. k=3 REVISED to use weak-threshold scale."""
    if k == 0: return "C"

    rb = ctx.get("r_bits", "000")
    s = int(rb[0]) if len(rb) >= 1 else 0
    m = int(rb[1]) if len(rb) >= 2 else 0
    w = int(rb[2]) if len(rb) >= 3 else 0

    # k>=1: Resonance
    res = "High" if s == 1 else ("Mid" if m == 1 else "Low")
    if k == 1: return f"C_{res}"

    # k>=2: Boundary
    bd = "Edge" if ctx.get("boundary_mid", 0) == 1 else "Core"
    if k == 2: return f"C_{res}_{bd}"

    # k>=3: Island Scale (REVISED - uses weak bit for richer signal)
    # None: not in any island at weak threshold
    # WeakOnly: in weak island but NOT in mid island
    # Mid+: in mid (or stronger) island
    if s == 1 or m == 1:
        scale = "Mid+"
    elif w == 1:
        scale = "WeakOnly"
    else:
        scale = "None"
    if k == 3: return f"C_{res}_{bd}_{scale}"

    # k>=4: Intrusion
    ie = "1p" if ctx.get("intrusion_bin", 0) >= 1 else "0"
    return f"C_{res}_{bd}_{scale}_{ie}"


def reconstruct_nodes(row):
    nodes = []
    for rb in R_BITS_KEYS:
        count = int(row.get(f"r_{rb}", 0))
        for _ in range(count):
            nodes.append({"r_bits": rb})
    n = len(nodes)
    if n == 0: return nodes
    bd1 = int(row.get("bd_1", 0)); sz1 = int(row.get("sz_1", 0))
    f1 = int(row.get("f_1", 0))
    intr1 = int(row.get("intr_1", 0)); intr2p = int(row.get("intr_2p", 0))
    for i, nd in enumerate(nodes):
        nd["boundary_mid"] = 1 if i < bd1 else 0
        nd["size_mid_bin"] = 1 if i < sz1 else 0
        nd["fert_bin"] = 1 if i < f1 else 0
        nd["intrusion_bin"] = 2 if i < intr2p else (1 if i < intr2p + intr1 else 0)
    return nodes


def compute_drift_jsd(nodes1, nodes2, k):
    """JSD-based drift between two window snapshots at resolution k."""
    l1 = Counter(ctx_to_label(n, k) for n in nodes1)
    l2 = Counter(ctx_to_label(n, k) for n in nodes2)
    all_l = set(l1.keys()) | set(l2.keys())
    t1 = sum(l1.values()); t2 = sum(l2.values())
    if t1 == 0 or t2 == 0 or not all_l: return None
    p = np.array([l1.get(l, 0)/t1 for l in all_l])
    q = np.array([l2.get(l, 0)/t2 for l in all_l])
    m = (p + q) / 2
    def kl(a, b): return sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
    return round(float(np.sqrt((kl(p,m)+kl(q,m))/2)), 4)


def compute_split_drift(prev_nodes, cur_nodes, k):
    """Compute drift separately for hit and nohit nodes (for O9.3 audit)."""
    def subset_jsd(prev, cur):
        if not prev or not cur: return None
        l1 = Counter(ctx_to_label(n, k) for n in prev)
        l2 = Counter(ctx_to_label(n, k) for n in cur)
        all_l = set(l1.keys()) | set(l2.keys())
        t1 = sum(l1.values()); t2 = sum(l2.values())
        if t1 == 0 or t2 == 0: return None
        p = np.array([l1.get(l,0)/t1 for l in all_l])
        q = np.array([l2.get(l,0)/t2 for l in all_l])
        m = (p+q)/2
        def kl(a,b): return sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
        return round(float(np.sqrt((kl(p,m)+kl(q,m))/2)), 4)

    hit_prev = [n for n in prev_nodes if n.get("intrusion_bin", 0) >= 1]
    hit_cur = [n for n in cur_nodes if n.get("intrusion_bin", 0) >= 1]
    nohit_prev = [n for n in prev_nodes if n.get("intrusion_bin", 0) == 0]
    nohit_cur = [n for n in cur_nodes if n.get("intrusion_bin", 0) == 0]

    d_hit = subset_jsd(hit_prev, hit_cur)
    d_nohit = subset_jsd(nohit_prev, nohit_cur)

    # Stable stats
    delta = round(d_hit - d_nohit, 4) if d_hit is not None and d_nohit is not None else None
    guard_triggered = d_nohit is not None and d_nohit < DRIFT_EPS
    ratio = round(d_hit / max(d_nohit, DRIFT_EPS), 3) if d_hit is not None and d_nohit is not None else None
    frac_hit = sum(1 for n in cur_nodes if n.get("intrusion_bin",0)>=1) / max(len(cur_nodes),1)

    return {
        "drift_hit": d_hit, "drift_nohit": d_nohit,
        "delta_drift": delta, "ratio_guarded": ratio,
        "guard_triggered": guard_triggered, "frac_hit": round(frac_hit, 4),
    }


def load_data(input_dir):
    wd = defaultdict(list)
    for d in sorted(input_dir.iterdir()):
        if not d.is_dir(): continue
        for wf in sorted(d.glob("*_window_raw.csv")):
            with open(wf) as f:
                for row in csv.DictReader(f):
                    wd[(float(row["rate"]), int(row["seed"]))].append(row)
    return wd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, default="outputs_v18O2")
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  Loading from {input_dir}...")
    wd = load_data(input_dir)
    print(f"  Loaded: {len(wd)} runs, {sum(len(v) for v in wd.values())} windows")

    comp_rows = []; optimal_rows = []; k3_rows = []; intr_rows = []
    qa_res = Counter(); qa_scale = Counter()

    for (rate, seed), windows in sorted(wd.items()):
        prev_nodes = None
        for wi, row in enumerate(windows):
            nodes = reconstruct_nodes(row)
            if not nodes: prev_nodes = None; continue

            # QA
            for n in nodes:
                rb = n["r_bits"]
                s,m,w = int(rb[0]), int(rb[1]), int(rb[2]) if len(rb)>=3 else 0
                qa_res["High" if s else ("Mid" if m else "Low")] += 1
                qa_scale["Mid+" if (s or m) else ("WeakOnly" if w else "None")] += 1

            # Compute k metrics
            for k in K_LEVELS:
                labels = [ctx_to_label(n, k) for n in nodes]
                counts = Counter(labels)
                tc = len(counts); H = shannon(list(counts.values()))
                drift = compute_drift_jsd(prev_nodes, nodes, k) if prev_nodes else None

                tH = round(H, 4)
                tD = round(LAMBDA * drift, 4) if drift is not None else 0
                tP = round(-MU * np.log2(tc + 1), 4)
                J = round(tH + tD + tP, 4)

                comp_rows.append({
                    "seed":seed,"window":wi+1,"rate":rate,"k":k,
                    "type_count":tc,"H":tH,"drift":drift,
                    "J":J,"term_H":tH,"term_drift":tD,"term_penalty":tP,
                })

            # k* selection
            cands = comp_rows[-5:]
            best = max(cands, key=lambda r: r["J"])
            k_star = best["k"]
            for r in comp_rows[-5:]: r["k_star"] = k_star

            optimal_rows.append({
                "seed":seed,"window":wi+1,"rate":rate,
                "k_star":k_star,"J_star":best["J"],
                "type_count":best["type_count"],"H":best["H"],"drift":best["drift"],
            })

            # O9.4: k=3 diagnosis
            H2 = [r for r in comp_rows[-5:] if r["k"]==2][0]["H"]
            H3 = [r for r in comp_rows[-5:] if r["k"]==3][0]["H"]
            J2 = [r for r in comp_rows[-5:] if r["k"]==2][0]["J"]
            J3 = [r for r in comp_rows[-5:] if r["k"]==3][0]["J"]
            k3_rows.append({
                "seed":seed,"window":wi+1,"rate":rate,
                "H2":H2,"H3":H3,"dH":round(H3-H2,4),"J2":J2,"J3":J3,
            })

            # O9.3: Intrusion drift audit (stabilized)
            if prev_nodes is not None:
                sd = compute_split_drift(prev_nodes, nodes, 4)
                intr_rows.append({"seed":seed,"window":wi+1,"rate":rate, **sd})

            prev_nodes = nodes

    # ============================================================
    # Save outputs
    # ============================================================
    with open(OUTPUT_DIR/"v19b_k_components.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=comp_rows[0].keys()); w.writeheader(); w.writerows(comp_rows)

    with open(OUTPUT_DIR/"v19b_optimal_k.csv","w",newline="") as f:
        if optimal_rows:
            w=csv.DictWriter(f,fieldnames=optimal_rows[0].keys()); w.writeheader(); w.writerows(optimal_rows)

    with open(OUTPUT_DIR/"v19b_k3_diagnosis.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=k3_rows[0].keys()); w.writeheader(); w.writerows(k3_rows)

    if intr_rows:
        with open(OUTPUT_DIR/"v19b_intrusion_audit.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=intr_rows[0].keys()); w.writeheader(); w.writerows(intr_rows)

    # ============================================================
    # Analysis
    # ============================================================
    k_star_dist = Counter(r["k_star"] for r in optimal_rows)

    print(f"\n{'='*70}")
    print(f"  v1.9b REVISED k* SELECTION ({len(optimal_rows)} windows)")
    print(f"{'='*70}")

    print(f"\n  QA: Resonance={dict(qa_res)}")
    print(f"  QA: Island Scale={dict(qa_scale)}")

    print(f"\n  k* Distribution:")
    for k in K_LEVELS:
        n = k_star_dist.get(k, 0)
        print(f"    k={k}: {n} ({n/max(len(optimal_rows),1)*100:.1f}%)")

    # Per-rate
    print(f"\n  Per-rate:")
    rate_agg = []
    for rate in RATE_GRID:
        sub = [r for r in optimal_rows if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        kd = Counter(r["k_star"] for r in sub)
        dom = kd.most_common(1)[0][0]
        mJ = np.mean([r["J_star"] for r in sub])
        mT = np.mean([r["type_count"] for r in sub])
        rate_agg.append({"rate":rate,"dom_k":dom,"dist":dict(kd),"mJ":round(mJ,4),"mT":round(mT,2)})
        print(f"    rate={rate}: k*={dom} dist={dict(kd)} J={mJ:.3f} types={mT:.1f}")

    # k=3 analysis
    print(f"\n  k=3 Diagnosis (REVISED):")
    for rate in RATE_GRID:
        sub = [r for r in k3_rows if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        mdH = np.mean([r["dH"] for r in sub])
        k3_wins = sum(1 for r in optimal_rows if abs(r["rate"]-rate)<1e-6 and r["k_star"]==3)
        print(f"    rate={rate}: mean ΔH(k3-k2)={mdH:.4f} k=3 wins={k3_wins}")

    # Intrusion audit (stabilized)
    print(f"\n  Intrusion Drift Audit (stabilized):")
    for rate in RATE_GRID:
        sub = [r for r in intr_rows if abs(r["rate"]-rate)<1e-6 and r["delta_drift"] is not None]
        if not sub: continue
        deltas = [r["delta_drift"] for r in sub]
        guards = sum(1 for r in sub if r["guard_triggered"])
        print(f"    rate={rate}: Δdrift={np.median(deltas):+.4f} "
              f"[{np.percentile(deltas,25):+.3f}, {np.percentile(deltas,75):+.3f}] "
              f"guards={guards}/{len(sub)}")

    # ============================================================
    # Plots
    # ============================================================
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle("ESDE Genesis v1.9b — Revised k* Selection\n"
                 "(k=3 revived: Island Scale = None/WeakOnly/Mid+)",
                 fontsize=13, fontweight="bold")

    # k* distribution
    ax = axes[0][0]
    colors = ["#95a5a6","#2ecc71","#3498db","#e67e22","#e74c3c"]
    ax.bar(K_LEVELS, [k_star_dist.get(k,0) for k in K_LEVELS], color=colors)
    ax.set_title("k* Distribution (all windows)"); ax.set_xlabel("k"); ax.grid(True, alpha=0.2)

    # Dominant k* vs rate
    ax = axes[0][1]
    if rate_agg:
        ax.plot([a["rate"] for a in rate_agg], [a["dom_k"] for a in rate_agg],
                "o-", color="#e67e22", ms=10, lw=2)
    ax.set_title("Dominant k* vs Rate"); ax.set_yticks(K_LEVELS); ax.grid(True, alpha=0.2)

    # ΔH(k3-k2) distribution
    ax = axes[0][2]
    dhs = [r["dH"] for r in k3_rows]
    ax.hist(dhs, bins=40, color="#e67e22", alpha=0.7, edgecolor="white")
    ax.axvline(x=0, color="red", ls="--"); ax.axvline(x=0.05, color="green", ls=":", label="target ΔH=0.05")
    ax.set_title("ΔH(k3−k2) Distribution (REVISED)"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    # Δdrift (stabilized) vs rate
    ax = axes[1][0]
    for rate in RATE_GRID:
        sub = [r["delta_drift"] for r in intr_rows if abs(r["rate"]-rate)<1e-6 and r["delta_drift"] is not None]
        if sub:
            ax.boxplot([sub], positions=[RATE_GRID.index(rate)], widths=0.6)
    ax.set_xticks(range(len(RATE_GRID))); ax.set_xticklabels([str(r) for r in RATE_GRID], fontsize=8)
    ax.axhline(y=0, color="red", ls="--", alpha=0.5)
    ax.set_title("Δdrift (hit−nohit) at k=4"); ax.grid(True, alpha=0.2)

    # Island Scale distribution
    ax = axes[1][1]
    ax.bar(["None","WeakOnly","Mid+"],
           [qa_scale.get("None",0), qa_scale.get("WeakOnly",0), qa_scale.get("Mid+",0)],
           color=["#95a5a6","#3498db","#e74c3c"])
    ax.set_title("Island Scale Distribution (all C nodes)"); ax.grid(True, alpha=0.2)

    # Mean J per k
    ax = axes[1][2]
    for k in K_LEVELS:
        vals = [r["J"] for r in comp_rows if r["k"]==k]
        if vals: ax.bar(k, np.mean(vals), color=colors[k], alpha=0.7)
    ax.set_title("Mean J per k Level"); ax.set_xlabel("k"); ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19b_plots.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v19b_plots.png'}")

    # Conclusion
    k3_revived = any(a.get("dist",{}).get(3,0) > len(optimal_rows)*0.01 for a in rate_agg)
    k3_dH_met = any(np.mean([r["dH"] for r in k3_rows if abs(r["rate"]-rate)<1e-6]) > 0.05
                     for rate in RATE_GRID
                     if [r for r in k3_rows if abs(r["rate"]-rate)<1e-6])

    txt = f"""ESDE Genesis v1.9b — Revised k* Selection Conclusion
======================================================
Revision: k=3 uses Island Scale (None/WeakOnly/Mid+) instead of size_mid_bin
          Drift stats use Δdrift (difference) primary, guarded ratio secondary

k* Distribution:
{chr(10).join(f'  k={k}: {k_star_dist.get(k,0)} ({k_star_dist.get(k,0)/max(len(optimal_rows),1)*100:.1f}%)' for k in K_LEVELS)}

Per-rate:
{chr(10).join(f'  rate={a["rate"]}: k*={a["dom_k"]} J={a["mJ"]:.3f} types={a["mT"]:.1f}' for a in rate_agg)}

k=3 Revival:
  Island Scale dist: {dict(qa_scale)}
  k=3 selected: {'YES' if k3_revived else 'NO (still dominated)'}
  ΔH(k3-k2) > 0.05: {'YES' if k3_dH_met else 'NO'}

Intrusion Drift (stabilized):
  Uses Δdrift = drift_hit - drift_nohit (no division instability)
  Guard triggered: {sum(1 for r in intr_rows if r.get('guard_triggered'))} times
"""
    with open(OUTPUT_DIR/"v19b_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
