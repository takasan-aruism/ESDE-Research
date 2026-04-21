"""
v9.16 段階 3 Layer C — CID Self-Buffer [B]
==========================================

CID が自分自身のメンバーノード/リンクを読み取るための専用メモリ領域。
研究者観察 (A) から分離された CID 主体 (B) 側モジュール。

段階 3 との差分 (vs 段階 2):
  - Q0 を cid birth 時に確定値として保持
  - age_factor = Q_remaining / Q0 に比例するノードのみ観察 (サンプリング)
  - 未観察ノードは missing として 3 値化 (match / mismatch / missing)
  - engine.rng を touch せず hash ベースの決定論的 RNG を独自構築
  - divergence を全ノードと観察ノード両方で記録

段階 2 との共通:
  - Fetch は event 駆動 (Layer B の spend_packet 実行後、E1/E2/E3 トリガ)
  - read_own_state は段階 1 互換で残置 (メインループから呼ばない)

規約 (A/B 分離):
  - 本ファイルは [B]。他の [B] ファイル (v916_fetch_operations) のみ import 可
  - [A] ファイル (v916_a_observer, v916_divergence_tracker) を import してはいけない
  - A 側への露出は `_a_observer_` 接頭辞メソッドの read-only API のみ

段階 3 禁止:
  - 研究者向け統計量 (mean / std / percentile) を持たない
  - 自分の member_nodes 以外を参照しない
  - 補完しない (欠損は missing のまま)
  - 他 cid の情報を読まない
  - engine.rng を touch しない
"""

from __future__ import annotations

import random
from typing import Any, Optional

import numpy as np


# event_type_full → int マップ (PYTHONHASHSEED 非依存、§4.3 安全版)
_EVENT_TYPE_HASH = {
    "E1_death":   1001,
    "E1_birth":   1002,
    "E2_rise":    2001,
    "E2_fall":    2002,
    "E3_contact": 3001,
}


class CidSelfBuffer:
    """
    v9.16 段階 3: CID が自分の構造を event 発火時に読むための専用メモリ領域。
    age_factor = Q_remaining / Q0 に比例した数のメンバーノードのみを判定対象とする。

    設計原則:
      Y: 構造体の差分のみを知覚 (連続値の統計量を持たない)
      Z: age_factor 依存の確率的「見る」操作 (Q 消耗に応じて観察粒度が粗くなる)
      ζ: 補完しない (欠損は missing のまま)

    禁止:
      - mean, std 等の A 向け集約量を持たない
      - 他 cid の情報を読まない
      - engine.rng を touch しない
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
        Q0: int,
    ):
        # 不変 (生誕時に固定)
        self.cid_id = cid_id
        self.member_nodes = member_nodes
        self.sorted_member_list = sorted(member_nodes)  # 参照順序を固定
        self.birth_step = birth_step
        self.n_core = len(member_nodes)

        # 段階 3 新規: 生誕時 Q0 (= floor(B_Gen))、動的再計算しない
        # b_gen=inf / <=0 の cid は Q0=0 として扱う (age_factor 常に 0)
        self.Q0: int = int(Q0) if Q0 is not None else 0
        if self.Q0 < 0:
            self.Q0 = 0

        # 生誕時スナップショット (不変、深いコピー)
        self.theta_birth = np.asarray(initial_theta, dtype=float).copy()
        self.S_birth = dict(initial_S)

        # 最新 Fetch スナップショット (毎 Fetch で更新)
        self.theta_current = self.theta_birth.copy()
        self.S_current = dict(self.S_birth)

        # 欠損フラグ (段階 1 から器として存在、段階 3 で初めて意味を持つ)
        # cumulative: 一度 missing になったら True を保持
        self.missing_flags = np.zeros(self.n_core, dtype=bool)

        # 一致/不一致履歴 (段階 3 フォーマット)
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

        # 段階 3 新規: age_factor 履歴 (A 向け観測用)
        self.age_factor_history: list[dict] = []

        # 段階 3 新規: サンプリング統計
        self.total_observed_count: int = 0      # 観察されたノード数の累計
        self.total_missing_count: int = 0       # 欠損だったノード数の累計
        self.total_match_obs_count: int = 0     # 観察されて match だった回数
        self.total_mismatch_obs_count: int = 0  # 観察されて mismatch だった回数

    # ----- B 本体 (CID 主体の Fetch 操作) -----

    def read_on_event(
        self,
        state: Any,
        alive_l: set,
        current_step: int,
        event_type_full: str,
        Q_remaining: int,
        seed: int,
    ) -> bool:
        """
        段階 3: event 発火時に呼ばれる age_factor サンプリング付き Fetch。
        Layer B の spend_packet 実行後にメインループから呼ばれる
        (spend → fetch の依存順序)。

        Parameters
        ----------
        state : engine.state (read-only)
        alive_l : set of tuple (read-only)
        current_step : int — v913_global_step (tracking 連続 step)
        event_type_full : str — 'E1_death' / 'E1_birth' /
                                 'E2_rise' / 'E2_fall' / 'E3_contact'
        Q_remaining : int — spend_packet 後の残存 Q (Layer B の ledger 値を
                            読むだけで書き換えない)
        seed : int — run の seed。local RNG 構築のみに使用、engine.rng は
                     touch しない

        Returns
        -------
        bool : Fetch 成否 (段階 3 でも常に True)
        """
        event_type_coarse = self._coarse_event_type(event_type_full)

        # 1. age_factor と n_observed の計算
        age_factor = self._compute_age_factor(Q_remaining)
        n_observed = self._compute_n_observed(age_factor)

        # 2. サンプリング (hash ベース独自 RNG、engine.rng は touch しない)
        local_rng = self._build_local_rng(seed, current_step, event_type_full)
        observed_indices = self._sample_observed_indices(n_observed, local_rng)
        observed_set = set(observed_indices)

        # 3. メンバーノード・リンクを全 Fetch (物理アクセスは全体、判定のみ選択)
        new_theta = np.array(
            [state.theta[node] for node in self.sorted_member_list],
            dtype=float,
        )
        new_S: dict = {}
        for link in self._iter_member_links(alive_l):
            new_S[link] = state.S[link]

        # 4. 観察ノードのみ判定、それ以外は missing (3 値化)
        node_status: dict = {}
        obs_match_count = 0
        obs_mismatch_count = 0
        for i in range(self.n_core):
            if i in observed_set:
                birth_theta_i = self.theta_birth[i]
                current_theta_i = new_theta[i]
                is_match = (
                    abs(float(current_theta_i) - float(birth_theta_i))
                    < self.NODE_MATCH_TOLERANCE
                )
                if is_match:
                    node_status[i] = "match"
                    obs_match_count += 1
                else:
                    node_status[i] = "mismatch"
                    obs_mismatch_count += 1
            else:
                node_status[i] = "missing"
                # missing_flags は cumulative: 一度 missing になったら True を保持
                self.missing_flags[i] = True

        # 5. any_mismatch 判定 (段階 3 禁止 §1.2 #24):
        #    観察ノード (obs) の mismatch のみで決定。
        #    - missing ノードは判定不能として除外 (指示書 §1.3 #22)
        #    - リンクは any_mismatch に不寄与 (段階 2 との意味変更)。
        #      リンクの状況は divergence_log.link_match_ratio に残すのみ。
        #    n_observed=0 のとき obs_mismatch_count=0 → any_mismatch_now=False
        any_mismatch_now = obs_mismatch_count > 0

        # 6. 3 点セット更新 (段階 2 から継承、リンクは不寄与に変更)
        if any_mismatch_now:
            self.any_mismatch_ever = True
            self.mismatch_count_total += 1
            self.last_mismatch_step = current_step

        # 7. event 種別ごとの fetch / mismatch カウント (段階 2 から継承)
        self._ensure_event_counters()
        self.fetch_count_by_event[event_type_coarse] += 1
        if any_mismatch_now:
            self.mismatch_count_by_event[event_type_coarse] += 1

        # 8. 段階 3 新規: サンプリング統計の更新
        self.total_observed_count += len(observed_indices)
        self.total_missing_count += (self.n_core - len(observed_indices))
        self.total_match_obs_count += obs_match_count
        self.total_mismatch_obs_count += obs_mismatch_count

        # 9. バッファ更新 (missing_flags は 4 の時点で更新済、リセットしない)
        self.theta_current = new_theta
        self.S_current = new_S

        # 10. match_history 記録 (段階 3 フォーマット)
        self.match_history.append({
            "step": current_step,
            "event_type_full": event_type_full,
            "event_type_coarse": event_type_coarse,
            "age_factor": age_factor,
            "n_observed": n_observed,
            "observed_indices": list(observed_indices),
            "node_status": dict(node_status),
            "any_mismatch": any_mismatch_now,
        })

        # 11. age_factor_history 記録 (A 向け観測用)
        self.age_factor_history.append({
            "step": current_step,
            "age_factor": age_factor,
        })

        self.fetch_count += 1
        self.last_fetch_step = current_step
        self.last_fetch_success = True

        # 12. Divergence log (全ノード + 観察ノード両方、論点 Z-c)
        self._log_divergence_on_event(
            current_step, new_theta, new_S,
            event_type_full, event_type_coarse,
            age_factor, n_observed, observed_indices,
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

    def _ensure_event_counters(self) -> None:
        """defensive: 旧 pickle 等から復元した場合のための初期化保証。"""
        if not hasattr(self, "fetch_count_by_event") or self.fetch_count_by_event is None:
            self.fetch_count_by_event = {k: 0 for k in self.COARSE_EVENT_TYPES}
        if not hasattr(self, "mismatch_count_by_event") or self.mismatch_count_by_event is None:
            self.mismatch_count_by_event = {k: 0 for k in self.COARSE_EVENT_TYPES}

    # ----- 段階 3: サンプリング基本メソッド -----

    def _compute_age_factor(self, Q_remaining: int) -> float:
        """
        age_factor = Q_remaining / Q0。
        範囲 [0, 1]。Q0 は cid birth 時に確定した値を使う。
        Q0=0 の cid (floor(B_Gen)=0 もしくは B_Gen=inf) は age_factor=0 固定。
        """
        if self.Q0 == 0:
            return 0.0
        # 念のため [0, 1] に clamp (Q_remaining < 0 や > Q0 は理論上起きない)
        return max(0.0, min(1.0, float(Q_remaining) / float(self.Q0)))

    def _compute_n_observed(self, age_factor: float) -> int:
        """
        n_observed = round(n_core * age_factor)。
        最小値 0 (完全失明許可、論点 X-a)、最大値 n_core。
        """
        n = int(round(self.n_core * age_factor))
        return max(0, min(self.n_core, n))

    def _build_local_rng(
        self,
        seed: int,
        current_step: int,
        event_type_full: str,
    ) -> random.Random:
        """
        engine.rng を touch しない独自 RNG。
        hash ベースで決定論的に生成する。PYTHONHASHSEED 非依存のため
        event_type は明示マップ (_EVENT_TYPE_HASH) を使用。
        """
        et_int = _EVENT_TYPE_HASH.get(event_type_full, 0)
        rng_seed_raw = (
            (int(seed) * 100003)
            ^ (int(self.cid_id) * 10007)
            ^ (int(current_step) * 131)
            ^ (et_int * 31)
        )
        rng_seed = abs(rng_seed_raw) % (2**31)
        return random.Random(rng_seed)

    def _sample_observed_indices(
        self,
        n_observed: int,
        local_rng: random.Random,
    ) -> list:
        """
        メンバーノード index [0, n_core) から n_observed 個を決定論的に選ぶ。
        返り値は昇順 (決定論性のため)。
        """
        if n_observed <= 0:
            return []
        if n_observed >= self.n_core:
            return list(range(self.n_core))
        return sorted(local_rng.sample(range(self.n_core), n_observed))

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
        age_factor: float,
        n_observed: int,
        observed_indices: list,
    ) -> None:
        """段階 3: event 発火時の divergence_log。
        全ノード版 (theta_diff_norm_all) と観察ノード版 (theta_diff_norm_observed)
        の両方を記録。段階 2 の theta_diff_norm は theta_diff_norm_all に改名。
        """
        # 全ノードでの L2 distance (段階 2 と比較可能)
        theta_diff_norm_all = float(
            np.linalg.norm(new_theta - self.theta_birth)
        )

        # 観察ノードのみでの L2 distance
        if n_observed > 0:
            obs_idx = np.array(observed_indices, dtype=int)
            theta_diff_norm_observed = float(
                np.linalg.norm(
                    new_theta[obs_idx] - self.theta_birth[obs_idx]
                )
            )
            theta_diff_norm_observed_normalized = (
                theta_diff_norm_observed / n_observed
            )
        else:
            theta_diff_norm_observed = 0.0
            theta_diff_norm_observed_normalized = 0.0

        # link_match_ratio (段階 2 から継続、リンクは any_mismatch には不寄与だが
        # 研究者観察 A 向けに比率のみ残す)
        if self.S_birth:
            link_matches = self._compare_links(new_S)
            link_match_ratio = sum(link_matches) / len(self.S_birth)
        else:
            link_match_ratio = 1.0

        self.divergence_log.append({
            "step": current_step,
            "event_type_full": event_type_full,
            "event_type_coarse": event_type_coarse,
            "age_factor": age_factor,
            "n_observed": n_observed,
            "theta_diff_norm_all": theta_diff_norm_all,
            "theta_diff_norm_observed": theta_diff_norm_observed,
            "theta_diff_norm_observed_normalized":
                theta_diff_norm_observed_normalized,
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
        A 向け: 段階 3 の集計。
        event 別 fetch / mismatch カウント、3 点セット、サンプリング統計を返す。
        段階 1 の mean 系は廃止。段階 3 で Q0 / age_factor 統計を追加。
        """
        # divergence_final は段階 2 互換のため theta_diff_norm_all (段階 2 の
        # theta_diff_norm と同じ計算) を返す。段階 3 独自の observed 版も併記。
        if self.divergence_log:
            last = self.divergence_log[-1]
            divergence_final = last.get(
                "theta_diff_norm_all",
                last.get("theta_diff_norm"),  # 段階 1/2 互換 fallback
            )
            divergence_final_observed = last.get(
                "theta_diff_norm_observed", None
            )
        else:
            divergence_final = None
            divergence_final_observed = None

        # age_factor 統計 (A 向け観測用、B 内では判定に使わない)
        if self.age_factor_history:
            af_values = [e["age_factor"] for e in self.age_factor_history]
            avg_age_factor = float(sum(af_values) / len(af_values))
            min_age_factor = float(min(af_values))
            age_factor_final = float(af_values[-1])
        else:
            avg_age_factor = None
            min_age_factor = None
            age_factor_final = None

        total_possible_obs = self.fetch_count * self.n_core
        if total_possible_obs > 0:
            final_missing_fraction = (
                self.total_missing_count / total_possible_obs
            )
        else:
            final_missing_fraction = 0.0

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
            # 段階 3 新規
            "Q0": self.Q0,
            "avg_age_factor": avg_age_factor,
            "min_age_factor": min_age_factor,
            "age_factor_final": age_factor_final,
            "total_observed_count": self.total_observed_count,
            "total_missing_count": self.total_missing_count,
            "total_match_obs_count": self.total_match_obs_count,
            "total_mismatch_obs_count": self.total_mismatch_obs_count,
            "final_missing_fraction": final_missing_fraction,
            "divergence_norm_observed_final": divergence_final_observed,
        }
