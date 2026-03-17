#!/usr/bin/env python3
"""
ESDE v4.8c — Automated Parameter Discovery
==============================================
Phase : v4.8c (Homeostatic Controller for Z-Coupling)
Role  : Claude (Implementation)
Arch  : Gemini (+ Taka directive) | Audit: GPT

Inherits v4.8b (cooling + Z-coupling) and adds a single mechanism:

  State-Dependent Parameter Drift (Axiom X for Z-coupling)

  At the end of each observation window:
    ΔL = alive_links(t) - alive_links(t-1)
    z_decay_compound_restore -= α × ΔL

  If links are growing (ΔL > 0): restore decreases → slows growth
  If links are shrinking (ΔL < 0): restore increases → aids recovery

  The system discovers its own equilibrium — no hardcoded target.

  Bounds: compound_restore clamped to [0.0, 1.0]
  α = 0.0001 (very gradual drift)

Physics operators: UNCHANGED from v4.8b.
Observation layer: UNCHANGED from v4.8b (v4.6 tracker + motifs).

Principle: "Structure first, meaning later."
"""

import sys, math, time, hashlib
import numpy as np
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
_V48B_DIR = _SCRIPT_DIR.parent / "v48b"
_V48_DIR = _SCRIPT_DIR.parent / "v48"
_V46_DIR = _SCRIPT_DIR.parent / "v46"
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V48B_DIR), str(_V48_DIR), str(_V46_DIR), str(_V45A_DIR),
          str(_V44_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v48b_engine import V48bEngine, V48bEncapsulationParams


# ================================================================
# v4.8c CONSTANTS
# ================================================================
V48C_WINDOW = 50


# ================================================================
# v4.8c PARAMETERS
# ================================================================
@dataclass
class V48cEncapsulationParams(V48bEncapsulationParams):
    """v4.8c: adds parameter drift settings."""
    # Drift learning rate
    drift_alpha: float = 0.0001
    # Parameter bounds
    drift_restore_min: float = 0.0
    drift_restore_max: float = 1.0
    # Enable/disable drift (for ablation)
    drift_enabled: bool = True


# ================================================================
# v4.8c ENGINE
# ================================================================
class V48cEngine(V48bEngine):
    """
    V48bEngine + automated parameter discovery.

    After each step_window, applies link momentum feedback
    to z_decay_compound_restore. No other changes.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V48cEncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.prev_alive_links = 0
        self.restore_trajectory = []  # [(window, restore_value, delta_L)]
        self.last_isum = {}

    def step_window(self, steps=V48C_WINDOW):
        """
        Run v4.8b step_window, then apply parameter drift.

        NOTE: First window produces delta_L=0 (no prior reference),
        so effective drift begins at window 2.
        """
        # Record pre-window link count
        pre_links = len(self.state.alive_l)

        # ── Full v4.8b physics + observation ──
        # last_isum is set by V48bEngine.step_window() via parent chain.
        frame = super().step_window(steps=steps)

        # ── v4.8c: Parameter drift ──
        if self.island_tracker.params.drift_enabled:
            post_links = frame.alive_links
            # First window: prev=0, delta_L=0, no drift applied
            delta_L = post_links - self.prev_alive_links if self.prev_alive_links > 0 else 0
            self.prev_alive_links = post_links

            alpha = self.island_tracker.params.drift_alpha
            lo = self.island_tracker.params.drift_restore_min
            hi = self.island_tracker.params.drift_restore_max

            # Saturate delta_L to prevent runaway parameter swings
            # tanh(ΔL/1000) caps effective ΔL to ±1.0 for large swings
            delta_L_norm = math.tanh(delta_L / 1000.0)

            # Update compound_restore
            old_restore = self.island_tracker.params.z_decay_compound_restore
            new_restore = old_restore - (alpha * delta_L_norm)
            new_restore = max(lo, min(hi, new_restore))
            self.island_tracker.params.z_decay_compound_restore = new_restore

            self.restore_trajectory.append({
                "window": frame.window,
                "restore": round(new_restore, 6),
                "delta_L": delta_L,
                "delta_L_norm": round(delta_L_norm, 6),
                "alive_links": post_links,
            })

            # Cap trajectory length for long runs
            if len(self.restore_trajectory) > 500:
                self.restore_trajectory = self.restore_trajectory[-250:]
        else:
            self.prev_alive_links = frame.alive_links

        return frame
