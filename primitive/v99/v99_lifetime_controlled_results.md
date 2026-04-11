# v9.9 Lifetime-Controlled Results (short)

*Generated*: 2026-04-12
*Source*: `/home/takasan/esde/ESDE-Research/primitive/v99/diag_v99_internal_axis_short` (48 seeds)

## Definitions

- **lifetime** = length of introspection history per (seed, cid) from `introspection/introspection_log_seed*.csv`
  (v9.8c+ と同一定義、v99 でも同じ列構造のログを継承)
- **lifetime bins** (v9.8c+ と一致):
  - `L01_very_short` : 1-2 win
  - `L02_short`      : 3-5 win
  - `L03_medium`     : 6-10 win
  - `L04_long`       : 11-20 win
  - `L05_very_long`  : 21-35 win
  - `L06_extreme`    : 36+ win
- **Input**: 2979 cid rows across 48 seeds
- **With history**: 1879 cid rows have ≥1 introspection entry (cid without history → L01 with n=0 → skipped from 'with hist' count but still tallied)

---

## Step 1: lifetime bin distribution (cell counts)

| lifetime      |  count |  share |
|---|---:|---:|
| L01_very_short |   1827 |  61.3% |
| L02_short     |    377 |  12.7% |
| L03_medium    |    775 |  26.0% |
| **total**     | **2979** |  |

## Step 1b: formation_status × lifetime

| lifetime      |  count |      formed |    unformed |
|---|---|---|---|
| L01_very_short |   1827 |    0 ( 0.0%)| 1827 (100.0%)|
| L02_short     |    377 |  377 (100.0%)|    0 ( 0.0%)|
| L03_medium    |    775 |  775 (100.0%)|    0 ( 0.0%)|

## Step 1c: lowest_std_axis × lifetime

| lifetime      |  count |      spread |   stability |      social | familiarity |         tie |    unformed |
|---|---|---|---|---|---|---|---|
| L01_very_short |   1827 |    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)| 1827 (100.0%)|
| L02_short     |    377 |  199 (52.8%)|   99 (26.3%)|   79 (21.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|
| L03_medium    |    775 |  580 (74.8%)|  115 (14.8%)|   80 (10.3%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|

## Step 1d: dominant_positive_drift_axis × lifetime

| lifetime      |  count | familiarity |      social |   stability |      spread |        none |         tie |    unformed |
|---|---|---|---|---|---|---|---|---|
| L01_very_short |   1827 |    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)| 1827 (100.0%)|
| L02_short     |    377 |   98 (26.0%)|   74 (19.6%)|   11 ( 2.9%)|   11 ( 2.9%)|  123 (32.6%)|   60 (15.9%)|    0 ( 0.0%)|
| L03_medium    |    775 |  409 (52.8%)|   40 ( 5.2%)|   15 ( 1.9%)|    8 ( 1.0%)|  202 (26.1%)|  101 (13.0%)|    0 ( 0.0%)|

## Step 1e: dominant_negative_drift_axis × lifetime

| lifetime      |  count | familiarity |      social |   stability |      spread |        none |         tie |    unformed |
|---|---|---|---|---|---|---|---|---|
| L01_very_short |   1827 |    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)| 1827 (100.0%)|
| L02_short     |    377 |  356 (94.4%)|    0 ( 0.0%)|    2 ( 0.5%)|    0 ( 0.0%)|    9 ( 2.4%)|   10 ( 2.7%)|    0 ( 0.0%)|
| L03_medium    |    775 |  597 (77.0%)|   18 ( 2.3%)|    7 ( 0.9%)|    2 ( 0.3%)|  101 (13.0%)|   50 ( 6.5%)|    0 ( 0.0%)|

## Step 2-1: familiarity negative dominance (formed のみ)

観察: 全集約 82.7% familiarity。lifetime bin 内で維持されるか?

| lifetime      |  count | familiarity |      social |   stability |      spread |        none |         tie |
|---|---|---|---|---|---|---|---|
| L02_short     |    377 |  356 (94.4%)|    0 ( 0.0%)|    2 ( 0.5%)|    0 ( 0.0%)|    9 ( 2.4%)|   10 ( 2.7%)|
| L03_medium    |    775 |  597 (77.0%)|   18 ( 2.3%)|    7 ( 0.9%)|    2 ( 0.3%)|  101 (13.0%)|   50 ( 6.5%)|

## Step 2-2: lowest_std = spread 比率 (formed のみ)

観察: 全集約 67.6% spread。lifetime 依存か?

| lifetime      |  count |      spread |   stability |      social | familiarity |         tie |
|---|---|---|---|---|---|---|
| L02_short     |    377 |  199 (52.8%)|   99 (26.3%)|   79 (21.0%)|    0 ( 0.0%)|    0 ( 0.0%)|
| L03_medium    |    775 |  580 (74.8%)|  115 (14.8%)|   80 (10.3%)|    0 ( 0.0%)|    0 ( 0.0%)|

## Step 2-3: effective_ttl × formation_status × lifetime

観察: effective_ttl ≥12 で 100% formed (seed 0)。lifetime 統制で有意か、境界効果か?

| lifetime      | ttl 10 formed/total | ttl 11 formed/total | ttl 12+ formed/total |
|---|---|---|---|
| L01_very_short |   0/1450 (   0%) |   0/320 (   0%) |   0/57  (   0%) |
| L02_short     | 165/165 ( 100%) | 140/140 ( 100%) |  72/72  ( 100%) |
| L03_medium    | 185/185 ( 100%) | 240/240 ( 100%) | 350/350 ( 100%) |

## Step 3: 同 lifetime bin 内の familiarity dominance 分散

各 lifetime bin 内での negative dominant axis 分布の entropy (bit 数)
= 0 なら bin 内で 1 軸集中、> 1 で bin 内にまだ分散が残る

| lifetime      | formed | fam%  | top2 %  | entropy (bit) |
|---|---:|---:|---:|---:|
| L02_short     |    377 | 94.4% | 97.1% | 0.386 |
| L03_medium    |    775 | 77.0% | 90.1% | 1.138 |
