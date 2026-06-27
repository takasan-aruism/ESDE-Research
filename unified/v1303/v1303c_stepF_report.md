# v1303c Step B〜F — 研究者手本イベント二系統の event_ledger 観察事実報告（判定なし）

*作成*: 2026-06-28、Code A。
*位置づけ*: v1303c 主題設計（Step A 反映・道3版）の Step B〜F。既存 v1303a ledger（seed0）の**後処理のみ**（再走なし・write-back なし・Step E 不要）で、研究者手本イベント二系統（**birth_signature**=R_positive 誕生署名 / **salience_template**=θ高同期 cid 内 percentile）を read-only 検出し event_class で分けて event_ledger に保持できるかを観察した。**(a)/(b) 判定・主題評価はしない（#12）。** 「自律注意」「経験成立」とは言わず、「二系統の手本イベントを read-only 検出し event_class を分けて記録器に保持できた＝注意センター前段の記録配線・離脱可能な構造を作る段階」までに留める。判定は Web Claude / Taka。
*成果物*: `v1303c_event_ledger.py` / `outputs/v1303c/v1303c_event_ledger_seed0.parquet`（4,222行×25列）/ `v1303c_distributions.html`。
*前提突合*: Step A 認識確認（`v1303c_stepA_recognition.md`）で設計の配線前提を全突合。道3版の θ-high percentile 値・寿命位置・重なり・健全性3 も実装前に実データで再突合済（下記）。

---

## 0. 実行設定（道3・二系統・event_class 分離）
- 入力 = `v1303_ledger_seed0.parquet` の hosted_available 行（後処理のみ・再走なし）。anchor=v105_v2（v1114 は v918 anchor で F型ゆえ流用せず・Step A §4）。
- **birth_signature**（R_positive 誕生署名）：`core_internal_R_positive_count>0` 行を連続区間化、event_type = present_at_birth(先頭かつ i=0) / active(中間) / offset(区間末)。**onset は使わない**（Step A：観測不能・捏造しない）。
- **salience_template**（θ高同期）：各 cid の `theta_resultant_length >= cid内 q95値`（quantile 0.95 しきい値・上位5%）。**絶対値 θ>0.9 は使わない**（D型回避＝θ>0.9 行の85%が n2）。event_source=`researcher_template:theta_high_cid_percentile_v1`。
- event_source/template_version に手本タグを焼く＝将来 endogenous へ一括置換できる**離脱ポインタ**（A型/#CW7 回避）。

## 1. 観察 — 二系統を event_class で分けて記録できたか
- **総イベント 4,222 行**（birth_signature **1,002** / salience_template **3,220**）。25列。
- **event_class × event_type**：
  | event_class | event_type | rows | cids |
  |---|---|---|---|
  | birth_signature | present_at_birth | 140 | 140 |
  | birth_signature | active | 743 | — |
  | birth_signature | offset | 119 | — |
  | salience_template | theta_high | 3,220 | 228 |
  - present_at_birth=140（全 R_positive cid が誕生時に在）。offset=119（21 cid は segment 長1 で present_at_birth と一致＝先頭優先で present_at_birth に分類）。
- **event_class 別 cid 分布（n_core 別）**：
  | class | cid総 | n2 | n3 | n4 | n5 |
  |---|---|---|---|---|---|
  | birth_signature | 140 | 123 | 4 | 6 | 7 |
  | salience_template | 228 | 180 | 12 | 15 | 21 |
  - salience は **全 228 cid・全 n_core を網羅**（健全性3）。birth_signature は 140 cid（R_positive を持つ cid のみ）。

## 2. 欠損構造・二系統の重なり
- pre_context_id null = **169**（各 cid の最初の hosted t 行＝直前なし）／ post_context_id null = **13**（最後の hosted t 行＝直後なし）。それ以外は隣接 step10 行（t±10）へ参照紐づけ（context_window=`pm1_step10` 固定）。
- **二系統の重なり = 270 行（135 (cid,t) ペアが両 class）**。誕生直後に θ も高い cid＝R_positive と θ高同期が同時刻に立つ。**event_class で分離保持しているため混ざらない**（同一 cid/t が birth_signature 行と salience_template 行に各1つ）。重なりの解釈は次段（#11 合成しない）。

## 3. 素の分布（event_class 別・n_core 別・合成しない）
- **θ_resultant 中央値**：
  | class | n2 | n3 | n4 | n5 |
  |---|---|---|---|---|
  | birth_signature | 0.942 | 0.741 | 0.683 | 0.522 |
  | salience_template | 0.999 | 0.974 | 0.902 | 0.856 |
  - salience（θ高同期）は当然 θ が高い。birth_signature の θ は n_core が大きいほど低い（誕生署名時の位相同期は n_core 依存）。
- レンズ②（rank_1_sim 等）・①（C/Q）も各 event 行に read-only 同梱（HTML 参照）。

## 4. 健全性 sanity check（主題の出口にしない）
- **健全性1**: birth_signature 1,002 行は**全件 hosted_available**（`assert` True）。R_positive が ghost/reaped に混入していない（G/F型なし）。
- **健全性2（予測修正・assert せず記録）**: R_positive 行の rank_1 entropy は全 hosted と差あり・n_core 依存逆向き（n2: 1.026→1.333 / n5: 2.366→0.471）。設計の「|d|<0.2 差なし」予測は不成立ゆえ **assert せず効果を観察事実として記録**（新発見扱いしない）。
- **健全性3（道3新規）**: salience の θ高同期は **全 n_core から拾えている**（cid: n2 180/180・n3 12/12・n4 15/15・n5 21/21）＝cid 内 percentile が n2 偏りを起こしていない（D型回避の確認）。

## 5. 【ユーザ指示の核心】説明可能性ルーブリック 実装後突合（全項目 PASS）
Step A §5 で各列に設定した操作定義と、生成 event_ledger を `verify_rubric()` で自己突合（強引な解釈が入っていないかの実装後検証）：
| 検証項目 | 操作定義の確認内容 | 結果 |
|---|---|---|
| present_at_birth_all_at_first_t | present_at_birth 行は全て各 cid の最初の hosted t か | **True** |
| birth_rows_all_rpos_positive | birth_signature 行は全て r_positive_count>0 か（0行を混ぜていない） | **True** |
| salience_rows_all_above_cid_q95 | salience 行は全て cid 内 q95 値以上か | **True** |
| resonating_eq_rpos | resonating_internal_link_count == r_positive_count（生カウント別名の整合・「強さ」を盛らない） | **True** |
| event_class_only_two | event_class は birth_signature / salience_template の二値のみ | **True** |
| event_source_all_template | 全行 event_source が `researcher_template:` で始まる（離脱ポインタ＝手本明示） | **True** |
| pre_context_null_at_first_t | 誕生時行の pre_context_id は全て null（隣接行なしを正しく null 化） | **True** |
- → **7項目すべて PASS**。LOW 説明可能性だった event_type/onset_flag は Step A 時点で `present_at_birth` へ再定義（onset 捏造を排除）、event_strength は `resonating_internal_link_count` 生カウントに置換済で、生成物が操作定義通りであることを実装後に確認した。

## 6. 言えること / 言えないこと（道3・厳守）
- **言える（観察事実）**: 研究者手本イベント二系統を read-only 検出し、event_class（birth_signature / salience_template）で分けて cid/t と pre/post 文脈に紐づけて event_ledger に保持できた（4,222行・離脱ポインタ event_source 付き）。birth_signature は誕生集中（present_at_birth 140）・salience は全 n_core 分散。重なり 135 ペアは別 class で混ぜず保持。
- **言わない**: 「ESDE が自律注意した」「経験成立」「外部照合開始」とは言わない。**R_positive を「稀な結節イベント」と呼ばない**（誕生署名＝founding cycle 減衰痕）。**θ高同期を「本質的注意イベント」と言い切らない**（研究者手本の本命候補）。二系統を合成・単一スコア化しない（#11）。Atom 意味解釈しない（L型）。(a)/(b) 判定は委ねる。

## 7. 規律遵守
- A型/#CW7: event_source/template_version に手本タグ＝離脱ポインタ。θ高同期も「研究者手本」と明記（自律検出でない）。**Step A で R_positive の onset 捏造を事前回避＝C型予防**。
- #2/B型: 既存 ledger 後処理のみ・write-back なし・物理/CID/親非書込。書込 `outputs/v1303c/` のみ。
- D型: θ高同期は cid 内 percentile（絶対値閾値の n2 偏り回避）。cid 個別・n_core 別。#11: 二系統を event_class 分離・合成しない・link を node に混ぜない。
- L型: R_positive を結節と偽らず誕生署名。event_strength を避け生カウント。#12/J型: 判定せず観察事実のみ・手本2系統で打ち止め・seed0 のみ。F型: anchor=v105_v2（v1114 流用せず）。

## 8. v1303b 読み修正の申し送り（設計§2・Web Claude が Phase Result で追記）
v1303b 観察E の「R_positive 時の θ高同期(0.889)」は「閉路イベントが途中で生じた」でなく「**誕生直後の CID は founding cycle と高位相同期**」の反映（θ@R_positive は θ@誕生直後と交絡）。観察A/B/C/D は不変。→ Web Claude が v1303b Phase Result に追記。

## 9. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（event_class 分離・θ cid内 percentile・onset 不使用・離脱ポインタ・ルーブリック突合の生データ再確認）→ Phase Result（+v1303b 読み修正追記）→ Taka 主題評価。離脱本体（ESDE 自身の珍しさ/B_Gen で手本を外す）・外部照合は次段以降。

---

## 10. 一文サマリ
v1303c 道3版（既存 v1303a ledger 後処理・再走/write-back なし・seed0・anchor v105_v2）で研究者手本イベント二系統を read-only 検出し event_class 分離で event_ledger（4,222行×25列）に保持＝**birth_signature(R_positive 誕生署名)1,002行**(present_at_birth140/active743/offset119・全hosted・140cid・onset は観測不能ゆえ不使用)と **salience_template(θ高同期 cid内q95上位5%)3,220行**(全228cid・全n_core網羅・絶対値θ>0.9のn2偏りをcid内percentileで回避)を同格にせず分離保持(重なり135ペアは別classで混ぜない)、健全性1(birth全hosted)assert True・健全性2(rank_1 entropy差あり n_core依存ゆえassertせず記録)・健全性3(θ高同期 全n_coreから 180/12/15/21)、**説明可能性ルーブリック7項目を実装後 verify_rubric() で全PASS**(present_at_birth=各cid最初t・birth全rpos>0・salience全q95以上・resonating=rpos生カウント・class二値・source全手本タグ・誕生時行pre null)＝強引な解釈が入っていないことを実装後に確認、event_source に手本タグ＝将来endogenousへ置換できる離脱ポインタ(A型/#CW7回避)、出口は「二系統を read-only 検出し event_class分けて記録器保持できた＝注意センター前段の記録配線・離脱可能な構造」まで(自律注意・経験成立・R_positiveを結節・θ高同期を本質とは言わない)、v1303b観察E解釈を誕生署名に修正の申し送り、判定はWeb Claude/Taka。
