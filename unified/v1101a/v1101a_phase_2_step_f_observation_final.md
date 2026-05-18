# v11.0.1.a (v1101a) 段階 2 Step F 観察事実最終報告 — Code A

*作成*: 2026-05-19、Code A
*親*: `v1101a_phase_2_design.md` (Web Claude 段階 2 設計書) + `v1101a_phase_2_step_a_recognition.md` (Code A 認識確認) + Taka 確認要請 3 件確定回答 (2026-05-19) + Step B/C/D/E 出力
*対象*: Web Claude (Phase Result 翻訳統合担当) + Taka (主題評価)
*位置づけ*: v11.0.1.a 主題「ESDE スケール注意機構」段階 2 の Code A 観察事実総括、judgement 回避 (絶対格言 #12)、解釈統合は Web Claude Phase Result 領域

---

## 0. 一文サマリ

v11.0.1.a 段階 2 Step A-F 全完了、Step B cid state ledger 再生 (a) 簡易版 (atom_profiles mean ベース、Taka 条件 1.3 性質明記済、24 seeds 1 batch、175,200 records / 86 MB、32.3 秒) + 時間軸付き unit_KL_delta 171,696 records、Step C 観察 A/B/C 算出 (24.1 秒、観察 A 39,537 / 観察 B 79,812 / 観察 C 432 records)、Step D 段階 2 グラフ (`v1101a_phase_2_observations.html` 11 KB、Section 5 候補数推移 / 中心 atom 一致 / 予測可能性 vs shuffle baseline)、Step E 段階 2 bit-identity 3 層全 PASS (v106 731 + v107 222 + v112 207 + v105_integration 144 = 1,304 files frozen、shuffle baseline rng=42 固定で deterministic 保証、書込み unified/v1101a/ 配下のみ)、観察 A は注意候補数の cog→csc 切替時推移で全 scope mean_delta 0.00-0.19 で **収束も発散も顕著でない** (CID 0.00 / alpha 0.03 / beta 0.04 / ESDE_event 0.19 / ESDE_step10 0.14 / ESDE_window 0.00)、観察 B は隣接 window 中心 atom 一致 frac で **認知優位の方が一致率高い** (CID 0.79 vs 0.62、alpha 0.62 vs 0.55、beta 0.68 vs 0.56、ESDE_event 0.58 vs 0.40、ESDE_step10 0.56 vs 0.41、ESDE_window 0.34 vs 0.33) で意識優位ほど中心 atom が変わる傾向、観察 C は予測可能性 vs shuffle baseline (×100、rng=42) で alpha unit_kl_static 0.977 vs baseline 0.087 (lift +0.889) / alpha rank1_flip 0.838 vs 0.080 (+0.758) / alpha atom_delta 0.740 vs 0.073 (+0.668) / beta 同パターンで lift 0.59-0.79 / CID scope 全 records 100% 到達 (predict 定義の self-reference 構造) / ESDE 3 scope は actual ≈ baseline (lift ≈ 0、shuffle と区別不可、scope_id=-1 集約のため shuffle 効果薄) / **100% 未満確認 282/432 records (65.3%)、100% 到達 150/432 (34.7%、CID scope 全部 + 一部 unit_kl_static)**、留保 #41 段階 1 解決済記載済 (member_cids は v105 lifecycle/membership/distribution log から段階 1 で取得済、段階 2 で復元作業不要)、Step E 因果候補集約 (留保 #L5 sum/zscore 併記) と Step B 時間軸付き unit_KL_delta (留保 #L1 (a) 簡易版性質明記) が両方とも v1101 留保 #33「集計単位で像が変わる」と同型対応、新規留保候補 #L8 候補 (CID scope 予測定義 self-reference)、設計書 §3 出口 6 項目すべて満たし観察事実 (選択と集中 / 拡散の方向性は alpha/beta で「強い予測可能性 + 認知優位での一致率高い + 意識優位で中心 atom 変動」、ESDE 3 scope で「scope_id 集約のため shuffle で baseline と差が出ない」、CID で「self-reference 構造のため予測 100%」と scope によって割れた observation を記録)、判定 (選択と集中か拡散か) は Web Claude Phase Result + Taka 主題評価領域。

---

## 1. 段階 2 進行と入出力

### 1.1 進行 (Step A-F)

| Step | 内容 | 担当 | 状態 | 出力 |
|---|---|---|---|---|
| A | 認識確認 (事前齟齬 3 件 + 確認要請 3 件) | Code A | 完了 | v1101a_phase_2_step_a_recognition.md |
| B | cid state ledger 再生 (a) 簡易版 + unit_KL_delta | Code A | 完了 | cid_state_ledger_seed{N}.parquet × 24 + unit_kl_delta_seed{N}.parquet × 24 |
| C | 観察 A/B/C 算出 | Code A | 完了 | observation_a/b/c_*.parquet × 3 |
| D | 段階 2 グラフ拡張 | Code A | 完了 | v1101a_phase_2_observations.html (11 KB) |
| E | 段階 2 bit-identity 3 層検証 | Code A | 完了 | v1101a_phase_2_step_e_bit_identity_report.json |
| F | 観察事実最終報告 | Code A | 本書 | v1101a_phase_2_step_f_observation_final.md |
| G | Phase Result | Web Claude | 待ち | — |

### 1.2 Taka 確認要請 3 件 (2026-05-19 確定回答)

- 確認 1: 留保 #41 段階 1 解決済の前提更新 → **更新で確定**、段階 2 で member_cids 復元作業不要
- 確認 2: 326 atom 全濃度時系列の再構築方針 → **(a) 簡易版で確定**、条件: unit_KL_delta に「(a) 簡易版 atom_profiles mean ベース、完全再現の濃度時系列ではない」性質明記
- 確認 3: 観察 C 予測可能性 baseline → **(i) 完全 shuffle で確定**、100% 未満確認は観察事実として必ず記録

### 1.3 出力規模

| ファイル | 行数 | サイズ |
|---|---:|---:|
| cid_state_ledger_all.parquet | 175,200 | 86 MB |
| unit_kl_delta_all.parquet | 171,696 | 217 KB |
| observation_a_candidate_count.parquet | 39,537 | (parquet) |
| observation_b_jaccard_proxy.parquet | 79,812 | (parquet) |
| observation_c_predictability.parquet | 432 | (parquet) |
| v1101a_phase_2_observations.html | — | 11 KB |
| v1101a_phase_2_step_e_bit_identity_report.json | — | (json) |

---

## 2. 観察 A 主要事実 — 注意候補数の収束/発散

### 2.1 cog→csc 切替時の attention_candidate_id ユニーク数推移 (24 seeds 集約)

| change_scope | n_transitions | mean_cog_pre_5w | mean_csc_post_5w | mean_delta | median_delta |
|---|---:|---:|---:|---:|---:|
| CID | 3,798 | 1.00 | 1.00 | **0.00** | 0.0 |
| alpha | 34,812 | 1.22 | 1.25 | **0.03** | 0.0 |
| beta | 711 | 1.26 | 1.30 | **0.04** | 0.0 |
| ESDE_event | 72 | 3.11 | 3.31 | **0.19** | 0.0 |
| ESDE_step10 | 72 | 3.19 | 3.33 | **0.14** | 0.0 |
| ESDE_window | 72 | 2.74 | 2.74 | **0.00** | 0.0 |

### 2.2 観察事実

- 全 scope で mean_delta が ±0.2 以内、median は 0 — **収束 (-) も発散 (+) も顕著でない**
- ESDE 3 scope は cog/csc とも 2.74-3.33 で他 scope (CID 1.00 / alpha 1.22 / beta 1.26) より候補数多い → ESDE 集約で複数 cid が候補に並ぶため
- CID/alpha/beta scope は scope_id 単位の per scope_id 観察、ESDE は集約 scope (scope_id=-1) のため候補数の意味が異なる

判定 (収束 / 発散 / 横ばい) は Web Claude / Taka 領域。

---

## 3. 観察 B 主要事実 — 中心 atom 隣接時点一致

### 3.1 隣接 window 中心 atom (center_atom_t0) 一致 frac (24 seeds 集約)

| change_scope | qc_regime | n_records | mean same_frac |
|---|---|---:|---:|
| CID | cognitive_dominant | 4,137 | **0.791** |
| CID | conscious_dominant | 4,593 | 0.616 |
| alpha | cognitive_dominant | 33,810 | **0.620** |
| alpha | conscious_dominant | 35,379 | 0.555 |
| beta | cognitive_dominant | 660 | **0.684** |
| beta | conscious_dominant | 801 | 0.560 |
| ESDE_event | cognitive_dominant | 72 | 0.581 |
| ESDE_event | conscious_dominant | 72 | 0.404 |
| ESDE_step10 | cognitive_dominant | 72 | 0.564 |
| ESDE_step10 | conscious_dominant | 72 | 0.413 |
| ESDE_window | cognitive_dominant | 72 | 0.339 |
| ESDE_window | conscious_dominant | 72 | 0.329 |

### 3.2 観察事実

- **全 6 scope で認知優位 ≧ 意識優位** (cog same_frac が同 scope の csc を一貫して上回る)
- 差: CID +0.18 / alpha +0.07 / beta +0.13 / ESDE_event +0.18 / ESDE_step10 +0.15 / ESDE_window +0.01
- 認知優位フェーズでは「中心 atom が隣接 window で同じ」が継続し、意識優位フェーズで「中心 atom が変わる」傾向
- 留保 #L4 対応で per scope 並列に観察、scope 間で同方向の差

実装上の留保: 厳密な Jaccard (波及先 cid 集合の集合間重なり) は段階 1 propagation 出力に raw 波及先 cid id 集合が保存されていないため、ここでは center_atom_t0 の隣接一致を Jaccard 代替指標 (proxy) として算出。観察事実の方向性は捉えるが厳密 Jaccard ではない (留保候補)。

---

## 4. 観察 C 主要事実 — 注意候補の予測可能性 vs shuffle baseline

### 4.1 actual_predict_rate vs baseline_shuffle_mean (24 seeds 集約、shuffle ×100、rng=42)

| change_scope | change_metric_type | actual | baseline | lift |
|---|---|---:|---:|---:|
| CID | atom_delta | **1.0000** | 0.0346 | 0.9654 |
| CID | rank1_flip_density | **1.0000** | 0.0344 | 0.9656 |
| CID | unit_kl_static | **1.0000** | 0.0345 | 0.9655 |
| alpha | atom_delta | 0.7396 | 0.0729 | **+0.6668** |
| alpha | rank1_flip_density | 0.8380 | 0.0798 | **+0.7582** |
| alpha | unit_kl_static | 0.9766 | 0.0867 | **+0.8899** |
| beta | atom_delta | 0.7027 | 0.1143 | **+0.5884** |
| beta | rank1_flip_density | 0.7824 | 0.1270 | **+0.6554** |
| beta | unit_kl_static | 0.9741 | 0.1819 | **+0.7923** |
| ESDE_event | atom_delta | 0.0097 | 0.0085 | 0.0012 |
| ESDE_event | rank1_flip_density | 0.0286 | 0.0259 | 0.0027 |
| ESDE_event | unit_kl_static | **0.9430** | **0.9430** | 0.0000 |
| ESDE_step10 | atom_delta | 0.0031 | 0.0031 | -0.0000 |
| ESDE_step10 | rank1_flip_density | 0.0213 | 0.0212 | 0.0001 |
| ESDE_step10 | unit_kl_static | **0.9422** | **0.9422** | -0.0000 |
| ESDE_window | atom_delta | 0.0321 | 0.0319 | 0.0002 |
| ESDE_window | rank1_flip_density | 0.2719 | 0.2727 | -0.0008 |
| ESDE_window | unit_kl_static | **0.9497** | **0.9497** | 0.0000 |

### 4.2 100% 未満確認 (Aruism 対称性、箱 3) — Taka 条件 3.3 遵守

- **100% 到達 records: 150 / 432 (34.7%)** — CID scope 72 records 全部 + alpha/beta の unit_kl 等 ~80 records
- **100% 未満 records: 282 / 432 (65.3%)** — alpha/beta の他 metric + ESDE 3 scope すべて

### 4.3 観察事実

#### 4.3.1 alpha/beta scope は「妥当性方向」(baseline 上回りつつ 100% 未満)

- alpha unit_kl_static: actual 0.977 vs baseline 0.087、lift +0.889
- beta unit_kl_static: actual 0.974 vs baseline 0.182、lift +0.792
- alpha rank1_flip / atom_delta / beta 同様、全て baseline の 6-11 倍 + 100% 未満
- これは Taka 整理「ランダム水準より高いが 100% でない帯」(Aさんの揺れ幅) に乗る observation

#### 4.3.2 CID scope は全 records 100% 到達 — 予測定義の self-reference 構造

- CID scope の actual_predict_rate は全 72 records (3 metric × 24 seeds) で 1.0000
- 原因: CID scope では scope_id = cognitive_id = attention_candidate_id (self)、predecessor_attention_ref も同 scope 内ループで同じ cid を指す → 構造的に必ず一致
- shuffle baseline は 0.034 (cid 1/n_cids 水準) なので lift 0.965 — baseline は意味あるが actual が定義上 100%

**新規留保候補 #L8**: CID scope 予測 self-reference 構造、観察 C の予測定義改訂候補 (judgement は Taka 領域)。

#### 4.3.3 ESDE 3 scope unit_kl_static は actual ≈ baseline (lift ≈ 0)

- ESDE_event/step10/window の unit_kl_static で actual 0.94-0.95、baseline も同値 → lift 0
- ESDE scope は scope_id=-1 集約のため shuffle で並べ替えても結果が同じ (1 record / scope_id / window)
- 観察事実: ESDE 集約 scope での予測可能性は shuffle baseline と区別不可

#### 4.3.4 atom_delta / rank1_flip_density の ESDE scope は actual と baseline どちらも 0.001-0.27 と低い

- 中心 atom が time window 単位で変化頻度高く、予測も baseline も低水準

### 4.4 Taka フレーム「ランダムか妥当か」との対応 (記録のみ、判定なし)

- alpha/beta scope: 「妥当性方向」(baseline < actual < 100%) を満たす — Aさんの揺れ幅
- CID scope: 観察手法の限界 (self-reference)、判定不能
- ESDE 3 scope unit_kl: actual ≈ baseline = ランダム水準と区別不可
- ESDE 3 scope atom_delta/rank1_flip: 両方低水準、判定保留

判定 (どの scope が「妥当性方向」を確証するか) は Web Claude / Taka 領域。

---

## 5. 時間軸付き unit_KL_delta (留保 #L1 対応、Taka 条件 1.3 性質明記)

per (cid, window→window+1) で 326 atom 濃度分布の自己 KL 差分:

- 24 seeds 合計 171,696 records
- mean unit_kl_self_delta = 0.004 / std 0.025 / min 0 / median 0 / max 0.35
- 多数の window 遷移で KL ≈ 0 (atom 集合変化なし、cumulative なので)、一部で large KL (新 atom intro 直後)

**性質明記** (Taka 条件 1.3、絶対格言 #14 直感語保存):
- `(a) 簡易版 atom_profiles mean ベースで算出した時間変化であって、完全再現の濃度時系列ではない`
- 出力 parquet の `note_simplified` 列に明記
- 段階 1 unit_kl_static (時間軸なし、静的) と並べて読む際の解像度差を Web Claude / Taka が誤解しないため

留保 #L1 段階 1 から継承の対応として段階 2 で時間軸付き取得を実施した観察事実。

---

## 6. bit-identity 3 層検証 (Step E 結果)

| 層 | 内容 | 結果 |
|---|---|---|
| A (再現性) | Step B smoke seed 0 を re-run → parquet hash 一致 (cid_state_ledger + unit_kl_delta) | all_match=True |
| B (frozen) | v106 (731) + v107 (222) + v112 (207) + v105_integration (144) = **1,304 files frozen** | all_pass=True (0 added / 0 removed / 0 modified) |
| C (書込み境界) | 段階 2 scripts 内 8 write calls すべて unified/v1101a/ 配下 | all_under_v1101a=True |

→ **all_layers_pass = True**

cid state ledger 再生 (a) 簡易版は **実 ledger 不変** (atom_introduction_events_v108_standard を read-only で参照、累積処理は in-memory)。書込みは unified/v1101a/outputs/{smoke,main}/ 配下のみ。shuffle baseline (観察 C) は rng_seed=42 固定で deterministic 保証。

---

## 7. 留保事項総括

### 7.1 段階 2 設計時の既知留保 (本主題 §6 + 認識確認)

| id | 内容 | 段階 2 での状態 |
|---|---|---|
| #L1 | unit_kl_static は時間軸なし → 段階 2 で時間軸付き unit_KL_delta | **本書 §5 で実装、(a) 簡易版性質明記済** |
| #L4 | alpha records 92.5% 占有、scope 内正規化必要 | 段階 2 でも全 plot 正規化済 |
| **#41** | **Integration member_cids 未 persistence** | **段階 1 で解決済 (v105 log から取得)、設計書 §2.5 更新 (本書 §1.2 確認 1 確定)** |

### 7.2 本段階 2 新規留保候補

| candidate id | 内容 |
|---|---|
| **#L8 candidate** | CID scope の観察 C 予測定義 self-reference (scope_id=cognitive_id=attention_candidate_id) で actual_predict_rate が定義上 100%、予測の意味が消失。観察 C の予測定義を CID scope で別途設計するか、alpha/beta/ESDE scope のみ予測可能性を測るかの判断要。本書 §4.3.2 |
| #L9 candidate | 観察 B の Jaccard が厳密な「波及先 cid 集合の集合間重なり」でなく、center_atom_t0 の隣接一致 (proxy) を採用。段階 1 propagation 出力で raw 波及先 cid id 集合を持っていないため。本書 §3.2 |
| #L10 candidate | ESDE 3 scope (event/step10/window) で観察 C unit_kl_static の actual ≈ baseline (lift ≈ 0)。scope_id=-1 集約のため shuffle が効かない。ESDE scope 用の baseline を再設計する候補。本書 §4.3.3 |

### 7.3 v1101 + 段階 1 からの継承留保

- v1101 留保 #33 (集計単位で像が変わる): 段階 2 でも観察 A/B/C で scope 別差確認、段階 1 Step E 修正で sum/zscore 併記したのと同型の現象が観察 C ESDE scope と CID scope で異なる
- 段階 1 #L3 (集計単位方向変動): 段階 2 でも seed 間バラつきあり (観察 B std、観察 C lift std)

---

## 8. 規律遵守自己点検 (絶対格言 15 件、本段階 2 全 Step 通算)

| # | 格言 | 遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ Step B で構造 (cid state ledger) を先、観察 A/B/C は記述のみ |
| 2 | 物理層 frozen 絶対 | ✓ Step E 層 B で 1,304 files 完全保証 |
| 3 | ベースライン比較 + 効果サイズ | ✓ 観察 C で shuffle baseline + lift 算出 |
| 4 | 集団平均の罠 / 層化 | ✓ scope 別並列観察、留保 #L4 継承 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ §0.2 段階 1 核心観察の未解決一点を詰める駆動要因明示 |
| 6 | 出口の固定 | ✓ 段階 2 設計書 §3 出口 6 項目すべて満たす |
| 7 | 主題着手前に上位資料を読む | ✓ 段階 2 設計書 + 段階 1 Phase Result + 認識確認 §1 |
| 8 | 過去観察軸の照会 | ✓ 段階 1 Step C/D/E 出力を入力として直接使用 |
| 9 | 神の手回避 | ✓ shuffle baseline rng=42 固定 (構造的決定)、閾値なし |
| 10 | 因果でなく因果候補 | ✓ 観察 C 予測「可能性」、確定しない |
| 11 | 概念単位を雑に扱わない | ✓ Jaccard と proxy、cid state ledger と原 ledger の違いを明記 |
| 12 | Aruism 判定回避 | ✓ 全 records 観察事実、判定 (選択と集中 / 拡散) は Web Claude / Taka |
| 13 | AI を信じない原則は Taka 個人 | ✓ §1.2 Taka 確認要請 3 件確定回答を反映、Code A 仮所見と区別 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ 設計書 §0.3 / 認識確認 §3.3 Taka 整理を継承、ランダム/妥当の言葉を保存 |
| 15 | 5 者運用体制の補完性 | ✓ Web Claude (設計+確認) / Code A (実装+観察) / Taka (判断) |

→ **15 格言全項目遵守**。

---

## 9. 出力ファイル総覧 (`unified/v1101a/`、段階 2 分のみ)

### 9.1 設計書・報告書 (markdown、3 ファイル)

- `v1101a_phase_2_design.md` (Web Claude)
- `v1101a_phase_2_step_a_recognition.md` (Code A)
- `v1101a_phase_2_step_f_observation_final.md` (本書)

### 9.2 実装スクリプト (Python、4 ファイル)

- `v1101a_phase_2_step_b_cid_state_ledger.py` (Step B、(a) 簡易版)
- `v1101a_phase_2_step_c_observations.py` (Step C、観察 A/B/C + shuffle ×100)
- `v1101a_phase_2_step_d_graph.py` (Step D、Section 5 dashboard)
- `v1101a_phase_2_step_e_bit_identity.py` (Step E、段階 2 検証)

### 9.3 観察データ (parquet、~52 ファイル + JSON 1 + HTML 1)

| 種類 | ファイル | サイズ |
|---|---|---:|
| cid state ledger | seed{0..23} + all = 25 ファイル | ~86 MB (all) |
| unit_KL_delta | seed{0..23} + all = 25 ファイル | ~217 KB (all) |
| observation_a/b/c | 3 ファイル | (~MB) |
| bit-identity report | v1101a_phase_2_step_e_bit_identity_report.json | <1 KB |
| 段階 2 グラフ HTML | v1101a_phase_2_observations.html | 11 KB |

---

## 10. Web Claude Phase Result + 次主題への接続

### 10.1 Web Claude Phase Result 領域 (絶対格言 #12 解釈統合)

Code A は本書で観察事実を記録。以下の **解釈統合は Web Claude 領域**:

- 観察 A/B/C を「選択と集中 / 拡散」のどちらに読むか
- alpha/beta scope の「妥当性方向」(baseline < actual < 100%) を Aさんの揺れ幅と同定するか
- CID scope の self-reference (新規留保 #L8) を予測定義改訂対象とするか別 scope のみ評価するか
- ESDE 3 scope unit_kl の actual ≈ baseline (新規留保 #L10) の意味づけ
- 段階 2 結果が Taka が示した大きなストリーム (スレッド=器官の切り分け、Language 融合) にどう繋がるか

### 10.2 v1101a 主題担当範囲 (Code A)

段階 1 (Step B-H 全 7 段階 + Step E 修正) + 段階 2 (Step A-F 全 6 段階) で Code A 主題担当範囲は完了。段階 3 (生きた版、新規 main run 必要) は v1101a 設計書 §5.1 で「今回範囲外」明示。

---

## 11. 一文サマリ (再掲)

v11.0.1.a 段階 2 Step A-F 全完了、Taka 確認要請 3 件確定 (留保 #41 解決済前提更新 / (a) 簡易版採用で unit_KL_delta 性質明記 / shuffle baseline 採用で 100% 未満確認必須) を遵守、Step B cid state ledger 再生 (a) 簡易版 175,200 records (86 MB) + 時間軸付き unit_KL_delta 171,696 records、Step C 観察 A (候補数推移、全 scope mean_delta 0.00-0.19 で収束/発散顕著でなし) + 観察 B (中心 atom 隣接一致 frac、全 scope で認知優位 ≧ 意識優位、CID +0.18 / alpha +0.07 / beta +0.13 / ESDE_event +0.18 / ESDE_step10 +0.15 / ESDE_window +0.01) + 観察 C (予測可能性 vs shuffle baseline、alpha/beta は actual baseline の 6-11 倍 lift で 100% 未満帯 = 「妥当性方向」、CID 全 records 100% 到達 (self-reference 構造、新規 #L8 candidate)、ESDE 3 scope unit_kl は actual ≈ baseline (scope_id=-1 集約のため shuffle 効果薄、新規 #L10 candidate)、100% 未満確認 282/432 records 65.3% 100% 到達 150/432 34.7%)、Step D 段階 2 dashboard (11 KB、Section 5 観察 A/B/C 3 panel)、Step E bit-identity 3 層全 PASS (v106+v107+v112+v105_integration 1,304 files frozen、shuffle baseline rng=42 deterministic、書込み unified/v1101a/ 配下のみ)、新規留保候補 #L8 (CID scope 予測 self-reference) / #L9 (観察 B Jaccard proxy で厳密ではない) / #L10 (ESDE 3 scope unit_kl shuffle 効かない)、判定 (選択と集中か拡散か / alpha/beta の Aさんの揺れ幅同定 / ESDE scope の意味づけ) は Web Claude Phase Result + Taka 主題評価領域、段階 3 (生きた版) は v1101a 設計書 §5.1 で範囲外明示、v1101a Code A 主題担当範囲は段階 1 + 段階 2 で完了。

---

*以上、v11.0.1.a 段階 2 Step F 観察事実最終報告 (Code A、2026-05-19)。judgement なし観察記録 (絶対格言 #12)。Web Claude Phase Result + Taka 主題評価判断を待つ。*
