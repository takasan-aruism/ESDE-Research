# v1303f 注意センター統合 Phase1 — Now-event(canonical再構成)+Archive-persistence 観察事実報告

*作成*: 2026-06-30、Code A。
*位置づけ*: 注意センター統合方針（Web Claude）の Phase1 実装。**Taka 判断（v1114=spec化・別run JSONは不使用・canonical再構成）を受け、一括せず Step B1(再構成)→B2(統合)を逐次自己チェックで実装。** 後処理のみ・物理非書込・判定なし（#12）。判定は Web Claude / Taka。
*成果物*: `v1303f_now_events.py`(B1) / `v1303f_attention_center.py`(B2) / `outputs/v1303f/v1303f_now_events_seed0.parquet` / `v1303f_attention_center_seed0.parquet`(33,885行) / `v1303f_distributions.html` / Step A `v1303f_stepA_preinvestigation.md`。

---

## 0. 統合方針の確定（Step A 報告→Taka 判断）
- **判断1=Yes**：v1114 の443 JSON 直接統合を止め、**canonical diag_v105_main_v2 から v1114 型イベントを再構成**（v1114=データ源→spec/参考実装）。理由：v1114 は別run・退化バグ・t曖昧（Step A で実証）。
- **判断2=No**：別run・退化承知の122共通cidは使わない。
- **判断3**：familiarity は canonical 優先（fam_edges）→ 取れた（37/228cid・限界タグ）。

## 1. Step B1 — Now-event の canonical 再構成（自己チェック済）
v1114 spec（step2a_live_observer.py の6トリガー delta 検出）を canonical ログに再適用：
| trigger | canonical ソース | 件数 |
|---|---|---|
| cid_birth | ledger 各cidの最初の hosted t | 228 |
| cid_death | per_subject host_lost_step | 191 |
| pulse | pulse_log [cid,t] | 12,530 |
| alpha_formation | alpha_lifecycle [event_type=birth, member_cids, step] | 1,067 |
| beta_formation | beta_lifecycle [member_cids, step] | 478 |
| c_conversion | c_trajectory [C_at_window_end 増, cid, step] | 582 |
- **計15,076イベント・全て v1303 の228宇宙内（宇宙外0）**＝別run混入なし（F型回避を実証）。
- hosted行への join 率 0.99–1.00（外れる131件は step10 丸めの端数で ±10 回収可）。t は全ログ tracking-step 域で ledger と同一原点（時間anchor確認済・G型なし）。

## 2. Step B2 — 統合レコード（Now/Archive を event_class 分離）
- **統合 33,885行 = now_event 15,076 + archive_persistence 18,809**、228宇宙、cid個別・n_core層化可能・合成なし。
- **point/neighborhood**：now_event に ledger から n_core/θ/rank_1/C/Q/phys_core_status/pulse_reactivity を付与。
- **【自己チェックで修正】death の point**：当初 death は host_lost_step=ghost行(θ NaN)に当たり θ付与=0.00 だった。hosted_available のみに絞り backward asof で「死ぬ直前の最後の hosted 状態」を付与する形に修正→ **death θ付与=1.00**。`point_source_t`/`point_lag` で point の出所 t を透明化（death は event_t と異なる＝最後の hosted t であることを隠さない）。
- **familiarity**（判断3・canonical fam_edges 最終スナップ）：37/228cid のみ（限界）。`familiarity_status` = canonical_final_snapshot / missing_no_fam_edge でタグ。統合レコードの familiarity_n notna=0.46。
- **Comparator前駆体**（v1114 EWMA+z）：trigger別 window 集計の `trigger_count_in_window`/`trigger_rate_ewma`/`z_like_deviation` を**監査列として残す**（判定に使わない・GPT）。z med 0.27・範囲[-5.5,4.1]。
- **Comparator 本体**：`comparator_class` 列は**全 null（Phase2 土台のみ・4分類しない）**。

## 3. 検証ゲート（全PASS・想定通り動くことを機械確認してから完了）
| ゲート | 内容 | 結果 |
|---|---|---|
| gate1_all_in_universe | 全レコードが228宇宙内 | **PASS** |
| gate2_event_class_two | event_class は now_event / archive_persistence の2値 | **PASS** |
| gate3_now_point_joined | now_event の n_core 付与 >98% | **PASS** |
| gate3b_now_theta_joined | now_event の θ 付与 >98%（death も最後のhostedで付く） | **PASS** |
| gate4_no_composite_col | 合成スコア列なし（#11） | **PASS** |
| gate5_raw_audit_present | EWMA+z 監査列あり（独立検証可能） | **PASS** |
| gate6_comparator_scaffold_only | comparator_class 全null（4分類しない） | **PASS** |
| gate7_familiarity_tagged | familiarity 出所タグ付き | **PASS** |

## 4. 言えること / 言えないこと（GPT・Phase1 厳守）
- **言える（観察事実）**：過去（v1114 のイベント駆動設計）と現在（v1303e の持続）の際立ちを、**同じ v105 seed0 の228 CID宇宙上で event_class（now_event / archive_persistence）に分けて1体系の read-only 統合レコードに並べられた**。v1114=spec として6トリガーを canonical から t付き・宇宙整合で再構成し、別run/退化/t曖昧を回避。EWMA+z は監査列として保持（前駆体）。
- **言わない**：「注意センターが統合された」「Comparator が成立した」「CID が自律的に注意した」「Atom 意味理解が始まった」とは言わない。Phase1 は「過去と現在の際立ちを同じ CID 宇宙で event_class 分けて並べた」まで。Comparator 4分類は Phase2。

## 5. 限界（隠さず明記）
- **familiarity は 37/228cid のみ**（fam_edges 最終スナップ・静的・時間解像度なし）。残り missing。Phase2 で per-t familiarity 源を要検討。
- **death の point は「最後の hosted 状態」**（event_t と異なる・point_lag で明示）。死亡時点そのものの phys は存在しない（ghost）ため。
- **EWMA+z は前駆体**（簡易 novelty・Comparator 本体でない）・判定に使わない。
- **Atom接続（v1114 step2b）は未統合**（4月手定義投影の人工性ゆえ将来・限界タグ前提）。
- **seed0 のみ**。

## 6. 規律遵守
- 過去を無駄にしない（v1114 の6トリガー設計・familiarity・EWMA+z を spec 継承）・現在を主（Now/Archive/Comparator 3系分離が骨格）。物理非書込・後処理のみ・合成しない(#11)・n_core層化/cid個別・判定数値は監査rawで残すが判定に使わない・#12 判定せず観察事実のみ・F型回避（228宇宙統一）。
- **信頼問題の継続**：一括せず B1→B2 逐次・**自己チェックで death-θ の見かけ問題を捕捉し修正してから完了**（想定外で先に進まない）。

## 7. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（再構成の宇宙整合・t anchor・death point_source_t・familiarity限界・EWMA+z監査値の生データ再確認）→ Phase Result → Taka。Phase2候補：Comparator 4分類（Now event と Archive pattern の照合）・Now系に v1303e q95 瞬間を追加・familiarity per-t 源・Atom接続(限界タグ)。

## 8. 一文サマリ
v1303f 注意センター統合 Phase1（Taka判断=v1114 spec化・canonical再構成・後処理のみ・seed0・判定なし#12）── Step A で v1114 が別run(9cid が per_subject に不在)・t未保持・退化バグと判明したのを受け **v1114=データ源→spec化**、B1 で v1114 の6トリガー(birth/death/pulse/α/β formation/c_conversion)を canonical(pulse_log/lifecycle/c_trajectory/per_subject)から **t付き・228宇宙で15,076イベント再構成(宇宙外0=F型回避実証・hosted join 0.99-1.00・時間anchor全ログ tracking-step で同一原点)**、B2 で **Now-event(15,076)+Archive-persistence(v1303e 18,809)を event_class 分離した統合33,885行**に並べ point を ledger から付与(**自己チェックで death が ghost行に当たり θ=0.00 を検出→hosted-only backward asof で『死ぬ直前の最後のhosted状態』を付与しpoint_source_t/point_lagで透明化→death θ=1.00 に修正**)、familiarity は canonical fam_edges(37/228cid・限界タグ)、EWMA+z は監査列(Comparator前駆体・判定に使わない)、comparator_class 全null(Phase2土台のみ・4分類しない)、**検証ゲート8項目 全PASS で『想定通り動く』を機械確認してから完了**、出口は「過去(v1114設計)と現在(v1303e持続)の際立ちを同じ228宇宙で event_class 分けて1体系に並べた」まで(注意センター統合成立/Comparator成立/自律注意/Atom理解 とは言わない)、限界(familiarity 37cid・death point=最後のhosted・EWMA+z前駆体・Atom未統合・seed0)を明記、過去を無駄にせず(spec継承)現在を主(3系分離)・信頼問題(一括せず逐次自己チェックで修正してから完了)、判定は Web Claude/Taka。
