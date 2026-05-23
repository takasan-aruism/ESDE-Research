# v11.0.4a (v1104a) Step A' 認識確認 — Code A

*作成*: 2026-05-23、Code A
*親*: `v1104a_phase_design.md` (Web Claude 設計書 v2、GPT 修正必須 4 点 + 追加推奨 3 点 + Gemini 1 点反映済)
*対象*: Web Claude (相談役) + Taka (主題判断者)
*位置づけ*: v1104a 進行表 Step A' (Code A 認識確認、§6.1.1 6 項目確認 + 実環境照合 + 確認要請事項)。判定 (a)/(b)/(c) は行わず、観察手順の実装可能性と Web Claude/Taka 領域への確認要請事項に限定。

---

## 0. 一文サマリ

v1104a 設計書 v2 (2 AI 監査反映版) を受領、§6.1.1 6 項目すべてに Code A の認識を提示、実環境照合 (v10.6 window_trajectory n_core_member NaN 件数 24 seeds 31,482 行で 0 件確認 / final_state 'ghost' でも n_core_member 記録あり 値 2 / v1104 既存 5 parquet 構造確認 / v1103 density 4 種の実体特定 / v1102 + v1104 observation_4_b_overlap の scope 埋め込み確認) を完了、判定 (a)/(b)/(c) は行わず観察手順の実装可能性 + Web Claude/Taka 領域への確認要請事項 3 件を提示: 確認要請 1 (追加調整 1 入力 gap: `observation_2_shuffle_variants.parquet` は per (seed, scope) で 144 行集約済 / per-chain shuffle B/C は保持されておらず、Step B' で `v1104_step_h3_reinvestigation.py` の reinvestigation_2 関数を per-chain 保持に拡張する補助実装が必要)、確認要請 2 (追加調整 3 入力 gap: 設計書 §2.3.3「48 次元密度 4 種 raw/norm/quality_weighted/receiver_conditioned」と実体 `density_summary.parquet` の `raw_density / qweighted_density / const_adjusted_density` の 3 種 + 別ファイル `atom_centroids_48d_normalized.parquet` の per-atom norm という構造の解釈、4 種をどう特定するか、または 3 種で進めるか確認)、確認要請 3 (追加調整 1 で integration_n_members の per-window 復元は v1102 では既に `integration_composition_alpha.parquet` / `_beta.parquet` で per (seed, alpha_id, n_members) 集約済が存在、設計書 §1.5 の「alpha_lifecycle_log / beta_distribution_log から per-window 復元」をこの既存集約で代替可能か確認)、NaN ハンドリングは Gemini 監査懸念が実環境では発生していないため defensive 処理 (NaN 検出時は警告 + 該当 row 除外) を Step B' で実装する方針提案、追加調整 2/4 は既存出力に scope/n_members 情報が埋め込み済で追加 join 不要のため Step C'/E' は §2 の手順通り実装可能、判定語制限 + selector 化禁止 + judgment 回避 + 0 を 1 にはできない歯止め + 観察方法有利化との区別を全 Step で堅持、書込み unified/v1104a/ 配下のみ。

---

## 1. §6.1.1 6 項目への Code A 認識

### 1.1 NaN ハンドリング (Gemini Architect 監査)

**実環境照合結果** (Code A、2026-05-23):

| 集計対象 | 値 |
|---|---:|
| v10.6 window_trajectory 全 24 seeds 行数 | 31,482 |
| n_core_member NaN 件数 | **0** |
| n_core_member 欠損率 | 0.0000% |
| unique CIDs across all seeds | 316 |
| final_state 値 | hosted (688) / reaped (373) / ghost (1) |
| final_state='ghost' での n_core_member | 値=2 (記録あり、NaN ではない) |
| n_core_member 値域 | 2-5 (全 final_state で同じ) |

→ Gemini 監査懸念「CID Ghost 化による NaN/Null」は **v10.6 window_trajectory レベルでは発生していない**。Ghost 状態でも n_core_member が記録される (推測: v10.6 集計時点で消滅前の最大 n_core_member が保存されている)。

**Code A 処理方針提案**:
- 主方針: NaN 検出時の処理は **defensive 実装**で行う (実際には発生しないが、念のため対応)
  - NaN 検出 → 警告ログ出力 + 該当 row 除外、chain は edge 単位で除外 (chain 全体除外しない)
  - 集計時に NaN 件数を report として記録、観察事実報告 Step H' で「NaN 検出 0 件」を明記
- 副方針: Ghost 状態の CID も含めて join (final_state='ghost' でも n_core_member 値あり、除外不要)
- 追加調整 2 (CID scope の cid_n_core 層化) で n_core_member=2..5 の 4 bin (n=2/3/4/5+) に分割、5+ には n=5 のみ含まれる (実体 n_max=5、設計書 §1.5 の n=5+ は念のため将来拡張用)

**Web Claude/Taka 領域**: NaN 件数 0 の実測を踏まえて defensive 実装で進める方針で良いか確認 (実装は §1.1 主方針通り Step B' で実施)。

### 1.2 n-size 列の使い分け (GPT 修正必須 B)

**実環境照合結果**:

| 列名 | ファイル | per | 用途 |
|---|---|---|---|
| **cid_n_core** | v106/.../window_cid_alignment_seed{N}.csv → n_core_member 列 | (seed, cognitive_id) | CID scope の n-size 軸 |
| **integration_n_alpha_members** | v1101a/.../integration_composition_alpha.parquet → n_members 列 | (seed, alpha_id) | alpha scope の n-size 軸 |
| **integration_n_beta_members** | v1101a/.../integration_composition_beta.parquet → n_members 列 | (seed, beta_id) | beta scope の n-size 軸 |

→ Code A は **cid_n_core / integration_n_alpha_members / integration_n_beta_members の 3 列を別列名で扱う**。設計書 §1.5 の `integration_n_members` を alpha と beta で別ファイル由来であることを踏まえて、Code A 実装では分離 (絶対格言 #11「概念単位を雑に扱わない」)。

ESDE 3 解像度 (event/step10/window) は集約 scope のため n-size 層化対象外 (設計書 §1.5 通り)。

### 1.3 追加調整 1 の self-loop 分離 + shuffle B/C 別集計 (GPT 追加推奨 5)

**実環境照合結果**:

| 入力ファイル | per | 含まれる情報 | 追加調整 1 に必要か |
|---|---|---|---|
| observation_2_shuffle_variants.parquet | (seed, scope) 144 行 | sim_actual / sim_shuffle_A/B/C / lift_A/B/C **scope 集約済** | per-chain ではない、**追加調整 1 で再計算必要** |
| observation_2_predecessor_chain.parquet | (seed, scope, scope_id, metric) 39,537 chains | chain_length / n_self_loops / lift_over_baseline (shuffle A 1 種のみ) | per-chain あり、shuffle A 既存 |
| observation_2_restratified.parquet | (scope, n_bin, gini_bin) 27 行 | bin 内 lift_mean、self_loop_rate | bin 集約済、参考のみ |
| observation_2_self_loop_split.parquet | (scope, is_full_self_loop) 11 行 | 全体 atom_change_rate | scope 集約済、参考のみ |

→ **追加調整 1 で per-chain shuffle B/C を再計算する Step B' 補助実装が必要**。これは設計書 §1.4 「既存出力流用のみ」原則と一見矛盾するが、Step H-3 で per-chain shuffle B/C は内部計算されており scope 集約のみ保存していた構造のため、**既存 reinvestigation_2 関数を per-chain 保持に拡張する形で対応** (新規 main run なし、ESDE 内部書き戻し 0、絶対格言 #5 物理層 frozen 維持)。

**Web Claude/Taka 領域 確認要請 1**: 追加調整 1 で per-chain shuffle B/C 再計算を Step B' で実施する方針 (新規機構なし、既存 reinvestigation_2 拡張)、これを「既存出力流用」の範囲内と判断するか確認。代案: Step B' で v1104a 用に専用 per-chain shuffle 再計算スクリプトを書く (v1104 既存 output には触らず unified/v1104a/outputs/main/observation_2_per_chain_shuffle.parquet として新規生成)。

Code A 提案: **代案採用** (v1104 出力を改変せず v1104a で独立 per-chain shuffle parquet を生成、設計書原則と完全整合)。

self-loop 分離 + shuffle B/C 別集計の Step B' 実装方針:
- shuffle B と shuffle C を平均で混ぜず、別カラム (lift_B, lift_C) で保持
- self-loop / non-self-loop を分離 (is_full_self_loop=True/False で別行)
- 集約軸: (scope × n-size_bin × shuffle_type × is_self_loop)

### 1.4 追加調整 3 の比較条件固定 (GPT 修正必須 C)

**実環境照合結果**:

| ファイル | per | 含まれる予測指標 |
|---|---|---|
| density_summary.parquet | (receiver_bin × metric × start_atom × sim_basis × k) 486 行 | `raw_density` / `qweighted_density` / `const_adjusted_density` (3 種) + `mean_pairwise_sim` / `conscious_frac` |
| atom_centroids_48d_raw.parquet | per atom (325 行) | 48 axes raw centroid |
| atom_centroids_48d_normalized.parquet | per atom (325 行) | 48 axes normalized centroid |
| trajectory_metrics_per_chain | per chain (Step D + Step H-4) | stability / diffusion / chain_len / unique_count |
| response_atom_distribution.parquet | (receiver_bin × metric × start_atom × sim_basis × k × candidate) 5,670 行 | response_max_prob / response_entropy (5 各 distribution に集約後) |

→ **設計書 §2.3.3 の「48 次元密度 4 種 (raw / norm / quality_weighted / receiver_conditioned)」と実体不一致**:
- 実体は per-receiver_bin で `density_summary.parquet` 内の 3 種 (`raw_density`, `qweighted_density`, `const_adjusted_density`)
- per-atom 別ファイル `atom_centroids_48d_normalized.parquet` は normalized centroid (per-atom、receiver_bin に対応していない)
- 「receiver_conditioned」が実体のどれに対応するか不明 (`const_adjusted_density` か?)

**Web Claude/Taka 領域 確認要請 2**: 設計書 §2.3.3「48 次元密度 4 種」の実体特定。Code A 提案 2 案:
- **案 A** (3 種で進む): `density_summary.parquet` の 3 種 (raw_density / qweighted_density / const_adjusted_density) を density 比較対象とし、`mean_pairwise_sim` も補助で並べる。`atom_centroids_48d_*` (per-atom) は本主題範囲外。比較 4 種 → 3 種に縮減と Web Claude に報告
- **案 B** (4 種に揃える): `const_adjusted_density` を「receiver_conditioned」と読み替え、`raw_density` = raw、`qweighted_density` = quality_weighted、`const_adjusted_density` = receiver_conditioned とし、`norm` を別途定義 (例: density_summary に追加列を post-process で計算: raw_density / max(raw_density) for norm) → 仮想 norm 列を生成、設計書通り 4 種で進む

Code A 提案: **案 A** (3 種で進む、設計書修正は Web Claude 領域)。理由: density_summary の実体 3 種で構造的記述は十分可能、4 種化のための仮想 norm 計算は人為性追加 (絶対格言 #4 と #5 違反候補)、案 B は selector 化禁止精神とは別軸で「指標の人為合成」を導入してしまう。

比較条件固定の Step D' 実装方針 (案 A 採用前提):
- 同一 receiver_bin・同一 scope (CID / ESDE 別、alpha/beta は scope-filter で参考のみ)
- response 指標は max_prob / entropy の 2 種に固定 (top3_mass / gini 使わない)
- coverage 欠損 (trajectory 値 NaN or density 値 NaN) は除外、別 parquet (observation_3_density_coverage.parquet) に件数記録
- ランキングは (scope × predictor × response) 別、scope 横並びにしない

### 1.5 追加調整 4 の表現規制 (GPT 修正必須 D + 追加推奨 6)

**実環境照合結果**:

| 入力ファイル | 構造 | scope-filter 可能性 |
|---|---|---|
| observation_4_b_overlap.parquet | 81 cells = 27 receiver_bin × 3 metric (`atom_delta` / `rank1_flip_density` / `unit_kl_static`) | receiver_bin から scope 抽出可 (CID_n=2..6+ / ESDE_window/step10/event / alpha_*/beta_*) |
| outstanding_cells.parquet (v1102) | 81 cells、A_outstanding_high 等 | 同上 |
| primary_table.parquet (v1102) | 81 cells | 同上 |

→ 追加調整 4 は `observation_4_b_overlap.parquet` の 81 cells を receiver_bin prefix で 5 グループ (all / CID / alpha / beta / ESDE) に分割、per-scope で A∩B / A∪B / A\B / B\A 再計算可能。

**Code A 表現規制の遵守宣言** (Step E'/H' に向けて):
- 「B を selector として使える」「B が selector として使える可能性」を **書かない**
- 「B が A primary 化を次主題で点検する根拠を提供する」までを上限表現
- B の意味判定 (例: 「B は ESDE 自身の重要性 emit を表す」) を **書かない**、観察事実 (例: 「B が独自に拾う cell の件数は scope X で N 件、scope Y で M 件」) のみ記録
- selector 化禁止: post-process 仮想評価のみ (B primary 化の Recall/Precision 数値計算は記録するが「B primary 化が妥当か」の判定は行わない)

### 1.6 観察方法有利化との区別 (GPT 追加推奨 7)

**Code A の運用宣言**:
- 追加調整 1-4 はすべて §2 の手順を逸脱しない (新しい層化軸や scope を追加しない)
- 結果が予想と違う (例: 追加調整 1 で ESDE/CID でも lift が顕在化しない) → 観察方法を変えて lift を探さない、(b) または (c) の出口として記録
- 追加調整 1 で「特定 n-size_bin でだけ lift が出る」結果が出ても、その bin を強調する報告にしない (構造事実として 4 bin 全てを並べて記録)
- 追加調整 3 で「特定の density と特定の trajectory metric だけが高い |r| を出す」結果が出ても、そのペアだけを強調しない (同一条件下の全ランキングを記録)
- 0 を 1 にはできない歯止め: 全 4 追加調整で結果が出ない場合 (全 (b) 出口) でも観察事実として記録、追加調整 5 への観察方法変更を提案しない (v1104b としてバージョン上げするのは Taka 判断領域)

---

## 2. 追加調整 1-4 の実装可能性

### 2.1 追加調整 1 (Step B'): 観察 2 を scope × n-size 層化

| 項目 | Code A 認識 |
|---|---|
| 入力データ | observation_2_predecessor_chain.parquet (per-chain shuffle A あり) + v1104a 新規生成 observation_2_per_chain_shuffle.parquet (per-chain shuffle B/C、確認要請 1 承認後) + v10.6 n_core_member + v1101a integration_composition_alpha/beta |
| n-size join | CID: scope_id → cognitive_id で join cid_n_core / alpha: scope_id → alpha_id で join n_alpha_members / beta: scope_id → beta_id で join n_beta_members / ESDE 3 解像度: 層化対象外 (集約 scope) |
| 集約軸 | (scope × n-size_bin × shuffle_type × is_self_loop) |
| 出力 | observation_2_scope_stratified.parquet |
| 想定実行時間 | per-chain shuffle 再計算込みで 60-90s (Step H-3 reinvestigation_2 と同等) |
| 実装可能性 | 可能 (確認要請 1 承認後) |

### 2.2 追加調整 2 (Step C'): 観察 3 を CID scope の cid_n_core 層化

| 項目 | Code A 認識 |
|---|---|
| 入力データ | observation_3_trajectory_response.parquet (既存、receiver_bin に CID_n=2..6+ 埋め込み済) |
| n-size 層化 | CID scope 行を抽出 (receiver_bin.str.startswith('CID_n=')) → cid_n_core_bin = receiver_bin から既に取得可能、追加 join 不要 |
| 集約軸 | (cid_n_core_bin) で stability_vs_maxprob / diffusion_vs_maxprob / stability_vs_entropy / diffusion_vs_entropy の Pearson + Spearman r |
| 参考値 | ESDE-only scope (receiver_bin.str.startswith('ESDE_')) の全体 |r| を必ず並べる |
| 出力 | observation_3_scope_n_stratified.parquet |
| 想定実行時間 | < 5s (既存 parquet の再集約のみ) |
| 実装可能性 | 可能、§2 手順通り |

### 2.3 追加調整 3 (Step D'): 観察 3 vs 48 次元密度

| 項目 | Code A 認識 |
|---|---|
| 入力データ | trajectory_metrics_per_chain (Step D 既存) + response_atom_distribution + density_summary (v1103) |
| density 種類 | 3 種 (案 A、確認要請 2 承認後): raw_density / qweighted_density / const_adjusted_density、+ mean_pairwise_sim 補助 |
| response 指標 | max_prob と entropy の 2 種に固定 |
| 比較条件 | 同一 receiver_bin・同一 scope (CID / ESDE 別)、coverage 欠損は別 parquet 記録 |
| 出力 | observation_3_density_comparison.parquet + observation_3_density_coverage.parquet |
| 想定実行時間 | < 10s |
| 実装可能性 | 可能 (確認要請 2 案 A 承認後) |

### 2.4 追加調整 4 (Step E'): 観察 4 を scope-filter

| 項目 | Code A 認識 |
|---|---|
| 入力データ | observation_4_b_overlap.parquet (81 cells、既存) |
| scope-filter | receiver_bin prefix で 5 グループ (all / CID / alpha / beta / ESDE) |
| 計算 | per-scope で A∩B / A∪B / A\B / B\A、Jaccard / Recall / Precision |
| B 意味判定 | 行わない (Step E'/H' で観察事実のみ記録) |
| selector 化 | 禁止 (post-process 仮想評価のみ、ESDE 内部書き戻し 0) |
| 出力 | observation_4_scope_filtered.parquet |
| 想定実行時間 | < 5s |
| 実装可能性 | 可能、§2 手順通り |

---

## 3. 確認要請 (Web Claude/Taka 領域)

### 3.1 確認要請 1 — 追加調整 1 の per-chain shuffle B/C 実装方針

**論点**: observation_2_shuffle_variants.parquet は per (seed, scope) 144 行に集約済で、追加調整 1 の §2.1.4 手順 1「chain ごとに shuffle B と shuffle C の lift を別集計で取得」を満たさない。

**Code A 案** (採用したい):
- v1104 既存 output を改変せず、v1104a で独立 per-chain shuffle 再計算スクリプトを書く
- 出力: `unified/v1104a/outputs/main/observation_2_per_chain_shuffle.parquet`
- Step H-3 `reinvestigation_2` 関数の per-chain 計算ロジック (sim 系列を chain 内 permutation/chain 間入替/global pool で shuffle して再計算) を v1104a 用に複製
- 既存出力流用原則と整合 (v1104 出力 read-only 維持、v1104a に独立に保存)

**Web Claude/Taka 判断**: 採用 / 別案要求。

### 3.2 確認要請 2 — 追加調整 3 の density 4 種の実体特定

**論点**: 設計書 §2.3.3「48 次元密度 4 種 (raw / norm / quality_weighted / receiver_conditioned)」が `density_summary.parquet` の実体 3 種 (raw_density / qweighted_density / const_adjusted_density) と一致しない。

**Code A 案 A** (採用したい): 3 種で進む、density_summary の 3 種を density 比較対象、`mean_pairwise_sim` も補助で並べる。`atom_centroids_48d_*` (per-atom) は本主題範囲外として除外。
**Code A 案 B** (代替): 4 種に揃える、`const_adjusted_density` = receiver_conditioned と読み替え、norm を後付け計算で生成。ただし人為性追加のため非推奨。

**Web Claude/Taka 判断**: 案 A / 案 B / 別案要求。

### 3.3 確認要請 3 — 追加調整 1 の integration_n_members の per-window 復元 vs 既存集約

**論点**: 設計書 §1.3「alpha_lifecycle_log / beta_distribution_log から per-window 復元」と書かれているが、実体は v1101a/integration_composition_alpha.parquet / _beta.parquet で per (seed, alpha_id, n_members) の **集約済 (final n_members of integration's lifecycle)** が既に保存されている。

**Code A 案** (採用したい): 既存集約 `integration_composition_alpha/beta.parquet` の n_members を使用する。理由: per-window 復元は時系列内で n_members 値が変動 (Integration の memberships は段階的に増減) するが、本主題は構造的指標としての n-size 層化を目的とし、Integration の代表 n-size として lifecycle 集約値で十分。per-window 復元は Step B (Step D) と Step H-4 で既に同方式を採用済、整合性も担保。

**Web Claude/Taka 判断**: 採用 / per-window 復元を要求 (時間コスト増、代替手段なし)。

---

## 4. NaN / 空欄 / Ghost 化の処理方針 (§1.7 設計書追記候補)

Code A が Step B'-E' で適用する処理方針:

| ケース | 処理 |
|---|---|
| cid_n_core NaN (実環境 0 件、念のため) | 該当 row 除外、警告ログ、件数 report |
| integration_n_alpha/beta_members NaN | 該当 row 除外、警告ログ、件数 report (alpha/beta scope のみ) |
| Ghost 化 CID (final_state='ghost') | n_core_member 値あり (2)、除外しない (実観測通り) |
| trajectory_stability NaN (chain_length < 2) | 既存 Step D 通り NaN として保存、相関計算時に dropna |
| density NaN (該当 receiver_bin に density 計算行なし) | 追加調整 3 で coverage 欠損として別 parquet 記録、ランキング比較から除外 |
| observation_2 chain で predecessor_cid_id 不在 | observation_2_predecessor_chain.parquet 構築時点で既に除外済 (Step C で確認済)、Step B' で追加処理不要 |

---

## 5. 規律遵守宣言 (Step A' 範囲)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.x / v1101a / v1102 / v1103 / v1104 read-only、書込み unified/v1104a/ のみ) |
| 絶対格言 #3 (\|effect\| 閾値) | ✓ (\|lift\|>0.01 / \|r\|>0.1 弱・0.3 中・0.5 強の参考ガイド、強の主張は条件を必ず付記) |
| 絶対格言 #5 (新規 main run 禁止 / 観察軸追加禁止) | ✓ (追加調整 1-4 は §2 手順を逸脱しない、per-chain shuffle 再計算は既存 reinvestigation_2 拡張で範囲内、新規 main run なし) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (cid_n_core / integration_n_alpha_members / integration_n_beta_members を別列名で扱う、ESDE 3 解像度は層化対象外) |
| 絶対格言 #12 (judgment 回避) | ✓ (本書で (a)/(b)/(c) 判定なし、Web Claude/Taka 領域として明記) |
| GPT 追加 4 (判定語制限) | ✓ (「連想」「成功/失敗」「意味がある/ない」未使用) |
| GPT 修正必須 D (selector 表現規制) | ✓ (B selector 表現を Step E'/H' で書かない宣言) |
| GPT 追加推奨 6 (B 意味判定先送り) | ✓ (追加調整 4 で B の意味判定なし宣言) |
| GPT 追加推奨 7 (観察方法有利化と区別) | ✓ (結果が出ない場合の観察方法変更を提案しない宣言、0 を 1 にはできない歯止め継承) |
| Gemini Architect 監査 (NaN ハンドリング) | ✓ (実環境照合で NaN 0 件確認、defensive 実装方針提示) |
| 書込みパス unified/v1104a/ 配下 | ✓ (Step B'-H' すべて unified/v1104a/ 配下に書込み予定) |
| smoke 含めず | ✓ (v1104a は smoke run なし、main outputs のみ生成) |
| 観察 4 selector 化禁止 (v1104 §2.4.5 継承) | ✓ (post-process 仮想評価のみ、ESDE 内部書き戻し 0) |

---

## 6. Step A' 完了後の進行 (確認要請 3 件への Web Claude/Taka 回答受領後)

1. **確認要請 1 回答**: per-chain shuffle B/C の実装方針確定 (Code A 案: v1104a 独立 parquet 生成)
2. **確認要請 2 回答**: density 4 種 vs 3 種の方針確定 (Code A 案 A: 3 種で進む)
3. **確認要請 3 回答**: integration_n_members の代表値 vs per-window 復元の方針確定 (Code A 案: 既存集約使用)

回答受領後 Step B' から順次実装:
- Step B' (追加調整 1): per-chain shuffle 再計算 + scope × n-size 層化
- Step C' (追加調整 2): observation_3 の CID scope cid_n_core 層化
- Step D' (追加調整 3): observation_3 vs density 比較
- Step E' (追加調整 4): observation_4 scope-filter
- Step F' (グラフ HTML)
- Step G' (bit-identity 拡張、LAYER_A 17 ファイル予定)
- Step H' (観察事実報告、judgment 回避、Web Claude/Taka 統合 Phase Result 領域)

---

## 7. 一文サマリ (再掲)

v1104a 設計書 v2 (2 AI 監査反映版) を Code A 受領し、§6.1.1 6 項目すべてに認識を提示 (NaN ハンドリング = 実環境 v10.6 24 seeds 31,482 行で NaN 0 件確認 + Ghost 化 CID でも n_core_member 値あり + defensive 実装方針 / n-size 列 = cid_n_core / integration_n_alpha_members / integration_n_beta_members の 3 別列で扱う宣言 / 追加調整 1 self-loop 分離 + shuffle B/C 別集計 = §2.1.4 通り実装宣言 / 追加調整 3 比較条件固定 = 同一 receiver_bin / 同一 response (max_prob, entropy 2 種) / 同一 scope で実装宣言 / 追加調整 4 表現規制 = B selector 表現を書かない + B 意味判定なし宣言 / 観察方法有利化との区別 = 0 を 1 にはできない歯止め遵守宣言) し、判定 (a)/(b)/(c) を行わず Web Claude/Taka 領域への確認要請 3 件提示 (1: 追加調整 1 の per-chain shuffle B/C 実装方針 = Code A 案 v1104a 独立 parquet 生成、2: 追加調整 3 の density 4 種 vs 実体 3 種 = Code A 案 A 3 種で進む、3: 追加調整 1 の integration_n_members 復元 = Code A 案 既存 v1101a/integration_composition 集約値使用)、追加調整 1-4 の実装可能性確認 (Step B' 60-90s / C' < 5s / D' < 10s / E' < 5s) + NaN/空欄/Ghost 化処理方針 + 規律遵守宣言 (絶対格言 #2/#3/#5/#11/#12 + GPT 修正必須 D / 追加推奨 6/7 + Gemini NaN + selector 化禁止 + 書込み unified/v1104a/ 配下) を整理し、確認要請 3 件への回答受領後に Step B' から実装着手予定、書込み unified/v1104a/ 配下のみ。
