# v9.14 §6.3 — Shadow-vs-Fixed Overlap

*Phase 2 §6.3 output — Describe only.*


## 1. 計算方法

- Layer A: `diag_v914_{short,long}/pulse/pulse_log_seed*.csv` (cid × t)。cold_start (`pulse_n ≤ 3`) は除外。
- Layer B: `diag_v914_{short,long}/audit/per_event_audit_seed*.csv` (cid × global_step × event_type)。
- Step 軸: pulse_log の `t` と per_event の `global_step` が engine の共通 step 時計。
- 厳密マッチ (Jaccard): 各 (seed, cid) で A_steps ∩ B_steps / A_steps ∪ B_steps。全体は micro-average (inter 総和 / union 総和) と macro-mean (cid 平均) の 2 種で記載。
- 近接マッチ (±N): N ∈ {5, 10, 25}。`match_rate_A_by_B_N` = A のうち ±N step 以内に B event が存在する割合。B 基準は対称定義。
- 独立性 (±25): `only_A` = A で捕捉・B で ±25 未捕捉、`only_B` 同様、`both` = ±25 で相手あり (A 基準 count)。
- ベースライン期待値: Layer B event が cid の観測期間で一様分布すると仮定した場合の `match_rate_A_by_B_N` の理論値。cid ごとに p = 1 − (1 − (2N+1)/span)^{n_B} を計算し、n_A weighted 平均。
- 内容比較: exact-match の行について v11_delta と v14_delta_norm の Pearson 相関、`v11_captured` と `v14_spend_flag` の一致率。同 step 内で複数 event が発火した場合、Layer B 側は max(delta) + any(spend_flag) に集約。event_type 層別 (E3 を含むかどうか) も算出。
- n_core バケット (2/3/4/5+) 別の計算は per_subject_audit の `n_core_member` を使用。

## 2. Short run: overlap 集計

| group | n_cids | n_A_total | n_B_total | exact_intersection | exact_union | jaccard_micro | jaccard_macro_mean | match_rate_A_by_B_5 | match_rate_B_by_A_5 | match_rate_A_by_B_10 | match_rate_B_by_A_10 | match_rate_A_by_B_25 | match_rate_B_by_A_25 | only_A_25_count | only_B_25_count | both_25_count_A | both_25_count_B | only_A_25_share_of_A | only_B_25_share_of_B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 2979 | 110383 | 25896 | 266 | 130550 | 0.002038 | 0.001636 | 0.02389 | 0.1173 | 0.04484 | 0.2254 | 0.1056 | 0.5398 | 98730 | 11918 | 11653 | 13978 | 0.8944 | 0.4602 |


ベースライン期待 match_rate_A_by_B: ±5=0.05184, ±10=0.09493, ±25=0.2058

## 3. Long run: overlap 集計

| group | n_cids | n_A_total | n_B_total | exact_intersection | exact_union | jaccard_micro | jaccard_macro_mean | match_rate_A_by_B_5 | match_rate_B_by_A_5 | match_rate_A_by_B_10 | match_rate_B_by_A_10 | match_rate_A_by_B_25 | match_rate_B_by_A_25 | only_A_25_count | only_B_25_count | both_25_count_A | both_25_count_B | only_A_25_share_of_A | only_B_25_share_of_B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 1112 | 72264 | 25472 | 353 | 92321 | 0.003824 | 0.002877 | 0.04752 | 0.1639 | 0.08747 | 0.31 | 0.1989 | 0.7473 | 57888 | 6437 | 14376 | 19035 | 0.8011 | 0.2527 |


ベースライン期待 match_rate_A_by_B: ±5=0.0756, ±10=0.1375, ±25=0.2926

## 4. 内容的比較 (exact-match)

### 4.1 Short run

- 全マッチ: n=266, Pearson(v11_delta, v14_delta_norm) = 0.1079, agreement(captured, spend_flag) = 0.3158
- E3 非含 (E1/E2 のみ): n=16, Pearson = 0.2999, agreement = 0.375
- E3 含む: n=250, Pearson = 0.09111, agreement = 0.312

### 4.2 Long run

- 全マッチ: n=353, Pearson(v11_delta, v14_delta_norm) = 0.08939, agreement(captured, spend_flag) = 0.5694
- E3 非含 (E1/E2 のみ): n=9, Pearson = 0.1057, agreement = 0.4444
- E3 含む: n=344, Pearson = 0.09075, agreement = 0.5727

## 5. n_core バケット別 overlap

### 5.1 Short run

| group | n_cids | n_A_total | n_B_total | exact_intersection | exact_union | jaccard_micro | jaccard_macro_mean | match_rate_A_by_B_5 | match_rate_B_by_A_5 | match_rate_A_by_B_10 | match_rate_B_by_A_10 | match_rate_A_by_B_25 | match_rate_B_by_A_25 | only_A_25_count | only_B_25_count | both_25_count_A | both_25_count_B | only_A_25_share_of_A | only_B_25_share_of_B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1966 | 39832 | 10887 | 55 | 48313 | 0.001138 | 0.001204 | 0.01514 | 0.06228 | 0.02897 | 0.1224 | 0.06866 | 0.2918 | 37097 | 7710 | 2735 | 3177 | 0.9313 | 0.7082 |
| 3 | 215 | 10315 | 1793 | 13 | 11753 | 0.001106 | 0.001099 | 0.02104 | 0.1478 | 0.03994 | 0.2839 | 0.09355 | 0.6916 | 9350 | 553 | 965 | 1240 | 0.9064 | 0.3084 |
| 4 | 260 | 17800 | 3624 | 52 | 20638 | 0.00252 | 0.002167 | 0.02775 | 0.1592 | 0.05197 | 0.303 | 0.121 | 0.7271 | 15647 | 989 | 2153 | 2635 | 0.879 | 0.2729 |
| 5+ | 538 | 42436 | 9592 | 146 | 49846 | 0.002929 | 0.003174 | 0.03118 | 0.1582 | 0.05795 | 0.3019 | 0.1367 | 0.7221 | 36636 | 2666 | 5800 | 6926 | 0.8633 | 0.2779 |


### 5.2 Long run

| group | n_cids | n_A_total | n_B_total | exact_intersection | exact_union | jaccard_micro | jaccard_macro_mean | match_rate_A_by_B_5 | match_rate_B_by_A_5 | match_rate_A_by_B_10 | match_rate_B_by_A_10 | match_rate_A_by_B_25 | match_rate_B_by_A_25 | only_A_25_count | only_B_25_count | both_25_count_A | both_25_count_B | only_A_25_share_of_A | only_B_25_share_of_B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 851 | 18177 | 7496 | 61 | 23902 | 0.002552 | 0.00225 | 0.03136 | 0.09232 | 0.05887 | 0.1744 | 0.14 | 0.4368 | 15632 | 4222 | 2545 | 3274 | 0.86 | 0.5632 |
| 3 | 57 | 5899 | 1508 | 27 | 7100 | 0.003803 | 0.004362 | 0.03967 | 0.1943 | 0.07272 | 0.3647 | 0.1651 | 0.8488 | 4925 | 228 | 974 | 1280 | 0.8349 | 0.1512 |
| 4 | 75 | 15475 | 4961 | 83 | 19448 | 0.004268 | 0.005086 | 0.04943 | 0.1889 | 0.09279 | 0.3657 | 0.2129 | 0.8909 | 12181 | 541 | 3294 | 4420 | 0.7871 | 0.1091 |
| 5+ | 129 | 32713 | 11507 | 182 | 41871 | 0.004347 | 0.005071 | 0.05701 | 0.1959 | 0.1035 | 0.3673 | 0.2312 | 0.8743 | 25150 | 1446 | 7563 | 10061 | 0.7688 | 0.1257 |


## 6. 観察事項 (Describe, do not decide)

1. Short run: Layer A pulse 数 (cold_start 除外) = 110383、Layer B event 数 = 25896、exact Jaccard (micro) = 0.002038。
2. Long run: Layer A pulse 数 = 72264、Layer B event 数 = 25472、exact Jaccard (micro) = 0.003824。
3. ±25 step 近接マッチ率 (A 基準, long): 0.1989 (ベースライン均一分布期待 0.2926)。
4. ±25 step 近接マッチ率 (B 基準, long): 0.7473。
5. Short run の n_core バケット別 ±25 match_rate_A_by_B: 2=0.06866, 3=0.09355, 4=0.121, 5+=0.1367。
6. Long run の n_core バケット別 ±25 match_rate_A_by_B: 2=0.14, 3=0.1651, 4=0.2129, 5+=0.2312。
7. Long run の only_A_25_share_of_A (±25 で B に未マッチな A の割合) = 0.8011、only_B_25_share_of_B = 0.2527。
8. Long run exact-match での内容相関 (v11_delta vs v14_delta_norm): n=353, Pearson r = 0.08939。
9. Long run exact-match での v11_captured と v14_spend_flag の一致率 = 0.5694 (n=353)。
10. Long run, E3 を含まない (E1/E2 のみの) exact-match: n=9, Pearson r = 0.1057, 一致率 = 0.4444。
11. Long run, E3 を含む exact-match: n=344, Pearson r = 0.09075, 一致率 = 0.5727。

---

*End of §6.3 report.*