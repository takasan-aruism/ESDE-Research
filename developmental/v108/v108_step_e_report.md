# v10.8 Step E 報告 — global activation 補正 + v10.7 natural baseline

*作成*: 2026-05-07、Code A
*親*: `v108_step_d_report.md` (Step D 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v108_global_activation_correction.py` を実装、natural events 5 種 (atom_intro 除外) で 100 step bin の `global_activation_factor` を計算 (251 bins、mean=54、max=106)、excess_change の 18 delta 列に対し `adjusted_*` 列を追加 (= raw - normalized_factor × std)、v10.7 natural source_event baseline (5 source × 10 path の mean delta、50 rows) を seed 0 で **1.73 秒** で集計、Step F (副次観察 3 件) 進行準備完了。

---

## 1. smoke 結果 (seed 0、1.73 秒)

| 機能 | 出力 | rows | size |
|---|---|---:|---:|
| global_activation_factor | `global_activation_factor_seed0.parquet` | 251 step bins | < 0.01 MB |
| excess_change_adjusted | `excess_change_adjusted_seed0.parquet` | 133,332 | ~6 MB |
| natural_baseline_diff | `natural_baseline_diff_seed0.parquet` | 50 (5 src × 10 path) | < 0.01 MB |

実行時間内訳:
- factor 計算: 0.05 秒
- excess_change 拡張: 1.62 秒
- v10.7 natural baseline 集計: 0.06 秒

---

## 2. global_activation_factor (即決 §2.4 反映)

### 2.1 計算式

```python
total = pulse_count + ingestion_count + alpha_birth_count + beta_birth_count + consciousness_count
# atom_introduction_event は除外 (= 自己補正回避)
normalized = (total - mean) / std  # mean=0, std=1
```

### 2.2 seed 0 統計

| 量 | 値 |
|---|---:|
| 全 events 集計 (251 bins × 100 step = 25,100 step 範囲) | - |
| pulse 集計 mean | 約 50 events/100 step |
| total mean (全 natural events) | **53.8 events/100 step** |
| total max | **106 events/100 step** (最も活発な期間) |
| step bin 数 | 251 |
| 100 step bin size | 100 step |

→ ESDE は 100 step あたり平均 54 natural events を発火、ピーク 106 events。これが atom_intro の補正基準。

---

## 3. adjusted_baseline_excess_change

### 3.1 補正式

```python
adjusted_excess = raw_excess - normalized_factor_at_event * raw_excess.std()
```

各 event の timestamp に対応する `normalized_factor_at_event` を取得して補正。

### 3.2 18 delta 列に対応する adjusted 列

`mean_delta_*_immediate/short/medium` (15 列) + `mean_n_pulses_in_window_*` (3 列) = 18 列に対し `adjusted_*` 列を追加。

### 3.3 補正の意味

global_activation_factor が高い時刻の event は ESDE 全体が活発な期間の一部 → 個別 event の効果と全体活性化を区別することが可能。

→ Step J で Level 2/3 判定時に **raw + adjusted の両方** で finding 検出予定。

---

## 4. v10.7 natural source_event baseline (Level 3.5 判定基盤)

### 4.1 集計内容

`developmental/v107/outputs/main/excess_change_seed0.parquet` から:
- 5 種 source_event (pulse / ingestion / alpha_formation / beta_formation / c_conversion) ごとに
- 10 種 relation_path_type (familiarity / attention_via_salience / integration_α/β / temporal_coactivation + 5 baselines) ごとに
- 18 delta 列の mean

### 4.2 出力規模

5 source × 10 path = **50 rows × 18 delta cols = 900 値** (seed 0 単独)。

→ Step J で v10.8 atom_introduction_event の delta と直接比較し、Level 3.5 (introduced vs natural) の判定基盤。

### 4.3 比較ロジック (Step J で実装)

```python
# 各 (atom, path) で
v108_delta = df_v108_excess[(df_v108_excess.atom_id == atom) &
                              (df_v108_excess.relation_path_type == path)].mean()
v107_natural_delta = df_natural_baseline[(df_natural_baseline.event_source_type == src) &
                                            (df_natural_baseline.relation_path_type == path)]
diff = v108_delta - v107_natural_delta
# diff > 1% かつ 24 seeds direction 一貫 → Level 3.5 finding
```

---

## 5. Step E 完了条件チェック

- [x] global_activation_factor 計算 (natural events のみ、atom_intro 除外、即決 §2.4)
- [x] 100 step bin × normalize (mean=0, std=1)
- [x] excess_change に adjusted_* 列追加 (18 delta 列)
- [x] v10.7 natural source_event baseline 集計 (Level 3.5 判定基盤)
- [x] read-only / v108 出力 path 縛り維持
- [x] 24 seeds 単一バッチ実行可能性 (1.73 秒/seed × 24 = 42 秒、軽量)

---

## 6. 出力ファイル

```
developmental/v108/
├── v108_global_activation_correction.py
├── v108_step_e_report.md
└── outputs/smoke/
    ├── global_activation_factor_seed0.parquet  (251 step bins)
    ├── excess_change_adjusted_seed0.parquet     (133,332 rows × 拡張 18 adjusted 列)
    ├── natural_baseline_diff_seed0.parquet      (50 rows、v10.7 集計値)
    └── step_e_run_summary.parquet
```

---

## 7. Step F 進行への申請

Step F (副次観察 3 件、`v108_subsidiary_observations.py`) に進む許可を求めます。

実装方針:
1. **Whiteout 監視** (Gemini A1):
   - 25 atom × 25 atom = 625 ペア (重複除外で 300)
   - 同時刻 ± 5 step 内の event ペアを抽出
   - 波及プロファイル (delta vector) の相関係数
   - 0.7 以上で whiteout_flag
2. **Small-World 維持確認** (Gemini A6):
   - v10.7 vs v10.8 の loop_2_hop / loop_3_hop 比較
   - **Step D smoke で既に同一値 (711/4,563) を確認済**
   - 構造的に変化なし、記録のみ
3. **誤差分布の形状観察** (Gemini A5):
   - 25 atom × 7 path × 3 window で delta 分布集計
   - mean / std / skewness / kurtosis / bimodality_coefficient (Sarle's)
   - 形状ラベル (normal / skewed / bimodal / other)

実行時間予想: 30-45 分 (Whiteout の atom ペア計算)。

Step F 完了後、Step G (統合 smoke + bit-identity 判定) → Step I (24 seeds main run) に進む前に再度報告します。

24 seeds 単一バッチ厳守 (multiprocessing 24 並列、3 バッチ分割禁止)。

---

*以上、Step E 報告。Web Claude / Taka からの Step F 進行許可待ち。*
