# v11.0.5a (v1105a) Step A 認識確認 — Code A

*作成*: 2026-05-24、Code A
*親*: `v1105a_phase_design.md` v2 (Web Claude 設計書、2 AI 監査クリア済)
*対象*: Web Claude (相談役) + Taka (主題判断者)
*位置づけ*: v1105a 進行表 Step A (Code A 認識確認 + 実環境照合 + Web Claude/Taka 領域への確認要請 4 件)。判定は行わず、観察手順の実装可能性と確認要請に限定。

---

## 0. 一文サマリ

v1105a 設計書 v2 (問いの形 B 初切替、2 AI 監査クリア = rank-based 絞り式 / 構造ラベル / 共通比較指標 / B emit read-only / v1106 接続条件 3 点) を Code A 受領、§5 確認要請 8 項目に Code A 認識提示 + 実環境照合 (v112 atom_introduction_events_v112 全 24 seeds = **10,500 events で設計書 §2.2 値と完全一致** / ただし n_core_bin=bin_5_plus のみ (n_core_member=5/7/8) で **設計書「CID_n=2/3/4/5/6+ 5 bin 並列保持」と不整合** / v108_standard series 60,000 events に 3 bin あり bin_2 52,864 + bin_3_4 3,717 + bin_5_plus 3,419 で 5 bin 並列保持を満たす / unique atom_id v112 25 種 + v108 25 種 (共通 atom セット) / v1103 response_atom_distribution.parquet の start_atom は 7 種のみ (EMO.manifest / EXS.being / EXS.presence / FND.timeless / SOC.nation / SPC.nowhere / WLD.culture) / 入力 atom_id 25 種のうち start_atom と一致 4 種のみ = **案 B 静的取り出し方式だと カバレッジ 16%**)、Web Claude/Taka 領域への確認要請 4 件提示: 確認要請 8 (入力データ選択: v112 10,500 / v108_standard 60,000 / 両方 70,500 / 設計書通り v112 のみで bin_5_plus のみ実体保持の 3 案、Code A 案 v108_standard 60,000 採用で 5 bin 並列保持を実体で満たす)、確認要請 9 (v1103 段 4-d 機構の継承方法 = 案 A 動的再計算 / 案 B 静的取り出し 16% カバレッジ、Code A 案 B 採用 + カバレッジ欠損は candidate_empty ラベルとして記録)、確認要請 10 (rank の計算粒度 = rank_source_i / rank_trajectory_i / rank_density_i は per-atom か per-receiver_bin か、Code A 案: rank_source_i は per-atom (Step 2 出力)、rank_trajectory_i / rank_density_i は per-receiver_bin の値を該当 receiver_bin 内 atom 全てに均等に付与)、確認要請 11 (構造ラベル操作的閾値: candidate_empty = n_after==0 / distribution_degenerate = max_prob ≥ 0.999 or prob_ge_0.999_count > 0 / distribution_valid = max_prob < 0.999 かつ entropy > 0 / pipeline_complete = distribution_valid 達成、Code A 案 max_prob 閾値 0.999 採用 v1103 §7.5 と同型)、§5 確認要請 1-8 への回答 (1: v112 10,500 events 確認、ただし bin 構成は §8 で確認要請 / 2: Python post-process 新規スクリプト 4 本 Step B-E 別 / 3: parquet event_id × source_layer × candidate_atom_set / 4: §2.4 rank-based 仕様通り実装、独自発明なし、tied rank は average / 5: 確認要請 9 / 6: parquet event_id × series_id × atom × prob / 7: 構造ラベル確認要請 11 / 8: v1106 接続条件 §2.7 通り)、Step B-H 想定実行時間 (B 環境準備 < 1s / C 試行 Step 1+2 数分 / D 試行 Step 3 7 系列並列で数分 / E 試行 Step 4 数分 / F 観察項目集計 < 1s / G bit-identity 数分 / H 観察事実報告)、規律遵守宣言 (絶対格言 #2/#6/#9/#11/#12 + 試行 ≠ selector 化 / 試行 ≠ 会話成立判定 / 試行 ≠ ハンドチューニング + 7 系列・6 値統合禁止 + 書込み unified/v1105a/ 配下) を完了、確認要請 4 件回答受領後に Step B から実装着手予定、書込み unified/v1105a/ 配下のみ。

---

## 1. §5 Code A 確認要請 1-8 への認識

### 1.1 §5-1: 入力 atom_introduction_event の所在 + 件数

**実環境照合結果**:

| ファイル系列 | 全 24 seeds 合計 | n_core_bin 構成 | unique atom_id |
|---|---:|---|---:|
| `developmental/v112/outputs/main/atom_introduction_events_v112_seed{N}.parquet` | **10,500 events** | bin_5_plus のみ (n_core_member=5/7/8) | 25 |
| `developmental/v112/outputs/main/atom_introduction_events_v108_standard_seed{N}.parquet` | **60,000 events** | bin_2 52,864 + bin_3_4 3,717 + bin_5_plus 3,419 | 25 |

**設計書 §2.2 と実体の対応**:
- 設計書「v1102 と同じ 10,500 events」 → v112 series が完全一致 (10,500)、v1102 outputs には atom_introduction events は保存されていない (集約済 primary_table のみ)、v1102 計算に使われた入力が v112 と推察
- 設計書「CID_n=2/3/4/5/6+ の 5 bin で並列保持」 → v112 series では **不整合** (bin_5_plus のみ)、v108_standard なら満たす

確認要請 8 (§3) を参照。

### 1.2 §5-2: 試行スクリプト言語 + 実装方法

**Code A 実装方針**:
- Python 3、numpy/pandas/scipy ベースの post-process スクリプト
- 新規スクリプト 4 本 (Step B-E 別):
  - `v1105a_step_b_env_check.py` (環境準備、簡易検証)
  - `v1105a_step_c_trial_step1_2.py` (Step 1+2 入力投入 + 段 4-b 連想)
  - `v1105a_step_d_trial_step3.py` (Step 3 段 4-c 絞り、7 系列並列)
  - `v1105a_step_e_trial_step4.py` (Step 4 段 4-d 確率分布出力)
  - + `v1105a_step_f_aggregate.py` (Step F 観察項目集計)
- 新規 main run なし、全 post-process、既存 outputs を read-only で参照

### 1.3 §5-3: 段 4-b 連想出力フォーマット

**Code A 実装方針**:
- parquet 出力: `event_id × source_layer × candidate_atom × layer_metadata`
- 4 source レイヤー: `genesis_alpha / genesis_beta / language_alpha / language_beta`
- 各 candidate_atom に layer_metadata として lift_C (Genesis) または couple_hit_rate (Language) を保持
- 統合しない (絶対格言 #11、別レイヤー保持)

### 1.4 §5-4: 段 4-c 絞り式 (rank-based 仕様通り)

**Code A 実装方針** (設計書 §2.4 通り、独自発明禁止):

```python
# 各 atom i について:
score_i = w_source_i * w_trajectory_i * w_density_i
where:
  w_source_i      = 1 / log(rank_source_i + 2)
  w_trajectory_i  = 1 / log(rank_trajectory_i + 2)
  w_density_i     = 1 / log(rank_density_i + 2)

# 各系列内で正規化:
  p_i = score_i / sum(score_j for all candidates)
```

**実装詳細**:
- `log` の底: **自然対数 (e)** を採用 (numpy.log)、底は理論的に任意 (rank の単調性のみ保つ)
- **tied rank**: `pandas.rank(method='average')` を採用 (同順位は平均順位)
- 7 系列で並列実行 (設計書 §2.4 通り、density 種類で分岐)

rank 計算粒度は確認要請 10 (§3) を参照。

### 1.5 §5-5: v1103 段 4-d 機構の継承方法

**実体照合**:
- v1103 `response_atom_distribution.parquet` (5,670 rows = 27 receiver_bin × 3 metric × 1 start_atom × 2 sim_basis × 3 k × 約 14 candidates)
- start_atom は 7 種のみ (EMO.manifest / EXS.being / EXS.presence / FND.timeless / SOC.nation / SPC.nowhere / WLD.culture)
- 入力 atom_id 25 種のうち start_atom と一致 4 種のみ (EXS.being / FND.timeless / SOC.nation / WLD.culture)

確認要請 9 (§3) を参照。

### 1.6 §5-6: 7 系列出力フォーマット

**Code A 実装方針**:
- parquet: `event_id × series_id × candidate_atom × probability × metadata`
- series_id: 1-7 (設計書 §2.4 表通り)
- metadata: source_layer / B_high_flag (read-only) / rank_source/trajectory/density

### 1.7 §5-7: 構造ラベル操作的判定条件

**Code A 案** (確認要請 11、§3 参照):

| ラベル | 操作的条件 |
|---|---|
| `candidate_empty` | n_candidates_after == 0 |
| `distribution_degenerate` | max_prob ≥ 0.999 OR prob_ge_0.999_count > 0 |
| `distribution_valid` | max_prob < 0.999 AND entropy > 0 (n_after >= 2 implicit) |
| `pipeline_complete` | distribution_valid を達成 (candidate_empty / degenerate でなく完了) |

max_prob 閾値 0.999 採用は v1103 §7.5 (Aruism 対称性チェック) と同型。

### 1.8 §5-8: v1106 着手判断観察項目の優先順位

**Code A 提示** (Web Claude/Taka 領域への素材):

| 優先順位 | 観察項目 | 観察源 |
|---|---|---|
| 1 | `pipeline_complete` event 数 (絶対値 + 全 event に対する比率) | §2.6 構造ラベル集計 |
| 2 | `distribution_valid` 系列数 (7 系列で何系列が valid か) | §2.6 共通比較指標 |
| 3 | `reduction_ratio` 系列別分布 (n_before / n_after の構造的記述) | §2.6 共通比較指標 |
| 4 | `layer_jaccard` 系列間重なり (7 系列で類似か独立か) | §2.6 |
| 5 | `b_high_in_top5_ratio` (B emit read-only 観察) | §2.4 |

設計書 §2.7 の 3 条件は優先順位 1-3 と対応。

---

## 2. 試行 Step B-H の実装可能性 + 想定実行時間

| Step | 内容 | 想定実行時間 | 実装可能性 |
|---|---|---|---|
| B | 環境準備 (sample 検証) | < 1s | ✓ |
| C | 試行 Step 1+2 (入力投入 + 段 4-b 連想 4 レイヤー) | 数十秒〜数分 (60,000 events × 4 レイヤー、確認要請 8 結果次第) | ✓ |
| D | 試行 Step 3 (rank-based 絞り 7 系列並列) | 数分 (events × 7 系列 × per-atom rank 計算) | ✓ (確認要請 9, 10 後) |
| E | 試行 Step 4 (確率分布出力 7 系列) | < 1s (Step D で生成済の確率を再正規化のみ) | ✓ |
| F | 観察項目集計 | < 1s | ✓ |
| G | bit-identity 3 層検証 | 数分 (Step C-E 再実行) | ✓ |
| H | 観察事実報告 | — | ✓ |

合計想定 < 10 分 + bit-identity 数分。

---

## 3. 確認要請 4 件 (Web Claude/Taka 領域)

### 3.1 確認要請 8 — 入力データの選択 (設計書 §2.2 vs 実体)

**論点**:
- 設計書「v1102 と同じ 10,500 events」 → v112 series で完全一致
- 設計書「CID_n=2/3/4/5/6+ の 5 bin で並列保持」 → v112 は bin_5_plus のみで不整合
- v108_standard 60,000 events なら 3 bin (bin_2 / bin_3_4 / bin_5_plus) で 5 bin 並列保持に近い (ただし bin_2 = n=2 / bin_3_4 = n=3/4 集約 / bin_5_plus = n=5+ で粒度不完全)

**Code A 案 3 つ**:

| 案 | 入力 | 利点 | 欠点 |
|---|---|---|---|
| **案 A (Code A 推奨)** | v108_standard 60,000 events | 3 bin (bin_2 / bin_3_4 / bin_5_plus) が揃う、CID_n=2 (#L35 観察対象) を含む | event 数増 (60,000)、bin_3_4 と bin_5_plus を細分化できない |
| 案 B | v112 10,500 events のまま | 設計書通り、event 数小 | bin_5_plus のみ、CID_n=2 観察できない (#L35 試行内検証不能) |
| 案 C | v112 + v108_standard 70,500 events | 全 bin カバー、最大カバレッジ | event 数最大、condition_id (v112 / v108_standard) で出自混在 |

**Code A 推奨**: **案 A** (v108_standard 60,000)。理由: §0.8 で 7 留保のうち #L35 (CID_n=2 の特殊性) を試行内で観察することが明示され、CID_n=2 観察には bin_2 を含む入力が必須。v108_standard は bin_2 が 88% (52,864/60,000) を占め、#L35 試行内動的観察の主入力となる。

### 3.2 確認要請 9 — v1103 段 4-d 機構の継承方法

**論点**:
- 設計書「v1103 で機構成立した段 4-d の確率分布出力機構を継承」 → 2 案あり
- v1103 response_atom_distribution は start_atom 7 種のみ計算済
- 入力 atom_id 25 種中 4 種 (EXS.being / FND.timeless / SOC.nation / WLD.culture) のみが start_atom と一致

**Code A 案 2 つ**:

| 案 | 内容 | 利点 | 欠点 |
|---|---|---|---|
| **案 A** | v1103 のコード (cosine_sim 計算 + 確率化) を呼び出して新規 atom に対して動的計算 | 全 atom_id 25 種をカバー (カバレッジ 100%) | v1103 のコード再実装または流用、新規計算コスト、再現性確保が複雑 |
| **案 B (Code A 推奨)** | 既存 response_atom_distribution から start_atom + receiver_bin で取り出し (静的流用) | 計算なし、再現性高、v1103 を物理層 frozen 維持 | 入力 atom 21/25 (84%) が start_atom 範囲外 = candidate_empty ラベル多発 |

**Code A 推奨**: **案 B** (静的取り出し)。理由: 物理層 frozen 維持 (絶対格言 #2)、v1103 機構の再実装回避。カバレッジ欠損 21/25 atom は `candidate_empty` ラベルとして構造事実記録 (構造ラベル化 §1.1 / GPT Auditor 2026-05-24)。これは v1103 機構の構造的限界を試行内で観察する形となり、設計書 §1.3「入力-出力対応」の意義に合致する。

「カバレッジ 16% で試行成立か」の判定は Web Claude/Taka 領域。Code A は構造事実として記録のみ。

### 3.3 確認要請 10 — rank の計算粒度

**論点**: 設計書 §2.4 rank_source_i / rank_trajectory_i / rank_density_i は各 atom に対して計算するが、source / trajectory / density の元データの粒度が異なる:

| rank 種類 | 元データ粒度 | per-atom 計算可否 |
|---|---|---|
| rank_source_i | 4 source レイヤーの candidate atom set | per-atom 直接計算可 (atom が含まれるレイヤー内での lift_C / couple_hit_rate rank) |
| rank_trajectory_i | v1105 observation_2_terrain_4c の per (receiver_bin × predictor) で pearson_r | per-receiver_bin で 1 値、atom 個別の trajectory r を持たない |
| rank_density_i | v1103 density_summary の per (receiver_bin × metric × sim_basis × k) で density 6 種 | per-receiver_bin で 1 値、atom 個別の density を持たない |

**Code A 案**:
- `rank_source_i`: per-atom で計算 (atom の source レイヤー lift_C / couple_hit_rate を rank、複数レイヤー含む場合は min rank)
- `rank_trajectory_i`: per-receiver_bin の trajectory r を該当 receiver_bin 内の全 atom に均等付与 → atom rank は receiver_bin 単位
- `rank_density_i`: 同上、per-receiver_bin の density r を全 atom に均等付与

結果として、`rank_trajectory_i` と `rank_density_i` は同一 receiver_bin 内 atom で同値、rank の差別化は `rank_source_i` (per-atom) のみ。これにより最終 score の差別化は主に source rank に依存。

**Web Claude/Taka 判断**: Code A 案採用 / per-atom 計算を要求 (atom 個別の trajectory / density を持つ計算源を v1102/v1103 にあたる、必要なら追加実装)。

### 3.4 確認要請 11 — 構造ラベル操作的閾値

**論点**: 設計書 §1.1 構造ラベル (pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid) の操作的判定条件を Code A が確定する必要。

**Code A 案** (§1.7 と同じ、再掲):

| ラベル | 操作的条件 |
|---|---|
| `candidate_empty` | n_candidates_after == 0 |
| `distribution_degenerate` | max_prob ≥ 0.999 OR prob_ge_0.999_count > 0 |
| `distribution_valid` | max_prob < 0.999 AND entropy > 0 (n_after >= 2 implicit) |
| `pipeline_complete` | distribution_valid を達成 (candidate_empty / degenerate でない) |

**閾値 0.999** は v1103 §7.5 (Aruism 対称性チェック) と同型 (prob_ge_0.999_count 列を流用)。Web Claude 承認 or 別閾値要求。

---

## 4. 規律遵守宣言 (Step A 範囲)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.x / v1101a / v1102 / v1103 / v1104 / v1104a / v1105 read-only、書込み unified/v1105a/ のみ) |
| 絶対格言 #6 (出口の固定) | ✓ (構造ラベル化で「会話できる」を判定しない) |
| 絶対格言 #9 (神の手回避) | ✓ (絞り式 rank-based 固定、独自発明なし、ハンドチューニング禁止) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (7 系列・6 値統合なし、4 source レイヤー別保持) |
| 絶対格言 #12 (judgment 回避) | ✓ (success/failure 表現未使用、構造事実のみ記録) |
| 試行 ≠ selector 化 | ✓ (役割表に従う動作のみ、ESDE 「自由選択」なし) |
| 試行 ≠ 会話成立判定 | ✓ (構造ラベル化、意味判定なし) |
| 試行 ≠ ハンドチューニング | ✓ (絞り式 §2.4 通り、閾値調整なし) |
| ハンドチューニング禁止 (絶対格言 #9) | ✓ (絞り式 rank-based 固定、独自発明禁止) |
| 試行方法を有利化しない | ✓ (結果が出ない場合の方法変更なし、留保として記録) |
| B emit 試行に組み込まない (最小 3 役割) | ✓ (read-only 観察列、絞り score 不使用) |
| 段 5a/5b 範囲外 | ✓ (本主題は段 4-b/4-c のみ) |
| 新規 main run 禁止 | ✓ (post-process のみ) |
| 新規観察軸の追加禁止 | ✓ (v1105 役割表構造継承、追加軸 0) |
| 7 系列・6 値統合禁止 | ✓ (別レイヤー保持、共通比較指標 §2.6 で並列) |
| 書込みパス unified/v1105a/ 配下 | ✓ (Step B-H すべて unified/v1105a/ 配下) |
| smoke 含めず | ✓ (post-process のみ) |

---

## 5. Step A 完了後の進行 (確認要請 4 件への Web Claude/Taka 回答受領後)

1. **確認要請 8 回答**: 入力データ確定 (Code A 推奨案 A = v108_standard 60,000)
2. **確認要請 9 回答**: 段 4-d 機構継承方法確定 (Code A 推奨案 B = 静的取り出し)
3. **確認要請 10 回答**: rank 計算粒度確定 (Code A 推奨案 = source は per-atom、trajectory/density は receiver_bin 単位)
4. **確認要請 11 回答**: 構造ラベル閾値確定 (Code A 推奨 = max_prob 0.999)

回答受領後 Step B から順次実装:
- Step B (環境準備)
- Step C (Step 1+2: 入力投入 + 4 source レイヤー連想)
- Step D (Step 3: rank-based 絞り 7 系列)
- Step E (Step 4: 確率分布出力)
- Step F (観察項目集計)
- Step G (bit-identity 3 層検証)
- Step H (観察事実報告、judgment 回避、Web Claude Phase Result + v1106/v1105b 着手判断領域)

---

## 6. 一文サマリ (再掲)

v1105a 設計書 v2 (問いの形 B 初切替、2 AI 監査クリア) を Code A 受領、§5 確認要請 8 項目に Code A 認識提示 + 実環境照合 (v112 series 全 24 seeds = 10,500 events で設計書 §2.2 値完全一致、ただし n_core_bin=bin_5_plus のみ で 5 bin 並列保持と不整合 / v108_standard series 60,000 events に 3 bin で 5 bin 並列保持満たす / v1103 start_atom 7 種のみ、入力 atom_id 25 種中 4 種カバレッジ 16%) し、Web Claude/Taka 領域への確認要請 4 件提示 (確認要請 8 = 入力データ v108_standard 60,000 案 A 推奨、確認要請 9 = 段 4-d 機構静的取り出し案 B 推奨カバレッジ欠損は candidate_empty ラベル記録、確認要請 10 = rank 計算粒度 source per-atom + trajectory/density per-receiver_bin、確認要請 11 = 構造ラベル閾値 max_prob 0.999 v1103 §7.5 同型)、§5-1〜8 への回答 (1: v112 件数確認 / 2: Python post-process 4 スクリプト / 3: parquet event_id × source_layer × candidate_atom / 4: rank-based 仕様通り自然対数 tied=average / 5: 確認要請 9 / 6: parquet event_id × series_id × atom × prob / 7: 確認要請 11 / 8: v1106 接続条件 §2.7 + 優先順位 5 項目)、Step B-H 想定実行時間 (B < 1s / C-G 数分〜10 分) + 規律遵守宣言 (絶対格言 #2/#6/#9/#11/#12 + 試行 ≠ selector 化/会話成立判定/ハンドチューニング + 7 系列・6 値統合禁止 + B emit 補助 + 書込み unified/v1105a/ 配下) を完了、確認要請 4 件回答受領後に Step B から実装着手予定、書込み unified/v1105a/ 配下のみ。
