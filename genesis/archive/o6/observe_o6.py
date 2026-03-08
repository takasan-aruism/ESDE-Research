"""
ESDE Genesis — Observation Phase O6
======================================
Transformation Cycle Detection

Pure observation. No physics changes.

1. Record every transformation event (source_state → target_state)
2. Build directed transition graph
3. Detect cycles (length 2, 3, 4)
4. Report strongly connected components

Author: GPT (Audit) | Implemented: Claude
"""

import numpy as np
import json
import time
from collections import defaultdict, Counter

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 400
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005

STATE_NAMES = {0: "Dust", 1: "A", 2: "B", 3: "C"}


class TransitionTracker:
    """Track per-node state transitions and build directed graph."""

    MAX_STATES = 10_000
    MAX_EDGES = 50_000

    def __init__(self):
        self.edge_counts = Counter()      # (src, tgt) -> count
        self.events = []                  # list of (step, src, tgt)
        self.node_history = defaultdict(list)  # node_id -> [(step, state)]
        self.states_seen = set()

    def snapshot_states(self, state, step):
        """Record current Z for all alive nodes (called before chemistry)."""
        self._pre_z = {}
        for i in state.alive_n:
            self._pre_z[i] = int(state.Z[i])

    def record_transitions(self, state, step):
        """Compare post-chemistry Z to pre-chemistry snapshot."""
        for i, old_z in self._pre_z.items():
            new_z = int(state.Z[i])
            if new_z != old_z:
                self._add(step, old_z, new_z, i)

        # Also catch nodes that were alive before but now dead (shouldn't happen
        # in current physics, but safe)
        for i in state.alive_n:
            if i not in self._pre_z:
                # newly alive — seeded from injection
                new_z = int(state.Z[i])
                if new_z != 0:
                    self._add(step, 0, new_z, i)

    def _add(self, step, src, tgt, node_id):
        src_name = STATE_NAMES.get(src, str(src))
        tgt_name = STATE_NAMES.get(tgt, str(tgt))

        self.states_seen.add(src_name)
        self.states_seen.add(tgt_name)

        if len(self.states_seen) <= self.MAX_STATES and \
           len(self.edge_counts) <= self.MAX_EDGES:
            self.edge_counts[(src_name, tgt_name)] += 1

        self.events.append((step, src_name, tgt_name))
        self.node_history[node_id].append((step, tgt_name))

    def get_graph(self):
        """Return adjacency list of the transition graph."""
        adj = defaultdict(set)
        for (src, tgt) in self.edge_counts:
            adj[src].add(tgt)
        return dict(adj)

    def find_cycles(self, max_length=4):
        """Find all simple cycles up to max_length in the transition graph."""
        adj = self.get_graph()
        nodes = list(self.states_seen)
        cycles = []

        def dfs(start, current, path, depth):
            if depth > max_length:
                return
            for nbr in adj.get(current, []):
                if nbr == start and len(path) >= 2:
                    cycle = path + [nbr]
                    canonical = self._canonical_cycle(cycle[:-1])
                    if canonical not in seen:
                        seen.add(canonical)
                        cycles.append(cycle)
                elif nbr not in set(path) and depth < max_length:
                    dfs(start, nbr, path + [nbr], depth + 1)

        seen = set()
        for node in nodes:
            dfs(node, node, [node], 1)

        return cycles

    @staticmethod
    def _canonical_cycle(cycle):
        n = len(cycle)
        rotations = [tuple(cycle[i:] + cycle[:i]) for i in range(n)]
        return min(rotations)

    def find_sccs(self):
        """Tarjan's SCC algorithm on the transition graph."""
        adj = self.get_graph()
        nodes = list(self.states_seen)

        index_counter = [0]
        stack = []
        on_stack = set()
        indices = {}
        lowlinks = {}
        sccs = []

        def strongconnect(v):
            indices[v] = index_counter[0]
            lowlinks[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack.add(v)

            for w in adj.get(v, []):
                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[w])

            if lowlinks[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == v:
                        break
                sccs.append(scc)

        for v in nodes:
            if v not in indices:
                strongconnect(v)

        return sccs

    def node_lifecycle_cycles(self):
        """
        Track per-node state sequences to detect individual lifecycle cycles.
        E.g., a single node going Dust→A→C→Dust is a lifecycle cycle.
        """
        lifecycle_cycles = Counter()
        for node_id, history in self.node_history.items():
            states = [s for _, s in history]
            # Look for returns to previously visited states
            for i in range(len(states)):
                for j in range(i + 1, len(states)):
                    if states[j] == states[i]:
                        cycle = tuple(states[i:j+1])
                        lifecycle_cycles[cycle] += 1
                        break  # only first return
        return lifecycle_cycles


def main():
    print("=" * 70)
    print("  ESDE Genesis — Observation Phase O6")
    print("  Transformation Cycle Detection")
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
    tracker = TransitionTracker()

    t0 = time.time()

    # ---- INJECTION ----
    print("  Injection Phase...")
    for step in range(INJECTION_STEPS):
        # Snapshot BEFORE any changes (seeding + chemistry)
        tracker.snapshot_states(state, state.step)

        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])

        # Record seeding transitions (Dust→A, Dust→B)
        tracker.record_transitions(state, state.step)

        physics.step_pre_chemistry(state)

        # Snapshot again before chemistry
        tracker.snapshot_states(state, state.step)
        chem.step(state)
        # Record chemistry transitions
        tracker.record_transitions(state, state.step)

        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        if step % 100 == 99:
            print(f"    step {step+1}: transitions so far = {len(tracker.events)}")

    # ---- QUIET ----
    print("\n  Quiet Phase...")
    for step in range(QUIET_STEPS):
        physics.step_pre_chemistry(state)

        tracker.snapshot_states(state, state.step)
        chem.step(state)
        tracker.record_transitions(state, state.step)

        cd = physics.step_post_chemistry(state)
        if cd:
            logger.observe_loops(cd)
        logger.observe(state)

        if step % 100 == 99:
            print(f"    quiet {step+1}: transitions so far = {len(tracker.events)}")

    elapsed = time.time() - t0

    # ============================================================
    # ANALYSIS
    # ============================================================

    print(f"\n{'='*70}")
    print(f"  O6 ANALYSIS")
    print(f"{'='*70}")

    total_events = len(tracker.events)
    unique_states = len(tracker.states_seen)
    unique_edges = len(tracker.edge_counts)

    print(f"\n  Total transformations: {total_events}")
    print(f"  Unique states: {unique_states} — {sorted(tracker.states_seen)}")
    print(f"  Unique edges:  {unique_edges}")

    # Top transitions
    print(f"\n  Top Transitions:")
    for (src, tgt), count in tracker.edge_counts.most_common(20):
        print(f"    {src:>5} → {tgt:<5} : {count}")

    # Phase breakdown
    inject_events = [e for e in tracker.events if e[0] < INJECTION_STEPS]
    quiet_events = [e for e in tracker.events if e[0] >= INJECTION_STEPS]

    inject_counts = Counter((s, t) for _, s, t in inject_events)
    quiet_counts = Counter((s, t) for _, s, t in quiet_events)

    print(f"\n  Injection Phase ({len(inject_events)} events):")
    for (s, t), c in inject_counts.most_common(10):
        print(f"    {s:>5} → {t:<5} : {c}")

    print(f"\n  Quiet Phase ({len(quiet_events)} events):")
    for (s, t), c in quiet_counts.most_common(10):
        print(f"    {s:>5} → {t:<5} : {c}")

    # Cycles in transition graph
    cycles = tracker.find_cycles(max_length=4)
    print(f"\n  Cycle Detection:")
    print(f"  Total cycles found: {len(cycles)}")

    by_length = defaultdict(list)
    for c in cycles:
        by_length[len(c) - 1].append(c)

    for length in [2, 3, 4]:
        cl = by_length.get(length, [])
        print(f"    Length {length}: {len(cl)}")
        for c in cl:
            arrow = " → ".join(c)
            # Check if this cycle has real counts
            edges_in_cycle = [(c[i], c[i+1]) for i in range(len(c)-1)]
            min_count = min(tracker.edge_counts.get(e, 0) for e in edges_in_cycle)
            print(f"      {arrow}  (min edge count: {min_count})")

    if not cycles:
        print(f"    cycles = none")

    # SCCs
    sccs = tracker.find_sccs()
    print(f"\n  Strongly Connected Components:")
    print(f"  Total SCCs: {len(sccs)}")
    for i, scc in enumerate(sorted(sccs, key=len, reverse=True)):
        nodes_str = ", ".join(scc[:10])
        print(f"    SCC {i+1}: size={len(scc)} — [{nodes_str}]")

    # Node lifecycle cycles
    lc = tracker.node_lifecycle_cycles()
    print(f"\n  Node Lifecycle Cycles (individual node journeys):")
    print(f"  Unique lifecycle patterns: {len(lc)}")
    for pattern, count in lc.most_common(15):
        arrow = " → ".join(pattern)
        print(f"    {arrow} : {count} nodes")

    # ============================================================
    # OUTPUT FILES
    # ============================================================

    # O6_summary.txt
    summary = []
    summary.append("ESDE Genesis — O6 Transformation Cycle Detection")
    summary.append(f"Seed: {SEED} | Elapsed: {elapsed:.1f}s")
    summary.append(f"")
    summary.append(f"Total transformations: {total_events}")
    summary.append(f"  Injection: {len(inject_events)}")
    summary.append(f"  Quiet:     {len(quiet_events)}")
    summary.append(f"Unique states: {unique_states} — {sorted(tracker.states_seen)}")
    summary.append(f"Unique edges:  {unique_edges}")
    summary.append(f"")
    summary.append(f"Graph cycles: {len(cycles)}")
    for length in [2, 3, 4]:
        cl = by_length.get(length, [])
        for c in cl:
            summary.append(f"  len={length}: {' → '.join(c)}")
    if not cycles:
        summary.append(f"  none")
    summary.append(f"")
    summary.append(f"SCCs: {len(sccs)}")
    for i, scc in enumerate(sorted(sccs, key=len, reverse=True)):
        summary.append(f"  SCC {i+1}: size={len(scc)} — [{', '.join(scc[:10])}]")
    summary.append(f"")
    summary.append(f"Node lifecycle patterns: {len(lc)}")
    for pattern, count in lc.most_common(10):
        summary.append(f"  {' → '.join(pattern)} : {count}")

    with open("O6_summary.txt", "w") as f:
        f.write("\n".join(summary))
    print(f"\n  Output: O6_summary.txt")

    # O6_transition_counts.csv
    with open("O6_transition_counts.csv", "w") as f:
        f.write("source,target,count,phase\n")
        for (s, t), c in tracker.edge_counts.most_common():
            ic = inject_counts.get((s, t), 0)
            qc = quiet_counts.get((s, t), 0)
            f.write(f"{s},{t},{c},inject={ic}|quiet={qc}\n")
    print(f"  Output: O6_transition_counts.csv")

    # O6_cycles.txt
    with open("O6_cycles.txt", "w") as f:
        f.write("Directed Graph Cycles\n")
        f.write(f"Total: {len(cycles)}\n\n")
        for length in [2, 3, 4]:
            cl = by_length.get(length, [])
            f.write(f"Length {length}: {len(cl)}\n")
            for c in cl:
                edges_in_cycle = [(c[i], c[i+1]) for i in range(len(c)-1)]
                counts = [tracker.edge_counts.get(e, 0) for e in edges_in_cycle]
                f.write(f"  {' → '.join(c)}  counts={counts}\n")
        f.write(f"\nNode Lifecycle Cycles\n")
        for pattern, count in lc.most_common():
            f.write(f"  {' → '.join(pattern)} : {count}\n")
    print(f"  Output: O6_cycles.txt")

    # O6_scc_report.txt
    with open("O6_scc_report.txt", "w") as f:
        f.write("Strongly Connected Components\n\n")
        for i, scc in enumerate(sorted(sccs, key=len, reverse=True)):
            f.write(f"SCC {i+1}: size={len(scc)}\n")
            f.write(f"  nodes: {', '.join(scc[:10])}\n")
            # Internal edges
            scc_set = set(scc)
            internal = [(s, t, c) for (s, t), c in tracker.edge_counts.items()
                        if s in scc_set and t in scc_set]
            for s, t, c in internal:
                f.write(f"  {s} → {t} : {c}\n")
            f.write(f"\n")
    print(f"  Output: O6_scc_report.txt")

    # ============================================================
    # PATTERN SUMMARY
    # ============================================================

    print(f"""
{'='*70}
  O6 OBSERVED PATTERNS (no interpretation)
{'='*70}

  Total transformations: {total_events}
    Injection: {len(inject_events)}
    Quiet:     {len(quiet_events)}

  Transition graph:
    States: {sorted(tracker.states_seen)}
    Edges:  {unique_edges}

  Graph cycles: {len(cycles)}
{chr(10).join('    ' + ' → '.join(c) for c in cycles) if cycles else '    none'}

  SCCs with size > 1: {sum(1 for s in sccs if len(s) > 1)}

  Node lifecycle patterns: {len(lc)}
    Most common: {' → '.join(lc.most_common(1)[0][0]) + ' : ' + str(lc.most_common(1)[0][1]) if lc else 'none'}

  Elapsed: {elapsed:.1f}s | Seed: {SEED}

{'='*70}
  O6 observation complete. No interpretation applied.
{'='*70}
""")


if __name__ == "__main__":
    main()
