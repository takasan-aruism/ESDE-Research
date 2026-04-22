# v9.17 Stage 4 — Other-Readout + Interaction Log Result

*Phase output, Describe only.*

---

## 1. 実装サマリ

### 1.1 実行条件

| 項目 | 値 |
|---|---|
| 実行日 | 2026-04-22 〜 2026-04-23 |
| 本番コマンド | `seq 0 23 \| parallel -j24 "python3 v917_memory_readout.py --seed {} --maturation-windows 20 --tracking-windows 50 --window-steps 500 --tag main"` |
| wall time (v9.17 main) | 184m53.566s (3h4m54s) |
| wall time (v9.16 main 参考) | 187m4.5s (3h7m4s) |
| 差 | −2m10s (−1.2%) |
| 環境変数 | `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0` |
| parallel | GNU parallel 20231122, `-j24` |

### 1.2 段階 3 からの変更点 (§0.3 再掲)

- **下層 (他者読み)**: `CidSelfBuffer` に `read_other_on_e3_contact` 追加、`other_records` リスト + 3 統計カウンタ
- **上層 (接触体記録)**: 新規クラス `InteractionLog` を外部器として配置
- **アダプタ**: `CidView` (frozen dataclass) + `build_cid_view()` で cid-as-int ↔ spec が想定する cid-as-object のギャップを吸収 (相談役 Q1 合意事項, 2026-04-22)
- **event_id**: seed 内 0-based index (`v914_ledger.events` の absolute index、Q2 合意)
- **InteractionLog dedup**: main loop の canonical ordering `observer_cid < contacted_cid` で pair ごと 1 行 (Q3 合意)
- **partner cid 抽出**: `v917_parse_contacted_cid(link_id)` を main loop 側に配置 (Q4 合意)
- **M_c features**: 10 項目固定 (B_Gen, Q0, n_core, S_avg_birth, r_core_birth, phase_sig_birth, theta_birth_mean/std/range, birth_step) — theta_birth 配列本体は含めず統計量 3 つ (Q5 合意)
- **新規 CSV**: `other_records_seed{N}.csv` (10 列) + `interaction_log_seed{N}.csv` (12 列)
- **per_subject.csv**: v917_* 接頭辞 5 列追加 (既存列は不変)

### 1.3 bit-identity 結果

| 対象 | ファイル数 | MD5 一致 |
|---|---|---|
| v9.14 baseline 6 CSV × 24 seed | 144 | **144 / 144 一致** |
| 内訳 | aggregates/per_window, pulse/pulse_log, labels/per_label, audit/per_event_audit, audit/per_subject_audit, audit/run_level_audit_summary | 全て v9.16 main と bit-identical |

物理層 / Layer A / Layer B / v9.14 baseline CSV への影響はゼロ。

### 1.4 Fetch 総数 (v9.16 段階 3 との比較)

| 指標 | v9.17 | v9.16 | 差 |
|---|---|---|---|
| E3_contact events 合計 (24 seed) | 100,432 | 100,432 | 0 |
| v915_fetch_count 合計 (自己読み) | 120,782 | 120,782 | 0 |
| divergence_norm_max 最大絶対差 (cid 単位 5,224 件) | — | — | **0.0** |

物理計算・自己読み計算は完全に不変。

---

## 2. 下層: 他者読みの観察 (24 seeds 合算)

### 2.1 visible_ratio 分布

全 100,432 event の visible_ratio (= 相手の age_factor = Q_remaining / Q0):

| 統計 | 値 |
|---|---|
| min | 0.0 |
| q25 | 0.0 |
| median | 0.364 |
| mean | **0.360** |
| q75 | 0.583 |
| max | 1.0 |
| std | 0.299 |

**smoke (tracking 10 window) の visible_ratio 平均 0.74 と比較**: main (tracking 50 window) では 0.36 に低下。tracking 長が伸びるほど Q_remaining が消耗した状態で E3 event が発火する割合が増加する。

### 2.2 n_core 別 visible_ratio

| n_core | event 数 | median | mean | std |
|---|---|---|---|---|
| 2 | 25,021 | 0.455 | 0.439 | 0.326 |
| 3 | 5,732 | 0.364 | 0.357 | 0.297 |
| 4 | 17,585 | 0.333 | 0.334 | 0.284 |
| 5 | 51,764 | 0.333 | 0.332 | 0.282 |
| 6 | 41 | 0.273 | 0.299 | 0.295 |
| 7 | 147 | 0.333 | 0.335 | 0.276 |
| 8 | 142 | 0.250 | 0.274 | 0.277 |

n_core=2 の観察対象が他の n_core より高い visible_ratio で読まれている (mean 0.44 vs 他 0.27–0.36)。

### 2.3 features 取得量の分布

event 単位の fetched features 数 (0–10):

| 統計 | 値 |
|---|---|
| min | 0 |
| q25 | 0 |
| median | 4 |
| mean | 3.608 |
| q75 | 6 |
| max | 10 |

event 単位の missing features 数: median 6, mean 6.392。
合算: fetched = 362,358 + missing = 641,962 = 1,004,320 = 10 × 100,432 (全 event で制約 fetched + missing = 10 が完全に成立)。

### 2.4 visible_ratio 区間別の取得量

| visible_ratio 区間 | event 数 | fetched mean | fetched max |
|---|---|---|---|
| [0.0, 0.1) | 30,839 | 0.111 | 1 |
| [0.1, 0.3) | 13,148 | 2.219 | 3 |
| [0.3, 0.5) | 20,112 | 4.030 | 5 |
| [0.5, 0.7) | 20,039 | 5.677 | 7 |
| [0.7, 0.9) | 11,406 | 8.0* | — |
| [0.9, 1.0] | 4,888 | — | — |

visible_ratio の区間別 fetched features 数は round(10 × visible_ratio) と整合。

### 2.5 cid の接触統計

| 指標 | 値 |
|---|---|
| per_subject 総 cid 数 (24 seed) | 5,224 |
| 接触 1 回以上の cid (total_other_contacts ≥ 1) | **5,124 (98.1%)** |
| 接触 0 回の cid (total_other_contacts = 0) | **100 (1.9%)** |
| cid 生涯 total_other_contacts median / mean / max | 11 / 19.2 / 259 (std 26.3) |
| cid 生涯 unique contacts median / mean / max | 5 / 6.9 / 45 |

### 2.6 n_core 別の cid 接触回数

| n_core | cid 数 | total_other_contacts mean | median | max |
|---|---|---|---|---|
| 2 | 1,728 | 14.5 | 8 | 196 |
| 3 | 466 | 12.3 | 6 | 168 |
| 4 | 897 | 19.6 | 11 | 217 |
| 5 | 2,126 | 24.4 | 15 | 259 |

n_core=5 の cid が他と比べて接触回数が多い。

---

## 3. 上層: 接触体候補の観察

### 3.1 接触体の総数

| 指標 | 値 |
|---|---|
| interaction_log 行数 (24 seed 合計) | **47,453** |
| seed ごとの ilog 行数: min / median / mean / max | 1,426 / 2,050 / 1,977 / 2,779 |
| seed ごとの ilog 行数: std / CV | 346.8 / 17.5% |
| unique composition (frozenset, 24 seed 合計) | **25,383** |
| 複数回出現した composition (= 再接触らしきもの) | **12,376** |

*注: 複数回出現は seed を跨がない (seed 間で cid_id が独立のため事実上異なる pair)。seed 内での再接触頻度の集計値。*

### 3.2 接触体の構成パターン — n_core 組み合わせ

| 構成 (n_core bucket) | 件数 | 割合 |
|---|---|---|
| 2 × 5+ | 21,883 | 46.1% |
| 2 × 4 | 6,999 | 14.7% |
| 5+ × 5+ | 4,767 | 10.1% |
| 2 × 2 | 4,231 | 8.9% |
| 4 × 5+ | 3,789 | 8.0% |
| 3 × 5+ | 2,240 | 4.7% |
| 2 × 3 | 1,902 | 4.0% |
| 3 × 4 | 774 | 1.6% |
| 4 × 4 | 737 | 1.6% |
| 3 × 3 | 131 | 0.3% |

n_core=2 と n_core=5+ の組み合わせが最多。

### 3.3 接触時の age_factor カテゴリ

判定閾値 0.5 (`AGE_HIGH_THRESH = 0.5`) で分類:

| カテゴリ | 件数 | 割合 |
|---|---|---|
| 両者 high (both ≥ 0.5) | 5,290 | 11.1% |
| 片方 low (一方 < 0.5, 他方 ≥ 0.5) | 12,854 | 27.1% |
| 両者 low (both < 0.5) | **29,309** | **61.8%** |

接触体成立時は両側の age_factor が 0.5 未満の状態が過半数。

### 3.4 時系列分布

接触体成立の step 分布 (cumulative_step 単位):

| 統計 | 値 |
|---|---|
| min | 0 |
| q25 | 10,238 |
| median | 16,157 |
| mean | 15,226 |
| q75 | 20,960 |
| max | 24,998 |

window 別の成立数 (抜粋、WINDOW_STEPS=500):

| window | 件数 | window | 件数 |
|---|---|---|---|
| 0 | 280 | 25 | 1,059 |
| 5 | 457 | 30 | 980 |
| 10 | 560 | 35 | 1,153 |
| 15 | 754 | 40 | 1,289 |
| 20 | 825 | 45 | 1,356 |
| 24 | 978 | 49 | **1,598** |

window index が増加するほど接触数も概ね増加 (約 5.7 倍: w0=280 → w49=1,598)。

---

## 4. 下層と上層の整合

### 4.1 件数の整合

| 対応 | 値 | 検証 |
|---|---|---|
| Σ CidSelfBuffer.other_records | 100,432 | = E3_contact events 100,432 ✓ |
| InteractionLog の行数 | 47,453 | ≤ Layer B unique pairs ✓ |
| interaction_log 行 × 2 | 94,906 | E3 events 100,432 の 94.5% (Taka Q3 予測「E3/2」の近似) |

### 4.2 canonical ordering と dedup

- seed 内の composition 重複: **0 件** (全 24 seed で dedup 成立)
- cid_a_id < cid_b_id 違反: **0 件** (全 47,453 行で canonical 不変)
- `composition_str` と `(cid_a_id, cid_b_id)` の整合: **100%**

### 4.3 Layer B 側の pair 発火動態

| pair タイプ | 件数 | E3 events 寄与 |
|---|---|---|
| Unique pairs (24 seed 合計) | 81,642 | — |
| Bi-directional (2 events) | 18,790 (23%) | 37,580 |
| Uni-directional (1 event) | 62,852 (77%) | 62,852 |

- Layer B は `observer_cid` の ledger entry が存在しない方向の event 発行を skip する (`v914_spend_audit_ledger.py:204-206`)
- そのため pair のどちらか一方が Layer B の lazy registration を未通過の場合は片方向のみ発火
- interaction_log は canonical ordering dedup のもとで:
  - bi-directional pair: 1 row 確定 (18,790 rows)
  - uni-directional pair: canonical 方向が event 側なら 1 row (28,663 rows, 約 45.6% の比率)
  - 合計: 18,790 + 28,663 = **47,453 rows** (実測と一致)

### 4.4 smoke と main の片方向発火率

| 条件 | tracking windows | 片方向 pair 率 |
|---|---|---|
| smoke | 10 | 25.6% (30/117) |
| main | 50 | **77.0% (62,852/81,642)** |

tracking を長くすると Layer B ledger への登録タイミングのばらつきが増加し、片方向発火率が 3 倍強に上昇する観察事実。

---

## 5. v9.16 段階 3 との比較 (参考)

### 5.1 E3_contact の頻度

- v9.17 main: **100,432** (24 seed 合計)
- v9.16 main: **100,432**
- 差: **0**

### 5.2 Fetch 総数 (v915_fetch_count 合計)

- v9.17: **120,782**
- v9.16: **120,782**
- 差: **0**

(段階 4 は Q 消費 0 / 自己読みのタイミング・頻度を変更しないため、自己読み数は完全一致)

### 5.3 divergence_norm_max の最大絶対差

- 24 seed 全 5,224 cid 中、v9.17 と v9.16 の per_cid_self に両方存在する件: 5,224
- |v917 - v916| の最大値: **0.0**

物理計算および自己読み結果は v9.16 段階 3 と完全に一致。

---

## 6. Seed 別分散分析

### 6.1 avg_visible_ratio (seed 平均)

- 24 seed の avg_visible_ratio 値: 0.441–0.493 (範囲)
- 平均: 0.466、std: 0.023
- **CV (std/mean): 4.96%** (非常に低い seed 間分散)

### 6.2 total_other_contacts (seed 内合計)

- 24 seed の total_other_contacts 合計値: 3,063–5,501 (範囲)
- 平均: 4,185、std: 645
- **CV: 15.41%** (moderate な seed 間分散 — pair 発生数自体が seed 依存のため自然)

---

## 7. 承認条件チェック (§8 の 14 項目)

| # | 項目 | 結果 | 備考 |
|---|---|---|---|
| 1 | v9.14 baseline 6 CSV × 24 seed bit-identity | PASS | 144 / 144 MD5 一致 |
| 2 | per_subject v9.14 baseline 96 列 bit-identical | PASS | 全 24 seed |
| 3 | per_subject v915_* 20 列一致 | PASS | 全 24 seed |
| 4 | per_subject v917_* 5 列追加 | PASS | 5 列存在 |
| 5 | other_records 基本範囲 | PASS | 100,432 rows, visible_ratio [0.0, 1.0] |
| 6 | interaction_log 整合 (改訂基準: dedup / 上限 / 下限) | PASS | 47,453 rows, composition 重複 0 |
| 7 | visible_ratio ∈ [0, 1] | PASS | 100,432 / 100,432 |
| 8 | n_features_fetched = len(fetched_M_c_keys) | PASS | 全 row |
| 9 | fetched + missing = 10 | PASS | 全 row disjoint |
| 10 | 決定論性 2 run MD5 (smoke 段階で検証) | PASS | 22 CSV 全て bit-identical (smoke run1 vs smoke_run2) |
| 11 | wall time +20% 以内 (smoke) | PASS | ratio 0.974 |
| 12 | エラー・例外ゼロ | PASS | 24 seed 全て exit 0 |
| 13 | 責務分離 CID → InteractionLog 非参照 | PASS | AST |
| 14 | 責務分離 InteractionLog → CID 非 import | PASS | AST |

**14 / 14 項目 PASS**

---

## 8. 観察事項 (Describe, do not decide)

### 8.1 visible_ratio の分布

- main run での visible_ratio 平均 0.360、median 0.364
- smoke run での visible_ratio 平均 0.740 より低い
- tracking windows 数 (10 → 50) を 5 倍に伸ばすと、visible_ratio の平均値が大きく低下する観察

### 8.2 n_core と visible_ratio

- n_core=2 の観察対象が他のサイズより高い visible_ratio で読まれる (mean 0.44 vs 他 0.27–0.36)
- n_core=5 以上は visible_ratio の平均が 0.33 前後に収束
- n_core=8 は mean 0.274 で最も低い (ただし n=142 と少ないサンプル)

### 8.3 cid 接触の偏り

- 5,224 cid のうち 100 cid (1.9%) が生涯 0 回の他者読み (E3_contact pair 非成立)
- 接触回数 max は 259 回、median は 11 回 — cid 間で接触回数に大きな差
- n_core=5 の cid は接触 mean 24.4 回で他サイズより高い

### 8.4 接触体候補 (InteractionLog)

- 全 47,453 行のうち unique composition は 25,383、12,376 compositions が複数回発生
- 構成パターンは 2 × 5+ が最多 (46.1%)、次いで 2 × 4 (14.7%)
- 接触時の age_factor は両者 low が 61.8%、両者 high は 11.1% と少数
- window index が大きいほど接触成立数が多い (w0=280 → w49=1,598、約 5.7 倍)

### 8.5 Layer B の片方向発火

- smoke (tracking 10) での片方向発火率 25.6% に対し、main (tracking 50) では 77.0%
- Layer B の lazy registration が tracking 期間中に進行するため、発火時点で contacted 側が未登録なケースが main 条件で顕著
- interaction_log の行数はこの動態の関数であり、「E3 events / 2」の近似は tracking 長に強く依存する

### 8.6 seed 分散

- avg_visible_ratio の seed 間 CV 4.96% (非常に低い)
- total_other_contacts の seed 間 CV 15.41% (physics 駆動の pair 発生数自体の分散に由来)

### 8.7 物理層への影響

- v9.14 baseline 6 CSV × 24 seed = 144 ファイル全てで v9.16 main と MD5 一致
- v915_fetch_count, E3_contact 数, divergence_norm_max のいずれも v9.16 と完全一致
- Layer A / Layer B / v9.14 baseline は完全に不変

### 8.8 wall time

- v9.17 main は 3h4m54s、v9.16 main 3h7m4s に対して −1.2%
- 段階 4 の他者読み + 接触体記録のオーバーヘッドは実測上では負の値 (他要因で吸収されている)

---

*以上、v9.17 段階 4 本番 run 結果レポート。Code A 作成、Describe only 徹底。*
