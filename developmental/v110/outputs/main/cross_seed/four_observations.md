# v10.10 4 種観察 (Step H)
*主題ドキュメント §5.1 の構造的事実 / 24 seeds 方向一致 / 効果量階層 / 留保事項更新*

## (a) 構造的事実
- 24 seeds × 28 conditions main run 完了 (全 155,448 sensitivity rows)
- bit-identity 全層 PASS (層 A 85 files / 層 B v107+v108+v109 = 867 files / 層 C パス制限)
- 全 seed で sensitivity rows = 6,408-6,480 (seed 23 のみ若干少、他は 6,480)
- comparison_type 数: 3, comparison_name 数: 42

## (b) 24 seeds 方向一致 (Web Claude Round 1 §1.4 4 段階観察)

### gate_effect (mean_delta_C × medium)
- complete_consistent: 90
- majority_consistent: 79
- tied: 35

### v110_vs_v108re (mean_delta_C × medium)
- complete_consistent: 8
- majority_consistent: 43
- tied: 27

### timing_axis (mean_delta_C × medium)
- complete_consistent: 12
- majority_consistent: 34
- tied: 32

## (c) 効果量階層 (comparison_type 別、全 metric × path × window)

| comparison_type | abs_mean | abs_max | n_large(>=0.5) |
|---|---:|---:|---:|
| gate_effect | 0.098 | 2.468 | 1615 |
| v110_vs_v108re | 0.445 | 9.545 | 8525 |
| timing_axis | 0.245 | 7.314 | 3662 |

## (d) 留保事項更新

v10.9 継承 3 件 + v10.10 新規発生:
1. (継承) bimodal KDE fallback 100% (v10.9 留保 1)
2. (継承) QC_cost 評価不能 (v10.9 留保 2、v10.10 では非対象)
3. (継承) high_fam_out_integ 構造未解明 (v10.9 留保 3、v10.10 で再確認)
4. (新規) **gate 効果が mean_delta_C medium で abs_mean 0.053 と小さい** (v10.9 で観察された high_fam_out 経路の 0.222 が複合 gate / 母集団小化で減衰)
5. (新規) **timing 軸 (t200 vs t500) で全 gate が負方向** (t500 で C 波及増 = age=500 で短命 cid 脱落の効果が外部刺激への C 反応を増す方向)
6. (新規) **v110 vs v108_re で全 gate が正方向** (v110 全体は v108_re より C 波及が大、ただし gate 効果としてではなく timing=age=200 集中の効果)

## Level 3.5 構造的統合 (v109 vs v110)

| path | v109 bimodal n | v109 dom | v109 pct | v110 timing axis | consistency |
|---|---:|---|---:|---:|---|
| familiarity | 214 | H3_lifecycle | 59.3% | -0.079 | v110_reverses_v109 |
| same_integration_low_familiarity_baseline | 0 | n/a | 0.0% | 0.087 | n/a or marginal |
| high_familiarity_outside_integration_baseline | 0 | n/a | 0.0% | -0.253 | n/a or marginal |
| unrelated_baseline | 0 | n/a | 0.0% | -0.230 | n/a or marginal |
| same_step_random_baseline | 0 | n/a | 0.0% | -0.016 | n/a or marginal |
| temporal_coactivation | 422 | H3_lifecycle | 74.4% | -0.022 | v109_strong_v110_weak |
| matched_baseline | 0 | n/a | 0.0% | -0.042 | n/a or marginal |
| attention_via_salience | 282 | H1_n_core | 48.2% | -0.019 | v109_strong_v110_weak |
| integration_alpha | 0 | n/a | 0.0% | -0.008 | n/a or marginal |
| integration_beta | 0 | n/a | 0.0% | -0.008 | n/a or marginal |
