#!/usr/bin/env python3
"""
ESDE Virtual Layer v3 — 代謝モデル + Lifecycle Logging
========================================================
v2 と同一ロジック。変更なし。
追加: per-label lifecycle log (birth/alive/death 全記録)

「点を打ち続ける。関係性が見えたら数式化。仮説は不十分。」
"""

import math
from collections import defaultdict


class VirtualLayer:

    def __init__(self):
        self.recurrence = {}
        self.labels = {}
        self.next_label_id = 0
        self.stats = {}
        self.lifecycle_log = []  # v3: per-label per-window log

    def _territory_stats(self, lid, label, state, node_torques):
        """Compute territory statistics for a label. O(alive_l) single pass."""
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
        """Phase distance to nearest other label."""
        min_dist = math.pi  # max possible
        for other_id, other in self.labels.items():
            if other_id == lid:
                continue
            d = abs(label["phase_sig"] - other["phase_sig"])
            if d > math.pi:
                d = 2 * math.pi - d  # wrap around
            if d < min_dist:
                min_dist = d
        return min_dist

    def _n_phase_neighbors(self, lid, label, threshold=0.3):
        """Count labels within threshold radians."""
        count = 0
        for other_id, other in self.labels.items():
            if other_id == lid:
                continue
            d = abs(label["phase_sig"] - other["phase_sig"])
            if d > math.pi:
                d = 2 * math.pi - d
            if d < threshold:
                count += 1
        return count

    def step(self, state, window_count, islands=None, substrate=None):
        stats = {
            "budget": 0.0,
            "labels_active": 0,
            "labels_born": 0,
            "labels_died": 0,
            "torque_events": 0,
            "torque_total": 0.0,
            "motifs_detected": 0,
            "mean_torque": 0.0,
            "top_share": 0.0,
            "label_rplus_rate": 0.0,
        }

        alive_links = len(state.alive_l)
        budget = 1.0 if alive_links > 0 else 0.0
        stats["budget"] = budget

        # ── 1. SEED ──
        cluster_list = []
        if islands:
            for iid, info in islands.items():
                nodes = frozenset(info.nodes)
                if len(nodes) >= 2:
                    cluster_list.append(nodes)
                    self.recurrence[nodes] = \
                        self.recurrence.get(nodes, 0) + 1

        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                pair = frozenset(lk)
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

        # Birth labels
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

        if not self.labels or budget == 0:
            stats["labels_active"] = len(self.labels)
            self.stats = stats
            return stats

        # ── 2. INFLUENCE ──
        node_owner = {}

        for lid, label in self.labels.items():
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
        total_influence = sum(label_link_count.values())
        if total_influence == 0:
            total_influence = 1

        for lid, label in self.labels.items():
            label["share"] = label_link_count.get(lid, 0) / total_influence

        # ── 4. TORQUE ──
        node_torques = {}
        label_torque_applied = defaultdict(float)  # v3: track per-label

        for lid, label in self.labels.items():
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

        for n, (torque, _, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        # ── v3: LOG ALIVE + BIRTH for all current labels ──
        for lid, label in self.labels.items():
            t_links, t_rplus, t_S_mean = self._territory_stats(
                lid, label, state, node_torques)
            nearest = self._nearest_label_dist(lid, label)
            n_neighbors = self._n_phase_neighbors(lid, label)

            # Cognitive binding measure: θ coherence of label nodes
            # R = mean resultant length of θ. R=1: perfectly aligned. R≈0: random.
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
                "label_id": lid,
                "window": window_count,
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

        # ── 5. CULL ──
        label_count = len(self.labels)
        fair_share = 1.0 / max(1, label_count)
        death_threshold = fair_share * 0.5

        dead_labels = [lid for lid, label in self.labels.items()
                       if label["share"] < death_threshold]

        # v3: log death events BEFORE deletion, with real territory stats
        five_node_deaths = 0
        for lid in dead_labels:
            label = self.labels[lid]
            if len(label["nodes"]) == 5:
                five_node_deaths += 1
            # Get actual territory stats before deletion
            t_links, t_rplus, t_S_mean = self._territory_stats(
                lid, label, state, node_torques)
            nearest = self._nearest_label_dist(lid, label)
            n_neighbors = self._n_phase_neighbors(lid, label)
            # Coherence at death
            thetas_d = [float(state.theta[n]) for n in label["nodes"]
                        if n in state.alive_n]
            if len(thetas_d) >= 2:
                sin_s = sum(math.sin(t) for t in thetas_d)
                cos_s = sum(math.cos(t) for t in thetas_d)
                theta_coh_d = math.sqrt(sin_s**2 + cos_s**2) / len(thetas_d)
            else:
                theta_coh_d = 0.0
            self.lifecycle_log.append({
                "label_id": lid,
                "window": window_count,
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

        # ── 6. METRICS ──
        stats["labels_active"] = len(self.labels)

        if self.labels:
            shares = [lb["share"] for lb in self.labels.values()]
            stats["top_share"] = round(max(shares), 4)

            # v3: age stats
            ages = [window_count - lb["born"] for lb in self.labels.values()]
            stats["v_oldest_age"] = max(ages)
            stats["v_mean_age"] = round(sum(ages) / len(ages), 1)

            five_node = [lb for lb in self.labels.values()
                         if len(lb["nodes"]) == 5]
            if five_node:
                stats["v_mean_share_5node"] = round(
                    sum(lb["share"] for lb in five_node) / len(five_node), 4)
                stats["v_births_5node"] = sum(
                    1 for lid in born_this_window
                    if lid in self.labels and len(self.labels[lid]["nodes"]) == 5)
            else:
                stats["v_mean_share_5node"] = 0.0
                stats["v_births_5node"] = 0

            stats["v_share_std"] = round(
                (sum((s - sum(shares)/len(shares))**2
                     for s in shares) / len(shares)) ** 0.5, 4)

            stats["v_deaths_5node"] = five_node_deaths

        if stats["torque_events"] > 0:
            stats["torque_total"] = round(stats["torque_total"], 4)
            stats["mean_torque"] = round(
                stats["torque_total"] / stats["torque_events"], 6)

        # Label territory R+ rate
        label_nodes = set()
        for label in self.labels.values():
            for n in label["nodes"]:
                label_nodes.add(n)
        label_rplus = 0
        label_total = 0
        other_rplus = 0
        other_total = 0
        for lk in state.alive_l:
            n1, n2 = lk
            r = state.R.get(lk, 0.0)
            in_label = (n1 in label_nodes or n2 in label_nodes)
            if in_label:
                label_total += 1
                if r > 0:
                    label_rplus += 1
            else:
                other_total += 1
                if r > 0:
                    other_rplus += 1
        if label_total > 0 and other_total > 0:
            rate_label = label_rplus / label_total
            rate_other = other_rplus / other_total
            stats["label_rplus_rate"] = round(
                rate_label / max(0.001, rate_other), 4)

        # Prune recurrence
        if len(self.recurrence) > 1000:
            sorted_rec = sorted(self.recurrence.items(),
                                key=lambda x: x[1])
            to_remove = len(self.recurrence) - 1000
            for k, _ in sorted_rec[:to_remove]:
                del self.recurrence[k]

        self.stats = stats
        return stats

    def summary(self):
        total_shares = {lid: lb["share"]
                        for lid, lb in self.labels.items()}
        return {
            "budget": 1.0,
            "labels_active": len(self.labels),
            "share_distribution": sorted(
                total_shares.values(), reverse=True)[:20],
            "label_details": [
                {
                    "id": lid,
                    "nodes": len(label["nodes"]),
                    "share": round(label["share"], 6),
                    "born": label["born"],
                    "phase_sig": round(label["phase_sig"], 4),
                    "alignment": round(
                        label.get("prev_alignment", 0), 4),
                }
                for lid, label in sorted(
                    self.labels.items(),
                    key=lambda x: x[1]["share"], reverse=True)[:30]
            ],
            "lifecycle_log_size": len(self.lifecycle_log),
        }
