# v9.10 stability 残差切り分け調査

*Generated*: 2026-04-12
*Source*: `diag_v910_pulse_long` (5 seeds, active pulses only)
*目的*: L06 での stability 17.7% 残差が「観測器の癖」か「ESDE 性質」かの Stage A 検証

---

## 1. 4 軸の計算式 (並列比較)

全て `v910_pulse_model.py` 行 1371-1374 (pulse 発火時) から:
```python
d_soc_p = cog.get_n_partners(cid_p) / max_n_p
d_sta_p = 1.0 / (1.0 + st_std_p / (st_mean_p + EPS))
d_spr_p = cog.get_attention_entropy(cid_p)
d_fam_p = cog.get_familiarity_mean(cid_p)
```

| 軸 | 式 | 入力 | 値域 | 更新頻度 |
|---|---|---|---|---|
| social      | n_partners / max_all              | familiarity dict       | [0,1] | 毎 step (fam 更新) |
| **stability** | **1/(1 + std/mean)**           | **window 内 st_sizes** | **(0,1]** | **window 内累積** |
| spread      | Shannon H / log(n)                | attention map          | [0,1] | 毎 step (att 更新) |
| familiarity | mean(fam_values)                  | familiarity dict       | [0,∞) | 毎 step (fam 更新) |

★ **stability の特異性**:
- 入力が `window_st_sizes[cid]` — **window 先頭でリセットされる累積バッファ**
- pulse t=0 (window 先頭直後) では st_sizes に 1 entry しかなく std=0 → stability=1.0 固定
- pulse t=450 (window 末近く) では st_sizes に ~451 entries → std が安定
- 他 3 軸 (social/spread/familiarity) は累積的な dict (全 window にまたがる) から計算、window リセットなし
- → **stability だけ window 内位置に強く依存する「ノコギリ波」特性を持つ**

## 2. |delta| 生分布 (4 軸並列、active pulses)

| 軸 | n | min | p10 | p25 | p50 | p75 | p90 | p99 | max | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| social | 72264 | 0.000000 | 0.000000 | 0.000000 | 0.001461 | 0.019133 | 0.030303 | 0.069444 | 0.454545 | 0.011136 |
| **stability** | 72264 | 0.000000 | 0.002621 | 0.006622 | 0.014470 | 0.036466 | 0.115390 | 0.301389 | 0.471175 | 0.038951 |
| spread | 72264 | 0.000000 | 0.001210 | 0.003045 | 0.006659 | 0.012271 | 0.020053 | 0.043367 | 0.129211 | 0.009176 |
| familiarity | 72264 | 0.000000 | 0.138182 | 0.347402 | 0.697811 | 1.268397 | 2.804778 | 16.839656 | 236.258055 | 1.527457 |

## 3. theta 分布 (per_subject v10_theta_*_last、全 cid)

| 軸 | n | p10 | p25 | p50 | p75 | p90 | p99 | max | near_zero(<1e-5)% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| social | 1112 | 0.000000 | 0.000000 | 0.000000 | 0.004973 | 0.010177 | 0.022817 | 0.048440 | 66.9% |
| **stability** | 1112 | 0.000000 | 0.000000 | 0.000000 | 0.028770 | 0.044375 | 0.074664 | 0.085100 | 66.7% |
| spread | 1112 | 0.000000 | 0.000000 | 0.000000 | 0.007189 | 0.015230 | 0.028437 | 0.059665 | 66.7% |
| familiarity | 1112 | 0.000000 | 0.000000 | 0.000000 | 0.614261 | 4.031464 | 16.133201 | 43.763321 | 66.7% |

## 4. R 分布 (pulse_log active pulses)

| 軸 | n | min | p10 | p25 | p50 | p75 | p90 | p99 | max | |R|≤1 % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| social | 72264 | -19.995 | -1.520 | 0.000 | 0.000 | 0.714 | 2.064 | 5.427 | 19.992 | 62.6% |
| **stability** | 72264 | -8.600 | -1.524 | -0.538 | -0.018 | 0.290 | 0.944 | 5.711 | 11.073 | 75.0% |
| spread | 72264 | -8.522 | -1.658 | -0.892 | -0.128 | 0.666 | 1.401 | 2.853 | 5.322 | 60.7% |
| familiarity | 72264 | -6.699 | -1.228 | -0.780 | -0.307 | 0.506 | 1.454 | 3.612 | 20.000 | 68.0% |

## 5. lifetime bin 別 stability Normal 発火率 (4 軸並列)

各 bin の active pulse 中の Normal gain+loss 率:

| bin | pulses | soc gain+loss (%) | sta gain+loss (%) | spr gain+loss (%) | fam gain+loss (%) |
|---|---:|---:|---:|---:|---:|
| L01 |   8935 |  2202 (24.6%) |  1492 (16.7%) |  3088 (34.6%) |   861 ( 9.6%) |
| L02 |   6969 |  1821 (26.1%) |  1685 (24.2%) |  2613 (37.5%) |  1023 (14.7%) |
| L03 |   5339 |  1660 (31.1%) |  1361 (25.5%) |  2011 (37.7%) |  1174 (22.0%) |
| L04 |   6143 |  2301 (37.5%) |  1594 (25.9%) |  2433 (39.6%) |  2020 (32.9%) |
| L05 |  11207 |  4711 (42.0%) |  2985 (26.6%) |  4553 (40.6%) |  4337 (38.7%) |
| L06 |  33671 | 14313 (42.5%) |  8964 (26.6%) | 13668 (40.6%) | 13739 (40.8%) |

## 6. 一次判定

|delta| p50 比較: social=0.001461, stability=0.014470, spread=0.006659, familiarity=0.697811
|delta| p90 比較: social=0.030303, stability=0.115390, spread=0.020053, familiarity=2.804778

|R|≤1.0 率: social=62.6%, stability=75.0%, spread=60.7%, familiarity=68.0%

theta near-zero (<1e-5) 率: social=66.9%, stability=66.7%, spread=66.7%, familiarity=66.7%

### 観測器の癖の候補:

1. **window_st_sizes リセット問題**: stability は window 先頭で st_sizes が空になり、
   初期 pulse では std=0 → stability=1.0 → delta≈0。window 内位置依存の「ノコギリ波」
   が delta を系統的に圧縮する。他 3 軸にはこの特性がない。

2. **1/(1+x) 圧縮関数**: stability = 1/(1+std/mean) は std が小さいとき
   1.0 に張り付き、std が大きいときに急落する非線形圧縮。
   pulse 間隔 50 step で std の変動が小さいと delta が微小になる。

**一次判定**: 観測器の癖の候補 **あり**
  根拠: |R|≤1 率が stability=75.0% で他軸 (60.7-68.0%) より 高い
  根拠: window_st_sizes リセットによるノコギリ波特性が stability 固有
  注: ESDE 性質の可能性は否定できない (Stage B/C 未実施)