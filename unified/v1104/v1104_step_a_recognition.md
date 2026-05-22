# v1104 Step A 認識確認 — Code A

*作成*: 2026-05-23、Code A
*親*: `v1104_phase_design.md` (Web Claude 改訂版 v2、GPT 5 点 + Gemini 1 点反映済) + Taka 配置承認 (2026-05-23)
*対象*: Web Claude (相談役、Genesis 側) + Taka (実装着手判断)
*目的*: 設計書 §6.1.1 認識確認 6 項目の repo 実状照合。実装着手前の判断材料整理。

---

## 0. 一文サマリ

v1104 設計書 §6.1.1 認識確認 6 項目の Code A 実環境照合結果として、**時間軸同期** (Gemini 運用注意) は v10.5 alpha_membership_log が step=25000 (run 終了時) のスナップショットのみで per-window 時系列を直接持たないが alpha_lifecycle_log (424 events × 267 step in seed 0、event_type=birth/member_ghosted/active_to_recorded、member_cids '|' 区切り) で per-step 構成変化を復元可能で v10.6 step_at_window_end と v1101a window (19-69、v10.6 は 20-69) を介して per-window 化可能、cid_id 整合性 (v10.5 alpha_member 27 cid ⊂ v1101a CID scope 135 cid、overlap 27 / 不整合 0) 確認、**IID 表現** (GPT 修正必須 A) は §1.5 通り新規構造なしで既存 (α/β/member_cids/attention_candidate_id/predecessor_attention_ref/cid_state_ledger) の参照表現として読む方針確定、**観察 1 の Jaccard 厳密化** (GPT 修正必須 B) は k=1 一致率と top-k Jaccard (k=3/5) を別指標として算出する設計を堅持、**観察 2 の判定語制限** (GPT 追加 4) は Code A が「連想」と判定しない・cid/atom/category/similarity 推移のみ記録する方針を §2.2.5 通り遵守、**観察 3 の重複回避** (GPT 追加 5) は v1101a 観察 B 既知事実 (認知優位安定/意識優位移動) は再観察せず trajectory↔response_atom_distribution の対応観察のみ、**観察 4 の selector 化禁止** (GPT 修正必須 C) は post-process 仮想評価のみで ESDE 内部に書き戻さない方針を堅持、入力データ規模 (v1101a attention_emit 1.73M records / alpha_lifecycle ~25,000 events 24 seeds / v10.6 4 解像度 trajectory) すべて読み込み可能、確認要請 2 件 (window 範囲統一 v1101a 19-69 vs v10.6 20-69 / observation_b の Jaccard proxy 既存出力の v1101a/outputs/main/ への有無確認) を §5 で整理、新規 main run 不要・既存出力流用のみ・想定実装 4-5 日 (設計書 §6.1 想定 6-7 日内、観察 4 が selector 化禁止で軽量化)。

---

## 1. 設計書 §6.1.1 認識確認 6 項目への Code A 回答

### 1.1 時間軸同期 (Gemini Architect 運用注意)

設計書 §1.6 + §6.1.1 で「v10.5 alpha_membership と v1101a window の対応 / v10.6 trajectory と v1101a/v1102 window / cid_id 整合性」の検証を指定。

#### 1.1.1 v10.5 alpha_membership_log_seed0.csv の実体

- **rows: 27 / unique step: 1 (step=25000) / unique cid_id: 27**
- run 終了時 (step=25000) の最終所属スナップショットのみ。per-window 時系列を直接持たない
- → 観察 1 で per (alpha_id, window) の member 構成を追うには alpha_lifecycle_log が必要

#### 1.1.2 alpha_lifecycle_log_seed0.csv で per-step 復元可能

- **rows: 1,063 / unique step: 267 / unique alpha_id: 424**
- event_type 分布: birth 424 / member_ghosted 545 / active_to_recorded 94
- 各イベントに member_cids ('|' 区切り) 列があり、構成変化を per-step で復元できる
- 例: alpha_id 0 は step 248 に "2|22" で生まれ、step 11000 に "22" のみに (member 2 が ghost 化)

#### 1.1.3 window 範囲の差

| データ | window 範囲 | step 対応 |
|---|---|---|
| v10.6 window_trajectory_seed0 | 20-69 (50 windows) | step_at_window_end 500-25000 |
| v1101a attention_emit_seed0 | 19-69 (51 windows、+1) | step ? (window=19 は v10.6 にない) |

→ v1101a が window=19 を持つ理由は smoke 期間または初期化期間と推測。観察 1/3 で window 範囲を統一するか含めるかを Web Claude 確認要請 (§5.1)。

#### 1.1.4 cid_id 整合性

| 集合 | unique cid 数 | overlap |
|---|---:|---:|
| v10.5 alpha_member cid (seed 0) | 27 | — |
| v1101a CID scope scope_id (seed 0) | 135 | — |
| **overlap** | **27** | v10.5 ⊂ v1101a (alpha 所属 cid は全 cid に含まれる) |
| v105 only | 0 | (不整合なし) |
| v1101a only | 108 | (alpha に所属しない cid) |

→ cid_id の意味は同じ (cognitive_id)、不整合なし。観察 1 で alpha_id × cid_id ジョインに問題なし。

#### 1.1.5 時間軸同期の Code A 方針

- per (alpha_id, window) の member 構成 = alpha_lifecycle_log を per-step で累積 → v10.6 step_at_window_end で window 化
- v10.5 alpha_membership_log の step=25000 は run 終了時の確認用に併用 (最終整合性チェック)
- alpha の ghost 化 / member_ghosted イベントを per-window で記録、観察 1 で構成変化を反映

### 1.2 IID 表現 (GPT 修正必須 A)

設計書 §1.5 通り、IID は新規データ構造でなく既存構造の参照表現:
- α / β Integration (alpha_membership_log, beta_distribution_log, alpha_lifecycle_log)
- member_cids
- attention_candidate_id (attention_emit_log)
- predecessor_attention_ref (attention_emit_log)
- cid_state_ledger (v1101a 段階 2 簡易版)

Code A は本主題で **IID という新規 entity を作らない**。スクリプト内・出力ファイル内で "IID" 名称を使う際は上記既存構造を指す参照表現として使用、新規ファイル名・新規列名としては使わない (例: `iid_state_ledger.parquet` のようなファイルは作らない)。

### 1.3 観察 1 の Jaccard 厳密化 (GPT 修正必須 B)

設計書 §2.1.4 通り、3 指標別算出:
- **k=1 一致率**: 各 CID 単独 rank_1_atom と Integration α top_atom の完全一致割合 (Jaccard と呼ばない)
- **top-3 Jaccard 類似度**: CID top-3 atom 集合 ∩ α top-3 atom 集合 / 和集合
- **top-5 Jaccard 類似度**: 同 top-5

Code A 出力列名:
- `match_rate_k1` (k=1 一致率、別名 not Jaccard)
- `jaccard_top3`
- `jaccard_top5`

### 1.4 観察 2 の判定語制限 (GPT 追加 4)

設計書 §2.2.5 通り、Code A は以下のみ記録:
- predecessor chain 上の cid 推移
- atom 推移
- category 推移 (BOD → COG → EXS 等)
- cid_atom_sim_matrix 上の類似度推移
- shuffle baseline との比較値

Step H 観察事実報告で「連想」「連想を辿る」「連想処理である」等の表現を使わない。整理語は Web Claude Phase Result 領域。

### 1.5 観察 3 の重複回避 (GPT 追加 5)

設計書 §2.3.4 通り、既知事実 (認知優位安定 / 意識優位移動 / qc_regime で像が変わる) は再観察しない。本観察の新規性は限定的に:
- trajectory 安定 ⇔ response_atom_distribution 収束 の対応
- trajectory 拡散 ⇔ response_atom_distribution 拡散 の対応

trajectory 自体の動きの再観察でなく、**v1103 response_atom_distribution との対応関係に絞る**。

#### 1.5.1 観察 B の Jaccard proxy の所在確認

設計書 §2.3.3 で「観察 B Jaccard proxy (隣接 window 中心 atom 一致) | unified/v1101a 段階 2 observation_b」と指定されているが、`observation_c_predictability.parquet` 等の段階 2 出力は確認済だが `observation_b_*` の所在を再確認要 (§5.2 確認要請)。

### 1.6 観察 4 の selector 化禁止 (GPT 修正必須 C)

設計書 §2.4.5 通り、Code A 実装上の制約:
- B primary 化した場合の仮想順位・仮想候補集合を **post-process で算出するのみ**
- ESDE 内部の attention_emit / salience / trajectory / cid_state_ledger には **一切書き戻さない**
- 新しい重要性 emit を ESDE 内部に追加する処理を含めない
- selector として動作する処理を追加しない

書込み先: `unified/v1104/outputs/main/observation_4_*.parquet` のみ。`unified/v1101a/`、`developmental/v105/` 等への書き戻しは禁止。

---

## 2. 入力データ規模確認

| データ | 規模 (seed 0、24 seeds total) | 用途 |
|---|---|---|
| attention_emit_seed{N}.parquet | 48,714 rows × 24 seeds ≈ 1.73M | 観察 1/2/3/4 |
| alpha_lifecycle_log_seed{N}.csv | 1,063 events × 24 seeds ≈ 25,500 | 観察 1 (per-window member 復元) |
| alpha_membership_log_seed{N}.csv | 27 cid × 24 seeds ≈ 650 | 観察 1 (最終整合性チェック) |
| beta_distribution_log_seed{N}.csv | 50 events × 24 seeds ≈ 1,200 | 観察 1 (β 用) |
| v10.6 trajectory (event/pulse/step10/window × 24 seeds) | 各 ~1,000 rows / seed | 観察 1/3 |
| cid_atom_sim_matrix_seed{N}.parquet | 228 cid × 326 atom × 24 seeds | 観察 2/3 |
| attention_propagation_seed{N}.parquet | 48,714 rows × 24 seeds | 観察 2 |
| attention_causality_seed{N}.parquet | 48,714 rows × 24 seeds | 観察 2 |
| cid_state_ledger_seed{N}.parquet | 7,900 rows × 24 seeds ≈ 175,200 | 観察 3 |
| salience_event_log_seed{N}.csv | 3,114 rows × 24 seeds ≈ 75,000 | 観察 4 |
| outstanding_cells.parquet (v1102) | 81 cells | 観察 4 |
| primary_table.parquet (v1102) | 81 cells × 27 cols | 観察 1/3/4 |
| response_atom_distribution.parquet (v1103) | 5,670 rows | 観察 3 |
| density_summary.parquet (v1103) | 486 rows | 観察 3 |
| Step G stratified_observation.parquet (v1101a) | 19 rows | 観察 1/4 |

全データ読み込み可能、新規 main run 不要。

---

## 3. 観察 1-4 の実装計画 (概略)

### 3.1 観察 1 (項目 1.1): CID-Integration の像の差分

- per (seed, window, alpha_id) で alpha_lifecycle_log → 該当時点 member_cids 復元
- per cid の rank_1_atom を v10.6 trajectory から取得 (window 単位)
- per (alpha_id, window) で:
  - alpha top_atom = member_cids の rank_1_atom modal value (most frequent)
  - CID 単独 top_atom = 各 member cid の rank_1_atom
  - match_rate_k1 / jaccard_top3 / jaccard_top5 を計算
- n_members × qc_gini で層化 (Step G 継承)
- 出力: `observation_1_cid_integration.parquet`

### 3.2 観察 2 (項目 1.6): predecessor 連鎖

- attention_emit から意識優位 window の predecessor_attention_ref 連鎖を per (seed, scope) で復元
- 連鎖の経路: cid_a → cid_b → cid_c → ...
- 経路上の atom 推移、category 推移、cid_atom_sim_matrix 類似度推移
- shuffle baseline (per-seed × 100 回 permutation) との比較
- 出力: `observation_2_predecessor_chain.parquet`

### 3.3 観察 3 (項目 1.7): attention trajectory ↔ response_atom_distribution 対応

- per (cid_id, window, qc_regime) で attention trajectory 安定度・拡散度算出
- v1103 response_atom_distribution の収束/拡散指標 (max_prob / entropy) と対応
- 時間粒度別 (immediate/short/medium) 比較 (Taka 直感メモ接続可能性)
- 出力: `observation_3_trajectory_response.parquet`

### 3.4 観察 4 (項目 2.6): 際立ち掬い取り B 現状確認

- ESDE 自身の emit (salience candidate_mass / attention_emit change_metric_value/rank/qc_ratio) を A primary 結果 (outstanding_cells) と重ね合わせ
- 57/81 cells の重なり方を定量化
- B primary 化仮想評価 (post-process のみ、ESDE 内部書き戻さない)
- 出力: `observation_4_b_overlap.parquet`

---

## 4. 既知留保の本主題への適用 (Step F で確定)

設計書 §5.1 継承留保を本主題で扱う際の方針:

| id | 本主題での扱い方針 |
|---|---|
| #33 系列 (集計単位で像が変わる) | 観察 1 の核心。CID-Integration の像の差を「集計単位で像が変わる」と整合的に観察 |
| #L4 (alpha records 92.5%) | 観察 1/4 で scope 内正規化 (Step G 継承) |
| #L8 (CID scope self-reference) | 観察 3 で CID scope の trajectory 観察時、self-reference を明示してから結果記録 |
| #L10 (ESDE 3 scope shuffle 効果薄) | 観察 1/3 で ESDE 3 scope の集約限界を継承 |
| #L11 (alpha n=1 偏り) | 観察 1/4 で n_members 別層化 |
| #L14 (CID 構成ノード数で atom 階層反転) | 観察 1 の参照点 |
| #L17 (raw vs norm 密度 Δ0.208) | 観察 1 の駆動要因の一部。本観察は #L17 を支える内部構造を探す |
| #L18 / #L19 | 本主題範囲外 (Language 側関連) |
| 48 次元人為性留保 | 観察 1 で CID の atom 定義が人為的であることは前提として明示、ただし観察対象は Genesis 側 cid 構造で Language 側人為性は直接扱わない |

---

## 5. Web Claude / Taka 確認要請

### 5.1 確認要請 1 — window 範囲統一

v1101a attention_emit_seed{N}.parquet は window 19-69 (51 windows)、v10.6 window_trajectory は window 20-69 (50 windows)。差は window=19 (1 window 分、smoke 期間または初期化期間と推測)。

観察 1/3 で per-window 集計を行う際の window 範囲:
- (i) v1101a 範囲 (19-69) を採用、window=19 を含める
- (ii) v10.6 範囲 (20-69) に揃え、window=19 を除外
- (iii) 両方算出して比較

Code A 仮所見: **(ii) v10.6 範囲 (20-69) に揃える** — v10.6 trajectory が観察 1 の主要入力、window=19 は v10.6 にないため整合性確保のため除外。window=19 の特性 (smoke or 初期化) は独立観察として留保。

### 5.2 確認要請 2 — 観察 B Jaccard proxy の所在

設計書 §2.3.3 で「観察 B Jaccard proxy | unified/v1101a 段階 2 observation_b」と指定されているが、`unified/v1101a/outputs/main/` 配下で `observation_b_*` ファイルが見当たらない。`observation_a_candidate_count.parquet` / `observation_c_predictability.parquet` は確認済 (v1101a 段階 2 Step C 出力)。

3 選択肢:
- (i) `observation_b_jaccard_proxy.parquet` 等の別名で存在 → Web Claude が所在確認
- (ii) v1101a 段階 2 Step C の中間出力で commit されていない → Code A が attention_propagation_seed{N}.parquet から再計算
- (iii) 設計書の記述は概念参照 (実ファイルでなく観察事実) で、本観察 3 では再計算前提

Code A 仮所見: **(iii) 概念参照、Code A が必要に応じて attention_propagation から再計算** — 設計書 §2.3.4「既知事実として前提とする」記述から、Jaccard proxy 数値は再計算不要 (既知の傾向のみ参照)、本観察 3 は trajectory↔response_atom_distribution 対応に集中。

---

## 6. 進行 — Step A 完了後の流れ

| Step | 内容 | 担当 | 想定 | 待機 |
|---|---|---|---|---|
| Step A (本書) | 認識確認 | Code A | 完了 | Web Claude/Taka §5 確認要請 2 件回答待ち |
| Step B | 観察 1 実装 (CID-Integration、top-k Jaccard、layer 化) | Code A | 1 日 | §5.1 確定後 |
| Step C | 観察 2 実装 (predecessor 連鎖、判定語制限) | Code A | 1 日 | Step B 後 |
| Step D | 観察 3 実装 (trajectory ↔ response 対応) | Code A | 1 日 | §5.2 確定後 |
| Step E | 観察 4 実装 (B 重なり、selector 化禁止) | Code A | 半日 | Step D 後 |
| Step F | グラフ HTML 4 観察 dashboard | Code A | 半日 | Step E 後 |
| Step G | bit-identity 3 層検証 | Code A | 短時間 | Step F 後 |
| Step H | 観察事実報告 (judgment なし、判定語制限) | Code A | 半日 | Step G 後 |
| Step I | Phase Result | Web Claude | — | Step H 後 |

想定合計 **4-5 日** (設計書 §6.1 想定 6-7 日内、観察 4 が selector 化禁止で軽量化)。

---

## 7. 規律遵守自己点検 (本 Step A)

| # | 格言 | 遵守 |
|---|---|---|
| 2 | 物理層 frozen | 本書は read-only 調査、書込み unified/v1104/ 配下のみ |
| 5 | 観察軸を増やすことを駆動要因にしない | 既存出力流用のみ、新規軸なし |
| 8 | 過去観察軸の照会義務 | §5.2 で v1101a 段階 2 observation_b の所在確認要請 |
| 11 | 概念単位を雑に扱わない | §1.1.4 cid_id 整合性 / §1.2 IID 既存構造参照 / §1.3 Jaccard k=1 と k=3/5 別指標 |
| 12 | Aruism 判定回避 | 本書は事実記録、(i)(ii)(iii) の判定は Web Claude / Taka |
| 13 | AI を信じない原則は Taka 個人 | §5 確認要請を明示、Code A 仮所見と最終判断を区別 |
| 14 | Taka 直感優先 | 設計書 §0 Taka 整理原文 + 直感メモ (時間条件) 範囲外を §1.5 で継承 |

---

## 8. 一文サマリ (再掲)

v1104 設計書 §6.1.1 認識確認 6 項目の Code A 実環境照合結果として、時間軸同期は v10.5 alpha_membership が step=25000 のみで per-window 時系列なしだが alpha_lifecycle_log (424 events × 267 step in seed 0、event_type=birth/member_ghosted/active_to_recorded + member_cids '|' 区切り) で per-step 構成変化を復元可能 + v10.6 step_at_window_end で per-window 化可能 + cid_id 整合性 (v10.5 alpha_member 27 cid ⊂ v1101a CID scope 135 cid、overlap 27 / 不整合 0)、IID 表現は §1.5 通り新規構造なし既存構造参照、Jaccard 厳密化 (k=1 一致率 vs top-k Jaccard k=3/5) と判定語制限 (「連想」と判定しない) と重複回避 (trajectory↔response_atom_distribution 対応に絞る) と selector 化禁止 (post-process 仮想評価のみ、ESDE 内部書き戻さない) の規律を全 §2.x で堅持、入力データ規模 (attention_emit 1.73M / alpha_lifecycle 25,500 / cid_state_ledger 175,200 等) すべて読み込み可能、新規 main run 不要、Web Claude/Taka 確認要請 2 件 (§5.1 window 範囲統一は Code A 仮所見 (ii) v10.6 範囲 20-69、§5.2 観察 B Jaccard proxy 所在は Code A 仮所見 (iii) 概念参照で再計算不要) を整理、想定実装 4-5 日 (Step B-H、設計書想定 6-7 日内、観察 4 軽量化)。

---

*以上、v1104 Step A 認識確認 (Code A、2026-05-23)。確認要請 2 件への Web Claude / Taka 回答後、Step B (観察 1 実装) に着手可。*
