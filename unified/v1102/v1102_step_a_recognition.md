# v1102 Step A 認識確認 — Code A

*作成*: 2026-05-19、Code A
*親*: `v1102_phase_design.md` (Web Claude 設計書、2 AI 監査反映済) + Taka 配置承認 (2026-05-19)
*対象*: Web Claude (相談役) + Taka (実装着手判断)
*目的*: 設計書 §3.2 論点 5 (新規 main run 要否) + 事前齟齬一般の照合。既存出力で primary table が作れるかを実環境で確認し、実装着手前の判断材料を整理。

---

## 0. 一文サマリ

設計書 §3.2 論点 5 に対する Code A 実環境照合結果として、**v1102 primary table は既存出力のみで作成可能・新規 main run 不要** と確認、受け手構造軸 (Integration α/β は v1101a Step G `integration_composition_alpha/beta.parquet` 既存 + CID は v10.6 trajectory `n_core_member` 列 24 seeds 揃い 3,088 cids 全分布 = n=2 62.6% / n=5 20.1% で Taka 整理「2 ノード大半、5 ノードは情報量で強い」がデータで確認済 + ESDE 全体は v10.6 4 解像度 trajectory 既存) と時間スケール軸 (v10.7 `baselines_with_delta_seed{N}.parquet` に immediate/short/medium 完全揃い 5 metric × 3 粒度 = 15 列 + window は v10.6 trajectory window 軸) と応答軸 (v1101a 段階 1 `attention_emit/propagation/causality_*.parquet` + 段階 2 `cid_state_ledger_*.parquet` + `observation_c_predictability.parquet` の actual_predict_rate と lift) のすべてが揃い、際立ち掬い取り A primary は v10.7 effect size (delta_*_immediate/short/medium) + v1101a 観察 C の lift_over_baseline + Step G stratified_observation を構造的指標として閾値分布から選定可能、B secondary は v1101a 既存 emit (attention_candidate_id + causality_candidate_path_zscore + influence_candidate_count 等) の read-back で新規 emit 機構不要、事前齟齬 3 件 (1) 設計書 §2.2 「CID は n_members」は repo 実装名で `n_core_member` (v10.6 trajectory 列)、命名整合明示要 (2) Integration α n_members は Step G で確認した v105 alpha_membership_log 由来の '|' 区切り cid 数 (Step G 命名と一致、整合) (3) primary input atom_introduction_event は v10.8 standard と v10.12 (v112) の 2 系統あり段階 2 で v108_standard (224 cids、attention_candidate 98.7% カバー) を採用済、v1102 でも踏襲が自然、Web Claude/Taka 確認要請 2 件 (応答指標の重み付けと時間スケール × 受け手構造の per-cell サンプル数下限) を §5 で整理、想定実装 1-1.5 日 (既存出力流用、新規 main run なし)。

---

## 1. 設計書 §3.2 論点 5 への回答 — 新規 main run 不要

### 1.1 既存出力で primary table 作成可能性確認

設計書 §3.2 論点 5「既存出力 (atom_introduction_event + v1101a attention 系 + Step G 層化) だけで primary table が作れるか」への Code A 回答: **作れる、新規 main run 不要**。

| 軸 | 既存出力 | 場所 |
|---|---|---|
| **入力** atom_introduction_event | v108_standard 24 seeds (per seed ~2,500 events / 224 cids、attention_candidate 98.7% カバー) | `developmental/v112/outputs/main/atom_introduction_events_v108_standard_seed{N}.parquet` |
| **受け手構造軸 Integration α** | n_members + qc_gini 24 seeds | `unified/v1101a/outputs/main/integration_composition_alpha.parquet` (11,799 rows) |
| **受け手構造軸 Integration β** | n_members + qc_gini 24 seeds | `integration_composition_beta.parquet` (341 rows) |
| **受け手構造軸 CID** | n_core_member 列 per (cid, window) | `developmental/v106/outputs/main/window_trajectory/window_cid_alignment_seed{N}.csv` |
| **受け手構造軸 ESDE 全体** | 4 解像度 trajectory | v106 event/pulse/step10/window cid_alignment |
| **時間スケール軸 immediate/short/medium** | 5 metric × 3 粒度 = 15 列、24 seeds | `developmental/v107/outputs/main/baselines_with_delta_seed{N}.parquet` |
| **時間スケール軸 window** | window 列 | v106 trajectory |
| **応答** attention trajectory | per (cid, window, scope, metric_type) | `unified/v1101a/outputs/main/attention_emit_seed{N}.parquet` (24 seeds) |
| **応答** 影響波及 | influence_candidate_count | `attention_propagation_seed{N}.parquet` (24 seeds) |
| **応答** 因果候補 | causality_path_sum / _zscore | `attention_causality_seed{N}.parquet` (24 seeds) |
| **応答** 326 atom 全濃度時系列 | 段階 2 cid state ledger (a) 簡易版 | `cid_state_ledger_seed{N}.parquet` (175,200 rows) |
| **応答** 揺れ幅 (variability) | 段階 2 観察 C lift | `observation_c_predictability.parquet` (432 rows) |
| **応答** 構成層化 | Step G stratified | `stratified_observation_integration.parquet` (19 rows) |

→ **すべて既存、24 seeds 揃い、post-process のみで primary table 構築可能**。

### 1.2 設計書 §2.2 「CID n_members」の実装名確認 (事前齟齬 1)

設計書 §2.2 表で CID の軸として「n_members (構成ノード数)」と書かれているが、repo 実装では `n_core_member` (v10.6 trajectory 列) が該当。命名差は同一物の別名表記。

Taka 整理「2 ノードが大半、5 ノードは情報量で強い」を 24 seeds で確認:

| n_core_member | n cids | 占有率 |
|---:|---:|---:|
| 2 | 1,932 | **62.6%** ← Taka「2 ノードが大半」確認 |
| 3 | 228 | 7.4% |
| 4 | 303 | 9.8% |
| 5 | 622 | **20.1%** ← Taka「5 ノードは情報量で強い」確認 |
| 6 | 1 | 0.03% |
| 7 | 1 | 0.03% |
| 8 | 1 | 0.03% |
| **total** | **3,088** | mean 2.88 / median 2.0 |

→ Taka 整理通り、CID の構成は **n=2 圧倒** + **n=5 次点 (20.1%)** + 他は稀。n_core=5 のクラスタが 622 cids あり、層化観察として十分なサンプル数。

### 1.3 Integration α n_members の整合 (事前齟齬 2)

設計書 §2.2 「Integration α n_members × qc_gini」は Step G の既存命名と完全一致 (`v105 alpha_membership_log` 由来の '|' 区切り cid 数)。整合性 OK。

| Integration | n_members 分布 (24 seeds) |
|---|---|
| α | n=1: 49.6% / n=2: 38.7% / n=3: 9.9% / n=4+: 1.8% |
| β | n=1: 73.6% / n=2-3: 15.5% / n=4+: 10.9% |

### 1.4 primary input の v108_standard 採用根拠 (事前齟齬 3)

`atom_introduction_event` には v10.8 standard (per seed ~2,500 events / 224 unique cids) と v10.12 = v112 (per seed 400 events / 16 受容 cids) の 2 系統がある。

| ファイル | per seed events | unique cids | attention_candidate 重なり率 (seed 0) |
|---|---:|---:|---:|
| v108_standard | 2,500 | 224 | **98.7%** (156/158 attention_candidate cids が v108_standard にあり) |
| v112 | 400 | 16 | 16/158 = 10% (受容 pool 小範囲) |

→ 段階 2 cid state ledger 再生では v108_standard を採用、v1102 でも踏襲が自然 (broader coverage、attention_candidate の 98.7% カバー)。v112 を補助比較対象とする場合は別途明示。

---

## 2. 受け手構造軸の具体経路

設計書 §2.2 受け手構造軸の Code A 実装案:

### 2.1 Integration α/β (primary receiver scale)

Step G `integration_composition_alpha.parquet` + `integration_composition_beta.parquet` をそのまま使用:
- n_members_bin: n=1 / n=2 / n=3 / n=4+ (Step G 既存)
- qc_gini_bin: low<0.05 / mid<0.20 / high≥0.20 (Step G 既存)
- 既に 10 セル (alpha) + 9 セル (beta) 層化済 (`stratified_observation_integration.parquet`)

### 2.2 CID (低次の比較対象、Taka 整理直接対応)

v10.6 window_trajectory の `n_core_member` 列を per (cid, window) で取得し、CID ごとに以下に層化:

| 層 | 内容 |
|---|---|
| n_core=2 | 1,932 cids、62.6% — Taka「2 ノードが大半」 |
| n_core=3 | 228 cids、7.4% |
| n_core=4 | 303 cids、9.8% |
| n_core=5 | 622 cids、20.1% — Taka「5 ノードは情報量で強い」 |
| n_core>=6 | 3 cids、< 0.1% (極端値、観察事実として記録) |

### 2.3 ESDE 全体 (高次の比較対象)

v10.6 4 解像度 trajectory (event/pulse/step10/window) を集約軸として並列観察。段階 2 で event/step10/window を扱ったのと同型。

### 2.4 注意 — Run を分けない (Gemini 論点 3 + GPT-4 確定)

同一 Run の post-process 層化抽出のみ。新規 Run を構造別に分けると Genesis 系の確率的発生でベースラインがズレる。Step G の手法を継承。

---

## 3. 時間スケール軸の具体経路

設計書 §2.3 時間スケール軸の Code A 実装案:

### 3.1 immediate / short / medium

v10.7 `baselines_with_delta_seed{N}.parquet` の delta_* 列を使用:

| 時間粒度 | 利用列 (5 metric × 3 粒度 = 15 列) |
|---|---|
| immediate (1-10 step) | delta_R_familiarity_immediate / delta_Q_immediate / delta_C_immediate / delta_n_alphas_immediate / delta_n_observed_immediate |
| short (10-100 step) | delta_*_short (同 5 metric) |
| medium (100-1000 step) | delta_*_medium (同 5 metric) |

per (source_cid, relation_path_type, 時間粒度) で集計済 (1.76M rows × 26 cols / seed)。

### 3.2 window

v10.6 trajectory の `window` 列 (per seed 50 windows、step 単位 ~500)。

### 3.3 時間スケールは読みの軸 (実験変数にしない、GPT-3 確定)

immediate/short/medium/window は同一 Run 内の異なる時間ウィンドウで応答を切り取る読み取り解像度。時間を遅延・介入として操作しない。

---

## 4. 応答 read-back 軸 + 際立ち掬い取り A primary / B secondary

### 4.1 応答指標一覧 (v1101a 既存出力からの read-back)

| 応答指標 | source | 用途 |
|---|---|---|
| attention trajectory (注意移動) | attention_emit / causality の attention_candidate_id 時系列 | per (受け手構造, 時間スケール) で attention 推移 |
| influence (波及) | attention_propagation の influence_candidate_count | per cell で influence 集計 |
| 揺れ幅 (variability) | 観察 C actual_predict_rate + lift_over_baseline | per cell で 揺れの妥当性指標 |
| atom 反応 profile | cid_state_ledger 326 atom 濃度 | per (cid, window) で atom 分布 |
| category 反応 profile | 326 atom を category (BOD/COG/...) に集約 | category-level 応答 |

### 4.2 際立ち掬い取り A primary (実験者の構造的指標)

設計書 §2.4 + Gemini 論点 4 (閾値は分布から構造的に) に従い:

| 指標案 | 算出 | 閾値方針 |
|---|---|---|
| 効果サイズ | v10.7 delta_*_short の per cell mean を nominal scale で比較 | per cell mean 分布の Top N% (10% / 5%)、N は分布の自然な切れ目から選定 |
| baseline 乖離 | 観察 C lift_over_baseline (= actual - shuffle baseline) | per cell lift 分布の Top N% |
| 外れ値 | per (cell) records の Q3 + 1.5*IQR を超える数 | IQR ベース構造的判定 |

z-score 単体は不可 (絶対格言 #3、GPT-監査)。

### 4.3 B secondary (v1101a 既存 emit の read-back、軽い踏み込み)

A で掬った際立ちが v1101a 既存 emit と重なるかを read-back:

| v1101a emit | read-back 内容 |
|---|---|
| attention_candidate_id | A が選んだ cell の cid と一致するか |
| causality_candidate_path_zscore | Step E z-score 方式の dominant path と整合するか |
| predicted_lock_mode (cognitive/conscious) | A 際立ち cell の qc_regime と整合するか |
| Step G stratified_observation | A 際立ち cell の構成 bin に Step G で報告済の現象 (integration_β 0.950 等) があるか |

新規 emit 機構なし、v1101a 既存出力からの読み直しに留める (研究手法アップデート §2.6 軽い踏み込み)。

---

## 5. Web Claude / Taka 確認要請 2 件

### 5.1 確認要請 1 — 応答指標の重み付け / 主従

§4.1 で挙げた応答指標 5 種 (attention trajectory / influence / 揺れ幅 / atom profile / category profile) のうち、v1102 の primary table で **主軸とする指標** は何か:

- (i) attention trajectory + influence + 揺れ幅 (注意系を主軸、段階 2 までの流れを継承)
- (ii) atom/category profile (326 atom 濃度、cid_state_ledger 主軸、内容応答に近い)
- (iii) 全 5 種を並列表示 (主従なし)

Code A 仮所見: (iii) 全 5 種並列、ただし掬い取り A の閾値判定は (i) 注意系から (Step G の延長として自然)。

### 5.2 確認要請 2 — per-cell サンプル数下限

受け手構造軸 × 時間スケール軸の組合せセル数:
- Integration α: 10 セル (Step G 既存)
- CID: 5 bin (n_core=2/3/4/5/6+)
- ESDE 4 解像度
- 時間スケール 4 粒度 (immediate/short/medium/window)
- × 24 seeds

全積で 10 × 5 × 4 × 4 × 24 = 19,200 セル (理論上限)。実際は spars に。

**極小サンプル cell の扱い**:
- (i) n < 10 records cell を除外 (統計的検定の慣例)
- (ii) n < 5 records cell を除外 (Step G で 1 alpha / 141 records が integration_β 0.950 を出した前例があるので保守的)
- (iii) 全 cell 残し、際立ち判定時に「サンプル少 = 単発事例」として注釈付き記録

Code A 仮所見: (iii) 全 cell 残す。サンプル少の極端値は Step G で観察した「大型均等構造で integration_β 0.950」のような構造的シグナルになりうるため (留保候補 #L12 同型)。掬い取り時に「サンプル数」を別軸で表示し閾値判定でない注釈で記録。

---

## 6. 進行 — Step A 完了後の流れ

| Step | 内容 | 担当 | 想定 | 待機 |
|---|---|---|---|---|
| Step A (本書) | 認識確認 | Code A | 完了 | Taka 確認待ち |
| Step B 実装 1 | primary table 構築 (受け手構造 × 時間スケール × 応答指標) | Code A | 半日 | §5.1 / §5.2 確定後 |
| Step C 実装 2 | 際立ち掬い取り A primary + B secondary read-back | Code A | 半日 | Step B 後 |
| Step D グラフ | 2 次元 (際立ち配置) + 3 次元 (内部波及) dashboard | Code A | 短時間 | Step C 後 |
| Step E bit-identity | 3 層検証 (実 ledger 不変、書込みパス制限) | Code A | 短時間 | Step D 後 |
| Step F 観察事実報告 | judgement なし (#12) | Code A | 短時間 | Step E 後 |
| Step G Phase Result | v1102 解釈統合 | Web Claude | — | Step F 後 |

想定合計 **1-1.5 日** (既存出力流用、新規 main run なし)。設計書 §6 進行表「Code A 認識確認 → 実装」の Step B-F フェーズ。

---

## 7. 規律遵守自己点検 (本 Step A)

| # | 格言 | 遵守 |
|---|---|---|
| 2 | 物理層 frozen | 本書は read-only 調査、書き込み unified/v1102/ 配下のみ |
| 5 | 観察軸を増やすことを駆動要因にしない | §1.1 で既存出力のみで構築可能を確認、新軸なし |
| 6 | 出口の固定 | 設計書 §4 出口 5 項目を継承、Step A で変更しない |
| 9 | 神の手回避 | §4.2 閾値は分布から構造的に選定 (Top N% / IQR)、恣意的閾値なし |
| 11 | 概念単位を雑に扱わない | §1.2 「n_members」(設計書) と「n_core_member」(実装名) の同義性を明示、§1.4 v108_standard と v112 の区別 |
| 12 | Aruism 判定回避 | 本書は事実記録、(i)(ii)(iii) の判定は Web Claude / Taka |
| 13 | AI を信じない原則は Taka 個人 | §5 確認要請を明示、Code A 仮所見と最終判断を区別 |
| 14 | Taka 直感優先 | §1.2 で Taka「2 ノードが大半、5 ノードは情報量で強い」をデータで確認 |

---

## 8. 一文サマリ (再掲)

設計書 §3.2 論点 5 への Code A 回答として **v1102 primary table は既存出力のみで作成可能・新規 main run 不要** と確認、受け手構造軸 (Integration α/β は Step G `integration_composition_*.parquet` 既存 + CID は v10.6 trajectory `n_core_member` 列で 24 seeds 3,088 cids 分布 n=2 62.6% / n=5 20.1% で Taka 整理確認 + ESDE 全体は v10.6 4 解像度 trajectory) と時間スケール軸 (v10.7 `baselines_with_delta` の immediate/short/medium 5 metric × 3 粒度 = 15 列 + v10.6 window) と応答軸 (v1101a 段階 1 attention_emit/propagation/causality + 段階 2 cid_state_ledger + observation_c) と際立ち掬い取り (A primary 構造的指標 = 効果サイズ・baseline 乖離・外れ値で閾値は分布から / B secondary v1101a 既存 emit read-back) すべて既存出力で揃う、事前齟齬 3 件 (CID n_members ≡ 実装 n_core_member 命名差 / Integration α n_members は Step G と整合 / primary input v108_standard 採用継承) は説明可能、Web Claude/Taka 確認要請 2 件 (§5.1 応答指標の主従 / §5.2 per-cell サンプル数下限) を整理、想定実装 1-1.5 日 (Step B 半日 primary table + Step C 半日 掬い取り + Step D グラフ + Step E bit-identity + Step F 報告)、判定は Web Claude / Taka 領域。

---

*以上、v1102 Step A 認識確認 (Code A、2026-05-19)。確認要請 2 件 (§5) への Web Claude/Taka 回答待ち。回答後 Step B 実装 1 (primary table 構築) に着手可。*
