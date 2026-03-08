"""
ESDE Genesis v0.4 — Parameter Sweep
=====================================
Problem: Topology persists (L_HL=155) but energy dies (E_HL=14).
No oscillation possible without energy.

Hypothesis: Node decay rate is too high for sustained oscillation.
The "hardware" (links) survives but the "fuel" (energy) doesn't.

Sweep:
  1. node_decay: {0.05, 0.02, 0.01, 0.005} — can energy survive longer?
  2. K_sync: {0.0, 0.1, 0.3, 0.5} — does stronger coupling help?
"""

import numpy as np
import matplotlib.pyplot as plt
import time

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42; BETA = 1.0


def run_one(node_decay=0.05, K_sync=0.1, phase=True):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    params = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=phase, beta=BETA,
        decay_rate_node=node_decay, K_sync=K_sync, alpha=0.0, gamma=1.0)
    physics = GenesisPhysics(params)
    logger = GenesisLogger()

    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            physics.inject(state)
        cd = physics.step(state)
        if cd: logger.observe_loops(cd)
        logger.observe(state)

    quiet_start = state.step
    for step in range(QUIET_STEPS):
        cd = physics.step(state)
        if cd: logger.observe_loops(cd)
        logger.observe(state)

    return logger, logger.compute_kpis(quiet_start)


def main():
    print("=" * 70)
    print("  Genesis v0.4 — Finding the Heartbeat")
    print("  Problem: E_HL=14 (energy dies). L_HL=155 (structure lives)")
    print("  Can we keep the fuel alive long enough to oscillate?")
    print("=" * 70)

    # Sweep 1: Node decay rate
    decays = [0.05, 0.02, 0.01, 0.005]
    print("\n  --- Sweep 1: Node Decay Rate (K_sync=0.1, phase=ON) ---")
    print(f"  {'decay':>8} {'E_HL':>6} {'L_HL':>6} {'RM_HL':>6} {'OscP':>6} {'kr_mean':>8} {'kr_peak':>8}")

    sweep1_loggers = {}
    sweep1_kpis = {}
    for nd in decays:
        t0 = time.time()
        lgr, kpis = run_one(node_decay=nd)
        label = f"nd={nd}"
        sweep1_loggers[label] = lgr
        sweep1_kpis[label] = kpis
        print(f"  {nd:>8.3f} {str(kpis.get('energy_half_life','?')):>6} "
              f"{str(kpis.get('link_half_life','?')):>6} "
              f"{str(kpis.get('resonant_mass_half_life','?')):>6} "
              f"{str(kpis.get('oscillation_persistence','?')):>6} "
              f"{str(kpis.get('mean_kuramoto_r','?')):>8} "
              f"{str(kpis.get('peak_kuramoto_r','?')):>8}  "
              f"({time.time()-t0:.1f}s)")

    # Find best decay rate
    best_decay = max(decays, key=lambda d: sweep1_kpis[f"nd={d}"].get("oscillation_persistence", 0))
    print(f"\n  Best node_decay for oscillation: {best_decay}")

    # Sweep 2: K_sync at best decay
    k_syncs = [0.0, 0.1, 0.3, 0.5]
    print(f"\n  --- Sweep 2: K_sync (node_decay={best_decay}, phase=ON) ---")
    print(f"  {'K_sync':>8} {'E_HL':>6} {'L_HL':>6} {'OscP':>6} {'kr_mean':>8} {'kr_peak':>8}")

    sweep2_loggers = {}
    sweep2_kpis = {}
    for ks in k_syncs:
        t0 = time.time()
        lgr, kpis = run_one(node_decay=best_decay, K_sync=ks)
        label = f"ks={ks}"
        sweep2_loggers[label] = lgr
        sweep2_kpis[label] = kpis
        print(f"  {ks:>8.2f} {str(kpis.get('energy_half_life','?')):>6} "
              f"{str(kpis.get('link_half_life','?')):>6} "
              f"{str(kpis.get('oscillation_persistence','?')):>6} "
              f"{str(kpis.get('mean_kuramoto_r','?')):>8} "
              f"{str(kpis.get('peak_kuramoto_r','?')):>8}  "
              f"({time.time()-t0:.1f}s)")

    # Sweep 3: Phase ON vs OFF at best decay (control)
    print(f"\n  --- Control: Phase OFF vs ON at node_decay={best_decay} ---")
    _, kpi_off = run_one(node_decay=best_decay, phase=False)
    _, kpi_on = run_one(node_decay=best_decay, phase=True)
    print(f"  Phase OFF: E_HL={kpi_off.get('energy_half_life','?')} "
          f"L_HL={kpi_off.get('link_half_life','?')} "
          f"OscP={kpi_off.get('oscillation_persistence','?')}")
    print(f"  Phase ON:  E_HL={kpi_on.get('energy_half_life','?')} "
          f"L_HL={kpi_on.get('link_half_life','?')} "
          f"OscP={kpi_on.get('oscillation_persistence','?')}")

    # Plot: Sweep 1
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle(f"Genesis v0.4 — Parameter Sweep (Finding the Heartbeat)",
                 fontsize=14, fontweight="bold")

    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(decays)))
    metrics = [("active_links", "Active Links"), ("total_energy", "Total Energy"),
               ("kuramoto_r", "Kuramoto r"), ("active_oscillators", "Active Oscillators"),
               ("resonant_mass", "Resonant Mass")]

    for idx, (mk, mt) in enumerate(metrics):
        row, col = divmod(idx, 3)
        ax = axes[row][col]
        for i, nd in enumerate(decays):
            ts = sweep1_loggers[f"nd={nd}"].get_timeseries()
            ax.plot(ts["step"], ts[mk], label=f"decay={nd}",
                    color=colors[i], linewidth=1.5)
        ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
        ax.set_title(mt, fontsize=10)
        ax.grid(True, alpha=0.15)
        if idx == 0: ax.legend(fontsize=7)

    # Bar: OscP vs decay
    ax_bar = axes[1][2]
    x = np.arange(len(decays))
    oscps = [sweep1_kpis[f"nd={d}"]["oscillation_persistence"] for d in decays]
    ehls = [sweep1_kpis[f"nd={d}"].get("energy_half_life") or 0 for d in decays]
    w = 0.35
    b1 = ax_bar.bar(x - w/2, oscps, w, label="Osc Persist", color="#2ecc71")
    b2 = ax_bar.bar(x + w/2, ehls, w, label="E Half-Life", color="#e74c3c")
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels([str(d) for d in decays])
    ax_bar.set_xlabel("Node Decay Rate")
    ax_bar.set_title("Oscillation vs Energy Survival")
    ax_bar.legend(fontsize=8)
    ax_bar.grid(True, axis="y", alpha=0.2)
    for bar, v in zip(b1, oscps):
        ax_bar.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, str(v), ha="center", fontsize=8)
    for bar, v in zip(b2, ehls):
        ax_bar.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, str(v), ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig("genesis_v04_sweep.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: genesis_v04_sweep.png")


if __name__ == "__main__":
    main()
