"""
v9.18 単体テスト: compute_v_unified / compute_unity_metrics
"""

from __future__ import annotations

import numpy as np

from v918_unity_metrics import (
    compute_v_unified,
    compute_unity_metrics,
    _wrap_to_pi,
)


EPS = 1e-9


# ---------------------------------------------------------------
# compute_v_unified の境界
# ---------------------------------------------------------------

def test_v_unified_empty():
    v = compute_v_unified(np.array([]))
    assert v == complex(0.0, 0.0)


def test_v_unified_single_node():
    theta = np.array([0.5])
    v = compute_v_unified(theta)
    # k=1 なら |v| = 1、argument = theta
    assert abs(abs(v) - 1.0) < EPS
    assert abs(np.angle(v) - 0.5) < EPS


def test_v_unified_all_same():
    theta = np.array([0.3, 0.3, 0.3, 0.3])
    v = compute_v_unified(theta)
    # 全ノード同一 → concentration=1
    assert abs(abs(v) - 1.0) < EPS
    assert abs(np.angle(v) - 0.3) < EPS


def test_v_unified_antipodal():
    # 対向する 2 点は concentration=0
    theta = np.array([0.0, np.pi])
    v = compute_v_unified(theta)
    assert abs(v) < EPS


def test_v_unified_uniform_distribution():
    # 円周上均等な 8 点 → concentration ≈ 0
    theta = np.array([i * 2 * np.pi / 8 for i in range(8)])
    v = compute_v_unified(theta)
    assert abs(v) < 1e-12


# ---------------------------------------------------------------
# _wrap_to_pi の境界
# ---------------------------------------------------------------

def test_wrap_to_pi_within():
    assert abs(_wrap_to_pi(0.0) - 0.0) < EPS
    assert abs(_wrap_to_pi(1.0) - 1.0) < EPS
    assert abs(_wrap_to_pi(-1.0) - (-1.0)) < EPS


def test_wrap_to_pi_boundary():
    # π の境界: [-π, π) の仕様なので π は -π に畳まれる (modular)
    # _wrap_to_pi(π) = ((π + π) % 2π) - π = 0 - π = -π
    assert abs(_wrap_to_pi(np.pi) - (-np.pi)) < EPS
    # -π はそのまま
    assert abs(_wrap_to_pi(-np.pi) - (-np.pi)) < EPS


def test_wrap_to_pi_wraparound():
    # 3π/2 → -π/2
    assert abs(_wrap_to_pi(3 * np.pi / 2) - (-np.pi / 2)) < EPS
    # -3π/2 → π/2
    assert abs(_wrap_to_pi(-3 * np.pi / 2) - (np.pi / 2)) < EPS


# ---------------------------------------------------------------
# compute_unity_metrics の境界
# ---------------------------------------------------------------

def test_unity_metrics_k_zero():
    # current_member_nodes が current_theta_by_node に全くなければ k=0
    result = compute_unity_metrics(
        current_theta_by_node={},
        birth_v_unified=complex(1.0, 0.0),
        current_member_nodes={1, 2, 3},
    )
    assert result["k"] == 0
    assert result["unity_direction"] is None
    assert result["unity_concentration"] is None
    assert result["unity_direction_shift"] is None


def test_unity_metrics_k_partial():
    # member 5 個のうち 2 個だけ current_theta にある
    result = compute_unity_metrics(
        current_theta_by_node={1: 0.1, 2: 0.2},
        birth_v_unified=complex(1.0, 0.0),
        current_member_nodes={1, 2, 3, 4, 5},
    )
    assert result["k"] == 2
    assert result["unity_direction"] is not None
    assert result["unity_concentration"] is not None


def test_unity_metrics_no_change():
    # 生誕時と同一分布 → direction_shift = 0
    birth_theta = np.array([0.1, 0.2, 0.3])
    birth_v = compute_v_unified(birth_theta)
    result = compute_unity_metrics(
        current_theta_by_node={10: 0.1, 20: 0.2, 30: 0.3},
        birth_v_unified=birth_v,
        current_member_nodes={10, 20, 30},
    )
    assert result["k"] == 3
    # direction は birth と同じ
    assert abs(result["unity_direction"] - np.angle(birth_v)) < EPS
    # direction_shift = 0
    assert abs(result["unity_direction_shift"]) < 1e-6
    # concentration は birth と同じ
    assert abs(result["unity_concentration"] - abs(birth_v)) < EPS


def test_unity_metrics_shift_range():
    # 生誕時 θ=0, 現在 θ=π/2 に偏移 → shift ≈ π/2
    birth_v = compute_v_unified(np.array([0.0, 0.0]))  # direction = 0
    result = compute_unity_metrics(
        current_theta_by_node={1: np.pi / 2, 2: np.pi / 2},
        birth_v_unified=birth_v,
        current_member_nodes={1, 2},
    )
    assert abs(result["unity_direction_shift"] - np.pi / 2) < EPS


def test_unity_metrics_concentration_range():
    result = compute_unity_metrics(
        current_theta_by_node={1: 0.0, 2: np.pi},
        birth_v_unified=complex(1.0, 0.0),
        current_member_nodes={1, 2},
    )
    # concentration ∈ [0, 1]
    assert 0.0 <= result["unity_concentration"] <= 1.0 + EPS
    # 対向点なので concentration は 0 に近い
    assert result["unity_concentration"] < EPS


def test_unity_metrics_birth_zero_vector():
    # birth_v_unified が (0,0) のとき (ほぼ発生しないが境界) direction_shift は直接計算
    result = compute_unity_metrics(
        current_theta_by_node={1: 1.0, 2: 1.0},
        birth_v_unified=complex(0.0, 0.0),
        current_member_nodes={1, 2},
    )
    # 例外を投げず有限値を返す
    assert result["unity_direction_shift"] is not None
    # shift ∈ [0, π]
    assert 0.0 <= result["unity_direction_shift"] <= np.pi + EPS


# ---------------------------------------------------------------
# runner
# ---------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_v_unified_empty,
        test_v_unified_single_node,
        test_v_unified_all_same,
        test_v_unified_antipodal,
        test_v_unified_uniform_distribution,
        test_wrap_to_pi_within,
        test_wrap_to_pi_boundary,
        test_wrap_to_pi_wraparound,
        test_unity_metrics_k_zero,
        test_unity_metrics_k_partial,
        test_unity_metrics_no_change,
        test_unity_metrics_shift_range,
        test_unity_metrics_concentration_range,
        test_unity_metrics_birth_zero_vector,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"[ERR ] {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed "
          f"({failed} failed)")
    exit(1 if failed else 0)
