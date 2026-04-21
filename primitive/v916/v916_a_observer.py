"""
v9.16 段階 3 Layer C — A-side Observer [A]
==========================================

研究者向け観察レイヤ。CidSelfBuffer を read-only でのみ参照し、
per_subject CSV への v915_* 列追加、per_cid_self CSV 出力、
observation_log CSV (段階 3 新規) 出力等を行う。

規約 (A/B 分離):
  - 本ファイルは [A]。v916_cid_self_buffer を read-only でのみ参照
  - 参照は `_a_observer_*` 接頭辞メソッド経由のみ
  - CidSelfBuffer の内部フィールドへの直接書き込み禁止
  - 断定表現 (「自己」「意識」等) をレポート/コードで使わない
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from v916_cid_self_buffer import CidSelfBuffer


# per_subject CSV に追加する v915_* 列の順序 (固定)
# 段階 2: 13 列 (fetch/mismatch 3 点セット + event 別カウント)
# 段階 3: +7 列 (age_factor / 観察統計) → 合計 20 列
# 接頭辞は v915_* で統一 (機構の連続性を優先、Claude 推奨)
V915_SUBJECT_COLUMNS = (
    # 段階 2 継承
    "v915_fetch_count",
    "v915_last_fetch_step",
    "v915_divergence_norm_final",
    "v915_n_divergence_log",
    "v915_any_mismatch_ever",
    "v915_mismatch_count_total",
    "v915_last_mismatch_step",
    "v915_fetch_count_e1",
    "v915_fetch_count_e2",
    "v915_fetch_count_e3",
    "v915_mismatch_count_e1",
    "v915_mismatch_count_e2",
    "v915_mismatch_count_e3",
    # 段階 3 新規
    "v915_avg_age_factor",
    "v915_min_age_factor",
    "v915_total_observed_count",
    "v915_total_missing_count",
    "v915_total_match_obs_count",
    "v915_total_mismatch_obs_count",
    "v915_final_missing_fraction",
)

# per_cid_self CSV の列 (固定順、段階 3 で age_factor / 観察統計追加)
V915_PER_CID_SELF_COLUMNS = (
    "seed",
    "cid_id",
    "member_nodes_repr",
    "n_core",
    "birth_step",
    "Q0",
    "fetch_count",
    "theta_birth_repr",
    "theta_current_repr",
    "divergence_norm_final",
    "divergence_norm_max",
    "divergence_norm_mean",
    "any_mismatch_ever",
    "mismatch_count_total",
    "last_mismatch_step",
    "fetch_count_e1",
    "fetch_count_e2",
    "fetch_count_e3",
    "mismatch_count_e1",
    "mismatch_count_e2",
    "mismatch_count_e3",
    # 段階 3 新規
    "age_factor_final",
    "avg_age_factor",
    "total_observed_count",
    "total_missing_count",
    "total_match_obs_count",
    "total_mismatch_obs_count",
    "final_missing_fraction",
)

# observation_log CSV の列 (段階 3 新規、§7.4)
V916_OBSERVATION_LOG_COLUMNS = (
    "seed",
    "cid_id",
    "step",
    "event_type_coarse",
    "age_factor",
    "n_core",
    "n_observed",
    "observed_indices",
    "match_count",
    "mismatch_count",
    "missing_count",
)


def _array_repr(arr: np.ndarray, decimals: int = 6) -> str:
    """ndarray を人間可読な文字列に (再解析は想定しない)。"""
    if arr is None or len(arr) == 0:
        return ""
    return "[" + ",".join(f"{float(x):.{decimals}f}" for x in arr) + "]"


def _member_nodes_repr(member_nodes) -> str:
    """frozenset of ints を sorted tuple 文字列に。"""
    return "[" + ",".join(str(n) for n in sorted(member_nodes)) + "]"


def _unformed_or(value, formatter=None):
    """None のとき "unformed"、それ以外は formatter を通した値を返す。"""
    if value is None:
        return "unformed"
    if formatter is None:
        return value
    return formatter(value)


def build_v915_subject_columns(registry: dict, cid) -> dict:
    """
    per_subject CSV 末尾に追加する v915_* 列を返す (段階 3、20 列)。
    v9.14 既存列は一切触らない (呼び出し側で **展開して末尾追加する想定)。

    registry に cid が無い場合は "unformed" / 0 で埋める。
    """
    buf = registry.get(cid) if registry else None
    if buf is None:
        return {
            # 段階 2 継承
            "v915_fetch_count": 0,
            "v915_last_fetch_step": "unformed",
            "v915_divergence_norm_final": "unformed",
            "v915_n_divergence_log": 0,
            "v915_any_mismatch_ever": False,
            "v915_mismatch_count_total": 0,
            "v915_last_mismatch_step": "unformed",
            "v915_fetch_count_e1": 0,
            "v915_fetch_count_e2": 0,
            "v915_fetch_count_e3": 0,
            "v915_mismatch_count_e1": 0,
            "v915_mismatch_count_e2": 0,
            "v915_mismatch_count_e3": 0,
            # 段階 3 新規
            "v915_avg_age_factor": "unformed",
            "v915_min_age_factor": "unformed",
            "v915_total_observed_count": 0,
            "v915_total_missing_count": 0,
            "v915_total_match_obs_count": 0,
            "v915_total_mismatch_obs_count": 0,
            "v915_final_missing_fraction": "unformed",
        }

    summary = buf._a_observer_get_summary()
    div_log = buf._a_observer_get_divergence_log()

    def _round_or_unformed(v, dec=6):
        if v is None:
            return "unformed"
        return round(float(v), dec)

    return {
        # 段階 2 継承
        "v915_fetch_count": summary["fetch_count"],
        "v915_last_fetch_step": _unformed_or(summary["last_fetch_step"]),
        "v915_divergence_norm_final": _round_or_unformed(
            summary["divergence_norm_final"]),
        "v915_n_divergence_log": len(div_log),
        "v915_any_mismatch_ever": bool(summary["any_mismatch_ever"]),
        "v915_mismatch_count_total": int(summary["mismatch_count_total"]),
        "v915_last_mismatch_step": _unformed_or(summary["last_mismatch_step"]),
        "v915_fetch_count_e1": int(summary["fetch_count_e1"]),
        "v915_fetch_count_e2": int(summary["fetch_count_e2"]),
        "v915_fetch_count_e3": int(summary["fetch_count_e3"]),
        "v915_mismatch_count_e1": int(summary["mismatch_count_e1"]),
        "v915_mismatch_count_e2": int(summary["mismatch_count_e2"]),
        "v915_mismatch_count_e3": int(summary["mismatch_count_e3"]),
        # 段階 3 新規
        "v915_avg_age_factor": _round_or_unformed(summary["avg_age_factor"]),
        "v915_min_age_factor": _round_or_unformed(summary["min_age_factor"]),
        "v915_total_observed_count": int(summary["total_observed_count"]),
        "v915_total_missing_count": int(summary["total_missing_count"]),
        "v915_total_match_obs_count": int(summary["total_match_obs_count"]),
        "v915_total_mismatch_obs_count": int(summary["total_mismatch_obs_count"]),
        "v915_final_missing_fraction": _round_or_unformed(
            summary["final_missing_fraction"]),
    }


def write_per_cid_self_csv(
    registry: dict,
    seed: int,
    out_path: Path,
) -> int:
    """
    cid ごとの自己像最終状態を CSV 出力 (1 cid = 1 行、段階 3)。
    registry に登録された全 cid が対象 (fetch_count=0 の cid も含む)。
    """
    rows: list = []
    for cid in sorted(registry.keys()):
        buf = registry[cid]
        if not isinstance(buf, CidSelfBuffer):
            continue

        summary = buf._a_observer_get_summary()
        div_log = buf._a_observer_get_divergence_log()
        snap = buf._a_observer_get_current_snapshot()

        # divergence 集計 (A 側で計算、B は mean/max を持たない)
        # 段階 3: 全ノード版 theta_diff_norm_all を使う (段階 2 の theta_diff_norm
        # と同じ計算)。段階 1/2 互換のため theta_diff_norm にも fallback。
        if div_log:
            diffs = [
                float(d.get("theta_diff_norm_all", d.get("theta_diff_norm", 0.0)))
                for d in div_log
            ]
            div_max = float(np.max(diffs))
            div_mean = float(np.mean(diffs))
        else:
            div_max = None
            div_mean = None

        def _r(v, dec=6):
            return "unformed" if v is None else round(float(v), dec)

        rows.append({
            "seed": seed,
            "cid_id": buf.cid_id,
            "member_nodes_repr": _member_nodes_repr(buf.member_nodes),
            "n_core": buf.n_core,
            "birth_step": buf.birth_step,
            "Q0": int(summary["Q0"]),
            "fetch_count": buf.fetch_count,
            "theta_birth_repr": _array_repr(snap["theta_birth"]),
            "theta_current_repr": _array_repr(snap["theta"]),
            "divergence_norm_final": _r(summary["divergence_norm_final"]),
            "divergence_norm_max": _r(div_max),
            "divergence_norm_mean": _r(div_mean),
            "any_mismatch_ever": bool(summary["any_mismatch_ever"]),
            "mismatch_count_total": int(summary["mismatch_count_total"]),
            "last_mismatch_step": _unformed_or(summary["last_mismatch_step"]),
            "fetch_count_e1": int(summary["fetch_count_e1"]),
            "fetch_count_e2": int(summary["fetch_count_e2"]),
            "fetch_count_e3": int(summary["fetch_count_e3"]),
            "mismatch_count_e1": int(summary["mismatch_count_e1"]),
            "mismatch_count_e2": int(summary["mismatch_count_e2"]),
            "mismatch_count_e3": int(summary["mismatch_count_e3"]),
            # 段階 3 新規
            "age_factor_final": _r(summary["age_factor_final"]),
            "avg_age_factor": _r(summary["avg_age_factor"]),
            "total_observed_count": int(summary["total_observed_count"]),
            "total_missing_count": int(summary["total_missing_count"]),
            "total_match_obs_count": int(summary["total_match_obs_count"]),
            "total_mismatch_obs_count": int(summary["total_mismatch_obs_count"]),
            "final_missing_fraction": _r(summary["final_missing_fraction"]),
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(V915_PER_CID_SELF_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def write_observation_log_csv(
    registry: dict,
    seed: int,
    out_path: Path,
) -> int:
    """
    段階 3 新規: 各 event 発火時のサンプリング結果を event 単位で出力。
    (cid × event 数) 行。cid_id 昇順、cid 内は step 昇順 (match_history 順)。

    列: seed, cid_id, step, event_type_coarse, age_factor, n_core,
        n_observed, observed_indices, match_count, mismatch_count, missing_count
    """
    rows: list = []
    for cid in sorted(registry.keys()):
        buf = registry[cid]
        if not isinstance(buf, CidSelfBuffer):
            continue
        history = buf._a_observer_get_match_history()
        n_core = buf.n_core
        for h in history:
            # 段階 2 フォーマットの残留 (read_own_state 由来) はスキップ
            if "node_status" not in h:
                continue
            ns = h["node_status"]
            match_c = sum(1 for v in ns.values() if v == "match")
            mismatch_c = sum(1 for v in ns.values() if v == "mismatch")
            missing_c = sum(1 for v in ns.values() if v == "missing")
            observed_indices = h.get("observed_indices", [])
            rows.append({
                "seed": seed,
                "cid_id": int(buf.cid_id),
                "step": int(h["step"]),
                "event_type_coarse": h.get("event_type_coarse", ""),
                "age_factor": round(float(h.get("age_factor", 0.0)), 6),
                "n_core": n_core,
                "n_observed": int(h.get("n_observed", 0)),
                "observed_indices":
                    "[" + ",".join(str(i) for i in observed_indices) + "]",
                "match_count": match_c,
                "mismatch_count": mismatch_c,
                "missing_count": missing_c,
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(V916_OBSERVATION_LOG_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
