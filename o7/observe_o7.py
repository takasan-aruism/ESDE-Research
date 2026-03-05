"""
ESDE Genesis — Observation Phase O7
======================================
Phase Boundary Analysis

Why do transformation cycles exist in the graph but never execute at node level?
O6 found: C→Dust→A→C cycle exists structurally but no node completes it.
O7 observes the injection→quiet boundary to understand why.

No physics changes. Observation only.

Author: GPT (Audit) | Implemented: Claude
"""

import numpy as np
import csv
import time
from collections import Counter, defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005

STATE_NAMES = {0: "Dust", 1: "A", 2: "B", 3: "C"}


def node_degree(state, nid):
    d = 0
    for k in state.alive_l:
        if k[0] == nid or k[1] == nid:
            d += 1
    return d


def main():
    print("=" * 70)
    print("  ESDE Genesis — Observation Phase O7")
    print("  Phase Boundary Analysis")
    print("  No physics changes. Observation only.")
    print("=" * 70)
    print()

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem = ChemistryEngine(ChemistryParams(enabled=True))
    logger = GenesisLogger()

    t0 = time.time()

    # ---- INJECTION ----
    print("  Running Injection Phase...")
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

    # ============================================================
    # 1. BOUNDARY SNAPSHOT (injection→quiet transition)
    # ============================================================
    print(f"\n  Taking boundary snapshot at step {state.step}...")

    boundary_rows = []
    for i in range(N_NODES):
        if i in state.alive_n:
            boundary_rows.append({
                "step": state.step,
                "node_id": i,
                "state": STATE_NAMES[state.Z[i]],
                "energy": round(state.E[i], 6),
                "phase_theta": round(state.theta[i], 6),
                "degree": node_degree(state, i),
            })

    with open("O7_boundary_snapshot.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["step", "node_id", "state", "energy",
                                           "phase_theta", "degree"])
        w.writeheader()
        w.writerows(boundary_rows)
    print(f"    O7_boundary_snapshot.csv: {len(boundary_rows)} nodes")

    # ============================================================
    # 4. BOUNDARY ENERGY BY STATE
    # ============================================================
    state_energy = defaultdict(list)
    for row in boundary_rows:
        state_energy[row["state"]].append(row["energy"])

    with open("O7_boundary_energy.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["state", "avg_energy", "min_energy", "max_energy", "node_count"])
        for s in ["Dust", "A", "B", "C"]:
            vals = state_energy.get(s, [])
            if vals:
                w.writerow([s, round(np.mean(vals), 6), round(min(vals), 6),
                            round(max(vals), 6), len(vals)])
            else:
                w.writerow([s, 0, 0, 0, 0])

    print(f"\n  Boundary Energy by State:")
    print(f"    {'State':<6} {'Count':>6} {'Avg E':>10} {'Min E':>10} {'Max E':>10}")
    for s in ["Dust", "A", "B", "C"]:
        vals = state_energy.get(s, [])
        if vals:
            print(f"    {s:<6} {len(vals):>6} {np.mean(vals):>10.5f} "
                  f"{min(vals):>10.5f} {max(vals):>10.5f}")
        else:
            print(f"    {s:<6} {0:>6} {'—':>10} {'—':>10} {'—':>10}")

    # State counts at boundary
    bc = Counter(row["state"] for row in boundary_rows)
    print(f"\n  State distribution at boundary: {dict(bc)}")

    # Degree by state
    state_degree = defaultdict(list)
    for row in boundary_rows:
        state_degree[row["state"]].append(row["degree"])
    print(f"\n  Avg degree by state at boundary:")
    for s in ["Dust", "A", "B", "C"]:
        vals = state_degree.get(s, [])
        if vals:
            print(f"    {s}: avg_degree={np.mean(vals):.2f} "
                  f"max={max(vals)} nodes={len(vals)}")

    # ============================================================
    # 2. EARLY QUIET MONITORING (first 100 steps)
    # ============================================================
    print(f"\n  Monitoring first 100 quiet steps...")

    quiet_window_rows = []
    quiet_transforms = []

    for step in range(QUIET_STEPS):
        # Snapshot before chemistry
        pre_z = {i: int(state.Z[i]) for i in state.alive_n}

        physics.step_pre_chemistry(state)
        chem.step(state)

        # Detect transitions
        step_transforms = []
        for i, old_z in pre_z.items():
            new_z = int(state.Z[i])
            if new_z != old_z:
                step_transforms.append({
                    "step": state.step,
                    "node_id": i,
                    "source": STATE_NAMES[old_z],
                    "target": STATE_NAMES[new_z],
                    "energy": round(state.E[i], 6),
                    "degree": node_degree(state, i),
                })

        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        if step < 100:
            sc = Counter(int(state.Z[i]) for i in state.alive_n)
            quiet_window_rows.append({
                "step": state.step,
                "n_Dust": sc.get(0, 0),
                "n_A": sc.get(1, 0),
                "n_B": sc.get(2, 0),
                "n_C": sc.get(3, 0),
                "n_transforms": len(step_transforms),
                "transform_types": "|".join(f"{t['source']}->{t['target']}" for t in step_transforms) if step_transforms else "",
            })

        quiet_transforms.extend(step_transforms)

        if step % 50 == 49 and step < 200:
            sc = Counter(int(state.Z[i]) for i in state.alive_n)
            n_rx = sum(1 for t in quiet_transforms if t["step"] > state.step - 50)
            print(f"    quiet {step+1}: "
                  f"D={sc.get(0,0)} A={sc.get(1,0)} B={sc.get(2,0)} C={sc.get(3,0)} "
                  f"rxns(50)={n_rx}")

    with open("O7_quiet_window.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["step", "n_Dust", "n_A", "n_B", "n_C",
                                           "n_transforms", "transform_types"])
        w.writeheader()
        w.writerows(quiet_window_rows)
    print(f"    O7_quiet_window.csv: {len(quiet_window_rows)} rows")

    # ============================================================
    # 3. CYCLE OPPORTUNITY DETECTION
    # ============================================================
    print(f"\n  Cycle Opportunity Analysis...")

    # C→Dust events in first 100 quiet steps
    early_c_to_dust = [t for t in quiet_transforms
                       if t["source"] == "C" and t["target"] == "Dust"
                       and t["step"] <= INJECTION_STEPS + 100]

    # All C→Dust events
    all_c_to_dust = [t for t in quiet_transforms
                     if t["source"] == "C" and t["target"] == "Dust"]

    opp_lines = []
    opp_lines.append("O7 — Cycle Opportunity Detection")
    opp_lines.append("=" * 50)
    opp_lines.append("")
    opp_lines.append(f"Total C→Dust events (all quiet): {len(all_c_to_dust)}")
    opp_lines.append(f"C→Dust events (first 100 quiet steps): {len(early_c_to_dust)}")

    if early_c_to_dust:
        energies = [t["energy"] for t in early_c_to_dust]
        degrees = [t["degree"] for t in early_c_to_dust]
        opp_lines.append(f"")
        opp_lines.append(f"First 100 steps — nodes that decayed C→Dust:")
        opp_lines.append(f"  avg energy after decay:  {np.mean(energies):.6f}")
        opp_lines.append(f"  min energy after decay:  {min(energies):.6f}")
        opp_lines.append(f"  max energy after decay:  {max(energies):.6f}")
        opp_lines.append(f"  avg degree after decay:  {np.mean(degrees):.2f}")
        opp_lines.append(f"  max degree after decay:  {max(degrees)}")
        opp_lines.append(f"  min degree after decay:  {min(degrees)}")
    else:
        opp_lines.append(f"  No C→Dust events in first 100 quiet steps.")

    if all_c_to_dust:
        energies_all = [t["energy"] for t in all_c_to_dust]
        degrees_all = [t["degree"] for t in all_c_to_dust]
        steps_all = [t["step"] for t in all_c_to_dust]
        opp_lines.append(f"")
        opp_lines.append(f"All quiet C→Dust events:")
        opp_lines.append(f"  avg energy after decay:  {np.mean(energies_all):.6f}")
        opp_lines.append(f"  avg degree after decay:  {np.mean(degrees_all):.2f}")
        opp_lines.append(f"  first event at step:     {min(steps_all)}")
        opp_lines.append(f"  last event at step:      {max(steps_all)}")
        opp_lines.append(f"  step range:              {min(steps_all)}-{max(steps_all)}")

        # Could these nodes theoretically continue the cycle?
        opp_lines.append(f"")
        opp_lines.append(f"Cycle continuation conditions:")
        opp_lines.append(f"  To continue C→Dust→A, node needs:")
        opp_lines.append(f"    1. Seeding event (Dust→A) — currently injection-only")
        opp_lines.append(f"    2. Energy above threshold — E_thr=0.3")
        opp_lines.append(f"    3. Strong link — S_thr=0.3")
        opp_lines.append(f"    4. Phase coherence — P_thr=0.7")
        opp_lines.append(f"")
        above_e_thr = sum(1 for e in energies_all if e > 0.3)
        has_links = sum(1 for d in degrees_all if d > 0)
        opp_lines.append(f"  Nodes with energy > 0.3 after decay: "
                         f"{above_e_thr}/{len(all_c_to_dust)}")
        opp_lines.append(f"  Nodes with degree > 0 after decay:   "
                         f"{has_links}/{len(all_c_to_dust)}")
        opp_lines.append(f"")

        # The C→Dust threshold is E < 0.2
        # So by definition, energy after C→Dust is < 0.2
        opp_lines.append(f"  NOTE: C→Dust triggers when E < 0.2 (E_low).")
        opp_lines.append(f"  Therefore ALL decayed nodes have E < 0.2,")
        opp_lines.append(f"  which is BELOW E_thr=0.3 for reactions.")
        opp_lines.append(f"  Even if Dust→A seeding occurred, the node")
        opp_lines.append(f"  could not react (A+B→C) without energy injection.")

    opp_text = "\n".join(opp_lines)
    with open("O7_cycle_opportunity.txt", "w") as f:
        f.write(opp_text)
    print(opp_text)

    # ============================================================
    # SUMMARY
    # ============================================================

    elapsed = time.time() - t0
    print(f"""
{'='*70}
  O7 OBSERVED PATTERNS (no interpretation)
{'='*70}

  Boundary State Distribution:
    {dict(bc)}

  Boundary Avg Energy by State:""")
    for s in ["Dust", "A", "B", "C"]:
        vals = state_energy.get(s, [])
        if vals:
            print(f"    {s}: {np.mean(vals):.5f} ({len(vals)} nodes)")

    print(f"""
  Quiet Phase Transitions (first 100 steps):
    C→Dust: {len(early_c_to_dust)}
    Other:  {sum(1 for t in quiet_transforms if t['step'] <= INJECTION_STEPS + 100) - len(early_c_to_dust)}

  Cycle Blocking Factor:
    C→Dust requires E < 0.2
    A+B→C requires E > 0.3
    Gap: 0.1 energy units with no external source during quiet

  Elapsed: {elapsed:.1f}s | Seed: {SEED}

{'='*70}
  O7 observation complete. No interpretation applied.
{'='*70}
""")


if __name__ == "__main__":
    main()
