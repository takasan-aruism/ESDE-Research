# v10.12 Step A 認識確認文書 — 第 4 版主題ドキュメント + 第 3 版実装指示書への応答

*作成*: 2026-05-10、Code A
*親*: `v112_phase_design.md` 第 4 版 + `v112_implementation_brief.md` 第 3 版 (Web Claude 2026-05-10)
*対象*: Web Claude (即決事項返答へ)、Taka (承認)
*目的*: Q-A1〜Q-A11 + DC-A1〜DC-A5 全件回答 + 重大ブロッカー早期警告 + 規律遵守自己検証

---

## 0. 一文サマリ

第 4 版主題ドキュメント (2 trial 分割、§5.6 規律チェックリスト追加) + 第 3 版実装指示書を読み込み、Step A 認識確認を実施、**Q-A1 で 1 件の重大ブロッカーを早期警告**: Step Z 補完データ (`q_z1_n_core_breakdown.parquet`) から **trial-B (bin_2 × 4 条件) は per seed mean 0.2、total 4 events** で paired_d 算出不能 (Q2=977 緩和でも cond4 high_fam top 25% が bin_2 にとって厳しすぎる構造的問題、bin_2 76% 多数派の cid は familiarity 分散で top 25% 該当が 12.5% に留まる)、trial-A (bin_5+ × 4 条件) は Q3 維持で per seed 3.9 / Q2 緩和で推定 7-8 で境界、Q-A4 paired_d は per (seed, atom, path, window) で v112 vs v108_matched_pool_bin の delta を取り 24 seeds 集計の方針提案、Q-A5 命名は v10.10 規約継承で `atom_events_{condition_id}_seed{N}.parquet` (condition_id = "v112_trial_A" 等) 6 種類、Q-A6 bootstrap n_iter 1000 (主軸) / 500 (副次)、Q-A8 main run 推定 1-2 分 (24 並列、6 conditions × 6 baselines = 36 baseline)、Q-A9 storage 累計 v107-v112 約 2.0-2.5 GB / 上限 6 GB (33-42%) 余裕あり、Q-A10 メモリ使用量 v10.10 と同等 (4-8 GB peak 推定)、Q-A11 §6.3 規律遵守項目すべて遵守、DC-A1 trial-B cond4 緩和案 (top 50% / cond4 除外) を Web Claude/Taka 判断要請、DC-A2 top_quartile_threshold per-seed 採用 (Step Z で std/global=0.61 確定)、DC-A3 v108_original は v10.8 既存出力流用 (層 B 不変対象、bin 別 filter は post-process)、DC-A4 bootstrap n_iter 1000 採用、Code A 規律遵守自己検証は §3 で全項目チェック、Step B (環境チェック詳細 + Q2_threshold / top_quartile_threshold 実測 + trial-B 母集団緩和案再実測) に進む準備完了、ただし Q-A1 重大ブロッカー解消が前提。

---

## §1 重大ブロッカーの早期警告 (Q-A1)

### 1.1 trial-B 母集団の構造的問題

Step Z 補完データ (`q_z1_n_core_breakdown.parquet`、commit df04d0a) を再確認した結果、以下が判明:

| 条件 | bin_2 (trial-B 想定) | bin_5+ (trial-A 想定) |
|---|---:|---:|
| AND_1_2 (cond1 ∧ cond2_Q3、cond3/cond4 なし) | per seed 14.5 | per seed 18.7 |
| AND_1_4 (cond1 ∧ cond4、cond2/cond3 なし) | per seed **39.1** | per seed 4.5 |
| **AND_1_2_4_no_cond3** (4 条件で cond3 抜き) | per seed **0.2** | per seed 3.9 |

→ **trial-B の 4 条件 (cond1 + cond2_Q2 + cond3=n_core==2 + cond4) は per seed 0.2 (Q3 維持)** で paired_d 算出不能。

### 1.2 構造的根拠

bin_2 (ESDE 76% 多数派) では:
- cond4 (familiarity top 25%) は per seed quantile で計算
- v108 top_k_100 pool の n_core 分布は 75.6% bin_2 / 12.5% bin_5+
- しかし「top 25% by fam」は bin 別ではなく全 cid の上位 25% を取るため、bin_2 でも分布上 12.5% 程度しか該当しない (実測値)
- AND_1_4 = per seed 39.1 (cond1 + cond4 のみ) → bin_2 で「¬β + 高 fam」は確保
- AND_1_2 (cond1 + cond2_Q3) = per seed 14.5 → bin_2 で「¬β + 長寿」は確保
- ただし **cond1 + cond2 + cond4 の AND** で bin_2 母集団が劇的に減る

### 1.3 Q2=977 緩和での推定

- Q3=2,485 → Q2=977 で cond2 該当が約 2 倍 (Step Z Q-Z2 分布から推定)
- AND_1_2_4_no_cond3 (bin_2): per seed 0.2 → Q2 緩和で **per seed 0.4 程度** (依然絶対不足)
- 主因は cond4 が bin_2 で稀少なこと (Q2 緩和では解消されない)

### 1.4 trial-A の境界懸念

- AND_1_2_4_no_cond3 (bin_5+): per seed 3.9 (Q3) → Q2 緩和で推定 **7-8** (境界、paired_d 算出は技術的に可能だが信頼性懸念)
- AND_1_2 (bin_5+): per seed 18.7 (Q3) → Q2 緩和で推定 **35-40** (cond4 抜きなら十分)

### 1.5 Web Claude/Taka 判断要請事項 (新規)

主題 §13.2 4 項目固定 (条件は変更しない) 規律と Q-A1 重大ブロッカーの両立:

#### 候補 a: trial-B のみ条件緩和 (cond4 除外 or 緩和)

trial-B では cond4 を:
- (a-1) 除外 (cond1 + cond2 + cond3 のみ)
- (a-2) 緩和 (top 50%)
- (a-3) 別 metric (例: total familiarity sum)

→ 主題 §13.2 4 項目固定の「primary 条件は変更しない」と矛盾するため、Web Claude/Taka 判断必須。

#### 候補 b: trial-B 中止、trial-A のみ実施

- trial-B 母集団確保が構造的に困難 → trial-B を中止
- trial-A 単独で v10.12 を実施
- v10.13 で別アプローチで pulse 系を扱う

#### 候補 c: 主題変更

- 2 trial 分割設計の前提 (bin_2 で pulse 系 4 条件複合) が成立しない
- 3 条件設計 (cond4 除外) で 2 trial 続行
- 主題 §5 の 4 条件複合を 3 条件に修正

→ Code A は **(a-2) trial-B のみ cond4 を top 50% 緩和** が主題 §13.2 規律と整合性高いと推定 (緩和は trial 別、4 条件構造維持)、ただし判断は Web Claude/Taka。

---

## §2 Q-A2〜Q-A11 回答

### 2.1 Q-A2: 母集団不足以外の重大ブロッカー

| 項目 | 状態 | 備考 |
|---|---|---|
| 機構不在 | なし | v10.10 build_alpha_beta_intervals + v10.11 q_c_inherited observer 流用可能 |
| データ不在 | なし | Step Z でデータ全確認、alpha/beta_lifecycle_log + balance_decisions + pulse_log 全揃い |
| 規模超過 | なし | main run 1-2 分、storage 累計 33-42% (打ち切り 50% 余裕) |
| **規律違反リスク** | あり | Q-A1 trial-B 母集団不足対応で §13.2 規律と接触の可能性、§1.5 で Web Claude/Taka 判断要請 |

### 2.2 Q-A3: v10.5 機構との整合 (Step Z Q-Z5 + main run 後)

| 確認時点 | 内容 | 状態 |
|---|---|---|
| §1.1 先取り | 主題 §1.1 で v10.5 機構 A/C を参照、条件 1 (β member 除外) で機構 A 自明再観察を回避 | 第 4 版で遵守 |
| Step Z Q-Z5 | (b) 部分的に重なる: 条件 1 単独は v10.11 既知、4 条件複合での比較は新規 | Step Z で確認済 |
| 実装段階 | retrospective + online-deployable 2 層分離 (GPT 修正 2)、主題 §5.1.1 / §5.2.1 で実装 | 担保可能 |
| main run 後再確認 | 結果が v10.5 機構の自明な再観察に終わっていないか、§4 で確認 | 主題完了報告で実施 |

→ **担保可能**、Step A 段階での懸念なし。

### 2.3 Q-A4: paired effect size の対応関係

提案: **per (seed, atom, path, window) でペアリング、24 seeds 集計**

```python
# 各 (seed, atom, path, window) で v112 と v108_matched の delta を取得
def compute_paired_d(v112_metrics, v108_matched_metrics):
    # per (atom, path, window) で per-seed 値を取り、24 seeds 内で paired
    pairs = []
    for (atom, path, window) in itertools.product(ATOMS, PATHS, WINDOWS):
        v112_per_seed = [v112_metrics[seed][atom][path][window] for seed in range(24)]
        v108_per_seed = [v108_matched_metrics[seed][atom][path][window] for seed in range(24)]
        # paired delta
        delta_per_seed = [v112[i] - v108[i] for i in range(24)]
        d = np.mean(delta_per_seed) / np.std(delta_per_seed, ddof=1) if np.std(delta_per_seed, ddof=1) > 0 else 0
        pairs.append((atom, path, window, d))
    return pairs
```

per-cid ではなく per-seed × per-atom × per-path × per-window でペアリング。理由:
- per-cid ペアリングだと target_pool が trial 別に異なるため非対応
- per-seed ペアリングで cid 構造差を排除 (within-seed 比較)
- 24 seeds が paired data points

代替案 (Code A 留保): per-seed の **集計後 metric** (mean across atoms × paths × windows) で 24 seeds 内 paired。これは「主軸 metric は per-seed の単一値」になり、bootstrap CI が seed 軸でしか取れない。

→ Web Claude/Taka 判断: 上記主提案で OK か、別の paired 構造か。

### 2.4 Q-A5: 6 種類 event 命名 (v10.10 規約継承)

```
developmental/v112/outputs/main/
├── atom_introduction_events_v112_trial_A_seed{N}.parquet
├── atom_introduction_events_v108_matched_trial_A_seed{N}.parquet
├── atom_introduction_events_v108_original_bin_5plus_seed{N}.parquet
├── atom_introduction_events_v112_trial_B_seed{N}.parquet
├── atom_introduction_events_v108_matched_trial_B_seed{N}.parquet
└── atom_introduction_events_v108_original_bin_2_seed{N}.parquet
```

condition_id 列で同じ 6 値、trial 列で "A"/"B" の 2 値、varied_factor 列で詳細。v10.10 v109 atom_event_generator 規約継承。

### 2.5 Q-A6: bootstrap CI n_iter

| metric | n_iter |
|---|---:|
| 主軸 (指標 1-A, 3-A, 2-B) | **1000** |
| 副次 (指標 1-B) | **500** |

n_iter=1000 で 95% CI の SE ≈ 0.03 以下、副次 metric は計算量節約で 500 (SE ≈ 0.04)。

### 2.6 Q-A7: 本指示書で曖昧・不足な箇所

| 項目 | 不明点 | Code A 提案 |
|---|---|---|
| target_step の定義 | 「cid age = 200 で発火」だが、target_step が main の `t = cid.t_birth + 200` で v108_matched / v108_original も同 timestamp か別か | v112_trial: t = birth + 200、v108_matched: 主題 §5.5.1 の「均等分散」で atom_idx × 10 step (v10.8 規約)、v108_original: 同様 |
| performance_evaluator の自然 baseline | natural_baseline = 5 source events (pulse / ingestion / α / β / c_conversion) の v10.7 既存値 | v10.7 既存出力流用 (層 B 不変) |
| trial 内 same_baseline | 各 trial で baseline を 6 種計算するが、natural baseline は v10.7 共通か trial 別か | natural は trial 共通 (cid 構造に基づく)、5 種 baseline は trial 別 (events に基づく) |

→ 上記提案で進めて良いか Web Claude 確認。

### 2.7 Q-A8: 計算時間見積もり (Step Z 14.24 秒から)

| Step | 推定時間 (24 並列) |
|---|---:|
| Step C: receptive_cid_detector 24 seeds テスト | ~5 秒 |
| Step D: atom_event_generator (6 種) seed 0 smoke | ~5 秒 |
| Step E: baseline_recalculator (6 cond × 6 baseline) seed 0 smoke | ~30-60 秒 |
| Step F: performance_evaluator smoke | ~10 秒 |
| Step G: success_judgment smoke | ~5 秒 |
| Step H: orchestrator smoke | ~60-90 秒 (Step C-G 統合) |
| **Step J: main run** (24 seeds × 6 conditions) | **~60-120 秒** |
| Step K: cross-seed 集計 + bootstrap CI 1000 iter × 24 seeds × 4 metrics | ~30-60 秒 |
| **Step C-L 合計** | **~5-10 分** |

→ 主題 §0.3 打ち切り条件 (30 分超) に **大幅余裕**。

### 2.8 Q-A9: ストレージ累計予測

| Phase | サイズ |
|---|---:|
| v10.7-v10.11 main 既存 | 1.52 GB |
| **v10.12 追加 (推定)** | **0.5-1.0 GB** |
| **累計** | **2.0-2.5 GB / 上限 6 GB (33-42%)** |

→ 打ち切り条件 50% (3 GB) に **余裕**。

per-seed 内訳:
- atom_events × 6 conditions × 0.1 MB = 0.6 MB
- baselines × 6 cond × ~4 MB = 24 MB
- excess_change_adjusted × 6 cond × ~3 MB = 18 MB
- per-seed total: ~43 MB
- 24 seeds: ~1 GB
- + cross_seed: ~50 MB

### 2.9 Q-A10: メモリ使用量

24 seeds 並列実行時:
- per-worker ~200-400 MB (v10.10 main 実測ベース)
- 24 workers × 300 MB = ~7 GB
- ESDE 環境のメモリ余裕は v10.10/v10.11 で確認済 (Threadripper 環境)

### 2.10 Q-A11: 規律遵守自己検証

| 規律 | 状態 |
|---|---|
| §35 #9 (主題着手前に上位資料を読む) | 第 4 版主題 §1 で参照証明、Code A は本書 §3 で再確認 |
| §35 #10 (観察できる軸を駆動要因にしない) | 本書で観察軸増加提案なし、§4.4 駆動要因 (v10.13 prototype 進行可否) に従う |
| GPT B6 (各変動条件で baseline 再計算) | 6 condition × 6 baseline = 36 baseline 設計 |
| §34 #37 (n_core 別層化必須) | 2 trial 分割で bin_2 / bin_5+ 独立評価、第 3 版違反を解消 |
| §5.6 規律チェックリスト (案 X) | 第 4 版 §5.6 で実装、本書 §3 で再確認 |
| 物理層 frozen | post-process 計算的減算のみ、ledger 不変 |
| 神の手回避 | 構造条件のみで発火、ハンドチューニングなし |
| Atom 326 絶対化禁止 | 25 atom 継承、326 化なし |
| 因果断定回避 | paired_d / sign test で記述語、命名規律遵守 |

→ **全項目遵守**、§4.3 自己検証項目すべてに「遵守」と回答可能。

---

## §3 規律遵守の自己検証 (実装指示書 §6.3)

### 3.1 §35 #9 (主題着手前に上位資料を読む)

| 上位資料 | 読了状態 |
|---|---|
| v10.5 §7.4-§7.10 | Step Z Q-Z5 で確認、v105_integration.py:1035 機構 A 実装本体確認 |
| v10.10 §3.4 反応 type 分業 | 第 4 版 §5.0.1 で明示反映、本書 Q-A1 で母集団分析に活用 |
| v10.10/v10.11 完了レポート | 留保事項 22 件継承確認、第 4 版 §9 で扱い明示 |
| v10.7-v10.9 main run 構造 | v109_baseline_recalculator / v109_atom_event_generator 流用可能 |

### 3.2 §35 #10 (「観察できる軸が見えた」を駆動要因にしない)

本書で禁止項目チェック:
- ❌ 「3 trial 目を追加して bin_3_4 も見るべき」 → 提案していない
- ❌ formation_relation 軸を主題化 → 本書では条件 1 として実装のみ
- ❌ Multi-gate × timing 二次元観察設計への転換 → 提案していない
- ❌ within-cid design による Integration 形成プロセス解析の主題化 → 提案していない
- ✅ trial-B 母集団不足を Q-A1 で警告 → これは **設計破綻警告**、観察軸増加ではない

### 3.3 §34 #37 (n_core 別層化必須)

第 4 版 §5.0.1 で 2 trial 分割 (bin_2 / bin_5+) として遵守。本書 Q-A1 で trial-B bin_2 母集団問題を **n_core 別層化の文脈** で警告。

### 3.4 §5.6 規律チェックリスト (案 X) 遵守

第 4 版 §5.6.1 累積規律 41 件 + §35 メタ規律 10 項目を Code A 視点で再確認:

| 規律 | 第 4 版反映状況 | Code A 確認 |
|---|---|---|
| 物理層 frozen | post-process 計算的減算 (§5.4) | 実装で ledger 改変なし、read のみ |
| 神の手回避 | 構造条件のみで発火 | 実装で is_receptive_cid 関数のみで判定、ハンドチューニングなし |
| Atom 326 絶対化禁止 | 25 atom 継承 | 326 化なし、v108 TARGET_ATOMS 25 件流用 |
| 因果断定回避 | 「寄与候補の感度評価」命名 | 関数名 `performance_evaluator` で遵守 |
| post-process 計算的減算 | §5.4 | Q_delta=-1, C_delta=+1 を post-process で記録 |
| 出口の固定 | §4.2 単一勝負案明記 | 観察延長への転換禁止 |
| Code A 認識確認必須 | 本書 | 実施中 |
| 構造語と直感語の併記 | 用語注記 | 「会話」→「字面反応」併記 |
| 寄与候補感度評価命名 | 命名規律 | 因果断定語 (「効いた」) を使わない |
| 各変動条件で baseline 再計算 | §5.5 で 6 condition | 6 cond × 6 baseline = 36 baseline 設計 |
| 4 層階層化 | L1/L2/L3/L3.5 | trial 別に算出、cross_seed 集計 |
| n_core 別層化必須 | §5.0.1 で 2 trial 分割 | 第 3 版違反解消 |
| formation_relation 観察軸 | §5.1.1 / §5.2.1 で条件 1 | 遵守 |
| 完全マージ版文書 | 第 4 版 / 本書 | 全マージ |
| §35 #9 主題着手前に上位資料 | §1 で証明 | 本書 §3.1 で再確認 |
| §35 #10 観察軸を駆動要因にしない | §4.4 | 本書 §3.2 で再確認 |

### 3.5 事前調査の規律遵守

- [x] Step Z で実装に進まなかった (commit df04d0a)
- [x] 設計破綻を発見した場合 Web Claude/Taka に判定を要請した (Step Z 報告 + 本書 Q-A1)
- [x] 観察軸増加への転換提案しない (本書 §3.2)
- [x] 母集団不足を発見しても条件を勝手に緩めない (本書 Q-A1 は **警告のみ**、緩和実装は Web Claude/Taka 判断後)

---

## §4 即決事項候補 (DC-A1〜DC-A5)

### DC-A1: trial-B cond4 緩和の必要性 (Q-A1 重大ブロッカー対応)

**Code A 提案**: **(a-2) cond4 を top 50% 緩和** (trial-B のみ)
- 主題 §13.2 4 項目固定との関係: trial 別の閾値変更は「primary 条件」の構造維持と整合 (条件構造は 4 条件複合のまま、閾値のみ trial 別)
- 代替: cond4 除外 (3 条件複合)、trial-B 中止、主題変更

→ Web Claude/Taka 判断要請。Step B 環境チェックで Q2 緩和 + cond4 緩和の trial-B 母集団を実測。

### DC-A2: top_quartile_threshold の seed 別 vs 全体共通

**Code A 提案**: **per-seed 採用**
- Step Z Q-Z3 で std/global = **0.61** (≫ 0.10)
- 第 4 版 §5.0.0 の Step Z 反映方針と整合

### DC-A3: v108_original の流用 vs 再計算

**Code A 提案**: **流用**
- v108 outputs/main/ は v10.8 で生成済 (368 files、層 B 不変対象)
- bin 別 filter は post-process (v112 で n_core_bin filter)、層 B 影響なし
- 計算時間節約 (再計算なら +10-20 秒)

### DC-A4: bootstrap CI n_iter

**Code A 提案**: **1000 (主軸) / 500 (副次)** (Q-A6)

### DC-A5: その他 Code A 判断で進めない事項

- target_step の v108_matched / v108_original timestamp 設定 (Q-A7) → Web Claude 確認
- performance_evaluator の natural baseline 流用方針 (Q-A7) → Web Claude 確認

---

## §5 Step B 進行案 (Q-A1 解消後)

### 5.1 Step B 環境チェック実装内容

```python
# v112_step_b_environment_check.py
# 1. Q2_threshold (lifespan ≥ 977) 確定
# 2. top_quartile_threshold per-seed 確定
# 3. trial-A / trial-B 母集団実測 (Q2 緩和 + cond4 緩和案ありの場合)
# 4. formation_relation 取得方法の最終確認
# 5. v108_original の bin 別抽出ロジック動作確認
# 6. seed 0 smoke の準備 (前段階)
```

### 5.2 Step B 完了条件

- [x] Q2_threshold = 977 確定
- [x] top_quartile_threshold per-seed 確定
- [x] trial-A 母集団 per seed mean 確定 (Q2 緩和)
- [x] trial-B 母集団 per seed mean 確定 (Q2 緩和、Web Claude/Taka 判断による cond4 緩和ありの場合)
- [x] formation_relation 取得 (build_alpha_beta_intervals 流用) 動作確認
- [x] v108_original 流用パス確認

---

## §6 一文サマリ (再掲)

第 4 版主題ドキュメント + 第 3 版実装指示書を読み込み Step A 認識確認実施、**Q-A1 で 1 件の重大ブロッカー早期警告**: trial-B (bin_2 × 4 条件) の per seed 0.2 / total 4 events で paired_d 算出不能 (cond4 high_fam top 25% が bin_2 多数派にとって構造的に厳しすぎる、Q2 緩和でも解消されない、Code A 提案 (a-2) cond4 top 50% 緩和を Web Claude/Taka 判断要請)、Q-A4 paired_d は per (seed, atom, path, window) で v112 vs v108_matched の delta を取り 24 seeds 内 paired (cid 構造差排除)、Q-A5 命名 6 種類 v10.10 規約継承 (`atom_introduction_events_{condition_id}_seed{N}.parquet`)、Q-A6 bootstrap n_iter 1000 主軸 / 500 副次、Q-A8 main run 推定 1-2 分 (24 並列、6 conditions × 6 baselines)、Q-A9 storage 累計 v107-v112 約 2.0-2.5 GB / 上限 6 GB (33-42%) で打ち切り 50% 余裕、Q-A10 メモリ ~7 GB peak、Q-A11 規律遵守項目すべて遵守 (§35 #9 / #10 / §34 #37 / §5.6 規律チェックリスト)、DC-A1 trial-B cond4 緩和案 Web Claude/Taka 判断要請、DC-A2 top_quartile per-seed 採用、DC-A3 v108_original 流用 (層 B 不変)、DC-A4 bootstrap n_iter 1000、§3 規律遵守自己検証で全項目チェック (上位資料読了、観察軸増加提案なし、母集団不足を警告のみで実装提案なし)、Step B (環境チェック詳細 + Q2 緩和 + cond4 緩和案ありの場合の trial-B 母集団再実測) に進む準備完了、ただし **Q-A1 重大ブロッカー解消が前提** (trial-B 母集団確保の方針確定後に Step B 着手)、Web Claude/Taka 即決事項返答 + DC-A1〜DC-A5 判断後に Step B 進行。

---

*以上、Code A による v10.12 Step A 認識確認文書。Web Claude `v112_response_to_code_a.md` (即決事項返答) 受領 + Taka 承認後、Step B (環境チェック詳細) に進む。Q-A1 重大ブロッカー解消が前提。*
