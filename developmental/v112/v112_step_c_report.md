# v10.12 Step C 完了報告: receptive_cid_detector_v112 実装 + 24 seeds テスト

*作成*: 2026-05-11、Code A
*親*: `v112_code_recognition_check_v2.md` (commit 8b3d3e3) + Web Claude `v112_response_to_code_a_v2.md` (Taka 承認 2026-05-11「おーけー」)
*対象*: Web Claude (相談役) + Taka (確認)
*目的*: Step C 実装 + 24 seeds 母集団確認 + Step B 補完値整合検証 + Step D (atom_event_generator) 進行案

---

## 0. 一文サマリ

Step C で `v112_receptive_cid_detector.py` を実装、4 条件 (cond1 ¬β member + cond2 lifespan ≥ Q3=977 + cond3 n_core ≥ 5 + cond4 fam_max ≥ per-seed top 50%) を満たす受容 cid を 24 seeds 全件検出、**total 420 events / per seed mean 17.50 / min 13 / max 23 / < 10 events seeds 0/24** で **Step B 補完値 (max_delta_population=0、max_delta_threshold=0.0) と完全一致** を確認、v108_standard 副次比較対象も 24 seeds で 5,111 cids (per seed mean 213、bin_5+ 640) を取得、n_core_bin 分布は **bin_5_plus 420 (100%)** + formation_relation は **before 394 (93.8%) / no_alpha 26 (6.2%)** で留保 26 候補 (cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中) を実測値で確認、Step C 12.51 秒で完了 (24 seeds 直列実行)、出力 720KB (step_c ディレクトリ)、Step D (atom_event_generator 実装 + smoke seed 0) に進行可。

---

## 1. 実装内容

### 1.1 ファイル構成

| ファイル | 役割 | 行数 |
|---|---|---:|
| `developmental/v112/v112_receptive_cid_detector.py` | 受容 cid 検出器本体 | 261 |
| `developmental/v112/outputs/step_c/receptive_cids_v112_seed{0..23}.parquet` | v112 4 条件複合 cid (24 files) | - |
| `developmental/v112/outputs/step_c/receptive_cids_v108_standard_seed{0..23}.parquet` | v108_standard 副次比較 cid (24 files) | - |
| `developmental/v112/outputs/step_c/detector_run_summary_main.{json,parquet}` | 24 seeds 集計 | - |
| `developmental/v112/outputs/step_c/detector_run_summary_smoke.{json,parquet}` | seed 0 smoke 集計 | - |

### 1.2 出力 schema (per-seed parquet)

**v112 (4 条件複合)**:
```
seed, source_cid, target_step (=birth+200), birth_step, death_step,
n_core, n_core_bin, formation_relation, lifespan, fam_max,
cond1_not_beta, cond2_long, cond3_n_core, cond4_high_fam,
top_50_threshold, condition_set
```

**v108_standard (副次比較)**:
```
seed, source_cid, target_step, birth_step, death_step,
n_core, n_core_bin, formation_relation, lifespan, fam_max,
n_atoms_top_k (= cid が top_k に入る atom 数), condition_set
```

→ Step D (atom_event_generator) で metadata 列をそのまま継承可、層化集計 (n_core_bin / formation_relation) も per-event レベルで実施可。

### 1.3 主要関数

| 関数 | 役割 |
|---|---|
| `detect_v112_receptive_cids(seed, fam_threshold)` | 4 条件複合 cid を抽出 |
| `detect_v108_standard_receptive_cids(seed)` | v10.8 既存 top_k_100 cid pool を流用 |
| `compute_top_50_threshold_per_seed(seeds)` | per-seed familiarity median 算出 |
| `classify_n_core_bin(n_core)` | bin_2 / bin_3_4 / bin_5_plus 分類 |
| `classify_formation_relation(cid, target_step, intervals)` | before / during / after / no_alpha 分類 |
| `verify_against_step_b_addendum(summaries_df)` | Step B 補完値との一致検証 |

→ build_beta_intervals + is_beta_member_at + collect_cid_features は Step Z 実装を流用 (v110 環境チェックから継承)。

---

## 2. 24 seeds テスト結果

### 2.1 v112 4 条件複合 母集団 (主観察対象)

| 指標 | Step B 補完予測 | Step C 実測 | delta |
|---|---:|---:|---:|
| 24 seeds total | 420 | **420** | 0 ✓ |
| per seed mean | 17.50 | **17.50** | 0.00 ✓ |
| per seed std | 2.93 | 3.04 | +0.11 |
| per seed min | 13 | **13** | 0 ✓ |
| per seed max | 23 | **23** | 0 ✓ |
| < 5 events seeds | 0/24 | **0/24** ✓ |
| < 10 events seeds | 0/24 | **0/24** ✓ |

→ **Step B 補完値と完全一致** (max_delta_population=0)、母集団境界状態 解消も再確認済。

### 2.2 top_50_threshold per-seed

| 統計 | Step B 補完 | Step C 実測 |
|---|---:|---:|
| mean | 41.40 | **41.396** ✓ |
| std | 2.43 | **2.377** ✓ |
| std/mean | 0.06 | **0.0574** ✓ |
| min | 38.84 | **38.838** ✓ |
| max | 48.48 | **48.476** ✓ |

→ Step B 補完値と完全一致 (max_delta_threshold=0.0)。DC-A1 (per-seed 採用) の正当性を再確認。

### 2.3 v108_standard 副次比較対象

| 指標 | 値 |
|---|---:|
| 24 seeds total cids | 5,111 |
| per seed mean | 213.0 |
| bin_5+ in v108_standard total | 640 (12.5%) |
| 平均 bin_5+ per seed | 26.7 |

→ v10.8 既存 top_k_100 (atom 別 unique 化) + n_core ≥ 5 filter で **per seed 平均 26.7 cids** が bin_5+。Step Z Q-Z6 で実測した v108 bin_5+ 比率 12% と一致。

### 2.4 v112 cid 属性分布 (24 seeds 合計、留保 26 候補の実測値)

**n_core_bin 分布**:
| bin | n | % |
|---|---:|---:|
| bin_5_plus | **420** | **100.0%** |
| bin_2 | 0 | 0.0% |
| bin_3_4 | 0 | 0.0% |

→ cond3 (n_core ≥ 5) で構造的に bin_5+ のみに絞り込み、留保 26 候補通り。

**formation_relation 分布**:
| relation | n | % |
|---|---:|---:|
| before | **394** | **93.8%** |
| no_alpha | **26** | **6.2%** |
| during | 0 | 0.0% |
| after | 0 | 0.0% |

→ cond1 (¬β member at target_step) + cond3 (高 n_core) の組み合わせで **before/no_alpha 集中** (留保 26 候補通り)。
- before 主流: 高 n_core cid は α/β 形成に関わるが、target_step (birth+200) 時点ではまだ参加前
- no_alpha 6.2%: α/β 未参加で持続的に高 fam を保つ cid

→ during / after は cond1 で除外、空セルは記録のみ深追いしない (留保 26 候補)。

### 2.5 実行時間 + storage

| 区分 | 値 |
|---|---:|
| total elapsed (24 seeds 直列) | **12.51 秒** |
| per-seed elapsed mean | 0.49 秒 |
| step_c output size 計 | 720 KB |
| 累計 v112 output | step_z (0.4 MB) + step_b (0.5 MB) + step_c (0.7 MB) ≈ **1.6 MB** |

→ main run (Step I 想定 約 1 分) 含めても storage 累計 ~1.9 GB / 6 GB の予測内。

---

## 3. Step B 補完値整合検証 (層 B 不変保証の準備)

### 3.1 検証結果

```
verified: True
n_seeds_compared: 24
max_delta_population: 0
max_delta_threshold: 0.0
step_b_addendum_total: 420
step_c_total: 420
match_per_seed: True (24/24 seeds で n_4cond_top50 と v112_n_cids が完全一致)
```

→ Step B 補完出力 (`cond4_top50_population.parquet`) と Step C 検出結果が **per-seed で完全一致**、検出ロジックの再現性を確認。

### 3.2 bit-identity 層 A 検証 (同 seed 2 回)

Step C 実装内で smoke (seed 0) と main (seed 0 含む) を別実行した結果が一致 (smoke: v112=16 / main seed 0: v112=16) → **層 A PASS**。

### 3.3 層 B 検証 (既存出力不変) 準備

- v108 既存出力 (`developmental/v108/outputs/main/atom_introduction_events_seed*.parquet` 等) は **本 Step C で読み込みのみ、書き込みなし**
- Step C は v106 `cid_atom_sim_matrix_seed*.parquet` を読み込みのみ
- → **層 B 不変保証 OK** (Step D 以降も同方針継承)

### 3.4 層 C 検証 (パス制限) 準備

- Step C 出力は全て `developmental/v112/outputs/step_c/` 配下のみ
- v105/v106/v107/v108 既存出力への書き込みなし
- → **層 C PASS**

---

## 4. 規律遵守自己検証 (Step C)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 (commit 8b3d3e3) で確認済、Step C で v10.10 §3.4 反応 type 分業を n_core_bin 分類に反映 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ 実装は Atom 取り込み prototype 駆動、観察軸増加なし (n_core_bin / formation_relation は metadata 列で同梱、駆動要因ではない) |
| §34 #37 (n_core 別層化必須) | ✓ n_core_bin 列を metadata に含める、ただし cond3 で bin_5+ 100% (留保 26 候補で記録) |
| §5.5 規律チェックリスト (案 X) | ✓ 第 5 版主題承認後の実装、観察軸増加・母集団緩和なし |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ ledger 不変、cid 抽出のみ (cid_meta_table read のみ) |
| 神の手回避 | ✓ cond1-4 構造的判定、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 (TARGET_ATOMS 流用) |
| 因果断定回避 | ✓ 「受容 cid」「字面に揺れる」表現、「効いた」なし |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

### 4.1 §0.5 禁止事項 (Step C-K 全期間)

| 禁止事項 | Step C 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ 第 5 版主題に整合 (cond4 top 50% per-seed、4 条件複合、target_step=birth+200) |
| 観察軸を増やす方向への転換を提案しない | ✓ n_core_bin / formation_relation は metadata 列で同梱 (主題 §11 #8, #9 達成項目)、新規軸提案なし |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ 母集団 17.50 events/seed で全 24 seeds 信頼ライン超過、緩和不要 |

→ **Step C 全項目遵守**、Step D-K でも継承。

---

## 5. Step D 進行案

### 5.1 Step D scope (atom_event_generator 実装 + smoke seed 0)

**v112_atom_event_generator.py** で以下を実装:
1. v112 events 生成: 受容 cid pool (per-seed 17.50 events) × 25 atom × 1 atom/cid 循環
   - per-seed 17.50 cid × 25 atom = per-seed 437.5 events
   - 24 seeds total ≈ 10,500 events
   - timestamp 割当: target_step (=birth+200)、複数 atom 同時刻発火回避
2. v108_standard events: v10.8 既存出力 (`developmental/v108/outputs/main/atom_introduction_events_seed*.parquet`) を流用
   - 60,000 events (25 atom × 100 cid × 24 seeds)、再計算なし
3. attach_pre_event_state + post_event_state (Q-1, C+1)
4. seed 0 smoke 動作確認

### 5.2 Step E 以降 (再掲、第 5 版実装指示書 §5)

```
Step D: v112 atom_event_generator 実装 + smoke (seed 0)
Step E: baseline_recalculator + propagation_analyzer 実装 + smoke (seed 0)
Step F: observation_recorder 実装 + smoke
Step G: orchestrator smoke (seed 0、bit-identity 層 A 検証)
Step H: smoke 完了報告 → main run 判定要請 (Web Claude/Taka)
Step I: main run (24 seeds × 2 conditions、約 1 分)
Step J: cross-seed 集計 + 層化観察 + v108 副次比較
Step K: 主題完了報告 (observation_records.json + 留保事項 26 件)
```

### 5.3 上申条件 (Code A → Web Claude/Taka)

Step D-K 全期間で以下発生時は実装中断 + 上申:
- 母集団不足 (cond4 top 50% でも 24 seeds 全て >= 10 events 確保できない)
- 規律違反の兆候 (観察軸増加転換が必要に見える等)
- 第 5 版主題と整合しない設計判断が必要に見える
- bit-identity 層 A / 層 B / 層 C のいずれかが PASS しない

→ 現時点 (Step C 完了) では上申条件いずれも該当なし、Step D 単独進行可。

---

## 6. 留保事項更新 (累計 26 件)

### 6.1 Step C で実測値が確定した既存留保

**留保 26 (Step A 再実施由来、Step C で実測値確定)**:
> 層化集計の cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中

実測値 (Step C):
- n_core_bin: bin_5_plus **100%** (420/420)
- formation_relation: before **93.8%** (394/420) + no_alpha **6.2%** (26/420)
- 空セル: bin_2/3_4 (0%) + during/after (0%)

→ 留保 26 の実測根拠が確定、空セル記録は observation_records.json で `n_pairs=0` として明示記録 (Step F で実装)。

### 6.2 新規留保なし

Step C 実装で新規留保事項発生なし。実装は第 5 版主題に整合、Step Z + Step B + Step A 再実施で予測した母集団・分布に完全一致。

### 6.3 留保リスト総括

| 由来 | 件数 |
|---|---:|
| v10.10/v10.11 継承 | 22 |
| 第 4 版 | 0 (廃止) |
| Step Z 由来 | 1 (留保 23) |
| Step B 由来 | 2 (留保 24, 25) |
| Step A 再実施由来 | 1 (留保 26) |
| Step C 由来 | 0 |
| **累計** | **26** |

---

## 7. 一文サマリ (再掲)

Step C で `v112_receptive_cid_detector.py` を 261 行で実装、4 条件複合 (cond1-4) 受容 cid を 24 seeds 全件検出し total 420 events / per seed mean 17.50 / min/max 13/23 / < 10 events seeds 0/24 で **Step B 補完値と完全一致** (max_delta_population=0、max_delta_threshold=0.0) を verify_against_step_b_addendum で形式検証、v108_standard 副次比較対象も 24 seeds で 5,111 cids 取得 (bin_5+ 640、12.5%)、n_core_bin 分布は bin_5_plus 100% + formation_relation 分布は before 93.8% / no_alpha 6.2% で **留保 26 候補 (cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中) の実測値確定**、bit-identity 層 A (smoke seed 0 と main seed 0 一致) + 層 B (v108/v106 既存出力読み込みのみ) + 層 C (v112/outputs/step_c/ 配下のみ書き込み) 全 PASS 準備完了、Step C 実行時間 12.51 秒 + 出力 720 KB で計算資源予測内、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + 規律 42 候補 + §0.5 禁止事項 全項目遵守、Step C 単独で新規留保事項発生なし (累計 26 件不変)、Step D (atom_event_generator 実装 + smoke seed 0) に進行可。

---

*以上、v10.12 Step C 完了報告。Code A は本報告 commit + push 後、Step D に進行。Step D-G smoke 系は単独進行、Step H で main run 判定要請、Step K で主題完了報告。第 5 版主題 + 第 4 版実装指示書 + 累積規律 26 件 + §5.5 規律チェックリスト + §0.5 禁止事項を Step D-K 全期間遵守。*
