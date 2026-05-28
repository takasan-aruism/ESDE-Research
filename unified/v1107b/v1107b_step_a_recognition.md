# v1107b Step A — Code A 認識確認

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A 認識確認、Taka + Web Claude 確認待ち
**親**: v1107b 設計書草案 (Web Claude、2026-05-28)

---

## 0. 受領内容認識

### 0.1 主題確認

**v1107b — 問いのスケールに応じた参照 CID 領域の動的変化の観察 (48 axes スケールアプローチ)**

- 問いの形: A (点検)
- 推奨 AI: Gemini Architect
- 並行: v1107a (category 一般化アプローチ、GPT Auditor 推奨)
- 駆動: v1106b #L51 が単なる category 偏りでなく「48 軸スケールの使い分け」を反映している可能性
- ボツも構造事実 (Gemini 仮説棄却も価値ある観察)

### 0.2 観察 4 段 + 3 基準 (A/B/C) 統合判定の認識

| 観察 | 内容 | 基準 |
|---|---|---|
| 1 | 48 axes の Micro/Meso/Macro グルーピング検証 | (基準 B 材料) |
| 2 | 入力 atom 種類で活用軸スケールが変わるか | (基準 B 判定) |
| 3 | shuffle baseline 比較 | **基準 A** |
| 4 | v1108 試行への接続検証 | **基準 C** |

統合判定: A→B→C 機械的判定、5 通り (§2.4 表) 事前確定。

### 0.3 **重要**: Gemini 仮説軸名 3/6 が実環境不在 (Code A 事前照合)

Code A の事前実環境照合結果:

| Gemini 仮説 | 軸名 | 実在 |
|---|---|---|
| Micro | `temporal.immediate` | **★不在★** (実際は emergence/indication/influence/transformation/establishment/continuation/permanence) |
| Micro | `scale.individual` | ✓ 実在 |
| Meso | `interconnection.*` | ✓ 全 5 levels 実在 |
| Meso | `resonance.*` | ✓ 全 4 levels 実在 |
| Macro | `ontological.entirety` | **★不在★** (実際は material/informational/relational/structural/semantic) |
| Macro | `experience.integrated` | **★不在★** (実際は discovery/creation/comprehension) |

→ **Gemini 仮説の概念マッピング (Micro/Meso/Macro) は作業仮説として保持、軸名は実環境の 48 軸からデータ駆動でマッピング再構成**。

設計書 §5 確認要請 2 + §6 設計-2 に正しく留保として明示されている。Q4 で詳細回答。

---

## 1. データ取り違え防止 §0.7 必須確認

### 1.1 データ所在

| データ | パス | 用途 |
|---|---|---|
| v106 axes_metadata | `developmental/v106/outputs/main/axes_metadata.json` | 48 軸定義 |
| v1103 atom_centroids_48d_raw | `unified/v1103/outputs/main/atom_centroids_48d_raw.parquet` (325 atoms) | 軸別 centroid |
| mapper_output | `language/lexicon/data/mapper_output/*_a1.jsonl` (325 files) | word raw_scores 48 軸 |
| v1106b 高/低 event 分類 | `unified/v1106b/outputs/main/observation_3_high_low_events.parquet` (3,300 events) | event_class |
| v1106a 案 Y word 分布 | `unified/v1106a/outputs/main/observation_Y_word_distributions.parquet` | 案 Y 出力 |
| v106 cid_structure_profile | `developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv` (24) | CID 48d vec |
| v1105a 関連付け | `unified/v1105a/outputs/main/trial_step2_associations.parquet` | event ↔ CID |

### 1.2 timestamp 確認 (全 frozen)

すべて frozen (v1107a §1.2 と同じ)。

### 1.3 生成方法 / 古い実装並存 / 出力上書き防止

すべて OK (v1107a §1.3-1.5 と同じ枠組み)、出力は `unified/v1107b/outputs/main/` 配下のみ。

→ **データ取り違え防止規律 §0.7 すべて確認、問題なし**。

---

## 2. Code A 確認要請 8 件への回答

### Q1: axis 寄与分解方法

**Code A 提案**: cos_sim の軸別寄与分解

```
cos_sim(atom_centroid, word_raw_48d) = (Σ_i a_i × w_i) / (||a|| × ||w||)
軸 i の寄与 = (a_i × w_i) / (||a|| × ||w||)
```

per (atom, word) ペアで:
- 各軸の寄与の絶対値
- 寄与順位 (top-K 軸)
- 寄与の累積 (上位 K 軸で全 cos_sim の何 % 説明できるか)

→ 軸寄与は **加法分解** で厳密 (cos_sim 全体 = 全軸寄与の和)、情報損失なし。

### Q2: クラスタリング手法

**Code A 提案**: **3 手法併用** (頑健性確認)

| 手法 | 用途 |
|---|---|
| k-means (軸間 cosine sim マトリクス) | データ駆動 k 探索 |
| 階層クラスタリング (Ward, average linkage) | 階層構造確認 |
| spectral clustering | 軸間関連性の構造的分離 |

3 手法で一致する k と cluster 構成を採用、不一致なら頑健性低と判定。

### Q3: shuffle 回数

**Code A 提案**: **10 回** (v1107a と同じ、軸ラベルシャッフルと category ラベルシャッフルの両方)

### Q4: Gemini 仮説検証方法 (**重要、軸名不在問題への対処**)

**Code A 提案**: 2 段階検証

**段階 1: 仮説の実環境軸名へのマッピング再構成**

| Gemini 概念 | 実環境軸候補 (Code A 案、データ駆動で確定) |
|---|---|
| Micro (即物的) | `temporal.emergence` / `temporal.indication` / `scale.individual` / `interconnection.independent` / `ontological.material` |
| Meso (関係的) | `interconnection.{catalytic/chained/synchronous/resonant}` / `resonance.{structural/essential}` / `epistemological.experience` / `ontological.relational` |
| Macro (存在的) | `scale.{ecosystem/stellar/cosmic}` / `resonance.existential` / `ontological.semantic` / `experience.comprehension` / `lawfulness.necessary` / `value_generation.sacred` |

→ Code A 案はあくまで **作業仮説**、データ駆動 (k-means + 階層 + spectral 3 手法併用) で軸クラスタを取得して確定。

**段階 2: 仮説マッピングとデータ駆動クラスタの一致度測定**

- データ駆動 cluster と仮説マッピングの purity (Rand index, NMI)
- purity > 0.7: 仮説支持 (`gemini_hypothesis_supported`)
- 0.4 < purity ≤ 0.7: 部分支持 (`gemini_hypothesis_partial`)
- purity ≤ 0.4: 仮説不支持 (`gemini_hypothesis_rejected_alternative_k`)
- データ駆動でクラスタ分離不能: 軸スケール構造なし (`axes_no_scale_structure`)

### Q5: 基準 A threshold

**Code A 提案**: **2 条件 AND** (v1107a Q4 と同枠組み)

| 条件 | threshold |
|---|---|
| silhouette score (k=最適クラスタ) | > 0.5 (良好なクラスタ分離) |
| shuffle z スコア | z > 2 |

両方クリアで基準 A 通過。silhouette < 0.5 だがデータ駆動 k で分離あり → 弱信号議題化。

### Q6: 想定実行時間

**Code A 提案**: v1106b 2 分実績 + v1107a と並行で計測

| Step | 内容 | 想定時間 |
|---|---|---|
| B | 環境準備 | 数秒 |
| C | 観察 1 (48 axes クラスタリング 3 手法) | 1-2 分 |
| D | 観察 2 (axis 寄与分解 28,369 ペア + category × scale 偏り集計) | 1-2 分 |
| E | 観察 3 (shuffle 10 回 + 比較) | 2-3 分 |
| F | 観察 4 (v1108 部品化検討) | 数秒 |
| G | bit-identity 3 層検証 | 5-10 分 |
| H | 観察事実最終報告 | 待ち |

**合計実装時間**: **10-20 分**

### Q7: v1107a との並行性確保

**Code A 提案**: 完全並行可能 (v1107a Q7 と同枠組み)
- 入力データ重複 (read-only)、出力パス分離、bit-identity 検証は独立

### Q8: Micro/Meso/Macro 作業呼称の規律

**Code A 提案**:

```python
# 結果報告
cluster_labels = ['cluster_0', 'cluster_1', 'cluster_2', ...]  # 機械的命名

# 本文中の表記規則
# OK: 「cluster_0 (Gemini 仮説では Micro 候補に対応する軸群を含む)」
# OK: 「データ駆動 cluster と Gemini 仮説の purity = 0.65」
# NG: 「Micro cluster は ...」「Macro 軸は ...」(確定的呼称)
```

→ 「Micro/Meso/Macro」は **仮説名としてのみ使用**、結果のラベルには使わない。Phase Result で Web Claude が判断するまで確定しない。

---

## 3. Step 分解

| Step | 内容 |
|---|---|
| **A** | **本文書、認識確認** |
| B | 環境準備 |
| C | 観察 1 (48 axes クラスタリング 3 手法、データ駆動 + 仮説検証) |
| D | 観察 2 (axis 寄与分解 + category × scale 偏り) |
| E | 観察 3 (shuffle baseline 10 回 + 基準 A 判定) |
| F | 観察 4 (v1108 出口要件 + 基準 C 判定) |
| G | bit-identity 3 層検証 |
| H | 観察事実最終報告 (3 基準判定 + 統合判定表) |

---

## 4. 規律遵守確認

| 規律 | 遵守確認 |
|---|---|
| 絶対格言 #5 軸増やさない | ✓ 既存 48 軸でグルーピング |
| 絶対格言 #6 出口固定 | ✓ §2.4 統合判定 5 通り事前確定 |
| 絶対格言 #9 神の手回避 | ✓ Micro/Meso/Macro マッピング確定回避、データ駆動 |
| 絶対格言 #11 概念単位を雑に扱わない | ✓ 軸 × スケール × category 別レイヤー |
| 絶対格言 #12 judgment 回避 | ✓ Gemini 仮説棄却も「失敗」と書かない |
| データ取り違え防止 §0.7 | ✓ §1 で確認 |
| 留保番号統一管理 | ✓ Web Claude 採番 |
| 物理層 frozen | ✓ 全 frozen |
| 書込みパス | ✓ unified/v1107b/ 配下のみ |
| Micro/Meso/Macro 確定呼称回避 | ✓ Q8 で実装方針確定 |
| Gemini 仮説棄却を失敗と書かない | ✓ 構造事実として記録 |
| 計算量見積を字面通り受け入れない | ✓ 28,369 ペア × 48 軸寄与分解の実測検証 (Step C で確認) |
| 集約関数情報損失明示 | ✓ axis 寄与分解は加法分解で情報損失なし、cluster 集約で何を捨てているかは Phase Result で明示 |

---

## 5. Web Claude / Taka への確認

### 5.1 Web Claude 確認待ち事項
- Q1-Q8 すべての Code A 提案 OK か
- **特に Q4 (Gemini 仮説軸名 3/6 不在への対処)、Q8 (Micro/Meso/Macro 作業呼称規律)** が重要
- 段階 1 の実環境軸名へのマッピング再構成案 (Code A 案) は妥当か、Web Claude/Gemini から追加意見あるか

### 5.2 Taka 確認 (任意)
- Step C-F の Code A 自走 OK か (v1106b 同様)
- Gemini 仮説軸名問題への対処方針 (Q4 段階 1) OK か

### 5.3 v1107a 並行進行
- v1107a Step A も並行提示済
- 両者完了後に Web Claude Phase Result で統合判定

---

**Step A 認識確認 end. Web Claude / Taka 確認後に Step B 進行。**
