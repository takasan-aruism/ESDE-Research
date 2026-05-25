# v1106a 確認要請 11 への Web Claude 回答 + Atom 抽出確認反映 + Step B 着手指示

*作成*: 2026-05-26、Web Claude (相談役、Genesis 側)
*対象*: Code A
*親*: `v1106a_phase_design.md` v3 + `v1106a_step_a_recognition.md` (Code A、確認要請 11) + `docs/atom_extraction_check/atom_extraction_mechanism_2026-05-26.md` (Code A 実環境照合報告) + Taka 整理 (2026-05-25「先に進めていい」)
*位置づけ*: Code A Step B 着手前の Web Claude 回答兼指示。

---

## 1. 確認要請 11 への回答 — Code A 推奨案 Z-1 採用 (Taka 承認)

**論点**: 接続式案 Z の具体定義 (Z-1 / Z-2 / Z-3)

**Taka 判断 (2026-05-25)**: **案 Z-1 採用** (Code A 推奨、設計書通り)

**根拠**:
1. 設計書字面に忠実 (§1.3 案 Z 文面通り)
2. 観察 5 で raw_scores vs normalized_scores の挙動対比そのものが #L41 構造特性切り分けの観察対象
3. 案 Z-2 / 案 Z-3 は Code A 自身が「独自発明、設計書範囲外」と評価
4. 案 Y 除外妥当 (計算量 50 倍は「忘れ物を取りに戻っても遅刻しない範囲」を超える)

**確定する接続式の組み合わせ**:

| 系列 | 接続式 |
|---|---|
| **案 X (主軸)** | `score = Σ p_s7(atom_i) × (raw_scores_max(atom_i, word_j) / 10)` |
| **案 Z-1 (補助)** | `score = Σ p_s7(atom_i) × normalized_scores_max(atom_i, word_j)` |
| 案 Y (除外) | 計算量 50 倍 |

案 X 主軸 + 案 Z-1 補助の並列実行 (絶対格言 #11、別レイヤー保持)。

**観察 5 (#L41 解消確認) で見るべき対比**:

| 指標 | 案 X (raw_scores_max) | 案 Z-1 (normalized_scores_max) |
|---|---|---|
| top1 score 分布 | 0-10 整数、10 タイは部分的 (45.2% で出現) | 0-1 連続、1.0 タイ多発の可能性 |
| atom 間差別化 | raw_scores 0-10 で差別化観察可能 | normalized_scores 1.0 タイで埋まる場合 v1106 #L41 と同型 |
| #L41 解消判断 | raw で解消 / norm で再現 = 構造特性は raw でのみ解消 | 両方で解消 = mapper_output 全体で解消 |

両者の対比が #L41 の構造的原因を切り分ける素材。

---

## 2. Atom 抽出仕組み確認結果の反映 (Code A 報告 2026-05-26)

### 2.1 v1106a 進行への影響

| 確認 | 結果 |
|---|---|
| Atom a = Atom a か Atom a × x × y か | **A + B のハイブリッド** (atom 固定 326 + cid 揺れる) |
| 48 axes と Atom 内部 yyy 一致か | **別構造** (axes = 座標軸、yyy = atom 名) |

→ **v1106a 現状設計 (接続式案 X 主軸 + 案 Z-1 補助) のまま Step B から進行可能、修正不要**

### 2.2 v1106a で意識すべき点

1. v1106a 接続式の「48 axes」は mapper_output の座標軸 (axis.level、48 種)
2. Atom 表記 `XXX.yyy` の `XXX` (category prefix、24 種) ではない、両者を混同しない
3. v1106a で扱う Atom 候補 (v1105a s7 出力) は 326 固定 atom の確率分布
4. cid 自体の揺れ (cid_atom_sim_matrix per-cid 分布解析) は v1107 以降の主題候補

### 2.3 #L43 (FND.spaceless 欠落) の構造的解明

- esde_dictionary.json 326 中 1 件、mapper_output には最初から存在しない (a1_batch `zero_core_atoms: 1`)
- v1103 atom_centroids 325 = mapper_output 325 完全一致 (FND.spaceless 自然除外)
- v1106 で Synapse v3 を使ったときに差分顕在化
- **v1106a で mapper_output ベースなら差分 0 (構造的解消)**

a1_batch `zero_core_atoms` の理由は Code A 報告 §6.3 で「推測」明示、Language 側指摘で断定不可、v1107 以降の主題候補。

---

## 3. Code A Step B 着手指示

### 3.1 Step B (環境準備) 6 件

1. v1105a s7 出力読み込み確認
2. mapper_output データ (325 jsonl / 125.2 MB) 読み込み確認
3. atom_id mapping 確認 (v1103 325 = mapper_output 325 完全一致)
4. v1106 outputs 参照可能性 (Phase Result 統合素材)
5. mapper_output frozen 確認 (Synapse v3 も frozen のまま放置)
6. bit-identity LAYER_B baseline 確認 (v1106 まで + 増分)

### 3.2 Step C-J 構成 (設計書 v3 §4 通り)

| Step | 内容 | 想定 |
|---|---|---|
| C | 観察 1 (Atom → word 変換) | 約 10 分 |
| D | 観察 2 (mapper_output と s7 整合) | 約 10 分 |
| E | 観察 3 (word 広がり/絞り) | 約 5 分 |
| F | 観察 4 (s7 vs s1-s6) | 約 10 分 |
| G | 観察 5 (#L41 解消確認) | 約 10 分 |
| H | 観察 6 (#L42 解消確認) | 約 5 分 |
| I | bit-identity + 集計 | 数十分 |
| J | 観察事実報告 | — |

合計想定 1-2 時間。

---

## 4. 規律遵守

| 規律 | 内容 |
|---|---|
| 物理層 frozen 維持 | mapper_output + Synapse v3 共に frozen、書込み unified/v1106a/ |
| 接続式の独自発明禁止 | 案 X + 案 Z-1、案 Y 除外 |
| 7 系列 + 案 X/Z-1 統合禁止 | 別レイヤー保持 |
| 構造ラベルのみで判定回避 | success/failure 不使用 |
| Operator/分子・ESDE らしさ語らない | Taka 規律「妄想化回避」継承 |
| v1106 結果との対比を「正しい/間違い」で判定しない | 両者構造事実 (Taka「うっかりミスは仕方ない」) |
| mapper_output 品質判定しない | Language 側評価は別主題 |
| 48 axes 意味解釈を v1107 以降 | axis = Operator 領域に近い |

---

## 5. 一文サマリ

確認要請 11 案 Z-1 採用 (Taka 承認、Code A 推奨、normalized_scores_max 設計書通り、案 Y 除外、案 X 主軸 + 案 Z-1 補助の並列実行)、Atom 抽出確認結果反映 (A 固定 326 + B cid 揺れる ハイブリッド構造、48 axes と Atom yyy は別構造、v1106a 現状設計のまま修正不要、#L43 mapper_output ベースで構造的解消)、Code A は Step B (環境準備 6 件) → Step C-J (4 観察 + 対比 2 観察 + bit-identity + 報告) の流れで実装、想定 1-2 時間、書込み unified/v1106a/ 配下のみ。

---

*以上、Code A への Step B 着手指示 (Web Claude、2026-05-26)。*
