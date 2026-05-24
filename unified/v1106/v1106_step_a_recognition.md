# v11.0.6 (v1106) Step A 認識確認 — Code A

*作成*: 2026-05-25、Code A
*親*: `v1106_phase_design.md` (Web Claude 設計書、GPT 監査クリア + Taka 確定「Gemini 不要」)
*対象*: Web Claude (相談役) + Taka (主題判断者)
*位置づけ*: v1106 進行表 Step A (Code A 認識確認 + 実環境照合 + Web Claude/Taka 領域への確認要請 1 件)。判定は行わず、観察手順の実装可能性と確認要請に限定。

---

## 0. 一文サマリ

v1106 設計書 (Synapse 接続点検、問いの形 A 復帰、GPT 監査クリア) を Code A 受領、§5 確認要請 7 項目に Code A 認識提示 + 実環境照合 (Synapse データ実体構造特定: `language/synapse/esde_synapses_v3.json` 5.5 MB、**11,557 word_id** × 326 atoms、1 word → 1-3 atoms (mean 1.9)、**1 atom → 13-181 words (mean 68.4)**、**weight 連続値 0-1 (mean 0.52)** で設計書「1-10 強度」と不一致、rank 1-3)、Web Claude/Taka 領域への確認要請 1 件提示: 確認要請 8 (Synapse weight が設計書「1-10 強度」と異なり実体は 0-1 連続値、接続式 §2.1 normalize(syn) = syn/10 の修正方針確定、Code A 案 A weight をそのまま使用 (normalize 不要、推奨) / Code A 案 B weight × 10 で 1-10 スケール化 (設計書文面合わせ) / Code A 案 C rank 反転を使用 (rank-based 採用) の 3 案)、§5-1〜7 への回答 (1: esde_synapses_v3.json + patches v3.1-v3.5 / 2: v1105a outputs main / 3: atom 325 完全一致 / 4: 接続式は確認要請 8 後に確定、計算量 11,557 words × 3,300 events で 38M ペア = 動的計算可 / 5: word_expansion_ratio = n_words_after / n_candidates_after、total_word_coverage = n_words_after / 11,557 (実体合わせ、20,000 でなく) / 6: 接続条件 4 点は Web Claude/Taka 領域 / 7: 想定時間数十分〜1 時間)、Step B-H 想定実行時間 + 規律遵守宣言 (絶対格言 #2/#6/#9/#11/#12 + 試行 ≠ 会話成立判定/ハンドチューニング + 7 系列・観察 1-4 統合禁止 + Synapse データ frozen + 書込み unified/v1106/ 配下) を完了、確認要請 8 回答受領後に Step B から実装着手予定、書込み unified/v1106/ 配下のみ。

---

## 1. §5 Code A 確認要請 1-7 への認識

### 1.1 §5-1: Synapse データの所在と読み込み方

**実環境照合結果**:

| ファイル | 所在 | サイズ | 内容 |
|---|---|---:|---|
| `esde_synapses_v3.json` | `language/synapse/` | 5.5 MB | メイン Synapse データ |
| `synapse_v3.1.json` 〜 `v3.5.json` | `language/synapse/patches/` | 17-2 KB | パッチ |
| `synapse_profiles.json` | `language/synapse/` | 1.4 KB | プロファイル設定 |
| `esde_dictionary.json` | `language/atoms/` | — | atom 辞書 |

**メイン構造** (esde_synapses_v3.json):
```python
{
  '_meta': {'version': '3.0.0', ...},
  'synapses': {
    'vow.n.01': [
      {'concept_id': 'EMO.love', 'axis': 'value_generation', 'level': 'ethical',
       'lemma': 'vow', 'pos': 'n', 'raw_score': 0.4309, 'weight': 0.6179, 'rank': 1},
      {'concept_id': 'ABS.bound', ..., 'weight': 0.3821, 'rank': 2},
      ...
    ],
    ...  # 11,557 word_id
  }
}
```

**統計**:
- **11,557 word_id** (設計書「約 2 万語」≒ 実体 11,557)
- **326 unique atoms** used in Synapse
- 1 word → **1-3 atoms** (mean 1.9, median 2, max 3)
- 1 atom → **13-181 words** (mean **68.4**, max 181)
- **weight 連続値 0-1** (min 0.0065, max 1.0, mean 0.518)
- rank 1-3 (1 word 内の atom 順位)

### 1.2 §5-2: v1105a s7 出力の読み込み方

**実環境照合**:

| ファイル | 所在 | 内容 |
|---|---|---|
| `trial_step4_distributions.parquet` | `unified/v1105a/outputs/main/` | 206,900 rows、構造ラベル付き 7 系列確率分布 |
| `trial_step4_labels.parquet` | 同上 | 420,000 rows、event 別構造ラベル |

s7 (48D raw_density k=5) pipeline_complete events 抽出方法:
```python
dist = pd.read_parquet('trial_step4_distributions.parquet')
s7_pc = dist[(dist['series_id'] == 's7_48d_raw_k5') &
              (dist['structural_label'] == 'distribution_valid')]
# 3,300 events × candidate_atom × probability
```

### 1.3 §5-3: atom_id ↔ Synapse atom_id mapping

**実環境照合結果**: **v1103 atom_centroids (325 atoms) ∩ Synapse atoms (326) = 325 完全一致**、Synapse only 1 件 (誤差レベル)、mapping 不要、両者で同じ atom 名 (ABS.bound 等) を直接使用可能。

### 1.4 §5-4: 接続式 §2.1 の妥当性 (確認要請 8 として §3 で別途扱う)

設計書 §2.1 の `normalize(syn) = syn / 10` は **実体 weight が 0-1 連続値であることと不一致**。詳細は §3 確認要請 8。

**計算量見積もり**:
- pipeline_complete events: 3,300 × 7 系列 = **23,100 event-series**
- per event-series: candidate atoms (mean ~6) × words per atom (mean 68) = **~408 word candidates**
- 合計 word 候補計算: 23,100 × 408 = **9.4M ペア** (動的計算可能、数十秒-数分)

### 1.5 §5-5: word_expansion_ratio / total_word_coverage

**Code A 実装方針**:
- `word_expansion_ratio` = n_words_after / n_candidates_after (per event-series)
- `total_word_coverage` = n_words_after / **11,557** (設計書「20,000 のうち」は v1106 で実体 11,557 に調整)

設計書 §2.4 の「2 万語のうちどの割合」は実体 11,557 word の割合に再定義。設計書 §0.1 の「2 万語」も実体不一致だが、§2.4 の意味は同じ (Synapse 全 word 中のカバレッジ)。

### 1.6 §5-6: v1106a 接続条件 4 点の操作的閾値

**Code A 実装方針** (構造ラベル付与、v1105a §1.1 継承):

| ラベル | 操作的条件 (v1105a §1.1 同型) |
|---|---|
| `word_candidate_empty` | n_words_after == 0 |
| `word_distribution_degenerate` | word_max_prob ≥ 0.999 OR word_prob_ge_0.999_count > 0 |
| `word_distribution_valid` | word_max_prob < 0.999 AND word_entropy > 0 |
| `word_pipeline_complete` | word_distribution_valid 達成 |

接続条件 4 点の判定 (3 条件以上で v1106a、2 条件以下で v1106b) は Web Claude/Taka 領域、Code A は構造ラベル件数・割合のみ報告。

### 1.7 §5-7: 想定実行時間

| Step | 想定実行時間 |
|---|---:|
| B 環境準備 (Synapse + v1105a 読み込み確認) | < 1 分 |
| C 観察 1 (Atom → word 変換、3,300 events × 7 系列) | 数分 |
| D 観察 2 (Synapse 強度と s7 確率の整合、相関指標) | 数分 |
| E 観察 3 (word_expansion_ratio / total_word_coverage) | 数分 |
| F 観察 4 (s7 vs s1-s6 layer_jaccard) | 数分 |
| G bit-identity 3 層 | 数十分 (Step C-F 再実行 + LAYER_B 1,503 files) |
| H 観察事実報告 | — |

合計想定 **30 分-1 時間** (v1105a が 1-3 時間想定だったが、Synapse 接続は post-process のみで動的計算済の v1105a output を使うため軽い)。

---

## 2. 実装可能性

| Step | 内容 | 実装可能性 |
|---|---|:---:|
| B | 環境準備 | ✓ |
| C | 観察 1 (Atom → word 変換) | ✓ (接続要請 8 後) |
| D | 観察 2 (Synapse 強度 vs s7 整合) | ✓ (確認要請 8 後) |
| E | 観察 3 (広がり/絞り) | ✓ (確認要請 8 後) |
| F | 観察 4 (s7 vs s1-s6) | ✓ (確認要請 8 後) |
| G | bit-identity 3 層 | ✓ |
| H | 観察事実報告 | ✓ |

---

## 3. 確認要請 8 (Web Claude/Taka 領域)

**論点**: 設計書 §2.1 接続式 `normalize(syn) = syn / 10` は実体不一致。

**実体**: `esde_synapses_v3.json` の `weight` は **0-1 連続値** (min 0.0065、max 1.0、mean 0.518)、rank は 1-3 (1 word 内の atom 順位)。設計書「1-10 強度」は便宜表現または初版仕様で、実体は連続 weight。

**Code A 案 3 つ**:

| 案 | 内容 | 利点 | 欠点 |
|---|---|---|---|
| **案 A (Code A 推奨)** | weight をそのまま使用 (normalize 不要、設計書 normalize 部分を「weight」に置き換え) | 実体構造に素直、計算簡潔、追加加工なし | 設計書文面の修正必要 |
| 案 B | weight × 10 で 1-10 スケール化、設計書 normalize(syn/10) を適用 | 設計書文面に忠実 | 二度の正規化 (10倍 → ÷10 で元に戻る、無意味な加工) |
| 案 C | rank 反転を使用 (rank=1 → 強度高、rank=3 → 強度低)、`syn_strength = (max_rank+1) - rank` | 順位情報を活用 | weight 情報を捨てる、設計書「1-10」と数値範囲も合わない |

**Code A 推奨**: **案 A** (weight をそのまま score 計算で使用)。

**修正後の接続式**:
```
各単語 word_j の候補確率:
  score(word_j) = Σ_i [ p_s7(atom_i) × syn_weight(atom_i, word_j) ]
  
  (weight は既に 0-1 範囲、normalize 不要)

各 event 内で正規化:
  p_word(word_j) = score(word_j) / Σ_k score(word_k)
```

これは設計書 §2.1 の積構造を維持しつつ実体 weight を直接使用、Aruism 規律違反リスクなし (weight × s7 確率の積で Σ 1.0 になる、緩やか分布)。

**Web Claude/Taka 判断**: 案 A / 案 B / 案 C / 別案要求。

---

## 4. 規律遵守宣言 (Step A 範囲)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.x / v1101a-v1105a + Synapse データ read-only、書込み unified/v1106/ のみ) |
| 絶対格言 #6 (出口の固定) | ✓ (v1106a 接続条件 4 点を §2.7 で事前確定) |
| 絶対格言 #9 (神の手回避) | ✓ (接続式は §2.1 仕様、独自発明なし、確認要請 8 で式微修正のみ) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (7 系列・観察 1-4 統合禁止、別レイヤー保持) |
| 絶対格言 #12 (judgment 回避) | ✓ (success/failure 未使用、構造ラベルのみ、判定は Web Claude/Taka) |
| 全体図位置づけ規律 (§0.1) | ✓ (Atom → Synapse 接続のみ、Operator/分子経由しない明示) |
| 妄想化回避規律 (§0.6) | ✓ (Operator/分子/会話成立/ESDE らしさを語らない) |
| 試行 ≠ 会話成立判定 | ✓ (構造ラベルのみ、意味判定なし) |
| LLM プロキシ呼び出し禁止 | ✓ (本主題は単語候補までで止める) |
| Synapse データ frozen | ✓ (read-only、v1106 で更新しない) |
| 接続式独自発明禁止 | ✓ (Code A 案 A は実体合わせの微修正、独自設計でない) |
| 7 系列・観察 1-4 統合禁止 | ✓ (別レイヤー保持) |
| 書込みパス unified/v1106/ 配下 | ✓ |
| smoke 含めず | ✓ (post-process のみ) |

---

## 5. Step A 完了後の進行 (確認要請 8 への Web Claude/Taka 回答受領後)

1. **確認要請 8 回答**: 接続式 weight 処理方針確定 (Code A 推奨案 A = そのまま使用)
2. 回答受領後 Step B から順次実装:
   - Step B (環境準備)
   - Step C (観察 1: Atom → word 変換)
   - Step D (観察 2: Synapse 強度 vs s7 整合)
   - Step E (観察 3: 広がり/絞り)
   - Step F (観察 4: 7 系列別)
   - Step G (bit-identity 3 層 + 集計)
   - Step H (観察事実報告)

---

## 6. 一文サマリ (再掲)

v1106 設計書 (Synapse 接続点検、問いの形 A 復帰、GPT 監査クリア) を Code A 受領、実環境照合で Synapse データ `language/synapse/esde_synapses_v3.json` 5.5 MB / 11,557 words × 326 atoms (v1103 325 と完全一致) / 1 word → 1-3 atoms / 1 atom → 13-181 words (mean 68.4) / weight 0-1 連続値 (mean 0.52) と特定、Web Claude/Taka 領域への確認要請 1 件提示: 確認要請 8 (接続式 §2.1 normalize(syn)=syn/10 と実体 weight 0-1 連続値の不一致、Code A 推奨案 A weight そのまま使用 = score = Σ p_s7 × weight で正規化、案 B 1-10 スケール化、案 C rank 反転)、§5-1〜7 への回答 (esde_synapses_v3.json 所在 + v1105a outputs から s7 PC events 抽出 + atom mapping 325 完全一致 + 計算量 9.4M ペア動的可 + word_expansion_ratio / total_word_coverage を 11,557 word で実体合わせ + 接続条件は Web Claude/Taka 領域 + 想定 30 分-1 時間)、Step B-H 実装可能性 + 規律遵守宣言 (絶対格言 #2/#6/#9/#11/#12 + 全体図位置づけ + 妄想化回避 + 試行 ≠ 会話成立判定 + LLM 呼び出し禁止 + Synapse データ frozen + 7 系列・観察 1-4 統合禁止 + 書込み unified/v1106/) を完了、確認要請 8 回答受領後に Step B 着手予定、書込み unified/v1106/ 配下のみ。
