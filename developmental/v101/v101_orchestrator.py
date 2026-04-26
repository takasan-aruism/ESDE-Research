"""
v9.18 段階 5 — per_step orchestrator + window CSV writer [A]
=============================================================

v918_cid_self_buffer の CidSelfBuffer に対して per_step で v18_* を更新する
orchestrator、および per_cid_window_v18 CSV (新規) / per_subject の追加列を
提供する。

責務:
  - v918_update_per_step : 毎 cumulative_step ごとに呼ばれ、
                            hosted cid すべての v18_* を更新
  - v918_finalize_ghost_if_needed : ghost 化検出時に _finalize を呼ぶ
  - v918_finalize_all_at_tracking_end : tracking 終了時に全 hosted の _final 確定
  - build_v918_subject_columns : per_subject CSV 追加列を返す
  - write_v18_window_trajectory_csv : 新規 selfread CSV を書く

設計 (Q1-Q7 確定後):
  - per_step 計算 (Taka 2026-04-23 判断 (X))
  - 計算位置は event Fetch ループ後、cumulative_step += 1 直前
  - 既存 per_window.csv (Layer A) には v18_* を追加しない (bit-identity 維持)
    代わりに selfread/per_cid_window_v18_seed{N}.csv を新規作成
  - v18_* は run 中の分岐条件に使わない (承認条件 #12)

規約 (A/B 分離):
  - 本ファイルは [A]。v918_cid_self_buffer (B) と v918_unity_metrics /
    v918_theta_distance (pure function) を read-only で参照
  - CidSelfBuffer への書き戻しは orchestrator の責務 (計算モジュールは
    pure function、書き戻しなし)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from v101_cid_self_buffer import CidSelfBuffer
from v101_unity_metrics import compute_unity_metrics
from v101_theta_distance import compute_theta_distance


# ────────────────────────────────────────────────────────────
# per_step orchestration
# ────────────────────────────────────────────────────────────

def v918_update_per_step(
    self_buffers: Dict[int, CidSelfBuffer],
    cog: Any,
    vl: Any,
    engine: Any,
    v914_ledger: Any,
    current_step: int,
) -> None:
    """
    毎 step 呼ばれ、self_buffers 内の全 CID の v18_* を更新する。

    更新ポリシ:
      - ghost 化済 (current_lid[cid] is None) or 未登録 label: 更新スキップ +
        初回検出なら _finalize_v18_values(reason='ghost') を呼ぶ
      - 正常 hosted: cumulative_cognitive_gain / V_unified / theta_distance 更新

    v18_* は run 中の分岐条件に使わない (GPT §8.2)。
    """
    labels = getattr(vl, "labels", {})
    current_lid_map = cog.current_lid
    ledger_map = v914_ledger.ledger

    for cid_id, self_buffer in self_buffers.items():
        if self_buffer.v18_finalized_at_step is not None:
            continue

        current_lid = current_lid_map.get(cid_id)
        if current_lid is None or current_lid not in labels:
            self_buffer.finalize_v18_values(
                current_step=current_step, reason="ghost"
            )
            continue

        ledger_entry = ledger_map.get(cid_id)
        if ledger_entry is None:
            continue
        q_remaining = int(ledger_entry.get("v14_q_remaining", self_buffer.Q0))

        # C: cumulative_cognitive_gain 更新
        gain = self_buffer.Q0 - q_remaining
        if gain < 0:
            gain = 0
        if gain > self_buffer.Q0:
            gain = self_buffer.Q0
        self_buffer.v18_cumulative_cognitive_gain = int(gain)

        # 現在の member_nodes と θ を取得
        current_member_nodes = frozenset(labels[current_lid]["nodes"])
        current_theta_by_node: Dict[int, float] = {}
        state_theta = engine.state.theta
        for n in current_member_nodes:
            if 0 <= n < len(state_theta):
                current_theta_by_node[n] = float(state_theta[n])

        # A-Gemini: V_unified
        unity_result = compute_unity_metrics(
            current_theta_by_node=current_theta_by_node,
            birth_v_unified=self_buffer.v18_birth_v_unified,
            current_member_nodes=set(current_member_nodes),
        )
        self_buffer.v18_unity_direction = unity_result["unity_direction"]
        self_buffer.v18_unity_concentration = unity_result["unity_concentration"]
        self_buffer.v18_unity_direction_shift = unity_result["unity_direction_shift"]
        self_buffer.v18_unity_k = int(unity_result["k"])

        # A-GPT: theta_distance
        distance_result = compute_theta_distance(
            current_theta_by_node=current_theta_by_node,
            birth_theta_by_node=self_buffer.v18_birth_theta_by_node,
            current_member_nodes=set(current_member_nodes),
            birth_member_nodes=set(self_buffer.v18_birth_member_nodes),
        )
        self_buffer.v18_theta_distance_from_birth = distance_result[
            "theta_distance_from_birth"
        ]
        self_buffer.v18_theta_distance_coverage_ratio = float(
            distance_result["coverage_ratio"]
        )


# ────────────────────────────────────────────────────────────
# window snapshot (per-cid-per-window record)
# ────────────────────────────────────────────────────────────

def v918_snapshot_window(
    self_buffers: Dict[int, CidSelfBuffer],
    cog: Any,
    vl: Any,
    window_idx: int,
    cumulative_step: int,
    accumulator: List[dict],
) -> None:
    """
    window 終了時の v18_* snapshot を accumulator に append。

    hosted cid のみ (ghost 化済 / 未登録 lid の cid はスキップ)。
    ghost 化済でも _final 前の record は別途残す必要はない (それは _final で捕捉)。
    """
    labels = getattr(vl, "labels", {})
    current_lid_map = cog.current_lid

    for cid_id, self_buffer in self_buffers.items():
        current_lid = current_lid_map.get(cid_id)
        if current_lid is None or current_lid not in labels:
            continue
        if self_buffer.v18_finalized_at_step is not None:
            continue

        accumulator.append({
            "cid_id": int(cid_id),
            "window": int(window_idx),
            "step_at_window_end": int(cumulative_step),
            "v18_cognitive_gain_at_window_end": int(
                self_buffer.v18_cumulative_cognitive_gain
            ),
            "v18_v_unified_concentration_at_window_end":
                self_buffer.v18_unity_concentration,
            "v18_v_unified_direction_shift_at_window_end":
                self_buffer.v18_unity_direction_shift,
            "v18_v_unified_k_at_window_end": int(self_buffer.v18_unity_k),
            "v18_theta_distance_from_birth_at_window_end":
                self_buffer.v18_theta_distance_from_birth,
            "v18_theta_distance_coverage_ratio_at_window_end":
                float(self_buffer.v18_theta_distance_coverage_ratio),
            # 補助ログ (selfread): 生の argument
            "v18_v_unified_direction_at_window_end":
                self_buffer.v18_unity_direction,
        })


# ────────────────────────────────────────────────────────────
# tracking-end finalize (ghost 化していない hosted も _final 確定)
# ────────────────────────────────────────────────────────────

def v918_finalize_all_at_tracking_end(
    self_buffers: Dict[int, CidSelfBuffer],
    cumulative_step: int,
) -> int:
    """
    tracking 終了時に未 _final の全 CID を tracking_end reason で確定。

    Returns
    -------
    int : 実際に確定した件数
    """
    count = 0
    for self_buffer in self_buffers.values():
        if self_buffer.v18_finalized_at_step is None:
            if self_buffer.finalize_v18_values(
                current_step=cumulative_step, reason="tracking_end"
            ):
                count += 1
    return count


# ────────────────────────────────────────────────────────────
# per_subject CSV 追加列
# ────────────────────────────────────────────────────────────

V918_SUBJECT_COLUMNS = (
    "v18_cognitive_gain_final",
    "v18_v_unified_concentration_birth",
    "v18_v_unified_concentration_final",
    "v18_v_unified_direction_shift_final",
    "v18_v_unified_k_final",
    "v18_theta_distance_from_birth_final",
    "v18_theta_distance_coverage_ratio_final",
    # 補助 (finalize メタ)
    "v18_finalized_at_step",
    "v18_finalize_reason",
)


def _round_or_unformed(v, dec: int = 6):
    if v is None:
        return "unformed"
    try:
        return round(float(v), dec)
    except (TypeError, ValueError):
        return "unformed"


def build_v918_subject_columns(
    registry: Dict[int, CidSelfBuffer], cid: int
) -> dict:
    """per_subject CSV に追加する v918_* 列 (9 列) を dict で返す。"""
    buf = registry.get(cid)
    if buf is None:
        return {col: "unformed" for col in V918_SUBJECT_COLUMNS}

    return {
        "v18_cognitive_gain_final": (
            int(buf.v18_cognitive_gain_final)
            if buf.v18_cognitive_gain_final is not None else "unformed"
        ),
        "v18_v_unified_concentration_birth": _round_or_unformed(
            buf.v18_v_unified_concentration_birth
        ),
        "v18_v_unified_concentration_final": _round_or_unformed(
            buf.v18_v_unified_concentration_final
        ),
        "v18_v_unified_direction_shift_final": _round_or_unformed(
            buf.v18_v_unified_direction_shift_final
        ),
        "v18_v_unified_k_final": (
            int(buf.v18_v_unified_k_final)
            if buf.v18_v_unified_k_final is not None else "unformed"
        ),
        "v18_theta_distance_from_birth_final": _round_or_unformed(
            buf.v18_theta_distance_from_birth_final
        ),
        "v18_theta_distance_coverage_ratio_final": _round_or_unformed(
            buf.v18_theta_distance_coverage_ratio_final
        ),
        "v18_finalized_at_step": (
            int(buf.v18_finalized_at_step)
            if buf.v18_finalized_at_step is not None else "unformed"
        ),
        "v18_finalize_reason": (
            buf.v18_finalize_reason if buf.v18_finalize_reason else "unformed"
        ),
    }


# ────────────────────────────────────────────────────────────
# per_cid_window CSV (新規)
# ────────────────────────────────────────────────────────────

V918_WINDOW_COLUMNS = (
    "seed",
    "cid_id",
    "window",
    "step_at_window_end",
    "v18_cognitive_gain_at_window_end",
    "v18_v_unified_concentration_at_window_end",
    "v18_v_unified_direction_shift_at_window_end",
    "v18_v_unified_k_at_window_end",
    "v18_theta_distance_from_birth_at_window_end",
    "v18_theta_distance_coverage_ratio_at_window_end",
    # 補助 (selfread)
    "v18_v_unified_direction_at_window_end",
)


def write_v18_window_trajectory_csv(
    accumulator: List[dict],
    seed: int,
    out_path: Path,
) -> int:
    """
    per_cid × per_window の v18_* 軌跡を CSV に出力。

    Returns
    -------
    int : 書き出した行数
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for entry in accumulator:
        rows.append({
            "seed": int(seed),
            "cid_id": int(entry["cid_id"]),
            "window": int(entry["window"]),
            "step_at_window_end": int(entry["step_at_window_end"]),
            "v18_cognitive_gain_at_window_end":
                int(entry["v18_cognitive_gain_at_window_end"]),
            "v18_v_unified_concentration_at_window_end": _round_or_unformed(
                entry.get("v18_v_unified_concentration_at_window_end")
            ),
            "v18_v_unified_direction_shift_at_window_end": _round_or_unformed(
                entry.get("v18_v_unified_direction_shift_at_window_end")
            ),
            "v18_v_unified_k_at_window_end":
                int(entry["v18_v_unified_k_at_window_end"]),
            "v18_theta_distance_from_birth_at_window_end": _round_or_unformed(
                entry.get("v18_theta_distance_from_birth_at_window_end")
            ),
            "v18_theta_distance_coverage_ratio_at_window_end": _round_or_unformed(
                entry.get("v18_theta_distance_coverage_ratio_at_window_end")
            ),
            "v18_v_unified_direction_at_window_end": _round_or_unformed(
                entry.get("v18_v_unified_direction_at_window_end")
            ),
        })

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=V918_WINDOW_COLUMNS)
        writer.writeheader()
        if rows:
            writer.writerows(rows)

    return len(rows)
