"""
ESDE Genesis v1.1 — Noise Tolerance (η) Sweep
================================================
How much noise can the system tolerate before explainability collapses?

Knobs (sweep independently):
  A) background_injection_prob
  B) latent_refresh_rate
  C) p_link_birth

Controller FROZEN. bias=0.7 fixed. 5 seeds per setting.
η = X(setting) / X(baseline)
"""

import numpy as np
import matplotlib.pyplot as plt
import csv, time
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
BIAS = 0.7
STRENGTH_BINS = [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 1.01)]

BASE = {
    "reaction_energy_threshold": 0.26, "link_death_threshold": 0.007,
    "background_injection_prob": 0.003, "exothermic_release_amount": 0.17,
    "p_link_birth": 0.007, "latent_to_active_threshold": 0.07,
    "latent_refresh_rate": 0.003, "auto_growth_rate": 0.03,
}

SEEDS = [42, 789, 2024]
QUIET = 500

KNOBS = {
    "background_injection_prob": [0.001, 0.003, 0.015, 0.03],
    "latent_refresh_rate": [0.0003, 0.001, 0.003, 0.01],
    "p_link_birth": [0.001, 0.004, 0.01, 0.03],
}


class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list)
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i]); h = self.history[i]
            if not h or h[-1][1] != z: h.append((step, z))
    def count_cycles(self):
        n = 0
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0 and states[i+2] in (1, 2):
                    for j in range(i+3, len(states)):
                        if states[j] == 3: n += 1; break
        return n


def run_one(seed, params_override=None):
    p = dict(BASE)
    if params_override:
        p.update(params_override)

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True, phase_enabled=True,
        beta=BETA, decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem_params = ChemistryParams(enabled=True, E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"])
    chem = ChemistryEngine(chem_params)
    rp = RealizationParams(enabled=True, p_link_birth=p["p_link_birth"],
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer = RealizationOperator(rp)
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True, auto_growth_rate=p["auto_growth_rate"]))
    state.EXTINCTION = p["link_death_threshold"]
    logger = GenesisLogger()
    tracker = CycleTracker()
    g_scores = np.zeros(N_NODES)

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

    total_opp = 0; total_nm = 0; total_miss = Counter()
    spr_vals = []; strength_hists = []; min_links = 9999

    for step in range(QUIET):
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
                if actual > 0: g_scores[k[0]] += actual; g_scores[k[1]] += actual
        gz_mass = float(g_scores.sum())
        physics.step_decay_exclusion(state)
        logger.observe(state, reactions=rxns)
        tracker.record(state, state.step - 1)

        # Biased seeding
        alive_list = list(state.alive_n)
        n_alive = len(alive_list)
        if n_alive > 0:
            alive_arr = np.array(alive_list)
            if BIAS > 0 and gz_mass > 0:
                g_alive = g_scores[alive_arr]; g_sum = g_alive.sum()
                if g_sum > 0:
                    pg = g_alive / g_sum
                    p_dist = (1-BIAS)*(np.ones(n_alive)/n_alive) + BIAS*pg
                    p_dist /= p_dist.sum()
                else: p_dist = np.ones(n_alive)/n_alive
            else: p_dist = np.ones(n_alive)/n_alive
            mask = state.rng.random(n_alive) < p["background_injection_prob"]
            for idx in range(n_alive):
                if mask[idx]:
                    target = int(state.rng.choice(alive_arr, p=p_dist))
                    state.E[target] = min(1.0, state.E[target] + 0.3)
                    if state.Z[target] == 0 and state.rng.random() < 0.5:
                        state.Z[target] = 1 if state.rng.random() < 0.5 else 2

        if step % 50 == 49:
            n_links = len(state.alive_l); min_links = min(min_links, n_links)
            strengths = [state.S[k] for k in state.alive_l]
            loop_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr_vals.append(loop_links / max(n_links, 1))
            hist = [0]*len(STRENGTH_BINS)
            for s in strengths:
                for bi, (lo, hi) in enumerate(STRENGTH_BINS):
                    if lo <= s < hi: hist[bi] += 1; break
            strength_hists.append(hist)
            for k in state.alive_l:
                i, j = k; s = state.S[k]
                c_s = s >= 0.3; c_e = state.E[i]>=chem_params.E_thr and state.E[j]>=chem_params.E_thr
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

    cycles = tracker.count_cycles()
    total_steps = INJECTION_STEPS + QUIET
    s03 = sum(1 for k in state.alive_l if state.S[k] >= 0.3)

    if strength_hists:
        mh = np.mean(strength_hists, axis=0); t = mh.sum()
        if t > 0:
            pp = mh/t; pp = pp[pp>0]; H = -np.sum(pp*np.log2(pp))
            C_score = 1.0 - H/np.log2(len(STRENGTH_BINS))
        else: C_score = 0.0; H = 0.0
    else: C_score = 0.0; H = 0.0

    spr_mean = np.mean(spr_vals) if spr_vals else 0
    cyc_rate = cycles / (total_steps / 1000)
    opp_rate = total_opp / max(QUIET/50, 1)

    return {
        "cycles": cycles, "cycles_rate": round(cyc_rate, 3),
        "opp_rate": round(opp_rate, 3),
        "min_links": min_links if min_links < 9999 else 0,
        "s03": s03, "spr_mean": round(spr_mean, 4),
        "compressibility": round(C_score, 4),
        "strength_entropy": round(H, 4),
        "miss_strong": round(total_miss.get("strong",0)/max(total_nm,1), 3),
        "miss_energy": round(total_miss.get("energy",0)/max(total_nm,1), 3),
    }


def compute_X(r):
    # Simple X: compressibility + spr + small cycle bonus
    return round(r["compressibility"] + r["spr_mean"] + 0.01 * r["cycles_rate"], 4)


def main():
    print("=" * 70)
    print("  ESDE Genesis v1.1 — Noise Tolerance (η) Sweep")
    print(f"  bias={BIAS} frozen, {len(SEEDS)} seeds × {QUIET} quiet steps")
    print("=" * 70)

    # Baseline
    print("\n  Computing baselines...")
    baselines = {}
    for seed in SEEDS:
        r = run_one(seed)
        r["X"] = compute_X(r)
        baselines[seed] = r
        print(f"    seed={seed}: X={r['X']:.4f} cyc={r['cycles']} spr={r['spr_mean']:.3f}")

    all_rows = []
    agg_rows = []

    for knob_name, grid in KNOBS.items():
        print(f"\n  Knob: {knob_name}")
        for val in grid:
            is_base = abs(val - BASE[knob_name]) < 1e-9
            seed_results = []
            for seed in SEEDS:
                t0 = time.time()
                r = run_one(seed, {knob_name: val})
                r["X"] = compute_X(r)
                X_base = baselines[seed]["X"]
                eta = r["X"] / X_base if X_base > 0.01 else 0
                collapse = r["min_links"] == 0 or r["strength_entropy"] < 0.2

                row = {"knob": knob_name, "value": val, "seed": seed,
                       "X": r["X"], "X_baseline": X_base,
                       "eta": round(eta, 4),
                       "cycles_rate": r["cycles_rate"], "opp_rate": r["opp_rate"],
                       "min_links": r["min_links"], "s03": r["s03"],
                       "spr_mean": r["spr_mean"],
                       "miss_strong": r["miss_strong"], "miss_energy": r["miss_energy"],
                       "entropy": r["strength_entropy"],
                       "collapse": collapse}
                all_rows.append(row)
                seed_results.append(row)

            etas = [r["eta"] for r in seed_results]
            med_eta = round(np.median(etas), 3)
            collapses = sum(1 for r in seed_results if r["collapse"])
            status = "collapse" if med_eta < 0.6 or collapses >= 3 else \
                     "degraded" if med_eta < 0.8 else "stable"

            agg_rows.append({
                "knob": knob_name, "value": val,
                "median_eta": med_eta,
                "mean_eta": round(np.mean(etas), 3),
                "median_cyc_rate": round(np.median([r["cycles_rate"] for r in seed_results]), 3),
                "median_X": round(np.median([r["X"] for r in seed_results]), 4),
                "pct_collapse": round(collapses/len(seed_results)*100, 0),
                "status": status,
            })

            marker = "●" if is_base else " "
            print(f"  {marker} {val:>8.4f}: η={med_eta:.3f} [{status:>8}] "
                  f"cyc={np.median([r['cycles_rate'] for r in seed_results]):.1f} "
                  f"col={collapses}/{len(seed_results)}")

    # Save
    with open("noise_sweep_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_rows[0].keys()); w.writeheader(); w.writerows(all_rows)
    with open("noise_sweep_aggregate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=agg_rows[0].keys()); w.writeheader(); w.writerows(agg_rows)

    # ============================================================
    # PLOT
    # ============================================================
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle("ESDE Genesis v1.1 — Noise Tolerance (η) Sweep",
                 fontsize=14, fontweight="bold", y=0.99)

    colors = {"background_injection_prob": "#e74c3c",
              "latent_refresh_rate": "#3498db",
              "p_link_birth": "#2ecc71"}

    for ki, (knob, grid) in enumerate(KNOBS.items()):
        subset = [a for a in agg_rows if a["knob"] == knob]
        vs = [a["value"] for a in subset]
        etas = [a["median_eta"] for a in subset]
        cycs = [a["median_cyc_rate"] for a in subset]
        xs = [a["median_X"] for a in subset]
        c = colors[knob]

        ax = axes[0][ki]
        ax.plot(vs, etas, "o-", color=c, ms=8, linewidth=2)
        ax.axhline(y=0.8, color="orange", linestyle="--", alpha=0.5, label="stable threshold")
        ax.axhline(y=0.6, color="red", linestyle="--", alpha=0.5, label="collapse threshold")
        ax.axvline(x=BASE[knob], color="gray", linestyle=":", alpha=0.5)
        ax.set_title(f"η: {knob[:20]}", fontsize=9)
        ax.set_xlabel("value"); ax.set_ylabel("η")
        ax.legend(fontsize=7); ax.grid(True, alpha=0.2)
        ax.set_xscale("log")

        ax = axes[1][ki]
        ax.plot(vs, cycs, "s-", color=c, ms=6, linewidth=1.5, label="cycles/1k")
        ax2 = ax.twinx()
        ax2.plot(vs, xs, "^--", color="gray", ms=5, alpha=0.7, label="X")
        ax.set_title(f"Cycles & X: {knob[:20]}", fontsize=9)
        ax.set_xlabel("value"); ax.set_ylabel("cycles/1k", color=c)
        ax2.set_ylabel("X", color="gray")
        ax.set_xscale("log"); ax.grid(True, alpha=0.2)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("eta_vs_knob.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: eta_vs_knob.png")

    # Conclusion
    conclusion = ["ESDE Genesis v1.1 — Noise Tolerance Summary", "=" * 50, ""]
    for knob in KNOBS:
        subset = [a for a in agg_rows if a["knob"] == knob]
        stable = [a for a in subset if a["status"] == "stable"]
        safe_range = [a["value"] for a in stable]
        conclusion.append(f"{knob}:")
        conclusion.append(f"  Safe band (η≥0.8): {safe_range if safe_range else 'NONE'}")
        collapse_pts = [a for a in subset if a["status"] == "collapse"]
        if collapse_pts:
            conclusion.append(f"  Collapse at: {[a['value'] for a in collapse_pts]}")
        conclusion.append("")

    txt = "\n".join(conclusion)
    with open("v11_noise_sweep_conclusion.txt", "w") as f: f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
