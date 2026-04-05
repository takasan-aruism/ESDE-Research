#!/usr/bin/env python3
"""
ESDE Virtual Layer v9 — Self-Referential Feedback Loop (Phase 1)
=================================================================
Based on virtual_layer_v5. Changes:
  - Global turnover signal: died labels' share sum → EMA → ratio
  - Weak torque modulation: torque_mag *= M
  - M = 1 + gamma * (ratio - 1), clamped [0.8, 1.2]
  - Warmup: first 20 windows M=1.0 (EMA accumulates only)
  - No change to birth/death/share/cull logic

Level 1: Physical layer (V43, frozen). Does not know labels.
Level 2: THIS FILE. v5 + global feedback loop.
Level 3: Ontology (future). Built on top of Level 2.

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

    N_BINS = 64
    BIN_WIDTH = 2 * math.pi / 64  # ≈ 0.098 rad ≈ 5.6°

    def __init__(self, compression_enabled=False, compress_at_window=50,
                 compress_min_age=10,
                 maturation_alpha=0.10, rigidity_beta=0.10,
                 feedback_gamma=0.10, feedback_clamp=(0.8, 1.2)):
        self.recurrence = {}
        self.labels = {}
        self.next_label_id = 0
        self.stats = {}
        self.lifecycle_log = []

        # Compression config
        self.compression_enabled = compression_enabled
        self.compress_at_window = compress_at_window
        self.compress_min_age = compress_min_age

        # Phase B: maturation + rigidity (v4.9 history tensor → label)
        # α from 48-seed Phase A: age 1-5 → 20-40 = 8.3× survival increase
        # β from 48-seed Phase A: alignment 0.77 → 0.20 over 50 windows
        # Both derived from observation, not designed.
        self.maturation_alpha = maturation_alpha
        self.rigidity_beta = rigidity_beta

        # Macro-node registry
        self.macro_nodes = {}        # {label_id: MacroNode}
        self.compressed_nodes = set() # set of node IDs under compression
        self.removed_links = set()    # internal links removed at compression

        # Phase space observation (v8.2 Phase A)
        # O = occupancy (current), H = history (cumulative), V = vacancy
        # These are OBSERVATION ONLY. They do not affect any logic.
        # V is a vacancy proxy, not "the future" itself.
        self.occupancy = [0.0] * self.N_BINS   # O[b]
        self.history = [0.0] * self.N_BINS     # H[b]
        self.vacancy = [0.0] * self.N_BINS     # V[b]
        self.phase_snapshots = []  # per-window O/H snapshots for JSON

        # ── v9: Global feedback loop ──
        self.turnover_ema = None       # EMA of died labels' share sum
        self.feedback_gamma = feedback_gamma   # modulation sensitivity
        self.feedback_clamp = feedback_clamp   # M clamp range (lo, hi)
        self.warmup_windows = 20       # M=1.0 during warmup
        self._torque_multiplier = 1.0  # current M (applied to torque)
        self.semantic_gravity_enabled = True  # v9.2: ON/OFF for audit
        # v9.3: Per-label deviation detection + local response
        self._prev_territory = {}     # {lid: territory_links} for window-level D2
        self._prev_label_links = {}   # {lid: local_link_sum} for step-level response
        self._gravity_factors = {}    # {lid: 0.0-1.0} persisted from step() for apply_torque_only()
        self._deviation_log = []      # per-window deviation records
        self.torque_order = "random"  # "random" / "share" / "age"
        self.deviation_enabled = True  # v9.3: deviation detection ON/OFF

    def _phase_bin(self, theta):
        """Map theta to bin index [0, N_BINS)."""
        t = theta % (2 * math.pi)
        b = int(t / self.BIN_WIDTH)
        return min(b, self.N_BINS - 1)  # clamp

    def _update_phase_space(self, window_count):
        """Update O, H, V from current label positions. OBSERVATION ONLY."""
        o = [0.0] * self.N_BINS

        # Regular labels
        for lid, label in self.labels.items():
            if lid in self.macro_nodes:
                continue
            b = self._phase_bin(label["phase_sig"])
            o[b] += label["share"]

        # Macro-nodes
        for mn in self.macro_nodes.values():
            b = self._phase_bin(mn.phase_core_theta)
            o[b] += mn.share

        self.occupancy = o

        # History: cumulative (no decay)
        for b in range(self.N_BINS):
            self.history[b] += o[b]

        # Vacancy: relative emptiness
        max_o = max(o) if o else 0.0
        if max_o > 0:
            self.vacancy = [1.0 - o[b] / max_o for b in range(self.N_BINS)]
        else:
            self.vacancy = [1.0] * self.N_BINS

        # Snapshot for JSON
        self.phase_snapshots.append({
            "window": window_count,
            "O": [round(v, 6) for v in o],
            "H": [round(v, 4) for v in self.history],
        })

    def _phase_space_stats(self):
        """Compute summary stats for CSV. OBSERVATION ONLY."""
        o = self.occupancy
        h = self.history
        v = self.vacancy

        occ_max = max(o) if o else 0.0
        occ_mean = sum(o) / len(o) if o else 0.0
        occ_nonzero = sum(1 for x in o if x > 0.001)
        vacancy_mean = sum(v) / len(v) if v else 0.0
        history_max = max(h) if h else 0.0

        # Gini coefficient of H
        h_sorted = sorted(h)
        n = len(h_sorted)
        if n > 0 and sum(h_sorted) > 0:
            cum = 0.0
            gini_sum = 0.0
            total = sum(h_sorted)
            for i, val in enumerate(h_sorted):
                cum += val
                gini_sum += (2 * (i + 1) - n - 1) * val
            history_gini = gini_sum / (n * total)
        else:
            history_gini = 0.0

        return {
            "occ_max": round(occ_max, 6),
            "occ_mean": round(occ_mean, 6),
            "occ_nonzero": occ_nonzero,
            "vacancy_mean": round(vacancy_mean, 4),
            "history_max": round(history_max, 4),
            "history_gini": round(history_gini, 4),
        }

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

            # Nodes STAY in alive_n. They participate in all physics.
            # Only internal links are removed. This makes macro-node
            # a "fast label" (no internal cost) not a "strong label"
            # (immune to physics). Territory changes with physical
            # fluctuations. Share is earned, not guaranteed.

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
        Compressed nodes are not in alive_n but still have theta.
        Same rigidity rule as regular labels — macro-node is a
        'fast label', not a privileged one."""
        energy = mn.share
        if energy < 0.0001:
            return
        # Rigidity: same formula as regular labels
        mn_age = mn.h_age + (mn.compressed_at - mn.born_window)
        rigidity_factor = 1.0 / (1.0 + self.rigidity_beta * mn_age)
        torque_mag = energy * rigidity_factor * self._torque_multiplier
        for n in mn.node_ids:
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
    def apply_torque_only(self, state, window_count, substrate=None):
        """Apply torque without birth/share/cull. For sub-window feedback.
        v9.3+: Sequential application with deviation-based gravity_factors.
        Returns number of torque events applied.
        """
        alive_links = len(state.alive_l)
        if alive_links == 0 or not self.labels:
            return 0

        import random as _rnd
        label_ids = [lid for lid in self.labels if lid not in self.macro_nodes]
        if self.torque_order == "share":
            label_ids.sort(key=lambda lid: self.labels[lid]["share"], reverse=True)
        elif self.torque_order == "age":
            label_ids.sort(key=lambda lid: self.labels[lid]["born"])
        else:  # "random"
            _seq_rng = _rnd.Random(window_count * 1000 + len(self.labels))
            _seq_rng.shuffle(label_ids)

        budget = 1.0
        events = 0

        for lid in label_ids:
            label = self.labels[lid]
            energy = budget * label["share"]
            if energy < 0.0001:
                continue

            age = window_count - label["born"]
            rigidity_factor = 1.0 / (1.0 + self.rigidity_beta * age)
            torque_mag = energy * rigidity_factor * self._torque_multiplier

            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_mag * math.sin(
                    label["phase_sig"] - theta_n)
                state.theta[n] += torque
                events += 1

            if substrate and self.semantic_gravity_enabled:
                # Use persisted gravity_factors from last step()
                gf = self._gravity_factors.get(lid, 1.0)
                grav_mag = torque_mag / max(1, len(label["nodes"])) * gf
                for n in label["nodes"]:
                    for nb in substrate.get(n, set()):
                        if nb not in state.alive_n:
                            continue
                        if nb in label["nodes"]:
                            continue
                        theta_nb = float(state.theta[nb])
                        grav_torque = grav_mag * math.sin(
                            label["phase_sig"] - theta_nb)
                        state.theta[nb] += grav_torque
                        events += 1

        # MacroNode torque
        for mn_id, mn in self.macro_nodes.items():
            node_torques_mn = {}
            self._macro_node_torque(mn, state, node_torques_mn)
            for n, (torque, _, _) in node_torques_mn.items():
                state.theta[n] += torque
                events += 1

        return events

    def step(self, state, window_count, islands=None, substrate=None):
        stats = {
            "budget": 0.0, "labels_active": 0,
            "labels_born": 0, "labels_died": 0,
            "torque_events": 0, "torque_total": 0.0,
            "motifs_detected": 0, "mean_torque": 0.0,
            "top_share": 0.0, "label_rplus_rate": 0.0,
            "macro_nodes_active": len(self.macro_nodes),
            "compressed_links_removed": len(self.removed_links),
            # v9 feedback defaults
            "died_share_sum": 0.0, "turnover_ema": 0.0,
            "signal_ratio": 0.0, "torque_multiplier": 1.0,
            "warmup_active": 1, "feedback_gamma": self.feedback_gamma,
            # v9.3 deviation detection
            "dev_mean_score": 0.0, "dev_max_score": 0.0,
            "dev_n_responding": 0, "dev_mean_gf": 1.0,
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
        # All labels (including macro-nodes) get share from physical
        # link count. Macro-nodes are "fast labels" — same rules,
        # just no internal links. Their share rises and falls with
        # the physical layer, like everyone else.
        total_influence = sum(label_link_count.values())

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

        # ── 4a. DEVIATION DETECTION (v9.3) ──
        # Per-label deviation score: phase_drift + link_loss + torque_exposure
        # Score drives local gravity modulation (Phase B response)
        deviation_scores = {}
        gravity_factors = {}  # {lid: 0.0-1.0} for semantic gravity

        if self.deviation_enabled:
            for lid, label in self.labels.items():
                if lid in self.macro_nodes:
                    continue

                # D1: Phase drift — |current θ mean - stored phase_sig|
                thetas = [float(state.theta[n]) for n in label["nodes"]
                          if n in state.alive_n]
                if len(thetas) >= 2:
                    sin_s = sum(math.sin(t) for t in thetas)
                    cos_s = sum(math.cos(t) for t in thetas)
                    mean_theta = math.atan2(sin_s, cos_s)
                    phase_drift = abs(mean_theta - label["phase_sig"])
                    if phase_drift > math.pi:
                        phase_drift = 2 * math.pi - phase_drift
                else:
                    phase_drift = 0.0

                # D2: Link loss — territory_links drop from last window
                current_terr = label_link_count.get(lid, 0)
                prev_terr = self._prev_territory.get(lid, current_terr)
                link_loss = max(0, prev_terr - current_terr) / max(1, prev_terr)

                # D3: Torque exposure — how much torque was applied last window
                torque_exposure = label.get("_last_torque_applied", 0.0)

                # Combined deviation score (0-1 each, weighted sum)
                score = (0.5 * min(phase_drift / math.pi, 1.0)
                         + 0.3 * link_loss
                         + 0.2 * min(torque_exposure * 100, 1.0))

                deviation_scores[lid] = {
                    "phase_drift": round(phase_drift, 4),
                    "link_loss": round(link_loss, 4),
                    "torque_exposure": round(torque_exposure, 6),
                    "score": round(score, 4),
                }

                gravity_factors[lid] = max(0.0, 1.0 - score)
        else:
            # Deviation OFF: all gravity_factors = 1.0
            for lid in self.labels:
                if lid not in self.macro_nodes:
                    gravity_factors[lid] = 1.0

        # Persist gravity_factors for apply_torque_only()
        self._gravity_factors = gravity_factors

        # Update prev_territory for next window
        self._prev_territory = {lid: label_link_count.get(lid, 0)
                                for lid in self.labels
                                if lid not in self.macro_nodes}

        # ── 4b. TORQUE (v9.3+: sequential application) ──
        # Each label computes torque on CURRENT theta, applies IMMEDIATELY.
        # Next label sees the updated theta. No batch buffering.
        import random as _rnd
        label_ids = [lid for lid in self.labels if lid not in self.macro_nodes]
        if self.torque_order == "share":
            label_ids.sort(key=lambda lid: self.labels[lid]["share"], reverse=True)
        elif self.torque_order == "age":
            label_ids.sort(key=lambda lid: self.labels[lid]["born"])
        else:  # "random"
            _seq_rng = _rnd.Random(window_count)
            _seq_rng.shuffle(label_ids)

        node_torques = {}  # record of last torque applied (for logging)
        label_torque_applied = defaultdict(float)

        for lid in label_ids:
            label = self.labels[lid]
            energy = budget * label["share"]
            if energy < 0.0001:
                continue

            age = window_count - label["born"]
            rigidity_factor = 1.0 / (1.0 + self.rigidity_beta * age)
            torque_mag = energy * rigidity_factor * self._torque_multiplier

            # Core torque: compute and apply IMMEDIATELY
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_mag * math.sin(
                    label["phase_sig"] - theta_n)
                state.theta[n] += torque
                node_torques[n] = (torque, energy, lid)
                label_torque_applied[lid] += abs(torque)
                stats["torque_events"] += 1
                stats["torque_total"] += abs(torque)

            # Semantic gravity: compute and apply IMMEDIATELY
            if substrate and self.semantic_gravity_enabled:
                gf = gravity_factors.get(lid, 1.0)
                grav_mag = torque_mag / max(1, len(label["nodes"])) * gf
                for n in label["nodes"]:
                    for nb in substrate.get(n, set()):
                        if nb not in state.alive_n:
                            continue
                        if nb in label["nodes"]:
                            continue
                        theta_nb = float(state.theta[nb])
                        grav_torque = grav_mag * math.sin(
                            label["phase_sig"] - theta_nb)
                        state.theta[nb] += grav_torque
                        node_torques[nb] = (grav_torque, energy, lid)
                        label_torque_applied[lid] += abs(grav_torque)
                        stats["torque_events"] += 1
                        stats["torque_total"] += abs(grav_torque)

        # MacroNode torque (Level 2: formula-based, still batch)
        for mn_id, mn in self.macro_nodes.items():
            self._macro_node_torque(mn, state, node_torques)
            label_torque_applied[mn_id] = mn.share

        # ── v9.3: Store torque_applied per label for next window's D3 ──
        for lid, label in self.labels.items():
            if lid not in self.macro_nodes:
                label["_last_torque_applied"] = label_torque_applied.get(lid, 0.0)

        # ── v9.3: Deviation log (Phase C: record) ──
        if deviation_scores:
            scores = [d["score"] for d in deviation_scores.values()]
            gfs = [gravity_factors.get(lid, 1.0) for lid in deviation_scores]
            n_responding = sum(1 for gf in gfs if gf < 0.95)
            dev_summary = {
                "window": window_count,
                "mean_score": round(sum(scores) / len(scores), 4),
                "max_score": round(max(scores), 4),
                "n_labels": len(scores),
                "n_responding": n_responding,
                "mean_gravity_factor": round(sum(gfs) / len(gfs), 4),
            }
            self._deviation_log.append(dev_summary)
            stats["dev_mean_score"] = dev_summary["mean_score"]
            stats["dev_max_score"] = dev_summary["max_score"]
            stats["dev_n_responding"] = n_responding
            stats["dev_mean_gf"] = dev_summary["mean_gravity_factor"]

        # ── v8.2 Phase A: Update phase space observation ──
        self._update_phase_space(window_count)

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

            # Phase space bin info (observation only)
            b = self._phase_bin(label["phase_sig"])

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
                "bin_id": b,
                "bin_occupancy": round(self.occupancy[b], 6),
                "bin_vacancy": round(self.vacancy[b], 4),
                "bin_history": round(self.history[b], 4),
            })

        # Log macro-nodes
        for mn_id, mn in self.macro_nodes.items():
            b = self._phase_bin(mn.phase_core_theta)
            self.lifecycle_log.append({
                "label_id": mn_id, "window": window_count,
                "event": "macro_alive",
                "nodes": mn.size_class_N,
                "share": round(mn.share, 6),
                "h_age": mn.h_age,
                "local_stress_omega": round(mn.local_stress_omega, 4),
                "nearest_dist": round(mn.nearest_dist, 4),
                "phase_sig": round(mn.phase_core_theta, 4),
                "bin_id": b,
                "bin_occupancy": round(self.occupancy[b], 6),
                "bin_vacancy": round(self.vacancy[b], 4),
                "bin_history": round(self.history[b], 4),
            })

        # ── 5. CULL ──
        total_entities = len(self.labels) + len(self.macro_nodes)
        # Don't double-count labels that are also macro-nodes
        total_entities = len([l for l in self.labels if l not in self.macro_nodes]) + len(self.macro_nodes)
        fair_share = 1.0 / max(1, total_entities)
        base_threshold = fair_share * 0.5

        # Phase B: Maturation (v4.9 h_age → label version)
        # Older labels tolerate lower share before dying.
        # threshold_i = base / (1 + α × age)
        # age=0: threshold = base (young labels die easily)
        # age=20: threshold = base/3 (mature labels are resilient)
        dead_labels = []
        for lid, label in self.labels.items():
            if lid in self.macro_nodes:
                continue
            age = window_count - label["born"]
            threshold_i = base_threshold / (1.0 + self.maturation_alpha * age)
            if label["share"] < threshold_i:
                dead_labels.append(lid)

        # ── v9: Global feedback — collect died share BEFORE deletion ──
        died_share_sum = sum(self.labels[lid]["share"]
                            for lid in dead_labels if lid in self.labels)

        # EMA update
        if self.turnover_ema is None:
            self.turnover_ema = died_share_sum
        tau = min(window_count, 20)
        alpha_ema = 2.0 / (tau + 1.0)
        self.turnover_ema = (alpha_ema * died_share_sum
                             + (1 - alpha_ema) * self.turnover_ema)

        # Signal ratio
        signal_ratio = died_share_sum / max(1e-6, self.turnover_ema)

        # Torque multiplier for NEXT window
        if window_count < self.warmup_windows:
            # Warmup: M=1.0, EMA accumulates only
            self._torque_multiplier = 1.0
        else:
            M_raw = 1.0 + self.feedback_gamma * (signal_ratio - 1.0)
            lo, hi = self.feedback_clamp
            self._torque_multiplier = max(lo, min(hi, M_raw))
        # ── end v9 feedback ──

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

        # Macro-node cull (same maturation rule)
        dead_macros = []
        for mn_id, mn in self.macro_nodes.items():
            mn_age = mn.h_age + (mn.compressed_at - mn.born_window)
            mn_threshold = base_threshold / (1.0 + self.maturation_alpha * mn_age)
            if mn.share < mn_threshold:
                dead_macros.append(mn_id)
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
            # Release compressed node tracking
            for n in mn.node_ids:
                self.compressed_nodes.discard(n)
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

        # Phase space stats (observation only)
        stats.update(self._phase_space_stats())

        # ── v9: Feedback stats ──
        stats["died_share_sum"] = round(died_share_sum, 6)
        stats["turnover_ema"] = round(self.turnover_ema, 6) if self.turnover_ema else 0
        stats["signal_ratio"] = round(signal_ratio, 4)
        stats["torque_multiplier"] = round(self._torque_multiplier, 4)
        stats["warmup_active"] = 1 if window_count < self.warmup_windows else 0
        stats["feedback_gamma"] = self.feedback_gamma

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
            "phase_space_snapshots": self.phase_snapshots,
        }
