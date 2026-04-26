#!/usr/bin/env python3
"""
v10.1 Minimal Ingestion 単体テスト
====================================
SubjectLayer.attempt_ingestion / SpendAuditLedger.add_q /
SubjectLayer.reap_ghosts_step / detach (residual_Q snapshot) の
境界条件を検証する。

run: python -m pytest test_v101_ingestion.py -v
     または python test_v101_ingestion.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent  # developmental/v101 -> ESDE-Research
for p in [str(_HERE),
          str(_REPO_ROOT / "autonomy" / "v82"),
          str(_REPO_ROOT / "ecology" / "engine"),
          str(_REPO_ROOT / "genesis" / "canon"),
          str(_REPO_ROOT / "primitive" / "v910"),
          str(_REPO_ROOT / "primitive" / "v911")]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

from v101_memory_readout import SubjectLayer
from v914_spend_audit_ledger import SpendAuditLedger


def _make_cog_with_one_ghost(residual_q: int):
    """ghost を 1 体だけ持つ最小 cog を作る (ledger 経由ではなく直接登録)。"""
    cog = SubjectLayer()
    # cid=0 を birth → detach してghostにする
    cid = cog.birth(lid=10, phase_sig=0.0, current_window=0)
    cog.detach(lid=10, current_window=1, residual_Q=residual_q, current_step=100)
    return cog, cid


def _make_ledger_with_one_hosted(cid: int, q0: int, q_remaining: int):
    """ledger.add_q が走る最小 ledger を作る (registration 偽装)。"""
    ledger = SpendAuditLedger()
    ledger.ledger[cid] = {
        "v14_q0": q0,
        "v14_q_remaining": q_remaining,
        "v14_virtual_attention": {},
        "v14_virtual_familiarity": {},
        "v14_last_snapshot": None,
        "v14_shadow_pulse_index": 0,
        "v14_prev_member_alive_links": frozenset(),
        "v14_prev_member_r": {},
        "member_nodes": frozenset(),
        "registered_at": (0, 0),
        "v14_last_event_global_step": None,
    }
    return ledger


# ─────────────────────────────────────────────────────────
# detach / residual_Q snapshot
# ─────────────────────────────────────────────────────────

def test_detach_inherits_residual_Q():
    cog = SubjectLayer()
    cog.birth(lid=1, phase_sig=0.0, current_window=0)
    cid = cog.detach(lid=1, current_window=2,
                      residual_Q=15, current_step=200)
    assert cog.ghost_residual_Q[cid] == 15
    assert cog.ghost_residual_Q_initial[cid] == 15
    assert cog.ghost_q_lost_at_step[cid] == 200
    assert cog.is_ghost(cid) is True


def test_detach_residual_Q_zero_creates_empty_ghost():
    """Q=0 で detach した ghost は ghost_residual_Q[cid]==0 で登録され、
    次の reap_ghosts_step で即 reap される (空 ghost)。"""
    cog = SubjectLayer()
    cog.birth(lid=1, phase_sig=0.0, current_window=0)
    cid = cog.detach(lid=1, current_window=2,
                      residual_Q=0, current_step=200)
    assert cog.ghost_residual_Q[cid] == 0
    reaped = cog.reap_ghosts_step(201)
    assert cid in reaped
    # reap 後は dict から消える
    assert cid not in cog.ghost_residual_Q
    assert cid not in cog.current_lid


# ─────────────────────────────────────────────────────────
# add_q (Q0 上限 clamp)
# ─────────────────────────────────────────────────────────

def test_add_q_no_clamp_below_q0():
    ledger = _make_ledger_with_one_hosted(cid=5, q0=20, q_remaining=10)
    received, q_before, q_after = ledger.add_q(5, 7)
    assert (received, q_before, q_after) == (7, 10, 17)


def test_add_q_clamps_at_q0():
    ledger = _make_ledger_with_one_hosted(cid=5, q0=20, q_remaining=18)
    # gain=10 だが q0=20 で頭打ち、received=2、digested は caller 側で計算 (gain - received)
    received, q_before, q_after = ledger.add_q(5, 10)
    assert received == 2
    assert q_before == 18
    assert q_after == 20


def test_add_q_already_at_q0():
    ledger = _make_ledger_with_one_hosted(cid=5, q0=20, q_remaining=20)
    received, q_before, q_after = ledger.add_q(5, 5)
    assert (received, q_before, q_after) == (0, 20, 20)


def test_add_q_unknown_cid():
    ledger = SpendAuditLedger()
    received, q_before, q_after = ledger.add_q(999, 5)
    assert (received, q_before, q_after) == (0, 0, 0)


# ─────────────────────────────────────────────────────────
# attempt_ingestion (full / partial / empty / phantom)
# ─────────────────────────────────────────────────────────

def test_attempt_ingestion_full_transfer():
    """ghost.residual_Q=10、observer は q0=20 で q_remaining=5 → 全部受け取る"""
    cog, ghost_cid = _make_cog_with_one_ghost(residual_q=10)
    observer_cid = 99
    ledger = _make_ledger_with_one_hosted(observer_cid, q0=20, q_remaining=5)
    result = cog.attempt_ingestion(observer_cid, ghost_cid, ledger)
    assert result is not None
    assert result["gain"] == 10
    assert result["received"] == 10
    assert result["digested"] == 0
    assert result["was_empty"] is False
    assert result["residual_Q_after"] == 0
    assert result["q_remaining_after"] == 15
    # ghost の residual_Q が 0 になった
    assert cog.ghost_residual_Q[ghost_cid] == 0


def test_attempt_ingestion_q0_overflow_digests():
    """ghost.residual_Q=10、observer は q0=12 で q_remaining=8 → 4 received、6 digested"""
    cog, ghost_cid = _make_cog_with_one_ghost(residual_q=10)
    observer_cid = 99
    ledger = _make_ledger_with_one_hosted(observer_cid, q0=12, q_remaining=8)
    result = cog.attempt_ingestion(observer_cid, ghost_cid, ledger)
    assert result["gain"] == 10
    assert result["received"] == 4
    assert result["digested"] == 6
    assert result["q_remaining_after"] == 12  # q0 で頭打ち
    assert cog.ghost_residual_Q[ghost_cid] == 0  # 全 gain 分減った (消化分含む)


def test_attempt_ingestion_empty_ghost():
    """ghost.residual_Q=0 → 空摂食 (was_empty=True、gain=0)"""
    cog, ghost_cid = _make_cog_with_one_ghost(residual_q=0)
    observer_cid = 99
    ledger = _make_ledger_with_one_hosted(observer_cid, q0=20, q_remaining=5)
    result = cog.attempt_ingestion(observer_cid, ghost_cid, ledger)
    assert result["gain"] == 0
    assert result["received"] == 0
    assert result["digested"] == 0
    assert result["was_empty"] is True
    assert result["q_remaining_after"] == 5  # 何も増えてない


def test_attempt_ingestion_phantom_returns_none():
    """ghost が cog から消えた状態 (reap 済) → None 返す (caller が phantom log)"""
    cog = SubjectLayer()
    observer_cid = 99
    ledger = _make_ledger_with_one_hosted(observer_cid, q0=20, q_remaining=5)
    result = cog.attempt_ingestion(observer_cid, ghost_cid=12345, ledger=ledger)
    assert result is None


def test_satiated_observer_still_ingests_and_drains_ghost():
    """飢餓判定撤廃: observer が q_remaining=q0 (満腹) でも摂食発動、
    ghost.residual_Q は全 gain 分減る (全部消化分)"""
    cog, ghost_cid = _make_cog_with_one_ghost(residual_q=8)
    observer_cid = 99
    ledger = _make_ledger_with_one_hosted(observer_cid, q0=10, q_remaining=10)
    result = cog.attempt_ingestion(observer_cid, ghost_cid, ledger)
    assert result["gain"] == 8
    assert result["received"] == 0    # 満腹
    assert result["digested"] == 8    # 全部消化分
    assert cog.ghost_residual_Q[ghost_cid] == 0  # ghost は空っぽに


# ─────────────────────────────────────────────────────────
# reap_ghosts_step (Q ベース、step 末)
# ─────────────────────────────────────────────────────────

def test_reap_ghosts_step_only_zero_residual():
    cog = SubjectLayer()
    # ghost A: residual_Q=5、ghost B: residual_Q=0
    cog.birth(lid=1, phase_sig=0.0, current_window=0)
    cid_a = cog.detach(1, current_window=1, residual_Q=5, current_step=10)
    cog.birth(lid=2, phase_sig=0.1, current_window=0)
    cid_b = cog.detach(2, current_window=1, residual_Q=0, current_step=10)
    reaped = cog.reap_ghosts_step(15)
    assert cid_b in reaped
    assert cid_a not in reaped  # まだ residual_Q > 0


def test_reap_ghosts_step_idempotent_when_nothing_to_reap():
    cog = SubjectLayer()
    cog.birth(lid=1, phase_sig=0.0, current_window=0)
    cid = cog.detach(1, current_window=1, residual_Q=3, current_step=10)
    assert cog.reap_ghosts_step(15) == []
    assert cog.ghost_residual_Q[cid] == 3


def test_reap_ghosts_step_drained_by_ingestion_then_reaped():
    """ingestion で residual_Q が 0 になった ghost が次 reap_ghosts_step で消える"""
    cog, ghost_cid = _make_cog_with_one_ghost(residual_q=4)
    observer_cid = 99
    ledger = _make_ledger_with_one_hosted(observer_cid, q0=20, q_remaining=10)
    cog.attempt_ingestion(observer_cid, ghost_cid, ledger)
    assert cog.ghost_residual_Q[ghost_cid] == 0
    reaped = cog.reap_ghosts_step(150)
    assert ghost_cid in reaped
    assert ghost_cid not in cog.ghost_residual_Q


# ─────────────────────────────────────────────────────────
# 1 ghost を複数 cid が摂食した場合 (順次 cid_id 順)
# ─────────────────────────────────────────────────────────

def test_multiple_eaters_first_takes_all_then_empty():
    """同 ghost に対し 2 cid が摂食試行: 先に来た方が全部取る、後続は空摂食"""
    cog, ghost_cid = _make_cog_with_one_ghost(residual_q=6)
    ledger = SpendAuditLedger()
    for cid_id, q_rem in [(11, 10), (22, 12)]:
        ledger.ledger[cid_id] = {
            "v14_q0": 20, "v14_q_remaining": q_rem,
            "v14_virtual_attention": {}, "v14_virtual_familiarity": {},
            "v14_last_snapshot": None, "v14_shadow_pulse_index": 0,
            "v14_prev_member_alive_links": frozenset(),
            "v14_prev_member_r": {}, "member_nodes": frozenset(),
            "registered_at": (0, 0), "v14_last_event_global_step": None,
        }
    # 11 が先 (cid_id 昇順)
    r1 = cog.attempt_ingestion(11, ghost_cid, ledger)
    assert r1["gain"] == 6 and r1["received"] == 6
    assert cog.ghost_residual_Q[ghost_cid] == 0
    # 22 は空摂食
    r2 = cog.attempt_ingestion(22, ghost_cid, ledger)
    assert r2["gain"] == 0
    assert r2["was_empty"] is True
    assert r2["received"] == 0
    # ledger Q_remaining も更新されてる
    assert ledger.ledger[11]["v14_q_remaining"] == 16
    assert ledger.ledger[22]["v14_q_remaining"] == 12  # 不変


# ─────────────────────────────────────────────────────────
# 統合: detach → ingestion → reap の 1 サイクル
# ─────────────────────────────────────────────────────────

def test_full_cycle_detach_ingest_reap():
    cog = SubjectLayer()
    cog.birth(lid=1, phase_sig=0.0, current_window=0)
    ghost_cid = cog.detach(1, current_window=2, residual_Q=7, current_step=50)
    ledger = _make_ledger_with_one_hosted(99, q0=20, q_remaining=5)
    # step 50: ingestion
    result = cog.attempt_ingestion(99, ghost_cid, ledger)
    assert result["received"] == 7
    # step 50 末: reap
    reaped = cog.reap_ghosts_step(50)
    assert ghost_cid in reaped
    # _reaped_history に記録
    rh = cog._reaped_history[-1]
    assert rh["cid"] == ghost_cid
    assert rh["initial_residual_Q"] == 7
    assert rh["final_residual_Q"] == 0
    assert rh["reap_reason"] == "residual_Q_zero"
    assert rh["host_lost_step"] == 50
    assert rh["reaped_step"] == 50
    assert rh["ghost_duration_steps"] == 0


# ─────────────────────────────────────────────────────────
# 手動 runner (pytest 不要)
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    g = dict(globals())
    fns = [(k, v) for k, v in g.items()
           if k.startswith("test_") and callable(v)]
    n_pass = 0
    n_fail = 0
    for name, fn in fns:
        try:
            fn()
            n_pass += 1
            print(f"  PASS  {name}")
        except Exception:
            n_fail += 1
            print(f"  FAIL  {name}")
            traceback.print_exc()
    print(f"\n{'─' * 60}\n  {n_pass} passed, {n_fail} failed (of {len(fns)})")
    sys.exit(1 if n_fail else 0)
