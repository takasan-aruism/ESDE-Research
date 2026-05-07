# v10.8 Level 3: atom source-specific 報告

*親*: `v108_implementation_brief.md` §5.2 Level 3
*基準*: 25 集計対象 atom 間で Kruskal-Wallis p < 0.05 かつ effect_size (max - min) > 1%

---

## 0. 一文サマリ

5 path × 18 delta field の 24 集計対象 atom 間 Kruskal-Wallis 検定の結果、**78 candidates のうち 36 が Level 3 finding 達成** (46%)、最大 effect_size は **familiarity × medium window n_pulses で 6.83** (atom 別 max 13.02 vs min 6.19、2.1 倍差)、attention_via_salience では effect_size 2.30 (5.55 vs 3.26)、ESDE は atom 種別で systematic に異なる波及プロファイルを示し、**familiarity 経路が最も atom 依存性が強く、temporal_coactivation は atom 中立 (effect_size 0.03)**。

---

## 1. 全体集計

| 指標 | 値 |
|---|---|
| Level 3 candidates | 78 |
| Level 3 findings | **36** (46%) |
| 全 finding で p < 1e-30 (大量サンプルで強有意) |  |

---

## 2. Top 15 Level 3 finding (effect_size 大)

| relation_path | delta_field | p_value | effect_size | max_atom_mean | min_atom_mean |
|---|---|---:|---:|---:|---:|
| **familiarity** | n_pulses_in_window_medium | 1.2e-181 | **6.83** | 13.02 | 6.19 |
| attention_via_salience | n_pulses_in_window_medium | 2.7e-280 | **2.30** | 5.55 | 3.26 |
| familiarity | delta_n_observed_medium | 4.5e-50 | 1.40 | 2.82 | 1.42 |
| integration_beta | delta_n_alphas_medium | 1.0e-47 | 0.88 | 1.52 | 0.63 |
| integration_alpha | delta_n_alphas_medium | 4.9e-46 | 0.85 | 1.35 | 0.51 |
| familiarity | n_pulses_in_window_short | 2.1e-183 | 0.72 | 1.34 | 0.62 |
| familiarity | delta_n_alphas_medium | 2.5e-43 | 0.66 | 1.45 | 0.78 |
| attention_via_salience | delta_n_observed_medium | 4.2e-311 | 0.58 | 1.34 | 0.76 |
| attention_via_salience | delta_n_alphas_medium | 0 | 0.42 | 0.82 | 0.40 |
| attention_via_salience | n_pulses_in_window_short | 3.0e-265 | 0.23 | 0.56 | 0.34 |
| integration_beta | delta_n_alphas_short | 6.1e-45 | 0.11 | 0.19 | 0.08 |
| familiarity | n_pulses_in_window_immediate | 5.6e-33 | 0.11 | 0.17 | 0.07 |
| integration_alpha | delta_n_alphas_short | 3.2e-40 | 0.10 | 0.17 | 0.07 |
| integration_beta | delta_n_observed_short | 1.4e-36 | 0.09 | 0.30 | 0.21 |
| attention_via_salience | delta_n_observed_short | 0 | 0.05 | 0.13 | 0.08 |

---

## 3. path 別の atom 依存性ランキング

最大 effect_size (= atom 種で最も差が出る path):

| path | max effect_size | 解釈 |
|---|---:|---|
| **familiarity** | **6.83** (n_pulses_medium) | atom 種で 6 events 差、強い atom 依存 |
| attention_via_salience | 2.30 | 中程度の atom 依存 |
| integration_alpha/beta | 0.88 / 0.85 | 弱い atom 依存 |
| **temporal_coactivation** | **0.03** (n_pulses_short) | atom 中立、atom 種に依存しない |

→ **familiarity 経路が最も atom-specific**、temporal_coactivation は **atom 中立** という ESDE 構造的特徴。

これは Level 1/2 で「temporal_coactivation 全 atom +15.6〜15.8 で均質」と整合。temporal_coactivation は時間的近接の関係で atom 種に依存せず、familiarity は atom 別の cid ネットワークで差が出る。

---

## 4. v10.7 との比較

v10.7 (5 source × path):
- Level 3 findings: 85
- 最大 effect_size: familiarity × delta_n_observed_medium で 1.98

v10.8 (25 atom × path):
- Level 3 findings: 36 (atom 数増だが p_value 厳格化で減)
- 最大 effect_size: familiarity × n_pulses_medium で **6.83** (3.4 倍)

→ atom 間の差は natural 5 source の差より **大きい**。これは 25 atom が cid 構造的に多様 (top_k cid が異なる) なためで、natural source の 5 種より明確に source-specific。

---

## 5. 観察

Level 3 達成: **atom 種別で systematic に異なる波及プロファイル**確認。特に familiarity 経路で atom 種別の差が顕著 (effect_size 6.83)。

→ ESDE は atom 種別を識別する波及シグナルを持つ可能性 (Level 4 causal intervention の素材、v10.9 以降)。

---

*Level 3.5 で natural との比較を実施 (introduced と natural の波及プロファイル差異)。*
