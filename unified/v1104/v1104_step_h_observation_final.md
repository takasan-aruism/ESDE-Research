# v11.0.4 (v1104) Step H 観察事実最終報告 — Code A

*作成*: 2026-05-23、Code A
*親*: `v1104_phase_design.md` (Web Claude 改訂版 v2、GPT 5 点 + Gemini 1 点反映済) + `v1104_step_a_recognition.md` (Code A 認識確認、Taka 承認済) + Step B-G 出力
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価)
*位置づけ*: v1104 主題「CID/IID が下でやっていることの点検 — 段 4-b/4-c を支える ESDE 内部処理の確認」の Code A 観察事実総括。**judgment 回避** (絶対格言 #12)、**判定語制限** (「連想」「成功/失敗」を使わない、GPT 追加 4)、**selector 化禁止遵守** (観察 4、GPT 修正必須 C)。

---

## 0. 一文サマリ

v1104 主題段階 1 Step A-H 全完了、Step A 認識確認 (時間軸同期 + IID 既存参照 + Jaccard 厳密化 + 判定語制限 + selector 化禁止) を Taka 承認、Step B 観察 1 (CID-Integration 像の差分、404,039 alpha-window records、n_members 増で match_rate_k1 が 0.884 → 0.569 と低下) / Step C 観察 2 (predecessor 連鎖、39,537 chains、85% self-loop、lift_over_baseline = 0 で shuffle と区別不能) / Step D 観察 3 (trajectory↔response 対応、972 rows、stability×max_prob Pearson r=0.157 弱い正相関 / diffusion×entropy r=0.020 相関なし) / Step E 観察 4 (際立ち掬い取り B 現状確認、81 cells、A∩B Jaccard 0.227、Recall 0.74、Precision 0.25、B 指標と A_score Pearson r<0.12 有意でない) / Step F グラフ HTML 4 観察 dashboard (13 KB) / Step G bit-identity 3 層全 PASS (v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 = 1,489 files frozen、Step B-E re-run 完全 deterministic) すべて完了、核心観察事実 (judgement なし、判定語制限遵守) は (1) **CID-Integration 像不一致が n_members 増で系統的に拡大** (n=1 match_k1=0.884 → n=4+ match_k1=0.569、inter_category_mismatch 0.24 → 1.85) で留保 #L14「CID 構成ノード数で atom 階層反転」と #33 系列「集計単位で像が変わる」と整合的、(2) **predecessor 連鎖は cid_atom_sim_matrix の類似度地形と shuffle baseline で区別不能** (lift=0)、self-loop 比率は CID 100% / alpha 99% / beta 99% / ESDE 系 95-97% で高、(3) **trajectory stability ↔ response_max_prob は弱い正相関** (r=0.157、有意) ・diffusion_ratio ↔ response_entropy は無相関 (r=0.020)、(4) **B (ESDE 自身の重要性 emit) と A (v1102 構造的指標) は弱い相関で部分的重なり** (Jaccard 0.23、Recall 0.74 = A 際立ち cell の 74% は B でもカバーされる subset 関係、ただし B 独自際立ち多数 = Precision 0.25)、新規留保候補 #L20 candidate (CID-Integration 像不一致と n_members の系統的関係) / #L21 candidate (predecessor 連鎖は類似度地形と区別不能、ランダム walk と等価な可能性) / #L22 candidate (trajectory stability と response 収束の弱い対応、48 次元密度との関係は別途検証要) / #L23 candidate (B と A の subset 関係、B は A の超集合を含むが独自シグナルも持つ)、48 次元人為性留保継承、判定 (各観察の出口 (a)/(b)、4 通り組み合わせ §4.2、次主題候補) は Web Claude Phase Result + Taka 主題評価領域、規律遵守チェック (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + 既存出力流用のみ) を全 Step で堅持、書込み unified/v1104/ 配下のみ。

---

## 1. Step A-H 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A | 認識確認 (時間軸同期 + IID + Jaccard + 判定語 + selector 禁止 6 項目) | 完了 (Taka 承認) | v1104_step_a_recognition.md |
| B | 観察 1 (CID-Integration 像差分、top-k Jaccard) | 完了 (19s) | observation_1_cid_integration.parquet (404,039 rows) |
| C | 観察 2 (predecessor 連鎖、判定語制限) | 完了 (56s) | observation_2_predecessor_chain.parquet (39,537 chains) |
| D | 観察 3 (trajectory↔response 対応、重複回避) | 完了 (7s) | observation_3_trajectory_response.parquet (972 rows) |
| E | 観察 4 (B 現状確認、selector 化禁止) | 完了 (1s) | observation_4_b_overlap.parquet (81 cells) |
| F | グラフ HTML (4 観察 dashboard) | 完了 | v1104_observation.html (13 KB) |
| G | bit-identity 3 層 | 完了 (all PASS、84s) | v1104_step_g_bit_identity_report.json |
| H | 観察事実最終報告 | 本書 | v1104_step_h_observation_final.md |
| I | Phase Result | 待ち | Web Claude 担当 |

---

## 2. 観察 1: CID-Integration 像の差分 (項目 1.1、段 4-c 挙動の根拠)

### 2.1 全体 (404,039 alpha-window records)

| 指標 | 平均 | 意味 |
|---|---:|---|
| match_rate_k1 | 0.7697 | CID 単独 rank_1_atom と α top_atom の完全一致率 |
| jaccard_top3 | 0.1069 | CID 静的 top-3 (cid_atom_sim_matrix) と α 動的 top-3 (per-window rank_1 集約) の Jaccard |
| jaccard_top5 | 0.0961 | 同 top-5 |

### 2.2 層化観察 (n_members_bin × qc_gini_bin、Step G 継承)

| n_members | qc_gini | n_records | match_k1 | inter_cat_mean |
|---|---|---:|---:|---:|
| n=1 | low | 187,085 | **0.884** | 0.24 |
| n=2 | low | 4,583 | 0.661 | 0.72 |
| n=2 | mid | 129,097 | 0.644 | 0.76 |
| n=2 | high | 9,349 | 0.638 | 0.76 |
| n=3 | high | 15,781 | 0.599 | 1.21 |
| n=3 | mid | 20,656 | 0.602 | 1.21 |
| n=3 | low | 110 | 0.660 | 1.03 |
| n=4+ | high | 5,019 | **0.569** | **1.85** |
| n=4+ | mid | 1,524 | 0.564 | 1.88 |
| n=4+ | low | 11 | 0.750 | 1.00 |

### 2.3 構造的事実 (Code A judgment 回避)

- **n_members 増 → match_k1 単調低下** (n=1: 0.884 → n=4+: 0.569、Δ-0.315)
- **n_members 増 → inter_category_mismatch 単調増加** (n=1: 0.24 → n=4+: 1.85、約 8 倍)
- jaccard_top3/5 全体的に低 (0.10 前後) — CID 静的特性 (sim_matrix) と α 動的応答 (per-window rank_1) は構造的に異なる集合
- 留保 #L14「CID 構成ノード数で atom 階層的反転」と #33 系列「集計単位で像が変わる」と整合的観察

### 2.4 新規留保候補 #L20

CID-Integration 像不一致と n_members の系統的関係 — match_k1 の n_members 単調依存性 (n=1 → n=4+ で Δ-0.315) を確認。

---

## 3. 観察 2: predecessor 連鎖の経路 (項目 1.6、段 4-b の核)

### 3.1 全体 (39,537 chains)

| 指標 | 平均 | 意味 |
|---|---:|---|
| chain_length | 29.67 | 連続 conscious window 数 (median 32、max 43) |
| n_unique_destinations | 1.46 | chain 内で predecessor → 何 unique cid に到達したか |
| n_self_loops | 25.29 | chain 内で predecessor == attention_candidate の回数 |
| mean_sim_along_chain | 0.9956 | chain 上 edge の cid_atom_sim_matrix cosine sim 平均 |
| **shuffle_baseline_sim_mean** | 0.9955 | 同列を permutation した baseline sim |
| **lift_over_baseline** | **0.0000** | sim - baseline |
| atom_changes/chain | 0.09 | chain 内で rank_1_atom が変わった回数 |
| category_changes/chain | 0.09 | 同 category 変化 |

### 3.2 scope 別

| scope | n_chains | sim_mean | baseline | lift | atom_chg_rate | self_loop_rate |
|---|---:|---:|---:|---:|---:|---:|
| **CID** | 3,798 | **1.0000** | 1.0000 | 0.0000 | 0.00 | **100%** |
| alpha | 34,812 | 0.9954 | 0.9954 | 0.0000 | 0.10 | 99% |
| beta | 711 | 0.9913 | 0.9910 | 0.0002 | 0.09 | 99% |
| ESDE_event | 72 | 0.9515 | 0.9515 | 0.0000 | 0.17 | 95% |
| ESDE_step10 | 72 | 0.9476 | 0.9477 | -0.0000 | 0.15 | 95% |
| ESDE_window | 72 | 0.9566 | 0.9568 | -0.0002 | 0.35 | 97% |

### 3.3 構造的事実 (Code A judgment 回避、判定語制限遵守)

- **predecessor 連鎖の cid 推移は shuffle baseline と統計的に区別不能** (全 scope で lift=0)
- **chain の 85% が self-loop**: CID scope 100%、alpha/beta 99%、ESDE 系 95-97%
- chain 内 atom 推移はほぼなし (atom_changes/chain ≈ 0.1)
- Code A は本観察を「連想を辿る」と判定しない (GPT 追加 4 遵守)、cid/atom/category/similarity 推移の構造的事実のみ記録
- 留保 #L8「CID scope 予測 self-reference (100% 到達)」と同型構造

### 3.4 新規留保候補 #L21

predecessor 連鎖は cid_atom_sim_matrix の類似度地形と区別不能 — lift_over_baseline=0 で shuffle baseline と一致、85% self-loop で経路の概念自体が「同一 cid に居続ける」状態を多く含む構造的事実。

---

## 4. 観察 3: attention trajectory ↔ response_atom_distribution 対応 (項目 1.7)

### 4.1 全体 (972 rows = receiver_bin × metric × qc_regime × sim_basis × k)

| 指標 | 平均 |
|---|---:|
| trajectory_stability (全 chains) | 0.9116 |
| response_max_prob | 0.2660 |
| response_entropy | 2.0785 |

### 4.2 対応観察 (相関分析)

| 対応 | Pearson r | p-value | 構造的事実 |
|---|---:|---:|---|
| trajectory_stability × response_max_prob | **0.157** | 8.8e-07 | **弱い正相関、有意** |
| diffusion_ratio × response_entropy | 0.020 | 0.53 | **相関なし** |

### 4.3 qc_regime × sim_basis 別

| qc_regime | sim_basis | stability | response_max_prob | response_entropy |
|---|---|---:|---:|---:|
| cognitive | norm | 0.820 | 0.359 | 1.90 |
| cognitive | raw | 0.820 | 0.173 | 2.25 |
| conscious | norm | 0.790 | 0.359 | 1.90 |
| conscious | raw | 0.790 | 0.173 | 2.25 |

### 4.4 構造的事実 (Code A judgment 回避)

- trajectory stability の cognitive vs conscious 差は 0.03 (小)、既知傾向と整合 (再観察回避遵守、GPT 追加 5)
- **trajectory 安定度 ↔ response 収束は弱い対応** (r=0.157)、強い対応とは言えない構造
- **trajectory 拡散度 ↔ response 拡散は無関係** (r=0.020)
- sim_basis (raw/norm) で response_max_prob 差: raw 0.173、norm 0.359 (留保 #L17 raw/norm Δ0.208 と整合)
- 設計書 §2.3.6 出口の (a)/(b) 境界: 完全な (a) (48 次元密度と同等以上) でも完全な (b) (無関係) でもない

### 4.5 新規留保候補 #L22

trajectory stability と response 収束の弱い対応 (r=0.157)、ただし 48 次元密度との関係は別途検証要 (本観察では trajectory 単独 vs response、48 次元密度との直接比較は未実施)。

---

## 5. 観察 4: 際立ち掬い取り B 現状確認 (項目 2.6、selector 化禁止遵守)

### 5.1 全体 (81 cells)

A primary = v1102 outstanding_cells (15 指標 × Top 10% + IQR で per cell outstanding_score)、B = ESDE 自身の emit (v10.5 salience candidate_mass / v1101a attention_emit change_metric_value / change_rank_within_type / qc_ratio)。

### 5.2 B 指標と A primary outstanding_score の相関

| 対応 | Pearson r | p-value | 構造的事実 |
|---|---:|---:|---|
| cmv_mean × A_score | 0.099 | 0.38 | 統計的に有意でない |
| sal_mass × A_score | 0.120 | 0.29 | 同 |

### 5.3 A 際立ち vs B 際立ち 重なり (post-process 仮想評価)

| 指標 | 値 |
|---|---:|
| A 際立ち cells (outstanding_score≥3) | 23 |
| B 際立ち cells (B_score≥1、緩) | 69 |
| B 際立ち cells (B_score≥2、強) | 14 |
| **Jaccard (A, B≥1)** | **0.227** |
| **Recall (B≥1 covers A)** | **0.739** |
| **Precision (B≥1 is A)** | 0.246 |

### 5.4 B≥2 際立ち cell の receiver_bin 分布

- beta_n=3/low (2), beta_n=4+/high (2), alpha 各 n_bin × 1, ESDE 3 scope 各 1
- 計 14 cells

### 5.5 構造的事実 (Code A judgment 回避、selector 化禁止遵守)

- B 指標と A_score は **ほぼ無相関** (r<0.12、有意でない)
- B≥1 (緩い基準) は **A 際立ちの 74% をカバー** (subset 関係)
- ただし B≥1 cells の **25% のみが A 際立ち** (B 独自の際立ち多数)
- 設計書 §2.4.6 出口: 完全な (a) でも (b) でもなく **部分的**

### 5.6 規律遵守 (selector 化禁止、GPT 修正必須 C)

- ✓ post-process 仮想評価のみ
- ✓ ESDE 内部 (attention_emit / salience / cid_state_ledger) 書き戻し なし
- ✓ 書込み unified/v1104/outputs/main/ 配下のみ
- ✓ 新規 emit 機構追加 なし

### 5.7 新規留保候補 #L23

B (ESDE 自身の重要性 emit) と A (研究者の構造的指標) は subset 関係 — B は A の超集合を含むが (Recall 0.74) B 独自の際立ちも多数 (Precision 0.25)。両者は別の対象を際立たせる側面あり。

---

## 6. bit-identity 3 層検証 (Step G)

| 層 | 内容 | 結果 |
|---|---|---|
| A | Step B+C+D+E re-run hash 一致 (B 19s + C 56s + D 7s + E 1s = 84s) | True (all_match) |
| B | v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 = **1,489 files frozen** | 0/0/0 全 frozen |
| C | scripts 5 write calls すべて unified/v1104/ 配下 | True |

→ all_layers_pass = True

---

## 7. 規律遵守総括 (絶対格言 15 件 + GPT 5 点 + Gemini 1 点 + 固有規律)

| # | 規律 | 遵守 |
|---|---|---|
| 2 | 物理層 frozen | ✓ Step G 層 B で 1,489 files 完全保証 |
| 4 | 集団平均の罠 / 層化必須 | ✓ 観察 1 で n_members × qc_gini 層化、観察 3/4 で qc_regime × sim_basis 層化 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ 既存出力流用のみ (Step A §5.1/5.2 確定通り) |
| 6 | 出口の固定 | ✓ §2.x-5.x で各観察の構造事実を §0 駆動要因と接続 |
| 9 | 神の手回避 | ✓ 観察 1 の k=1/3/5 別指標 / 観察 2 の shuffle baseline / 観察 4 の Top 10% 構造的閾値、すべて構造的 |
| 12 | Aruism 判定回避 | ✓ Code A judgment 回避、§2-5 出口 (a)/(b) の判定なし |
| GPT-A | IID 既存構造の参照 | ✓ 新規データ構造作らず、既存 (α/β/member_cids/predecessor_attention_ref/cid_state_ledger) のみ参照 |
| GPT-B | Jaccard 厳密化 | ✓ match_rate_k1 / jaccard_top3 / jaccard_top5 別指標 |
| GPT-C | selector 化禁止 | ✓ 観察 4 で post-process 仮想評価のみ、ESDE 内部書き戻し なし |
| GPT 追加 4 | 判定語制限 | ✓ 観察 2 で「連想」と判定せず構造事実のみ記録 |
| GPT 追加 5 | 重複回避 | ✓ 観察 3 で既知再観察せず trajectory↔response 対応に絞る |
| Gemini | 時間軸同期検証 | ✓ Step A §1.1 で alpha_lifecycle_log 経由 per-window 復元方針確定 |
| 固有 | Genesis 側単独 | ✓ Language 側噛み合わせは扱わず |
| 固有 | 段 4-d 扱わない | ✓ 確率分布表現は v1103 既知、本主題は段 4-b/4-c の前段に集中 |

---

## 8. 新規留保候補 4 件 (Code A 報告、Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L20** | CID-Integration 像不一致と n_members の系統的関係 — match_rate_k1 が n=1 (0.884) → n=4+ (0.569) で Δ-0.315 単調低下、留保 #L14 と整合的だが本主題で初めて Jaccard 厳密化で定量化 |
| **#L21** | predecessor 連鎖は cid_atom_sim_matrix 類似度地形と shuffle baseline で区別不能 (lift=0、85% self-loop)、ランダム walk と等価な可能性 |
| **#L22** | trajectory stability と response 収束の弱い対応 (r=0.157、有意)、ただし 48 次元密度との直接比較は本主題で未実施 |
| **#L23** | B (ESDE 自身の重要性 emit) と A (研究者の構造的指標) は subset 関係 (Recall 0.74、Precision 0.25)、B は A の超集合を含むが独自シグナルも持つ |

---

## 9. 設計書 §4.2 想定 4 通り組み合わせとの対応 (構造事実、判定は Taka 領域)

各観察の出口 (a)/(b) を Code A は判定しないが、構造事実の方向を整理:

| 観察 | 構造事実の方向 | (a) / (b) 候補 |
|---|---|---|
| 観察 1 (像差分) | n_members 増で match_k1 単調低下 = 「ESDE 内部の構造的特徴」と整合 | (a) 候補強め |
| 観察 2 (predecessor 連鎖) | lift=0 で shuffle と区別不能、self-loop 85% | (b) 候補強め |
| 観察 3 (trajectory↔response) | 弱い対応 (r=0.157) | (a)/(b) 中間、判定不能 |
| 観察 4 (B 現状) | B は A subset を含むが独自 | (a)/(b) 中間、subset 関係 |

→ 設計書 §4.2 「1+3 (a) / 2 (b) / 4 不明」または「全 (b)」に近い組み合わせと推測されるが、**最終判定は Web Claude Phase Result + Taka 主題評価領域**。

---

## 10. 出力ファイル総覧 (`unified/v1104/`)

| ファイル | サイズ |
|---|---:|
| v1104_phase_design.md | (markdown) |
| v1104_step_a_recognition.md | (markdown) |
| v1104_step_h_observation_final.md (本書) | (markdown) |
| v1104_step_b_observation_1.py | (python) |
| v1104_step_c_observation_2.py | (python) |
| v1104_step_d_observation_3.py | (python) |
| v1104_step_e_observation_4.py | (python) |
| v1104_step_f_graph.py | (python) |
| v1104_step_g_bit_identity.py | (python) |
| outputs/main/observation_1_cid_integration.parquet | 404,039 rows |
| outputs/main/observation_2_predecessor_chain.parquet | 39,537 chains |
| outputs/main/observation_3_trajectory_response.parquet | 972 rows |
| outputs/main/observation_4_b_overlap.parquet | 81 cells |
| outputs/v1104_observation.html | 13 KB |
| v1104_step_g_bit_identity_report.json | all_layers_pass=True |

---

## 11. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A は本書で観察事実を記録、judgment 回避 + 判定語制限遵守。**解釈統合は Web Claude Phase Result 領域**:

- 観察 1 match_k1 単調低下の主題的意味
- 観察 2 lift=0 を「predecessor 連鎖は『連想を辿る』と呼べる構造を持たない」と読むか別の意味で読むか
- 観察 3 trajectory↔response の弱い対応 (r=0.157) を 48 次元密度と並ぶ構造的指標候補とするか別の役割とするか
- 観察 4 B subset 関係の意味、B primary 化試行の妥当性 (selector 化への昇格判断は本主題範囲外)
- 設計書 §4.2 16 通りの組み合わせから現状の組み合わせ位置づけ
- 次主題候補 (段 4-b Language 噛み合わせ / 段 4-c B primary 化 / 段 4-b 別機構 / パイプライン再設計 + Taka 直感メモ方向)

v1104 主題担当範囲 (Code A): 段階 1 Step A-H 全完了、設計書 §4 出口要件すべて満たす。Language 側噛み合わせ / 段 5b LLM 外注 / 会話 ESDE の完成は v1104 範囲外 (§1.2 明示)。

---

## 12. 一文サマリ (再掲)

v1104 主題段階 1 Step A-H 全完了、観察 1 (CID-Integration 像差分、404,039 records、n_members 増で match_k1 が 0.884 → 0.569 単調低下) ・観察 2 (predecessor 連鎖、39,537 chains、85% self-loop、lift=0 で shuffle と区別不能) ・観察 3 (trajectory↔response 対応、972 rows、stability×max_prob r=0.157 弱い正相関 / diffusion×entropy r=0.020 無相関) ・観察 4 (B 現状確認、81 cells、A∩B Jaccard 0.227 / Recall 0.74 / Precision 0.25、B は A subset 関係) のすべてで構造事実を記録、新規留保 #L20-#L23 candidate 4 件、Step G bit-identity 3 層全 PASS (1,489 files frozen)、規律 (絶対格言 + GPT 5 点 + Gemini 1 点 + Genesis 側単独 + 段 4-d 扱わない + 判定語制限 + selector 化禁止) を全 Step で堅持、設計書 §4.2 出口 16 通りの組み合わせから現状の位置づけ + 次主題候補選定は Web Claude Phase Result + Taka 主題評価領域、新規 main run なし + 既存出力流用のみ + 書込み unified/v1104/ 配下のみ + 物理層 frozen 絶対遵守、Code A 主題担当範囲は本書で完了。

---

*以上、v11.0.4 (v1104) Step H 観察事実最終報告 (Code A、2026-05-23)。judgment 回避 + 判定語制限遵守 + selector 化禁止遵守。Web Claude Phase Result + Taka 主題評価判断を待つ。*
