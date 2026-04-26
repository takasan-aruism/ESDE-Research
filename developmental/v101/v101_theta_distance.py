"""
v9.18 段階 5 — Theta Distance (A-GPT: 生誕時分布からの距離指標)
================================================================

CID の現在の θ 分布と生誕時 θ 分布の距離を計算する純関数モジュール。
設計: B 案 + coverage_ratio (2 AI §4.1 固定)
  - common_nodes (生誕時 ∩ 現在) のみで RMS 距離を計算
  - coverage_ratio = |common_nodes| / |birth_member_nodes| を必ず記録

責務:
  - 生誕時と現在の θ 分布から distance を計算
  - coverage_ratio と共に返す
  - 戻り値で結果を返すのみ

規約:
  - pure function のみ (副作用なし)
  - CidSelfBuffer / engine / cog を import しない
  - numpy のみ依存
"""

from __future__ import annotations

from typing import Dict, Optional, Set

import numpy as np


def _wrap_to_pi_array(raw_diffs: np.ndarray) -> np.ndarray:
    """角度差 array を [-π, π] に折りたたむ。"""
    return ((raw_diffs + np.pi) % (2 * np.pi)) - np.pi


def compute_theta_distance(
    current_theta_by_node: Dict[int, float],
    birth_theta_by_node: Dict[int, float],
    current_member_nodes: Set[int],
    birth_member_nodes: Set[int],
) -> Dict[str, Optional[float]]:
    """
    生誕時 θ 分布との距離 + coverage_ratio を計算。

    Parameters
    ----------
    current_theta_by_node : Dict[int, float]
        現在の θ (node_id -> θ)
    birth_theta_by_node : Dict[int, float]
        生誕時の θ (node_id -> θ)
    current_member_nodes : Set[int]
        現在の構成ノード集合
    birth_member_nodes : Set[int]
        生誕時の構成ノード集合 (CidSelfBuffer.member_nodes と同値)

    Returns
    -------
    Dict[str, Optional[float]]:
        theta_distance_from_birth : float | None
            共通ノード上での位相差 RMS。coverage < 2 のとき None
        coverage_ratio : float
            |common_nodes| / |birth_member_nodes|。分母 0 は 0.0
    """
    common_nodes = birth_member_nodes & current_member_nodes

    if len(birth_member_nodes) == 0:
        coverage_ratio = 0.0
    else:
        coverage_ratio = len(common_nodes) / len(birth_member_nodes)

    if len(common_nodes) < 2:
        return {
            "theta_distance_from_birth": None,
            "coverage_ratio": float(coverage_ratio),
        }

    diffs = []
    for node in common_nodes:
        theta_curr = current_theta_by_node.get(node)
        theta_birth = birth_theta_by_node.get(node)
        if theta_curr is None or theta_birth is None:
            continue
        diffs.append(float(theta_curr) - float(theta_birth))

    if len(diffs) < 2:
        return {
            "theta_distance_from_birth": None,
            "coverage_ratio": float(coverage_ratio),
        }

    diffs_array = np.asarray(diffs, dtype=float)
    wrapped = _wrap_to_pi_array(diffs_array)
    distance = float(np.sqrt(np.mean(wrapped ** 2)))

    return {
        "theta_distance_from_birth": distance,
        "coverage_ratio": float(coverage_ratio),
    }
