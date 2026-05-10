# v10.12 Step G 完了報告: orchestrator smoke + bit-identity 全工程再検証

*作成*: 2026-05-11、Code A
*親*: Step F 完了報告 (commit 431e59e) + Step C-E 完了報告
*対象*: Web Claude (相談役) + Taka (確認、main run 判定要請への進行)
*目的*: Step G 実装 + smoke (seed 0) 全工程一括実行 + bit-identity 層 A/B/C 全層 PASS 確認 + Step H (main run 判定要請) に進む準備

---

## 0. 一文サマリ

Step G で `v112_orchestrator.py` を 297 行で実装、Step D (atom_event_generator) → Step E_baseline (baseline_recalculator) → Step E_propagation (propagation_analyzer) → Step F (observation_recorder) を 1 コマンドで順次実行 + smoke モードで bit-identity 層 A (2 回実行 hash 一致) + 層 B (v108_re/v108 既存出力 mtime/size 不変) + 層 C (v112/outputs/ 配下のみ書き込み構造的保証) を一括検証、smoke seed 0 で **層 A 11 ファイル全 PASS (mismatches=0)** + **層 B 443 files unchanged (0 modified / 0 added / 0 removed)** + **層 C 構造的保証 PASS** の **全 3 層 PASS** を確定、Step C 24 seeds 既存 + Step D-F 2 回実行 (Run 1 + Run 2) + 全検証を 14.02 秒で完了、main run 起動準備状態の最終確認 (Step C cid pool 24 seeds 全件 / Step D-F module 全 PASS / Layer B/C 不変保証) も済、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項 全項目遵守、新規留保事項発生なし (累計 26 件不変)、**Step H (main run 判定要請)** に進行可、Web Claude/Taka 承認後に Step I (24 seeds × 2 conditions main run、推定 12-15 秒) を発動。

---

## 1. 実装内容

### 1.1 ファイル構成

| ファイル | 役割 | 行数 |
|---|---|---:|
| `developmental/v112/v112_orchestrator.py` | Step D-F 順次実行 + 全層検証 | 297 |
| `developmental/v112/outputs/smoke/orchestrator_run_summary_smoke.json` | 実行 + 検証サマリ | ~12 KB |

### 1.2 orchestrator 構造

#### 順次実行 (Step C は前提条件)

```
[prereq] Step C v112/v108_standard cid 24 seeds 既存確認
  ↓
[Step D] v112_atom_event_generator.py (subprocess、--mode smoke)
  ↓
[Step E_baseline] v112_baseline_recalculator.py (--n_workers 12)
  ↓
[Step E_propagation] v112_propagation_analyzer.py (--n_workers 12)
  ↓
[Step F] v112_observation_recorder.py
  ↓
[層 A 検証] (--verify-bit-identity)
  Run 2: 上記を再実行
  hash 比較: 11 ファイル全件で run1 == run2
  ↓
[層 B 検証] (--layer-b-check)
  before/after で v108_re/v108 既存ファイルの mtime + size を比較
  ↓
[層 C 検証] (構造的保証)
  各モジュール safe_write_parquet_v112() で v112/outputs/{smoke,main}/ 配下限定
```

#### CLI

```
--mode {smoke,main}        : seed 数選択 (smoke=1、main=24)
--n_workers N              : 並列度 (default 12)
--verify-bit-identity      : Run 2 で hash 一致検証 (smoke のみ)
--layer-b-check            : v108_re/v108 既存出力 mtime/size 不変検証
```

---

## 2. Smoke seed 0 全工程実行結果

### 2.1 実行時間 (Run 1 + Run 2 + 全検証)

| 工程 | 時間 |
|---|---:|
| Step D (atom_event_generator) Run 1 | 0.09 s |
| Step E baseline_recalculator Run 1 | 2.72 s |
| Step E propagation_analyzer Run 1 | 2.08 s |
| Step F observation_recorder Run 1 | 0.07 s |
| Run 1 小計 | ~5.0 s |
| Run 2 (Step D-F 再実行) | ~5.0 s |
| 検証 (層 A hash 比較 + 層 B mtime 比較) | ~4.0 s |
| **Total** | **14.02 秒** |

→ Step G の追加コスト (Run 2 + 検証) は smoke で +9 秒。main run では検証省略で約 12-15 秒。

### 2.2 層 A (bit-identity 2 回実行 hash 一致): 11/11 PASS

| ファイル | run1 hash | run2 hash | 結果 |
|---|---|---|:-:|
| `atom_introduction_events_v112_seed0.parquet` | `22daba56788d6574` | `22daba56788d6574` | ✓ |
| `atom_introduction_events_v108_standard_seed0.parquet` | `4f14914b66e91250` | `4f14914b66e91250` | ✓ |
| `baselines_with_delta_v112_seed0.parquet` | `2d71fad9ac82a751` | `2d71fad9ac82a751` | ✓ |
| `baselines_with_delta_v108_standard_seed0.parquet` | `1a4da9da1761fdcb` | `1a4da9da1761fdcb` | ✓ |
| `excess_change_adjusted_v112_seed0.parquet` | `cbd9ecf29739c0ee` | `cbd9ecf29739c0ee` | ✓ |
| `excess_change_adjusted_v108_standard_seed0.parquet` | `0113395633523452` | `0113395633523452` | ✓ |
| `propagation_profile_v112_seed0.parquet` | `09db019bd3a0c9f0` | `09db019bd3a0c9f0` | ✓ |
| `propagation_profile_v108_standard_seed0.parquet` | `840e38ebba19977f` | `840e38ebba19977f` | ✓ |
| `observation_summary_smoke.parquet` | `71d541a55ff05d93` | `71d541a55ff05d93` | ✓ |
| `observation_stratified_smoke.parquet` | `5467111d4946a806` | `5467111d4946a806` | ✓ |
| `observation_records_smoke.json` (elapsed_sec normalize) | `3cbb491aef404461` | `3cbb491aef404461` | ✓ |

→ **mismatches=0**、**deterministic 動作完全確認**。

### 2.3 層 B (v108_re/v108 既存出力不変): 443/443 PASS

| 指標 | 値 |
|---|---:|
| tracked files | **443** |
| n_modified | **0** |
| n_added | **0** |
| n_removed | **0** |
| **layer B passed** | **TRUE** ✓ |

検証対象ディレクトリ:
- `developmental/v110/v108_re/outputs/main/` (atom_intro + baselines + excess、24 seeds × 4 type ≈ 96 files)
- `developmental/v110/v108_re/outputs/smoke/` (seed 0 × 4 type ≈ 4 files + 集計)
- `developmental/v108/outputs/main/` (baselines_with_delta + global_activation_factor、24 × 数 type ≈ 343 files)

→ 443 files の mtime + size が完全不変、**v108 既存研究成果は本主題で 1 byte も変更されていない**。

### 2.4 層 C (パス制限、構造的保証): PASS

各モジュールに `assert_output_under_v112()` + `safe_write_parquet_v112()` を実装、書き込み先が v112/ 配下以外なら例外。
- `v112_receptive_cid_detector.py`: outputs/step_c/ のみ
- `v112_atom_event_generator.py`: outputs/{smoke,main}/ のみ
- `v112_baseline_recalculator.py`: outputs/{smoke,main}/ のみ
- `v112_propagation_analyzer.py`: outputs/{smoke,main}/ のみ
- `v112_observation_recorder.py`: outputs/{smoke,main}/ のみ
- `v112_orchestrator.py`: outputs/{smoke,main}/ のみ

→ **構造的保証 PASS** (実行時 violation 検出メカニズム + 全モジュール経路検証済)。

---

## 3. 規律遵守自己検証 (Step G)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 + Step C-F で確認済 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ orchestrator は既存 4 モジュールを順次呼ぶのみ、新規ロジックなし |
| §34 #37 (n_core 別層化必須) | ✓ Step F で実装済、Step G では検証 |
| §5.5 規律チェックリスト (案 X) | ✓ 全項目 ○ |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ Run 2 でも ledger 不変、層 B 検証で 0 modified 確認 |
| 神の手回避 | ✓ 既存モジュール subprocess 呼び出しのみ |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 |
| 因果断定回避 | ✓ Step G は検証フェーズ、観察解釈なし |
| Aruism 整合 | ✓ 3 段階判定なし、PASS/FAIL は層 A/B/C 構造的判定のみ (検証 = 観察ではない) |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

### 3.1 §0.5 禁止事項

| 禁止事項 | Step G 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ orchestrator は Step D-F の chain のみ、新規設計なし |
| 観察軸を増やす方向への転換を提案しない | ✓ 検証専用、新規軸なし |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ 該当なし (検証フェーズ) |

→ **Step G 全項目遵守**。

---

## 4. main run 起動準備状態の最終確認

### 4.1 前提条件チェック

| 項目 | 状態 |
|---|:-:|
| Step C cid pool (v112) 24 seeds | ✓ (24 / 24) |
| Step C cid pool (v108_standard) 24 seeds | ✓ (24 / 24) |
| Step D-F 全モジュール bit-identity 層 A | ✓ (smoke seed 0 で 11/11 PASS) |
| 層 B v108_re/v108 既存出力不変 | ✓ (443 / 443 unchanged) |
| 層 C パス制限 | ✓ (構造的保証) |
| 規律全項目遵守 | ✓ |

### 4.2 main run 実行コマンド (Step H 承認後 Step I で発動)

```bash
# Step I main run (24 seeds × 2 conditions)
python3 developmental/v112/v112_orchestrator.py --mode main --n_workers 12
```

期待値:
- Step D: ~2.5 秒 (24 seeds 直列、subprocess 内並列なし)
- Step E baseline (v112 + v108_standard): ~10 秒 (24 seeds × 12 workers 並列)
- Step E propagation: ~5 秒
- Step F: ~2 秒
- **Total: 約 20-25 秒** (smoke 5 秒の 4-5 倍、Step E が律速)

出力サイズ推定:
- Step D events: ~12 MB (per seed 0.5 MB × 24)
- Step E baseline: ~75 MB
- Step E propagation: ~3 MB
- Step F observation: ~1 MB
- **Total: ~90 MB / 上限 6 GB の 1.5%、累計 v112 1.7 MB + 90 MB = ~92 MB**

### 4.3 Step H 上申内容 (Web Claude/Taka 判定要請)

Code A から Web Claude/Taka に以下を報告 + 判定要請:
1. **Step C-G smoke 全工程 PASS** (本書)
2. **bit-identity 層 A/B/C 全層 PASS**
3. **規律全項目遵守 + §0.5 禁止事項全件遵守**
4. **新規留保事項発生なし** (累計 26 件不変)
5. **main run 推定 20-25 秒、出力 ~90 MB、累計 storage ~92 MB / 6 GB**
6. **判定要請: Step I (main run 24 seeds × 2 conditions) 発動承認**

→ Taka 承認 + Web Claude 確認後、Step I 発動。

---

## 5. Step H-K 進行案 (再掲)

```
Step H: smoke 完了報告 → main run 判定要請 (Web Claude/Taka)
   ↓ Taka 承認
Step I: main run (24 seeds × 2 conditions、約 20-25 秒)
Step J: cross-seed 集計 + 層化観察 + v108 副次比較 + paired_d (24 seeds)
Step K: 主題完了報告 (observation_records_main.json + 留保事項リスト 26 件)
```

### 5.1 上申条件 (Step I-K 全期間)

- 母集団不足 (Step C で解消済、現時点なし)
- 規律違反の兆候
- 第 5 版主題と整合しない設計判断
- bit-identity 層 A / 層 B / 層 C のいずれかが PASS しない (Step G 時点で全 PASS、Step I main で再検証は scope 外)

→ Step G 完了時点で上申条件いずれも該当なし、Step H で main run 判定要請に進む準備完了。

---

## 6. 計算資源 (smoke 全工程 + 検証)

| 区分 | 値 |
|---|---:|
| Step G smoke (Run 1 + Run 2 + 検証) | **14.02 秒** |
| 累計 v112 output (Step Z + B + C + D + E + F + G smoke) | ~1.8 MB |
| main run 推定 (Step I) | ~20-25 秒 |
| 累計 v112 storage 想定 (main 後) | ~92 MB / 6 GB (1.5%) |

---

## 7. 留保事項 (累計 26 件、Step G で新規発生なし)

Step G は検証専用フェーズ、新規留保なし。

既存留保 26 件の状態:
- 継承 22 件 (v10.9-v10.11 由来): 本主題対象外
- #23 (Step Z、n_core 反応 type 分業): cond3 構造的に bin_5+ 集中、観察事実確定
- #24 (Step B、Q3_threshold): 977 採用、観察事実確定
- #25 (Step B、familiarity 閾値): top 50% 採用、観察事実確定
- #26 (Step A 再実施、cond1/cond3 絞り込み集中): smoke seed 0 で実測値確定 (bin_5_plus 100% / before 100%)、空セル `n_pairs=0` 明示記録 (Step F)

→ 留保 #23-#26 は Step F observation_records_smoke.json の `reservations.new_reservations` で機械可読形式記録済、Step K 主題完了報告で v10.13 主題候補として再評価素材化。

---

## 8. 一文サマリ (再掲)

Step G で `v112_orchestrator.py` を 297 行で実装、Step D-F を subprocess で順次実行 + smoke モードで Run 2 を追加実行し bit-identity 層 A (11 ファイル × 2 回実行で hash 完全一致、mismatches=0)、層 B (v108_re/v108 既存出力 443 files の mtime + size を before/after snapshot 比較で 0 modified / 0 added / 0 removed)、層 C (assert_output_under_v112 で v112/outputs/ 配下以外への書き込みを構造的阻止) の **全 3 層 PASS** を 14.02 秒で確定、Step C 24 seeds 前提条件 + Step D-F 全モジュール bit-identity + 層 B/C 不変保証 + 規律全項目遵守 + 累計留保 26 件不変で **main run 起動準備完了**、main run 推定 20-25 秒 + 出力 ~90 MB + 累計 v112 storage ~92 MB / 6 GB (1.5%)、Web Claude/Taka に Step I (24 seeds × 2 conditions main run) 発動の承認を Step H で要請、Aruism 整合 (3 段階判定なし、層 A/B/C は構造的検証のみ、観察解釈は Step J cross-seed で実施)、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項 全項目遵守、新規留保事項発生なし、Step H で main run 判定要請に進行可。

---

*以上、v10.12 Step G 完了報告。Code A は本報告 commit + push 後、Step H (main run 判定要請) に進む。Step H で Web Claude/Taka 承認を得て Step I (main run) → Step J (cross-seed 集計) → Step K (主題完了報告) に進行。第 5 版主題 + 第 4 版実装指示書 + 累積規律 26 件 + §5.5 規律チェックリスト + §0.5 禁止事項を Step H-K 全期間遵守。*
