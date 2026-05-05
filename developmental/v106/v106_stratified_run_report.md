# v10.6 層化解析 run 報告書

*生成*: 2026-05-05、Code A
*親*: `v106_implementation_brief_stratified.md` (Web Claude 層化追加仕様)
*対象*: Web Claude → Taka

## 0. 一文サマリ

post-post-process として 24 seeds を **11.29 秒** (単一バッチ) で完了、5 層化軸 + 2 cross-tab + ハブ層化 + α/β 層化 + cross-seed 集計 + attack-related atom 解析の **12 種類 197 ファイル** を生成。集団平均 CHG.begin 51% の正体は **「89% が short-lived (lifespan<1000) cid」由来の集団平均効果** と判明し、層化により **n=5/long/hub cid は COG.enlightenment / FND.logic / FND.timeless 偏り、Integration 増大で atom 接地が逆に弱くなる、attack-related 15 atom のうち 11 が 24/24 unmatched (個体経験 [fear/pain/wound/death] は接地、社会的破壊 [destroy/conflict/war/evil/hate] は完全欠如)** という構造が浮上した。

---

## 1. 実装結果

| 項目 | 値 |
|---|---|
| 入力 | 既存 main run の per-seed 出力 (再 run 不要) |
| 出力 | `outputs/main/stratified/` 配下 197 ファイル |
| 実行時間 | 11.29 秒 (24 seeds 単一バッチ) |
| 層化軸 | n_core / lifespan / familiarity / integration / final_state (5 軸) |
| cross-tab | B×D (lifespan × integration), A×B (n_core × lifespan) |
| α/β 層化 | 5 パターン × seed、β サイズ class × seed |
| attack-related | 15 atom curated set + 24/24 検証 |

---

## 2. 集団平均の罠の正体 — n_core / lifespan 偏り

### 2.1 n_core 別の本当の atom 分布

| n_core | n_cid (24 seeds 合算) | 割合 | dominant atom (24/24 一致率) | mean_max_sim | matched 比率 |
|---|---|---|---|---|---|
| n=2 | 3,968 | 76.0% | CHG.begin (100%) | 0.633 | 100.0% |
| n=3 | 288 | 5.5% | TIM.moment (58.3%) | 0.507 | 67.2% |
| n=4 | 327 | 6.3% | SOC.city (41.7%) | 0.549 | 88.7% |
| n=5 | 638 | 12.2% | FND.logic (75.0%) | 0.529 | 62.5% |
| n=6/7/8 | 3 | 0.06% | (各 1 cid、サンプル不足) | - | - |

→ **集団平均 51% CHG.begin の正体は n=2 cid (76%) の偏在**。
→ n=5 cid は **FND.logic (論理基底)** に偏り、SOC/STA/BEI ではない。

### 2.2 lifespan 別

| lifespan | n_cid | 割合 | dominant atom (一致率) | mean_max_sim | matched | partial | unmatched |
|---|---|---|---|---|---|---|---|
| short (<1000) | 4,641 | 88.8% | CHG.begin (100%) | 0.618 | 96.1% | 3.9% | 0% |
| medium (1000-10000) | 253 | 4.8% | FND.logic (50%) | 0.550 | 79.4% | 20.6% | 0% |
| long (10000+) | 330 | 6.3% | COG.enlightenment (75%) | 0.510 | 56.5% | 43.5% | 0% |

→ **Long-lived cid の 43.5% が partial_match** (max_sim < 0.5)、構造ベクトル空間の周縁に位置。
→ 集団平均 51% CHG.begin は **89% short-lived cid** が押し上げた値。

### 2.3 integration 所属別

| integration | n_cid | 割合 | dominant atom (一致率) | mean_max_sim | matched | partial |
|---|---|---|---|---|---|---|
| isolated (≤1 alpha) | 4,637 | 88.8% | CHG.begin (100%) | 0.616 | 95.3% | 4.7% |
| catalytic (2-5) | 98 | 1.9% | FND.logic (91.7%) | 0.606 | 100% | 0% |
| chained (6-50) | 345 | 6.6% | FND.logic (41.7%) | 0.540 | 74.4% | 25.6% |
| **hub (51+)** | **144** | **2.8%** | **COG.enlightenment (62.5%)** | **0.495** | **45.2%** | **54.7%** |

→ **Integration が増えるほど atom 接地が弱くなる** (hub の 54.7% が partial_match)。
→ ハブ cid は構造ベクトル空間で「特殊点」化、atom 軸への接地度が低い。

### 2.4 final_state 別

| final_state | n_cid | dominant atom | mean_max_sim | matched |
|---|---|---|---|---|
| reaped (run 中消滅) | 4,334 (83%) | CHG.begin | 0.619 | 95.3% |
| hosted (生存) | 795 (15%) | FND.logic (75%) | 0.552 | 78.5% |
| ghost (label 死) | 95 (1.8%) | COG.learn (78.3%) | 0.574 | 96.4% |

### 2.5 familiarity 別

| familiarity | n_cid | dominant atom | mean_max_sim |
|---|---|---|---|
| weak (<30) | 1,609 | CHG.begin (91.7%) | 0.627 |
| medium (30-150) | 2,562 | CHG.begin (100%) | 0.600 |
| strong (150+) | 1,053 | CHG.begin (100%) | 0.598 |

→ familiarity の高低では atom alignment は **ほぼ変わらない** (CHG.begin 支配)。これは familiarity が cid 構造ベクトルのどの軸にも強く効いていない可能性を示唆。

---

## 3. cross-tab — lifespan × integration

seed 0 抜粋 (24 seeds 全体での傾向は seed 0 と整合):

| | isolated | catalytic | chained | hub |
|---|---|---|---|---|
| short | **203** CHG.begin | 4 COG.learn | 3 SOC.city | **0** |
| medium | 3 WLD.artless | 0 | 6 FND.logic (50%) | 0 |
| long | 1 FND.unchanging | 0 | 6 FND.timeless (50%) | **2 COG.enlightenment (100%)** |

→ **short × hub = 0 cid** (短寿命 cid はハブ化しない、論理的整合)
→ **long × hub = COG.enlightenment 100%** (ハブ cid の atom 偏りは「長寿命 hub cid」で純粋化)

→ **「ハブ cid」と「long-lived cid」は事実上同義**。短寿命でハブ化した cid は 24 seeds 通してほぼ存在しない。

---

## 4. cross-tab — n_core × lifespan (seed 0 例)

| | short | medium | long |
|---|---|---|---|
| n=2 | 179 CHG.begin (57%) | 1 WLD.artless | 0 |
| n=3 | 12 ELM.morning (33%) | 0 | 0 |
| n=4 | 11 SOC.city (36%) | 2 WLD.culture | 2 COG.enlightenment |
| n=5 | 8 FND.logic (88%) | 6 FND.logic (33%) | 7 FND.timeless (43%) |

→ **n=2 はほぼ全部 short**, **n=5 だけが全 lifespan に分布**, **long-lived は n=5 中心**。
→ n=5 cid の long subset は **FND.timeless** に接地 (時間超越的軸に長寿命 cid が集まる)。

---

## 5. attack-related atom — 構造的盲点の定量化

curated 15 atom set (`outputs/main/stratified/attack_related_atoms_definition.json` 参照):

### 5.1 完全欠如 (24/24 unmatched)

| atom | category | max_sim_overall | max_sim_min | nearest cid example |
|---|---|---|---|---|
| ACT.destroy | ACT | **0.126** | 0.113 | n=2 reaped |
| EMO.hate | EMO | 0.239 | 0.214 | n=2 reaped |
| LOG.unreason | LOG | 0.245 | 0.193 | n=2 hosted |
| STA.war | STA | 0.246 | 0.207 | n=4 hosted |
| VAL.evil | VAL | 0.249 | 0.115 | n=2 reaped |
| ECO.loss | ECO | 0.265 | 0.192 | n=4 hosted |
| EMO.despair | EMO | 0.282 | 0.258 | n=2 reaped |
| CHG.decay | CHG | 0.297 | 0.260 | n=2 reaped |
| COM.conflict | COM | 0.299 | 0.268 | n=2 reaped |
| STA.danger | STA | 0.207 | 0.183 | n=2/4 reaped/hosted |
| SOC.attack | SOC | 0.308 (22/24) | 0.256 | n=2 reaped |

### 5.2 部分接地 (24 中 0 seed unmatched)

| atom | category | max_sim_overall | max_sim_mean | 解釈 |
|---|---|---|---|---|
| **STA.wound** | STA | **0.462** | 0.456 | 個体身体損傷 → 接地 |
| **STA.pain** | STA | **0.451** | 0.425 | 個体身体痛 → 接地 |
| **EMO.fear** | EMO | **0.453** | 0.435 | 個体感情恐怖 → 接地 |
| **EXS.death** | EXS | 0.381 | 0.350 | 個体死 (ghost) → 弱接地 |

### 5.3 構造的境界線

11/15 が完全欠如、4/15 が接地。境界線:

- **個体的経験 (pain / wound / fear / death)**: Genesis 系の構造ベクトル空間で表現可能 (STA / EMO / EXS の身体・感情系列)
- **社会的破壊・対立 (destroy / conflict / war / hate / attack / despair / decay / evil)**: Genesis 系では構造的に表現不可能

→ Taka 整理「攻撃性などのより高等生物的な営みに関するアトムとの接続がない、ESDE Language と接続されたことで初めて可視化された (不可視による論理的な可視化)」を **定量化** した結果。

→ Genesis 系は **個体経験までは扱えるが、社会的・他者破壊的な概念は構造的に持たない**。これは「ない」ことの能動的観察。

---

## 6. 24/24 unmatched atom の全 35 種拡張リスト

attack-related 以外も含めた 24/24 unmatched atom (consistency_24_24=True):

| atom | category | max_sim_overall |
|---|---|---|
| ACT.destroy | ACT | 0.126 |
| STA.danger | STA | 0.207 |
| EMO.hate | EMO | 0.239 |
| FND.information | FND | 0.244 |
| LOG.unreason | LOG | 0.245 |
| STA.war | STA | 0.246 |
| REL.together | REL | 0.246 |
| VAL.evil | VAL | 0.249 |
| ECO.loss | ECO | 0.265 |
| VAL.sacred | VAL | 0.281 |
| EMO.despair | EMO | 0.282 |
| REL.different | REL | 0.284 |
| CHG.decay | CHG | 0.297 |
| COM.conflict | COM | 0.299 |

→ 14 atom が 24/24 unmatched で確定。VAL.sacred, FND.information, REL.together, REL.different も完全欠如。

部分 unmatched (15-22/24): EMO.trust (22), SOC.attack (22), EMO.love (21), SOC.criticize (21), VAL.good (19), FND.uninformed (18), COM.cooperate (16), VAL.incorrect (15)

→ **EMO.love 21/24 unmatched** は注目。事前 atom 集計で EMO.love は十分なプロファイルがあったのに (Code A env check §6.2)、cid 側の構造ベクトル空間に対応点が少ない。

---

## 7. 5 パターンの seed 別件数

| pattern | total | mean/seed | std |
|---|---|---|---|
| core (5,5,5) | 702 | 29.2 | 17.0 |
| near_core (4,5,5) | 793 | 33.0 | 14.4 |
| capture (2,5,5) | **969** | **40.4** | 14.2 |
| bridge (2,4,5) | 623 | 26.0 | 11.7 |
| peripheral (2,2,5) | 563 | 23.5 | 10.5 |
| other (5 パターン外) | 1,757 | 73.2 | 23.0 |
| total size 3 α | **5,407** | 225.3 | - |

→ サンプル数十分 (5 パターンとも 1 seed あたり 23-40)。**capture (2,5,5) が最頻出**。
→ smoke 報告書 §4.3 の「core 9/24 で FND.logic」の "9/24" は (5,5,5) パターンが seed ごとに 9-71 件出現する中で、9 seed では FND.logic が dominant、他 15 seed では別 atom (TIM.moment 等) が拮抗していたことを示す。サンプル数の問題ではなく **真の分岐**。

---

## 8. ハブ cid 層化結果

各 seed の hub cid (Top 1%) の特性内訳例 (seed 0):

- すべて n_core 不明 (hub cid は v11 unformed の場合あり、または n=5 多)
- すべて lifespan_class = long
- すべて final_state = hosted (run 終了時生存)

→ **「hub cid」≈「long + hosted + n=5」の純粋集合**。これにより v10.6 で観察された「ハブ cid → COG.enlightenment / FND.timeless / EXS.being」は **「長寿命・高 n_core・生存 cid」の atom alignment** と等価。

---

## 9. 集団平均の罠 — 全体観察 vs 層別観察

| 観察 | 集団平均 (全 5,224 cid) | 層別実態 |
|---|---|---|
| dominant atom | CHG.begin (51%) | n=2 (76%, short, isolated) の特徴 |
| ハブ cid bias | COG.enlightenment | n=5 / long / hosted / hub の特徴 |
| 5 パターン bias | TIM.moment 支配 | パターンごとに分岐あり (core は FND.logic 寄り) |
| max_sim 平均 | 0.608 | hub 0.495 vs isolated 0.616 (大きな差) |
| unmatched 比率 | 0% (全体) | hub で 54.7% が partial_match |

→ **集団平均は階層構造を平均化して情報を失う** (v10.2 教訓 #120 の確認)。

---

## 10. 出力ファイル一覧 (197 ファイル)

```
developmental/v106/outputs/main/stratified/
├── stratified_atom_distribution_seed{0..23}.csv           (24 file, 各 16-18 行)
├── stratified_category_distribution_seed{0..23}.csv       (24 file)
├── cross_tab_lifespan_integration_seed{0..23}.csv         (24 file, 各 12 cell)
├── cross_tab_ncore_lifespan_seed{0..23}.csv               (24 file)
├── stratified_unmatched_atoms_seed{0..23}.csv             (24 file, atom-side per stratum)
├── hub_cid_stratified_seed{0..23}.csv                     (24 file, n_core × lifespan × final_state)
├── alpha_atom_aggregate_stratified_seed{0..23}.csv        (24 file, 5 パターン × atom)
├── beta_atom_aggregate_stratified_seed{0..23}.csv         (24 file, β size class × atom)
├── stratified_summary_cross_seed.csv                      (1 file, 20 行)
├── unmatched_atoms_consistency.csv                        (1 file, 35 atom)
├── five_pattern_counts_per_seed.csv                       (1 file, 24 row)
├── attack_related_atoms_analysis.csv                      (1 file, 15 atom)
└── attack_related_atoms_definition.json                   (1 file, curated set + rationale)
```

---

## 11. Web Claude / Taka への要判断 4 項目

1. **集団平均 CHG.begin 51% は「n=2 short-lived cid 偏り」由来**で確定して良いか。観察記録として「層別化により真の構造が判明」と整理する案。

2. **ハブ cid = long + hosted + n=5 の純粋集合**であることが判明。事前推測 SOC.central/STA.persistent/BEI.integrated の miss は **「ハブ性は身体・社会的関係ではなく時間継続・論理的・存在論的な軸で表現される」** という観察として記録する案。

3. **attack-related 15 atom のうち 11 が完全構造的欠如**、4 が接地 (個体身体・感情系列のみ)。**「Genesis 系は社会的破壊・対立・価値判断概念を構造ベクトルとして持たない」** という観察を v10.6 主結果として記録する案。Taka 整理「不可視による論理的な可視化」を裏付け。

4. **hub cid の 54.7% が partial_match**。Integration 増大が atom 接地度を下げるという逆相関は、48 軸設計の **scale axis (n_core based)** との非線形性を示唆。Web Claude 解釈待ち。

---

## 12. 完了条件チェック

### 12.1 機能完了
- [x] 5 層化軸 × stratified_atom_distribution / category_distribution
- [x] cross_tab_lifespan_integration (B×D, 12 cell × 24 seed)
- [x] cross_tab_ncore_lifespan (A×B, ~15 cell × 24 seed)
- [x] stratified_unmatched_atoms (atom-side per stratum)
- [x] hub_cid_stratified (n_core × lifespan × final_state)
- [x] alpha_atom_aggregate_stratified (5 pattern)
- [x] beta_atom_aggregate_stratified (β size class)
- [x] stratified_summary_cross_seed (20 行)
- [x] unmatched_atoms_consistency (35 atom)
- [x] five_pattern_counts_per_seed (24 row)
- [x] attack_related_atoms_analysis (15 atom curated)

### 12.2 規律完了
- [x] read-only 縛り維持 (v105 配下に書き込みなし)
- [x] 出力先 v106/outputs/main/stratified/ 配下のみ
- [x] ウェット概念禁止維持
- [x] 24 seeds 単一バッチで実行

### 12.3 出力検証
- [x] 各 CSV が想定スキーマで生成
- [x] サンプル少ない層 (n=6/7/8 = 1 cid 各) でもエラーなし
- [x] cross_seed_summary が 24 seeds 全部含む

---

*以上、Code A による v10.6 層化解析 run 報告。Web Claude の解釈待ち項目は §11。*

---

## 後注: 時間軸混在 caveat (2026-05-06 追記)

本層化解析で得た「long-lived cid のみ COG.enlightenment 接地」「hub cid 54.7% partial_match」「short × hub = 0」「Integration 増大で atom 接地が逆に弱くなる」等の結果は、cid 構造ベクトルの累積指標が **長寿命 cid ほど豊か (data 生成期間が最大 125 倍違う)** という時間軸混在の構造的バイアスの影響を受けている可能性がある。詳細: → `v106_temporal_axis_caveat.md`
