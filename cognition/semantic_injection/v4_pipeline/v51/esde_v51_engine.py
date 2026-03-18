#!/usr/bin/env python3
"""
ESDE v5.1 — Closed Circulation
================================
Phase : v5.1 (E↔V Closure + Phase Torque)
Role  : Claude (Implementation + Design)

Four corrections to close remaining v5.0 disconnections:

§1 — V→E Coupling (birth event):
  When transition field creates a link, consumed V excites E.
    E[i] += (1 - E[i]) × V_consumed
  No constants. Capacity-proportional.

§2 — Remove RNG Injection:
  bg_prob, rng-based E injection, Z=0→A/B assignment ALL removed.
  "入口を作るな" — energy enters through circulation, not injection.

§3 — Deterministic E→V Radiation:
  Every alive node radiates E into V per step:
    Radiation = E[i] × (1 - exp(-Π))
    V[i] += Radiation
    E[i] -= Radiation
  Π=0 → no radiation. High Π → strong radiation. All state-derived.

§4 — Proximity Phase Torque:
  R=0 links with structural neighbors get θ coupling:
    Δθ_i = S_ij × E[i] × sin(θ_j − θ_i)
  Accelerates phase sync before cycle formation.
  No fixed coefficients.

All v5.0 fixes retained (proximity S-restore, resonance heat,
dissipation capture, multi-source Π). Frozen operators untouched.
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
_V50_DIR = _SCRIPT_DIR.parent / "v50"
_V49_DIR = _SCRIPT_DIR.parent / "v49"
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

for p in [str(_V50_DIR), str(_V49_DIR), str(_V48C_DIR), str(_V48B_DIR),
          str(_V48_DIR), str(_V46_DIR), str(_V45A_DIR), str(_V44_DIR),
          str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v50_engine import (
    V50Engine, V50EncapsulationParams, V50_WINDOW,
    apply_resonance_heat,
    apply_dissipation_capture,
)
from esde_v49_engine import (
    apply_history_decay_correction,
    apply_history_brittleness,
    apply_history_plasticity_suppression,
    apply_avalanche,
    apply_void_topological_decay,
    apply_void_consumption,
    apply_void_substrate_diffusion,
    _node_active_degree,
)
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
V51_WINDOW = 50


# ================================================================
# PARAMETERS
# ================================================================
@dataclass
class V51EncapsulationParams(V50EncapsulationParams):
    """v5.1: Ablation toggle only. No physics parameters added."""
    keep_bg: bool = False  # ablation: restore canonical bg seeding


# ================================================================
# §1: V→E COUPLED TRANSITION FIELD
# ================================================================
def apply_void_transition_field_v51(state, void_field, params, substrate,
                                     void_active):
    """
    Phase 8 transition field + §1 V→E coupling.

    Identical to v4.9 P8 transition field except:
    On successful birth, consumed V excites E at endpoints:
      E[i] += (1 - E[i]) × V_consumed_at_i
      E[j] += (1 - E[j]) × V_consumed_at_j

    V_consumed_at_i = min(cost, V[i]) — the actual V removed.
    No constants. Capacity gap (1-E) is the natural scaling.
    """
    stats = {"gen_births": 0, "gen_candidates": 0,
             "gen_max_T": 0.0, "gen_max_delta": 0.0,
             "gen_mean_delta": 0.0,
             "birth_v_consumed_tot": 0.0,
             "birth_e_excitation_tot": 0.0}
    pi = params.proliferation_pi
    pi_max = params.proliferation_pi_max
    cost = params.void_consumption

    if pi < 0.001 or pi_max <= 0:
        return stats

    pi_ratio = pi / pi_max
    deltas_list = []

    for n in list(void_active):
        v_n = void_field[n]
        if v_n < 0.001:
            continue
        if n not in state.alive_n:
            continue

        deg_n = _node_active_degree(state, n)
        theta_n = float(state.theta[n])

        sub_nbs = substrate.get(n, set())
        for nb in sub_nbs:
            if nb not in state.alive_n:
                continue
            lk = state.key(n, nb)
            if lk in state.alive_l:
                continue

            v_nb = void_field[nb]
            deg_nb = _node_active_degree(state, nb)
            theta_nb = float(state.theta[nb])

            # Transition Field
            void_factor = math.tanh(v_n + v_nb)
            phase_resonance = 0.5 * (1.0 + math.cos(theta_n - theta_nb))
            T_ij = void_factor * pi_ratio * phase_resonance

            # Emergent Threshold
            E_ij = math.tanh(max(deg_n, deg_nb) / (1.0 + pi))

            delta_ij = T_ij - E_ij
            deltas_list.append(delta_ij)

            if T_ij > stats["gen_max_T"]:
                stats["gen_max_T"] = T_ij
            if delta_ij > stats["gen_max_delta"]:
                stats["gen_max_delta"] = delta_ij

            if delta_ij > 0:
                stats["gen_candidates"] += 1

            # Deterministic birth
            if T_ij > E_ij:
                state.set_latent(n, nb, 1.0)
                stats["gen_births"] += 1

                # Consume V
                consumed_n = min(cost, void_field[n])
                consumed_nb = min(cost, void_field[nb])
                void_field[n] = max(0.0, void_field[n] - cost)
                void_field[nb] = max(0.0, void_field[nb] - cost)

                # §1: V→E coupling — consumed V excites E
                e_excite_n = (1.0 - state.E[n]) * consumed_n
                e_excite_nb = (1.0 - state.E[nb]) * consumed_nb
                state.E[n] = min(1.0, state.E[n] + e_excite_n)
                state.E[nb] = min(1.0, state.E[nb] + e_excite_nb)

                stats["birth_v_consumed_tot"] += consumed_n + consumed_nb
                stats["birth_e_excitation_tot"] += e_excite_n + e_excite_nb

                if void_field[n] < 0.001:
                    void_active.discard(n)
                if void_field[nb] < 0.001:
                    void_active.discard(nb)

    if deltas_list:
        stats["gen_mean_delta"] = round(float(np.mean(deltas_list)), 6)

    return stats


# ================================================================
# §3: E→V RADIATION
# ================================================================
def apply_e_to_v_radiation(state, void_field, void_active, params):
    """
    Deterministic E→V radiation. Replaces RNG background injection.

    Every alive node:
      Radiation = E[i] × (1 - exp(-Π))
      V[i] += Radiation
      E[i] -= Radiation

    Π=0 → (1-exp(0)) = 0 → no radiation.
    Π=5 → (1-exp(-5)) ≈ 0.993 → nearly all E radiates.
    Π=1 → (1-exp(-1)) ≈ 0.632 → moderate radiation.

    No constants. Π governs the fraction. E provides the fuel.
    System breathes: E → V → birth → V→E → back to E.
    """
    stats = {"boil_events": 0, "boil_v_added_tot": 0.0,
             "boil_e_consumed_tot": 0.0}
    pi = params.proliferation_pi
    v_max = params.void_v_max

    if pi < 0.001:
        return stats

    radiation_frac = 1.0 - math.exp(-pi)

    for n in list(state.alive_n):
        e_n = state.E[n]
        if e_n < 0.001:
            continue

        radiation = e_n * radiation_frac
        if radiation < 0.0001:
            continue

        state.E[n] -= radiation
        void_field[n] = min(v_max, void_field[n] + radiation)

        if void_field[n] > 0.001:
            void_active.add(n)

        stats["boil_events"] += 1
        stats["boil_v_added_tot"] += radiation
        stats["boil_e_consumed_tot"] += radiation

    return stats


# ================================================================
# §4: PROXIMITY RESONANCE + PHASE TORQUE
# ================================================================
def apply_proximity_resonance_v51(state, pre_decay_S):
    """
    v5.0 proximity resonance + §4 phase torque.

    S restoration: identical to v5.0.
      restore = S_lost × tanh(neighbor_S)

    Phase torque (NEW): for R=0 links with nb_S > 0:
      Δθ_i = S_ij × E[i] × sin(θ_j − θ_i)
      Δθ_j = S_ij × E[j] × sin(θ_i − θ_j)
    Accelerates θ synchronization before cycle formation.
    No fixed coefficients. S×E is the coupling strength.
    """
    stats = {"proximity_restored": 0, "proximity_total_restore": 0.0,
             "prox_phase_torque_events": 0, "total_phase_torque": 0.0}

    for lk in list(state.alive_l):
        if state.R.get(lk, 0.0) > 0:
            continue

        n1, n2 = lk
        s_before = pre_decay_S.get(lk, 0.0)
        s_now = state.S.get(lk, 0.0)
        s_lost = s_before - s_now

        # Compute neighbor S (needed for both restore and torque gate)
        nb_S = 0.0
        for nb in state.neighbors(n1):
            if nb in state.alive_n:
                nlk = state.key(n1, nb)
                if nlk in state.alive_l and nlk != lk:
                    nb_S += state.S.get(nlk, 0.0)
        for nb in state.neighbors(n2):
            if nb in state.alive_n:
                nlk = state.key(n2, nb)
                if nlk in state.alive_l and nlk != lk:
                    nb_S += state.S.get(nlk, 0.0)

        # S restoration (v5.0)
        if s_lost > 0:
            proximity = math.tanh(nb_S)
            restore = s_lost * proximity
            if restore > 0.0001:
                state.S[lk] = min(1.0, s_now + restore)
                stats["proximity_restored"] += 1
                stats["proximity_total_restore"] += restore

        # §4: Phase torque (only if structural neighbors exist)
        if nb_S > 0 and s_now > 0.001:
            theta_1 = float(state.theta[n1])
            theta_2 = float(state.theta[n2])
            delta_theta = theta_2 - theta_1

            torque_1 = s_now * state.E[n1] * math.sin(delta_theta)
            torque_2 = s_now * state.E[n2] * math.sin(-delta_theta)

            state.theta[n1] += torque_1
            state.theta[n2] += torque_2

            torque_mag = abs(torque_1) + abs(torque_2)
            if torque_mag > 0.0001:
                stats["prox_phase_torque_events"] += 1
                stats["total_phase_torque"] += torque_mag

    return stats


# ================================================================
# V5.1 ENGINE
# ================================================================
class V51Engine(V50Engine):
    """
    V50Engine + E↔V closure + phase torque.

    Changes from v5.0:
      - apply_void_transition_field → v51 (V→E on birth)
      - Background seeding REMOVED (E→V radiation replaces it)
      - apply_proximity_resonance → v51 (+ phase torque)
      - apply_e_to_v_radiation added to per-step loop

    Full step_window override. All v5.0 + v4.9 P1–P8 retained.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V51EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)

    def step_window(self, steps=V51_WINDOW):
        """
        PER-STEP:
          1-2.  realizer, physics.step_pre_chemistry
          3.    Z phase correction
          4-5.  chem, physics.step_resonance
          6.    Resonance Heat (v5.0 Fix 2: R>0 → E)
          7-8.  grower + g_scores, intruder
          9.    pre-decay S snapshot
          10.   physics.step_decay_exclusion
          11.   Z decay correction
          12.   [v5.1] Proximity Resonance + Phase Torque
          13.   Dissipation Capture (v5.0 Fix 3: S lost → V)
          14-16. Phase 1: history
          17.   Phase 3: substrate diffusion
          18.   [v5.1] E→V Radiation (replaces background seeding)
          19.   [v5.1] Transition field with V→E coupling
          20-21. Phase 6: tension-gated decay, consumption + cascade
          (background seeding REMOVED)

        POST-LOOP:
          22.   Multi-source Π (v5.0 Fix 4)
          23+.  void metrics, plasticity, cooling, islands,
                avalanche, observer, drift
        """
        t0 = time.time()
        p = self.island_tracker.params
        z_enabled = p.z_coupling_enabled
        hist_enabled = p.history_enabled
        void_enabled = p.void_enabled
        circ_enabled = p.circulation_enabled

        wz = {"hardened": 0, "softened": 0, "tensioned": 0}
        wh = {"matured": 0, "snapped": 0, "suppressed_nodes": 0,
              "void_deposited": 0.0}
        wv = {"consumed_events": 0, "void_induced_births": 0,
              "diffusion_events": 0, "void_to_active": 0,
              "cascade_splashes": 0,
              "gen_births": 0, "gen_candidates": 0,
              "gen_max_T": 0.0, "gen_max_delta": 0.0}
        wc = {"proximity_restored": 0, "proximity_total_restore": 0.0,
              "heat_events": 0, "heat_total": 0.0,
              "capture_events": 0, "capture_total": 0.0,
              "prox_phase_torque_events": 0, "total_phase_torque": 0.0,
              "birth_v_consumed_tot": 0.0, "birth_e_excitation_tot": 0.0,
              "boil_events": 0, "boil_v_added_tot": 0.0}

        for step in range(steps):
            pre_alive_l = set(self.state.alive_l) if void_enabled else set()

            # ── 1-2: Canonical operators ──
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)

            # ── 3: Z phase correction ──
            if z_enabled:
                zp = apply_z_phase_correction(self.state, p)
                wz["tensioned"] += zp["tensioned"]

            # ── 4-5: Chemistry + Resonance ──
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)

            # ── 6: Resonance Heat (R>0 → E) ──
            if circ_enabled:
                rh = apply_resonance_heat(self.state)
                wc["heat_events"] += rh["heat_events"]
                wc["heat_total"] += rh["heat_total"]

            # ── 7: Grower + g_scores ──
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

            # ── 8: Intruder ──
            self.intruder.step(self.state)

            # ── 9: Pre-decay S snapshot ──
            if circ_enabled:
                pre_decay_S = {lk: self.state.S[lk]
                               for lk in self.state.alive_l}
            else:
                pre_decay_S = {}

            # ── 10: Canonical decay + exclusion ──
            self.physics.step_decay_exclusion(self.state)

            # ── 11: Z decay correction ──
            if z_enabled:
                zd = apply_z_decay_correction(self.state, p)
                wz["hardened"] += zd["hardened"]
                wz["softened"] += zd["softened"]

            # ── 12: [v5.1] Proximity Resonance + Phase Torque ──
            if circ_enabled and pre_decay_S:
                pr = apply_proximity_resonance_v51(self.state, pre_decay_S)
                wc["proximity_restored"] += pr["proximity_restored"]
                wc["proximity_total_restore"] += pr["proximity_total_restore"]
                wc["prox_phase_torque_events"] += pr["prox_phase_torque_events"]
                wc["total_phase_torque"] += pr["total_phase_torque"]

            # ── 13: Dissipation Capture (S lost → V) ──
            if circ_enabled and void_enabled and pre_decay_S:
                dc = apply_dissipation_capture(
                    self.state, self.void_field, self.void_active,
                    pre_decay_S, p)
                wc["capture_events"] += dc["capture_events"]
                wc["capture_total"] += dc["capture_total"]

            # ── 14-16: Phase 1 history ──
            if hist_enabled:
                self.link_history.update_step(self.state)
                hd = apply_history_decay_correction(
                    self.state, self.link_history, p)
                wh["matured"] += hd["matured"]
                hb = apply_history_brittleness(
                    self.state, self.link_history, p, self.void_field,
                    self.void_active)
                wh["snapped"] += hb["snapped"]
                wh["void_deposited"] += hb["void_deposited"]

            # ── 17: Phase 3 substrate diffusion ──
            if void_enabled and self.void_active:
                sd = apply_void_substrate_diffusion(
                    self.void_field, self.state, self.substrate, p,
                    self.void_active)
                wv["diffusion_events"] += sd["diffusion_events"]
                wv["void_to_active"] += sd["void_to_active"]
                wv["c_diff"] = sd.get("c_diff", 0)

            # ── 18: [v5.1] E→V Radiation — MOVED to post-loop (C2 fix) ──
            # Per-step was 50× too aggressive → E→0 inert collapse.
            # Radiation is a window-scale thermodynamic process.

            # ── 19: [v5.1] Transition field with V→E coupling ──
            if void_enabled and self.void_active:
                gn = apply_void_transition_field_v51(
                    self.state, self.void_field, p, self.substrate,
                    self.void_active)
                wv["gen_births"] += gn["gen_births"]
                wv["gen_candidates"] += gn["gen_candidates"]
                if gn["gen_max_T"] > wv.get("gen_max_T", 0):
                    wv["gen_max_T"] = gn["gen_max_T"]
                if gn["gen_max_delta"] > wv.get("gen_max_delta", 0):
                    wv["gen_max_delta"] = gn["gen_max_delta"]
                wc["birth_v_consumed_tot"] += gn["birth_v_consumed_tot"]
                wc["birth_e_excitation_tot"] += gn["birth_e_excitation_tot"]

            # ── 20-21: Phase 6 decay + consumption ──
            if void_enabled:
                apply_void_topological_decay(
                    self.void_field, self.state, self.void_active, p)
                vc = apply_void_consumption(
                    self.state, self.void_field, p, pre_alive_l,
                    self.void_active, self.substrate)
                wv["consumed_events"] += vc["consumed_events"]
                wv["void_induced_births"] += vc["void_induced_births"]
                wv["cascade_splashes"] += vc.get("cascade_splashes", 0)

            # ── Background seeding ──
            if p.keep_bg:
                # Ablation mode: canonical bg seeding (v4.9 behavior)
                bg_prob = BASE_PARAMS["background_injection_prob"]
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
                            self.state.E[t_node] = min(
                                1.0, self.state.E[t_node] + 0.3)
                            if (self.state.Z[t_node] == 0
                                    and self.state.rng.random() < 0.5):
                                self.state.Z[t_node] = (
                                    1 if self.state.rng.random() < 0.5
                                    else 2)
            # else: §2 — "入口を作るな"
            # E enters via resonance heat + V→E birth coupling.
            # V enters via E→V radiation + dissipation capture.

        # ════════════════════════════════════════════════════
        # POST-LOOP
        # ════════════════════════════════════════════════════

        # Z stats
        self.z_stats = wz
        self.total_z_hardened += wz["hardened"]
        self.total_z_softened += wz["softened"]
        self.total_z_tensioned += wz["tensioned"]

        # History stats
        self.history_stats = wh
        self.history_stats.update(self.link_history.summary())

        # Void stats
        self.void_stats = wv
        alive_nodes_list = list(self.state.alive_n)
        if alive_nodes_list:
            self.void_stats["mean_V"] = round(float(sum(
                self.void_field[n] for n in alive_nodes_list
            ) / len(alive_nodes_list)), 4)
        else:
            self.void_stats["mean_V"] = 0
        self.void_stats["max_V"] = round(
            float(np.max(self.void_field)), 4)
        self.void_stats["active_V_nodes"] = int(
            np.sum(self.void_field > 0.01))

        # Multi-Source Π (v5.0 Fix 4)
        window_snaps = wh.get("snapped", 0)
        alive_links = len(self.state.alive_l)

        if circ_enabled:
            tension_snap = window_snaps / max(1, alive_links)
            tension_entropy = abs(self.prev_entropy_delta)
            if alive_nodes_list:
                mean_E = float(sum(
                    self.state.E[n] for n in alive_nodes_list
                ) / len(alive_nodes_list))
            else:
                mean_E = 0.0
            tension_energy = max(0.0, 1.0 - mean_E)

            self.current_pi = p.proliferation_pi_max * math.tanh(
                tension_snap + tension_entropy + tension_energy)
        else:
            self.current_pi = p.proliferation_pi_max * math.tanh(
                window_snaps / max(1, alive_links))

        p.proliferation_pi = self.current_pi

        # ── [v5.1] E→V Radiation (post-loop, once per window) ──
        # C2 fix: per-step was 50× too aggressive → E→0 collapse.
        # Window-scale is the correct thermodynamic timescale.
        # Uses freshly computed Π from this window.
        if circ_enabled and void_enabled:
            br = apply_e_to_v_radiation(
                self.state, self.void_field, self.void_active, p)
            wc["boil_events"] += br["boil_events"]
            wc["boil_v_added_tot"] += br["boil_v_added_tot"]

        # Circulation stats
        self.circulation_stats = wc
        if circ_enabled:
            self.circulation_stats["pi_tension_snap"] = round(
                tension_snap, 6)
            self.circulation_stats["pi_tension_entropy"] = round(
                tension_entropy, 6)
            self.circulation_stats["pi_tension_energy"] = round(
                tension_energy, 6)
            # Boil-to-birth ratio
            boil_total = wc.get("boil_v_added_tot", 0)
            birth_consumed = wc.get("birth_v_consumed_tot", 0)
            self.circulation_stats["boil_to_birth_ratio"] = round(
                boil_total / max(0.001, birth_consumed), 4)

        # Mandatory void metrics (GPT audit)
        self.void_stats["total_void_mass"] = round(
            float(np.sum(self.void_field)), 4)
        self.void_stats["void_variance"] = round(float(np.var(
            self.void_field[np.array(alive_nodes_list)])), 6) \
            if alive_nodes_list else 0
        isolated_high = 0
        active_neighbor_high = 0
        for n in self.void_active:
            if self.void_field[n] < 0.01:
                continue
            has_active_link = False
            if n in self.state.alive_n:
                for nb in self.state.neighbors(n):
                    if nb in self.state.alive_n:
                        lk = self.state.key(n, nb)
                        if lk in self.state.alive_l:
                            has_active_link = True
                            break
            if has_active_link:
                active_neighbor_high += 1
            else:
                isolated_high += 1
        self.void_stats["isolated_high_V"] = isolated_high
        self.void_stats["active_neighbor_high_V"] = active_neighbor_high

        # Plasticity suppression (per-window)
        if hist_enabled:
            hp = apply_history_plasticity_suppression(
                self.state, self.link_history, p)
            self.history_stats["suppressed_nodes"] = hp["suppressed_nodes"]

        # Cooled semantic pressure
        ps = apply_cooled_semantic_pressure(
            self.state, self.substrate,
            self.pressure_params, self.island_tracker,
            self.state.rng, self.island_tracker.params)
        self.cooling_stats = ps
        self.window_count += 1

        # Island observation
        isl_s = find_islands_sets(self.state, 0.30)
        isl_m = find_islands_sets(self.state, 0.20)
        isl_w = find_islands_sets(self.state, 0.10)

        prev_islands = dict(self.island_tracker.islands)
        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)
        self.last_isum = isum

        # Avalanche
        if hist_enabled:
            av = apply_avalanche(
                self.state, self.link_history, prev_islands, p)
            self.history_stats["avalanche_events"] = av["avalanche_events"]
            self.history_stats["cascade_links"] = av["cascade_links"]

        # Observer
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
        self.prev_entropy_delta = ed

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
        if wc.get("heat_events", 0) > 0:
            anom.append(f"[HEAT] {wc['heat_events']}")
        if wc.get("boil_events", 0) > 0:
            anom.append(f"[BOIL] {wc['boil_events']}")

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

        # Drift Loops A+B
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
                "proliferation_pi": round(self.current_pi, 6),
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
