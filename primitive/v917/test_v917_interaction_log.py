"""
v9.17 段階 4 Step 1 単体テスト: InteractionLog + CidView

指示書 §3.2 の 8 項目をカバー:
  1. 空の状態: get_record_count() == 0
  2. 単一接触: record_contact 1 回で get_record_count() == 1
  3. 記録内容: dict に composition / cid_a_id / cid_b_id /
     cid_a_age_factor 等が正しく含まれる
  4. composition が frozenset
  5. Q0=0 保護: age_factor=0.0 が記録される (ゼロ除算しない)
  6. 同一ペアの複数記録: 重複排除しない
  7. get_records は copy: 返り値改変が self.records に影響しない
  8. CID object の非保持: rec に live CID object が直接含まれない
     (scalar / frozenset のみ)

加えて CidView の基本動作もカバー:
  9. CidView.age_factor (Q0>0, Q0=0, Q_remaining>Q0 clamp)
 10. build_cid_view が None を返す 3 条件

実行: python test_v917_interaction_log.py
"""

from __future__ import annotations

import sys
import types

import numpy as np

from v917_cid_view import CidView, build_cid_view
from v917_interaction_log import InteractionLog


# ----------------------------------------------------------------------
# CidView test fixtures
# ----------------------------------------------------------------------

def make_cid_view(
    cid_id: int = 1,
    Q_remaining: int = 8,
    Q0: int = 10,
    n_core: int = 4,
    birth_step: int = 100,
    B_Gen: float = 5.5,
    S_avg_birth: float = 0.7,
    r_core_birth: float = 0.3,
    phase_sig_birth: float = 0.1,
    theta_birth=None,
) -> CidView:
    if theta_birth is None:
        theta_birth = np.arange(n_core, dtype=float)
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


# ----------------------------------------------------------------------
# §3.2 item 1: empty state
# ----------------------------------------------------------------------

def test_empty_log():
    log = InteractionLog()
    assert log.get_record_count() == 0
    assert log.get_records() == []


# ----------------------------------------------------------------------
# §3.2 item 2: single contact
# ----------------------------------------------------------------------

def test_single_contact_count():
    log = InteractionLog()
    a = make_cid_view(cid_id=1)
    b = make_cid_view(cid_id=2)
    log.record_contact(step=200, cid_a=a, cid_b=b, event_id=0)
    assert log.get_record_count() == 1


# ----------------------------------------------------------------------
# §3.2 item 3: record content
# ----------------------------------------------------------------------

def test_record_content():
    log = InteractionLog()
    a = make_cid_view(cid_id=1, Q_remaining=8, Q0=10, n_core=4)
    b = make_cid_view(cid_id=7, Q_remaining=5, Q0=20, n_core=3)
    log.record_contact(step=500, cid_a=a, cid_b=b, event_id=42)

    rec = log.get_records()[0]
    assert rec["step"] == 500
    assert rec["cid_a_id"] == 1
    assert rec["cid_b_id"] == 7
    assert rec["cid_a_Q0"] == 10
    assert rec["cid_b_Q0"] == 20
    assert rec["cid_a_n_core"] == 4
    assert rec["cid_b_n_core"] == 3
    assert rec["event_id"] == 42
    # age_factor = Q_remaining / Q0
    assert abs(rec["cid_a_age_factor"] - 0.8) < 1e-9
    assert abs(rec["cid_b_age_factor"] - 0.25) < 1e-9
    assert rec["composition"] == frozenset({1, 7})


# ----------------------------------------------------------------------
# §3.2 item 4: composition is frozenset
# ----------------------------------------------------------------------

def test_composition_is_frozenset():
    log = InteractionLog()
    a = make_cid_view(cid_id=3)
    b = make_cid_view(cid_id=5)
    log.record_contact(step=1, cid_a=a, cid_b=b, event_id=0)
    rec = log.get_records()[0]
    assert isinstance(rec["composition"], frozenset)


# ----------------------------------------------------------------------
# §3.2 item 5: Q0=0 protection
# ----------------------------------------------------------------------

def test_q0_zero_no_division():
    log = InteractionLog()
    # Q0=0 の cid (B_Gen=inf 由来) は age_factor=0.0
    a = make_cid_view(cid_id=1, Q_remaining=0, Q0=0)
    b = make_cid_view(cid_id=2, Q_remaining=0, Q0=0)
    log.record_contact(step=1, cid_a=a, cid_b=b, event_id=0)
    rec = log.get_records()[0]
    assert rec["cid_a_age_factor"] == 0.0
    assert rec["cid_b_age_factor"] == 0.0
    assert rec["cid_a_Q0"] == 0
    assert rec["cid_b_Q0"] == 0


def test_q0_zero_mixed_pair():
    # 片方 Q0=0, もう片方 Q0>0
    log = InteractionLog()
    a = make_cid_view(cid_id=1, Q_remaining=0, Q0=0)
    b = make_cid_view(cid_id=2, Q_remaining=4, Q0=8)
    log.record_contact(step=1, cid_a=a, cid_b=b, event_id=0)
    rec = log.get_records()[0]
    assert rec["cid_a_age_factor"] == 0.0
    assert abs(rec["cid_b_age_factor"] - 0.5) < 1e-9


# ----------------------------------------------------------------------
# §3.2 item 6: duplicate pair records not dedupped
# ----------------------------------------------------------------------

def test_same_pair_multiple_records():
    log = InteractionLog()
    a = make_cid_view(cid_id=1)
    b = make_cid_view(cid_id=2)
    log.record_contact(step=100, cid_a=a, cid_b=b, event_id=0)
    log.record_contact(step=200, cid_a=a, cid_b=b, event_id=5)
    log.record_contact(step=300, cid_a=a, cid_b=b, event_id=11)
    assert log.get_record_count() == 3
    recs = log.get_records()
    assert [r["step"] for r in recs] == [100, 200, 300]
    # composition 同一であることも確認 (dedup しない)
    compositions = [r["composition"] for r in recs]
    assert all(c == frozenset({1, 2}) for c in compositions)


# ----------------------------------------------------------------------
# §3.2 item 7: get_records is a copy
# ----------------------------------------------------------------------

def test_get_records_is_copy():
    log = InteractionLog()
    a = make_cid_view(cid_id=1)
    b = make_cid_view(cid_id=2)
    log.record_contact(step=1, cid_a=a, cid_b=b, event_id=0)
    snap = log.get_records()
    # 返り値を改変
    snap.clear()
    snap.append({"fake": 1})
    # self.records は影響を受けない
    assert log.get_record_count() == 1
    assert "fake" not in log.get_records()[0]


# ----------------------------------------------------------------------
# §3.2 item 8: no CID object reference in records
# ----------------------------------------------------------------------

def test_no_cid_object_retention():
    """
    CidView 本体は records 内に保持されないことを確認。
    rec に格納されるのは int / float / frozenset のみ。
    """
    log = InteractionLog()
    a = make_cid_view(cid_id=1)
    b = make_cid_view(cid_id=2)
    log.record_contact(step=1, cid_a=a, cid_b=b, event_id=0)
    rec = log.get_records()[0]
    for key, val in rec.items():
        if key == "composition":
            assert isinstance(val, frozenset)
            continue
        assert isinstance(val, (int, float)), (
            f"{key} should be primitive, got {type(val)}: {val}"
        )
    # CidView instance そのものが値として埋め込まれていないこと
    assert not any(isinstance(v, CidView) for v in rec.values())


# ----------------------------------------------------------------------
# CidView additional coverage
# ----------------------------------------------------------------------

def test_cidview_age_factor():
    # 通常ケース
    v = make_cid_view(Q_remaining=3, Q0=10)
    assert abs(v.age_factor - 0.3) < 1e-9
    # Q0=0
    v2 = make_cid_view(Q_remaining=0, Q0=0)
    assert v2.age_factor == 0.0
    # Q_remaining > Q0 (理論上起きないが clamp)
    v3 = make_cid_view(Q_remaining=15, Q0=10)
    assert v3.age_factor == 1.0
    # Q_remaining < 0 (clamp)
    v4 = make_cid_view(Q_remaining=-3, Q0=10)
    assert v4.age_factor == 0.0


def test_build_cid_view_none_conditions():
    """build_cid_view が None を返す 3 条件:
       cid_id=None / self_buffer=None / ledger に未登録"""
    dummy_ledger = types.SimpleNamespace(ledger={})
    dummy_cog = types.SimpleNamespace(v11_b_gen={}, v11_m_c={})

    # cid_id None
    assert build_cid_view(None, object(), dummy_ledger, dummy_cog) is None

    # self_buffer None
    assert build_cid_view(1, None, dummy_ledger, dummy_cog) is None

    # ledger に未登録
    stub_buf = types.SimpleNamespace(
        Q0=10, n_core=3, birth_step=0,
        theta_birth=np.zeros(3),
    )
    assert build_cid_view(1, stub_buf, dummy_ledger, dummy_cog) is None


def test_build_cid_view_happy_path():
    """正常系: 必要な情報が揃っていれば CidView を返す。"""
    stub_buf = types.SimpleNamespace(
        Q0=10, n_core=3, birth_step=50,
        theta_birth=np.array([0.1, 0.2, 0.3]),
    )
    stub_ledger = types.SimpleNamespace(ledger={
        7: {"v14_q_remaining": 4},
    })
    stub_cog = types.SimpleNamespace(
        v11_b_gen={7: 5.5},
        v11_m_c={7: {"n_core": 3, "s_avg": 0.7,
                     "r_core": 0.4, "phase_sig": 0.15}},
    )
    v = build_cid_view(7, stub_buf, stub_ledger, stub_cog)
    assert v is not None
    assert v.cid_id == 7
    assert v.Q_remaining == 4
    assert v.Q0 == 10
    assert v.n_core == 3
    assert v.birth_step == 50
    assert abs(v.B_Gen - 5.5) < 1e-9
    assert abs(v.S_avg_birth - 0.7) < 1e-9
    assert abs(v.r_core_birth - 0.4) < 1e-9
    assert abs(v.phase_sig_birth - 0.15) < 1e-9
    assert abs(v.age_factor - 0.4) < 1e-9


def test_build_cid_view_bgen_inf_preserved():
    """B_Gen=inf の cid (unformed) でも build_cid_view は CidView を返す。
    CidView は inf をそのまま保持する (呼び出し側で解釈)。"""
    stub_buf = types.SimpleNamespace(
        Q0=0, n_core=2, birth_step=0,
        theta_birth=np.zeros(2),
    )
    stub_ledger = types.SimpleNamespace(ledger={
        1: {"v14_q_remaining": 0},
    })
    stub_cog = types.SimpleNamespace(
        v11_b_gen={1: float("inf")},
        v11_m_c={1: {"n_core": 2, "s_avg": 0.0,
                     "r_core": 0.0, "phase_sig": 0.0}},
    )
    v = build_cid_view(1, stub_buf, stub_ledger, stub_cog)
    assert v is not None
    assert v.B_Gen == float("inf")
    assert v.Q0 == 0
    assert v.age_factor == 0.0  # Q0=0 → age_factor 0


# ----------------------------------------------------------------------
# Test runner
# ----------------------------------------------------------------------

ALL_TESTS = [
    # §3.2 items
    test_empty_log,
    test_single_contact_count,
    test_record_content,
    test_composition_is_frozenset,
    test_q0_zero_no_division,
    test_q0_zero_mixed_pair,
    test_same_pair_multiple_records,
    test_get_records_is_copy,
    test_no_cid_object_retention,
    # CidView coverage
    test_cidview_age_factor,
    test_build_cid_view_none_conditions,
    test_build_cid_view_happy_path,
    test_build_cid_view_bgen_inf_preserved,
]


def main():
    failed = []
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed.append((fn.__name__, str(e)))
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed.append((fn.__name__, f"{type(e).__name__}: {e}"))
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")

    print()
    if failed:
        print(f"{len(failed)}/{len(ALL_TESTS)} tests failed:")
        for name, msg in failed:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    print(f"All {len(ALL_TESTS)} tests passed.")


if __name__ == "__main__":
    main()
