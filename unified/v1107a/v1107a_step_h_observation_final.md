# v1107a Step H — 観察事実最終報告

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A-G 完了、Web Claude Phase Result 着手判断材料

---

## 0. 全 Step 完了状況

| Step | 内容 | 実行時間 | 結果 |
|---|---|---:|---|
| A | 認識確認 | - | Taka 承認 |
| B | 環境準備 | 0.1s | 全リソース OK + 構造制約発見 (5 category) |
| C | 観察 1 (category × CID profile) | 0.0s | category_profile_differentiated |
| D | 観察 2 (5 category クラスタリング) | 0.1s | k=2 silhouette 0.44 |
| E | 観察 3 (shuffle baseline、基準 A) | 0.1s | **完全 PASS** (5/5 指標 z>2) |
| F | 観察 4 (v1108 部品化、基準 C) | 0.0s | **v1108_ready** (3/3 要件) |
| G | bit-identity 3 層検証 | 2.5s | **全 PASS** (hash 一致 / frozen / 書込みパス) |

合計実装時間: **約 3 秒** (post-process のみ)

---

## 1. 構造制約 (Step B で発見、Step H 明示)

- verification_a 3,300 events の input_atom は **13 種のみ、5 category** (PER 1900 / EXS 800 / BOD 200 / FND 200 / PRP 200)
- 設計書「全 24 category 一般化」は **データ上不可、5 category 内一般化** に縮小
- v1106b までで試行された input_atom の制約 (v1105a 19 種、PC events 13 種)
- 19 category (ACT/CHG/CIM/COG/COM/ECO/ELM/EMO/EXS/LOG/MAT/NAT/REL/SOC/SPC/STA/SYM/TIM/VAL/WLD) は予測不能

→ **Phase Result で明示すべき構造事実**。

---

## 2. 観察結果

### 2.1 観察 1 (category × CID profile)

5 category × CID 物理量分布:

| category | n_events | pct_hosted | pct_reaped | familiarity | n_alphas | social |
|---|---:|---:|---:|---:|---:|---:|
| EXS | 800 | 0.221 | 0.751 | 57.5 | **5.86** | **0.42** |
| FND | 200 | 0.155 | 0.825 | 76.1 | **3.44** | **0.43** |
| BOD | 200 | 0.015 | 0.960 | 70.4 | 0.000 | 0.17 |
| PER | 1900 | 0.011 | **0.983** | 58.9 | 0.004 | 0.18 |
| PRP | 200 | 0.025 | 0.955 | 77.1 | 0.020 | 0.24 |

差別化指標:
- n_alphas CV = **1.29** (threshold 0.5) ✓
- social CV = **0.40** (threshold 0.1) ✓
- pct_reaped std = **0.10** (threshold 0.1) ✓
- 構造ラベル: **category_profile_differentiated**

### 2.2 観察 2 (5 category クラスタリング)

k=2 (silhouette 0.44 最高):
- **cluster_0**: EXS, FND (社会的)
  - pct_hosted 18.8%、n_alphas 4.65、social 0.43
- **cluster_1**: BOD, PER, PRP (孤立)
  - pct_hosted 1.7%、n_alphas 0.008、social 0.20

→ **v1106b #L51 二極化が 5 category 内で 「2 vs 3 構造」で構造的に一般化**

### 2.3 観察 3 (shuffle baseline、基準 A 判定)

| 指標 | 真 | shuffle mean | z スコア | paired rate | 通過 |
|---|---:|---:|---:|---:|---|
| final_state_std_max | 0.101 | 0.019 | **12.88** | 1.00 | ✓ |
| familiarity_cv | 0.123 | 0.052 | **2.33** | 1.00 | ✓ |
| n_alphas_cv | 1.287 | 0.261 | **8.97** | 1.00 | ✓ |
| social_cv | 0.399 | 0.067 | **13.34** | 1.00 | ✓ |
| silhouette_k2 | 0.439 | 0.263 | **2.00** | 1.00 | ✓ |

→ **基準 A 完全 PASS** (5/5 指標で z>2 AND paired>0.75)、構造ラベル `shuffle_passes_threshold`

### 2.4 観察 4 (v1108 部品化、基準 C)

3 要件すべて成立:
1. ✓ category → cluster マッピング (5 category)
2. ✓ cluster → CID profile (重み付き平均)
3. ✓ 予測枠組み (新規 input_atom 対 5 category 内なら予測可)

→ **基準 C 通過、構造ラベル `v1108_ready`**

ただし注意: 24 category 中 5 category のみ対応、19 category 予測不能 (構造制約)

---

## 3. 3 基準統合判定

| 基準 | 結果 |
|---|---|
| A (shuffle baseline) | **PASS** (5/5 指標、z 最大 13.34) |
| B (category 一般化) | **PASS** (k=2 cluster で 2 vs 3 二極化) |
| C (v1108 部品化) | **PASS** (3/3 要件、5 category 内) |

**統合判定 (Phase Result §2.4 表 1 行目)**: **v1107a 完全成立、v1108 進行可**

ただし v1108 設計時に注意:
- 「全 24 category」でなく「5 category (PER/EXS/BOD/FND/PRP) 内」での試行
- 19 category への一般化は v1106b までで試行されていないため不可

---

## 4. v1107b との関係

| 観点 | v1107a | v1107b |
|---|---|---|
| アプローチ | category 一般化 | 48 axes スケール |
| 基準 A | 完全 PASS | 緩和 PASS (厳格 FAIL: silhouette 弱) |
| 基準 B | PASS | PASS |
| 基準 C | PASS | PASS |
| 主要発見 | 2 cluster 構造 (EXS/FND vs BOD/PER/PRP) | category × Macro 寄与差別化 (EXS/FND の Macro 寄与が他より高) |

**両主題で共通する発見**:
- v1106b #L51 が 5 category 内で構造的に一般化
- EXS/FND が「社会的 + Macro 寄与」、PER/BOD/PRP が「孤立 + Micro 寄与」の **同一構造を別レイヤーで確認**

---

## 5. Code A 主観 (Web Claude 参考)

### 5.1 観察事実として強い (Phase Result で記述すべき)

1. **5 category 内二極化** (cluster_0 EXS/FND vs cluster_1 BOD/PER/PRP)
2. **shuffle baseline 完全敗北** (z 最大 13.34、5 指標すべて通過)
3. **v1108 部品化成立** (3 要件すべて、5 category 内限定)

### 5.2 議題化候補

4. **構造制約 (5/24 category)**: v1108 設計時に「全 category 一般化」は不可、5 category 限定での試行が筋
5. **v1107b との並行発見**: 同じ二極化が「category profile」と「48 軸 scale 寄与」の両方で確認 → ESDE 内部構造の二重根拠

### 5.3 解釈は控える (Web Claude 判断)

- 「ESDE が問いを理解している」(judgment 回避)
- 「鉛筆 = PER、人生 = EXS」の意味的対応 (GPT 指摘、観察に意味を引っ張られない)

---

## 6. 留保候補 (Web Claude 採番管理)

| 候補 番号 | 内容 |
|---|---|
| #L53 候補 | category 一般化二極化 (5 category 内、cluster_0 EXS/FND vs cluster_1 BOD/PER/PRP、shuffle z=13.34、v1108 部品化成立) |
| 構造制約 | 24 category 中 5 category 対応、19 category 予測不能 (v1106b 試行制約) |

---

## 7. 出力ファイル一覧

### スクリプト
- `v1107a_step_b_env_check.py` 〜 `v1107a_step_g_bit_identity.py` (6 ファイル)

### 出力 (parquet)
- `env_check_summary.parquet`, `env_check_category_counts.parquet`
- `observation_1_category_profiles.parquet`, `observation_1_summary.parquet`
- `observation_2_clusters.parquet`, `observation_2_summary.parquet`
- `observation_3_shuffle_comparison.parquet`, `observation_3_summary.parquet`
- `observation_4_category_to_cluster.parquet`, `observation_4_cluster_profiles.parquet`, `observation_4_summary.parquet`

### 報告書
- `v1107a_step_a_recognition.md`, `v1107a_step_g_bit_identity_report.json`, `v1107a_step_h_observation_final.md`

---

**Step H end. Web Claude Phase Result 着手判断材料を提供。**
