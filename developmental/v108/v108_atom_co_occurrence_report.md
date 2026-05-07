# v10.8 Level 1: atom co-occurrence 報告

*作成*: 2026-05-07、Code A
*親*: `v108_implementation_brief.md` §5.2 Level 1
*基準*: `|baseline_excess_change| > 1%` かつ 24 seeds direction 一貫 (WLD.artless 除く)

---

## 0. 一文サマリ

24 集計対象 atom × 5 path × 18 delta field = 約 2,160 candidates のうち **1,384 集計、811 が Level 1 finding 達成** (37.5%)、最大 finding は **temporal_coactivation × medium window n_pulses で +15.6〜+15.8** (全 24 atom 24/24 direction 一貫)、atom 間で findings 数 31-41 (極めて均質、特定 atom が突出することなく)、ESDE は atom_introduction_event 後に target が medium window で平均 +15 events の追加 pulse を発火するという v10.7 と整合する共起観察。

---

## 1. 全体集計

| 指標 | 値 |
|---|---|
| Level 1 candidates | 1,384 |
| Level 1 findings | **811** (38%) |
| WLD.artless 留保 (集計外) | 100 events × 24 seeds、別記録 |

---

## 2. Top 15 Level 1 finding (overall_mean 大)

全部 **temporal_coactivation × mean_n_pulses_in_window_medium** で +15.6 ~ +15.8、direction 24/24 一貫:

| atom_id | overall_mean |
|---|---:|
| BOD.ear | 15.81 |
| COM.silence | 15.68 |
| COG.learn | 15.68 |
| FND.transformation | 15.68 |
| FND.timeless | 15.68 |
| PER.feel | 15.67 |
| EXS.nonbeing | 15.66 |
| EXS.being | 15.65 |
| PER.fragrance | 15.64 |
| TIM.appear | 15.64 |
| PER.hear | 15.64 |
| PER.see | 15.64 |
| SOC.city | 15.63 |
| WLD.technique | 15.62 |
| PER.soundless | 15.62 |

→ atom 種にほぼ依存せず、temporal_coactivation 経路で **medium window 内 +15 pulse 発火** が共通効果。

---

## 3. atom 別 findings 数 (top 15)

| atom_id | findings |
|---|---:|
| FND.timeless | 41 |
| EXS.nonbeing | 40 |
| WLD.culture | 39 |
| SOC.public | 39 |
| SOC.nation | 39 |
| PRP.deep | 38 |
| SOC.city | 37 |
| EXS.being | 35 |
| PER.feel | 35 |
| PER.hear | 34 |
| COM.silence | 34 |
| COG.learn | 34 |
| PER.taste | 33 |
| FND.transformation | 32 |
| WLD.technique | 32 |

→ 各 atom が 32-41 件の Level 1 finding (= 18 delta × 5 path = 90 候補のうち 35-46% で達成)。**特定 atom が突出することなく均質**。

---

## 4. 観察

### 4.1 Level 1 達成

24 集計対象 atom 全部で複数 finding 達成。**atom_introduction_event を入れた後、target cid で systematic に変化が観測される** という基本事実は確立。

### 4.2 v10.7 との比較

v10.7 (5 種 natural source_event):
- Level 1: 93 findings
- 主シグナル: temporal_coactivation × n_pulses_medium で +15.28

v10.8 (atom_introduction_event 追加):
- Level 1: 811 findings (約 9 倍、25 atom × ほぼ全 path × 全 delta field で達成)
- 主シグナル: 同 +15.6〜15.8 (v10.7 と同レベル)

→ **atom_introduction_event の波及プロファイルは v10.7 natural source_event と同等の共起強度**。Level 1 では atom と natural の差異は不明、Level 3.5 で詳細比較。

---

## 5. 出力

```
developmental/v108/outputs/main/cross_seed/
└── level_1_atom_co_occurrence.parquet
```

---

*Level 1 達成、Level 2 (path-enriched) と Level 3.5 (introduced vs natural) で詳細評価。*
