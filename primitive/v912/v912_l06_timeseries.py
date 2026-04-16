#!/usr/bin/env python3
"""
v9.12 Phase 1 — L06 個別時系列分析
====================================
対象: diag_v911_capture_long/ (5 seeds × 50 tracking windows)
目的: L06 (n_pulses_eval ≥ 167, long top 10%) の cid 単位 pulse 時系列を集計し、
      M_c-vs-E_t 乖離の挙動を可視化用 CSV + 集約レポートとして出力する。

実装変更ゼロ。集計のみ。

設計書: v912_l06_timeseries_design.md
体制: 軽量 (Code A 実行のみ、Code B チェック省略)

USAGE:
  # pilot (seed=0 のみ)
  python v912_l06_timeseries.py --pilot

  # 本実行 (全 5 seeds)
  python v912_l06_timeseries.py
"""

import csv
import math
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

# ================================================================
# PATHS
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
_V911_LONG = _SCRIPT_DIR.parent / "v911" / "diag_v911_capture_long"
_OUTDIR = _SCRIPT_DIR / "diag_l06_timeseries"

SEEDS = [0, 1, 2, 3, 4]
L06_THRESHOLD = 167   # n_pulses_eval ≥ 167 = long top 10%

# 集計パラメータ (設計書 §10 確定)
BIN_WIDTH = 5                        # pulse_n を 5 pulse ごとに bin
AUTOCORR_LAGS = [1, 2, 3, 5, 10]    # Δ 自己相関の lag

# ================================================================
# HELPERS
# ================================================================

def read_csv(path):
    """CSV を list of dict で読む。"""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def extract_l06_cids(seeds):
    """per_subject CSV から L06 cid を抽出。
    Returns: list of (seed, cid, n_core, b_gen) tuples
    """
    l06 = []
    for seed in seeds:
        subj_path = _V911_LONG / "subjects" / f"per_subject_seed{seed}.csv"
        if not subj_path.exists():
            print(f"  WARNING: {subj_path} not found, skipping seed {seed}")
            continue
        rows = read_csv(subj_path)
        for r in rows:
            npe = r.get("v11_n_pulses_eval", "0")
            if npe == "unformed" or npe == "":
                continue
            if int(npe) >= L06_THRESHOLD:
                cid = int(r["cognitive_id"])
                nc_raw = r.get("v11_m_c_n_core", "unformed")
                n_core = int(nc_raw) if nc_raw != "unformed" else 0
                bg_raw = r.get("v11_b_gen", "unformed")
                b_gen = float(bg_raw) if bg_raw not in ("unformed", "inf") else 0.0
                l06.append((seed, cid, n_core, b_gen))
    return l06


def extract_pulse_rows(seed, cid_set):
    """pulse_log から該当 seed の cid_set に属する eval 行を抽出。
    Returns: dict of cid -> list of row dicts (pulse_n 昇順)
    """
    pulse_path = _V911_LONG / "pulse" / f"pulse_log_seed{seed}.csv"
    if not pulse_path.exists():
        print(f"  WARNING: {pulse_path} not found")
        return {}
    rows = read_csv(pulse_path)
    result = defaultdict(list)
    for r in rows:
        cid = int(r["cid"])
        if cid not in cid_set:
            continue
        captured = r.get("v11_captured", "")
        # cold_start 行は別カウントのみ、eval 集計対象外
        if captured == "cold_start":
            continue
        result[cid].append(r)
    # sort by pulse_n
    for cid in result:
        result[cid].sort(key=lambda x: int(x["pulse_n"]))
    return result


def safe_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def autocorrelation(series, lag):
    """1D 系列の自己相関 (lag)。十分な長さがなければ NaN。"""
    n = len(series)
    if n <= lag + 1:
        return float("nan")
    arr = np.array(series, dtype=float)
    mean = arr.mean()
    var = ((arr - mean) ** 2).mean()
    if var < 1e-15:
        return float("nan")
    cov = ((arr[:-lag] - mean) * (arr[lag:] - mean)).mean()
    return cov / var


# ================================================================
# MAIN ANALYSIS
# ================================================================

def run(pilot=False):
    seeds = [0] if pilot else SEEDS
    print(f"=== v9.12 Phase 1: L06 timeseries analysis ===")
    print(f"  seeds: {seeds}")

    # ─── Step 1: L06 cid 抽出 ───
    l06_list = extract_l06_cids(seeds)
    print(f"  L06 cids extracted: {len(l06_list)}")
    if not pilot:
        assert len(l06_list) > 0, "No L06 cids found"

    # seed -> set of cids
    seed_cids = defaultdict(set)
    cid_meta = {}  # (seed, cid) -> {n_core, b_gen}
    for seed, cid, n_core, b_gen in l06_list:
        seed_cids[seed].add(cid)
        cid_meta[(seed, cid)] = {"n_core": n_core, "b_gen": b_gen}

    # ─── Step 2: pulse 行抽出 ───
    all_cid_series = {}  # (seed, cid) -> list of parsed rows
    for seed in seeds:
        cid_rows = extract_pulse_rows(seed, seed_cids[seed])
        for cid, rows in cid_rows.items():
            parsed = []
            for r in rows:
                parsed.append({
                    "pulse_n": int(r["pulse_n"]),
                    "t": int(r["t"]),
                    "window": int(r["window"]),
                    "delta": safe_float(r.get("v11_delta")),
                    "d_n": safe_float(r.get("v11_d_n")),
                    "d_s": safe_float(r.get("v11_d_s")),
                    "d_r": safe_float(r.get("v11_d_r")),
                    "d_phase": safe_float(r.get("v11_d_phase")),
                    "p_capture": safe_float(r.get("v11_p_capture")),
                    "captured": 1 if r.get("v11_captured") == "TRUE" else 0,
                    "n_local": int(safe_float(r.get("v11_n_local", 0))),
                    "s_avg_local": safe_float(r.get("v11_s_avg_local")),
                    "r_local": safe_float(r.get("v11_r_local")),
                    "theta_avg_local": safe_float(r.get("v11_theta_avg_local")),
                })
            all_cid_series[(seed, cid)] = parsed

    total_pulses = sum(len(v) for v in all_cid_series.values())
    print(f"  Total eval pulses loaded: {total_pulses}")

    # ─── Output directory ───
    _OUTDIR.mkdir(parents=True, exist_ok=True)
    per_cid_dir = _OUTDIR / "per_cid"
    per_cid_dir.mkdir(exist_ok=True)

    # ─── Step 4 (b): cid 別 CSV 出力 ───
    for (seed, cid), series in all_cid_series.items():
        meta = cid_meta[(seed, cid)]
        out_path = per_cid_dir / f"cid_{cid}_seed{seed}.csv"
        if series:
            with open(out_path, "w", newline="") as f:
                extra = {"seed": seed, "cid": cid,
                         "n_core": meta["n_core"], "b_gen": round(meta["b_gen"], 4)}
                fields = list(extra.keys()) + list(series[0].keys())
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for row in series:
                    w.writerow({**extra, **row})

    print(f"  Per-cid CSVs written: {len(all_cid_series)}")

    # ─── Step 3 (a): 全 L06 平均推移 (pulse_n bin) ───
    # pulse_n の範囲: 4 (cold_start 後) 〜 max
    max_pulse_n = max(
        (row["pulse_n"] for s in all_cid_series.values() for row in s),
        default=0)
    bins = list(range(4, max_pulse_n + BIN_WIDTH, BIN_WIDTH))

    bin_stats = []
    for b_start in bins:
        b_end = b_start + BIN_WIDTH
        deltas = []
        d_ns, d_ss, d_rs, d_phases = [], [], [], []
        captures = []
        p_caps = []
        for series in all_cid_series.values():
            for row in series:
                if b_start <= row["pulse_n"] < b_end:
                    deltas.append(row["delta"])
                    d_ns.append(row["d_n"])
                    d_ss.append(row["d_s"])
                    d_rs.append(row["d_r"])
                    d_phases.append(row["d_phase"])
                    captures.append(row["captured"])
                    p_caps.append(row["p_capture"])
        if not deltas:
            continue
        n = len(deltas)
        bin_stats.append({
            "bin_start": b_start,
            "bin_end": b_end,
            "n_pulses": n,
            "n_cids": len(set(
                (s, c) for (s, c), series in all_cid_series.items()
                for row in series if b_start <= row["pulse_n"] < b_end)),
            "delta_mean": round(np.mean(deltas), 6),
            "delta_p50": round(np.median(deltas), 6),
            "d_n_mean": round(np.mean(d_ns), 6),
            "d_s_mean": round(np.mean(d_ss), 6),
            "d_r_mean": round(np.mean(d_rs), 6),
            "d_phase_mean": round(np.mean(d_phases), 6),
            "capture_rate": round(np.mean(captures), 6),
            "p_capture_mean": round(np.mean(p_caps), 6),
        })

    agg_path = _OUTDIR / "aggregate_bin.csv"
    if bin_stats:
        with open(agg_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=bin_stats[0].keys())
            w.writeheader()
            w.writerows(bin_stats)
    print(f"  Aggregate bin stats: {len(bin_stats)} bins written")

    # ─── Step 5 (c): Δ spike vs capture failure ───
    all_deltas = []
    for series in all_cid_series.values():
        for row in series:
            all_deltas.append(row["delta"])
    all_deltas_arr = np.array(all_deltas)
    p90 = float(np.percentile(all_deltas_arr, 90))
    p10 = float(np.percentile(all_deltas_arr, 10))

    spike_captured = [row["captured"] for s in all_cid_series.values()
                      for row in s if row["delta"] >= p90]
    low_captured = [row["captured"] for s in all_cid_series.values()
                    for row in s if row["delta"] <= p10]

    spike_stats = {
        "delta_p90_threshold": round(p90, 6),
        "delta_p10_threshold": round(p10, 6),
        "spike_n": len(spike_captured),
        "spike_capture_rate": round(np.mean(spike_captured), 6) if spike_captured else None,
        "low_n": len(low_captured),
        "low_capture_rate": round(np.mean(low_captured), 6) if low_captured else None,
    }
    print(f"  Spike analysis: p90={p90:.4f} spike_cap={spike_stats['spike_capture_rate']}, "
          f"p10={p10:.4f} low_cap={spike_stats['low_capture_rate']}")

    # ─── Step 6 (d): Δ 自己相関 ───
    autocorr_rows = []
    for (seed, cid), series in all_cid_series.items():
        deltas_seq = [row["delta"] for row in series]
        if len(deltas_seq) < max(AUTOCORR_LAGS) + 2:
            continue
        meta = cid_meta[(seed, cid)]
        row_ac = {"seed": seed, "cid": cid,
                  "n_core": meta["n_core"], "n_pulses": len(deltas_seq)}
        for lag in AUTOCORR_LAGS:
            row_ac[f"ac_lag{lag}"] = round(autocorrelation(deltas_seq, lag), 6)
        autocorr_rows.append(row_ac)

    ac_path = _OUTDIR / "autocorrelation.csv"
    if autocorr_rows:
        with open(ac_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=autocorr_rows[0].keys())
            w.writeheader()
            w.writerows(autocorr_rows)

    # 集約
    ac_summary = {}
    for lag in AUTOCORR_LAGS:
        vals = [r[f"ac_lag{lag}"] for r in autocorr_rows
                if not math.isnan(r[f"ac_lag{lag}"])]
        ac_summary[f"ac_lag{lag}_mean"] = round(np.mean(vals), 6) if vals else None
        ac_summary[f"ac_lag{lag}_p50"] = round(np.median(vals), 6) if vals else None
    print(f"  Autocorrelation: {len(autocorr_rows)} cids analyzed")
    for k, v in ac_summary.items():
        print(f"    {k}: {v}")

    # ─── Step 7 (e): 最初に乖離する軸 ───
    # overall p90 閾値 (long 全 eval pulse)
    all_d = {"n": [], "s": [], "r": [], "phase": []}
    for series in all_cid_series.values():
        for row in series:
            all_d["n"].append(row["d_n"])
            all_d["s"].append(row["d_s"])
            all_d["r"].append(row["d_r"])
            all_d["phase"].append(row["d_phase"])

    axis_p90 = {}
    for ax in ("n", "s", "r", "phase"):
        axis_p90[ax] = float(np.percentile(all_d[ax], 90))
    print(f"  Axis p90 thresholds: {axis_p90}")

    first_diverge = defaultdict(int)  # axis -> count
    first_diverge_by_ncore = defaultdict(lambda: defaultdict(int))

    for (seed, cid), series in all_cid_series.items():
        meta = cid_meta[(seed, cid)]
        found = None
        for row in series:
            for ax in ("n", "s", "r", "phase"):
                key = f"d_{ax}"
                if row[key] > axis_p90[ax]:
                    found = ax
                    break
            if found:
                break
        if found is None:
            found = "none"
        first_diverge[found] += 1
        first_diverge_by_ncore[meta["n_core"]][found] += 1

    print(f"  First diverge axis distribution:")
    for ax in ("n", "s", "r", "phase", "none"):
        print(f"    {ax}: {first_diverge.get(ax, 0)}")

    # ─── Step 8 (f): n_core 別層別集計 ───
    ncore_groups = defaultdict(list)
    for (seed, cid), series in all_cid_series.items():
        nc = cid_meta[(seed, cid)]["n_core"]
        ncore_groups[nc].append(series)

    ncore_stats = []
    for nc in sorted(ncore_groups):
        all_d_nc = []
        all_cap_nc = []
        for series in ncore_groups[nc]:
            for row in series:
                all_d_nc.append(row["delta"])
                all_cap_nc.append(row["captured"])
        # autocorrelation mean for this n_core
        ac_vals = [r[f"ac_lag1"] for r in autocorr_rows
                   if r["n_core"] == nc and not math.isnan(r["ac_lag1"])]
        ncore_stats.append({
            "n_core": nc,
            "n_cids": len(ncore_groups[nc]),
            "n_pulses": len(all_d_nc),
            "delta_mean": round(np.mean(all_d_nc), 6) if all_d_nc else None,
            "delta_p50": round(np.median(all_d_nc), 6) if all_d_nc else None,
            "capture_rate": round(np.mean(all_cap_nc), 6) if all_cap_nc else None,
            "ac_lag1_mean": round(np.mean(ac_vals), 6) if ac_vals else None,
            "first_diverge_dist": dict(first_diverge_by_ncore.get(nc, {})),
        })

    ncore_path = _OUTDIR / "ncore_stats.csv"
    if ncore_stats:
        # flatten first_diverge_dist for CSV
        flat_rows = []
        for ns in ncore_stats:
            r = {k: v for k, v in ns.items() if k != "first_diverge_dist"}
            fd = ns["first_diverge_dist"]
            for ax in ("n", "s", "r", "phase", "none"):
                r[f"fd_{ax}"] = fd.get(ax, 0)
            flat_rows.append(r)
        with open(ncore_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=flat_rows[0].keys())
            w.writeheader()
            w.writerows(flat_rows)

    print(f"\n  n_core stats:")
    for ns in ncore_stats:
        print(f"    n_core={ns['n_core']}: {ns['n_cids']} cids, "
              f"Δ mean={ns['delta_mean']}, cap_rate={ns['capture_rate']}, "
              f"ac1={ns['ac_lag1_mean']}")

    # ─── Summary JSON ───
    import json
    summary = {
        "seeds": seeds,
        "l06_cids_total": len(l06_list),
        "total_eval_pulses": total_pulses,
        "spike_stats": spike_stats,
        "autocorr_summary": ac_summary,
        "axis_p90_thresholds": axis_p90,
        "first_diverge_distribution": dict(first_diverge),
        "ncore_stats": [{k: v for k, v in ns.items()
                         if k != "first_diverge_dist"}
                        for ns in ncore_stats],
        "bin_width": BIN_WIDTH,
        "autocorr_lags": AUTOCORR_LAGS,
        "l06_threshold": L06_THRESHOLD,
    }
    with open(_OUTDIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n=== Done. Output: {_OUTDIR} ===")
    return summary


# ================================================================
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", action="store_true",
                   help="Pilot mode: seed=0 only")
    args = p.parse_args()
    run(pilot=args.pilot)
