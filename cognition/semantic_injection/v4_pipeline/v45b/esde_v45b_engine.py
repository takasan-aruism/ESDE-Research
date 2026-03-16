#!/usr/bin/env python3
"""
ESDE v4.5b — Boundary Metabolism (Resonance-Biased Accretion)
===============================================================
Phase : v4.5b (First Physics Change Since v4.3)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

FIRST PHYSICS CHANGE since v4.3 paradigm shift.

Mechanism: Resonance-Biased Boundary Accretion
  - For qualified clusters (configurable DR/seen gates), external
    nodes adjacent to cluster boundary on the substrate grid receive
    a latent field boost proportional to phase resonance.
  - resonance_factor = exp(-lambda * phase_diff)
  - Boost is applied to the latent field, which converts to active
    links through the existing RealizationOperator in subsequent
    physics steps. No link is created directly.
  - Existing link_decay, semantic pressure, and phase diffusion
    remain unchanged. This enables the metabolism cycle:
    ingestion (resonant accretion) + excretion (natural decay).

Observation: All v4.5a logging systems preserved (personality,
deformation, resonance, P/D monitor).

GPT Audit constraints satisfied:
  - Smooth, bounded, monotonic resonance function (exponential)
  - No direct link creation (works through latent field)
  - link_decay NOT weakened
  - Growth metrics logged, NOT capped

Principle: "Structure first, meaning later."
"""

import sys, math
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent        # v45b/
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent  # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V45A_DIR), str(_V44_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# engine_accel MUST be imported before any engine modules
import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v45a_engine import (
    V45aEngine, V45aEncapsulationParams, V45aTracker, V45A_WINDOW,
    _phase_diff,
)
from esde_v43_engine import MotifParams


# ================================================================
# v4.5b CONSTANTS
# ================================================================
V45B_WINDOW = V45A_WINDOW  # 50 steps


# ================================================================
# v4.5b PARAMETERS
# ================================================================
@dataclass
class V45bEncapsulationParams(V45aEncapsulationParams):
    """v4.5b: adds accretion parameters."""
    # Accretion gating (which clusters receive the boost)
    accretion_dr_gate: float = 1.0     # spec suggests 1.5; relaxed for bootstrap
    accretion_seen_gate: int = 2       # spec suggests 3; relaxed for bootstrap

    # Resonance function: factor = exp(-lambda * phase_diff)
    accretion_lambda: float = 2.0      # selectivity; at π/4: factor=0.21

    # Latent field boost magnitude for resonant pairs
    accretion_boost: float = 0.25      # added to latent field per window

    # Whether to use substrate (grid) or active-link neighbors
    # for finding external candidates. Substrate = broader reach.
    accretion_use_substrate: bool = True


# ================================================================
# RESONANCE ACCRETION (standalone function)
# ================================================================
def apply_resonance_accretion(state, tracker, substrate, params, rng):
    """
    For qualified clusters, boost latent field between boundary nodes
    and phase-resonant external neighbors on the substrate grid.

    This is the ONLY physics change in v4.5b. The boost enters the
    existing latent→active→strong pipeline via the RealizationOperator
    in subsequent physics steps.

    Args:
        state: GenesisState (live, mutable)
        tracker: V45aTracker (read-only — uses .islands for gating)
        substrate: dict (frozen grid adjacency)
        params: V45bEncapsulationParams
        rng: numpy RandomState

    Returns:
        dict with accretion stats for logging
    """
    stats = {
        "qualified_clusters": 0,
        "contact_events": 0,
        "boosts_applied": 0,
        "resonance_factors": [],
        "boosted_nodes": set(),
    }

    for iid, info in tracker.islands.items():
        # ── Gating: only qualified clusters ──
        if info.density_ratio < params.accretion_dr_gate:
            continue
        if info.seen_count < params.accretion_seen_gate:
            continue

        stats["qualified_clusters"] += 1

        # ── Cluster mean phase (circular mean) ──
        cluster_thetas = [float(state.theta[n]) for n in info.nodes
                          if n in state.alive_n]
        if len(cluster_thetas) < 2:
            continue
        mean_phase = math.atan2(
            float(np.mean(np.sin(cluster_thetas))),
            float(np.mean(np.cos(cluster_thetas)))
        ) % (2 * math.pi)

        cluster_nodes = info.nodes  # frozenset

        # ── Scan boundary → external pairs ──
        for bnd_node in info.boundary_nodes:
            if bnd_node not in state.alive_n:
                continue

            # Use substrate neighbors for candidate discovery
            if params.accretion_use_substrate:
                neighbors = substrate.get(bnd_node, [])
            else:
                neighbors = list(state.neighbors(bnd_node))

            for ext_node in neighbors:
                if ext_node not in state.alive_n:
                    continue
                if ext_node in cluster_nodes:
                    continue  # not external

                # Skip if link already exists (active)
                lk = state.key(bnd_node, ext_node)
                if lk in state.alive_l:
                    continue

                stats["contact_events"] += 1

                # ── Resonance factor ──
                phase_diff = _phase_diff(state.theta[ext_node], mean_phase)
                resonance = math.exp(-params.accretion_lambda * phase_diff)
                stats["resonance_factors"].append(round(resonance, 4))

                # ── Probabilistic latent boost ──
                # Higher resonance → higher probability of receiving boost
                if rng.random() < resonance:
                    cur_latent = state.get_latent(bnd_node, ext_node)
                    new_latent = min(1.0, cur_latent + params.accretion_boost)
                    state.set_latent(bnd_node, ext_node, new_latent)
                    stats["boosts_applied"] += 1
                    stats["boosted_nodes"].add(ext_node)

    # Convert set to count for JSON serialization
    stats["unique_boosted_nodes"] = len(stats["boosted_nodes"])
    del stats["boosted_nodes"]

    return stats


# ================================================================
# v4.5b ENGINE
# ================================================================
class V45bEngine(V45aEngine):
    """
    V45aEngine + resonance-biased boundary accretion.

    Architecture: super().step_window() runs all physics + observation.
    Then _apply_accretion() boosts latent field for qualified clusters.
    The boost takes effect in the NEXT window's physics steps.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V45bEncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        # Accretion stats per window (overwritten each call)
        self.accretion_stats = {}
        # Cumulative accretion counters
        self.total_accretion_boosts = 0
        self.total_accretion_contacts = 0

    def step_window(self, steps=V45B_WINDOW):
        """
        Run parent step_window (physics + observation + v4.5a logging),
        then apply resonance accretion for NEXT window.
        """
        # ── All physics, pressure, observation, v4.5a logging ──
        frame = super().step_window(steps=steps)

        # ── v4.5b: Resonance-biased boundary accretion ──
        self.accretion_stats = apply_resonance_accretion(
            state=self.state,
            tracker=self.island_tracker,
            substrate=self.substrate,
            params=self.island_tracker.params,
            rng=self.state.rng,
        )
        self.total_accretion_boosts += self.accretion_stats["boosts_applied"]
        self.total_accretion_contacts += self.accretion_stats["contact_events"]

        return frame
