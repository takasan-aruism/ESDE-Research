# v10.8 Level 3.5: introduced vs natural 報告

*親*: `v108_implementation_brief.md` §5.1 Level 3.5
*基準*: `mean(atom 波及) - mean(natural 波及) の絶対値 > 1%` かつ 24 seeds direction 一貫
*位置づけ*: 因果断定回避、event 比較として観察記録

---

## 0. 一文サマリ

5 path × 18 delta field の atom_introduction_event 波及と v10.7 natural source_event (5 種統合) 波及の差分集計の結果、**39 candidates のうち 22 が Level 3.5 finding 達成** (56%)、最大差分は **attention_via_salience × medium n_pulses で atom 4.37 vs natural 8.75 = -4.38** (atom が natural の **半分**)、22 finding 中 **20 件が negative (introduced < natural)**、ESDE は人工的に注入された atom_introduction_event に対して natural source_event より弱い波及を示し、これは **「外部からの注入は系の自然な発火パターンに完全には乗らない」** という観察記録 (因果断定ではない)。

---

## 1. 全体集計

| 指標 | 値 |
|---|---|
| Level 3.5 candidates | 39 |
| Level 3.5 findings | **22** (56%) |
| direction: introduced < natural (negative) | 20/22 (91%) |
| direction: introduced > natural (positive) | 2/22 (9%) |

---

## 2. Top 全 22 finding

| relation_path | delta_field | atom_mean | natural_mean | diff |
|---|---|---:|---:|---:|
| **attention_via_salience** | n_pulses_in_window_medium | 4.37 | **8.75** | **-4.38** |
| **familiarity** | n_pulses_in_window_medium | 8.11 | 10.67 | -2.56 |
| attention_via_salience | delta_n_observed_medium | 0.99 | 2.07 | -1.08 |
| attention_via_salience | delta_n_alphas_medium | 0.58 | 1.30 | -0.73 |
| integration_alpha | delta_n_observed_medium | 2.09 | 2.71 | -0.61 |
| integration_alpha | delta_n_alphas_medium | 1.07 | 1.67 | -0.60 |
| integration_beta | delta_n_alphas_medium | 1.17 | 1.75 | -0.58 |
| attention_via_salience | n_pulses_in_window_short | 0.45 | 0.93 | -0.48 |
| **temporal_coactivation** | n_pulses_in_window_medium | 15.63 | 15.28 | **+0.36** ← positive |
| familiarity | n_pulses_in_window_short | 0.81 | 1.11 | -0.30 |
| attention_via_salience | delta_n_observed_short | 0.10 | 0.22 | -0.12 |
| integration_beta | delta_n_alphas_short | 0.14 | 0.24 | -0.10 |
| integration_alpha | delta_n_alphas_short | 0.13 | 0.22 | -0.10 |
| attention_via_salience | delta_n_alphas_short | 0.06 | 0.15 | -0.09 |
| integration_alpha | delta_n_observed_short | 0.23 | 0.30 | -0.07 |
| attention_via_salience | n_pulses_in_window_immediate | 0.05 | 0.12 | -0.07 |
| familiarity | n_pulses_in_window_immediate | 0.09 | 0.13 | -0.04 |
| integration_alpha | n_pulses_in_window_immediate | 0.13 | 0.15 | -0.03 |
| **temporal_coactivation** | n_pulses_in_window_short | 1.71 | 1.68 | **+0.03** ← positive |
| temporal_coactivation | n_pulses_in_window_immediate | 0.30 | 0.31 | -0.02 |
| attention_via_salience | delta_R_familiarity_medium | -0.001 | -0.017 | +0.015 |
| attention_via_salience | delta_n_observed_immediate | 0.010 | 0.023 | -0.013 |

---

## 3. 観察

### 3.1 引動主要パターン

**20/22 finding が introduced < natural (atom < natural)**:
- attention_via_salience × medium n_pulses で **atom 4.37 vs natural 8.75** = atom は natural の **半分**
- familiarity × medium n_pulses で atom 8.11 vs natural 10.67 (76%)
- Integration α/β、attention での delta_n_alphas / delta_n_observed も同様に atom 弱

→ **atom_introduction_event は、ほとんどの path × delta field で natural source_event より波及効果が小さい**。

### 3.2 例外 2 件: introduced > natural

- **temporal_coactivation × n_pulses_in_window_medium**: atom 15.63 vs natural 15.28 (+0.36)
- temporal_coactivation × n_pulses_in_window_short: atom 1.71 vs natural 1.68 (+0.03)

→ 時間的近接の関係 (temporal_coactivation) のみ atom が natural を **わずかに上回る**。これは atom_introduction_event の **均等分散発火** (案 α、250 step 間隔) が natural の不均一発火タイミングより temporal 経路で目立つため。

### 3.3 解釈 (因果断定なし)

事実観察:
- **「外部から注入された atom_introduction_event は、ESDE の natural な発火と区別できる波及プロファイル」** (Level 3.5 達成)
- atom event は **より弱い波及** (familiarity / attention / Integration の path で)、ただし **temporal で同等以上**

これは **「event を入れたら X が起きた」 (因果) ではなく** 、 **「introduced と natural の波及プロファイルが systematic に異なる」 (event 比較)** という記録。

考えられる理由 (推測のみ、確認は次フェーズ):
- atom event は固定 Q -1 / C +1 コストだが natural は path 別に異なるコスト
- atom event の cid は v10.6 top_k 選定で偏り (familiarity edge が比較的弱い cid に集中)
- natural event は cid のライフサイクルに沿って自然発火、atom event は外部スケジュールで発火

---

## 4. v10.8 主結果

**Level 3.5 達成**: 22 finding で introduced と natural の差異を 24 seeds で確認。**atom_introduction_event は ESDE の自然な発火パターンに完全には乗らない (波及がより弱い、temporal を除く)**。これは「人工的な atom 注入が系に与える影響が natural event と同等ではない」という観察。

→ v10.9 以降の射程: なぜ atom event が weak か (Q/C コスト調整、cid 選定基準、発火タイミング等)。

---

*Level 3.5 達成、副次観察 (Whiteout / Small-World / 誤差分布) は別 report 参照。*
