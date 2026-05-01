#!/usr/bin/env python3
"""
ESDE v10.3 — Spend Audit Ledger (Layer B + 双方向 E3)
=====================================================
v9.14 を fork、v10.3 双方向 E3 機構を E3 detect 後 + balance loop 前に挿入。

v10.3 拡張 (実装指示書 §2-§3):
  - 既存 E3 onset の new_e3_pairs を走査
  - 各 pair について: 両者 hosted ∧ Q>0 ∧ C≥1 を確認
  - 条件満たせば bidirectional_e3_log に記録 + 両者 C-1
  - 条件満たさなければ skip 記録 (skip_reason)
  - shadow_audit モード: log のみ、C 減算なし
  - ObservationTargetTracker と連携、Stage 1/2 で動的絞り込み

(以下、v914 オリジナル文書)
方針 (v914_implementation_instructions.md §5):
  - audit-only。Layer A (既存 50-step 固定 pulse) の state は read-only でのみ参照
  - engine.state / engine.rng / capture_rng への mutation は一切行わない
  - Layer B は RNG を使わない (全て決定論的)
  - 書き込みは self.ledger / self.events のみ。baseline CSV には 1 列も追加しない

cid 単位 ledger のスキーマ (v914_implementation_instructions.md §7):
  ledger[cid] = {
      "v14_q0":                    int,   # 初期原資 = floor(B_Gen)
      "v14_q_remaining":           int,   # 残存原資 (Q>0 のときのみ spend)
      "v14_virtual_attention":     dict,  # Layer B 専用 attention map (node -> weight)
      "v14_virtual_familiarity":   dict,  # Layer B 専用 familiarity map (other_cid -> weight)
      "v14_last_snapshot":         dict,  # 前回 spend 時の E_t snapshot (None = 未 spend)
      "v14_shadow_pulse_index":    int,   # Layer B 上の pulse 連番 (spend 成立のたびに +1)
      "v14_prev_member_alive_links": frozenset,  # E1 検知用
      "v14_prev_member_r":         dict,  # E2 検知用 (Step 4〜)
      "member_nodes":              frozenset,  # 登録時の member node 集合 (固定)
      "registered_at":             (window, step),
      "v14_last_event_global_step": int | None,  # post_event_gap 計算用
  }

Spend packet (Step 3〜):
  event 発生時 (E1/E2/E3) に以下を実行:
    1. 現 E_t と reference (前回 snapshot、または初回は M_c) の差分 Δ を算出
    2. Q_remaining > 0 なら:
       - virtual_attention[node] += 1 (node は struct_set - core)
       - virtual_familiarity[other_cid] += 1 (struct_set 経由で接触した cid)
       - Q_remaining -= 1
       - last_snapshot = 現 E_t, shadow_pulse_index += 1
    3. event ごとに 1 行 audit record を self.events に append

Virtual layer の更新は +1/event のシンプルな方針 (Layer A の update_attention /
update_familiarity と同じ加算量)。Layer B では per-step 自動 decay は行わない
(event-driven で審議するため)。差分 Δ は記録のみで、update 量には使わない。

Step 3 時点: E1 (core link death/birth) 発生時に spend packet を実行。
E2 (Step 4) / E3 (Step 5) は後続 Step で追加。
"""

from __future__ import annotations

import math
from typing import Any

from v914_event_emitter import (
    compute_member_alive_links,
    detect_e1_events,
    compute_member_r,
    detect_e2_events,
    detect_e3_new_pairs,
)


# ────────────────────────────────────────────────────────────────────
# v10.2 Probabilistic Cognitive-Conscious Balance: 確率決定関数
# ────────────────────────────────────────────────────────────────────

def decide_balance(*, cognition_candidate: bool,
                   consciousness_candidate: bool,
                   Q: int, C: int, balance_rng) -> str:
    """E3 onset の認知 / 意識の振り分けを決める。

    判定順序 (条件因子チェック先行、§3.4):
      1. 両方候補なし → "skip"
      2. 片方のみ候補 → その側に確定 (RNG draw なし)
      3. 両方候補     → 確率決定 P(認知) = Q / (Q+C)

    Q=0 / C=0 の特殊扱い (主題 §3.1 D):
      cognition_candidate は呼び出し側が Q>0 を含めて判定して渡す前提。
      Q=0 のときは cognition_candidate=False で渡される。
      C=0 ∧ ghost residual_Q>0 の場合、consciousness_candidate=True だが
      C=0 なので意識行動はできない → ここで "skip" 扱いにする。

    神の手回避 (§3.1 D 注): ε > 0 を加える方法は採用しない。
    """
    # Q=0 のとき cognition_candidate は False で渡される (Q>0 が前提条件)
    # C=0 のとき意識発動不可なので consciousness_candidate を実効的に False に
    if not cognition_candidate and not consciousness_candidate:
        return "skip"
    if consciousness_candidate and C <= 0:
        # 意識候補だが C=0 → 意識行動できない
        if cognition_candidate:
            return "cognition"
        return "skip"
    if cognition_candidate and not consciousness_candidate:
        return "cognition"
    if consciousness_candidate and not cognition_candidate:
        return "consciousness"

    # 両方候補: 確率決定 P(認知) = Q/(Q+C)
    total = Q + C
    if total <= 0:
        # 念のため (cognition_candidate=True なら Q>0 が保証されるはず)
        return "skip"

    p_cognition = Q / total
    if balance_rng.random() < p_cognition:
        return "cognition"
    return "consciousness"


class SpendAuditLedger:
    """cid 単位で仮想原資 Q と virtual attention / familiarity を保持する audit-only ledger。

    Layer A の state を一切書き換えない。全ての書き込みは self.ledger と
    self.events (audit event list) に閉じる。

    外部の delta 計算ヘルパ (v11_compute_delta, ref 変換) は本体から注入する
    (observe_step の引数 delta_fn)。これにより v911 定数 / 関数への直接依存を
    本モジュール内に持たせず、疎結合を保つ。
    """

    def __init__(self, delta_fn=None, disable_e3: bool = False,
                 cog=None, ingestion_rng=None, balance_rng=None,
                 # v10.3 双方向 E3 拡張
                 be3_target_tracker=None,
                 be3_shadow_audit: bool = False,
                 be3_disable: bool = False,
                 # v10.4 Integration 拡張
                 be3_fired_callback=None) -> None:
        """delta_fn(ref_m_c_like, e_t) -> (delta_total, axes_dict)。

        ref_m_c_like は {"n_core", "s_avg", "r_core", "phase_sig"} を持つ dict。
        e_t は {"n_local", "s_avg_local", "r_local", "theta_avg_local"} を持つ dict。
        本体から v11_compute_delta を差し込んで使う。

        disable_e3=True のとき E3_contact の event 発行を skip する (§6.4
        ablation)。contacted_pairs への登録は継続 (再現性維持)。E1/E2 の
        検知・spend は変更なし。Layer A state は読み取り専用のまま。

        v10.1 Minimal Ingestion:
          cog: SubjectLayer 参照 (None なら ingestion 無効、後方互換)。
            E3 検知時に cog.attempt_ingestion / cog.is_ghost を呼ぶ。
          ingestion_rng: numpy.random.Generator (1 CID : 多 ghost のランダム選定用)。
            None なら ingestion 無効。bit-identity 維持のため独立 stream
            (engine.rng / capture_rng とは分離、慣例 seed ^ MAGIC)。

        v10.2 Probabilistic Cognitive-Conscious Balance:
          balance_rng: numpy.random.Generator (E3 onset 確率決定用)。
            None なら確率機構が無効化され v10.1 互換の機械発動になる
            (テスト用後方互換)。本番ではかならず balance_rng を渡す。
        """
        self.ledger: dict[Any, dict[str, Any]] = {}
        # audit event list (Step 6 で per_event_audit.csv に書き出される)
        self.events: list[dict[str, Any]] = []
        self._delta_fn = delta_fn
        self._disable_e3 = bool(disable_e3)
        # E3 contact 検出用: 登録済み cid の member nodes から構築する
        # node -> set of cids 逆引き。cid 登録時に add、cid retire 時は残す
        # (member_nodes は soul で不変、一度発生した contact pair も不変記録)。
        self._node_to_cids: dict[Any, set] = {}
        # 既に記録した E3 contact ペア (frozenset({cid_a, cid_b}))
        self._contacted_pairs: set = set()
        # v10.1 Minimal Ingestion
        self._cog = cog
        self._ingestion_rng = ingestion_rng
        # ingestion phase で使うステージング用ペアバッファ。
        # v10.1 では observe_step 中の E3 onset で (hosted_a, ghost_b, link_id) を集めて、
        # 同じ observe_step 末尾で 1 CID あたり 1 ghost を選定して摂食する設計。
        # v10.2 即時摂食 (案 B) では使わないが、後方互換のため残す。
        self._pending_ingestion_pairs: list = []
        # ingestion event log (raw)。flush 時に CSV 出力。
        self.ingestion_events: list[dict[str, Any]] = []
        # phantom contact log: cog で既に reap 済の ghost への E3 onset
        self.phantom_contacts: list[dict[str, Any]] = []

        # v10.2 Probabilistic Balance
        self._balance_rng = balance_rng
        # 確率決定の raw マスター (per_event_audit / ingestion_events は補助)
        # 各 E3 onset の観察者視点 1 行ずつ (= pair あたり 2 行)。skip 行も含む。
        self.balance_decisions: list[dict[str, Any]] = []

        # v10.3 双方向 E3 拡張
        self._be3_target_tracker = be3_target_tracker  # ObservationTargetTracker
        self._be3_shadow_audit = bool(be3_shadow_audit)  # True: log のみ
        self._be3_disable = bool(be3_disable)  # True: be3 一切走らない (debug 用)
        # bidirectional_e3_log エントリ (skip 含む全 pair)
        self.bidirectional_e3_events: list[dict[str, Any]] = []
        # bidirectional_e3_member_nodes_log エントリ (発火時のみ)
        self.bidirectional_e3_member_nodes: list[dict[str, Any]] = []
        # 集計用: window 内 be3 発火数 (target 内/外)
        self._be3_count_target_inner = 0
        self._be3_count_target_outer = 0
        # per_subject 蓄積用: cid -> {n_be3_total, partners (set), repeated}
        self._be3_per_cid: dict = {}  # cid -> {"n_be3", "partners": dict, "c_spent"}
        # v10.2 balance_decision の consciousness 当選数 (Stage 1 判定用)
        # 双方向 E3 phase より前 (= 過去 step での累積) を参照する
        self._n_consciousness_per_cid: dict = {}  # cid -> int

        # v10.4 Integration: be3 fired 直後に呼ぶ callback
        # signature: callback(cid_a, cid_b, window, step, global_step,
        #                     cog, ledger=self) -> None
        # shadow_audit 中でも fired ペアごとに呼ぶ (Integration 機構の挙動を観察)
        self._be3_fired_callback = be3_fired_callback

    # ----------------------------------------------------------------
    # observe_step: 各 tracking step の Layer A 処理完了後に呼ぶ
    # ----------------------------------------------------------------

    def observe_step(self, *, window: int, step: int, global_step: int,
                     alive_l_set: set, state_r: dict,
                     cid_ctx: dict) -> None:
        """各 step で event 検知 + spend packet を実行し、self.events に append。

        Args:
            window: 現在の tracking window index
            step: window 内 step index (0-based)
            global_step: tracking 全体で連続する step 番号 (post_event_gap 用)
            alive_l_set: engine.state.alive_l (set of (min,max) tuples)
            cid_ctx: dict cid -> {
                "b_gen": float,  # cog.v11_b_gen[cid]
                "member_nodes": frozenset,  # label["nodes"] at current lid
                "e_t": dict,  # v11_compute_e_t(...) の結果
                "m_c": dict,  # cog.v11_m_c[cid]
                "attn_nodes": frozenset,  # struct_set - core (virtual_attention 更新対象)
                "other_cids": frozenset,  # struct_set 経由で接触した他 cid
            }
        """
        for cid, ctx in cid_ctx.items():
            b_gen = ctx.get("b_gen", float("inf"))
            if not math.isfinite(b_gen) or b_gen <= 0:
                continue
            member_nodes = ctx.get("member_nodes")
            if member_nodes is None or len(member_nodes) < 2:
                continue

            entry = self.ledger.get(cid)

            if entry is None:
                # Lazy registration: 初回観測時に member_nodes を固定、
                # 現在の alive member links を prev として snapshot。
                # この step では event 発行しない。
                curr_alive = compute_member_alive_links(
                    member_nodes, alive_l_set)
                self.ledger[cid] = {
                    "v14_q0": int(math.floor(b_gen)),
                    "v14_q_remaining": int(math.floor(b_gen)),
                    "v14_virtual_attention": {},
                    "v14_virtual_familiarity": {},
                    "v14_last_snapshot": None,
                    "v14_shadow_pulse_index": 0,
                    "v14_prev_member_alive_links": curr_alive,
                    "v14_prev_member_r": {},
                    "member_nodes": frozenset(member_nodes),
                    "registered_at": (window, step),
                    "v14_last_event_global_step": None,
                }
                # E3 のための逆引き更新: 各 member node に cid を登録
                for _n in member_nodes:
                    self._node_to_cids.setdefault(_n, set()).add(cid)
                continue

            # 使い回し: 登録時 member_nodes を固定で使う (ctx の可変性から切り離す)
            curr_alive = compute_member_alive_links(
                entry["member_nodes"], alive_l_set)
            curr_r = compute_member_r(
                entry["member_nodes"], state_r, alive_l_set)

            # E1 + E2 detection
            e1 = detect_e1_events(
                entry["v14_prev_member_alive_links"], curr_alive)
            e2 = detect_e2_events(
                entry["v14_prev_member_r"], curr_r)

            # 1 step 内の全 event に対して delta は同じ E_t を使うが、
            # reference は spend のたびに更新される (last_snapshot が更新される)。
            # 方針: event 順 (E1 → E2) に処理、各 event で最新の last_snapshot を
            # 参照として delta 計算。最初の spend 後は reference==E_t になり、
            # 同 step 内の後続 event は delta==0 になる (定義通り)。
            for (etype, lk) in e1:
                self._process_event(
                    cid=cid, entry=entry, ctx=ctx,
                    event_type=etype,
                    link_id=f"({lk[0]},{lk[1]})",
                    window=window, step=step,
                    global_step=global_step,
                )
            for (etype, lk) in e2:
                self._process_event(
                    cid=cid, entry=entry, ctx=ctx,
                    event_type=etype,
                    link_id=f"({lk[0]},{lk[1]})",
                    window=window, step=step,
                    global_step=global_step,
                )

            entry["v14_prev_member_alive_links"] = curr_alive
            entry["v14_prev_member_r"] = curr_r

        # E3: step レベルの検出 (全 alive link を node_to_cids で引く)。
        # per-cid ループの後で 1 回だけ実行。
        # disable_e3=True でも detect は呼ぶ (contacted_pairs 登録維持)。
        # event 発行のみ skip する (§6.4 ablation 仕様)。
        new_e3_pairs = detect_e3_new_pairs(
            alive_l_set, self._node_to_cids, self._contacted_pairs)
        if self._disable_e3:
            return

        # ═══════════════════════════════════════════════════════════════
        # v10.3 双方向 E3 phase (実装指示書 §3 step 4)
        # 既存 E3 detect 直後、balance_decision より前に処理する。
        # → C 状態の更新が balance_rng の確率計算に反映される (shadow audit
        #    では C を変えないので balance は v10.2 と一致するはず)。
        # ═══════════════════════════════════════════════════════════════
        if not self._be3_disable:
            self._process_bidirectional_e3(
                new_e3_pairs=new_e3_pairs,
                cid_ctx=cid_ctx,
                window=window, step=step, global_step=global_step,
            )

        # v10.2 Probabilistic Cognitive-Conscious Balance:
        #   Pair の処理順 (cid_a < cid_b) で順次確率決定 + 即時摂食 (案 B)。
        #   step 内で先行 cid の確率決定結果が後続 cid の候補集合を動的に
        #   変える (主題 §3.1 F の動的連鎖)。
        #
        # 処理フロー (各観察者視点 = pair あたり 2 視点):
        #   1. 候補集合判定 (条件因子チェック先行)
        #      - cognition_candidate = (Q_observer > 0)
        #      - consciousness_candidate = (相手 ghost で residual_Q > 0)
        #   2. decide_balance(Q, C, candidates, balance_rng)
        #   3a. cognition: _process_event (E3 spend) + cog.C[obs] += 1
        #   3b. consciousness: cog.C[obs] -= 1 + 即時 attempt_ingestion
        #       + audit 行を spend_flag=False で append (last_event_global_step
        #         のみ更新、shadow_pulse_index は不変)
        #   3c. skip: balance_decisions のみ記録 (audit 行も append しない)
        #
        # balance_rng が None (= v10.1 互換モード) の場合は機械発動 fallback。

        # v10.2 fallback: balance_rng が None なら v10.1 互換 (機械発動)
        if self._balance_rng is None:
            self._observe_step_v101_compat(
                new_e3_pairs, cid_ctx,
                window=window, step=step, global_step=global_step,
            )
            return

        for (cid_a, cid_b, lk) in new_e3_pairs:
            # 各 cid 視点で順次処理 (計 2 視点/pair)。
            # ペア処理順 = detect_e3_new_pairs の戻り順 (sorted 済、§I 修正)
            for observer_cid, contacted_cid in (
                    (cid_a, cid_b), (cid_b, cid_a)):
                ob_entry = self.ledger.get(observer_cid)
                ob_ctx = cid_ctx.get(observer_cid)
                if ob_entry is None or ob_ctx is None:
                    # observer は hosted ではない (ghost 側、または登録前)
                    continue

                # 候補集合判定 (条件因子チェック先行、§3.4)
                _is_ghost_b = self._cog.is_ghost(contacted_cid)
                _is_reaped_b = (
                    not _is_ghost_b
                    and not self._cog.is_hosted(contacted_cid)
                    and contacted_cid in self.ledger
                )
                # 意識候補: 相手 ghost (active) で residual_Q > 0 のときのみ
                # phantom (reaped) は意識候補から除外 (主題 §3.1 C)
                residual_b = (
                    int(self._cog.ghost_residual_Q.get(contacted_cid, 0))
                    if _is_ghost_b else 0
                )
                consciousness_candidate = bool(
                    _is_ghost_b and residual_b > 0)
                # 認知候補: Q > 0 (E3 spend 可能)
                Q_obs = int(ob_entry["v14_q_remaining"])
                C_obs = int(self._cog.C.get(observer_cid, 0))
                cognition_candidate = bool(Q_obs > 0)

                decision = decide_balance(
                    cognition_candidate=cognition_candidate,
                    consciousness_candidate=consciousness_candidate,
                    Q=Q_obs, C=C_obs,
                    balance_rng=self._balance_rng,
                )

                # 確率決定の raw マスター (§5.1.1、§H balance_decisions = master)
                p_cog = (Q_obs / (Q_obs + C_obs)
                         if (cognition_candidate
                             and consciousness_candidate
                             and (Q_obs + C_obs) > 0)
                         else "")
                self.balance_decisions.append({
                    "window": window,
                    "step": step,
                    "global_step": global_step,
                    "observer_cid": observer_cid,
                    "contacted_cid": contacted_cid,
                    "is_ghost": bool(_is_ghost_b),
                    "is_phantom": bool(_is_reaped_b),
                    "residual_Q_at_decision": residual_b,
                    "Q_at_decision": Q_obs,
                    "C_at_decision": C_obs,
                    "cognition_candidate": cognition_candidate,
                    "consciousness_candidate": consciousness_candidate,
                    "P_cognition": p_cog,
                    "decision": decision,
                    # action_taken / 後続更新は分岐内で確定
                })
                _decision_idx = len(self.balance_decisions) - 1

                if decision == "cognition":
                    # 既存 E3 spend (Q-1 + virtual_*) を起動 + C+1
                    self._process_event(
                        cid=observer_cid, entry=ob_entry, ctx=ob_ctx,
                        event_type="E3_contact",
                        link_id=f"cid{contacted_cid}|({lk[0]},{lk[1]})",
                        window=window, step=step,
                        global_step=global_step,
                    )
                    self._cog.C[observer_cid] = C_obs + 1
                    self.balance_decisions[_decision_idx][
                        "action_taken"] = "spend"

                elif decision == "consciousness":
                    # 意識発火: E3 spend は走らない (Q 不変、virtual_* 不変)
                    # C-1 + 即時摂食 (主題 §3.1 F 動的連鎖を成立させるため)
                    self._cog.C[observer_cid] = C_obs - 1
                    # v10.3: Stage 1 判定用の consciousness 当選数 counter
                    self._n_consciousness_per_cid[int(observer_cid)] = (
                        self._n_consciousness_per_cid.get(int(observer_cid), 0)
                        + 1
                    )

                    # 即時 attempt_ingestion (案 B、§B 事前齟齬指摘)
                    # 候補は contacted_cid の単一 (pair 単位で完結)
                    result = self._cog.attempt_ingestion(
                        observer_cid=observer_cid,
                        ghost_cid=contacted_cid,
                        ledger=self,
                    )
                    if result is None:
                        # 残候補が居ない: phantom 化
                        self.phantom_contacts.append({
                            "window": window,
                            "step": step,
                            "global_step": global_step,
                            "observer_cid": observer_cid,
                            "ghost_cid": contacted_cid,
                            "link_id": f"({lk[0]},{lk[1]})",
                            "n_other_candidates": 0,
                        })
                        self.balance_decisions[_decision_idx][
                            "action_taken"] = "ingestion_phantom"
                    else:
                        self.ingestion_events.append({
                            "window": window,
                            "step": step,
                            "global_step": global_step,
                            "observer_cid": observer_cid,
                            "ghost_cid": contacted_cid,
                            "link_id": f"({lk[0]},{lk[1]})",
                            "n_candidates": 1,
                            "gain": result["gain"],
                            "received": result["received"],
                            "digested": result["digested"],
                            "was_empty": result["was_empty"],
                            "residual_Q_before": result["residual_Q_before"],
                            "residual_Q_after": result["residual_Q_after"],
                            "q_remaining_before":
                                result["q_remaining_before"],
                            "q_remaining_after":
                                result["q_remaining_after"],
                        })
                        self.balance_decisions[_decision_idx][
                            "action_taken"] = "ingestion"

                    # 案 Y (§C): 意識発火も per_event_audit に E3 行を残す。
                    # spend_flag=False, attention_delta=0, familiarity_delta=0、
                    # last_event_global_step は更新、shadow_pulse_index は不変
                    last_gs = ob_entry.get("v14_last_event_global_step")
                    post_event_gap = (
                        global_step - last_gs if last_gs is not None else -1)
                    ob_entry["v14_last_event_global_step"] = global_step
                    self.events.append({
                        "cid": observer_cid,
                        "seed_placeholder": None,
                        "window": window,
                        "step": step,
                        "global_step": global_step,
                        "v14_event_type": "E3_contact",
                        "link_id":
                            f"cid{contacted_cid}|({lk[0]},{lk[1]})",
                        "v14_q0": ob_entry["v14_q0"],
                        "v14_q_remaining": ob_entry["v14_q_remaining"],
                        "v14_spend_flag": False,
                        "v14_delta_norm": 0.0,
                        "v14_attention_delta": 0.0,
                        "v14_familiarity_delta": 0.0,
                        "v14_post_event_gap": int(post_event_gap),
                        "v14_shadow_pulse_index":
                            ob_entry["v14_shadow_pulse_index"],
                    })
                    # Q_at_decision は decision 時点の値、q_remaining_after は
                    # 摂食後の値を後付けで balance_decisions に追記
                    self.balance_decisions[_decision_idx][
                        "q_remaining_after"] = int(
                            ob_entry["v14_q_remaining"])
                    self.balance_decisions[_decision_idx][
                        "c_after"] = int(self._cog.C[observer_cid])
                    continue  # consciousness 処理完了

                else:  # decision == "skip"
                    # Q=0 ∧ C=0 (両候補なし)、または条件因子なし
                    self.balance_decisions[_decision_idx][
                        "action_taken"] = "none"
                    self.balance_decisions[_decision_idx][
                        "q_remaining_after"] = Q_obs
                    self.balance_decisions[_decision_idx][
                        "c_after"] = C_obs
                    continue

                # cognition 後の状態を balance_decisions に追記
                self.balance_decisions[_decision_idx][
                    "q_remaining_after"] = int(ob_entry["v14_q_remaining"])
                self.balance_decisions[_decision_idx][
                    "c_after"] = int(self._cog.C[observer_cid])

    # ----------------------------------------------------------------
    # v10.3 双方向 E3 処理
    # ----------------------------------------------------------------
    def _process_bidirectional_e3(
        self, *, new_e3_pairs, cid_ctx,
        window: int, step: int, global_step: int,
    ) -> None:
        """E3 onset 直後、balance_decision 前に呼ぶ。

        実装指示書 §2 (発火条件):
          両者 hosted ∧ Q>0 ∧ C ≥ 1 で発火、両者 C-1
          条件不満は skip 記録 (skip_reason)
          shadow_audit モード: C は減らさず log のみ
        """
        if self._cog is None:
            return  # cog 不在では発火判定不可

        for (cid_a, cid_b, lk) in new_e3_pairs:
            # 並び固定 (cid_a < cid_b、detect_e3_new_pairs で sorted 済)
            assert cid_a < cid_b, f"new_e3_pairs not sorted: {cid_a},{cid_b}"

            link_id_str = f"({lk[0]},{lk[1]})"

            # 状態取得
            entry_a = self.ledger.get(cid_a)
            entry_b = self.ledger.get(cid_b)
            ctx_a = cid_ctx.get(cid_a)
            ctx_b = cid_ctx.get(cid_b)

            # 両者 hosted 条件: ledger と ctx の両方が必要 + cog.is_hosted
            hosted_a = (
                entry_a is not None and ctx_a is not None
                and self._cog.is_hosted(cid_a)
            )
            hosted_b = (
                entry_b is not None and ctx_b is not None
                and self._cog.is_hosted(cid_b)
            )

            # 状態スナップショット (skip 含む全ペアで記録)
            q_a = int(entry_a["v14_q_remaining"]) if entry_a else 0
            q_b = int(entry_b["v14_q_remaining"]) if entry_b else 0
            c_a = int(self._cog.C.get(cid_a, 0))
            c_b = int(self._cog.C.get(cid_b, 0))
            age_a = int(entry_a.get("v14_shadow_pulse_index", 0)) if entry_a else 0
            age_b = int(entry_b.get("v14_shadow_pulse_index", 0)) if entry_b else 0

            # M_c 取得 (shaped from ctx; m_c = {n_core, s_avg, r_core, phase_sig})
            m_c_a = ctx_a.get("m_c") if ctx_a else None
            m_c_b = ctx_b.get("m_c") if ctx_b else None

            # skip 判定
            skip_reason = ""
            if not hosted_a:
                skip_reason = "ghost_a"
            elif not hosted_b:
                skip_reason = "ghost_b"
            elif q_a <= 0:
                skip_reason = "q_zero_a"
            elif q_b <= 0:
                skip_reason = "q_zero_b"
            elif c_a < 1:
                skip_reason = "c_zero_a"
            elif c_b < 1:
                skip_reason = "c_zero_b"

            fired = (skip_reason == "")

            # 観察対象判定: 主役条件 (Stage 1) + Stage 2 propagate
            target_inner = False
            if self._be3_target_tracker is not None and fired:
                # Stage 1: n_core ≥ 4 ∧ n_consciousness_decisions ≥ 5
                # n_consciousness は v10.2 balance_decision の累積カウンタを使う
                # (be3 phase より前の累積。同 step の balance loop はまだ未実行)
                n_consciousness_a = self._n_consciousness_per_cid.get(
                    int(cid_a), 0)
                n_consciousness_b = self._n_consciousness_per_cid.get(
                    int(cid_b), 0)
                n_core_a = m_c_a.get("n_core") if m_c_a else None
                n_core_b = m_c_b.get("n_core") if m_c_b else None

                self._be3_target_tracker.stage1_check(
                    cid_a, n_core_a, n_consciousness_a, global_step)
                self._be3_target_tracker.stage1_check(
                    cid_b, n_core_b, n_consciousness_b, global_step)

                # Stage 2: 片方 target なら相手も追加
                self._be3_target_tracker.stage2_propagate(
                    cid_a, cid_b, global_step)

                target_inner = self._be3_target_tracker.either_target(
                    cid_a, cid_b)

            # log 記録 (実装指示書 §4.3 通り):
            #   - shadow audit モード: 全件詳細記録 (= 検証目的、絞らない)
            #   - 本番モード + target tracker あり: target 内のみ詳細記録
            #   - target tracker なし: 全件詳細記録
            log_detail = (
                self._be3_shadow_audit  # shadow では絞らない
                or self._be3_target_tracker is None
                or target_inner
            )
            if log_detail:
                self.bidirectional_e3_events.append({
                    "window": window,
                    "step": step,
                    "global_step": global_step,
                    "cid_a": int(cid_a),
                    "cid_b": int(cid_b),
                    "ncore_a": (m_c_a.get("n_core") if m_c_a
                                else (len(entry_a["member_nodes"])
                                      if entry_a else 0)),
                    "ncore_b": (m_c_b.get("n_core") if m_c_b
                                else (len(entry_b["member_nodes"])
                                      if entry_b else 0)),
                    "phase_sig_a": (
                        round(float(m_c_a["phase_sig"]), 6) if m_c_a else ""),
                    "phase_sig_b": (
                        round(float(m_c_b["phase_sig"]), 6) if m_c_b else ""),
                    "s_avg_a": (
                        round(float(m_c_a["s_avg"]), 6) if m_c_a else ""),
                    "s_avg_b": (
                        round(float(m_c_b["s_avg"]), 6) if m_c_b else ""),
                    "r_core_a": (
                        round(float(m_c_a["r_core"]), 6) if m_c_a else ""),
                    "r_core_b": (
                        round(float(m_c_b["r_core"]), 6) if m_c_b else ""),
                    "q_a_before": q_a,
                    "q_b_before": q_b,
                    "c_a_before": c_a,
                    "c_b_before": c_b,
                    "age_a": age_a,
                    "age_b": age_b,
                    "link_id": link_id_str,
                    "fired": fired,
                    "skip_reason": skip_reason,
                    "shadow_audit": self._be3_shadow_audit,
                    "in_observation_target": target_inner,
                })

            # 集計カウンタ
            if fired:
                if target_inner:
                    self._be3_count_target_inner += 1
                else:
                    self._be3_count_target_outer += 1

                # per_cid 蓄積
                for cid_x, cid_partner in (
                        (cid_a, cid_b), (cid_b, cid_a)):
                    rec = self._be3_per_cid.setdefault(
                        int(cid_x),
                        {"n_be3": 0, "partners": {}, "c_spent": 0}
                    )
                    rec["n_be3"] += 1
                    p = rec["partners"]
                    p[int(cid_partner)] = p.get(int(cid_partner), 0) + 1
                    if not self._be3_shadow_audit:
                        rec["c_spent"] += 1

                # member_nodes log (詳細記録のときのみ)
                if log_detail:
                    mn_a = entry_a["member_nodes"] if entry_a else frozenset()
                    mn_b = entry_b["member_nodes"] if entry_b else frozenset()
                    self.bidirectional_e3_member_nodes.append({
                        "window": window,
                        "step": step,
                        "global_step": global_step,
                        "cid_a": int(cid_a),
                        "cid_b": int(cid_b),
                        "member_nodes_a": "|".join(
                            str(int(n)) for n in sorted(mn_a)),
                        "member_nodes_b": "|".join(
                            str(int(n)) for n in sorted(mn_b)),
                        "n_member_a": len(mn_a),
                        "n_member_b": len(mn_b),
                    })

                # C 消費 (shadow audit モードでない場合のみ)
                if not self._be3_shadow_audit:
                    self._cog.C[cid_a] = c_a - 1
                    self._cog.C[cid_b] = c_b - 1

                # v10.4 Integration: be3 fired callback (shadow audit でも呼ぶ)
                # Integration 誕生判定は C 消費の有無と独立に観察したい
                if self._be3_fired_callback is not None:
                    self._be3_fired_callback(
                        cid_a=int(cid_a), cid_b=int(cid_b),
                        window=window, step=step, global_step=global_step,
                        cog=self._cog, ledger=self,
                    )

    def _observe_step_v101_compat(
        self, new_e3_pairs, cid_ctx, *,
        window: int, step: int, global_step: int
    ) -> None:
        """v10.1 互換 fallback (balance_rng=None のとき)。

        v10.2 単体テストで balance 機構を無効化したいケース、
        または ablation 用に残す。本番では使わない。
        """
        ingest_candidates_per_observer: dict = {}

        for (cid_a, cid_b, lk) in new_e3_pairs:
            for observer_cid, contacted_cid in (
                    (cid_a, cid_b), (cid_b, cid_a)):
                ob_entry = self.ledger.get(observer_cid)
                ob_ctx = cid_ctx.get(observer_cid)
                if ob_entry is None or ob_ctx is None:
                    continue
                self._process_event(
                    cid=observer_cid, entry=ob_entry, ctx=ob_ctx,
                    event_type="E3_contact",
                    link_id=f"cid{contacted_cid}|({lk[0]},{lk[1]})",
                    window=window, step=step,
                    global_step=global_step,
                )

                if self._cog is not None:
                    _is_ghost_b = self._cog.is_ghost(contacted_cid)
                    _is_reaped_b = (
                        not _is_ghost_b
                        and not self._cog.is_hosted(contacted_cid)
                        and contacted_cid in self.ledger
                    )
                    if _is_ghost_b or _is_reaped_b:
                        ingest_candidates_per_observer.setdefault(
                            observer_cid, []
                        ).append((contacted_cid, f"({lk[0]},{lk[1]})"))

        if (self._cog is not None and self._ingestion_rng is not None
                and ingest_candidates_per_observer):
            self._run_ingestion_phase(
                ingest_candidates_per_observer,
                window=window, step=step, global_step=global_step,
            )

    def _run_ingestion_phase(self, candidates_per_observer: dict, *,
                              window: int, step: int,
                              global_step: int) -> None:
        """v10.1 Minimal Ingestion: 摂食 phase の本体。

        candidates_per_observer: observer_cid -> [(ghost_cid, link_id), ...]
        """
        for observer_cid in sorted(candidates_per_observer.keys()):
            cands = candidates_per_observer[observer_cid]
            if not cands:
                continue
            # seeded RNG で 1 candidate を選ぶ。candidates は cid_id でソートして
            # bit-identity を確保 (発生順序は detect_e3_new_pairs に依存するため、
            # ここで明示的にソートする)。
            cands_sorted = sorted(cands, key=lambda x: x[0])
            if len(cands_sorted) == 1:
                chosen_idx = 0
            else:
                chosen_idx = int(self._ingestion_rng.integers(
                    low=0, high=len(cands_sorted)))
            ghost_cid, link_id = cands_sorted[chosen_idx]

            # ingestion 試行。ghost が cog から消えていれば phantom log に。
            result = self._cog.attempt_ingestion(
                observer_cid=observer_cid,
                ghost_cid=ghost_cid,
                ledger=self,
            )
            if result is None:
                # phantom contact: cog 上で既に reap 済みの ghost
                self.phantom_contacts.append({
                    "window": window,
                    "step": step,
                    "global_step": global_step,
                    "observer_cid": observer_cid,
                    "ghost_cid": ghost_cid,
                    "link_id": link_id,
                    "n_other_candidates": len(cands_sorted) - 1,
                })
                continue

            # ingestion 成功 (gain == 0 で空摂食もここで記録)
            self.ingestion_events.append({
                "window": window,
                "step": step,
                "global_step": global_step,
                "observer_cid": observer_cid,
                "ghost_cid": ghost_cid,
                "link_id": link_id,
                "n_candidates": len(cands_sorted),
                "gain": result["gain"],
                "received": result["received"],
                "digested": result["digested"],
                "was_empty": result["was_empty"],
                "residual_Q_before": result["residual_Q_before"],
                "residual_Q_after": result["residual_Q_after"],
                "q_remaining_before": result["q_remaining_before"],
                "q_remaining_after": result["q_remaining_after"],
            })

    # ----------------------------------------------------------------
    # v10.1 Layer B Q 書き込み API (cog.attempt_ingestion から呼ばれる)
    # ----------------------------------------------------------------
    def add_q(self, cid, gain: int):
        """observer_cid (hosted) の Q_remaining を gain だけ増やす。

        Q0 上限あり: Q_remaining + gain > Q0 なら Q0 で頭打ち、
        超過分は received に含めず ghost からは引かれる (消化分、cog 側で計算)。

        Returns: (received, q_before, q_after)
          received: 実際に CID に入った量 (0 ≤ received ≤ gain、Q0 上限内)
          q_before: gain 加算前の v14_q_remaining
          q_after:  gain 加算後の v14_q_remaining (Q0 で clamp 済み)
        """
        entry = self.ledger.get(cid)
        if entry is None:
            return 0, 0, 0
        q0 = int(entry["v14_q0"])
        q_before = int(entry["v14_q_remaining"])
        capacity = max(0, q0 - q_before)
        received = min(int(gain), capacity)
        q_after = q_before + received
        entry["v14_q_remaining"] = q_after
        return received, q_before, q_after

    def get_q_remaining(self, cid):
        """detach 時の residual_Q snapshot 用 (cog 側 caller が読む)。"""
        entry = self.ledger.get(cid)
        if entry is None:
            return 0
        return int(entry["v14_q_remaining"])

    # ----------------------------------------------------------------
    # spend packet
    # ----------------------------------------------------------------

    def _process_event(self, *, cid, entry, ctx,
                       event_type: str, link_id: str,
                       window: int, step: int,
                       global_step: int) -> None:
        """1 event に対して spend packet を実行 + audit record を append。"""
        delta = self._compute_delta(entry, ctx)

        q_before = entry["v14_q_remaining"]
        spend_flag = (q_before > 0)
        attention_delta = 0.0
        familiarity_delta = 0.0

        if spend_flag:
            # virtual_attention: struct_set - core の各 node に +1
            virt_att = entry["v14_virtual_attention"]
            for n in ctx.get("attn_nodes", ()):
                virt_att[n] = virt_att.get(n, 0.0) + 1.0
                attention_delta += 1.0

            # virtual_familiarity: struct_set 経由で接触した他 cid に +1
            virt_fam = entry["v14_virtual_familiarity"]
            for other_cid in ctx.get("other_cids", ()):
                virt_fam[other_cid] = virt_fam.get(other_cid, 0.0) + 1.0
                familiarity_delta += 1.0

            entry["v14_q_remaining"] -= 1
            entry["v14_last_snapshot"] = dict(ctx["e_t"])
            entry["v14_shadow_pulse_index"] += 1

        last_gs = entry.get("v14_last_event_global_step")
        post_event_gap = (global_step - last_gs) if last_gs is not None else -1
        entry["v14_last_event_global_step"] = global_step

        self.events.append({
            "cid": cid,
            "seed_placeholder": None,  # flush 時に埋める
            "window": window,
            "step": step,
            "global_step": global_step,
            "v14_event_type": event_type,
            "link_id": link_id,
            "v14_q0": entry["v14_q0"],
            "v14_q_remaining": entry["v14_q_remaining"],
            "v14_spend_flag": bool(spend_flag),
            "v14_delta_norm": round(float(delta), 6),
            "v14_attention_delta": float(attention_delta),
            "v14_familiarity_delta": float(familiarity_delta),
            "v14_post_event_gap": int(post_event_gap),
            "v14_shadow_pulse_index": entry["v14_shadow_pulse_index"],
        })

    def _compute_delta(self, entry, ctx) -> float:
        """Δ = Weighted L1(reference, E_t)。

        reference: 初回 spend 前は M_c、以降は last_snapshot。
        last_snapshot は E_t 形式 ({n_local, s_avg_local, r_local, theta_avg_local})。
        delta_fn は M_c 形式 ({n_core, s_avg, r_core, phase_sig}) を期待するので
        変換する。
        """
        if self._delta_fn is None:
            return 0.0
        e_t = ctx["e_t"]
        last_snap = entry["v14_last_snapshot"]
        if last_snap is None:
            ref = ctx["m_c"]
        else:
            ref = {
                "n_core": last_snap["n_local"],
                "s_avg": last_snap["s_avg_local"],
                "r_core": last_snap["r_local"],
                "phase_sig": last_snap["theta_avg_local"],
            }
        delta, _ = self._delta_fn(ref, e_t)
        return float(delta)

    # ----------------------------------------------------------------
    # flush: audit CSV 出力 (v914_implementation_instructions.md §8.2)
    # ----------------------------------------------------------------

    def flush_run(self, outdir, seed: int) -> None:
        """run 終了時に audit CSV を出力する。

        出力先:
          outdir/audit/per_event_audit_seed{seed}.csv
          outdir/audit/run_level_audit_summary_seed{seed}.csv
          outdir/audit/per_subject_audit_seed{seed}.csv

        baseline CSV (per_window / per_subject / pulse_log / per_label) には
        1 列も追加しない (§5.3、§8.3)。
        """
        import csv
        from pathlib import Path

        audit_dir = Path(outdir) / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)

        # ─── per_event_audit.csv ───────────────────────────────────
        per_event_path = audit_dir / f"per_event_audit_seed{seed}.csv"
        per_event_fields = [
            "seed", "cid", "window", "step", "global_step",
            "v14_event_type", "link_id",
            "v14_q0", "v14_q_remaining", "v14_spend_flag",
            "v14_delta_norm", "v14_attention_delta", "v14_familiarity_delta",
            "v14_post_event_gap", "v14_shadow_pulse_index",
        ]
        with open(per_event_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=per_event_fields)
            writer.writeheader()
            for ev in self.events:
                row = {k: ev.get(k) for k in per_event_fields
                       if k in ev or k == "seed"}
                row["seed"] = seed
                writer.writerow(row)

        # ─── per_subject_audit.csv (cid 単位の最終 ledger 状態) ────
        per_subject_path = audit_dir / f"per_subject_audit_seed{seed}.csv"
        per_subject_fields = [
            "seed", "cid", "n_core_member",
            "v14_q0", "v14_q_remaining", "v14_q_spent",
            "v14_q_exhausted",
            "v14_shadow_pulse_count",
            "v14_virtual_attention_entries", "v14_virtual_attention_sum",
            "v14_virtual_familiarity_entries", "v14_virtual_familiarity_sum",
            "registered_window", "registered_step",
        ]
        with open(per_subject_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=per_subject_fields)
            writer.writeheader()
            for cid, entry in sorted(self.ledger.items()):
                q0 = entry["v14_q0"]
                q_rem = entry["v14_q_remaining"]
                reg_w, reg_s = entry["registered_at"]
                va = entry["v14_virtual_attention"]
                vf = entry["v14_virtual_familiarity"]
                writer.writerow({
                    "seed": seed,
                    "cid": cid,
                    "n_core_member": len(entry["member_nodes"]),
                    "v14_q0": q0,
                    "v14_q_remaining": q_rem,
                    "v14_q_spent": q0 - q_rem,
                    "v14_q_exhausted": bool(q_rem == 0),
                    "v14_shadow_pulse_count": entry["v14_shadow_pulse_index"],
                    "v14_virtual_attention_entries": len(va),
                    "v14_virtual_attention_sum": round(sum(va.values()), 4),
                    "v14_virtual_familiarity_entries": len(vf),
                    "v14_virtual_familiarity_sum": round(sum(vf.values()), 4),
                    "registered_window": reg_w,
                    "registered_step": reg_s,
                })

        # ─── run_level_audit_summary.csv (n_core バケット別集計) ──
        # n_core_bucket: 2, 3, 4, 5+
        summary_path = audit_dir / f"run_level_audit_summary_seed{seed}.csv"

        def _bucket(nc):
            return str(nc) if nc <= 4 else "5+"

        bucket_stats = {}
        for cid, entry in self.ledger.items():
            nc = len(entry["member_nodes"])
            b = _bucket(nc)
            d = bucket_stats.setdefault(b, {
                "n_cids": 0, "q0_sum": 0, "q_spent_sum": 0,
                "exhausted": 0,
                "shadow_pulse_sum": 0,
                "att_sum": 0.0, "fam_sum": 0.0,
            })
            d["n_cids"] += 1
            d["q0_sum"] += entry["v14_q0"]
            d["q_spent_sum"] += entry["v14_q0"] - entry["v14_q_remaining"]
            if entry["v14_q_remaining"] == 0:
                d["exhausted"] += 1
            d["shadow_pulse_sum"] += entry["v14_shadow_pulse_index"]
            d["att_sum"] += sum(entry["v14_virtual_attention"].values())
            d["fam_sum"] += sum(entry["v14_virtual_familiarity"].values())

        event_by_bucket = {}
        spend_by_bucket = {}
        event_type_by_bucket = {}
        for ev in self.events:
            cid = ev["cid"]
            entry = self.ledger.get(cid)
            if entry is None:
                continue
            nc = len(entry["member_nodes"])
            b = _bucket(nc)
            event_by_bucket[b] = event_by_bucket.get(b, 0) + 1
            if ev["v14_spend_flag"]:
                spend_by_bucket[b] = spend_by_bucket.get(b, 0) + 1
            key = (b, ev["v14_event_type"])
            event_type_by_bucket[key] = event_type_by_bucket.get(key, 0) + 1

        summary_fields = [
            "seed", "n_core_bucket", "n_cids",
            "q0_mean", "q_spent_mean", "q_exhaustion_ratio",
            "event_count", "spend_count", "event_to_spend_ratio",
            "shadow_pulse_sum", "shadow_pulse_per_cid",
            "attention_gain_total", "attention_gain_per_spend",
            "familiarity_gain_total", "familiarity_gain_per_spend",
            "e1_death_count", "e1_birth_count",
            "e2_rise_count", "e2_fall_count",
            "e3_contact_count",
        ]
        with open(summary_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summary_fields)
            writer.writeheader()
            for b in sorted(bucket_stats.keys()):
                d = bucket_stats[b]
                ev_count = event_by_bucket.get(b, 0)
                sp_count = spend_by_bucket.get(b, 0)
                n = d["n_cids"]
                writer.writerow({
                    "seed": seed,
                    "n_core_bucket": b,
                    "n_cids": n,
                    "q0_mean": round(d["q0_sum"] / max(n, 1), 4),
                    "q_spent_mean": round(d["q_spent_sum"] / max(n, 1), 4),
                    "q_exhaustion_ratio": round(
                        d["exhausted"] / max(n, 1), 4),
                    "event_count": ev_count,
                    "spend_count": sp_count,
                    "event_to_spend_ratio": (
                        round(ev_count / sp_count, 4) if sp_count > 0
                        else ""),
                    "shadow_pulse_sum": d["shadow_pulse_sum"],
                    "shadow_pulse_per_cid": round(
                        d["shadow_pulse_sum"] / max(n, 1), 4),
                    "attention_gain_total": round(d["att_sum"], 4),
                    "attention_gain_per_spend": (
                        round(d["att_sum"] / sp_count, 4) if sp_count > 0
                        else ""),
                    "familiarity_gain_total": round(d["fam_sum"], 4),
                    "familiarity_gain_per_spend": (
                        round(d["fam_sum"] / sp_count, 4) if sp_count > 0
                        else ""),
                    "e1_death_count": event_type_by_bucket.get(
                        (b, "E1_death"), 0),
                    "e1_birth_count": event_type_by_bucket.get(
                        (b, "E1_birth"), 0),
                    "e2_rise_count": event_type_by_bucket.get(
                        (b, "E2_rise"), 0),
                    "e2_fall_count": event_type_by_bucket.get(
                        (b, "E2_fall"), 0),
                    "e3_contact_count": event_type_by_bucket.get(
                        (b, "E3_contact"), 0),
                })

        print(f"  v914 Layer B audit CSVs written to {audit_dir}/")
        print(f"    per_event_audit: {len(self.events)} rows")
        print(f"    per_subject_audit: {len(self.ledger)} rows")
        print(f"    run_level_audit_summary: {len(bucket_stats)} rows")

        # ─── v10.3 双方向 E3 CSV 出力 ──────────────────────────────
        be3_dir = Path(outdir) / "bidirectional"
        be3_dir.mkdir(parents=True, exist_ok=True)

        # bidirectional_e3_log
        be3_log_path = be3_dir / f"bidirectional_e3_log_seed{seed}.csv"
        be3_fields = [
            "seed", "window", "step", "global_step",
            "cid_a", "cid_b",
            "ncore_a", "ncore_b",
            "phase_sig_a", "phase_sig_b",
            "s_avg_a", "s_avg_b",
            "r_core_a", "r_core_b",
            "q_a_before", "q_b_before",
            "c_a_before", "c_b_before",
            "age_a", "age_b",
            "link_id",
            "fired", "skip_reason",
            "shadow_audit", "in_observation_target",
        ]
        with open(be3_log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=be3_fields)
            writer.writeheader()
            for ev in self.bidirectional_e3_events:
                row = {k: ev.get(k, "") for k in be3_fields if k != "seed"}
                row["seed"] = seed
                writer.writerow(row)

        # bidirectional_e3_member_nodes_log (発火時のみ)
        mn_path = be3_dir / f"bidirectional_e3_member_nodes_log_seed{seed}.csv"
        mn_fields = [
            "seed", "window", "step", "global_step",
            "cid_a", "cid_b",
            "member_nodes_a", "member_nodes_b",
            "n_member_a", "n_member_b",
        ]
        with open(mn_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=mn_fields)
            writer.writeheader()
            for mn in self.bidirectional_e3_member_nodes:
                row = {k: mn.get(k, "") for k in mn_fields if k != "seed"}
                row["seed"] = seed
                writer.writerow(row)

        # bidirectional_e3_summary (run-level)
        be3_summary_path = be3_dir / f"bidirectional_e3_summary_seed{seed}.csv"
        n_total_records = len(self.bidirectional_e3_events)
        n_fired_records = sum(
            1 for ev in self.bidirectional_e3_events if ev.get("fired"))
        n_skipped_records = n_total_records - n_fired_records
        skip_reason_counts = {}
        for ev in self.bidirectional_e3_events:
            if not ev.get("fired"):
                skip_reason_counts[ev.get("skip_reason", "")] = (
                    skip_reason_counts.get(ev.get("skip_reason", ""), 0) + 1)
        with open(be3_summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["seed", "field", "value"])
            writer.writerow([seed, "n_be3_records_total", n_total_records])
            writer.writerow([seed, "n_be3_fired", n_fired_records])
            writer.writerow([seed, "n_be3_skipped", n_skipped_records])
            writer.writerow(
                [seed, "n_be3_target_inner", self._be3_count_target_inner])
            writer.writerow(
                [seed, "n_be3_target_outer", self._be3_count_target_outer])
            writer.writerow([seed, "shadow_audit_mode",
                             self._be3_shadow_audit])
            for sk, cnt in skip_reason_counts.items():
                writer.writerow([seed, f"skip_{sk}", cnt])
            if self._be3_target_tracker is not None:
                writer.writerow(
                    [seed, "n_observation_targets",
                     len(self._be3_target_tracker)])
                writer.writerow(
                    [seed, "n_target_via_stage1",
                     sum(1 for v in
                         self._be3_target_tracker.added_via.values()
                         if v == "stage1")])
                writer.writerow(
                    [seed, "n_target_via_stage2",
                     sum(1 for v in
                         self._be3_target_tracker.added_via.values()
                         if v == "stage2")])

        print(f"  v10.3 bidirectional E3 CSVs written to {be3_dir}/")
        print(f"    bidirectional_e3_log: {n_total_records} rows "
              f"({n_fired_records} fired, {n_skipped_records} skipped)")
        print(f"    bidirectional_e3_member_nodes: "
              f"{len(self.bidirectional_e3_member_nodes)} rows")
        print(f"    bidirectional_e3_summary: 1 file")
