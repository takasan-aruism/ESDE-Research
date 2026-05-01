"""
v9.17 段階 4: CidView — cid の read-only snapshot adapter [B]
===========================================================

spec (v9.17 段階 4 実装指示書) は InteractionLog / read_other_on_e3_contact の
引数に "cid object" を想定しているが、v9.14/v9.15/v9.16 実装では cid は int で、
値は CidSelfBuffer / cog / v914_ledger の 3 箇所に分散している。

本モジュールはそのギャップを吸収する薄いアダプタ:
  - CidView は frozen dataclass (mutation 不可)
  - 生誕時情報 (Q0, n_core, theta_birth, B_Gen, ...) は不変
  - Q_remaining のみ dynamic で、build 時点の snapshot を格納する
  - 相談役 Taka 回答 (2026-04-22) による Q1 解消方針

規約 (A/B 分離):
  - 本ファイルは [B]。dataclass のみで依存なし
  - [A] ファイル (v917_a_observer, v917_divergence_tracker) を import しない
  - cog / v914_ledger は関数引数として受け取るのみ (依存を閉じる)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass(frozen=True)
class CidView:
    """
    1 個の cid に対する read-only snapshot。

    生誕時決定値 (Q0, n_core, birth_step, B_Gen, S_avg_birth, r_core_birth,
    phase_sig_birth, theta_birth) は不変。
    Q_remaining は build 時点の値。以降の変動は反映しない。

    spec §1.2 禁止 #19-20: 他者の動的状態は保持しない。
    Q_remaining は visible_ratio 計算のため唯一許容される dynamic 値 (相手の
    age_factor を算出するのに不可欠)。それ以外は全て不変。
    """
    cid_id: int
    Q_remaining: int
    Q0: int
    n_core: int
    birth_step: int
    B_Gen: float
    S_avg_birth: float
    r_core_birth: float
    phase_sig_birth: float
    theta_birth: np.ndarray = field(repr=False)

    @property
    def age_factor(self) -> float:
        """
        相手の age_factor を派生値として取得するためのプロパティ。
        CidSelfBuffer._compute_age_factor と同じ式 (Q_remaining / Q0)。
        Q0=0 のとき 0.0 を返す。
        """
        if self.Q0 <= 0:
            return 0.0
        return max(0.0, min(1.0, float(self.Q_remaining) / float(self.Q0)))


def build_cid_view(
    cid_id: int,
    self_buffer: Any,
    v914_ledger: Any,
    cog: Any,
) -> Optional[CidView]:
    """
    cid_id と周辺レジストリから read-only な CidView を組み立てる。

    Parameters
    ----------
    cid_id : int
    self_buffer : CidSelfBuffer — Q0, n_core, theta_birth, birth_step の source
    v914_ledger : SpendAuditLedger — v14_q_remaining の source (動的値)
    cog : CognitiveOverlay — v11_b_gen, v11_m_c の source (不変値)

    Returns
    -------
    CidView または None:
      - cid_id が None
      - self_buffer が None (未登録)
      - v914_ledger.ledger に cid_id のエントリがない (未登録)
      これらの場合は None を返す。呼び出し側で guard する想定。
    """
    if cid_id is None or self_buffer is None:
        return None

    ledger_entry = v914_ledger.ledger.get(cid_id)
    if ledger_entry is None:
        return None

    # v11_m_c は v11_record_birth_metrics で記録済みの不変 dict
    # {n_core, s_avg, r_core, phase_sig}
    m_c = cog.v11_m_c.get(cid_id, {})
    s_avg = float(m_c.get("s_avg", 0.0))
    r_core = float(m_c.get("r_core", 0.0))
    phase_sig = float(m_c.get("phase_sig", 0.0))

    # v11_b_gen は inf の可能性あり (unformed label); そのまま渡す
    b_gen_raw = cog.v11_b_gen.get(cid_id, 0.0)
    try:
        b_gen = float(b_gen_raw)
    except (TypeError, ValueError):
        b_gen = 0.0

    # theta_birth は self_buffer の snapshot を共有参照で持つ
    # (frozen dataclass なので外部から差し替え不可、numpy array 自体の内容は
    # CidSelfBuffer が生誕時に copy 済 → 以降変更されない)
    return CidView(
        cid_id=int(cid_id),
        Q_remaining=int(ledger_entry["v14_q_remaining"]),
        Q0=int(self_buffer.Q0),
        n_core=int(self_buffer.n_core),
        birth_step=int(self_buffer.birth_step),
        B_Gen=b_gen,
        S_avg_birth=s_avg,
        r_core_birth=r_core,
        phase_sig_birth=phase_sig,
        theta_birth=self_buffer.theta_birth,
    )
