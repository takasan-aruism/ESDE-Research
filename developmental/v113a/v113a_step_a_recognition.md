# v10.13.a Step A 認識確認文書 — Code A 事前齟齬指摘 + 9 論点回答

*作成*: 2026-05-12、Code A
*親*: `v113a_phase_design.md` (主題ドキュメント、Web Claude 2026-05-11) + `v113a_implementation_brief.md` (実装指示書、Web Claude 2026-05-11)
*対象*: Web Claude (相談役、即決事項返答) + Taka (承認)
*目的*: 主題ドキュメント §10 Step A + 実装指示書 §5 Step A の認識確認、§7 の 9 論点全件回答、想定外の事前齟齬を全件指摘

---

## 0. 一文サマリ + 着手前提条件

### 0.1 一文サマリ

実環境調査 (developmental/v112/outputs/main/ + developmental/v107/outputs/main/) で 7 件の事前齟齬を発見、特に重大なのは **A. `propagation_profile.parquet` は medium 固定で 3 window 全集計には `excess_change_adjusted` を使う必要、B. `observation_records.parquet` は存在せず JSON + 集計 parquet 2 種、C. v112 では matched_baseline 空 (cond3 構造的)、D. integration_alpha/beta 小サンプル (24 seeds 1,405 events)、E. null absorption 判定で per-event CI が v10.12 cross_seed_analyzer に存在せず構造的再定義が必要 (Web Claude/Taka 上申事項)、F. long phase (>1000 step) は v10.12 既存出力にも v107 にも含まれず compute_deltas 拡張 + ledger 再走査が必要 (但し計算コスト数分以内)、G. Map 4 で v107 source_events と excess_change を event_id 経由 join 必要**、これらを 9 論点回答に統合し、5 phase 5 Map の post-process 算出は技術的に実装可能、Step B-K 進行案を確定、ただし null absorption 判定の構造的再定義は Web Claude/Taka 承認後に Step G で実装、累計留保 27 件 + 候補 #28 (long phase data 可用性) / #29 (null phase 判定方式) / #30 (matched_baseline 空セル扱い) / #31 (integration_α/β 小サンプル下限) を提示、規律遵守 15 格言全件遵守確認、judgment 回避 (Aruism 整合)。

### 0.2 着手前提条件

| 項目 | 確認 |
|---|---|
| 物理層 frozen 維持 (絶対格言 #2) | ✓ post-process のみ、ledger 不変 |
| 層 B 不変保証 | ✓ 既存出力 read-only、書き込みは v113a/ 配下のみ |
| 層 C パス制限 | ✓ `assert_output_under_v113a()` で構造的保証 |
| smoke 後 main 自動進行回避 | ✓ Step B-G smoke → Step H 判定要請 |
| 資料 push まで完結 | ✓ Step A 文書を同 commit で push 予定 |

---

## 1. 実環境調査結果

### 1.1 v10.12 既存出力 schema 実測

#### 1.1.1 `propagation_profile_v112_seed0.parquet`

```
shape: (400, 27)
windows: medium のみ (immediate / short の集計列なし)
metadata: source_cid, atom_id, atom_index, n_core_bin, formation_relation, n_core, lifespan, fam_max, target_step, death_step, seed, condition_id
delta 列: delta_C_medium, delta_Q_medium, n_pulses_short (1 個のみ short)
path_excess 列: path_X_excess_delta_C_medium × 4 (familiarity / attention_via_salience / temporal_coactivation / integration_alpha)
raw 列: raw_X_delta_C_medium × 5 (5 relation_paths) + raw_unrelated_baseline_delta_C_medium
```

→ **propagation_profile は medium 固定**、Phase 1 (immediate) + Phase 2 (short) の集計には使えない。`excess_change_adjusted` を使う必要。

#### 1.1.2 `excess_change_adjusted_v112_seed0.parquet` (Map 1-3 算出の主入力)

```
shape: (2,718, 43)
relation_path_type: 9 種 (5 path + 4 baseline、matched_baseline は v112 では空)
  - familiarity 325 / attention_via_salience 400 / integration_alpha 59 / integration_beta 59 / temporal_coactivation 400
  - unrelated_baseline 400 / same_step_random_baseline 400 / high_familiarity_outside_integration_baseline 400 / same_integration_low_familiarity_baseline 275
  - matched_baseline 0 (v112 cond3 で構造的に空)
3 window 完全保持: mean_delta_X_{immediate/short/medium} × 5 量 (R_familiarity/Q/C/n_alphas/n_observed)
  + mean_n_pulses_in_window_{imm/short/med}
  + adjusted_* (global_activation 補正済) も同様
columns 43 列 (seed, event_id, relation_path_type, n_targets, 5量×3win×raw/adj, timestamp, normalized_factor_at_event, condition_id)
```

→ **Phase 1-3 (immediate/short/mid) の集計は excess_change_adjusted から完全に算出可能**。

#### 1.1.3 `excess_change_adjusted_v108_standard_seed0.parquet`

```
shape: (17,207, 43)
relation_path_type: 10 種 (matched_baseline 2,391 件含む)
v108_standard では matched_baseline 含む
```

#### 1.1.4 metadata の所在 (observation_records.parquet 不在)

実装指示書 §3.1 で「`observation_records_seed{N}.parquet`」と参照されているが、**実体は存在しない**:

- 存在するファイル:
  - `observation_records_main.json` (1.6 MB、per-seed/per-condition summaries の集計、metadata 含む)
  - `observation_summary_main.parquet` (per-seed × condition の集計 tabular、31 KB)
  - `observation_stratified_main.parquet` (per-seed × condition × stratify_axis × stratum、154 KB)

- **per-event の metadata (n_core_bin, formation_relation, atom_id, source_cid) は `propagation_profile_*.parquet` に含まれる** (上記 §1.1.1)

→ Map 1-5 で metadata を取得する際は `propagation_profile_*.parquet` から merge (event_id keyed) または `excess_change_adjusted` を直接 + propagation_profile から metadata 補完。

#### 1.1.5 `cross_seed_analysis.json` + `paired_analysis.parquet`

```
paired_analysis_per_metric: 7 entries (cross-seed level)
  metric, n_seeds=24, paired_d, sign_test (n_positive/negative/zero, p_value_two_sided),
  bootstrap_CI_95 (lower, upper, n_iter=1000, crosses_zero), boot_mean, boot_std

paired_analysis.parquet: shape (7, 15) — metric ベース、cross-seed level のみ
```

→ **per-event レベルの CI は算出されていない**、cross-seed level の paired_d のみ。

#### 1.1.6 `window_paired_analysis.parquet` (本日追加調査)

```
shape: (21, 15) = 3 window × 7 metric の paired analyses
columns: window, metric, paired_d, sign_p_two_sided, ci_lower, ci_upper, crosses_zero
```

→ 3 window × metric の paired_d は既に算出済。これを Map 1-5 で利用可能。

### 1.2 v10.7 既存出力の存在確認

```
developmental/v107/outputs/main/: 218 files
  source_events_seed{N}.parquet × 24 (event_source_type 5 種、event_id → type の mapping)
  excess_change_seed{N}.parquet × 24 (per-event × path、3 window、event_source_type 列なし)
  baselines_with_delta_seed{N}.parquet × 24
```

→ **Map 4 (phase × event 種別) で v107 を参照可能**。ただし v107 `excess_change` には `event_source_type` 列がない、`source_events.parquet` から event_id 経由で type を join 必要。

### 1.3 long phase (>1000 step) のデータ可用性

- **v10.12 propagation_profile**: medium 固定、long なし
- **v10.12 excess_change_adjusted**: 3 window (imm/short/med = 1-10, 10-100, 100-1000)、long なし
- **v107 excess_change**: 同じく 3 window のみ
- **v107 ledger (diag_v105_main_v2/)**: 利用可能、再走査で long phase 算出可能

**算出コスト見積もり** (Code A 推定):
- 各 event について timestamp + (1000, RUN_END=25000) の post-state を取得 → 24,000 step 窓の集計
- v107 compute_deltas の WINDOW_DEFS に `("long", 1000, RUN_END=25000)` を追加して再実行
- v112 events 10,500 + v108_standard 60,000 = 約 70K events × ~10 path = 700K (event, path) 計算
- per-seed ~5-10 秒、24 並列で **約 1-3 分** (層 B 不変、ledger は read-only)

→ **long phase 算出は技術的に可能、コスト許容範囲内**。

---

## 2. 9 論点への formal 回答 (実装指示書 §7)

### 2.1 論点 1: 5 phase 境界 (半開区間で良いか)

**回答**: ✓ OK、v107 WINDOW_DEFS と完全整合。

Phase 1-3 は v107 既存 `compute_deltas` の挙動を継承:
```python
# v107 baseline_constructor.py の挙動 (実測)
df["post_ts_{win}"] = df["timestamp"] + high  # high は閾値の上限
df[f"delta_X_{win}"] = X_at_post - X_at_pre
# 各 window で `low < pulse_t <= high` で n_pulses_in_window をカウント (n_pulses は閉区間 high 含む)
```

→ Phase 1 (immediate 1-10): t+1 から t+10 までの状態変化、t+10 含む  
→ Phase 2 (short 10-100): t+10 から t+100 までの状態変化、t+100 含む  
→ Phase 3 (mid 100-1000): t+100 から t+1000 までの状態変化、t+1000 含む

実質的に **post-state 取得 step を high で取る** 設計のため、phase 間で境界 step (10, 100, 1000) は共有される (immediate の終点 = short の post-state 取得 step)。これは v107 設計通り、変更不要。

### 2.2 論点 2: long phase (>1000 step) の可用性

**回答**: ✗ 既存出力に **含まれない**、新規実装が必要。ただし計算可能。

- v10.12 既存: 3 window のみ
- v107 既存: 3 window のみ
- v107 ledger は利用可能 → `compute_deltas` の WINDOW_DEFS に `("long", 1000, 25000)` を追加して再走査

**実装方針** (Step H で実施):
- v107 `compute_deltas` を拡張、`WINDOW_DEFS_LONG = [("long", 1000, 25000)]` を新規定義
- v10.12 受容 cid pool 420 + v108_standard 5,111 cid に対して long phase の delta を算出
- 出力: `developmental/v113a/outputs/main/excess_change_long_v112_seed{N}.parquet` + v108_standard 版

**計算コスト**: 24 seeds × 24,000 step 窓集計 → 約 1-3 分 (parallel -j24)、層 B 不変保証。

### 2.3 論点 3: null absorption 判定の CI 結果

**回答**: ✗ v10.12 cross_seed_analyzer は **cross-seed level のみ**、per-event レベルの CI なし。**判定条件の構造的再定義が必要 (Web Claude/Taka 上申事項)**。

#### 2.3.1 現状の限界

実装指示書 §2.3 の `is_null_absorption` 関数:
```python
def is_ci_crosses_zero(event_id, target_cid, path) -> bool:
    # per-event の CI ??
```
↑ この関数は **v10.12 出力には対応するデータがない**。

理由:
- v10.12 cross_seed_analyzer は (metric × condition pair) の cross-seed paired_d / bootstrap CI のみ
- 各 event_id × path の CI を算出するには、各 event_id × path について 24 seeds の値で bootstrap → ナイーブ実装ではコスト大 (10,500 events × 4 paths × 1000 iter ≈ 42M ops、別途見積もり)
- そもそも event_id は seed 内 unique (v112 では `{seed}_v112_atom_{i}`、v108 では `{seed}_atom_{i}`)、24 seeds 間で同 event_id の値を集めることが不可能

#### 2.3.2 Code A 提案する代替判定 (Web Claude/Taka 承認待ち)

**案 X-1: cell-level null absorption** (推奨):
- 集計単位: phase × condition × n_core_bin × atom_id
- 「null cell」= その cell 内で、`mean(delta_C) != 0` だが `mean(path_excess)` 5 種全て CI が 0 を跨ぐ (cross-seed bootstrap で 24 seeds 集計)
- これは **既存 window_paired_analysis** の延長で算出可能

**案 X-2: event-level proxy 判定** (代替):
- 「null event」= その event で `|raw_X_delta_C_medium - raw_unrelated_baseline_delta_C_medium|` 5 path 全てが 0 ちょうど または NaN
- これは構造的判定 (CI を使わない)、ただし「方向性なし」の本来意味とは異なる

**Code A 推奨**: 案 X-1 (cell-level)、ただし Web Claude/Taka 承認待ち。

#### 2.3.3 Map 5 設計への影響

実装指示書 §4.5 Map 5 schema (`map5_null_phase_*.parquet`) は event 単位を想定:
- `n_null_events`, `n_total_events`, `null_ratio`, `n_null_by_ncore_bin_*`, `atom_distribution` (json)

案 X-1 採用時の修正案:
- 集計単位を phase × condition × n_core × atom に変更
- `n_null_cells` / `n_total_cells` / `null_cell_ratio`
- per-cell 構造的特徴を記録

Web Claude/Taka 判断要請事項。

### 2.4 論点 4: v10.7 既存出力との接続 (Map 4 で event 種別)

**回答**: ✓ 可能、ただし event_id 経由 join 必要。

#### 2.4.1 v10.7 出力構造

- `source_events_seed{N}.parquet`: 14,385 events/seed、columns: `event_id, event_source_type, source_cid, timestamp, ...`
- `excess_change_seed{N}.parquet`: 116,125 rows、columns に `event_source_type` **なし**

#### 2.4.2 接続方法 (Step F 実装)

```python
df_excess = pd.read_parquet(f'v107/outputs/main/excess_change_seed{seed}.parquet')
df_source = pd.read_parquet(f'v107/outputs/main/source_events_seed{seed}.parquet')
type_map = df_source[['event_id', 'event_source_type']].drop_duplicates('event_id')
df_with_type = df_excess.merge(type_map, on='event_id', how='left')
# 以後 event_source_type で groupby して phase × event 種別を集計
```

#### 2.4.3 注意事項

- v107 excess_change は 3 window のみ (long phase なし)
- v10.12 atom_introduction_event は v10.7 出力には含まれない (v108 以降に追加された 6 種目)
- Map 4 で v10.7 (5 種 natural) + v10.12 (atom_introduction_event 1 種) を **6 種で並列記述** が望ましい

### 2.5 論点 5: v107 既存モジュール (baseline_constructor, path_analyzer) の流用範囲

**回答**: ✓ 流用可、ただし long phase 用に `compute_deltas` 拡張が必要 (論点 2 参照)。

#### 2.5.1 流用可能関数 (Phase 1-3 集計)

- `v107_event_aggregator.attach_pre_event_state` (event 時点の cid 状態取得)
- `v107_baseline_constructor.compute_deltas` (3 window 6 量集計)
- `v107_baseline_constructor.compute_baseline_excess_change` (event × path mean 集計)
- `v108_global_activation_correction.add_adjusted_excess` (global_activation 補正)

→ v10.12 excess_change_adjusted は **既に上記関数で算出済**、Phase 1-3 は流用のみで完結。

#### 2.5.2 長 phase で必要な拡張

- `v107_baseline_constructor.WINDOW_DEFS` に `("long", 1000, 25000)` を追加
- v107 `compute_deltas` を再実行 (v107 出力には書き込まない、v113a/ 配下に新規出力)

Step H で `v113a_long_phase_compute.py` を新規実装、v107 関数を import + WINDOW_DEFS 拡張版で再走査。

### 2.6 論点 6: 出力ディレクトリ命名 (v113a vs v113_a)

**回答**: ✓ `v113a` で OK (`developmental/v113a/`)。

理由:
- バージョン命名規則は過去 `v101`〜`v112` で 3 桁数字 + 末尾接尾辞なし
- v113a は新運用 (主題ドキュメント §3.4 Taka 整理「マイナーバージョンの次元を一つ増やす」) の最初の適用
- `v113a` (3 桁 + 1 文字) で統一的命名、パス短縮、検索性高い
- `developmental/v113a/outputs/main/` 作成済

### 2.7 論点 7: path_category 分離の実装方法

**回答**: ✓ parquet 列として `path_category` を追加、別ファイル分離は不要。

```python
PATH_CATEGORY_MAP = {
    "familiarity": "atom_related",
    "attention_via_salience": "atom_related",
    "temporal_coactivation": "atom_related",
    "integration_alpha": "layer5_structural",
    "integration_beta": "layer5_structural",
    "unrelated_baseline": "baseline",
    "same_step_random_baseline": "baseline",
    "matched_baseline": "baseline",
    "same_integration_low_familiarity_baseline": "baseline",
    "high_familiarity_outside_integration_baseline": "baseline",
}
df["path_category"] = df["relation_path_type"].map(PATH_CATEGORY_MAP)
```

- Map 2 では `path_category` で groupby + `path_name` (= relation_path_type) で詳細記録
- baseline 系は Map 2 の主観察対象ではない (baseline は path_excess の reference)、別系統 (`path_category="baseline"`) で記録

絶対格言 #11 遵守: 「path 5 種」と一括化せず、atom_related (3) と layer5_structural (2) の構造的区別を明示。

### 2.8 論点 8: 規律遵守要件 (§8) の具体的実装方針

**回答**: 既存 v10.12 実装の規律を継承。

| 規律 | 実装 |
|---|---|
| 絶対格言 #2 物理層 frozen | `safe_write_parquet_v113a()` + read-only 既存出力参照 + ledger 不変 |
| 絶対格言 #4 n_core 別層化 | Map 1-5 全てで n_core_bin (bin_2/3_4/5+) 別が default、集団平均は補助 |
| 絶対格言 #9 神の手回避 | 5 phase 境界は v107 WINDOW_DEFS 継承、null 判定は構造的 (案 X-1)、効果サイズ閾値なし |
| 絶対格言 #11 概念単位を雑に扱わない | `path_category` 列で atom_related / layer5_structural / baseline 分離 |
| 絶対格言 #12 Aruism 判定回避 | Step J 観察報告で success/fail なし、観察事実のみ |

### 2.9 論点 9: 想定外の事前齟齬指摘 (Code A 観点で全件列挙)

下記 §3 (事前齟齬指摘リスト) に整理。

---

## 3. 事前齟齬指摘リスト (重要度順、Web Claude/Taka 即決事項候補)

### 3.1 重大度 高 (実装着手前に Web Claude/Taka 即決事項とすべき)

#### 齟齬 A: `propagation_profile.parquet` は medium 固定

**実装指示書 §3.1 の記述**:
> | `propagation_profile_v112_seed{N}.parquet` | per-event 波及プロファイル | event_id, target_cid, delta_C_immediate, delta_C_short, delta_C_medium, n_pulses_short, path_*_excess_delta_C_medium 等 |

**実体**:
- propagation_profile は **medium のみ** (delta_C_immediate / delta_C_short 列は存在しない)
- 3 window 集計には `excess_change_adjusted_*.parquet` を使う必要

**Code A 提案**: 実装指示書 §3.1 を修正、`excess_change_adjusted_v112_seed{N}.parquet` を主入力とする。propagation_profile は metadata (n_core_bin, formation_relation 等) 取得用に併用。

#### 齟齬 B: `observation_records_seed{N}.parquet` は存在しない

**実装指示書 §3.1 の記述**:
> | `observation_records_seed{N}.parquet` | metadata (n_core_bin, formation_relation 等) | event_id, target_cid, n_core_bin, formation_relation, atom_id |

**実体**:
- 存在するのは `observation_records_main.json` (1.6 MB、集計 JSON)、`observation_summary_main.parquet`、`observation_stratified_main.parquet`
- per-event の metadata は **propagation_profile 自体に含まれる** (n_core_bin, formation_relation, atom_id, source_cid 列)

**Code A 提案**: 実装指示書 §3.1 を修正、per-event metadata は propagation_profile から取得。

#### 齟齬 C: v112 では matched_baseline が空 (cond3 構造的)

**実装指示書 §2.3 path 5 種**: `["familiarity", "attention_via_salience", "temporal_coactivation", "integration_alpha", "integration_beta"]` ← これは path だが、null absorption 判定で「path 5 種全て CI 0 を跨ぐ」と書いている。

**実体**: v112 では:
- matched_baseline 0 件 (cond3 で n_core ≥ 5 絞り込み、留保 #26)
- familiarity 325 / attention_via_salience 400 / temporal_coactivation 400 / integration_alpha 59 / integration_beta 59
- → integration_α/β は per-event level で 1-2 events のみの場合あり (24 seeds 集計で 1,405)

**Code A 提案**:
- 「path 5 種」は relation_paths (5 種、baselines 4 種は除く)
- v112 integration_α/β は小サンプル (留保 #31 候補)、null 判定で集計困難な場合は記録のみ
- matched_baseline 空は留保 #30 候補として記録

#### 齟齬 E: null absorption 判定の構造的設計問題 (論点 3 詳細)

実装指示書 §2.3 の `is_ci_crosses_zero(event_id, target_cid, path)` は **v10.12 出力には対応する CI なし**。per-event レベルの bootstrap CI を新規算出するか、集計単位を変更 (cell-level、案 X-1) するか **Web Claude/Taka 即決事項**。

### 3.2 重大度 中

#### 齟齬 D: integration_alpha/beta が小サンプル

**実体**:
- v112 seed 0 で integration_alpha 59 events / integration_beta 59 events (path 別)
- 24 seeds 全体で integration_α/β それぞれ 1,405 events
- v108_standard では integration_α/β それぞれ 699/seed = 16,776/24 seeds
- per-event level 集計では integration_α/β は 1-2 events になる場合あり

**Code A 提案**: Map 2 で integration_α/β の n_events を併記、小サンプル cell は層化集計で記録のみ深追いしない。

#### 齟齬 F: long phase 算出には ledger 再走査 + compute_deltas 拡張が必要

**実体**:
- v10.12 / v107 既存出力に long phase なし
- v107 ledger (`diag_v105_main_v2/`) は利用可能、compute_deltas に WINDOW_DEFS 追加で算出可能
- 計算コスト: per-seed ~5-10 秒、24 並列で約 1-3 分

**Code A 提案**: Step H で long phase 算出を実装、v113a/ 配下に `excess_change_long_*.parquet` を新規出力。

#### 齟齬 G: Map 4 で v107 source_events と excess_change の event_id 経由 join 必要

**実体**: v107 excess_change には `event_source_type` 列なし、source_events.parquet から merge 必要 (論点 4 §2.4.2 参照)。

### 3.3 重大度 低 (Code A 内部判断で進められる、報告のみ)

| 齟齬 | 内容 | 対応 |
|---|---|---|
| 命名 | implementation_brief は `_main.json` 形式、新出力は `_seed{N}.parquet` + `_cross_seed.parquet` で統一 | Step C-G で実装、Web Claude 確認 |
| n_iter | 既存 v10.12 cross_seed_analyzer は `BOOTSTRAP_N = 1000, RANDOM_SEED = 12112` | 流用、deterministic 保証 |
| pandas 列順 | post-process 集計時の列順は seed → condition → phase → ... → 値列 | 命名規則統一 |

---

## 4. 留保事項候補 (累計 27 → 31 件)

実装指示書 §10 + Code A 観察:

| id | step | title (要約) |
|---|---|---|
| **#28** | Step H | long phase (>1000 step) のデータ可用性 → 算出可能だが新規 post-process 必要 (本書で確定) |
| **#29** | Step G | null absorption phase 判定方式 (per-event CI vs cell-level) → Web Claude/Taka 上申事項 |
| **#30** | Step C-D | matched_baseline が v112 で空、null 判定での扱い |
| **#31** | Step D | v112 integration_α/β が小サンプル (n_events 1-2/event)、per-event 集計の信頼性 |

---

## 5. Step B-K 進行案 (Code A 推奨、Web Claude/Taka 承認後発動)

| Step | 内容 | 想定時間 | 出力 |
|---|---|---|---|
| Step A (本書) | 認識確認 + 9 論点回答 + 事前齟齬指摘 | (完了) | `v113a_step_a_recognition.md` |
| Step B | 環境チェック + 層 B baseline 記録 (~1,500 files の mtime+size snapshot) | 10 分 | `v113a_step_b_environment.md` + baseline.json |
| Step C | Map 1 (phase × n_core_bin) × 3 phase (imm/short/mid) | 3 分 | `map1_phase_x_ncore_seed{N}.parquet` × 48 + cross_seed |
| Step D | Map 2 (phase × relation_path × path_category) | 3 分 | `map2_phase_x_path_seed{N}.parquet` × 48 + cross_seed |
| Step E | Map 3 (phase × formation_relation) | 2 分 | `map3_phase_x_formation_seed{N}.parquet` × 48 + cross_seed |
| Step F | Map 4 (phase × event 種別)、v107 source_events 参照 | 5 分 | `map4_phase_x_event_seed{N}.parquet` × 48 + cross_seed |
| Step G | Map 5 (null phase)、案 X-1 (cell-level) 実装、Web Claude/Taka 即決事項返答後 | 3-5 分 | `map5_null_phase_*.parquet` |
| Step H | long phase (>1000 step) 算出、v107 compute_deltas 拡張 + ledger 再走査 | 3-5 分 + 1-3 分 計算 | `excess_change_long_*.parquet` + Map 1-5 long phase 追加 |
| Step I | bit-identity 全層検証 (層 A 同 seed 2 回 / 層 B ~1,500 files 不変 / 層 C v113a/ 配下) | 10 分 | `v113a_step_i_bit_identity_report.md` |
| Step J | 観察事実報告 (Map 1-5 直感語 + 構造文併記、留保 31 件、judgment 回避) | Code A 作業時間 2-3 時間 | `v113a_observation_report.md` |
| Step K | Phase Result (Web Claude 担当) | Web Claude 作業 | `v113a_phase_result.md` |

**合計計算時間 (Step C-I)**: 30-45 分、`v10x_implementation_spec.md` の v10.12 main run (20.35 秒) と比べて軽量。

**Step G null absorption 判定方式** は Web Claude/Taka 即決事項 (本書 §2.3) 確定後に発動、それまで他 Step は進行可。

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step A での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 5 phase は v10.6-v10.12 観察事実 (構造) を起点 |
| 2 | 物理層 frozen 絶対 | ✓ post-process のみ、ledger 不変、層 B ~1,500 files 不変保証 |
| 3 | ベースライン比較 + 効果サイズ | ✓ v108_standard baseline 継承、|delta_ratio|>1% 評価 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ Map 1-5 全てで n_core_bin 別 default |
| 5 | 観察軸増やすことを駆動要因にしない | ✓ 5 phase は既存観察軸の統合枠組み |
| 6 | 出口の固定 | ✓ Map 1-5 を出口物として固定 |
| 7 | 主題着手前に上位資料を読む | ✓ v10.7 オービス + v10.10 §3.4 + v10.12 §4 + v10.12 §5.1 参照済 |
| 8 | 過去観察軸の照会 | ✓ §2-3 で v10.6-v10.12 の取扱を全件確認 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ 5 phase 境界は v107 継承、null 判定は構造的、ハンドチューニングなし |
| 10 | 因果ではなく因果候補 | ✓ Map 1-5 は「対応関係を観察」表現、「効いた」「失敗」表現なし |
| 11 | 概念単位を雑に扱わない | ✓ path_category で atom_related / layer5_structural / baseline 分離 |
| 12 | Aruism 判定回避 | ✓ success/fail 判定置かない |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Gemini / GPT / Web Claude / Code A の役割境界遵守 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka §1.9 + 2026-05-11 整理は主題ドキュメント §4 で原文保存済、本書では参照のみ |
| 15 | 5 者運用体制の補完性 | ✓ Web Claude 統合 / GPT Auditor 案を主軸 / Gemini 案は v10.13.c へ |

→ **15 格言全項目遵守確認**。

---

## 7. Web Claude/Taka への即決事項返答要請

### 7.1 即決事項 (Step B 着手前に必要)

1. **null absorption 判定方式**: 案 X-1 (cell-level、phase × condition × n_core × atom で集計) を採用するか、別案か
2. **Map 5 schema 修正**: cell-level 採用時、実装指示書 §4.5 の event-based schema を cell-based に変更してよいか
3. **propagation_profile vs excess_change_adjusted の主入力選択**: 齟齬 A/B 確認、`excess_change_adjusted` を主入力 + propagation_profile を metadata 補完で OK か
4. **integration_α/β 小サンプル扱い**: 留保 #31 として記録、Map 2 で n_events 併記で OK か
5. **long phase 算出時期**: Step H で実装 (B-G smoke 後)、または Step C-G と並行して優先実装するか

### 7.2 Step B 着手判断

上記 #1-#5 が確定すれば Step B 環境チェック → Step C-G 順次進行 → Step H (long phase) → Step I-K の流れで進行可能。

---

## 8. 一文サマリ (再掲)

実環境調査で 7 件の事前齟齬を発見 (A: propagation_profile は medium 固定 / B: observation_records.parquet 不在 / C: v112 matched_baseline 空 / D: integration_α/β 小サンプル / E: null absorption per-event CI なし / F: long phase 新規実装必要 / G: v107 event_source_type は join 必要)、9 論点全件回答で 5 phase 境界 (v107 WINDOW_DEFS 半開区間継承) / long phase (compute_deltas 拡張 + ledger 再走査で算出可能、1-3 分) / null absorption (案 X-1 cell-level 推奨、Web Claude/Taka 即決事項) / v10.7 接続 (event_id 経由 join) / v107 流用 (compute_deltas 拡張で完結) / 命名 (v113a で OK) / path_category (parquet 列で分離) / 規律 (15 格言全遵守) / 想定外齟齬 7 件 を整理、累計留保 27 件 + 新規 4 件 (#28 long phase 可用性 / #29 null 判定方式 / #30 matched_baseline 空 / #31 integration_α/β 小サンプル) を提示、Step B-K 進行案で合計計算時間 30-45 分 + Code A 作業時間 4-6 時間と見積もり、絶対格言 #2 (物理層 frozen) + #4 (n_core 別層化) + #9 (神の手回避) + #11 (path_category 分離) + #12 (判定回避) 全項目遵守、Taka §1.9 + 2026-05-11 整理は主題ドキュメント §4 で原文保存済を確認、Web Claude/Taka 即決事項返答 (null 判定方式 + 入力選択 + small_sample 扱い + long phase 時期) 確定後に Step B 着手可。

---

*以上、v10.13.a Step A 認識確認 (Code A)。Web Claude/Taka 即決事項返答を受領後、Step B 環境チェックに進む。事前齟齬 7 件 + 留保候補 4 件 + 9 論点全件回答 + 規律 15 格言遵守確認 を本書に整理。*
