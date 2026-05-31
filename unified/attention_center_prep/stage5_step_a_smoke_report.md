# 注意センター ESDE — Step A smoke 観察事実報告 (判定置かない)

**Date**: 2026-05-31
**Author**: Code A
**Status**: smoke 完了、観察事実のみ記録、Web Claude 機能設計待ち
**親**: 機能設計 v1 確定 (判断 5 件ロック) + dynamic_threshold 提案 (案 A)
**規律**: 判定置かない / 観察事実のみ / 主題評価は Taka 領域 / source_event 1 本 / 物理層 frozen

---

## 0. 観察事実 (要点)

| 項目 | no_center | with_center | Δ rel |
|---|---|---|---|
| **labels_total** | 150 | 151 | +0.67% |
| **pct_n_core_5plus** | 2.67% | 1.99% | **-25.50%** |
| **share_max** | 0.037 | 0.029 | **-21.89%** |
| **occ_max** (phase 集中) | 0.063 | 0.046 | **-26.71%** |
| occ_nonzero (phase 広がり) | 56 | 58 | +3.57% |
| alive_l_count | 3147 | 3181 | +1.08% |
| torque_events | 1520 | 1507 | -0.86% |

**発火**: 5/5 windows (全 windows で should_attend = True)
**overlap_labels**: 0/0/0/0/2 (w=0-3 はゼロ、w=4 で 2)

---

## 1. 実行構成 (確定アーキ)

- 3 instance すべて同型 V82Engine(N=5000) + VirtualLayerV9
  - Atom 系 (seed=42): cog なし、labels で代用
  - Center (seed=99): cog なし、while 常駐
  - Other (seed=100): cog なし、素
- 2 conditions × 5 windows × 100 steps
- 計算量: no_center 196s + with_center 461s = **661 秒 (11 分)**

---

## 2. dynamic_threshold (案 A) 発火動態

| window | z_score | stress | fire | overlap_labels | atom_inject_n |
|---|---|---|---|---|---|
| 0 | 5.49 | 1.0 | True | 0 | 5 |
| 1 | 6.07 | 1.0 | True | 0 | 5 |
| 2 | 7.40 | 1.0 | True | 0 | 5 |
| 3 | 6.89 | 1.0 | True | 0 | 5 |
| 4 | 6.78 | 1.0 | True | 2 | 5 |

- 全 windows で z_score > stress (案 A 発火条件)
- z_score は 5.5-7.4 で動的、stress は 1.0 (smoke で stress_enabled=False のため EMA 初期値)
- → **発火タイミングは center.state.E 分布の極端さに依存** (state-driven)

---

## 3. 観察事実の詳細

### 3.1 CID 構造 ((a)、Web Claude §3)

| 指標 | no_center | with_center | 観察 |
|---|---|---|---|
| labels_total | 150 | 151 | +1 |
| n_core_mean | 2.12 | 2.09 | -0.027 |
| pct_n_core_2 | 94.7% | 94.7% | 不変 |
| **pct_n_core_5plus** | **2.67%** | **1.99%** | **-25.5% rel** |
| share_mean | 0.0067 | 0.0066 | -0.7% |
| **share_max** | **0.037** | **0.029** | **-21.9% rel** |
| age_mean | 2.86 | 2.87 | 不変 |

- with_center で **大 CID (n_core ≥ 5) 比率が rel 25.5% 減少**
- with_center で **最大 share label が rel 21.9% 減少**
- 弱い CID (n_core=2) 比率は不変

### 3.2 phase 分布 ((c)、Web Claude §3 = 応答候補分布の本丸)

| 指標 | no_center | with_center | 観察 |
|---|---|---|---|
| **occ_max** | **0.063** | **0.046** | **-26.7% rel** |
| occ_mean | 0.0156 | 0.0156 | 不変 |
| occ_nonzero | 56 | 58 | +3.57% rel |

- with_center で **phase bin の最大集中度が rel 26.7% 減少** (occ_max)
- with_center で **phase bin の埋まり (non-zero bin 数) が rel 3.57% 増加** (分散化)
- mean は不変

### 3.3 物理層 ((Web Claude §0.1 同型 fork 検証))

| 指標 | no_center | with_center | 観察 |
|---|---|---|---|
| alive_n_count | 5000 | 5000 | 不変 (固定) |
| alive_l_count | 3147 | 3181 | +1.08% rel |
| torque_events | 1520 | 1507 | -0.86% rel |

- 物理層 alive_l は微増 (with_center の inject 追加で link 生成)
- torque_events は微減
- 第 4 段階改修小 smoke でも観察された「物理層は条件変動で堅牢」と整合

---

## 4. 留保 (観察事実のみ、判定なし)

### 4.1 overlap_labels = 0 の構造的背景

- センター (seed=99) の state.E top-K node ID と Atom 系 (seed=42) の labels[lid]["nodes"] (frozenset) との偶然一致確率は低い
- N=5000 中で 5 nodes target に対し labels.nodes 集合 (各 2-5 nodes) と当たる確率は計算上小さい
- w=0-3 では overlap=0、w=4 で overlap=2 が出た
- → **overlap=0 でも overlap_nodes = target_ids (フォールバック) として別系へ inject**
- 別系経由で Atom 系へ書き戻される (new_targets ≠ target_ids)
- → センター由来の inject が間接的に Atom 系に届く

### 4.2 発火 5/5 (常に発火)

- 案 A z_score > stress が初期から常に成立 (z_score = 5.5-7.4 で常に > 1.0)
- 「無視も機能」の検証は本 smoke では成立しない (常に発火)
- 別案 (B/C) または z_score の比較対象を変える (例: > 2 × stress) で間引き可能

### 4.3 計算量

| 項目 | 時間 |
|---|---|
| Atom 系 起動 (run_injection) | 65s |
| Center 起動 | 64s |
| Other 起動 | 65s |
| no_center 5 windows | ~130s (200 - 65) |
| with_center 5 windows (Atom + Center + Other + inject) | ~270s (461 - 191) |
| 合計 | 661s (11 分) |

→ フル (mat 20 + track 10 = 30 windows、24 seeds) なら推定 11 × 6 × 24 = 1584 分 ≈ 26 時間 / seed × 24、並列なら ~2-3 時間。

---

## 5. 規律遵守確認 (Web Claude §5 不変条件)

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 (3 instance すべて同 V82+VirtualLayerV9) | ✓ 全部 N=5000, seed のみ違う |
| 書込 source_event 1 本 (physics.inject のみ) | ✓ state 直接 / cog 直接 書込なし |
| トリガー固定しない (両辺 state-dependent) | ✓ z_score (E 分布) と stress (link 動態)、両者動的 |
| 定義しない (出力が変わるかで判断) | ✓ 「学習」「成功」「失敗」未使用 |
| **判定置かない** | ✓ 「変わった」「増えた / 減った」のみ、success/fail なし |

---

## 6. Code A 観察 (判定でない、観察事実の整理)

### 6.1 何が観察されたか

- with_center で Atom 系の **複数指標が変動** (pct_n_core_5plus / share_max / occ_max が rel 20-27% 減)
- 物理層 (alive_n, alive_l, mean_E) は **ほぼ不変** (Δ rel < 2%)
- 発火は 5/5 windows、案 A z_score > stress が機能
- overlap_labels は w=0-3 でゼロ、w=4 で 2 (構造的低確率)

### 6.2 何が観察されなかったか (留保)

- 「無視」(should_attend=False) 動作は本 smoke では観察できず (常に発火)
- 多 seed 比較 (1 seed のみ、統計的妥当性は別 smoke)
- overlap_labels = 0 が大半なので「向き先マップ機能」の主作用ではなく、別系経由の間接効果が主要因

### 6.3 観察パターン (Web Claude §3 への入力)

「**no_center vs with_center で Atom 系出力が変わるか**」に対する答え:
- (a) CID 構造: **変わる** (pct_5+ -25%, share_max -22%)
- (b) Integration: 未統合 (本 smoke スコープ外)
- (c) phase 分布: **変わる** (occ_max -27%, occ_nonzero +3.6%)

主題評価 (これが「学習」「動いた」と呼べるか) は Taka 領域、Code A は判定置かない。

---

## 7. Web Claude / Taka 判断要請

| # | 問い (Code A は提示のみ、判断は Taka) |
|---|---|
| ① | dynamic_threshold 案 A (z_score > stress) で「常に発火」(5/5) は機能設計上 OK か (無視動作の検証が要るか) |
| ② | overlap_labels = 0 が大半 (w=0-3) の構造を、機能 2「向き先マップ」の問題と見るか、別系経由の間接効果で十分とするか |
| ③ | 観察された差 (CID 構造 -25%, phase -27%) が次の機能設計の起点として使えるか、それともノイズか (多 seed で検証要か) |
| ④ | フル (24 seeds 並列) を回すか、Step A 観察のみで次の機能設計に進むか |

---

## 8. 出力ファイル

- `dynamic_threshold_proposal.md` (案 A 提案)
- `stage5_step_a_smoke.py` (実装)
- `stage5_step_a_smoke_report.md` (本文書)
- `run_smoke_a/smoke_a_full.parquet` (10 rows = 2 cond × 5 win)
- `run_smoke_a/smoke_a_loop_log.parquet` (5 rows、発火動態)
- `run_smoke_a/smoke_a_run_summary.json`

---

## 9. 一文サマリ

注意センター ESDE Step A smoke 観察事実報告 (Code A、2026-05-31、機能設計 v1 確定後 + dynamic_threshold 案 A 採用 + 判定置かない規律遵守) として、実行 (3 instance Atom seed=42 / Center seed=99 / Other seed=100 全部 V82Engine N=5000 + VirtualLayerV9 cog なし、2 conditions no_center/with_center × 5 windows × 100 steps、661 秒 11 分)、観察事実 (with_center で Atom 系: labels +0.67% / pct_n_core_5plus rel **-25.5%** / share_max rel **-21.9%** / occ_max rel **-26.7%** / occ_nonzero rel +3.57% / alive_l_count rel +1.08% / 物理層 alive_n 不変)、dynamic_threshold 案 A 発火 5/5 (常に発火、z_score 5.5-7.4 stress 1.0、両辺 state 動的)、overlap_labels = 0 (w0-3) overlap=2 (w4) 構造的低確率 (N=5000 中 5 nodes target が labels.nodes 集合と当たる確率小、フォールバックで target_ids がそのまま別系へ inject 経由間接効果)、規律遵守 (物理層 frozen + 同型 3 instance + source_event 1 本 + トリガー固定しない両辺 state-dependent + 定義しない出力変わるかで判断 + **判定置かない** 観察事実のみ Web Claude/Taka 主題評価領域)、留保 (無視動作未観察 / 多 seed 未検証 / overlap_labels=0 多数で向き先マップ主作用でなく別系経由間接効果)、Code A 観察 (a CID 構造 変わる / b Integration 未統合 / c phase 分布 変わる)、判断 4 件提示 (常に発火 OK か / overlap=0 構造をマップ問題と見るか / 観察差がノイズか起点か / フル進行か機能設計次か)、書込み unified/attention_center_prep/ 配下のみ。

---

**Step A smoke 観察事実 end. Web Claude 機能設計 + Taka 主題評価待ち。**
