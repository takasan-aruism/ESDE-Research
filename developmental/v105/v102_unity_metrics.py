"""
v9.18 段階 5 — Unity Metrics (A-Gemini: V_unified)
===================================================

CID 内部の「統合方向ベクトル / 収束度 / 生誕時からの角度差」を
Kuramoto オーダーパラメータとして計算する純関数モジュール。

責務:
  - 現在の構成ノードの θ から V_unified (complex) を計算
  - 生誕時 V_unified との argument 差 (wrap 済) を計算
  - 戻り値で結果を返すのみ (CidSelfBuffer への書き戻しは orchestrator 側)

規約:
  - pure function のみ (副作用なし)
  - CidSelfBuffer / engine / cog を import しない
  - numpy のみ依存
"""

from __future__ import annotations

from typing import Dict, Optional, Set

import numpy as np


def compute_v_unified(theta_values: np.ndarray) -> complex:
    """
    Kuramoto オーダーパラメータ (複素平面上の平均) を計算。

    V_unified = (1/k) * Σ exp(i * theta)

    Parameters
    ----------
    theta_values : np.ndarray
        構成ノードの θ 値 (k 個、radians)

    Returns
    -------
    complex : V_unified
        |.| ∈ [0, 1]、argument ∈ [-π, π]
        k=0 の場合は complex(0, 0) (計算不可)
    """
    if len(theta_values) == 0:
        return complex(0.0, 0.0)
    theta_array = np.asarray(theta_values, dtype=float)
    return complex(np.mean(np.exp(1j * theta_array)))


def _wrap_to_pi(raw_diff: float) -> float:
    """角度差を [-π, π] に折りたたむ (numpy 非依存のスカラー版)。"""
    return ((raw_diff + np.pi) % (2 * np.pi)) - np.pi


def compute_unity_metrics(
    current_theta_by_node: Dict[int, float],
    birth_v_unified: complex,
    current_member_nodes: Set[int],
) -> Dict[str, Optional[float]]:
    """
    V_unified 系 3 指標 + k を計算。

    Parameters
    ----------
    current_theta_by_node : Dict[int, float]
        現在の θ 値 (node_id -> θ)
    birth_v_unified : complex
        生誕時の V_unified (CID 確立時に 1 回計算、以降不変)
    current_member_nodes : Set[int]
        現在の構成ノード集合

    Returns
    -------
    Dict[str, Optional[float]]:
        unity_direction : float | None — 現在の argument (-π, π)
        unity_concentration : float | None — 現在の amplitude (0, 1)
        unity_direction_shift : float | None — 生誕時からの角度差絶対値 (0, π)
        k : int — 計算対象ノード数
    """
    theta_list = [
        current_theta_by_node[n]
        for n in current_member_nodes
        if n in current_theta_by_node
    ]
    k = len(theta_list)

    if k == 0:
        return {
            "unity_direction": None,
            "unity_concentration": None,
            "unity_direction_shift": None,
            "k": 0,
        }

    theta_array = np.asarray(theta_list, dtype=float)
    v_current = compute_v_unified(theta_array)

    direction = float(np.angle(v_current))
    concentration = float(abs(v_current))

    # 生誕時からの argument 差 ([-π, π] に wrap、絶対値で [0, π])
    if abs(birth_v_unified) > 1e-12:
        birth_direction = float(np.angle(birth_v_unified))
    else:
        birth_direction = 0.0
    raw_diff = direction - birth_direction
    wrapped_diff = _wrap_to_pi(raw_diff)
    direction_shift = float(abs(wrapped_diff))

    return {
        "unity_direction": direction,
        "unity_concentration": concentration,
        "unity_direction_shift": direction_shift,
        "k": k,
    }
