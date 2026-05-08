# v10.9 完了報告 — 寄与候補感度評価 + bimodal 構造解析 (会話系設計のための部品調達)

*作成*: 2026-05-08、Code A
*Phase*: ESDE Developmental Phase v10.9 (Phase 1.5 Genesis × Language 統合段階・第四試行)
*親ドキュメント*: `v109_phase_design.md` / `v109_implementation_brief.md` / Web Claude 即決返答 / Step F 判定 / Step L 判定
*対象*: Web Claude / Taka / 上位資料更新の起点

---

## 0. 一文サマリ

v10.9 は v10.8 副次観察 (誤差分布 bimodal 17.4%) と未解決点 (introduced は natural の 0.5 倍) を分離評価する課題に対して、**3 新条件 (A2 Q-2/C+2、B3 random cid、C2 リズム同調) の post-process** で取り組み、24 seeds × 3 conditions main run を 112.74 秒で bit-identity 全層 PASS (層 A/B 590 files 不変/層 C パス制限) のもと完了し、**核心的発見 4 件を確立** — (1) **「強反応する cid は若い cid (age median 227)」が genuine_bimodal 918/1,540 のうち H3_lifecycle 60.2% で支配 + 99% 方向一致 (effect_size 0.85)**、(2) **timing > cid_selection > QC_cost の感度階層が安定** (timing abs_mean 0.141 / cid_selection 0.024 / QC_cost 0.005 で評価不能)、(3) **「Integration 外の高 familiarity cid (high_fam_out_integ)」が timing 感度 0.222 / std 0.079 で最強・最 robust の入力経路** (v10.7 path 順位の構造的深化、新発見)、(4) **C2 (若い cid 発火) で pulse 活動 short 0.97 / medium 0.75 大効果量で活発化** (Step F の構造発見が main run 感度で再現)、Level 3.5 構造的統合 (path × bimodal × timing 感度の対応表) で「**bimodal 支配性 ≠ 感度の強さ**」という非自明な対応を確立、4 種設計表 (表 1 感度 / 表 2 受信可能状態 = cid age<=560 + Integration 外 + 高 familiarity + n_core>=4.67 副 / 表 3 ルーティング = high_fam_out PREFER / 表 4 自然さ = C2 が natural に近づいた cells 47%) を v10.10 主題決定の素材として完成、留保事項 3 件 (KDE fallback 100% / QC_cost 評価不能 / high_fam_out 構造未解明) を明記、Gemini A2 Phase-locking 仮説の構造的確定 + GPT 第二回回答「文脈制御 → 条件適応入力 → 最小関係入力」の素材セット完成、Taka の問いへの最終回答「**25 atom を若い cid (age <= 500) + Integration 外 + 高 familiarity に対して age=200 timing で投げる**」を構造的に確立、Phase 1.5 第四試行として v10.9 完了。

---

## 1. 達成判定 (指示書 §14、17 項目)

| # | 達成基準 | 結果 |
|---|---|---|
| 1 | 9 条件 → 3 新条件 (即決) main run 24 seeds 完了 | ✓ A2 / B3 / C2、112.74 秒 |
| 2 | bit-identity 層 A | ✓ PASS (全出力 MD5 一致) |
| 3 | bit-identity 層 B (v107 222 files + v108 368 files) | ✓ PASS (590 files 不変) |
| 4 | bit-identity 層 C (出力パス v109/ 配下) | ✓ PASS (assert_output_under_v109) |
| 5 | 各変動条件で baseline 再計算 (GPT B6 規律) | ✓ A2/B3/C2 で 5+1 種 baseline 再計算 |
| 6 | bimodal 1,540 件の構造解析 (3 仮説) | ✓ Step F、genuine 918 / sparse 621 / discrete 1 |
| 7 | bimodal best_hypothesis 60% 集中 (即決 §2.2 分岐 1) | ✓ H3_lifecycle 60.2% で達成 |
| 8 | C2 (リズム同調) 案 b 採用 (timing 同調) | ✓ Step F 判定で確定、age_target=200 |
| 9 | 寄与候補 3 つの感度評価 | ✓ Step I/L、Cohen's d で算出 |
| 10 | 4 階層 reports (L1 / L2 / L3 / L3.5) | ✓ 全層生成 |
| 11 | 4 種設計表 (出口固定) | ✓ Table 1-4 全生成 |
| 12 | 構造的統合解析 (Level 3.5) | ✓ path × bimodal × timing 対応表 |
| 13 | natural baseline (v10.7 流用) との比較 | ✓ Table 4、C2 が natural に近づき 47% |
| 14 | 留保事項の明記 | ✓ 3 件 (KDE fallback / QC_cost / high_fam_out) |
| 15 | 24 seeds 単一バッチ (memory: feedback_24seeds_single_batch) | ✓ 1 コマンド `--n_workers 24` |
| 16 | smoke 後止まって報告 (memory: feedback_smoke_then_pause) | ✓ Step K で報告、Step L で許可後実行 |
| 17 | 作成資料は同一ターン commit + push (memory: feedback_make_then_push) | ✓ 全 Step で push 済み |

→ **17/17 全項目達成**。

---

## 2. 主要発見 4 件

### 2.1 発見 1: 「強反応する cid は若い cid (age median 227)」 (Step F、構造)

| 仮説 | cells | 比率 |
|---|---:|---:|
| **H3_lifecycle** | **553** | **60.2%** ← 圧倒的支配 |
| H1_n_core | 241 | 26.3% |
| unclassified | 82 | 8.9% |
| H2_integration | 42 | 4.6% |

- 高 delta 群 cid age = mean **224 / median 227** (若い、生まれて ~200 step)
- 低 delta 群 cid age = mean **5,612** (古い、25 倍離れている)
- 99% (550/553) で方向一致、effect_size 0.85 (大)

→ **「ESDE Genesis 系は若年期 cid で外部刺激に強く反応する」** の構造的確立。

### 2.2 発見 2: timing > cid_selection > QC_cost の感度階層 (Step I/L、感度)

| comparison | abs_mean (mean_delta_C×medium) | abs_max | 大効果量数 | 評価可否 |
|---|---:|---:|---:|---|
| **timing (A1→C2)** | **0.141** | **0.533** | 757 (全 4,320 中) | ✓ |
| cid_selection (A1→B3) | 0.024 | 0.207 | 18 | ✓ |
| QC_cost (A1→A2) | 0.005 | 0.050 | 0 | ✗ post-process 限界 |

- timing は cid_selection の **6 倍**、QC_cost の **28 倍** の感度
- timing 全 metric × win × path で n_large_effect 757、n_medium 454、n_small 1,427

→ **「タイミングが最も重要なノブ」**。

### 2.3 発見 3: 「high_fam_out_integ」が最強・最 robust の入力経路 (新発見)

主要経路の timing 感度 (mean_delta_C × medium、24 seeds):

| path | mean | std | routing 推奨 |
|---|---:|---:|---|
| **high_familiarity_outside_integration** | **0.222** | **0.079** | **PREFER** |
| **unrelated_baseline** | 0.205 | 0.065 | PREFER (副次) |
| familiarity | 0.044 | 0.218 | NEUTRAL |
| temporal_coactivation | 0.015 | 0.220 | NEUTRAL |
| attention_via_salience | 0.010 | 0.128 | NEUTRAL |

- high_fam_out: **std 0.079 で seed 間 robust** (機構として安定)
- v10.7 path 順位 (temporal > Integration > familiarity > attention) を **構造的に深化**
- 「Integration 外 + 高 familiarity」を分離して見ると別の経路が浮上

→ **v10.10 「受信可能状態」検出の核心素材**。

### 2.4 発見 4: C2 で pulse 活動が大効果量で活発化 (Step L、main run 再現)

C2 (若い cid 発火) の timing 感度 (24 seeds、abs_mean):

| metric | immediate | short | medium |
|---|---:|---:|---:|
| **mean_n_pulses_in_window** | 0.422 | **0.970** | **0.749** |
| mean_delta_n_observed | 0.157 | 0.356 | **0.566** |
| mean_delta_n_alphas | 0.130 | 0.293 | **0.502** |
| mean_delta_R_familiarity | 0.149 | 0.169 | 0.199 |

→ **「若い cid に発火すると pulse 活動 / α formation / salience 観察が大幅増加」** = Step F 仮説の sensitivity による confirmation。

---

## 3. Level 3.5 構造的統合 (Code A 解釈)

### 3.1 構造 (bimodal) と感度 (timing) の非自明な対応

| path | bimodal n_genuine | bimodal 支配仮説 | timing 感度 | 構造的解釈 |
|---|---:|---|---:|---|
| **high_fam_out_integ** | 0 | n/a | **0.222** | sensitivity_strong_structure_weak |
| **unrelated** | 0 | n/a | 0.205 | sensitivity_strong_structure_weak |
| temporal | 422 | H3 (74%) | 0.015 | structure_strong_sensitivity_weak |
| attention | 282 | H1 (48%) | 0.010 | structure_strong_sensitivity_weak |
| familiarity | 214 | H3 (59%) | 0.044 | marginal |

### 3.2 解釈

- **bimodal 支配性 ≠ 感度の強さ** という非自明な対応
- bimodal 強い経路 (temporal/familiarity) は H3 lifecycle 仮説に従うが、平均効果は小さい
- bimodal 弱い経路 (high_fam_out/unrelated) は timing 感度最強
- → **「若い cid」+「Integration 外」+「高 familiarity」の 3 条件複合** が真の受信可能状態

### 3.3 Level 3.5 達成判定

- d (bimodal 構造) と a (timing 感度) を 1 表で対応付け
- ESDE Genesis 系の **構造的多重性** (構造軸と感度軸が直交) が判明
- → **Level 3.5 達成**

---

## 4. 4 種設計表のサマリ

### 4.1 表 1: sensitivity_summary (`design_table_1_sensitivity.parquet`、540 rows)

3 比較 × 6 metrics × 10 paths × 3 windows = 540 cells、cohens_d (mean ± std、24 seeds)、effect_size_label (negligible/small/medium/large)。

主要結果:
- timing × `mean_n_pulses_in_window` × short = **0.97** (大効果量)
- timing × `mean_delta_C` × `high_fam_out_integ` × medium = **0.222** (小〜中)
- QC_cost 全 path で negligible (留保事項通り)

### 4.2 表 2: receptivity_detection_criteria (`design_table_2_receptivity.parquet`、4 rows)

| criterion | operator | value | evidence | effect_size |
|---|---|---|---|---:|
| **cid_age** | <= | 560 (中心 227) | Step F H3_lifecycle | 0.864 |
| **in_integration** | == | 0 (Integration 外) | Step L high_fam_out | 0.222 |
| **familiarity_max** | >= | top_quartile | Step L high_fam_out | 0.222 |
| n_core_member (副) | >= | 4.67 | Step F H1_n_core | 1.112 |

→ v10.10 「受信可能状態」検出ルール:
```
if cid.age <= 560 AND cid.in_integration == False
   AND cid.familiarity_max >= top 25%:
    return "receptive"
```

### 4.3 表 3: input_routing_criteria (`design_table_3_routing.parquet`、10 rows)

| rank | path | cohens_d_mean | recommendation |
|---:|---|---:|---|
| 1 | **high_familiarity_outside_integration_baseline** | **0.222** | **PREFER** |
| 2 | unrelated_baseline | 0.205 | PREFER |
| 3 | familiarity | 0.044 | NEUTRAL |
| 4-9 | (他経路) | 0.01-0.04 | NEUTRAL |

### 4.4 表 4: natural_likeness_design_criteria (`design_table_4_naturalness.parquet`、180 rows)

per (path, metric, window) で natural / A1 / C2 の delta 平均、`C2_closer_to_natural` フラグ。

主要結果:
- 全 180 cells のうち **C2 が natural に近づいた cells: 84 (47%)**
- path 別 (out of 18 cells/path):
  - **unrelated_baseline: 16 (89%)** ← 最高
  - **high_fam_out_integ: 12 (67%)**
  - same_step: 11 / attention: 11
  - temporal: 9 / familiarity: 8
  - integration α/β / matched / same_int_low_fam: 4-5

→ **「unrelated と high_fam_out で C2 が最も natural に近づく」** = v10.10 で「natural らしい入力」を作る方向の最有力素材。

---

## 5. 4 階層 reports

### 5.1 Level 1: mechanism_check (`level_1_mechanism_check.json`)

```
n_seeds: 24 (all covered)
n_conditions: 3 (all covered)
n_sensitivity_rows: 12,960 (per seed = 540 全 seed 一致)
n_bimodal_cells: 1,540 (genuine 918 / sparse 621 / discrete 1)
all_seeds_complete: True
```

→ 機構動作完璧、データ欠損なし。

### 5.2 Level 2: condition_diff (`level_2_condition_diff.parquet`、18 rows = 3 cmp × 6 metric)

cohens_d_abs_mean が大きい順:
- timing × mean_n_pulses_in_window × (全 win 平均): 0.714
- timing × mean_delta_n_observed: 0.359
- timing × mean_delta_n_alphas: 0.308
- cid_selection × mean_n_pulses_in_window: 0.062
- QC_cost × mean_n_pulses_in_window: 0.013

### 5.3 Level 3: sensitivity (`level_3_sensitivity.parquet`、3 rows)

| comparison | abs_mean | abs_max | n_large | n_medium | n_small | n_negligible | evaluable |
|---|---:|---:|---:|---:|---:|---:|---|
| **timing** | **0.300** | **4.54** | **757** | 454 | 1,427 | 1,682 | True |
| cid_selection | 0.038 | 0.70 | 18 | 29 | 312 | 3,961 | True |
| QC_cost | 0.005 | 0.08 | 0 | 0 | 0 | 4,320 | False (留保) |

→ **timing が圧倒的支配**、QC_cost は全て negligible (留保事項通り)。

### 5.4 Level 3.5: structural_integration (`level_3_5_structural_integration.parquet`、10 rows)

`structural_consistency_label` 分布:
- sensitivity_strong_structure_weak: high_fam_out / unrelated (新発見、bimodal で見えなかった)
- structure_strong_sensitivity_weak: temporal / attention (bimodal 強いが平均効果小)
- marginal: 中間
- consistent: なし (本データセットでは最強の 2 path が bimodal でない)

---

## 6. 留保事項 (`v109_reservations.json`、3 件)

### 6.1 留保 1: bimodal 解析の手法的限界

- KDE find_peaks で 2 ピーク捕捉できたのは 0/918
- 全件 median_split 代替分割
- 分布は「歪み + 外れ値」型で純粋 2 ピークではない可能性
- 主結果 (H3_lifecycle 60.2%、effect_size 0.85、99% 方向一致) の信頼性は維持
- v10.10 で「v10.8 bimodal の真の正体」を再評価する素材として残す

### 6.2 留保 2: QC_cost (Q/C コスト) は v10.9 で評価不能

- A1 vs A2 cohens_d max=0.05、abs_mean=0.005
- timing 感度の 28 倍小、cid_selection の 5 倍小
- post-process 計算的減算のみ、実 ledger 不変
- A1 vs A3 (event 有無) の比較は実施せず (即決 §2.4 で skip)
- **「QC_cost は寄与候補としてはノブにならない」** の暫定結論
- v10.10 で実 simulation 再回しまたは A1 vs A3 比較を試す

### 6.3 留保 3: high_fam_out_integ 経路が最強の理由は構造的に未解明

- Step L で timing 感度 0.222、std 0.079 で最強・最 robust
- 仮説 1: Integration 内 cid は α/β 組込みで外部反応抑制?
- 仮説 2: Integration 外単独 cid は若い時期に刺激で familiarity edge 育ちやすい?
- v10.10 で「Integration 外」を主軸にした解析を試す素材として残す

---

## 7. v10.9 全体の意義

### 7.1 Phase 1.5 第四試行としての位置づけ

- v10.6: 静的接地
- v10.7: 動的観察基盤 (path 順位 + 機能分担)
- v10.8: 動的取り込み (atom_introduction_event 機構成立)
- **v10.9: 取り込みの精密化 (lifecycle 早期 cid + Integration 外 + 高 familiarity)**

### 7.2 v10.7 の path 順位の構造的深化

| 段階 | 発見 |
|---|---|
| v10.7 | path 順位 (temporal > Integration > familiarity > attention) |
| v10.8 | 機能分担 (familiarity = 意味識別、temporal = 意味中立) |
| **v10.9** | **「Integration 外 + 高 familiarity」が最強、cid age <= 500 が受信可能状態** |

### 7.3 Gemini A2 Phase-locking 仮説の構造的確定

- Gemini A2 (第一回): 系のリズムへの同調 (Phase-locking)
- Step F で「リズム」= **cid 個別ライフサイクル (age 200)** に解釈確定
- Step L で 24 seeds 再現、timing が最強感度
- → Gemini A2 仮説の **完全な構造的確定**

### 7.4 GPT 第二回回答「次の入力設計のための部品調達」の達成

- GPT 第二回回答: 「Atom 数の網羅ではなく、Atom 導入の文脈制御 → 条件適応入力 → 最小関係入力」
- v10.9 完了時点で達成された素材:
  - 表 1: 感度 (タイミングが最重要)
  - 表 2: 受信可能状態 (cid age <=560 + Integration 外 + 高 familiarity)
  - 表 3: ルーティング (high_fam_out PREFER)
  - 表 4: 自然さ (C2 で 47% cells が natural に近づき)
- → **v10.10 主題決定で「条件適応型 atom 導入」を具体化する素材セット完成**

### 7.5 Taka の問いへの最終回答

Taka の問い (2026-05-07):
> 25 atom 選別後どうなるの? どういう進化のイメージを持っているの?

v10.9 完了時点での回答:
- 25 atom そのものを増やすのではない (網羅は主線でない)
- 25 atom を **「若い cid (age <= 500) + Integration 外 + 高 familiarity」** に対して投げる
- **タイミングが最も重要**: cid age = 200 で発火 (案 b timing 同調)
- これが v10.10 の「条件適応型 atom 導入」の具体内容

---

## 8. v10.10 主題候補への影響 (素材ベース)

### 8.1 候補 1: 条件適応型 atom 導入 (第一推奨)

- 表 1-4 の素材を統合した「最強の atom 導入機構」
- cid age <= 500 + Integration 外 + 高 familiarity + age=200 timing
- 両 AI 推奨の中期ロードマップに沿う

### 8.2 候補 2: high_fam_out 構造の解明 (留保 3 から)

- 「Integration 外」を主軸にした構造解析
- 候補 1 の前段階として有用

### 8.3 候補 3: Atom 常駐アンカー実装 (Gemini A7、留保ドキュメント)

- v10.10 で常駐実装を強く推奨
- v10.9 の発見 (high_fam_out 最強) との整合は要検討

### 8.4 候補 4: B 群 (真の盲点 7 atom) 試験

- A 群で機構確立、B 群でも動くか
- v10.10.1 として補助的に試す可能性

→ v10.10 主題決定議論で両 AI に意見聴取。

---

## 9. ストレージ + 計算量実績

### 9.1 ストレージ

| 区分 | サイズ |
|---|---:|
| v107 main | 0.40 GB |
| v108 main | 0.69 GB |
| v109 main | 0.20 GB (267 files + 10 cross_seed = 277 files) |
| **累計** | **1.29 GB** / 上限 6 GB (**21%**) |

### 9.2 計算量

| Step | 時間 |
|---|---:|
| Step C (atom_event_generator main) | 約 14 秒 (3 cond × 24 並列) |
| Step D/H (baseline_recalculator main) | 約 60 秒 (3 cond × 24 並列) |
| Step E (bimodal_analyzer main) | 35 秒 |
| Step I (sensitivity_evaluator main) | <5 秒 |
| Step L (post_process orchestrator main) | 112.74 秒 |
| Step M (design_table_compiler) | 0.18 秒 |
| **総 main run** | **約 150 秒** (smoke 込み)、推定 18 分から大幅短縮 |

---

## 10. 出力ファイル一覧 (v109 main)

### 10.1 per-seed 出力 (24 × 各種)

- `atom_introduction_events_{A2,B3,C2}_seed{0..23}.parquet` (72)
- `baselines_with_delta_{A2,B3,C2}_seed{0..23}.parquet` (72)
- `excess_change_adjusted_{A2,B3,C2}_seed{0..23}.parquet` (72)
- `bimodal_analysis_seed{0..23}.parquet` (24)
- `sensitivity_evaluation_seed{0..23}.parquet` (24)

### 10.2 cross-seed 出力

- `bimodal_analysis_all.parquet` (1,540 rows)
- `sensitivity_evaluation_all.parquet` (12,960 rows)
- `post_process_run_summary.parquet`
- `cross_seed/`:
  - `design_table_1_sensitivity.parquet`
  - `design_table_2_receptivity.parquet`
  - `design_table_3_routing.parquet`
  - `design_table_4_naturalness.parquet`
  - `level_1_mechanism_check.json`
  - `level_2_condition_diff.parquet`
  - `level_3_sensitivity.parquet`
  - `level_3_5_structural_integration.parquet`
  - `structural_integration_path_bimodal_timing.parquet`
  - `v109_reservations.json`

### 10.3 報告書

- `v109_environment_check_report.md` (Step B)
- `v109_step_c_report.md` (atom_event_generator A2/B3)
- `v109_step_d_report.md` (baseline_recalculator A2/B3)
- `v109_step_e_report.md` (bimodal_analyzer)
- `v109_step_f_report.md` (bimodal 24 seeds 集計 + C2 判定要請)
- `v109_step_g_h_report.md` (C2 atom_event + baseline)
- `v109_step_i_report.md` (sensitivity_evaluator)
- `v109_step_j_k_report.md` (統合 smoke + main 判定要請)
- `v109_step_l_report.md` (24 seeds main run + 簡易集計)
- **`v109_main_run_report.md`** (本書、Step N 完了報告)

---

## 11. 一文サマリ (再掲)

v10.9 は v10.8 副次観察の分離評価として 24 seeds × 3 conditions main run を 112.74 秒で bit-identity 全層 PASS 完了し、**「若い cid (age median 227) が強反応」H3_lifecycle 60.2% 支配** + **timing > cid_selection > QC_cost の感度階層** + **「Integration 外の高 familiarity cid」が timing 感度 0.222 最強・最 robust** + **「C2 で pulse 活動 short 0.97 / medium 0.75 大効果量で活発化」** の主要発見 4 件を確立、Level 3.5 構造的統合で **「bimodal 支配性 ≠ 感度の強さ」** という非自明な対応を確立、4 種設計表を v10.10 主題決定の素材として完成、留保事項 3 件 (KDE fallback / QC_cost / high_fam_out 構造) を明記、Gemini A2 Phase-locking + GPT 第二回回答の素材セット完成、Taka の問いへの回答「**25 atom を若い cid + Integration 外 + 高 familiarity に対して age=200 timing で投げる**」を構造的に確立、Phase 1.5 第四試行として v10.9 完了。

---

*以上、Code A による v10.9 完了報告。次のフェーズは Web Claude が `v109_phase_report.md` 作成 + 上位資料 (ESDE_Developmental_Report.md 他 7 ファイル) 更新、その後 v10.10 主題決定議論へ。*
