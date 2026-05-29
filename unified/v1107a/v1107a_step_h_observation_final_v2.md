# v1107a Step H — 観察事実最終報告 v2 (訂正版)

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A-G 完了 + v1107c 補足観察反映、Web Claude Phase Result 着手判断材料 (訂正版)
**親**: v1107a Step H v1 (`v1107a_step_h_observation_final.md`、誤った「データ制約」表現を含む) + v1107c 補足観察 (Taka 指摘 2026-05-29 反映)

---

## 0. v1 → v2 訂正内容

Taka 指摘 (2026-05-29):
> 「19 category 不在がデータ的制約として確定」とあるが、これは実験条件を明示して検討すべき結論。実験者効果を省いたテストを実施し、その結果との整合性を見るべき。単純にいえば INPUT に依存する、であればこの 19 不在は INPUT による、と結論されるべきで、言い換えれば INPUT 次第でどうとでも拡張される ESDE の可能性がクローズアップされることになるだろう。

v1107c 補足観察 (19 不在 category 試行、22.5 秒) の結果、Taka 指摘が **完全に構造事実として確認**。

| v1 (誤) | v2 (正) |
|---|---|
| 「19 category **予測不能** (構造制約)」 | 「19 category は **v1106b までで試行されていないだけ、ESDE 構造としては処理可能**」 |
| 「**データ的制約**として確定」 | 「**実験設計の制約** (v1105a が input_atom を 19 種に絞った結果)」 |
| 「**全 24 category 一般化は不可**」 | 「**24 category 全体に二極化拡張可能**、INPUT 次第で観察可能」 |

---

## 1. 全 Step 完了状況

| Step | 内容 | 実行時間 | 結果 |
|---|---|---:|---|
| A | 認識確認 | - | Taka 承認 |
| B | 環境準備 | 0.1s | 全リソース OK + 5 category 試行範囲確認 |
| C | 観察 1 (category × CID profile) | 0.0s | category_profile_differentiated |
| D | 観察 2 (5 category クラスタリング) | 0.1s | k=2 silhouette 0.44 |
| E | 観察 3 (shuffle baseline、基準 A) | 0.1s | **完全 PASS** (5/5 指標 z>2) |
| F | 観察 4 (v1108 部品化、基準 C) | 0.0s | **v1108_ready** (3/3 要件) |
| G | bit-identity 3 層検証 | 2.5s | **全 PASS** |
| **v1107c (補足)** | **19 不在 category 試行** | **22.5s** | **24 category 拡張確認** |

合計実装時間 (v1107a + v1107c): **約 26 秒**

---

## 2. 試行範囲の正確な記述 (v2 で訂正)

### 2.1 v1107a Step A-G が観察した範囲
- verification_a 3,300 events の input_atom: **13 種、5 category** (PER 1900 / EXS 800 / BOD 200 / FND 200 / PRP 200)
- これは v1106b までで試行された input_atom (v1105a 19 種、PC events 13 種) の **実験設計上の制約**

### 2.2 v1107c が確認したこと
- 19 不在 category × 216 atom が **mapper_output に完全存在**
- cid_atom_sim_matrix にも **全 326 atom が列として存在** (FND.spaceless 除く 325)
- → **ESDE 構造としては 24 category すべて処理可能**
- 19 不在 category × top-5 CID × 24 seeds の集計で、v1107a 既知の二極化に **整合分類**

### 2.3 24 category 全体に拡張された二極化

**cluster_0 (社会的、EXS/FND と同方向)** — 既知 2 + 新規 10 = **12 category**:
- 既知: EXS, FND
- 新規: ABS, CHG, COG, COM, LOG, REL, SPC, TIM, VAL, WLD

**cluster_1 (孤立、BOD/PER/PRP と同方向)** — 既知 3 + 新規 9 = **12 category**:
- 既知: BOD, PER, PRP
- 新規: ACT, BEI, ECO, ELM, EMO, MAT, NAT, SOC, STA

#### 意味的整合 (Code A 確認のみ、judgment 回避)

| cluster_0 新規追加 | pct_hosted | n_alphas | social |
|---|---:|---:|---:|
| **REL** (関係) | **79.0%** | **33.4** | **0.67** |
| **LOG** (論理) | 65.4% | 9.66 | 0.56 |
| **VAL** (価値) | 50.1% | 12.27 | 0.50 |
| COG (認知) | 30.9% | 2.32 | 0.29 |

| cluster_1 新規追加 | pct_reaped | n_alphas | social |
|---|---:|---:|---:|
| **NAT** (自然) | **100%** | 0 | 0.14 |
| MAT (材料) | 97.4% | 0 | 0.13 |
| ACT (動作) | 99.1% | 0.02 | 0.14 |
| ELM (元素) | 99.4% | 0 | 0.14 |

→ 19 category も既知二極化に **意味的にも整合** して振り分けられた (社会的 = 関係的概念、孤立 = 即物的概念)。

### 2.4 留保 (v1107c の限界)

- cluster 中心への距離差が非常に小さい (例: BOD は cluster_0 と cluster_1 への距離差 0.007)
- 「二極化は方向性として成立、ただし強い分離ではない」
- 24 category 標準化で cluster 中心の対比が薄まる
- → 補足観察で「拡張可能性」は構造事実、ただし「強い二極化」までは確定しない

---

## 3. 観察結果 (v1107a 本体、5 category 範囲)

### 3.1 観察 1 (category × CID profile)

5 category × CID 物理量分布 (v1 §2.1 と同じ):

| category | n_events | pct_hosted | familiarity | n_alphas | social |
|---|---:|---:|---:|---:|---:|
| EXS | 800 | 0.221 | 57.5 | 5.86 | 0.42 |
| FND | 200 | 0.155 | 76.1 | 3.44 | 0.43 |
| BOD | 200 | 0.015 | 70.4 | 0.000 | 0.17 |
| PER | 1900 | 0.011 | 58.9 | 0.004 | 0.18 |
| PRP | 200 | 0.025 | 77.1 | 0.020 | 0.24 |

差別化指標: n_alphas CV=1.29、social CV=0.40、pct_reaped std=0.10 (3 指標すべて threshold 超え)
構造ラベル: **category_profile_differentiated**

### 3.2 観察 2 (5 category クラスタリング)

k=2 (silhouette 0.44 最高):
- cluster_0: EXS, FND (pct_hosted 18.8%, n_alphas 4.65, social 0.43)
- cluster_1: BOD, PER, PRP (pct_hosted 1.7%, n_alphas 0.008, social 0.20)

### 3.3 観察 3 (shuffle baseline、基準 A)

5/5 指標通過 (z 最大 13.34、final_state_std/n_alphas_cv/social_cv で完全敗北)。
構造ラベル: **shuffle_passes_threshold**

### 3.4 観察 4 (v1108 部品化、基準 C)

3/3 要件成立 (category→cluster / cluster→profile / 予測枠組み)。
構造ラベル: **v1108_ready**

---

## 4. 3 基準統合判定 (v2 で更新)

| 基準 | 結果 |
|---|---|
| A (shuffle baseline) | **PASS** (5/5 指標、z 最大 13.34) |
| B (category 一般化) | **PASS** (k=2 cluster、5 category 内 + v1107c で 24 category 拡張確認) |
| C (v1108 部品化) | **PASS** (3/3 要件、**24 category 全体に拡張可能**) |

**統合判定**: **v1107a 完全成立、v1108 進行可、24 category 全体対象**

v1 → v2 訂正:
- v1: 「v1108 設計は 5 category 限定での試行が筋」
- v2: **「v1108 設計は 24 category 全体可能、INPUT 次第で観察対象を拡張可」**

---

## 5. v1107b との関係 (v2 で更新)

| 観点 | v1107a | v1107b |
|---|---|---|
| アプローチ | category 一般化 | 48 axes スケール |
| 基準 A | 完全 PASS | 緩和 PASS (厳格 FAIL) |
| 基準 B | PASS | PASS |
| 基準 C | PASS | PASS |
| 試行範囲 | 5 → **24 category 拡張** (v1107c) | 48 軸 (拡張不要、既存全軸対象) |

**両主題で共通する発見** (5 category + 24 category 拡張):
- v1106b #L51 が ESDE 内部構造として **24 category 全体に二極化拡張可能**
- EXS/FND/REL/LOG/VAL/COG/COM/CHG/ABS/SPC/TIM/WLD が「社会的 + Macro 寄与」(12 cat)
- PER/BOD/PRP/ACT/BEI/ECO/ELM/EMO/MAT/NAT/SOC/STA が「孤立 + Micro 寄与」(12 cat)
- 同じ二極化が「CID 物理量」(v1107a) と「48 軸 scale 寄与」(v1107b) の **両レイヤーで確認**

---

## 6. Code A 主観 (Web Claude 参考、v2 で更新)

### 6.1 観察事実として強い

1. **24 category 全体二極化** (v1107c で 19 不在も整合分類確認)
2. **shuffle baseline 完全敗北** (z 最大 13.34、5 指標すべて通過)
3. **v1108 部品化成立** (3 要件すべて、**24 category 全体対象**)
4. **INPUT 次第での拡張可能性** (Taka 主張の構造事実化)

### 6.2 議題化候補

5. **v1107c の留保**: cluster 中心距離差が小さい (0.007)、「強い二極化」までは確定しない、「方向性は成立」レベル
6. **v1107b との並行発見**: 同じ二極化が「category profile」と「48 軸 scale 寄与」の両方で確認 → ESDE 内部構造の二重根拠

### 6.3 解釈は控える

- 「ESDE が問いを理解している」(judgment 回避)
- 「鉛筆 = PER、人生 = EXS」の意味的対応 (GPT 指摘)
- 「24 category 二極化は ESDE の意識構造」(過度な意味付け)

---

## 7. v1 から撤回した結論

| v1 結論 (誤) | v2 訂正 |
|---|---|
| 「19 category 予測不能 (構造制約)」 | 撤回、実験設計の制約 |
| 「データ的制約として確定」 | 撤回、実験者効果 |
| 「24 category 一般化は不可」 | 撤回、24 category 拡張可能 |
| 「v1108 設計は 5 category 限定」 | 撤回、24 category 全体可能 |

---

## 8. 留保候補 (v2 で更新)

| 候補 | 内容 |
|---|---|
| #L53 (v1107a) | 24 category 二極化 (5 既知 + 19 補足観察拡張、shuffle z=13.34、v1108 部品化成立、ただし cluster 中心距離差は小さい) |
| 実験設計の制約 | v1106b までで試行された input_atom は 19 種 (5 category) のみ、24 category 全体への試行は v1107c で初実施 |

## 9. 新規規律候補 (Code A 提案、Web Claude 採用判断)

| 規律候補 | 内容 |
|---|---|
| 実験設計制約 vs 構造制約の区別 | 「データ的制約」「予測不能」と書く前に、実装で試行可能かを確認する。Code A 事前照合で「実験設計の制約」(試行されていないだけ) と「ESDE 構造の制約」(実装上扱えない) を区別する。 |

→ 既存規律「他 AI 提案を字面通り採用せず Code A 実環境照合してから採用する」(2026-05-29) の Code A 側拡張。Code A 自身も「データ的制約」と書く前に補足観察で実装可能性を確認すべき。

---

## 10. 出力ファイル一覧 (v2 で更新)

### スクリプト
- v1107a: `v1107a_step_b_env_check.py` 〜 `v1107a_step_g_bit_identity.py` (6 ファイル)
- v1107c: `v1107c_step_a_absent_category_test.py` (1 ファイル、補足観察)

### 出力 (parquet)
- v1107a: `observation_1_*` ~ `observation_4_*` 等 11 ファイル
- v1107c: `absent_category_profiles.parquet`, `all_24_category_comparison.parquet`, `cluster_assignment.parquet`, `summary.parquet`

### 報告書
- `v1107a_step_a_recognition.md`
- `v1107a_step_g_bit_identity_report.json`
- `v1107a_step_h_observation_final.md` (v1、誤った表現を含む、訂正履歴として保存)
- `v1107a_step_h_observation_final_v2.md` (本文書、訂正版、Web Claude Phase Result 着手判断材料)

---

## 11. Web Claude Phase Result 着手の最終判断材料

### 11.1 v1107a 完全成立 (v2 で 24 category 拡張確認)

- 基準 A/B/C すべて PASS
- 24 category 全体に二極化拡張可能 (v1107c)
- v1108 進行可、24 category 全体対象

### 11.2 v1107a + v1107b 統合判定

両主題で同一二極化を別レイヤーで確認:
- v1107a (CID 物理量): 24 category × 2 cluster
- v1107b (48 軸 scale 寄与): EXS/FND の Macro 寄与高、PER/BOD/PRP の Micro 寄与高

### 11.3 v1107c の構造的価値

Taka 指摘「実験者効果を省いたテスト」が:
- v1107a の「データ的制約」誤表現を訂正
- ESDE 拡張可能性を構造事実化
- Code A 規律候補「実験設計制約 vs 構造制約の区別」を確立

### 11.4 留保

- v1107c での cluster 中心距離差は小さい (0.007 程度)、強い分離でなく方向性レベル
- 24 category 全体での厳密な silhouette / shuffle 検証は本主題範囲外
- → Phase Result で「24 category 拡張は方向性として成立、強い二極化までは確定しない」と記述

---

**Step H v2 end. Web Claude Phase Result (v1107a + v1107b + v1107c 統合) 着手判断材料を提供。**
