"""
v9.15 段階 2 Layer C — A-side Observer [A]
==========================================

研究者向け観察レイヤ。CidSelfBuffer を read-only でのみ参照し、
per_subject CSV への v915_* 列追加、per_cid_self CSV 出力等を行う。

規約 (A/B 分離):
  - 本ファイルは [A]。v915s2_cid_self_buffer を read-only でのみ参照
  - 参照は `_a_observer_*` 接頭辞メソッド経由のみ
  - CidSelfBuffer の内部フィールドへの直接書き込み禁止
  - 断定表現 (「自己」「意識」等) をレポート/コードで使わない
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from v915s2_cid_self_buffer import CidSelfBuffer


# per_subject CSV に追加する v915_* 列の順序 (固定、13 列)
# 段階 1 の node_match_ratio_mean / link_match_ratio_mean は削除、
# 段階 2 の 3 点セット + event 別カウント 9 列を追加。
V915_SUBJECT_COLUMNS = (
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
)

# per_cid_self CSV の列 (固定順、段階 2)
V915_PER_CID_SELF_COLUMNS = (
    "seed",
    "cid_id",
    "member_nodes_repr",
    "n_core",
    "birth_step",
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
    per_subject CSV 末尾に追加する v915_* 13 列を返す (段階 2)。
    v9.14 既存列は一切触らない (呼び出し側で **展開して末尾追加する想定)。

    registry に cid が無い場合は "unformed" / 0 で埋める。
    """
    buf = registry.get(cid) if registry else None
    if buf is None:
        return {
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
        }

    summary = buf._a_observer_get_summary()
    div_log = buf._a_observer_get_divergence_log()

    def _round_or_unformed(v, dec=6):
        if v is None:
            return "unformed"
        return round(float(v), dec)

    return {
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
    }


def write_per_cid_self_csv(
    registry: dict,
    seed: int,
    out_path: Path,
) -> int:
    """
    cid ごとの自己像最終状態を CSV 出力 (1 cid = 1 行、段階 2)。
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
        if div_log:
            diffs = [float(d["theta_diff_norm"]) for d in div_log]
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
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(V915_PER_CID_SELF_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
