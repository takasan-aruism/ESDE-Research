"""
ESDE Genesis v0.4 — GenesisState
==================================
"Artificial Wave Physics"

New in v0.4:
  - theta[i]: phase angle (0..2*pi)
  - omega[i]: natural frequency (randomly initialized)
  - Phase state persists alongside energy and link topology

Designed by: Gemini | Audited by: GPT | Implemented by: Claude
"""

import numpy as np
from collections import defaultdict
from typing import Dict, Tuple, Set, List


class GenesisState:
    EXTINCTION = 0.01

    def __init__(self, n_nodes: int, c_max: float = 1.0, seed: int = 42):
        self.n_nodes = n_nodes
        self.c_max = c_max
        self.step = 0
        self.rng = np.random.RandomState(seed)

        # Node state
        self.E: Dict[int, float] = {i: 0.0 for i in range(n_nodes)}
        self.alive_n: Set[int] = set()

        # v0.4: Phase dynamics
        self.theta: np.ndarray = self.rng.uniform(0, 2 * np.pi, n_nodes)
        self.omega: np.ndarray = self.rng.uniform(0.05, 0.3, n_nodes)  # natural freq

        # Link state
        self.S: Dict[Tuple[int, int], float] = {}
        self.alive_l: Set[Tuple[int, int]] = set()
        self.birth: Dict[Tuple[int, int], int] = {}
        self.R: Dict[Tuple[int, int], float] = {}

        # Neighbor cache
        self._nbr: Dict[int, List[int]] = defaultdict(list)
        self._nbr_dirty = True

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

    @staticmethod
    def key(i: int, j: int) -> Tuple[int, int]:
        return (min(i, j), max(i, j))

    def add_link(self, i: int, j: int, strength: float) -> bool:
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

    def enforce_extinction(self):
        self.alive_n.clear()
        for i in range(self.n_nodes):
            if self.E[i] < self.EXTINCTION:
                self.E[i] = 0.0
            else:
                self.alive_n.add(i)
        dead = [k for k in list(self.alive_l) if self.S[k] < self.EXTINCTION]
        for k in dead:
            self.kill_link(k)

    # ---- Topology ----

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

    # ---- Cycle Detection (from v0.3) ----

    def find_all_cycles(self, max_length: int = 5) -> Dict[int, list]:
        all_cycles = {k: set() for k in range(3, max_length + 1)}
        for (li, lj) in self.alive_l:
            cur = {lj: [[lj]]}
            for depth in range(1, max_length):
                nxt = defaultdict(list)
                for node, paths in cur.items():
                    for nbr in self.neighbors(node):
                        if depth == 1 and node == lj and nbr == li:
                            continue
                        if nbr == lj:
                            continue
                        for p in paths:
                            if nbr not in p:
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
    def _canonical_cycle(cycle):
        n = len(cycle)
        mi = cycle.index(min(cycle))
        rot = cycle[mi:] + cycle[:mi]
        rev = [rot[0]] + rot[1:][::-1]
        return min(rot, rev)

    # ---- Phase Metrics ----

    def kuramoto_order_parameter(self) -> float:
        """
        r = |(1/N) * Σ exp(i * theta_j)| for alive nodes.
        r ~ 0: incoherent, r ~ 1: synchronized.
        """
        alive = list(self.alive_n)
        if len(alive) < 2:
            return 0.0
        phases = self.theta[alive]
        z = np.mean(np.exp(1j * phases))
        return float(np.abs(z))

    def active_oscillators(self, energy_thresh=0.1) -> int:
        """Nodes with energy > threshold (can oscillate)."""
        return sum(1 for i in self.alive_n if self.E[i] > energy_thresh)
