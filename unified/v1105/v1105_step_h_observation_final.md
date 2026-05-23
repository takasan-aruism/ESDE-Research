# v11.0.5 (v1105) Step H 観察事実最終報告 — Code A

*作成*: 2026-05-24、Code A
*親*: `v1105_phase_design.md` v4 (Web Claude 設計書、2 AI 監査 + Code A 確認要請 7 クリア済) + `v1105_step_a_recognition.md` + `v1105_step_a_answer.md` + Step C-G 出力
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価)
*位置づけ*: v1105 主題「CID/IID 内部動作点検 + 段 4-b と段 4-c を対称的に統合点検、役割表まで進める」(問いの形 A、段階 1) の Code A 観察事実総括。**judgment 回避** (絶対格言 #12)、**判定語制限** (「連想」「成功/失敗」「意味がある/ない」を使わない、GPT 追加 4)、**selector 化禁止遵守** (観察 4、GPT 修正必須 D + 追加推奨 6)、**0 を 1 にはできない歯止め遵守** (§3.3、GPT 追加推奨 7)、**binary 判定/単一スコア化禁止** (観察 3、§2.4)、**統合方向遵守** (§0.3)。

---

## 0. 一文サマリ

v1105 主題段階 1 Step A-G 全完了、Step A 認識確認 (実環境照合 6 項目: proposals.json B_COUPLE 6 件 / Couple endpoint 12 atoms / response_atom_distribution `is_couple_link` 列実は全 False = pair-based 厳判定で該当 0、設計書 §2.2 解釈 A を採用 (candidate.isin(endpoints) 方式、237/5670=4.18%) / density_summary 6 値構造 / observation_4_b_minus_a_cells 流用可) + 確認要請 7 Taka 承認案 B (6 値別レイヤー保持) → Step C (観察 1 段 4-b 地形: Genesis lift_C + Language couple_hit_rate 2 種、scope 別逆方向強度 = alpha Genesis 強/Language 弱 vs beta 逆、CID_n=2 で couple_hit_rate 15.7%/22.1% 断トツ、ESDE_window 粒度感度 1.4%) → Step D (観察 2 段 4-c 地形: trajectory r 2 種 + density r 6 種、coverage 100%、CID_n=2 で density 6 種 +0.65-0.99 超強、CID_n=5/n=6+ で density 6 種全 sign_flip +0.39→-0.39、ESDE_window でも sign_flip、ESDE event/step10 で trajectory +0.64 / -0.62 強相関 = #L31 再現、#L17 raw vs norm 反転を qweighted/const_adjusted でも確認) → Step E (観察 3 強度マップ: 12 strata × 11 数値別レイヤー parquet + 4 panel heatmap 14.9 KB、binary 判定なし、単一スコア化なし、絶対格言 #11 厳密適用、4 つの非対称性 #L30-L33 が強度マップにそのまま現れる構造を確定) → Step F (観察 4 役割表: 5 役割を「仮割り当て + 観察支持 + 留保」3 列形式で記録、確定表でない、v1105a 試行設計書素材として明示、selector 化禁止維持 + B 意味判定なし、Web Claude 草案を Step C-E 構造事実で検証 + v1105 新規発見 3 件を留保拡充) → Step G (bit-identity 3 層全 PASS: LAYER_A 4 ファイル全 hash 一致 1.6s、LAYER_B 1,490 frozen files 不変 v1104a まで含む、LAYER_C 6 件全て unified/v1105/ 配下) すべて完了、核心観察事実 (judgment なし) は (1) **scope 別逆方向強度の確定**: alpha Genesis lift_C 0.165 最強/Language couple_hit_rate 0.014 最弱、beta Genesis 0.116/Language 0.070 最強、scope ごとに段 4-b の主担当層が異なる、(2) **CID_n=2 の極端な特殊性**: couple_hit_rate 15.7%/22.1% (他 CID bin 1.4%/0.5% の 10-50 倍) + density 6 種 +0.65-0.99 超強 (他 CID_n=3/4 は +0.10 と均一)、(3) **粒度依存の trajectory-density 優劣**: 細粒 (ESDE_event/step10) trajectory +0.64 主役、集約粒度 (CID_all/ESDE_all/window) density 主役 (#L31 再現)、(4) **#L17 拡張**: raw vs norm 反転 = sign_flip が CID_n=5/n=6+ と ESDE_window で **density 6 種全てで発生** (qweighted/const_adjusted も raw_density 同様)、sim_basis × density 種類の 2 軸非対称性が構造として確定 (#33 系列拡張)、(5) **CID 100% self-loop の trajectory 系統消失効果 #L33** を v1105 CID 全 stratum で再現確認、新規留保候補 #L34-L36 提示: #L34 (scope 別の Genesis/Language 逆方向強度)、#L35 (CID_n=2 の特殊性 = Language Couple endpoint と density の同時超強)、#L36 (CID_n=5/n=6+/ESDE_window の全 density 6 種 sign_flip = sim_basis × density 種類の 2 軸非対称性)、48 次元人為性留保 + #L17/#L21'/#L22'/#L24-29/#L30-L33 継承、最終判定 (役割表の出口判定、設計書 §2.x.2 (a)/(b)/(c) 候補方向、v1105a 着手判断) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 #2/#5/#6/#10/#11/#12/#14 + selector 化禁止 + 判定語制限 + binary 判定/単一スコア化禁止 + 物理層 frozen + 既存出力流用のみ + 0 を 1 にはできない歯止め + 観察方法有利化と区別 + 統合方向遵守) を全 Step で堅持、書込み unified/v1105/ 配下のみ。

---

## 1. Step A-G 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A | 認識確認 + 確認要請 7 | 完了 (Web Claude/Taka 承認、案 B 採用) | v1105_step_a_recognition.md + v1105_step_a_answer.md |
| C | 観察 1 段 4-b 地形 (Genesis lift_C + Language couple_hit_rate 2 種) | 完了 (< 1s) | observation_1_terrain_4b.parquet (81 rows) |
| D | 観察 2 段 4-c 地形 (trajectory r 2 種 + density r 6 種) | 完了 (0.1s) | observation_2_terrain_4c.parquet (192 rows) |
| E | 観察 3 強度マップ (12 strata × 11 数値別レイヤー) | 完了 (< 1s) | observation_3_intensity_map.parquet + v1105_intensity_map.html (14.9 KB) |
| F | 観察 4 役割表 (5 役割 3 列形式) | 完了 (< 1s) | observation_4_role_assignment.parquet + v1105_role_assignment_table.md (6.7 KB) |
| G | bit-identity 3 層検証 | 完了 (all PASS、1.6s) | v1105_step_g_bit_identity_report.json |
| H | 観察事実最終報告 | 本書 | v1105_step_h_observation_final.md |
| I | Phase Result (v1104 + v1104a + v1105 統合) | 待ち | Web Claude 担当 |

---

## 2. 観察 1: 段 4-b 地形 (連想を辿る)

### 2.1 scope × 段 4-b 地形 集約表

| scope | Genesis lift_C (non-self / self) | Language couple_hit_rate (uw / pw) |
|---|---:|---:|
| alpha | **0.152 / 0.181** | 0.014 / 0.006 |
| beta | 0.091 / 0.149 | **0.070 / 0.092** |
| CID | — / 0.106 (100% self-loop) | 0.043 / 0.047 |
| ESDE | 0.042 / 0.204 | 0.046 / 0.053 |

### 2.2 ESDE 3 解像度別 (粒度感度)

| receiver_bin | couple_hit_rate_uw | couple_hit_rate_pw |
|---|---:|---:|
| ESDE_event | 0.062 | 0.077 |
| ESDE_step10 | 0.062 | 0.077 |
| **ESDE_window** | **0.014** | **0.003** |

→ ESDE_window で event/step10 の 1/4 以下 (粒度感度、#L26 系列の Language 側拡張)

### 2.3 CID n_size_bin 別 (特殊性)

| receiver_bin | couple_hit_rate_uw | couple_hit_rate_pw |
|---|---:|---:|
| **CID_n=2** | **0.157** | **0.221** |
| CID_n=3 | 0.014 | 0.005 |
| CID_n=4 | 0.014 | 0.005 |
| CID_n=5 | 0.014 | 0.003 |
| CID_n=6+ | 0.014 | 0.001 |

→ **CID_n=2 のみ couple_hit_rate 断トツ** (他 CID bin の 10-50 倍)、CID 内部での極端な非対称性

### 2.4 構造事実 (judgment 回避)

- alpha は predecessor (Genesis) 強、Language Couple 弱: scope ごとに段 4-b の主担当層が異なる
- beta は逆方向 (Language Couple 強、predecessor 中)
- CID_n=2 が Language Couple endpoint と強接触 (15.7%/22.1%)、他 CID bin は均一弱 (1.4%/0.5%)
- ESDE_window で Language Couple 接触が顕著に低下 (粒度感度)

注記: v1103 `is_couple_link` 列は全 5,670 行で False (start_atom × candidate_atom 両方が couple pair として登録の場合のみ True、該当 0)。設計書 §2.2「候補 atom が endpoint に接触」を解釈 A (candidate.isin(endpoints)) で採用。

---

## 3. 観察 2: 段 4-c 地形 (応答 Atom を絞る)

### 3.1 response=max_prob、12 stratum × 8 predictor (trajectory 2 + density 6) Pearson r

| stratum | traj_stab | traj_diff | raw_raw | raw_norm | qw_raw | qw_norm | ca_raw | ca_norm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ESDE_event | **+0.64** | **-0.61** | -0.28 | -0.22 | -0.27 | -0.21 | -0.28 | -0.23 |
| ESDE_step10 | **+0.64** | **-0.62** | -0.28 | -0.22 | -0.27 | -0.21 | -0.28 | -0.23 |
| **ESDE_window** | 0 | 0 | **+0.39** | **-0.39** | +0.39 | -0.39 | +0.39 | -0.38 |
| ESDE_all | 0.42 | -0.48 | -0.22 | -0.30 | -0.21 | -0.29 | -0.21 | -0.30 |
| **CID_n=2** | NaN | 0 | **+0.72** | **+0.99** | +0.65 | **+0.99** | +0.72 | **+0.98** |
| CID_n=3 | NaN | 0 | +0.10 | +0.10 | +0.10 | +0.10 | +0.10 | +0.10 |
| CID_n=4 | NaN | 0 | +0.10 | +0.10 | +0.10 | +0.10 | +0.10 | +0.10 |
| **CID_n=5** | NaN | 0 | **+0.39** | **-0.39** | +0.39 | -0.39 | +0.39 | -0.38 |
| **CID_n=6+** | NaN | 0 | **+0.62** | **-0.63** | +0.63 | -0.63 | +0.62 | -0.63 |
| CID_all | NaN | -0.31 | -0.10 | -0.43 | -0.10 | -0.43 | -0.10 | -0.43 |
| alpha_all | 0.14 | -0.11 | -0.20 | +0.17 | -0.17 | **+0.25** | -0.20 | +0.16 |
| beta_all | -0.07 | -0.27 | -0.35 | **-0.50** | -0.35 | -0.50 | -0.35 | -0.50 |

太字 = |r| ≥ 0.3 中相関以上。Coverage 100% (欠損 0)。

### 3.2 構造事実

- **CID_n=2 で density 6 種 r=+0.65-0.99 超強** (norm 系列が +0.98-0.99 で raw を上回る)、他 CID_n=3/4 は均一弱 +0.10
- **CID_n=5/n=6+ で density 6 種全て raw vs norm sign_flip** (+0.39→-0.39 と +0.62→-0.63)
- **ESDE_window でも density 6 種全て sign_flip** (CID_n=5 と同 pattern)
- **#L31 (粒度依存) 確認**: 細粒 (event/step10) で trajectory r=+0.64 主役、集約 (CID_all/ESDE_all/window) で density 主役
- **#L17 raw vs norm 反転** を v1103 raw_density で確認していたが、本観察で qweighted/const_adjusted でも全 stratum で同 pattern を確認 (sim_basis × density 種類の 2 軸非対称性)
- alpha_all qweighted_density で sign_flip (-0.17→+0.25)、beta_all は density norm で強 (-0.50)

---

## 4. 観察 3: 11 数値強度マップ

### 4.1 12 strata × 11 数値別レイヤー

(parquet `observation_3_intensity_map.parquet`、heatmap `v1105_intensity_map.html` 14.9 KB)

| stratum | lift_C | couple_uw | couple_pw | traj_stab | traj_diff | density 代表 (raw/norm) |
|---|---:|---:|---:|---:|---:|---|
| ESDE_event | 0.077 | 0.062 | 0.077 | +0.64 | -0.61 | -0.28 / -0.22 |
| ESDE_step10 | 0.069 | 0.062 | 0.077 | +0.64 | -0.62 | -0.28 / -0.22 |
| **ESDE_window** | 0.128 | 0.014 | 0.003 | 0 | 0 | **+0.39 / -0.39** sign_flip |
| ESDE_all | 0.091 | 0.046 | 0.052 | 0.42 | -0.48 | -0.22 / -0.30 |
| **CID_n=2** | 0.045 | **0.157** | **0.221** | NaN | 0 | **+0.72 / +0.99** |
| CID_n=3 | 0.099 | 0.014 | 0.005 | NaN | 0 | +0.10 / +0.10 |
| CID_n=4 | 0.138 | 0.014 | 0.005 | NaN | 0 | +0.10 / +0.10 |
| **CID_n=5** | 0.141 | 0.014 | 0.003 | NaN | 0 | **+0.39 / -0.39** sign_flip |
| **CID_n=6+** | 0.141 | 0.014 | 0.001 | NaN | 0 | **+0.62 / -0.63** sign_flip |
| CID_all | 0.104 | 0.043 | 0.047 | NaN | -0.31 | -0.10 / -0.43 |
| **alpha_all** | **0.165** | 0.014 | 0.006 | 0.14 | -0.11 | -0.20 / +0.17 (qw_norm +0.25) |
| beta_all | 0.116 | **0.070** | **0.092** | -0.07 | -0.27 | -0.35 / -0.50 |

### 4.2 構造事実 (4 非対称性 #L30-L33 + 新規 #L34-L36)

- 4 つの非対称性 (#L30-L33) が 11 数値強度マップにそのまま現れる
- 11 数値別レイヤー保持、binary 判定なし、単一スコア化なし (絶対格言 #11 厳密適用)
- 視覚化: 4 panel heatmap (lift / couple_hit_rate × 2 / trajectory × 2 / density × 6)、各 layer 別 colorscale

---

## 5. 観察 4: 役割表 (5 役割仮割り当て、3 列形式)

### 5.1 仮割り当て (詳細は `v1105_role_assignment_table.md`)

| 役割 | 仮割り当て | 主な観察支持 |
|---|---|---|
| 候補保持 | CID (全 n_size_bin) | 100% self-loop + density CID_all -0.43 norm + CID_n=2 超強 |
| 連想・踏み台 | alpha/beta non-self-loop + 別レイヤーで couple_hit_rate | Genesis lift_C alpha 0.165 / beta 0.116、Language beta 0.070 |
| 即時応答の揺れ | ESDE event/step10 | trajectory r=+0.64 (stab) / -0.62 (diff) |
| 重要性 emit | ESDE 全粒度 + scope 別 B 性質 | v1104a 観察 4: ESDE A=0/B=9、CID で B subset |
| 統合判断 | CID 集約 density (sim_basis × density 6 値) | CID_all norm -0.43、CID_n=2 全 6 種 +0.99 |

### 5.2 v1105a 進行条件 (最小役割表 3 役割成立、GPT §2.6)

| 最小役割 | 主候補 | 観察支持 |
|---|---|---|
| 候補保持 | CID | 100% self-loop + density 強 |
| 連想 | alpha/beta non-self-loop + couple_hit_rate | predecessor lift + couple_hit_rate 別レイヤー |
| 絞り | ESDE event/step10 trajectory + CID/48D density | 細粒 trajectory + 集約 density、粒度依存 |

→ 3 役割 すべて Step C-E 観察事実から分離可能、**v1105a 進行条件成立** (Code A 構造事実報告として記録、判定は Web Claude/Taka 領域)。

### 5.3 構造事実 (judgment 回避、selector 化禁止維持)

- 5 役割すべて scope × 粒度の構造事実から仮割り当て可能
- 役割表は「確定表」ではなく v1105a 試行設計書の素材として明示 (GPT 修正必須 #2)
- 「B selector」「B selector として使える可能性」表現未使用 (GPT 修正必須 D)
- B の意味判定をしない (GPT 追加推奨 6、v1105a 送り)

---

## 6. bit-identity 3 層検証 (Step G)

### 6.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step C-F 再実行で hash 完全一致 | **4 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a/v1102/v1103/v1104/v1104a main outputs 全 frozen | **all PASS** (a/r/m すべて 0、1,490 files) |
| **C** | 全 4 scripts (Step C/D/E/F) の書込みパスが unified/v1105/ 配下 | **all_under=True** (6 件) |

- LAYER_A_FILES (4): observation_1_terrain_4b / observation_2_terrain_4c / observation_3_intensity_map / observation_4_role_assignment
- LAYER_A_RERUN 経過時間: Step C 0.32s / D 0.64s / E 0.40s / F 0.26s = 計 1.62s
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 + v1104 13 + v1104a 8 = **1,490 files 全 frozen 確認**
- 報告 JSON: `v1105_step_g_bit_identity_report.json`

---

## 7. 規律遵守総括 (絶対格言 15 件 + GPT 5 点 + Gemini 1 点 + 本主題固有規律)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.5/6/7 + v1101a〜v1104a read-only、bit-identity 層 B 全 PASS) |
| 絶対格言 #3 (\|effect\| 閾値) | ✓ (\|lift\|>0.01 / \|r\|>0.1 弱・0.3 中・0.5 強の参考ガイド、binary 判定なし) |
| 絶対格言 #5 (新規 main run 禁止 / 観察軸追加禁止) | ✓ (post-process のみ、v1104+v1104a 軸継承、新規軸 0) |
| 絶対格言 #6 (出口の固定) | ✓ (役割表は「確定表」でなく仮割り当て) |
| 絶対格言 #10 (因果でなく因果候補) | ✓ (役割割り当ては #L30-L33 から構造事実翻訳、因果断定なし) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (11 数値別レイヤー、density 6 値別保持、単一スコア化なし) |
| 絶対格言 #12 (judgment 回避) | ✓ (各観察の出口判定は Phase Result 領域、Code A は構造事実のみ) |
| 絶対格言 #14 (Taka 直感優先 + 原文保存) | ✓ (Taka 整理「分散しない / 統合方向」を §0.3 引用継承) |
| GPT 修正必須 C (比較条件固定) | ✓ (Step D で同一 receiver_bin / 同一 response / 同一 scope) |
| GPT 修正必須 D (selector 表現規制) | ✓ (Step F で「B selector」「使える可能性」未使用) |
| GPT 追加推奨 6 (B 意味判定 v1105a 送り) | ✓ (Step F で B 意味判定なし、観察事実のみ) |
| GPT 追加推奨 7 (観察方法有利化と区別) | ✓ (§2 観察方法を事前確定、結果が出ない場合の観察方法変更を提案しない) |
| binary 判定/単一スコア化禁止 | ✓ (観察 3 で 11 数値別レイヤー、閾値なし、統合スコアなし) |
| selector 化禁止 (役割表は post-process) | ✓ (selector として動作させない、観察 4 で割り当て根拠は構造事実のみ) |
| 統合方向遵守 (§0.3) | ✓ (新規観察軸追加なし、v1104+v1104a の多軸を 11 数値強度マップで統合) |
| 4 つの非対称性 (#L30-#L33) 必須軸 | ✓ (Step C-F すべてで scope × 粒度 × n_size を主軸として継承、強度マップで顕在化) |
| Aruism 100% を作らない | ✓ (各構造事実に scope/粒度別の連続強度を記録、100% 一致の主張は CID 100% self-loop など構造的必然のみ) |
| Aruism #33 系列「集計単位で像が変わる」 | 整合 (#L17 拡張 + CID_n=5/6+/ESDE_window で density 6 種 sign_flip = sim_basis × density 種類の 2 軸非対称性確認) |
| 書込みパス unified/v1105/ 配下 | ✓ (層 C all_under=True、6 件) |
| smoke 含めず | ✓ (post-process のみ、main outputs のみ生成) |

---

## 8. 新規留保候補 3 件 (Code A 報告、Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L34** | scope 別の Genesis/Language 逆方向強度: alpha (Genesis predecessor 0.165 強 / Language couple_hit_rate 0.014 弱) vs beta (Genesis 0.116 中 / Language 0.070/0.092 強)。scope によって段 4-b の主担当層が逆向き、段 4-b を「Genesis のみ」または「Language のみ」で語ると scope 別の構造を見落とす |
| **#L35** | CID_n=2 の極端な特殊性: couple_hit_rate 15.7%/22.1% (他 CID bin の 10-50 倍) + density 6 種 +0.65-0.99 超強 (norm 系列 +0.98-0.99)。CID 集約だけでは捉えられない、CID 内部の n_size 別構造が段 4-b/4-c 両方に効く |
| **#L36** | CID_n=5/n=6+/ESDE_window で density 6 種全て raw vs norm sign_flip 発生 (+0.39→-0.39 / +0.62→-0.63)。#L17 (raw vs norm 反転) を qweighted/const_adjusted でも観察、sim_basis × density 種類の 2 軸非対称性が構造として確定。#33 系列「集計単位で像が変わる」の v1105 拡張 |

既存留保継承: #L17 (raw vs norm 反転) / #L21' (predecessor 連鎖 shuffle A 依存) / #L22' (trajectory↔response の scope 依存) / #L24-29 (Step H-3/H-4 系列) / #L30-L33 (v1104a 4 非対称性) / 48 次元人為性留保 (v1103 GPT 監査 5)

---

## 9. 設計書 §2.x.2 (a)/(b)/(c) 候補方向 (Code A 構造事実、判定は Taka 領域)

### 9.1 観察 1 (§2.2): 段 4-b 地形

期待観察形と本観察事実の対応:
- 期待: alpha non-self-loop で lift_C 最強 → **一致** (alpha_all lift_C 0.165 最強)
- 期待: ESDE 粒度別で lift_C 変動 → **一致** (event 0.077 / step10 0.069 / window 0.128)
- 期待: couple_hit_rate 連続変動分布 → **一致** (scope/粒度別に 0.001-0.221 で連続変動)

### 9.2 観察 2 (§2.3): 段 4-c 地形

- 期待: ESDE event/step10 で trajectory r=0.64 主役 → **一致** (再現)
- 期待: 集約で density 主役 → **一致** (CID_n=2 +0.99、CID_all -0.43、ESDE_all -0.30)
- 期待: raw vs norm 反転が qweighted/const_adjusted でも → **一致** (CID_n=5/6+/ESDE_window で全 density 6 種で sign_flip)

### 9.3 観察 3 (§2.4): 強度マップ

- 期待: #L30-L33 が強度マップにそのまま現れる → **一致** (4 panel heatmap で確認)
- 期待: scope × 粒度連続強度分布 → **一致** (12 strata × 11 数値で連続)
- 期待: density 6 種で 2 軸非対称性 → **一致 + 拡張** (#L36 新規留保)
- パターン読み取りは Phase Result 領域

### 9.4 観察 4 (§2.5): 役割表

- 期待: 5 役割を構造事実から仮割り当て → **一致** (Step F 完了、3 列形式 md 出力)
- v1105a 進行条件 (最小 3 役割成立) → **成立** (候補保持/連想/絞り の 3 役割すべて分離可能、Code A 構造事実報告として記録)

→ **判定は Web Claude Phase Result + Taka 主題評価領域**。

---

## 10. 出力ファイル総覧 (`unified/v1105/`)

| ファイル | サイズ |
|---|---:|
| v1105_phase_design.md | 設計書 v4 (2 AI 監査 + 確認要請 7 反映) |
| v1105_step_a_recognition.md | Code A 認識確認 + 確認要請 7 |
| v1105_step_a_answer.md | Web Claude 回答 (案 B 採用) |
| v1105_step_c_observation_1.py | 観察 1 (段 4-b 地形) |
| v1105_step_d_observation_2.py | 観察 2 (段 4-c 地形) |
| v1105_step_e_observation_3.py | 観察 3 (11 数値強度マップ + heatmap) |
| v1105_step_f_observation_4.py | 観察 4 (5 役割仮割り当て表) |
| v1105_step_g_bit_identity.py | bit-identity 3 層検証 |
| v1105_step_g_bit_identity_report.json | 全 PASS |
| v1105_role_assignment_table.md | 役割表 md (6.7 KB) |
| v1105_step_h_observation_final.md | 本書 |
| outputs/main/observation_1_terrain_4b.parquet | 81 rows |
| outputs/main/observation_2_terrain_4c.parquet | 192 rows |
| outputs/main/observation_3_intensity_map.parquet | 12 strata × 11 数値 |
| outputs/main/observation_4_role_assignment.parquet | 5 roles |
| outputs/v1105_intensity_map.html | 14.9 KB (4 panel heatmap) |

物理層 (v105/v106/v107/v112/v1101a/v1102/v1103/v1104/v1104a main outputs 1,490 ファイル) frozen 維持。

---

## 11. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (v1105 段階 1 観察 1-4) の提示完了。以下は Web Claude + Taka 領域:

1. **§2.x.2 (a)/(b)/(c) 出口判定**: 各観察の構造事実方向は §9 に記録、判定は Web Claude/Taka 領域
2. **v1104 + v1104a + v1105 統合 Phase Result**: 4 観察 + 段 4-b/4-c 統合強度マップ + 役割表を統合、段 4-b/4-c の Genesis/Language 接続点の確定
3. **役割表の出口判定**: 5 役割仮割り当ての採用 / 修正 / 削除 + 全体整合性評価
4. **v1105a 進行判断**: 最小 3 役割成立 (Code A 構造事実) を踏まえた進行可否 + 試行設計書のたたき台 (役割表 md を v1105a 試行設計に翻訳)
5. **#L34-L36 新規留保**: scope 別 Genesis/Language 逆方向強度 / CID_n=2 特殊性 / sim_basis × density 種類の 2 軸非対称性

---

## 12. 一文サマリ (再掲)

Step A-G 全完了、Step A (確認要請 7 案 B 採用) → Step C (観察 1 段 4-b 地形: alpha Genesis 強/Language 弱 vs beta 逆 / CID_n=2 couple_hit_rate 15.7% 断トツ / ESDE_window 粒度感度 1.4%) → Step D (観察 2 段 4-c 地形: trajectory r 2 種 + density r 6 種、coverage 100% / CID_n=2 全 density 6 種 +0.65-0.99 超強 / CID_n=5/6+ + ESDE_window で density 6 種全 sign_flip / ESDE event/step10 で trajectory +0.64 主役 = #L31 再現 / #L17 raw vs norm 反転を qweighted/const_adjusted でも確認) → Step E (観察 3 11 数値強度マップ: 12 strata × 11 数値別レイヤー parquet + 4 panel heatmap 14.9 KB / binary 判定なし / 単一スコア化なし / 絶対格言 #11 厳密適用 / 4 非対称性 #L30-L33 が強度マップにそのまま現れる) → Step F (観察 4 役割表: 5 役割「仮割り当て + 観察支持 + 留保」3 列形式 md 6.7 KB / 確定表でなく v1105a 試行設計書素材 / selector 化禁止維持 / B 意味判定なし / 最小 3 役割成立) → Step G (bit-identity 3 層全 PASS: LAYER_A 4 hash 一致 1.6s / LAYER_B 1,490 frozen v1104a まで含む / LAYER_C 6 件 unified/v1105/ 配下) すべて完了、新規留保候補 #L34-L36 提示 (scope 別 Genesis/Language 逆方向強度 / CID_n=2 極端な特殊性 / CID_n=5/n=6+/ESDE_window で全 density 6 種 sign_flip = sim_basis × density 種類の 2 軸非対称性)、#L17/#L21'/#L22'/#L24-29/#L30-L33 + 48 次元人為性留保継承、設計書 §2.x.2 (a)/(b)/(c) 出口判定 + 役割表の出口判定 + v1105a 進行判断 (最小 3 役割成立を Code A 構造事実として報告) + #L34-L36 解釈統合は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + selector 化禁止 + 判定語制限 + binary 判定/単一スコア化禁止 + 物理層 frozen + judgment 回避 + 0 を 1 にはできない歯止め + 観察方法有利化と区別 + 統合方向遵守) を全 Step で堅持、書込み unified/v1105/ 配下のみ。
