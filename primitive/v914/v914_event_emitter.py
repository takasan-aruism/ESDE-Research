#!/usr/bin/env python3
"""
ESDE v9.14 — Event Emitter (Layer B)
=====================================
E1 / E2 / E3 event 検知ロジック。全て pure function (決定論的、RNG 非使用、
state mutation 無し)。SpendAuditLedger から呼び出される。

イベント定義 (v914_implementation_instructions.md §4):
  E1 (core link death/birth):
    cid の member node pair で構成されるリンクが alive_l から落ちた瞬間 (death)、
    または再び alive_l に加わった瞬間 (birth)。
  E2 (core link R-state change):
    member link の R 値が 0 境界を跨いだ step (0→>0 = rise, >0→0 = fall)。
    core-adjacent への拡張は禁止。
  E3 (familiarity contact onset):
    cid A と cid B の member node 集合が同じ alive リンクを共有した最初の step。
    既に記録済みのペアは onset ではない (初回のみ event 化)。

Step 2 時点では E1 のみ実装。E2 (Step 4) / E3 (Step 5) は後続で追加。
"""

from __future__ import annotations

from typing import Iterable


def compute_member_alive_links(member_nodes, alive_l_set: set) -> frozenset:
    """member_nodes の pair 中で alive_l に存在するリンクを返す。

    alive_l_set: (min, max) 正規化された 2-tuple の集合 (engine.state.alive_l)。
    member_nodes: frozenset / set / iterable of int。

    計算量: O(|member_nodes|^2)。|member_nodes| は典型 3-10 程度なので問題なし
    (v914_implementation_instructions.md §6)。
    """
    nodes_list = sorted(member_nodes)
    result = set()
    n = len(nodes_list)
    for i in range(n):
        for j in range(i + 1, n):
            lk = (nodes_list[i], nodes_list[j])
            if lk in alive_l_set:
                result.add(lk)
    return frozenset(result)


def detect_e1_events(prev_member_alive: frozenset,
                     curr_member_alive: frozenset) -> list:
    """E1 (core link death/birth) を検出。

    Returns:
        list of (event_type, link_key) tuples:
          event_type: "E1_death" or "E1_birth"
          link_key: (min, max) tuple
    """
    events = []
    for lk in sorted(prev_member_alive - curr_member_alive):
        events.append(("E1_death", lk))
    for lk in sorted(curr_member_alive - prev_member_alive):
        events.append(("E1_birth", lk))
    return events


def compute_member_r(member_nodes, state_r: dict, alive_l_set: set) -> dict:
    """alive な member link について R>0 のものを返す。

    戻り値は dict link_key -> R value。
    R==0 や dead link は含めない (E2 is narrow by design — §4.2、§9.3)。
    """
    nodes_list = sorted(member_nodes)
    result = {}
    n = len(nodes_list)
    for i in range(n):
        for j in range(i + 1, n):
            lk = (nodes_list[i], nodes_list[j])
            if lk in alive_l_set:
                r = state_r.get(lk, 0.0)
                if r > 0:
                    result[lk] = float(r)
    return result


def detect_e2_events(prev_member_r: dict, curr_member_r: dict) -> list:
    """E2 (core link R-state change): R が 0 境界を跨いだ step を検出。

    prev_member_r / curr_member_r: dict link_key -> R (R>0 のもののみ)。

    Semantics (§4.2):
      - E2_rise: prev に無く (dead or R==0) curr で alive & R>0
      - E2_fall: prev で alive & R>0 だったのに curr で dead or R==0

    Returns: list of (event_type, link_key) tuples, sorted by link_key.
    core-adjacent への拡張は一切しない (§4.2 禁則、§9.3 監視対象)。
    """
    events = []
    for lk in sorted(prev_member_r.keys() - curr_member_r.keys()):
        events.append(("E2_fall", lk))
    for lk in sorted(curr_member_r.keys() - prev_member_r.keys()):
        events.append(("E2_rise", lk))
    return events


def detect_e3_new_pairs(alive_l_set: set, node_to_cids: dict,
                         contacted_pairs: set) -> list:
    """E3 (familiarity contact onset): cid A と cid B の member nodes が同じ
    alive link で接続された最初の step を検出。

    最適化 (§4.3、§6.2): 各 alive link について両端ノードが属する cid を引いて
    2 cid 以上が関わるとき contact 候補。O(|alive_l| × avg_cids_per_node^2)。

    既に contacted_pairs に含まれる cid ペアはスキップ (onset = 初回のみ)。

    Args:
        alive_l_set: engine.state.alive_l (set of (min,max) tuples)
        node_to_cids: dict node -> set of cids (member_nodes にその node を
            含む cid 集合、self.ledger から構築)
        contacted_pairs: set of frozenset({cid_a, cid_b})。この関数内で
            新規ペアを追加 (mutation する)。

    Returns:
        list of (cid_a, cid_b, link_key) tuples。cid_a < cid_b で canonical 化。
        新規 pair のみ含む。caller が spend packet / event 発行を行う。

    禁止 (§4.3): familiarity state 由来のトリガーは一切使わない。
    物理的事実 (リンク共有) のみで判定。
    """
    new_pairs = []
    for lk in alive_l_set:
        a, b = lk
        cids_at_a = node_to_cids.get(a)
        cids_at_b = node_to_cids.get(b)
        if not cids_at_a or not cids_at_b:
            continue
        # Cross product: 同じ cid 同士 (内部リンク) は contact ではない。
        # frozenset で pair 正規化し、contacted_pairs で重複防止。
        for cid_a in cids_at_a:
            for cid_b in cids_at_b:
                if cid_a == cid_b:
                    continue
                pair_key = frozenset((cid_a, cid_b))
                if pair_key in contacted_pairs:
                    continue
                contacted_pairs.add(pair_key)
                c1 = cid_a if cid_a < cid_b else cid_b
                c2 = cid_b if cid_a < cid_b else cid_a
                new_pairs.append((c1, c2, lk))
    return new_pairs
