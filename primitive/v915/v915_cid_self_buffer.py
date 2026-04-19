"""
v9.15 Layer C — CID Self-Buffer [B]
====================================

CID が自分自身のメンバーノード/リンクを読み取るための専用メモリ領域。
研究者観察 (A) から分離された CID 主体 (B) 側モジュール。

規約 (A/B 分離):
  - 本ファイルは [B]。他の [B] ファイル (v915_fetch_operations) のみ import 可
  - [A] ファイル (v915_a_observer, v915_divergence_tracker) を import してはいけない
  - A 側への露出は `_a_observer_` 接頭辞メソッドの read-only API のみ

段階 1 禁止:
  - 研究者向け統計量 (mean / std / percentile) を持たない
  - Q_remaining を参照しない
  - 自分の member_nodes 以外を参照しない
  - 補完しない (欠損は np.nan または missing_flag で表現)
  - 他 cid の情報を読まない
"""

from __future__ import annotations

from typing import Any

import numpy as np


class CidSelfBuffer:
    """
    v9.15 段階 1: CID が自分の構造を読むための専用メモリ領域。

    設計原則:
      Y: 構造体の差分のみを知覚 (連続値の統計量を持たない)
      Z: 確率的「見る」操作 (段階 1 では成功確率 1、段階 2 で導入)
      ζ: 補完しない (欠損は np.nan / missing_flag で表現)

    禁止:
      - mean, std 等の A 向け集約量を持たない
      - Q_remaining を参照しない
      - 他 cid の情報を読まない
    """

    # 一致判定の許容誤差
    NODE_MATCH_TOLERANCE = 1e-6
    LINK_MATCH_TOLERANCE = 1e-6

    def __init__(
        self,
        cid_id: int,
        member_nodes: frozenset,
        birth_step: int,
        initial_theta: np.ndarray,
        initial_S: dict,
    ):
        # 不変 (生誕時に固定)
        self.cid_id = cid_id
        self.member_nodes = member_nodes
        self.sorted_member_list = sorted(member_nodes)  # 参照順序を固定
        self.birth_step = birth_step
        self.n_core = len(member_nodes)

        # 生誕時スナップショット (不変、深いコピー)
        self.theta_birth = np.asarray(initial_theta, dtype=float).copy()
        self.S_birth = dict(initial_S)

        # 最新 Fetch スナップショット (毎 Fetch で更新)
        self.theta_current = self.theta_birth.copy()
        self.S_current = dict(self.S_birth)

        # 欠損フラグ (段階 2 以降で意味を持つ、段階 1 では常に False)
        self.missing_flags = np.zeros(self.n_core, dtype=bool)

        # 一致/不一致履歴
        self.match_history: list[dict] = []

        # Self-Divergence 追跡 (A 向け観測用、B は使わない)
        self.divergence_log: list[dict] = []

        # Fetch 統計
        self.fetch_count = 0
        self.last_fetch_step: int | None = None
        self.last_fetch_success = True

    # ----- B 本体 (CID 主体の Fetch 操作) -----

    def read_own_state(
        self,
        state: Any,
        alive_l: set,
        current_step: int,
    ) -> bool:
        """
        CID が自分の構成ノードとリンクを B 専用領域へ Fetch する。

        段階 1 では常に成功 (True を返す)。

        重要:
          - state, alive_l は read-only (呼び出し側も B も書き換えない前提)
          - self.member_nodes 以外のノード/リンクは触らない
          - Q_remaining を参照しない
        """
        # 1. メンバーノードの現在 theta を取得 (sorted_member_list の順)
        new_theta = np.array(
            [state.theta[node] for node in self.sorted_member_list],
            dtype=float,
        )

        # 2. メンバー内リンクの現在 S を取得
        new_S: dict = {}
        for link in self._iter_member_links(alive_l):
            new_S[link] = state.S[link]

        # 3. 一致判定 (離散)
        node_matches = self._compare_nodes(new_theta)
        link_matches = self._compare_links(new_S)

        # 4. バッファ更新
        self.theta_current = new_theta
        self.S_current = new_S
        # 段階 1 では欠損なし。段階 2 以降で意味を持つ器
        self.missing_flags = np.zeros(self.n_core, dtype=bool)

        self.match_history.append({
            "step": current_step,
            "node_match_ratio": (
                sum(node_matches) / self.n_core
                if self.n_core > 0 else 1.0
            ),
            "link_match_ratio": (
                sum(link_matches) / len(link_matches)
                if link_matches else 1.0
            ),
            "node_matches": list(node_matches),  # list of bool
        })

        self.fetch_count += 1
        self.last_fetch_step = current_step
        self.last_fetch_success = True

        # 5. Divergence log (A 観測用、B は使わない)
        self._log_divergence(current_step, new_theta, new_S)

        return True

    # ----- 内部ヘルパ (B のみが呼ぶ) -----

    def _iter_member_links(self, alive_l):
        """
        メンバーノード内部に両端が収まっているリンクのみを yield。

        v9.14 engine は alive_l を tuple (i,j) で表現 (i<j)。
        frozenset 表現も対応するよう、両端ノードが member_nodes に
        属しているかを iterable として検査する。
        """
        members = self.member_nodes
        for link in alive_l:
            if all(n in members for n in link):
                yield link

    def _compare_nodes(self, new_theta: np.ndarray) -> list[bool]:
        """
        生誕時 theta_birth と現在 new_theta の一致判定 (離散)。
        tolerance 以下は一致とみなす。
        """
        return [
            abs(float(new) - float(birth)) < self.NODE_MATCH_TOLERANCE
            for new, birth in zip(new_theta, self.theta_birth)
        ]

    def _compare_links(self, new_S: dict) -> list[bool]:
        """
        生誕時 S_birth に存在したリンクについて、現在の S との一致判定。
        リンクが消滅している場合は不一致とする。
        """
        matches: list[bool] = []
        for link, birth_s in self.S_birth.items():
            current_s = new_S.get(link, None)
            if current_s is None:
                matches.append(False)
            else:
                matches.append(
                    abs(float(current_s) - float(birth_s))
                    < self.LINK_MATCH_TOLERANCE
                )
        return matches

    def _log_divergence(
        self,
        current_step: int,
        new_theta: np.ndarray,
        new_S: dict,
    ) -> None:
        """
        Self-Divergence 追跡用。theta_birth からの L2 距離と、
        S_birth リンクのうち一致している割合を記録。
        A 向け観測用 (B 本体は使わない)。
        """
        theta_diff = float(np.linalg.norm(new_theta - self.theta_birth))

        if self.S_birth:
            link_matches = self._compare_links(new_S)
            link_match_ratio = sum(link_matches) / len(self.S_birth)
        else:
            link_match_ratio = 1.0

        self.divergence_log.append({
            "step": current_step,
            "theta_diff_norm": theta_diff,
            "link_match_ratio": link_match_ratio,
        })

    # ----- A 向け read-only API (必ず `_a_observer_` 接頭辞) -----
    # 返却はすべて深い copy。内部オブジェクトへの参照は渡さない。

    def _a_observer_get_match_history(self) -> list[dict]:
        """A 向け: match_history の copy を返す。"""
        return [dict(h) for h in self.match_history]

    def _a_observer_get_current_snapshot(self) -> dict:
        """A 向け: 現在の self-snapshot を dict copy で返す。"""
        return {
            "theta": self.theta_current.copy(),
            "S": dict(self.S_current),
            "missing_flags": self.missing_flags.copy(),
            "theta_birth": self.theta_birth.copy(),
        }

    def _a_observer_get_divergence_log(self) -> list[dict]:
        """A 向け: divergence_log の copy を返す。"""
        return [dict(d) for d in self.divergence_log]

    def _a_observer_get_summary(self) -> dict:
        """
        A 向け: 段階 1 向けの基本集計。
        B 本体は mean 等を持たないので、A 側で要求される時に計算する。
        """
        if not self.match_history:
            return {
                "fetch_count": 0,
                "node_match_ratio_mean": None,
                "link_match_ratio_mean": None,
                "divergence_norm_final": None,
                "last_fetch_step": None,
            }

        node_ratios = [h["node_match_ratio"] for h in self.match_history]
        link_ratios = [h["link_match_ratio"] for h in self.match_history]

        divergence_final = (
            self.divergence_log[-1]["theta_diff_norm"]
            if self.divergence_log else None
        )

        return {
            "fetch_count": self.fetch_count,
            "node_match_ratio_mean": float(np.mean(node_ratios)),
            "link_match_ratio_mean": float(np.mean(link_ratios)),
            "divergence_norm_final": divergence_final,
            "last_fetch_step": self.last_fetch_step,
        }
