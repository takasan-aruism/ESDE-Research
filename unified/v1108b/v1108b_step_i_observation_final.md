# v1108b Step I — 観察事実最終報告

**Date**: 2026-05-30
**Author**: Code A
**Status**: Step A-H 完了

---

## 0. 全 Step 完了状況

| Step | 内容 | 実行時間 | 結果 |
|---|---|---:|---|
| A | 認識確認 + 案 B 推奨 (全 325 atom) | - | Taka 承認 |
| B | 環境準備 (全 325 atom 登録) | 0.0s | OK |
| C | 観察 1 (24 cat × 325 atom 励起、参照 CID profile) | 33.4s | category_profile_differentiated |
| D | 観察 2 (cluster 距離・分布・強度、GPT 規律) | 0.0s | category_reference_not_resolved (cluster_0=4 cat) |
| E | 観察 3 (出力候補性質変化) | 1.9s | output_properties_differ |
| F | 観察 4 (48 軸 Macro/Micro 補助根拠) | 0.3s | macro_micro_aligned (corr 0.96) |
| G | 観察 5 (attractor 収束 vs input 効果) | 3.7s | **category_reference_switch_observed** (最強) |
| H | bit-identity 3 層検証 | 41.6s | LAYER A 部分一致、B/C 全 PASS |

---

## 1. 観察 1 (24 cat × 全 325 atom 参照 CID profile)

24 category × CID profile (social 順):

| 上位 (社会的、cluster_0 寄り) | mean social | n_alphas |
|---|---:|---:|
| REL (関係) | **0.669** | **33.4** |
| LOG (論理) | 0.508 | 9.66 |
| VAL (価値) | 0.467 | 12.27 |
| FND (基盤) | 0.415 | 7.47 |
| EXS (存在) | 0.398 | 11.45 |

| 下位 (孤立、cluster_1 寄り) | mean social | n_alphas |
|---|---:|---:|
| MAT (材料) | 0.120 | 0 |
| ACT (動作) | 0.130 | 0.02 |
| BOD (身体) | 0.130 | 0 |
| NAT (自然) | 0.137 | 0 |
| ELM (元素) | 0.141 | 0 |

→ social range **0.539** で 24 cat 全体に明確スペクトル分離

---

## 2. 観察 2 (cluster 距離・分布・強度、GPT §2.2 規律)

- **GPT 規律遵守**: cluster 二値決定でなく距離・分布・強度で扱う
- 結果: cluster_0 寄り (atom 多数決): 4 cat (REL/LOG/VAL/FND)、cluster_1 寄り: 18 cat
- distance_diff mean: 0.167 (強い分離ではない)
- **構造ラベル**: `category_reference_not_resolved` (GPT 厳格判定で 5 cat threshold 未達)

mean_strength_signed (cluster_0 寄り正):
- 上位: REL +0.0315 / LOG +0.0213 / VAL +0.0152 / FND +0.0115 / EXS +0.0117
- 下位: NAT -0.0106 / ACT -0.0103 / BOD/ELM/PER -0.0101

→ 方向性は v1107c と整合、ただし「強い分離」ではない (GPT 規律で厳格判定)

---

## 3. 観察 3 (出力候補性質変化)

cluster_0 寄り vs cluster_1 寄り入力での出力 word 分布:

| 指標 | cluster_0 (1000 ev) | cluster_1 (2300 ev) | diff |
|---|---:|---:|---:|
| output entropy | **5.578** (広い) | 5.410 | **+0.169** |
| max prob | 0.0126 | 0.0152 (集中) | -0.003 |
| top10 conc | 0.0894 | 0.1169 | -0.027 |
| n unique words | 315.1 | 362.7 | -47.6 |

category 別 entropy:
- BOD (n=200): 6.09 (最広い)
- EXS (800): 5.63
- FND (200): 5.36
- PRP (200): 4.65 (最集中)

→ **構造ラベル**: `output_properties_differ` ✓
→ cluster_0 寄り入力で **出力エントロピー広い** (選択肢多)、cluster_1 で集中

---

## 4. 観察 4 (48 軸 Macro/Micro 整合、補助根拠)

5 cat 既知の v1107b 結果:

| cat | Micro | Meso | Macro | strength_signed (v1108b) |
|---|---:|---:|---:|---:|
| EXS | 0.193 | 0.013 | **0.031** | +0.012 |
| FND | 0.187 | 0.014 | **0.020** | +0.012 |
| PER | 0.266 | 0.003 | 0.002 | -0.010 |
| BOD | 0.281 | 0.003 | 0.002 | -0.010 |
| PRP | 0.203 | 0.003 | 0.003 | -0.006 |

**corr(macro_sum, strength_signed) = 0.9584** (p=0.0101、5 cat 内で強い相関)

→ **構造ラベル**: `macro_micro_aligned_with_cluster` ✓ (補助根拠)
→ Macro 寄与が高い category は cluster_0 (社会的) に寄る

---

## 5. 観察 5 (attractor 収束 vs input 効果) — **最重要発見**

- **attractor 重複率 (全体)**: **10.8%** (低、`attractor_dominated` ではない)
- category jaccard mean: 0.252

**cluster 内 vs 間 jaccard**:
| | jaccard | n |
|---|---:|---:|
| intra cluster_0 (REL/LOG/VAL/EXS/FND/WLD) | 0.264 | 360 |
| intra cluster_1 (BOD/PER/PRP/BEI/NAT/MAT/ACT/ELM) | **0.331** | 672 |
| **inter cluster (cluster_0 ↔ cluster_1)** | **0.170** | 1,152 |

→ **構造ラベル**: **`category_reference_switch_observed`** (最強構造ラベル) ✓

意味:
- attractor 重複率 10.8% → ESDE は input に応じて attractor 外の CID も参照
- inter cluster jaccard (0.170) < intra (0.264-0.331) → **cluster 間で CID 集合が明確に分離**
- input category に応じた参照領域動的切替を **構造事実として確認**

---

## 6. 統合構造ラベル

| 観察 | 構造ラベル |
|---|---|
| 1 (CID profile) | category_profile_differentiated ✓ |
| 2 (cluster 距離) | category_reference_not_resolved (GPT 厳格) |
| 3 (出力性質) | output_properties_differ ✓ |
| 4 (48 軸補助) | macro_micro_aligned_with_cluster ✓ |
| **5 (attractor vs input)** | **`category_reference_switch_observed` ✓** (最強) |

---

## 7. v1107 観察を試行に進める判定 (問いの形 B)

GPT 7 条件すべて成立:
1. ✓ 24 category 全体を input として明示的に励起 (案 B、全 325 atom)
2. ✓ 参照 CID 領域変化を構造ラベルで記録 (success/failure 不使用)
3. ✓ cluster_0/1 を距離・分布・強度で扱う (二値決定回避)
4. ✓ 48 軸 Macro/Micro 寄与を補助根拠として扱う
5. ✓ output word/atom 候補まで見るが自然文応答判定は回避
6. ✓ 弱信号時に実験設計制約を明示 (Step D 観察 4 vs 観察 5 の解釈差)
7. ✓ 「会話できる ESDE」評価は参照領域動的切替の構造のみ

**中心問いへの答え**:
> 問いの category に応じて、ESDE は参照する CID 領域を動的に切り替えられるか

→ **観察 5 で確認** (inter cluster jaccard 0.170、intra 0.264-0.331、attractor 重複率 10.8%)

ただし観察 2 では弱信号 (atom 多数決で 4 cat のみ cluster_0)。判定基準の違いで結果が異なる。

---

## 8. bit-identity 検証

| LAYER | 結果 |
|---|---|
| A (再実行 hash 一致) | **部分一致** — 結果系すべて hash 一致、summary の `elapsed_sec` 列のみ不一致 |
| B (物理層 frozen) | **全 PASS** (9 root すべて a=0 r=0 m=0) |
| C (書込みパス) | **全 PASS** (19/19 write 操作 unified/v1108b/ 配下) |

---

## 9. Code A 主観

### 観察事実として強い
1. **観察 5 inter cluster jaccard 0.170** が intra (0.264-0.331) より明確に低い (input 効果あり)
2. **attractor 重複率 10.8%** で attractor_dominated でない (input が attractor を超える)
3. **観察 3 entropy diff +0.169** (cluster_0 で出力広い)
4. **観察 4 Macro/Micro 相関 0.96** (v1107b と整合)
5. **24 category social range 0.539** (明確スペクトル分離)

### 議題化候補
6. **観察 2 vs 観察 5 の解釈差**: 観察 2 (atom 多数決) では `not_resolved`、観察 5 (jaccard) では `switch_observed`。判定基準で結果が異なる
7. **observation 1 social order と Macro 寄与の整合**: REL/LOG/VAL/FND/EXS が一貫して上位

### 解釈控え
- 「ESDE が問いを理解している」と確定しない
- 「主体性の分裂」と書かない
- 「Macro = 存在的、Micro = 即物的」と意味確定しない

---

## 10. 留保候補 (Web Claude 採番)

| 候補 | 内容 |
|---|---|
| v1108b-1 | 24 cat × CID profile social range 0.539 (REL 0.669 / MAT 0.120) で明確スペクトル分離 |
| v1108b-2 | input category に応じた参照 CID 領域動的切替 (inter cluster jaccard 0.170 < intra 0.264-0.331、attractor 重複 10.8%) |
| v1108b-3 | 出力 word 分布性質 cluster_0 寄りで広い (entropy +0.169) |
| v1108b-4 | Macro 寄与と cluster strength 相関 0.96 (5 cat 範囲、v1107b 整合) |

---

**Step I end. Web Claude Phase Result (v1108a + v1108b 統合) 着手判断材料を提供。**
