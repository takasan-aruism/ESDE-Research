#!/usr/bin/env python3
"""
ESDE v4.8c — Axiomatic Parameter Discovery
=============================================
Phase : v4.8c (Parameter Layer as Third Term)
Role  : Claude (Implementation)
Arch  : Gemini (+ Taka / ESDE Formal Theory) | Audit: GPT

Grounded in ESDE Formal Theory:
  Axiom T: Binary relations (Physics ↔ Topology) remain latent.
           The Parameter Layer is the Third Term (C) that closes
           the ternary loop, enabling autonomous emergence.
  Axiom L: dx/dt = -α ∇F
           Parameters move to minimize structural volatility (∇F),
           NOT toward human-defined targets.

Phase 1: Two loops only.
  Loop A: compound_restore ← ΔL (link acceleration)
  Loop B: inert_penalty    ← ΔZ0 (void acceleration)

Update frequency: every 3 windows (allow dynamics to settle).
No target values. No direct loop interaction. Coupling occurs
only through ESDE state evolution.

Physics operators: UNCHANGED.
Observation layer: UNCHANGED (v4.6 tracker + motifs).
"""

import sys, math, time
import numpy as np
from pathlib import Path
from dataclasses import dataclass

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
    """v4.8c: axiomatic parameter discovery settings."""
    # Learning rate (shared by all loops)
    drift_alpha: float = 0.0001
    # Saturation scale for tanh (controls gradient sensitivity)
    drift_scale_L: float = 1000.0    # Loop A (link acceleration)
    drift_scale_Z0: float = 500.0    # Loop B (void acceleration)
    # Parameter bounds
    drift_restore_min: float = 0.0
    drift_restore_max: float = 1.0
    drift_inert_min: float = 0.0
    drift_inert_max: float = 0.10
    # Update cadence (windows between parameter updates)
    drift_interval: int = 3
    # Enable/disable (for ablation)
    drift_enabled: bool = True


# ================================================================
# v4.8c ENGINE
# ================================================================
class V48cEngine(V48bEngine):
    """
    V48bEngine + Axiomatic Parameter Discovery.

    The Parameter Layer is the Third Term (Axiom T). It observes
    structural gradients and adjusts biology-layer parameters via
    gradient relaxation (Axiom L: dx/dt = -α ∇F).

    Two loops (Phase 1):
      A) compound_restore ← -α × tanh(ΔL / scale)
      B) inert_penalty    ← -α × tanh(ΔZ0 / scale)

    Updated every drift_interval windows. No target values.
    Destructive emergence (crashes) is permitted.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V48cEncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        # State tracking for gradient computation
        self.prev_alive_links = 0
        self.prev_z0_links = 0
        # Trajectory log
        self.drift_trajectory = []
        self.last_isum = {}
        # Window counter for update cadence
        self._drift_window_counter = 0

    def _count_z0_links(self):
        """Count alive links where at least one endpoint is Z=0."""
        count = 0
        for lk in self.state.alive_l:
            if int(self.state.Z[lk[0]]) == 0 or int(self.state.Z[lk[1]]) == 0:
                count += 1
        return count

    def step_window(self, steps=V48C_WINDOW):
        """
        Run v4.8b step_window, then apply axiomatic parameter drift.

        First window records baseline only (no drift applied).
        Drift updates occur every drift_interval windows thereafter.
        """
        # ── Full v4.8b physics + observation ──
        # last_isum is set by V48bEngine.step_window() via parent chain.
        frame = super().step_window(steps=steps)

        # ── v4.8c: Axiomatic parameter drift ──
        if not self.island_tracker.params.drift_enabled:
            self.prev_alive_links = frame.alive_links
            self.prev_z0_links = self._count_z0_links()
            return frame

        post_links = frame.alive_links
        post_z0 = self._count_z0_links()

        # Compute gradients (∇F = structural volatility)
        # delta is net change since LAST DRIFT APPLICATION,
        # not since last window. This allows dynamics to settle
        # over the full interval before measuring net effect.
        if self.prev_alive_links > 0:
            delta_L = post_links - self.prev_alive_links
        else:
            delta_L = 0  # first window: set baseline
            self.prev_alive_links = post_links

        if self.prev_z0_links > 0:
            delta_Z0 = post_z0 - self.prev_z0_links
        else:
            delta_Z0 = 0  # first window: set baseline
            self.prev_z0_links = post_z0

        # Check update cadence
        self._drift_window_counter += 1
        applied = False

        if self._drift_window_counter >= self.island_tracker.params.drift_interval:
            self._drift_window_counter = 0
            applied = True

            p = self.island_tracker.params
            alpha = p.drift_alpha

            # Loop A: compound_restore ← -α × tanh(ΔL / scale)
            grad_L = math.tanh(delta_L / p.drift_scale_L)
            old_restore = p.z_decay_compound_restore
            new_restore = old_restore - (alpha * grad_L)
            new_restore = max(p.drift_restore_min,
                              min(p.drift_restore_max, new_restore))
            p.z_decay_compound_restore = new_restore

            # Loop B: inert_penalty ← -α × tanh(ΔZ0 / scale)
            grad_Z0 = math.tanh(delta_Z0 / p.drift_scale_Z0)
            old_inert = p.z_decay_inert_penalty
            new_inert = old_inert - (alpha * grad_Z0)
            new_inert = max(p.drift_inert_min,
                            min(p.drift_inert_max, new_inert))
            p.z_decay_inert_penalty = new_inert

            # Update baseline ONLY on drift application
            # Next interval measures net change from this point
            self.prev_alive_links = post_links
            self.prev_z0_links = post_z0

        # Log trajectory (every window, regardless of update)
        p = self.island_tracker.params
        self.drift_trajectory.append({
            "window": frame.window,
            "compound_restore": round(p.z_decay_compound_restore, 6),
            "inert_penalty": round(p.z_decay_inert_penalty, 6),
            "delta_L": delta_L,
            "delta_Z0": delta_Z0,
            "grad_L": round(math.tanh(delta_L / p.drift_scale_L), 6),
            "grad_Z0": round(math.tanh(delta_Z0 / p.drift_scale_Z0), 6),
            "alive_links": post_links,
            "z0_links": post_z0,
            "applied": applied,
        })

        # Cap trajectory for long runs
        if len(self.drift_trajectory) > 500:
            self.drift_trajectory = self.drift_trajectory[-250:]

        return frame
