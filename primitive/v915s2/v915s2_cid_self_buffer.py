"""
v9.15 段階 2 Layer C — CID Self-Buffer [B]
==========================================

CID が自分自身のメンバーノード/リンクを読み取るための専用メモリ領域。
研究者観察 (A) から分離された CID 主体 (B) 側モジュール。

段階 2 との差分 (vs 段階 1):
  - Fetch は event 駆動 (Layer B の spend_packet 実行後、E1/E2/E3 トリガ)
  - Match Ratio 集約 (比率) を廃止、any_mismatch / count の 3 点セット + event 別 count
  - read_own_state は段階 1 互換で残置 (メインループから呼ばない)

規約 (A/B 分離):
  - 本ファイルは [B]。他の [B] ファイル (v915s2_fetch_operations) のみ import 可
  - [A] ファイル (v915s2_a_observer, v915s2_divergence_tracker) を import してはいけない
  - A 側への露出は `_a_observer_` 接頭辞メソッドの read-only API のみ

段階 2 禁止:
  - 研究者向け統計量 (mean / std / percentile) を持たない
  - Q_remaining を参照しない
  - 自分の member_nodes 以外を参照しない
  - 補完しない (欠損は np.nan または missing_flag で表現)
  - 他 cid の情報を読まない
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np


class CidSelfBuffer:
    """
    v9.15 段階 2: CID が自分の構造を event 発火時に読むための専用メモリ領域。

    設計原則:
      Y: 構造体の差分のみを知覚 (連続値の統計量を持たない)
      Z: 確率的「見る」操作 (段階 2 では成功確率 1、段階 3 以降で導入予定)
      ζ: 補完しない (欠損は np.nan / missing_flag で表現)

    禁止:
      - mean, std 等の A 向け集約量を持たない
      - Q_remaining を参照しない
      - 他 cid の情報を読まない
    """

    # 一致判定の許容誤差
    NODE_MATCH_TOLERANCE = 1e-6
    LINK_MATCH_TOLERANCE = 1e-6

    # event 種別 (coarse、3 種別)
    COARSE_EVENT_TYPES = ("E1", "E2", "E3")

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

        # 欠損フラグ (段階 3 以降で意味を持つ、段階 2 では常に False)
        self.missing_flags = np.zeros(self.n_core, dtype=bool)

        # 一致/不一致履歴 (段階 2 フォーマット)
        self.match_history: list[dict] = []

        # Self-Divergence 追跡 (A 向け観測用、B は使わない)
        self.divergence_log: list[dict] = []

        # Fetch 統計
        self.fetch_count = 0
        self.last_fetch_step: Optional[int] = None
        self.last_fetch_success = True

        # 段階 2 新規: 不一致の最小観察層 (3 点セット)
        self.any_mismatch_ever: bool = False
        self.mismatch_count_total: int = 0
        self.last_mismatch_step: Optional[int] = None

        # 段階 2 新規: event 種別ごとの fetch / mismatch カウント (E1/E2/E3)
        self.fetch_count_by_event: dict = {k: 0 for k in self.COARSE_EVENT_TYPES}
        self.mismatch_count_by_event: dict = {k: 0 for k in self.COARSE_EVENT_TYPES}

    # ----- B 本体 (CID 主体の Fetch 操作) -----

    def read_on_event(
        self,
        state: Any,
        alive_l: set,
        current_step: int,
        event_type_full: str,
    ) -> bool:
        """
        段階 2: event 発火時に呼ばれる Fetch。
        Layer B の spend_packet 実行後にメインループから呼ばれる
        (spend → fetch の依存順序)。

        Parameters
        ----------
        state : engine.state (read-only)
        alive_l : set of tuple (read-only)
        current_step : int — v913_global_step (tracking 連続 step)
        event_type_full : str — 'E1_death' / 'E1_birth' /
                                 'E2_rise' / 'E2_fall' / 'E3_contact'

        Returns
        -------
        bool : Fetch 成否 (段階 2 では常に True)
        """
        event_type_coarse = self._coarse_event_type(event_type_full)

        # 1. メンバーノード・リンクを Fetch
        new_theta = np.array(
            [state.theta[node] for node in self.sorted_member_list],
            dtype=float,
        )
        new_S: dict = {}
        for link in self._iter_member_links(alive_l):
            new_S[link] = state.S[link]

        # 2. 不一致判定 (離散、生誕時との比較)
        node_matches = self._compare_nodes(new_theta)
        link_matches = self._compare_links(new_S)

        any_mismatch_now = (
            not all(node_matches) or not all(link_matches)
        )

        # 3. 3 点セット更新
        if any_mismatch_now:
            self.any_mismatch_ever = True
            self.mismatch_count_total += 1
            self.last_mismatch_step = current_step

        # 4. event 種別ごとの fetch / mismatch カウント
        self.fetch_count_by_event[event_type_coarse] += 1
        if any_mismatch_now:
            self.mismatch_count_by_event[event_type_coarse] += 1

        # 5. バッファ更新
        self.theta_current = new_theta
        self.S_current = new_S
        self.missing_flags = np.zeros(self.n_core, dtype=bool)

        # 6. match_history 記録 (段階 2 フォーマット)
        self.match_history.append({
            "step": current_step,
            "event_type_full": event_type_full,
            "event_type_coarse": event_type_coarse,
            "any_mismatch": any_mismatch_now,
            "node_matches": list(node_matches),
            "link_matches": list(link_matches),
        })

        self.fetch_count += 1
        self.last_fetch_step = current_step
        self.last_fetch_success = True

        # 7. Divergence log (event_type を含む、A 観測用)
        self._log_divergence_on_event(
            current_step, new_theta, new_S,
            event_type_full, event_type_coarse,
        )

        return True

    def read_own_state(
        self,
        state: Any,
        alive_l: set,
        current_step: int,
    ) -> bool:
        """
        段階 1 互換の 50 step pulse 駆動 Fetch。

        段階 2 ではメインループから呼ばれない。
        将来 (Paired Audit 等) で 50 step 駆動を復活させる可能性のため残置。
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
            "node_matches": list(node_matches),
        })

        self.fetch_count += 1
        self.last_fetch_step = current_step
        self.last_fetch_success = True

        self._log_divergence(current_step, new_theta, new_S)

        return True

    # ----- 内部ヘルパ (B のみが呼ぶ) -----

    def _coarse_event_type(self, event_type_full: str) -> str:
        """event_type_full を 3 種別 (E1/E2/E3) にマップ。"""
        if event_type_full.startswith("E1"):
            return "E1"
        if event_type_full.startswith("E2"):
            return "E2"
        if event_type_full.startswith("E3"):
            return "E3"
        raise ValueError(f"Unknown event_type: {event_type_full}")

    def _iter_member_links(self, alive_l):
        """
        メンバーノード内部に両端が収まっているリンクのみを yield。
        """
        members = self.member_nodes
        for link in alive_l:
            if all(n in members for n in link):
                yield link

    def _compare_nodes(self, new_theta: np.ndarray) -> list:
        """生誕時 theta_birth と現在 new_theta の一致判定 (離散)。"""
        return [
            abs(float(new) - float(birth)) < self.NODE_MATCH_TOLERANCE
            for new, birth in zip(new_theta, self.theta_birth)
        ]

    def _compare_links(self, new_S: dict) -> list:
        """生誕時 S_birth に存在したリンクについて、現在の S との一致判定。"""
        matches: list = []
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
        """段階 1 互換の divergence_log (event_type なし、read_own_state から)。"""
        theta_diff = float(np.linalg.norm(new_theta - self.theta_birth))
        if self.S_birth:
            link_matches = self._compare_links(new_S)
            link_match_ratio = sum(link_matches) / len(self.S_birth)
        else:
            link_match_ratio = 1.0
        self.divergence_log.append({
            "step": current_step,
            "event_type_full": None,
            "event_type_coarse": None,
            "theta_diff_norm": theta_diff,
            "link_match_ratio": link_match_ratio,
        })

    def _log_divergence_on_event(
        self,
        current_step: int,
        new_theta: np.ndarray,
        new_S: dict,
        event_type_full: str,
        event_type_coarse: str,
    ) -> None:
        """段階 2: event 発火時の divergence_log (event_type を含む)。"""
        theta_diff = float(np.linalg.norm(new_theta - self.theta_birth))
        if self.S_birth:
            link_matches = self._compare_links(new_S)
            link_match_ratio = sum(link_matches) / len(self.S_birth)
        else:
            link_match_ratio = 1.0
        self.divergence_log.append({
            "step": current_step,
            "event_type_full": event_type_full,
            "event_type_coarse": event_type_coarse,
            "theta_diff_norm": theta_diff,
            "link_match_ratio": link_match_ratio,
        })

    # ----- A 向け read-only API (必ず `_a_observer_` 接頭辞) -----
    # 返却はすべて深い copy。内部オブジェクトへの参照は渡さない。

    def _a_observer_get_match_history(self) -> list:
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

    def _a_observer_get_divergence_log(self) -> list:
        """A 向け: divergence_log の copy を返す。"""
        return [dict(d) for d in self.divergence_log]

    def _a_observer_get_summary(self) -> dict:
        """
        A 向け: 段階 2 の集計。
        event 別 fetch / mismatch カウントと 3 点セットを返す。
        段階 1 の mean 系は廃止。
        """
        divergence_final = (
            self.divergence_log[-1]["theta_diff_norm"]
            if self.divergence_log else None
        )

        return {
            "fetch_count": self.fetch_count,
            "last_fetch_step": self.last_fetch_step,
            "any_mismatch_ever": self.any_mismatch_ever,
            "mismatch_count_total": self.mismatch_count_total,
            "last_mismatch_step": self.last_mismatch_step,
            "fetch_count_e1": self.fetch_count_by_event["E1"],
            "fetch_count_e2": self.fetch_count_by_event["E2"],
            "fetch_count_e3": self.fetch_count_by_event["E3"],
            "mismatch_count_e1": self.mismatch_count_by_event["E1"],
            "mismatch_count_e2": self.mismatch_count_by_event["E2"],
            "mismatch_count_e3": self.mismatch_count_by_event["E3"],
            "divergence_norm_final": divergence_final,
        }
