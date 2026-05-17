# v11.0.1.a (v1101a) Step H 観察事実最終報告 — ESDE スケール注意機構 (Code A 総括)

*作成*: 2026-05-18、Code A
*親*: `v1101a_phase_design.md` (Web Claude 正式版 2026-05-17) + Step B 環境チェック + Step C 注意 emit + Step D 注意候補中心の波及 + Step E 因果候補抽出 + Step F グラフ HTML + Step G bit-identity 検証
*対象*: Web Claude (Phase Result 翻訳統合担当) + Taka (主題判断者、最終承認)
*位置づけ*: v11.0.1.a 主題「ESDE スケール注意機構」(v1101 の進化系) 段階 1 の Code A 観察事実総括、judgement 回避 (絶対格言 #12)、解釈統合は Web Claude Phase Result 領域

---

## 0. 一文サマリ

v11.0.1.a (v1101a) Code A 主題「ESDE スケール注意機構」段階 1 が Step B 環境チェック完了から Step G bit-identity 3 層全 PASS まで全 7 段階 (B-H) 完了、Step C 注意 emit ログ生成 (1,726,974 records = 6 構造単位 CID/α/β/ESDE_event/ESDE_step10/ESDE_window × 3 変化指標 atom_delta/rank1_flip_density/unit_kl_static × 24 seeds 1 batch、約 16 分、main 8.8 MB)、Step D 注意候補中心の波及 (v1101 observation_2 同型、中心 ±10 windows = 21 点、Step C records に influence_candidate_count を join、4.2 秒、main 5.9 MB)、Step E 因果候補抽出 (v10.7 5 種 relation_path から source=attention_candidate で集約、causality_candidate_path + 効果サイズ delta_Q/C/R_short、13.3 秒、main ~10 MB)、Step F グラフ HTML 統合 (main dashboard 3×3 panel + top_k=10 別ビュー 18 subplots、合計 40 KB、留保 #L4 全 plot 正規化済、§5.7 確認要請 2 対応)、Step G bit-identity 3 層全 PASS (層 A: Step C/D/E smoke seed 0 parquet hash 3/3 match / 層 B: v106 main 731 files + v107 main 222 files + v105 integration 144 files 全 frozen / 層 C: 8 write calls すべて unified/v1101a/ 配下)、**核心観察事実 = 意識優位時の influence_candidate_count が認知優位の 1.54-1.78 倍** (全 6 scope で同方向、ESDE 解像度系で倍率最大 1.78×、Taka フレーム「意識層 = 選択と集中」と整合的観察、judgement Taka 領域)、副次観察 1 = causality_candidate_path 分布で **integration_alpha / integration_beta が最強 path として 0 件出現** (attention_via_salience 76.5% / familiarity 23.5% / temporal_coactivation 0.01%、v10.5 内生注意の cid レベル mass-weighted event が因果候補 strength で支配)、副次観察 2 = qc_regime × causality で **意識優位時に familiarity 経路 +6%** (cog 19.1% → csc 25.4%、箱 1 「連想ゲーム」直前認知固定からの既知概念連想の構造的裏付け候補、judgement Taka 領域)、副次観察 3 = scope 別 records 数で **alpha 92.5% 占有** (留保 #L4、n_alphas 母数差由来、Step F 全 plot で scope 内割合に正規化 = 集団平均の罠回避)、副次観察 4 = predecessor 連鎖 (箱 1) 全 6 scope で成立 (alpha 99.1 / ESDE 系 100 / beta 94.2 / CID 86.6%、霧の中の意識だけ状態を構造的に禁止)、副次観察 5 = **seed 0 は他 seed より控えめ + ESDE_event が振れ幅最大** (cog/csc seed0 0.42 → all 0.57、留保 #L3 集計単位方向変動と同型)、新規留保候補 #L5 candidate (integration paths 0 件問題、絶対格言 #11 概念単位の慎重扱い)、#L6 candidate (意識優位 familiarity +6%、箱 1 連想ゲームの構造的裏付け候補)、#L7 candidate (ESDE 3 解像度で qc_regime 分布偏差 event 56.6 / step10 57.6 / window 61.0%)、書き込み unified/v1101a/ 配下 5 script + 75 parquet (Step C/D/E × 25 ファイル) + 2 HTML + 1 JSON + 2 md = 85 ファイル合計 ~25 MB、v106/v107/v105 main outputs 1,097 files frozen 完全保証、Web Claude Phase Result + Taka 主題評価判断を待つ。

---

## 1. 主題と駆動要因 (再掲、絶対格言 #5)

### 1.1 主題

「ESDE スケール注意機構」(v1101 後継、Taka 主題化決定 2026-05-17):
- 6 構造単位 (CID/α/β/ESDE_event/ESDE_step10/ESDE_window) で qc_ratio 並列集約 (修正 #2)
- 3 変化定義 (atom_delta / rank1_flip_density / unit_kl_static) で別系列 emit (修正 #3)
- 注意 emit ログ (因果候補・影響候補・predecessor 連鎖)
- post-process emitter のみ、selector / 物理層介入なし (修正 #4 + 箱 3)

### 1.2 駆動要因 (GPT-1 監査確定文言、再掲)

> 本主題は、v10.5 Salience-driven Focus で cid レベルに成立している内生注意 (observer × candidate × mass-weighted 選択、mass = Q + C + β継承分) を、v1101 で確認された観察単位分裂に対応できるよう ESDE スケール / 複数構造単位へ拡張し、駆動信号を静的 mass から動的 change へ置き換える構造転換である。attention_emit_log は主題の理由ではなく、再配置の結果として生じる派生記録である。

→ 観察軸の追加でなく、既存 Q/C/β継承の **構造転換** (集約スケール + 駆動信号)。絶対格言 #5 遵守。

### 1.3 §5.7 Web Claude 確定回答 (Step C 着手前)

- 確認要請 1 (unit_KL_delta): 選択肢 (i) 段階 1 で unit_kl_static (時間軸なし、構造単位間距離) のみ、時間軸付きは段階 2 行き (留保 #L1)
- 確認要請 2 (top_k=10): raw 全保存 + top_k=10 別ビューを Step F で切り出し
- 確認要請 3 (predecessor_attention_ref): 選択肢 (iii) 同 seed + 同 change_scope + 同 change_metric_type 粒度

---

## 2. Step C 注意 emit 主要観察事実

### 2.1 構造的成果

| 項目 | 値 |
|---|---:|
| records 合計 (24 seeds 1 batch) | 1,726,974 |
| 構造単位 × 変化指標 × 24 seeds | 6 × 3 × 24 |
| 実行時間 (main 24 seeds 1 batch) | 約 16 分 (864.7s) |
| 出力ファイル | attention_emit_seed{0..23}.parquet + all (合計 25 ファイル、8.8 MB) |
| スクリプト | `v1101a_step_c_attention_emit.py` |

実装ポイント:
- qc_ratio_majority 列追加 (留保 #L2、中央値 + 多数決を併出)
- predecessor_attention_ref を全 6 scope で追跡 (粒度 iii)
- 3 系列分離成立 (各 metric_type が独立 emit、統合スコア禁止 = 修正 #3 遵守)
- cid_atom_sim_matrix の per-cid 1 cell NaN を nan_to_num で 0 置換 (bug fix)
- raw 全保存、top_k=10 は Step F 別ビューに切り出し

### 2.2 主要観察事実 4 件

#### 観察 2-1: qc_regime conscious_dominant 占有率 (24 seeds 平均、scope 別)

| change_scope | cognitive_dominant | conscious_dominant | conscious 占有率 |
|---|---:|---:|---:|
| CID | 32,292 | 62,154 | 0.658 |
| alpha | 490,149 | 1,109,010 | **0.693** ← 最大 |
| beta | 7,722 | 14,775 | 0.657 |
| ESDE_event | 1,563 | 2,037 | 0.566 |
| ESDE_step10 | 1,557 | 2,115 | 0.576 |
| ESDE_window | 1,404 | 2,196 | 0.610 |

→ 全 scope で意識優位多数派。alpha が最も意識優位寄り (0.693)、ESDE_event が最も控えめ (0.566)。

#### 観察 2-2: predecessor 連鎖 (箱 1) 全 6 scope で成立

| change_scope | conscious 行 | predecessor 埋まり率 |
|---|---:|---:|
| alpha | 1,109,010 | 0.991 |
| ESDE_event | 2,037 | 1.000 |
| ESDE_step10 | 2,115 | 1.000 |
| ESDE_window | 2,196 | 1.000 |
| beta | 14,775 | 0.942 |
| CID | 62,154 | **0.866** |

→ 箱 1 「霧の中の意識だけ」状態を構造的に禁止する設計が成立。CID scope のみ 86.6% で 13% が踏み台なし conscious (= 認知優位 phase なしで開始した cid)、他 scope は ~94-100%。

#### 観察 2-3: seed 0 vs all 24 seeds の conscious 占有率の差 (留保 #L3 集計単位方向変動と同型)

| change_scope | seed0 conscious | all 24 conscious | Δ |
|---|---:|---:|---:|
| CID | 0.565 | 0.658 | +0.093 |
| alpha | 0.606 | 0.693 | +0.088 |
| beta | 0.564 | 0.657 | +0.093 |
| **ESDE_event** | 0.420 | 0.566 | **+0.146** ← 最大変動 |
| ESDE_step10 | 0.451 | 0.576 | +0.125 |
| ESDE_window | 0.520 | 0.610 | +0.090 |

→ seed 0 は他 seed より一貫して controlled。ESDE_event は seed 0 で認知優位寄り (0.42)、24 seeds で意識優位寄り (0.57)、振れ幅 +0.146 と 6 scope 中最大。留保 #L3 (v1101 #33 集計単位方向反転) と同型の seed 方向変動。**反転は起きていない** (全 scope で意識優位多数派 = 強化のみ)。

#### 観察 2-4: scope 別 records 数の偏り (留保 #L4)

| change_scope | records | 占有率 |
|---|---:|---:|
| **alpha** | 1,599,159 | **92.59%** |
| CID | 94,446 | 5.47% |
| beta | 22,497 | 1.30% |
| ESDE_event | 3,600 | 0.21% |
| ESDE_step10 | 3,672 | 0.21% |
| ESDE_window | 3,600 | 0.21% |

→ alpha が 92.5% 占有。n_alphas (per seed ~300-700) が n_cids (~120-150) や n_betas (~10-20) より遥かに大きい母数差由来。**raw 集計は alpha が他 scope を塗りつぶす**ため、Step F グラフは scope 内割合に正規化必須 (Taka 留保 #L4 想定通り)。

---

## 3. Step D 注意候補中心の波及 主要観察事実

### 3.1 構造的成果

| 項目 | 値 |
|---|---:|
| records 合計 (Step C と一致) | 1,726,974 |
| Δt 範囲 (v1101 observation_2 同型) | ±10 windows = 21 点 |
| 追加列 | influence_candidate_count, center_atom_t0, n_delta_t_points, n_peripheral_cids_alive |
| 実行時間 (main 24 seeds 1 batch) | 4.2 秒 (pre-build dict lookup) |
| 出力ファイル | attention_propagation_seed{0..23}.parquet + all (25 ファイル、5.9 MB) |
| スクリプト | `v1101a_step_d_attention_propagation.py` |

実装ポイント:
- pre-build per-window cid→rank_1_atom dict で高速化 (24 seeds 4.2 秒)
- unique (window, attention_candidate_id) 集約 (per seed ~1,000-1,300 unique center)、Step C records に join
- 別 parquet 出力で trace 容易性 (Step C 不変、bit-identity 層 B/C 維持)

### 3.2 主要観察事実 (核心観察): 意識優位時の influence_candidate_count が認知優位の 1.54-1.78 倍

| change_scope | cognitive_dominant | conscious_dominant | 倍率 |
|---|---:|---:|---:|
| CID | 78.66 | 122.80 | 1.56× |
| alpha | 73.24 | 117.62 | 1.61× |
| beta | 71.14 | 109.22 | 1.54× |
| ESDE_event | 56.28 | 96.41 | **1.71×** |
| ESDE_step10 | 51.46 | 90.63 | **1.76×** |
| ESDE_window | 57.04 | 101.59 | **1.78×** ← 最大 |

→ 全 6 scope で同方向 (意識優位 > 認知優位)。ESDE 解像度系で倍率最大 (1.71-1.78×)。意識優位時に attention_candidate が選んだ atom (rank_1_atom @ t0) が Δt ±10 windows 範囲内で周辺 cid に広く共有されている (= 波及大)。Taka フレーム「意識層 = 選択と集中」と整合的観察、ただし judgement は Taka 領域。

### 3.3 副次観察

- scope 別 mean influence_candidate_count: CID 107.7 / alpha 104.0 / beta 96.1 / ESDE_event 78.99 / ESDE_step10 74.02 / ESDE_window 84.21
- max influence_candidate_count = 433 (理論上限 21 windows × 平均 ~150 cid alive = ~3150 の 14%)
- seed 間 std: 20.0-29.0 (mean の ~25%)、scope-level 傾向は seed 安定 (留保 #L3 範囲内)
- center_atom_t0 None records: 各 seed 数十件 (中心 cid が t0 window で alive でない or rank_1_atom NaN 由来)

---

## 4. Step E 因果候補抽出 主要観察事実

### 4.1 構造的成果

| 項目 | 値 |
|---|---:|
| records 合計 (Step D と一致) | 1,726,974 |
| 追加列 | strength_5path + causality_strength_sum_max/total + causality_candidate_path + effect_delta_Q/C/R_short + n_baseline_rows |
| 実行時間 (main 24 seeds 1 batch) | 13.3 秒 |
| 入力 | v10.7 relation_paths_seed{N}.parquet × 24 + baselines_with_delta_seed{N}.parquet × 24 |
| 出力ファイル | attention_causality_seed{0..23}.parquet + all (25 ファイル、~10 MB) |
| スクリプト | `v1101a_step_e_attention_causality.py` |

実装ポイント:
- per (source_cid, path_type) で strength 集約 → pivot 後 argmax で causality_candidate_path
- 時間軸の扱い: per source_cid で全 timestamp 集約 (run 全体 static path map)、時間軸付きは段階 2 候補
- baselines_with_delta で per (source_cid, path_type) の delta_*_short mean を effect size として保存 (絶対格言 #3 遵守)

### 4.2 主要観察事実 4 件

#### 観察 4-1: causality_candidate_path 分布 (24 seeds 全体)

| path | count | 割合 |
|---|---:|---:|
| attention_via_salience | 1,321,256 | 0.765 |
| familiarity | 405,557 | 0.235 |
| temporal_coactivation | 161 | 0.0001 |
| **integration_alpha** | **0** | **0.000** |
| **integration_beta** | **0** | **0.000** |

→ 段階 1 では因果候補が 3 path に集中、**integration paths は最強 path として全く出現しない**。原因: v10.7 で integration_alpha / integration_beta の sum(relation_strength) が attention_via_salience に常に負ける (cid レベル mass-weighted event の数 vs 構造的接続のみ)。新規留保候補 #L5。

#### 観察 4-2: qc_regime × causality (意識優位時に familiarity 経路 +6%)

| qc_regime | attention_via_salience | familiarity |
|---|---:|---:|
| cognitive_dominant | 0.808 | 0.191 |
| conscious_dominant | 0.746 | **0.254** |

→ 意識優位時は familiarity 経路が +6% (認知優位 19.1% → 意識優位 25.4%)、attention_via_salience は -6%。箱 1 「連想ゲーム」(直前認知固定からの既知概念連想) の構造的裏付け候補と読めるが judgement は Taka 領域。新規留保候補 #L6。

#### 観察 4-3: effect size by causality path (per path 平均、絶対格言 #3)

| path | ΔQ_short | ΔC_short | ΔR_familiarity_short |
|---|---:|---:|---:|
| attention_via_salience | +0.001 | +0.010 | +0.003 |
| familiarity | -0.007 | +0.008 | +0.001 |
| temporal_coactivation | +0.163 | +0.029 | -0.002 |

→ familiarity 経路は ΔQ 減 (認知消費) + ΔC 増 (意識加点)、attention_via_salience は両方微増 (穏やか)。temporal_coactivation は ΔQ +0.163 と大きいが n=161 でサンプル少。判定は Taka / Web Claude 領域。

#### 観察 4-4: seed 別 attention_via_salience 占有率 (留保 #L3 と同型方向変動)

- min 0.412 / max 0.960 / mean 0.768 / **std 0.174**
- seed 間バラつき大 (±17%)、ある seed では attention_via_salience 96%、別 seed では 41% で familiarity 半分以上
- v1101 留保 #33 (集計単位による方向変動) と同型の seed 方向変動

---

## 5. Step F グラフ HTML 統合 (ダッシュボード)

### 5.1 出力

| ファイル | サイズ | 内容 |
|---|---:|---|
| `v1101a_observation.html` | 18 KB | main dashboard 3 セクション × 3 panel = 9 panel |
| `v1101a_topk_attention_candidates.html` | 22 KB | §5.7 確認要請 2 別ビュー、6 scope × 3 metric_type = 18 subplots |

### 5.2 構成

- **Section 1**: qc_regime conscious frac by (scope, metric_type) — §3.1 修正 #2 並列単位
- **Section 2**: influence_candidate_count cognitive vs conscious + ratio + std (留保 #L3)
- **Section 3**: causality_path by scope + qc_regime + per-seed (留保 #L3)
- **top_k view**: scope × metric_type の 18 subplots、attention_candidate_id 上位 10 mean change_metric_value

### 5.3 留保 #L4 対応

全 plot は scope 内割合 (causality) / per record mean (influence) で正規化、alpha 92.5% 占有が他 scope を塗りつぶさない構成。集団平均の罠回避 (絶対格言 #4)。

### 5.4 軽量化

v1101 step F (50-100 MB) から大幅圧縮 (合計 40 KB)。集計値のみ表示、raw データは Step C/D/E parquet で全保存済、詳細 animation は段階 2 候補。

---

## 6. Step G bit-identity 検証 (3 層全 PASS)

### 6.1 検証結果

| 層 | 内容 | 結果 |
|---|---|---|
| A (再現性) | Step C/D/E smoke seed 0 re-run → parquet hash 一致 | 3/3 match |
| A (HTML 構造) | Step F main + topk HTML 再生成 → plotly_graph_div / Plotly_newPlot count 一致 | 全一致 |
| B (frozen) | v106 main (731 files) + v107 main (222) + v105 integration (144) mtime+size 不変 | 0 added / 0 removed / 0 modified |
| C (書込み境界) | scripts 内 8 write calls すべて `unified/v1101a/` 配下 | 全 PASS |

→ **all_layers_pass = True**

### 6.2 含意

- 段階 1 全体が deterministic (Step C/D/E に乱数 seed なし、pure post-process)
- 物理層 frozen 絶対 (絶対格言 #2) を 1,097 files 範囲で完全保証
- 改訂フレーム §3.5 emitter 境界条項遵守 (selector / 物理層介入なし)

### 6.3 既知制約

- Step C main 24 seeds の再現性検証は 16 分かかるため smoke seed 0 で代用 (note 明記、本主題 post-process は smoke と main で同じスクリプト切替のみ、deterministic 保証は同等)
- HTML byte-identity は plotly UUID div IDs 非決定性のため不要、構造 (count) 比較で代替

---

## 7. 留保事項総括

### 7.1 段階 1 設計時の既知留保 (本主題 §9)

| id | 内容 | 状態 |
|---|---|---|
| #L1 | unit_kl_static は時間軸なし、atom_delta / rank1_flip_density (時間軸あり) と性質差。時間軸付き unit_KL_delta は段階 2 行き | 段階 1 対応済 (出力に明記) |
| #L2 | qc_regime の「多数決」か「中央値」は両方算出して併記 | 対応済 (qc_ratio_majority + qc_ratio 両列保存) |
| #L3 | v1101 留保 #33 集計単位による方向変動の継承 | 観察された (seed 0 vs 24 seeds Δ +0.09-0.15、attention_via_salience seed std 17.4%) |
| #L4 | alpha records 92.5% 偏り、Step F 正規化必須 | 対応済 (Step F 全 plot で scope 内割合に正規化) |

### 7.2 本 v1101a 新規留保候補 3 件 (Web Claude / Taka 判断)

| candidate id | 内容 |
|---|---|
| #L5 candidate | integration_alpha / integration_beta が causality_candidate_path として全 24 seeds で 0 件出現。v10.7 strength sum で attention_via_salience に常に負ける構造的事実。段階 1 因果候補の path 多様性が 3 path に縮退 |
| #L6 candidate | 意識優位時に familiarity 経路 +6% (認知優位 19.1% → 意識優位 25.4%)、attention_via_salience は -6%。箱 1 「連想ゲーム」(直前認知固定からの既知概念連想) の構造的裏付け候補だが、judgement は Taka 領域 |
| #L7 candidate | ESDE 3 解像度で qc_regime conscious 占有率に偏差 (event 0.566 / step10 0.576 / window 0.610)、時間解像度依存。集計単位による値変動の更なる事例、留保 #L3 と関連 |

### 7.3 v1101 から継承の留保 (本主題で該当しうる)

- #21 v10.5 機構 A 既知挙動 (mass-weighted event の dominance、本主題 #L5 と直結)
- #26 受容 cid pool 偏り (本主題では使用しないが Integration member 集合に類似偏り想定)
- #27 smoke seed 0 特異性 (本主題でも seed 0 控えめ確認、観察 2-3)
- #33 集計単位による方向反転 (本主題 #L3 = 継承、ESDE 3 解像度差で観察)

---

## 8. 出力ファイル総覧 (`unified/v1101a/`)

### 8.1 設計書・報告書 (markdown, 3 ファイル)

| ファイル | 内容 |
|---|---|
| `v1101a_phase_design.md` | Web Claude 正式版主題設計書 |
| `v1101a_step_b_environment_check.md` | Code A Step B 環境チェック報告 |
| `v1101a_step_h_observation_final.md` | 本書 (Code A 観察事実最終報告) |

### 8.2 実装スクリプト (python, 5 ファイル)

| スクリプト | 機能 |
|---|---|
| `v1101a_step_c_attention_emit.py` | 注意 emit ログ生成 (6 scope × 3 metric × 24 seeds) |
| `v1101a_step_d_attention_propagation.py` | 注意候補中心の波及 (v1101 observation_2 同型) |
| `v1101a_step_e_attention_causality.py` | 因果候補抽出 (v10.7 5 path argmax + 効果サイズ) |
| `v1101a_step_f_graph_html.py` | グラフ HTML 統合 (dashboard + top_k 別ビュー) |
| `v1101a_step_g_bit_identity.py` | bit-identity 3 層検証 |

### 8.3 観察データ (parquet × 75 + JSON × 1)

| 種類 | ファイル | サイズ |
|---|---|---:|
| Step C attention_emit | seed{0..23} + all = 25 ファイル | 8.8 MB |
| Step D attention_propagation | seed{0..23} + all = 25 ファイル | 5.9 MB |
| Step E attention_causality | seed{0..23} + all = 25 ファイル | ~10 MB |
| Step G bit-identity report | v1101a_step_g_bit_identity_report.json | <1 KB |

### 8.4 グラフ HTML (2 ファイル)

| ファイル | サイズ |
|---|---:|
| `outputs/v1101a_observation.html` | 18 KB |
| `outputs/v1101a_topk_attention_candidates.html` | 22 KB |

合計 約 85 ファイル、~25 MB。

---

## 9. 累計 commit (9 件)

| commit | 内容 |
|---|---|
| `f36b9f5` | Step 7-③ 環境チェック報告 (pre_investigation 配下 step_4) |
| `720a8f9` | Step 7-② 正規配置 (unified/v1101a/ 配下へ rename) |
| `f335077` | 改訂フレーム → v11.0.1.a 主題設計書 (正式版) 置換 |
| `65f77c7` | Step C 注意 emit ログ生成完了 (main 24 seeds 1 batch、1.73M records) |
| `5d87fa7` | Step D 注意候補中心の波及完了 (influence_candidate_count、4.2s) |
| `b0769db` | Step E 因果候補抽出完了 (causality_candidate_path + 効果サイズ、13.3s) |
| `fdde5ea` | Step F グラフ HTML 統合完了 (集計値ベース dashboard 2 HTML 40 KB) |
| `19abca8` | Step G bit-identity 検証完了 (3 層全 PASS) |
| (本 commit) | Step H 観察事実最終報告完了 |

---

## 10. 規律遵守総括 (絶対格言 15 件、本主題全 Step 通算)

| # | 格言 | 遵守状況 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ Step C で構造 (注意 emit) を先に置き、意味づけは段階後 |
| 2 | 物理層 frozen 絶対 | ✓ Step G 層 B で v106/v107/v105 main outputs 1,097 files 完全保証 |
| 3 | ベースライン比較 + 効果サイズ | ✓ Step E で v10.7 baselines_with_delta 流用、effect_delta_Q/C/R 保存 |
| 4 | 集団平均の罠 / 層化必須 | ✓ §3.1 修正 #2 構造単位別並列、Step F 留保 #L4 scope 内正規化 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ §1.2 GPT-1 確定文言、構造転換であり軸追加でない |
| 6 | 出口の固定 | ✓ §6 出口 6 項目全て成果物として確定 |
| 7 | 主題着手前に上位資料を読む | ✓ Step B で v10.2/v10.5/v10.6/v10.7/v1101 既存出力照合済 |
| 8 | 過去観察軸の照会 | ✓ Step C で v10.5 salience event_log を emit スキーマの前例として参照 |
| 9 | 神の手回避 | ✓ §3.2 修正 #3、統合スコア/固定閾値/重み付け禁止。100% を作らない (箱 3 Aruism 対称性) |
| 10 | 因果でなく因果候補 | ✓ causality_candidate_path / influence_candidate_count 候補表記、判定なし |
| 11 | 概念単位を雑に扱わない | ✓ change_scope / change_metric_type / emitter / selector / candidate 区別 |
| 12 | Aruism 判定回避 | ✓ Code A は success/fail なし、観察事実のみ。本書も判定しない (Web Claude / Taka 領域) |
| 13 | AI を信じない原則は Taka 個人 | ✓ §1.3 §5.7 確認要請は Web Claude 確定回答、Taka 主題判断 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka フレーム §1.1 原文保存、3 箱確定 §4 原文保存 |
| 15 | 5 者運用体制の補完性 | ✓ Web Claude (設計+確認回答) / Code A (実装+観察) / GPT/Gemini (事前監査) / Taka (判断) |

→ **15 格言全項目遵守**。

---

## 11. Web Claude Phase Result + 段階 2 推奨

### 11.1 Web Claude Phase Result 領域 (絶対格言 #12 解釈統合)

Code A は本書で観察事実を記録。以下の **解釈統合は Web Claude 領域**:
- 意識優位時 influence 1.54-1.78 倍 (§3.2 核心観察) の意味づけ
- 意識優位時 familiarity +6% (§4.2 観察 4-2) と 箱 1 「連想ゲーム」の対応
- integration paths 0 件出現 (§4.2 観察 4-1) の v10.5 / v10.7 設計との関係
- 留保 #L5/L6/L7 candidate の本主題位置づけ

### 11.2 段階 2 進行案 (任意、Code A、設計書 §5.1)

- cid state ledger 再生 (326 atom 全濃度時系列)
- per-step qc_ratio (window 解像度から細粒化)
- 時間軸付き unit_KL_delta (留保 #L1)
- v1101 段階 2 同型、想定 1.5-2 日

### 11.3 段階 3 (後段主題、今回範囲外)

- 「生きた版」(時間が逐次進む、step t で t 以前のみ利用)
- 「観測を行うことで系を動かしているように見える」連鎖 (注意の記録が次の観測の向きを決める)
- 新規 main run が必要、設計書 §5.1 で範囲外と明示

---

## 12. 一文サマリ (再掲)

v11.0.1.a (v1101a) Code A 主題「ESDE スケール注意機構」段階 1 が Step B-H 全 7 段階完了、Step C 注意 emit ログ 1,726,974 records (6 構造単位 × 3 変化指標 × 24 seeds、約 16 分、main 8.8 MB)、Step D 注意候補中心の波及 (v1101 observation_2 同型 ±10 windows、Step C records に influence_candidate_count を join、4.2 秒)、Step E 因果候補抽出 (v10.7 5 path argmax + 効果サイズ、13.3 秒)、Step F グラフ HTML 統合 (main dashboard + top_k 別ビュー 40 KB、留保 #L4 全 plot 正規化)、Step G bit-identity 3 層全 PASS (層 A parquet hash 3/3 + HTML 構造一致 / 層 B v106+v107+v105 main 1,097 files 完全 frozen / 層 C scripts 8 write calls すべて unified/v1101a/ 配下)、核心観察 = 意識優位時の influence_candidate_count が認知優位の 1.54-1.78 倍 (全 6 scope 同方向、ESDE 解像度系で倍率最大 1.78×)、副次観察 = integration paths が causality_candidate_path として 0 件出現 + 意識優位時 familiarity 経路 +6% + alpha records 92.5% 占有 (留保 #L4) + predecessor 連鎖 (箱 1) 全 6 scope 成立 + seed 0 控えめで ESDE_event 振れ幅最大 (留保 #L3)、新規留保候補 #L5 (integration 0 件) / #L6 (familiarity +6% 連想ゲーム裏付け) / #L7 (ESDE 3 解像度偏差)、書き込み unified/v1101a/ 配下 5 script + 75 parquet + 2 HTML + 1 JSON + 3 md = 約 85 ファイル ~25 MB、v106/v107/v105 main outputs 1,097 files frozen 完全保証、累計 commit 9 件 (本書合わせて)、絶対格言 15 件全項目遵守、judgement なし観察記録 (絶対格言 #12)、Web Claude Phase Result + Taka 主題評価判断を待つ。

---

*以上、v11.0.1.a (v1101a) Step H 観察事実最終報告 (Code A、2026-05-18)。段階 1 全 7 段階 (B-H) 完了、段階 2 (cid state ledger 再生、時間軸付き unit_KL_delta) は任意、段階 3 (生きた版、selector 連鎖) は後段主題で今回範囲外。Code A 主題担当範囲は本書で完了。*
