# v10.10 第一弾 多軸層化解析 統合観察報告 — 5 軸並列観察記述

*作成*: 2026-05-10、Code A
*依頼*: Web Claude 第一弾 5 軸並列層化解析依頼書
*対象*: Web Claude (観察状態判定書第三稿への素材) / Taka
*位置づけ*: 観察記述のみ、判定なし、因果断定回避規律継承

---

## 0. 一文サマリ

第一弾 5 軸 (A: Integration α/β 4 層化 / B: cid 寿命 4 分位 + n_core 交差 / C: 25 atom 個別 + category / E: window × n_core_bin / F: seed 別ばらつき + tied 内訳) を 24 seeds 並列で 236.58 秒で完了 (3.1M rows 集計)、**4 つの構造的事実を観察** — (1) **Integration α/β 4 層化は実質「both vs none」の 2 層化** (only_alpha / only_beta は events 0、ESDE では α 形成 cid は β にも所属)、(2) **長寿 cid (Q4: lifespan ≥ 2,485) で timing_axis -0.196 / v110_vs_v108re +0.214 と効果大**、短命 (Q1) は age=500 通過できず timing_axis 評価不能、(3) **atom category で効果に大差**: BOD/COM/EXS が v110_vs_v108re +0.2-0.4、WLD/TIM が +0.01-0.02 (1 桁差)、(4) **gate_effect は seed 間ばらつき大 (tied 多発)、pulse 系 (timing/v110_vs_v108re) は seed 間収束 (tied 極少)**、Code A 暫定見立てとしての判定は本第一弾では行わず、Web Claude 判定書第三稿の素材として観察事実を提示。

---

## 1. 軸 A: Integration α/β 4 層化

### 1.1 構造的事実 (主要発見)

| layer | seed 0 cid 数 | 24 seeds 集計事実 |
|---|---:|---|
| **only_alpha** | 0 | 全 seed で 0 件付近 (構造的不在) |
| **only_beta** | 0 | 全 seed で 0 件付近 |
| **both** (α+β 両所属) | 129 | 24 seeds 集計でも層 events 多 |
| **none** (Integration 外) | 99 | 同上 |

→ **「ESDE では α/β は同じ cid 集合に発生」という構造的事実**。only_alpha / only_beta は実装上区別できない (β は α の上位構造)。

### 1.2 cohens_d 観察 (mean_delta_C × medium)

| layer | gate_effect | timing_axis | v110_vs_v108re | layer events mean |
|---|---:|---:|---:|---:|
| **both** | +0.001 | **-0.097** | **+0.163** | 38 |
| **none** | -0.014 | -0.046 | +0.061 | 38 |

### 1.3 観察 (記述のみ)

- both 層 で timing_axis -0.097, v110_vs_v108re +0.163 と none より大きい cohens_d が観察された
- これは v10.9 で観察された high_fam_out_integ baseline path (Integration 外の cid を target にした path) の核心とは別の軸
  - v10.9 / Code A n_core 報告: target_cid の Integration 状態
  - 本軸 A: source_cid (atom event 発火対象 cid) の Integration 状態
- 仮説 1: source_cid が Integration 内にあると、外部刺激の伝播経路が確保されやすい (推測、構造的根拠未確認)
- 仮説 2: Integration 内 cid は α/β の中心として活発な lifecycle を持ち、その平均反応が大きい (推測、要追加観察)
- 留保: only_alpha / only_beta が区別できない実装上の制約は ESDE 構造に由来、解析の限界ではない

### 1.4 形成タイミングと event timestamp の関係

実装したが本報告では未集計 (formation_relation 列を出力に追加済み、第二弾解析に持ち越し可能)。

---

## 2. 軸 B: cid 寿命 4 分位

### 2.1 寿命分位値 (24 seeds 集計、n=5,224)

- Q1: lifespan < 481
- Q2: 481 ≤ lifespan < 977
- Q3: 977 ≤ lifespan < 2,485
- Q4: lifespan ≥ 2,485

### 2.2 cohens_d 観察 (mean_delta_C × medium、n_core_bin=all)

| Q | gate_effect | timing_axis | v110_vs_v108re |
|---|---:|---:|---:|
| Q1 (短命 < 481) | -0.012 | **NaN** | +0.056 |
| Q2 (481-977) | -0.005 | -0.025 | +0.048 |
| Q3 (977-2,485) | -0.005 | -0.058 | +0.095 |
| **Q4 (長寿 ≥ 2,485)** | +0.006 | **-0.196** | **+0.214** |

### 2.3 観察 (記述のみ)

- **timing_axis (t200 vs t500) の負方向効果は寿命分位順に増大**: Q1 NaN → Q4 -0.196
- **Q1 の timing_axis NaN**: t500 で短命 cid (lifespan < 481) は age=500 通過できず events 0 → 評価不能
- **Q4 で v110_vs_v108re +0.214 (大効果量に近い)**
- 観察解釈:
  - 仮説 1: 「timing_axis 方向反転」は短命 cid 脱落効果ではなく **長寿 cid そのものの timing 応答性** が関与する可能性
  - 仮説 2: 長寿 cid は構造的に成熟しており、timing による外部刺激への C 反応が安定して大きい (推測)
- 留保: Q1 の評価不能を「短命 cid の事実」として記録、t500 全体の解釈で短命脱落効果を排除できない

### 2.4 寿命 × n_core 交差 (parquet で詳細出力済み)

`v110_lifespan_stratified.parquet` に Q × n_core_bin × path × window × metric の詳細あり。本報告では割愛、第二弾の素材として保留。

---

## 3. 軸 C: 25 atom 個別 + category

### 3.1 atom 別 events 分布 (v110_ABC_t200、24 seeds 合計 1,106)

- max: BOD.ear 55、COG.learn 54、COM.silence 52
- min: WLD.technique 32、WLD.culture 34、WLD.artless 35
- mean: 44.2 events/atom (25 atom 循環でほぼ均等)

### 3.2 atom category 別 cohens_d (mean_delta_C × medium、n_core_bin=all)

| category | atom 数 | gate_effect | timing_axis | **v110_vs_v108re** |
|---|---:|---:|---:|---:|
| **BOD** (身体) | 1 | +0.033 | -0.072 | **+0.399** (最大) |
| **COM** (沈黙) | 1 | +0.031 | -0.078 | +0.284 |
| **EXS** (存在) | 2 | +0.009 | -0.075 | +0.223 |
| **FND** (時空基盤) | 2 | -0.009 | -0.067 | +0.149 |
| COG (学習) | 1 | -0.012 | -0.071 | +0.126 |
| **PER** (五感) | 8 | -0.017 | -0.060 | +0.109 |
| PRP (属性) | 3 | -0.010 | -0.045 | +0.064 |
| SOC (社会) | 3 | -0.014 | -0.027 | +0.044 |
| TIM (時間) | 1 | +0.002 | -0.006 | +0.022 |
| WLD (世界) | 3 | -0.004 | -0.010 | +0.009 |

### 3.3 観察 (記述のみ)

- **v110_vs_v108re で BOD (+0.399) と WLD (+0.009) で 1 桁以上の差** が観察された
- **timing_axis 負方向の絶対値**: BOD/COM/EXS/FND/COG/PER で 0.06-0.08、TIM/WLD で 0.01 以下
- カテゴリー別の差分原因 (推測、留保):
  - 仮説 1: BOD/COM (身体・沈黙) は cid 状態への直接マッピングが他 category より明確で、外部刺激への C 反応が大きい (推測)
  - 仮説 2: WLD/TIM は概念抽象度が高く、cid 状態との対応が弱い (推測)
  - 仮説 3: 1 atom あたり events 数の差 (BOD 55 vs WLD 32) が一部の効果差に寄与する可能性
- 留保:
  - WLD は留保ラベル (artless) を含む 3 atoms で平均、artless を除けば WLD culture/technique のみ
  - TIM は 1 atom のみで n=44 と少、解像度限定
  - 「効いた」と判定せず「観察された」「方向は同様、絶対値が異なる」のような記述に留める

### 3.4 atom × n_core_bin 交差 (parquet で詳細出力済み)

`v110_atom_individual.parquet` に atom_id × n_core_bin × path × metric の詳細。1 atom × 1 n_core_bin の events 数が少なく n_b 不足セルが多い。第二弾で集計するか保留。

---

## 4. 軸 E: window × n_core_bin

### 4.1 timing_axis × n_core_bin × window (mean_delta_C、cohens_d_mean)

| window | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| immediate | -0.006 | -0.012 | -0.034 |
| **short** | -0.034 | **-0.146** | **-0.209** |
| medium | -0.039 | -0.119 | -0.207 |

### 4.2 観察 (記述のみ)

- **immediate window では n_core 別の差が小** (-0.006 〜 -0.034)
- **short / medium で n_core 階層的に大効果**: bin_5+ で -0.21 / -0.21
- **短時間スケール (immediate=1-10 step) では timing 効果が捕捉されにくい**
- 仮説 (留保): atom event 直後 (immediate) は cid の即時反応が捕捉前、外部刺激の C 波及は short-medium で展開

### 4.3 long window について

実装指示書 §2.4 で言及された「long」window は v107 既存定義 `WINDOW_DEFS = [(immediate,1,10),(short,10,100),(medium,100,1000)]` に存在せず、本軸では集計対象外。

第二弾以降で long window (1,000-5,000 step 等) を新規実装する場合は、baselines_with_delta の compute_deltas を改修必要 (現状の v10.10 既存データから集計不能)。

---

## 5. 軸 F: seed 別構造ばらつき + tied 内訳

### 5.1 seed 別 n_core 分布 (24 seeds)

n_core_2 比率の seed 別:
- 最低 (中 cluster 多い): **seed 7 (n_core_2=123 / 179 = 68.7%)**, seed 18 (65.3%)
- 最高 (ペア集中): seed 9 (78.9%), seed 23 (82.1%), seed 20 (78.3%)

n_core_5+ の seed 別:
- 最多: seed 7 (35), seed 21 (34), seed 17 (33), seed 6 (31)
- 最少: seed 8 (19), seed 23 (21), seed 16 (20), seed 0 (21)

### 5.2 seed 別事件 (Code A Round 2 §1.4 で指摘の seed 7/18)

- seed 7: 全 cid 179 (24 seeds 中 2 番目に少)、中 cluster (n_core 5+) 比率 19.6% (24 seeds 中最高)
- seed 18: 全 cid 170 (最少)、中 cluster 比率 18.8%

→ seed 7/18 は **「全 cid 少、中 cluster 比率高」** という共通特徴 = ABC × age=500 で events 6 (Round 2 報告) になった構造的根拠。

### 5.3 tied 20% セルの内訳 (gate_effect / timing_axis / v110_vs_v108re × metric)

| comparison | metric | n_tied (= seed 11-13/24 で方向分散) |
|---|---|---:|
| **gate_effect** | mean_delta_R_familiarity | **223** |
| gate_effect | mean_delta_n_observed | 122 |
| gate_effect | mean_delta_C | 114 |
| gate_effect | mean_delta_n_alphas | 102 |
| gate_effect | mean_delta_Q | 89 |
| gate_effect | mean_n_pulses_in_window | 86 |
| timing_axis | mean_delta_R_familiarity | 80 |
| v110_vs_v108re | mean_delta_Q | 69 |
| v110_vs_v108re | mean_delta_C | 69 |
| timing_axis | mean_delta_C | 64 |
| timing_axis | mean_delta_Q | 61 |
| v110_vs_v108re | mean_delta_R_familiarity | 46 |
| v110_vs_v108re | mean_delta_n_alphas | 39 |
| v110_vs_v108re | mean_delta_n_observed | 28 |
| timing_axis | mean_delta_n_alphas | 13 |
| **timing_axis** | **mean_n_pulses_in_window** | **9** |
| **v110_vs_v108re** | **mean_n_pulses_in_window** | **8** |

### 5.4 観察 (記述のみ)

- **gate_effect で tied 多発**: 全 metric で 86-223 cells が seed 間で方向分散
  - 特に mean_delta_R_familiarity が 223 で tied 最多
  - → gate_effect は seed 別に方向が一定しない傾向 (= 効果が seed 依存)
- **pulse 系で tied 極少**: timing_axis × mean_n_pulses 9 / v110_vs_v108re × mean_n_pulses 8
  - → pulse 系の効果は **24 seeds で安定して同方向** (= 機構的 robust)
- 仮説 (留保):
  - 仮説 1: gate_effect は events 数の seed 別ばらつきが大きく、Cohen's d が seed で逆転しやすい
  - 仮説 2: pulse 系は cid lifecycle に直結する効果で、seed 間で構造的に安定する

---

## 6. 第一弾 4 つの構造的事実 (Code A 観察記述)

判定なし、観察記述のみ:

### 事実 1: ESDE α/β は同 cid 集合に発生

軸 A 観察。only_alpha / only_beta は events 0 付近 (構造的不在)。実装上 α 形成 cid は β にも所属する。

### 事実 2: 寿命分位順に timing_axis 効果が増大

軸 B 観察。Q1 (短命) NaN → Q4 (長寿) -0.196。「timing 方向反転」は短命脱落効果ではなく長寿 cid の応答性も寄与する可能性 (仮説、留保)。

### 事実 3: atom category 別効果差は 1 桁

軸 C 観察。v110_vs_v108re で BOD (+0.399) vs WLD (+0.009) で 40 倍差。category と概念抽象度の対応 (仮説、留保)。

### 事実 4: gate_effect は seed 間不安定、pulse 系は安定

軸 F 観察。gate_effect で tied 86-223 cells、pulse 系で 8-9 cells。pulse 系の機構的 robust 性が再確認 (24 seeds 方向一致 80% 報告との整合)。

---

## 7. 留保事項の更新 (新規発生)

v10.10 既存留保 6 件 + n_core 層化での 3 件は維持。第一弾で新規発生:

7. **「only_alpha / only_beta」の実装上の不在**: ESDE 構造的事実、解析の限界ではない (軸 A)
8. **長寿 cid (Q4) の timing_axis 方向反転寄与**: timing 真の効果と長寿構造的応答性の切り分けは未解決 (軸 B)
9. **atom category 別効果差の構造的解釈**: BOD/COM/EXS/FND vs WLD/TIM の 1 桁差は概念抽象度との対応か events 数差か未解明 (軸 C)
10. **gate_effect の tied 多発**: gate 効果が seed 別に変動する原因は events 数ばらつきか機構的不安定か未解明 (軸 F)

---

## 8. 出力ファイル一覧

| 軸 | ファイル | 行数 |
|---|---|---:|
| A | `cross_seed/v110_integration_layer_stratified.parquet` | 280,926 |
| B | `cross_seed/v110_lifespan_stratified.parquet` | 1,572,732 |
| C | `cross_seed/v110_atom_individual.parquet` | 820,336 |
| E | `cross_seed/v110_window_n_core_cross.parquet` | 432,702 |
| F | `cross_seed/v110_seed_distribution.parquet` | 24 |
| F | `cross_seed/v110_tied_by_comparison_metric.parquet` | 18 |
| F | `cross_seed/v110_tied_by_path.parquet` | 10 |
| F | `cross_seed/v110_seed_event_summary.parquet` | 72 |
| - | `v110_multi_axis_stratified_summary.md` | 本書 |

総 rows: 約 3.1M (軸 A+B+C+E)、約 0.6 GB (parquet snappy)。

---

## 9. 一文サマリ (再掲)

5 軸並列層化解析を 236.58 秒で完了 (3.1M rows、24 seeds 並列)、**4 つの構造的事実** を観察記述 — (1) ESDE α/β 構造的に同 cid 集合発生 (only_alpha/only_beta 不在) / (2) 寿命分位順に timing_axis 効果増大 (Q4 で -0.196、Q1 で評価不能) / (3) atom category 別 v110_vs_v108re 1 桁差 (BOD +0.399 vs WLD +0.009) / (4) gate_effect は seed 間 tied 多発、pulse 系は seed 間収束、Code A は本第一弾で判定せず Web Claude 判定書第三稿への素材として観察事実のみを提供、第二弾候補 (path × n_core × 全 metric / bimodal の n_core 層化) と第三弾候補 (cid pair) は本第一弾結果を見て Taka 判断、留保事項に新規 4 件追加 (only_alpha/only_beta 不在 / 長寿 cid 寄与切り分け未解決 / atom category 効果差解釈未解明 / gate_effect tied 多発原因未解明)。

---

*以上、Code A による v10.10 第一弾 多軸層化解析統合観察報告。Web Claude 判定書第三稿の素材として活用。判定なし、観察記述のみ、因果断定回避規律遵守。*
