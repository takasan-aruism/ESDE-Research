#!/usr/bin/env python3
"""
ESDE v9.14 — Spend Audit Ledger (Layer B)
==========================================
v9.14 Probabilistic Expenditure Audit の Layer B 専用モジュール。

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


class SpendAuditLedger:
    """cid 単位で仮想原資 Q と virtual attention / familiarity を保持する audit-only ledger。

    Layer A の state を一切書き換えない。全ての書き込みは self.ledger と
    self.events (audit event list) に閉じる。

    外部の delta 計算ヘルパ (v11_compute_delta, ref 変換) は本体から注入する
    (observe_step の引数 delta_fn)。これにより v911 定数 / 関数への直接依存を
    本モジュール内に持たせず、疎結合を保つ。
    """

    def __init__(self, delta_fn=None, disable_e3: bool = False) -> None:
        """delta_fn(ref_m_c_like, e_t) -> (delta_total, axes_dict)。

        ref_m_c_like は {"n_core", "s_avg", "r_core", "phase_sig"} を持つ dict。
        e_t は {"n_local", "s_avg_local", "r_local", "theta_avg_local"} を持つ dict。
        本体から v11_compute_delta を差し込んで使う。

        disable_e3=True のとき E3_contact の event 発行を skip する (§6.4
        ablation)。contacted_pairs への登録は継続 (再現性維持)。E1/E2 の
        検知・spend は変更なし。Layer A state は読み取り専用のまま。
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
        for (cid_a, cid_b, lk) in new_e3_pairs:
            # 各 cid 視点で 1 event ずつ発行 (計 2 event/pair)。
            # ただし ctx に無い (hosted でない、または登録前) cid は skip。
            # contacted_pairs は detect 関数内で既に追加されているため、次 step
            # 以降で hosted に戻っても E3 は再発火しない (仕様通り onset のみ)。
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
