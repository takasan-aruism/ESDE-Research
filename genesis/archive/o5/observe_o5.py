"""
ESDE Genesis — Observation Phase O5
======================================
Energy Flow Tracking

Pure measurement. No physics changes.

Questions:
- Does energy preferentially move toward closed structures?
- Does energy leave closed structures faster or slower?
- Are there stable flow patterns across links?

Method: Instrument the flow calculation to capture per-node
inflow/outflow, then aggregate by closed structure membership.

Author: GPT (Audit) | Implemented: Claude
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import time
from collections import defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005


def measure_energy_flows(state, params):
    """
    Replicate flow calculation to capture per-node inflow/outflow.
    Does NOT modify state — read-only measurement.
    """
    k = params.flow_coefficient
    gamma = params.gamma
    phase_on = params.phase_enabled

    inflow = defaultdict(float)   # node -> total received
    outflow = defaultdict(float)  # node -> total sent
    link_transfer = {}            # (i,j) -> signed energy transfer

    for (li, lj) in state.alive_l:
        ei = state.E[li]
        ej = state.E[lj]
        s = state.S[(li, lj)]

        if phase_on and gamma > 0:
            dtheta = state.theta[lj] - state.theta[li]
            pf = 0.5 + 0.5 * gamma * np.cos(dtheta)
            pf = max(0.0, min(1.0, pf))
        else:
            pf = 1.0

        # f > 0 means energy flows from j to i (gradient: ej > ei)
        f = k * s * (ej - ei) * pf

        if f > 0:
            # Energy flows j → i
            inflow[li] += f
            outflow[lj] += f
        else:
            # Energy flows i → j (f is negative, flip sign)
            inflow[lj] += (-f)
            outflow[li] += (-f)

        link_transfer[(li, lj)] = round(f, 8)

    return dict(inflow), dict(outflow), link_transfer


def aggregate_flows(state, inflow, outflow):
    """Aggregate by inside/outside closed structures."""
    crystal_nodes = state.nodes_in_resonant_loops()
    alive = state.alive_n
    inside = crystal_nodes & alive
    outside = alive - crystal_nodes

    def avg_or_zero(nodes, d):
        vals = [d.get(n, 0.0) for n in nodes]
        return float(np.mean(vals)) if vals else 0.0

    def total_or_zero(nodes, d):
        return sum(d.get(n, 0.0) for n in nodes)

    ai = avg_or_zero(inside, inflow)
    ao = avg_or_zero(outside, inflow)
    oi = avg_or_zero(inside, outflow)
    oo = avg_or_zero(outside, outflow)
    ni = avg_or_zero(inside, {n: inflow.get(n, 0) - outflow.get(n, 0) for n in range(state.n_nodes)})
    no = avg_or_zero(outside, {n: inflow.get(n, 0) - outflow.get(n, 0) for n in range(state.n_nodes)})

    # Cross-boundary flow: energy moving from outside→inside vs inside→outside
    flow_into_crystal = 0.0
    flow_out_of_crystal = 0.0
    for (li, lj), f in {}: pass  # placeholder — computed below

    return {
        "avg_inflow_inside": round(ai, 7),
        "avg_inflow_outside": round(ao, 7),
        "avg_outflow_inside": round(oi, 7),
        "avg_outflow_outside": round(oo, 7),
        "net_flow_inside": round(ni, 7),
        "net_flow_outside": round(no, 7),
        "total_inflow_inside": round(total_or_zero(inside, inflow), 6),
        "total_outflow_inside": round(total_or_zero(inside, outflow), 6),
        "n_inside": len(inside),
        "n_outside": len(outside),
    }


def measure_boundary_flow(state, link_transfer):
    """Measure energy crossing the boundary between inside/outside."""
    crystal_nodes = state.nodes_in_resonant_loops()
    alive = state.alive_n
    inside = crystal_nodes & alive

    flow_in = 0.0   # net flow INTO crystal from outside
    flow_out = 0.0   # net flow OUT of crystal to outside
    boundary_links = 0

    for (li, lj), f in link_transfer.items():
        i_in = li in inside
        j_in = lj in inside
        if i_in == j_in:
            continue  # both same side
        boundary_links += 1
        # f > 0 means flow j→i
        if f > 0:
            if i_in:  # energy enters crystal
                flow_in += f
            else:      # energy leaves crystal
                flow_out += f
        else:
            if j_in:  # energy enters crystal (negative = i→j, j is inside)
                flow_in += (-f)
            else:
                flow_out += (-f)

    return {
        "boundary_flow_in": round(flow_in, 7),
        "boundary_flow_out": round(flow_out, 7),
        "boundary_net": round(flow_in - flow_out, 7),
        "boundary_links": boundary_links,
    }


def main():
    print("=" * 70)
    print("  ESDE Genesis — Observation Phase O5")
    print("  Energy Flow Tracking")
    print("  No physics changes. Measurement only.")
    print("=" * 70)
    print()

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    phys_params = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0)
    physics = GenesisPhysics(phys_params)
    chem = ChemistryEngine(ChemistryParams(enabled=True))
    logger = GenesisLogger()

    o5_log = []
    t0 = time.time()

    def record_step(state, phase_label):
        inflow, outflow, lt = measure_energy_flows(state, phys_params)
        agg = aggregate_flows(state, inflow, outflow)
        bnd = measure_boundary_flow(state, lt)
        agg.update(bnd)
        agg["step"] = state.step
        agg["phase"] = phase_label
        o5_log.append(agg)
        return agg

    # ---- INJECTION ----
    print("  Injection Phase...")
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])

        # Measure BEFORE physics step (captures current-state flows)
        m = record_step(state, "inject")

        physics.step_pre_chemistry(state)
        chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        if step % 100 == 99:
            print(f"    step {step+1}: "
                  f"net_in={m['net_flow_inside']:+.5f} "
                  f"net_out={m['net_flow_outside']:+.5f} "
                  f"bnd_net={m['boundary_net']:+.5f} "
                  f"({m['n_inside']}in/{m['n_outside']}out)")

    # ---- QUIET ----
    print("\n  Quiet Phase...")
    for step in range(QUIET_STEPS):
        m = record_step(state, "quiet")

        physics.step_pre_chemistry(state)
        chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        if step % 50 == 49:
            print(f"    quiet {step+1}: "
                  f"net_in={m['net_flow_inside']:+.5f} "
                  f"net_out={m['net_flow_outside']:+.5f} "
                  f"bnd_net={m['boundary_net']:+.5f} "
                  f"({m['n_inside']}in/{m['n_outside']}out)")

    # ============================================================
    # ANALYSIS
    # ============================================================

    inject_data = [e for e in o5_log if e["phase"] == "inject"]
    quiet_data = [e for e in o5_log if e["phase"] == "quiet"]

    def summarize(data, label):
        valid = [e for e in data if e["n_inside"] > 0 and e["n_outside"] > 0]
        if not valid:
            return {"phase": label}
        return {
            "phase": label,
            "avg_inflow_in": round(np.mean([e["avg_inflow_inside"] for e in valid]), 7),
            "avg_inflow_out": round(np.mean([e["avg_inflow_outside"] for e in valid]), 7),
            "avg_outflow_in": round(np.mean([e["avg_outflow_inside"] for e in valid]), 7),
            "avg_outflow_out": round(np.mean([e["avg_outflow_outside"] for e in valid]), 7),
            "net_flow_in": round(np.mean([e["net_flow_inside"] for e in valid]), 7),
            "net_flow_out": round(np.mean([e["net_flow_outside"] for e in valid]), 7),
            "bnd_flow_in": round(np.mean([e["boundary_flow_in"] for e in valid]), 7),
            "bnd_flow_out": round(np.mean([e["boundary_flow_out"] for e in valid]), 7),
            "bnd_net": round(np.mean([e["boundary_net"] for e in valid]), 7),
            "n_samples": len(valid),
        }

    s_inj = summarize(inject_data, "inject")
    s_qui = summarize(quiet_data, "quiet")

    # Quiet windows
    windows = [(0, 100), (100, 200), (200, 300), (300, 400)]
    s_windows = [summarize(quiet_data[ws:we], f"q{ws}-{we}") for ws, we in windows]

    # ============================================================
    # OUTPUT
    # ============================================================

    print(f"\n{'='*70}")
    print(f"  O5 RESULTS — Energy Flow Tracking")
    print(f"{'='*70}")

    print(f"\n  Per-Node Averages:")
    print(f"  {'Phase':<12} {'Inflow_In':>11} {'Inflow_Out':>11} "
          f"{'Outflow_In':>11} {'Outflow_Out':>12} {'Net_In':>10} {'Net_Out':>10}")
    print(f"  {'-'*78}")
    for s in [s_inj, s_qui] + s_windows:
        if "avg_inflow_in" not in s:
            continue
        print(f"  {s['phase']:<12} {s['avg_inflow_in']:>11.6f} {s['avg_inflow_out']:>11.6f} "
              f"{s['avg_outflow_in']:>11.6f} {s['avg_outflow_out']:>12.6f} "
              f"{s['net_flow_in']:>+10.6f} {s['net_flow_out']:>+10.6f}")

    print(f"\n  Boundary Flow (crossing crystal edge):")
    print(f"  {'Phase':<12} {'Into Crystal':>13} {'Out of Crystal':>15} {'Net':>10} {'Bnd Links':>10}")
    print(f"  {'-'*62}")
    for s in [s_inj, s_qui] + s_windows:
        if "bnd_flow_in" not in s:
            continue
        print(f"  {s['phase']:<12} {s['bnd_flow_in']:>13.6f} {s['bnd_flow_out']:>15.6f} "
              f"{s['bnd_net']:>+10.6f}")

    # JSON
    with open("obs_o5_energy_flow.json", "w") as f:
        json.dump(o5_log, f)
    print(f"\n  Log: obs_o5_energy_flow.json")

    # ============================================================
    # PLOT
    # ============================================================

    fig, axes = plt.subplots(3, 2, figsize=(18, 15))
    fig.suptitle("ESDE Genesis — O5: Energy Flow Tracking\n"
                 "How does energy move through the network?",
                 fontsize=14, fontweight="bold", y=0.99)

    steps = [e["step"] for e in o5_log]

    # 1. Avg inflow: inside vs outside
    ax = axes[0][0]
    ax.plot(steps, [e["avg_inflow_inside"] for e in o5_log],
            label="inflow inside", color="#2ecc71", linewidth=1.2)
    ax.plot(steps, [e["avg_inflow_outside"] for e in o5_log],
            label="inflow outside", color="#e74c3c", linewidth=1.2)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Avg Inflow per Node", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 2. Avg outflow: inside vs outside
    ax = axes[0][1]
    ax.plot(steps, [e["avg_outflow_inside"] for e in o5_log],
            label="outflow inside", color="#2ecc71", linewidth=1.2)
    ax.plot(steps, [e["avg_outflow_outside"] for e in o5_log],
            label="outflow outside", color="#e74c3c", linewidth=1.2)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Avg Outflow per Node", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 3. Net flow: inside vs outside
    ax = axes[1][0]
    ax.plot(steps, [e["net_flow_inside"] for e in o5_log],
            label="net inside", color="#2ecc71", linewidth=1.2)
    ax.plot(steps, [e["net_flow_outside"] for e in o5_log],
            label="net outside", color="#e74c3c", linewidth=1.2)
    ax.axhline(y=0, color="gray", linestyle=":", alpha=0.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Net Flow per Node (inflow - outflow)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 4. Boundary flow
    ax = axes[1][1]
    ax.plot(steps, [e["boundary_flow_in"] for e in o5_log],
            label="into crystal", color="#3498db", linewidth=1.2)
    ax.plot(steps, [e["boundary_flow_out"] for e in o5_log],
            label="out of crystal", color="#e67e22", linewidth=1.2)
    ax.plot(steps, [e["boundary_net"] for e in o5_log],
            label="net boundary", color="#9b59b6", linewidth=1.5, linestyle="--")
    ax.axhline(y=0, color="gray", linestyle=":", alpha=0.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Boundary Flow (crystal edge)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 5. Quiet zoom: net flow
    ax = axes[2][0]
    q = quiet_data
    qs = [e["step"] for e in q]
    valid_q = [e for e in q if e["n_inside"] > 0 and e["n_outside"] > 0]
    if valid_q:
        vqs = [e["step"] for e in valid_q]
        ax.plot(vqs, [e["net_flow_inside"] for e in valid_q],
                label="net inside", color="#2ecc71", linewidth=1.0, alpha=0.5)
        ax.plot(vqs, [e["net_flow_outside"] for e in valid_q],
                label="net outside", color="#e74c3c", linewidth=1.0, alpha=0.5)
        # Rolling avg
        if len(valid_q) > 20:
            ni_arr = np.array([e["net_flow_inside"] for e in valid_q])
            no_arr = np.array([e["net_flow_outside"] for e in valid_q])
            k_size = 20
            ri = np.convolve(ni_arr, np.ones(k_size)/k_size, mode='valid')
            ro = np.convolve(no_arr, np.ones(k_size)/k_size, mode='valid')
            ax.plot(vqs[k_size//2:k_size//2+len(ri)], ri,
                    color="#27ae60", linewidth=2.0, label="inside (20-avg)")
            ax.plot(vqs[k_size//2:k_size//2+len(ro)], ro,
                    color="#c0392b", linewidth=2.0, label="outside (20-avg)")
    ax.axhline(y=0, color="gray", linestyle=":", alpha=0.5)
    ax.set_title("Quiet Phase: Net Flow (zoom + rolling avg)", fontsize=10)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.15)

    # 6. Quiet zoom: boundary net
    ax = axes[2][1]
    if valid_q:
        bnet = [e["boundary_net"] for e in valid_q]
        ax.plot(vqs, bnet, color="#9b59b6", linewidth=1.0, alpha=0.5)
        if len(bnet) > 20:
            rb = np.convolve(np.array(bnet), np.ones(20)/20, mode='valid')
            ax.plot(vqs[10:10+len(rb)], rb,
                    color="#8e44ad", linewidth=2.0, label="20-avg")
    ax.axhline(y=0, color="gray", linestyle=":", alpha=0.5)
    ax.set_title("Quiet Phase: Boundary Net Flow (zoom)", fontsize=10)
    ax.set_ylabel("+ = energy entering crystal")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("obs_o5_energy_flow.png", dpi=150, bbox_inches="tight")
    print(f"  Plot: obs_o5_energy_flow.png")

    # ============================================================
    # PATTERN SUMMARY
    # ============================================================

    print(f"""
{'='*70}
  O5 OBSERVED PATTERNS (no interpretation)
{'='*70}

  Injection Phase:
    Net flow inside:     {s_inj.get('net_flow_in', 0):+.7f} per node
    Net flow outside:    {s_inj.get('net_flow_out', 0):+.7f} per node
    Boundary net:        {s_inj.get('bnd_net', 0):+.7f}

  Quiet Phase:
    Net flow inside:     {s_qui.get('net_flow_in', 0):+.7f} per node
    Net flow outside:    {s_qui.get('net_flow_out', 0):+.7f} per node
    Boundary net:        {s_qui.get('bnd_net', 0):+.7f}

  Elapsed: {time.time()-t0:.1f}s | Seed: {SEED}

{'='*70}
  O5 observation complete. No interpretation applied.
{'='*70}
""")


if __name__ == "__main__":
    main()
