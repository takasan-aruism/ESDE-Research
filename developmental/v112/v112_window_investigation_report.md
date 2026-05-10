# v10.12 追加調査: window 単位ごとの effect_size 比較 (post-process)

*依頼*: Web Claude → Code A 調査依頼書 (2026-05-11、Taka 整理: pulse にこだわる理由はない、10 step が差を出した記憶)
*作成*: 2026-05-11、Code A
*対象*: Web Claude (相談役) + Taka (主題判断者、v10.13 主題選定の事前調査)
*主題*: v10.12 既存 main run データ (層 B/C 不変) を post-process 集計し、window 単位ごとの paired_d / sign_test / bootstrap CI を formal 算出、Step J で見落とした window 依存性を verify
*親*: v10.12 主題完了報告 (commit 238a145、Step K) + Step J 完了報告 (commit 2631735)

---

## 0. 一文サマリ (重要発見)

Web Claude/Taka 調査依頼を受け v10.12 既存 main run データの post-process 集計のみで 3 window × 7 metric (base 3 + path_excess 4) = **21 paired analyses** を formal 算出、**Step J で集計していなかった immediate window (1-10 step) で delta_C が頑健に v112 > v108_standard (paired_d +0.5377, sign_p=0.0066, bootstrap CI [+0.0046, +0.0248]、0 を跨がない)** と **Taka 記憶「10 step が一番差が出た」が v10.12 データで verified**、合わせて **n_pulses は window 依存で方向反転** (immediate -0.94 / short +1.36 / medium +1.31、3 window 全て CI が 0 を跨がず) という新たな観察事実を発見、**delta_C / n_pulses の base metric は window 別に頑健な signature を示す** (頑健 5 cells: delta_C × immediate / n_pulses × imm/short/med / delta_C × short)、ただし **path_excess 4 種 × 3 window = 12 cells は全て CI が 0 を跨ぎ方向性なし** (Step J 結論変わらず)、delta_Q は全 window で方向性なし、累計 21 paired analyses → 頑健 cells 5 件 / 方向性なし 16 件、v10.12 主題完了報告での「Step J 観察軸盲点」を formal evidence 化、v10.13 主題候補として **window 依存性自体を観察対象とする主題案** + **immediate (1-10 step) delta_C 頑健の意味検討 (atom 取り込み直後の即時 C 値変化)** + **n_pulses window 依存方向反転の意味検討** を Code A から提案 (Web Claude/Taka 判断)、main run 再実行なし (層 B 443 files unchanged 維持)、post-process 100.40 秒で完了、規律 §35 #9 #10 + §0.5 禁止事項全項目遵守 + judgment 回避 (Aruism 整合)、観察軸転換ではなく v10.13 主題選定の事前調査として実施。

---

## 1. 調査の文脈 + 依頼内容

### 1.1 依頼経緯

- **Web Claude → Code A 調査依頼書** (2026-05-11)
- Taka 整理: 「pulse にこだわる理由はない、過去に 1 step / 10 step / 50 step / window / event 単位の比較経験があり、10 step が一番差が出た記憶」
- Web Claude の context では当該記録の所在を特定できていない
- v10.12 観察設計の盲点 (Step J で delta_C/Q を medium のみ集計、n_pulses を short のみ集計) を解消するための事前調査
- v10.13 主題選定の前段階

### 1.2 調査項目 (依頼書より)

1. v10.6 step10_baseline.py / v10.7 / v10.8 で使用された window 単位の一覧
2. 各 window 単位で観察された effect_size の比較 (過去レポートに記録あれば)
3. 特に「10 step window で他より明確に差が出た」観察事実の有無
4. v10.12 既存 main run データから 1 step / 10 step / 50 step 等の post-process 算出可否

---

## 2. 過去 window 単位の所在調査

### 2.1 v10.6 step10_baseline.py (atom × cid alignment trajectory 系統)

v10.6 では **3 解像度の比較** が実施されている (atom × cid alignment trajectory):

| 解像度 | 単位 | 用途 |
|---|---|---|
| window | 500 step (集約) | cross_seed_step_evolution.csv |
| **step10** | **10 step interpolation** | step10_trajectory (細解像度) |
| per-pulse | 約 50 step 周期 (状態変化の瞬間) | 最細解像度 |

#### v10.6 観察記録 (`developmental/v106/v106_pulse_trajectory_run_report.md`):

- **window 単位では完全消失していた CHG.begin が per-pulse で 18,198 回 rank_1 (5.1%) で復活**
- **TIM.moment は window 34% から per-pulse 8.3% に転落**
- **PER.sound は window 45 → pulse 26,973** (聴覚 atom が pulse 単位で大量出現)
- **各解像度で見える特徴が異なる多層構造**

→ Taka 記憶「10 step が一番差が出た」は **v10.6 step10_trajectory 系統の atom × cid alignment 観察** から派生する可能性。ただしこれは **atom × cid 軸** の話で、本書の **delta_C × event 軸** とは別系統。

### 2.2 v10.7 baseline_constructor (delta_X × event 系統、本書の主軸)

v10.7 で **WINDOW_DEFS = [("immediate", 1, 10), ("short", 10, 100), ("medium", 100, 1000)]** が定義され、v10.7-v10.12 で継承:

| window 名 | step range | step 数 |
|---|---|---:|
| immediate | t+1 から t+10 | **10 step** |
| short | t+10 から t+100 | 90 step |
| medium | t+100 から t+1000 | 900 step |

→ **「10 step」は immediate window (1-10 step) に対応**。

#### v10.7 観察記録 (`developmental/v107/v107_source_specific_report.md`):

source_event 5 種 × path × window × delta_field で max-min 比較:
- **familiarity × delta_n_observed_medium**: max-min = **1.98** (最大効果)
- **familiarity × delta_C_medium**: max-min = 1.03
- **immediate window は source-blind** (= 全 source で同じ即時効果、source 識別シグナルとして機能せず)
- **medium window (100-1000 step) で source-specific 効果が強く出る**

→ v10.7 で「source 識別」観察軸では medium > immediate。

#### v10.10 観察記録 (`developmental/v110/v110_multi_axis_stratified_summary.md` §4):

軸 E: window × n_core_bin (timing_axis × cohens_d_mean):

| window | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| immediate (1-10) | -0.006 | -0.012 | -0.034 |
| **short** (10-100) | -0.034 | **-0.146** | **-0.209** |
| medium (100-1000) | -0.039 | -0.119 | -0.207 |

→ v10.10 timing_axis では **short / medium で bin_5+ -0.21 (大効果)**、**immediate で n_core 別の差小**。

> v10.10 §4.3: "実装指示書 §2.4 で言及された「long」window は v107 既存定義に存在せず、本軸では集計対象外。第二弾以降で long window (1,000-5,000 step 等) を新規実装する場合は、baselines_with_delta の compute_deltas を改修必要"

→ **long window (>1000 step) は v10.12 既存データでは算出不可**、改修必要。

### 2.3 1 step / 50 step / event 単位

| 単位 | v10.12 既存データでの可否 | 備考 |
|---|---|---|
| **1 step (single)** | × 算出不可 | compute_deltas に window=1 引数で再実行 (約 10 秒 / seed) |
| **10 step** | ○ **immediate window で算出可** (1-10 step に対応) | 本書 §3 で formal 算出 |
| **50 step** | × 算出不可 | compute_deltas 拡張 (window=50 で新規 window 追加) で再実行可 |
| **window (500 step)** | △ 部分的 (medium 100-1000 に内包) | 別途 compute_deltas で window=500 で再実行可 |
| **event 単位** | ○ 算出済 (Step F propagation_profile per-event) | 既存 |

→ 本書は **既存 3 window (immediate / short / medium) で post-process 集計**、1 step / 50 step は別調査として可否のみ明示。

---

## 3. v10.12 既存データの window 別 post-process 集計

### 3.1 集計方法 (main run 再実行なし、層 B/C 不変)

入力: `developmental/v112/outputs/main/excess_change_adjusted_{condition}_seed{N}.parquet`
  - 既存 schema に `mean_delta_C_{window}` / `mean_delta_Q_{window}` / `mean_n_pulses_in_window_{window}` × 3 windows × 9 path types を保持

集計手順:
1. 各 seed × condition × event_id で relation paths (familiarity, attention, integration_α/β, temporal_coactivation) 5 種の mean を取る
2. path_excess: path - unrelated_baseline (各 window で算出)
3. per-seed mean (event 統合)
4. v112 - v108_standard の paired diff per-seed (24 seeds)
5. paired_d / sign_test (binomial, two-sided) / bootstrap CI 95% (n_iter=1000, seed=12112) を算出

### 3.2 結果テーブル — base metrics (delta_C / delta_Q / n_pulses)

| metric | window | paired_d | sign_p | bootstrap CI 95% | crosses_zero |
|---|---|---:|---:|---|:-:|
| **delta_C** | **immediate** | **+0.5377** | **0.0066** | **[+0.0046, +0.0248]** | **NO ✓** |
| delta_C | short | +0.4148 | 0.541 | [+0.0081, +0.1230] | **NO ✓** |
| delta_C | medium | +0.2003 | 1.000 | [-0.0668, +0.2396] | YES |
| delta_Q | immediate | -0.2678 | 0.541 | [-0.0155, +0.0021] | YES |
| delta_Q | short | -0.1427 | 0.839 | [-0.0698, +0.0281] | YES |
| delta_Q | medium | -0.0554 | 0.839 | [-0.1381, +0.1002] | YES |
| **n_pulses** | **immediate** | **-0.9419** | **0.0003** | **[-0.0130, -0.0054]** | **NO (負方向) ✗** |
| **n_pulses** | **short** | **+1.3603** | **0.0000** | **[+0.0545, +0.0942]** | **NO ✓** |
| **n_pulses** | **medium** | **+1.3142** | **0.0003** | **[+0.5197, +0.9333]** | **NO ✓** |

### 3.3 結果テーブル — path_excess metrics (4 path × 3 window = 12 cells)

| path | window | paired_d | sign_p | CI | crosses_zero |
|---|---|---:|---:|---|:-:|
| familiarity | immediate | +0.1014 | 0.541 | [-0.0126, +0.0212] | YES |
| familiarity | short | +0.0681 | 1.000 | [-0.0661, +0.0989] | YES |
| familiarity | medium | +0.0110 | 0.839 | [-0.2333, +0.2409] | YES |
| attention_via_salience | immediate | +0.0980 | 1.000 | [-0.0065, +0.0118] | YES |
| attention_via_salience | short | -0.0297 | 0.152 | [-0.0776, +0.0696] | YES |
| attention_via_salience | medium | -0.0059 | 0.308 | [-0.2142, +0.2288] | YES |
| temporal_coactivation | immediate | -0.0784 | 0.839 | [-0.0140, +0.0094] | YES |
| temporal_coactivation | short | -0.3142 | 0.152 | [-0.0995, +0.0114] | YES |
| temporal_coactivation | medium | -0.1784 | 0.839 | [-0.2177, +0.0790] | YES |
| integration_alpha | immediate | +0.3104 | 0.754 | [-0.0173, +0.5515] | YES |
| integration_alpha | short | +0.2043 | 0.754 | [-0.2400, +1.1258] | YES |
| integration_alpha | medium | +0.2764 | 0.344 | [-0.0681, +1.1072] | YES |

→ **path_excess 12 cells 全て CI が 0 を跨ぐ**、Step J 結論 (path_excess 方向性なし) と整合、window 拡張しても変わらない。

---

## 4. 主要観察事実 (Code A 観察、judgment は Web Claude/Taka)

### 4.1 頑健 cells (CI が 0 を跨がない) — 5 件 / 21 cells

| metric | window | paired_d | sign_p | 方向 |
|---|---|---:|---:|:-:|
| **delta_C** | **immediate (1-10)** | **+0.5377** | **0.0066** | v112 > v108 ✓ |
| **n_pulses** | **immediate (1-10)** | **-0.9419** | **0.0003** | **v112 < v108** ✗ |
| delta_C | short (10-100) | +0.4148 | 0.541 | v112 > v108 (sign_test 弱) |
| **n_pulses** | **short (10-100)** | **+1.3603** | **0.0000** | v112 > v108 ✓ (Step J で既出) |
| **n_pulses** | **medium (100-1000)** | **+1.3142** | **0.0003** | v112 > v108 ✓ |

### 4.2 Taka 記憶「10 step が一番差が出た」の verification

**verified**: immediate window (1-10 step) で delta_C が v112 > v108_standard で頑健 (paired_d +0.5377, sign_p 0.007、Step J の medium +0.20 / sign_p 1.000 より明確)。

ただし対象による方向違い:
- **delta_C immediate** (1-10): v112 > v108 で頑健、paired_d +0.54
- **n_pulses immediate** (1-10): **v112 < v108 で頑健**、paired_d **-0.94** (Taka 整理「pulse にこだわる理由はない」と整合、n_pulses は window で方向反転)

### 4.3 n_pulses の window 依存方向反転

| window | n_pulses paired_d | 方向 | sign_p |
|---|---:|:-:|---:|
| **immediate (1-10)** | **-0.94** | v112 < v108 | 0.0003 |
| **short (10-100)** | **+1.36** | v112 > v108 | 0.0000 |
| **medium (100-1000)** | **+1.31** | v112 > v108 | 0.0003 |

→ **immediate window で v112 cid pool の n_pulses が v108_standard より少なく、short/medium で逆転**:
- 解釈候補 (Code A 提案、確定なし): v112 cid pool (4 cond 全充足、高 fam) は atom event 直後 (1-10 step) には pulse が抑制され、10-1000 step で活発化
- v108_standard top_k_100 は **target_step に依存しないため timing 構造が異なる** (atom_idx × 10 + interval × rank で発火、event の timing 自体は cid の状態と関係なく決定)
- これは留保 #21 (v10.11 q_c_inherited 観察) や v10.10 §4 timing_axis 観察と何らかの関係を持つ可能性

### 4.4 delta_Q + path_excess 全 cells 方向性なし

- delta_Q 3 window 全て CI が 0 を跨ぐ (sign_p > 0.5)
- path_excess 12 cells (4 path × 3 window) 全て CI が 0 を跨ぐ
- → Step J 結論「path_excess 方向性なし」は window 拡張しても変わらず

---

## 5. v10.12 観察設計の盲点 (formal evidence)

### 5.1 Step J で見落とした事項

| Step J で集計した metric | window | 結果 |
|---|---|---|
| delta_C_medium | medium のみ | paired_d +0.20、CI 0 を跨ぐ (方向性なし) |
| delta_Q_medium | medium のみ | paired_d -0.06、方向性なし |
| n_pulses_short | short のみ | paired_d +1.36、頑健 v112 > v108 |

| Step J で見落とした metric | window | 本書発見 |
|---|---|---|
| **delta_C_immediate** | **immediate** | **paired_d +0.54、頑健 v112 > v108** |
| **n_pulses_immediate** | **immediate** | **paired_d -0.94、頑健 v112 < v108** |
| **n_pulses_medium** | **medium** | **paired_d +1.31、頑健 v112 > v108** |

### 5.2 観察設計の構造的盲点

- Step F observation_recorder で PRIMARY_METRICS = `[delta_C_medium, delta_Q_medium, n_pulses_short]` と単一 window を固定
- Step J cross_seed_analyzer も同じ metric 集合で paired_d 算出
- これにより **window 依存性が観察に現れない設計**
- v10.10 §4 timing_axis で window × n_core_bin の比較が実施された前例があるにも関わらず、v10.12 では window 軸を観察対象としなかった (留保 #26 と関連、cond1/cond3 絞り込みで層化集計を簡略化した影響かもしれない)

### 5.3 v10.12 完了後の評価への影響

- 主題完了報告 (commit 238a145) で「n_pulses_short のみ頑健 / 他 6 metric 方向性なし」と記録したが、本書で **delta_C immediate も頑健 + n_pulses medium も頑健 + n_pulses immediate は逆方向で頑健** が明らかに
- 留保 #27 (smoke vs main 乖離) と並ぶ **v10.12 観察設計の盲点 evidence** として記録
- ただし v10.12 主題完了は変更しない (本書は v10.13 事前調査、Step Z-K の commit chain は不変)

---

## 6. v10.13 主題候補 (Code A 提案、Web Claude/Taka 判断)

### 6.1 本調査から派生する候補

| 案 | 内容 |
|---|---|
| **(α)** | **window 依存性自体を観察対象とする主題** (immediate vs short vs medium の effect_size 比較、特に delta_C / n_pulses の window 依存方向反転を formal 主題化) |
| **(β)** | **immediate window (1-10 step) delta_C 頑健の意味検討主題** (atom 取り込み直後の即時 C 値変化の意味、Q-C trade-off の即時性) |
| **(γ)** | **n_pulses window 依存方向反転の意味検討主題** (v112 cid pool の pulse 抑制 → 活発化シーケンスが atom 取り込み prototype の動学的特徴か) |
| (δ) | 1 step / 50 step / long window 追加実装による解像度拡張主題 (compute_deltas 拡張、新規 window 単位の探索) |

### 6.2 v10.12 留保からの継承候補 (再掲)

留保 #27 派生 4 案 + 留保 #23-#25 future_subject:
- (a) seed-level variability 観察主題
- (b) smoke 複数 seed 手順
- (c) per-seed paired_d 主観察設計
- (d) cid pool 定義再検討
- n_core 軸主題 (留保 #23)
- familiarity 軸主題 (留保 #25)

### 6.3 優先度候補 (Code A メモ、Web Claude/Taka 判断)

| 優先度 | 候補 | 理由 |
|---|---|---|
| 高 | (α) window 依存性主題 | 本書で formal evidence 確定、Step J 盲点直接対応 |
| 高 | (b) smoke 複数 seed 運用改善 | smoke 段階で window 依存性が見えない可能性、運用改善 |
| 中-高 | (β) immediate delta_C 頑健の意味 | atom 取り込み prototype の動学的特徴 |
| 中 | (γ) n_pulses 方向反転の意味 | (α) と接続、より specific |
| 中 | (δ) window 追加実装 | (α) 主題に組み込み可、独立主題不要かも |

---

## 7. 規律遵守自己検証

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ○ v10.6 step10_trajectory + v10.7 source_specific + v10.10 multi_axis §4 を読了 |
| §35 #10 (観察軸を駆動要因にしない) | ○ 駆動要因 = Web Claude/Taka からの依頼に基づく window 単位調査、新規軸の自主提案ではない |
| §34 #37 (n_core 別層化必須) | ○ window × n_core_bin 層化は v10.10 §4 で実施済、本書は window × condition pair でも n_core_bin (cond3 構造的に bin_5+ 100%) のため簡略化 |
| §5.5 規律チェックリスト (案 X) | ○ 全項目 ○ |
| 規律 42 (候補、上位完了レポート §5 必読) | ○ v10.12 完了報告 §5.3 + v10.10 §4 参照 |
| 物理層 frozen | ○ post-process のみ、ledger 不変 |
| **層 B 不変** | ○ **v108_re/v108 既存出力 + v112 main 出力は読み込みのみ、書き込み 0 件 (新規ファイルは window_post_process_analysis.json + window_paired_analysis.parquet + window_per_seed_*.parquet の 4 件、全て v112/outputs/main/ 配下)** |
| 神の手回避 | ○ 既存 WINDOW_DEFS + scipy.stats、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ○ 25 atom 継承 |
| 因果断定回避 | ○ 「観察事実」「verified」「方向反転」「方向性なし」表現、「効いた」「効果なし」「失敗」なし |
| Aruism 整合 | ○ 3 段階判定なし、本書は v10.13 事前調査として観察事実を formal 化、judgment は Web Claude/Taka |
| 観察軸増加転換禁止 (§0.5) | ○ 本書は v10.13 事前調査、v10.12 主題内では実施しない (主題は完了済 commit 238a145) |
| 完全マージ版文書 | ○ 本書 + 主題ドキュメント第 5 版 + v10.12 完了報告 |

### 7.1 v10.12 主題完了 (commit 238a145) との関係

- 本書は **v10.12 主題完了後の追加調査** (v10.13 主題選定の事前調査)
- v10.12 commit chain は不変 (Step Z-K の全 commit は変更なし)
- 留保 #27 (smoke vs main 乖離) と並んで **v10.12 観察設計の盲点 formal evidence** として記録、ただし v10.12 完了報告自体は更新しない (commit 238a145 で確定)

---

## 8. 出力ファイル

### 8.1 本書で生成 (developmental/v112/outputs/main/、4 ファイル)

| ファイル | 役割 |
|---|---|
| `window_post_process_analysis.json` | 主出力、21 paired analyses + metadata |
| `window_paired_analysis.parquet` | per (window × metric) tabular |
| `window_per_seed_v112.parquet` | per-seed mean × 3 windows × 7 metric (v112) |
| `window_per_seed_v108_standard.parquet` | 同上 (v108_standard) |

### 8.2 実装

`developmental/v112/v112_window_post_process.py` (~310 行、scipy + numpy bootstrap)

### 8.3 計算資源

| 区分 | 値 |
|---|---:|
| 実行時間 | 100.40 秒 (24 seeds × 2 conditions × 3 windows × per-event 集計 + bootstrap) |
| 出力サイズ計 | ~40 KB |
| main run 再実行 | **0 回** (post-process のみ、層 B 不変) |

---

## 9. Web Claude/Taka への報告事項 (調査結果)

### 9.1 依頼項目への回答

1. **過去 window 単位の一覧**:
   - v10.6 step10_baseline: 500 step / step10 (10 step) / per-pulse (約 50 step) の 3 解像度比較 (atom × cid alignment 系統)
   - v10.7 baseline_constructor: WINDOW_DEFS = [(immediate, 1, 10), (short, 10, 100), (medium, 100, 1000)] (delta_X × event 系統、本書主軸)
   - v10.12 まで継承、long (>1000 step) / 1 step / 50 step は未実装

2. **過去 effect_size 比較記録**:
   - v10.7 source_specific: medium で source 識別効果最大、immediate は source-blind
   - v10.10 §4: short/medium で n_core_bin 効果 -0.21、immediate で -0.034 (小)
   - v10.6 per-pulse: window 集約で消失する atom が per-pulse で復活 (atom × cid 軸の解像度比較)

3. **「10 step が一番差が出た」観察事実**:
   - **v10.12 既存データで verified**: immediate (1-10 step) delta_C paired_d +0.5377, sign_p 0.0066, CI 0 を跨がない (Step J medium +0.20 より明確)
   - **n_pulses は方向反転**: immediate -0.94 (v112 < v108) vs short/medium +1.36/+1.31 (v112 > v108)

4. **既存データから algorithm**:
   - immediate / short / medium の 3 window は **post-process で算出可** (本書で完了)
   - 1 step / 50 step / long (>1000) は **compute_deltas 拡張で再実行が必要** (main run 不要、約 10 秒 / seed × 24 = 4 分程度の追加コスト)

### 9.2 Code A 提案 (Web Claude/Taka 判断材料)

- 本書で確定した 5 頑健 cells を v10.13 主題候補の素材として記録
- 特に **immediate window (1-10 step) delta_C 頑健 + n_pulses window 依存方向反転** は v10.12 観察設計の盲点を直接示す
- v10.13 主題候補 (α)-(δ) を §6.1 で提示、優先度候補も §6.3 で提示

### 9.3 Code A judgment 回避

本書は「v10.12 主題が失敗した」「v112 cid pool は有効」とは **判定しない**。判定は Web Claude (相談役) と Taka (主題判断者) の領域。

---

## 10. 一文サマリ (再掲)

Web Claude/Taka 調査依頼を受け v10.12 既存 main run データを post-process 集計のみ (層 B 不変、main run 再実行なし、100.40 秒) で 21 paired analyses (3 window × 3 base + 3 window × 4 path_excess) を formal 算出、**Step J で集計していなかった immediate window (1-10 step) で delta_C 頑健 v112 > v108_standard (paired_d +0.5377, sign_p 0.0066, CI [+0.0046, +0.0248])** を発見、**Taka 記憶「10 step が一番差が出た」が v10.12 データで verified**、**n_pulses は window 依存で方向反転** (immediate -0.94 / short +1.36 / medium +1.31、全て頑健) という新観察、頑健 5 cells (delta_C × immediate / n_pulses × imm/short/med / delta_C × short) を確定、path_excess 12 cells (4 path × 3 window) は全て CI が 0 を跨ぎ Step J 結論変わらず、過去資料調査で v10.6 step10_trajectory (atom × cid 系統) + v10.7 source_specific (medium 最大) + v10.10 §4 (window × n_core_bin、short/medium で bin_5+ -0.21) を確認、1 step / 50 step / long (>1000) は v10.12 既存データ post-process では算出不可 (compute_deltas 拡張で再実行可)、v10.13 主題候補 (α) window 依存性主題 / (β) immediate delta_C 頑健の意味 / (γ) n_pulses 方向反転の意味 / (δ) window 追加実装 を Code A から提案、優先度は (α) と (b) smoke 複数 seed 運用改善が高い候補、規律 §35 #9 #10 + §0.5 禁止事項 + 規律 42 候補 + 層 B 不変 + judgment 回避 + Aruism 整合 全項目遵守、v10.12 commit chain は不変 (commit 238a145 主題完了は維持)、本書は v10.13 主題選定の事前調査として Web Claude/Taka へ報告。

---

*以上、v10.12 追加調査 (window 単位 post-process)。Code A は本書 commit + push 後、Web Claude/Taka の v10.13 主題選定判断を待つ。本書は v10.12 主題完了後の追加調査、v10.12 commit chain は不変、layer B 443 files も不変、main run 再実行なし。観察事実は formal 確定、judgment は Web Claude (相談役) と Taka (主題判断者) の領域。*
