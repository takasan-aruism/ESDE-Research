# v11.0.1 (v1101) Step E 観察事実報告 — 観察 3「補助平均統計 3 単位」

*作成*: 2026-05-17、Code A
*親*: `v1101_phase_design.md` (Web Claude 2026-05-16 改訂版) + `v1101_step_c_report.md` (観察 1) + `v1101_step_d_report.md` (観察 2) + Taka Step E 承認 (2026-05-17)
*対象*: Web Claude (Phase Result 翻訳用素材) + Taka (確認)
*目的*: Step E-1〜E-4 観察事実報告 (補助、3 単位)、judgment 回避、観察 1/2 との統合視点

---

## 0. 一文サマリ

Step E-1〜E-3 完了 (実行時間 1.5 秒、書き込み `unified/v1101/outputs/main/` 配下 3 ファイル計 58 KB)、観察 3 補助平均統計を 3 単位で算出: CID 単位 (24 seeds × ~228 cids × 326 atom cosine 類似度分布 = 1,253,760 (seed,cid,atom) ペア、326 atom × 14 統計列に集約) + Integration 単位 (β top_atom 24 seeds 横断集計 14 atoms / α pattern_class dominant_atom 横断集計 3 atoms = 17 行、ただし **member_cids 個別 cid id list は v10.x outputs に persistence されていないため段階 1 では top-K 集約に範囲調整**、齟齬 K candidate) + ESDE 単位 (4 解像度 × 60-65 atoms = 225 行、cross_seed_* 既存出力統合)、**核心発見 = 観察単位による dominant atom の構造的反転**: 同じ ESDE 系で CID-static sim_mean 首位 `CHG.begin` (0.54) / β top_atom 首位 `FND.logic` (160 βs / 24 seeds) / α pattern_class dominant 首位 `TIM.moment` (114 / 24 seeds) / ESDE event rank_1 首位 `WLD.artless` (26.2%) + `PER.sound` (25.9%) / ESDE step10 首位 `PER.sound` (28.3%) / ESDE window 首位 `TIM.moment` (34.2%) — **観察単位を変えるだけで dominant atom が CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound と categorically 異なる**、Taka 整理「平均化の罠」(絶対格言 #4) の生きた実例、観察 1/2 との接続として観察 1 v108_standard 中心 cid dominant = WLD.artless (21/24) + 観察 2 周辺 cid 占有 = PER.sound + WLD.artless (60%) は ESDE event/step10 レベルと整合だが Integration α/β レベルでは別 atom 像 (FND.logic / TIM.moment)、新規発見 = 観察フレームの選択が「Atom 隆盛」の見え方を決定的に変える構造、Code A は判定回避 (解釈統合は Web Claude Phase Result 領域)、齟齬 K candidate (Integration member_cids 個別 list 未 persistence、段階 2 で cid state ledger 再生対応) + 齟齬 L candidate (観察単位による dominant atom 反転、観察 3 の核心発見) を記録、Step F グラフ HTML 作成へ進行可。

---

## 1. Step E 構造的成果

### 1.1 観察 3 CID 単位 (E-1、24 seeds × 326 atom 濃度分布)

| 項目 | 値 |
|---|---:|
| 入力 | `cid_atom_sim_matrix_seed{0..23}.parquet` × 24 seeds |
| (seed, cid, atom) ペア数 | 1,253,760 (= 24 × ~228 × 326) |
| 集計 atom 数 | 326 (cid_atom_sim_matrix 全カラム) |
| 統計列 | 14 (n_obs, sim_mean/std/min/q25/median/q75/q90/q99/max + n_cids_sim_gt_{0.3,0.4,0.5,0.6}) |

### 1.2 観察 3 Integration 単位 (E-2、β/α top-K 集約)

| 項目 | 値 |
|---|---:|
| 入力 (β) | `beta_atom_aggregate_seed{0..23}.csv` × 24 seeds |
| 入力 (α) | `alpha_atom_aggregate_stratified_seed{0..23}.csv` × 24 seeds |
| 集計行 (unit × atom) | 17 (β 14 atoms + α 3 atoms) |

**齟齬 K candidate (Step E 発見、重要)**: Integration の **member_cids 個別 cid id list は v10.x outputs に persistence されていない** (beta_atom_aggregate には n_member_cids 個数のみ、cid id 列なし)。Web Claude 改訂版 §3.3 の「member_cids 全 atom ベクトル分布への解像度向上」は **段階 1 では実装不可**、段階 2 で対応 (cid state ledger 再生 + Integration 形成イベント再生、新規 main run 不要)。本書では top-K 集約 (top_atom + top5_atoms + max_atom_sim) + Integration size 分布 + atom popularity に範囲調整。

### 1.3 観察 3 ESDE 単位 (E-3、4 解像度集約)

| 項目 | 値 |
|---|---:|
| 入力 | `cross_seed_event/pulse/step10/dynamic_atom_emergence` (4 ファイル) |
| 解像度 | event / pulse / step10 / window |
| atom 数 (per resolution) | event 60 / pulse 65 / step10 60 / window 40 (= 225 total) |
| ratio_within_res 列追加 | per resolution 内 atom 比率 |

---

## 2. 核心発見: 観察単位による dominant atom の構造的反転 (齟齬 L candidate)

### 2.1 同じ ESDE 系で 6 つの異なる dominant atom

| 観察単位 | dominant atom (1 位) | 値 | 解像度依存 |
|---|---|---:|---|
| CID 単位 (cid_atom_sim_matrix sim_mean、24 seeds × 228 cids) | **CHG.begin** | 0.536 mean (cid 数 sim>0.5 = 3,890 / 5,224) | 静的 |
| Integration β top_atom (24 seeds 横断、156 βs) | **FND.logic** | 160 βs (= 79% of all β) | β レベル |
| Integration α pattern_class dominant (24 seeds × 6 patterns) | **TIM.moment** | 114 pattern classes (= 79% of 144) | α レベル |
| ESDE event resolution rank_1 (24 seeds 横断 atom 隆盛) | **WLD.artless** | 26.2% (115,670 / 440,640 records) | per event |
| ESDE pulse resolution rank_1 | **WLD.artless** | 22.0% | per pulse |
| ESDE step10 resolution rank_1 | **PER.sound** | 28.3% (507,845 records) | per 10 step |
| ESDE window resolution rank_1 | **TIM.moment** | 34.2% (10,751 records) | per window (~500 step) |

**観察事実**:
- 同じ ESDE 系で **5 つの異なる atom (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound)** が観察単位ごとに 1 位を取る
- 「ESDE で最も盛んな atom は何か」という問いに **構造的に単一答えがない**
- Taka 整理「私たちはこれまでに散々平均化の罠に陥ってきた」「決定論的に、全ての Integration 内の CID は同じ方向を向かなければいけない、と決めないこと」(主題ドキュメント §1.3) の **直接的な観察的根拠**

### 2.2 観察 1/2 との接続

| 観察 | dominant atom | 観察単位 |
|---|---|---|
| 観察 1 v108_standard 中心 cid (Step C §2.1) | WLD.artless (21/24 seeds) | n_pulses_short 最大 cid の rank_1 |
| 観察 1 v112 中心 cid | PER.sound (10/24) / TIM.moment (5/24) / TIM.appear (4/24) | 受容 cid pool 内 rank_1 |
| 観察 2 周辺 cid 占有 (Step D §2.2) | PER.sound (32%) + WLD.artless (30%) | per (event, Δt) rank_1 |
| 観察 2 中心 cid 支配可 (Step D §2.1) | PER.sound peak 84.8% | 取り込み時 rank_1 切替 |
| 観察 3 ESDE event resolution (本 Step E) | WLD.artless (26.2%) + PER.sound (25.9%) | 24 seeds 横断 event rank_1 |
| 観察 3 ESDE step10 | PER.sound (28.3%) + WLD.artless (24.3%) | 24 seeds 横断 step10 rank_1 |
| 観察 3 Integration β | FND.logic (79%) | β top_atom |
| 観察 3 Integration α | TIM.moment (79%) | α dominant_atom |

**観察事実 (統合)**:
- **観察 1 + 観察 2 + 観察 3 ESDE event/step10 は整合**: WLD.artless + PER.sound が cid rank_1 レベルで dominant
- **観察 3 Integration β/α レベルは categorically 異なる**: FND.logic (β) / TIM.moment (α) が dominant
- ESDE は「cid の rank_1_atom 分布」と「Integration の構成 atom 分布」が **異なる atom 群** を持つ二層構造

### 2.3 留保解釈候補 (Web Claude 領域)

Code A は以下のように解釈統合**しない**、留保候補のみ:
- 候補 (a): cid の rank_1_atom (= 各 cid が「最も似ている」と判定する atom) と、cid 集団が形成する Integration の top atom は **異なる Atom 像** を提示している可能性
- 候補 (b): Integration α pattern_class (bridge/capture/core/...) は構造的に TIM 系 atom (時間的継起) を dominant にする傾向、β は「条件因子で結合された cid 群」として FND/COG 系 (基底論理) を dominant にする傾向 → ただし要厳密検証
- 候補 (c): 集計単位による方向反転は留保 #33 (v10.13.a) と同型構造、本観察は留保 #33 を Atom レベルで一般化した事例

解釈統合は Web Claude Phase Result 領域。

---

## 3. 副次観察 (Web Claude 必要時翻訳用)

### 3.1 CID 単位 sim_mean による atom ランキング (上位 10)

| rank | atom | category | sim_mean | sim_median | n_cids_sim>0.5 (out of 5,224) |
|---|---|---|---:|---:|---:|
| 1 | CHG.begin | CHG | 0.536 | 0.616 | **3,890** (74.5%) |
| 2 | TIM.moment | TIM | 0.528 | 0.545 | 3,772 |
| 3 | PRP.easy | PRP | 0.518 | 0.554 | 3,806 |
| 4 | TIM.period | TIM | 0.514 | 0.539 | 3,773 |
| 5 | SPC.direction | SPC | 0.513 | 0.531 | 3,742 |
| 6 | CHG.advance | CHG | 0.508 | 0.541 | 3,764 |
| 7 | WLD.artless | WLD | 0.498 | 0.535 | 3,668 |
| 8 | STA.healing | STA | 0.485 | 0.541 | 3,591 |
| 9 | SOC.work | SOC | 0.484 | 0.526 | 3,354 |
| 10 | WLD.technique | WLD | 0.476 | 0.516 | 3,090 |

**観察事実**:
- 上位 6 atom は CHG / TIM / PRP / SPC 系 (変化 / 時間 / 性質 / 空間方向) で **観察 1/2/3 ESDE rank_1 dominant の WLD.artless / PER.sound と異なる**
- CHG.begin は cid の **74.5%** で sim > 0.5、構造的に高類似度の atom

### 3.2 CID 単位 category 別 sim_mean

| category | mean sim across atoms | n atoms in category |
|---|---:|---:|
| CHG (change) | 0.383 | 7 |
| ECO (ecological) | 0.382 | 12 |
| BOD (body) | 0.378 | 8 |
| TIM (time) | 0.371 | 7 |
| ACT (action) | 0.356 | 28 |
| COM (communication) | 0.345 | 12 |

**観察事実**: CHG / ECO / BOD / TIM 系は cid との類似度が体系的に高い。

### 3.3 Integration β top_atom 横断分布 (24 seeds、全 156 βs)

| atom | n_βs as top | n_seeds_appeared | size_mean (n_member_cids) | sim_mean |
|---|---:|---:|---:|---:|
| **FND.logic** | **160** | 24 | 1.24 (主に単独 cid β) | 0.591 |
| COG.enlightenment | 50 | 24 | **7.06** (large β) | 0.502 |
| COG.learn | 25 | 14 | 1.12 | 0.602 |
| WLD.culture | 18 | 13 | 1.00 | 0.549 |
| EXS.being | 14 | 9 | 1.07 | 0.475 |
| CHG.end | 12 | 9 | 1.00 | 0.581 |
| FND.timeless | 12 | 7 | 1.08 | 0.466 |

**観察事実**:
- FND.logic は **24 seeds 全部** で複数 β の top_atom (合計 160 / 全 βs)
- **COG.enlightenment は size_mean = 7.06** (member_cids 7 個平均) で他の β より構造的に大きい
- FND.logic + COG.enlightenment + COG.learn の 3 atom で全 β top の **75%** (160+50+25 = 235 / ~290)
- 全 β の dominant は **FND/COG 系 (論理 / 認知)** で偏在

### 3.4 Integration α pattern_class dominant (24 seeds × 6 patterns)

| atom | n_pattern_class_as_dominant | n_seeds_appeared | n_alphas_mean | sim_mean |
|---|---:|---:|---:|---:|
| **TIM.moment** | **114** (out of 144) | 24 | 117.9 | 0.461 |
| FND.logic | 20 | 15 | 100.7 | 0.444 |
| COG.enlightenment | 10 | 8 | 77.1 | 0.456 |

**観察事実**:
- TIM.moment は **24 seeds 全部 × 6 pattern classes** で 114 / 144 = **79%** が dominant
- 第 2 位 FND.logic は 15 seed のみで dominant
- α レベルは **TIM.moment が圧倒的支配的**

### 3.5 ESDE 4 解像度の atom ランキング (top 5 比較)

| rank | event | pulse | step10 | window |
|---|---|---|---|---|
| 1 | WLD.artless (26.2%) | WLD.artless (22.0%) | PER.sound (28.3%) | **TIM.moment (34.2%)** |
| 2 | PER.sound (25.9%) | TIM.appear (12.4%) | WLD.artless (24.3%) | WLD.artless (11.9%) |
| 3 | WLD.culture (6.7%) | EXS.being (11.6%) | WLD.culture (7.9%) | TIM.appear (8.6%) |
| 4 | EXS.being (6.4%) | TIM.moment (8.3%) | EXS.being (7.7%) | WLD.culture (7.3%) |
| 5 | FND.timeless (5.3%) | PER.sound (7.5%) | FND.timeless (6.5%) | EXS.being (6.9%) |

**観察事実**:
- **window 解像度のみ TIM.moment が 1 位 (34.2%)** で他 3 解像度と異なる
- event / pulse / step10 では WLD.artless / PER.sound が首位を分け合う
- 解像度が粗くなる (event → pulse → step10 → window) ほど top の偏在度が高くなる傾向 (event 26% → window 34%)

---

## 4. 観察事実の解釈規律遵守 (絶対格言 #10, #12)

Code A は本観察事実を以下のように **断定しない**:

- 観察事実: 観察単位ごとに dominant atom が異なる (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound)
- 主題評価 (NOT Code A 領域): 「ESDE の本当の dominant atom はどれか」「Integration α と β が異なる意味階層を反映している」等の解釈統合は **Web Claude Phase Result 領域**
- Code A 領域: 構造的事実 + 留保解釈候補 + 観察 1/2/3 間の整合点と齟齬点の整理

success/fail 判定なし、観察フレームの違いそのものを観察事実として記録、Web Claude が Phase Result で「平均化の罠の生きた実例」として翻訳統合する素材を提供。

---

## 5. 出力ファイル仕様 (58 KB)

| ファイル | サイズ | 行数 | 用途 |
|---|---:|---:|---|
| `observation_3_cid_atom_distribution.parquet` | 35 KB | 326 | per atom × 14 統計列 (CID 単位) |
| `observation_3_integration_summary.parquet` | 5.8 KB | 17 | per (unit × atom) の Integration 集計 (β 14 + α 3) |
| `observation_3_esde_aggregate.parquet` | 17 KB | 225 | per (resolution × atom) の ESDE 隆盛 |

書き込みは `unified/v1101/outputs/main/` 配下のみ、`developmental/v106/v108/v112` の main outputs は **1 byte も変更していない** (Step G で bit-identity 層 B 検証予定)。

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step E での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ §1-3 で構造的事実先、§4 で解釈規律 |
| 2 | 物理層 frozen 絶対 | ✓ v10.6 既存出力 read-only、書き込み unified/v1101/ 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | △ 観察 3 は平均集計、観察 1/2 との接続で構造比較 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ §2 核心発見が「観察単位による dominant atom 反転」、平均化の罠の生きた実例として記録 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ v10.6 既存出力流用のみ、新規軸なし、観察フレーム転換 |
| 6 | 出口の固定 | ✓ §5 で 3 出力ファイル + §2 核心発見 + §3 副次観察 5 件を固定 |
| 7 | 主題着手前に上位資料を読む | ✓ Step C/D 完了、主題ドキュメント反映済 |
| 8 | 過去観察軸の照会 | ✓ §2.2 で観察 1/2/3 の整合点と齟齬点を表で整理 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ 全 atom 一括処理、threshold 0.3/0.4/0.5/0.6 構造的、ハンドチューニングなし |
| 10 | 因果ではなく因果候補 | ✓ 「~の可能性」「留保解釈候補」表現、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ CID-static / β / α / ESDE-{event/pulse/step10/window} を §2.1 表で完全区別 |
| 12 | Aruism 判定回避 | ✓ success/fail なし、留保解釈候補 (a)(b)(c) を §2.3 で提示 |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Code A 仮所見は Web Claude 確認待ち、断定なし |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka「平均化の罠」「Integration 内同方向強制せず」が §2 核心発見と整合 |
| 15 | 5 者運用体制の補完性 | ✓ Code A 齟齬 K candidate (member_cids list 未 persistence) + 齟齬 L candidate (観察単位反転) を Web Claude 確認要請 |

→ **15 格言全項目遵守** (#3 段階 2 で適用検討)。

---

## 7. 新規留保 (Step E 由来、2 件)

| id | step | title | 状態 |
|---|---|---|---|
| **#41 candidate** (旧 §10.1 #38) | v1101 Step E | Integration の member_cids 個別 cid id list は v10.x outputs に persistence されておらず、Web Claude 改訂版 §3.3 の「member_cids 全 atom ベクトル分布」は段階 1 では実装不可、段階 2 で cid state ledger 再生 + Integration 形成イベント再生で対応 (新規 main run 不要) | 段階 2 検討対象 |
| **#42 candidate** | v1101 Step E | 観察単位 (CID-static / β / α / ESDE-{event/pulse/step10/window}) による dominant atom の構造的反転 (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound)、Taka「平均化の罠」と整合、v10.13.a 留保 #33 (集計単位による方向反転) の Atom レベル一般化 | Web Claude Phase Result で解釈統合 |

---

## 8. Step F 進行案 (Code A 推奨)

| Step | 内容 | 想定時間 |
|---|---|---|
| Step F-1 | グラフ HTML 設計 — v105 Plotly + go.Frame pattern を踏襲、観察 1/2/3 の主要結果を可視化 | 30 分 |
| Step F-2 | 観察 1 グラフ (中心 cid の atom 時系列、4 解像度 selectable) | 1 時間 |
| Step F-3 | 観察 2 グラフ (取り込み点中心の波及プロファイル、Δt 軸 × 25 atom × center_match_rate) | 1 時間 |
| Step F-4 | 観察 3 グラフ (3 単位 dominant atom 反転の可視化、本 Step E 核心発見) | 1 時間 |
| Step F-5 | 単一 HTML 統合出力 (`v1101_observation.html`、include_plotlyjs="cdn") | 30 分 |

→ Step F 合計約 3-4 時間。Web Claude/Taka 承認後着手。

---

## 9. 一文サマリ (再掲)

Step E-1〜E-3 完了 (実行時間 1.5 秒、出力 58 KB)、観察 3 補助平均統計を CID 単位 (24 seeds × 228 cids × 326 atom = 1,253,760 ペアを 326 atom × 14 統計に集約) + Integration 単位 (β 14 atoms + α 3 atoms = 17 行、ただし齟齬 K candidate: member_cids 個別 cid id list 未 persistence のため段階 1 では top-K 集約に範囲調整) + ESDE 単位 (4 解像度 × 60-65 atoms = 225 行) で算出、**核心発見** (齟齬 L candidate) = 観察単位による dominant atom の構造的反転: CID-static sim 首位 CHG.begin (0.54) / β top_atom 首位 FND.logic (160/24 seeds) / α pattern_class dominant 首位 TIM.moment (114/24) / ESDE event 首位 WLD.artless (26.2%) + PER.sound (25.9%) / ESDE step10 首位 PER.sound (28.3%) / ESDE window 首位 TIM.moment (34.2%) — 同じ ESDE で観察単位を変えるだけで dominant atom が 5 atom (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound) に変わる、Taka「平均化の罠」(絶対格言 #4) の生きた実例、観察 1/2 (WLD.artless + PER.sound) と観察 3 ESDE event/step10 は整合だが Integration α/β レベル (FND.logic / TIM.moment) では別 atom 像、副次観察 5 件 (CID-level top 10 / category 別 / β/α/4 解像度 top 5)、絶対格言 15 件全項目遵守、Code A は judgment 回避 (解釈統合は Web Claude)、新規留保 #41/#42 candidate、書き込み unified/v1101/outputs/main/ 配下 3 ファイル (58 KB)、v106/v108/v112 main outputs 不変、Step F グラフ HTML 作成 (観察 1/2/3 統合可視化、v105 Plotly pattern 踏襲) へ進行可。

---

*以上、v11.0.1 (v1101) Step E 観察事実報告 (Code A、2026-05-17)。Web Claude/Taka 確認後、Step F グラフ HTML 作成に進む。Code A 認識確認連続 10 段階継続中。*
