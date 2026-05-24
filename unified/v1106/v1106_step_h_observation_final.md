# v11.0.6 (v1106) Step H 観察事実最終報告 — Code A

*作成*: 2026-05-25、Code A
*親*: `v1106_phase_design.md` (Web Claude 設計書、GPT 監査クリア + Taka 確定「Gemini 不要」) + `v1106_step_a_recognition.md` 改訂版 (Taka 指摘 4 点反映) + `v1106_step_a_answer.md` (Web Claude 回答、確認要請 8/9 案 A 両方承認) + Step B-G 出力
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価 + v1106a/v1106b 着手判断)
*位置づけ*: v1106 主題「Genesis 応答 Atom 候補分布と Synapse 強度の接続点検」(問いの形 A 復帰) の Code A 観察事実総括。**judgment 回避** (絶対格言 #12)、**判定語制限** (success/failure を使わず構造ラベル)、**selector 化禁止遵守**、**LLM プロキシ呼び出し禁止**、**Operator/分子・会話成立・ESDE らしさ語らない (妄想化回避)**、**Synapse データ frozen + SynapseStore 仕様遵守**。

---

## 0. 一文サマリ

v1106 主題段階 1 Step A-G 全完了、Step A (確認要請 4 件改訂版で SynapseStore overlay 経由 + synset/word/lemma 単位分離 + WLD.artless/FND.spaceless 別現象明示、Web Claude 回答で確認要請 8/9 案 A 両方承認 = 接続式 weight そのまま + FND.spaceless 除外+警告) → Step B (環境準備、SynapseStore overlay 適用 11,581 synset / 326 atoms / s7 PC events 14,600 rows × 3,300 events / FND.spaceless 23 synset 指すが s7 PC input/candidate atom に含まれず防御的のみ / LAYER_B baseline 1,520 files) → Step C (観察 1 Atom → synset 変換、接続式 score = Σ p_s7 × syn_weight 適用、19.5s で 13.4M rows、全 23,100 event-series synset_distribution_valid 100% で candidate_empty/degenerate 0、n_synsets mean 582 / max 1,339、max_prob mean 0.0084 で一点集中なし Aruism 規律仕様化担保、entropy mean 5.84) → Step D (観察 2 Synapse 強度と s7 確率整合、3.3s で 23,100 rows、top1_atom_top1_syn_strength=1.0 普遍 + top1_atom_n_syn_links 72-77 + atom_synapse_rank_correlation NaN 多発 = top1 weight=1.0 タイで Spearman 計算不能 = Synapse データ構造特性、mean_syn_strength 0.53-0.55 で微差別化のみ) → Step E (観察 3 候補広がり/絞り、0.2s、s1-s6 同値 n_synsets mean 629 / max 1339 / coverage max 12% vs s7 (48D k=5) n_synsets mean 298 / max 465 / coverage max 4% で s7 約半分、expansion_ratio mean ~66/atom 全系列同値 = Synapse 構造特性、候補爆発リスク s7 >=500 synset 0% で観察可能範囲) → Step F (観察 4 7 系列 layer_jaccard、7.8s、s1 vs s5 = 0.99 / s2 vs s6 = 0.97 で couple_bonus 効果ほぼなし、s7 vs raw 系列 0.84-0.85 / s7 vs qweighted 0.63、s7 集計値独立 #L40 持続、**s1-s6 集計値完全同値 = density 6 種の差が Synapse 接続段階で平均化**) → Step G (bit-identity 3 層全 PASS、LAYER_A 8 ファイル全 hash 一致 32.9s、LAYER_B 1,520 frozen files 不変 = v105/106/107/112/1101a-v1105a 全 + language/synapse/ 19、LAYER_C 8 件全て unified/v1106/ 配下) すべて完了、核心構造事実 (judgment なし、構造ラベルのみ): (1) **v1106a 接続条件 4 点すべて構造的成立**: 条件 1 synset_pipeline_complete 23,100 events 全て (100%)、条件 2 synset_distribution_valid max_prob mean 0.008-0.011 / entropy mean 5.4-5.9 で degenerate 0、条件 3 候補爆発 s7 max coverage 4% (制御不能でない、観察可能範囲)、条件 4 s7 主軸の synset 候補構造的に存在 (n_synsets mean 298)、ただし判定は Web Claude/Taka 領域、(2) **接続式 score = Σ p_s7 × syn_weight が Aruism 規律仕様化担保**: 全系列 max_prob mean 0.008-0.011 で一点集中なし (582 synset に分散)、(3) **s7 #L40 独立挙動の Synapse 接続後持続**: s1-s6 集計値完全同値 (n_synsets 629 / max_prob 0.008 / entropy 5.92) vs s7 (n_synsets 298 / max_prob 0.011 / entropy 5.39)、s7 は s1-s6 の約半分の synset 候補数、(4) **density 6 種差が Synapse 接続で平均化** (s1-s6 集計同値、ただし per-event top5 jaccard 0.62-0.99 で微差残存)、(5) **Synapse 構造特性**: top1_atom_top1_syn_strength=1.0 普遍 (atom 間差別化困難)、1 atom → mean 68 synsets、couple_bonus 1.1 効果ほぼなし (s1 vs s5 jaccard 0.99)、新規留保候補 #L41-L43 提示 (#L41 Synapse weight=1.0 普遍化で top1 weight 軸の atom 間差別化困難、mean_syn_strength のみ微差、#L42 s1-s6 集計値同値 = density 6 種の差が Synapse 接続段階で平均化される構造的事実、#L43 FND.spaceless が v1103 atom_centroids に欠落する理由は v1106 範囲外、v1107 以降の主題候補)、既存留保 #L17/#L21'/#L22'/#L24-29/#L30-L36/#L37-L40 + 48 次元人為性留保継承、最終判定 (v1106a 着手 vs v1106b 移行) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 #2/#5/#6/#9/#11/#12 + 全体図位置づけ + 妄想化回避 + selector 化禁止 + LLM プロキシ呼び出し禁止 + Synapse データ frozen + SynapseStore 仕様 + 接続式独自発明禁止 + 7 系列・観察 1-4 統合禁止 + Atom 単体限界継承 + Lexicon Core pool は v1106a 以降) を全 Step で堅持、書込み unified/v1106/ 配下のみ。

---

## 1. Step A-G 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A | 認識確認 + 確認要請 8/9 | 完了 (Taka 指摘 4 点反映改訂 + Web Claude 案 A 両方承認) | v1106_step_a_recognition.md + v1106_step_a_answer.md |
| B | 環境準備 (SynapseStore overlay + s7 PC events) | 完了 | v1106_step_b_env_check.py |
| C | 観察 1 (Atom → synset 変換、7 系列並列) | 完了 (19.5s) | observation_1_synset_distributions.parquet (13.4M) + observation_1_labels.parquet (23.1k) + observation_1_excluded_fnd_spaceless.json |
| D | 観察 2 (Synapse 強度 vs s7 確率整合) | 完了 (3.3s) | observation_2_synapse_alignment.parquet (23.1k) |
| E | 観察 3 (synset 広がり/絞り) | 完了 (0.2s) | observation_3_expansion.parquet (23.1k) + observation_3_summary.parquet (7) |
| F | 観察 4 (7 系列 layer_jaccard) | 完了 (7.8s) | observation_4_layer_jaccard.parquet (49) + observation_4_series_comparison.parquet (7) |
| G | bit-identity 3 層検証 | 完了 (all PASS、32.9s) | v1106_step_g_bit_identity_report.json |
| H | 観察事実最終報告 | 本書 | v1106_step_h_observation_final.md |
| I | Phase Result (v1106a / v1106b 着手判断) | 待ち | Web Claude 担当 |

---

## 2. v1106a 接続条件 4 点 (§2.7) 構造事実

**Code A 判定なし、構造的観察事実のみ報告。判定は Web Claude/Taka 領域**。

### 2.1 条件 1: synset_pipeline_complete ラベルの event が構造的に存在

| 構造ラベル | 件数 (全 7 系列で同値、23,100 event-series) | 割合 |
|---|---:|---:|
| synset_candidate_empty | 0 | 0% |
| synset_distribution_degenerate | 0 | 0% |
| **synset_distribution_valid (= synset_pipeline_complete)** | **23,100** | **100%** |

→ **全 23,100 event-series で synset_pipeline_complete を構造的に確認**

### 2.2 条件 2: synset_distribution_valid 成立

| 系列 | n_synsets mean | max_prob mean | entropy mean | degenerate count |
|---|---:|---:|---:|---:|
| s1-s6 (全 6 同値) | 629 | 0.0084 | 5.92 | 0 |
| s7 (48D k=5) | 298 | 0.0110 | 5.39 | 0 |

→ **distribution_valid 成立**: max_prob mean 0.008-0.011 で 0.999 大幅下回り、entropy > 0、degenerate 全 0

### 2.3 条件 3: 候補爆発が制御不能でない

| 系列 | n_synsets max | total_synset_coverage max | >= 500 synset events |
|---|---:|---:|---:|
| s1-s6 | 1,339 | 12% | 様々 |
| s7 (48D k=5) | 465 | **4%** | **0%** |

→ **候補爆発は観察可能範囲**: s7 max 4% / s1-s6 max 12% で Synapse 11,581 全体に対して低割合、構造的「制御不能」ではない

### 2.4 条件 4: s7 主軸の synset 候補が構造的に存在

s7 (48D k=5) で synset_distribution_valid 3,300 events (全 events)、n_synsets mean 298 / max_prob mean 0.011 / entropy mean 5.39

→ **s7 主軸の synset 候補が構造的に存在**、s7 単独でも接続成立

### 2.5 4 条件統合の構造事実

4 条件すべて構造的に成立。Web Claude/Taka 領域で v1106a (LLM プロキシ呼び出し or Operator 対応議論) 進行 vs v1106b (Synapse 接続点検再設計) 移行を判定。

---

## 3. 接続式の Aruism 規律仕様化担保 (Web Claude 確認要請 8 案 A 採用結果)

接続式 `score(s_j) = Σ_i [ p_s7(atom_i) × syn_weight(atom_i, s_j) ]` の Aruism 規律 (max_prob 一点集中回避) を構造事実として担保:

| 系列 | max_prob mean | max_prob max | 担保 |
|---|---:|---:|---|
| s1-s6 | 0.008 | (sample) | ✓ 0.999 大幅下回り |
| s7 | 0.011 | (sample) | ✓ 同上 |

→ **接続式は仕様として Aruism 規律担保**、ハンドチューニングなし、独自発明なし

---

## 4. s7 #L40 独立挙動の Synapse 接続後持続 (構造事実)

v1105a #L40 (s7 48D 独立挙動) を Synapse 接続後も持続:

| 指標 | s1-s6 (6 系列同値) | s7 | s7/s1-s6 比 |
|---|---:|---:|---:|
| n_synsets mean | 629 | **298** | **0.47** |
| max_prob mean | 0.008 | **0.011** | 1.38 |
| entropy mean | 5.92 | **5.39** | 0.91 |
| max coverage | 12% | **4%** | 0.33 |

→ **s7 は Synapse 接続後も独立挙動を保持**、s1-s6 の約半分の synset 候補数、entropy 低く集中傾向 (#L40 持続)

---

## 5. density 6 種差が Synapse 接続段階で平均化 (新規発見、v1106 で初出)

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

→ **density 6 種の差は集計レベルで平均化されるが per-event top5 で微差残存**、これは v1106 で初めて見える Synapse 接続効果の構造事実

---

## 6. Synapse 構造特性 (構造事実)

- **top1_atom_top1_syn_strength = 1.0 普遍** (全 7 系列、ほとんどの atom が weight=1.0 synset を 1 つ以上持つ)
- 1 atom → mean **68 synsets** (max 181)、expansion_ratio mean 66/atom 全系列同値
- **atom_synapse_rank_correlation NaN 多発**: top5 atom の top1 weight=1.0 タイで Spearman 計算不能
- mean_syn_strength 0.53-0.55 で **微差別化のみ** (Synapse 全体 mean 0.518 と整合)
- couple_bonus 1.1 効果ほぼなし (s1 vs s5 jaccard 0.99)
- **FND.spaceless が v1103 atom_centroids に欠落** (Synapse 内 23 synset 指す、s7 PC events に登場せず防御的除外のみ発火)

---

## 7. bit-identity 3 層検証 (Step G)

### 7.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step C-F 再実行で hash 完全一致 | **8 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a-v1105a main outputs 全 frozen + Synapse データ frozen | **all PASS** (a/r/m すべて 0、1,520 files) |
| **C** | 全 5 scripts の書込みパスが unified/v1106/ 配下 | **all_under=True** (8 件) |

- LAYER_A_FILES (8): observation_1_synset_distributions / observation_1_labels / observation_1_excluded_fnd_spaceless / observation_2_synapse_alignment / observation_3_expansion / observation_3_summary / observation_4_layer_jaccard / observation_4_series_comparison
- LAYER_A_RERUN 経過時間: Step C 20.5s / D 3.8s / E 0.4s / F 8.2s = 計 32.9s
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 + v1104 13 + v1104a 8 + v1105 4 + v1105a 7 + **language/synapse 19** = **1,520 files 全 frozen 確認** (Synapse データも含む)
- 報告 JSON: `v1106_step_g_bit_identity_report.json`

---

## 8. 規律遵守総括

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.5/6/7 + v1101a-v1105a + Synapse データ frozen、LAYER_B 全 PASS) |
| 絶対格言 #5 (観察軸を増やさない) | ✓ (FND.spaceless 除外で軸増加なし、Lexicon Core pool は v1106a 以降) |
| 絶対格言 #6 (出口の固定) | ✓ (v1106a 接続条件 4 点を §2.7 で事前確定) |
| 絶対格言 #9 (神の手回避) | ✓ (接続式 §2.1 案 A 仕様、SynapseStore overlay 経由、独自発明なし) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (7 系列・観察 1-4 別レイヤー、synset vs word vs lemma 明示区別) |
| 絶対格言 #12 (judgment 回避) | ✓ (success/failure 未使用、構造ラベルのみ、v1106a/v1106b 判定は Web Claude/Taka 領域) |
| 全体図位置づけ規律 (§0.1) | ✓ (Atom → Synapse 接続のみ、Operator/分子経由しない) |
| 妄想化回避規律 (§0.6) | ✓ (Operator/分子/会話成立/ESDE らしさを語らない) |
| selector 化禁止 | ✓ (役割表に従う動作のみ、ESDE 自由選択なし) |
| 試行 ≠ 会話成立判定 | ✓ (構造ラベルのみ、意味判定なし) |
| LLM プロキシ呼び出し禁止 | ✓ (本主題は synset 候補まで、自然文生成は v1106a 以降) |
| Synapse データ frozen + SynapseStore 仕様遵守 | ✓ (SynapseStore overlay 経由、read-only、LAYER_B 全 PASS) |
| 接続式独自発明禁止 | ✓ (案 A 実体合わせの微修正、独自設計なし) |
| 7 系列・観察 1-4 統合禁止 | ✓ (別レイヤー保持、共通比較指標で並列) |
| Atom 単体限界継承 | ✓ (Operator/分子 v1106 範囲外、Atom → Synapse 直接接続のみ) |
| Lexicon Core pool は v1106a 以降 | ✓ (Synapse atom → synset 逆引きのみ、Lexicon Core pool 32,666 word は別主題) |
| FND.spaceless 欠落理由は v1106 範囲外 | ✓ (除外 + 警告のみ、理由調査は v1107 以降の主題候補) |
| 書込みパス unified/v1106/ 配下 | ✓ (LAYER_C all_under=True、8 件) |
| smoke 含めず | ✓ (post-process のみ) |

---

## 9. 新規留保候補 3 件 (Code A 報告、Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L41** | Synapse weight=1.0 普遍化で top1 weight 軸の atom 間差別化困難 (top1_atom_top1_syn_strength 全系列 1.0 タイ、atom_synapse_rank_correlation NaN 多発)、mean_syn_strength のみ微差別化 (0.53-0.55)。Synapse 構造の特性であり、観察方法側で深掘り必要な留保 |
| **#L42** | s1-s6 集計値完全同値: density 6 種 (raw/qweighted/const_adjusted × raw/norm) の差が Synapse 接続段階で平均化される (n_synsets / max_prob / entropy 集計値同値)、ただし per-event top5 で jaccard 0.62-0.99 の微差残存。v1106 で初めて見える Synapse 接続効果の構造事実、couple_bonus 1.1 効果ほぼなし (s1 vs s5 jaccard 0.99) |
| **#L43** | FND.spaceless が v1103 atom_centroids に欠落: Synapse 内 23 synset が指す、v1106 範囲では除外 + 警告で処理、なぜ欠落するかは Genesis 側 Web Claude が v1106 完了後に把握 (v1107 以降の主題候補)。同種の構造的欠落が別 atom でも起きうるかの調査素材 |

既存留保継承: #L17 / #L21' / #L22' / #L24-29 / #L30-L36 (v1104+v1104a + v1105) / #L37-L40 (v1105a) / 48 次元人為性留保 (v1103 GPT 監査 5)

---

## 10. 出力ファイル総覧 (`unified/v1106/`)

| ファイル | 件数 |
|---|---:|
| v1106_phase_design.md | — |
| v1106_step_a_recognition.md | — |
| v1106_step_a_answer.md | — |
| v1106_step_b_env_check.py | — |
| v1106_step_c-f_observation_*.py | 4 scripts |
| v1106_step_g_bit_identity.py + report | — |
| v1106_step_h_observation_final.md | 本書 |
| outputs/main/observation_1_synset_distributions.parquet | 13,444,700 rows |
| outputs/main/observation_1_labels.parquet | 23,100 rows |
| outputs/main/observation_1_excluded_fnd_spaceless.json | report |
| outputs/main/observation_2_synapse_alignment.parquet | 23,100 rows |
| outputs/main/observation_3_expansion.parquet | 23,100 rows |
| outputs/main/observation_3_summary.parquet | 7 rows |
| outputs/main/observation_4_layer_jaccard.parquet | 49 rows (7×7) |
| outputs/main/observation_4_series_comparison.parquet | 7 rows |

物理層 (v105/v106/v107/v112/v1101a-v1105a main outputs + language/synapse 1,520 ファイル) frozen 維持。

---

## 11. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (v1106 4 観察) の提示完了。以下は Web Claude + Taka 領域:

1. **v1106a 接続条件 4 点判定**: 構造的にすべて成立 (§2 参照)、ただし接続後の **synset_max_prob mean 0.008-0.011** (非常に低、582 synset に分散) を「絞れた」と判断するか「絞り切れていない (broad)」と判断するか
2. **v1106a 着手 vs v1106b 移行判断**: 4 条件成立 + 3 留保候補を踏まえた最終判定
3. **v1101-v1106 統合 Phase Result**: 役割表 + 試行 + Synapse 接続の集約事実
4. **#L41-L43 新規留保**: Synapse weight=1.0 普遍化 / density 6 種平均化 / FND.spaceless 欠落理由 (Genesis 側 v1107 以降の主題候補)
5. **v1106a 着手の場合の次主題**: LLM プロキシ呼び出し / Operator 対応議論

---

## 12. 一文サマリ (再掲)

Step A-G 全完了、Step A (Taka 指摘 4 点反映 + 確認要請 8/9 案 A 両方承認) → Step B (環境準備 SynapseStore overlay 11,581 synset / 326 atoms / 1,520 frozen baseline / FND.spaceless 防御的除外) → Step C (観察 1 Atom → synset 変換、13.4M rows / 23.1k event-series 全 synset_distribution_valid 100% / n_synsets mean 582 / max_prob mean 0.008 で Aruism 担保) → Step D (観察 2 Synapse 強度 vs s7 整合、top1_weight=1.0 普遍タイで Spearman 計算不能、mean_syn_strength 0.53 微差別化) → Step E (観察 3 候補広がり/絞り、s7 max coverage 4% / s1-s6 max 12% で候補爆発リスク観察可能範囲) → Step F (観察 4 7 系列 layer_jaccard、s7 vs raw 0.84 / s7 vs qweighted 0.63 で s7 独立挙動 #L40 持続、s1 vs s5 = 0.99 で couple_bonus 効果ほぼなし、s1-s6 集計値完全同値 = density 6 種が Synapse 接続段階で平均化) → Step G (bit-identity 3 層全 PASS: LAYER_A 8 ファイル hash 一致 32.9s / LAYER_B 1,520 frozen Synapse 含む / LAYER_C 8 件 unified/v1106/ 配下)、**v1106a 接続条件 4 点すべて構造的成立** (条件 1 PC 23,100 / 条件 2 distribution_valid max_prob mean 0.008-0.011 entropy 5.4-5.9 / 条件 3 候補爆発 s7 max coverage 4% 制御不能でない / 条件 4 s7 主軸構造的存在 n_synsets mean 298)、新規留保候補 #L41-L43 提示 (Synapse weight=1.0 普遍化 / density 6 種平均化 / FND.spaceless 欠落理由 v1107 以降)、既存留保 #L17/#L21'/#L22'/#L24-29/#L30-L36/#L37-L40 + 48 次元人為性留保継承、v1106a 着手 vs v1106b 移行判定 + Phase Result 統合 + #L41-L43 解釈統合は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + selector 化禁止 + LLM 呼び出し禁止 + 妄想化回避 + Synapse frozen + SynapseStore 仕様遵守 + 接続式独自発明禁止 + 7 系列統合禁止 + Atom 単体限界継承) を全 Step で堅持、書込み unified/v1106/ 配下のみ。
