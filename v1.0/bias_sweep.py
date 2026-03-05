"""
ESDE Genesis v1.0 — Bias Sweep + Explainability X
====================================================
Map the habitable zone of growth_seeding_bias.
Controller FROZEN (isolate bias effect). 10 seeds × 5 bias values.

X = R(reproducibility) + C(compressibility) + B(boundary-ness)

No design changes. Measurement only.
"""

import numpy as np
import matplotlib.pyplot as plt
import csv, json, time
from collections import Counter, defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; INJECT_INTERVAL = 3
BETA = 1.0; NODE_DECAY = 0.005
STATE_NAMES = {0: "Dust", 1: "A", 2: "B", 3: "C"}
STRENGTH_BINS = [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 1.01)]

# Frozen params from best v0.9 run
FIXED = {
    "reaction_energy_threshold": 0.26, "link_death_threshold": 0.007,
    "background_injection_prob": 0.003, "exothermic_release_amount": 0.17,
    "p_link_birth": 0.007, "latent_to_active_threshold": 0.07,
    "latent_refresh_rate": 0.003, "auto_growth_rate": 0.03,
}


class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list); self.completed = []
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i]); h = self.history[i]
            if not h or h[-1][1] != z: h.append((step, z))
    def detect_cycles(self):
        self.completed = []
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0 and states[i+2] in (1, 2):
                    for j in range(i+3, len(states)):
                        if states[j] == 3:
                            self.completed.append({"node": nid, "start": h[i][0], "end": h[j][0]})
                            break
        return self.completed


def run_one(seed, bias, quiet_steps=2000):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True, phase_enabled=True,
        beta=BETA, decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem_params = ChemistryParams(enabled=True,
        E_thr=FIXED["reaction_energy_threshold"],
        exothermic_release=FIXED["exothermic_release_amount"])
    chem = ChemistryEngine(chem_params)
    rp = RealizationParams(enabled=True, p_link_birth=FIXED["p_link_birth"],
        latent_to_active_threshold=FIXED["latent_to_active_threshold"],
        latent_refresh_rate=FIXED["latent_refresh_rate"])
    realizer = RealizationOperator(rp)
    gp = AutoGrowthParams(enabled=True, auto_growth_rate=FIXED["auto_growth_rate"])
    grower = AutoGrowthEngine(gp)
    state.EXTINCTION = FIXED["link_death_threshold"]
    logger = GenesisLogger()
    tracker = CycleTracker()
    g_scores = np.zeros(N_NODES)

    # Injection
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        chem.step(state)
        cd = physics.step_resonance(state)
        if cd: logger.observe_loops(cd)
        grower.step(state)
        physics.step_decay_exclusion(state)
        logger.observe(state)
        tracker.record(state, state.step - 1)

    # Accumulators
    total_opp = 0; total_nm = 0; total_miss = Counter()
    spr_vals = []; strength_hists = []; loop_fracs = []
    min_links = 9999

    for step in range(quiet_steps):
        realizer.step(state)
        physics.step_pre_chemistry(state)
        rxns = chem.step(state)
        cd = physics.step_resonance(state)
        if cd: logger.observe_loops(cd)

        g_scores[:] = 0.0
        grower.step(state)
        for k in state.alive_l:
            r_ij = state.R.get(k, 0.0)
            if r_ij > 0:
                actual = min(grower.params.auto_growth_rate * r_ij, max(state.get_latent(k[0], k[1]), 0))
                if actual > 0:
                    g_scores[k[0]] += actual; g_scores[k[1]] += actual
        gz_mass = float(g_scores.sum())

        physics.step_decay_exclusion(state)
        logger.observe(state, event="quiet", reactions=rxns)
        tracker.record(state, state.step - 1)

        # Biased seeding
        bg_prob = FIXED["background_injection_prob"]
        alive_list = list(state.alive_n)
        n_alive = len(alive_list)
        if n_alive > 0:
            alive_arr = np.array(alive_list)
            if bias > 0 and gz_mass > 0:
                g_alive = g_scores[alive_arr]
                g_sum = g_alive.sum()
                if g_sum > 0:
                    pg = g_alive / g_sum
                    p_dist = (1 - bias) * (np.ones(n_alive)/n_alive) + bias * pg
                    p_dist /= p_dist.sum()
                else:
                    p_dist = np.ones(n_alive)/n_alive
            else:
                p_dist = np.ones(n_alive)/n_alive

            mask = state.rng.random(n_alive) < bg_prob
            for idx in range(n_alive):
                if mask[idx]:
                    target = int(state.rng.choice(alive_arr, p=p_dist))
                    state.E[target] = min(1.0, state.E[target] + 0.3)
                    if state.Z[target] == 0 and state.rng.random() < 0.5:
                        state.Z[target] = 1 if state.rng.random() < 0.5 else 2

        # Metrics every 50 steps
        if step % 50 == 49:
            n_links = len(state.alive_l)
            min_links = min(min_links, n_links)
            strengths = [state.S[k] for k in state.alive_l]
            loop_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr = loop_links / max(n_links, 1)
            spr_vals.append(spr)
            loop_fracs.append(loop_links / max(n_links, 1))

            # Strength bin histogram
            hist = [0]*len(STRENGTH_BINS)
            for s in strengths:
                for bi, (lo, hi) in enumerate(STRENGTH_BINS):
                    if lo <= s < hi: hist[bi] += 1; break
            strength_hists.append(hist)

            # Opportunities/near-misses
            for k in state.alive_l:
                i, j = k; s = state.S[k]
                c_s = s >= 0.3
                c_e = state.E[i] >= chem_params.E_thr and state.E[j] >= chem_params.E_thr
                c_st = int(state.Z[i]) in (1,2) or int(state.Z[j]) in (1,2)
                c_sy = np.cos(state.theta[j]-state.theta[i]) >= 0.7
                n_met = sum([c_s, c_e, c_st, c_sy])
                if n_met == 4: total_opp += 1
                elif n_met == 3:
                    total_nm += 1
                    if not c_s: total_miss["strong"] += 1
                    if not c_e: total_miss["energy"] += 1
                    if not c_st: total_miss["state"] += 1
                    if not c_sy: total_miss["sync"] += 1

    all_cycles = tracker.detect_cycles()
    total_steps = INJECTION_STEPS + quiet_steps

    # Compressibility: 1 - H(strength_bins)/log(K)
    if strength_hists:
        mean_hist = np.mean(strength_hists, axis=0)
        total_h = mean_hist.sum()
        if total_h > 0:
            p = mean_hist / total_h; p = p[p > 0]
            H = -np.sum(p * np.log2(p))
            C_score = 1.0 - H / np.log2(len(STRENGTH_BINS))
        else:
            C_score = 0.0
    else:
        C_score = 0.0

    return {
        "seed": seed, "bias": bias,
        "cycles": len(all_cycles),
        "cycles_per_1k": round(len(all_cycles) / (total_steps / 1000), 3),
        "opp_rate": round(total_opp / max(quiet_steps/50, 1), 3),
        "nm_rate": round(total_nm / max(quiet_steps/50, 1), 3),
        "miss_strong_share": round(total_miss.get("strong", 0) / max(total_nm, 1), 3),
        "miss_energy_share": round(total_miss.get("energy", 0) / max(total_nm, 1), 3),
        "miss_state_share": round(total_miss.get("state", 0) / max(total_nm, 1), 3),
        "miss_sync_share": round(total_miss.get("sync", 0) / max(total_nm, 1), 3),
        "spr_mean": round(np.mean(spr_vals), 4) if spr_vals else 0,
        "loop_edge_frac": round(np.mean(loop_fracs), 4) if loop_fracs else 0,
        "min_links": min_links if min_links < 9999 else 0,
        "compressibility": round(C_score, 4),
        "strength_entropy": round(H if 'H' in dir() else 0, 4),
    }


def main():
    print("=" * 70)
    print("  ESDE Genesis v1.0 — Bias Sweep + Explainability X")
    print("  Controller FROZEN. Sweep b ∈ {0.0, 0.2, 0.4, 0.6, 0.8}")
    print("=" * 70)

    biases = [0.0, 0.2, 0.4, 0.6, 0.8]
    seeds = [42, 123, 789, 2024, 1337]
    QUIET = 800
    all_results = []

    for b in biases:
        print(f"\n  bias={b:.1f}:")
        for seed in seeds:
            t0 = time.time()
            r = run_one(seed, b, QUIET)
            all_results.append(r)
            cyc = r["cycles"]; opp = r["opp_rate"]
            print(f"    s={seed:>5} cyc={cyc:>3} opp={opp:>6.1f} "
                  f"spr={r['spr_mean']:.3f} C={r['compressibility']:.3f} "
                  f"({time.time()-t0:.0f}s)")

    # Save sweep_summary
    with open("sweep_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_results[0].keys())
        w.writeheader(); w.writerows(all_results)

    # Aggregate per bias
    agg = []
    for b in biases:
        subset = [r for r in all_results if r["bias"] == b]
        cyc_vals = [r["cycles_per_1k"] for r in subset]
        opp_vals = [r["opp_rate"] for r in subset]
        spr_vals = [r["spr_mean"] for r in subset]
        comp_vals = [r["compressibility"] for r in subset]

        # Reproducibility R: 1 - normalized variance of key metrics
        def norm_var(vals):
            if len(vals) < 2 or np.mean(vals) == 0: return 0
            return np.std(vals) / (np.mean(vals) + 1e-9)

        R_score = 1.0 - np.mean([norm_var(cyc_vals), norm_var(opp_vals), norm_var(spr_vals)])
        R_score = max(0, min(1, R_score))

        C_score = np.mean(comp_vals)
        B_score = np.mean(spr_vals)
        X = R_score + C_score + B_score

        row = {
            "bias": b,
            "mean_cycles": round(np.mean([r["cycles"] for r in subset]), 1),
            "mean_cyc_per_1k": round(np.mean(cyc_vals), 3),
            "std_cyc_per_1k": round(np.std(cyc_vals), 3),
            "mean_opp_rate": round(np.mean(opp_vals), 2),
            "mean_spr": round(np.mean(spr_vals), 4),
            "mean_compress": round(C_score, 4),
            "miss_strong_share": round(np.mean([r["miss_strong_share"] for r in subset]), 3),
            "miss_energy_share": round(np.mean([r["miss_energy_share"] for r in subset]), 3),
            "seeds_with_cycles": sum(1 for r in subset if r["cycles"] > 0),
            "min_links_worst": min(r["min_links"] for r in subset),
            "R_reproducibility": round(R_score, 4),
            "C_compressibility": round(C_score, 4),
            "B_boundaryness": round(B_score, 4),
            "X_explainability": round(X, 4),
        }
        agg.append(row)

    with open("sweep_aggregate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=agg[0].keys())
        w.writeheader(); w.writerows(agg)

    # Print table
    print(f"\n{'='*70}")
    print(f"  AGGREGATE RESULTS")
    print(f"{'='*70}")
    print(f"\n  {'bias':>5} {'cyc':>6} {'cyc/1k':>7} {'opp':>6} {'spr':>6} "
          f"{'R':>6} {'C':>6} {'B':>6} {'X':>6} {'seeds_cyc':>10} {'minL':>5}")
    for a in agg:
        print(f"  {a['bias']:>5.1f} {a['mean_cycles']:>6.1f} {a['mean_cyc_per_1k']:>7.3f} "
              f"{a['mean_opp_rate']:>6.1f} {a['mean_spr']:>6.4f} "
              f"{a['R_reproducibility']:>6.3f} {a['C_compressibility']:>6.3f} "
              f"{a['B_boundaryness']:>6.4f} {a['X_explainability']:>6.3f} "
              f"{a['seeds_with_cycles']:>10} {a['min_links_worst']:>5}")

    # Best by X, best by cycles
    best_X = max(agg, key=lambda a: a["X_explainability"])
    best_cyc = max(agg, key=lambda a: a["mean_cycles"])

    # ============================================================
    # PLOT
    # ============================================================
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle("ESDE Genesis v1.0 — Bias Sweep + Explainability X",
                 fontsize=14, fontweight="bold", y=0.99)

    bs = [a["bias"] for a in agg]

    ax = axes[0][0]
    ax.plot(bs, [a["mean_cycles"] for a in agg], "o-", color="#2ecc71", ms=8, linewidth=2)
    ax.fill_between(bs,
        [a["mean_cycles"]-a["std_cyc_per_1k"]*2.3 for a in agg],
        [a["mean_cycles"]+a["std_cyc_per_1k"]*2.3 for a in agg],
        alpha=0.15, color="#2ecc71")
    ax.set_title("Mean Cycles vs Bias"); ax.set_xlabel("bias"); ax.grid(True, alpha=0.2)

    ax = axes[0][1]
    ax.plot(bs, [a["X_explainability"] for a in agg], "s-", color="#e67e22", ms=8, linewidth=2)
    ax.set_title("Explainability X vs Bias"); ax.set_xlabel("bias"); ax.grid(True, alpha=0.2)

    ax = axes[0][2]
    ax.plot(bs, [a["R_reproducibility"] for a in agg], "o-", label="R (reprod)", ms=5)
    ax.plot(bs, [a["C_compressibility"] for a in agg], "s-", label="C (compress)", ms=5)
    ax.plot(bs, [a["B_boundaryness"] for a in agg], "^-", label="B (boundary)", ms=5)
    ax.set_title("X Components"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    ax = axes[1][0]
    ax.plot(bs, [a["miss_strong_share"] for a in agg], "o-", label="strong", color="#e74c3c")
    ax.plot(bs, [a["miss_energy_share"] for a in agg], "s-", label="energy", color="#3498db")
    ax.set_title("Near-Miss Shares vs Bias"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    ax = axes[1][1]
    ax.bar(bs, [a["seeds_with_cycles"] for a in agg], width=0.15, color="#2ecc71", alpha=0.7)
    ax.set_title("Seeds with Cycles"); ax.set_xlabel("bias"); ax.set_ylim(0, 11)
    ax.grid(True, axis="y", alpha=0.2)

    ax = axes[1][2]; ax.axis("off")
    txt = [
        f"Best X: bias={best_X['bias']} (X={best_X['X_explainability']:.3f})",
        f"Best cycles: bias={best_cyc['bias']} (mean={best_cyc['mean_cycles']:.1f})",
        "", "Aggregate:",
    ]
    for a in agg:
        txt.append(f"  b={a['bias']:.1f}: cyc={a['mean_cycles']:>5.1f} X={a['X_explainability']:.3f}")
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=11,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("sweep_curves.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: sweep_curves.png")

    # Summary
    summary = f"""ESDE Genesis v1.0 — Bias Sweep Summary
========================================
Controller: FROZEN (best v0.9 params)
Seeds: {len(seeds)} | Quiet: {QUIET} steps | Biases: {biases}

Best by Explainability X:
  bias = {best_X['bias']}  X = {best_X['X_explainability']:.3f}
  (R={best_X['R_reproducibility']:.3f} C={best_X['C_compressibility']:.3f} B={best_X['B_boundaryness']:.4f})
  cycles = {best_X['mean_cycles']:.1f}  seeds_with_cycles = {best_X['seeds_with_cycles']}/10

Best by cycles:
  bias = {best_cyc['bias']}  mean_cycles = {best_cyc['mean_cycles']:.1f}
  X = {best_cyc['X_explainability']:.3f}

Near-miss shift (b=0.0 → b=0.8):
  missing_strong: {agg[0]['miss_strong_share']:.3f} → {agg[-1]['miss_strong_share']:.3f}
  missing_energy: {agg[0]['miss_energy_share']:.3f} → {agg[-1]['miss_energy_share']:.3f}

Durability:
  Worst min_links across all runs: {min(r['min_links'] for r in all_results)}
  {'✓ No inert collapse' if min(r['min_links'] for r in all_results) > 0 else '✗ Some runs collapsed'}

Recommendation: bias ∈ [{best_X['bias']:.1f}, {best_cyc['bias']:.1f}]
"""
    with open("sweep_summary_note.txt", "w") as f:
        f.write(summary)
    print(summary)


if __name__ == "__main__":
    main()
