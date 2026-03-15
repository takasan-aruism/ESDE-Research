#!/usr/bin/env python3
"""
ESDE v4.4 — Observation Layer Upgrade (Whirlpool Identity)
=============================================================
Phase : v4.4 Identity Persistence Resolution
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

ZERO PHYSICS CHANGES from v4.3. Observation-only upgrade.

Two changes:
  1. WHIRLPOOL METRIC: Cluster identity = topological center proximity
     (1-2 hop neighborhood on substrate), NOT node-set overlap.
  2. HIGH-SPEED OBSERVATION: Window 200 → 50 steps. 100 windows.

Principle: "Structure first, meaning later."
"""

import sys, math, time, hashlib
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent        # v44/
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent  # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v43_engine import (
    V43Engine, EncapsulationParams, MotifParams, SemanticPressureParams,
    compute_density_ratio, compute_inner_entropy, find_inner_motifs,
    find_islands_sets, build_substrate,
)

# ================================================================
# v4.4 CONSTANTS
# ================================================================
V44_WINDOW = 50   # down from 200

@dataclass
class V44EncapsulationParams(EncapsulationParams):
    """v4.4: adds whirlpool_hops to v4.3 params."""
    whirlpool_hops: int = 2


# ================================================================
# v4.4 ISLAND STATE (adds center_node)
# ================================================================
@dataclass
class V44IslandState:
    island_id: str
    nodes: frozenset
    boundary_nodes: frozenset
    interior_nodes: frozenset
    center_node: int                    # topological center of mass
    born_window: int
    encapsulated_window: int = 0
    last_seen_window: int = 0
    seen_count: int = 1
    density_ratio: float = 0.0
    inner_entropy: float = 0.0
    inner_motif_counts: dict = field(default_factory=dict)
    status: str = "candidate"


# ================================================================
# v4.4 WHIRLPOOL TRACKER
# ================================================================
class WhirlpoolTracker:
    """
    Cluster identity via topological center proximity.

    Center = highest internal-degree node (S >= s_internal).
    Match = any node in new cluster within whirlpool_hops of
            previous center on substrate grid.

    Clusters can fully metabolize while preserving identity.
    """

    def __init__(self, params=None, motif_params=None, substrate=None):
        self.params = params or EncapsulationParams()
        self.motif_params = motif_params or MotifParams()
        self.substrate = substrate or {}
        self.islands: dict[str, V44IslandState] = {}
        self.graveyard: dict[str, V44IslandState] = {}
        self.next_id = 0
        self.window = 0
        self.encapsulation_events = 0
        self.dissolution_events = 0
        self.motif_history: dict[str, list[dict]] = {}

    def _new_id(self):
        self.next_id += 1
        return f"ISL{self.next_id:04d}"

    def _find_center(self, state, nodes):
        """Highest internal-degree node at S >= s_internal."""
        best = -1; best_deg = -1
        s_thr = self.params.s_internal
        for n in nodes:
            if n not in state.alive_n: continue
            deg = sum(1 for nb in state.neighbors(n)
                      if nb in nodes and nb in state.alive_n
                      and state.key(n, nb) in state.alive_l
                      and state.S[state.key(n, nb)] >= s_thr)
            if deg > best_deg:
                best_deg = deg; best = n
        return best

    def _neighborhood(self, center, hops):
        """All substrate nodes within N hops of center."""
        if center < 0: return set()
        visited = {center}; frontier = [center]
        for _ in range(hops):
            nxt = []
            for n in frontier:
                for nb in self.substrate.get(n, []):
                    if nb not in visited:
                        visited.add(nb); nxt.append(nb)
            frontier = nxt
        return visited

    def step(self, state, hardening, precomputed_islands=None):
        self.window += 1
        if precomputed_islands is not None:
            raw = precomputed_islands
        else:
            raw = find_islands_sets(state, self.params.s_threshold)
        current = [frozenset(isl) for isl in raw
                    if len(isl) >= self.params.min_cluster_size]

        # Pre-compute center neighborhoods
        active_hoods = {iid: self._neighborhood(info.center_node,
                        self.params.whirlpool_hops)
                        for iid, info in self.islands.items()
                        if info.center_node >= 0}
        grave_hoods = {gid: self._neighborhood(info.center_node,
                       self.params.whirlpool_hops)
                       for gid, info in self.graveyard.items()
                       if info.center_node >= 0}

        matched_old = set(); new_islands = {}

        for nodes in current:
            ratio, _, _, boundary = compute_density_ratio(
                state, nodes, self.params.s_internal)
            interior = nodes - boundary
            center = self._find_center(state, nodes)

            # Whirlpool match: active
            best_id = None
            for iid, hood in active_hoods.items():
                if iid in matched_old: continue
                if nodes & hood:  # any overlap with neighborhood
                    best_id = iid; break

            # Whirlpool match: graveyard
            if best_id is None:
                for gid, hood in grave_hoods.items():
                    if nodes & hood:
                        best_id = gid; break

            if best_id and best_id in self.islands:
                old = self.islands[best_id]; matched_old.add(best_id)
                ns = V44IslandState(
                    island_id=best_id, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    center_node=center,
                    born_window=old.born_window,
                    encapsulated_window=old.encapsulated_window,
                    last_seen_window=self.window,
                    seen_count=old.seen_count + 1,
                    density_ratio=ratio, status=old.status)

                if old.status == "candidate":
                    if (ratio >= self.params.ratio_threshold and
                            ns.seen_count >= self.params.min_persistence):
                        ns.status = "encapsulated"
                        ns.encapsulated_window = self.window
                        self.encapsulation_events += 1
                        self._harden_boundary(state, boundary, hardening)
                elif old.status == "encapsulated":
                    if ratio < self.params.dissolution_threshold:
                        ns.status = "dissolved"
                        self.dissolution_events += 1
                    else:
                        self._harden_boundary(state, boundary, hardening)

                if ns.status == "encapsulated" and interior:
                    ns.inner_entropy = compute_inner_entropy(state, interior)
                    ns.inner_motif_counts = find_inner_motifs(
                        state, interior, self.params.s_internal,
                        self.motif_params.motif_sizes)
                    self.motif_history.setdefault(best_id, []).append(
                        ns.inner_motif_counts.copy())

                new_islands[best_id] = ns

            elif best_id and best_id in self.graveyard:
                old = self.graveyard.pop(best_id)
                ns = V44IslandState(
                    island_id=best_id, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    center_node=center,
                    born_window=old.born_window,
                    last_seen_window=self.window,
                    seen_count=old.seen_count + 1,
                    density_ratio=ratio, status="candidate")
                new_islands[best_id] = ns

            else:
                iid = self._new_id()
                ns = V44IslandState(
                    island_id=iid, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    center_node=center,
                    born_window=self.window, last_seen_window=self.window,
                    density_ratio=ratio, status="candidate")
                new_islands[iid] = ns

        for iid in self.islands:
            if iid not in matched_old:
                self.graveyard[iid] = self.islands[iid]
        self.graveyard = {k: v for k, v in self.graveyard.items()
                          if self.window - v.last_seen_window <= 10}
        self.islands = new_islands
        self._decay_hardening(hardening)
        return self._summary()

    def _harden_boundary(self, state, boundary, hardening):
        b = self.params.boundary_hardening_bonus
        for n in boundary:
            if n not in state.alive_n: continue
            for nb in state.neighbors(n):
                if nb in state.alive_n:
                    lk = state.key(n, nb)
                    if lk in state.alive_l:
                        hardening[lk] = min(hardening.get(lk, 0) + b, 0.2)

    def _decay_hardening(self, hardening):
        d = self.params.boundary_hardening_decay
        dead = [k for k, v in hardening.items() if v - d <= 0]
        for k in dead: del hardening[k]
        for k in hardening: hardening[k] -= d

    def _summary(self):
        enc = [i for i in self.islands.values() if i.status == "encapsulated"]
        sizes = [len(i.nodes) for i in self.islands.values()]
        drs = [i.density_ratio for i in self.islands.values()]
        ie = [i.inner_entropy for i in enc if i.inner_entropy > 0]
        total_tri = sum(i.inner_motif_counts.get((2,2,2), 0) for i in enc)
        motif_rec = 0
        for iid, hist in self.motif_history.items():
            if len(hist) >= 2:
                last, prev = hist[-1], hist[-2]
                for sig in last:
                    if sig in prev and last[sig] > 0 and prev[sig] > 0:
                        motif_rec += 1
        return {
            "n_clusters": len(self.islands),
            "n_encapsulated": len(enc),
            "n_candidates": len(self.islands) - len(enc),
            "max_size": max(sizes) if sizes else 0,
            "mean_density_ratio": round(float(np.mean(drs)), 4) if drs else 0,
            "max_density_ratio": round(float(max(drs)), 4) if drs else 0,
            "encap_events": self.encapsulation_events,
            "dissolve_events": self.dissolution_events,
            "mean_inner_entropy": round(float(np.mean(ie)), 4) if ie else 0,
            "max_inner_entropy": round(float(max(ie)), 4) if ie else 0,
            "total_inner_tri": total_tri,
            "motif_recurrence": motif_rec,
            "max_seen_count": max((i.seen_count for i in self.islands.values()),
                                  default=0),
        }


# ================================================================
# v4.4 ENGINE
# ================================================================
class V44Engine(V43Engine):
    """V43Engine with WhirlpoolTracker and configurable window size."""

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V44EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        # Replace v4.3 tracker with v4.4 whirlpool tracker
        self.island_tracker = WhirlpoolTracker(
            params=params,
            motif_params=MotifParams(),
            substrate=self.substrate,
        )
