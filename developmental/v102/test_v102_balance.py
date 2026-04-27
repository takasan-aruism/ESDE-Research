#!/usr/bin/env python3
"""
v10.2 Probabilistic Cognitive-Conscious Balance 単体テスト
==========================================================
decide_balance() の数式 / Q=0 / C=0 特殊扱い、observe_step の
E3 認知/意識分岐、E1/E2 不変、双方向、phantom、step 内動的連鎖、
bit-identity smoke の 10 件。

run: python -m pytest test_v102_balance.py -v
     または python test_v102_balance.py
"""

from __future__ import annotations

import sys
import os
import subprocess
import hashlib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
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

from v102_memory_readout import SubjectLayer
from v914_spend_audit_ledger import SpendAuditLedger, decide_balance


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _make_cog_with_one_ghost(residual_q: int, host_lid_birth: int = 1):
    cog = SubjectLayer()
    cid = cog.birth(lid=host_lid_birth, phase_sig=0.0, current_window=0)
    cog.detach(lid=host_lid_birth, current_window=1,
               residual_Q=residual_q, current_step=100)
    return cog, cid


def _register_hosted_cid(cog, lid, q0, q_remaining,
                         ledger=None, member_nodes=None):
    """hosted cid を作って ledger にも entry を入れる最小ヘルパ。"""
    cid = cog.birth(lid=lid, phase_sig=0.0, current_window=0)
    if ledger is not None:
        ledger.ledger[cid] = {
            "v14_q0": q0,
            "v14_q_remaining": q_remaining,
            "v14_virtual_attention": {},
            "v14_virtual_familiarity": {},
            "v14_last_snapshot": None,
            "v14_shadow_pulse_index": 0,
            "v14_prev_member_alive_links": frozenset(),
            "v14_prev_member_r": {},
            "member_nodes":
                frozenset(member_nodes) if member_nodes
                else frozenset({lid * 10, lid * 10 + 1}),
            "registered_at": (0, 0),
            "v14_last_event_global_step": None,
        }
    return cid


def _make_minimal_ctx(cid, member_nodes):
    return {
        "b_gen": 5.0,
        "member_nodes": frozenset(member_nodes),
        "e_t": {"n_local": 0, "s_avg_local": 0.0,
                "r_local": 0.0, "theta_avg_local": 0.0},
        "m_c": {"n_core": 0, "s_avg": 0.0,
                "r_core": 0.0, "phase_sig": 0.0},
        "attn_nodes": frozenset(),
        "other_cids": frozenset(),
    }


# ─────────────────────────────────────────────────────────
# Test 1: decide_balance simple formula
# ─────────────────────────────────────────────────────────

def test_v102_balance_decision_simple_formula():
    """P(認知) = Q/(Q+C). Q=4, C=1 で多数回 draw → 認知 ≈ 80% を期待。"""
    rng = np.random.default_rng(0xBA1A2C ^ 1)
    n_trials = 10000
    n_cog = 0
    for _ in range(n_trials):
        d = decide_balance(
            cognition_candidate=True,
            consciousness_candidate=True,
            Q=4, C=1, balance_rng=rng,
        )
        if d == "cognition":
            n_cog += 1
    ratio = n_cog / n_trials
    assert 0.78 <= ratio <= 0.82, f"P(認知) = {ratio:.4f}, 期待 ≈ 0.80"


# ─────────────────────────────────────────────────────────
# Test 2: Q=0 excludes cognition
# ─────────────────────────────────────────────────────────

def test_v102_q_zero_excludes_cognition():
    """Q=0: 認知候補から除外 → 意識候補のみなら意識確定、両 0 なら skip"""
    rng = np.random.default_rng(0)
    # Q=0, C=3, 意識候補あり → 意識確定
    d = decide_balance(
        cognition_candidate=False, consciousness_candidate=True,
        Q=0, C=3, balance_rng=rng,
    )
    assert d == "consciousness"

    # Q=0, C=0, 候補なし → skip
    d = decide_balance(
        cognition_candidate=False, consciousness_candidate=False,
        Q=0, C=0, balance_rng=rng,
    )
    assert d == "skip"


# ─────────────────────────────────────────────────────────
# Test 3: C=0 excludes consciousness
# ─────────────────────────────────────────────────────────

def test_v102_c_zero_excludes_consciousness():
    """C=0: 意識候補があっても意識発動できない (skip 扱い)、
    認知候補あれば認知確定"""
    rng = np.random.default_rng(0)
    # C=0, Q=5, 意識候補成立 (相手 ghost residual_Q>0) ただし C=0 → 認知に流れる
    d = decide_balance(
        cognition_candidate=True, consciousness_candidate=True,
        Q=5, C=0, balance_rng=rng,
    )
    assert d == "cognition"

    # C=0, Q=0, 意識候補成立だが両資源 0 → skip
    d = decide_balance(
        cognition_candidate=False, consciousness_candidate=True,
        Q=0, C=0, balance_rng=rng,
    )
    assert d == "skip"


# ─────────────────────────────────────────────────────────
# Test 4: E3 consciousness fires ingestion, no E3 spend
# ─────────────────────────────────────────────────────────

def test_v102_e3_consciousness_fires_ingestion_no_spend():
    """意識当選: q_remaining 不変、C-1、virtual_* 不変、ingestion_event 1 行"""
    cog = SubjectLayer()
    # observer cid (hosted) を作成、Q=10 で C=5
    ledger = SpendAuditLedger(
        cog=cog, ingestion_rng=np.random.default_rng(0),
        balance_rng=_AlwaysConsciousness())
    obs_cid = _register_hosted_cid(
        cog, lid=1, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={10, 11})
    cog.C[obs_cid] = 5
    # ghost cid を作成、residual_Q=8
    ghost_lid = 2
    ghost_cid = cog.birth(lid=ghost_lid, phase_sig=0.0, current_window=0)
    cog.detach(lid=ghost_lid, current_window=1, residual_Q=8, current_step=10)
    # ledger に ghost も entry (E3 onset でアクセスされる)
    ledger.ledger[ghost_cid] = {
        "v14_q0": 8, "v14_q_remaining": 0,
        "v14_virtual_attention": {}, "v14_virtual_familiarity": {},
        "v14_last_snapshot": None, "v14_shadow_pulse_index": 0,
        "v14_prev_member_alive_links": frozenset(),
        "v14_prev_member_r": {},
        "member_nodes": frozenset({20, 21}),
        "registered_at": (0, 0),
        "v14_last_event_global_step": None,
    }
    # node_to_cids の手動更新 (本来は observe_step 内の lazy registration)
    for n in [10, 11]:
        ledger._node_to_cids.setdefault(n, set()).add(obs_cid)
    for n in [20, 21]:
        ledger._node_to_cids.setdefault(n, set()).add(ghost_cid)

    # alive link で observer-ghost を共有させる
    alive_l_set = {(11, 20)}  # node 11 (obs) - node 20 (ghost) を共有
    # observe_step 呼ぶ
    cid_ctx = {obs_cid: _make_minimal_ctx(obs_cid, {10, 11})}
    ledger.observe_step(
        window=1, step=0, global_step=10,
        alive_l_set=alive_l_set, state_r={},
        cid_ctx=cid_ctx,
    )

    # 検証
    # q_remaining は摂食で +received。Q0 上限 10、もとが 10 なので received=0、digested=8
    assert ledger.ledger[obs_cid]["v14_q_remaining"] == 10  # 不変 (Q0 で頭打ち)
    # virtual_* は 1 回も更新されていない (空)
    assert ledger.ledger[obs_cid]["v14_virtual_attention"] == {}
    assert ledger.ledger[obs_cid]["v14_virtual_familiarity"] == {}
    # C は 5 → 4
    assert cog.C[obs_cid] == 4
    # ingestion_event 1 行
    assert len(ledger.ingestion_events) == 1
    assert ledger.ingestion_events[0]["gain"] == 8


# ─────────────────────────────────────────────────────────
# Test 5: E3 cognition fires spend + C+1
# ─────────────────────────────────────────────────────────

def test_v102_e3_cognition_fires_spend_increments_c():
    """認知当選: Q-1、C+1、ingestion 不発火"""
    cog = SubjectLayer()
    ledger = SpendAuditLedger(
        cog=cog, ingestion_rng=np.random.default_rng(0),
        balance_rng=_AlwaysCognition(),
        delta_fn=lambda a, b: (0.0, {}))
    obs_cid = _register_hosted_cid(
        cog, lid=1, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={10, 11})
    cog.C[obs_cid] = 5
    ghost_lid = 2
    ghost_cid = cog.birth(lid=ghost_lid, phase_sig=0.0, current_window=0)
    cog.detach(lid=ghost_lid, current_window=1, residual_Q=8, current_step=10)
    ledger.ledger[ghost_cid] = {
        "v14_q0": 8, "v14_q_remaining": 0,
        "v14_virtual_attention": {}, "v14_virtual_familiarity": {},
        "v14_last_snapshot": None, "v14_shadow_pulse_index": 0,
        "v14_prev_member_alive_links": frozenset(),
        "v14_prev_member_r": {},
        "member_nodes": frozenset({20, 21}),
        "registered_at": (0, 0),
        "v14_last_event_global_step": None,
    }
    for n in [10, 11]:
        ledger._node_to_cids.setdefault(n, set()).add(obs_cid)
    for n in [20, 21]:
        ledger._node_to_cids.setdefault(n, set()).add(ghost_cid)

    alive_l_set = {(11, 20)}
    cid_ctx = {obs_cid: _make_minimal_ctx(obs_cid, {10, 11})}
    ledger.observe_step(
        window=1, step=0, global_step=10,
        alive_l_set=alive_l_set, state_r={},
        cid_ctx=cid_ctx,
    )

    # 認知 spend が走った: Q-1
    assert ledger.ledger[obs_cid]["v14_q_remaining"] == 9
    # C は 5 → 6
    assert cog.C[obs_cid] == 6
    # ingestion 不発火
    assert len(ledger.ingestion_events) == 0
    # ghost は無傷
    assert cog.ghost_residual_Q[ghost_cid] == 8


# ─────────────────────────────────────────────────────────
# Test 6: E1/E2 unconditional spend, no C change
# ─────────────────────────────────────────────────────────

def test_v102_e1_e2_unconditional_spend_no_c_change():
    """E1/E2: 確率対象外、Q-1 のみ、C 不変"""
    cog = SubjectLayer()
    ledger = SpendAuditLedger(
        cog=cog, ingestion_rng=np.random.default_rng(0),
        balance_rng=_AlwaysCognition(),
        delta_fn=lambda a, b: (0.0, {}))
    obs_cid = _register_hosted_cid(
        cog, lid=1, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={10, 11})
    cog.C[obs_cid] = 3

    # E1 死生 (member link が alive→dead) を直接 _process_event で再現
    entry = ledger.ledger[obs_cid]
    ctx = _make_minimal_ctx(obs_cid, {10, 11})
    ledger._process_event(
        cid=obs_cid, entry=entry, ctx=ctx,
        event_type="E1_death", link_id="(10,11)",
        window=0, step=0, global_step=5,
    )
    assert entry["v14_q_remaining"] == 9
    assert cog.C[obs_cid] == 3   # E1 では C は変わらない


# ─────────────────────────────────────────────────────────
# Test 7: Bidirectional E3 (hosted-hosted): both cognition
# ─────────────────────────────────────────────────────────

def test_v102_bidirectional_e3_both_cognition():
    """hosted ↔ hosted: 三項共鳴は v10.3 以降のため両者認知確定"""
    cog = SubjectLayer()
    ledger = SpendAuditLedger(
        cog=cog, ingestion_rng=np.random.default_rng(0),
        balance_rng=_AlwaysConsciousness(),  # 意識ばかり引いても認知に倒れる
        delta_fn=lambda a, b: (0.0, {}))
    cid_a = _register_hosted_cid(
        cog, lid=1, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={10, 11})
    cid_b = _register_hosted_cid(
        cog, lid=2, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={20, 21})
    cog.C[cid_a] = 5
    cog.C[cid_b] = 5
    for n in [10, 11]:
        ledger._node_to_cids.setdefault(n, set()).add(cid_a)
    for n in [20, 21]:
        ledger._node_to_cids.setdefault(n, set()).add(cid_b)

    alive_l_set = {(11, 20)}
    cid_ctx = {
        cid_a: _make_minimal_ctx(cid_a, {10, 11}),
        cid_b: _make_minimal_ctx(cid_b, {20, 21}),
    }
    ledger.observe_step(
        window=1, step=0, global_step=10,
        alive_l_set=alive_l_set, state_r={},
        cid_ctx=cid_ctx,
    )

    # 両者ともに認知 spend (Q-1, C+1)
    assert ledger.ledger[cid_a]["v14_q_remaining"] == 9
    assert ledger.ledger[cid_b]["v14_q_remaining"] == 9
    assert cog.C[cid_a] == 6
    assert cog.C[cid_b] == 6
    # ingestion 不発火
    assert len(ledger.ingestion_events) == 0


# ─────────────────────────────────────────────────────────
# Test 8: Phantom (reaped) → cognition only
# ─────────────────────────────────────────────────────────

def test_v102_phantom_e3_cognition_only():
    """phantom (cog から消えた cid) は認知確定 (主題 §3.1 C)"""
    cog = SubjectLayer()
    ledger = SpendAuditLedger(
        cog=cog, ingestion_rng=np.random.default_rng(0),
        balance_rng=_AlwaysConsciousness(),
        delta_fn=lambda a, b: (0.0, {}))
    obs_cid = _register_hosted_cid(
        cog, lid=1, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={10, 11})
    cog.C[obs_cid] = 5

    # phantom: cog にも ledger にも居る (member_nodes 由来) が、is_hosted=False で is_ghost=False
    phantom_cid = cog.birth(lid=2, phase_sig=0.0, current_window=0)
    cog.detach(lid=2, current_window=1, residual_Q=0, current_step=10)
    cog.reap_ghosts_step(11)  # reap → phantom 化
    # ledger 側の entry を残す (phantom は ledger にだけ居る)
    ledger.ledger[phantom_cid] = {
        "v14_q0": 5, "v14_q_remaining": 0,
        "v14_virtual_attention": {}, "v14_virtual_familiarity": {},
        "v14_last_snapshot": None, "v14_shadow_pulse_index": 0,
        "v14_prev_member_alive_links": frozenset(),
        "v14_prev_member_r": {},
        "member_nodes": frozenset({20, 21}),
        "registered_at": (0, 0),
        "v14_last_event_global_step": None,
    }
    for n in [10, 11]:
        ledger._node_to_cids.setdefault(n, set()).add(obs_cid)
    for n in [20, 21]:
        ledger._node_to_cids.setdefault(n, set()).add(phantom_cid)

    alive_l_set = {(11, 20)}
    cid_ctx = {obs_cid: _make_minimal_ctx(obs_cid, {10, 11})}
    ledger.observe_step(
        window=1, step=0, global_step=12,
        alive_l_set=alive_l_set, state_r={},
        cid_ctx=cid_ctx,
    )

    # 認知確定: Q-1, C+1
    assert ledger.ledger[obs_cid]["v14_q_remaining"] == 9
    assert cog.C[obs_cid] == 6
    # phantom も ingestion 不発火 (意識候補なし)
    assert len(ledger.ingestion_events) == 0


# ─────────────────────────────────────────────────────────
# Test 9: Step internal dynamic chain (主題 §3.1 F)
# ─────────────────────────────────────────────────────────

def test_v102_step_internal_dynamic_chain():
    """先行 cid が意識当選で食べきり → 後続 cid の候補集合が変わり認知確定。

    pair (5,10) で 5 が意識当選 → ghost 10 食べきり
    pair (7,10) では 7 視点で residual_Q=0 → 認知確定
    """
    cog = SubjectLayer()
    # 5, 7 を強制発番するため、5 個の cid を生み (0..4)、最後 5 を hosted で確保
    for _ in range(5):
        cog._next_cid += 1  # 5 番から始まるよう ID 操作
    ledger = SpendAuditLedger(
        cog=cog, ingestion_rng=np.random.default_rng(0),
        balance_rng=_AlwaysConsciousness(),
        delta_fn=lambda a, b: (0.0, {}))
    cid_5 = _register_hosted_cid(
        cog, lid=1, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={50, 51})
    assert cid_5 == 5
    # cid_6 をパディング (cid_id 増加)
    cog._next_cid = 7
    cid_7 = _register_hosted_cid(
        cog, lid=2, q0=10, q_remaining=10, ledger=ledger,
        member_nodes={70, 71})
    assert cid_7 == 7
    cog.C[cid_5] = 5
    cog.C[cid_7] = 5

    # ghost 10 を作成 (residual_Q=8)
    cog._next_cid = 10
    g_lid = 3
    cid_10 = cog.birth(lid=g_lid, phase_sig=0.0, current_window=0)
    cog.detach(lid=g_lid, current_window=1, residual_Q=8, current_step=10)
    assert cid_10 == 10
    ledger.ledger[cid_10] = {
        "v14_q0": 8, "v14_q_remaining": 0,
        "v14_virtual_attention": {}, "v14_virtual_familiarity": {},
        "v14_last_snapshot": None, "v14_shadow_pulse_index": 0,
        "v14_prev_member_alive_links": frozenset(),
        "v14_prev_member_r": {},
        "member_nodes": frozenset({100, 101}),
        "registered_at": (0, 0),
        "v14_last_event_global_step": None,
    }
    for n in [50, 51]:
        ledger._node_to_cids.setdefault(n, set()).add(cid_5)
    for n in [70, 71]:
        ledger._node_to_cids.setdefault(n, set()).add(cid_7)
    for n in [100, 101]:
        ledger._node_to_cids.setdefault(n, set()).add(cid_10)

    # 5-10 と 7-10 の両方の link を alive に
    alive_l_set = {(51, 100), (71, 101)}
    cid_ctx = {
        cid_5: _make_minimal_ctx(cid_5, {50, 51}),
        cid_7: _make_minimal_ctx(cid_7, {70, 71}),
    }
    ledger.observe_step(
        window=1, step=0, global_step=12,
        alive_l_set=alive_l_set, state_r={},
        cid_ctx=cid_ctx,
    )

    # 5 は意識当選 → 食べきり, C-1, Q+received(0、Q0 で頭打ち)
    # 7 は residual_Q=0 ≠ 意識候補 → 認知確定 (Q-1, C+1)
    assert cog.ghost_residual_Q[cid_10] == 0  # 食べきり
    assert cog.C[cid_5] == 4  # 5-1
    assert ledger.ledger[cid_5]["v14_q_remaining"] == 10  # Q0=10、頭打ち

    assert cog.C[cid_7] == 6  # 5+1 (認知)
    assert ledger.ledger[cid_7]["v14_q_remaining"] == 9  # Q-1
    # ingestion_event は 5 のぶんだけ
    assert len(ledger.ingestion_events) == 1
    assert ledger.ingestion_events[0]["observer_cid"] == cid_5


# ─────────────────────────────────────────────────────────
# Test 10: Bit-identity smoke (2 連続 run、24 CSV MD5 一致)
# ─────────────────────────────────────────────────────────

def test_v102_smoke_bit_identity():
    """smoke 2 連続 run で出力 CSV が完全一致 (v10.2 内部 bit-identity)。

    実時間がかかるため、tracking_windows=2 / window_steps=200 で短く回す。
    seed=42 固定。
    """
    runner = _HERE / "v102_memory_readout.py"
    if not runner.exists():
        return  # スキップ (パス変更時の保護)

    def _hash_dir(d: Path) -> dict:
        result = {}
        for p in sorted(d.rglob("*.csv")):
            with open(p, "rb") as f:
                result[str(p.relative_to(d))] = hashlib.md5(
                    f.read()).hexdigest()
        return result

    # 既存の diag_v102_smoke_a/b があれば消す
    import shutil
    for tag in ("smoke_v102_a", "smoke_v102_b"):
        d = Path(f"diag_v102_{tag}")
        if d.exists():
            shutil.rmtree(d)

    common = [sys.executable, str(runner),
              "--seed", "42", "--maturation-windows", "5",
              "--tracking-windows", "2", "--window-steps", "200"]
    subprocess.run(common + ["--tag", "smoke_v102_a"],
                   check=True, capture_output=True)
    subprocess.run(common + ["--tag", "smoke_v102_b"],
                   check=True, capture_output=True)

    h_a = _hash_dir(Path("diag_v102_smoke_v102_a"))
    h_b = _hash_dir(Path("diag_v102_smoke_v102_b"))
    assert h_a == h_b, (
        "bit-identity 違反: smoke 2 連続 run で CSV が一致しない\n"
        f"a: {h_a}\nb: {h_b}\n")


# ─────────────────────────────────────────────────────────
# Helper RNG: 常に認知 / 常に意識を引く
# ─────────────────────────────────────────────────────────

class _AlwaysCognition:
    """balance_rng.random() を 0 にする (P(認知) = 1)。"""
    def random(self):
        return 0.0

    def integers(self, low, high):
        return low


class _AlwaysConsciousness:
    """balance_rng.random() を 1 にする (P(認知) = 0)。"""
    def random(self):
        return 0.999999

    def integers(self, low, high):
        return low


# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    tests = [
        test_v102_balance_decision_simple_formula,
        test_v102_q_zero_excludes_cognition,
        test_v102_c_zero_excludes_consciousness,
        test_v102_e3_consciousness_fires_ingestion_no_spend,
        test_v102_e3_cognition_fires_spend_increments_c,
        test_v102_e1_e2_unconditional_spend_no_c_change,
        test_v102_bidirectional_e3_both_cognition,
        test_v102_phantom_e3_cognition_only,
        test_v102_step_internal_dynamic_chain,
        test_v102_smoke_bit_identity,
    ]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except Exception as e:
            fails += 1
            print(f"FAIL: {t.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{len(tests) - fails}/{len(tests)} PASSED")
    sys.exit(0 if fails == 0 else 1)
