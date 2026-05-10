# v10.12 Step Z 事前調査報告 — 設計破綻と主題機構崩壊の同時発生

*作成*: 2026-05-10、Code A
*親*: `v112_implementation_brief.md` 第 2 版 (Web Claude 2026-05-10)
*対象*: Web Claude (主題ドキュメント / 実装指示書の修正検討) / Taka (分岐判断)
*位置づけ*: 実装に進まず、実測結果のみ提示。設計判断は Web Claude/Taka に委ねる。

---

## 0. 一文サマリ

v10.12 主題ドキュメント第 3 版が現作業環境に未配置のため実装指示書 §1 の Q-Z1〜Q-Z7 を **target_step = cid.birth + 200 (age=200 timing、v10.9/v10.11 慣例)** の仮置きで実測、**4 つの重大乖離** を検出 — (1) **Q-Z1 (4 条件複合の母集団)**: 24/24 seed で AND_all < 10 (mean 3.9/seed、min 0、max 8、24 seeds 合計 94)、Web Claude 想定 (per seed 数十) から大きく乖離、設計破綻判定基準を全 seed が下回る、(2) **Q-Z2 (Q3_threshold)**: Web Claude 想定 977 に対し実測 **Q3 = 2,485** (Q2=977、Q1=481)、想定が Q2 と Q3 を取り違えている可能性、(3) **Q-Z6 (cid pool 重なり)**: overlap_ratio_v112 mean **0.958** で v112 pool は v108 top_k_100 のほぼ完全な subset、GPT 修正 1 の matched_pool 比較の意味が崩壊、(4) **Q-Z5 (v10.5 機構との重複)**: 条件 1 (β member 除外) は v10.11 既知 (留保 21) の実装適用 (b)、Q-Z3 (top_quartile_threshold) は per_seed std/global = 0.61 で **seed 別採用が妥当**、Q-Z4 (formation_relation 時点判定) は v10.10/v10.11 既存実装流用可能で整合、Q-Z7 (規模見積もり) は計算時間 1-3 分 / storage 累計 1.7-1.9 GB (28-32%) で打ち切り条件に余裕、Code A は §0.4 禁止事項に従い設計判断せず Web Claude/Taka 分岐判断要請事項を §6 で整理、観察軸増加への転換提案・条件緩和の独自実装・実装着手はいずれも行わない、Web Claude/Taka 判断後の対応 (主題 §13.2 4 項目固定発動 / 主題変更 / 中止) を待って Step A 認識確認に進む。

---

## §1 Q-Z1: 4 条件複合の母集団 (設計の根幹、最重要)

### 1.1 実測結果 (per-seed × 各条件)

target_step = cid.birth + 200 仮置き。Q3_threshold は Q-Z2 実測値 2,485 を使用 (要 Web Claude 確認)。

| seed | n_total | cond1 (¬β) | cond2 (long) | cond3 (n_core≥5) | cond4 (high_fam) | AND_1_2 | AND_1_2_3 | **AND_all** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 228 | 190 | 50 | 21 | 57 | 44 | 18 | **2** |
| 1 | 207 | 174 | 53 | 27 | 53 | 45 | 15 | **4** |
| 2 | 246 | 206 | 51 | 28 | 62 | 46 | 17 | **3** |
| 3 | 221 | 190 | 47 | 24 | 57 | 45 | 18 | **3** |
| 4 | 210 | 172 | 64 | 29 | 53 | 51 | 23 | **8** |
| 5 | 233 | 208 | 61 | 30 | 59 | 55 | 19 | **8** |
| 6 | 209 | 165 | 50 | 31 | 53 | 41 | 25 | **8** |
| 7 | 179 | 137 | 47 | 35 | 45 | 38 | 24 | **1** |
| 8 | 217 | 185 | 53 | 19 | 55 | 45 | 15 | **2** |
| 9 | 232 | 200 | 41 | 23 | 62 | 37 | 13 | **2** |
| 10 | 181 | 158 | 51 | 32 | 47 | 42 | 21 | **7** |
| 11 | 240 | 194 | 51 | 26 | 66 | 38 | 16 | **4** |
| 12 | 248 | 209 | 63 | 30 | 63 | 49 | 19 | **2** |
| 13 | 204 | 187 | 55 | 28 | 52 | 51 | 24 | **4** |
| 14 | 192 | 166 | 55 | 25 | 48 | 48 | 21 | **6** |
| 15 | 198 | 176 | 54 | 17 | 50 | 48 | 15 | **1** |
| 16 | 229 | 182 | 56 | 20 | 58 | 44 | 13 | **2** |
| 17 | 227 | 193 | 57 | 33 | 57 | 47 | 23 | **1** |
| 18 | 170 | 128 | 50 | 32 | 44 | 39 | 22 | **7** |
| 19 | 220 | 192 | 54 | 23 | 55 | 49 | 19 | **2** |
| 20 | 253 | 225 | 63 | 26 | 64 | 53 | 15 | **5** |
| 21 | 200 | 176 | 60 | 34 | 50 | 51 | 22 | **8** |
| 22 | 240 | 200 | 68 | 27 | 60 | 55 | 16 | **4** |
| 23 | 240 | 212 | 55 | 21 | 61 | 46 | 15 | **0** |

### 1.2 集計

- **AND_all 24 seeds total: 94**
- per seed: mean **3.9**, min **0** (seed 23)、max **8** (seed 4/5/6/21)、std 2.6
- Web Claude 想定 (per seed 数十) との乖離: 約 1 桁分

### 1.3 判定基準照合 (実装指示書 §1.2 Q-Z1 判定基準)

| 基準 | 該当 seed |
|---|---|
| n_AND_all ≥ 30 (整合) | **0/24** |
| n_AND_all 10-29 (境界) | **0/24** |
| **n_AND_all < 10 (設計破綻判定)** | **24/24** |

→ **全 24 seed で設計破綻判定基準を下回る**。

### 1.4 4 条件 AND での絞り込み連鎖の観察

各条件単独: cond1 (¬β) ~80%、cond2 (long) ~25%、cond3 (n_core≥5) ~12%、cond4 (high_fam) ~25%
AND_1_2 ~22%、AND_1_2_3 ~9%、**AND_all ~2%**

→ 4 条件 AND は seed あたり 200 cid から数 cid (1.7%) まで絞り込まれる。

---

## §2 Q-Z2: Q3_threshold (lifespan の Q3) — 想定の 2.5 倍

### 2.1 実測 (24 seeds 集計、n=5,224)

| 統計 | 値 |
|---|---:|
| min | 451 |
| max | 25,000 |
| Q1 (25%) | 481 |
| **Q2 (median)** | **977** |
| **Q3 (75%)** | **2,485** |
| mean | 3,413 |
| std | 6,030 |

### 2.2 Web Claude 想定との乖離

- Web Claude 想定: 977 (実装指示書 §1.2 Q-Z2)
- 実測: **Q3 = 2,485** (Web Claude 想定の **2.5 倍**)
- 977 は **Q2 (中央値)** であり、Web Claude が Q2 と Q3 を **取り違えている可能性**

### 2.3 判定基準照合 (実装指示書 Q-Z2)

- 800-1,200 範囲: NO (実測 2,485)
- 大きく乖離: **YES** → Web Claude/Taka 判断要請

### 2.4 影響

- 設計通り Q3=2,485 採用: cond2 該当が ~25% に縮小、AND_all 母集団が更に縮小 (現状のまま)
- Q2=977 採用 (取り違え修正): cond2 該当が ~50% に拡大、AND_all 母集団は推定で 2-3 倍 (主題意図と異なる)

---

## §3 Q-Z3: top_quartile_threshold (familiarity_max)

### 3.1 実測

| 指標 | 値 |
|---|---:|
| global_q3 (24 seeds 統合) | 81.07 |
| per_seed_q3 mean | 80.87 |
| per_seed_q3 std | **49.70** |
| per_seed_q3 min | 58.41 |
| per_seed_q3 max | 316.24 (seed 23 が外れ値) |
| **std_to_global_ratio** | **0.61** |

### 3.2 判定 (実装指示書 Q-Z3)

- std_to_global_ratio = 0.61 ≫ **0.10**
- → **seed 別採用が妥当**

---

## §4 Q-Z4: formation_relation 時点判定の実現性

### 4.1 既存実装 (流用可能)

| ファイル | 機能 | 存在 |
|---|---|---|
| `developmental/v110/v110_environment_check.py` | build_alpha_beta_intervals (v10.10) | ✓ |
| `developmental/v110/v110_multi_axis_stratified_analyzer.py` | build_cid_features + integration_layer | ✓ |
| `developmental/v111/v111_q_c_inherited_observer.py` | q_c_inherited 起点 within-cid 観察 | ✓ |

### 4.2 データ源

- alpha_lifecycle_log_seed*.csv (event_type birth / member_ghosted / active_to_recorded)
- beta_lifecycle_log_seed*.csv (event_type birth / alpha_added / beta_merged / q_c_inherited / active_to_recorded)

### 4.3 判定 (実装指示書 Q-Z4)

- (a) v10.10/v10.11 既存実装を流用、新規実装規模 30 行
- → **整合、進める**

---

## §5 Q-Z5: v10.5 機構との整合 (Code A 視点、Q-Z5 設計破綻リスク)

### 5.1 v10.5 機構の本体 (`developmental/v105/v105_integration.py:1035`)

```python
def on_ghost(self, ...):
    # 1. α 側: メンバー除外、recorded 化判定 (Q/C 継承はしない)
    self.alpha.on_ghost(cid=cid, global_step=global_step)
    # 2. β 側: Q/C 100% 継承
    self.beta.on_ghost(...)
```

→ **機構 A**: cid が ghost 化時、その cid が β member なら β が Q/C を 100% 継承。α 側は Q/C 継承なし。

### 5.2 v10.11 既知との重複

- **v10.11 q_c_inherited 観察** で、β member cid の C 値が 24 seeds 一貫して正方向に動くことを確認 (delta_C +0.097〜+0.497、全 12 cells)
- **v10.11 留保 21**: ESDE β 機能 (q_c_inherited で C 増加) の直接観察可能性
- v10.11 結論: 「β member cid は C 値が継続的に増加するため、v10.12 概念取り込み対象から除外」

### 5.3 判定候補 (実装指示書 Q-Z5)

- (a) 整合、自明な再観察ではない: 該当しない
- (b) **部分的に重なる**: 該当 ← Code A 視点
  - 条件 1 単独 (β member 除外) は v10.11 既知の延長
  - ただし「4 条件複合 cid で atom event 効果が v108 top_k_100 (β member 含む) より強いか」の比較は v10.12 で初めて
- (c) 自明な再観察である: 部分該当 (条件 1 のみで見ると)

### 5.4 Web Claude/Taka 判断要請事項

- 留保事項として「条件 1 は v10.11 既知の延長」を明記して進めるか
- 主題変更で v10.11 違反パターン (再観察) の再発を防止するか

---

## §6 Q-Z6: cid pool 重なり (主題 §5 機構案の核心)

### 6.1 実測 (per-seed)

| 統計 | 値 |
|---|---:|
| **overlap_ratio_v112 mean** (v112 pool のうち v108 にも含まれる率) | **0.958** |
| overlap_ratio_v108 mean (v108 pool のうち v112 にも含まれる率) | 0.019 |

per-seed: 23/24 seed で v112 pool が v108 top_k_100 の **完全な subset** (ratio = 1.0)、seed 23 で v112 pool = 0 cid。

### 6.2 判定 (実装指示書 Q-Z6)

- overlap_ratio 0.2-0.7 (部分重なり、想定通り): NO
- **overlap_ratio > 0.9 (ほぼ完全重なり)**: **YES** ← 該当
- overlap_ratio < 0.1 (ほぼ完全分離): NO

### 6.3 含意

- v112 pool (4 条件複合) は v108 top_k_100 の **ほぼ完全な subset**
- → 主題 §5 で導入した GPT 修正 1 (matched_pool 比較) の **意味が崩壊**:
  - 「同 cid pool で条件適応なし (matched_pool)」と「v108_original (top_k_100)」を比較する場合、両者は **ほぼ同じ cid 集合**
  - matched_pool は v108_original の subset で、本来狙っていた「条件適応の有無を切り分ける」比較ができない
- 主題機構案 (3 種類の atom_introduction_event) のうち matched_pool の独立性が確保できない

---

## §7 Q-Z7: 規模見積もり

### 7.1 events 数推定

| 区分 | 値 |
|---|---:|
| n_v112_events_low (1 cid 1 atom) | 94 |
| n_v112_events_high (25 atom 全展開) | 2,350 |
| n_v108_events (top_k_100 × 25 atom × 24 seeds) | 5,111 (per seed unique cid) |

### 7.2 計算量

- main run 推定: 1-3 分 (24 並列、events 規模次第)
- storage: 200-400 MB
- 累計 (v107-v112): 1.7-1.9 GB / 上限 6 GB (28-32%)
- 打ち切り条件 50% に **大幅余裕**

---

## §8 Code A 規律遵守 (実装指示書 §0.4 禁止事項)

### 遵守項目

- [x] 事前調査結果を見て勝手に設計を変えない
- [x] 観察軸を増やす方向への転換を提案しない
- [x] 母集団不足を発見しても条件を勝手に緩めない
- [x] Step A 以降の実装に進まない (本書は実測のみ)

### 「やってはいけない」を回避

- Multi-gate × timing 二次元観察への転換: **提案していない**
- within-cid design による Integration 形成プロセス解析: **提案していない**
- formation_relation 軸の主題化: **提案していない**
- 「面白い観察軸」の追加: **提案していない**

---

## §9 Web Claude/Taka 分岐判断要請事項 (Code A 判断はしない、選択肢提示のみ)

### §9.1 重大な乖離 4 件

| # | 乖離 | 想定 | 実測 | 影響 |
|---|---|---|---|---|
| 1 | Q-Z1 母集団 | per seed 数十 | per seed mean 3.9、24/24 で <10 | **設計破綻判定** |
| 2 | Q-Z2 Q3_threshold | 977 | 2,485 (Q2 = 977) | Web Claude 想定の取り違え可能性 |
| 3 | Q-Z6 cid pool 重なり | 0.2-0.7 | **0.958** | 主題 §5 matched_pool 比較が崩壊 |
| 4 | Q-Z5 v10.5 機構との重複 | 自明な再観察ではない | **(b) 部分的に重なる** | v10.11 違反パターン懸念 |

### §9.2 Web Claude/Taka 判断対象 (選択肢提示)

#### Q-Z1 母集団不足 (24/24 seed で設計破綻判定)

- 候補 (a): 主題 §13.2 4 項目固定発動 (条件緩和版は exploratory / appendix、main 判定は判定不能)
- 候補 (b): 主題変更 (4 → 2-3 条件の AND、または別の絞り込みルール)
- 候補 (c): 中止 (v10.12 主題見直し)

#### Q-Z2 Q3_threshold

- 候補 (a): Q2=977 (Web Claude 想定の修正、母集団 2-3 倍に拡大)
- 候補 (b): Q3=2,485 のまま (主題意図維持、ただし母集団更に縮小)

#### Q-Z6 cid pool 重なり

- 候補 (a): matched_pool 比較を撤回 (主題 §5 簡素化、v112 vs v108_original のみで比較)
- 候補 (b): v108 を別 pool 抽出に変更 (例: top_k_30 や random、独立性確保)
- 候補 (c): 主題変更 (cid pool 比較の前提を再設計)

#### Q-Z5 v10.11 既知との重複

- 候補 (a): 留保事項として記録して進める (条件 1 は v10.11 結論の実装適用と明記)
- 候補 (b): 主題変更 (v10.11 違反パターンの再発防止、Code A は積極的に (c) を疑うべきと指示書 §1.2 Q-Z5 にある)

### §9.3 Code A 提案 (規律 §0.4 違反のため、参考までの留保付き)

実装指示書 §0.4 で「Code A は対応案を提示するのみ、実装は Web Claude/Taka 分岐判断後」とあるため、以下は **対応案候補の提示** であり Code A の判断ではない:

- Q-Z1 + Q-Z6 が同時発生 → **主題機構の核心が崩れている** 可能性
- Web Claude/Taka が主題ドキュメント第 3 版の §5 機構案を再検討する必要があると見られる
- Code A としては Web Claude/Taka 判断後、修正版主題ドキュメント / 実装指示書を受領後に Step A 認識確認に進む準備が整っている

---

## §10 出力ファイル

- `developmental/v112/v112_step_z_environment_check.py` (実装、実測のみ)
- `developmental/v112/v112_step_z_report.md` (本書)
- `developmental/v112/outputs/step_z/q_z1_population.parquet` (24 rows)
- `developmental/v112/outputs/step_z/q_z2_lifespan.parquet`
- `developmental/v112/outputs/step_z/q_z3_familiarity.parquet`
- `developmental/v112/outputs/step_z/q_z6_cid_overlap.parquet` (24 rows)
- `developmental/v112/outputs/step_z/q_z4_5_7_qualitative.json`

---

## §11 一文サマリ (再掲)

Step Z 事前調査を実装指示書 §1 の Q-Z1〜Q-Z7 で実測 (target_step = cid.birth + 200 仮置き)、4 つの重大乖離検出 — Q-Z1 母集団 24/24 seed で AND_all<10 (設計破綻判定基準該当)、Q-Z2 Q3_threshold 想定 977 vs 実測 2,485 (Q2/Q3 取り違え可能性)、Q-Z6 cid pool 重なり overlap_ratio_v112=0.958 で matched_pool 比較崩壊、Q-Z5 v10.11 既知 (留保 21、β 機能直接観察) との部分的重複 (b)、Q-Z3 (seed 別採用妥当) と Q-Z4 (既存実装流用可能) と Q-Z7 (規模余裕あり) は整合、Code A は実装指示書 §0.4 禁止事項に従い設計判断せず対応案候補を §9 で提示、Web Claude/Taka 分岐判断要請事項 4 件 (主題 §13.2 4 項目固定発動 / 主題変更 / 中止 / matched_pool 撤回 / v108 pool 別抽出 / Q3 vs Q2 採用 / v10.11 重複の留保 vs 主題変更) を整理、Code A 提案として「Q-Z1 + Q-Z6 同時発生 → 主題機構の核心崩れの可能性、主題ドキュメント第 3 版 §5 機構案の再検討が見られる」を留保付きで提示、実装には進まず Web Claude/Taka 判断後の修正版主題ドキュメント / 実装指示書受領を待って Step A 認識確認に進む準備状態を維持。

---

*以上、Code A による v10.12 Step Z 事前調査報告。実装には進まず、Web Claude/Taka 分岐判断要請。Step A 認識確認は分岐判断後に着手する。*
