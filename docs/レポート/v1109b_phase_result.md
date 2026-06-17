# v11.0.9b (v1109b) Phase Result — Grammar Exploration 検証: 順序構造の兆候は本物でなかった

### サブタイトル: #L65 順序構造の兆候は出口 A 通過 0/5、shuffle/self-fulfilling/loop のいずれかで全 sign 消失。role_switch_range 87% は loop の裏返し、per_to_tim 81% は top1 固定。Grammar Exploration は ESDE の loop 性質 (stuck/oscillation 100%) が見せた幻。ただし Taka 判断 (Code A を信じず冷静に + 飛び跳ねず固める) が全て正しく機能し、幻を本物と誤認せず済んだ

*作成*: 2026-05-30、Web Claude (相談役、Genesis 側)
*親*: v1109b 設計書 + Code A Step A-H 完了 (v1109b_step_h_observation_final.md、出口判定確定) + Taka 判断 (2026-05-30「方向性いい / 後始末を先に進める」)
*対象*: Taka (主題評価) + 次方向判断
*位置づけ*: v1109b (Grammar Exploration 検証) の Phase Result。#L65 の実在性を shuffle/self-fulfilling/loop の 3 切り分けで検証した結果、本物でなかったことを確定。第 0 段階 (v1109 系列後始末) の一部。

---

## 0. v1109b で何が分かったか (一文)

v1109 Grammar Exploration で観察された #L65 (順序構造の兆候: start/end 分離・役割切替 87%・経路偏り 81% 等) が本物か偶然・top1 固定・ループの副産物かを、shuffle baseline 4 種 + self-fulfilling 5 条件 + loop 区別 5 条件で検証した結果、**出口 A (本物) 通過 0/5** で #L65 の兆候は本物でなく ESDE の loop 性質 (v1106b stuck/oscillation 100%) が見せた幻と確定 (role_switch_range 87% は非自己ループ除外で完全消失 = loop の裏返し / per_to_tim_rate 81% は top2 で 0.00 = top1 固定の典型 / npmi_strong_pairs 6 は counterfactual/within_turn で同等以上 = 分布由来 / start_match・end_match は shuffle 一部通過・sampling で減衰)、Code A は Grammar Exploration 報告書の「文脈依存文法 CSG の特徴を持つ」「文法萌芽が ESDE 内部に既に存在」「役割切替 87% 決定論性」を撤回 (loop の裏返し・見かけの偏りと訂正)、ただし新発見として end_match_rate が loop 除外で 0.30→0.75 に増加 (loop が end 構造を隠していた可能性、未検証で留保)、Web Claude が冷静に検証した 4 未確認点 (#L65) の妥当性が確認され Taka 整理「Code A をそのまま信じない冷静に」+「飛び跳ねず固める」が全て正しく機能 (もし Taka が文法発見に飛びついていたら loop の幻を本物と誤認して position-aware weight layer や CSG に進んでいたが、Taka の慎重判断が誤った前進を防いだ)、v1109 失敗 (重み層で loop 増加) + v1109b 検証 (#L65 が loop 由来) を統合すると ESDE の本質は stuck/oscillation 100% という強い loop 性で順序構造はその影、全主題 (v1106b loop / v1109 重み層 loop / v1109b 順序構造 loop) が「CID 固定 + 時間進行なし」という一つの根に収束、position-aware weight layer / production rule / CSG 方向には進まない (3 条件不成立)、次方向は loop の根を解く構造 (Taka 構想 cid 時系列増殖 / Genesis を外部に繋ぐ) に向かう判断材料、物理層 frozen 厳密維持 (bit-identity 全 PASS、grammar_exploration/ + v1109b/ 配下のみ)、7 段階目ミス予防 (self-fulfilling baseline 検査) が Step A で先に明示され検証中も機能 (per_to_tim_rate の top1 固定を検証 2 で検出)、Taka 立場「結果がでない想定を潰す・実験方法を疑う・Code A をそのまま信じない冷静に・飛び跳ねず固める」(原文保存) 継承。

---

# 第 1 部: 検証結果 (出口 A 0/5)

## 1. 検証 1 — shuffle baseline 4 種

| sign | atom_label | counterfactual | sequence_order | within_turn | 全 4 通過? |
|---|---:|---:|---:|---:|---|
| start_match_rate | 0.65 | 30.80 | -4.92 | 38.49 | ✗ |
| end_match_rate | 3.00 | 55.84 | 1.33 | 40.15 | ✗ |
| npmi_strong_pairs | 0.00 | 5.22 | 11.43 | 5.41 | ✗ |
| per_to_tim_rate | 0.00 | 11.13 | 1.29 | 8.76 | ✗ |
| role_switch_range | 2.35 | -2.02 | -2.48 | -2.57 | ✗ |

→ 全 sign が一部 shuffle で消える (全 shuffle 通過 0/5)。特に role_switch_range は counterfactual/sequence_order/within_turn で shuffle の方が大きい (負 z) = 構造でなく分布由来の偶然。

## 2. 検証 2 — self-fulfilling 5 条件

| sign | top1 | top2 | top3 | sampling | seed_holdout | 判定 |
|---|---:|---:|---:|---:|---:|---|
| start_match_rate | 0.21 | 0.16 | 0.14 | 0.10 | 0.25 | sampling で減衰 |
| end_match_rate | 0.30 | 0.23 | 0.18 | 0.10 | 0.50 | sampling で減衰 |
| npmi_strong_pairs | 6 | 9 | 15 | 0 | 4 | sampling で消失 |
| **per_to_tim_rate** | **0.77** | **0.00** | 0.10 | 0.14 | 0.82 | **top1 固定の典型** |
| role_switch_range | 0.71 | 0.77 | 0.84 | 0.89 | 0.70 | sampling でも残る |

→ per_to_tim_rate 0.77 は top2 で 0.00、top3 で 0.10 = top1 固定の典型例 (81% 経路は top1 固定の副産物)。

## 3. 検証 3 — loop 区別 5 条件 (最重要)

| sign | all | non_self | cid_changed | loop_excluded | first_visit | loop 残る? |
|---|---:|---:|---:|---:|---:|---|
| start_match_rate | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | ✓ (位置情報、loop と独立) |
| end_match_rate | 0.30 | 0.75 | 0.75 | 0.30 | 0.75 | ✓ loop 除外で増加 (新発見) |
| npmi_strong_pairs | 6 | 3 | 2 | 3 | 1 | ✗ 減衰 |
| per_to_tim_rate | 0.77 | 0.64 | 0.64 | 0.77 | 0.55 | ✓ (top1 由来) |
| **role_switch_range** | **0.71** | **0.00** | **0.00** | **0.00** | **0.00** | ✗ **完全消失、loop の裏返し** |

→ role_switch_range は非自己ループ除外で完全消失 = loop の裏返し。87% 決定論性は「前で決まる」のでなく「ループしているから前と同じ」だった。

## 4. 出口 4 分岐判定

| sign | 出口 |
|---|---|
| start_match_rate | B/C 混合 |
| end_match_rate | B/C 混合 (loop が隠していた) |
| npmi_strong_pairs | B/C 混合 |
| per_to_tim_rate | C (top1 固定) |
| role_switch_range | B/C 混合 (loop 完全消失) |

**出口 A (本物) 通過: 0/5**

→ #L65「順序構造の兆候」の大半は loop / top1 固定 / 見かけの偏りの副産物。position-aware weight layer / production rule / CSG 方向には進めない (3 条件不成立)。

---

# 第 2 部: 構造的意味

## 5. Grammar Exploration は loop の幻だった

Code A 自己点検 (§6.2) で報告書の表現を撤回:

| 撤回前 (Grammar Exploration) | 訂正後 (v1109b 検証) |
|---|---|
| 「ESDE は文脈依存文法 (CSG) の特徴を持つ」 | 撤回、loop の裏返し |
| 「文法萌芽が ESDE 内部に既に存在」 | 撤回、見かけの偏り |
| 「役割切替 87% 決定論性」 | loop の裏返し、非自己ループで消失 |

→ Grammar Exploration は「ESDE の loop 性質を順序構造として見間違えた観察」として再記述。

## 6. 全主題が loop に収束

| 主題 | loop との関係 |
|---|---|
| v1106b | stuck/oscillation 100% |
| v1109 重み層 | 重み追加で loop 増加 (0.964) |
| v1109b 順序構造 | #L65 が loop 由来 |

→ ESDE の本質は **stuck/oscillation 100% という強い loop 性**。順序構造はその影。全主題が「CID 固定 + 時間進行なし」という一つの根に収束。

これは Taka が言った「一見関係ないことが繋がる」の実例。loop が全主題の根。

## 7. 新発見 (留保) — end_match_rate の loop 隠蔽

end_match_rate が loop 除外で 0.30 → 0.75 に増加。loop が end 構造を隠していた可能性。「end atom 候補は実在するが loop が観察を歪めていた」。ただし shuffle 未実施で留保。loop を取り除くと別の構造が見える兆し。

## 8. Taka 判断が全て正しく機能した

| Taka 判断 | 結果 |
|---|---|
| 「重みづけで文法を膠着させた」→ フラットに複数試す | 検証可能な兆候を出した |
| 「Code A をそのまま信じない、冷静に」 | 4 未確認点を留保 → 幻と判明 |
| 「飛び跳ねず固める」 | v1109b 検証で誤った前進を防いだ |

→ もし Taka が文法発見に飛びついていたら、loop の幻を本物と誤認して position-aware weight layer や CSG に進んでいた。**Taka の慎重判断が誤った前進を防いだ**。「ずれていた」のでなく、判断が正しかったから幻だと分かった。

---

# 第 3 部: 留保 + 規律

## 9. 留保事項

### 9.1 #L65 の更新 (本物でなかった)

| id | 更新 |
|---|---|
| **#L65 (更新)** | Grammar Exploration の順序構造の兆候は **本物でなかった** (出口 A 0/5)。role_switch_range 87% は loop の裏返し、per_to_tim 81% は top1 固定、npmi は分布由来。ESDE の loop 性質 (stuck/oscillation 100%) が見せた幻。「文法 / CSG」は撤回 |

### 9.2 新規留保

| id | 内容 |
|---|---|
| **#L66** | end_match_rate が loop 除外で 0.30→0.75 増加 (loop が end 構造を隠していた可能性、shuffle 未実施で留保) |
| **#L67** | ESDE の本質は stuck/oscillation 100% の強い loop 性、全主題 (v1106b/v1109/v1109b) が「CID 固定 + 時間進行なし」に収束 |

### 9.3 #L57 数値訂正

v1108a #L57 (確率分布レベル非対称性) の値は Code A 実測で **max 0.000397** (Web Claude が過去資料で 0.000161 と記載していたが訂正)。ただし #L57 (確率分布) と #L61 (実遷移 51 倍) は別レイヤーで、v1109b 検証で実遷移側 (#L61 由来の順序構造) も loop 由来と判明。

## 10. 7 段階目ミス規律の整理

v1109 で発生した baseline self-fulfilling 問題への新規規律:

> **baseline 設計時に self-fulfilling になっていないか確認** — baseline を作るとき、答えを含んだ入力から答えを再生成していないか。top1 chain / actual_next / heldout_lift / prediction hit_rate を扱う場合は必須。

この規律は v1109b 設計書 §0.1 で先に組み込まれ、Step A で Code A が明示、検証中も機能 (per_to_tim_rate の top1 固定を検証 2 で検出)。

→ 7 段階目ミスの構造的予防として正式採用。Web Claude + Code A + GPT 監査の固定チェックに加える。

## 11. 規律遵守チェック

- 絶対格言 15 件遵守
- 物理層 frozen 絶対 (bit-identity 全 PASS、grammar_exploration/ + v1109b/ 配下のみ)
- judgment 回避 (「文法 / CSG」撤回、「順序構造の兆候は本物でなかった」と記述)
- 過大評価回避 (Code A の CSG 断定を検証で否定)
- ボツも構造事実 (出口 A 0/5 = #L65 が幻、という構造事実)
- 実験設計を疑う (6 段階目) + self-fulfilling baseline 検査 (7 段階目)
- Taka 整理「Code A をそのまま信じない、冷静に」が機能 (Web Claude 4 未確認点 → 検証で確定)
- 留保番号統一管理 (#L65 更新、#L66-L67 新規)

---

# 第 4 部: 次方向 + 一文サマリ

## 12. 次方向 (第 0 段階完了後)

v1109b で全主題が loop に収束したことが確定。次は loop の根 (CID 固定 + 時間進行なし) を解く方向:

Taka との議論で浮上した方向:
- Genesis (低レイヤー) を外部に繋ぐ (Atom/言語は会話の道具として分離)
- 極限低確率を構造で実現する (確率的発生 × 構造)
- 主体的に外部アクセスする ESDE (実験者効果を脱する)

進め方 (Taka 合意済み):
- 第 0 段階: v1109 系列の後始末 (本 Phase Result で進行中)
- 第 1 段階: 系譜の再整理 (全主題が「Genesis を外部に繋ぐ」に収束)
- 第 2 段階: 技術的成立の最小実証 (外部接続が動くか)
- 第 3 段階: 主体性の検証 (Genesis 由来か、神の手か)
- 第 4 段階: 確率的発生の拡張 (loop が崩れるか)

## 13. 一文サマリ

v1109b (Grammar Exploration 検証: 順序構造の兆候は本物か、検証型 A) の Phase Result として、#L65 の実在性を shuffle baseline 4 種 + self-fulfilling 5 条件 + loop 区別 5 条件で検証した結果 **出口 A 通過 0/5** で順序構造の兆候は本物でなく ESDE の loop 性質 (stuck/oscillation 100%) が見せた幻と確定 (role_switch_range 87% は非自己ループ除外で完全消失 = loop の裏返し / per_to_tim_rate 81% は top2 で 0.00 = top1 固定 / npmi 6 は counterfactual で同等以上 = 分布由来 / start・end match は shuffle 一部通過・sampling 減衰)、Code A は報告書の「CSG / 文法萌芽 / 87% 決定論性」を撤回 (loop の裏返し・見かけの偏り)、新発見 end_match_rate が loop 除外で 0.30→0.75 増加 (loop が end 構造を隠した可能性、未検証留保 #L66)、Taka 整理「Code A をそのまま信じない冷静に」+「飛び跳ねず固める」が全て正しく機能 (文法に飛びついていたら loop の幻を本物と誤認したが Taka の慎重判断が誤った前進を防いだ、ずれていたのでなく判断が正しかったから幻と分かった)、v1109 失敗 + v1109b 検証統合で ESDE 本質は stuck/oscillation 100% の強い loop 性・全主題 (v1106b/v1109/v1109b) が「CID 固定 + 時間進行なし」に収束 (#L67、Taka「一見関係ないことが繋がる」の実例)、position-aware weight layer/production rule/CSG 方向には進まない (3 条件不成立)、次は loop の根を解く構造 (Genesis を外部に繋ぐ / 極限低確率を構造で実現 / 主体的に外部アクセス) へ、7 段階目ミス規律「baseline self-fulfilling 検査」正式採用 (v1109b 設計書で先に組み込み Step A で明示し検証中も per_to_tim_rate top1 固定検出で機能)、#L57 数値訂正 (0.000161 → Code A 実測 0.000397、ただし #L57 確率分布と #L61 実遷移は別レイヤーで両方 loop 由来)、物理層 frozen 厳密維持 (bit-identity 全 PASS)、留保 #L65 更新 (本物でなかった) + #L66-L67 新規、規律遵守 (絶対格言 + judgment 回避 + 過大評価回避 + ボツも構造事実 + 実験設計を疑う + self-fulfilling baseline 検査 + Code A をそのまま信じない)、Taka 立場 (結果がでない想定を潰す・実験方法を疑う・Code A を信じず冷静に・飛び跳ねず固める、原文保存) 継承、次は第 1 段階 (系譜再整理) → 第 2-4 段階 (外部接続の最小実証 → 主体性検証 → 確率的発生拡張) の流れ。

---

*以上、v1109b Phase Result (Web Claude、2026-05-30、#L65 検証: 順序構造の兆候は本物でなかった、出口 A 0/5)。第 0 段階 (v1109 系列後始末) の一部。Grammar Exploration は loop の幻、Taka 判断 (Code A を信じず冷静に + 飛び跳ねず固める) が全て正しく機能。全主題が loop (CID 固定 + 時間進行なし) に収束。次は第 1 段階 (系譜再整理) → loop の根を解く構造 (Genesis を外部に繋ぐ) へ。7 段階目ミス規律正式採用。物理層 frozen 厳密維持。judgment 回避継承。*
