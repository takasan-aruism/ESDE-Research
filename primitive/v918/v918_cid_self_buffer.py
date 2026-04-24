"""
v9.18 段階 5 Layer C — CID Self-Buffer 拡張 [B]
===============================================

v9.17 段階 4 の CidSelfBuffer に以下を追加 (read-only 観察層):

  C   (認知増加の量的基盤)        : v18_cumulative_cognitive_gain
  A-Gemini (V_unified 系 3 指標)   : unity_direction / unity_concentration /
                                      unity_direction_shift / unity_k
  A-GPT    (生誕時分布からの距離) : theta_distance_from_birth /
                                      theta_distance_coverage_ratio

いずれも run 中の分岐条件に使われない (GPT §8.2 固定)。

設計 (Taka 2026-04-23 判断):
  - 生誕時 θ 分布と生誕時 member_nodes は既存フィールドを property で再利用
  - 生誕時 V_unified は __init__ で 1 回計算、以降不変
  - per_step 計算、CSV 出力は window 末と _final のみ
  - ghost 化検出で _finalize_v18_values を呼び、_final 確定

規約 (A/B 分離):
  - 本ファイルは [B]。v917_cid_self_buffer / v918_unity_metrics /
    v918_theta_distance のみ import 可
  - [A] ファイル (v917_a_observer, v918_a_observer) を import しない
  - A 側への露出は `_a_observer_` 接頭辞メソッド または属性 read-only アクセス
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from v917_cid_self_buffer import CidSelfBuffer as _V917CidSelfBuffer
from v918_unity_metrics import compute_v_unified


class CidSelfBuffer(_V917CidSelfBuffer):
    """
    v9.18: v917 CidSelfBuffer を拡張。

    追加フィールド:
      生誕時スナップショット (CID 確立時に __init__ で 1 回設定、以降不変):
        v18_birth_v_unified : complex
        v18_v_unified_concentration_birth : float

      per_step で更新される current 値 (orchestrator が書き込み):
        v18_cumulative_cognitive_gain : int
        v18_unity_direction : Optional[float]
        v18_unity_concentration : Optional[float]
        v18_unity_direction_shift : Optional[float]
        v18_unity_k : int
        v18_theta_distance_from_birth : Optional[float]
        v18_theta_distance_coverage_ratio : float

      ghost 化時または tracking 終了時に確定する _final 値:
        v18_cognitive_gain_final : Optional[int]
        v18_v_unified_concentration_final : Optional[float]
        v18_v_unified_direction_shift_final : Optional[float]
        v18_v_unified_k_final : Optional[int]
        v18_theta_distance_from_birth_final : Optional[float]
        v18_theta_distance_coverage_ratio_final : Optional[float]
        v18_finalized_at_step : Optional[int]
        v18_finalize_reason : Optional[str] — 'ghost' | 'tracking_end'

    Property (既存フィールドの再パッケージ、冗長実体なし):
        v18_birth_theta_by_node : Dict[int, float]
        v18_birth_member_nodes : frozenset[int]
    """

    def __init__(
        self,
        cid_id: int,
        member_nodes,
        birth_step: int,
        initial_theta: np.ndarray,
        initial_S: dict,
        Q0: int,
    ):
        super().__init__(
            cid_id=cid_id,
            member_nodes=member_nodes,
            birth_step=birth_step,
            initial_theta=initial_theta,
            initial_S=initial_S,
            Q0=Q0,
        )

        # ---- v9.18 新規 生誕時スナップショット ----
        # theta_birth は既に __init__ で copy 済の ndarray。
        # V_unified は complex (numpy mean of exp(i theta))。
        birth_v = compute_v_unified(np.asarray(self.theta_birth, dtype=float))
        self.v18_birth_v_unified: complex = birth_v
        self.v18_v_unified_concentration_birth: float = float(abs(birth_v))

        # ---- v9.18 per_step 更新対象 (初期値) ----
        self.v18_cumulative_cognitive_gain: int = 0
        self.v18_unity_direction: Optional[float] = None
        self.v18_unity_concentration: Optional[float] = None
        self.v18_unity_direction_shift: Optional[float] = None
        self.v18_unity_k: int = 0
        self.v18_theta_distance_from_birth: Optional[float] = None
        self.v18_theta_distance_coverage_ratio: float = 0.0

        # ---- v9.18 _final 値 (ghost 化 or tracking_end で確定) ----
        self.v18_cognitive_gain_final: Optional[int] = None
        self.v18_v_unified_concentration_final: Optional[float] = None
        self.v18_v_unified_direction_shift_final: Optional[float] = None
        self.v18_v_unified_k_final: Optional[int] = None
        self.v18_theta_distance_from_birth_final: Optional[float] = None
        self.v18_theta_distance_coverage_ratio_final: Optional[float] = None
        self.v18_finalized_at_step: Optional[int] = None
        self.v18_finalize_reason: Optional[str] = None

    # ---- property: 既存フィールドの再パッケージ (冗長実体なし) ----

    @property
    def v18_birth_theta_by_node(self) -> Dict[int, float]:
        """
        生誕時の θ を node_id -> θ の dict で返す。
        既存の sorted_member_list + theta_birth から派生。
        """
        return {
            self.sorted_member_list[i]: float(self.theta_birth[i])
            for i in range(self.n_core)
        }

    @property
    def v18_birth_member_nodes(self) -> frozenset:
        """生誕時のメンバーノード集合 (既存 member_nodes の alias)。"""
        return self.member_nodes

    # ---- _finalize_v18_values: ghost 化 or tracking_end で呼ばれる ----

    def finalize_v18_values(
        self,
        current_step: int,
        reason: str,
    ) -> bool:
        """
        v18_* の _final 値を確定する (1 回のみ)。

        Parameters
        ----------
        current_step : int — 確定時点の cumulative_step
        reason : str — 'ghost' | 'tracking_end'

        Returns
        -------
        bool : 実際に確定した場合 True、既に確定済みなら False
        """
        if self.v18_finalized_at_step is not None:
            return False

        self.v18_cognitive_gain_final = int(self.v18_cumulative_cognitive_gain)
        self.v18_v_unified_concentration_final = self.v18_unity_concentration
        self.v18_v_unified_direction_shift_final = self.v18_unity_direction_shift
        self.v18_v_unified_k_final = int(self.v18_unity_k)
        self.v18_theta_distance_from_birth_final = self.v18_theta_distance_from_birth
        self.v18_theta_distance_coverage_ratio_final = float(
            self.v18_theta_distance_coverage_ratio
        )
        self.v18_finalized_at_step = int(current_step)
        self.v18_finalize_reason = str(reason)
        return True

    # ---- A 向け read-only API (v918 拡張) ----

    def _a_observer_get_v18_summary(self) -> dict:
        """A 向け: v18_* の要約 (per_subject CSV / 集計用)。"""
        return {
            "v18_birth_v_unified_concentration": self.v18_v_unified_concentration_birth,
            "v18_cognitive_gain_final": self.v18_cognitive_gain_final,
            "v18_v_unified_concentration_final": self.v18_v_unified_concentration_final,
            "v18_v_unified_direction_shift_final": self.v18_v_unified_direction_shift_final,
            "v18_v_unified_k_final": self.v18_v_unified_k_final,
            "v18_theta_distance_from_birth_final": self.v18_theta_distance_from_birth_final,
            "v18_theta_distance_coverage_ratio_final": self.v18_theta_distance_coverage_ratio_final,
            "v18_finalized_at_step": self.v18_finalized_at_step,
            "v18_finalize_reason": self.v18_finalize_reason,
        }
