# v9.15 Step 5 — Smoke Report

*Code A から相談役 Claude への報告、2026-04-20*

## 1. 実行条件

| 項目 | 値 |
|---|---|
| コマンド | `python v915_memory_readout.py --seed 0 --maturation-windows 20 --tracking-windows 10 --window-steps 500 --tag smoke` |
| CLI flag | `--disable-e3` なし (default) |
| 実行環境 | `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1` |
| 出力先 | `primitive/v915/diag_v915_smoke/` |
| 比較 baseline | `primitive/v914/diag_v914_step5baseline/` (v9.14 fresh repro、同パラメータ) |

## 2. 実行時間

| run | 実時間 | user 時間 |
|---|---|---|
| v9.15 smoke | 64m38.97s | 64m37.51s |
| v9.14 baseline | 64m34.93s | 64m33.47s |
| 差分 | +4.04s (+0.1%) | +4.04s |

指示書基準の **+15% 以内** を満たす (実測 +0.1%)。
※ 両 run を並列実行した CPU 競合込みの値。単独実行なら両方 30-40 分程度と推定。

## 3. Bit-identity Check

### 3.1 Baseline CSV (6 本、MD5 完全一致必須)

| ファイル | 判定 |
|---|---|
| `aggregates/per_window_seed0.csv` | **OK** |
| `pulse/pulse_log_seed0.csv` | **OK** |
| `labels/per_label_seed0.csv` | **OK** |
| `audit/per_event_audit_seed0.csv` | **OK** |
| `audit/per_subject_audit_seed0.csv` | **OK** |
| `audit/run_level_audit_summary_seed0.csv` | **OK** |

### 3.2 per_subject CSV (v914 列 value-identical + v915_* 列追加)

| 項目 | 結果 |
|---|---|
| 行数 | 46 rows (v914 / v915 共通) |
| v9.14 既存列 (96 cols) | **全値一致** |
| 列順 (v914 列は先頭、v915_* は末尾) | 保持 |
| v915_* 列数 | 6 (v915_fetch_count / v915_last_fetch_step / v915_node_match_ratio_mean / v915_link_match_ratio_mean / v915_divergence_norm_final / v915_n_divergence_log) |
| 非 v9.14・非 v915_* の列 | 0 |

## 4. v9.15 新規出力 (selfread/)

### 4.1 ファイル概要

| ファイル | 行数 | 列数 |
|---|---|---|
| `selfread/per_cid_self_seed0.csv` | 99 | 13 |
| `selfread/divergence_log_seed0.csv` | 1870 | 5 |
| `selfread/class_divergence_seed0.csv` | 46 | 10 |

### 4.2 Fetch カウント分布 (per_cid_self)

`fetch_count` 分布 (cid 数):

| fetch_count | cid 数 | 備考 |
|---:|---:|---|
| 0 | 53 | 登録のみ、Fetch 未到達 (maturation 中に reap された等) |
| 10 | 19 | 約 10 pulse = tracking 途中で host_lost |
| 20 | 5 |  |
| 30 | 6 |  |
| 40 | 2 |  |
| 60 | 1 |  |
| 70 | 1 |  |
| 90 | 1 |  |
| 100 | 11 | tracking 全期間 hosted の cid (理論値) |
| **max** | **100** | 理論値 `tracking_windows × window_steps / PULSE_INTERVAL = 10 × 500 / 50 = 100` と一致 |

### 4.3 n_core 分布 (Fetch された cid に限らず登録全体)

| n_core | cid 数 |
|---:|---:|
| 2 | 77 |
| 3 | 7 |
| 4 | 2 |
| 5 | 13 |

### 4.4 Self-Divergence (最終時点、fetched cid のみ)

| 指標 | 値 |
|---|---:|
| `divergence_norm_final` (mean) | 4.021 |
| `divergence_norm_final` (max) | 7.533 |
| `divergence_log` 総エントリ | 1870 |

### 4.5 Class Divergence (同クラスペア)

| 指標 | 値 |
|---|---:|
| 計算されたペア総数 | 46 |
| 参加クラス数 (n_core × phase_bucket ユニーク) | 10 |
| クラス内最大ペア数 | 10 (指示書上限と一致) |
| ペア別 `divergence_final` (mean) | 3.407 |
| ペア別 `divergence_final` (max) | 7.701 |

## 5. エラー・例外

- v9.15 smoke run: exit code 0、Traceback 無し
- v9.14 baseline: exit code 0、Traceback 無し

## 6. 承認条件チェックリスト (指示書 §8.2 Step 5)

| 条件 | 結果 |
|---|---|
| bit-identity check | **全 OK** (6 baseline + per_subject v914 列) |
| 1 cid あたり期待回数 Fetch (tracking 10 × 10 pulse = 100) | **OK** (max fetch_count = 100) |
| エラー・例外ゼロ | **OK** |
| 実行時間 v9.14 smoke の +15% 以内 | **OK** (+0.1%) |

## 7. 決定論性 (追記: Step 4 smoke で検証済み)

- Step 4 smoke の 2 回連続 run で selfread/ 3 CSV が完全 bit-identical
- class_divergence のサンプリング RNG は Python hash randomization 非依存 (seed × 997 + n_core × 131 + bucket × 31 の明示 mix)

## 8. 相談役へのエスカレーション

本 smoke レポートの内容で Step 5 承認条件を満たしたと判断します。
Step 6 (本番 24 seeds × tracking 50 × -j24 並列、指示書 §10.2) への進行は、
相談役の明示的な承認を待ちます。

---

*以上、Step 5 smoke 報告書。承認で Step 6 本番開始。*
