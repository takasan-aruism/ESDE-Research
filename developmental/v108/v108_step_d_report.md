# v10.8 Step D 報告 — orchestrator + 第 6 種統合 + smoke

*作成*: 2026-05-07、Code A
*親*: `v108_step_c_report.md` (Step C 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v108_post_process.py` orchestrator を実装、5 種 natural source_event (v10.7 流用) + 1 種 atom_introduction_event を統合した完全パイプライン (Step C → D → E → F) を seed 0 で **131 秒、16.32 MB** で smoke、bit-identity 層 B PASS (v10.7 出力 222 ファイル不変)、24 seeds 推定 storage **392 MB** (上限 6 GB の 6%、v10.7 428 MB とほぼ同等)、Step E (global activation 補正) 進行準備完了。

---

## 1. smoke 結果 (seed 0、131 秒)

| Step | 実行時間 | 出力 records |
|---:|---:|---|
| C: source_events 統合 (5 種 + 1 種) | (含 D-F) | 16,885 (natural 14,385 + atom 2,500) |
| D: relation_paths | (5 種、v10.7 流用) | 928,095 |
| E: baselines + delta | | 1,098,672 baselines + 133,332 excess |
| F: multi-hop + peak_lag + loop | | 347,371 mh、711 loop_2、4,563 loop_3 |
| **TOTAL** | **130.89 秒** | - |

→ v10.7 (114 秒) の **+15%** (atom 2,500 events 追加分)。

### 1.1 v10.7 比

| 指標 | v10.7 (seed 0) | v10.8 (seed 0) | 増分 |
|---|---:|---:|---:|
| events | 14,385 | 16,885 | +17% |
| paths records | 851,154 | 928,095 | +9% |
| baselines records | 911,877 | 1,098,672 | +20% |
| excess rows | 116,125 | 133,332 | +14% |
| multi_hop records | 328,936 | 347,371 | +6% |
| loops_2_hop | 711 | 711 | 0 (familiarity edge 不変) |
| loops_3_hop | 4,563 | 4,563 | 0 (同上) |
| 実行時間 | 114 秒 | 131 秒 | +15% |
| storage | 13.81 MB | 16.32 MB | +18% |

→ Small-World 構造 (loop_2/3) は **完全に不変** (Step B §4.2 で構造的に確定済、確認できた)。

---

## 2. bit-identity 検証

### 2.1 層 B (v10.7 baseline 不変性) — **PASS**

```
v10.7 files tracked: 222
PASS: v10.7 baseline 222 files 全て不変
```

→ smoke 前後で `developmental/v107/outputs/main/` 配下 222 ファイルの MD5 完全一致。**v10.8 が v10.7 出力を破壊していないこと確認**。

### 2.2 層 A (同 seed 2 回)

Step C で smoke レベルで PASS 確認済 (atom_introduction_event 単独)。Step F の peak_lag サブサンプリング (random_state=42 固定) も決定論。

→ 全機構統合での層 A は Step I main run で再確認予定。

---

## 3. storage 実測 (seed 0)

```
baselines_with_delta_seed0.parquet                10.66 MB
excess_change_seed0.parquet                        3.77 MB
relation_paths_seed0.parquet                       0.99 MB
source_events_seed0.parquet                        0.59 MB
multi_hop_paths_seed0.parquet                      0.26 MB
resonance_loops_seed0.parquet                      0.03 MB
decay_rate_seed0.parquet                           0.01 MB
peak_lag_curve_seed0.parquet                       0.01 MB
wave_patterns_seed0.parquet                        0.00 MB
TOTAL                                             16.32 MB
```

→ Step B 推定 72 MB/seed よりも大幅小 (parquet snappy 圧縮効果)。24 seeds 推定 **392 MB** (上限 6 GB の 6%)。

修正案 D (pulse 1/5 サブサンプリング) **不要**。

---

## 4. atom_introduction_event の波及への寄与

第 6 種 source_event 追加で:
- **path records +77K** (851K → 928K、+9%): atom event の source_cid は v10.6 top_k cid なので、relation_path の familiarity / Integration / temporal_coactivation がより集約的に計上
- **baseline records +187K** (912K → 1,099K、+20%): 各 atom event について 5 種 baseline を構築、増分大
- **excess rows +17K** (116K → 133K、+14%): per (event, path) 集計、atom event ごとに新規 row

→ atom_introduction_event は **path 経由で natural events と同じ計算ロジック** に乗る。v10.7 機構の流用は完璧に機能。

---

## 5. Step D 完了条件チェック

- [x] v107_event_aggregator + v108_atom_event_generator を統合 (16,885 events)
- [x] v107_path_analyzer 流用 (5 種 path、928,095 records)
- [x] v107_baseline_constructor 流用 (5 種 baseline + 6 量 × 3 windows delta)
- [x] v107_avalanche_monitor 流用 (multi_hop、loop、peak_lag、wave_pattern)
- [x] read-only / v108 出力 path 縛り維持
- [x] bit-identity 層 B PASS (v10.7 出力 222 files 不変)
- [x] 24 seeds 単一バッチ実行可能性 (131 秒/seed × 24 順次 = 52 分、並列 24 workers なら約 3-5 分)
- [x] storage 392 MB/24 seeds (上限 6%)

---

## 6. 出力ファイル

```
developmental/v108/
├── v108_post_process.py                  (orchestrator)
├── v108_step_d_report.md                 (本報告)
└── outputs/smoke/
    ├── source_events_seed0.parquet           (16,885 rows、6 種統合)
    ├── relation_paths_seed0.parquet          (928,095 rows)
    ├── baselines_with_delta_seed0.parquet    (1,098,672 rows)
    ├── excess_change_seed0.parquet           (133,332 rows)
    ├── multi_hop_paths_seed0.parquet         (347,371 rows)
    ├── resonance_loops_seed0.parquet         (5,274 rows)
    ├── decay_rate_seed0.parquet
    ├── peak_lag_curve_seed0.parquet          (1,010 rows)
    ├── wave_patterns_seed0.parquet           (10 rows)
    ├── atom_introduction_events_seed0.parquet (Step C 出力、separate file)
    └── post_process_run_summary.parquet
```

---

## 7. 残課題 (Step E-F で対処)

### 7.1 global activation 補正の未実装

Step E でこれから実装。current smoke 結果は **未補正** の baseline_excess_change。Step E 後に再 smoke で補正効果を確認。

### 7.2 v10.7 natural source_event baseline (新規 6 種目) の未実装

current smoke は v10.7 5 種 baseline のみ。Step E で v10.7 natural source_event との比較を追加実装し、Level 3.5 (introduced vs natural) の判定基盤を作る。

### 7.3 副次観察 3 件の未実装

Step F で:
- Whiteout (87/2,500 = 3.5% の同時刻多重発火 step を分析)
- Small-World 維持 (構造的に変化なしが確定済、記録のみ)
- 誤差分布 (atom × path × window で bimodality)

---

## 8. Step E 進行への申請

Step E (global activation 補正、`v108_global_activation_correction.py`) に進む許可を求めます。

実装方針:
1. **global_activation_factor 計算**:
   - 各 step で natural events のみカウント (atom_introduction_event 除外、即決 §2.4)
   - pulse + ingestion + alpha_birth + beta_birth + consciousness
   - 25,000 step × 24 seeds = 600K records
2. **正規化** (mean-0 / std-1 等):
   - factor を normalize して `normalized_factor` 列追加
3. **adjusted_baseline_excess_change** の計算:
   - 各 (event, path) で raw_excess - normalize(global_activation_factor(timestamp))
   - 既存 excess_change を拡張、追加列 `adjusted_*` を作成
4. **v10.7 natural source_event baseline** の集計:
   - v10.7 excess_change から source_event 別 mean delta を取得
   - atom_introduction_event の delta と差分計算 (Level 3.5 候補)
5. seed 0 smoke で動作確認

実行時間予想: 1-1.5 時間。

Step E 完了後、Step F (副次観察 3 件) に進む前に再度報告します。

24 seeds 単一バッチ厳守 (multiprocessing 24 並列、3 バッチ分割禁止)。

---

*以上、Step D 報告。Web Claude / Taka からの Step E 進行許可待ち。*
