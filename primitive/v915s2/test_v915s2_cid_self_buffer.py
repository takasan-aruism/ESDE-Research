"""
v9.15 段階 2 Step 1 単体テスト: CidSelfBuffer

承認条件 (指示書 §7.1 Step 1):
  - read_on_event が 5 種別の event_type で正常動作
  - _coarse_event_type が E1/E2/E3 に正しくマップ
  - any_mismatch_ever が一度 True になれば以降 True を保持
  - mismatch_count_total が正しくカウント
  - last_mismatch_step が最新 mismatch step を保持
  - fetch_count_by_event / mismatch_count_by_event の dict が E1/E2/E3 キーで正しくカウント
  - A からのアクセスが read-only
  - read_own_state (段階 1 残存) が段階 2 event counter を汚染しないこと

実行: python test_v915s2_cid_self_buffer.py
"""

from __future__ import annotations

import sys
import types

import numpy as np

from v915s2_cid_self_buffer import CidSelfBuffer


def make_dummy_state(theta_map: dict, S_map: dict):
    state = types.SimpleNamespace()
    state.theta = dict(theta_map)
    state.S = dict(S_map)
    return state


# ---------------------------------------------------------------------------
# Fixture (tuple-key 表現 = v9.14 engine 実表現)
# ---------------------------------------------------------------------------

def make_fixture():
    member_nodes = frozenset({10, 20, 30})
    birth_step = 100

    # state.theta: ndarray (node id で index)
    theta_arr = np.zeros(100)
    theta_arr[10] = 1.0
    theta_arr[20] = 2.0
    theta_arr[30] = 3.0
    theta_arr[99] = 999.0

    # state.S: tuple キー (i<j)
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


# ---------------------------------------------------------------------------
# 初期化 / 基本構造
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

    # 段階 2 新規フィールド
    assert buf.any_mismatch_ever is False
    assert buf.mismatch_count_total == 0
    assert buf.last_mismatch_step is None
    assert buf.fetch_count_by_event == {"E1": 0, "E2": 0, "E3": 0}
    assert buf.mismatch_count_by_event == {"E1": 0, "E2": 0, "E3": 0}
    print("PASS test_init_basic")


# ---------------------------------------------------------------------------
# _coarse_event_type
# ---------------------------------------------------------------------------

def test_coarse_event_type_mapping():
    buf, _, _, _ = make_fixture()
    assert buf._coarse_event_type("E1_death") == "E1"
    assert buf._coarse_event_type("E1_birth") == "E1"
    assert buf._coarse_event_type("E2_rise") == "E2"
    assert buf._coarse_event_type("E2_fall") == "E2"
    assert buf._coarse_event_type("E3_contact") == "E3"

    try:
        buf._coarse_event_type("X9_something")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for unknown event_type")
    print("PASS test_coarse_event_type_mapping")


# ---------------------------------------------------------------------------
# read_on_event: 5 種別で動作
# ---------------------------------------------------------------------------

def test_read_on_event_all_types():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    for i, et in enumerate(
        ["E1_death", "E1_birth", "E2_rise", "E2_fall", "E3_contact"]
    ):
        ok = buf.read_on_event(state, alive_l, current_step=100 + i, event_type_full=et)
        assert ok is True, f"Expected True from read_on_event for {et}"
        h = buf.match_history[-1]
        assert h["event_type_full"] == et
        assert h["event_type_coarse"] == et.split("_")[0]
        # 変化なしなので mismatch は False
        assert h["any_mismatch"] is False
        assert "node_matches" in h and "link_matches" in h

    assert buf.fetch_count == 5
    assert buf.last_fetch_step == 104
    # E1 が 2 回、E2 が 2 回、E3 が 1 回
    assert buf.fetch_count_by_event == {"E1": 2, "E2": 2, "E3": 1}
    assert buf.mismatch_count_by_event == {"E1": 0, "E2": 0, "E3": 0}
    assert buf.any_mismatch_ever is False
    print("PASS test_read_on_event_all_types")


def test_read_on_event_with_drift_flags_mismatch():
    buf, theta_arr, S_map, alive_l = make_fixture()

    drifted = theta_arr.copy()
    drifted[10] = 1.5  # tolerance を超える変化
    state = types.SimpleNamespace()
    state.theta = drifted
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, current_step=200, event_type_full="E1_death")

    assert buf.any_mismatch_ever is True
    assert buf.mismatch_count_total == 1
    assert buf.last_mismatch_step == 200
    assert buf.mismatch_count_by_event["E1"] == 1
    assert buf.mismatch_count_by_event["E2"] == 0
    assert buf.mismatch_count_by_event["E3"] == 0

    h = buf.match_history[-1]
    assert h["any_mismatch"] is True
    # node 10 だけ不一致
    assert h["node_matches"] == [False, True, True]
    print("PASS test_read_on_event_with_drift_flags_mismatch")


# ---------------------------------------------------------------------------
# 3 点セット (any_mismatch_ever, mismatch_count_total, last_mismatch_step)
# ---------------------------------------------------------------------------

def test_any_mismatch_ever_sticky():
    """一度 True になったら、以降の一致 event でも False に戻らない。"""
    buf, theta_arr, S_map, alive_l = make_fixture()

    drifted = theta_arr.copy()
    drifted[10] = 1.5
    state_drift = types.SimpleNamespace()
    state_drift.theta = drifted
    state_drift.S = dict(S_map)

    state_same = types.SimpleNamespace()
    state_same.theta = theta_arr
    state_same.S = dict(S_map)

    buf.read_on_event(state_drift, alive_l, current_step=100, event_type_full="E1_death")
    assert buf.any_mismatch_ever is True

    # 以降、state を birth と同一に戻してから event 発火
    buf.theta_current = theta_arr.copy()  # 外部からは触らないが、初期状態に近付ける
    buf.read_on_event(state_same, alive_l, current_step=200, event_type_full="E2_rise")
    # state は birth と一致、でも any_mismatch_ever は True のまま
    assert buf.any_mismatch_ever is True
    print("PASS test_any_mismatch_ever_sticky")


def test_mismatch_count_only_on_actual_mismatch():
    """一致 event は mismatch_count をインクリメントしない。"""
    buf, theta_arr, S_map, alive_l = make_fixture()
    state_same = types.SimpleNamespace()
    state_same.theta = theta_arr
    state_same.S = dict(S_map)

    for i in range(5):
        buf.read_on_event(state_same, alive_l, current_step=100 + i, event_type_full="E1_death")

    assert buf.fetch_count == 5
    assert buf.mismatch_count_total == 0
    assert buf.any_mismatch_ever is False
    assert buf.last_mismatch_step is None

    # 1 回不一致にする
    drifted = theta_arr.copy()
    drifted[20] = 2.9
    state_drift = types.SimpleNamespace()
    state_drift.theta = drifted
    state_drift.S = dict(S_map)
    buf.read_on_event(state_drift, alive_l, current_step=200, event_type_full="E3_contact")

    assert buf.mismatch_count_total == 1
    assert buf.last_mismatch_step == 200
    assert buf.mismatch_count_by_event == {"E1": 0, "E2": 0, "E3": 1}
    print("PASS test_mismatch_count_only_on_actual_mismatch")


def test_last_mismatch_step_tracks_latest():
    buf, theta_arr, S_map, alive_l = make_fixture()

    drifted = theta_arr.copy()
    drifted[10] = 1.5
    state = types.SimpleNamespace()
    state.theta = drifted
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, current_step=100, event_type_full="E1_death")
    assert buf.last_mismatch_step == 100

    buf.read_on_event(state, alive_l, current_step=250, event_type_full="E2_rise")
    assert buf.last_mismatch_step == 250

    buf.read_on_event(state, alive_l, current_step=400, event_type_full="E3_contact")
    assert buf.last_mismatch_step == 400
    print("PASS test_last_mismatch_step_tracks_latest")


# ---------------------------------------------------------------------------
# 整合性: event 別カウンタの合計が全体カウントと一致
# ---------------------------------------------------------------------------

def test_event_counter_integrity():
    buf, theta_arr, S_map, alive_l = make_fixture()
    drifted = theta_arr.copy()
    drifted[10] = 1.5
    state_drift = types.SimpleNamespace()
    state_drift.theta = drifted
    state_drift.S = dict(S_map)
    state_same = types.SimpleNamespace()
    state_same.theta = theta_arr
    state_same.S = dict(S_map)

    buf.read_on_event(state_same,  alive_l, 101, "E1_death")
    buf.read_on_event(state_drift, alive_l, 102, "E1_birth")
    buf.read_on_event(state_same,  alive_l, 103, "E2_rise")
    buf.read_on_event(state_drift, alive_l, 104, "E2_fall")
    buf.read_on_event(state_drift, alive_l, 105, "E3_contact")

    # fetch_count 合計
    fe = buf.fetch_count_by_event
    assert fe["E1"] + fe["E2"] + fe["E3"] == buf.fetch_count
    assert buf.fetch_count == 5

    # mismatch_count 合計
    me = buf.mismatch_count_by_event
    assert me["E1"] + me["E2"] + me["E3"] == buf.mismatch_count_total
    # drift: 102 (E1_birth), 104 (E2_fall), 105 (E3_contact)
    assert buf.mismatch_count_total == 3
    assert me == {"E1": 1, "E2": 1, "E3": 1}
    print("PASS test_event_counter_integrity")


# ---------------------------------------------------------------------------
# link 死: any_mismatch フラグ、event 別カウンタ
# ---------------------------------------------------------------------------

def test_link_death_triggers_mismatch():
    buf, theta_arr, S_map, alive_l = make_fixture()
    dead_alive_l = set(alive_l)
    dead_alive_l.discard((10, 20))

    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)
    buf.read_on_event(state, dead_alive_l, 150, "E1_death")

    assert buf.any_mismatch_ever is True
    h = buf.match_history[-1]
    assert h["any_mismatch"] is True
    # S_birth に 3 本、うち (10,20) が alive_l から消えた → 1 本不一致
    assert h["link_matches"].count(False) == 1
    print("PASS test_link_death_triggers_mismatch")


def test_iter_member_links_excludes_outside():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, 300, "E2_rise")

    external_link = (10, 99)
    assert external_link not in buf.S_current
    assert external_link in alive_l
    print("PASS test_iter_member_links_excludes_outside")


# ---------------------------------------------------------------------------
# divergence_log: event_type を含む
# ---------------------------------------------------------------------------

def test_divergence_log_has_event_type():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, 150, "E1_death")
    buf.read_on_event(state, alive_l, 200, "E3_contact")

    log = buf._a_observer_get_divergence_log()
    assert len(log) == 2
    assert log[0]["event_type_full"] == "E1_death"
    assert log[0]["event_type_coarse"] == "E1"
    assert log[1]["event_type_full"] == "E3_contact"
    assert log[1]["event_type_coarse"] == "E3"
    # theta_diff_norm / link_match_ratio キーは段階 1 から継続
    assert "theta_diff_norm" in log[0]
    assert "link_match_ratio" in log[0]
    print("PASS test_divergence_log_has_event_type")


# ---------------------------------------------------------------------------
# A 側 summary (段階 2 フォーマット)
# ---------------------------------------------------------------------------

def test_a_observer_summary_empty():
    buf, _, _, _ = make_fixture()
    summary = buf._a_observer_get_summary()
    expected_keys = {
        "fetch_count", "last_fetch_step",
        "any_mismatch_ever", "mismatch_count_total", "last_mismatch_step",
        "fetch_count_e1", "fetch_count_e2", "fetch_count_e3",
        "mismatch_count_e1", "mismatch_count_e2", "mismatch_count_e3",
        "divergence_norm_final",
    }
    assert set(summary.keys()) == expected_keys
    assert summary["fetch_count"] == 0
    assert summary["any_mismatch_ever"] is False
    assert summary["mismatch_count_total"] == 0
    assert summary["fetch_count_e1"] == 0
    assert summary["fetch_count_e2"] == 0
    assert summary["fetch_count_e3"] == 0
    assert summary["mismatch_count_e1"] == 0
    assert summary["mismatch_count_e2"] == 0
    assert summary["mismatch_count_e3"] == 0
    assert summary["divergence_norm_final"] is None
    # 段階 1 の mean 系キーは廃止
    assert "node_match_ratio_mean" not in summary
    assert "link_match_ratio_mean" not in summary
    print("PASS test_a_observer_summary_empty")


def test_a_observer_summary_populated():
    buf, theta_arr, S_map, alive_l = make_fixture()
    drifted = theta_arr.copy()
    drifted[10] = 1.5
    state_drift = types.SimpleNamespace()
    state_drift.theta = drifted
    state_drift.S = dict(S_map)
    state_same = types.SimpleNamespace()
    state_same.theta = theta_arr
    state_same.S = dict(S_map)

    buf.read_on_event(state_same,  alive_l, 110, "E1_death")
    buf.read_on_event(state_drift, alive_l, 220, "E2_rise")
    buf.read_on_event(state_drift, alive_l, 330, "E3_contact")

    s = buf._a_observer_get_summary()
    assert s["fetch_count"] == 3
    assert s["last_fetch_step"] == 330
    assert s["any_mismatch_ever"] is True
    assert s["mismatch_count_total"] == 2
    assert s["last_mismatch_step"] == 330
    assert s["fetch_count_e1"] == 1
    assert s["fetch_count_e2"] == 1
    assert s["fetch_count_e3"] == 1
    assert s["mismatch_count_e1"] == 0
    assert s["mismatch_count_e2"] == 1
    assert s["mismatch_count_e3"] == 1
    assert s["divergence_norm_final"] is not None
    assert s["divergence_norm_final"] > 0
    print("PASS test_a_observer_summary_populated")


# ---------------------------------------------------------------------------
# A 側 read-only 性
# ---------------------------------------------------------------------------

def test_a_observer_match_history_is_copy():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)
    buf.read_on_event(state, alive_l, 150, "E1_death")

    returned = buf._a_observer_get_match_history()
    assert len(returned) == 1

    returned.clear()
    returned.append({"spoofed": True})

    assert len(buf.match_history) == 1
    assert "spoofed" not in buf.match_history[0]
    assert buf.match_history[0]["event_type_full"] == "E1_death"

    returned2 = buf._a_observer_get_match_history()
    returned2[0]["event_type_full"] = "X_spoofed"
    assert buf.match_history[0]["event_type_full"] == "E1_death"
    print("PASS test_a_observer_match_history_is_copy")


def test_a_observer_snapshot_is_copy():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)
    buf.read_on_event(state, alive_l, 150, "E2_rise")

    snap = buf._a_observer_get_current_snapshot()
    snap["theta"][:] = -999.0
    snap["theta_birth"][:] = -999.0
    snap["missing_flags"][:] = True
    snap["S"].clear()

    assert np.allclose(buf.theta_current, [1.0, 2.0, 3.0])
    assert np.allclose(buf.theta_birth, [1.0, 2.0, 3.0])
    assert not buf.missing_flags.any()
    assert buf.S_current[(10, 20)] == 0.5
    print("PASS test_a_observer_snapshot_is_copy")


def test_a_observer_divergence_log_is_copy():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)
    buf.read_on_event(state, alive_l, 150, "E1_death")
    buf.read_on_event(state, alive_l, 200, "E2_fall")

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
# 段階 1 残存の read_own_state は event counter を汚染しない
# ---------------------------------------------------------------------------

def test_read_own_state_does_not_affect_event_counters():
    """
    段階 1 残存の read_own_state が万一呼ばれても、段階 2 event 別カウンタ
    (fetch_count_by_event / mismatch_count_by_event) に影響しないことを確認。
    read_own_state 自体は fetch_count と divergence_log は更新する。
    """
    buf, theta_arr, S_map, alive_l = make_fixture()
    drifted = theta_arr.copy()
    drifted[10] = 1.5
    state = types.SimpleNamespace()
    state.theta = drifted
    state.S = dict(S_map)

    buf.read_own_state(state, alive_l, current_step=100)

    # fetch_count は増える (段階 1 互換)
    assert buf.fetch_count == 1
    # ただし event 別カウンタには影響しない (段階 2 の責務)
    assert buf.fetch_count_by_event == {"E1": 0, "E2": 0, "E3": 0}
    assert buf.mismatch_count_by_event == {"E1": 0, "E2": 0, "E3": 0}
    # any_mismatch_ever / mismatch_count_total も段階 2 固有 → 更新しない
    assert buf.any_mismatch_ever is False
    assert buf.mismatch_count_total == 0
    print("PASS test_read_own_state_does_not_affect_event_counters")


# ---------------------------------------------------------------------------
# B の規約遵守: Q_remaining を参照しない
# ---------------------------------------------------------------------------

def test_no_q_reference():
    import ast
    import inspect

    import v915s2_cid_self_buffer as mod

    src = inspect.getsource(mod)
    tree = ast.parse(src)

    offending: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in ("Q_remaining", "q_remaining"):
                offending.append(f"attribute access .{node.attr}")
        if isinstance(node, ast.Name):
            if node.id in ("Q_remaining", "q_remaining"):
                offending.append(f"name reference {node.id}")

    assert not offending, f"Forbidden Q references: {offending}"
    print("PASS test_no_q_reference")


# ---------------------------------------------------------------------------
# ドライバ
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_init_basic,
        test_coarse_event_type_mapping,
        test_read_on_event_all_types,
        test_read_on_event_with_drift_flags_mismatch,
        test_any_mismatch_ever_sticky,
        test_mismatch_count_only_on_actual_mismatch,
        test_last_mismatch_step_tracks_latest,
        test_event_counter_integrity,
        test_link_death_triggers_mismatch,
        test_iter_member_links_excludes_outside,
        test_divergence_log_has_event_type,
        test_a_observer_summary_empty,
        test_a_observer_summary_populated,
        test_a_observer_match_history_is_copy,
        test_a_observer_snapshot_is_copy,
        test_a_observer_divergence_log_is_copy,
        test_read_own_state_does_not_affect_event_counters,
        test_no_q_reference,
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
