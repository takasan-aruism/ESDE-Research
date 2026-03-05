#!/usr/bin/env python3
"""
ESDE Genesis v1.4 — Long-Run Band Validation
===============================================
Validates the operating band under long quiet runs.

3 operating points × 10 seeds = 30 runs
Designed for parallel execution on multi-core machines.

Usage:
  # Run all (sequential):
  python v14_longrun.py

  # Run single point+seed (for parallel dispatch):
  python v14_longrun.py --point P1 --seed 42

  # Run all seeds for one point (good for GNU parallel):
  python v14_longrun.py --point P2

  # Aggregate only (after all runs complete):
  python v14_longrun.py --aggregate-only

Parallel example (GNU parallel on Ryzen):
  parallel -j 20 python v14_longrun.py --point {} --seed {} \
    ::: P1 P2 P3 ::: 42 123 456 789 2024 7 314 999 55 1337

Then:
  python v14_longrun.py --aggregate-only
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import csv, json, time, os, sys, argparse
from collections import Counter, defaultdict
from pathlib import Path

# ---- Import Genesis modules (must be in same directory or PYTHONPATH) ----
from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams

# ============================================================
# CONFIGURATION
# ============================================================
N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; INJECT_INTERVAL = 3
BETA = 1.0; NODE_DECAY = 0.005; BIAS = 0.7
QUIET_STEPS = 5000  # ← long run target
STRENGTH_BINS = [(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]

BASE = {
    "reaction_energy_threshold": 0.26, "link_death_threshold": 0.007,
    "background_injection_prob": 0.003, "exothermic_release_amount": 0.17,
    "p_link_birth": 0.007, "latent_to_active_threshold": 0.07,
    "latent_refresh_rate": 0.003, "auto_growth_rate": 0.03,
}

POINTS = {
    "P1": {"p_link_birth": 0.007, "bg_inject": 0.003, "label": "order/safe"},
    "P2": {"p_link_birth": 0.008, "bg_inject": 0.003, "label": "center"},
    "P3": {"p_link_birth": 0.010, "bg_inject": 0.003, "label": "activity/edge"},
}

ALL_SEEDS = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337]

OUTPUT_DIR = Path("outputs_v14")

# ============================================================
# CYCLE TRACKER
# ============================================================
class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list)
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i]); h = self.history[i]
            if not h or h[-1][1] != z:
                h.append((step, z))
    def find_cycles(self):
        cycles = []
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0 and states[i+2] in (1, 2):
                    for j in range(i+3, len(states)):
                        if states[j] == 3:
                            cycles.append({
                                "node": nid, "start": h[i][0], "end": h[j][0],
                                "duration": h[j][0] - h[i][0],
                            })
                            break
        return cycles


# ============================================================
# SINGLE RUN
# ============================================================
def run_single(seed, plb, bgi, quiet_steps=QUIET_STEPS):
    """Run one full simulation. Returns result dict."""
    p = dict(BASE)
    p["p_link_birth"] = plb
    p["background_injection_prob"] = bgi

    state = GenesisState(N_NODES, C_MAX, seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True, phase_enabled=True,
        beta=BETA, decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    cp = ChemistryParams(enabled=True, E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"])
    chem = ChemistryEngine(cp)
    rp = RealizationParams(enabled=True, p_link_birth=plb,
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer = RealizationOperator(rp)
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True,
        auto_growth_rate=p["auto_growth_rate"]))
    state.EXTINCTION = p["link_death_threshold"]
    tracker = CycleTracker()
    g_scores = np.zeros(N_NODES)

    t0 = time.time()

    # Injection
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state); chem.step(state)
        cd = physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state); tracker.record(state, state.step - 1)

    # Quiet
    tot_opp = 0; tot_nm = 0; miss = Counter()
    spr_v = []; s_hists = []; min_l = 99999
    first_cycle_step = None

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        rxns = chem.step(state)
        cd = physics.step_resonance(state)
        g_scores[:] = 0; grower.step(state)
        for k in state.alive_l:
            r = state.R.get(k, 0.0)
            if r > 0:
                a = min(grower.params.auto_growth_rate * r,
                        max(state.get_latent(k[0], k[1]), 0))
                if a > 0: g_scores[k[0]] += a; g_scores[k[1]] += a
        gz = float(g_scores.sum())
        physics.step_decay_exclusion(state)
        tracker.record(state, state.step - 1)

        # Biased seeding
        al = list(state.alive_n); na = len(al)
        if na > 0:
            aa = np.array(al)
            if BIAS > 0 and gz > 0:
                ga = g_scores[aa]; gs = ga.sum()
                if gs > 0:
                    pg = ga / gs
                    pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
                    pd /= pd.sum()
                else: pd = np.ones(na) / na
            else: pd = np.ones(na) / na
            mk = state.rng.random(na) < bgi
            for idx in range(na):
                if mk[idx]:
                    t = int(state.rng.choice(aa, p=pd))
                    state.E[t] = min(1.0, state.E[t] + 0.3)
                    if state.Z[t] == 0 and state.rng.random() < 0.5:
                        state.Z[t] = 1 if state.rng.random() < 0.5 else 2

        # Metrics every 50 steps
        if step % 50 == 49:
            nl = len(state.alive_l); min_l = min(min_l, nl)
            ss = [state.S[k] for k in state.alive_l]
            ll = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr_v.append(ll / max(nl, 1))
            h = [0] * 5
            for s in ss:
                for bi, (lo, hi) in enumerate(STRENGTH_BINS):
                    if lo <= s < hi: h[bi] += 1; break
            s_hists.append(h)
            for k in state.alive_l:
                i, j = k; s = state.S[k]
                cs = s >= 0.3
                ce = state.E[i] >= cp.E_thr and state.E[j] >= cp.E_thr
                ct = int(state.Z[i]) in (1, 2) or int(state.Z[j]) in (1, 2)
                cy = np.cos(state.theta[j] - state.theta[i]) >= 0.7
                nm = sum([cs, ce, ct, cy])
                if nm == 4: tot_opp += 1
                elif nm == 3:
                    tot_nm += 1
                    if not cs: miss["strong"] += 1
                    if not ce: miss["energy"] += 1
                    if not ct: miss["state"] += 1
                    if not cy: miss["sync"] += 1

        # Track first cycle
        if first_cycle_step is None and step % 200 == 199:
            cyc_so_far = tracker.find_cycles()
            if cyc_so_far:
                first_cycle_step = min(c["end"] for c in cyc_so_far) - INJECTION_STEPS

        # Progress (every 1000 steps)
        if step % 1000 == 999:
            cyc_n = len(tracker.find_cycles())
            print(f"      quiet {step+1}/{quiet_steps}: "
                  f"L={len(state.alive_l):>4} cyc={cyc_n} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # Final metrics
    all_cycles = tracker.find_cycles()
    if first_cycle_step is None and all_cycles:
        first_cycle_step = min(c["end"] for c in all_cycles) - INJECTION_STEPS

    ts = quiet_steps
    s03 = sum(1 for k in state.alive_l if state.S[k] >= 0.3)
    mx_s = max((state.S[k] for k in state.alive_l), default=0)

    # X components
    if s_hists:
        mh = np.mean(s_hists, axis=0); t = mh.sum()
        if t > 0:
            pp = mh / t; pp = pp[pp > 0]
            H = -np.sum(pp * np.log2(pp))
            C_score = 1 - H / np.log2(5)
        else: C_score = 0; H = 0
    else: C_score = 0; H = 0

    spr = np.mean(spr_v) if spr_v else 0
    sep_n = set(); sep_ab = 0
    for k in state.alive_l:
        if state.S[k] >= 0.3:
            sep_n.add(k[0]); sep_n.add(k[1])
            if int(state.Z[k[0]]) in (1, 2): sep_ab += 1
            if int(state.Z[k[1]]) in (1, 2): sep_ab += 1
    cov = sep_ab / (max(len(sep_n) * 2, 1)) if sep_n else 0

    cyc_rate = len(all_cycles) / (ts / 1000)
    opp_rate = tot_opp / max(ts / 50, 1)
    X = round(C_score + spr + 0.01 * cyc_rate, 4)
    elapsed = time.time() - t0

    return {
        "cycles_total": len(all_cycles),
        "cycles_per_1k": round(cyc_rate, 3),
        "time_to_first_cycle": first_cycle_step,
        "opp_per_1k": round(opp_rate * (1000 / 50), 3),
        "min_links": min_l if min_l < 99999 else 0,
        "s03": s03, "max_s": round(mx_s, 4),
        "spr": round(spr, 4), "compress": round(C_score, 4),
        "X": X, "R": 0, "C": round(C_score, 4), "B": round(spr, 4),
        "strong_cov": round(cov, 4),
        "miss_strong": round(miss.get("strong", 0) / max(tot_nm, 1), 3),
        "miss_energy": round(miss.get("energy", 0) / max(tot_nm, 1), 3),
        "miss_state": round(miss.get("state", 0) / max(tot_nm, 1), 3),
        "miss_sync": round(miss.get("sync", 0) / max(tot_nm, 1), 3),
        "elapsed": round(elapsed, 1),
    }


# ============================================================
# BASELINE (per seed)
# ============================================================
def compute_baseline(seed):
    r = run_single(seed, BASE["p_link_birth"], BASE["background_injection_prob"],
                   quiet_steps=min(QUIET_STEPS, 600))  # shorter for baseline
    return r["X"]


# ============================================================
# RUN ONE POINT+SEED AND SAVE
# ============================================================
def run_and_save(point_id, seed, baselines, quiet_steps=QUIET_STEPS):
    pt = POINTS[point_id]
    plb = pt["p_link_birth"]; bgi = pt["bg_inject"]

    out_dir = OUTPUT_DIR / point_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result_file = out_dir / f"seed_{seed}.json"

    # Skip if already done
    if result_file.exists():
        with open(result_file) as f:
            return json.load(f)

    print(f"  [{point_id}] seed={seed} plb={plb} bg={bgi} quiet={quiet_steps}...",
          flush=True)
    r = run_single(seed, plb, bgi, quiet_steps)

    xb = baselines.get(seed, 0.6)
    eta = r["X"] / xb if xb > 0.01 else 0
    collapse = bool(r["min_links"] == 0 or eta < 0.6)

    result = {
        "point_id": point_id,
        "p_link_birth": plb, "bg_inject": bgi,
        "seed": int(seed), "quiet_steps": int(quiet_steps),
        "eta_ratio": round(float(eta), 4),
        "collapse_flag": collapse,
    }
    for k, v in r.items():
        if isinstance(v, (np.integer, np.floating)):
            result[k] = float(v)
        elif isinstance(v, np.bool_):
            result[k] = bool(v)
        else:
            result[k] = v

    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"    → cyc={r['cycles_total']} eta={eta:.3f} "
          f"first_cyc={r['time_to_first_cycle']} ({r['elapsed']:.0f}s)",
          flush=True)
    return result


# ============================================================
# AGGREGATE
# ============================================================
def aggregate():
    all_results = []
    for pid in POINTS:
        d = OUTPUT_DIR / pid
        if not d.exists(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh:
                all_results.append(json.load(fh))

    if not all_results:
        print("  No results found. Run experiments first."); return

    # Summary CSV
    with open(OUTPUT_DIR / "v14_longrun_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_results[0].keys())
        w.writeheader(); w.writerows(all_results)

    # Aggregate per point
    agg = []
    for pid in POINTS:
        sub = [r for r in all_results if r["point_id"] == pid]
        if not sub: continue
        cyc_rates = [r["cycles_per_1k"] for r in sub]
        etas = [r["eta_ratio"] for r in sub]
        ttfc = [r["time_to_first_cycle"] for r in sub if r["time_to_first_cycle"] is not None]

        agg.append({
            "point_id": pid,
            "p_link_birth": sub[0]["p_link_birth"],
            "n_seeds": len(sub),
            "med_cyc_per_1k": round(np.median(cyc_rates), 3),
            "mean_cyc_per_1k": round(np.mean(cyc_rates), 3),
            "iqr_cyc": f"{np.percentile(cyc_rates,25):.2f}-{np.percentile(cyc_rates,75):.2f}",
            "seeds_with_cycles": sum(1 for r in sub if r["cycles_total"] > 0),
            "med_eta": round(np.median(etas), 3),
            "pct_collapse": round(sum(1 for r in sub if r["collapse_flag"]) / len(sub) * 100, 0),
            "med_ttfc": round(np.median(ttfc), 0) if ttfc else "N/A",
            "med_min_links": int(np.median([r["min_links"] for r in sub])),
        })

    with open(OUTPUT_DIR / "v14_longrun_aggregate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=agg[0].keys())
        w.writeheader(); w.writerows(agg)

    # Print table
    print(f"\n{'='*70}")
    print(f"  v1.4 AGGREGATE RESULTS")
    print(f"{'='*70}")
    for a in agg:
        print(f"  {a['point_id']} (plb={a['p_link_birth']}): "
              f"cyc/1k={a['med_cyc_per_1k']} [{a['iqr_cyc']}] "
              f"η={a['med_eta']} "
              f"seeds_cyc={a['seeds_with_cycles']}/{a['n_seeds']} "
              f"ttfc={a['med_ttfc']} "
              f"minL={a['med_min_links']}")

    # ---- Plots ----
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("ESDE Genesis v1.4 — Long-Run Band Validation",
                 fontsize=14, fontweight="bold")

    pids = [a["point_id"] for a in agg]
    colors = {"P1": "#2ecc71", "P2": "#3498db", "P3": "#e67e22"}

    # Boxplot: cycles/1k
    ax = axes[0][0]
    data_cyc = [[r["cycles_per_1k"] for r in all_results if r["point_id"] == pid] for pid in pids]
    bp = ax.boxplot(data_cyc, tick_labels=pids, patch_artist=True)
    for patch, pid in zip(bp["boxes"], pids):
        patch.set_facecolor(colors.get(pid, "gray"))
    ax.set_title("Cycles per 1k Quiet Steps"); ax.grid(True, alpha=0.2)

    # Boxplot: eta
    ax = axes[0][1]
    data_eta = [[r["eta_ratio"] for r in all_results if r["point_id"] == pid] for pid in pids]
    bp = ax.boxplot(data_eta, tick_labels=pids, patch_artist=True)
    for patch, pid in zip(bp["boxes"], pids):
        patch.set_facecolor(colors.get(pid, "gray"))
    ax.axhline(y=0.8, color="red", linestyle="--", alpha=0.5, label="η threshold")
    ax.set_title("η (Explainability Stability)"); ax.legend(); ax.grid(True, alpha=0.2)

    # ECDF: time to first cycle
    ax = axes[1][0]
    for pid in pids:
        ttfc_vals = sorted([r["time_to_first_cycle"] for r in all_results
                           if r["point_id"] == pid and r["time_to_first_cycle"] is not None])
        if ttfc_vals:
            y = np.arange(1, len(ttfc_vals) + 1) / len([r for r in all_results if r["point_id"] == pid])
            ax.step(ttfc_vals, y, label=pid, color=colors.get(pid, "gray"), linewidth=2)
    ax.set_title("Time to First Cycle (ECDF)"); ax.set_xlabel("Quiet Steps")
    ax.set_ylabel("Fraction of Seeds"); ax.legend(); ax.grid(True, alpha=0.2)

    # Summary text
    ax = axes[1][1]; ax.axis("off")
    txt = ["v1.4 Long-Run Summary", "=" * 30, ""]
    for a in agg:
        txt.append(f"{a['point_id']} (plb={a['p_link_birth']}):")
        txt.append(f"  cyc/1k: {a['med_cyc_per_1k']} [{a['iqr_cyc']}]")
        txt.append(f"  η: {a['med_eta']}  col: {a['pct_collapse']}%")
        txt.append(f"  seeds w/cyc: {a['seeds_with_cycles']}/{a['n_seeds']}")
        txt.append(f"  TTFC median: {a['med_ttfc']}")
        txt.append("")
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=10,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "v14_longrun_plots.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plots: {OUTPUT_DIR / 'v14_longrun_plots.png'}")

    # Conclusion
    conclusion = ["ESDE Genesis v1.4 — Long-Run Validation Conclusion", "=" * 50, ""]
    for a in agg:
        status = "PASS" if a["med_eta"] >= 0.8 and a["pct_collapse"] == 0 else "FAIL"
        conclusion.append(f"{a['point_id']} (plb={a['p_link_birth']}): {status}")
        conclusion.append(f"  cycles/1k: {a['med_cyc_per_1k']} [{a['iqr_cyc']}]")
        conclusion.append(f"  η={a['med_eta']}, collapse={a['pct_collapse']}%")
        conclusion.append(f"  seeds with cycles: {a['seeds_with_cycles']}/{a['n_seeds']}")
        conclusion.append(f"  TTFC median: {a['med_ttfc']}")
        conclusion.append("")

    with open(OUTPUT_DIR / "v14_longrun_conclusion.txt", "w") as f:
        f.write("\n".join(conclusion))


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="v1.4 Long-Run Band Validation")
    parser.add_argument("--point", type=str, default=None,
                       help="Point ID (P1/P2/P3). If omitted, run all.")
    parser.add_argument("--seed", type=int, default=None,
                       help="Single seed. If omitted, run all seeds.")
    parser.add_argument("--aggregate-only", action="store_true",
                       help="Only aggregate existing results.")
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS,
                       help=f"Quiet phase length (default: {QUIET_STEPS})")
    parser.add_argument("--sanity", action="store_true",
                       help="Quick sanity check: 1 point, 1 seed, 300 quiet steps")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    qs = args.quiet_steps

    if args.aggregate_only:
        aggregate()
        return

    qs = args.quiet_steps

    if args.sanity:
        print("  SANITY CHECK: P2, seed=42, 300 quiet steps")
        r = run_single(42, 0.008, 0.003, 300)
        print(f"  Result: cyc={r['cycles_total']} links_min={r['min_links']} "
              f"X={r['X']} ({r['elapsed']:.0f}s)")
        print("  Sanity OK." if r["min_links"] > 0 else "  WARNING: links collapsed!")
        return

    # Determine what to run
    points = [args.point] if args.point else list(POINTS.keys())
    seeds = [args.seed] if args.seed else ALL_SEEDS

    # Compute baselines
    print("  Computing baselines...")
    baselines = {}
    bl_file = OUTPUT_DIR / "baselines.json"
    if bl_file.exists():
        with open(bl_file) as f:
            baselines = {int(k): v for k, v in json.load(f).items()}
        print(f"    Loaded {len(baselines)} cached baselines")

    for seed in seeds:
        if seed not in baselines:
            print(f"    baseline seed={seed}...", end=" ", flush=True)
            baselines[seed] = compute_baseline(seed)
            print(f"X={baselines[seed]:.4f}")
            with open(bl_file, "w") as f:
                json.dump(baselines, f)

    # Run experiments
    print(f"\n  Running: points={points} seeds={seeds} quiet={qs}")
    for pid in points:
        for seed in seeds:
            run_and_save(pid, seed, baselines, qs)

    # Aggregate if we ran everything
    if args.point is None and args.seed is None:
        aggregate()


if __name__ == "__main__":
    main()
