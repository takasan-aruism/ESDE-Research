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
    World B — independent causal layer on top of physics.

    物理層は種を撒く。仮想層は自分で育てる。

    R+ events SEED new labels. That's all physics gives.
    Once born, a label lives by its own logic:
      - Label exerts phase torque on its constituent nodes.
      - If torque SUCCEEDS (θ actually moves toward label's sig),
        that success IS the label's energy. Influence = existence.
      - If torque FAILS (nodes don't respond), label weakens.
      - Labels compete for nodes. Strongest influence wins.
      - Labels can outlive their physical structures entirely.
        A label is a standing wave in θ-space, not in S-space.

    Physical layer: R>0 links come and go. That's physics.
    Virtual layer: patterns of θ-influence persist, compete, evolve.
    Different timescale. Different energy. Different world.
    """

    def __init__(self):
        # Recurrence Map: {lk: times_seen_rplus}
        # Just a counter. How many windows was this pair R>0?
        self.recurrence = {}

        # Label Registry: {label_id: Label}
        self.labels = {}
        self.next_label_id = 0

        # Per-window stats
        self.stats = {}

    def step(self, state, window_count):
        """
        Called once per window, post-physics-loop.
        1. Seed: detect R>0 motifs → birth new labels
        2. Live: labels exert torque → measure success → update strength
        3. Die: labels with no influence decay
        """
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

        # ── 1. SEED: Observe R>0 motifs in physics layer ──
        current_rplus = set()
        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                current_rplus.add(lk)
                self.recurrence[lk] = self.recurrence.get(lk, 0) + 1

        # Clean stale recurrence entries (not seen for a while)
        # But don't rush — memory persists longer than physics
        stale = [lk for lk, count in self.recurrence.items()
                 if lk not in current_rplus and count < 2]
        for lk in stale:
            del self.recurrence[lk]

        stats["recurrence_entries"] = len(self.recurrence)

        # Find connected R>0 subgraphs (motifs)
        motifs = self._find_rplus_motifs(state, current_rplus)
        stats["motifs_detected"] = len(motifs)

        # Birth new labels from motifs not yet labeled
        for motif_nodes, motif_links in motifs:
            already_labeled = False
            for label in self.labels.values():
                overlap = label["nodes"] & motif_nodes
                if len(overlap) > len(motif_nodes) * 0.5:
                    already_labeled = True
                    break
            if already_labeled:
                continue

            # Capture phase signature at birth
            thetas = [float(state.theta[n]) for n in motif_nodes
                      if n in state.alive_n]
            if not thetas:
                continue
            phase_sig = math.atan2(
                sum(math.sin(t) for t in thetas) / len(thetas),
                sum(math.cos(t) for t in thetas) / len(thetas))

            # Initial strength = number of constituent R>0 links
            # Small. Must earn more through influence.
            self.labels[self.next_label_id] = {
                "nodes": frozenset(motif_nodes),
                "links": frozenset(motif_links),
                "phase_sig": phase_sig,
                "strength": float(len(motif_links)),
                "born": window_count,
                "prev_alignment": 0.0,  # for measuring torque success
            }
            self.next_label_id += 1
            stats["labels_born"] += 1

        # ── 2. LIVE: Labels exert torque and measure success ──
        # Torque: pull constituent nodes' θ toward phase_sig.
        # Success: how much θ actually aligns (cos similarity).
        # Success IS energy. No physics dependency.

        node_torques = {}  # {node: (torque_val, label_strength, label_id)}
        total_virtual_energy = 0.0

        for lid, label in list(self.labels.items()):
            # Measure current alignment of constituent nodes
            alignments = []
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                # cos(θ_n - phase_sig): 1.0 = perfect alignment, -1.0 = opposite
                alignment = math.cos(theta_n - label["phase_sig"])
                alignments.append(alignment)

            if alignments:
                mean_alignment = sum(alignments) / len(alignments)
            else:
                mean_alignment = 0.0

            # Success = improvement in alignment since last window
            prev = label.get("prev_alignment", 0.0)
            success = mean_alignment - prev
            label["prev_alignment"] = mean_alignment

            # Strength update:
            # Positive success (nodes moved toward us) → strength grows
            # Negative success (nodes moved away) → strength shrinks
            # Neutral → slow natural decay (must keep influencing to survive)
            #
            # strength += success × |current_strength|
            # The stronger you are, the more you gain/lose from success.
            # tanh bounds the growth to prevent runaway.
            strength_delta = success * math.tanh(label["strength"])

            # Natural decay: labels must actively maintain influence
            # Decay = 1/label_count → more competition = faster decay
            label_count = max(1, len(self.labels))
            natural_decay = label["strength"] / label_count

            label["strength"] += strength_delta - natural_decay

            if label["strength"] < 0:
                label["strength"] = 0.0

            total_virtual_energy += label["strength"]

            # Compute torque for this label
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

        # Apply torque (strongest label per node wins)
        for n, (torque, _, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        # ── 3. DIE: Remove dead labels ──
        dead_labels = [lid for lid, label in self.labels.items()
                       if label["strength"] < 0.001]
        for lid in dead_labels:
            del self.labels[lid]
            stats["labels_died"] += 1

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
