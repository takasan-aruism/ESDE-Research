# v11.0.6a (v1106a) Step J 観察事実最終報告 — Code A

*作成*: 2026-05-26、Code A
*親*: `v1106a_phase_design.md` v3 + `v1106a_step_a_recognition.md` + `v1106a_step_a_answer.md` (確認要請 11 案 Z-1 採用) + `docs/atom_extraction_check/atom_extraction_mechanism_2026-05-26.md` (Atom 抽出仕組み記録) + Step B-I 出力
*対象*: Web Claude (Phase Result 統合担当、Step K) + Taka (主題評価 + v1106b/v1107/v1106c 着手判断)
*位置づけ*: v1106a 主題 (v1106 同主題段階 2、mapper_output ベース) の Code A 観察事実総括。**judgment 回避** (絶対格言 #12)、**構造ラベルのみ**、**LLM プロキシ呼び出し禁止**、**Operator/分子・会話成立・ESDE らしさ語らない (妄想化回避)**、**mapper_output + Synapse v3 frozen**、**接続式独自発明禁止**、**v1106 結果との対比を「正しい/間違い」で判定しない**。

---

## 0. 一文サマリ

v1106a 主題 (v1106 同主題段階 2、mapper_output LLM 1 億トークン 8 日間判定ベース) Step A-I 全完了、Step A (確認要請 11 案 Z-1 採用 = normalized_scores_max 設計書通り、Code A 推奨案 Z-1 承認 + 案 X (raw_scores_max) 主軸の並列実行 + Atom 抽出確認 7 件 = Atom A 固定 326 + B cid 揺れる ハイブリッド構造 + 48 axes と Atom yyy は別構造、v1106a 現状設計のまま修正不要、#L43 mapper_output ベースで構造的解消) → Step B (環境準備、SynapseStore overlay + mapper_output 325 jsonl 125.2 MB + v1105a s7 PC events 14,600 rows + atom mapping v1103 325 = mapper_output 325 完全一致 + LAYER_B baseline 2,180 files) → Step C (観察 1 Atom → word 変換、案 X + 案 Z-1 並列、32.9M rows / 46,200 event-series-formula 全 word_distribution_valid 100%、n_words mean s1-s6 774 / s7 348、max_prob mean X 0.011 / Z1 0.014、Z1 約 30% 高、entropy X 6.03 / Z1 5.94) → Step D (観察 2 mapper_output と s7 整合、top1_score mean 案 X 10.0 普遍 / 案 Z-1 0.89-0.92、atom_word_rank_correlation 案 X NaN / 案 Z-1 mean -0.034 で無相関、top1 tied 案 X 100% / 案 Z-1 0%) → Step E (観察 3 word 候補広がり/絞り、案 X と Z-1 候補数完全同値、s7 max coverage 8.15% / s1-s6 14% で観察可能範囲、expansion_ratio 76/atom = Lexicon per atom mean 87 word に近い) → Step F (観察 4 7 系列 word layer_jaccard、s1 vs s5 = 案 X 1.00 / Z-1 0.99 = couple_bonus 効果ほぼなし、s7 vs raw 系列 = X 0.79 / Z-1 0.84、s7 vs qweighted = 0.63-0.68) → Step G (観察 5 #L41 解消確認、案 X top1_tied_rate 100% で v1106 と完全同型、案 Z-1 top1_tied 0% で tied 解消するが rc_mean -0.15〜+0.08 / positive_rate 39-52% で **無相関 (rank correlation 構造そのもの存在せず)**、→ **#L41 は Synapse v3 固有でなく Atom-word 関係の構造的特性として確定**) → Step H (観察 6 #L42 解消確認、s1-s6 n_words std=0 完全同値が 3 ソースすべて (v1106 + 案 X + 案 Z-1) で同型、max_prob/entropy 微小差で実質同値、s1 vs s5 jaccard = 案 X 1.00 全 3,300 events 完全一致 / 案 Z-1 0.99 (97% 完全一致)、→ **#L42 も Atom-word 関係の構造的特性として確定**) → Step I (bit-identity 3 層全 PASS: LAYER_A 9 ファイル全 hash 一致 105s、LAYER_B 2,180 frozen files 不変 (mapper_output 325 + a1_batch 327 + synapse 19 含む)、LAYER_C 9 件全て unified/v1106a/ 配下) すべて完了、核心構造事実 (judgment なし、Code A 報告のみ): **(1) v1106a 進行条件 6 点のうち 4 条件 (v1106 継承) は構造的成立、対比 2 条件 (#L41 / #L42 解消) は両方とも構造的に持続 = 「解消しない」方向**、(2) **#L41/#L42 は Synapse v3 固有の特性でなく Atom-word 関係そのものの構造的特性として確定** (mapper_output 案 X/Z-1 両方で持続)、(3) **mapper_output (LLM 1 億トークン 8 日間判定) は v1106 Synapse v3 (sentence-BERT) より広いカバレッジ** (n_words mean 774 vs 629、unique 17,790 word vs 11,581 synset)、(4) **s7 #L40 独立挙動 mapper_output でも持続** (s7 n_words 348 約半分、max_prob 30% 高、entropy 低)、(5) **#L43 (FND.spaceless 欠落) は mapper_output ベースで構造的解消** (mapper_output に最初から存在せず、v1103 atom_centroids 325 = mapper_output 325 完全一致)、(6) **案 X vs 案 Z-1 対比**: top1_tied は raw_scores 構造 (案 X) vs normalized_scores 構造 (案 Z-1) で挙動異なるが、相関構造の不在 (rank_correlation 無相関) は両者で同型、(7) **設計書 §1.4 進行条件分岐 (4 + 5/6 解消 → v1106b / 4 + 5/6 部分解消 → v1107 先検討 / 4 未成立 → v1106c)** に照らすと **v1107 (Atom 単体限界対応) を先検討** に該当する方向の構造事実、新規留保候補 #L44-L46 提示: #L44 (#L41/#L42 は Synapse データ全般の特性でなく Atom-word 関係そのものの構造特性、データソース変更では解消しない)、#L45 (s7 高 prob atom と word score の rank_correlation 無相関 = atom 確率分布と word score の関係性そのものが Atom-word レイヤーに存在しない)、#L46 (couple_bonus 1.1 効果が案 X で完全消失 raw_scores_max ベースでは構造的にゼロ)、既存留保 #L17/#L21'/#L22'/#L24-29/#L30-L36/#L37-L40/#L41-L43 + 48 次元人為性留保継承、最終判定 (v1106b 着手 vs v1107 vs v1106c) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 #2/#5/#6/#9/#11/#12 + データ取り違え防止規律初適用 + 全体図位置づけ + 妄想化回避 + mapper_output/Synapse v3 frozen + 接続式独自発明禁止 + 7 系列・案 X/Z-1 統合禁止 + v1106 結果との対比を「正しい/間違い」で判定しない + mapper_output 自体の品質判定しない + 48 axes 意味解釈 v1107 以降) を全 Step で堅持、書込み unified/v1106a/ 配下のみ。

---

## 1. Step A-I 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A | 認識確認 + 確認要請 11 + Atom 抽出確認 7 件 | 完了 (Taka 承認 案 Z-1 + Atom 構造把握) | v1106a_step_a_recognition.md + v1106a_step_a_answer.md + docs/atom_extraction_check/ |
| B | 環境準備 (mapper_output + v1105a + LAYER_B baseline) | 完了 | v1106a_step_b_env_check.py |
| C | 観察 1 (Atom → word 変換、案 X + 案 Z-1 並列) | 完了 (51s) | observation_1_word_distributions.parquet (32.9M) + observation_1_labels.parquet (46,200) |
| D | 観察 2 (mapper_output と s7 整合) | 完了 (8.8s) | observation_2_mapper_alignment.parquet (46,200) |
| E | 観察 3 (word 候補広がり/絞り) | 完了 (0.2s) | observation_3_expansion + observation_3_summary |
| F | 観察 4 (7 系列 word layer_jaccard) | 完了 (21.2s) | observation_4_layer_jaccard (98) + observation_4_series_comparison (14) |
| G | 観察 5 (#L41 解消確認) | 完了 (0.1s) | observation_5_L41_resolution (14) |
| H | 観察 6 (#L42 解消確認) | 完了 (17.7s) | observation_6_L42_resolution (3) |
| I | bit-identity 3 層検証 | 完了 (all PASS、105s) | v1106a_step_i_bit_identity_report.json |
| J | 観察事実最終報告 | 本書 | v1106a_step_j_observation_final.md |
| K | Phase Result (v1106b/v1107/v1106c 着手判断) | 待ち | Web Claude 担当 |

---

## 2. v1106a 進行条件 6 点 (§1.4) 構造事実

**Code A 判定なし、構造的観察事実のみ報告。判定は Web Claude/Taka 領域**。

### 2.1 条件 1: word_pipeline_complete event の構造的存在

| 構造ラベル | 件数 (全 7 系列 × 案 X/Z-1 = 46,200 event-series-formula) | 割合 |
|---|---:|---:|
| word_candidate_empty | 0 | 0% |
| word_distribution_degenerate | 0 | 0% |
| **word_distribution_valid (= word_pipeline_complete)** | **46,200** | **100%** |

→ ✓ 構造的成立

### 2.2 条件 2: word_distribution_valid 成立

| 系列 | n_words mean | max_prob mean (X / Z1) | entropy mean (X / Z1) | degenerate count |
|---|---:|---:|---:|---:|
| s1-s6 (全 6 同値) | 774 | 0.011 / 0.014 | 6.03 / 5.94 | 0 |
| s7 (48D k=5) | 348 | 0.014 / 0.019 | 5.45 / 5.35 | 0 |

→ ✓ 成立: max_prob mean 0.011-0.019 で 0.999 大幅下回り、entropy > 0、degenerate 0

### 2.3 条件 3: 候補爆発が制御不能でない

| 系列 | n_words max | coverage_unique max | coverage_lexicon max | >= 2000 events |
|---|---:|---:|---:|---:|
| s1-s6 | 2,486 | 14% | 7.6% | 0 |
| s7 | 1,450 | **8.15%** | **4.44%** | 0 |

→ ✓ 観察可能範囲 (s7 max coverage 8.15%、>= 2000 words 0% events)

### 2.4 条件 4: s7 主軸の word 候補が構造的に存在

s7 (48D k=5) で word_distribution_valid 3,300 events × 案 X/Z-1 = 6,600 全 event-series-formula、n_words mean 348 / max_prob mean 0.014 (X) / entropy mean 5.45

→ ✓ s7 主軸構造的存在

### 2.5 条件 5: #L41 解消確認 (raw_scores 0-10 整数で atom 間差別化)

| 指標 | v1106 (Synapse v3) | v1106a 案 X | v1106a 案 Z-1 |
|---|---:|---:|---:|
| top1_score mean | 1.0 (=max) | **10.0 (=max)** | 0.89-0.92 |
| top1_tied_rate | 100% | **100%** | 0% |
| rc 計算可能率 | 0% (NaN) | 0% (NaN) | 87.9% |
| rc_mean | NaN | NaN | -0.15 〜 +0.08 |
| rc positive_rate | NaN | NaN | **39-52% (ランダム)** |

→ **解消しない方向の構造事実**:
- 案 X (raw_scores_max=10) は v1106 と完全同型 (top1=10 タイ完全)
- 案 Z-1 (normalized_scores) では tied 解消するが **相関構造そのものがない** (rank_correlation 無相関)

### 2.6 条件 6: #L42 解消確認 (s1-s6 集計値の差)

| 指標 | v1106 (Synapse v3) | v1106a 案 X | v1106a 案 Z-1 |
|---|---:|---:|---:|
| s1-s6 n_words std | **0** | **0** | **0** |
| s1-s6 max_prob std | 0.000036 | 0.000053 | 0.000154 |
| s1-s6 entropy std | 0.0023 | 0.0023 | 0.0040 |
| s1 vs s5 layer_jaccard | 0.9899 | **1.0000** | 0.9899 |
| per-event 完全一致率 (s1 vs s5) | - | **100%** (3,300/3,300) | 96.97% |

→ **解消しない方向の構造事実** (3 ソースすべてで s1-s6 n_words std=0 完全同値、max_prob/entropy 微小差)

### 2.7 6 条件統合の構造事実

| 条件 | 状態 |
|---|---|
| 1 word_pipeline_complete 存在 | ✓ 成立 (100%) |
| 2 word_distribution_valid 成立 | ✓ 成立 |
| 3 候補爆発制御可能 | ✓ 観察可能範囲 |
| 4 s7 主軸構造的存在 | ✓ 成立 |
| **5 #L41 解消** | **持続方向 (解消しない)** |
| **6 #L42 解消** | **持続方向 (解消しない)** |

→ **4 条件 + 5/6 部分解消 (両方とも持続)** = 設計書 §1.4 の **v1107 (Atom 単体限界対応) を先検討** に該当する方向の構造事実。Web Claude/Taka 領域で v1107 vs v1106b vs v1106c を判定。

---

## 3. #L41/#L42 が Atom-word 関係の構造的特性として確定 (核心発見)

### 3.1 構造的特性の確定根拠

v1106 で発見された #L41 (atom 間差別化困難) / #L42 (s1-s6 平均化) を **Synapse v3 固有の現象か、Atom-word 関係そのものの構造特性か** を切り分けるのが v1106a の核心目的だった。

| データソース | weight 体系 | #L41 結果 | #L42 結果 |
|---|---|---|---|
| v1106 Synapse v3 | sentence-BERT、weight 0-1 (top1=1.0 普遍) | 持続 (top1_tied 100%) | 持続 (s1-s6 std=0) |
| **v1106a 案 X (raw_scores)** | LLM 1 億トークン 8 日間判定、raw 0-10 整数 (top1=10 普遍) | **持続 (top1_tied 100%)** | **持続 (s1-s6 std=0)** |
| **v1106a 案 Z-1 (normalized_scores)** | 同上、norm 0-1 連続 (top1≈0.9 で tied なし) | **持続** (相関構造そのもの存在せず) | **持続** (s1-s6 std=0、微差残存) |

→ **3 ソース (v1106 + v1106a X + v1106a Z-1) すべてで #L41/#L42 が持続** = データソース変更や接続式変更では解消しない、**Atom-word 関係そのものの構造的特性として確定**

### 3.2 Synapse 一般構造特性の含意

- atom 1 つには必ず最大 weight (Synapse v3 では 1.0、mapper_output raw では 10) を持つ word が存在する構造
- これは Synapse / mapper_output 生成プロセス (atom 1 つに「典型 word」が必ず存在する設計) の構造的帰結
- atom 間差別化を観察するには **最大値 weight でなく分布全体 (平均値、entropy 等)** を見る必要 = 観察方法を変更しないと差別化は見えない

### 3.3 s7 高 prob atom と word score の rank_correlation 無相関 (新発見)

| 指標 (案 Z-1) | 値 | 意味 |
|---|---:|---|
| rc_mean | -0.034 | ほぼゼロ |
| rc_positive_rate | 49.75% | ランダム (50% 期待値に近い) |
| rc >0.5 | 14.29% | 弱 |
| rc <-0.5 | 20.69% | やや負相関側に偏り |

→ **s7 で高確率の Atom と、mapper_output で高 weight を持つ word の間に rank 相関構造がない**

含意:
- s7 主軸の Atom 選択 (Genesis 側の認知過程) と Language 側 word の重要度は **独立** に動いている
- 「Genesis Atom の確率順位を Language word に投影する」型の接続が無相関 = v1106a 接続式 (案 X / 案 Z-1) は計算は通るが構造的に対応関係を持たない
- 接続式の見直しが v1107 以降の主題候補

---

## 4. mapper_output (新データ) vs v1106 Synapse v3 (古いデータ) 対比

### 4.1 カバレッジ対比

| 指標 | v1106 (Synapse v3) | v1106a (mapper_output) | 増減 |
|---|---:|---:|---|
| ファイル数 | 1 file (esde_synapses_v3.json) + 6 patches | 325 jsonl files | 別構造 |
| 接続単位 | synset (lemma.pos.sense) | word | 別単位 |
| 件数 | 11,581 synset | 17,790 unique word | +53% |
| atom mapping | v1103 325 ⊂ Synapse 326 (FND.spaceless 差分) | v1103 325 = mapper_output 325 完全一致 | 構造的解消 |

### 4.2 接続結果対比

| 指標 | v1106 | v1106a (案 X) | v1106a (案 Z-1) |
|---|---:|---:|---:|
| n_words/synsets mean (s1-s6) | 629 | **774** | 774 |
| n s7 | 298 | **348** | 348 |
| max_prob mean (s1-s6) | 0.008 | 0.011 | **0.014** |
| max_prob mean (s7) | 0.011 | 0.014 | **0.019** |
| entropy mean (s1-s6) | 5.92 | 6.03 | 5.94 |
| coverage max | 12% | 14% | 14% |
| expansion_ratio | 66/atom | **76/atom** | 76/atom |

→ v1106a は v1106 より約 17-23% 広い (Lexicon 17,790 unique > Synapse 11,581)、coverage 同程度

### 4.3 構造特性対比 (持続 vs 解消)

| 構造特性 | v1106 | v1106a | 結論 |
|---|---|---|---|
| s7 #L40 独立挙動 | n_synsets 約半分 | **n_words 約半分** | **持続** |
| #L41 atom 間差別化困難 | top1=1.0 普遍、rc 計算不能 | **両案で持続** | **持続** (構造特性) |
| #L42 s1-s6 平均化 | std=0 完全同値 | **3 ソースすべて std=0** | **持続** (構造特性) |
| couple_bonus 効果 | s1 vs s5 = 0.99 | 案 X 1.00 / 案 Z-1 0.99 | **ほぼなし** (構造的) |
| #L43 FND.spaceless 欠落 | Synapse only 1 件 | **mapper_output に最初から存在せず** | **構造的解消** |

---

## 5. bit-identity 3 層検証 (Step I)

### 5.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step C-H 再実行で hash 完全一致 | **9 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a-v1106 main outputs + Synapse v3 + mapper_output + a1_batch 全 frozen | **all PASS** (a/r/m すべて 0、2,180 files) |
| **C** | 全 7 scripts (Step B-H) の書込みパスが unified/v1106a/ 配下 | **all_under=True** (9 件) |

- LAYER_A_FILES (9): observation_1_word_distributions / observation_1_labels / observation_2_mapper_alignment / observation_3_expansion / observation_3_summary / observation_4_layer_jaccard / observation_4_series_comparison / observation_5_L41_resolution / observation_6_L42_resolution
- LAYER_A_RERUN 経過時間: Step C 53s / D 9.5s / E 0.5s / F 22s / G 0.4s / H 19s = 計 104s
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 + v1104 13 + v1104a 8 + v1105 4 + v1105a 7 + v1106 8 + language_synapse 19 + **language_mapper_output 325 + language_atoms_a1_batch 327** = **2,180 files 全 frozen 確認**
- 報告 JSON: `v1106a_step_i_bit_identity_report.json`

---

## 6. 規律遵守総括

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (mapper_output + Synapse v3 + a1_batch 全 frozen) |
| 絶対格言 #5 (観察軸を増やさない) | ✓ (観察 5/6 は #L41/#L42 対比、v1106 観察軸の継承) |
| 絶対格言 #6 (出口の固定) | ✓ (v1106a 進行条件 6 点を §1.4 で事前確定) |
| 絶対格言 #9 (神の手回避) | ✓ (接続式案 X 主軸 + 案 Z-1 補助、独自発明禁止) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (7 系列 × 2 案 別レイヤー、観察 1-6 別レイヤー) |
| 絶対格言 #12 (judgment 回避) | ✓ (構造ラベルのみ、success/failure 未使用、判定は Web Claude/Taka 領域) |
| データ取り違え防止規律 §0.7 (本主題で初適用) | ✓ (Step A 必須確認 5 件すべて実施、データ所在/timestamp/生成方法/Taka 過去評価/古い実装並存) |
| 全体図位置づけ規律 (§0.1) | ✓ (Atom → mapper_output → word の最小経路) |
| 妄想化回避規律 (§0.6) | ✓ (Operator/分子/ESDE らしさ/会話成立 を語らない) |
| mapper_output + Synapse v3 frozen | ✓ |
| 接続式独自発明禁止 | ✓ (案 X 主軸 + 案 Z-1 補助、案 Y 除外) |
| 7 系列・案 X/Z-1 統合禁止 | ✓ (別レイヤー保持) |
| v1106 結果との対比を「正しい/間違い」で判定しない | ✓ (両者構造事実、Taka「うっかりミスは仕方ない」継承) |
| mapper_output 自体の品質判定しない | ✓ (Language 側評価は別主題) |
| 48 axes 意味解釈を v1107 以降に保留 | ✓ (axis = Operator 領域に近い、妄想化回避) |
| Atom 抽出確認結果反映 | ✓ (cid 揺れ解析は v1107 以降の主題候補と明示) |
| 書込みパス unified/v1106a/ 配下 | ✓ |
| smoke 含めず | ✓ |

---

## 7. 新規留保候補 3 件 (Code A 報告、Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L44** | #L41 (atom 間差別化困難) と #L42 (s1-s6 平均化) は **Synapse データ全般の特性でなく、Atom-word 関係そのものの構造的特性として確定**。v1106 Synapse v3 (sentence-BERT) と v1106a mapper_output (LLM 1 億トークン 8 日間判定) の **3 ソースすべて (Synapse v3 + 案 X + 案 Z-1) で持続**、データソース変更や接続式変更では解消しない構造的限界 |
| **#L45** | s7 高確率 Atom と word score の **rank_correlation 無相関** (案 Z-1 で rc_mean -0.034 / positive_rate 49.75% ランダム)、Genesis Atom の確率分布と Language word の重要度は独立に動く構造、現状の接続式 (案 X / 案 Z-1) は計算は通るが構造的対応関係を持たない = 接続式の構造的見直しが v1107 以降の主題候補 |
| **#L46** | couple_bonus 1.1 効果が **案 X (raw_scores_max) で完全消失** (s1 vs s5 = 1.000 全 3,300 events 完全一致)、案 Z-1 (normalized_scores_max) で 0.99 (97% 完全一致、3% 微差)、raw_scores_max ベースでは const_adjusted の効果が score 計算後に構造的にゼロ、normalized_scores では微小な痕跡のみ |

既存留保継承: #L17/#L21'/#L22'/#L24-29/#L30-L36/#L37-L40/#L41-L43 + 48 次元人為性留保 (v1103 GPT 監査 5)

---

## 8. 設計書 §1.4 進行条件分岐への対応

設計書 §1.4 で事前確定した進行判定:

| 結果 | v1106a 構造事実との対応 | 進行方向 |
|---|---|---|
| 4 + 5/6 解消 | **該当せず** (5/6 両方とも持続) | v1106b 進行 |
| **4 + 5/6 部分解消** | **該当** (5/6 両方とも持続方向で「部分解消」より深刻、ただし 4 条件は構造的成立) | **v1107 (Atom 単体限界対応) 先検討** |
| 4 未成立 | 該当せず (4 条件すべて成立) | v1106c 接続式再設計 |

→ 構造事実は **v1107 (Atom 単体限界対応) を先検討** 方向。判定は Web Claude/Taka 領域。

ただし「部分解消」より深刻 (両方とも解消しない = Atom-word 関係の構造特性、#L44) なので、v1106c (接続式再設計) でも改善しない可能性が #L44/#L45 で示唆される。v1107 (Operator/分子レイヤー対応、cid 揺れ解析等) で初めて改善する可能性がある。

---

## 9. 出力ファイル総覧 (`unified/v1106a/`)

| ファイル | サイズ |
|---|---:|
| v1106a_phase_design.md | 設計書 v3 |
| v1106a_step_a_recognition.md | 認識確認 + 確認要請 11 |
| v1106a_step_a_answer.md | Web Claude 回答 |
| v1106a_step_b-h スクリプト | 7 ファイル |
| v1106a_step_i_bit_identity.py + report | — |
| v1106a_step_j_observation_final.md | 本書 |
| outputs/main/observation_1_word_distributions.parquet | 32,943,000 rows |
| outputs/main/observation_1_labels.parquet | 46,200 rows |
| outputs/main/observation_2_mapper_alignment.parquet | 46,200 rows |
| outputs/main/observation_3_expansion.parquet | 46,200 rows |
| outputs/main/observation_3_summary.parquet | 14 rows |
| outputs/main/observation_4_layer_jaccard.parquet | 98 rows (2×7×7) |
| outputs/main/observation_4_series_comparison.parquet | 14 rows |
| outputs/main/observation_5_L41_resolution.parquet | 14 rows |
| outputs/main/observation_6_L42_resolution.parquet | 3 rows |

物理層 (v105/v106/v107/v112/v1101a-v1106 + language/synapse 19 + mapper_output 325 + a1_batch 327 = **2,180 files**) frozen 維持。

---

## 10. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (v1106a 6 観察) の提示完了。以下は Web Claude + Taka 領域:

1. **v1106a 進行条件 6 点判定**: 構造事実は 4 条件成立 + 5/6 両方持続、「v1107 先検討」方向だが #L44 で「v1106c でも改善しない可能性」も示唆 (§2.7 / §8)
2. **v1106b 着手 vs v1107 vs v1106c 判断**: 4 条件 + 持続 5/6 + 新規留保 #L44-L46 を踏まえた最終判定
3. **v1106 + v1106a 統合 Phase Result**: Synapse v3 vs mapper_output 対比 + #L41/#L42 構造特性確定の集約
4. **#L44-L46 新規留保**: Atom-word 関係の構造特性 / s7 と word score 無相関 / couple_bonus 消失
5. **v1107 着手の場合の次主題**: Operator/分子レイヤー対応 / cid 揺れ解析 / 接続式構造的見直し

---

## 11. 一文サマリ (再掲)

Step A-I 全完了、Step A (確認要請 11 案 Z-1 採用 + Atom 抽出確認 7 件) → Step B (環境準備 LAYER_B 2,180 files) → Step C (Atom → word 変換 案 X + 案 Z-1 並列 32.9M rows / 46,200 全 word_distribution_valid 100%) → Step D (top1_score X=10/Z1=0.89-0.92、rc X=NaN / Z1=-0.034 無相関) → Step E (候補爆発 s7 coverage 8.15% 観察可能) → Step F (s1-s6 完全同値、s1 vs s5 X=1.00/Z1=0.99 couple_bonus ほぼなし、s7 独立 #L40 持続) → Step G (#L41 解消確認 = 持続方向、案 X 完全同型・案 Z-1 無相関) → Step H (#L42 解消確認 = 持続方向、3 ソース s1-s6 std=0 完全同値) → Step I (bit-identity 3 層全 PASS LAYER_A 9 hash 一致 105s / LAYER_B 2,180 frozen / LAYER_C 9 件 unified/v1106a/ 配下)、**v1106a 進行条件 6 点**: 4 条件成立 + 5/6 両方持続 = v1107 (Atom 単体限界対応) 先検討方向の構造事実、**#L41/#L42 は Synapse v3 固有でなく Atom-word 関係そのものの構造的特性として確定** (3 ソースすべて持続、データソース変更で解消しない構造限界)、新規留保候補 #L44 (構造特性確定) / #L45 (s7 と word score 無相関) / #L46 (couple_bonus 案 X 完全消失) 提示、既存留保 #L17/#L21'/#L22'/#L24-29/#L30-L36/#L37-L40/#L41-L43 + 48 次元人為性継承、v1106b vs v1107 vs v1106c 判定 + Phase Result 統合 + #L44-L46 解釈統合は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + データ取り違え防止規律初適用 + 全体図位置づけ + 妄想化回避 + mapper_output/Synapse v3/a1_batch frozen + 接続式独自発明禁止 + 7 系列・案 X/Z-1 統合禁止 + v1106 結果との対比を「正しい/間違い」で判定しない + mapper_output 品質判定なし + 48 axes 意味解釈 v1107 以降) を全 Step で堅持、書込み unified/v1106a/ 配下のみ。
