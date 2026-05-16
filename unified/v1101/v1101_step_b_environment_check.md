# v11.0.1 (v1101) Step B 環境チェック報告 — Code A

*作成*: 2026-05-17、Code A
*親*: `v1101_phase_design.md` (Web Claude 2026-05-16 改訂版) + `v1101_step_a_recognition.md` (Code A、即決事項受領済) + Taka Step B 進行承認 (2026-05-17)
*対象*: Web Claude (相談役) + Taka (確認)
*目的*: Step C-F 着手前の実環境完全性確認 (read-only) + 観察 1/2 必要データ所在確定 + v105 グラフ HTML 構造把握

---

## 0. 一文サマリ

Step B 環境チェック完了 (read-only、書き込みなし、所要 5 分)、観察 1/2/3 の必要データは全て v10.6/v10.8/v10.12 main outputs 内に存在し新規 main run 不要、cid_atom_sim_matrix + 4 解像度 trajectory (event/pulse/step10/window_cid_alignment) + beta/alpha_atom_aggregate + 観察 2 用 atom_introduction_events_v112/v108_standard + 観察 1 用 propagation_profile_v112/v108_standard が **全て 24 seeds 揃って存在**、観察 1 中心 cid 選定基準 (Taka 確定 (c) n_pulses_short 最大 cid 主 + (d) ランダム比較対照) は propagation_profile から source_cid 別 max(n_pulses_short) で per-seed 選定可能、観察 2 中心 (Taka 確定 (a) v10.12 受容 cid pool 420) は atom_introduction_events_v112_seed{N}.parquet の source_cid + timestamp で per-seed 取得可能 (per-seed 400 行 = 16 cids × 25 atoms 平均、seed 0 確認)、v105 グラフ HTML 8 ファイルの構造は Plotly Figure + go.Frame アニメーション + slider + write_html(include_plotlyjs="cdn") で単一 HTML 出力 (v105_animate_grid.py 確認、v105_3layer_all_seeds.html 53MB / v105_grid_seed22.html 833KB の規模幅)、Step F グラフ HTML はこの pattern 踏襲、絶対格言 15 件遵守、書き込みなし、Step C 着手判断材料を本書に整理。

---

## 1. 観察 1/2/3 必要データの所在確認

### 1.1 v10.6 既存出力 (24 seeds 完全性確認)

| 出力 | 所在 | 24 seeds 揃い | 用途 |
|---|---|:-:|---|
| `cid_atom_sim_matrix_seed{0..23}.parquet` | `developmental/v106/outputs/main/` | ✓ 24 | 観察 3 CID 単位 (静的 326 atom 濃度)、観察 1 段階 2 (cid vector 再計算の基準) |
| `event_trajectory/event_cid_alignment_seed{0..23}.csv` | `.../main/event_trajectory/` | ✓ 24 | 観察 1 段階 1 (per-cid per-event 時系列、rank_1_atom + rank_1_sim) |
| `pulse_trajectory/pulse_cid_alignment_seed{0..23}.csv` | `.../main/pulse_trajectory/` | ✓ 24 | 観察 1 段階 1 (per-cid per-pulse 時系列、`pulse_n` 累計あり) |
| `step10_trajectory/step10_cid_alignment_seed{0..23}.csv` | `.../main/step10_trajectory/` | ✓ 24 | 観察 1 段階 1 (per-cid per-10step 時系列) |
| `window_trajectory/window_cid_alignment_seed{0..23}.csv` | `.../main/window_trajectory/` | ✓ 24 | 観察 1 段階 1 (per-cid per-window 時系列) |
| `beta_atom_aggregate_seed{0..23}.csv` | `.../main/` | ✓ 24 | 観察 3 Integration 単位 (β top-K 集約、本主題で完全分布化) |
| `alpha_atom_aggregate_stratified_seed{0..23}.csv` | `.../main/stratified/` | ✓ 24 | 観察 3 Integration 単位 (α pattern_class top-K 集約、本主題で完全分布化) |

→ **v10.6 全 7 出力タイプ × 24 seeds = 168 ファイル揃い**、観察 1/3 の段階 1 素材は完備。

### 1.2 観察 1 中心 cid 選定 (Taka 確定 (c) n_pulses_short 最大 + (d) ランダム比較対照)

| 出力 | 所在 | 24 seeds | 用途 |
|---|---|:-:|---|
| `propagation_profile_v112_seed{0..23}.parquet` | `developmental/v112/outputs/main/` | ✓ 24 | per-event の `n_pulses_short` + `source_cid` + `target_step` (per seed 400 行) |
| `propagation_profile_v108_standard_seed{0..23}.parquet` | `developmental/v112/outputs/main/` | ✓ 24 | per-event の `n_pulses_short` + `source_cid` + `target_step` (per seed ~2,500 行) |

#### 1.2.1 propagation_profile 構造 (seed 0 v112、実測)

```
shape: (400, 27)
key cols: ['event_id', 'n_pulses_short', 'source_cid', 'timestamp', 'atom_id',
           'delta_C_medium', 'delta_Q_medium', 'target_step', 'death_step',
           'n_core_bin', 'formation_relation', 'n_core', 'lifespan', 'fam_max']
example: source_cid=22, atom_id=PRP.deep, target_step=222, n_pulses_short=1.7196
```

#### 1.2.2 観察 1 中心 cid 選定アルゴリズム (Code A 提案)

```
per seed:
  df = propagation_profile_v112_seed{N}.parquet (or v108_standard)
  per source_cid:
    cid_n_pulses_short = max(df[df.source_cid == cid].n_pulses_short)
  center_cid_main = argmax(cid_n_pulses_short)  # (c) n_pulses_short 最大
  center_cid_random = sample(cid_pool, k=3-5)   # (d) ランダム比較対照
```

主候補 (Code A 仮所見): v112 (受容 cid pool 420 内) と v108_standard (5,111 unique cid) で **両方算出** + 結果を併記、Web Claude 翻訳で取捨選択。

### 1.3 観察 2 取り込み点中心 (Taka 確定 (a) v10.12 受容 cid pool 420)

| 出力 | 所在 | 24 seeds | 用途 |
|---|---|:-:|---|
| `atom_introduction_events_v112_seed{0..23}.parquet` | `developmental/v112/outputs/main/` | ✓ 24 | 受容 cid pool 420 (per-seed mean 17.5) の発火点 (source_cid + timestamp + atom_id) |
| `atom_introduction_events_v108_standard_seed{0..23}.parquet` | `developmental/v112/outputs/main/` | ✓ 24 | top_k_100 cid pool 5,111 unique の発火点 (比較対照) |

#### 1.3.1 atom_introduction_events_v112 構造 (seed 0、実測)

```
shape: (400, 36)
key cols: ['source_cid', 'timestamp', 'atom_id', 'atom_index',
           'event_id', 'birth_step', 'lifespan_so_far', 'n_core_member',
           'Q_pre', 'C_pre', 'Q_after_atom_intro', 'C_after_atom_intro',
           'window_value', 'C_at_window_end', 'Q_remaining_at_window_end',
           'R_familiarity_pre', 'n_alphas_pre', 'n_observed_pre',
           'target_step', 'death_step', 'n_core', 'n_core_bin',
           'formation_relation', 'lifespan', 'fam_max', 'top_50_threshold',
           'condition_id', 'seed']
example: source_cid=0, timestamp=200, atom_id=BOD.ear, target_step=200,
         Q_pre=13, C_pre=24, Q_after=12, C_after=25
```

→ **取り込み点 = (source_cid, timestamp) のペア、per seed 400 events (≈ 16 cids × 25 atoms 平均)**。state before/after も同 row に記録、波及観察の起点として完備。

### 1.4 観察 2 周辺 cid 定義

Taka 確定: (a) 受容 cid pool 中心、(b) atom 濃度近接は **不採用**。残る選択肢:

| 選択肢 | 内容 | 既存出力 |
|---|---|---|
| (a) 物理近接 | リンク接続 (genesis 物理層の neighbor) | 物理層 ledger 要参照 |
| (c) 同 Integration | 同 α / β に属する member cid | beta/alpha_atom_aggregate の member 情報 |
| (default Code A 仮所見) | 同 seed の全 cid (228 cid per seed) を周辺と定義し中心 cid との関係を可視化 | cid_atom_sim_matrix |

→ 観察 2 「周辺 CID」の定義は Web Claude 改訂版 §3.5 論点 4 で 2 AI 監査対象。**Code A は Step D で同 seed 全 cid (228) を「周辺」とし、中心 cid と atom 状態の同期/差異を観察** することを仮提案、Step D 着手前に Web Claude 確認要請。

### 1.5 観察 3 平均統計 (補助、3 単位)

| 単位 | 既存出力 | 段階 1 で算出可能 |
|---|---|---|
| CID 単位 | cid_atom_sim_matrix × 24 seeds | 全 cid の 326 atom 濃度プロファイル統計 |
| Integration 単位 | beta_atom_aggregate (β) + alpha_atom_aggregate_stratified (α pattern_class) | top-K 既存 + member_cids 全 atom ベクトル分布への解像度向上 |
| ESDE 単位 | cross_seed_event_step_evolution + cross_seed_event_atom_distribution + cross_seed_dynamic_atom_emergence | 24 seeds 横断の atom 動学 |

---

## 2. v10.12 受容 cid pool の取得経路 (観察 2 中心)

Taka 確定「観察 2 中心 = (a) 受容 cid pool 420」の取得方法:

```
per seed:
  df = atom_introduction_events_v112_seed{N}.parquet
  receptive_cids = df['source_cid'].unique()  # per-seed 13-23 cid (mean 17.5)

24 seeds 統合:
  total_receptive = ⋃ (per-seed receptive_cids) = 420 unique observations
  (注: cid id は seed 間で独立、cid_seed12_42 は cid_seed13_42 と別物)
```

→ **受容 cid pool は atom_introduction_events_v112 から派生取得、別ファイル不要**。

---

## 3. v105 グラフ HTML 構造の把握 (Step F グラフ設計)

### 3.1 v105 グラフ HTML 8 ファイル一覧 + サイズ

| ファイル | サイズ | 内容 (推定) |
|---|---:|---|
| `v105_grid_seed22.html` | 833 KB | 71×71 トーラスグリッド × β-Integration、seed 22 単独 |
| `v105_grid_all_seeds.html` | 14 MB | 同 24 seeds 全部 |
| `v105_3layer_seed22.html` | 5.2 MB | 3 層 (cid/α/β?) アニメーション、seed 22 |
| `v105_3layer_all_seeds.html` | 53 MB | 同 24 seeds |
| `v105_compare_seed22.html` | 2.5 MB | 比較ビュー、seed 22 |
| `v105_compare_all_seeds.html` | 43 MB | 同 24 seeds |
| `v105_integration_seed22.html` | 1.7 MB | Integration ビュー、seed 22 |
| `v105_integration_all_seeds.html` | 29 MB | 同 24 seeds |

### 3.2 v105 グラフ HTML 構造 (`v105_animate_grid.py` 実測)

技術スタック:
- **Plotly.js 3.5.0** (CDN 経由、`include_plotlyjs="cdn"`)
- `plotly.graph_objects.Figure` + `go.Frame` でアニメーション
- Slider widget で時間 window 移動
- 単一 HTML ファイル出力 (`fig.write_html(out_path, include_plotlyjs="cdn")`)

実装 pattern:
```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(...))  # initial trace

plotly_frames = []
for window in tracking_windows:
    plotly_frames.append(go.Frame(
        data=[go.Scatter(...)],
        name=f"window_{window}"
    ))
fig.frames = plotly_frames

fig.update_layout(
    updatemenus=[{...}],  # play/pause button
    sliders=[{...}]  # window navigation slider
)
fig.write_html(out_path, include_plotlyjs="cdn")
```

### 3.3 Step F グラフ HTML への踏襲設計 (Code A 提案)

| 観察 | グラフ形式 (Code A 仮所見) |
|---|---|
| 観察 1 「一点」 | 中心 cid (n_pulses_short 最大) の atom 状態時系列、x=t、y=rank_1_sim or top-K atom 濃度 (折れ線 + slider で粒度切替) |
| 観察 2 「取り込み点中心」 | 中心 cid + 周辺 cid (同 seed 全 228 cid) の atom 状態を 2D 散布図 + slider で時間進化、atom_introduction_event 発火点を marker でハイライト |
| 観察 3 補助 | 3 単位の atom 濃度ヒートマップ or barchart (時間軸なし or 集約) |

出力規模見積もり: seed 22 単独で <5 MB、24 seeds 全部で 50-100 MB (v105 範囲内、storage 圧迫なし)。

---

## 4. 物理層 frozen 絶対 (絶対格言 #2) 遵守確認

### 4.1 read-only 確認 (本 Step B では書き込みなし)

| 対象 | 読み取り | 書き込み |
|---|:-:|:-:|
| `developmental/v106/outputs/main/**` | ✓ (ls + sample read) | ✗ |
| `developmental/v108/outputs/main/**` | ✓ (ls) | ✗ |
| `developmental/v112/outputs/main/**` | ✓ (ls + sample read) | ✗ |
| `developmental/v105/*.html` | ✓ (peek + script grep) | ✗ |
| `unified/v1101/` | (本書作成のみ) | ✓ |

### 4.2 Step C 以降の書き込み計画

書き込みは **`unified/v1101/outputs/` 配下のみ**:
- `unified/v1101/outputs/main/observation_1_*.parquet` (per-cid 時系列)
- `unified/v1101/outputs/main/observation_2_*.parquet` (取り込み点中心の波及)
- `unified/v1101/outputs/main/observation_3_*.parquet` (3 単位平均統計)
- `unified/v1101/outputs/v1101_observation.html` (Step F グラフ HTML)
- `unified/v1101/outputs/smoke/` (Step G bit-identity 検証用)

bit-identity 層 A (smoke 2 回実行 hash 一致) + 層 B (v10.x main outputs 全 mtime+size 不変) + 層 C (構造的書き込み制限 `unified/v1101/` 配下のみ) は Step G で保証。

---

## 5. Step C 進行案 (Code A 推奨、Step B 結果反映)

| Step | 内容 | 想定時間 | 主な入力 | 出力 |
|---|---|---|---|---|
| Step C-1 | 観察 1 主 (n_pulses_short 最大 cid) per-seed 選定 | 30 分 | propagation_profile_v112 (24 seeds) | `unified/v1101/outputs/observation_1_center_cids.parquet` |
| Step C-2 | 観察 1 主 cid の 4 解像度 atom 時系列抽出 | 30 分 | 4 解像度 trajectory (24 seeds) | `observation_1_center_trajectory.parquet` |
| Step C-3 | 観察 1 副 (ランダム比較対照、各 seed 3-5 cid) | 20 分 | 同上 + 構造的 sample | `observation_1_random_trajectory.parquet` |
| Step C-4 | 観察 1 観察事実集計 (rank_1_atom 方向反転回数 + rank_1_sim 分散 + 中心 vs ランダム 比較) | 30 分 | C-2 + C-3 | `observation_1_summary.parquet` |

→ **Step C 合計時間 ~2 時間**、観察 1 段階 1 (rank 1 既存値のみ、326 atom 全濃度時系列は段階 2 で別途) 完成。

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step B での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 実環境照合 (§1-3) を先、解釈 (§5) は構造記述 |
| 2 | 物理層 frozen 絶対 | ✓ §4 で read-only 完全保証、書き込みなし |
| 3 | ベースライン比較 + 効果サイズ | △ Step C で観察 1 主 vs ランダム比較を計画 (§5 C-4) |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ §1.5 で Integration 観察を「top-K → 完全分布」解像度向上として明示 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ §1-2 で既存出力流用のみ、新規観察軸なし |
| 6 | 出口の固定 | ✓ §5 で Step C-1〜C-4 の 4 出口物を固定 |
| 7 | 主題着手前に上位資料を読む | ✓ v1101_phase_design.md (Web Claude 改訂版) + v1101_step_a_recognition.md (即決事項) を反映 |
| 8 | 過去観察軸の照会 | ✓ §1.1-1.4 で v10.6/v10.8/v10.12 既存出力を実環境照合済 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ §1.2.2 で構造的選定 (argmax) を採用、ハンドチューニングなし |
| 10 | 因果ではなく因果候補 | ✓ §3.3 グラフ設計は仮所見、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ source_cid / cid pool / 受容 cid / β-Integration / α pattern_class を §1-2 で区別 |
| 12 | Aruism 判定回避 | ✓ success/fail なし、観察事実所在のみ |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Code A は実環境照合結果のみ報告 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka 確定 ((c)+(d) / (a) / (b)不採用) を §1.2/1.3/1.4 で反映 |
| 15 | 5 者運用体制の補完性 | ✓ §1.4 観察 2 周辺 cid 定義の論点 4 を Web Claude 確認要請 |

→ **15 格言全項目遵守** (#3 は Step C で適用予定)。

---

## 7. Web Claude / Taka 確認要請 (Step C 着手前、small)

### 7.1 確認要請 1: 観察 1 中心 cid の cid pool 選択

Taka 確定 (c) n_pulses_short 最大 cid に関して、対象 cid pool は:
- (i) v112 受容 cid pool 420 内 (per-seed 13-23 cid から最大)、または
- (ii) v108_standard top_k_100 5,111 cid 内 (per-seed 213 cid から最大)、または
- (iii) 両方併記 (per seed 2 中心 cid × 24 seeds = 48 中心 cid 観察)

**Code A 仮所見**: (iii) 両方併記が情報量最大、Step C 作業時間+30 分。Web Claude/Taka 判断要請。

### 7.2 確認要請 2: 観察 2 「周辺 CID」の定義 (論点 4)

Taka 確定で (b) atom 濃度近接は不採用。残る選択肢:
- (a) 物理近接 (genesis 物理層 neighbor、ledger 要参照)
- (c) 同 Integration (同 α / β の member cid)
- (Code A 仮所見) 同 seed の全 cid (228) を周辺として 2D 散布図

**Code A 推奨**: (Code A 仮所見) を Step D 段階 1 で採用、(a)+(c) は Step D 結果次第で段階 2 検討。Web Claude 判断要請。

### 7.3 確認要請 3: 観察 1 副ランダム比較対照の cid 数

Taka 確定「(d) ランダム比較対照」の per seed cid 数:
- (i) 3 cid (中心 1 + ランダム 3 = 4 比較)
- (ii) 5 cid (中心 1 + ランダム 5 = 6 比較)
- (iii) 10 cid (中心 1 + ランダム 10 = 11 比較)

**Code A 仮所見**: (ii) 5 cid を提案、計算負荷小・統計的多様性確保。Web Claude/Taka 判断要請。

### 7.4 Step C 進行判断

上記 #1-#3 が確定すれば Step C-1〜C-4 (合計 ~2 時間) で進行可能。確認待ち時間中、Step C-1 の per-seed argmax 算出は (iii) 両方併記 + (i) v112 単独の両方で実行し、結果比較する形でも可。

---

## 8. 一文サマリ (再掲)

Step B 環境チェック完了 (read-only、書き込みなし、所要 5 分)、観察 1/2/3 必要データは全て既存 outputs 内に存在 (v10.6 cid_atom_sim_matrix + 4 解像度 trajectory + beta/alpha_atom_aggregate × 24 seeds + v10.12 atom_introduction_events_v112 + propagation_profile_v112/v108_standard × 24 seeds + v10.8 atom_introduction_events_v108_standard × 24 seeds)、新規 main run 不要、観察 1 中心 cid 選定 ((c) n_pulses_short 最大 + (d) ランダム) は propagation_profile から source_cid 別 argmax で per-seed 算出可能、観察 2 中心 ((a) v10.12 受容 cid pool 420) は atom_introduction_events_v112_seed{N} の source_cid から派生 (別ファイル不要)、観察 2 周辺 cid 定義は Web Claude 論点 4 監査対象 (Code A 仮所見: 同 seed 全 228 cid を 2D 散布図で示す)、v105 グラフ HTML 8 ファイルの構造は Plotly.js 3.5 + go.Frame アニメーション + slider + write_html(include_plotlyjs="cdn") の単一 HTML 出力 pattern (v105_animate_grid.py 確認)、Step F グラフ HTML はこの pattern 踏襲、Step C-1〜C-4 進行案 (合計 ~2 時間で観察 1 段階 1 完成)、Web Claude/Taka 確認要請 3 件 (観察 1 cid pool 選択 / 観察 2 周辺 cid 定義 / 観察 1 副ランダム数)、絶対格言 15 件全項目遵守 (#3 は Step C で適用)、物理層 frozen 絶対 (v10.x main outputs read-only、書き込み unified/v1101/ 配下のみ予定)、確認要請返答後に Step C 着手。

---

*以上、v11.0.1 (v1101) Step B 環境チェック (Code A、2026-05-17)。Web Claude/Taka 確認要請 3 件 (small) を受領後、Step C-1 (観察 1 中心 cid 選定) に進む。Code A 認識確認連続 10 段階継続中。*
