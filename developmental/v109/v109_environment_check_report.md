# v10.9 Step B 環境チェック詳細報告

*作成*: 2026-05-08、Code A
*親*: `v109_implementation_brief.md` + 即決事項確定文書
*目的*: 実環境で 3 新条件 (A2/B3/C2) の実装パスと bimodal 分布を確定
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

3 新条件 (A2 Q-2/C+2、B3 random cid、C2 リズム同調) の実装パス + bimodal 1,540 件の分布を実環境で確認、**bimodal は attention 54% / temporal 30% / familiarity 15%、integration α/β は 0 件 (no_signal フラグの整合)** で path 依存性が判明、**各 seed で 35-96 件 (mean 64)** のため cross-seed 集計が主流確認、再 run コストは **atom_event_generator 軽量 + baseline 再計算 5 分 (24 並列) + bimodal_analyzer 3 分 + 全機構 main 16-20 分**、Step C (atom_event_generator A2/B3 先行実装) 進行準備完了。

---

## 1. bimodal 1,540 件の実分布

### 1.1 seed 別件数

| 統計 | 値 |
|---|---:|
| min | 35 |
| max | 96 |
| mean | 64 |
| seed 0 | 67 |
| seed 23 | 85 |
| 24 seeds 合計 | **1,540** |

→ seed 単独では bimodal が 35-96 件で**少数**、cross-seed 集計 (24 seeds 統合 1,540 件) が解析の主流。

### 1.2 path × observation_window 分布

| path | immediate | short | medium | 計 |
|---|---:|---:|---:|---:|
| **attention_via_salience** | 258 | 279 | 301 | **838 (54.4%)** |
| temporal_coactivation | 185 | 139 | 140 | 464 (30.1%) |
| familiarity | 92 | 73 | 73 | 238 (15.5%) |
| **integration_alpha** | 0 | 0 | 0 | **0** |
| **integration_beta** | 0 | 0 | 0 | **0** |
| 合計 | 535 | 491 | 514 | 1,540 |

### 1.3 観察

- **bimodal は attention/temporal/familiarity に集中**
- **integration α/β で bimodal 0 件** (v10.8 Step F の no_signal フラグと整合、C 変化なしのため bimodal 検出対象外)
- 3 path × 3 window = 9 セルに分布
- attention_via_salience が圧倒的多数 (54.4%)

### 1.4 bimodal_analyzer 実装への影響

- 1,540 件で 9 セル → 平均 171 件/セル
- 各 (atom, path, window) では 1-30 件程度 (atom 25 個に分散)
- **n_samples が 30 未満の (atom, path, window) も多い** → KDE の最低サンプル閾値 (即決 §3.1 で n_samples >= 30) を満たさないケース多発予想
- 代替閾値 (n_samples >= 10) に下げる判断が必要

→ Code A 推奨: **smoke 段階で実測してから閾値調整**。

---

## 2. atom_introduction_event の生成 (3 新条件)

### 2.1 A2 (Q -2 / C +2)

**実装**: v10.8 atom_event_generator.py を継承、ATOM_INTRO_Q_COST = 2、ATOM_INTRO_C_GAIN = 2 に変更。
- Q_after = Q_pre - 2、C_after = C_pre + 2
- post-process 計算的減算、実 ledger 不変
- 他は v10.8 と同じ (top_k 100、案 α 均等分散)

### 2.2 B3 (random cid、即決 §2.3 採用)

**実装**:
```python
import numpy as np
rng = np.random.default_rng(seed=109_b3_seed)  # 再現性担保
# 各 atom について seed 内全 cid から random 100 を選定
for atom_id in TARGET_ATOMS:
    # seed 内の 全 cid 一覧 (per_subject から)
    seed_cids = list(df_subj['cognitive_id'])
    if len(seed_cids) >= 100:
        random_cids = rng.choice(seed_cids, size=100, replace=False)
    else:
        random_cids = seed_cids  # 全 cid 使う
    # 各 random_cid で event 生成 (top_k_rank = -1)
```

注: seed 内 cid 数は seed 別 170-253、平均 218。100 cid 選定は基本的に問題なし。

### 2.3 C2 (リズム同調、Step F 後に実装)

**Step F bimodal 解析完了後の分岐ロジック** (即決 §2.2 確定):

```
分岐 1: 「明確な受信可能状態」が同定された
  → C2 = 高ピーク cid 構造特性を満たす cid のみに発火
  → タイミングは cid のライフサイクル中盤に分散

分岐 2: 「受信可能状態」が曖昧
  → C2 = 高 sim cid (top_k 30) のみに発火
  → B2 (top_k 30) との差が小さくなるリスクを記録

分岐 3: 完全に判定不能
  → C2 を C1 と同等扱い、留保事項として記録
  → Gemini A2 仮説 (リズム同調) の検証失敗として明記
```

→ Step F 完了時に Web Claude / Taka に詳細報告して分岐確定。

### 2.4 A3 (Q 0 / C 0、即決 §2.4 確定 — 案 c では実施しない)

即決 §2.1 確定の案 c では A3 は実施しない (3 新条件 = A2 / B3 / C2)。A1 vs A2 の比較で Q/C コスト感度を 1 軸で評価。

参考までに、A3 が今後追加される場合の扱い:
- delta 計算スキップ (コスト 0 = 刺激なし)
- Q_after = Q_pre、C_after = C_pre
- イベント記録のみ、実 ledger 不変

---

## 3. baseline 再計算 (3 条件、即決 GPT B6 規律)

### 3.1 流用元

`v107_baseline_constructor.py` (Step B 確認済):
- `build_baselines(seed, source_events)`: 5 種 baseline 構築
- `compute_deltas(seed, df_targets)`: 6 量 × 3 windows delta
- `compute_baseline_excess_change(df_with_delta)`: per (event, path) excess

### 3.2 v10.9 拡張

各新条件 (A2 / B3 / C2) で:
1. condition_id 別に source_events を生成
2. 各 condition_id で build_baselines → compute_deltas → compute_baseline_excess_change を実行
3. 出力ファイルに `condition_id` 列追加

### 3.3 計算量

- 3 条件 × 24 seeds × build_baselines 約 87 秒 = **6,300 秒順次** (1.75 時間)
- 24 並列で **約 5 分**
- v10.7/v10.8 の並列パターンを再利用

### 3.4 v10.7 natural baseline (Level 3.5 用)

`developmental/v108/outputs/main/natural_baseline_diff_seed*.parquet` を流用。各 seed 内に 5 source × 10 path × 18 delta の集計値あり。新規計算不要。

---

## 4. bimodal_analyzer 実装 (即決 §2.5 確定)

### 4.1 アルゴリズム (KDE 第一試行)

```python
from scipy.stats import gaussian_kde
from scipy.signal import find_peaks

def find_bimodal_peaks(delta_values, n_samples_threshold=10):
    if len(delta_values) < n_samples_threshold:
        return None
    kde = gaussian_kde(delta_values)
    x_grid = np.linspace(min(delta_values), max(delta_values), 200)
    density = kde(x_grid)
    peaks_idx, _ = find_peaks(density)
    if len(peaks_idx) < 2:
        return None
    # 上位 2 ピーク を peak_high, peak_low として記録
    sorted_peaks = sorted(peaks_idx, key=lambda i: -density[i])[:2]
    peak_high_idx, peak_low_idx = max(sorted_peaks), min(sorted_peaks)
    return {
        "peak_high_value": x_grid[peak_high_idx],
        "peak_high_density": density[peak_high_idx],
        "peak_low_value": x_grid[peak_low_idx],
        "peak_low_density": density[peak_low_idx],
    }
```

### 4.2 3 仮説評価 (即決 §3.2 確定 — effect_size 主、p_value 副)

```python
# 仮説 1: n_core 別
high_cids_n_core = [...]  # 高ピーク値に近い delta を持つ cid の n_core
low_cids_n_core = [...]
score_1_cohens_d = (mean(high) - mean(low)) / pooled_std

# 仮説 2: Integration 内外
score_2_cohens_d = ...  # cid が α 内なら 1、外なら 0

# 仮説 3: ライフサイクル段階
score_3_cohens_d = ...  # cid age

best_hypothesis = argmax([score_1, score_2, score_3])
# スコア閾値 (例: 0.3) 未満なら "未分類" (即決 §3.3)
if max([score_1, score_2, score_3]) < 0.3:
    best_hypothesis = "unclassified"
```

### 4.3 計算量

- 1,540 件 × KDE + find_peaks + 仮説評価 = 約 0.1 秒/件
- 順次で約 3 分
- 並列化不要 (3 分は許容)

---

## 5. ストレージ予算 (実測ベース)

### 5.1 案 c (3 新条件) の実測予想

| 区分 | 値 |
|---|---:|
| 3 新条件 atom_intro 関連 (× v10.8 736 MB) | 約 **2.2 GB** |
| bimodal_analyzer 出力 | 約 1 MB |
| sensitivity_evaluator 出力 | 数 MB |
| design_table 4 種 | 数 MB |
| **合計** | **約 2.2 GB** |

### 5.2 累計

- v10.7: 0.4 GB
- v10.8: 0.7 GB
- v10.9: **2.2 GB**
- 合計: **3.3 GB** (上限 6 GB の 55%)

### 5.3 各機構別の seed あたり storage 推定

3 条件 × 約 24.65 MB (v10.8 全機構統合 seed 0) = 74 MB/seed
24 seeds = 1.78 GB
+ 副次 ≈ 2.2 GB

---

## 6. v10.7/v10.8 流用一覧

### 6.1 v10.7 から流用 (関数 import)

| モジュール | 流用関数 |
|---|---|
| v107_event_aggregator.py | aggregate_source_events, attach_pre_event_state |
| v107_path_analyzer.py | build_all_paths |
| v107_baseline_constructor.py | build_baselines, compute_deltas, compute_baseline_excess_change |
| v107_avalanche_monitor.py | build_multi_hop_paths, compute_decay_rate, detect_resonance_loops, compute_peak_lag_curve, compute_peak_lag_per_path, classify_wave_patterns |

### 6.2 v10.8 から流用

| モジュール | 流用関数 |
|---|---|
| v108_atom_event_generator.py | generate_seed_atom_events (拡張で condition_id 追加) |
| v108_global_activation_correction.py | compute_global_activation_factor, add_adjusted_excess |

### 6.3 v10.9 で新規実装

| モジュール | 機能 |
|---|---|
| v109_atom_event_generator.py | 3 新条件 (A2/B3/C2) の atom_introduction_event 生成 |
| v109_baseline_recalculator.py | 各条件で baseline 再計算 (5+1 種 + global activation 補正) |
| v109_bimodal_analyzer.py | KDE + 3 仮説評価 |
| v109_sensitivity_evaluator.py | 3 候補感度評価 |
| v109_design_table_compiler.py | 出口固定 4 種設計表生成 |
| v109_post_process.py | orchestrator (v10.7/v10.8 流用 + 拡張) |

---

## 7. Step B 完了条件チェック

- [x] 3 新条件 (A2/B3/C2) の実装パス確認
- [x] bimodal 1,540 件の seed 別 / path × window 分布確認
- [x] bimodal_analyzer の KDE 実装方針確定
- [x] 3 仮説評価の effect_size (Cohen's d) ベース
- [x] 「未分類」閾値 (0.3) の方針
- [x] baseline 再計算流用元確認
- [x] ストレージ予算実測 (案 c 採用、約 2.2 GB、上限 37%)
- [x] v10.7/v10.8 流用関数一覧 (8 モジュール)

---

## 8. Step C 進行への申請

Step C (`v109_atom_event_generator.py`、A2 + B3 を先行実装) に進む許可を求めます。

実装方針:
1. **A2 (Q -2 / C +2)**: v10.8 atom_event_generator.py 流用、コスト変更のみ、25 atom × 100 events
2. **B3 (random cid)**: seed 内全 cid から random 100、top_k_rank = -1
3. **C2 は Step F bimodal 完了後** (Step G で実装)
4. seed 0 smoke で動作確認、bit-identity 層 A 検証

実行時間予想: 1.5 時間 (A2 + B3、C2 は別途)。

Step D (baseline 再計算 A2 + B3) と Step E (bimodal_analyzer) の順序:
- D を E と並行実装可能
- E 完了 (bimodal 結果) → F 報告 → G (C2 atom_event_generator) → H (C2 baseline)

24 seeds 単一バッチ厳守 (3 バッチ分割禁止) を継続。

---

*以上、Code A による v10.9 Step B 環境チェック詳細報告。Web Claude / Taka からの Step C 進行許可待ち。*
