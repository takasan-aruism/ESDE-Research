"""
v9.15 Layer C — Self-Divergence Tracker [A]
============================================

同クラス (n_core, phase_sig_bucket) に属する cid ペアについて、
最終時点の theta_current 乖離を集計する観測モジュール。

また、全 cid の divergence_log (Fetch ごとの theta_diff_norm / link_match_ratio)
を集約して 1 ファイルに出力する。

規約 (A/B 分離):
  - 本ファイルは [A]。v915s2_cid_self_buffer を read-only でのみ参照
  - 参照は `_a_observer_*` 接頭辞メソッド経由のみ

段階 1 スコープ:
  - ペア数が爆発しないよう、同クラス内で最大 10 ペアを決定論的にサンプリング
  - phase_sig は cog.original_phase_sig から取得 (reaped cid は欠損扱いでスキップ)
"""

from __future__ import annotations

import csv
import itertools
import math
import random
from pathlib import Path

import numpy as np

from v915s2_cid_self_buffer import CidSelfBuffer


# phase_sig を 8 バケットに分類
PHASE_SIG_N_BUCKETS = 8

# クラス内ペア数の上限 (段階 1)
MAX_PAIRS_PER_CLASS = 10

# class_divergence CSV 列 (固定順)
V915_CLASS_DIVERGENCE_COLUMNS = (
    "seed",
    "class_n_core",
    "class_phase_bucket",
    "cid_a",
    "cid_b",
    "divergence_final",
    "n_core_a",
    "n_core_b",
    "fetch_count_a",
    "fetch_count_b",
)

# divergence_log CSV 列 (固定順、段階 2 で event_type を追加)
V915_DIVERGENCE_LOG_COLUMNS = (
    "seed",
    "cid_id",
    "step",
    "event_type_full",
    "event_type_coarse",
    "theta_diff_norm",
    "link_match_ratio",
)


def phase_sig_bucket(phase_sig: float, n_buckets: int = PHASE_SIG_N_BUCKETS) -> int:
    """
    phase_sig を n_buckets バケットに分類。
    phase_sig は 0..2π または -π..π の範囲を想定、正規化して bucket を返す。
    """
    # [-π, π] 正規化 → [0, 2π]
    normalized = phase_sig % (2.0 * math.pi)
    if normalized < 0:
        normalized += 2.0 * math.pi
    idx = int(normalized / (2.0 * math.pi) * n_buckets)
    # 端点保護 (normalized == 2π のまれな case)
    if idx >= n_buckets:
        idx = n_buckets - 1
    return idx


def _deterministic_rng(seed: int, n_core: int, phase_bucket: int) -> random.Random:
    """
    クラスキー (n_core, phase_bucket) と seed から決定論的な RNG を作る。
    Python の hash randomization に依存しないよう、明示的な numeric mix を使う。
    """
    mixed = (int(seed) * 997
             + int(n_core) * 131
             + int(phase_bucket) * 31)
    return random.Random(mixed)


def compute_class_divergence(
    registry: dict,
    phase_sig_map: dict,
    seed: int,
    max_pairs_per_class: int = MAX_PAIRS_PER_CLASS,
) -> list[dict]:
    """
    同クラス cid ペアの最終 theta_current L2 乖離を計算。

    Parameters
    ----------
    registry : dict[cid -> CidSelfBuffer]
    phase_sig_map : dict[cid -> float]
        cog.original_phase_sig のコピー。reaped cid は欠損する想定。
        欠損 cid は本分析から除外 (スキップ)。
    seed : int
        サンプリング RNG に使う (決定論的)
    max_pairs_per_class : int
        クラスあたり最大ペア数 (段階 1 では 10)

    Returns
    -------
    list[dict] : class_divergence CSV 行のリスト
    """
    # 1. cid をクラス (n_core, phase_bucket) で分類
    classes: dict[tuple, list] = {}

    for cid, buf in registry.items():
        if not isinstance(buf, CidSelfBuffer):
            continue
        # Fetch されていない cid は theta_current == theta_birth なので除外
        if buf.fetch_count == 0:
            continue
        # phase_sig 欠損 cid (reaped) は除外
        phase_sig = phase_sig_map.get(cid)
        if phase_sig is None:
            continue

        class_key = (buf.n_core, phase_sig_bucket(float(phase_sig)))
        classes.setdefault(class_key, []).append(cid)

    # 2. 各クラス内でペアサンプリング
    results: list[dict] = []
    for class_key, cid_list in classes.items():
        if len(cid_list) < 2:
            continue

        n_core_cls, phase_bucket_cls = class_key
        all_pairs = list(itertools.combinations(cid_list, 2))
        if len(all_pairs) > max_pairs_per_class:
            rng = _deterministic_rng(seed, n_core_cls, phase_bucket_cls)
            sampled_pairs = rng.sample(all_pairs, max_pairs_per_class)
        else:
            sampled_pairs = all_pairs

        for cid_a, cid_b in sampled_pairs:
            buf_a = registry[cid_a]
            buf_b = registry[cid_b]

            # A 側 read-only API で theta 取得
            snap_a = buf_a._a_observer_get_current_snapshot()
            snap_b = buf_b._a_observer_get_current_snapshot()
            theta_a = snap_a["theta"]
            theta_b = snap_b["theta"]

            # 同じ n_core のクラスなので長さ一致前提だが、防御的に確認
            if len(theta_a) != len(theta_b):
                continue

            div = float(np.linalg.norm(theta_a - theta_b))

            results.append({
                "seed": seed,
                "class_n_core": n_core_cls,
                "class_phase_bucket": phase_bucket_cls,
                "cid_a": int(cid_a),
                "cid_b": int(cid_b),
                "divergence_final": round(div, 6),
                "n_core_a": buf_a.n_core,
                "n_core_b": buf_b.n_core,
                "fetch_count_a": buf_a.fetch_count,
                "fetch_count_b": buf_b.fetch_count,
            })

    return results


def write_class_divergence_csv(
    rows: list[dict],
    out_path: Path,
) -> int:
    """class_divergence CSV を書き出す。rows=0 でも空ファイル (header のみ) を出力。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(V915_CLASS_DIVERGENCE_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_divergence_log_csv(
    registry: dict,
    seed: int,
    out_path: Path,
) -> int:
    """
    registry 全 cid の divergence_log を 1 ファイルに集約。
    cid_id 昇順、cid 内は step 昇順。
    """
    rows: list[dict] = []
    for cid in sorted(registry.keys()):
        buf = registry[cid]
        if not isinstance(buf, CidSelfBuffer):
            continue
        log = buf._a_observer_get_divergence_log()
        for entry in log:
            rows.append({
                "seed": seed,
                "cid_id": int(buf.cid_id),
                "step": int(entry["step"]),
                "event_type_full": (
                    entry.get("event_type_full") or ""),
                "event_type_coarse": (
                    entry.get("event_type_coarse") or ""),
                "theta_diff_norm": round(float(entry["theta_diff_norm"]), 6),
                "link_match_ratio": round(float(entry["link_match_ratio"]), 6),
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(V915_DIVERGENCE_LOG_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
