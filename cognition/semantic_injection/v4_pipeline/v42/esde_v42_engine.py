#!/usr/bin/env python3
"""
ESDE v4.2 — Adaptive Dynamics Engine
======================================
Phase : v4.2 Topological Plasticity + Structural Hardening
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

Extends v4.1 wave propagation engine with three new mechanisms:

  1. TOPOLOGICAL PLASTICITY
     - Nodes whose links are severed by a wave gain temporary P_val > 0
     - Plastic nodes have increased probability of forming new local links
     - Plasticity decays exponentially per step

  2. STRUCTURAL HARDENING
     - Links formed between two plastic nodes receive a hardening bonus
     - Hardened links require higher effective amplitude to sever
     - Hardening decays over time (no permanent reinforcement)

  3. LINEAGE TRACKING (extended)
     - cluster_lineage_id (inherited from v4.1 ClusterTracker)
     - structural_resistance_mean: avg amplitude to sever cluster links
     - reformation_cycles: already tracked, now exposed in StateFrame

Design cycle: Wave → Damage → Plasticity → Rewiring → Hardening → Next Wave

GPT Audit constraints:
  - plasticity_factor ∈ [1.1, 1.5]
  - hardening must include temporal decay
  - rewiring must be local (substrate neighbors + 2nd-order)
  - no global topology randomization

Principle: "Structure first, meaning later."
"""

import numpy as np
import sys, math, time, json
from pathlib import Path
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Optional

# ================================================================
# PATH SETUP (same as v4.1)
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent        # v42/
_V41_DIR = _SCRIPT_DIR.parent / "v41"                # v4_pipeline/v41/
_PIPELINE_DIR = _SCRIPT_DIR.parent                   # v4_pipeline/
_COGNITION_DIR = _PIPELINE_DIR.parent                # semantic_injection/
_REPO_ROOT = _COGNITION_DIR.parent.parent            # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V41_DIR), str(_ENGINE_DIR), str(_COGNITION_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel  # MUST be before any engine imports
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "engine_accel not loaded — performance will be degraded"

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

# Import v4.1 components we reuse
from esde_v41_engine import (
    WaveParams as V41WaveParams,
    WaveEvent, WaveResult,
    build_substrate, select_substrate_origin,
    ClusterInfo, ClusterDelta, ClusterTracker,
    compile_v41_context, validate_v41,
    assign_regions, N_REGIONS, MIN_C_NODES_FOR_VALID,
    COG_N, COG_PLB, COG_RATE,
)


# ================================================================
# v4.2 PARAMETERS
# ================================================================
@dataclass
class PlasticityParams:
    """Configuration for topological plasticity mechanics."""
    # Plasticity assignment
    initial_plasticity: float = 0.8     # P_val assigned to severed-link nodes
    decay_rate: float = 0.1             # P_val *= (1 - decay_rate) per step
    min_threshold: float = 0.05         # below this, P_val → 0

    # Rewiring
    plasticity_factor: float = 1.3      # multiplier on link birth prob (GPT: 1.1–1.5)
    rewire_radius: int = 2              # max substrate hops for candidate partners
    max_rewire_per_step: int = 3        # cap rewiring events per node per step

    # Structural hardening
    hardening_bonus: float = 0.15       # added to link's effective S_threshold
    hardening_decay: float = 0.005      # hardening -= this per step
    hardening_cap: float = 0.5          # max hardening value


@dataclass
class V42WaveParams(V41WaveParams):
    """v4.2 wave params — adds hardening-aware destruction."""
    pass  # destruction logic override is in propagate_wave_v42


# ================================================================
# v4.2 WAVE PROPAGATION (hardening-aware)
# ================================================================
def propagate_wave_v42(state: GenesisState, event: WaveEvent,
                       params: V41WaveParams, rng,
                       substrate: dict = None,
                       hardening: dict = None,
                       plasticity: np.ndarray = None,
                       plasticity_params: PlasticityParams = None,
                       ) -> WaveResult:
    """
    BFS wave propagation with hardening-aware destruction.

    Same as v4.1 propagate_wave, but:
    - Links with hardening bonus require higher A_eff to sever
    - Severed-link nodes receive plasticity (P_val > 0)

    Returns standard WaveResult (v4.1 compatible).
    """
    if hardening is None:
        hardening = {}
    if plasticity_params is None:
        plasticity_params = PlasticityParams()

    arrival = {}
    amplitudes_map = {}

    # BFS initialization
    queue = deque()
    for n in event.origin_nodes:
        if n in state.alive_n:
            arrival[n] = 0
            amplitudes_map[n] = event.amplitude
            queue.append(n)

    # BFS propagation via SUBSTRATE (not active links)
    while queue:
        node = queue.popleft()
        h = arrival[node]
        if h >= params.max_hops:
            continue
        neighbors = substrate[node] if substrate else state.neighbors(node)
        for nb in neighbors:
            if nb in state.alive_n and nb not in arrival:
                nh = h + 1
                a_eff = event.amplitude * math.exp(-params.decay_lambda * nh)
                if a_eff < params.activation_threshold * 0.1:
                    continue
                arrival[nb] = nh
                amplitudes_map[nb] = a_eff
                queue.append(nb)

    # Apply effects
    links_severed = 0
    links_activated = 0
    theta_shifts = 0
    severed_nodes = set()  # v4.2: track which nodes lost links

    for node, a_eff in amplitudes_map.items():
        # --- Phase shift (always) ---
        direction = rng.uniform(-1, 1)
        delta_theta = a_eff * params.theta_shift_scale * direction
        state.theta[node] = (state.theta[node] + delta_theta) % (2 * np.pi)
        theta_shifts += 1

        # --- Destruction regime (hardening-aware) ---
        if a_eff > params.destruction_threshold:
            for nb in list(state.neighbors(node)):
                lk = state.key(node, nb)
                if lk in state.alive_l:
                    # v4.2: effective threshold includes hardening
                    h_bonus = hardening.get(lk, 0.0)
                    effective_threshold = state.EXTINCTION + h_bonus
                    stress = a_eff * params.stress_factor
                    state.S[lk] = max(0, state.S[lk] - stress)
                    if state.S[lk] < effective_threshold:
                        state.alive_l.discard(lk)
                        links_severed += 1
                        severed_nodes.add(node)
                        severed_nodes.add(nb)
                        # Remove hardening for dead link
                        hardening.pop(lk, None)

        # --- Activation regime ---
        elif a_eff > params.activation_threshold:
            for nb in state.neighbors(node):
                if nb in state.alive_n:
                    lk = state.key(node, nb)
                    if lk not in state.alive_l:
                        current = state.get_latent(node, nb)
                        state.set_latent(node, nb,
                                         min(1.0, current + params.activation_boost))
                        links_activated += 1

    # v4.2: Assign plasticity to severed-link nodes
    if plasticity is not None and severed_nodes:
        for n in severed_nodes:
            plasticity[n] = max(plasticity[n],
                                plasticity_params.initial_plasticity)

    max_hop = max(arrival.values()) if arrival else 0

    return WaveResult(
        event_id=event.event_id,
        origin_nodes=event.origin_nodes,
        amplitude=event.amplitude,
        nodes_reached=len(arrival),
        max_hop=max_hop,
        links_severed=links_severed,
        links_activated=links_activated,
        theta_shifts_applied=theta_shifts,
        arrival_times=arrival,
        effective_amplitudes=amplitudes_map,
    )


# ================================================================
# PLASTICITY MECHANICS
# ================================================================
def plasticity_rewire(state: GenesisState, plasticity: np.ndarray,
                      substrate: dict, params: PlasticityParams,
                      hardening: dict, rng) -> dict:
    """
    Plastic nodes attempt local rewiring.

    For each node with P_val > min_threshold:
      - Gather candidate partners within rewire_radius substrate hops
      - Filter to alive nodes (prefer other plastic nodes)
      - Probabilistic link formation: p = base_p * plasticity_factor * P_val
      - Links formed between two plastic nodes get hardening bonus

    Returns dict of stats: {rewire_attempts, rewire_successes,
                            hardened_links_formed}
    """
    stats = {"rewire_attempts": 0, "rewire_successes": 0,
             "hardened_links_formed": 0}

    plastic_nodes = [n for n in range(len(plasticity))
                     if plasticity[n] > params.min_threshold
                     and n in state.alive_n]

    if not plastic_nodes:
        return stats

    base_p = state._latent_rng.random() * 0.01 + 0.005  # baseline ~0.5-1.5%

    for node in plastic_nodes:
        rewire_count = 0

        # Gather candidates within rewire_radius substrate hops (BFS)
        candidates = set()
        visited = {node}
        frontier = [node]
        for hop in range(params.rewire_radius):
            next_frontier = []
            for fn in frontier:
                for nb in substrate.get(fn, []):
                    if nb not in visited:
                        visited.add(nb)
                        if nb in state.alive_n and nb != node:
                            candidates.add(nb)
                        next_frontier.append(nb)
            frontier = next_frontier

        if not candidates:
            continue

        # Sort candidates: prefer plastic nodes (higher priority)
        candidate_list = list(candidates)
        rng.shuffle(candidate_list)
        # Move plastic candidates to front
        candidate_list.sort(key=lambda c: -plasticity[c])

        for cand in candidate_list:
            if rewire_count >= params.max_rewire_per_step:
                break

            lk = state.key(node, cand)
            if lk in state.alive_l:
                continue  # already linked

            stats["rewire_attempts"] += 1

            # Rewiring probability
            p = base_p * params.plasticity_factor * plasticity[node]
            if plasticity[cand] > params.min_threshold:
                p *= 1.5  # bonus for plastic-plastic pairs

            if rng.random() < p:
                # Check exclusion constraint
                si = state.link_strength_sum(node)
                sj = state.link_strength_sum(cand)
                new_s = 0.05  # weak initial link
                if si + new_s > state.c_max or sj + new_s > state.c_max:
                    continue

                # Form link
                state.add_link(node, cand, new_s)
                stats["rewire_successes"] += 1
                rewire_count += 1

                # Hardening: if both nodes are plastic
                if (plasticity[node] > params.min_threshold and
                        plasticity[cand] > params.min_threshold):
                    h_val = min(params.hardening_bonus *
                                (plasticity[node] + plasticity[cand]) / 2,
                                params.hardening_cap)
                    hardening[lk] = h_val
                    stats["hardened_links_formed"] += 1

    return stats


def decay_plasticity(plasticity: np.ndarray, params: PlasticityParams):
    """Exponential decay of plasticity values."""
    mask = plasticity > params.min_threshold
    plasticity[mask] *= (1.0 - params.decay_rate)
    plasticity[plasticity < params.min_threshold] = 0.0


def decay_hardening(hardening: dict, params: PlasticityParams):
    """Gradual decay of structural hardening bonuses."""
    dead_keys = []
    for lk, h_val in hardening.items():
        hardening[lk] = h_val - params.hardening_decay
        if hardening[lk] <= 0:
            dead_keys.append(lk)
    for k in dead_keys:
        del hardening[k]


# ================================================================
# EXTENDED CLUSTER TRACKER (v4.2)
# ================================================================
class V42ClusterTracker(ClusterTracker):
    """
    Extends v4.1 ClusterTracker with structural resistance measurement.
    """

    def __init__(self, overlap_threshold=0.5):
        super().__init__(overlap_threshold)
        # Track per-cluster resistance history
        self.resistance_history: dict[str, list[float]] = {}

    def compute_structural_resistance(self, state: GenesisState,
                                      hardening: dict) -> dict:
        """
        For each active cluster, compute mean effective threshold
        of its internal links. Higher = more resistant to wave damage.

        Returns {cluster_id: resistance_mean}
        """
        result = {}
        for cid, info in self.active.items():
            nodes = info.nodes
            internal_thresholds = []
            for n in nodes:
                if n not in state.alive_n:
                    continue
                for nb in state.neighbors(n):
                    if nb in nodes:
                        lk = state.key(n, nb)
                        if lk in state.alive_l:
                            base = state.EXTINCTION
                            h_bonus = hardening.get(lk, 0.0)
                            internal_thresholds.append(base + h_bonus)

            if internal_thresholds:
                resistance = float(np.mean(internal_thresholds))
            else:
                resistance = state.EXTINCTION  # no internal links

            result[cid] = resistance

            # Track history
            if cid not in self.resistance_history:
                self.resistance_history[cid] = []
            self.resistance_history[cid].append(resistance)

        # Prune dead cluster history
        active_ids = set(self.active.keys())
        dead_ids = [k for k in self.resistance_history if k not in active_ids]
        for k in dead_ids:
            # Keep for graveyard period
            if k not in self.graveyard:
                del self.resistance_history[k]

        return result

    def get_summary_v42(self, resistance_map: dict = None) -> dict:
        """Extended summary with structural resistance."""
        base = self.get_summary()

        if resistance_map and self.active:
            resistances = [resistance_map.get(cid, 0)
                           for cid in self.active]
            base["resistance_mean"] = round(float(np.mean(resistances)), 6)
            base["resistance_max"] = round(float(max(resistances)), 6)

            # Rising resistance: clusters whose resistance increased
            rising = 0
            for cid in self.active:
                hist = self.resistance_history.get(cid, [])
                if len(hist) >= 2 and hist[-1] > hist[-2]:
                    rising += 1
            base["resistance_rising_count"] = rising
        else:
            base["resistance_mean"] = 0.0
            base["resistance_max"] = 0.0
            base["resistance_rising_count"] = 0

        return base


# ================================================================
# v4.2 STATE FRAME
# ================================================================
@dataclass
class V42StateFrame:
    """One observation window's state (v4.2 adaptive dynamics)."""
    # Identity
    seed: int = 0
    window: int = 0

    # Wave
    wave_amplitude: float = 0.0
    wave_origin: list = field(default_factory=list)
    wave_nodes_reached: int = 0
    wave_max_hop: int = 0
    wave_links_severed: int = 0
    wave_links_activated: int = 0

    # Observer
    k_star: int = 0
    k_changed: bool = False
    k_margin: float = 0.0
    divergence: bool = False
    regional_k: list = field(default_factory=list)

    # Thermodynamics
    entropy: float = 0.0
    entropy_delta: float = 0.0
    alive_nodes: int = 0
    alive_links: int = 0

    # Clusters (v4.1 base)
    n_clusters: int = 0
    cluster_mean_size: float = 0.0
    cluster_max_lifetime: int = 0
    cluster_births: int = 0
    cluster_deaths: int = 0
    cluster_reformations: int = 0
    cluster_migrations: int = 0
    homeostatic_count: int = 0
    proto_memory_count: int = 0

    # v4.2: Plasticity
    plastic_nodes_count: int = 0
    mean_plasticity: float = 0.0
    max_plasticity: float = 0.0
    rewire_attempts: int = 0
    rewire_successes: int = 0

    # v4.2: Hardening
    hardened_links_count: int = 0
    hardened_links_formed_this_window: int = 0
    mean_hardening: float = 0.0
    max_hardening: float = 0.0

    # v4.2: Structural resistance
    resistance_mean: float = 0.0
    resistance_max: float = 0.0
    resistance_rising_count: int = 0

    # Anomalies
    anomalies: list = field(default_factory=list)

    # Hash
    state_hash: str = ""

    def compute_hash(self):
        import hashlib
        raw = f"{self.seed}_{self.window}_{self.alive_links}_{self.entropy:.6f}"
        self.state_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]


# ================================================================
# v4.2 ENGINE
# ================================================================
class V42Engine:
    """
    ESDE v4.2 engine: V41Engine + Plasticity + Hardening + Resistance.

    Execution order per window:
      1. Physics steps (realizer → phase → chemistry → resonance →
         growth → intrusion → decay/exclusion)
      2. Wave propagation (BFS on substrate, hardening-aware destruction)
      3. Plasticity assignment (severed-link nodes)
      4. Plasticity rewiring (local new links, hardening for plastic pairs)
      5. Plasticity decay
      6. Hardening decay
      7. Cluster observation + resistance measurement
      8. Observer computation
    """

    def __init__(self, seed=42, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                 wave_params: V41WaveParams = None,
                 plasticity_params: PlasticityParams = None):
        self.seed = seed
        self.N = N
        self.wave_params = wave_params or V41WaveParams()
        self.plasticity_params = plasticity_params or PlasticityParams()
        self.window_count = 0
        self.wave_event_count = 0
        self.frames: list[V42StateFrame] = []

        # v4.2 state arrays
        self.plasticity = np.zeros(N, dtype=float)
        self.hardening: dict = {}  # link_key -> hardening_value

        # Tracker (v4.2 extended)
        self.tracker = V42ClusterTracker()

        # --- Genesis setup (identical to v4.1) ---
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

        # Observer state
        self.png = None
        self.ckg = None
        self.pnr = {r: None for r in range(N_REGIONS)}
        self.ckr = {r: None for r in range(N_REGIONS)}

        # Substrate
        self.substrate = build_substrate(N)

    def run_injection(self):
        """Injection phase (identical to v4.1)."""
        t0 = time.time()
        print(f"  ⟐ Injection phase ({INJECTION_STEPS} steps)...", flush=True)
        for step in range(INJECTION_STEPS):
            if step % INJECT_INTERVAL == 0:
                tgts = self.physics.inject(self.state)
                self.chem.seed_on_injection(self.state, tgts or [])
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.grower.step(self.state)
            self.physics.step_decay_exclusion(self.state)
            if (step + 1) % 500 == 0:
                print(f"    step {step+1}/{INJECTION_STEPS} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        print(f"  ⟐ Injection complete ({time.time()-t0:.0f}s).", flush=True)

    def select_wave_origin(self, n_origins=1) -> list:
        return select_substrate_origin(self.substrate, self.state,
                                       self.state.rng, n_origins)

    def step_window(self, amplitude: float,
                    origin_nodes: list = None,
                    steps: int = WINDOW) -> V42StateFrame:
        """
        Run one window: physics + wave + plasticity + hardening + observation.
        """
        t0 = time.time()

        # ---- 1. Physics steps ----
        for step in range(steps):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.grower.step(self.state)
            self.intruder.step(self.state)
            self.physics.step_decay_exclusion(self.state)

            # v4.2: Per-step plasticity + hardening decay
            decay_plasticity(self.plasticity, self.plasticity_params)
            decay_hardening(self.hardening, self.plasticity_params)

        # ---- 2. Wave event ----
        if origin_nodes is None:
            origin_nodes = self.select_wave_origin()

        self.wave_event_count += 1
        event = WaveEvent(
            origin_nodes=origin_nodes,
            amplitude=amplitude,
            event_id=self.wave_event_count,
        )
        wave_result = propagate_wave_v42(
            self.state, event, self.wave_params, self.state.rng,
            substrate=self.substrate,
            hardening=self.hardening,
            plasticity=self.plasticity,
            plasticity_params=self.plasticity_params,
        )

        # ---- 3. Plasticity rewiring (recovery phase) ----
        rewire_stats = plasticity_rewire(
            self.state, self.plasticity, self.substrate,
            self.plasticity_params, self.hardening, self.state.rng,
        )

        # ---- 4. Cluster observation ----
        self.window_count += 1

        # Pre-compute islands ONCE — shared between tracker + observer
        isl_s = find_islands_sets(self.state, 0.30)
        isl_m = find_islands_sets(self.state, 0.20)
        isl_w = find_islands_sets(self.state, 0.10)

        # Tracker uses isl_m (avoids redundant find_islands_sets call)
        current_clusters = [frozenset(isl) for isl in isl_m if len(isl) >= 3]
        cluster_delta = self.tracker.update(current_clusters,
                                            wave_result.arrival_times)

        # v4.2: Structural resistance
        resistance_map = self.tracker.compute_structural_resistance(
            self.state, self.hardening)
        cluster_summary = self.tracker.get_summary_v42(resistance_map)

        # ---- 5. Observer ----
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

        # Compute observer (global + regional)
        nodes_g = []
        for i in self.state.alive_n:
            if int(self.state.Z[i]) != 3:
                continue
            s = 1 if i in nm_s else 0
            m = 1 if i in nm_m else 0
            w = 1 if i in nm_w else 0
            nodes_g.append({
                "r_bits": f"{s}{m}{w}",
                "boundary_mid": 1 if i in bm else 0,
                "intrusion_bin": 0,
            })

        if nodes_g and len(nodes_g) >= MIN_C_NODES_FOR_VALID:
            js_g = {k: compute_J(nodes_g, self.png, k)[0] for k in K_LEVELS}
            gk, self.png, self.ckg = select_k_star(js_g, self.ckg)
        else:
            gk = 0; js_g = {}

        # Regional observer
        regional_k = []
        for r in range(N_REGIONS):
            rnodes = [nd for i, nd in enumerate(nodes_g)
                      if i < len(nodes_g)]
            # Simplified: use global k for now (consistent with v4.1)
            regional_k.append(gk)

        k_changed = (self.ckg is not None and gk != (self.frames[-1].k_star
                      if self.frames else 0))
        k_margin = max(js_g.values()) - sorted(js_g.values())[-2] \
            if len(js_g) >= 2 else 0.0
        div = any(rk != gk for rk in regional_k) if regional_k else False

        # Entropy
        region_counts = Counter()
        for i in self.state.alive_n:
            if int(self.state.Z[i]) == 3:
                region_counts[self.rmap.get(i, 0)] += 1
        total_c = sum(region_counts.values())
        if total_c > 0:
            ent = -sum((v/total_c) * math.log2(v/total_c)
                       for v in region_counts.values() if v > 0)
        else:
            ent = 0.0
        prev_ent = self.frames[-1].entropy if self.frames else 0.0
        ent_delta = ent - prev_ent

        # ---- 6. Plasticity/hardening metrics ----
        p_mask = self.plasticity > self.plasticity_params.min_threshold
        plastic_count = int(p_mask.sum())
        mean_p = float(self.plasticity[p_mask].mean()) if plastic_count > 0 else 0.0
        max_p = float(self.plasticity.max())

        h_count = len(self.hardening)
        h_vals = list(self.hardening.values())
        mean_h = float(np.mean(h_vals)) if h_vals else 0.0
        max_h = float(max(h_vals)) if h_vals else 0.0

        # ---- 7. Anomaly detection ----
        anomalies = []
        if wave_result.links_severed > 20:
            anomalies.append(f"[WAVE_DESTRUCTION] {wave_result.links_severed} links")
        if len(cluster_delta.births) > 3:
            anomalies.append(f"[CLUSTER_BURST] +{len(cluster_delta.births)}")
        if len(cluster_delta.deaths) > 3:
            anomalies.append(f"[CLUSTER_COLLAPSE] -{len(cluster_delta.deaths)}")
        if cluster_delta.reformations:
            anomalies.append(f"[REFORMATION] {len(cluster_delta.reformations)}")
        if abs(ent_delta) > 0.03:
            anomalies.append(f"[ENTROPY_SPIKE] {ent_delta:+.4f}")
        if rewire_stats["rewire_successes"] > 5:
            anomalies.append(f"[PLASTIC_REWIRE] {rewire_stats['rewire_successes']}")
        if rewire_stats["hardened_links_formed"] > 0:
            anomalies.append(f"[HARDENING] +{rewire_stats['hardened_links_formed']}")

        # ---- 8. Frame ----
        frame = V42StateFrame(
            seed=self.seed, window=self.window_count,
            wave_amplitude=amplitude,
            wave_origin=origin_nodes,
            wave_nodes_reached=wave_result.nodes_reached,
            wave_max_hop=wave_result.max_hop,
            wave_links_severed=wave_result.links_severed,
            wave_links_activated=wave_result.links_activated,
            k_star=gk, k_changed=k_changed, k_margin=k_margin,
            divergence=div, regional_k=regional_k,
            entropy=ent, entropy_delta=ent_delta,
            alive_nodes=len(self.state.alive_n),
            alive_links=len(self.state.alive_l),
            n_clusters=cluster_summary["n_clusters"],
            cluster_mean_size=cluster_summary.get("mean_size", 0),
            cluster_max_lifetime=cluster_summary.get("max_lifetime", 0),
            cluster_births=len(cluster_delta.births),
            cluster_deaths=len(cluster_delta.deaths),
            cluster_reformations=len(cluster_delta.reformations),
            cluster_migrations=len(cluster_delta.migrations),
            homeostatic_count=cluster_summary.get("homeostatic", 0),
            proto_memory_count=cluster_summary.get("proto_memory", 0),
            # v4.2
            plastic_nodes_count=plastic_count,
            mean_plasticity=round(mean_p, 4),
            max_plasticity=round(max_p, 4),
            rewire_attempts=rewire_stats["rewire_attempts"],
            rewire_successes=rewire_stats["rewire_successes"],
            hardened_links_count=h_count,
            hardened_links_formed_this_window=rewire_stats["hardened_links_formed"],
            mean_hardening=round(mean_h, 4),
            max_hardening=round(max_h, 4),
            resistance_mean=cluster_summary.get("resistance_mean", 0.0),
            resistance_max=cluster_summary.get("resistance_max", 0.0),
            resistance_rising_count=cluster_summary.get(
                "resistance_rising_count", 0),
            anomalies=anomalies,
        )
        frame.compute_hash()
        self.frames.append(frame)
        return frame
