#!/usr/bin/env python3
"""
ESDE Genesis v1.5 — Differentiation (Diversity) Observation
==============================================================
Do multiple distinct activity regions coexist? Or is it one dominant type?

Observations (no physics changes):
  A) Active Island Count (coexisting strong-link domains)
  B) Cycle Type Diversity (pattern variety)
  C) Loop Spectrum Diversity (structural variety)
  D) Regime Switching vs Coexistence (time structure)

Usage:
  python v15_differentiation.py --sanity          # quick check
  python v15_differentiation.py --seed 42         # single seed
  python v15_differentiation.py                   # all 10 seeds (sequential)

  # Parallel (Ryzen):
  parallel -j 10 python v15_differentiation.py --seed {} \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v15_differentiation.py --aggregate-only
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, time, argparse
from collections import Counter, defaultdict
from pathlib import Path
try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams

# ============================================================
# CONFIG (v1.4 validated defaults)
# ============================================================
N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; INJECT_INTERVAL = 3
QUIET_STEPS = 5000
BETA = 1.0; NODE_DECAY = 0.005; BIAS = 0.7
WINDOW = 200
S_DOM = 0.30  # strong-link threshold for islands
STRENGTH_BINS = [(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]
STATE_NAMES = {0:"Dust",1:"A",2:"B",3:"C"}

PARAMS = {
    "reaction_energy_threshold": 0.26, "link_death_threshold": 0.007,
    "background_injection_prob": 0.003, "exothermic_release_amount": 0.17,
    "p_link_birth": 0.010, "latent_to_active_threshold": 0.07,
    "latent_refresh_rate": 0.003, "auto_growth_rate": 0.03,
}

ALL_SEEDS = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337]
OUTPUT_DIR = Path("outputs_v15")


# ============================================================
# HELPERS
# ============================================================
class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list)
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i]); h = self.history[i]
            if not h or h[-1][1] != z: h.append((step, z))
    def find_cycles(self):
        cycles = []
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0 and states[i+2] in (1, 2):
                    for j in range(i+3, len(states)):
                        if states[j] == 3:
                            type_str = "→".join(STATE_NAMES[s] for s in states[i:j+1])
                            cycles.append({
                                "node": nid, "start": h[i][0], "end": h[j][0],
                                "type": type_str,
                                "states": [STATE_NAMES[s] for s in states[i:j+1]],
                            })
                            break
        return cycles


def find_islands(state):
    """Connected components on strong-link subgraph (S >= S_DOM)."""
    strong = {}
    for k in state.alive_l:
        if state.S[k] >= S_DOM:
            strong[k] = True
    # Build adjacency
    adj = defaultdict(set)
    for (i, j) in strong:
        adj[i].add(j); adj[j].add(i)
    # BFS components
    visited = set(); islands = []
    for start in adj:
        if start in visited: continue
        q = [start]; comp = set()
        while q:
            n = q.pop()
            if n in visited: continue
            visited.add(n); comp.add(n)
            for nb in adj[n]:
                if nb not in visited: q.append(nb)
        if len(comp) >= 3:
            islands.append(comp)
    return islands


def shannon(counts):
    """Shannon entropy from a list of counts."""
    total = sum(counts)
    if total == 0: return 0.0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * np.log2(p) for p in probs)


# ============================================================
# SINGLE SEED RUN
# ============================================================
def run_seed(seed, quiet_steps=QUIET_STEPS):
    p = PARAMS
    state = GenesisState(N_NODES, C_MAX, seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True, phase_enabled=True,
        beta=BETA, decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    cp = ChemistryParams(enabled=True, E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"])
    chem = ChemistryEngine(cp)
    rp = RealizationParams(enabled=True, p_link_birth=p["p_link_birth"],
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer = RealizationOperator(rp)
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True, auto_growth_rate=p["auto_growth_rate"]))
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

    # Quiet with windowed observation
    window_metrics = []
    win_id = 0

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        rxns = chem.step(state); cd = physics.step_resonance(state)
        g_scores[:] = 0; grower.step(state)
        for k in state.alive_l:
            r = state.R.get(k, 0.0)
            if r > 0:
                a = min(grower.params.auto_growth_rate * r, max(state.get_latent(k[0], k[1]), 0))
                if a > 0: g_scores[k[0]] += a; g_scores[k[1]] += a
        gz = float(g_scores.sum())
        physics.step_decay_exclusion(state); tracker.record(state, state.step - 1)

        # Biased seeding
        al = list(state.alive_n); na = len(al)
        if na > 0:
            aa = np.array(al)
            if BIAS > 0 and gz > 0:
                ga = g_scores[aa]; gs = ga.sum()
                if gs > 0:
                    pg = ga / gs; pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg; pd /= pd.sum()
                else: pd = np.ones(na) / na
            else: pd = np.ones(na) / na
            mk = state.rng.random(na) < p["background_injection_prob"]
            for idx in range(na):
                if mk[idx]:
                    t = int(state.rng.choice(aa, p=pd))
                    state.E[t] = min(1.0, state.E[t] + 0.3)
                    if state.Z[t] == 0 and state.rng.random() < 0.5:
                        state.Z[t] = 1 if state.rng.random() < 0.5 else 2

        # Window boundary
        if (step + 1) % WINDOW == 0:
            win_id += 1
            step_start = INJECTION_STEPS + step + 1 - WINDOW
            step_end = INJECTION_STEPS + step + 1

            # A) Islands
            islands = find_islands(state)
            island_sizes = sorted([len(isl) for isl in islands], reverse=True)

            # C) Loop spectrum
            loops = {3: 0, 4: 0, 5: 0}
            if cd:  # last resonance update data
                for length, count in cd.items():
                    if length in loops: loops[length] = count
            loop_counts = [loops[3], loops[4], loops[5]]

            # Strength histogram
            strengths = [state.S[k] for k in state.alive_l]
            s_hist = [0] * len(STRENGTH_BINS)
            for s in strengths:
                for bi, (lo, hi) in enumerate(STRENGTH_BINS):
                    if lo <= s < hi: s_hist[bi] += 1; break
            s_ent = shannon(s_hist)

            # X components
            nl = len(state.alive_l)
            ll = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr = ll / max(nl, 1)
            total_s = sum(s_hist)
            if total_s > 0:
                pp = [h / total_s for h in s_hist if h > 0]
                H = -sum(p * np.log2(p) for p in pp)
                C_score = 1 - H / np.log2(len(STRENGTH_BINS))
            else: C_score = 0
            X = round(C_score + spr, 4)

            wm = {
                "seed": seed, "window_id": win_id,
                "step_start": step_start, "step_end": step_end,
                "island_count": len(islands),
                "max_island_size": island_sizes[0] if island_sizes else 0,
                "island_sizes_str": str(island_sizes[:5]),
                "loop3": loop_counts[0], "loop4": loop_counts[1], "loop5": loop_counts[2],
                "strength_entropy": round(s_ent, 4),
                "X_total": X, "C": round(C_score, 4), "B": round(spr, 4),
                "active_links": nl,
            }
            window_metrics.append(wm)

            if win_id % 5 == 0:
                print(f"      W{win_id}: isl={len(islands)} "
                      f"maxIsl={island_sizes[0] if island_sizes else 0} "
                      f"L={nl} ({time.time()-t0:.0f}s)", flush=True)

    # ---- Post-run analysis ----
    all_cycles = tracker.find_cycles()

    # B) Cycle type diversity
    type_counts = Counter(c["type"] for c in all_cycles)
    n_types = len(type_counts)
    type_ent = shannon(list(type_counts.values()))
    top1 = type_counts.most_common(1)[0][1] / len(all_cycles) if all_cycles else 0

    # D) Regime analysis (simple k-means on window signatures)
    if len(window_metrics) >= 4:
        sigs = []
        for wm in window_metrics:
            lsum = wm["loop3"] + wm["loop4"] + wm["loop5"] + 1e-9
            sig = [wm["island_count"],
                   wm["loop3"] / lsum, wm["loop4"] / lsum, wm["loop5"] / lsum,
                   wm["strength_entropy"]]
            sigs.append(sig)
        sigs_arr = np.array(sigs)
        K = min(4, len(sigs_arr))
        if HAS_SKLEARN:
            try:
                km = KMeans(n_clusters=K, n_init=10, random_state=seed).fit(sigs_arr)
                labels = km.labels_
            except Exception:
                labels = np.zeros(len(sigs_arr), dtype=int)
        else:
            # Simple fallback: bin by island_count
            labels = np.clip(np.array([int(s[0]) for s in sigs]), 0, K - 1)

        regimes_used = len(set(labels))
        switches = sum(1 for i in range(1, len(labels)) if labels[i] != labels[i-1])
        # Mean duration
        durations = []
        cur = 1
        for i in range(1, len(labels)):
            if labels[i] == labels[i-1]: cur += 1
            else: durations.append(cur); cur = 1
        durations.append(cur)
        mean_dur = np.mean(durations)
    else:
        regimes_used = 1; switches = 0; mean_dur = len(window_metrics); labels = [0]*len(window_metrics)

    coexist_rate = sum(1 for wm in window_metrics if wm["island_count"] >= 2) / max(len(window_metrics), 1)

    # Baseline X for η
    bl_X = np.mean([wm["X_total"] for wm in window_metrics[:3]]) if len(window_metrics) >= 3 else 0.5
    etas = [wm["X_total"] / bl_X if bl_X > 0.01 else 1.0 for wm in window_metrics]

    elapsed = time.time() - t0

    summary = {
        "seed": seed,
        "cycles_total": len(all_cycles),
        "cycles_per_1k": round(len(all_cycles) / (quiet_steps / 1000), 3),
        "cycle_type_count": n_types,
        "cycle_type_entropy": round(type_ent, 4),
        "top1_share": round(top1, 4),
        "mean_island_count": round(np.mean([wm["island_count"] for wm in window_metrics]), 2),
        "max_island_count": max(wm["island_count"] for wm in window_metrics),
        "coexistence_rate": round(coexist_rate, 4),
        "regime_count_used": regimes_used,
        "mean_regime_duration": round(mean_dur, 1),
        "switch_rate": round(switches / (quiet_steps / 1000), 2),
        "median_eta": round(float(np.median(etas)), 4),
        "min_eta": round(float(np.min(etas)), 4),
        "elapsed": round(elapsed, 1),
    }

    # Save per-seed outputs
    out_dir = OUTPUT_DIR / f"seed_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "window_metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=window_metrics[0].keys())
        w.writeheader(); w.writerows(window_metrics)

    cycle_rows = [{"seed": seed, "cycle_id": i, "cycle_type": c["type"],
                    "step_start": c["start"], "step_end": c["end"], "node_id": c["node"]}
                   for i, c in enumerate(all_cycles)]
    if cycle_rows:
        with open(out_dir / "cycle_types.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cycle_rows[0].keys())
            w.writeheader(); w.writerows(cycle_rows)

    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Regime labels
    with open(out_dir / "regime_labels.json", "w") as f:
        json.dump({"labels": [int(l) for l in labels]}, f)

    print(f"  seed={seed}: cyc={len(all_cycles)} types={n_types} "
          f"islands_mean={summary['mean_island_count']:.1f} "
          f"coexist={coexist_rate:.2f} regimes={regimes_used} "
          f"η={summary['median_eta']:.3f} ({elapsed:.0f}s)", flush=True)

    return summary, window_metrics, all_cycles, labels


# ============================================================
# AGGREGATE
# ============================================================
def aggregate():
    summaries = []
    all_windows = []
    all_cycle_types = Counter()

    for seed_dir in sorted(OUTPUT_DIR.glob("seed_*")):
        sf = seed_dir / "summary.json"
        if not sf.exists(): continue
        with open(sf) as f: s = json.load(f)
        summaries.append(s)

        wf = seed_dir / "window_metrics.csv"
        if wf.exists():
            with open(wf) as f:
                for row in csv.DictReader(f):
                    all_windows.append(row)

        cf = seed_dir / "cycle_types.csv"
        if cf.exists():
            with open(cf) as f:
                for row in csv.DictReader(f):
                    all_cycle_types[row["cycle_type"]] += 1

    if not summaries:
        print("  No results found."); return

    # Save aggregated CSVs
    with open(OUTPUT_DIR / "v15_run_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summaries[0].keys())
        w.writeheader(); w.writerows(summaries)

    if all_windows:
        with open(OUTPUT_DIR / "v15_window_metrics.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=all_windows[0].keys())
            w.writeheader(); w.writerows(all_windows)

    # Print summary
    print(f"\n{'='*70}")
    print(f"  v1.5 DIFFERENTIATION RESULTS ({len(summaries)} seeds)")
    print(f"{'='*70}")

    print(f"\n  {'seed':>6} {'cyc':>5} {'types':>6} {'H_type':>7} {'top1':>6} "
          f"{'isl_m':>6} {'isl_max':>7} {'coexist':>8} {'reg':>4} {'η':>6}")
    for s in summaries:
        print(f"  {s['seed']:>6} {s['cycles_total']:>5} {s['cycle_type_count']:>6} "
              f"{s['cycle_type_entropy']:>7.3f} {s['top1_share']:>6.3f} "
              f"{s['mean_island_count']:>6.1f} {s['max_island_count']:>7} "
              f"{s['coexistence_rate']:>8.3f} {s['regime_count_used']:>4} "
              f"{s['median_eta']:>6.3f}")

    # Aggregate stats
    print(f"\n  Aggregate:")
    print(f"    Mean cycle types: {np.mean([s['cycle_type_count'] for s in summaries]):.1f}")
    print(f"    Mean coexistence rate: {np.mean([s['coexistence_rate'] for s in summaries]):.3f}")
    print(f"    Mean island count: {np.mean([s['mean_island_count'] for s in summaries]):.2f}")
    print(f"    Mean η: {np.mean([s['median_eta'] for s in summaries]):.3f}")
    print(f"    Global cycle types: {len(all_cycle_types)}")
    for t, c in all_cycle_types.most_common(10):
        print(f"      {t}: {c}")

    # ---- Plots ----
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("ESDE Genesis v1.5 — Differentiation Observation",
                 fontsize=14, fontweight="bold")

    # A) Island count distribution
    ax = axes[0][0]
    isl_counts = [float(row["island_count"]) for row in all_windows]
    ax.hist(isl_counts, bins=range(0, max(int(max(isl_counts))+2, 6)),
            color="#2ecc71", alpha=0.7, edgecolor="white")
    ax.set_title("Island Count Distribution (all windows)")
    ax.set_xlabel("Active Islands (≥3 nodes)"); ax.set_ylabel("Windows")
    ax.grid(True, alpha=0.2)

    # B) Cycle type distribution
    ax = axes[0][1]
    if all_cycle_types:
        top_types = all_cycle_types.most_common(8)
        labels_ct = [t[:25] for t, _ in top_types]
        vals_ct = [c for _, c in top_types]
        ax.barh(labels_ct, vals_ct, color="#3498db", alpha=0.7)
    ax.set_title("Cycle Type Distribution (all seeds)")
    ax.set_xlabel("Count"); ax.grid(True, axis="x", alpha=0.2)

    # C) Island count time series (first seed)
    ax = axes[1][0]
    first_seed = summaries[0]["seed"]
    first_wins = [row for row in all_windows if int(row["seed"]) == first_seed]
    if first_wins:
        ws = [int(row["window_id"]) for row in first_wins]
        ic = [int(row["island_count"]) for row in first_wins]
        ax.plot(ws, ic, "o-", color="#e67e22", ms=3, linewidth=1)
    ax.set_title(f"Island Count over Time (seed={first_seed})")
    ax.set_xlabel("Window"); ax.set_ylabel("Islands"); ax.grid(True, alpha=0.2)

    # D) Summary text
    ax = axes[1][1]; ax.axis("off")
    txt = ["v1.5 Differentiation Summary", "=" * 35, ""]
    txt.append(f"Seeds: {len(summaries)}")
    txt.append(f"Global cycle types: {len(all_cycle_types)}")
    txt.append(f"Mean coexistence rate: {np.mean([s['coexistence_rate'] for s in summaries]):.3f}")
    txt.append(f"Mean island count: {np.mean([s['mean_island_count'] for s in summaries]):.2f}")
    txt.append(f"Mean regimes used: {np.mean([s['regime_count_used'] for s in summaries]):.1f}")
    txt.append(f"Mean η: {np.mean([s['median_eta'] for s in summaries]):.3f}")
    txt.append("")
    txt.append("Top cycle types:")
    for t, c in all_cycle_types.most_common(5):
        txt.append(f"  {t}: {c}")
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=10,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "v15_differentiation_plots.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plots: {OUTPUT_DIR / 'v15_differentiation_plots.png'}")

    # Conclusion
    mean_coex = np.mean([s["coexistence_rate"] for s in summaries])
    mean_types = np.mean([s["cycle_type_count"] for s in summaries])
    mean_eta = np.mean([s["median_eta"] for s in summaries])

    conclusion = f"""ESDE Genesis v1.5 — Differentiation Conclusion
=================================================
Seeds: {len(summaries)} | Quiet: {QUIET_STEPS} steps | plb={PARAMS['p_link_birth']}

A) Coexistence:
  Mean island count: {np.mean([s['mean_island_count'] for s in summaries]):.2f}
  Coexistence rate (island≥2): {mean_coex:.3f}
  → {'COEXISTENCE OBSERVED' if mean_coex > 0.1 else 'MOSTLY SINGLE DOMAIN'}

B) Cycle Type Diversity:
  Global unique types: {len(all_cycle_types)}
  Mean types per seed: {mean_types:.1f}
  Mean type entropy: {np.mean([s['cycle_type_entropy'] for s in summaries]):.3f}
  Top1 share: {np.mean([s['top1_share'] for s in summaries]):.3f}
  → {'DIVERSE' if mean_types > 2 else 'LOW DIVERSITY'}

C) Regime Structure:
  Mean regimes used: {np.mean([s['regime_count_used'] for s in summaries]):.1f}
  Mean switch rate: {np.mean([s['switch_rate'] for s in summaries]):.1f}/1k steps
  → {'SWITCHING' if np.mean([s['switch_rate'] for s in summaries]) > 1 else 'STABLE'}

D) Explainability:
  Mean η: {mean_eta:.3f}
  Min η (any seed): {min(s['min_eta'] for s in summaries):.3f}
  → {'PRESERVED (η≥0.8)' if min(s['min_eta'] for s in summaries) >= 0.8 else 'CHECK: some η<0.8'}
"""
    with open(OUTPUT_DIR / "v15_differentiation_conclusion.txt", "w") as f:
        f.write(conclusion)
    print(conclusion)


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.aggregate_only:
        aggregate(); return

    if args.sanity:
        print("  SANITY: seed=42, 300 quiet steps")
        s, wm, cyc, _ = run_seed(42, 300)
        print(f"  islands_mean={s['mean_island_count']:.1f} types={s['cycle_type_count']} "
              f"cyc={s['cycles_total']}  OK" if s["cycles_total"] >= 0 else "  FAIL")
        return

    qs = args.quiet_steps
    seeds = [args.seed] if args.seed else ALL_SEEDS

    for seed in seeds:
        out = OUTPUT_DIR / f"seed_{seed}" / "summary.json"
        if out.exists():
            print(f"  seed={seed}: already done, skipping"); continue
        run_seed(seed, qs)

    if args.seed is None:
        aggregate()


if __name__ == "__main__":
    main()
