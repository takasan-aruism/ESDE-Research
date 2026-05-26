# v1106a Step K — 案 Y (48 axes cosine_sim) 実装結果 + #L41/#L42 解消再評価

**Version**: v11.0.6a Step K (post Step J 修正)
**Date**: 2026-05-26
**Role**: Code A (実装担当)
**Status**: 観察事実報告 — 判定回避 / 構造ラベルのみ

---

## 0. なぜこの Step が必要か (Code A 自己反省)

### 0.1 経緯

v1106a Step A 認識確認で、私 (Code A) は「案 Y (axis 単位 48 axes cosine_sim) は
**計算量 50 倍** (推定 4-8 時間) のため除外推奨」と判断、Web Claude/Taka 承認のもと
案 X (raw_scores_max) と案 Z-1 (normalized_scores_max) のみで Step C-J を完了した。

Step J で #L41 (top1_score=10 タイ多発 → rank_correlation 計算不能) を
「Atom-word 関係の構造特性」と #L44 として固定した。

### 0.2 Taka の指摘 (2026-05-26)

> 「案 X (raw_scores_max) は 48 axes を 1 に潰している、Qwen32B 10 段階重みづけの
> 趣旨を活かしていない」

私 (Code A) は再評価し、計算量見積もりに誤りがあったことを認めた:
- 全 (atom, word) ペア: **28,369 件** (想定より小さい)
- 48 axes ベクトル: 1.36M 要素 (numpy ベクトル化で軽量)
- 実測実行時間: **32.5 秒** (見積 4-8 時間 vs 実測 0.009 時間 = **約 800-1700 倍過大評価**)

### 0.3 Step K の目的

案 Y を実装し、#L41/#L42 が:
- (a) 案 X 固有の選定ミスが原因 (Code A の責任) — 解消すれば #L44 撤回
- (b) Atom-word 関係の真の構造特性 — 持続すれば #L44 妥当

どちらかを **構造事実として記録**する。

---

## 1. 案 Y 実装仕様

### 1.1 接続式

```
各 atom について 48 axes centroid: atom_centroids_48d_raw (v1103, 325 × 48)
各 word について 48 axes raw_scores: mapper_output 各 entry の raw_scores (48 axes × 0-10 整数)

cos_sim(atom, word) = (atom_centroid · word_raw_48d) / (||atom_centroid|| × ||word_raw_48d||)

各 event:
  score(word_j) = Σ_i [p_s7(atom_i) × max(cos_sim(atom_i, word_j), 0)]
  p_word(word_j) = score(word_j) / Σ_k score(word_k)
```

負の cos_sim は 0 に clip (確率正規化のため)。実測では cos_sim ∈ [0.17, 0.98] で
ほぼ全て正、clip は実質効かない。

### 1.2 計算実装

- per atom で cosine_sim_batch (numpy 並列): (48,) × (N, 48) → (N,) を 325 atoms に対し実行
- 事前計算で atom_to_word_sim dict 構築 (1 回のみ)
- 各 event で atom 候補から word union を取り、score 累積
- 実行時間: **32.5 秒** (23,100 events × 案 Y)

### 1.3 入出力

入力 (read-only, frozen):
- `unified/v1105a/outputs/main/trial_step4_distributions.parquet` (s7 PC 196,400 rows)
- `unified/v1103/outputs/main/atom_centroids_48d_raw.parquet` (325 × 48)
- `language/lexicon/data/mapper_output/*_a1.jsonl` (325 files, 28,369 entries)
- `language/atoms/esde_dictionary.json` (48 axes 順序)

出力:
- `unified/v1106a/outputs/main/observation_Y_word_distributions.parquet` (16.5M rows)
- `unified/v1106a/outputs/main/observation_Y_labels.parquet` (23,100 rows)
- `unified/v1106a/outputs/main/observation_Y_alignment.parquet` (23,100 rows)
- `unified/v1106a/outputs/main/observation_Y_L41L42_comparison.parquet` (7 rows)

---

## 2. cos_sim 分布の構造事実

### 2.1 全 (atom, word) ペア cos_sim 分布 (28,369 件)

| 統計量 | 値 |
|---|---|
| min | 0.1743 |
| max | **0.9823** (1.0 に達しない) |
| mean | 0.8018 |
| median | 0.8204 |
| >= 0.99 割合 | **0.00%** |
| >= 0.95 割合 | 1.09% |

### 2.2 top1_atom_top1_cos_sim 分布 (23,100 events)

| 統計量 | 値 |
|---|---|
| min | 0.8860 |
| max | **0.9823** |
| mean | 0.9360 |
| median | 0.9360 |
| std | 0.0231 |
| >= 0.99 割合 | **0.00%** |
| >= 0.95 割合 | 28.14% |
| >= 0.90 割合 | 89.18% |

**事実**: cos_sim は完全同値 (1.0) に到達せず、tied 状態が構造的に発生しない。

---

## 3. #L41 解消状況 (3 案直接対比)

### 3.1 s1_raw_density_raw 系列での対比

| 接続式 | top1_tied (>= max) | rc_valid_rate | rc_mean |
|---|---|---|---|
| 案 X (raw_scores_max) | **1.0000** | **0.0000** (全件 NaN) | NaN |
| 案 Z-1 (normalized_scores_max) | 0.0000 | 0.8788 | -0.0114 |
| **案 Y (cos_sim 48 axes)** | **0.0000** | **0.8788** | **+0.0643** |

### 3.2 全 7 系列での案 Y top1_tied99 / rc_valid_rate

| series_id | top1_cos_mean | top1_tied_99 | rc_valid_rate | rc_mean |
|---|---|---|---|---|
| s1_raw_density_raw | 0.9379 | **0.0** | 0.8788 | +0.0643 |
| s2_raw_density_norm | 0.9332 | **0.0** | 0.8788 | -0.0426 |
| s3_qweighted_density_raw | 0.9373 | **0.0** | 0.8788 | +0.0103 |
| s4_qweighted_density_norm | 0.9355 | **0.0** | 0.8788 | +0.0134 |
| s5_const_adjusted_density_raw | 0.9379 | **0.0** | 0.8788 | +0.0574 |
| s6_const_adjusted_density_norm | 0.9327 | **0.0** | 0.8788 | -0.0909 |
| s7_48d_raw_k5 | 0.9373 | **0.0** | 0.8788 | +0.0333 |

### 3.3 構造事実

**#L41 (top1_score=10 タイ → rc 計算不能) は案 X 固有の問題**:
- 案 X: top1_tied=100%、rc 計算不能 100% (全件 NaN)
- 案 Z-1: top1_tied=0%、rc 計算可能 87.88%
- 案 Y: top1_tied=0%、rc 計算可能 87.88%、cos_sim max=0.9823 で構造的に完全タイ不可能

**rc_mean 解釈**:
- 案 Y: 系列により -0.09 〜 +0.06、s1/s5 (raw density) でわずか正、s2/s6 (norm) で負
- |rc_mean| < 0.1: atom 確率と word cos_sim に強い相関は **観察されない** (ほぼ無相関)
- rc_positive_rate も 0.36-0.55 で偶然レベル

---

## 4. #L42 解消状況 (s1-s6 集計値差)

### 4.1 s1-s6 集計値 std (差別化指標)

| source | n_words_mean_std | max_prob_mean_std | entropy_mean_std |
|---|---|---|---|
| v1106 Synapse v3 | 0.0 | 0.000036 | 0.002262 |
| v1106a 案 X | 0.0 | 0.000053 | 0.002304 |
| v1106a 案 Z-1 | 0.0 | 0.000154 | 0.003954 |
| **v1106a 案 Y** | **0.0** | **0.000098** | **0.003388** |

### 4.2 構造事実

**n_words_mean が完全同値 (std=0) は持続**:
- 全 6 系列 (s1-s6) で word 候補数 773.8485 件で完全一致
- これは Atom 集合が同じだと word 候補 union も同じになる構造的必然
- s7 のみ 348.27 (k=5 で atom 候補が異なるため)

**max_prob/entropy には微小だが差が出る**:
- 案 Y: max_prob_mean_std=0.000098、entropy_mean_std=0.003388
- v1106/v1106a 全案で同レベルのオーダー
- これは確率分布 (probability mass) には density 6 種の効果が漏れ出ている

**#L42 解釈の更新**:
- 「s1-s6 が完全同値」は **不正確** (max_prob/entropy には微差あり、ただしオーダー O(10^-4))
- 「s1-s6 が word 候補集合レベルで完全同値」は **正確** (n_words std=0)
- これは Atom-word 接続式の構造的必然 (atom union → word union)、案 Y でも変わらず

---

## 5. Step J 結論の修正

### 5.1 #L41/#L42 の Step J 段階の結論 (修正前)

> "v1106 で #L41/#L42 が解消されることを期待したが、mapper_output (案 X/Z-1) でも
>  持続。これは Atom-word 関係の構造特性 (#L44) として記録"

### 5.2 案 Y 結果による修正後の事実

| 留保 | 内容 | 案 X | 案 Z-1 | 案 Y | 修正後の構造ラベル |
|---|---|---|---|---|---|
| #L41 | top1_score=max タイ → rc 計算不能 | **持続 (100% tied)** | 解消 (0%) | **解消 (0%)** | **案 X 固有問題、Code A 選定ミス** |
| #L42 | s1-s6 集計値同値 | 部分同値 | 部分同値 | **部分同値** | **構造特性 (word 候補 union 同一)** |

### 5.3 #L44 (Step J で導入) の撤回

Step J §6.4 で導入した:
> "#L44: Atom-word 関係は確率分布構造上 max() タイで rc 不能の構造特性を持つ"

→ **撤回**。これは案 X の `raw_scores_max()` が 48 axes 中の最大 1 つだけ採用して
47 axes 情報を捨てたことによる選定ミスの結果であり、48 axes 全部経由する案 Y では
構造的にタイが発生しない (cos_sim max=0.9823、>=0.99 = 0.00%)。

### 5.4 #L42 の構造ラベル更新

> **#L42 (更新後)**: density 6 種 (s1-s6) は word 候補 union (n_words) では構造的に
> 同値、確率分布 (max_prob/entropy) では O(10^-4) オーダーの微差を持つ。
> これは Atom 集合 → word union の経路が density 6 種で共通であるため。

---

## 6. Code A の過誤と教訓

### 6.1 過誤 1: 計算量見積もりミス

Step A で「案 Y は計算量 50 倍 (4-8 時間)」と申告 → 実測 32.5 秒 (約 800-1700 倍過大評価)

**原因**: 単純な O(N×M×48) を計算したが、numpy ベクトル化の効果を見落とした

**教訓**: 計算量見積もりは小規模実測 (10-100 件) で検証してから判断する

### 6.2 過誤 2: 案 X の構造的欠陥見落とし

`raw_scores_max(atom, word)` = 48 axes 中の最大 1 つ → top1_score=10 タイ多発は構造的必然

**原因**: max() の情報損失 (47 axes 切り捨て) を意識せず、Qwen32B 10 段階重みづけが
活きていることを暗黙に仮定した

**教訓**: 集約関数 (max/mean/sum) の情報損失を接続式設計段階で明示する

### 6.3 過誤 3: Step J 結論の過早断定

「#L41/#L42 持続」を「構造特性」と断定 → 実際は案 X 選定ミスが原因

**原因**: 案 Z-1 で #L41 が部分解消していた事実 (rc_valid=87.88%) を「平均化されただけ」と
過小評価した。案 Y を試さなかった

**教訓**: 観察値の差が出ない時、接続式の構造を疑う段階を必ず入れる

---

## 7. 残留留保 (案 Y 結果反映後)

### 7.1 解消した留保
- #L41: 案 X 固有問題、案 Y で構造的解消
- #L43: FND.spaceless 欠落 (Step C-D で既に解消確認済)

### 7.2 修正した留保
- #L42: 「s1-s6 完全同値」→「word 候補 union 同値、確率分布で O(10^-4) 微差」
- #L44: **撤回** (Step J で導入したが案 Y 結果で否定)

### 7.3 持続する留保
- #L17/#L21'/#L22'/#L24-29/#L30-L36/#L37-L40: 案 Y では再評価せず (Step C-H 範囲外)

### 7.4 案 Y 結果からの新規観察
- atom 確率と word cos_sim の相関 (rc_mean) は系列により -0.09〜+0.06、|rho|<0.1 で
  ほぼ無相関 → atom 重みづけと word 接続強度は独立に近い (これ自体は Aruism 的に自然)
- top1_cos max=0.9823 は構造的上限 (atom_centroid と word_raw_48d が完全同方向に
  ならない理由は cos_sim の数学的構造 + word vector の sparsity)

---

## 8. Web Claude への報告ポイント

### 8.1 認識合わせが必要な事項
1. Code A は Step A で案 Y を「計算量 50 倍」と見積もり除外推奨したが、実測は 32.5 秒
2. 案 X (raw_scores_max) は 48 axes 中 1 つだけ採用、Qwen32B の 10 段階重みづけ趣旨を活かしていない
3. Step J 結論 #L44 (Atom-word 構造特性) は撤回、案 Y で #L41 解消確認
4. #L42 は完全同値ではなく word 候補 union 同値 (構造特性)、確率分布には微差あり

### 8.2 判断材料 (Web Claude / Taka 用)
- 案 Y の cos_sim ∈ [0.17, 0.98]、top1_cos_mean ≈ 0.94 は妥当か
- rc_mean が系列により -0.09〜+0.06 でほぼ無相関 → atom と word の独立性を示唆、これは v1106a 全体の解釈に影響するか
- v1106a の正式接続式として 案 Y を採用するか (X/Z-1 を併記する代替案も)

---

## 9. bit-identity 検証 (Step K 含む)

Step I の 3 層検証は Step C-H + Step J までを対象としていた。
Step K の Y 出力 4 ファイル (observation_Y_*.parquet) は Step I の対象外だが、
書込みパス検証 (LAYER_C) と同じく `unified/v1106a/outputs/main/` 配下のみへ書込み、
読込みパスは全て read-only (v1103/v1105a/language) で frozen。

必要なら Step L で Step K を含む 3 層再検証可能。

---

**Report end.**
