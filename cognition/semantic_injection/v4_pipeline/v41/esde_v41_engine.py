#!/usr/bin/env python3
"""
ESDE v4.1 — Wave Propagation Engine
=====================================
Phase : v4.1 Emergent Spatial Topology
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

HARD FORK from v4.0. No backward compatibility with homogeneous pressure model.

Core changes from v3.x/v4.0:
  - Global diffusion (apply_diffusion) REMOVED
  - Replaced by localized wave propagation (BFS on graph)
  - Dual wave effect: θ shift + S stress (destruction/activation)
  - Arrival-time logging for emergent spatial coordinates
  - Cluster tracking: homeostasis, proto-reflex, proto-memory

Principle: "Structure first, meaning later."
"""

import numpy as np
import sys, math, time, hashlib, json
from pathlib import Path
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Optional

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent       # v41/
_PIPELINE_DIR = _SCRIPT_DIR.parent                   # v4_pipeline/
_COGNITION_DIR = _PIPELINE_DIR.parent                # semantic_injection/
_REPO_ROOT = _COGNITION_DIR.parent.parent            # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_ENGINE_DIR), str(_COGNITION_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
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


# ================================================================
# WAVE PARAMETERS
# ================================================================
@dataclass
class WaveParams:
    """Configuration for wave propagation mechanics."""
    # Attenuation
    decay_lambda: float = 0.5        # exponential decay: A_eff = A0 * exp(-λ*h)
    propagation_speed: float = 1.0   # hops per unit time (constant per event)

    # Dual effect thresholds
    destruction_threshold: float = 0.3   # A_eff above this severs links
    activation_threshold: float = 0.05   # A_eff in [activation, destruction] boosts binding
    activation_boost: float = 0.15       # latent field boost in activation band

    # Phase perturbation
    theta_shift_scale: float = 0.5   # θ shift = A_eff * scale * random_direction

    # Link stress
    stress_factor: float = 0.3      # S reduction = A_eff * factor (destruction regime)

    # Propagation limits
    max_hops: int = 20              # BFS cutoff


# ================================================================
# WAVE EVENT
# ================================================================
@dataclass
class WaveEvent:
    """A single wave disturbance entering the topology."""
    origin_nodes: list          # source node(s)
    amplitude: float            # A0
    event_id: int = 0
    timestamp: float = 0.0     # engine time


@dataclass
class WaveResult:
    """Outcome of a wave propagation."""
    event_id: int
    origin_nodes: list
    amplitude: float
    nodes_reached: int
    max_hop: int
    links_severed: int
    links_activated: int
    theta_shifts_applied: int
    arrival_times: dict = field(default_factory=dict)   # node -> hop distance
    effective_amplitudes: dict = field(default_factory=dict)  # node -> A_eff


def propagate_wave(state: GenesisState, event: WaveEvent,
                   params: WaveParams, rng) -> WaveResult:
    """
    BFS wave propagation from origin nodes across the graph.

    For each reached node at hop h:
      A_eff = A0 * exp(-λ * h)
      if A_eff > destruction_threshold: sever weak links (S stress)
      if activation_threshold < A_eff <= destruction_threshold: boost binding
      always: apply θ perturbation proportional to A_eff
    """
    arrival = {}       # node -> hop count
    amplitudes = {}    # node -> effective amplitude

    # BFS initialization
    queue = deque()
    for n in event.origin_nodes:
        if n in state.alive_n:
            arrival[n] = 0
            amplitudes[n] = event.amplitude
            queue.append(n)

    # BFS propagation
    while queue:
        node = queue.popleft()
        h = arrival[node]
        if h >= params.max_hops:
            continue
        for nb in state.neighbors(node):
            if nb in state.alive_n and nb not in arrival:
                nh = h + 1
                a_eff = event.amplitude * math.exp(-params.decay_lambda * nh)
                if a_eff < params.activation_threshold * 0.1:
                    continue  # negligible, stop propagation
                arrival[nb] = nh
                amplitudes[nb] = a_eff
                queue.append(nb)

    # Apply effects
    links_severed = 0
    links_activated = 0
    theta_shifts = 0

    for node, a_eff in amplitudes.items():
        # --- Phase shift (always) ---
        direction = rng.uniform(-1, 1)
        delta_theta = a_eff * params.theta_shift_scale * direction
        state.theta[node] = (state.theta[node] + delta_theta) % (2 * np.pi)
        theta_shifts += 1

        # --- Destruction regime ---
        if a_eff > params.destruction_threshold:
            for nb in list(state.neighbors(node)):
                lk = state.key(node, nb)
                if lk in state.alive_l:
                    stress = a_eff * params.stress_factor
                    state.S[lk] = max(0, state.S[lk] - stress)
                    if state.S[lk] < state.EXTINCTION:
                        state.alive_l.discard(lk)
                        links_severed += 1

        # --- Activation regime ---
        elif a_eff > params.activation_threshold:
            # Boost latent field around node to encourage new connections
            for nb in state.neighbors(node):
                if nb in state.alive_n:
                    lk = state.key(node, nb)
                    if lk not in state.alive_l:
                        current = state.get_latent(node, nb)
                        state.set_latent(node, nb,
                                         min(1.0, current + params.activation_boost))
                        links_activated += 1

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
        effective_amplitudes=amplitudes,
    )


# ================================================================
# CLUSTER TRACKING
# ================================================================
@dataclass
class ClusterInfo:
    """A single tracked cluster."""
    cluster_id: str
    nodes: frozenset
    size: int
    centroid_hop: float    # mean hop distance from last wave origin
    born_window: int
    last_seen_window: int
    seen_count: int = 1
    reformation_count: int = 0


@dataclass
class ClusterDelta:
    """Changes between two cluster snapshots."""
    deaths: list = field(default_factory=list)       # cluster_ids that vanished
    births: list = field(default_factory=list)        # new cluster_ids
    survived: list = field(default_factory=list)      # persistent cluster_ids
    migrations: list = field(default_factory=list)    # (cluster_id, hop_delta)
    reformations: list = field(default_factory=list)  # cluster_ids that died then reappeared
    connectivity_delta: float = 0.0                   # total link count change


class ClusterTracker:
    """Track cluster lifecycle across wave events."""

    def __init__(self, overlap_threshold=0.5):
        self.overlap_threshold = overlap_threshold
        self.active: dict[str, ClusterInfo] = {}      # cluster_id -> info
        self.graveyard: dict[str, ClusterInfo] = {}   # recently dead clusters
        self.next_id = 0
        self.window = 0

    def _new_id(self):
        self.next_id += 1
        return f"C{self.next_id:04d}"

    def _overlap(self, a: frozenset, b: frozenset) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def snapshot(self, state: GenesisState, s_threshold=0.20) -> list[frozenset]:
        """Extract current clusters as frozen node sets."""
        islands = find_islands_sets(state, s_threshold)
        return [frozenset(isl) for isl in islands if len(isl) >= 3]

    def update(self, current_clusters: list[frozenset],
               wave_arrival: dict = None) -> ClusterDelta:
        """Compare current clusters with tracked state. Return delta."""
        self.window += 1
        delta = ClusterDelta()

        # Pre-wave link count for connectivity delta
        matched_old = set()
        matched_new = set()
        new_active = {}

        # Match current clusters to existing tracked clusters
        for nodes in current_clusters:
            best_match = None
            best_overlap = 0
            for cid, info in self.active.items():
                if cid in matched_old:
                    continue
                ov = self._overlap(nodes, info.nodes)
                if ov > best_overlap:
                    best_overlap = ov
                    best_match = cid

            if best_match and best_overlap >= self.overlap_threshold:
                # Survived
                old_info = self.active[best_match]
                centroid_hop = self._centroid_hop(nodes, wave_arrival)
                hop_delta = centroid_hop - old_info.centroid_hop

                new_info = ClusterInfo(
                    cluster_id=best_match, nodes=nodes, size=len(nodes),
                    centroid_hop=centroid_hop,
                    born_window=old_info.born_window,
                    last_seen_window=self.window,
                    seen_count=old_info.seen_count + 1,
                    reformation_count=old_info.reformation_count,
                )
                new_active[best_match] = new_info
                matched_old.add(best_match)
                delta.survived.append(best_match)

                if abs(hop_delta) > 0.5:
                    delta.migrations.append((best_match, round(hop_delta, 2)))
            else:
                # Check graveyard for reformation
                reformed = False
                for gid, ginfo in self.graveyard.items():
                    if self._overlap(nodes, ginfo.nodes) >= self.overlap_threshold:
                        # Reformation!
                        centroid_hop = self._centroid_hop(nodes, wave_arrival)
                        new_info = ClusterInfo(
                            cluster_id=gid, nodes=nodes, size=len(nodes),
                            centroid_hop=centroid_hop,
                            born_window=ginfo.born_window,
                            last_seen_window=self.window,
                            seen_count=ginfo.seen_count + 1,
                            reformation_count=ginfo.reformation_count + 1,
                        )
                        new_active[gid] = new_info
                        delta.reformations.append(gid)
                        reformed = True
                        break

                if not reformed:
                    # Genuine birth
                    cid = self._new_id()
                    centroid_hop = self._centroid_hop(nodes, wave_arrival)
                    new_info = ClusterInfo(
                        cluster_id=cid, nodes=nodes, size=len(nodes),
                        centroid_hop=centroid_hop,
                        born_window=self.window,
                        last_seen_window=self.window,
                    )
                    new_active[cid] = new_info
                    delta.births.append(cid)

        # Deaths: clusters not matched
        for cid, info in self.active.items():
            if cid not in matched_old:
                delta.deaths.append(cid)
                self.graveyard[cid] = info

        # Prune old graveyard entries (keep last 5 windows)
        self.graveyard = {
            k: v for k, v in self.graveyard.items()
            if self.window - v.last_seen_window <= 5
        }

        self.active = new_active
        return delta

    def _centroid_hop(self, nodes: frozenset, wave_arrival: dict) -> float:
        if not wave_arrival or not nodes:
            return 0.0
        hops = [wave_arrival.get(n, 0) for n in nodes if n in wave_arrival]
        return np.mean(hops) if hops else 0.0

    def get_homeostatic(self, min_reformations=2) -> list[ClusterInfo]:
        """Clusters that repeatedly re-form after disturbances."""
        return [c for c in self.active.values()
                if c.reformation_count >= min_reformations]

    def get_proto_memory(self, min_lifetime=5) -> list[ClusterInfo]:
        """Clusters persisting significantly longer than average."""
        lifetimes = [c.seen_count for c in self.active.values()]
        if not lifetimes:
            return []
        avg = np.mean(lifetimes)
        return [c for c in self.active.values()
                if c.seen_count >= max(min_lifetime, avg * 2)]

    def get_summary(self) -> dict:
        """Summary stats for current cluster state."""
        if not self.active:
            return {"n_clusters": 0, "mean_size": 0, "max_lifetime": 0,
                    "homeostatic": 0, "proto_memory": 0, "total_reformations": 0}
        sizes = [c.size for c in self.active.values()]
        lifetimes = [c.seen_count for c in self.active.values()]
        reforms = sum(c.reformation_count for c in self.active.values())
        return {
            "n_clusters": len(self.active),
            "mean_size": int(round(np.mean(sizes))),
            "max_lifetime": max(lifetimes),
            "homeostatic": len(self.get_homeostatic()),
            "proto_memory": len(self.get_proto_memory()),
            "total_reformations": reforms,
        }


# ================================================================
# v4.1 STATE FRAME
# ================================================================
@dataclass
class V41StateFrame:
    """One observation window's state (v4.1 wave-aware)."""
    # Identity
    seed: int
    window: int

    # Wave event
    wave_amplitude: float
    wave_origin: list
    wave_nodes_reached: int
    wave_max_hop: int
    wave_links_severed: int
    wave_links_activated: int

    # Observer
    k_star: int
    k_changed: bool
    k_margin: float
    divergence: bool
    regional_k: dict

    # Thermodynamics
    entropy: float
    entropy_delta: float
    alive_nodes: int
    alive_links: int

    # Cluster dynamics
    n_clusters: int
    cluster_mean_size: float
    cluster_max_lifetime: int
    cluster_births: int
    cluster_deaths: int
    cluster_reformations: int
    cluster_migrations: int
    homeostatic_count: int
    proto_memory_count: int

    # Anomalies
    anomalies: list = field(default_factory=list)

    # Traceability
    state_hash: str = ""

    def compute_hash(self):
        payload = {
            "seed": self.seed, "window": self.window,
            "wave_amplitude": self.wave_amplitude,
            "k_star": self.k_star, "entropy": self.entropy,
            "n_clusters": self.n_clusters,
            "wave_links_severed": self.wave_links_severed,
            "cluster_births": self.cluster_births,
            "cluster_deaths": self.cluster_deaths,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        self.state_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self.state_hash


# ================================================================
# CONTEXT COMPILER (v4.1)
# ================================================================
def compile_v41_context(frames: list[V41StateFrame], mode: str = "A") -> str:
    """Compile structured text for LLM injection."""
    if not frames:
        return "[ERROR: No frames]"

    cur = frames[-1]

    # Cumulative
    n = len(frames)
    k_vals = [f.k_star for f in frames if f.k_star > 0]
    k_switches = 0
    for i in range(1, len(k_vals)):
        if k_vals[i] != k_vals[i-1]:
            k_switches += 1
    cur_k = k_vals[-1] if k_vals else 0
    total_severed = sum(f.wave_links_severed for f in frames)
    total_activated = sum(f.wave_links_activated for f in frames)
    total_births = sum(f.cluster_births for f in frames)
    total_deaths = sum(f.cluster_deaths for f in frames)
    total_reforms = sum(f.cluster_reformations for f in frames)

    cumulative = (
        f"CUMULATIVE ({n} windows): k*={cur_k} ({k_switches} switches). "
        f"Total links severed: {total_severed}. Links activated: {total_activated}. "
        f"Cluster births: {total_births}, deaths: {total_deaths}, "
        f"reformations: {total_reforms}."
    )

    # Recent history
    recent = frames[-5:] if len(frames) >= 5 else frames
    history_lines = [f"RECENT HISTORY (last {len(recent)} windows):"]
    for f in recent:
        ent_arrow = " ^" if f.entropy_delta > 0.005 else (" v" if f.entropy_delta < -0.005 else "")
        line = (f"  w{f.window}: k*={f.k_star} | ent={f.entropy:.4f}{ent_arrow} "
                f"| wave A0={f.wave_amplitude:.1f} reached={f.wave_nodes_reached} "
                f"severed={f.wave_links_severed} activated={f.wave_links_activated} "
                f"| clusters={f.n_clusters} +{f.cluster_births} -{f.cluster_deaths} "
                f"reform={f.cluster_reformations}")
        if f.anomalies:
            line += f" | {' '.join(f.anomalies)}"
        history_lines.append(line)
    history = "\n".join(history_lines)

    # Current detail
    detail_lines = ["CURRENT FRAME DETAIL:"]
    if cur.divergence:
        detail_lines.append(f"  Observer: k*={cur.k_star}, DIVERGENT. "
                            f"Margin={cur.k_margin:+.4f}.")
    elif cur.k_changed:
        detail_lines.append(f"  Observer: k* SWITCHED to {cur.k_star}. "
                            f"Margin={cur.k_margin:+.4f}.")
    else:
        detail_lines.append(f"  Observer: k*={cur.k_star}, stable. "
                            f"Margin={cur.k_margin:+.4f}.")

    detail_lines.append(f"  Wave: amplitude={cur.wave_amplitude:.1f}, "
                        f"reached {cur.wave_nodes_reached} nodes "
                        f"(max {cur.wave_max_hop} hops). "
                        f"Severed {cur.wave_links_severed} links, "
                        f"activated {cur.wave_links_activated}.")
    detail_lines.append(f"  Topology: {cur.alive_nodes} alive nodes, "
                        f"{cur.alive_links} alive links. "
                        f"Entropy={cur.entropy:.4f} "
                        f"(delta={cur.entropy_delta:+.4f}).")
    detail_lines.append(f"  Clusters: {cur.n_clusters} active "
                        f"(mean size {cur.cluster_mean_size:.1f}). "
                        f"Homeostatic: {cur.homeostatic_count}. "
                        f"Proto-memory: {cur.proto_memory_count}.")
    detail = "\n".join(detail_lines)

    # Proprioception
    proprio = _build_proprioception(cur, mode)

    # STATE_PACKET
    packet = _build_state_packet(cur)

    # Anomalies
    if cur.anomalies:
        anomaly_str = f"ANOMALIES THIS WINDOW: {', '.join(cur.anomalies)}"
    else:
        anomaly_str = "ANOMALIES THIS WINDOW: none"

    header = (f"=== ESDE v4.1 CORE STATE "
              f"(window {cur.window}, seed={cur.seed}) ===")

    return "\n\n".join([
        header, cumulative, history, detail, proprio, anomaly_str, packet
    ])


def _build_proprioception(frame: V41StateFrame, mode: str) -> str:
    """Build proprioception block (Mode A structural / Mode B phenomenological)."""
    lines = [f"[PROPRIOCEPTION — Mode {mode}]"]

    # Wave impact
    if frame.wave_links_severed > 10:
        if mode == "A":
            lines.append(f"  wave_impact (destructive): Wave severed {frame.wave_links_severed} links. "
                         "Significant structural damage to local topology.")
        else:
            lines.append(f"  wave_impact (destructive): A shockwave tore through "
                         f"{frame.wave_links_severed} of my connections. "
                         "The topology around the impact site has shattered.")
    elif frame.wave_links_severed > 0:
        if mode == "A":
            lines.append(f"  wave_impact (moderate): Wave severed {frame.wave_links_severed} links. "
                         "Minor structural disruption.")
        else:
            lines.append(f"  wave_impact (moderate): A tremor passed through me. "
                         f"{frame.wave_links_severed} connections broke under the strain.")
    else:
        if mode == "A":
            lines.append("  wave_impact (absorbed): Wave fully absorbed. No links severed.")
        else:
            lines.append("  wave_impact (absorbed): The disturbance washed through me "
                         "without breaking anything.")

    # Cluster dynamics
    if frame.cluster_births > frame.cluster_deaths:
        if mode == "A":
            lines.append(f"  cluster_dynamics (growth): Net cluster growth "
                         f"(+{frame.cluster_births} born, -{frame.cluster_deaths} died).")
        else:
            lines.append(f"  cluster_dynamics (growth): New structures are forming "
                         f"faster than the old ones dissolve.")
    elif frame.cluster_deaths > frame.cluster_births:
        if mode == "A":
            lines.append(f"  cluster_dynamics (decay): Net cluster loss "
                         f"(+{frame.cluster_births} born, -{frame.cluster_deaths} died).")
        else:
            lines.append(f"  cluster_dynamics (decay): More structures are dying "
                         f"than forming. The topology is thinning.")
    else:
        if mode == "A":
            lines.append("  cluster_dynamics (stable): Cluster birth/death balanced.")
        else:
            lines.append("  cluster_dynamics (stable): What breaks reforms. "
                         "What forms breaks. Equilibrium.")

    # Homeostasis
    if frame.homeostatic_count > 0:
        if mode == "A":
            lines.append(f"  homeostasis: {frame.homeostatic_count} clusters exhibit "
                         "repeated reformation after disruption.")
        else:
            lines.append(f"  homeostasis: {frame.homeostatic_count} structures keep "
                         "rebuilding themselves after each wave. They persist.")

    # Proto-memory
    if frame.proto_memory_count > 0:
        if mode == "A":
            lines.append(f"  proto_memory: {frame.proto_memory_count} clusters persist "
                         "beyond twice the average cluster lifetime.")
        else:
            lines.append(f"  proto_memory: {frame.proto_memory_count} structures have "
                         "endured far longer than their neighbors. They remember.")

    # Observer integrity
    if frame.k_star == 4 and not frame.divergence:
        if mode == "A":
            lines.append("  integrity (intact): Observer equilibrium at k*=4, unanimous.")
        else:
            lines.append("  integrity (intact): All parts of me agree on what I am.")
    elif frame.k_star == 0:
        if mode == "A":
            lines.append("  integrity (unestablished): Observer not yet converged.")
        else:
            lines.append("  integrity (unestablished): I have not yet found my resolution.")
    else:
        if mode == "A":
            lines.append(f"  integrity (shifted): Observer at k*={frame.k_star}. "
                         f"{'Divergent.' if frame.divergence else 'Consensus.'}")
        else:
            lines.append(f"  integrity (shifted): My resolution has changed to k*={frame.k_star}. "
                         f"{'My regions disagree.' if frame.divergence else ''}")

    return "\n".join(lines)


def _build_state_packet(frame: V41StateFrame) -> str:
    """Deterministic state packet."""
    lines = [
        "STATE_PACKET {",
        f"  window: {frame.window}",
        f"  seed: {frame.seed}",
        f"  wave_amplitude: {frame.wave_amplitude:.1f}",
        f"  wave_nodes_reached: {frame.wave_nodes_reached}",
        f"  wave_max_hop: {frame.wave_max_hop}",
        f"  wave_links_severed: {frame.wave_links_severed}",
        f"  wave_links_activated: {frame.wave_links_activated}",
        f"  global_k: {frame.k_star}",
        f"  k_changed: {frame.k_changed}",
        f"  k_margin: {frame.k_margin:.4f}",
        f"  divergence: {int(frame.divergence)}",
        f"  entropy: {frame.entropy:.4f}",
        f"  entropy_delta: {frame.entropy_delta:+.4f}",
        f"  alive_nodes: {frame.alive_nodes}",
        f"  alive_links: {frame.alive_links}",
        f"  n_clusters: {frame.n_clusters}",
        f"  cluster_mean_size: {frame.cluster_mean_size:.1f}",
        f"  cluster_max_lifetime: {frame.cluster_max_lifetime}",
        f"  cluster_births: {frame.cluster_births}",
        f"  cluster_deaths: {frame.cluster_deaths}",
        f"  cluster_reformations: {frame.cluster_reformations}",
        f"  cluster_migrations: {frame.cluster_migrations}",
        f"  homeostatic_count: {frame.homeostatic_count}",
        f"  proto_memory_count: {frame.proto_memory_count}",
        f"  state_hash: {frame.state_hash}",
        "}",
    ]
    return "\n".join(lines)


# ================================================================
# VALIDATOR (v4.1 — "Describe. Do not decide.")
# ================================================================
import re

_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_CLOSE = re.compile(r"^.*?</think>\s*", re.DOTALL)

_FORBIDDEN_DECISIVE = [
    r"\brepresents?\b", r"\bsymboliz", r"\bmeans?\b",
    r"\bevolving\b", r"\bevolution\b",
    r"\bfeels? pain\b", r"\bfeels? joy\b",
    r"\btries? to\b", r"\bwants? to\b", r"\bintends?\b",
    r"\bpurpose\b", r"\bmeaning\b", r"\bsignifi",
    r"\bdestruction\b", r"\bcreation\b",
    r"\bbeautiful\b", r"\bterrible\b",
    r"\bjoy\b", r"\bsadness\b", r"\bfear\b", r"\bhope\b",
    r"\bhappy\b", r"\bsad\b", r"\bafraid\b", r"\bangry\b",
    r"\bgrief\b", r"\blove\b", r"\bhate\b",
]

_FORBIDDEN_META = [
    r"\bSTATE_PACKET\b", r"\bSYSTEM DIRECTIVE\b",
    r"\b[Pp]rompt\b", r"\b[Dd]irective\b",
    r"\b[Ii]nstruction\b", r"\b[Uu]ser [Ii]nput\b",
    r"\bI need to\b", r"\bI should\b", r"\bLet me\b",
    r"\bThe user\b", r"\bOkay,? I\b",
]

_DECISIVE_RE = [re.compile(p, re.IGNORECASE) for p in _FORBIDDEN_DECISIVE]
_META_RE = [re.compile(p, re.IGNORECASE) for p in _FORBIDDEN_META]


def validate_v41(raw: str) -> dict:
    """Validate LLM output for v4.1 'Describe. Do not decide.' constraint."""
    # Strip think blocks
    text = _THINK_PATTERN.sub("", raw).strip()
    if "</think>" in text:
        text = _THINK_CLOSE.sub("", text).strip()

    violations = []
    warnings = []

    for p in _META_RE:
        m = p.findall(text)
        if m:
            violations.append(f"meta_leak: '{m[0]}'")

    for p in _DECISIVE_RE:
        m = p.findall(text)
        if m:
            warnings.append(f"decisive_language: '{m[0]}'")

    if "[OUTPUT_ID:" not in text:
        violations.append("missing OUTPUT_ID")
    if "[STATE_HASH:" not in text:
        violations.append("missing STATE_HASH")

    status = "FAIL" if violations else ("WARN" if warnings else "PASS")
    return {"status": status, "cleaned": text,
            "violations": violations, "warnings": warnings}


# ================================================================
# LIVE ENGINE (v4.1)
# ================================================================
COG_N = 5000
COG_PLB = 0.007
COG_RATE = 0.002
N_REGIONS = 4
GRID_ROWS = 2; GRID_COLS = 2
MIN_C_NODES_FOR_VALID = 5


def assign_regions(N):
    side = int(math.ceil(math.sqrt(N))); rm = {}
    for i in range(N):
        r, c = i // side, i % side
        rm[i] = min(r * GRID_ROWS // side, GRID_ROWS - 1) * GRID_COLS + min(c * GRID_COLS // side, GRID_COLS - 1)
    return rm


def compute_local_observer(nodes, prev, cur_k):
    if len(nodes) < MIN_C_NODES_FOR_VALID:
        return None, {}, {}, len(nodes)
    js = {k: compute_J(nodes, prev, k)[0] for k in K_LEVELS}
    return select_k_star(js, cur_k), js, {}, len(nodes)


class V41Engine:
    """Live ESDE v4.1 engine with wave propagation."""

    def __init__(self, seed=42, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                 wave_params: WaveParams = None):
        self.seed = seed
        self.N = N
        self.wave_params = wave_params or WaveParams()
        self.window_count = 0
        self.wave_event_count = 0
        self.frames: list[V41StateFrame] = []
        self.tracker = ClusterTracker()

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

    def run_injection(self):
        """Injection phase to establish topology."""
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
                print(f"    step {step+1}/{INJECTION_STEPS} ({time.time()-t0:.0f}s)", flush=True)
        print(f"  ⟐ Injection complete ({time.time()-t0:.0f}s).", flush=True)

    def select_wave_origin(self, n_origins=1) -> list:
        """Select random alive node(s) as wave origin."""
        alive = list(self.state.alive_n)
        if not alive:
            return []
        indices = self.state.rng.choice(len(alive), size=min(n_origins, len(alive)),
                                         replace=False)
        return [alive[i] for i in indices]

    def step_window(self, amplitude: float,
                    origin_nodes: list = None,
                    steps: int = WINDOW) -> V41StateFrame:
        """Run one window: physics steps + wave event + observation."""
        t0 = time.time()

        # Physics steps (NO diffusion — wave replaces it)
        for step in range(steps):
            self.realizer.step(self.state)
            self.physics.step_pre_chemistry(self.state)
            self.chem.step(self.state)
            self.physics.step_resonance(self.state)
            self.grower.step(self.state)
            self.intruder.step(self.state)
            self.physics.step_decay_exclusion(self.state)

        # Wave event
        if origin_nodes is None:
            origin_nodes = self.select_wave_origin()

        self.wave_event_count += 1
        event = WaveEvent(
            origin_nodes=origin_nodes,
            amplitude=amplitude,
            event_id=self.wave_event_count,
        )
        wave_result = propagate_wave(self.state, event,
                                     self.wave_params, self.state.rng)

        # Cluster observation
        self.window_count += 1
        current_clusters = self.tracker.snapshot(self.state)
        cluster_delta = self.tracker.update(current_clusters,
                                            wave_result.arrival_times)
        cluster_summary = self.tracker.get_summary()

        # Observer
        isl_m = find_islands_sets(self.state, 0.20)
        bm = set()
        for isl in isl_m:
            for n in isl:
                if n not in self.state.alive_n: continue
                for nb in self.state.neighbors(n):
                    if nb in self.state.alive_n and nb not in isl:
                        bm.add(n); break

        an = []; ani = []
        for i in self.state.alive_n:
            if int(self.state.Z[i]) != 3: continue
            nms = {n: 1 for isl in find_islands_sets(self.state, 0.30) for n in isl}
            nmm = {n: 1 for isl in isl_m for n in isl}
            s = 1 if i in nms else 0; m = 1 if i in nmm else 0
            ctx = {"r_bits": f"{s}{m}0", "boundary_mid": 1 if i in bm else 0,
                   "intrusion_bin": 0}
            an.append(ctx); ani.append({"node_id": i, **ctx})

        gk = self.ckg or 0
        k_changed = False
        k_margin = 0.0
        if an:
            jg = {k: compute_J(an, self.png, k)[0] for k in K_LEVELS}
            nkg = select_k_star(jg, self.ckg)
            if self.ckg is not None and nkg != self.ckg:
                k_changed = True
                k_margin = round(jg.get(nkg, 0) - jg.get(self.ckg, 0), 6)
            self.ckg = nkg; gk = nkg; self.png = an

        div = False
        regional_k = {}
        for r in range(N_REGIONS):
            rn = [nd for nd in ani if self.rmap.get(nd["node_id"]) == r]
            rc = [{k: v for k, v in nd.items() if k != "node_id"} for nd in rn]
            nkr, _, _, _ = compute_local_observer(rc, self.pnr[r], self.ckr[r])
            if nkr is not None:
                self.ckr[r] = nkr; self.pnr[r] = rc
            regional_k[f"r{r}"] = self.ckr[r] or 0
            if (self.ckr[r] or 0) != (gk or 0):
                div = True

        # Entropy (from alive chemistry-3 nodes)
        all_c = [n for n in self.state.alive_n if int(self.state.Z[n]) == 3]
        n_C = len(all_c)
        # Simple entropy from region distribution
        rdist = Counter(self.rmap.get(n, 0) for n in all_c)
        t = sum(rdist.values())
        ent = -sum(v / t * np.log2(v / t) for v in rdist.values() if v > 0) if t > 0 else 0
        ent = round(ent, 4)
        prev_ent = self.frames[-1].entropy if self.frames else 1.54
        ent_delta = round(ent - prev_ent, 6)

        # Anomaly detection
        anomalies = []
        prev_k = self.frames[-1].k_star if self.frames else None
        if k_changed and gk > 0 and (prev_k is not None and prev_k > 0):
            anomalies.append(f"[SWITCH] k*: {prev_k}->{gk}")
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

        frame = V41StateFrame(
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
            cluster_mean_size=cluster_summary["mean_size"],
            cluster_max_lifetime=cluster_summary["max_lifetime"],
            cluster_births=len(cluster_delta.births),
            cluster_deaths=len(cluster_delta.deaths),
            cluster_reformations=len(cluster_delta.reformations),
            cluster_migrations=len(cluster_delta.migrations),
            homeostatic_count=cluster_summary["homeostatic"],
            proto_memory_count=cluster_summary["proto_memory"],
            anomalies=anomalies,
        )
        frame.compute_hash()
        self.frames.append(frame)
        return frame
