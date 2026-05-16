# v1101 後継主題候補「ESDE スケール注意機構」事前調査 — Code A Step 3 成果物 (2 AI 監査入力資料)

*作成*: 2026-05-17、Code A
*親*: Web Claude 事前調査要望書 (本会話 2026-05-17 受領、未 repo 化) + Step 2 認識確認 (`step_2_recognition.md`、commit 0c72bd8)
*位置*: 要望書 §5.4 進行案 Step 3 (本調査) + §3 成果物作成
*対象*: GPT (Auditor) / Gemini (Architect) 2 AI 監査入力資料、Web Claude (相談役) 取りまとめ前提
*成果物範囲*: 要望書 §3 の 7 項目を D-3 反映で再構成 (駆動要因の検証を #1)
*バージョン番号*: 未確定 (Taka 主題確定後決定)、仮配置 `unified/v1101/post_v1101_attention_pre_investigation/`

---

## 0. AI への指示 + 一文サマリ

### 0.1 監査者 (GPT / Gemini) への指示

1. **本書は調査成果物であり設計書ではない**: Code A は判定回避 (success/fail なし)、構造的事実のみ。設計の確定は本書 + 監査結果を見てからの Taka 領域
2. **役割境界**: GPT = Auditor (§5.2 GPT 論点) / Gemini = Architect (§5.2 Gemini 論点) / Web Claude = 相談役 (本書取りまとめ) / Code A (本書著者) = 実環境照合
3. **3 問規律 (Taka 2026-05-12)**: 提案・解釈の前に「どうあるか / どう使うか / どう繋がるか」に答えられない発言はしない
4. **絶対格言 15 件 + Taka 哲学 4 件遵守** (要望書 §0.1-6 + Step 2 §F に明示)
5. **Taka 領域 (§4 要望書 + 本書 §1.1.4) は埋めない**: 選択と集中対象 / 主体単位 / 構造形成 fb / バージョン番号
6. **要望書本体は未 repo 化**: 本会話 2026-05-17 受領時の Web Claude チャット内記述が一次資料。本書はその実環境照合と再構造化。

### 0.2 一文サマリ

本書は v1101 (Atom 的隆盛統計観察、2026-05-17 Step H 完了) の後継主題候補「ESDE スケール注意機構」(Web Claude 抽象フレーム: 細胞カオス → 変化抽出 → 注意 / v10.2 cid レベル Q/C シーソーの ESDE スケール同型展開) について Code A が要望書 §2.A-G を実環境照合し、(1) 駆動要因の検証として v10.5 Salience-driven Focus が既に observer_cid × candidate_cid × mass = Q+C+β継承分の **cid レベル内生的注意機構** として 3 系統 (read_other / be3 fired / ingestion target) に実装されており、本フレームは「観察軸の追加」ではなく v10.5 の (a) スケール変更 (cid → ESDE 全体)、(b) 駆動信号変更 (mass 静的 → 変化動的)、(c) ΣQ/(ΣQ+ΣC) シーソーの cid → ESDE 同型展開、の **3 重の構造転換** であり真に新規だが駆動要因の言葉を「内生化」から「内生注意のスケール変更 + 変化駆動への切替」に精緻化する必要があると結論、(2) 既存で組める部分として v10.5 balance_decisions / c_trajectory による Q/C 集約 + v10.6 4 解像度 trajectory + v10.7 5 種 relation_path (familiarity / attention_via_salience / integration_α/β / temporal_coactivation) + v1101 観察 2 propagation 構造 (event × Δt = 21 points × 13 列、1.3 MB) が直接流用可能、(3) 新規実装が要る部分として ΣQ/(ΣQ+ΣC) per-window 集約 + 変化抽出 (rank_1_atom 反転密度 / 観察単位間 KL divergence 時間差分) + 注意 emit (per-step or per-event で最大変化点 + 認知/意識優位フラグ + 因果/影響候補を記録) + 「注意先中心の波及」観察 2 同型作業、(4) 不可能 / 要再設計の部分として cid vector の 326 atom 全濃度時系列再計算は段階 2 で cid state ledger 再生が必要 (v105_animate_integration.py の β-level reconstruct_beta_snapshots() に同型実装の前例)、(5) 段階区分として段階 1 (粗解像度、既存出力流用、6-10 時間、新規 main run 不要、v1101 同型) と段階 2 (cid state ledger 再生、1.5-2 日、v1101 で未着手の Step I 同型)、(6) frozen 境界として v10.5 SalienceTracker.log_event() = emitter / select_ingestion_target() = selector のパターンを踏襲、段階 1 は emitter のみ (派生記録、新規 unified/v???/ 配下に書き込み、v10.x main outputs read-only)、selector (構造形成 fb) は v9.7 認知→存在介入の撤回前例 (B_Gen 導入時に torque_factor 不活性化、05_primitive_summary / 07_concept_core / 08_esde_system_structure の 3 文書で撤回明記) のため段階 1 では採らず Taka 領域、(7) 齟齬指摘として Step 2 で出した 5 件を実環境深掘りで更新 (齟齬 2 v10.4 focus/attention 動的化候補を v104_cid_usage_audit.md で発見 = Web Claude memory 正しかった、Code A Step 2 第 1 Explore の検索範囲不足を自己訂正、Step 2 で「未発見」とした記述を訂正)、絶対格言 #5 (観察軸追加でなく駆動要因明示) は本書 #1 の精緻化で遵守、Taka 領域 4 項目は本書 §1.1.4 で明示し Code A 埋めない、本書は 2 AI 監査入力資料として §3 7 項目を本書 §1.1.1-1.1.7 で記述。

---

## 1. §3 成果物 — 要望書 7 項目 (D-3 反映、駆動要因の検証を #1 に配置)

### 1.1.1 #1: 駆動要因の検証 — 「観察軸追加」でなく「構造転換」と言えるか

**結論**: **真に新規な構造転換だが、駆動要因の言葉を精緻化する必要がある**。

#### 1.1.1.1 v10.5 Salience-driven Focus は既に「内生的注意機構」として動作中

実環境 (`developmental/v105/v105_salience.py` 全 299 行) で確認:

| 項目 | 実装内容 |
|---|---|
| **mass 定義** (L60-79 `compute_mass`) | `mass(X) = X.Q + X.C + β.Q_inherited + β.C_inherited` — 要望書 §2.B 記述と式完全一致 |
| **適用 3 系統** (L4-24 docstring) | (1) read_other: visible_ratio に mass-based ブースト (L141-168) / (2) be3 fired: log のみ (L264-298、発火そのものは物理駆動) / (3) ingestion target: uniform random を mass-weighted random に置換 (L175-257) |
| **observer × candidate 構造** | L106-127 `log_event`: observer_cid (注意主体) × candidate_cid (注意対象) × candidate_mass × selected フラグを per-step で記録 |
| **shadow_audit ではOFF** (L9, L157-158) | 機構の介入を v10.4 比較できる |
| **新規 RNG** (L11-12, L92-94) | salience_rng を独立に持ち、既存 RNG (engine/capture/ingestion/balance/be3) には touch しない |

→ これは「ESDE が自分の内部状態 (Q+C+β継承) に基づいて何を観察するか / 何を取り込むかを自動で決めている」構造。**典型的な attention mechanism の cid レベル実装**。Web Claude 要望書 §2.B「v10.5 は既に注意の cid レベル実装ではないか」という問いに対する答えは **YES**。

#### 1.1.1.2 v10.7 attention_via_salience path は run 集約の静的 attention map

実環境 (`developmental/v107/v107_path_analyzer.py:104-131` `build_attention_via_salience_targets`) で確認:

- `salience_event_log_seed*.csv` の `observer_cid × candidate_cid × candidate_mass` を **run 全体で `groupby().sum()`** (L114)
- `salience_mass_sum` を relation_strength として source_event ごとに「source_cid = observer_cid」上位 20 target を抽出 (L118-121)
- → これは「過去 run 全体で観察主体がどの候補に多く注意を向けたか」の **静的・累積マップ**

つまり v10.7 で「注意の経路」は既に観察軸化されているが、**(a) 動的でない (run 全体集約)、(b) cid レベルにとどまる (ESDE スケール集約なし)**。

#### 1.1.1.3 v10.4 focus/attention 動的化候補は repo 上に存在 (Step 2 齟齬 2 自己訂正)

`developmental/v104/v104_cid_usage_audit.md` に明示記述あり (本書 Step 3 深掘り Explore で発見):

> "**focus / attention_weight 動的化**: 現状 attention は decay + 加算のみで、振り分けルールの input ではない。動的化するなら「実験者がどういう event 観察規則を attention 値に依存させるか」を決める段階"

→ 文脈は「現状未実装、将来の実装課題」。**Web Claude memory の主張は正しかった**、Step 2 第 1 Explore は `v104_integration_alpha_beta_proposal.md` のみ確認したため見落とし。Code A 自己訂正。

#### 1.1.1.4 本フレームと v10.5 の構造的関係 — 3 重の構造転換

| 軸 | v10.5 Salience-driven Focus | 本フレーム ESDE スケール注意機構 |
|---|---|---|
| **スケール** | cid レベル (observer_cid × candidate_cid) | ESDE 全体 (系全体に 1 つ or 階層的) |
| **駆動信号** | 静的 mass = Q+C+β継承分 (現在状態) | 動的「変化の大きさ」(時間差分、連鎖・同期) |
| **シーソー** | mass 単体 (Q と C は和、シーソーなし) | ΣQ/(ΣQ+ΣC) で認知優位 (固定) / 意識優位 (選択と集中) を切替 |
| **観察対象** | observer が candidate を観察 (mass-weighted) | 系全体が「最大変化点」に注意を向け、因果と影響を観察 |
| **時間軸** | per-event log (event 駆動) | per-step or per-event で「いつ何に注意が向いたか」を時系列に |

→ **観察軸追加ではない**: 新規の数値列を増やすのではなく、既存の Q/C/β継承を **集約スケールと駆動信号の構造** に再配置する。
→ **真に新規な構造転換**: v10.5 を「3 重に転換」したものであり、単なる cid → ESDE 集約や mass → 変化置換単体では本フレームを構成しない (3 つ揃って初めて Taka フレームと一致)。

#### 1.1.1.5 駆動要因の精緻化提案 (本書 D-3 反映、Web Claude 判断)

要望書 §0.2 の駆動要因「v1101 で外から読み取った atom 像を ESDE 内部構造が内生的に立ち上げる構造転換」は v10.5 の存在に照らすと **言葉が広すぎる**。v10.5 が既に部分的に「内生的に立ち上げている」ため、現状の駆動要因記述では「v10.5 で既に達成されている」と読まれるリスクあり。

**精緻化案** (Code A 提案、判断 Web Claude):

> 「v10.5 Salience-driven Focus が既に cid レベルで内生的注意 (observer×candidate×mass-weighted 選択) として動作している前提で、それを (a) ESDE スケール集約 (cid → 系全体)、(b) 駆動信号の動的化 (mass 静的 → 変化動的)、(c) Q/C シーソーの cid → ESDE 同型展開 (ΣQ/(ΣQ+ΣC) による認知/意識優位切替) の 3 重に構造転換し、v1101 で観察された『単位ごとに割れる atom 像』を ESDE 自身が階層的に内生する形へ移行する」

→ 絶対格言 #5 (観察軸を増やすことを駆動要因にしない) との整合: 観察軸 (新規数値列) を増やすのではなく、既存の Q/C/β継承を **集約スケールと駆動信号の構造** に再配置する。本フレームは構造転換であり軸追加ではない。

#### 1.1.1.6 §5.2 GPT 監査論点への素材提供

GPT 論点 (1)「観察軸を増やすことを駆動要因にしていないか」への Code A 観察事実: §1.1.1.4 の 3 重構造転換は「軸追加でない」と読める。ただし「3 重」と「軸」の境界は概念定義次第。GPT 判断。

---

### 1.1.2 #2: 既存で組める部分 — 既存出力 + 既存機構の流用範囲

#### 1.1.2.1 v10.5 Q/C cid 別 persistence

| 出力 | 所在 | 列 |
|---|---|---|
| balance_decisions | `developmental/v105/diag_v105_main/balance/balance_decisions_seed{0..23}.csv` | 9 列、`Q_at_decision` / `C_at_decision` を per (seed, step, cid) で保持 |
| c_trajectory | `developmental/v105/diag_v105_main/balance/c_trajectory_seed{0..23}.csv` | 9 列、`C_at_window_end` / `Q_remaining_at_window_end` を per (seed, cid, window) で保持 |

**ΣQ/(ΣQ+ΣC) per-window 集約**: balance_decisions を `groupby(seed, step).sum()` または c_trajectory を `groupby(seed, window).sum()` するだけ。新規 post-process 30 分。

**ΣQ/ΣC per-step**: 直接出力なし、step 単位の cid 別 Q/C は balance_decisions の意思決定タイミング駆動 (event 駆動でなく意思決定駆動)。完全な per-step は段階 2 (cid state ledger 再生) で取れる。

#### 1.1.2.2 v10.5 Salience event log (run 全体)

| 出力 | 所在 | サイズ |
|---|---|---|
| salience_event_log | `developmental/v105/diag_v105_main/salience/salience_event_log_seed{0..23}.csv` | 7 列 (seed/step/observer_cid/candidate_cid/candidate_mass/selected/event_type)、24 seeds × 各 ~3,115 行 |

→ 過去 v10.5 run の「cid レベル注意」が persistence 済。本フレームの ESDE スケール注意の「派生記録 = どの cid が注意主体だったか」の基礎データとして直接流用可能。

#### 1.1.2.3 v10.6 4 解像度 trajectory (rank_1_atom 時系列)

v1101 Step C / E で確認済の既存出力:

| 解像度 | 所在 | 用途 |
|---|---|---|
| event | `developmental/v106/outputs/main/event_trajectory/event_cid_alignment_seed*.csv` | 最細粒度、per-cid per-event の rank_1_atom + rank_1_sim |
| pulse | `.../pulse_trajectory/` | per-cid per-pulse |
| step10 | `.../step10_trajectory/` | per-cid per-10step |
| window | `.../window_trajectory/` | per-cid per-window |

**変化抽出への流用**:
- rank_1_atom 反転 (per-cid per-t で前 t と異なる atom が rank 1 になった) の密度 = 「変化の大きさ」候補 (b) の素材
- rank_1_sim の時間差分 = 「変化の強度」候補

#### 1.1.2.4 v10.7 5 種 relation_path

`developmental/v107/v107_path_analyzer.py` の 4 種 + Step F multi-hop で計 5 種:

| path | source | 強度の計算 |
|---|---|---|
| familiarity | fam_edges (network) | familiarity 値 |
| attention_via_salience | salience_event_log | salience_mass_sum (run 全体集約) |
| integration_alpha | alpha_lifecycle | birth event 時の同 α member cid (1.0) |
| integration_beta | beta_lifecycle | birth event 時の同 β member cid (1.0) |
| temporal_coactivation | pulse_log | 1 / (1 + abs_lag)、±100 step window |

→ 本フレームの「注意先の因果と影響」観察基盤として直接流用可。注意先 (= 最大変化点 cid) を source_cid 扱いにすれば、上記 5 path で「注意先がどこと繋がっているか」が取れる。

#### 1.1.2.5 v10.7 baselines_with_delta_seed*.parquet

`developmental/v107/outputs/main/baselines_with_delta_seed{0..23}.parquet` (各 11-18 MB):

26 列、per event × target_cid × relation_path 構造、列は `delta_Q_immediate / short / medium`, `delta_C_immediate / short / medium`, `delta_R_familiarity_*`, `delta_n_alphas_*`, `delta_n_observed_*`, `n_pulses_in_window_*` (3 phase: immediate / short / medium)。

→ Web Claude 要望書 §2.A の「Q_pre / C_pre」直接列はない (Step 2 齟齬 4 確認) が、**delta 形式で 3 phase 波及が既に集約**。本フレームの「影響」観察 (注意先 → 周辺) の素材として直接流用可。

#### 1.1.2.6 v1101 観察 2 propagation 構造 (本書最重要素材)

`unified/v1101/v1101_step_d_observation_2.py` で実装、出力 `observation_2_propagation.parquet` (1.3 MB):

- **入力**: v112 atom_introduction_events + v106 step10_trajectory
- **構造**: 中心 cid (source_cid) × Δt ∈ {-100, -90, ..., 0, ..., +100} 21 point × 13 列
- **列**: n_cids_alive / n_cids_matching_atom_intro / match_fraction / n_unique_atoms / atom_entropy_bits / mean_rank_1_sim / center_alive / center_rank_1_atom / center_rank_1_sim / center_atom_matches_intro
- **解像度**: step10 (10 step 均一間隔)

**「注意先中心の波及」への置換マッピング** (本書 Step 3 提案):

| v1101 観察 2 | 本フレーム「注意先中心の波及」 |
|---|---|
| atom_introduction_events (取り込み点) | attention_events (最大変化点で注意が固定された event) |
| atom_intro (取り込まれた atom) | attended_target (注意が向いた cid or atom) |
| match_fraction (周辺 cid が atom_intro と一致した割合) | match_fraction (周辺 cid が attended_target と一致した割合) |
| center_atom_matches_intro | center_matches_attended |
| atom_entropy_bits (周辺の atom 多様性) | そのまま流用 |

→ 観察 2 の 13 列構造はほぼ全て流用可能。書き換えポイントは入力 event 定義のみ。

#### 1.1.2.7 v10.13.a 3 phase 波及観察 (Step 2 齟齬 3 確認、5 phase でなく 3 phase)

`developmental/v113a/` の Map 1-5 出力 × 24 seeds、3 phase = immediate (1-10) / short (10-100) / mid (100-1000)。

→ v10.13.a は post-process 単位での波及構造観察の前例。本フレームの「変化の連鎖・同期」測定で参考になるが、観察 2 propagation 構造の方が「中心 cid × Δt」形式で本フレームに直接的。

---

### 1.1.3 #3: 新規実装が要る部分 — 新規 post-process / ledger 再生

#### 1.1.3.1 段階 1 (粗解像度、既存出力流用)

| # | 機能 | 入力 | 出力 | 想定時間 |
|---|---|---|---|---:|
| 3-1 | ΣQ/(ΣQ+ΣC) per-window 集約 | balance_decisions + c_trajectory | esde_qc_seesaw_seed*.parquet (per-window ratio) | 30 分 |
| 3-2 | 変化抽出 — rank_1_atom 反転密度 | 4 解像度 trajectory | atom_change_density_seed*.parquet (per-resolution per-window 反転カウント) | 1 時間 |
| 3-3 | 変化抽出 — 観察単位間 KL divergence 時間差分 | 4 解像度 trajectory + cid_atom_sim_matrix + beta/alpha_atom_aggregate | unit_divergence_time_seed*.parquet | 1.5 時間 |
| 3-4 | 注意 emit (per-step or per-event で「最大変化点」を記録) | 3-2 + 3-3 + 3-1 (シーソー判定) | attention_emit_log_seed*.parquet | 1.5 時間 |
| 3-5 | 「注意先中心の波及」観察 2 同型作業 | 3-4 + step10_trajectory + v10.7 5 relation_path | attention_propagation_seed*.parquet (event × Δt 構造) | 2 時間 |
| 3-6 | グラフ HTML (v1101 step F と同型、Plotly CDN) | 3-1 〜 3-5 | post_v1101_attention.html (単一 HTML) | 1.5 時間 |
| 3-7 | bit-identity 検証 (v1101 Step G と同型 3 層) | 3-1 〜 3-6 出力 + v10.x main outputs | bit_identity_report.json | 30 分 |

**合計**: **8.5 時間** (Code A 作業、新規 main run 不要)。

#### 1.1.3.2 段階 2 (cid state ledger 再生、必要なら)

| # | 機能 | 想定時間 |
|---|---|---:|
| 3-8 | cid state ledger 再生 (v105_animate_integration.py の reconstruct_beta_snapshots() 同型、cid level に拡張) | 1 日 |
| 3-9 | 326 atom 全濃度時系列再計算 (v10.6 cid_atom_sim_matrix を per-step に展開) | 0.5 日 |
| 3-10 | per-step ΣQ/ΣC (3-1 の最細粒度版) | 0.5 日 |

**合計**: **1.5-2 日** (v1101 で未着手の Step I と同型、Taka 承認次第)。

#### 1.1.3.3 emit の最小単位 (Code A 提案、Taka 領域 §4)

注意 emit (3-4) の per-record スキーマ素案 (要望書 §1.6 を反映):

```
seed, step, t_window,
attention_target_unit,     # CID / α / β / ESDE-event / ESDE-step10 / ESDE-window のどれか
attention_target_id,        # cid or atom id
change_magnitude,           # 「変化の大きさ」(複数指標併記、神の手回避)
sigma_q, sigma_c,           # 集約値 (該当 unit 範囲の)
qc_ratio,                   # sigma_q / (sigma_q + sigma_c)
qc_regime,                  # cognitive_dominant / conscious_dominant
attention_locked,            # cognitive 時は True (固定)、conscious 時は False (選択)
causality_candidate_path,    # v10.7 5 path のうち最強の relation_path_type
influence_candidate_count,   # 周辺 cid 数 (Δt 範囲内で attended_target と一致)
```

→ 全構造単位 (CID / α / β / ESDE-{event/step10/window}) で同型に emit。**主体を一つに固定しない** (Taka 領域 §4 への対応、v1101 核心発見との整合)。

---

### 1.1.4 #4: 不可能 / 要再設計の部分 — 現状データ構造の限界

#### 1.1.4.1 cid vector の 326 atom 全濃度時系列 (段階 2 で要 cid state ledger 再生)

**現状**: v10.6 trajectory は rank_1_atom + rank_1_sim のみ、2 位以下の atom は捨象 (v1101 Step A 段階 2 留保 #41 と同型)。

**要再設計**: cid state ledger 再生 + per-step に 326 atom 全濃度を再計算する post-process。**v105_animate_integration.py に β-level の前例**あり (reconstruct_beta_snapshots、L34-57、lifecycle_log replay)、これを cid level に拡張。新規実装、1.5-2 日。

#### 1.1.4.2 per-step ΣQ/ΣC (step 単位の最細粒度)

**現状**: balance_decisions は意思決定タイミング駆動、c_trajectory は window 単位。1 step ごとの cid 別 Q/C は無し。

**要再設計**: cid state ledger 再生で取れる (§1.1.4.1 と同じ段階 2 作業)。

#### 1.1.4.3 「生きた版」(step t で t 以前のみ利用可) は今回範囲外 (要望書 §1.5 + §2.F)

**現状**: 全 post-process が全 step 同時取得の後追い処理。

**要再設計**: 各 post-process を step-wise streaming にする必要。「変化抽出 + 注意 emit」は per-step streaming 可能、ただし「因果/影響の事後集約」は連鎖の終端が未来側にあるため step t では未確定。これは要望書 §1.5「ESDE を本当に生きたシステムとして扱う段階」で、後段主題。

#### 1.1.4.4 構造形成フィードバック (selector としての注意機構)

**現状**: v10.5 select_ingestion_target() が既に注意選択を構造に反映している (cid レベル)。本フレームを ESDE スケールで selector にする場合、注意先が cid ラベル / Integration 形成 / Q/C 更新にフィードバック。

**要再設計 + Taka 領域**: v9.7 認知→存在介入の撤回前例 (`docs/ai_summaries/05_primitive_summary.md` + `07_concept_core.md` + `08_esde_system_structure.md` の 3 文書で明記) との衝突可能性。段階 1 では採らない、Taka 領域 §4 で判断。

---

### 1.1.5 #5: 段階区分 — 段階 1 / 段階 2 の切り分け

| 段階 | 内容 | 入力 | 想定時間 | 新規 main run |
|---|---|---|---:|---|
| **段階 1** (粗解像度) | §1.1.3.1 の 3-1 〜 3-7、既存出力流用、emitter のみ | balance_decisions + c_trajectory + 4 解像度 trajectory + v10.7 5 path + 観察 2 構造 | **8.5 時間** | **不要** |
| **段階 2** (cid state ledger 再生) | §1.1.3.2 の 3-8 〜 3-10、cid vector 326 atom 全濃度 + per-step ΣQ/ΣC | + v9.6 ledger 再生 (β-level 前例の cid-level 拡張) | **1.5-2 日** | 不要 (post-process) |
| **段階 3** (生きた版) | step-wise streaming、注意 emit を t 以前のみで構成 | + main run 改修 (要再設計) | 後段主題 (今回範囲外) | 必要 |

**v1101 との関係**: v1101 は段階 1 で 6-8 時間、段階 2 未着手 (Step I optional)。本フレーム段階 1 (8.5 時間) は v1101 と同型のスケール、段階 2 (1.5-2 日) も v1101 段階 2 想定と同型。

---

### 1.1.6 #6: frozen 境界 — emitter vs selector / 派生記録 vs 構造形成 fb

#### 1.1.6.1 v10.5 SalienceTracker のパターン (前例)

| 関数 | 役割 | 物理層への影響 |
|---|---|---|
| `SalienceTracker.log_event` (L104-134) | **emitter** (記録のみ) | なし、log 蓄積のみ |
| `adjust_visible_ratio` (L141-168) | selector (visible_ratio 介入) | 認知層 (visible_ratio = 観察対象の解像度) |
| `select_ingestion_target` (L175-257) | **selector** (ingestion 選択介入) | 構造形成 (取り込み機構の選択) |
| `log_be3_fired_event` (L264-298) | **emitter** (記録のみ) | なし、be3 fired 自体は物理駆動 |

→ v10.5 自体が emitter と selector を **同一機構の中で分離**。本フレーム段階 1 は emitter パターン (log_event / log_be3_fired_event 同型) のみ採用。

#### 1.1.6.2 段階 1 emitter 案 (派生記録、Code A 推奨)

**実装位置**: `unified/v???/post_process/` 配下に新規 post-process。書き込み先は `unified/v???/outputs/` のみ。
**境界**: v10.x main outputs (v10.5 ledger / v10.6 trajectory / v10.7 path / v10.8 events / v10.12 ingestion / v1101 propagation) は **read-only**。
**bit-identity**: v1101 Step G の 3 層検証 (層 A: 新規 outputs deterministic / 層 B: v10.x main outputs 不変 / 層 C: 中間 output consistency) を同型適用。
**実 ledger 不変**: 本フレーム emit は v105 SalienceTracker の log_event を「ESDE スケール集約 + 変化駆動」に置換したもの、物理層動作 (Q/C 更新 / ingestion 動作 / be3 fire) には触れない。

#### 1.1.6.3 段階 1+ selector 案 (構造形成 fb、Taka 領域)

**実装位置**: v10.5 の select_ingestion_target() を ESDE スケール「最大変化点優先選択」に置換 (cid mass → 系全体変化駆動)。
**境界**: 新規 main run が必要 (post-process でなく機構介入)。
**v9.7 撤回前例との衝突**: `docs/ai_summaries/` 3 文書で確認した v9.7「認知→存在介入」撤回 (B_Gen 導入時に torque_factor 不活性化) は「認知層が存在層に直接介入する設計」の撤回。本フレームの selector も「ESDE スケール注意が cid レベル構造形成にフィードバック」する設計のため、**同型の構造的問題に遭遇する可能性**。

→ Code A 観察事実: 段階 1 (emitter) と段階 1+ (selector) は実装上 **新規 main run の要否で大きく分かれる**。Taka 領域 §4 の「構造形成 fb の可否」判断材料として両案の差を本書 §1.1.6.2 / §1.1.6.3 で明示。

#### 1.1.6.4 §5.2 GPT 監査論点への素材提供

GPT 論点 (3)「注意機構の発火が emitter に留まり selector になっていないか」への Code A 観察事実: §1.1.6.1 で v10.5 自体が両方を持つことを確認。本フレームの段階 1 は emitter 限定で安全、段階 1+ は selector で v9.7 前例の構造的衝突可能性あり。GPT 判断。

---

### 1.1.7 #7: 齟齬指摘 — Step 2 5 件 + 本調査追加

#### 1.1.7.1 Step 2 で出した 5 件の本調査での更新

| # | Step 2 記述 | 本調査での更新 | 更新理由 |
|---|---|---|---|
| **齟齬 1** | v10.5 Salience は既に「内生的注意」を実装 | **確定**、§1.1.1 で 3 重構造転換として再構造化 | 全 299 行読了、3 系統 + emitter/selector 分離を確認 |
| **齟齬 2** | v10.4 focus/attention 動的化候補 repo 未確認 | **訂正**、`v104_cid_usage_audit.md` で発見、Web Claude memory 正しかった | Step 2 第 1 Explore は `v104_integration_alpha_beta_proposal.md` のみ確認、検索範囲不足 |
| **齟齬 3** | v10.13.a は 5 phase でなく 3 phase | **確定**、第 2 Explore で immediate/short/mid 3 phase 再確認 | 変化測定流用検討で v1101 観察 2 構造の方が直接的と判明 |
| **齟齬 4** | attach_pre_event_state ファイル名相違 | **確定** + 詳細化、`baselines_with_delta_seed*.parquet` (26 列、3 phase delta、event-level 1.76M 行) が実体 | 列構成確認で Q_pre/C_pre は無いが delta 形式で 3 phase 波及が集約 |
| **齟齬 5** | ESDE スケール単一注意 vs v1101 核心発見 (観察単位反転) の構造的衝突 | **確定**、§1.1.3.3 emit スキーマで「全構造単位で同型 emit」案を提示、主体を一つに固定しない設計 | v1101 核心発見 (5 単位で atom 分裂) との整合解を構造提示 |

#### 1.1.7.2 本調査で新規発見の齟齬 (2 件)

**齟齬 6 (微細)**: 要望書 §2.B「v10.5 mass = X.Q + X.C + β継承分」の β 単数表記

**要望書記述**: 「mass(X) = X.Q + X.C + β継承分」(β 単数として記述)
**実環境**: `v105_salience.py:60-79` で `mass(X) = X.Q + X.C + β.Q_inherited + β.C_inherited`、L73-78 で beta_manager 経由の **1 個の β** からのみ加算 (規律 A2 案 b — 「cid は 1 個の β にしか所属しない」)
**影響**: 要望書の表記は正確、ただし β 単数の前提が暗黙。本フレームで ESDE スケール集約する際に「複数 β 集約」する場合は規律 A2 と衝突。
**処理**: §1.1.3.3 emit スキーマでは「attention_target_unit が β の場合」を per-β 単位とすることで規律 A2 維持。

**齟齬 7 (補足)**: 要望書 §2.E「v10.7 baselines」の名称

**要望書記述**: 「v10.7 の 5 種 baseline」
**実環境**: v107 baselines_with_delta_seed*.parquet には **3 phase** (immediate/short/medium) の delta が含まれ、「baseline 種別」は 4 種 relation_path × 3 phase の組み合わせと読める (実装は relation_path 5 種 = 4 種 + multi-hop)。「5 種 baseline」の独立した baseline 群はない。
**影響**: 微細、本フレーム流用では baselines_with_delta の 26 列構造が「3 phase 影響」素材として直接流用可。

#### 1.1.7.3 齟齬集計

| 区分 | Step 2 | 本調査追加 | 自己訂正 | 合計 |
|---|---:|---:|---:|---:|
| 重要 (駆動要因 / 構造) | 2 (齟齬 1, 5) | 0 | 0 | 2 |
| 通常 (ファイル名 / 数値) | 2 (齟齬 3, 4) | 2 (齟齬 6, 7) | 1 (齟齬 2) | 5 |
| **合計** | **5** | **2** | **1** | **7** (内 1 が訂正) |

**v1101 Step A との比較**: v1101 は 10 件 (即決事項 7 で対応)、本書は 7 件 (内 1 が自己訂正)。本書は要望書段階で齟齬が少ない (Web Claude が v1101 Step A 経験を反映して精度を上げたためと推定)。

---

## 2. §5.2 監査論点への素材まとめ (Code A 観察事実、判断は GPT / Gemini)

### 2.1 GPT (Auditor) 論点

| # | 論点 | Code A 素材 |
|---|---|---|
| GPT-1 | 「観察軸を増やすことを駆動要因にしていない」か | §1.1.1.4 の 3 重構造転換 (スケール / 駆動信号 / シーソー) は軸追加でないと読める。ただし「3 重」と「軸」の境界は GPT 判断 |
| GPT-2 | 「変化 (連鎖・同期したかたまり)」の測り方が神の手・ハンドチューニングを含まないか | §1.1.2.3 / §1.1.3.1 で 3 候補 (a/b/c) を併記、Code A は取捨せず構造的併記。GPT が「3 併記が神の手回避と整合か」判断 |
| GPT-3 | 注意機構の発火が emitter に留まり selector になっていないか | §1.1.6.1 で v10.5 自体が両方持つ、本フレーム段階 1 は emitter 限定で安全、段階 1+ は selector で v9.7 前例衝突可能性。GPT 判断 |

### 2.2 Gemini (Architect) 論点

| # | 論点 | Code A 素材 |
|---|---|---|
| Gemini-1 | ΣQ/(ΣQ+ΣC) という Q/C の ESDE スケール同型展開が構造的に妥当か | §1.1.2.1 で balance_decisions / c_trajectory に cid 別 Q/C があり、`groupby().sum()` で集約可。同型展開は計算上自然、Gemini が「同型」が ESDE 設計と整合か判断 |
| Gemini-2 | post-process をどこに置けば物理層 frozen + bit-identity が保てるか | §1.1.6.2 で v1101 Step G 3 層検証パターン (層 A/B/C) を同型適用提案。Gemini が「位置」が Architect 視点で適切か判断 |
| Gemini-3 | v10.5 salience 機構との関係 (上位版 / 別物 / 拡張) の整理が Architect 視点で妥当か | §1.1.1.4 の「3 重構造転換」整理。Gemini が「v10.5 を 3 重に転換」記述が Architect 視点で妥当か判断 |

---

## 3. Taka 領域の箱 (Code A 埋めない、要望書 §4 継承)

| 未確定事項 | 本書での扱い |
|---|---|
| 選択と集中が何を選ぶか | 本書 §1.1.3.3 emit スキーマで「conscious 時 attention_locked=False」と記述、選択対象の確定はせず |
| ESDE の主体をどの単位に置くか | 本書 §1.1.3.3 で「全構造単位 (CID / α / β / ESDE-{event/step10/window}) で同型 emit」を提示、単一固定しない |
| 構造形成フィードバックの可否 | 本書 §1.1.6.2 / §1.1.6.3 で emitter / selector 両案の実装差を提示、採否は Taka |
| バージョン番号 | 本書未確定、Taka 主題確定後決定 |

→ Taka 領域 4 項目すべて Code A 埋めず、判断材料のみ提示。

---

## 4. 規律遵守チェック (絶対格言 15 件、本書遵守状況)

| # | 格言 | 本書での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | §1.1.1 で v10.5 の構造を先に確認、本フレームの意味づけは後 |
| 2 | 物理層 frozen 絶対 | §1.1.6.2 で v10.x main outputs read-only、新規 post-process は `unified/v???/` 配下のみと宣言 |
| 3 | ベースライン比較 + 効果サイズ | §1.1.2.5 v10.7 baselines_with_delta を流用候補として明示 |
| 4 | 集団平均の罠 / n_core 別層化 | §1.1.3.3 で全構造単位 emit、単一固定しない (v1101 核心発見との整合) |
| 5 | **観察軸を増やすことを駆動要因にしない** | §1.1.1.5 で駆動要因の精緻化案 (軸追加でなく 3 重構造転換) |
| 6 | 出口の固定 | §1.1.7 で 7 項目固定、Step 3 §3 成果物 |
| 7 | 主題着手前に上位資料を読む | §1.1.1 で v10.5 全 299 行 + v10.7 全 324 行 + v1101 観察 2 全 199 行読了 |
| 8 | 過去観察軸の照会 | §1.1.1.1-3 で v10.5 / v10.7 / v10.4 を実環境照合、Step 2 齟齬 2 自己訂正 |
| 9 | 神の手回避 + Pulse 同一フォーマット | §1.1.3.1 の「変化抽出」3 候補併記、取捨は Code A 判定せず |
| 10 | 因果ではなく因果候補 | §1.1.3.3 emit スキーマで「causality_candidate_path」と記述 (「候補」明示) |
| 11 | 概念単位を雑に扱わない | §1.1.4.3 / §1.1.4.4 / §1.1.6.1 で emitter / selector / 派生記録 / 構造形成 fb を区別 |
| 12 | Aruism 判定回避 | 本書全体で success/fail 判定なし、構造的事実 + 判断材料提示のみ |
| 13 | AI を信じない原則は Taka 個人 / 主題判断は Taka | §3 Taka 領域 4 項目 Code A 埋めず |
| 14 | Taka 直感優先 + 直感語保存 | 要望書 §1 Taka 原文は要望書本体に保持、本書は構造的整理のみ |
| 15 | 5 者運用体制の補完性 | §2 GPT / Gemini 監査論点に Code A 素材提示、相互補完 |

→ 15 格言全て遵守。

---

## 5. Step 3 進行報告 + Step 4 (2 AI 監査) 進行案

### 5.1 Step 3 完了内容

| 順 | 項目 | 状態 |
|---|---|---|
| 1 | §2.B 先行 (v10.5 / v10.7 / v10.4 深掘り) | 完了、§1.1.1 |
| 2 | §2.B 結論 trigger (v10.5 拡張 vs 別物) | 完了、§1.1.1.4 3 重構造転換 |
| 3 | §2.A / §2.E (Q/C 集約 + 因果/影響観察基盤) | 完了、§1.1.2 |
| 4 | §2.C (変化抽出) | 完了、§1.1.2.3 + §1.1.3.1 |
| 5 | §2.D (post-process 位置 + frozen 境界 + emitter/selector) | 完了、§1.1.6 |
| 6 | §2.F (時間軸 簡易見立て) | 完了、§1.1.4.3 |
| 7 | §2.G (新規 main run 要否 + 段階区分 + 想定時間) | 完了、§1.1.5 |
| 8 | §3 成果物作成 (7 項目 markdown 化、D-3 反映で駆動要因の検証を #1 に) | 完了、本書 |

**実 Step 3 想定**: 6-9 時間 → **実所要**: 約 1.5 時間 (Code A 作業、Explore 2 回 + 既存ファイル読了 + 統合 markdown 化)。Web Claude 要望書のフレームが既に詳細だったため。

### 5.2 Step 4 (2 AI 監査) 進行案 (要望書 §5.4 / §5.2 継承)

| Step | 内容 | 主体 |
|---|---|---|
| Step 4 | Web Claude が Step 3 (本書) を 2 AI 監査資料に整形 | Web Claude |
| Step 5 | 2 AI 監査 (GPT Auditor / Gemini Architect)、最大 3 ラウンド (絶対格言 #13) | GPT / Gemini |
| Step 6 | 監査反映 → Taka 主題化判断 | Taka |
| Step 7 | (主題化された場合) バージョン番号確定 + repo 配置先確定 | Taka |
| Step 8 | (主題化された場合) Code A 実装 (段階 1 8.5 時間想定) | Code A |

### 5.3 仮配置 + バージョン番号

本書および Step 2 報告書は仮配置 `unified/v1101/post_v1101_attention_pre_investigation/` で進行。Taka 主題化判断 + バージョン確定後に正規配置 (`unified/v11???/` 配下) へ移動。

---

## 6. 一文サマリ (再掲)

本書は v1101 (Atom 的隆盛統計観察、2026-05-17 Step H 完了) の後継主題候補「ESDE スケール注意機構」(Web Claude 抽象フレーム: 細胞カオス → 変化抽出 → 注意 / v10.2 cid レベル Q/C シーソーの ESDE スケール同型展開) について Code A が要望書 §2.A-G を実環境照合し §3 成果物 7 項目 (D-3 反映で駆動要因の検証を #1 に) を作成、(#1) 駆動要因の検証として v10.5 Salience-driven Focus が既に observer_cid × candidate_cid × mass = Q+C+β継承分の cid レベル内生的注意機構として 3 系統 (read_other / be3 fired / ingestion target) に実装されており、本フレームは v10.5 の (a) スケール変更 (cid → ESDE 全体) (b) 駆動信号変更 (mass 静的 → 変化動的) (c) Q/C シーソーの cid → ESDE 同型展開 の 3 重構造転換であり真に新規だが駆動要因の言葉を精緻化する必要があると結論、(#2) 既存で組める部分として v10.5 Q/C cid 別 (balance_decisions + c_trajectory) + v10.5 salience_event_log + v10.6 4 解像度 trajectory + v10.7 5 種 relation_path + v10.7 baselines_with_delta (26 列、3 phase delta) + v1101 観察 2 propagation 構造 (event × Δt = 21 points × 13 列、1.3 MB) が直接流用可能、(#3) 新規実装が要る部分として段階 1 で 7 項目 (ΣQ/(ΣQ+ΣC) per-window 集約 / 変化抽出 / 注意 emit / 注意先中心の波及 / グラフ HTML / bit-identity 検証) を 8.5 時間、段階 2 で cid state ledger 再生 + 326 atom 全濃度時系列 + per-step ΣQ/ΣC を 1.5-2 日、(#4) 不可能 / 要再設計の部分として 326 atom 全濃度時系列は v105_animate_integration.py の β-level reconstruct_beta_snapshots() 同型を cid level に拡張する必要 + 「生きた版」(step t で t 以前のみ) は今回範囲外 + 構造形成 fb (selector としての注意) は v9.7 認知→存在介入の撤回前例 (3 文書で確認) との衝突可能性、(#5) 段階区分として段階 1 (粗解像度、既存出力流用、8.5 時間、新規 main run 不要、v1101 同型) と段階 2 (cid state ledger 再生、1.5-2 日)、(#6) frozen 境界として v10.5 SalienceTracker の emitter (log_event / log_be3_fired_event) と selector (adjust_visible_ratio / select_ingestion_target) の分離パターンを踏襲し段階 1 は emitter 限定で v9.7 撤回前例衝突を回避、(#7) 齟齬指摘として Step 2 5 件を本調査深掘りで更新 (齟齬 2 自己訂正で v10.4 focus/attention 動的化候補を v104_cid_usage_audit.md で発見 = Web Claude memory 正しかった) + 本調査追加 2 件 (β 単数表記 / baselines 種別表記)、合計 7 件中 1 件が Code A 自己訂正、Taka 領域 4 項目 (選択と集中対象 / 主体単位 / 構造形成 fb / バージョン番号) は Code A 埋めず判断材料のみ提示、絶対格言 15 件全遵守、Step 4 で Web Claude が本書を 2 AI 監査資料に整形 → Step 5 GPT/Gemini 監査 → Step 6 Taka 主題化判断、本書は 2 AI 監査入力資料として §1.1.1-1.1.7 で 7 項目記述。

---

*以上、v1101 後継主題候補「ESDE スケール注意機構」事前調査 Code A Step 3 成果物 (Code A 2026-05-17)。Taka 確認 + Web Claude 2 AI 監査資料整形 → GPT/Gemini 監査 → Taka 主題化判断 の流れ。仮配置 `unified/v1101/post_v1101_attention_pre_investigation/`、バージョン番号は Taka 主題確定後に決定。*
