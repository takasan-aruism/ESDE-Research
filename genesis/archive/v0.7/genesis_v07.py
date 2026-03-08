"""
ESDE Genesis v0.7 — Axiom X Controller
=========================================
Adaptive parameter tuning to find the metabolic regime.

Controller adjusts 4 parameters via round-robin hill climbing
to maximize Vitality V = R + w1*S + w2*M + w3*P.

Core engine unchanged. Probe: does adaptive tuning enable node-level cycles?

Designed: Gemini | Audited: GPT | Built: Claude
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import time
from collections import Counter, defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from controller import AdaptiveController

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300
QUIET_STEPS = 4000  # long quiet for controller to explore
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005

STATE_NAMES = {0: "Dust", 1: "A", 2: "B", 3: "C"}


class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list)
        self.completed_cycles = []

    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i])
            h = self.history[i]
            if not h or h[-1][1] != z:
                h.append((step, z))

    def detect_cycles(self):
        self.completed_cycles = []
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0:
                    if states[i+2] in (1, 2):
                        for j in range(i+3, len(states)):
                            if states[j] == 3:
                                self.completed_cycles.append({
                                    "node_id": nid,
                                    "cycle": [STATE_NAMES[s] for s in states[i:j+1]],
                                    "length": j - i,
                                    "start_step": h[i][0],
                                    "end_step": h[j][0],
                                    "duration": h[j][0] - h[i][0],
                                })
                                break
        return self.completed_cycles


def main():
    print("=" * 70)
    print("  ESDE Genesis v0.7 — Axiom X Controller")
    print("  'Can the system tune itself into metabolism?'")
    print("=" * 70)
    print(f"  Controller: window=200, round-robin hill climbing")
    print(f"  V = R + 10*S + 2*M + 1*P")
    print(f"  Quiet phase: {QUIET_STEPS} steps ({QUIET_STEPS//200} windows)")
    print()

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    phys_params = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0)
    physics = GenesisPhysics(phys_params)

    chem_params = ChemistryParams(enabled=True)
    chem = ChemistryEngine(chem_params)
    logger = GenesisLogger()
    controller = AdaptiveController(window_size=200)
    tracker = CycleTracker()

    # Apply initial controller params
    controller.apply_to_system(chem_params, state)

    t0 = time.time()

    # ---- INJECTION (no controller) ----
    print("  Injection Phase (no adaptation)...")
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        rxns = chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state, reactions=rxns)
        tracker.record(state, state.step - 1)

    print(f"    Injection done. C={sum(1 for i in state.alive_n if state.Z[i]==3)} "
          f"L={len(state.alive_l)}")

    # ---- QUIET (with controller) ----
    print(f"\n  Quiet Phase ({QUIET_STEPS} steps, controller active)...")
    window_history = []  # last window_size entries for controller
    cycles_per_window = []

    for step in range(QUIET_STEPS):
        cur_step = state.step

        # Background micro-injection (rate from controller)
        bg_prob = controller.get_param("background_injection_prob")
        mask = state.rng.random(N_NODES) < bg_prob
        for i in range(N_NODES):
            if mask[i] and i in state.alive_n:
                state.E[i] = min(1.0, state.E[i] + 0.3)
                if state.Z[i] == 0 and state.rng.random() < 0.5:
                    state.Z[i] = 1 if state.rng.random() < 0.5 else 2

        physics.step_pre_chemistry(state)

        # Ensure chem params reflect controller
        chem.params.E_thr = controller.get_param("reaction_energy_threshold")
        chem.params.exothermic_release = controller.get_param("exothermic_release_amount")
        state.EXTINCTION = controller.get_param("link_death_threshold")

        rxns = chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state, event="quiet", reactions=rxns)
        tracker.record(state, state.step - 1)
        controller.track_c_lifetimes(state)

        # Collect window data
        sc = Counter(int(state.Z[i]) for i in state.alive_n)
        rc = Counter(r.rule for r in rxns)
        rm = sum(state.S[k] for k in state.alive_l if state.R.get(k, 0) > 0)
        window_history.append({
            "n_Dust": sc.get(0, 0), "n_A": sc.get(1, 0),
            "n_B": sc.get(2, 0), "n_C": sc.get(3, 0),
            "rxn_total": len(rxns),
            "rxn_synth": rc.get(1, 0), "rxn_auto": rc.get(2, 0),
            "rxn_decay": rc.get(3, 0),
            "resonant_mass": rm,
        })

        # Controller evaluation at window boundary
        if (step + 1) % controller.window_size == 0:
            recent = window_history[-controller.window_size:]
            entry = controller.evaluate_and_adapt(recent)

            # Count cycles so far
            cycles_so_far = tracker.detect_cycles()
            n_cycles = len(cycles_so_far)
            cycles_per_window.append(n_cycles)

            w = entry["window"]
            print(f"    W{w:>2}: V={entry['V']:>7.1f} "
                  f"(R={entry['R']:>3} S={entry['S']:.2f} "
                  f"M={entry['M']:.1f} P={entry['P']:.0f}) "
                  f"dV={entry['delta_V']:>+7.1f} "
                  f"→ {entry['param_adjusted']}="
                  f"{entry['new_value']:.4f} "
                  f"{'(rev)' if entry['reverted'] else ''} "
                  f"cycles={n_cycles} "
                  f"({time.time()-t0:.0f}s)")

    # Final cycle detection
    all_cycles = tracker.detect_cycles()
    elapsed = time.time() - t0

    # ============================================================
    # RESULTS
    # ============================================================

    print(f"\n{'='*70}")
    print(f"  RESULTS — Axiom X Controller")
    print(f"{'='*70}")

    print(f"\n  Total cycles completed: {len(all_cycles)}")
    print(f"  Unique cycling nodes: {len(set(c['node_id'] for c in all_cycles))}")
    print(f"  Controller windows: {controller.window_count}")
    print(f"  Best V: {max(e['V'] for e in controller.log):.1f} "
          f"(window {max(controller.log, key=lambda e: e['V'])['window']})")

    # Final parameter values
    print(f"\n  Final Parameter Values:")
    for p in controller.params:
        print(f"    {p.name:<35} {p.value:.5f}  "
              f"[{p.min_bound}, {p.max_bound}]")

    # Cycle details
    if all_cycles:
        print(f"\n  Cycle Details:")
        patterns = Counter(tuple(c["cycle"]) for c in all_cycles)
        for pat, count in patterns.most_common(10):
            print(f"    {' → '.join(pat)} : {count}")
        durations = [c["duration"] for c in all_cycles]
        print(f"  Duration: mean={np.mean(durations):.0f} "
              f"min={min(durations)} max={max(durations)}")
        print(f"\n  First 5 cycles:")
        for c in all_cycles[:5]:
            print(f"    node {c['node_id']:>3}: {' → '.join(c['cycle'])} "
                  f"step {c['start_step']}-{c['end_step']}")

    # Controller log export
    controller.export_log("controller_log.csv")
    print(f"\n  Controller log: controller_log.csv")

    # ============================================================
    # PLOTS
    # ============================================================

    fig, axes = plt.subplots(4, 2, figsize=(20, 22))
    fig.suptitle("ESDE Genesis v0.7 — Axiom X Controller\n"
                 "Adaptive Parameter Tuning for Metabolic Emergence",
                 fontsize=14, fontweight="bold", y=0.99)

    clog = controller.log
    windows = [e["window"] for e in clog]

    # 1. Vitality over windows
    ax = axes[0][0]
    ax.plot(windows, [e["V"] for e in clog], "o-", color="#2ecc71",
            markersize=4, linewidth=1.5)
    ax.set_title("Vitality Score (V) per Window", fontsize=10)
    ax.set_ylabel("V")
    ax.grid(True, alpha=0.2)

    # 2. V components
    ax = axes[0][1]
    ax.plot(windows, [e["R"] for e in clog], label="R (reactions)", linewidth=1.2)
    ax.plot(windows, [e["S"]*10 for e in clog], label="S×10 (diversity)", linewidth=1.2)
    ax.plot(windows, [e["M"]*2 for e in clog], label="M×2 (mass)", linewidth=1.2)
    ax.plot(windows, [e["P"] for e in clog], label="P (persistence)", linewidth=1.2)
    ax.set_title("V Components (weighted)", fontsize=10)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.2)

    # 3-6. Parameter traces
    param_colors = ["#e74c3c", "#3498db", "#f39c12", "#9b59b6"]
    for idx, p in enumerate(controller.params):
        row = 1 + idx // 2
        col = idx % 2
        ax = axes[row][col]
        # Extract this param's values from log
        vals = []
        for e in clog:
            if e["param_adjusted"] == p.name:
                vals.append((e["window"], e["new_value"]))
        if vals:
            ws, vs = zip(*vals)
            ax.plot(ws, vs, "o-", color=param_colors[idx],
                    markersize=4, linewidth=1.2)
        ax.axhline(y=p.min_bound, color="gray", linestyle=":", alpha=0.3)
        ax.axhline(y=p.max_bound, color="gray", linestyle=":", alpha=0.3)
        ax.set_title(f"{p.name} (current: {p.value:.4f})", fontsize=9)
        ax.set_ylabel("value")
        ax.grid(True, alpha=0.2)

    # 7. Cycles per window
    ax = axes[3][0]
    if cycles_per_window:
        ax.bar(range(1, len(cycles_per_window)+1), cycles_per_window,
               color="#2ecc71", alpha=0.7)
    ax.set_title("Cumulative Cycles Detected (per window)", fontsize=10)
    ax.set_xlabel("Window")
    ax.grid(True, alpha=0.2)

    # 8. System state timeseries
    ax = axes[3][1]
    ts = logger.get_timeseries()
    ax.plot(ts["step"], ts["n_C"], label="C", color="#2ecc71", linewidth=1.2)
    ax.plot(ts["step"], ts["n_A"], label="A", color="#3498db", linewidth=1.0, alpha=0.7)
    ax.plot(ts["step"], ts["n_B"], label="B", color="#e67e22", linewidth=1.0, alpha=0.7)
    ax.plot(ts["step"], ts["active_links"], label="Links", color="#e74c3c",
            linewidth=1.0, alpha=0.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("System State over Time", fontsize=10)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.2)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("genesis_v07_axiom_x.png", dpi=150, bbox_inches="tight")
    print(f"  Plot: genesis_v07_axiom_x.png")

    # Export
    logger.export_json("genesis_v07_log.json")
    with open("genesis_v07_cycles.json", "w") as f:
        json.dump(all_cycles, f, indent=2)

    # ============================================================
    # VERDICT
    # ============================================================

    n_cycles = len(all_cycles)
    print(f"""
{'='*70}
  VERDICT
{'='*70}

  Cycles completed: {n_cycles}
  Controller windows: {controller.window_count}
  Best Vitality: {max(e['V'] for e in clog):.1f}
  Final params:""")
    for p in controller.params:
        print(f"    {p.name}: {p.value:.5f}")

    if n_cycles > 0:
        print(f"""
  >>> METABOLIC LOOP ACHIEVED VIA SELF-TUNING <<<
  The system found its own parameter regime for cycle execution.
""")
    else:
        print(f"""
  cycle_execution = 0

  The controller explored the parameter space but did not find
  a regime enabling node-level cycle completion.
  This is a valid scientific result.
""")

    print(f"  Elapsed: {elapsed:.0f}s | Seed: {SEED}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
