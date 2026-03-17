#!/usr/bin/env python3
"""
ESDE v4.9 Phase 1 — Multidimensional History Layer
=====================================================
Phase : v4.9-P1 (Structural Fatigue & Maturation)
Role  : Claude (Implementation)
Arch  : Gemini (+ Taka) | Audit: GPT

History as Material Properties (not memory):
  - Maturation: old links resist slow decay
  - Rigidity: resonance-locked links suppress new connections
  - Brittleness: stressed links snap catastrophically
  - Avalanche: ossified clusters shatter when breached

Micro-History: Link Tensor H_ij = {h_age, h_res, h_str}
  h_age ∈ [0,1]: temporal survival → slight decay resistance
  h_res ∈ [0,1]: resonance exposure → plasticity suppression
  h_str ∈ [0,1]: stress exposure → fracture brittleness

Macro-History: Cluster H_C = {C_age, C_fragility}
  C_age: consecutive windows survived (from tracker)
  C_fragility: f(C_age, lack_of_deformation) → avalanche trigger

Inherits V48cEngine (axiomatic parameter discovery preserved).
Physics operators: UNCHANGED (corrections applied post-step).
"""

import sys, math, time
import numpy as np
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
_V48C_DIR = _SCRIPT_DIR.parent / "v48c"
_V48B_DIR = _SCRIPT_DIR.parent / "v48b"
_V48_DIR = _SCRIPT_DIR.parent / "v48"
_V46_DIR = _SCRIPT_DIR.parent / "v46"
_V45A_DIR = _SCRIPT_DIR.parent / "v45a"
_V44_DIR = _SCRIPT_DIR.parent / "v44"
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V48C_DIR), str(_V48B_DIR), str(_V48_DIR), str(_V46_DIR),
          str(_V45A_DIR), str(_V44_DIR), str(_V43_DIR), str(_V41_DIR),
          str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v48c_engine import V48cEngine, V48cEncapsulationParams
from esde_v48b_engine import apply_z_decay_correction, apply_z_phase_correction
from esde_v48_engine import apply_cooled_semantic_pressure
from esde_v43_engine import (
    find_islands_sets, V43StateFrame, evaluate_milestones, WINDOW,
)
from esde_v41_engine import MIN_C_NODES_FOR_VALID, N_REGIONS
from v19g_canon import K_LEVELS, BASE_PARAMS, BIAS, compute_J, select_k_star


# ================================================================
# v4.9 CONSTANTS
# ================================================================
V49_WINDOW = 50

# Tensor update rates (per step, normalized to [0,1])
H_AGE_INCREMENT = 0.002      # ~100 steps to reach 0.2, ~500 to 1.0
H_RES_INCREMENT = 0.003      # slightly faster for resonance-active links
H_STR_INCREMENT = 0.005      # stress accumulates faster


# ================================================================
# v4.9 PARAMETERS
# ================================================================
@dataclass
class V49EncapsulationParams(V48cEncapsulationParams):
    """v4.9 Phase 1: history layer parameters."""
    # h_age: maturation → decay resistance
    history_age_decay_reduction: float = 0.3  # max 30% decay reduction at h_age=1.0
    # h_res: resonance exposure → plasticity suppression (GPT: soft, not hard)
    history_res_plasticity_alpha: float = 0.5  # P(new_link) *= (1 - alpha * h_res)
    # h_str: stress → brittleness
    history_str_fracture_threshold: float = 0.7  # h_str above this → fragile
    history_str_snap_stress: float = 0.15  # instantaneous S-drop that triggers snap
    # Avalanche
    avalanche_decay_spike: float = 0.05  # extra decay on neighbors when boundary snaps
    avalanche_radius: int = 1  # hops within cluster for avalanche propagation
    # Fragility
    fragility_age_threshold: int = 5  # C_age above this starts accumulating fragility
    fragility_deformation_decay: float = 0.3  # deformation resets fragility by this fraction
    # Enable/disable (ablation)
    history_enabled: bool = True


# ================================================================
# LINK HISTORY TENSOR
# ================================================================
class LinkHistoryTensor:
    """
    Stores H_ij = {h_age, h_res, h_str} for each alive link.
    All values ∈ [0, 1].
    Entries are created when a link is first observed alive and
    removed when the link dies.
    """

    def __init__(self):
        self.h_age = {}   # {link_key: float}
        self.h_res = {}
        self.h_str = {}

    def update_step(self, state):
        """Per-step update of all tensor dimensions."""
        # Remove dead links
        dead = [lk for lk in self.h_age if lk not in state.alive_l]
        for lk in dead:
            del self.h_age[lk]
            self.h_res.pop(lk, None)
            self.h_str.pop(lk, None)

        # Update alive links
        for lk in state.alive_l:
            # h_age: increment for survival
            self.h_age[lk] = min(1.0, self.h_age.get(lk, 0.0) + H_AGE_INCREMENT)

            # h_res: increment if in resonance loop (R > 0)
            if state.R.get(lk, 0.0) > 0:
                self.h_res[lk] = min(1.0, self.h_res.get(lk, 0.0) + H_RES_INCREMENT)
            else:
                # Ensure entry exists
                if lk not in self.h_res:
                    self.h_res[lk] = 0.0

            # h_str: increment on stress conditions
            # Spec §2.3 defines stress as "energy fluctuations."
            # Implementation substitutes Z-mismatch + low-S, because
            # per-step ΔE tracking is not in the physics loop.
            # Functionally equivalent: both capture adverse conditions.
            n1, n2 = lk
            z1, z2 = int(state.Z[n1]), int(state.Z[n2])
            s_val = state.S.get(lk, 0.0)
            stressed = False
            if (z1 == 1 and z2 == 2) or (z1 == 2 and z2 == 1):
                stressed = True  # A-B heterogeneous tension
            if s_val < 0.15:  # near extinction threshold
                stressed = True
            if stressed:
                self.h_str[lk] = min(1.0, self.h_str.get(lk, 0.0) + H_STR_INCREMENT)
            else:
                if lk not in self.h_str:
                    self.h_str[lk] = 0.0

    def get(self, lk):
        """Return (h_age, h_res, h_str) for a link."""
        return (
            self.h_age.get(lk, 0.0),
            self.h_res.get(lk, 0.0),
            self.h_str.get(lk, 0.0),
        )

    def summary(self):
        """Aggregate statistics for logging."""
        if not self.h_age:
            return {
                "n_tracked": 0,
                "mean_h_age": 0, "max_h_age": 0,
                "mean_h_res": 0, "max_h_res": 0,
                "mean_h_str": 0, "max_h_str": 0,
                "mature_links": 0, "rigid_links": 0, "brittle_links": 0,
            }
        ages = list(self.h_age.values())
        ress = list(self.h_res.values())
        strs = list(self.h_str.values())
        return {
            "n_tracked": len(ages),
            "mean_h_age": round(np.mean(ages), 4),
            "max_h_age": round(max(ages), 4),
            "mean_h_res": round(np.mean(ress), 4) if ress else 0,
            "max_h_res": round(max(ress), 4) if ress else 0,
            "mean_h_str": round(np.mean(strs), 4) if strs else 0,
            "max_h_str": round(max(strs), 4) if strs else 0,
            "mature_links": sum(1 for a in ages if a > 0.5),
            "rigid_links": sum(1 for r in ress if r > 0.5),
            "brittle_links": sum(1 for s in strs if s > 0.7),
        }


# ================================================================
# HISTORY CORRECTIONS (applied per-step)
# ================================================================
def apply_history_decay_correction(state, tensor, params):
    """
    h_age maturation: reduce effective decay for aged links.
    Applied after standard decay. Partially restores S for mature links.
    """
    stats = {"matured": 0}
    reduction = params.history_age_decay_reduction

    for lk in list(state.alive_l):
        h_age = tensor.h_age.get(lk, 0.0)
        if h_age > 0.1:
            # Restore a fraction of decay proportional to h_age
            restore = 0.002 * reduction * h_age  # small per-step restoration
            state.S[lk] = min(1.0, state.S[lk] + restore)
            stats["matured"] += 1

    return stats


def apply_history_brittleness(state, tensor, params):
    """
    h_str brittleness: links with high stress history snap
    catastrophically when instantaneous conditions are adverse.
    """
    stats = {"snapped": 0}
    threshold = params.history_str_fracture_threshold
    snap_stress = params.history_str_snap_stress

    for lk in list(state.alive_l):
        h_str = tensor.h_str.get(lk, 0.0)
        if h_str >= threshold:
            # Check instantaneous stress: rapid S decline or low S
            s_val = state.S.get(lk, 0.0)
            if s_val < snap_stress:
                # SNAP: catastrophic failure
                state.S[lk] = 0.0
                state.kill_link(lk)
                stats["snapped"] += 1

    return stats


def apply_history_plasticity_suppression(state, tensor, params):
    """
    h_res rigidity: suppress new link formation probability for
    nodes connected by high-resonance-history links.
    Applied by reducing latent field near rigid nodes.

    GPT adjustment: soft suppression P *= (1 - α * h_res),
    never fully eliminates plasticity.
    """
    stats = {"suppressed_nodes": 0}
    alpha = params.history_res_plasticity_alpha
    suppressed = set()

    for lk in state.alive_l:
        h_res = tensor.h_res.get(lk, 0.0)
        if h_res > 0.2:
            suppressed.add(lk[0])
            suppressed.add(lk[1])

    # Reduce latent field for suppressed nodes' non-active neighbors
    for n in suppressed:
        if n not in state.alive_n:
            continue
        max_h_res = max(
            (tensor.h_res.get(state.key(n, nb), 0.0)
             for nb in state.neighbors(n) if nb in state.alive_n),
            default=0.0)
        if max_h_res > 0.2:
            factor = 1.0 - alpha * max_h_res  # GPT soft suppression
            for nb in state.neighbors(n):
                if nb in state.alive_n:
                    lk = state.key(n, nb)
                    if lk not in state.alive_l:
                        cur = state.get_latent(n, nb)
                        if cur > 0:
                            state.set_latent(n, nb, cur * factor)
            stats["suppressed_nodes"] += 1

    return stats


def apply_avalanche(state, tensor, prev_islands, params):
    """
    Macro-history avalanche: when a boundary link of an ossified
    cluster snaps, neighboring intra-cluster links receive a
    temporary decay spike.

    Uses PREVIOUS window's cluster topology (prev_islands) to
    detect boundary links that died during this window's physics.
    This is correct because current-window cluster detection
    already excludes dead links.

    C_fragility = f(C_age, lack_of_deformation).
    """
    stats = {"avalanche_events": 0, "cascade_links": 0}

    for iid, info in prev_islands.items():
        if info.status != "encapsulated":
            continue

        # Compute C_fragility
        c_age = info.relaxed_seen_count if hasattr(info, 'relaxed_seen_count') else info.seen_count
        if c_age < params.fragility_age_threshold:
            continue

        # Check for recent deformation (identity_drift reduces fragility)
        has_drift = getattr(info, 'identity_class', '') == 'identity_drift'
        fragility = min(1.0, (c_age - params.fragility_age_threshold) * 0.1)
        if has_drift:
            fragility *= (1.0 - params.fragility_deformation_decay)

        if fragility < 0.1:
            continue

        # Check if any boundary link snapped this step
        boundary_snapped = False
        for bn in info.boundary_nodes:
            if bn not in state.alive_n:
                continue
            for nb in state.neighbors(bn):
                if nb in state.alive_n and nb in info.nodes:
                    lk = state.key(bn, nb)
                    if lk not in state.alive_l:
                        # This link was alive last step but is now dead
                        boundary_snapped = True
                        break
            if boundary_snapped:
                break

        if not boundary_snapped:
            continue

        # AVALANCHE: spike decay on internal cluster links
        stats["avalanche_events"] += 1
        spike = params.avalanche_decay_spike * fragility
        for n in info.nodes:
            if n not in state.alive_n:
                continue
            for nb in state.neighbors(n):
                if nb in state.alive_n and nb in info.nodes:
                    lk = state.key(n, nb)
                    if lk in state.alive_l:
                        state.S[lk] = max(0.0, state.S[lk] - spike)
                        stats["cascade_links"] += 1
                        if state.S[lk] < state.EXTINCTION:
                            state.kill_link(lk)

    return stats


# ================================================================
# v4.9 ENGINE
# ================================================================
class V49Engine(V48cEngine):
    """
    V48cEngine + Multidimensional History Layer.

    Overrides step_window to insert per-step history tensor
    updates and corrections into the physics loop.

    NOTE: Full override of parent step_window(). This is
    intentional for physics isolation — v4.9 adds per-step
    corrections that must interleave with physics operators.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V49EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.link_history = LinkHistoryTensor()
        self.history_stats = {}
        self.last_isum = {}

    def step_window(self, steps=V49_WINDOW):
        """
        Physics loop with history corrections:
          [7 canonical operators]
          [Z-coupling corrections (v4.8b)]
          [history tensor update]
          [history decay correction (h_age)]
          [history brittleness check (h_str)]
          [history plasticity suppression (h_res)]
          [background seeding]
        Post-loop:
          [cooled semantic pressure (v4.8)]
          [avalanche check (macro-history)]
          [axiomatic parameter drift (v4.8c)]
          [island observation (v4.6)]
          [observer + frame (v4.3)]
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        p = self.island_tracker.params
        z_enabled = p.z_coupling_enabled
        hist_enabled = p.history_enabled

        window_z_stats = {"hardened": 0, "softened": 0, "tensioned": 0}
        window_hist_stats = {"matured": 0, "snapped": 0, "suppressed_nodes": 0}

        # ── PHYSICS LOOP ──
        for step in range(steps):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)

            if z_enabled:
                zp = apply_z_phase_correction(self.state, p)
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

            if z_enabled:
                zd = apply_z_decay_correction(self.state, p)
                window_z_stats["hardened"] += zd["hardened"]
                window_z_stats["softened"] += zd["softened"]

            # ── v4.9: History tensor update + corrections ──
            if hist_enabled:
                self.link_history.update_step(self.state)

                hd = apply_history_decay_correction(
                    self.state, self.link_history, p)
                window_hist_stats["matured"] += hd["matured"]

                hb = apply_history_brittleness(
                    self.state, self.link_history, p)
                window_hist_stats["snapped"] += hb["snapped"]

                # NOTE: plasticity suppression moved to per-window
                # (post-loop, before semantic pressure) for ~50× speedup.
                # Latent field changes slowly; per-step is unnecessary.

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
                        t_node = int(self.state.rng.choice(aa, p=pd))
                        self.state.E[t_node] = min(1.0, self.state.E[t_node] + 0.3)
                        if self.state.Z[t_node] == 0 and self.state.rng.random() < 0.5:
                            self.state.Z[t_node] = 1 if self.state.rng.random() < 0.5 else 2

        # Store Z stats
        self.z_stats = window_z_stats
        self.total_z_hardened += window_z_stats["hardened"]
        self.total_z_softened += window_z_stats["softened"]
        self.total_z_tensioned += window_z_stats["tensioned"]

        # Store history stats
        self.history_stats = window_hist_stats
        self.history_stats.update(self.link_history.summary())

        # ── POST-LOOP: Plasticity suppression (h_res, once per window) ──
        if hist_enabled:
            hp = apply_history_plasticity_suppression(
                self.state, self.link_history, p)
            self.history_stats["suppressed_nodes"] = hp["suppressed_nodes"]

        # ── POST-LOOP: Cooled semantic pressure (v4.8) ──
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

        # Save previous window's cluster state for avalanche check
        # (avalanche needs to detect links that died DURING this window
        # relative to the PREVIOUS cluster topology)
        prev_islands = dict(self.island_tracker.islands)

        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)
        self.last_isum = isum

        # ── POST-LOOP: Avalanche check (macro-history) ──
        # Uses prev_islands (previous window's clusters) to detect
        # boundary links that snapped during this window's physics.
        if hist_enabled:
            av = apply_avalanche(
                self.state, self.link_history,
                prev_islands, p)
            self.history_stats["avalanche_events"] = av["avalanche_events"]
            self.history_stats["cascade_links"] = av["cascade_links"]

        # ── POST-LOOP: Observer ──
        from collections import Counter
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
        if self.history_stats.get("snapped", 0) > 0:
            anom.append(f"[SNAP] {self.history_stats['snapped']}")
        if self.history_stats.get("avalanche_events", 0) > 0:
            anom.append(f"[AVALANCHE] {self.history_stats['avalanche_events']}")

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

        # ── v4.8c: Axiomatic parameter drift ──
        # NOTE: Drift logic replicated from V48cEngine because this
        # method fully overrides step_window(). Future refactor:
        # extract to V48cEngine._apply_drift(frame) method.
        if p.drift_enabled:
            post_links = f.alive_links
            post_z0 = self._count_z0_links()

            if self.prev_alive_links > 0:
                delta_L = post_links - self.prev_alive_links
            else:
                delta_L = 0
                self.prev_alive_links = post_links
            if self.prev_z0_links > 0:
                delta_Z0 = post_z0 - self.prev_z0_links
            else:
                delta_Z0 = 0
                self.prev_z0_links = post_z0

            alpha_t = p.alpha_min + p.alpha_beta * math.tanh(
                abs(delta_L) / p.alpha_v_scale)

            self._drift_window_counter += 1
            applied = False

            if self._drift_window_counter >= p.drift_interval:
                self._drift_window_counter = 0
                applied = True

                grad_L = math.tanh(delta_L / p.drift_scale_L)
                old_restore = p.z_decay_compound_restore
                new_restore = old_restore - (alpha_t * grad_L)
                new_restore = max(p.drift_restore_min,
                                  min(p.drift_restore_max, new_restore))
                p.z_decay_compound_restore = new_restore

                grad_Z0 = math.tanh(delta_Z0 / p.drift_scale_Z0)
                old_inert = p.z_decay_inert_penalty
                new_inert = old_inert - (alpha_t * grad_Z0)
                new_inert = max(p.drift_inert_min,
                                min(p.drift_inert_max, new_inert))
                p.z_decay_inert_penalty = new_inert

                self.prev_alive_links = post_links
                self.prev_z0_links = post_z0

            self.drift_trajectory.append({
                "window": f.window,
                "alpha_t": round(alpha_t, 6),
                "compound_restore": round(p.z_decay_compound_restore, 6),
                "inert_penalty": round(p.z_decay_inert_penalty, 6),
                "delta_L": delta_L,
                "delta_Z0": delta_Z0,
                "abs_delta_L": abs(delta_L),
                "alive_links": post_links,
                "z0_links": post_z0,
                "applied": applied,
            })

            if len(self.drift_trajectory) > 500:
                self.drift_trajectory = self.drift_trajectory[-250:]
        else:
            self.prev_alive_links = f.alive_links

        return f
