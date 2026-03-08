"""
ESDE Genesis v0.5 — Chemistry Layer
======================================
Phase-Coupled Artificial Chemistry

States: 0=Dust, 1=A, 2=B, 3=C
Triggers: Strong link + Energy + Phase coherence
Rules: Synthesis (A+B→CC), Autocatalysis (C+A→CC), Decay (C→0 if low E)

Resolution: Greedy maximal matching (each node ≤1 reaction/step)
Update: Synchronous (compute all, then apply)

Designed by: Gemini | Audited by: GPT | Implemented by: Claude
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set
from genesis_state import GenesisState


@dataclass
class ChemistryParams:
    enabled: bool = True

    # Seeding
    p_seed: float = 0.1        # prob of 0→A/B during injection
    ab_ratio: float = 0.5      # fraction that become A (rest become B)

    # Trigger thresholds
    S_thr: float = 0.3         # min link strength (matches inject_link_strength)
    E_thr: float = 0.3         # min energy for both nodes
    P_thr: float = 0.7         # min cos(dtheta) phase coherence

    # Decay
    E_low: float = 0.2         # C decays to 0 if energy below this

    # v0.6: Exothermic decay — energy released when C→Dust
    exothermic_release: float = 0.15

    # Toggle gates (for ablation experiments)
    gate_phase: bool = True    # require phase coherence
    gate_link: bool = True     # require strong link
    rule_autocatalysis: bool = True  # enable rule 2


@dataclass
class ReactionRecord:
    """One reaction applied this step."""
    rule: int          # 1=synthesis, 2=autocatalysis, 3=decay
    node_i: int
    node_j: int = -1   # -1 for decay (single-node)
    s_ij: float = 0.0
    phase_cos: float = 0.0


class ChemistryEngine:
    """
    Runs chemistry on GenesisState.
    Called between Flow/Phase and Resonance/Decay.
    """

    def __init__(self, params: ChemistryParams):
        self.params = params

    def seed_on_injection(self, state: GenesisState, injected_nodes: list):
        """
        During injection, Dust nodes have p_seed chance to become A or B.
        """
        if not self.params.enabled or not injected_nodes:
            return
        p = self.params
        for nid in injected_nodes:
            if state.Z[nid] == 0:
                if state.rng.random() < p.p_seed:
                    state.Z[nid] = 1 if state.rng.random() < p.ab_ratio else 2

    def step(self, state: GenesisState) -> List[ReactionRecord]:
        """
        Execute chemistry: find candidate reactions, resolve, apply.
        Returns list of applied reactions.
        """
        if not self.params.enabled:
            return []

        reactions = []

        # Phase 1: Decay (Rule 3) — independent, no conflict
        decay_reactions = self._find_decays(state)

        # Phase 2: Pairwise reactions (Rule 1 + Rule 2)
        candidates = self._find_candidates(state)
        matched = self._greedy_match(candidates, state)

        # Phase 3: Apply synchronously
        used_nodes: Set[int] = set()

        # Apply decays first (they don't conflict with pairwise since C→0)
        for r in decay_reactions:
            state.Z[r.node_i] = 0
            # v0.6: Exothermic decay — release stored energy
            state.E[r.node_i] = min(1.0, state.E[r.node_i] + self.params.exothermic_release)
            used_nodes.add(r.node_i)
            reactions.append(r)

        # Apply pairwise
        for r in matched:
            if r.node_i in used_nodes or r.node_j in used_nodes:
                continue
            if r.rule == 1:  # Synthesis: A+B → C+C
                state.Z[r.node_i] = 3
                state.Z[r.node_j] = 3
            elif r.rule == 2:  # Autocatalysis: C+A → C+C
                # The A node becomes C
                if state.Z[r.node_i] == 3 and state.Z[r.node_j] == 1:
                    state.Z[r.node_j] = 3
                elif state.Z[r.node_j] == 3 and state.Z[r.node_i] == 1:
                    state.Z[r.node_i] = 3
            used_nodes.add(r.node_i)
            used_nodes.add(r.node_j)
            reactions.append(r)

        return reactions

    def _find_decays(self, state: GenesisState) -> List[ReactionRecord]:
        """Rule 3: C nodes with low energy decay to Dust."""
        decays = []
        for i in list(state.alive_n):
            if state.Z[i] == 3 and state.E[i] < self.params.E_low:
                decays.append(ReactionRecord(rule=3, node_i=i))
        return decays

    def _find_candidates(self, state: GenesisState) -> List[ReactionRecord]:
        """
        Find all link-pairs meeting trigger conditions.
        Returns candidates sorted by score (descending).
        """
        p = self.params
        candidates = []

        for (li, lj) in state.alive_l:
            s = state.S[(li, lj)]

            # Gate: link strength
            if p.gate_link and s < p.S_thr:
                continue

            # Gate: energy
            ei, ej = state.E[li], state.E[lj]
            if ei < p.E_thr or ej < p.E_thr:
                continue

            # Gate: phase coherence
            if p.gate_phase:
                dtheta = state.theta[lj] - state.theta[li]
                pc = float(np.cos(dtheta))
                if pc < p.P_thr:
                    continue
            else:
                pc = 1.0

            zi, zj = state.Z[li], state.Z[lj]

            # Rule 1: Synthesis (A+B → C+C)
            if (zi == 1 and zj == 2) or (zi == 2 and zj == 1):
                candidates.append(ReactionRecord(
                    rule=1, node_i=li, node_j=lj, s_ij=s, phase_cos=pc))

            # Rule 2: Autocatalysis (C+A → C+C)
            if p.rule_autocatalysis:
                if (zi == 3 and zj == 1) or (zi == 1 and zj == 3):
                    candidates.append(ReactionRecord(
                        rule=2, node_i=li, node_j=lj, s_ij=s, phase_cos=pc))

        # Sort: descending S_ij, tie-break by min energy, then phase
        candidates.sort(key=lambda r: (
            -r.s_ij,
            -min(state.E[r.node_i], state.E[r.node_j]),
            -r.phase_cos
        ))
        return candidates

    def _greedy_match(self, candidates: List[ReactionRecord],
                      state: GenesisState) -> List[ReactionRecord]:
        """
        Greedy maximal matching: each node participates in at most one reaction.
        """
        used = set()
        matched = []
        for r in candidates:
            if r.node_i not in used and r.node_j not in used:
                matched.append(r)
                used.add(r.node_i)
                used.add(r.node_j)
        return matched
