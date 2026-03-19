#!/usr/bin/env python3
"""
ESDE v7.3 — Stress Equilibrium + 代謝モデル
==============================================
Physical: V72 (V43 + dynamic equilibrium stress)
Virtual: virtual_layer_v2.py (budget=1 metabolism)
"""

import sys, math, time
import numpy as np
from pathlib import Path
from collections import Counter
from dataclasses import dataclass

_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
_SEMANTIC_DIR = _PIPELINE_DIR.parent
_V4_PIPELINE = _SEMANTIC_DIR / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_REPO_ROOT = _SEMANTIC_DIR.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_PIPELINE_DIR), str(_V43_DIR),
          str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum')

from esde_v43_engine import (
    V43Engine, EncapsulationParams, V43StateFrame,
    find_islands_sets, evaluate_milestones, WINDOW,
    apply_semantic_pressure,
)
from esde_v41_engine import MIN_C_NODES_FOR_VALID, N_REGIONS
from v19g_canon import K_LEVELS, BASE_PARAMS, BIAS, compute_J, select_k_star
# Import virtual layer v2
from virtual_layer_v2 import VirtualLayer


def compute_omega(state, lk):
    """Ω_ij = degree_i + degree_j. Purely topological."""
    n1, n2 = lk
    deg1 = sum(1 for nb in state.neighbors(n1)
               if state.key(n1, nb) in state.alive_l)
    deg2 = sum(1 for nb in state.neighbors(n2)
               if state.key(n2, nb) in state.alive_l)
    return deg1 + deg2


def apply_stress_decay(state, stress_intensity):
    """
    Post-correction. Stress scaled by dynamic equilibrium.
    stress_intensity = current_links / EMA(past_links).
    > 1.0: overgrown → stress ON. < 1.0: depleted → growth boost.
    """
    stats = {"stressed": 0, "calcified": 0, "mean_omega": 0.0}
    if not state.alive_l:
        return stats

    omegas = {}
    for lk in state.alive_l:
        omegas[lk] = compute_omega(state, lk)

    omega_values = list(omegas.values())
    mean_omega = sum(omega_values) / len(omega_values) if omega_values else 1.0
    stats["mean_omega"] = round(mean_omega, 2)

    global_pressure = stress_intensity - 1.0

    for lk in list(state.alive_l):
        omega = omegas.get(lk, 0)
        r = state.R.get(lk, 0.0)
        s = state.S.get(lk, 0.0)
        if s <= 0:
            continue

        omega_ratio = omega / max(1.0, mean_omega)
        vulnerability = 1.0 - r
        penalty = s * global_pressure * omega_ratio * vulnerability

        if penalty > 0:
            state.S[lk] = max(0.0, s - penalty)
            stats["stressed"] += 1
            if state.S[lk] <= state.EXTINCTION:
                state.S[lk] = 0.0
                state.kill_link(lk)
        elif penalty < 0 and global_pressure < 0:
            boost = min(-penalty, 1.0 - s)
            state.S[lk] = s + boost
            stats["calcified"] += 1

    return stats

V73_WINDOW = 50


@dataclass
class V73EncapsulationParams(EncapsulationParams):
    stress_enabled: bool = True
    virtual_enabled: bool = True


class V73Engine(V43Engine):

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V73EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.virtual = VirtualLayer()
        self.virtual_stats = {}
        self.stress_stats = {}
        self.window_count = 0
        self.link_ema = None

    def step_window(self, steps=V73_WINDOW):
        t0 = time.time()
        bg_prob = BASE_PARAMS["background_injection_prob"]
        p = self.island_tracker.params
        stress_enabled = p.stress_enabled

        ws = {"stressed": 0, "calcified": 0, "suppressed": 0,
              "mean_omega": 0.0, "stress_intensity": 1.0, "link_ema": 0.0}

        # ── PHYSICS LOOP (V43 canonical) ──
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

            # Background seeding
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

        # ── STRESS (post-loop, dynamic equilibrium) ──
        if stress_enabled:
            current_links = len(self.state.alive_l)
            if self.link_ema is None:
                self.link_ema = float(current_links)
            tau = min(self.window_count + 1, 20)
            alpha_ema = 2.0 / (tau + 1.0)
            self.link_ema = alpha_ema * current_links + \
                (1 - alpha_ema) * self.link_ema

            stress_intensity = current_links / max(1.0, self.link_ema)
            ws["stress_intensity"] = round(stress_intensity, 4)
            ws["link_ema"] = round(self.link_ema, 1)

            sd = apply_stress_decay(self.state, stress_intensity)
            ws["stressed"] = sd["stressed"]
            ws["calcified"] = sd["calcified"]
            ws["mean_omega"] = sd["mean_omega"]

        self.stress_stats = ws

        # ── OBSERVATION (V43 canonical) ──
        ps = apply_semantic_pressure(
            self.state, self.substrate,
            self.pressure_params, self.island_tracker,
            self.state.rng)

        isl_m = find_islands_sets(self.state, 0.20)
        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)
        self.last_isum = isum

        # Observer
        isl_s = find_islands_sets(self.state, 0.30)
        isl_w = find_islands_sets(self.state, 0.10)
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

        # ── VIRTUAL LAYER ──
        if p.virtual_enabled:
            vs = self.virtual.step(
                self.state, f.window,
                islands=self.island_tracker.islands,
                substrate=self.substrate)
            self.virtual_stats = vs
        else:
            self.virtual_stats = {}

        return f
