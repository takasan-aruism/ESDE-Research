"""
ESDE Genesis v0.3 — GenesisState
==================================
State container: Nodes (E_i), Links (S_ij), Resonance cache (R_ij).

Designed by: Gemini (Architect)
Audited by: GPT
Implemented by: Claude
"""

import numpy as np
from collections import defaultdict
from typing import Dict, Tuple, Set, List, Optional


class GenesisState:
    """
    Holds the complete state of the physical sphere.
    
    Attributes:
        E:       dict[int, float]     — node energies
        S:       dict[(i,j), float]   — link strengths (canonical key: i < j)
        R:       dict[(i,j), float]   — resonance factors (cached)
        alive_n: set[int]             — alive node IDs
        alive_l: set[(i,j)]           — alive link keys
        birth:   dict[(i,j), int]     — link birth steps
    """

    EXTINCTION = 0.01

    def __init__(self, n_nodes: int, c_max: float = 1.0, seed: int = 42):
        self.n_nodes = n_nodes
        self.c_max = c_max
        self.step = 0
        self.rng = np.random.RandomState(seed)

        # Node energy
        self.E: Dict[int, float] = {i: 0.0 for i in range(n_nodes)}
        self.alive_n: Set[int] = set()

        # Link strength
        self.S: Dict[Tuple[int, int], float] = {}
        self.alive_l: Set[Tuple[int, int]] = set()
        self.birth: Dict[Tuple[int, int], int] = {}

        # Resonance cache (updated every N steps)
        self.R: Dict[Tuple[int, int], float] = {}

        # Neighbor cache
        self._nbr: Dict[int, List[int]] = defaultdict(list)
        self._nbr_dirty = True

    # ---- Neighbor Cache ----

    def _rebuild_nbr(self):
        self._nbr = defaultdict(list)
        for (i, j) in self.alive_l:
            self._nbr[i].append(j)
            self._nbr[j].append(i)
        self._nbr_dirty = False

    def neighbors(self, nid: int) -> List[int]:
        if self._nbr_dirty:
            self._rebuild_nbr()
        return self._nbr.get(nid, [])

    # ---- Link Operations ----

    @staticmethod
    def key(i: int, j: int) -> Tuple[int, int]:
        return (min(i, j), max(i, j))

    def add_link(self, i: int, j: int, strength: float) -> bool:
        """Add or strengthen a link. Returns True if new link created."""
        k = self.key(i, j)
        self._nbr_dirty = True
        if k in self.alive_l:
            self.S[k] = min(1.0, self.S[k] + strength)
            return False
        self.S[k] = min(1.0, strength)
        self.R[k] = 0.0
        self.alive_l.add(k)
        self.birth[k] = self.step
        return True

    def kill_link(self, k: Tuple[int, int]):
        if k in self.alive_l:
            self.alive_l.discard(k)
            self.S[k] = 0.0
            self.R.pop(k, None)
            self._nbr_dirty = True

    def link_strength_sum(self, nid: int) -> float:
        t = 0.0
        for k in self.alive_l:
            if k[0] == nid or k[1] == nid:
                t += self.S[k]
        return t

    # ---- Extinction ----

    def enforce_extinction(self):
        changed = False
        # Nodes
        self.alive_n.clear()
        for i in range(self.n_nodes):
            if self.E[i] < self.EXTINCTION:
                self.E[i] = 0.0
            else:
                self.alive_n.add(i)
        # Links
        dead = []
        for k in list(self.alive_l):
            if self.S[k] < self.EXTINCTION:
                dead.append(k)
        for k in dead:
            self.kill_link(k)
            changed = True
        if changed:
            self._nbr_dirty = True

    # ---- Topology Queries ----

    def connected_components(self) -> List[Set[int]]:
        visited = set()
        comps = []
        for s in self.alive_n:
            if s in visited:
                continue
            q = [s]
            c = set()
            while q:
                cur = q.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                c.add(cur)
                for nbr in self.neighbors(cur):
                    if nbr in self.alive_n and nbr not in visited:
                        q.append(nbr)
            if c:
                comps.append(c)
        return comps

    # ---- Cycle Detection (DFS depth-limited) ----

    def find_all_cycles(self, max_length: int = 5) -> Dict[int, List[list]]:
        """
        Find all cycles of length 3..max_length.
        Returns: {length: [list of cycles]} where each cycle is a list of node IDs.
        
        Uses per-link BFS approach: for each alive link (i,j),
        find paths from j back to i (avoiding direct edge) of length up to max_length-1.
        Deduplicate by canonical form.
        """
        all_cycles = {k: set() for k in range(3, max_length + 1)}

        for (li, lj) in self.alive_l:
            # BFS from lj, find paths back to li
            cur = {lj: [[lj]]}  # node -> list of paths to reach it

            for depth in range(1, max_length):
                nxt = defaultdict(list)
                for node, paths in cur.items():
                    for nbr in self.neighbors(node):
                        # Skip direct edge at depth 1
                        if depth == 1 and node == lj and nbr == li:
                            continue
                        if nbr == lj:
                            continue
                        for p in paths:
                            if nbr not in p:  # no revisiting
                                nxt[nbr].append(p + [nbr])

                clen = depth + 1
                if li in nxt and clen in all_cycles:
                    for path in nxt[li]:
                        cycle = [li] + path
                        canonical = tuple(self._canonical_cycle(cycle))
                        all_cycles[clen].add(canonical)

                cur = dict(nxt)

        return {k: [list(c) for c in v] for k, v in all_cycles.items()}

    @staticmethod
    def _canonical_cycle(cycle: list) -> list:
        """Canonical form: rotate so min element is first, then pick smaller direction."""
        n = len(cycle)
        min_idx = cycle.index(min(cycle))
        rotated = cycle[min_idx:] + cycle[:min_idx]
        reversed_r = [rotated[0]] + rotated[1:][::-1]
        return min(rotated, reversed_r)

    def find_link_resonance(self, max_length: int = 5,
                            weights: Dict[int, float] = None) -> Dict[Tuple[int, int], float]:
        """
        Compute R_ij for all alive links based on cycle membership.
        
        For each cycle found, every link in that cycle gets += weight(k).
        Returns dict of {link_key: resonance_score}.
        """
        if weights is None:
            weights = {3: 1.0, 4: 0.5, 5: 0.25}

        R_new = {k: 0.0 for k in self.alive_l}

        cycles = self.find_all_cycles(max_length)

        for length, cycle_list in cycles.items():
            w = weights.get(length, 0.0)
            if w == 0.0:
                continue
            for cycle in cycle_list:
                # Extract all edges in this cycle
                for idx in range(len(cycle)):
                    ni = cycle[idx]
                    nj = cycle[(idx + 1) % len(cycle)]
                    k = self.key(ni, nj)
                    if k in R_new:
                        R_new[k] += w

        return R_new

    # ---- Snapshots ----

    def snapshot(self) -> dict:
        return {
            "step": self.step,
            "n_alive_nodes": len(self.alive_n),
            "n_alive_links": len(self.alive_l),
            "total_energy": round(sum(self.E[i] for i in self.alive_n), 4),
            "resonant_mass": round(
                sum(self.S[k] for k in self.alive_l if self.R.get(k, 0) > 0), 4),
        }
