#!/usr/bin/env python3
"""
ESDE v4.6 — Dynamic Identity & Motif Observation
===================================================
Phase : v4.6 Observation Layer Overhaul
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

ZERO PHYSICS CHANGES. Observation + tracking layer only.

Two upgrades:
  1. DYNAMIC IDENTITY TRACKING: Island identity uses Jaccard
     similarity (configurable threshold, default 0.3) instead
     of strict node-set equality. Clusters that mutate nodes
     at their boundary are classified as "identity_drift" not
     "dissolution". Both strict_lifespan and relaxed_lifespan
     are tracked simultaneously.

  2. MOTIF SCANNER: Real-time detection of topological motifs
     within the active graph (S >= s_internal):
       Alpha (3-cycle / triangle)
       Beta  (3-cycle + degree-1 whisker)
       Gamma (4-cycle / square)
     Motif gain/loss logged at each identity drift event.
     Purely observational — does NOT influence physics.

Principle: "Structure first, meaning later."
"""

import sys, math
import numpy as np
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent        # v46/
_V45B_DIR = _SCRIPT_DIR.parent / "v45b"
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent  # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V45B_DIR), str(_V45A_DIR), str(_V44_DIR),
          str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v45b_engine import (
    V45bEngine, V45bEncapsulationParams,
    apply_resonance_accretion,
)
from esde_v45a_engine import (
    V45aTracker, _phase_diff, _phase_coherence,
)
from esde_v43_engine import (
    MotifParams,
    compute_density_ratio, compute_inner_entropy,
    find_islands_sets,
)
from esde_v44_engine import V44IslandState


# ================================================================
# v4.6 CONSTANTS
# ================================================================
V46_WINDOW = 50


# ================================================================
# v4.6 PARAMETERS
# ================================================================
@dataclass
class V46EncapsulationParams(V45bEncapsulationParams):
    """v4.6: adds relaxed identity + motif parameters."""
    # Dynamic identity
    jaccard_threshold: float = 0.3       # J >= this → same island
    use_jaccard_primary: bool = True     # if False, use whirlpool only
    # Motif scanner
    motif_scan_enabled: bool = True
    motif_s_threshold: float = 0.30      # link strength for motif detection


# ================================================================
# MOTIF SCANNER (read-only)
# ================================================================
def scan_motifs(state, s_thr=0.30):
    """
    Detect topological motifs in the active graph at S >= s_thr.
    Returns dict of motif counts and node sets.

    Alpha: 3-node cycle (triangle)
    Beta:  3-node cycle + 1 degree-1 appendage (whisker)
    Gamma: 4-node cycle (square)

    Purely observational — no state mutation.
    """
    # Build adjacency at threshold
    adj = defaultdict(set)
    for n in state.alive_n:
        for nb in state.neighbors(n):
            if nb in state.alive_n:
                lk = state.key(n, nb)
                if lk in state.alive_l and state.S[lk] >= s_thr:
                    adj[n].add(nb)

    # Alpha: triangles (u < v < w)
    triangles = []
    for u in adj:
        for v in adj[u]:
            if v <= u:
                continue
            common = adj[u] & adj[v]
            for w in common:
                if w > v:
                    triangles.append(frozenset({u, v, w}))

    # Gamma: chordless 4-cycles (squares) — u-v-w-x-u with no diagonal
    # Only scan if graph is small enough (< 500 nodes with edges)
    squares = set()
    if len(adj) < 500:
        for u in adj:
            for v in adj[u]:
                if v <= u:
                    continue
                for w in adj[v]:
                    if w <= u or w == u:
                        continue
                    for x in adj[w]:
                        if x <= v or x == u or x == v:
                            continue
                        if u in adj[x]:
                            # Reject if any chord exists (u-w or v-x)
                            if w in adj[u] or x in adj[v]:
                                continue
                            squares.add(frozenset({u, v, w, x}))

    tri_set = set(triangles)

    # Beta: triangle + whisker
    # A whisker node has degree 1 in adj and its single neighbor is in a triangle
    betas = []
    degree_1_nodes = [n for n in adj if len(adj[n]) == 1]
    for w_node in degree_1_nodes:
        parent = next(iter(adj[w_node]))
        # Find triangles containing parent
        for tri in tri_set:
            if parent in tri:
                betas.append({
                    "triangle": tri,
                    "whisker_node": w_node,
                    "parent_node": parent,
                })

    return {
        "alpha_count": len(triangles),
        "alpha_nodes": triangles,
        "beta_count": len(betas),
        "beta_details": betas,
        "gamma_count": len(squares),
        "gamma_nodes": squares,
    }


# ================================================================
# v4.6 ISLAND STATE (adds relaxed tracking)
# ================================================================
@dataclass
class V46IslandState:
    island_id: str
    nodes: frozenset
    boundary_nodes: frozenset
    interior_nodes: frozenset
    center_node: int
    born_window: int
    encapsulated_window: int = 0
    last_seen_window: int = 0

    # Dual lifespan
    strict_seen_count: int = 1       # legacy (exact match or whirlpool)
    relaxed_seen_count: int = 1      # new (Jaccard >= threshold)

    density_ratio: float = 0.0
    inner_entropy: float = 0.0
    inner_motif_counts: dict = field(default_factory=dict)
    status: str = "candidate"

    # Identity drift log
    identity_class: str = "new"      # new / stable / identity_drift / dissolution
    jaccard_score: float = 1.0       # J with previous window's version
    motifs_gained: list = field(default_factory=list)
    motifs_lost: list = field(default_factory=list)

    @property
    def seen_count(self):
        """Backward compatible — returns relaxed count."""
        return self.relaxed_seen_count


# ================================================================
# v4.6 DYNAMIC IDENTITY TRACKER
# ================================================================
class V46Tracker(V45aTracker):
    """
    Replaces WhirlpoolTracker's matching logic with Jaccard-based
    dynamic identity. Preserves all v4.5a observation systems.
    """

    def __init__(self, params, motif_params, substrate):
        super().__init__(params=params, motif_params=motif_params,
                         substrate=substrate)
        # Motif state per island {iid: set of motif frozensets}
        self.island_motifs = {}
        # System-level motif counts per window (v4.6 specific)
        self.system_motif_history = []

    def _jaccard(self, a, b):
        """Jaccard similarity between two frozensets."""
        if not a and not b:
            return 0.0
        return len(a & b) / len(a | b)

    def step(self, state, hardening, precomputed_islands=None):
        """
        Override: use Jaccard + whirlpool hybrid for identity matching.
        Then run v4.5a observation overlay.
        """
        # Save pre-step state for v4.5a deformation tracking
        pre_nodes = {iid: info.nodes for iid, info in self.islands.items()}
        pre_boundary = {iid: info.boundary_nodes
                        for iid, info in self.islands.items()}

        # ── Get current clusters ──
        self.window += 1
        if precomputed_islands is not None:
            raw = precomputed_islands
        else:
            raw = find_islands_sets(state, self.params.s_threshold)
        current = [frozenset(isl) for isl in raw
                    if len(isl) >= self.params.min_cluster_size]

        # ── Motif scan (system-level, before island matching) ──
        motif_data = {}
        if self.params.motif_scan_enabled:
            motif_data = scan_motifs(state, self.params.motif_s_threshold)
            self.system_motif_history.append({
                "window": self.window,
                "alpha": motif_data.get("alpha_count", 0),
                "beta": motif_data.get("beta_count", 0),
                "gamma": motif_data.get("gamma_count", 0),
            })
            if len(self.system_motif_history) > 200:
                self.system_motif_history = self.system_motif_history[-100:]

        # ── Hybrid identity matching ──
        # Pre-compute whirlpool neighborhoods (from parent)
        active_hoods = {}
        for iid, info in self.islands.items():
            if info.center_node >= 0:
                active_hoods[iid] = self._neighborhood(
                    info.center_node, self.params.whirlpool_hops)
        grave_hoods = {}
        for gid, info in self.graveyard.items():
            if info.center_node >= 0:
                grave_hoods[gid] = self._neighborhood(
                    info.center_node, self.params.whirlpool_hops)

        matched_old = set()
        new_islands = {}

        for nodes in current:
            ratio, _, _, boundary = compute_density_ratio(
                state, nodes, self.params.s_internal)
            interior = nodes - boundary
            center = self._find_center(state, nodes)

            # ── Matching: Jaccard primary, whirlpool fallback ──
            best_id = None
            best_jaccard = 0.0
            match_method = None

            if self.params.use_jaccard_primary:
                # Jaccard match against active islands
                for iid, info in self.islands.items():
                    if iid in matched_old:
                        continue
                    j = self._jaccard(nodes, info.nodes)
                    if j > best_jaccard:
                        best_jaccard = j
                        best_id = iid
                        match_method = "jaccard"

                # If Jaccard fails, try whirlpool (best-Jaccard among overlapping)
                if best_id is None or best_jaccard < self.params.jaccard_threshold:
                    wp_best_id = None
                    wp_best_j = -1.0
                    for iid, hood in active_hoods.items():
                        if iid in matched_old:
                            continue
                        if nodes & hood:
                            j = self._jaccard(nodes, self.islands[iid].nodes)
                            if j > wp_best_j:
                                wp_best_j = j
                                wp_best_id = iid
                    if wp_best_id is not None:
                        best_id = wp_best_id
                        best_jaccard = wp_best_j
                        match_method = "whirlpool"
            else:
                # Whirlpool only (legacy behavior) — best-match
                wp_best_id = None
                wp_best_j = -1.0
                for iid, hood in active_hoods.items():
                    if iid in matched_old:
                        continue
                    if nodes & hood:
                        j = self._jaccard(nodes, self.islands[iid].nodes)
                        if j > wp_best_j:
                            wp_best_j = j
                            wp_best_id = iid
                if wp_best_id is not None:
                    best_id = wp_best_id
                    best_jaccard = wp_best_j
                    match_method = "whirlpool"

            # ── Graveyard check ──
            if best_id is None or (best_jaccard < self.params.jaccard_threshold
                                   and match_method != "whirlpool"):
                # Jaccard match against graveyard — best match
                g_best_id = None
                g_best_j = 0.0
                for gid, info in self.graveyard.items():
                    j = self._jaccard(nodes, info.nodes)
                    if j >= self.params.jaccard_threshold and j > g_best_j:
                        g_best_j = j
                        g_best_id = gid
                if g_best_id is not None:
                    best_id = g_best_id
                    best_jaccard = g_best_j
                    match_method = "jaccard_grave"

                # Whirlpool fallback on graveyard — best match
                if best_id is None:
                    gw_best_id = None
                    gw_best_j = -1.0
                    for gid, hood in grave_hoods.items():
                        if nodes & hood:
                            j = self._jaccard(
                                nodes, self.graveyard[gid].nodes)
                            if j > gw_best_j:
                                gw_best_j = j
                                gw_best_id = gid
                    if gw_best_id is not None:
                        best_id = gw_best_id
                        best_jaccard = gw_best_j
                        match_method = "whirlpool_grave"

            # ── Classify identity ──
            # Per-island motifs
            island_motif_set = set()
            if motif_data:
                for tri in motif_data.get("alpha_nodes", []):
                    if tri <= nodes:  # all triangle nodes in this island
                        island_motif_set.add(("alpha", tri))
                for beta in motif_data.get("beta_details", []):
                    ext = beta["triangle"] | {beta["whisker_node"]}
                    if ext <= nodes:
                        island_motif_set.add(("beta", frozenset(ext)))
                for sq in motif_data.get("gamma_nodes", []):
                    if sq <= nodes:
                        island_motif_set.add(("gamma", sq))

            matched = (best_id is not None and
                       (best_jaccard >= self.params.jaccard_threshold
                        or match_method in ("whirlpool", "whirlpool_grave")))

            if matched and best_id in self.islands:
                old = self.islands[best_id]
                matched_old.add(best_id)

                # Determine identity class
                if best_jaccard >= 0.95:
                    id_class = "stable"
                elif best_jaccard >= self.params.jaccard_threshold:
                    id_class = "identity_drift"
                else:
                    id_class = "identity_drift"  # whirlpool fallback

                # Strict lifespan: only if J >= 0.5 (legacy-equivalent)
                strict_inc = 1 if best_jaccard >= 0.5 else 0

                # Motif diff
                old_motifs = self.island_motifs.get(best_id, set())
                gained = island_motif_set - old_motifs
                lost = old_motifs - island_motif_set

                ns = V46IslandState(
                    island_id=best_id, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    center_node=center,
                    born_window=old.born_window,
                    encapsulated_window=old.encapsulated_window,
                    last_seen_window=self.window,
                    strict_seen_count=old.strict_seen_count + strict_inc,
                    relaxed_seen_count=old.seen_count + 1,
                    density_ratio=ratio,
                    status=old.status,
                    identity_class=id_class,
                    jaccard_score=round(best_jaccard, 4),
                    motifs_gained=[str(m) for m in gained],
                    motifs_lost=[str(m) for m in lost],
                )

                # Encapsulation check
                if old.status == "candidate":
                    if (ratio >= self.params.ratio_threshold and
                            ns.relaxed_seen_count >= self.params.min_persistence):
                        ns.status = "encapsulated"
                        ns.encapsulated_window = self.window
                        self.encapsulation_events += 1
                elif old.status == "encapsulated":
                    if ratio < self.params.dissolution_threshold:
                        ns.status = "candidate"
                        self.dissolution_events += 1

                # Inner metrics for encapsulated
                if ns.status == "encapsulated":
                    ns.inner_entropy = compute_inner_entropy(state, interior)
                    ns.inner_motif_counts = {}

                new_islands[best_id] = ns
                self.island_motifs[best_id] = island_motif_set

            elif matched and best_id in self.graveyard:
                # Reformation from graveyard
                old_g = self.graveyard[best_id]
                ns = V46IslandState(
                    island_id=best_id, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    center_node=center,
                    born_window=old_g.born_window,
                    last_seen_window=self.window,
                    strict_seen_count=old_g.strict_seen_count + 1,
                    relaxed_seen_count=old_g.seen_count + 1,
                    density_ratio=ratio,
                    identity_class="reformation",
                    jaccard_score=round(best_jaccard, 4),
                )
                new_islands[best_id] = ns
                self.island_motifs[best_id] = island_motif_set
                del self.graveyard[best_id]

            else:
                # New island
                nid = self._new_id()
                ns = V46IslandState(
                    island_id=nid, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    center_node=center,
                    born_window=self.window,
                    last_seen_window=self.window,
                    density_ratio=ratio,
                    identity_class="new",
                )
                new_islands[nid] = ns
                self.island_motifs[nid] = island_motif_set

        # ── Move unmatched to graveyard ──
        for iid, info in self.islands.items():
            if iid not in matched_old:
                self.graveyard[iid] = info
        # Prune old graveyard entries
        stale = [gid for gid, g in self.graveyard.items()
                 if self.window - g.last_seen_window > 10]
        for gid in stale:
            del self.graveyard[gid]
            self.island_motifs.pop(gid, None)

        self.islands = new_islands

        # ── Hardening for encapsulated boundaries ──
        for iid, info in self.islands.items():
            if info.status == "encapsulated":
                for n in info.boundary_nodes:
                    if n not in state.alive_n:
                        continue
                    for nb in state.neighbors(n):
                        if nb in state.alive_n:
                            lk = state.key(n, nb)
                            if lk in state.alive_l:
                                hardening[lk] = min(
                                    0.5, hardening.get(lk, 0) + self.params.hardening_bonus)
        # Decay then prune (keys hitting 0 removed in same window)
        for k in list(hardening):
            hardening[k] -= self.params.hardening_decay
        dead = [k for k, v in hardening.items() if v <= 0]
        for k in dead:
            del hardening[k]

        # ── Standard isum for backward compatibility ──
        isum = self._summary()

        # ── v4.5a observation overlay ──
        self._resolve_resonance(state)
        for iid, info in self.islands.items():
            self._track_deformation(iid, info, pre_nodes, pre_boundary)
            if iid not in self.dr_per_cluster:
                self.dr_per_cluster[iid] = []
            self.dr_per_cluster[iid].append(round(info.density_ratio, 4))
            if len(self.dr_per_cluster[iid]) > 50:
                self.dr_per_cluster[iid] = self.dr_per_cluster[iid][-50:]
            self._maybe_record_personality(iid, info, state)
            self._classify_pd(iid, info)

        self._record_boundary_candidates(state)
        self._prev_island_nodes = {
            iid: info.nodes for iid, info in self.islands.items()}
        self._prev_island_boundary = {
            iid: info.boundary_nodes for iid, info in self.islands.items()}
        self._prune_observation_data()

        return isum

    # ────────────────────────────────────────────────────────────
    # EXTENDED SUMMARY (v4.6 additions)
    # ────────────────────────────────────────────────────────────
    def _summary(self):
        """Add v4.6 fields to v4.5a/b summary."""
        base = super()._summary()

        # Relaxed vs strict lifespan
        relaxed = [info.relaxed_seen_count for info in self.islands.values()]
        strict = [info.strict_seen_count for info in self.islands.values()]
        base["max_relaxed_lifespan"] = max(relaxed) if relaxed else 0
        base["max_strict_lifespan"] = max(strict) if strict else 0

        # Identity drift counts this window
        classes = [info.identity_class for info in self.islands.values()]
        base["identity_stable"] = sum(1 for c in classes if c == "stable")
        base["identity_drift"] = sum(1 for c in classes if c == "identity_drift")
        base["identity_new"] = sum(1 for c in classes if c == "new")
        base["identity_reformation"] = sum(1 for c in classes if c == "reformation")

        # Mean Jaccard this window
        jaccards = [info.jaccard_score for info in self.islands.values()
                    if info.identity_class in ("stable", "identity_drift")]
        base["mean_jaccard"] = round(float(np.mean(jaccards)), 4) if jaccards else 0.0

        # System motifs
        if self.system_motif_history:
            latest = self.system_motif_history[-1]
            base["motif_alpha"] = latest.get("alpha", 0)
            base["motif_beta"] = latest.get("beta", 0)
            base["motif_gamma"] = latest.get("gamma", 0)
        else:
            base["motif_alpha"] = 0
            base["motif_beta"] = 0
            base["motif_gamma"] = 0

        return base

    def detailed_report(self):
        """Extend v4.5a report with v4.6 data."""
        base = super().detailed_report()
        base["system_motif_history"] = self.system_motif_history[-50:]
        base["island_identity_log"] = {
            iid: {
                "identity_class": info.identity_class,
                "jaccard": info.jaccard_score,
                "relaxed_seen": info.relaxed_seen_count,
                "strict_seen": info.strict_seen_count,
                "motifs_gained": info.motifs_gained,
                "motifs_lost": info.motifs_lost,
            }
            for iid, info in self.islands.items()
        }
        return base


# ================================================================
# v4.6 ENGINE
# ================================================================
class V46Engine(V45bEngine):
    """V45bEngine with V46Tracker. Physics unchanged."""

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V46EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        # Replace tracker with v4.6 dynamic identity version
        self.island_tracker = V46Tracker(
            params=params,
            motif_params=MotifParams(),
            substrate=self.substrate,
        )
