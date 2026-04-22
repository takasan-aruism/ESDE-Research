"""
v9.17 段階 4: Interaction Log (接触体候補の外部記録器) [A]
==========================================================

位置づけ (指示書 §3):
  - A 側 (研究者観察)、Layer ではない、外部記録器
  - CID はこのクラスを参照しない・書き込まない
  - 状態なし、機能なし (記録のみ)
  - Describe 徹底: 接触体の成立/持続/消滅の定義を与えない

規約 (A/B 分離):
  - 本ファイルは [A]。B 側 (CidSelfBuffer / fetch_operations) から import 禁止
  - CID object の直接参照を保持しない (指示書 §1.2 禁止 #33):
    record_contact は CidView (値スナップショット) を受け取り、
    scalar のみを dict に格納する

spec 上は引数を "cid object" としていたが、v9.14/v9.15/v9.16 実装では cid は int。
相談役 Taka 回答 (2026-04-22) により CidView (v917_cid_view.py) を介して橋渡しする
方針で合意。本ファイルでは CidView を受け取り、scalar 値のみ records に格納する。
"""

from __future__ import annotations

from typing import Any, List


class InteractionLog:
    """
    E3_contact 由来の接触体候補を記録する外部器。

    重要 (指示書 §3.1):
      - CID はこのクラスを参照しない・書き込まない
      - A 側 (研究者観察) が E3_contact を検知して書き込む
      - 状態を持たない (Describe 徹底)
      - 機能を持たない (記録のみ)
      - 接触体の成立/持続/消滅の定義を与えない (v9.17 では観察のみ)

    dedup (指示書 Q3 / Taka 回答 2026-04-22):
      Layer B は E3_contact pair ごとに 2 event を発行 (各 cid 視点)。
      record_contact を pair ごと 1 回にするため、canonical ordering
      (observer_cid < contacted_cid) の event のみ呼び出す。この dedup は
      main loop 側で実施する。InteractionLog 自体は dedup ロジックを持たない。
    """

    def __init__(self) -> None:
        self.records: List[dict] = []

    def record_contact(
        self,
        step: int,
        cid_a: Any,
        cid_b: Any,
        event_id: int,
    ) -> None:
        """
        E3_contact 発火時に呼ばれる。外部から受け取った CidView から
        scalar を抽出して記録するだけ。

        Parameters
        ----------
        step : int — cumulative_step (v913_global_step)
        cid_a : CidView — pair の一方 (canonical: 小さい cid_id)
        cid_b : CidView — pair の他方 (canonical: 大きい cid_id)
        event_id : int — seed 内 0-based event index (Taka Q2 回答)

        CidView は値スナップショット (frozen dataclass) なので、
        record_contact 後に呼び出し側で CidView を捨てても records に保存
        されるのは scalar のみ。CID object (live state) への参照は残らない。
        """
        composition = frozenset({cid_a.cid_id, cid_b.cid_id})

        a_age_factor = cid_a.age_factor  # CidView.age_factor property
        b_age_factor = cid_b.age_factor

        self.records.append({
            "step": int(step),
            "composition": composition,
            "cid_a_id": int(cid_a.cid_id),
            "cid_b_id": int(cid_b.cid_id),
            "cid_a_age_factor": float(a_age_factor),
            "cid_b_age_factor": float(b_age_factor),
            "cid_a_Q0": int(cid_a.Q0),
            "cid_b_Q0": int(cid_b.Q0),
            "cid_a_n_core": int(cid_a.n_core),
            "cid_b_n_core": int(cid_b.n_core),
            "event_id": int(event_id),
        })

    def get_records(self) -> List[dict]:
        """A 側の研究者ツール向け read-only アクセス (浅い copy)。"""
        return list(self.records)

    def get_record_count(self) -> int:
        return len(self.records)
