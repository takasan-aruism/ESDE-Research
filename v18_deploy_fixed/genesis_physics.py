"""
ESDE Genesis v0.4 — GenesisPhysics
=====================================
"Artificial Wave Physics"

Five Forces (execution order):
  A. Phase Rotation  (The Clock)     — NEW
  B. Flow + Sync     (The Wave)      — UPDATED with phase coupling
  C. Resonance       (Topology)      — from v0.3
  D. Decay           (Entropy)       — from v0.3
  E. Exclusion       (Competition)   — from v0.3

Audit corrections applied:
  1. phase_factor = 0.5 + 0.5 * gamma * cos(dtheta)  [prevents negative flow]
  2. Phase rotation: theta += omega  [alpha=0 initially]
  3. Kuramoto coupling: theta += K * sum(sin(theta_j - theta_i))

Designed by: Gemini | Audited by: GPT | Implemented by: Claude
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict
from collections import defaultdict

from genesis_state import GenesisState


@dataclass
class PhysicsParams:
    # Flow
    flow_coefficient: float = 0.1       # k

    # Phase dynamics (v0.4)
    gamma: float = 1.0                  # phase-flow influence
    alpha: float = 0.0                  # energy-frequency coupling (0 = stable start)
    K_sync: float = 0.1                 # Kuramoto coupling strength
    phase_enabled: bool = True

    # Resonance (v0.3)
    beta: float = 1.0
    beta_max: float = 5.0
    resonance_interval: int = 10
    max_cycle_length: int = 5
    cycle_weights: Dict[int, float] = None
    resonance_enabled: bool = True

    # Decay
    decay_rate_node: float = 0.05
    decay_rate_link: float = 0.05

    # Injection
    inject_amount: float = 0.6
    inject_prob: float = 0.15
    inject_pair_radius: int = 8
    inject_link_strength: float = 0.3

    # Exclusion
    exclusion_enabled: bool = True

    def __post_init__(self):
        if self.cycle_weights is None:
            self.cycle_weights = {3: 1.0, 4: 0.5, 5: 0.25}


class GenesisPhysics:
    """Five forces: Phase → Flow+Sync → Resonance → Decay → Exclusion"""

    def __init__(self, params: PhysicsParams):
        self.params = params

    def step(self, state: GenesisState):
        """Full physics step (no chemistry). Returns cycle_data if resonance updated."""
        self.step_pre_chemistry(state)
        return self.step_post_chemistry(state)

    def step_pre_chemistry(self, state: GenesisState):
        """Phase A+B: Phase Rotation + Flow. Run BEFORE chemistry."""
        if self.params.phase_enabled:
            self._phase_rotate(state)
        self._flow_and_sync(state)

    def step_post_chemistry(self, state: GenesisState):
        """Phase C+D+E: Resonance + Decay + Exclusion. Run AFTER chemistry."""
        cycle_data = self.step_resonance(state)
        self.step_decay_exclusion(state)
        return cycle_data

    def step_resonance(self, state: GenesisState):
        """Resonance only. Returns cycle_data if updated."""
        cycle_data = None
        if state.step % self.params.resonance_interval == 0:
            cycle_data = self._update_resonance(state)
        return cycle_data

    def step_decay_exclusion(self, state: GenesisState):
        """Decay + Exclusion + step increment."""
        self._decay(state)
        if self.params.exclusion_enabled:
            self._exclusion(state)
        state.enforce_extinction()
        state.step += 1

    # ---- Force A: Phase Rotation (The Clock) ----

    def _phase_rotate(self, state: GenesisState):
        """
        theta_new = theta_old + omega_i + K * sum(sin(theta_j - theta_i))
        
        Audit correction: alpha=0 initially (no energy-frequency coupling).
        Kuramoto coupling provides weak synchronization between neighbors.
        """
        p = self.params
        n = state.n_nodes
        d_theta = np.zeros(n)

        for i in range(n):
            if i not in state.alive_n:
                continue

            # Natural frequency + energy coupling
            freq = state.omega[i] + p.alpha * state.E[i]
            d_theta[i] = freq

            # Kuramoto synchronization: K * sum_j sin(theta_j - theta_i)
            if p.K_sync > 0:
                nbrs = state.neighbors(i)
                if nbrs:
                    sync_sum = 0.0
                    for j in nbrs:
                        if j in state.alive_n:
                            sync_sum += np.sin(state.theta[j] - state.theta[i])
                    d_theta[i] += p.K_sync * sync_sum / max(len(nbrs), 1)

        state.theta += d_theta
        state.theta %= (2 * np.pi)

    # ---- Force B: Flow + Synchronization (The Wave) ----

    def _flow_and_sync(self, state: GenesisState):
        """
        dE_ij = k * S_ij * (E_j - E_i) * phase_factor
        
        Audit correction:
          phase_factor = 0.5 + 0.5 * gamma * cos(theta_j - theta_i)
          This keeps factor in [0, 1], preventing energy amplification.
        """
        p = self.params
        flows = {i: 0.0 for i in range(state.n_nodes)}

        for (li, lj) in state.alive_l:
            ei = state.E[li]
            ej = state.E[lj]

            if p.phase_enabled and p.gamma > 0:
                dtheta = state.theta[lj] - state.theta[li]
                phase_factor = 0.5 + 0.5 * p.gamma * np.cos(dtheta)
                # Clamp to [0, 1] for safety
                phase_factor = max(0.0, min(1.0, phase_factor))
            else:
                phase_factor = 1.0

            f = p.flow_coefficient * state.S[(li, lj)] * (ej - ei) * phase_factor
            flows[li] += f
            flows[lj] -= f

        for i, net in flows.items():
            state.E[i] = float(np.clip(state.E[i] + net, 0.0, 1.0))

    # ---- Force C: Resonance (Topology) ----

    def _update_resonance(self, state: GenesisState):
        if not self.params.resonance_enabled:
            for k in state.alive_l:
                state.R[k] = 0.0
            return None

        cycles = state.find_all_cycles(self.params.max_cycle_length)
        cycle_counts = {k: len(v) for k, v in cycles.items()}

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

        cap = self.params.beta_max / max(self.params.beta, 0.001)
        for k, val in R_new.items():
            state.R[k] = min(val, cap)

        return cycle_counts

    # ---- Force D: Decay ----

    def _decay(self, state: GenesisState):
        p = self.params
        for i in list(state.alive_n):
            state.E[i] *= (1.0 - p.decay_rate_node)

        for k in list(state.alive_l):
            r = state.R.get(k, 0.0)
            eff = p.decay_rate_link / (1.0 + p.beta * r)
            state.S[k] *= (1.0 - eff)

    # ---- Force E: Exclusion ----

    def _exclusion(self, state: GenesisState):
        for i in list(state.alive_n):
            total = state.link_strength_sum(i)
            if total <= state.c_max:
                continue
            conn = [(k, state.S[k]) for k in list(state.alive_l)
                    if k[0] == i or k[1] == i]
            conn.sort(key=lambda x: x[1])
            cur = total
            for k, s in conn:
                if cur <= state.c_max:
                    break
                cur -= s
                state.kill_link(k)

    # ---- Injection ----

    def inject(self, state: GenesisState, target_nodes=None):
        p = self.params
        if target_nodes is None:
            mask = state.rng.random(state.n_nodes) < p.inject_prob
            target_nodes = [i for i in range(state.n_nodes) if mask[i]]
        if not target_nodes:
            return target_nodes
        for nid in target_nodes:
            state.E[nid] = min(1.0, state.E[nid] + p.inject_amount)
            state.alive_n.add(nid)
        for a in range(len(target_nodes)):
            for b in range(a + 1, len(target_nodes)):
                ni, nj = target_nodes[a], target_nodes[b]
                if abs(ni - nj) <= p.inject_pair_radius:
                    self._try_add_link(state, ni, nj, p.inject_link_strength)
        return target_nodes

    def _try_add_link(self, state, i, j, strength):
        if not self.params.exclusion_enabled:
            state.add_link(i, j, strength)
            return
        k = state.key(i, j)
        if k in state.alive_l:
            state.add_link(i, j, strength)
            return
        si = state.link_strength_sum(i)
        sj = state.link_strength_sum(j)
        if si + strength > state.c_max or sj + strength > state.c_max:
            return
        state.add_link(i, j, strength)
