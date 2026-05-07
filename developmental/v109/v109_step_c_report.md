# v10.9 Step C 完了報告 — atom_event_generator (A2 + B3)

*作成*: 2026-05-08、Code A
*実装ファイル*: `developmental/v109/v109_atom_event_generator.py`
*出力*: `developmental/v109/outputs/smoke/atom_introduction_events_{A2,B3}_seed0.parquet`
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

A2 (Q -2 / C +2、top_k 100) と B3 (random cid、Q -1 / C +1) の atom_event_generator を v10.8 拡張で実装、seed 0 smoke で **bit-identity 層 A (同 seed 2 回再現) ✓、層 B (v10.9 A2 と v10.8 A1 の (atom, cid, timestamp) セット完全一致) ✓**、A2 と B3 ともに 2,500 events、Q/C コスト delta 値正常、B3 は seed 内 228 cid からの random 100 で per-atom 重複なし、Step D (baseline 再計算 A2 + B3) 進行準備完了。

---

## 1. 実装内容

### 1.1 v10.9 拡張点 (v10.8 atom_event_generator からの差分)

| 項目 | v10.8 | v10.9 |
|---|---|---|
| condition_id 列 | なし | あり (A2 / B3 / 後続 C2) |
| Q/C コスト | 固定 (-1 / +1) | 条件別 dict (CONDITIONS) |
| cid 選定方法 | top_k 100 のみ | top_k_100 / random_100 切替 |
| event_id 形式 | `{seed}_atom_{i}` | `{seed}_{condition_id}_atom_{i}` |
| 出力ファイル名 | `atom_introduction_events_seed{N}.parquet` | `atom_introduction_events_{cond}_seed{N}.parquet` |

### 1.2 流用元 (v10.8 import)

```python
from v108_atom_event_generator import (
    TARGET_ATOMS, RESERVED_ATOM, RESERVED_LABEL,
    RUN_END_STEP, EVENTS_PER_ATOM, ATOM_INDEX_STEP_OFFSET,
    schedule_atom_event_timestamps,  # timing は v10.8 と同じ
    extract_top_k_cids,              # top_k_100 用
)
from v107_event_aggregator import attach_pre_event_state
```

→ 25 atom 一覧、timestamp 均等分散ロジック (atom_index × 10 step ずらし)、pre_event_state 添付は v10.7/v10.8 完全流用。

### 1.3 新規実装

- `extract_random_cids(seed, atoms, n=100)`: seed 内全 cid から **rng_seed = 1_090_000_300 + seed** で 100 個 random 選定 (再現性担保)
- `select_cids_for_condition(seed, atoms, condition_id)`: cid_selection 方針切替
- `generate_atom_events_for_condition(...)`: condition_id 列付与版
- `attach_states_for_condition(...)`: condition 別 Q/C cost 適用

---

## 2. smoke 結果 (seed 0、A2 + B3)

```
v10.9 atom_event_generator - mode=smoke, seeds=[0], conditions=['A2', 'B3']
  TARGET_ATOMS: 25 (incl. WLD.artless reserved)
  TOP_K: 100, EVENTS_PER_ATOM: 100
  [A2] Q -2 / C +2: cid_selection=top_k_100
  [B3] random cid: cid_selection=random_100

  seed=0 cond=A2: events=2500, atoms=25, unique_cids=224, reserved=100, t_range=100-24753, size=0.101MB
  seed=0 cond=B3: events=2500, atoms=25, unique_cids=228, reserved=100, t_range=100-24753, size=0.086MB

DONE  total elapsed = 0.27s
```

### 2.1 数値検証

| 指標 | A2 | B3 |
|---|---:|---:|
| n_events | 2,500 | 2,500 |
| n_atoms | 25 | 25 |
| unique_cids | 224 | 228 (= seed 内全 cid) |
| WLD.artless reserved | 100 | 100 |
| timestamp range | 100-24,753 | 100-24,753 |
| Q delta (after - pre) | **-2 全件** | **-1 全件** |
| C delta (after - pre) | **+2 全件** | **+1 全件** |
| sim_score NaN ratio | 0% | 100% (random なので NaN) |
| per-atom unique cid 数 | (top_k 重複) | **100 全件** (replace=False OK) |

→ 全指標が想定通り。

---

## 3. bit-identity 検証

### 3.1 層 A (同 seed 同条件で 2 回生成して一致)

| 条件 | 結果 |
|---|---|
| A2 (seed 0 × 2 回) | **完全一致 (event_id × source_cid × timestamp × atom_id)** ✓ |
| B3 (seed 0 × 2 回) | **完全一致** ✓ |

→ B3 の random も rng_seed 固定で完全再現。

### 3.2 層 B (v10.9 A2 と v10.8 A1 の構造同一性)

```
v10.8 A1 (atom_id, source_cid, timestamp) keys: 2,500
v10.9 A2 (atom_id, source_cid, timestamp) keys: 2,500
完全一致: True
```

→ A2 は v10.8 A1 と **cid 選定 + timestamp 配置が完全同一**、Q/C コストのみが違う設計通りに実装。これにより A1 vs A2 の比較は「コスト感度の純粋評価」になる (cid 構造の違いはノイズにならない)。

### 3.3 層 C (出力パス制限)

```python
def assert_output_under_v109(path):
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(...)
```

→ smoke / main 出力が v109/ 配下に強制。v10.5/v10.6/v10.7/v10.8 への書き込み禁止。

---

## 4. 設計判断のメモ

### 4.1 B3 random cid pool の決定 (即決 §2.3)

- 案 b1 (seed 内 random) を採用、seed 内全 cid (228 個 / seed 0) から random 100
- per-atom で 100 cid 全部一意 (replace=False)
- 25 atom × 100 cid = 2,500 events
- rng_seed = 1_090_000_300 + seed → seed 別に異なる random、ただし bit-identity 担保

### 4.2 sim_score = NaN (B3)

random 選定なので sim_score を持たない。downstream で:
- Level 3 寄与候補感度評価では sim_score を参照しないので影響なし
- sensitivity_evaluator では cid 選定方法 (top_k_rank、sim) ではなく **波及量 (delta_C など)** で比較するため問題なし
- もし sim_score 必要な解析があれば、seed 0 の cid_atom_sim_matrix から後付けで取得可能

### 4.3 timestamp は v10.8 と完全共通 (uniform_atom_offset)

A2 と B3 ともに `schedule_atom_event_timestamps(atom_index)` を流用、v10.8 A1 と同じ間隔・配置。これにより:
- A1 vs A2 = Q/C コスト感度のみ
- A1 vs B3 = cid 選定感度のみ
- A2 vs B3 = (両方の差、要 careful 解釈)

C2 (リズム同調) のみ timing が違う。Step F 完了後に Step G で実装。

---

## 5. 計算量

- A2 + B3 smoke (seed 0): 0.27 秒
- main run (24 seeds × 2 条件) 推定: 約 6 秒 (sequential)、並列で 1 秒未満
- ストレージ予算: A2 + B3 各 0.1 MB × 24 seeds = 約 5 MB (極めて軽量、main run pipeline 全体の 0.2%)

→ atom_event_generator 自体は計算負荷が小さい、本体は次の Step D (baseline 再計算) で。

---

## 6. Step D 進行への申請

Step D (`v109_baseline_recalculator.py`、A2 + B3 各条件で 5+1 種 baseline 再計算 + global_activation 補正) に進む許可を求めます。

### 6.1 実装方針

```python
# 各 condition で:
#   1. atom_introduction_events_{cond}_seed{N}.parquet を読込
#   2. v107 build_baselines, compute_deltas, compute_baseline_excess_change を再実行
#   3. v107 natural_baseline_diff (固定、再計算不要) と統合
#   4. v108 global_activation_factor (natural events のみで計算、再利用) を適用
#   5. condition_id 列付きで baselines_with_delta_{cond}_seed{N}.parquet 出力
```

### 6.2 計算量見積もり

- v10.8 base: build_baselines 約 87 秒/seed
- 2 条件 (A2 + B3) × 24 seeds × 87 秒 = 4,176 秒順次
- 24 並列 (multiprocessing.Pool 24): **約 3-4 分**
- ストレージ: v10.8 baselines_with_delta_seed0.parquet が約 30 MB → 2 条件 × 24 seeds = 1.4 GB

### 6.3 smoke → main の進行

- Step D smoke (seed 0、A2 + B3) → 動作確認 (約 3 分)
- Step E (bimodal_analyzer) と並行実装可能
- Step D main は Step C/D/E 全部の smoke 通過後に Step J で統合実行

---

## 7. Step C 完了条件チェック

- [x] v109_atom_event_generator.py 実装
- [x] A2 (Q -2 / C +2、top_k 100) 動作確認
- [x] B3 (random cid、Q -1 / C +1) 動作確認
- [x] condition_id 列付与
- [x] bit-identity 層 A (同 seed 2 回再現) ✓ A2 / B3 とも
- [x] bit-identity 層 B (v10.9 A2 == v10.8 A1 の cid+timestamp セット完全一致) ✓
- [x] bit-identity 層 C (出力パス v109/ 配下強制) ✓
- [x] B3 rng_seed 固定 (1_090_000_300 + seed) で再現性担保
- [x] WLD.artless reserved label 各条件で 100 件付与
- [x] seed 0 smoke 0.27 秒で完了

---

*以上、Code A による v10.9 Step C 完了報告。Web Claude / Taka からの Step D 進行許可待ち。Step E (bimodal_analyzer) と並行実装可能。*
