#!/usr/bin/env python3
"""
ESDE v4.8 — Terrain Genesis: Density-Dependent Cooling
=========================================================
Phase : v4.8 (Physics Change — Paradigm Shift)
Role  : Claude (Implementation)
Arch  : Gemini (+ Taka directive) | Audit: GPT

PARADIGM SHIFT: All forced accretion mechanisms (v4.5b, v4.7)
are deprecated. Focus shifts from "life mechanisms" to
"terrain formation."

Physics change: Density-Dependent Cooling
  Nodes in structurally dense regions receive reduced phase
  perturbation from semantic pressure. This allows dense
  motifs to stabilize and aggregate into persistent
  macro-structures (polyhedral terrain).

  cooling_factor = 1.0 / (1.0 + cooling_strength * local_density)

  where local_density = number of S>=0.20 links at the node.
  Higher density → lower perturbation → more phase stability
  → stronger resonance protection → longer structure lifetime.

  This is a continuous function (per GPT audit recommendation),
  not a hard threshold.

All v4.6 observation preserved (dynamic identity, motif scanner).
v4.5b/v4.7 accretion: REMOVED.

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
_SCRIPT_DIR = Path(__file__).resolve().parent
_V46_DIR = _SCRIPT_DIR.parent / "v46"
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V46_DIR), str(_V45A_DIR), str(_V44_DIR),
          str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v46_engine import V46Engine, V46EncapsulationParams, V46Tracker
from esde_v43_engine import (
    MotifParams, SemanticPressureParams,
    find_islands_sets, V43StateFrame, evaluate_milestones, WINDOW,
)
from esde_v41_engine import MIN_C_NODES_FOR_VALID, N_REGIONS
from v19g_canon import K_LEVELS, BASE_PARAMS, BIAS, compute_J, select_k_star


# ================================================================
# v4.8 CONSTANTS
# ================================================================
V48_WINDOW = 50


# ================================================================
# v4.8 PARAMETERS
# ================================================================
@dataclass
class V48EncapsulationParams(V46EncapsulationParams):
    """v4.8: adds cooling parameters. Removes accretion."""
    # Density-dependent cooling
    cooling_strength: float = 1.0     # scaling factor for density effect
    cooling_s_threshold: float = 0.20  # link strength threshold for density count
    cooling_enabled: bool = True


# ================================================================
# DENSITY-DEPENDENT COOLING (v4.8 physics change)
# ================================================================
def apply_cooled_semantic_pressure(state, substrate, pressure_params,
                                   tracker, rng, cooling_params):
    """
    Modified semantic pressure with density-dependent cooling.

    Identical to v4.3 apply_semantic_pressure EXCEPT:
    each node's perturbation strength is scaled by:

      cooling_factor = 1.0 / (1.0 + cooling_strength * local_density)

    where local_density = count of alive links with S >= s_threshold
    at that node.

    Dense regions experience less phase noise → phase coherence
    maintained → resonance protection sustained → structure persists.

    Returns stats dict compatible with v4.3.
    """
    stats = {
        "pressure_events": 0,
        "latent_boosts": 0,
        "nodes_shielded": 0,
        "cooled_nodes": 0,
        "mean_cooling_factor": 0.0,
    }

    # Shielded nodes (encapsulated interiors — legacy from v4.3)
    shielded = set()
    for isl in tracker.islands.values():
        if isl.status == "encapsulated":
            shielded |= isl.interior_nodes

    cooling_factors = []

    for n in list(state.alive_n):
        if n in shielded:
            stats["nodes_shielded"] += 1
            continue
        if rng.random() > pressure_params.pressure_prob:
            continue

        # Compute local density (count of strong links)
        if cooling_params.cooling_enabled:
            local_density = 0
            for nb in state.neighbors(n):
                if nb in state.alive_n:
                    lk = state.key(n, nb)
                    if (lk in state.alive_l and
                            state.S[lk] >= cooling_params.cooling_s_threshold):
                        local_density += 1
            cooling_factor = 1.0 / (1.0 + cooling_params.cooling_strength * local_density)
            cooling_factors.append(cooling_factor)
            if cooling_factor < 0.9:
                stats["cooled_nodes"] += 1
        else:
            cooling_factor = 1.0

        # Apply cooled perturbation
        d = rng.uniform(-1, 1)
        effective_strength = pressure_params.pressure_strength * cooling_factor
        state.theta[n] = (state.theta[n] + effective_strength * d) % (2 * np.pi)
        stats["pressure_events"] += 1

        # Latent boost for non-linked substrate neighbors (unchanged from v4.3)
        for nb in substrate.get(n, []):
            if nb in state.alive_n and nb not in shielded:
                lk = state.key(n, nb)
                if lk not in state.alive_l:
                    cur = state.get_latent(n, nb)
                    state.set_latent(n, nb,
                                     min(1.0, cur + pressure_params.latent_boost))
                    stats["latent_boosts"] += 1

    stats["mean_cooling_factor"] = (
        round(float(np.mean(cooling_factors)), 4) if cooling_factors else 1.0)

    return stats


# ================================================================
# v4.8 ENGINE
# ================================================================
class V48Engine(V46Engine):
    """
    V46Engine with density-dependent cooling replacing standard
    semantic pressure. All accretion mechanisms removed.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V48EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.cooling_stats = {}
        self.last_isum = {}
        # Backward compat stubs — accretion removed in v4.8
        self.accretion_stats = {
            "qualified_clusters": 0, "contact_events": 0,
            "boosts_applied": 0, "unique_boosted_nodes": 0,
            "resonance_factors": [],
        }
        self.total_accretion_boosts = 0
        self.total_accretion_contacts = 0

    def step_window(self, steps=V48_WINDOW):
        """
        Physics loop identical to V43 + cooled semantic pressure.
        No accretion. Full v4.6 observation.

        NOTE: Full override of parent step_window(). Changes to
        V46/V45b/V43 step_window will NOT auto-propagate here.
        This is intentional for physics isolation — v4.8 modifies
        the pressure function, which requires explicit control of
        the entire post-loop sequence.
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]

        # ── PHYSICS LOOP (identical to V43) ──
        for step in range(steps):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)

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

            # Background seeding (canonical)
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

        # ── POST-LOOP: Cooled semantic pressure (v4.8 change) ──
        ps = apply_cooled_semantic_pressure(
            self.state, self.substrate,
            self.pressure_params, self.island_tracker,
            self.state.rng, self.island_tracker.params)
        self.cooling_stats = ps
        self.window_count += 1

        # ── POST-LOOP: Island observation (identical to V43) ──
        isl_s = find_islands_sets(self.state, 0.30)
        isl_m = find_islands_sets(self.state, 0.20)
        isl_w = find_islands_sets(self.state, 0.10)

        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)
        self.last_isum = isum  # exposed for calibrate (avoids redundant _summary())

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

        return f
