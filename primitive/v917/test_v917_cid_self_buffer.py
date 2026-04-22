"""
v9.16 段階 3 Step 1 + 2 単体テスト: CidSelfBuffer

段階 2 から継続するテスト (18):
  - read_on_event が 5 種別の event_type で正常動作
  - _coarse_event_type が E1/E2/E3 に正しくマップ
  - any_mismatch_ever が一度 True になれば以降 True を保持
  - mismatch_count_total が正しくカウント
  - last_mismatch_step が最新 mismatch step を保持
  - fetch_count_by_event / mismatch_count_by_event の dict が E1/E2/E3 キーで正しくカウント
  - A からのアクセスが read-only
  - read_own_state (段階 1 残存) が段階 2 event counter を汚染しないこと

段階 3 新規テスト (Step 1 サンプリング基本メソッド):
  - _compute_age_factor の境界値 (Q0=0, Q_remaining=0, full, half)
  - _compute_n_observed の境界値 (age_factor=0, 0.5, 1.0)
  - _build_local_rng の決定論性 (同入力 → 同乱数列)
  - _sample_observed_indices の境界 (0 件, 全件, 部分)

実行: python test_v917_cid_self_buffer.py
"""

from __future__ import annotations

import sys
import types

import numpy as np

from v917_cid_self_buffer import CidSelfBuffer


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
        Q0=10,
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
        ok = buf.read_on_event(state, alive_l, current_step=100 + i, event_type_full=et, Q_remaining=10, seed=0)
        assert ok is True, f"Expected True from read_on_event for {et}"
        h = buf.match_history[-1]
        assert h["event_type_full"] == et
        assert h["event_type_coarse"] == et.split("_")[0]
        # 変化なしなので mismatch は False
        assert h["any_mismatch"] is False
        # 段階 3: node_status に n_core 要素、全て match (age_factor=1.0)
        assert "node_status" in h
        assert len(h["node_status"]) == buf.n_core
        assert all(v == "match" for v in h["node_status"].values())
        assert "observed_indices" in h
        assert h["n_observed"] == buf.n_core

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

    buf.read_on_event(state, alive_l, current_step=200, event_type_full="E1_death", Q_remaining=10, seed=0)

    assert buf.any_mismatch_ever is True
    assert buf.mismatch_count_total == 1
    assert buf.last_mismatch_step == 200
    assert buf.mismatch_count_by_event["E1"] == 1
    assert buf.mismatch_count_by_event["E2"] == 0
    assert buf.mismatch_count_by_event["E3"] == 0

    h = buf.match_history[-1]
    assert h["any_mismatch"] is True
    # 段階 3: sorted_member_list = [10, 20, 30] → index 0 が node 10
    # age_factor=1.0 で全観察、node 0 のみ mismatch、残りは match
    assert h["n_observed"] == buf.n_core
    assert h["node_status"][0] == "mismatch"
    assert h["node_status"][1] == "match"
    assert h["node_status"][2] == "match"
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

    buf.read_on_event(state_drift, alive_l, current_step=100, event_type_full="E1_death", Q_remaining=10, seed=0)
    assert buf.any_mismatch_ever is True

    # 以降、state を birth と同一に戻してから event 発火
    buf.theta_current = theta_arr.copy()  # 外部からは触らないが、初期状態に近付ける
    buf.read_on_event(state_same, alive_l, current_step=200, event_type_full="E2_rise", Q_remaining=10, seed=0)
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
        buf.read_on_event(state_same, alive_l, current_step=100 + i, event_type_full="E1_death", Q_remaining=10, seed=0)

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
    buf.read_on_event(state_drift, alive_l, current_step=200, event_type_full="E3_contact", Q_remaining=10, seed=0)

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

    buf.read_on_event(state, alive_l, current_step=100, event_type_full="E1_death", Q_remaining=10, seed=0)
    assert buf.last_mismatch_step == 100

    buf.read_on_event(state, alive_l, current_step=250, event_type_full="E2_rise", Q_remaining=10, seed=0)
    assert buf.last_mismatch_step == 250

    buf.read_on_event(state, alive_l, current_step=400, event_type_full="E3_contact", Q_remaining=10, seed=0)
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

    buf.read_on_event(state_same,  alive_l, 101, "E1_death", Q_remaining=10, seed=0)
    buf.read_on_event(state_drift, alive_l, 102, "E1_birth", Q_remaining=10, seed=0)
    buf.read_on_event(state_same,  alive_l, 103, "E2_rise", Q_remaining=10, seed=0)
    buf.read_on_event(state_drift, alive_l, 104, "E2_fall", Q_remaining=10, seed=0)
    buf.read_on_event(state_drift, alive_l, 105, "E3_contact", Q_remaining=10, seed=0)

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
# link 死: 段階 3 では any_mismatch には不寄与、divergence_log にのみ反映
# ---------------------------------------------------------------------------

def test_link_death_does_not_trigger_mismatch_stage3():
    """段階 3: リンク死のみでは any_mismatch=False。
    リンクは divergence_log の link_match_ratio にのみ反映される
    (指示書 §5 pseudocode: any_mismatch は observed ノードのみで判定)。
    """
    buf, theta_arr, S_map, alive_l = make_fixture()
    dead_alive_l = set(alive_l)
    dead_alive_l.discard((10, 20))

    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)
    buf.read_on_event(state, dead_alive_l, 150, "E1_death", Q_remaining=10, seed=0)

    # ノードは全 match のため any_mismatch=False
    assert buf.any_mismatch_ever is False
    h = buf.match_history[-1]
    assert h["any_mismatch"] is False
    assert all(v == "match" for v in h["node_status"].values())

    # ただしリンク死は divergence_log に反映される (3 本中 1 本欠損 → 2/3)
    div = buf._a_observer_get_divergence_log()
    assert len(div) == 1
    assert abs(div[0]["link_match_ratio"] - 2.0 / 3.0) < 1e-9
    print("PASS test_link_death_does_not_trigger_mismatch_stage3")


def test_iter_member_links_excludes_outside():
    buf, theta_arr, S_map, alive_l = make_fixture()
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, 300, "E2_rise", Q_remaining=10, seed=0)

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

    buf.read_on_event(state, alive_l, 150, "E1_death", Q_remaining=10, seed=0)
    buf.read_on_event(state, alive_l, 200, "E3_contact", Q_remaining=10, seed=0)

    log = buf._a_observer_get_divergence_log()
    assert len(log) == 2
    assert log[0]["event_type_full"] == "E1_death"
    assert log[0]["event_type_coarse"] == "E1"
    assert log[1]["event_type_full"] == "E3_contact"
    assert log[1]["event_type_coarse"] == "E3"
    # 段階 3: theta_diff_norm_all / theta_diff_norm_observed / link_match_ratio
    assert "theta_diff_norm_all" in log[0]
    assert "theta_diff_norm_observed" in log[0]
    assert "theta_diff_norm_observed_normalized" in log[0]
    assert "link_match_ratio" in log[0]
    assert "age_factor" in log[0]
    assert "n_observed" in log[0]
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
        # 段階 3 新規
        "Q0", "avg_age_factor", "min_age_factor", "age_factor_final",
        "total_observed_count", "total_missing_count",
        "total_match_obs_count", "total_mismatch_obs_count",
        "final_missing_fraction", "divergence_norm_observed_final",
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
    # 段階 3: Q0 / 統計
    assert summary["Q0"] == 10
    assert summary["avg_age_factor"] is None
    assert summary["age_factor_final"] is None
    assert summary["total_observed_count"] == 0
    assert summary["total_missing_count"] == 0
    assert summary["final_missing_fraction"] == 0.0
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

    buf.read_on_event(state_same,  alive_l, 110, "E1_death", Q_remaining=10, seed=0)
    buf.read_on_event(state_drift, alive_l, 220, "E2_rise", Q_remaining=10, seed=0)
    buf.read_on_event(state_drift, alive_l, 330, "E3_contact", Q_remaining=10, seed=0)

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
    buf.read_on_event(state, alive_l, 150, "E1_death", Q_remaining=10, seed=0)

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
    buf.read_on_event(state, alive_l, 150, "E2_rise", Q_remaining=10, seed=0)

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
    buf.read_on_event(state, alive_l, 150, "E1_death", Q_remaining=10, seed=0)
    buf.read_on_event(state, alive_l, 200, "E2_fall", Q_remaining=10, seed=0)

    returned = buf._a_observer_get_divergence_log()
    assert len(returned) == 2

    returned.clear()
    returned.append({"spoofed": True})

    assert len(buf.divergence_log) == 2
    assert "spoofed" not in buf.divergence_log[0]

    returned2 = buf._a_observer_get_divergence_log()
    returned2[0]["theta_diff_norm_all"] = -999.0
    # 内部は不変 (Fetch 直後で state==birth なので 0)
    assert abs(buf.divergence_log[0]["theta_diff_norm_all"]) < 1e-12
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
# 段階 3 新規テスト: read_on_event サンプリング挙動 (§8.2)
# ---------------------------------------------------------------------------

def _make_larger_fixture(n_core: int = 6, Q0: int = 10):
    """サンプリングの部分観察が可視化できる広めの fixture。"""
    member_nodes = frozenset(range(n_core))
    theta_arr = np.zeros(n_core + 10)
    for i in range(n_core):
        theta_arr[i] = float(i)

    S_map = {
        (i, j): 0.5 for i in range(n_core) for j in range(i + 1, n_core)
    }
    alive_l = set(S_map.keys())

    sorted_members = sorted(member_nodes)
    initial_theta = np.array([theta_arr[n] for n in sorted_members])
    initial_S = dict(S_map)

    buf = CidSelfBuffer(
        cid_id=7,
        member_nodes=member_nodes,
        birth_step=0,
        initial_theta=initial_theta,
        initial_S=initial_S,
        Q0=Q0,
    )
    return buf, theta_arr, S_map, alive_l


def test_read_on_event_n_observed_matches_sample():
    """observed_indices の要素数 == n_observed。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    # Q_remaining=5 → age_factor=0.5 → n_observed=round(3.0)=3
    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=5, seed=0)
    h = buf.match_history[-1]
    assert h["n_observed"] == 3
    assert len(h["observed_indices"]) == 3
    assert all(0 <= i < buf.n_core for i in h["observed_indices"])
    assert len(set(h["observed_indices"])) == 3  # 重複なし
    print("PASS test_read_on_event_n_observed_matches_sample")


def test_read_on_event_node_status_three_values():
    """観察ノードに match/mismatch、未観察ノードに missing が現れる。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    drifted = theta_arr.copy()
    # 一部ノードに drift を加える (sorted index 0,1,2 全てに drift)
    drifted[0] = 99.0
    drifted[1] = 99.0
    drifted[2] = 99.0
    state = types.SimpleNamespace()
    state.theta = drifted
    state.S = dict(S_map)

    # age_factor=0.5 → n_observed=3、missing=3
    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=5, seed=0)
    h = buf.match_history[-1]
    ns = h["node_status"]
    assert set(ns.values()) <= {"match", "mismatch", "missing"}
    # missing は n_core - n_observed 個
    assert sum(1 for v in ns.values() if v == "missing") == 3
    # observed は n_observed 個
    assert sum(1 for v in ns.values() if v != "missing") == 3
    print("PASS test_read_on_event_node_status_three_values")


def test_read_on_event_missing_does_not_trigger_mismatch():
    """未観察ノード (missing) は any_mismatch_ever に影響しない。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)

    # 全ノードを drift させる (実体は全 mismatch のはず)
    drifted = theta_arr.copy()
    for i in range(6):
        drifted[i] = 99.0 + i
    state = types.SimpleNamespace()
    state.theta = drifted
    state.S = dict(S_map)

    # Q_remaining=0 → age_factor=0 → n_observed=0 (完全失明)
    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=0, seed=0)
    h = buf.match_history[-1]
    assert h["n_observed"] == 0
    # 全 node が missing、any_mismatch は False (観察していないので判定不能)
    assert all(v == "missing" for v in h["node_status"].values())
    assert h["any_mismatch"] is False
    assert buf.any_mismatch_ever is False
    assert buf.mismatch_count_total == 0
    print("PASS test_read_on_event_missing_does_not_trigger_mismatch")


def test_read_on_event_missing_flags_cumulative():
    """missing_flags は一度 True になったら True を保持 (cumulative)。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    # 1 回目: n_observed=3 → 3 node が missing
    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=5, seed=0)
    flags_after_first = buf.missing_flags.copy()
    first_missing_count = int(flags_after_first.sum())
    assert first_missing_count == 3

    # 2 回目: Q_remaining=10 → age_factor=1.0 → 全観察、新たな missing は無い
    # しかし既存の missing_flags は True のまま保持されるべき
    buf.read_on_event(state, alive_l, 101, "E1_birth", Q_remaining=10, seed=0)
    # 1 回目で True になった flag は消えない (cumulative)
    assert np.all(buf.missing_flags >= flags_after_first)
    # 2 回目は全観察なので新規 True は追加されない
    assert int(buf.missing_flags.sum()) == first_missing_count
    print("PASS test_read_on_event_missing_flags_cumulative")


def test_read_on_event_negative_q_safe():
    """Q_remaining が負でもクラッシュせず age_factor=0 扱い。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    ok = buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=-5, seed=0)
    assert ok is True
    h = buf.match_history[-1]
    assert h["age_factor"] == 0.0
    assert h["n_observed"] == 0
    print("PASS test_read_on_event_negative_q_safe")


def test_read_on_event_counts_observed_only():
    """total_match_obs_count + total_mismatch_obs_count == total_observed_count。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    drifted = theta_arr.copy()
    drifted[0] = 99.0
    drifted[1] = 99.0
    state_drift = types.SimpleNamespace()
    state_drift.theta = drifted
    state_drift.S = dict(S_map)
    state_same = types.SimpleNamespace()
    state_same.theta = theta_arr
    state_same.S = dict(S_map)

    for i, (st, q) in enumerate(
        [(state_same, 10), (state_drift, 7), (state_same, 4), (state_drift, 2)]
    ):
        buf.read_on_event(st, alive_l, 100 + i, "E2_rise", Q_remaining=q, seed=42)

    obs_total = buf.total_match_obs_count + buf.total_mismatch_obs_count
    assert obs_total == buf.total_observed_count
    # 観察 + 欠損 = 全 Fetch × n_core
    assert (
        buf.total_observed_count + buf.total_missing_count
        == buf.fetch_count * buf.n_core
    )
    print("PASS test_read_on_event_counts_observed_only")


def test_read_on_event_deterministic():
    """同じ (seed, step, event_type, Q_remaining) で同じ observed_indices。"""
    buf1, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    buf2, _, _, _ = _make_larger_fixture(n_core=6, Q0=10)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    buf1.read_on_event(state, alive_l, 200, "E2_rise", Q_remaining=5, seed=42)
    buf2.read_on_event(state, alive_l, 200, "E2_rise", Q_remaining=5, seed=42)
    h1 = buf1.match_history[-1]
    h2 = buf2.match_history[-1]
    assert h1["observed_indices"] == h2["observed_indices"]
    assert h1["node_status"] == h2["node_status"]
    print("PASS test_read_on_event_deterministic")


def test_read_on_event_q0_zero_always_blind():
    """Q0=0 (b_gen=inf / <=0 由来) の cid は age_factor 常に 0、全 missing。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=0)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    # Q_remaining に何を渡しても n_observed=0 となる
    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=9999, seed=0)
    h = buf.match_history[-1]
    assert h["age_factor"] == 0.0
    assert h["n_observed"] == 0
    assert buf.total_missing_count == buf.n_core
    print("PASS test_read_on_event_q0_zero_always_blind")


def test_divergence_log_both_all_and_observed():
    """divergence_log に theta_diff_norm_all と theta_diff_norm_observed 両方が入る。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    drifted = theta_arr.copy()
    drifted[0] = 99.0
    state = types.SimpleNamespace()
    state.theta = drifted
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=5, seed=0)
    d = buf.divergence_log[-1]
    assert "theta_diff_norm_all" in d
    assert "theta_diff_norm_observed" in d
    assert "theta_diff_norm_observed_normalized" in d
    # 全ノード版は常に drift を検出
    assert d["theta_diff_norm_all"] > 0
    # 観察ノード版は n_observed>0 なら計算される
    assert d["n_observed"] > 0
    assert d["theta_diff_norm_observed"] >= 0
    # normalized は observed を n_observed で割った値
    expected_norm = d["theta_diff_norm_observed"] / d["n_observed"]
    assert abs(d["theta_diff_norm_observed_normalized"] - expected_norm) < 1e-12
    print("PASS test_divergence_log_both_all_and_observed")


def test_divergence_log_observed_zero_when_blind():
    """n_observed=0 のとき theta_diff_norm_observed は 0.0。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    buf.read_on_event(state, alive_l, 100, "E1_death", Q_remaining=0, seed=0)
    d = buf.divergence_log[-1]
    assert d["n_observed"] == 0
    assert d["theta_diff_norm_observed"] == 0.0
    assert d["theta_diff_norm_observed_normalized"] == 0.0
    print("PASS test_divergence_log_observed_zero_when_blind")


def test_age_factor_history_recorded():
    """age_factor_history が event ごとに追記される。"""
    buf, theta_arr, S_map, alive_l = _make_larger_fixture(n_core=6, Q0=10)
    state = types.SimpleNamespace()
    state.theta = theta_arr
    state.S = dict(S_map)

    for q in [10, 8, 5, 2, 0]:
        buf.read_on_event(state, alive_l, 100 + q, "E1_death", Q_remaining=q, seed=0)

    assert len(buf.age_factor_history) == 5
    af = [e["age_factor"] for e in buf.age_factor_history]
    assert af == [1.0, 0.8, 0.5, 0.2, 0.0]
    print("PASS test_age_factor_history_recorded")


# ---------------------------------------------------------------------------
# B の規約遵守: 段階 3 で Q_remaining を読むが書き換えない
# ---------------------------------------------------------------------------

def test_no_q_write():
    """Q_remaining / Q0 への代入 (書き換え) が無いことを AST で確認。

    段階 3 では Q_remaining の読みは許可されるが、消費 / 書き換えは禁止。
    """
    import ast
    import inspect

    import v917_cid_self_buffer as mod

    src = inspect.getsource(mod)
    tree = ast.parse(src)

    offending: list = []
    for node in ast.walk(tree):
        # self.Q_remaining = ... や self.Q0 = ... の代入のみ検査
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name):
                    if tgt.value.id == "self" and tgt.attr in ("Q_remaining", "q_remaining"):
                        offending.append(f"assignment self.{tgt.attr}")
        if isinstance(node, ast.AugAssign):
            tgt = node.target
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name):
                if tgt.value.id == "self" and tgt.attr in ("Q_remaining", "q_remaining"):
                    offending.append(f"aug-assignment self.{tgt.attr}")

    assert not offending, f"Forbidden Q write operations: {offending}"
    print("PASS test_no_q_write")


# ---------------------------------------------------------------------------
# 段階 3 新規テスト: Q0 初期化
# ---------------------------------------------------------------------------

def test_q0_stored():
    buf, _, _, _ = make_fixture()
    assert buf.Q0 == 10, f"Q0 should be 10, got {buf.Q0}"
    print("PASS test_q0_stored")


def test_q0_negative_coerced_to_zero():
    member = frozenset({1, 2})
    initial_theta = np.array([0.0, 0.0])
    buf = CidSelfBuffer(
        cid_id=1, member_nodes=member, birth_step=0,
        initial_theta=initial_theta, initial_S={}, Q0=-5,
    )
    assert buf.Q0 == 0, f"Negative Q0 should coerce to 0, got {buf.Q0}"
    print("PASS test_q0_negative_coerced_to_zero")


def test_q0_none_coerced_to_zero():
    member = frozenset({1, 2})
    initial_theta = np.array([0.0, 0.0])
    buf = CidSelfBuffer(
        cid_id=1, member_nodes=member, birth_step=0,
        initial_theta=initial_theta, initial_S={}, Q0=None,
    )
    assert buf.Q0 == 0
    print("PASS test_q0_none_coerced_to_zero")


# ---------------------------------------------------------------------------
# 段階 3 新規テスト: _compute_age_factor
# ---------------------------------------------------------------------------

def test_compute_age_factor_full():
    buf, _, _, _ = make_fixture()  # Q0=10
    assert buf._compute_age_factor(Q_remaining=10) == 1.0
    print("PASS test_compute_age_factor_full")


def test_compute_age_factor_half():
    buf, _, _, _ = make_fixture()  # Q0=10
    assert buf._compute_age_factor(Q_remaining=5) == 0.5
    print("PASS test_compute_age_factor_half")


def test_compute_age_factor_zero():
    buf, _, _, _ = make_fixture()  # Q0=10
    assert buf._compute_age_factor(Q_remaining=0) == 0.0
    print("PASS test_compute_age_factor_zero")


def test_compute_age_factor_q0_zero():
    """Q0=0 は安全に 0.0 を返す (floor(B_Gen)=0 or b_gen=inf)。"""
    member = frozenset({1, 2})
    initial_theta = np.array([0.0, 0.0])
    buf = CidSelfBuffer(
        cid_id=1, member_nodes=member, birth_step=0,
        initial_theta=initial_theta, initial_S={}, Q0=0,
    )
    assert buf._compute_age_factor(Q_remaining=5) == 0.0
    print("PASS test_compute_age_factor_q0_zero")


def test_compute_age_factor_clamp_negative_q():
    """Q_remaining が負でも 0.0 に clamp (理論上は起きないが保護)。"""
    buf, _, _, _ = make_fixture()  # Q0=10
    assert buf._compute_age_factor(Q_remaining=-1) == 0.0
    print("PASS test_compute_age_factor_clamp_negative_q")


def test_compute_age_factor_clamp_overflow_q():
    """Q_remaining > Q0 でも 1.0 に clamp (理論上は起きないが保護)。"""
    buf, _, _, _ = make_fixture()  # Q0=10
    assert buf._compute_age_factor(Q_remaining=20) == 1.0
    print("PASS test_compute_age_factor_clamp_overflow_q")


# ---------------------------------------------------------------------------
# 段階 3 新規テスト: _compute_n_observed
# ---------------------------------------------------------------------------

def test_compute_n_observed_full():
    buf, _, _, _ = make_fixture()  # n_core=3
    assert buf._compute_n_observed(1.0) == 3
    print("PASS test_compute_n_observed_full")


def test_compute_n_observed_zero():
    buf, _, _, _ = make_fixture()  # n_core=3
    assert buf._compute_n_observed(0.0) == 0
    print("PASS test_compute_n_observed_zero")


def test_compute_n_observed_half():
    """age_factor=0.5, n_core=3 → round(1.5)=2 (banker's rounding)。"""
    buf, _, _, _ = make_fixture()  # n_core=3
    n = buf._compute_n_observed(0.5)
    # Python: round(1.5) == 2 (banker's: 0.5 → 最近接偶数)
    assert n == 2, f"Expected 2 (banker's rounding), got {n}"
    print("PASS test_compute_n_observed_half")


def test_compute_n_observed_monotonic():
    """age_factor が増えると n_observed が単調非減少。"""
    buf, _, _, _ = make_fixture()  # n_core=3
    prev = 0
    for af in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
        n = buf._compute_n_observed(af)
        assert n >= prev, f"monotonic violated at af={af}: {prev}->{n}"
        assert 0 <= n <= buf.n_core
        prev = n
    print("PASS test_compute_n_observed_monotonic")


# ---------------------------------------------------------------------------
# 段階 3 新規テスト: _build_local_rng (決定論)
# ---------------------------------------------------------------------------

def test_build_local_rng_deterministic():
    buf, _, _, _ = make_fixture()
    r1 = buf._build_local_rng(seed=42, current_step=100, event_type_full="E1_death")
    r2 = buf._build_local_rng(seed=42, current_step=100, event_type_full="E1_death")
    # 同じ入力 → 同じ乱数列
    seq1 = [r1.random() for _ in range(10)]
    seq2 = [r2.random() for _ in range(10)]
    assert seq1 == seq2, "Identical inputs must yield identical RNG streams"
    print("PASS test_build_local_rng_deterministic")


def test_build_local_rng_different_seeds():
    buf, _, _, _ = make_fixture()
    r1 = buf._build_local_rng(seed=1, current_step=100, event_type_full="E1_death")
    r2 = buf._build_local_rng(seed=2, current_step=100, event_type_full="E1_death")
    seq1 = [r1.random() for _ in range(10)]
    seq2 = [r2.random() for _ in range(10)]
    assert seq1 != seq2, "Different seeds should yield different RNG streams"
    print("PASS test_build_local_rng_different_seeds")


def test_build_local_rng_different_event_types():
    buf, _, _, _ = make_fixture()
    r1 = buf._build_local_rng(seed=42, current_step=100, event_type_full="E1_death")
    r2 = buf._build_local_rng(seed=42, current_step=100, event_type_full="E2_rise")
    seq1 = [r1.random() for _ in range(10)]
    seq2 = [r2.random() for _ in range(10)]
    assert seq1 != seq2, "Different event types should yield different RNG streams"
    print("PASS test_build_local_rng_different_event_types")


# ---------------------------------------------------------------------------
# 段階 3 新規テスト: _sample_observed_indices
# ---------------------------------------------------------------------------

def test_sample_observed_indices_zero():
    buf, _, _, _ = make_fixture()  # n_core=3
    rng = buf._build_local_rng(0, 0, "E1_death")
    assert buf._sample_observed_indices(0, rng) == []
    print("PASS test_sample_observed_indices_zero")


def test_sample_observed_indices_full():
    buf, _, _, _ = make_fixture()  # n_core=3
    rng = buf._build_local_rng(0, 0, "E1_death")
    assert buf._sample_observed_indices(3, rng) == [0, 1, 2]
    print("PASS test_sample_observed_indices_full")


def test_sample_observed_indices_partial_sorted():
    buf, _, _, _ = make_fixture()  # n_core=3
    rng = buf._build_local_rng(0, 0, "E1_death")
    idx = buf._sample_observed_indices(2, rng)
    assert len(idx) == 2
    assert idx == sorted(idx)  # 昇順
    assert all(0 <= i < buf.n_core for i in idx)
    assert len(set(idx)) == 2  # 重複なし
    print("PASS test_sample_observed_indices_partial_sorted")


def test_sample_observed_indices_overflow_capped():
    """n_observed > n_core は n_core にキャップ。"""
    buf, _, _, _ = make_fixture()  # n_core=3
    rng = buf._build_local_rng(0, 0, "E1_death")
    idx = buf._sample_observed_indices(100, rng)
    assert idx == [0, 1, 2]
    print("PASS test_sample_observed_indices_overflow_capped")


def test_sample_observed_indices_deterministic():
    """同じ seed+step+event でサンプル結果も同じ。"""
    buf, _, _, _ = make_fixture()  # n_core=3
    rng1 = buf._build_local_rng(42, 100, "E2_rise")
    rng2 = buf._build_local_rng(42, 100, "E2_rise")
    idx1 = buf._sample_observed_indices(2, rng1)
    idx2 = buf._sample_observed_indices(2, rng2)
    assert idx1 == idx2
    print("PASS test_sample_observed_indices_deterministic")


# ---------------------------------------------------------------------------
# v9.17 段階 4 Step 3 新規テスト: read_other_on_e3_contact
# ---------------------------------------------------------------------------

from v917_cid_view import CidView  # noqa: E402


def _make_view(
    cid_id=99,
    Q_remaining=8,
    Q0=10,
    n_core=4,
    birth_step=50,
    B_Gen=5.5,
    S_avg_birth=0.7,
    r_core_birth=0.4,
    phase_sig_birth=0.15,
    theta_birth=None,
):
    if theta_birth is None:
        theta_birth = np.array([0.1, 0.2, 0.3, 0.4])
    return CidView(
        cid_id=cid_id,
        Q_remaining=Q_remaining,
        Q0=Q0,
        n_core=n_core,
        birth_step=birth_step,
        B_Gen=B_Gen,
        S_avg_birth=S_avg_birth,
        r_core_birth=r_core_birth,
        phase_sig_birth=phase_sig_birth,
        theta_birth=theta_birth,
    )


# §4.6 test 1: basic behavior
def test_read_other_basic():
    buf, *_ = make_fixture()
    assert buf.other_records == []
    assert buf.total_other_contacts == 0

    other = _make_view(cid_id=7)
    buf.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=200,
        event_id=3,
        seed=0,
    )
    assert len(buf.other_records) == 1
    rec = buf.other_records[0]
    assert rec["other_cid_id"] == 7
    assert rec["step"] == 200
    assert rec["event_id"] == 3
    print("PASS test_read_other_basic")


# §4.6 test 2: visible_ratio computation
def test_read_other_visible_ratio_08():
    buf, *_ = make_fixture()
    other = _make_view(cid_id=7, Q_remaining=8, Q0=10)
    buf.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=1, event_id=0, seed=0,
    )
    rec = buf.other_records[0]
    assert abs(rec["visible_ratio"] - 0.8) < 1e-9
    print("PASS test_read_other_visible_ratio_08")


# §4.6 test 3: Q0=0 protection (no division, fully blind)
def test_read_other_q0_zero_protection():
    buf, *_ = make_fixture()
    other = _make_view(cid_id=7, Q_remaining=0, Q0=0)
    buf.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=1, event_id=0, seed=0,
    )
    rec = buf.other_records[0]
    assert rec["visible_ratio"] == 0.0
    assert rec["sampled_feature_indices"] == []
    assert rec["fetched_M_c"] == {}
    # 10 features 全て missing
    assert len(rec["missing_feature_names"]) == 10
    print("PASS test_read_other_q0_zero_protection")


# §4.6 test 4: n_visible = round(n_features * visible_ratio)
def test_read_other_n_visible_half():
    buf, *_ = make_fixture()
    # visible_ratio=0.5, n_features=10 → n_visible=5
    other = _make_view(cid_id=7, Q_remaining=5, Q0=10)
    buf.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=1, event_id=0, seed=0,
    )
    rec = buf.other_records[0]
    assert rec["visible_ratio"] == 0.5
    assert len(rec["sampled_feature_indices"]) == 5
    assert len(rec["fetched_M_c"]) == 5
    print("PASS test_read_other_n_visible_half")


# §4.6 test 5: sampled_feature_indices size = n_visible (multiple ratios)
def test_read_other_sampled_indices_size_match():
    # visible_ratio の関数として len(sampled) が一貫することを確認
    for q_rem, q0, expected_n in [
        (10, 10, 10),  # full
        (7, 10, 7),
        (3, 10, 3),
        (1, 10, 1),
        (0, 10, 0),
    ]:
        buf, *_ = make_fixture()
        other = _make_view(cid_id=7, Q_remaining=q_rem, Q0=q0)
        buf.read_other_on_e3_contact(
            other_cid_view=other,
            current_step=1, event_id=0, seed=0,
        )
        rec = buf.other_records[0]
        assert len(rec["sampled_feature_indices"]) == expected_n, (
            f"q_rem={q_rem} q0={q0}: "
            f"got {len(rec['sampled_feature_indices'])} expected {expected_n}"
        )
    print("PASS test_read_other_sampled_indices_size_match")


# §4.6 test 6: fetched_M_c + missing_feature_names = all 10 features
def test_read_other_fetched_plus_missing_equals_all():
    for q_rem in [0, 1, 3, 5, 7, 10]:
        buf, *_ = make_fixture()
        other = _make_view(cid_id=7, Q_remaining=q_rem, Q0=10)
        buf.read_other_on_e3_contact(
            other_cid_view=other,
            current_step=1, event_id=0, seed=0,
        )
        rec = buf.other_records[0]
        total = len(rec["fetched_M_c"]) + len(rec["missing_feature_names"])
        assert total == 10, f"q_rem={q_rem}: total={total}"
        # 重複なし (fetched と missing は disjoint)
        fetched_names = set(rec["fetched_M_c"].keys())
        missing_names = set(rec["missing_feature_names"])
        assert fetched_names.isdisjoint(missing_names)
        # 合わせて全 10 種の名前が揃う
        assert len(fetched_names | missing_names) == 10
    print("PASS test_read_other_fetched_plus_missing_equals_all")


# §4.6 test 7: determinism (same args → same sampled indices)
def test_read_other_deterministic():
    buf1, *_ = make_fixture()
    buf2, *_ = make_fixture()
    other = _make_view(cid_id=7, Q_remaining=5, Q0=10)
    buf1.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=123, event_id=4, seed=42,
    )
    buf2.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=123, event_id=4, seed=42,
    )
    rec1 = buf1.other_records[0]
    rec2 = buf2.other_records[0]
    assert rec1["sampled_feature_indices"] == rec2["sampled_feature_indices"]
    assert rec1["fetched_M_c"] == rec2["fetched_M_c"]

    # 異なる seed で結果も異なるはず (ほぼ必ず、hash 衝突除外)
    buf3, *_ = make_fixture()
    buf3.read_other_on_e3_contact(
        other_cid_view=other,
        current_step=123, event_id=4, seed=99,
    )
    # 全く同一になる確率は極めて低いが、必ずしも異なるとは限らないので
    # 決定論性 (再現性) のみを主張
    print("PASS test_read_other_deterministic")


# §4.6 test 8: self-as-other does not crash
#   (メインループでは呼ばれない前提だが、防御的に確認)
def test_read_other_self_as_other_safe():
    buf, *_ = make_fixture()
    # buf.cid_id = 42, view.cid_id = 42 (same)
    same_id_view = _make_view(cid_id=42, Q_remaining=5, Q0=10)
    # crash しないこと
    buf.read_other_on_e3_contact(
        other_cid_view=same_id_view,
        current_step=1, event_id=0, seed=0,
    )
    assert len(buf.other_records) == 1
    assert buf.total_other_contacts == 1
    print("PASS test_read_other_self_as_other_safe")


# §4.6 test 9: statistics counters updated correctly
def test_read_other_stats_updated():
    buf, *_ = make_fixture()
    # 3 回呼び、各回の取得/欠損数が累計される
    views = [
        _make_view(cid_id=7, Q_remaining=10, Q0=10),   # n_visible=10
        _make_view(cid_id=8, Q_remaining=5, Q0=10),    # n_visible=5
        _make_view(cid_id=9, Q_remaining=0, Q0=10),    # n_visible=0
    ]
    expected_fetched = 10 + 5 + 0  # = 15
    expected_missing = 0 + 5 + 10  # = 15
    for i, v in enumerate(views):
        buf.read_other_on_e3_contact(
            other_cid_view=v,
            current_step=100 + i, event_id=i, seed=0,
        )
    assert buf.total_other_contacts == 3
    assert buf.total_features_fetched == expected_fetched
    assert buf.total_features_missing == expected_missing
    print("PASS test_read_other_stats_updated")


# §4.6 test 10: AST-level check — no engine.rng / state.rng access
def test_no_engine_rng_access_ast():
    """v917_cid_self_buffer.py のソースを AST で走査し、
    engine.rng や state.rng への attribute access が存在しないことを確認。
    段階 4 禁止 §1.1 #5 (engine.rng を touch しない) の形式的検証。"""
    import ast
    import v917_cid_self_buffer as mod

    src_path = mod.__file__
    with open(src_path, "r") as f:
        tree = ast.parse(f.read(), filename=src_path)

    forbidden = []
    for node in ast.walk(tree):
        # engine.rng / state.rng の pattern を検出
        # ast.Attribute(value=Name(id='engine'), attr='rng')
        # または attribute chain (engine.state.rng 等) 全般
        if isinstance(node, ast.Attribute) and node.attr == "rng":
            # node.value が Name で 'engine' や 'state' のとき検出
            inner = node.value
            if isinstance(inner, ast.Name) and inner.id in ("engine", "state"):
                forbidden.append(
                    f"line {node.lineno}: {inner.id}.rng attribute access"
                )
            # chain: foo.engine.rng / foo.state.rng も検出
            elif isinstance(inner, ast.Attribute) and inner.attr in (
                "engine", "state"
            ):
                forbidden.append(
                    f"line {node.lineno}: ...{inner.attr}.rng attribute access"
                )
    assert forbidden == [], (
        "engine.rng / state.rng access detected:\n" + "\n".join(forbidden)
    )
    print("PASS test_no_engine_rng_access_ast")


# bonus: _extract_M_c_features shape & order
def test_extract_m_c_features_shape_and_order():
    from v917_cid_self_buffer import _extract_M_c_features
    view = _make_view(
        cid_id=7, Q0=12, n_core=4,
        birth_step=77, B_Gen=5.25,
        S_avg_birth=0.55, r_core_birth=0.33, phase_sig_birth=0.11,
        theta_birth=np.array([1.0, 2.0, 3.0, 4.0]),
    )
    feats = _extract_M_c_features(view)
    assert isinstance(feats, list)
    assert len(feats) == 10
    # 名前順序は固定
    expected_names = [
        "B_Gen", "Q0", "n_core", "S_avg_birth", "r_core_birth",
        "phase_sig_birth", "theta_birth_mean", "theta_birth_std",
        "theta_birth_range", "birth_step",
    ]
    actual_names = [name for (name, _) in feats]
    assert actual_names == expected_names
    # 各値
    d = dict(feats)
    assert abs(d["B_Gen"] - 5.25) < 1e-9
    assert d["Q0"] == 12
    assert d["n_core"] == 4
    assert d["birth_step"] == 77
    assert abs(d["theta_birth_mean"] - 2.5) < 1e-9
    assert abs(d["theta_birth_range"] - 3.0) < 1e-9
    # std = sqrt(var)
    expected_std = float(np.std(np.array([1.0, 2.0, 3.0, 4.0])))
    assert abs(d["theta_birth_std"] - expected_std) < 1e-9
    print("PASS test_extract_m_c_features_shape_and_order")


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
        test_link_death_does_not_trigger_mismatch_stage3,
        test_iter_member_links_excludes_outside,
        test_divergence_log_has_event_type,
        # --- v9.16 段階 3 新規テスト (Step 1) ---
        test_q0_stored,
        test_q0_negative_coerced_to_zero,
        test_q0_none_coerced_to_zero,
        test_compute_age_factor_full,
        test_compute_age_factor_half,
        test_compute_age_factor_zero,
        test_compute_age_factor_q0_zero,
        test_compute_age_factor_clamp_negative_q,
        test_compute_age_factor_clamp_overflow_q,
        test_compute_n_observed_full,
        test_compute_n_observed_zero,
        test_compute_n_observed_half,
        test_compute_n_observed_monotonic,
        test_build_local_rng_deterministic,
        test_build_local_rng_different_seeds,
        test_build_local_rng_different_event_types,
        test_sample_observed_indices_zero,
        test_sample_observed_indices_full,
        test_sample_observed_indices_partial_sorted,
        test_sample_observed_indices_overflow_capped,
        test_sample_observed_indices_deterministic,
        test_a_observer_summary_empty,
        test_a_observer_summary_populated,
        test_a_observer_match_history_is_copy,
        test_a_observer_snapshot_is_copy,
        test_a_observer_divergence_log_is_copy,
        test_read_own_state_does_not_affect_event_counters,
        # --- v9.16 段階 3 新規テスト (Step 2) ---
        test_read_on_event_n_observed_matches_sample,
        test_read_on_event_node_status_three_values,
        test_read_on_event_missing_does_not_trigger_mismatch,
        test_read_on_event_missing_flags_cumulative,
        test_read_on_event_negative_q_safe,
        test_read_on_event_counts_observed_only,
        test_read_on_event_deterministic,
        test_read_on_event_q0_zero_always_blind,
        test_divergence_log_both_all_and_observed,
        test_divergence_log_observed_zero_when_blind,
        test_age_factor_history_recorded,
        test_no_q_write,
        # --- v9.17 段階 4 新規テスト (Step 3): 他者読み ---
        test_read_other_basic,
        test_read_other_visible_ratio_08,
        test_read_other_q0_zero_protection,
        test_read_other_n_visible_half,
        test_read_other_sampled_indices_size_match,
        test_read_other_fetched_plus_missing_equals_all,
        test_read_other_deterministic,
        test_read_other_self_as_other_safe,
        test_read_other_stats_updated,
        test_no_engine_rng_access_ast,
        test_extract_m_c_features_shape_and_order,
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
