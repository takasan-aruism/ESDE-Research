"""
v9.15 Layer C — Fetch Operations [B]
=====================================

CidSelfBuffer の生成 (Lazy Registration) および pulse タイミングでの
read_own_state 呼び出しを担うヘルパ群。

規約 (A/B 分離):
  - 本ファイルは [B]。v916_cid_self_buffer のみ import 可
  - [A] ファイルを import してはいけない

設計:
  - registry: dict[cid(int) -> CidSelfBuffer]。main loop で保持
  - Lazy Registration: cid が最初に Fetch される必要が出た時
    (= birth 直後) に CidSelfBuffer を生成
  - birth_step: v9.14 の cumulative_step / v913_global_step を使用
    (maturation 中は 0、tracking 開始以降は step 単位で増加)
"""

from __future__ import annotations

from typing import Any

import numpy as np

from v916_cid_self_buffer import CidSelfBuffer


def ensure_cid_registered(
    registry: dict,
    cid: int,
    member_node_set,
    state: Any,
    current_step: int,
    Q0: int,
) -> CidSelfBuffer | None:
    """
    cid が registry に未登録であれば、現在の state を生誕時スナップショットとして
    CidSelfBuffer を生成し、registry に登録して返す。
    既に登録済みなら no-op (既存バッファを返す)。

    Parameters
    ----------
    registry : dict[int, CidSelfBuffer]
        main loop が保持する cid -> buffer のマッピング
    cid : int
        cid 番号。None の場合は何もせず None を返す
    member_node_set : iterable[int]
        cid を構成するメンバーノード集合 (lab["nodes"] を想定)
    state : engine.state
        state.theta (ndarray), state.S (dict), state.alive_l (set of tuples)
    current_step : int
        生誕時ステップ (v913_global_step / cumulative_step)
    Q0 : int
        生誕時 Q0 (= floor(B_Gen))。v9.16 段階 3 で age_factor の分母として使用。
        b_gen=inf / <=0 の cid は Q0=0 を渡す (age_factor 常に 0)。

    Returns
    -------
    CidSelfBuffer または None (cid が None の場合)
    """
    if cid is None:
        return None
    if cid in registry:
        return registry[cid]

    member_nodes = frozenset(member_node_set)
    sorted_members = sorted(member_nodes)

    # 初期 theta スナップショット (sorted 順)
    initial_theta = np.array(
        [float(state.theta[n]) for n in sorted_members],
        dtype=float,
    )

    # 初期 S スナップショット (メンバー内リンクのみ)
    # engine の alive_l は tuple (i,j) 形式
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
    """
    pulse タイミングで呼ぶ: cid の CidSelfBuffer に現在状態を Fetch させる。
    registry に cid がいない場合は何もせず False。

    Parameters
    ----------
    registry : dict[int, CidSelfBuffer]
    cid : int
    state : engine.state
    alive_l : set (tuple キー)
    current_step : int

    Returns
    -------
    bool : Fetch が行われたかどうか
    """
    buf = registry.get(cid)
    if buf is None:
        return False
    return buf.read_own_state(state, alive_l, current_step)
