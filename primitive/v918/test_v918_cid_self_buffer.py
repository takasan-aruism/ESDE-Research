"""
v9.18 単体テスト: CidSelfBuffer v9.18 拡張 + orchestrator

境界 + ghost 化 + tracking_end finalize の検証。
v917 baseline の test は v917 側で担保 (継承クラスなので挙動は同一)。
"""

from __future__ import annotations

import sys
from pathlib import Path
import types

import numpy as np

# v917 相対パスを通す (v917_cid_self_buffer を import 可能にする)
_V917_DIR = Path(__file__).resolve().parent.parent / "v917"
if str(_V917_DIR) not in sys.path:
    sys.path.insert(0, str(_V917_DIR))

from v918_cid_self_buffer import CidSelfBuffer
from v918_orchestrator import (
    v918_update_per_step,
    v918_snapshot_window,
    v918_finalize_all_at_tracking_end,
    build_v918_subject_columns,
)
from v918_unity_metrics import compute_v_unified


EPS = 1e-9


def make_buf(cid_id=42, member_nodes=(10, 20, 30), Q0=10,
             theta_values=(1.0, 2.0, 3.0)):
    member_frozen = frozenset(member_nodes)
    initial_theta = np.asarray(theta_values, dtype=float)
    initial_S = {(10, 20): 0.5, (10, 30): 0.6, (20, 30): 0.7}
    return CidSelfBuffer(
        cid_id=cid_id,
        member_nodes=member_frozen,
        birth_step=100,
        initial_theta=initial_theta,
        initial_S=initial_S,
        Q0=Q0,
    )


# ---------------------------------------------------------------
# CidSelfBuffer 初期化
# ---------------------------------------------------------------

def test_init_v917_attrs_intact():
    buf = make_buf()
    # v917 の属性が継承され正常
    assert buf.cid_id == 42
    assert buf.n_core == 3
    assert buf.sorted_member_list == [10, 20, 30]
    assert buf.Q0 == 10
    assert np.allclose(buf.theta_birth, [1.0, 2.0, 3.0])


def test_init_v918_birth_v_unified():
    buf = make_buf()
    expected = compute_v_unified(np.array([1.0, 2.0, 3.0]))
    assert abs(buf.v18_birth_v_unified - expected) < 1e-12
    assert abs(buf.v18_v_unified_concentration_birth - abs(expected)) < EPS


def test_init_v918_defaults():
    buf = make_buf()
    assert buf.v18_cumulative_cognitive_gain == 0
    assert buf.v18_unity_direction is None
    assert buf.v18_unity_concentration is None
    assert buf.v18_unity_direction_shift is None
    assert buf.v18_unity_k == 0
    assert buf.v18_theta_distance_from_birth is None
    assert buf.v18_theta_distance_coverage_ratio == 0.0
    assert buf.v18_finalized_at_step is None
    assert buf.v18_finalize_reason is None


def test_property_birth_theta_by_node():
    buf = make_buf()
    d = buf.v18_birth_theta_by_node
    assert d == {10: 1.0, 20: 2.0, 30: 3.0}


def test_property_birth_member_nodes():
    buf = make_buf()
    assert buf.v18_birth_member_nodes == frozenset({10, 20, 30})


# ---------------------------------------------------------------
# finalize_v18_values
# ---------------------------------------------------------------

def test_finalize_basic():
    buf = make_buf()
    buf.v18_cumulative_cognitive_gain = 5
    buf.v18_unity_concentration = 0.8
    buf.v18_unity_direction_shift = 0.3
    buf.v18_unity_k = 3
    buf.v18_theta_distance_from_birth = 0.5
    buf.v18_theta_distance_coverage_ratio = 1.0

    ok = buf.finalize_v18_values(current_step=500, reason="tracking_end")
    assert ok is True
    assert buf.v18_cognitive_gain_final == 5
    assert buf.v18_v_unified_concentration_final == 0.8
    assert buf.v18_v_unified_direction_shift_final == 0.3
    assert buf.v18_v_unified_k_final == 3
    assert buf.v18_theta_distance_from_birth_final == 0.5
    assert buf.v18_theta_distance_coverage_ratio_final == 1.0
    assert buf.v18_finalized_at_step == 500
    assert buf.v18_finalize_reason == "tracking_end"


def test_finalize_idempotent():
    buf = make_buf()
    buf.v18_cumulative_cognitive_gain = 5
    buf.finalize_v18_values(current_step=500, reason="ghost")
    # 2 回目の finalize は False を返し、値は変わらない
    ok = buf.finalize_v18_values(current_step=999, reason="tracking_end")
    assert ok is False
    assert buf.v18_finalized_at_step == 500
    assert buf.v18_finalize_reason == "ghost"


def test_finalize_none_passthrough():
    # 未計算の None 値はそのまま _final に反映される
    buf = make_buf()
    buf.finalize_v18_values(current_step=100, reason="tracking_end")
    assert buf.v18_v_unified_concentration_final is None
    assert buf.v18_theta_distance_from_birth_final is None


# ---------------------------------------------------------------
# orchestrator: v918_update_per_step (mock engine/cog/vl)
# ---------------------------------------------------------------

def make_mock_env(cid_id=42, current_lid=7, current_nodes=(10, 20, 30),
                  theta_values=(1.5, 2.5, 3.5), q_remaining=8, Q0=10):
    cog = types.SimpleNamespace()
    cog.current_lid = {cid_id: current_lid}
    vl = types.SimpleNamespace()
    vl.labels = {current_lid: {"nodes": list(current_nodes)}}
    engine = types.SimpleNamespace()
    state_theta = np.zeros(100)
    for node, th in zip(current_nodes, theta_values):
        state_theta[node] = th
    engine.state = types.SimpleNamespace(theta=state_theta)
    ledger = types.SimpleNamespace()
    ledger.ledger = {cid_id: {"v14_q_remaining": q_remaining}}
    return cog, vl, engine, ledger


def test_update_per_step_hosted_updates_all():
    buf = make_buf(cid_id=42, theta_values=(1.0, 2.0, 3.0), Q0=10)
    cog, vl, engine, ledger = make_mock_env(
        cid_id=42, current_nodes=(10, 20, 30),
        theta_values=(1.0, 2.0, 3.0), q_remaining=7, Q0=10,
    )
    v918_update_per_step(
        self_buffers={42: buf}, cog=cog, vl=vl, engine=engine,
        v914_ledger=ledger, current_step=500,
    )
    # C: gain = 10 - 7 = 3
    assert buf.v18_cumulative_cognitive_gain == 3
    # V_unified: θ 変化なし → direction_shift ≈ 0, concentration = birth
    assert buf.v18_unity_k == 3
    assert buf.v18_unity_direction_shift is not None
    assert abs(buf.v18_unity_direction_shift) < 1e-6
    # theta_distance: 変化なし → 0
    assert buf.v18_theta_distance_from_birth is not None
    assert abs(buf.v18_theta_distance_from_birth) < 1e-9
    assert buf.v18_theta_distance_coverage_ratio == 1.0


def test_update_per_step_ghost_finalizes():
    buf = make_buf(cid_id=42)
    cog, vl, engine, ledger = make_mock_env(cid_id=42)
    # ghost 化: current_lid を None に
    cog.current_lid[42] = None

    buf.v18_cumulative_cognitive_gain = 4
    buf.v18_unity_concentration = 0.9

    v918_update_per_step(
        self_buffers={42: buf}, cog=cog, vl=vl, engine=engine,
        v914_ledger=ledger, current_step=300,
    )
    # ghost 検出で _finalize が走る
    assert buf.v18_finalized_at_step == 300
    assert buf.v18_finalize_reason == "ghost"
    assert buf.v18_cognitive_gain_final == 4
    assert buf.v18_v_unified_concentration_final == 0.9


def test_update_per_step_label_missing_treated_as_ghost():
    buf = make_buf(cid_id=42)
    cog, vl, engine, ledger = make_mock_env(cid_id=42)
    # current_lid は残っているが vl.labels に存在しない (整合性不足)
    vl.labels = {}

    v918_update_per_step(
        self_buffers={42: buf}, cog=cog, vl=vl, engine=engine,
        v914_ledger=ledger, current_step=300,
    )
    assert buf.v18_finalized_at_step == 300
    assert buf.v18_finalize_reason == "ghost"


def test_update_per_step_skip_after_finalize():
    buf = make_buf(cid_id=42)
    cog, vl, engine, ledger = make_mock_env(cid_id=42)
    buf.finalize_v18_values(current_step=100, reason="ghost")
    # 再度 update を呼んでも変わらない
    v918_update_per_step(
        self_buffers={42: buf}, cog=cog, vl=vl, engine=engine,
        v914_ledger=ledger, current_step=500,
    )
    assert buf.v18_finalized_at_step == 100
    assert buf.v18_finalize_reason == "ghost"


def test_update_per_step_gain_clamp():
    buf = make_buf(cid_id=42, Q0=10)
    cog, vl, engine, ledger = make_mock_env(cid_id=42, Q0=10, q_remaining=15)
    # q_remaining > Q0 (理論上ありえないが防御)
    v918_update_per_step(
        self_buffers={42: buf}, cog=cog, vl=vl, engine=engine,
        v914_ledger=ledger, current_step=500,
    )
    # gain は 0 以上に clamp
    assert buf.v18_cumulative_cognitive_gain == 0


def test_update_per_step_no_ledger_entry():
    buf = make_buf(cid_id=42)
    cog, vl, engine, ledger = make_mock_env(cid_id=42)
    ledger.ledger = {}  # cid 未登録
    v918_update_per_step(
        self_buffers={42: buf}, cog=cog, vl=vl, engine=engine,
        v914_ledger=ledger, current_step=500,
    )
    # 更新スキップ、_final 未発火
    assert buf.v18_cumulative_cognitive_gain == 0
    assert buf.v18_finalized_at_step is None


# ---------------------------------------------------------------
# orchestrator: snapshot_window / finalize_all_at_tracking_end
# ---------------------------------------------------------------

def test_snapshot_window_appends_hosted_only():
    buf1 = make_buf(cid_id=1)
    buf2 = make_buf(cid_id=2)
    cog = types.SimpleNamespace()
    cog.current_lid = {1: 10, 2: None}  # 2 は ghost
    vl = types.SimpleNamespace()
    vl.labels = {10: {"nodes": [10, 20, 30]}}

    acc = []
    v918_snapshot_window(
        self_buffers={1: buf1, 2: buf2}, cog=cog, vl=vl,
        window_idx=5, cumulative_step=2500, accumulator=acc,
    )
    # hosted のみ (cid=1)
    assert len(acc) == 1
    assert acc[0]["cid_id"] == 1
    assert acc[0]["window"] == 5
    assert acc[0]["step_at_window_end"] == 2500


def test_snapshot_window_skips_finalized():
    buf = make_buf(cid_id=1)
    buf.finalize_v18_values(current_step=100, reason="ghost")
    cog = types.SimpleNamespace()
    cog.current_lid = {1: 10}
    vl = types.SimpleNamespace()
    vl.labels = {10: {"nodes": [10, 20, 30]}}

    acc = []
    v918_snapshot_window(
        self_buffers={1: buf}, cog=cog, vl=vl,
        window_idx=5, cumulative_step=2500, accumulator=acc,
    )
    # 既 finalize 済はスキップ
    assert len(acc) == 0


def test_finalize_all_at_tracking_end():
    buf1 = make_buf(cid_id=1)  # 未 finalize
    buf2 = make_buf(cid_id=2)  # 既 ghost finalize
    buf2.finalize_v18_values(current_step=200, reason="ghost")

    n = v918_finalize_all_at_tracking_end(
        self_buffers={1: buf1, 2: buf2}, cumulative_step=25000,
    )
    assert n == 1
    assert buf1.v18_finalized_at_step == 25000
    assert buf1.v18_finalize_reason == "tracking_end"
    # buf2 は元の ghost 値を保持
    assert buf2.v18_finalized_at_step == 200
    assert buf2.v18_finalize_reason == "ghost"


# ---------------------------------------------------------------
# build_v918_subject_columns
# ---------------------------------------------------------------

def test_subject_columns_unformed_for_missing():
    cols = build_v918_subject_columns({}, 999)
    assert all(v == "unformed" for v in cols.values())


def test_subject_columns_values_populated():
    buf = make_buf(cid_id=7)
    buf.v18_cumulative_cognitive_gain = 5
    buf.v18_unity_concentration = 0.7
    buf.v18_unity_direction_shift = 0.2
    buf.v18_unity_k = 3
    buf.v18_theta_distance_from_birth = 0.4
    buf.v18_theta_distance_coverage_ratio = 1.0
    buf.finalize_v18_values(current_step=1000, reason="tracking_end")

    cols = build_v918_subject_columns({7: buf}, 7)
    assert cols["v18_cognitive_gain_final"] == 5
    assert cols["v18_v_unified_concentration_final"] == 0.7
    assert cols["v18_v_unified_k_final"] == 3
    assert cols["v18_finalized_at_step"] == 1000
    assert cols["v18_finalize_reason"] == "tracking_end"


# ---------------------------------------------------------------
# runner
# ---------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_init_v917_attrs_intact,
        test_init_v918_birth_v_unified,
        test_init_v918_defaults,
        test_property_birth_theta_by_node,
        test_property_birth_member_nodes,
        test_finalize_basic,
        test_finalize_idempotent,
        test_finalize_none_passthrough,
        test_update_per_step_hosted_updates_all,
        test_update_per_step_ghost_finalizes,
        test_update_per_step_label_missing_treated_as_ghost,
        test_update_per_step_skip_after_finalize,
        test_update_per_step_gain_clamp,
        test_update_per_step_no_ledger_entry,
        test_snapshot_window_appends_hosted_only,
        test_snapshot_window_skips_finalized,
        test_finalize_all_at_tracking_end,
        test_subject_columns_unformed_for_missing,
        test_subject_columns_values_populated,
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
