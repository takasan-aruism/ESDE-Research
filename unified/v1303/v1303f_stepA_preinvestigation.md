# 注意センター統合 Step A 事前調査 — v1114 統合の前提に重大なずれ（報告・実装前に判断要請）

*作成*: 2026-06-30、Code A。
*種別*: Step A 事前調査（実装前）。read-only。**設計の前提と実データのずれを2件検出（うち1件は設計の根幹）→ 実装に進まず報告し判断を仰ぐ。** 構成的な代替案も提示。
*対象*: Web Claude（設計者）/ Taka（判断）。

---

## 0. 結論（先に）
- **v1114 の構造的理解（イベント駆動6トリガー・familiarity・EWMA+z・read-only・443レコード）は設計通りで正しい。**
- だが**統合の前提「v1114 は v105 移植済・v1303 と同じ CID 宇宙・t だけ復元すればよい」は実データと食い違う**：
  - **【問題1・t】v1114 はレコードに t を持たない**（order のみ）。かつ40件の (cid,trigger) が複数回出現し **order→t を一意に決められない**。
  - **【問題2・CID宇宙・設計の根幹】v1114 の run は diag_v105_main_v2（v1303 anchor）とは別の run**。v1114-only の9 cid は per_subject に**1つも存在しない**＝同一runの hosted フィルタ差でなく**別run**。しかも v1114 の run は既知の退化バグ付き。
- → **v1114 の 443 JSON を cid/t で直接統合するのは F型（別run・別CID宇宙）。** 構成的代替＝**canonical ログから v1114 型イベントを再構成**（同228 cid・t 付き・再走不要・v1114バグ回避）を提案。**設計の根幹に関わるので実装前に判断を仰ぐ。**

---

## 1. 確認できた事実（v1114 は設計通り）
- step1(287)→step1b(383)→step2a(443)→step2b(453)。step2a/2b の run 設定 = seed0 / mat20 / track50 / win500 / final_step35000 ＝ **v1303 と同一 config**。
- レコード構造: `order, cid, trigger, point{n_core,lifespan,pulse_reactivity,C,Q_remaining}, neighborhood{familiarity_n,familiarity_sizes}`。
- trigger 分布（step2a 443）: alpha_formation 145 / c_conversion 119 / beta_formation 68 / cid_birth 58 / cid_death 43 / pulse 10。
- **イベント駆動・read-only・familiarity・EWMA+z** という設計の理解は実コード/出力と一致。

## 2. 【問題1】t 未保持・order→t が一意でない
- v1114 レコードの時間情報は `order`(連番)のみ。**t(step10刻み)が無い**。
- **40件の (cid,trigger) が複数回出現**（例: (0,c_conversion),(2,alpha_formation),(19,c_conversion)…）＝同一cidで同種イベントが複数回 → **order だけでは各レコードの t を一意に決められない**。
- 復元元候補の source_events timestamp は step1 が使用したが step2a/2b JSON には残っていない。

## 3. 【問題2・根幹】v1114 の run は別run（同一CID宇宙でない）
| 比較 | 値 |
|---|---|
| v1114 step2a cid 数 | 131 |
| v1303 ledger cid 数 | 228 |
| 共通 | **122** |
| v1114-only | 9（27,32,35,39,45,53,55,59,63）|
| v1303-only | 106 |
- **決定的**: v1114-only の9 cid は **per_subject_seed0(228cid) に1つも存在しない**（全 False）。v1303 ledger cid ⊆ per_subject（完全部分集合）だが **v1114 cid は per_subject の部分集合でない**。
- → ESDE は bit-identity（同 code+seed+config で同一 cid・v1303a で実証済）。**cid が食い違う＝v1114 の run は別 code/config の v105**（step2a summary に「v105 hook で 100%退化・formation_relation/lifecycle_phase を落とした既知バグ」と明記＝退化した別 run）。
- → **v1114 の 443 を v1303 の cid に直接 join すると、9 cid は宇宙外・106 cid は欠落・退化フィールド(Q_remaining=unknown)混入＝F型の異系対応**。Web Claude の予備「9個ズレ・微妙に違う」より深く、**統合の土台が別run**。

## 4. 構成的代替案（過去を無駄にせず・整合性を回復）
**v1114 の JSON データを使わず、v1114 の「設計」（6トリガー型 + familiarity + EWMA+z novelty）を canonical diag_v105_main_v2 ログに再適用して Now-event レコードを再構成する。**
- **feasibility 確認済**（canonical ログに6トリガー全てが t+cid 付きで存在）:
  | トリガー | canonical ソース | t | cid |
  |---|---|---|---|
  | cid_birth / cid_death | per_subject_seed0（birth_window→step / host_lost_step / reaped_step） | ✓ | cognitive_id |
  | pulse | pulse_log_seed0（t） | ✓ | cid |
  | alpha_formation | alpha_lifecycle_log（step, event_type, member_cids） | ✓ | member_cids |
  | beta_formation | beta_lifecycle_log（step, member_cids） | ✓ | member_cids |
  | c_conversion | c_trajectory（step_at_window_end, cid） | ✓ | cid |
- 利点: (1)**v1303 と同一 228 cid 宇宙**（F型回避）、(2)**t 付き**（step10 に丸めて v1303 ledger と exact/±1 join 可）、(3)**v1114 の退化バグを持ち込まない**、(4)**後処理のみ・再走不要**、(5)**過去を無駄にしない**＝v1114 の event-type 設計・familiarity・EWMA+z ロジックを spec として再利用（v1114 はデータ源でなく「何を検出するかの参考実装」になる）。
- familiarity（v1114 固有・v1303 に無い）は v105 の familiarity ログ/per_subject から再構成可能か Step B で確認（neighborhood 情報の出所）。

## 5. 今回分の実装範囲（提案・Phase1）
判断が出たら、Phase1 を以下に絞る（一括にしない）:
1. canonical ログから **Now-event レコード**（6トリガー・t付き・228宇宙）を再構成。
2. v1303e の **persistence(stable-above-baseline) を Archive-event** として既存流用。
3. 両者を **event_class（now_event / archive_persistence）で分けた統合レコード**に並べる（合成しない・Comparator 4分類は土台列のみ・判定数値は監査用 raw で残す）。
4. familiarity・EWMA+z は段階的に（まず Now-event の t 付き再構成と join 健全性を固めてから）。

## 6. 判断を仰ぐ点（実装前・設計の根幹ゆえ）
1. **v1114 の 443 JSON を直接統合するのを止め、canonical ログから v1114 型イベントを再構成する**方針でよいか（v1114=データ源 → v1114=spec/参考実装 への変更）。これは「過去を無駄にしない」を満たす（設計・ロジックを継承）が、設計文の「v1114 の443レコードを過去の型として蓄積」を「canonicalから再構成した型を蓄積」に読み替える。
2. それとも v1114 の別run・退化を承知で 122 共通 cid のみで t 復元を試みるか（推奨しない＝別run混入・t曖昧・106欠落）。
3. familiarity の出所（v105 ログから再構成 or v1114 の値を参考値として限界タグ付きで借りるか）。

## 7. 規律
- read-only・親非書込・#12 判定せず事実のみ。**一括で進めず、設計の根幹のずれ（別run）を実装前に報告**（信頼問題・前回の教訓「想定外で先に進まない」を継続）。

## 8. 一文サマリ
注意センター統合 Step A 事前調査（Code A, 2026-06-30, read-only・実装前）── v1114 の構造的理解(イベント駆動6トリガー/familiarity/EWMA+z/read-only/step2a 443)は設計通りと確認した一方、統合前提に2つのずれを検出＝**【問題1】v1114 はレコードに t を持たず(order のみ)40件の(cid,trigger)重複で order→t が一意でない**、**【問題2・根幹】v1114 の run は diag_v105_main_v2(v1303 anchor)とは別run**(v1114-only の9 cid 27,32,35,39,45,53,55,59,63 は per_subject_seed0 に1つも存在せず・v1303 cid⊆per_subject だが v1114 cid⊄per_subject・step2a summary に「v105 hook 100%退化」既知バグ明記=退化した別run・共通122/v1114のみ9/v1303のみ106)、ゆえに v1114 の443 JSON を cid/t で直接統合するのは F型(別run・別CID宇宙・退化フィールド混入)、構成的代替＝**canonical diag_v105_main_v2 ログ(pulse_log[cid,t]/α・β lifecycle[step,member_cids]/c_trajectory[cid,step]/per_subject[birth,host_lost,reaped])から v1114 の6トリガー型を t+cid 付き・同228 cid宇宙で再構成**(F型回避・t付き・v1114バグ回避・後処理のみ・過去を無駄にしない=v1114の設計/familiarity/EWMA+zを spec として継承)を feasibility 確認の上で提案、Phase1 範囲は Now-event 再構成+v1303e persistence を Archive として event_class 分離した統合レコード(合成しない・Comparator土台のみ・raw監査値)に絞る、設計の根幹(v1114=データ源→spec)に関わるため実装前に判断要請(一括で進めず・信頼問題)。
