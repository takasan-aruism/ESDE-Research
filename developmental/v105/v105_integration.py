"""ESDE v10.5 — α/β Integration

v10.4 (`v104_integration.py`) からの差分:
  - α-Integration から Q_inherited / C_inherited / redistribute を削除
  - α は v10.5 で観察軸として再定義 (会計はしない)
  - β-Integration クラスを新規追加 (会計単位)

α と β の関係 (v105_integrated_design.md §3):
  - α  = 観察軸 (cid 集合の自然帰結、複数所属可、ダブルブッキング許容)
  - β  = 会計単位 (α 集合の意図的統合、cid は 1 β にのみ所属)

β 誕生条件 (Code A 質問回答 A2):
  - α 同士が共有 cid を 2 個以上持つ時、両者を含む β を統合 (推移閉包)
  - cid 単一共有時 (= 共有 1 個のみで β 統合されない場合) は、最強結合の
    α が属する β に cid を所属させる (案 b)

ghost 化時の処理 (回答 A3):
  - α への Q/C 継承は廃止
  - cid X が ghost 化 → X が所属する β-Integration が Q/C を 100% 継承

window 末再分配 (回答 A4):
  - α レベル再分配は廃止、β レベルでのみ実行
  - 状態依存逆張り分配 (v10.4 と同じルール)

recorded 化 (回答 A5):
  - α が member_cids 空 → α.state = recorded、β.member_alphas から外す
  - β の active 構成 α が 0 → β.state = recorded
  - recorded は永続 (Phantom 規律)

決定論性確保 (H.2):
  - α リストを α_id 順にソート、tie-break は α_id 最小
  - β 統合の順序を ID 順で固定
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


# ════════════════════════════════════════════════════════════════════
# α-Integration (v10.4 から Q/C 関連を削除した観察軸版)
# ════════════════════════════════════════════════════════════════════

@dataclass
class AlphaIntegration:
    integration_id: int
    birth_step: int
    trigger_type: str               # "be3" / "open_triad" / "closed_triad" / "third_overlap"
    state: str                      # "active" / "recorded"
    member_cids: set[int]           # 現在の active 構成 cid (ghost 化で除外)
    member_history: set[int]        # 過去含む全構成 cid (永続)
    binding_strengths: dict[int, float]  # cid -> strength (event 参加回数の合計)
    became_recorded_step: int = -1


class AlphaIntegrationManager:
    """α-Integration の lifecycle 管理 (観察軸専用)。

    v10.4 IntegrationManager からの変更点:
      - Q_inherited / C_inherited 関連を全削除
      - on_ghost で Q/C 継承を行わない (β に移管)
      - redistribute_q_c メソッドを削除 (β に移管)
      - lifecycle_log の event_type に "q_inherited" は出さない
    """

    def __init__(self, seed: int, target_tracker: Any = None) -> None:
        self.seed = int(seed)
        self._next_id = 0
        self.alphas: dict[int, AlphaIntegration] = {}
        self._target_tracker = target_tracker
        # cid -> set of alpha_id (active のみ)
        self.cid_to_alphas: dict[int, set[int]] = defaultdict(set)
        # 構造補助: members frozenset -> alpha_id
        self._active_members_index: dict[frozenset[int], int] = {}

        # window-scoped state
        self._window_be3_edges: set[tuple[int, int]] = set()
        self._window_be3_adj: dict[int, set[int]] = defaultdict(set)

        # window 集計用カウンタ
        self._window_n_born: int = 0
        self._window_n_state_transitioned: int = 0
        self._window_trigger_counter: Counter = Counter()

        # logger row buffers
        self.lifecycle_log: list[dict[str, Any]] = []

        # per_subject 集計補助
        self.cid_n_alphas_joined: Counter = Counter()

        # v10.5: β-Integration manager への通知用 callback
        # (新 α 誕生時、α member 変化時に呼ばれる)
        self._on_alpha_changed_callback: Any = None

    # ----------------------------------------------------------------
    def set_alpha_changed_callback(self, callback) -> None:
        """β-Integration manager の callback を登録する。

        callback(alpha_id, event: "birth" | "member_removed", removed_cid=None)
        """
        self._on_alpha_changed_callback = callback

    # ----------------------------------------------------------------
    def reset_window_state(self) -> None:
        self._window_be3_edges.clear()
        self._window_be3_adj.clear()
        self._window_n_born = 0
        self._window_n_state_transitioned = 0
        self._window_trigger_counter = Counter()

    def get_window_summary(self) -> dict[str, Any]:
        n_active = sum(
            1 for a in self.alphas.values() if a.state == "active")
        n_recorded = sum(
            1 for a in self.alphas.values() if a.state == "recorded")
        sizes = [len(a.member_cids) for a in self.alphas.values()
                 if a.state == "active" and a.member_cids]
        max_size = max(sizes) if sizes else 0
        mean_size = (sum(sizes) / len(sizes)) if sizes else 0.0
        trigger_dist_str = "{" + ",".join(
            f"{k}:{v}" for k, v in sorted(
                self._window_trigger_counter.items())
        ) + "}"
        return {
            "n_alphas_active": n_active,
            "n_alphas_recorded": n_recorded,
            "n_alphas_born": self._window_n_born,
            "n_alphas_state_transitioned":
                self._window_n_state_transitioned,
            "max_alpha_size": max_size,
            "mean_alpha_size": round(mean_size, 4),
            "alpha_trigger_dist": trigger_dist_str,
        }

    # ----------------------------------------------------------------
    # Trigger A-D 判定
    # ----------------------------------------------------------------
    def on_be3_fired(
        self, *,
        cid_a: int, cid_b: int,
        window: int, step: int, global_step: int,
        cog: Any, ledger: Any,
    ) -> list[int]:
        a, b = sorted((int(cid_a), int(cid_b)))

        prev_a_neighbors = set(self._window_be3_adj.get(a, ()))
        prev_b_neighbors = set(self._window_be3_adj.get(b, ()))

        new_ids: list[int] = []

        # Trigger A: be3
        new_id = self._maybe_birth(
            members=frozenset({a, b}),
            trigger_type="be3",
            window=window, step=step, global_step=global_step,
        )
        if new_id is not None:
            new_ids.append(new_id)

        # Trigger C: closed triad
        common = (prev_a_neighbors & prev_b_neighbors) - {a, b}
        for c in sorted(common):
            new_id = self._maybe_birth(
                members=frozenset({a, b, c}),
                trigger_type="closed_triad",
                window=window, step=step, global_step=global_step,
            )
            if new_id is not None:
                new_ids.append(new_id)

        # Trigger B: open triad
        for c in sorted((prev_a_neighbors - prev_b_neighbors) - {a, b}):
            new_id = self._maybe_birth(
                members=frozenset({a, b, c}),
                trigger_type="open_triad",
                window=window, step=step, global_step=global_step,
            )
            if new_id is not None:
                new_ids.append(new_id)
        for c in sorted((prev_b_neighbors - prev_a_neighbors) - {a, b}):
            new_id = self._maybe_birth(
                members=frozenset({a, b, c}),
                trigger_type="open_triad",
                window=window, step=step, global_step=global_step,
            )
            if new_id is not None:
                new_ids.append(new_id)

        # Trigger D: third_overlap
        third_candidates = (
            common
            | (prev_a_neighbors - prev_b_neighbors - {a, b})
            | (prev_b_neighbors - prev_a_neighbors - {a, b})
        )
        if len(third_candidates) >= 2:
            members = frozenset({a, b} | third_candidates)
            new_id = self._maybe_birth(
                members=members,
                trigger_type="third_overlap",
                window=window, step=step, global_step=global_step,
            )
            if new_id is not None:
                new_ids.append(new_id)

        # window edge graph 更新
        edge = (a, b)
        self._window_be3_edges.add(edge)
        self._window_be3_adj[a].add(b)
        self._window_be3_adj[b].add(a)

        return new_ids

    # ----------------------------------------------------------------
    def _maybe_birth(
        self, *,
        members: frozenset[int],
        trigger_type: str,
        window: int,
        step: int,
        global_step: int,
    ) -> int | None:
        if len(members) < 2:
            return None

        existing_id = self._active_members_index.get(members)
        if existing_id is not None:
            alpha = self.alphas[existing_id]
            for cid in members:
                alpha.binding_strengths[cid] = (
                    alpha.binding_strengths.get(cid, 0.0) + 1.0)
                alpha.member_history.add(cid)
            return None

        # 新規誕生
        aid = self._next_id
        self._next_id += 1
        member_set = set(int(c) for c in members)
        binding_strengths = {cid: 1.0 for cid in member_set}
        alpha = AlphaIntegration(
            integration_id=aid,
            birth_step=int(global_step),
            trigger_type=trigger_type,
            state="active",
            member_cids=member_set,
            member_history=set(member_set),
            binding_strengths=binding_strengths,
        )
        self.alphas[aid] = alpha
        self._active_members_index[frozenset(member_set)] = aid
        for cid in member_set:
            self.cid_to_alphas[cid].add(aid)
            self.cid_n_alphas_joined[cid] += 1

        # observation target に追加 (Stage 4)
        if self._target_tracker is not None:
            for cid in member_set:
                self._target_tracker.stage4_integration_member(
                    cid, int(global_step))

        # 集計
        self._window_n_born += 1
        self._window_trigger_counter[trigger_type] += 1

        # lifecycle log (α 専用、Q/C 列なし)
        self.lifecycle_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "alpha_id": aid,
            "event_type": "birth",
            "trigger_type": trigger_type,
            "member_cids": "|".join(str(c) for c in sorted(member_set)),
        })

        # β manager 通知
        if self._on_alpha_changed_callback is not None:
            self._on_alpha_changed_callback(
                alpha_id=aid, event="birth", global_step=int(global_step))

        return aid

    # ----------------------------------------------------------------
    # ghost 化時 (v10.5: Q/C 継承は β に移管、α はメンバーから外すのみ)
    # ----------------------------------------------------------------
    def on_ghost(
        self, *,
        cid: int,
        global_step: int,
    ) -> list[int]:
        """cid X が ghost 化した時、α からのメンバー除外のみ実施。

        Returns:
            recorded 化した α_id のリスト
        """
        cid = int(cid)
        joined_ids = list(self.cid_to_alphas.get(cid, ()))
        if not joined_ids:
            return []

        recorded_alphas: list[int] = []

        for aid in joined_ids:
            alpha = self.alphas[aid]
            old_members = frozenset(alpha.member_cids)
            if cid in alpha.member_cids:
                alpha.member_cids.discard(cid)
                alpha.member_history.add(cid)
                if old_members in self._active_members_index:
                    if self._active_members_index[old_members] == aid:
                        del self._active_members_index[old_members]
                if alpha.state == "active" and alpha.member_cids:
                    new_members = frozenset(alpha.member_cids)
                    if new_members not in self._active_members_index:
                        self._active_members_index[new_members] = aid

        self.cid_to_alphas.pop(cid, None)

        # β manager 通知 (member 削除)
        if self._on_alpha_changed_callback is not None:
            for aid in joined_ids:
                self._on_alpha_changed_callback(
                    alpha_id=aid, event="member_removed",
                    removed_cid=cid, global_step=int(global_step))

        # recorded 遷移判定
        for aid in joined_ids:
            alpha = self.alphas[aid]
            if alpha.state == "active" and not alpha.member_cids:
                alpha.state = "recorded"
                alpha.became_recorded_step = int(global_step)
                self._window_n_state_transitioned += 1
                recorded_alphas.append(aid)
                self.lifecycle_log.append({
                    "seed": self.seed,
                    "step": int(global_step),
                    "alpha_id": aid,
                    "event_type": "active_to_recorded",
                    "trigger_type": alpha.trigger_type,
                    "member_cids": "",
                })
                # β manager 通知
                if self._on_alpha_changed_callback is not None:
                    self._on_alpha_changed_callback(
                        alpha_id=aid, event="recorded",
                        global_step=int(global_step))

        # member_ghosted log (Q/C 列なし)
        for aid in joined_ids:
            alpha = self.alphas[aid]
            self.lifecycle_log.append({
                "seed": self.seed,
                "step": int(global_step),
                "alpha_id": aid,
                "event_type": "member_ghosted",
                "trigger_type": alpha.trigger_type,
                "member_cids": "|".join(
                    str(c) for c in sorted(alpha.member_cids)),
            })

        return recorded_alphas

    # ----------------------------------------------------------------
    def all_member_cids(self) -> set[int]:
        out: set[int] = set()
        for alpha in self.alphas.values():
            out.update(alpha.member_history)
        return out

    def get_membership_snapshot_rows(self, current_step: int) -> list[dict]:
        rows = []
        cid_to_active: dict[int, list[int]] = defaultdict(list)
        for aid, alpha in self.alphas.items():
            if alpha.state != "active":
                continue
            for cid in alpha.member_cids:
                cid_to_active[cid].append(aid)
        for cid, aids in cid_to_active.items():
            aids_sorted = sorted(aids)
            strengths = []
            for aid in aids_sorted:
                strengths.append(
                    f"{aid}:{self.alphas[aid].binding_strengths.get(cid, 0.0):.1f}"
                )
            rows.append({
                "seed": self.seed,
                "step": int(current_step),
                "cid_id": int(cid),
                "alpha_ids": "|".join(str(i) for i in aids_sorted),
                "binding_strengths": "|".join(strengths),
            })
        return rows


# ════════════════════════════════════════════════════════════════════
# β-Integration (v10.5 新規、会計単位)
# ════════════════════════════════════════════════════════════════════

@dataclass
class BetaIntegration:
    beta_id: int
    birth_step: int
    state: str                              # "active" / "recorded"
    member_alphas: set[int]                 # 現在の active 構成 α
    member_alphas_history: set[int]         # 過去含む全構成 α (永続)
    member_cids: set[int]                   # 現在 active な所属 cid
    member_cids_history: set[int]           # 過去含む所属 cid (永続)
    Q_inherited: int                        # ghost 化 cid から継承した Q
    C_inherited: int                        # ghost 化 cid から継承した C
    # cid -> 元 α での最強 binding_strength (recorded β 漏れ機構で参照)
    cid_original_binding: dict[int, float] = field(default_factory=dict)
    became_recorded_step: int = -1


# β 統合の最小共有閾値 (Taka 承認: 2)
BETA_MERGE_MIN_SHARED_CIDS = 2


class BetaIntegrationManager:
    """β-Integration の lifecycle 管理 (会計単位)。

    α-Integration 群の連結関係を Union-Find で保持し、共有 cid 2 個以上
    の α 同士を 1 つの β に統合する。cid 1 個共有では統合せず、cid 自身
    は最強結合 α が属する β に 1 個だけ所属する (会計の規律)。
    """

    def __init__(self, seed: int, alpha_manager: AlphaIntegrationManager,
                 target_tracker: Any = None) -> None:
        self.seed = int(seed)
        self.alpha_manager = alpha_manager
        self._target_tracker = target_tracker
        self._next_id = 0
        self.betas: dict[int, BetaIntegration] = {}

        # α_id -> beta_id (active α が属する β)
        self.alpha_to_beta: dict[int, int] = {}
        # cid -> beta_id (active cid が会計上属する β、1 個のみ)
        self.cid_to_beta: dict[int, int] = {}

        # window 集計
        self._window_n_born: int = 0
        self._window_n_state_transitioned: int = 0
        self._window_total_q_inherited: int = 0
        self._window_total_c_inherited: int = 0
        self._window_total_q_distributed: int = 0
        self._window_total_c_distributed: int = 0

        # logger
        self.lifecycle_log: list[dict[str, Any]] = []
        self.distribution_log: list[dict[str, Any]] = []

        # per_subject 集計
        self.cid_q_received_from_betas: Counter = Counter()
        self.cid_c_received_from_betas: Counter = Counter()
        self.cid_q_inherited_to_beta: Counter = Counter()
        self.cid_c_inherited_to_beta: Counter = Counter()
        self.cid_n_betas_joined: Counter = Counter()

        # alpha_manager に callback を登録
        alpha_manager.set_alpha_changed_callback(
            self._on_alpha_changed)

    # ----------------------------------------------------------------
    def reset_window_state(self) -> None:
        self._window_n_born = 0
        self._window_n_state_transitioned = 0
        self._window_total_q_inherited = 0
        self._window_total_c_inherited = 0
        self._window_total_q_distributed = 0
        self._window_total_c_distributed = 0

    def get_window_summary(self) -> dict[str, Any]:
        n_active = sum(1 for b in self.betas.values() if b.state == "active")
        n_recorded = sum(
            1 for b in self.betas.values() if b.state == "recorded")
        sizes_alpha = [len(b.member_alphas) for b in self.betas.values()
                       if b.state == "active" and b.member_alphas]
        sizes_cid = [len(b.member_cids) for b in self.betas.values()
                     if b.state == "active" and b.member_cids]
        return {
            "n_betas_active": n_active,
            "n_betas_recorded": n_recorded,
            "n_betas_born": self._window_n_born,
            "n_betas_state_transitioned": self._window_n_state_transitioned,
            "total_beta_q_inherited": self._window_total_q_inherited,
            "total_beta_c_inherited": self._window_total_c_inherited,
            "total_beta_q_distributed": self._window_total_q_distributed,
            "total_beta_c_distributed": self._window_total_c_distributed,
            "max_beta_alpha_size": max(sizes_alpha) if sizes_alpha else 0,
            "mean_beta_alpha_size":
                round(sum(sizes_alpha) / len(sizes_alpha), 4)
                if sizes_alpha else 0.0,
            "max_beta_cid_size": max(sizes_cid) if sizes_cid else 0,
            "mean_beta_cid_size":
                round(sum(sizes_cid) / len(sizes_cid), 4)
                if sizes_cid else 0.0,
        }

    # ----------------------------------------------------------------
    # α 変化通知 → β 構造の再評価
    # ----------------------------------------------------------------
    def _on_alpha_changed(
        self, *, alpha_id: int, event: str,
        global_step: int, removed_cid: int = None,
    ) -> None:
        """alpha_manager からの通知。

        event: "birth" / "member_removed" / "recorded"
        """
        if event == "birth":
            self._handle_alpha_birth(alpha_id, global_step)
        elif event == "member_removed":
            self._handle_alpha_member_removed(
                alpha_id, removed_cid, global_step)
        elif event == "recorded":
            self._handle_alpha_recorded(alpha_id, global_step)

    # ----------------------------------------------------------------
    def _handle_alpha_birth(self, alpha_id: int, global_step: int) -> None:
        """新 α 誕生時の β 統合判定。

        新 α と既存 active α 群の cid 共有度を計算し、共有 ≥ 2 の α が
        所属する β に新 α を加える (推移閉包で複数 β を統合する場合あり)。
        """
        alpha = self.alpha_manager.alphas[alpha_id]
        new_cids = set(alpha.member_cids)

        # 既存 active α のうち、新 α と共有 cid ≥ 2 のものを候補とする
        # (大規模時の高速化: 新 α の cid から逆引きで関連 α を絞る)
        candidate_alphas: set[int] = set()
        for cid in new_cids:
            for other_aid in self.alpha_manager.cid_to_alphas.get(cid, ()):
                if other_aid != alpha_id:
                    candidate_alphas.add(other_aid)

        merged_betas: set[int] = set()
        for other_aid in sorted(candidate_alphas):
            other = self.alpha_manager.alphas.get(other_aid)
            if other is None or other.state != "active":
                continue
            shared = new_cids & other.member_cids
            if len(shared) >= BETA_MERGE_MIN_SHARED_CIDS:
                other_beta = self.alpha_to_beta.get(other_aid)
                if other_beta is not None:
                    merged_betas.add(other_beta)

        if not merged_betas:
            # 既存 β なし → 新 β を生成
            bid = self._create_new_beta(alpha_id, global_step)
        else:
            # 1 つ以上の β に統合 (推移閉包)
            target_bid = min(merged_betas)
            for other_bid in sorted(merged_betas):
                if other_bid != target_bid:
                    self._merge_beta_into(other_bid, target_bid, global_step)
            self._add_alpha_to_beta(alpha_id, target_bid, global_step)
            bid = target_bid

        # 全 cid の β 所属を再評価 (= 最強結合 α の β に揃える)
        self._reassign_cids_for_beta(bid, global_step)

        # observation target に追加 (Stage 4)
        if self._target_tracker is not None:
            beta = self.betas[bid]
            for cid in beta.member_cids:
                self._target_tracker.stage4_integration_member(
                    cid, int(global_step))

    # ----------------------------------------------------------------
    def _create_new_beta(self, alpha_id: int, global_step: int) -> int:
        bid = self._next_id
        self._next_id += 1
        alpha = self.alpha_manager.alphas[alpha_id]
        beta = BetaIntegration(
            beta_id=bid,
            birth_step=int(global_step),
            state="active",
            member_alphas={alpha_id},
            member_alphas_history={alpha_id},
            member_cids=set(alpha.member_cids),
            member_cids_history=set(alpha.member_cids),
            Q_inherited=0,
            C_inherited=0,
            cid_original_binding={
                cid: alpha.binding_strengths.get(cid, 0.0)
                for cid in alpha.member_cids
            },
        )
        self.betas[bid] = beta
        self.alpha_to_beta[alpha_id] = bid
        for cid in alpha.member_cids:
            self.cid_to_beta[cid] = bid
            self.cid_n_betas_joined[cid] += 1
        self._window_n_born += 1

        self.lifecycle_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "beta_id": bid,
            "event_type": "birth",
            "member_alphas": str(alpha_id),
            "member_cids": "|".join(str(c) for c in sorted(beta.member_cids)),
            "q_inherited_total": 0,
            "c_inherited_total": 0,
            "q_inherited_delta": 0,
            "c_inherited_delta": 0,
        })
        return bid

    # ----------------------------------------------------------------
    def _add_alpha_to_beta(
        self, alpha_id: int, bid: int, global_step: int,
    ) -> None:
        beta = self.betas[bid]
        if alpha_id in beta.member_alphas:
            return
        alpha = self.alpha_manager.alphas[alpha_id]
        beta.member_alphas.add(alpha_id)
        beta.member_alphas_history.add(alpha_id)
        beta.member_cids_history.update(alpha.member_cids)
        self.alpha_to_beta[alpha_id] = bid

        self.lifecycle_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "beta_id": bid,
            "event_type": "alpha_added",
            "member_alphas": "|".join(
                str(a) for a in sorted(beta.member_alphas)),
            "member_cids": "",
            "q_inherited_total": int(beta.Q_inherited),
            "c_inherited_total": int(beta.C_inherited),
            "q_inherited_delta": 0,
            "c_inherited_delta": 0,
        })

    # ----------------------------------------------------------------
    def _merge_beta_into(
        self, src_bid: int, dst_bid: int, global_step: int,
    ) -> None:
        """src_bid β を dst_bid β に吸収する (src は削除)。"""
        if src_bid == dst_bid:
            return
        src = self.betas[src_bid]
        dst = self.betas[dst_bid]

        for aid in list(src.member_alphas):
            self.alpha_to_beta[aid] = dst_bid
        dst.member_alphas.update(src.member_alphas)
        dst.member_alphas_history.update(src.member_alphas_history)
        dst.member_cids.update(src.member_cids)
        dst.member_cids_history.update(src.member_cids_history)
        # binding 情報マージ (大きい方を採用)
        for cid, bs in src.cid_original_binding.items():
            if bs > dst.cid_original_binding.get(cid, 0.0):
                dst.cid_original_binding[cid] = bs
        # Q/C 加算
        dst.Q_inherited += src.Q_inherited
        dst.C_inherited += src.C_inherited

        # cid_to_beta 更新
        for cid in list(self.cid_to_beta.keys()):
            if self.cid_to_beta[cid] == src_bid:
                self.cid_to_beta[cid] = dst_bid

        # log
        self.lifecycle_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "beta_id": dst_bid,
            "event_type": "beta_merged",
            "member_alphas": "|".join(
                str(a) for a in sorted(dst.member_alphas)),
            "member_cids": f"merged_from_beta_{src_bid}",
            "q_inherited_total": int(dst.Q_inherited),
            "c_inherited_total": int(dst.C_inherited),
            "q_inherited_delta": int(src.Q_inherited),
            "c_inherited_delta": int(src.C_inherited),
        })

        del self.betas[src_bid]

    # ----------------------------------------------------------------
    def _reassign_cids_for_beta(
        self, bid: int, global_step: int,
    ) -> None:
        """β に所属する全 α が共有する cid 群を再評価し、最強結合 α の β
        に各 cid を所属させる。ダブルブッキング解消の中核処理 (案 b)。
        """
        beta = self.betas[bid]
        # この β の構成 α 群が触れる全 cid を集める
        cid_set: set[int] = set()
        for aid in beta.member_alphas:
            alpha = self.alpha_manager.alphas.get(aid)
            if alpha is None or alpha.state != "active":
                continue
            cid_set.update(alpha.member_cids)

        for cid in cid_set:
            # cid が所属する全 active α を取得
            joined_alphas = list(self.alpha_manager.cid_to_alphas.get(cid, ()))
            if not joined_alphas:
                continue
            # 各 α での binding_strength の最大値で cid の β 所属を決定
            best_aid = None
            best_bs = -1.0
            for aid in sorted(joined_alphas):
                alpha = self.alpha_manager.alphas.get(aid)
                if alpha is None or alpha.state != "active":
                    continue
                bs = alpha.binding_strengths.get(cid, 0.0)
                if bs > best_bs or (bs == best_bs and best_aid is None):
                    best_bs = bs
                    best_aid = aid
            if best_aid is None:
                continue
            target_bid = self.alpha_to_beta.get(best_aid)
            if target_bid is None:
                continue
            current_bid = self.cid_to_beta.get(cid)
            if current_bid != target_bid:
                # cid の β 所属を更新
                if current_bid is not None and current_bid in self.betas:
                    self.betas[current_bid].member_cids.discard(cid)
                self.betas[target_bid].member_cids.add(cid)
                self.betas[target_bid].member_cids_history.add(cid)
                self.betas[target_bid].cid_original_binding[cid] = best_bs
                self.cid_to_beta[cid] = target_bid
                if current_bid is None:
                    self.cid_n_betas_joined[cid] += 1

    # ----------------------------------------------------------------
    def _handle_alpha_member_removed(
        self, alpha_id: int, removed_cid: int, global_step: int,
    ) -> None:
        """α から cid が除外されたとき、β の cid 集合を再評価。"""
        bid = self.alpha_to_beta.get(alpha_id)
        if bid is None or bid not in self.betas:
            return
        beta = self.betas[bid]
        # cid が他の active α (この β 内) にも所属しているか確認
        still_active = False
        for aid in beta.member_alphas:
            other = self.alpha_manager.alphas.get(aid)
            if other is None or other.state != "active":
                continue
            if removed_cid in other.member_cids:
                still_active = True
                break
        if not still_active:
            beta.member_cids.discard(removed_cid)

    # ----------------------------------------------------------------
    def _handle_alpha_recorded(self, alpha_id: int, global_step: int) -> None:
        """α が recorded 化したとき、β.member_alphas から削除。
        β の active 構成 α が 0 になったら β.state = recorded。"""
        bid = self.alpha_to_beta.get(alpha_id)
        if bid is None or bid not in self.betas:
            return
        beta = self.betas[bid]
        beta.member_alphas.discard(alpha_id)
        # alpha_to_beta は履歴として残す (recorded β 漏れ機構で参照)

        # active 構成 α が 0 → β recorded
        if not beta.member_alphas and beta.state == "active":
            beta.state = "recorded"
            beta.became_recorded_step = int(global_step)
            self._window_n_state_transitioned += 1
            self.lifecycle_log.append({
                "seed": self.seed,
                "step": int(global_step),
                "beta_id": bid,
                "event_type": "active_to_recorded",
                "member_alphas": "",
                "member_cids": "",
                "q_inherited_total": int(beta.Q_inherited),
                "c_inherited_total": int(beta.C_inherited),
                "q_inherited_delta": 0,
                "c_inherited_delta": 0,
            })

    # ----------------------------------------------------------------
    # ghost 化時 Q/C 継承 (β に 100%、回答 A3)
    # ----------------------------------------------------------------
    def on_ghost(
        self, *,
        cid: int,
        q_at_ghost: int,
        c_at_ghost: int,
        global_step: int,
    ) -> None:
        cid = int(cid)
        bid = self.cid_to_beta.get(cid)
        if bid is None or bid not in self.betas:
            return  # cid は β に未所属、継承先なし
        beta = self.betas[bid]
        beta.Q_inherited += int(q_at_ghost)
        beta.C_inherited += int(c_at_ghost)
        self._window_total_q_inherited += int(q_at_ghost)
        self._window_total_c_inherited += int(c_at_ghost)

        self.cid_q_inherited_to_beta[cid] += int(q_at_ghost)
        self.cid_c_inherited_to_beta[cid] += int(c_at_ghost)

        beta.member_cids.discard(cid)
        # cid_to_beta は履歴として残す (recorded β 漏れ機構が参照)

        self.lifecycle_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "beta_id": bid,
            "event_type": "q_c_inherited",
            "member_alphas": "|".join(
                str(a) for a in sorted(beta.member_alphas)),
            "member_cids": "|".join(
                str(c) for c in sorted(beta.member_cids)),
            "q_inherited_total": int(beta.Q_inherited),
            "c_inherited_total": int(beta.C_inherited),
            "q_inherited_delta": int(q_at_ghost),
            "c_inherited_delta": int(c_at_ghost),
        })

    # ----------------------------------------------------------------
    # window 末再分配 (β レベルで実行、回答 A4)
    # ----------------------------------------------------------------
    def redistribute_q_c(
        self, *,
        window: int,
        global_step: int,
        cog: Any,
        ledger: Any,
        shadow_audit: bool = False,
    ) -> None:
        for bid, beta in list(self.betas.items()):
            if beta.state != "active":
                continue
            if beta.Q_inherited == 0 and beta.C_inherited == 0:
                continue
            active_members = sorted(int(c) for c in beta.member_cids
                                    if cog.is_hosted(c))
            if not active_members:
                continue

            total_q = int(beta.Q_inherited)
            total_c = int(beta.C_inherited)

            shortage_q: list[float] = []
            shortage_c: list[float] = []
            for cid in active_members:
                ledger_entry = ledger.ledger.get(cid)
                q_val = int(ledger_entry["v14_q_remaining"]) \
                    if ledger_entry is not None else 0
                c_val = int(cog.C.get(cid, 0))
                denom = q_val + c_val + 1e-9
                q_ratio = q_val / denom
                if q_ratio < 0.5:
                    shortage_q.append(0.5 - q_ratio)
                    shortage_c.append(0.0)
                else:
                    shortage_q.append(0.0)
                    shortage_c.append(q_ratio - 0.5)

            sum_sq = sum(shortage_q) + 1e-9
            sum_sc = sum(shortage_c) + 1e-9

            actual_dist_q = 0
            actual_dist_c = 0
            for i, cid in enumerate(active_members):
                q_alloc = int(total_q * shortage_q[i] / sum_sq)
                c_alloc = int(total_c * shortage_c[i] / sum_sc)
                if q_alloc == 0 and c_alloc == 0:
                    continue

                ledger_entry = ledger.ledger.get(cid)
                q_before = int(ledger_entry["v14_q_remaining"]) \
                    if ledger_entry is not None else 0
                c_before = int(cog.C.get(cid, 0))
                denom_b = q_before + c_before + 1e-9
                ratio_before = q_before / denom_b

                if not shadow_audit:
                    if q_alloc > 0 and ledger_entry is not None:
                        ledger_entry["v14_q_remaining"] = q_before + q_alloc
                    if c_alloc > 0 and cid in cog.C:
                        cog.C[cid] = c_before + c_alloc

                q_after = q_before + q_alloc if not shadow_audit else q_before
                c_after = c_before + c_alloc if not shadow_audit else c_before
                denom_a = q_after + c_after + 1e-9
                ratio_after = q_after / denom_a

                actual_dist_q += q_alloc
                actual_dist_c += c_alloc

                self.cid_q_received_from_betas[cid] += q_alloc
                self.cid_c_received_from_betas[cid] += c_alloc

                self.distribution_log.append({
                    "seed": self.seed,
                    "step": int(global_step),
                    "beta_id": bid,
                    "target_cid": int(cid),
                    "q_distributed": int(q_alloc),
                    "c_distributed": int(c_alloc),
                    "target_q_ratio_before": round(ratio_before, 6),
                    "target_q_ratio_after": round(ratio_after, 6),
                })

            beta.Q_inherited = 0
            beta.C_inherited = 0
            self._window_total_q_distributed += actual_dist_q
            self._window_total_c_distributed += actual_dist_c

    # ----------------------------------------------------------------
    # 漏れ機構サポート: cid Y が過去に所属した recorded β を返す (最強結合 1 個)
    # ----------------------------------------------------------------
    def get_strongest_recorded_beta_for(self, cid: int) -> int | None:
        """cid の history を辿り、最強結合の recorded β_id を返す。
        該当なしなら None。"""
        cid = int(cid)
        # cid_to_beta は active 中のみだが、cid が ghost 化後は履歴として残る
        # member_cids_history を持つ β を検索
        candidates: list[tuple[float, int]] = []
        for bid, beta in self.betas.items():
            if beta.state != "recorded":
                continue
            if cid not in beta.member_cids_history:
                continue
            if beta.C_inherited <= 0:
                continue
            bs = beta.cid_original_binding.get(cid, 0.0)
            candidates.append((bs, bid))
        if not candidates:
            return None
        # 最強結合、tie は β_id 最小
        candidates.sort(key=lambda x: (-x[0], x[1]))
        return candidates[0][1]

    def apply_leakage(
        self, *, recipient_cid: int, recorded_bid: int,
        amount: int, cog: Any, shadow_audit: bool = False,
    ) -> int:
        """recorded β から recipient_cid.C へ amount 単位の漏れを実行。

        Returns:
            実際に漏れた量 (β.C_inherited が不足の場合は減らす)
        """
        if recorded_bid not in self.betas:
            return 0
        beta = self.betas[recorded_bid]
        if beta.state != "recorded":
            return 0
        actual = min(int(amount), int(beta.C_inherited))
        if actual <= 0:
            return 0
        if not shadow_audit:
            beta.C_inherited -= actual
            if recipient_cid in cog.C:
                cog.C[recipient_cid] = int(cog.C.get(recipient_cid, 0)) + actual
        return actual

    # ----------------------------------------------------------------
    def get_membership_snapshot_rows(self, current_step: int) -> list[dict]:
        rows = []
        for bid, beta in self.betas.items():
            rows.append({
                "seed": self.seed,
                "step": int(current_step),
                "beta_id": bid,
                "state": beta.state,
                "birth_step": int(beta.birth_step),
                "became_recorded_step": int(beta.became_recorded_step),
                "n_member_alphas_active": len(beta.member_alphas),
                "n_member_alphas_history": len(beta.member_alphas_history),
                "n_member_cids_active": len(beta.member_cids),
                "n_member_cids_history": len(beta.member_cids_history),
                "member_alphas": "|".join(
                    str(a) for a in sorted(beta.member_alphas)),
                "member_cids": "|".join(
                    str(c) for c in sorted(beta.member_cids)),
                "Q_inherited": int(beta.Q_inherited),
                "C_inherited": int(beta.C_inherited),
            })
        return rows


# ════════════════════════════════════════════════════════════════════
# 統合エントリポイント (main loop から見ると 1 つの interface)
# ════════════════════════════════════════════════════════════════════

class IntegrationManagerV105:
    """v10.5 統合 manager: α + β を 1 ハンドルで操作。

    main loop からの呼び出し互換性のため、v104 と同名のメソッドを提供する:
      - on_be3_fired
      - on_ghost
      - redistribute_q_c
      - reset_window_state
      - get_window_summary
    """

    def __init__(self, seed: int, target_tracker: Any = None) -> None:
        self.seed = int(seed)
        self.alpha = AlphaIntegrationManager(seed=seed,
                                              target_tracker=target_tracker)
        self.beta = BetaIntegrationManager(seed=seed,
                                            alpha_manager=self.alpha,
                                            target_tracker=target_tracker)

    def reset_window_state(self) -> None:
        self.alpha.reset_window_state()
        self.beta.reset_window_state()

    def on_be3_fired(
        self, *,
        cid_a: int, cid_b: int,
        window: int, step: int, global_step: int,
        cog: Any, ledger: Any,
    ) -> list[int]:
        return self.alpha.on_be3_fired(
            cid_a=cid_a, cid_b=cid_b,
            window=window, step=step, global_step=global_step,
            cog=cog, ledger=ledger)

    def on_ghost(
        self, *,
        cid: int,
        q_at_ghost: int,
        c_at_ghost: int,
        global_step: int,
        cog: Any,
        ledger: Any,
    ) -> None:
        # 1. α 側: メンバー除外、recorded 化判定 (Q/C 継承はしない)
        self.alpha.on_ghost(cid=cid, global_step=global_step)
        # 2. β 側: Q/C 100% 継承
        self.beta.on_ghost(
            cid=cid, q_at_ghost=q_at_ghost, c_at_ghost=c_at_ghost,
            global_step=global_step)

    def redistribute_q_c(
        self, *,
        window: int, global_step: int,
        cog: Any, ledger: Any,
        shadow_audit: bool = False,
    ) -> None:
        # β レベルでのみ再分配
        self.beta.redistribute_q_c(
            window=window, global_step=global_step,
            cog=cog, ledger=ledger, shadow_audit=shadow_audit)

    def get_window_summary(self) -> dict[str, Any]:
        s = {}
        s.update(self.alpha.get_window_summary())
        s.update(self.beta.get_window_summary())
        return s
