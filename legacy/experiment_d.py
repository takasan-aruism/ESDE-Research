"""
ESDE Genesis v0.1 — Experiment D
==================================
The Critical Experiment: Triangle Bonus -> Closed Path Bonus

D1: bonus_mode="triangle"     (original rule)
D2: bonus_mode="cycle"        (3+4+5 cycles, weighted)
D3: bonus_mode="cycle"        (4+5 ONLY — triangles EXCLUDED!)

gamma = 2.0 for all (reduced from 5.0 per audit).
No parameter tuning. Failure is valid.

Author: Claude (Implementation)
Issued by: GPT (Audit)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Dict, Tuple, Optional
import json
import time

from universe import Universe
from physics_engine import PhysicsEngine, PhysicsParams
from observer import Observer

N_NODES = 200
INJECTION_STEPS = 300
QUIET_STEPS = 400
INJECT_INTERVAL = 3
SEED = 42
GAMMA = 2.0


def make_params(exclusion, struct_adv, bonus_mode="triangle",
                gamma=GAMMA, cycle_weights=None, max_cycle=5):
    p = PhysicsParams(
        exclusion_enabled=exclusion,
        structural_advantage_enabled=struct_adv,
        node_decay_rate=0.02,
        link_decay_rate=0.08,
        gamma=gamma,
        connectivity_shelter=0.5,
        flow_coefficient=0.1,
        inject_amount=0.6,
        inject_prob=0.15,
        inject_pair_radius=8,
        inject_link_strength=0.3,
        bonus_mode=bonus_mode,
        max_cycle_length=max_cycle,
    )
    if cycle_weights is not None:
        p.cycle_weights = cycle_weights
    return p


def run_condition(name, params, verbose=True):
    universe = Universe(n_nodes=N_NODES, c_max=0.8, seed=SEED)
    engine = PhysicsEngine(params)
    observer = Observer()
    t0 = time.time()

    for step in range(INJECTION_STEPS):
        evt = ""
        if step % INJECT_INTERVAL == 0:
            tgts = engine.inject(universe)
            evt = f"inject_{len(tgts) if tgts else 0}"
        engine.step(universe)
        observer.observe(universe, event=evt)

        if verbose and step % 100 == 99:
            s = observer.global_log[-1]["stats"]
            elapsed = time.time() - t0
            print(f"      {name} step {step+1}: L={s['link_count']} T={s['triangle_count']} ({elapsed:.0f}s)")

    observer.take_snapshot(universe, label="end_injection")
    cycle_stats = universe.total_cycle_count(5) if params.bonus_mode == "cycle" else {}

    quiet_start = universe.step_count
    for step in range(QUIET_STEPS):
        engine.step(universe)
        observer.observe(universe, event="quiet")

        if verbose and step % 100 == 99:
            s = observer.global_log[-1]["stats"]
            elapsed = time.time() - t0
            print(f"      {name} quiet {step+1}: L={s['link_count']} T={s['triangle_count']} ({elapsed:.0f}s)")

    observer.take_snapshot(universe, label="end_quiet")
    kpis = observer.compute_kpis(quiet_start=quiet_start)
    elapsed = time.time() - t0

    kpis["gamma"] = params.gamma
    kpis["bonus_mode"] = params.bonus_mode
    kpis["seed"] = SEED
    kpis["elapsed_sec"] = round(elapsed, 1)
    if cycle_stats:
        kpis["cycles_at_inject"] = cycle_stats

    if verbose:
        inj_s = observer.global_log[INJECTION_STEPS - 1]["stats"]
        end_s = observer.global_log[-1]["stats"]
        print(f"    {name:40s} "
              f"inj=[L={inj_s['link_count']:>3} T={inj_s['triangle_count']:>3}] "
              f"end=[L={end_s['link_count']:>3} T={end_s['triangle_count']:>3}] "
              f"L_HL={kpis['link_half_life']:>3} T_HL={kpis['triangle_half_life']:>3} "
              f"({elapsed:.1f}s)")

    return observer, kpis


def run_three(label, bonus_mode, gamma=GAMMA, cycle_weights=None, verbose=True):
    if verbose:
        print(f"\n  --- {label} ---")
    results = {}

    p1 = make_params(False, False, bonus_mode="none", gamma=0)
    o1, k1 = run_condition(f"{label}/Control-1(Chaos)", p1, verbose)
    results["Control-1"] = (o1, k1)

    p2 = make_params(True, False, bonus_mode="none", gamma=0)
    o2, k2 = run_condition(f"{label}/Control-2(Rigid)", p2, verbose)
    results["Control-2"] = (o2, k2)

    p3 = make_params(True, True, bonus_mode=bonus_mode,
                     gamma=gamma, cycle_weights=cycle_weights)
    o3, k3 = run_condition(f"{label}/Genesis", p3, verbose)
    results["Genesis"] = (o3, k3)

    return results


def plot_d_comparison(all_results, save_path):
    exps = list(all_results.keys())
    n_exp = len(exps)
    colors = {"Control-1": "#e74c3c", "Control-2": "#f39c12", "Genesis": "#2ecc71"}
    metrics = [("total_energy", "Total Energy"), ("active_links", "Active Links"),
               ("triangle_count", "Triangles"), ("entropy", "Entropy")]

    fig, axes = plt.subplots(n_exp, len(metrics), figsize=(20, 4 * n_exp))
    if n_exp == 1:
        axes = [axes]
    fig.suptitle(f"Experiment D: Triangle vs Closed Path (gamma={GAMMA})",
                 fontsize=14, fontweight="bold", y=0.99)

    for row, en in enumerate(exps):
        res = all_results[en]
        for col, (mk, mt) in enumerate(metrics):
            ax = axes[row][col]
            for cn, (obs, _) in res.items():
                ts = obs.get_timeseries()
                ax.plot(ts["step"], ts[mk], label=cn,
                        color=colors.get(cn, "gray"), linewidth=1.5, alpha=0.85)
            ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
            ax.grid(True, alpha=0.15)
            if row == 0: ax.set_title(mt, fontsize=11, fontweight="bold")
            if col == 0: ax.set_ylabel(en, fontsize=9, fontweight="bold")
            if row == n_exp - 1: ax.set_xlabel("Step", fontsize=9)
            if col == 0 and row == 0: ax.legend(fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot: {save_path}")


def plot_d_kpi_bars(all_results, save_path):
    exps = list(all_results.keys())
    conds = ["Control-1", "Control-2", "Genesis"]
    colors = {"Control-1": "#e74c3c", "Control-2": "#f39c12", "Genesis": "#2ecc71"}
    kpis_list = [("energy_half_life", "Energy Half-Life"),
                 ("link_half_life", "Link Half-Life"),
                 ("triangle_half_life", "Triangle Half-Life")]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f"Experiment D KPI (gamma={GAMMA})", fontsize=14, fontweight="bold")

    for ai, (kk, kt) in enumerate(kpis_list):
        ax = axes[ai]
        x = np.arange(len(exps))
        w = 0.25
        for ci, cn in enumerate(conds):
            vals = [all_results[en][cn][1].get(kk, 0) if cn in all_results[en] else 0
                    for en in exps]
            bars = ax.bar(x + ci * w, vals, w, label=cn, color=colors[cn], alpha=0.85)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                       str(v), ha="center", va="bottom", fontsize=8)
        ax.set_ylabel(kt)
        ax.set_title(kt, fontsize=11)
        ax.set_xticks(x + w)
        ax.set_xticklabels(exps, rotation=20, fontsize=7)
        ax.grid(True, axis="y", alpha=0.2)
        if ai == 0: ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"  Plot: {save_path}")


def main():
    print("=" * 65)
    print("  ESDE Genesis v0.1 — EXPERIMENT D")
    print("  Is it triangles, or closed circuits?")
    print("=" * 65)
    print(f"  gamma={GAMMA} (reduced from 5.0)  nodes={N_NODES}")
    print(f"  D1: triangle   D2: cycle(3+4+5)   D3: cycle(4+5 only)")
    print()

    all_results = {}

    # D1: Triangle only
    print("=" * 65)
    print("  D1: Triangle Bonus (original)")
    print("=" * 65)
    d1 = run_three("D1:triangle", bonus_mode="triangle", gamma=GAMMA)
    all_results["D1:triangle"] = d1

    # D2: All cycles
    print("\n" + "=" * 65)
    print("  D2: Cycle Bonus (3+4+5, weighted: tri=1.0 sq=0.6 pent=0.3)")
    print("=" * 65)
    d2 = run_three("D2:cycle(3+4+5)", bonus_mode="cycle", gamma=GAMMA,
                   cycle_weights={3: 1.0, 4: 0.6, 5: 0.3})
    all_results["D2:cycle(3+4+5)"] = d2

    # D3: Cycles 4+5 ONLY — THE CRITICAL TEST
    print("\n" + "=" * 65)
    print("  D3: Cycle Bonus (4+5 ONLY — TRIANGLES EXCLUDED)")
    print("  >>> THIS IS THE CRITICAL TEST <<<")
    print("=" * 65)
    d3 = run_three("D3:cycle(4+5only)", bonus_mode="cycle", gamma=GAMMA,
                   cycle_weights={3: 0.0, 4: 1.0, 5: 0.6})
    all_results["D3:cycle(4+5only)"] = d3

    # Plots
    print("\n" + "=" * 65)
    print("  Generating Plots...")
    print("=" * 65)
    plot_d_comparison(all_results, "exp_d_timeseries.png")
    plot_d_kpi_bars(all_results, "exp_d_kpi_bars.png")

    # Logs
    for en, res in all_results.items():
        for cn, (obs, kpis) in res.items():
            safe = en.replace(":", "_").replace("(", "").replace(")", "").replace("+", "")
            obs.export_json(f"exp_d_log_{safe}_{cn.lower().replace('-','_')}.json")

    # Report
    d1g = d1["Genesis"][1]
    d2g = d2["Genesis"][1]
    d3g = d3["Genesis"][1]
    ctrl = d1["Control-2"][1]

    print(f"""
{'='*65}
  EXPERIMENT D — RESULTS
{'='*65}

  THE CRITICAL COMPARISON (Genesis only, gamma={GAMMA})
  +--------------------------+--------+--------+--------+
  |                          | L_HL   | T_HL   | E_HL   |
  +--------------------------+--------+--------+--------+
  | Control-2 (no bonus)     | {ctrl['link_half_life']:>5}  | {ctrl['triangle_half_life']:>5}  | {ctrl['energy_half_life']:>5}  |
  | D1: triangle             | {d1g['link_half_life']:>5}  | {d1g['triangle_half_life']:>5}  | {d1g['energy_half_life']:>5}  |
  | D2: cycle(3+4+5)         | {d2g['link_half_life']:>5}  | {d2g['triangle_half_life']:>5}  | {d2g['energy_half_life']:>5}  |
  | D3: cycle(4+5 only)      | {d3g['link_half_life']:>5}  | {d3g['triangle_half_life']:>5}  | {d3g['energy_half_life']:>5}  |
  +--------------------------+--------+--------+--------+
""")

    d3_works = d3g["link_half_life"] > ctrl["link_half_life"]
    d3_strong = d3g["link_half_life"] >= d1g["link_half_life"] * 0.7

    print("  INTERPRETATION:")
    if d3_works:
        if d3_strong:
            print("""
  >>> CLOSED CIRCUITS ARE PHYSICS <<<

  4+5 cycles (without triangles) produce comparable persistence.
  It is NOT triangles specifically — it IS topological closure.
  The diffusion equation requires closed energy paths.

  node = atom | cycle = molecule | cycle cluster = proto-chemistry
""")
        else:
            print("""
  CLOSED CIRCUITS HELP, BUT SHORTER LOOPS ARE STRONGER

  4+5 cycles produce persistence above baseline, but less than triangles.
  Topological closure IS the mechanism, shorter cycles more efficient.
""")
    else:
        print("""
  ONLY TRIANGLES PRODUCE PERSISTENCE (at these parameters)

  4+5 cycles alone do NOT extend link half-life beyond control.
  Either the effect is geometry-specific, or longer cycles are too fragile.
  Further investigation needed with different decay rates.
""")

    print(f"""  No parameters were tuned to force success.
  All outcomes are scientifically valid.

{'='*65}
  Experiment D complete.
{'='*65}""")


if __name__ == "__main__":
    main()
