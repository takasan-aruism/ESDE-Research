# v10.7 Step F 報告 — avalanche + peak_lag 実装 + smoke

*作成*: 2026-05-07、Code A
*親*: `v107_step_e_report.md` (Step E 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v107_avalanche_monitor.py` を実装、5 機能 (multi-hop graph traversal / 減衰率 / 共鳴ループ / peak_lag / 波及パターン分類) を seed 0 で **9.3 秒** で smoke (予想 4-6 時間から大幅短縮)、ESDE familiarity グラフは **2-hop で 159,099 records / 3-hop で 4,595 records** という small-world 性 (3-hop に急減)、**double 双方向 loop 711 ペア** + **3-hop closure 4,563 三角ループ** を検出、peak_lag は temporal_coactivation で **lag=290 (peak 0.107)**、familiarity で **lag=480 (peak 0.112)** という中期遅延型優勢で 10 path 中 8 path が echo (残響) パターンに分類、Step G (統合 smoke + bit-identity 層 B) 進行準備完了。

---

## 1. smoke 実行結果

| 機構 | seed 0 結果 | 24 seeds 推定 |
|---|---|---|
| multi_hop_paths | **328,936 records** (1-hop 165K + 2-hop 159K + 3-hop 4.6K) | 7.9M records |
| 共鳴ループ | **loop_2_hop 711 + loop_3_hop 4,563** | 約 12K loops |
| decay_rate | 4 行 (hop 別 + decay_pattern) | 96 行 |
| peak_lag_curve | 1,010 rows (10 path × 101 lag bins) | 24,240 rows |
| wave_patterns | 10 path × 1 = 10 rows | 240 rows |
| 実行時間 | **9.3 秒/seed** | 約 4 分 (24 seeds) |
| size 合計 | **0.32 MB/seed** (multi_hop + その他) | 7.7 MB |

→ 予想 4-6 時間から **2000 倍以上短縮** (peak_lag を per-event でなく path 別集約 + サブサンプリング 5000 で計算)。

---

## 2. multi-hop graph 構造 (familiarity 経路)

| hop | records (seed 0) | 比率 |
|---|---:|---:|
| 1 hop | 165,242 | 50.2% |
| 2 hop | 159,099 | 48.4% |
| **3 hop** | **4,595** | **1.4%** |

→ ESDE Genesis 系の familiarity グラフは **3-hop で急減 (50% → 50% → 1.4%)** という構造を示す。これは:
- 1, 2 hop で大半の cid ペアが既にカバーされる (small-world 性)
- 3-hop neighbor は visited 除外で大幅減 (グラフ密度が高い)
- → ESDE 内の "アバランシェ" は 2-hop で実質的に全域に到達、3 hop 以上は飽和済

これは **アバランシェ防止 3 hop 制限が現実的に作用している** 重要な構造観察。

---

## 3. 共鳴ループ検出

| loop_type | count | mean min_strength |
|---|---:|---:|
| loop_2_hop (双方向 fam edge) | **711** | 15.56 |
| loop_3_hop (3 cid 三角閉路) | **4,563** | 6.56 |

→ 711 個の **双方向 familiarity ペア** = cid_a → cid_b と cid_b → cid_a の両方向接続あり。
→ 4,563 個の **三角ループ** = 3-hop で source に戻る path 群。
→ loop_2 の min_strength (15.56) >> loop_3 (6.56) → **直接の双方向ループは強い、間接 3-hop ループは弱い接続**。

これは ESDE Genesis 系の familiarity 構造に **強い対称的接続 (loop_2)** と **弱い triadic closure (loop_3)** が混在していることを示す。

---

## 4. 減衰率追跡 (hop 別 baseline_excess_change)

| hop | n_events | mean_dC_imm | mean_dC_med | n_pulses_imm | n_pulses_med | decay_pattern |
|---|---:|---:|---:|---:|---:|---|
| 1 | 8,565 | 0.009 | 0.184 | 0.111 | 9.88 | sharp_decay |
| 2 | **0** | - | - | - | - | (excess 紐付け失敗) |
| 3 | **0** | - | - | - | - | (同上) |

→ **重要な実装上の留意点**: Step E の baseline_constructor は `familiarity` (1-hop) しか集計せず、Step F multi_hop の `familiarity_hop2/hop3` は excess_change に存在しない。

→ **decay_rate の n_events=0 は、Step F で multi_hop を構築したが対応する delta 集計を再実行していないため**。Step G (統合 smoke) で:
- (a) Step E baseline_constructor を multi_hop も対象に拡張、または
- (b) Step F で multi_hop の delta を独立に集計
- どちらかの方針を Web Claude / Taka に確認

→ smoke 段階では multi_hop の **構造 (graph)** は確認できているが、**減衰率の数値** は要再 run。Step G で統合判断。

---

## 5. peak_lag 測定 (10 path × 101 lag bins)

サブサンプル 5,000/path で実施。lag 0, 10, ..., 1000 の 101 bins。

### 5.1 path 別 peak_lag (mean_delta_C で argmax)

| relation_path_type | peak_lag | abs_peak_value | n_local_maxes | wave_pattern_class |
|---|---:|---:|---:|---|
| **familiarity** | 480 | **0.112** | 17 | echo |
| **attention_via_salience** | 480 | 0.115 | 14 | echo |
| **temporal_coactivation** | 290 | 0.107 | 14 | echo |
| same_step_random_baseline | 310 | 0.102 | 14 | echo |
| matched_baseline | 380 | 0.045 | 16 | echo |
| same_integration_low_familiarity_baseline | 440 | 0.041 | 9 | echo |
| high_familiarity_outside_integration_baseline | 430 | 0.046 | 4 | echo |
| unrelated_baseline | 490 | 0.042 | 13 | echo |
| **integration_alpha** | **0** | 0.000 | 0 | immediate |
| **integration_beta** | **0** | 0.000 | 0 | immediate |

### 5.2 観察と問題点

**観察**:
- **temporal_coactivation peak_lag = 290** (中期で C 変化最大)、**familiarity peak_lag = 480** (より遅延)
- relation_path 経由 (path 4 種) と baseline (5 種) の peak_value 比較:
  - relation paths: 0.107-0.115
  - baselines: 0.041-0.102
  - → relation_path 経由のほうが baseline より高い peak_value (path-enriched 方向の予兆)

**問題点 (Step G で対処)**:
- **integration_alpha / integration_beta が全 lag で 0.0000** → integration cid の C 変化がほぼ無 (Step E mean_delta_C_imm = 0.001 と整合)、ただし peak_lag 算出には不向き
- 大半の path が **echo (残響) 分類**: local_maxes 判定の閾値 0.001 が低すぎる (curve が小振動でも echo になる)
- **lag 500 と lag 1000 が同値**: balance_decisions の `direction='backward'` merge で run end (step 25000) を超えると C_at_decision が更新されないため、lag が大きいほど fill が発生
- これは smoke 段階の制限、Step G で:
  - echo 判定の閾値を 0.01 に上げる
  - integration の peak_lag は除外フラグ
  - run end 近傍 event は除外

---

## 6. 波及パターン分類

10 path 中:
- **immediate (peak_lag < 10)**: integration_alpha, integration_beta (= 全 lag 0、特殊ケース)
- **delayed (peak_lag > 100)**: temporal_coactivation, familiarity 等 8 path (echo に再分類されるため見えない)
- **echo (残響、local_maxes ≥ 2)**: 8 path

→ echo 判定が支配的で **delayed / immediate / echo の 3 区分の意味的差異が出にくい** smoke 結果。Step G で 閾値を厳しくして再分類する必要。

---

## 7. 出力 schema

### 7.1 multi_hop_paths_seed{N}.parquet

```
event_id              object
source_cid            int64
timestamp             int64
target_cid            int64
relation_path_type    object   familiarity_hop1 / hop2 / hop3
relation_strength     float64  経路の弱リンク min(strength)
hop_distance          int64    1, 2, 3
seed                  int64
```

### 7.2 resonance_loops_seed{N}.parquet

```
loop_type    object   loop_2_hop / loop_3_hop
cid_a        int64
cid_b        int64
cid_c        int64    (loop_3_hop only)
fam_ab       float64  (loop_2_hop only)
fam_ba       float64  (loop_2_hop only)
min_strength float64  ループの弱リンク
seed         int64
```

### 7.3 peak_lag_curve_seed{N}.parquet

```
relation_path_type        object
lag_bin                   int64    0, 10, 20, ..., 1000
n_records                 int64
mean_delta_C_at_lag       float64
median_delta_C_at_lag     float64
seed                      int64
```

### 7.4 wave_patterns_seed{N}.parquet

```
relation_path_type     object
peak_lag               int64
n_local_maxes          int64
wave_pattern_class     object   immediate / short_term / delayed / echo
abs_peak_value         float64
seed                   int64
```

---

## 8. 設計判断 (Code A 視点)

### 8.1 multi-hop は familiarity のみ

実装範囲を familiarity に絞った理由:
- attention_via_salience は run 集約 (時間情報なし) → multi-hop 概念無し
- integration_alpha/beta は同 α/β 内で均等 → multi-hop = 同 α 内移動 = 1 hop と等価
- temporal_coactivation は時間窓固有 → multi-hop が時間と path の混合になる

→ familiarity のみで multi-hop graph を構築。これは指示書 §6.1 の「relation_path 経由の到達距離」の意味として自然。

### 8.2 peak_lag のサブサンプリング (5000/path)

per-event-target × 101 lag = 1.7M × 101 = 178M lookups は重いため、relation_path × 5000 records に絞り集計値で peak_lag を出す。これは:
- relation_path レベルの集計 finding (Level 2 / 3 用) には十分
- per-event-target の細粒度 peak_lag は本 step では取らない
- サンプリング seed (random_state=42) 固定で再現性担保

### 8.3 wave_pattern の echo 判定閾値

local_maxes >= 2 で echo。閾値 0.001 で smoke 結果は echo 過多。**Step G で 0.01 に上げる予定**。

---

## 9. Step F 完了条件チェック

- [x] multi-hop graph traversal (3 hop 制限、familiarity 経路)
- [x] 減衰率追跡 (hop 別 baseline_excess_change)
   - 注: hop 2/3 の delta は Step E に存在せず、Step G で再 run 判断
- [x] 共鳴ループ検出 (loop_2_hop 711、loop_3_hop 4563)
- [x] peak_lag 測定 (10 step bin、サブサンプル 5000/path)
- [x] 波及パターン分類 (immediate / short_term / delayed / echo)
- [x] read-only / v107 出力 path 縛り維持
- [x] 構造語徹底
- [x] 24 seeds 単一バッチ実行可能性 (9.3 秒 × 24 = 4 分)

---

## 10. 出力ファイル

```
developmental/v107/
├── v107_avalanche_monitor.py
├── v107_step_f_report.md
└── outputs/smoke/
    ├── multi_hop_paths_seed0.parquet      (328,936 rows × 8 cols, 0.24 MB)
    ├── resonance_loops_seed0.parquet      (5,274 rows, 0.03 MB)
    ├── decay_rate_seed0.parquet           (3 rows, 0.01 MB)
    ├── peak_lag_curve_seed0.parquet       (1,010 rows, 0.01 MB)
    ├── wave_patterns_seed0.parquet        (10 rows, 0.001 MB)
    └── step_f_run_summary.parquet
```

---

## 11. Step G 進行への申請

Step G (統合 smoke + bit-identity 層 B) に進む許可を求めます。

実装方針:
1. **全機構統合 smoke** (seed 0 で全 Step C-F を一気に再実行)
2. **bit-identity 層 A** (再確認、全機構の決定論)
3. **bit-identity 層 B** (v10.6 出力 717 ファイルの MD5 比較、smoke 前後で不変性検証)
4. **Step F の問題点修正**:
   - multi_hop の hop 2/3 delta 集計 (Step E baseline_constructor 拡張または Step F 内独立集計)
   - echo 判定閾値を 0.01 に上げる
   - integration の peak_lag は除外フラグ
5. **storage 実測** (全機構 smoke で seed 0 の総容量を確認、24 seeds 推定)

実行時間予想: 1-2 時間 (smoke 自体は速い、統合と検証が中心)。

Step G 完了後、smoke が PASS なら Step I (24 seeds main run) に進む判定を Web Claude / Taka に求めます。

24 seeds 単一バッチ厳守、3 バッチ分割禁止。

---

*以上、Step F 報告。Web Claude / Taka からの Step G 進行許可待ち。*
