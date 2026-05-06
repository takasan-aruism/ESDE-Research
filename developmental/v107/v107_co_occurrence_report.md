# v10.7 Level 1: co-occurrence finding 報告

*作成*: 2026-05-07、Code A
*親*: `v107_implementation_brief.md` §7.1
*基準*: `|baseline_excess_change| > 1%` かつ 24 seeds direction 一貫

---

## 0. 一文サマリ

24 seeds × 5 source_event 種 × 10 relation_path/baseline で集計した baseline_excess_change のうち **111 candidates から 93 件が Level 1 finding 達成** (84%)、最大 finding は **temporal_coactivation の medium window 内 pulse 数 +15.28** (24/24 direction 一貫)、relation_paths は medium window で n_pulses / delta_n_observed / delta_n_alphas に大きな正の co-occurrence を示す。

---

## 1. 全体集計

| 指標 | 値 |
|---|---|
| 集計 candidates | 111 (10 path × delta_field 18 = 180、threshold で絞込) |
| Level 1 findings | **93** (基準: \|mean\| > 1% かつ direction 24/24 一貫) |
| 達成率 | 83.8% |
| direction-consistent (24/24) findings | 全 93 件 |

---

## 2. Top 20 Level 1 finding (overall_mean 大)

| relation_path_type | delta_field | overall_mean | direction |
|---|---|---:|---|
| temporal_coactivation | n_pulses_in_window_medium | **15.28** | 24/24 + |
| same_step_random_baseline | n_pulses_in_window_medium | 13.76 | 24/24 + |
| integration_beta | n_pulses_in_window_medium | 12.40 | 24/24 + |
| integration_alpha | n_pulses_in_window_medium | 11.97 | 24/24 + |
| **familiarity** | n_pulses_in_window_medium | **10.67** | 24/24 + |
| attention_via_salience | n_pulses_in_window_medium | 8.75 | 24/24 + |
| matched_baseline | n_pulses_in_window_medium | 6.83 | 24/24 + |
| same_integration_low_familiarity | n_pulses_in_window_medium | 6.80 | 24/24 + |
| temporal_coactivation | delta_n_observed_medium | 3.29 | 24/24 + |
| same_step_random_baseline | delta_n_observed_medium | 2.92 | 24/24 + |
| integration_beta | delta_n_observed_medium | 2.83 | 24/24 + |
| integration_alpha | delta_n_observed_medium | 2.71 | 24/24 + |
| familiarity | delta_n_observed_medium | 2.18 | 24/24 + |
| attention_via_salience | delta_n_observed_medium | 2.07 | 24/24 + |
| temporal_coactivation | delta_n_alphas_medium | 1.86 | 24/24 + |
| integration_beta | delta_n_alphas_medium | 1.75 | 24/24 + |
| temporal_coactivation | n_pulses_in_window_short | 1.68 | 24/24 + |
| integration_alpha | delta_n_alphas_medium | 1.67 | 24/24 + |
| same_step_random_baseline | delta_n_alphas_medium | 1.65 | 24/24 + |

---

## 3. 観察

### 3.1 medium window (100-1000 step) が最強の signal

- top 18 すべて medium window (immediate / short よりも明確な共起)
- **遅延型の波及が dominant** (Step F の wave_pattern peak_lag 250-300 と整合)

### 3.2 量別の出現順 (relation_path 内、最大値)

1. n_pulses_in_window_medium: 8.75-15.28 (**最大シグナル**)
2. delta_n_observed_medium: 2.07-3.29 (salience event 累積)
3. delta_n_alphas_medium: 0.80-1.86 (α 加入累積)
4. delta_C_medium: 0.10-1.03 (consciousness 累積、source-specific が強)

→ 「target cid が source_event 後に **追加 pulse を発火する**」現象が最大の共起 finding。これは ESDE の動学的な伝播の主成分。

### 3.3 path 間の比較 (medium n_pulses)

```
temporal_coactivation 15.28   ←最大 (時間近接 cid は最も追加 pulse)
integration (α + β)   12.4    ←強い (同 α/β 内は連動)
familiarity           10.67   ←中-強
attention_via_salience 8.75   ←中
─ baseline ─
same_step             13.76   ←temporal と相関 (= 同期する cid は近い時刻に動く)
matched_baseline      6.83    ←弱、relation 関係なしの構造的同等 cid
high_fam_out_integ    (top20 外、< 5)
unrelated_baseline    (top20 外)
```

→ **temporal_coactivation > Integration > familiarity > attention** の順で path-enriched 効果が大きい (Level 2 で詳細)。

---

## 4. Level 1 達成と次層への移行

Level 1 (co-occurrence) は全 path で達成。**source_event 後に target cid が状態変化する** という基本観察は確立。次に:

- **Level 2** (`v107_path_enriched_report.md`): relation_path 経由は unrelated_baseline よりどれだけ大きい変化を引き起こすか
- **Level 3** (`v107_source_specific_report.md`): source_event の種類 (pulse/ingestion/alpha/beta/consciousness) ごとに変化パターンが異なるか

---

*以上、Level 1 報告。全データ: `developmental/v107/outputs/main/cross_seed/level_1_co_occurrence.parquet`*
