# v1109b Step H — 観察事実最終報告

**Date**: 2026-05-30
**Author**: Code A
**Status**: Step A-G 完了、**出口判定確定**

---

## 0. 全 Step 完了

| Step | 内容 | 結果 |
|---|---|---|
| A | 認識確認 + 6 項目チェック | OK |
| B | 環境準備 (#L65 サンプル数) | n=4-307、小さい兆候は留保 |
| C | shuffle baseline 4 種 | **全 sign が一部 shuffle で消える** |
| D | self-fulfilling 5 条件 | **per_to_tim_rate に top1 固定確認** |
| E | loop 区別 5 条件 | **role_switch_range は loop 除外で完全消失** |
| F | 出口 4 分岐判定 | **A 通過 0/5** |
| G | bit-identity | 全 PASS (物理層 1 byte も侵さず) |

---

## 1. 検証 1 (shuffle baseline 4 種) 結果

| sign | atom_label | counterfactual | sequence_order | within_turn | 全 4 通過? |
|---|---:|---:|---:|---:|---|
| start_match_rate | 0.65 | **30.80** | -4.92 | **38.49** | ✗ |
| end_match_rate | 3.00 | **55.84** | 1.33 | **40.15** | ✗ |
| npmi_strong_pairs | 0.00 | **5.22** | **11.43** | **5.41** | ✗ |
| per_to_tim_rate | 0.00 | **11.13** | 1.29 | **8.76** | ✗ |
| role_switch_range | **2.35** | **-2.02** | **-2.48** | **-2.57** | ✗ |

→ **全 sign が一部 shuffle で消える** (全 shuffle 通過は 0/5)

特に role_switch_range は counterfactual/sequence_order/within_turn で **shuffle の方が大きい** (負 z) → **構造でなく分布由来の偶然**

---

## 2. 検証 2 (self-fulfilling) 結果

| sign | top1 | top2 | top3 | sampling | seed_holdout | 判定 |
|---|---:|---:|---:|---:|---:|---|
| start_match_rate | 0.21 | 0.16 | 0.14 | 0.10 | 0.25 | sampling で減衰 |
| end_match_rate | 0.30 | 0.23 | 0.18 | 0.10 | 0.50 | sampling で減衰 |
| npmi_strong_pairs | 6 | 9 | 15 | **0** | 4 | sampling で消える |
| **per_to_tim_rate** | **0.77** | **0.00** | **0.10** | 0.14 | 0.82 | **★ top1 固定の典型** |
| role_switch_range | 0.71 | 0.77 | 0.84 | 0.89 | 0.70 | ✓ sampling でも残る |

→ **per_to_tim_rate 0.77** は top2 で 0、top3 で 0.10 になる **top1 固定の典型例**

---

## 3. 検証 3 (loop 区別) 結果 — **最重要**

| sign | all | non_self | cid_changed | loop_excluded | first_visit | loop 残る? |
|---|---:|---:|---:|---:|---:|---|
| start_match_rate | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | ✓ (位置情報、loop と独立) |
| end_match_rate | 0.30 | **0.75** | **0.75** | 0.30 | **0.75** | ✓ **loop 除外で増加** (新発見) |
| npmi_strong_pairs | 6 | 3 | 2 | 3 | 1 | ✗ 減衰 |
| per_to_tim_rate | 0.77 | 0.64 | 0.64 | 0.77 | 0.55 | ✓ (top1 由来) |
| **role_switch_range** | **0.71** | **0.00** | **0.00** | **0.00** | **0.00** | ✗ **完全消失、loop の裏返し** |

→ **role_switch_range は loop の裏返し** (非自己ループで完全に消える)
→ end_match_rate が loop 除外で **増加** = loop が end_match を隠していた (新発見、副産物観察)

---

## 4. 出口 4 分岐判定 (Step F)

| sign | 出口 | 理由 |
|---|---|---|
| start_match_rate | **B/C 混合** | loop 残るが sampling で減衰、shuffle 一部通過 |
| end_match_rate | **B/C 混合** | loop 除外で増加 (loop が隠していた) |
| npmi_strong_pairs | **B/C 混合** | loop 除外で減衰、sampling で消失 |
| per_to_tim_rate | **C (top1 固定)** | top1 0.77 → top2 0.00 の典型 |
| role_switch_range | **B/C 混合** | loop 除外で完全消失 |

**出口 A (本物) 通過: 0/5**

→ **#L65 「順序構造の兆候」の大半は loop / top1 固定 / 見かけの偏りの副産物**
→ position-aware weight layer / production rule / CSG 方向には進めない (3 条件不成立)

---

## 5. 統合構造観察

### 5.1 確認された事実
1. **「順序構造の兆候」(#L65) は実在せず**、loop / top1 固定 / 分布バイアスの副産物
2. **role_switch_range 87% は loop の裏返し** (非自己ループで 0 になる)
3. **per_to_tim_rate 81% は top1 固定の副産物** (top2 で 0)
4. **npmi_strong_pairs 6 は分布由来** (counterfactual/within_turn で同等以上)

### 5.2 新発見 (Step E)
- **end_match_rate が loop 除外で 0.30 → 0.75 に増加**
- これは loop が end_match を隠していた、loop 除外すると end atom がより一貫
- → 「end atom 候補は実在するが、loop が観察を歪めていた」可能性
- ただしこれも shuffle 検証必要 (今回未実施)

### 5.3 v1109 失敗 + v1109b 検証の意味

v1109: 重み層追加で loop が増えた → 「重み機構の問題」と書いた
v1109b: #L65 が loop 由来 → **元から loop 構造が観察を支配していた**

→ Grammar Exploration は「ESDE が文法萌芽を持つ」ように見えたが、実態は **stuck/oscillation 100% という loop 性質が見せた幻**

---

## 6. Code A 自己点検 (重要)

### 6.1 7 段階目ミス予防は機能した
- v1109 で踏んだ self-fulfilling baseline 問題を Step A で先に明示
- 検証 1-3 で baseline と比較量の独立性を逐次チェック
- 結果: per_to_tim_rate が top1 固定の典型と検出できた (検証 2 で発見)

### 6.2 Grammar Exploration 統合報告書の表現訂正必要

私の `grammar_exploration_results.md` で書いた:
- 「ESDE は文脈依存文法 (CSG) の特徴を持つ」 → **撤回必要、loop の裏返し**
- 「文法萌芽が ESDE 内部にすでに存在」 → **撤回必要、見かけの偏り**
- 「役割切替 87% 決定論性」 → **loop の裏返し、非自己ループで消える**

訂正版: Grammar Exploration は **「ESDE の loop 性質を順序構造として見間違えた観察」** として再記述

---

## 7. 次の方向候補

| 候補 | 内容 |
|---|---|
| (α) end_match_rate loop 隠蔽の追検証 | loop 除外で 0.30→0.75 は新事実、shuffle/sampling で再検証 |
| (β) loop 自体の構造解析 | ESDE の loop 性質 (v1106b stuck 100%) を直接研究 |
| (γ) 文法方向は時期尚早として撤退 | Grammar Exploration を「見かけの偏り」として留保、別主題へ |
| (δ) Taka 構想 (cid 時系列増殖、注目マーカー) | loop の根本原因 (CID 固定 + 時間進行なし) を解く方向 |

---

## 8. bit-identity

| LAYER | 結果 |
|---|---|
| A (出力存在) | 全 5 ファイル ✓ |
| B (物理層 frozen) | 5 root 全て不変 ✓ |
| C (書込みパス) | 5 / 5 unified/v1109b/ 配下 ✓ |

**all_layers_pass = True**、**物理層 1 byte も侵さず**

---

## 9. 結論

**#L65「順序構造の兆候」は本物ではない、loop / top1 固定 / 分布偶然の副産物**

- 出口 A (本物) 通過: **0/5**
- 全 sign が shuffle / sampling / loop 除外のいずれかで消える
- 特に role_switch_range は loop の典型的裏返し

→ **position-aware weight layer / production rule / CSG 方向には進まない**
→ Grammar Exploration 報告書の「文法萌芽」表現を撤回
→ end_match_rate の loop 隠蔽は新発見、別途検証候補

### Code A から Taka への報告
v1109b は **Grammar Exploration の「文法萌芽」発見を否定**する結果。Web Claude が冷静に検証した #L65 の妥当性が確認された (大半 loop/top1 由来)。

ただし「ESDE は文法を持たない」と断定するのではなく、「**Grammar Exploration の集計方法が loop に支配された**」が正確。loop 自体を解く構造 (Taka 構想: cid 時系列増殖) に向かう判断材料。

---

**Step H end. 出口 D 寄り判定、Web Claude Phase Result 着手判断材料を提供。**
