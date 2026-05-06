# v10.7 Code A 認識確認文書

*作成*: 2026-05-06、Code A
*親*: `v107_implementation_brief.md` (本リポジトリ未配置、Web Claude 保有)
*目的*: 実装着手前の認識確認 (指示書 §0 の 10 項目を含む)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

v10.7 implementation brief を精読、実環境を事前確認した結果 **設計の甘さ 6 点 + 重大ブロッカー 2 点 (attention 経路の構築データが不在、ストレージ予算 31x 超過)** を検出、本指示書のまま実装着手すると後段で破綻する箇所が複数あるため、Web Claude / Taka に修正案の確認を取ってから着手する必要がある。

---

## 1. 主題の理解 (項目 1)

**v10.7 の主題**: post-process として ESDE Genesis 系内部の **5 種 source_event (pulse / ingestion / alpha_formation / beta_formation / c_conversion)** を起点に、**5 種 candidate_target_set (familiarity / attention / Integration / temporal_coactivation / matched 経路)** を **5 種ベースライン群** に対する `baseline_excess_change` として定量化、因果候補の **階層化 Level 1-3 (co-occurrence / path-enriched / source-specific)** + **peak_lag 測定** + **アバランシェ防止 (3 hop, 200 MB/seed)** + **構造語徹底** + **WLD.artless 除外** + **二層 bit-identity 検証** を達成する観察解析。物理層 frozen は post-process で自動保証。

→ 認識は明確。実装パスは見える。ただし §3 以下に挙げる設計の甘さ複数の解決が必要。

---

## 2. 5 種 source_event の定義の判定 (項目 2)

実環境確認 (seed 0) での event 数:

| event 種別 | 既存ログ | 件数/seed | 指示書記載との整合 |
|---|---|---|---|
| pulse | `pulse/pulse_log_seed*.csv` | 12,530 | ✓ 一致 |
| ingestion | `ingestion/ingestion_events_seed*.csv` | 155 | ✓ 列名は `observer_cid`、指示書の "eater_cid" と異なるが OK |
| alpha_formation | `integration/alpha_lifecycle_log_seed*.csv (event_type='birth')` | 424 | ✓ 一致 (member_cids 列に複数 cid 含む) |
| beta_formation | `integration/beta_lifecycle_log_seed*.csv (event_type='birth')` | 239 | ✓ 一致 |
| **c_conversion** | 指示書: `balance/c_trajectory_seed*.csv (delta_C > 0 の瞬間)` | **誤り** | ✗ |

### 2.1 c_conversion ソースの設計甘さ (重要)

指示書の `c_trajectory.delta_C > 0` は **window 単位の集計値の差分** で、per-event の瞬間ではない。実態:
- `balance/c_trajectory_seed0.csv`: window 単位 (50 windows × 平均 21 cid = 1062 行/seed)、`C_at_window_end` の差分 → `delta_C > 0` events 582 件 (= 偽の event 件数)
- `balance/balance_decisions_seed0.csv`: **per-event** (3,483 件/seed)、`decision == 'consciousness'` で **155 件** が真の c_conversion event
- スキーマ: `seed, window, step, global_step, observer_cid, contacted_cid, decision, c_after, q_remaining_after, ...`

→ **修正案**: c_conversion source は `balance/balance_decisions_seed*.csv` の `decision == 'consciousness'` 行を採用。timestamp は `step` 列。observer_cid が source_cid。

合計 source_events (修正後): pulse 12,530 + ingestion 155 + alpha_birth 424 + beta_birth 239 + consciousness 155 = **13,503 events/seed × 24 seeds = 約 324,072 events**。

---

## 3. 5 種 candidate_target_set 構築の判定 (項目 3)

### 3.1 各経路の構築可能性

| relation_path_type | 構築データ | 状態 |
|---|---|---|
| familiarity | `network/fam_edges_seed*.csv` (1,029 edges/seed) | ✓ 構築可能 |
| **attention** | per_subject に `last_attention_size` (集計値) のみ、**個別 partner ログ無し** | **✗ 構築不可** |
| Integration | `integration/alpha_lifecycle_log` の event-by-event | ✓ ただし要再構築 (snapshot は run 終了 1 step のみ) |
| temporal_coactivation | `pulse_log` の time-window 集計 | ✓ 構築可能 |
| matched_baseline | per_subject + audit の n_core / age / final_state | ✓ 構築可能 |

### 3.2 attention 経路の重大ブロッカー (1)

per_subject の attention 関連列は `last_attention_size` のみ (集計スカラー)。**「source_cid の attention map 内の cid」** を取得するための **partner-by-partner attention データが ESDE 出力に存在しない**。

確認した v10.5 出力ディレクトリ全部:
- `attention` 名のディレクトリ・ファイル: なし
- per_subject の attention 関連列: `last_attention_size`、`v14_virtual_attention_entries`、`v14_virtual_attention_sum` (いずれも集計値)
- per-cid x per-partner の attention map 個別ログ: **存在しない**

→ **修正案 A**: attention 経路を v10.7 範囲外にし、4 種 relation_path_type で進める
→ **修正案 B**: ESDE engine を改修して per-cid x per-partner attention map を出力する (= post-process の前提を超える、規律違反)
→ **修正案 C**: salience_event_log (3,114 events/seed、observer_cid → candidate_cid のペア) を「擬似 attention」として代替

修正案 C が現実的。salience event は「observer cid が candidate cid を観察した記録」で attention に近い意味。判断要 Web Claude / Taka。

### 3.3 Integration 経路の再構築

`alpha_membership_log_seed*.csv` は **run 終了時の 1 step snapshot のみ** (27 行/seed、step=25000)。per-source_event の時点で「同 α 内の cid」を取るには `alpha_lifecycle_log` の event-by-event を時系列に集計して membership state を再構築する必要。

実装は v10.6 per-pulse trajectory で同様の処理あり (`_expand_alpha_membership_to_events`) → 流用可能。

---

## 4. 5 種ベースライン群の構築判定 (項目 4)

### 4.1 各ベースラインの構築可能性

| ベースライン名 | 定義 | 構築可能性 |
|---|---|---|
| unrelated_baseline | familiarity / attention / Integration の **全てで非接続** | ✗ attention 不在で部分緩和必要 |
| same_step_random_baseline | 同 step で動いている任意 cid | ✓ pulse_log で実装可能 |
| matched_baseline | 同 n_core / 同 age / 同 hosted | ✓ per_subject で実装可能 |
| same_integration_low_familiarity_baseline | 同 Integration 内 + familiarity 下位 25% | ✓ 構築可能 |
| high_familiarity_outside_integration_baseline | familiarity 上位 25% + Integration 外 | ✓ 構築可能 |

### 4.2 unrelated_baseline の cid 不足懸念

「全関係で非接続」を厳密に取ると、各 source_cid に対し:
- familiarity edge を持たない (= fam_edges で from/to に含まれない)
- 同 α / 同 β に所属しない

→ 実 cid 数で確認: 28-30% の cid が「fam edge 含」、Integration 内 30-40% → unrelated は 30-40% 程度 (≈ 60-90 cid/seed)。**cid 不足にはならない** が relation_path との対称性が崩れる可能性あり。

→ 緩和案: 緩い unrelated (fam edge **強度 < 5** + 同 α 内なし) で実装。

---

## 5. アバランシェ防止 + ストレージ予算判定 (項目 5)

### 5.1 ストレージ予算の重大ブロッカー (2)

指示書 §6.4: **1 seed あたり 200 MB**、24 seeds で 4.8 GB。

実環境見積もり (seed 0):
- source_events: 13,503/seed
- target/event: 100 (5 path × 20 cid)
- delta fields: 6 (Q, C, familiarity_max, n_alphas, n_observed, pulse_count)
- window fields: 4 (immediate, short, medium, peak_lag)
- record schema rough: 200 bytes/cell

**計算**: 13,503 × 100 × 6 × 4 × 200 bytes = **約 6,181 MB/seed → 200 MB 上限の 31x 超過**

24 seeds で **約 148 GB** に膨張。

### 5.2 修正案 (3 通り、選択)

**修正案 D**: source_event を絞る
- pulse 92% の混雑が原因 → pulse を **時間サブサンプリング** (例: 10 pulse ごとに 1 抽出 = 1/10) で 1,253 events/seed
- 全 source_events 約 2,200/seed → ストレージ 約 1 GB/seed (5x まだ超過)

**修正案 E**: schema 圧縮 + parquet
- 200 → 8 bytes/cell (float32 + compression) で 25x 縮小
- 13,503 × 100 × 6 × 4 × 8 = **約 247 MB/seed** (200 MB 上限近い、許容)
- **推奨**: parquet 出力 + 数値列のみ + atom 名は別 dim_table で管理

**修正案 F**: target 絞り
- 100 target/event を 30 target/event (上位 6 cid × 5 path)
- 約 73 MB/seed = OK
- ただし relation_path の表現力が落ちる

**Code A 推奨**: 修正案 E + 修正案 D の併用 = pulse サブサンプリング (1/5 = 2,506 pulses/seed) + parquet 圧縮で 50 MB/seed 以下。

### 5.3 アバランシェ 3 hop の現実性

3 hop 計算は graph traversal で可能。1 seed × 13,503 events × 平均 100 target × 3 hop = 約 4 M graph queries → 数秒/seed。問題なし。

### 5.4 peak_lag 1 step 単位の計算量

指示書 §5.2: peak_lag は 1 step 単位で同定 (lag 1-1000)。各 source_event × 100 target × 1000 lag = 100K 計算/event × 13,503 events = **13.5 億計算/seed × 24 = 324 億計算 → 重い**。

→ **修正案 G**: peak_lag 解像度を **10 step bin** に粗く (lag 10, 20, ..., 1000 で 100 値) → 1.35 億計算/seed、数分/seed。

---

## 6. 構造語の置換規則の混乱可能性 (項目 6)

### 6.1 規則の整理

指示書 §8.1 の置換は明確。1 つだけ補足:

| 仮名 | 構造語 | 私の解釈 |
|---|---|---|
| 発火 | source_event | OK |
| 波及 | post_event_path_enriched_delta | OK、長いので CSV 列名では `delta_post_event_<field>` 推奨 |
| 影響 | baseline_excess_change | OK |
| 同期 | temporal_coactivation_enrichment | OK、ただし「経路」と「同期 metric」が同じ語 (`temporal_coactivation_*`) で重複 |
| 経路 | relation_path_type | OK |
| 周辺 | candidate_target_set | OK |
| 意識 | c_conversion_event | OK |

→ 実装上の混乱は限定的。`temporal_coactivation` が「relation_path 名」と「効果 metric 名」両用なので、列名で `relation_temporal_coactivation` と `effect_temporal_coactivation_enrichment` のように分離する。

---

## 7. 環境チェック結果 (項目 7)

### 7.1 利用可能データ

| データ | パス | 状態 |
|---|---|---|
| pulse_log | `developmental/v105/diag_v105_main_v2/pulse/pulse_log_seed*.csv` | ✓ |
| ingestion | `ingestion/ingestion_events_seed*.csv` | ✓ (155 events/seed) |
| alpha/beta lifecycle | `integration/{alpha,beta}_lifecycle_log_seed*.csv` | ✓ |
| balance_decisions (c_conversion 用) | `balance/balance_decisions_seed*.csv` | ✓ (155 consciousness/seed) |
| network/fam_edges | `network/fam_edges_seed*.csv` | ✓ (1,029 edges/seed) |
| salience_event_log (attention 代替候補) | `salience/salience_event_log_seed*.csv` | ✓ (3,114 events/seed) |
| atom_profiles_cache (v10.6 流用) | `developmental/v106/outputs/main/atom_profiles_cache.npz` | ✓ |
| per_subject + audit | `subjects/per_subject_seed*.csv` + `audit/per_subject_audit_seed*.csv` | ✓ (n_core_member 等) |

### 7.2 不在データ (= 設計の甘さ)

| データ | 影響 |
|---|---|
| **per-cid x per-partner attention map** | attention 経路構築不可 |
| **alpha_membership state per-step** | snapshot のみ、event-by-event で再構築必要 |

### 7.3 ライブラリ

- pandas 2.3, numpy 2.3, scipy 1.16, sklearn 1.7 (v10.6 と同じ環境): ✓
- Kruskal-Wallis 検定 (Level 3): scipy.stats.kruskal で利用可
- Parquet 出力: pyarrow 利用可

---

## 8. 設計の甘い部分 (項目 8、Code A 視点で 6 点)

### 8.1 重大ブロッカー (2 点、修正必須)

**A. attention 経路の構築データ不在** (§3.2)
→ 修正案 A/B/C のいずれかを採択 (Web Claude / Taka 判断)

**B. ストレージ予算 31x 超過** (§5.1)
→ 修正案 D + E (pulse サブサンプリング + parquet 圧縮) を Code A は推奨

### 8.2 設計修正必要 (4 点)

**C. c_conversion source の誤り**: 指示書 `c_trajectory.delta_C > 0` は誤り、`balance_decisions.decision == 'consciousness'` が正解。

**D. alpha_membership 再構築必要**: snapshot のみで per-source_event 時点を取れず、`alpha_lifecycle` event-by-event 再構築が必要。

**E. peak_lag 1 step 単位は計算過大**: 10 step bin に粗い解像度を採用すべき。

**F. unrelated_baseline 厳密性**: 「全関係で非接続」を厳密にすると attention 不在で実質 familiarity + Integration の 2 軸でしか定義できない。緩和案で対応。

### 8.3 文書整合性 (1 点)

**G. v107_phase_design.md が本リポジトリに不在**: 親資料として参照する記載があるが、実態としては Web Claude が手元保持のみ。本ファイル群を発展させる際の参照は「指示書記載」で代用するか、実体ファイルを repo に commit するか判断要。

### 8.4 v10.6 birth_step バグの遡及影響

v10.6 step10 解析で発見した `birth_step = birth_window * WIN_LEN` のバグは、v10.7 で再利用する場合は **`pulse_log の最初 t`** から取得することで修正可能 (v10.6 step10 / per-event で既に修正済の手法を流用)。

---

## 9. 実装予想時間 (項目 9)

| ステップ | 予想時間 |
|---|---|
| 認識確認 (本文書) | **完了** (本文書、約 1 時間) |
| 環境チェック詳細 (`v107_environment_check_report.md`) | 30 分-1 時間 |
| `v107_event_aggregator.py` (5 種 source_event) | 1.5 時間 |
| `v107_path_analyzer.py` (4 種 relation_path、attention は代替方式に依存) | 2 時間 |
| `v107_baseline_constructor.py` (5 種 baseline) | 1.5 時間 |
| `v107_avalanche_monitor.py` (graph traversal、減衰、ループ) | 1 時間 |
| `v107_post_process.py` (主処理 orchestration) | 2 時間 |
| smoke test (seed 0) | 30 分 |
| **修正イテレーション** | 1 時間 |
| main run (24 seeds 単一バッチ) | 1-2 時間 (storage と peak_lag 計算量次第) |
| Level 1-3 reports + 総括 report | 2 時間 |

**合計**: 13-16 時間 (= 1.5-2 日相当の連続作業)

ストレージ修正案 D+E を採択しない場合、main run が破綻して再 run になる可能性あり。

---

## 10. Web Claude / Taka への質問・確認事項 (項目 10)

### 10.1 即決を要する判断 (実装着手前に確定)

1. **attention 経路の代替方式**: A 4 種で進める / B engine 改修 / **C salience_event_log を擬似 attention に流用** のいずれを採用するか
2. **ストレージ修正案**: D pulse サブサンプリング (1/5) / **E parquet 圧縮** / F target 絞り、または併用
3. **peak_lag 解像度**: 1 step / **10 step bin** / 100 step
4. **c_conversion source**: `balance_decisions.decision == 'consciousness'` で確定して良いか
5. **unrelated_baseline 緩和**: attention 不在のため 2 軸 (familiarity 強度 < 5 + 同 α 内なし) で定義

### 10.2 実装中の判断 (smoke 後に確認)

6. relation_path 重複の扱い: 1 cid が複数 path に該当するとき (重複行 OK か、main path 1 つに集約か)
7. WLD.artless 除外の具体ポイント: target cid の atom rank_1 が WLD.artless の場合の扱い (集計から除外 / 補助記録として残す)
8. bit-identity 層 B (v10.6 baseline 比較) の実装手順: v10.6 出力の MD5 hash 一覧をどこから取得するか

### 10.3 v10.7 範囲確認

9. v107_phase_design.md を repo に commit するか (現状 Web Claude のみ保有)
10. salience_event を attention 代替で使う場合、salience は別の event source として扱うか、attention 経路として扱うか (両用注意)

---

## 11. Code A 推奨の進行手順 (修正版)

指示書 §11 をベースに、§8 の指摘を反映:

```
Step A: 本文書を Web Claude / Taka が確認、§10 の判断 5 項目 (即決) を確定
Step B: Code A が修正された設計で実装着手
Step C: 環境チェック報告 (実装の前提となるパス・列名・ファイルの確定)
Step D: 5 種 source_event aggregator → smoke (seed 0)
Step E: 5 種 relation_path constructor → smoke
Step F: 5 種 baseline + 4 種 delta 集計 → smoke
Step G: アバランシェ防止 + peak_lag → smoke
Step H: 全機構統合 smoke (seed 0、storage 確認、bit-identity 検証)
Step I: smoke 結果を Taka に報告、main run 進める判定
Step J: 24 seeds main run
Step K: cross-seed 解析、Level 1-3 reports 作成
Step L: 完了報告
```

各 Step で完了報告し、Web Claude / Taka 確認を取る。

---

## 12. 完了条件チェック (本文書の)

- [x] §0.1 の 10 項目を網羅
- [x] 主題の理解 (3-5 行)
- [x] 5 種 source_event 定義の判定 + 修正案
- [x] 5 種 candidate_target_set の構築方針判定 + ブロッカー指摘
- [x] 5 種ベースラインの構築可能性判定
- [x] アバランシェ + ストレージの現実性判定 + 修正案
- [x] 構造語規則の混乱判定
- [x] 環境チェック結果
- [x] 設計の甘い部分 (6 点)
- [x] 実装予想時間
- [x] 質問事項 (10 項目)

---

*以上、Code A による v10.7 実装着手前認識確認文書。Web Claude / Taka の §10.1 即決事項 5 項目を待って実装着手します。*
