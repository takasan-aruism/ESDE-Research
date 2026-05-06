# v10.7 Step C 報告 — source_event aggregator 実装 + smoke

*作成*: 2026-05-07、Code A
*親*: `v107_implementation_brief.md` + `v107_environment_check_report.md` (Step B)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v107_event_aggregator.py` を実装、5 種 source_event を統合した 21 列 DataFrame を seed 0 で生成 (**14,385 events、0.43 MB、0.15 秒**)、bit-identity 層 A (2 回実行同一性) PASS、pre_event_state 7 量 (Q_pre / C_pre / R_familiarity_pre / n_alphas_pre / n_observed_pre / lifespan_so_far / n_core_member) を merge_asof で添付済み、Step D (relation_path constructor) に進む準備完了。

---

## 1. smoke 実行結果

| 指標 | 値 |
|---|---|
| seed 0 total events | **14,385** |
| 内訳 (event_source_type) | pulse 12,530 / alpha_formation 1,067 / beta_formation 478 / ingestion 155 / c_conversion 155 |
| columns | 21 |
| size (parquet snappy) | **0.43 MB/seed** |
| 実行時間 | **0.15 秒/seed** |
| bit-identity 層 A | **PASS** (md5 完全一致、DataFrame equal OK) |

### 1.1 Step B 推定との差異

| event 種別 | Step B 推定 | smoke 実測 |
|---|---:|---:|
| pulse | 12,530 | 12,530 ✓ |
| ingestion | 155 | 155 ✓ |
| alpha_formation (birth event) | 424 | **1,067** ← member 展開後 |
| beta_formation (birth event) | 239 | **478** ← member 展開後 |
| c_conversion | 155 | 155 ✓ |
| **total** | 13,503 | **14,385** |

→ alpha/beta_formation は **birth event × 平均 member 数** で展開されるため Step B の件数とは異なる。**指示書 §2.1 の意図 (member_cids 展開) と一致**。

### 1.2 24 seeds 推定 (smoke ベース)

14,385 × 24 ≈ **345,240 events** (Step B 推定 386,655 から微減、これは seed ごとの member 数のばらつきが反映)。

ストレージ予想:
- 0.43 MB/seed × 24 = **約 10 MB** (parquet snappy 圧縮効果大)
- Step B で 295 MB/seed と見積もったのは target × delta 展開後の総容量、source_events 単独はずっと小

→ 最終 storage は Step D-F の target/delta/baseline 展開後に Step G で実測。

---

## 2. 出力 schema (21 列)

```
event_source_type        object   pulse / alpha_formation / beta_formation / ingestion / c_conversion
source_cid               int64    主体 cid
timestamp                int64    step
ref_index                int64    元 event の参照 ID (alpha/beta_id 等)
seed                     int64    0-23
event_id                 object   "{seed}_{auto_increment}"
birth_step               int64    pulse_log 最初 t (v10.6 birth_step バグ回避済)
lifespan_so_far          int64    timestamp - birth_step (clip 1)
n_core_member            int64    audit 由来 (固定値)
v14_q0                   int64    audit 由来 (出生時 Q)
final_state              object   hosted / ghost / reaped
host_lost_step           float64  null=7846 (hosted のみ NaN)
reaped_step              float64  null=13246 (reaped 28 cid のみ値)
R_familiarity_pre        float64  pulse_log 直近 R_familiarity (merge_asof backward)
Q_pre                    float64  balance_decisions Q_at_decision 直近 (fallback v14_q0)
C_pre                    float64  balance_decisions C_at_decision 直近 (fallback 0)
window_value             int64    timestamp/500 + 19
C_at_window_end          float64  c_trajectory 同 window 値
Q_remaining_at_window_end float64 同上 (fallback v14_q0)
n_alphas_pre             int64    alpha_lifecycle event 累積 (merge_asof)
n_observed_pre           int64    salience_event observer 累積
```

### 2.1 pre_event_state 統計 (seed 0)

| 量 | mean | std | min | 25% | 50% | 75% | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q_pre | 7.10 | 8.23 | 0 | 0 | 5 | 10 | 34 |
| C_pre | 20.14 | 17.63 | 0 | 4 | 18 | 34 | 58 |
| R_familiarity_pre | -0.05 | 1.12 | -5.79 | -0.72 | -0.26 | 0.37 | 20 |
| n_alphas_pre | 12.80 | 15.04 | 0 | 0 | 6 | 23 | 59 |
| n_observed_pre | 27.79 | 30.24 | 0 | 5 | 14 | 45 | 134 |
| lifespan_so_far | 5,747 | 6,533 | 1 | 700 | 2,750 | 9,350 | 24,950 |
| n_core_member | 3.74 | 1.30 | 2 | 2 | 4 | 5 | 5 |

→ R_familiarity が負の値を取る (-5.79 〜 +20) のは pulse_log の R_familiarity 列が **delta-like な signed 量** であることに由来 (v10.6 で確認済)。これは relation_path の familiarity 強度と異なる量なので、Step D で familiarity 経路構築時には `network/fam_edges` の `familiarity` 値 (正の量) を使う。

---

## 3. bit-identity 層 A 検証

```
run A md5: fed2aa6d1b9f8512664ba29947fd21c6
run B md5: fed2aa6d1b9f8512664ba29947fd21c6
identical: True
pd.testing.assert_frame_equal: OK
```

→ 同 seed 2 回実行で完全一致、非決定性なし。

層 B (v10.6 baseline 不変性) は Step G (統合 smoke) で全機構動作後に実施する予定。

---

## 4. 実装で確認した事実 (Step D に活かせる情報)

### 4.1 alpha_formation の member 数

24 seeds 全体 alpha_birth 13,881 events → member 展開後 **約 1,067 × 24 ≈ 25,608 records**。

per-event の member 数: 平均 2.5 (seed 0: 1067/424 = 2.52)。

### 4.2 c_conversion の補助情報

balance_decisions の `decision == 'consciousness'` 行には:
- observer_cid, contacted_cid (relation_path 構築の有用情報)
- Q_at_decision, C_at_decision, q_remaining_after, c_after (effect 測定の直接ソース)

→ Step E (delta 集計) で q_remaining_after - Q_at_decision を直接 delta_Q として使える。

### 4.3 R_familiarity_pre の意味

pulse_log の `R_familiarity` 列は **per-pulse の familiarity 信号 (signed)** で、relation_path の familiarity 強度 (network/fam_edges の正値) とは異なる量。役割を区別する:

- pre_event_state の R_familiarity_pre: 直近 pulse の familiarity 信号 (cid の動的状態)
- relation_path "familiarity": fam_edges の正の familiarity 強度 (cid 間の関係強度)

---

## 5. Step C 完了条件チェック

- [x] 5 種 source_event の統合 DataFrame 構築 (14,385 rows)
- [x] event_id auto-increment (`{seed}_{idx}`)
- [x] pre_event_state 7 量を merge_asof で添付
- [x] alpha/beta_formation の member_cids 展開 (1067/478)
- [x] birth_step バグ回避 (pulse_log 最初 t)
- [x] parquet 出力 (snappy 圧縮、0.43 MB/seed)
- [x] read-only 縛り (V105_ROOT 配下のみ)
- [x] 出力 v107 path 縛り (assert_output_under_v107)
- [x] bit-identity 層 A PASS (md5 一致)

---

## 6. 出力ファイル

```
developmental/v107/
├── v107_event_aggregator.py            (本実装)
├── v107_step_c_report.md               (本報告)
└── outputs/smoke/
    ├── source_events_seed0.parquet      (14,385 rows × 21 cols)
    └── source_events_run_summary.parquet (1 row summary)
```

---

## 7. Step D 進行への申請

Step D (5 種 relation_path constructor、`v107_path_analyzer.py`) に進む許可を求めます。

実装方針:
1. 各 source_event について 5 種 relation_path で target_cid を取得:
   - **familiarity**: `network/fam_edges` から 1-hop 接続 cid (上位 strength)
   - **attention_via_salience**: salience_event_log の (observer_cid → candidate_cid) 集計
   - **Integration**: alpha_lifecycle / beta_lifecycle event-by-event 再構築で同 α/β 内 cid
   - **temporal_coactivation**: pulse_log time-window 集計 (lag ≤ 100 step)
   - **matched_baseline**: 同 n_core / age / final_state の cid (baseline 兼用)
2. 1 source_event あたり 各 path 上位 20 cid (relation_strength 順)
3. アバランシェ防止 hop 計算は Step F で実装、Step D ではまず 1-hop のみ
4. seed 0 で smoke、出力件数と各 path の cid 数を確認

実行時間予想: 1.5-2 時間。

Step D 完了後、Step E (baseline + delta) に進む前に再度報告します。

---

*以上、Step C 報告。Web Claude / Taka からの Step D 進行許可待ち。*
