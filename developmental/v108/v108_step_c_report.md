# v10.8 Step C 報告 — atom_event_generator 実装 + smoke

*作成*: 2026-05-07、Code A
*親*: `v108_environment_check_report.md` (Step B)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v108_atom_event_generator.py` を実装、25 atom × top 100 cid を seed 0 で **2,500 events、27 列、0.1 MB、0.15 秒** で smoke 生成、bit-identity 層 A PASS、case α 均等分散発火 (atom_index × 10 step ずらし) で同時刻多重発火を **87 step (3.5%) のみ** に抑制、Q/C 計算的減算 (Q-1 / C+1) 動作確認、WLD.artless 100 events に `reserved_label=wld_artless_pending` 付与済、Step D (source_event 第 6 種統合) 進行準備完了。

---

## 1. smoke 結果

| 指標 | 値 |
|---|---|
| seed 0 events | **2,500** (= 25 atom × 100 events) |
| 列数 | 27 (v10.7 source_event 互換 + atom メタ 4 + post_event 2) |
| size (parquet snappy) | **0.1 MB/seed** |
| 実行時間 | **0.15 秒/seed** |
| bit-identity 層 A | **PASS** (md5 完全一致、DataFrame equal OK) |
| reserved (WLD.artless) | 100 events (`wld_artless_pending`) |
| 24 seeds 推定 | events 60,000、size 2.4 MB、時間 4 秒 |

---

## 2. timestamp 均等分散 (案 α 確認)

### 2.1 atom_index 別の最初/最後 timestamp

```
atom_index 0 (BOD.ear):           100 → 24751 (100 events、間隔 ~250 step)
atom_index 1 (COG.learn):         110 → 24662
atom_index 2 (COM.silence):       120 → 24672
...
atom_index 9 (PER.hear):          190 → 24742
```

→ 各 atom は **base_offset = 100 + atom_index × 10** から開始、interval ~250 step。

### 2.2 同時刻多重発火

- `max events at same timestamp`: 4
- `events with > 1 atom at same step`: 87 (= 全 2,500 events の 3.5%)
- 残り 96.5% は **同時刻発火なし**

→ 案 α の同時刻発火回避は成功。Whiteout 副次観察 (Step F) で 87 多重発火 step の atom 相関を見ることになる。

---

## 3. 出力 schema (27 列)

```
# v10.7 source_event 互換 (Step B 即決 §2.1)
event_source_type    object   "atom_introduction_event"
source_cid           int64    top_k 100 cid から
timestamp            int64    案 α 均等分散
event_id             object   "{seed}_atom_{i}"
seed                 int64    0-23

# atom メタ情報 (新規 4 列)
atom_id              object   "PER.sound" 等の 25 atom
atom_index           int64    0-24
top_k_rank           int64    1-100
atom_sim_score       float64  v10.6 cid_atom_sim_matrix 値
reserved_label       object   "" or "wld_artless_pending"

# pre_event_state (v10.7 attach_pre_event_state 流用、12 列)
birth_step           int64
lifespan_so_far      int64
n_core_member        int64
v14_q0               int64
final_state          object
host_lost_step       float64 (NaN許容)
reaped_step          float64 (NaN許容)
R_familiarity_pre    float64
Q_pre                float64
C_pre                float64
window_value         int64
C_at_window_end      float64
Q_remaining_at_window_end float64
n_alphas_pre         int64
n_observed_pre       int64

# post_event_state (新規、計算的減算)
Q_after_atom_intro   float64  Q_pre - 1 (即決 §2.3)
C_after_atom_intro   float64  C_pre + 1
```

合計 27 列。post_event_state は **post-process 計算的減算** で実 v10.5 ledger 不変。

---

## 4. Q/C 計算的減算の動作確認

サンプル (seed 0、最初の 5 events):

| Q_pre | Q_after_atom_intro | delta_Q | C_pre | C_after_atom_intro | delta_C |
|---:|---:|---:|---:|---:|---:|
| 11.0 | 10.0 | -1.0 | 0.0 | 1.0 | +1.0 |
| 7.0 | 6.0 | -1.0 | 3.0 | 4.0 | +1.0 |
| 3.0 | 2.0 | -1.0 | 4.0 | 5.0 | +1.0 |
| 8.0 | 7.0 | -1.0 | 18.0 | 19.0 | +1.0 |
| 23.0 | 22.0 | -1.0 | 25.0 | 26.0 | +1.0 |

→ **Q -1 / C +1 が全 events で固定減算** 動作確認。balance_decisions.cognition と完全に同等のコスト。

---

## 5. 25 atom 発火確認

| atom_index | atom_id | n_events | reserved |
|---:|---|---:|---|
| 0 | BOD.ear | 100 | |
| 1 | COG.learn | 100 | |
| 2 | COM.silence | 100 | |
| 3 | EXS.being | 100 | |
| 4 | EXS.nonbeing | 100 | |
| 5 | FND.timeless | 100 | |
| 6 | FND.transformation | 100 | |
| 7-14 | PER 系 8 atom (feel/fragrance/hear/see/smell/sound/soundless/taste) | 各 100 | |
| 15-17 | PRP 系 3 atom (bright/deep/sharp) | 各 100 | |
| 18-20 | SOC 系 3 atom (city/nation/public) | 各 100 | |
| 21 | TIM.appear | 100 | |
| **22** | **WLD.artless** | **100** | **wld_artless_pending** |
| 23 | WLD.culture | 100 | |
| 24 | WLD.technique | 100 | |

→ 25 atom × 100 events = 2,500 events、WLD.artless 100 events のみ reserved label。

---

## 6. unique source_cid (top_k 100 cid 動作確認)

seed 0 の全 cid 数 = 228、atom_introduction_events で使用された unique source_cid = **224** (= 228 中 224 が少なくとも 1 つの atom の top 100 に入った)。

→ 25 atom × 100 cid = 2,500 selections だが多数 cid が複数 atom に重複出現。実際の unique cid は 224。

---

## 7. Step C 完了条件チェック

- [x] 25 atom × top 100 cid 抽出 (cid_atom_sim_matrix 由来)
- [x] 案 α 均等分散発火 (atom_index × 10 step ずらし、同時刻多重 87/2500 = 3.5%)
- [x] v10.7 source_event 互換スキーマ (即決 §2.1)
- [x] atom メタ 4 列 (atom_id, atom_index, top_k_rank, atom_sim_score)
- [x] reserved_label (WLD.artless 100 events のみ)
- [x] Q/C 計算的減算 (Q-1, C+1、固定値、balance_decisions.cognition 同等)
- [x] 実 ledger 不変 (post-process のみ、層 B 維持の前提)
- [x] bit-identity 層 A PASS (md5 完全一致)
- [x] 24 seeds 推定 60,000 events、size 2.4 MB、時間 4 秒

---

## 8. 出力ファイル

```
developmental/v108/
├── v108_atom_event_generator.py
├── v108_step_c_report.md
└── outputs/smoke/
    └── atom_introduction_events_seed0.parquet  (2,500 rows × 27 cols, 0.1 MB)
```

---

## 9. Step D 進行への申請

Step D (source_event 第 6 種統合 + v10.7 機構流用、`v108_post_process.py`) に進む許可を求めます。

実装方針:
1. **v10.7 機構の流用**:
   - v107_event_aggregator: 5 種 source_event (pulse/ingestion/α/β/c_conversion) 取得
   - 第 6 種として atom_introduction_event を追加
   - 統合した source_events_seed*.parquet を v108 ディレクトリに保存
2. **v107_path_analyzer 流用**: 5 種 relation_path で target 候補を抽出 (atom_introduction_event の source_cid 経由)
3. **v107_baseline_constructor 流用**: 5 種 baseline + delta 集計
4. **v107_avalanche_monitor 流用**: peak_lag、共鳴ループ、減衰率
5. **新規**: v10.7 natural source_event baseline (= v10.7 出力の集計値を再利用)
6. seed 0 smoke で動作確認

実行時間予想: 1.5-2 時間 (主に v10.7 機構の 26 種 source_event 拡張で実行時間増)。

Step D 完了後、Step E (global activation 補正) に進む前に再度報告します。

24 seeds 単一バッチ厳守 (multiprocessing 24 並列、3 バッチ分割禁止)。

---

*以上、Step C 報告。Web Claude / Taka からの Step D 進行許可待ち。*
