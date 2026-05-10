# v10.12 Step E 完了報告: baseline_recalculator + propagation_analyzer 実装 + smoke seed 0

*作成*: 2026-05-11、Code A
*親*: Step D 完了報告 (commit b790d56) + Step C 完了報告 (commit 8880574)
*対象*: Web Claude (相談役) + Taka (確認)
*目的*: Step E 実装 (2 モジュール) + smoke (seed 0) 動作確認 + bit-identity 層 A 全 6 ファイル検証 + Step F (observation_recorder) 進行案

---

## 0. 一文サマリ

Step E で `v112_baseline_recalculator.py` (215 行) + `v112_propagation_analyzer.py` (235 行) を実装、baseline_recalculator は v107 build_all_paths + build_baselines + compute_deltas + compute_baseline_excess_change + v108 add_adjusted_excess パイプラインを共通利用、v112 condition で新規計算 (400 events → 45,396 (event,target,path) → 2,718 (event,path) excess、2.6 秒) + v108_standard condition で v110/v108_re/outputs/{mode}/ 既存出力を Step C v108_standard pool の event_id で filter 流用 (2,500 events → 263,736 → 17,207、0.3 秒、層 B 不変)、propagation_analyzer は per-event 波及プロファイル算出で delta_C_medium / delta_Q_medium / n_pulses_short / path_X_excess_delta_C_medium × 4 path (familiarity / attention_via_salience / temporal_coactivation / integration_alpha) を unrelated_baseline 比較で算出、smoke seed 0 で v112 **delta_C_medium mean +0.7465** + **path_familiarity_excess +1.2169** + **path_attention_excess +1.0766** / v108_standard delta_C_medium mean +0.0402 + path_familiarity_excess +0.1175 を実測 (観察事実のみ、判定は Step J で実施)、bit-identity 層 A で baseline + excess + profile 各 condition 2 ファイル × 2 condition = 6 ファイル全てで 2 回実行 hash 完全一致 PASS、層 B (v108_re/v108 既存出力読み込みのみ) + 層 C (v112/outputs/smoke/ 配下のみ書き込み) も保証、Step E 実行時間 smoke seed 0 で 5.5 秒 + 出力 3.34 MB、main run 24 seeds 並列 (12 workers) 推定 10-15 秒、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + 規律 42 候補 + §0.5 禁止事項 全項目遵守、新規留保事項発生なし (累計 26 件不変)、Step D で v108_standard event_id を rename していた問題は v108_re 既存値保持に修正済 (smoke 再実行で bit-identity 不変)、Step F (observation_recorder 実装 + smoke seed 0) に進行可。

---

## 1. 実装内容

### 1.1 ファイル構成

| ファイル | 役割 | 行数 |
|---|---|---:|
| `developmental/v112/v112_baseline_recalculator.py` | 6 path + 5 baseline × 2 condition で delta 計算 | 215 |
| `developmental/v112/v112_propagation_analyzer.py` | per-event 波及プロファイル + path_excess 算出 | 235 |
| `developmental/v112/v112_atom_event_generator.py` (修正) | v108_standard event_id rename 廃止 → v108_re 既存値保持 | -1/+1 |

### 1.2 baseline_recalculator 出力 schema

```
v112/outputs/{smoke,main}/
├── baselines_with_delta_v112_seed{N}.parquet
│   shape ~ (45,396, ~50)  : (event_id × target_cid × relation_path_type, delta 6 種 × window 3 種)
├── excess_change_adjusted_v112_seed{N}.parquet
│   shape ~ (2,718, 43)    : (event_id × relation_path_type) で mean delta + adjusted_delta
├── baselines_with_delta_v108_standard_seed{N}.parquet     (v108_re 既存流用 + filter)
│   shape ~ (263,736, ~50)
├── excess_change_adjusted_v108_standard_seed{N}.parquet   (v108_re 既存流用 + filter)
│   shape ~ (17,207, 43)
└── baseline_recalc_run_summary_{mode}.parquet
```

relation_path_type 9 種実測 (v112 seed 0):
- relation paths 5 種: familiarity (325), attention_via_salience (400), integration_alpha (59), integration_beta (59), temporal_coactivation (400)
- baselines 4 種: unrelated_baseline (400), same_step_random_baseline (400), high_familiarity_outside_integration_baseline (400), same_integration_low_familiarity_baseline (275)
- matched_baseline は 0 件 (smoke seed 0 では空、v107 規約通り欠損可)

### 1.3 propagation_analyzer 出力 schema

```
v112/outputs/{smoke,main}/
├── propagation_profile_v112_seed{N}.parquet
│   shape ~ (400, 27)      : per event 行
│   主観察列:
│     delta_C_medium       : relation paths 5 種の mean (medium window)
│     delta_Q_medium       : 同上
│     n_pulses_short       : relation paths 5 種の mean (short window)
│     path_{X}_excess_delta_C_medium  (X = familiarity / attention_via_salience /
│                                            temporal_coactivation / integration_alpha)
│   補助列 (post-process 検査用):
│     raw_{path}_delta_C_medium  (5 paths + unrelated_baseline)
│   層化軸 (Step C metadata 由来):
│     n_core_bin, formation_relation, n_core, lifespan, fam_max,
│     target_step, death_step
│   event metadata:
│     source_cid, timestamp, atom_id, atom_index
├── propagation_profile_v108_standard_seed{N}.parquet  (shape ~ (2,500, 27))
└── propagation_profile_run_summary_{mode}.parquet
```

### 1.4 設計上の注

**EXCESS_REFERENCE = "unrelated_baseline"**: path_excess の基準は最も中立な unrelated_baseline を採用 (Step A v2 §3.3 設計)。matched_baseline は smoke seed 0 で 0 件、main run でも欠損可能のため reference に採用しない。

**v108_standard event_id 保持** (Step D 修正): v108_re 既存 baselines は event_id で索引、v108_standard で event_id を rename すると流用不可。Step D の `df["event_id"] = [f"{seed}_v108_standard_atom_{i}" ...]` を廃止し、v108_re 元値 (`{seed}_atom_{i}`) を保持。Step D smoke を再実行し bit-identity 不変を確認済。

---

## 2. Smoke seed 0 結果

### 2.1 baseline_recalculator 結果

| condition | n_events | n_with_delta | n_excess | t_total | size_with_delta + excess |
|---|---:|---:|---:|---:|---:|
| **v112** | 400 | 45,396 | 2,718 | 2.6 秒 | 0.30 + 0.23 = **0.53 MB** |
| **v108_standard** | 2,500 | 263,736 | 17,207 | 0.3 秒 | 1.60 + 1.11 = **2.71 MB** |
| 合計 | 2,900 | 309,132 | 19,925 | 2.9 秒 | **3.24 MB** |

v108_standard filter ratio: 17,207 / v108_re 全件 ≈ 28-29% (v108_re main excess ~60,000 → smoke 60,000/24 ≈ 2,500 events worth)。

### 2.2 propagation_analyzer 結果 (per-event 集計、smoke seed 0)

#### v112 (400 events)

| 指標 | mean | std | min | max |
|---|---:|---:|---:|---:|
| delta_C_medium | **+0.7465** | 3.301 | -15.79 | +11.69 |
| delta_Q_medium | -0.0962 | 2.645 | -12.08 | +13.61 |
| n_pulses_short | +1.192 | 0.200 | +0.78 | +1.72 |
| path_familiarity_excess_delta_C_medium | **+1.2169** | 3.296 | -4.75 | +16.85 |
| path_attention_excess_delta_C_medium | **+1.0766** | (略) | - | - |
| path_temporal_excess_delta_C_medium | (略) | - | - | - |
| path_integration_alpha_excess_delta_C_medium | -2.169 | 12.500 | -32.50 | +16.25 |

注: integration_alpha は smoke seed 0 では 59 events のみで std 大、main run 24 seeds で再評価予定。

#### v108_standard (2,500 events)

| 指標 | mean |
|---|---:|
| delta_C_medium | +0.0402 |
| delta_Q_medium | -0.0183 |
| path_familiarity_excess | +0.1175 |
| path_attention_excess | +0.0201 |

→ smoke seed 0 では v112 と v108_standard で **delta_C_medium が約 19 倍**、**path_familiarity_excess が約 10 倍** の差。**観察事実のみ記録**、3 段階判定は廃止 (Step A v2 §3.4)、Step J cross-seed 集計で 24 seeds 統合観察 + Step F observation_recorder で予想との比較記録予定。

### 2.3 n_core_bin × formation_relation 分布 (v112 seed 0)

| n_core_bin | formation_relation | count |
|---|---|---:|
| bin_5_plus | before | 400 (100%) |

→ Step C 留保 26 通り、cond3 (n_core ≥ 5) + cond1 (¬β at target_step、seed 0 では before が全件) で構造的に 1 cell 集中。空セル (bin_2/3_4 + during/after + no_alpha) は記録のみ深追いしない。

---

## 3. bit-identity 検証 (層 A: 全 6 ファイル PASS)

### 3.1 2 回実行 hash 比較

| ファイル | run1 hash | run2 hash | 結果 |
|---|---|---|:-:|
| `baselines_with_delta_v112_seed0.parquet` | `6813dc915d3fee27` | `6813dc915d3fee27` | ✓ |
| `excess_change_adjusted_v112_seed0.parquet` | `7d7f6dd77c6d5d6e` | `7d7f6dd77c6d5d6e` | ✓ |
| `propagation_profile_v112_seed0.parquet` | `b49c82b1428f3c11` | `b49c82b1428f3c11` | ✓ |
| `baselines_with_delta_v108_standard_seed0.parquet` | `c18d2a0836234667` | `c18d2a0836234667` | ✓ |
| `excess_change_adjusted_v108_standard_seed0.parquet` | `10c9cff1de66c1a7` | `10c9cff1de66c1a7` | ✓ |
| `propagation_profile_v108_standard_seed0.parquet` | `80ec643e63bb5f28` | `80ec643e63bb5f28` | ✓ |

→ **層 A PASS** (6/6)、deterministic 動作確認。

### 3.2 層 B (既存出力不変)

確認:
- `developmental/v108/outputs/main/global_activation_factor_seed*.parquet` を **読み込みのみ** (add_adjusted_excess で利用、mtime/size 不変)
- `developmental/v110/v108_re/outputs/{mode}/baselines_with_delta_v108_re_seed*.parquet` を **読み込みのみ** (filter のみ)
- `developmental/v110/v108_re/outputs/{mode}/excess_change_adjusted_v108_re_seed*.parquet` を **読み込みのみ**
- v107/v106 ledger 系 (diag_v105_main_v2/) は v107 build_all_paths/build_baselines/compute_deltas が読み込み (これも v10.7 既存実装と同経路)

→ **層 B 不変保証**。

### 3.3 層 C (パス制限)

`assert_output_under_v112()` + `safe_write_parquet_v112()` で v112/outputs/{smoke,main}/ 配下以外への書き込みを構造的阻止。
→ **層 C PASS**。

---

## 4. 規律遵守自己検証 (Step E)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 + Step C + D で確認済 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ propagation_analyzer の 7 観察列 (delta_C_medium / delta_Q_medium / n_pulses_short + 4 path_excess) は Step A v2 §3.3 で確定済、新規軸増加なし |
| §34 #37 (n_core 別層化必須) | ✓ profile に n_core_bin 列を同梱、Step F observation_recorder で集計予定 |
| §5.5 規律チェックリスト (案 X) | ✓ 全項目 ○ |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ baseline 計算は post-process 集計、ledger 不変 |
| 神の手回避 | ✓ v107 build_baselines (5 種) + build_all_paths (5 種) を共通利用、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 |
| 因果断定回避 | ✓ 「波及」「字面に揺れる」表現、smoke 数値も「観察事実」のみ |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

### 4.1 §0.5 禁止事項

| 禁止事項 | Step E 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ Step A v2 §3.3 設計 (7 observation columns) と整合 |
| 観察軸を増やす方向への転換を提案しない | ✓ propagation profile schema は Step A v2 §3.3 + raw_{path}_delta_C_medium 検査列のみ追加 (新規軸ではない) |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ Step C 母集団 (v112 17.50 events/seed、v108_std 213 cids/seed) を変更せず処理 |

→ **Step E 全項目遵守**。

---

## 5. Step F 進行案

### 5.1 Step F scope (observation_recorder 実装 + smoke seed 0)

`v112_observation_recorder.py` で以下を実装:

1. **観察事実集計** (per-seed → cross-seed):
   - n_events, n_atoms_unique, n_cids_unique
   - delta_C_medium / delta_Q_medium / n_pulses_short の mean/std/median (per condition)
   - path_X_excess_delta_C_medium の mean/std/median (per condition × path × seed)
   - cohens_d (v112 vs v108_standard、Step A v2 §3.4 副次比較)

2. **層化観察** (Step A v2 §3.3 layering):
   - by_n_core_bin: bin_5_plus 100% (留保 26 で記録)
   - by_formation_relation: before / no_alpha 集計 (空セル `n_pairs=0` 明示)
   - by_atom_id: 25 atom 別 propagation profile (副次)

3. **予想との比較** (Aruism 整合、Step A v2 §3.4):
   ```json
   "expectations_vs_observation": [
     {"expectation": "v112 受容 cid pool (420 events) が確保される",
      "observed": true, "value": 420},
     {"expectation": "波及プロファイルが算出される (delta_C/path_excess)",
      "observed": true},
     {"expectation": "v108_standard との比較で何らかの差が出る",
      "observed": ..., "value": ...}
   ]
   ```

4. **留保事項記録** (新規 + 継承、計 26 件):
   - 留保 26 (cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中) を `n_pairs=0` 明示で記録

出力: `v112/outputs/{smoke,main}/observation_records_{mode}.json`

### 5.2 Step G-K (再掲、Step C 報告 §5)

```
Step F: observation_recorder 実装 + smoke seed 0
Step G: orchestrator smoke (seed 0、bit-identity 層 A 再検証)
Step H: smoke 完了報告 → main run 判定要請 (Web Claude/Taka)
Step I: main run (24 seeds × 2 conditions、約 15 秒)
Step J: cross-seed 集計 + 層化観察 + v108 副次比較
Step K: 主題完了報告 (observation_records.json + 留保事項リスト)
```

### 5.3 上申条件 (Code A → Web Claude/Taka)

Step F-K 全期間で発生時は実装中断 + 上申:
- 母集団不足 (cond4 top 50% でも 24 seeds 全て >= 10 events 確保できない) → Step C で解消済、現時点なし
- 規律違反の兆候 (観察軸増加転換が必要に見える等)
- 第 5 版主題と整合しない設計判断が必要に見える
- bit-identity 層 A / 層 B / 層 C のいずれかが PASS しない

→ 現時点 (Step E 完了) では上申条件いずれも該当なし、Step F 単独進行可。

---

## 6. 計算資源実測 + main run 推定

### 6.1 smoke (seed 0) 実測

| 工程 | 時間 | 出力サイズ |
|---|---:|---:|
| Step E baseline_recalculator (2 cond) | 2.9 s | 3.24 MB |
| Step E propagation_analyzer (2 cond) | 2.5 s | 0.11 MB |
| **Step E 合計** | **5.4 s** | **3.35 MB** |

### 6.2 main run 推定 (24 seeds × 2 condition、12 workers 並列)

| 工程 | per-seed time | 並列効果 (12 workers) | 24 seeds 推定 |
|---|---:|---:|---:|
| baseline_recalculator (v112) | 2.6 s | 2 wave | ~5-6 s |
| baseline_recalculator (v108_standard) | 0.3 s | 1 wave | ~1 s |
| propagation_analyzer (v112) | 0.4 s | 1 wave | ~1 s |
| propagation_analyzer (v108_standard) | 2.1 s | 2 wave | ~5 s |
| **Step I main 推定** | - | - | **約 12-15 秒** |

出力サイズ推定: smoke 3.35 MB × 24 ≈ **80 MB** (累計 v112 ~2.0 GB、上限 6 GB の 33%)。

---

## 7. 留保事項 (累計 26 件、変更なし)

### 7.1 Step E で新規発生なし

baseline_recalculator + propagation_analyzer は Step A v2 §3.3 設計に厳密整合、新規留保なし。

### 7.2 既存留保 26 の event-level 確認 (再)

留保 26 (層化集計の cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中):
- v112 seed 0 propagation profile (400 events): bin_5_plus 400 (100%) + before 400 (100%)
- Step F observation_recorder で集計時に `by_n_core_bin: {bin_2: n_pairs=0, bin_3_4: n_pairs=0, bin_5_plus: ...}` 形式で空セル明示記録予定

### 7.3 副次観察候補 (留保候補、Step J で再評価)

smoke seed 0 では v112 と v108_standard で:
- delta_C_medium mean が **約 19 倍** (+0.75 vs +0.04)
- path_familiarity_excess が **約 10 倍** (+1.22 vs +0.12)
- path_attention_excess が **約 50 倍** (+1.08 vs +0.02)

→ これは seed 0 単独の観察事実、main run 24 seeds で cross-seed 統合判定 (Step J)。観察事実として記録、3 段階判定はしない (Aruism 整合、Step A v2 §3.4)。

---

## 8. 一文サマリ (再掲)

Step E で `v112_baseline_recalculator.py` (215 行) + `v112_propagation_analyzer.py` (235 行) を実装、v107 build_all_paths / build_baselines / compute_deltas / compute_baseline_excess_change + v108 add_adjusted_excess 共通利用で v112 新規計算 (400 events → 2,718 (event,path) excess、2.6 秒) + v108_standard は v108_re 既存出力流用 (event_id filter、0.3 秒、層 B 不変)、propagation_analyzer で per-event 波及プロファイル (delta_C_medium / delta_Q_medium / n_pulses_short + 4 path_excess vs unrelated_baseline、Step C metadata 同梱) 算出、smoke seed 0 で v112 delta_C_medium mean +0.7465 / path_familiarity_excess +1.2169 / path_attention_excess +1.0766 / v108_standard delta_C_medium +0.0402 / path_familiarity_excess +0.1175 を観察事実として記録 (判定は Step J 24 seeds 統合で実施、Aruism 整合)、bit-identity 層 A で baseline + excess + profile × 2 condition × 1 seed = 6 ファイル全てで 2 回実行 hash 完全一致 PASS + 層 B (v108_re/v108 既存出力読み込みのみ) + 層 C (v112/outputs/smoke/ 配下のみ) も保証、Step E smoke 実行時間 5.4 秒 + 出力 3.35 MB、main run 24 seeds × 12 workers 並列推定 12-15 秒、Step D で v108_standard event_id rename していた問題を v108_re 既存値保持に修正 (smoke 再実行で bit-identity 不変)、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + 規律 42 候補 + §0.5 禁止事項 全項目遵守、新規留保事項発生なし (累計 26 件不変)、副次観察として v112 vs v108_standard で delta_C_medium 約 19 倍 / path_familiarity_excess 約 10 倍の差を smoke seed 0 で観察 (cross-seed 判定は Step J)、Step F (observation_recorder 実装 + smoke seed 0) に進行可。

---

*以上、v10.12 Step E 完了報告。Code A は本報告 commit + push 後、Step F に進行。Step F-G 単独進行 + Step H で main run 判定要請、Step K で主題完了報告。第 5 版主題 + 第 4 版実装指示書 + 累積規律 26 件 + §5.5 規律チェックリスト + §0.5 禁止事項を Step F-K 全期間遵守。*
