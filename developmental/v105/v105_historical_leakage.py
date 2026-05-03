"""ESDE v10.5 — Historical Resource Leakage (recorded β からの漏れ)

設計資料 v105_integrated_design.md §5 + Code A 質問回答 C1-C3:
  - 発火イベント: 双方向 E3 fired + ingestion の 2 系統 (回答 C1)
  - 漏れ量 ε: 固定値 1 (回答 C2)
  - 複数 recorded β: 最強結合 1 個から漏れ (回答 C3)

実装方針:
  - 構造的副作用 (能動的選択ではない)
  - shadow_audit モードでは log のみ、実 C 転記なし (回答 D1)
  - leakage_rng は確率的に発火させる場合のみ使用 (現状は確率なし、
    全 fire でε=1 漏れ)

機構動作 (本番時):
  双方向 E3 fired (cid_x, cid_y):
    cid_y が過去に所属した recorded β を取得 (最強結合 1 個)
    その β.C_inherited から ε=1 を cid_x.C へ転記
    (双方向: cid_x 視点の β からは cid_y へも転記)

  ingestion (observer X が ghost Y を摂食):
    Y が過去に所属した recorded β を取得 (最強結合 1 個)
    その β.C_inherited から ε=1 を X.C へ転記

漏れ規律:
  - 漏れ先は X (event 主体) のみ
  - Recorded → active 状態遷移はしない (recorded 永続)
  - β.C_inherited が 0 ならスキップ (在庫切れ)
"""
from __future__ import annotations

from typing import Any


# 漏れ量 (固定、回答 C2)
LEAKAGE_AMOUNT = 1


class LeakageTracker:
    """漏れイベントの log 蓄積 + per_subject 集計。"""

    def __init__(self, seed: int):
        self.seed = int(seed)
        self.event_log: list[dict] = []
        self.cid_total_leakage_received: dict[int, int] = {}

    def log_leakage(
        self, *,
        global_step: int,
        recipient_cid: int,
        source_cid: int,
        recorded_beta_id: int,
        leakage_amount: int,
        trigger_event: str,
    ) -> None:
        self.event_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "recipient_cid": int(recipient_cid),
            "source_cid": int(source_cid),
            "recorded_beta_id": int(recorded_beta_id),
            "leakage_amount": int(leakage_amount),
            "trigger_event": trigger_event,
        })
        self.cid_total_leakage_received[recipient_cid] = (
            self.cid_total_leakage_received.get(recipient_cid, 0)
            + int(leakage_amount))


# ════════════════════════════════════════════════════════════════════
# 漏れの実行 (be3 fired / ingestion 時に呼ぶ)
# ════════════════════════════════════════════════════════════════════

def trigger_leakage_be3(
    *,
    cid_a: int,
    cid_b: int,
    beta_manager: Any,
    cog: Any,
    leakage_tracker: LeakageTracker,
    global_step: int,
    shadow_audit: bool,
    enabled: bool,
) -> int:
    """be3 fired 時の漏れ処理 (双方向)。

    cid_a と cid_b の双方について、相手が所属した recorded β から
    自分の C へ ε=1 を転記する。

    Returns:
        漏れた合計量 (0, 1, 2 のいずれか)
    """
    if not enabled or leakage_tracker is None or beta_manager is None:
        return 0
    total_leaked = 0
    for recipient, source in [
        (int(cid_a), int(cid_b)),
        (int(cid_b), int(cid_a)),
    ]:
        bid = beta_manager.get_strongest_recorded_beta_for(source)
        if bid is None:
            continue
        actual = beta_manager.apply_leakage(
            recipient_cid=recipient, recorded_bid=bid,
            amount=LEAKAGE_AMOUNT, cog=cog,
            shadow_audit=shadow_audit,
        )
        if actual > 0:
            leakage_tracker.log_leakage(
                global_step=global_step,
                recipient_cid=recipient,
                source_cid=source,
                recorded_beta_id=bid,
                leakage_amount=actual,
                trigger_event="be3",
            )
            total_leaked += actual
    return total_leaked


def trigger_leakage_ingestion(
    *,
    observer_cid: int,
    ghost_cid: int,
    beta_manager: Any,
    cog: Any,
    leakage_tracker: LeakageTracker,
    global_step: int,
    shadow_audit: bool,
    enabled: bool,
) -> int:
    """ingestion 時の漏れ処理。

    observer X が ghost Y を摂食する時、Y が所属した recorded β から
    X.C へ ε=1 を転記する。

    Returns:
        漏れた量 (0 または 1)
    """
    if not enabled or leakage_tracker is None or beta_manager is None:
        return 0
    bid = beta_manager.get_strongest_recorded_beta_for(int(ghost_cid))
    if bid is None:
        return 0
    actual = beta_manager.apply_leakage(
        recipient_cid=int(observer_cid), recorded_bid=bid,
        amount=LEAKAGE_AMOUNT, cog=cog,
        shadow_audit=shadow_audit,
    )
    if actual > 0:
        leakage_tracker.log_leakage(
            global_step=global_step,
            recipient_cid=int(observer_cid),
            source_cid=int(ghost_cid),
            recorded_beta_id=bid,
            leakage_amount=actual,
            trigger_event="ingestion",
        )
    return actual
