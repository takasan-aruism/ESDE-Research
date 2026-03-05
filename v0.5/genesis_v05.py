"""
ESDE Genesis v0.5 — Artificial Chemistry
==========================================
Phase-Coupled Chemistry: reactions require topology + energy + phase sync.

4 conditions (audit-mandated ablation):
  Full:      All gates ON, all rules ON
  NoPhase:   Phase gate OFF (cos threshold disabled)
  NoLink:    Link gate OFF (S_thr disabled)
  NoAutocat: Autocatalysis OFF (Rule 2 disabled)

Pass/Fail: C enrichment inside crystals > 1.0 in Full, drops toward 1.0 in controls.

Designed: Gemini | Audited: GPT | Built: Claude
"""

import numpy as np
import matplotlib.pyplot as plt
import time

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005


def run_condition(name, phys_params, chem_params, verbose=True):
    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    physics = GenesisPhysics(phys_params)
    chem = ChemistryEngine(chem_params)
    logger = GenesisLogger()
    t0 = time.time()

    for step in range(INJECTION_STEPS):
        evt = ""
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
            evt = "inject"

        # Phase A+B: physics pre-chemistry
        physics.step_pre_chemistry(state)
        # Phase C: chemistry
        rxns = chem.step(state)
        # Phase D+E+F: physics post-chemistry
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state, event=evt, reactions=rxns)

        if verbose and step % 100 == 99:
            r = logger.log[-1]
            print(f"    {name} step {step+1}: "
                  f"L={r['active_links']:>3} C={r['n_C']:>3} "
                  f"enrich={r['enrichment']:.2f} "
                  f"rxn=[s{r['rxn_synthesis']} a{r['rxn_autocatalysis']} d{r['rxn_decay']}] "
                  f"({time.time()-t0:.0f}s)")

    logger.take_snapshot(state, "end_injection")
    quiet_start = state.step

    for step in range(QUIET_STEPS):
        physics.step_pre_chemistry(state)
        rxns = chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state, event="quiet", reactions=rxns)

        if verbose and step % 100 == 99:
            r = logger.log[-1]
            print(f"    {name} quiet {step+1}: "
                  f"L={r['active_links']:>3} C={r['n_C']:>3} "
                  f"enrich={r['enrichment']:.2f} "
                  f"({time.time()-t0:.0f}s)")

    kpis = logger.compute_kpis(quiet_start)
    kpis["elapsed"] = round(time.time() - t0, 1)
    kpis["name"] = name

    if verbose:
        print(f"  {name:20s} "
              f"peakC={kpis.get('peak_C',0):>3} "
              f"synth={kpis.get('total_synthesis',0):>3} "
              f"autocat={kpis.get('total_autocatalysis',0):>3} "
              f"decay={kpis.get('total_decay',0):>3} "
              f"enrich={kpis.get('mean_enrichment',0):.3f} "
              f"c_life={kpis.get('c_lifetime_mean',0):.0f} "
              f"({kpis['elapsed']}s)")

    return logger, kpis


def make_params(gate_phase=True, gate_link=True, rule_autocat=True):
    pp = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0)
    cp = ChemistryParams(
        enabled=True,
        gate_phase=gate_phase,
        gate_link=gate_link,
        rule_autocatalysis=rule_autocat)
    return pp, cp


def plot_results(loggers, kpis_all, save_path):
    colors = {"Full": "#2ecc71", "NoPhase": "#e74c3c",
              "NoLink": "#f39c12", "NoAutocat": "#9b59b6"}

    fig = plt.figure(figsize=(22, 20))
    fig.suptitle("ESDE Genesis v0.5 — Artificial Chemistry\n"
                 "Phase-Coupled Reactions in Topological Crystals",
                 fontsize=15, fontweight="bold", y=0.99)
    gs = fig.add_gridspec(5, 3, hspace=0.4, wspace=0.3)

    def plot_metric(row, col, key, title, ylabel=None):
        ax = fig.add_subplot(gs[row, col])
        for name, lgr in loggers.items():
            ts = lgr.get_timeseries()
            ax.plot(ts["step"], ts[key], label=name,
                    color=colors.get(name, "gray"), linewidth=1.5, alpha=0.85)
        ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
        ax.set_title(title, fontsize=10)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.15)
        return ax

    # Row 0: Chemistry state counts
    ax = plot_metric(0, 0, "n_C", "Compound C Count", "Nodes")
    ax.legend(fontsize=7)
    plot_metric(0, 1, "n_A", "Element A Count")
    plot_metric(0, 2, "n_B", "Element B Count")

    # Row 1: Enrichment + reactions
    ax_en = plot_metric(1, 0, "enrichment", "C Enrichment in Crystals", "ratio")
    ax_en.axhline(y=1.0, color="red", linestyle=":", alpha=0.5, label="baseline")
    ax_en.legend(fontsize=7)

    plot_metric(1, 1, "rxn_synthesis", "Synthesis Reactions / Step")
    plot_metric(1, 2, "rxn_autocatalysis", "Autocatalysis Reactions / Step")

    # Row 2: Physical substrate
    plot_metric(2, 0, "active_links", "Active Links")
    plot_metric(2, 1, "resonant_mass", "Resonant Mass")
    plot_metric(2, 2, "total_energy", "Total Energy")

    # Row 3: Phase dynamics
    ax = plot_metric(3, 0, "kuramoto_r", "Kuramoto r (Global)")
    plot_metric(3, 1, "c_in_crystal", "C Nodes in Crystals")
    plot_metric(3, 2, "c_total", "C Total")

    # Row 4: KPI summary
    ax_kpi = fig.add_subplot(gs[4, :])
    ax_kpi.axis("off")

    header = f"{'Metric':<25} " + " ".join(f"{n:>12}" for n in loggers.keys())
    lines = [header, "-" * (25 + 13 * len(loggers))]

    kpi_show = [
        ("peak_C", "Peak C"),
        ("total_synthesis", "Total Synthesis"),
        ("quiet_synthesis", "Quiet Synthesis"),
        ("total_autocatalysis", "Total Autocat"),
        ("quiet_autocatalysis", "Quiet Autocat"),
        ("total_decay", "Total Decay"),
        ("mean_enrichment", "Mean Enrichment"),
        ("c_lifetime_mean", "C Lifetime Mean"),
        ("c_lifetime_max", "C Lifetime Max"),
        ("link_half_life", "Link Half-Life"),
    ]
    for kk, kn in kpi_show:
        vals = [str(kpis_all.get(n, {}).get(kk, "?")) for n in loggers.keys()]
        lines.append(f"{kn:<25} " + " ".join(f"{v:>12}" for v in vals))

    ax_kpi.text(0.02, 0.95, "\n".join(lines), transform=ax_kpi.transAxes,
                fontsize=9, va="top", fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="lightyellow",
                          edgecolor="gray", alpha=0.8))

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {save_path}")


def main():
    print("=" * 70)
    print("  ESDE Genesis v0.5 — Artificial Chemistry")
    print("  'Do crystals become chemical factories?'")
    print("=" * 70)
    print(f"  beta={BETA}  node_decay={NODE_DECAY}  K_sync=0.1")
    print(f"  Chem: S_thr=0.3  E_thr=0.3  P_thr=0.7  p_seed=0.1")
    print(f"  Execution: Flow→Phase→Chemistry→Resonance→Decay→Exclusion")
    print()

    loggers = {}
    kpis_all = {}

    conditions = [
        ("Full",      True,  True,  True),
        ("NoPhase",   False, True,  True),
        ("NoLink",    True,  False, True),
        ("NoAutocat", True,  True,  False),
    ]

    for name, gp, gl, ra in conditions:
        sep = "=" * 70
        print(f"\n{sep}")
        tag = []
        if not gp: tag.append("phase gate OFF")
        if not gl: tag.append("link gate OFF")
        if not ra: tag.append("autocatalysis OFF")
        print(f"  {name}: {', '.join(tag) if tag else 'all gates ON, all rules ON'}")
        print(sep)

        pp, cp = make_params(gate_phase=gp, gate_link=gl, rule_autocat=ra)
        lgr, kpis = run_condition(name, pp, cp)
        loggers[name] = lgr
        kpis_all[name] = kpis

    # Plot
    print(f"\n{'='*70}")
    print("  Generating Plots...")
    print(f"{'='*70}")
    plot_results(loggers, kpis_all, "genesis_v05_chemistry.png")

    # Export
    for name, lgr in loggers.items():
        lgr.export_json(f"genesis_v05_log_{name.lower()}.json")

    # Results table
    full = kpis_all["Full"]
    noph = kpis_all["NoPhase"]
    nolk = kpis_all["NoLink"]
    noac = kpis_all["NoAutocat"]

    print(f"""
{'='*70}
  GENESIS v0.5 RESULTS — Artificial Chemistry
{'='*70}

  +---------------------------+--------+--------+--------+--------+
  |                           |  Full  |NoPhase | NoLink |NoAutoc |
  +---------------------------+--------+--------+--------+--------+
  | Peak C                    | {full.get('peak_C',0):>5}  | {noph.get('peak_C',0):>5}  | {nolk.get('peak_C',0):>5}  | {noac.get('peak_C',0):>5}  |
  | Total Synthesis           | {full.get('total_synthesis',0):>5}  | {noph.get('total_synthesis',0):>5}  | {nolk.get('total_synthesis',0):>5}  | {noac.get('total_synthesis',0):>5}  |
  | Quiet Synthesis           | {full.get('quiet_synthesis',0):>5}  | {noph.get('quiet_synthesis',0):>5}  | {nolk.get('quiet_synthesis',0):>5}  | {noac.get('quiet_synthesis',0):>5}  |
  | Total Autocatalysis       | {full.get('total_autocatalysis',0):>5}  | {noph.get('total_autocatalysis',0):>5}  | {nolk.get('total_autocatalysis',0):>5}  | {noac.get('total_autocatalysis',0):>5}  |
  | Quiet Autocatalysis       | {full.get('quiet_autocatalysis',0):>5}  | {noph.get('quiet_autocatalysis',0):>5}  | {nolk.get('quiet_autocatalysis',0):>5}  | {noac.get('quiet_autocatalysis',0):>5}  |
  | Mean Enrichment           | {full.get('mean_enrichment',0):>5.2f}  | {noph.get('mean_enrichment',0):>5.2f}  | {nolk.get('mean_enrichment',0):>5.2f}  | {noac.get('mean_enrichment',0):>5.2f}  |
  | C Lifetime Mean           | {full.get('c_lifetime_mean',0):>5.0f}  | {noph.get('c_lifetime_mean',0):>5.0f}  | {nolk.get('c_lifetime_mean',0):>5.0f}  | {noac.get('c_lifetime_mean',0):>5.0f}  |
  | C Lifetime Max            | {full.get('c_lifetime_max',0):>5}  | {noph.get('c_lifetime_max',0):>5}  | {nolk.get('c_lifetime_max',0):>5}  | {noac.get('c_lifetime_max',0):>5}  |
  | Link Half-Life            | {str(full.get('link_half_life','?')):>5}  | {str(noph.get('link_half_life','?')):>5}  | {str(nolk.get('link_half_life','?')):>5}  | {str(noac.get('link_half_life','?')):>5}  |
  +---------------------------+--------+--------+--------+--------+
""")

    # Verdict
    full_en = full.get("mean_enrichment", 0)
    noph_en = noph.get("mean_enrichment", 0)
    nolk_en = nolk.get("mean_enrichment", 0)

    print("  INTERPRETATION:")
    if full_en > 1.2 and full_en > noph_en:
        print(f"""
  >>> CRYSTALS ARE CHEMICAL FACTORIES <<<

  Full v0.5: C enrichment = {full_en:.2f} (>{1.0}).
  Compound C preferentially forms/survives INSIDE resonant crystals.

  NoPhase: enrichment = {noph_en:.2f}
    → Phase coherence gate matters: {'YES' if full_en > noph_en * 1.3 else 'weak effect'}
  NoLink: enrichment = {nolk_en:.2f}
    → Link gate matters: {'YES' if full_en > nolk_en * 1.3 else 'weak effect'}

  The topology (v0.3) + oscillation (v0.4) + chemistry (v0.5) stack works.
  Crystals provide the stable, synchronized environment for reactions.
""")
    elif full_en > 1.0:
        print(f"""
  WEAK ENRICHMENT (>{full_en:.2f})
  C concentrates slightly inside crystals but effect may not be robust.
  Consider: lower thresholds, longer runs, or stronger phase coupling.
""")
    else:
        print(f"""
  NO ENRICHMENT ({full_en:.2f})
  C does not preferentially form inside crystals at current parameters.
  Chemistry may be too rare. Check: p_seed, thresholds, phase coherence freq.
""")

    print(f"""  Parameters: p_seed=0.1, S_thr=0.3, E_thr=0.3, P_thr=0.7
  No parameters were tuned to force success.

{'='*70}
  Genesis v0.5 complete.
{'='*70}""")


if __name__ == "__main__":
    main()
