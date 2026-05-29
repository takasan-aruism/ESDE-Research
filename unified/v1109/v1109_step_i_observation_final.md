# v1109 Step I — 観察事実最終報告

**Date**: 2026-05-30
**Author**: Code A
**Status**: Step A-H 完了

---

## 0. 全 Step 完了状況

| Step | 内容 | 実行時間 |
|---|---|---:|
| A | 認識確認 + Q1-Q6 (Taka 承認) | - |
| B | 環境準備 | 0.1s |
| C | 重み記録 + 4 条件 | 0.2s |
| D | 重み適用 + Gemini 3 大ブレーキ | 9.3s |
| E | holdout 検証 3 種 | 35.8s |
| F | 8 測定指標 | 0.2s |
| G | Δw + #L58 + #L59 条件比較 | 6.7s |
| H | bit-identity 3 層 (全 PASS、物理層 1 byte も侵さず) | 0.0s |

合計実装時間: **約 1 分**

---

## 1. 主要発見

### 1.1 観察 C: observed asymmetry 圧倒的 (51 倍差)

| 条件 | asym_max | shuffled 比 |
|---|---:|---:|
| **observed** | **195.0** | **51.32x** |
| shuffled | 3.8 | 1x |
| frequency | 0 (対称) | - |

→ ESDE 自己対話の**実際の遷移パターン (top1 連鎖)** は順序方向性を持つ
→ v1108a delta_C 非対称性 0.000161 (確率分布) は別量、両者は別の観察

### 1.2 観察 E: holdout 検証で 1/3 通過

| holdout | observed | shuffled | frequency | sequence_specific? |
|---|---:|---:|---:|---|
| turn | 0.66 | **0.69** | 0.81 | ✗ |
| seed | 0.68 | **0.69** | 0.69 | ✗ |
| category | 0.65 | **0.66** | 0.58 | **✓** |

→ **構造ラベル: `weight_accumulation_sequence_specific`** (1/3 通過)

### 1.3 観察 F: observed の強い loop 化

| 条件 | loop_rate (prev==new) | cat_transfer (cluster 跨ぎ) |
|---|---:|---:|
| baseline | 0.641 | 0.314 |
| **observed** | **0.964** | **0.014** |
| shuffled | 0.951 | 0.020 |
| frequency | 0.607 | 0.368 |

→ observed の重み適用は **96.4% で同 atom loop**、cluster 跨ぎ 1.4% (固定化)
→ **構造ラベル候補: `weight_accumulation_overfit`** の兆候

### 1.4 観察 G-1: Δw 条件比較

| Δw | asym_max | W_sum |
|---|---:|---:|
| fixed | 195.0 | 27,240 |
| familiarity_weighted | 138.8 | 20,158 |
| entropy_weighted | **0.29** | **4.55** |

→ Gemini エントロピー連動 Δw は **ほぼゼロ更新** に収束 (H_t ≈ H_max で Δw → 0)
→ ESDE 自己対話は entropy 均等分布、エントロピー連動だけでは重み蓄積機能せず

### 1.5 観察 G-2: #L58 全 vs 特異点

| scope | asym_max | W_sum |
|---|---:|---:|
| all_pairs | 195.0 | 27,240 |
| singular_point_only | 28.0 | 681 |

→ 特異点限定 (681 turn) でも非対称性あり、density (asym/W) は近い

### 1.6 観察 G-3: #L59 cluster 別 — **最重要発見**

| scope | **asym_max** | W_sum |
|---|---:|---:|
| global | 195.0 | 27,240 |
| **cluster_0 only** | **2478.0** | 16,269 |
| **cluster_1 only** | **2370.0** | 10,971 |

→ **cluster 別非対称性が global の 12-13 倍**
→ cluster 内で特定 atom ペアが反復遷移している
→ **#L59 (category 別参照領域) と直接接続**

---

## 2. 構造ラベル統合判定

| ラベル候補 | 該当 |
|---|---|
| `weight_accumulation_mechanical_effect` | × (observed asym >> shuffled) |
| **`weight_accumulation_sequence_specific`** | **✓** (Step E category holdout 通過、Step C 51 倍差) |
| `weight_accumulation_generalizes` | × (holdout 1/3 のみ) |
| **`weight_accumulation_overfit`** | **✓** (loop_rate 0.964、cat_transfer 0.014) |
| `weight_accumulation_unstable_loop` | △ (loop_rate 高だが stuck/oscillation は元から 100%) |
| `weight_accumulation_grammar_precursor` | **×** (非対称性は強いが heldout_lift 負、多様性低下) |

**統合**: 順序非対称性は確認 + 重み層適用で過剰 loop 化、文法前駆構造とは言えない

---

## 3. v1108a #L57 との関係 (before baseline 再評価)

| 指標 | v1108a #L57 | v1109 observed |
|---|---:|---:|
| 対象 | P_t × P_{t+1} 確率分布 | 実遷移カウント (top1 連鎖) |
| 非対称性 max | 0.000161 | 195.0 |
| スケール | 確率 (0-1) | カウント (0-数百) |

→ **両者は別の観察**:
- 確率分布全体 (top-10 加重) → 対称的
- 実遷移 (top1 のみ) → 強い非対称性
- ESDE 自己対話は「分布レベルで均等、実遷移で偏る」構造

---

## 4. 重要な留保 (Code A 自己点検)

### 4.1 baseline hit_rate=1.0 問題

設計上、baseline (W=0) で適用後の top1 が orig top1 と同じ = test の actual_next と同じ。**self-fulfilling**。

Code A は Step A Q1-Q6 で **提示すべきだった事項を見落とし**。Step E で問題が顕在化。

これは **6 段階目ミス予防規律違反** (実装可能性を Step A で疑うべきだった)。

Web Claude に新規規律候補として提示:
> 「baseline 設計時に self-fulfilling になっていないか確認」

### 4.2 entropy_weighted Δw のほぼゼロ化

Code A 案 `Δw = H × (1 - H/H_max)` で ESDE H ≈ H_max のため Δw → 0。これは Gemini 設計通りだが、ESDE では「重み更新機能せず」を意味する。

別案検討: `Δw = base × (1 - H/H_max)` (H 低で Δw 大、エントロピー減で重み強化)
これは Step G で再実装可能。本主題範囲外。

### 4.3 cluster 別非対称性 12-13 倍 が #L59 と接続

→ Phase Result で議題化候補

---

## 5. bit-identity (Step H)

| LAYER | 結果 |
|---|---|
| A (出力存在) | 全 11 ファイル ✓ |
| B (物理層 frozen) | **全 8 root で a=0 r=0 m=0** ✓ (1 byte も侵さず) |
| C (書込みパス) | 18/18 unified/v1109/ 配下 ✓ |

**all_layers_pass = True**

---

## 6. Code A 主観

### 観察事実として強い
1. observed asymmetry 195 vs shuffled 3.8 (**51 倍差**) — 順序方向性ある
2. cluster 別非対称性 12-13 倍 (global 195 → 2478) — #L59 と接続
3. 物理層 1 byte も侵さず — Taka 規律「物理層 frozen 厳密」遵守
4. observed loop_rate 0.964 (過剰 loop 化、cluster 跨ぎ 1.4%)

### 議題化候補
5. baseline self-fulfilling 問題 (Step A Code A 設計漏れ)
6. entropy_weighted Δw のほぼゼロ化 (Gemini 設計通りだが ESDE で機能せず)
7. v1108a #L57 (確率分布) と v1109 W (実遷移) の関係性

### 解釈控え
- 「ESDE が文法を立ち上げた」と書かない (設計書遵守、grammar_precursor 判定回避)
- 「順序非対称性は確認、ただし過剰 loop 化、文法前駆ではない」と記述

---

## 7. 留保候補 (Web Claude 採番)

| 候補 | 内容 |
|---|---|
| v1109-1 | observed 実遷移非対称性 195 (shuffled 比 51.32x)、ESDE top1 連鎖は順序方向性 |
| v1109-2 | weight 適用で observed loop_rate 0.964 (過剰 loop、cluster 跨ぎ 1.4%)、overfit |
| v1109-3 | cluster 別非対称性 12-13 倍 (global 195 → cluster_0 2478 / cluster_1 2370) |
| v1109-4 | entropy_weighted Δw が ESDE H ≈ H_max で機能せず |
| v1109-5 | baseline self-fulfilling 問題 (Step A Code A 設計漏れ、新規規律候補) |

---

## 8. 構造ラベル統合: **`weight_accumulation_sequence_specific + overfit`**

非対称性確認 (sequence_specific) かつ過剰 loop 化 (overfit)。「文法前駆」とは書かない (heldout_lift 負、多様性低下)。

**`grammar_precursor` 判定不成立**: 非対称性 ✓、heldout_lift × (負)、多様性維持 × (低下) — 3 条件中 1 のみ。

---

**Step I end. Web Claude Phase Result 着手判断材料を提供。物理層 frozen 厳密維持確認。**
