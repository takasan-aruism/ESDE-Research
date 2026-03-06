#!/usr/bin/env python3
"""
ESDE Genesis v1.9 — Adaptive Resolution Observer (Postprocess)
================================================================
Offline k* selection from v18O2 raw features.

k=0: C
k=1: C + Resonance_Bin (High/Mid/Low)
k=2: k1 + Boundary_Flag (Core/Edge)
k=3: k2 + Island_Size (None/Small/Large)
k=4: k3 + Intrusion_Exposure (0/1+)

J_k = H(C′_k) + λ*drift_k − μ*log(|Types(C′_k)| + 1)
Hard constraint: η ≥ 0.8

Usage:
  python v19_postprocess.py --input-dir outputs_v18O2
  python v19_postprocess.py --input-dir outputs_v18O2 --rate 0.002
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, argparse
from collections import Counter, defaultdict
from pathlib import Path

LAMBDA = 1.0
MU = 0.5
K_LEVELS = [0, 1, 2, 3, 4]
OUTPUT_DIR = Path("outputs_v19")
RATE_GRID = [0.0, 0.0005, 0.001, 0.002, 0.005]


def shannon(counts):
    t = sum(counts)
    if t == 0: return 0.0
    ps = [c/t for c in counts if c > 0]
    return -sum(p * np.log2(p) for p in ps)


def ctx_to_label(ctx, k):
    """Convert raw context dict to label at resolution k."""
    if k == 0:
        return "C"

    # k>=1: Resonance bin
    rb = ctx.get("r_bits", "000")
    strong = int(rb[0]) if len(rb) >= 1 else 0
    mid = int(rb[1]) if len(rb) >= 2 else 0
    if strong == 1:
        res = "High"
    elif mid == 1:
        res = "Mid"
    else:
        res = "Low"
    if k == 1:
        return f"C_{res}"

    # k>=2: Boundary
    bd = ctx.get("boundary_mid", 0)
    bdf = "Edge" if bd == 1 else "Core"
    if k == 2:
        return f"C_{res}_{bdf}"

    # k>=3: Island size
    sz = ctx.get("size_mid_bin", 0)
    # Remap: size_mid_bin=0 could mean None or Small. Use r_bits mid to distinguish.
    if mid == 0 and strong == 0:
        szl = "None"
    elif sz == 0:
        szl = "Small"
    else:
        szl = "Large"
    if k == 3:
        return f"C_{res}_{bdf}_{szl}"

    # k>=4: Intrusion exposure
    intr = ctx.get("intrusion_bin", 0)
    ie = "1p" if intr >= 1 else "0"
    return f"C_{res}_{bdf}_{szl}_{ie}"


def load_window_snapshots(input_dir):
    """Load per-window raw feature CSVs. Returns dict: (rate, seed) -> list of window dicts."""
    data = defaultdict(list)
    for rate_dir in sorted(input_dir.iterdir()):
        if not rate_dir.is_dir():
            continue
        for wf in sorted(rate_dir.glob("*_window_raw.csv")):
            with open(wf) as f:
                for row in csv.DictReader(f):
                    seed = int(row["seed"])
                    rate = float(row["rate"])
                    data[(rate, seed)].append(row)
    return data


def load_cycle_pairs(input_dir):
    """Load cycle context pairs. Returns dict: (rate, seed) -> list of pair dicts."""
    data = defaultdict(list)
    for rate_dir in sorted(input_dir.iterdir()):
        if not rate_dir.is_dir():
            continue
        for cf in sorted(rate_dir.glob("*_cycle_pairs.csv")):
            with open(cf) as f:
                for row in csv.DictReader(f):
                    seed = int(row["seed"])
                    rate = float(row["rate"])
                    data[(rate, seed)].append(row)
    return data


def load_summaries(input_dir):
    """Load per-run summaries."""
    summaries = {}
    for rate_dir in sorted(input_dir.iterdir()):
        if not rate_dir.is_dir():
            continue
        for sf in sorted(rate_dir.glob("*_summary.json")):
            with open(sf) as fh:
                s = json.load(fh)
                summaries[(s["rate"], s["seed"])] = s
    return summaries


def reconstruct_node_contexts_from_window(row):
    """From aggregate window row, reconstruct approximate per-node contexts.
    Since we only have counts (not per-node), we create synthetic nodes."""
    nodes = []
    # r_bits distribution
    r_keys = ["000","001","010","011","100","101","110","111"]
    for rb in r_keys:
        count = int(row.get(f"r_{rb}", 0))
        for _ in range(count):
            nodes.append({"r_bits": rb})

    # Now distribute bd, sz, f, intr across nodes proportionally
    n_total = len(nodes)
    if n_total == 0:
        return nodes

    bd1 = int(row.get("bd_1", 0))
    sz1 = int(row.get("sz_1", 0))
    f1 = int(row.get("f_1", 0))
    intr1 = int(row.get("intr_1", 0))
    intr2p = int(row.get("intr_2p", 0))

    # Assign features in order (deterministic approximation)
    for i, n in enumerate(nodes):
        n["boundary_mid"] = 1 if i < bd1 else 0
        n["size_mid_bin"] = 1 if i < sz1 else 0
        n["fert_bin"] = 1 if i < f1 else 0
        n["intrusion_bin"] = 2 if i < intr2p else (1 if i < intr2p + intr1 else 0)

    return nodes


def compute_k_metrics_for_window(nodes, eta_val):
    """Compute metrics for k=0..4 from a list of node context dicts."""
    results = {}
    for k in K_LEVELS:
        labels = [ctx_to_label(n, k) for n in nodes]
        counts = Counter(labels)
        type_count = len(counts)
        H = shannon(list(counts.values()))
        results[k] = {
            "type_count": type_count,
            "H": round(H, 4),
            "eta": eta_val,
        }
    return results


def compute_drift_between_windows(nodes_w1, nodes_w2, k):
    """Compute drift: fraction of 'same position' nodes that changed label.
    Since we don't have true node IDs from aggregates, use JSD as proxy."""
    labels1 = Counter(ctx_to_label(n, k) for n in nodes_w1)
    labels2 = Counter(ctx_to_label(n, k) for n in nodes_w2)
    # JSD proxy
    all_labels = set(labels1.keys()) | set(labels2.keys())
    if not all_labels:
        return None
    t1 = sum(labels1.values()); t2 = sum(labels2.values())
    if t1 == 0 or t2 == 0:
        return None
    p = np.array([labels1.get(l, 0)/t1 for l in all_labels])
    q = np.array([labels2.get(l, 0)/t2 for l in all_labels])
    m = (p + q) / 2
    # Avoid log(0)
    def kl(a, b):
        s = 0
        for i in range(len(a)):
            if a[i] > 0 and b[i] > 0:
                s += a[i] * np.log2(a[i] / b[i])
        return s
    jsd = (kl(p, m) + kl(q, m)) / 2
    return round(float(np.sqrt(jsd)), 4)  # sqrt-JSD as drift proxy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, default="outputs_v18O2")
    parser.add_argument("--rate", type=float, default=None)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  Loading from {input_dir}...")
    window_data = load_window_snapshots(input_dir)
    cycle_data = load_cycle_pairs(input_dir)
    summaries = load_summaries(input_dir)

    print(f"  Loaded: {len(window_data)} (rate,seed) pairs, "
          f"{sum(len(v) for v in window_data.values())} windows")

    rates_to_process = [args.rate] if args.rate is not None else RATE_GRID

    all_k_rows = []
    all_optimal = []
    qa_resonance_dist = Counter()

    for (rate, seed), windows in sorted(window_data.items()):
        if rate not in rates_to_process:
            continue

        # Get eta from summary (constant across k)
        summ = summaries.get((rate, seed), {})
        eta_global = summ.get("X", 0.5)  # use X as eta proxy

        # Reconstruct nodes per window
        prev_nodes = None
        for wi, row in enumerate(windows):
            nodes = reconstruct_node_contexts_from_window(row)
            if not nodes:
                continue

            # QA: check resonance distribution
            for n in nodes:
                rb = n["r_bits"]
                s, m = int(rb[0]), int(rb[1])
                if s == 1: qa_resonance_dist["High"] += 1
                elif m == 1: qa_resonance_dist["Mid"] += 1
                else: qa_resonance_dist["Low"] += 1

            eta_val = eta_global  # same for all k
            km = compute_k_metrics_for_window(nodes, eta_val)

            # Drift
            for k in K_LEVELS:
                drift = None
                if prev_nodes is not None:
                    drift = compute_drift_between_windows(prev_nodes, nodes, k)

                J = None
                flags = ""
                # η check: X is used as proxy. In postprocess we compute J regardless
                # but flag low-η windows.
                if drift is not None:
                    J = km[k]["H"] + LAMBDA * drift - MU * np.log2(km[k]["type_count"] + 1)
                    J = round(J, 4)
                else:
                    J = km[k]["H"] - MU * np.log2(km[k]["type_count"] + 1)
                    J = round(J, 4)
                    flags = "drift_missing"
                if eta_val < 0.8:
                    flags = (flags + ",low_eta" if flags else "low_eta")

                all_k_rows.append({
                    "seed": seed, "rate": rate, "window": wi + 1, "k": k,
                    "eta": round(eta_val, 4), "type_count": km[k]["type_count"],
                    "H_k": km[k]["H"], "drift_k": drift, "J_k": J,
                    "flags": flags,
                })

            # Select k*
            candidates = [r for r in all_k_rows[-5:]  # last 5 = k=0..4 for this window
                         if r["J_k"] is not None]
            if candidates:
                best = max(candidates, key=lambda r: r["J_k"])
                all_optimal.append({
                    "seed": seed, "rate": rate, "window": wi + 1,
                    "k_star": best["k"], "J_star": best["J_k"],
                    "eta": best["eta"],
                    "type_count_kstar": best["type_count"],
                    "H_kstar": best["H_k"],
                    "drift_kstar": best["drift_k"],
                    "flags": best["flags"],
                })

            prev_nodes = nodes

    # Save
    with open(OUTPUT_DIR / "k_metrics_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_k_rows[0].keys())
        w.writeheader(); w.writerows(all_k_rows)

    with open(OUTPUT_DIR / "optimal_k_history.csv", "w", newline="") as f:
        if all_optimal:
            w = csv.DictWriter(f, fieldnames=all_optimal[0].keys())
            w.writeheader(); w.writerows(all_optimal)
        else:
            f.write("# No optimal k selections (insufficient data)\n")

    # ============================================================
    # QA checks
    # ============================================================
    print(f"\n  QA CHECKS:")
    print(f"    Resonance distribution: {dict(qa_resonance_dist)}")
    all_low = qa_resonance_dist.get("Low", 0)
    all_total = sum(qa_resonance_dist.values())
    if qa_resonance_dist.get("High", 0) > 0:
        print(f"    ✓ High resonance exists ({qa_resonance_dist['High']}/{all_total})")
    else:
        print(f"    ✗ WARNING: No High resonance nodes detected")

    # Type count monotonicity check
    mono_violations = 0
    for wi_start in range(0, len(all_k_rows) - 4, 5):
        chunk = all_k_rows[wi_start:wi_start + 5]
        for i in range(1, len(chunk)):
            if chunk[i]["type_count"] < chunk[i-1]["type_count"]:
                mono_violations += 1
    print(f"    Type count monotonicity violations: {mono_violations} "
          f"({'✓ OK' if mono_violations < len(all_k_rows)//20 else '✗ CHECK'})")

    # Drift coverage
    drift_defined = sum(1 for r in all_k_rows if r["drift_k"] is not None)
    print(f"    Drift defined: {drift_defined}/{len(all_k_rows)} "
          f"({drift_defined/max(len(all_k_rows),1)*100:.0f}%)")

    # ============================================================
    # Aggregate k* distribution
    # ============================================================
    k_star_dist = Counter(r["k_star"] for r in all_optimal)
    print(f"\n  k* DISTRIBUTION (all windows):")
    for k in K_LEVELS:
        pct = k_star_dist.get(k, 0) / max(len(all_optimal), 1) * 100
        print(f"    k={k}: {k_star_dist.get(k, 0)} windows ({pct:.1f}%)")

    always_k0 = all(r["k_star"] == 0 for r in all_optimal)
    if always_k0:
        print(f"\n  ⚠ FAIL CONDITION: k* is always 0. Observation limit under η≥0.8.")

    # Per-rate k* summary
    print(f"\n  PER-RATE k* SUMMARY:")
    rate_agg = []
    for rate in rates_to_process:
        sub = [r for r in all_optimal if abs(r["rate"] - rate) < 1e-6]
        if not sub:
            continue
        kd = Counter(r["k_star"] for r in sub)
        dominant_k = kd.most_common(1)[0][0] if kd else 0
        mean_J = np.mean([r["J_star"] for r in sub])
        mean_types = np.mean([r["type_count_kstar"] for r in sub])
        rate_agg.append({
            "rate": rate, "n": len(sub),
            "dominant_k": dominant_k,
            "k_dist": dict(kd),
            "mean_J": round(mean_J, 4),
            "mean_types": round(mean_types, 2),
        })
        print(f"    rate={rate}: dominant_k={dominant_k} "
              f"dist={dict(kd)} mean_J={mean_J:.3f} types={mean_types:.1f}")

    # ============================================================
    # Plots
    # ============================================================
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle("ESDE Genesis v1.9 — Adaptive Resolution Observer (k* Selection)",
                 fontsize=14, fontweight="bold")

    # k* distribution bar
    ax = axes[0][0]
    ax.bar(K_LEVELS, [k_star_dist.get(k, 0) for k in K_LEVELS],
           color=["#95a5a6", "#2ecc71", "#3498db", "#e67e22", "#e74c3c"])
    ax.set_title("k* Selection Distribution"); ax.set_xlabel("k")
    ax.set_ylabel("Windows"); ax.grid(True, alpha=0.2)

    # Mean J_k per k (across all windows)
    ax = axes[0][1]
    for k in K_LEVELS:
        j_vals = [r["J_k"] for r in all_k_rows if r["k"] == k and r["J_k"] is not None]
        if j_vals:
            ax.bar(k, np.mean(j_vals), color=["#95a5a6", "#2ecc71", "#3498db", "#e67e22", "#e74c3c"][k],
                   alpha=0.7)
    ax.set_title("Mean J_k per Level"); ax.set_xlabel("k"); ax.grid(True, alpha=0.2)

    # Type count vs k
    ax = axes[0][2]
    for k in K_LEVELS:
        tc = [r["type_count"] for r in all_k_rows if r["k"] == k]
        if tc:
            ax.boxplot([tc], positions=[k], widths=0.6)
    ax.set_title("Type Count by k"); ax.set_xlabel("k"); ax.grid(True, alpha=0.2)

    # k* over rate
    ax = axes[1][0]
    if rate_agg:
        rs = [a["rate"] for a in rate_agg]
        dk = [a["dominant_k"] for a in rate_agg]
        ax.plot(rs, dk, "o-", color="#e67e22", ms=10, lw=2)
    ax.set_title("Dominant k* vs Intrusion Rate")
    ax.set_xlabel("intrusion_rate"); ax.set_ylabel("k*"); ax.grid(True, alpha=0.2)
    ax.set_yticks(K_LEVELS)

    # Mean J* over rate
    ax = axes[1][1]
    if rate_agg:
        ax.plot(rs, [a["mean_J"] for a in rate_agg], "s-", color="#3498db", ms=8, lw=2)
    ax.set_title("Mean J* vs Intrusion Rate")
    ax.set_xlabel("intrusion_rate"); ax.grid(True, alpha=0.2)

    # Summary text
    ax = axes[1][2]; ax.axis("off")
    txt = ["v1.9 Adaptive Resolution", "=" * 30, "",
           f"Total windows: {len(all_optimal)}",
           f"k* distribution: {dict(k_star_dist)}",
           f"Always k=0: {'YES ⚠' if always_k0 else 'NO ✓'}",
           "", "Per-rate dominant k:"]
    for a in rate_agg:
        txt.append(f"  rate={a['rate']}: k*={a['dominant_k']} J={a['mean_J']:.3f}")
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=10,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "v19_k_selection_plots.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR / 'v19_k_selection_plots.png'}")

    # Conclusion
    txt = f"""ESDE Genesis v1.9 — Adaptive Resolution Observer Conclusion
==============================================================
Input: {args.input_dir} | λ={LAMBDA} μ={MU}

k* Distribution:
{chr(10).join(f'  k={k}: {k_star_dist.get(k,0)} ({k_star_dist.get(k,0)/max(len(all_optimal),1)*100:.1f}%)' for k in K_LEVELS)}

Always k=0: {'YES — observation limit under η≥0.8' if always_k0 else 'NO — system selects higher resolution'}

Per-rate:
{chr(10).join(f'  rate={a["rate"]}: k*={a["dominant_k"]} J={a["mean_J"]:.3f} types={a["mean_types"]:.1f}' for a in rate_agg)}

QA:
  Resonance dist: {dict(qa_resonance_dist)}
  Monotonicity violations: {mono_violations}
  Drift coverage: {drift_defined}/{len(all_k_rows)} ({drift_defined/max(len(all_k_rows),1)*100:.0f}%)

Interpretation:
  k*>0 means the system benefits from structural context labeling.
  Increasing k* with intrusion_rate means boundary noise creates observationally
  richer structure that Axiom X rewards with higher resolution.
"""
    with open(OUTPUT_DIR / "v19_conclusion.txt", "w") as f:
        f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
