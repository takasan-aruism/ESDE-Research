#!/usr/bin/env python3
"""
v9.13 Analyzer — S>=0.20 撤去の影響評価
==========================================
Stage 1: tau=50 単独分析 (v9.11 short 48 seeds との比較)
Stage 2: tau=50 vs tau=100 比較 (--compare フラグ)

USAGE:
  # Stage 1
  python analyze_v913.py --tau 50

  # Stage 2 (tau=100 完了後)
  python analyze_v913.py --tau 100
  python analyze_v913.py --compare

スキーマ対応:
  v9.13 per_subject = v9.11 per_subject + v913_{tau,birth_age_r_min,...} 5列
  pulse_log は v9.11 と同一スキーマ
  per_label は v9.11 と同一スキーマ (label_id = cognitive_id)
"""

import csv, argparse, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict, Counter

# ═══════════════════════════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════════════════════════
_SCRIPT_DIR = Path(__file__).resolve().parent
_V911_SHORT = _SCRIPT_DIR.parent / "v911" / "diag_v911_capture_short"
_V911_LONG  = _SCRIPT_DIR.parent / "v911" / "diag_v911_capture_long"
_OUT_BASE   = _SCRIPT_DIR / "v913_analysis"

# v9.11 reference values
V911_REF = {
    "capture_rate_mean": 0.38,
    "bgen_by_ncore": {2: 12, 3: 19, 4: 26, 5: 34},
    "capture_by_ncore": {2: 0.464, 3: 0.368, 4: 0.308, 5: 0.292},
    "axis_phase_r_pct": 72,
    "l06_count": 114,
    "l06_capture": 0.307,
    "l06_ncore5_pct": 61,
}
L06_THRESHOLD = 6  # lifespan >= 6 windows


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def safe_float(v, default=None):
    try:
        if v in ("unformed", "", "inf", "nan", None):
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_int(v, default=None):
    try:
        if v in ("unformed", "", None):
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════
def load_subjects(base_dir, n_seeds=None):
    """Load per_subject CSVs from all seeds."""
    subj_dir = Path(base_dir) / "subjects"
    files = sorted(subj_dir.glob("per_subject_seed*.csv"))
    if n_seeds:
        files = files[:n_seeds]
    all_rows = []
    for f in files:
        all_rows.extend(read_csv(f))
    return all_rows, len(files)


def load_labels(base_dir, n_seeds=None):
    """Load per_label CSVs from all seeds."""
    label_dir = Path(base_dir) / "labels"
    files = sorted(label_dir.glob("per_label_seed*.csv"))
    if n_seeds:
        files = files[:n_seeds]
    all_rows = []
    for f in files:
        all_rows.extend(read_csv(f))
    return all_rows, len(files)


def load_pulse_logs(base_dir, n_seeds=None):
    """Load pulse_log CSVs from all seeds."""
    pulse_dir = Path(base_dir) / "pulse"
    files = sorted(pulse_dir.glob("pulse_log_seed*.csv"))
    if n_seeds:
        files = files[:n_seeds]
    all_rows = []
    for f in files:
        all_rows.extend(read_csv(f))
    return all_rows, len(files)


# ═══════════════════════════════════════════════════════════════
# Analysis Functions
# ═══════════════════════════════════════════════════════════════
def analyze_basic_stats(labels, n_seeds, tag):
    """§3.1: label count, n_core distribution, lifespan."""
    # Label count per seed
    seed_counts = Counter()
    for r in labels:
        seed_counts[r["seed"]] += 1
    counts = list(seed_counts.values())

    stats = {
        "tag": tag,
        "n_seeds": n_seeds,
        "total_labels": len(labels),
        "labels_per_seed_mean": round(np.mean(counts), 1),
        "labels_per_seed_median": round(np.median(counts), 1),
        "labels_per_seed_std": round(np.std(counts), 1),
        "labels_per_seed_min": min(counts),
        "labels_per_seed_max": max(counts),
    }

    # n_core distribution
    ncore_dist = Counter()
    for r in labels:
        nc = safe_int(r.get("n_core"))
        if nc is not None:
            ncore_dist[nc] += 1
    stats["ncore_dist"] = dict(sorted(ncore_dist.items()))

    # Lifespan
    lifespans = [safe_int(r.get("lifespan"), 0) for r in labels]
    stats["lifespan_mean"] = round(np.mean(lifespans), 2) if lifespans else 0
    stats["lifespan_median"] = round(np.median(lifespans), 1) if lifespans else 0

    # Lifespan by n_core
    ls_by_nc = defaultdict(list)
    for r in labels:
        nc = safe_int(r.get("n_core"))
        ls = safe_int(r.get("lifespan"), 0)
        if nc is not None:
            ls_by_nc[nc].append(ls)
    stats["lifespan_by_ncore"] = {
        nc: round(np.mean(v), 2) for nc, v in sorted(ls_by_nc.items())
    }

    # Birth rate per window
    birth_windows = Counter()
    for r in labels:
        bw = safe_int(r.get("birth_window"))
        if bw is not None:
            birth_windows[bw] += 1
    stats["birth_per_window"] = dict(sorted(birth_windows.items()))

    return stats


def analyze_r0_inclusion(subjects, tag):
    """§3.2: R=0 inclusion rate at birth."""
    # Use v913_birth_age_r_min: if > 0, all member links had R>0 for at least that many steps
    # For v9.11 we don't have this info directly, so we check v11_m_c_r_core
    has_v913 = "v913_birth_age_r_min" in (subjects[0] if subjects else {})

    results = {"tag": tag}

    if has_v913:
        # v9.13: check age_r_min at birth
        formed = [r for r in subjects
                  if safe_float(r.get("v913_birth_age_r_min")) is not None
                  and r.get("v913_n_member_edges", "") not in ("", "0")]
        if formed:
            all_pure = sum(1 for r in formed
                          if safe_float(r["v913_birth_age_r_min"], 0) > 0)
            results["n_formed"] = len(formed)
            results["n_pure_r_positive"] = all_pure
            results["pure_rate"] = round(all_pure / len(formed), 4)
            age_r_mins = [safe_float(r["v913_birth_age_r_min"], 0) for r in formed]
            results["age_r_min_mean"] = round(np.mean(age_r_mins), 1)
            results["age_r_min_p50"] = round(np.median(age_r_mins), 1)
        else:
            results["n_formed"] = 0
            results["pure_rate"] = None
    else:
        # v9.11: approximate via n_core - n_core=2 came from R>0 pairs (経路B)
        # but we can't directly measure R=0 inclusion from per_subject
        formed = [r for r in subjects
                  if r.get("v11_n_pulses_eval", "unformed") not in ("unformed", "")]
        ncore2 = sum(1 for r in formed if safe_int(r.get("v11_m_c_n_core")) == 2)
        results["n_formed"] = len(formed)
        results["n_ncore2_pair"] = ncore2
        results["ncore2_rate"] = round(ncore2 / len(formed), 4) if formed else 0
        results["note"] = "v9.11: R=0 inclusion cannot be directly measured; n_core=2 (経路B) rate shown as proxy"

    return results


def analyze_bgen(subjects, tag):
    """§3.3: B_Gen band structure."""
    bgen_by_nc = defaultdict(list)
    for r in subjects:
        nc = safe_int(r.get("v11_m_c_n_core"))
        bg = safe_float(r.get("v11_b_gen"))
        if nc is not None and bg is not None and bg < 100:  # filter inf
            bgen_by_nc[nc].append(bg)

    result = {"tag": tag, "bgen_stats": {}}
    for nc in sorted(bgen_by_nc.keys()):
        vals = bgen_by_nc[nc]
        result["bgen_stats"][nc] = {
            "n": len(vals),
            "mean": round(np.mean(vals), 2),
            "std": round(np.std(vals), 2),
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
            "p50": round(np.median(vals), 2),
        }
    return result


def analyze_capture(subjects, tag):
    """§3.4: capture dynamics."""
    formed = [r for r in subjects
              if r.get("v11_n_pulses_eval", "unformed") not in ("unformed", "")]

    cap_rates = [safe_float(r.get("v11_capture_rate")) for r in formed]
    cap_rates = [c for c in cap_rates if c is not None]

    result = {"tag": tag}
    result["n_formed"] = len(formed)
    result["capture_rate_mean"] = round(np.mean(cap_rates), 4) if cap_rates else None

    # By n_core
    cap_by_nc = defaultdict(list)
    delta_by_nc = defaultdict(list)
    for r in formed:
        nc = safe_int(r.get("v11_m_c_n_core"))
        cr = safe_float(r.get("v11_capture_rate"))
        d = safe_float(r.get("v11_mean_delta"))
        if nc is not None and cr is not None:
            cap_by_nc[nc].append(cr)
        if nc is not None and d is not None:
            delta_by_nc[nc].append(d)

    result["capture_by_ncore"] = {
        nc: round(np.mean(v), 4) for nc, v in sorted(cap_by_nc.items())
    }
    result["delta_by_ncore"] = {
        nc: round(np.mean(v), 4) for nc, v in sorted(delta_by_nc.items())
    }

    # Axis contribution
    dn_sum = ds_sum = dr_sum = dp_sum = 0
    count = 0
    for r in formed:
        dn = safe_float(r.get("v11_mean_d_n"))
        ds = safe_float(r.get("v11_mean_d_s"))
        dr = safe_float(r.get("v11_mean_d_r"))
        dp = safe_float(r.get("v11_mean_d_phase"))
        if all(v is not None for v in [dn, ds, dr, dp]):
            dn_sum += dn * 0.25
            ds_sum += ds * 0.25
            dr_sum += dr * 0.25
            dp_sum += dp * 0.25
            count += 1

    if count > 0:
        total = dn_sum + ds_sum + dr_sum + dp_sum
        result["axis_contrib"] = {
            "n": round(dn_sum / total * 100, 1),
            "s": round(ds_sum / total * 100, 1),
            "r": round(dr_sum / total * 100, 1),
            "phase": round(dp_sum / total * 100, 1),
        }
        result["phase_plus_r"] = round((dr_sum + dp_sum) / total * 100, 1)

    # Axis by n_core
    axis_by_nc = defaultdict(lambda: {"n": 0, "s": 0, "r": 0, "phase": 0, "count": 0})
    for r in formed:
        nc = safe_int(r.get("v11_m_c_n_core"))
        dn = safe_float(r.get("v11_mean_d_n"))
        ds = safe_float(r.get("v11_mean_d_s"))
        dr = safe_float(r.get("v11_mean_d_r"))
        dp = safe_float(r.get("v11_mean_d_phase"))
        if nc and all(v is not None for v in [dn, ds, dr, dp]):
            axis_by_nc[nc]["n"] += dn * 0.25
            axis_by_nc[nc]["s"] += ds * 0.25
            axis_by_nc[nc]["r"] += dr * 0.25
            axis_by_nc[nc]["phase"] += dp * 0.25
            axis_by_nc[nc]["count"] += 1

    result["axis_by_ncore"] = {}
    for nc in sorted(axis_by_nc.keys()):
        d = axis_by_nc[nc]
        total = d["n"] + d["s"] + d["r"] + d["phase"]
        if total > 0:
            result["axis_by_ncore"][nc] = {
                "n": round(d["n"] / total * 100, 1),
                "s": round(d["s"] / total * 100, 1),
                "r": round(d["r"] / total * 100, 1),
                "phase": round(d["phase"] / total * 100, 1),
            }

    return result


def analyze_l06(subjects, tag):
    """§3.5: long-lived group analysis."""
    formed = [r for r in subjects
              if r.get("v11_n_pulses_eval", "unformed") not in ("unformed", "")]

    # Calculate lifespan from n_pulses_eval (proxy: pulse_count / pulses_per_window)
    # Actually, use birth_window and host_lost_window/reaped_window
    long_lived = []
    short_lived = []
    for r in formed:
        bw = safe_int(r.get("birth_window"))
        hlw = safe_int(r.get("host_lost_window"))
        rw = safe_int(r.get("reaped_window"))
        end_w = hlw if hlw is not None else rw
        if bw is not None:
            if end_w is not None:
                lifespan = end_w - bw
            else:
                # Still alive — use last window as proxy
                npe = safe_int(r.get("v11_n_pulses_eval"), 0)
                # Each window has ~10 pulses (500 steps / 50 pulse_interval)
                lifespan = max(1, npe // 10) if npe > 0 else 0
            if lifespan >= L06_THRESHOLD:
                long_lived.append(r)
            elif lifespan < 3:
                short_lived.append(r)

    result = {"tag": tag, "n_long": len(long_lived), "n_short": len(short_lived)}

    if long_lived:
        nc_dist = Counter(safe_int(r.get("v11_m_c_n_core")) for r in long_lived)
        nc_dist.pop(None, None)
        result["long_ncore_dist"] = dict(sorted(nc_dist.items()))
        n5 = nc_dist.get(5, 0)
        result["long_ncore5_pct"] = round(n5 / len(long_lived) * 100, 1)

        caps = [safe_float(r.get("v11_capture_rate")) for r in long_lived]
        caps = [c for c in caps if c is not None]
        result["long_capture_mean"] = round(np.mean(caps), 4) if caps else None

        deltas = [safe_float(r.get("v11_mean_delta")) for r in long_lived]
        deltas = [d for d in deltas if d is not None]
        result["long_delta_mean"] = round(np.mean(deltas), 4) if deltas else None
    else:
        result["long_ncore_dist"] = {}
        result["long_ncore5_pct"] = 0
        result["long_capture_mean"] = None
        result["long_delta_mean"] = None

    return result


# ═══════════════════════════════════════════════════════════════
# Plotting
# ═══════════════════════════════════════════════════════════════
COLORS = {"v911": "#4477AA", "v913_50": "#EE6677", "v913_100": "#228833"}


def plot_ncore_dist(stats_v911, stats_v913, fig_dir, tau):
    """fig02: n_core distribution comparison."""
    fig, ax = plt.subplots(figsize=(8, 5))
    nc_keys = sorted(set(list(stats_v911["ncore_dist"].keys()) +
                         list(stats_v913["ncore_dist"].keys())))
    x = np.arange(len(nc_keys))
    w = 0.35
    v911_vals = [stats_v911["ncore_dist"].get(k, 0) / stats_v911["total_labels"] * 100
                 for k in nc_keys]
    v913_vals = [stats_v913["ncore_dist"].get(k, 0) / stats_v913["total_labels"] * 100
                 for k in nc_keys]
    ax.bar(x - w/2, v911_vals, w, label=f"v9.11 (48 seeds)", color=COLORS["v911"])
    ax.bar(x + w/2, v913_vals, w, label=f"v9.13 τ={tau} (24 seeds)", color=COLORS[f"v913_{tau}"])
    ax.set_xticks(x)
    ax.set_xticklabels(nc_keys)
    ax.set_xlabel("n_core")
    ax.set_ylabel("% of labels")
    ax.set_title("n_core Distribution: v9.11 vs v9.13")
    ax.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "fig02_n_core_distribution.png", dpi=150)
    plt.close()


def plot_bgen_bands(bgen_v911, bgen_v913, fig_dir, tau):
    """fig05: B_Gen boxplot by n_core."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, (data, title, color) in zip(axes, [
        (bgen_v911, "v9.11", COLORS["v911"]),
        (bgen_v913, f"v9.13 τ={tau}", COLORS[f"v913_{tau}"])
    ]):
        nc_keys = sorted(data["bgen_stats"].keys())
        box_data = []
        labels = []
        for nc in nc_keys:
            s = data["bgen_stats"][nc]
            # Approximate boxplot from stats
            labels.append(f"n={nc}\n(n={s['n']})")
        # Just show mean ± std as bar
        means = [data["bgen_stats"][nc]["mean"] for nc in nc_keys]
        stds = [data["bgen_stats"][nc]["std"] for nc in nc_keys]
        ax.bar(range(len(nc_keys)), means, yerr=stds, color=color, alpha=0.7, capsize=5)
        ax.set_xticks(range(len(nc_keys)))
        ax.set_xticklabels(labels)
        ax.set_title(title)
        ax.set_ylabel("B_Gen")
    plt.suptitle("B_Gen Band Structure by n_core")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig05_bgen_bands.png", dpi=150)
    plt.close()


def plot_capture_by_ncore(cap_v911, cap_v913, fig_dir, tau):
    """fig06: capture rate by n_core."""
    fig, ax = plt.subplots(figsize=(8, 5))
    nc_keys = sorted(set(list(cap_v911["capture_by_ncore"].keys()) +
                         list(cap_v913["capture_by_ncore"].keys())))
    x = np.arange(len(nc_keys))
    w = 0.35
    v911_vals = [cap_v911["capture_by_ncore"].get(k, 0) for k in nc_keys]
    v913_vals = [cap_v913["capture_by_ncore"].get(k, 0) for k in nc_keys]
    ax.bar(x - w/2, v911_vals, w, label="v9.11", color=COLORS["v911"])
    ax.bar(x + w/2, v913_vals, w, label=f"v9.13 τ={tau}", color=COLORS[f"v913_{tau}"])
    ax.set_xticks(x)
    ax.set_xticklabels([f"n={k}" for k in nc_keys])
    ax.set_ylabel("capture_rate")
    ax.set_title("Capture Rate by n_core")
    ax.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "fig06_capture_rate_by_ncore.png", dpi=150)
    plt.close()


def plot_axis_contribution(cap_v911, cap_v913, fig_dir, tau):
    """fig07: axis contribution stacked bar."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, (data, title) in zip(axes, [
        (cap_v911, "v9.11"),
        (cap_v913, f"v9.13 τ={tau}")
    ]):
        if "axis_contrib" not in data:
            continue
        axes_names = ["n", "s", "r", "phase"]
        vals = [data["axis_contrib"].get(a, 0) for a in axes_names]
        colors = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3"]
        ax.bar(axes_names, vals, color=colors)
        ax.set_ylabel("% contribution")
        ax.set_title(title)
        ax.set_ylim(0, 50)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)
    plt.suptitle("Axis Contribution to Δ")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig07_axis_contribution.png", dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════
def generate_report(tau, stats_v911, stats_v913, r0_v911, r0_v913,
                    bgen_v911, bgen_v913, cap_v911, cap_v913,
                    l06_v911, l06_v913, out_path):
    lines = []
    lines.append(f"# v9.13 τ={tau} Analysis Report\n")
    lines.append(f"- Date: 2026-04-17")
    lines.append(f"- v9.13: 24 seeds, τ={tau}, mat=20, track=20, steps=500")
    lines.append(f"- v9.11: 48 seeds, mat=20, track=10, steps=500\n")

    # Executive Summary
    lines.append("## 0. Executive Summary\n")
    ratio = stats_v913["labels_per_seed_mean"] / stats_v911["labels_per_seed_mean"]
    lines.append(f"- label 数: v9.11 {stats_v911['labels_per_seed_mean']}/seed → "
                 f"v9.13 {stats_v913['labels_per_seed_mean']}/seed "
                 f"(**{ratio:.1%}**, 予測 1/3={1/3:.1%})")
    if r0_v913.get("pure_rate") is not None:
        lines.append(f"- R>0 純度: v9.13 birth 時 100% R>0 = **{r0_v913['pure_rate']:.1%}**")
    lines.append(f"- capture_rate: v9.11 {cap_v911.get('capture_rate_mean','?')} → "
                 f"v9.13 {cap_v913.get('capture_rate_mean','?')}")
    lines.append(f"- phase+r 寄与: v9.11 {cap_v911.get('phase_plus_r','?')}% → "
                 f"v9.13 {cap_v913.get('phase_plus_r','?')}%")
    lines.append(f"- L06 (lifespan>=6): v9.13 {l06_v913['n_long']} cids\n")

    # §1 Setup
    lines.append("## 1. Setup\n")
    lines.append(f"| 項目 | v9.11 | v9.13 τ={tau} |")
    lines.append("|---|---|---|")
    lines.append(f"| seeds | 48 | 24 |")
    lines.append(f"| tracking_windows | 10 | 20 |")
    lines.append(f"| birth 方式 | S>=0.20 + R>0 pair | age_r>={tau} components |")
    lines.append(f"| total labels | {stats_v911['total_labels']} | {stats_v913['total_labels']} |\n")

    # §2 Basic Stats
    lines.append("## 2. Basic Statistics\n")
    lines.append("| 指標 | v9.11 | v9.13 |")
    lines.append("|---|---|---|")
    lines.append(f"| labels/seed mean | {stats_v911['labels_per_seed_mean']} | {stats_v913['labels_per_seed_mean']} |")
    lines.append(f"| labels/seed median | {stats_v911['labels_per_seed_median']} | {stats_v913['labels_per_seed_median']} |")
    lines.append(f"| labels/seed std | {stats_v911['labels_per_seed_std']} | {stats_v913['labels_per_seed_std']} |")
    lines.append(f"| lifespan mean | {stats_v911['lifespan_mean']} | {stats_v913['lifespan_mean']} |")
    lines.append(f"| lifespan median | {stats_v911['lifespan_median']} | {stats_v913['lifespan_median']} |\n")

    lines.append("### n_core 分布\n")
    lines.append("| n_core | v9.11 count (%) | v9.13 count (%) |")
    lines.append("|---|---|---|")
    all_nc = sorted(set(list(stats_v911["ncore_dist"].keys()) +
                        list(stats_v913["ncore_dist"].keys())))
    for nc in all_nc:
        c911 = stats_v911["ncore_dist"].get(nc, 0)
        c913 = stats_v913["ncore_dist"].get(nc, 0)
        p911 = round(c911 / stats_v911["total_labels"] * 100, 1) if stats_v911["total_labels"] else 0
        p913 = round(c913 / stats_v913["total_labels"] * 100, 1) if stats_v913["total_labels"] else 0
        lines.append(f"| {nc} | {c911} ({p911}%) | {c913} ({p913}%) |")
    lines.append("")

    # §3 R=0 Inclusion
    lines.append("## 3. R=0 Inclusion Rate\n")
    if r0_v913.get("pure_rate") is not None:
        lines.append(f"v9.13 τ={tau}: birth 時メンバーリンクが全て R>0 の label = "
                     f"**{r0_v913['n_pure_r_positive']}/{r0_v913['n_formed']} ({r0_v913['pure_rate']:.1%})**")
        lines.append(f"- age_r_min mean = {r0_v913.get('age_r_min_mean')}")
        lines.append(f"- age_r_min p50 = {r0_v913.get('age_r_min_p50')}")
    if "ncore2_rate" in r0_v911:
        lines.append(f"\nv9.11 参考: n_core=2 (経路B由来) = "
                     f"{r0_v911['n_ncore2_pair']}/{r0_v911['n_formed']} ({r0_v911['ncore2_rate']:.1%})")
        lines.append(f"- {r0_v911.get('note', '')}")
    lines.append("")

    # §4 B_Gen
    lines.append("## 4. B_Gen Band Structure\n")
    lines.append(f"| n_core | v9.11 mean (std) | v9.13 mean (std) | v9.11 ref |")
    lines.append("|---|---|---|---|")
    for nc in sorted(set(list(bgen_v911["bgen_stats"].keys()) +
                         list(bgen_v913["bgen_stats"].keys()))):
        s911 = bgen_v911["bgen_stats"].get(nc, {})
        s913 = bgen_v913["bgen_stats"].get(nc, {})
        ref = V911_REF["bgen_by_ncore"].get(nc, "?")
        lines.append(f"| {nc} | {s911.get('mean','?')} ({s911.get('std','?')}) "
                     f"| {s913.get('mean','?')} ({s913.get('std','?')}) | {ref} |")
    lines.append("")

    # §5 Capture
    lines.append("## 5. Capture Dynamics\n")
    lines.append(f"| 指標 | v9.11 | v9.13 |")
    lines.append("|---|---|---|")
    lines.append(f"| capture_rate mean | {cap_v911.get('capture_rate_mean')} | {cap_v913.get('capture_rate_mean')} |")
    lines.append(f"| phase+r % | {cap_v911.get('phase_plus_r','?')}% | {cap_v913.get('phase_plus_r','?')}% |")
    lines.append("")
    lines.append("### n_core 別 capture_rate\n")
    lines.append(f"| n_core | v9.11 | v9.13 | v9.11 ref |")
    lines.append("|---|---|---|---|")
    for nc in sorted(set(list(cap_v911.get("capture_by_ncore", {}).keys()) +
                         list(cap_v913.get("capture_by_ncore", {}).keys()))):
        c911 = cap_v911.get("capture_by_ncore", {}).get(nc, "?")
        c913 = cap_v913.get("capture_by_ncore", {}).get(nc, "?")
        ref = V911_REF["capture_by_ncore"].get(nc, "?")
        lines.append(f"| {nc} | {c911} | {c913} | {ref} |")
    lines.append("")

    lines.append("### 軸寄与\n")
    lines.append("| 軸 | v9.11 | v9.13 |")
    lines.append("|---|---|---|")
    for ax in ["n", "s", "r", "phase"]:
        v911 = cap_v911.get("axis_contrib", {}).get(ax, "?")
        v913 = cap_v913.get("axis_contrib", {}).get(ax, "?")
        lines.append(f"| {ax} | {v911}% | {v913}% |")
    lines.append("")

    # §6 L06
    lines.append("## 6. Long-lived Group (L06 equivalent)\n")
    lines.append(f"| 指標 | v9.11 | v9.13 |")
    lines.append("|---|---|---|")
    lines.append(f"| L06 count | {V911_REF['l06_count']} (5 seeds long) | {l06_v913['n_long']} |")
    lines.append(f"| n_core=5 % | {V911_REF['l06_ncore5_pct']}% | {l06_v913.get('long_ncore5_pct', '?')}% |")
    lines.append(f"| capture_rate | {V911_REF['l06_capture']} | {l06_v913.get('long_capture_mean', '?')} |")
    lines.append(f"| Δ mean | — | {l06_v913.get('long_delta_mean', '?')} |")
    if l06_v913.get("long_ncore_dist"):
        lines.append(f"\nL06 n_core 分布 (v9.13): {l06_v913['long_ncore_dist']}")
    lines.append("")

    # §7 Axis by n_core
    lines.append("## 7. Axis Contribution by n_core\n")
    for version, data in [("v9.11", cap_v911), (f"v9.13 τ={tau}", cap_v913)]:
        if "axis_by_ncore" in data:
            lines.append(f"### {version}\n")
            lines.append("| n_core | n% | s% | r% | phase% |")
            lines.append("|---|---|---|---|---|")
            for nc in sorted(data["axis_by_ncore"].keys()):
                a = data["axis_by_ncore"][nc]
                lines.append(f"| {nc} | {a['n']} | {a['s']} | {a['r']} | {a['phase']} |")
            lines.append("")

    # §8 Summary
    lines.append("## 8. Findings Summary\n")
    lines.append("### Step 0 audit 予測との一致/乖離\n")
    lines.append(f"- label 数 {ratio:.1%} (予測 ~33%): "
                 f"{'概ね一致' if 0.2 < ratio < 0.5 else '乖離あり'}")
    lines.append(f"- n_core=2 廃止: "
                 f"{'確認' if stats_v913['ncore_dist'].get(2, 0) == 0 else '残存あり'}")
    lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Report written: {out_path}")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
def run_analysis(tau):
    print(f"=== v9.13 τ={tau} Analysis ===")

    v913_dir = _SCRIPT_DIR / f"diag_v913_persistence_tau{tau}_main"
    fig_dir = _OUT_BASE / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    inter_dir = _OUT_BASE / "intermediate"
    inter_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("  Loading v9.13 subjects...")
    subj_v913, ns913 = load_subjects(v913_dir)
    print(f"    {len(subj_v913)} rows from {ns913} seeds")

    print("  Loading v9.11 subjects...")
    subj_v911, ns911 = load_subjects(_V911_SHORT)
    print(f"    {len(subj_v911)} rows from {ns911} seeds")

    print("  Loading v9.13 labels...")
    labels_v913, _ = load_labels(v913_dir)
    print(f"    {len(labels_v913)} labels")

    print("  Loading v9.11 labels...")
    labels_v911, _ = load_labels(_V911_SHORT)
    print(f"    {len(labels_v911)} labels")

    # Analyze
    print("  Analyzing basic stats...")
    stats_v911 = analyze_basic_stats(labels_v911, ns911, "v9.11")
    stats_v913 = analyze_basic_stats(labels_v913, ns913, f"v9.13_tau{tau}")

    print("  Analyzing R=0 inclusion...")
    r0_v911 = analyze_r0_inclusion(subj_v911, "v9.11")
    r0_v913 = analyze_r0_inclusion(subj_v913, f"v9.13_tau{tau}")

    print("  Analyzing B_Gen bands...")
    bgen_v911 = analyze_bgen(subj_v911, "v9.11")
    bgen_v913 = analyze_bgen(subj_v913, f"v9.13_tau{tau}")

    print("  Analyzing capture dynamics...")
    cap_v911 = analyze_capture(subj_v911, "v9.11")
    cap_v913 = analyze_capture(subj_v913, f"v9.13_tau{tau}")

    print("  Analyzing L06...")
    l06_v911 = analyze_l06(subj_v911, "v9.11")
    l06_v913 = analyze_l06(subj_v913, f"v9.13_tau{tau}")

    # Plot
    print("  Generating figures...")
    plot_ncore_dist(stats_v911, stats_v913, fig_dir, tau)
    plot_bgen_bands(bgen_v911, bgen_v913, fig_dir, tau)
    plot_capture_by_ncore(cap_v911, cap_v913, fig_dir, tau)
    plot_axis_contribution(cap_v911, cap_v913, fig_dir, tau)

    # Report
    report_path = _OUT_BASE / f"v913_tau{tau}_analysis.md"
    generate_report(tau, stats_v911, stats_v913, r0_v911, r0_v913,
                    bgen_v911, bgen_v913, cap_v911, cap_v913,
                    l06_v911, l06_v913, report_path)

    print(f"=== Done. Output: {_OUT_BASE} ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="v9.13 Analysis")
    parser.add_argument("--tau", type=int, default=50)
    parser.add_argument("--compare", action="store_true",
                        help="Run tau=50 vs tau=100 comparison")
    args = parser.parse_args()

    if args.compare:
        run_analysis(50)
        run_analysis(100)
        print("  Comparison mode: both reports generated. Manual merge needed.")
    else:
        run_analysis(args.tau)
