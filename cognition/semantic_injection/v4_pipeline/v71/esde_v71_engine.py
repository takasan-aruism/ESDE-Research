#!/usr/bin/env python3
"""
ESDE v7.1 — Genesis + World Induction
========================================
"安定していた物理層が本来の正しい評価軸。
 そこにバーチャルな何を加えるか。"

Physical Layer: V43Engine UNCHANGED.
  7 canonical operators (realizer, physics, chem, resonance,
  grower, intruder, decay_exclusion) + bg seeding.
  Island tracker + semantic pressure.
  NO brittleness, NO void, NO history tensor, NO Z-coupling,
  NO transition field, NO topological E_ij.

Virtual Layer: VirtualLayer from v7.0 (territorial competition).
  Runs post-loop. Reads R+. Seeds labels. Torques θ.
  The ONLY addition to Genesis physics.

Inheritance: V71Engine(V43Engine) + VirtualLayer composition.
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
_V43_DIR = _SCRIPT_DIR.parent / "v43"
_V41_DIR = _SCRIPT_DIR.parent / "v41"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
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


# ================================================================
V71_WINDOW = 50


# ================================================================
@dataclass
class V71EncapsulationParams(EncapsulationParams):
    """v7.1: adds virtual layer toggle to V43 params."""
    virtual_enabled: bool = True


# ================================================================
# VIRTUAL LAYER (identical to v7.0 latest)
# ================================================================
class VirtualLayer:
    """
    World B — independent causal layer on top of Genesis physics.

    R+ events SEED new labels. Once born, labels live by influence.
    Labels that lose territorial control decay via squared loss.
    Feedback: phase torque only.
    """

    def __init__(self):
        self.recurrence = {}
        self.labels = {}
        self.next_label_id = 0
        self.stats = {}

    def step(self, state, window_count):
        stats = {
            "virtual_energy_total": 0.0,
            "recurrence_entries": 0,
            "labels_active": 0,
            "labels_born": 0,
            "labels_died": 0,
            "torque_events": 0,
            "torque_total": 0.0,
            "torque_success": 0.0,
            "motifs_detected": 0,
            "mean_torque": 0.0,
        }

        # ── 1. SEED ──
        current_rplus = set()
        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                current_rplus.add(lk)
                self.recurrence[lk] = self.recurrence.get(lk, 0) + 1

        stale = [lk for lk, count in self.recurrence.items()
                 if lk not in current_rplus and count < 2]
        for lk in stale:
            del self.recurrence[lk]

        stats["recurrence_entries"] = len(self.recurrence)

        motifs = self._find_rplus_motifs(state, current_rplus)
        stats["motifs_detected"] = len(motifs)

        for motif_nodes, motif_links in motifs:
            already_labeled = False
            for label in self.labels.values():
                overlap = label["nodes"] & motif_nodes
                if len(overlap) > len(motif_nodes) * 0.5:
                    already_labeled = True
                    break
            if already_labeled:
                continue

            thetas = [float(state.theta[n]) for n in motif_nodes
                      if n in state.alive_n]
            if not thetas:
                continue
            phase_sig = math.atan2(
                sum(math.sin(t) for t in thetas) / len(thetas),
                sum(math.cos(t) for t in thetas) / len(thetas))

            self.labels[self.next_label_id] = {
                "nodes": frozenset(motif_nodes),
                "links": frozenset(motif_links),
                "phase_sig": phase_sig,
                "strength": float(len(motif_links)),
                "born": window_count,
                "prev_alignment": 0.0,
                "coherence": 1.0,
            }
            self.next_label_id += 1
            stats["labels_born"] += 1

        # ── 2. LIVE ──
        node_torques = {}
        total_virtual_energy = 0.0

        for lid, label in list(self.labels.items()):
            alignments = []
            alive_count = 0
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                alive_count += 1
                theta_n = float(state.theta[n])
                alignment = math.cos(theta_n - label["phase_sig"])
                alignments.append(alignment)

            if alignments:
                mean_alignment = sum(alignments) / len(alignments)
            else:
                mean_alignment = 0.0

            label["coherence"] = alive_count / max(1, len(label["nodes"]))

            prev = label.get("prev_alignment", 0.0)
            success = mean_alignment - prev
            label["prev_alignment"] = mean_alignment

            strength_delta = success * math.tanh(label["strength"])
            label["strength"] += strength_delta

            if label["strength"] < 0:
                label["strength"] = 0.0

            torque_mag = math.tanh(label["strength"])
            if torque_mag < 0.001:
                continue

            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_mag * math.sin(
                    label["phase_sig"] - theta_n)

                existing = node_torques.get(n)
                if existing is None or label["strength"] > existing[1]:
                    node_torques[n] = (torque, label["strength"], lid)

            if success > 0:
                stats["torque_success"] += success

        for n, (torque, _, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        # ── 3. COMPETE ──
        dead_labels = []
        for lid, label in self.labels.items():
            if label["strength"] < 0.001:
                dead_labels.append(lid)
                continue

            my_nodes_alive = [n for n in label["nodes"]
                              if n in state.alive_n]
            if not my_nodes_alive:
                label["strength"] *= 0.5
                if label["strength"] < 0.001:
                    dead_labels.append(lid)
                continue

            nodes_won = sum(1 for n in my_nodes_alive
                           if node_torques.get(n, (0, 0, -1))[2] == lid)
            territory_frac = nodes_won / len(my_nodes_alive)
            territory_loss = 1.0 - territory_frac
            decay = label["strength"] * territory_loss * territory_loss
            label["strength"] -= decay

            if label["strength"] < 0.001:
                dead_labels.append(lid)

            total_virtual_energy += max(0, label["strength"])

        for lid in set(dead_labels):
            if lid in self.labels:
                del self.labels[lid]
                stats["labels_died"] += 1

        # ── 4. Prune recurrence ──
        if len(self.recurrence) > 1000:
            sorted_rec = sorted(self.recurrence.items(), key=lambda x: x[1])
            to_remove = len(self.recurrence) - 1000
            for lk, _ in sorted_rec[:to_remove]:
                del self.recurrence[lk]

        stats["labels_active"] = len(self.labels)
        stats["virtual_energy_total"] = round(total_virtual_energy, 4)

        if stats["torque_events"] > 0:
            stats["torque_total"] = round(stats["torque_total"], 4)
            stats["mean_torque"] = round(
                stats["torque_total"] / stats["torque_events"], 6)
        stats["torque_success"] = round(stats["torque_success"], 4)

        self.stats = stats
        return stats

    def _find_rplus_motifs(self, state, rplus_links):
        if not rplus_links:
            return []
        adj = defaultdict(set)
        for lk in rplus_links:
            n1, n2 = lk
            adj[n1].add(n2)
            adj[n2].add(n1)
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
                component_links = set()
                for lk in rplus_links:
                    if lk[0] in component_nodes and lk[1] in component_nodes:
                        component_links.add(lk)
                motifs.append((frozenset(component_nodes),
                               frozenset(component_links)))
        return motifs

    def summary(self):
        total_strength = sum(lb["strength"] for lb in self.labels.values())
        return {
            "recurrence_entries": len(self.recurrence),
            "virtual_energy_total": round(total_strength, 4),
            "labels_active": len(self.labels),
            "label_details": [
                {
                    "id": lid,
                    "nodes": len(label["nodes"]),
                    "strength": round(label["strength"], 4),
                    "born": label["born"],
                    "phase_sig": round(label["phase_sig"], 4),
                    "alignment": round(label.get("prev_alignment", 0), 4),
                    "coherence": round(label.get("coherence", 0), 4),
                }
                for lid, label in sorted(
                    self.labels.items(),
                    key=lambda x: x[1]["strength"], reverse=True)
            ],
        }


# ================================================================
# V7.1 ENGINE
# ================================================================
class V71Engine(V43Engine):
    """
    V43Engine (Genesis canon) + VirtualLayer.

    step_window: V43's step_window (via super()), then virtual layer.
    Physical layer is IDENTICAL to v4.3.
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V71EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.virtual = VirtualLayer()
        self.virtual_stats = {}

    def step_window(self, steps=V71_WINDOW):
        # V43 full physics + observation
        frame = super().step_window(steps=steps)

        # Virtual Layer (World B) — post-physics
        p = self.island_tracker.params
        if hasattr(p, 'virtual_enabled') and p.virtual_enabled:
            # Count R+ for reporting
            rplus_count = sum(1 for lk in self.state.alive_l
                              if self.state.R.get(lk, 0.0) > 0)

            vs = self.virtual.step(self.state, frame.window)
            self.virtual_stats = vs
            self.virtual_stats["total_rplus"] = rplus_count
        else:
            self.virtual_stats = {"total_rplus": 0}

        return frame
