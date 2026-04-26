"""
v9.18 Layer C — Fetch Operations [B]
=====================================

v9.17 fetch_operations の薄いラッパ。CidSelfBuffer の生成のみを
v918 サブクラスに差し替え、他挙動は v917 と完全同一。

規約 (A/B 分離):
  - 本ファイルは [B]。v918_cid_self_buffer のみ import 可
  - [A] ファイルを import してはいけない
"""

from __future__ import annotations

from typing import Any

import numpy as np

from v101_cid_self_buffer import CidSelfBuffer


def ensure_cid_registered(
    registry: dict,
    cid: int,
    member_node_set,
    state: Any,
    current_step: int,
    Q0: int,
) -> CidSelfBuffer | None:
    """
    cid 未登録なら v9.18 CidSelfBuffer を生成して registry に登録。
    既登録なら no-op (既存 buffer を返す)。

    v9.17 版と機能等価。CidSelfBuffer 生成時に v9.18 の生誕時スナップショット
    (v18_birth_v_unified 等) が __init__ で自動計算される。
    """
    if cid is None:
        return None
    if cid in registry:
        return registry[cid]

    member_nodes = frozenset(member_node_set)
    sorted_members = sorted(member_nodes)

    initial_theta = np.array(
        [float(state.theta[n]) for n in sorted_members],
        dtype=float,
    )

    initial_S: dict = {}
    for link in state.alive_l:
        if all(n in member_nodes for n in link):
            initial_S[link] = float(state.S[link])

    buf = CidSelfBuffer(
        cid_id=cid,
        member_nodes=member_nodes,
        birth_step=int(current_step),
        initial_theta=initial_theta,
        initial_S=initial_S,
        Q0=int(Q0),
    )
    registry[cid] = buf
    return buf


def pulse_fetch(
    registry: dict,
    cid: int,
    state: Any,
    alive_l,
    current_step: int,
) -> bool:
    """v9.15 互換の pulse_fetch (メインループから呼ばれない、残置)。"""
    buf = registry.get(cid)
    if buf is None:
        return False
    return buf.read_own_state(state, alive_l, current_step)
