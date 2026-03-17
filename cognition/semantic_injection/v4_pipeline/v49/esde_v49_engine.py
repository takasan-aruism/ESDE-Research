#!/usr/bin/env python3
"""
ESDE v4.9 — History Layer + Fertile Void
==========================================
Phase : v4.9 (P1: Structural Fatigue + P2: Latent Potential)
Role  : Claude (Implementation)
Arch  : Gemini (+ Taka) | Audit: GPT

Phase 1 (Past): Link Tensor H_ij = {h_age, h_res, h_str}
  Maturation, rigidity, brittleness, avalanche.

Phase 2 (Future): Fertile Void V_i
  Generation: snap echo → V_i += k × h_age (structural inertia
    of collapsed link converts to undirected potential)
  Action: divergence pressure → latent field boost proportional
    to tanh(V_i + V_j) (GPT mandatory saturation)
  Dissipation: temporal decay V *= (1-λ), consumption on link birth
  Interaction with h_res: P = base × (1-α×h_res) × (1+γ×tanh(V))

The Fertile Void is NOT memory. It contains zero topological
information about what collapsed. It is pure undirected
structural possibility — "vacuum energy" after collapse.

Physics operators: UNCHANGED.
v4.8c axiomatic drift: PRESERVED.

NOTE: Full override of parent step_window(). Intentional for
physics isolation.
"""

import sys, math, time
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
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
# CONSTANTS
# ================================================================
V49_WINDOW = 50
H_AGE_INCREMENT = 0.002
H_RES_INCREMENT = 0.003
H_STR_INCREMENT = 0.005


# ================================================================
# PARAMETERS
# ================================================================
@dataclass
class V49EncapsulationParams(V48cEncapsulationParams):
    """v4.9: history layer + fertile void parameters."""
    # Phase 1: h_age maturation
    history_age_decay_reduction: float = 0.3
    # Phase 1: h_res plasticity suppression (GPT soft)
    history_res_plasticity_alpha: float = 0.5
    # Phase 1: h_str brittleness
    history_str_fracture_threshold: float = 0.7
    history_str_snap_stress: float = 0.15
    # Phase 1: avalanche
    avalanche_decay_spike: float = 0.05
    avalanche_radius: int = 1
    fragility_age_threshold: int = 5
    fragility_deformation_decay: float = 0.3
    # Phase 2: fertile void
    void_k: float = 0.5           # snap echo: V += k * h_age
    void_gamma: float = 2.0       # divergence pressure strength
    void_decay_lambda: float = 0.05  # V *= (1 - λ) per step
    void_consumption: float = 0.1  # V consumed per link birth
    void_v_max: float = 5.0       # cap on V_i
    void_diffusion: float = 0.01  # spatial diffusion to neighbors
    # Toggles
    history_enabled: bool = True
    void_enabled: bool = True


# ================================================================
# LINK HISTORY TENSOR (Phase 1)
# ================================================================
class LinkHistoryTensor:
    """H_ij = {h_age, h_res, h_str} per alive link."""

    def __init__(self):
        self.h_age = {}
        self.h_res = {}
        self.h_str = {}

    def update_step(self, state):
        """Per-step update."""
        dead = [lk for lk in self.h_age if lk not in state.alive_l]
        for lk in dead:
            del self.h_age[lk]
            self.h_res.pop(lk, None)
            self.h_str.pop(lk, None)

        for lk in state.alive_l:
            self.h_age[lk] = min(1.0, self.h_age.get(lk, 0.0) + H_AGE_INCREMENT)

            if state.R.get(lk, 0.0) > 0:
                self.h_res[lk] = min(1.0, self.h_res.get(lk, 0.0) + H_RES_INCREMENT)
            elif lk not in self.h_res:
                self.h_res[lk] = 0.0

            # h_str: stress from Z-mismatch or low-S
            # (Spec §2.3 uses "energy fluctuations"; this is a functionally
            # equivalent substitution — see code review documentation)
            n1, n2 = lk
            z1, z2 = int(state.Z[n1]), int(state.Z[n2])
            s_val = state.S.get(lk, 0.0)
            stressed = ((z1 == 1 and z2 == 2) or (z1 == 2 and z2 == 1)
                        or s_val < 0.15)
            if stressed:
                self.h_str[lk] = min(1.0, self.h_str.get(lk, 0.0) + H_STR_INCREMENT)
            elif lk not in self.h_str:
                self.h_str[lk] = 0.0

    def get(self, lk):
        return (self.h_age.get(lk, 0.0),
                self.h_res.get(lk, 0.0),
                self.h_str.get(lk, 0.0))

    def summary(self):
        if not self.h_age:
            return {"n_tracked": 0, "mean_h_age": 0, "max_h_age": 0,
                    "mean_h_res": 0, "max_h_res": 0,
                    "mean_h_str": 0, "max_h_str": 0,
                    "mature_links": 0, "rigid_links": 0, "brittle_links": 0}
        ages = list(self.h_age.values())
        ress = list(self.h_res.values())
        strs = list(self.h_str.values())
        return {
            "n_tracked": len(ages),
            "mean_h_age": round(float(np.mean(ages)), 4),
            "max_h_age": round(max(ages), 4),
            "mean_h_res": round(float(np.mean(ress)), 4) if ress else 0,
            "max_h_res": round(max(ress), 4) if ress else 0,
            "mean_h_str": round(float(np.mean(strs)), 4) if strs else 0,
            "max_h_str": round(max(strs), 4) if strs else 0,
            "mature_links": sum(1 for a in ages if a > 0.5),
            "rigid_links": sum(1 for r in ress if r > 0.5),
            "brittle_links": sum(1 for s in strs if s > 0.7),
        }


# ================================================================
# PHASE 1 CORRECTIONS
# ================================================================
def apply_history_decay_correction(state, tensor, params):
    """h_age maturation: partial decay resistance."""
    stats = {"matured": 0}
    reduction = params.history_age_decay_reduction
    for lk in list(state.alive_l):
        h_age = tensor.h_age.get(lk, 0.0)
        if h_age > 0.1:
            restore = 0.002 * reduction * h_age
            state.S[lk] = min(1.0, state.S[lk] + restore)
            stats["matured"] += 1
    return stats


def apply_history_brittleness(state, tensor, params, void_field):
    """
    h_str brittleness: catastrophic snap.
    Phase 2 integration: snap deposits potential into void_field.
    Returns snap stats.
    """
    stats = {"snapped": 0, "void_deposited": 0.0}
    threshold = params.history_str_fracture_threshold
    snap_stress = params.history_str_snap_stress
    void_k = params.void_k
    void_enabled = params.void_enabled
    v_max = params.void_v_max

    for lk in list(state.alive_l):
        h_str = tensor.h_str.get(lk, 0.0)
        if h_str >= threshold:
            s_val = state.S.get(lk, 0.0)
            if s_val < snap_stress:
                # Get h_age before killing
                h_age = tensor.h_age.get(lk, 0.0)
                n1, n2 = lk

                # SNAP
                state.S[lk] = 0.0
                state.kill_link(lk)
                stats["snapped"] += 1

                # Phase 2: Snap Echo → deposit V_i
                if void_enabled and h_age > 0:
                    deposit = void_k * h_age
                    void_field[n1] = min(v_max, void_field[n1] + deposit)
                    void_field[n2] = min(v_max, void_field[n2] + deposit)
                    stats["void_deposited"] += deposit * 2

    return stats


def apply_history_plasticity_suppression(state, tensor, params):
    """h_res rigidity: suppress new link formation (per-window)."""
    stats = {"suppressed_nodes": 0}
    alpha = params.history_res_plasticity_alpha
    suppressed = set()

    for lk in state.alive_l:
        if tensor.h_res.get(lk, 0.0) > 0.2:
            suppressed.add(lk[0])
            suppressed.add(lk[1])

    for n in suppressed:
        if n not in state.alive_n:
            continue
        max_h_res = max(
            (tensor.h_res.get(state.key(n, nb), 0.0)
             for nb in state.neighbors(n) if nb in state.alive_n),
            default=0.0)
        if max_h_res > 0.2:
            factor = 1.0 - alpha * max_h_res
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
    """Macro-history avalanche on ossified clusters."""
    stats = {"avalanche_events": 0, "cascade_links": 0}

    for iid, info in prev_islands.items():
        if info.status != "encapsulated":
            continue
        c_age = getattr(info, 'relaxed_seen_count', info.seen_count)
        if c_age < params.fragility_age_threshold:
            continue
        has_drift = getattr(info, 'identity_class', '') == 'identity_drift'
        fragility = min(1.0, (c_age - params.fragility_age_threshold) * 0.1)
        if has_drift:
            fragility *= (1.0 - params.fragility_deformation_decay)
        if fragility < 0.1:
            continue

        boundary_snapped = False
        for bn in info.boundary_nodes:
            if bn not in state.alive_n:
                continue
            for nb in state.neighbors(bn):
                if nb in state.alive_n and nb in info.nodes:
                    lk = state.key(bn, nb)
                    if lk not in state.alive_l:
                        boundary_snapped = True
                        break
            if boundary_snapped:
                break
        if not boundary_snapped:
            continue

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
# PHASE 2: FERTILE VOID
# ================================================================
def apply_void_divergence_pressure(state, void_field, params, tensor):
    """
    Phase 2 Action: boost latent field for node pairs with high V_i.
    Applied before realizer.step() each physics step.

    P_new_link effect = base × (1 - α×h_res) × (1 + γ×tanh(V_i+V_j))
    h_res suppression is already applied per-window; here we apply
    the void amplification to the latent field directly.

    Returns stats.
    """
    stats = {"boosted_pairs": 0, "total_boost": 0.0}
    gamma = params.void_gamma

    # Only process nodes with V > 0
    active_nodes = [n for n in range(len(void_field))
                    if void_field[n] > 0.01 and n in state.alive_n]

    for n in active_nodes:
        v_n = void_field[n]
        for nb in state.neighbors(n):
            if nb not in state.alive_n:
                continue
            lk = state.key(n, nb)
            if lk in state.alive_l:
                continue  # already active

            v_nb = void_field[nb]
            # Divergence pressure with GPT mandatory tanh saturation
            amplification = gamma * math.tanh(v_n + v_nb)
            if amplification > 0.01:
                cur = state.get_latent(n, nb)
                boost = 0.01 * amplification  # small per-step boost
                state.set_latent(n, nb, min(1.0, cur + boost))
                stats["boosted_pairs"] += 1
                stats["total_boost"] += boost

    return stats


def apply_void_decay(void_field, params):
    """Per-step temporal decay: V *= (1 - λ)."""
    decay = 1.0 - params.void_decay_lambda
    void_field *= decay


def apply_void_consumption(state, void_field, params, pre_alive_l):
    """
    Consumption: when a new link is born (present now but not before),
    consume potential at both endpoints.
    """
    stats = {"consumed_events": 0}
    cost = params.void_consumption

    new_links = state.alive_l - pre_alive_l
    for lk in new_links:
        n1, n2 = lk
        if void_field[n1] > 0 or void_field[n2] > 0:
            void_field[n1] = max(0.0, void_field[n1] - cost)
            void_field[n2] = max(0.0, void_field[n2] - cost)
            stats["consumed_events"] += 1

    return stats


def apply_void_diffusion(void_field, state, params):
    """Optional weak spatial diffusion of V_i to neighbors."""
    if params.void_diffusion <= 0:
        return
    diff = params.void_diffusion
    # Accumulate diffusion deltas to avoid order-dependence
    deltas = np.zeros_like(void_field)
    for n in range(len(void_field)):
        if void_field[n] < 0.01 or n not in state.alive_n:
            continue
        nbs = [nb for nb in state.neighbors(n) if nb in state.alive_n]
        if not nbs:
            continue
        share = void_field[n] * diff / len(nbs)
        for nb in nbs:
            deltas[nb] += share
        deltas[n] -= void_field[n] * diff
    void_field += deltas
    np.clip(void_field, 0.0, params.void_v_max, out=void_field)


# ================================================================
# v4.9 ENGINE
# ================================================================
class V49Engine(V48cEngine):
    """
    V48cEngine + Phase 1 (History) + Phase 2 (Fertile Void).

    NOTE: Full override of parent step_window(). Intentional
    for physics isolation — history and void corrections must
    interleave with physics operators. Future refactor: extract
    drift to V48cEngine._apply_drift().
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V49EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.link_history = LinkHistoryTensor()
        self.void_field = np.zeros(N, dtype=np.float64)
        self.history_stats = {}
        self.void_stats = {}
        self.last_isum = {}

    def step_window(self, steps=V49_WINDOW):
        """
        Physics loop:
          [void divergence pressure → latent boost]
          [7 canonical operators]
          [Z-coupling corrections]
          [history tensor update]
          [history decay correction (h_age)]
          [history brittleness + snap echo → V_i deposit]
          [void temporal decay]
          [void consumption on new links]
          [background seeding]
        Post-loop:
          [void spatial diffusion]
          [plasticity suppression (h_res, per-window)]
          [cooled semantic pressure]
          [island observation + avalanche]
          [axiomatic parameter drift]
          [observer + frame]
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        p = self.island_tracker.params
        z_enabled = p.z_coupling_enabled
        hist_enabled = p.history_enabled
        void_enabled = p.void_enabled

        wz = {"hardened": 0, "softened": 0, "tensioned": 0}
        wh = {"matured": 0, "snapped": 0, "suppressed_nodes": 0,
              "void_deposited": 0.0}
        wv = {"boosted_pairs": 0, "total_boost": 0.0, "consumed_events": 0}

        for step in range(steps):
            # Snapshot alive links before physics (for consumption tracking)
            pre_alive_l = set(self.state.alive_l) if void_enabled else set()

            # Phase 2: void divergence pressure (before realizer)
            if void_enabled:
                vp = apply_void_divergence_pressure(
                    self.state, self.void_field, p, self.link_history)
                wv["boosted_pairs"] += vp["boosted_pairs"]
                wv["total_boost"] += vp["total_boost"]

            # 7 canonical operators
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)

            if z_enabled:
                zp = apply_z_phase_correction(self.state, p)
                wz["tensioned"] += zp["tensioned"]

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
                wz["hardened"] += zd["hardened"]
                wz["softened"] += zd["softened"]

            # Phase 1: history
            if hist_enabled:
                self.link_history.update_step(self.state)
                hd = apply_history_decay_correction(
                    self.state, self.link_history, p)
                wh["matured"] += hd["matured"]
                # Brittleness + snap echo (deposits into void_field)
                hb = apply_history_brittleness(
                    self.state, self.link_history, p, self.void_field)
                wh["snapped"] += hb["snapped"]
                wh["void_deposited"] += hb["void_deposited"]

            # Phase 2: void decay + consumption
            if void_enabled:
                apply_void_decay(self.void_field, p)
                vc = apply_void_consumption(
                    self.state, self.void_field, p, pre_alive_l)
                wv["consumed_events"] += vc["consumed_events"]

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
                            self.state.Z[t_node] = (1 if self.state.rng.random() < 0.5
                                                     else 2)

        # Store Z stats
        self.z_stats = wz
        self.total_z_hardened += wz["hardened"]
        self.total_z_softened += wz["softened"]
        self.total_z_tensioned += wz["tensioned"]

        # Store history stats
        self.history_stats = wh
        self.history_stats.update(self.link_history.summary())

        # Store void stats
        self.void_stats = wv
        self.void_stats["mean_V"] = round(float(np.mean(
            self.void_field[list(self.state.alive_n)])), 4) if self.state.alive_n else 0
        self.void_stats["max_V"] = round(float(np.max(self.void_field)), 4)
        self.void_stats["active_V_nodes"] = int(np.sum(self.void_field > 0.01))

        # ── POST-LOOP: Void spatial diffusion ──
        if void_enabled:
            apply_void_diffusion(self.void_field, self.state, p)

        # ── POST-LOOP: Plasticity suppression (h_res, per-window) ──
        if hist_enabled:
            hp = apply_history_plasticity_suppression(
                self.state, self.link_history, p)
            self.history_stats["suppressed_nodes"] = hp["suppressed_nodes"]

        # ── POST-LOOP: Cooled semantic pressure ──
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

        prev_islands = dict(self.island_tracker.islands)
        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)
        self.last_isum = isum

        # ── POST-LOOP: Avalanche ──
        if hist_enabled:
            av = apply_avalanche(
                self.state, self.link_history, prev_islands, p)
            self.history_stats["avalanche_events"] = av["avalanche_events"]
            self.history_stats["cascade_links"] = av["cascade_links"]

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
        if self.history_stats.get("snapped", 0) > 0:
            anom.append(f"[SNAP] {self.history_stats['snapped']}")
        if self.history_stats.get("avalanche_events", 0) > 0:
            anom.append(f"[AVALANCHE]")
        if wv.get("consumed_events", 0) > 0:
            anom.append(f"[VOID_CONSUME] {wv['consumed_events']}")

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
                new_restore = p.z_decay_compound_restore - (alpha_t * grad_L)
                p.z_decay_compound_restore = max(p.drift_restore_min,
                    min(p.drift_restore_max, new_restore))
                grad_Z0 = math.tanh(delta_Z0 / p.drift_scale_Z0)
                new_inert = p.z_decay_inert_penalty - (alpha_t * grad_Z0)
                p.z_decay_inert_penalty = max(p.drift_inert_min,
                    min(p.drift_inert_max, new_inert))
                self.prev_alive_links = post_links
                self.prev_z0_links = post_z0

            self.drift_trajectory.append({
                "window": f.window,
                "alpha_t": round(alpha_t, 6),
                "compound_restore": round(p.z_decay_compound_restore, 6),
                "inert_penalty": round(p.z_decay_inert_penalty, 6),
                "delta_L": delta_L, "delta_Z0": delta_Z0,
                "abs_delta_L": abs(delta_L),
                "alive_links": post_links, "z0_links": post_z0,
                "applied": applied,
            })
            if len(self.drift_trajectory) > 500:
                self.drift_trajectory = self.drift_trajectory[-250:]
        else:
            self.prev_alive_links = f.alive_links

        return f
