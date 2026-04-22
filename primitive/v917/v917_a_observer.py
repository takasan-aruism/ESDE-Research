"""
v9.17 段階 4 Layer C — A-side Observer [A]
==========================================

研究者向け観察レイヤ。CidSelfBuffer を read-only でのみ参照し、
per_subject CSV への v915_* / v917_* 列追加、per_cid_self CSV 出力、
observation_log CSV (段階 3) / other_records CSV / interaction_log CSV
(段階 4 新規) 出力等を行う。

規約 (A/B 分離):
  - 本ファイルは [A]。v917_cid_self_buffer を read-only でのみ参照
  - 参照は `_a_observer_*` 接頭辞メソッド経由のみ
  - CidSelfBuffer の内部フィールドへの直接書き込み禁止
  - 断定表現 (「自己」「意識」等) をレポート/コードで使わない
  - 段階 4: InteractionLog も [A] 側。CSV 書き出しは本ファイルから行う
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from v917_cid_self_buffer import CidSelfBuffer


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
V917_OBSERVATION_LOG_COLUMNS = (
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

# 段階 4 新規 (指示書 §6.1): per_subject CSV に追加する v917_* 列 (5 列)
# 接頭辞は v917_* で統一 (段階の識別子、v915_* と共存)
V917_SUBJECT_COLUMNS = (
    "v917_total_other_contacts",
    "v917_total_features_fetched",
    "v917_total_features_missing",
    "v917_avg_visible_ratio",
    "v917_unique_contacts",
)

# 段階 4 新規 (指示書 §6.2): other_records_seed{N}.csv の列
# 各 cid の他者接触ログ、1 row = 1 contact event
V917_OTHER_RECORDS_COLUMNS = (
    "seed",
    "cid_id",
    "step",
    "other_cid_id",
    "event_id",
    "visible_ratio",
    "n_features_fetched",
    "n_features_missing",
    "fetched_M_c_keys",        # | 区切り文字列
    "missing_feature_names",   # | 区切り文字列
)

# 段階 4 新規 (指示書 §6.3): interaction_log_seed{N}.csv の列
# pair ごと 1 row (main loop 側で canonical ordering dedup 済み)
V917_INTERACTION_LOG_COLUMNS = (
    "seed",
    "step",
    "cid_a_id",
    "cid_b_id",
    "composition_str",
    "cid_a_age_factor",
    "cid_b_age_factor",
    "cid_a_Q0",
    "cid_b_Q0",
    "cid_a_n_core",
    "cid_b_n_core",
    "event_id",
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
            f, fieldnames=list(V917_OBSERVATION_LOG_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ========================================================================
# v9.17 段階 4 新規: 他者読み / 接触体候補 出力
# ========================================================================

def build_v917_subject_columns(registry: dict, cid) -> dict:
    """
    per_subject CSV 末尾に追加する v917_* 列を返す (段階 4、5 列)。
    指示書 §6.1 準拠。v9.14 既存列・v915_* 列は一切触らない。

    registry に cid が無い場合は 0 / "unformed" で埋める。

    返り値の列:
      v917_total_other_contacts     生涯の他者接触回数 (int)
      v917_total_features_fetched   取得 features の累計 (int)
      v917_total_features_missing   欠損 features の累計 (int)
      v917_avg_visible_ratio        他者読み時の visible_ratio 平均 (float)
      v917_unique_contacts          一意な接触相手の数 (int)
    """
    buf = registry.get(cid) if registry else None
    if buf is None:
        return {
            "v917_total_other_contacts": 0,
            "v917_total_features_fetched": 0,
            "v917_total_features_missing": 0,
            "v917_avg_visible_ratio": "unformed",
            "v917_unique_contacts": 0,
        }

    total_other_contacts = int(getattr(buf, "total_other_contacts", 0))
    total_features_fetched = int(getattr(buf, "total_features_fetched", 0))
    total_features_missing = int(getattr(buf, "total_features_missing", 0))
    other_records = getattr(buf, "other_records", []) or []

    if total_other_contacts == 0 or not other_records:
        avg_visible_ratio = 0.0
        unique_contacts = 0
    else:
        visible_ratios = [
            float(rec.get("visible_ratio", 0.0)) for rec in other_records
        ]
        avg_visible_ratio = round(
            sum(visible_ratios) / len(visible_ratios), 6
        )
        unique_contacts = len({
            int(rec["other_cid_id"]) for rec in other_records
        })

    return {
        "v917_total_other_contacts": total_other_contacts,
        "v917_total_features_fetched": total_features_fetched,
        "v917_total_features_missing": total_features_missing,
        "v917_avg_visible_ratio": avg_visible_ratio,
        "v917_unique_contacts": unique_contacts,
    }


def write_other_records_csv(
    registry: dict,
    seed: int,
    out_path: Path,
) -> int:
    """
    段階 4 新規 (指示書 §6.2): 各 cid の other_records を 1 row = 1 contact
    event で CSV 出力する。

    出力先: diag_v917_{tag}/selfread/other_records_seed{N}.csv

    列 (V917_OTHER_RECORDS_COLUMNS):
      seed, cid_id, step, other_cid_id, event_id, visible_ratio,
      n_features_fetched, n_features_missing,
      fetched_M_c_keys, missing_feature_names

    fetched_M_c / missing_feature_names の値は | 区切り文字列化。
    値そのもの (fetched_M_c の value) は記録しない (サイズ膨張回避、§6.2)。
    行順: cid_id 昇順、cid 内は step 昇順 (append 順 = step 昇順)。
    """
    rows: list = []
    for cid in sorted(registry.keys()):
        buf = registry[cid]
        if not isinstance(buf, CidSelfBuffer):
            continue
        other_records = getattr(buf, "other_records", []) or []
        for rec in other_records:
            fetched_keys = "|".join(rec.get("fetched_M_c", {}).keys())
            missing_names = "|".join(rec.get("missing_feature_names", []))
            rows.append({
                "seed": int(seed),
                "cid_id": int(buf.cid_id),
                "step": int(rec["step"]),
                "other_cid_id": int(rec["other_cid_id"]),
                "event_id": int(rec["event_id"]),
                "visible_ratio": round(float(rec["visible_ratio"]), 6),
                "n_features_fetched": len(rec.get("fetched_M_c", {})),
                "n_features_missing": len(
                    rec.get("missing_feature_names", [])),
                "fetched_M_c_keys": fetched_keys,
                "missing_feature_names": missing_names,
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(V917_OTHER_RECORDS_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def write_interaction_log_csv(
    interaction_log,
    seed: int,
    out_path: Path,
) -> int:
    """
    段階 4 新規 (指示書 §6.3): InteractionLog.records を CSV 出力する。

    出力先: diag_v917_{tag}/selfread/interaction_log_seed{N}.csv

    行数 = E3_contact pair 数 (Layer B が発火する 2 event/pair に対して
    main loop 側 canonical ordering dedup 済み、pair ごと 1 row)。

    列 (V917_INTERACTION_LOG_COLUMNS):
      seed, step, cid_a_id, cid_b_id, composition_str,
      cid_a_age_factor, cid_b_age_factor,
      cid_a_Q0, cid_b_Q0, cid_a_n_core, cid_b_n_core,
      event_id

    composition_str は frozenset を sort 済文字列化 (例: "{1,7}")。
    """
    rows: list = []
    records = interaction_log.get_records() if interaction_log else []
    for rec in records:
        composition = rec.get("composition", frozenset())
        composition_str = "{" + ",".join(
            str(x) for x in sorted(composition)
        ) + "}"
        rows.append({
            "seed": int(seed),
            "step": int(rec["step"]),
            "cid_a_id": int(rec["cid_a_id"]),
            "cid_b_id": int(rec["cid_b_id"]),
            "composition_str": composition_str,
            "cid_a_age_factor": round(float(rec["cid_a_age_factor"]), 6),
            "cid_b_age_factor": round(float(rec["cid_b_age_factor"]), 6),
            "cid_a_Q0": int(rec["cid_a_Q0"]),
            "cid_b_Q0": int(rec["cid_b_Q0"]),
            "cid_a_n_core": int(rec["cid_a_n_core"]),
            "cid_b_n_core": int(rec["cid_b_n_core"]),
            "event_id": int(rec["event_id"]),
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(V917_INTERACTION_LOG_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
