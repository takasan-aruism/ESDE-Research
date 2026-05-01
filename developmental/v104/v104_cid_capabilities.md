# cid (Cognitive ID) を巡る記録機構の現状 (v10.4 時点)

*作成*: 2026-04-30、Claude Code (改訂)
*対象*: `developmental/v104/` 時点で実験者が cid 周りに記録している量と、cid の挙動を観察する機構の整理
*親資料*: v104_main_run_report.md、v104_phase_design.md

---

## 0. 観察者枠組み (重要な前提)

**ESDE では cid 自身が自分を「視る」状況を定義しない**。

人間の意識が科学的に定義できないのと同じ理由で、cid の意識も定義できない。客観的に言えるのは「物理層 (engine.state) がこう変化した」「cid が関わる event がこう発生した」という観察事実だけ。実験者ができるのは:

1. それを記録する (各種 CSV)
2. 統計的に処理する (post-process)
3. 「きっとこう動いているのだろう」と推測する (主題ドキュメント)

### 0.1 認知層・意識層は実験者の事前定義

「**認知層**」「**意識層**」は cid が持つ内部属性ではなく、**実験者が「cid が受信できる範囲」「決定に関わる範囲」をそれぞれ先回りして定義した区分**。事後にラベルを貼るのではなく、**事前に「これは認知側、これは意識側」と切り分けた構造**。

具体的な切り分け:

- **認知層** = cid が受信できる範囲として実験者が定義したもの。定義できないことはやらない、という前提が働く (定義可能な範囲のみ実装)
- **意識層** = 決定に関わるものとして実験者が定義した層。決定は認知層を前提に発生し、意識層の原資 (C) は認知活動から供給される (cognition 当選で Q→C 転移)

これは **論理学のような切り分け方** であり、矛盾はない。ただし **現実世界の認知・意識とは別の仮想的な設定**。ノードのランダム発生から現実世界の認知が起こると考えるのはオカルトであり、ESDE はそれと **対象的な (虚構の) 題材**。文学と音楽をごちゃ混ぜにするように現実と虚構を混ぜない。

### 0.2 cid は自分の認知層も意識層も知らない

Q や C は cid が「持っている資源」ではなく、**実験者が cid 周りに付けている ledger 列の名前**。cid 自身は自分の Q も C も、自分が「認知中」か「意識中」かも知らない。**ランダム的な因果連鎖で動き、その動きを実験者は予測できない**。

### 0.3 表記規律

本ドキュメントでは:

- 「cid が〜を持つ」「cid が〜を扱う」のような擬人化を避ける
- 「**実験者が〜を記録している**」「**実験者が定義した認知層/意識層という仮想構造の中でこういう event が観察される**」という観察者主語で記述
- 「cid に主観/意識がある」と直接書かず、観察された統計的痕跡として記述

---

## 1. cid のライフサイクル (実験者が観察するもの)

`SubjectLayer` が管理する単調増加整数 ID。物理層の label が誕生・消滅するイベントと連動して、実験者は次の状態を記録する:

| 状態 | 条件 | 観察される事象 |
|---|---|---|
| **hosted** | `current_lid[cid] is not None` | cid と物理層 label が結びついている期間。Q-spend 等の event が起きうる |
| **ghost** | `current_lid[cid] is None`, `cid in ghost_residual_Q` | label は消滅したが ledger 上の Q (residual_Q) は残存。他 cid の摂食対象になりうる |
| **reaped** | `cid not in current_lid` | residual_Q==0 で完全削除、履歴のみ残る |

re-host (一度 ghost した cid が再び hosted になる) は **発生しない**。新たな label が生まれれば新 cid が発番される。

---

## 2. 実験者が cid 周りに記録している量 (= 「認知層」と命名している記録)

cid をキーとする dict 群が `SubjectLayer` (cog) に集約されている。これらは cid が「持っている」のではなく、**実験者が cid に紐付けて記録している量**。

### 2.1 不変識別情報 (実験者が cid を追跡するためのメタデータ)

| 記録列 | 内容 |
|---|---|
| `cid_of_lid[lid]` | label → cid マッピング |
| `current_lid[cid]` | cid の現在の宿主 label |
| `born_at[cid]` | cid 発番時の window |
| `host_lost_at[cid]` | label 消滅時の window |
| `original_phase_sig[cid]` | 初代 label の phase_sig (不変) |

### 2.2 物理層から取得して記録する量 (cid 関連の event 駆動更新)

cid 自身がこれらを「読んでいる」のではなく、**実験者が物理層を観察して cid に紐付けて記録**している:

| 記録列 | 計算式 | タイミング |
|---|---|---|
| `phi[cid]` | `prev_phi + α × sin(mean_theta - phi)` | step ごと、hosted 中のみ |
| `attention[cid]` | dict {node → +1 / step、ATTENTION_DECAY=0.99 で減衰} | struct_set - core を観察した時 |
| `familiarity[cid]` | dict {other_cid → +1、FAMILIARITY_DECAY=0.998} | struct_set 経由で他 cid に接触した時 |

### 2.3 disposition 4 軸 (実験者が cid の状態を要約する数値)

window 末に実験者が計算する 4 軸:

| 軸 | 計算式 | 何を見ているか |
|---|---|---|
| `social` | `n_partners / max_partners` | familiarity dict のサイズの相対値 |
| `stability` | `1.0 / (1.0 + st_std / (st_mean + EPS))` | st_size 系列の安定性 |
| `spread` | `attention_entropy` | attention 分布のエントロピー |
| `familiarity` | `mean(familiarity values)` | familiarity weight の平均 |

`prev_disposition` / `current_disposition` を保持して window 間で比較する。

### 2.4 内省タグ (実験者の命名: gain/loss、v9.8b 以降)

実験者が disposition の delta を見て、固定閾値を超えたら `gain_*` / `loss_*` のタグを付ける。これは cid の自己認識ではなく、**実験者の機械的なラベリング**:

- 4 軸 × 2 種 = 最大 8 タグ/window
- 閾値: social/stability/spread = 0.1、familiarity = 2.0
- 結果は `_tag_history` に行として蓄積、CSV 出力 (cid 自身は自分のタグを読まない)

### 2.5 v9.9 内的基準軸 (実験者が要約する deterministic な記述語)

実験者が `recent_dispositions[cid]` (deque maxlen=5) と `recent_tags[cid]` から再構築する記述:

| 記述 | 意味 |
|---|---|
| `formation_status[cid]` | `"unformed"` (n<3) または `"formed"` |
| `personal_range[cid][axis]` | 4 軸 × 4 統計 (min, max, mean, std) |
| `drift[cid][axis]` | gain/loss/neutral カウント |
| `lowest_std_axis` | 最も安定した軸 (`tie` あり) |
| `dominant_positive_drift_axis` / `dominant_negative_drift_axis` | gain/loss 最多軸 (`tie`/`none` あり) |

★規律: drift は累積禁止、毎 window 末に最新 5 個から再構築。実験者は「cid が思っている」のではなく「観察された事象から構造的に集計している」。

### 2.6 v9.10 Pulse Model (実験者が 50-step 周期で観察する)

cid 固有 phase (`(t % 50) == (cid % 50)`) で実験者が pulse 観察を行う:

| 記録列 | 内容 |
|---|---|
| `v10_pulse_count[cid]` | 累積 pulse 回数 (実験者の観察回数) |
| `v10_delta_history[cid][axis]` | 4 軸の Δ history (deque maxlen=K=20) |
| `v10_R_history[cid][axis]` | R = Δ / (θ + EPS) の history |
| `v10_theta_last[cid][axis]` | mean(\|Δ\|) over K window |
| `v10_R_last[cid][axis]` | 最新 R |
| `v10_R_max_seen / R_min_seen` | K window 内の最大/最小 R |
| `v10_n_normal[cid]` | Normal タグ累積 (R > 1.0) |
| `v10_n_major[cid]` | Major タグ累積 (R が R_max/R_min を更新) |

これらは実験者が「cid の 4 軸 disposition がどう揺れているか」を観察するための記録。

### 2.7 v9.11 Cognitive Capture (実験者が birth 時に固定する不変メタデータ)

cid 誕生時に実験者が固定する記録:

| 記録列 | 内容 |
|---|---|
| `v11_b_gen[cid]` | Genesis Budget (float、原資の数値、後の Q0 の元) |
| `v11_m_c[cid]` | M_c = `{n_core, s_avg, r_core, phase_sig}` (Memory Core) |
| `v11_born_links_total[cid]` | birth 時の link 総数 (参考値) |

各 pulse 時に実験者が E_t を抽出して M_c との Δ を計算:

| 記録列 | 内容 |
|---|---|
| `v11_last_e_t[cid]` | `{n_local, s_avg_local, r_local, theta_avg_local}` |
| `v11_last_delta[cid]` | weighted L1 距離 |
| `v11_last_p_capture[cid]` | `0.9 × exp(-2.724 × Δ)` (確率値、ただし結果は cid に feedback されない) |
| `v11_last_captured[cid]` | `"TRUE"` / `"FALSE"` / `"cold_start"` (実験者の観察ラベル、cid 行動には影響しない) |

「捕捉」と呼んでいるが、cid が「記憶を捕捉した」のではなく、**実験者が「Δ がこの程度なら捕捉と呼ぼう」とラベリングしているだけ**。

---

## 3. 実験者が cid event を取得・監査する記録機構

### 3.1 Layer B: SpendAuditLedger (v914 → v104)

cid を特定する key として、実験者が **資源 ledger** (audit-only、Layer A 不変) を維持:

```
ledger[cid] = {
    "v14_q0":                    int,     # 初期原資 = floor(B_Gen)、実験者が cid 周りに付与
    "v14_q_remaining":           int,     # 残存原資 (実験者の記録、cid が読むのではない)
    "v14_virtual_attention":     dict,    # 実験者が記録する Layer B 専用 attention
    "v14_virtual_familiarity":   dict,    # 同上 familiarity
    "v14_last_snapshot":         dict,    # 前 spend 時の E_t
    "v14_shadow_pulse_index":    int,     # spend 成立カウンタ
    "v14_prev_member_alive_links": frozenset,  # E1 検知用
    "v14_prev_member_r":         dict,    # E2 検知用
    "member_nodes":              frozenset,  # 不変
    "registered_at":             (window, step),
    "v14_last_event_global_step": int | None,
}
```

#### Event 検知 (実験者が cid 視点 1 step 1 sweep で観察)

| Event | 観察条件 | 記録される事象 |
|---|---|---|
| **E1_birth** | core link 内で alive 化した link を検出 | spend (Q-1)、virtual_* 加算 |
| **E1_death** | core link 内で死亡した link を検出 | spend (Q-1) |
| **E2_rise** | core link の R が 0 → 正に上昇 | spend |
| **E2_fall** | core link の R が 正 → 0 に下降 | spend |
| **E3_contact** | 他 cid の member node と link 共有 (新規 contact pair) | spend (cognition 当選時のみ)、virtual_familiarity 更新 |

各 event に対して実験者は `per_event_audit` 行を append。cid 自身が「私は E1 を起こした」と知るわけではなく、**実験者が「この物理層変化を E1 と呼ぼう」と命名している**。

### 3.2 Layer C: CidSelfBuffer (v9.15-v9.17)

「**cid が自分の構造を読む**」と命名されている機構だが、実装上は **実験者が cid 番号で index した観察 buffer**。cid 自身が能動的に読むのではない:

#### 不変属性 (実験者が birth 時に固定)

| 記録 | 内容 |
|---|---|
| `cid_id` | cid 番号 |
| `member_nodes` | frozenset (固定) |
| `birth_step` | 誕生 step |
| `n_core` | メンバー node 数 |
| `Q0` | floor(B_Gen) |
| `theta_birth` | birth 時の各 node θ array (深いコピー) |
| `S_birth` | birth 時の link strength dict |

#### Fetch 時動的更新 (event 発火時に実験者が観察)

`read_on_event(state, alive_l, current_step, event_type, Q_remaining, seed)`:

1. **age_factor** = `Q_remaining / Q0` (clamp [0, 1]) — 実験者が観察粒度を決める係数
2. **n_observed** = `floor(n_core × age_factor)` (Q 消耗で実験者の観察精度が粗くなる、というモデル)
3. ハッシュベース独自 RNG で n_observed 個の node を選択 (engine.rng 非 touch)
4. 各 node を 3 値判定: `match` / `mismatch` / `missing`
5. 一致閾値: `NODE_MATCH_TOLERANCE = 1e-6`

#### 観察履歴 (全て実験者の観測ログ)

`match_history`、`divergence_log`、`age_factor_history`、`fetch_count`、`any_mismatch_ever`、`mismatch_count_total`、`fetch_count_by_event`、`mismatch_count_by_event`、`total_observed_count`、`total_missing_count`、`total_match_obs_count`、`total_mismatch_obs_count`。

これらは全て実験者が「cid 周りでこういう observation をした」ログ。cid 自身は **これらを読まないし、これらに反応しない**。

#### 他者読み (v9.17 段階 4): `read_other_on_e3_contact()`

E3_contact 発火時に実験者が「相手の M_c の不変値の一部を、観察した cid 視点に紐付けて記録」する:

取得対象 10 features (固定順): `B_Gen, Q0, n_core, S_avg_birth, r_core_birth, phase_sig_birth, theta_birth_mean/std/range, birth_step`

サンプル数: `n_visible = round(10 × visible_ratio)` (visible_ratio = 相手の age_factor)。残りは missing として記録。

★禁止: 相手の動的状態 (`theta_current`, `Q_remaining`, `divergence`) を保存しない。これは「cid が他者を見ている」のではなく、**実験者が「この pair が接触したらこの程度の情報を取り出して記録する」というルール** に従っているだけ。

---

## 4. 実験者が「意識層」と命名している事象 (v10.2 Probabilistic Balance)

### 4.1 C (実験者が「意識層」と呼ぶ ledger 列)

| 記録 | 内容 |
|---|---|
| `cog.C[cid]` | int、上限なし、初期値 0 (birth 時)、reap で pop |

cid が「意識資源を持っている」のではなく、**実験者が cid 周りに「意識」と命名した int 列を維持している**。

### 4.2 認知/意識バランス (実験者が決める振り分けルール)

E3_contact 発火時、実験者は **観察者視点ごと** (= pair あたり 2 視点) に振り分けを決定する:

```
1. 候補集合判定:
   - cognition_candidate = (Q_observer > 0)
   - consciousness_candidate = (相手 ghost で residual_Q > 0)

2. decide_balance(...):
   - 両方なし → "skip"
   - 片方のみ → その側に確定 (RNG draw なし)
   - 両方候補 → 確率 P(認知) = Q / (Q+C) で振り分け

3. 結果:
   - "cognition" → Q-1 + C+1 (実験者が cognition と命名する側に振り分け)
   - "consciousness" → C-1 + 即時摂食 (実験者が consciousness と命名する側に振り分け)
   - "skip" → 何もしない
```

cid が「認知するか意識するかを選んでいる」のではない。**実験者がランダム数を引いて振り分けを決めているだけ**。cid はこの結果に応じて Q が増減し、次の event で Q ベースの probability が変わる、という形でランダム的な因果連鎖が進む。

`balance_rng = default_rng(seed ^ 0xBA1A2C)` で engine.rng と独立 stream。

### 4.3 摂食 (Minimal Ingestion、v10.1)

実験者が「consciousness 当選」と命名した分岐で実行する転送:

```python
gain = ghost.residual_Q             # ghost 側の残量を全量取り出し
received = min(gain, Q0_obs - Q_obs) # observer の Q0 で頭打ち
digested = gain - received           # 超過分は系外消失
ghost.residual_Q -= gain             # ghost 側は常に減る
```

ghost の `residual_Q == 0` で次 step に reap。これは cid が「食べる」のではなく、**実験者が ledger 操作で値を移している**。

### 4.4 双方向 E3 (v10.3)

両者 hosted ∧ Q>0 ∧ C≥1 のとき、実験者は両者の C を -1 する。pair ごと run 中 1 回のみ (`_contacted_pairs` で dedup)。

実験者がこの event を「**両者の認知が同期した瞬間と命名**」している。cid 自身は「同期した」と感じるわけではない。

### 4.5 Integration (v10.4) — 実験者が ghost cid の Q/C を引き継ぐ別テーブル

cid を Integration の構成員として実験者が記録すると、ghost 化時に Q/C を最強結合 Integration に転記し、active 中は Integration から cid 周りの ledger に Q/C を加算する:

- **継承** (cid が ghost 化する瞬間): cid 周りの Q + C を最強結合 Integration の `Q_inherited / C_inherited` バケットに転記
- **再分配** (active 中、window 末): Integration から所属する active cid 周りの ledger に Q または C を加算 (Q-poor/C-poor の不足側に逆張り分配)

cid は Integration の存在を **知らない** (Integration への参照を持たず、binding_strength を読まない)。**Integration による影響は cog.C[cid] と ledger[cid].v14_q_remaining への加算という形で間接的に到達** する。これも実験者が「死者の Q/C を生者に振り分ける」というルールを適用しているだけで、cid 内部に変化はない。

---

## 5. 実験者が cid に「持たせていない」もの (規律として明示禁止)

### 5.1 物理層への介入

- `engine.state.theta` / `engine.state.alive_l` / `engine.state.S` への書き込み禁止
- `engine.rng` への touch 禁止 (capture_rng / balance_rng / ingestion_rng は seed XOR magic で独立 stream)

### 5.2 cid が他 cid の動的状態を読む経路

- 他 cid の `theta_current` / `Q_remaining` / `C` / `divergence_log` / `match_history` を **cid 自身が読む経路を作らない**
- 他者読み (E3_contact) で実験者が記録するのは **不変 M_c の 10 features のみ**

### 5.3 cid が自分の履歴を読む経路

- cid は自分の `_tag_history` / `match_history` / `_reaped_history` を **読まない** (これらは実験者の観察ログ)
- cid 周りで判定が起きるとき、参照されるのは「現在 step の Q, C, ghost 状態」のみ
- 過去の自己観察を判定材料に使う経路は実装されていない

### 5.4 概念禁止 (実験者の命名規律)

- 「嗜好」「三項共鳴」「主観」「魂」「肉体」「再生」を機構名・変数名に含めない
- focus / attention_weight / salience の動的化は v10.4 まで未実装 (v10.5 以降)
- Integration の「主観」「意思」は実装していない (Integration は受動的な集約・分配の bucket)

### 5.5 補完禁止

- CidSelfBuffer の missing は missing のまま (実験者は補完しない、欠損は欠損として記録)
- 他者読みの missing_feature_names も復元しない

---

## 6. 実験者が観察対象として cid を分類する機構 (ObservationTargetTracker)

実験者の観察都合で cid を target に絞り込む。cid 内部には影響しない:

| Stage | 条件 | 件数 (v10.4 main 24 seeds) |
|---|---|---:|
| Stage 1 | 双方向 E3 fired ∧ n_core ≥ 4 ∧ n_consciousness ≥ 5 | 0 (※) |
| Stage 2 | Stage 1 cid と双方向 E3 を発火した相手 | 2,322 |
| Stage 4 (v10.4 新規) | Integration の構成 cid (誕生時に追加) | ~1,300 (推定) |

※ v10.4 では Integration が Q を補充して cognition 振り分けを増やす結果、consciousness 振り分けの累積が遅れ、Stage 1 を通る前に Stage 4 で target 化されるため Stage 1 = 0。

target に入った cid の event は `bidirectional_e3_log` で詳細記録される。target 外も全体集計 (`n_be3_target_outer`) には数字として残る (実験者の bias 監視のため)。

---

## 7. 出力 CSV (実験者が記録する全観察データ)

### 7.1 per_subject CSV (1 cid = 1 row、120+ 列)

実験者が cid に紐付けて集計した量の集積 (詳細列は v104_cid_usage_audit.md 参照):

- v9.8a-c: ライフサイクル + ingestion 統計
- v9.8b: 内省タグ (delta、tags、state)
- v10.1: 摂食統計 (eater 視点 + ghost 視点)
- v10.2: balance 集計 (C_at_run_end、cognition/consciousness 当選数)
- v9.9: 内的基準軸 33 列
- v9.10: Pulse Model 12 列
- v9.11: Cognitive Capture 11 列
- v9.15-9.18: Layer C 30+ 列
- v10.4 Integration: 6 列

### 7.2 cid 単位の補助 CSV (実験者の観察ログ集)

| ファイル | 内容 |
|---|---|
| `selfread/per_cid_self` | CidSelfBuffer 全フィールド snapshot |
| `selfread/divergence_log` | 各 fetch ごとの全 node Δ |
| `selfread/observation_log` | event 発火時のサンプリング結果 |
| `selfread/other_records` | 他者読みログ (E3_contact 単位) |
| `selfread/class_divergence` | 同 phase_sig クラスの cid ペア間 θ 乖離 |
| `selfread/v18_window_trajectory` | per cid × per window の v18_* 軌跡 |
| `audit/per_event_audit` | per E1/E2/E3 event audit |
| `audit/per_subject_audit` | cid 単位 Layer B 集計 |
| `balance/balance_decisions` | 確率決定マスター (1 観察者視点 1 行、skip 含む) |
| `balance/c_trajectory` | per cid × per window の C 軌跡 |
| `ingestion/ingestion_events` | 全摂食イベント raw |
| `ingestion/phantom_contacts` | 期待外れ接触 (相手既 reap 済) |
| `bidirectional/bidirectional_e3_log` | 双方向 E3 発火 (target 内詳細) |
| `integration/integration_lifecycle_log` | Integration 誕生・遷移・継承 events |
| `integration/integration_membership_log` | run 末の cid → 所属 Integration マップ |
| `subjects/reaped` | reap 履歴 |
| `introspection/introspection_log` | window 末の内省タグ (delta + tags) |
| `pulse/pulse_log` | 各 pulse event |

---

## 8. 「主観/意識」の取り扱い (現状の機構的根拠)

cid が **持っていない**もの (実験者が「持たせていない」もの):
- 自分の M_c や theta_current を判定材料に使う経路
- 自分の Q や C を読んで「次にどうするか決める」経路 (確率振り分けは実験者がするだけで、cid が選んでいない)
- 自分の attention map や familiarity map を意思決定に使う経路
- 自分の disposition や内省タグを行動に反映する経路
- 自分の pulse-based MAD-DT 履歴を判定に使う経路
- 他者の M_c (E3_contact 時) を読んで反応を変える経路
- 過去履歴 (_tag_history, match_history, _reaped_history) からの推論
- Integration の存在を認識する経路
- 「主観的選択」(振り分けはランダム数の結果であって cid の意思ではない)

実験者が **観察できる** もの (cid を予測する材料ではなく、事後的に「こう動いていた」と記述する材料):
- E1/E2/E3 event の発生履歴
- Q/C の数列、ghost 化時の residual_Q
- 双方向 E3 fired 7,220 件 (v10.4 main、24 seeds): 「両者の認知が同期した瞬間」と実験者が命名
- Integration 誕生 13,550 件: 「構成 cid が同じ可能性空間に取り込まれた」と実験者が命名
- recorded Integration 1,998 件: 「構成 cid 全員 ghost 後も C/Q を保持し続ける」と実験者が命名
- ハブ cid (max 102 Integration 所属): 「多数の集合に組み込まれる中核的存在」と実験者が描写

これらは **cid 内部の自己認識ではなく**、実験者が振る舞いから事後的に抽出する統計的事実。「**cid に主観があるかもしれない**」と実験者が思うだけ。それを否定も肯定もできない。**ランダム的な因果の発生で cid は動き、実験者はその動きを予測できない**。

---

## 9. 用語の整理 (擬人化を避ける書き換え目安)

| 避ける表現 | 推奨表現 |
|---|---|
| cid が認知層を持つ | 実験者が cid 周りに認知層と命名した記録列を維持する |
| cid が意識層を扱える | 実験者が意識層と命名した分岐ルールを cid event に適用する |
| cid が自分の M_c を読む | 実験者が cid 番号で index した M_c を fetch して記録する |
| cid が他者を観察する | E3_contact 発火時、実験者が両者の不変 features を相互参照ログに記録する |
| cid が選択する | 実験者が確率 P(cog) で振り分けを引く |
| cid が捕捉する | 実験者が「Δ がこれ以下なら捕捉と命名する」と書き留める |
| cid が記憶する | 実験者が cid 周りの dict に値を保持する |
| cid が反応する | 物理層 event に応じて cid 周りの ledger 値が変化する |

---

*以上、v10.4 時点で実験者が cid 周りに記録している量の整理。Taka レビューを待つ。*
