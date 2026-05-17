# 改訂フレーム「ESDE スケール注意機構」 環境チェック報告 — Code A

*作成*: 2026-05-17、Code A
*親*: `esde_scale_attention_revised_frame.md` (Web Claude 改訂フレーム、本会話 2026-05-17 受領 / **未 repo 化**) + Taka 主題化決定 (2026-05-17) + Taka Step 7-③ 環境チェック先行承認 (2026-05-17、バージョン番号確定待ち並行進行)
*対象*: Web Claude (相談役) + Taka (バージョン番号確定 + 段階 1 着手判断)
*目的*: 改訂フレーム §2 既存機構 (v10.2/v10.5/v10.6/v10.7/v1101) の実環境 read-only 照合 + 段階 1 で読める形か + 出力先ディレクトリ確保案 (バージョン未確定下の仮固定) + 監査修正 #2 #3 反映後の段階 1 工数見積 (Code A 実測ベース)
*位置*: 改訂フレーム §8 進行表の **Step 7-③** に相当。Step 7-① (Taka バージョン番号確定) と並行先行
*配置*: 仮配置 `unified/v1101/post_v1101_attention_pre_investigation/step_4_environment_check.md`、Step 7-① 確定後に正規ディレクトリ (`unified/v1101a/` or `unified/v1102/`) へ改訂フレーム本体と共に移動想定

---

## 0. 一文サマリ

改訂フレーム §2 既存機構 5 系統 (v10.2/v10.5/v10.6/v10.7/v1101) の実環境照合を read-only で完了 (書き込みなし)、v10.5 Salience-driven Focus emitter (`v105_salience.py` L104-134 `log_event`、per-event 記録 seed/step/observer_cid/candidate_cid/candidate_mass/selected/event_type) が実出力 `diag_v105_main/salience/salience_event_log_seed{0..23}.csv` (3114 rows/seed × 24 seeds、read_other 2610 + be3_fired 504) として既存、本主題 §3.4 注意 emit スキーマの直接前例と確認、v10.2 P(認知)=Q/(Q+C) のデータ実体は v10.6 trajectory の `Q_remaining_at_window_end` / `C_at_window_end` が時系列化済で CID 単位 `qc_ratio` per-window 算出に直接使用可、Integration 単位は `alpha/beta_atom_aggregate` の member_cids ごと集計可、v10.6 4 解像度 (event/pulse/step10/window) 全てに `rank_1_atom` + `rank_1_sim` + Q/C per-window が揃い `atom_delta` (rank_1_sim Δt 差分) + `rank1_flip_density` (rank_1_atom 変化頻度) + per-window `qc_ratio` を直接算出可、ただし `unit_KL_delta` は `cid_atom_sim_matrix` が run 最終時点の静的データのため時間軸付き KL は段階 1 で出せず段階 2 (cid state ledger 再生) 行き候補、v10.7 `relation_paths_seed{N}.parquet` (851k rows/seed × 8 cols × 24 seeds) に 5 種 relation_path_type 揃い (temporal_coactivation 281k / attention_via_salience 219k / familiarity 165k / integration_alpha 105k / integration_beta 80k) + `baselines_with_delta_seed{N}.parquet` (1.76M rows × 26 cols × 24 seeds) で relation_path_type 別 delta_R_familiarity/Q/C × immediate/short/medium があり §3.3 因果候補・影響候補観察に直接流用可、v1101 `observation_2_propagation.parquet` (220500 rows × 17 cols、中心 cid × Δt 21 点 × 13 列) は §3.3 「注意候補中心の波及」テンプレートとして中心置換のみで成立、`observation_2_events.parquet` (10500 × 15) に `Q_pre/C_pre/Q_after/C_after` ありで CID 単位 `qc_ratio` per-event も同時算出可、新規 main run 不要 (改訂フレーム §5 段階 1 と整合)、書き込みは新規 `unified/v{番号}/outputs/` 配下のみで物理層 frozen 絶対遵守、改訂フレーム本体 (`esde_scale_attention_revised_frame.md`) は **ディスク未配置** (Web Claude 会話送信のみ) で Step 7-② 正規配置時に本書と同時書き出し必須、出力先候補は v11.0.1.a 採用なら `unified/v1101a/`、v11.0.2 採用なら `unified/v1102/` の 2 系統、段階 1 工数見積は v1101 Step B-H 実工数 (63 分、commit timeline 実測) を base に監査修正 #2 (qc_ratio 6 構造単位並列) + #3 (変化指標 3 系列分離) の並列化増分を加算して **5.5-9.5 時間** の幅 (unit_KL_delta 取扱次第)、出力規模見積は 30-50 MB (v1101 main 6.9 MB の数倍想定、storage 圧迫小)、絶対格言 15 件遵守 (#3 ベースライン比較は v10.7 baselines_with_delta で確保、#9 神の手回避は監査修正 #3 統合スコア禁止で確保、#4 集団平均の罠は監査修正 #2 構造単位別並列で確保)、Web Claude/Taka 確認要請 3 件 (unit_KL_delta 段階 1 取扱 / 注意候補 raw vs top_k / predecessor_attention_ref 参照粒度) を §5 で整理、Step 7-① バージョン番号確定後に正規配置 + Step 7-④ 段階 1 着手の流れ。

---

## 1. 既存機構の実環境照合 (改訂フレーム §2、read-only)

### 1.1 v10.5 Salience-driven Focus — emitter 実体

| 項目 | 実装位置 / 出力位置 |
|---|---|
| emitter ロジック | `developmental/v105/v105_salience.py` L104-134 `log_event` |
| per-event 記録列 | seed, step, observer_cid, candidate_cid, candidate_mass, selected, event_type |
| 実出力 (per-seed) | `developmental/v105/diag_v105_main/salience/salience_event_log_seed{0..23}.csv` × 24 seeds |
| 規模 (seed 0 実測) | 3114 rows (read_other 2610 + be3_fired 504) |
| selector (本主題段階 1 不採用) | `select_ingestion_target` (L175-257)、改訂フレーム §3.5 emitter 境界条項により段階 1 内では参照しない |

→ **本主題 §3.4 注意 emit スキーマの直接前例**。スキーマ拡張点は § 1.6 で整理。

### 1.2 v10.2 P(認知)=Q/(Q+C) — データ実体は v10.6 trajectory に時系列化済

v10.2 は概念的起点。`qc_ratio` の per-time-series 算出に使うデータは v10.6 側にあり、v10.2 単独の追加 read は不要。

| 構造単位 | データソース | 集約方式 |
|---|---|---|
| CID | v10.6 trajectory の `Q_remaining_at_window_end` / `C_at_window_end` | per-window 直接算出 |
| Integration α | `alpha_atom_aggregate_stratified_seed{N}.csv` の member_cids | member 全 cid の Q+C 集約 |
| Integration β | `beta_atom_aggregate_seed{N}.csv` の member_cids | 同上 |
| ESDE-event/step10/window | v10.6 4 解像度 trajectory を per-resolution 集約 | 監査修正 #2 に従い **単一値作らず**、下位単位の多数決 or 中央値で `qc_regime` 判定 |

### 1.3 v10.6 4 解像度 trajectory — 24 seeds 完全揃い (v1101 Step B 確認済 + 列再確認)

| 解像度 | ファイル | 主要列 |
|---|---|---|
| event | `event_trajectory/event_cid_alignment_seed{0..23}.csv` × 24 | seed, cognitive_id, t, source, window, **rank_1_atom**, **rank_1_sim**, **C_at_window_end**, **Q_remaining_at_window_end**, R_familiarity |
| pulse | `pulse_trajectory/pulse_cid_alignment_seed{0..23}.csv` × 24 | + pulse_n, trigger, v11_captured |
| step10 | `step10_trajectory/step10_cid_alignment_seed{0..23}.csv` × 24 | + cumulative_pulse_count, cumulative_n_ingestions |
| window | `window_trajectory/window_cid_alignment_seed{0..23}.csv` × 24 | + window_fam_max, max_sim, mean_sim |

→ **4 解像度全てに `rank_1_atom` + `rank_1_sim` + Q/C per-window が揃う**。本主題 §3.2 監査修正 #3 の 3 系列のうち:
- `atom_delta` = `rank_1_sim` の Δt 差分: ✓ 算出可
- `rank1_flip_density` = `rank_1_atom` 変化頻度: ✓ 算出可
- `unit_KL_delta` = 観察単位間 atom 分布 KL の時間差分: △ **段階 1 で出せず** (詳細 §2.2)

### 1.4 v10.7 5 種 relation_path — 完全揃い

| 出力 | 所在 | 規模 (seed 0 実測) | 用途 |
|---|---|---|---|
| `relation_paths_seed{0..23}.parquet` | `developmental/v107/outputs/main/` × 24 | 851154 rows × 8 cols | 5 種 relation_path: event_id × source_cid × target_cid × relation_path_type × relation_strength × hop_distance |
| `baselines_with_delta_seed{0..23}.parquet` | 同上 × 24 | 1763031 rows × 26 cols | relation_path_type 別 delta_R_familiarity/delta_Q/delta_C × immediate/short/medium |

5 種 relation_path_type 実測 (seed 0):
- temporal_coactivation: 281190 (33%)
- attention_via_salience: 219003 (26%)
- familiarity: 165547 (19%)
- integration_alpha: 105521 (12%)
- integration_beta: 79893 (9%)

→ **§3.3 因果候補・影響候補観察の素材完備**。注意候補 (=各変化定義での最大変化 cid) を source として上記 5 種から target を抽出するだけで `causality_candidate_path` (最強 relation_path_type) 算出可。`baselines_with_delta` で効果サイズも同時取得 (絶対格言 #3 遵守)。

### 1.5 v1101 観察 2 propagation — 「注意候補中心の波及」テンプレート

| 出力 | 規模 | 用途 |
|---|---|---|
| `unified/v1101/outputs/main/observation_2_propagation.parquet` | 220500 rows × 17 cols (中心 cid × Δt 21 点 × 列) | §3.3 「注意候補中心の波及」観察の構造テンプレート。中心定義を「v10.12 受容 cid」から「attention_candidate」に置換のみで spec 成立 |
| `unified/v1101/outputs/main/observation_2_events.parquet` | 10500 rows × 15 cols | source_cid × timestamp × atom_id × **Q_pre/C_pre/Q_after_atom_intro/C_after_atom_intro** 持ち。CID 単位 `qc_ratio` per-event 算出に直接流用可 |

列構造 (`observation_2_propagation.parquet`):
```
seed, event_id, source_cid, atom_intro, t0_aligned, delta_t, t,
n_cids_alive, n_cids_matching_atom_intro, match_fraction,
n_unique_atoms, atom_entropy_bits, mean_rank_1_sim,
center_alive, center_rank_1_atom, center_rank_1_sim, center_atom_matches_intro
```

→ Δt × 周辺集計列 (`n_cids_alive`, `match_fraction`, `atom_entropy_bits`) は §3.3 `influence_candidate_count` の直接的計算基盤。

### 1.6 注意 emit スキーマ拡張点 (v10.5 log_event ベース)

v10.5 既存列: `seed, step, observer_cid, candidate_cid, candidate_mass, selected, event_type`

本主題 §3.4 で追加する列:
| 列名 | 既存/追加 | 由来 |
|---|---|---|
| seed, step | 既存 | v10.5 log_event 由来 |
| `change_scope` | **追加** | 6 構造単位 (CID/α/β/ESDE-event/ESDE-step10/ESDE-window)、監査修正 #2 |
| `change_metric_type` | **追加** | atom_delta / rank1_flip_density / unit_kl_delta、監査修正 #3 |
| `change_metric_value` | **追加** | raw value、確率的記述 (箱 3) |
| `change_rank_within_type` | **追加** | metric type 内順位、監査修正 #3 |
| `attention_candidate_id` | **追加** (改名) | v10.5 `candidate_cid` から拡張。命名は target でなく candidate (箱 3) |
| `qc_ratio` | **追加** | change_scope 単位での Q/(Q+C)、§3.1 監査修正 #2 |
| `qc_regime` | **追加** | cognitive_dominant / conscious_dominant、多数決 or 中央値 (修正 #2) |
| `predicted_lock_mode` | **追加** | 旧 attention_locked、記録専用予測 (修正 #4) |
| `predecessor_attention_ref` | **追加** | 意識優位時の踏み台参照 (箱 1) |
| `causality_candidate_path` | **追加** | v10.7 5 path のうち最強 relation_path_type (§3.3) |
| `influence_candidate_count` | **追加** | Δt 範囲内の周辺一致 cid 数 (§3.3、v1101 observation_2 同型) |

---

## 2. 段階 1 で組める部分・組めない部分の境界

### 2.1 既存出力で組める (新規 main run 不要、改訂フレーム §5 段階 1 と整合)

| 設計要素 | データソース | 算出方式 |
|---|---|---|
| qc_ratio CID 単位 | v10.6 trajectory Q_remaining/C_at_window_end | per-window 直接算出 |
| qc_ratio Integration α/β 単位 | alpha/beta_atom_aggregate member_cids | member 集約 |
| qc_ratio ESDE 単位 (event/step10/window) | v10.6 trajectory | **下位単位の多数決 or 中央値** (修正 #2、単一値作らず) |
| atom_delta | v10.6 rank_1_sim | Δt 差分 |
| rank1_flip_density | v10.6 rank_1_atom | Δt 内変化頻度 |
| 注意候補中心の波及 | v1101 observation_2_propagation 同型 + v10.6 4 解像度 trajectory | 中心 = attention_candidate に置換 |
| causality_candidate_path | v10.7 relation_paths_seed{N}.parquet + baselines_with_delta_seed{N}.parquet | source=attention_candidate で 5 種別に集約 |
| influence_candidate_count | v1101 observation_2_propagation 同型 | Δt 範囲内 一致 cid 数 |
| predecessor_attention_ref (箱 1) | 同 seed 内 attention_emit_log の前順走査 | qc_regime 切替前最後の cognitive 状態 attention_candidate 参照 |

### 2.2 段階 1 で組めない / 要 Web Claude・Taka 判断

| 設計要素 | 障害 | 選択肢 |
|---|---|---|
| `unit_KL_delta` (時間軸付き) | `cid_atom_sim_matrix` は run 最終時点の静的データ。各 cid の atom 分布の時系列がない | (i) 段階 1 で `unit_KL_static` (時間軸なし、構造単位間距離) のみ出す / (ii) 段階 2 へ送る (段階 1 は 2 系列運用) / (iii) 段階 1 で cid state ledger 部分再生 (+1.5-2 日、段階 2 と境界曖昧化) |

→ 詳細・Code A 仮所見は §5.1 確認要請。

---

## 3. 出力先ディレクトリ確保案 (バージョン未確定下の仮固定)

### 3.1 バージョン番号別配置候補 (Step 7-① Taka 判断対象)

| バージョン候補 | 配置先 | 命名根拠 |
|---|---|---|
| **v11.0.1.a** | `unified/v1101a/` | v1101 の進化系として並列配置、v1100/v1101 と同階層 |
| **v11.0.2** | `unified/v1102/` | v1100/v1101 からの連番継続、独立番号 |

注: `developmental/v113a/` が既存だがこれは別文脈 (developmental シリーズの v11.3a)。`unified/` 配下の v1101a/v1102 は本主題専用で衝突なし。

### 3.2 仮配置先 (Step 7-① 確定前、本書を含む)

| ファイル | 仮配置 | Step 7-② 後の正規配置 |
|---|---|---|
| 本書 (環境チェック報告) | `unified/v1101/post_v1101_attention_pre_investigation/step_4_environment_check.md` | `unified/v{番号}/v{番号}_step_b_environment_check.md` (v1101 命名規則同型) |
| 改訂フレーム本体 | **未 repo 化** (Web Claude 会話送信のみ) | `unified/v{番号}/v{番号}_phase_design.md` 相当として書き出し必須 |
| 既存: step_2_recognition.md / step_3_deliverable.md | 同 pre_investigation 配下 | そのまま history として残置 (移動しない) |

### 3.3 物理層 frozen 遵守 (絶対格言 #2 + 改訂フレーム §3.5 emitter 境界条項)

| 対象 | 読み取り | 書き込み |
|---|:-:|:-:|
| `developmental/v102/diag_v102_main/**` | ✓ (本書 ls + sample) | ✗ |
| `developmental/v105/v105_salience.py` + `diag_v105_main/salience/**` | ✓ (本書 read + sample) | ✗ |
| `developmental/v106/outputs/main/**` | ✓ (v1101 Step B + 本書 sample) | ✗ |
| `developmental/v107/outputs/main/**` | ✓ (本書 sample) | ✗ |
| `unified/v1101/outputs/main/**` | ✓ (本書 sample) | ✗ |
| `unified/v1101/post_v1101_attention_pre_investigation/` | (本書作成のみ) | ✓ |
| Step 7-② 後の `unified/v{番号}/outputs/` 配下 | — | ✓ (段階 1 で書き込み) |

emitter 境界条項 (改訂フレーム §3.5): `attention_emit_log` は段階 1 内では target selection / atom introduction 対象選別 / ingestion 選択 / 構造形成 fb に **使用しない**。後続主題で selector として使う場合は段階 1+ として別主題化 + その時点の認知層・意識層構造に対する独立監査必須。

---

## 4. 段階 1 工数見積 (Code A 実測、監査修正 #2 #3 反映)

### 4.1 v1101 Step B-H 実工数 (commit timeline 実測、参考)

| Step | commit 間隔 | 内容 |
|---|---|---|
| Step B (環境チェック) | 18 分 | db2bf45 |
| Step C (観察 1 一点) | 9 分 | 8b21637 |
| Step D (観察 2 propagation) | 9 分 | bea48a0 |
| Step E (観察 3) | 7 分 | 56f5ae6 |
| Step F (グラフ HTML) | 7 分 | 8315601 |
| Step G (bit-identity) | 7 分 | 2e468d2 |
| Step H (最終報告) | 6 分 | f3a4a95 |
| **合計** | **63 分** (約 1 時間) | |

→ v1101 が 1 時間で 7 step 完了したのは **既存出力流用 + 単純集計のみ** だったため。本主題は監査修正 #2 #3 で並列化・系列分離があり、Step C 同等の作業量は v1101 の 6-10 倍規模想定。

### 4.2 本主題段階 1 見積 (Code A 実測ベース)

| Step | 内容 | 想定時間 |
|---|---|---|
| Step B 同型 (本書) | 環境チェック (**完了済**) | 1-2 時間 |
| Step C 同型 | 注意 emit ログ生成: **6 構造単位 × 3 (or 2) 変化指標 × 24 seeds = 最大 18 系列並列** | 2-3 時間 |
| Step D 同型 | 注意候補中心の波及 (v1101 observation_2 同型、source 置換のみ) | 30 分-1 時間 |
| Step E 同型 | 因果候補抽出 (v10.7 relation_paths から source=attention_candidate で 5 種別) | 30 分-1 時間 |
| Step F 同型 | グラフ HTML 統合 (v1101 同型 + 6 単位 × 3 指標 panel) | 30 分-1 時間 |
| Step G 同型 | bit-identity 3 層検証 (層 A smoke 2 回 hash 一致 + 層 B v10.x main outputs mtime+size 不変 + 層 C 書き込み制限) | 30 分 |
| Step H 同型 | 観察事実最終報告 | 30 分-1 時間 |
| **合計** | | **5.5-9.5 時間** |

→ 改訂フレーム §5 「約 8.5-10 時間」は Web Claude 概算、Code A 実測ベースでは **5.5-9.5 時間** の幅。幅の主因は §5.1 確認要請 1 (unit_KL_delta 取扱) の選択:
- (i) 段階 1 で `unit_KL_static` 出す → 7.5-9.5 時間
- (ii) 段階 2 へ送る (2 系列運用) → 5.5-7.5 時間
- (iii) 段階 1 で cid state ledger 部分再生 → +1.5-2 日 (段階 2 と境界曖昧化、推奨せず)

### 4.3 出力規模見積

- v1101 main outputs: 6.9 MB (10 ファイル)
- 本主題: 注意 emit が最大 6 単位 × 3 指標 × 24 seeds = v1101 の数倍想定、**30-50 MB**
- v10.7 baselines_with_delta は流用 (新規生成なし、428 MB)、storage 圧迫小

---

## 5. Web Claude / Taka 確認要請

### 5.1 確認要請 1: unit_KL_delta の段階 1 取扱

`cid_atom_sim_matrix` が run 最終時点の静的データのため、時間軸付き観察単位間 KL の差分は段階 1 で算出できない。監査修正 #3 「変化指標 3 系列分離」を維持する方法 3 選択肢:

| 選択肢 | 内容 | 監査修正 #3 整合性 | 工数 |
|---|---|---|---|
| (i) | 段階 1 で `unit_KL_static` (時間軸なし、構造単位間距離) のみ出す | 「3 種類記録」で守る、時間軸の精度低下 | +0.5 時間 |
| (ii) | 段階 2 へ送る (段階 1 は atom_delta + rank1_flip の 2 系列運用) | 本数で守らない、スコープ縮小 | -0 (むしろ -1 時間) |
| (iii) | 段階 1 で cid state ledger 部分再生 | 厳密に守るが段階区分曖昧化 | +1.5-2 日 |

**Code A 仮所見**: (i) を提案。監査修正 #3 の核心は「種類を統合しないこと (神の手回避)」であり、時間軸の精度は副次。Web Claude/Taka 判断要請。

### 5.2 確認要請 2: 注意候補 raw vs top_k の保存方針

監査修正 #3 「top_k は表示用に限定し raw candidate を保存」に対し、raw のサイズは:
- per (構造単位 × 変化定義 × seed × time-resolution) で全 cid 候補を保持
- 圧縮込み概算: 30-50 MB (本主題段階 1 全体、§4.3 と整合)

**Code A 仮所見**: raw を parquet で全保存 (30-50 MB は storage 圧迫小)、表示用 `top_k = 10` (per 構造単位 per 変化定義) で `change_rank_within_type ≤ 10` を別ビューに切り出す。Web Claude/Taka 判断要請。

### 5.3 確認要請 3: predecessor_attention_ref の参照粒度

箱 1 「意識優位時、踏み台にした直前の認知的固定への参照」を実装する際の参照粒度:

| 選択肢 | 内容 |
|---|---|
| (i) | 同 seed 内の最も直近の qc_regime=cognitive 状態 attention_candidate を参照 (粒度粗) |
| (ii) | 同 seed 内 + 同 `change_scope` での最も直近を参照 |
| (iii) | 同 seed 内 + 同 `change_scope` + 同 `change_metric_type` での最も直近を参照 (粒度細) |

**Code A 仮所見**: (iii) を提案。`change_metric_type` 別に 3 系列分離する以上、踏み台も指標別に追う方が一貫性確保。Web Claude/Taka 判断要請。

### 5.4 確認要請 4 (Taka 専属): バージョン番号 (Step 7-①)

`v11.0.1.a` (v1101 進化系) / `v11.0.2` (独立番号) のどちらか。本書 §3.1 で配置先候補を 2 つとも整理済。確定後に Step 7-② 正規配置 → Step 7-④ 段階 1 着手の流れ。

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本書での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ §1 で実環境構造を先、§2-4 で組み立てと工数 |
| 2 | 物理層 frozen 絶対 | ✓ §3.3 で read-only 完全保証、書き込みは pre_investigation 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | ✓ v10.7 `baselines_with_delta` 流用で効果サイズ算出を §1.4 で確保 |
| 4 | 集団平均の罠 / 層化必須 | ✓ §1.2/§2.1 で監査修正 #2 (qc_ratio 構造単位別並列、ESDE 単位は多数決 or 中央値) を反映 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ §0.2 GPT-1 確定文言 (構造転換、軸追加でない) を起点として記述 |
| 6 | 出口の固定 | ✓ §4.2 で Step B-H 7 step を出口固定 |
| 7 | 主題着手前に上位資料を読む | ✓ 改訂フレーム + Code A Step 2/3 成果物 + v1101 Step B 同型を踏襲 |
| 8 | 過去観察軸の照会 | ✓ §1 で v10.2/v10.5/v10.6/v10.7/v1101 を実環境照合 |
| 9 | 神の手回避 | ✓ §1.6 / §5.2 で監査修正 #3 (統合スコア禁止、raw 保存) を反映 |
| 10 | 因果でなく因果候補 | ✓ §1.6 / §2.1 で `causality_candidate_path` / `influence_candidate_count` と候補表記 |
| 11 | 概念単位を雑に扱わない | ✓ change_scope / change_metric_type / emitter / selector / candidate を §1.6 で明示区別 |
| 12 | Aruism 判定回避 | ✓ success/fail なし、所在・規模・spec 整合のみ |
| 13 | AI を信じない原則は Taka 個人 | ✓ Code A 仮所見は明示し判断は Web Claude/Taka に委ねる (§5) |
| 14 | Taka 直感優先 + 直感語保存 | ✓ 改訂フレーム §1.1 / §4 の Taka 原文は本書では参照のみ、改変なし |
| 15 | 5 者運用体制の補完性 | ✓ §0 で 5 者 (Web Claude/Code A/GPT/Gemini/Taka) と本書位置を明示 |

→ **15 格言全項目遵守** (#3 は v10.7 流用、#4 #9 は監査修正 #2 #3 で構造的に確保)。

---

## 7. Step 7 進行への接続

| Step 7 | 担当 | 状態 | 依存 |
|---|---|---|---|
| ① バージョン番号確定 (v11.0.1.a or v11.0.2) | Taka | 待ち | — |
| ② 正規配置 (本書 + 改訂フレーム本体を `unified/v{番号}/` へ移動 + 書き出し) | Code A | ① 確定後 | ① |
| ③ 環境チェック (本書) | Code A | **完了** | — |
| ④ 段階 1 実装着手 (Step B 同型再開 → C-H) | Code A | 待ち | ① + ②、§5.1-5.3 Web Claude/Taka 判断 |

§5.1-5.3 (確認要請 1-3) は段階 1 着手前に Web Claude/Taka 判断要請、Taka バージョン番号確定 (Step 7-①) と並行で進められる。

---

## 8. 一文サマリ (再掲)

改訂フレーム §2 既存機構 5 系統 (v10.2/v10.5/v10.6/v10.7/v1101) の実環境照合を read-only で完了 (書き込みなし)、v10.5 Salience emitter の per-event ログ実体 (`diag_v105_main/salience/salience_event_log_seed{0..23}.csv` × 24 seeds × 3114 rows/seed) + v10.6 4 解像度 trajectory (event/pulse/step10/window、全て rank_1_atom + rank_1_sim + Q/C per-window) + v10.7 5 種 relation_path 完全揃い (`relation_paths_seed{N}.parquet` × 24 + `baselines_with_delta_seed{N}.parquet` × 24) + v1101 observation_2 propagation 17 列 + observation_2_events Q/C per-event の全データが本主題段階 1 (新規 main run 不要) に直接流用可と確認、ただし `unit_KL_delta` は cid_atom_sim_matrix が静的のため時間軸付きは段階 2 行き候補で §5.1 で 3 選択肢を Web Claude/Taka 判断要請、出力先候補は v11.0.1.a なら `unified/v1101a/`・v11.0.2 なら `unified/v1102/` の 2 系統 (§3.1)、改訂フレーム本体 (`esde_scale_attention_revised_frame.md`) は **ディスク未配置** のため Step 7-② 正規配置時に同時書き出し必須、段階 1 工数見積は v1101 Step B-H 実工数 63 分 (commit timeline 実測) を base に監査修正 #2 #3 並列化増分を加算して **5.5-9.5 時間** (unit_KL_delta 取扱で変動)、出力規模 30-50 MB (v1101 main 6.9 MB の数倍)、絶対格言 15 件遵守 (#3 v10.7 baselines、#4 構造単位別並列、#9 統合スコア禁止)、Web Claude/Taka 確認要請 3 件 (§5.1-5.3) + Taka 専属 1 件 (§5.4 バージョン番号)、Step 7-① バージョン確定 + §5.1-5.3 判断 → Step 7-② 正規配置 → Step 7-④ 段階 1 着手の流れ。

---

*以上、改訂フレーム「ESDE スケール注意機構」 環境チェック報告 (Code A、2026-05-17)。Step 7-① Taka バージョン番号確定 + §5.1-5.3 Web Claude/Taka 判断 → Step 7-② 正規配置 → Step 7-④ 段階 1 着手の流れ。Code A は §5.4 バージョン判断と §5.1-5.3 設計判断を待つ。*
