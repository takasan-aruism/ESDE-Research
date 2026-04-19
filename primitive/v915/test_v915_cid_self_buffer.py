"""
v9.15 Step 1 単体テスト: CidSelfBuffer

承認条件 (指示書 §8.2 Step 1):
  - CidSelfBuffer クラスが実装されている
  - 単体テスト: ダミーデータで read_own_state が動作、match_history が記録される
  - _a_observer_* メソッドが read-only で動作
  - A からのアクセスが read-only であることを単体テストで確認
    (例: _a_observer_get_match_history の返り値を変更しても内部に影響しない)

実行: python test_v915_cid_self_buffer.py
"""

from __future__ import annotations

import sys
import types

import numpy as np

from v915_cid_self_buffer import CidSelfBuffer


def make_dummy_state(theta_map: dict, S_map: dict):
    """state.theta[node], state.S[link] で参照できる最小オブジェクト。"""
    state = types.SimpleNamespace()
    state.theta = dict(theta_map)  # defensive copy
    state.S = dict(S_map)
    return state


# ---------------------------------------------------------------------------
# Fixture: 3 ノード cid (nodes 10, 20, 30) + 3 メンバー内リンク
# ---------------------------------------------------------------------------

def make_fixture():
    member_nodes = frozenset({10, 20, 30})
    birth_step = 100
    initial_theta_map = {10: 1.0, 20: 2.0, 30: 3.0, 99: 999.0}  # 99 は外部ノード
    initial_S_map = {
        frozenset({10, 20}): 0.5,
        frozenset({10, 30}): 0.6,
        frozenset({20, 30}): 0.7,
        frozenset({10, 99}): 0.9,  # メンバー外リンク、バッファは触るべきではない
    }
    alive_l = set(initial_S_map.keys())

    sorted_members = sorted(member_nodes)
    initial_theta = np.array([initial_theta_map[n] for n in sorted_members])
    initial_S = {
        link: s for link, s in initial_S_map.items()
        if link.issubset(member_nodes)
    }

    buf = CidSelfBuffer(
        cid_id=42,
        member_nodes=member_nodes,
        birth_step=birth_step,
        initial_theta=initial_theta,
        initial_S=initial_S,
    )

    return buf, initial_theta_map, initial_S_map, alive_l


# ---------------------------------------------------------------------------
# テスト本体
# ---------------------------------------------------------------------------

def test_init_basic():
    buf, _, _, _ = make_fixture()
    assert buf.cid_id == 42
    assert buf.n_core == 3
    assert buf.sorted_member_list == [10, 20, 30]
    assert buf.birth_step == 100
    assert buf.fetch_count == 0
    assert buf.last_fetch_step is None
    assert buf.match_history == []
    assert buf.divergence_log == []
    assert np.allclose(buf.theta_birth, [1.0, 2.0, 3.0])
    assert np.allclose(buf.theta_current, buf.theta_birth)
    assert not buf.missing_flags.any()
    print("PASS test_init_basic")


def test_read_own_state_no_change():
    """生誕時と同じ state を Fetch → 全一致、divergence=0。"""
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)

    ok = buf.read_own_state(state, alive_l, current_step=150)
    assert ok is True
    assert buf.fetch_count == 1
    assert buf.last_fetch_step == 150
    assert len(buf.match_history) == 1

    h = buf.match_history[0]
    assert h["step"] == 150
    assert h["node_match_ratio"] == 1.0
    assert h["link_match_ratio"] == 1.0
    assert all(h["node_matches"])

    d = buf.divergence_log[-1]
    assert d["step"] == 150
    assert abs(d["theta_diff_norm"]) < 1e-12
    assert abs(d["link_match_ratio"] - 1.0) < 1e-12
    print("PASS test_read_own_state_no_change")


def test_read_own_state_with_drift():
    """theta が変化 → node_match_ratio < 1、divergence > 0。"""
    buf, theta_map, S_map, alive_l = make_fixture()

    drifted_theta = dict(theta_map)
    drifted_theta[10] = 1.5  # +0.5 (超えてる)
    drifted_theta[20] = 2.0  # 同一
    drifted_theta[30] = 3.0 + 1e-9  # tolerance 内

    state = make_dummy_state(drifted_theta, S_map)
    buf.read_own_state(state, alive_l, current_step=200)

    h = buf.match_history[0]
    # node 10 不一致, node 20, 30 一致 → 2/3
    assert abs(h["node_match_ratio"] - (2.0 / 3.0)) < 1e-12
    assert h["link_match_ratio"] == 1.0

    d = buf.divergence_log[-1]
    assert abs(d["theta_diff_norm"] - 0.5) < 1e-5
    print("PASS test_read_own_state_with_drift")


def test_read_own_state_link_death():
    """メンバー内リンクが 1 本消える → link_match_ratio 低下。"""
    buf, theta_map, S_map, alive_l = make_fixture()

    dead_alive_l = set(alive_l)
    dead_alive_l.discard(frozenset({10, 20}))  # 1 本消す

    state = make_dummy_state(theta_map, S_map)
    buf.read_own_state(state, dead_alive_l, current_step=250)

    h = buf.match_history[0]
    # S_birth に 3 本、うち 2 本だけ一致 → 2/3
    assert abs(h["link_match_ratio"] - (2.0 / 3.0)) < 1e-12
    assert h["node_match_ratio"] == 1.0
    print("PASS test_read_own_state_link_death")


def test_iter_member_links_excludes_outside():
    """メンバー外リンクを Fetch しない: S_current にメンバー外リンクが入らない。"""
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)

    buf.read_own_state(state, alive_l, current_step=300)

    external_link = frozenset({10, 99})
    assert external_link not in buf.S_current
    assert external_link in alive_l  # alive_l には存在する (念のため)
    print("PASS test_iter_member_links_excludes_outside")


def make_fixture_tuple_keys():
    """
    v9.14 engine の実表現 (tuple キー、ndarray theta) で fixture を構築。
    CidSelfBuffer が両方の表現に耐えることを確認するためのテスト用。
    """
    member_nodes = frozenset({10, 20, 30})
    birth_step = 100

    # state.theta は np.ndarray (node id で直接 index)
    theta_arr = np.zeros(100)
    theta_arr[10] = 1.0
    theta_arr[20] = 2.0
    theta_arr[30] = 3.0
    theta_arr[99] = 999.0

    # state.S は tuple キー (i<j)
    S_map = {
        (10, 20): 0.5,
        (10, 30): 0.6,
        (20, 30): 0.7,
        (10, 99): 0.9,  # メンバー外リンク
    }
    alive_l = set(S_map.keys())

    sorted_members = sorted(member_nodes)
    initial_theta = np.array([theta_arr[n] for n in sorted_members])
    initial_S = {
        link: s for link, s in S_map.items()
        if all(n in member_nodes for n in link)
    }

    buf = CidSelfBuffer(
        cid_id=42,
        member_nodes=member_nodes,
        birth_step=birth_step,
        initial_theta=initial_theta,
        initial_S=initial_S,
    )

    return buf, theta_arr, S_map, alive_l


def test_tuple_keys_compatibility():
    """engine 実表現 (tuple キー、ndarray theta) で Fetch が正しく動作する。"""
    buf, theta_arr, S_map, alive_l = make_fixture_tuple_keys()

    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    ok = buf.read_own_state(state, alive_l, current_step=150)
    assert ok is True
    assert buf.fetch_count == 1

    # S_current にはメンバー内 tuple キーのみ
    assert (10, 20) in buf.S_current
    assert (10, 30) in buf.S_current
    assert (20, 30) in buf.S_current
    assert (10, 99) not in buf.S_current  # メンバー外は除外

    h = buf.match_history[0]
    assert h["node_match_ratio"] == 1.0
    assert h["link_match_ratio"] == 1.0
    print("PASS test_tuple_keys_compatibility")


def test_tuple_keys_link_death():
    """tuple キー表現で、メンバー内リンク 1 本が消える → link_match_ratio 低下。"""
    buf, theta_arr, S_map, alive_l = make_fixture_tuple_keys()

    dead_alive_l = set(alive_l)
    dead_alive_l.discard((10, 20))

    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    buf.read_own_state(state, dead_alive_l, current_step=200)

    h = buf.match_history[0]
    # S_birth に 3 本、うち (10,20) が alive_l から消えた → 不一致 1 本
    assert abs(h["link_match_ratio"] - (2.0 / 3.0)) < 1e-12
    print("PASS test_tuple_keys_link_death")


def test_multiple_fetches():
    """複数回 Fetch: match_history / divergence_log が蓄積される。"""
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)

    for step in [150, 200, 250, 300]:
        buf.read_own_state(state, alive_l, current_step=step)

    assert buf.fetch_count == 4
    assert buf.last_fetch_step == 300
    assert len(buf.match_history) == 4
    assert len(buf.divergence_log) == 4
    assert [h["step"] for h in buf.match_history] == [150, 200, 250, 300]
    print("PASS test_multiple_fetches")


def test_a_observer_summary_empty():
    buf, _, _, _ = make_fixture()
    summary = buf._a_observer_get_summary()
    assert summary["fetch_count"] == 0
    assert summary["node_match_ratio_mean"] is None
    assert summary["link_match_ratio_mean"] is None
    assert summary["divergence_norm_final"] is None
    print("PASS test_a_observer_summary_empty")


def test_a_observer_summary_populated():
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)
    for step in [150, 200]:
        buf.read_own_state(state, alive_l, current_step=step)

    summary = buf._a_observer_get_summary()
    assert summary["fetch_count"] == 2
    assert summary["node_match_ratio_mean"] == 1.0
    assert summary["link_match_ratio_mean"] == 1.0
    assert abs(summary["divergence_norm_final"]) < 1e-12
    assert summary["last_fetch_step"] == 200
    print("PASS test_a_observer_summary_populated")


# ---------------------------------------------------------------------------
# A 側 read-only 性の検証 (最重要)
# ---------------------------------------------------------------------------

def test_a_observer_match_history_is_copy():
    """_a_observer_get_match_history の返り値を mutate しても内部に影響しない。"""
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)
    buf.read_own_state(state, alive_l, current_step=150)

    returned = buf._a_observer_get_match_history()
    assert len(returned) == 1

    # A 側で mutate を試みる
    returned.clear()
    returned.append({"spoofed": True})
    returned[0] if returned else None

    # B 内部の match_history が影響を受けていないことを確認
    assert len(buf.match_history) == 1
    assert "spoofed" not in buf.match_history[0]
    assert buf.match_history[0]["node_match_ratio"] == 1.0

    # 個別 dict の mutate も internal に反映されてはいけない
    returned2 = buf._a_observer_get_match_history()
    returned2[0]["node_match_ratio"] = -999.0
    assert buf.match_history[0]["node_match_ratio"] == 1.0
    print("PASS test_a_observer_match_history_is_copy")


def test_a_observer_snapshot_is_copy():
    """_a_observer_get_current_snapshot の theta / S を mutate しても内部に影響しない。"""
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)
    buf.read_own_state(state, alive_l, current_step=150)

    snap = buf._a_observer_get_current_snapshot()

    # numpy array を A 側で mutate
    snap["theta"][:] = -999.0
    snap["theta_birth"][:] = -999.0
    snap["missing_flags"][:] = True
    snap["S"].clear()
    snap["S"][frozenset({10, 20})] = -999.0

    # 内部が生きていることを確認
    assert np.allclose(buf.theta_current, [1.0, 2.0, 3.0])
    assert np.allclose(buf.theta_birth, [1.0, 2.0, 3.0])
    assert not buf.missing_flags.any()
    assert buf.S_current[frozenset({10, 20})] == 0.5
    print("PASS test_a_observer_snapshot_is_copy")


def test_a_observer_divergence_log_is_copy():
    """_a_observer_get_divergence_log の返り値を mutate しても内部に影響しない。"""
    buf, theta_map, S_map, alive_l = make_fixture()
    state = make_dummy_state(theta_map, S_map)
    buf.read_own_state(state, alive_l, current_step=150)
    buf.read_own_state(state, alive_l, current_step=200)

    returned = buf._a_observer_get_divergence_log()
    assert len(returned) == 2

    returned.clear()
    returned.append({"spoofed": True})

    assert len(buf.divergence_log) == 2
    assert "spoofed" not in buf.divergence_log[0]

    returned2 = buf._a_observer_get_divergence_log()
    returned2[0]["theta_diff_norm"] = -999.0
    assert abs(buf.divergence_log[0]["theta_diff_norm"]) < 1e-12
    print("PASS test_a_observer_divergence_log_is_copy")


# ---------------------------------------------------------------------------
# B の規約遵守: Q_remaining / Q を参照しない
# ---------------------------------------------------------------------------

def test_no_q_reference():
    """
    ソースコード (docstring 外) で Q_remaining / .Q 等への属性アクセスが
    発生していないことを AST で検証。

    docstring 中の「Q_remaining を参照しない」等の禁止事項文言は許容、
    実際の属性アクセス / 変数名としての使用のみを検出。
    """
    import ast
    import inspect

    import v915_cid_self_buffer as mod

    src = inspect.getsource(mod)
    tree = ast.parse(src)

    offending: list[str] = []

    for node in ast.walk(tree):
        # 属性アクセス: obj.Q_remaining, obj.q_remaining
        if isinstance(node, ast.Attribute):
            if node.attr in ("Q_remaining", "q_remaining"):
                offending.append(f"attribute access .{node.attr}")
        # 変数名として直接: Q_remaining = ..., or reading Q_remaining
        if isinstance(node, ast.Name):
            if node.id in ("Q_remaining", "q_remaining"):
                offending.append(f"name reference {node.id}")

    assert not offending, (
        f"Forbidden Q references in code: {offending}"
    )
    print("PASS test_no_q_reference")


# ---------------------------------------------------------------------------
# ドライバ
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_init_basic,
        test_read_own_state_no_change,
        test_read_own_state_with_drift,
        test_read_own_state_link_death,
        test_iter_member_links_excludes_outside,
        test_multiple_fetches,
        test_a_observer_summary_empty,
        test_a_observer_summary_populated,
        test_a_observer_match_history_is_copy,
        test_a_observer_snapshot_is_copy,
        test_a_observer_divergence_log_is_copy,
        test_no_q_reference,
        test_tuple_keys_compatibility,
        test_tuple_keys_link_death,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
            failures += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            failures += 1

    if failures == 0:
        print(f"\nAll {len(tests)} tests passed.")
        sys.exit(0)
    else:
        print(f"\n{failures}/{len(tests)} tests failed.")
        sys.exit(1)
