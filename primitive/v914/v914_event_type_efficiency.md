# v9.14 §6.1 — Event-type Efficiency

*Phase 2 §6.1 output — Describe only.*


## 1. 計算方法

- 入力: `diag_v914_{short,long}/audit/per_event_audit_seed*.csv` (短 48 seeds / 長 5 seeds)、`per_subject_audit_seed*.csv` (n_core マップ用)。
- 集計単位: event 種別 (E1_death / E1_birth / E2_rise / E2_fall / E3_contact)、および event 種 × n_core バケット (2 / 3 / 4 / 5+)。
- `event_count` は全 event、`spend_count`/`delta_*`/`attention_delta_*`/`familiarity_delta_*` は `v14_spend_flag=True` の event のみを対象。
- `exhaustion_contribution` は各 (seed, cid) 内でその event 種が占める `spend 回数 / q_spent_total` 比を cid 平均したもの (q_spent_total=0 の cid は除外)。
- n_core バケット = `per_subject_audit.n_core_member` を 2/3/4/5+ に集約 (v9.14 慣習)。

## 2. Short run: event 種別集計

| event_type | event_count | spend_count | spend_rate | delta_mean | delta_p50 | delta_p90 | attention_delta_mean | attention_delta_p50 | familiarity_delta_mean | familiarity_delta_p50 | exhaustion_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1_death | 3331 | 3331 | 1 | 0.1902 | 0.1856 | 0.3347 | 21.17 | 11 | 0.9442 | 1 | 0.2068 |
| E1_birth | 94 | 93 | 0.9894 | 0.2632 | 0.2642 | 0.4178 | 46.08 | 39 | 0.871 | 0 | 0.06789 |
| E2_rise | 2660 | 2660 | 1 | 0.03933 | 0.01488 | 0.06647 | 22.29 | 13 | 1.396 | 1 | 0.1712 |
| E2_fall | 2660 | 2660 | 1 | 0.09345 | 0 | 0.2715 | 19.31 | 12 | 1.241 | 1 | 0.1712 |
| E3_contact | 17151 | 16988 | 0.9905 | 0.1943 | 0.1979 | 0.3579 | 31.28 | 20 | 1.608 | 1 | 0.6504 |


## 3. Long run: event 種別集計

| event_type | event_count | spend_count | spend_rate | delta_mean | delta_p50 | delta_p90 | attention_delta_mean | attention_delta_p50 | familiarity_delta_mean | familiarity_delta_p50 | exhaustion_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1_death | 1659 | 1615 | 0.9735 | 0.1829 | 0.1753 | 0.3271 | 19.44 | 11 | 1.051 | 1 | 0.158 |
| E1_birth | 67 | 25 | 0.3731 | 0.2479 | 0.2676 | 0.3775 | 47.36 | 42 | 0.88 | 0 | 0.03676 |
| E2_rise | 1296 | 1295 | 0.9992 | 0.03282 | 0.0146 | 0.05188 | 22.18 | 12 | 1.454 | 1 | 0.1367 |
| E2_fall | 1296 | 1295 | 0.9992 | 0.09061 | 0 | 0.2659 | 19.52 | 12 | 1.319 | 1 | 0.1367 |
| E3_contact | 21154 | 8986 | 0.4248 | 0.1707 | 0.1759 | 0.329 | 25.73 | 14 | 1.429 | 1 | 0.6497 |


## 4. Short run: event 種 × n_core バケット

| bucket | event_type | event_count | spend_count | spend_rate | delta_mean | delta_p50 | delta_p90 | attention_delta_mean | attention_delta_p50 | familiarity_delta_mean | familiarity_delta_p50 | exhaustion_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | E1_death | 1643 | 1643 | 1 | 0.1933 | 0.1921 | 0.318 | 7.621 | 7 | 1.186 | 1 | 0.1976 |
| 2 | E1_birth | 0 | 0 | - | - | - | - | - | - | - | - | - |
| 2 | E2_rise | 1394 | 1394 | 1 | 0.02673 | 0.01906 | 0.04862 | 10.12 | 10 | 1.928 | 2 | 0.1643 |
| 2 | E2_fall | 1394 | 1394 | 1 | 0.1383 | 0.139 | 0.2956 | 9.079 | 9 | 1.74 | 2 | 0.1643 |
| 2 | E3_contact | 6456 | 6379 | 0.9881 | 0.15 | 0.1584 | 0.3105 | 9.26 | 9 | 1.654 | 2 | 0.5923 |
| 3 | E1_death | 284 | 284 | 1 | 0.2037 | 0.1928 | 0.3481 | 14.46 | 13 | 0.5845 | 0 | 0.3177 |
| 3 | E1_birth | 4 | 4 | 1 | 0.2791 | 0.2627 | 0.3815 | 12.75 | 13 | 0.25 | 0 | 0.1059 |
| 3 | E2_rise | 150 | 150 | 1 | 0.04818 | 0 | 0.1948 | 15.88 | 13 | 1.047 | 1 | 0.2116 |
| 3 | E2_fall | 150 | 150 | 1 | 0.06697 | 0 | 0.2352 | 16.15 | 15 | 0.9867 | 0.5 | 0.2116 |
| 3 | E3_contact | 1205 | 1186 | 0.9842 | 0.1904 | 0.1935 | 0.3385 | 17.59 | 17 | 1.242 | 1 | 0.7157 |
| 4 | E1_death | 432 | 432 | 1 | 0.1781 | 0.1605 | 0.3481 | 24.92 | 22 | 0.7037 | 0 | 0.2517 |
| 4 | E1_birth | 7 | 7 | 1 | 0.2332 | 0.2183 | 0.3247 | 30.29 | 21 | 0.8571 | 1 | 0.06684 |
| 4 | E2_rise | 294 | 294 | 1 | 0.04362 | 0 | 0.1598 | 22.71 | 20.5 | 0.7585 | 0 | 0.1937 |
| 4 | E2_fall | 294 | 294 | 1 | 0.04932 | 0 | 0.2101 | 21.39 | 20 | 0.6395 | 0 | 0.1937 |
| 4 | E3_contact | 2597 | 2571 | 0.99 | 0.2075 | 0.2104 | 0.3571 | 31.77 | 29 | 1.368 | 1 | 0.7623 |
| 5+ | E1_death | 972 | 972 | 1 | 0.1864 | 0.1768 | 0.3504 | 44.36 | 38 | 0.7469 | 0 | 0.189 |
| 5+ | E1_birth | 83 | 82 | 0.988 | 0.265 | 0.2657 | 0.429 | 49.05 | 39 | 0.9024 | 0.5 | 0.06594 |
| 5+ | E2_rise | 822 | 822 | 1 | 0.05753 | 0 | 0.3075 | 43.94 | 40 | 0.7871 | 0 | 0.2011 |
| 5+ | E2_fall | 822 | 822 | 1 | 0.03805 | 0 | 0.1622 | 36.5 | 32 | 0.6582 | 0 | 0.2011 |
| 5+ | E3_contact | 6893 | 6852 | 0.9941 | 0.2314 | 0.2305 | 0.401 | 53.96 | 50 | 1.718 | 1 | 0.7742 |


## 5. Long run: event 種 × n_core バケット

| bucket | event_type | event_count | spend_count | spend_rate | delta_mean | delta_p50 | delta_p90 | attention_delta_mean | attention_delta_p50 | familiarity_delta_mean | familiarity_delta_p50 | exhaustion_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | E1_death | 824 | 824 | 1 | 0.1896 | 0.188 | 0.3162 | 7.708 | 7 | 1.189 | 1 | 0.1556 |
| 2 | E1_birth | 0 | 0 | - | - | - | - | - | - | - | - | - |
| 2 | E2_rise | 690 | 690 | 1 | 0.0278 | 0.01927 | 0.04661 | 9.68 | 10 | 1.843 | 2 | 0.1338 |
| 2 | E2_fall | 690 | 690 | 1 | 0.1374 | 0.1438 | 0.2922 | 9.116 | 9 | 1.683 | 2 | 0.1338 |
| 2 | E3_contact | 5292 | 4354 | 0.8228 | 0.1436 | 0.1496 | 0.2996 | 8.743 | 8 | 1.37 | 1 | 0.636 |
| 3 | E1_death | 106 | 105 | 0.9906 | 0.1928 | 0.1885 | 0.3457 | 13.37 | 12 | 0.6476 | 0 | 0.2298 |
| 3 | E1_birth | 1 | 1 | 1 | 0.09694 | 0.09694 | 0.09694 | 7 | 7 | 0 | 0 | 0.05556 |
| 3 | E2_rise | 42 | 42 | 1 | 0.03445 | 0 | 0.1712 | 15.02 | 14 | 1.167 | 1 | 0.169 |
| 3 | E2_fall | 42 | 42 | 1 | 0.05193 | 0 | 0.2228 | 11 | 7.5 | 0.7381 | 0 | 0.169 |
| 3 | E3_contact | 1317 | 588 | 0.4465 | 0.1757 | 0.1814 | 0.3138 | 17.41 | 16 | 1.054 | 1 | 0.7304 |
| 4 | E1_death | 229 | 223 | 0.9738 | 0.1585 | 0.1343 | 0.2997 | 24.48 | 22 | 0.8744 | 1 | 0.1617 |
| 4 | E1_birth | 10 | 4 | 0.4 | 0.2259 | 0.2204 | 0.3235 | 20 | 17 | 0.25 | 0 | 0.03849 |
| 4 | E2_rise | 151 | 151 | 1 | 0.04823 | 0 | 0.1942 | 21.13 | 20 | 0.7616 | 0 | 0.1455 |
| 4 | E2_fall | 151 | 151 | 1 | 0.04467 | 0 | 0.1811 | 21.45 | 20 | 0.9338 | 0 | 0.1455 |
| 4 | E3_contact | 4420 | 1246 | 0.2819 | 0.1821 | 0.1885 | 0.3346 | 31.16 | 29 | 1.291 | 1 | 0.6892 |
| 5+ | E1_death | 500 | 463 | 0.926 | 0.1805 | 0.1623 | 0.3437 | 39.26 | 34 | 0.9827 | 1 | 0.142 |
| 5+ | E1_birth | 56 | 20 | 0.3571 | 0.2599 | 0.2713 | 0.3837 | 54.85 | 50 | 1.05 | 0.5 | 0.03525 |
| 5+ | E2_rise | 413 | 412 | 0.9976 | 0.03543 | 0 | 0.07629 | 44.24 | 41 | 1.085 | 1 | 0.1491 |
| 5+ | E2_fall | 413 | 412 | 0.9976 | 0.03303 | 0 | 0.1488 | 37.09 | 28 | 0.9102 | 1 | 0.1491 |
| 5+ | E3_contact | 10125 | 2798 | 0.2763 | 0.2069 | 0.209 | 0.3749 | 51.48 | 47 | 1.659 | 1 | 0.6809 |


## 6. 観察事項 (Describe, do not decide)

1. Short run の event_count は E3_contact=17151, E1_death=3331, E2_rise=2660, E2_fall=2660, E1_birth=94。
2. Long run の event_count は E3_contact=21154, E1_death=1659, E2_rise=1296, E2_fall=1296, E1_birth=67。
3. Short run の spend_rate は全 event type で E1_death=1, E1_birth=0.9894, E2_rise=1, E2_fall=1, E3_contact=0.9905。
4. Long run の spend_rate は E1_death=0.9735, E1_birth=0.3731, E2_rise=0.9992, E2_fall=0.9992, E3_contact=0.4248。
5. Long run の delta_mean (spend のみ) は E1_death=0.1829, E1_birth=0.2479, E2_rise=0.03282, E2_fall=0.09061, E3_contact=0.1707。
6. Long run の attention_delta_mean は E1_death=19.44, E2_rise=22.18, E3_contact=25.73。
7. Long run の familiarity_delta_mean は E1_death=1.051, E2_rise=1.454, E3_contact=1.429。
8. Long run の exhaustion_contribution (各 event 種が cid の q_spent に 占める平均割合) は E1_death=0.158, E2_rise=0.1367, E3_contact=0.6497。
9. Long run E3_contact の event_count (n_core バケット別): bucket=2: 5292, bucket=3: 1317, bucket=4: 4420, bucket=5+: 10125。
10. Long run E3_contact の spend_rate (n_core バケット別): bucket=2: 0.8228, bucket=3: 0.4465, bucket=4: 0.2819, bucket=5+: 0.2763。

---

*End of §6.1 report.*