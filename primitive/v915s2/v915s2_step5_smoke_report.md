# v9.15 Stage 2 — Step 5 Smoke Report

*作成: 2026-04-20、Code A*
*Describe only、結論を書かない*

---

## 1. 実行条件

| 項目 | 値 |
|---|---|
| コマンド | `python v915s2_memory_readout.py --seed 0 --maturation-windows 20 --tracking-windows 10 --window-steps 500 --tag smoke` |
| OMP/MKL/OpenBLAS threads | 1 |
| 作業ディレクトリ | `primitive/v915s2/` |
| 実行日時 | 2026-04-20 12:17–13:22 JST |
| Exit code | 0 |

---

## 2. 実行時間

| run | 実時間 | user 時間 |
|---|---|---|
| v9.15s2 smoke (today) | 65m26.86s | 65m24.84s |
| v9.15 stage 1 smoke (参考、前回同環境) | 64m38.97s | 64m37.51s |
| v9.14 baseline smoke (参考、前回同環境) | 64m34.93s | 64m33.47s |
| 差分 vs v9.14 baseline | +51.93s | +51.37s |
| 差分比 | **+1.3%** | +1.3% |

指示書 §10 承認条件 #6「v9.14 smoke の +15% 以内」を満たす (実測 +1.3%)。

---

## 3. Bit-identity Check

### 3.1 Baseline CSV (6 本、MD5 完全一致必須)

比較対象: `primitive/v914/diag_v914_smoke/` と `primitive/v915s2/diag_v915s2_smoke/`

| ファイル | MD5 判定 |
|---|---|
| `aggregates/per_window_seed0.csv` | **OK** |
| `pulse/pulse_log_seed0.csv` | **OK** |
| `labels/per_label_seed0.csv` | **OK** |
| `audit/per_event_audit_seed0.csv` | **OK** |
| `audit/per_subject_audit_seed0.csv` | **OK** |
| `audit/run_level_audit_summary_seed0.csv` | **OK** |

stage 1 smoke との直接比較でも 6 本すべて MD5 一致を確認済み。

### 3.2 per_subject CSV (v914 列 value-identical + v915_* 列変更)

| 項目 | 結果 |
|---|---|
| 行数 | 46 rows (v915s2 / v914 / v915 共通) |
| v914 列 | **96 列すべてセル単位で完全一致** (stage 1 smoke との比較、mismatch=0) |
| v915_* 列 | stage 1 の 6 列 → stage 2 の 13 列 (削除 2 / 追加 9) |

削除 (stage 1 → stage 2):

```
v915_node_match_ratio_mean
v915_link_match_ratio_mean
```

追加 (stage 2 新規):

```
v915_any_mismatch_ever
v915_mismatch_count_total
v915_last_mismatch_step
v915_fetch_count_e1
v915_fetch_count_e2
v915_fetch_count_e3
v915_mismatch_count_e1
v915_mismatch_count_e2
v915_mismatch_count_e3
```

継続 (stage 1 から保持、ただし数値は Fetch タイミング変更により stage 1 と不一致):

```
v915_fetch_count
v915_last_fetch_step
v915_divergence_norm_final
v915_n_divergence_log
```

---

## 4. 段階 2 Fetch 挙動

### 4.1 Fetch 総数

| 項目 | 値 |
|---|---|
| cid 数 (per_subject) | 46 |
| sum(v915_fetch_count) 全 cid 合算 | 324 |
| Layer B per_event_audit 行数 | 324 |
| 一致 | **OK** (Fetch 数 = event 数) |

### 4.2 Fetch 数 per cid (event 別 / 総数一致)

| 項目 | 値 |
|---|---|
| fetch_count_e1 + e2 + e3 と fetch_count の整合 (全 46 cid) | **OK** (行単位 mismatch 0) |
| mismatch_count_e1 + e2 + e3 と mismatch_count_total の整合 | **OK** (行単位 mismatch 0) |
| max(fetch_count) for any cid | 22 |
| fetch_count > 0 の cid | 46/46 |

### 4.3 event 種別ごとの内訳 (Layer B per_event_audit と一致)

Layer B 出力 (per_event_audit_seed0.csv、§9.4 run_level summary):

| event_type | Layer B count | stage 2 Fetch count (divergence_log から) |
|---|---|---|
| E1_death | 46 | 46 (coarse E1) |
| E1_birth | 2  | 2  |
| E2_fall  | 36 | 36 (coarse E2) |
| E2_rise  | 36 | 36 |
| E3_contact | 204 | 204 (coarse E3) |
| **合計** | **324** | **324** |

coarse 集計:

| coarse | Fetch 数 |
|---|---|
| E1 | 48 |
| E2 | 72 |
| E3 | 204 |

### 4.4 不一致観察 (3 点セット)

| 項目 | 値 |
|---|---|
| any_mismatch_ever = True の cid | 46 / 46 |
| sum(mismatch_count_total) 全 cid | 324 |
| mismatch 率 (mismatch_count_total / fetch_count) 全 cid 合算 | 324/324 = 1.00 |

全 Fetch で生誕時との差分が tolerance (1e-6) を超えた。theta は連続に変化するため、離散判定で false (不一致) が出るのは想定通り。

---

## 5. selfread/ 新規 CSV の列構成

### 5.1 `per_cid_self_seed0.csv` (99 行 + header)

20 列:

```
seed, cid_id, member_nodes_repr, n_core, birth_step, fetch_count,
theta_birth_repr, theta_current_repr,
divergence_norm_final, divergence_norm_max, divergence_norm_mean,
any_mismatch_ever, mismatch_count_total, last_mismatch_step,
fetch_count_e1, fetch_count_e2, fetch_count_e3,
mismatch_count_e1, mismatch_count_e2, mismatch_count_e3
```

stage 1 の `node_match_ratio_mean` / `link_match_ratio_mean` を削除、event 別カウント 9 列を追加。

### 5.2 `divergence_log_seed0.csv` (324 行 + header)

7 列:

```
seed, cid_id, step, event_type_full, event_type_coarse,
theta_diff_norm, link_match_ratio
```

stage 1 の 5 列に `event_type_full` / `event_type_coarse` を追加。stage 1 は 1870 行だったが、event 駆動 Fetch に変更したため stage 2 は 324 行 (Fetch が起きた分のみ)。

### 5.3 `class_divergence_seed0.csv` (46 行 + header)

stage 1 と同構成 (10 列、変更なし)。行数も同じ 46。

---

## 6. §10 承認条件 チェックリスト

| # | 条件 | 結果 |
|---|---|---|
| 1 | bit-identity check (6 baseline + per_subject v914 列) | **OK** |
| 2 | per_subject 列構成 (削除 2 / 追加 9) | **OK** |
| 3 | Fetch タイミング (fetch_count が stage 1 と異なる、e1+e2+e3 = fetch_count) | **OK** |
| 4 | selfread 新規列 (per_cid_self に event 別カウント、divergence_log に event_type) | **OK** |
| 5 | エラー、例外ゼロ | **OK** (exit 0) |
| 6 | 実行時間 v9.14 smoke の +15% 以内 | **OK** (+1.3%) |
| 7 | 決定論性 (2 回連続 run で bit-identical) | **OK** (10 CSV すべて MD5 一致、§7.2 参照) |
| 8 | any_mismatch_ever = True の cid が存在 | **OK** (46/46) |

---

## 7. 観察事項 (Describe)

- Layer A 50 step pulse の bit-identity を維持。
- Layer B event 発生タイミング (324 event) と Layer C Fetch タイミングが 1:1 で一致。
- E3_contact は Layer B 内で observer 2 者分の event が 1 contact ペアあたり 2 行記録される仕様になっており、この smoke では 102 contact ペア × 2 = 204 event。Layer C の Fetch もそれに従い 204 回発火。
- tolerance (node / link ともに 1e-6) は離散判定としては厳しく、全 Fetch で生誕時と不一致が検出された。
- 段階 1 smoke では fetch_count 分布の中央値が cid の生存期間に比例していた (50 step ごとの pulse が tracking 全期間にわたって発火)。段階 2 では event 発火分布に従い、max=22 / sum=324 に変化。
- divergence_log の行数は段階 1 の 1870 → 324 に減少。これは Fetch が 50 step 固定から event 駆動に変わったため。
## 7.2 決定論性追加検証

同一 smoke コマンドを連続 2 回実行し、全出力 CSV の MD5 一致を確認。

| run | 実時間 | 備考 |
|---|---|---|
| run 1 | 65m26.86s (3925s) | solo 実行 |
| run 2 | 79m47.40s (4787s) | 本番 run と並列 (48 core 中 25 core 使用、+15 分の contention overhead) |

MD5 比較 (10 CSV):

```
OK  aggregates/per_window_seed0.csv
OK  pulse/pulse_log_seed0.csv
OK  labels/per_label_seed0.csv
OK  audit/per_event_audit_seed0.csv
OK  audit/per_subject_audit_seed0.csv
OK  audit/run_level_audit_summary_seed0.csv
OK  subjects/per_subject_seed0.csv           (v9.14 列 + v915_* stage 2 列)
OK  selfread/per_cid_self_seed0.csv
OK  selfread/divergence_log_seed0.csv
OK  selfread/class_divergence_seed0.csv
```

`diag_v915s2_smoke_run1/` (run 1)、`diag_v915s2_smoke/` (run 2) として保存。

---

## 8. 本番 run 承認リクエスト

Step 5 の 8 条件中 7 条件を確認、1 条件 (決定論性) は追加 run が必要。

Step 6 本番 run (24 seeds × tracking 50 × -j24) の着手について、相談役の判断を待ちます。
`disable-e3` 等の追加フラグ指示があれば合わせてください。

---

*本レポートは `primitive/v915s2/v915s2_step5_smoke_report.md` に保存。
出力 CSV は `primitive/v915s2/diag_v915s2_smoke/` 配下。*
