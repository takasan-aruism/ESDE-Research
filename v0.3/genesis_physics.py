"""
ESDE Genesis v0.3 — GenesisPhysics
=====================================
The Four Forces, execution order: Flow → Resonance → Decay → Exclusion

Force A: Flow (Injection + Diffusion)
Force B: Resonance (Closed Path detection, cached every N steps)
Force C: Decay (Entropy, mitigated by resonance)
Force D: Exclusion (Capacity constraint)

Designed by: Gemini | Audited by: GPT | Implemented by: Claude
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from genesis_state import GenesisState


@dataclass
class PhysicsParams:
    # A. Flow
    decay_rate_node: float = 0.05
    decay_rate_link: float = 0.05
    flow_coefficient: float = 0.1

    # B. Resonance
    beta: float = 0.1             # Resonance strength (conservative)
    beta_max: float = 5.0         # Cap to prevent explosion
    resonance_interval: int = 10  # Update R_ij every N steps
    max_cycle_length: int = 5
    cycle_weights: Dict[int, float] = None

    # C. Injection
    inject_amount: float = 0.6
    inject_prob: float = 0.15
    inject_pair_radius: int = 8
    inject_link_strength: float = 0.3

    # D. Exclusion
    exclusion_enabled: bool = True
    resonance_enabled: bool = True

    def __post_init__(self):
        if self.cycle_weights is None:
            self.cycle_weights = {3: 1.0, 4: 0.5, 5: 0.25}


class GenesisPhysics:
    """
    Executes the four forces on GenesisState.
    Step order: Flow → Resonance → Decay → Exclusion
    """

    def __init__(self, params: PhysicsParams):
        self.params = params

    def step(self, state: GenesisState):
        """One physics step. Returns cycle_data dict if resonance updated, else None."""
        self._flow(state)

        cycle_data = None
        if state.step % self.params.resonance_interval == 0:
            cycle_data = self._update_resonance(state)

        self._decay(state)

        if self.params.exclusion_enabled:
            self._exclusion(state)

        state.enforce_extinction()
        state.step += 1
        return cycle_data

    # ---- Force A: Flow ----

    def _flow(self, state: GenesisState):
        """Energy diffusion through links."""
        k = self.params.flow_coefficient
        flows = {i: 0.0 for i in range(state.n_nodes)}

        for (li, lj) in state.alive_l:
            ei = state.E[li]
            ej = state.E[lj]
            f = k * state.S[(li, lj)] * (ei - ej)
            flows[li] -= f
            flows[lj] += f

        for i, net in flows.items():
            state.E[i] = float(np.clip(state.E[i] + net, 0.0, 1.0))

    # ---- Force B: Resonance ----

    def _update_resonance(self, state: GenesisState):
        """
        Recalculate R_ij for all alive links.
        Returns cycle count dict {3: n, 4: n, 5: n} or None.
        """
        if not self.params.resonance_enabled:
            for k in state.alive_l:
                state.R[k] = 0.0
            return None

        # Get cycles and compute resonance
        cycles = state.find_all_cycles(self.params.max_cycle_length)
        cycle_counts = {k: len(v) for k, v in cycles.items()}

        # Compute R_ij from cycles
        weights = self.params.cycle_weights
        R_new = {k: 0.0 for k in state.alive_l}
        for length, cycle_list in cycles.items():
            w = weights.get(length, 0.0)
            if w == 0.0:
                continue
            for cycle in cycle_list:
                for idx in range(len(cycle)):
                    ni = cycle[idx]
                    nj = cycle[(idx + 1) % len(cycle)]
                    lk = state.key(ni, nj)
                    if lk in R_new:
                        R_new[lk] += w

        # Cap and apply
        cap = self.params.beta_max / max(self.params.beta, 0.001)
        for k, val in R_new.items():
            state.R[k] = min(val, cap)

        return cycle_counts

    # ---- Force C: Decay ----

    def _decay(self, state: GenesisState):
        """
        Apply decay to nodes and links.
        Node decay: simple linear.
        Link decay: mitigated by resonance R_ij.
          effective_decay = base_decay / (1 + beta * R_ij)
        """
        p = self.params

        # Node decay (simple)
        for i in list(state.alive_n):
            state.E[i] *= (1.0 - p.decay_rate_node)

        # Link decay (resonance-mitigated)
        for k in list(state.alive_l):
            r = state.R.get(k, 0.0)
            eff_decay = p.decay_rate_link / (1.0 + p.beta * r)
            state.S[k] *= (1.0 - eff_decay)

    # ---- Force D: Exclusion ----

    def _exclusion(self, state: GenesisState):
        """
        Enforce capacity: sum(S_connected) <= C_max per node.
        Prune weakest links if exceeded.
        """
        for i in list(state.alive_n):
            total = state.link_strength_sum(i)
            if total <= state.c_max:
                continue

            # Collect links, sort by strength (weakest first)
            connected = []
            for k in list(state.alive_l):
                if k[0] == i or k[1] == i:
                    connected.append((k, state.S[k]))
            connected.sort(key=lambda x: x[1])  # weakest first

            cur = total
            for k, s in connected:
                if cur <= state.c_max:
                    break
                cur -= s
                state.kill_link(k)

    # ---- Injection ----

    def inject(self, state: GenesisState, target_nodes: Optional[List[int]] = None):
        """External energy burst."""
        p = self.params

        if target_nodes is None:
            mask = state.rng.random(state.n_nodes) < p.inject_prob
            target_nodes = [i for i in range(state.n_nodes) if mask[i]]

        if not target_nodes:
            return target_nodes

        for nid in target_nodes:
            state.E[nid] = min(1.0, state.E[nid] + p.inject_amount)
            state.alive_n.add(nid)

        # Form links between co-struck nodes
        for a in range(len(target_nodes)):
            for b in range(a + 1, len(target_nodes)):
                ni, nj = target_nodes[a], target_nodes[b]
                if abs(ni - nj) <= p.inject_pair_radius:
                    self._try_add_link(state, ni, nj, p.inject_link_strength)

        return target_nodes

    def _try_add_link(self, state: GenesisState, i: int, j: int, strength: float):
        """Add link with exclusion check."""
        if not self.params.exclusion_enabled:
            state.add_link(i, j, strength)
            return

        k = state.key(i, j)
        if k in state.alive_l:
            state.add_link(i, j, strength)
            return

        si = state.link_strength_sum(i)
        sj = state.link_strength_sum(j)
        if (si + strength > state.c_max or sj + strength > state.c_max):
            return
        state.add_link(i, j, strength)
