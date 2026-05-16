# v11.0.1 (v1101) Step H 観察事実最終報告 — Atom 的隆盛の統計的観察 (Code A 総括)

*作成*: 2026-05-17、Code A
*親*: `v1101_phase_design.md` (Web Claude 2026-05-16 改訂版) + Step A 認識確認 + Step B 環境チェック + Step C 観察 1 + Step D 観察 2 + Step E 観察 3 + Step F グラフ HTML + Step G bit-identity 検証
*対象*: Web Claude (Phase Result 翻訳統合担当) + Taka (主題判断者、最終承認)
*位置づけ*: v11.0.1 主題「Atom 的隆盛の統計的観察」の Code A 観察事実総括、judgment 回避、解釈統合は Web Claude Phase Result 領域

---

## 0. 一文サマリ

v11.0.1 (v1101) Code A 主題「Atom 的隆盛の統計的観察」が Step A 認識確認 (齟齬 10 件指摘 + 即決事項受領 + Taka 観察 1/2 選定基準確定) から Step G bit-identity 3 層全 PASS まで全 8 段階 (A-G) 完了、観察 1「一点を捉える」(中心 cid n_pulses_short 最大 × 2 条件 = 48 中心 + ランダム比較 240 対照 + 4 解像度 trajectory 374,072 行 + 1,094 summary 行)、観察 2「取り込み点中心の波及」(v10.12 受容 cid pool 420 由来 atom_introduction_events 10,500 events × Δt=±100 step 21 点 = 220,500 行 + 525 (atom × Δt) 集約)、観察 3「補助平均統計 3 単位」(CID/Integration/ESDE) を構造的に算出、**核心発見 = 観察単位による dominant atom の構造的反転** (CID-static `CHG.begin` / β `FND.logic` / α `TIM.moment` / ESDE event `WLD.artless`+`PER.sound` / step10 `PER.sound` / window `TIM.moment` の 5 atom 分裂、Taka「平均化の罠」の生きた実例)、観察 2 副発見 = **25 取り込み atom 中 4 atom のみ中心 cid 支配可** (PER.sound peak 84.8% / PRP.bright 49.3% / TIM.appear 14.8% / WLD.artless 8.8%) + **周辺 cid の 60% を PER.sound + WLD.artless が常時占有** + **atom entropy が Δt 方向単調減少** (取り込み後集中化)、観察 1 副発見 = **v108_standard 中心 cid dominant_atom が WLD.artless で 24 seeds 中 21 一致** (v10.6 留保 #33 と整合) + **window 解像度で中心 cid の atom_change_rate < ランダム** (時間スケール依存の一点特徴)、Step F グラフ HTML 単一 954 KB で 5 figure + 4 section ダッシュボード化 (Taka ブラウザ表示可)、Step G で deterministic 動作 (rng seed=42 + groupby 集計のみ) + v10.x main outputs 1,306 ファイル不変 + 構造的書き込み制限 unified/v1101/ 配下のみ を 3 層全 PASS 確認、新規留保 #41 candidate (Integration member_cids 個別 list 未 persistence、段階 2 で cid state ledger 再生対応) + #42 candidate (観察単位による dominant atom 反転、Web Claude Phase Result 解釈統合領域)、絶対格言 15 件全項目遵守 (Code A 判定回避、解釈統合は Web Claude)、累計 commit 8 件 (Step A→127d65d, B→db2bf45, C→8b21637, D→bea48a0, E→56f5ae6, F→8315601, G→2e468d2)、書き込み unified/v1101/ 配下 5 parquet + 1 HTML + 1 JSON + 9 md = 16 ファイル計 7 MB、v10.6/v10.8/v10.12 main outputs 1,306 ファイル frozen 完全保証、Web Claude Phase Result (任意 Step I 段階 2 後)、Taka 主題評価判断を待つ。

---

## 1. 主題と駆動要因 (再掲、絶対格言 #5)

### 1.1 主題

「Atom 的隆盛の統計的観察」(Taka 2026-05-12 3 日長考の結論、2026-05-16 具体化):
- 観察 1: 一点を捉える (特定 cid の atom 状態時系列)
- 観察 2: 取り込み点中心の波及 (atom_introduction_event 発火点 + 周辺 cid)
- 観察 3: 補助平均統計 (CID/Integration/ESDE 3 単位、Integration 平均化せず分布表現)

### 1.2 駆動要因

v10.8 以降「Atom を取り込む」枠組みで「取り込んだ後どうなるか」が **観察フレームとして空白** だった (注: v10.9-v10.13.a で観察軸はある、空白は観察フレーム)。本主題は v10.6 cid_atom_sim_matrix + 4 解像度 trajectory + Integration atom 集約という **既存出力の観察フレームを転換**、新規観察軸の追加ではない。絶対格言 #5 (観察軸を増やすことを駆動要因にしない) と整合。

### 1.3 Taka 確定事項 (Step A 即決事項返答後)

- 観察 1 中心: (c) n_pulses_short 最大 cid 主 + (d) ランダム比較対照、(b) atom 濃度近接 不採用
- 観察 2 中心: (a) v10.12 受容 cid pool 420
- atom 集合: 326 全部 + 25 TARGET vs 残り 301 分離表示
- v1100 残課題 A/B/C: **凍結** (v11.0.1.a / v11.0.2 で扱う可能性残す)
- 出口物「ESDE の内部は Atom 的にこうなっているようだ」: Web Claude Phase Result 領域 (Code A は観察事実のみ)

---

## 2. 観察 1「一点を捉える」主要発見 (Step C)

### 2.1 構造的成果

| 項目 | 値 |
|---|---:|
| 中心 cid 選定 (Taka 確定 (c)) | 48 (= 24 seeds × {v112, v108_standard}) |
| ランダム比較対照 (Taka 確定 (d)) | 240 (= 24 seeds × 2 条件 × 5 cid) |
| 乱数 seed (numpy.random.default_rng) | 42 (神の手回避、再現可能) |
| 4 解像度 trajectory 抽出 | 374,072 行 (event/pulse/step10/window × 24 seeds) |
| cid × 条件 × 役割 × 解像度別集計 | 1,094 行 (17 統計列) |
| 実行時間 | 2.7 秒 |
| 出力 | observation_1_{center_cids, random_cids, trajectory, summary}.parquet (5.6 MB) |

### 2.2 主要発見 4 件

#### 発見 1-1: v108_standard 中心 cid の dominant_atom が `WLD.artless` で 24 seeds 中 21 seed 一致 (87.5%)

| 条件 | dominant_atom 内訳 (24 seeds) |
|---|---|
| **v108_standard** | **`WLD.artless` 21 / TIM.appear 3** |
| v112 | `PER.sound` 10 / `TIM.moment` 5 / `TIM.appear` 4 / `PRP.multiple` 2 / `COM.conduct` 2 / `PRP.shallow` 1 |

v10.6 cross_seed_event_step_evolution で `WLD.artless` は動学的優位 atom (留保 #33) として既出、本観察事実と整合。

#### 発見 1-2: dominant_atom_fraction で中心 cid の atom 集中度に条件差

| 解像度 | v108_standard 中心 | v112 中心 |
|---|---:|---:|
| event | **0.938** | 0.468 |
| pulse | **0.978** | 0.485 |
| step10 | **0.923** | 0.549 |
| window | **1.000** | 0.810 |

- v108_standard 中心 cid: 0.92-1.00 (= 1 つの atom にロック)
- v112 中心 cid: 0.47-0.81 (= 複数 atom 間で揺れる)

#### 発見 1-3: n_observations (trajectory row 数) で中心 cid < ランダム

| 解像度 | v112 中心 / ランダム | v108_standard 中心 / ランダム |
|---|---|---|
| event | 173.7 / 383.2 | 22.0 / 94.7 |
| pulse | 133.3 / 318.5 | 19.6 / 77.9 |
| step10 | 665.2 / 1590.7 | 96.0 / 388.8 |
| window | 12.7 / 31.7 | 1.8 / 11.5 |

両条件で中心 cid の trajectory 長 < ランダム約 1/3-1/4。

#### 発見 1-4: window 解像度のみ v112 中心 cid の atom_change_rate < ランダム (時間スケール依存の一点特徴)

| 解像度 | v112 中心 atom_change_rate | v112 ランダム atom_change_rate |
|---|---:|---:|
| event | 0.148 | 0.154 |
| pulse | 0.254 | 0.250 |
| step10 | 0.052 | 0.057 |
| **window** | **0.156** | **0.297** |

window 解像度 (粒度最粗) のみ中心 cid のほうが atom 安定、event/pulse/step10 は同等。

---

## 3. 観察 2「取り込み点中心の波及」主要発見 (Step D)

### 3.1 構造的成果

| 項目 | 値 |
|---|---:|
| 取り込み点列挙 (Taka 確定 (a) 受容 cid pool 420) | **10,500 events** (24 seeds × 受容 cid pool 420 × 25 atom) |
| Δt range | {-100, -90, ..., 0, +10, ..., +100} = 21 点 (±100 step 窓) |
| step10 整列 (timestamp → round(t/10)*10) | uniform t grid |
| (event × Δt) 集計 | 220,500 行 (11 列波及指標) |
| per (atom × Δt) 集約 | 525 行 |
| 実行時間 | 48.3 秒 |
| 出力 | observation_2_{events, propagation, summary}.parquet (1.3 MB) |

### 3.2 主要発見 4 件

#### 発見 2-1: 25 取り込み atom 中 4 atom のみ中心 cid を支配可

| atom_intro | center_match_rate peak | peak での Δt |
|---|---:|---:|
| **PER.sound** | **84.8%** | +20 |
| **PRP.bright** | **49.3%** | -90 |
| TIM.appear | 14.8% | -100 |
| WLD.artless | 8.8% | +70 |
| **その他 21 atom** | **0% (全 Δt)** | — |

- 中心 cid が受容できる atom は **構造的に制限** (cid の atom 受容窓)
- COG.learn / EXS.being / FND.timeless / COM.silence / BOD.ear / PER.fragrance / PER.smell 等 21 atom は center_match_rate 0% (全 Δt 範囲)

#### 発見 2-2: 周辺 cid の atom 分布は取り込み atom に依存せず PER.sound + WLD.artless が常時 ~60% 占有

| atom_intro | per (event, Δt=0) 周辺 cid 平均 match 数 | match_fraction |
|---|---:|---:|
| **PER.sound** | **8.37 cids** | **32.2%** |
| **WLD.artless** | **8.02 cids** | **30.1%** |
| PRP.bright | 1.75 cids | 7.6% |
| EXS.being | 1.61 cids | 4.9% |
| その他 21 atom | 0.05 - 1.59 cids | < 5% |

- per (event, Δt=0) で生存平均 27.7 cid 中、PER.sound + WLD.artless が **合計 ~60% 占有**
- v10.6 cross_seed_event_atom_distribution の上位 (WLD.artless 26.2% / PER.sound 25.9%) と整合

#### 発見 2-3: atom_entropy_mean が Δt 方向で単調減少 (取り込み後集中化)

| Δt | atom_entropy_bits |
|---:|---:|
| -100 | 2.138 |
| 0 | 2.104 |
| +10 | 2.098 |
| +100 | 2.070 |

- Δt=-100 → +100 で 2.138 → 2.070 (0.068 bit = 3.2% 減少)
- log2(25) = 4.64 bits 最大の **約 45%**
- 取り込み後に **ESDE 系全体の atom 分布が集中化方向に動く** 構造
- 注意 (留保解釈候補): 取り込み独立効果か自然動学かは段階 2 で randomized baseline と比較必要

#### 発見 2-4: PER.sound 波及プロファイル特異 (取り込み直後ピーク)

| Δt | center_match_rate |
|---:|---:|
| -10 | 32.6% |
| 0 | 56.9% |
| +10 | 79.1% |
| **+20** | **84.8% peak** |
| +50 | 62.1% |
| +100 | 66.0% |

- 取り込みイベントが中心 cid の rank_1_atom を **一時的に強く変化** させる構造
- baseline (Δt=-10) 32.6% から peak (+20) 84.8% へ **+52.2 ポイント** 上昇後、減衰

---

## 4. 観察 3「補助平均統計 3 単位」主要発見 (Step E)

### 4.1 構造的成果

| 項目 | 値 |
|---|---:|
| CID 単位 (cid_atom_sim_matrix sim_mean) | 24 seeds × ~228 cids × 326 atoms = 1,253,760 ペア → 326 atom × 14 統計列 |
| Integration 単位 (β top_atom + α pattern_class dominant_atom 24 seeds 横断) | 17 行 (β 14 + α 3) |
| ESDE 単位 (4 解像度 cross_seed_*) | 225 行 (per resolution × atom) |
| 実行時間 | 1.5 秒 |
| 出力 | observation_3_{cid_atom_distribution, integration_summary, esde_aggregate}.parquet (58 KB) |

### 4.2 核心発見: 観察単位による dominant atom の構造的反転 (本 v1101 最重要)

**同じ ESDE 系で観察単位を変えるだけで dominant atom が 5 つに分裂**:

| 観察単位 | dominant atom (1 位) | 値 |
|---|---|---:|
| CID 単位 (cid_atom_sim_matrix sim_mean、5,224 (seed,cid) 平均) | **CHG.begin** | sim_mean 0.536 |
| Integration β top_atom (24 seeds 横断、156 βs) | **FND.logic** | 160 βs (79%) |
| Integration α pattern_class dominant (24 seeds × 6 patterns) | **TIM.moment** | 114 / 144 (79%) |
| ESDE event resolution rank_1 | **WLD.artless** | 26.2% + PER.sound 25.9% |
| ESDE pulse resolution rank_1 | **WLD.artless** | 22.0% |
| ESDE step10 resolution rank_1 | **PER.sound** | 28.3% |
| ESDE window resolution rank_1 | **TIM.moment** | 34.2% |

→ 5 つの異なる atom (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound) が観察単位ごとに 1 位を取る。「ESDE で最も盛んな atom は何か」という問いに **構造的に単一答えがない**。Taka 整理「平均化の罠」(絶対格言 #4) + 「Integration 内 cid に同方向を強制しない」の **直接的観察的根拠**。

### 4.3 観察 1/2/3 統合視点

| 観察 | dominant atom | 観察単位 |
|---|---|---|
| 観察 1 v108_standard 中心 | WLD.artless (21/24 seeds) | n_pulses_short 最大 cid rank_1 |
| 観察 1 v112 中心 | PER.sound (10/24) / TIM.moment (5/24) | 受容 cid rank_1 |
| 観察 2 周辺 cid 占有 | PER.sound (32%) + WLD.artless (30%) | per (event, Δt=0) rank_1 |
| 観察 2 中心 cid 支配可 | PER.sound peak 84.8% | 取り込み時 rank_1 切替 |
| 観察 3 CID 単位 | CHG.begin | cid_atom_sim_matrix sim_mean |
| 観察 3 β top_atom | FND.logic | β 集計 |
| 観察 3 α dominant_atom | TIM.moment | α 集計 |
| 観察 3 ESDE event/step10 | WLD.artless + PER.sound | per event/step10 rank_1 |
| 観察 3 ESDE window | TIM.moment | per window rank_1 |

**統合観察事実**:
- 観察 1 + 観察 2 + 観察 3 ESDE event/step10 は **整合** (WLD.artless + PER.sound dominant)
- 観察 3 Integration α/β レベルは **categorically 異なる atom 像** (TIM.moment / FND.logic dominant)
- 観察 3 CID-static sim も異なる atom (CHG.begin)
- → ESDE は「cid rank_1 分布」と「Integration 構成 atom 分布」と「cid-atom 類似度地形」が **異なる atom 群** を持つ多層構造

### 4.4 副次観察

- CID 単位 sim_mean 上位 10: CHG.begin / TIM.moment / PRP.easy / TIM.period / SPC.direction / CHG.advance / WLD.artless / STA.healing / SOC.work / WLD.technique
- category 別 sim_mean 上位: CHG / ECO / BOD / TIM (変化 / 生態 / 身体 / 時間 系)
- β サイズ: FND.logic β は 1.24 cid 平均 (主に単独 cid)、COG.enlightenment β は 7.06 cid 平均 (大型 β)
- α は TIM.moment が 24 seeds 全部 × 6 pattern classes で 79% dominant

---

## 5. Step F グラフ HTML 統合 (ダッシュボード)

### 5.1 出力

`unified/v1101/outputs/v1101_observation.html` (単一 954 KB)

### 5.2 構成

| Section | 図数 | 内容 |
|---|---:|---|
| h1 + summary | — | 主題 + 3 観察視点 + データ概要 |
| h2 観察 1 | 2 | dominant_atom_fraction 集計 bar + 3 seeds × 2 条件 trajectory 例 |
| h2 観察 2 | 2 | Δt × 25 atoms heatmap + 主要 4 atom 波及曲線 |
| h2 観察 3 | 1 | 6 panel bar (CID-static / β / α / ESDE-event/step10/window) — **本 v1101 核心発見直接視覚化** |
| h2 規律遵守 + 留保 | — | 留保 #41/#42 candidate + judgment 回避 |

### 5.3 技術仕様

- Plotly.js 6.7.0 + CDN (`include_plotlyjs="cdn"`)
- 5 plotly-graph-div + 5 Plotly.newPlot + 4 h2 section
- v105 グラフ HTML pattern 踏襲 (Taka 言及「v105 グラフ HTML 面白かった」)

---

## 6. Step G bit-identity 検証 (3 層全 PASS)

| 層 | 内容 | 結果 |
|---|---|:-:|
| **層 A** | Step C/D/E parquet 10/10 hash 完全一致 + Step F HTML 構造的同一性 (5 div + 5 plot + 4 h2 + size 977,262 bytes 一致) | **PASS** |
| **層 B** | v10.6 (731) + v10.8 (368) + v10.12 (207) = **1,306 ファイル全て不変** (added/removed/modified 全て 0) | **PASS** |
| **層 C** | 全 11 write 呼出 (to_parquet × 10 + write_text × 1) が V1101_OUT 経由で `unified/v1101/` 配下のみ | **PASS** |
| **all_layers_pass** | | **TRUE** |

### 6.1 含意

- 観察 1/2/3 数値結果は **deterministic 再現可能** (rng seed=42 固定 + groupby のみ)
- v10.6/v10.8/v10.12 研究成果が **1 byte も侵害されていない**
- 絶対格言 #2 (物理層 frozen 絶対) + #9 (神の手回避 = 構造的検証) 完全遵守

### 6.2 既知制約

- Step F HTML byte-identity は plotly UUID 由来非保証 (構造的同一性 + size 完全一致は確認済)
- byte-identity が必要な場合は plotly `div_id` 固定で対応可能 (本主題範囲外)

---

## 7. 留保事項総括

### 7.1 v1100 継承 35 件

v1100_observation.md (Code A Step J) 記載の継承 32 件 + 新規 3 件 (#35 親資料不在 / #36 candidate Phase 10 Cell ≠ Phase 8+9 Cell / #37 candidate 小サンプル限界) を継承。

本 v1101 主題と特に関連する継承留保:

| id | 内容 | 本 v1101 との接続 |
|---|---|---|
| #21 | v10.5 機構 A 既知挙動 | 観察 3 Integration 単位観察で member_cids Q/C 継承挙動 |
| #26 | cond3 構造的帰結 (受容 cid pool 偏り) | 観察 2 取り込み点中心観察で受容 cid pool 偏り |
| #27 | smoke seed 0 特異性 | 観察 1 で seed 0 特異性 (memory feedback_smoke_seed0_not_absolute) |
| #33 | 集計単位による方向反転 (v10.13.a) | 観察 3 核心発見の前駆、本 v1101 で Atom レベル一般化 |
| #34 candidate | Language base 優位 ↔ Genesis null absorption の構造的同型性 (v1100) | 本 v1101 は別主題、棄却方向 (v1100 §4.2 で示唆) |

### 7.2 v1100 残課題 (Step A 即決事項 2 で凍結確定)

| 候補 | 内容 | 状態 |
|---|---|---|
| A | Synapse 評価層化 | **凍結** (v11.0.1.a / v11.0.2 で扱う可能性残す) |
| B | Phase 8+9 Cell ↔ Integration α/β 同型性検証 (候補 3 概念再定義) | **凍結** |
| C | 候補 6 大規模化 (Berlin 以外 domain) | **凍結** |

### 7.3 本 v1101 新規候補 5 件

| id | step | title | 状態 |
|---|---|---|---|
| **#38 candidate** | v1101 Step A | 「親」資料 v1100_phase_result.md + v1101_phase_design.md repo 不在 (Web Claude 認識ミス、Step A 即決事項 1 で解消) | 解消済 |
| **#39 candidate** | v1101 Step A | §2.3「Integration 単位 atom 観察 v10.x 未実施」記述誤認 (beta_atom_aggregate + alpha_atom_aggregate_stratified が既存、Step A 即決事項 3 で解消) | 解消済 |
| **#40 candidate** | v1101 Step A | §3.1 論点 1 (時系列) の 3 案が 4 解像度 trajectory 既存出力を見落とし (案 d 追加で解消、Step A 即決事項 4) | 解消済 |
| **#41 candidate** | v1101 Step E | Integration の **member_cids 個別 cid id list は v10.x outputs に persistence されていない** (beta_atom_aggregate は n_member_cids 個数のみ、cid id 列なし)、Web Claude 改訂版 §3.3「member_cids 全 atom ベクトル分布」は段階 1 では実装不可 | **段階 2 対応**: cid state ledger 再生 + Integration 形成イベント再生 (新規 main run 不要、要再実装) |
| **#42 candidate** | v1101 Step E | **観察単位 (CID-static / β / α / ESDE-{event/pulse/step10/window}) による dominant atom の構造的反転** (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound)、Taka「平均化の罠」と整合、v10.13.a 留保 #33 の Atom レベル一般化 | **Web Claude Phase Result で解釈統合** |

### 7.4 留保関連の観察事項

#### 観察 2 §2.3 atom entropy Δt 単調減少の解釈留保

- 観察事実: Δt=-100 → +100 で entropy 2.138 → 2.070 bits 単調減少
- 解釈候補 (留保): 取り込み独立効果 vs 自然動学 vs selection bias
- 段階 2 で randomized baseline (取り込み時刻を ランダムシャッフル) と比較で検証可能

#### 観察 2 §2.4 PRP.bright Δt=-90 peak の解釈留保

- 観察事実: PRP.bright center_match_rate peak 49.3% at **Δt=-90** (取り込み 前)
- 解釈候補 (留保): selection bias の兆候 (事前にすでに PRP.bright だった cid に PRP.bright が取り込まれた可能性)
- 段階 2 で取り込み時刻と中心 cid の事前 atom 状態の独立性検証可能

### 7.5 Code A 認識確認連続段階 (本 v1101 で 10 段階継続)

| 連続段階 | 内容 |
|---:|---|
| 1-2 | v110 Step A + Step J (v10.10) |
| 3 | v112 認識確認 v1/v2 (v10.12) |
| 4 | v113a Step A (v10.13.a) |
| 5-6 | v1100 Step A + Step J (v11.0.0) |
| 7 | v1101 Step A (旧 v1102 として作成、Step A 番号修正で v1101 確定) |
| 8 | v1101 Step B (環境チェック) |
| 9 | v1101 Step C-F (観察 1-3 + グラフ HTML) |
| 10 | **v1101 Step G + Step H (本書、bit-identity + 観察事実最終総括)** |

→ Code A 認識確認連続 **10 段階継続中**、本 Step H で v1101 主題の Code A 担当範囲完了。

---

## 8. 出力ファイル総覧 (`unified/v1101/`)

### 8.1 Step 報告書 (markdown, 9 ファイル)

| ファイル | サイズ | 内容 |
|---|---:|---|
| v1101_step_a_recognition.md | ~25 KB | Step A 認識確認 (齟齬 10 件) |
| v1101_step_b_environment_check.md | ~12 KB | Step B 環境チェック |
| v1101_step_c_report.md | ~14 KB | Step C 観察 1 報告 |
| v1101_step_d_report.md | ~16 KB | Step D 観察 2 報告 |
| v1101_step_e_report.md | ~17 KB | Step E 観察 3 報告 |
| v1101_step_f_report.md | ~10 KB | Step F グラフ HTML 報告 |
| v1101_step_g_report.md | ~12 KB | Step G bit-identity 報告 |
| **v1101_step_h_observation_final.md** | (本書) | Step H 観察事実最終総括 |

### 8.2 実装スクリプト (python, 4 ファイル)

| ファイル | サイズ | 内容 |
|---|---:|---|
| v1101_step_c_observation_1.py | ~6 KB | 観察 1 中心 cid 選定 + trajectory + 集計 |
| v1101_step_d_observation_2.py | ~5 KB | 観察 2 波及指標算出 |
| v1101_step_e_observation_3.py | ~6 KB | 観察 3 3 単位集計 |
| v1101_step_f_graph_html.py | ~10 KB | 観察 1/2/3 統合 HTML 生成 |
| v1101_step_g_bit_identity.py | ~5 KB | bit-identity 3 層検証 |

### 8.3 観察データ (parquet, 10 ファイル + JSON 1)

| ファイル | サイズ | 内容 |
|---|---:|---|
| `outputs/main/observation_1_center_cids.parquet` | 5.9 KB | 中心 cid 48 |
| `outputs/main/observation_1_random_cids.parquet` | 3.9 KB | ランダム比較対照 240 |
| `outputs/main/observation_1_trajectory.parquet` | 5.5 MB | 4 解像度 trajectory 374,072 行 |
| `outputs/main/observation_1_summary.parquet` | 72 KB | cid 別集計 1,094 行 |
| `outputs/main/observation_2_events.parquet` | 165 KB | 取り込み点 10,500 events |
| `outputs/main/observation_2_propagation.parquet` | 1.1 MB | per (event × Δt) 220,500 行 |
| `outputs/main/observation_2_summary.parquet` | 19 KB | per (atom × Δt) 525 行 |
| `outputs/main/observation_3_cid_atom_distribution.parquet` | 35 KB | 326 atom × 14 統計 |
| `outputs/main/observation_3_integration_summary.parquet` | 5.8 KB | β/α 集計 17 行 |
| `outputs/main/observation_3_esde_aggregate.parquet` | 17 KB | 4 解像度 × atom 225 行 |
| `outputs/v1101_step_g_bit_identity_report.json` | ~5 KB | bit-identity 検証結果 |

### 8.4 グラフ HTML (1 ファイル)

| ファイル | サイズ | 内容 |
|---|---:|---|
| `outputs/v1101_observation.html` | 954 KB | 5 figure + 4 section dashboard |

**合計**: **25 ファイル、約 7 MB**、書き込み全て `unified/v1101/` 配下のみ、v10.x main outputs 1,306 ファイル不変。

---

## 9. 累計 commit (8 件)

| commit | Step | 内容 |
|---|---|---|
| 0bc21b3 | (Step A 初版) | v11.0.2 として作成、齟齬 10 件指摘 |
| **127d65d** | (Step A 修正) | v11.0.2 → v11.0.1 番号修正、即決事項 7 件反映 |
| **db2bf45** | Step B | 環境チェック完了、観察 1/2/3 必要データ全所在確定 |
| **8b21637** | Step C | 観察 1「一点を捉える」段階 1 完了 |
| **bea48a0** | Step D | 観察 2「取り込み点中心の波及」完了 |
| **56f5ae6** | Step E | 観察 3「補助平均統計 3 単位」完了 (核心発見: 観察単位 reversal) |
| **8315601** | Step F | グラフ HTML 統合完了 (954 KB dashboard) |
| **2e468d2** | Step G | bit-identity 3 層全 PASS |

---

## 10. 規律遵守総括 (絶対格言 15 件、本 v1101 全 Step 通算)

| # | 格言 | 本 v1101 全 Step での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 全 Step で構造的事実先、解釈は留保候補で記述 |
| 2 | 物理層 frozen 絶対 | ✓ Step G 層 B で v10.x main outputs 1,306 ファイル不変確認、全 Step で遵守 |
| 3 | ベースライン比較 + 効果サイズ | ✓ 観察 1 で中心 vs ランダム比較、観察 2 で Δt baseline、観察 3 で観察単位間比較 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ 観察 3 核心発見 (観察単位反転) が本格言の生きた実例 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ Step A §0.2 + Step E で観察フレーム転換明示、新規軸なし |
| 6 | 出口の固定 | ✓ 各 Step で出口物固定、本 Step H で全観察事実総括 |
| 7 | 主題着手前に上位資料を読む | ✓ Step A で v1100 + v10.6-v10.13.a 既存出力照合、Step B で v105 グラフ HTML 把握 |
| 8 | 過去観察軸の照会 | ✓ Step A §2 で過去観察軸照会、Step C-E で v10.6 既存出力流用 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ rng seed=42 固定、argmax / groupby / pivot のみ、Step G 層 C で構造的検証 |
| 10 | 因果ではなく因果候補 | ✓ 全 Step で「~の可能性」「留保解釈候補」表現、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ 中心 / 周辺 / 取り込み atom / rank_1_atom / β / α / pattern_class / 解像度を全 Step で区別 |
| 12 | Aruism 判定回避 | ✓ 全 Step で success/fail なし、解釈統合は Web Claude 領域明示 |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Code A は構造的事実のみ、Web Claude / Taka 即決事項受領 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka 整理 (2026-05-12 3 日長考 + 2026-05-16 具体化 + Step A/B/C/D/E/F/G 承認) 全反映 |
| 15 | 5 者運用体制の補完性 | ✓ Code A 認識確認連続 10 段階継続、Web Claude 即決事項受領 7 件、Taka 承認 7 件 |

→ **絶対格言 15 件全項目遵守**。本 v1101 主題の Code A 担当範囲は本 Step H で完了、Web Claude Phase Result + Taka 主題評価を待つ。

---

## 11. Step I (任意、段階 2) + Step J (Web Claude Phase Result) 推奨

### 11.1 Step I 進行案 (任意、Code A 段階 2)

| Sub-step | 内容 | 想定時間 | 主要解消対象 |
|---|---|---|---|
| I-1 | cid state ledger 再生 (v10.6/v10.12 ledger から t 別 cid vector 構築) | 半日 | 留保 #41 candidate (Integration member_cids list 再生) |
| I-2 | cid vector 326 atom 全時系列再計算 (4 解像度) | 半日 | 観察 1 段階 2 (rank 2 以降の atom も含む全濃度時系列) |
| I-3 | Integration member_cids 完全 atom ベクトル分布算出 | 1-2 時間 | Web Claude 改訂版 §3.3 想定の解像度向上 |
| I-4 | atom entropy 取り込み独立効果 vs 自然動学の randomized baseline 検証 | 半日 | 観察 2 留保 §7.4 |
| I-5 | Step I 報告 + commit + push | 30 分 | — |

→ Step I 合計 **約 1.5-2 日** (半日-1 日 × 4 sub-step)、Taka 主題評価次第。

### 11.2 Step J 進行案 (Web Claude Phase Result)

Code A は Step H までで完了、Step J は **Web Claude 担当**:

- 観察 1/2/3 + Step G の主要発見 を ESDE Atom 隆盛の解釈として統合
- 核心発見 (観察単位による dominant atom 反転) を「ESDE は Atom 的にこうなっているようだ」の記述に変換
- 留保 #41/#42 candidate の formal 化
- Taka 主題評価判断材料の提供

→ 想定: Web Claude 1-2 日。

---

## 12. 一文サマリ (再掲)

v11.0.1 (v1101) Code A 主題「Atom 的隆盛の統計的観察」が Step A 認識確認 → Step G bit-identity 全 PASS まで **全 8 段階完了** (累計 commit 8 件)、観察 1 (中心 cid 48 + ランダム 240 + 4 解像度 trajectory 374,072 行) + 観察 2 (受容 cid pool 420 由来 取り込み 10,500 events × Δt 21 点 = 220,500 行) + 観察 3 (CID 326 atom + Integration β/α + ESDE 4 解像度) を構造的算出、**核心発見** = 観察単位による dominant atom 反転 (CID-static `CHG.begin` / β `FND.logic` / α `TIM.moment` / ESDE event `WLD.artless+PER.sound` / step10 `PER.sound` / window `TIM.moment` の 5 atom 分裂、Taka「平均化の罠」生きた実例)、観察 2 副発見 = 25 取り込み atom 中 4 atom のみ中心 cid 支配可 (PER.sound peak 84.8%) + 周辺 cid 60% 占有が PER.sound + WLD.artless + atom entropy Δt 単調減少、観察 1 副発見 = v108_standard 中心 cid dominant WLD.artless 21/24 seeds + window 解像度の一点特徴、Step F グラフ HTML 単一 954 KB ダッシュボード化 (Taka ブラウザ表示可)、Step G bit-identity 3 層全 PASS (deterministic 動作 + v10.x main outputs 1,306 ファイル不変 + 構造的書き込み制限 unified/v1101/ 配下のみ)、新規留保 #41 candidate (Integration member_cids 個別 list 未 persistence、段階 2 で cid state ledger 再生対応) + #42 candidate (観察単位反転、Web Claude 解釈統合領域)、絶対格言 15 件全項目遵守 (Code A 判定回避、解釈統合は Web Claude)、書き込み unified/v1101/ 配下 25 ファイル 7 MB、v10.6/v10.8/v10.12 main outputs 1,306 ファイル frozen 完全保証、Code A 認識確認連続 10 段階継続、本 Step H で v1101 主題の Code A 担当範囲完了、Step I (任意段階 2) または Step J (Web Claude Phase Result)、Taka 主題評価判断を待つ。

---

*以上、v11.0.1 (v1101) Step H 観察事実最終報告 (Code A、2026-05-17)。本書で v1101 主題の Code A 担当範囲完了。Web Claude Phase Result + Taka 主題評価を待つ。任意 Step I (段階 2、cid state ledger 再生 + 留保 #41 解消、想定 1.5-2 日) は Taka 承認次第。Code A 認識確認連続 10 段階継続中。*
