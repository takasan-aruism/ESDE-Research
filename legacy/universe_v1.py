"""
ESDE Genesis v0.1 — Universe Module
=====================================
State container: Nodes, Links, and network topology.

v0.1 changes:
  - Added general cycle detection (length 3, 4, 5)
  - cycle_count_for_link() replaces triangle-only detection
  - total_cycle_count() for global metrics

Author: Claude (Implementation)
Architect: Gemini | Auditor: GPT
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Tuple, Set, List, Optional
from collections import defaultdict


@dataclass
class Node:
    id: int
    energy: float = 0.0
    c_max: float = 3.0
    alive: bool = True

    def total_link_strength(self, links):
        total = 0.0
        for (i, j), link in links.items():
            if link.alive and (i == self.id or j == self.id):
                total += link.strength
        return total


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
        self.links = {}

    def active_nodes(self):
        return [n for n in self.nodes.values() if n.alive]

    def active_links(self):
        return [l for l in self.links.values() if l.alive]

    def neighbors(self, node_id):
        nbrs = []
        for (i, j), link in self.links.items():
            if not link.alive:
                continue
            if i == node_id:
                nbrs.append(j)
            elif j == node_id:
                nbrs.append(i)
        return nbrs

    def node_link_strength_sum(self, node_id):
        total = 0.0
        for (i, j), link in self.links.items():
            if link.alive and (i == node_id or j == node_id):
                total += link.strength
        return total

    # ==================================================================
    # CYCLE DETECTION (v0.1 — replaces triangle-only)
    # ==================================================================

    def triangle_count_for_link(self, li, lj):
        """Legacy: count triangles only. Kept for backward compat."""
        nbrs_i = set(self.neighbors(li))
        nbrs_j = set(self.neighbors(lj))
        return len(nbrs_i & nbrs_j)

    def cycle_count_for_link(self, li, lj, max_length=5):
        """
        Count cycles of length 3..max_length passing through edge (li, lj).

        Method: BFS from lj, avoiding the direct (li,lj) edge,
        counting paths of length d that reach li → cycle of length d+1.

        Returns: {3: n3, 4: n4, 5: n5, "total": sum}
        """
        counts = {k: 0 for k in range(3, max_length + 1)}

        # BFS layers: current_layer[node] = number of paths from lj to node
        current_layer = {lj: 1}

        for depth in range(1, max_length):
            next_layer = {}
            for node, path_count in current_layer.items():
                for nbr in self.neighbors(node):
                    # At depth 1, skip the direct li-lj edge
                    if depth == 1 and node == lj and nbr == li:
                        continue
                    # Don't revisit start node (avoid degenerate loops)
                    if nbr == lj:
                        continue
                    if nbr not in next_layer:
                        next_layer[nbr] = 0
                    next_layer[nbr] += path_count

            cycle_len = depth + 1
            if li in next_layer and cycle_len in counts:
                counts[cycle_len] = next_layer[li]

            current_layer = next_layer

        counts["total"] = sum(counts[k] for k in range(3, max_length + 1))
        return counts

    def total_triangle_count(self):
        """Count all unique triangles."""
        triangles = set()
        for (i, j), link in self.links.items():
            if not link.alive:
                continue
            nbrs_i = set(self.neighbors(i))
            nbrs_j = set(self.neighbors(j))
            for k in nbrs_i & nbrs_j:
                triangles.add(tuple(sorted([i, j, k])))
        return len(triangles)

    def total_cycle_count(self, max_length=5):
        """
        Count all unique cycles of length 3..max_length.
        Each cycle of length k is detected k times (once per edge),
        so divide raw count by k.
        """
        raw = {k: 0 for k in range(3, max_length + 1)}
        for key, link in self.links.items():
            if not link.alive:
                continue
            cc = self.cycle_count_for_link(link.i, link.j, max_length)
            for k in range(3, max_length + 1):
                raw[k] += cc.get(k, 0)
        unique = {}
        for k in range(3, max_length + 1):
            unique[k] = raw[k] // k if k > 0 else 0
        unique["total"] = sum(unique[k] for k in range(3, max_length + 1))
        return unique

    # ==================================================================
    # TOPOLOGY QUERIES
    # ==================================================================

    def connected_components(self):
        alive_ids = {n.id for n in self.active_nodes()}
        visited = set()
        components = []
        for start in alive_ids:
            if start in visited:
                continue
            queue = [start]
            component = set()
            while queue:
                cur = queue.pop(0)
                if cur in visited:
                    continue
                visited.add(cur)
                component.add(cur)
                for nbr in self.neighbors(cur):
                    if nbr in alive_ids and nbr not in visited:
                        queue.append(nbr)
            if component:
                components.append(component)
        return components

    def component_density(self, component):
        n = len(component)
        if n < 2:
            return 0.0
        possible = n * (n - 1) / 2
        actual = 0
        comp_list = list(component)
        for a in range(len(comp_list)):
            for b in range(a + 1, len(comp_list)):
                key = (min(comp_list[a], comp_list[b]), max(comp_list[a], comp_list[b]))
                if key in self.links and self.links[key].alive:
                    actual += 1
        return actual / possible

    # ==================================================================
    # STATE MUTATION
    # ==================================================================

    def add_link(self, i, j, strength):
        key = (min(i, j), max(i, j))
        if key in self.links and self.links[key].alive:
            self.links[key].strength = min(1.0, self.links[key].strength + strength)
            return self.links[key]
        link = Link(i=key[0], j=key[1], strength=strength,
                    alive=True, birth_step=self.step_count)
        self.links[key] = link
        return link

    def kill_link(self, key):
        if key in self.links:
            self.links[key].alive = False
            self.links[key].strength = 0.0

    def enforce_extinction(self):
        for node in self.nodes.values():
            if node.energy < self.EXTINCTION_THRESHOLD:
                node.energy = 0.0
                node.alive = False
            else:
                node.alive = True
        for key, link in self.links.items():
            if link.strength < self.EXTINCTION_THRESHOLD:
                link.strength = 0.0
                link.alive = False

    def get_energy_array(self):
        return np.array([self.nodes[i].energy for i in range(self.n_nodes)])

    def get_degree_array(self):
        degrees = np.zeros(self.n_nodes)
        for (i, j), link in self.links.items():
            if link.alive:
                degrees[i] += 1
                degrees[j] += 1
        return degrees

    def snapshot(self):
        return {
            "step": self.step_count,
            "nodes": {nid: {"energy": n.energy, "alive": n.alive}
                      for nid, n in self.nodes.items()},
            "links": {f"{k[0]}-{k[1]}": {"strength": l.strength, "alive": l.alive}
                      for k, l in self.links.items() if l.alive},
        }
