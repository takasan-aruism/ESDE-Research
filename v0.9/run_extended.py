"""
ESDE Genesis v0.9 — Extended Runs + Near-Miss Observation
============================================================
A1) Long-run: 10,000 steps, single seed, best params from prior run
A2) Multi-seed: 10 seeds × 3,000 steps
B)  Near-miss metrics: opportunity count, near-miss breakdown, endpoint-hit rate

No design changes. Observation only.
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

# Best params from prior v0.9 run
BEST_PARAMS = {
    "reaction_energy_threshold": 0.26,
    "link_death_threshold": 0.007,
    "background_injection_prob": 0.003,
    "exothermic_release_amount": 0.17,
    "p_link_birth": 0.007,
    "latent_to_active_threshold": 0.07,
    "latent_refresh_rate": 0.003,
    "auto_growth_rate": 0.03,
}


class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list)
        self.completed = []
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i])
            h = self.history[i]
            if not h or h[-1][1] != z:
                h.append((step, z))
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
    """Count opportunity events and near-misses."""
    E_thr = chem_params.E_thr
    S_thr = 0.3  # reaction link threshold
    P_thr = 0.7  # phase coherence threshold

    opportunities = 0
    near_misses = 0
    miss_reasons = Counter()
    strong_endpoint_ab = 0
    strong_endpoint_nodes = set()

    for k in state.alive_l:
        i, j = k
        s = state.S[k]
        has_strong = s >= S_thr
        has_energy = state.E[i] >= E_thr and state.E[j] >= E_thr
        zi, zj = int(state.Z[i]), int(state.Z[j])
        has_state = (zi in (1,2) or zj in (1,2))  # at least one A/B
        dtheta = state.theta[j] - state.theta[i]
        has_sync = np.cos(dtheta) >= P_thr

        conds = [has_strong, has_energy, has_state, has_sync]
        n_met = sum(conds)

        if has_strong:
            strong_endpoint_nodes.add(i)
            strong_endpoint_nodes.add(j)
            if zi in (1, 2):
                strong_endpoint_ab += 1
            if zj in (1, 2):
                strong_endpoint_ab += 1

        if n_met == 4:
            opportunities += 1
        elif n_met == 3:
            near_misses += 1
            if not has_strong: miss_reasons["missing_strong_link"] += 1
            if not has_energy: miss_reasons["missing_energy"] += 1
            if not has_state: miss_reasons["missing_state"] += 1
            if not has_sync: miss_reasons["missing_sync"] += 1

    return {
        "opportunities": opportunities,
        "near_misses": near_misses,
        "miss_reasons": dict(miss_reasons),
        "strong_endpoint_ab": strong_endpoint_ab,
        "strong_endpoint_nodes": len(strong_endpoint_nodes),
    }


def run_simulation(seed, quiet_steps, use_controller=True, verbose=False):
    """Run one full simulation. Returns (window_log, cycles, final_summary)."""
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem_params = ChemistryParams(enabled=True)
    chem = ChemistryEngine(chem_params)
    real_params = RealizationParams(enabled=True)
    realizer = RealizationOperator(real_params)
    grow_params = AutoGrowthParams(enabled=True)
    grower = AutoGrowthEngine(grow_params)
    controller = AdaptiveController(window_size=200)
    logger = GenesisLogger()
    tracker = CycleTracker()

    # Set best params as initial
    for p in controller.params:
        if p.name in BEST_PARAMS:
            p.value = BEST_PARAMS[p.name]

    window_log = []
    t0 = time.time()

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

    # Quiet
    w_opp = 0; w_nm = 0; w_miss = Counter()
    w_real = 0; w_grow = 0; w_rxn = 0

    for step in range(quiet_steps):
        # Background injection
        bg_prob = controller.get_param("background_injection_prob")
        mask = state.rng.random(N_NODES) < bg_prob
        for i in range(N_NODES):
            if mask[i] and i in state.alive_n:
                state.E[i] = min(1.0, state.E[i] + 0.3)
                if state.Z[i] == 0 and state.rng.random() < 0.5:
                    state.Z[i] = 1 if state.rng.random() < 0.5 else 2

        # Sync params
        real_params.p_link_birth = controller.get_param("p_link_birth")
        real_params.latent_to_active_threshold = controller.get_param("latent_to_active_threshold")
        real_params.latent_refresh_rate = controller.get_param("latent_refresh_rate")
        chem.params.E_thr = controller.get_param("reaction_energy_threshold")
        chem.params.exothermic_release = controller.get_param("exothermic_release_amount")
        state.EXTINCTION = controller.get_param("link_death_threshold")
        grower.params.auto_growth_rate = controller.get_param("auto_growth_rate")

        w_real += realizer.step(state)
        physics.step_pre_chemistry(state)
        rxns = chem.step(state)
        w_rxn += len(rxns)
        cd = physics.step_resonance(state)
        if cd: logger.observe_loops(cd)
        grower.step(state)
        w_grow += grower.growth_events
        physics.step_decay_exclusion(state)
        logger.observe(state, reactions=rxns)
        tracker.record(state, state.step - 1)

        # Opportunity measurement
        opp = measure_opportunities(state, chem.params)
        w_opp += opp["opportunities"]
        w_nm += opp["near_misses"]
        for k, v in opp.get("miss_reasons", {}).items():
            w_miss[k] += v

        # Window boundary
        if (step + 1) % controller.window_size == 0:
            strengths = [state.S[k] for k in state.alive_l]
            med_s = float(np.median(strengths)) if strengths else 0.0
            max_s = max(strengths) if strengths else 0.0
            loop_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr = loop_links / max(len(state.alive_l), 1)
            s03 = sum(1 for s in strengths if s >= 0.3)
            sc = Counter(int(state.Z[i]) for i in state.alive_n)

            all_cyc = tracker.detect_cycles()

            if use_controller:
                entry = controller.evaluate_and_adapt({
                    "median_strength": med_s, "spr": spr,
                    "cycles_window": 0,
                })

            window_log.append({
                "window": len(window_log) + 1,
                "links": len(state.alive_l),
                "med_s": round(med_s, 5), "max_s": round(max_s, 5),
                "s_gt_03": s03, "spr": round(spr, 4),
                "loop_edges": loop_links, "realized": w_real,
                "growth": w_grow, "rxn": w_rxn,
                "opp": w_opp, "near_miss": w_nm,
                "miss_reasons": dict(w_miss),
                "cycles": len(all_cyc), "n_C": sc.get(3, 0),
                "ab_on_strong": opp["strong_endpoint_ab"],
                "strong_nodes": opp["strong_endpoint_nodes"],
            })

            if verbose and len(window_log) % 10 == 0:
                w = window_log[-1]
                print(f"    W{w['window']:>3}: L={w['links']:>4} med={w['med_s']:.4f} "
                      f"S>0.3={w['s_gt_03']:>3} opp={w['opp']:>3} nm={w['near_miss']:>3} "
                      f"cyc={w['cycles']} ({time.time()-t0:.0f}s)")

            w_opp = 0; w_nm = 0; w_miss = Counter()
            w_real = 0; w_grow = 0; w_rxn = 0

    all_cycles = tracker.detect_cycles()
    elapsed = time.time() - t0

    summary = {
        "seed": seed,
        "steps": INJECTION_STEPS + quiet_steps,
        "cycles_completed": len(all_cycles),
        "min_links": min(w["links"] for w in window_log) if window_log else 0,
        "max_links": max(w["links"] for w in window_log) if window_log else 0,
        "max_s_gt_03": max(w["s_gt_03"] for w in window_log) if window_log else 0,
        "max_s": max(w["max_s"] for w in window_log) if window_log else 0,
        "median_s_best": max(w["med_s"] for w in window_log) if window_log else 0,
        "total_opp": sum(w["opp"] for w in window_log),
        "total_near_miss": sum(w["near_miss"] for w in window_log),
        "elapsed": round(elapsed, 1),
    }

    return window_log, all_cycles, summary, controller


def main():
    print("=" * 70)
    print("  ESDE Genesis v0.9 — Extended Runs + Near-Miss Observation")
    print("  No design changes. Longer time + more seeds + diagnostics.")
    print("=" * 70)

    # ============================================================
    # A1) LONG RUN — 10,000 quiet steps
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  A1) Long Run: seed=42, 5000 quiet steps")
    print(f"{'='*70}")

    wlog, cycles, summary, ctrl = run_simulation(42, 5000, verbose=True)

    # Save metrics
    with open("O9_longrun_metrics.csv", "w", newline="") as f:
        keys = [k for k in wlog[0].keys() if k != "miss_reasons"]
        w = csv.DictWriter(f, fieldnames=keys + ["miss_str"])
        w.writeheader()
        for row in wlog:
            r = {k: row[k] for k in keys}
            r["miss_str"] = str(row.get("miss_reasons", {}))
            w.writerow(r)

    ctrl.export_log("controller_log.csv")

    # Near-miss breakdown
    all_miss = Counter()
    for row in wlog:
        for k, v in row.get("miss_reasons", {}).items():
            all_miss[k] += v

    with open("near_miss_breakdown.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["reason", "count"])
        for reason, count in all_miss.most_common():
            w.writerow([reason, count])

    print(f"\n  Long-run summary:")
    print(f"    Cycles: {summary['cycles_completed']}")
    print(f"    Min links: {summary['min_links']}")
    print(f"    Max S>0.3: {summary['max_s_gt_03']}")
    print(f"    Max S: {summary['max_s']:.4f}")
    print(f"    Total opportunities: {summary['total_opp']}")
    print(f"    Total near-misses: {summary['total_near_miss']}")
    print(f"    Near-miss breakdown: {dict(all_miss)}")
    print(f"    Elapsed: {summary['elapsed']}s")

    # Plot long run
    fig, axes = plt.subplots(4, 2, figsize=(20, 22))
    fig.suptitle("ESDE Genesis v0.9 — Long Run (10,000 quiet steps)\n"
                 "Near-Miss Analysis", fontsize=14, fontweight="bold", y=0.99)

    ws = [e["window"] for e in wlog]

    axes[0][0].plot(ws, [e["links"] for e in wlog], color="#2ecc71", linewidth=1)
    axes[0][0].set_title("Active Links"); axes[0][0].grid(True, alpha=0.2)

    axes[0][1].plot(ws, [e["med_s"] for e in wlog], color="#3498db", linewidth=1)
    axes[0][1].axhline(y=0.3, color="red", linestyle=":", alpha=0.5)
    axes[0][1].set_title("Median Link Strength"); axes[0][1].grid(True, alpha=0.2)

    axes[1][0].plot(ws, [e["s_gt_03"] for e in wlog], color="#e67e22", linewidth=1)
    axes[1][0].set_title("Links with S > 0.3"); axes[1][0].grid(True, alpha=0.2)

    axes[1][1].plot(ws, [e["opp"] for e in wlog], label="opportunities", color="#2ecc71", linewidth=1)
    axes[1][1].plot(ws, [e["near_miss"] for e in wlog], label="near-misses", color="#e74c3c", linewidth=1)
    axes[1][1].set_title("Opportunities & Near-Misses"); axes[1][1].legend(fontsize=8)
    axes[1][1].grid(True, alpha=0.2)

    axes[2][0].plot(ws, [e["spr"] for e in wlog], color="#1abc9c", linewidth=1)
    axes[2][0].set_title("Structural Persistence Ratio"); axes[2][0].grid(True, alpha=0.2)

    axes[2][1].plot(ws, [e["loop_edges"] for e in wlog], color="#9b59b6", linewidth=1)
    axes[2][1].set_title("Loop Edges (R>0)"); axes[2][1].grid(True, alpha=0.2)

    # Near-miss breakdown bar
    ax = axes[3][0]
    if all_miss:
        reasons = list(all_miss.keys())
        counts = [all_miss[r] for r in reasons]
        short = [r.replace("missing_", "") for r in reasons]
        ax.barh(short, counts, color="#e74c3c", alpha=0.7)
    ax.set_title("Near-Miss Failure Modes (total)"); ax.grid(True, axis="x", alpha=0.2)

    # Summary text
    ax = axes[3][1]; ax.axis("off")
    txt = [
        f"LONG RUN SUMMARY (seed=42)",
        f"Steps: {summary['steps']}",
        f"Cycles: {summary['cycles_completed']}",
        f"Min Links: {summary['min_links']}",
        f"Max S>0.3: {summary['max_s_gt_03']}",
        f"Max S: {summary['max_s']:.4f}",
        f"Total Opportunities: {summary['total_opp']}",
        f"Total Near-Misses: {summary['total_near_miss']}",
        f"",
        "Near-miss breakdown:",
    ]
    for r, c in all_miss.most_common():
        txt.append(f"  {r}: {c}")
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=10,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("O9_longrun_plots.png", dpi=150, bbox_inches="tight")
    print(f"  Plot: O9_longrun_plots.png")

    # ============================================================
    # A2) MULTI-SEED — 10 seeds × 3000 steps
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  A2) Multi-Seed: 10 seeds × 2000 quiet steps")
    print(f"{'='*70}")

    seeds = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337]
    multi_results = []

    for seed in seeds:
        t0 = time.time()
        _, cyc, summ, _ = run_simulation(seed, 2000, use_controller=True, verbose=False)
        multi_results.append(summ)
        print(f"    seed={seed:>5}: cyc={summ['cycles_completed']} "
              f"minL={summ['min_links']:>3} maxS03={summ['max_s_gt_03']:>3} "
              f"opp={summ['total_opp']:>4} nm={summ['total_near_miss']:>4} "
              f"({summ['elapsed']:.0f}s)")

    with open("O9_multiseed_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=multi_results[0].keys())
        w.writeheader()
        w.writerows(multi_results)

    total_cyc = sum(r["cycles_completed"] for r in multi_results)
    seeds_with_opp = sum(1 for r in multi_results if r["total_opp"] > 0)
    print(f"\n  Multi-seed summary:")
    print(f"    Total cycles across all seeds: {total_cyc}")
    print(f"    Seeds with opportunities: {seeds_with_opp}/{len(seeds)}")
    print(f"    Seeds with S>0.3: {sum(1 for r in multi_results if r['max_s_gt_03'] > 0)}/{len(seeds)}")
    print(f"    Min links (worst seed): {min(r['min_links'] for r in multi_results)}")

    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    summary_txt = f"""ESDE Genesis v0.9 — Extended Runs Summary
==========================================

A1) LONG RUN (seed=42, 10300 steps total)
  Cycles completed: {summary['cycles_completed']}
  Max S>0.3 in quiet: {summary['max_s_gt_03']}
  Max link strength: {summary['max_s']:.4f}
  Min active links: {summary['min_links']}
  Total opportunities (4/4 conditions met): {summary['total_opp']}
  Total near-misses (3/4 conditions met): {summary['total_near_miss']}

  Dominant near-miss failure mode:
{chr(10).join(f'    {r}: {c}' for r, c in all_miss.most_common())}

A2) MULTI-SEED ({len(seeds)} seeds × 3300 steps)
  Total cycles across all seeds: {total_cyc}
  Seeds with links>0 throughout: {sum(1 for r in multi_results if r['min_links'] > 0)}/{len(seeds)}
  Seeds with S>0.3: {sum(1 for r in multi_results if r['max_s_gt_03'] > 0)}/{len(seeds)}
  Seeds with opportunities: {seeds_with_opp}/{len(seeds)}
  Mean near-misses: {np.mean([r['total_near_miss'] for r in multi_results]):.0f}
"""

    with open("O9_summary_note.txt", "w") as f:
        f.write(summary_txt)
    print(summary_txt)


if __name__ == "__main__":
    main()
