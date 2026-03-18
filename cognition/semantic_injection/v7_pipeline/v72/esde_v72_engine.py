#!/usr/bin/env python3
"""
ESDE v7.2 — Stress Equilibrium + World Induction
===================================================
Physical Layer: V43 + Spatial Stress (Ω_ij = deg_i + deg_j)
Virtual Layer: virtual_layer.py (unchanged)

Ω creates dynamic equilibrium:
  - High Ω (dense) → links decay faster (unless R>0 protects)
  - Low Ω (branches) → links calcify (survive longer → scaffold for triads)
  - Birth barrier: E_ij = tanh(Ω_ij) — hard to add links in dense areas

No fixed constants. Ω is purely topological.
Frozen operators untouched. Stress applied as post-corrections.

Inheritance: V72Engine(V43Engine) + stress functions + VirtualLayer
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
_PIPELINE_DIR = _SCRIPT_DIR.parent
_V4_PIPELINE = _PIPELINE_DIR.parent / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_REPO_ROOT = _V4_PIPELINE.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_PIPELINE_DIR), str(_V43_DIR), str(_V41_DIR),
          str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v43_engine import (
    V43Engine, EncapsulationParams, V43StateFrame,
    find_islands_sets, evaluate_milestones, WINDOW,
)
from esde_v41_engine import MIN_C_NODES_FOR_VALID, N_REGIONS
from v19g_canon import K_LEVELS, BASE_PARAMS, BIAS, compute_J, select_k_star
from virtual_layer import VirtualLayer


# ================================================================
V72_WINDOW = 50


@dataclass
class V72EncapsulationParams(EncapsulationParams):
    """V43 params + stress/virtual toggles."""
    stress_enabled: bool = True
    virtual_enabled: bool = True


# ================================================================
# STRESS FUNCTIONS
# ================================================================
def compute_omega(state, lk):
    """Ω_ij = degree_i + degree_j. Purely topological."""
    n1, n2 = lk
    deg1 = 0
    deg2 = 0
    for nb in state.neighbors(n1):
        if state.key(n1, nb) in state.alive_l:
            deg1 += 1
    for nb in state.neighbors(n2):
        if state.key(n2, nb) in state.alive_l:
            deg2 += 1
    return deg1 + deg2


def apply_stress_decay(state):
    """
    Post-correction after canonical step_decay_exclusion.

    Effective_Decay = base_decay × Ω × (1 - R)  [Gemini spec §3A]

    Canonical decay already applied base_decay. We apply the Ω×(1-R) factor
    as additional S reduction. Self-scaling: normalized by mean Ω.

    Low Ω (branches): mild additional decay → scaffolding survives.
    High Ω (dense, R=0): heavy additional decay → junk cleared.
    High Ω (dense, R>0): immune → resonant structures persist.
    """
    stats = {"stressed": 0, "calcified": 0, "mean_omega": 0.0}

    if not state.alive_l:
        return stats

    # Compute Ω for all alive links
    omegas = {}
    for lk in state.alive_l:
        omegas[lk] = compute_omega(state, lk)

    omega_values = list(omegas.values())
    mean_omega = sum(omega_values) / len(omega_values) if omega_values else 1.0
    stats["mean_omega"] = round(mean_omega, 2)

    for lk in list(state.alive_l):
        omega = omegas.get(lk, 0)
        r = state.R.get(lk, 0.0)
        s = state.S.get(lk, 0.0)

        if s <= 0:
            continue

        # Stress factor: Ω relative to system mean.
        # Self-scaling — no fixed constants (#V72-3 fix).
        omega_ratio = omega / max(1.0, mean_omega)

        # R>0 immune: (1 - R) [Gemini spec §3A]
        vulnerability = 1.0 - r

        # Penalty = S × (excess over mean) × vulnerability
        # omega_ratio > 1: overcrowded → positive penalty (decay)
        # omega_ratio < 1: sparse → negative penalty (scaffold)
        penalty = s * (omega_ratio - 1.0) * vulnerability

        if penalty > 0:
            state.S[lk] = max(0.0, s - penalty)
            stats["stressed"] += 1
            if state.S[lk] <= state.EXTINCTION:
                state.S[lk] = 0.0
                state.kill_link(lk)
        elif penalty < 0:
            # Calcification: sparse branches strengthen.
            # Boost = -penalty × (1 - omega_ratio)
            # Self-scaling: sparser branch → stronger boost.
            # No fixed 0.5 factor (#V72-3 fix).
            sparsity = 1.0 - omega_ratio  # 0..1
            boost = min(-penalty * sparsity, 1.0 - s)
            state.S[lk] = s + boost
            stats["calcified"] += 1

    return stats


def apply_stress_formation_barrier(state, substrate):
    """
    Pre-realizer: suppress latent in high-Ω regions.

    barrier = tanh(Ω / mean_Ω)  — state-dependent scaling.
    No fixed /6.0 constant (#V72-2/#V72-3 fix).

    mean_Ω normalizes: barrier responds to system's current density.
    Dense system → mean_Ω high → each node needs higher Ω to be blocked.
    Sparse system → mean_Ω low → even moderate Ω blocks formation.
    """
    stats = {"suppressed": 0}

    # Compute mean degree across alive nodes
    degree_sum = 0
    degree_count = 0
    for n in state.alive_n:
        deg = 0
        for nb in state.neighbors(n):
            if state.key(n, nb) in state.alive_l:
                deg += 1
        degree_sum += deg
        degree_count += 1
    mean_degree = degree_sum / max(1, degree_count)
    # mean_omega for pairs ≈ 2 × mean_degree
    mean_omega_est = max(1.0, 2.0 * mean_degree)

    for n in state.alive_n:
        deg_n = 0
        for nb in state.neighbors(n):
            if state.key(n, nb) in state.alive_l:
                deg_n += 1

        for nb in substrate.get(n, set()):
            if nb not in state.alive_n:
                continue
            lk = state.key(n, nb)
            if lk in state.alive_l:
                continue

            cur_L = state.get_latent(n, nb)
            if cur_L <= 0:
                continue

            deg_nb = 0
            for nnb in state.neighbors(nb):
                if state.key(nb, nnb) in state.alive_l:
                    deg_nb += 1

            omega = deg_n + deg_nb
            # State-dependent scaling: barrier relative to system mean
            barrier = math.tanh(omega / mean_omega_est)

            suppressed_L = cur_L * (1.0 - barrier)
            if suppressed_L < cur_L:
                state.set_latent(n, nb, suppressed_L)
                stats["suppressed"] += 1

    return stats


# ================================================================
# V7.2 ENGINE
# ================================================================
class V72Engine(V43Engine):
    """
    V43 (Genesis canon) + Spatial Stress (Ω) + VirtualLayer.

    Physics loop: V43's 7 operators + stress post-corrections.
    Virtual layer: post-loop.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V72EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.virtual = VirtualLayer()
        self.virtual_stats = {}
        self.stress_stats = {}
        self.window_count = 0

    def step_window(self, steps=V72_WINDOW):
        """
        Override V43 step_window to insert stress corrections.

        Per-step loop:
          [canonical 7 operators]
          [stress formation barrier — pre-next-realizer]
          [stress decay — post canonical decay]
          [background seeding]
        Post-loop:
          [V43 observation]
          [virtual layer]
        """
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        p = self.island_tracker.params
        stress_enabled = p.stress_enabled

        ws = {"stressed": 0, "calcified": 0, "suppressed": 0,
              "mean_omega": 0.0}

        for step in range(steps):
            # ── 1: Stress formation barrier (before realizer) ──
            if stress_enabled:
                sf = apply_stress_formation_barrier(
                    self.state, self.substrate)
                ws["suppressed"] += sf["suppressed"]

            # ── 2: Canonical realizer ──
            self.realizer.step(self.state)

            # ── 3-6: Physics + Chemistry + Resonance + Grower ──
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

            # ── 7: Intruder ──
            self.intruder.step(self.state)

            # ── 8: Canonical decay + exclusion ──
            self.physics.step_decay_exclusion(self.state)

            # ── 9: Stress decay (post-correction) ──
            if stress_enabled:
                sd = apply_stress_decay(self.state)
                ws["stressed"] += sd["stressed"]
                ws["calcified"] += sd["calcified"]
                ws["mean_omega"] = sd["mean_omega"]  # last step's value

            # ── 10: Background seeding (canonical) ──
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

        self.stress_stats = ws

        # ════════════════════════════════════════
        # POST-LOOP: V43 observation (reproduced from V43Engine)
        # ════════════════════════════════════════
        # Semantic pressure
        from esde_v43_engine import apply_semantic_pressure
        ps = apply_semantic_pressure(
            self.state, self.substrate,
            self.pressure_params, self.island_tracker,
            self.state.rng)
        self.cooling_stats = ps

        # Island observation
        isl_m = find_islands_sets(self.state, 0.20)
        prev_islands = dict(self.island_tracker.islands)
        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)

        # Observer
        nm_m = {n for isl in isl_m for n in isl}
        isl_s = find_islands_sets(self.state, 0.30)
        isl_w = find_islands_sets(self.state, 0.10)
        nm_s = {n for isl in isl_s for n in isl}
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

        self.window_count += 1

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
        self.last_isum = isum

        # Virtual Layer (World B)
        if p.virtual_enabled:
            vs = self.virtual.step(
                self.state, f.window,
                islands=self.island_tracker.islands,
                substrate=self.substrate)
            self.virtual_stats = vs
        else:
            self.virtual_stats = {}

        return f