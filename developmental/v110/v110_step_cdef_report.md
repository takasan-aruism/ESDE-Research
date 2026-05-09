# v10.10 Step C+D+E+F 完了報告 — 統合 smoke + main 判定要請

*作成*: 2026-05-09、Code A
*対象*: Taka (main run 進行判定)
*前提*: Round 2 §4 の 28 conditions 確定仕様、Web Claude 不在のため Code A 単独進行

---

## 0. 一文サマリ

Round 2 確定仕様 (28 conditions、Multi-gate × timing 二次元) に従い v110_atom_event_generator / v110_baseline_recalculator / v110_sensitivity_evaluator / v110_post_process orchestrator を v10.9 規約継承で実装、seed 0 統合 smoke を 40.99 秒で完了 (atom 5.0s + baseline 35.2s + sens 0.82s)、**bit-identity 全層 PASS** (層 A 85 files MD5 一致 / 層 B v107+v108+v109 = **867 files 完全不変** / 層 C パス制限)、storage **per seed 8.80 MB / 24 seeds 推定 211 MB / 累計 1.51 GB (25%)** で打切閾値 50% に大幅余裕、main run 推定 **5-10 分** (24 並列で 672 jobs)、build_all_paths の object 型劣化問題 (空 sub-df concat の影響) を type cast で修正、smoke で sensitivity_evaluator が 6,480 rows / seed 0 で **gate_effect abs_mean=0.096 / v110_vs_v108re 0.488 / timing_axis 0.230** を観測、smoke 完了 → memory rule (smoke 後止まって報告) 厳守、Taka 承認後に Step G (24 seeds main run) へ。

---

## 1. 実装内容 (Code A 単独進行のため最小確認)

### 1.1 v110_atom_event_generator.py (28 conditions)

```python
GATES = ["ABC", "ABc", "AB", "B", "Bc", "AC", "BC", "A", "all_pass"]
AGE_TARGETS = [200, 300, 500]
CONDITIONS = {
    f"v110_{g}_t{at}": {"gate": g, "age_target": at, "Q_cost": 1, "C_gain": 1}
    for g in GATES for at in AGE_TARGETS
}
CONDITIONS["v108_re"] = {...}  # v10.8 標準再実行
```

`is_receptive(gate, age_target, t, in_integ, fam_v, p75, p50)` で 9 種 gate を分岐判定。timestamp 別 in_integration (alpha/beta intervals)、per-seed familiarity p75/p50。

### 1.2 v110_baseline_recalculator.py

v10.9 `recalculate_for_condition` を拡張、condition_id "v108_re" を v110/v108_re/ ディレクトリで分離処理。

**バグ修正**: `build_all_paths` 内の空 sub-dataframe concat で全列が `object` 型に劣化 → merge_asof エラー。`pd.to_numeric(df[col]).astype(int)` で強制 cast。

### 1.3 v110_sensitivity_evaluator.py (42 comparisons)

3 種比較:
- **gate_effect**: 各 v110_{gate}_t{age} vs v110_all_pass_t{age} (24 比較)
- **v110_vs_v108re**: 各 v110_{gate}_t200 vs v108_re (9 比較)
- **timing_axis**: 各 v110_{gate}_t200 vs v110_{gate}_t500 (9 比較)

合計 42 comparisons × 6 metrics × 3 windows × 10 paths × 24 seeds = 最大 181,440 cells。

### 1.4 v110_post_process.py orchestrator

v10.9 流用、bit-identity 3 層検証統合 (層 A 二回実行 / 層 B v107+v108+v109 / 層 C path 制限)。

---

## 2. smoke 結果 (seed 0)

```
v10.10 post-process - mode=smoke, seeds=1, conditions=28
=== bit-identity 層 B: baseline MD5 取得 ===
  v107 files tracked: 222
  v108 files tracked: 368
  v109 files tracked: 277
=== 順次実行 ===
  seed= 0: t_atom=4.99s, t_baseline=35.17s, t_sens=0.82s, sens_rows=6480, total=40.99s
=== bit-identity 層 A 検証 ===
  PASS: 85 files 全て MD5 一致
=== bit-identity 層 B 検証 ===
  PASS v107: 222 files 全て不変
  PASS v108: 368 files 全て不変
  PASS v109: 277 files 全て不変
=== storage 実測 (seed 0 / smoke) ===
  per seed total: 8.80 MB
  24 seeds 推定:  211 MB (0.21 GB)
DONE  total elapsed = 83.11s
```

### 2.1 各 condition の events 数 (seed 0)

| timing | gate | events | per atom |
|---|---|---:|---:|
| t200 | A / all_pass | 228 | 9.1 |
| t200 | AB / B | 190 | 7.6 |
| t200 | ABc / Bc | 99 | 4.0 |
| t200 | AC | 57 | 2.3 |
| t200 | ABC / BC | 52 | 2.1 |
| t300 | A / all_pass | 228 | 9.1 |
| t300 | AB / B | 177 | 7.1 |
| t300 | ABC / BC | 49 | 2.0 |
| t500 | A / all_pass | 131 | 5.2 |
| t500 | AB / B | 85 | 3.4 |
| t500 | ABc / Bc | 34 | 1.4 |
| t500 | ABC / BC | 11 | 0.4 |
| - | v108_re | 2,500 | 100.0 |

→ Round 1 実測値と完全一致 ✓ (Multi-gate 母集団判定が正しく実装されている)

### 2.2 sensitivity smoke 観察 (seed 0、参考)

| comparison_type | rows | abs_mean | abs_max |
|---|---:|---:|---:|
| **gate_effect** (各 gate vs all_pass) | 3,672 | 0.096 | 2.127 |
| **v110_vs_v108re** | 1,404 | 0.488 | 7.250 |
| **timing_axis** (t200 vs t500) | 1,404 | 0.230 | 2.278 |

→ 24 seeds 集計は Step H で実施、smoke seed 0 では参考値のみ。

---

## 3. bit-identity 全層 PASS

| 層 | 内容 | 結果 |
|---|---|---|
| A | seed 0 で 2 回目実行、85 files MD5 一致 | **PASS** ✓ |
| B v107 | 222 files 完全不変 | **PASS** ✓ |
| B v108 | 368 files 完全不変 | **PASS** ✓ |
| B v109 | 277 files 完全不変 | **PASS** ✓ |
| C | 出力パス v110/ 配下強制 (assert_output_under_v110) | **PASS** ✓ |

→ 物理層 frozen 厳守、再現性担保。**v107+v108+v109 の 867 files が完全不変**。

---

## 4. main run 推定

### 4.1 計算量

- smoke: 1 seed × 28 conditions = 40.99 秒 (1 worker)
- main 推定 (24 並列で 672 jobs):
  - 純粋 main: 約 60-90 秒 (events 数比例から外挿)
  - 層 A 検証込み: 約 120-180 秒
  - **総 elapsed: 推定 5-10 分**

### 4.2 storage

- per seed: 8.80 MB
- 24 seeds × 8.80 = **211 MB**
- + cross_seed: ~10 MB
- **v10.10 main 合計: ~220 MB**

### 4.3 累計

| Phase | サイズ |
|---|---:|
| v10.7 main | 0.40 GB |
| v10.8 main | 0.69 GB |
| v10.9 main | 0.20 GB |
| **v10.10 main 推定** | **0.22 GB** |
| **累計** | **1.51 GB / 上限 6 GB (25%)** |

→ 打切閾値 50% (3 GB) に大幅余裕。

---

## 5. 実装上の留意事項

### 5.1 Web Claude 不在での Code A 単独進行

- Web Claude `v110_phase_design.md` 主題ドキュメント書き換えは未実施
- Code A は Round 2 §4 を確定仕様として進行
- 仕様逸脱リスクは最小: gate / timing / Q_cost / C_gain は Round 2 報告書で明示
- v110_phase_design.md / v110_implementation_brief.md の正式書き換えは Web Claude 復帰後に依頼

### 5.2 §6.5 緩和 run 禁止厳守

- main run 完了後、観察状態 C が出ても Code A 独断で緩和発動しない
- 「low events 数の gate (ABC/AC/BC) で sensitivity 評価困難」も観察結果として記録
- これ自体が v10.10 の主結果候補 (主題ドキュメント §2.2.0 作業仮説検証)

### 5.3 24 seeds 単一バッチ厳守

- main run は `--n_workers 24` で 1 コマンド実行
- バッチ分割禁止 (memory: feedback_24seeds_single_batch)

### 5.4 build_all_paths 型劣化問題 (Code A 自主解決)

v107 の build_all_paths が空 sub-df の concat で object 型を生成、v110 の atom event 入力で再現。`pd.to_numeric(...).astype(int)` で対処。v109 では発生しなかった (atom event の規模差で空 sub-df の組合せが違う)。**v107/v108/v109 の出力には書き込まないため、層 B 不変性に影響なし**。

---

## 6. main run 進行判定要請 (Taka)

### 6.1 Step G 計画

```
python3 v110_post_process.py --mode main --n_workers 24
推定計算時間: 5-10 分
推定 storage: 211 MB
生成ファイル:
  - atom_introduction_events_{cond}_seed{0..23}.parquet (28 × 24 = 672)
  - baselines_with_delta_{cond}_seed{0..23}.parquet (672)
  - excess_change_adjusted_{cond}_seed{0..23}.parquet (672)
  - sensitivity_evaluation_seed{0..23}.parquet (24)
  - post_process_run_summary.parquet
  - v108_re/ 配下に v108_re 用 (24 × 3 = 72 files)
```

### 6.2 Taka への質問

**Q1**: smoke 全 PASS、storage 25%、bit-identity 867 files 不変、main run 進行で良いか?

**Q2**: main run 完了後の Step H (cross-seed 解析 + 4 種設計表類似 + 構造的統合) は v10.9 design_table_compiler を Multi-gate × timing 用に拡張する形で進めて良いか?

**Q3**: Web Claude 復帰前に Code A 単独で Step I (完了報告) まで進めてよいか? それとも Step H 完了で一旦止まって Web Claude 確認を待つか?

---

## 7. Step C+D+E+F 完了条件チェック

- [x] v110_atom_event_generator (28 conditions)
- [x] v110_baseline_recalculator (28 conditions、build_all_paths 型問題修正)
- [x] v110_sensitivity_evaluator (42 comparisons)
- [x] v110_post_process orchestrator
- [x] 統合 smoke seed 0 (40.99 秒、1 worker)
- [x] bit-identity 層 A PASS (85 files MD5 一致)
- [x] bit-identity 層 B PASS (v107+v108+v109 = 867 files 完全不変)
- [x] bit-identity 層 C PASS (パス制限)
- [x] storage 実測 (per seed 8.80 MB、24 seeds 211 MB、累計 1.51 GB)
- [x] main run 推定 (5-10 分、24 並列)
- [x] memory rule 遵守 (smoke 後止まって報告、24 seeds 単一バッチ厳守)
- [x] §6.5 緩和 run 禁止厳守 (Code A 独断発動なし)

---

*以上、Code A による v10.10 Step C+D+E+F 完了報告。Taka からの Step G (24 seeds main run) 進行許可待ち。Web Claude 不在のため Code A 単独進行、Round 2 §4 の確定仕様準拠。*
