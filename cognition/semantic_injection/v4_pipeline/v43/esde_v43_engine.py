#!/usr/bin/env python3
"""
ESDE v4.3 — Fractal Inner Topology Engine
============================================
Phase : v4.3 Encapsulation + Inner Expansion
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

PARADIGM SHIFT from v4.2:
  - Destructive waves REMOVED
  - Steady non-destructive semantic pressure replaces catastrophic perturbation
  - Island detection via internal/external density ratio
  - Encapsulated islands: boundary buffered, interior fully dynamic
  - Inner topology observation: entropy, motif recurrence, attractor detection

From v4.2 (GPT clarification):
  - Plasticity retained as WEAK BOUNDARY STABILIZER (factor=1.1, boundary only)
  - Hardening retained as WEAK BOUNDARY BUFFER (bonus=0.05, decay=0.001)
  - Internal topology remains fully dynamic

Milestone progression:
  M1: Topology stable   M2: Clusters persist   M3: Islands encapsulate
  M4: Motifs recur      M5: Differentiated islands

Principle: "Structure first, meaning later."
"""

import numpy as np
import sys, math, time, hashlib, json
from pathlib import Path
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_PIPELINE_DIR = _SCRIPT_DIR.parent
_COGNITION_DIR = _PIPELINE_DIR.parent
_REPO_ROOT = _COGNITION_DIR.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V41_DIR), str(_ENGINE_DIR), str(_COGNITION_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "engine_accel not loaded"

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

from v19g_canon import (
    K_LEVELS, WINDOW, QUIET_STEPS, BASE_PARAMS,
    INJECTION_STEPS, INJECT_INTERVAL, BETA, NODE_DECAY, BIAS, C_MAX,
    E_YIELD_SYN, E_YIELD_AUTO, TOPO_VAR, HYST_THRESHOLD,
    compute_J, select_k_star, init_fert,
)
from esde_v41_engine import (
    build_substrate, assign_regions, N_REGIONS, MIN_C_NODES_FOR_VALID,
    COG_N, COG_PLB, COG_RATE,
)

# ================================================================
# PARAMETERS
# ================================================================
@dataclass
class SemanticPressureParams:
    """Steady, non-destructive semantic pressure."""
    pressure_prob: float = 0.005
    pressure_strength: float = 0.03   # mild phase nudge
    latent_boost: float = 0.05

@dataclass
class EncapsulationParams:
    """Island detection and lifecycle."""
    ratio_threshold: float = 3.0      # internal/external density to encapsulate
    dissolution_threshold: float = 1.5
    min_cluster_size: int = 5
    min_persistence: int = 3          # windows before encapsulation
    s_threshold: float = 0.20
    boundary_hardening_bonus: float = 0.05
    boundary_hardening_decay: float = 0.001

@dataclass
class MotifParams:
    motif_sizes: tuple = (3, 4)
    recurrence_window: int = 5
    min_recurrence: int = 2

# ================================================================
# ISLAND DETECTION
# ================================================================
@dataclass
class IslandState:
    island_id: str
    nodes: frozenset
    boundary_nodes: frozenset
    interior_nodes: frozenset
    born_window: int
    encapsulated_window: int = 0
    last_seen_window: int = 0
    seen_count: int = 1
    density_ratio: float = 0.0
    inner_entropy: float = 0.0
    inner_motif_counts: dict = field(default_factory=dict)
    status: str = "candidate"

def compute_density_ratio(state, nodes, s_thr=0.20):
    internal = 0; external = 0; boundary = set()
    for n in nodes:
        if n not in state.alive_n: continue
        for nb in state.neighbors(n):
            lk = state.key(n, nb)
            if lk not in state.alive_l or state.S[lk] < s_thr: continue
            if nb in nodes:
                internal += 1
            else:
                external += 1; boundary.add(n)
    internal //= 2
    nn = len(nodes)
    max_int = nn * (nn - 1) / 2 if nn > 1 else 1
    max_ext = nn * (state.n_nodes - nn) if nn > 0 else 1
    d_int = internal / max(max_int, 1)
    d_ext = external / max(max_ext, 1)
    return d_int / max(d_ext, 1e-10), internal, external, frozenset(boundary)

def find_inner_motifs(state, interior, s_thr=0.20, sizes=(3, 4)):
    adj = defaultdict(set)
    for n in interior:
        if n not in state.alive_n: continue
        for nb in state.neighbors(n):
            if nb in interior and nb in state.alive_n:
                lk = state.key(n, nb)
                if lk in state.alive_l and state.S[lk] >= s_thr:
                    adj[n].add(nb)
    counts = {}
    if 3 in sizes:
        tri = 0
        for u in adj:
            for v in adj[u]:
                if v <= u: continue
                tri += len(adj[u] & adj[v] - {n for n in range(0) if n <= v})
                # proper counting
        # Recount properly
        tri = 0
        for u in adj:
            for v in adj[u]:
                if v <= u: continue
                for w in adj[u] & adj[v]:
                    if w > v: tri += 1
        counts[3] = tri
    if 4 in sizes and len(interior) < 200:
        sq = 0
        for u in adj:
            for v in adj[u]:
                if v <= u: continue
                for w in adj[u]:
                    if w <= v or w == v: continue
                    for x in adj[w] & adj[v]:
                        if x > w and x != u: sq += 1
        counts[4] = sq
    return counts

def compute_inner_entropy(state, interior):
    zc = Counter(int(state.Z[n]) for n in interior if n in state.alive_n)
    t = sum(zc.values())
    if t == 0: return 0.0
    return -sum((v/t) * math.log2(v/t) for v in zc.values() if v > 0)

# ================================================================
# ISLAND TRACKER
# ================================================================
class IslandTracker:
    def __init__(self, params=None, motif_params=None):
        self.params = params or EncapsulationParams()
        self.motif_params = motif_params or MotifParams()
        self.islands: dict[str, IslandState] = {}
        self.graveyard: dict[str, IslandState] = {}
        self.next_id = 0
        self.window = 0
        self.encapsulation_events = 0
        self.dissolution_events = 0
        self.motif_history: dict[str, list[dict]] = {}

    def _new_id(self):
        self.next_id += 1; return f"ISL{self.next_id:04d}"

    def _overlap(self, a, b):
        if not a or not b: return 0.0
        return len(a & b) / len(a | b)

    def step(self, state, hardening, precomputed_islands=None):
        self.window += 1
        if precomputed_islands is not None:
            raw = precomputed_islands
        else:
            raw = find_islands_sets(state, self.params.s_threshold)
        current = [frozenset(isl) for isl in raw
                    if len(isl) >= self.params.min_cluster_size]
        matched_old = set(); new_islands = {}

        for nodes in current:
            best_id = None; best_ov = 0
            for iid, info in self.islands.items():
                if iid in matched_old: continue
                ov = self._overlap(nodes, info.nodes)
                if ov > best_ov: best_ov = ov; best_id = iid
            if best_id is None or best_ov < 0.5:
                for gid, ginfo in self.graveyard.items():
                    ov = self._overlap(nodes, ginfo.nodes)
                    if ov > best_ov: best_ov = ov; best_id = gid

            ratio, _, _, boundary = compute_density_ratio(
                state, nodes, self.params.s_threshold)
            interior = nodes - boundary

            if best_id and best_ov >= 0.5 and best_id in self.islands:
                old = self.islands[best_id]; matched_old.add(best_id)
                ns = IslandState(island_id=best_id, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    born_window=old.born_window,
                    encapsulated_window=old.encapsulated_window,
                    last_seen_window=self.window,
                    seen_count=old.seen_count + 1,
                    density_ratio=ratio, status=old.status)

                if old.status == "candidate":
                    if (ratio >= self.params.ratio_threshold and
                            ns.seen_count >= self.params.min_persistence):
                        ns.status = "encapsulated"
                        ns.encapsulated_window = self.window
                        self.encapsulation_events += 1
                        self._harden_boundary(state, boundary, hardening)
                elif old.status == "encapsulated":
                    if ratio < self.params.dissolution_threshold:
                        ns.status = "dissolved"
                        self.dissolution_events += 1
                    else:
                        self._harden_boundary(state, boundary, hardening)

                if ns.status == "encapsulated" and interior:
                    ns.inner_entropy = compute_inner_entropy(state, interior)
                    ns.inner_motif_counts = find_inner_motifs(
                        state, interior, self.params.s_threshold,
                        self.motif_params.motif_sizes)
                    self.motif_history.setdefault(best_id, []).append(
                        ns.inner_motif_counts.copy())

                new_islands[best_id] = ns

            elif best_id and best_ov >= 0.5 and best_id in self.graveyard:
                old = self.graveyard.pop(best_id)
                ns = IslandState(island_id=best_id, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    born_window=old.born_window, last_seen_window=self.window,
                    seen_count=old.seen_count + 1,
                    density_ratio=ratio, status="candidate")
                new_islands[best_id] = ns
            else:
                iid = self._new_id()
                ns = IslandState(island_id=iid, nodes=nodes,
                    boundary_nodes=boundary, interior_nodes=interior,
                    born_window=self.window, last_seen_window=self.window,
                    density_ratio=ratio, status="candidate")
                new_islands[iid] = ns

        for iid in self.islands:
            if iid not in matched_old:
                self.graveyard[iid] = self.islands[iid]
        self.graveyard = {k: v for k, v in self.graveyard.items()
                          if self.window - v.last_seen_window <= 5}
        self.islands = new_islands
        self._decay_hardening(hardening)
        return self._summary()

    def _harden_boundary(self, state, boundary, hardening):
        b = self.params.boundary_hardening_bonus
        for n in boundary:
            if n not in state.alive_n: continue
            for nb in state.neighbors(n):
                lk = state.key(n, nb)
                if lk in state.alive_l:
                    if hardening.get(lk, 0) < b:
                        hardening[lk] = b

    def _decay_hardening(self, hardening):
        r = self.params.boundary_hardening_decay
        dead = [k for k, v in hardening.items() if v - r <= 0]
        for k in dead: del hardening[k]
        for k in hardening: hardening[k] -= r

    def get_motif_recurrence(self):
        result = {}
        w = self.motif_params.recurrence_window
        mr = self.motif_params.min_recurrence
        for iid, hist in self.motif_history.items():
            if len(hist) < w: continue
            tri = [h.get(3, 0) for h in hist[-w:]]
            nz = sum(1 for t in tri if t > 0)
            if nz >= mr: result[iid] = nz
        return result

    def _summary(self):
        n_tot = len(self.islands)
        n_enc = sum(1 for i in self.islands.values() if i.status == "encapsulated")
        n_cand = sum(1 for i in self.islands.values() if i.status == "candidate")
        sizes = [len(i.nodes) for i in self.islands.values()]
        ratios = [i.density_ratio for i in self.islands.values()]
        enc = [i for i in self.islands.values() if i.status == "encapsulated"]
        ie = [i.inner_entropy for i in enc if i.inner_entropy > 0]
        it = [i.inner_motif_counts.get(3, 0) for i in enc]
        rec = self.get_motif_recurrence()
        return {
            "n_clusters": n_tot, "n_encapsulated": n_enc, "n_candidates": n_cand,
            "mean_size": round(float(np.mean(sizes)), 1) if sizes else 0,
            "max_size": max(sizes) if sizes else 0,
            "mean_density_ratio": round(float(np.mean(ratios)), 2) if ratios else 0,
            "max_density_ratio": round(float(max(ratios)), 2) if ratios else 0,
            "encap_events": self.encapsulation_events,
            "dissolve_events": self.dissolution_events,
            "mean_inner_entropy": round(float(np.mean(ie)), 4) if ie else 0,
            "max_inner_entropy": round(float(max(ie)), 4) if ie else 0,
            "total_inner_tri": sum(it),
            "motif_recurrence": len(rec),
            "motif_recurrence_ids": list(rec.keys()),
        }

# ================================================================
# SEMANTIC PRESSURE (non-destructive)
# ================================================================
def apply_semantic_pressure(state, substrate, params, tracker, rng):
    stats = {"pressure_events": 0, "latent_boosts": 0, "nodes_shielded": 0}
    shielded = set()
    for isl in tracker.islands.values():
        if isl.status == "encapsulated":
            shielded |= isl.interior_nodes
    for n in list(state.alive_n):
        if n in shielded:
            stats["nodes_shielded"] += 1; continue
        if rng.random() > params.pressure_prob: continue
        d = rng.uniform(-1, 1)
        state.theta[n] = (state.theta[n] + params.pressure_strength * d) % (2*np.pi)
        stats["pressure_events"] += 1
        for nb in substrate.get(n, []):
            if nb in state.alive_n and nb not in shielded:
                lk = state.key(n, nb)
                if lk not in state.alive_l:
                    cur = state.get_latent(n, nb)
                    state.set_latent(n, nb, min(1.0, cur + params.latent_boost))
                    stats["latent_boosts"] += 1
    return stats

# ================================================================
# STATE FRAME
# ================================================================
@dataclass
class V43StateFrame:
    seed: int = 0; window: int = 0
    k_star: int = 0; k_changed: bool = False; k_margin: float = 0.0
    entropy: float = 0.0; entropy_delta: float = 0.0
    alive_nodes: int = 0; alive_links: int = 0
    n_clusters: int = 0; n_encapsulated: int = 0; n_candidates: int = 0
    mean_cluster_size: float = 0.0; max_cluster_size: int = 0
    mean_density_ratio: float = 0.0; max_density_ratio: float = 0.0
    encap_events_total: int = 0; dissolve_events_total: int = 0
    mean_inner_entropy: float = 0.0; max_inner_entropy: float = 0.0
    total_inner_triangles: int = 0; motif_recurrence_count: int = 0
    pressure_events: int = 0; latent_boosts: int = 0; nodes_shielded: int = 0
    hardened_links_count: int = 0; mean_hardening: float = 0.0
    milestone: int = 0
    anomalies: list = field(default_factory=list)
    state_hash: str = ""
    physics_seconds: float = 0.0

    def compute_hash(self):
        raw = f"{self.seed}_{self.window}_{self.alive_links}_{self.entropy:.6f}"
        self.state_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

# ================================================================
# MILESTONES
# ================================================================
def evaluate_milestones(frame, history):
    if len(history) < 3: return 0
    m = 0; recent = history[-5:] if len(history) >= 5 else history
    links = [f.alive_links for f in recent[-3:]]
    if all(l > 0 for l in links):
        if (links[0] - links[-1]) / max(links[0], 1) < 0.10: m = 1
    if m >= 1:
        cs = [f.n_clusters for f in recent]
        consec = 0
        for c in cs:
            consec = consec + 1 if c > 0 else 0
        if consec >= 2: m = 2
    if m >= 2 and frame.n_encapsulated > 0: m = 3
    if m >= 3 and frame.motif_recurrence_count > 0: m = 4
    if m >= 4 and frame.n_encapsulated >= 2: m = 5
    return m

# ================================================================
# v4.3 ENGINE
# ================================================================
class V43Engine:
    def __init__(self, seed=42, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                 pressure_params=None, encap_params=None, motif_params=None):
        self.seed = seed; self.N = N
        self.pressure_params = pressure_params or SemanticPressureParams()
        self.encap_params = encap_params or EncapsulationParams()
        self.motif_params = motif_params or MotifParams()
        self.window_count = 0
        self.frames: list[V43StateFrame] = []
        self.hardening: dict = {}
        self.island_tracker = IslandTracker(self.encap_params, self.motif_params)

        p = dict(BASE_PARAMS); p["p_link_birth"] = plb
        self.state = GenesisState(N, C_MAX, seed)
        init_fert(self.state, TOPO_VAR, seed)
        self.rmap = assign_regions(N)
        self.physics = GenesisPhysics(PhysicsParams(
            exclusion_enabled=True, resonance_enabled=True,
            phase_enabled=True, beta=BETA, decay_rate_node=NODE_DECAY,
            K_sync=0.1, alpha=0.0, gamma=1.0))
        self.chem = ChemistryEngine(ChemistryParams(
            enabled=True, E_thr=p["reaction_energy_threshold"],
            exothermic_release=p["exothermic_release_amount"],
            E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO))
        self.realizer = RealizationOperator(RealizationParams(
            enabled=True, p_link_birth=plb,
            latent_to_active_threshold=p["latent_to_active_threshold"],
            latent_refresh_rate=p["latent_refresh_rate"]))
        self.grower = AutoGrowthEngine(AutoGrowthParams(
            enabled=True, auto_growth_rate=p["auto_growth_rate"]))
        self.intruder = BoundaryIntrusionOperator(intrusion_rate=rate)
        self.state.EXTINCTION = p["link_death_threshold"]
        self.png = None; self.ckg = None
        self.substrate = build_substrate(N)

    def run_injection(self):
        t0 = time.time()
        print(f"  ⟐ Injection ({INJECTION_STEPS} steps)...", flush=True)
        for step in range(INJECTION_STEPS):
            if step % INJECT_INTERVAL == 0:
                tgts = self.physics.inject(self.state)
                self.chem.seed_on_injection(self.state, tgts or [])
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.grower.step(self.state)
            self.physics.step_decay_exclusion(self.state)
            if (step+1) % 500 == 0:
                print(f"    step {step+1}/{INJECTION_STEPS} ({time.time()-t0:.0f}s)", flush=True)
        print(f"  ⟐ Injection done ({time.time()-t0:.0f}s).", flush=True)

    def step_window(self, steps=WINDOW):
        t0 = time.time()
        for step in range(steps):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.grower.step(self.state)
            self.intruder.step(self.state)
            self.physics.step_decay_exclusion(self.state)

        ps = apply_semantic_pressure(self.state, self.substrate,
            self.pressure_params, self.island_tracker, self.state.rng)
        self.window_count += 1

        # Compute islands ONCE — shared by tracker + observer
        isl_s = find_islands_sets(self.state, 0.30)
        isl_m = find_islands_sets(self.state, 0.20)
        isl_w = find_islands_sets(self.state, 0.10)

        isum = self.island_tracker.step(self.state, self.hardening,
                                         precomputed_islands=isl_m)

        # Observer (uses pre-computed islands)
        nm_s = {n for isl in isl_s for n in isl}
        nm_m = {n for isl in isl_m for n in isl}
        nm_w = {n for isl in isl_w for n in isl}
        bm = set()
        for isl in isl_m:
            for n in isl:
                if n not in self.state.alive_n: continue
                for nb in self.state.neighbors(n):
                    if nb in self.state.alive_n and nb not in isl:
                        bm.add(n); break
        ng = []
        for i in self.state.alive_n:
            if int(self.state.Z[i]) != 3: continue
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
            if int(self.state.Z[i]) == 3: rc[self.rmap.get(i, 0)] += 1
        tc = sum(rc.values())
        ent = -sum((v/tc)*math.log2(v/tc) for v in rc.values() if v > 0) if tc > 0 else 0.0
        ed = ent - (self.frames[-1].entropy if self.frames else 0.0)

        hc = len(self.hardening)
        hv = list(self.hardening.values())
        mh = float(np.mean(hv)) if hv else 0.0

        anom = []
        if isum["n_encapsulated"] > 0:
            anom.append(f"[ENCAP] {isum['n_encapsulated']}")
        if isum["motif_recurrence"] > 0:
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
            motif_recurrence_count=isum["motif_recurrence"],
            pressure_events=ps["pressure_events"],
            latent_boosts=ps["latent_boosts"],
            nodes_shielded=ps["nodes_shielded"],
            hardened_links_count=hc, mean_hardening=round(mh, 4),
            anomalies=anom, physics_seconds=round(time.time()-t0, 1),
        )
        f.milestone = evaluate_milestones(f, self.frames)
        f.compute_hash(); self.frames.append(f)
        return f
