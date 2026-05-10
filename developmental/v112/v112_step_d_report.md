# v10.12 Step D 完了報告: v112_atom_event_generator 実装 + smoke seed 0

*作成*: 2026-05-11、Code A
*親*: Step C 完了報告 (commit 8880574) + Web Claude `v112_response_to_code_a_v2.md` (Taka 承認 2026-05-11)
*対象*: Web Claude (相談役) + Taka (確認)
*目的*: Step D 実装 + smoke (seed 0) 動作確認 + bit-identity 層 A 検証 + Step E (baseline_recalculator + propagation_analyzer) 進行案

---

## 0. 一文サマリ

Step D で `v112_atom_event_generator.py` を 309 行で実装、v112 events は Step C 受容 cid pool (4 条件複合) に対し 25 atom × cid × (target_step + atom_idx × 10) で生成、smoke seed 0 で v112 **400 events** (16 cid × 25 atom、期待値 delta=0)、v108_standard は v110/v108_re/outputs/main/ 既存出力 (DC-A3 流用、層 B 不変) に Step C metadata (n_core_bin / formation_relation / target_step 等) を inner-join で付与し **2,500 events** (224 cid、Step C v108_standard pool 全 PASS で raw v108 100×25 と一致)、attach_pre_event_state による Q_pre / C_pre / R_familiarity_pre 等の取得済、計算的減算 Q_after = Q_pre - 1 / C_after = C_pre + 1 (ledger 不変)、per-cid event count 全 cid 25 events 完全一致、n_core_bin 分布 bin_5_plus 100% / formation_relation 分布 before 100% (seed 0)、bit-identity 層 A 検証で smoke 2 回実行し **v112 hash 22daba56788d6574 完全一致** + **v108_std hash a69dba1c15a6a259 完全一致** で再現性 PASS、層 B (v108_re 既存出力読み込みのみ、書き込みなし) + 層 C (v112/outputs/smoke/ 配下のみ書き込み) も保証、Step D 実行時間 0.10s + smoke 出力 ~0.5 MB、規律 §35 #9 #10 + §34 #37 + §0.5 禁止事項 全項目遵守、新規留保事項発生なし、Step E (baseline_recalculator + propagation_analyzer 実装 + smoke seed 0) に進行可。

---

## 1. 実装内容

### 1.1 ファイル構成

| ファイル | 役割 | 行数 |
|---|---|---:|
| `developmental/v112/v112_atom_event_generator.py` | atom events 生成本体 | 309 |
| `developmental/v112/outputs/smoke/atom_introduction_events_v112_seed0.parquet` | v112 smoke events | - |
| `developmental/v112/outputs/smoke/atom_introduction_events_v108_standard_seed0.parquet` | v108_standard smoke events | - |
| `developmental/v112/outputs/smoke/atom_event_run_summary_smoke.{json,parquet}` | smoke 集計 | - |

### 1.2 v112 events schema (Step C metadata + v107 pre_event_state)

```
event_source_type, condition_id="v112", source_cid, timestamp, atom_id, atom_index,
top_k_rank=-1, atom_sim_score=NaN, reserved_label, seed, event_id,
# v107 attach_pre_event_state 由来
birth_step, lifespan_so_far, n_core_member, v14_q0, final_state, host_lost_step, reaped_step,
R_familiarity_pre, Q_pre, C_pre, window_value, C_at_window_end, Q_remaining_at_window_end,
n_alphas_pre, n_observed_pre,
# v112 計算的減算
Q_after_atom_intro, C_after_atom_intro,
# Step C metadata (cid-level 層化軸)
target_step, death_step, n_core, n_core_bin, formation_relation,
lifespan, fam_max, top_50_threshold
```

→ 全 35 columns、Step E 以降の baseline_recalculator + propagation_analyzer + observation_recorder が共通利用。

### 1.3 v112 timestamp 設計

各受容 cid `c` に対し:
- target_step(c) = c.birth + 200 (Step C で算出済)
- atom_index = 0..24 (25 atom 全展開)
- event.timestamp = target_step(c) + atom_index × 10

per-cid burst window = [target_step, target_step + 240]
- cond2 (lifespan ≥ 977) で burst end < target_step + 977 = death ⇒ 全 25 events が死亡前に発火
- death 制限の filter 残置 (`t_event >= death_step` で skip)、smoke seed 0 では 0 件 skip (期待値 delta=0)

### 1.4 v108_standard events 構成 (DC-A3 既存出力流用、層 B 不変)

| 工程 | 内容 |
|---|---|
| 入力 | `developmental/v110/v108_re/outputs/main/atom_introduction_events_v108_re_seed{N}.parquet` (v10.10 で v10.8 を再現実行した既存出力、層 B 不変保証) |
| condition_id 変更 | `v108_re` → `v108_standard` (副次比較対象としての命名) |
| Step C metadata inner-join | `source_cid` で `receptive_cids_v108_standard_seed{N}.parquet` の metadata (target_step / n_core_bin / formation_relation / lifespan / fam_max / death_step) を付与、Step C pool 外 cid は drop |
| event_id 再付番 | `{seed}_v108_standard_atom_{i}` |
| 層 B 保証 | v108_re main 出力は **読み込みのみ** (write は v112/outputs/ 配下のみ) |

注: v108_standard の `birth_step` / `host_lost_step` / `reaped_step` は v108 既存実装 (v107 attach_pre_event_state) の値をそのまま継承、Step C `birth_step` / `death_step` は列名衝突回避のため `death_step` のみ Step C 由来で別列として保持。

---

## 2. Smoke seed 0 結果

### 2.1 events 数 + 期待値整合

| condition | 実測 events | 実測 unique cids | 期待値 | delta |
|---|---:|---:|---:|---:|
| v112 | **400** | 16 | 16 × 25 = 400 | **0** ✓ |
| v108_standard | **2,500** | 224 | v108 raw 25 × 100 = 2,500 | **0** ✓ |

→ 両 condition で期待値完全一致、想定通り。

### 2.2 per-cid event count (v112)

| 統計 | 値 |
|---|---:|
| count (cids) | 16 |
| mean | 25.0 |
| std | 0.0 |
| min/max | 25/25 |

→ 全 cid で 25 events、burst 設計通り (death filter による skip 0 件)。

### 2.3 n_core_bin / formation_relation 分布 (v112 seed 0)

| 軸 | 分布 |
|---|---|
| n_core_bin | bin_5_plus 400 (100%) |
| formation_relation | before 400 (100%) |

→ Step C seed 0 結果 (cid: bin_5_plus 100% + before 100%、no_alpha 0) と整合、event-level に正しく伝播。

### 2.4 Q_pre / C_pre 統計 (v112 seed 0)

| 指標 | mean | std | min | max |
|---|---:|---:|---:|---:|
| Q_pre | 7.62 | 9.27 | 0 | 35 |
| C_pre | 24.94 | 15.98 | 0 | 57 |
| Q_after_atom_intro | 6.62 | 9.27 | **-1** | 34 |
| C_after_atom_intro | 25.94 | 15.98 | 1 | 58 |

→ Q_after = Q_pre - 1 / C_after = C_pre + 1 で全 events 一致。Q_pre = 0 の event で Q_after = -1 (計算的減算、ledger 不変、v10.8 と同じ挙動)。

---

## 3. bit-identity 検証

### 3.1 層 A: 同 seed 2 回実行

| condition | hash run1 | hash run2 | 一致 |
|---|---|---|:-:|
| v112 seed 0 | `22daba56788d6574` | `22daba56788d6574` | ✓ |
| v108_standard seed 0 | `a69dba1c15a6a259` | `a69dba1c15a6a259` | ✓ |

→ **層 A PASS**、deterministic 動作確認。

### 3.2 層 B: 既存出力不変

確認項目:
- `developmental/v108/outputs/main/` の baselines_with_delta_seed*.parquet 等 (v10.8 元出力) を **読み込み 0 件、書き込み 0 件** (Step D は v108 main にアクセスしない)
- `developmental/v110/v108_re/outputs/main/atom_introduction_events_v108_re_seed*.parquet` を **読み込みのみ** (mtime / size 不変、`pd.read_parquet` のみ)
- `developmental/v106/outputs/main/cid_atom_sim_matrix_seed*.parquet` は本 Step D で読み込みなし (Step C で読み込み済、Step D は不参照)
- v112 書き込み先は **`developmental/v112/outputs/{smoke,main}/` 配下のみ**

→ **層 B 不変保証**。

### 3.3 層 C: パス制限

`assert_output_under_v112()` を `safe_write_parquet_v112()` 内で実行、v112 配下以外への書き込みを構造的に阻止。
→ **層 C PASS**。

---

## 4. 規律遵守自己検証 (Step D)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 + Step C で確認済、Step D は実装段階 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ 駆動要因 = Atom 取り込み prototype 動作確認、観察軸増加なし |
| §34 #37 (n_core 別層化必須) | ✓ event-level に n_core_bin 列を付与 (Step E 以降で層化集計可) |
| §5.5 規律チェックリスト (案 X) | ✓ 第 5 版主題承認後の実装、観察軸増加・母集団緩和なし |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ Q_after / C_after は計算的減算、ledger 不変 |
| 神の手回避 | ✓ Step C 4 条件複合 + 25 atom 全展開、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 (TARGET_ATOMS) |
| 因果断定回避 | ✓ 「受容 cid」「atom 取り込み」表現、「効いた」なし |

### 4.1 §0.5 禁止事項

| 禁止事項 | Step D 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ 25 atom × cid burst (Step C v2 §3.6 明示 10,500 events 設計と整合) |
| 観察軸を増やす方向への転換を提案しない | ✓ event schema は Step C metadata + v107 pre_event_state のみ、新規軸なし |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ death filter での event skip = 0 件、緩和不要 |

→ **Step D 全項目遵守**。

---

## 5. Step E 進行案

### 5.1 Step E scope (baseline_recalculator + propagation_analyzer 実装 + smoke seed 0)

**`v112_baseline_recalculator.py`** (v10.10 baseline_recalculator 流用):
- 6 baseline (pulse / ingestion / α_formation / β_formation / c_conversion / natural_combined) を 2 condition × seed で再計算
- delta_C / delta_Q in {short=50, medium=200, long=500} step window
- v108_standard baseline は v108_re/outputs/main/ 既存出力流用可 (層 B 不変保証)、v112 のみ新規計算
- per-seed baseline_recalculator × condition で 12 計算 (smoke seed 0 → 1 seed × 12)

**`v112_propagation_analyzer.py`** (v10.10 multi_axis_stratified_analyzer 流用):
- per-event 波及プロファイル算出: delta_C_medium / delta_Q_medium / n_pulses_short / path_excess 4 種 (familiarity / attention / temporal / integration_alpha)
- 出力: `propagation_profile_seed{N}.parquet` (per-event 行)
- 層化集計は Step J (cross-seed) で実施、Step E では per-seed 出力のみ

### 5.2 Step F-K (再掲、Step C 報告 §5)

```
Step E: baseline_recalculator + propagation_analyzer 実装 + smoke seed 0
Step F: observation_recorder 実装 + smoke
Step G: orchestrator smoke (seed 0、bit-identity 層 A 再検証 + 層 B 再確認)
Step H: smoke 完了報告 → main run 判定要請 (Web Claude/Taka)
Step I: main run (24 seeds × 2 conditions、約 1 分)
Step J: cross-seed 集計 + 層化観察 + v108 副次比較
Step K: 主題完了報告 (observation_records.json + 留保事項リスト 26 件)
```

### 5.3 上申条件 (Code A → Web Claude/Taka)

Step E-K 全期間で発生時は実装中断 + 上申:
- 母集団不足 (cond4 top 50% でも 24 seeds 全て >= 10 events 確保できない)
- 規律違反の兆候 (観察軸増加転換が必要に見える等)
- 第 5 版主題と整合しない設計判断が必要に見える
- bit-identity 層 A / 層 B / 層 C のいずれかが PASS しない

→ 現時点 (Step D 完了) では上申条件いずれも該当なし、Step E 単独進行可。

---

## 6. 留保事項 (累計 26 件、変更なし)

### 6.1 Step D で新規発生なし

Step D 実装は Step C metadata + v107 attach_pre_event_state の組み合わせで完結、新規留保なし。

### 6.2 既存留保 26 の実測値 (event-level)

留保 26 (層化集計の cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中):
- seed 0 v112 events: bin_5_plus 100% (400/400) + before 100% (400/400)
- Step C seed 0 cid level (16 cids: bin_5+ 100%, before 100%) と event level 完全一致

→ 留保 26 の event-level 反映を確認、Step F observation_recorder で `n_pairs=0` として空セル記録予定。

---

## 7. 計算資源 (smoke seed 0 実測)

| 区分 | 値 |
|---|---:|
| Step D 実行時間 (smoke seed 0) | 0.10 秒 |
| 内訳: v112 生成 | 0.08 秒 |
| 内訳: v108_standard 生成 | 0.01 秒 |
| smoke 出力サイズ計 | ~0.5 MB |
| 累計 v112 output (step_z + step_b + step_c + step_d smoke) | ~2.1 MB |

→ main run 推定 (24 seeds): v112 ~2 秒 + v108_standard ~0.3 秒 ≈ **約 2.5 秒** (Step D だけの計算量、attach_pre_event_state 含む)。

---

## 8. 一文サマリ (再掲)

Step D で `v112_atom_event_generator.py` を 309 行で実装、Step C 受容 cid (4 条件複合) に対し 25 atom × cid × (target_step + atom_idx × 10) で v112 events 生成 + v110/v108_re/outputs/main/ 既存出力 (DC-A3 流用) に Step C metadata inner-join で v108_standard events 生成、smoke seed 0 で v112 **400 events** (16 × 25、delta=0) + v108_standard **2,500 events** (224 cids、Step C 全 PASS) を確認、per-cid event count 全 25 events 完全一致、n_core_bin bin_5_plus 100% + formation_relation before 100% (seed 0) で event-level 層化軸も Step C 整合、Q_after = Q_pre - 1 / C_after = C_pre + 1 計算的減算 (ledger 不変)、bit-identity 層 A (v112 hash 22daba56788d6574 + v108_std hash a69dba1c15a6a259 が 2 回実行で完全一致) + 層 B (v108_re/v108 既存出力読み込みのみ、不変) + 層 C (v112/outputs/smoke/ 配下のみ書き込み) 全 PASS、smoke 実行時間 0.10s + 出力 0.5 MB で計算資源予測内、規律 §35 #9/#10 + §34 #37 + §5.5 案 X + 規律 42 候補 + §0.5 禁止事項 全項目遵守、新規留保事項発生なし (累計 26 件不変)、Step E (baseline_recalculator + propagation_analyzer 実装 + smoke seed 0) に進行可。

---

*以上、v10.12 Step D 完了報告。Code A は本報告 commit + push 後、Step E に進行。Step E-G 単独進行 + Step H で main run 判定要請、Step K で主題完了報告。第 5 版主題 + 第 4 版実装指示書 + 累積規律 26 件 + §5.5 規律チェックリスト + §0.5 禁止事項を Step E-K 全期間遵守。*
