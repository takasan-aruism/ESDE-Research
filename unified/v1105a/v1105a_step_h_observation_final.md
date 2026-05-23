# v11.0.5a (v1105a) Step H 観察事実最終報告 — Code A

*作成*: 2026-05-24、Code A
*親*: `v1105a_phase_design.md` v3 (Web Claude 設計書、2 AI 監査 + Code A Step A 確認要請 4 件クリア済) + `v1105a_step_a_recognition.md` + `v1105a_step_a_answer.md` + Step B-G 出力
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価 + v1106/v1105b 着手判断)
*位置づけ*: v1105a 主題「役割表を使って実際に応答候補を絞る試行」(問いの形 B、v1101 以来初の切替) の Code A 観察事実総括。**judgment 回避** (絶対格言 #12)、**判定語制限** (success/failure を使わず構造ラベル、GPT 追加 4)、**selector 化禁止遵守**、**0 を 1 にはできない歯止め遵守**、**試行 ≠ 会話成立判定 / 試行 ≠ ハンドチューニング**、**構造ラベルのみで判定回避**。

---

## 0. 一文サマリ

v1105a 主題 (v1101 以来初の問いの形 B) Step A-G 全完了、Step A (確認要請 4 件 Taka 判断「ラッキー判定の余地なし、本番前に気づけたのはラッキー、忘れ物を取りに戻っても遅刻しないなら戻るべき」歌手の音痴比喩で全面修正反映: v108_standard 60,000 events / 動的計算 100% カバレッジ / per-atom rank 3 軸 / max_prob 0.999 閾値) → Step B (環境準備: v108_standard 60,000 確認 / per-atom stability + cosine_sim 計算源確認 / atom_id ↔ candidate_id mapping 確立 / LAYER_B 1,494 files) → Step C (試行 Step 1+2 入力投入 + 4 source レイヤー連想、38,700 rows 出力 4.5s、Genesis alpha 20,500 / Genesis beta 17,000 / Language alpha 500 / Language beta 700、bin_5_plus で Genesis 候補数最大、Language は couple endpoints 12 制限で少ない) → Step D (試行 Step 3 rank-based 絞り 7 系列 per-atom、206,900 rows 出力 11s、3 軸 per-atom rank + 緩やか減衰 1/log(rank+2)、全系列 max_prob mean 0.27-0.36 で Aruism 規律内、s7 48D k=5 で max_prob mean 0.36 + entropy mean 1.39 で集中傾向、B 高 atom top5 到達 1.2-1.9%) → Step E (試行 Step 4 構造ラベル付与、420,000 rows 出力 13s、全 60,000 events × 7 系列 = candidate_empty 55,200 (92%) / distribution_degenerate 1,500 (2.5%) / **distribution_valid = pipeline_complete 3,300 (5.5%)**、bin_2 valid_rate 5.67% > bin_5_plus 4.59% で #L35 試行内動的反映、7 系列で構造ラベル分布が同値 = density 種類非依存) → Step F (観察項目集計、共通比較指標 + layer_jaccard 7×7 + 4 source レイヤー overlap、s7 reduction_ratio 0.345 で k=5 制限が絞り効果、Genesis vs Language alpha scope jaccard 0.561 (Language ⊂ Genesis) / beta scope jaccard 0.247 (Language 独立傾向) で #L34 試行内動的観察) → Step G (bit-identity 3 層全 PASS: LAYER_A 7 ファイル全 hash 一致 32s、LAYER_B 1,494 frozen files 不変 v1105 まで含む、LAYER_C 7 件全て unified/v1105a/ 配下) すべて完了、核心構造事実 (judgment なし、構造ラベルのみ): (1) **v1106 接続条件 3 点 (§2.7) すべて構造的成立** - 条件 1 pipeline_complete 3,300 events 存在、条件 2 distribution_valid 成立 (max_prob mean 0.27、prob_ge_0.999 限定的 2.5%)、条件 3 reduction_ratio 観察 (緩やか減衰で候補絞り、s7 で 34.5% 削減) - ただし判定は Web Claude/Taka 領域、(2) **rank-based 絞り式の Aruism 規律担保**: 全系列 max_prob mean 0.27-0.36 で Gemini「首位 0.3 程度」予想内、緩やか減衰の仕様としての機能を構造事実として確認、(3) **#L34 試行内動的観察**: alpha scope Genesis vs Language jaccard 0.561 (Language ⊂ Genesis)、beta scope 0.247 (Language 独立)、scope 別 Genesis/Language 関係の試行内反映、(4) **#L35 試行内動的観察**: bin_2 valid_rate 5.67% > bin_3_4 3.93% / bin_5_plus 4.59% で CID_n=2 の試行内特殊性確認、(5) **#L36 試行内動的観察**: 7 系列で layer_jaccard 高 (s1 vs s5 が 0.97、s2 vs s6 が 0.99、ただし s7 48D k=5 のみ他系列と 0.65-0.73)、sim_basis × density 種類は試行内で類似挙動 (#L36 観察 3 vs 試行 で挙動異なる)、新規留保候補 #L37-L40 提示 (#L37 candidate_empty 92% は入力 atom が alpha/beta scope chain 登場有無で構造的に決まる試行特性、#L38 7 系列 valid_rate 同値で density 種類が構造ラベルに影響しない試行特性、#L39 Genesis ⊃ Language alpha vs Genesis ⊥ Language beta の試行内対比、#L40 s7 48D k=5 のみ集中傾向 + 他系列と独立挙動)、既存留保 #L17/#L21'/#L22'/#L24-29/#L30-L36 + 48 次元人為性留保継承、最終判定 (v1106 着手 vs v1105b 移行) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 #2/#6/#9/#11/#12 + selector 化禁止 + ハンドチューニング禁止 + 構造ラベル + 試行 ≠ 会話成立判定 + B emit read-only + 7 系列・6 値統合禁止 + 物理層 frozen + 0 を 1 にはできない歯止め) を全 Step で堅持、書込み unified/v1105a/ 配下のみ。

---

## 1. Step A-G 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A | 認識確認 + 確認要請 4 件 | 完了 (Taka 判断「歌手の音痴比喩」で v108_standard 60,000 / 動的計算 100% / per-atom rank / max_prob 0.999 全面反映) | v1105a_step_a_recognition.md + v1105a_step_a_answer.md |
| B | 環境準備 | 完了 | v1105a_step_b_env_check.py (新規出力なし、サマリのみ) |
| C | 試行 Step 1+2 (入力投入 + 4 source レイヤー連想) | 完了 (4.5s) | trial_step2_associations.parquet (38,700 rows) |
| D | 試行 Step 3 (rank-based 絞り 7 系列 per-atom) | 完了 (11s) | trial_step3_distributions.parquet (206,900 rows) |
| E | 試行 Step 4 (段 4-d 機構 + 構造ラベル付与) | 完了 (13s) | trial_step4_labels.parquet (420,000 rows) + trial_step4_distributions.parquet (206,900 rows) |
| F | 観察項目集計 | 完了 (3s) | trial_summary_metrics + trial_layer_jaccard + trial_source_layer_overlap |
| G | bit-identity 3 層検証 | 完了 (all PASS、32s) | v1105a_step_g_bit_identity_report.json |
| H | 観察事実最終報告 | 本書 | v1105a_step_h_observation_final.md |
| I | Phase Result (v1106 / v1105b 着手判断) | 待ち | Web Claude 担当 |

---

## 2. v1106 接続条件 3 点 (§2.7) 構造事実

**Code A 判定なし、構造的観察事実のみ報告。判定は Web Claude/Taka 領域**。

### 2.1 条件 1: pipeline_complete ラベルの event が構造的に存在

| ラベル | 件数 (全 60,000 events × 7 系列) | 割合 |
|---|---:|---:|
| candidate_empty | 55,200 | **92.0%** |
| distribution_degenerate | 1,500 | 2.5% |
| **distribution_valid (= pipeline_complete)** | **3,300** | **5.5%** |

→ **3,300 events で pipeline_complete を構造的に確認** (全 7 系列で同値)

### 2.2 条件 2: distribution_valid 成立 (max_prob<0.999, entropy>0, prob_ge_count 過剰でない)

| series_id | max_prob mean | entropy mean | prob_ge_0.999 count |
|---|---:|---:|---:|
| s1-s6 (raw/qweighted/const_adj × raw/norm) | 0.27 | 1.91 | 1,500 (2.5%) |
| s7 48D k=5 | 0.36 | 1.39 | 1,500 (2.5%) |

→ **distribution_valid 成立**: max_prob mean 0.27-0.36 で 0.999 大幅下回り、entropy > 0、degenerate 2.5% 限定的

### 2.3 条件 3: reduction_ratio 観察 (候補数が構造的に減る)

| series_id | reduction_ratio mean | median |
|---|---:|---:|
| s1-s6 | 0.002 | 約 0 |
| s7 48D k=5 | **0.345** | — |

→ **s7 48D k=5 で 34.5% 削減**、他系列は候補そのまま (rank で重みづけのみ、削除なし)、絞り効果は s7 のみ顕著

### 2.4 3 条件統合の構造事実

3 条件すべて構造的に成立。pipeline_complete 5.5% は限定的だが構造的存在、Aruism 規律遵守 (max_prob mean 0.27-0.36)、s7 のみ k=5 で実質削減。Web Claude/Taka 領域で 5.5% を v1106 進行に十分と判断するか、v1105b として絞り式の再点検に戻るかを判定。

---

## 3. rank-based 絞り式の Aruism 規律担保 (構造事実)

設計書 §2.4 の rank-based 絞り式 (`1/log(rank+2)` × 積 × 正規化) が Gemini Architect 警告「首位 atom でも確率 0.3 程度」を構造事実として担保:

| 指標 | 値 | 評価 |
|---|---:|---|
| max_prob mean (全 7 系列) | 0.27-0.36 | Gemini「首位 0.3 程度」予想内 |
| max_prob median | 0.13-0.41 | candidate=1 個の event (degenerate) で max=1.0、それ以外は緩やか減衰 |
| max_prob max | 1.0 | candidate=1 個の構造的帰結 (degenerate 1,500 events) |
| max_prob min | 0.09-0.23 | candidate 多数で更に緩やか |

→ **rank-based 絞り式は仕様として Aruism 規律 (複数候補並立) を担保**、ハンドチューニングなし。

---

## 4. 試行内 7 留保 (#L30-L36) の動的観察

### 4.1 #L34 (scope 別 Genesis/Language 逆方向強度) 試行内動的

Genesis vs Language overlap per scope (Step F):

| scope | n_common_events | jaccard_mean | gen_only_events | lang_only_events |
|---|---:|---:|---:|---:|
| alpha | 400 | **0.561** | 3,300 | 0 |
| beta | 600 | **0.247** | 1,800 | 0 |

→ **alpha scope では Language は Genesis の subset (Language ⊂ Genesis)、beta scope では Language が Genesis から独立傾向**。#L34 静的観察 (alpha Genesis 強/Language 弱、beta 逆) と試行内動的動作が整合。

### 4.2 #L35 (CID_n=2 の極端な特殊性) 試行内動的

n_core_bin × valid_rate (Step E):

| n_core_bin | valid_rate |
|---|---:|
| **bin_2** | **5.67%** (最高) |
| bin_3_4 | 3.93% |
| bin_5_plus | 4.59% |

→ **bin_2 (CID_n=2 相当) が valid_rate 最高**、#L35 静的観察 (CID_n=2 で density 6 種 +0.99 / couple_hit_rate 15.7%) の試行内動的反映として bin_2 で pipeline_complete 率が高い。

### 4.3 #L36 (sim_basis × density 種類の 2 軸非対称性) 試行内動的

7 系列 layer_jaccard (Step F、top5 atom 重なり):

| s1 vs | s2 | s3 | s4 | s5 | s6 | s7 |
|---|---:|---:|---:|---:|---:|---:|
| s1 (raw×raw) | 0.85 | 0.81 | 0.82 | **0.97** | 0.85 | 0.72 |
| s2 (raw×norm) | — | 0.77 | 0.85 | 0.84 | **0.99** | 0.68 |
| s3 (qw×raw) | — | — | 0.83 | 0.80 | 0.78 | 0.65 |

→ **s1 (raw×raw) と s5 (const_adj×raw) が 0.97**、s2 (raw×norm) と s6 (const_adj×norm) が 0.99 (couple_bonus 1.1 の効果限定)、**s7 48D k=5 のみ他系列と 0.65-0.73 で独立**。観察 3 (#L36 sign_flip の 2 軸非対称) と試行内で **挙動が異なる** (試行では類似系列化)。

### 4.4 4 つの非対称性 #L30-L33 の試行内再現

- **#L30 scope 別 chain 構造**: 試行内で alpha 候補数 5.5-7.8 / event、beta 6.9-9.5 / event、CID 不在 (Step 2 は CID scope chain なし)、scope 別構造差確認
- **#L31 粒度依存 trajectory-density 優劣**: 試行内で per-atom trajectory rank は ESDE_event/step10 から取得、s7 48D は別動作で粒度依存性を試行で観察
- **#L32 B 指標の scope 別 pattern**: B 高 atom top5 到達 1.2-1.9% で限定、scope 別 B 性質は Step 3 では絞り score 不使用 (read-only)
- **#L33 CID 100% self-loop が trajectory 構造的消失**: 試行 Step 2 は alpha/beta scope のみで CID scope 使わず、#L33 は試行内で観察対象外

---

## 5. 7 系列・6 値統合禁止と構造ラベル統合の確認

- 7 系列で構造ラベル分布が **完全に同値** (全系列 valid 3,300 / empty 55,200 / degen 1,500): rank-based 絞り後の正規化で全系列 atom set がほぼ同じ候補、構造ラベルは候補数構成で決まり density 種類に依存しない
- ただし max_prob / entropy 等の連続指標は系列間で差あり (s7 で集中傾向)
- 共通比較指標を別レイヤーで並列保持 (絶対格言 #11、6 値・7 系列統合禁止遵守)

---

## 6. bit-identity 3 層検証 (Step G)

### 6.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step C-F 再実行で hash 完全一致 (sort 適用後) | **7 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a/v1102/v1103/v1104/v1104a/v1105 main outputs 全 frozen | **all PASS** (a/r/m すべて 0、1,494 files) |
| **C** | 全 5 scripts の書込みパスが unified/v1105a/ 配下 | **all_under=True** (7 件) |

- LAYER_A_FILES (7): trial_step2_associations / trial_step3_distributions / trial_step4_labels / trial_step4_distributions / trial_summary_metrics / trial_layer_jaccard / trial_source_layer_overlap
- LAYER_A_RERUN 経過時間: Step C 4.5s / D 11.1s / E 13.4s / F 3.0s = 計 32.0s
- 初回 run では hash 不一致発生 (4 ファイル)、Step C/D/E/F の最終 sort 適用で hash 一致確保
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 + v1104 13 + v1104a 8 + v1105 4 = **1,494 files 全 frozen 確認**
- 報告 JSON: `v1105a_step_g_bit_identity_report.json`

---

## 7. 規律遵守総括

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.5/6/7 + v1101a〜v1105 read-only、LAYER_B 全 PASS) |
| 絶対格言 #6 (出口の固定) | ✓ (会話成立判定なし、構造ラベルのみ) |
| 絶対格言 #9 (神の手回避) | ✓ (絞り式 rank-based 固定、独自発明なし、ハンドチューニング 0) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (7 系列・6 値統合禁止、別レイヤー保持) |
| 絶対格言 #12 (judgment 回避) | ✓ (success/failure 未使用、構造ラベルのみ、v1106 判定は Web Claude/Taka 領域) |
| GPT 修正必須 (構造ラベル化) | ✓ (pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid 採用) |
| GPT 修正必須 (rank-based 固定) | ✓ (`1/log(rank+2)` 仕様通り、独自発明なし) |
| GPT 追加推奨 (B emit read-only) | ✓ (絞り score に組み込まず、b_high_in_top5_count として観察記録のみ) |
| 試行 ≠ selector 化 | ✓ (役割表 = 構造的指標に従う、ESDE 「自由選択」なし) |
| 試行 ≠ 会話成立判定 | ✓ (構造ラベルのみ、意味判定なし) |
| 試行 ≠ ハンドチューニング | ✓ (絞り式 rank-based 固定、閾値変更なし) |
| 試行方法を有利化しない | ✓ (確認要請 4 件で Taka 判断「ラッキー判定の余地なし」修正反映、結果が出ない場合の方法変更なし) |
| 0 を 1 にはできない歯止め | ✓ (動的計算 100% は欠損補完、v1103 機構流用) |
| 物理層 frozen 境界明示 (§0.6) | ✓ (既存ファイル不変、v1103 計算ロジックの post-process 呼び出し) |
| Aruism 規律仕様化 | ✓ (rank-based 緩やか減衰、max_prob mean 0.27-0.36) |
| 7 系列・6 値別レイヤー保持 | ✓ (Step D/E で全系列並列保持、統合なし) |
| 書込みパス unified/v1105a/ 配下 | ✓ (LAYER_C all_under=True、7 件) |
| smoke 含めず | ✓ (post-process のみ) |

---

## 8. 新規留保候補 4 件 (Code A 報告、Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L37** | candidate_empty 92% は入力 atom が alpha/beta scope chain に登場するか否かで構造的に決まる試行特性。25 atom_id 中で alpha scope に登場するのは限定 (scope 構造の選別性)、これは試行設計上の構造事実であり 0 を 1 にはできない |
| **#L38** | 7 系列で構造ラベル valid_rate が完全同値: rank-based 絞り後の正規化で候補集合がほぼ同じ、density 種類は連続指標 (max_prob 等) で差別化するが離散ラベル付与には影響しない。観察 3 #L36 (sim_basis × density 2 軸非対称) と試行で動作が異なる |
| **#L39** | Genesis ⊃ Language alpha (jaccard 0.561) vs Genesis ⊥ Language beta (jaccard 0.247) の試行内対比: #L34 静的観察 (alpha Genesis 強/Language 弱) と整合的だが、alpha では Language が Genesis subset で全包含、beta では Language が Genesis から独立して候補を持つ |
| **#L40** | s7 48D k=5 のみ他系列と layer_jaccard 0.65-0.73 で独立挙動、max_prob mean 0.36 (他系列 0.27) + entropy mean 1.39 (他 1.91) で集中傾向、reduction_ratio 0.345 で実質削減効果。48D 機構 (v1103 段 4-c) の試行内動作が他 density 系列と質的に異なる |

既存留保継承: #L17 / #L21' / #L22' / #L24-L29 / #L30-L36 / 48 次元人為性留保 (v1103 GPT 監査 5)

---

## 9. 出力ファイル総覧 (`unified/v1105a/`)

| ファイル | サイズ |
|---|---:|
| v1105a_phase_design.md | 設計書 v3 (2 AI 監査 + 確認要請 4 件反映) |
| v1105a_step_a_recognition.md | Code A 認識確認 + 確認要請 4 件 |
| v1105a_step_a_answer.md | Web Claude 回答 (Taka 判断 4 件全採用) |
| v1105a_step_b_env_check.py | 環境準備 |
| v1105a_step_c_trial_step1_2.py | 試行 Step 1+2 (4 source レイヤー連想) |
| v1105a_step_d_trial_step3.py | 試行 Step 3 (rank-based 絞り 7 系列 per-atom) |
| v1105a_step_e_trial_step4.py | 試行 Step 4 (構造ラベル付与) |
| v1105a_step_f_aggregate.py | 観察項目集計 |
| v1105a_step_g_bit_identity.py | bit-identity 3 層検証 |
| v1105a_step_g_bit_identity_report.json | 全 PASS |
| v1105a_step_h_observation_final.md | 本書 |
| outputs/main/trial_step2_associations.parquet | 38,700 rows (4 source × event) |
| outputs/main/trial_step3_distributions.parquet | 206,900 rows (7 系列 × candidate) |
| outputs/main/trial_step4_labels.parquet | 420,000 rows (60,000 events × 7 系列) |
| outputs/main/trial_step4_distributions.parquet | 206,900 rows (ラベル付き分布) |
| outputs/main/trial_summary_metrics.parquet | 7 rows (per series) |
| outputs/main/trial_layer_jaccard.parquet | 49 rows (7×7 対称行列) |
| outputs/main/trial_source_layer_overlap.parquet | 2 rows (alpha/beta scope) |

物理層 (v105/v106/v107/v112/v1101a/v1102/v1103/v1104/v1104a/v1105 main outputs 1,494 ファイル) frozen 維持。

---

## 10. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (v1105a 4 試行段階 + 7 系列観察) の提示完了。以下は Web Claude + Taka 領域:

1. **v1106 接続条件 3 点判定**: 構造的にすべて成立 (§2 参照)、ただし pipeline_complete 5.5% を「十分」と判断するか「v1105b で絞り式再点検」と判断するか
2. **v1106 着手 vs v1105b 移行判断**: 3 条件成立 + 4 留保候補を踏まえた最終判定
3. **v1104 + v1104a + v1105 + v1105a 統合 Phase Result**: 4 観察 × 7 系列 × 4 source レイヤーの集約事実、役割表動作の構造的記述
4. **#L37-L40 新規留保**: candidate_empty 92% の試行特性 / 7 系列構造ラベル同値 / Genesis-Language 対比 / s7 48D 独立挙動
5. **v1106 着手の場合の次主題**: 段 5a/5b 自然文化 (Atom → 単語 → 文) への接続

---

## 11. 一文サマリ (再掲)

Step A-G 全完了、Step A (Taka「ラッキー判定の余地なし」歌手の音痴比喩で確認要請 4 件全面修正 = v108_standard 60,000/動的計算 100%/per-atom rank/max_prob 0.999) → Step B (環境準備、atom_id ↔ candidate_id mapping 確立) → Step C (4 source レイヤー連想 38,700 rows、Genesis 圧倒/Language 12 endpoints 制限) → Step D (rank-based 絞り 7 系列 per-atom 206,900 rows、max_prob mean 0.27-0.36 で Aruism 規律仕様化担保) → Step E (構造ラベル付与 420,000 rows、candidate_empty 92%/degenerate 2.5%/**valid 5.5%**、bin_2 valid_rate 5.67% で #L35 試行内反映) → Step F (観察集計、Genesis ⊃ Language alpha jaccard 0.561 vs Genesis ⊥ Language beta 0.247 で #L34 試行内対比、s1-s6 layer_jaccard 0.77-0.99 / s7 のみ 0.65-0.73 独立) → Step G (bit-identity 3 層全 PASS: LAYER_A 7 ファイル hash 一致 32s / LAYER_B 1,494 frozen 不変 v1105 まで / LAYER_C 7 件 unified/v1105a/ 配下) すべて完了、**v1106 接続条件 3 点すべて構造的成立** (条件 1 pipeline_complete 3,300 events 存在、条件 2 distribution_valid max_prob mean 0.27、条件 3 reduction_ratio s7 34.5% / 他系列 0.2%)、新規留保候補 #L37-L40 提示 (candidate_empty 試行特性 / 7 系列ラベル同値 / Genesis-Language 対比 / s7 48D 独立挙動)、既存留保 #L17/#L21'/#L22'/#L24-29/#L30-L36 + 48 次元人為性留保継承、v1106 着手 vs v1105b 移行判定 + v1104+v1104a+v1105+v1105a 統合 Phase Result + #L37-L40 解釈統合は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + selector 化禁止 + 構造ラベル + 試行 ≠ 会話成立判定/ハンドチューニング + B emit read-only + 7 系列・6 値統合禁止 + 物理層 frozen + 0 を 1 にはできない歯止め) を全 Step で堅持、書込み unified/v1105a/ 配下のみ。
