"""
ESDE Genesis v0.1 — Universe Module
=====================================
v0.1: Added general cycle detection (3,4,5) + neighbor cache for performance.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Set, List, Optional
from collections import defaultdict


@dataclass
class Node:
    id: int
    energy: float = 0.0
    c_max: float = 3.0
    alive: bool = True


@dataclass
class Link:
    i: int
    j: int
    strength: float = 0.1
    alive: bool = True
    birth_step: int = 0

    @property
    def key(self):
        return (min(self.i, self.j), max(self.i, self.j))


class Universe:
    EXTINCTION_THRESHOLD = 0.01

    def __init__(self, n_nodes, c_max=3.0, seed=42):
        self.n_nodes = n_nodes
        self.c_max = c_max
        self.step_count = 0
        self.rng = np.random.RandomState(seed)
        self.nodes = {i: Node(id=i, energy=0.0, c_max=c_max) for i in range(n_nodes)}
        self.links: Dict[Tuple[int,int], Link] = {}
        self._nbr_cache: Dict[int, List[int]] = defaultdict(list)
        self._cache_ok = False

    def _invalidate(self):
        self._cache_ok = False

    def _rebuild_cache(self):
        self._nbr_cache = defaultdict(list)
        for (i, j), lk in self.links.items():
            if lk.alive:
                self._nbr_cache[i].append(j)
                self._nbr_cache[j].append(i)
        self._cache_ok = True

    def active_nodes(self):
        return [n for n in self.nodes.values() if n.alive]

    def active_links(self):
        return [l for l in self.links.values() if l.alive]

    def neighbors(self, nid):
        if not self._cache_ok:
            self._rebuild_cache()
        return self._nbr_cache.get(nid, [])

    def node_link_strength_sum(self, nid):
        t = 0.0
        for (i, j), lk in self.links.items():
            if lk.alive and (i == nid or j == nid):
                t += lk.strength
        return t

    # ---- Cycle Detection ----

    def triangle_count_for_link(self, li, lj):
        ni = set(self.neighbors(li))
        nj = set(self.neighbors(lj))
        return len(ni & nj)

    def cycle_count_for_link(self, li, lj, max_length=5):
        """
        Count cycles of length 3..max_length through edge (li,lj).
        BFS from lj avoiding direct (li,lj) edge, count paths to li.
        """
        counts = {k: 0 for k in range(3, max_length + 1)}
        cur = {lj: 1}
        for depth in range(1, max_length):
            nxt = defaultdict(int)
            for node, pc in cur.items():
                for nbr in self.neighbors(node):
                    if depth == 1 and node == lj and nbr == li:
                        continue
                    if nbr == lj:
                        continue
                    nxt[nbr] += pc
            clen = depth + 1
            if li in nxt and clen in counts:
                counts[clen] = nxt[li]
            cur = dict(nxt)
        counts["total"] = sum(counts[k] for k in range(3, max_length + 1))
        return counts

    def total_triangle_count(self):
        tris = set()
        for (i, j), lk in self.links.items():
            if not lk.alive:
                continue
            ni = set(self.neighbors(i))
            nj = set(self.neighbors(j))
            for k in ni & nj:
                tris.add(tuple(sorted([i, j, k])))
        return len(tris)

    def total_cycle_count(self, max_length=5):
        raw = {k: 0 for k in range(3, max_length + 1)}
        for key, lk in self.links.items():
            if not lk.alive:
                continue
            cc = self.cycle_count_for_link(lk.i, lk.j, max_length)
            for k in range(3, max_length + 1):
                raw[k] += cc.get(k, 0)
        unique = {k: raw[k] // k for k in range(3, max_length + 1)}
        unique["total"] = sum(unique[k] for k in range(3, max_length + 1))
        return unique

    # ---- Topology ----

    def connected_components(self):
        alive_ids = {n.id for n in self.active_nodes()}
        visited = set()
        comps = []
        for s in alive_ids:
            if s in visited:
                continue
            q = [s]
            c = set()
            while q:
                cur = q.pop(0)
                if cur in visited:
                    continue
                visited.add(cur)
                c.add(cur)
                for nbr in self.neighbors(cur):
                    if nbr in alive_ids and nbr not in visited:
                        q.append(nbr)
            if c:
                comps.append(c)
        return comps

    def component_density(self, comp):
        n = len(comp)
        if n < 2:
            return 0.0
        possible = n * (n - 1) / 2
        actual = 0
        cl = list(comp)
        for a in range(len(cl)):
            for b in range(a + 1, len(cl)):
                key = (min(cl[a], cl[b]), max(cl[a], cl[b]))
                if key in self.links and self.links[key].alive:
                    actual += 1
        return actual / possible

    # ---- Mutation ----

    def add_link(self, i, j, strength):
        key = (min(i, j), max(i, j))
        self._invalidate()
        if key in self.links and self.links[key].alive:
            self.links[key].strength = min(1.0, self.links[key].strength + strength)
            return self.links[key]
        lk = Link(i=key[0], j=key[1], strength=strength,
                   alive=True, birth_step=self.step_count)
        self.links[key] = lk
        return lk

    def kill_link(self, key):
        if key in self.links:
            self.links[key].alive = False
            self.links[key].strength = 0.0
            self._invalidate()

    def enforce_extinction(self):
        ch = False
        for n in self.nodes.values():
            if n.energy < self.EXTINCTION_THRESHOLD:
                n.energy = 0.0
                n.alive = False
            else:
                n.alive = True
        for k, lk in self.links.items():
            if lk.strength < self.EXTINCTION_THRESHOLD:
                if lk.alive:
                    ch = True
                lk.strength = 0.0
                lk.alive = False
        if ch:
            self._invalidate()

    def get_energy_array(self):
        return np.array([self.nodes[i].energy for i in range(self.n_nodes)])

    def get_degree_array(self):
        d = np.zeros(self.n_nodes)
        for (i, j), lk in self.links.items():
            if lk.alive:
                d[i] += 1
                d[j] += 1
        return d

    def snapshot(self):
        return {
            "step": self.step_count,
            "nodes": {nid: {"energy": n.energy, "alive": n.alive}
                      for nid, n in self.nodes.items()},
            "links": {f"{k[0]}-{k[1]}": {"strength": l.strength}
                      for k, l in self.links.items() if l.alive},
        }
