"""
ESDE Genesis v1.0 — Latent-Coupled Seeding (Growth-Zone Bias)
===============================================================
Single change: Quiet-phase A/B seeding biased toward nodes where
auto-growth is actively strengthening links.

Targets: missing_strong_link bottleneck (79% of near-misses in v0.9).

Comparison: v0.9 baseline (bias=0) vs v1.0 (bias=0.4) + multi-seed.

Designed: Gemini | Audited: GPT | Built: Claude
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
from controller import AdaptiveController

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; INJECT_INTERVAL = 3
BETA = 1.0; NODE_DECAY = 0.005
STATE_NAMES = {0: "Dust", 1: "A", 2: "B", 3: "C"}

BEST_PARAMS = {
    "reaction_energy_threshold": 0.26, "link_death_threshold": 0.007,
    "background_injection_prob": 0.003, "exothermic_release_amount": 0.17,
    "p_link_birth": 0.007, "latent_to_active_threshold": 0.07,
    "latent_refresh_rate": 0.003, "auto_growth_rate": 0.03,
    "growth_seeding_bias": 0.4,
}


class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list); self.completed = []
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i])
            h = self.history[i]
            if not h or h[-1][1] != z: h.append((step, z))
    def detect_cycles(self):
        self.completed = []
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0 and states[i+2] in (1, 2):
                    for j in range(i+3, len(states)):
                        if states[j] == 3:
                            self.completed.append({
                                "node": nid, "start": h[i][0], "end": h[j][0],
                                "cycle": [STATE_NAMES[s] for s in states[i:j+1]],
                            })
                            break
        return self.completed


def measure_opportunities(state, chem_params):
    E_thr = chem_params.E_thr; S_thr = 0.3; P_thr = 0.7
    opportunities = 0; near_misses = 0; miss_reasons = Counter()
    strong_ab = 0; strong_nodes = set()

    for k in state.alive_l:
        i, j = k; s = state.S[k]
        has_strong = s >= S_thr
        has_energy = state.E[i] >= E_thr and state.E[j] >= E_thr
        zi, zj = int(state.Z[i]), int(state.Z[j])
        has_state = (zi in (1,2) or zj in (1,2))
        has_sync = np.cos(state.theta[j] - state.theta[i]) >= P_thr
        conds = [has_strong, has_energy, has_state, has_sync]
        n_met = sum(conds)
        if has_strong:
            strong_nodes.add(i); strong_nodes.add(j)
            if zi in (1,2): strong_ab += 1
            if zj in (1,2): strong_ab += 1
        if n_met == 4: opportunities += 1
        elif n_met == 3:
            near_misses += 1
            if not has_strong: miss_reasons["missing_strong_link"] += 1
            if not has_energy: miss_reasons["missing_energy"] += 1
            if not has_state: miss_reasons["missing_state"] += 1
            if not has_sync: miss_reasons["missing_sync"] += 1

    coverage = strong_ab / max(len(strong_nodes) * 2, 1) if strong_nodes else 0
    return {"opp": opportunities, "nm": near_misses, "miss": dict(miss_reasons),
            "strong_ab": strong_ab, "strong_nodes": len(strong_nodes),
            "coverage": round(coverage, 4)}


def run_sim(seed, quiet_steps, bias_override=None, verbose=False):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True, phase_enabled=True,
        beta=BETA, decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem_params = ChemistryParams(enabled=True)
    chem = ChemistryEngine(chem_params)
    real_params = RealizationParams(enabled=True)
    realizer = RealizationOperator(real_params)
    grow_params = AutoGrowthParams(enabled=True)
    grower = AutoGrowthEngine(grow_params)
    controller = AdaptiveController(window_size=200)
    logger = GenesisLogger(); tracker = CycleTracker()

    for p in controller.params:
        if p.name in BEST_PARAMS: p.value = BEST_PARAMS[p.name]
    if bias_override is not None:
        for p in controller.params:
            if p.name == "growth_seeding_bias": p.value = bias_override

    # Growth-zone scores per node
    growth_scores = np.zeros(N_NODES)

    wlog = []; t0 = time.time()
    w_opp = 0; w_nm = 0; w_miss = Counter(); w_real = 0; w_grow = 0; w_rxn = 0
    w_seed_g_targets = []; w_growth_mass = 0; prev_cyc = 0

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
        logger.observe(state); tracker.record(state, state.step - 1)

    # Quiet
    for step in range(quiet_steps):
        # Sync controller params
        rp = realizer.params
        rp.p_link_birth = controller.get_param("p_link_birth")
        rp.latent_to_active_threshold = controller.get_param("latent_to_active_threshold")
        rp.latent_refresh_rate = controller.get_param("latent_refresh_rate")
        chem.params.E_thr = controller.get_param("reaction_energy_threshold")
        chem.params.exothermic_release = controller.get_param("exothermic_release_amount")
        state.EXTINCTION = controller.get_param("link_death_threshold")
        grower.params.auto_growth_rate = controller.get_param("auto_growth_rate")
        bias = controller.get_param("growth_seeding_bias")

        # v1.0: Growth-zone biased seeding
        bg_prob = controller.get_param("background_injection_prob")
        n_bg = int(np.sum(state.rng.random(N_NODES) < bg_prob))
        if n_bg > 0:
            # Build sampling distribution
            g_sum = growth_scores.sum()
            if g_sum > 0 and bias > 0:
                uniform = np.ones(N_NODES) / N_NODES
                growth_dist = growth_scores / g_sum
                p_dist = (1 - bias) * uniform + bias * growth_dist
                p_dist = p_dist / p_dist.sum()  # renormalize
            else:
                p_dist = np.ones(N_NODES) / N_NODES

            targets = state.rng.choice(N_NODES, size=n_bg, replace=False, p=p_dist)
            for i in targets:
                if i in state.alive_n:
                    state.E[i] = min(1.0, state.E[i] + 0.3)
                    if state.Z[i] == 0 and state.rng.random() < 0.5:
                        state.Z[i] = 1 if state.rng.random() < 0.5 else 2
                    w_seed_g_targets.append(growth_scores[i])

        # Realization
        w_real += realizer.step(state)

        # Physics + Chemistry
        physics.step_pre_chemistry(state)
        rxns = chem.step(state); w_rxn += len(rxns)

        # Resonance
        cd = physics.step_resonance(state)
        if cd: logger.observe_loops(cd)

        # Auto-Growth + update growth scores
        growth_scores[:] = 0.0
        grower.step(state)
        w_grow += grower.growth_events
        # Record per-node growth (from autogrowth's last step)
        for k in state.alive_l:
            r_ij = state.R.get(k, 0.0)
            if r_ij > 0:
                i, j = k
                l_ij = state.get_latent(i, j)
                actual = min(grower.params.auto_growth_rate * r_ij, l_ij, 1.0 - state.S[k])
                if actual > 0:
                    growth_scores[i] += actual
                    growth_scores[j] += actual
        w_growth_mass += growth_scores.sum()

        # Decay + Exclusion
        physics.step_decay_exclusion(state)
        logger.observe(state, event="quiet", reactions=rxns)
        tracker.record(state, state.step - 1)

        # Opportunities
        opp = measure_opportunities(state, chem.params)
        w_opp += opp["opp"]; w_nm += opp["nm"]
        for k, v in opp.get("miss", {}).items(): w_miss[k] += v

        # Window boundary
        if (step + 1) % controller.window_size == 0:
            strengths = [state.S[k] for k in state.alive_l]
            med_s = float(np.median(strengths)) if strengths else 0.0
            max_s = max(strengths) if strengths else 0.0
            s03 = sum(1 for s in strengths if s >= 0.3)
            loop_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr = loop_links / max(len(state.alive_l), 1)
            sc = Counter(int(state.Z[i]) for i in state.alive_n)
            all_cyc = tracker.detect_cycles()
            new_cyc = len(all_cyc) - prev_cyc; prev_cyc = len(all_cyc)

            # Seeding alignment
            mean_g_target = np.mean(w_seed_g_targets) if w_seed_g_targets else 0
            mean_g_all = np.mean(growth_scores) if growth_scores.sum() > 0 else 0

            entry = controller.evaluate_and_adapt({
                "median_strength": med_s, "spr": spr, "cycles_window": new_cyc})

            wlog.append({
                "w": entry["window"], "V": entry["V"],
                "links": len(state.alive_l), "med_s": round(med_s, 5),
                "max_s": round(max_s, 5), "s03": s03, "spr": round(spr, 4),
                "opp": w_opp, "nm": w_nm, "miss": dict(w_miss),
                "cycles_new": new_cyc, "cycles_total": len(all_cyc),
                "strong_ab": opp["strong_ab"], "coverage": opp["coverage"],
                "growth_mass": round(w_growth_mass, 3),
                "seed_align": round(mean_g_target, 6),
                "real": w_real, "grow": w_grow, "rxn": w_rxn, "n_C": sc.get(3, 0),
            })

            if verbose and len(wlog) % 5 == 0:
                w = wlog[-1]
                print(f"    W{w['w']:>3}: L={w['links']:>4} S>0.3={w['s03']:>3} "
                      f"opp={w['opp']:>3} nm={w['nm']:>4} cyc={w['cycles_total']} "
                      f"cov={w['coverage']:.3f} ({time.time()-t0:.0f}s)")

            w_opp=0; w_nm=0; w_miss=Counter(); w_real=0; w_grow=0; w_rxn=0
            w_seed_g_targets=[]; w_growth_mass=0

    all_cycles = tracker.detect_cycles()
    elapsed = time.time() - t0
    total_miss = Counter()
    for row in wlog:
        for k, v in row.get("miss", {}).items(): total_miss[k] += v

    summary = {
        "seed": seed, "bias": bias_override if bias_override is not None else BEST_PARAMS["growth_seeding_bias"],
        "steps": INJECTION_STEPS + quiet_steps,
        "cycles": len(all_cycles),
        "min_links": min(w["links"] for w in wlog) if wlog else 0,
        "max_s03": max(w["s03"] for w in wlog) if wlog else 0,
        "max_s": max(w["max_s"] for w in wlog) if wlog else 0,
        "total_opp": sum(w["opp"] for w in wlog),
        "total_nm": sum(w["nm"] for w in wlog),
        "miss_strong": total_miss.get("missing_strong_link", 0),
        "miss_energy": total_miss.get("missing_energy", 0),
        "miss_state": total_miss.get("missing_state", 0),
        "miss_sync": total_miss.get("missing_sync", 0),
        "mean_coverage": round(np.mean([w["coverage"] for w in wlog]), 4) if wlog else 0,
        "elapsed": round(elapsed, 1),
    }
    return wlog, all_cycles, summary


def main():
    print("=" * 70)
    print("  ESDE Genesis v1.0 — Latent-Coupled Seeding")
    print("  Growth-Zone Bias targets missing_strong_link bottleneck")
    print("=" * 70)

    # ============================================================
    # A) Long run: v0.9 baseline vs v1.0 (seed=42, 5000 quiet)
    # ============================================================
    print(f"\n  Long Run Comparison (seed=42, 3000 quiet steps)")
    print(f"  {'='*50}")

    print(f"\n  v0.9 baseline (bias=0.0)...")
    wlog_09, cyc_09, sum_09 = run_sim(42, 3000, bias_override=0.0, verbose=True)

    print(f"\n  v1.0 (bias=0.4)...")
    wlog_10, cyc_10, sum_10 = run_sim(42, 3000, bias_override=0.4, verbose=True)

    print(f"\n  {'Metric':<30} {'v0.9':>12} {'v1.0':>12} {'Delta':>10}")
    print(f"  {'-'*64}")
    for k, label in [("cycles", "Cycles"), ("total_opp", "Opportunities"),
                      ("total_nm", "Near-Misses"), ("miss_strong", "Miss: Strong Link"),
                      ("miss_energy", "Miss: Energy"), ("miss_state", "Miss: State"),
                      ("miss_sync", "Miss: Sync"), ("max_s03", "Max S>0.3"),
                      ("mean_coverage", "Mean Coverage"), ("min_links", "Min Links")]:
        v09 = sum_09[k]; v10 = sum_10[k]
        d = v10 - v09 if isinstance(v09, (int, float)) else "—"
        print(f"  {label:<30} {str(v09):>12} {str(v10):>12} {str(d):>10}")

    # ============================================================
    # B) Multi-seed: 10 seeds × 3000 quiet
    # ============================================================
    print(f"\n  {'='*70}")
    print(f"  Multi-Seed Comparison (5 seeds × 2000 quiet)")
    print(f"  {'='*70}")

    seeds = [42, 123, 789, 2024, 1337]
    multi_09 = []; multi_10 = []

    for seed in seeds:
        _, _, s09 = run_sim(seed, 2000, bias_override=0.0)
        _, _, s10 = run_sim(seed, 2000, bias_override=0.4)
        multi_09.append(s09); multi_10.append(s10)
        print(f"    seed={seed:>5}: v0.9 cyc={s09['cycles']:>2} opp={s09['total_opp']:>4} | "
              f"v1.0 cyc={s10['cycles']:>2} opp={s10['total_opp']:>4}")

    print(f"\n  {'Metric':<25} {'v0.9 (sum)':>12} {'v1.0 (sum)':>12}")
    print(f"  {'-'*50}")
    for k, label in [("cycles", "Total Cycles"), ("total_opp", "Total Opportunities"),
                      ("miss_strong", "Miss: Strong"), ("mean_coverage", "Mean Coverage (avg)")]:
        if k == "mean_coverage":
            v09 = round(np.mean([r[k] for r in multi_09]), 4)
            v10 = round(np.mean([r[k] for r in multi_10]), 4)
        else:
            v09 = sum(r[k] for r in multi_09); v10 = sum(r[k] for r in multi_10)
        print(f"  {label:<25} {str(v09):>12} {str(v10):>12}")

    # ============================================================
    # PLOT
    # ============================================================
    fig, axes = plt.subplots(4, 2, figsize=(20, 22))
    fig.suptitle("ESDE Genesis v1.0 — Growth-Zone Bias\nv0.9 (blue) vs v1.0 (green)",
                 fontsize=14, fontweight="bold", y=0.99)

    def plot_compare(ax, key, title, ylabel=None):
        ax.plot([w["w"] for w in wlog_09], [w[key] for w in wlog_09],
                ".-", color="#3498db", ms=3, linewidth=1, label="v0.9", alpha=0.8)
        ax.plot([w["w"] for w in wlog_10], [w[key] for w in wlog_10],
                ".-", color="#2ecc71", ms=3, linewidth=1, label="v1.0", alpha=0.8)
        ax.set_title(title, fontsize=10); ax.legend(fontsize=7); ax.grid(True, alpha=0.2)
        if ylabel: ax.set_ylabel(ylabel)

    plot_compare(axes[0][0], "links", "Active Links")
    plot_compare(axes[0][1], "s03", "Links with S > 0.3")
    plot_compare(axes[1][0], "opp", "Opportunities per Window")
    plot_compare(axes[1][1], "nm", "Near-Misses per Window")
    plot_compare(axes[2][0], "coverage", "Strong-Endpoint Coverage (A/B)")
    plot_compare(axes[2][1], "cycles_total", "Cumulative Cycles")

    # Near-miss breakdown comparison
    ax = axes[3][0]
    reasons = ["missing_strong_link", "missing_energy", "missing_state", "missing_sync"]
    short = ["strong_link", "energy", "state", "sync"]
    x = np.arange(len(reasons)); w_bar = 0.35
    v09_counts = [sum_09.get(f"miss_{r.split('_',1)[1]}", 0) for r in reasons]
    v10_counts = [sum_10.get(f"miss_{r.split('_',1)[1]}", 0) for r in reasons]
    # Fix key mapping
    v09_counts = [sum_09["miss_strong"], sum_09["miss_energy"], sum_09["miss_state"], sum_09["miss_sync"]]
    v10_counts = [sum_10["miss_strong"], sum_10["miss_energy"], sum_10["miss_state"], sum_10["miss_sync"]]
    ax.barh(x - w_bar/2, v09_counts, w_bar, label="v0.9", color="#3498db", alpha=0.7)
    ax.barh(x + w_bar/2, v10_counts, w_bar, label="v1.0", color="#2ecc71", alpha=0.7)
    ax.set_yticks(x); ax.set_yticklabels(short)
    ax.set_title("Near-Miss Breakdown (Long Run)"); ax.legend(fontsize=8)
    ax.grid(True, axis="x", alpha=0.2)

    # Summary text
    ax = axes[3][1]; ax.axis("off")
    txt = [
        "LONG RUN COMPARISON (seed=42, 5300 steps)",
        f"  v0.9: {sum_09['cycles']} cycles, {sum_09['total_opp']} opp",
        f"  v1.0: {sum_10['cycles']} cycles, {sum_10['total_opp']} opp",
        "",
        f"MULTI-SEED ({len(seeds)} seeds × 3300 steps)",
        f"  v0.9: {sum(r['cycles'] for r in multi_09)} total cycles",
        f"  v1.0: {sum(r['cycles'] for r in multi_10)} total cycles",
        f"  v0.9 mean coverage: {np.mean([r['mean_coverage'] for r in multi_09]):.4f}",
        f"  v1.0 mean coverage: {np.mean([r['mean_coverage'] for r in multi_10]):.4f}",
    ]
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=11,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("genesis_v10_growth_bias.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: genesis_v10_growth_bias.png")

    # CSV exports
    with open("v10_longrun_metrics.csv", "w", newline="") as f:
        keys = [k for k in wlog_10[0].keys() if k != "miss"]
        w = csv.DictWriter(f, fieldnames=keys + ["miss_str"])
        w.writeheader()
        for row in wlog_10:
            r = {k: row[k] for k in keys}; r["miss_str"] = str(row.get("miss",{}))
            w.writerow(r)

    with open("v10_multiseed_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=multi_10[0].keys())
        w.writeheader(); w.writerows(multi_10)

    # Summary note
    summary_txt = f"""ESDE Genesis v1.0 — Summary
===========================
Change: Growth-zone biased seeding (bias=0.4)

LONG RUN (seed=42, 5300 steps):
  v0.9: {sum_09['cycles']} cycles, {sum_09['total_opp']} opp, miss_strong={sum_09['miss_strong']}
  v1.0: {sum_10['cycles']} cycles, {sum_10['total_opp']} opp, miss_strong={sum_10['miss_strong']}

MULTI-SEED ({len(seeds)} seeds):
  v0.9: {sum(r['cycles'] for r in multi_09)} total cycles, mean_cov={np.mean([r['mean_coverage'] for r in multi_09]):.4f}
  v1.0: {sum(r['cycles'] for r in multi_10)} total cycles, mean_cov={np.mean([r['mean_coverage'] for r in multi_10]):.4f}
"""
    with open("v10_summary.txt", "w") as f: f.write(summary_txt)
    print(summary_txt)


if __name__ == "__main__":
    main()
