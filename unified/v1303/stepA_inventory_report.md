# v1303 Step A — Inventory Report（認識確認・実装前の必須ゲート）

*作成*: 2026-06-26、Code A。
*位置づけ*: v1303 主題設計書 完成版（Web Claude, 2026-06-25）§6.0 の **Step A**。【GPT 7-5】「認識確認＝inventory report に固定。inventory が出るまで Step B 禁止」に従い、3 レンズ（①CID固有値・②Atom一致率・③phys_core）の **データ源・列・粒度・取得コードの file:line・再走必要性・コスト** を read-only で棚卸しする。**本書は事実の棚卸しのみ。(a)/(b) 判定・主題評価はしない（#12）。**
*規律宣言*: 親 `physics/inject/ledger/state/per_subject/persistence` 非書込。本 Step は **既存ファイルの読み取りと行数確認のみ実施**、再走・smoke・本番は未実施（出力は本 md のみ）。
*上位資料の参照*: `docs/最低限規律.md` / `docs/ESDE_失敗の記録.md`(12型) / `docs/レポート/v1302_phase_result.md`(#CW1-11) / `docs/ESDE_技術仕様書.md`(§3.1/§4.1/§8.4/§8.5/§10.3/§10.5/§11.1) / `unified/v1301/physics_cid_ledger.md`(per_subject 130列台帳) を読了の上で作成。

---

## 0. 最重要の発見（Step B 設計に直結・3点）

### 0.1 【発見1】3 レンズの canonical run が割れている（anchor 統一が必須）
CID を索引キーにする以上、3 レンズは**同一の run（同一 CID 宇宙）**から来ねばならない（F型＝異系対応の回避）。実コードを辿ると現状は割れている：

| レンズ | 既存データが乗っている canonical run |
|---|---|
| ① per_subject（固有値） | 3 系統に存在: `developmental/v105/diag_v105_main/` ・ `developmental/v105/diag_v105_main_v2/` ・ `primitive/v918/diag_v918_main/`（各 seed 0-23, 24本） |
| ② Atom一致率（step10 alignment） | **`developmental/v105/diag_v105_main_v2/` のみ**（v106 が v2 を入力に固定、後述 §2） |
| ③ phys_core 再走 harness の前例（v1302） | **`primitive/v918/diag_v918_main/`**（cw_v1302 系が v918 seed0 を読む） |

→ **レンズ②（既算出・後述）が `diag_v105_main_v2` に固定されているため、anchor は `developmental/v105/diag_v105_main_v2` が自然**。v918 と v105 は別エンジン版（v918=primitive 130列 / v105=developmental α/β統合 152列）で **cognitive_id 空間が異なる**＝混在は E型/F型。**v1302 の再走 harness（v918 ベース）はそのまま使えない**——③の再走は v918 でなく **v105 main run を再現する**必要がある（§3 で詳述）。これは Step B 着手前に Web Claude/Taka が確認すべき第一の論点。

### 0.2 【発見2】レンズ②（rank_1 / rank_1_sim）は step10 で全24 seed が既に算出済み（再計算不要）
`developmental/v106/outputs/main/step10_trajectory/step10_cid_alignment_seed{0..23}.csv` が **24本そろって存在**。各行 = (cognitive_id, t=step10) で `rank_1_atom, rank_1_sim` を保持。→ **レンズ②は本体再計算が不要、ledger への join のみ**。ただし `rank_1_margin`（rank1−rank2）は全 atom cosine が要り、それは seed0 のみ（§2.4）。設計§2.5 通り **margin は第一段階で必須にしない**ので整合。

### 0.3 【発見3】レンズ③（生 E/θ/Z/S/R）は既存ログに無い＝決定論的再走が必須（設計§3.2 と一致）
既存ログは window(500step) 粒度の集計・age_r 等のみで、**各 step10 の member node 生 θ/E/Z・個別 link S/R の全件スナップショットは記録されていない**。→ 設計の Secondary Readout Pipeline（in-memory 再走で `engine.state` を吸い出す）が必要。再走は **v105 main run（§0.1）を再現**し、window cadence を変えずに **per-step ループ内に read-only スナップショット hook** を入れる形でないと bit-identity が壊れる（§3.4）。

---

## 1. レンズ① CID固有値（static / dynamic 分離）

**データ源（anchor 候補）**: `developmental/v105/diag_v105_main_v2/subjects/per_subject_seed{N}.csv`（seed 0-23、各 152列・228 CID/seed 前後）。
**生成コード**: `developmental/v105/v105_memory_readout.py:3069-3074`（CSV 書出し）・`:2841-3067`（subject_rows 構築）。
**粒度の注意（GPT 7-1）**: per_subject は **1 CID = 1 行＝最終状態（final）**。`v105_memory_readout.py:2841` で tracking 終了後に一度だけ構築。→ **dynamic 値を step10 全行に雑貼り禁止**。dynamic は別途 per-(cid,t) 源から取る（下表「step10 で取れるか」列）。

### 1.1 static_cid_features（誕生時固定＝全 t で定数として貼ってよい）
| 列 | 内容 | 取得元 file:line | step10 で取れるか |
|---|---|---|---|
| `v11_b_gen` | B_Gen | 計測 `primitive/v911/v911_genesis_budget_measure.py:40-70` / 記録 `developmental/v105/v105_memory_readout.py:1367-1389` / 出力 `:2987-3015` | 固定値 → 全 t に貼可 |
| `v11_m_c_n_core` / `_s_avg` / `_r_core` / `_phase_sig` | M_c | 同上（v11_record_birth_metrics） | 固定値 → 全 t に貼可。**n_core はここから（層化キー）** |
| `original_phase_sig` | phase_sig | 記録 `v105_memory_readout.py:597` / 出力 `:2894` | 固定値 |
| `birth_window` | 誕生 window | 記録 `:595` / 出力 `:2885` | 固定値 |

> 補足: `step10_cid_alignment`（§2）にも `n_core_member` 列が per-(cid,t) で入っており（merge_asof 由来）、n_core 層化はそちら経由でも可。

### 1.2 dynamic_cid_features（時変＝step10 の値が要る／final 貼り禁止）
| 列 | 内容 | 取得元 file:line | step10 で取れるか |
|---|---|---|---|
| `C_at_run_end`（final）/ `C_at_window_end`（per-t） | C＝消費Q | 計算 `developmental/v105/v102_orchestrator.py:46-90`(`v918_update_per_step`) / 確定 `developmental/v105/v102_cid_self_buffer.py:135-165` / **per-t は §2 step10 alignment の `C_at_window_end` 列に既存** | ✅ step10 alignment 経由で per-t 取得可 |
| `initial_residual_Q`/`final_residual_Q`/`total_q_*`（final）/ `Q_remaining_at_window_end`（per-t） | Q 残量・受領・消化 | 記録 `v105_memory_readout.py:648-671` / 集計 `:2865-2880` / **per-t は §2 step10 alignment の `Q_remaining_at_window_end` 列に既存** | ✅ step10 alignment 経由で per-t 取得可 |
| `current_social`/`_stability`/`_spread`/`_familiarity`（+`prev_`/`delta_`） | disposition 4軸 | 計算 `v105_memory_readout.py:2280-2283` / 記録 `:2331`(`set_current_disposition`) / 出力 `:2904-2907`（**最後の値のみ**） | ⚠ **per_subject は final のみ**。per-window 4軸の時系列 CSV は現存せず（`v18_window_trajectory_seed*.csv` は `diag_v105_main_v2` に**不在**を確認）。step10 で disposition 4軸が要るなら **③の再走時に同時吸い出し or 別途 per-window 再導出が必要**（§5 留保） |
| `final_state`/`host_lost_window`/`host_lost_step`/`reaped_step`/`ghost_duration_steps` | 存在状態 | 記録 `v105_memory_readout.py:663-671` / 再判定 `:2843-2860` / 出力 `:2885-2893` | host_lost_step/reaped_step は step 値 → step10 と境界判定可（§4） |

---

## 2. レンズ② Atom一致率（rank_1）— 既算出の join が本線

**データ源（既算出・再計算不要）**: `developmental/v106/outputs/main/step10_trajectory/step10_cid_alignment_seed{0..23}.csv`（24本確認済、seed0 で 62,907 行）。
**列**: `seed, cognitive_id, t, window, lifespan_so_far, n_core_member, final_state, C_at_window_end, Q_remaining_at_window_end, R_familiarity, cumulative_pulse_count, cumulative_n_alphas, cumulative_n_betas, cumulative_n_ingestions, rank_1_atom, rank_1_sim, top_category`。
**入力 run**: `developmental/v106/v106_step10_trajectory.py:29` が `DIAG_ROOT = V105_ROOT/"diag_v105_main_v2"` に固定（§0.1 の anchor 根拠）。

### 2.1 cid48 生成（②の中核）
- `developmental/v106/v106_step10_trajectory.py:217-231` `build_step10_cid_vector(row, seed_max) -> (48,) float32`。10 軸関数を concat、`:229-230` で `len==48` を assert。
- 10 軸の実装: `developmental/v106/v106_pulse_trajectory.py:180-299`（temporal7/scale6/epistemological5/ontological5/interconnection5/resonance4/symmetry5/lawfulness4/experience3/value_generation4）。
- step10 テーブル構築: `v106_step10_trajectory.py:85-215` `build_step10_table(seed)`（pulse/per_subject/audit/c_trajectory/ingestion を merge_asof で (cid,t) に backfill）。

### 2.2 atom 側（cid48 source）
- `developmental/v106/outputs/main/atom_profiles_cache.npz`（87 KB 確認）。keys = `atom_names (326,)` / `profiles (326,48) float32` / `valid_mask (326,)`（**325 valid / 1 NaN**＝設計の「326 valid325」と一致）。
- 生成: `developmental/v106/v106_post_process.py:209-231` `build_atom_cache` / プロファイル `:181-206` `load_atom_profile`（`language/atoms/a1_batch/{ATOM}.json` の word 48軸スコアを mean、simplex 和=1.0）。

### 2.3 rank_1 算出経路（既存、設計§10.3 通り）
- cosine: `v106_step10_trajectory.py:255-259`（valid 325 atom のみ `cosine_similarity`、無効列 NaN）。
- argmax で潰す: `:261-263`（`rank1=argmax`、`rank1_atoms`/`rank1_sims`）。→ 出力列 `rank_1_atom, rank_1_sim`。
- 設計§2.5 の保存列のうち `rank_1_atom, rank_1_sim` は **既存 CSV にあり**。`cid48_source_id` は明示列としては無いが **(seed, cognitive_id, t) が source_id を一意に与える**（build_step10_table の行と1:1、`v106_step10_trajectory.py:251-253`）。

### 2.4 全 cosine / rank_1_margin（第一段階では必須でない）
- argmax 前の全 cosine: `unified/v1201/full_cosine_probe/m31_full_cosine_probe.py`（`:36-62`）。出力 `full_cosine_step10_seed0.parquet`（62,906行×327列, 121.3MB／**seed0 のみ存在**）。コスト実測 `unified/v1201/full_cosine_probe/cost.json`（seed0 で 4.0s, 4粒度×24seed なら ~2.0TB/~6.4h の粗概算）。
- `rank_1_margin`(rank1−rank2) は **未算出**。必要なら full_cosine から `argsort()[-2]` で復元、または再計算。**設計§2.5 通り第一段階は不要（補助監査列）**。

---

## 3. レンズ③ phys_core（生 E/θ/Z/S/R）— 決定論的再走で吸い出す

### 3.1 engine.state の構造（読み取りフィールド）
| 変数 | 保持先 | file:line |
|---|---|---|
| E[node] (energy) | `state.E` (Dict[int,float]) | `ecology/engine/genesis_state.py:29` |
| θ[node] (phase) | `state.theta` (ndarray) | `genesis_state.py:33` |
| Z[node] (chem) | `state.Z` (ndarray) | `genesis_state.py:37` |
| ω[node] | `state.omega` (ndarray) | `genesis_state.py:34` |
| S[(i,j)] (link strength) | `state.S` (Dict[Tuple,float]) | `genesis_state.py:40` |
| R[(i,j)] (resonance) | `state.R` (Dict[Tuple,float]) | `genesis_state.py:43` |

link キー正規化 `state.key(i,j)=(min,max)`（`genesis_state.py:70-71`）。**read-only 参照のみ**（`engine.state.E[n]+=` 等は B型で禁止）。

### 3.2 member_nodes（CID 構成ノード）の所在と join
- 存在層 label = `frozenset(cluster_nodes)`、**誕生時固定・不解放**（技術仕様書 §4.1 `docs/ESDE_技術仕様書.md:191-192`）。
- v105 run 内: `vl.labels[lid]["nodes"]` を `frozenset` 化（`developmental/v105/v105_memory_readout.py:2091`、`:2109` で `"member_nodes"` として保持）。
- CidSelfBuffer registry（cid→buffer）が member_nodes/links snapshot を保持（`v105_memory_readout.py:1635-1636` registry、参考実装 `primitive/v918/v918_fetch_operations.py:42-53` の `member_nodes=frozenset(...)` / 内部 link 抽出 `for link in state.alive_l: if all(n in member_nodes for n in link)`）。
- → **member node id → state 配列要素 / member 内 link の S/R は engine.state から直接引ける**（§3.1）。

### 3.3 設計§2.3「乾かす」への対応（node 変数 / link 変数の分離・no link≠zero R）
吸い出し時に設計の必須区別を作れることを確認：
- node 変数（E/θ/Z）: `member_nodes` を sorted で回し `state.E/theta/Z[n]`。θ は circular mean / resultant length を後段で。
- link 変数（S/R）: `state.alive_l` のうち両端 member の link のみ。`core_internal_link_count`=該当 link 数、S/R は `state.S[link]`/`state.R.get(link,0.0)`。
- **【最重要】no_internal_link（該当 link 数=0）と internal_link_R0（link あり R=0）は engine.state で原理的に区別可能**（`alive_l` に member 内 link が無い＝前者 → null/missing 記録、ある＝後者 R=0 を記録）。混同回避は**実装側の責務**（n_core=2 偽ゼロ埋め防止、設計§2.3）。

### 3.4 phys_core_status / ghost 境界（設計§2.4・健全性1）
- 状態遷移: hosted(host_lost_step=NaN) → ghost(host_lost_step 設定, reaped_step=NaN) → reaped(残Q=0, reaped_step 設定)（技術仕様書 §5）。per_subject に `host_lost_step`/`reaped_step` 列あり（§1.2）。
- ghost 判定式の前例: `t >= host_lost_step & notna`（`unified/v1201/cid_trajectory_probe/m27_step1_trajectory_probe.py:82-84`）。→ **step10 の t で境界判定可**（window でなく step 値ゆえ境界ズレ最小）。
- 第一段階は **hosted_phys_core のみ**。ghost 化後の residual_node_phys_core は第二段階候補へ退避（設計§2.4）。`phys_core_status` 列は `host_lost_step`/`reaped_step`/snapshot 有無から導出。

### 3.5 再走 harness（v105 main を再現する）
- v105 main run 本体: `developmental/v105/v105_memory_readout.py:1475 def run(seed, maturation_windows=20, tracking_windows=10, ...)`。
  - engine 構築 `:1503 engine = V82Engine(seed=seed, N=N, encap_params=...)` + `:1504 engine.virtual = VirtualLayerV9(...)`。
  - 注入 `:1520 engine.run_injection()`。
  - window 駆動ループ `:1658 engine.step_window(steps=window_steps)`。
- **per-step ループ**: `autonomy/v82/esde_v82_engine.py:143 for step in range(steps)`（`step_window` 内）。→ **window cadence を変えずに、この per-step ループの 10step 毎に member_nodes の state を read-only でスナップショットする hook を挿す**のが正しい（window_steps を 10 に変えると window 境界処理＝disposition更新/label評価/α-β が動く位置がズレ run が別物になる＝bit-identity 崩壊）。
- 前例 harness: `unified/v1302/cw_v1302_abx.py:85-155`（engine 構築→run_injection→step_window 駆動→signature 抽出）。ただし**これは v918 ベースの child engine**で、v1303 ③は **v105 main の再現が要る**（§0.1）。

### 3.6 bit-identity / frozen 検証（設計§6.3・GPT 7-6）
- RNG 5分離: `docs/ESDE_技術仕様書.md:392-399`（engine.rng=seed / capture=seed^0xC0FFEE / ingestion=seed^0x1A7E57 / balance=seed^0xBA1A2C / cid_self_buffer 派生）。
- bit-identity 規律: §11.1（`docs/ESDE_技術仕様書.md:464-468`）。前例の確認法: 同 seed 2回で署名 MD5 一致（`cw_v1302_abx.py:222-235`）。
- **§6.3 の要件**: 単に「物理が同一か」でなく **instrumentation（snapshot hook）を入れても canonical run の既存出力（per_subject 等）が一字一句変わらないこと**を確認する。read-only hook（RNG を引かない・state を書かない）であれば不変のはず——Step E で同 seed 2回（canonical 出力＋ledger の両方）比較で実証する。

---

## 4. ghost/reaped の step10 判定（健全性1 の材料）
- `host_lost_step` / `reaped_step` は per_subject に step 値で存在（§1.2、`v105_memory_readout.py:663-671`）。
- 健全性1（設計§3.4）: `is_ghost XOR is_phys_missing` の総和=0 を assert → 崩れたら G型(timescale mismatch) or F型(配管ミス)。step 値ゆえ window join の境界ズレ問題は小さい（明記すべきは「step10 grid と host_lost_step の端数」程度）。

---

## 5. 再現性・コスト概算（設計§6.4「24並列一発で収まるか」）

### 5.1 何が再走要 / 既存で済むか
| レンズ | 再走要否 | 根拠 |
|---|---|---|
| ① static | 不要（per_subject 既存） | §1.1 |
| ① dynamic C/Q | 不要（step10 alignment に per-t 既存） | §1.2 / §2 |
| ① dynamic disposition 4軸(per-t) | ⚠ per-t 源が無い → ③再走で同時吸い出し or 別途再導出 | §1.2 |
| ② rank_1/rank_1_sim | **不要（24 seed 既算出）**、join のみ | §0.2 / §2 |
| ② rank_1_margin | 第一段階で不要（要れば full_cosine 再計算） | §2.4 |
| ③ phys_core 生 E/θ/Z/S/R | **必須（決定論的再走）** | §0.3 / §3 |

### 5.2 ③再走のスケール
- 1 seed の run 長: maturation 20×500 + tracking（標準 50、ただし v105 main の `run()` 既定は tracking_windows=10、**main_v2 実 run の tracking 窓数は run スクリプト引数を Step B で要確認**）+ injection 300。`docs/ESDE_技術仕様書.md:372/384-389`。
- 実時間: 単一 seed ~5 min（Ryzen 24C, OMP/MKL/OPENBLAS=1, `-j24`）。`技術仕様書 §8.4`。
- snapshot 規模の目安: step10 alignment が seed0 で 62,906 (cid,t) 行（`unified/v1201/full_cosine_probe/cost.json`）。③はそこに member node 単位（n_core 個）× 物理変数の列が乗る。**メモリ 500GB 非制約（Taka 方針）**ゆえ step10 全 snapshot in-memory 一括で可。ストレージ最小化の分割は不要（設計§6.4）。
- **24並列一発で収まるか**: seed 0-23 を `-j24` 一発、各 seed ~5min ＋ snapshot I/O。レンズ②③④の中で律速は③再走（~5min×並列）＝**24並列一発で現実的**（厳密 runtime は smoke seed0 で実測する）。

---

## 6. Step A 認識確認テーブル（設計§6.2 への直接回答）
| 対象 | 確認結果 |
|---|---|
| CID固有値 | per_subject 列・粒度=final・seed別 row≈228。static/dynamic 分離可。B_Gen/M_c/n_core/phase_sig/Q/C 取得元 file:line を §1 に明記。**dynamic C/Q の per-t は step10 alignment に既存** |
| disposition | 4軸の計算/記録 file:line は §1.2。**ただし per_subject は final のみ・per-window 時系列 CSV は不在**＝per-t は③再走同時吸い出し or 再導出が要る（留保） |
| Atom一致率 | cid48 生成 `v106_step10_trajectory.py:217-231` / atom_cache shape(326,48 valid325) / **rank_1 は全24seed step10 既算出**（再計算経路も §2.3 に明記） |
| phys_core | step10 の生 E/θ/Z/S/R snapshot は**既存に無い**。engine.state 吸い出し（§3.1）＋ member_nodes join（§3.2）＝**再走必須**。API・hook 位置 file:line を §3.5 に明記 |
| ghost/reaped | host_lost_step/reaped_step/final_state 列あり・**step10 で判定可**（§4） |
| 再現性 | ①②は既存で済む。③は**新規 run（v105 main の再現）が必要**。v1302 harness は v918 ベースで流用不可（§0.1/§3.5） |

---

## 7. Step B 着手前に Web Claude / Taka が確認すべき論点（判定は委ねる・#12）
1. **anchor の確定**: 3 レンズを `developmental/v105/diag_v105_main_v2` に揃える（②の既算出がそこに乗るため自然）でよいか。v918 系は使わない確認。
2. **③再走の対象 run**: v1302 の v918 child engine でなく **v105 main run（`v105_memory_readout.py:run()`）の再現**で member_nodes を v105_v2 と一致させる方針でよいか（main_v2 の実 tracking 窓数・引数を Step B 冒頭で固定）。
3. **disposition 4軸(per-t)**: ③再走時に `set_current_disposition` 相当の per-window 値も同時吸い出すか、第一段階は disposition を final/欠損扱いにして dynamic は C/Q 中心に絞るか。
4. **粒度の最終確認**: ledger は step10 固定（②③の自然粒度と一致）。①static は定数貼り、①dynamic は per-t、final 雑貼り禁止（GPT 7-1）を実装ガードに。

---

## 8. 規律遵守（本 Step）
- #2/B型: read-only のみ。既存ファイル read と行数確認だけ実施、書込は本 md。親 physics/inject/ledger/state/per_subject 非書込。
- #7: 上位資料（最低限規律・失敗記録12型・v1302_phase_result #CW1-11・技術仕様書 §3.1/§4.1/§8.4/§8.5/§10.3/§10.5/§11.1・v1301 physics_cid_ledger）を読了の上で作成。
- #11/L型: ①②③・node(E/θ/Z) と link(S/R)・R は link・no link≠zero R を区別して棚卸し。単一スコア化しない。乾いた列名前提。
- #12: (a)/(b) 判定なし。観察・棚卸し事実のみ。判定・主題評価は Taka/Web Claude。
- F型/E型: anchor 統一（同一 CID 宇宙）を §0.1/§7 で最優先論点として明示。
- smoke→本番（§6.1）: 本 Step では未実施。**inventory が出た＝Step A 出口達成。Step B（実装）は本書レビュー後**（smoke も Taka/Web Claude 承認後）。

---

## 9. 一文サマリ
v1303 Step A inventory（Code A, 2026-06-26、read-only 棚卸しのみ・実装/再走/smoke 未実施）── 3 レンズのデータ源を file:line で棚卸しした結果、**(発見1) canonical run が割れており**（②が `developmental/v105/diag_v105_main_v2` 固定・v1302 再走 harness は別系 v918）3 レンズの anchor を v105_v2 に統一し③再走も v105 main(`v105_memory_readout.py:1475 run()`=V82Engine+VirtualLayerV9)を再現する必要、**(発見2) レンズ②(rank_1/rank_1_sim)は step10 で全24 seed が既算出済**(`step10_cid_alignment_seed{0..23}.csv`)で再計算不要・join のみ(margin は seed0 full_cosine のみ＝第一段階不要)、**(発見3) レンズ③の生 E/θ/Z/S/R は既存ログに無く決定論的再走が必須**(engine.state `genesis_state.py:29-43` を member_nodes `v105_memory_readout.py:2091` で引き、per-step ループ `esde_v82_engine.py:143` に window cadence を壊さない read-only snapshot hook を挿す、no_internal_link≠internal_link_R0 を区別、bit-identity は instrumentation 込みで canonical 出力不変を Step E 検証)、レンズ①は static(B_Gen/M_c/n_core/phase_sig 固定)＝定数貼り可/dynamic(C/Q は step10 alignment に per-t 既存・disposition 4軸は per-t 源が無く③再走同時吸い出し要)で final 雑貼り禁止(GPT 7-1)、ghost/reaped は host_lost_step/reaped_step が step 値で step10 判定可(健全性1)、コストは①②既存・③のみ再走で 24並列一発が現実的(メモリ500GB非制約)、**(a)/(b) 判定はせず**、Step B 着手前に Web Claude/Taka が確認すべき論点(anchor 確定/③対象 run/disposition per-t/粒度ガード)を §7 に提示、出口＝本 inventory 完成ゆえ Step A 達成・Step B は本書レビュー後(smoke も承認後)。

---

*以上、v1303 Step A inventory report（Code A, 2026-06-26）。設計書§6.0 の Step A 出口＝本 `unified/v1303/stepA_inventory_report.md`。【GPT 7-5】に従い、本書がレビューされるまで Step B（ledger 実装）には進まない。最大の論点は §0.1/§7 の anchor 統一（②既算出が乗る v105_v2 に揃え、③再走を v105 main で再現）。*
