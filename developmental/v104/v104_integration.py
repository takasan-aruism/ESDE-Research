"""ESDE v10.4 — Integration

実装指示書 v104_phase_design.md / v104_implementation_brief.md に基づく。

Integration は構成 cid の Q/C を集約・保持・再分配し、ghost 化した構成 cid の
Q/C を継承する独立主体。

誕生 trigger (§3):
  A. be3            — 双方向 E3 fired pair (cid_a, cid_b)
  B. open_triad     — A-B + (A-C or B-C) 成立、欠片の C-? 不在
  C. closed_triad   — A-B, B-C, C-A 全成立
  D. third_overlap  — 1 つの be3 ペアに対し第三項候補が 2 個以上同 step 重複

設計規律 (§14):
  - 物理層 frozen
  - cid 内部 (M_c 等) は不変
  - Integration は認知層・意識層への間接バイアスのみ (Q/C 加算)
  - recorded 状態は永続
  - Q/C 継承は最強結合 1 つに全部 (二重カウント回避)
  - 神の手回避 (誕生条件は客観条件のみ)

§3.2 重複判定: 新規 Integration を作る前に、同じ member_cids を持つ active
Integration が既に存在するかチェック。存在する場合は新規作成せず、binding
strengths のみ更新。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Integration:
    integration_id: int
    birth_step: int
    trigger_type: str               # "be3" / "open_triad" / "closed_triad" / "third_overlap"
    state: str                      # "active" / "recorded"
    member_cids: set[int]           # 現在の active 構成 cid (ghost 化で除外)
    member_history: set[int]        # 過去含む全構成 cid (永続)
    Q_inherited: int                # ghost 化した cid から継承した Q
    C_inherited: int                # ghost 化した cid から継承した C
    binding_strengths: dict[int, float]  # cid -> strength (event 参加回数の合計)
    became_recorded_step: int = -1  # state="recorded" 遷移 step (-1 = 未遷移)


class IntegrationManager:
    """Integration の lifecycle 管理。

    seed ごとに 1 インスタンス。誕生・継承・再分配を一元管理。
    Logger 4-6 の row 蓄積もここで行う。
    """

    def __init__(self, seed: int, target_tracker: Any = None) -> None:
        self.seed = int(seed)
        self._next_id = 0
        self.integrations: dict[int, Integration] = {}
        # ObservationTargetTracker (§11: Integration 構成 cid を target に追加)
        # None なら何もしない (テスト互換)
        self._target_tracker = target_tracker
        # cid -> set of integration_id (active 構成 cid のみ)
        self.cid_to_integrations: dict[int, set[int]] = defaultdict(set)
        # 構造補助: members frozenset -> integration_id (active 一致判定の高速化)
        self._active_members_index: dict[frozenset[int], int] = {}

        # window-scoped state (window 開始時にリセット)
        # 同 window 内 be3 fired edges (sorted tuple)
        self._window_be3_edges: set[tuple[int, int]] = set()
        # cid -> set of partners (be3 fired this window, undirected)
        self._window_be3_adj: dict[int, set[int]] = defaultdict(set)

        # window 集計用カウンタ (per_window 列に出力)
        self._window_n_born: int = 0
        self._window_n_state_transitioned: int = 0
        self._window_total_q_inherited: int = 0
        self._window_total_c_inherited: int = 0
        self._window_total_q_distributed: int = 0
        self._window_total_c_distributed: int = 0
        self._window_trigger_counter: Counter = Counter()

        # logger row buffers
        self.lifecycle_log: list[dict[str, Any]] = []
        self.distribution_log: list[dict[str, Any]] = []
        # membership log は run 末に snapshot を取るので、ここでは蓄積しない
        # (per_subject 集計用に cid_received_q / cid_received_c などを別途保持)

        # per_subject 集計補助
        self.cid_n_integrations_joined: Counter = Counter()  # 累積所属
        self.cid_q_received_from_integrations: Counter = Counter()
        self.cid_c_received_from_integrations: Counter = Counter()
        self.cid_q_inherited_to_integration: Counter = Counter()
        self.cid_c_inherited_to_integration: Counter = Counter()

    # ----------------------------------------------------------------
    # window 開始/末
    # ----------------------------------------------------------------
    def reset_window_state(self) -> None:
        """window 開始時に呼ぶ。be3 edge graph と window 集計カウンタをリセット。"""
        self._window_be3_edges.clear()
        self._window_be3_adj.clear()
        self._window_n_born = 0
        self._window_n_state_transitioned = 0
        self._window_total_q_inherited = 0
        self._window_total_c_inherited = 0
        self._window_total_q_distributed = 0
        self._window_total_c_distributed = 0
        self._window_trigger_counter = Counter()

    def get_window_summary(self) -> dict[str, Any]:
        n_active = sum(
            1 for i in self.integrations.values() if i.state == "active")
        n_recorded = sum(
            1 for i in self.integrations.values() if i.state == "recorded")
        sizes = [len(i.member_cids) for i in self.integrations.values()
                 if i.state == "active" and i.member_cids]
        max_size = max(sizes) if sizes else 0
        mean_size = (sum(sizes) / len(sizes)) if sizes else 0.0
        trigger_dist_str = "{" + ",".join(
            f"{k}:{v}" for k, v in sorted(
                self._window_trigger_counter.items())
        ) + "}"
        return {
            "n_integrations_active": n_active,
            "n_integrations_recorded": n_recorded,
            "n_integrations_born": self._window_n_born,
            "n_integrations_state_transitioned":
                self._window_n_state_transitioned,
            "total_q_inherited": self._window_total_q_inherited,
            "total_c_inherited": self._window_total_c_inherited,
            "total_q_distributed": self._window_total_q_distributed,
            "total_c_distributed": self._window_total_c_distributed,
            "max_integration_size": max_size,
            "mean_integration_size": round(mean_size, 4),
            "trigger_type_dist": trigger_dist_str,
        }

    # ----------------------------------------------------------------
    # Trigger A-D 判定 (per-step、be3 fired 直後に呼ぶ)
    # ----------------------------------------------------------------
    def on_be3_fired(
        self, *,
        cid_a: int, cid_b: int,
        window: int, step: int, global_step: int,
        cog: Any, ledger: Any,
    ) -> list[int]:
        """be3 が発火した直後 (= bidirectional_e3 phase 内、shadow_audit 関係なく)
        に呼ぶ。Trigger A/B/C/D を判定し、必要なら Integration 誕生。

        Returns:
            新規誕生した integration_id のリスト (既存更新は含まない)
        """
        a, b = sorted((int(cid_a), int(cid_b)))

        prev_a_neighbors = set(self._window_be3_adj.get(a, ()))
        prev_b_neighbors = set(self._window_be3_adj.get(b, ()))

        # window edge graph 更新 (Trigger 判定後に追加すると、両方向に対応できる)
        new_ids: list[int] = []

        # Trigger A: be3 fired (cid_a, cid_b)
        new_id = self._maybe_birth(
            members=frozenset({a, b}),
            trigger_type="be3",
            window=window, step=step, global_step=global_step,
            cog=cog, ledger=ledger,
        )
        if new_id is not None:
            new_ids.append(new_id)

        # Trigger C: closed triad — a と b の共通隣接 c (除自分)
        common = (prev_a_neighbors & prev_b_neighbors) - {a, b}
        for c in sorted(common):
            new_id = self._maybe_birth(
                members=frozenset({a, b, c}),
                trigger_type="closed_triad",
                window=window, step=step, global_step=global_step,
                cog=cog, ledger=ledger,
            )
            if new_id is not None:
                new_ids.append(new_id)

        # Trigger B: open triad — a-b 新規 + (a-c のみ) or (b-c のみ)
        for c in sorted((prev_a_neighbors - prev_b_neighbors) - {a, b}):
            new_id = self._maybe_birth(
                members=frozenset({a, b, c}),
                trigger_type="open_triad",
                window=window, step=step, global_step=global_step,
                cog=cog, ledger=ledger,
            )
            if new_id is not None:
                new_ids.append(new_id)
        for c in sorted((prev_b_neighbors - prev_a_neighbors) - {a, b}):
            new_id = self._maybe_birth(
                members=frozenset({a, b, c}),
                trigger_type="open_triad",
                window=window, step=step, global_step=global_step,
                cog=cog, ledger=ledger,
            )
            if new_id is not None:
                new_ids.append(new_id)

        # Trigger D: third_overlap — 同 step で第三項候補が 2 個以上重複
        # (closed + open 両方の third 候補集合の和)
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
                cog=cog, ledger=ledger,
            )
            if new_id is not None:
                new_ids.append(new_id)

        # window edge graph に追加 (次回以降の判定で使う)
        edge = (a, b)
        self._window_be3_edges.add(edge)
        self._window_be3_adj[a].add(b)
        self._window_be3_adj[b].add(a)

        return new_ids

    # ----------------------------------------------------------------
    # 新規誕生 / 既存更新
    # ----------------------------------------------------------------
    def _maybe_birth(
        self, *,
        members: frozenset[int],
        trigger_type: str,
        window: int,
        step: int,
        global_step: int,
        cog: Any,
        ledger: Any,
    ) -> int | None:
        """同 member_cids の active Integration が既存なら binding 更新のみ。
        なければ新規誕生。

        Returns:
            新規誕生した integration_id、または None (既存更新時)
        """
        if len(members) < 2:
            return None  # 防御: 単独 cid の Integration は無効

        # §3.2 重複判定: 同 member の active が既存か?
        existing_id = self._active_members_index.get(members)
        if existing_id is not None:
            integ = self.integrations[existing_id]
            # binding_strengths を更新 (event 参加回数 +1)
            for cid in members:
                integ.binding_strengths[cid] = (
                    integ.binding_strengths.get(cid, 0.0) + 1.0)
                integ.member_history.add(cid)
            return None

        # 新規誕生
        iid = self._next_id
        self._next_id += 1
        member_set = set(int(c) for c in members)
        binding_strengths = {cid: 1.0 for cid in member_set}
        integ = Integration(
            integration_id=iid,
            birth_step=int(global_step),
            trigger_type=trigger_type,
            state="active",
            member_cids=member_set,
            member_history=set(member_set),
            Q_inherited=0,
            C_inherited=0,
            binding_strengths=binding_strengths,
        )
        self.integrations[iid] = integ
        self._active_members_index[frozenset(member_set)] = iid
        for cid in member_set:
            self.cid_to_integrations[cid].add(iid)
            self.cid_n_integrations_joined[cid] += 1

        # §11: Integration 構成 cid を target に追加
        if self._target_tracker is not None:
            for cid in member_set:
                self._target_tracker.stage4_integration_member(
                    cid, int(global_step))

        # 集計
        self._window_n_born += 1
        self._window_trigger_counter[trigger_type] += 1

        # lifecycle log
        q_total = self._compute_q_total(integ, cog, ledger)
        c_total = self._compute_c_total(integ, cog)
        self.lifecycle_log.append({
            "seed": self.seed,
            "step": int(global_step),
            "integration_id": iid,
            "event_type": "birth",
            "trigger_type": trigger_type,
            "member_cids": "|".join(str(c) for c in sorted(member_set)),
            "q_total": int(q_total),
            "c_total": int(c_total),
            "q_inherited_delta": 0,
            "c_inherited_delta": 0,
        })

        return iid

    # ----------------------------------------------------------------
    # ghost 化時 Q/C 継承 (§5)
    # ----------------------------------------------------------------
    def on_ghost(
        self, *,
        cid: int,
        q_at_ghost: int,
        c_at_ghost: int,
        global_step: int,
        cog: Any,
        ledger: Any,
    ) -> None:
        """cid X が ghost 化した直後 (detach 完了後、reap 前) に呼ぶ。

        §5.1 処理順:
          2. X が所属する Integration リストを取得
          3. 最強結合 Integration I* を特定
          4. X.Q を I*.Q_inherited に加算
          5. X.C を I*.C_inherited に加算
          6. I* の member_cids から X を除外、member_history に追加
          7. 他の Integration の member_cids からも X を除外、member_history に追加
          8. I* の member_cids が empty になったら state = "recorded"
        """
        cid = int(cid)
        joined_ids = list(self.cid_to_integrations.get(cid, ()))
        if not joined_ids:
            return  # cid は Integration に未所属、何もしない

        # 最強結合 I* を特定 (binding_strength 最大、tie は integration_id 最小)
        def _strength(iid: int) -> tuple[float, int]:
            integ = self.integrations[iid]
            return (-float(integ.binding_strengths.get(cid, 0.0)), iid)

        joined_ids_sorted = sorted(joined_ids, key=_strength)
        strongest_iid = joined_ids_sorted[0]
        strongest = self.integrations[strongest_iid]

        # I* に Q/C を加算
        strongest.Q_inherited += int(q_at_ghost)
        strongest.C_inherited += int(c_at_ghost)
        self._window_total_q_inherited += int(q_at_ghost)
        self._window_total_c_inherited += int(c_at_ghost)

        # cid_to_integration の per_subject 集計
        self.cid_q_inherited_to_integration[cid] += int(q_at_ghost)
        self.cid_c_inherited_to_integration[cid] += int(c_at_ghost)

        # I* の member_cids から X を除外
        # (active_members_index も更新)
        for iid in joined_ids:
            integ = self.integrations[iid]
            old_members = frozenset(integ.member_cids)
            if cid in integ.member_cids:
                integ.member_cids.discard(cid)
                integ.member_history.add(cid)
                # active_members_index 更新
                if old_members in self._active_members_index:
                    if self._active_members_index[old_members] == iid:
                        del self._active_members_index[old_members]
                if integ.state == "active" and integ.member_cids:
                    new_members = frozenset(integ.member_cids)
                    # 既に同じ members を持つ active があるかチェック
                    # (空白を回避するため index には書き込まない可能性あり)
                    if new_members not in self._active_members_index:
                        self._active_members_index[new_members] = iid

        # cid_to_integrations から cid を完全削除
        self.cid_to_integrations.pop(cid, None)

        # I* の member_cids が empty になったら state = "recorded"
        # (他の Integration も同様にチェック — 必須)
        for iid in joined_ids:
            integ = self.integrations[iid]
            if integ.state == "active" and not integ.member_cids:
                integ.state = "recorded"
                integ.became_recorded_step = int(global_step)
                self._window_n_state_transitioned += 1
                # active_members_index から除去 (空集合でないかも)
                # 注: 既に上のループで除去済の可能性
                # log
                self.lifecycle_log.append({
                    "seed": self.seed,
                    "step": int(global_step),
                    "integration_id": iid,
                    "event_type": "active_to_recorded",
                    "trigger_type": integ.trigger_type,
                    "member_cids": "",  # active members は空
                    "q_total": int(integ.Q_inherited),
                    "c_total": int(integ.C_inherited),
                    "q_inherited_delta": 0,
                    "c_inherited_delta": 0,
                })

        # member_ghosted log (I* + 他 active)
        for iid in joined_ids:
            integ = self.integrations[iid]
            event_subtype = (
                "q_inherited" if iid == strongest_iid else "member_ghosted")
            self.lifecycle_log.append({
                "seed": self.seed,
                "step": int(global_step),
                "integration_id": iid,
                "event_type": event_subtype,
                "trigger_type": integ.trigger_type,
                "member_cids": "|".join(
                    str(c) for c in sorted(integ.member_cids)),
                "q_total": int(self._compute_q_total(integ, cog, ledger)),
                "c_total": int(self._compute_c_total(integ, cog)),
                "q_inherited_delta":
                    int(q_at_ghost) if iid == strongest_iid else 0,
                "c_inherited_delta":
                    int(c_at_ghost) if iid == strongest_iid else 0,
            })

    # ----------------------------------------------------------------
    # window 末 Q/C 再分配 (§6)
    # ----------------------------------------------------------------
    def redistribute_q_c(
        self, *,
        window: int,
        global_step: int,
        cog: Any,
        ledger: Any,
        shadow_audit: bool = False,
    ) -> None:
        """window 末で active Integration の Q_inherited/C_inherited を
        active member_cids の不足側に分配する。

        §6.2 簡潔な逆張り分配:
          意識優位 cid (q_ratio < 0.5): Q を多めに分配
          認知優位 cid (q_ratio > 0.5): C を多めに分配

        shadow_audit=True のとき、log は記録するが実分配は行わない。
        """
        for iid, integ in list(self.integrations.items()):
            if integ.state != "active":
                continue
            if integ.Q_inherited == 0 and integ.C_inherited == 0:
                continue
            active_members = sorted(int(c) for c in integ.member_cids
                                    if cog.is_hosted(c))
            if not active_members:
                continue

            total_q = int(integ.Q_inherited)
            total_c = int(integ.C_inherited)

            # 各 cid の不足度 (q_ratio = Q/(Q+C))
            shortage_q: list[float] = []
            shortage_c: list[float] = []
            q_ratios_before: list[float] = []
            for cid in active_members:
                ledger_entry = ledger.ledger.get(cid)
                q_val = int(ledger_entry["v14_q_remaining"]) \
                    if ledger_entry is not None else 0
                c_val = int(cog.C.get(cid, 0))
                denom = q_val + c_val + 1e-9
                q_ratio = q_val / denom
                q_ratios_before.append(q_ratio)
                if q_ratio < 0.5:
                    shortage_q.append(0.5 - q_ratio)
                    shortage_c.append(0.0)
                else:
                    shortage_q.append(0.0)
                    shortage_c.append(q_ratio - 0.5)

            sum_sq = sum(shortage_q) + 1e-9
            sum_sc = sum(shortage_c) + 1e-9

            # 各 cid に分配
            actual_dist_q = 0
            actual_dist_c = 0
            for i, cid in enumerate(active_members):
                q_alloc = int(total_q * shortage_q[i] / sum_sq)
                c_alloc = int(total_c * shortage_c[i] / sum_sc)
                if q_alloc == 0 and c_alloc == 0:
                    continue

                # 適用前の状態 (log 用)
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

                self.cid_q_received_from_integrations[cid] += q_alloc
                self.cid_c_received_from_integrations[cid] += c_alloc

                self.distribution_log.append({
                    "seed": self.seed,
                    "step": int(global_step),
                    "integration_id": iid,
                    "target_cid": int(cid),
                    "q_distributed": int(q_alloc),
                    "c_distributed": int(c_alloc),
                    "target_q_ratio_before": round(ratio_before, 6),
                    "target_q_ratio_after": round(ratio_after, 6),
                })

            # 在庫を消費 (shadow audit でも消費する: 観察として再分配の挙動を見るため)
            integ.Q_inherited = 0
            integ.C_inherited = 0
            self._window_total_q_distributed += actual_dist_q
            self._window_total_c_distributed += actual_dist_c

    # ----------------------------------------------------------------
    # 補助: Q_total / C_total 動的計算 (logger 用)
    # ----------------------------------------------------------------
    def _compute_q_total(self, integ: Integration, cog: Any, ledger: Any) -> int:
        total = int(integ.Q_inherited)
        for cid in integ.member_cids:
            entry = ledger.ledger.get(cid)
            if entry is not None:
                total += int(entry["v14_q_remaining"])
        return total

    def _compute_c_total(self, integ: Integration, cog: Any) -> int:
        total = int(integ.C_inherited)
        for cid in integ.member_cids:
            total += int(cog.C.get(cid, 0))
        return total

    # ----------------------------------------------------------------
    # observation target 拡張 (§11): Integration 構成 cid を target に追加
    # ----------------------------------------------------------------
    def all_member_cids(self) -> set[int]:
        """全 Integration の構成 cid (active + history) の和集合。"""
        out: set[int] = set()
        for integ in self.integrations.values():
            out.update(integ.member_history)
        return out

    # ----------------------------------------------------------------
    # 出力: membership snapshot (run 末に 1 回)
    # ----------------------------------------------------------------
    def get_membership_snapshot_rows(self, current_step: int) -> list[dict]:
        rows = []
        # cid ごとに、所属している Integration 一覧 (active のみ)
        cid_to_active: dict[int, list[int]] = defaultdict(list)
        for iid, integ in self.integrations.items():
            if integ.state != "active":
                continue
            for cid in integ.member_cids:
                cid_to_active[cid].append(iid)
        for cid, iids in cid_to_active.items():
            iids_sorted = sorted(iids)
            strengths = []
            for iid in iids_sorted:
                strengths.append(
                    f"{iid}:{self.integrations[iid].binding_strengths.get(cid, 0.0):.1f}"
                )
            rows.append({
                "seed": self.seed,
                "step": int(current_step),
                "cid_id": int(cid),
                "integration_ids": "|".join(str(i) for i in iids_sorted),
                "binding_strengths": "|".join(strengths),
            })
        return rows
