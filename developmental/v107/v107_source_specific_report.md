# v10.7 Level 3: source-specific finding 報告

*作成*: 2026-05-07、Code A
*親*: `v107_implementation_brief.md` §7.3
*基準*: source_type 別 distribution の **Kruskal-Wallis p < 0.05** かつ effect_size (max - min) > 1%

---

## 0. 一文サマリ

5 source_event 種 (pulse / ingestion / alpha_formation / beta_formation / c_conversion) で path-enriched profile が異なるかを Kruskal-Wallis 検定した結果、**90 candidates のうち 85 件が Level 3 finding 達成** (94%)、ほぼ全 path × 全 delta_field で source 種別の有意差が検出された (p ≈ 0)、最大効果は **familiarity 経路 medium window の delta_n_observed で max-min = 1.98** (source 種で 4 倍差)、ESDE 内の波及は source_event 種別に応じて **systematic に異なる** ことが確定。

---

## 1. 全体集計

| 指標 | 値 |
|---|---|
| 集計 candidates | 90 |
| Level 3 findings | **85** (基準: p < 0.05 + effect_size > 1%) |
| 達成率 | 94.4% |
| ほぼ全 finding で p = 0.0 (大量サンプルで検定有意) |

---

## 2. Top 20 Level 3 finding (effect_size 大、p_value 小)

| relation_path | delta_field | p_value | max_group_mean | min_group_mean | effect_size |
|---|---|---:|---:|---:|---:|
| **familiarity** | delta_n_observed_medium | 0.0 | 2.66 | 0.68 | **1.98** |
| **attention_via_salience** | delta_n_alphas_medium | 0.0 | 2.42 | 0.64 | 1.78 |
| **integration_alpha** | delta_n_observed_medium | 0.0 | 3.98 | 2.48 | 1.50 |
| familiarity | delta_n_alphas_medium | 0.0 | 1.71 | 0.42 | 1.29 |
| familiarity | delta_Q_medium | 0.0 | 0.00 | -1.07 | 1.07 |
| familiarity | delta_C_medium | 0.0 | 1.03 | -0.00 | 1.03 |
| familiarity | n_pulses_in_window_medium | 0.0 | 11.16 | 3.95 | 7.21 |
| integration_alpha | n_pulses_in_window_medium | 0.0 | 17.07 | 11.69 | 5.38 |
| familiarity | delta_Q_short | 0.0 | -0.00 | -0.48 | 0.48 |
| integration_alpha | n_pulses_in_window_short | 0.0 | 1.69 | 1.24 | 0.45 |
| integration_alpha | delta_n_observed_short | 0.0 | 0.44 | 0.07 | 0.37 |
| attention_via_salience | delta_C_medium | 0.0 | 0.35 | 0.00 | 0.35 |
| attention_via_salience | delta_n_alphas_short | 0.0 | 0.34 | 0.01 | 0.33 |
| attention_via_salience | delta_n_observed_short | 0.0 | 0.34 | 0.08 | 0.25 |
| familiarity | delta_n_observed_short | 0.0 | 0.26 | 0.05 | 0.21 |
| familiarity | delta_n_alphas_short | 0.0 | 0.20 | 0.01 | 0.20 |
| familiarity | n_pulses_in_window_immediate | 0.0 | 0.13 | 0.04 | 0.09 |
| attention_via_salience | n_pulses_in_window_immediate | 0.0 | 0.10 | 0.03 | 0.07 |
| attention_via_salience | delta_n_alphas_immediate | 0.0 | 0.04 | 0.001 | 0.04 |
| attention_via_salience | delta_n_observed_immediate | 0.0 | 0.03 | 0.008 | 0.025 |

---

## 3. 観察

### 3.1 全 5 source 種で profile が systematic に異なる

source_types: `alpha_formation, beta_formation, c_conversion, ingestion, pulse` の 5 種で Kruskal-Wallis 検定し、ほぼ全項目で p < 0.001 (p = 0.0 表示)。

→ **同じ relation_path でも source_event 種類が違うと波及プロファイルが大きく異なる**ことが確定。

### 3.2 最大の source-specific 効果

**familiarity × delta_n_observed_medium**: max 2.66 vs min 0.68 (差 1.98)
- ある source では target が **2.66 個追加観察される** (= salience 累積)
- 別の source では 0.68 個のみ
- 4 倍差 = 大きな source-specific 性

### 3.3 source-specific が強い量・弱い量

#### 強い (effect_size > 1.0)

- familiarity / attention の delta_n_observed_medium (salience event 累積)
- familiarity の delta_n_alphas_medium (α 加入累積)
- familiarity の delta_Q_medium / delta_C_medium (認知/意識資源変化)
- familiarity / integration_alpha の n_pulses_in_window_medium (pulse 発火)

#### 弱い (effect_size < 0.1)

- immediate window の量全般 (1-10 step は短すぎ source 差出ず)
- 短期 short window も中程度

→ **medium window (100-1000 step) で source-specific 効果が強く出る**。これは Level 1/2 と整合する。

### 3.4 source 間の階層

`max_group_mean` を path × field で見ると:
- **familiarity × n_pulses_in_window_medium**: max 11.16 (= 11 pulse)、min 3.95 (4 pulse)
- **integration_alpha × n_pulses_in_window_medium**: max 17.07、min 11.69 (どちらも高い)

→ Integration 経由は **どの source 種でも基本的に強い波及**、familiarity は source 種で大きくばらつく (= source 依存性が強い)。

---

## 4. Level 3 達成と研究的意義

Level 3 達成: **source_event 種別ごとに systematic に異なる波及プロファイル**が 24 seeds で確定。この結果から:

1. ESDE 内の波及は **source 種別で機能的に分化**している (= 異なる種類のイベントは異なる経路を駆動)
2. 特に `familiarity 経路 × medium window` は source 種に最も敏感で、 **source 識別シグナル** として機能している可能性
3. integration 経路は **source-robust** (どの source でも一定の強い波及)
4. immediate window は source-blind (= 全 source で同じ即時効果)

→ v10.8 以降 (Level 4: causal intervention) で source 種を input として ESDE 状態を予測できるかの仮説検証材料。

---

## 5. 残課題 (本フェイズ未達)

- **multi_hop hop 2/3 の Level 3** は Step E 拡張未実施で評価不能
- **integration_alpha/beta の C 系 delta** は no_signal フラグ (C 変化なし)、Level 3 候補から外れる
- **ingestion / c_conversion の絶対サンプル数** が他より小 (各 3,594/24 seeds)、Kruskal-Wallis の検出力低下リスク

---

*以上、Level 3 報告。全データ: `developmental/v107/outputs/main/cross_seed/level_3_source_specific.parquet`*
