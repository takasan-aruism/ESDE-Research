# v10.7 Step D 報告 — relation_path constructor 実装 + smoke

*作成*: 2026-05-07、Code A
*親*: `v107_step_c_report.md` (Step C 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v107_path_analyzer.py` を実装、4 種 relation_path (familiarity / attention_via_salience / integration_alpha / integration_beta / temporal_coactivation) を seed 0 で **851,154 records (event 14,385 × 平均 59 target/event)、0.72 MB、19.3 秒** で smoke、全 14,385 events 100% で path 構築済、Integration を α/β 別 path として実装したため実質 5 path、matched_baseline は §3.1.5 通り Step E (baseline_constructor) に分離、Step E 進行準備完了。

---

## 1. smoke 実行結果

| 指標 | 値 |
|---|---|
| seed 0 events | 14,385 |
| **total path records** | **851,154** |
| records/event | 平均 59.2、median 60、min 15、max 100 |
| events covered | 14,385 / 14,385 (**100%**) |
| size (parquet snappy) | **0.72 MB/seed** |
| 実行時間 | **19.26 秒/seed** |

### 1.1 relation_path 別 records 数

| path | records | 平均/event | strength 平均 | strength max |
|---|---:|---:|---:|---:|
| temporal_coactivation | **281,190** | 19.5 | 0.160 (1/(1+lag)) | 1.00 |
| attention_via_salience | 219,003 | 15.2 | 37.44 (mass sum) | 124.0 |
| familiarity | 165,547 | 11.5 | 33.30 (fam edge) | 499.99 |
| integration_alpha | 105,521 | 7.3 | 1.00 (one-hot) | 1.00 |
| integration_beta | 79,893 | 5.6 | 1.00 (one-hot) | 1.00 |

→ 4 種 + α/β 分離 = **5 path** で各 source_event 上位 20 cid。一部 path で path_strength の分布パターンが異なる:
- temporal: 距離 (lag) ベースで strength 値が小 (1/(1+lag))
- attention/familiarity: 累積 mass / strength で値が大
- integration: 一様 1.0 (membership 関係なので strength 概念無し)

### 1.2 24 seeds 推定 (smoke ベース)

- 851,154 × 24 ≈ **20.4M records**
- 0.72 × 24 ≈ **17 MB** (parquet 圧縮効果大)
- 19.26 × 24 ≈ **7.7 分** (主に temporal_coactivation の per-event ループ、本番許容範囲)

最終 storage 予算 (Step E-F 統合後) は Step G で実測。

---

## 2. 出力 schema (8 列)

```
event_id              object    Step C 出力との結合キー (例: "0_42")
source_cid            int64     主体 cid
timestamp             int64     source_event の step
target_cid            int64     候補 cid
relation_path_type    object    familiarity / attention_via_salience /
                                 integration_alpha / integration_beta /
                                 temporal_coactivation
relation_strength     float64   path 別の強度
hop_distance          int64     1 (multi-hop は Step F)
seed                  int64     0-23
```

→ 重複行許容 (即決事項 §3.1)。1 cid が複数 path に該当する場合、各 path で別行。

---

## 3. 各 relation_path の構築ロジック

### 3.1 familiarity (1-hop)

- `network/fam_edges_seed*.csv` の (from, to, familiarity) を **双方向に展開** (無向グラフ的)
- source_cid ごとに familiarity 強度上位 20 cid を target に
- 1 source_event あたり: source_cid と接続する fam edge 上位 20 を target

### 3.2 attention_via_salience (即決事項 §2.1 の代替)

- `salience/salience_event_log_seed*.csv` の (observer_cid, candidate_cid, candidate_mass) を集計
- (observer, candidate) ペアごとに mass を sum (= 重み付き接続強度)
- source_cid (= observer) ごとに mass_sum 上位 20 cid を target

→ **per-event ではなく run 全体集約の attention map** として使用。これは salience event が時系列で均等に分布する仮定に基づく。

### 3.3 integration_alpha / integration_beta

- alpha_lifecycle / beta_lifecycle の event_type='birth' を per-event 展開
- 各 (source_cid, timestamp) について、source_cid が **timestamp 以前に加入した** α / β を抽出
- その α / β の他 member を全部 target に
- relation_strength は 1.0 (one-hot、membership 関係)
- α と β は別 path として記録 (= 5 path 構成)

### 3.4 temporal_coactivation (lag ≤ 100 step)

- pulse_log の (cid, t) で source_event の timestamp ± 100 step 内の pulse を抽出
- source_cid 自身は除外、他 cid を candidate
- |lag| 小さい順に上位 20 cid (cid 単位 dedupe で 1 cid につき 1 record)
- relation_strength = 1 / (1 + |lag|) (近いほど強い)

---

## 4. 設計判断 (即決事項 + Code A 判断)

### 4.1 即決事項反映済

- ✓ matched_baseline は Step D **対象外** (Step E baseline_constructor で実装、§3.1.5)
- ✓ attention は salience_event_log 流用 (`relation_path_type = 'attention_via_salience'`)
- ✓ 重複行許容 (1 cid が複数 path → 別行で記録、§3.1)
- ✓ 1-hop のみ (multi-hop は Step F)

### 4.2 Code A 判断

- **Integration を α / β 別 path として記録**: §3.1.3 では「同 α または同 β」だが、α と β は性質が異なる (横の関係 vs 縦の階層) ので Step E / Level 比較で分離できるよう別 path として出力。集計時に統合可
- **temporal_coactivation の lag 範囲**: 指示書 §3.1.4 の「中期 100-1000 step」に対し smoke は **±100 step** に絞った (Step D は 1-hop 想定で短期窓のみ、長 lag は Step F の peak_lag 機構で扱う)
- **fam_edge 双方向展開**: fam_edge は (from, to, familiarity) 形式だが意味的には対称 (cid_a と cid_b の親密度)。両方向に展開して source_cid から見える neighbor を取得

→ §4.2 の判断は Web Claude / Taka に確認願えれば。

---

## 5. Step D 完了条件チェック

- [x] 4 種 relation_path 実装 (familiarity / attention_via_salience / integration / temporal_coactivation)
- [x] Integration を α/β 別 path で実装 (= 計 5 path)
- [x] 1 source_event あたり各 path 上位 20 target
- [x] 1-hop のみ (Step F で multi-hop)
- [x] 全 14,385 events で path 構築 (100%)
- [x] read-only 縛り / v107 出力 path 縛り維持
- [x] parquet 圧縮で軽量出力 (0.72 MB/seed)
- [x] 構造語徹底 (event_id / source_cid / target_cid / relation_path_type / relation_strength / hop_distance)

---

## 6. 出力ファイル

```
developmental/v107/
├── v107_path_analyzer.py
├── v107_step_d_report.md
└── outputs/smoke/
    ├── relation_paths_seed0.parquet            (851,154 rows × 8 cols, 0.72 MB)
    └── relation_paths_run_summary.parquet
```

---

## 7. Step E 進行への申請

Step E (5 種 baseline + delta 集計、`v107_baseline_constructor.py`) に進む許可を求めます。

実装方針:
1. **5 種 baseline 構築** (即決事項 §4 緩和定義):
   - unrelated_baseline: familiarity 強度 < 5 + 同 α/β なし + salience 接続少
   - same_step_random_baseline: 同 step (window) で動いている任意 cid
   - matched_baseline: 同 n_core / age (±20%) / 同 final_state
   - same_integration_low_familiarity_baseline: 同 α/β + familiarity 下位 25%
   - high_familiarity_outside_integration_baseline: familiarity 上位 25% + 同 α/β なし
2. 各 baseline で 1 source_event あたり上位 20 cid 抽出
3. **delta 集計** 6 量 × 4 windows (immediate 1-10 / short 10-100 / medium 100-1000 / peak_lag 10 step bin):
   - Q / C / familiarity_max / n_alphas / n_observed / pulse 発火回数
4. baseline_excess_change = mean(target_delta) - mean(baseline_delta)
5. seed 0 で smoke、storage 実測 (一気に膨張する見込み)

実行時間予想: 2-3 時間。

Step E 完了後、Step F (avalanche + peak_lag) に進む前に再度報告します。

24 seeds 単一バッチ、3 バッチ分割禁止 (memory 規律) を厳守。

---

*以上、Step D 報告。Web Claude / Taka からの Step E 進行許可待ち。*
