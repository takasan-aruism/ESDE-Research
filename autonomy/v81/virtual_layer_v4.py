#!/usr/bin/env python3
"""
ESDE Virtual Layer v4 — Macro-Node Compression
=================================================
Level 1: Physical layer (V43, frozen). Does not know labels.
Level 2: THIS FILE. Compression engine. Replaces expensive
         micro-computations with localized formulas.
Level 3: Ontology (future). Built on top of Level 2.

v3 logic preserved. Added:
  - MacroNode: compressed representation of stable 5-node clusters
  - compress_stable_labels(): identifies & compresses at designated window
  - Compressed nodes' internal links removed from physics
  - MacroNode exerts torque via state vector, not micro-physics

物理層は床。圧縮は床のショートカット。意味は後から。
"""

import math
from collections import defaultdict


# ================================================================
# MACRO-NODE STATE (Gemini v8.1 §3)
# ================================================================
class MacroNode:
    """Compressed representation of a stable multi-node cluster.
    
    Required: phase_core_theta, size_class_N, local_stress_omega, h_age
    Optional: nearest_neighbor_dist (pending re-fit validation)
    Quarantined: internal_coherence, carrying_capacity
    """
    __slots__ = [
        'label_id', 'node_ids', 'phase_core_theta', 'size_class_N',
        'local_stress_omega', 'h_age', 'share', 'nearest_dist',
        'born_window', 'compressed_at', 'territory_at_compression',
    ]

    def __init__(self, label_id, node_ids, phase_sig, born_window,
                 compressed_at, territory_at_compression=0):
        self.label_id = label_id
        self.node_ids = frozenset(node_ids)
        self.phase_core_theta = phase_sig
        self.size_class_N = len(node_ids)
        self.local_stress_omega = 0.0
        self.h_age = 0
        self.share = 0.0
        self.nearest_dist = 0.0
        self.born_window = born_window
        self.compressed_at = compressed_at
        self.territory_at_compression = territory_at_compression

    def to_dict(self):
        return {
            'label_id': self.label_id,
            'n_nodes': self.size_class_N,
            'phase_core_theta': round(self.phase_core_theta, 4),
            'h_age': self.h_age,
            'share': round(self.share, 6),
            'nearest_dist': round(self.nearest_dist, 4),
            'local_stress_omega': round(self.local_stress_omega, 4),
            'born_window': self.born_window,
            'compressed_at': self.compressed_at,
            'territory_at_compression': self.territory_at_compression,
        }


class VirtualLayer:

    def __init__(self, compression_enabled=False, compress_at_window=50,
                 compress_min_age=10):
        self.recurrence = {}
        self.labels = {}
        self.next_label_id = 0
        self.stats = {}
        self.lifecycle_log = []

        # Compression config
        self.compression_enabled = compression_enabled
        self.compress_at_window = compress_at_window
        self.compress_min_age = compress_min_age

        # Macro-node registry
        self.macro_nodes = {}        # {label_id: MacroNode}
        self.compressed_nodes = set() # set of node IDs under compression
        self.removed_links = set()    # internal links removed at compression

    # ================================================================
    # COMPRESSION (Gemini v8.1 §4, Run B)
    # ================================================================
    def compress_stable_labels(self, state, window_count):
        """Identify stable labels and compress them into MacroNodes.
        Called once at compress_at_window. Removes internal links
        from the physical layer."""
        if not self.compression_enabled:
            return 0

        compressed_count = 0
        for lid, label in list(self.labels.items()):
            age = window_count - label["born"]
            if age < self.compress_min_age:
                continue
            if len(label["nodes"]) < 3:
                continue

            # Collect ANY internal links (regardless of S)
            # 48-seed data shows: internal S decays to ~0.045 within
            # a few windows. Requiring S >= 0.20 blocks all compression.
            internal_links = []
            for lk in state.alive_l:
                n1, n2 = lk
                if n1 in label["nodes"] and n2 in label["nodes"]:
                    internal_links.append(lk)

            # Compression does NOT require internal links.
            # COMPRESSION TARGET: the virtual claim (frozenset),
            # NOT the physical structure. Label's essence is
            # cognitive binding — the assertion that these nodes
            # belong together, regardless of physical connection.
            # (GPT audit 2026-03-23: approved, explicitly documented)

            # Measure territory before compression (frozen baseline)
            label_node_set = set(label["nodes"])
            territory_at_compress = 0
            for lk in state.alive_l:
                n1, n2 = lk
                if n1 in label_node_set or n2 in label_node_set:
                    territory_at_compress += 1

            # Create MacroNode
            mn = MacroNode(
                label_id=lid,
                node_ids=label["nodes"],
                phase_sig=label["phase_sig"],
                born_window=label["born"],
                compressed_at=window_count,
                territory_at_compression=territory_at_compress,
            )
            mn.h_age = age
            mn.share = label["share"]
            self.macro_nodes[lid] = mn

            # Register compressed nodes
            for n in label["nodes"]:
                self.compressed_nodes.add(n)

            # Remove internal links from physics (proper bookkeeping)
            for lk in internal_links:
                if lk in state.alive_l:
                    state.S[lk] = 0.0
                    del state.alive_l[lk]
                    self.removed_links.add(lk)

            # Remove compressed nodes from alive_n → frozen operators
            # skip them entirely → SPEED IMPROVEMENT.
            # MacroNode handles torque for these nodes via formula.
            for n in label["nodes"]:
                state.alive_n.discard(n)

            # Invalidate neighbor cache (state rebuilds lazily)
            if hasattr(state, '_nbr_cache'):
                state._nbr_cache.clear()

            compressed_count += 1

            self.lifecycle_log.append({
                "label_id": lid, "window": window_count,
                "event": "compressed",
                "nodes": len(label["nodes"]),
                "share": round(label["share"], 6),
                "internal_links_removed": len(internal_links),
                "phase_sig": round(label["phase_sig"], 4),
                "h_age": age,
            })

        return compressed_count

    def _compute_perimeter_omega(self, mn, state, substrate=None,
                                  degree_map=None):
        """Compute local stress from macro-node's perimeter.
        Uses pre-built degree map for O(1) per neighbor."""
        omega_sum = 0.0
        count = 0
        if substrate and degree_map:
            for n in mn.node_ids:
                for nb in substrate.get(n, []):
                    if nb in state.alive_n and nb not in self.compressed_nodes:
                        deg = degree_map.get(nb, 0)
                        if deg > 0:
                            omega_sum += deg
                            count += 1
        mn.local_stress_omega = omega_sum / max(1, count)

    @staticmethod
    def _build_degree_map(state):
        """Pre-compute degree for all alive nodes. O(links) total."""
        deg = {}
        for lk in state.alive_l:
            n1, n2 = lk
            deg[n1] = deg.get(n1, 0) + 1
            deg[n2] = deg.get(n2, 0) + 1
        return deg

    def _macro_node_torque(self, mn, state, node_torques):
        """MacroNode exerts torque via state vector (Level 2).
        Compressed nodes are not in alive_n but still have theta."""
        energy = mn.share
        if energy < 0.0001:
            return
        torque_mag = energy
        for n in mn.node_ids:
            # Compressed nodes still have theta — torque applies directly
            theta_n = float(state.theta[n])
            torque = torque_mag * math.sin(mn.phase_core_theta - theta_n)
            existing = node_torques.get(n)
            if existing is None or energy > existing[1]:
                node_torques[n] = (torque, energy, mn.label_id)

    # ================================================================
    # TERRITORY STATS (v3)
    # ================================================================
    def _territory_stats(self, lid, label, state, node_torques):
        label_node_set = set(label["nodes"])
        territory_links = 0
        territory_rplus = 0
        territory_S_sum = 0.0
        for lk in state.alive_l:
            n1, n2 = lk
            if n1 in label_node_set or n2 in label_node_set:
                territory_links += 1
                r = state.R.get(lk, 0.0)
                s = state.S.get(lk, 0.0)
                if r > 0:
                    territory_rplus += 1
                territory_S_sum += s
        territory_S_mean = (territory_S_sum / territory_links
                            if territory_links > 0 else 0.0)
        return territory_links, territory_rplus, territory_S_mean

    def _nearest_label_dist(self, lid, label):
        min_dist = math.pi
        for other_id, other in self.labels.items():
            if other_id == lid:
                continue
            d = abs(label["phase_sig"] - other["phase_sig"])
            if d > math.pi:
                d = 2 * math.pi - d
            if d < min_dist:
                min_dist = d
        # Also check macro-nodes
        for mn_id, mn in self.macro_nodes.items():
            if mn_id == lid:
                continue
            d = abs(label["phase_sig"] - mn.phase_core_theta)
            if d > math.pi:
                d = 2 * math.pi - d
            if d < min_dist:
                min_dist = d
        return min_dist

    def _n_phase_neighbors(self, lid, label, threshold=0.3):
        count = 0
        for other_id, other in self.labels.items():
            if other_id == lid:
                continue
            d = abs(label["phase_sig"] - other["phase_sig"])
            if d > math.pi:
                d = 2 * math.pi - d
            if d < threshold:
                count += 1
        for mn_id, mn in self.macro_nodes.items():
            if mn_id == lid:
                continue
            d = abs(label["phase_sig"] - mn.phase_core_theta)
            if d > math.pi:
                d = 2 * math.pi - d
            if d < threshold:
                count += 1
        return count

    # ================================================================
    # MAIN STEP (v3 logic + macro-node handling)
    # ================================================================
    def step(self, state, window_count, islands=None, substrate=None):
        stats = {
            "budget": 0.0, "labels_active": 0,
            "labels_born": 0, "labels_died": 0,
            "torque_events": 0, "torque_total": 0.0,
            "motifs_detected": 0, "mean_torque": 0.0,
            "top_share": 0.0, "label_rplus_rate": 0.0,
            "macro_nodes_active": len(self.macro_nodes),
            "compressed_links_removed": len(self.removed_links),
        }

        alive_links = len(state.alive_l)
        budget = 1.0 if alive_links > 0 else 0.0
        stats["budget"] = budget

        # ── COMPRESSION CHECK ──
        if (self.compression_enabled
                and window_count == self.compress_at_window
                and not self.macro_nodes):
            n_compressed = self.compress_stable_labels(state, window_count)
            stats["macro_nodes_active"] = len(self.macro_nodes)
            stats["compressed_links_removed"] = len(self.removed_links)

        # ── 1. SEED ──
        cluster_list = []
        if islands:
            for iid, info in islands.items():
                nodes = frozenset(info.nodes)
                if len(nodes) >= 2:
                    # Don't seed labels from compressed nodes
                    if not (nodes & self.compressed_nodes):
                        cluster_list.append(nodes)
                    self.recurrence[nodes] = \
                        self.recurrence.get(nodes, 0) + 1

        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                pair = frozenset(lk)
                if not (pair & self.compressed_nodes):
                    if pair not in self.recurrence:
                        cluster_list.append(pair)
                self.recurrence[pair] = \
                    self.recurrence.get(pair, 0) + 1

        current_clusters = set()
        if islands:
            for info in islands.values():
                if len(info.nodes) >= 2:
                    current_clusters.add(frozenset(info.nodes))
        for lk in state.alive_l:
            if state.R.get(lk, 0.0) > 0:
                current_clusters.add(frozenset(lk))
        stale = [k for k, v in self.recurrence.items()
                 if k not in current_clusters and v < 2]
        for k in stale:
            del self.recurrence[k]

        stats["motifs_detected"] = len(cluster_list)

        # Birth labels (exclude already-compressed labels)
        born_this_window = []
        for cluster_nodes in cluster_list:
            already_labeled = False
            for label in self.labels.values():
                overlap = label["nodes"] & cluster_nodes
                if len(overlap) > len(cluster_nodes) * 0.5:
                    already_labeled = True
                    break
            if already_labeled:
                continue

            thetas = [float(state.theta[n]) for n in cluster_nodes
                      if n in state.alive_n]
            if not thetas:
                continue
            phase_sig = math.atan2(
                sum(math.sin(t) for t in thetas) / len(thetas),
                sum(math.cos(t) for t in thetas) / len(thetas))

            lid = self.next_label_id
            self.labels[lid] = {
                "nodes": frozenset(cluster_nodes),
                "phase_sig": phase_sig,
                "share": 0.0,
                "born": window_count,
                "prev_alignment": 0.0,
            }
            self.next_label_id += 1
            stats["labels_born"] += 1
            born_this_window.append(lid)

        if not self.labels and not self.macro_nodes:
            stats["labels_active"] = 0
            self.stats = stats
            return stats
        if budget == 0:
            stats["labels_active"] = len(self.labels)
            self.stats = stats
            return stats

        # ── 2. INFLUENCE ──
        node_owner = {}

        # Regular labels
        for lid, label in self.labels.items():
            if lid in self.macro_nodes:
                continue  # handled separately
            alignments = []
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                alignment = math.cos(theta_n - label["phase_sig"])
                alignments.append((n, alignment))

            if alignments:
                mean_align = sum(a for _, a in alignments) / len(alignments)
            else:
                mean_align = 0.0
            label["prev_alignment"] = mean_align

            influence = max(0.0, mean_align)
            for n, _ in alignments:
                existing = node_owner.get(n)
                if existing is None or influence > existing[1]:
                    node_owner[n] = (lid, influence)

        # MacroNodes: they own their nodes unconditionally
        for mn_id, mn in self.macro_nodes.items():
            for n in mn.node_ids:
                if n in state.alive_n:
                    node_owner[n] = (mn_id, 1.0)

        # Count links per label
        label_link_count = defaultdict(int)
        for lk in state.alive_l:
            n1, n2 = lk
            owner1 = node_owner.get(n1)
            owner2 = node_owner.get(n2)
            if owner1:
                label_link_count[owner1[0]] += 1
            if owner2 and (not owner1 or owner2[0] != owner1[0]):
                label_link_count[owner2[0]] += 1

        # ── 3. ALLOCATE ──
        # Regular labels: share from physical link count
        # MacroNodes: share from frozen baseline (last observed
        # territory_links before compression). No formula, no
        # constants. Constitution §3 compliant.
        total_influence = sum(label_link_count.values())

        for mn_id, mn in self.macro_nodes.items():
            label_link_count[mn_id] = mn.territory_at_compression
            total_influence += mn.territory_at_compression

        if total_influence == 0:
            total_influence = 1

        for lid, label in self.labels.items():
            if lid not in self.macro_nodes:
                label["share"] = label_link_count.get(lid, 0) / total_influence
        # Build degree map once for all macro-nodes (O(links))
        _deg_map = self._build_degree_map(state) if self.macro_nodes else {}

        for mn_id, mn in self.macro_nodes.items():
            mn.share = label_link_count.get(mn_id, 0) / total_influence
            mn.h_age += 1
            self._compute_perimeter_omega(mn, state, substrate, _deg_map)
            # Update nearest_dist
            min_dist = math.pi
            for other_id in self.labels:
                if other_id == mn_id:
                    continue
                other = self.labels[other_id]
                d = abs(mn.phase_core_theta - other["phase_sig"])
                if d > math.pi:
                    d = 2 * math.pi - d
                if d < min_dist:
                    min_dist = d
            for other_mn_id, other_mn in self.macro_nodes.items():
                if other_mn_id == mn_id:
                    continue
                d = abs(mn.phase_core_theta - other_mn.phase_core_theta)
                if d > math.pi:
                    d = 2 * math.pi - d
                if d < min_dist:
                    min_dist = d
            mn.nearest_dist = min_dist

        # ── 4. TORQUE ──
        node_torques = {}
        label_torque_applied = defaultdict(float)

        # Regular labels
        for lid, label in self.labels.items():
            if lid in self.macro_nodes:
                continue
            energy = budget * label["share"]
            if energy < 0.0001:
                continue
            torque_mag = energy
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_mag * math.sin(
                    label["phase_sig"] - theta_n)
                existing = node_torques.get(n)
                if existing is None or energy > existing[1]:
                    node_torques[n] = (torque, energy, lid)
                    label_torque_applied[lid] += abs(torque)

            if substrate:
                grav_mag = torque_mag / max(1, len(label["nodes"]))
                for n in label["nodes"]:
                    for nb in substrate.get(n, set()):
                        if nb not in state.alive_n:
                            continue
                        if nb in label["nodes"]:
                            continue
                        theta_nb = float(state.theta[nb])
                        grav_torque = grav_mag * math.sin(
                            label["phase_sig"] - theta_nb)
                        existing = node_torques.get(nb)
                        if existing is None or energy > existing[1]:
                            node_torques[nb] = (grav_torque, energy, lid)
                            label_torque_applied[lid] += abs(grav_torque)

        # MacroNode torque (Level 2: formula-based)
        for mn_id, mn in self.macro_nodes.items():
            self._macro_node_torque(mn, state, node_torques)
            label_torque_applied[mn_id] = mn.share  # simplified

        # Apply torque
        for n, (torque, _, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        # ── v3: LOG ALIVE + BIRTH ──
        for lid, label in self.labels.items():
            if lid in self.macro_nodes:
                continue
            t_links, t_rplus, t_S_mean = self._territory_stats(
                lid, label, state, node_torques)
            nearest = self._nearest_label_dist(lid, label)
            n_neighbors = self._n_phase_neighbors(lid, label)

            thetas = [float(state.theta[n]) for n in label["nodes"]
                      if n in state.alive_n]
            if len(thetas) >= 2:
                sin_sum = sum(math.sin(t) for t in thetas)
                cos_sum = sum(math.cos(t) for t in thetas)
                theta_coherence = math.sqrt(sin_sum**2 + cos_sum**2) / len(thetas)
            else:
                theta_coherence = 0.0

            event = "birth" if lid in born_this_window else "alive"
            self.lifecycle_log.append({
                "label_id": lid, "window": window_count,
                "event": event,
                "nodes": len(label["nodes"]),
                "share": round(label["share"], 6),
                "alignment": round(label["prev_alignment"], 4),
                "torque_applied": round(label_torque_applied.get(lid, 0), 6),
                "territory_links": t_links,
                "territory_rplus": t_rplus,
                "territory_S_mean": round(t_S_mean, 4),
                "phase_sig": round(label["phase_sig"], 4),
                "nearest_label_dist": round(nearest, 4),
                "n_phase_neighbors": n_neighbors,
                "theta_coherence": round(theta_coherence, 4),
            })

        # Log macro-nodes
        for mn_id, mn in self.macro_nodes.items():
            self.lifecycle_log.append({
                "label_id": mn_id, "window": window_count,
                "event": "macro_alive",
                "nodes": mn.size_class_N,
                "share": round(mn.share, 6),
                "h_age": mn.h_age,
                "local_stress_omega": round(mn.local_stress_omega, 4),
                "nearest_dist": round(mn.nearest_dist, 4),
                "phase_sig": round(mn.phase_core_theta, 4),
            })

        # ── 5. CULL ──
        total_entities = len(self.labels) + len(self.macro_nodes)
        # Don't double-count labels that are also macro-nodes
        total_entities = len([l for l in self.labels if l not in self.macro_nodes]) + len(self.macro_nodes)
        fair_share = 1.0 / max(1, total_entities)
        death_threshold = fair_share * 0.5

        dead_labels = [lid for lid, label in self.labels.items()
                       if lid not in self.macro_nodes
                       and label["share"] < death_threshold]

        five_node_deaths = 0
        for lid in dead_labels:
            label = self.labels[lid]
            if len(label["nodes"]) == 5:
                five_node_deaths += 1
            t_links, t_rplus, t_S_mean = self._territory_stats(
                lid, label, state, node_torques)
            nearest = self._nearest_label_dist(lid, label)
            n_neighbors = self._n_phase_neighbors(lid, label)
            thetas_d = [float(state.theta[n]) for n in label["nodes"]
                        if n in state.alive_n]
            if len(thetas_d) >= 2:
                sin_s = sum(math.sin(t) for t in thetas_d)
                cos_s = sum(math.cos(t) for t in thetas_d)
                theta_coh_d = math.sqrt(sin_s**2 + cos_s**2) / len(thetas_d)
            else:
                theta_coh_d = 0.0
            self.lifecycle_log.append({
                "label_id": lid, "window": window_count,
                "event": "death",
                "nodes": len(label["nodes"]),
                "share": round(label["share"], 6),
                "alignment": round(label["prev_alignment"], 4),
                "torque_applied": round(label_torque_applied.get(lid, 0), 6),
                "territory_links": t_links,
                "territory_rplus": t_rplus,
                "territory_S_mean": round(t_S_mean, 4),
                "phase_sig": round(label["phase_sig"], 4),
                "nearest_label_dist": round(nearest, 4),
                "n_phase_neighbors": n_neighbors,
                "theta_coherence": round(theta_coh_d, 4),
                "death_cause": "cull",
                "share_at_death": round(label["share"], 6),
                "age_at_death": window_count - label["born"],
            })
            del self.labels[lid]
            stats["labels_died"] += 1

        # Macro-node cull (same threshold)
        dead_macros = [mn_id for mn_id, mn in self.macro_nodes.items()
                       if mn.share < death_threshold]
        for mn_id in dead_macros:
            mn = self.macro_nodes[mn_id]
            self.lifecycle_log.append({
                "label_id": mn_id, "window": window_count,
                "event": "macro_death",
                "nodes": mn.size_class_N,
                "share": round(mn.share, 6),
                "h_age": mn.h_age,
                "death_cause": "cull",
            })
            # Release compressed nodes — restore to alive_n
            for n in mn.node_ids:
                self.compressed_nodes.discard(n)
                state.alive_n.add(n)  # re-enter physics
            del self.macro_nodes[mn_id]
            if mn_id in self.labels:
                del self.labels[mn_id]
            stats["labels_died"] += 1

        # ── 6. METRICS ──
        active_labels = len([l for l in self.labels if l not in self.macro_nodes])
        stats["labels_active"] = active_labels + len(self.macro_nodes)
        stats["macro_nodes_active"] = len(self.macro_nodes)

        if self.labels or self.macro_nodes:
            all_shares = []
            for lid, lb in self.labels.items():
                if lid not in self.macro_nodes:
                    all_shares.append(lb["share"])
            for mn in self.macro_nodes.values():
                all_shares.append(mn.share)

            if all_shares:
                stats["top_share"] = round(max(all_shares), 4)
                ages = []
                for lid, lb in self.labels.items():
                    if lid not in self.macro_nodes:
                        ages.append(window_count - lb["born"])
                for mn in self.macro_nodes.values():
                    ages.append(mn.h_age + (mn.compressed_at - mn.born_window))
                if ages:
                    stats["v_oldest_age"] = max(ages)
                    stats["v_mean_age"] = round(sum(ages)/len(ages), 1)

                five_node = [lb for lid, lb in self.labels.items()
                             if lid not in self.macro_nodes
                             and len(lb["nodes"]) == 5]
                five_mn = [mn for mn in self.macro_nodes.values()
                           if mn.size_class_N == 5]
                all_5 = five_node + [{"share": mn.share} for mn in five_mn]
                if all_5:
                    stats["v_mean_share_5node"] = round(
                        sum(x["share"] for x in all_5)/len(all_5), 4)
                    stats["v_births_5node"] = sum(
                        1 for lid in born_this_window
                        if lid in self.labels and len(self.labels[lid]["nodes"]) == 5)
                else:
                    stats["v_mean_share_5node"] = 0.0
                    stats["v_births_5node"] = 0

                stats["v_share_std"] = round(
                    (sum((s - sum(all_shares)/len(all_shares))**2
                         for s in all_shares)/len(all_shares))**0.5, 4)
                stats["v_deaths_5node"] = five_node_deaths

        if stats["torque_events"] > 0:
            stats["torque_total"] = round(stats["torque_total"], 4)
            stats["mean_torque"] = round(
                stats["torque_total"] / stats["torque_events"], 6)

        # Label territory R+ rate
        label_nodes = set()
        for lid, label in self.labels.items():
            if lid not in self.macro_nodes:
                for n in label["nodes"]:
                    label_nodes.add(n)
        for mn in self.macro_nodes.values():
            for n in mn.node_ids:
                label_nodes.add(n)

        label_rplus = 0; label_total = 0
        other_rplus = 0; other_total = 0
        for lk in state.alive_l:
            n1, n2 = lk
            r = state.R.get(lk, 0.0)
            if n1 in label_nodes or n2 in label_nodes:
                label_total += 1
                if r > 0: label_rplus += 1
            else:
                other_total += 1
                if r > 0: other_rplus += 1
        if label_total > 0 and other_total > 0:
            rate_label = label_rplus / label_total
            rate_other = other_rplus / other_total
            stats["label_rplus_rate"] = round(
                rate_label / max(0.001, rate_other), 4)

        # Prune recurrence
        if len(self.recurrence) > 1000:
            sorted_rec = sorted(self.recurrence.items(), key=lambda x: x[1])
            for k, _ in sorted_rec[:len(self.recurrence)-1000]:
                del self.recurrence[k]

        self.stats = stats
        return stats

    def summary(self):
        total_shares = {}
        for lid, lb in self.labels.items():
            if lid not in self.macro_nodes:
                total_shares[lid] = lb["share"]
        for mn_id, mn in self.macro_nodes.items():
            total_shares[mn_id] = mn.share

        label_details = []
        for lid, label in sorted(self.labels.items(),
                                  key=lambda x: x[1]["share"], reverse=True)[:30]:
            if lid in self.macro_nodes:
                continue
            label_details.append({
                "id": lid, "nodes": len(label["nodes"]),
                "share": round(label["share"], 6),
                "born": label["born"],
                "phase_sig": round(label["phase_sig"], 4),
                "alignment": round(label.get("prev_alignment", 0), 4),
            })

        macro_details = [mn.to_dict() for mn in
                         sorted(self.macro_nodes.values(),
                                key=lambda x: x.share, reverse=True)]

        return {
            "budget": 1.0,
            "labels_active": len(self.labels) - len(self.macro_nodes),
            "macro_nodes_active": len(self.macro_nodes),
            "share_distribution": sorted(total_shares.values(), reverse=True)[:20],
            "label_details": label_details,
            "macro_node_details": macro_details,
            "lifecycle_log_size": len(self.lifecycle_log),
        }
