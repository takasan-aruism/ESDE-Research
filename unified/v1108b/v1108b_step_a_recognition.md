# v1108b Step A — Code A 認識確認

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A 認識確認、実装制約なし、Step B 進行可
**親**: v1108b 設計書草案 (Web Claude、2026-05-29)

---

## 0. 受領内容認識

### 0.1 主題
v1108b — 24 category 全体における入力 category 別参照領域選択の試行 (GPT 推奨、問いの形 B 試行)
- 観察 1: 24 cat 全体 input 励起と参照 CID profile
- 観察 2: cluster_0/1 への距離・分布・強度
- 観察 3: 出力候補性質変化
- 観察 4: 48 軸 Macro/Micro 整合
- 観察 5: attractor 収束 vs input 効果

### 0.2 設計書冒頭予防規律 11 件 + v1107 結果外挿予防 (受領)

### 0.3 構造ラベル 5 種 + GPT 7 条件 (受領)

### 0.4 Code A への一言 (受領)
> 「わからんことは言えよな」

→ 本主題は **実装制約なし**、確認事項のみ。

---

## 1. 実装条件事前チェック (6 項目)

### 1.1 データ存在
| データ | パス | 状態 |
|---|---|---|
| v106 cid_atom_sim_matrix | 24 seeds | ✓ frozen |
| v106 cid_structure_profile | 24 seeds | ✓ frozen |
| mapper_output | 325 files | ✓ frozen |
| v1103 atom_centroids | 325 atoms × 48 軸 | ✓ frozen |
| v1107a cluster 定義 | observation_4_cluster_profiles.parquet | ✓ frozen |
| v1107b axis 寄与 | observation_2_axis_contribution.parquet | ✓ frozen |
| v1107c 24 cat 拡張 | cluster_assignment.parquet | ✓ frozen |
| esde_dictionary | 326 atom 定義 | ✓ frozen |

**全データ存在、frozen 確認**。

### 1.2 計算可能性
24 category × 代表 atom × 24 seeds × top-5 CID:
- 24 cat × 数 atom/cat (例 3) × 24 seeds × 5 CID = 8,640 行程度
- v1107c の枠組み流用可能 (22.5 秒実績)
- 計算量軽量、ベクトル化容易

→ **計算可能性 OK**。

### 1.3 方法論成立性
- v1107c で 19 不在 category × 216 atom 全 atom 試行実績あり
- 同じ枠組みを「明示的 input 励起」として使う (問いの形 B 試行)
- v1107c は post-process 観察、v1108b は試行段階確認 (差は主題の位置づけのみ、計算機構は同じ)

→ **方法論成立**。

### 1.4 cluster 距離計算方法 (Code A 提案)

**euclidean (標準化後)**:
- v1107c で実装済 (StandardScaler + euclidean)
- cluster_0/1 中心への距離を [0, 1] 規格化して扱う
- 距離差 (|d_0 - d_1|) で「強度」測定 (GPT §2.2 反映で連続量扱い)

代替: cosine 距離も併記可 (v1107c の特徴ベクトルは符号方向もあるので euclidean が自然)

### 1.5 attractor 収束 vs input 効果の切り分け方法 (Code A 提案)

**手法**:
1. 同 seed 内で複数 category input を投入、各 input で top-5 CID を取得
2. 各 CID の v1106b 観察 2 attractor list (per_seed 90%+ 集約 CID) との重複率を測定
3. attractor 重複率 > 0.5 → `attractor_dominated`
4. category 別 CID 集合の overlap < 0.3 → `category_reference_switch_observed` (input 効果)
5. その間 → `weak_switch` (構造ラベル 2)

閾値 (0.5 / 0.3) は v1106b 観察 2 と v1107c の実績から推定、Step C 結果で再調整可。

### 1.6 代表 atom 選定方針 (Code A 提案)

**Web Claude 確認待ち事項**:

| 案 | 内容 |
|---|---|
| 案 A | 各 category 1 atom (代表のみ、24 atom 試行) |
| **案 B (推奨)** | **各 category 全 atom** (cat 別 6-30 atom、計 325 atom、v1107c と同枠組み) |
| 案 C | 各 category 3 atom (中間案、72 atom) |

案 B 推奨理由:
- v1107c で 19 cat 全 216 atom 試行実績あり (計算量問題なし、22.5 秒)
- 5 cat も v1107a で実績あり
- 全 325 atom は **「代表 atom 選定の恣意性」を排除** (神の手回避)
- atom 単位の input 励起効果も観察可能 (cat 内 atom 別の分散も見える)

**Web Claude 確認要**: 案 A/B/C どれを採用するか。

---

## 2. データ取り違え防止 §0.7

全 frozen 確認済 (§1.1)。書込みは `unified/v1108b/outputs/main/` 配下のみ。

---

## 3. 計算量事前確認は不要 (Taka 判断 4)

想定: 案 B 採用なら v1107c 22.5 秒のオーダー (1 分以内)。

---

## 4. 規律遵守確認

| 規律 | 遵守確認 |
|---|---|
| 絶対格言 15 件 | ✓ |
| 6 段階目ミス予防 (実験設計を疑う) | ✓ |
| 5 段階目ミス予防 (他 AI 提案実環境照合) | ✓ §1.3 で v1107c 実績照合 |
| 4 段階目以前予防 | ✓ |
| v1107 結果外挿予防 | ✓ 5 cat → 24 cat 外挿せず、明示的試行で確認 |
| 物理層 frozen | ✓ |
| ボツも構造事実 | ✓ 構造ラベル 5 種事前確定 |
| cluster 二値決定回避 | ✓ §1.4 で距離・分布・強度として扱う |
| 48 軸単独根拠回避 | ✓ 観察 4 を補助根拠扱い |
| 自然文判定回避 | ✓ atom/word 候補レベルで止める |
| 実験設計制約 vs 構造制約区別 | ✓ 構造ラベル 4 + 5 で明示 |

---

## 5. Step 分解

| Step | 内容 |
|---|---|
| A | 本文書、認識確認 |
| B | 環境準備 (24 cat × 案 B 全 325 atom 選定) |
| C | 観察 1 (24 cat profile) |
| D | 観察 2 (cluster 距離・分布・強度) |
| E | 観察 3 (出力候補性質) |
| F | 観察 4 (48 軸 Macro/Micro 整合) |
| G | 観察 5 (attractor 収束 vs input 効果) |
| H | bit-identity 3 層検証 |
| I | 観察事実最終報告 + 構造ラベル 5 種判定 |

---

## 6. Web Claude / Taka への確認

| 項目 | Code A 提案 | 確認待ち |
|---|---|---|
| 代表 atom 選定: 案 A/B/C | 案 B (全 325 atom) 推奨 | Web Claude / Taka 判断 |
| cluster 距離計算: euclidean | OK | 確認待ち |
| attractor 閾値: 0.5 / 0.3 | OK | 確認待ち |

---

## 7. v1108a との関係

- v1108a 観察 1 で実装制約あり (Atom 確率分布記録なし、Web Claude / Taka 判断待ち)
- v1108b は実装制約なし、Step B 進行可
- 両主題並行 OK (出力パス分離、入力 read-only 重複)

---

**Step A end. 実装制約なし、Web Claude / Taka 確認 (代表 atom 選定) 後に Step B 進行。**
