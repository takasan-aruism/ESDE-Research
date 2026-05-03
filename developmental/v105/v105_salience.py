"""ESDE v10.5 — Salience-driven Focus (mass-weighted observation)

設計資料 v105_integrated_design.md §4 + Code A 質問回答 B1-B3:
  - 適用範囲: 他者読み / be3 fired / ingestion 摂食 (3 系統)
  - 関数形: 線形 P ∝ mass(Y)
  - 質量定義: mass(X) = X.Q + X.C + β.Q_inherited + β.C_inherited (β 1 個分)

実装方針:
  - shadow_audit モードでは Salience を OFF (D1)
  - 既存 RNG (engine.rng / capture_rng / ingestion_rng / balance_rng /
    be3_rng) には touch しない。新規 salience_rng を独立に持つ
  - bit-identity を v10.4 と維持する必要は本機構では崩れる (v10.5 の
    設計上正常: 物理層は frozen、認知/意識層は機構の副作用で異なる)

3 系統の適用:
  1. read_other (CidSelfBuffer.read_other_on_e3_contact):
     visible_ratio に mass-based 加算。重い相手はより多くの features
     が見える (= 解像度が上がる)
  2. be3 fired:
     fire 自体は v10.4 と同じ (物理駆動)。本機構は log 記録のみ
     (発火時の両者 mass を記録、観察に使用)
  3. ingestion target selection:
     uniform random を mass-weighted random に置換
"""
from __future__ import annotations

import math
from typing import Any


# ════════════════════════════════════════════════════════════════════
# 設定パラメータ (調整候補、smoke 後に再決定)
# ════════════════════════════════════════════════════════════════════

# read_other 解像度ブースト係数 (0.0 = 効果なし、1.0 = 最大ブースト)
SALIENCE_READOTHER_STRENGTH = 0.5

# read_other で mass を正規化するベース (この値で 1.0 のブーストになる)
SALIENCE_READOTHER_MASS_NORM = 100.0

# ingestion で mass=0 候補に与える基底重み (uniform fallback 防止)
SALIENCE_INGESTION_BASE_WEIGHT = 1.0

# ingestion で mass の影響度 (0.0 = uniform、1.0 = pure mass-weighted)
# 線形なので 1.0 で P ∝ mass 完全採用
SALIENCE_INGESTION_MASS_COEF = 1.0


# ════════════════════════════════════════════════════════════════════
# Mass calculation
# ════════════════════════════════════════════════════════════════════

def compute_mass(
    *,
    cid: int,
    cog: Any,
    ledger: Any,
    beta_manager: Any = None,
) -> float:
    """mass(X) = X.Q + X.C + β.Q_inherited + β.C_inherited

    cid が hosted でも ghost でも ledger / cog の値があればそれを返す。
    β は 1 個のみ所属 (規律 A2 案 b)、未所属の cid は 0。
    """
    cid = int(cid)
    q = 0
    ledger_entry = ledger.ledger.get(cid) if ledger is not None else None
    if ledger_entry is not None:
        q = int(ledger_entry.get("v14_q_remaining", 0))
    c = int(cog.C.get(cid, 0)) if cog is not None else 0
    base = float(q + c)

    if beta_manager is not None:
        bid = beta_manager.cid_to_beta.get(cid)
        if bid is not None and bid in beta_manager.betas:
            beta = beta_manager.betas[bid]
            base += float(beta.Q_inherited + beta.C_inherited)

    return max(0.0, base)


# ════════════════════════════════════════════════════════════════════
# SalienceTracker (event log + RNG 管理)
# ════════════════════════════════════════════════════════════════════

class SalienceTracker:
    """Salience event の log 蓄積 + 共通 RNG 管理。

    main loop から各サブモジュールに渡し、Salience の発火・選択を記録する。
    """

    def __init__(self, seed: int, salience_rng, *, enabled: bool = True):
        self.seed = int(seed)
        self.salience_rng = salience_rng
        self.enabled = bool(enabled)

        self.event_log: list[dict] = []
        # per_subject 集計
        self.cid_n_observed_as_target: dict[int, int] = {}
        self.cid_n_selected_as_target: dict[int, int] = {}
        self.cid_total_observed_mass: dict[int, float] = {}

    # ----------------------------------------------------------------
    def log_event(
        self, *,
        global_step: int,
        observer_cid: int,
        candidate_cids: list[int],
        candidate_masses: list[float],
        selected_cid: int,
        event_type: str,
    ) -> None:
        """1 件の Salience 適用イベントをログに残す。

        candidate が 1 個 (= 選択肢なし) でも記録する。
        """
        for c, m in zip(candidate_cids, candidate_masses):
            sel = (c == selected_cid)
            self.event_log.append({
                "seed": self.seed,
                "step": int(global_step),
                "observer_cid": int(observer_cid),
                "candidate_cid": int(c),
                "candidate_mass": float(round(m, 4)),
                "selected": bool(sel),
                "event_type": event_type,
            })
            self.cid_n_observed_as_target[c] = (
                self.cid_n_observed_as_target.get(c, 0) + 1)
            self.cid_total_observed_mass[c] = (
                self.cid_total_observed_mass.get(c, 0.0) + float(m))
            if sel:
                self.cid_n_selected_as_target[c] = (
                    self.cid_n_selected_as_target.get(c, 0) + 1)


# ════════════════════════════════════════════════════════════════════
# read_other 拡張 (visible_ratio を mass-based に boost)
# ════════════════════════════════════════════════════════════════════

def adjust_visible_ratio(
    *,
    base_visible_ratio: float,
    other_cid: int,
    cog: Any,
    ledger: Any,
    beta_manager: Any,
    enabled: bool,
) -> float:
    """read_other での visible_ratio を mass-based に調整。

    base_visible_ratio は CidView.age_factor (Q-based)。
    重い cid (大きい mass) は base_visible_ratio に加算ブーストが入る。

    enabled=False (shadow_audit) の場合は base_visible_ratio をそのまま返す。
    """
    if not enabled:
        return float(base_visible_ratio)

    mass = compute_mass(cid=other_cid, cog=cog, ledger=ledger,
                        beta_manager=beta_manager)
    # 線形ブースト: norm 質量で 1.0 全開、それ以上は cap (clamp)
    boost = min(1.0, mass / SALIENCE_READOTHER_MASS_NORM)
    # 効果は (1 - base_visible_ratio) の余地に対する増分として加算
    headroom = max(0.0, 1.0 - float(base_visible_ratio))
    adjusted = float(base_visible_ratio) + (
        SALIENCE_READOTHER_STRENGTH * boost * headroom)
    return max(0.0, min(1.0, adjusted))


# ════════════════════════════════════════════════════════════════════
# ingestion target 選択 (mass-weighted random)
# ════════════════════════════════════════════════════════════════════

def select_ingestion_target(
    *,
    observer_cid: int,
    candidates: list,           # [(ghost_cid, link_id), ...]
    cog: Any,
    ledger: Any,
    beta_manager: Any,
    salience_tracker: SalienceTracker,
    fallback_rng,                # ingestion_rng (shadow_audit 時 / disable 時)
    global_step: int,
    enabled: bool,
) -> int:
    """ghost candidate から 1 つを選ぶ。mass-weighted random。

    enabled=False のときは fallback_rng (= ingestion_rng) で uniform random、
    既存 (v10.4) と同じ挙動。

    Returns:
        chosen_idx (candidates 内の index)
    """
    n = len(candidates)
    if n <= 1:
        return 0

    candidates_sorted = sorted(candidates, key=lambda x: x[0])
    cand_cids = [c[0] for c in candidates_sorted]

    if not enabled or salience_tracker is None:
        # uniform random fallback (= v10.4 ingestion_rng の挙動)
        chosen_idx = int(fallback_rng.integers(low=0, high=n))
        # log は残す (mass=0 で全候補 uniform と等価)
        if salience_tracker is not None:
            masses = [
                compute_mass(cid=cid, cog=cog, ledger=ledger,
                             beta_manager=beta_manager)
                for cid in cand_cids
            ]
            salience_tracker.log_event(
                global_step=global_step,
                observer_cid=observer_cid,
                candidate_cids=cand_cids,
                candidate_masses=masses,
                selected_cid=cand_cids[chosen_idx],
                event_type="ingestion_target_uniform",
            )
        return chosen_idx

    # mass-weighted random (本番時)
    masses = [
        compute_mass(cid=cid, cog=cog, ledger=ledger,
                     beta_manager=beta_manager)
        for cid in cand_cids
    ]
    weights = [
        SALIENCE_INGESTION_BASE_WEIGHT
        + SALIENCE_INGESTION_MASS_COEF * float(m)
        for m in masses
    ]
    total = sum(weights)
    if total <= 0:
        chosen_idx = int(salience_tracker.salience_rng.integers(low=0, high=n))
    else:
        # 累積 + 1 引き
        r = float(salience_tracker.salience_rng.random()) * total
        cum = 0.0
        chosen_idx = n - 1
        for i, w in enumerate(weights):
            cum += w
            if r <= cum:
                chosen_idx = i
                break

    salience_tracker.log_event(
        global_step=global_step,
        observer_cid=observer_cid,
        candidate_cids=cand_cids,
        candidate_masses=masses,
        selected_cid=cand_cids[chosen_idx],
        event_type="ingestion_target",
    )

    # 順序が変わった可能性があるため、元 candidates での index を返す
    return candidates.index(candidates_sorted[chosen_idx])


# ════════════════════════════════════════════════════════════════════
# be3 fired log only (発火そのものは物理駆動なので変更しない)
# ════════════════════════════════════════════════════════════════════

def log_be3_fired_event(
    *,
    cid_a: int,
    cid_b: int,
    cog: Any,
    ledger: Any,
    beta_manager: Any,
    salience_tracker: SalienceTracker,
    global_step: int,
    enabled: bool,
) -> None:
    """be3 fired 時に両者 mass を記録 (動作は変えない)。"""
    if salience_tracker is None or not enabled:
        return
    mass_a = compute_mass(cid=cid_a, cog=cog, ledger=ledger,
                          beta_manager=beta_manager)
    mass_b = compute_mass(cid=cid_b, cog=cog, ledger=ledger,
                          beta_manager=beta_manager)
    # 双方向 (a 観察 b、b 観察 a) を 2 件記録
    salience_tracker.log_event(
        global_step=global_step,
        observer_cid=int(cid_a),
        candidate_cids=[int(cid_b)],
        candidate_masses=[mass_b],
        selected_cid=int(cid_b),
        event_type="be3_fired",
    )
    salience_tracker.log_event(
        global_step=global_step,
        observer_cid=int(cid_b),
        candidate_cids=[int(cid_a)],
        candidate_masses=[mass_a],
        selected_cid=int(cid_a),
        event_type="be3_fired",
    )
