# v9.14 §6.2 — n_core Efficiency

*Phase 2 §6.2 output — Describe only.*


## 1. 計算方法

- 入力: `diag_v914_{short,long}/audit/per_subject_audit_seed*.csv` (cid 単位) と `per_event_audit_seed*.csv` (event 単位)。
- n_core バケット = `n_core_member` を 2 / 3 / 4 / 5+ に集約。n_core=6 以上は「5+」に含める。
- 基礎指標: n_cids, q0_mean/std, q_spent_mean/std, exhaustion_ratio (= Q_remaining==0 の cid 割合), event_count_mean (= 1 cid あたり event 数平均), event_per_q0 (= event_count_mean / q0_mean)。
- Efficiency 指標: 各バケットの全 cid を合算した (attention_delta 総和) / (spend 回数合計)、(familiarity_delta 総和) / (spend 回数合計)、(delta_norm 総和) / (spend 回数合計)。spend_flag=True のみ。
- Exhaustion プロファイル (long 専用): 各 cid で Q_remaining が初めて 0 に 到達した event の global_step (= engine の通し step) と window を分布集計。
- Non-exhaustion cid: per_subject の `v14_q_remaining > 0` で抽出、同バケットの exhausted cid と q0/event_count を対照。

## 2. Short run: 基礎指標

| bucket | n_cids | q0_mean | q0_std | q_spent_mean | q_spent_std | exhaustion_ratio | non_exhaustion_ratio | event_count_mean | event_per_q0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1966 | 11.49 | 0.5781 | 5.498 | 2.618 | 0.02645 | 0.9736 | 5.538 | 0.4821 |
| 3 | 215 | 18.33 | 0.5083 | 8.251 | 4.69 | 0.02791 | 0.9721 | 8.34 | 0.455 |
| 4 | 260 | 25.69 | 0.7539 | 13.84 | 6.123 | 0.03462 | 0.9654 | 13.94 | 0.5426 |
| 5+ | 538 | 33.4 | 1.641 | 17.75 | 7.206 | 0.0316 | 0.9684 | 17.83 | 0.5338 |


## 3. Long run: 基礎指標

| bucket | n_cids | q0_mean | q0_std | q_spent_mean | q_spent_std | exhaustion_ratio | non_exhaustion_ratio | event_count_mean | event_per_q0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 851 | 11.55 | 0.5558 | 7.706 | 2.893 | 0.2209 | 0.7791 | 8.808 | 0.7629 |
| 3 | 57 | 18.28 | 0.4868 | 13.65 | 5.447 | 0.4561 | 0.5439 | 26.46 | 1.447 |
| 4 | 75 | 25.79 | 0.6984 | 23.67 | 5.259 | 0.8 | 0.2 | 66.15 | 2.565 |
| 5+ | 129 | 33.51 | 1.02 | 31.82 | 5.198 | 0.845 | 0.155 | 89.2 | 2.662 |


## 4. Efficiency 指標 (spend あたり)

### 4.1 Short run

| bucket | n_cids | spend_count_total | attention_gain_total | familiarity_gain_total | delta_gain_total | attn_per_spend | fam_per_spend | delta_per_spend |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1966 | 10810 | 9.835e+04 | 1.761e+04 | 1504 | 9.098 | 1.629 | 0.1391 |
| 3 | 215 | 1774 | 2.982e+04 | 1945 | 302 | 16.81 | 1.096 | 0.1702 |
| 4 | 260 | 3598 | 1.056e+05 | 4238 | 639.5 | 29.36 | 1.178 | 0.1777 |
| 5+ | 538 | 9550 | 4.83e+05 | 1.376e+04 | 1867 | 50.57 | 1.441 | 0.1955 |


### 4.2 Long run

| bucket | n_cids | spend_count_total | attention_gain_total | familiarity_gain_total | delta_gain_total | attn_per_spend | fam_per_spend | delta_per_spend |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 851 | 6558 | 5.739e+04 | 9378 | 895.5 | 8.751 | 1.43 | 0.1365 |
| 3 | 57 | 778 | 1.274e+04 | 768 | 127.3 | 16.38 | 0.9871 | 0.1636 |
| 4 | 75 | 1775 | 5.08e+04 | 2061 | 277.1 | 28.62 | 1.161 | 0.1561 |
| 5+ | 129 | 4105 | 1.968e+05 | 5941 | 695.7 | 47.95 | 1.447 | 0.1695 |


## 5. Long run: Exhaustion プロファイル

| bucket | n_exhausted | exhaust_step_mean | exhaust_step_median | exhaust_step_min | exhaust_step_max | exhaust_window_mean | exhaust_window_median | exhaust_window_min | exhaust_window_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 188 | 1.744e+04 | 1.845e+04 | 4176 | 24952 | 54.3 | 56 | 28 | 69 |
| 3 | 26 | 1.386e+04 | 1.394e+04 | 5157 | 23142 | 47.19 | 47 | 30 | 66 |
| 4 | 60 | 1.326e+04 | 1.243e+04 | 3903 | 24938 | 45.98 | 44.5 | 27 | 69 |
| 5+ | 109 | 1.363e+04 | 1.16e+04 | 4179 | 24904 | 46.77 | 43 | 28 | 69 |


## 6. Long run: Non-exhaustion cid の特性

| bucket | n_total | n_non_exhausted | non_exhausted_share | non_exh_q0_mean | non_exh_q0_std | non_exh_q_remaining_mean | non_exh_event_count_mean | exh_q0_mean | exh_event_count_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 851 | 663 | 0.7791 | 11.56 | 0.5513 | 4.929 | 6.629 | 11.51 | 16.49 |
| 3 | 57 | 31 | 0.5439 | 18.32 | 0.532 | 8.516 | 9.806 | 18.23 | 46.31 |
| 4 | 75 | 15 | 0.2 | 25.6 | 0.611 | 10.6 | 15 | 25.83 | 78.93 |
| 5+ | 129 | 20 | 0.155 | 33.3 | 0.7141 | 10.9 | 22.4 | 33.55 | 101.5 |


## 7. 観察事項 (Describe, do not decide)

1. Q0_mean は n_core に単調増加: short で 2=11.49, 3=18.33, 4=25.69, 5+=33.4。
2. exhaustion_ratio (Q_remaining=0 の cid 割合) は short で 2=0.02645, 3=0.02791, 4=0.03462, 5+=0.0316、long で 2=0.2209, 3=0.4561, 4=0.8, 5+=0.845。
3. event_count_mean は short で 2=5.538, 3=8.34, 4=13.94, 5+=17.83、long で 2=8.808, 3=26.46, 4=66.15, 5+=89.2。
4. event_per_q0 (平均 event 数 ÷ 平均 Q0) は long で 2=0.7629, 3=1.447, 4=2.565, 5+=2.662。
5. attention_per_spend (総 attention_delta / 総 spend 回数) は long で 2=8.751, 3=16.38, 4=28.62, 5+=47.95。
6. familiarity_per_spend は long で 2=1.43, 3=0.9871, 4=1.161, 5+=1.447。
7. delta_per_spend は long で 2=0.1365, 3=0.1636, 4=0.1561, 5+=0.1695。
8. Exhaustion の到達タイミング (long run, global_step 中央値) は 2=2e+04, 3=1e+04, 4=1e+04, 5+=1e+04。
9. Non-exhaustion cid の割合 (long run) は 2=0.7791, 3=0.5439, 4=0.2, 5+=0.155。
10. Non-exhaustion と exhaustion の event_count_mean 差 (long, 5+ バケット): non_exhausted=22.4、exhausted=101.5。

---

*End of §6.2 report.*