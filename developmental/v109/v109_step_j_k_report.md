# v10.9 Step J + K 完了報告 — 統合 smoke + bit-identity 全層 + main run 判定要請

*作成*: 2026-05-08、Code A
*実装*: `developmental/v109/v109_post_process.py` (orchestrator)
*対象*: Web Claude / Taka (main run 進行判定)

---

## 0. 一文サマリ

`v109_post_process.py` orchestrator を実装、3 condition (A2/B3/C2) を 1 コマンドで atom_event_generator → baseline_recalculator → sensitivity_evaluator チェーン実行、seed 0 統合 smoke 46.3 秒で完了、**bit-identity 全層 (層 A/B/C) PASS** (層 A 全出力 MD5 一致 / 層 B v107 222 files + v108 368 files 完全不変 / 層 C 出力パス v109/ 配下強制)、**storage per seed 7.5 MB / 24 seeds 推定 179 MB (0.17 GB)** で Step B 推定 2.2 GB より大幅軽量、main 推定計算時間は **24 並列で 50-60 秒** (順次 18 分)、累計 storage v107 + v108 + v109 = 1.2 GB / 上限 6 GB (20%)、Step L (24 seeds main run) 進行許可を要請。

---

## 1. v109_post_process.py orchestrator 実装

### 1.1 構成

```
v109_post_process.py
  ├── Step C: atom_event_generator (3 conditions × 各 cid)
  ├── Step D/H: baseline_recalculator (3 conditions、build_baselines + delta + excess + global_activation)
  └── Step I: sensitivity_evaluator (per seed、A1 vs A2/B3/C2)

bit-identity 検証:
  ├── 層 A: seed 0 で 2 回目実行して MD5 完全一致
  ├── 層 B: v10.7/v10.8 main 出力の MD5 不変性 (590 files)
  └── 層 C: 出力パス v109/ 配下強制 (assert_output_under_v109)

multiprocessing.Pool で 24 seeds 並列対応 (24 seeds 単一バッチ厳守)
```

### 1.2 流用元

```python
from v109_atom_event_generator import (
    CONDITIONS, generate_seed_atom_events, safe_write_parquet_v109,
)
from v109_baseline_recalculator import recalculate_for_condition
from v109_sensitivity_evaluator import evaluate_seed as eval_sensitivity
```

→ 既存 v109 関数を直接 import、改変なし。

---

## 2. 統合 smoke 結果 (seed 0、A2 + B3 + C2)

```
v10.9 post-process orchestrator - mode=smoke, seeds=1,
                                  conditions=['A2', 'B3', 'C2']

=== bit-identity 層 B baseline MD5 取得 ===
  v107 main files tracked: 222
  v108 main files tracked: 368

=== 順次実行 ===
  seed= 0: t_atom=0.4s, t_baseline=45.74s, t_sens=0.17s,
           sens_rows=540, total=46.3s

=== bit-identity 層 A 検証 (seed 0 で 2 回目実行) ===
  PASS: 全出力が 2 回目で MD5 完全一致

=== bit-identity 層 B 検証 (v10.7/v10.8 main 不変性) ===
  PASS v107: 222 files 全て不変
  PASS v108: 368 files 全て不変

=== storage 実測 (seed 0 / smoke) ===
  atom_events:        0.254 MB
  baselines:          4.228 MB
  excess:             2.955 MB
  sensitivity:        0.028 MB
  TOTAL (per seed):   7.465 MB
  24 seeds 推定:        179 MB (0.17 GB)
```

### 2.1 計算時間内訳

| Step | 時間 |
|---|---:|
| atom_event_generator (3 cond) | 0.4 秒 |
| baseline_recalculator (3 cond) | 45.7 秒 |
| sensitivity_evaluator | 0.17 秒 |
| **per seed total** | **46.3 秒** |

**main run 推定**:
- 24 並列 (24 workers): **50-60 秒**
- 順次: 18 分
- (Step B 推定 16-20 分から大幅短縮)

### 2.2 storage 内訳

| カテゴリ | per seed (MB) | 24 seeds 推定 (MB) |
|---|---:|---:|
| atom_introduction_events × 3 cond | 0.254 | 6.1 |
| baselines_with_delta × 3 cond | 4.228 | 101.5 |
| excess_change_adjusted × 3 cond | 2.955 | 70.9 |
| sensitivity_evaluation | 0.028 | 0.7 |
| bimodal_analysis (Step E main、既存) | - | 0.6 (24 files) |
| **合計** | **7.465** | **179.8 MB** |

→ Step B 推定 2.2 GB より **12 倍軽量**。理由: atom events のみで baseline 再計算 (natural events 流用)、Step E bimodal は集計のみ。

### 2.3 累計 storage

| 区分 | サイズ |
|---|---:|
| v10.7 main outputs | 0.4 GB |
| v10.8 main outputs | 0.7 GB |
| v10.9 main outputs (推定) | 0.18 GB |
| **合計** | **1.28 GB** / 上限 6 GB (**21%**) |

→ 余裕大。

---

## 3. bit-identity 全層検証

### 3.1 層 A (再現性)

| 検証 | 結果 |
|---|---|
| seed 0 × 3 conditions × 3 種出力 (atom_event / baselines / excess) | **全 9 ファイル MD5 完全一致** ✓ |
| seed 0 sensitivity_evaluation | **MD5 完全一致** ✓ |

→ 同 seed 同条件で 2 回回しても完全再現。`np.random.default_rng(20250507)` 固定 (build_baselines)、`np.random.default_rng(1_090_000_300 + seed)` 固定 (B3 random)、cid_birth_lookup 決定論的 (C2)。

### 3.2 層 B (v10.7/v10.8 不変性)

| 区分 | 監視ファイル数 | 結果 |
|---|---:|---|
| v107 main outputs | 222 | **全 files 完全不変** ✓ |
| v108 main outputs | 368 | **全 files 完全不変** ✓ |
| 合計 | **590** | **全 PASS** ✓ |

→ v10.9 の post-process は v10.7/v10.8 出力に書き込まず、read のみ。物理層 frozen 厳守。

### 3.3 層 C (出力パス制限)

```python
def assert_output_under_v109(path):
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")
```

→ atom_event_generator / baseline_recalculator / sensitivity_evaluator / bimodal_analyzer 全モジュールで `safe_write_parquet_v109` を使用、`assert_output_under_v109` で強制チェック。v10.5/v10.6/v10.7/v10.8 への書き込み不可。

---

## 4. main run 進行判定要請 (Step K)

### 4.1 main run 計画

```
Step L: 24 seeds main run
  python3 v109_post_process.py --mode main --n_workers 24
  推定計算時間: 50-60 秒 (24 seeds 単一バッチ並列)
  推定 storage: 179 MB (0.17 GB)
  生成ファイル:
    - atom_introduction_events_{A2,B3,C2}_seed{0..23}.parquet (72 ファイル)
    - baselines_with_delta_{A2,B3,C2}_seed{0..23}.parquet (72 ファイル)
    - excess_change_adjusted_{A2,B3,C2}_seed{0..23}.parquet (72 ファイル)
    - sensitivity_evaluation_seed{0..23}.parquet (24 ファイル)
    - sensitivity_evaluation_all.parquet (cross-seed 集計)
    - post_process_run_summary.parquet
```

### 4.2 main run 後の Step M (cross-seed 解析 + 4 種設計表)

```
Step M: cross-seed 解析
  1. sensitivity_evaluation_all.parquet を 24 seeds 集計
     - QC_cost / cid_selection / timing 別の cohens_d を path × window で集計
     - mean, 95% CI, p_value (副)
  2. bimodal_analysis_all.parquet (Step F 既存) と統合解析
     - bimodal セルでの cid 群と sensitivity_evaluation の対応
  3. 4 階層 reports
     - Level 1: 機構動作確認
     - Level 2: 条件差確認
     - Level 3: 寄与候補感度評価
     - Level 3.5: 構造的説明候補整合
  4. 出口固定 4 種設計表
     - 表 1: sensitivity_summary (寄与候補別感度)
     - 表 2: receptivity_detection_criteria (Step F: cid age <= 500)
     - 表 3: input_routing_criteria
     - 表 4: natural_likeness_design_criteria

Step N: 完了報告 (v109_main_run_report.md)
```

### 4.3 main run 進行で確認すべき点

1. **24 seeds 単一バッチ厳守** (memory ルール: 3 バッチ分割禁止)
2. **24 並列実行** (multiprocessing.Pool 24 workers)
3. **smoke 後止まって報告** ルールは **Step J (本書) で完了**、Step L 進行は Web Claude / Taka 判定後
4. **bit-identity 層 A/B/C 全 PASS が前提** ← 既に達成
5. **storage 余裕 (累計 21%)**
6. **計算時間 50-60 秒推定** (smoke 46 秒 / seed × 24 並列)

### 4.4 Web Claude / Taka 判定要請

**Q1: main run 実行許可**
- smoke 全層 PASS、storage 余裕、計算時間問題なし
- 進行可で良いか?

**Q2: Step M cross-seed 解析の優先度**
- 4 種設計表のうち優先するものは?
- (Code A 推奨: 全 4 種同時生成、Step M で 1-2 時間)

**Q3: bimodal_analysis (Step E、既存) と sensitivity_evaluation の統合解析の方針**
- 単純に並べる vs 構造的に統合 (例: 高 delta cid と高 sensitivity 経路の対応)
- (Code A 推奨: まず統合、結果次第で並列に分離)

---

## 5. Step J + K 完了条件チェック

- [x] v109_post_process.py orchestrator 実装
- [x] 3 conditions (A2/B3/C2) を 1 コマンドで実行
- [x] atom_event_generator → baseline_recalculator → sensitivity_evaluator チェーン
- [x] multiprocessing.Pool 24 並列対応
- [x] bit-identity 層 A 検証 (seed 0 で 2 回目実行、全 MD5 一致 PASS)
- [x] bit-identity 層 B 検証 (v107 222 files + v108 368 files 完全不変 PASS)
- [x] bit-identity 層 C (出力パス v109/ 配下強制 PASS)
- [x] storage 実測 (per seed 7.465 MB、24 seeds 推定 179 MB)
- [x] main run 推定 (50-60 秒並列、累計 storage 21%)
- [x] Step L 進行判定要請の整理

---

## 6. 24 seeds 単一バッチ厳守宣言

memory ルール `feedback_24seeds_single_batch.md` に従い、Step L main run は:
- **1 つの `python3 v109_post_process.py --mode main --n_workers 24` コマンドで全 24 seeds 完了**
- 8/8/8 等のバッチ分割禁止
- 部分実行禁止

許可後即実行可能。

---

*以上、Code A による v10.9 Step J + K 完了報告。Web Claude / Taka からの Step L (24 seeds main run) 進行許可待ち。*
