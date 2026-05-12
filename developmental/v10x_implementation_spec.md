# ESDE v10.x 実装技術仕様書

*作成*: 2026-05-11、Code A
*最終更新*: 2026-05-12 (v10.13.a 反映)
*目的*: ESDE v10.0-v10.13.a の実装レベル詳細仕様を 1 本に集約、後出しドキュメント
*対象*: AI (Web Claude / 他の Code Agent / Code A 自身) 参照用、無駄を削減
*親資料*: `docs/ai_summaries/06_developmental_summary.md` (概念詳細) + `docs/ai_summaries/06b_developmental_phase15_summary.md` (Phase 1.5 概念詳細) + `developmental/v10x_overall_review.md` (バージョン俯瞰)、本書は **実装ファイル中心**

---

## 0. このドキュメントの位置づけ

- 各 v10.x バージョンの **モジュール構成 / class / 関数 / 定数 / I/O schema** を列挙
- 共通技術基盤 (v107 baseline_constructor、path_analyzer、global_activation 等) を一箇所に集約
- Phase ごとの機能リストを §7 に独立掲載
- コード片は最小限、構造記述を中心

---

## 1. ESDE 全体アーキテクチャ

### 1.1 4 層 + Layer 5

| 層 | 主体 | 主要 attribute |
|---|---|---|
| 物理層 | node | label、frozen (v10.0 以降不変) |
| 存在層 | label | hosted/ghost、E1/E2/E3 接触 |
| 認知層 (cog) | cid | Q (認知資源)、pulse、familiarity |
| 意識層 | cid | C (意識資源、Q から転化) |
| **Layer 5** (v10.4-v10.5) | α/β-Integration | member_cids、Q_inherited、C_inherited |

### 1.2 データフロー (v10.5 以降の正準パイプライン)

```
[Phase 1] v9.18 + v10.1-v10.5 ESDE シミュレーション
   ↓
diag_v105_main_v2/ (CSV ledger):
   subjects/, audit/, balance/, pulse/, integration/, network/, ingestion/, salience/
   ↓
[Phase 1.5 post-process]
v10.6 cid_atom_sim_matrix.parquet (cid × 326 atom cosine)
   ↓
v10.7 source_events.parquet (5 種 natural event)
       relation_paths.parquet (5 種 path)
       baselines_with_delta.parquet (3 window × 6 metric)
       excess_change.parquet (event × path mean_delta)
   ↓
v10.8 atom_introduction_events.parquet (60K events、25 atom × 100 cid × 24 seed)
       global_activation_factor.parquet (natural only、100 step bin)
       excess_change_adjusted.parquet (補正済)
   ↓
v10.9-v10.12 各種派生 (gate/cond/within-cid 等)
   ↓
v10.13.a Map 1-5 + long phase (5 phase × 各軸の post-process)
       map1-5_*.parquet (phase × n_core/path/formation/event/null cell)
       excess_change_long_*.parquet (v107 WINDOW_DEFS monkey-patch で 1000-25000 step)
```

### 1.3 共通規約

- `assert_output_under_v{NNN}(path)`: 書き込み先を v{NNN}/ 配下に制限 (層 C 保証)
- `safe_write_parquet_v{NNN}()`: 上記 wrapper + 親 dir 作成 + snappy 圧縮
- bit-identity 3 層: 層 A (同 seed 2 回実行 hash 一致) / 層 B (既存出力不変) / 層 C (パス制限)
- per-seed × per-condition の並列実行: `multiprocessing.Pool(processes=24)`
- 確定的乱数: `numpy.random.default_rng(seed)` または `random.Random(seed)`

---

## 2. 共通技術モジュール (Phase 1.5 で使い回し)

### 2.1 v107_event_aggregator.attach_pre_event_state

```python
def attach_pre_event_state(df: pd.DataFrame, seed: int) -> pd.DataFrame
```

各 event の timestamp 時点の cid 状態を merge_asof backward fill で添付:

| 列 | 由来 | 説明 |
|---|---|---|
| birth_step | pulse_log の cid 最初 t | cid 誕生 step |
| lifespan_so_far | timestamp - birth_step | event 時点の年齢 |
| n_core_member, v14_q0 | per_subject_audit | cid 構造 |
| final_state, host_lost_step, reaped_step | per_subject | ghost 化 step |
| R_familiarity_pre | pulse_log 直近 R_familiarity | 接触頻度 |
| Q_pre, C_pre | balance_decisions Q_at_decision, C_at_decision | event 時点の Q/C |
| window_value, C_at_window_end, Q_remaining_at_window_end | c_trajectory | window 別 |
| n_alphas_pre, n_observed_pre | alpha_lifecycle, salience_event_log | 累積 |

### 2.2 v107_path_analyzer.build_all_paths

```python
def build_all_paths(seed: int, source_events: pd.DataFrame) -> pd.DataFrame
```

5 種 relation_path_type を統合した DataFrame を返す。各 event について target cid を top-N (default 20) で抽出:

| relation_path_type | 構築方法 | 元データ |
|---|---|---|
| familiarity | network/fam_edges 双向 1-hop | network/fam_edges_seed{N}.csv |
| attention_via_salience | salience_event_log の mass 累積 | salience/salience_event_log_seed{N}.csv |
| integration_alpha | alpha_lifecycle birth member_cids 全ペア | integration/alpha_lifecycle_log_seed{N}.csv |
| integration_beta | beta_lifecycle birth member_cids 全ペア | integration/beta_lifecycle_log_seed{N}.csv |
| temporal_coactivation | pulse_log の同時間窓 (±100 step) cid | pulse/pulse_log_seed{N}.csv |

出力スキーマ: `event_id, source_cid, timestamp, target_cid, relation_path_type, relation_strength, hop_distance, seed`

### 2.3 v107_baseline_constructor.build_baselines

```python
def build_baselines(seed: int, source_events: pd.DataFrame) -> pd.DataFrame
```

5 種 baseline_type を統合 (relation_path_type と同じ column 名で区別):

| baseline_type | 定義 |
|---|---|
| unrelated_baseline | R_familiarity < 5.0 (FAM_LOW_THRESHOLD) |
| same_step_random_baseline | 同 window で active な random cid |
| matched_baseline | n_core / age / final_state 同一 |
| same_integration_low_familiarity_baseline | 同 α/β + familiarity bottom 25% |
| high_familiarity_outside_integration_baseline | familiarity top 25% + 異なる α/β |

### 2.4 v107_baseline_constructor.compute_deltas

```python
def compute_deltas(seed: int, df_targets: pd.DataFrame) -> pd.DataFrame
```

各 (event_id, target_cid, relation_path_type) について 6 量 × 3 window の delta を計算:

```python
WINDOW_DEFS = [
    ("immediate", 1, 10),     # t+1 to t+10
    ("short", 10, 100),       # t+10 to t+100
    ("medium", 100, 1000),    # t+100 to t+1000
]
```

6 量: `delta_Q`, `delta_C`, `delta_R_familiarity`, `delta_n_alphas`, `delta_n_observed`, `n_pulses_in_window`
→ 6 × 3 = 18 delta 列

### 2.5 v107_baseline_constructor.compute_baseline_excess_change

```python
def compute_baseline_excess_change(df_with_delta: pd.DataFrame) -> pd.DataFrame
```

`groupby(["seed", "event_id", "relation_path_type"])` で各 (event, path) の mean delta を集計。出力: 18 mean_delta_* 列 + n_targets。

### 2.6 v108_global_activation_correction

```python
def compute_global_activation_factor(seed: int) -> pd.DataFrame
def add_adjusted_excess(df_excess, df_src, df_factor) -> pd.DataFrame
```

natural events 5 種 (pulse / ingestion / alpha_birth / beta_birth / consciousness) のみを 100 step bin でカウント、正規化:
- `STEP_BIN_SIZE = 100`
- 正規化: `(count - mean) / std`
- 各 event の `timestamp` で factor を lookup
- `adjusted_mean_delta_X = mean_delta_X - normalized_factor × delta.std()`

### 2.7 v108_atom_event_generator.TARGET_ATOMS

```python
TARGET_ATOMS = [  # 25 atom (WLD.artless は reserved_label="wld_artless_pending")
    "BOD.ear", "COG.learn", "COM.silence", "EXS.being", "EXS.nonbeing",
    "FND.timeless", "FND.transformation", "PER.feel", "PER.fragrance", "PER.hear",
    "PER.see", "PER.smell", "PER.sound", "PER.soundless", "PER.taste",
    "PRP.bright", "PRP.deep", "PRP.sharp", "SOC.city", "SOC.nation",
    "SOC.public", "TIM.appear", "WLD.artless", "WLD.culture", "WLD.technique",
]
RESERVED_ATOM = "WLD.artless"
```

---

## 3. Phase 1 実装詳細 (v10.0 - v10.5)

### 3.1 v10.0 — フェイズ宣言

実装機構なし。4 層アーキテクチャ + 死の二階層 + 燃料概念 (Q/C) を概念整理。

### 3.2 v10.1 — Minimal Ingestion (CidSelfBuffer + Unity Metrics)

**主要モジュール** (`developmental/v101/`):

| ファイル | 役割 |
|---|---|
| `v101_cid_self_buffer.py` | v9.18 CidSelfBuffer を v18_* 系 15 フィールドで拡張 |
| `v101_orchestrator.py` | per-step で全 hosted cid の v18_* を更新、window/final snapshot CSV 出力 |
| `v101_unity_metrics.py` | V_unified = mean(exp(iθ)) を計算、4 指標 (direction/concentration/shift/k) |
| `v101_theta_distance.py` | 生誕時 θ 分布からの L2 距離と coverage_ratio |
| `v101_memory_readout.py` | SubjectLayer クラス、cid 存在/認知状態を subject space 上でベクトル化 |
| `v101_fetch_operations.py` | fetch 時の操作 wrapper |

**dataclass**:

```python
CidSelfBuffer:
    v18_birth_v_unified: complex
    v18_cumulative_cognitive_gain: int
    v18_unity_direction: float
    v18_unity_concentration: float
    v18_unity_direction_shift: float
    v18_unity_k: int
    v18_theta_distance_from_birth: float
    v18_finalized_at_step: int
    v18_finalized_reason: str  # "ghost" | "tracking_end"
```

**主要関数**:
- `v918_update_per_step()`: 毎 step、self_buffers 内全 cid の v18_* を更新
- `v918_snapshot_window()`: window 末に accumulator に追加
- `v918_finalize_all_at_tracking_end()`: tracking 終了時の確定

**重要定数**:
- `PULSE_INTERVAL = 50`, `K_PULSE = 20`, `COLD_START_PULSES = 3`
- `INTROSPECTION_THRESHOLD_*` (social/stability/spread/familiarity): 0.1-2.0
- `ATTENTION_DECAY = 0.99`, `FAMILIARITY_DECAY = 0.998`

**入出力**:
- 入力: v917 CidSelfBuffer、engine.state.θ、v914 ledger
- 出力: `per_cid_window_v18_seed{N}.csv` (列: seed, cid_id, window, v18_*)、per_subject に 9 列追加

**実装の核心**: v9.18 段階 5 として既存観察層に「認知増加の量化」と「分布進化追跡」を追加。V_unified を複素ベクトルで表現し、生誕時と現在の複素平面位相差を tracking。read-only 観察 (run 中の分岐に使わない)。

### 3.3 v10.2 — Probabilistic Cognitive-Conscious Balance

**主要モジュール** (`developmental/v102/`):

| ファイル | 役割 |
|---|---|
| `v102_cid_self_buffer.py` | v101 と同一 |
| `v102_orchestrator.py` | v101 と同一 schema、probabilistic balance hook 追加 |
| `v102_memory_readout.py` | v101 と同一 |
| `v102_detailed_analysis.py` | 詳細解析 (n_core 別層化) post-process |
| `v102_scale_analysis.py`, `v102_scale_compare.py`, `v102_scale_*_analysis.py` x4 | スケール検証・比較分析 (post-process) |
| `v102_v103_category_freq.py` | v103 準備用カテゴリ頻度分析 |

**主要関数** (v10.2 で実装された機構、本体は v9.18 base):
- `decide_balance(Q, C)`: `P(認知) = Q / (Q + C)` で確率分岐
- 認知ブランチ: Q-1 + C+1 + virtual_attention/familiarity 更新
- 意識ブランチ: C-1 + 即時摂食発動 (attempt_ingestion)

**重要定数**: v101 と同じ + 確率分岐は閾値なし (Q/C 比率のみ)

**入出力**:
- 入力: v101 base + balance_decisions per-step ログ
- 出力: `balance_decisions_seed{N}.csv` (列: step, observer_cid, decision, Q_at_decision, C_at_decision), per_subject に C 関連列追加

**実装の核心**: 認知/意識を Q/C 比率で確率切替。即時摂食 (案 B、step 内動的連鎖) により先行 cid が ghost を食べきって後続 cid の候補集合が動的変化、phantom と空摂食が完全消失。C 上限なしでも暴走しない自己均衡。

### 3.4 v10.3 — Bidirectional E3 + ObservationTarget 動的追跡

**主要モジュール** (`developmental/v103/`):

| ファイル | 役割 |
|---|---|
| `v103_observation_target.py` | 3 段階追跡 Tracker class |
| `v103_be3_postprocess.py` | bidirectional_e3_log から triad (closed/open) 検出、post-process |
| `v103_spend_audit_ledger.py` | v10.3 拡張 (be3 detected pair に C-1 実行、shadow_audit 対応) — 57KB |
| (他は v102 から継承) | |

**class**:

```python
ObservationTargetTracker:
    target_ids: Set[int]
    added_at_step: Dict[int, int]  # cid -> step
    added_via: Dict[int, str]      # cid -> "stage1" | "stage2" | "stage3"
    
    def stage1_check(cid, n_core, n_consciousness, step) -> bool:
        # n_core >= 4 ∧ n_consciousness >= 5
    def stage2_propagate(cid_a, cid_b, step) -> (bool, bool):
        # be3 paired cid を追加
    def stage3_propagate(cid_c, step):
        # post-process 第三項
```

**主要関数**:
- `detect_triads_per_window()`: be3_df を window 単位で走査、closed/open triad 検出、per_pair_flags + window_stats 返却

**重要定数**:
- `N_CORE_THRESHOLD = 4`, `N_CONSCIOUSNESS_THRESHOLD = 5`
- Bidirectional E3 条件: hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触

**入出力**:
- 入力: e3_pairs (v914 event emitter)、observation_target 条件
- 出力: `bidirectional_e3_log` (fired/skip_reason フラグ付き)、`v103_be3_3rd_cid_log_seed{N}.csv` (closed/open/proximate triads)、per_window に triad counts 追加

**実装の核心**: 動的観察対象追跡。Stage 1 で主役選定 → Stage 2 で相互作用パートナー → Stage 3 で post-process 第三項。並行して bidirectional E3 検出・記録、両者 C-1 消費。三層分離 (機構 vs 観察 vs 解釈) を確立。

### 3.5 v10.4 — Integration 機構 (単層、Q/C 継承 + 再分配)

**主要モジュール** (`developmental/v104/`):

| ファイル | 役割 |
|---|---|
| `v104_integration.py` | Integration dataclass + IntegrationManager (誕生・ghost時継承・window末再分配) — 25KB |
| `v104_be3_postprocess.py` | v103 と同一 |
| `v104_observation_target.py` | Stage 4 追加 (integration 構成 cid を target に) |
| `v104_shadow_audit.py`, `v104_smoke.py` | dry-run / smoke test |
| `v104_spend_audit_ledger.py` | v10.4 拡張 (integration の Q/C 継承・再分配ログ) — 58KB |

**dataclass**:

```python
@dataclass
class Integration:
    integration_id: int
    birth_step: int
    trigger_type: str  # "be3" | "open_triad" | "closed_triad" | "third_overlap"
    state: str         # "active" | "recorded"
    member_cids: set[int]
    member_history: set[int]
    Q_inherited: int  # ghost cid から継承
    C_inherited: int
    binding_strengths: dict[int, float]  # cid -> event 参加回数
    became_recorded_step: int | None

class IntegrationManager:
    integrations: dict[int, Integration]
    cid_to_integrations: dict[int, set[int]]
    _active_members_index: dict[frozenset[int], int]  # 重複判定高速化
    lifecycle_log: list
    distribution_log: list
```

**主要関数**:
- `on_be3_fired()`: be3 直後、Trigger A/B/C/D 判定 → `_maybe_birth()`
- `_maybe_birth()`: 同 members の active Integration 重複チェック、新規誕生 or binding 更新
- `on_ghost()`: cid 削除時、member 除外 → Q/C 継承 (最強結合 1 個から 100%、二重カウント回避)、recorded 遷移判定
- `redistribute_q_c_window_end()`: window 末、active integration に Q/C 再分配 (状態依存逆張り)

**重要定数**:
- Trigger 誕生条件: be3 (A) / open_triad (B) / closed_triad (C) / third_overlap (D)
- Q/C 継承: 最強結合 1 個のみ
- Recorded 永続化

**入出力**:
- 入力: be3 fired (cog, ledger)、cid ghost 化通知
- 出力: `integration_lifecycle_log`、`integration_distribution_log` (per step/window)、per_subject に integration 関連列追加

**実装の核心**: cid 集団の「第二次生物」としての Integration を実装。誕生・成長・recorded 化の lifecycle、ghost 化時 Q/C 継承、window 末再分配。物理層 frozen、認知/意識層への間接バイアスのみ。ハブ cid (1 cid 所属 max 102) が自然形成、ダブルブッキング問題が表面化。

### 3.6 v10.5 — α/β Integration 二層化 + Salience + Leakage (Layer 5 完成)

**主要モジュール** (`developmental/v105/`):

| ファイル | 役割 |
|---|---|
| `v105_integration.py` | AlphaIntegration + AlphaIntegrationManager + BetaIntegration + BetaIntegrationManager — 43KB |
| `v105_salience.py` | mass-weighted selection (read_other 解像度、be3 fire log、ingestion target) — 13KB |
| `v105_historical_leakage.py` | recorded β からの C leakage (ε=1、be3/ingestion trigger) — 5.2KB |
| `v105_shadow_audit.py`, `v105_smoke.py` | dry-run / smoke test |
| `v105_spend_audit_ledger.py` | v104 + α/β lifecycle/distribution log 統合 — 60KB |
| `v105_animate_*.py` x4 | 可視化スクリプト (post-process) |

**dataclass**:

```python
@dataclass
class AlphaIntegration:  # 観察軸、Q/C 削除
    alpha_id: int
    member_cids: set[int]
    member_history: set[int]
    binding_strengths: dict[int, float]
    state: str  # "active" | "recorded"
    birth_step: int
    trigger_type: str

@dataclass
class BetaIntegration:  # 会計単位、α 群の統合
    beta_id: int
    member_alphas: set[int]
    member_alphas_history: set[int]
    member_cids: set[int]
    member_cids_history: set[int]
    Q_inherited: int
    C_inherited: int
    cid_original_binding: dict[int, float]  # recorded β 漏れ参照
    state: str

class SalienceTracker:
    event_log: list[dict]
    cid_n_observed_as_target: dict[int, int]
    selected_as_target: dict[int, int]
    cid_total_observed_mass: dict[int, float]

class LeakageTracker:
    event_log: list[dict]
    cid_total_leakage_received: dict[int, int]
```

**主要関数**:
- `AlphaIntegrationManager.on_be3_fired()`: Trigger A-D 判定 → `_maybe_birth()`
- `AlphaIntegrationManager.on_ghost()`: cid 削除 → α member 除外 → β へ通知 (callback) → recorded 遷移
- `BetaIntegrationManager._on_alpha_changed()`: α 誕生・member 削除時、Union-Find で β 統合判定 (共有 cid ≥ 2)
- `compute_mass(X)`: `X.Q + X.C + sum(β.Q_inherited + β.C_inherited for β in X が所属する β)`
- `trigger_leakage_be3()`: be3 fired → 相手の recorded β から C-1 漏れ (双方向)
- `trigger_leakage_ingestion()`: ingestion → ghost Y の recorded β から C-1 漏れ

**重要定数**:
- `BETA_MERGE_MIN_SHARED_CIDS = 2`
- `SALIENCE_READOTHER_STRENGTH = 0.5`, `SALIENCE_INGESTION_MASS_COEF = 1.0`
- `LEAKAGE_AMOUNT = 1` (ε=1)
- Recorded 状態は永続 (active → recorded のみ)

**入出力**:
- 入力: be3 fired、cid ghost、ingestion target selection
- 出力 (diag_v105_main_v2 ディレクトリ): `alpha_lifecycle_log`, `beta_lifecycle_log`, `alpha_membership_snapshot`, `beta_distribution_log`, `salience_event_log`, `leakage_event_log`, per_subject に α/β 関連列追加

**実装の核心**: Layer 5 完成。α (観察軸、複数所属許容、Q/C 廃止) と β (会計単位、cid 単一所属、Q/C 継承先) の二層化でダブルブッキングを構造的解消。Salience (mass-weighted) と Leakage (ε=1) を実装、Phase 1 完成。

---

## 4. Phase 1.5 実装詳細 (v10.6 - v10.13.a)

### 4.1 v10.6 — Atom Alignment Observer

**主要モジュール** (`developmental/v106/`):

| ファイル | 役割 |
|---|---|
| `v106_post_process.py` | cid × atom cosine 類似度計算 (メイン) |
| `v106_atom_match_classification.py` | 26 atom 構造的特異性検出、z-score 分析 |
| `v106_step10_baseline.py` | 10 step 単位の atom 特性集計 |
| `v106_event_trajectory.py` | per-event atom alignment の時間推移 |
| `v106_pulse_trajectory.py` | pulse 起点の atom 反応パターン |

**データ構造**:

```python
# cid_vector: np.ndarray[48]  (10 axes × 48 levels)
# atom_profile: dict[str, float]  # Atom ID → semantic_centroid vector
# sim_score: float = cosine(cid_vector, atom_profile)

# cid_atom_sim_matrix.parquet schema:
# columns: [cid:int, BOD.ear:float, COG.learn:float, ..., WLD.technique:float]
# shape: (5224 cids, 326 atoms)
```

**主要関数**:
- `build_cid_atom_vectors(seed)`: 48 次元ベクトル構築
- `compute_cosine_similarity(cid_vectors, atom_profiles)`: cosine 類似度
- `compute_z_scores_per_atom(sim_matrix)`: atom 別 z-score
- `classify_structural_atoms(z_scores, threshold=0.01)`: |delta_ratio| > 1% で構造的特異性判定

**重要定数**:
- `WIN_LEN = 500`, `RUN_END_STEP = 25000`, `SEEDS = list(range(24))`
- `TARGET_ATOMS` (25 atom): §2.7 参照

**入出力**:
- 入力: v10.5 diag_v105_main_v2 全層
- 出力: `outputs/main/cid_atom_sim_matrix_seed{N}.parquet` (5,224 × 326)、`step10_atom_z_score.csv`、`atom_trajectory_per_event.parquet`、`atom_trajectory_pulse.parquet`

**実装の核心**: 各 cid を 10 axes × 48 levels の 48 次元ベクトルに写像し、Language 層 Atom (semantic centroid) との cosine 類似度を計算。326 atom 中 25 atom が構造的特異性 (δ > 1% × 9 + z-score ∞ × 17) を示すことを発見、WLD.artless は z-score = ∞ で留保扱い。以降 v10.7-v10.12 で atom_introduction_event の対象として固定。

### 4.2 v10.7 — Post-process オービス (5 機構)

**主要モジュール** (`developmental/v107/`):

| ファイル | 役割 |
|---|---|
| `v107_event_aggregator.py` | 5 種 source_event 統合 + `attach_pre_event_state` |
| `v107_path_analyzer.py` | 5 種 relation_path 構築 (1-hop) |
| `v107_baseline_constructor.py` | 5 種 baseline + delta 計算 + excess_change 集計 |
| `v107_avalanche_monitor.py` | multi-hop path / peak_lag / loop detection |
| `v107_post_process.py` | Orchestrator (Step C-G) + bit-identity 検証 |
| `v107_cross_seed_analyzer.py` | 24 seeds 統合集計 |

**dataclass**:

```python
@dataclass
class SourceEvent:
    event_id: str                  # f"{seed}_{source_type}_{idx}"
    event_source_type: str         # 5 種のいずれか
    source_cid: int
    timestamp: int                 # [0, 25000]
    Q_pre: float                   # merge_asof backward fill
    C_pre: float
    n_observed: int
    lifespan_so_far: int
    birth_step: int

@dataclass
class RelationPath:
    event_id: str
    source_cid: int
    timestamp: int
    target_cid: int
    relation_path_type: str
    relation_strength: float
    hop_distance: int = 1
```

**5 種 source_event** (per seed):

| Type | 数 | 出所 |
|---|---:|---|
| pulse | ~12,530 | pulse_log の各 cid t |
| ingestion | ~155 | ingestion_events observer_cid |
| alpha_formation | ~424 | alpha_lifecycle_log birth + member_cids 展開 |
| beta_formation | ~239 | beta_lifecycle_log birth + member_cids 展開 |
| c_conversion | ~155 | balance_decisions decision='consciousness' |

**主要関数**: §2.1-2.5 参照

**重要定数**:
- `WINDOW_DEFS = [("immediate", 1, 10), ("short", 10, 100), ("medium", 100, 1000)]`
- `TOP_N_PER_BASELINE = 20`
- `TEMPORAL_LAG_BACKWARD/FORWARD = 100`
- `FAM_LOW_THRESHOLD = 5.0`

**入出力**:
- 入力: diag_v105_main_v2/ + v10.6 cid_atom_sim_matrix
- 出力 (per seed): `source_events.parquet` (~13,500 rows), `relation_paths.parquet`, `baselines_with_delta.parquet`, `excess_change.parquet` (415K rows × 24 seeds), `peak_lag_analyses.parquet`, `wave_classification.parquet`

**実装の核心**: 5 種 source_event を統合 + pre_event_state 添付 + 5 種 relation_path 構築 + 5 種 baseline 構築 + 6 量 × 3 window delta 計算 + event × path 別 mean_delta 集計。Level 1-3 因果候補抽出基盤 (オービス) を完成。medium window (100-1000 step) で因果候補が最も多く検出される、temporal_coactivation > Integration > familiarity > attention の path 順位を確立。

### 4.3 v10.8 — atom_introduction_event 機構 (Level 3.5)

**主要モジュール** (`developmental/v108/`):

| ファイル | 役割 |
|---|---|
| `v108_atom_event_generator.py` | 25 atom × top_k cid × 均等分散発火で 60K 生成 |
| `v108_global_activation_correction.py` | global_activation_factor (natural のみ) + adjusted_excess |
| `v108_baseline_recalculator.py` | 各条件別 baseline 再計算 |
| `v108_post_process.py` | v10.7 パイプライン + atom_intro orchestrator |
| `v108_cross_seed_analyzer.py` | 24 seeds 統合集計 |
| `v108_subsidiary_observations.py` | atom 別 effect / timing axis 等 |

**dataclass**:

```python
@dataclass
class AtomIntroductionEvent:
    event_id: str                  # f"{seed}_atom_{idx}"
    event_source_type: str = "atom_introduction_event"
    source_cid: int
    timestamp: int                 # [100, 24850] 均等分散
    atom_id: str                   # 25 atom のいずれか
    atom_index: int                # [0, 24]
    top_k_rank: int                # [1, 100]
    atom_sim_score: float
    reserved_label: str            # "wld_artless_pending" if atom_id == WLD.artless
    # v10.7 attach_pre_event_state 由来
    Q_pre, C_pre, R_familiarity_pre, lifespan_so_far, birth_step, ...
    # v10.8 計算的減算
    Q_after_atom_intro: float      # = Q_pre - 1
    C_after_atom_intro: float      # = C_pre + 1
```

**主要関数**:
- `extract_top_k_cids(seed, atoms, top_k=100)`: atom 別 top_k cid 抽出
- `schedule_atom_event_timestamps(atom_index, n_events=100)`: 均等分散 timestamp (atom_index × 10 offset)
- `generate_atom_events(seed, top_k_df)`: 60K events 生成
- `attach_atom_event_states(df, seed)`: pre + post state 添付
- `compute_global_activation_factor(seed)`: §2.6 参照
- `add_adjusted_excess(df_excess, df_src, df_factor)`: §2.6 参照
- `compute_natural_baseline_diff(df_excess_v108, seed)`: Level 3.5 判定基盤 (v10.7 natural との比較)

**重要定数**:
- `TARGET_ATOMS` (25, §2.7), `TOP_K = 100`, `EVENTS_PER_ATOM = 100`
- `ATOM_INDEX_STEP_OFFSET = 10` (atom_index × 10 step ずらし)
- `ATOM_INTRO_Q_COST = 1`, `ATOM_INTRO_C_GAIN = 1`
- `STEP_BIN_SIZE = 100` (global_activation_factor bin 幅)

**計算規模**: 25 atom × 100 cid × 24 seeds = **60,000 atom_intro_events**、合計 384K events (natural 324K + atom 60K)

**timestamp 均等分散ロジック**:
```python
base_offset = 100 + (atom_index * 10)
interval = (RUN_END_STEP - base_offset) // 100  # ≈ 248 step
# atom_index=0: [100, 348, 596, ..., 24848]
# atom_index=1: [110, 358, ...]  (10 step ずらし)
```

**入出力**:
- 入力: v10.6 sim_matrix (top_k 抽出)、diag_v105 (pre_event_state)、v10.7 出力 (natural baseline)
- 出力: `atom_introduction_events_seed{N}.parquet` (2,500/seed)、`global_activation_factor_seed{N}.parquet`, `excess_change_adjusted_seed{N}.parquet`, `natural_baseline_diff_seed{N}.parquet`

**実装の核心**: atom_introduction_event を source_event 第 6 種として追加、cid_atom_sim_matrix top_k 100 × 25 atom = 2,500 events/seed を均等分散発火。Q-1/C+1 を post-process 計算的減算 (実 ledger 不変)。global_activation_factor (natural のみ) で global 影響を補正、Level 3.5 で「introduced < natural、atom event は natural の半分」を発見。familiarity 経路 effect_size 6.83、temporal_coactivation 0.03 で機能分担を実証。

### 4.4 v10.9 — 寄与候補感度評価 + bimodal 構造解析

**主要モジュール** (`developmental/v109/`):

| ファイル | 役割 |
|---|---|
| `v109_atom_event_generator.py` | A2/B3/C2 の 3 新条件 atom_intro_event 生成 |
| `v109_baseline_recalculator.py` | 各条件 v107 ロジックで baseline 再計算、condition_id 列付与 |
| `v109_bimodal_analyzer.py` | v108 bimodal セル 1,540 件に KDE/find_peaks、3 仮説 (H1: n_core / H2: integration / H3: lifecycle age) 効果量評価 |
| `v109_design_table_compiler.py` | 4 種設計表 + 4 階層レポート + 構造的統合解析 |
| `v109_sensitivity_evaluator.py` | A1 vs A2/B3/C2 で path × window × metric 別 cohens_d |
| `v109_post_process.py` | Orchestrator (Step C/D/H/I) + 3 層 bit-identity |

**3 新条件 (CONDITIONS)**:

```python
CONDITIONS = {
    "A2": {"Q_cost": 2, "C_gain": 2, "cid_selection": "top_k_100", "timing": "uniform_atom_offset"},
    "B3": {"Q_cost": 1, "C_gain": 1, "cid_selection": "random_100", "timing": "uniform_atom_offset"},
    "C2": {"Q_cost": 1, "C_gain": 1, "cid_selection": "top_k_100", "timing": "lifecycle_synced", "age_target": 200},
}

COMPARISONS = {
    "QC_cost": {"a": "A1", "b": "A2"},
    "cid_selection": {"a": "A1", "b": "B3"},
    "timing": {"a": "A1", "b": "C2"},
}
```

**重要定数**:
- `SEEDS = list(range(24))`
- `TOP_K = 100`, `AGE_TARGET = 200` (C2)
- `B3_RNG_SEED_OFFSET = 1_090_000_300`
- `WINDOWS = ["immediate", "short", "medium"]`
- `DELTA_METRICS = 6` 種, `ALL_PATHS = 10` 種 (5 paths + 5 baselines)
- bimodal: `EFFECT_SIZE_THRESHOLD = 0.3`, `KDE_PROMINENCE_FRAC = 0.05`

**入出力**:
- 入力: v10.8 出力 (atom_events, deltas, excess), v10.5 diag
- 出力: 各条件 × seed の `atom_introduction_events_{cond}_seed{N}.parquet` 等 + `bimodal_analysis_seed{N}.parquet` + `sensitivity_evaluation_seed{N}.parquet` + cross_seed/ (design_table_1-4、level reports)

**実装の核心**: 3 新条件 (A2 Q/C コスト変動 / B3 random cid / C2 age=200 timing 同調) で寄与候補感度評価。bimodal 1,540 cells に KDE+find_peaks で 2 ピーク抽出 + 3 仮説評価、H3_lifecycle が 60.2% で dominant → 「強反応する cid は若い (age median 227)」を発見。high_fam_outside_integ 経路が timing 感度 0.222 で最強と判明。4 種設計表で v10.10 用素材セット完成。

### 4.5 v10.10 — Multi-gate × timing 28 conditions + 5 軸層化

**主要モジュール** (`developmental/v110/`):

| ファイル | 役割 |
|---|---|
| `v110_atom_event_generator.py` | 9 GATES × 3 AGE_TARGETS = 28 条件 atom events、`is_receptive` 関数 |
| `v110_baseline_recalculator.py` | 28 条件 × 24 seeds 並列 baseline 再計算 |
| `v110_sensitivity_evaluator.py` | gate / v110 vs v108re / timing の 3 種比較で cohens_d |
| `v110_multi_axis_stratified_analyzer.py` | 5 軸並列観察 (A/B/C/E/F) |
| `v110_n_core_stratified_analyzer.py` | n_core 別深掘り集計 |
| `v110_round2_analyzer.py` | 追加分析 |
| `v110_design_table_compiler.py` | 28 条件 5 軸結果整理 |
| `v110_post_process.py` | Orchestrator + 3 層 bit-identity |

**CONDITIONS (28 種 = 9 GATES × 3 AGE_TARGETS + v108_re)**:

```python
GATES = ["ABC", "ABc", "AB", "B", "Bc", "AC", "BC", "A", "all_pass"]
AGE_TARGETS = [200, 300, 500]
AGE_UPPER_LIMIT = 560

CONDITIONS = {f"v110_{g}_t{at}": {...} for g in GATES for at in AGE_TARGETS}
CONDITIONS["v108_re"] = {...}  # bit-identity 用 (v10.8 再現)
```

**is_receptive 関数** (各 cid × event timestamp で gate 判定):

```python
def is_receptive(gate, age_target, t_event, in_integ, fam_v, p75, p50) -> bool:
    age_ok = (age_target <= AGE_UPPER_LIMIT)          # 560 step まで
    out_integ = not in_integ                          # 当該 timestamp で α/β 非所属
    fam_C = (fam_v >= p75)                            # familiarity top 25%
    fam_c = (fam_v >= p50)                            # familiarity top 50%
    if gate == "ABC": return age_ok and out_integ and fam_C
    if gate == "ABc": return age_ok and out_integ and fam_c
    if gate == "AB":  return age_ok and out_integ
    if gate == "B":   return out_integ
    if gate == "AC":  return age_ok and fam_C
    if gate == "BC":  return out_integ and fam_C
    if gate == "Bc":  return out_integ and fam_c
    if gate == "A":   return age_ok
    if gate == "all_pass": return True
```

**COMPARISONS (42 種)**: gate_effect (8 × 3 = 24) + v110_vs_v108re (9) + timing_axis (9)

**5 軸層化** (`v110_multi_axis_stratified_analyzer.py`):

| 軸 | 内容 |
|---|---|
| A: Integration α/β 4 層化 | only_alpha / only_beta / both / none |
| B: cid 寿命 Q1-Q4 分位 + n_core 交差 | lifespan_q + n_core_bin |
| C: 25 atom 個別 + category | per-atom + COG/PER/EXS/SOC etc. |
| E: window × n_core_bin | imm/short/med × bin_2/3_4/5+ |
| F: seed 別 ばらつき + tied 内訳 | per seed direction consistency |

**重要定数**: §2 共通 + 上記 GATES/AGE_TARGETS

**入出力**:
- 入力: v10.5 diag、v10.8 atom_events
- 出力: 各 condition × seed の `atom_introduction_events_{cond}_seed{N}.parquet`, `baselines_with_delta_{cond}_seed{N}.parquet`, `excess_change_adjusted_{cond}_seed{N}.parquet`, `sensitivity_evaluation_seed{N}.parquet` + cross_seed/ 5 軸結果

**v108_re** (層 B bit-identity 用): `developmental/v110/v108_re/outputs/{smoke,main}/` 下に v10.8 を再実行した出力を保持

**実装の核心**: v10.9 の 4 種設計表を統合し、9 gates × 3 age_targets の 28 conditions で Multi-gate × timing 二次元探索。`is_receptive` で event timestamp 別に cid の receptive 判定 (integration lifecycle log を時間関数化)。5 軸層化解析で構造的差異・lifecycle 依存・原子操作性・density 効果・確率的安定性を多面評価。**長寿 cid (Q4) で timing_axis -0.196 / v110_vs_v108re +0.214 と効果大**、**n_core 別反応 type 分業** (bin_2 = pulse 系 / bin_5+ = delta_C 系) を発見。

### 4.6 v10.11 — q_c_inherited 起点 within-cid 観察

**主要モジュール** (`developmental/v111/`):

| ファイル | 役割 |
|---|---|
| `v111_q_c_inherited_observer.py` | beta_lifecycle_log から q_c_inherited events 抽出、member cid の T-50 vs T+50 を 21 snapshot (5 step 刻み) で追跡 |
| `v111_response_profile_compiler.py` | 24 seeds profile 集計、within-cid delta、4 段階方向一致観察、routing_conditions 抽出 |

**データ構造**:

```python
T_OFFSETS = list(range(-50, 51, 5))  # [-50, -45, ..., +45, +50] (21 samples)

# q_c_inherited_response_profile schema:
# event_id, beta_id, cid, T (event_step), t_offset, t_obs,
# C_value, pulse_count, n_core, n_core_bin (3 layer),
# cumulative_c_before, c_q_partition (4 layer Q1-Q4), c_inherited_delta, seed

# within_cid_delta schema (compiler 出力):
# seed, event_id, cid, n_core_bin, c_q_partition, T, beta_id,
# cumulative_c_before, n_core,
# C_at_minus_50, C_at_plus_50, delta_C_within,
# pulse_at_minus_50, pulse_at_plus_50, delta_pulse_within
```

**重要定数**:
- `SEEDS = list(range(24))`
- `T_OFFSETS` (21 samples, 5 step 刻み)
- `N_CORE_BINS = ["bin_2", "bin_3_4", "bin_5plus"]`
- `C_Q_PARTITIONS = ["Q1", "Q2", "Q3", "Q4"]` (β 累積 c_inherited 分位: <3 / 3-6 / 6-9 / ≥10)

**入出力**:
- 入力: `beta_lifecycle_log_seed{N}.csv` (v105)、`balance_decisions_seed{N}.csv`、`pulse_log_seed{N}.csv`
- 出力: `q_c_inherited_events_seed{N}.parquet`, `q_c_inherited_response_profile_seed{N}.parquet`、cross_seed/ (within_cid_delta_summary / direction_consistency / level reports / routing_conditions)

**4 段階方向一致**: `complete_consistent` (全 24 seed 同方向) / `majority_consistent` / `majority_zero` / `tied`

**実装の核心**: 「event 発生 → 全 cid effect_size」から「特定 event → 影響 cid 個別プロファイル」へシフト (within-cid design)。β の q_c_inherited event 前後 (T-50 vs T+50) で member cid の C 値 / pulse activity を 21 snapshot で追跡、n_core × c_q_partition の 12 cell で 24 seeds 方向一致度を評価。**結果は v10.5 機構 A (β に Q/C 100% 継承) の既知挙動の再観察に過ぎなかった** (留保 21、v10.11 完了レポート §5 で記録)。Aruism「予想と違えば再観察」を §5.2 末尾で確立。

### 4.7 v10.12 — Atom 取り込み prototype (現在地、完了)

**主要モジュール** (`developmental/v112/`):

| ファイル | 役割 | 行数 |
|---|---|---:|
| `v112_step_z_environment_check.py` | 事前調査 (Q-Z1〜Q-Z7、4 条件母集団 / Q3=977 / fam top 25% / formation_relation / v108 pool overlap / 規模見積) | - |
| `v112_step_z_n_core_addendum.py` | Step Z n_core 別補完調査 | - |
| `v112_step_b_environment_check.py` | 環境チェック詳細 (trial-A 単独、Step Z 反映) | - |
| `v112_receptive_cid_detector.py` | Step C: 4 条件複合 cid 検出 (cond1-4) | 261 |
| `v112_atom_event_generator.py` | Step D: 25 atom × cid burst (10,500 events) | 309 |
| `v112_baseline_recalculator.py` | Step E1: baseline 計算 (v107 共通基盤利用) | 215 |
| `v112_propagation_analyzer.py` | Step E2: per-event 波及プロファイル (delta_C/Q/n_pulses + 4 path_excess) | 235 |
| `v112_observation_recorder.py` | Step F: 観察事実 + 層化 + cohens_d + 予想 + 留保の網羅記録 | 391 |
| `v112_orchestrator.py` | Step G/I: Step D-F 順次実行 + bit-identity 全層検証 | 297 |
| `v112_cross_seed_analyzer.py` | Step J: paired_d / sign_test / bootstrap CI / 留保 #27 formal | 274 |
| `v112_window_post_process.py` | 追加調査: window 単位 post-process (3 window × 7 metric の 21 paired analyses) | ~310 |

**4 条件 cid 検出** (Step C):

```python
Q3_THRESHOLD = 977             # Step Z 実測、v10.10 §3.2 整合
N_CORE_THRESHOLD = 5           # cond3
DEFAULT_AGE_TARGET = 200       # target_step = cid.birth + 200
DEFAULT_FAM_PERCENTILE = 50    # cond4 top 50% (median)、第 5 版主題

def detect_v112_receptive_cids(seed, fam_threshold):
    # cond1: not is_beta_member_at(cid, target_step, intervals)
    # cond2: row["lifespan"] >= Q3_THRESHOLD
    # cond3: row["n_core"] >= N_CORE_THRESHOLD
    # cond4: row["fam_max"] >= fam_threshold (per-seed top 50%)
    # all and → receptive cid

def classify_n_core_bin(n_core):
    if n_core == 2: return "bin_2"
    if 3 <= n_core <= 4: return "bin_3_4"
    if n_core >= 5: return "bin_5_plus"

def classify_formation_relation(cid, target_step, intervals):
    # "before" | "during" | "after" | "no_alpha"
```

**atom event 生成** (Step D):

```python
ATOM_INDEX_STEP_OFFSET = 10
Q_COST = 1
C_GAIN = 1

# Per cid:
#   for atom_idx, atom_id in enumerate(TARGET_ATOMS):
#     t_event = target_step + atom_idx * ATOM_INDEX_STEP_OFFSET
#     event を 25 atom 分生成 (target_step burst)
# v112: 420 cid × 25 atom = 10,500 events (24 seeds total)
# v108_standard: v110/v108_re/outputs/main/ 既存出力流用 (層 B 不変)
```

**propagation profile** (Step E2):

```python
PROFILE_PATHS = ["familiarity", "attention_via_salience",
                 "temporal_coactivation", "integration_alpha"]
EXCESS_REFERENCE = "unrelated_baseline"

# per-event 列:
# delta_C_medium, delta_Q_medium, n_pulses_short (relation paths 5 種の mean)
# path_X_excess_delta_C_medium = path X delta_C - unrelated_baseline delta_C  (for X in PROFILE_PATHS)
# raw_{path}_delta_C_medium (検査用)
# + Step C metadata (n_core_bin, formation_relation 等)
```

**paired_d / sign_test / bootstrap CI** (Step J):

```python
BOOTSTRAP_N = 1000
RANDOM_SEED = 12112

def paired_analysis(diff_per_seed, metric):
    paired_d = mean_diff / std_diff  # Cohen's d (paired)
    sign_p = scipy.stats.binomtest(n_positive, n_nonzero, p=0.5, alternative="two-sided")
    # bootstrap: rng.choice with replacement, 1000 iter
    ci_lower, ci_upper = np.percentile(boot_means, [2.5, 97.5])
```

**入出力**:
- 入力: v10.5 diag, v10.6 sim_matrix, v110 v108_re 既存出力
- 出力 (per seed × 2 conditions): atom_intro / baselines_with_delta / excess_change_adjusted / propagation_profile + observation_records / cross_seed_analysis / window_post_process

**実装の核心**: 4 条件 (¬β + lifespan ≥ 977 + n_core ≥ 5 + fam ≥ top 50%) の受容 cid pool 420 個に対し 25 atom × cid burst (target_step + atom_idx × 10) で 10,500 events 生成、v108_standard (top_k_100 unique 5,111 cid) と比較。Step Z → J → K の 10 段階 commit chain で物理層 frozen + 層 B 443 files unchanged + bit-identity 全層 PASS を維持。観察結果: **n_pulses_short のみ paired_d +1.36 で頑健 v112 > v108、他 6 metric は方向性なし、smoke seed 0 と main 24 seeds で 4/7 metric 符号反転 (Aruism 発動)**。追加調査で **immediate (1-10 step) delta_C 頑健 + n_pulses window 依存方向反転** を発見。留保累計 27 件。

### 4.8 v10.13.a — reaction phase 5 段階の整備 (post-process、v10.13 a/b/c 順次運用初回)

**主要モジュール** (`developmental/v113a/`):

| ファイル | 役割 | 行数 |
|---|---|---:|
| `v113a_step_b_environment.py` | 環境チェック + 層 B baseline 記録 (~3,243 files mtime+size snapshot) | - |
| `v113a_maps_analyzer.py` | Map 1-4 算出 (phase × n_core / path / formation / event 種別) | ~330 |
| `v113a_null_phase_analyzer.py` | Map 5 cell-based null absorption (案 X-1) | ~280 |
| `v113a_long_phase_compute.py` | long phase (1000-25000 step) 算出、v107 WINDOW_DEFS monkey-patch | ~180 |
| `v113a_bit_identity_check.py` | 層 A/B/C 検証 | - |

**5 phase 定義** (Taka 整理 2026-05-11「時間軸 = 波及深度」起点):

```python
PHASE_DEFS = [
    ("immediate", 1, 10),     # Phase 1: Immediate Disturbance (反射 A-B)、v107 immediate
    ("short", 10, 100),       # Phase 2: Short Circulation (器官循環 A-B-C)、v107 short
    ("mid", 100, 1000),       # Phase 3: Mid Integration (脳循環 A-B-C-D)、v107 medium 改名
    ("long", 1000, 25000),    # Phase 4: Long Conditioning (長期記憶 A-B-C-D-E)、新規 monkey-patch
]
# Phase 5: Null Absorption は phase 横断、cell-based 判定 (path 5 種全 CI 0 跨ぎ + 過半数 seeds で delta_C 動く + n>=3)
```

**dataclass 不在 (post-process のみ、parquet スキーマで表現)**

**Map 1-5 schema**:

Map 1 (phase × n_core_bin):
```
seed, condition (v112/v108_standard), phase, n_core_bin (bin_2/3_4/5_plus),
n_events, delta_C_mean, delta_C_std, delta_Q_mean, n_pulses_mean, n_pulses_std
cross_seed: + paired_diff_mean, paired_diff_std, paired_d, sign_test, bootstrap CI 95%, crosses_zero
```

Map 2 (phase × relation_path × path_category):
```
seed, condition, phase,
path_category (atom_related/layer5_structural/baseline),
path_name (5 paths + 5 baselines),
n_events, path_excess_mean, path_excess_std, path_delta_C_mean
```

Map 3 (phase × formation_relation):
```
seed, condition, phase, formation_relation (before/during/after/no_alpha),
n_events, delta_C_mean, delta_C_std, n_pulses_mean, n_pulses_std
```

Map 4 (phase × event 種別、v107 source_events join):
```
seed, condition (v107_natural/v112/v108_standard), phase,
event_source_type (pulse/ingestion/alpha_formation/beta_formation/c_conversion/atom_introduction_event),
n_events, delta_C_mean, delta_C_std, n_pulses_mean
```

Map 5 (null phase、cell-based 案 X-1):
```
condition, phase, n_core_bin, atom_id, atom_category (10 種 BOD/COG/.../WLD),
n_events_in_cell, delta_C_cell_mean, delta_C_cell_std,
n_paths_with_no_signal (0-5),
n_seeds_with_signal (0-24),
cond_1_all_paths_no_signal (bool), cond_2_majority_seeds_signal (bool), cond_3_min_events (bool),
is_null_cell_candidate (3 条件全 PASS の bool)
```

**重要定数**:
- `PHASES = ["immediate", "short", "mid"]` (Map 1-5 で 3 phase 集計、long は Step H 別出力)
- `PHASE_TO_V107_WIN = {"immediate": "immediate", "short": "short", "mid": "medium"}`
- `RELATION_PATHS_ATOM = ["familiarity", "attention_via_salience", "temporal_coactivation"]`
- `RELATION_PATHS_LAYER5 = ["integration_alpha", "integration_beta"]`
- `EXCESS_REFERENCE = "unrelated_baseline"`
- `BOOTSTRAP_N = 1000`, `RANDOM_SEED = 13013`
- Null 判定: cond_2 (過半数 seeds 動く) ≥ 12、cond_3 (n_events) ≥ 3
- `TARGET_ATOMS` 25 個は v108 から継承 (§2.7)

**long phase 算出ロジック** (v107 WINDOW_DEFS monkey-patch):

```python
import v107_baseline_constructor as v107_bc
v107_bc.WINDOW_DEFS = [("long", 1000, 25000)]  # 書き換え
df_with_delta = v107_bc.compute_deltas(seed, df_targets)  # long delta のみ算出
df_excess = v107_bc.compute_baseline_excess_change(df_with_delta)
df_excess_adj = add_adjusted_excess(df_excess, df_atom, df_factor)  # v108 流用
```

**入出力**:
- 入力: v107 source_events + excess_change、v112 excess_change_adjusted + propagation_profile (主入力、Web Claude 即決事項 #3) + step_c receptive_cids (v108_standard pool filter)
- 出力 (per-seed): Map 1-5 parquet × 24 seeds × 2 conditions + cross_seed
- long phase: `excess_change_long_*.parquet` × 48 jobs + baselines_with_delta_long_*

**実装の核心**: v10.7 オービスで確立した 3 window (immediate/short/medium) を Taka 整理「時間軸 = 波及深度」を起点として 5 phase に拡張、v10.12 main run 既存出力の post-process のみで 5 Map を算出 (main run 再実行なし、層 B 3,243 files unchanged)。Map 5 (null phase) は cell-based 案 X-1 (Web Claude 即決事項 2026-05-12) で per-event CI ではなく phase × condition × n_core_bin × atom_id cell × bootstrap CI で判定 (per-event CI は v10.12 cross_seed_analyzer に不在のため構造的設計問題を回避)。long phase は v107 WINDOW_DEFS を monkey-patch で `[("long", 1000, 25000)]` に変更し compute_deltas を呼ぶ。bit-identity 全層 PASS (層 B 3,243 files unchanged、層 A deterministic、層 C 構造的)。実行時間 Step B-I 合計 57 秒、出力 61 MB。

主要観察事実 (judgment 回避、Aruism 整合):
- Map 1: n_pulses 3 phase 全頑健 v112 > v108 (paired_d +0.91-1.19、bin_5_plus 限定)、delta_C short のみ頑健 (+0.46)
- Map 2: 15 cells (3 phase × 5 path) 全て CI 0 跨ぎ、path_excess 方向性なし (v10.12 Step J 結論変わらず)
- Map 3: before formation imm/short 頑健 (paired_d +0.63/+0.42)、mid で消失
- Map 4: c_conversion = ingestion 完全同値 (留保 #32 = v10.2 即時摂食設計の物理的に同一瞬間を 2 ラベルで記録)、v112 atom phase 別 6 倍増加 (imm 0.013 → mid 0.081)
- Map 5: v112 で 36 null candidates (path 経路を経ない波及)、v108_standard で 0、PER/WLD/PRP/SOC で分散、EXS が mid で 2 atoms

新規留保 6 件 (累計 27 → 33 件):
- #28 long phase data 可用性 (算出可能と確定)
- #29 null absorption 判定方式 (cell-level 案 X-1 採用、Web Claude 即決事項)
- #30 matched_baseline v112 空 (cond3 構造的)
- #31 v112 integration_α/β 小サンプル (per-event 1-2 events)
- #32 c_conversion = ingestion 完全同値 (v10.2 即時摂食設計の構造的帰結、追究で解明済)
- #33 候補: 集計単位による方向反転 (全 events vs bin_5_plus で paired_d 符号反転 -0.94 vs +1.19、絶対格言 #4 集団平均の罠の生きた実例、Taka §1.9「揺れの幅」と接続)

10 段階の commit chain:
```
2281336  v10.13.a Step A 認識確認 + 事前齟齬 7 件指摘 + 9 論点回答
dd4aecd  v10.13.a Step B-J 完了 (Map 1-5 + long phase + 観察事実報告)
```

---

## 5. 出力ファイル schema 一覧 (主要)

### 5.1 v10.5 diag (CSV、subsequent versions 共通入力)

`developmental/v105/diag_v105_main_v2/`:

| ディレクトリ | ファイル | 主要列 |
|---|---|---|
| subjects/ | per_subject_seed{N}.csv | cognitive_id, birth_step, host_lost_step, reaped_step, final_state, n_core_member, last_familiarity_max |
| audit/ | per_subject_audit_seed{N}.csv | cid, n_core_member, v14_q0 |
| balance/ | balance_decisions_seed{N}.csv | step, observer_cid, decision, Q_at_decision, C_at_decision |
| balance/ | c_trajectory_seed{N}.csv | cid, window, C_at_window_end, Q_remaining_at_window_end |
| pulse/ | pulse_log_seed{N}.csv | cid, t, R_familiarity |
| ingestion/ | ingestion_events_seed{N}.csv | step, observer_cid, ghost_cid |
| integration/ | alpha_lifecycle_log_seed{N}.csv | alpha_id, step, event_type (birth/death/member_ghosted/active_to_recorded), member_cids |
| integration/ | beta_lifecycle_log_seed{N}.csv | beta_id, step, event_type (birth/alpha_added/beta_merged/q_c_inherited/active_to_recorded), member_cids |
| salience/ | salience_event_log_seed{N}.csv | step, observer_cid, candidate_cid, mass |
| network/ | fam_edges_seed{N}.csv | from, to, familiarity |

### 5.2 v10.6 sim_matrix

`outputs/main/cid_atom_sim_matrix_seed{N}.parquet`:
- 列: `cid:int, BOD.ear:float, COG.learn:float, ..., WLD.technique:float` (326 atom 列)
- 行: 5,224 cid

### 5.3 v10.7-v10.8 主要出力

| ファイル | 主要列 |
|---|---|
| `source_events_seed{N}.parquet` | event_id, event_source_type, source_cid, timestamp, Q_pre, C_pre, R_familiarity_pre, n_observed, lifespan_so_far, birth_step |
| `relation_paths_seed{N}.parquet` | event_id, source_cid, timestamp, target_cid, relation_path_type, relation_strength, hop_distance |
| `baselines_with_delta_seed{N}.parquet` | event_id, source_cid, target_cid, relation_path_type, timestamp, seed, delta_X_window (6 量 × 3 window = 18 列) + n_pulses_in_window_window |
| `excess_change_seed{N}.parquet` | seed, event_id, relation_path_type, n_targets, mean_delta_X_window (18 列) |
| `excess_change_adjusted_seed{N}.parquet` | 上記 + adjusted_mean_delta_X_window (18 列) + normalized_factor_at_event |
| `global_activation_factor_seed{N}.parquet` | step_bin_start, step_bin_end, pulse_count, ingestion_count, ..., global_activation_factor, normalized_factor |
| `atom_introduction_events_seed{N}.parquet` | source_events_seed schema + atom_id, atom_index, top_k_rank, atom_sim_score, reserved_label, Q_after_atom_intro, C_after_atom_intro |

### 5.4 v10.9-v10.12 条件付き出力

- `*_{cond}_seed{N}.parquet` の `{cond}` は: v10.9 `A1/A2/B3/C2`、v10.10 `v110_{gate}_t{age}` (28 種) + `v108_re`、v10.12 `v112/v108_standard`
- v10.11: `q_c_inherited_response_profile_seed{N}.parquet` (T_OFFSETS × pairs)
- v10.12: `propagation_profile_{cond}_seed{N}.parquet` (per-event 7 metric + Step C metadata、medium 固定)

### 5.5 v10.13.a 出力 (Map 1-5 + long phase、`developmental/v113a/outputs/main/`)

| ファイル | 主要列 |
|---|---|
| `map1_phase_x_ncore_per_seed.parquet` | seed, condition, phase, n_core_bin, n_events, delta_C_mean/std, delta_Q_mean, n_pulses_mean/std |
| `map1_phase_x_ncore_cross_seed.parquet` | + paired_diff_mean, paired_d, sign_test, bootstrap CI 95%, crosses_zero |
| `map2_phase_x_path_per_seed.parquet` | seed, condition, phase, path_category, path_name, n_events, path_excess_mean/std, path_delta_C_mean |
| `map3_phase_x_formation_per_seed.parquet` | seed, condition, phase, formation_relation, n_events, delta_C_mean/std, n_pulses_mean |
| `map4_phase_x_event_per_seed.parquet` | seed, condition (v107_natural/v112/v108_standard), phase, event_source_type, n_events, delta_C_mean |
| `map5_null_phase_per_cell.parquet` | condition, phase, n_core_bin, atom_id, atom_category, n_events_in_cell, n_paths_with_no_signal, is_null_cell_candidate |
| `excess_change_long_{cond}_seed{N}.parquet` | 通常の excess_change schema、ただし window 列が `long` のみ (1000-25000 step) |
| `step_b_environment.json`, `layer_b_baseline.json` | 環境チェック + 層 B baseline 記録 |
| `step_g_summary.json`, `step_h_summary.json`, `step_i_bit_identity_report.json` | 各 step メタデータ |

---

## 6. 実行コマンド (主要バージョン)

```bash
# v10.7 オービス完成
python3 developmental/v107/v107_post_process.py --mode main --n_workers 24

# v10.8 atom_introduction_event
python3 developmental/v108/v108_atom_event_generator.py --mode main
python3 developmental/v108/v108_post_process.py --mode main --n_workers 24

# v10.9 3 条件感度評価
python3 developmental/v109/v109_post_process.py --mode main --n_workers 24

# v10.10 28 conditions Multi-gate
python3 developmental/v110/v110_atom_event_generator.py --mode main --n_workers 24
python3 developmental/v110/v110_baseline_recalculator.py --mode main --n_workers 24
python3 developmental/v110/v110_multi_axis_stratified_analyzer.py --mode main

# v10.11 q_c_inherited within-cid
python3 developmental/v111/v111_q_c_inherited_observer.py --mode main --n_workers 24
python3 developmental/v111/v111_response_profile_compiler.py

# v10.12 Atom 取り込み prototype (10 段階)
python3 developmental/v112/v112_step_z_environment_check.py
python3 developmental/v112/v112_step_b_environment_check.py
python3 developmental/v112/v112_receptive_cid_detector.py --mode main
python3 developmental/v112/v112_orchestrator.py --mode main --n_workers 12 --layer-b-check
python3 developmental/v112/v112_cross_seed_analyzer.py
python3 developmental/v112/v112_window_post_process.py

# v10.13.a reaction phase 5 段階の整備 (post-process のみ)
python3 developmental/v113a/v113a_step_b_environment.py
python3 developmental/v113a/v113a_maps_analyzer.py
python3 developmental/v113a/v113a_null_phase_analyzer.py
python3 developmental/v113a/v113a_long_phase_compute.py --n_workers 8
python3 developmental/v113a/v113a_bit_identity_check.py
```

---

## 7. Phase ごとの機能リスト

### 7.1 Phase 1 (v10.0 - v10.5): ESDE 内部進化、物理層 frozen 絶対

**確立された機能**:

| 機能 | 確立版 | 役割 |
|---|---|---|
| 4 層アーキテクチャ | v10.0 | 物理 / 存在 / 認知 / 意識 |
| 死の二階層 | v10.0 | 存在層死 (ghost 化) / 認知層死 (Q=0 消滅) |
| ghost.residual_Q | v10.1 | ghost 化時 Q 完全継承、resource として摂食可能 |
| 摂食機構 | v10.1 | 1 step 1 ghost 食べきり、空摂食許容、ランダム選定 |
| 確率的認知/意識切替 | v10.2 | P(認知) = Q/(Q+C)、認知 = Q-1/C+1、意識 = C-1+摂食 |
| 即時摂食 | v10.2 | step 内動的連鎖 (先行 cid が ghost 食べきり、後続 cid 候補が動的変化) |
| n_core 層化観察 | v10.2 | 集団平均の罠を回避、戦略二極化 (bin_2 76% / bin_5+ 12%) を発見 |
| V_unified / Unity Metrics | v10.1 | mean(exp(iθ))、direction/concentration/shift/k の 4 指標 |
| θ 距離追跡 | v10.1 | 生誕時から L2 距離、coverage_ratio |
| 双方向 E3 機構 | v10.3 | 両者 hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触で両者 C-1 |
| ObservationTarget 動的追跡 | v10.3 | 3 段階 (主役選定 / be3 partner / post-process 第三項) |
| Triad 検出 | v10.3 | open_triad / closed_triad / proximate を post-process で抽出 |
| Integration 機構 (単層) | v10.4 | 誕生条件 4 種、Q/C 継承 (最強結合 1 個から 100%)、window 末再分配、recorded 永続化 |
| α/β 階層分離 | v10.5 | α = 観察軸 (Q/C 廃止) / β = 会計単位 (cid 単一所属、Q/C 継承先) |
| Salience-driven Focus | v10.5 | mass(X) = X.Q + X.C + β継承分、read_other / ingestion / be3 で mass-weighted 選択 |
| Recorded β からの Leakage | v10.5 | recorded β の C から ε=1 を主体 cid.C に転記 (be3 / ingestion trigger) |

### 7.2 Phase 1.5 (v10.6 - v10.13.a): Genesis × Language 統合

**確立された機能**:

| 機能 | 確立版 | 役割 |
|---|---|---|
| cid × atom cosine 類似度 | v10.6 | 48 次元 cid vector × 326 atom semantic centroid、sim_matrix 出力 |
| 25 atom 構造的特異性検出 | v10.6 | δ > 1% + z-score 評価で 25 atom 確定 (WLD.artless 留保) |
| 動学的発展段階観察 | v10.6 | 24 seeds 完全一致: WLD.artless → TIM.appear → WLD.artless → EXS.being |
| 観察解像度比較 | v10.6 | window (500) / step10 (10) / per-pulse (~50) |
| 5 種 source_event 統合 | v10.7 | pulse / ingestion / alpha_formation / beta_formation / c_conversion |
| attach_pre_event_state | v10.7 | merge_asof backward fill で event 時点の Q/C/familiarity 等を取得 |
| 5 種 relation_path 構築 | v10.7 | familiarity / attention_via_salience / integration_α/β / temporal_coactivation |
| 5 種 baseline 構築 | v10.7 | unrelated / same_step_random / matched / same_integ_low_fam / high_fam_outside |
| 3 window delta 計算 | v10.7 | immediate (1-10) / short (10-100) / medium (100-1000)、6 量 × 3 = 18 delta 列 |
| Level 1-3 因果候補階層化 | v10.7 | Level 1 co-occurrence / 2 path-enriched / 3 source-specific / 4 causal intervention (未実装) |
| atom_introduction_event 第 6 種 | v10.8 | 25 atom × top_k 100 × 24 seeds = 60K events、atom_index × 10 step ずらし均等分散発火 |
| Q/C 計算的減算 | v10.8 | Q-1/C+1 を post-process で算出、ledger 不変 |
| global_activation_factor 補正 | v10.8 | natural events のみ 100 step bin で正規化、adjusted_excess に反映 |
| Level 3.5 introduced vs natural | v10.8 | atom event mean_delta と v10.7 natural mean_delta の比較 |
| 寄与候補感度評価 | v10.9 | A1 vs A2 (Q/C cost) / B3 (random cid) / C2 (timing age=200) で cohens_d |
| bimodal KDE + 3 仮説 | v10.9 | KDE/find_peaks で 2 ピーク、H1 n_core / H2 integration / H3 lifecycle で効果量評価 |
| 4 種設計表 | v10.9 | sensitivity / receptivity / routing / natural_likeness の出口固定 |
| 9 GATES × 3 AGE 28 conditions | v10.10 | ABC/ABc/AB/B/Bc/AC/BC/A/all_pass × 200/300/500 + v108_re |
| is_receptive 関数 | v10.10 | event timestamp 別に cid の gate 判定 (in_integration 時間関数化) |
| 5 軸層化解析 | v10.10 | A: Integration 4 層 / B: 寿命 + n_core / C: atom 個別 / E: window × n_core / F: seed 別 |
| n_core 別反応 type 分業 | v10.10 | bin_2 (pulse 系 76%) / bin_5+ (delta_C 系 12%) |
| within-cid design | v10.11 | event ごとに影響 cid の個別プロファイル追跡 (T-50 vs T+50 を 21 snapshot) |
| 4 段階方向一致 | v10.11 | complete_consistent / majority_consistent / majority_zero / tied で 24 seeds 一致度評価 |
| 4 条件複合 cid 検出 | v10.12 | ¬β + lifespan ≥ 977 + n_core ≥ 5 + fam ≥ top 50%、420 cid × 25 atom |
| target_step burst 発火 | v10.12 | cid.birth + 200 を基準に atom_idx × 10 step ずらし (240 step 窓) |
| Aruism 整合 observation_recorder | v10.12 | 3 段階判定廃止、観察事実 + 層化 + 予想 vs 観察 + 留保を網羅記録 |
| paired_d / sign_test / bootstrap CI | v10.12 | 24 seeds で formal 統計、deterministic random_seed |
| bit-identity 3 層検証 | v10.12 | 層 A (smoke 2 回 hash 一致) / 層 B (既存 443 files mtime+size 不変) / 層 C (構造的保証) |
| smoke seed 0 限界の formal 化 | v10.12 追加 | window 単位 post-process で smoke vs main 乖離 4/7 metric を verify |
| 5 phase 統合枠組み | v10.13.a | immediate / short / mid / long / null。v10.7 3 window を Taka「時間軸 = 波及深度」で 5 phase 化、観察軸増加ではなく統合 |
| Map 1-5 reaction phase map | v10.13.a | phase × n_core / path / formation / event 種別 / null cell の 5 出口物 |
| cell-based null absorption (案 X-1) | v10.13.a | per-event CI 不要、phase × condition × n_core × atom cell で path 5 種無信号判定 |
| v107 WINDOW_DEFS monkey-patch | v10.13.a | 既存 v107 compute_deltas を再利用、長 phase (1000-25000 step) を層 B 不変で算出 |
| path_category 分離 | v10.13.a | atom_related (3) / layer5_structural (2) / baseline (5) を parquet 列で明示、絶対格言 #11 |
| 集計単位による方向反転の操作的観察 | v10.13.a 追究 | 全 events vs bin_5_plus で paired_d 符号反転 (-0.94 vs +1.19)、絶対格言 #4 集団平均の罠の実例 |

---

## 8. 凡例 (規約) — 各バージョン共通

| 規約 | 内容 |
|---|---|
| 物理層 frozen | v10.0 以降、ledger は不変。新機構は post-process 計算的減算で表現 |
| bit-identity 層 A | 同 seed 2 回実行で全出力 hash 一致 (deterministic 動作) |
| bit-identity 層 B | 既存バージョンの出力 (mtime + size) は不変 |
| bit-identity 層 C | 書き込みは当該バージョン配下のみ (構造的 assert) |
| safe_write_parquet_v{NNN} | 上記層 C を強制、親 dir 自動作成、snappy 圧縮 |
| per-seed × per-condition 並列 | `multiprocessing.Pool(processes=N)` で 24 workers 並列 |
| 確定的乱数 | numpy.random.default_rng(seed) または random.Random(seed) |
| event_id 命名 | `f"{seed}_{source_type}_{idx}"` (v107) / `f"{seed}_atom_{idx}"` (v108) / `f"{seed}_v112_atom_{idx}"` (v112)。v108_standard は v108 互換で `{seed}_atom_{idx}` 保持 |
| バージョンディレクトリ命名 | v10.0-v10.12 は 3 桁数字 (`v100`-`v112`)、v10.13 以降は a/b/c 接尾辞付き (`v113a`、`v113b`、`v113c`)、v10.13 は旧メジャーバージョン級主題 (Taka 確定 2026-05-11) |

---

## 9. 参照資料

| 種別 | ファイル | 行数 |
|---|---|---:|
| 概念サマリ (v10.0-v10.9) | `docs/ai_summaries/06_developmental_summary.md` | 1230 |
| 概念サマリ (v10.4-v10.12) | `docs/ai_summaries/06b_developmental_phase15_summary.md` | 683 |
| バージョン俯瞰 | `developmental/v10x_overall_review.md` | 407 |
| **実装技術仕様 (本書)** | `developmental/v10x_implementation_spec.md` | (本書) |
| 上位 Developmental Report | `docs/ESDE_Developmental_Report.md` | 801 |
| 上位 Primitive Report | `docs/ESDE_Primitive_Report.md` | - |
| ESDE Language legacy | `docs/LANGUAGE_LEGACY_DIGEST.md` | - |

### v10.13.a 主題ドキュメント (Web Claude + Code A)

| 種別 | ファイル |
|---|---|
| 主題ドキュメント | `developmental/v113a/v113a_phase_design.md` (Web Claude、Taka §1.9 + Taka 2026-05-11 整理を起点) |
| 実装指示書 | `developmental/v113a/v113a_implementation_brief.md` (Web Claude) |
| Step A 認識確認 | `developmental/v113a/v113a_step_a_recognition.md` (Code A、事前齟齬 7 件 + 9 論点回答) |
| Step A 即決事項返答 | `developmental/v113a/v113a_step_a_response_from_web_claude.md` (Web Claude → Code A) |
| Step J 観察事実報告 | `developmental/v113a/v113a_observation_report.md` (Code A、Map 1-5 直感語 + 構造文併記) |

各バージョン完了レポートは `developmental/v{NNN}/v{NNN}_*_report.md` を参照。

---

## 10. 最終一文

本書は ESDE v10.0-v10.13.a の **実装レベル詳細仕様** を 1 本に集約した後出しドキュメントであり、各バージョンの主要モジュール (`.py` ファイル) + データ構造 (`@dataclass` / NamedTuple) + 主要関数 (引数 + 戻り値) + 重要定数 + 入出力 schema を §3 (Phase 1) と §4 (Phase 1.5) に列挙、共通技術モジュール (v107 baseline_constructor の WINDOW_DEFS と compute_deltas、v107 path_analyzer の 5 種 relation_path、v107 baseline_constructor の 5 種 baseline、v108 global_activation_correction の補正、v108 TARGET_ATOMS 25 atom) を §2 に集約、Phase ごとの機能リスト (Phase 1 で 16 機能 / Phase 1.5 で 32 機能 [v10.13.a で +6]) を §7 に独立掲載、出力 schema 一覧を §5 (v10.13.a Map 1-5 + long phase を §5.5 で追加)、実行コマンドを §6 (v10.13.a 5 段階を追加)、各バージョン共通の規約 (物理層 frozen / bit-identity 3 層 / safe_write_parquet / per-seed 並列 / 確定的乱数 / event_id 命名 / バージョンディレクトリ命名 [v10.13 以降 a/b/c 接尾辞]) を §8 に整理、AI 対象として無駄を削減しつつ抜けなく記述、v10.12 完了 (commit 238a145) + window 追加調査 (commit ee87f63) + v10.13.a Step A-J 完了 (commit 2281336 + dd4aecd) までの全実装情報を網羅、v10.13.a は v10.7 オービス 3 window を Taka 整理「時間軸 = 波及深度」を起点として 5 phase (immediate / short / mid / long / null) に拡張、Map 1-5 (phase × n_core / path / formation / event / null cell) を post-process のみで算出、cell-based null absorption (案 X-1) + v107 WINDOW_DEFS monkey-patch (long phase) + 集計単位による方向反転の操作的観察 (留保 #33 候補、絶対格言 #4 集団平均の罠の実例、Taka §1.9「揺れの幅」と接続) を §4.8 + §7.2 で追加、留保事項累計 27 → 33 件 (#28-#33)。

---

*以上、ESDE v10.x 実装技術仕様書。AI 参照用、コードファイル中心、概念レベルは 06/06b、俯瞰は v10x_overall_review.md を参照。*
