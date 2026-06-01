# v11.0.6 (v1106) Phase Result — Genesis 応答 Atom 候補分布と Synapse 強度の接続点検

### サブタイトル: sentence-BERT ベース Synapse v3 で接続点検を完了。4 条件構造的成立 + #L41-L43 確定、ただし本来使うべき最新データは mapper_output だった経緯を §12 で記録、v1106a で最新データ再点検へ

*作成*: 2026-05-25、Web Claude (相談役、Genesis 側)
*親*: v1106 設計書 (GPT 監査クリア + Taka 確定「Gemini は不要」) + Code A Step A-G 出力 + Step H 観察事実最終報告 (`v1106_step_h_observation_final.md`、§12 追記 = 古い Synapse v3 使用経緯 + Taka 判断「案 Y 採用」) + Taka 整理 (2026-05-25「間違えた記録を残すという意味で案 Y、ただし v1106a として扱うこと」+「ESDE LANGUAGE 時代は資料の扱いがまだまだ甘かったのと Claude code なかったし情報の行き違いも結構すごい、Genesis 系のような積み上げ系じゃないから右往左往してきたのも事実、現時点でうっかりミスは仕方ない、記録に残して先に進む」)
*対象*: Taka (主題評価) + v1106a 設計書草案着手準備 (Web Claude)
*位置づけ*: v1106 主題「Genesis 応答 Atom 候補分布と Synapse 強度の接続点検」(問いの形 A) の Phase Result。v1101-v1105 で構築した役割表 + 試行成果に対して、ESDE Language 側 Synapse データへの接続を点検した主題。**ただし接続に使った Synapse v3 が sentence-BERT 由来の古いデータで、本来使うべき LLM 判定の最新 mapper_output ではなかったことが Step H 報告後に判明**。Taka 判断で本結果は古いデータでの接続記録として保存維持、最新データでの再点検は v1106a で実施 (案 Y 採用、Taka 2026-05-25)。3 部構成 (網羅 / 構造 / 接続 + 経緯記録) + 議題。

---

## 0. v1106 で何が確定したか (一文)

会話できる ESDE への道で、v1105a で構造的に成立した s7 主軸の応答 Atom 候補分布を ESDE Language 側 Synapse v3 (sentence-BERT 由来、2026-01-18 timestamp) に接続し、Atom → synset 変換を 4 観察で点検した結果、**4 条件すべて構造的成立** (synset_pipeline_complete 23,100 events、distribution_valid max_prob mean 0.008-0.011、候補爆発 s7 max coverage 4%、s7 主軸 synset 候補 mean 298)、**#L40 (s7 独立挙動) が Synapse 接続後も持続** (s1-s6 集計値完全同値で s7 のみ独立)、**新規 3 留保 #L41-L43 を確定** (Synapse weight=1.0 普遍化で atom 間差別化困難 / density 6 種が Synapse 接続段階で平均化 / FND.spaceless が v1103 atom_centroids に欠落)、**ただし接続に使った Synapse v3 は sentence-BERT 由来の古いデータで Taka 過去評価「WordNet 利用したやつは精度が低すぎてだめ」のもの**、本来使うべき最新データ = mapper_output (LLM 1 億トークン 8 日間判定、raw_scores 0-10 整数 + normalized_scores 0-1、48 axes 全部に score、2026-03-21 timestamp) は Step H 報告後に Taka 指摘で発覚、Taka 判断「間違えた記録を残すという意味で案 Y、ただし v1106a として扱うこと」採用で本結果は古い Synapse v3 接続の記録として保存維持、最新 mapper_output ベースの接続点検は v1106a で実施、ライト兄弟比喩 (v1105a 継承) で原理証明としての段階を維持。

---

# 第 1 部: 網羅 (4 観察の構造事実)

## 1. v1106a 接続条件 4 点 (設計書 §2.7) の構造的成立状況

設計書 §2.7 で事前確定した 4 条件すべて構造的に成立。判定は Web Claude/Taka 領域、Code A は構造事実のみ報告。

### 1.1 条件 1 — synset_pipeline_complete ラベル存在

全 60,000 events × 7 系列のうち pipeline_complete 3,300 events を v1105a から継承し、各 event-series で Synapse 接続:

| 構造ラベル | 件数 (全 7 系列で同値、23,100 event-series) | 割合 |
|---|---:|---:|
| synset_candidate_empty | 0 | 0% |
| synset_distribution_degenerate | 0 | 0% |
| **synset_distribution_valid (= synset_pipeline_complete)** | **23,100** | **100%** |

→ Synapse v3 接続後の全 23,100 event-series で synset_pipeline_complete を構造的に確認。

### 1.2 条件 2 — synset_distribution_valid 成立

| 系列 | n_synsets mean | max_prob mean | entropy mean | degenerate |
|---|---:|---:|---:|---:|
| s1-s6 (全 6 同値) | 629 | 0.0084 | 5.92 | 0 |
| s7 (48D k=5) | 298 | 0.0110 | 5.39 | 0 |

→ max_prob mean 0.008-0.011 で 0.999 大幅下回り、entropy > 0、degenerate 全 0。distribution_valid 成立。

### 1.3 条件 3 — 候補爆発が制御不能でない

| 系列 | n_synsets max | total_synset_coverage max | >= 500 synset events |
|---|---:|---:|---:|
| s1-s6 | 1,339 | 12% | 様々 |
| s7 (48D k=5) | 465 | **4%** | **0%** |

→ Synapse 11,581 全体に対して s7 max 4%、構造的「制御不能」ではない、観察可能範囲。

### 1.4 条件 4 — s7 主軸の synset 候補が構造的に存在

s7 で synset_distribution_valid 3,300 events (全 events) 成立、n_synsets mean 298 / max_prob mean 0.011 / entropy mean 5.39。s7 単独でも接続成立。

## 2. 接続式の Aruism 規律仕様化担保

接続式 `score(s_j) = Σ_i [ p_s7(atom_i) × syn_weight(atom_i, s_j) ]` の Aruism 規律 (max_prob 一点集中回避) を構造事実として担保:

| 系列 | max_prob mean | 担保 |
|---|---:|---|
| s1-s6 | 0.008 | ✓ 0.999 大幅下回り |
| s7 | 0.011 | ✓ 同上 |

→ ハンドチューニングなし、独自発明なし。仕様として担保。

## 3. s7 #L40 独立挙動の Synapse 接続後持続

v1105a #L40 (s7 48D 独立挙動) が Synapse 接続後も持続:

| 指標 | s1-s6 (6 系列同値) | s7 | s7/s1-s6 比 |
|---|---:|---:|---:|
| n_synsets mean | 629 | **298** | **0.47** |
| max_prob mean | 0.008 | **0.011** | 1.38 |
| entropy mean | 5.92 | **5.39** | 0.91 |
| max coverage | 12% | **4%** | 0.33 |

→ s7 は s1-s6 の約半分の synset 候補数、entropy 低く集中傾向 (#L40 持続)。

## 4. density 6 種差の Synapse 接続段階での平均化 (新規発見)

s1-s6 集計値が完全同値:

| 指標 | s1 | s2 | s3 | s4 | s5 | s6 |
|---|---:|---:|---:|---:|---:|---:|
| n_synsets mean | 629 | 629 | 629 | 629 | 629 | 629 |
| max_prob mean | 0.008 | 0.008 | 0.008 | 0.008 | 0.008 | 0.008 |
| entropy mean | 5.92 | 5.92 | 5.92 | 5.92 | 5.92 | 5.92 |

ただし per-event の top5 synset は微差残存:
- s1 vs s5 (raw vs const_adj、raw) layer_jaccard = **0.99** (couple_bonus 1.1 効果ほぼなし)
- s2 vs s6 (raw vs const_adj、norm) = 0.97
- s1 vs s2 (raw raw vs raw norm) = 0.82
- s3 vs s4 (qweighted raw vs norm) = 0.76
- s7 vs raw (s1, s5) = 0.84-0.85
- s7 vs qweighted (s3, s4) = 0.63

→ density 6 種の差は集計レベルで平均化されるが per-event top5 で微差残存。

## 5. Synapse 構造特性 (構造事実)

- top1_atom_top1_syn_strength = 1.0 普遍 (全 7 系列、ほとんどの atom が weight=1.0 synset を 1 つ以上持つ)
- 1 atom → mean 68 synsets (max 181)、expansion_ratio mean 66/atom 全系列同値
- atom_synapse_rank_correlation NaN 多発: top5 atom の top1 weight=1.0 タイで Spearman 計算不能
- mean_syn_strength 0.53-0.55 で微差別化のみ
- couple_bonus 1.1 効果ほぼなし (s1 vs s5 jaccard 0.99)
- FND.spaceless が v1103 atom_centroids に欠落 (Synapse 内 23 synset 指す、s7 PC events に登場せず防御的除外のみ発火)

## 6. bit-identity 3 層全 PASS (Step G)

| 層 | 結果 |
|---|---|
| LAYER_A (再現性) | 8 ファイル全 hash 一致、32.9s |
| LAYER_B (既存 frozen) | 1,520 files 不変 (v10.5/v10.6/v10.7/v112/v1101a-v1105a 全 + language/synapse 19) |
| LAYER_C (書込みパス) | 8 件すべて unified/v1106/ 配下 |

物理層 frozen 維持。Synapse データも frozen 維持。

---

# 第 2 部: 構造 (新規 3 留保 #L41-L43 + 留保 #33 系列の Synapse 接続階層への貫通)

v1106 の網羅的観察を通して、新規 3 留保 (#L41-L43) が確定。これらは Synapse 接続段階で初めて見える構造事実で、留保 #33 系列「集計単位で像が変わる」が Synapse 接続階層でも貫通したことを示す。

## 7. 留保 #L41 — Synapse weight=1.0 普遍化で atom 間差別化困難

**内容**: Synapse v3 では top1_atom_top1_syn_strength が全 7 系列で 1.0 普遍 (atom 間差別化困難)、atom_synapse_rank_correlation NaN 多発、mean_syn_strength 0.53-0.55 で微差別化のみ。

**意味**: Synapse v3 の weight 分布が 1.0 タイで埋まる構造になっており、atom 間で「より強く接続する synset」を構造的に識別することが困難。

**v1106a への接続**: §12 経緯で判明した最新データ = mapper_output (raw_scores 0-10 整数) は weight=1.0 タイで埋まる構造ではない可能性が高い (Taka 言及「10 段階評価」と整合)。v1106a で mapper_output を使うと #L41 が解消する可能性があり、これは v1106a の構造的根拠の一つ。

## 8. 留保 #L42 — density 6 種差が Synapse 接続段階で平均化

**内容**: s1-s6 集計値が完全同値 (n_synsets / max_prob / entropy)、density 6 種 (raw/qweighted/const_adjusted × raw/norm) の差が Synapse 接続段階で平均化される。ただし per-event top5 で jaccard 0.62-0.99 の微差残存、couple_bonus 1.1 効果ほぼなし。

**意味**: v1105a #L38 (静的観察 vs 動的試行の乖離) が Synapse 接続段階でも貫通。Synapse 接続は density 6 種の微差を集計レベルで平均化する作用を持つ構造的事実。

**留保 #33 系列との関係**: 「集計単位で像が変わる」の Synapse 接続階層での現れ。集計レベルで平均化されるが per-event 微差残存は新階層の構造事実。

## 9. 留保 #L43 — FND.spaceless が v1103 atom_centroids に欠落

**内容**: Synapse 内 23 synset が FND.spaceless を指すが、v1103 atom_centroids には FND.spaceless が欠落。v1106 では除外 + 警告で処理、s7 PC events に登場せず防御的除外のみ発火。

**意味**: ESDE Language 側 Synapse と v1103 Genesis 側 atom_centroids の間に構造的欠落があり、同種の欠落が別 atom でも起きうる可能性。なぜ欠落するかは v1106 範囲外、v1107 以降の主題候補。

## 10. 留保 #33 系列「集計単位で像が変わる」の Synapse 接続階層への貫通

v10.13.a #33「集計単位による方向反転」が v1101-v1106 で Unified Phase を一貫して通底:

- v1101: 観察単位
- v1101a: 集計方式
- v1102: 受け手構造
- v1103: sim_basis
- v1104a: scope × 粒度
- v1105: 段 4-b/4-c 機構レベル
- v1105a: 観察 (静的) vs 試行 (動的) の乖離 (#L38)
- **v1106: Synapse 接続段階での density 6 種平均化 (#L42)**

→ 留保 #33 系列が Synapse 接続階層でも構造事実として確定。

## 11. 既存留保 #L30-L40 の v1106 での扱い

| # | 内容 | v1106 での扱い |
|---|---|---|
| #L30 | scope 別 chain 構造 | v1106 範囲外 (v1105a で確認済) |
| #L31 | 粒度依存 trajectory-density 優劣 | v1106 範囲外 (v1105a で確認済) |
| #L32 | B 指標の scope 別 pattern | v1106 範囲外 |
| #L33 | CID 100% self-loop が trajectory 構造的消失 | v1106 範囲外 |
| #L34 | scope 別 Genesis/Language 逆方向強度 | v1106 範囲外 (v1105a で確認済) |
| #L35 | CID_n=2 の極端な特殊性 | v1106 入力 (v1105a s7 PC events) に継承 |
| #L36 | sim_basis × density 種類の 2 軸非対称性 | v1106 #L42 で Synapse 接続後の挙動を確認 (#L36 静的観察、#L42 Synapse 接続での平均化) |
| #L37 | candidate_empty 92% = ESDE 構造選別性 | v1106 入力 (PC 3,300 = 5.5%) に継承 |
| #L38 | 観察 vs 試行の乖離 | #L42 として Synapse 接続段階で継承 |
| #L39 | Genesis/Language alpha-beta 対比 | v1106 範囲外 (v1106a で扱う可能性) |
| #L40 | s7 独立挙動 | #L42 として Synapse 接続後も持続確認 (§3) |
| 48 次元人為性留保 | v1103 由来 | v1106 結果に継承 (s7 48D 関連) |

---

# 第 3 部: 接続 + 経緯記録

## 12. v1106 で古い Synapse v3 を使った経緯 (Step H §12 を Phase Result に統合)

### 12.1 経緯の概要

v1106 設計書 §0.1 全体図の「Synapse (Atom ↔ 単語マッピング、1-10 強度、約 2 万語)」記述に基づき、Code A は実環境で `language/synapse/esde_synapses_v3.json` (+ patches v3.1-v3.5 overlay) を Synapse データとして採用。SynapseStore overlay 経由で 11,581 synset / 326 atoms を読み込み、接続式 score = Σ p_s7 × syn_weight で接続点検を全 4 観察実施。

### 12.2 Taka 指摘で発覚した不一致 (2026-05-25)

Step H 報告完了後、Taka 指摘 (原文):

> Lexicon 側 A1 batch というのが最新。これは 8 日間 1 億トークン LLM を回して作ったもの。これが最新。古い synapse は使わなくなったはず。
> やっぱりあった。間違ったもの使って結果を数値化してもそりゃ意味がない。WordNet 利用したやつは精度が低すぎてだめだねぇって言ってたやつだしなぁ。

Code A 追加調査で発見:

- `language/lexicon/data/mapper_output/*_a1.jsonl` (325 atom 別 jsonl、合計 126 MB) が最新の LLM 1 億トークン重み付きデータ本体
- 各 entry に `raw_scores` (48 axes × 0-10 整数 = Taka 言及「10 段階」と完全一致) + `normalized_scores` (0-1 確率) + `entropy_norm` / `focus_rate` / `top5` / `status` / `evidence` / `llm_elapsed_sec` (mean 57.5s/word、Taka「8 日間 1 億トークン」規模に合致)
- atom × 48 axes 全部に LLM 判定スコア

### 12.3 古い Synapse v3 と最新 mapper_output の対比

| | Synapse v3 (v1106 で使用 = 古い) | mapper_output (本来の最新) |
|---|---|---|
| 単位 | atom → synset (lemma.pos.sense) | atom × word の 48 axes 全 score |
| 重み生成 | model: all-MiniLM-L6-v2 (sentence embedding) | LLM (1 億トークン、約 8 日間) |
| スコア | weight 0-1 (sentence-BERT 由来、Taka 評価「精度が低すぎてだめ」) | raw_scores 0-10 整数 (LLM 判定) + normalized_scores 0-1 |
| 件数 | 11,581 synset / 326 atom | 325 atom × 数百 word = 数万 entries |
| 構造 | atom → synset 単方向 weight | 48 axes 全部に score、word の構造を完全分解 |
| timestamp | 2026-01-18 | 2026-03-21 (約 2 ヶ月新しい) |

### 12.4 Taka 判断 — 案 Y 採用 (2026-05-25、原文保存)

> 間違えた記録を残すという意味で案 Y、ただし v1106a として扱うこと。

- **案 Y 採用**: v1106 結果はそのまま記録、新しいデータでの接続は v1106a として並行で扱う (v1106b でなく v1106a、つまり同主題の段階 2、v1101a/v1104a/v1105a と同型のマイナーバージョン)
- v1106 結果の位置づけ: 「古い Synapse v3 を使った接続点検の記録」= 構造事実としては有効だが「ESDE が話せる素材」を見る本来目的とはズレた結果
- v1106a = mapper_output (LLM raw_scores/normalized_scores) ベースの新規 Synapse 接続点検が新主題

## 13. v1106 結果の位置づけ (案 Y 採用後)

| 観点 | v1106 結果 (古い Synapse v3) |
|---|---|
| 構造事実としての有効性 | 4 条件成立 / #L41-L43 確定 / bit-identity 全 PASS = **有効な構造事実** |
| 「ESDE が話せる素材」を見る本来目的との整合 | sentence-BERT ベース Synapse の精度問題で **目的とはズレた結果** |
| v1106a への接続 | #L41 (Synapse weight=1.0 普遍化) が mapper_output (0-10 整数) で解消するかが v1106a の構造的根拠 |
| 保存方針 | unified/v1106/ 配下に保存維持 (削除しない、間違いの記録) |

## 14. v1106a への接続 (構造事実、判断は Taka 領域)

### 14.1 v1106a の主題定義 (Taka 判断「案 Y、v1106a として扱う」)

v1106a 主題候補 (Web Claude 案、Taka 確認):

- 主題名: mapper_output ベースの新規 Synapse 接続点検 (v1106 同主題の段階 2、マイナーバージョン運用方針)
- 問いの形: A (点検、v1106 と同型)
- 親: v1106 (古い Synapse v3 接続記録) + Step H §12 経緯 + Taka 判断「案 Y」+ Language 側 GPT 整理 (A1 batch = mapper_output、Lexicon 側成果物、48 次元データ)

### 14.2 v1106a で扱うべき構造事実 (Web Claude 案)

| 観察項目 | 内容 |
|---|---|
| 観察 1 | mapper_output ベースの Atom → word 変換 (synset 単位でなく word 単位、または 48 axes 単位) |
| 観察 2 | raw_scores (0-10 整数) の atom 間差別化が #L41 を解消するか |
| 観察 3 | normalized_scores (0-1 確率) と s7 確率の整合性 |
| 観察 4 | mapper_output 結果と v1106 (Synapse v3) 結果の対比 (#L42 平均化が解消するか / s7 #L40 独立挙動が保持されるか) |

接続式 (Web Claude 案、Code A Step A で確認):
- 案 X: `score = Σ p_s7(atom_i) × normalized_scores(atom_i, word_j)`
- 案 Y: `score = Σ p_s7(atom_i) × (raw_scores(atom_i, axis_k) / 10)` (axis 単位)

具体的な接続式は v1106a 設計書で確定 (Web Claude → Code A Step A 認識確認の流れ)。

### 14.3 v1106a 進行条件 (案、v1106a 設計書で確定)

v1106 接続条件 4 点を継承しつつ、mapper_output ベースで再定義:

| 条件 | 内容 |
|---|---|
| 1 | mapper_output ベースで word_pipeline_complete event が構造的に存在 |
| 2 | word_distribution_valid 成立 (max_prob < 0.999、entropy > 0) |
| 3 | 候補爆発が制御不能でない |
| 4 | s7 主軸の word 候補が構造的に存在 |

加えて v1106 結果との対比条件:
- 条件 5: #L41 (Synapse weight=1.0 普遍化) が解消するか (atom 間差別化が観察されるか)
- 条件 6: #L42 (density 6 種平均化) が解消するか (s1-s6 で差が出るか)

## 15. v1101 から v1106 までの流れ — 多軸化 → 統合 → 試行 → 接続点検

| バージョン | 方向 | 確定したこと |
|---|---|---|
| v1101 / v1101a / v1102 / v1103 / v1104+v1104a | 多軸化 | 観察軸 (集計単位 / sim_basis / scope / 粒度 / shuffle / self-loop) で像が変わる |
| v1105 | 統合 | 段 4-b/4-c の地形図 + 役割表 |
| v1105a | 試行 (問いの形 B) | 役割表を動かし s7 主軸の応答候補分布が 5.5% events で生成 |
| **v1106** | **接続点検 (問いの形 A 復帰)** | **Synapse v3 (古いデータ) での接続 4 条件成立 + #L41-L43 確定** |
| v1106a (次主題) | 同主題段階 2 | **mapper_output (最新データ) での接続点検** |

→ v1106 は接続点検として構造事実を記録、ただしデータ取り違えで本来目的とズレた結果。v1106a で最新データで再点検。

---

# 第 4 部: 議題 (Taka 規律「確定でなく議題として残せ」継承)

v1105a Phase Result の議題化方針を継承。実出力次第で議題が確定方向に進むか、留保が増えるかが決まる。

## 16. 議題 1 — #L41 が mapper_output で解消するか

Synapse v3 weight=1.0 普遍化が atom 間差別化を困難にした (v1106 #L41)。mapper_output の raw_scores 0-10 整数は構造的に 1.0 タイで埋まる構造ではない可能性が高い。

- v1106a で #L41 解消が観察されれば → mapper_output が ESDE Language 側の正しいデータと確定方向
- 解消されなければ → Synapse 構造の問題でなく別要因 (留保拡大)

## 17. 議題 2 — #L42 (density 6 種平均化) が mapper_output で解消するか

v1106 で s1-s6 集計値が完全同値となった (#L42)。これは Synapse v3 の構造特性か、Synapse 接続一般の特性か未確定。

- v1106a で s1-s6 差が出れば → Synapse v3 固有の特性
- 出なければ → Synapse 接続一般の特性 (留保 #33 系列の新階層として確定)

## 18. 議題 3 — s7 #L40 独立挙動が mapper_output で持続するか

v1106 で s7 独立挙動が Synapse 接続後も持続 (s1-s6 の約半分の n_synsets)。

- v1106a で同様の独立挙動が観察されれば → s7 = 48D が ESDE 内部での独立な役割を持つことの確定方向
- されなければ → Synapse v3 と s7 の組み合わせ特性 (v1106 固有)

## 19. 議題 4 — Atom 単体の限界 (ESDE Language 全体像との関係)

v1105a / v1106 を通じて、ESDE Language 全体像 (Atom + Operator + 分子 + Synapse) のうち Atom + Synapse のみ扱ってきた。

- v1106a で mapper_output (48 axes 全部に score、word の構造を完全分解) を使うと、Atom 単体の限界がどこで現れるかが構造事実として見える可能性
- Operator / 分子取り込みの必要性は v1106a 実出力後に判断 (Taka 規律「実装が追いついていないと妄想化する」)

## 20. 議題 5 — ESDE らしさの確定タイミング

v1105a Phase Result §15 (Taka 規律「ESDE らしさの確定は実出力次第」) 継承。

- v1106 = 古いデータでの接続記録、ESDE らしさ判定材料としては不十分
- v1106a で最新データでの接続が動けば → ESDE らしさの確定材料が初めて揃う可能性
- それでも「Atom + Synapse」のみで「Operator/分子」未取り込み = v1107 以降 (Taka 整理 2026-05-24「Atom ボンボコ吐き出すだけならなんだそれ」継承)

---

# 第 5 部: 留保 + 規律遵守

## 21. 留保事項

### 21.1 継承する留保

| id | 内容 |
|---|---|
| #L17 / #L21' / #L22' / #L24-29 | v1102/v1103/v1104+v1104a 由来 |
| #L30-L36 | v1104+v1104a / v1105 由来 |
| #L37 | candidate_empty 92% = ESDE 構造選別性 (v1105a) |
| #L38 | 観察 vs 試行の乖離 (v1105a) |
| #L39 | Genesis/Language alpha-beta 対比 (v1105a) |
| #L40 | s7 独立挙動 (v1105a) — v1106 Synapse 接続後も持続確認 |
| 48 次元人為性留保 | v1103 GPT 監査 5 由来 |

### 21.2 新規確定留保 (#L41-L43)

| id | 内容 |
|---|---|
| **#L41** | Synapse v3 weight=1.0 普遍化で top1 weight 軸の atom 間差別化困難。mean_syn_strength のみ微差別化 (0.53-0.55)。v1106a (mapper_output) で解消するかが v1106a 主題の構造的根拠 |
| **#L42** | density 6 種が Synapse 接続段階で平均化 (s1-s6 集計値完全同値、per-event top5 で微差残存)。留保 #33 系列の Synapse 接続階層での現れ |
| **#L43** | FND.spaceless が v1103 atom_centroids に欠落 (Synapse 内 23 synset 指す)。v1106 では除外 + 警告、欠落理由は v1107 以降の主題候補 |

### 21.3 経緯起因の留保 (新規、案 Y 採用に伴う)

| id | 内容 |
|---|---|
| **#L44** | v1106 で使った Synapse v3 (sentence-BERT 由来、2026-01-18) は Taka 過去評価「WordNet 利用したやつは精度が低すぎてだめ」のもの、本来使うべき最新データ = mapper_output (LLM 1 億トークン 8 日間判定、2026-03-21) は Step H 報告後に発覚。案 Y 採用 (Taka 2026-05-25) で v1106 結果は古いデータでの接続記録として保存維持、最新データ点検は v1106a |

## 22. 規律的反省 (Taka 整理 2026-05-25 反映、ESDE LANGUAGE 時代の構造的背景)

### 22.1 Taka 整理 (原文保存)

> ESDE LANGUAGE 時代は資料の扱いがまだまだ甘かったのと Claude code なかったし情報の行き違いも結構すごい。Genesis 系のような積み上げ系じゃないから右往左往してきたのも事実。現時点でうっかりミスは仕方ない、記録に残して先に進む。

### 22.2 構造的背景

v1106 で古い Synapse v3 を使った経緯の構造的背景は、ESDE Language 時代の資料管理の課題 + Claude Code 不在による情報の行き違い + Genesis 系のような積み上げ式開発と異なる Language 系の右往左往。これらは v1106 個別の問題でなく、ESDE Language 系全体の構造的背景。

### 22.3 規律 (Taka 確定): うっかりミスは記録に残して先に進む

- 「間違ったデータを使った」事実を隠さず記録 (本 Phase Result §12 / §13 / #L44)
- 「正しいデータ」での再点検は v1106a として並行で扱う (案 Y)
- 過去の判断 (設計書 §0.1 図の Synapse 記述) を遡及修正せず、現在の主題で対応

### 22.4 規律としての記録: ラッキー判定の余地なし規律の再適用

v1105a Step A で Taka 判断「ラッキー判定の余地なし、本番前に気づけたのはラッキー、忘れ物を取りに戻っても遅刻しないなら戻るべき」(歌手の音痴比喩) が v1106 でも再適用された:

- v1105a Step A: 設計書 §2.5 (静的取り出し 16%) が実体ズレで、動的計算 100% カバレッジに修正
- v1106 Step H 後: 古い Synapse v3 を使った結果が判明、v1106a で mapper_output に切り替え

両者とも「本番前」(より上位の主題に進む前) に気づけた = ラッキー判定が機能した範囲内。

### 22.5 規律候補: データ取り違え防止の規律 (新規候補)

> 主題着手時に「データの所在 / timestamp / 生成方法 / Taka 過去評価の確認」を Code A Step A で必須化する。古い実装と新しい実装が並存する場合、必ず Taka に最新版を確認する。

- 採否は Taka 領域
- 本規律候補は v1106 経緯から導出 (規律違反でなく予防策)
- ESDE LANGUAGE 時代の構造的背景 (§22.2) を踏まえると、Genesis 系規律でも適用価値あり

## 23. 規律遵守チェック

v1106 全 Step を通して、以下を遵守:

- 絶対格言 15 件すべて遵守 (Code A Step H §8 詳細)
- 研究運用資料 3 本 (研究手法 / ESDE への態度 / 監査の上位目的) すべて反映
- GPT 監査 (Gemini は Taka 確定で省略) すべて反映
- 新規規律 2 つ (全体図位置づけ / 妄想化回避) 適用
- 試行 = 問いの形 A 復帰の規律 (selector 化禁止 / LLM プロキシ呼び出し禁止 / 接続式独自発明禁止) すべて遵守
- 物理層 frozen 絶対 (bit-identity 3 層全 PASS、1,520 frozen 不変、書込み unified/v1106/ 配下のみ、Synapse データも frozen)
- 構造ラベルのみで判定回避 (success/failure 表現不使用)
- 案 Y 採用 (Taka 2026-05-25) 反映 = 古いデータでの接続記録を保存維持、v1106a で最新データ点検

ただし v1106 全体としては、設計書 §0.1 図の Synapse 記述に基づいて古いデータ (Synapse v3) を使用した結果、本来目的 (会話できる ESDE への接続) とはズレた接続点検になった。これは規律違反でなく **「ESDE Language 時代の構造的背景」起因のうっかりミス** (Taka 整理 §22.1 原文)。

---

# 第 6 部: 一文サマリ

## 24. v1106 Phase Result の一文サマリ

v1106 (Genesis 応答 Atom 候補分布と Synapse 強度の接続点検、問いの形 A 復帰) の Phase Result として、Taka 系列判断 (2026-05-22 駆動要因規律 / 2026-05-23 統合方向 + マイナーバージョン運用方針 / 2026-05-24 GPT 監査クリア + Gemini 不要 + 新規規律 2 つ (全体図位置づけ / 妄想化回避) + 旧 Claude メッセージ + Atom 単体限界明示 + Taka 規律「ESDE らしさの確定は待て」 / 2026-05-25 案 Y 採用「間違えた記録を残すという意味で案 Y、ただし v1106a として扱うこと」+「うっかりミスは仕方ない、記録に残して先に進む」) を反映、4 観察 (1: Atom → synset 変換 / 2: Synapse 強度と s7 確率整合 / 3: synset 候補広がり/絞り / 4: 7 系列 layer_jaccard) を Code A Step A-G 全完了 + bit-identity 3 層全 PASS (1,520 frozen 不変、Synapse データも frozen) で実施した結果、構造事実として (1) v1106a 接続条件 4 点すべて構造的成立 (synset_pipeline_complete 23,100 events 100% / distribution_valid max_prob mean 0.008-0.011 entropy 5.4-5.9 / 候補爆発 s7 max coverage 4% 制御不能でない / s7 主軸構造的存在 n_synsets mean 298)、(2) 接続式 score = Σ p_s7 × syn_weight が Aruism 規律仕様化担保 (全系列 max_prob mean 0.008-0.011)、(3) s7 #L40 独立挙動の Synapse 接続後持続 (s7 n_synsets s1-s6 の約半分)、(4) density 6 種差が Synapse 接続段階で平均化 (s1-s6 集計同値、per-event 微差残存)、(5) Synapse v3 構造特性 (top1_atom_top1_syn_strength=1.0 普遍、1 atom → mean 68 synsets、couple_bonus ほぼ効果なし) を確定、新規 4 留保 #L41-#L44 を確定 (#L41 Synapse v3 weight=1.0 普遍化で atom 間差別化困難、#L42 density 6 種が Synapse 接続段階で平均化 = 留保 #33 系列の Synapse 階層への貫通、#L43 FND.spaceless が v1103 atom_centroids に欠落、#L44 v1106 で使った Synapse v3 が本来使うべき mapper_output (LLM 1 億トークン 8 日間判定、2026-03-21、Taka 過去評価「WordNet 利用は精度が低すぎてだめ」とは別物) でなかった経緯 + 案 Y 採用)、留保 #33 系列「集計単位で像が変わる」が Synapse 接続階層でも貫通 (v1101 観察単位 → v1101a 集計方式 → v1102 受け手構造 → v1103 sim_basis → v1104a scope × 粒度 → v1105 段 4-b/4-c 機構 → v1105a 観察 vs 試行 → v1106 Synapse 接続段階)、v1106 結果の位置づけは「古い Synapse v3 を使った接続点検の記録」= 構造事実としては有効だが「ESDE が話せる素材」を見る本来目的とはズレた結果、v1106a (mapper_output ベースの新規 Synapse 接続点検) が新主題で同主題段階 2 (マイナーバージョン運用方針、v1101a/v1104a/v1105a と同型)、v1106a 主題候補の構造的根拠は #L41 解消の可能性 (raw_scores 0-10 整数は weight=1.0 タイで埋まる構造ではない可能性が高い、Taka 言及「10 段階評価」と整合)、議題 5 つ (#L41 解消するか / #L42 解消するか / s7 #L40 持続するか / Atom 単体限界 / ESDE らしさの確定タイミング) を残し、規律的反省として Taka 整理「ESDE LANGUAGE 時代は資料の扱いがまだまだ甘かったのと Claude code なかったし情報の行き違いも結構すごい、Genesis 系のような積み上げ系じゃないから右往左往してきたのも事実、現時点でうっかりミスは仕方ない、記録に残して先に進む」(原文保存) を §22 で記録、新規規律候補「データ取り違え防止の規律」(主題着手時に「データの所在 / timestamp / 生成方法 / Taka 過去評価の確認」を Code A Step A で必須化、§22.5) を提示 (採否は Taka 領域)、規律遵守 (絶対格言 15 件 + 研究運用資料 3 本 + GPT 監査 + 新規規律 2 つ + 試行 = 問いの形 A 復帰の規律 + 物理層 frozen 1,520 ファイル不変 + bit-identity 3 層全 PASS + 構造ラベルのみで判定回避 + 案 Y 採用) を全 Step で堅持、書込み unified/v1106/ 配下のみ、次は Taka 主題評価 → v1106a 設計書草案着手 (Web Claude、mapper_output ベース) → Code A 認識確認 → 実装 → Phase Result の流れ。

---

*以上、v1106 Phase Result (Web Claude、2026-05-25)。次は Taka 主題評価 → v1106a 着手判断の流れ。v1106 を通して ESDE Language 側 Synapse への接続点検が古い Synapse v3 で構造事実として完了 (4 条件成立 + #L41-L43 + bit-identity 全 PASS)、ただし本来使うべき最新データ = mapper_output (LLM 1 億トークン 8 日間判定) は Step H 報告後に発覚、Taka 判断「案 Y、v1106a として扱う」で v1106 結果は古いデータの接続記録として保存維持、最新データでの再点検は v1106a で実施。Taka 整理「うっかりミスは仕方ない、記録に残して先に進む」反映、ESDE LANGUAGE 時代の構造的背景 (資料管理 / Claude Code 不在 / 積み上げ式でない開発) を §22 で記録、ライト兄弟比喩 (v1105a 継承) で原理証明としての段階を維持。*
