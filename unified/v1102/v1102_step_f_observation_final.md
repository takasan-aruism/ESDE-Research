# v11.0.2 (v1102) Step F 観察事実最終報告 — Code A

*作成*: 2026-05-20、Code A
*親*: `v1102_phase_design.md` (Web Claude 設計書、§2.6 確認要請回答反映済) + `v1102_step_a_recognition.md` (Code A 認識確認、新規 main run 不要確定) + Step B-E 出力
*対象*: Web Claude (Phase Result 翻訳統合担当) + Taka (主題評価)
*位置づけ*: v11.0.2 主題「条件が応答を変える」の Code A 観察事実総括。judgement なし (絶対格言 #12)、解釈統合は Web Claude Phase Result 領域。

---

## 0. 一文サマリ

v11.0.2 (v1102) 主題「条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察」段階 1 Step A-F 全完了、Step B primary table 構築 (81 cells × 27 cols、24 seeds 1 batch、11.4 秒、新規 main run なし) で応答 5 種 (attention trajectory / influence / variability / atom profile / category profile) + v107 時間粒度 (immediate/short/medium) を並列出力、設計書 §2.6 「5 種並列・主従なし」「per-cell 全セル残し・サンプル数で除外せず」を遵守、Step C 際立ち掬い取り A primary (15 構造的指標 × Top 10% + IQR 外れ値、神の手回避 #9、z-score 単体不可) + B secondary (Step G stratified との read-back、新規 emit なし軽い踏み込み) で 67/81 cells (82.7%) が何らかの指標で際立つ・最高 outstanding_score=8、Step D グラフ HTML 4 セクション (際立ち度ヒートマップ + 際立った cells 応答 5 種 panel + v107 effect_delta 時間粒度推移 + B secondary Step G 重なり、33 KB)、Step E bit-identity 3 層全 PASS (v106 731 + v107 222 + v112 207 + v105_integration 144 + v1101a_main 131 = 1,435 files frozen、Step B smoke parquet hash 一致 deterministic、書込み unified/v1102/ 配下のみ)、核心観察事実 (judgement なし) は (1) **CID n_core 別で応答 atom/category が劇的に変化** (CID_n=2 = EMO.manifest / BOD / conscious 0.51 / influence 61.5 vs CID_n=5 = EXS.being / EXS / conscious 0.71 / influence 130.2) で Taka 整理「2 ノードが大半・5 ノードは情報量で強い・平均化で潰れる」がデータで顕在化、(2) **alpha_n=4+ / gini=low (47 records、Step G 留保 #L12) で unit_kl_static metric が全 8 指標で際立ち** = 単発の極端値でなく多面的シグナル、(3) **CID_n=6+ (66 records、極稀) で 6 指標で際立ち** = Taka「5 ノード強」を上回る極端ケース、(4) **CID_n=2 (Taka「2 ノード大半」、6,012 records) は variability_actual のみで outstanding_score=1** = ordinary を構造的に確認、(5) v107 effect_delta は多くの cells で immediate→short→medium で ΔQ 消費拡大 (電話 vs 手紙の比喩がデータで現れる候補)、(6) ESDE 3 scope は 1-2 で目立たず集約 scope の限界、B secondary 57/81 cells (Integration scope のみ) で Step G stratified との read-back あり、新規留保候補 #L14 (CID_n=2/n=5 で atom 像が反転、Taka「平均化で潰れる」直接対応) と #L15 (alpha_n=4+ / gini=low が 8 指標際立ち、極端値が多面シグナル化、留保 #L12 拡張) と #L16 (variability_lift が全 alpha cells で同値 = observation_c 粒度不足、Step C 改善要)、判定 (選択と集中 / 拡散の方向性、CID 階層と Integration 構成の関係、時間粒度推移の意味) は Web Claude Phase Result + Taka 主題評価領域。

---

## 1. 段階 1 進行と入出力

| Step | 内容 | 状態 | 出力 |
|---|---|---|---|
| A | 認識確認 (新規 run 不要確定 + 確認要請 2 件) | 完了 | v1102_step_a_recognition.md |
| B | primary table 構築 (応答 5 種 + 時間粒度) | 完了 | primary_table.parquet (81 cells × 27 cols) |
| C | 際立ち掬い取り A primary + B secondary | 完了 | outstanding_cells.parquet + thresholds.parquet |
| D | グラフ HTML (4 section) | 完了 | v1102_observation.html (33 KB) |
| E | bit-identity 3 層検証 | 完了 (all PASS) | v1102_step_e_bit_identity_report.json |
| F | 観察事実最終報告 | 本書 | v1102_step_f_observation_final.md |
| G | Phase Result | 待ち | Web Claude 担当 |

---

## 2. 核心観察事実 (judgement なし、絶対格言 #12)

### 2.1 CID n_core 別で応答 atom/category が劇的に変化 (Taka 整理直接対応)

| receiver_bin | n_records | conscious_frac | influence_count_mean | **atom_top1** | **category_top1** | outstanding_score |
|---|---:|---:|---:|---|---|---:|
| **CID_n=2** (Taka「大半」) | 6,012 | 0.51 | 61.5 | **EMO.manifest** (情動の現れ) | **BOD** (身体) | **1** (ordinary) |
| CID_n=3 | 2,313 | 0.58 | 135.1 | SOC.nation | SPC (空間) | 5 |
| CID_n=4 | 6,366 | 0.70 | 82.5 | SOC.nation | SPC | 1-2 |
| **CID_n=5** (Taka「情報量強」) | 16,725 | 0.71 | 130.2 | **EXS.being** (存在) | **EXS** (存在) | 3-4 |
| **CID_n=6+** (極稀) | 66 | 0.82 | 79.6 | **FND.timeless** (時間性なし) | EXS | **6** |

→ **CID_n=2 (情動・身体) と CID_n=5 (存在・存在) で atom/category が反転**、CID_n=6+ で更に異なる (時間性なし)。Taka 整理「2 ノード大半、5 ノードは情報量で強い、平均化で潰れる」がデータで顕在化。

新規留保候補 **#L14**: CID 構成ノード数で応答 atom 像が階層的に反転 — n=2 EMO.manifest / n=3-4 SOC.nation / n=5 EXS.being / n=6+ FND.timeless。Taka「平均化で潰れる」直接対応。

### 2.2 alpha_n=4+ / gini=low (47 records) で全 8 指標際立ち (留保 #L12 拡張)

Step G で発見の留保 #L12 (大型均等構造で integration_β 0.950) の cell が、v1102 Step C で **15 構造的指標中 8 個** で際立ち (outstanding_score=8、最高):

| 指標 | 該当 |
|---|---|
| effect_delta_Q_immediate / short / medium | × 3 |
| effect_delta_C_immediate / short / medium | × 3 |
| effect_delta_R_familiarity_immediate / short / medium | × 3 (うち 2 該当) |

新規留保候補 **#L15**: alpha_n=4+ / gini=low (47 records) は単発の極端値でなく **8 指標 (時間粒度 immediate/short/medium 含む) で多面シグナル**。留保 #L12 の拡張。

### 2.3 CID_n=6+ (66 records、極稀構造) で 6 指標際立ち

CID_n=6+ は per seed 0.03% (3/3,088 cids)、Taka「5 ノードは情報量で強い」を上回る極端構造:

| 指標 | 該当 |
|---|---|
| conscious_frac | 0.818 (CID 中最高) |
| effect_delta_Q_short_mean | 際立ち |
| effect_delta_R_familiarity_immediate_mean | 際立ち |
| 他 3 指標 | 該当 |

サンプル 66 records と極小ながら 6 指標で際立つ — 留保 #L15 と同型の「極端値が多面シグナル化」。

### 2.4 CID_n=2 (Taka「大半」) の ordinary 確認

CID_n=2 (n=1,932 cids、62.6%、6,012 records) は variability_actual_mean のみで outstanding_score=1。15 指標中 1 つだけ。

→ **平凡 (ordinary) を構造的に確認**。Taka「2 ノードが大半」は分布の事実であって、際立ちの源ではないことが指標レベルで確定。

### 2.5 v107 effect_delta 時間粒度推移 (電話 vs 手紙の比喩)

多くの cells で effect_ΔQ が immediate (1-10 step) → short (10-100) → medium (100-1000) で消費が拡大:

| cell | ΔQ_imm | ΔQ_short | ΔQ_medium |
|---|---:|---:|---:|
| alpha_n=1 / gini=low | -0.0008 | (中) | -0.0078 |
| alpha_n=4+ / gini=low | **-0.0053** (immediate 大) | (中) | -0.0068 |
| CID_n=2 | +0.0003 | (中) | -0.0085 |
| CID_n=5 | -0.0012 | (中) | -0.0082 |

→ 「電話 (immediate) vs 手紙 (medium)」で異なる効果サイズが構造的に出現。判定 (これが選択と集中か拡散か) は Web Claude / Taka 領域。

### 2.6 ESDE 3 scope は際立たず (集約 scope の限界)

ESDE_event / ESDE_step10 / ESDE_window はすべて outstanding_score 1-2 で目立たない。集約 scope (scope_id=-1) の限界、留保 #L10 (v1101a 段階 2) と整合。

### 2.7 B secondary Step G 重なり

Integration scope (alpha / beta) で 57/81 cells が Step G stratified と read-back あり。新規 emit なし、軽い踏み込み遵守。

---

## 3. 構造的成果 (network、数値)

### 3.1 primary table (Step B)

| 軸 | bin |
|---|---|
| 受け手構造 | CID 5 bin (n=2/3/4/5/6+) + alpha 10 bin (n × gini) + beta 9 bin + ESDE 3 解像度 |
| 時間スケール | window + immediate/short/medium |
| 応答 5 種 | attention/influence/variability/atom/category |

| 出力 | 規模 |
|---|---:|
| primary_table.parquet | 81 cells × 27 cols (28 KB) |
| outstanding_cells.parquet | 81 cells (B secondary join 済) |
| outstanding_thresholds.parquet | 15 threshold rows |
| v1102_observation.html | 33 KB (4 sections) |
| v1102_step_e_bit_identity_report.json | all_layers_pass=True |

### 3.2 outstanding_score 分布 (Step C)

| score | n cells | 割合 | 該当 cells |
|---:|---:|---:|---|
| 8 | 1 | 1.2% | alpha_n=4+ / gini=low / unit_kl |
| 7 | 1 | 1.2% | alpha_n=4+ / gini=low / rank1_flip |
| 6 | 4 | 4.9% | CID_n=6+ × 2 / beta_n=3 low × 2 |
| 5 | 8 | 9.9% | 中型サンプル多面シグナル |
| 4 | 5 | 6.2% | |
| 3 | 4 | 4.9% | |
| 2 | 20 | 24.7% | |
| 1 | 24 | 29.6% | border (CID_n=2 含む) |
| 0 | 14 | 17.3% | 際立たず |

合計 67/81 cells (82.7%) で何らかの際立ち。

### 3.3 bit-identity (Step E)

| 層 | 内容 | 結果 |
|---|---|---|
| A | Step B smoke seed 0 re-run parquet hash 一致 | True (0.9s) |
| B | v10.x + v1101a main outputs 1,435 files 不変 | 0/0/0 (全 frozen) |
| C | v1102 scripts 4 write calls すべて unified/v1102/ 配下 | True |

→ all_layers_pass = True

---

## 4. 留保事項総括

### 4.1 段階 1 設計時の既知留保 (継承)

| id | 内容 | v1102 での状態 |
|---|---|---|
| #L1 | unit_kl_static は時間軸なし、cid_state_ledger (a) 簡易版 | 段階 2 で時間軸付き unit_KL_delta 算出済、atom/category profile も (a) 簡易版ベース性質明記 |
| #L4 | alpha records 92.5% 偏り | Step F グラフで scope 内割合に正規化済 |
| #L8 | CID scope 予測 self-reference | v1102 でも CID scope は self-reference 構造を一部継承 |
| #L10 | ESDE 3 scope shuffle 効果薄 | §2.6 で ESDE 3 scope が際立たないことを確認 |
| #L12 | alpha_n=4+ / gini=low (1α / 141 records) で integration_β 0.950 | §2.2 で 8 指標際立ち拡張、新規 #L15 candidate |
| #L13 | beta scope で integration_α 経路出現 | v1102 では未追跡、Phase Result 領域 |

### 4.2 本 v1102 新規留保候補 3 件

| candidate id | 内容 |
|---|---|
| **#L14 candidate** | CID 構成ノード数で応答 atom 像が階層的に反転 (n=2 EMO.manifest / n=3-4 SOC.nation / n=5 EXS.being / n=6+ FND.timeless)、Taka「平均化で潰れる」直接対応、§2.1 |
| **#L15 candidate** | alpha_n=4+ / gini=low (47 records) で 15 指標中 8 指標で際立ち、極端値が多面シグナル化、留保 #L12 の拡張、§2.2 |
| **#L16 candidate** | variability_lift_mean が全 alpha cells で同値 = observation_c が per (scope, metric_type) で 1 値しかなく receiver_bin で分かれない (粒度問題)、Step C 改善要、§3.1 |

---

## 5. 規律遵守自己点検 (絶対格言 + 研究手法アップデート、抜粋)

| # | 格言 | 遵守 |
|---|---|---|
| 2 | 物理層 frozen | Step E 層 B で 1,435 files 完全保証 |
| 4 | 集団平均の罠 / 層化 | 受け手構造軸の層化が主題の核、Step G 拡張で実施 |
| 5 | 観察軸を増やすことを駆動要因にしない | 既存軸 (Step G 構成 / 時間粒度) の組み合わせ、新軸なし |
| 6 | 出口の固定 | §4 設計書出口 5 項目すべて満たす |
| 9 | 神の手回避 (意味更新版) | Top 10% + IQR 構造的閾値、恣意的閾値なし、z-score 単体不可 |
| 10 | 因果でなく因果候補 | 「条件が応答を変える」観察記録、因果断定なし |
| 12 | Aruism 判定回避 | 全 records 観察事実、判定 (選択と集中/拡散) は Web Claude / Taka |
| 13 | AI を信じない原則は Taka 個人 | §1.2 Taka 確認要請 2 件確定回答を反映 |
| 14 | Taka 直感優先 + 直感語保存 | §2.1 Taka「2 ノード大半 / 5 ノード強」を 24 seeds 3,088 cids で確認、§2.4 ordinary の構造的確認 |
| — | 研究手法アップデート | 際立ちの掬い取り A+B 適用、軽い踏み込み (B は v1101a 既存 emit read-back のみ) |
| — | Aruism 対称性 | 全出力候補・確率表記、100% を作らない (留保 #L8 CID self-reference は段階 2 で既知) |

---

## 6. Web Claude Phase Result + 次主題接続

### 6.1 Web Claude Phase Result 領域 (絶対格言 #12 解釈統合)

Code A は本書で観察事実を記録。**解釈統合は Web Claude 領域**:

- CID n_core 階層 (n=2 EMO/BOD → n=5 EXS/EXS → n=6+ FND/EXS) が何を意味するか
- alpha_n=4+ / gini=low が 8 指標で際立つことの主題的意味
- v107 effect_delta の時間粒度推移 (電話 vs 手紙の比喩) を「選択と集中 / 拡散」とどう接続するか
- 留保 #L14/L15/L16 candidate の v1102 / 次主題での位置づけ

### 6.2 v1102 主題担当範囲 (Code A)

段階 1 (Step A-F 全 6 段階) で Code A 主題担当範囲完了。設計書 §4 出口 5 項目すべて満たし、段 4・段 5 (応答候補化・言語化) と会話 ESDE 完成は v1102 範囲外明示済。

---

## 7. 出力ファイル総覧 (`unified/v1102/`)

| 種類 | ファイル | サイズ |
|---|---|---:|
| 設計書 | v1102_phase_design.md | (markdown) |
| 認識確認 | v1102_step_a_recognition.md | (markdown) |
| 観察事実報告 | v1102_step_f_observation_final.md (本書) | (markdown) |
| Step B 実装 | v1102_step_b_primary_table.py | (python) |
| Step C 実装 | v1102_step_c_outstanding_extraction.py | (python) |
| Step D 実装 | v1102_step_d_graph.py | (python) |
| Step E 実装 | v1102_step_e_bit_identity.py | (python) |
| primary table | outputs/main/primary_table.parquet | 28 KB |
| outstanding cells | outputs/main/outstanding_cells.parquet | (parquet) |
| outstanding thresholds | outputs/main/outstanding_thresholds.parquet | (parquet) |
| dashboard | outputs/v1102_observation.html | 33 KB |
| bit-identity report | v1102_step_e_bit_identity_report.json | (json) |

合計 12 ファイル、~100 KB。新規 main run なし、既存出力流用のみ (v1101a / v10.x main outputs read-only 完全保証)。

---

## 8. 一文サマリ (再掲)

v11.0.2 (v1102) 主題「条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察」段階 1 Step A-F 全完了、Step B primary table 構築 (81 cells × 27 cols、24 seeds 1 batch、11.4 秒) で応答 5 種 (attention / influence / variability / atom / category) + v107 時間粒度 (immediate/short/medium) を並列出力、Step C 際立ち掬い取り A primary (15 構造的指標 × Top 10%+IQR、神の手回避 #9) + B secondary (Step G read-back) で 67/81 cells (82.7%) 際立ち・最高 outstanding_score=8、Step D グラフ HTML 4 セクション (33 KB)、Step E bit-identity 3 層全 PASS (1,435 files frozen)、核心観察事実は (1) CID n_core 別で応答 atom/category 階層的に反転 (n=2 EMO.manifest/BOD → n=5 EXS.being/EXS → n=6+ FND.timeless) で Taka「平均化で潰れる」直接確認 (留保 #L14)、(2) alpha_n=4+ / gini=low (47 records) で 8 指標際立ち = 単発の極端値でなく多面シグナル (留保 #L12 拡張、#L15)、(3) CID_n=6+ (66 records、極稀) で 6 指標、(4) CID_n=2 (大半、6,012 records) は variability_actual のみで outstanding=1 = ordinary 構造確認、(5) v107 effect_ΔQ が immediate→medium で消費拡大 (電話 vs 手紙の比喩候補)、(6) ESDE 3 scope は集約限界で際立たず、新規留保候補 3 件 (#L14 CID 構成ノード数で atom 階層的反転 / #L15 alpha_n=4+ low の 8 指標際立ち / #L16 variability_lift が全 alpha 同値で粒度不足)、判定 (選択と集中 / 拡散、CID 階層、時間粒度推移の意味) は Web Claude Phase Result + Taka 主題評価領域。

---

*以上、v11.0.2 (v1102) Step F 観察事実最終報告 (Code A、2026-05-20)。judgement なし観察記録 (絶対格言 #12)。Web Claude Phase Result + Taka 主題評価判断を待つ。*
