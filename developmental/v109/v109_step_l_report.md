# v10.9 Step L 完了報告 — 24 seeds main run + cross-seed 簡易集計

*作成*: 2026-05-08、Code A
*実行*: `python3 v109_post_process.py --mode main --n_workers 24` (1 コマンド単一バッチ)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

24 seeds × 3 conditions (A2/B3/C2) の main run を **112.74 秒** (1 回目 60 秒 + 層 A 検証 30 秒 + メタ) で完了、**bit-identity 全層 PASS** (層 A 全出力 MD5 完全一致 / 層 B v107 222 + v108 368 = 590 files 完全不変 / 層 C パス制限)、storage 累計 v107 + v108 + v109 = 1.29 GB / 上限 6 GB (**21%**)、267 files / 190 MB の main outputs 生成、簡易 cross-seed 集計で **timing が cid_selection の 6 倍感度** (abs_mean 0.141 vs 0.024)、特に **mean_n_pulses_in_window short 0.97 / medium 0.75 (大効果量)** で「C2 (若い cid 発火) で pulse 活動が活発化」の構造的証拠、**QC_cost は max 0.05 で留保事項通り評価不能**、Step M (4 種設計表生成 + 構造的統合解析) 進行準備完了、Web Claude / Taka の Step M 方針判定 (Q2 設計表優先度 / Q3 統合解析方針) を待ち。

---

## 1. 24 seeds main run 実績

```
v10.9 post-process orchestrator - mode=main, seeds=24,
                                  conditions=['A2', 'B3', 'C2'], n_workers=24

=== 並列実行 (24 workers、24 seeds 単一バッチ) ===
  seed= 0: t_atom=0.59s, t_baseline=61.42s, t_sens=0.18s, total=62.20s
  seed= 1: t_atom=0.59s, t_baseline=58.27s, t_sens=0.20s, total=59.06s
  ...
  seed=23: t_atom=0.62s, t_baseline=61.37s, t_sens=0.19s, total=62.18s

=== bit-identity 層 A 検証 (seed 0 で 2 回目実行) ===
  PASS: 全出力が 2 回目で MD5 完全一致

=== bit-identity 層 B 検証 (v10.7/v10.8 main 不変性) ===
  PASS v107: 222 files 全て不変
  PASS v108: 368 files 全て不変

=== storage 実測 (seed 0 / main) ===
  TOTAL (per seed): 7.465 MB
  24 seeds 推定:    179 MB

DONE  total elapsed = 112.74s
```

### 1.1 計算時間内訳

| 項目 | 時間 |
|---|---:|
| 24 seeds × 3 conditions 並列 (1 回目) | 約 63 秒 |
| 層 A 検証 (seed 0 で 2 回目実行) | 約 46 秒 |
| 層 B baseline MD5 取得 + 検証 | 数秒 |
| **総 elapsed** | **112.74 秒** |

→ 純粋な main 24 並列実行は約 63 秒。Step J smoke 推定 (50-60 秒) と整合。

### 1.2 storage 実測

| 区分 | 値 |
|---|---:|
| v10.9 main outputs files | 267 |
| v10.9 main outputs total | **190.4 MB (0.186 GB)** |
| 累計 (v107 + v108 + v109) | 1.29 GB / 上限 6 GB (**21%**) |

---

## 2. bit-identity 全層検証 (main run)

| 層 | 内容 | 結果 |
|---|---|---|
| A | seed 0 で 2 回目実行、全出力 MD5 一致 | **PASS** ✓ |
| B v107 | 222 files 完全不変 | **PASS** ✓ |
| B v108 | 368 files 完全不変 | **PASS** ✓ |
| C | 出力パス v109/ 配下強制 | **PASS** ✓ |

→ 物理層 frozen 厳守、再現性担保。

---

## 3. 簡易 cross-seed 集計 (24 seeds)

### 3.1 timing 感度 (A1 vs C2、全 metric × window、Cohen's d abs_mean)

| metric | immediate | short | medium |
|---|---:|---:|---:|
| mean_delta_C | 0.072 | 0.126 | 0.141 |
| mean_delta_Q | 0.077 | 0.140 | 0.177 |
| mean_delta_R_familiarity | 0.149 | 0.169 | 0.199 |
| **mean_delta_n_alphas** | 0.130 | 0.293 | **0.502** |
| **mean_delta_n_observed** | 0.157 | 0.356 | **0.566** |
| **mean_n_pulses_in_window** | 0.422 | **0.970** | **0.749** |

→ **C2 (若い cid 発火) で観察時間 medium-short の pulse 数 / α formation 数 / salience 観察数が大幅増加**。

### 3.2 3 候補感度の最終階層 (mean_delta_C × medium、24 seeds)

| comparison | mean | abs_mean | max_abs |
|---|---:|---:|---:|
| **timing** (A1 vs C2) | 0.050 | **0.141** | **0.533** |
| cid_selection (A1 vs B3) | -0.003 | 0.024 | 0.207 |
| QC_cost (A1 vs A2) | -0.000 | 0.005 | 0.050 |

→ timing > cid_selection > QC_cost の感度階層が **24 seeds でも安定**、smoke 結果 (seed 0) と整合。

### 3.3 主要経路の timing 感度 (mean_delta_C × medium、seed 別ばらつき)

| path | mean | std | seeds |
|---|---:|---:|---:|
| **high_fam_out_integ** | **0.222** | 0.079 | 24 |
| familiarity | 0.044 | 0.218 | 24 |
| temporal_coactivation | 0.015 | 0.220 | 24 |
| attention_via_salience | 0.010 | 0.128 | 24 |

→ **「Integration 外の高 familiarity cid」(high_fam_out)** が最も安定した正方向 timing 感度 (0.222、std 0.079 で seed 間 robust)。

### 3.4 bimodal × path × best_hypothesis (Step F 既存集計)

| path | H1_n_core | H2_integration | H3_lifecycle | unclassified | total |
|---|---:|---:|---:|---:|---:|
| temporal_coactivation | 57 | 4 | **314 (74%)** | 47 | 422 |
| attention_via_salience | 136 (48%) | 4 | 112 (40%) | 30 | 282 |
| familiarity | 48 | 34 (16%) | 127 (59%) | 5 | 214 |

---

## 4. Step F + Step I の構造的統合 (Code A 解釈)

### 4.1 構造 (bimodal) と感度の対応

| path | bimodal 支配仮説 | timing 感度 (mean_delta_C medium) | 解釈 |
|---|---|---:|---|
| **high_fam_out** | (bimodal 少) | **0.222** | C2 で安定した強い効果 |
| familiarity | H3 lifecycle | 0.044 | H3 仮説で seed 別変動大 |
| temporal | H3 lifecycle 圧倒 (74%) | 0.015 | bimodal 構造強いが平均効果小 |
| attention | H1 n_core (48%) | 0.010 | n_core 仮説で平均効果小 |

### 4.2 高 fam_out_integ が最強感度の意味

- bimodal 解析では特に支配的でないが、timing 感度では最強
- 「Integration 外の高 familiarity cid」 = 「他の cid と familiarity edge を持つが α/β に所属していない cid」
- C2 (若い cid 発火) で最も C 増えやすい
- → **「単独の若い cid が familiarity 経由で反応」** が最も robust なシグナル

### 4.3 v10.10 への含意

- 「受信可能状態」検出基準 (表 2): **cid age < 500 + Integration 外 + 高 familiarity** が最強候補
- 「入力ルーティング」: high_fam_out 経路を優先

---

## 5. Step M 進行への申請 (Web Claude / Taka 判定要請)

Step M (cross-seed 解析 + 4 種設計表生成 + 構造的統合解析) に進む許可を求めます。

### 5.1 Code A 推奨進行案

#### 5.1.1 4 種設計表 (Code A 推奨フォーマット)

##### 表 1: sensitivity_summary
- 候補別 (timing / cid_selection / QC_cost) × metric × path × window で Cohen's d (mean ± std、24 seeds)
- 留保事項 (QC_cost 不能) 明記
- 出力: `developmental/v109/outputs/main/cross_seed/design_table_1_sensitivity.parquet`

##### 表 2: receptivity_detection_criteria
- Step F 結果反映: cid age <= 500 = 受信可能状態
- 各 path × cid 属性 (n_core, age, in_integration) で受信可能スコアを定義
- 出力: `design_table_2_receptivity.parquet`

##### 表 3: input_routing_criteria
- Step F + Step I 統合: high_fam_out (Integration 外 + 高 familiarity) 経路が最強
- atom 別 × cid 属性別の routing rule
- 出力: `design_table_3_routing.parquet`

##### 表 4: natural_likeness_design_criteria
- v10.7 natural baseline と C2 の比較
- introduced (atom_intro) を natural に近づけるための条件組合せ
- 出力: `design_table_4_naturalness.parquet`

#### 5.1.2 4 階層 reports (v10.7/v10.8 流用)

- Level 1: 機構動作確認 (3 conditions が想定通り動いているか)
- Level 2: 条件差確認 (A1 vs A2/B3/C2 の path × window 別差)
- Level 3: 寄与候補感度評価 (Step I 集計結果)
- Level 3.5: 構造的説明候補整合 (Step F の H3 lifecycle と Step I の timing 感度の対応)

### 5.2 Web Claude / Taka 判定要請

**Q2 (Step J 報告書から再掲): Step M 4 種設計表の優先度**
- A. 4 種同時生成 (Code A 推奨、Step M で 1-2 時間)
- B. 表 2 (receptivity) と表 3 (routing) を優先、表 1/4 は v109 完了後に追加
- C. その他

**Q3: bimodal × sensitivity 統合解析**
- A. 単純に並列レポートで提示 (簡単)
- B. 構造的統合 (Code A 推奨、例: Step F の H3_lifecycle と Step I の timing 感度を 1 表で対応)
- C. その他

### 5.3 Step M 推定計算量

- 全 4 種設計表生成: 5-10 分 (集計のみ)
- 4 階層 reports: 5-10 分
- 統合解析: 5 分
- 計: 約 30 分

### 5.4 Step N 予定

Step M 完了後、Step N (`v109_main_run_report.md`) で v10.9 完了報告書を生成、commit + push。

---

## 6. Step L 完了条件チェック

- [x] 24 seeds × 3 conditions main run 完了 (112.74 秒)
- [x] 24 seeds 単一バッチ厳守 (1 コマンド、--n_workers 24)
- [x] bit-identity 層 A PASS
- [x] bit-identity 層 B PASS (v107 222 + v108 368 = 590 files 不変)
- [x] bit-identity 層 C PASS
- [x] storage 実測 (190 MB、累計 1.29 GB / 21%)
- [x] sensitivity_evaluation_all.parquet 生成 (12,960 rows / 498 KB)
- [x] 簡易 cross-seed 集計実施
- [x] 主要発見 (timing 感度の安定性、high_fam_out の robust 性) を抽出
- [x] Step M 進行案を Code A 推奨で整理

---

*以上、Code A による v10.9 Step L 完了報告。Web Claude / Taka からの Step M 方針判定 (Q2 / Q3) を待ち、Step M (4 種設計表 + 構造的統合解析) → Step N (完了報告) へ。*
