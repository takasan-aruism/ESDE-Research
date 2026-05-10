# v10.12 入力ルーティング条件 (達成条件 §0.2)
*抽出元*: v10.11 within-cid design (q_c_inherited 起点、12 cells)
*規律*: 観察事実 / 整理仮説 / 未解明 を分離 (§3 ラベル規律)

## 観察事実

### delta_C_within (T+50 - T-50) の n_core_bin × c_q_partition × 24 seeds 方向一致

| n_core_bin | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| bin_2 | +0.187 (complete) | +0.116 (majority) | +0.097 (majority) | +0.247 (majority) |
| bin_3_4 | +0.467 (majority) | +0.206 (tied) | +0.497 (tied) | +0.276 (complete) |
| bin_5plus | +0.356 (majority) | +0.314 (majority) | +0.368 (tied) | +0.377 (majority) |

### delta_pulse_within の n_core_bin × c_q_partition

| n_core_bin | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| bin_2 | -0.047 (majority) | -0.032 (majority) | -0.008 (majority) | -0.020 (majority) |
| bin_3_4 | +0.000 (complete) | +0.000 (complete) | +0.000 (complete) | -0.001 (majority) |
| bin_5plus | +0.000 (complete) | +0.000 (complete) | +0.000 (complete) | -0.000 (majority) |

## 整理仮説 (構造的根拠は本主題で確定せず留保継承)

- Q1 (累積 c < 3) で delta_C_mean > 0.05 の cells: 3/3 (n_core_bin)
- Q4 (累積 c ≥ 10) で delta_C_mean ≈ 0 (|x|<0.05) の cells: 0/3
- 観察パターンは仮説 2 (C 値飽和) と部分的に整合、または別パターン (留保事項として記録)

## v10.12 入力ルーティング条件候補

### 条件 1: 概念取り込み (delta_C 系)

**「β 累積 c_inherited が 3 未満 (Q1) の状態の cid を狙う」**

- 最大効果 n_core_bin: bin_3_4 (delta_C mean +0.467、majority_consistent)
- 全 n_core_bin で Q1 が他の Q を上回る場合、入力対象を「累積 c_inherited < 3 の cid」に絞る
