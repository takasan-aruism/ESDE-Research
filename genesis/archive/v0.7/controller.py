"""
ESDE Genesis v0.7 — Adaptive Controller (Axiom X)
====================================================
Meta-Physics Engine: observes system, adjusts parameters to maximize
Metabolic Vitality (V) via round-robin coordinate ascent.

Does NOT alter core laws. Only adjusts 4 bounded parameters.

V = R + w1*S + w2*M + w3*P
  R = reactions in window
  S = state diversity (Shannon entropy)
  M = resonant mass (mean over window)
  P = mean C lifetime in window (persistence term, GPT addendum)

Designed: Gemini | Audited: GPT | Built: Claude
"""

import numpy as np
import csv
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class AdaptiveParam:
    name: str
    min_bound: float
    max_bound: float
    delta: float
    value: float = 0.0

    def clip(self):
        self.value = max(self.min_bound, min(self.max_bound, self.value))


class AdaptiveController:
    """
    Round-robin hill climbing controller.
    Adjusts ONE parameter per window. Reverts on failure.
    """

    W1 = 10.0  # state diversity weight
    W2 = 2.0   # resonant mass weight
    W3 = 1.0   # C persistence weight (GPT addendum)

    def __init__(self, window_size: int = 200):
        self.window_size = window_size

        # Adaptive parameter set
        self.params: List[AdaptiveParam] = [
            AdaptiveParam("reaction_energy_threshold", 0.10, 0.60, 0.02, 0.30),
            AdaptiveParam("link_death_threshold",      0.0005, 0.05, 0.002, 0.001),
            AdaptiveParam("background_injection_prob",  0.001, 0.05, 0.002, 0.005),
            AdaptiveParam("exothermic_release_amount",  0.05, 0.40, 0.02, 0.15),
        ]

        self.current_param_index = 0
        self.current_direction = +1
        self.previous_V = 0.0
        self.window_count = 0

        # Log
        self.log: List[dict] = []

        # C lifetime tracking (per-node counter)
        self._c_ticks: Dict[int, int] = {}  # node_id -> steps in state C
        self._c_lifetimes_window: List[int] = []

    def get_param(self, name: str) -> float:
        for p in self.params:
            if p.name == name:
                return p.value
        return 0.0

    def apply_to_system(self, chem_params, state):
        """Push current adaptive values into the running system."""
        chem_params.E_thr = self.get_param("reaction_energy_threshold")
        chem_params.exothermic_release = self.get_param("exothermic_release_amount")
        state.EXTINCTION = self.get_param("link_death_threshold")
        # background_injection_prob is read directly by the runner

    def track_c_lifetimes(self, state):
        """Called every step. Track C persistence WITHIN current window only."""
        current_c = set()
        for i in state.alive_n:
            if state.Z[i] == 3:
                current_c.add(i)
                self._c_ticks[i] = self._c_ticks.get(i, 0) + 1

        # Nodes that left C state — record their window-local lifetime
        departed = [nid for nid in list(self._c_ticks) if nid not in current_c]
        for nid in departed:
            self._c_lifetimes_window.append(self._c_ticks.pop(nid))

    def compute_vitality(self, history: List[dict]) -> dict:
        """
        Compute V from the last window_size log entries.
        P = mean C lifetime of nodes that COMPLETED C state in this window.
        For still-alive C nodes, cap contribution at window_size.
        """
        if not history:
            return {"V": 0, "R": 0, "S": 0, "M": 0, "P": 0}

        R = sum(h.get("rxn_total", 0) for h in history)

        entropies = []
        for h in history:
            counts = [h.get("n_Dust", 0), h.get("n_A", 0),
                      h.get("n_B", 0), h.get("n_C", 0)]
            total = sum(counts)
            if total == 0:
                entropies.append(0)
                continue
            probs = [c / total for c in counts if c > 0]
            ent = -sum(p * np.log2(p) for p in probs)
            entropies.append(ent)
        S = float(np.mean(entropies)) if entropies else 0.0

        M = float(np.mean([h.get("resonant_mass", 0) for h in history]))

        # P: mean C lifetime, capped at window_size for still-alive
        lifetimes = list(self._c_lifetimes_window)
        for ticks in self._c_ticks.values():
            lifetimes.append(min(ticks, self.window_size))
        P = float(np.mean(lifetimes)) if lifetimes else 0.0
        # Cap P to window_size to prevent unbounded growth
        P = min(P, float(self.window_size))

        V = R + self.W1 * S + self.W2 * M + self.W3 * P

        return {"V": round(V, 3), "R": R, "S": round(S, 4),
                "M": round(M, 4), "P": round(P, 2)}

    def evaluate_and_adapt(self, history: List[dict]):
        """
        Called every window_size steps.
        Returns log entry dict.
        """
        self.window_count += 1
        scores = self.compute_vitality(history)
        current_V = scores["V"]
        delta_V = current_V - self.previous_V

        # Current parameter being tuned
        param = self.params[self.current_param_index]
        old_value = param.value
        reverted = False

        if delta_V >= 0:
            # Success: keep direction
            pass
        else:
            # Failure: reverse and revert
            self.current_direction = -self.current_direction
            # Revert: undo the step that was applied at end of LAST window
            param.value -= self.current_direction * param.delta  # undo
            param.clip()
            reverted = True

        # Move to next parameter
        self.current_param_index = (self.current_param_index + 1) % len(self.params)
        next_param = self.params[self.current_param_index]

        # Apply next adjustment
        next_old = next_param.value
        next_param.value += self.current_direction * next_param.delta
        next_param.clip()

        entry = {
            "window": self.window_count,
            "V": current_V,
            "R": scores["R"],
            "S": scores["S"],
            "M": scores["M"],
            "P": scores["P"],
            "delta_V": round(delta_V, 3),
            "param_adjusted": next_param.name,
            "old_value": round(next_old, 5),
            "new_value": round(next_param.value, 5),
            "direction": self.current_direction,
            "reverted": reverted,
        }
        self.log.append(entry)

        self.previous_V = current_V
        self._c_lifetimes_window.clear()
        # Reset window-local C tick counters (keep tracking, just reset counts)
        for nid in self._c_ticks:
            self._c_ticks[nid] = 0

        return entry

    def export_log(self, path: str):
        if not self.log:
            return
        keys = self.log[0].keys()
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(self.log)
