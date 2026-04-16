# v9.12 Phase 1 — L06 個別時系列分析 結果レポート

- 実行日: 2026-04-16
- スクリプト: `v912_l06_timeseries.py`
- データソース: `v911/diag_v911_capture_long/` (5 seeds x 50 tracking windows)

---

## 1. 概要

L06 (n_pulses_eval >= 167, long 上位 10%) に該当する cid の pulse 時系列を集計し、
M_c-vs-E_t 乖離 (delta) の挙動を分析した。

| 項目 | 値 |
|---|---|
| seeds | 0, 1, 2, 3, 4 |
| L06 該当 cid 数 | 114 |
| 総 eval pulse 数 | 43,958 |
| L06 閾値 | n_pulses_eval >= 167 |
| bin 幅 | 5 pulse |

---

## 2. Spike / Low 分析

| 指標 | 値 |
|---|---|
| delta p90 閾値 | 0.5834 |
| delta p10 閾値 | 0.2553 |
| spike (p90 超) pulse 数 | 4,396 |
| spike 時 capture_rate | 0.1538 (15.4%) |
| low (p10 未満) pulse 数 | 4,396 |
| low 時 capture_rate | 0.5093 (50.9%) |

**所見**: delta が大きい (M_c と E_t の乖離大) spike 時は capture_rate が 15.4% に低下し、
delta が小さい low 時は 50.9% に上昇する。乖離が小さいほど capture されやすいという
直感的な関係が確認された。

---

## 3. 自己相関 (Autocorrelation)

| lag | mean | p50 |
|---|---|---|
| 1 | 0.0150 | 0.0080 |
| 2 | 0.0100 | 0.0067 |
| 3 | 0.0121 | 0.0088 |
| 5 | 0.0045 | -0.0045 |
| 10 | 0.0104 | 0.0088 |

**所見**: 全 lag で mean/p50 ともにほぼ 0 に近い。delta 系列に有意な自己相関はなく、
pulse 間の乖離変動はほぼ独立 (i.i.d. 的) である。
lag=1 の mean=0.015 がわずかに正だが、実質的に無視できる水準。

---

## 4. First Diverge Axis (最初に乖離が p90 を超えた軸)

| 軸 | cid 数 | 割合 |
|---|---|---|
| phase | 49 | 43.0% |
| n | 35 | 30.7% |
| r | 20 | 17.5% |
| s | 10 | 8.8% |

各軸の p90 閾値:

| 軸 | p90 閾値 |
|---|---|
| n | 0.8140 |
| s | 0.4030 |
| r | 0.7858 |
| phase | 0.8961 |

**所見**: phase 軸が最初に乖離する cid が最多 (43%)。次いで n 軸 (31%)。
s 軸は閾値自体が低い (0.403) にもかかわらず最初に発散するケースが最少 (8.8%)
であり、s 軸は M_c と E_t の整合性が最も安定していることを示す。

---

## 5. n_core 別統計

| n_core | cid 数 | pulse 数 | delta mean | delta p50 | capture_rate | ac_lag1 |
|---|---|---|---|---|---|---|
| 2 | 3 | 771 | 0.2518 | 0.2534 | 0.4643 | -0.0242 |
| 3 | 7 | 2,919 | 0.3550 | 0.3563 | 0.3683 | 0.0172 |
| 4 | 34 | 12,188 | 0.4097 | 0.4099 | 0.3076 | 0.0133 |
| 5 | 70 | 28,080 | 0.4325 | 0.4275 | 0.2923 | 0.0173 |

**所見**:
- n_core が増加するほど delta (乖離) が増大: n_core=2 で 0.252 → n_core=5 で 0.433
- capture_rate は n_core 増加に伴い低下: n_core=2 で 46.4% → n_core=5 で 29.2%
- core 数が多い cid ほど M_c の複雑性が高く、E_t との乖離が大きくなる傾向
- L06 の大半 (70/114 = 61.4%) は n_core=5

---

## 6. bin 時系列トレンド (aggregate_bin)

100 bin (pulse_n 4~504, bin 幅 5) の集計結果から主要指標の推移を確認した。

| 指標 | 序盤 (bin 0-9) | 中盤 (bin 45-54) | 終盤 (bin 90-99) |
|---|---|---|---|
| delta_mean | 0.427 | 0.418 | 0.405 |
| capture_rate | 0.300 | 0.302 | 0.293 |
| d_n_mean | 0.428 | 0.412 | 0.368 |
| d_phase_mean | 0.522 | 0.508 | 0.481 |
| n_cids | 114 | 114 | 41 |

**所見**:
- delta_mean はほぼ横ばい (0.40~0.43) でトレンド性が弱い
- d_n_mean と d_phase_mean はわずかに後半で低下傾向
- 終盤では脱落 cid が増え n_cids が減少 (114 → 41)、生存バイアスに注意
- capture_rate も全体的に 0.27~0.34 の範囲で安定

---

## 7. 出力ファイル一覧

| ファイル | 内容 |
|---|---|
| `diag_l06_timeseries/aggregate_bin.csv` | 全 cid 集約の bin 時系列 (100 bins) |
| `diag_l06_timeseries/autocorrelation.csv` | cid 別 autocorrelation (114 行) |
| `diag_l06_timeseries/ncore_stats.csv` | n_core 別集計 |
| `diag_l06_timeseries/per_cid/*.csv` | cid 別 pulse 時系列 (114 ファイル) |
| `diag_l06_timeseries/summary.json` | 全指標の JSON (本レポートの元データ) |

---

## 8. まとめ

1. **乖離と capture の逆相関**: delta が大きいほど capture されにくい関係が明確 (spike 15.4% vs low 50.9%)
2. **時系列独立性**: delta 系列に自己相関はほぼなく、各 pulse の乖離は前の pulse に依存しない
3. **phase 軸優位の発散**: 最初に乖離が発散する軸は phase が最多 (43%)、次いで n (31%)
4. **n_core 効果**: core 数が多いほど delta が大きく capture_rate が低い — 複雑な M_c ほど E_t との整合が困難
5. **時系列安定**: bin 集計でトレンド性は弱く、delta/capture_rate ともに pulse 進行によらず概ね安定
