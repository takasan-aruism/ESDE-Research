# v1107b Step H — 観察事実最終報告

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A-G 完了、Web Claude Phase Result 着手判断材料

---

## 0. 全 Step 完了状況

| Step | 内容 | 実行時間 | 結果 |
|---|---|---:|---|
| A | 認識確認 (Gemini 仮説軸名 3/6 不在を Q4 で明示) | - | Taka 承認 |
| B | 環境準備 + 48 軸構造確認 | 0.1s | 全リソース OK + intra/inter 予想外発見 |
| C | 観察 1 (48 軸クラスタリング 3 手法) | 0.1s | gemini_hypothesis_supported (purity 0.81)、silhouette 弱 (0.34) |
| D | 観察 2 (axis 寄与分解 + category × scale 偏り) | 22.2s | scale_usage_differentiated (max CV 1.14) |
| E | 観察 3 (shuffle、基準 A) | 0.2s | 緩和 PASS (category シャッフル z=13.75)、厳格 FAIL (silhouette<0.5) |
| F | 観察 4 (v1108 部品化、基準 C) | 0.0s | **v1108_ready** (3/3 要件) |
| G | bit-identity 3 層検証 | 24.5s | **全 PASS** |

合計実装時間: **約 1 分**

---

## 1. Gemini 仮説軸名 3/6 不在 — Q4 段階 1 対処

Code A 事前照合で発覚:

| Gemini 仮説 | 軸名 | 実在 |
|---|---|---|
| Micro | `temporal.immediate` | 不在 |
| Micro | `scale.individual` | ✓ |
| Meso | `interconnection.*` (5 levels) | ✓ |
| Meso | `resonance.*` (4 levels) | ✓ |
| Macro | `ontological.entirety` | 不在 |
| Macro | `experience.integrated` | 不在 |

**対処**: Code A 案で実環境軸名にマッピング再構成 (Q4 段階 1):
- Micro 候補: temporal.emergence/indication/scale.individual/interconnection.independent/ontological.material
- Meso 候補: interconnection.{catalytic/chained/synchronous/resonant}/resonance.{structural/essential}/epistemological.experience/ontological.relational
- Macro 候補: scale.{ecosystem/stellar/cosmic}/resonance.existential/ontological.semantic/experience.comprehension/lawfulness.necessary/value_generation.sacred

→ Phase Result で「5 段階目ミス」として記録、Code A 事前照合の構造的価値確認。

---

## 2. 観察結果

### 2.1 観察 1 (48 軸クラスタリング 3 手法 × k=2-6)

| 手法 | 最適 k | silhouette | 評価 |
|---|---:|---:|---|
| kmeans | 2 | 0.240 | 弱分離 |
| agglomerative | 3 | 0.343 | 弱分離 |
| spectral | 2 | 0.359 | 弱分離 |

仮説 purity 最高: **kmeans k=6 で 0.81** (threshold 0.7 超)

構造ラベル: **gemini_hypothesis_supported** (purity 0.81 > 0.7)

ただし silhouette 全手法で 0.5 未満 → **「仮説マッピングに近い構造はあるが、クラスタ分離は弱い」混合構造**

予想外の発見 (Step B):
- intra-group (同 group 内、例 temporal 7 levels) mean 0.4503
- inter-group (異 group 間) mean 0.4836
- → 意味的 group 構造とデータ構造が一致しない

### 2.2 観察 2 (axis 寄与分解 + category × scale 偏り)

3,300 events の axis 寄与分解 (加法分解、情報損失なし):

| category | Micro 寄与 | Meso 寄与 | **Macro 寄与** | dominant scale |
|---|---:|---:|---:|---|
| BOD | 0.281 | 0.003 | 0.002 | Micro |
| EXS | 0.193 | **0.013** | **0.031** | Micro |
| FND | 0.187 | **0.014** | **0.020** | Micro |
| PER | 0.266 | 0.003 | 0.002 | Micro |
| PRP | 0.203 | 0.003 | 0.003 | Micro |

scale CV (category 間):
- Micro: 0.196 (弱)
- Meso: **0.841**
- Macro: **1.136**

構造ラベル: **scale_usage_differentiated** (max CV 1.14、threshold 0.2 超)

→ **EXS/FND が Macro 軸 (存在的) 寄与高、PER/BOD/PRP が Micro 軸 (即物的) 寄与高**

### 2.3 観察 3 (shuffle baseline、基準 A)

**軸ラベルシャッフル** (10 回):
| method | true silhouette | shuf mean | z | paired | 通過 |
|---|---:|---:|---:|---:|---|
| kmeans | 0.231 | -0.061 | 0.93 | 1.00 | ✗ |
| agglomerative | 0.343 | 0.108 | 0.64 | 1.00 | ✗ |
| spectral | 0.203 | 0.002 | 0.60 | 0.90 | ✗ |

→ 軸クラスタリング自体は shuffle と有意差なし (z < 1.0)

**category ラベルシャッフル** (10 回、観察 2 への直接攻撃):
- 真 max scale CV: **1.136**
- shuffle mean: **0.157**
- **z = 13.75、paired = 1.00**

→ category × scale 偏りは shuffle に対し圧倒的に強い

**基準 A 判定**:
- 厳格 (silhouette > 0.5 AND z > 2): **FAIL** (silhouette 0.34)
- 緩和 (category シャッフル通過のみ): **PASS** (z 13.75)

### 2.4 観察 4 (v1108 部品化、基準 C)

3 要件すべて成立:
1. ✓ category → scale 偏り表 (5 category × Micro/Meso/Macro)
2. ✓ scale → 軸 mapping (48 軸すべてに Gemini scale または data 駆動 cluster 割当)
3. ✓ 予測枠組み (新規 input_atom → 想定 scale パターン予測)

→ **基準 C 通過、構造ラベル `v1108_ready`**

ただし注意: dominant scale が全 category で Micro (差別化は Macro 寄与で確認)

---

## 3. 3 基準統合判定

| 基準 | 結果 |
|---|---|
| A (shuffle baseline) | **緩和 PASS** / 厳格 FAIL |
| B (scale 使用差別化) | **PASS** (Macro CV 1.14) |
| C (v1108 部品化) | **PASS** (3/3 要件) |

**統合判定**: **「構造あり強し (category × scale 偏り)、ただし軸クラスタリング自体は弱信号」議題化候補**

(Phase Result §2.4 表: A 通過 B 通過 C 通過 → スケール構造あり強し)

→ v1108 進行可、ただし「48 軸 cluster は data 駆動で分離弱い」という補助観察を記録すべき

---

## 4. v1107a との関係

| 観点 | v1107a | v1107b |
|---|---|---|
| アプローチ | category 一般化 | 48 axes スケール |
| 基準 A | 完全 PASS | 緩和 PASS (厳格 FAIL) |
| 基準 B | PASS | PASS |
| 基準 C | PASS | PASS |
| 主要発見 | 2 cluster (EXS/FND vs BOD/PER/PRP) | category × Macro 寄与差別化 |

**両主題共通発見**:
- v1106b #L51 が 5 category 内で構造的に一般化
- EXS/FND が「社会的 + Macro 寄与」、PER/BOD/PRP が「孤立 + Micro 寄与」の **二重根拠** (category profile + 48 軸 scale 寄与)

---

## 5. Code A 主観 (Web Claude 参考)

### 5.1 観察事実として強い

1. **category × Macro 寄与差別化** (EXS/FND の Macro 寄与が他より 10 倍高)
2. **category シャッフル完全敗北** (z = 13.75)
3. **5 段階目ミス本番前修正** (Code A 事前照合で Gemini 軸名照合漏れ発見、新規規律「他 AI 提案実環境照合」確立)
4. **v1107a との二重根拠** (同じ二極化が別レイヤーで確認)

### 5.2 議題化候補

5. **軸クラスタリング弱信号**: silhouette 全手法 < 0.5、48 軸自体は強い構造でない可能性
6. **intra/inter 予想外**: 同 group 内よりも異 group 間の cos_sim が高い、意味的 group 構造とデータ構造の不一致

### 5.3 解釈は控える

- 「ESDE が 48 軸を使い分けている」(judgment 回避)
- 「Macro 軸 = 存在的、Micro 軸 = 即物的」の確定的解釈 (Web Claude 判断)

---

## 6. 留保候補 (Web Claude 採番管理)

| 候補 | 内容 |
|---|---|
| #L54 候補 | category × Macro 寄与差別化 (EXS/FND Macro 高、PER/BOD/PRP Macro 低、shuffle z=13.75) |
| #L55 候補 | 48 軸クラスタリング弱信号 (silhouette 全手法 < 0.5)、Gemini 仮説 purity 0.81 で支持はあるがデータ駆動分離自体は弱 |
| 5 段階目ミス | Gemini 仮説軸名 3/6 不在、本番前 Code A 照合で発見、新規規律確立 |

---

## 7. 出力ファイル一覧

### スクリプト
- `v1107b_step_b_env_check.py` 〜 `v1107b_step_g_bit_identity.py` (6 ファイル)

### 出力 (parquet)
- `env_check_summary.parquet`, `env_check_axes_meta.parquet`, `axes_correlation_matrix.parquet`
- `observation_1_axis_clusters.parquet`, `observation_1_hypothesis_purity.parquet`, `observation_1_summary.parquet`
- `observation_2_axis_contribution.parquet`, `observation_2_category_scale_bias.parquet`, `observation_2_summary.parquet`
- `observation_3_axis_shuffle.parquet`, `observation_3_category_shuffle.parquet`, `observation_3_summary.parquet`
- `observation_4_category_scale_map.parquet`, `observation_4_scale_to_axes.parquet`, `observation_4_summary.parquet`

### 報告書
- `v1107b_step_a_recognition.md`, `v1107b_step_g_bit_identity_report.json`, `v1107b_step_h_observation_final.md`

---

**Step H end. Web Claude Phase Result 着手 (v1107a + v1107b 統合判定) の判断材料を提供。**
