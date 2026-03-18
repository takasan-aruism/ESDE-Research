#!/usr/bin/env python3
"""
ESDE v6.0 — Recurrence Architecture
=====================================
Phase : v6.0 (Cognitive Transition — Layer 1 + Layer 2)
Role  : Claude (Implementation)
Arch  : Gemini + Taka (Expected Outcomes v1.1)
Audit : GPT (v1.2 + v1.3)

BASE: v4.9 (hard revert from v5.x)

Paradigm shift: "Existence is Recurrence"
  - Energy is Activity (frequency of evaluation), not shielding
  - Persistence is Recurrence (break→reform), not duration
  - Selection is Topological (R>0 only), restored from Genesis

Layer 1 — Selection Recovery + Activity:
  (a) E_ij strictly topological: E_ij = tanh(max(deg_i, deg_j))
      Π removed from denominator. High degree is hard to penetrate.
      Only massive Void tension can overcome structural resistance.
  (b) Energy as Activity: before RealizationOperator, high-E nodes
      amplify their substrate latent field. More active → more
      potential → more sampling. RealizationOperator itself UNTOUCHED.

Layer 2 — Resonance Echo (Topological Scar):
  When R>0 link snaps (brittleness):
    L_ij += S_snapped × R_snapped
  Deposit goes into the SPECIFIC latent slot between those endpoints.
  NOT diffused to void. The scar makes that exact link overwhelmingly
  likely to reform. Structure pulses (break→reform) instead of freezing.
  R=0 snaps still deposit to void field (no resonance memory to preserve).

Layer 3 — World Induction: DEFERRED (requires verified recurrence).

All v4.9 P1-P8 mechanics retained. Frozen operators untouched.
v5.0/v5.1 energy-shielding mechanisms NOT inherited.
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

for p in [str(_V49_DIR), str(_V48C_DIR), str(_V48B_DIR), str(_V48_DIR),
          str(_V46_DIR), str(_V45A_DIR), str(_V44_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v49_engine import (
    V49Engine, V49EncapsulationParams, V49_WINDOW,
    LinkHistoryTensor,
    apply_history_decay_correction,
    apply_history_plasticity_suppression,
    apply_avalanche,
    apply_void_topological_decay,
    apply_void_consumption,
    apply_void_substrate_diffusion,
    _node_active_degree,
    H_AGE_INCREMENT, H_RES_INCREMENT, H_STR_INCREMENT,
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
V60_WINDOW = 50


# ================================================================
# PARAMETERS
# ================================================================
@dataclass
class V60EncapsulationParams(V49EncapsulationParams):
    """v6.0: No new physics parameters. Only ablation toggles."""
    recurrence_enabled: bool = True  # Layer 1+2 toggle


# ================================================================
# LAYER 1a: TOPOLOGICAL TRANSITION FIELD (E_ij without Π)
# ================================================================
def apply_transition_field_v60(state, void_field, params, substrate,
                                void_active):
    """
    Transition field with STRICTLY TOPOLOGICAL threshold.

    T_ij = tanh(V_i + V_j) × (Π / Π_max) × Phase_Resonance(i,j)
      (unchanged from v4.9 — Void tension × crisis × phase alignment)

    E_ij = tanh(max(degree_i, degree_j))
      (CHANGED: Π REMOVED from denominator)

    degree=0: E=0.00 → any T>0 births a link (fresh territory)
    degree=1: E=0.76 → needs strong T (V>1 + phase sync + Π>10)
    degree=3: E=0.995 → nearly impossible (dense regions resist)

    Genesis principle: "the system's metabolic capacity is
    structurally determined, not energetically determined."
    """
    stats = {"gen_births": 0, "gen_candidates": 0,
             "gen_max_T": 0.0, "gen_max_delta": 0.0,
             "gen_mean_delta": 0.0}
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

            # Transition Field (unchanged)
            void_factor = math.tanh(v_n + v_nb)
            phase_resonance = 0.5 * (1.0 + math.cos(theta_n - theta_nb))
            T_ij = void_factor * pi_ratio * phase_resonance

            # Emergent Threshold — STRICTLY TOPOLOGICAL
            E_ij = math.tanh(max(deg_n, deg_nb))

            delta_ij = T_ij - E_ij
            deltas_list.append(delta_ij)

            if T_ij > stats["gen_max_T"]:
                stats["gen_max_T"] = T_ij
            if delta_ij > stats["gen_max_delta"]:
                stats["gen_max_delta"] = delta_ij

            if delta_ij > 0:
                stats["gen_candidates"] += 1

            if T_ij > E_ij:
                state.set_latent(n, nb, 1.0)
                stats["gen_births"] += 1
                void_field[n] = max(0.0, void_field[n] - cost)
                void_field[nb] = max(0.0, void_field[nb] - cost)
                if void_field[n] < 0.001:
                    void_active.discard(n)
                if void_field[nb] < 0.001:
                    void_active.discard(nb)

    if deltas_list:
        stats["gen_mean_delta"] = round(float(np.mean(deltas_list)), 6)

    return stats


# ================================================================
# LAYER 1b: ENERGY AS ACTIVITY (Latent Amplification)
# ================================================================
def apply_activity_amplification(state, substrate):
    """
    High-E nodes amplify substrate latent field before RealizationOperator.

    For each alive node with E > 0:
      For each substrate neighbor also alive:
        L_ij += E[i] × E[j] × current_L_ij

    Active nodes (high E) at active locations produce stronger
    latent potential → RealizationOperator converts more at those
    sites → births concentrate where activity is high.

    RealizationOperator itself is UNTOUCHED (frozen operator).
    This only feeds it more material at active locations.

    No constants. E×E is [0,1] self-scaling.
    """
    stats = {"amplified_pairs": 0}

    for n in state.alive_n:
        e_n = state.E[n]
        if e_n < 0.01:
            continue
        sub_nbs = substrate.get(n, set())
        for nb in sub_nbs:
            if nb not in state.alive_n:
                continue
            lk = state.key(n, nb)
            if lk in state.alive_l:
                continue  # already active, skip
            e_nb = state.E[nb]
            if e_nb < 0.01:
                continue
            cur_L = state.get_latent(n, nb)
            if cur_L < 0.001:
                continue  # no seed to amplify
            boost = e_n * e_nb * cur_L
            if boost > 0.0001:
                state.set_latent(n, nb, min(1.0, cur_L + boost))
                stats["amplified_pairs"] += 1

    return stats


# ================================================================
# LAYER 2: RESONANCE ECHO (Topological Scar)
# ================================================================
def apply_brittleness_v60(state, tensor, params, void_field, void_active,
                           scar_registry, window_count):
    """
    Brittleness snap with Resonance Echo.

    For R>0 links that snap:
      L_ij += S_snapped × R_snapped
      → specific topological scar at exact endpoints
      → RealizationOperator will reform this link preferentially
      → structure PULSES (break→reform) instead of dying

    For R=0 links that snap:
      → void deposit (v4.9 behavior) — no resonance memory

    Scar registry: tracks dead R>0 pairs for reformation detection.
    """
    stats = {"snapped": 0, "void_deposited": 0.0,
             "echo_deposits": 0, "echo_latent_total": 0.0}
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
                h_age = tensor.h_age.get(lk, 0.0)
                r_val = state.R.get(lk, 0.0)
                n1, n2 = lk

                # Capture pre-death values
                s_at_death = s_val
                r_at_death = r_val

                state.S[lk] = 0.0
                state.kill_link(lk)
                stats["snapped"] += 1

                if r_at_death > 0:
                    # LAYER 2: Resonance Echo — scar at exact endpoints
                    echo_deposit = s_at_death * r_at_death
                    if echo_deposit > 0.001:
                        cur_L = state.get_latent(n1, n2)
                        state.set_latent(n1, n2,
                                         min(1.0, cur_L + echo_deposit))
                        stats["echo_deposits"] += 1
                        stats["echo_latent_total"] += echo_deposit

                    # Register scar for reformation tracking
                    scar_registry[lk] = {
                        "died_window": window_count,
                        "S_at_death": round(s_at_death, 4),
                        "R_at_death": round(r_at_death, 4),
                        "echo_L": round(echo_deposit, 4),
                    }
                else:
                    # R=0 snap: void deposit (v4.9 behavior)
                    if void_enabled and h_age > 0:
                        deposit = void_k * h_age
                        void_field[n1] = min(v_max,
                                             void_field[n1] + deposit)
                        void_field[n2] = min(v_max,
                                             void_field[n2] + deposit)
                        void_active.add(n1)
                        void_active.add(n2)
                        stats["void_deposited"] += deposit * 2

    return stats


# ================================================================
# RECURRENCE TRACKER
# ================================================================
def check_reformations(state, scar_registry, window_count):
    """
    Check if any scarred link pairs have reformed.

    A reformation = scar link is now alive AND has R>0.
    Record latency (windows between death and reformation).
    """
    stats = {"reformations": 0, "reforms_alive": 0,
             "mean_latency": 0.0, "max_latency": 0, "latencies": []}

    reformed = []
    for lk, info in list(scar_registry.items()):
        if lk in state.alive_l:
            stats["reforms_alive"] += 1  # scar → link (mechanical)
            r_now = state.R.get(lk, 0.0)
            if r_now > 0:  # link → cycle (structural)
                latency = window_count - info["died_window"]
                stats["reformations"] += 1
                stats["latencies"].append(latency)
                reformed.append(lk)

    for lk in reformed:
        del scar_registry[lk]

    # Prune old scars (>50 windows without reformation)
    stale = [lk for lk, info in scar_registry.items()
             if window_count - info["died_window"] > 50]
    for lk in stale:
        del scar_registry[lk]

    if stats["latencies"]:
        stats["mean_latency"] = round(
            sum(stats["latencies"]) / len(stats["latencies"]), 2)
        stats["max_latency"] = max(stats["latencies"])

    return stats


# ================================================================
# R TRANSITION TRACKER
# ================================================================
def track_r_transitions(state, prev_r_status):
    """
    Track links transitioning from R=0 → R>0 and vice versa.

    prev_r_status: {lk: bool(R>0)} from previous step.
    Returns updated status and transition counts.
    """
    stats = {"r0_to_rplus": 0, "rplus_to_r0": 0,
             "total_rplus": 0, "total_r0": 0}
    new_status = {}

    for lk in state.alive_l:
        has_r = state.R.get(lk, 0.0) > 0
        new_status[lk] = has_r
        if has_r:
            stats["total_rplus"] += 1
        else:
            stats["total_r0"] += 1

        was_r = prev_r_status.get(lk, False)
        if has_r and not was_r:
            stats["r0_to_rplus"] += 1
        elif not has_r and was_r:
            stats["rplus_to_r0"] += 1

    return new_status, stats


# ================================================================
# V6.0 ENGINE
# ================================================================
class V60Engine(V49Engine):
    """
    V4.9 + Recurrence Architecture (Layer 1 + Layer 2).

    Layer 1a: Topological E_ij (no Π in denominator)
    Layer 1b: Activity amplification (E→latent before realizer)
    Layer 2:  Resonance Echo (R>0 snaps → L_ij scar)

    Full step_window override. All v4.9 P1-P8 retained except:
    - Transition field E_ij formula changed
    - Brittleness deposits rerouted for R>0 snaps
    - Activity amplification inserted before realizer
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V60EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.scar_registry = {}
        self.reformation_stats = {}
        self.r_transition_stats = {}
        self.recurrence_stats = {}
        self.prev_r_status = {}

    def step_window(self, steps=V60_WINDOW):
        """
        PER-STEP:
          1.    [Layer 1b] Activity amplification (E→latent)
          2.    realizer.step()
          3-4.  physics.step_pre_chemistry, Z phase correction
          5-6.  chem, physics.step_resonance
          7-8.  grower + g_scores, intruder
          9.    physics.step_decay_exclusion
          10.   Z decay correction
          11.   Phase 1: history tensor update + decay correction
          12.   [MODIFIED] Brittleness with Resonance Echo
          13.   Phase 3: substrate diffusion
          14.   [MODIFIED] Transition field (topological E_ij)
          15-16. Phase 6: tension-gated decay, consumption + cascade
          17.   Background seeding (v4.9 canonical — KEPT)

        POST-LOOP:
          18.   Phase 5: stateless Π
          19.   R transition tracking
          20.   Reformation detection
          21+   void metrics, plasticity, cooling, islands,
                avalanche, observer, drift (unchanged from v4.9)
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        p = self.island_tracker.params
        z_enabled = p.z_coupling_enabled
        hist_enabled = p.history_enabled
        void_enabled = p.void_enabled
        recur_enabled = p.recurrence_enabled

        wz = {"hardened": 0, "softened": 0, "tensioned": 0}
        wh = {"matured": 0, "snapped": 0, "suppressed_nodes": 0,
              "void_deposited": 0.0,
              "echo_deposits": 0, "echo_latent_total": 0.0}
        wv = {"consumed_events": 0, "void_induced_births": 0,
              "diffusion_events": 0, "void_to_active": 0,
              "cascade_splashes": 0,
              "gen_births": 0, "gen_candidates": 0,
              "gen_max_T": 0.0, "gen_max_delta": 0.0}
        wr = {"amplified_pairs": 0,
              "r0_to_rplus_total": 0, "rplus_to_r0_total": 0}

        for step in range(steps):
            pre_alive_l = set(self.state.alive_l) if void_enabled else set()

            # ── 1: [Layer 1b] Activity Amplification ──
            if recur_enabled:
                aa = apply_activity_amplification(
                    self.state, self.substrate)
                wr["amplified_pairs"] += aa["amplified_pairs"]

            # ── 2: Canonical realizer (UNTOUCHED) ──
            self.realizer.step(self.state)

            # ── 3-4: Physics + Z phase correction ──
            self.physics.step_pre_chemistry(self.state)
            if z_enabled:
                zp = apply_z_phase_correction(self.state, p)
                wz["tensioned"] += zp["tensioned"]

            # ── 5-6: Chemistry + Resonance ──
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)

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

            # ── 9: Canonical decay + exclusion ──
            self.physics.step_decay_exclusion(self.state)

            # ── 10: Z decay correction ──
            if z_enabled:
                zd = apply_z_decay_correction(self.state, p)
                wz["hardened"] += zd["hardened"]
                wz["softened"] += zd["softened"]

            # ── 11: Phase 1 history tensor + decay correction ──
            if hist_enabled:
                self.link_history.update_step(self.state)
                hd = apply_history_decay_correction(
                    self.state, self.link_history, p)
                wh["matured"] += hd["matured"]

            # ── 12: [MODIFIED] Brittleness with Resonance Echo ──
            if hist_enabled:
                if recur_enabled:
                    hb = apply_brittleness_v60(
                        self.state, self.link_history, p,
                        self.void_field, self.void_active,
                        self.scar_registry, self.window_count)
                    wh["echo_deposits"] += hb["echo_deposits"]
                    wh["echo_latent_total"] += hb["echo_latent_total"]
                else:
                    from esde_v49_engine import apply_history_brittleness
                    hb = apply_history_brittleness(
                        self.state, self.link_history, p,
                        self.void_field, self.void_active)
                wh["snapped"] += hb["snapped"]
                wh["void_deposited"] += hb.get("void_deposited", 0.0)

            # ── 13: Phase 3 substrate diffusion ──
            if void_enabled and self.void_active:
                sd = apply_void_substrate_diffusion(
                    self.void_field, self.state, self.substrate, p,
                    self.void_active)
                wv["diffusion_events"] += sd["diffusion_events"]
                wv["void_to_active"] += sd["void_to_active"]
                wv["c_diff"] = sd.get("c_diff", 0)

            # ── 14: [MODIFIED] Transition field (topological E_ij) ──
            if void_enabled and self.void_active:
                if recur_enabled:
                    gn = apply_transition_field_v60(
                        self.state, self.void_field, p, self.substrate,
                        self.void_active)
                else:
                    from esde_v49_engine import apply_void_transition_field
                    gn = apply_void_transition_field(
                        self.state, self.void_field, p, self.substrate,
                        self.void_active)
                wv["gen_births"] += gn["gen_births"]
                wv["gen_candidates"] += gn["gen_candidates"]
                if gn["gen_max_T"] > wv.get("gen_max_T", 0):
                    wv["gen_max_T"] = gn["gen_max_T"]
                if gn["gen_max_delta"] > wv.get("gen_max_delta", 0):
                    wv["gen_max_delta"] = gn["gen_max_delta"]

            # ── 15-16: Phase 6 tension-gated decay + consumption ──
            if void_enabled:
                apply_void_topological_decay(
                    self.void_field, self.state, self.void_active, p)
                vc = apply_void_consumption(
                    self.state, self.void_field, p, pre_alive_l,
                    self.void_active, self.substrate)
                wv["consumed_events"] += vc["consumed_events"]
                wv["void_induced_births"] += vc["void_induced_births"]
                wv["cascade_splashes"] += vc.get("cascade_splashes", 0)

            # ── 17: Background seeding (v4.9 canonical — KEPT) ──
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
                                1 if self.state.rng.random() < 0.5 else 2)

            # ── Per-step R transition tracking ──
            if recur_enabled:
                self.prev_r_status, rt = track_r_transitions(
                    self.state, self.prev_r_status)
                wr["r0_to_rplus_total"] += rt["r0_to_rplus"]
                wr["rplus_to_r0_total"] += rt["rplus_to_r0"]

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
        self.void_stats["mean_V"] = round(float(np.mean(
            self.void_field[list(self.state.alive_n)])), 4) \
            if self.state.alive_n else 0
        self.void_stats["max_V"] = round(
            float(np.max(self.void_field)), 4)
        self.void_stats["active_V_nodes"] = int(
            np.sum(self.void_field > 0.01))

        # Phase 5: Stateless Π (v4.9 unchanged)
        window_snaps = wh.get("snapped", 0)
        alive_links = len(self.state.alive_l)
        self.current_pi = p.proliferation_pi_max * math.tanh(
            window_snaps / max(1, alive_links))
        p.proliferation_pi = self.current_pi

        # Recurrence stats
        if recur_enabled:
            ref = check_reformations(
                self.state, self.scar_registry, self.window_count)
            self.reformation_stats = ref

            # Final R snapshot for this window
            _, rt_final = track_r_transitions(
                self.state, self.prev_r_status)
            self.r_transition_stats = {
                "r0_to_rplus": wr["r0_to_rplus_total"],
                "rplus_to_r0": wr["rplus_to_r0_total"],
                "total_rplus": rt_final["total_rplus"],
                "total_r0": rt_final["total_r0"],
                "amplified_pairs": wr["amplified_pairs"],
                "active_scars": len(self.scar_registry),
            }
        else:
            self.reformation_stats = {}
            self.r_transition_stats = {}

        self.recurrence_stats = {
            **self.r_transition_stats,
            **self.reformation_stats,
        }

        # Mandatory void metrics (GPT audit)
        alive_nodes_list = list(self.state.alive_n)
        self.void_stats["total_void_mass"] = round(
            float(np.sum(self.void_field)), 4)
        self.void_stats["void_variance"] = round(float(np.var(
            self.void_field[alive_nodes_list])), 6) \
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

        hc = len(self.hardening)
        hv = list(self.hardening.values())
        mh = float(np.mean(hv)) if hv else 0.0

        anom = []
        if isum["n_encapsulated"] > 0:
            anom.append(f"[ENCAP] {isum['n_encapsulated']}")
        if wh.get("snapped", 0) > 0:
            anom.append(f"[SNAP] {wh['snapped']}")
        if wh.get("echo_deposits", 0) > 0:
            anom.append(f"[ECHO] {wh['echo_deposits']}")
        if self.history_stats.get("avalanche_events", 0) > 0:
            anom.append(f"[AVALANCHE]")
        if wv.get("consumed_events", 0) > 0:
            anom.append(f"[VOID_CONSUME] {wv['consumed_events']}")
        if self.recurrence_stats.get("reformations", 0) > 0:
            anom.append(f"[REFORM] {self.recurrence_stats['reformations']}")

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

        # Drift Loops A+B (v4.8c)
        if p.drift_enabled:
            post_links = f.alive_links
            post_z0 = self._count_z0_links()
            if self.prev_alive_links > 0:
                delta_L = post_links - self.prev_alive_links
            else:
                delta_L = 0; self.prev_alive_links = post_links
            if self.prev_z0_links > 0:
                delta_Z0 = post_z0 - self.prev_z0_links
            else:
                delta_Z0 = 0; self.prev_z0_links = post_z0
            alpha_t = p.alpha_min + p.alpha_beta * math.tanh(
                abs(delta_L) / p.alpha_v_scale)
            self._drift_window_counter += 1
            applied = False
            if self._drift_window_counter >= p.drift_interval:
                self._drift_window_counter = 0; applied = True
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
                "window": f.window, "alpha_t": round(alpha_t, 6),
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
