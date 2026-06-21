# v12 Atomset（atom×atom 関係網）STEP 1 — 調査のみ報告

## 自己規律宣言（Code A）
① 過去引用済: `developmental/v107/outputs/main/relation_paths_seed0.parquet`、`developmental/v107/outputs/main/source_events_seed0.parquet`、`developmental/v106/outputs/main/cid_atom_sim_matrix_seed0.parquet`、`genesis/canon/genesis_physics.py:232 inject`、`developmental/v108/v108_post_process.py`・`v108_subsidiary_observations.py:5`・`v108_atom_co_occurrence_report.md`、`unified/v1103/v1103_step_c_density_distribution.py`、`unified/v1106a/v1106a_step_l_verification_a.py`。
② Taka 逐語（原文）: 「これは調査 STEP のみ。網を組まない・演算しない・可視化しない。 frozen データに「何が在るか」を出すだけ」「適当に演算して解決したことがない」「v108 は atom→CID 波及を測ったが atom 同士の網は組んでいない、という私の読みの裏取り」。
③ 成否判定は Taka（本報告に success/fail/Full/Partial/Failure を置かない、観察事実のみ）。
④ 集約語（効いた/失敗/個性化成立 等）なし。

*作成*: 2026-06-16、Code A。*この STEP でやったこと*: dump と在/無の確認のみ（網形成・演算・可視化・cid pool 選抜・effect_size/cosine 等の演算はしていない）。

---

## Q1. 経路が「結ぶ相手 CID」を変えるか（dump）

データ: `relation_paths_seed0.parquet`（851,154 行、列 = `event_id, source_cid, timestamp, target_cid, relation_path_type, relation_strength, hop_distance, seed`）。経路種別 5 種の行数: temporal_coactivation 281,190 / attention_via_salience 219,003 / familiarity 165,547 / integration_alpha 105,521 / integration_beta 79,893。

source_cid ごとの経路別 target_cid（dump）:

**source_cid=0**
| relation_path_type | 到達 CID 数 | 例（target_cid） |
|---|---|---|
| attention_via_salience | 20 | 2, 9, 10, 19, 22, 26 |
| familiarity | 11 | 41, 42, 107, 128, 178, 190 |
| integration_alpha | 20 | 2, 10, 19, 22, 26, 42 |
| integration_beta | 15 | 2, 10, 19, 42, 44, 90 |
| temporal_coactivation | 197 | 2, 7, 9, 10, 19, 22 |

**source_cid=100**
| relation_path_type | 到達 CID 数 | 例 |
|---|---|---|
| attention_via_salience | 2 | 81, 99 |
| temporal_coactivation | 27 | 0, 2, 9, 10, 19, 22 |

→ 観察事実: 全経路で到達 CID 集合が同一か = **False**（経路ごとに到達 CID 数も成員も異なる。例: source_cid=0 で familiarity は 41,42,107… に到達、attention は 2,9,10… に到達）。

## Q2. homophily 滑りが測れるか（在/無）

データ: `cid_atom_sim_matrix_seed0.parquet`、shape = **(228, 328)** = 228 CID 行 × 列 `[seed, cid, <326 atom 列>]`（atom 列 = `ABS.bound, ABS.exempt, …, COG.confusion, …` の sim score）。

→ 観察事実: 各 CID の atom membership（atom 列の rank 上位）を**取れる**。`cid` 列で `relation_paths` の source_cid / target_cid と **join できる列が在る**。（注: seed0 の sim_matrix は 228 CID＝その seed の run-end 対象 CID。relation_paths の CID と完全一致するかは join 時に要確認。本 STEP は「列が在る・join 可能」までの確認。）

## Q3. 珍しさゲートの材料（dump）

データ: `source_events_seed0.parquet`（21 列）。珍しさを測れる候補列が**在る**:
- `event_source_type`（種別頻度: pulse 12,530 / alpha_formation 1,067 / beta_formation 478 / ingestion 155 / c_conversion 155）
- `n_observed_pre`（min 0 / med 14 / max 134）
- `timestamp`, `source_cid`, `R_familiarity_pre`, `Q_pre`, `C_pre`, `n_alphas_pre`

→ 観察事実: 各 CID を `source_cid` で groupby し、`timestamp` 順に上記量の median/MAD（robust_z, MAD-DT 系）を per-CID で取る材料は `source_events` だけで**揃う**（外部結合不要）。

## Q4. 一方向保証の構造点（在/無、grep）

**書き戻し禁止先（物理・CID・ledger）の所在**:
- 物理: `genesis/canon/genesis_physics.py:232 def inject(...)` → `state.E[nid]` 書込（L240）、他に `state.theta[]`（L168）、`state.kill_link`。
- CID/atom テーブル: `developmental/v107/outputs/main/source_events_seed*.parquet`、`developmental/v106/outputs/main/cid_atom_sim_matrix_seed*.parquet`、per_subject 系。
- ledger: `unified/v1101a/v1101a_phase_2_step_b_cid_state_ledger.py`、`developmental/v104/v104_spend_audit_ledger.py`。

**atom 専用世界の書込先（新規 output パス）**: 現状**未作成**（atom×atom を書く専用ディレクトリは無い。設計時に新規作成する想定。例えば `unified/v1201/atom_world/` 等は未存在）。

**この STEP の物理書込確認**: 本 STEP は調査スクリプトを作っていない（`python -c` の dump と grep のみ実行、ファイル書込ゼロ）。よって物理/CID/ledger への書込は**無い**（grep 対象の永続スクリプトが存在しない）。

## Q5. 過去観察軸の照会（atom×atom 網は既に在るか、grep ベース）

**event 駆動で atom 同士を結ぶ関係網（atom が共有 event/CID を通して辺を張る網）**: grep 全 `unified/`・`developmental/` で、atom_pair/atom_edge/atom_graph/atom_network/atom_to_atom 等の event 駆動辺構築コードは**無し**。

**atom×atom の比較が在る箇所（但し event 駆動の網でなく別種、所在を明示）**:
1. `developmental/v108/v108_subsidiary_observations.py:5,88-106`: **25 atom × 25 atom = 300 ペア**、各 atom の「CID 波及プロファイル（delta vector）」の**相関係数**（whiteout 監視, 閾 0.7）。＝atom 間の「下流 CID 効果が似てるか」の相関であって、共有 event を通した辺ではない。
2. `unified/v1103/v1103_step_c_density_distribution.py`: 起点 atom → 応答 atom 分布を**centroid の cosine_similarity**（静的な意味類似）で。event 駆動でない。
3. `unified/v1106a/v1106a_step_l_verification_a.py:6`: atom 間距離（rc 指標）。コード内コメントで「本来の繋がり指標でない」と注記。

**v108 本体が結ぶ単位**: `v108_post_process.py` は `atom_id`（atom_introduction_event）→ target CID の pulse 応答（`v108_atom_co_occurrence_report.md`: 「atom_introduction_event 後に target が medium window で平均 +15 events の追加 pulse」）。＝**atom→CID 波及**。

→ 観察事実: Taka の読み「v108 は atom→CID 波及を測ったが atom 同士の網は組んでいない」は grep/コードと**一致**。atom 同士の比較は (1) 波及プロファイル相関 (2) 静的 centroid cosine (3) rc 距離 の 3 種が在るが、いずれも**共有 event/CID を通して辺を育てる関係網ではない**。

---

## この STEP でやらなかったこと（明示）
網形成（辺を張る）・可視化・effect_size/cosine/cohens_d 等の演算・cid pool 選抜 は**していない**。Q1-Q5 は dump と在/無のみ。

*以上、Atomset（atom×atom 関係網）STEP 1 調査（Code A、2026-06-16）。Q1=経路で到達 CID は変わる(全経路同一=False)、Q2=cid_atom_sim_matrix で membership 取得・join 列在り、Q3=source_events だけで珍しさ材料(event種別頻度/n_observed_pre/per-CID robust_z)揃う、Q4=書込禁止先(genesis_physics.inject/CIDテーブル/ledger)列挙・atom世界の新規パス未作成・本STEPは書込ゼロ、Q5=event駆動 atom×atom 網は無し(atom間比較は波及相関/静的cosine/rc距離の3種のみ)。設計示唆は書かない(Web Claude 次段)。*
