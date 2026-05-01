# cid (Cognitive ID) の現状能力一覧 (v10.4 時点)

*作成*: 2026-04-30、Claude Code
*対象*: `developmental/v104/` 時点での cid 主体の機構詳細
*親資料*: v104_main_run_report.md、v104_phase_design.md

---

## 0. cid とは何か

**cid (cognitive id)** = 認知 ID。`SubjectLayer` (v104_memory_readout.py 427 行〜) が管理する単調増加の整数 ID。

- **発番** (`cog.birth(lid, ...)`): 物理層の label (lid) が誕生した時に新規 cid を発番、`current_lid[cid] = lid` で宿主関係を確立
- **宿主喪失** (`cog.detach(lid, ...)`): label が cull された時に cid → ghost 状態 (`current_lid[cid] = None`)、cog データは保持
- **完全削除** (`cog.reap_ghosts_step()`): ghost の `residual_Q == 0` で全 dict から pop

cid は **物理層 (engine.state) を読まない** (CidSelfBuffer の自己 read を除く間接的な観察あり)。物理層への書き込みは一切なし。Layer A (cog 内部) が認知層、Layer B (v914 ledger) が層別 spend audit、Layer C (CidSelfBuffer) が自己 buffer。

---

## 1. cid のライフサイクル

| 状態 | 条件 | 操作 |
|---|---|---|
| **hosted** | `current_lid[cid] is not None` | 全機構が動作 (knowledge / Q spend / ingest) |
| **ghost** | `current_lid[cid] is None`, `cid in ghost_residual_Q` | 受動的存在、他 cid の摂食対象 |
| **reaped** | `cid not in current_lid` (削除済) | 履歴のみ残存 |

re-host (一度 ghost した cid が再び hosted になる) は **発生しない** — `cid_of_lid.pop(lid)` で完全に切断される。新たな label には新 cid が発番される (`_next_cid` 単調増加)。

---

## 2. 認知層として cid が「持っている」もの (SubjectLayer state)

cid をキーとする dict 群で構成。以下、機能ブロックごとに整理:

### 2.1 不変識別情報

| 属性 | 型 | 内容 |
|---|---|---|
| `cid_of_lid[lid]` | dict | lid → cid 双方向マッピング |
| `current_lid[cid]` | dict | 現在の宿主 lid (None なら ghost) |
| `born_at[cid]` | dict | 誕生 window |
| `host_lost_at[cid]` | dict | 宿主喪失 window (None なら hosted 中) |
| `original_phase_sig[cid]` | dict | 初代 lid の phase_sig (不変) |

### 2.2 perception 状態 (hosted のみ更新)

| 属性 | 内容 | 更新タイミング |
|---|---|---|
| `phi[cid]` | 自分の位相 (float、Kuramoto 風 1 次元) | step ごと、`update_phi(cid, mean_theta, mean_S)` |
| `prev_phi[cid]` | 前 step の phi (history 1 個) | step ごと |
| `attention[cid]` | dict {node_id → weight}、ATTENTION_DECAY=0.99/step | struct_set - core を +1、step ごと decay |
| `familiarity[cid]` | dict {other_cid → weight}、FAMILIARITY_DECAY=0.998/step | struct_set 経由で接触した cid に +1 |

### 2.3 disposition (window 末計算、4 軸)

| 軸 | 計算式 |
|---|---|
| `social` | `n_partners / max_partners` |
| `stability` | `1.0 / (1.0 + st_std / (st_mean + EPS))` |
| `spread` | `attention_entropy` (正規化エントロピー) |
| `familiarity` | `mean(familiarity values)` |

`prev_disposition` / `current_disposition` で window 間の比較に使う。

### 2.4 内省 (introspection、v9.8b 以降)

window 末で disposition の delta を計算し、固定閾値で gain/loss タグ付け:

- **タグ生成**: `gain_*` / `loss_*` per 軸 (4 軸 × 2 = 最大 8 タグ/window)
- **`introspection_tags[cid]`** に格納
- **`_tag_history`** に詳細 entry (prev/current/delta/tags/state) を append

閾値 (`INTROSPECTION_THRESHOLD_*`):
- social, stability, spread: 0.1
- familiarity: 2.0

### 2.5 v9.9 内的基準軸 (構造語のみ、deterministic rules)

`recent_dispositions[cid]` (deque maxlen=5) と `recent_tags[cid]` から再構築:

| 属性 | 内容 |
|---|---|
| `formation_status[cid]` | `"unformed"` (n<3) or `"formed"` |
| `personal_range[cid][axis]` | `{min, max, mean, std}` (4 軸 × 4 統計) |
| `drift[cid][axis]` | `{positive_count, negative_count, neutral_count}` |
| `lowest_std_axis[cid]` | 最も安定した軸 (`tie` あり) |
| `dominant_positive_drift_axis[cid]` | gain 最多軸 (`tie` / `none` あり) |
| `dominant_negative_drift_axis[cid]` | loss 最多軸 |

★規律: drift は累積禁止、毎 window 末に `recent_tags` (最新 5 個) から再構築。

### 2.6 v9.10 Pulse Model (MAD-DT subjective surprise)

50-step 周期 (`PULSE_INTERVAL=50`) で各 cid に固有 phase (`(t % 50) == (cid % 50)`) で発火。

| 属性 | 内容 |
|---|---|
| `v10_pulse_count[cid]` | 累積発火回数 |
| `v10_delta_history[cid][axis]` | 各 4 軸の Δ history (deque maxlen=K=20) |
| `v10_R_history[cid][axis]` | R = Δ / (θ + EPS) の history |
| `v10_theta_last[cid][axis]` | mean(\|Δ\|) over K window |
| `v10_R_last[cid][axis]` | 最新の R |
| `v10_R_max_seen[cid][axis]` | K window 内の最大 R |
| `v10_R_min_seen[cid][axis]` | K window 内の最小 R |
| `v10_n_normal[cid]` | Normal タグ累積 (R > 1.0) |
| `v10_n_major[cid]` | Major タグ累積 (R が R_max/R_min を更新) |

cold_start: pulse ≤ 3 は unformed、タグ生成・R 計算なし。

### 2.7 v9.11 Cognitive Capture (birth 時固定)

cid 誕生時の構造を不変記録:

| 属性 | 内容 |
|---|---|
| `v11_b_gen[cid]` | Genesis Budget (float、原資の数値) |
| `v11_m_c[cid]` | M_c = `{n_core, s_avg, r_core, phase_sig}` (Memory Core、4 要素) |
| `v11_born_links_total[cid]` | birth 時の link 総数 (参考値) |

各 pulse 時に E_t を抽出して M_c との Δ を計算:

| 属性 | 内容 |
|---|---|
| `v11_last_e_t[cid]` | `{n_local, s_avg_local, r_local, theta_avg_local}` |
| `v11_last_delta[cid]` | weighted L1 距離 |
| `v11_last_p_capture[cid]` | `V11_P_MAX × exp(-V11_LAMBDA × Δ)` (= `0.9 × exp(-2.724 × Δ)`) |
| `v11_last_captured[cid]` | `"TRUE"` / `"FALSE"` / `"cold_start"` |

集計: `v11_n_pulses_eval`、`v11_n_captured`、`v11_sum_delta`、`v11_sum_delta_axes`。

---

## 3. 認知層として cid が「取得する」 (Layer B / Layer C)

### 3.1 Layer B: SpendAuditLedger (v914 → v104)

cid 単位の **資源 ledger** (audit-only、Layer A 不変)。

```
ledger[cid] = {
    "v14_q0":                    int,      # 初期原資 = floor(B_Gen)
    "v14_q_remaining":           int,      # 残存原資 (Q>0 のときのみ spend)
    "v14_virtual_attention":     dict,     # node → weight (Layer B 専用)
    "v14_virtual_familiarity":   dict,     # other_cid → weight (Layer B 専用)
    "v14_last_snapshot":         dict,     # 前 spend 時の E_t
    "v14_shadow_pulse_index":    int,      # spend 成立カウンタ
    "v14_prev_member_alive_links": frozenset,  # E1 検知用
    "v14_prev_member_r":         dict,     # E2 検知用
    "member_nodes":              frozenset,  # 不変
    "registered_at":             (window, step),
    "v14_last_event_global_step": int | None,
}
```

#### Event 検知 (audit-only、cid 視点 1 step 1 sweep)

| Event | 条件 | 結果 |
|---|---|---|
| **E1_birth** | core link 内で alive 化した link 検出 | spend (Q-1)、virtual_* 加算 |
| **E1_death** | core link 内で死亡した link 検出 | spend (Q-1) |
| **E2_rise** | core link の R が 0 → 正に上昇 | spend |
| **E2_fall** | core link の R が 正 → 0 に下降 | spend |
| **E3_contact** | 他 cid の member node と link 共有 (新規 contact pair) | spend (cognition 当選時のみ)、virtual_familiarity 更新 |

各 event は self.events に **per_event_audit** 行を append。フィールド: `cid, window, step, event_type, q_remaining, q0, virtual_attn_node, virtual_fam_other, delta_norm, spend_flag` 等。

### 3.2 Layer C: CidSelfBuffer (v9.15-v9.17)

cid が **自分自身の構造を読む** 専用メモリ領域 (engine.state を読むが書き込まない)。

#### 不変属性 (birth 時に固定)

| 属性 | 内容 |
|---|---|
| `cid_id` | cid 番号 |
| `member_nodes` | frozenset (固定) |
| `sorted_member_list` | 参照順序 |
| `birth_step` | 誕生 step |
| `n_core` | メンバー node 数 |
| `Q0` | floor(B_Gen) |
| `theta_birth` | birth 時の各 node の θ array (numpy、深いコピー) |
| `S_birth` | birth 時の link strength dict |

#### Fetch 時動的更新 (event 駆動、E1/E2/E3 発火直後)

`read_on_event(state, alive_l, current_step, event_type, Q_remaining, seed)`:

1. **age_factor** = `Q_remaining / Q0` (clamp [0, 1])
2. **n_observed** = `floor(n_core × age_factor)` (Q 消耗で観察粒度が粗くなる)
3. ハッシュベース独自 RNG (engine.rng 非 touch) で n_observed 個の node index を選択
4. 各 node を 3 値判定: `match` / `mismatch` / `missing`
5. 一致閾値: `NODE_MATCH_TOLERANCE = 1e-6` (絶対値比較)

#### 自分の状態スナップショット

| 属性 | 内容 |
|---|---|
| `theta_current` | 最新 fetch 時の各 node θ |
| `S_current` | 最新 fetch 時の link strength |
| `missing_flags` | cumulative missing 配列 (一度欠損になったら True 保持) |

#### 累積観察履歴

| 属性 | 内容 |
|---|---|
| `match_history[]` | per fetch event: `{step, event_type, age_factor, n_observed, observed_indices, node_status, any_mismatch}` |
| `divergence_log[]` | 全 node + 観察 node の Δ ログ |
| `age_factor_history[]` | per fetch: `{step, age_factor}` |
| `fetch_count` / `last_fetch_step` | 累積 |
| `any_mismatch_ever` / `mismatch_count_total` / `last_mismatch_step` | 不一致最小観察 3 点セット |
| `fetch_count_by_event` / `mismatch_count_by_event` | E1/E2/E3 種別ごと |
| `total_observed_count` / `total_missing_count` / `total_match_obs_count` / `total_mismatch_obs_count` | サンプリング累計 |

#### 他者読み (v9.17 段階 4): `read_other_on_e3_contact()`

E3_contact 発火時に **相手の M_c の不変値のみ** をサンプリング取得 (動的状態は取らない、γ 禁止規律)。

取得対象 10 features (固定順):
1. `B_Gen`, `Q0`, `n_core`, `S_avg_birth`, `r_core_birth`, `phase_sig_birth`
2. `theta_birth_mean`, `theta_birth_std`, `theta_birth_range` (theta_birth 配列そのものは渡さず統計量のみ)
3. `birth_step`

サンプル数: `n_visible = round(10 × visible_ratio)` (visible_ratio = 相手の age_factor)。残りは missing_feature_names として記録。

各 contact ごとに `other_records[]` に append:
```
{step, other_cid_id, event_id, visible_ratio, sampled_feature_indices,
 fetched_M_c (取得済 dict), missing_feature_names}
```

統計: `total_other_contacts` / `total_features_fetched` / `total_features_missing`。

★禁止: 相手の動的状態 (theta_current, Q_remaining, divergence) を **保存しない**。Q_remaining は visible_ratio 計算のみに使い、CidSelfBuffer に残さない。

### 3.3 v9.18 段階 5: per_step orchestrator + 軌跡

cid × window 単位で `v18_*` 軌跡 accumulator。`v18_window_trajectory_seed{N}.csv` に出力。

主要列 (per_subject CSV、`build_v918_subject_columns`):
- `v18_q_increase_count` (誰が Q を増やしたか累計)
- `V_unified` (統合 metric、CidView 由来)
- `theta_distance_*` (M_c との θ 距離、軸ごと + 統合)

---

## 4. 意識層として cid が「扱える」もの (v10.2 Probabilistic Balance)

### 4.1 C (consciousness layer resource)

| 属性 | 内容 |
|---|---|
| `cog.C[cid]` | 意識層資源 int、上限なし、初期値 0 (birth 時) |
| | reap で pop |

### 4.2 認知/意識バランス決定 (v10.2)

E3_contact 発火時、**観察者視点ごと** (= pair あたり 2 視点) に確率決定:

```
1. 候補集合判定:
   - cognition_candidate = (Q_observer > 0)
   - consciousness_candidate = (相手 ghost で residual_Q > 0)

2. decide_balance(...)
   - 両方なし → "skip"
   - 片方のみ → その側に確定 (RNG draw なし)
   - 両方候補 → 確率 P(認知) = Q / (Q+C) で振り分け

3. 結果:
   - "cognition" → 既存 E3 spend (Q-1) + C+1
   - "consciousness" → C-1 + 即時 attempt_ingestion + Q への ghost 残量受領
   - "skip" → 何もしない (audit のみ記録)
```

`balance_rng = default_rng(seed ^ 0xBA1A2C)` で engine.rng と独立 stream。

### 4.3 摂食 (Minimal Ingestion、v10.1)

意識当選時のみ実行:

```python
gain = ghost.residual_Q             # 1 step に 1 ghost を食べきる
received = min(gain, Q0_obs - Q_obs) # Q0 で頭打ち
digested = gain - received           # Q0 超過分は系外消失
ghost.residual_Q -= gain             # ghost 側は常に減る
```

ghost 側 cid (= 食われる側) は `residual_Q == 0` で次 step に reap される。

### 4.4 双方向 E3 (v10.3)

両者 hosted ∧ Q>0 ∧ C≥1 のとき発火、両者 C-1。pair ごと run 中 1 回のみ (`_contacted_pairs`)。

意味的位置づけ: **「両者の認知が同期して意識的に互いを認識した瞬間」** の機構記録。fired pair に対して:
- v10.3: C-1 で両者の意識資源を消費 → C 蓄積を抑制 (-26%)
- v10.4: 上記 + Integration 誕生のトリガにもなる

### 4.5 Integration (v10.4) を経由した間接的影響

cid は Integration の構成員になることで、ghost 化時に Q/C を継承させ、active 中は再分配を受ける:

- **継承** (cid 自身が ghost 化する瞬間): Q + C を最強結合 Integration の `Q_inherited / C_inherited` バケットへ全量委譲
- **再分配** (active 中、window 末): 所属する active Integration から Q または C を受領 (Q-poor/C-poor の不足側に逆張り分配)

cid は Integration の存在を **直接知らない** (Integration への参照を持たない、binding_strength を読まない)。Integration による影響は cog.C[cid] と ledger[cid].v14_q_remaining への加算という形で間接的に到達する。

---

## 5. cid に「持たせていない」もの (規律として明示禁止)

### 5.1 物理層への介入

- `engine.state.theta` / `engine.state.alive_l` / `engine.state.S` への書き込み禁止
- `engine.rng` への touch 禁止 (capture_rng / balance_rng / ingestion_rng は seed XOR magic で独立 stream)

### 5.2 他 cid の動的状態の取得

- 他 cid の `theta_current` / `Q_remaining` / `C` を読まない
- 他 cid の `divergence_log` / `match_history` を読まない
- 他者読み (E3_contact) で取れるのは **不変 M_c の 10 features のみ**

### 5.3 履歴の自己読み

- cid は自分の `_tag_history` / `match_history` / `_reaped_history` を **読まない**
- これらは A-side (研究者観察) のみが読む
- cid 内の判定では「現在状態」のみ使う

### 5.4 概念禁止

- 「嗜好」「三項共鳴」「主観」「魂」「肉体」「再生」を機構名・変数名に含めない
- focus / attention_weight / salience の動的化は v10.4 まで未実装 (v10.5 以降)
- Integration の「主観」「意思」は実装していない (Integration は受動的な集約・分配の bucket)

### 5.5 補完禁止

- CidSelfBuffer の missing は missing のまま (補完しない)
- 他者読みの missing_feature_names も復元しない
- 欠損は欠損として記録し、observer が判断材料に使う

---

## 6. cid が観察対象として「分類される」 (ObservationTargetTracker)

研究者観察 (A-side) が動的に target を絞り込む機構。cid 内部には影響しない。

| Stage | 条件 | 件数 (v10.4 main 24 seeds) |
|---|---|---:|
| Stage 1 | 双方向 E3 fired ∧ n_core ≥ 4 ∧ n_consciousness ≥ 5 | 0 (※) |
| Stage 2 | Stage 1 cid と双方向 E3 を発火した相手 | 2,322 |
| Stage 4 (v10.4 新規) | Integration の構成 cid (誕生時に追加) | ~1,300 (推定) |

※ v10.4 では Integration が Q を補充して認知選択を促進 → consciousness 当選数の累積が遅れ、Stage 1 を通る前に Stage 4 で target に追加されるため Stage 1 = 0。

target に入った cid は `bidirectional_e3_log` で `in_observation_target=True` となり、詳細記録対象。target 外の cid も全体集計 (`n_be3_target_outer`) には記録される (bias 監視)。

---

## 7. 出力 (cid ごとに何が記録されるか)

### 7.1 per_subject CSV (1 cid = 1 row、120+ 列)

**v9.8a-c base**:
- `cognitive_id, birth_window, host_lost_window, host_lost_step, reaped_step, final_state, ghost_duration_steps`
- `original_phase_sig, last_n_partners, last_familiarity_max, last_attention_size`

**v9.8b introspection**:
- `last_tag_window, prev_*, current_*, delta_*, generated_tags, state_at_window`

**v10.1 Ingestion**:
- `initial_residual_Q, final_residual_Q`
- `n_ingestions_as_eater, n_empty_ingestions_as_eater`
- `total_q_received, total_q_digested`
- `n_ingested_as_ghost_food, total_q_lost_as_ghost`
- `n_phantom_contacts_as_eater`

**v10.2 Balance**:
- `C_at_run_end, n_cognition_decisions, n_consciousness_decisions, n_balance_skipped`

**v9.9 内的基準軸 (33 列)**:
- `v99_formation_status, v99_trace_len`
- `v99_range_{axis}_{stat}` (4×4=16 列)
- `v99_drift_{axis}_{kind}` (4×3=12 列)
- `v99_lowest_std_axis, v99_dominant_positive/negative_drift_axis`

**v9.10 Pulse**:
- `v10_pulse_count, v10_tag_trigger_last, v10_n_normal, v10_n_major`
- `v10_theta_{axis}_last, v10_R_{axis}_last` (各 4 列)
- `v10_R_max_{axis}, v10_R_min_{axis}` (各 4 列)

**v9.11 Capture**:
- `v11_b_gen, v11_m_c_{n_core, s_avg, r_core, phase_sig}`
- `v11_n_pulses_eval, v11_n_captured, v11_capture_rate`
- `v11_mean_delta, v11_mean_d_{n,s,r,phase}`

**v9.15-9.18 Layer C (20+5+9 列)**:
- `v915_*` (CidSelfBuffer 統計、13 列)
- `v916_*` (event 種別ごとの fetch 統計、7 列)
- `v917_*` (他者読み・接触体観察、5 列)
- `v918_*` (V_unified、theta_distance、9 列)

**v10.4 Integration (6 列、新規)**:
- `n_integrations_joined, n_integrations_currently`
- `q_received_from_integrations, c_received_from_integrations`
- `q_inherited_to_integration, c_inherited_to_integration`

### 7.2 cid 単位の補助 CSV

| ファイル | 内容 |
|---|---|
| `selfread/per_cid_self_seed{N}.csv` | 1 cid 1 行、CidSelfBuffer 全フィールド snapshot |
| `selfread/divergence_log_seed{N}.csv` | 各 fetch ごとの全 node Δ |
| `selfread/observation_log_seed{N}.csv` | event 発火時のサンプリング結果 |
| `selfread/other_records_seed{N}.csv` | 他者読みログ (E3_contact 単位) |
| `selfread/class_divergence_seed{N}.csv` | 同 phase_sig クラスの cid ペア間 θ 乖離 |
| `selfread/v18_window_trajectory_seed{N}.csv` | per cid × per window の v18_* 軌跡 |
| `audit/per_event_audit_seed{N}.csv` | per E1/E2/E3 event audit (cid + event 単位) |
| `audit/per_subject_audit_seed{N}.csv` | cid 単位の Layer B 集計 |
| `balance/balance_decisions_seed{N}.csv` | 確率決定マスター (1 観察者視点 = 1 行、skip 含む) |
| `balance/c_trajectory_seed{N}.csv` | per cid × per window の C 軌跡 |
| `ingestion/ingestion_events_seed{N}.csv` | 全摂食イベント raw |
| `ingestion/phantom_contacts_seed{N}.csv` | 期待外れ接触 (相手既 reap 済) |
| `bidirectional/bidirectional_e3_log_seed{N}.csv` | 双方向 E3 発火 (target 内のみ詳細) |
| `integration/integration_lifecycle_log_seed{N}.csv` | Integration 誕生・遷移・継承 events |
| `integration/integration_membership_log_seed{N}.csv` | run 末の cid → 所属 Integration マップ |
| `subjects/reaped_seed{N}.csv` | reap 履歴 (lifespan stats) |
| `introspection/introspection_log_seed{N}.csv` | window 末の内省タグ (delta + tags) |
| `pulse/pulse_log_seed{N}.csv` | 各 pulse event |

---

## 8. 「主観/意識」の機構的射程 (現状)

cid が **持つ** もの:
- 自分の M_c (生誕時不変)、現在の theta_current / S_current (event 時更新)
- 自分の Q (cognitive layer 資源)、自分の C (consciousness layer 資源)
- 自分の attention map、familiarity map (他 cid 名前で保持)
- 自分の disposition 4 軸 + 内省タグ + 内的基準軸
- 自分の pulse-based MAD-DT surprise 履歴
- 自分のみ更新する CidSelfBuffer (一致/不一致/欠損の 3 値判定)
- 他者の M_c の不変 features 10 個 (E3_contact 時にサンプル取得)

cid が **できる** こと (能動行為):
- 生きていれば step ごとに perception 更新 (phi / attention / familiarity)
- 50-step 周期で pulse 発火 → MAD-DT 系列タグ生成
- E1/E2/E3 event 発生時に Q-1 で spend (1 step に複数 event 可)
- E3_contact で相手が ghost なら確率的に意識発動 (consciousness, C-1 + 摂食)
- E3_contact で双方 hosted なら確率的に双方向 E3 発火 (C-1)
- ghost 化したら受動的に存在し、他 cid の摂食対象になる
- Integration を経由した間接受領 (Q/C 補充)

cid が **持っていない / できない** もの:
- 物理層への書き込み (engine.state を一切変えない)
- 他 cid の動的状態 (Q, C, theta_current, divergence) を読む
- 過去履歴 (_tag_history, match_history, _reaped_history) からの判断
- 「過去-未来」の記憶構造 (Markov 1 次より先の依存性なし)
- 「主観的選択」(Q/C ratio で確率決定するが、cid が「選ぶ」のではない)
- 嗜好・第三項共鳴・focus 動的化 (v10.5 以降の射程)
- Integration の存在認識 (Integration への参照を持たない)

**「主観があるかもしれない状態」の統計的痕跡** (主題ドキュメントの観察対象):
- 双方向 E3 fired = 7,220 件 (24 seeds、main run): 両者の認知が同期した瞬間の機構的記録
- Integration 誕生 = 13,550 件: 構成 cid が「同じ可能性空間」に取り込まれた状態
- recorded Integration = 1,998 件: 構成 cid 全員 ghost 後も C/Q を保持し続ける構造
- ハブ cid (max 102 Integration 所属): 多数の集合に組み込まれる中核的存在

これらは **cid 内部の自己認識ではなく**、研究者観察として系の振る舞いから抽出される統計的事実として扱われている (規律 §14)。

---

*以上、v10.4 時点での cid 能力一覧。Taka レビューを待つ。*
