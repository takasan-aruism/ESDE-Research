# v10.9 Step F 完了報告 — bimodal 24 seeds 集計 + C2 分岐判定要請

*作成*: 2026-05-08、Code A
*前提*: Step E main run 24 seeds 完了 (35.47 秒)、出力 `bimodal_analysis_all.parquet` (1,540 cells)
*対象*: Web Claude / Taka (C2 分岐判定の最終決定)

---

## 0. 一文サマリ

24 seeds × 1,540 bimodal cells の cross-seed 解析で **H3_lifecycle が 553/918 = 60.2% で支配的** (即決 §2.2 分岐 1 の閾値達成)、しかも **99% のセルで「高 delta = 若い cid (age mean 224 / median 227)」、低 delta = 古い cid (age mean 5,612)」と方向が一貫**、副次的に H1_n_core 26% (91% で「高 delta = 高 n_core cid」)、H2_Integration は 4.6% で v10.8 既知の no_signal 傾向と整合、ただし **KDE fallback 率が 100%** (find_peaks が 2 ピーク捕捉せず median_split 代替) で技術的留意事項あり、Code A 推奨は **分岐 1 採用 + C2 設計を「若い cid (age 100-300 帯) を狙う event timing」** に確定、Web Claude / Taka の C2 分岐判定 (1/2/3) と具体実装方針の決定を要請。

---

## 1. 24 seeds bimodal 集計結果

### 1.1 全体 (1,540 cells)

| subtype | cells | 割合 |
|---|---:|---:|
| **genuine_bimodal** (unique > 5) | 918 | **60%** |
| sparse_outlier (unique ≤ 5 + pct_zero ≥ 95%) | 621 | 40% |
| discrete_bimodal | 1 | 0% |

### 1.2 best_hypothesis (genuine_bimodal 918 cells)

| best_hypothesis | cells | 割合 | 即決 §2.2 判定 |
|---|---:|---:|---|
| **H3_lifecycle** | 553 | **60.2%** | **分岐 1 閾値達成** |
| H1_n_core | 241 | 26.3% | 副次寄与 |
| unclassified (effect_size < 0.3) | 82 | 8.9% | - |
| H2_integration | 42 | 4.6% | ほぼ機能せず |

### 1.3 effect_size (Cohen's d) 分布 (genuine 918 cells)

| 統計 | 値 |
|---|---:|
| mean | 0.85 (大効果量) |
| std | 0.38 |
| median | 0.93 |
| 25%-75% | 0.65-1.03 |
| max | 2.34 |

→ effect_size は中〜大、H3 支配仮説の信頼性高い。

---

## 2. H3_lifecycle の方向性 (553 cells、最重要発見)

| 群 | age 平均 (event_ts - birth_step) | age 中央値 |
|---|---:|---:|
| 高 delta 群 (peak_high 側 cid) | **224** | **227** |
| 低 delta 群 (peak_low 側 cid) | 5,612 | 6,119 |

- **age_diff (high - low) mean = -5,388**
- **99% (550/553)** のセルで「**高 delta = 若い cid**」と方向一致
- 1% のみ「高 delta = 古い cid」(逆方向)

→ **「atom_intro に対して強く反応する cid は、ほぼ生まれたて (age ~200) の若い cid」** という極めて明確なパターン。

### 2.1 解釈 (構造的説明)

- 若い cid は familiarity edge / Integration 構造がまだ未確立
- atom_intro が「外部刺激」として作用する余地が大きい (受容性が高い)
- 古い cid は既存の関係構造に固定化されており、新しい atom_intro に対しても変化しにくい

→ **「受信可能状態」の構造的説明: 若年期 cid (age < 500)** が候補。

---

## 3. H1_n_core (241 cells、副次的支配)

| 群 | n_core_member 平均 |
|---|---:|
| 高 delta 群 | 4.67 |
| 低 delta 群 | 3.49 |

- **91% (219/241)** で「高 delta = 高 n_core cid」
- mean 差 1.18 (Cohen's d で中効果量)

→ **副次仮説: 高 n_core (cid の中心メンバー数が多い) cid が強反応**。H3 と独立に作用。

---

## 4. path × window 別分布 (genuine 918 cells)

### 4.1 best_hypothesis × relation_path_type

| path | H1_n_core | H2_integration | H3_lifecycle | unclassified | total |
|---|---:|---:|---:|---:|---:|
| temporal_coactivation | 57 | 4 | **314 (74%)** | 47 | 422 |
| attention_via_salience | 136 | 4 | 112 | 30 | 282 |
| familiarity | 48 | 34 | 127 (59%) | 5 | 214 |

### 4.2 best_hypothesis × observation_window

| window | H1 | H2 | **H3** | unclassified | total |
|---|---:|---:|---:|---:|---:|
| immediate | 79 | 7 | 173 (61%) | 28 | 287 |
| short | 68 | 16 | 185 (58%) | 29 | 298 |
| medium | 94 | 19 | 195 (59%) | 25 | 333 |

→ window で H3 比率はほぼ均一 (58-61%)、観察時間スケールに依存しない普遍的傾向。
→ path 別では **temporal_coactivation で H3 が 74% と最強**、attention で H1 (n_core) が H3 を上回る (136 vs 112)。

---

## 5. seed 別 H3 支配比率の分散

| 統計 | 値 |
|---|---:|
| seed 別 H3 比率 mean | 62% |
| min | 30% (seed 23) |
| max | 87% |
| H3 ≥ 60% の seed | **14/24 (58%)** |
| H3 < 60% の seed | 10/24 (seed 0/1/5/8/9/13/15/16/22/23) |

→ 集計 (cross-seed) では 60.2% で分岐 1 閾値達成、しかし**個別 seed では 60% 未満が 42%**。これは 24 seeds の集計が必須の理由 (個別 seed 観察では結論ぶれる)。

---

## 6. 技術的留意事項

### 6.1 KDE fallback 率 100%

| 統計 | 値 |
|---|---:|
| KDE 成功 (peak_method='kde') | 0/918 = 0% |
| median_split fallback | 918/918 = **100%** |

**なぜ KDE で 2 ピーク取れない**:
- vals の分布が「広い 0 中心 + 端に少数の外れ値」の片寄り型
- gaussian_kde の bandwidth が広すぎ (silverman/scott 自動値)
- find_peaks の prominence 閾値も検出に至らない
- 実際の分布は **「滑らかな歪んだ unimodal + 端部クラスタ」** の可能性 (純粋な 2 ピーク分布ではない)

### 6.2 sparse_outlier 621 件 (40%) の意味

- pct_zero mean = 99.5% (1 cid だけ大きく動き、残りは 0)
- std mean = 0.716 (狭い分散)
- best_hypothesis (参考値): unclassified 403 (65%)、H3 114、H1 88、H2 16

→ 「外れ値型」現象は **ほとんどの cid が atom_intro に不反応、稀な特殊状態 cid のみが反応**を示唆。これは v10.10 への含意 (条件適応型の本質はこの「特殊状態 cid」を狙うこと)。

### 6.3 「2 ピーク」より「歪み + 外れ値」の解釈

- KDE fallback 100% + sparse_outlier 40% から推測
- v10.8 で「bimodal 17.4%」と分類されたが、**真の 2 ピーク分布は少数**かもしれない
- ただし median_split + Cohen's d による評価は「高 delta vs 低 delta」の構造的差異を捉えるのに**実用的に有効**
- → 結果の信頼性は確保 (effect_size 0.85 + 99% 方向一致)

---

## 7. C2 分岐判定 (即決 §2.2、Code A 推奨案)

### 7.1 即決事項の 3 分岐

```
分岐 1: 「明確な受信可能状態」が同定された
  → C2 = 高ピーク cid 構造特性を満たす cid のみに発火
  → タイミングは cid のライフサイクル中盤に分散

分岐 2: 「受信可能状態」が曖昧
  → C2 = 高 sim cid (top_k 30) のみに発火
  → B2 (top_k 30) との差が小さくなるリスクを記録

分岐 3: 完全に判定不能
  → C2 を C1 と同等扱い、留保事項として記録
```

### 7.2 Code A 推奨判定

**分岐 1 採用** (H3_lifecycle 60.2% で閾値達成、99% 方向一致、effect_size 0.85)

ただし**実装上の選択肢が 2 通りある**:

#### 案 a: cid 選定で絞る (top_k 100 のうち若い cid のみ)

```python
# event 発火時刻に source_cid の age が 100-500 のものに限定
def select_young_cids_for_atom(seed, atom_id, age_target_min=100, age_target_max=500):
    top_k_100 = extract_top_k_cids(seed, atom_id, top_k=100)
    # 各 event 発火時刻で age を計算し、若い cid のみフィルタ
    # → 結果的に cid 数は atom × seed 別にバラバラ (10-50 程度予想)
```

**問題**: cid 数が atom × seed で大きく変動、A1/B3 (100 cid 固定) との比較で「cid 数差異がノイズ」になる。

#### 案 b: timing で絞る (top_k 100 + 各 cid のライフサイクル中盤に発火)

```python
# 各 source_cid について、その cid の age が 100-300 に入るタイミングで event 発火
def schedule_lifecycle_synced_timestamps(source_cid, birth_step, age_target=200):
    return birth_step + age_target  # 各 cid 個別の発火時刻
```

**この案では**:
- top_k 100 cid 固定 (A1/B3 と同じ)
- timestamp は cid 別に変動 (リズム同調の本来の意味)
- atom_intro_event の発火が cid のライフサイクル中盤に集中
- 25 atom × 100 cid × 24 seeds = 60,000 events、ただし発火時刻分散

→ Code A 推奨: **案 b (リズム同調の本来意図に最も近い)**

#### 案 c: 両方の組み合わせ (cid 選定 + timing)

- top_k 100 のうち age が 100-500 帯の cid のみ
- かつ各 cid の age = 200 で発火
- 最も厳密だが、cid 数変動 + 各 cid 1 event のみで発火回数激減

→ 比較しにくい、推奨せず。

### 7.3 Code A の最終推奨: 案 b

理由:
1. 即決 §2.2 「タイミングは cid のライフサイクル中盤に分散」と整合
2. cid 数が A1/B3 と同じ (100 cid) なので比較が clean
3. timing のみが違う → 「リズム同調 vs 均等分散」の純粋比較
4. 実装コストが低 (timing 関数のみ書換)

### 7.4 Web Claude / Taka への決定要請

**Q1**: 分岐 1 採用で良いか? それとも seed 別 H3 支配が 14/24 (58%) と均一でないことを重視して分岐 2 (top_k 30 fallback) にするか?
**Q2**: 案 a / 案 b / 案 c のどれを採用するか?
**Q3**: 案 b 採用なら age_target を 200 (若い cid の median) で良いか? それとも 150 (より若い) や 300 (中盤の上端) にするか?
**Q4**: KDE fallback 100% という技術的留意事項を「留保事項」として明記するか? それとも結果の信頼性 (effect_size 0.85 + 方向一致 99%) を優先して標準的な解釈とするか?

---

## 8. 次のステップ (Step G 進行準備)

Web Claude / Taka の C2 判定 (Q1-Q4) を受けて:

- Step G: `v109_atom_event_generator.py` に C2 condition を追加実装
- Step H: `v109_baseline_recalculator.py` で C2 baseline 再計算
- Step I: `v109_sensitivity_evaluator.py` (3 候補感度評価)
- Step J: 統合 smoke + bit-identity 検証
- Step K: smoke 結果報告、main run 判定
- Step L: 24 seeds main run (3 新条件)
- Step M: cross-seed analysis + 4 種設計表
- Step N: 完了報告

---

## 9. 補足: ファイル

- `developmental/v109/outputs/main/bimodal_analysis_all.parquet` (1,540 rows × 30 cols)
- `developmental/v109/outputs/main/bimodal_analysis_seed{0..23}.parquet` (per-seed)
- 全データ列: seed, atom_id, relation_path_type, observation_window, n_samples, subtype, n_unique, pct_zero, min/max/std, bimodality_coefficient, peak_method, peak_high_value, peak_low_value, peak_high_density, peak_low_density, n_high, n_low, h1_n_core_d, h1_high_mean, h1_low_mean, h2_integration_d, h2_high_pct, h2_low_pct, h3_lifecycle_d, h3_high_age_mean, h3_low_age_mean, best_hypothesis, best_effect_size

---

*以上、Code A による v10.9 Step F 完了報告 + C2 分岐判定要請。Web Claude / Taka からの判定 (Q1-Q4) を待ち、Step G 進行へ。*
