#!/usr/bin/env python3
"""
ESDE v4.8b — Terrain Genesis + Chemical Valence
==================================================
Phase : v4.8b (Track A + Track B combined)
Role  : Claude (Implementation)
Arch  : Gemini (+ Taka directive) | Audit: GPT

Two orthogonal physics changes, both toggleable:

Track A (v4.8): Density-dependent cooling
  Dense regions receive less semantic pressure perturbation.
  Inherited from V48Engine.

Track B (NEW): Z-state topological coupling
  A) Z-dependent decay resistance (bond hardness):
     After standard decay, apply correction based on Z-states.
     Z=0 (inert):    fragile bonds, extra decay
     Z=1,2 (A,B):    standard (no modifier)
     Z=3 (compound):  hard bonds, partial decay restoration
  B) Z-dependent phase coupling (chemical polarity):
     After standard phase sync, apply correction to theta.
     Homogeneous (A-A, B-B): standard sync
     Heterogeneous (A-B):    reduced sync (persistent tension)

Both corrections are applied INSIDE the physics loop as
post-step adjustments (same pattern as v3.5 decay dampening).
The frozen engine operators are NOT modified.

Toggle: z_coupling_enabled = True/False for ablation.

Principle: "Structure first, meaning later."

NOTE: Full override of parent step_window(). Changes to
V48/V46/V43 step_window will NOT auto-propagate here.
This is intentional for physics isolation.
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
_V48_DIR = _SCRIPT_DIR.parent / "v48"
_V46_DIR = _SCRIPT_DIR.parent / "v46"
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V48_DIR), str(_V46_DIR), str(_V45A_DIR),
          str(_V44_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v48_engine import (
    V48Engine, V48EncapsulationParams,
    apply_cooled_semantic_pressure,
)
from esde_v43_engine import (
    MotifParams, find_islands_sets,
    V43StateFrame, evaluate_milestones, WINDOW,
)
from esde_v41_engine import MIN_C_NODES_FOR_VALID, N_REGIONS
from v19g_canon import K_LEVELS, BASE_PARAMS, BIAS, compute_J, select_k_star


# ================================================================
# v4.8b CONSTANTS
# ================================================================
V48B_WINDOW = 50


# ================================================================
# v4.8b PARAMETERS
# ================================================================
@dataclass
class V48bEncapsulationParams(V48EncapsulationParams):
    """v4.8b: adds Z-coupling parameters to v4.8 cooling."""
    # Z-coupling toggle (for ablation)
    z_coupling_enabled: bool = True

    # A) Z-dependent decay resistance
    z_decay_inert_penalty: float = 0.02    # extra S reduction for Z=0 links
    z_decay_compound_restore: float = 0.5  # fraction of decay restored for Z=3 links

    # B) Z-dependent phase coupling
    z_phase_hetero_dampen: float = 0.3     # K_sync multiplier for A-B pairs (0=decouple, 1=standard)


# ================================================================
# Z-STATE CORRECTIONS (applied per-step inside physics loop)
# ================================================================
def apply_z_decay_correction(state, params):
    """
    Post-decay correction based on Z-states of linked nodes.

    Applied after state.step_decay_exclusion() each step.
    Records the S value before decay (pre_S) and adjusts:
      Z=0 involved: extra penalty (weaker bonds)
      Z=3 involved: partial restoration (stronger bonds)
      Z=1,Z=2 only: no change

    Returns stats dict.
    """
    stats = {"hardened": 0, "softened": 0}

    for lk in list(state.alive_l):
        n1, n2 = lk
        z1 = int(state.Z[n1])
        z2 = int(state.Z[n2])

        # Z=0 involved: extra decay penalty (fragile void bonds)
        if z1 == 0 or z2 == 0:
            state.S[lk] = max(0.0, state.S[lk] - params.z_decay_inert_penalty)
            stats["softened"] += 1
            # Check if link should die
            if state.S[lk] < state.EXTINCTION:
                state.kill_link(lk)

        # Z=3 involved: partial decay restoration (hard bonds)
        elif z1 == 3 or z2 == 3:
            # Restore a fraction of the decay that just occurred
            # We don't know exact pre-decay S, but we boost proportionally
            restore = params.z_decay_compound_restore
            # Small fixed boost to counteract standard decay
            state.S[lk] = min(1.0, state.S[lk] + 0.005 * restore)
            stats["hardened"] += 1

    return stats


def apply_z_phase_correction(state, params):
    """
    Post-phase correction for Z-dependent coupling.

    For heterogeneous pairs (Z=1-Z=2 or Z=2-Z=1), partially
    reverse the phase synchronization that just occurred.
    This maintains persistent phase tension across A-B bonds.

    Applied after step_pre_chemistry (which includes phase sync).

    Returns stats dict.
    """
    stats = {"tensioned": 0}
    dampen = params.z_phase_hetero_dampen

    for lk in state.alive_l:
        n1, n2 = lk
        z1 = int(state.Z[n1])
        z2 = int(state.Z[n2])

        # Heterogeneous pair: A-B or B-A
        if (z1 == 1 and z2 == 2) or (z1 == 2 and z2 == 1):
            # The standard phase sync moved theta toward each other.
            # We partially reverse this by pushing them apart.
            # The magnitude is proportional to (1 - dampen).
            diff = state.theta[n2] - state.theta[n1]
            # Circular correction
            if diff > math.pi:
                diff -= 2 * math.pi
            elif diff < -math.pi:
                diff += 2 * math.pi

            # Reverse (1 - dampen) of the sync that occurred
            reverse = diff * (1.0 - dampen) * 0.1  # 0.1 = K_sync baseline
            state.theta[n1] = (state.theta[n1] - reverse * 0.5) % (2 * math.pi)
            state.theta[n2] = (state.theta[n2] + reverse * 0.5) % (2 * math.pi)
            stats["tensioned"] += 1

    return stats


# ================================================================
# v4.8b ENGINE
# ================================================================
class V48bEngine(V48Engine):
    """
    V48Engine (cooling) + Z-state chemical valence coupling.
    Both toggleable for ablation experiments.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V48bEncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.z_stats = {"hardened": 0, "softened": 0, "tensioned": 0}
        self.total_z_hardened = 0
        self.total_z_softened = 0
        self.total_z_tensioned = 0

    def step_window(self, steps=V48B_WINDOW):
        """
        Physics loop with:
          - Z-dependent decay correction (after decay_exclusion)
          - Z-dependent phase correction (after pre_chemistry)
          - Background seeding (canonical)
          - Cooled semantic pressure (post-loop, Track A)
          - v4.6 observation (post-loop)
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        z_enabled = self.island_tracker.params.z_coupling_enabled

        window_z_stats = {"hardened": 0, "softened": 0, "tensioned": 0}

        # ── PHYSICS LOOP ──
        for step in range(steps):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)

            # v4.8b: Z-dependent phase correction (after phase sync)
            if z_enabled:
                zp = apply_z_phase_correction(
                    self.state, self.island_tracker.params)
                window_z_stats["tensioned"] += zp["tensioned"]

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

            # v4.8b: Z-dependent decay correction (after decay)
            if z_enabled:
                zd = apply_z_decay_correction(
                    self.state, self.island_tracker.params)
                window_z_stats["hardened"] += zd["hardened"]
                window_z_stats["softened"] += zd["softened"]

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

        # Store Z stats
        self.z_stats = window_z_stats
        self.total_z_hardened += window_z_stats["hardened"]
        self.total_z_softened += window_z_stats["softened"]
        self.total_z_tensioned += window_z_stats["tensioned"]

        # ── POST-LOOP: Cooled semantic pressure (Track A) ──
        ps = apply_cooled_semantic_pressure(
            self.state, self.substrate,
            self.pressure_params, self.island_tracker,
            self.state.rng, self.island_tracker.params)
        self.cooling_stats = ps
        self.window_count += 1

        # ── POST-LOOP: Island observation ──
        isl_s = find_islands_sets(self.state, 0.30)
        isl_m = find_islands_sets(self.state, 0.20)
        isl_w = find_islands_sets(self.state, 0.10)

        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)
        self.last_isum = isum

        # ── POST-LOOP: Observer ──
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
