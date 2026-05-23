# v11.0.5 (v1105) Step A 認識確認 — Code A

*作成*: 2026-05-24、Code A
*親*: `v1105_phase_design.md` (Web Claude 設計書 v3、旧 Claude チェック + 2 AI 監査クリア済)
*対象*: Web Claude (相談役) + Taka (主題判断者)
*位置づけ*: v1105 進行表 Step A (Code A 認識確認、§5 確認要請 6 項目 + 実環境照合 + Step A' 追加確認要請 1 件)。判定 (a)/(b)/(c) は行わず、観察手順の実装可能性と Web Claude/Taka 領域への確認要請に限定。

---

## 0. 一文サマリ

v1105 設計書 v3 (2 AI 監査クリア済、4 つの非対称性 #L30-L33 を必須軸として組み込み、binary 判定および単一スコア化禁止、役割表は「仮割り当て + 観察支持 + 留保」3 列形式、v1105a 進行条件は最小 3 役割成立) を Code A 受領、§5 Code A 確認要請 6 項目すべてに認識を提示、実環境照合 (v1103 proposals.json 構造 = meta + proposals 14 件 / B_COUPLE 6 件 + D_SUBSUME 1 件 + MONITOR 7 件 / Couple endpoint atoms 12 unique 確定 / response_atom_distribution.parquet に **is_couple_link 列既存** = couple_hit_rate 計算済の集約のみで実装可 / scope 別 couple_hit_rate 粗集計 CID 4.29% / ESDE 4.60% / alpha 1.43% / beta 7.04% (unweighted)、ESDE 3 解像度 event 6.19 / step10 6.19 / window 1.43% で粒度感度確認 / density_summary.parquet 列 raw_density + qweighted_density + const_adjusted_density + mean_pairwise_sim の 3+1 種 × sim_basis (raw/norm) で並列保持 / observation_4_b_minus_a_cells 122 cells と observation_4_scope_filtered 10 rows が B_cmv/B_sal/B_crank の 3 種 boolean 詳細を含み Step F 役割「重要性 emit」に直接流用可) を完了、判定 (a)/(b)/(c) は行わず Web Claude/Taka 領域への確認要請 1 件提示: 確認要請 7 (設計書 §2.3 の「48 次元密度 raw / norm / qweighted / constitution-adjusted 4 種」と実体 density_summary.parquet の 3 列 (raw_density / qweighted_density / const_adjusted_density) × 2 sim_basis (raw / norm) = 6 値の対応、Code A 案 A: 「sim_basis='raw' の 3 種 + sim_basis='norm' の raw_density」で 4 種 / Code A 案 B: 「3 種 × 2 sim_basis = 6 種すべてを別レイヤー保持」/ どちらを採用するか確認)、§5 確認要請 1-6 への回答 (1: proposals.json 読み込み + is_couple_link 列利用で実装可 / 2: density_summary.parquet 既存列、ただし sim_basis 解釈は確認要請 7 / 3: 仮割り当て表は parquet + md 併記の 3 列形式 / 4: 観察 3 視覚化は heatmap 補助、parquet が 4 数値別レイヤー本体 / 5: couple_hit_rate 計測単位は unweighted (件数比) + prob-weighted (response_prob 加重) の 2 種を別カラム保持、scope × 粒度 (receiver_bin) 別集計 / 6: observation_4_b_minus_a_cells + observation_4_scope_filtered 両方を直接流用可、B_cmv/sal/crank 3 種 boolean を保持) を整理、Step B-H 想定実行時間 (B 環境準備 < 1s / C 観察 1 < 5s / D 観察 2 < 5s / E 観察 3 < 5s / F 観察 4 役割表 < 5s / G bit-identity 数十秒 / H 観察事実報告) + 規律遵守宣言 (絶対格言 #2/#5/#11/#12 + selector 化禁止 + binary 判定/単一スコア化禁止 + judgment 回避 + 0 を 1 にはできない歯止め + 観察方法有利化との区別 + 書込み unified/v1105/ 配下) を完了、確認要請 7 への回答受領後に Step B 着手予定、書込み unified/v1105/ 配下のみ。

---

## 1. §5 Code A 確認要請 6 項目への認識

### 1.1 §5-1: Constitution Couple データの読み込み + couple_hit_rate 実装

**実環境照合結果**:

| 項目 | 値 |
|---|---|
| proposals.json 所在 | `unified/v1103/outputs/main/proposals.json` |
| 構造 | dict (`meta` + `proposals`)、proposals は list of 14 dict |
| pattern 分布 | B_COUPLE 6 / D_SUBSUME 1 / MONITOR 7 |
| Couple endpoint atoms (6 pairs × 2) | 12 unique: ABS.other, BOD.mouth, COG.ignorance, COG.instinct, COM.cooperate, COM.speak, FND.intuition, FND.uninformed, REL.different, REL.together, SPC.outside, WLD.outer_realm |
| response_atom_distribution.parquet | 5,670 rows、列に **`is_couple_link` (bool) 既存** = atom が couple endpoint かどうかの判定既に計算済 |
| candidate_atom unique 数 | 139 |
| couple 接触 row 数 | 237 / 5,670 = 4.18% |

**Code A 実装方針**:
- proposals.json から Couple endpoint atoms set を抽出 (defensive 確認、is_couple_link 既存と一致確認)
- response_atom_distribution.parquet の `is_couple_link` 列を直接利用
- scope × 粒度 (receiver_bin) 別に couple_hit_rate を計算 (件数比 + prob-weighted)

**実装可能性**: ✓ 可能、独自計算なし、is_couple_link 既存列の集約のみ

### 1.2 §5-2: 48 次元密度 4 種の出力先

**実環境照合結果**:

| ファイル | per | 含まれる density 系列 |
|---|---|---|
| density_summary.parquet | (receiver_bin × metric × sim_basis × k) 486 rows | `raw_density` / `qweighted_density` / `const_adjusted_density` / `mean_pairwise_sim` (補助) |
| atom_centroids_48d_raw.parquet | per atom 325 rows | 48 axes raw centroid |
| atom_centroids_48d_normalized.parquet | per atom 325 rows | 48 axes normalized centroid |
| atom_quality.parquet | per atom 325 rows | focus_rate_mean / nonzero_raw_mean / nonzero_norm_mean / frac_OK |

**設計書 §2.3「raw / norm / qweighted / constitution-adjusted 4 種」と実体の対応**:

実体は density_summary.parquet 内に 3 列 (raw / qweighted / const_adjusted) × 2 sim_basis (raw / norm) = 6 値が並列で保持される。設計書の 4 種解釈は **確認要請 7 として明示** (§3 参照)。

**density 4 種の sim_basis 別平均 (実環境)**:

| sim_basis | raw_density | qweighted_density | const_adjusted_density | mean_pairwise_sim |
|---|---:|---:|---:|---:|
| raw | 0.8319 | (略) | (略) | 0.8319 |
| norm | 0.6470 | (略) | (略) | 0.6470 |

sim_basis を変えると raw_density 値も大きく変わる (0.83 → 0.65) ため、4 種解釈の確定が観察 2 の結論に直結。

### 1.3 §5-3: 仮割り当て表の出力フォーマット

**Code A 実装方針** (Web Claude/Taka 領域として要請、提案):
- parquet 本体: `observation_4_role_assignment.parquet`
  - 列: `role`, `scope_x_granularity_label`, `support_factual_basis`, `reservations`
  - 5 役割 × 各役割の scope × 粒度 = 行数は割り当て先によって変動 (1 役割が複数 scope に対応する場合あり)
- md 併記: `v1105_role_assignment_table.md` (Step H 観察事実報告内に組み込み)
- 設計書 §2.5 仮割り当て表通り「仮割り当て + 観察支持 + 留保」の 3 列形式を採用

### 1.4 §5-4: 観察 3 強度マップの視覚化方法

**Code A 実装方針**:
- データ本体: `observation_3_intensity_map.parquet` (per (scope, granularity, n_size_bin) × 4 + 数値別レイヤー)
  - 列: `scope` (CID/alpha/beta/ESDE)、`granularity` (event/step10/window/集約)、`n_size_bin` (CID_n=2..6+/alpha_n=*/beta_n=*/ESDE_*)、`lift_C` (Genesis 段 4-b)、`couple_hit_rate_unweighted` (Language 段 4-b)、`couple_hit_rate_prob_weighted` (補助)、`trajectory_r_stability_vs_maxprob` (Genesis 段 4-c)、`trajectory_r_diffusion_vs_maxprob` (Genesis 段 4-c)、`density_r_raw` / `density_r_norm` / `density_r_qweighted` / `density_r_const_adjusted` (Language 段 4-c、4 種の sim_basis 解釈は確認要請 7 後に決定)
- **異なる尺度を単一スコア化しない** (絶対格言 #11 + GPT 監査 §2.4 反映)
- 視覚化補助: heatmap × 4 layer (4 数値別) を `v1105_intensity_map.html` で生成、各 layer ごとに colorscale 別 (lift は RdBu、couple_hit_rate は Viridis、r は RdBu)
- binary 判定なし、閾値なし

### 1.5 §5-5: couple_hit_rate 計測単位

**Code A 実装方針**:
- **scope × 粒度 = receiver_bin 単位**で集計 (27 receiver_bin: CID_n=2..6+ / ESDE_window/step10/event / alpha_*/beta_*)
- 各 receiver_bin 内で:
  - **couple_hit_rate_unweighted** = (is_couple_link=True row 数) / (該当 receiver_bin の全 row 数)
  - **couple_hit_rate_prob_weighted** = Σ(is_couple_link × response_prob) / Σ(response_prob)
- 両方を別カラム保持 (絶対格言 #11、単一指標化しない)
- scope × 粒度別の粗集計 (実環境照合):
  - CID 4.29% (unweighted) / 4.71% (prob-weighted)
  - ESDE 4.60% / 5.25%
  - alpha 1.43% / 0.58%
  - beta 7.04% / 9.20%
  - ESDE_event 6.19%、ESDE_step10 6.19%、ESDE_window 1.43% (window で粒度感度顕著)

### 1.6 §5-6: observation_4_b_minus_a_cells 流用可否

**実環境照合結果**:

| ファイル | per | 含まれる情報 | 役割「重要性 emit」流用可否 |
|---|---|---|---|
| observation_4_b_minus_a_cells.parquet | (scope_filter × b_threshold × receiver_bin × metric) 122 rows | B_outstanding_score / B_cmv / B_sal / B_crank / A_outstanding_score | **直接流用可** |
| observation_4_scope_filtered.parquet | (scope_filter × b_threshold) 10 rows | Jaccard / Recall / Precision per scope | **直接流用可** |

**Code A 実装方針**:
- 役割「重要性 emit」割り当ては observation_4_b_minus_a_cells.parquet の per-receiver_bin B_cmv/B_sal/B_crank 詳細から、scope 別 B-A 非対称性 (#L32) を根拠として割り当て
- B_outstanding_score >= 1 (any) / >= 2 (strong) の両 threshold を併記、構造事実として scope 別の B 役割の独自性を記録
- 仮割り当て: 設計書 §2.5「重要性 emit | ESDE (全粒度) | A=0 / B=9 = B のみ独自領域 (#L32 v1104a 追加調整 4)」を継承

**実装可能性**: ✓ 可能、追加計算なし、既存出力の集約と意味付けのみ

---

## 2. 実装可能性 (Step B-H、想定実行時間)

| Step | 内容 | 想定実行時間 | 実装可能性 |
|---|---|---|---|
| B | 環境準備 (proposals.json + density_summary + observation_4 等の読み込み確認) | < 1s | ✓ |
| C | 観察 1 段 4-b 地形 (predecessor lift_C + couple_hit_rate 2 種) | < 5s | ✓ (確認要請 7 後) |
| D | 観察 2 段 4-c 地形 (trajectory r + density 4 種 r) | < 5s | ✓ (確認要請 7 後) |
| E | 観察 3 強度マップ (4 数値別レイヤー parquet + heatmap 補助) | < 5s | ✓ |
| F | 観察 4 役割表 (3 列形式 parquet + md) | < 5s | ✓ |
| G | bit-identity 3 層検証 (LAYER_A v1105 出力 + LAYER_B v1104a まで 1,502 frozen + v1104a 7 = 1,509) | 数十秒 | ✓ |
| H | 観察事実報告 (judgment 回避、観察事実のみ) | — | ✓ |

合計想定 < 1 分の実装時間 + bit-identity 数十秒。

---

## 3. 確認要請 7 (Web Claude/Taka 領域)

**論点**: 設計書 §2.3「48 次元密度 raw / norm / qweighted / constitution-adjusted 4 種」と density_summary.parquet 実体 (3 density 列 × 2 sim_basis = 6 値) の対応が複数解釈可能。

**実体構造**:

```
density_summary.parquet (486 rows = 27 receiver_bin × 3 metric × 2 sim_basis × 3 k)
├ raw_density           (sim_basis に応じて raw / norm 値が変わる)
├ qweighted_density     (同上)
├ const_adjusted_density (同上)
└ mean_pairwise_sim     (補助、sim_basis に応じて変わる)
```

**設計書「4 種」の解釈案**:

| 案 | 4 種の内容 | 利点 | 欠点 |
|---|---|---|---|
| **案 A (Code A 提案)** | sim_basis='raw' の raw_density / sim_basis='norm' の raw_density / sim_basis='raw' の qweighted_density / sim_basis='raw' の const_adjusted_density | 設計書「raw / norm / qweighted / constitution-adjusted」の文面に最も近い、4 種に揃う | norm 版の qweighted / const_adjusted は捨てる |
| 案 B | 3 density 列 × 2 sim_basis = 6 値すべて別レイヤー保持 | 全情報保持、絶対格言 #11 完全遵守 | 「4 種」と言わなくなる、列数増加 (6 列) |
| 案 C | sim_basis を統合して 3 種 (raw_density / qweighted_density / const_adjusted_density)、sim_basis は別カラムで保持 | 概念単位は 3 種で明確 | 設計書「4 種」と数が合わない |

**Code A 推奨**: **案 A** (設計書文面の素直な解釈、絶対格言 #11 と整合的、Phase Result で sim_basis の選択を明示)。

**Web Claude/Taka 判断**: 案 A / 案 B / 案 C / 別案要求。

---

## 4. 規律遵守宣言 (Step A 範囲)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.x / v1101a / v1102 / v1103 / v1104 / v1104a read-only、書込み unified/v1105/ のみ) |
| 絶対格言 #3 (\|effect\| 閾値) | ✓ (\|lift\|>0.01 / \|r\|>0.1 弱・0.3 中・0.5 強の参考ガイドのみ、強の主張は条件付記、binary 判定なし) |
| 絶対格言 #5 (新規 main run 禁止 / 観察軸追加禁止) | ✓ (post-process のみ、scope × 粒度 × n_size 既存軸継承、couple_hit_rate は既存 is_couple_link 列の集約) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (lift_C / couple_hit_rate / trajectory_r / density_r の 4 数値を別レイヤー保持、単一スコア化なし、density 4 種解釈は確認要請 7) |
| 絶対格言 #12 (judgment 回避) | ✓ (各観察の出口判定は Phase Result 領域、Code A は構造事実のみ) |
| 絶対格言 #14 (Taka 直感優先 + 原文保存) | ✓ (Taka 整理「分散化しない / 統合方向」を §0.3 で引用、原文継承) |
| GPT 修正必須 (binary 判定/単一スコア化禁止) | ✓ (観察 3 で 4 数値別レイヤー parquet + heatmap 補助、閾値なし) |
| GPT 修正必須 (役割表 3 列形式) | ✓ (仮割り当て + 観察支持 + 留保、確定表でない) |
| GPT 追加推奨 (観察方法有利化と区別) | ✓ (§2 観察方法を事前確定、結果が出ない場合の観察方法変更を提案しない、0 を 1 にはできない歯止め) |
| selector 化禁止 (役割表は post-process 観察) | ✓ (selector として動作させない宣言、Step F で割り当て根拠は構造事実のみ) |
| 統合方向の遵守 (§0.3) | ✓ (新規観察軸追加なし、v1104+v1104a の多軸を統合する形で 4 数値強度マップを作成) |
| 4 つの非対称性 (#L30-#L33) の必須軸組み込み | ✓ (Step C-F すべてで scope × 粒度 × n_size を主軸として継承) |
| 書込みパス unified/v1105/ 配下 | ✓ (Step B-H すべて unified/v1105/ 配下に書込み予定) |
| smoke 含めず | ✓ (v1105 は post-process のみ、main outputs のみ生成) |

---

## 5. Step A 完了後の進行 (確認要請 7 への Web Claude/Taka 回答受領後)

1. **確認要請 7 回答**: density 4 種の sim_basis 解釈確定 (Code A 推奨案 A)
2. 回答受領後 Step B から順次実装:
   - Step B (環境準備 + 既存 outputs 読み込み確認)
   - Step C (観察 1: predecessor lift_C + couple_hit_rate 2 種)
   - Step D (観察 2: trajectory r + density 4 種 r)
   - Step E (観察 3: 4 数値強度マップ別レイヤー parquet + heatmap)
   - Step F (観察 4: 仮割り当て表 3 列形式)
   - Step G (bit-identity 3 層検証)
   - Step H (観察事実報告、judgment 回避、Web Claude Phase Result + Taka 主題評価領域)

---

## 6. 一文サマリ (再掲)

v1105 設計書 v3 (2 AI 監査クリア、4 非対称性 #L30-L33 を必須軸組み込み、binary 判定/単一スコア化禁止、役割表 3 列形式、v1105a 進行条件最小 3 役割) を Code A 受領、§5 確認要請 6 項目すべてに認識提示 (1: proposals.json B_COUPLE 6 件 / Couple endpoint 12 atoms / response_atom_distribution に **is_couple_link 列既存** = couple_hit_rate 集約のみで実装可、CID 4.29% / ESDE 4.60% / alpha 1.43% / beta 7.04%、ESDE_window 1.43% で粒度感度確認 / 2: density_summary は 3 density 列 × 2 sim_basis = 6 値、4 種解釈は確認要請 7 / 3: 仮割り当て表 parquet + md 併記 3 列形式 / 4: 観察 3 視覚化 heatmap 補助、parquet が 4 数値別レイヤー本体 / 5: couple_hit_rate は unweighted + prob-weighted 2 種別カラム / 6: observation_4_b_minus_a_cells + scope_filtered 両方直接流用可、B_cmv/sal/crank 詳細) し、Web Claude/Taka 領域への確認要請 7 提示 (density 4 種の sim_basis 解釈、Code A 推奨案 A = sim_basis='raw' の 3 種 + sim_basis='norm' の raw_density で 4 種に揃える) し、Step B-H 想定実行時間 (B 環境準備 / C 観察 1 / D 観察 2 / E 観察 3 / F 観察 4 / G bit-identity / H 観察事実報告) + 規律遵守宣言 (絶対格言 #2/#5/#11/#12/#14 + selector 化禁止 + binary/単一スコア化禁止 + judgment 回避 + 0 を 1 にはできない歯止め + 観察方法有利化との区別 + 統合方向遵守 + 4 非対称性必須軸 + 書込み unified/v1105/ 配下) を完了、確認要請 7 回答受領後に Step B から実装着手予定、書込み unified/v1105/ 配下のみ。
