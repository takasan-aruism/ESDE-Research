#!/usr/bin/env python3
"""
ESDE v4.5a — Local Observer Logging (Deformation-Tolerant Identity)
=====================================================================
Phase : v4.5a Observation Layer Upgrade
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

ZERO PHYSICS CHANGES from v4.4. Observation-only upgrade.

Four new observation systems:
  A. PERSONALITY SIGNATURE: When a shell reaches seen_count >= 3,
     record its internal structural fingerprint (degree dist, phase
     distribution, phase coherence, density).
  B. DEFORMATION-TOLERANT IDENTITY: Track node turnover at boundary,
     structural continuity score across windows, and max lifespan
     under continuous deformation (A → A' → A'').
  C. NATURAL BOUNDARY RESONANCE LOGGING: For each boundary interaction,
     log phase difference between shell boundary and external node,
     and whether the node becomes incorporated at the next window.
     No rule biases incorporation — purely observational.
  D. SEPARATION PARADOX MONITOR: Per-cluster DR logging to track
     whether Type P (persistent) and Type D (dense) populations
     show any natural convergence.

GPT Audit constraints:
  - Physics engine unchanged.
  - No attractive forces or active incorporation rules.
  - No rule biases node attachment or shell growth.
  - All new logic is observational and logging-only.

Principle: "Structure first, meaning later."
"""

import sys, math
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent        # v45a/
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent  # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V44_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# engine_accel MUST be imported before any engine modules (Implementation Memo §6)
import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v44_engine import (
    V44Engine, V44EncapsulationParams, V44_WINDOW,
    WhirlpoolTracker,
)
from esde_v43_engine import (
    MotifParams,
)

# ================================================================
# v4.5a CONSTANTS
# ================================================================
V45A_WINDOW = V44_WINDOW  # 50 steps — same high-speed observation as v4.4


# ================================================================
# v4.5a PARAMETERS
# ================================================================
@dataclass
class V45aEncapsulationParams(V44EncapsulationParams):
    """v4.5a: adds observation thresholds to v4.4 params."""
    resonance_threshold: float = 0.7854  # π/4 radians; |Δθ| < this → resonant
    personality_trigger_seen: int = 3     # record personality at seen_count >= N
    deformation_history_len: int = 20     # max continuity scores to retain


# ================================================================
# PHASE UTILITIES
# ================================================================
def _phase_diff(theta1, theta2):
    """Circular phase difference in [0, π]."""
    d = abs(float(theta1) - float(theta2)) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def _phase_coherence(thetas):
    """Kuramoto order parameter |<e^{iθ}>| ∈ [0, 1]."""
    if len(thetas) < 2:
        return 0.0
    arr = np.array(thetas, dtype=float)
    return float(abs(np.mean(np.exp(1j * arr))))


# ================================================================
# v4.5a TRACKER
# ================================================================
class V45aTracker(WhirlpoolTracker):
    """
    Extends WhirlpoolTracker with four observation-only systems.

    Architecture: call super().step() for all physics-coupled island
    tracking, then overlay v4.5a observation logging on the resulting
    island states. All v4.5a data stored in separate dicts keyed by
    island_id — parent's V44IslandState objects are never modified.
    """

    def __init__(self, params, motif_params, substrate):
        super().__init__(params=params, motif_params=motif_params,
                         substrate=substrate)
        # A. Personality signatures  {iid: {signature dict}}
        self.personalities = {}

        # B. Deformation tracking  {iid: {cumulative_turnover, ...}}
        self.deformation = {}

        # C. Boundary resonance  {iid: {resonant_in, dissonant_in, ...}}
        self.resonance_stats = {}
        # Candidates from previous window for resonance resolution
        self._prev_boundary_candidates = {}   # {iid: {ext_node: min_phase_diff}}

        # D. Per-cluster DR history  {iid: [float]}
        self.dr_per_cluster = {}

        # System-level Separation Paradox tracking
        self.pd_events = []    # [{window, iid, is_P, is_D}]

        # Internal state for deformation
        self._prev_island_nodes = {}     # {iid: frozenset}
        self._prev_island_boundary = {}  # {iid: frozenset}

    # ────────────────────────────────────────────────────────────
    # MAIN STEP (observation wrapper around parent)
    # ────────────────────────────────────────────────────────────
    def step(self, state, hardening, precomputed_islands=None):
        """
        Run parent WhirlpoolTracker.step(), then overlay v4.5a logging.
        Returns standard isum dict (backward compatible).
        """
        # Save pre-step island state for deformation comparison
        pre_nodes = {iid: info.nodes for iid, info in self.islands.items()}
        pre_boundary = {iid: info.boundary_nodes
                        for iid, info in self.islands.items()}

        # ── Parent step (island matching, DR, encapsulation check) ──
        isum = super().step(state, hardening, precomputed_islands)

        # ── A. Resolve boundary resonance from PREVIOUS window ──
        self._resolve_resonance(state)

        # ── B. Per-island observation ──
        for iid, info in self.islands.items():
            # Deformation tracking
            self._track_deformation(iid, info, pre_nodes, pre_boundary)

            # Per-cluster DR history
            if iid not in self.dr_per_cluster:
                self.dr_per_cluster[iid] = []
            self.dr_per_cluster[iid].append(round(info.density_ratio, 4))
            # Cap history length
            if len(self.dr_per_cluster[iid]) > 50:
                self.dr_per_cluster[iid] = self.dr_per_cluster[iid][-50:]

            # Personality signature
            self._maybe_record_personality(iid, info, state)

            # P/D classification
            self._classify_pd(iid, info)

        # ── C. Record boundary candidates for NEXT window's resonance ──
        self._record_boundary_candidates(state)

        # ── D. Update prev state ──
        self._prev_island_nodes = {
            iid: info.nodes for iid, info in self.islands.items()}
        self._prev_island_boundary = {
            iid: info.boundary_nodes for iid, info in self.islands.items()}

        # ── Prune dead island data ──
        self._prune_observation_data()

        return isum

    # ────────────────────────────────────────────────────────────
    # A. PERSONALITY SIGNATURE
    # ────────────────────────────────────────────────────────────
    def _maybe_record_personality(self, iid, info, state):
        """Record structural fingerprint when persistence threshold is met."""
        trigger = self.params.personality_trigger_seen
        if info.seen_count < trigger:
            return
        if iid in self.personalities:
            # Already recorded; update if island is still alive
            # (re-record periodically to track evolution)
            if self.window % 10 != 0:
                return

        s_thr = self.params.s_internal  # 0.30

        # Internal degree distribution (strong links only)
        degrees = []
        for n in info.nodes:
            if n not in state.alive_n:
                continue
            deg = 0
            for nb in state.neighbors(n):
                if nb in info.nodes and nb in state.alive_n:
                    lk = state.key(n, nb)
                    if lk in state.alive_l and state.S[lk] >= s_thr:
                        deg += 1
            degrees.append(deg)

        # Phase distribution
        thetas = [float(state.theta[n]) for n in info.nodes
                  if n in state.alive_n]

        self.personalities[iid] = {
            "node_count": len(info.nodes),
            "interior_count": len(info.interior_nodes),
            "boundary_count": len(info.boundary_nodes),
            "degree_mean": round(float(np.mean(degrees)), 3) if degrees else 0.0,
            "degree_std": round(float(np.std(degrees)), 3) if degrees else 0.0,
            "degree_max": max(degrees) if degrees else 0,
            "phase_mean": round(float(np.mean(thetas)), 4) if thetas else 0.0,
            "phase_std": round(float(np.std(thetas)), 4) if thetas else 0.0,
            "phase_coherence": round(_phase_coherence(thetas), 4),
            "density_ratio": round(info.density_ratio, 4),
            "seen_count": info.seen_count,
            "window_recorded": self.window,
        }

    # ────────────────────────────────────────────────────────────
    # B. DEFORMATION-TOLERANT IDENTITY TRACKING
    # ────────────────────────────────────────────────────────────
    def _track_deformation(self, iid, info, pre_nodes, pre_boundary):
        """Track node turnover and structural continuity."""
        if iid not in self.deformation:
            self.deformation[iid] = {
                "cumulative_turnover": 0,
                "max_turnover_rate": 0.0,
                "continuity_scores": [],
                "lifespan_windows": 0,
                "boundary_turnover_total": 0,
            }

        d = self.deformation[iid]
        d["lifespan_windows"] = info.seen_count

        if iid not in pre_nodes:
            # Newly born island — no deformation to track yet
            return

        old_nodes = pre_nodes[iid]
        old_boundary = pre_boundary.get(iid, frozenset())

        # Node-set turnover
        gained = info.nodes - old_nodes
        lost = old_nodes - info.nodes
        turnover = len(gained) + len(lost)
        union_size = len(old_nodes | info.nodes)
        continuity = 1.0 - (turnover / max(union_size, 1))
        turnover_rate = turnover / max(len(old_nodes), 1)

        d["cumulative_turnover"] += turnover
        d["max_turnover_rate"] = max(d["max_turnover_rate"], turnover_rate)
        d["continuity_scores"].append(round(continuity, 4))

        # Cap history length
        max_len = self.params.deformation_history_len
        if len(d["continuity_scores"]) > max_len:
            d["continuity_scores"] = d["continuity_scores"][-max_len:]

        # Boundary-specific turnover
        bnd_gained = info.boundary_nodes - old_boundary
        bnd_lost = old_boundary - info.boundary_nodes
        d["boundary_turnover_total"] += len(bnd_gained) + len(bnd_lost)

    # ────────────────────────────────────────────────────────────
    # C. NATURAL BOUNDARY RESONANCE LOGGING
    # ────────────────────────────────────────────────────────────
    def _record_boundary_candidates(self, state):
        """
        For each island, find external alive-link neighbors of boundary
        nodes and record their phase difference. These become candidates
        for resonance resolution at the NEXT window.
        """
        self._prev_boundary_candidates = {}

        for iid, info in self.islands.items():
            candidates = {}  # {ext_node: min_phase_diff}
            for n in info.boundary_nodes:
                if n not in state.alive_n:
                    continue
                n_theta = state.theta[n]
                for nb in state.neighbors(n):
                    if nb in state.alive_n and nb not in info.nodes:
                        diff = _phase_diff(n_theta, state.theta[nb])
                        # Keep minimum phase diff if ext_node touches
                        # multiple boundary nodes
                        if nb not in candidates or diff < candidates[nb]:
                            candidates[nb] = diff
            if candidates:
                self._prev_boundary_candidates[iid] = candidates

    def _resolve_resonance(self, state):
        """
        Check previous window's boundary candidates against current islands.
        If an external node is now inside the same island → incorporated.
        Otherwise → rejected.
        """
        thr = self.params.resonance_threshold

        for iid, candidates in self._prev_boundary_candidates.items():
            if iid not in self.resonance_stats:
                self.resonance_stats[iid] = {
                    "resonant_in": 0,
                    "dissonant_in": 0,
                    "resonant_out": 0,
                    "dissonant_out": 0,
                    "total_events": 0,
                }
            rs = self.resonance_stats[iid]

            # Check if the island still exists with the same id
            current_nodes = self.islands[iid].nodes if iid in self.islands else frozenset()

            for ext_node, phase_diff in candidates.items():
                is_resonant = phase_diff < thr
                incorporated = ext_node in current_nodes

                rs["total_events"] += 1
                if is_resonant and incorporated:
                    rs["resonant_in"] += 1
                elif is_resonant and not incorporated:
                    rs["resonant_out"] += 1
                elif not is_resonant and incorporated:
                    rs["dissonant_in"] += 1
                else:
                    rs["dissonant_out"] += 1

    # ────────────────────────────────────────────────────────────
    # D. SEPARATION PARADOX MONITOR
    # ────────────────────────────────────────────────────────────
    def _classify_pd(self, iid, info):
        """Classify island as Type P, Type D, both, or neither."""
        is_P = info.seen_count >= 3
        is_D = info.density_ratio >= self.params.ratio_threshold  # 1.5

        self.pd_events.append({
            "window": self.window,
            "iid": iid,
            "is_P": bool(is_P),
            "is_D": bool(is_D),
            "seen_count": info.seen_count,
            "density_ratio": round(info.density_ratio, 4),
        })

        # Cap events list to prevent unbounded growth
        if len(self.pd_events) > 5000:
            self.pd_events = self.pd_events[-5000:]

    # ────────────────────────────────────────────────────────────
    # CLEANUP
    # ────────────────────────────────────────────────────────────
    def _prune_observation_data(self):
        """Remove v4.5a data for islands no longer active or in graveyard."""
        keep = set(self.islands.keys()) | set(self.graveyard.keys())
        for store in [self.deformation, self.dr_per_cluster,
                      self.resonance_stats, self.personalities]:
            for k in list(store):
                if k not in keep:
                    del store[k]

    # ────────────────────────────────────────────────────────────
    # EXTENDED SUMMARY
    # ────────────────────────────────────────────────────────────
    def _summary(self):
        """
        Backward-compatible summary (all v4.4 keys preserved) plus
        v4.5a observation fields.
        """
        base = super()._summary()

        # v4.5a: Deformation metrics
        lifespans = [d["lifespan_windows"] for d in self.deformation.values()]
        all_continuity = []
        for d in self.deformation.values():
            all_continuity.extend(d["continuity_scores"])
        max_turnover_rates = [d["max_turnover_rate"]
                              for d in self.deformation.values()]

        base["max_lifespan"] = max(lifespans) if lifespans else 0
        base["mean_continuity"] = (round(float(np.mean(all_continuity)), 4)
                                   if all_continuity else 0.0)
        base["max_continuity"] = (round(float(max(all_continuity)), 4)
                                  if all_continuity else 0.0)
        base["mean_turnover_rate"] = (round(float(np.mean(max_turnover_rates)), 4)
                                      if max_turnover_rates else 0.0)

        # v4.5a: Boundary resonance aggregates
        total_res_in = sum(rs["resonant_in"]
                           for rs in self.resonance_stats.values())
        total_dis_in = sum(rs["dissonant_in"]
                           for rs in self.resonance_stats.values())
        total_res_out = sum(rs["resonant_out"]
                            for rs in self.resonance_stats.values())
        total_dis_out = sum(rs["dissonant_out"]
                            for rs in self.resonance_stats.values())
        total_events = total_res_in + total_dis_in + total_res_out + total_dis_out

        base["resonant_incorporations"] = total_res_in
        base["dissonant_incorporations"] = total_dis_in
        base["resonant_rejections"] = total_res_out
        base["dissonant_rejections"] = total_dis_out
        base["resonance_total_events"] = total_events

        incorporations = total_res_in + total_dis_in
        if incorporations > 0:
            base["resonance_ratio"] = round(total_res_in / incorporations, 4)
        else:
            base["resonance_ratio"] = 0.0

        # v4.5a: P/D paradox — current-window snapshot
        current_pd = [e for e in self.pd_events if e["window"] == self.window]
        base["pd_p_count"] = sum(1 for e in current_pd if e["is_P"])
        base["pd_d_count"] = sum(1 for e in current_pd if e["is_D"])
        base["pd_both_count"] = sum(1 for e in current_pd
                                    if e["is_P"] and e["is_D"])

        # v4.5a: Personality signatures recorded
        base["personalities_recorded"] = len(self.personalities)

        return base

    # ────────────────────────────────────────────────────────────
    # DETAILED REPORT (for JSON dump)
    # ────────────────────────────────────────────────────────────
    def detailed_report(self):
        """Full v4.5a observation data for JSON serialization."""
        return {
            "personalities": dict(self.personalities),
            "deformation": {
                iid: {
                    "cumulative_turnover": d["cumulative_turnover"],
                    "max_turnover_rate": d["max_turnover_rate"],
                    "mean_continuity": (round(float(np.mean(d["continuity_scores"])), 4)
                                        if d["continuity_scores"] else 0.0),
                    "lifespan_windows": d["lifespan_windows"],
                    "boundary_turnover_total": d["boundary_turnover_total"],
                }
                for iid, d in self.deformation.items()
            },
            "resonance_per_island": dict(self.resonance_stats),
            "dr_per_cluster": {
                iid: vals for iid, vals in self.dr_per_cluster.items()
            },
            "pd_convergence_summary": {
                "total_both_events": sum(
                    1 for e in self.pd_events if e["is_P"] and e["is_D"]),
                "total_p_events": sum(1 for e in self.pd_events if e["is_P"]),
                "total_d_events": sum(1 for e in self.pd_events if e["is_D"]),
                "unique_both_islands": len(set(
                    e["iid"] for e in self.pd_events
                    if e["is_P"] and e["is_D"])),
            },
        }


# ================================================================
# v4.5a ENGINE
# ================================================================
class V45aEngine(V44Engine):
    """V44Engine with V45aTracker. Zero physics changes."""

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V45aEncapsulationParams()
        # Call V44Engine.__init__ which calls V43Engine.__init__
        # V44Engine.__init__ will create a WhirlpoolTracker, which we
        # immediately replace below.
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        # Replace tracker with v4.5a extended version
        self.island_tracker = V45aTracker(
            params=params,
            motif_params=MotifParams(),
            substrate=self.substrate,
        )
