# v9.16 Stage 3 — Step 5 Smoke Report

*作成: 2026-04-21、Code A*
*Describe only、結論を書かない*

---

## 1. 実行条件

| 項目 | 値 |
|---|---|
| コマンド | `python v916_memory_readout.py --seed 0 --maturation-windows 20 --tracking-windows 10 --window-steps 500 --tag smoke` |
| OMP/MKL/OpenBLAS threads | 1 |
| PYTHONHASHSEED | 0 |
| 作業ディレクトリ | `primitive/v916/` |
| 実行日時 | 2026-04-21 14:53–15:58 JST |
| Exit code (run1, run2) | 0, 0 |

指示書 §10.1 smoke コマンドに準拠。決定論性確認のため run1 / run2 の 2 回を並列実行。

---

## 2. 実行時間

| run | 実時間 (real) | user 時間 |
|---|---|---|
| v9.16 smoke run1 (timed) | 65m23.57s | 65m22.13s |
| v9.16 smoke run2 (parallel) | 65m16.84s | 65m15.37s |
| v9.15 段階 2 smoke (参考) | 65m26.86s | 65m24.84s |
| 差分 vs 段階 2 smoke | **-3.29s (-0.1%)** | -2.71s |
| Threshold (+15% = 4515.89s) | | |

指示書 §8.3 承認条件 #10「段階 2 smoke の +15% 以内」を満たす (実測 -0.1%、むしろ微減)。

---

## 3. Bit-identity Check (指示書 §9)

### 3.1 v9.14 baseline CSV 6 本 MD5 一致 (承認条件 #1)

比較対象: `primitive/v914/diag_v914_smoke/` と `primitive/v916/diag_v916_smoke/`

| ファイル | MD5 判定 |
|---|---|
| `aggregates/per_window_seed0.csv` | **OK** |
| `pulse/pulse_log_seed0.csv` | **OK** |
| `labels/per_label_seed0.csv` | **OK** |
| `audit/per_event_audit_seed0.csv` | **OK** |
| `audit/per_subject_audit_seed0.csv` | **OK** |
| `audit/run_level_audit_summary_seed0.csv` | **OK** |

Layer A / Layer B frozen を示す。

### 3.2 per_subject v9.14 列 = 段階 2 bit-identical (承認条件 #2)

`--ignore-prefix v915_` 相当の除外比較。

| 項目 | 値 |
|---|---|
| 比較対象 | `v915s2/diag_v915s2_smoke/subjects/per_subject_seed0.csv` vs `v916/diag_v916_smoke/subjects/per_subject_seed0.csv` |
| v9.14 列数 | 96 |
| 行数 | 46 |
| 差分 | **0 行** |

v9.14 既存の 96 列はすべて値まで完全一致。

### 3.3 v915_* 列構成 (承認条件 #3)

| 種別 | 列数 | 内訳 |
|---|---|---|
| 段階 2 継承 | 13 | fetch/mismatch 3 点セット + event 別カウント 9 列 + divergence |
| 段階 3 新規 | 7 | avg/min age_factor, total observed/missing/match_obs/mismatch_obs, final_missing_fraction |
| **合計** | **20** | |

指示書 §7.1 指定通り 20 列。欠損・余剰なし。

---

## 4. 段階 3 サンプリング挙動 Check (指示書 §8.3)

| 承認条件 | 結果 | 備考 |
|---|---|---|
| #4 age_factor ∈ [0, 1] | PASS | 全 324 行 |
| #5 0 ≤ n_observed ≤ n_core | PASS | 全 324 行 |
| #6 n_observed == round(n_core × age_factor) | PASS | 全 324 行で一致 |
| #7 total_missing が observation_log と整合 | PASS | 99 cids 全体で一致 |
| #8 match_obs + mismatch_obs == observed | PASS | 99 cids |
| #9 決定論性 (run1 vs run2 全 CSV MD5) | PASS | 20 CSV |
| #11 エラー/例外ゼロ | PASS | stderr クリーン |
| #12 observation_log サイズ | PASS | 324 rows (<= audit 324), サイズ約 34 KB |

**#12 補足**: observation_log 324 行 == per_event_audit 324 行。Layer B の E3_contact 両 cid 記録と Layer C の Fetch が 1:1 対応している (registry に未登録な cid は本 smoke では発生していない)。

---

## 5. Fetch 総数の段階 2 整合 (Taka 観察点 3)

| 項目 | v9.16 | v9.15 段階 2 |
|---|---|---|
| Σ fetch_count (per_cid_self 合算) | **324** | 324 |
| observation_log 行数 | 324 | — |
| per_event_audit 行数 | 324 | 324 |
| E1 event 数 (ledger audit) | 48 | 48 |
| E2 event 数 | 72 | 72 |
| E3 event 数 | 204 | 204 |

Fetch 総数は段階 2 と **1 単位も違わず完全一致**。event 駆動の継承が維持されていることを示す。

---

## 6. age_factor 推移 (Taka 観察点 1)

観察対象: 46 cid (smoke で fetch された cid、fetch 総数 324 event)。

### 6.1 cid 生涯での age_factor 最小値・最終値 (46 cid)

| 集計 | 初回観察時 age_factor | 最終観察時 age_factor |
|---|---|---|
| min | 0.727 | 0.273 |
| mean | 0.885 | 0.594 |
| max | 0.971 | 0.917 |

初回 event 時点で既に 73–97% の cid が残量 Q を持っており、最終 event 時点では 27–92% まで減少。全 cid で単調減少 (既消費分はゼロに戻らない)。

### 6.2 n_core 別の age_factor 分布 (全 324 event 観察)

| n_core | event 数 | age_factor min | mean | max |
|---|---|---|---|---|
| 2 | 152 | 0.273 | 0.721 | 0.917 |
| 3 | 31 | 0.421 | 0.750 | 0.947 |
| 4 | 14 | 0.720 | 0.840 | 0.960 |
| 5 | 127 | 0.333 | 0.763 | 0.971 |

`n_core=2` と `n_core=5` が支配的 (合わせて 279/324 = 86%)。

---

## 7. missing_flags の広がり (Taka 観察点 2)

| 集計 | 値 |
|---|---|
| registry に登録された cid | 99 |
| fetch >=1 回の cid | 46 |
| `total_missing_count > 0` の cid | **43** (fetched の 93.5%) |
| 全 fetch で完全失明だった cid | 0 |

43/46 (93.5%) の cid で、少なくとも 1 event 分の missing が発生。すなわち age_factor < 1.0 の状態で Fetch が起きた cid が大半。

---

## 8. node 状態の 3 値分布 (smoke 全体)

node-cell レベル (= fetch 回数 × n_core の合計) の集計:

| 状態 | cell 数 | 比率 |
|---|---|---|
| match | 0 | 0.0 % |
| mismatch | 838 | 77.0 % |
| missing | 250 | 23.0 % |

観察されたノードはすべて NODE_MATCH_TOLERANCE (1e-6) を超えて生誕時 theta と乖離している (smoke 5000 step で phase oscillator が動く間に全ノードが tolerance 以上動いたという事実)。missing は 23% で、サンプリング機構が機能している。

---

## 9. any_mismatch_ever

- `any_mismatch_ever = True` の cid: **46 / 46 fetched** (= 100%)
- `total_mismatch_obs_count > 0` の cid: 46 (上記と一致)

指示書 §13.3 の「`any_mismatch_ever = False` の cid が 1% より大きい → 報告」に抵触しない。

---

## 10. event 種別別 Fetch

observation_log からの集計:

| event | 行数 | mismatch_cell 合計 |
|---|---|---|
| E1 | 48 | 99 |
| E2 | 72 | 154 |
| E3 | 204 | 585 |
| 合計 | **324** | 838 |

E3_contact が全 event の約 63% を占めるのは段階 2 と同様。

---

## 11. 決定論性 (承認条件 #9)

run1 (`diag_v916_smoke`) と run2 (`diag_v916_smoke_run2`) の全 CSV 比較:

| 項目 | 値 |
|---|---|
| 比較 CSV ファイル数 | 20 |
| MD5 差分が出た CSV | 0 |

並列実行 (同一マシン、別プロセス) でも bit-identical。Layer C 独自 RNG が `engine.rng` から独立している証明になる。

---

## 12. 警告・注意点

- **`match = 0.0 %`**: smoke 5000 step で観察された node はすべて NODE_MATCH_TOLERANCE=1e-6 を超えて drift していた。指示書 §13 にこれを報告対象とする記述はないが、事実として記録する。本番 run (tracking 50 windows × 500 step = 25000 step) でも同傾向が続くと予想される。
- **`全 fetch で完全失明した cid = 0`**: smoke では age_factor=0 に到達する前に Fetch が終了した cid は無い。本番 run では age_factor=0 到達 cid が出現する可能性が高い。
- **`NaN / 例外`**: なし。

---

## 13. 生成ファイル (smoke run1)

```
diag_v916_smoke/
├── aggregates/per_window_seed0.csv       # v9.14 baseline, MD5 一致
├── pulse/pulse_log_seed0.csv             # v9.14 baseline, MD5 一致
├── labels/per_label_seed0.csv            # v9.14 baseline, MD5 一致
├── audit/
│   ├── per_event_audit_seed0.csv         # v9.14 baseline, MD5 一致 (324 rows)
│   ├── per_subject_audit_seed0.csv       # v9.14 baseline, MD5 一致 (46 rows)
│   └── run_level_audit_summary_seed0.csv # v9.14 baseline, MD5 一致 (4 rows)
├── subjects/per_subject_seed0.csv        # v9.14 96 列 bit-identical + v915_* 20 列
├── selfread/
│   ├── per_cid_self_seed0.csv            # 28 列 × 99 rows (段階 3)
│   ├── divergence_log_seed0.csv          # 11 列 × N rows
│   ├── observation_log_seed0.csv         # 11 列 × 324 rows (段階 3 新規)
│   └── class_divergence_seed0.csv        # 10 列 (段階 2 継承)
└── ... (他 pickup / representatives / network / introspection / persistence)
```

---

## 14. 指示書 §8.3 承認条件 12 項目サマリ

| # | 項目 | 結果 |
|---|---|---|
| 1 | v9.14 baseline 6 本 MD5 一致 | **PASS** |
| 2 | per_subject v9.14 96 列 bit-identical | **PASS** |
| 3 | v915_* 20 列の存在 | **PASS** |
| 4 | age_factor ∈ [0, 1] | **PASS** |
| 5 | 0 ≤ n_observed ≤ n_core | **PASS** |
| 6 | n_observed == round(n_core × age_factor) | **PASS** |
| 7 | missing_flags の cumulative 更新 / total_missing 整合 | **PASS** |
| 8 | match_obs + mismatch_obs == observed | **PASS** |
| 9 | 決定論 (2 回連続 run MD5 一致) | **PASS** |
| 10 | 実行時間 ≤ 段階 2 smoke × 1.15 | **PASS** (-0.1%) |
| 11 | エラー / 例外ゼロ | **PASS** |
| 12 | observation_log 行数 / サイズ健全 | **PASS** |

**12 / 12 PASS**。Step 6 本番 run への Taka 承認を待つ。

---

*以上、Step 5 smoke 観察報告。結論なし、観察事実のみ。*
