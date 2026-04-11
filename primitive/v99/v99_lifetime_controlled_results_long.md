# v9.9 Lifetime-Controlled Results (long)

*Generated*: 2026-04-12
*Source*: `/home/takasan/esde/ESDE-Research/primitive/v99/diag_v99_internal_axis_long` (48 seeds)

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
- **Input**: 1112 cid rows across 5 seeds
- **With history**: 648 cid rows have ≥1 introspection entry (cid without history → L01 with n=0 → skipped from 'with hist' count but still tallied)

---

## Step 1: lifetime bin distribution (cell counts)

| lifetime      |  count |  share |
|---|---:|---:|
| L01_very_short |    735 |  66.1% |
| L02_short     |    157 |  14.1% |
| L03_medium    |     67 |   6.0% |
| L04_long      |     39 |   3.5% |
| L05_very_long |     41 |   3.7% |
| L06_extreme   |     73 |   6.6% |
| **total**     | **1112** |  |

## Step 1b: formation_status × lifetime

| lifetime      |  count |      formed |    unformed |
|---|---|---|---|
| L01_very_short |    735 |    0 ( 0.0%)|  735 (100.0%)|
| L02_short     |    157 |   46 (29.3%)|  111 (70.7%)|
| L03_medium    |     67 |   28 (41.8%)|   39 (58.2%)|
| L04_long      |     39 |   28 (71.8%)|   11 (28.2%)|
| L05_very_long |     41 |   29 (70.7%)|   12 (29.3%)|
| L06_extreme   |     73 |   73 (100.0%)|    0 ( 0.0%)|

## Step 1c: lowest_std_axis × lifetime

| lifetime      |  count |      spread |   stability |      social | familiarity |         tie |    unformed |
|---|---|---|---|---|---|---|---|
| L01_very_short |    735 |    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|  735 (100.0%)|
| L02_short     |    157 |   25 (15.9%)|   17 (10.8%)|    4 ( 2.5%)|    0 ( 0.0%)|    0 ( 0.0%)|  111 (70.7%)|
| L03_medium    |     67 |   19 (28.4%)|    6 ( 9.0%)|    3 ( 4.5%)|    0 ( 0.0%)|    0 ( 0.0%)|   39 (58.2%)|
| L04_long      |     39 |   21 (53.8%)|    4 (10.3%)|    3 ( 7.7%)|    0 ( 0.0%)|    0 ( 0.0%)|   11 (28.2%)|
| L05_very_long |     41 |   21 (51.2%)|    5 (12.2%)|    3 ( 7.3%)|    0 ( 0.0%)|    0 ( 0.0%)|   12 (29.3%)|
| L06_extreme   |     73 |   54 (74.0%)|    5 ( 6.8%)|   14 (19.2%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|

## Step 1d: dominant_positive_drift_axis × lifetime

| lifetime      |  count | familiarity |      social |   stability |      spread |        none |         tie |    unformed |
|---|---|---|---|---|---|---|---|---|
| L01_very_short |    735 |    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|  735 (100.0%)|
| L02_short     |    157 |    5 ( 3.2%)|    9 ( 5.7%)|    2 ( 1.3%)|    1 ( 0.6%)|   21 (13.4%)|    8 ( 5.1%)|  111 (70.7%)|
| L03_medium    |     67 |   10 (14.9%)|    4 ( 6.0%)|    0 ( 0.0%)|    1 ( 1.5%)|   12 (17.9%)|    1 ( 1.5%)|   39 (58.2%)|
| L04_long      |     39 |   19 (48.7%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    9 (23.1%)|    0 ( 0.0%)|   11 (28.2%)|
| L05_very_long |     41 |   22 (53.7%)|    1 ( 2.4%)|    0 ( 0.0%)|    0 ( 0.0%)|    5 (12.2%)|    1 ( 2.4%)|   12 (29.3%)|
| L06_extreme   |     73 |   42 (57.5%)|    1 ( 1.4%)|    0 ( 0.0%)|    0 ( 0.0%)|   27 (37.0%)|    3 ( 4.1%)|    0 ( 0.0%)|

## Step 1e: dominant_negative_drift_axis × lifetime

| lifetime      |  count | familiarity |      social |   stability |      spread |        none |         tie |    unformed |
|---|---|---|---|---|---|---|---|---|
| L01_very_short |    735 |    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|  735 (100.0%)|
| L02_short     |    157 |   44 (28.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    1 ( 0.6%)|    1 ( 0.6%)|  111 (70.7%)|
| L03_medium    |     67 |   22 (32.8%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    4 ( 6.0%)|    2 ( 3.0%)|   39 (58.2%)|
| L04_long      |     39 |   24 (61.5%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    3 ( 7.7%)|    1 ( 2.6%)|   11 (28.2%)|
| L05_very_long |     41 |   23 (56.1%)|    0 ( 0.0%)|    2 ( 4.9%)|    0 ( 0.0%)|    4 ( 9.8%)|    0 ( 0.0%)|   12 (29.3%)|
| L06_extreme   |     73 |   40 (54.8%)|    1 ( 1.4%)|    1 ( 1.4%)|    0 ( 0.0%)|   25 (34.2%)|    6 ( 8.2%)|    0 ( 0.0%)|

## Step 2-1: familiarity negative dominance (formed のみ)

観察: 全集約 82.7% familiarity。lifetime bin 内で維持されるか?

| lifetime      |  count | familiarity |      social |   stability |      spread |        none |         tie |
|---|---|---|---|---|---|---|---|
| L02_short     |     46 |   44 (95.7%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    1 ( 2.2%)|    1 ( 2.2%)|
| L03_medium    |     28 |   22 (78.6%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    4 (14.3%)|    2 ( 7.1%)|
| L04_long      |     28 |   24 (85.7%)|    0 ( 0.0%)|    0 ( 0.0%)|    0 ( 0.0%)|    3 (10.7%)|    1 ( 3.6%)|
| L05_very_long |     29 |   23 (79.3%)|    0 ( 0.0%)|    2 ( 6.9%)|    0 ( 0.0%)|    4 (13.8%)|    0 ( 0.0%)|
| L06_extreme   |     73 |   40 (54.8%)|    1 ( 1.4%)|    1 ( 1.4%)|    0 ( 0.0%)|   25 (34.2%)|    6 ( 8.2%)|

## Step 2-2: lowest_std = spread 比率 (formed のみ)

観察: 全集約 67.6% spread。lifetime 依存か?

| lifetime      |  count |      spread |   stability |      social | familiarity |         tie |
|---|---|---|---|---|---|---|
| L02_short     |     46 |   25 (54.3%)|   17 (37.0%)|    4 ( 8.7%)|    0 ( 0.0%)|    0 ( 0.0%)|
| L03_medium    |     28 |   19 (67.9%)|    6 (21.4%)|    3 (10.7%)|    0 ( 0.0%)|    0 ( 0.0%)|
| L04_long      |     28 |   21 (75.0%)|    4 (14.3%)|    3 (10.7%)|    0 ( 0.0%)|    0 ( 0.0%)|
| L05_very_long |     29 |   21 (72.4%)|    5 (17.2%)|    3 (10.3%)|    0 ( 0.0%)|    0 ( 0.0%)|
| L06_extreme   |     73 |   54 (74.0%)|    5 ( 6.8%)|   14 (19.2%)|    0 ( 0.0%)|    0 ( 0.0%)|

## Step 2-3: effective_ttl × formation_status × lifetime

観察: effective_ttl ≥12 で 100% formed (seed 0)。lifetime 統制で有意か、境界効果か?

| lifetime      | ttl 10 formed/total | ttl 11 formed/total | ttl 12+ formed/total |
|---|---|---|---|
| L01_very_short |   0/616 (   0%) |   0/98  (   0%) |   0/21  (   0%) |
| L02_short     |  22/80  (  28%) |  13/53  (  25%) |  11/24  (  46%) |
| L03_medium    |  12/25  (  48%) |   7/21  (  33%) |   9/21  (  43%) |
| L04_long      |   9/11  (  82%) |   4/7   (  57%) |  15/21  (  71%) |
| L05_very_long |   2/2   ( 100%) |   6/10  (  60%) |  21/29  (  72%) |
| L06_extreme   |   5/5   ( 100%) |   2/2   ( 100%) |  66/66  ( 100%) |

## Step 3: 同 lifetime bin 内の familiarity dominance 分散

各 lifetime bin 内での negative dominant axis 分布の entropy (bit 数)
= 0 なら bin 内で 1 軸集中、> 1 で bin 内にまだ分散が残る

| lifetime      | formed | fam%  | top2 %  | entropy (bit) |
|---|---:|---:|---:|---:|
| L02_short     |     46 | 95.7% | 97.8% | 0.301 |
| L03_medium    |     28 | 78.6% | 92.9% | 0.946 |
| L04_long      |     28 | 85.7% | 96.4% | 0.708 |
| L05_very_long |     29 | 79.3% | 93.1% | 0.926 |
| L06_extreme   |     73 | 54.8% | 89.0% | 1.471 |
