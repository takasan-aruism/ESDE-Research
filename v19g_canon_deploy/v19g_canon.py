#!/usr/bin/env python3
"""
ESDE Genesis v1.9g — Canonical Freeze + N=500 Scale Transfer Test
===================================================================
Frozen observer: hyst_0.01 (T=0.01, k=3↔4 boundary)
Primary stability metric: switches_per_100_windows

This script is the CANONICAL implementation. No ad-hoc modes.

Tasks:
  A) Observer config frozen as constants
  B) Structured switch logging
  C) Stability metric: switches_per_100
  D) Comparable output schema
  E) N=500 run path (change N only)
  F) Baseline comparison bundle

Usage:
  python v19g_canon.py --sanity
  python v19g_canon.py --N 200 --plb 0.010 --rate 0.001 --seed 42
  python v19g_canon.py --N 500 --plb 0.010 --rate 0.001 --seed 42
  python v19g_canon.py --aggregate

  # Parallel N=200 baseline (120 runs):
  parallel -j 20 python v19g_canon.py --N 200 --plb {1} --rate {2} --seed {3} \
    ::: 0.007 0.008 0.010 ::: 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337

  # N=500 scale transfer (same grid):
  parallel -j 10 python v19g_canon.py --N 500 --plb {1} --rate {2} --seed {3} \
    ::: 0.007 0.008 0.010 ::: 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337

  # Aggregate both:
  python v19g_canon.py --aggregate
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, time, argparse
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import dataclass, asdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

# ================================================================
# CANONICAL OBSERVER CONFIGURATION (FROZEN)
# ================================================================
OBSERVER_POLICY = "hyst_0.01"
HYST_THRESHOLD = 0.01          # margin required to switch k=3↔4
LAMBDA = 1.0                   # drift weight in J_k
MU = 0.5                       # over-fragmentation penalty in J_k
K_LEVELS = [0, 1, 2, 3, 4]
WINDOW = 200                   # observation window size (steps)

# CANONICAL STABILITY METRIC: switches_per_100_windows
# Secondary: dominant_k_fraction, time_stable (first_half == second_half)

# ================================================================
# FROZEN PHYSICS PARAMETERS
# ================================================================
INJECTION_STEPS = 300; INJECT_INTERVAL = 3
QUIET_STEPS = 5000
BETA = 1.0; NODE_DECAY = 0.005; BIAS = 0.7; C_MAX = 1.0
E_YIELD_SYN = 0.08; E_YIELD_AUTO = 0.00; TOPO_VAR = 0.20

BASE_PARAMS = {
    "reaction_energy_threshold": 0.26, "link_death_threshold": 0.007,
    "background_injection_prob": 0.003, "exothermic_release_amount": 0.17,
    "latent_to_active_threshold": 0.07, "latent_refresh_rate": 0.003,
    "auto_growth_rate": 0.03,
}

PLB_GRID = [0.007, 0.008, 0.010]
RATE_GRID = [0.0005, 0.001, 0.002, 0.005]
ALL_SEEDS = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337]
OUTPUT_DIR = Path("outputs_v19g_canon")


# ================================================================
# CANONICAL LABEL FUNCTION (k=0..4)
# ================================================================
def ctx_label(ctx, k):
    """Deterministic C′ label at resolution k. FROZEN."""
    if k == 0: return "C"
    rb = ctx.get("r_bits", "000")
    s = int(rb[0]); m = int(rb[1]) if len(rb) >= 2 else 0
    w = int(rb[2]) if len(rb) >= 3 else 0
    res = "High" if s else ("Mid" if m else "Low")
    if k == 1: return f"C_{res}"
    bd = "Edge" if ctx.get("boundary_mid", 0) == 1 else "Core"
    if k == 2: return f"C_{res}_{bd}"
    scale = "Strong" if s else ("Mid" if m else ("WeakOnly" if w else "None"))
    if k == 3: return f"C_{res}_{bd}_{scale}"
    ie = "1p" if ctx.get("intrusion_bin", 0) >= 1 else "0"
    return f"C_{res}_{bd}_{scale}_{ie}"


# ================================================================
# CANONICAL J_k COMPUTATION
# ================================================================
def shannon(c):
    t = sum(c)
    if t == 0: return 0.0
    return -sum((x/t)*np.log2(x/t) for x in c if x > 0)

def compute_J(nodes, prev_nodes, k):
    labs = [ctx_label(n, k) for n in nodes]
    counts = Counter(labs); tc = len(counts); H = shannon(list(counts.values()))
    drift = None
    if prev_nodes:
        l1 = Counter(ctx_label(n, k) for n in prev_nodes)
        l2 = counts; al = set(l1)|set(l2)
        t1 = sum(l1.values()); t2 = sum(l2.values())
        if t1 > 0 and t2 > 0 and al:
            p = np.array([l1.get(l,0)/t1 for l in al])
            q = np.array([l2.get(l,0)/t2 for l in al])
            mm = (p+q)/2
            kl = lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
            drift = round(float(np.sqrt((kl(p,mm)+kl(q,mm))/2)), 4)
    tD = LAMBDA * drift if drift is not None else 0
    J = round(H + tD - MU * np.log2(tc + 1), 4)
    return J, round(H, 4), drift, tc


# ================================================================
# CANONICAL k* SELECTION (hyst_0.01)
# ================================================================
def select_k_star(j_scores, current_k):
    """Select k* using hyst_0.01 rule. FROZEN.
    j_scores: dict k -> J value
    current_k: previous k* (None for first window)
    Returns: new k*
    """
    if current_k is None:
        return max(j_scores, key=lambda k: j_scores[k])

    # For k=3↔4 boundary: apply hysteresis
    j3 = j_scores.get(3, -999); j4 = j_scores.get(4, -999)
    margin = j4 - j3

    if current_k == 3 and margin >= HYST_THRESHOLD:
        candidate = 4
    elif current_k == 4 and margin <= -HYST_THRESHOLD:
        candidate = 3
    elif current_k in (3, 4):
        candidate = current_k  # hold
    else:
        # For other k levels, use argmax (no hysteresis needed)
        candidate = max(j_scores, key=lambda k: j_scores[k])

    # Ensure candidate is competitive with non-3/4 options
    best_other = max((k for k in j_scores if k not in (3, 4)),
                     key=lambda k: j_scores[k], default=None)
    if best_other is not None and j_scores[best_other] > j_scores[candidate]:
        candidate = best_other

    return candidate


# ================================================================
# SWITCH EVENT LOG
# ================================================================
@dataclass
class SwitchEvent:
    seed: int; N: int; window: int; step: int
    prev_k: int; new_k: int
    margin: float; threshold: float
    j3: float; j4: float; h3: float; h4: float


# ================================================================
# SIMULATION RUNNER
# ================================================================
def init_fert(state, v, seed):
    rng = np.random.RandomState(seed + 7777)
    if v <= 0: state.F = np.ones(state.n_nodes); return
    u = rng.uniform(-1, 1, state.n_nodes); raw = 1.0 + v * u
    raw = np.clip(raw, 0.01, 2.0); state.F = raw / raw.mean()


def run_canonical(seed, N, plb, rate, quiet_steps=QUIET_STEPS):
    """Run with canonical frozen observer. Returns structured result."""
    p = dict(BASE_PARAMS); p["p_link_birth"] = plb
    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)
    physics = GenesisPhysics(PhysicsParams(exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA, decay_rate_node=NODE_DECAY,
        K_sync=0.1, alpha=0.0, gamma=1.0))
    cp = ChemistryParams(enabled=True, E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],
        E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO)
    chem = ChemistryEngine(cp)
    rp = RealizationParams(enabled=True, p_link_birth=plb,
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer = RealizationOperator(rp)
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True,
        auto_growth_rate=p["auto_growth_rate"]))
    intruder = BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION = p["link_death_threshold"]
    g_scores = np.zeros(N); t0 = time.time()
    node_intr = Counter()

    # Injection
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state); chem.step(state)
        cd = physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state)

    # Quiet: canonical observation
    k_star_seq = []; switch_events = []; margin_seq = []
    prev_nodes = None; current_k = None
    island_summaries = []

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        chem.step(state); physics.step_resonance(state)
        g_scores[:] = 0; grower.step(state)
        for k in state.alive_l:
            r = state.R.get(k, 0.0)
            if r > 0:
                a = min(grower.params.auto_growth_rate * r,
                        max(state.get_latent(k[0], k[1]), 0))
                if a > 0: g_scores[k[0]] += a; g_scores[k[1]] += a
        gz = float(g_scores.sum())
        pre_S = {k: state.S[k] for k in state.alive_l}
        intruder.step(state)
        for k in state.alive_l:
            if k in pre_S and abs(state.S[k] - pre_S[k]) > 0.001:
                node_intr[k[0]] += 1; node_intr[k[1]] += 1
        physics.step_decay_exclusion(state)

        # Seeding
        al = list(state.alive_n); na = len(al)
        if na > 0:
            aa = np.array(al)
            if BIAS > 0 and gz > 0:
                ga = g_scores[aa]; gs = ga.sum()
                if gs > 0:
                    pg = ga / gs
                    pd = (1-BIAS)*(np.ones(na)/na) + BIAS*pg; pd /= pd.sum()
                else: pd = np.ones(na) / na
            else: pd = np.ones(na) / na
            mk = state.rng.random(na) < BASE_PARAMS["background_injection_prob"]
            for idx in range(na):
                if mk[idx]:
                    t = int(state.rng.choice(aa, p=pd))
                    state.E[t] = min(1.0, state.E[t] + 0.3)
                    if state.Z[t] == 0 and state.rng.random() < 0.5:
                        state.Z[t] = 1 if state.rng.random() < 0.5 else 2

        # Window observation
        if (step + 1) % WINDOW == 0:
            isl_s = find_islands_sets(state, 0.30)
            isl_m = find_islands_sets(state, 0.20)
            isl_w = find_islands_sets(state, 0.10)
            nm_s = {n: 1 for isl in isl_s for n in isl}
            nm_m = {n: 1 for isl in isl_m for n in isl}
            nm_w = {n: 1 for isl in isl_w for n in isl}
            bnd_m = set()
            for isl in isl_m:
                for n in isl:
                    if n not in state.alive_n: continue
                    for nb in state.neighbors(n):
                        if nb in state.alive_n and nb not in isl:
                            bnd_m.add(n); break

            nodes = []
            for i in state.alive_n:
                if int(state.Z[i]) != 3: continue
                s = 1 if i in nm_s else 0
                m = 1 if i in nm_m else 0
                w = 1 if i in nm_w else 0
                nodes.append({
                    "r_bits": f"{s}{m}{w}",
                    "boundary_mid": 1 if i in bnd_m else 0,
                    "intrusion_bin": min(node_intr.get(i, 0), 2),
                })

            if nodes:
                j_scores = {}
                h_scores = {}
                for k in K_LEVELS:
                    j, h, dr, tc = compute_J(nodes, prev_nodes, k)
                    j_scores[k] = j; h_scores[k] = h

                new_k = select_k_star(j_scores, current_k)
                margin = round(j_scores.get(4, 0) - j_scores.get(3, 0), 4)
                margin_seq.append(margin)

                # Log switch event
                if current_k is not None and new_k != current_k:
                    switch_events.append(SwitchEvent(
                        seed=seed, N=N, window=len(k_star_seq)+1,
                        step=INJECTION_STEPS + step + 1,
                        prev_k=current_k, new_k=new_k,
                        margin=margin, threshold=HYST_THRESHOLD,
                        j3=j_scores.get(3, 0), j4=j_scores.get(4, 0),
                        h3=h_scores.get(3, 0), h4=h_scores.get(4, 0),
                    ))

                current_k = new_k
                k_star_seq.append(new_k)

                # Island summary
                island_summaries.append({
                    "n_islands_strong": len(isl_s),
                    "n_islands_mid": len(isl_m),
                    "n_islands_weak": len(isl_w),
                    "n_C": len(nodes),
                    "none_ratio": round(sum(1 for n in nodes if n["r_bits"]=="000")/max(len(nodes),1), 4),
                })
            else:
                k_star_seq.append(current_k or 0)

            prev_nodes = nodes
            node_intr.clear()

        if step % 1000 == 999:
            print(f"      q{step+1}/{quiet_steps}: N={N} L={len(state.alive_l)} "
                  f"k*={current_k} ({time.time()-t0:.0f}s)", flush=True)

    # ================================================================
    # CANONICAL RESULT ASSEMBLY
    # ================================================================
    elapsed = time.time() - t0
    n_windows = len(k_star_seq)
    kd = Counter(k_star_seq)
    dom_k = kd.most_common(1)[0][0] if kd else 0
    dom_frac = kd.most_common(1)[0][1] / max(n_windows, 1) if kd else 0
    n_switches = len(switch_events)
    sw_per_100 = round(n_switches / max(n_windows / 100, 1), 2)

    mid = n_windows // 2
    first_dom = Counter(k_star_seq[:mid]).most_common(1)[0][0] if mid > 0 else 0
    second_dom = Counter(k_star_seq[mid:]).most_common(1)[0][0] if mid > 0 else 0
    time_stable = first_dom == second_dom

    # Island summary averages
    mean_isl_strong = np.mean([s["n_islands_strong"] for s in island_summaries]) if island_summaries else 0
    mean_isl_mid = np.mean([s["n_islands_mid"] for s in island_summaries]) if island_summaries else 0
    mean_none = np.mean([s["none_ratio"] for s in island_summaries]) if island_summaries else 0
    mean_nC = np.mean([s["n_C"] for s in island_summaries]) if island_summaries else 0

    result = {
        # Identity
        "N": N, "seed": int(seed), "plb": plb, "rate": rate,
        "quiet_steps": quiet_steps, "n_windows": n_windows,
        # Observer
        "policy": OBSERVER_POLICY, "hyst_threshold": HYST_THRESHOLD,
        # Primary metrics
        "dominant_k": dom_k, "dominant_k_fraction": round(dom_frac, 4),
        "switch_count": n_switches,
        "switches_per_100": sw_per_100,  # CANONICAL stability metric
        "time_stable": time_stable,
        "first_half_dom": first_dom, "second_half_dom": second_dom,
        # k distribution
        "k_dist": {str(k): kd.get(k, 0) for k in K_LEVELS},
        # Margin
        "mean_margin": round(np.mean(margin_seq), 4) if margin_seq else 0,
        "pct_close_002": round(sum(1 for m in margin_seq if abs(m)<0.02)/max(len(margin_seq),1)*100, 1),
        # Island/cluster summary
        "mean_islands_strong": round(mean_isl_strong, 2),
        "mean_islands_mid": round(mean_isl_mid, 2),
        "mean_none_ratio": round(mean_none, 4),
        "mean_n_C": round(mean_nC, 1),
        # Runtime
        "elapsed": round(elapsed, 1),
    }

    # Switch event log
    switch_log = [asdict(se) for se in switch_events]

    return result, switch_log


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results = []
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: results.append(json.load(fh))
    if not results:
        print("  No results found."); return

    # Save flat summary
    flat = []
    for r in results:
        row = {k: (v if not isinstance(v, dict) else json.dumps(v)) for k, v in r.items()}
        flat.append(row)
    with open(OUTPUT_DIR / "v19g_canon_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=flat[0].keys()); w.writeheader(); w.writerows(flat)

    # Aggregate by (N, plb, rate)
    agg = []
    for N_val in sorted(set(r["N"] for r in results)):
        for plb in PLB_GRID:
            for rate in RATE_GRID:
                sub = [r for r in results
                       if r["N"] == N_val and abs(r["plb"]-plb) < 1e-6
                       and abs(r["rate"]-rate) < 1e-6]
                if not sub: continue
                doms = [r["dominant_k"] for r in sub]
                maj = Counter(doms).most_common(1)[0]
                agg.append({
                    "N": N_val, "plb": plb, "rate": rate, "n_seeds": len(sub),
                    "policy": OBSERVER_POLICY,
                    "dominant_k": maj[0],
                    "agree_pct": round(maj[1]/len(sub)*100, 0),
                    "med_sw_100": round(np.median([r["switches_per_100"] for r in sub]), 1),
                    "med_dom_frac": round(np.median([r["dominant_k_fraction"] for r in sub]), 3),
                    "time_stable_count": sum(1 for r in sub if r["time_stable"]),
                    "mean_margin": round(np.mean([r["mean_margin"] for r in sub]), 4),
                    "mean_islands_strong": round(np.mean([r["mean_islands_strong"] for r in sub]), 2),
                    "mean_islands_mid": round(np.mean([r["mean_islands_mid"] for r in sub]), 2),
                    "mean_none_ratio": round(np.mean([r["mean_none_ratio"] for r in sub]), 4),
                    "mean_n_C": round(np.mean([r["mean_n_C"] for r in sub]), 1),
                })

    with open(OUTPUT_DIR / "v19g_canon_aggregate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    # Print comparison table
    print(f"\n{'='*80}")
    print(f"  v1.9g CANONICAL COMPARISON (policy={OBSERVER_POLICY})")
    print(f"{'='*80}")
    print(f"\n  {'N':>4} {'plb':>5} {'rate':>7} | {'k*':>3} {'agree':>6} {'sw/100':>7} "
          f"{'stable':>7} | {'isl_s':>5} {'isl_m':>5} {'none':>6} {'n_C':>5}")
    for a in agg:
        print(f"  {a['N']:>4} {a['plb']:>5.3f} {a['rate']:>7.4f} | "
              f"k={a['dominant_k']} {a['agree_pct']:>5.0f}% {a['med_sw_100']:>7.1f} "
              f"{a['time_stable_count']:>4}/{a['n_seeds']} | "
              f"{a['mean_islands_strong']:>5.1f} {a['mean_islands_mid']:>5.1f} "
              f"{a['mean_none_ratio']:>6.3f} {a['mean_n_C']:>5.1f}")

    # Plots: N=200 vs N=500 comparison
    n_vals = sorted(set(a["N"] for a in agg))
    if len(n_vals) >= 2:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"ESDE Genesis v1.9g — Scale Transfer (N={' vs '.join(map(str,n_vals))})",
                     fontsize=14, fontweight="bold")

        for ni, N_val in enumerate(n_vals):
            sub = [a for a in agg if a["N"] == N_val]
            for pi, plb in enumerate(PLB_GRID):
                ps = [a for a in sub if abs(a["plb"]-plb) < 1e-6]
                if not ps: continue
                rs = [a["rate"] for a in ps]
                style = "o-" if N_val == n_vals[0] else "s--"

                axes[0][0].plot(rs, [a["agree_pct"] for a in ps], style,
                               label=f"N={N_val} plb={plb}", ms=6, lw=1.5)
                axes[0][1].plot(rs, [a["med_sw_100"] for a in ps], style,
                               label=f"N={N_val} plb={plb}", ms=6, lw=1.5)
                axes[1][0].plot(rs, [a["dominant_k"] for a in ps], style,
                               label=f"N={N_val} plb={plb}", ms=8, lw=2)
                axes[1][1].plot(rs, [a["mean_none_ratio"] for a in ps], style,
                               label=f"N={N_val} plb={plb}", ms=6, lw=1.5)

        axes[0][0].axhline(y=80, color="red", ls="--", alpha=0.5)
        axes[0][0].set_title("Seed Agreement (%)"); axes[0][0].legend(fontsize=6)
        axes[0][0].grid(True, alpha=0.2)
        axes[0][1].set_title("Switch Rate (/100 win)"); axes[0][1].legend(fontsize=6)
        axes[0][1].grid(True, alpha=0.2)
        axes[1][0].set_title("Dominant k*"); axes[1][0].set_yticks(K_LEVELS)
        axes[1][0].legend(fontsize=6); axes[1][0].grid(True, alpha=0.2)
        axes[1][1].set_title("None Ratio (C nodes)"); axes[1][1].legend(fontsize=6)
        axes[1][1].grid(True, alpha=0.2)

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "v19g_scale_comparison.png", dpi=150, bbox_inches="tight")
        print(f"\n  Plot: {OUTPUT_DIR / 'v19g_scale_comparison.png'}")

    # Interpretation
    n200 = [a for a in agg if a["N"] == 200]
    n500 = [a for a in agg if a["N"] == 500]

    if n200 and n500:
        k4_200 = all(a["dominant_k"] == 4 for a in n200)
        k4_500 = all(a["dominant_k"] == 4 for a in n500)
        k3_in_500 = any(a["dominant_k"] == 3 for a in n500)
        mixed_500 = any(a["agree_pct"] < 80 for a in n500)

        if k4_500 and not mixed_500:
            branch = "Branch 1: k=4 robust across scale"
        elif k3_in_500:
            branch = "Branch 2: k=3 re-emerges at N=500"
        else:
            branch = "Branch 3: mixed/unstable at N=500"
    else:
        branch = "Incomplete data — run both N=200 and N=500"

    conclusion = f"""# ESDE Genesis v1.9g — Canonical Freeze + Scale Transfer

## Observer Freeze Note
Policy: {OBSERVER_POLICY}
Hysteresis threshold: {HYST_THRESHOLD}
Stability metric: switches_per_100_windows (canonical)
Label function: ctx_label(ctx, k) for k=0..4 (frozen)
k=3 bins: None / WeakOnly / Mid / Strong
k=4 adds: Intrusion exposure (0 / 1+)

## Results
Runs: {len(results)} total ({len(n200)} at N=200, {len(n500)} at N=500)

{'## N=200 vs N=500 Comparison' if n200 and n500 else ''}
{'| N | Rate | k* | Agree | sw/100 | None ratio | Islands(mid) |' if n200 and n500 else ''}
{'|---|------|----|----|--------|---------|---------|' if n200 and n500 else ''}
{chr(10).join(f'| {a["N"]} | {a["rate"]} | k={a["dominant_k"]} | {a["agree_pct"]}% | {a["med_sw_100"]} | {a["mean_none_ratio"]:.3f} | {a["mean_islands_mid"]:.1f} |' for a in agg)}

## Interpretation
{branch}

## Audit Checklist
[AC-1] hyst_0.01 frozen as canonical: YES (OBSERVER_POLICY constant)
[AC-2] k-switch logged: YES (SwitchEvent dataclass, per-run JSON)
[AC-3] Stability metric canonical: YES (switches_per_100_windows)
[AC-4] N=500 without theory patches: {'YES' if n500 else 'PENDING'}
[AC-5] Comparable outputs: YES (identical schema)
[AC-6] No ontology expansion: YES
"""
    with open(OUTPUT_DIR / "v19g_canon_conclusion.md", "w") as f:
        f.write(conclusion)
    print(conclusion)


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="v1.9g Canonical Freeze + Scale Transfer")
    parser.add_argument("--N", type=int, default=200)
    parser.add_argument("--plb", type=float, default=None)
    parser.add_argument("--rate", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N=200 plb=0.010 rate=0.001 seed=42 quiet=500")
        r, sw = run_canonical(42, 200, 0.010, 0.001, 500)
        print(f"  k*={r['dominant_k']} sw={r['switches_per_100']} "
              f"stable={r['time_stable']} policy={r['policy']}")
        print(f"  N=500 sanity:")
        r5, sw5 = run_canonical(42, 500, 0.010, 0.001, 500)
        print(f"  k*={r5['dominant_k']} sw={r5['switches_per_100']} "
              f"n_C={r5['mean_n_C']} isl_mid={r5['mean_islands_mid']}")
        print("  OK"); return

    if args.aggregate:
        aggregate(); return

    # Run mode
    N = args.N; qs = args.quiet_steps
    plbs = [args.plb] if args.plb else PLB_GRID
    rates = [args.rate] if args.rate is not None else RATE_GRID
    seeds = [args.seed] if args.seed else ALL_SEEDS

    for plb in plbs:
        for rate in rates:
            for seed in seeds:
                tag = f"N{N}_plb{plb:.3f}_rate{rate:.4f}"
                od = OUTPUT_DIR / tag; od.mkdir(parents=True, exist_ok=True)
                rf = od / f"seed_{seed}.json"
                if rf.exists():
                    print(f"  {tag} s={seed}: skip"); continue
                print(f"  {tag} s={seed}...", flush=True)
                result, switch_log = run_canonical(seed, N, plb, rate, qs)
                with open(rf, "w") as f:
                    json.dump(result, f, indent=2)
                if switch_log:
                    with open(od / f"seed_{seed}_switches.json", "w") as f:
                        json.dump(switch_log, f, indent=2)
                print(f"    k*={result['dominant_k']} sw={result['switches_per_100']} "
                      f"({result['elapsed']:.0f}s)")


if __name__ == "__main__":
    main()
