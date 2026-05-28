# v1107a Step A — Code A 認識確認

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A 認識確認、Taka + Web Claude 確認待ち
**親**: v1107a 設計書草案 (Web Claude、2026-05-28)

---

## 0. 受領内容認識

### 0.1 主題確認

**v1107a — 問いのスケールに応じた参照 CID 領域の動的変化の観察 (category 一般化アプローチ)**

- 問いの形: A (点検)
- 推奨 AI: GPT Auditor
- 並行: v1107b (48 axes スケールアプローチ、Gemini Architect 推奨)
- 駆動: v1106b #L51 (PER × 孤立 reaped / EXS × 社会的 hosted の二極化) が全 category で一般化するか
- ボツも構造事実 (Taka 整理「結果がでない想定を潰すほうが ESDE らしい」)

### 0.2 観察 4 段 + 3 基準 (A/B/C) 統合判定の認識

| 観察 | 内容 | 基準 |
|---|---|---|
| 1 | 全 24 category × CID profile 集計 | (基準 B 材料) |
| 2 | 参照 CID profile のクラスタリング (意味名なし) | (基準 B 判定) |
| 3 | shuffle baseline 比較 | **基準 A** |
| 4 | v1108 試行への接続検証 | **基準 C** |

統合判定: A→B→C 機械的判定、5 通り (§2.4 表) すべてに構造ラベル事前確定。

---

## 1. データ取り違え防止 §0.7 必須確認 (v1106 §22.5 継承)

### 1.1 データ所在 (実環境照合)

| データ | パス | 用途 |
|---|---|---|
| v1106b 高/低 event 分類 | `unified/v1106b/outputs/main/observation_3_high_low_events.parquet` (3,300 events) | event_class + CID 物理量 |
| v1106b input_atom 偏り | `unified/v1106b/outputs/main/observation_3_input_atom_bias.parquet` | event_class × atom |
| v1106b CID 物理量 | `unified/v1106b/outputs/main/env_check_cid_props.parquet` (5,224 CID) | 全 CID プロファイル |
| v1106a 案 Y word 分布 | `unified/v1106a/outputs/main/observation_Y_word_distributions.parquet` | 案 Y 出力 |
| v1106a verification_a | `unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet` | cos_sim 集計 |
| v1105a 関連付け | `unified/v1105a/outputs/main/trial_step2_associations.parquet` | event ↔ CID |
| v106 cid_atom_sim_matrix | `developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet` (24) | CID × atom sim |
| v106 cid_structure_profile | `developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv` (24) | CID 48d vec |
| v105 per_subject | `developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv` (24) | CID 物理量詳細 |

### 1.2 timestamp 確認 (frozen)

| データ | timestamp | 状態 |
|---|---|---|
| v106 (cid_atom_sim_matrix / cid_structure_profile) | 旧 main run | frozen ✓ |
| v1103 atom_centroids | v1103 実行時 | frozen ✓ |
| mapper_output | 2026-02-21〜23 | frozen ✓ |
| v1105a / v1106a / v1106b 出力 | 2026-05-25〜28 | frozen ✓ |
| v105 per_subject | 旧 main run | frozen ✓ |

→ **全データ frozen、v1107a 実行で書き換わらない**。

### 1.3 生成方法

| データ | 整合性 |
|---|---|
| v1106b observation_3_high_low_events | v1106a Step L verification_a を再分類 + CID 物理量 merge ✓ |
| v1106b env_check_cid_props | per_subject 24 seeds 集約 + fam_bin 付与 ✓ |
| v1106a 案 Y | mapper_output raw_scores + 48 軸 cos_sim ✓ |

### 1.4 古い実装との並存

- v1107a は v1106b 出力 (案 Y) をそのまま使用
- 古い案 X / 案 Z-1 / Synapse v3 は不使用
- → **古い実装との並存なし**

### 1.5 出力上書き防止

- v1107a 出力は `unified/v1107a/outputs/main/` 配下のみ
- v1107b 出力は `unified/v1107b/outputs/main/` (別ディレクトリ、並行実行 OK)
- bit-identity 検証 (Step G) で書込みパス機械的確認

→ **データ取り違え防止規律 §0.7 すべて確認、問題なし**。

---

## 2. Code A 確認要請 8 件への回答

### Q1: 集計閾値 (category profile 差別化の std threshold)

**Code A 提案**:

| 物理量 | threshold | 単位 |
|---|---|---|
| final_state 分布 (hosted/ghost/reaped 比率) | std > 0.10 | 確率比率 |
| last_familiarity_max | coefficient of variation (CV) > 0.30 | 無次元 |
| n_alphas_currently | CV > 0.50 | 無次元 |
| current_social | std > 0.10 | 0-1 範囲 |
| current_stability/spread | std > 0.05 | 0-1 範囲 |

→ 複数物理量で threshold 超えれば「差別化あり」と判定。複数 threshold は AND でなく OR (どれか 1 つでも超えれば差別化候補)。

### Q2: shuffle 回数

**Code A 提案**: **10 回**

- v1106a Step L 検証 A で使用した枠組み (10 回 within-seed shuffle、5 回 cross-seed) を継承
- paired diff の統計安定性は 10 回で確保 (Step L で σ 1.0 計測実績)
- 計算量軽量 (post-process)

### Q3: cluster k 探索範囲

**Code A 提案**: **k = 2-6**

- k=2 (二極化、#L51 そのもの)
- k=3 (Gemini 仮説 Micro/Meso/Macro 等)
- k=4-6 (多極化探索)
- silhouette score で最適 k 選択
- elbow method 併用

### Q4: 基準 A threshold (shuffle 通過判定)

**Code A 提案**: **2 条件 AND**

| 条件 | threshold |
|---|---|
| z スコア (true mean - shuffle mean) / shuffle std | z > 2 |
| event-paired diff > 0 rate | > 0.75 (75% 以上が一方向) |

両方クリアで基準 A 通過。片方のみなら「弱信号」として議題化。

→ Step L 検証 A の σ 1.0 (z=1.0、paired 83%) は paired のみクリアで弱信号扱いだったことと整合的に厳しく設定。

### Q5: 観察 4 出口要件 (v1108 部品化判定)

**Code A 提案**: **以下 3 要件すべて成立で v1108_ready 判定**

1. category → cluster マッピング (24 category → cluster_0/1/2/... の対応表) が出力できる
2. cluster → CID profile (各 cluster の代表 CID 物理量分布) が出力できる
3. 新規 input_atom (category 既知) で「想定参照 CID cluster (確率分布)」を予測できる枠組みが構築可能

1+2+3 すべて成立 → v1108_ready
1+2 のみ成立 → 「観察構造あり、v1108 試行は別途設計要」として議題化
1 のみ成立 → v1108_not_ready

### Q6: 想定実行時間

**Code A 提案**: v1106b 2 分実績ベース

| Step | 内容 | 想定時間 |
|---|---|---|
| B | 環境準備 | 数秒 |
| C | 観察 1 (24 category × CID profile 集計) | 30 秒-1 分 |
| D | 観察 2 (クラスタリング、k=2-6 探索) | 1-2 分 |
| E | 観察 3 (shuffle baseline 10 回 + 比較) | 2-3 分 |
| F | 観察 4 (v1108 出口要件チェック) | 数秒 |
| G | bit-identity 3 層検証 | 5-10 分 (Step C-F 再実行含む) |
| H | 観察事実最終報告 | 待ち |

**合計実装時間**: **10-20 分** (Code A 当初見積、v1106b 同様に短縮される可能性大)

### Q7: v1107b との並行性確保

**Code A 提案**:
- 入力データ重複 (read-only) → 競合なし、同時実行 OK
- 出力パス分離 (unified/v1107a/ vs unified/v1107b/) → 衝突なし
- bit-identity 検証は各々独立 (v1107a Step G は v1107a Step C-F のみ再実行、v1107b 出力に影響なし)

→ **完全並行可能**、両者を同時に実行しても干渉なし。

### Q8: cluster 命名 (意味名なし規律)

**Code A 提案**:

```python
cluster_labels = ['cluster_0', 'cluster_1', 'cluster_2', ...]  # 機械的命名
# 各 cluster の category 構成と CID profile 特徴は集計値のみで記録
# 意味解釈 (例: 「これは知覚系 cluster」) は本主題で確定せず
```

各 cluster の特徴は数値表のみで記述:
- 構成 category 一覧 (例: cluster_0 = {PER.see, PER.smell, ...})
- 平均 final_state 分布 (hosted/ghost/reaped 比率)
- 平均物理量 (familiarity, n_alphas, lifespan, social, stability, spread)
- 意味解釈は Phase Result で Web Claude が判断

---

## 3. Step 分解 (Code A 想定)

| Step | 内容 | smoke pause |
|---|---|---|
| **A** | **本文書、認識確認** | - |
| B | 環境準備 (リソース load 確認) | - |
| C | 観察 1 (category × CID profile 集計) | - (smoke なし、軽量) |
| D | 観察 2 (k=2-6 クラスタリング) | - |
| E | 観察 3 (shuffle baseline 10 回 + 基準 A 判定) | - |
| F | 観察 4 (v1108 出口要件 + 基準 C 判定) | - |
| G | bit-identity 3 層検証 | - |
| H | 観察事実最終報告 (3 基準判定 + 統合判定表) | Web Claude Phase Result 着手 |

注: post-process で smoke と main の区別がない (全 3,300 events を一括処理)。Step C で smoke 的に小サンプル試行も可能だが、v1106b の Step E (Step D データ再集計、smoke なし) と同型で進行。

---

## 4. 規律遵守確認

| 規律 | 遵守確認 |
|---|---|
| 絶対格言 #5 軸増やさない | ✓ 既存 (24 category × CID profile) で観察 |
| 絶対格言 #6 出口固定 | ✓ §2.4 統合判定 5 通り事前確定 |
| 絶対格言 #11 概念単位を雑に扱わない | ✓ category × profile を別レイヤー保持 |
| 絶対格言 #12 judgment 回避 | ✓ ボツも構造事実 |
| データ取り違え防止 §0.7 | ✓ §1 で 5 件確認 |
| 留保番号統一管理 | ✓ Code A は候補扱い、Web Claude 採番 |
| 概念定義 vs 実装段階の区別 | ✓ Atom 326/325 区別を継続 |
| 物理層 frozen | ✓ v106 / v1103 / mapper_output / v1106a / v1106b 全 frozen |
| 書込みパス | ✓ unified/v1107a/ 配下のみ |
| ボツを失敗と書かない | ✓ 構造事実として記録 |
| 意味名を結果に使わない | ✓ cluster_0/1/2... 機械的命名 |
| 鉛筆/人生対応を結果に使わない | ✓ Phase Result で議題化のみ |

---

## 5. Web Claude / Taka への確認

### 5.1 Web Claude 確認待ち事項 (Q1-Q8 への Code A 回答全部)
- Q1-Q8 すべての Code A 提案 OK か
- 特に Q4 (基準 A threshold 2 条件 AND)、Q5 (出口要件 3 要件)、Q8 (cluster 命名規律) が重要

### 5.2 Taka 確認 (任意)
- Step C-F の Code A 自走 OK か (v1106b 同様)
- Step E の shuffle 10 回 (10 vs 100 等の希望あれば)
- main 中の Web Claude 確認頻度

### 5.3 v1107b 並行進行
- v1107b Step A 認識確認も同時提示
- 両者完了後に Web Claude Phase Result で統合判定

---

**Step A 認識確認 end. Web Claude / Taka 確認後に Step B 進行。**
