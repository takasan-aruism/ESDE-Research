# v9.14 §6.4 — E3 Ablation Result

*Phase 2 §6.4 output — Describe only.*


## 1. 実装 (flag + smoke + bit-identity)

- **CLI flag**: `--disable-e3` (action=store_true, default False)
- **挙動**: E3 event 発行を skip、contacted_pairs 登録は継続、E1/E2 検知・spend packet は不変。Layer A 完全不変。
- **smoke 条件**: 1 seed × maturation 20 / tracking 10 / steps 500
- **bit-identity**: (run smoke and fill in)

## 2. Ablation run の実行結果

- **short ablation 出力**: /home/takasan/esde/ESDE-Research/primitive/v914/diag_v914_short_noE3
- **long ablation 出力**: /home/takasan/esde/ESDE-Research/primitive/v914/diag_v914_long_noE3
- **実行条件 short**: 48 seeds × mat 20 / track 10 / steps 500, parallel -j24
- **実行条件 long**: 5 seeds × mat 20 / track 50 / steps 500, parallel -j5
- **実行時間**: short wall ~82m (resumed for seeds 24-47); long_noE3 wall 9171s avg (5 seed)

## 3.1 Short run: E3 有効 vs 無効 比較

| bucket | n_cids_base | n_cids_abl | n_cids_rel | q0_mean_base | q0_mean_abl | q0_mean_rel | q_spent_mean_base | q_spent_mean_abl | q_spent_mean_rel | exhaustion_ratio_base | exhaustion_ratio_abl | exhaustion_ratio_rel | event_count_base | event_count_abl | event_count_rel | spend_count_base | spend_count_abl | spend_count_rel | event_to_spend_base | event_to_spend_abl | event_to_spend_rel | attn_per_spend_base | attn_per_spend_abl | attn_per_spend_rel | fam_per_spend_base | fam_per_spend_abl | fam_per_spend_rel | count_E1_death_base | count_E1_death_abl | count_E1_death_rel | count_E1_birth_base | count_E1_birth_abl | count_E1_birth_rel | count_E2_rise_base | count_E2_rise_abl | count_E2_rise_rel | count_E2_fall_base | count_E2_fall_abl | count_E2_fall_rel | count_E3_contact_base | count_E3_contact_abl | count_E3_contact_rel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 2e+03 | 2e+03 | 1 | 11.49 | 11.49 | 1 | 5.498 | 2.254 | 0.4099 | 0.02645 | 0 | 0 | 1e+04 | 4e+03 | 0.407 | 1e+04 | 4e+03 | 0.4099 | 1.007 | 1 | 0.9929 | 9.098 | 8.865 | 0.9744 | 1.629 | 1.594 | 0.9783 | 2e+03 | 2e+03 | 1 | 0 | 0 | - | 1e+03 | 1e+03 | 1 | 1e+03 | 1e+03 | 1 | 6e+03 | 0 | 0 |
| 3 | 2e+02 | 2e+02 | 1 | 18.33 | 18.33 | 1 | 8.251 | 2.735 | 0.3315 | 0.02791 | 0 | 0 | 2e+03 | 6e+02 | 0.3279 | 2e+03 | 6e+02 | 0.3315 | 1.011 | 1 | 0.9894 | 16.81 | 15.24 | 0.9066 | 1.096 | 0.8027 | 0.7321 | 3e+02 | 3e+02 | 1 | 4 | 4 | 1 | 2e+02 | 2e+02 | 1 | 2e+02 | 2e+02 | 1 | 1e+03 | 0 | 0 |
| 4 | 3e+02 | 3e+02 | 1 | 25.69 | 25.69 | 1 | 13.84 | 3.95 | 0.2854 | 0.03462 | 0 | 0 | 4e+03 | 1e+03 | 0.2834 | 4e+03 | 1e+03 | 0.2854 | 1.007 | 1 | 0.9928 | 29.36 | 23.31 | 0.7942 | 1.178 | 0.702 | 0.596 | 4e+02 | 4e+02 | 1 | 7 | 7 | 1 | 3e+02 | 3e+02 | 1 | 3e+02 | 3e+02 | 1 | 3e+03 | 0 | 0 |
| 5+ | 5e+02 | 5e+02 | 1 | 33.4 | 33.4 | 1 | 17.75 | 5.017 | 0.2826 | 0.0316 | 0 | 0 | 1e+04 | 3e+03 | 0.2814 | 1e+04 | 3e+03 | 0.2826 | 1.004 | 1 | 0.9956 | 50.57 | 41.99 | 0.8302 | 1.441 | 0.7369 | 0.5114 | 1e+03 | 1e+03 | 1 | 8e+01 | 8e+01 | 1 | 8e+02 | 8e+02 | 1 | 8e+02 | 8e+02 | 1 | 7e+03 | 0 | 0 |


## 3.2 Long run: E3 有効 vs 無効 比較

| bucket | n_cids_base | n_cids_abl | n_cids_rel | q0_mean_base | q0_mean_abl | q0_mean_rel | q_spent_mean_base | q_spent_mean_abl | q_spent_mean_rel | exhaustion_ratio_base | exhaustion_ratio_abl | exhaustion_ratio_rel | event_count_base | event_count_abl | event_count_rel | spend_count_base | spend_count_abl | spend_count_rel | event_to_spend_base | event_to_spend_abl | event_to_spend_rel | attn_per_spend_base | attn_per_spend_abl | attn_per_spend_rel | fam_per_spend_base | fam_per_spend_abl | fam_per_spend_rel | count_E1_death_base | count_E1_death_abl | count_E1_death_rel | count_E1_birth_base | count_E1_birth_abl | count_E1_birth_rel | count_E2_rise_base | count_E2_rise_abl | count_E2_rise_rel | count_E2_fall_base | count_E2_fall_abl | count_E2_fall_rel | count_E3_contact_base | count_E3_contact_abl | count_E3_contact_rel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 9e+02 | 9e+02 | 1 | 11.55 | 11.55 | 1 | 7.706 | 2.59 | 0.3361 | 0.2209 | 0 | 0 | 7e+03 | 2e+03 | 0.294 | 7e+03 | 2e+03 | 0.3361 | 1.143 | 1 | 0.8749 | 8.751 | 8.766 | 1.002 | 1.43 | 1.549 | 1.083 | 8e+02 | 8e+02 | 1 | 0 | 0 | - | 7e+02 | 7e+02 | 1 | 7e+02 | 7e+02 | 1 | 5e+03 | 0 | 0 |
| 3 | 6e+01 | 6e+01 | 1 | 18.28 | 18.28 | 1 | 13.65 | 3.351 | 0.2455 | 0.4561 | 0 | 0 | 2e+03 | 2e+02 | 0.1267 | 8e+02 | 2e+02 | 0.2455 | 1.938 | 1 | 0.5159 | 16.38 | 13.18 | 0.8046 | 0.9871 | 0.7749 | 0.785 | 1e+02 | 1e+02 | 1 | 1 | 1 | 1 | 4e+01 | 4e+01 | 1 | 4e+01 | 4e+01 | 1 | 1e+03 | 0 | 0 |
| 4 | 8e+01 | 8e+01 | 1 | 25.79 | 25.79 | 1 | 23.67 | 7.213 | 0.3048 | 0.8 | 0 | 0 | 5e+03 | 5e+02 | 0.1091 | 2e+03 | 5e+02 | 0.3048 | 2.795 | 1 | 0.3578 | 28.62 | 22.59 | 0.7893 | 1.161 | 0.8447 | 0.7275 | 2e+02 | 2e+02 | 1 | 1e+01 | 1e+01 | 1 | 2e+02 | 2e+02 | 1 | 2e+02 | 2e+02 | 1 | 4e+03 | 0 | 0 |
| 5+ | 1e+02 | 1e+02 | 1 | 33.51 | 33.51 | 1 | 31.82 | 10.71 | 0.3367 | 0.845 | 0 | 0 | 1e+04 | 1e+03 | 0.1201 | 4e+03 | 1e+03 | 0.3367 | 2.803 | 1 | 0.3567 | 47.95 | 40.49 | 0.8444 | 1.447 | 0.9978 | 0.6895 | 5e+02 | 5e+02 | 1 | 6e+01 | 6e+01 | 1 | 4e+02 | 4e+02 | 1 | 4e+02 | 4e+02 | 1 | 1e+04 | 0 | 0 |


## 4. 構造的比較

### 4.1 Short: Q0 ↔ q_spent 相関

| label | bucket | n | pearson_r |
| --- | --- | --- | --- |
| base | 2 | 1966 | 0.08853 |
| base | 3 | 215 | -0.01528 |
| base | 4 | 260 | 0.09075 |
| base | 5+ | 538 | 0.1258 |
| base | all | 2979 | 0.7499 |
| abl | 2 | 1966 | 0.101 |
| abl | 3 | 215 | 0.1081 |
| abl | 4 | 260 | 0.1301 |
| abl | 5+ | 538 | 0.04851 |
| abl | all | 2979 | 0.3048 |


### 4.2 Long: Q0 ↔ q_spent 相関

| label | bucket | n | pearson_r |
| --- | --- | --- | --- |
| base | 2 | 851 | 0.06986 |
| base | 3 | 57 | -0.04887 |
| base | 4 | 75 | 0.2638 |
| base | 5+ | 129 | 0.238 |
| base | all | 1112 | 0.918 |
| abl | 2 | 851 | 0.1257 |
| abl | 3 | 57 | 0.1407 |
| abl | 4 | 75 | 0.1764 |
| abl | 5+ | 129 | 0.2367 |
| abl | all | 1112 | 0.7113 |


### 4.3 Long: Exhaustion timing shift

| bucket | n_exh_base | n_exh_abl | median_step_base | median_step_abl | mean_step_base | mean_step_abl |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 188 | 0 | 1.845e+04 | - | 1.744e+04 | - |
| 3 | 26 | 0 | 1.394e+04 | - | 1.386e+04 | - |
| 4 | 60 | 0 | 1.243e+04 | - | 1.326e+04 | - |
| 5+ | 109 | 0 | 1.16e+04 | - | 1.363e+04 | - |


## 5. E1+E2 単独の特性 (ablation 側)

### 5.1 Short

| bucket | event_type | event_count | spend_count | spend_rate | delta_mean | attn_mean | fam_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | E1_death | 1643 | 1643 | 1 | 0.2046 | 7.621 | 1.186 |
| 2 | E1_birth | 0 | 0 | - | - | - | - |
| 2 | E2_rise | 1394 | 1394 | 1 | 0.2262 | 10.12 | 1.928 |
| 2 | E2_fall | 1394 | 1394 | 1 | 0.1401 | 9.079 | 1.74 |
| 3 | E1_death | 284 | 284 | 1 | 0.2162 | 14.46 | 0.5845 |
| 3 | E1_birth | 4 | 4 | 1 | 0.364 | 12.75 | 0.25 |
| 3 | E2_rise | 150 | 150 | 1 | 0.1075 | 15.88 | 1.047 |
| 3 | E2_fall | 150 | 150 | 1 | 0.06898 | 16.15 | 0.9867 |
| 4 | E1_death | 432 | 432 | 1 | 0.1894 | 24.92 | 0.7037 |
| 4 | E1_birth | 7 | 7 | 1 | 0.3427 | 30.29 | 0.8571 |
| 4 | E2_rise | 294 | 294 | 1 | 0.06795 | 22.71 | 0.7585 |
| 4 | E2_fall | 294 | 294 | 1 | 0.05058 | 21.39 | 0.6395 |
| 5+ | E1_death | 972 | 972 | 1 | 0.1893 | 44.36 | 0.7469 |
| 5+ | E1_birth | 83 | 83 | 1 | 0.388 | 49.16 | 0.9036 |
| 5+ | E2_rise | 822 | 822 | 1 | 0.07119 | 43.94 | 0.7871 |
| 5+ | E2_fall | 822 | 822 | 1 | 0.03843 | 36.5 | 0.6582 |


### 5.2 Long

| bucket | event_type | event_count | spend_count | spend_rate | delta_mean | attn_mean | fam_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | E1_death | 824 | 824 | 1 | 0.2041 | 7.708 | 1.189 |
| 2 | E1_birth | 0 | 0 | - | - | - | - |
| 2 | E2_rise | 690 | 690 | 1 | 0.2187 | 9.68 | 1.843 |
| 2 | E2_fall | 690 | 690 | 1 | 0.1406 | 9.116 | 1.683 |
| 3 | E1_death | 106 | 106 | 1 | 0.2289 | 13.37 | 0.6415 |
| 3 | E1_birth | 1 | 1 | 1 | 0.3335 | 7 | 0 |
| 3 | E2_rise | 42 | 42 | 1 | 0.08866 | 15.02 | 1.167 |
| 3 | E2_fall | 42 | 42 | 1 | 0.05284 | 11 | 0.7381 |
| 4 | E1_death | 229 | 229 | 1 | 0.1737 | 24.48 | 0.8603 |
| 4 | E1_birth | 10 | 10 | 1 | 0.2904 | 18.5 | 0.4 |
| 4 | E2_rise | 151 | 151 | 1 | 0.07457 | 21.13 | 0.7616 |
| 4 | E2_fall | 151 | 151 | 1 | 0.04591 | 21.45 | 0.9338 |
| 5+ | E1_death | 500 | 500 | 1 | 0.1931 | 39.85 | 1 |
| 5+ | E1_birth | 56 | 56 | 1 | 0.3206 | 41.96 | 0.9464 |
| 5+ | E2_rise | 413 | 413 | 1 | 0.07371 | 44.34 | 1.087 |
| 5+ | E2_fall | 413 | 413 | 1 | 0.03455 | 37.21 | 0.9128 |


## 6. 観察事項 (Describe, do not decide)

1. short bucket=2: event_count 1e+04 → 4e+03 (ratio 0.407), spend_count 1e+04 → 4e+03, exhaustion_ratio 0.02645 → 0, q_spent_mean 5.498 → 2.254。
2. short bucket=3: event_count 2e+03 → 6e+02 (ratio 0.3279), spend_count 2e+03 → 6e+02, exhaustion_ratio 0.02791 → 0, q_spent_mean 8.251 → 2.735。
3. short bucket=4: event_count 4e+03 → 1e+03 (ratio 0.2834), spend_count 4e+03 → 1e+03, exhaustion_ratio 0.03462 → 0, q_spent_mean 13.84 → 3.95。
4. short bucket=5+: event_count 1e+04 → 3e+03 (ratio 0.2814), spend_count 1e+04 → 3e+03, exhaustion_ratio 0.0316 → 0, q_spent_mean 17.75 → 5.017。
5. long bucket=2: event_count 7e+03 → 2e+03 (ratio 0.294), spend_count 7e+03 → 2e+03, exhaustion_ratio 0.2209 → 0, q_spent_mean 7.706 → 2.59。
6. long bucket=3: event_count 2e+03 → 2e+02 (ratio 0.1267), spend_count 8e+02 → 2e+02, exhaustion_ratio 0.4561 → 0, q_spent_mean 13.65 → 3.351。
7. long bucket=4: event_count 5e+03 → 5e+02 (ratio 0.1091), spend_count 2e+03 → 5e+02, exhaustion_ratio 0.8 → 0, q_spent_mean 23.67 → 7.213。
8. long bucket=5+: event_count 1e+04 → 1e+03 (ratio 0.1201), spend_count 4e+03 → 1e+03, exhaustion_ratio 0.845 → 0, q_spent_mean 31.82 → 10.71。

---

*End of §6.4 report.*