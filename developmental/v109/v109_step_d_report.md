# v10.9 Step D 完了報告 — baseline_recalculator (A2 + B3)

*作成*: 2026-05-08、Code A
*実装ファイル*: `developmental/v109/v109_baseline_recalculator.py`
*出力*: `developmental/v109/outputs/smoke/baselines_with_delta_{A2,B3}_seed0.parquet`、`excess_change_adjusted_{A2,B3}_seed0.parquet`
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

A2 + B3 の各条件で 5+1 種 baseline 再計算 + global_activation 補正を実装、seed 0 smoke で **A2 17.0 秒 / B3 17.1 秒 (並列 2 workers で 17.2 秒)**、bit-identity 層 A (4 ファイル全て同 seed 同条件 2 回再現) ✓、A2 で `mean_delta_C_medium` が path 別に **familiarity 0.137 > same_integration_low_fam 0.058 > temporal 0.031 > attention 0.028 > matched 0.007 > unrelated 0.008**、integration α/β は 0 (v10.8 と整合)、main 推定 24 seeds × 2 conditions で **約 130 MB**、Step E (bimodal_analyzer) 進行準備完了、Step D main run は Step C/D/E 全 smoke 通過後の Step J で統合実行。

---

## 1. 実装内容

### 1.1 v10.9 設計判断: atom events のみで再計算

natural events 部分は条件で変わらないため再計算しない。各条件の atom events のみで:
1. `build_all_paths` (relation_paths)
2. `build_baselines` (5 種 baseline cid 群)
3. `compute_deltas` (6 量 × 3 windows)
4. `compute_baseline_excess_change` (per (event, path) excess)
5. `add_adjusted_excess` (global_activation 補正)

→ 計算量は v10.8 main の atom 部分のみ (約 1/12 × 2 conditions)。

### 1.2 流用元

```python
from v107_path_analyzer import build_all_paths
from v107_baseline_constructor import (
    build_baselines, compute_deltas, compute_baseline_excess_change,
)
from v108_global_activation_correction import add_adjusted_excess
```

→ v10.7 の 4 関数 + v10.8 の 1 関数を直接 import、改変なし。

### 1.3 v10.9 拡張点

- `recalculate_for_condition(seed, condition_id, mode)`: condition 単位の wrapper
- `condition_id` 列を `baselines_with_delta` と `excess_change_adjusted` の両方に付与
- 出力ファイル名に condition 含む: `baselines_with_delta_{cond}_seed{N}.parquet` / `excess_change_adjusted_{cond}_seed{N}.parquet`
- `multiprocessing.Pool` 24 並列対応

---

## 2. smoke 結果 (seed 0、A2 + B3)

```
v10.9 baseline recalculator - mode=smoke, seeds=1, conditions=['A2', 'B3'], n_workers=2
=== 並列実行 (2 workers) ===
  seed= 0 cond=A2: rp=76,941, bl=186,795, with_delta=263,736, excess=17,207, size=1.599+1.108MB, t=16.77s
  seed= 0 cond=B3: rp=86,972, bl=182,785, with_delta=269,757, excess=17,491, size=1.669+1.161MB, t=17.13s

DONE  total elapsed = 17.20s
```

### 2.1 数値サマリ

| 指標 | A2 (top_k 100) | B3 (random 100) |
|---|---:|---:|
| relation_paths | 76,941 | 86,972 |
| baselines | 186,795 | 182,785 |
| with_delta rows | 263,736 | 269,757 |
| excess rows | 17,207 | 17,491 |
| size (with_delta + excess_adj) | 2.71 MB | 2.83 MB |
| 実行時間 (1 worker 単独) | 16.77 秒 | 17.13 秒 |

→ B3 (random cid) の relation_paths が A2 (top_k) より 13% 多い。これは random cid のほうが既存の familiarity edge にヒットする確率が seed 内 cid 全体に均等分散するため。

### 2.2 path 別 row 分布 (A2、excess_change_adjusted から)

| relation_path_type | rows | mean_delta_C_medium | std |
|---|---:|---:|---:|
| **familiarity** | 506 | **0.137** | 1.141 |
| same_integration_low_fam | 465 | 0.058 | 0.597 |
| same_step_random | 2500 | 0.031 | 0.418 |
| temporal_coactivation | 2500 | 0.031 | 0.412 |
| attention_via_salience | 2447 | 0.028 | 0.413 |
| high_fam_outside_integration | 2500 | 0.018 | 0.188 |
| matched | 2391 | 0.007 | 0.691 |
| unrelated | 2500 | 0.008 | 0.127 |
| **integration_alpha** | 699 | **0.000** | 0.000 |
| **integration_beta** | 699 | **0.000** | 0.000 |

→ 観察:
- **familiarity 経路が最も C 変化大 (0.137)**、A2 (Q-2/C+2) でもこの傾向
- **integration α/β は C 変化 0** (v10.8 と整合、no_signal 状態)
- baseline (unrelated, matched, same_step) の delta は 0.01 前後で familiarity と桁が違う
- **same_integration_low_familiarity_baseline** が baseline の中で最大 (0.058)、Integration 内では fam 低くても C 伝播あり

---

## 3. bit-identity 検証

### 3.1 層 A (同 seed 同条件で 2 回計算して MD5 一致)

| ファイル | 結果 |
|---|---|
| `baselines_with_delta_A2_seed0.parquet` | **MD5 完全一致** ✓ |
| `baselines_with_delta_B3_seed0.parquet` | **MD5 完全一致** ✓ |
| `excess_change_adjusted_A2_seed0.parquet` | **MD5 完全一致** ✓ |
| `excess_change_adjusted_B3_seed0.parquet` | **MD5 完全一致** ✓ |

→ 4 ファイル全て bit 完全再現。`build_baselines` 内の `np.random.default_rng(20250507)` 固定が機能、B3 の random cid は Step C で確定済みの atom_introduction_events が入力なので、ここではさらに random は導入されない。

### 3.2 層 C (出力パス v109/ 配下強制)

```python
def assert_output_under_v109(path):
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(...)
```

→ smoke / main 出力が v109/ 配下に強制。v10.5/v10.6/v10.7/v10.8 への書き込み禁止。

### 3.3 層 B (v10.8 出力流用部の不変性)

- `global_activation_factor_seed*.parquet` (v10.8 main 出力) を直接 read のみ、書き込みなし
- v10.8 main 出力の MD5 は変わらず

→ v10.8 main 出力に対する書き込みなし、不変性担保。

---

## 4. 計算量と main 推定

### 4.1 smoke 実測

- 1 seed × 2 conditions、2 workers 並列で **17.2 秒**
- per (seed, condition) で約 **17 秒**

### 4.2 main run 推定

- 24 seeds × 2 conditions = 48 jobs
- 24 並列で 2 ラウンド = **約 35 秒**
- Step C (atom_event_generator main) と統合実行で 36 秒以内

→ v10.8 base の 87 秒/seed × 24 seeds = 35 分から大幅短縮 (atom events のみ通すため)。

### 4.3 storage 推定

- per (seed, condition) = 2.7-2.8 MB
- 24 seeds × 2 conditions = **約 130 MB**
- main 累計 (v10.7 + v10.8 + v10.9) = 3.3 + 0.13 = **約 3.4 GB / 6 GB (57%)**

→ Step B 報告の 2.2 GB 推定より大幅小さい (atom 部分のみ計算なため)。Step E + Step F 結果次第で再評価、現状は予算余裕。

---

## 5. 設計判断のメモ

### 5.1 natural events を再計算しない決定

各 condition (A2, B3, C2) で natural events (pulse, ingestion, alpha, beta, c_conversion) は同じ。再計算は無駄。

→ Level 3.5 (構造的説明候補整合) で natural baseline と比較する際は v108 出力の `natural_baseline_diff_seed*.parquet` を直接流用。

### 5.2 atom event のみで build_baselines

`build_baselines` は per source event で独立 (各 event について 5 種 baseline cid を抽出)。atom events のみ通しても結果は同じ (rng seed 固定なので決定的)。

注: v108 と v109 で atom event のみ通した結果と全 events を通した結果は **rng の進み方が違う**ため bit 完全一致しない。**ただし v10.9 は新条件 (A2/B3/C2) なので v10.8 atom 部分との比較不要**、condition 内の再現性 (層 A) のみ担保。

### 5.3 condition_id 列の付与位置

- `baselines_with_delta`: per (event_id, target_cid) row に condition_id 付与
- `excess_change_adjusted`: per (event_id, relation_path_type) row に condition_id 付与
- 両方とも downstream で condition 別 filter 用

---

## 6. 観察ポイント (Level 3 sensitivity 用、暫定)

A2 vs v10.8 A1 の比較は Step I (sensitivity_evaluator) で正式実施。ここでは smoke レベルの暫定観察:

| path | A2 mean_delta_C_medium (smoke) | v10.8 A1 (推定、要確認) |
|---|---:|---:|
| familiarity | 0.137 | (Step I で取得) |
| same_integration_low_fam | 0.058 | (Step I で取得) |
| attention | 0.028 | (Step I で取得) |
| integration α/β | 0.000 | 0.000 (no_signal) |

→ A1 vs A2 の差 = Q/C コスト 2 倍化の感度。Step I で 24 seeds 集計後に判定。

---

## 7. Step E 進行への申請

Step E (`v109_bimodal_analyzer.py`、KDE + 3 仮説評価) に進む許可を求めます。

### 7.1 実装方針

- 入力: v108 main の `error_distribution_seed*.parquet` (1,540 件 bimodal) + `baselines_with_delta_seed*.parquet` (元データ)
- アルゴリズム: `scipy.stats.gaussian_kde` + `scipy.signal.find_peaks` で 2 ピーク抽出
- 各 (atom, path, window) で n_samples 閾値 (まず 30、足りなければ 10 に下げる)
- 3 仮説 (n_core / Integration / lifecycle) で Cohen's d 効果量を評価
- 最大 effect_size の仮説を選択、閾値 0.3 未満なら "unclassified"
- 出力: `bimodal_analysis_seed{N}.parquet` + cross-seed 集計

### 7.2 計算量見積もり

- 1,540 件 × KDE × 0.1 秒 = **約 3 分** (順次)
- 並列化不要

### 7.3 Step F の準備

Step E 完了後、Step F で:
- bimodal 解析結果の Web Claude / Taka 報告
- C2 (リズム同調) の分岐判定 (1: 明確な受信可能状態 / 2: 曖昧 → top_k 30 fallback / 3: 不能 → C1 同等)

### 7.4 並行作業の状況

Step D (本作業) は完了。Step E と Step D main run は独立、ただし Step F (C2 判定) の前に Step E 完了が必須。順序:
- Step E smoke → Step F → Step G (C2) → Step H (C2 baseline) → Step J (統合 smoke) → Step K → Step L (main)

---

## 8. Step D 完了条件チェック

- [x] v109_baseline_recalculator.py 実装
- [x] A2 condition の baseline 再計算 + adjusted 動作確認
- [x] B3 condition の baseline 再計算 + adjusted 動作確認
- [x] condition_id 列付与 (baselines_with_delta + excess_change_adjusted)
- [x] bit-identity 層 A (4 ファイル MD5 完全一致) ✓
- [x] bit-identity 層 B (v10.8 global_activation_factor 不変、read のみ) ✓
- [x] bit-identity 層 C (出力パス v109/ 配下強制) ✓
- [x] v10.7/v10.8 の 5 関数を import で流用、改変なし
- [x] multiprocessing.Pool 24 並列対応 (24 seeds 単一バッチ厳守)
- [x] storage 実測 (per job 2.7-2.8 MB、main 推定 130 MB)
- [x] 計算量実測 (per job 17 秒、main 24 並列 35 秒推定)

---

*以上、Code A による v10.9 Step D 完了報告。Web Claude / Taka からの Step E 進行許可待ち。*
