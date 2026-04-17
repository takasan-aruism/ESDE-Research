# v9.14 Implementation Notes (Code A)

*Date*: 2026-04-17 〜 2026-04-18
*Author*: Claude Code A (実装担当)
*関連*: `v914_implementation_instructions.md` (Taka 指示書), GPT memo (非参照)

---

## Summary

Steps 0-7 完了。bit-identity + 8 項目合格条件すべて満たす。
Step 8 (48 seeds short run) と Step 9 (5 seeds long run) はユーザー承認待ち。

## 完了状況

| Step | 内容 | 状態 | bit-identity |
|------|------|------|---|
| 0 | v913_persistence_audit.py コピー + docstring / outdir 更新 | ✅ | ✅ |
| 1 | Layer B skeleton (no-op SpendAuditLedger) | ✅ | ✅ |
| 2 | E1 (core link death/birth) 検知のみ | ✅ | ✅ |
| 3 | Spend packet (E_t 読み出し / Δ / virtual_* 更新 / Q 減算) | ✅ | ✅ |
| 4 | E2 (core link R-state change) 追加 | ✅ | ✅ |
| 5 | E3 (familiarity contact onset) 追加 | ✅ | ✅ |
| 6 | audit CSV 出力 (per_event / per_subject / run_summary) | ✅ | ✅ |
| 7 | full smoke (1 seed × mat 20 / track 10 / steps 500) | ✅ | ✅ |
| 8 | short run (48 seeds) | ⏸ pending | — |
| 9 | long run (5 seeds × track 50) | ⏸ pending | — |

## Step 7 合格条件チェック (§10.1)

| 項目 | 結果 |
|------|------|
| baseline per_window CSV が v9.13 smoke と bit-identical | ✅ |
| v10_ / v11_ / v13_ 列が v9.13 smoke と完全一致 | ✅ |
| Layer B audit CSV (per_event / summary) が欠損なく出力 | ✅ (324 rows / 4 rows / 46 rows) |
| v14_q_remaining が正しく減算、0 未満にならない | ✅ 0 cids Q<0 |
| E1 / E2 / E3 が意図通り発火 | ✅ E1_death=46, E1_birth=2, E2_rise=36, E2_fall=36, E3_contact=204 |
| エラー / 例外なし | ✅ exit code 0 |
| 実行時間の v9.13 比上振れが +15% 以内 | ✅ +0.5% (64m06s vs 63m46s) |
| Layer B から Layer A への mutation がゼロ | ✅ grep + bit-identity |

## 実装上の判断事項

### (A) コピー元の確認

指示書 §2.3 / §5.4 / Appendix B は `v913_persistence_audit.py` を copy 元と明示。
bit-identity 参照も同ファイル。v9.13 には別途 `v913_persistence_birth.py` が
存在するが、こちらは persistence birth 改変版 (audit.py は add-only)。
指示書の literal 解釈に従い、`v913_persistence_audit.py` を採用。

### (B) Lazy registration (SpendAuditLedger)

cid の birth 時点で engine.step_window が内部実行される maturation 期間は
per-step hook が取れない。そのため cid 登録は observe_step での **lazy
registration** 方式とした: 初回観測時に member_nodes / Q0 を確定、prev
snapshot を取り、この step では event 発行しない。次 step 以降で diff 検出。

利点:
- maturation/tracking 区別なしで動作
- birth site への hook 追加なしで実装が閉じる
- Layer A に一切手を加えない

欠点:
- cid の birth-time 正確な member_nodes ではなく初回観測時点の member_nodes
  を採用することになる (cid rehost で差異が生じる可能性、ただし極めて稀)

### (C) Event ごとの spend: 1 event = 1 spend attempt

同一 step 内で E1 / E2 / E3 が複数発火した場合、各 event が独立に spend
packet を実行 (Q が残っていれば消費)。last_snapshot は spend ごとに更新
されるため、同 step 内の 2 件目以降の event は delta=0 になる (定義通り)。

virtual_attention / virtual_familiarity の更新量は +1.0 per 対象 node/cid で
固定 (Layer A の `update_attention` / `update_familiarity` と同じ加算量)。
delta は記録のみで virtual 更新量にはフィードバックしない。

Note: Layer B は per-step decay を行わない (event-driven のため)。累積値で
保持し、分析時に必要なら正規化する方針。

### (D) E2 の narrow 実装

§4.2 / §9.3 に厳守して「core-local」のみ:
- 検出対象: member node pair で構成される link のみ
- R==0 の alive link は R dict に含めない (0 境界跨ぎだけが event)
- dead link は R 扱いせず (E2_fall は prev に存在 + curr で消失のみ)
- core-adjacent への拡張は一切していない

### (E) E3 の最適化 (§6.2)

alive link ごとに逆引き (node → cids 逆引き dict) を使う方式で実装:
O(|alive_l| × avg_cids_per_node²)。

逆引き dict (`_node_to_cids`) は cid 登録時に member_nodes 経由で add、
一度登録したら削除しない (member_nodes は soul で不変、一度成立した
contact pair も不変記録)。

重複防止は `_contacted_pairs` (frozenset set) で O(1) 判定。

### (F) E3 の event 発行単位

1 pair の contact onset につき 2 event 発行 (cid_a 視点 / cid_b 視点)。
各 cid が自身の spend packet を実行する。ただし observe_step 呼び出し時の
cid_ctx に含まれない (非 hosted) cid 側は skip する。これにより:
- 両 cid が hosted: 2 events, 2 spend attempts
- 片方のみ hosted: 1 event, 1 spend attempt
- どちらも非 hosted: 0 event (contacted_pairs には記録して再発火防止)

### (G) B_Gen inf の扱い

`cog.v11_b_gen[cid] = float('inf')` は n_core < 2 の退化ケース。ledger
対象外とした (Q0 が inf では計数不能、member link もないので E1/E2 対象外)。
ctx.member_nodes < 2 も同時に skip。

### (H) cid_ctx 構築の範囲

毎 step 全 hosted cid について build:
- b_gen 確認 (finite & positive)
- m_c 確認 (v11_m_c に記録あり)
- struct_set 確認 (v11_current_struct_set に本 step 分あり)
- e_t を v11_compute_e_t で計算
- attn_nodes = struct_set - core (Layer A と同じ除外)
- other_cids = struct_set 経由で接触する他 cid (Layer A update_familiarity と同じ)

オーバーヘッドは Step 7 smoke で +0.5% に収まった (5000 steps × ~50 cids)。

## Audit CSVs 出力

`diag_v914_{tag}/audit/` 配下に 3 種:
- `per_event_audit_seed{N}.csv`: event 発火ごとに 1 行 (15 列)
- `per_subject_audit_seed{N}.csv`: cid 単位の最終 ledger 状態 (14 列)
- `run_level_audit_summary_seed{N}.csv`: n_core バケット別集計 (20 列)

baseline CSV (per_window / per_subject / pulse / per_label) には 1 列も
追加していない (§5.3、§8.3)。

### run_level_audit_summary の制限事項

指示書 §8.2 で mentioning されている `shadow_vs_fixed_overlap`,
`spend_efficiency_capture_rate` など GPT memo 本文に詳細定義があると
思われる指標は、memo 非参照のため未実装。現在の summary は以下を出力:

```
seed, n_core_bucket, n_cids,
q0_mean, q_spent_mean, q_exhaustion_ratio,
event_count, spend_count, event_to_spend_ratio,
shadow_pulse_sum, shadow_pulse_per_cid,
attention_gain_total, attention_gain_per_spend,
familiarity_gain_total, familiarity_gain_per_spend,
e1_death_count, e1_birth_count,
e2_rise_count, e2_fall_count, e3_contact_count
```

fixed pulse との overlap は分析時に pulse_log と per_event_audit を突き合わせ
れば計算可能。相談役 Claude に委ねる。

## ファイル構成

新規作成:
- `primitive/v914/v914_probabilistic_expenditure.py` (v913_persistence_audit コピー + Layer B 追加のみ)
- `primitive/v914/v914_spend_audit_ledger.py` (Layer B class)
- `primitive/v914/v914_event_emitter.py` (E1/E2/E3 純関数)
- `primitive/v914/v914_implementation_notes.md` (本ファイル)

不変 (1 バイトも触らない):
- `autonomy/v82/esde_v82_engine.py`
- `ecology/engine/v19g_canon.py`, `genesis_state.py`, etc.
- `primitive/v910/virtual_layer_v9.py`
- `primitive/v911/v911_cognitive_capture.py`, `v911_genesis_budget_measure.py`
- `primitive/v913/v913_persistence_audit.py`

## 次フェーズ (pending)

### Step 8: short run (48 seeds × mat 20 / track 10 / steps 500)

想定: single seed smoke が ~64 min かかったため、parallel -j24 で 2 seed/core
= 約 2-3 時間 wall time。

想定外に重い (GPT memo の想定より長い可能性)。軽量化 (--window-steps 250 など)
の可否をユーザーに確認予定。

### Step 9: long run (5 seeds × mat 20 / track 50 / steps 500)

5 倍 tracking steps。single seed で ~5× = ~5 hours 想定。5 seeds × -j5
並列で wall ~5-6 時間。

## 観察事項 (Describe, do not decide)

Step 7 full smoke (seed 0) のみから観察:

- **n_core=5+ の 10 cids が event の 40% (127/324) を占める** — 期待通り
  大きい cid ほど多く spend する傾向。
- **E1_birth が 2 件発生** — 死んだ member link が復活する事例が稀に起こる。
  n_core=5+ で発生 (大きい構造ほど復活の余地が広い?)。
- **E3 contact が 204 件** — 最多イベント。物理的接触は 200 step に 1 回
  程度で新規発生。
- **q_exhaustion_ratio = 0** — 5000 step では誰も Q0 を使い切らない。より
  長い track が必要か、あるいは event 定義を拡張しないと Q exhaustion は
  見えない可能性。

これらは smoke 1 seed の個別観察。統計的主張は 48 seeds 完走後。
