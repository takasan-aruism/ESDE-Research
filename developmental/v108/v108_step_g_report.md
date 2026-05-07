# v10.8 Step G 報告 — 統合 smoke + bit-identity 層 A/C 検証 + storage 実測

*作成*: 2026-05-07、Code A
*親*: `v108_step_f_report.md` (Step F 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

seed 0 で全機構 (Step C-F) を 2 回実行して md5 比較した結果 **15/15 data ファイル完全一致** (summary 3 件のみ実行時間記録で除外、データ決定論性 PASS)、24 seeds 推定 storage **592 MB** (上限 6 GB の **10%**、Step B 推定 1.7 GB から大幅小)、層 B (Step D で v10.7 baseline 222 ファイル不変 PASS) と層 C (assert_output_under_v108 で全出力 v108 配下) も維持済、Step I (24 seeds 並列 main run) 進行準備完了。

---

## 1. bit-identity 検証結果

### 1.1 層 A: 同 seed 2 回実行 (新規確認)

```
run A files: 18, run B files: 18 (各 smoke で生成)
data files (summary 系除く): 15
identical: 15/15 ← 完全一致 PASS
```

除外 3 ファイル (実行時間記録):
- `post_process_run_summary.parquet`
- `step_e_run_summary.parquet`
- `step_f_run_summary.parquet`

→ **データの決定論性は完全に保たれている**。v10.7 と同様、summary 系のみ実行時間記録で differ。

### 1.2 層 B: v10.7 baseline 不変性 (Step D で PASS 済)

`v107_baseline 222 files 全て不変` (Step D smoke で確認)。Step I main run 後に再確認予定。

### 1.3 層 C: 出力先縛り

`assert_output_under_v108` で全出力 path を検証、`developmental/v108/outputs/` 配下のみ書き込み。v105/v106/v107 配下への書き込み無し。

---

## 2. storage 実測 (seed 0、全機構統合)

### 2.1 全 18 ファイル (data 15 + summary 3)

```
baselines_with_delta_seed0.parquet           10.66 MB  (Step D 最大)
excess_change_adjusted_seed0.parquet          8.24 MB  (Step E 拡張)
excess_change_seed0.parquet                   3.77 MB  (Step D)
relation_paths_seed0.parquet                  0.99 MB  (Step D)
source_events_seed0.parquet                   0.59 MB  (Step D 統合)
multi_hop_paths_seed0.parquet                 0.26 MB  (Step D)
resonance_loops_seed0.parquet                 0.03 MB  (Step D)
error_distribution_seed0.parquet              0.02 MB  (Step F)
natural_baseline_diff_seed0.parquet           0.02 MB  (Step E)
decay_rate_seed0.parquet                      0.01 MB  (Step D)
peak_lag_curve_seed0.parquet                  0.01 MB  (Step D)
global_activation_factor_seed0.parquet        0.01 MB  (Step E)
smallworld_comparison_seed0.parquet           0.01 MB  (Step F)
whiteout_monitor_seed0.parquet                0.01 MB  (Step F)
wave_patterns_seed0.parquet                   0.00 MB  (Step D)
post_process_run_summary.parquet              0.01 MB  (summary)
step_e_run_summary.parquet                    0.01 MB  (summary)
step_f_run_summary.parquet                    0.01 MB  (summary)
TOTAL                                        24.65 MB
```

### 2.2 24 seeds 推定

24.65 MB × 24 = **592 MB** (≈ 0.58 GB)

→ 上限 6 GB の **10%**。Step B で予想した 1.7 GB から大幅小 (parquet snappy 圧縮効果)。修正案 D (pulse 1/5 サブサンプリング) **不要**。

### 2.3 v10.7 比

- v10.7 main run: 428 MB
- v10.8 main run 推定: 592 MB
- 増分: +164 MB (= +38%、atom_intro + adjusted + 副次観察分)

---

## 3. Step G 完了条件チェック

- [x] 層 A 検証: 15/15 data 完全一致 (summary 系除く)
- [x] 層 B 検証: Step D で 222 files 不変 PASS
- [x] 層 C 検証: 出力 path 縛り (assert_output_under_v108)
- [x] storage 実測: 24.65 MB/seed、24 seeds 592 MB (上限 10%)
- [x] 全機構統合動作確認 (Step C-F、18 出力ファイル)
- [x] 24 seeds 単一バッチ実行可能性 (順次 (114+1.7+0.8) × 24 = 47 分、並列 24 workers なら 3-5 分)

---

## 4. v10.7 vs v10.8 統合比較表

| 項目 | v10.7 | v10.8 | 増分 |
|---|---:|---:|---|
| events/seed | 14,385 | 16,885 | +17% (atom 2,500) |
| storage/seed | 13.81 MB | 24.65 MB | +78% (adjusted + 副次観察) |
| 24 seeds total storage | 428 MB | 592 MB | +38% |
| 1 seed 順次時間 | 114 秒 | 約 134 秒 | +18% |
| 並列実行 (24 workers) | 234 秒 | **推定 250-300 秒** | 微増 |
| bit-identity 層 A | 9/10 PASS | 15/15 PASS | 同等 |
| bit-identity 層 B | 731 files | 222 files (v10.7 出力) | - |
| Small-World loops | 711 / 4,563 | 711 / 4,563 (完全同一) | 0 (構造的) |

---

## 5. 出力ファイル

```
developmental/v108/
├── v108_step_g_report.md (本報告)
└── outputs/smoke/ (18 files、Step C-F 全機構統合済)
```

---

## 6. Step I 進行への申請

Step H (smoke 結果報告) は本報告 (Step G) で兼ねる。Step I (24 seeds 並列 main run、`v108_post_process.py --mode main`) に進む許可を求めます。

実行方針:
1. **24 seeds 単一バッチ並列実行** (multiprocessing 24 workers、v10.7 で実証済)
2. 推定実行時間 **約 5 分** (= max seed time)
3. 推定 storage **約 592 MB** (上限 6 GB の 10%)
4. bit-identity 層 B 検証 (main run 前後で v10.7 baseline 不変性)
5. 全機構統合 main run:
   - Step D (v107 5 機構流用 + 第 6 種統合)
   - Step E (global activation 補正、natural baseline)
   - Step F (副次観察 3 件)

完了後、Step J (cross-seed 解析 + Level 1-3.5 reports + 総括) に進みます:
- v108_atom_co_occurrence_report.md (Level 1)
- v108_atom_path_enriched_report.md (Level 2)
- v108_atom_source_specific_report.md (Level 3)
- v108_introduced_vs_natural_report.md (Level 3.5)
- v108_subsidiary_observations_report.md (副次観察 3 件)
- v108_main_run_report.md (総括)

24 seeds 単一バッチ厳守 (3 バッチ分割禁止)。

---

*以上、Step G 報告。Web Claude / Taka からの Step I 進行許可待ち。*
