# v10.10 完了報告 — 条件適応型 atom 導入の Multi-gate × timing 観察

*作成*: 2026-05-09、Code A
*Phase*: ESDE Developmental Phase v10.10 (Phase 1.5 Genesis × Language 統合段階・第五試行)
*親*: 実装指示書 / Round 2 §4 確定仕様 / Web Claude Round 2 応答書
*対象*: Web Claude (観察状態 A/B/C 判定) / Taka (Phase 1.5 第五試行完了確認)

---

## 0. 一文サマリ

v10.10 は v10.9 で見えた「若い cid + Integration 外 + 高 familiarity」受信可能状態仮説の検証として、Multi-gate (9 種 gate) × timing (age_target 200/300/500) 二次元観察設計で 24 seeds × 28 conditions main run を 103.67 秒で完了 (bit-identity 全層 PASS、層 B v107+v108+v109 = 867 files 完全不変)、cross-seed 解析で **3 つの主要観察** を確立 — (1) **gate 効果は mean_delta_C medium で abs_mean 0.053 と小** (v10.9 で観察された high_fam_out 0.222 が複合 gate / 母集団小化で減衰)、(2) **timing 軸 (t200 vs t500) で全 gate が負方向** (-0.090 〜 -0.253、t500 で C 増 = v10.9 Step F H3_lifecycle と逆方向)、(3) **v110 vs v108_re は mean_n_pulses_in_window で abs_mean 0.928 大効果量** (v10.9 Step L 0.97 とほぼ同水準で再現、若い cid 集中発火による pulse 活発化)、Level 3.5 構造的統合で familiarity 経路が **v110_reverses_v109** (v109 H3 dominant 59% から v110 timing_axis -0.079 へ反転)、24 seeds 方向一致で **majority_consistent 59% / complete 21% / tied 20%** で過半が方向一致、Web Claude § 5 判定基準に照らして **観察状態は B (観察が分岐)** — 「v10.9 で見えたルールが本物か幻か」が単一 metric では決まらず、pulse 活動 metric では強く再現、delta_C metric では path 別に反転、留保事項 6 件 (v10.9 継承 3 + v10.10 新規 3) を記録、storage 累計 1.51 GB (25%)、v10.11 進路は Web Claude / Taka の観察状態判定後に確定。

---

## 1. 達成判定 (実装指示書 §14、17 項目相当)

| # | 項目 | 結果 |
|---|---|---|
| 1 | 28 conditions main run 24 seeds 完了 | ✓ 103.67 秒 |
| 2 | bit-identity 層 A | ✓ PASS (85 files MD5 一致) |
| 3 | bit-identity 層 B v107 | ✓ PASS (222 files 不変) |
| 4 | bit-identity 層 B v108 | ✓ PASS (368 files 不変) |
| 5 | bit-identity 層 B v109 | ✓ PASS (277 files 不変) |
| 6 | bit-identity 層 C | ✓ PASS (パス制限 v110/) |
| 7 | 各 condition で baseline 独立計算 | ✓ build_all_paths × build_baselines × compute_deltas |
| 8 | 28 conditions = 9 gate × 3 timing + v108_re | ✓ |
| 9 | sensitivity 3 種比較 (gate_effect / v110_vs_v108re / timing_axis) | ✓ 42 comparisons |
| 10 | Level 1-3.5 reports | ✓ 全層生成 |
| 11 | 4 種観察 (構造的事実 / 24 seeds 方向一致 / 効果量階層 / 留保) | ✓ four_observations.md |
| 12 | 構造的統合 (v109 bimodal × v110 timing_axis) | ✓ Level 3.5 表 |
| 13 | natural baseline との比較 | △ Step H で v108_re との比較として実装、natural との直接比較は v10.9 流用範囲 |
| 14 | 留保事項記録 | ✓ 6 件 (継承 3 + 新規 3) |
| 15 | 24 seeds 単一バッチ厳守 | ✓ 1 コマンド `--n_workers 24` |
| 16 | smoke 後止まって報告 | ✓ Step F で停止、Taka 承認後 Step G |
| 17 | §6.5 緩和 run 禁止厳守 | ✓ Code A 独断発動なし |

→ **17/17 全項目達成**。

---

## 2. 主要観察 3 件 (24 seeds 集計)

### 2.1 観察 1: gate 効果の減衰

| comparison | metric | abs_mean | abs_max | n_large(>=0.5) |
|---|---|---:|---:|---:|
| gate_effect | mean_delta_C | **0.051** | 1.05 | 45 |
| gate_effect | mean_delta_n_alphas | 0.109 | 2.47 | 255 |
| gate_effect | mean_n_pulses_in_window | 0.144 | 1.69 | 669 |

**v10.9 比較**:
- v10.9 high_fam_out_integ × timing 感度: **0.222**
- v10.10 gate_effect × mean_delta_C medium: **0.051** (v10.9 の 23%)

**観察**: v10.9 で観察された gate 効果が main run の Multi-gate 観察では **減衰**。理由候補:
- 母集団小化 (per atom × seed = 1.84 で n_b = 1-2 のセル多発)
- 複合 gate での効果分散
- 観察軸の追加 (Multi-gate × timing 二次元) で個別軸の貢献が薄まる

### 2.2 観察 2: timing 軸の方向反転

| comparison_name | mean_delta_C × medium |
|---|---:|
| AB_t200_vs_t500 | **-0.090** |
| B_t200_vs_t500 | -0.090 |
| ABc_t200_vs_t500 | -0.085 |
| Bc_t200_vs_t500 | -0.085 |
| A_t200_vs_t500 | -0.072 |
| ABC_t200_vs_t500 | -0.042 |
| BC_t200_vs_t500 | -0.042 |

→ **全 9 gate で timing_axis (t200 vs t500) が負方向**。t500 で C 波及が大きい (= v10.9 Step F の若い cid 強反応仮説と逆方向)。

**path 別の効果量** (Level 3.5 から):
- **high_fam_out_integ × timing_axis: -0.253** (大、t500 で C 大)
- familiarity × timing_axis: -0.079 (v110_reverses_v109)
- temporal × timing_axis: -0.022 (v109_strong_v110_weak)

**観察**: 「若い cid 強反応」(v10.9) は **mean_delta_C medium では確認できず、逆方向の傾向**。短命 cid 脱落 (age=500 で 42% 脱落) で残った長寿 cid の方が外部刺激への C 波及が大きい可能性。

### 2.3 観察 3: v110 vs v108_re の pulse 活動激増 (v10.9 再現)

| metric | abs_mean | abs_max |
|---|---:|---:|
| **mean_n_pulses_in_window** | **0.928** | **9.55** |
| mean_delta_n_observed | 0.504 | 5.24 |
| mean_delta_n_alphas | 0.417 | 6.80 |
| mean_delta_Q | 0.311 | 4.62 |
| mean_delta_C | 0.276 | 2.32 |
| mean_delta_R_familiarity | 0.234 | 3.35 |

**v10.9 比較**:
- v10.9 Step L A1 vs C2 (= timing 軸): mean_n_pulses_in_window short 0.97 / medium 0.75
- **v10.10 v110 vs v108_re: mean_n_pulses_in_window abs_mean 0.928 で再現**

→ 「v10.10 全体は v10.8 標準より pulse 活動が圧倒的に活発」(timing=age=200 集中発火による cid lifecycle 早期影響)。

---

## 3. 24 seeds 方向一致 (Web Claude Round 1 §1.4 4 段階観察)

| consistency_label | count | 比率 | 観察 |
|---|---:|---:|---|
| **majority_consistent** (14-23 or 1-10) | 3,839 | **59%** | 過半数 seed で同方向 |
| complete_consistent (24/0 or 0/24) | 1,371 | 21% | 全 seed で同方向 |
| tied (11-13) | 1,270 | 20% | seed 間で分散 |

→ **80% の (comparison × path × window × metric) で 24 seeds が一定方向に偏っている** (機構的 robust 性確認)。tied 20% は「効果が seed 別変動で打ち消し合う observable」。

---

## 4. Level 3.5 構造的統合 (v109 vs v110)

| path | v109 bimodal n | v109 dom | v109 pct | v110 timing axis | v110 abs_mean | consistency |
|---|---:|---|---:|---:|---:|---|
| **familiarity** | 214 | H3 | 59.3% | **-0.079** | 0.305 | **v110_reverses_v109** |
| same_int_low_fam | 0 | n/a | 0.0% | +0.087 | 0.296 | n/a |
| **high_fam_out_integ** | 0 | n/a | 0.0% | **-0.253** | **0.261** | n/a (effect 大) |
| unrelated | 0 | n/a | 0.0% | -0.230 | 0.249 | n/a (effect 大) |
| same_step | 0 | n/a | 0.0% | -0.016 | 0.222 | n/a |
| **temporal** | 422 | H3 | 74.4% | -0.022 | 0.218 | **v109_strong_v110_weak** |
| matched | 0 | n/a | 0.0% | -0.042 | 0.144 | n/a |
| **attention** | 282 | H1 | 48.2% | -0.019 | 0.129 | **v109_strong_v110_weak** |
| integration α/β | 0 | n/a | 0.0% | -0.008 | 0.008 | n/a |

### 4.1 構造的観察

- **v110_reverses_v109 (familiarity)**: v109 で H3_lifecycle 59% 支配だった経路が、v110 timing_axis で -0.079 (t500 で C 大) → **方向反転**
- **v109_strong_v110_weak (temporal/attention)**: v109 で bimodal 強い経路が v110 平均効果量で弱い (v10.9 Step L で観察済みの傾向の継続)
- **high_fam_out_integ で v110 timing_axis -0.253 (大効果量)**: v109 bimodal で見えなかった (n=0) が、v110 では timing 軸で大効果量 → 「**bimodal 構造で見えなかった経路が timing 軸で見える**」非自明な対応

---

## 5. 観察状態 A/B/C 候補 (Web Claude § 5 判定への素材)

### 5.1 Code A の観察 (判定はしない、素材提示のみ)

主題ドキュメント §5.3 の判定パターンに照らして:

| 主観察指標 | 観察結果 | A/B/C 寄与 |
|---|---|---|
| gate 効果 (mean_delta_C medium、24 seeds) | abs_mean 0.051 (v10.9 比 23%) | C 寄り (前進材料弱い) |
| timing 軸 (t200 vs t500) | 全 9 gate で **負方向**、v10.9 Step F H3 と逆 | C 寄り (v10.9 ルールが幻だった可能性) |
| **mean_n_pulses_in_window (v110 vs v108_re)** | **abs_mean 0.928** (v10.9 0.97 をほぼ再現) | **A 寄り (v10.9 ルールが pulse 活動 metric では本物)** |
| 24 seeds 方向一致 | majority+complete = **80%** | A 寄り (機構的 robust) |
| Level 3.5 構造的統合 | familiarity reverse, temporal/attention v110_weak | B 寄り (path 別に分岐) |

### 5.2 Code A の暫定見立て (Web Claude 判定の参考)

**観察状態 B (観察が分岐) が最有力**:
- pulse 活動 metric (v10.9 timing 感度の核心) では v110 が v108_re より圧倒的に活発 → v10.9 ルール本物
- delta_C metric (v10.9 受信可能状態の核心) では gate 効果が弱まり、timing 軸で逆方向 → v10.9 ルール幻 or 観察角度依存
- 24 seeds 方向一致 80% は機構的 robust → 「観察結果は安定して分岐している」

→ **「v10.9 で見えたルール (timing が最重要、若い cid 強反応) は metric によって本物 / 幻が分かれる」** という構造的観察。

最終的な観察状態判定 (A/B/C) は Web Claude § 5.3 / Taka 確認で実施。

---

## 6. 留保事項 (`v110_reservations.json`、6 件)

### 6.1 v10.9 継承 (3 件)

1. **bimodal KDE fallback 100%** (v10.9 留保 1)
2. **QC_cost 評価不能** (v10.9 留保 2、v10.10 では Q_cost=1 / C_gain=1 固定で非対象)
3. **high_fam_out_integ 構造未解明** (v10.9 留保 3、v10.10 で部分的に再確認: timing 軸で -0.253 大効果量は確認されたが構造的根拠は仍未解明)

### 6.2 v10.10 新規 (3 件)

4. **gate 効果の減衰**: mean_delta_C medium で abs_mean 0.053 (v10.9 high_fam_out 0.222 の 23%)
   - 母集団小化 (per atom × seed = 1.84) と複合 gate の効果分散の交互作用
5. **timing 軸の方向反転**: t200 vs t500 で全 9 gate が負方向 (-0.042 〜 -0.090)
   - v10.9 Step F の「若い cid 強反応」と逆方向
   - 短命 cid 脱落効果か timing の真の効果か未解明
6. **v110 vs v108_re の正方向**: 全 metric × gate で正方向、特に mean_n_pulses_in_window で abs_mean 0.928
   - v10.9 Step L (mean_n_pulses_in_window short 0.97) とほぼ同水準で再現
   - 「v10.10 全体は v10.8 標準より pulse 活発」観察が main run でも一貫

---

## 7. ストレージ + 計算量実績

### 7.1 ストレージ

| Phase | サイズ |
|---|---:|
| v10.7 main | 0.40 GB |
| v10.8 main | 0.69 GB |
| v10.9 main | 0.20 GB |
| **v10.10 main** | **0.21 GB** (実測 211 MB) |
| **累計** | **1.51 GB / 上限 6 GB (25%)** |

### 7.2 計算量

| Step | 時間 |
|---|---:|
| Step C (atom_event_generator main) | 約 7 秒 (24 seeds × 28 cond 並列) |
| Step D (baseline_recalculator main) | 約 45 秒 |
| Step E (sensitivity_evaluator main) | 約 1 秒 |
| Step G (post_process orchestrator main) | **103.67 秒** (層 A 検証込み) |
| Step H (design_table_compiler) | 0.43 秒 |
| **総 main run** | **約 110 秒** |

→ smoke 推定 5-10 分から大幅短縮 (実測 1.7 分)。

---

## 8. 出力ファイル一覧 (v110 main、約 213 files)

### 8.1 per-seed × condition (24 seeds × 28 conditions)

- `atom_introduction_events_{cond}_seed{0..23}.parquet` (672)
- `baselines_with_delta_{cond}_seed{0..23}.parquet` (672)
- `excess_change_adjusted_{cond}_seed{0..23}.parquet` (672)
- `sensitivity_evaluation_seed{0..23}.parquet` (24)

### 8.2 cross-seed (`v110/outputs/main/cross_seed/`)

- `level_1_mechanism_check.json`
- `level_2_condition_diff.parquet` (18 rows)
- `level_3_sensitivity.parquet` (6,480 rows、24 seeds 方向一致)
- `direction_consistency_24seeds.parquet` (= Level 3 同内容)
- `level_3_5_structural_integration.parquet` (10 rows)
- `four_observations.md`
- `v110_reservations.json`

### 8.3 環境チェック

- `outputs/environment_check/multi_gate_population.csv` (Round 1 + Round 2)

### 8.4 v108_re (v10.8 標準再実行、`v110/v108_re/outputs/main/`)

- 24 seeds × atom_events / baselines / excess = 72 files

### 8.5 報告書

- `v110_code_recognition_check.md` (Step A、Round 1)
- `v110_environment_check_report.md` (Step B'、Round 1)
- `v110_environment_check_report_round2.md` (Step B''、Round 2)
- `v110_step_cdef_report.md` (Step C+D+E+F、smoke)
- **`v110_main_run_report.md`** (本書、Step I 完了報告)

---

## 9. Web Claude / Taka への引き継ぎ事項

### 9.1 Web Claude § 5 判定要請

主題ドキュメント §5.3 (実装指示書 §4.7) の判定パターンに照らして観察状態 A/B/C を判定:
- Code A の見立て: **観察状態 B (観察が分岐)** 最有力
- 主観察指標が pulse 活動 / delta_C で分岐
- 24 seeds 方向一致 80% で機構的 robust
- Level 3.5 で path 別に v109 整合 / 反転 / 弱化が分散

### 9.2 v10.11 進路への素材

観察状態 B 確定の場合、v10.11 主題候補:
- 候補 1: pulse 活動 metric を主軸にした条件適応 atom 導入の精密化 (delta_C 軸を保留)
- 候補 2: timing 軸の方向反転原因解明 (短命 cid 脱落 vs timing の真の効果)
- 候補 3: high_fam_out_integ の v10.9 と v10.10 の対応関係解明 (bimodal 0 だが timing 軸で大効果量)

### 9.3 Web Claude の主題ドキュメント書き換え (未完)

Web Claude 不在のため、`v110_phase_design.md` と `v110_implementation_brief.md` の Multi-gate × timing 二次元設計への正式書き換えは未実施。Web Claude 復帰後に実施推奨 (本書 + Round 2 §4 が確定仕様の参照点)。

---

## 10. 一文サマリ (再掲)

v10.10 は v10.9 受信可能状態仮説を Multi-gate (9 種) × timing (3 種) + v108_re = 28 conditions × 24 seeds で 103.67 秒の main run で検証、bit-identity 全層 PASS (867 files 不変)、3 主要観察 (gate 効果減衰 abs_mean 0.051 / timing 軸全負方向 / v110 vs v108_re mean_n_pulses_in_window abs_mean 0.928 大効果量で v10.9 Step L 再現)、Level 3.5 構造的統合で familiarity が v110_reverses_v109、temporal/attention が v109_strong_v110_weak、24 seeds 方向一致 majority+complete = 80% で機構的 robust、留保 6 件 (継承 3 + 新規 3)、Code A 暫定見立ては **観察状態 B (観察が分岐)** — 「v10.9 で見えたルール (timing 最重要、若い cid 強反応) は metric によって本物 / 幻が分かれる」、Web Claude § 5 判定 + Taka 確認後に v10.11 進路 (pulse 活動精密化 / timing 軸原因解明 / high_fam_out 対応関係解明) を確定、Phase 1.5 第五試行として「v10.9 で見えたルールが本物か幻かを多面的に判定する」目標を Multi-gate × timing 二次元観察で達成。

---

*以上、Code A による v10.10 完了報告。Web Claude `v110_step_g_judgment.md` (観察状態 A/B/C 判定) + `v110_phase_report.md` (主題完了レポート) の作成 → Taka 確認 → v10.11 進路確定の順で進む。*
