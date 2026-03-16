#!/usr/bin/env python3
"""
ESDE v4.7 — Per-Step Boundary Accretion
==========================================
Phase : v4.7 (Physics Loop Modification)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT (Approved 2026-03-17)

PHYSICS CHANGE: Resonance-biased boundary accretion moved from
once-per-window (v4.5b) to per-step within the physics loop.

Mechanism:
  Every scan_interval steps (default 5), scan all clusters with
  size >= 3. For each boundary node's substrate neighbors that are
  external and lack an active link, compute resonance factor and
  probabilistically boost the latent field.

  per_step_boost = 0.01 (vs v4.5b's 0.25 once/window)
  scan_interval  = 5    (10 scans per 50-step window)
  max_latent_cap = 0.5  (cumulative cap per node-pair per window)
  gate           = cluster_size >= 3 only (no DR/seen gate)

All other physics operators: UNCHANGED.
link_decay: UNCHANGED.
Observation layer: v4.6 (dynamic identity + motif scanner).

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
_SCRIPT_DIR = Path(__file__).resolve().parent        # v47/
_V46_DIR = _SCRIPT_DIR.parent / "v46"
_V45B_DIR = _SCRIPT_DIR.parent / "v45b"
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent  # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V46_DIR), str(_V45B_DIR), str(_V45A_DIR),
          str(_V44_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v46_engine import (
    V46Engine, V46EncapsulationParams, V46Tracker, V46_WINDOW,
    scan_motifs,
)
from esde_v45a_engine import _phase_diff
from esde_v43_engine import (
    MotifParams, SemanticPressureParams,
    apply_semantic_pressure, find_islands_sets,
    V43StateFrame, evaluate_milestones,
    WINDOW,
)
from esde_v41_engine import MIN_C_NODES_FOR_VALID, N_REGIONS
from v19g_canon import (
    K_LEVELS, BASE_PARAMS, BIAS,
    compute_J, select_k_star,
)


# ================================================================
# v4.7 CONSTANTS
# ================================================================
V47_WINDOW = V46_WINDOW  # 50 steps


# ================================================================
# v4.7 PARAMETERS
# ================================================================
@dataclass
class V47EncapsulationParams(V46EncapsulationParams):
    """v4.7: adds per-step accretion parameters."""
    perstep_boost: float = 0.01       # latent boost per scan event
    perstep_scan_interval: int = 5    # steps between scans
    perstep_max_latent: float = 0.5   # cumulative cap per pair per window
    perstep_min_cluster: int = 3      # minimum cluster size (no DR/seen gate)


# ================================================================
# PER-STEP BOUNDARY SCAN (the v4.7 physics change)
# ================================================================
def per_step_boundary_scan(state, tracker, substrate, params, rng,
                           latent_accumulator):
    """
    Scan all qualified cluster boundaries and boost latent field
    for phase-resonant external neighbors.

    Called every scan_interval steps WITHIN the physics loop.
    Uses the tracker's current island state (updated at previous
    window end, so islands are 1 window stale — this is intentional
    to avoid per-step island detection overhead).

    Args:
        state: GenesisState (live, mutable)
        tracker: V46Tracker (read-only for island positions)
        substrate: frozen grid adjacency
        params: V47EncapsulationParams
        rng: numpy RandomState
        latent_accumulator: dict {(n1,n2): cumulative_boost_this_window}

    Returns:
        dict with scan stats
    """
    stats = {"scans": 0, "boosts": 0, "contacts": 0}

    for iid, info in tracker.islands.items():
        if len(info.nodes) < params.perstep_min_cluster:
            continue

        # Cluster mean phase (circular mean)
        cluster_thetas = [float(state.theta[n]) for n in info.nodes
                          if n in state.alive_n]
        if len(cluster_thetas) < 2:
            continue
        mean_phase = math.atan2(
            float(np.mean(np.sin(cluster_thetas))),
            float(np.mean(np.cos(cluster_thetas)))
        ) % (2 * math.pi)

        cluster_nodes = info.nodes

        for bnd_node in info.boundary_nodes:
            if bnd_node not in state.alive_n:
                continue
            for ext_node in substrate.get(bnd_node, []):
                if ext_node not in state.alive_n:
                    continue
                if ext_node in cluster_nodes:
                    continue

                lk = state.key(bnd_node, ext_node)
                if lk in state.alive_l:
                    continue  # link already active

                stats["contacts"] += 1

                # Cumulative cap check
                pair = (min(bnd_node, ext_node), max(bnd_node, ext_node))
                if latent_accumulator.get(pair, 0) >= params.perstep_max_latent:
                    continue

                # Resonance factor
                phase_diff = _phase_diff(state.theta[ext_node], mean_phase)
                resonance = math.exp(-params.accretion_lambda * phase_diff)

                if rng.random() < resonance:
                    cur = state.get_latent(bnd_node, ext_node)
                    new_val = min(1.0, cur + params.perstep_boost)
                    state.set_latent(bnd_node, ext_node, new_val)
                    latent_accumulator[pair] = (
                        latent_accumulator.get(pair, 0) + params.perstep_boost)
                    stats["boosts"] += 1

    stats["scans"] = 1
    return stats


# ================================================================
# v4.7 ENGINE
# ================================================================
class V47Engine(V46Engine):
    """
    V46Engine with per-step boundary accretion inside the physics loop.

    Overrides step_window to replicate V43Engine's physics loop with
    the per-step scan inserted after background seeding. Post-loop
    observation code is identical to V43Engine.

    The V45b post-window accretion is REMOVED (replaced by per-step).
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V47EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        # Per-window accretion stats
        self.perstep_stats = {"scans": 0, "boosts": 0, "contacts": 0}
        self.total_perstep_boosts = 0
        self.total_perstep_contacts = 0

    def step_window(self, steps=V47_WINDOW):
        """
        Physics loop with per-step boundary accretion.

        Structure:
          for step in range(steps):
              [7 canonical physics operators — identical to V43]
              [background seeding — identical to V43]
              [per-step boundary scan — NEW in v4.7]
          [semantic pressure — identical to V43]
          [island observation — via V46Tracker]
          [observer / frame — identical to V43]

        V45b's post-window accretion is NOT called.
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        scan_interval = self.island_tracker.params.perstep_scan_interval

        # Reset per-window accretion tracking
        latent_accumulator = {}  # {(n1,n2): cumulative_boost}
        window_stats = {"scans": 0, "boosts": 0, "contacts": 0}

        # ── PHYSICS LOOP (V43 canonical + v4.7 per-step scan) ──
        for step in range(steps):
            # ── 7 canonical operators (identical to V43) ──
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)

            # Growth score (for seeding bias)
            self._g_scores[:] = 0
            self.grower.step(self.state)
            for k in self.state.alive_l:
                r = self.state.R.get(k, 0.0)
                if r > 0:
                    a = min(self.grower.params.auto_growth_rate * r,
                            max(self.state.get_latent(k[0], k[1]), 0))
                    if a > 0:
                        self._g_scores[k[0]] += a
                        self._g_scores[k[1]] += a
            gz = float(self._g_scores.sum())

            self.intruder.step(self.state)
            self.physics.step_decay_exclusion(self.state)

            # ── Background seeding (canonical, identical to V43) ──
            al = list(self.state.alive_n)
            na = len(al)
            if na > 0:
                aa = np.array(al)
                if BIAS > 0 and gz > 0:
                    ga = self._g_scores[aa]; gs = ga.sum()
                    if gs > 0:
                        pg = ga / gs
                        pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
                        pd /= pd.sum()
                    else:
                        pd = np.ones(na) / na
                else:
                    pd = np.ones(na) / na
                mk = self.state.rng.random(na) < bg_prob
                for idx in range(na):
                    if mk[idx]:
                        t = int(self.state.rng.choice(aa, p=pd))
                        self.state.E[t] = min(1.0, self.state.E[t] + 0.3)
                        if self.state.Z[t] == 0 and self.state.rng.random() < 0.5:
                            self.state.Z[t] = 1 if self.state.rng.random() < 0.5 else 2

            # ── v4.7: Per-step boundary scan (NEW) ──
            if step % scan_interval == 0:
                scan_stats = per_step_boundary_scan(
                    self.state, self.island_tracker, self.substrate,
                    self.island_tracker.params, self.state.rng,
                    latent_accumulator)
                window_stats["scans"] += scan_stats["scans"]
                window_stats["boosts"] += scan_stats["boosts"]
                window_stats["contacts"] += scan_stats["contacts"]

        # Store window stats
        self.perstep_stats = window_stats
        self.total_perstep_boosts += window_stats["boosts"]
        self.total_perstep_contacts += window_stats["contacts"]

        # ── POST-LOOP: Semantic pressure (identical to V43) ──
        ps = apply_semantic_pressure(self.state, self.substrate,
            self.pressure_params, self.island_tracker, self.state.rng)
        self.window_count += 1

        # ── POST-LOOP: Island observation (identical to V43) ──
        isl_s = find_islands_sets(self.state, 0.30)
        isl_m = find_islands_sets(self.state, 0.20)
        isl_w = find_islands_sets(self.state, 0.10)

        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)

        # ── POST-LOOP: Observer (identical to V43) ──
        nm_s = {n for isl in isl_s for n in isl}
        nm_m = {n for isl in isl_m for n in isl}
        nm_w = {n for isl in isl_w for n in isl}
        bm = set()
        for isl in isl_m:
            for n in isl:
                if n not in self.state.alive_n:
                    continue
                for nb in self.state.neighbors(n):
                    if nb in self.state.alive_n and nb not in isl:
                        bm.add(n); break
        ng = []
        for i in self.state.alive_n:
            if int(self.state.Z[i]) != 3:
                continue
            s = 1 if i in nm_s else 0; m = 1 if i in nm_m else 0
            w = 1 if i in nm_w else 0
            ng.append({"r_bits": f"{s}{m}{w}",
                        "boundary_mid": 1 if i in bm else 0,
                        "intrusion_bin": 0})
        if ng and len(ng) >= MIN_C_NODES_FOR_VALID:
            js = {k: compute_J(ng, self.png, k)[0] for k in K_LEVELS}
            gk = select_k_star(js, self.ckg)
            self.png = ng; self.ckg = gk
        else:
            gk = 0; js = {}
        kc = gk != (self.frames[-1].k_star if self.frames else 0)
        km = (max(js.values()) - sorted(js.values())[-2]
              if len(js) >= 2 else 0.0)

        rc = Counter()
        for i in self.state.alive_n:
            if int(self.state.Z[i]) == 3:
                rc[self.rmap.get(i, 0)] += 1
        tc = sum(rc.values())
        ent = (-sum((v/tc)*math.log2(v/tc) for v in rc.values() if v > 0)
               if tc > 0 else 0.0)
        ed = ent - (self.frames[-1].entropy if self.frames else 0.0)

        hc = len(self.hardening)
        hv = list(self.hardening.values())
        mh = float(np.mean(hv)) if hv else 0.0

        anom = []
        if isum["n_encapsulated"] > 0:
            anom.append(f"[ENCAP] {isum['n_encapsulated']}")
        if isum.get("motif_recurrence", 0) > 0:
            anom.append(f"[MOTIF_RECUR] {isum['motif_recurrence']}")

        # ── POST-LOOP: Frame (identical to V43) ──
        f = V43StateFrame(
            seed=self.seed, window=self.window_count,
            k_star=gk, k_changed=kc, k_margin=km,
            entropy=ent, entropy_delta=ed,
            alive_nodes=len(self.state.alive_n),
            alive_links=len(self.state.alive_l),
            n_clusters=isum["n_clusters"],
            n_encapsulated=isum["n_encapsulated"],
            n_candidates=isum["n_candidates"],
            mean_cluster_size=isum["mean_size"],
            max_cluster_size=isum["max_size"],
            mean_density_ratio=isum["mean_density_ratio"],
            max_density_ratio=isum["max_density_ratio"],
            encap_events_total=isum["encap_events"],
            dissolve_events_total=isum["dissolve_events"],
            mean_inner_entropy=isum["mean_inner_entropy"],
            max_inner_entropy=isum["max_inner_entropy"],
            total_inner_triangles=isum["total_inner_tri"],
            motif_recurrence_count=isum.get("motif_recurrence", 0),
            pressure_events=ps["pressure_events"],
            latent_boosts=ps["latent_boosts"],
            nodes_shielded=ps["nodes_shielded"],
            hardened_links_count=hc, mean_hardening=round(mh, 4),
            anomalies=anom, physics_seconds=round(time.time()-t0, 1),
        )
        f.milestone = evaluate_milestones(f, self.frames)
        f.compute_hash()
        self.frames.append(f)

        # NOTE: V45b's post-window accretion is intentionally NOT called.
        # Per-step accretion within the loop replaces it.
        # We still set accretion_stats for calibrate compatibility.
        self.accretion_stats = {
            "qualified_clusters": window_stats["scans"],
            "contact_events": window_stats["contacts"],
            "boosts_applied": window_stats["boosts"],
            "unique_boosted_nodes": len(latent_accumulator),
            "resonance_factors": [],
        }
        self.total_accretion_boosts = self.total_perstep_boosts
        self.total_accretion_contacts = self.total_perstep_contacts

        return f
