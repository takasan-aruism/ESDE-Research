# v1303e Step A〜F — θ高同期閾値を5%固定から persistence(内部履歴由来)に置換 観察事実報告（判定なし）

*作成*: 2026-06-29、Code A。
*位置づけ*: v1303e 主題設計（判断A・全面適用 persistence一本）の Step A〜F。既存 v1303a ledger + v1303c event_ledger の**後処理のみ**（再走/write-back なし）で、θ高同期手本の閾値を **cid内 percentile 上位5%固定(q95)** から **persistence（θがcid中央値以上の状態が連続3点持続＝Frozen の age_r≥τ と同型の内部履歴由来閾値）** に置き換え、salience の像が変わるかを観察した。**(a)/(b) 判定はしない（#12）。** 「persistence が優れている」「5%固定を倒した」「離脱できた」とは言わない。**これはθ系閾値の内部化であって非θ系=言語の離脱ではない（L型・明記）。** 判定は Web Claude / Taka。
*成果物*: `v1303e_persistence_salience.py` / `outputs/v1303e/v1303e_persistence_salience_seed0.parquet`（25,568行）/ `v1303e_compare_q95_seed0.parquet` / `v1303e_distributions.html` / 調査の `v1303e_threshold_compare_seed0.parquet`。

---

## 0. Step A 認識確認（実装前確認・調査で実質済）
v1303e 調査（`v1303e_investigation_report.md`）で persistence_median_N3 が全n_core空振り0・q95とJaccard≈0.12 を確認済。本実装で event_ledger 構成（v1303c salience と同列構成）・event_source 手本タグ・q95比較経路・全n_core空振り0 を再確認（全て成立）。

## 1. persistence salience の定義（Frozen の age_r 型と同型）
- **persistence_median_N3**：θ_resultant が **cid内中央値以上の状態が連続3点（step10×3＝30step）以上続いた区間**に属する時点を θ高同期 salience とする（`runs_mask_ge`）。
- Frozen の `persistence-based birth（age_r≥τ, v104_memory_readout.py:1741/2367＝連続R>0数で判定）` と同型＝「状態が持続した時間」で閾値を立てる。
- **event_source=`researcher_template:theta_high_persistence_median_N3_v1`**（N=3・median は研究者選択ゆえ手本タグ＝離脱ポインタ・将来 endogenous 置換可）。

## 2. 観察 — persistence で salience を拾えたか・q95(5%固定)と違う像か
- **persistence salience = 25,568行 / 228 cid / 4,833 segment（segment長 中央4点＝40step）**。**全 cid 空振り0・全件 hosted**。
- **persistence vs q95（n_core別中央値）**：
  | n_core | persist_frac | q95_frac | Jaccard | persist空振り |
  |---|---|---|---|---|
  | 2 | 0.457 | 0.061 | 0.117 | 0/180 |
  | 3 | 0.418 | 0.051 | 0.115 | 0/12 |
  | 4 | 0.423 | 0.051 | 0.123 | 0/15 |
  | 5 | 0.399 | 0.050 | 0.123 | 0/21 |
- **像の違い（事実）**：persistence は **cid 寿命の約45%**（全体 med 0.447）を「持続高同期」として拾う＝**q95 の約5%（瞬間ピーク）と Jaccard≈0.12 で別の時点**。閾値の内部化で salience の像は**確かに変わった**（持続区間 vs 瞬間ピーク・多様性拡張の像）。

## 3. 【重要・正直な注記】persistence salience は「広い」（45%）
- persistence は **寿命の約45%を salience とする**＝q95（5%）の約9倍の広さ。「際立ち(rare)」という語感からは**かなり広い**（45%が salient なら「際立ち」と呼べるかは Taka 判断）。
- これは persistence 型の性質：θ≥中央値は定義上ほぼ50%、連続3点条件で僅かに絞られ約45%。**「持続した高同期区間」を拾う設計ゆえ広いのは仕様通り**だが、salience の選択性は q95 より大幅に低い。
- → 「5%固定と違う像が出た」(出口a) は成立。ただし**違いの方向は「より広く・選択性が低い」**＝Taka が「閾値内部化＝多様性拡張」として採るか、「salience は rare であるべき」として N を上げる/別定義にするかの判断材料（判定しない）。

## 4. 健全性 sanity check（主題の出口にしない）
- **健全性1**：persistence salience の空振り cid = **0**（全 n_core・全面適用の前提成立）。
- **健全性2**：persistence salience 行は**全件 hosted_available**（v1303c と同じ性質・ghost/reaped=0）。
- **健全性3**：persistence vs q95 Jaccard を n_core 別記録（0.115–0.123＝多様性拡張の像・新発見扱いしない）。

## 5. 【ユーザ重視】説明可能性ルーブリック 実装後突合（全項目 PASS）
| 検証項目 | 確認内容 | 結果 |
|---|---|---|
| persist_rows_all_ge_median | persistence 行は全て θ≥cid中央値か（持続区間の定義） | **True** |
| all_segments_ge_N | 各 segment が連続3点以上か | **True** |
| event_source_all_template | 全行 event_source が手本タグ（離脱ポインタ） | **True** |
| all_hosted | 全行 hosted_available か | **True** |
| no_empty_cid | 空振り cid なし（全面適用の前提） | **True** |
| event_type_single | event_type 単一（persistence版で統一） | **True** |
→ 6項目すべて PASS。生成物が操作定義通り（強引な解釈なし）を実装後に機械検証。

## 6. 言えること / 言えないこと
- **言える（観察事実）**：θ高同期閾値を内部履歴由来 persistence（θ≥中央値 連続3点）に置換でき、全 cid 空振りなく salience を拾え、5%固定 q95 とは Jaccard≈0.12 で**別の像（寿命の約45%の持続区間 vs 約5%の瞬間ピーク）**を生んだ。閾値の内部化（神の手を一つ外す）はできた。
- **言わない**：「persistence が優れている／正しい」「5%固定を倒した」「離脱できた」「ESDE が自律注意した」とは言わない。**これはθ系閾値の内部化であって非θ系=言語の離脱（v1303d 本筋）ではない**（persistence も θ の関数＝準同義反復の側面・隠さず明記）。salience が45%と広い点は事実として添え、選択性の評価は委ねる。

## 7. 規律遵守
- A型/#CW7: N=3・median は研究者選択ゆえ event_source 手本タグ（離脱ポインタ）。閾値内部化は多様性拡張の意図（神の手を厳格にしない・Taka方針）。
- L型: persistence を「離脱」「優れている」と言わない・θ系言い換えである点を明記・準同義反復を隠さない。
- D型: cid内中央値基準（cid局所主語）・全n_core機能の median 基準（q75 はn2空振りで不採用）・cid個別/n_core別。#11: persistence と q95 を合成せず比較・差分。
- #2/B型: 後処理のみ・write-back なし・親非書込。#12/J型: 判定せず観察事実のみ・seed0。F型: anchor=v105_v2。**結果を確定しにいかない**（v1303d の反省）。

## 8. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（persistence 定義・q95比較 Jaccard・全n_core空振り0・45%の広さの生データ再確認）→ Phase Result → Taka 主題評価。採否（persistence 版を salience の正式定義にするか・N を上げて選択性を上げるか・5%固定のままか）は Taka。

---

## 9. 一文サマリ
v1303e（判断A 全面適用・既存 ledger 後処理・再走/write-back なし・seed0・anchor v105_v2）でθ高同期手本の閾値を cid内q95上位5%固定から **persistence(θ≥cid中央値が連続3点持続＝Frozen age_r≥τ 同型の内部履歴由来閾値)** に置換し salience 25,568行/228cid/4,833segment を read-only 構成、**全cid空振り0・全hosted**で q95(5%)と **Jaccard≈0.12＝別の像（寿命の約45%の持続区間 vs 約5%の瞬間ピーク）** を生み閾値の内部化はできた（出口a成立）、ただし**正直な注記＝persistenceは寿命の約45%を拾い q95の9倍広く「rare な際立ち」としては選択性が大幅に低い**（多様性拡張として採るか N上げ/別定義かは Taka判断材料）、健全性1(空振り0)・2(全hosted)・3(Jaccard 0.115-0.123 記録)、**説明可能性ルーブリック6項目を実装後 verify_rubric() で全PASS**（persist行全てθ≥中央値・全segment≥3点・event_source手本タグ・全hosted・空振りなし・event_type単一）、L型厳守＝**これはθ系閾値の内部化であって非θ系=言語の離脱ではない**（persistenceもθの関数＝準同義反復を隠さず明記）・「persistenceが優れている/5%固定を倒した/離脱できた」とは言わない、結果を確定しにいかない、判定は Web Claude/Taka。
