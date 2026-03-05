"""
ESDE Genesis v0.4 — Main Experiment
======================================
"Artificial Wave Physics"
Crystal → Oscillator → Signal

Conditions:
  Dust:    Exclusion OFF, Resonance OFF, Phase OFF
  Crystal: Exclusion ON,  Resonance ON,  Phase OFF  (v0.3 baseline)
  Wave:    Exclusion ON,  Resonance ON,  Phase ON   (v0.4 test)

Hypothesis: Crystals with phase dynamics produce self-sustaining
oscillations ("heartbeats") after injection stops.

Designed: Gemini | Audited: GPT | Built: Claude
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
BETA = 1.0


def run_condition(name, params, verbose=True):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    physics = GenesisPhysics(params)
    logger = GenesisLogger()
    t0 = time.time()

    for step in range(INJECTION_STEPS):
        evt = ""
        if step % INJECT_INTERVAL == 0:
            physics.inject(state)
            evt = "inject"
        cd = physics.step(state)
        if cd is not None:
            logger.observe_loops(cd)
        logger.observe(state, event=evt)

        if verbose and step % 100 == 99:
            r = logger.log[-1]
            print(f"    {name} step {step+1}: "
                  f"L={r['active_links']:>3} RM={r['resonant_mass']:.1f} "
                  f"r={r['kuramoto_r']:.3f} osc={r['active_oscillators']} "
                  f"({time.time()-t0:.0f}s)")

    logger.take_snapshot(state, "end_injection")
    quiet_start = state.step

    for step in range(QUIET_STEPS):
        cd = physics.step(state)
        if cd is not None:
            logger.observe_loops(cd)
        logger.observe(state, event="quiet")

        if verbose and step % 100 == 99:
            r = logger.log[-1]
            print(f"    {name} quiet {step+1}: "
                  f"L={r['active_links']:>3} RM={r['resonant_mass']:.1f} "
                  f"r={r['kuramoto_r']:.3f} osc={r['active_oscillators']} "
                  f"({time.time()-t0:.0f}s)")

    logger.take_snapshot(state, "end_quiet")
    kpis = logger.compute_kpis(quiet_start)
    kpis["elapsed"] = round(time.time() - t0, 1)

    if verbose:
        inj = logger.log[INJECTION_STEPS - 1]
        end = logger.log[-1]
        print(f"  {name:30s} "
              f"inj=[L={inj['active_links']:>3} r={inj['kuramoto_r']:.3f}] "
              f"end=[L={end['active_links']:>3} r={end['kuramoto_r']:.3f}] "
              f"L_HL={kpis.get('link_half_life','?')} "
              f"OscP={kpis.get('oscillation_persistence','?')} "
              f"kr={kpis.get('mean_kuramoto_r','?')} "
              f"({kpis['elapsed']}s)")

    return logger, kpis


def plot_comparison(loggers, kpis_all, save_path):
    colors = {"Dust": "#e74c3c", "Crystal": "#f39c12", "Wave": "#2ecc71"}

    fig = plt.figure(figsize=(22, 18))
    fig.suptitle("ESDE Genesis v0.4 — Artificial Wave Physics\n"
                 "Crystal → Oscillator → Signal",
                 fontsize=15, fontweight="bold", y=0.99)

    gs = fig.add_gridspec(4, 3, hspace=0.4, wspace=0.3)

    # Row 0: Standard topology metrics
    m_row0 = [("total_energy", "Total Energy"),
              ("active_links", "Active Links"),
              ("resonant_mass", "Resonant Mass")]
    for col, (mk, mt) in enumerate(m_row0):
        ax = fig.add_subplot(gs[0, col])
        for name, lgr in loggers.items():
            ts = lgr.get_timeseries()
            ax.plot(ts["step"], ts[mk], label=name,
                    color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
        ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
        ax.set_title(mt, fontsize=10)
        ax.grid(True, alpha=0.15)
        if col == 0:
            ax.legend(fontsize=8)

    # Row 1: Phase dynamics metrics (THE NEW STUFF)
    ax_kr = fig.add_subplot(gs[1, 0])
    for name, lgr in loggers.items():
        ts = lgr.get_timeseries()
        ax_kr.plot(ts["step"], ts["kuramoto_r"], label=name,
                   color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
    ax_kr.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax_kr.set_title("Kuramoto Order Parameter (r)", fontsize=10, fontweight="bold")
    ax_kr.set_ylabel("r  (0=noise, 1=sync)")
    ax_kr.grid(True, alpha=0.15)
    ax_kr.legend(fontsize=8)

    ax_osc = fig.add_subplot(gs[1, 1])
    for name, lgr in loggers.items():
        ts = lgr.get_timeseries()
        ax_osc.plot(ts["step"], ts["active_oscillators"], label=name,
                    color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
    ax_osc.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax_osc.set_title("Active Oscillators (E>0.1)", fontsize=10, fontweight="bold")
    ax_osc.grid(True, alpha=0.15)

    ax_rl = fig.add_subplot(gs[1, 2])
    for name, lgr in loggers.items():
        ts = lgr.get_timeseries()
        ax_rl.plot(ts["step"], ts["resonant_links"], label=name,
                   color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
    ax_rl.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax_rl.set_title("Resonant Links", fontsize=10)
    ax_rl.grid(True, alpha=0.15)

    # Row 2: Quiet phase zoom (first 200 steps of quiet)
    quiet_range = (INJECTION_STEPS, INJECTION_STEPS + 200)
    m_zoom = [("active_links", "Links (Quiet Zoom)"),
              ("kuramoto_r", "Kuramoto r (Quiet Zoom)"),
              ("active_oscillators", "Oscillators (Quiet Zoom)")]
    for col, (mk, mt) in enumerate(m_zoom):
        ax = fig.add_subplot(gs[2, col])
        for name, lgr in loggers.items():
            ts = lgr.get_timeseries()
            mask = [(quiet_range[0] <= s <= quiet_range[1]) for s in ts["step"]]
            steps_z = [s for s, m in zip(ts["step"], mask) if m]
            vals_z = [v for v, m in zip(ts[mk], mask) if m]
            ax.plot(steps_z, vals_z, label=name,
                    color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
        ax.set_title(mt, fontsize=10)
        ax.grid(True, alpha=0.15)
        if col == 0:
            ax.legend(fontsize=8)

    # Row 3: KPI Summary
    ax_kpi = fig.add_subplot(gs[3, :])
    ax_kpi.axis("off")

    header = f"{'Metric':<30} {'Dust':>10} {'Crystal':>10} {'Wave':>10}"
    rows = [header, "-" * 62]
    kpi_keys = [
        ("link_half_life", "Link Half-Life"),
        ("resonant_mass_half_life", "Resonant Mass HL"),
        ("energy_half_life", "Energy Half-Life"),
        ("oscillation_persistence", "Oscillation Persist"),
        ("mean_kuramoto_r", "Mean Kuramoto r"),
        ("peak_kuramoto_r", "Peak Kuramoto r"),
        ("peak_active_oscillators", "Peak Oscillators"),
        ("crystal_count", "Crystal Count"),
    ]
    for kk, kn in kpi_keys:
        vals = []
        for cname in ["Dust", "Crystal", "Wave"]:
            v = kpis_all.get(cname, {}).get(kk, "?")
            vals.append(f"{v}" if v is not None else "N/A")
        rows.append(f"{kn:<30} {vals[0]:>10} {vals[1]:>10} {vals[2]:>10}")

    ax_kpi.text(0.02, 0.95, "\n".join(rows), transform=ax_kpi.transAxes,
                fontsize=10, va="top", fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="lightyellow",
                          edgecolor="gray", alpha=0.8))

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {save_path}")


def main():
    print("=" * 70)
    print("  ESDE Genesis v0.4 — Artificial Wave Physics")
    print("  'Can crystals have a heartbeat?'")
    print("=" * 70)
    print(f"  beta={BETA}  gamma=1.0  K_sync=0.1  alpha=0.0")
    print(f"  phase_factor = 0.5 + 0.5*gamma*cos(dtheta)  [audit corrected]")
    print(f"  nodes={N_NODES}  inject={INJECTION_STEPS}  quiet={QUIET_STEPS}")
    print()

    loggers = {}
    kpis_all = {}

    # Dust: no structure, no phase
    print("=" * 70)
    print("  Dust: No Exclusion, No Resonance, No Phase")
    print("=" * 70)
    p_dust = PhysicsParams(
        exclusion_enabled=False, resonance_enabled=False,
        phase_enabled=False, beta=0)
    l, k = run_condition("Dust", p_dust)
    loggers["Dust"] = l; kpis_all["Dust"] = k

    # Crystal: v0.3 behavior (no phase)
    print("\n" + "=" * 70)
    print("  Crystal (v0.3): Exclusion ON, Resonance ON, Phase OFF")
    print("=" * 70)
    p_crystal = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=False, beta=BETA)
    l, k = run_condition("Crystal", p_crystal)
    loggers["Crystal"] = l; kpis_all["Crystal"] = k

    # Wave: v0.4 (phase ON)
    print("\n" + "=" * 70)
    print("  Wave (v0.4): Exclusion ON, Resonance ON, Phase ON")
    print("  >>> THE CRITICAL TEST <<<")
    print("=" * 70)
    p_wave = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        gamma=1.0, K_sync=0.1, alpha=0.0)
    l, k = run_condition("Wave", p_wave)
    loggers["Wave"] = l; kpis_all["Wave"] = k

    # Plot
    print("\n" + "=" * 70)
    print("  Generating Plots...")
    print("=" * 70)
    plot_comparison(loggers, kpis_all, "genesis_v04_comparison.png")

    # Export
    for name, lgr in loggers.items():
        lgr.export_json(f"genesis_v04_log_{name.lower()}.json")

    # Report
    d = kpis_all["Dust"]
    c = kpis_all["Crystal"]
    w = kpis_all["Wave"]

    print(f"""
{'='*70}
  GENESIS v0.4 RESULTS — Artificial Wave Physics
{'='*70}

  +------------------------------+--------+--------+--------+
  |                              | Dust   |Crystal | Wave   |
  +------------------------------+--------+--------+--------+
  | Link Half-Life               | {str(d.get('link_half_life','?')):>5}  | {str(c.get('link_half_life','?')):>5}  | {str(w.get('link_half_life','?')):>5}  |
  | Resonant Mass HL             | {str(d.get('resonant_mass_half_life','N/A')):>5}  | {str(c.get('resonant_mass_half_life','N/A')):>5}  | {str(w.get('resonant_mass_half_life','N/A')):>5}  |
  | Energy Half-Life             | {str(d.get('energy_half_life','?')):>5}  | {str(c.get('energy_half_life','?')):>5}  | {str(w.get('energy_half_life','?')):>5}  |
  | Oscillation Persistence      | {str(d.get('oscillation_persistence','?')):>5}  | {str(c.get('oscillation_persistence','?')):>5}  | {str(w.get('oscillation_persistence','?')):>5}  |
  | Mean Kuramoto r              | {str(d.get('mean_kuramoto_r','?')):>5}  | {str(c.get('mean_kuramoto_r','?')):>5}  | {str(w.get('mean_kuramoto_r','?')):>5}  |
  | Peak Kuramoto r              | {str(d.get('peak_kuramoto_r','?')):>5}  | {str(c.get('peak_kuramoto_r','?')):>5}  | {str(w.get('peak_kuramoto_r','?')):>5}  |
  +------------------------------+--------+--------+--------+
""")

    # Interpretation
    wave_better_links = (w.get('link_half_life') or 0) > (c.get('link_half_life') or 0)
    wave_has_signal = (w.get('oscillation_persistence', 0) or 0) > (c.get('oscillation_persistence', 0) or 0)
    wave_sync = (w.get('mean_kuramoto_r', 0) or 0) > 0.3

    print("  INTERPRETATION:")
    if wave_has_signal and wave_sync:
        print("""
  >>> HEARTBEAT DETECTED <<<

  Phase dynamics produce sustained oscillations in crystals.
  Kuramoto synchronization shows phase-locked behavior.
  v0.3 built the hardware. v0.4 generated the signal.
  Dust → Crystal → Oscillator → Signal confirmed.
""")
    elif wave_has_signal:
        print("""
  OSCILLATION EXISTS BUT WEAK SYNCHRONIZATION

  Active oscillators persist longer with phase dynamics,
  but Kuramoto r is low — phases are not well locked.
  Phase coupling (K_sync) may need tuning.
""")
    elif wave_better_links:
        print("""
  PHASE DYNAMICS IMPROVE STRUCTURAL PERSISTENCE

  Link half-life is better with phase, but no clear oscillation signal.
  Phase-modulated flow may enhance resonance without creating heartbeats.
""")
    else:
        print("""
  NO SIGNIFICANT EFFECT AT CURRENT PARAMETERS

  Phase dynamics do not improve over v0.3 Crystal baseline.
  Consider: increasing gamma, K_sync, or alpha.
""")

    print(f"""  Parameters: gamma=1.0, K_sync=0.1, alpha=0.0 (audit-conservative)
  No parameters were tuned to force success.

{'='*70}
  Genesis v0.4 complete.
{'='*70}""")


if __name__ == "__main__":
    main()
