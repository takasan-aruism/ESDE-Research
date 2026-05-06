# v10.7 Step G 報告 — 統合 smoke + bit-identity B + Step F 修正

*作成*: 2026-05-07、Code A
*親*: `v107_step_f_report.md` (Step F 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v107_post_process.py` orchestrator を実装、Step C-F を seed 0 で順次実行する **全機構統合 smoke** を完走 (114 秒)、Step F 4 点修正 (echo 閾値 0.001→0.01、integration no_signal フラグ、event 終端除外、multi_hop hop 1 を familiarity と同義扱い) を反映、bit-identity **層 B PASS** (v10.6 出力 731 ファイル全て不変)、層 A は 9/10 ファイル完全一致 (`post_process_run_summary` のみ実行時間記録のため差分、これは仕様)、storage 13.81 MB/seed × 24 = 331 MB (上限 6 GB の **5%**)、24 seeds main run 推定 46 分、Step I (24 seeds 本番) 進行準備完了。

---

## 1. 統合 smoke 結果

| Step | seed 0 実行時間 | 出力 records |
|---|---:|---:|
| C: source_event aggregator | **0.13 秒** | 14,385 events |
| D: relation_path constructor | **19.08 秒** | 851,154 records |
| E: baseline + delta 集計 | **87.96 秒** | 1,763,031 records (path 851K + baseline 912K) |
| F: avalanche + peak_lag | **7.24 秒** | mh 328,936 / loops 5,274 / curve 1,010 / waves 10 |
| **TOTAL** | **114.41 秒/seed** | - |

→ 24 seeds 推定 **約 46 分** (114.41 × 24 / 60、Step E が支配的)。

### 1.1 storage 実測 (seed 0)

```
baselines_with_delta_seed0.parquet      9.08 MB
excess_change_seed0.parquet             3.29 MB
relation_paths_seed0.parquet            0.72 MB
source_events_seed0.parquet             0.43 MB
multi_hop_paths_seed0.parquet           0.24 MB
resonance_loops_seed0.parquet           0.03 MB
decay_rate_seed0.parquet                0.01 MB
peak_lag_curve_seed0.parquet            0.01 MB
wave_patterns_seed0.parquet             0.00 MB
TOTAL                                  13.81 MB/seed
```

→ **24 seeds 推定: 331 MB** (上限 6 GB の **5%**)。修正案 D (pulse 1/5 サブサンプリング) **不要**、E (parquet 圧縮) 単独で十分余裕。

---

## 2. bit-identity 検証

### 2.1 層 B: v10.6 baseline 不変性

```
v10.6 files tracked: 731
PASS: v10.6 baseline 731 files 全て不変
```

→ smoke 前後で `developmental/v106/outputs/main/` 配下 731 ファイル全部の MD5 が完全一致。**v10.7 実装が v10.6 出力を破壊していないことを確認**。

### 2.2 層 A: 同 seed 2 回実行

```
Layer A files compared: 10
identical files: 9/10
DIFFER: post_process_run_summary.parquet
```

差分の原因: `post_process_run_summary.parquet` は **各 Step の実行時間 (`t_step_c`, `t_step_d`, ... `t_total`) を記録** しており、毎回の wall-clock 時間が異なるため md5 が一致しない。

→ **データの決定論性は保たれている** (実 9 ファイル全部完全一致)。summary は **メタ情報のみ** で finding に影響しない。

→ Step I main run でも同様に summary は除外して bit-identity 層 A 検証する。

---

## 3. Step F 4 点修正反映

### 3.1 echo 判定閾値: 0.001 → 0.01

```python
ECHO_LOCAL_MAX_THRESHOLD = 0.01  # Step F の 0.001 から
```

local_maxes カウントが abs_value > 0.01 のものに限定。

### 3.2 integration の no_signal フラグ

```python
INTEGRATION_PATH_TYPES = {"integration_alpha", "integration_beta"}

# wave_pattern 判定で:
if path in INTEGRATION_PATH_TYPES or abs_peak < ECHO_LOCAL_MAX_THRESHOLD:
    wave_class = "no_signal"
```

→ Step F 修正後の wave_patterns 出力:

| relation_path_type | peak_lag | abs_peak | wave_class | excluded_reason |
|---|---:|---:|---|---|
| **familiarity** | 470 | **0.212** | echo | (記録対象) |
| **temporal_coactivation** | 490 | 0.121 | echo | (記録対象) |
| **attention_via_salience** | 460 | 0.097 | echo | (記録対象) |
| matched_baseline | 380 | 0.066 | echo | |
| same_step_random_baseline | 80 | 0.059 | echo | |
| unrelated_baseline | 500 | 0.043 | echo | |
| same_integration_low_familiarity_baseline | 380 | 0.035 | echo | |
| high_familiarity_outside_integration_baseline | 410 | 0.029 | echo | |
| **integration_alpha** | 0 | 0.000 | **no_signal** | integration (no C signal) |
| **integration_beta** | 0 | 0.000 | **no_signal** | integration (no C signal) |

→ integration が **明示的に no_signal フラグ**、解釈時に除外可能。

### 3.3 event 終端除外

```python
base = base[base["timestamp"] + max(LAG_BINS) <= RUN_END_STEP].copy()
```

= timestamp + 1000 > 25000 の event は peak_lag 計算から除外 (post_event の真の値が取得できないため)。サンプル size が `1,656,881` (Step F の `1,763,031` から 6% 減、終端 events 除外で適切に削減)。

### 3.4 multi_hop hop 1 を familiarity と同義扱い

Step E excess_change の `relation_path_type='familiarity'` は実態としては multi_hop hop 1 と同等。Step F の `compute_decay_rate` 内で:

```python
df_excess_for_decay.loc[df_excess_for_decay["relation_path_type"] == "familiarity",
                          "relation_path_type"] = "familiarity_hop1"
```

これにより hop 1 の delta は Step E から取得可能。

**残課題**: hop 2 / hop 3 の delta は Step E baseline_constructor に未対応 (multi_hop record が Step E に渡されていない)。Step I main run で:
- (a) baseline_constructor を multi_hop 対象に拡張する場合: storage 微増だが実装小改修
- (b) Step F 内で multi_hop の delta を独立集計する場合: storage 中量増だがロジック分離
- 現状: hop 1 のみで decay_pattern を判定 (`sharp_decay`)、hop 2/3 は records 0 で記録だけ

→ **Step I main run では hop 2/3 の delta 集計を追加実装** することで完全な減衰率追跡を実現。Step G の本 smoke 段階では hop 1 のみで進行。

---

## 4. Step F 修正後の主要観察 (seed 0)

### 4.1 path 別 peak_lag (Step F 修正後)

| relation_path_type | peak_lag | abs_peak | wave_class |
|---|---:|---:|---|
| **familiarity** | 470 | **0.212** | echo |
| temporal_coactivation | 490 | 0.121 | echo |
| attention_via_salience | 460 | 0.097 | echo |
| same_step_random_baseline | **80** | 0.059 | echo |
| matched_baseline | 380 | 0.066 | echo |
| (他 baselines) | 380-500 | 0.029-0.043 | echo |
| integration_alpha/beta | 0 | 0.000 | **no_signal** |

### 4.2 First-look (Level 1-3 候補、Step J で本格集計)

- **familiarity の peak_lag = 470 で abs_peak = 0.212** が最大 → **Level 2 候補** (relation_path 経由 > unrelated 0.043)
- temporal_coactivation 0.121 / attention_via_salience 0.097 も baselines (0.029-0.066) より高い → 同 Level 2
- **same_step_random_baseline は peak_lag = 80** (短期、他 baselines 380+ から特異的) → 同 step 動いてる cid は早期に変化、これは Genesis 系の **同期動学の証拠**
- integration は no_signal で除外、Level 比較からは外れる

→ Step J (Level 1-3 reports 作成) で 24 seeds 集計してから判定。本 Step G では smoke 動作確認のみ。

---

## 5. Step G 完了条件チェック

- [x] orchestrator (`v107_post_process.py`) 実装、Step C-F を順次実行
- [x] Step F 4 点修正反映 (echo 閾値、integration no_signal、event 終端除外、multi_hop hop 1)
- [x] bit-identity 層 B PASS (v10.6 出力 731 ファイル不変)
- [x] bit-identity 層 A: 9/10 ファイル完全一致 (summary は実行時間記録のため除外)
- [x] storage 実測 (13.81 MB/seed、24 seeds 331 MB、上限の 5%)
- [x] 24 seeds 単一バッチ実行可能性 (114 秒 × 24 = 46 分)

---

## 6. 出力ファイル

```
developmental/v107/
├── v107_post_process.py            (orchestrator、本実装)
├── v107_avalanche_monitor.py       (Step F 4 点修正反映)
├── v107_step_g_report.md           (本報告)
└── outputs/smoke/
    ├── source_events_seed0.parquet
    ├── relation_paths_seed0.parquet
    ├── baselines_with_delta_seed0.parquet
    ├── excess_change_seed0.parquet
    ├── multi_hop_paths_seed0.parquet
    ├── resonance_loops_seed0.parquet
    ├── decay_rate_seed0.parquet
    ├── peak_lag_curve_seed0.parquet
    ├── wave_patterns_seed0.parquet
    └── post_process_run_summary.parquet
```

---

## 7. Step I 進行への申請

Step H は不要 (Step G で smoke 報告と本番判定を一括)。Step I (24 seeds 単一バッチ main run、`v107_post_process.py --mode main`) に進む許可を求めます。

実行方針:
1. **24 seeds 単一バッチ実行** (memory 規律: 3 バッチ分割禁止)
2. 推定実行時間 **約 46 分**
3. 推定 storage **約 331 MB** (上限 6 GB の 5%)
4. bit-identity 層 B 検証を main run の前後で実施 (v10.6 baseline 不変性)
5. 出力先: `developmental/v107/outputs/main/`

完了後、Step J (Level 1-3 reports 作成 + 総括 report) に進みます:
- v107_co_occurrence_report.md (Level 1)
- v107_path_enriched_report.md (Level 2)
- v107_source_specific_report.md (Level 3)
- v107_main_run_report.md (総括)

---

*以上、Step G 報告。Web Claude / Taka からの Step I (24 seeds main run) 進行許可待ち。*
