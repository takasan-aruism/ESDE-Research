#!/usr/bin/env python3
"""
ESDE v7.0 — World Induction
==============================
Phase : v7.0 (Virtual Layer — World B)
Role  : Claude (Implementation)

"物理層は床。床の上に建てる。"

Physical Layer (World A): v6.0 unchanged.
  v4.9 + topological E_ij. Frozen operators. bg seeding.
  Runs per-step. Produces links, clusters, R+, snaps.
  NO modifications from v6.0.

Virtual Layer (World B): NEW. Runs once per window (post-loop).
  Input:  observes physical layer state (read-only).
  Energy: stability of physical structures IS virtual energy.
          1 R>0 link surviving 1 window = 1 unit of virtual fuel.
          This is not physical E. It's a different currency.
  Output: phase torque on constituent nodes (the ONLY feedback).
          Physical layer sees slightly adjusted θ. That's all.

Virtual Layer architecture:
  1. Recurrence Map: tracks which link-pairs have been R>0.
     Each window of R>0 survival adds virtual energy.
     Death doesn't erase — it's memory. Decay is state-dependent.

  2. Motif Detection: connected R>0 subgraphs (triangles+).
     Motifs with high recurrence energy → candidate labels.

  3. Label Registry: motifs that recur above dynamic threshold.
     Labels have: constituent nodes, phase signature, strength.
     Label strength = sum of constituent recurrence energies.

  4. Phase Torque: labels pull constituent nodes' θ toward
     the label's phase signature. Strength-proportional.
     This is the ONLY physical feedback. No latent manipulation.
     No S modification. No E injection. Just θ nudging.

  5. Diversity: multiple labels compete for the same nodes.
     Strongest label wins the torque. Weaker labels decay.
     New motifs can become new labels. Old labels can die.

No fixed constants. All thresholds derived from distributions.
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

from esde_v60_engine import V60Engine, V60EncapsulationParams, V60_WINDOW


# ================================================================
V70_WINDOW = 50


# ================================================================
@dataclass
class V70EncapsulationParams(V60EncapsulationParams):
    """v7.0: No new physics constants. Virtual layer is self-scaling."""
    pass


# ================================================================
# VIRTUAL LAYER (WORLD B)
# ================================================================
class VirtualLayer:
    """
    World B — runs on top of physics layer.

    The most stable physical structures become virtual energy.
    Virtual energy generates diversity (labels, competition).
    Feedback to physics: phase torque only.
    """

    def __init__(self):
        # Recurrence Map: {lk: virtual_energy}
        # Every window an R>0 link survives, it gains energy.
        self.recurrence = {}

        # Label Registry: {label_id: Label}
        self.labels = {}
        self.next_label_id = 0

        # Per-window stats
        self.stats = {}

    def step(self, state, window_count):
        """
        Called once per window, post-physics-loop.
        Read physical state → update virtual state → apply torque.
        """
        stats = {
            "virtual_energy_total": 0.0,
            "recurrence_entries": 0,
            "labels_active": 0,
            "labels_born": 0,
            "labels_died": 0,
            "torque_events": 0,
            "torque_total": 0.0,
            "motifs_detected": 0,
        }

        # ── 1. Update Recurrence Map ──
        # R>0 links accumulate virtual energy. R×S per window.
        # Physical energy is tiny. Virtual energy is its integral over time.
        current_rplus = set()
        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                current_rplus.add(lk)
                s = state.S.get(lk, 0.0)
                self.recurrence[lk] = self.recurrence.get(lk, 0.0) + r * s

        # Decay recurrence for links NOT currently R>0
        # Decay rate: proportion of R>0 links that died this window
        # More death → faster memory decay (crisis clears old patterns)
        # Less death → slower decay (stability preserves memory)
        alive_r_count = len(current_rplus)
        total_recurrence = len(self.recurrence)
        dead_r_count = total_recurrence - alive_r_count
        if total_recurrence > 0:
            decay_frac = dead_r_count / total_recurrence
        else:
            decay_frac = 0.0

        dead_keys = []
        for lk in list(self.recurrence):
            if lk not in current_rplus:
                self.recurrence[lk] *= (1.0 - decay_frac)
                if self.recurrence[lk] < 0.001:
                    dead_keys.append(lk)
        for lk in dead_keys:
            del self.recurrence[lk]

        stats["recurrence_entries"] = len(self.recurrence)
        stats["virtual_energy_total"] = round(
            sum(self.recurrence.values()), 4)

        # ── 2. Motif Detection ──
        # Find connected subgraphs of current R>0 links (triangles+).
        # A motif = a set of nodes forming a connected R>0 subgraph.
        motifs = self._find_rplus_motifs(state, current_rplus)
        stats["motifs_detected"] = len(motifs)

        # ── 3. Label Management ──
        # Motifs with high recurrence → labels.
        # Threshold: mean recurrence of all tracked pairs (dynamic).
        if self.recurrence:
            threshold = sum(self.recurrence.values()) / len(self.recurrence)
        else:
            threshold = 0.0

        # Check existing labels: still alive?
        dead_labels = []
        for lid, label in self.labels.items():
            # Label survives if ANY constituent link is currently R>0
            alive_in_label = sum(1 for lk in label["links"]
                                 if lk in current_rplus)
            if alive_in_label > 0:
                # Update strength: sum of recurrence of constituent links
                label["strength"] = sum(
                    self.recurrence.get(lk, 0.0)
                    for lk in label["links"])
                # Update phase signature: circular mean of constituent θ
                thetas = [float(state.theta[n]) for n in label["nodes"]
                          if n in state.alive_n]
                if thetas:
                    label["phase_sig"] = math.atan2(
                        sum(math.sin(t) for t in thetas) / len(thetas),
                        sum(math.cos(t) for t in thetas) / len(thetas))
            else:
                # No constituent R>0 link alive → label decays
                label["strength"] *= (1.0 - decay_frac)
                if label["strength"] < 0.001:
                    dead_labels.append(lid)

        for lid in dead_labels:
            del self.labels[lid]
            stats["labels_died"] += 1

        # New labels from motifs with sufficient recurrence
        for motif_nodes, motif_links in motifs:
            motif_energy = sum(
                self.recurrence.get(lk, 0.0) for lk in motif_links)
            if motif_energy < threshold:
                continue
            # Check if this motif is already a label (node overlap)
            already_labeled = False
            for label in self.labels.values():
                overlap = label["nodes"] & motif_nodes
                if len(overlap) > len(motif_nodes) * 0.5:
                    already_labeled = True
                    break
            if already_labeled:
                continue
            # Birth new label
            thetas = [float(state.theta[n]) for n in motif_nodes
                      if n in state.alive_n]
            phase_sig = math.atan2(
                sum(math.sin(t) for t in thetas) / max(1, len(thetas)),
                sum(math.cos(t) for t in thetas) / max(1, len(thetas))
            ) if thetas else 0.0

            self.labels[self.next_label_id] = {
                "nodes": motif_nodes,
                "links": motif_links,
                "phase_sig": phase_sig,
                "strength": motif_energy,
                "born": window_count,
            }
            self.next_label_id += 1
            stats["labels_born"] += 1

        stats["labels_active"] = len(self.labels)

        # ── 4. Phase Torque (the ONLY feedback to physics) ──
        # Each label pulls its constituent nodes' θ toward its phase sig.
        # Torque ∝ label strength (virtual energy).
        # Multiple labels on same node: strongest wins.
        node_torques = {}  # {node: (torque_value, label_strength)}

        for label in self.labels.values():
            if label["strength"] < 0.01:
                continue
            # Normalize strength to [0,1] range
            # Use tanh(strength) — no fixed constant, self-bounding
            torque_magnitude = math.tanh(label["strength"])
            phase_target = label["phase_sig"]

            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_magnitude * math.sin(
                    phase_target - theta_n)

                # Strongest label wins at each node
                existing = node_torques.get(n)
                if existing is None or label["strength"] > existing[1]:
                    node_torques[n] = (torque, label["strength"])

        for n, (torque, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        if stats["torque_events"] > 0:
            stats["torque_total"] = round(stats["torque_total"], 4)
            stats["mean_torque"] = round(
                stats["torque_total"] / stats["torque_events"], 6)
        else:
            stats["mean_torque"] = 0.0

        self.stats = stats
        return stats

    def _find_rplus_motifs(self, state, rplus_links):
        """
        Find connected subgraphs of R>0 links with 3+ nodes.
        Returns list of (node_set, link_set) tuples.
        """
        if not rplus_links:
            return []

        # Build adjacency from R>0 links
        adj = defaultdict(set)
        for lk in rplus_links:
            n1, n2 = lk
            adj[n1].add(n2)
            adj[n2].add(n1)

        # Connected components via BFS
        visited = set()
        motifs = []
        for start in adj:
            if start in visited:
                continue
            component_nodes = set()
            queue = [start]
            while queue:
                n = queue.pop()
                if n in visited:
                    continue
                visited.add(n)
                component_nodes.add(n)
                for nb in adj[n]:
                    if nb not in visited:
                        queue.append(nb)

            if len(component_nodes) >= 3:
                # Collect the R>0 links within this component
                component_links = set()
                for lk in rplus_links:
                    if lk[0] in component_nodes and lk[1] in component_nodes:
                        component_links.add(lk)
                motifs.append((frozenset(component_nodes),
                               frozenset(component_links)))

        return motifs

    def summary(self):
        """For JSON serialization."""
        return {
            "recurrence_entries": len(self.recurrence),
            "virtual_energy_total": round(
                sum(self.recurrence.values()), 4) if self.recurrence else 0,
            "labels_active": len(self.labels),
            "label_details": [
                {
                    "id": lid,
                    "nodes": len(label["nodes"]),
                    "strength": round(label["strength"], 4),
                    "born": label["born"],
                    "phase_sig": round(label["phase_sig"], 4),
                }
                for lid, label in self.labels.items()
            ],
        }


# ================================================================
# V7.0 ENGINE
# ================================================================
class V70Engine(V60Engine):
    """
    V6.0 + Virtual Layer (World B).

    Physical layer: v6.0 step_window() unchanged.
    Virtual layer: runs post-loop, before observer.
    Feedback: phase torque only.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V70EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.virtual = VirtualLayer()
        self.virtual_stats = {}

    def step_window(self, steps=V70_WINDOW):
        """
        Run v6.0 physics loop, then virtual layer.
        Virtual layer runs between physics post-loop and observer.
        """
        # Run v6.0's full step_window (returns frame)
        frame = super().step_window(steps=steps)

        # ── Virtual Layer (World B) ──
        # Runs AFTER physics, BEFORE next window.
        # Reads physical state. Applies phase torque.
        if self.island_tracker.params.recurrence_enabled:
            vs = self.virtual.step(self.state, self.window_count)
            self.virtual_stats = vs
        else:
            self.virtual_stats = {}

        return frame
