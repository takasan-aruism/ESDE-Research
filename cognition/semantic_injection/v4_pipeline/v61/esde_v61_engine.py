#!/usr/bin/env python3
"""
ESDE v6.1 — Activity & Recurrence
====================================
Phase : v6.1 (Cognitive Transition — Layer 1 refined + Layer 2 refined)
Role  : Claude (Implementation)
Arch  : Gemini + Taka | Audit: GPT (v1.3 + Claude interpretation approved)

Base: v6.0 (v4.9 + topological E_ij + activity amplification + resonance echo)

Changes from v6.0:

Layer 1 — action_potential (Energy = Time):
  action_potential[i] += E[i] each step.
  When >= 1.0: node is "active" this step → Realizer evaluates it.
  When < 1.0: node's latent is masked → Realizer skips it.
  Frozen RealizationOperator untouched — input is controlled.
  Existing link physics (decay, resonance, chemistry) NOT gated.

Layer 2 — Mem_ij (Non-Volatile Scar):
  Separate dict from latent field. Not subject to latent_refresh.
  R>0 link snaps → Mem_ij = max(Mem, S × R).
  Each step: L_ij = max(L_ij, Mem_ij) for all Mem entries.
    → latent floor. Realizer sees high L → probabilistic reform.
    → NOT threshold bypass. p_link_birth still gates.
  On successful reformation: Mem *= (1 - Mem), S += Mem_old × (1 - S).
  Per-window decay: Mem *= (1 - snaps/alive_links).
    → crisis clears old scars. stability preserves them.
  No fixed constants anywhere.

Layer 3 — World Induction: DEFERRED.
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
_V60_DIR = _SCRIPT_DIR.parent / "v60"
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

for p in [str(_V60_DIR), str(_V49_DIR), str(_V48C_DIR), str(_V48B_DIR),
          str(_V48_DIR), str(_V46_DIR), str(_V45A_DIR), str(_V44_DIR),
          str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v60_engine import (
    V60Engine, V60EncapsulationParams, V60_WINDOW,
    apply_transition_field_v60,
    apply_activity_amplification,
    track_r_transitions,
)
from esde_v49_engine import (
    apply_history_decay_correction,
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
V61_WINDOW = 50


# ================================================================
@dataclass
class V61EncapsulationParams(V60EncapsulationParams):
    """v6.1: No new physics constants."""
    pass


# ================================================================
# LAYER 2: NON-VOLATILE SCAR BRITTLENESS
# ================================================================
def apply_brittleness_v61(state, tensor, params, void_field, void_active,
                           mem, window_count):
    """
    Brittleness snap with Mem_ij (non-volatile scar).

    R>0 snap: Mem_ij = max(Mem_ij, S × R)
      → stored in separate dict, not in latent field.
    R=0 snap: void deposit (v4.9 canonical).
    """
    stats = {"snapped": 0, "void_deposited": 0.0,
             "mem_deposits": 0, "mem_total": 0.0}
    threshold = params.history_str_fracture_threshold
    snap_stress = params.history_str_snap_stress
    void_k = params.void_k
    void_enabled = params.void_enabled
    v_max = params.void_v_max

    for lk in list(state.alive_l):
        h_str = tensor.h_str.get(lk, 0.0)
        if h_str < threshold:
            continue
        s_val = state.S.get(lk, 0.0)
        if s_val >= snap_stress:
            continue

        h_age = tensor.h_age.get(lk, 0.0)
        r_val = state.R.get(lk, 0.0)
        n1, n2 = lk
        s_at_death = s_val
        r_at_death = r_val

        state.S[lk] = 0.0
        state.kill_link(lk)
        stats["snapped"] += 1

        if r_at_death > 0:
            # Non-volatile scar
            deposit = s_at_death * r_at_death
            if deposit > 0.001:
                mem[lk] = max(mem.get(lk, 0.0), deposit)
                stats["mem_deposits"] += 1
                stats["mem_total"] += deposit
        else:
            # R=0: void deposit (canonical)
            if void_enabled and h_age > 0:
                deposit = void_k * h_age
                void_field[n1] = min(v_max, void_field[n1] + deposit)
                void_field[n2] = min(v_max, void_field[n2] + deposit)
                void_active.add(n1)
                void_active.add(n2)
                stats["void_deposited"] += deposit * 2

    return stats


# ================================================================
# MEM LATENT FLOOR
# ================================================================
def apply_mem_latent_floor(state, mem):
    """
    Each step: for all Mem entries, ensure L_ij >= Mem_ij.
    Latent_refresh may have decayed L below the scar.
    This restores it. Realizer sees high L → high reform chance.
    NOT threshold bypass — p_link_birth still gates.
    """
    stats = {"floor_applied": 0}
    for lk, m_val in mem.items():
        if m_val < 0.001:
            continue
        n1, n2 = lk
        if n1 not in state.alive_n or n2 not in state.alive_n:
            continue
        if lk in state.alive_l:
            continue  # already alive, no need
        cur_L = state.get_latent(n1, n2)
        if cur_L < m_val:
            state.set_latent(n1, n2, m_val)
            stats["floor_applied"] += 1
    return stats


# ================================================================
# POST-REALIZATION: DETECT MEM REFORMATIONS + BONUS
# ================================================================
def apply_mem_reformation(state, mem, pre_alive_l):
    """
    After realizer step: check for new links at Mem locations.
    If reformed:
      S_bonus = Mem_old × (1 - S_current)
      Mem *= (1 - Mem)   (partial consumption)
    """
    stats = {"mem_reforms": 0, "bonus_total": 0.0}
    new_links = state.alive_l - pre_alive_l
    for lk in new_links:
        m_val = mem.get(lk, 0.0)
        if m_val < 0.001:
            continue
        # This link reformed from a scar
        s_now = state.S.get(lk, 0.0)
        bonus = m_val * (1.0 - s_now)
        state.S[lk] = min(1.0, s_now + bonus)
        stats["mem_reforms"] += 1
        stats["bonus_total"] += bonus
        # Partial consumption
        mem[lk] = m_val * (1.0 - m_val)
        if mem[lk] < 0.001:
            del mem[lk]
    return stats


# ================================================================
# V6.1 ENGINE
# ================================================================
class V61Engine(V60Engine):
    """
    V6.0 + action_potential gating + Mem_ij non-volatile scars.

    Full step_window override.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V61EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.action_potential = np.zeros(N, dtype=np.float64)
        self.mem = {}  # {lk: float} non-volatile scar
        self.mem_stats = {}

    def step_window(self, steps=V61_WINDOW):
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
              "mem_deposits": 0, "mem_total": 0.0}
        wv = {"consumed_events": 0, "void_induced_births": 0,
              "diffusion_events": 0, "void_to_active": 0,
              "cascade_splashes": 0,
              "gen_births": 0, "gen_candidates": 0,
              "gen_max_T": 0.0, "gen_max_delta": 0.0}
        wr = {"amplified_pairs": 0,
              "r0_to_rplus_total": 0, "rplus_to_r0_total": 0,
              "mem_reforms_total": 0, "mem_bonus_total": 0.0,
              "floor_applied_total": 0, "active_nodes_total": 0}

        for step in range(steps):
            pre_alive_l = set(self.state.alive_l) if void_enabled else set()

            # ── 1: [v6.1] Accumulate action_potential ──
            if recur_enabled:
                for n in self.state.alive_n:
                    self.action_potential[n] += self.state.E[n]

                # Determine active nodes this step
                active_this_step = set()
                for n in self.state.alive_n:
                    if self.action_potential[n] >= 1.0:
                        active_this_step.add(n)
                        self.action_potential[n] -= 1.0
                wr["active_nodes_total"] += len(active_this_step)

                # Mask latent for inactive nodes (save → zero → restore after realizer)
                saved_latent = {}
                for n in self.state.alive_n:
                    if n in active_this_step:
                        continue
                    # Zero latent for all substrate neighbors of inactive node
                    sub_nbs = self.substrate.get(n, set())
                    for nb in sub_nbs:
                        lk = self.state.key(n, nb)
                        if lk in self.state.alive_l:
                            continue
                        cur_L = self.state.get_latent(n, nb)
                        if cur_L > 0 and lk not in saved_latent:
                            saved_latent[lk] = cur_L
                            self.state.set_latent(n, nb, 0.0)

            # ── 2: [v6.0] Activity Amplification (only active nodes) ──
            if recur_enabled:
                aa = apply_activity_amplification(
                    self.state, self.substrate)
                wr["amplified_pairs"] += aa["amplified_pairs"]

            # ── 3: [v6.1] Mem latent floor (before realizer) ──
            if recur_enabled and self.mem:
                mf = apply_mem_latent_floor(self.state, self.mem)
                wr["floor_applied_total"] += mf["floor_applied"]

            # ── 4: Snapshot for reformation detection ──
            pre_real_alive = set(self.state.alive_l)

            # ── 5: Canonical realizer (UNTOUCHED) ──
            self.realizer.step(self.state)

            # ── 6: [v6.1] Detect Mem reformations + bonus ──
            if recur_enabled and self.mem:
                mr = apply_mem_reformation(
                    self.state, self.mem, pre_real_alive)
                wr["mem_reforms_total"] += mr["mem_reforms"]
                wr["mem_bonus_total"] += mr["bonus_total"]

            # ── 7: Restore masked latent ──
            if recur_enabled:
                for lk, val in saved_latent.items():
                    n1, n2 = lk
                    if lk not in self.state.alive_l:
                        self.state.set_latent(n1, n2, val)

            # ── 8-9: Physics + Z phase correction ──
            self.physics.step_pre_chemistry(self.state)
            if z_enabled:
                zp = apply_z_phase_correction(self.state, p)
                wz["tensioned"] += zp["tensioned"]

            # ── 10-11: Chemistry + Resonance ──
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)

            # ── 12: Grower + g_scores ──
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

            # ── 13: Intruder ──
            self.intruder.step(self.state)

            # ── 14: Canonical decay + exclusion ──
            self.physics.step_decay_exclusion(self.state)

            # ── 15: Z decay correction ──
            if z_enabled:
                zd = apply_z_decay_correction(self.state, p)
                wz["hardened"] += zd["hardened"]
                wz["softened"] += zd["softened"]

            # ── 16: Phase 1 history tensor + decay correction ──
            if hist_enabled:
                self.link_history.update_step(self.state)
                hd = apply_history_decay_correction(
                    self.state, self.link_history, p)
                wh["matured"] += hd["matured"]

            # ── 17: [v6.1] Brittleness with Mem deposit ──
            if hist_enabled:
                if recur_enabled:
                    hb = apply_brittleness_v61(
                        self.state, self.link_history, p,
                        self.void_field, self.void_active,
                        self.mem, self.window_count)
                    wh["mem_deposits"] += hb["mem_deposits"]
                    wh["mem_total"] += hb["mem_total"]
                else:
                    from esde_v49_engine import apply_history_brittleness
                    hb = apply_history_brittleness(
                        self.state, self.link_history, p,
                        self.void_field, self.void_active)
                wh["snapped"] += hb["snapped"]
                wh["void_deposited"] += hb.get("void_deposited", 0.0)

            # ── 18: Phase 3 substrate diffusion ──
            if void_enabled and self.void_active:
                sd = apply_void_substrate_diffusion(
                    self.void_field, self.state, self.substrate, p,
                    self.void_active)
                wv["diffusion_events"] += sd["diffusion_events"]
                wv["void_to_active"] += sd["void_to_active"]
                wv["c_diff"] = sd.get("c_diff", 0)

            # ── 19: Transition field (topological E_ij, v6.0) ──
            if void_enabled and self.void_active:
                gn = apply_transition_field_v60(
                    self.state, self.void_field, p, self.substrate,
                    self.void_active)
                wv["gen_births"] += gn["gen_births"]
                wv["gen_candidates"] += gn["gen_candidates"]
                if gn["gen_max_T"] > wv.get("gen_max_T", 0):
                    wv["gen_max_T"] = gn["gen_max_T"]
                if gn["gen_max_delta"] > wv.get("gen_max_delta", 0):
                    wv["gen_max_delta"] = gn["gen_max_delta"]

            # ── 20-21: Phase 6 tension-gated decay + consumption ──
            if void_enabled:
                apply_void_topological_decay(
                    self.void_field, self.state, self.void_active, p)
                vc = apply_void_consumption(
                    self.state, self.void_field, p, pre_alive_l,
                    self.void_active, self.substrate)
                wv["consumed_events"] += vc["consumed_events"]
                wv["void_induced_births"] += vc["void_induced_births"]
                wv["cascade_splashes"] += vc.get("cascade_splashes", 0)

            # ── 22: Background seeding (canonical) ──
            al = list(self.state.alive_n)
            na = len(al)
            if na > 0:
                aa_arr = np.array(al)
                if BIAS > 0 and gz > 0:
                    ga = self._g_scores[aa_arr]; gs = ga.sum()
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
                        t_node = int(self.state.rng.choice(aa_arr, p=pd))
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

        # Π (v4.9 snap-only)
        window_snaps = wh.get("snapped", 0)
        alive_links = len(self.state.alive_l)
        self.current_pi = p.proliferation_pi_max * math.tanh(
            window_snaps / max(1, alive_links))
        p.proliferation_pi = self.current_pi

        # [v6.1] Mem decay: state-dependent per window
        if recur_enabled and self.mem and alive_links > 0:
            decay_rate = window_snaps / max(1, alive_links)
            if decay_rate > 0.0001:
                dead_keys = []
                for lk in list(self.mem):
                    self.mem[lk] *= (1.0 - decay_rate)
                    if self.mem[lk] < 0.001:
                        dead_keys.append(lk)
                for lk in dead_keys:
                    del self.mem[lk]

        # Mem stats
        self.mem_stats = {
            "mem_size": len(self.mem),
            "mem_mean": round(float(np.mean(list(self.mem.values()))), 4)
                        if self.mem else 0,
            "mem_max": round(max(self.mem.values()), 4)
                       if self.mem else 0,
            "mem_reforms": wr["mem_reforms_total"],
            "mem_bonus_total": round(wr["mem_bonus_total"], 4),
            "floor_applied": wr["floor_applied_total"],
            "active_nodes_mean": round(
                wr["active_nodes_total"] / max(1, steps), 1),
        }

        # Recurrence stats (override v6.0's scar-based)
        _, rt_final = track_r_transitions(
            self.state, self.prev_r_status)
        self.recurrence_stats = {
            "r0_to_rplus": wr["r0_to_rplus_total"],
            "rplus_to_r0": wr["rplus_to_r0_total"],
            "total_rplus": rt_final["total_rplus"],
            "total_r0": rt_final["total_r0"],
            "amplified_pairs": wr["amplified_pairs"],
            "mem_reforms": wr["mem_reforms_total"],
        }
        self.reformation_stats = {
            "reformations": wr["mem_reforms_total"],
            "reforms_alive": wr["mem_reforms_total"],
        }

        # Mandatory void metrics
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

        # Plasticity suppression
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
        if wh.get("mem_deposits", 0) > 0:
            anom.append(f"[MEM] {wh['mem_deposits']}")
        if wr.get("mem_reforms_total", 0) > 0:
            anom.append(f"[REFORM] {wr['mem_reforms_total']}")
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

        # Drift
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
