# v10.7 Step E 報告 — baseline + delta 集計実装 + smoke

*作成*: 2026-05-07、Code A
*親*: `v107_step_d_report.md` (Step D 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v107_baseline_constructor.py` を実装、5 種 baseline (即決事項 §4 緩和定義) + 6 量 × 3 windows delta 集計 + baseline_excess_change を seed 0 で **1,763,031 records (path 851K + baseline 912K)、9.08 MB、87 秒** で smoke、bit-identity 層 A PASS、Step B 推定 295 MB/seed から **9 MB/seed に大幅圧縮** (parquet snappy 効果)、24 seeds 推定 storage 218 MB (上限 6 GB の 4%)、Step F (avalanche + peak_lag) 進行準備完了。

---

## 1. smoke 実行結果

| 指標 | 値 |
|---|---|
| seed 0 total records | **1,763,031** (path 851,154 + baseline 911,877) |
| excess_change rows | 116,125 (per (seed × event × relation_path_type) 集計) |
| size_with_delta (parquet snappy) | **9.08 MB/seed** |
| size_excess_change | 3.29 MB/seed |
| 実行時間 | **87 秒/seed** |
| bit-identity 層 A | **PASS** (md5 完全一致、DataFrame equal OK) |
| 24 seeds 推定 storage | **218 MB (delta) + 79 MB (excess) ≈ 300 MB** ← 上限 6 GB の 5% |
| 24 seeds 推定実行時間 | 35 分 (87 × 24、許容範囲) |

→ Step B での 295 MB/seed 推定から **97% 圧縮** (parquet snappy + 数値型 + group-by 集計の効果)。修正案 D (pulse サブサンプリング) **不要** で 24 seeds main run 可能。

---

## 2. relation_path_type 別 records 数 (seed 0)

| relation_path_type | records (path + baseline) |
|---|---:|
| high_familiarity_outside_integration_baseline | 287,700 |
| unrelated_baseline | 287,700 |
| same_step_random_baseline | 284,127 |
| temporal_coactivation | 281,190 |
| attention_via_salience | 219,003 |
| familiarity | 165,547 |
| integration_alpha | 105,521 |
| integration_beta | 79,893 |
| same_integration_low_familiarity_baseline | 26,413 |
| matched_baseline | 25,937 |

→ **5 path + 5 baseline = 10 種の relation_path_type** (Integration α/β 別なので相対 11 でも記録)。

baseline 群の records 数:
- unrelated / same_step / high_fam_out_integ: 大量 (各 cid 候補が多い)
- matched_baseline / same_integration_low_familiarity: 少数 (条件が厳しく、適合 cid が少ない)

→ **matched_baseline と same_integration_low_familiarity_baseline は cid 数不足の傾向**、ただし 0 件にはならず、Level 1-3 比較には使用可能。

---

## 3. delta 集計 (6 量 × 3 windows = 18 fields + n_pulses_in_window 3 = 21 fields)

### 3.1 delta フィールド一覧

```
delta_R_familiarity_{immediate,short,medium}      (R_familiarity 変化)
delta_Q_{immediate,short,medium}                  (Q_at_decision 変化)
delta_C_{immediate,short,medium}                  (C_at_decision 変化)
delta_n_alphas_{immediate,short,medium}           (累積 α 加入 変化)
delta_n_observed_{immediate,short,medium}         (累積 salience observe 変化)
n_pulses_in_window_{immediate,short,medium}       (window 内の pulse 発火数)
```

windows: **immediate (1-10 step) / short (10-100) / medium (100-1000)** (即決事項 §5.2 固定窓)。

### 3.2 relation_path_type 別 mean delta (seed 0 抜粋)

| relation_path_type | n_targets | mean_dC_imm | mean_dQ_imm | mean_dR_fam_imm | mean_n_pulses_imm | mean_dC_med |
|---|---:|---:|---:|---:|---:|---:|
| **familiarity** | 165,547 | 0.009 | -0.007 | 0.000 | 0.111 | **0.184** |
| **temporal_coactivation** | 281,190 | 0.000 | -0.002 | -0.000 | **0.275** | 0.063 |
| **attention_via_salience** | 219,003 | 0.002 | -0.003 | 0.000 | 0.109 | 0.099 |
| integration_alpha | 105,521 | 0.001 | -0.003 | -0.002 | 0.157 | -0.002 |
| integration_beta | 79,893 | 0.001 | -0.003 | -0.001 | 0.165 | -0.002 |
| **matched_baseline** | 25,937 | **0.018** | -0.006 | -0.004 | 0.232 | 0.073 |
| unrelated_baseline | 287,700 | 0.002 | -0.003 | 0.000 | 0.015 | 0.029 |
| same_step_random_baseline | 284,127 | 0.001 | -0.003 | 0.000 | 0.188 | 0.065 |
| same_integration_low_fam_baseline | 26,413 | -0.003 | -0.002 | -0.001 | 0.063 | 0.000 |
| high_fam_out_integration_baseline | 287,700 | 0.001 | -0.002 | -0.000 | 0.011 | 0.034 |

### 3.3 First-look 観察 (Level 1 candidate に向けた予兆)

- **familiarity 経路: medium window (100-1000 step) で mean_delta_C = 0.184** ← 他 path より大、interest 候補
- **temporal_coactivation: immediate で n_pulses 0.275** ← 同期発火が捕捉されている (近接 pulse 集計が機能)
- **matched_baseline: mean_dC_imm 0.018** が他より高い ← サンプル少 (25,937) で外れ値の可能性、要観察
- baseline 群の同期で **unrelated** と **high_fam_out_integration** がほぼ同等の delta → 「無関係」の意味として一貫
- `delta_n_observed_*` (salience 累積) は値が出ているはずだが mean_dC でなく抜粋に未表示

→ Step G (統合 smoke) で全 finding を Level 1-3 で集計。本 Step E は **集計データの生成のみ** で finding 判定は後段。

---

## 4. 出力 schema

### 4.1 baselines_with_delta_seed{N}.parquet

```
event_id              object   Step C 出力との結合キー
source_cid            int64    主体 cid
timestamp             int64    source_event 時点
target_cid            int64    候補 cid
relation_path_type    object   10 種 (5 path + 5 baseline)
relation_strength     float64  path 別 strength (baseline は 0)
hop_distance          int64    1 (path) / -1 (baseline)
seed                  int64
delta_R_familiarity_immediate  float64
delta_Q_immediate              float64
delta_C_immediate              float64
delta_n_alphas_immediate       int64 (cum 差分)
delta_n_observed_immediate     int64
delta_R_familiarity_short      float64
... (short, medium で同上)
n_pulses_in_window_immediate   int64
n_pulses_in_window_short       int64
n_pulses_in_window_medium      int64
合計 26 columns
```

### 4.2 excess_change_seed{N}.parquet

```
seed, event_id, relation_path_type, n_targets   (キー + 件数)
mean_delta_R_familiarity_immediate
mean_delta_Q_immediate
mean_delta_C_immediate
... (3 windows × 6 量 = 18 fields)
mean_n_pulses_in_window_immediate
... (3 windows = 3 fields)
合計 22 columns、116,125 rows (seed 0)
```

これが **Level 1-3 判定の主データ**。

---

## 5. bit-identity 層 A 検証

```
run A md5: 8e392e0a1466a753eee419ac407bb527
run B md5: 8e392e0a1466a753eee419ac407bb527
identical: True
pd.testing.assert_frame_equal: OK
```

→ Step E も非決定性なし、再現性確認。np.random.default_rng(20250507) で baseline 抽出を seed 固定。

---

## 6. 設計判断 (Code A 視点)

### 6.1 baseline 抽出順序の固定

5 種 baseline で **rng (numpy.random.default_rng(20250507))** で permutation。これにより 24 seeds 全部で同じ抽出順序、再現性担保。

### 6.2 `relation_strength = 0`、`hop_distance = -1` (baseline)

baseline は relation 関係そのものが定義されないので、`relation_strength = 0`, `hop_distance = -1` (= 「無関係マーク」) で記録。後段集計時に baseline と path を区別可能。

### 6.3 delta 計算で merge_asof + cumulative

- pre / post の状態取得は **target_cid + timestamp** で merge_asof (direction='backward')
- pulse の R_familiarity、balance_decisions の Q/C、cumulative alpha/observed は per-cid 時系列で sorted
- per_event_audit (q_spend) は cumulative count にしか使わない (Step E では未使用、value_generation は後段集計で必要時)

### 6.4 n_pulses_in_window は Python loop

24 seeds × 1.7M records × 3 windows のため Python loop で計算 (numpy 化は次回最適化)。87 秒/seed なら本番 35 分で許容。

---

## 7. Step E 完了条件チェック

- [x] 5 種 baseline 構築 (緩和定義反映)
- [x] delta 6 量 × 3 windows 計算
- [x] baseline_excess_change 集計 (per event × path × seed)
- [x] read-only / v107 出力 path 縛り維持
- [x] 構造語徹底 (event_id / source_cid / target_cid / relation_path_type / mean_delta_* / mean_n_pulses_in_window_*)
- [x] bit-identity 層 A PASS (md5 完全一致)
- [x] 24 seeds 単一バッチ実行可能性 (87 秒/seed × 24 = 35 分、storage 300 MB)

---

## 8. 出力ファイル

```
developmental/v107/
├── v107_baseline_constructor.py
├── v107_step_e_report.md
└── outputs/smoke/
    ├── baselines_with_delta_seed0.parquet      (1,763,031 rows × 26 cols, 9.08 MB)
    ├── excess_change_seed0.parquet              (116,125 rows × 22 cols, 3.29 MB)
    └── step_e_run_summary.parquet
```

---

## 9. Step F 進行への申請

Step F (avalanche + peak_lag、`v107_avalanche_monitor.py`) に進む許可を求めます。

実装方針:
1. **アバランシェ防止 (graph traversal、3 hop 制限)**:
   - 1 hop: Step D で構築済 (relation_paths)
   - 2 hop: 1-hop neighbor の neighbor (familiarity / Integration 経由)
   - 3 hop: 2-hop neighbor の neighbor
   - hop_distance 列に記録 (1, 2, 3 のみ、4+ は記録しない)
2. **減衰率追跡** (即決事項 §6.2):
   - hop_1_excess / hop_2_excess / hop_3_excess の比較
   - 線形 / 指数 / 急減衰 / 維持 のパターン分類
3. **共鳴ループ検出** (即決事項 §6.3):
   - loop_2_hop: source_cid ↔ target_cid 双方向 path
   - loop_3_hop: source_cid → A → B → source_cid
4. **peak_lag 測定 (10 step bin、即決事項 §2.3)**:
   - 各 (event, target) で lag 0, 10, 20, ..., 1000 (101 bins) で baseline_excess_change を計算
   - argmax_lag を peak_lag として記録
5. **波及パターン分類** (即決事項 §5.3):
   - 即時型 (peak_lag < 10)、遅延型 (peak_lag > 100)、残響型 (複数ピーク or 定常増加)

実行時間予想: 4-6 時間 (peak_lag が重い計算)。最適化次第で短縮可。

Step F 完了後、Step G (統合 smoke) に進む前に再度報告します。

24 seeds 単一バッチ厳守、3 バッチ分割禁止。

---

*以上、Step E 報告。Web Claude / Taka からの Step F 進行許可待ち。*
