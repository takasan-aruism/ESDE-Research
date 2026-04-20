# v9.15 Stage 2 — Event-Driven Self-Readout Result

*Phase 2 output, Describe only.*
*作成: 2026-04-20, Code A*

---

## 1. 実装サマリ

### 1.1 段階 2 の変更点 (段階 1 からの差分)

| 項目 | 段階 1 | 段階 2 |
|---|---|---|
| Fetch トリガ | 50 step 固定 pulse | v9.14 Layer B event 発火 (E1/E2/E3) |
| Match 集約 | Match Ratio (連続値) | any_mismatch (3 点セット) + event 別カウント |
| per_subject v915_* 列数 | 6 列 | **13 列** (削除 2 / 追加 9) |
| divergence_log 列数 | 5 列 | 7 列 (`event_type_full` / `event_type_coarse` 追加) |
| `read_own_state` | 50 step 駆動 | 残置 (メインループから呼ばない) |
| `read_on_event` | — | **新規** (event 発火直後に Fetch) |

### 1.2 bit-identity (smoke で確認済み)

`primitive/v914/diag_v914_smoke/` と `primitive/v915s2/diag_v915s2_smoke/` の比較:

| ファイル | MD5 判定 |
|---|---|
| `aggregates/per_window_seed0.csv` | OK |
| `pulse/pulse_log_seed0.csv` | OK |
| `labels/per_label_seed0.csv` | OK |
| `audit/per_event_audit_seed0.csv` | OK |
| `audit/per_subject_audit_seed0.csv` | OK |
| `audit/run_level_audit_summary_seed0.csv` | OK |

per_subject CSV の v9.14 96 列もセル単位で完全一致。決定論性 check (smoke × 2 回) も全 10 CSV MD5 一致確認済み。

### 1.3 本番 run 実行時間

| 項目 | 値 |
|---|---|
| seeds | 0–23 (24 seeds) |
| tracking_windows | 50 |
| maturation_windows | 20 |
| window_steps | 500 |
| parallel | `-j24` |
| wall time | **187m47s** (3h7m47s) |
| 並列 JobRuntime range | 10,662 – 11,267 sec (≈ 2h58m – 3h8m) |
| exit code | **全 24 seeds で 0** |

※ 並列実行中、決定論 smoke run が 15:19–16:39 の間で並走 (48 core 中最大 25 core 使用)。

### 1.4 出力構成

`primitive/v915s2/diag_v915s2_main/`:

| ディレクトリ | ファイル数 | 内訳 |
|---|---|---|
| `aggregates/` | 48 | per_window × 24 + disposition_summary × 24 |
| `subjects/` | 48 | per_subject × 24 + per_subject_audit × 24 |
| `pulse/` | 24 | pulse_log × 24 |
| `labels/` | 24 | per_label × 24 |
| `audit/` | 72 | per_event_audit / per_subject_audit / run_level_audit_summary × 24 |
| `selfread/` | 72 | per_cid_self / divergence_log / class_divergence × 24 |
| `persistence/` | 96 | v9.13 系 × 24 |

---

## 2. Basic Statistics (24 seeds 合算、per_subject 5,224 行)

### 2.1 Fetch 実行数 (全 cid、n_core バケット別)

段階 2 `v915_fetch_count` 分布:

| n_core | cid 数 | mean | median | p25 | p75 | min | max | sum |
|---|---|---|---|---|---|---|---|---|
| 2 | 840 | 12.53 | 10.0 | 8 | 15 | 1 | 60 | 10,526 |
| 3 | 87 | 43.72 | 36 | 15 | 78 | 3 | 111 | 3,804 |
| 4 | 212 | 79.32 | 91.0 | 46 | 109 | 6 | 147 | 16,815 |
| 5+ | 531 | 103.86 | 112 | 84 | 130 | 13 | 179 | 55,148 |
| unformed | 3,554 | 9.70 | 7.0 | 5 | 10 | 0 | 95 | 34,489 |
| **全体** | 5,224 | 23.12 | 9.0 | 6 | 17 | 0 | 179 | **120,782** |

#### 参考: 段階 1 の同じ指標 (`v915_fetch_count`、50 step 駆動)

| n_core | cid 数 | mean | median | p75 | max | sum |
|---|---|---|---|---|---|---|
| 2 | 840 | 27.70 | 10.0 | 30 | 400 | 23,270 |
| 3 | 87 | 161.61 | 70 | 330 | 500 | 14,060 |
| 4 | 212 | 261.13 | 260.0 | 430 | 500 | 55,360 |
| 5+ | 531 | 299.85 | 320 | 490 | 500 | 159,220 |
| unformed | 3,554 | 30.16 | 20.0 | 30 | 380 | 107,200 |
| **全体** | 5,224 | 68.74 | 20.0 | 50 | 500 | **359,110** |

段階 1 との差分比: sum は 120,782 / 359,110 ≈ 0.336 (段階 2 が段階 1 の約 33.6%)。n_core バケットごとの比: 2→0.452、3→0.271、4→0.304、5+→0.346、unformed→0.322。
※解釈は付さない。参考値として記載。

### 2.2 event 種別ごとの Fetch 発火数

全 cid 合算:

| 列 | mean | median | p75 | max | sum |
|---|---|---|---|---|---|
| `v915_fetch_count_e1` | 1.555 | 1 | 1 | 13 | 8,122 |
| `v915_fetch_count_e2` | 2.341 | 2 | 2 | 14 | 12,228 |
| `v915_fetch_count_e3` | 19.225 | 6 | 13 | 159 | 100,432 |

n_core バケット別 mean:

| n_core | e1 | e2 | e3 | 合計 |
|---|---|---|---|---|
| 2  | 0.996 | 1.719 | 9.815 | 12.53 |
| 3  | 2.046 | 1.977 | 39.701 | 43.72 |
| 4  | 3.104 | 3.651 | 72.561 | 79.32 |
| 5+ | 4.444 | 6.294 | 93.119 | 103.86 |

`per_event_audit` の 24 seeds 集計 (Layer B 側):

| event_type | 件数 |
|---|---|
| E1_death | 7,815 |
| E1_birth | 307 |
| E2_rise | 6,114 |
| E2_fall | 6,114 |
| E3_contact | 100,432 |
| 合計 | 120,782 |

Layer B の event 総数と Layer C Fetch 総数は **120,782 で一致**。

### 2.3 不一致の観察

`v915_any_mismatch_ever` の分布:

| 値 | cid 数 | 率 |
|---|---|---|
| True | 5,170 | 99.0% |
| False | 54 | 1.0% |

`v915_mismatch_count_total` 分布: mean 23.121, median 9, p75 17, max 179, sum 120,782。

event 種別ごとの mismatch_count 分布:

| 列 | mean | median | max | sum |
|---|---|---|---|---|
| `v915_mismatch_count_e1` | 1.555 | 1 | 13 | 8,122 |
| `v915_mismatch_count_e2` | 2.341 | 2 | 14 | 12,228 |
| `v915_mismatch_count_e3` | 19.225 | 6 | 159 | 100,432 |

全 event で mismatch_count = fetch_count (同値)。tolerance 1e-6 の離散判定では、生誕時との浮動小数点一致は発生しなかった。

### 2.4 Self-Divergence 最終値

段階 2 `v915_divergence_norm_final`:

| n_core | cid 数 | mean | median | p25 | p75 | max |
|---|---|---|---|---|---|---|
| 2  | 840 | 3.312 | 3.265 | — | — | 8.409 |
| 3  | 87 | 3.875 | 3.850 | — | — | 7.425 |
| 4  | 212 | 4.982 | 4.833 | — | — | 10.103 |
| 5+ | 531 | 5.470 | 5.426 | — | — | 10.783 |
| 全体 (fetch≥1) | 5,170 | 3.660 | 3.580 | 2.287 | 4.926 | 10.783 |

参考: 段階 1 の `v915_divergence_norm_final` 全体: mean 3.653、median 3.534、p75 4.883、max 10.424。

---

## 3. event 駆動 Fetch の特徴

### 3.1 event 種別 × mismatch 率

| event 種別 | fetch_count 合計 | mismatch_count 合計 | mismatch 比 |
|---|---|---|---|
| E1 | 8,122 | 8,122 | 1.0000 |
| E2 | 12,228 | 12,228 | 1.0000 |
| E3 | 100,432 | 100,432 | 1.0000 |

全 event で比 = 1.0。tolerance (node / link 共に 1e-6) の厳しさが支配的要因。

### 3.2 divergence の event 種別依存性 (divergence_log、24 seeds 合算)

`theta_diff_norm` 分布:

| event 種別 | n | mean | median | p25 | p75 | max |
|---|---|---|---|---|---|---|
| E1 | 8,122 | 4.160 | 4.234 | 2.470 | 5.703 | 10.595 |
| E2 | 12,228 | 2.843 | 1.593 | 0.639 | 5.148 | 10.591 |
| E3 | 100,432 | 4.495 | 4.671 | 3.159 | 6.035 | 12.288 |

E2 は median で最小、E3 は median で最大。E2 は p25 が 0.64 程度と小さい event の存在を示す。E3 は p25 が 3.16 で最も大きい。

---

## 4. v9.14 との連携指標

v9.14 Layer B の `v14_shadow_pulse_count` と v9.15 段階 2 の `v915_fetch_count` を cid 単位で対応付け (24 seeds 合算、5,224 cid):

| 関係 | cid 数 | 率 |
|---|---|---|
| `v14_shadow_pulse_count` == `v915_fetch_count` | 3,636 | 69.6% |
| `v14_shadow_pulse_count` < `v915_fetch_count` | 1,588 | 30.4% |
| `v14_shadow_pulse_count` > `v915_fetch_count` | 0 | 0.0% |

Pearson 相関係数: **r = 0.880**

`v14_shadow_pulse_count` は Layer B `_process_event` で `spend_flag = (Q_remaining > 0)` が真の event のみ +1 される定義、`v915_fetch_count` は event 発生時に無条件で +1 される定義 (Layer C は Q を参照しない)。両者の差分は Q 枯渇後の event 数に対応する。

---

## 5. Seed 別分散分析

### 5.1 Fetch (n_core バケット × seed の `v915_fetch_count` 平均)

| n_core | n_seeds | mean across seeds | stdev | CV | min | max |
|---|---|---|---|---|---|---|
| 2 | 24 | 12.39 | 2.06 | 0.166 | 8.87 | 17.14 |
| 3 | 23 | 42.68 | 20.47 | **0.480** | 12.00 | 89.80 |
| 4 | 24 | 78.88 | 19.56 | 0.248 | 43.60 | 113.30 |
| 5+ | 24 | 104.09 | 10.77 | 0.103 | 83.83 | 124.08 |
| unformed | 24 | 9.68 | 1.05 | 0.108 | 8.01 | 11.91 |

n_core=3 の CV (0.480) は他のバケットより大きい。 n_core=3 は 87 cid 全体と、23 seeds に不均等に分布する小サンプル層。

### 5.2 Divergence (n_core バケット × seed の `v915_divergence_norm_final` 平均)

| n_core | n_seeds | mean | stdev | CV | min | max |
|---|---|---|---|---|---|---|
| 2 | 24 | 3.302 | 0.201 | 0.061 | 2.982 | 3.657 |
| 3 | 23 | 3.906 | 0.936 | 0.240 | 1.955 | 5.621 |
| 4 | 24 | 4.980 | 0.360 | 0.072 | 4.195 | 5.601 |
| 5+ | 24 | 5.469 | 0.382 | 0.070 | 4.599 | 6.062 |
| unformed | 24 | 3.396 | 0.166 | 0.049 | 3.142 | 3.793 |

Divergence でも n_core=3 が CV 最大 (0.240)。他バケットは 0.05–0.07 のレンジ。

---

## 6. 観察事項 (Describe, do not decide)

- Layer A と Layer B の出力は v9.14 smoke と MD5 一致。段階 2 の追加コードによる baseline CSV への影響は確認されなかった (0 バイト差)。
- 段階 2 の Fetch 総数 (120,782) は Layer B の event 総数 (120,782) と完全一致。Fetch は Layer B の event 発火に 1:1 で従属する構造として機能している。
- Fetch の event 種別内訳は、E3_contact 83.2%、E2 10.1%、E1 6.7% の比率になった。E3 は `detect_e3_new_pairs` で両 cid 視点 (observer × contacted) それぞれ event が記録される実装のため、contact ペア数の 2 倍が event として発行される。
- E3_contact の fetch_count は n_core=5+ のバケットで mean 93.1、n_core=2 では mean 9.8 と、n_core の大小で約 9.5 倍の差が観察された。
- 全 event で mismatch 比 = 1.0。tolerance 1e-6 の離散判定の下では、生誕時点の theta / S 値から連続的に変化した構造体は、event 発火 step ではすべて不一致判定になる。
- `v915_any_mismatch_ever` が False の cid は 54/5224 (1.0%)。これらは `v915_fetch_count == 0` の cid (=生存期間中に event が 1 回も発火しなかった cid)。
- `v14_shadow_pulse_count` と `v915_fetch_count` は cid の 69.6% で完全一致、残り 30.4% で Layer B の方が小さい (Q 枯渇後 event)。Pearson 相関 r = 0.880。
- divergence_norm_final 分布は段階 1 (median 3.534) と段階 2 (median 3.580) で近い値になった。Fetch タイミングが 50 step 固定から event 駆動に変わったが、最終時点の theta drift 幅は cid の生存期間による変化が支配的であり、Fetch タイミングに対する感度は小さい可能性がある (解釈せず、数値のみ記載)。
- Seed 別 CV は n_core=3 のみ突出して大きい (Fetch 0.480、Divergence 0.240)。n_core=3 の cid 母集団が 87 と少なく、23 seeds に不均等配分であることが数値として反映されている。
- 段階 2 本番 run の wall time は 3h7m47s。並列実行中に smoke run が並走した時間帯 (≈80 分) を含む。

---

*本レポートは `primitive/v915s2/v915s2_stage2_result.md` に保存。
集計スクリプト: `primitive/v915s2/analyze_stage2_main.py`、
出力 CSV: `primitive/v915s2/diag_v915s2_main/` 配下、
smoke 出力: `primitive/v915s2/diag_v915s2_smoke/` 及び `primitive/v915s2/diag_v915s2_smoke_run1/`。*
