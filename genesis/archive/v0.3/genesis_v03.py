"""
ESDE Genesis v0.3 — Main Experiment (Final)
==============================================
"Artificial Topology Chemistry"

3 conditions:
  Dust    (Control-1): Exclusion OFF, Resonance OFF
  Web     (Control-2): Exclusion ON,  Resonance OFF
  Crystal (Genesis):   Exclusion ON,  Resonance ON

Execution: Flow → Resonance → Decay → Exclusion
Metrics: Resonant Mass, Crystal Count (life>100 & size>3), Loop Spectrum

Designed by: Gemini | Audited by: GPT | Implemented by: Claude
"""

import numpy as np
import matplotlib.pyplot as plt
import time

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger

N_NODES = 200
C_MAX = 1.0
INJECTION_STEPS = 300
QUIET_STEPS = 400
INJECT_INTERVAL = 3
SEED = 42


def run_condition(name, params, verbose=True):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    physics = GenesisPhysics(params)
    logger = GenesisLogger()
    t0 = time.time()

    # Injection Phase
    for step in range(INJECTION_STEPS):
        evt = ""
        if step % INJECT_INTERVAL == 0:
            physics.inject(state)
            evt = "inject"
        cycle_data = physics.step(state)
        if cycle_data is not None:
            logger.observe_loops(cycle_data)
        logger.observe(state, event=evt)

        if verbose and step % 100 == 99:
            r = logger.log[-1]
            ls = r.get("loop_spectrum", {})
            print(f"    {name} step {step+1}: "
                  f"L={r['active_links']:>3} RM={r['resonant_mass']:.1f} "
                  f"loops=[3:{ls.get('3',0)} 4:{ls.get('4',0)} 5:{ls.get('5',0)}] "
                  f"({time.time()-t0:.0f}s)")

    logger.take_snapshot(state, "end_injection")

    # Quiet Phase
    quiet_start = state.step
    for step in range(QUIET_STEPS):
        cycle_data = physics.step(state)
        if cycle_data is not None:
            logger.observe_loops(cycle_data)
        logger.observe(state, event="quiet")

        if verbose and step % 100 == 99:
            r = logger.log[-1]
            ls = r.get("loop_spectrum", {})
            print(f"    {name} quiet {step+1}: "
                  f"L={r['active_links']:>3} RM={r['resonant_mass']:.1f} "
                  f"RL={r['resonant_links']:>3} "
                  f"loops=[3:{ls.get('3',0)} 4:{ls.get('4',0)} 5:{ls.get('5',0)}] "
                  f"({time.time()-t0:.0f}s)")

    logger.take_snapshot(state, "end_quiet")
    kpis = logger.compute_kpis(quiet_start)
    kpis["elapsed"] = round(time.time() - t0, 1)
    kpis["beta"] = params.beta

    if verbose:
        inj = logger.log[INJECTION_STEPS - 1]
        end = logger.log[-1]
        print(f"  {name:30s} "
              f"inj=[L={inj['active_links']:>3} RM={inj['resonant_mass']:.1f}] "
              f"end=[L={end['active_links']:>3} RM={end['resonant_mass']:.1f}] "
              f"L_HL={kpis.get('link_half_life','?'):>4} "
              f"RM_HL={kpis.get('resonant_mass_half_life','?'):>4} "
              f"Crystals={kpis.get('crystal_count',0)} "
              f"({kpis['elapsed']}s)")

    return logger, kpis


def plot_comparison(loggers, kpis_all, save_path):
    colors = {"Dust": "#e74c3c", "Web": "#f39c12", "Crystal": "#2ecc71"}

    fig = plt.figure(figsize=(20, 16))
    fig.suptitle("ESDE Genesis v0.3 — Artificial Topology Chemistry",
                 fontsize=15, fontweight="bold", y=0.98)

    gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.3)

    metrics = [
        ("total_energy", "Total Energy"),
        ("active_links", "Active Links"),
        ("resonant_mass", "Resonant Mass"),
        ("resonant_links", "Resonant Links"),
        ("entropy", "Entropy"),
        ("n_components", "Components"),
        ("active_nodes", "Active Nodes"),
        ("largest_component", "Largest Component"),
    ]

    for idx, (mk, mt) in enumerate(metrics):
        row, col = divmod(idx, 3)
        ax = fig.add_subplot(gs[row, col])
        for name, lgr in loggers.items():
            ts = lgr.get_timeseries()
            ax.plot(ts["step"], ts[mk], label=name,
                    color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
        ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
        ax.set_title(mt, fontsize=10)
        ax.grid(True, alpha=0.15)
        if idx == 0:
            ax.legend(fontsize=8)

    # Row 3: Loop Spectrum (Crystal only)
    ax_loops = fig.add_subplot(gs[2, 2])
    if "Crystal" in loggers:
        ts = loggers["Crystal"].get_timeseries()
        ax_loops.plot(ts["step"], ts["loops_3"], label="3-loops",
                      color="#e74c3c", linewidth=1.2)
        ax_loops.plot(ts["step"], ts["loops_4"], label="4-loops",
                      color="#3498db", linewidth=1.2)
        ax_loops.plot(ts["step"], ts["loops_5"], label="5-loops",
                      color="#9b59b6", linewidth=1.2)
        ax_loops.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
        ax_loops.set_title("Loop Spectrum (Crystal)", fontsize=10)
        ax_loops.legend(fontsize=7)
        ax_loops.grid(True, alpha=0.15)

    # KPI panel
    ax_kpi = fig.add_subplot(gs[3, :])
    ax_kpi.axis("off")
    txt = ""
    for name, kpis in kpis_all.items():
        txt += (f"[{name}]  "
                f"Link HL={kpis.get('link_half_life','?')}  "
                f"RM HL={kpis.get('resonant_mass_half_life','?')}  "
                f"E HL={kpis.get('energy_half_life','?')}  "
                f"Crystals={kpis.get('crystal_count',0)}  "
                f"Alive={kpis.get('structures_alive',0)}  "
                f"Born={kpis.get('total_structures_born',0)}    ")
    ax_kpi.text(0.02, 0.5, txt, transform=ax_kpi.transAxes,
                fontsize=10, va="center", fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="lightyellow",
                          edgecolor="gray", alpha=0.8))

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {save_path}")


def main():
    print("=" * 65)
    print("  ESDE Genesis v0.3 — Artificial Topology Chemistry")
    print("  Designed: Gemini | Audited: GPT | Built: Claude")
    print("=" * 65)
    print(f"  beta=0.1  resonance_interval=10")
    print(f"  cycle_weights: 3->1.0  4->0.5  5->0.25")
    print(f"  nodes={N_NODES}  inject={INJECTION_STEPS}  quiet={QUIET_STEPS}")
    print(f"  Execution: Flow -> Resonance -> Decay -> Exclusion")
    print()

    loggers = {}
    kpis_all = {}

    # Control-1: Dust
    print("=" * 65)
    print("  Control-1 (Dust): No Exclusion, No Resonance")
    print("=" * 65)
    p1 = PhysicsParams(exclusion_enabled=False, resonance_enabled=False)
    l1, k1 = run_condition("Dust", p1)
    loggers["Dust"] = l1
    kpis_all["Dust"] = k1

    # Control-2: Web
    print("\n" + "=" * 65)
    print("  Control-2 (Web): Exclusion ON, No Resonance")
    print("=" * 65)
    p2 = PhysicsParams(exclusion_enabled=True, resonance_enabled=False)
    l2, k2 = run_condition("Web", p2)
    loggers["Web"] = l2
    kpis_all["Web"] = k2

    # Genesis: Crystal
    print("\n" + "=" * 65)
    print("  Genesis (Crystal): Exclusion ON, Resonance ON (beta=0.1)")
    print("=" * 65)
    p3 = PhysicsParams(exclusion_enabled=True, resonance_enabled=True)
    l3, k3 = run_condition("Crystal", p3)
    loggers["Crystal"] = l3
    kpis_all["Crystal"] = k3

    # Plots
    print("\n" + "=" * 65)
    print("  Generating Plots...")
    print("=" * 65)
    plot_comparison(loggers, kpis_all, "genesis_v03_comparison.png")

    # Export logs
    for name, lgr in loggers.items():
        lgr.export_json(f"genesis_v03_log_{name.lower()}.json")

    # Report
    dust = kpis_all["Dust"]
    web = kpis_all["Web"]
    crystal = kpis_all["Crystal"]

    print(f"""
{'='*65}
  GENESIS v0.3 RESULTS (beta=0.1, conservative)
{'='*65}

  +----------------------------+--------+--------+--------+
  |                            | Dust   | Web    |Crystal |
  +----------------------------+--------+--------+--------+
  | Link Half-Life             | {dust.get('link_half_life','?'):>5}  | {web.get('link_half_life','?'):>5}  | {crystal.get('link_half_life','?'):>5}  |
  | Resonant Mass HL           | {dust.get('resonant_mass_half_life','?'):>5}  | {web.get('resonant_mass_half_life','?'):>5}  | {crystal.get('resonant_mass_half_life','?'):>5}  |
  | Energy Half-Life           | {dust.get('energy_half_life','?'):>5}  | {web.get('energy_half_life','?'):>5}  | {crystal.get('energy_half_life','?'):>5}  |
  | Crystal Count (>100 & >3) | {dust.get('crystal_count',0):>5}  | {web.get('crystal_count',0):>5}  | {crystal.get('crystal_count',0):>5}  |
  | Structures Alive           | {dust.get('structures_alive',0):>5}  | {web.get('structures_alive',0):>5}  | {crystal.get('structures_alive',0):>5}  |
  +----------------------------+--------+--------+--------+

{'='*65}
  Genesis v0.3 complete.
{'='*65}""")


if __name__ == "__main__":
    main()
