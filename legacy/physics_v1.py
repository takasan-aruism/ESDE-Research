"""
ESDE Genesis v0.1 — PhysicsEngine Module
==========================================
v0.1 changes:
  - New bonus_mode parameter: "triangle", "cycle", or "none"
  - "cycle" mode: decay bonus based on ALL cycles ≤ max_cycle_length
  - "triangle" mode: original behavior (backward compat)
  - Cycle bonus weighted: shorter cycles = stronger bonus

Author: Claude (Implementation)
Architect: Gemini | Auditor: GPT
"""

import numpy as np
from typing import Optional, List
from dataclasses import dataclass

from universe import Universe


@dataclass
class PhysicsParams:
    # A. Dissipation
    node_decay_rate: float = 0.02
    link_decay_rate: float = 0.08
    connectivity_shelter: float = 0.5

    # B. Injection
    inject_amount: float = 0.6
    inject_prob: float = 0.15
    inject_pair_radius: int = 8
    inject_link_strength: float = 0.3

    # C. Exclusion
    exclusion_enabled: bool = True

    # D. Structural Advantage
    structural_advantage_enabled: bool = True
    gamma: float = 5.0

    # NEW: Bonus mode — "triangle", "cycle", or "none"
    bonus_mode: str = "triangle"      # "triangle" | "cycle" | "none"
    max_cycle_length: int = 5         # For cycle mode: detect up to this length
    # Cycle weighting: bonus = gamma * sum( weight_k * count_k )
    # Shorter cycles get more weight (they're tighter structures)
    cycle_weights: dict = None        # {3: w3, 4: w4, 5: w5}

    # Energy Flow
    flow_coefficient: float = 0.1

    # Extinction
    extinction_threshold: float = 0.01

    def __post_init__(self):
        if self.cycle_weights is None:
            # Default: shorter cycles = stronger bonus
            # Triangle (3): full weight
            # Square (4): 60% weight
            # Pentagon (5): 30% weight
            self.cycle_weights = {3: 1.0, 4: 0.6, 5: 0.3}


class PhysicsEngine:
    def __init__(self, params):
        self.params = params

    def step(self, universe):
        self._apply_energy_flow(universe)
        self._apply_dissipation(universe)
        self._apply_exclusion(universe)
        universe.enforce_extinction()
        universe.step_count += 1

    # ---- Force A: Dissipation ----

    def _apply_dissipation(self, universe):
        p = self.params

        # Node decay (connectivity-sheltered)
        for node in universe.nodes.values():
            if node.alive:
                lsum = universe.node_link_strength_sum(node.id)
                eff_decay = p.node_decay_rate / (1.0 + p.connectivity_shelter * lsum)
                node.energy *= (1.0 - eff_decay)

        # Link decay (with structural advantage)
        for key, link in universe.links.items():
            if not link.alive:
                continue

            base_decay = p.link_decay_rate

            if p.structural_advantage_enabled:
                bonus = self._compute_structure_bonus(universe, link.i, link.j)
                effective_decay = base_decay / (1.0 + bonus)
            else:
                effective_decay = base_decay

            link.strength *= (1.0 - effective_decay)

    def _compute_structure_bonus(self, universe, li, lj):
        """
        Compute structural advantage bonus for a link.

        triangle mode: gamma * triangle_count  (original)
        cycle mode:    gamma * sum(weight_k * cycle_count_k)  (new)
        none:          0
        """
        p = self.params

        if p.bonus_mode == "none" or not p.structural_advantage_enabled:
            return 0.0

        if p.bonus_mode == "triangle":
            tri_count = universe.triangle_count_for_link(li, lj)
            return p.gamma * tri_count

        if p.bonus_mode == "cycle":
            cc = universe.cycle_count_for_link(li, lj, p.max_cycle_length)
            weighted_sum = 0.0
            for k in range(3, p.max_cycle_length + 1):
                w = p.cycle_weights.get(k, 0.0)
                weighted_sum += w * cc.get(k, 0)
            return p.gamma * weighted_sum

        return 0.0

    # ---- Force B: Injection ----

    def inject(self, universe, target_nodes=None):
        p = self.params
        if target_nodes is None:
            mask = universe.rng.random(universe.n_nodes) < p.inject_prob
            target_nodes = [i for i in range(universe.n_nodes) if mask[i]]
        if not target_nodes:
            return target_nodes
        for nid in target_nodes:
            node = universe.nodes[nid]
            node.energy = min(1.0, node.energy + p.inject_amount)
            node.alive = True
        for a in range(len(target_nodes)):
            for b in range(a + 1, len(target_nodes)):
                ni, nj = target_nodes[a], target_nodes[b]
                if abs(ni - nj) <= p.inject_pair_radius:
                    self._try_add_link(universe, ni, nj, p.inject_link_strength)
        return target_nodes

    def inject_focused(self, universe, center, radius, amount):
        targets = [i for i in range(universe.n_nodes) if abs(i - center) <= radius]
        for nid in targets:
            universe.nodes[nid].energy = min(1.0, universe.nodes[nid].energy + amount)
            universe.nodes[nid].alive = True
        for a in range(len(targets)):
            for b in range(a + 1, len(targets)):
                self._try_add_link(universe, targets[a], targets[b],
                                   self.params.inject_link_strength)
        return targets

    # ---- Force C: Exclusion ----

    def _apply_exclusion(self, universe):
        if not self.params.exclusion_enabled:
            return
        for node in universe.nodes.values():
            if not node.alive:
                continue
            total = universe.node_link_strength_sum(node.id)
            if total <= node.c_max:
                continue
            connected = [(k, l) for k, l in universe.links.items()
                         if l.alive and (l.i == node.id or l.j == node.id)]
            connected.sort(key=lambda x: x[1].birth_step, reverse=True)
            cur = total
            for k, l in connected:
                if cur <= node.c_max:
                    break
                cur -= l.strength
                universe.kill_link(k)

    # ---- Energy Flow ----

    def _apply_energy_flow(self, universe):
        k = self.params.flow_coefficient
        flows = {nid: 0.0 for nid in range(universe.n_nodes)}
        for key, link in universe.links.items():
            if not link.alive:
                continue
            ei = universe.nodes[link.i].energy
            ej = universe.nodes[link.j].energy
            flow = k * link.strength * (ei - ej)
            flows[link.i] -= flow
            flows[link.j] += flow
        for nid, net in flows.items():
            universe.nodes[nid].energy = np.clip(
                universe.nodes[nid].energy + net, 0.0, 1.0)

    def _try_add_link(self, universe, i, j, strength):
        if not self.params.exclusion_enabled:
            universe.add_link(i, j, strength)
            return
        key = (min(i, j), max(i, j))
        existing = key in universe.links and universe.links[key].alive
        if not existing:
            si = universe.node_link_strength_sum(i)
            sj = universe.node_link_strength_sum(j)
            if (si + strength > universe.nodes[i].c_max or
                    sj + strength > universe.nodes[j].c_max):
                return
        universe.add_link(i, j, strength)
