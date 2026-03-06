"""
ESDE Genesis v1.8 — Boundary Intrusion Operator
==================================================
Micro-perturbation at island boundaries.
Gradually shifts strong-link connectivity from inside to outside islands.

Option 1 (Edge Swap):
  For boundary nodes, probabilistically transfer small strength
  from an intra-island link to a cross-boundary link.
  Auto-growth and Exclusion decide what becomes strong.

One knob: intrusion_rate (per boundary node per step).
Does NOT create strong links directly.
"""

import numpy as np
from collections import defaultdict
from genesis_state import GenesisState

S_STRONG = 0.30  # island definition threshold


def find_islands_sets(state):
    """Connected components on strong-edge subgraph, size>=3. Returns list of frozenset."""
    adj = defaultdict(set)
    for k in state.alive_l:
        if state.S[k] >= S_STRONG:
            adj[k[0]].add(k[1]); adj[k[1]].add(k[0])
    visited = set(); islands = []
    for s in adj:
        if s in visited: continue
        q = [s]; comp = set()
        while q:
            n = q.pop()
            if n in visited: continue
            visited.add(n); comp.add(n)
            for nb in adj[n]:
                if nb not in visited: q.append(nb)
        if len(comp) >= 3:
            islands.append(frozenset(comp))
    return islands


class BoundaryIntrusionOperator:
    """Perturbs island boundaries by swapping small amounts of link strength."""

    def __init__(self, intrusion_rate=0.001, delta_swap=0.02):
        self.intrusion_rate = intrusion_rate
        self.delta_swap = delta_swap
        self.swap_events = 0

    def step(self, state):
        """Apply boundary intrusion. Returns count of swap events."""
        if self.intrusion_rate <= 0:
            self.swap_events = 0
            return 0

        islands = find_islands_sets(state)
        if not islands:
            self.swap_events = 0
            return 0

        # Build node→island mapping
        node_island = {}
        for idx, isl in enumerate(islands):
            for n in isl:
                node_island[n] = idx

        # Find boundary nodes: island nodes with at least one non-island neighbor
        boundary_nodes = []
        for n, isl_idx in node_island.items():
            if n not in state.alive_n:
                continue
            for nb in state.neighbors(n):
                if nb in state.alive_n and node_island.get(nb, -1) != isl_idx:
                    boundary_nodes.append(n)
                    break

        if not boundary_nodes:
            self.swap_events = 0
            return 0

        self.swap_events = 0
        alive_list = list(state.alive_n)

        for bn in boundary_nodes:
            if state.rng.random() > self.intrusion_rate:
                continue

            bn_isl = node_island.get(bn, -1)
            if bn_isl < 0:
                continue

            # Find a strong intra-island neighbor to weaken
            intra_neighbors = []
            for nb in state.neighbors(bn):
                if node_island.get(nb, -1) == bn_isl:
                    k = state.key(bn, nb)
                    if k in state.alive_l and state.S[k] >= S_STRONG:
                        intra_neighbors.append((nb, k))

            if not intra_neighbors:
                continue

            # Find an outside node to strengthen connection to
            outside_candidates = []
            for nb in state.neighbors(bn):
                if nb in state.alive_n and node_island.get(nb, -1) != bn_isl:
                    k = state.key(bn, nb)
                    if k in state.alive_l:
                        outside_candidates.append((nb, k))

            # Also consider latent candidates (not yet linked)
            if not outside_candidates and alive_list:
                # Sample a few random outside nodes
                for _ in range(3):
                    j = alive_list[state.rng.randint(len(alive_list))]
                    if j != bn and node_island.get(j, -1) != bn_isl:
                        k = state.key(bn, j)
                        if k not in state.alive_l:
                            l_ij = state.get_latent(bn, j)
                            if l_ij > self.delta_swap:
                                # Create weak link from latent
                                state.add_link(bn, j, self.delta_swap)
                                state.set_latent(bn, j, l_ij - self.delta_swap)
                                outside_candidates.append((j, k))
                                break

            if not outside_candidates:
                continue

            # Pick random intra neighbor and outside target
            intra_nb, intra_k = intra_neighbors[state.rng.randint(len(intra_neighbors))]
            out_nb, out_k = outside_candidates[state.rng.randint(len(outside_candidates))]

            # Swap: weaken intra, strengthen outside
            actual = min(self.delta_swap, state.S[intra_k] - 0.01)  # don't kill intra link
            if actual <= 0:
                continue

            state.S[intra_k] -= actual
            if out_k in state.alive_l:
                state.S[out_k] = min(1.0, state.S[out_k] + actual)
            # Note: if out_k was just created above, it already has strength

            self.swap_events += 1

        return self.swap_events
