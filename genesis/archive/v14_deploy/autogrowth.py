"""
ESDE Genesis v0.9 — Auto-Growth Engine
=========================================
Links participating in closed loops (R_ij > 0) earn strength
by consuming latent potential (L_ij).

Rule: if R_ij > 0:
  growth = min(auto_growth_rate * R_ij, L_ij)
  S_ij += growth (capped at 1.0)
  L_ij -= growth (floored at 0.0)

Cost: Exclusion (Σ S_ij ≤ C_max) prunes weak links when budget exceeded.
This creates competition: loops strengthen their links at others' expense.

Runs AFTER resonance detection, BEFORE decay/exclusion.

Designed: Gemini | Audited: GPT | Built: Claude
"""

from dataclasses import dataclass
from genesis_state import GenesisState


@dataclass
class AutoGrowthParams:
    enabled: bool = True
    auto_growth_rate: float = 0.02  # S_ij += rate * R_ij per step


class AutoGrowthEngine:
    """Strengthens loop-participating links by consuming latent potential."""

    def __init__(self, params: AutoGrowthParams):
        self.params = params
        self.growth_events = 0
        self.total_growth = 0.0
        self.latent_consumed = 0.0

    def step(self, state: GenesisState):
        """Apply auto-growth to all active links with R_ij > 0."""
        if not self.params.enabled:
            return

        self.growth_events = 0
        self.total_growth = 0.0
        self.latent_consumed = 0.0

        for k in list(state.alive_l):
            r_ij = state.R.get(k, 0.0)
            if r_ij <= 0:
                continue

            i, j = k
            l_ij = state.get_latent(i, j)
            if l_ij <= 0:
                continue

            desired = self.params.auto_growth_rate * r_ij
            actual = min(desired, l_ij, 1.0 - state.S[k])

            if actual > 0:
                state.S[k] += actual
                state.set_latent(i, j, l_ij - actual)
                self.growth_events += 1
                self.total_growth += actual
                self.latent_consumed += actual

    def reset_counters(self):
        self.growth_events = 0
        self.total_growth = 0.0
        self.latent_consumed = 0.0
