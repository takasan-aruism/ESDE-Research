# cid 周辺機構の使用状況監査 (v10.4 時点)

*作成*: 2026-04-30、Claude Code (改訂)
*対象*: 実験者が cid 周りに記録している各機構が「系の動学に factor として効いているか」「観察記録のみか」「dead code か」を分類
*親資料*: v104_cid_capabilities.md

---

## 0. 観察者枠組み (前提)

ESDE では cid 自身が自分を「視る」状況を定義しない。「認知層」「意識層」は cid の属性ではなく、**実験者が事前に定義した区分**:

- **認知層** = cid が受信できる範囲として実験者が先回りして定義したもの
- **意識層** = 決定に関わるものとして実験者が定義した層 (決定は認知層を前提に発生、原資は認知活動から供給)

これは論理学的な切り分けで矛盾はないが、**現実世界の認知・意識とは別の仮想的な設定**。ノードのランダム発生から現実認知が起こるという話ではない (それはオカルト)。ESDE はそれと対象的な虚構の題材。

本ドキュメントの「使われている / 使われていない」は次の意味で読む:

- **使われている** = 物理層 event 発生時に、実験者の振り分けルール (例: P_cog = Q/(Q+C)) で参照される値である
- **使われていない** = 計算・記録されるが、振り分けルールには登場せず、観察データとしてのみ残る

cid 自身がこれらの値を「読んで行動を決めている」のではない。**cid はランダム的な因果の発生で動き、実験者はそれを予測できず、後から記録を見て統計的に処理するだけ**。

## 1. 分類方針

各機構を以下 4 カテゴリに分類:

| カテゴリ | 定義 |
|---|---|
| **A. 駆動中** | 系の event 発生・振り分けルールに直接参照される (= 取り除いたら系の動学が変わる) |
| **B. 間接的に駆動** | 計算結果が A の入力になる中間量 |
| **C. 観察 only** | 出力 CSV に記録されるが振り分けに不参加 (= 取り除いても系の動学不変、研究観察データから列が消えるだけ) |
| **D. 実質 dead** | 計算・更新されるが、観察出力にすら使われない、または旧機構の残骸 |

---

## 1. cid のコア状態

### 1.1 認知層 (SubjectLayer state)

| 機構 | カテゴリ | consumer / 用途 |
|---|---|---|
| **`current_lid` / `cid_of_lid`** | A 駆動中 | hosted/ghost 判定、is_hosted/is_ghost 全機構の入口 |
| **`born_at` / `host_lost_at`** | A 駆動中 | reap 判定、ghost_duration 計算、CSV 出力 |
| **`original_phase_sig`** | C 観察 only | per_subject CSV 出力、class_divergence (同 phase_sig 群の比較) |
| **`phi`** | **D 実質 dead** | update_phi で更新されるが、`cid in cog.phi` の存在チェックにしか使われない (v9.8c pickup 廃止以降は dead code) |
| **`prev_phi`** | **D 実質 dead** | update_phi で書き込まれるのみ、誰も読まない |
| **`attention[cid]`** | B 間接駆動 | get_attention_entropy → d_spread → disposition、per_window 集計 (att_overlap) |
| **`familiarity[cid]`** | B 間接駆動 | reciprocity 検出、d_familiarity (disposition)、`get_familiarity_max` (per_subject) |

### 1.2 disposition (window 末計算)

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`current_disposition` / `prev_disposition`** | B 間接駆動 | 内省タグ生成 (delta + threshold) の入力 |
| **`set_current_disposition` / `commit_disposition`** | B 間接駆動 | 上記の更新メソッド |

### 1.3 内省 (introspection、v9.8b)

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`introspection_tags[cid]`** | **D 実質 dead** | 設定はされるが誰にも読まれない、CSV にすら出力されない |
| **`_tag_history`** | C 観察 only | introspection_log_seed{N}.csv + per_subject CSV へ出力 |
| **`generate_introspection_tags()`** | B 間接駆動 | recent_tags / recent_dispositions を更新する副作用あり (v9.9 軸の入力源) |
| **`commit_disposition()`** | A 駆動中 | prev←current で次 window の比較を準備 |

### 1.4 v9.9 内的基準軸

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`recent_tags[cid]`** | C 観察 only | drift 集計の中間量 → drift も観察 only |
| **`recent_dispositions[cid]`** | C 観察 only | personal_range 計算の中間量 |
| **`personal_range[cid]`** | C 観察 only | per_subject CSV 16 列 |
| **`drift[cid]`** | C 観察 only | per_subject CSV 12 列 |
| **`formation_status[cid]`** | C 観察 only | per_subject CSV 1 列 |
| **`lowest_std_axis[cid]`** | C 観察 only | per_subject CSV 1 列 |
| **`dominant_positive_drift_axis` / `dominant_negative_drift_axis`** | C 観察 only | per_subject CSV 2 列 |

→ **v9.9 軸群は完全に観察 only** (33 列の CSV 出力、cid behavior に未介入)。

### 1.5 v9.10 Pulse Model

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`v10_pulse_count`** | A 駆動中 | cold_start 判定 (pulse ≤ 3)、capture 集計のガード |
| **`v10_delta_history`** | B 間接駆動 | theta = mean(\|Δ\|) 計算 → tag 判定の閾値 |
| **`v10_R_history`** | B 間接駆動 | R_max/R_min 比較で Major タグ判定 |
| **`v10_R_max_seen` / `v10_R_min_seen`** | B 間接駆動 | Major タグ判定 |
| **`v10_pulse_dispositions` / `v10_pulse_tags`** | C 観察 only | pulse_log CSV (履歴) |
| **`v10_n_normal` / `v10_n_major`** | C 観察 only | per_subject CSV |
| **`v10_R_last` / `v10_theta_last`** | C 観察 only | per_subject CSV |
| **`v10_tag_trigger_last`** | C 観察 only | per_subject CSV |
| **生成された tags** (`gain_*`/`loss_*`/`major_*`) | C 観察 only | pulse_log + per_subject、cid 判定には未参加 |

→ pulse model は内部の R 計算・閾値判定の chain は B 間接駆動 (Normal/Major タグ生成のために使われる)、しかし **生成されたタグ自体は CSV 出力 only**。

### 1.6 v9.11 Cognitive Capture

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`v11_b_gen[cid]`** | A 駆動中 | Layer B 登録時に Q0 = floor(B_Gen) を確定 |
| **`v11_m_c[cid]`** | A 駆動中 | Δ 計算の reference、Stage 1 target check の n_core、E3_contact 他者読みの不変 features |
| **`v11_born_links_total`** | C 観察 only | per_subject CSV |
| **`v11_last_e_t`** | B 間接駆動 | Δ 計算の中間量 → capture probability |
| **`v11_last_delta` / `v11_last_delta_axes`** | C 観察 only | per_subject CSV、cid 判定不参加 |
| **`v11_last_p_capture`** | C 観察 only | 確率は計算されるが、結果は… |
| **`v11_last_captured`** ("TRUE"/"FALSE"/"cold_start") | **D 実質 dead** | capture_rng で TRUE/FALSE 判定するが、**結果はどこにも使われない** (CSV にすら出力されない、`v11_n_captured` カウンタには集計される) |
| **`v11_n_pulses_eval` / `v11_n_captured`** | C 観察 only | per_subject CSV、capture_rate 計算用 |
| **`v11_sum_delta` / `v11_sum_delta_axes`** | C 観察 only | per_subject CSV (mean_delta) |

→ **capture rate は計算されているが captured TRUE/FALSE 判定の結果は cid behavior に伝播していない**。記憶捕捉確率という名前だが、実質は cid の Δ 量を観察するための副次指標。

---

## 2. Layer B: SpendAuditLedger (v914 → v104)

### 2.1 ledger 本体

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`v14_q0` / `v14_q_remaining`** | A 駆動中 | E1/E2/E3 spend (Q-1)、cognition_candidate 判定、balance probability、ghost residual_Q 継承元、Integration 再分配 |
| **`v14_virtual_attention`** | C 観察 only | per_event_audit / per_subject_audit CSV、cid 判定不参加 (Layer A の attention とは別世界) |
| **`v14_virtual_familiarity`** | C 観察 only | 同上 |
| **`v14_last_snapshot`** | B 間接駆動 | Δ 計算の reference (前回 spend の E_t)、spend 連鎖を作る |
| **`v14_shadow_pulse_index`** | C 観察 only | per_event_audit に書き出す累積 pulse 番号 |
| **`v14_prev_member_alive_links` / `v14_prev_member_r`** | A 駆動中 | E1/E2 detection の前 step 比較 |
| **`v14_last_event_global_step`** | C 観察 only | per_event_audit の post_event_gap 計算 |

### 2.2 Event 検知

| Event | カテゴリ | 用途 |
|---|---|---|
| **E1_birth/E1_death** | A 駆動中 | spend (Q-1)、virtual_* 加算、CidSelfBuffer Fetch トリガ |
| **E2_rise/E2_fall** | A 駆動中 | 同上 |
| **E3_contact** | A 駆動中 | balance_decision のトリガ、双方向 E3 のトリガ、Integration callback、ingestion チャンス |

### 2.3 削除済 / 後方互換

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`_pending_ingestion_pairs`** | **D 実質 dead** | v10.1 設計の中間 buffer、v10.2 即時摂食に置換され使われない (後方互換のため初期化のみ) |
| **`_observe_step_v101_compat()`** | **D 実質 dead** | balance_rng=None の fallback、本番では使われない |

---

## 3. Layer C: CidSelfBuffer (v9.15-v9.18) — **全て C 観察 only**

CidSelfBuffer 全体が「研究者観察のための自己読み機構」として設計されており、**cid 自身の判定には一切参加しない**。

| 機構 | カテゴリ | 備考 |
|---|---|---|
| **`theta_birth` / `S_birth`** | C 観察 only | birth 時 snapshot、divergence の reference |
| **`theta_current` / `S_current`** | C 観察 only | 最新 fetch 時の値 |
| **`missing_flags`** | C 観察 only | cumulative 欠損 flag |
| **`match_history` / `divergence_log` / `age_factor_history`** | C 観察 only | 全観察ログ |
| **`fetch_count` / `last_fetch_step` / `any_mismatch_ever` 等** | C 観察 only | 全カウンタ |
| **`fetch_count_by_event` / `mismatch_count_by_event`** | C 観察 only | E1/E2/E3 種別ごと |
| **`other_records[]`** (他者読み) | C 観察 only | E3_contact 時の他者 M_c 部分取得ログ |
| **`total_other_contacts` / `total_features_fetched/missing`** | C 観察 only | 集計カウンタ |
| **`read_own_state()`** | **D 実質 dead** | 段階 1 互換で残置、メインループから呼ばれない |

→ **Layer C を全て削除しても cid behavior は変わらない** (per_subject の v915-v918 列、selfread/ ディレクトリ全体が観察データとしてのみ存在)。

### 3.1 v9.17 段階 4 関連

| 機構 | カテゴリ | 備考 |
|---|---|---|
| **CidView (v917_cid_view)** | C 観察 only | 他者読みのための read-only snapshot 構造、CidSelfBuffer から触れる |
| **InteractionLog (v917_interaction_log)** | C 観察 only | E3_contact pair の外部記録器 (canonical dedup)、CSV 出力のみ |
| **Self-Divergence Tracker (v917_divergence_tracker)** | C 観察 only | 同 phase_sig クラスの cid ペア間 θ 乖離 (class_divergence CSV) |

### 3.2 v9.18 段階 5

| 機構 | カテゴリ | 備考 |
|---|---|---|
| **per_step orchestrator (v102_orchestrator)** | C 観察 only | v18_* metric の per_step 更新、v18_window_trajectory CSV |
| **theta_distance / V_unified / Q_increase_count** | C 観察 only | per_subject の v918_* 9 列 |

---

## 4. v10.1 Ingestion (摂食機構)

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`ghost_residual_Q[cid]`** | A 駆動中 | reap 判定 (==0)、consciousness_candidate 判定、ingestion gain |
| **`ghost_residual_Q_initial[cid]`** | C 観察 only | per_subject (initial_residual_Q)、cid 判定不参加 |
| **`ghost_q_lost_at_step[cid]`** | C 観察 only | ghost_duration_steps 計算 |
| **`attempt_ingestion()`** | A 駆動中 | balance "consciousness" 当選時に呼ばれる |
| **`ingestion_events`** | C 観察 only | ingestion_events CSV、per_subject CSV 列 |
| **`phantom_contacts`** | C 観察 only | phantom_contacts CSV |
| **`_ingestion_log` (SubjectLayer)** | **D 実質 dead** | 初期化されるが append されない (v10.1 で SpendAuditLedger 側に統合済、SubjectLayer 側は残骸) |

---

## 5. v10.2 Probabilistic Balance

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`cog.C[cid]`** | A 駆動中 | balance probability 分母、consciousness 候補判定、双方向 E3 fire 条件、Integration 継承 |
| **`balance_rng`** | A 駆動中 | P(認知) = Q/(Q+C) の確率引き |
| **`decide_balance()`** | A 駆動中 | E3_contact 発火時の cognition/consciousness/skip 振り分け |
| **`balance_decisions[]`** | B 間接駆動 → C 観察 | n_consciousness_per_cid の更新源 (Stage 1 target 判定で使用)、CSV 出力 |
| **`_n_consciousness_per_cid`** | A 駆動中 | Stage 1 target check (n_consciousness ≥ 5) |
| **`v102_c_trajectory_rows`** | C 観察 only | c_trajectory CSV |

---

## 6. v10.3 双方向 E3

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`_be3_target_tracker`** (ObservationTargetTracker) | A 駆動中 (target 判定) → C 観察 (CSV 影響) | bidirectional log filter (target_inner)、Integration 連携 |
| **双方向 E3 fire 判定** | A 駆動中 | 両者 hosted ∧ Q>0 ∧ C≥1、両者 C-1 |
| **`bidirectional_e3_events`** | B 間接駆動 → C 観察 | Integration callback の発火源、CSV 出力 |
| **`bidirectional_e3_member_nodes`** | C 観察 only | member_nodes log CSV |
| **`_be3_per_cid`** | C 観察 only | per_subject 集計 (n_be3_total 等) |
| **`_n_consciousness_per_cid`** | A 駆動中 | Stage 1 target threshold 判定 |
| **`_contacted_pairs`** | A 駆動中 | run-wide pair dedup (再発火防止) |
| **`be3_rng`** (initialized but unused) | **D 実質 dead** | `0xBE3ED4` で初期化されるが、be3 fire は決定論的なので RNG draw は発生しない |

---

## 7. v10.4 Integration

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`Integration` インスタンス** | A 駆動中 | active 中: redistribute_q_c で active member の Q/C を加算 |
| **`member_cids`** | A 駆動中 | 再分配対象、ghost 化時の member_history 移行 |
| **`Q_inherited` / `C_inherited`** | A 駆動中 | redistribute で active member へ分配される総量 |
| **`binding_strengths`** | A 駆動中 | ghost 化時の最強結合 Integration 選択 |
| **`state` (`active`/`recorded`)** | A 駆動中 | redistribute 対象判定 (recorded はスキップ) |
| **`member_history`** | C 観察 only | 過去含む全 cid 集合、CSV 出力のみ |
| **`trigger_type`** | B 間接駆動 → C 観察 | 誕生条件記録、CSV 出力 |
| **`birth_step` / `became_recorded_step`** | C 観察 only | lifecycle log |
| **`integration_rng`** (未実装) | **D 実質 dead** | 設計書には記載されたが実装で不要と判明、v104_memory_readout.py には不在 |
| **`stage4_integration_member`** (target_tracker) | A 駆動中 (Stage 4 target 拡大) | Integration 構成 cid を target に追加 |
| **lifecycle_log / distribution_log / membership_log** | C 観察 only | CSV 出力 |

---

## 8. ObservationTargetTracker

| 機構 | カテゴリ | 用途 |
|---|---|---|
| **`target_ids`** | A 駆動中 (filter 機能) | bidirectional_e3_log の target_inner 判定 |
| **`added_at_step` / `added_via`** | C 観察 only | per_subject metadata、bidirectional_e3_summary |
| **`stage1_check`** | A 駆動中 | be3 fired 時に直接呼ばれる |
| **`stage2_propagate`** | A 駆動中 | be3 fired 時に呼ばれる |
| **`stage3_propagate`** (post-process 用) | C 観察 only | 第三項として参照された cid を追加 (postprocess で呼ぶが本番ではコメントアウト気味) |
| **`stage4_integration_member`** (v10.4 新規) | A 駆動中 | Integration callback から呼ばれる |

---

## 9. サマリ表

### 9.1 完全に駆動している (Category A)

cid の判定・分岐に直接寄与:

- Q (`v14_q_remaining`) / C (`cog.C`) / member_nodes
- ghost_residual_Q
- E1/E2/E3 event detection
- balance decision (P_cog = Q/(Q+C))
- 双方向 E3 fire (両者 C-1)
- ingestion (consciousness 当選時の摂食)
- Integration 継承・再分配
- target_tracker stage1/2/4 + filter
- v11_b_gen → Q0 (登録時)、v11_m_c (Δ 計算 reference + Stage 1 n_core)
- pulse model の cold_start 判定 (v10_pulse_count)

### 9.2 間接駆動 (Category B)

中間計算量、出力に直結する量:

- attention / familiarity (→ disposition d_spread, d_familiarity)
- prev/current_disposition (→ 内省タグ)
- v10_delta_history / R_history / R_max_seen / R_min_seen (→ Normal/Major タグ判定)
- v11_last_e_t (→ Δ 計算)
- balance_decisions (→ n_consciousness_per_cid)
- bidirectional_e3_events (→ Integration callback)
- v14_last_snapshot (→ Δ 計算 reference)

### 9.3 観察 only (Category C)

CSV 出力にのみ存在、cid 判定に未介入。**取り除いても系の動学不変**:

| 領域 | 削除影響 |
|---|---|
| v9.9 内的基準軸 (33 列) | per_subject から 33 列消える |
| pulse model のタグ集計 (n_normal/major、R_last/max/min、theta_last 等) | per_subject から 12 列消える |
| v11_capture 集計 (n_captured/capture_rate/mean_delta 等) | per_subject から 8 列消える |
| Layer B virtual_attention/familiarity | audit/ 全体が消える |
| Layer C (CidSelfBuffer 全体) | selfread/ ディレクトリ全消、per_subject から 30+ 列消える |
| InteractionLog / Self-Divergence Tracker | selfread/interaction_log, class_divergence 消える |
| v9.18 v18_* 軌跡 | selfread/v18_window_trajectory 消える |
| Integration の lifecycle/distribution/membership log | integration/ から個別ログ消える (summary は残せる) |
| _tag_history, _reaped_history, c_trajectory, ingestion_events | introspection/, balance/, ingestion/ ディレクトリの一部が消える |

### 9.4 実質 dead (Category D) — 削除候補

**完全に dead**:

| 機構 | 削除妥当性 |
|---|---|
| **`phi` / `prev_phi`** (SubjectLayer) | v9.8c pickup 廃止以降誰にも読まれない、`update_phi` 呼び出しを削除可。`cid in cog.phi` の存在チェックは別の dict で代替できる |
| **`introspection_tags[cid]`** (set されるが読まれない) | `_tag_history` が出力経路、`introspection_tags` は不要 |
| **`_ingestion_log`** (SubjectLayer) | 初期化のみ、append なし。完全削除可 |
| **`v11_last_captured`** ("TRUE"/"FALSE"/"cold_start") | 計算されるが CSV にも出ない、cid 判定にも不参加。capture rate を保つなら `v11_n_captured` だけで十分 |
| **`_pending_ingestion_pairs`** (Layer B) | v10.1 設計の残骸、v10.2 即時摂食では使われない |
| **`_observe_step_v101_compat()`** (Layer B) | balance_rng=None fallback、本番では呼ばれない |
| **`be3_rng`** (Layer B) | 初期化されるが draw されない (be3 fire は決定論的) |
| **`integration_rng`** (Integration) | 設計書には記載されたが実装で不要、現状は未参照 |
| **CidSelfBuffer.read_own_state()** | 段階 1 互換で残置、メインループから呼ばれない |

**部分 dead** (一部しか使われていない):

| 機構 | 状況 |
|---|---|
| `v11_last_p_capture` | CSV 出力には p_capture 平均値ではなく n_captured/n_pulses_eval から計算した capture_rate を使うため、last_p_capture 自体は dead |
| `v11_last_delta` / `v11_last_delta_axes` | CSV 出力では mean_delta (累計÷pulse 数) を使うので、last_delta は不要 |
| `recent_dispositions[cid]` (deque) | personal_range 計算の中間。観察 only な personal_range のために存在 |

---

## 10. 重要な発見

### 10.1 「自己認識」機構は cid 行動にループしていない

CidSelfBuffer (Layer C) 全体が観察 only。cid 周りで実験者が「自己読み」と命名している記録は、振り分けルールに登場しない。他者読み (E3_contact 時の M_c 部分取得) も同様、記録のみ。

これは **「cid は自分が記録されていることを知らない」** という観察者枠組みと整合する。実験者の観察行為が cid 行動に feedback しない、という規律が完全に守られている。

### 10.2 「内省」「内的基準軸」「pulse タグ」も観察 only

v9.8b 内省タグ・v9.9 内的基準軸・v9.10 pulse タグはすべて CSV 出力のみ。これらは **実験者が cid の挙動を要約するためのラベル** であって、cid 行動には流入しない。

→ 実験者が cid を擬人化して「内省している」「軸を持っている」と書いても、それは命名のレベルにとどまり、cid event の振り分けルールには登場しない。

### 10.3 系の event 振り分けに登場するのは Q / C / member_nodes / event のみ

実験者の振り分けルール (E3_contact, balance_decision, 双方向 E3, Integration 継承・再分配) で実際に参照される値:

1. 物理層 (engine.state) で発生した E1/E2/E3 event の type + 関係する link/node
2. cid 周りの Q (ledger), C (cog.C), ghost_residual_Q
3. cid 同士の hosted/ghost 状態
4. Integration への所属関係 (cid_to_integrations)

これら以外の cid 周辺記録 (disposition, タグ, 内的基準軸, capture, 自己 buffer, 他者読み) は **すべて観察データとしてのみ存在**。cid は何ら参照しない。

### 10.4 dead code の規模

- 約 5 機構 (phi/prev_phi, introspection_tags, _ingestion_log, v11_last_captured, be3_rng, integration_rng) が完全 dead
- 約 3 機構 (`_pending_ingestion_pairs`, `_observe_step_v101_compat`, `read_own_state`) が後方互換の残骸
- 削除しても系の動学に影響なし、出力 CSV の一部列が消える/残骸が綺麗になる程度

---

## 11. 整理の含意 (観察者枠組みからの読み)

### 11.1 cid を擬人化しない記述の重要性

ESDE では cid に「主観」「自己モデル」を実装していない。cid は **ランダム的な因果の発生で動く**。実験者はその動きを予測できず、後から記録を見て「こう動いていた」「こう動くらしい」と統計的に推測するに留まる。

このとき、振り分けルールに登場しない量 (Category C) は「cid が持つ性質」ではなく、**実験者が cid を描写するために付けたラベル**。例えば:

- 「cid X は社交的だ」 → 実験者が `d_social > 0.5` のとき `social` タグを cid X に付ける、という記録ルール
- 「cid X は自分を観察している」 → 実験者が cid X の番号で index した buffer に theta_birth を保存する、という記録手順
- 「cid X は他者を読む」 → E3_contact 発火時、実験者が両者の M_c の一部を相互参照ログに書き込む、という記録手順

これらは cid 自身の認識ではない。cid は自分の状態名すら知らず、event に反応するだけ。

### 11.2 「主観があるかもしれない」状態の取り扱い

機構的には cid 内部に「主観」と呼べる構造は無い。実験者が観察できるのは:

- 双方向 E3 fired 7,220 件 (v10.4 main、24 seeds): 両者が同期して event を起こした統計的痕跡
- Integration 誕生 13,550 件: 構成 cid が振り分けルールで結びつく統計的痕跡
- recorded Integration 1,998 件: 構成 cid 全員 ghost 後も C/Q が ledger に残る統計的痕跡

これらは **「cid に主観があるかもしれない」と実験者が事後的に思う材料**。否定も肯定もできない、ランダム的な因果の発生がもたらす痕跡として記録される。

### 11.3 v10.5 以降の射程 (本監査からの示唆)

実装指示書 §15 で v10.5 持ち越しとされた項目について、本監査が示すのは:

- **focus / attention_weight 動的化**: 現状 attention は decay + 加算のみで、振り分けルールの input ではない。動的化するなら「実験者がどういう event 観察規則を attention 値に依存させるか」を決める段階
- **嗜好の数理化**: v9.9 軸群が観察 only にとどまっている。実験者が「cid の振る舞いを予測する材料に v9.9 軸を使うか」を決める段階
- **CidSelfBuffer の振り分け参加**: 自己読み結果を振り分けルールの input に使う = 「cid が自分を観察する」という擬人化を機構的に成立させる方向。これは §14 規律「cid 内部に新規状態を追加しない」「主観・意識を実装しない」と緊張する
- **他者読みの拡張**: 動的状態を読み・振り分けに使えば「他者観察に基づく行動」が可能になるが、上記と同じ緊張

→ いずれも観察者枠組みを **どこまで擬人化方向にずらすか** という主題決定。本監査は「現状はずらしていない」という事実を確認したもの。

---

*以上、cid 周辺機構の使用状況監査。Taka レビューを待つ。*
