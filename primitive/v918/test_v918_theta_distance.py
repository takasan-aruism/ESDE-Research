"""
v9.18 単体テスト: compute_theta_distance
"""

from __future__ import annotations

import numpy as np

from v918_theta_distance import compute_theta_distance, _wrap_to_pi_array


EPS = 1e-9


# ---------------------------------------------------------------
# _wrap_to_pi_array の境界
# ---------------------------------------------------------------

def test_wrap_to_pi_array_basic():
    arr = np.array([0.0, 1.0, -1.0])
    wrapped = _wrap_to_pi_array(arr)
    assert np.allclose(wrapped, arr)


def test_wrap_to_pi_array_wraparound():
    arr = np.array([3 * np.pi / 2, -3 * np.pi / 2, 2 * np.pi, -2 * np.pi])
    wrapped = _wrap_to_pi_array(arr)
    expected = np.array([-np.pi / 2, np.pi / 2, 0.0, 0.0])
    assert np.allclose(wrapped, expected, atol=1e-9)


# ---------------------------------------------------------------
# compute_theta_distance の境界
# ---------------------------------------------------------------

def test_distance_empty_birth():
    # birth_member_nodes 空 → coverage=0, distance=None
    result = compute_theta_distance(
        current_theta_by_node={1: 0.5, 2: 0.5},
        birth_theta_by_node={},
        current_member_nodes={1, 2},
        birth_member_nodes=set(),
    )
    assert result["coverage_ratio"] == 0.0
    assert result["theta_distance_from_birth"] is None


def test_distance_no_common_nodes():
    # 完全に入れ替わった member → common=0, distance=None
    result = compute_theta_distance(
        current_theta_by_node={10: 0.0, 20: 0.0},
        birth_theta_by_node={1: 0.5, 2: 0.5, 3: 0.5},
        current_member_nodes={10, 20},
        birth_member_nodes={1, 2, 3},
    )
    assert result["coverage_ratio"] == 0.0
    assert result["theta_distance_from_birth"] is None


def test_distance_single_common_node():
    # common=1 → distance 計算不可 (< 2)
    result = compute_theta_distance(
        current_theta_by_node={1: 0.1, 20: 0.2},
        birth_theta_by_node={1: 0.0, 2: 0.0, 3: 0.0},
        current_member_nodes={1, 20},
        birth_member_nodes={1, 2, 3},
    )
    assert abs(result["coverage_ratio"] - 1/3) < EPS
    assert result["theta_distance_from_birth"] is None


def test_distance_zero_when_no_change():
    # 完全一致 → distance=0
    result = compute_theta_distance(
        current_theta_by_node={1: 0.1, 2: 0.2, 3: 0.3},
        birth_theta_by_node={1: 0.1, 2: 0.2, 3: 0.3},
        current_member_nodes={1, 2, 3},
        birth_member_nodes={1, 2, 3},
    )
    assert result["coverage_ratio"] == 1.0
    assert abs(result["theta_distance_from_birth"]) < EPS


def test_distance_uniform_shift():
    # 全ノードが同じ δ で shift → RMS = δ
    delta = 0.3
    result = compute_theta_distance(
        current_theta_by_node={1: 0.1 + delta, 2: 0.2 + delta, 3: 0.3 + delta},
        birth_theta_by_node={1: 0.1, 2: 0.2, 3: 0.3},
        current_member_nodes={1, 2, 3},
        birth_member_nodes={1, 2, 3},
    )
    assert result["coverage_ratio"] == 1.0
    assert abs(result["theta_distance_from_birth"] - delta) < EPS


def test_distance_wraparound():
    # 位相差が 2π 超えても wrap で [-π, π] に畳まれる
    # birth 0, current 2π → wrap で 0 → distance 0
    result = compute_theta_distance(
        current_theta_by_node={1: 2 * np.pi, 2: 2 * np.pi},
        birth_theta_by_node={1: 0.0, 2: 0.0},
        current_member_nodes={1, 2},
        birth_member_nodes={1, 2},
    )
    assert abs(result["theta_distance_from_birth"]) < 1e-9


def test_distance_partial_coverage():
    # birth 4 member、current 3 member (1 消失) → coverage = 3/4
    result = compute_theta_distance(
        current_theta_by_node={1: 0.1, 2: 0.2, 3: 0.3, 99: 0.9},
        birth_theta_by_node={1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4},
        current_member_nodes={1, 2, 3, 99},
        birth_member_nodes={1, 2, 3, 4},
    )
    # coverage = |{1,2,3}| / |{1,2,3,4}| = 3/4
    assert abs(result["coverage_ratio"] - 0.75) < EPS
    # common={1,2,3} で全一致 → distance=0
    assert abs(result["theta_distance_from_birth"]) < EPS


def test_distance_missing_current_theta_for_node():
    # common ノードだが current_theta_by_node に値がない (k=1 になる)
    result = compute_theta_distance(
        current_theta_by_node={1: 0.1},  # 2 が欠損
        birth_theta_by_node={1: 0.0, 2: 0.0},
        current_member_nodes={1, 2},
        birth_member_nodes={1, 2},
    )
    # coverage = 1.0 (common = {1,2})、だが実際に値が取れるのは 1 ノードのみ → None
    assert result["coverage_ratio"] == 1.0
    assert result["theta_distance_from_birth"] is None


def test_distance_nonneg():
    # 任意の入力で distance >= 0 or None
    result = compute_theta_distance(
        current_theta_by_node={1: 1.5, 2: -0.8, 3: 2.0},
        birth_theta_by_node={1: -1.2, 2: 0.5, 3: 1.0},
        current_member_nodes={1, 2, 3},
        birth_member_nodes={1, 2, 3},
    )
    assert result["theta_distance_from_birth"] is not None
    assert result["theta_distance_from_birth"] >= 0.0


# ---------------------------------------------------------------
# runner
# ---------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_wrap_to_pi_array_basic,
        test_wrap_to_pi_array_wraparound,
        test_distance_empty_birth,
        test_distance_no_common_nodes,
        test_distance_single_common_node,
        test_distance_zero_when_no_change,
        test_distance_uniform_shift,
        test_distance_wraparound,
        test_distance_partial_coverage,
        test_distance_missing_current_theta_for_node,
        test_distance_nonneg,
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
