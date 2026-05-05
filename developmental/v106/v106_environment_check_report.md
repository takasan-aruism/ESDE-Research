# v10.6 実装前 環境調査報告書

*作成*: 2026-05-05、Code A (実環境調査担当)
*対象資料*: `v106_phase_design.md` (Web Claude 保持、本リポジトリ未配置) / 依頼書 `v106 実装前調査依頼書`
*参照*: ESDE_Glossary v5.7.0、ESDE_Module_Reference v5.7.0、ESDE_Language_Legacy_Digest

---

## 0. エグゼクティブサマリ

依頼書の §2-§4 は概ね **「資料記述と実態の乖離が散見される」**。実装着手前に下記を共有して指示書を確定すべき。

1. **Genesis 系のディレクトリ構造は文書記載と異なる** — 依頼書想定の `per_subject/`/`per_window/`/`integration/` ではなく、`subjects/`/`aggregates/`/`integration/`+`audit/`+`balance/`+`network/`+他 14 サブディレクトリの **17 ディレクトリ構成**。
2. **CSV 列名は `v11_m_c_*` などのバージョン接頭辞付きで揃っている** — 主要数値 (M_c、Q ledger、C trajectory、disposition、履歴、Integration) はすべて取得可能。
3. **familiarity マップは `network/fam_edges_seed*.csv` (from→to エッジリスト) として独立保存** — per_subject にあるのはスカラー集計のみ。属性/閾値計算には fam_edges 側を読む必要あり。
4. **既存 cid 集計スクリプト (5 パターン分類、ハブ抽出、寿命計算等) は v10.5 までに作られていない** — v10.6 で post-process として新規実装が必要。
5. **Atom 326 の 48 スロット連続値は `lexicon/data/mapper_output/*_a1.jsonl` に "per-word" の raw_scores/normalized_scores として保存** — atom レベルへの集計は未済。`atoms/a1_batch/` と `lexicon/data/lexicon_entries/` は **ファイルとして同一** (WordNet 拡張 word pool であって 48 スロット値は含まれない)。
6. **mapper_output には error 行が混入** — EMO.love は 58 word のうち 56 word のみ raw_scores 取得済 (2 word は LLM error)。集計時にフィルタ必須。
7. **FND_spaceless は資料記述通り未完** — a1_batch (atom 定義) には存在、mapper_output (A1 観測) には不存在。よって **観測済みは 325 atom、326 atom 全体プロファイルは欠落 1 atom**。
8. **Phase 9 のコードは現リポジトリに存在しない** — Module Reference v5.7.0 が想定する `language/runner/`、`language/integration/` (Phase 9-0)、`language/statistics/`、`language/discovery/`、`language/cell/` (Phase 10) はすべて欠如。`legacy/` 配下にも無し (legacy は古い simulator + PDF のみ)。
9. **環境は問題なし** — Python 3.13.5、numpy/pandas/scipy/sklearn 揃済、データ総量 1.9 GB で軽量。

---

## 1. ディレクトリ構造 (Genesis 系)

### 1.1 想定 vs 実態

| 依頼書想定パス | 実態 | 差異 |
|---|---|---|
| `developmental/v105/diag_v105_main_v2/per_subject/` | `subjects/` | 名称異 |
| `developmental/v105/diag_v105_main_v2/per_window/` | `aggregates/per_window_seed*.csv` (json 同居) | パス異 |
| `developmental/v105/diag_v105_main_v2/integration/` | 同名で存在 | 一致 |
| `developmental/v105/diag_v105_main_v2/salience/` | 同名で存在 | 一致 |
| `developmental/v105/diag_v105_main_v2/leakage/` | 同名で存在 | 一致 |

### 1.2 実態の全 17 サブディレクトリ

```
developmental/v105/diag_v105_main_v2/
├── aggregates/      conv_bias_seed{N}.json + per_window_seed{N}.csv
├── audit/           per_event_audit / per_subject_audit / run_level_audit_summary
├── balance/         balance_decisions / balance_summary / c_trajectory
├── bidirectional/   bidirectional_e3_log / bidirectional_e3_member_nodes_log / bidirectional_e3_summary
├── ingestion/       ingestion_events / ingestion_summary
├── integration/     alpha_lifecycle / alpha_membership / beta_lifecycle / beta_membership / beta_distribution / integration_summary
├── introspection/   introspection_log
├── labels/          per_label
├── leakage/         leakage_event_log
├── network/         fam_edges
├── persistence/     label_member_persistence / link_life_log / link_snapshot_log / shadow_component_log
├── pickup/          (空)
├── pulse/           pulse_log
├── representatives/ (空)
├── salience/        salience_event_log
├── selfread/        class_divergence / divergence_log / interaction_log / observation_log / other_records / per_cid_self / v18_window_trajectory
└── subjects/        per_subject_seed{N}.csv + reaped_seed{N}.csv  (= 48 file)
```

### 1.3 24 seeds 揃い具合

すべての CSV ファイルが seed0 〜 seed23 の **24 個揃っている** (確認済)。
- `subjects/per_subject_seed*.csv`: 5,248 行 (24 ヘッダ含む) → **5,224 cid 全体** で依頼書の数値と一致。

---

## 2. 48 次元構造ベクトル必要項目の所在マッピング (Genesis 系)

### 2.1 物理層由来 (M_c) — **すべて per_subject で取得可能**

| 項目 | CSV | 列名 | 備考 |
|---|---|---|---|
| n_core | `subjects/per_subject_seed{N}.csv` | `v11_m_c_n_core` | float |
| s_avg | 同上 | `v11_m_c_s_avg` | float |
| r_core | 同上 | `v11_m_c_r_core` | float |
| phase_sig | 同上 | `v11_m_c_phase_sig` | float、`original_phase_sig` 列も別に存在 (誕生時固定値) |

補足: 同じ per_subject に `v11_b_gen` (β-generation)、`v11_n_pulses_eval`/`v11_n_captured`/`v11_capture_rate`、`v11_mean_delta` 〜 `v11_mean_d_phase` も並ぶ。**capture_rate は M_c 由来のテンソル感度として 49 次元目に追加候補となり得る**。

### 2.2 認知層 (Q ledger) — **`audit/per_subject_audit_seed{N}.csv` が一次ソース**

per_subject にも `initial_residual_Q`/`final_residual_Q`/`total_q_received`/`total_q_digested` はあるが、**Q0 (出生時付与)、Q_remaining (現在量)、Q_spent (累積消費)、Q_exhausted (枯渇flag) は audit 側のみ**:

| 項目 | CSV | 列名 |
|---|---|---|
| Q0 (= Q at birth) | `audit/per_subject_audit_seed{N}.csv` | `v14_q0` |
| Q_remaining (run 終了時) | 同上 | `v14_q_remaining` |
| Q_spent (累積消費) | 同上 | `v14_q_spent` |
| Q_exhausted (bool) | 同上 | `v14_q_exhausted` |
| n_core_member (登録時の n_core) | 同上 | `n_core_member` |

派生指標 (依頼書記載):
- **Q_ratio**: `v14_q_remaining / v14_q0`
- **spend_rate**: `v14_q_spent / (host_lost_window - birth_window)` 程度

window 単位の Q 推移が必要なら → `balance/c_trajectory_seed{N}.csv` の `Q_remaining_at_window_end` 列を window-by-cid で参照。

### 2.3 意識層 (C) — **per_subject + balance/c_trajectory の併用**

| 項目 | CSV | 列名 |
|---|---|---|
| C 終値 | `subjects/per_subject_seed{N}.csv` | `C_at_run_end` |
| C window-by-window | `balance/c_trajectory_seed{N}.csv` | `C_at_window_end` |
| 意識発動回数 | `subjects/per_subject_seed{N}.csv` | `n_consciousness_decisions` |
| 認知発動回数 | 同上 | `n_cognition_decisions` |
| balance skip 回数 | 同上 | `n_balance_skipped` |
| C max (run 全体) | `balance/balance_summary_seed{N}.csv` | `C_max` (run scalar) |

**注意**: `C_max` は per-cid ではなく **run scalar (seed あたり 1 値)**。cid 単位の C max を取りたい場合は c_trajectory の `C_at_window_end` を cid でグルーピングして max() する必要あり。

### 2.4 関係性 (familiarity / attention) — **3 ソース要併用**

per_subject に出るのは **スカラー集計のみ** で、partner-by-partner の値は別ファイル:

| 項目 | CSV | 列名/取り方 |
|---|---|---|
| last_n_partners | `subjects/per_subject_seed{N}.csv` | `last_n_partners` |
| last_familiarity_max | 同上 | `last_familiarity_max` |
| last_attention_size | 同上 | `last_attention_size` |
| **familiarity マップ (from→to エッジ全件)** | `network/fam_edges_seed{N}.csv` | `seed,from,to,familiarity` (1030 行/seed 程度) |
| virtual_attention_sum (run 累積) | `audit/per_subject_audit_seed{N}.csv` | `v14_virtual_attention_sum` / `v14_virtual_attention_entries` |
| virtual_familiarity_sum (run 累積) | 同上 | `v14_virtual_familiarity_sum` / `v14_virtual_familiarity_entries` |

**重要**: `network/fam_edges_seed*.csv` は **run 終了時のスナップショット** であり、時系列推移は記録されていない。familiarity 推移を追うには `pulse/pulse_log_seed*.csv` の `R_familiarity` 列 (per-pulse トラッキング) を読む必要あり。

### 2.5 性格 (disposition) — **per_subject に揃っている**

| 項目 | CSV | 列名 |
|---|---|---|
| social/stability/spread/familiarity (出生時) | `subjects/per_subject_seed{N}.csv` | `prev_*` |
| social/stability/spread/familiarity (run 終了時) | 同上 | `current_*` |
| Δ disposition | 同上 | `delta_*` |
| disposition の range/std/drift (v99) | 同上 | `v99_range_*_min/max/mean/std`, `v99_drift_*_positive/negative/neutral` |
| run 全体最低 std 軸 | 同上 | `v99_lowest_std_axis` |
| run 全体最大正/負 drift 軸 | 同上 | `v99_dominant_positive_drift_axis` / `v99_dominant_negative_drift_axis` |

### 2.6 履歴 (寿命・pulse・event)

| 項目 | CSV | 列名 |
|---|---|---|
| 出生 window | `subjects/per_subject_seed{N}.csv` | `birth_window` |
| host_lost (= 死亡) window/step | 同上 | `host_lost_window` / `host_lost_step` |
| reaped (= ghost 化解消) step | 同上 | `reaped_step` |
| ghost 期間 (steps) | 同上 | `ghost_duration_steps` |
| reap 理由 | `subjects/reaped_seed{N}.csv` | `reap_reason` |
| pulse 数 | `subjects/per_subject_seed{N}.csv` | `v10_pulse_count` |
| n_normal/n_major (= タグ系列) | 同上 | `v10_n_normal` / `v10_n_major` |
| pulse 詳細時系列 | `pulse/pulse_log_seed{N}.csv` | per-pulse 全量 |
| ingestion event 経験回数 | `subjects/per_subject_seed{N}.csv` | `n_ingestions_as_eater` / `n_empty_ingestions_as_eater` / `n_ingested_as_ghost_food` / `n_phantom_contacts_as_eater` |
| be3 (bidirectional e3) 経験 | `bidirectional/bidirectional_e3_log_seed{N}.csv` | per-event |
| 内省タグ履歴 | `introspection/introspection_log_seed{N}.csv` | window 単位の `tags` 列 |

**寿命の正確な定義**:
- **active 期間**: `host_lost_step - (birth_window × steps_per_window)` (host 状態)
- **ghost 期間**: `reaped_step - host_lost_step`
- **トータル**: `reaped_step - birth_step`

reaped されていない (= run 終了時 hosted) cid は `host_lost_window` が空欄。`final_state` 列 (= `hosted` / `ghost` / `reaped`) で分岐必要。

### 2.7 Integration 関連

| 項目 | CSV | 取り方 |
|---|---|---|
| 所属 α-Integration リスト | `integration/alpha_membership_log_seed{N}.csv` | `alpha_ids` 列 (例: `0\|2\|12\|50\|...`)、`binding_strengths` 列 (`0:1.0\|2:1.0\|...`) |
| α 加入数 (run 全体) | `subjects/per_subject_seed{N}.csv` | `n_alphas_joined` |
| α 現在加入数 (run 終了時) | 同上 | `n_alphas_currently` |
| 所属 β-Integration | `subjects/per_subject_seed{N}.csv` | `current_beta_id` (1 cid → 1 β 規律) |
| β 加入数 | 同上 | `n_betas_joined` |
| β からの Q/C inheritance | 同上 | `q_received_from_beta` / `c_received_from_beta` |
| α メンバー詳細 (step 単位) | `integration/alpha_lifecycle_log_seed{N}.csv` | event_type ベース |
| β メンバー詳細 | `integration/beta_lifecycle_log_seed{N}.csv`, `beta_membership_log_seed{N}.csv` | 同上 |
| **ハブ性指標** | 直接列なし、`alpha_membership_log` の `alpha_ids` をパースして所属数カウント | 例: cid 2 は 33 α 所属 = ハブ候補 |

**注**: alpha_membership_log は **run 終了時 (step=25000) の snapshot** で 28 行/seed (= 観察対象 cid 数程度)。**全 cid (218 程度) を網羅していない**。Top-1% ハブ抽出には alpha_membership_log で十分だが、全 cid の所属 α 数を取りたい場合は不足。

代替: `integration/alpha_lifecycle_log_seed{N}.csv` の `member_cids` を全 step で集計する必要あり。

### 2.8 selfread (cid 観察履歴)

依頼書には明示なし。ただし v18 軌跡 (cognitive_gain、theta_distance) や divergence 推移を 49 次元目以降に乗せる場合に有用:

| 項目 | CSV |
|---|---|
| cid の自己観察集計 (run 全体) | `selfread/per_cid_self_seed{N}.csv` |
| window-by-window v18 軌跡 | `selfread/v18_window_trajectory_seed{N}.csv` |
| divergence event log | `selfread/divergence_log_seed{N}.csv` |

per_subject にも v18 関連列 (`v18_*`) は集計済みで存在する。

---

## 3. 既存 cid 集計スクリプトの確認

### 3.1 確認結果: **post-process 集計スクリプトは未実装**

`developmental/v105/*.py` 25 ファイルを精査:

- ランタイム emitter (CSV を生成する側): `v105_spend_audit_ledger.py`、`v914_event_emitter.py`、`v105_integration.py`、`v917_*` 群 など
- 可視化 (animation): `v105_animate_3layer.py`、`v105_animate_compare.py`、`v105_animate_grid.py`、`v105_animate_integration.py`
- 専用解析: `v105_historical_leakage.py`、`v105_salience.py`、`v105_shadow_audit.py`、`v105_memory_readout.py`

→ **依頼書 §2.4 の 4 項目すべて未実装**:
- [ ] cid ごとの寿命計算: なし
- [ ] 5 パターン分類: なし
- [ ] ハブ cid 抽出 (Top 1%): なし (v105 main report で言及されているのは hub β / hub cid の概念であって計算スクリプトは未実装)
- [ ] familiarity マップ集計: なし

### 3.2 v10.6 で新規作成必要

post-process は **完全新規** で書く前提で良い。CSV 読み込み + pandas 集計 + 5 パターン分類ロジックを 1 スクリプトで実装可能。

---

## 4. Language 系 ディレクトリ構造

### 4.1 想定 vs 実態

| 依頼書想定パス | 実態 | 差異 |
|---|---|---|
| `Research/language/atoms/a1_batch/` | `language/atoms/a1_batch/` (327 file) | 一致 (Research/ プレフィクス不要) |
| `Research/language/atoms/esde_dictionary.json` | `language/atoms/esde_dictionary.json` | 一致 |
| `Research/language/lexicon/data/lexicon_entries/` | 同上 (327 file) | 一致 |
| `Research/language/lexicon/data/mapper_output/` | 同上 (325 file) | 一致 |
| `Research/language/lexicon/data/definitions/` | 同上 (3 file: atoms_v1.json, axes_levels_v1.json, categories_v1.json) | 一致 |
| `Research/language/lexicon/data/expanded/` | 同上 (327 file) | 一致 |
| `Research/language/synapse/store.py` | 同上 | 一致 |
| `Research/language/synapse/esde_synapses_v3.json` | 同上 (246 KB) | 一致 |
| `Research/language/synapse/patches/` | 同上 (v3.1〜v3.5 + hotfix の 6 file) | 一致 |
| (依頼書記載なし) | `language/cache/atom_def_emb_v2_minilm.npz` (326×384 float32 MiniLM 埋め込み) | **追加発見** |
| (依頼書記載なし) | `language/esde/projection.py`, `language/projection/`, `language/relations/`, `language/sensor/`, `language/harveste/` (typo: harvester) | **追加発見** |

### 4.2 atom 数の正確な数

- `atoms/a1_batch/`: 327 file = **326 atom + `_summary.json`**
- `lexicon_entries/`: 同 327 file
- `expanded/`: 同 327 file
- `mapper_output/`: 325 file = **325 atom 観測済み**

差分集合 (a1_batch ∖ mapper_output):
- `FND_spaceless` (atom 定義はあるが A1 観測未完 — Legacy Digest 通り)
- `_summary` (集計ファイル、atom ではない)

→ **観測済み 325 atom、観測欠 1 atom (FND_spaceless) で確定**。

### 4.3 a1_batch と lexicon_entries の関係

`diff -q` で確認: **完全に同一ファイル**。バイト一致。

→ どちらか一方を参照すれば足りる。WordNet 拡張済みの core_pool / deviation_pool のリストを保持しているが、**48 スロット連続値は含まれない**。

---

## 5. Atom 326 のスキーマと 48 スロット形式

### 5.1 axes_levels_v1.json で軸構成を確定 (10 軸 × 48 levels)

```
temporal:        7 levels  (emergence/indication/influence/transformation/establishment/continuation/permanence)
scale:           6 levels  (individual/community/society/ecosystem/stellar/cosmic)
epistemological: 5 levels  (perception/identification/understanding/experience/creation)
ontological:     5 levels  (material/informational/relational/structural/semantic)
interconnection: 5 levels  (independent/catalytic/chained/synchronous/resonant)
resonance:       4 levels  (superficial/structural/essential/existential)
symmetry:        5 levels  (destructive/inclusive/transformative/generative/cyclical)
lawfulness:      4 levels  (predictable/emergent/contingent/necessary)
experience:      3 levels  (discovery/creation/comprehension)
value_generation:4 levels  (functional/aesthetic/ethical/sacred)
合計: 7+6+5+5+5+4+5+4+3+4 = 48 levels ✓
```

→ 依頼書記載「10 軸 × 平均 5 レベル = 48 スロット」と一致。

### 5.2 各 atom データの実態 (EMO.love 例)

#### atoms/a1_batch/EMO_love.json (= lexicon_entries/EMO_love.json)

```json
{
  "atom": "EMO.love",
  "category": "EMO",
  "status": "proposed",
  "symmetric_pair": "EMO.hate",
  "definition_en": "An intense feeling of deep affection and care.",
  "core_pool": {
    "rules": ["0_seed", "3_hyponym_d1", "6_derivational", "7_similar_to", "9_antonym"],
    "count": 58,
    "words": [{"w": "adorable", "pos": "adj", "src": "...", "definition": "...", ...}, ...]
  },
  "deviation_pool": { "count": 58, "words": [...] },
  "deviation_stats": { ... },
  "meta": { "generator": "wn_lexicon_entry.py", "version": "1.0.0" }
}
```

→ **48 スロット連続値はここには無い**。WordNet 拡張済みの word pool のみ。

#### lexicon/data/mapper_output/EMO_love_a1.jsonl (1 line per word)

```json
{
  "word": "adorable", "pos": "adj", "atom": "EMO.love",
  "raw_scores":        { "temporal.emergence": 2.0, ..., "value_generation.sacred": 2.0 },  // 48 keys
  "normalized_scores": { "temporal.emergence": 0.001999, ..., "value_generation.sacred": 0.013523 },  // 48 keys
  "entropy_norm": 0.xxx, "focus_rate": 0.xxx, "evidence": "...", "llm_elapsed_sec": ...
}
```

- raw_scores: 0-10 の **離散値** (LLM 生成の整数感)
- normalized_scores: 全 48 スロット合計 1.0 の確率分布 (softmax 系)
- 1 atom = 多 word = 多行 (EMO.love は 58 行、core_pool words に対応)

#### error 行の混入

EMO.love jsonl では **58 word のうち 2 word が error 行 (status="error", raw_scores 欠落)**。集計時は `if 'raw_scores' not in d: continue` で除外必須。

```json
{ "word": "...", "pos": "...", "atom": "EMO.love", "status": "error", "raw_response_length": ..., "error": "..." }
```

→ 全 325 atom × 平均 50 word ≈ **16,000 word 程度のうち error 行が一定比率含まれる**。集計実装ではフィルタ必須。

### 5.3 mapper_output が core_pool のみか deviation 含むか

EMO.love の場合: `core_pool.count = 58` / mapper_output 行数 58 → **core_pool のみ**。deviation_pool は A1 観測対象外。

→ 326 atom 全体で約 **325 × 50 ≈ 16,000 core word の 48 スロット観測** が利用可能。

---

## 6. Atom プロファイル抽出方法の選定

### 6.1 候補比較

| 候補 | データソース | 結果 | v10.6 適合性 |
|---|---|---|---|
| 1. a1_batch から直接 | `atoms/a1_batch/{atom}.json` | **48 スロット値が無い** ので不可 | 不適 |
| 2. mapper_output で集計 | `lexicon/data/mapper_output/{atom}_a1.jsonl` の per-word raw_scores/normalized_scores を mean | 動作確認済 (下記) | **推奨** |
| 3. lexicon_entries から | a1_batch と同一なので候補 1 と同じ | 不可 | 不適 |
| 4. cache/atom_def_emb_v2_minilm.npz | atom 定義の MiniLM 埋め込み (326×384 float32) | **48 次元 ESDE 空間ではない** ので v10.6 の cosine 類似度には使えない | 別目的 (定義文の意味類似度を見る場合のみ) |

### 6.2 推奨: 候補 2 (mapper_output 集計) + normalized_scores の per-word 平均

実証検証 (EMO.love & ACT.create):

```
EMO.love mean_normalized top-5:
  ontological.relational: 0.2638
  scale.individual:       0.1911
  resonance.essential:    0.1416
  epistemological.experience: 0.1301
  value_generation.sacred: 0.0552

ACT.create mean_normalized top-5:
  experience.creation:    0.2233
  symmetry.generative:    0.2217
  ontological.material:   0.0822
  scale.individual:       0.0592
  temporal.emergence:     0.0546

Cosine(EMO.love, ACT.create) = 0.1702  ← 直交に近い (love と create は別概念)
```

→ **意味的に妥当な atom プロファイルが得られる**。

### 6.3 実装上の注意

1. **error 行のフィルタ**: `if 'raw_scores' not in entry: continue` を必ず入れる
2. **正規化選択**: normalized_scores (per-word softmax) を mean → atom-level distribution。raw_scores の sum-then-renormalize もほぼ同等の結果になるが、mean-of-normalized の方が **per-word が等重みで反映される** (頻度高 word に偏らない)。
3. **欠損 atom の扱い**: FND_spaceless は mapper_output に無いので **空ベクトル / NaN として扱い、cid との類似度計算からは除外** する設計が必要。
4. **48 スロットの順序固定**: axes_levels_v1.json の axes 順 × 各 axis の levels 順で固定するか、最初の word entry の `raw_scores.keys()` 順を採用。両者が同一であることを assert する safeguard を入れること推奨。

### 6.4 「cid → Atom は cosine 類似度のみ、Synapse 経由は採用しない」(GPT 監査済み) の前提との整合

依頼書 §3.5 の方針を尊重し、Synapse v3.5 を経由しない直接 cosine 計算で実装する。Synapse は v10.6 では参照しない。

---

## 7. Synapse v3.5 / Phase 9 / 未完項目

### 7.1 Synapse の状態

- `language/synapse/esde_synapses_v3.json`: 246 KB、Base が存在
- `language/synapse/patches/synapse_v3.{1,2,3,3_hotfix,4,5}.json`: 6 patch 揃い
- `language/synapse/store.py`: SynapseStore class 実装あり、`get_instance()` でシングルトン取得 (ただし **明示的な load() 呼出が必要** — `get_instance()` 直後は `atoms count: 0`、`base_path: None` で空状態)
- 動作確認: schema は存在、API は `get_all_concept_ids()` / `get_synapse_dict()` / `get_audit_info()` / `has_synset()` / `get_edges()` / `get_meta_top_k()` が利用可能
- Phase 8 audit 最終 run: `language/data/audit_runs/phase8_integration_20260119_062830.json` (2026-01-19) — **凍結 2026-03 より前の最終健全 run**

→ **v10.6 では使わないが「保険」としては機能する状態**。

### 7.2 Phase 9 のコード所在 — **完全に欠落**

Module Reference v5.7.0 の想定する Phase 9 ディレクトリ:

| 想定パス | 役割 | 実態 |
|---|---|---|
| `language/runner/` | Phase 8-9 Long-Run 実行器 | 不在 |
| `language/integration/` | Phase 9-0 ContentGateway | 不在 |
| `language/integration/relations/` | Obs C SVO 抽出 | 不在 (relations/ は別途存在するが Phase 9-0 統合とは別物) |
| `language/harvester/` | Wikipedia fetch | **typo で `language/harveste/` として存在** (functional コード) |
| `language/statistics/` | Phase 9 legacy W1-W4 | 不在 |
| `language/statistics/pipeline/` | Phase 9 v2.0 Lens 統合 | 不在 |
| `language/discovery/` | Phase 9 legacy W5-W6 | 不在 |
| `language/cell/` | Phase 10 Cell 統合 | 不在 (元々未実装と Module Reference 記載) |

`legacy/` 配下にも無し (古い simulator + PDF のみ)。`tmp/` にも無し。

→ **凍結 2026-03 時点で Phase 9 v2.0 のコードはこのリポジトリ内には存在しない**。Module Reference の「完了」記載は **設計レベルの完了であって、実装は別 repo / branch / 未マージ** の可能性高い。

→ **v10.6 で必要になった場合は Web Claude (古い記憶) に問い合わせるか、新規実装する以外なし**。依頼書 §3.6 の懸念は実態として確認できた。

### 7.3 v10.6 で Phase 9 が必要になる可能性

依頼書 §3.5 の方針 (cid → Atom は cosine のみ、Synapse 不経由) に従う限り **不要**。Phase 9 (W1-W6 統計) は atom-Atom 関係統計の役割であり、cid-Atom 接地には関与しない。

→ v10.6 範囲では **Phase 9 不要、Phase 10 (Cell) も不要**。

### 7.4 凍結時点の他の未解決事項

- **FND_spaceless**: 観測未完 → §4.2 / §6.3 で対応方針整理済
- **triggers_en 拡充 (凍結時残作業)**: 依頼書 §7 範囲外、調査せず
- **Phase 8 再統合テスト (凍結時残作業)**: 同上、調査せず

---

## 8. 環境

### 8.1 Python 環境

```
Python 3.13.5
numpy   2.3.1
pandas  2.3.0
scipy   1.16.0
sklearn 1.7.1   (sklearn.metrics.pairwise.cosine_similarity 動作確認済)
```

→ **すべて揃済**。新規 install 不要。

### 8.2 メモリ・データ規模

| 対象 | 実測 |
|---|---|
| `diag_v105_main_v2/` 全体 | **1.7 GB** (24 seeds 合算) |
| `lexicon/data/mapper_output/` 全体 | 126 MB |
| `atoms/a1_batch/` 全体 | 34 MB |
| 全 cid 数 (24 seeds 合算) | **5,224 cid** (per_subject 合計行数 5248 - 24 ヘッダ) |
| 全 cid × 48 次元 | 5,224 × 48 = 250,752 セル |
| 全 atom × 48 次元 | 326 × 48 = 15,648 セル |
| cosine 類似度行列 | 5,224 × 326 = 1,703,024 セル |

→ **依頼書 §4.2 の試算と一致、Threadripper 環境で問題なし**。

### 8.3 24 seeds 並列処理の可否

- per_subject_seed{N}.csv は **seed 単位で完全独立** → 並列読み込み・並列集計可
- pandas で 24 seeds 全 concat しても 5,224 行程度なので **全 cid を 1 DataFrame に乗せる方が単純**

---

## 9. v10.6 実装上の注意点 (Code A の視点でまとめ)

### 9.1 データ読み込みパス

実装コードの先頭で以下を定数化推奨:

```python
DIAG_ROOT = Path("developmental/v105/diag_v105_main_v2")
SUBJ_DIR  = DIAG_ROOT / "subjects"      # per_subject_seed{N}.csv (依頼書想定の per_subject ではなく subjects)
WIN_DIR   = DIAG_ROOT / "aggregates"    # per_window_seed{N}.csv
AUDIT_DIR = DIAG_ROOT / "audit"         # per_subject_audit_seed{N}.csv  ← Q ledger
BAL_DIR   = DIAG_ROOT / "balance"       # c_trajectory_seed{N}.csv  ← C 推移
NET_DIR   = DIAG_ROOT / "network"       # fam_edges_seed{N}.csv  ← familiarity マップ
INT_DIR   = DIAG_ROOT / "integration"   # alpha_*/beta_* logs
PULSE_DIR = DIAG_ROOT / "pulse"         # pulse_log_seed{N}.csv

LEX_ROOT = Path("language/lexicon/data")
MAPPER_DIR = LEX_ROOT / "mapper_output"  # {atom}_a1.jsonl
AXES_DEF   = LEX_ROOT / "definitions" / "axes_levels_v1.json"
```

### 9.2 Q/C 派生指標の計算

per_subject だけ見ても Q_ratio / spend_rate は無い。必ず audit/per_subject_audit と join する:

```python
df_subj  = pd.read_csv(SUBJ_DIR / f"per_subject_seed{seed}.csv")
df_audit = pd.read_csv(AUDIT_DIR / f"per_subject_audit_seed{seed}.csv")
df = df_subj.merge(df_audit, on=['seed', 'cognitive_id'], how='left',
                    left_on='cognitive_id', right_on='cid')  # 列名要確認
df['q_ratio']    = df['v14_q_remaining'] / df['v14_q0'].replace(0, np.nan)
df['spend_rate'] = df['v14_q_spent'] / (df['host_lost_step'] - df['birth_window']*WIN_LEN).clip(lower=1)
```

**注**: per_subject の cid キーは `cognitive_id`、audit の cid キーは `cid`。**列名が seed × cid で異なる**ため merge 時に `left_on/right_on` 指定必須。

### 9.3 Atom プロファイルの cache 化

326 atom × 約 50 word × 48 dim = 約 750K セルの集計。

- 1 回読んで `atom_profiles.npz` (326×48 float32) として cache 化 → 以降の cosine 計算は埋め込み行列ロードだけで済む
- error 行除外 / 全 48 スロットの完全一致 / atom 順序固定を assert する safeguard を入れて再現性を担保

### 9.4 5 パターン分類ロジック (post-process 新規実装)

依頼書 §2.4 の「5 パターン分類」「ハブ抽出 (Top 1%)」スクリプトは v10.5 までに無い。v10.6 で新規実装する際は:

- 寿命カラム (active 期間 / ghost 期間 / total) の定義を `final_state` で分岐
- 5 パターンの境界 (例: short-lived / mid / long / hub / ghost-only) は `v106_phase_design.md` の指示に従って実装
- ハブ Top 1% は `alpha_membership_log_seed{N}.csv` の所属 α 数で抽出 (run 終了時 snapshot ベース)

### 9.5 familiarity マップの扱い

- run 終了時の **snapshot のみ** が `network/fam_edges_seed*.csv` に保存
- 時系列推移を見たい場合は `pulse/pulse_log_seed*.csv` の `R_familiarity` 列 (per-pulse トラッキング) を pivot
- per_subject の `last_familiarity_max` は **最後の pulse における familiarity 最大値** であって全期間の max ではない (注意)

### 9.6 alpha_membership の網羅性

`integration/alpha_membership_log_seed{N}.csv` は run 終了時の **観察対象 cid (約 28 cid/seed) の snapshot のみ**。全 cid (218/seed) の所属 α を取りたい場合は:

- alpha_lifecycle_log の `member_cids` を全 step で集計
- もしくは v10.6 では「観察対象の Top-1% ハブ抽出」目的のみで十分なので alpha_membership で良い

### 9.7 FND_spaceless の扱い

A1 観測欠損 1 atom。実装上の扱い:

```python
ATOM_LIST = sorted({a.split('_a1.jsonl')[0] for a in os.listdir(MAPPER_DIR)})
# 325 atom → 326 になるよう FND_spaceless を NaN ベクトルで埋めるか、除外するかは v10.6 設計次第
```

依頼書 §7 によると Lexicon v2 追加観測は v10.6 範囲外。**325 atom で進めるのが妥当**。FND_spaceless との類似度を計算する箇所では NaN を返す or skip。

### 9.8 出力先

`developmental/v106/` ディレクトリは **本調査で新規作成済**。v10.6 実装スクリプト・出力 CSV はここに集約推奨:

```
developmental/v106/
├── v106_environment_check_report.md   ← 本ファイル
├── v106_post_process.py               (実装後)
├── outputs/
│   ├── atom_profiles.npz              (Atom 326 × 48 cache)
│   ├── cid_vectors.csv                (5224 × 48)
│   ├── cid_atom_similarity.csv        (5224 × 326)
│   └── 5_pattern_classification.csv   (cid → pattern)
```

---

## 10. 未解決事項リスト (Web Claude への質問)

### Q1. 「48 次元構造ベクトル」の構成定義の確定

依頼書 §2.2 では物理層・認知層・意識層・関係性・性格・履歴・Integration の **7 系列** を挙げているが、**48 次元という数値は Atom 側 (axes_levels) の 48 と偶然一致しているのか、それとも cid 側の構造ベクトルも 48 次元に揃える設計か?**

→ axes_levels の 48 (10 軸) と同じ次元空間に cid を写像する場合、**cid のどの量がどの slot にマッピングされるか** の対応規則が `v106_phase_design.md` に定義されているはず。Web Claude 側で確認・提示願う。

仮: cid の物理層由来 4 値 (n_core, s_avg, r_core, phase_sig) を ontological.material/structural にマップ、disposition 4 値を experience 系にマップ、Q/C を value_generation 系にマップ — のような設計か?

### Q2. ハブ Top 1% の母集団定義

24 seeds 合算後の全 5,224 cid の Top 1% (= 52 cid) を抽出するか、各 seed 内 Top 1% (= 2-3 cid/seed × 24 seeds = 50-70 cid) を抽出するか?

→ 後者の方が seed 比較に有用、ただし "Top 1%" の絶対基準にはならない。`v106_phase_design.md` の意図を確認願う。

### Q3. 5 パターン分類の境界

長寿 / 中寿 / 短寿 / ハブ / ghost-only の 5 パターン想定だが、

- 寿命の閾値 (windows? steps?)
- ハブの所属 α 数閾値
- ghost-only の判定 (final_state == "reaped" で host になった事がない、はあり得るか?)

これらの具体値が `v106_phase_design.md` で定義されているはず。

### Q4. cid → Atom cosine の集約

5,224 cid × 326 atom = 1.7M sim 値。最終出力として:
- 各 cid の Top-K atom (K=?)
- 各 atom の Top-K cid
- 全 sim matrix (CSV / parquet)
の **どれを v10.6 のメインアウトプットとするか** を `v106_phase_design.md` で確定願う。

### Q5. Phase 9 の必要性確認

§7.3 で「v10.6 範囲では Phase 9 不要」と判断したが、これで合っているか Web Claude に確認願う。万一必要となる場合は実装相当のコードが repo 外に存在するかどうかは未確認。

---

## 11. 完了条件チェック

- [x] §2-§4 全項目確認・報告
- [x] Web Claude 想定との差異を §1.1 / §2 / §4.1 / §7.2 にリスト化
- [x] 実装上の注意点を §9 に整理
- [x] Atom プロファイル抽出方法を §6 で提案 (候補 2 = mapper_output mean-of-normalized)
- [x] Phase 9 所在判明 (= リポジトリ内不在を確認)
- [x] 報告書 `v106_environment_check_report.md` を `developmental/v106/` に作成

→ 調査完了。Web Claude が §10 の 5 質問に回答後、`v106_implementation_brief.md` (実装指示書) を確定可能。

---

## 12. 一文サマリ

ESDE Genesis 系の `diag_v105_main_v2/` は依頼書想定と異なる 17 サブディレクトリ構成だが M_c / Q ledger / C / disposition / 履歴 / Integration の **必要データはすべて取得可能**、Language 系は Atom 326 のうち **325 atom 観測済 (FND_spaceless のみ欠落)** で `mapper_output/*_a1.jsonl` の per-word normalized_scores を平均して atom 48 次元プロファイルを生成する方式が **動作検証済**、ただし **5 パターン分類 / ハブ抽出 / cid 寿命計算等の post-process スクリプトは v10.5 までに未実装で v10.6 で新規作成必要**、Phase 9 のコードは repo 内不在 (cosine 直接計算方針なら不要)。

---

*以上、Code A による v10.6 実装前環境調査報告。Web Claude の判断待ち項目は §10。*
