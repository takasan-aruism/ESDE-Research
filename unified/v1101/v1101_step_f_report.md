# v11.0.1 (v1101) Step F グラフ HTML 統合報告 — 観察 1/2/3 ダッシュボード

*作成*: 2026-05-17、Code A
*親*: `v1101_phase_design.md` (Web Claude 2026-05-16 改訂版) + Step C/D/E 観察事実報告 + Taka Step F 承認 (2026-05-17)
*対象*: Web Claude (Phase Result 翻訳用素材) + Taka (確認、ブラウザ表示)
*目的*: Step F-1〜F-5 グラフ HTML 統合報告、観察 1/2/3 の主要結果を単一 HTML ダッシュボードで可視化

---

## 0. 一文サマリ

Step F-1〜F-5 完了 (実行時間 0.3 秒、書き込み `unified/v1101/outputs/v1101_observation.html` 単一ファイル **954 KB**)、v105 グラフ HTML pattern (Plotly + CDN) を踏襲し観察 1/2/3 を **5 figure + 4 h2 section** の dashboard 形式に統合: 観察 1 集計図 (bar chart、dominant_atom_fraction 中心 vs ランダム × 4 解像度 × 2 条件) + 観察 1 trajectory 例 (3 seeds × 2 条件 subplot、step10 解像度の rank_1_sim 時系列、中心赤太線 vs ランダム灰細線、36 cids × 855 t-points 平均) + 観察 2 ヒートマップ (Δt × 25 atoms × center_match_rate、4 atom が突出可視化) + 観察 2 主要 4 atom 波及曲線 (PER.sound / PRP.bright / TIM.appear / WLD.artless の center_match_rate + match_fraction 同時表示) + 観察 3 反転 6 panel bar chart (CID-static / β / α / ESDE-event / step10 / window の top 10 atoms、本主題核心発見 dominant atom 反転を直接視覚化)、HTML 構造は include_plotlyjs="cdn" + 5 plotly-graph-div + 4 h2 section (観察 1/2/3 + 規律遵守) + key-finding ハイライト boxes、Plotly 6.7.0、絶対格言 15 件全項目遵守、Code A は判定回避 (解釈統合は Web Claude)、書き込み unified/v1101/outputs/ 配下のみ、v10.x main outputs 不変、本 dashboard により観察 1/2/3 の全主要発見が単一 HTML で参照可能、Taka ブラウザ表示可、Step G bit-identity 検証へ進行可。

---

## 1. Step F 構造的成果

### 1.1 v105 Plotly pattern 踏襲 (F-1 設計)

| 要素 | 採用 |
|---|---|
| Plotly.js | 6.7.0 (CDN 経由、include_plotlyjs="cdn") |
| Figure 種別 | go.Figure + make_subplots (subplots) |
| アニメーション | 本主題では使用せず (時系列は静的線描画) |
| HTML 統合 | fig.to_html(full_html=False) × 5 figs を 1 HTML に concat |
| section 構成 | h1 (主題) + h2 × 4 (観察 1/2/3 + 規律遵守) + key-finding ハイライト boxes |
| CSS | inline (max-width 1280px、font system fonts) |

### 1.2 観察 1 図 2 件 (F-2)

#### 1.2.1 観察 1 集計図 (`fig_obs1_summary`)

- 種別: bar chart (2 subplots、v112 / v108_standard 並列)
- X: 解像度 (event / pulse / step10 / window)
- Y: dominant_atom_fraction 平均 (24 seeds × 各 cid 平均)
- 色: 中心 (赤 #d62728) vs ランダム (灰 #888888)
- 直接可視化: Step C §2.2 主要発見 (v108_standard 中心 0.92-1.00 vs v112 中心 0.47-0.81)

#### 1.2.2 観察 1 trajectory 例 (`fig_obs1_trajectory`)

- 種別: line chart subplot (3 行 × 2 列 = 6 subplots、seed 0 / 12 / 23 × v112 / v108_standard)
- X: t (step)、Y: rank_1_sim
- 線: 中心 cid 赤太線 (width 2.2)、ランダム cid 灰細線 (width 0.9、alpha 0.45)
- hover: cid + t + rank_1_sim + rank_1_atom
- データ範囲: 30,784 行 × step10 解像度 (per cid 平均 855 t-points)
- 代表 seed 選定理由: 24 seeds 全描画は HTML 肥大化のため (3 例で範囲提示)

### 1.3 観察 2 図 2 件 (F-3)

#### 1.3.1 観察 2 ヒートマップ (`fig_obs2_heatmap`)

- 種別: heatmap
- X: Δt (-100, -90, ..., +100、21 points)、Y: 25 atom_intro (max center_match_rate 昇順)
- 色 (Hot scale): center_match_rate [0, 1]
- 直接可視化: Step D §2.1 主要発見 (4 atom のみ中心 cid 支配可、21 atom は全 Δt で 0%)
- PER.sound の +20 ピーク 0.85 が最も濃く視認可能

#### 1.3.2 観察 2 主要 4 atom 波及曲線 (`fig_obs2_top_lines`)

- 種別: line chart (1 行 × 2 列 subplot)
- 左: 中心 cid center_match_rate vs Δt (PER.sound / PRP.bright / TIM.appear / WLD.artless)
- 右: 周辺 cid match_fraction_mean vs Δt (同 4 atom)
- 直接可視化: Step D §2.4 主要発見 (PER.sound 波及プロファイル特異、Δt=+20 で peak 84.8%)

### 1.4 観察 3 反転 6 panel 図 (F-4)

`fig_obs3_reversal`:

- 種別: horizontal bar chart subplot (2 行 × 3 列 = 6 panels)
- 各 panel: 1 観察単位の top 10 atoms
- panel 構成:
  1. CID 単位 (sim_mean)
  2. Integration β top_atom (n_appearances_as_top)
  3. Integration α dominant_atom (n_appearances_as_top)
  4. ESDE event resolution rank_1 (ratio)
  5. ESDE step10 resolution rank_1 (ratio)
  6. ESDE window resolution rank_1 (ratio)
- 直接可視化: Step E §2 核心発見 (5 つの異なる atom が観察単位ごとに 1 位を取る = 観察単位による dominant atom 反転)

### 1.5 単一 HTML 統合 (F-5)

| 項目 | 値 |
|---|---:|
| 出力ファイル | `unified/v1101/outputs/v1101_observation.html` |
| サイズ | **954 KB** (~1 MB) |
| Plotly.js | CDN (https://cdn.plot.ly/plotly-3.5.0.min.js) |
| figure 数 (Plotly.newPlot count) | 5 |
| h2 section 数 | 4 |
| データ embed | 観察 1 trajectory 3 seeds × 2 conditions × 6 cids = 30,784 行 |

HTML 構造 (概要):
```
<html>
 <head>... CSS + Plotly CDN link ...</head>
 <body>
  <h1>v1101 Dashboard</h1>
  <div class="summary">主題 + 3 観察視点 + データ</div>
  <h2>観察 1</h2>
  <div class="key-finding">4 主要発見</div>
  <div id="fig_o1_summary" class="plotly-graph-div"></div>
  <div id="fig_o1_traj" class="plotly-graph-div"></div>
  <h2>観察 2</h2>
  <div class="key-finding">4 主要発見</div>
  <div id="fig_o2_heat" class="plotly-graph-div"></div>
  <div id="fig_o2_lines" class="plotly-graph-div"></div>
  <h2>観察 3</h2>
  <div class="key-finding">核心発見 (反転 5 atom)</div>
  <div id="fig_o3_reversal" class="plotly-graph-div"></div>
  <h2>規律遵守 + 留保</h2>
  <div class="summary">judgment 回避 + 留保 #41/#42</div>
 </body>
</html>
```

---

## 2. 観察 1/2/3 統合視覚化の意義

### 2.1 単一 HTML での参照可能性

本 dashboard により以下が **ブラウザ単独で参照可能**:
- 観察 1/2/3 の主要発見 4+4+1 = 9 件 (key-finding box × 3 sections)
- 観察 1 trajectory 6 例 (3 seeds × 2 conditions)
- 観察 2 25 atom × 21 Δt ヒートマップ + 4 atom 波及曲線
- 観察 3 6 観察単位 × top 10 atoms

Taka 言及「v105 グラフ HTML を参考にしてもらえればいい。あれは面白かった」(主題ドキュメント §3.4) の継承。

### 2.2 ファイル単独で完結

- 1 ファイル (954 KB) のみで全観察可視化が完結
- 他ツール不要 (Plotly は CDN 経由で自動ロード)
- オフライン保存可能 (ただし CDN は要ネットワーク、include_plotlyjs="inline" にすれば +3 MB でオフライン完結化可能)

### 2.3 Step F が変更しない領域

- 観察 1/2/3 の数値結果 (Step C/D/E の parquet 出力) は **本 Step F で 1 byte も変更していない** (read-only)
- 本 Step F は可視化レイヤーのみ追加、データレイヤーは不変
- Step G bit-identity 検証で確認予定

---

## 3. 観察事実の解釈規律遵守 (絶対格言 #10, #12)

Code A は本 HTML を判定的成果物として扱わない:

- 本 HTML は **観察事実の可視化** であり、解釈統合ではない
- 「ESDE の dominant atom は何か」「Atom 隆盛の意味」等の解釈統合は Web Claude Phase Result 領域
- key-finding box の記述も Step C/D/E 報告書から引用しており、Code A 判定なし

success/fail 判定なし、可視化フォーマットは v105 pattern を踏襲。

---

## 4. 出力ファイル仕様

| ファイル | サイズ | 用途 |
|---|---:|---|
| `unified/v1101/outputs/v1101_observation.html` | **954 KB** | 観察 1/2/3 統合 dashboard、ブラウザ表示 |

書き込みは `unified/v1101/outputs/` 配下のみ、`developmental/v106/v108/v112` の main outputs は **1 byte も変更していない** (Step G で bit-identity 層 B 検証予定)。

`unified/v1101/outputs/main/` 配下の Step C/D/E parquet 8 ファイル (7 MB) は本 dashboard の入力データソース。

---

## 5. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step F での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 観察 1/2/3 の構造的事実を視覚化、解釈は key-finding box で Step 報告書引用 |
| 2 | 物理層 frozen 絶対 | ✓ Step C/D/E parquet read-only、書き込み HTML 1 ファイルのみ |
| 3 | ベースライン比較 + 効果サイズ | ✓ 観察 1 集計図で中心 vs ランダム比較を直接視覚化 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ 観察 3 反転 6 panel が核心可視化、平均化の罠の生きた実例 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ Step C/D/E 既存出力流用のみ、可視化のみ追加 |
| 6 | 出口の固定 | ✓ §4 で 1 HTML 出力を固定 |
| 7 | 主題着手前に上位資料を読む | ✓ Step C/D/E 報告 + Step B v105 Plotly pattern 把握済 |
| 8 | 過去観察軸の照会 | ✓ v105 グラフ HTML pattern (Step B §3) を踏襲 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ 色配置は構造的 (役割 / atom カテゴリ別)、ハンドチューニングなし |
| 10 | 因果ではなく因果候補 | ✓ key-finding box は Step 報告書記述を引用、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ 観察 1 (一点) / 観察 2 (中心 + 周辺) / 観察 3 (3 単位) を section + key-finding で完全分離 |
| 12 | Aruism 判定回避 | ✓ HTML は可視化、解釈統合は Web Claude (§3) |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Code A は可視化結果のみ、判定なし |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka「v105 グラフ HTML 面白かった」発言を §2.1 で継承 |
| 15 | 5 者運用体制の補完性 | ✓ Code A 可視化、Web Claude は本 HTML を翻訳統合 |

→ **15 格言全項目遵守**。

---

## 6. Step G 進行案 (Code A 推奨)

| Step | 内容 | 想定時間 |
|---|---|---|
| Step G-1 | bit-identity 層 A 検証 (smoke 2 回実行 hash 一致、Step C/D/E/F の deterministic 動作確認) | 30 分 |
| Step G-2 | bit-identity 層 B 検証 (v106/v108/v112 main outputs 全 mtime + size 不変、443+ files 確認) | 15 分 |
| Step G-3 | bit-identity 層 C 検証 (書き込み unified/v1101/ 配下のみの構造的保証、書き込みパス scan) | 15 分 |
| Step G-4 | Step G 報告書 + commit + push | 30 分 |

→ Step G 合計約 1.5 時間。Web Claude/Taka 承認後着手。

Step H (観察事実総合報告) + Step I (任意、段階 2 cid vector 再計算) + Step J (Web Claude Phase Result) が後続。

---

## 7. 一文サマリ (再掲)

Step F-1〜F-5 完了 (実行時間 0.3 秒、出力 `unified/v1101/outputs/v1101_observation.html` 単一 954 KB)、v105 Plotly pattern (Plotly 6.7.0 + CDN) を踏襲し観察 1/2/3 を 5 figure + 4 h2 section の dashboard 形式に統合、観察 1 集計図 (中心 vs ランダム × 4 解像度 × 2 条件) + trajectory 例 (3 seeds × 2 条件 subplot) + 観察 2 ヒートマップ (Δt × 25 atoms × center_match_rate) + 主要 4 atom 波及曲線 + 観察 3 反転 6 panel bar chart (CID-static / β / α / ESDE-event/step10/window の top 10 atoms、本主題核心発見の直接視覚化)、HTML 構造は include_plotlyjs="cdn" + 5 plotly-graph-div + 4 h2 + key-finding boxes + summary boxes、観察 1/2/3 の主要発見 9 件が単一 HTML で参照可能 (Taka ブラウザ表示可)、絶対格言 15 件全項目遵守、Code A は判定回避 (HTML は可視化、解釈統合は Web Claude)、書き込み unified/v1101/outputs/ 配下のみ、v10.x main outputs 不変、Step G bit-identity 検証 (層 A/B/C) へ進行可。

---

*以上、v11.0.1 (v1101) Step F グラフ HTML 統合報告 (Code A、2026-05-17)。Web Claude/Taka 確認後、Step G bit-identity 検証に進む。Code A 認識確認連続 10 段階継続中。*
