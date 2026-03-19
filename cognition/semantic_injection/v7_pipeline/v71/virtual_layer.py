#!/usr/bin/env python3
"""
ESDE Virtual Layer (World B)
==============================
独立モジュール。物理層のバージョンに依存しない。

物理層は床。このファイルは床の上に建つもの。

入力: 物理層の state, island tracker, substrate（読み取りのみ）
出力: phase torque（θ調整、物理層への唯一のフィードバック）
内部: label 生成、torque 成功によるエネルギー蓄積、領土競争

使い方:
    from virtual_layer import VirtualLayer
    vl = VirtualLayer()
    stats = vl.step(state, window_count, islands=tracker.islands,
                    substrate=substrate)
"""

import math
from collections import defaultdict


class VirtualLayer:
    """
    World B — 物理層から独立した因果層。

    物理層のクラスタが種を撒く。仮想層は自分で育てる。

    Label のエネルギー源 = torque の成功度（影響力）。
    物理層の R>0 や links 数には依存しない。
    影響力を失った label は死ぬ。影響力 = 存在。

    Semantic gravity: label はコアノードだけでなく、
    substrate 上の隣接ノードの θ も引っ張る。
    リンクの数を増やすのではなく、配置を合理化する。
    「惑星は化学で安定している。エネルギーの塊ではない」
    """

    def __init__(self):
        # Recurrence: {frozenset(nodes): times_seen}
        self.recurrence = {}

        # Label Registry: {label_id: dict}
        self.labels = {}
        self.next_label_id = 0

        # Per-window stats
        self.stats = {}

    def step(self, state, window_count, islands=None, substrate=None):
        """
        1 window に 1 回、物理層の後に呼ぶ。

        Args:
            state: GenesisState（物理層の状態。θ のみ書き込む）
            window_count: 現在の window 番号
            islands: dict {island_id: IslandState} — island tracker から
            substrate: dict {node: set(neighbors)} — frozen grid
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

        # ── 1. SEED: clusters (2+) + R>0 pairs ──
        cluster_list = []
        if islands:
            for iid, info in islands.items():
                if len(info.nodes) >= 2:
                    cluster_list.append(info.nodes)
                    self.recurrence[info.nodes] = \
                        self.recurrence.get(info.nodes, 0) + 1

        # R>0 pairs as seeds (may not appear in islands)
        for lk in state.alive_l:
            r = state.R.get(lk, 0.0)
            if r > 0:
                pair = frozenset(lk)
                if pair not in self.recurrence:
                    cluster_list.append(pair)
                self.recurrence[pair] = \
                    self.recurrence.get(pair, 0) + 1

        # Stale recurrence cleanup
        current_clusters = set()
        if islands:
            for info in islands.values():
                if len(info.nodes) >= 2:
                    current_clusters.add(info.nodes)
        for lk in state.alive_l:
            if state.R.get(lk, 0.0) > 0:
                current_clusters.add(frozenset(lk))
        stale = [k for k, v in self.recurrence.items()
                 if k not in current_clusters and v < 2]
        for k in stale:
            del self.recurrence[k]

        stats["recurrence_entries"] = len(self.recurrence)
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
                "strength": float(len(cluster_nodes)),
                "born": window_count,
                "prev_alignment": 0.0,
                "coherence": 1.0,
            }
            self.next_label_id += 1
            stats["labels_born"] += 1

        # ── 2. LIVE: torque + semantic gravity ──
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

            # Core nodes: full torque
            for n in label["nodes"]:
                if n not in state.alive_n:
                    continue
                theta_n = float(state.theta[n])
                torque = torque_mag * math.sin(
                    label["phase_sig"] - theta_n)
                existing = node_torques.get(n)
                if existing is None or label["strength"] > existing[1]:
                    node_torques[n] = (torque, label["strength"], lid)

            # Semantic gravity: substrate neighbors, half strength
            if substrate:
                gravity_mag = torque_mag * 0.5
                for n in label["nodes"]:
                    for nb in substrate.get(n, set()):
                        if nb not in state.alive_n:
                            continue
                        if nb in label["nodes"]:
                            continue
                        theta_nb = float(state.theta[nb])
                        grav_torque = gravity_mag * math.sin(
                            label["phase_sig"] - theta_nb)
                        existing = node_torques.get(nb)
                        if existing is None or \
                                label["strength"] > existing[1]:
                            node_torques[nb] = (
                                grav_torque, label["strength"], lid)

            if success > 0:
                stats["torque_success"] += success

        # Apply torque
        for n, (torque, _, _) in node_torques.items():
            state.theta[n] += torque
            stats["torque_events"] += 1
            stats["torque_total"] += abs(torque)

        # ── 3. COMPETE: territorial decay ──
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

        # ── 4. Prune recurrence map ──
        if len(self.recurrence) > 1000:
            sorted_rec = sorted(self.recurrence.items(),
                                key=lambda x: x[1])
            to_remove = len(self.recurrence) - 1000
            for k, _ in sorted_rec[:to_remove]:
                del self.recurrence[k]

        stats["labels_active"] = len(self.labels)
        stats["virtual_energy_total"] = round(total_virtual_energy, 4)

        if stats["torque_events"] > 0:
            stats["torque_total"] = round(stats["torque_total"], 4)
            stats["mean_torque"] = round(
                stats["torque_total"] / stats["torque_events"], 6)
        stats["torque_success"] = round(stats["torque_success"], 4)

        self.stats = stats
        return stats

    def summary(self):
        """JSON serialization 用。"""
        total_strength = sum(
            lb["strength"] for lb in self.labels.values())
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
                    "alignment": round(
                        label.get("prev_alignment", 0), 4),
                    "coherence": round(
                        label.get("coherence", 0), 4),
                }
                for lid, label in sorted(
                    self.labels.items(),
                    key=lambda x: x[1]["strength"], reverse=True)
            ],
        }