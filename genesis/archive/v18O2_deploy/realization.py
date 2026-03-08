"""
ESDE Genesis v0.8 — Realization Operator
==========================================
Bridges the Potential Field (L) to the Manifest Field (S).

A. Latent Refresh: L_ij slowly recharges via noise
B. Realization: if no active link, P_realize = p_link_birth * L_ij
   → creates active link, consumes latent potential
C. Active decay handled by existing physics engine

Sampling-based: each step, each alive node samples k candidates.
Not O(N²).

Designed: Gemini | Audited: GPT | Built: Claude
"""

import numpy as np
from dataclasses import dataclass
from genesis_state import GenesisState


@dataclass
class RealizationParams:
    enabled: bool = True
    p_link_birth: float = 0.005
    latent_to_active_threshold: float = 0.05
    latent_refresh_rate: float = 0.002
    candidates_per_node: int = 5  # sampling budget


class RealizationOperator:
    """Converts latent potential into active links."""

    def __init__(self, params: RealizationParams):
        self.params = params
        self.realized_this_step = 0

    def step(self, state: GenesisState) -> int:
        """Run realization. Returns count of newly realized links."""
        if not self.params.enabled:
            return 0

        p = self.params
        self.realized_this_step = 0
        alive_list = list(state.alive_n)
        n_alive = len(alive_list)
        if n_alive < 2:
            return 0

        # A. Latent Refresh — modulated by node fertility (v1.7)
        l_keys = list(state.L.keys())
        if l_keys:
            n_refresh = min(len(l_keys), 500)
            refresh_idx = state._latent_rng.choice(len(l_keys), n_refresh, replace=False)
            for idx in refresh_idx:
                k = l_keys[idx]
                # v1.7: effective rate = base * mean(F_i, F_j)
                f_avg = (state.F[k[0]] + state.F[k[1]]) / 2.0
                eff_rate = p.latent_refresh_rate * f_avg
                noise = abs(state._latent_rng.randn()) * eff_rate
                state.L[k] = min(1.0, state.L[k] + noise)

        # B. Realization — sample 3 candidates per node
        k_samples = min(3, n_alive - 1)
        alive_arr = np.array(alive_list)

        for i in alive_list:
            candidates = state.rng.choice(alive_arr, size=k_samples + 1, replace=False)
            for j in candidates:
                j = int(j)
                if j == i:
                    continue
                link_key = state.key(i, j)
                if link_key in state.alive_l:
                    continue

                l_ij = state.get_latent(i, j)
                p_realize = p.p_link_birth * l_ij
                if state.rng.random() < p_realize:
                    state.add_link(i, j, p.latent_to_active_threshold)
                    state.set_latent(i, j, l_ij - p.latent_to_active_threshold)
                    self.realized_this_step += 1

        return self.realized_this_step
