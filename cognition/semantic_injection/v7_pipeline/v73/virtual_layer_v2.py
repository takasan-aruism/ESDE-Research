#!/usr/bin/env python3
"""
ESDE Virtual Layer v2 — 代謝モデル (Budget = 1)
==================================================
"物理層の安定的な稼働が１の原資。増減する必要がない。
 仮想的なエネルギーを定義したならそのエネルギーを使って
 何ができるか？ 代謝の仕組みを整えるだけ。"

物理層が動いている = budget 1。
1 を label 間で配分する。合計は常に 1。
影響力（支配するリンク数の割合）が配分基準。
多く支配する label は多く取り、少なければ少なく取る。
ゼロサム。太陽は増やせない。光の配分だけ。

torque の強さ = share × sin(Δθ)。
share が大きい label は物理層への影響力が大きい。
share が小さい label は死ぬ。

固定定数: なし。
"""

import math
from collections import defaultdict


class VirtualLayer:

    def __init__(self):
        self.recurrence = {}
        self.labels = {}
        self.next_label_id = 0
        self.stats = {}

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

        # ── 0. BUDGET ──
        # 物理層が動いている = 1。それだけ。
        alive_links = len(state.alive_l)
        budget = 1.0 if alive_links > 0 else 0.0
        stats["budget"] = budget

        # ── 1. SEED ──
        cluster_list = []
        if islands:
            for iid, info in islands.items():
                nodes = frozenset(info.nodes)  # ensure hashable
                if len(nodes) >= 2:
                    cluster_list.append(nodes)
                    self.recurrence[nodes] = \
                        self.recurrence.get(nodes, 0) + 1

        # R>0 pairs
        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                pair = frozenset(lk)
                if pair not in self.recurrence:
                    cluster_list.append(pair)
                self.recurrence[pair] = \
                    self.recurrence.get(pair, 0) + 1

        # Stale cleanup
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

            self.labels[self.next_label_id] = {
                "nodes": frozenset(cluster_nodes),
                "phase_sig": phase_sig,
                "share": 0.0,
                "born": window_count,
                "prev_alignment": 0.0,
            }
            self.next_label_id += 1
            stats["labels_born"] += 1

        if not self.labels or budget == 0:
            stats["labels_active"] = len(self.labels)
            self.stats = stats
            return stats

        # ── 2. INFLUENCE: who controls which nodes? ──
        # Each label torques its nodes. Strongest influence wins.
        # Then count links connected to won nodes.
        node_owner = {}  # {node: (label_id, alignment)}

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

            # Influence strength: how aligned are my nodes with me?
            # Positive alignment = I control this region.
            influence = max(0.0, mean_align)

            for n, _ in alignments:
                existing = node_owner.get(n)
                if existing is None or influence > existing[1]:
                    node_owner[n] = (lid, influence)

        # Count links per label: links where at least one endpoint is owned
        label_link_count = defaultdict(int)
        for lk in state.alive_l:
            n1, n2 = lk
            owner1 = node_owner.get(n1)
            owner2 = node_owner.get(n2)
            if owner1:
                label_link_count[owner1[0]] += 1
            if owner2 and (not owner1 or owner2[0] != owner1[0]):
                label_link_count[owner2[0]] += 1

        # ── 3. ALLOCATE: share = influence / total ──
        total_influence = sum(label_link_count.values())
        if total_influence == 0:
            total_influence = 1

        for lid, label in self.labels.items():
            label["share"] = label_link_count.get(lid, 0) / total_influence

        # ── 4. TORQUE: strength = budget × share ──
        node_torques = {}
        for lid, label in self.labels.items():
            energy = budget * label["share"]
            if energy < 0.0001:
                continue

            torque_mag = energy  # direct: share IS torque strength

            # Core nodes
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_mag * math.sin(
                    label["phase_sig"] - theta_n)
                existing = node_torques.get(n)
                if existing is None or energy > existing[1]:
                    node_torques[n] = (torque, energy, lid)

            # Semantic gravity: substrate neighbors
            # Gravity weakens with label size — more nodes = weaker per-node pull
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

        # Apply torque
        for n, (torque, _, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        # ── 5. CULL: below half of fair share → die ──
        label_count = len(self.labels)
        fair_share = 1.0 / max(1, label_count)
        death_threshold = fair_share * 0.5

        dead_labels = [lid for lid, label in self.labels.items()
                       if label["share"] < death_threshold]
        for lid in dead_labels:
            del self.labels[lid]
            stats["labels_died"] += 1

        # ── 6. METRICS ──
        stats["labels_active"] = len(self.labels)

        if self.labels:
            shares = [lb["share"] for lb in self.labels.values()]
            stats["top_share"] = round(max(shares), 4)

        if stats["torque_events"] > 0:
            stats["torque_total"] = round(stats["torque_total"], 4)
            stats["mean_torque"] = round(
                stats["torque_total"] / stats["torque_events"], 6)

        # Label territory R+ rate vs non-label R+ rate
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
        }
