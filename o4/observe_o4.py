"""
ESDE Genesis — Observation Phase O4
======================================
Energy Distribution Inside vs Outside Closed Structures

Pure measurement. No physics changes.

Question: Do closed structures accumulate or retain more energy?

Author: GPT (Audit) | Implemented: Claude
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import time

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005


def measure_energy_distribution(state):
    """Measure energy inside vs outside closed structures."""
    crystal_nodes = state.nodes_in_resonant_loops()
    alive = state.alive_n

    inside = crystal_nodes & alive
    outside = alive - crystal_nodes

    e_inside = [state.E[i] for i in inside] if inside else []
    e_outside = [state.E[i] for i in outside] if outside else []

    return {
        "avg_energy_inside": round(float(np.mean(e_inside)), 6) if e_inside else 0.0,
        "avg_energy_outside": round(float(np.mean(e_outside)), 6) if e_outside else 0.0,
        "max_energy_inside": round(float(max(e_inside)), 6) if e_inside else 0.0,
        "max_energy_outside": round(float(max(e_outside)), 6) if e_outside else 0.0,
        "node_count_inside": len(inside),
        "node_count_outside": len(outside),
    }


def main():
    print("=" * 70)
    print("  ESDE Genesis — Observation Phase O4")
    print("  Energy Distribution: Inside vs Outside Closed Structures")
    print("  No physics changes. Measurement only.")
    print("=" * 70)
    print()

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem = ChemistryEngine(ChemistryParams(enabled=True))
    logger = GenesisLogger()

    o4_log = []
    t0 = time.time()

    # ---- INJECTION ----
    print("  Injection Phase...")
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        m = measure_energy_distribution(state)
        m["step"] = state.step - 1
        m["phase"] = "inject"
        ratio = m["avg_energy_inside"] / m["avg_energy_outside"] if m["avg_energy_outside"] > 1e-9 else 0.0
        m["energy_ratio"] = round(ratio, 4)
        o4_log.append(m)

        if step % 100 == 99:
            print(f"    step {step+1}: "
                  f"in={m['avg_energy_inside']:.4f}({m['node_count_inside']:>3}n) "
                  f"out={m['avg_energy_outside']:.4f}({m['node_count_outside']:>3}n) "
                  f"ratio={m['energy_ratio']:.3f}")

    # ---- QUIET ----
    print("\n  Quiet Phase...")
    for step in range(QUIET_STEPS):
        physics.step_pre_chemistry(state)
        chem.step(state)
        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        m = measure_energy_distribution(state)
        m["step"] = state.step - 1
        m["phase"] = "quiet"
        ratio = m["avg_energy_inside"] / m["avg_energy_outside"] if m["avg_energy_outside"] > 1e-9 else 0.0
        m["energy_ratio"] = round(ratio, 4)
        o4_log.append(m)

        if step % 50 == 49:
            print(f"    quiet {step+1}: "
                  f"in={m['avg_energy_inside']:.4f}({m['node_count_inside']:>3}n) "
                  f"out={m['avg_energy_outside']:.4f}({m['node_count_outside']:>3}n) "
                  f"ratio={m['energy_ratio']:.3f}")

    # ============================================================
    # ANALYSIS
    # ============================================================

    inject_data = [e for e in o4_log if e["phase"] == "inject"]
    quiet_data = [e for e in o4_log if e["phase"] == "quiet"]

    def summarize(data, label):
        valid = [e for e in data if e["node_count_inside"] > 0 and e["node_count_outside"] > 0]
        if not valid:
            return {"phase": label, "avg_inside": 0, "avg_outside": 0,
                    "ratio_mean": 0, "ratio_median": 0,
                    "max_inside": 0, "max_outside": 0, "n_samples": 0}
        return {
            "phase": label,
            "avg_inside": round(np.mean([e["avg_energy_inside"] for e in valid]), 5),
            "avg_outside": round(np.mean([e["avg_energy_outside"] for e in valid]), 5),
            "ratio_mean": round(np.mean([e["energy_ratio"] for e in valid]), 4),
            "ratio_median": round(np.median([e["energy_ratio"] for e in valid]), 4),
            "max_inside": round(np.mean([e["max_energy_inside"] for e in valid]), 5),
            "max_outside": round(np.mean([e["max_energy_outside"] for e in valid]), 5),
            "n_samples": len(valid),
        }

    s_inj = summarize(inject_data, "inject")
    s_qui = summarize(quiet_data, "quiet")

    # Quiet phase time windows
    windows = [(0, 100), (100, 200), (200, 300), (300, 400)]
    s_windows = []
    for ws, we in windows:
        subset = quiet_data[ws:we]
        s_windows.append(summarize(subset, f"quiet_{ws}-{we}"))

    # ============================================================
    # OUTPUT
    # ============================================================

    print(f"\n{'='*70}")
    print(f"  O4 RESULTS — Energy Distribution")
    print(f"{'='*70}")

    print(f"\n  {'Phase':<16} {'Avg In':>10} {'Avg Out':>10} {'Ratio':>8} "
          f"{'Max In':>10} {'Max Out':>10} {'Samples':>8}")
    print(f"  {'-'*74}")
    for s in [s_inj, s_qui] + s_windows:
        print(f"  {s['phase']:<16} {s['avg_inside']:>10.5f} {s['avg_outside']:>10.5f} "
              f"{s['ratio_mean']:>8.4f} {s['max_inside']:>10.5f} {s['max_outside']:>10.5f} "
              f"{s['n_samples']:>8}")

    # Ratio evolution in quiet phase (10-step averages)
    print(f"\n  Quiet Phase Ratio Evolution (10-step bins):")
    for i in range(0, len(quiet_data), 20):
        chunk = quiet_data[i:i+20]
        valid = [e for e in chunk if e["node_count_inside"] > 0 and e["node_count_outside"] > 0]
        if valid:
            r = np.mean([e["energy_ratio"] for e in valid])
            ni = int(np.mean([e["node_count_inside"] for e in valid]))
            no = int(np.mean([e["node_count_outside"] for e in valid]))
            print(f"    step {quiet_data[i]['step']:>4}-{chunk[-1]['step']:>4}: "
                  f"ratio={r:.4f}  inside_n={ni:>3}  outside_n={no:>3}")

    # JSON
    with open("obs_o4_energy_distribution.json", "w") as f:
        json.dump(o4_log, f, indent=2)
    print(f"\n  Log: obs_o4_energy_distribution.json")

    # ============================================================
    # PLOT
    # ============================================================

    fig, axes = plt.subplots(3, 2, figsize=(18, 14))
    fig.suptitle("ESDE Genesis — O4: Energy Inside vs Outside Closed Structures",
                 fontsize=14, fontweight="bold", y=0.99)

    steps = [e["step"] for e in o4_log]
    ei = [e["avg_energy_inside"] for e in o4_log]
    eo = [e["avg_energy_outside"] for e in o4_log]
    ratios = [e["energy_ratio"] for e in o4_log]
    ni = [e["node_count_inside"] for e in o4_log]
    no = [e["node_count_outside"] for e in o4_log]
    mi = [e["max_energy_inside"] for e in o4_log]
    mo = [e["max_energy_outside"] for e in o4_log]

    # 1. Avg energy inside vs outside
    ax = axes[0][0]
    ax.plot(steps, ei, label="inside closed", color="#2ecc71", linewidth=1.5)
    ax.plot(steps, eo, label="outside closed", color="#e74c3c", linewidth=1.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Average Energy: Inside vs Outside", fontsize=10)
    ax.set_ylabel("Avg Energy")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 2. Energy ratio
    ax = axes[0][1]
    ax.plot(steps, ratios, color="#3498db", linewidth=1.2)
    ax.axhline(y=1.0, color="red", linestyle=":", alpha=0.5, label="ratio=1.0")
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Energy Ratio (inside / outside)", fontsize=10)
    ax.set_ylabel("Ratio")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 3. Node counts
    ax = axes[1][0]
    ax.plot(steps, ni, label="inside", color="#2ecc71", linewidth=1.5)
    ax.plot(steps, no, label="outside", color="#e74c3c", linewidth=1.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Node Counts: Inside vs Outside", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 4. Max energy inside vs outside
    ax = axes[1][1]
    ax.plot(steps, mi, label="max inside", color="#2ecc71", linewidth=1.2, alpha=0.7)
    ax.plot(steps, mo, label="max outside", color="#e74c3c", linewidth=1.2, alpha=0.7)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Max Energy: Inside vs Outside", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 5. Quiet phase zoom: ratio
    ax = axes[2][0]
    q_steps = [e["step"] for e in quiet_data]
    q_ratios = [e["energy_ratio"] for e in quiet_data]
    q_valid = [(s, r) for s, r, e in zip(q_steps, q_ratios, quiet_data)
               if e["node_count_inside"] > 0 and e["node_count_outside"] > 0]
    if q_valid:
        qs, qr = zip(*q_valid)
        ax.plot(qs, qr, color="#3498db", linewidth=1.2, alpha=0.7)
        # Rolling average
        if len(qr) > 20:
            roll = np.convolve(qr, np.ones(20)/20, mode='valid')
            ax.plot(list(qs)[10:10+len(roll)], roll,
                    color="#e67e22", linewidth=2.0, label="20-step avg")
        ax.axhline(y=1.0, color="red", linestyle=":", alpha=0.5)
    ax.set_title("Quiet Phase: Energy Ratio (zoom)", fontsize=10)
    ax.set_ylabel("Ratio (in/out)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 6. Quiet phase zoom: avg energies
    ax = axes[2][1]
    q_ei = [e["avg_energy_inside"] for e in quiet_data]
    q_eo = [e["avg_energy_outside"] for e in quiet_data]
    ax.plot(q_steps, q_ei, label="inside", color="#2ecc71", linewidth=1.5)
    ax.plot(q_steps, q_eo, label="outside", color="#e74c3c", linewidth=1.5)
    ax.set_title("Quiet Phase: Avg Energy (zoom)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("obs_o4_energy_distribution.png", dpi=150, bbox_inches="tight")
    print(f"  Plot: obs_o4_energy_distribution.png")

    # ============================================================
    # PATTERN SUMMARY
    # ============================================================

    print(f"""
{'='*70}
  O4 OBSERVED PATTERNS (no interpretation)
{'='*70}

  Injection Phase:
    Avg energy inside:  {s_inj['avg_inside']:.5f}
    Avg energy outside: {s_inj['avg_outside']:.5f}
    Mean ratio:         {s_inj['ratio_mean']:.4f}

  Quiet Phase:
    Avg energy inside:  {s_qui['avg_inside']:.5f}
    Avg energy outside: {s_qui['avg_outside']:.5f}
    Mean ratio:         {s_qui['ratio_mean']:.4f}

  Elapsed: {time.time()-t0:.1f}s | Seed: {SEED}

{'='*70}
  O4 observation complete. No interpretation applied.
{'='*70}
""")


if __name__ == "__main__":
    main()
