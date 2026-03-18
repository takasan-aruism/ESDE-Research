#!/usr/bin/env python3
"""
ESDE v5.0 — Circulation Dynamics
==================================
Phase : v5.0 (System-Level Circulation)
Role  : Claude (Implementation + Design)
Arch  : Claude Circulation Audit → Taka directive

System-level redesign: close ALL broken feedback loops.

Fix 1 — Proximity Resonance:
  R=0 links protected by neighbor structure.
  restore = S_lost × tanh(neighbor_S_sum)
  No arbitrary constants. tanh provides natural [0,1] bound.

Fix 2 — Resonance Heat:
  R>0 links return E to endpoints.
  heat = R × S / alive_links
  Genesis principle: closed loops are energy containers.

Fix 3 — Dissipation Capture:
  S decay → V at endpoints.
  capture = S_lost / degree(node)
  Isolated nodes capture more. Dense nodes less. Self-scaling.

Fix 4 — Multi-Source Π:
  Π = Π_max × tanh(snap_tension + entropy_tension + energy_tension)
  Π never collapses to zero while system has ANY structural tension.

Dynamic Constants:
  bg_prob modulated by Π (crisis → more injection)
  E_inject = 1 - E[node] (fill gap, not fixed amount)
  All scaling from system ratios. No human-set magnitudes.

All v4.9 Phase 1–8 mechanics retained. Frozen operators untouched.
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
    apply_history_decay_correction,
    apply_history_brittleness,
    apply_history_plasticity_suppression,
    apply_avalanche,
    apply_void_transition_field,
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
V50_WINDOW = 50


# ================================================================
# PARAMETERS
# ================================================================
@dataclass
class V50EncapsulationParams(V49EncapsulationParams):
    """v5.0: Circulation dynamics.
    Most scaling is derived from system state at runtime.
    Only structural toggles and Π_max remain as configured values.
    """
    circulation_enabled: bool = True


# ================================================================
# FIX 1: PROXIMITY RESONANCE
# ================================================================
def apply_proximity_resonance(state, pre_decay_S):
    """
    Post-decay correction for R=0 links.

    For each alive link with R=0:
      S_lost = pre_decay - current
      neighbor_S = sum of S at both endpoints' OTHER alive links
      proximity = tanh(neighbor_S)   ← [0,1], no constants
      S += S_lost × proximity

    Near structure → most of decay restored.
    Isolated → no restoration (proximity ≈ 0), natural death.
    After cycle forms → R>0, this mechanism yields to canonical resonance.
    """
    stats = {"proximity_restored": 0, "proximity_total_restore": 0.0}

    for lk in list(state.alive_l):
        if state.R.get(lk, 0.0) > 0:
            continue
        s_before = pre_decay_S.get(lk, 0.0)
        s_now = state.S.get(lk, 0.0)
        s_lost = s_before - s_now
        if s_lost <= 0:
            continue

        n1, n2 = lk
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

        proximity = math.tanh(nb_S)
        restore = s_lost * proximity
        if restore > 0.0001:
            state.S[lk] = min(1.0, s_now + restore)
            stats["proximity_restored"] += 1
            stats["proximity_total_restore"] += restore

    return stats


# ================================================================
# FIX 2: RESONANCE HEAT
# ================================================================
def apply_resonance_heat(state):
    """
    R>0 links return energy to endpoints.

    heat = R × S / alive_links

    Genesis v0.3: "Closed paths are energy containers."
    This makes that literal: resonant loops locally regenerate E.
    Normalization by alive_links → total heat scales with system.
    """
    stats = {"heat_events": 0, "heat_total": 0.0}
    alive_links = len(state.alive_l)
    if alive_links == 0:
        return stats

    for lk in state.alive_l:
        R_val = state.R.get(lk, 0.0)
        if R_val <= 0:
            continue
        s_val = state.S.get(lk, 0.0)
        heat = R_val * s_val / alive_links
        if heat > 0.00001:
            n1, n2 = lk
            state.E[n1] = min(1.0, state.E[n1] + heat)
            state.E[n2] = min(1.0, state.E[n2] + heat)
            stats["heat_events"] += 1
            stats["heat_total"] += heat * 2

    return stats


# ================================================================
# FIX 3: DISSIPATION CAPTURE
# ================================================================
def apply_dissipation_capture(state, void_field, void_active,
                               pre_decay_S, params):
    """
    S decay → V at endpoints.

    capture_per_endpoint = S_lost / degree(node)

    Isolated dying nodes → high V deposit (degree=1).
    Dense nodes → distributed V (degree=many).
    Dead links (killed by decay) → full S captured.
    v_max cap prevents overflow. Topological decay removes excess.

    No arbitrary constants. Ratio of S_lost to degree is
    the natural unit of "structural potential released."
    """
    stats = {"capture_events": 0, "capture_total": 0.0}
    v_max = params.void_v_max

    for lk, s_before in pre_decay_S.items():
        if lk in state.alive_l:
            s_now = state.S[lk]
        else:
            s_now = 0.0  # link died during decay
        s_lost = s_before - s_now
        if s_lost <= 0.0001:
            continue

        n1, n2 = lk
        deg1 = max(1, _node_active_degree(state, n1))
        deg2 = max(1, _node_active_degree(state, n2))

        cap1 = s_lost / deg1
        cap2 = s_lost / deg2

        void_field[n1] = min(v_max, void_field[n1] + cap1)
        void_field[n2] = min(v_max, void_field[n2] + cap2)

        if cap1 > 0.001:
            void_active.add(n1)
        if cap2 > 0.001:
            void_active.add(n2)

        stats["capture_events"] += 1
        stats["capture_total"] += cap1 + cap2

    return stats


# ================================================================
# V5.0 ENGINE
# ================================================================
class V50Engine(V49Engine):
    """
    V49Engine + Circulation Dynamics.

    Four closed feedback loops added:
      1. Proximity Resonance (S bootstrap for R=0 links)
      2. Resonance Heat (R>0 → E return)
      3. Dissipation Capture (S decay → V)
      4. Multi-Source Π (snap + entropy + energy tensions)

    Dynamic background seeding replaces fixed-rate injection.

    Full override of step_window(). All v4.9 P1-P8 retained.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V50EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.circulation_stats = {}
        self.prev_entropy_delta = 0.0  # for multi-source Π

    def step_window(self, steps=V50_WINDOW):
        """
        Physics loop with circulation dynamics.

        PER-STEP:
          1-2.  realizer, physics.step_pre_chemistry
          3.    Z phase correction
          4-5.  chem, physics.step_resonance
          6.    [NEW] Resonance Heat (R>0 → E)
          7-8.  grower + g_scores, intruder
          9.    [NEW] pre-decay S snapshot
          10.   physics.step_decay_exclusion
          11.   Z decay correction
          12.   [NEW] Proximity Resonance (R=0 link protection)
          13.   [NEW] Dissipation Capture (S lost → V)
          14-16. Phase 1: history tensor, decay correction, brittleness
          17.   Phase 3: substrate diffusion
          18.   Phase 8: transition field (T>E → birth)
          19-20. Phase 6: tension-gated decay, consumption + cascade
          21.   [MODIFIED] Dynamic background seeding

        POST-LOOP:
          22.   [MODIFIED] Multi-source Π
          23-30. Void metrics, plasticity, cooling, islands,
                 avalanche, observer, drift (unchanged from v4.9)
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
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
              "capture_events": 0, "capture_total": 0.0}

        # Dynamic bg_prob: modulated by Π (crisis → more seeding)
        pi_ratio = self.current_pi / max(0.001, p.proliferation_pi_max)
        bg_prob_eff = bg_prob * (1.0 + pi_ratio) if circ_enabled else bg_prob

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

            # ── 6: [NEW] Resonance Heat ──
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

            # ── 9: [NEW] Pre-decay S snapshot ──
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

            # ── 12: [NEW] Proximity Resonance ──
            if circ_enabled and pre_decay_S:
                pr = apply_proximity_resonance(self.state, pre_decay_S)
                wc["proximity_restored"] += pr["proximity_restored"]
                wc["proximity_total_restore"] += pr["proximity_total_restore"]

            # ── 13: [NEW] Dissipation Capture ──
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

            # ── 18: Phase 8 transition field ──
            if void_enabled and self.void_active:
                gn = apply_void_transition_field(
                    self.state, self.void_field, p, self.substrate,
                    self.void_active)
                wv["gen_births"] += gn["gen_births"]
                wv["gen_candidates"] += gn["gen_candidates"]
                if gn["gen_max_T"] > wv.get("gen_max_T", 0):
                    wv["gen_max_T"] = gn["gen_max_T"]
                if gn["gen_max_delta"] > wv.get("gen_max_delta", 0):
                    wv["gen_max_delta"] = gn["gen_max_delta"]

            # ── 19-20: Phase 6 decay + consumption ──
            if void_enabled:
                apply_void_topological_decay(
                    self.void_field, self.state, self.void_active, p)
                vc = apply_void_consumption(
                    self.state, self.void_field, p, pre_alive_l,
                    self.void_active, self.substrate)
                wv["consumed_events"] += vc["consumed_events"]
                wv["void_induced_births"] += vc["void_induced_births"]
                wv["cascade_splashes"] += vc.get("cascade_splashes", 0)

            # ── 21: [MODIFIED] Dynamic background seeding ──
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
                mk = self.state.rng.random(na) < bg_prob_eff
                for idx in range(na):
                    if mk[idx]:
                        t_node = int(self.state.rng.choice(aa, p=pd))
                        if circ_enabled:
                            # Dynamic E: fill half the gap (state-dependent,
                            # preserves E gradient as information source)
                            e_gap = 1.0 - self.state.E[t_node]
                            self.state.E[t_node] = min(
                                1.0, self.state.E[t_node] + e_gap * 0.5)
                        else:
                            self.state.E[t_node] = min(
                                1.0, self.state.E[t_node] + 0.3)
                        if (self.state.Z[t_node] == 0
                                and self.state.rng.random() < 0.5):
                            self.state.Z[t_node] = (
                                1 if self.state.rng.random() < 0.5 else 2)

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

        # ── [MODIFIED] Multi-Source Π ──
        window_snaps = wh.get("snapped", 0)
        alive_links = len(self.state.alive_l)

        if circ_enabled:
            # Three tension sources — all naturally [0, ∞), tanh bounds
            # NOTE (V50-2): In early windows (before resonance heat
            # raises mean_E), tension_energy dominates (0.3–0.7)
            # while snap/entropy tensions are ~0.001–0.01. This
            # creates a startup transient where Π ≈ 5–10 from energy
            # deficit alone, not structural crisis. Once Fix 2 raises
            # mean_E, tension_energy drops and structural tensions
            # take over. This is expected and self-correcting.
            tension_snap = window_snaps / max(1, alive_links)

            tension_entropy = abs(self.prev_entropy_delta)

            alive_nodes_arr = list(self.state.alive_n)
            if alive_nodes_arr:
                mean_E = float(sum(
                    self.state.E[n] for n in alive_nodes_arr
                ) / len(alive_nodes_arr))
            else:
                mean_E = 0.0
            tension_energy = max(0.0, 1.0 - mean_E)

            self.current_pi = p.proliferation_pi_max * math.tanh(
                tension_snap + tension_entropy + tension_energy)
        else:
            # v4.9 fallback: snap-only Π
            self.current_pi = p.proliferation_pi_max * math.tanh(
                window_snaps / max(1, alive_links))

        p.proliferation_pi = self.current_pi

        # Circulation stats
        self.circulation_stats = wc
        self.circulation_stats["dynamic_bg_prob"] = round(bg_prob_eff, 6)
        if circ_enabled:
            self.circulation_stats["pi_tension_snap"] = round(
                tension_snap, 6)
            self.circulation_stats["pi_tension_entropy"] = round(
                tension_entropy, 6)
            self.circulation_stats["pi_tension_energy"] = round(
                tension_energy, 6)

        # Update bg_prob for next window (Π may have changed)
        # (stored for calibrate logging only; actual bg_prob_eff is
        #  recomputed at start of each window)

        # Mandatory void metrics (GPT audit §LOGGING)
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

        # Store entropy_delta for next window's multi-source Π
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

        # ── Drift Loops A+B (from v4.8c) ──
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
