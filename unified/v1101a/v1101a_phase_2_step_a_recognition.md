# v1101a 段階 2 Step A 認識確認 — Code A

*作成*: 2026-05-18、Code A
*親*: `v1101a_phase_2_design.md` (Web Claude 段階 2 設計書) + Taka 確認 (2026-05-18 配置承認)
*対象*: Web Claude (相談役) + Taka (実装着手判断)
*目的*: 段階 2 設計書と repo 実状の事前齟齬指摘 + cid state ledger 再生の実現可能性確認 + 留保 #41 member_cids 復元可否 + 観察 C 予測可能性の baseline 確認、実装着手前の判断材料整理。

---

## 0. 一文サマリ

段階 2 設計書を repo 実状で照合した結果、(1) 留保 #41 (Integration member_cids 個別 cid id list が v10.x outputs に未 persistence) は **段階 1 Step C で実質的に解決済** — Code A が v105 `alpha_lifecycle_log_seed{N}.csv` (member_cids '|' 区切り、birth event ごと) + `alpha_membership_log_seed{N}.csv` (cid_id × alpha_ids 最終 step snapshot) + `beta_distribution_log_seed{N}.csv` (beta_id × target_cid) から 24 seeds 全て member 取得・使用済で、設計書 §2.5「再生で復元可能か Code A 認識確認で確認」は前提が古い情報のため設計書側を更新候補、(2) v105 `reconstruct_beta_snapshots()` (`v105_animate_integration.py` L34-57) は **β level の構造再構築** (member 集合 + Q/C 継承) で「326 atom 全濃度の時系列」ではなく cid level への拡張は別実装、(3) 「cid state ledger」が指すものは `atom_introduction_events_v112_seed{N}.parquet` (24 seeds 揃い、per seed 400 events = 16 cid × 25 atom intro × timestamp 200-22479) を時系列に並べ per (cid, timestamp) で「これまでに intro された atom 集合」を累積する経路が現実的、(4) per (cid, t) 326 atom 濃度の再構築方針は 2 択 (a) 簡易版 = 累積 atom 集合の atom_profiles を mean → 326 atom cosine sim (半日想定) or (b) 完全再現 = v106 `build_cid_vector()` を per-step replay (1 日-1.5 日想定) で Web Claude 判断要請、(5) 観察 C 予測可能性の baseline (ランダム水準) は shuffle baseline (attention_candidate_id を時系列内で permutation して t → t+1 遷移の当たり率を取る) が最簡で絶対格言 #9 神の手回避と整合、(6) 観察 B 隣接時点 Jaccard の時間粒度は段階 1 attention_emit ログの window 単位 (per seed ~50 window) で十分、(7) 時間軸付き unit_KL_delta は (a)(b) どちらの方針でも cid state 再構築後に per (cid, window) で 326 atom 分布 KL → window 方向差分で算出可能、留保 #41 解決済の明示 + 326 atom 濃度再構築方針 (a)/(b) 選択 + ランダム baseline 方法確定の 3 件を Web Claude/Taka 判断要請、設計書 §4 進行表「実装 1 半日-1 日」は (a) 簡易版採用前提と整合・(b) 完全再現採用なら +0.5-1 日。

---

## 1. 設計書と repo 実状の事前齟齬指摘

### 1.1 齟齬 1 — 留保 #41 は段階 1 Step C で解決済

設計書 §2.5 (留保 #41):
> Integration の member_cids 個別 cid id list が v10.x outputs に未 persistence の問題。cid state ledger 再生時に member_cids を復元できれば #41 も解消する。再生で復元可能か、Code A 認識確認で確認すること。

**実状**: 段階 1 Step C で member_cids は既に取得・使用済 (3 ソース揃い、24 seeds 完全):

| source | path | 列構造 | 用途 |
|---|---|---|---|
| α lifecycle | `developmental/v105/diag_v105_main/integration/alpha_lifecycle_log_seed{0..23}.csv` | seed, step, alpha_id, event_type, trigger_type, **member_cids ('\|' 区切り)** | birth event ごとに alpha → member cids list |
| α membership | `developmental/v105/diag_v105_main/integration/alpha_membership_log_seed{0..23}.csv` | seed, step, cid_id, **alpha_ids ('\|' 区切り)**, binding_strengths | 最終 step snapshot で cid → alpha 帰属 逆引き |
| β distribution | `developmental/v105/diag_v105_main/integration/beta_distribution_log_seed{0..23}.csv` | seed, step, **beta_id, target_cid**, q/c_distributed, target_q_ratio_before/after | per-distribution event で β → 配布した cid 取得 |

Step C 実装 (`v1101a_step_c_attention_emit.py` L92-115) で `load_alpha_membership()` / `load_beta_membership()` 関数として使用済。Step E までの全 records 1,726,974 で alpha/beta scope は正常に member ベースで集約済。

→ 設計書 §2.5 の「未 persistence」前提は古い情報。段階 2 では留保 #41 を「**段階 1 で実質解決済、cid state ledger 再生の追加機能としての member 復元は不要**」と更新する。

### 1.2 齟齬 2 — v105 `reconstruct_beta_snapshots()` は cid level 再構築でなく β level

設計書 §2.5:
> `v105_animate_integration.py` の `reconstruct_beta_snapshots()` (β-level lifecycle_log replay) を cid level に拡張する前例がある (段階 1 環境チェックで確認済)。

**実状確認** (`v105_animate_integration.py` L34-57):
```python
def reconstruct_beta_snapshots(lifecycle_path: Path):
    """β の lifecycle log から、event 時刻順に β の状態を replay。
    Returns: events: list of dict (timestamped β state)
    最終的に各 β の (birth_step, last_event_step, max_alpha_count,
    max_cid_count, became_recorded_step, Q_inherited, C_inherited)
    を全 step 横断で再構築。
    """
```

→ β の構造再構築 (member alpha/cid 集合、Q/C 継承量)、**「326 atom 全濃度の時系列」ではない**。

cid level への拡張 = cid lifecycle 相当の log + atom 濃度更新ロジックの両方が必要。前者 (cid lifecycle log) は v10.x outputs に明示的なファイルがない (cid は v10.5 で生成されるが lifecycle log は β/α と異なる方式) → 後者の atom 濃度更新は v106 `build_cid_vector()` (L486) を per-step 化する別実装が必要。「拡張前例」は β level 構造再構築のテンプレートとしては有用だが、cid level 326 atom 濃度時系列の直接前例ではない。

### 1.3 齟齬 3 — 「cid state ledger」の指すもの

設計書 §2.5 で「cid state ledger 再生」と書かれているが、具体実体は不明示。

**Code A の解釈** (現実的経路):

| 候補 | 内容 | 実現可能性 |
|---|---|---|
| (1) cid lifecycle log | v10.x に明示 file なし、cid の生成・消滅 event 単独 log | × 既存なし |
| **(2) atom_introduction_events_v112_seed{N}.parquet** | **per (cid, timestamp) で atom intro event 24 seeds 揃い** | **○ 実在、Step C 確認済** |
| (3) v106 cid_atom_sim_matrix を per-step 再計算 | build_cid_vector を per-step replay | △ 重実装、要 cid_vec input の per-step スナップショット |

→ 段階 2 の「cid state ledger 再生」は (2) を起点に (3) を組む経路が現実的。詳細は §2 参照。

---

## 2. cid state ledger 再生の実現可能性 + 326 atom 全濃度時系列の経路

### 2.1 入力データ (24 seeds 完全揃い、read-only)

| ファイル | 規模 (seed 0) | 用途 |
|---|---|---|
| `atom_introduction_events_v112_seed{0..23}.parquet` | 400 rows = 16 cid × 25 atom × timestamp 200-22479 | per (cid, timestamp) で「どの atom が intro されたか」 |
| `v106/mapper_dir/ atom_profile_*.npy` 等 | 各 atom の参照ベクトル (atom_profiles) | atom_id → 326 dim vector の lookup |
| v106 trajectory 4 解像度 (Step C 入力) | per (cid, window) の lifespan/Q/C/rank_1_atom 等 | cid alive 期間判定、qc_ratio 時系列 |

### 2.2 326 atom 全濃度時系列の再構築 — 2 方針

#### 方針 (a) 簡易版 — 累積 atom 集合 + atom_profiles mean

```
per (cid, target_time):
  intro_atoms_set = atom_introduction_events_v112[(cid, t<=target_time)].atom_id.unique()
  cid_vec = mean(atom_profiles[a] for a in intro_atoms_set)
  cid_atom_concentration = cosine_sim(cid_vec, atom_profiles[all 326 atoms])
```

- ロジック: cid に存在する atom 集合の参照ベクトル平均を cid_vec とし、各 atom 濃度 = cosine_sim
- 実装軽量、半日想定
- v106 `build_cid_vector` (L486) と厳密一致でない (build_cid_vector はより複雑、各 atom の Q/C 重みや lifespan を加味)
- 段階 2 の出口 (注意の方向性 = 選択と集中 / 拡散の切り分け) には十分な粒度の可能性

#### 方針 (b) 完全再現 — v106 `build_cid_vector` を per-step replay

```
per (cid, target_time):
  df_cid_snapshot = run_cid_state_at(cid, target_time)
    # cid の age/lifespan/Q/C/n_core_member/etc を target_time までで replay
  cid_vec = build_cid_vector(df_cid_snapshot, seed_max)
  cid_atom_concentration = cosine_sim(cid_vec, atom_profiles[all 326 atoms])
```

- ロジック: v106 build_cid_vector を完全再現、df_cid の per-step スナップショットを replay
- 実装重い、1-1.5 日想定 (build_cid_vector の入力依存解析 + per-step 状態管理 + cid_vec 計算)
- v106 cid_atom_sim_matrix (run 最終時点) と完全整合する時系列

#### 判断要請

設計書 §4 進行表「実装 1 半日-1 日」は (a) 採用なら整合、(b) なら +0.5-1 日。Code A 仮所見:

- (a) 簡易版: 段階 2 の出口 (選択と集中 vs 拡散の方向性) には十分な粒度。観察 A/B/C は注意候補の数・波及先 cid Jaccard・予測可能性で時間方向の形を見る → atom 濃度の細かい正確性は副次。
- (b) 完全再現: 厳密だが段階 2 出口を超える精度。段階 3 (生きた版) なら必要だが段階 2 ではオーバースペック。

→ Code A は (a) 簡易版を推奨。最終判断は Web Claude / Taka。

### 2.3 時間軸付き unit_KL_delta (留保 #L1 対応)

(a)(b) どちらでも cid state 再構築後に算出可能:

```
per (cid_pair_i, cid_pair_j, window):
  unit_kl[i,j,w] = KL(cid_i_atom_dist[w] || cid_j_atom_dist[w])
per (cid_pair, window-window+1):
  unit_kl_delta = unit_kl[..., w+1] - unit_kl[..., w]
```

- 段階 1 unit_kl_static は cid_atom_sim_matrix (run 最終、静的) で算出
- 段階 2 unit_kl_delta はこれの per-window 時系列差分
- 出力規模: cid pair × window で per-seed 数 MB 想定

時間粒度は段階 1 と整合させ window 単位 (per seed ~50 window) で十分。

---

## 3. 観察 A/B/C の実装方針 (Code A 仮所見)

### 3.1 観察 A — 注意候補数の収束/発散

入力: 段階 1 `attention_causality_*.parquet` の `predecessor_attention_ref` + `window` + `qc_regime` + `attention_candidate_id`。

- qc_regime が cognitive → conscious に切り替わった window を t0 とする (per seed × 構造単位 × metric_type)
- t0+1, t0+2, ... の各 window で attention_candidate_id のユニーク数を追う
- 比較 baseline: t0-1, t0-2, ... の認知優位フェーズでの同指標
- 数の推移 (収束 = 減る / 発散 = 増える/横ばい) を per scope 並列で記録

実装軽量 (段階 1 出力の集計のみ)、半日想定 (実装 2 の一部)。

### 3.2 観察 B — 波及先 cid 集合の隣接時点 Jaccard

入力: 段階 1 `attention_propagation_*.parquet` (中心 cid × Δt × 周辺 cid) + 段階 1 attention_emit log。

- per (seed, change_scope, change_metric_type, qc_regime) で window 時系列
- 隣接 window 間で「波及先 cid 集合」(中心 atom 一致 cid) の Jaccard を計算
- 段階 1 留保 #L4 (alpha 92.5% 偏り) に対応するため scope 内割合で正規化

実装軽量、段階 1 出力からの集計のみ。半日想定 (実装 2 の一部)。

### 3.3 観察 C — 注意候補の予測可能性

入力: 段階 1 `attention_causality_*.parquet` の `predecessor_attention_ref` (箱 1)。

- per (seed, change_scope, change_metric_type) で意識優位 window の attention_candidate_id 時系列
- 観察対象: t の候補 (or その predecessor_attention_ref) から t+1 の候補をどれだけ予測可能か
- 予測モデル: 段階 1 では「t+1 候補 == predecessor_attention_ref が指す cid」の単純判定が一案 (predecessor 連鎖が予測可能性の最小単位)

**baseline (ランダム水準) の算出 — 判断要請**:

| 方法 | 内容 | 実装 |
|---|---|---|
| (i) 完全 shuffle baseline | 同 seed 内 attention_candidate_id を時系列内で permutation し、permutation 後の t → t+1 当たり率を 100 回平均 | 簡単、絶対格言 #9 整合 (神の手なし) |
| (ii) 一様 random sampling | t+1 候補をランダム cid から取った場合の当たり率 (= 1/n_cids_alive) を理論計算 | 最簡だが「同 seed 内分布の偏り」を捨てる |
| (iii) Markov 0 次モデル | t+1 候補は同 seed 内の全 attention_candidate 頻度分布からサンプル | 中程度、頻度バイアスを含む |

Code A 推奨: **(i) 完全 shuffle baseline** が段階 1 規律 (神の手回避 #9、構造的決定) と最も整合。time permutation で per-seed × 100 回回しても計算量小。

100% 予測可能を作らないこと (箱 3 / Aruism 対称性) の確認:
- 観察 C 結果の予測率が 100% に到達したら、それ自体が観察事実として記録 (留保候補、段階 1 規律違反になる)
- 想定: predecessor 連鎖は段階 1 で 86.6-100% 埋まり率だったが、予測「率」(= t+1 候補 が predecessor 一致) は別物。100% 到達は構造的に低確率

### 3.4 段階 2 グラフ (Step F 拡張)

段階 1 `v1101a_observation.html` (4 セクション 12 panel) に Section 5 を追加:
- Panel 1: 観察 A 候補数推移 (cognitive vs conscious)
- Panel 2: 観察 B Jaccard scope 別
- Panel 3: 観察 C 予測可能性 (random baseline 付き)

留保 #L4 正規化 + Aruism 対称性 (100% でない確認) を視覚化。

---

## 4. Web Claude / Taka 確認要請

### 4.1 確認要請 1: 留保 #41 段階 1 解決済の前提更新

設計書 §2.5「再生で復元可能か Code A 認識確認で確認」は段階 1 Step C 時点で member 取得済 (本書 §1.1)。段階 2 設計書 §2.5 を「**留保 #41 は段階 1 で実質解決済 (v105 lifecycle/membership/distribution log から member 取得)、段階 2 では追加対応不要**」に更新するか。Code A 仮所見: 更新。

### 4.2 確認要請 2: 326 atom 全濃度時系列の再構築方針 (a) / (b)

(a) 簡易版 (累積 atom 集合 + atom_profiles mean、半日) / (b) 完全再現 (v106 build_cid_vector per-step replay、1-1.5 日)。Code A 仮所見: (a) 簡易版 (段階 2 出口に十分な粒度、§2.2)。

### 4.3 確認要請 3: 観察 C 予測可能性の baseline 算出方法

(i) 完全 shuffle baseline (per-seed × 100 回 permutation) / (ii) 一様 random sampling (1/n_cids_alive 理論計算) / (iii) Markov 0 次モデル。Code A 仮所見: (i) shuffle baseline (神の手回避 #9 整合、§3.3)。

---

## 5. 進行 — Step A 完了後の流れ

| Step | 内容 | 担当 | 想定 | 待機 |
|---|---|---|---|---|
| Step A (本書) | 認識確認 | Code A | 完了 | Taka 確認待ち |
| Step B 実装 1 | cid state ledger 再生 (方針 (a) or (b)) + 時間軸付き unit_KL_delta | Code A | (a) 半日 / (b) 1-1.5 日 | §4.2 確定後 |
| Step C 実装 2 | 観察 A/B/C 算出 | Code A | 半日 | §4.3 確定後 |
| Step D グラフ | Step F 拡張 (Section 5 追加) | Code A | 短時間 | Step B/C 後 |
| Step E bit-identity | 3 層再検証 (ledger 不変、書込みパス制限) | Code A | 短時間 | Step B/C 後 |
| Step F 観察事実報告 | judgement なし (#12) | Code A | 短時間 | Step E 後 |
| Step G Phase Result | 段階 2 解釈統合 | Web Claude | — | Step F 後 |

想定合計 (a) 採用なら 1.5 日 / (b) 採用なら 2-2.5 日 (設計書 §4 想定 1.5-2 日と整合)。

---

## 6. 規律遵守自己点検 (本 Step A、絶対格言抜粋)

| # | 格言 | 本書での遵守 |
|---|---|---|
| 2 | 物理層 frozen 絶対 | 本書は read-only 調査、書き込み unified/v1101a/ 配下のみ |
| 5 | 観察軸を増やすことを駆動要因にしない | §2 で既存 atom_introduction_events を再構築の素材として明示 |
| 6 | 出口の固定 | 設計書 §3 出口 6 項目を継承、段階 2 内で変更しない |
| 9 | 神の手回避 | §3.3 で shuffle baseline (構造的決定) を推奨 |
| 11 | 概念単位を雑に扱わない | 「cid state ledger」の具体実体を §1.3 / §2.1 で明確化 |
| 12 | Aruism 判定回避 | 本書は事実記録、(a)/(b) 等の判定は Web Claude / Taka |
| 13 | AI を信じない原則は Taka 個人 | §4 確認要請を明示、Code A 仮所見と最終判断を区別 |
| 14 | Taka 直感優先 | 設計書 §0.3 Taka 整理 (注意の方向性 = ランダムか妥当か) を継承 |

---

## 7. 一文サマリ (再掲)

段階 2 設計書を repo 実状で照合し (1) 留保 #41 は段階 1 Step C で実質解決済 (v105 alpha_lifecycle_log + alpha_membership_log + beta_distribution_log から 24 seeds member 取得済、設計書前提更新候補)、(2) v105 reconstruct_beta_snapshots は β level の構造再構築で cid level 326 atom 全濃度時系列ではない、(3) 「cid state ledger」が指すものは atom_introduction_events_v112_seed{N}.parquet を時系列に並べる経路が現実的 (24 seeds 揃い、Step C で構造確認済)、(4) per (cid, t) 326 atom 濃度の再構築方針は 2 択 (a) 簡易版 = 累積 atom 集合の atom_profiles mean → 326 atom cosine sim (半日) or (b) 完全再現 = v106 build_cid_vector の per-step replay (1-1.5 日) で Code A 仮所見 (a)、(5) 観察 C 予測可能性の baseline は (i) 完全 shuffle baseline (per-seed × 100 回 permutation) が神の手回避 #9 整合で Code A 仮所見、(6) 観察 B Jaccard / 時間軸付き unit_KL_delta は段階 1 出力 + cid state 再構築結果から算出可能で実装軽量、(7) 100% 予測可能を作らないこと (箱 3 / Aruism 対称性) の確認も観察事実として記録、Web Claude/Taka 確認要請 3 件 (留保 #41 前提更新 / 326 atom 再構築 (a)(b) / shuffle baseline (i)(ii)(iii)) を §4 で整理、Step A 完了後の進行表 §5、想定合計 (a) 採用なら 1.5 日 / (b) 採用なら 2-2.5 日。

---

*以上、v1101a 段階 2 Step A 認識確認 (Code A、2026-05-18)。確認要請 3 件 (§4) への Web Claude/Taka 回答待ち。回答後 Step B 実装 1 (cid state ledger 再生) に着手可。*
