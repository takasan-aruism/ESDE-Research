"""
ESDE Genesis v0.4 — Local Synchronization Test
=================================================
Measure Kuramoto order parameter INSIDE each detected cycle cluster.
No physics changes. Logging only.

Question: Do nodes in closed loops synchronize their phases locally,
even if the global Kuramoto r is low?

If r_cluster > 0.7 → local heartbeat exists.

Target: Claude | Instruction source: Gemini
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from collections import defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42; BETA = 1.0
NODE_DECAY = 0.005  # slow decay to keep energy alive


def local_kuramoto(state, node_ids):
    """Kuramoto r for a subset of nodes."""
    alive = [n for n in node_ids if n in state.alive_n]
    if len(alive) < 2:
        return 0.0
    phases = state.theta[alive]
    z = np.mean(np.exp(1j * phases))
    return float(np.abs(z))


def avg_energy(state, node_ids):
    alive = [n for n in node_ids if n in state.alive_n]
    if not alive:
        return 0.0
    return float(np.mean([state.E[n] for n in alive]))


def analyze_cycle_sync(state, cycles_by_length):
    """
    For each detected cycle, compute local Kuramoto r and avg energy.
    Returns list of dicts.
    """
    records = []
    cid = 0
    for length, cycle_list in cycles_by_length.items():
        for cycle in cycle_list:
            nodes = list(cycle)
            r = local_kuramoto(state, nodes)
            e = avg_energy(state, nodes)
            records.append({
                "cluster_id": cid,
                "size": len(nodes),
                "loop_type": length,
                "r_cluster": round(r, 4),
                "avg_energy": round(e, 4),
            })
            cid += 1
    return records


def main():
    print("=" * 70)
    print("  Genesis v0.4 — Local Synchronization Test")
    print("  'Do closed loops have local heartbeats?'")
    print("=" * 70)
    print(f"  node_decay={NODE_DECAY}  beta={BETA}  K_sync=0.1  gamma=1.0")
    print(f"  Threshold: r_cluster > 0.7 = local heartbeat")
    print()

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    params = PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0)
    physics = GenesisPhysics(params)
    logger = GenesisLogger()

    # Storage for local sync data
    sync_log = []  # (step, records)
    high_sync_events = []  # r_cluster > 0.7

    # ---- Injection Phase ----
    print("  Injection Phase...")
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            physics.inject(state)
        cd = physics.step(state)
        if cd is not None:
            logger.observe_loops(cd)

            # Analyze local sync at resonance update steps
            cycles = state.find_all_cycles(5)
            records = analyze_cycle_sync(state, cycles)
            sync_log.append({"step": state.step, "records": records})

            high = [r for r in records if r["r_cluster"] > 0.7]
            if high:
                high_sync_events.append({"step": state.step, "phase": "inject",
                                          "count": len(high), "records": high})

        logger.observe(state)

        if step % 100 == 99:
            r = logger.log[-1]
            n_high = sum(1 for e in high_sync_events if e["step"] > state.step - 100)
            print(f"    step {step+1}: L={r['active_links']:>3} "
                  f"r_global={r['kuramoto_r']:.3f} "
                  f"high_sync_events(last100)={n_high}")

    # ---- Quiet Phase ----
    print("\n  Quiet Phase...")
    quiet_start = state.step

    for step in range(QUIET_STEPS):
        cd = physics.step(state)
        if cd is not None:
            logger.observe_loops(cd)

            cycles = state.find_all_cycles(5)
            records = analyze_cycle_sync(state, cycles)
            sync_log.append({"step": state.step, "records": records})

            high = [r for r in records if r["r_cluster"] > 0.7]
            if high:
                high_sync_events.append({"step": state.step, "phase": "quiet",
                                          "count": len(high), "records": high})

        logger.observe(state)

        if step % 50 == 49:
            r = logger.log[-1]
            n_high = sum(1 for e in high_sync_events
                        if e["step"] > state.step - 50 and e["phase"] == "quiet")
            print(f"    quiet {step+1}: L={r['active_links']:>3} "
                  f"osc={r['active_oscillators']:>3} "
                  f"r_global={r['kuramoto_r']:.3f} "
                  f"high_sync(last50)={n_high}")

    # ============================================================
    # ANALYSIS
    # ============================================================

    print(f"\n{'='*70}")
    print(f"  ANALYSIS")
    print(f"{'='*70}")

    # Count high-sync events by phase
    inject_high = [e for e in high_sync_events if e["phase"] == "inject"]
    quiet_high = [e for e in high_sync_events if e["phase"] == "quiet"]

    print(f"\n  Total resonance updates: {len(sync_log)}")
    print(f"  High sync events (r>0.7): {len(high_sync_events)}")
    print(f"    During injection: {len(inject_high)}")
    print(f"    During quiet:     {len(quiet_high)}")

    # Breakdown by loop type
    all_high_records = []
    for e in high_sync_events:
        for r in e["records"]:
            r["step"] = e["step"]
            r["phase"] = e["phase"]
            all_high_records.append(r)

    if all_high_records:
        print(f"\n  High-sync clusters breakdown:")
        for lt in [3, 4, 5]:
            subset = [r for r in all_high_records if r["loop_type"] == lt]
            if subset:
                rs = [r["r_cluster"] for r in subset]
                es = [r["avg_energy"] for r in subset]
                print(f"    {lt}-loops: {len(subset)} events, "
                      f"r_mean={np.mean(rs):.3f} r_max={max(rs):.3f} "
                      f"e_mean={np.mean(es):.3f}")

        # Quiet-phase specifics
        quiet_records = [r for r in all_high_records if r["phase"] == "quiet"]
        if quiet_records:
            print(f"\n  QUIET PHASE high-sync clusters: {len(quiet_records)}")
            for lt in [3, 4, 5]:
                sub = [r for r in quiet_records if r["loop_type"] == lt]
                if sub:
                    rs = [r["r_cluster"] for r in sub]
                    es = [r["avg_energy"] for r in sub]
                    print(f"    {lt}-loops: {len(sub)} events, "
                          f"r_mean={np.mean(rs):.3f} "
                          f"e_mean={np.mean(es):.3f}")

            # Latest quiet high-sync event
            latest = max(quiet_records, key=lambda r: r["step"])
            print(f"\n  Latest quiet high-sync: step={latest['step']} "
                  f"loop={latest['loop_type']} r={latest['r_cluster']} "
                  f"e={latest['avg_energy']}")
    else:
        print("\n  NO high-sync events detected.")

    # ============================================================
    # Distribution of r_cluster over time
    # ============================================================

    # Collect all r values per update step
    steps_all = []
    r_means_3 = []
    r_means_4 = []
    r_means_5 = []
    r_maxes = []
    high_counts = []

    for entry in sync_log:
        s = entry["step"]
        recs = entry["records"]
        steps_all.append(s)

        for lt, store in [(3, r_means_3), (4, r_means_4), (5, r_means_5)]:
            sub = [r["r_cluster"] for r in recs if r["loop_type"] == lt]
            store.append(np.mean(sub) if sub else 0.0)

        all_r = [r["r_cluster"] for r in recs]
        r_maxes.append(max(all_r) if all_r else 0.0)
        high_counts.append(sum(1 for r in all_r if r > 0.7))

    # ============================================================
    # PLOT
    # ============================================================

    fig, axes = plt.subplots(3, 2, figsize=(18, 14))
    fig.suptitle("Genesis v0.4 — Local Synchronization Test\n"
                 "'Do closed loops have local heartbeats?'",
                 fontsize=14, fontweight="bold", y=0.99)

    # 1. Mean local r by loop type
    ax = axes[0][0]
    ax.plot(steps_all, r_means_3, label="3-loops", color="#e74c3c", linewidth=1.2)
    ax.plot(steps_all, r_means_4, label="4-loops", color="#3498db", linewidth=1.2)
    ax.plot(steps_all, r_means_5, label="5-loops", color="#9b59b6", linewidth=1.2)
    ax.axhline(y=0.7, color="red", linestyle=":", alpha=0.5, label="threshold")
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Mean Local Kuramoto r by Loop Type", fontsize=10)
    ax.set_ylabel("r_cluster (mean)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 2. Max local r over time
    ax = axes[0][1]
    ax.plot(steps_all, r_maxes, color="#2ecc71", linewidth=1.2)
    ax.axhline(y=0.7, color="red", linestyle=":", alpha=0.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Max Local r (any cluster)", fontsize=10)
    ax.set_ylabel("r_cluster (max)")
    ax.grid(True, alpha=0.15)

    # 3. High-sync cluster count
    ax = axes[1][0]
    ax.bar(steps_all, high_counts, width=8, color="#e67e22", alpha=0.7)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Clusters with r > 0.7 (per update)", fontsize=10)
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.15)

    # 4. Global vs local comparison
    ax = axes[1][1]
    ts = logger.get_timeseries()
    ax.plot(ts["step"], ts["kuramoto_r"], label="Global r", color="#e74c3c",
            linewidth=1.5, alpha=0.7)
    # Overlay max local r (interpolated to all steps)
    ax.scatter(steps_all, r_maxes, s=10, color="#2ecc71", label="Max Local r",
               alpha=0.7, zorder=5)
    ax.axhline(y=0.7, color="red", linestyle=":", alpha=0.5)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Global vs Local Synchronization", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 5. Standard metrics
    ax = axes[2][0]
    ax.plot(ts["step"], ts["active_links"], label="Links", color="#2ecc71", linewidth=1.5)
    ax.plot(ts["step"], ts["active_oscillators"], label="Oscillators", color="#f39c12", linewidth=1.2)
    ax.axvline(x=INJECTION_STEPS, color="gray", linestyle="--", alpha=0.4)
    ax.set_title("Links & Oscillators", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.15)

    # 6. Summary text
    ax = axes[2][1]
    ax.axis("off")
    total_h = len(high_sync_events)
    quiet_h = len(quiet_high)
    verdict = "LOCAL HEARTBEAT DETECTED" if quiet_h > 5 else "NO LOCAL HEARTBEAT"

    txt = f"""Local Synchronization Test Results
{'='*40}

Total resonance updates: {len(sync_log)}
High-sync events (r>0.7): {total_h}
  Injection phase: {len(inject_high)}
  Quiet phase:     {quiet_h}

Parameters:
  node_decay={NODE_DECAY}  beta={BETA}
  K_sync=0.1  gamma=1.0  alpha=0.0

VERDICT: {verdict}
"""
    ax.text(0.05, 0.95, txt, transform=ax.transAxes,
            fontsize=11, va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow",
                      edgecolor="gray", alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("genesis_v04_local_sync.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: genesis_v04_local_sync.png")

    # ============================================================
    # VERDICT
    # ============================================================

    print(f"\n{'='*70}")
    print(f"  VERDICT")
    print(f"{'='*70}")

    if quiet_h > 5:
        print(f"""
  >>> LOCAL HEARTBEAT DETECTED <<<

  {quiet_h} high-sync events (r>0.7) during quiet phase.
  Closed loops synchronize their phases locally even when
  global synchronization is low (r_global ~ 0.08).

  The crystals DO have heartbeats — they're just LOCAL,
  not global. This is more physical: local oscillator clusters
  with independent rhythms, not a single global pulse.
""")
    elif total_h > 0:
        print(f"""
  LOCAL SYNC EXISTS DURING INJECTION BUT FADES IN QUIET PHASE

  {len(inject_high)} high-sync events during injection, {quiet_h} during quiet.
  Loops synchronize when driven but lose coherence without input.
  Phase coupling (K_sync) may need to be stronger.
""")
    else:
        print(f"""
  NO LOCAL SYNCHRONIZATION DETECTED

  Even within closed loops, phases remain incoherent.
  Current K_sync={params.K_sync} may be too weak,
  or natural frequency spread is too wide.
""")

    print(f"{'='*70}")
    print(f"  Local sync test complete.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
