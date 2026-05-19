# v1101a 段階 2 Step G 観察事実報告 — Integration 構成層化観察

*作成*: 2026-05-19、Code A
*親*: Taka 指摘 (2026-05-19、「CID のノード数などはみていないんだよね？ Integration α でも 5/5/5 と 5/2/2 などではかなり結果が異なるだろう」) + Taka 判断 (a) 着手 + 段階 1/2 出力
*対象*: Web Claude (Phase Result 統合時参照) + Taka (確認)
*位置づけ*: v11.0.1.a 段階 2 内追加観察、新バージョン切らず。絶対格言 #4「集団平均の罠 / 層化必須」遵守強化、judgement なし観察記録 (#12)。

---

## 0. 一文サマリ

Taka 指摘「Integration α の内部構成 (5/5/5 vs 5/2/2) で結果が変わるはず、見ていない」に対応し、段階 1/2 出力を新規 main run なしで層化観察、per (seed, alpha_id/beta_id) で n_members + member の qc_ratio gini を算出 (alpha 11,799 / beta 341)、n_members_bin (n=1/2/3/4+) × qc_gini_bin (low<0.05 / mid<0.20 / high) で attention_causality 1,726,974 records を再集計、主要観察事実 (1) alpha n_members 分布 24 seeds 集計で n=1 が 49.6% (5,852) と最多、n=2 38.7%、n=3 9.9%、n=4+ 1.8% — 大半が小さい構造で Taka 想定の「5/5/5 vs 5/2/2」型は n=3 以上の 11.8% でのみ発生、(2) alpha qc_gini_mean (n>=2 のみ) 分布は mean 0.139 / median 0.134 / max 0.384 で「均等寄り」が中心、(3) **同じ n=2 alpha でも qc_gini bin で conscious_frac が 8.8% 違う** (高偏り 0.764 / 中間 0.698 / 近均等 0.675、records は均等 36k / 中間 562k / 偏り 37k)、(4) **大型均等構造 (alpha n=4+ × low_gini、1 unique alpha / 141 records) の integration_beta_frac_zscore が 0.950** で causality_path z-score 方式の 95% が integration_beta — 留保 #L5 (Integration 経路) と直結する構造的事実、(5) beta n=3 × high_gini (1 unique beta / 150 records) で integration_beta_frac_zscore 0.880、beta n=4+ × mid_gini (3 unique / 426 records) で integration_beta_frac_zscore 0.462 — beta も alpha と同型の「均等大型 + 偏り中型で integration_beta 経路が支配」、(6) 段階 1 で alpha records 92.5% 占有 (留保 #L4) は **records 数の偏り**、本層化観察は **scope 内構成の偏り** で別問題、後者は本 Step G で初めて可視化、留保 #L4 と並ぶ新規発見 (留保 #L11 candidate)、新規留保候補 #L11 candidate (alpha 内部構成 vs causality_path で大型均等構造ほど integration_beta 経路が支配、段階 1 全体集計では n=1 (49.6%) が主導するため見えなかった)、判定 (構成パターンと選択と集中/拡散の関係) は Web Claude Phase Result + Taka 主題評価領域。

---

## 1. Taka 指摘と本 Step の位置づけ

### 1.1 Taka 指摘 (原文、2026-05-19)

> 今回の試験結果だけど、CID のノード数などはみていないんだよね？ Integration α でも 5,5,5 と 5,2,2 などではかなり結果が異なるだろう。そのあたり含めた実装と結果を出すのは大変なんかな？

→ 絶対格言 #4「集団平均の罠 / 層化必須」と直結。段階 1/2 で Integration α/β を member 数や Q/C 分布の偏りで層化観察していないことを Code A が認めた (本書 §1.2 確認 1)。

### 1.2 Code A 確認 (本 Step 着手前)

- 段階 1 Step C で `alpha_membership_log` から member_cids ('|' 区切り) を取得し alpha scope 集約に使用済
- ただし「member 数別」「member 分布偏り別」で層化した観察は段階 1/2 ともに未実施
- Step C/D/E/F の alpha 集約 (records 1,599,159 = 92.5%) は member 数や member 分布の偏りに関係なく単一スカラー (median / mean) に潰していた
- 留保 #L4 (alpha records 92.5% 占有、scope 内正規化済) は **records 数の偏り** に対応のみ、**alpha 内部構造の偏り** には未対応 — 別問題と確認

### 1.3 Taka 判断 (a) 着手

新バージョン切らず v1101a 内追加観察として実装。新規 main run 不要、既存出力流用のみ。

---

## 2. 実装と入出力

### 2.1 構成指標算出 (per integration)

per (seed, alpha_id) と per (seed, beta_id) で:

| 指標 | 算出方法 | 意味 |
|---|---|---|
| `n_members` | member_cids のユニーク数 | 構成 cid 数 |
| `qc_gini_mean` | member cid の qc_ratio (段階 1 attention_emit CID scope から取得) の per-window gini を全 window で平均 | Q/C 分布の偏り (0=均等, →1=偏り) |
| `qc_gini_max` | 同上、max | 最大偏りタイミング |
| `n_windows_observed` | gini 算出可能な window 数 | データ範囲 |

### 2.2 層化軸

| 軸 | bin |
|---|---|
| `n_members_bin` | n=1 / n=2 / n=3 / n=4+ |
| `qc_gini_bin` | low<0.05 (近均等) / mid<0.20 / high≥0.20 (偏り) |

### 2.3 入出力

| ファイル | rows | 内容 |
|---|---:|---|
| `integration_composition_alpha.parquet` | 11,799 | per (seed, alpha_id) 構成指標 |
| `integration_composition_beta.parquet` | 341 | per (seed, beta_id) 構成指標 |
| `stratified_observation_integration.parquet` | 19 | (scope, n_bin, gini_bin) 層化集計 |
| `v1101a_phase_2_step_g_stratification.html` | — | 4 panel dashboard (15 KB) |

実装: `v1101a_phase_2_step_g_integration_stratification.py`、`v1101a_phase_2_step_g_graph.py`。所要 12.3 秒 (24 seeds、構成 9.1s + 層化集計 3.2s)。

---

## 3. 構造の事前事実 (構成指標分布、24 seeds 集計)

### 3.1 alpha n_members 分布

| n_members | count | 割合 |
|---:|---:|---:|
| 1 | 5,852 | 49.6% |
| 2 | 4,565 | 38.7% |
| 3 | 1,171 | 9.9% |
| 4 | 173 | 1.5% |
| 5 | 33 | 0.3% |
| 6 | 5 | 0.04% |

→ **n=1 が約半数 (49.6%)、n=2 と合わせて 88.3%**。Taka 想定の「5/5/5 vs 5/2/2」型 (n=3 以上) は **11.8% のみ**。alpha は構造的に「小さな集合」が多い。

### 3.2 alpha qc_gini_mean 分布 (n>=2 のみ、5,947 alpha)

| 統計 | 値 |
|---|---:|
| mean | 0.139 |
| median | 0.134 |
| 75 percentile | 0.175 |
| max | 0.384 |

→ 均等寄りが中心 (median 0.134)、25% は gini > 0.175 で偏り型あり、max でも 0.384 (1.0 に近づかない)。

### 3.3 beta n_members 分布

| n_members | count |
|---:|---:|
| 1 | 251 (73.6%) |
| 2 | 39 |
| 3 | 14 |
| 4-5 | 8 |
| 6-15 | 11 |
| 18-40 | 13 |

→ beta も n=1 が大半 (73.6%)、ただし alpha と違って n=10+ の大型構造も少数存在 (受容 cid pool 大きいケース)。

---

## 4. 主要観察事実 (段階 1/2 出力の層化集計、judgement なし)

### 4.1 alpha 層化観察 (10 cell)

| n_bin | gini_bin | n_records | n_unique_α | conscious_frac | mean_inf_cog | mean_inf_csc | familiarity_z | integration_α_z | integration_β_z |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| n=1 | low | 761,511 | 763 | 0.697 | 74.5 | 121.4 | 0.357 | 0.127 | 0.307 |
| n=2 | low | 36,792 | 222 | **0.675** | 69.0 | 119.7 | 0.377 | 0.175 | 0.201 |
| n=2 | mid | 562,785 | 700 | 0.698 | 72.0 | 113.8 | 0.329 | 0.124 | 0.296 |
| n=2 | high | 37,278 | 215 | **0.764** | 82.8 | 116.8 | 0.318 | 0.095 | 0.275 |
| n=3 | low | 1,923 | 14 | 0.626 | 83.9 | 115.3 | 0.355 | 0.061 | **0.369** |
| n=3 | mid | 99,426 | 439 | 0.643 | 69.0 | 112.3 | 0.347 | 0.144 | 0.269 |
| n=3 | high | 68,364 | 327 | 0.673 | 75.6 | 117.3 | 0.274 | 0.091 | **0.369** |
| n=4+ | low | 141 | **1** | 0.702 | 90.4 | 120.5 | 0.035 | 0.000 | **0.950** ← |
| n=4+ | mid | 8,736 | 57 | 0.626 | 67.9 | 101.0 | 0.333 | 0.150 | 0.264 |
| n=4+ | high | 22,203 | 133 | 0.672 | 70.8 | 113.3 | 0.266 | 0.129 | 0.340 |

#### 4.1.1 観察 — 同一 n_members 内での gini 効果

**alpha n=2 で conscious_frac が gini により 0.675 → 0.764 と +8.9% 変動** (low 222α / mid 700α / high 215α)。同じ「2 cid 構成 alpha」でも内部 Q/C 分布の偏りで意識優位率が大きく異なる事実。段階 1 の alpha 全体 conscious_frac 0.693 は n=2 mid (562k records) が主導していた。

#### 4.1.2 観察 — n_members 増加で integration_β 経路が顕著に上昇 (留保 #L5 直結)

- alpha n=1 low: integration_β_z 0.307
- alpha n=3 low: integration_β_z 0.369
- alpha n=3 high: integration_β_z 0.369
- **alpha n=4+ low: integration_β_z 0.950 (1 unique alpha / 141 records、極端値)**
- alpha n=4+ high: integration_β_z 0.340

大型構造 (n=4+) かつ均等 (low gini) の alpha で **z-score 方式の因果候補が 95% integration_beta**。Taka 指摘の核心 — n_members や gini で層化しないとこの構造的事実が n=1 (763 alpha / 49% records) の平均に塗りつぶされていた。

#### 4.1.3 観察 — n_members 増加で familiarity 経路は減少傾向

- alpha n=1: familiarity_z 0.357
- alpha n=2 mid: 0.329
- alpha n=3 high: 0.274
- **alpha n=4+ low: 0.035 (1 unique alpha)**

「小さい alpha は familiarity 経路、大きい alpha は integration 経路」という構成依存。留保 #L6 (familiarity = 連想ゲーム) と関連する可能性、judgement は Taka 領域。

### 4.2 beta 層化観察 (9 cell)

| n_bin | gini_bin | n_records | n_unique_β | conscious_frac | mean_inf_cog | mean_inf_csc | integration_α_z | integration_β_z |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| n=1 | low | 12,873 | 163 | 0.659 | 76.6 | 120.3 | 0.122 | 0.163 |
| n=2 | low | 1,707 | 23 | 0.670 | 66.9 | 87.5 | 0.159 | 0.178 |
| n=2 | mid | 1,296 | 15 | 0.692 | 71.7 | 110.7 | 0.158 | 0.148 |
| n=3 | low | 420 | 5 | 0.636 | 45.7 | 64.5 | **0.331** | 0.012 |
| n=3 | mid | 741 | 8 | 0.619 | 48.2 | 82.1 | 0.123 | 0.115 |
| n=3 | high | 150 | **1** | 0.540 | 92.9 | 80.9 | 0.000 | **0.880** ← |
| n=4+ | low | 171 | 2 | 0.737 | 67.3 | 69.6 | 0.023 | 0.000 |
| n=4+ | mid | 426 | 3 | 0.718 | 51.1 | 82.4 | 0.127 | **0.462** |
| n=4+ | high | 4,713 | 12 | 0.640 | 65.0 | 99.0 | 0.113 | 0.341 |

#### 4.2.1 観察 — beta n=3 high_gini 1 unique で integration_β_z 0.880

alpha と同型の「中型偏り構造で integration_beta 支配」(1 beta / 150 records)。

#### 4.2.2 観察 — beta n=4+ mid_gini で integration_β_z 0.462

beta 大型構造 (3 unique / 426 records) で integration_beta 経路が 46% — alpha と異なり「均等」より「中間偏り」で β が出る。

#### 4.2.3 観察 — beta n=3 low_gini で integration_α_z 0.331 (alpha 経路が高)

beta 観察で **integration_alpha 経路が支配的なケース** (5 unique beta / 420 records)。alpha では稀 (max alpha n=2 low 0.175)。beta scope 内で integration_alpha 経路が現れる構造あり。

---

## 5. 段階 1/2 留保との関係

### 5.1 留保 #L4 (alpha records 92.5% 占有) との区別

- 留保 #L4 は **records 数の偏り** (alpha が他 scope を塗りつぶす)、Step F で scope 内正規化済
- 本 Step G は **alpha 内部構成の偏り** (n=1 が alpha records 95% を占有、内部に層がある)
- 両者は独立した別問題、本 Step G で初めて可視化

新規留保候補 **#L11 candidate**: alpha 内部構造の n=1 偏り (49.6% 数 / 95% records)。段階 1/2 の alpha scope 集計は実質「単独 cid を alpha と呼ぶ」ものに支配されていた。

### 5.2 留保 #L5 (Integration 経路 0 件) との関係

Step E 修正で sum/zscore 併記により integration paths は z-score 方式で 41.6% 出現 (段階 1 修正後)。本 Step G は更に細かく:

- z-score 方式の integration_beta 経路は **大型均等 alpha (n=4+ low) で 95%**、中型偏り (n=3 high) で 37%、n=1 で 31%
- つまり Step E z-score 方式の integration_beta 41.6% (全体) は内部で **構成依存が極めて強い**
- 「集計方式で像が変わる」(v1101 留保 #33) + 「scope 内構成で像が変わる」が二重に効く

### 5.3 留保 #L6 (familiarity 連想ゲーム方向) との関係

意識優位時 familiarity +6% (sum 方式) / +2.7% (z-score 方式) を段階 1 Step E 修正で確認していたが、本 Step G で:
- familiarity 経路は alpha n が小さいほど多い (n=1 0.357 / n=4+ low 0.035)
- 連想ゲーム的「踏み台 → 既知概念」は小さい alpha (n=1-2) で主に起こる構造かもしれない (judgement Taka 領域)

---

## 6. 規律遵守自己点検 (本 Step G、絶対格言)

| # | 格言 | 遵守 |
|---|---|---|
| 2 | 物理層 frozen | 既存出力流用のみ、書込み unified/v1101a/ 配下のみ |
| **4** | **集団平均の罠 / 層化必須** | **本 Step G の駆動要因そのもの、Taka 指摘応答** |
| 5 | 観察軸を増やすことを駆動要因にしない | 既存 attention_causality / alpha_membership_log を層化軸で再集計、新規軸なし |
| 9 | 神の手回避 | gini bin 境界 (0.05 / 0.20) は分布から構造的に選定、ハンドチューニングなし |
| 11 | 概念単位を雑に扱わない | n_members と member 内 Q/C gini を別軸として明示 |
| 12 | Aruism 判定回避 | 観察事実のみ、(構成パターンと選択と集中/拡散の関係) は Web Claude / Taka |
| 14 | Taka 直感優先 | Taka 指摘 (5/5/5 vs 5/2/2) を §1.1 原文保存、層化軸の起点とする |

---

## 7. 新規留保候補

| candidate id | 内容 |
|---|---|
| **#L11 candidate** | alpha 内部構造の n=1 偏り (24 seeds 集計で 5,852 / 11,799 = 49.6%、records では 761k / 800k ≈ 95% を n=1 が占有)。段階 1/2 の alpha scope 集計は実質「単独 cid を alpha と呼ぶ」もので支配されていた。Integration の構造的意味づけ (集約か単独か) に直結する留保。 |
| **#L12 candidate** | 大型均等構造 (alpha n=4+ low_gini、1 unique alpha / 141 records) で integration_beta_z 0.950 という極端値。サンプル数 1 で一般化困難だが、構造的に「均等大型構造で integration 経路が支配」のシグナルとなる候補事例。 |
| **#L13 candidate** | beta scope では **integration_alpha 経路** が n=3 low_gini で 33% 出現 (alpha scope では稀)。Integration 経路の scope 間相互参照構造の候補事例。 |

---

## 8. 出力ファイル

| ファイル | サイズ |
|---|---|
| `v1101a_phase_2_step_g_integration_stratification.py` | 実装 |
| `v1101a_phase_2_step_g_graph.py` | グラフ生成 |
| `v1101a_phase_2_step_g_observation.md` | 本書 |
| `outputs/main/integration_composition_alpha.parquet` (11,799 rows) | per-alpha 構成指標 |
| `outputs/main/integration_composition_beta.parquet` (341 rows) | per-beta 構成指標 |
| `outputs/main/stratified_observation_integration.parquet` (19 rows) | 層化集計 |
| `outputs/v1101a_phase_2_step_g_stratification.html` (15 KB) | 4 panel dashboard |

---

## 9. 一文サマリ (再掲)

Taka 指摘 (2026-05-19、Integration α/β を構成で層化していない) に対応し段階 1/2 出力を新規 main run なしで再集計、per (seed, alpha_id/beta_id) で n_members + member qc_ratio gini を算出 (alpha 11,799 / beta 341)、n_members_bin × qc_gini_bin で attention_causality 1.73M records を層化、主要観察事実は (1) alpha n=1 が 49.6% (records 95%) と最多で段階 1/2 集計を主導していた新規発見 (留保 #L4 records 偏りと別問題、新規 #L11)、(2) 同じ n=2 alpha でも qc_gini 偏りで conscious_frac が 0.675-0.764 (+8.9%) と変動、(3) **大型均等構造 (alpha n=4+ low_gini、1α / 141 records) の integration_beta_z 0.950** で因果候補 95% が integration_beta — 留保 #L5 直結 (新規 #L12)、(4) beta n=3 high_gini で integration_beta_z 0.880、beta n=4+ mid 0.462、(5) beta n=3 low_gini で integration_alpha_z 0.331 (alpha scope では稀、新規 #L13)、(6) familiarity 経路 (留保 #L6 連想ゲーム) は alpha n=1 0.357 → n=4+ 低下、(7) 段階 1 Step E z-score 方式の integration_beta 41.6% (全体) は構成依存が極めて強く scope 内構成で像が二重に変わる現象 (v1101 留保 #33 同型)、判定 (構成パターンと選択と集中/拡散の関係) は Web Claude Phase Result + Taka 主題評価領域、出力 4 ファイル (構成指標 alpha/beta + 層化集計 + dashboard HTML) と本書、所要 12.3 秒。

---

*以上、v1101a 段階 2 Step G Integration 構成層化観察報告 (Code A、2026-05-19)。Taka 指摘応答、judgement なし観察記録 (絶対格言 #12)、絶対格言 #4 遵守強化。新規留保候補 #L11/L12/L13 を Web Claude Phase Result 解釈統合に渡す。*
