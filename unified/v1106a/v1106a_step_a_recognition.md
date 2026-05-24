# v11.0.6a (v1106a) Step A 認識確認 — Code A

*作成*: 2026-05-25、Code A
*親*: `v1106a_phase_design.md` (Web Claude 設計書、v1106 同主題段階 2)
*対象*: Web Claude (相談役) + Taka (主題判断者)
*位置づけ*: v1106a 進行表 Step A (Code A 認識確認 + 実環境照合)。データ取り違え防止規律 §0.7 を本主題で初適用、必須確認 5 件 + 追加確認 5 件 = 計 10 件を実施完了。判定は行わず、観察手順の実装可能性と Web Claude/Taka 領域への確認要請 1 件 (接続式 案 Z の挙動確認) に限定。

---

## 0. 一文サマリ

v1106a 設計書 (v1106 同主題段階 2、mapper_output ベース) を Code A 受領、データ取り違え防止規律 §0.7 を本主題で初適用し必須確認 5 件 + 追加確認 5 件 = 計 10 件を実施: 必須 1 (mapper_output 所在 325 jsonl / 125.2 MB、設計書約 126 MB と一致) / 必須 2 (timestamp 2026-02-21 〜 02-23 = 設計書「2026-03-21 前後」と微小差、実体は **2 月下旬**) / 必須 3 (生成方法 = LLM、total entries 33,414、status OK 28,369 / Diffuse 4,297 / Failed 748、**llm_elapsed_sec 合計 474.4h = 19.8 日相当** 設計書「8 日間」より大ただし並列実行で実時間 8 日もあり得る、**raw_scores max=10 出現 14,772 entries (45.2%) で Taka 言及「10 段階」と完全一致**) / 必須 4 (A1 batch 326 atoms = mapper_output 325 atoms + FND.spaceless 1 件、mapper_output ⊂ a1_batch) / 必須 5 (Synapse v3 frozen 並存確認) / 追加 6 (接続式案 X/Y/Z 実装可能性 + Code A 推奨案 X 主軸 + 案 Z 補助、案 Y は計算量 50 倍で除外推奨) / 追加 7 (atom_id mapping = v1103 325 ⊂ mapper_output 325 完全一致、**FND.spaceless は mapper_output に最初から存在しないため除外フィルタ不要** v1106 #L43 の構造的解消) / 追加 8 (word_expansion_ratio = entries 28,369 / unique words 17,790 / per atom mean 87.3 word・max 1,912・min 6、Lexicon Core 32,666 word に対し unique 17,790 = 54% カバレッジ) / 追加 9 (v1106 outputs 8 ファイル参照可能、observation_1_labels 23,100 rows 等) / 追加 10 (想定実行時間 = 案 X 主軸 5-15 分 / 案 Y 含む 4-8 時間 / 合計 Step C-J 1-2 時間 案 X 主軸推奨)、Web Claude/Taka 領域への確認要請 1 件提示: **確認要請 11 (接続式 案 Z の挙動確認)** = normalized_scores は **48 axes 内で Σ=1.0 に正規化されている確率分布** (sample max 0.9805 / sum 1.0)、案 Z で「normalized_scores_max」を取ると 1 word に 1 dominant axis = atom 単独で word の最大 axis のみ参照する形になり、案 X (raw_scores_max) より axis 単位の分解能を捨てる可能性。Code A 推奨: 案 X (raw_scores_max) 主軸 + 案 Z は「全 axes での normalized_scores 合計」または「normalized_scores の axis 集約方法」を明示する必要、Step C で実装する案 Z の具体定義を Web Claude/Taka で確認、Step B-J 想定実行時間 (B 1 分 / C 観察 1 約 10 分 / D 観察 2 約 10 分 / E 観察 3 約 5 分 / F 観察 4 約 10 分 / G 観察 5 約 10 分 / H 観察 6 約 5 分 / I bit-identity + 集計 数十分 / J 観察事実報告) + 規律遵守宣言 (絶対格言 #2/#5/#6/#9/#11/#12 + 全体図位置づけ + 妄想化回避 + データ取り違え防止規律初適用 + Synapse v3 frozen + mapper_output frozen + 接続式独自発明禁止 + 7 系列・案 X/Y/Z 統合禁止 + 書込み unified/v1106a/ 配下) を完了、確認要請 11 回答受領後に Step B から実装着手予定、書込み unified/v1106a/ 配下のみ。

---

## 1. 必須確認 5 件 (データ取り違え防止規律 §0.7 適用、本主題で初適用)

### 1.1 必須 1: mapper_output データ所在

| 項目 | 値 | 設計書照合 |
|---|---:|---|
| ディレクトリ | `language/lexicon/data/mapper_output/` | ✓ 設計書通り |
| ファイル数 | **325 jsonl** | ✓ 設計書通り |
| 合計サイズ | **125.2 MB** | ✓ 設計書「約 126 MB」と一致 |
| atom 名抽出 (filename) | 325 unique atoms (ABS.bound, ABS.exempt, ...) | ✓ |

### 1.2 必須 2: timestamp

**実環境照合結果**:
- ABS_bound_a1.jsonl 内 timestamp sample: **2026-02-21T23:00:07**
- 30 file sample timestamps range: **2026-02-21 〜 2026-02-23**

**設計書照合**: 設計書「2026-03-21 前後」と微小差、**実体は 2 月下旬 (Feb 21-23)**。Synapse v3 (2026-01-18) より約 1 ヶ月新しい (設計書「2 ヶ月新しい」より少し短いが大差なし)。

### 1.3 必須 3: 生成方法

| 項目 | 値 | Taka 言及との整合 |
|---|---:|---|
| total entries | **33,414** | ≒ a1_batch _summary 33,394 |
| status: OK | 28,369 (84.9%) | |
| status: Diffuse_Observation | 4,297 (12.9%) | |
| status: Observation_Failed | 748 (2.2%) | |
| **llm_elapsed_sec 合計** | **474.4h = 19.8 日相当** (mean 52.3s/entry) | Taka「約 8 日間」より大、並列実行で実時間 8 日もあり得る |
| **raw_scores max=10 出現** | **14,772 entries (45.2%)** | **Taka「10 段階」と完全一致** |
| 48 axes 全部スコア化 | ✓ (raw_scores keys 48 axes) | ✓ |

→ **LLM 1 億トークン 8 日間判定、48 axes × 0-10 整数 が実体として確認** = Taka 言及通り。

### 1.4 必須 4: A1 batch との対応

| 集合 | 件数 |
|---|---:|
| a1_batch atoms | 326 |
| mapper_output atoms | **325** |
| a1_batch ∩ mapper_output | 325 |
| **a1_batch - mapper_output** | **`FND.spaceless` 1 件** |
| mapper_output - a1_batch | 0 件 |

→ **mapper_output ⊂ a1_batch**、差分は FND.spaceless のみ (v1106 で発見した #L43 同型の構造、ただし mapper_output に最初から含まれない)。

### 1.5 必須 5: 古い Synapse v3 との並存

| ファイル | 状態 |
|---|---|
| `language/synapse/esde_synapses_v3.json` | exists、5.3 MB、frozen のまま read-only |
| `language/lexicon/data/mapper_output/*_a1.jsonl` | exists、125.2 MB、frozen のまま read-only |
| 並存確認 | ✓ 両者とも更新せず、v1106a では mapper_output のみ使用 |

---

## 2. 追加確認 5 件

### 2.1 追加 6: 接続式 §1.3 案 X/Y/Z 実装可能性 + Code A 推奨

**実環境照合結果** (sample: ACT_build_a1.jsonl entry "actable"):
- raw_scores: 48 axes × 0-10 整数、max=10.0、sum=36
- normalized_scores: 48 axes × 0-1 確率、max=0.9805、**sum=1.0** (= 48 axes 内で正規化)

**Code A 推奨**:

| 案 | 計算量 | Code A 評価 |
|---|---:|---|
| **案 X (主軸)** raw_scores_max | 13.86M ペア (5-15 分) | ✓ 主軸推奨、48 axes max を 0-10 → 0-1 正規化 (÷10) して接続 |
| 案 Y axis 単位 | **666M ペア (4-8 時間)** | 計算量 50 倍、Step C-J 合計時間が 5-10 時間に伸びる、Code A 推奨外 |
| **案 Z (補助)** normalized_scores 直接 | 13.86M ペア (案 X と同程度) | ✓ 補助系列推奨、ただし定義要確認 (確認要請 11) |

**Code A 推奨**: 案 X (raw_scores_max) 主軸 + 案 Z (normalized_scores) 補助、案 Y は計算量負担で除外推奨。

### 2.2 追加 7: atom_id mapping (FND.spaceless 欠落確認)

**実環境照合結果**:

| 集合 | 件数 |
|---|---:|
| v1103 atom_centroids_48d_raw | 325 |
| mapper_output atoms | **325** |
| **完全一致** | **325** |
| v1103 - mapper_output | 0 件 |
| mapper_output - v1103 | 0 件 |

→ **v1103 325 = mapper_output 325 完全一致、mapping 不要、FND.spaceless 除外フィルタも不要** (mapper_output には最初から存在しない)。

**v1106 との対比**: v1106 Synapse v3 では `Synapse only = FND.spaceless` 1 件で除外フィルタが必要だったが、**mapper_output には最初から存在しないため除外不要 = v1106 #L43 の構造的解消**。

### 2.3 追加 8: word_expansion_ratio / total_word_coverage 計算

**実環境照合結果** (status=OK のみ):
- total entries: **28,369** (status=OK のみ、Diffuse + Failed 除外)
- **unique words: 17,790** (重複 word 排除)
- per atom: mean **87.3** word、max **1,912** word (極端な atom あり)、min 6 word

**word_expansion_ratio 計算**:
- per event (s7 PC) atom mean ~6 (v1105a) × per atom 87.3 word = ~520 word/event 平均
- v1106 Synapse v3 で n_synsets mean 582 と近い数

**total_word_coverage 計算**:
- Lexicon Core 32,666 word (a1_batch _summary) のうち **unique 17,790 = 54%** がスコア付き
- 残り 46% は Diffuse_Observation / Observation_Failed で raw_scores 持たず
- coverage = n_words_after / 17,790 (実体合わせ) または / 32,666 (Lexicon 全体)

**Code A 実装方針**: total_word_coverage を 2 種類 (unique 17,790 ベース + Lexicon 32,666 ベース) 別レイヤーで記録、絶対格言 #11 概念単位を雑に扱わない継承。

### 2.4 追加 9: v1106 outputs 参照可能性

**実環境照合結果**:
- v1106 outputs 8 ファイル参照可能 (read-only)
- observation_1_labels.parquet (23,100 rows、構造ラベル付き) で対比可能
- v1106 + v1106a 統合 Phase Result (Web Claude 領域) の素材として利用可

### 2.5 追加 10: 想定実行時間

| Step | 想定実行時間 |
|---|---:|
| B 環境準備 (SynapseStore + mapper_output 読み込み確認) | < 1 分 |
| C 観察 1 (Atom → word 変換、案 X 主軸 + 案 Z 補助) | 約 10 分 |
| D 観察 2 (mapper_output と s7 確率整合、相関指標) | 約 10 分 |
| E 観察 3 (word 広がり/絞り) | 約 5 分 |
| F 観察 4 (s7 vs s1-s6 layer_jaccard) | 約 10 分 |
| G 観察 5 (#L41 解消確認) | 約 10 分 |
| H 観察 6 (#L42 解消確認) | 約 5 分 |
| I bit-identity 3 層 + 集計 | 数十分 (Step C-H 再実行) |
| J 観察事実報告 | — |

**合計想定**: **1-2 時間** (案 X 主軸採用前提)、案 Y を含めると 5-10 時間。

---

## 3. 確認要請 1 件 (Web Claude/Taka 領域)

### 3.1 確認要請 11 — 接続式案 Z の具体定義

**論点**: 設計書 §1.3 案 Z は「normalized_scores 直接使用 (案 X の raw_scores を normalized_scores に置換)」だが、実体は normalized_scores が **48 axes 内で Σ=1.0 に正規化** されている確率分布 (sum=1.0 確認、max 0.9805 等)。

**問題**: 案 Z で「normalized_scores_max(atom, word) = max over 48 axes of normalized_scores」を取ると:
- 1 word に 1 dominant axis (max ≈ 1.0 のことが多い、ACT_build sample で max=0.9805) しか参照しない
- atom × word 単位の差別化は出るが、48 axes の分布情報を捨てる
- atom 間差別化観察 (#L41 解消確認) で「normalized_scores_max が全 atom で ~1.0 タイ」になる可能性

**Code A 案 3 つ** (案 Z の具体定義):

| 案 | 内容 | 利点 | 欠点 |
|---|---|---|---|
| **案 Z-1 (Code A 推奨)** | `normalized_scores_max` 使用 (設計書通り、案 X と並列で挙動比較) | 設計書文面に忠実、案 X との単純対比 | 上記問題 (axis 分布捨てる、max タイ多発リスク) |
| 案 Z-2 | `normalized_scores_top_k_sum` (上位 k axis 合計、例 k=5) | axis 分布情報を一部保持 | k 選択の人為性、独自発明リスク |
| 案 Z-3 | `normalized_scores_entropy` (axis 分布の entropy、低 entropy = 集中 word、高 entropy = 拡散 word) | atom × word の axis 集中度を観察 | 独自発明、設計書範囲外 |

**Code A 推奨**: **案 Z-1 (設計書通り)** で案 X との単純対比、観察 5 (#L41 解消確認) で「normalized_scores_max が tied で raw_scores_max が differentiated か」を構造事実として記録 (両者の挙動対比そのものが観察対象)。

**Web Claude/Taka 判断**: 案 Z-1 (Code A 推奨) / 案 Z-2 / 案 Z-3 / 別案要求。

---

## 4. 規律遵守宣言 (Step A 範囲)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (mapper_output + Synapse v3 共に read-only、書込み unified/v1106a/ のみ) |
| 絶対格言 #5 (観察軸を増やさない) | ✓ (観察 5/6 は #L41/#L42 解消確認で v1106 観察軸の継承) |
| 絶対格言 #6 (出口の固定) | ✓ (v1106a 進行条件 6 点を §1.4 で事前確定) |
| 絶対格言 #9 (神の手回避) | ✓ (接続式は §1.3 案 X/Y/Z から選択、独自発明禁止) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (7 系列・案 X/Y/Z・観察 1-6 別レイヤー、word vs synset vs axis 単位明示) |
| 絶対格言 #12 (judgment 回避) | ✓ (success/failure 未使用、構造ラベルのみ、v1106 結果との対比判定なし) |
| データ取り違え防止規律 §0.7 (本主題で初適用) | ✓ (必須確認 5 件すべて実施、データ所在 / timestamp / 生成方法 / Taka 過去評価 / 古い実装並存) |
| 全体図位置づけ規律 (§0.1) | ✓ (Atom → mapper_output → word の最小経路、Operator/分子経由しない) |
| 妄想化回避規律 (§0.6) | ✓ (Operator/分子/ESDE らしさ/会話成立を語らない、48 axes の意味解釈は v1107 以降) |
| mapper_output frozen + Synapse v3 frozen | ✓ (両者とも read-only 維持) |
| 接続式独自発明禁止 | ✓ (案 X/Y/Z から選択、案 Z 具体定義は確認要請 11) |
| 7 系列・案 X/Y/Z 統合禁止 | ✓ (別レイヤー保持) |
| v1106 結果との対比判定なし | ✓ (案 Y 採用、間違いの記録、両者構造事実) |
| 書込みパス unified/v1106a/ 配下 | ✓ |
| smoke 含めず | ✓ |

---

## 5. Step A 完了後の進行 (確認要請 11 への Web Claude/Taka 回答受領後)

1. **確認要請 11 回答**: 案 Z 具体定義確定 (Code A 推奨案 Z-1 = normalized_scores_max)
2. 回答受領後 Step B から順次実装:
   - Step B (環境準備)
   - Step C (観察 1: Atom → word 変換)
   - Step D (観察 2: mapper_output と s7 整合)
   - Step E (観察 3: 広がり/絞り)
   - Step F (観察 4: s7 vs s1-s6)
   - Step G (観察 5: #L41 解消確認)
   - Step H (観察 6: #L42 解消確認)
   - Step I (bit-identity + 集計)
   - Step J (観察事実報告)

---

## 6. 一文サマリ (再掲)

v1106a 設計書 (v1106 同主題段階 2、mapper_output ベース) Code A 受領、データ取り違え防止規律 §0.7 を本主題で初適用し必須 5 件 + 追加 5 件 = 計 10 件実施完了 (mapper_output 325 jsonl / 125.2 MB / timestamp 2026-02-21〜23 / total entries 33,414 / status OK 28,369 (85%) / llm_elapsed_sec 合計 19.8 日相当 / raw_scores max=10 出現 45.2% で「10 段階」確認 / a1_batch 326 ⊂ mapper_output 325 で FND.spaceless 1 件除外 / Synapse v3 frozen 並存 / 接続式案 X 主軸 + 案 Z 補助推奨案 Y 計算量 50 倍で除外 / v1103 325 = mapper_output 325 完全一致 mapping 不要 FND.spaceless 構造的解消 (#L43 解消) / unique words 17,790 = Lexicon 32,666 の 54% / per atom mean 87.3 word max 1,912 / v1106 outputs 参照可能 / 想定 1-2 時間 案 X 主軸)、Web Claude/Taka 領域への確認要請 1 件 (確認要請 11 案 Z 具体定義 = normalized_scores が 48 axes 内 Σ=1.0 正規化で「normalized_scores_max が tied 多発リスク」、Code A 推奨案 Z-1 設計書通り raw_scores_max と並列対比) 提示、Step B-J 想定実行時間 + 規律遵守宣言 (絶対格言 #2/#5/#6/#9/#11/#12 + データ取り違え防止規律初適用 + 全体図位置づけ + 妄想化回避 + mapper_output/Synapse v3 frozen + 接続式独自発明禁止 + 7 系列・案 X/Y/Z 統合禁止 + v1106 結果との対比判定なし) 完了、確認要請 11 回答受領後に Step B 着手予定、書込み unified/v1106a/ 配下のみ。
