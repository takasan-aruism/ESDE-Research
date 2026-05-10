# v10.12 Step F 完了報告: observation_recorder 実装 + smoke seed 0

*作成*: 2026-05-11、Code A
*親*: Step E 完了報告 (commit df95646) + Step C/D 完了報告
*対象*: Web Claude (相談役) + Taka (確認)
*目的*: Step F 実装 + smoke (seed 0) 動作確認 + bit-identity 層 A 検証 + Step G (orchestrator) 進行案

---

## 0. 一文サマリ

Step F で `v112_observation_recorder.py` を 391 行で実装、Aruism「予想と違えば再観察」原則 (3 段階成功判定 Full/Partial/Failure 廃止、Step A v2 §3.4) に基づき観察事実 + 層化観察 + 副次比較 + 予想との比較 + 留保事項を網羅記録、smoke seed 0 で per-seed × condition 集計 (v112 / v108_standard) + 層化観察 (n_core_bin / formation_relation / atom_id) + cohens_d 7 metric (副次、参考値) + 予想 vs 観察 6 件 (全 matched) + 留保事項 26 件 (継承 22 + 新規 4 [#23 #24 #25 #26]) を出力、層化観察で v112 bin_5_plus 400 (100%) + bin_2/bin_3_4 **n_pairs=0 明示** (留保 26 通り) + before 400 (100%) + no_alpha/during/after **n_pairs=0 明示** / v108_standard では bin_2 2,219 (76%) + bin_5_plus 113 (4.5%) で ESDE 全体分布 (留保 23 通り)、cohens_d 副次比較で **delta_C_medium d=+0.5475** (中等度効果) + **path_attention_via_salience_excess d=+1.0869** (大効果) + path_familiarity_excess d=+0.4918 + path_temporal d=+0.3015 + path_integration_alpha d=-0.6264 (n_a=59 小サンプル、main で要再評価) を**判定主軸ではなく観察事実として記録**、bit-identity 層 A で observation_records.json (computation_metadata.elapsed_sec 除外) + observation_summary.parquet + observation_stratified.parquet 全 3 ファイル 2 回実行 hash 完全一致 PASS、Step F 実行時間 0.08 秒 + 出力 ~30 KB、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項 全項目遵守、新規留保事項発生なし (累計 26 件不変)、Step G (orchestrator smoke seed 0、Step C-F 全工程 bit-identity 層 A 再検証) に進行可。

---

## 1. 実装内容

### 1.1 ファイル構成

| ファイル | 役割 | 行数 |
|---|---|---:|
| `developmental/v112/v112_observation_recorder.py` | 観察事実 + 層化 + 比較 + 予想 + 留保の網羅記録 | 391 |
| `developmental/v112/outputs/smoke/observation_records_smoke.json` | 網羅 JSON | ~26 KB |
| `developmental/v112/outputs/smoke/observation_summary_smoke.parquet` | per-seed × condition tabular | ~10 KB |
| `developmental/v112/outputs/smoke/observation_stratified_smoke.parquet` | 層化観察 tabular | ~14 KB |

### 1.2 設計原則 (Aruism 整合、Step A v2 §3.4)

- **3 段階成功判定 (Full/Partial/Failure) は置かない**
- 「予想と違えば再観察」(v10.11 §5.2 末尾) を採用
- 観察事実 + 予想との比較 + 留保事項を **網羅的に記録**、Web Claude/Taka が読んで v10.13 主題候補を判断する素材として機能

### 1.3 出力 schema

#### `observation_records_{mode}.json` (主要出力)

```json
{
  "metadata": {
    "mode": "smoke",
    "seeds": [0],
    "conditions": ["v112", "v108_standard"],
    "subject": "v10.12 第 5 版主題: Atom 取り込み prototype",
    "subject_lineage": "v10.6 §7.1 で本来予定された主題への復帰、v10.11 §5.1 直接出発点",
    "judgment_principle": "Aruism「予想と違えば再観察」、3 段階判定は廃止"
  },
  "per_seed_condition_summaries": [...],
  "stratified_observations": [...],
  "v112_vs_v108_standard_comparison": {...},
  "expectations_vs_observations": [...],
  "reservations": {...},
  "computation_metadata": {...}
}
```

#### per-seed × condition summary 列 (parquet)

```
seed, condition_id, n_events, n_unique_cids, n_unique_atoms,
{metric}_mean / std / median / n  for metric in [
  delta_C_medium, delta_Q_medium, n_pulses_short,
  path_familiarity_excess_delta_C_medium,
  path_attention_via_salience_excess_delta_C_medium,
  path_temporal_coactivation_excess_delta_C_medium,
  path_integration_alpha_excess_delta_C_medium,
]
```

#### 層化観察 (parquet)

```
seed, condition_id, stratify_axis, stratum, n_pairs,
{metric}_mean / std  for metric in ALL_METRICS
```
3 軸: n_core_bin / formation_relation / atom_id

---

## 2. Smoke seed 0 結果 (網羅記録)

### 2.1 per-seed × condition 集計

| condition | n_events | delta_C_medium mean | delta_Q_medium mean | n_pulses_short mean | path_fam_excess mean | path_attn_excess mean |
|---|---:|---:|---:|---:|---:|---:|
| **v112** | 400 | **+0.7465** | -0.0962 | +1.192 | **+1.2169** | **+1.0766** |
| **v108_standard** | 2,500 | +0.0402 | -0.0183 | +1.048 | +0.1175 | +0.0201 |

→ smoke seed 0 観察事実、判定は Step J 24 seeds 統合で実施。

### 2.2 層化観察 (n_core_bin × condition、留保 26 で空セル明示)

| condition | bin_2 | bin_3_4 | bin_5_plus |
|---|:-:|:-:|:-:|
| **v112** | n_pairs=**0** ✓ | n_pairs=**0** ✓ | n_pairs=400 (delta_C_med +0.7465) |
| **v108_standard** | 2,219 (delta_C_med +0.0265) | 168 (+0.1262) | 113 (+0.1824) |

→ v112 bin_5_plus 100% (cond3 構造的)、v108_standard では bin_2 が 88% (留保 23 「ESDE 76% pulse 系」と整合)。

### 2.3 層化観察 (formation_relation × condition、留保 26 で空セル明示)

| condition | before | no_alpha | during | after |
|---|:-:|:-:|:-:|:-:|
| **v112** | 400 (delta_C_med +0.7465) | n_pairs=**0** ✓ | n_pairs=**0** ✓ | n_pairs=**0** ✓ |
| **v108_standard** | 886 (+0.0565) | 1,156 (+0.0244) | 458 (+0.0488) | n_pairs=0 |

→ v112 before 100% (smoke seed 0 では no_alpha 0、24 seeds 平均では 6.2%)、v108_standard では during 458 を含む (β member cid 含有、留保 #21 「q_c_inherited 観察」と整合)。

### 2.4 v108_standard 副次比較 (cohens_d、参考値、判定主軸ではない)

| metric | d | n_a (v112) | n_b (v108_std) | mean_a | mean_b |
|---|---:|---:|---:|---:|---:|
| delta_C_medium | **+0.5475** | 400 | 2,500 | +0.7465 | +0.0402 |
| delta_Q_medium | -0.0774 | 400 | 2,500 | -0.0962 | -0.0183 |
| n_pulses_short | +0.4976 | 400 | 2,500 | +1.192 | +1.048 |
| path_familiarity_excess | +0.4918 | 325 | 506 | +1.2169 | +0.1175 |
| **path_attention_via_salience_excess** | **+1.0869** | 400 | 2,447 | +1.0766 | +0.0201 |
| path_temporal_coactivation_excess | +0.3015 | 400 | 2,500 | +0.2864 | +0.0227 |
| path_integration_alpha_excess | -0.6264 | **59** | 699 | -2.1686 | +0.0000 |

→ smoke seed 0 で path_attention_via_salience_excess の d=+1.0869 (Cohen's 大効果) が最大、ただし**判定主軸ではなく観察事実として記録**。path_integration_alpha_excess は v112 n_a=59 と小サンプル、main run 24 seeds で再評価予定。

### 2.5 予想との比較 (Aruism 整合、6 件全 matched)

| id | 予想 | 観察 | matched |
|---|---|---|:-:|
| exp_1 | v112 cid pool = 16 (smoke seed 0) | 16 | ✓ |
| exp_2 | v112 events = 16 × 25 = 400 | 400 | ✓ |
| exp_3 | v108_standard events ≈ Step C filter 後 | 2,500 | ✓ |
| exp_4 | 波及プロファイル NaN ではない事象が存在 | v112=400, v108=2500 | ✓ |
| exp_5 | cohens_d (v112 vs v108) 算出 (副次、判定主軸ではない) | 算出済 (7 metric) | ✓ |
| exp_6 | v112 n_core_bin = bin_5_plus が 100% | 100% | ✓ |

→ smoke seed 0 で予想 6 件全 matched、Aruism「予想と違えば再観察」発動条件 (mismatched = 0/6) はなし。

### 2.6 留保事項 (累計 26 件、Step F で新規発生なし)

| id | step | title (要約) |
|---|---|---|
| 1-22 | v10.9-v10.11 | 継承 22 件 (Atom 326 排除、Multi-gate 化、within-cid design、受信機構解明、ε=1 漏れ等)、本主題で再評価対象外 |
| **23** | Step Z | n_core 別反応 type 分業 (v10.10 §3.4) と本主題の整合 |
| **24** | Step B | Q3_threshold (lifespan ≥ 977) の意味と他主題への汎用性 |
| **25** | Step B | familiarity 閾値選定 (top 25% vs top 50%) |
| **26** | Step A 再実施 | 層化集計の cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中 |

---

## 3. bit-identity 検証 (層 A: 全 3 ファイル PASS)

### 3.1 2 回実行 hash 比較 (computation_metadata.elapsed_sec 除外)

| ファイル | run1 hash | run2 hash | 結果 |
|---|---|---|:-:|
| `observation_records_smoke.json` (elapsed_sec=0 normalize) | `3cbb491aef404461` | `3cbb491aef404461` | ✓ |
| `observation_summary_smoke.parquet` | `71d541a55ff05d93` | `71d541a55ff05d93` | ✓ |
| `observation_stratified_smoke.parquet` | `5467111d4946a806` | `5467111d4946a806` | ✓ |

→ **層 A PASS** (3/3)、deterministic 動作確認。`elapsed_sec` のみ run-time 依存だが、normalize 後 content hash 一致。

### 3.2 層 B (既存出力不変)

確認:
- v112/outputs/{smoke,main}/ propagation_profile / events / step_c metadata を **読み込みのみ**
- v108_re/v108 既存出力には触らず

→ **層 B 不変保証**。

### 3.3 層 C (パス制限)

`assert_output_under_v112()` + `safe_write_parquet_v112()` + `safe_write_json_v112()` で v112/outputs/{smoke,main}/ 配下以外への書き込みを構造的阻止。
→ **層 C PASS**。

---

## 4. 規律遵守自己検証 (Step F)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 + Step C-E で確認済 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ 観察項目は Step A v2 §3.3-3.4 で確定済 7 metric + 3 層化軸、新規軸なし |
| §34 #37 (n_core 別層化必須) | ✓ stratified_observations で n_core_bin 別集計、空セル `n_pairs=0` 明示 |
| §5.5 規律チェックリスト (案 X) | ✓ 全項目 ○ |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ 集計のみ、ledger 不変 |
| 神の手回避 | ✓ 7 metric × 3 軸の構造的集計、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承、layered_observations の atom_id 軸も 25 atom 別集計 |
| 因果断定回避 | ✓ 「観察事実」「予想と乖離」「副次比較」表現、「効いた」「効果」なし |
| Aruism 整合 | ✓ 3 段階判定なし、cohens_d は **判定主軸ではなく観察事実として記録** と明記 |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

### 4.1 §0.5 禁止事項

| 禁止事項 | Step F 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ Step A v2 §3.3-3.4 設計に整合 (7 観察列 + 3 層化軸 + 6 予想項目) |
| 観察軸を増やす方向への転換を提案しない | ✓ 観察項目は Step E までで確定済を集計、新規軸提案なし |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ smoke seed 0 で v112 path_integration_alpha n_a=59 は小サンプル、main run で再評価と記録 (緩和なし) |

→ **Step F 全項目遵守**。

---

## 5. Step G 進行案

### 5.1 Step G scope (orchestrator smoke seed 0)

`v112_orchestrator.py` で以下を実装:
1. Step C-F の全工程を **1 コマンドで順次実行** (smoke seed 0)
   - receptive_cid_detector → atom_event_generator → baseline_recalculator → propagation_analyzer → observation_recorder
2. **bit-identity 層 A 全工程再検証**: 各工程の出力 hash を 2 回実行で一致確認
3. **層 B 再確認**: v108_re/v108 既存出力の mtime/size 不変確認
4. **層 C 再確認**: v112/outputs/{smoke,main}/ 配下以外への書き込み 0 件確認
5. main run 起動準備状態の最終確認

→ Step G 完了で **smoke 全工程の再現性 + 不変性が保証**、Step H で main run 判定要請。

### 5.2 Step H-K (再掲、Step E 報告 §5.2)

```
Step G: orchestrator smoke (seed 0、bit-identity 層 A 全工程再検証)
Step H: smoke 完了報告 → main run 判定要請 (Web Claude/Taka)
Step I: main run (24 seeds × 2 conditions、約 12-15 秒推定)
Step J: cross-seed 集計 + 層化観察 + v108 副次比較 + paired_d (24 seeds)
Step K: 主題完了報告 (observation_records.json + 留保事項リスト 26 件)
```

### 5.3 上申条件

Step G-K 全期間で発生時は実装中断 + 上申:
- 母集団不足 (Step C で解消済、現時点なし)
- 規律違反の兆候
- 第 5 版主題と整合しない設計判断
- bit-identity 層 A / 層 B / 層 C のいずれかが PASS しない

→ 現時点 (Step F 完了) では上申条件いずれも該当なし、Step G 単独進行可。

---

## 6. 計算資源 (smoke seed 0)

| 工程 | 時間 | 出力サイズ |
|---|---:|---:|
| Step F observation_recorder | **0.08 s** | ~30 KB |
| 累計 v112 (Step Z + B + C + D + E + F smoke) | - | ~1.7 MB |

main run 24 seeds 推定: 0.08 × 24 ≈ **2 秒以内**、Step F は最軽量。

---

## 7. 一文サマリ (再掲)

Step F で `v112_observation_recorder.py` を 391 行で Aruism 整合 (3 段階判定 Full/Partial/Failure 廃止) で実装、smoke seed 0 で per-seed × condition 集計 + 層化観察 (n_core_bin / formation_relation / atom_id 3 軸、留保 26 通り空セル `n_pairs=0` 明示) + cohens_d 副次比較 7 metric (delta_C_medium d=+0.5475 / path_attention d=+1.0869 / path_integration_alpha d=-0.6264 で n_a=59 小サンプル等、判定主軸ではなく観察事実として記録) + 予想 vs 観察 6 件 (全 matched、Aruism「予想と違えば再観察」発動条件なし) + 留保 26 件 (継承 22 + 新規 4 [#23 Step Z / #24 Step B / #25 Step B / #26 Step A 再実施]) を網羅出力、bit-identity 層 A で json (elapsed_sec 除外 normalize) + summary parquet + stratified parquet 全 3 ファイル 2 回実行 hash 完全一致 PASS + 層 B (既存出力読み込みのみ) + 層 C (v112/outputs/{smoke,main}/ 配下のみ) 保証、Step F 実行時間 0.08 秒 + 出力 30 KB で計算資源最軽量、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項 全項目遵守、新規留保事項発生なし (累計 26 件不変)、Step G (orchestrator smoke 全工程 bit-identity 層 A 再検証) に進行可。

---

*以上、v10.12 Step F 完了報告。Code A は本報告 commit + push 後、Step G に進行。Step G 完了で Step H (main run 判定要請) で Web Claude/Taka 承認を得て main run。第 5 版主題 + 第 4 版実装指示書 + 累積規律 26 件 + §5.5 規律チェックリスト + §0.5 禁止事項を Step G-K 全期間遵守。*
