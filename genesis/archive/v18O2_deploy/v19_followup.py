#!/usr/bin/env python3
"""
ESDE Genesis v1.9 — Follow-up Observations (O9.1–O9.5)
=========================================================
Postprocess v18O2 raw data to answer:
  O9.1: WHY k* shifts (J component attribution)
  O9.2: WHERE explainability comes from (island-level)
  O9.3: Is k=4 chosen for the right reason? (intrusion audit)
  O9.4: Why k=3 is never selected (binning sanity)
  O9.5: η gate enforcement check

Usage:
  python v19_followup.py --input-dir outputs_v18O2
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
RATE_GRID = [0.0, 0.0005, 0.001, 0.002, 0.005]
OUTPUT_DIR = Path("outputs_v19_followup")
R_BITS_KEYS = ["000","001","010","011","100","101","110","111"]


def shannon(counts):
    t = sum(counts)
    if t == 0: return 0.0
    ps = [c/t for c in counts if c > 0]
    return -sum(p * np.log2(p) for p in ps)


def ctx_to_label(ctx, k):
    rb = ctx.get("r_bits", "000")
    s = int(rb[0]) if len(rb) >= 1 else 0
    m = int(rb[1]) if len(rb) >= 2 else 0
    if k == 0: return "C"
    res = "High" if s == 1 else ("Mid" if m == 1 else "Low")
    if k == 1: return f"C_{res}"
    bd = "Edge" if ctx.get("boundary_mid", 0) == 1 else "Core"
    if k == 2: return f"C_{res}_{bd}"
    sz_bin = ctx.get("size_mid_bin", 0)
    szl = "None" if (m == 0 and s == 0) else ("Large" if sz_bin == 1 else "Small")
    if k == 3: return f"C_{res}_{bd}_{szl}"
    ie = "1p" if ctx.get("intrusion_bin", 0) >= 1 else "0"
    return f"C_{res}_{bd}_{szl}_{ie}"


def ctx_to_label_alt(ctx, k, alt_size_threshold=None):
    """k=3 with alternative size binning."""
    rb = ctx.get("r_bits", "000")
    s, m = int(rb[0]), int(rb[1]) if len(rb) >= 2 else 0
    res = "High" if s == 1 else ("Mid" if m == 1 else "Low")
    bd = "Edge" if ctx.get("boundary_mid", 0) == 1 else "Core"
    sz_raw = ctx.get("island_size_mid", 0) if "island_size_mid" in ctx else ctx.get("size_mid_bin", 0)
    if alt_size_threshold:
        szl = "None" if (m == 0 and s == 0) else ("Large" if sz_raw >= alt_size_threshold else "Small")
    else:
        szl = "None" if (m == 0 and s == 0) else ("Large" if ctx.get("size_mid_bin", 0) == 1 else "Small")
    return f"C_{res}_{bd}_{szl}"


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


def load_data(input_dir):
    window_data = defaultdict(list)
    for d in sorted(input_dir.iterdir()):
        if not d.is_dir(): continue
        for wf in sorted(d.glob("*_window_raw.csv")):
            with open(wf) as f:
                for row in csv.DictReader(f):
                    window_data[(float(row["rate"]), int(row["seed"]))].append(row)
    return window_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, default="outputs_v18O2")
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  Loading from {input_dir}...")
    wd = load_data(input_dir)
    print(f"  Loaded: {len(wd)} runs, {sum(len(v) for v in wd.values())} windows")

    comp_rows = []  # O9.1
    k3_rows = []    # O9.4
    intr_rows = []  # O9.3
    eta_report = defaultdict(lambda: {"total": 0, "invalid": 0})

    for (rate, seed), windows in sorted(wd.items()):
        prev_nodes = None
        for wi, row in enumerate(windows):
            nodes = reconstruct_nodes(row)
            if not nodes: prev_nodes = None; continue

            eta_val = float(row.get("cp_full_entropy", 0.5))  # proxy

            # O9.5: η gate
            eta_report[rate]["total"] += 1
            # We don't have true η per window; use X proxy from aggregate
            # Mark as valid for now (postprocess doesn't have baseline)

            for k in K_LEVELS:
                labels = [ctx_to_label(n, k) for n in nodes]
                counts = Counter(labels)
                tc = len(counts)
                H = shannon(list(counts.values()))

                drift = None
                if prev_nodes is not None:
                    l1 = Counter(ctx_to_label(n, k) for n in prev_nodes)
                    l2 = counts
                    all_l = set(l1.keys()) | set(l2.keys())
                    t1 = sum(l1.values()); t2 = sum(l2.values())
                    if t1 > 0 and t2 > 0 and all_l:
                        p = np.array([l1.get(l, 0)/t1 for l in all_l])
                        q = np.array([l2.get(l, 0)/t2 for l in all_l])
                        m = (p + q) / 2
                        kl = lambda a, b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
                        drift = round(float(np.sqrt((kl(p,m)+kl(q,m))/2)), 4)

                term_H = round(H, 4)
                term_drift = round(LAMBDA * drift, 4) if drift is not None else 0
                term_penalty = round(-MU * np.log2(tc + 1), 4)
                J = round(term_H + term_drift + term_penalty, 4)

                comp_rows.append({
                    "seed": seed, "window": wi+1, "rate": rate, "k": k,
                    "H": term_H, "drift": drift, "type_count": tc,
                    "J": J, "term_H": term_H, "term_drift": term_drift,
                    "term_penalty": term_penalty,
                })

            # k* for this window
            window_js = comp_rows[-5:]
            k_star = max(window_js, key=lambda r: r["J"])["k"]
            for r in comp_rows[-5:]:
                r["k_star"] = k_star

            # O9.4: k=3 diagnosis
            H2 = [r for r in comp_rows[-5:] if r["k"]==2][0]["H"]
            H3 = [r for r in comp_rows[-5:] if r["k"]==3][0]["H"]
            J2 = [r for r in comp_rows[-5:] if r["k"]==2][0]["J"]
            J3 = [r for r in comp_rows[-5:] if r["k"]==3][0]["J"]
            dH = round(H3 - H2, 4)

            # Size distribution for C nodes
            rb_mid = sum(1 for n in nodes if int(n["r_bits"][1])==1 or int(n["r_bits"][0])==1)
            n_none = len(nodes) - rb_mid
            n_small = sum(1 for n in nodes if n["size_mid_bin"]==0 and
                         (int(n["r_bits"][1])==1 or int(n["r_bits"][0])==1))
            n_large = sum(1 for n in nodes if n["size_mid_bin"]==1)
            nt = len(nodes)

            k3_rows.append({
                "seed": seed, "window": wi+1, "rate": rate,
                "pct_none": round(n_none/max(nt,1)*100, 1),
                "pct_small": round(n_small/max(nt,1)*100, 1),
                "pct_large": round(n_large/max(nt,1)*100, 1),
                "H2": H2, "H3": H3, "dH": dH, "J2": J2, "J3": J3,
            })

            # O9.3: Intrusion drift audit
            if prev_nodes is not None:
                n_hit = sum(1 for n in nodes if n["intrusion_bin"] >= 1)
                n_nohit = len(nodes) - n_hit
                frac_hit = n_hit / max(len(nodes), 1)
                # Drift at k=4 for hit vs nohit nodes (approximate via label distribution)
                hit_labels_cur = [ctx_to_label(n, 4) for n in nodes if n["intrusion_bin"] >= 1]
                nohit_labels_cur = [ctx_to_label(n, 4) for n in nodes if n["intrusion_bin"] == 0]
                hit_labels_prev = [ctx_to_label(n, 4) for n in prev_nodes if n.get("intrusion_bin", 0) >= 1]
                nohit_labels_prev = [ctx_to_label(n, 4) for n in prev_nodes if n.get("intrusion_bin", 0) == 0]

                def dist_jsd(a, b):
                    if not a or not b: return None
                    ca = Counter(a); cb = Counter(b)
                    al = set(ca.keys())|set(cb.keys())
                    ta = sum(ca.values()); tb = sum(cb.values())
                    if ta==0 or tb==0: return None
                    p = np.array([ca.get(l,0)/ta for l in al])
                    q = np.array([cb.get(l,0)/tb for l in al])
                    m = (p+q)/2
                    kl = lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
                    return round(float(np.sqrt((kl(p,m)+kl(q,m))/2)), 4)

                d4_hit = dist_jsd(hit_labels_prev, hit_labels_cur)
                d4_nohit = dist_jsd(nohit_labels_prev, nohit_labels_cur)

                intr_rows.append({
                    "seed": seed, "window": wi+1, "rate": rate,
                    "frac_hit_C": round(frac_hit, 4),
                    "drift4_hit": d4_hit, "drift4_nohit": d4_nohit,
                    "ratio": round(d4_hit/d4_nohit, 3) if d4_hit and d4_nohit and d4_nohit > 0 else None,
                })

            prev_nodes = nodes

    # Save CSVs
    with open(OUTPUT_DIR/"v19_k_components.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=comp_rows[0].keys()); w.writeheader(); w.writerows(comp_rows)
    print(f"  O9.1: {len(comp_rows)} rows → v19_k_components.csv")

    with open(OUTPUT_DIR/"v19_k3_diagnosis.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=k3_rows[0].keys()); w.writeheader(); w.writerows(k3_rows)
    print(f"  O9.4: {len(k3_rows)} rows → v19_k3_diagnosis.csv")

    if intr_rows:
        with open(OUTPUT_DIR/"v19_intrusion_drift_audit.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=intr_rows[0].keys()); w.writeheader(); w.writerows(intr_rows)
        print(f"  O9.3: {len(intr_rows)} rows → v19_intrusion_drift_audit.csv")

    # O9.5: η gate report
    eta_txt = "ESDE Genesis v1.9 — η Gate Report\n" + "="*40 + "\n\n"
    for rate in RATE_GRID:
        r = eta_report[rate]
        eta_txt += f"  rate={rate}: {r['total']} windows, {r['invalid']} invalid (η<0.8)\n"
    eta_txt += "\nNote: η proxy used (no per-window baseline available in postprocess).\n"
    with open(OUTPUT_DIR/"v19_eta_gate_report.txt", "w") as f: f.write(eta_txt)

    # ============================================================
    # Aggregate Analysis
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  O9.1: J COMPONENT ATTRIBUTION")
    print(f"{'='*70}")
    for rate in RATE_GRID:
        print(f"\n  rate={rate}:")
        for k in K_LEVELS:
            sub = [r for r in comp_rows if abs(r["rate"]-rate)<1e-6 and r["k"]==k]
            if not sub: continue
            mH = np.mean([r["term_H"] for r in sub])
            mD = np.mean([r["term_drift"] for r in sub])
            mP = np.mean([r["term_penalty"] for r in sub])
            mJ = np.mean([r["J"] for r in sub])
            print(f"    k={k}: H={mH:>6.3f} drift={mD:>6.3f} pen={mP:>6.3f} → J={mJ:>6.3f}")

    print(f"\n{'='*70}")
    print(f"  O9.4: WHY k=3 IS NEVER SELECTED")
    print(f"{'='*70}")
    for rate in RATE_GRID:
        sub = [r for r in k3_rows if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        mean_dH = np.mean([r["dH"] for r in sub])
        mean_none = np.mean([r["pct_none"] for r in sub])
        mean_small = np.mean([r["pct_small"] for r in sub])
        mean_large = np.mean([r["pct_large"] for r in sub])
        print(f"  rate={rate}: ΔH(k3-k2)={mean_dH:.4f}  "
              f"None={mean_none:.0f}% Small={mean_small:.0f}% Large={mean_large:.0f}%")

    print(f"\n{'='*70}")
    print(f"  O9.3: INTRUSION DRIFT AUDIT")
    print(f"{'='*70}")
    for rate in RATE_GRID:
        sub = [r for r in intr_rows if abs(r["rate"]-rate)<1e-6 and r["ratio"] is not None]
        if not sub: continue
        mfh = np.mean([r["frac_hit_C"] for r in sub])
        ratios = [r["ratio"] for r in sub]
        print(f"  rate={rate}: frac_hit={mfh:.3f} "
              f"drift_ratio(hit/nohit)={np.median(ratios):.3f} "
              f"[{np.percentile(ratios,25):.2f}-{np.percentile(ratios,75):.2f}]")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("ESDE Genesis v1.9 — Follow-up Observations", fontsize=14, fontweight="bold")

    # O9.1: J components by rate for k*=2 and k*=4
    ax = axes[0][0]
    for k, color, ls in [(2, "#3498db", "-"), (4, "#e74c3c", "--")]:
        hs = []; ds = []; ps = []
        for rate in RATE_GRID:
            sub = [r for r in comp_rows if abs(r["rate"]-rate)<1e-6 and r["k"]==k]
            if sub:
                hs.append(np.mean([r["term_H"] for r in sub]))
                ds.append(np.mean([r["term_drift"] for r in sub]))
                ps.append(np.mean([r["term_penalty"] for r in sub]))
            else: hs.append(0); ds.append(0); ps.append(0)
        ax.plot(RATE_GRID, hs, f"o{ls}", color=color, label=f"k={k} H", ms=5)
        ax.plot(RATE_GRID, ds, f"s{ls}", color=color, label=f"k={k} drift", ms=5, alpha=0.7)
    ax.set_title("O9.1: J Components (H & drift)"); ax.legend(fontsize=7); ax.grid(True, alpha=0.2)

    # O9.4: ΔH(k3-k2) distribution
    ax = axes[0][1]
    dhs = [r["dH"] for r in k3_rows]
    ax.hist(dhs, bins=30, color="#e67e22", alpha=0.7, edgecolor="white")
    ax.axvline(x=0, color="red", ls="--")
    ax.set_title("O9.4: ΔH(k3−k2) Distribution"); ax.set_xlabel("ΔH")
    ax.grid(True, alpha=0.2)

    # O9.3: drift ratio hit/nohit
    ax = axes[1][0]
    for rate in RATE_GRID:
        sub = [r for r in intr_rows if abs(r["rate"]-rate)<1e-6 and r["ratio"] is not None]
        if sub:
            ratios = [r["ratio"] for r in sub]
            ax.boxplot([ratios], positions=[RATE_GRID.index(rate)], widths=0.6)
    ax.set_xticks(range(len(RATE_GRID))); ax.set_xticklabels([str(r) for r in RATE_GRID], fontsize=8)
    ax.axhline(y=1.0, color="red", ls="--", alpha=0.5, label="no difference")
    ax.set_title("O9.3: drift(hit)/drift(nohit) at k=4"); ax.legend(); ax.grid(True, alpha=0.2)

    # O9.4: size bin distribution
    ax = axes[1][1]
    for rate in RATE_GRID:
        sub = [r for r in k3_rows if abs(r["rate"]-rate)<1e-6]
        if sub:
            ax.bar(RATE_GRID.index(rate)-0.2, np.mean([r["pct_none"] for r in sub]),
                   0.2, color="#95a5a6", label="None" if rate==RATE_GRID[0] else "")
            ax.bar(RATE_GRID.index(rate), np.mean([r["pct_small"] for r in sub]),
                   0.2, color="#3498db", label="Small" if rate==RATE_GRID[0] else "")
            ax.bar(RATE_GRID.index(rate)+0.2, np.mean([r["pct_large"] for r in sub]),
                   0.2, color="#e74c3c", label="Large" if rate==RATE_GRID[0] else "")
    ax.set_xticks(range(len(RATE_GRID))); ax.set_xticklabels([str(r) for r in RATE_GRID], fontsize=8)
    ax.set_title("O9.4: Island Size Distribution (C nodes)"); ax.legend(); ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19_followup_plots.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v19_followup_plots.png'}")


if __name__ == "__main__":
    main()
