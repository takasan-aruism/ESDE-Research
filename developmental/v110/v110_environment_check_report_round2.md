# v10.10 Step B'' Round 2 完了報告 — timing 軸追加集計 + Q-B1-B4 回答

*作成*: 2026-05-09、Code A
*親*: `v110_response_to_code_a_round2.md` (Web Claude 2026-05-09)
*対象*: Web Claude (主題ドキュメント Multi-gate × timing 二次元書き換えへの素材) / Taka

---

## 0. 一文サマリ

Round 1 で既に AGE_TARGETS=[200, 300, 500] の 11 gate × 3 timing × 24 seeds 全実測を完了済みのため、本 Round 2 は **既存データ (`multi_gate_population.csv`) からの集計と age 通過率の抽出**のみで完了 (追加実測コスト 0)、**重要発見: age=500 で 42% の cid が脱落** (寿命不足で age 500 通過不能、3,031/5,224 = 58.0%)、age=300 は全 cid 通過 (100%) で age=200 とほぼ同等の per 値、**age=500 で C 軸を含む gate は per FAIL** (ABC 0.52 / ABc 1.34 / Bc 1.34)、AB / B / A / all_pass は age=500 でも per≥3 PASS、最終 conditions 27 + v108_re = **28 conditions**、ストレージ累計 **1.74 GB (29%)** で打切閾値 50% 内、main run 推定 **5-10 分** (24 並列)、Q-B1-B4 全件回答完了 (実測コスト 0 / timing 軸追加候補は 200/300/500 で十分 / 累計 29% 余裕大 / CONDITIONS dict v10.9 規約継承で OK)、Web Claude の Multi-gate × timing 二次元設計への主題ドキュメント書き換え待ち。

---

## §1 Round 2 実測結果 (Round 1 データから抽出)

### 1.1 age 通過率 (all_pass = 制約なし条件下の cid 数)

| age_target | 通過 cids | 総 cids | 通過率 |
|---:|---:|---:|---:|
| **200** | **5,224** | 5,224 | **100.0%** |
| **300** | **5,224** | 5,224 | **100.0%** |
| **500** | **3,031** | 5,224 | **58.0%** ← **42% 脱落** |

→ **age=500 で 2,193 cid が脱落** (寿命不足、cid lifespan が age_target 通過前に terminate)。

cid 寿命分布 (Round 1 §1.4 から再掲):
- min 451, max 25,000、median 977
- lifespan >= 500 が 58.0% と一致 ✓

### 1.2 9 採用 gate × age_target の per 比較

| gate | age=200 per | age=300 per | age=500 per | min/max(>=3) PASS |
|---|---:|---:|---:|---|
| ABC | 1.84 (FAIL) | 1.71 (FAIL) | **0.52 (FAIL)** | 全 FAIL |
| ABc | 3.62 PASS | 3.32 PASS | **1.34 (FAIL)** | age=500 で FAIL |
| **AB** | **7.38 PASS** | **6.83 PASS** | **3.31 PASS** | 全 timing PASS |
| **B** | **7.38 PASS** | **6.83 PASS** | **3.31 PASS** | 全 timing PASS |
| Bc | 3.62 PASS | 3.32 PASS | **1.34 (FAIL)** | age=500 で FAIL |
| AC | 2.22 (FAIL) | 2.22 (FAIL) | 0.82 (FAIL) | 全 FAIL (観察用) |
| BC | 1.84 (FAIL) | 1.71 (FAIL) | 0.52 (FAIL) | 全 FAIL (観察用) |
| **A** | **8.71 PASS** | **8.71 PASS** | **5.05 PASS** | 全 timing PASS (controls) |
| **all_pass** | **8.71 PASS** | **8.71 PASS** | **5.05 PASS** | 全 timing PASS (controls) |

### 1.3 構造的観察

#### 観察 1: timing 軸の影響パターン

- **age=200 と age=300 はほぼ同等** (cid 寿命 >= 300 が 100%、events 差 < 8%)
- **age=500 で C 軸を含む gate が転倒** (FAIL 化)
- **A / B / AB / all_pass は age=500 でも生存** (短命 cid 脱落の影響を受けない、cid 寿命 >= 500 が 58%)

#### 観察 2: cid 寿命と C 軸の交差

- C 軸 (familiarity top 25%) は **per-seed quantile** で計算
- age=500 で短命 cid (寿命 < 500) が脱落すると、残った cid の familiarity 分布が偏る
- 結果として ABC / Bc / AC / BC / C で events 数が **65-72% 減少** (age=200 → age=500)

#### 観察 3: AB / B / A の頑健性

age=200 → age=500 で:
- AB / B: 7.38 → 3.31 (-55%)
- A / all_pass: 8.71 → 5.05 (-42%)

→ **「Integration 外」軸 (B) と「age 制約」軸 (A) は cid 寿命の影響を受けにくい** (ratio 維持)。

### 1.4 seed 別 events 数 (主軸 5 × 3 timing)

| gate | timing | min | max | mean | std |
|---|---|---:|---:|---:|---:|
| ABC | 200 | 28 | 57 | 46.1 | 7.3 |
| ABC | 300 | 23 | 54 | 42.7 | 7.4 |
| ABC | 500 | 6 | 23 | 12.9 | 3.3 |
| ABc | 200 | 59 | 110 | 90.6 | 13.0 |
| ABc | 300 | 49 | 103 | 83.0 | 12.7 |
| ABc | 500 | 20 | 43 | 33.4 | 6.2 |
| AB | 200 | 128 | 225 | 184.4 | 22.9 |
| AB | 500 | 56 | 102 | 82.8 | 12.1 |
| B | (AB と同じ) | - | - | - | - |
| Bc | 200 | 59 | 110 | 90.6 | 13.0 |
| Bc | 500 | 20 | 43 | 33.4 | 6.2 |

**最低 seed events**:
- age=500 ABC: seed 別最小 6 events (極端に少ない seed あり)
- age=200 ABC: 最小 28 events (mean 46 の 60%)

→ ABC × age=500 では sensitivity 評価が seed 別で seed 7 や seed 18 では完全に評価不能になる懸念。**main run で確認**。

---

## §2 Q-B1-B4 回答

### Q-B1: 追加実測の実装可能性

**回答: 追加実測コスト 0** (Round 1 で AGE_TARGETS=[200, 300, 500] 全実測済み)

実装ファイル `v110_environment_check.py` (既存) で:
```python
AGE_TARGETS = [200, 300, 500]  # Round 1 で全 timing 実測
for at in AGE_TARGETS:
    for seed in SEEDS:
        r = evaluate_gates_for_seed(seed, at)  # gate × timing 母集団
```

→ Round 2 は既存 csv からの集計のみ、新規実測不要。

age 通過率 (cid 寿命との比較) は `evaluate_gates_for_seed` 内の `if t_event >= death: continue` で実装済み、`all_pass` 列の値を使用して算出。

### Q-B2: timing 軸の追加候補

| 候補 age_target | 採否 | 理由 |
|---|---|---|
| **200** | 採用 (Web Claude 試案) | Step F median 227 中央 |
| **300** | 採用 (Web Claude 試案) | mean+1std 程度 |
| **500** | 採用 (Web Claude 試案) | A 境界 560 付近、cid 寿命脱落観察 |
| 100 | **却下** | cid lifecycle 確立前 (250 step では n_core 等が定常前)、観察意義薄い |
| 400 | △ 候補 | 300 と 500 の中間、補間観察に有用だが Web Claude 試案 3 通りで十分 |
| 560 | **却下** | A 境界そのもの、age=500 と類似で追加意義薄い |

→ **Web Claude 試案 (200/300/500) で確定、追加候補なし**

### Q-B3: 最終 conditions 数とストレージ予算

**最終 conditions 数: 27 + 1 = 28**:
- v110: 9 gate × 3 timing = 27 conditions
- v108_re: 1 condition (timing なし、v10.8 標準再実行)

**ストレージ推定** (events 数比例、v10.8 60,000 events = 7.5 MB/seed の比から):

| 区分 | events (24 seeds) | per seed | est. size/seed |
|---|---:|---:|---:|
| age=200 (9 conds) | 26,346 | 1,098 | ~4.4 MB |
| age=300 (9 conds) | 24,310 | 1,013 | ~4.0 MB |
| age=500 (9 conds) | 11,773 | 491 | ~1.95 MB |
| **v110 合計 (27 conds)** | **62,429** | **2,602** | **~10.4 MB** |
| v108_re (60,000) | 60,000 | 2,500 | 7.5 MB |
| **per seed total** | **122,429** | **5,102** | **~17.9 MB** |

**24 seeds main**: 17.9 × 24 = **~430 MB**
**+ cross_seed**: ~15 MB
**v10.10 合計**: **~445 MB**

**累計**:
- v10.7 (0.40) + v10.8 (0.69) + v10.9 (0.20) + v10.10 (0.45) = **1.74 GB / 上限 6 GB (29%)**
- 打切閾値 50% (3 GB) に大幅余裕

### Q-B4: CONDITIONS dict 構造

**Code A 提案 (v10.9 規約継承)**:

```python
CONDITIONS = {
    # 主軸 5 × 3 timing = 15 conditions
    "v110_ABC_t200": {"gate": "ABC", "age_target": 200, "Q_cost": 1, "C_gain": 1,
                       "cid_selection": "gate_filtered", "timing": "lifecycle_synced"},
    "v110_ABC_t300": {"gate": "ABC", "age_target": 300, ...},
    "v110_ABC_t500": {"gate": "ABC", "age_target": 500, ...},
    "v110_ABc_t200": {"gate": "ABc", ...},
    # ... 他 12 主軸
    
    # 観察用 2 × 3 = 6 conditions
    "v110_AC_t200": {"gate": "AC", ...},
    "v110_BC_t200": {"gate": "BC", ...},
    # ... 他 4
    
    # controls 2 × 3 = 6 conditions
    "v110_A_t200": {"gate": "A", ...},
    "v110_all_t200": {"gate": "all_pass", ...},
    # ... 他 4
    
    # bit-identity 1
    "v108_re": {"gate": "v108_standard", "age_target": "uniform", ...},
}
```

**整合性確認**:
- v10.9 CONDITIONS dict (A2/B3/C2 + 各 condition_id) と同形式 ✓
- recalculate_for_condition wrapper は引数で condition_id を取るので拡張容易 ✓
- multiprocessing.Pool 24 並列対応も継承 ✓

---

## §3 main run 推定時間

### 3.1 v10.9 ベースラインから外挿

- v10.9 (24 seeds × 3 conds × 17,000 events/seed) = 112 秒 (層 A 検証込み)
- 純粋 main: ~60 秒
- スループット: 51,000 events × 24 seeds / 60 秒 = **~20,000 events/秒** (24 worker 並列)

### 3.2 v10.10 推定

- v10.10 events 合計: 122,429 events × 24 seeds = **2.94M events**
- 純粋 main 推定: 2.94M / 20,000/秒 = **147 秒**
- 層 A 検証込み: 240-300 秒 = **約 5 分**
- 余裕見積: **5-10 分**

### 3.3 worker 負荷の偏り

各 condition の events 数が大きく異なる:
- 最小: ABC × age=500 = 310 events / 24 seeds = 13/seed
- 最大: A × age=200 = 5,224 / 24 seeds = 217/seed
- → 24 worker 並列で worker 間の処理量に差 (~17 倍)

worker 単位を **(seed, condition)** にすれば負荷分散される (48 cores Threadripper で十分)。
→ **multiprocessing.Pool 28 conditions × 24 seeds = 672 jobs を 24 workers で並列**

### 3.4 推奨実行戦略

```bash
python3 v110_post_process.py --mode main --n_workers 24 \
    --conditions ABC_t200,ABC_t300,...,v108_re
# 24 並列で 672 jobs (28 cond × 24 seeds) を分配
# 推定 5-10 分
```

---

## §4 Multi-gate × timing 二次元設計への素材

Web Claude が主題ドキュメント書き換え時に活用する素材:

### 4.1 §2.1 Multi-gate (Code A 推奨確定)

```
9 採用 gate (主軸 5 / 観察用 2 / controls 2):
  ABC / ABc / AB / B / Bc / AC / BC / A / all_pass

各 gate × 3 timing (age_target=200/300/500) = 27 conditions
+ v108_re (v10.8 標準再実行) = 28 conditions 計
```

### 4.2 §2.2 timing 軸 (確定)

```
age_target = 200: Step F median (中央) - 全 cid 通過 (100%)
age_target = 300: 中央 + 1std 程度 - 全 cid 通過 (100%)
age_target = 500: A 境界 (560) 付近 - 通過率 58.0% (短命 cid 脱落)
```

### 4.3 §4 観察対象 (Level 3 拡張)

```
Level 3 主観察指標 (Multi-gate × timing 二次元):
  - 各 gate × age_target × metric × path × window で cohens_d
  - 比較対象: vs v110_all_t{age} (controls) / vs v108_re (bit-identity)
  - 24 seeds 方向一致 4 段階観察
```

### 4.4 留意事項 (Code A 自主指摘)

- **per FAIL gate も記録対象**: ABC / AC / BC は age=200 でも FAIL だが「v10.9 主結果が main run で再現するか」の観察として残す (主題ドキュメント §2.2.0 の作業仮説検証と整合)
- **age=500 の C 軸 gate (Bc/ABc) は age=200 で PASS だったが age=500 で FAIL**: timing 軸の効果として観察、Level 3 で記述
- **A / all_pass は controls** で sensitivity 評価で v110 vs all_pass のベースラインとして使用

---

## §5 Step C 以降の進行 (主題ドキュメント書き換え後の予定)

```
[現在] Step B'' Round 2 完了 (本書) → Web Claude が主題ドキュメント書き換え (Multi-gate × timing 二次元)
   ↓
   Taka 確認
   ↓
[Web Claude] 実装指示書書き換え
   ↓
[Code A] 認識確認 (再、簡易版)
   ↓
   Taka 承認
   ↓
Step C: atom_event_generator (28 conditions、CONDITIONS dict 拡張)
Step D: baseline_recalculator (28 conditions baseline 再計算)
Step E: sensitivity_evaluator (各 v110 vs v110_all_t{age} / vs v108_re)
Step F: smoke 結果報告 (1 seed × 28 conditions、bit-identity)
Step G: 24 seeds main run (推定 5-10 分)
Step H: cross-seed 解析 + Level 1-3.5 reports + 4 種観察 + 構造的統合
Step I: 完了報告 + 観察状態 A/B/C 確定
```

---

## §6 一文サマリ (再掲)

Round 2 実測コスト 0 (Round 1 で AGE_TARGETS=[200, 300, 500] 全実測済みのため既存 csv からの集計のみで完了)、**age 通過率は age=200/300 で 100%、age=500 で 58.0%** (短命 cid 42% 脱落)、9 採用 gate × 3 timing の per 比較で **AB / B / A / all_pass が全 timing で per>=3 PASS**、**ABC は全 timing で FAIL** (per 1.84/1.71/0.52)、**ABc / Bc は age=200/300 PASS だが age=500 で FAIL** (C 軸が短命 cid 脱落の影響)、最終 28 conditions (27 v110 + 1 v108_re) でストレージ累計 **1.74 GB (29%)** / main run **5-10 分**、Q-B1-B4 全件回答完了 (実測コスト 0 / 試案 3 timing で十分 / 累計 29% 余裕大 / CONDITIONS dict v10.9 規約継承 OK)、Web Claude の Multi-gate × timing 二次元設計への主題ドキュメント書き換え待ち。

---

*以上、Code A による v10.10 Step B'' Round 2 完了報告。Web Claude `v110_phase_design.md` の Multi-gate × timing 二次元への書き換え + 実装指示書書き換え + Taka 確認 + Code A 認識確認 (再、簡易版) → Step C 進行へ。*
