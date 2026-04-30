"""ESDE v10.3 — ObservationTargetTracker

実装指示書 §4 に基づく動的観察対象追跡。

Stage 1: cid が n_core ≥ 4 ∧ n_consciousness_decisions ≥ 5 を満たした時点で追加
Stage 2: Stage 1 の cid が双方向 E3 を発火した相手 cid を追加
Stage 3: 第三項として現れた cid を追加 (Cat 1a/1b/1c、post-process 段階)

保持戦略: 一度 target に入った cid は ghost 化しても削除しない。
"""
from __future__ import annotations

from typing import Dict, Set, Tuple


# Stage 1 閾値 (Code A 第二次応答 §1.3 推奨)
N_CORE_THRESHOLD = 4
N_CONSCIOUSNESS_THRESHOLD = 5


class ObservationTargetTracker:
    """v10.3 動的観察対象追跡。

    target_ids: 観察対象の cid 集合
    added_at_step: cid -> step (target に入った step)
    added_via: cid -> "stage1" / "stage2" / "stage3"
    """

    def __init__(self) -> None:
        self.target_ids: Set[int] = set()
        self.added_at_step: Dict[int, int] = {}
        self.added_via: Dict[int, str] = {}

    # ----------------------------------------------------------------
    # Stage 1: 主役条件で逐次追加
    # ----------------------------------------------------------------
    def stage1_check(
        self,
        cid: int,
        n_core: int,
        n_consciousness: int,
        current_step: int,
    ) -> bool:
        """主役条件チェック。条件満たせば target に追加 (既登録ならそのまま)。

        Returns:
            target に含まれているか (新規追加 / 既存 / 未追加 のいずれ)
        """
        if cid in self.target_ids:
            return True
        if (n_core is not None
                and n_core >= N_CORE_THRESHOLD
                and n_consciousness >= N_CONSCIOUSNESS_THRESHOLD):
            self._add(cid, current_step, "stage1")
            return True
        return False

    # ----------------------------------------------------------------
    # Stage 2: 主役 cid と双方向 E3 を発火した相手も追加
    # ----------------------------------------------------------------
    def stage2_propagate(
        self,
        cid_a: int,
        cid_b: int,
        current_step: int,
    ) -> Tuple[bool, bool]:
        """両者のうち片方が target なら相手も追加。

        Returns:
            (cid_a が target になった or 既に target,
             cid_b が target になった or 既に target)
        """
        a_in = cid_a in self.target_ids
        b_in = cid_b in self.target_ids
        if a_in and not b_in:
            self._add(cid_b, current_step, "stage2")
            return (True, True)
        if b_in and not a_in:
            self._add(cid_a, current_step, "stage2")
            return (True, True)
        return (a_in, b_in)

    # ----------------------------------------------------------------
    # Stage 3: 第三項として参照された cid を追加 (post-process で呼ぶ)
    # ----------------------------------------------------------------
    def stage3_propagate(
        self,
        cid_c: int,
        current_step: int,
    ) -> None:
        if cid_c not in self.target_ids:
            self._add(cid_c, current_step, "stage3")

    # ----------------------------------------------------------------
    # ヘルパー
    # ----------------------------------------------------------------
    def is_target(self, cid: int) -> bool:
        return cid in self.target_ids

    def either_target(self, cid_a: int, cid_b: int) -> bool:
        """cid_a または cid_b のいずれかが target なら True。"""
        return (cid_a in self.target_ids) or (cid_b in self.target_ids)

    def _add(self, cid: int, current_step: int, via: str) -> None:
        self.target_ids.add(int(cid))
        self.added_at_step[int(cid)] = int(current_step)
        self.added_via[int(cid)] = via

    # ----------------------------------------------------------------
    # 出力 (per_subject 列の埋め込み用)
    # ----------------------------------------------------------------
    def get_metadata(self, cid: int) -> dict:
        """cid の target 情報を返す。target でなければ None で埋める。"""
        if cid in self.target_ids:
            return {
                "in_observation_target": True,
                "entered_target_set_step": self.added_at_step.get(cid),
                "added_via": self.added_via.get(cid),
            }
        return {
            "in_observation_target": False,
            "entered_target_set_step": None,
            "added_via": None,
        }

    def __len__(self) -> int:
        return len(self.target_ids)
