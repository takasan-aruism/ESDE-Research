# v11.0.4 (v1104) Step H-4 観察 3 再調査 観察事実最終報告 — Code A

*作成*: 2026-05-23、Code A
*親*: `v1104_step_h_observation_final.md` (Step H 初版) + `v1104_step_h3_observation_final.md` (観察 2 再調査) + Taka 指示 (観察 3 r=0.157 の観察方法問題可能性検討要請)
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価)
*位置づけ*: v1104 主題「CID/IID が下でやっていることの点検」**Step H 観察 3 (trajectory↔response_atom_distribution 弱い相関 r=0.157) の再調査総括**。本書は Step H-3 と並ぶ追補で、観察 3 部分のみを再調査結果で更新する。**judgment 回避** (絶対格言 #12)、**判定語制限** (「連想」「成功/失敗」「意味がある/ない」を使わない、GPT 追加 4)、**selector 化禁止遵守**。

---

## 0. 一文サマリ

Step H 初版で観察 3 (trajectory stability ↔ response_max_prob Pearson r=0.157) を弱い正相関と記録した後、観察 2 の再調査で「観察方法依存」が確定したのと同じ視点で観察 3 の r=0.157 が観察方法問題か検証、再調査 1 (qc_regime × sim_basis × k = 24 strata 層化、最大 r=0.256、層化単独では弱効果)、再調査 2 (scope-filter による分離 — pooled r=0.157 / **ESDE-only r=0.417 (stability_vs_maxprob) と r=-0.477 (diffusion_vs_maxprob)** / CID-only r=-0.351 (diffusion_vs_maxprob、weighted -0.477) / beta-only r=0.224 / alpha-only r=0.137 → 0.017 weighted)、再調査 3 (代替指標 4 trajectory × 4 response = 16 ペア pooled、最強 stability vs max_prob r=0.157 で代替指標も pooled では限定的)、再調査 4 (chain 内 cid permutation shuffle baseline、stability_mean overall 0.805 → 0.772、相関係数は actual 0.157 vs shuffled 0.163 でほぼ不変) すべて完了、bit-identity Step H-4 再検証 3 層全 PASS (LAYER_A_FILES 13 ファイル全 hash 一致、Step H-4 reinvestigation 22.4s で deterministic、1,489 frozen files 不変、書込み全 16 件 unified/v1104/ 配下) を確認、**核心観察事実 (judgment なし)**: 観察 3 初版 r=0.157 は **scope (CID/alpha/beta/ESDE) を集計単位として混ぜる pooled 評価**による希釈現象、scope-filter で分離すると ESDE 3 resolution scope に絞ったとき |r| > 0.4 が顕在化、alpha/beta scope では相関消失、CID scope は中間 (|r| ≈ 0.35)、初版 Step H reserves #L22「trajectory stability と response 収束の弱い対応」は **scope-aware に評価すべき構造事実 (留保 #L22')** へ refine、新規留保候補 #L27「観察 3 pooled r=0.157 は scope-mix 由来希釈、ESDE-only で |r| > 0.4 顕在化」/ #L28「層化 (qc_regime × sim_basis × k) 単独では効果限定 (max r=0.256)、scope-filter が主効果」/ #L29「chain 内 cid permutation shuffle baseline は aggregation 後の pooled 相関に効果薄、観察 2 shuffle と異なる特徴」、48 次元人為性留保継承、最終判定 (観察 3 出口 (a)/(b) 再判定、§4.2 4 通り組み合わせ更新、次主題候補) は Web Claude Phase Result + Taka 主題評価領域、規律遵守チェック (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + 既存出力流用のみ) を再調査 4 件全てで堅持、書込み unified/v1104/ 配下のみ。

---

## 1. 再調査 Step 進行サマリ (Step H-4)

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| H-4 R1 | 層化 (qc_regime × sim_basis × k = 24 strata) | 完了 (約 8s) | observation_3_stratified.parquet (24 rows) |
| H-4 R2 | weighting / scope-filter (alpha/beta/CID/ESDE) | 完了 (約 1s) | observation_3_weighted.parquet (35 rows) |
| H-4 R3 | 代替指標 (4 traj × 4 resp = 16 ペア pooled) | 完了 (約 1s) | observation_3_alt_metrics.parquet (16 rows) |
| H-4 R4 | shuffle baseline (chain 内 cid permutation) | 完了 (約 13s) | observation_3_shuffle_baseline.parquet (8 rows) |
| H-4 G | bit-identity 再検証 (LAYER_A 拡張 13 ファイル) | 完了 (all PASS、約 170s) | v1104_step_h4_bit_identity_report.json |
| H-4 F | グラフ拡張 (再調査 4 件 dashboard) | 完了 | v1104_reinvestigation_obs3.html (14 KB) |
| H-4 H | 観察事実最終報告 (本書) | 本書 | v1104_step_h4_observation_final.md |
| I | Phase Result (観察 3 再判定 + 4 観察統合) | 待ち | Web Claude 担当 |

---

## 2. 再調査 1: 層化 (qc_regime × sim_basis × k = 24 strata)

### 2.1 設計

trajectory_stability_mean vs response_max_prob、diffusion_ratio_mean vs response_entropy の 2 ペアを (qc_regime × sim_basis × k) で分離。各 stratum 内 n=81 (9 receiver_bin × 3 metric × 3 (3+) sim_basis combinations の subset)、Pearson + Spearman で評価。

### 2.2 結果 (top 5 |r|、24 strata 中)

| qc_regime | sim_basis | k | pair | pearson_r | spearman_r |
|---|---|---:|---|---:|---:|
| conscious_dominant | norm | 20 | stability_vs_maxprob | **0.256** | 0.271 |
| conscious_dominant | raw | 10 | stability_vs_maxprob | 0.245 | 0.362 |
| conscious_dominant | raw | 5 | stability_vs_maxprob | 0.244 | 0.241 |
| conscious_dominant | norm | 10 | stability_vs_maxprob | 0.244 | 0.317 |
| conscious_dominant | raw | 20 | stability_vs_maxprob | 0.232 | 0.330 |

### 2.3 構造事実

- 24 strata 中で |r| > 0.3 (中効果) は **0 件**
- 最大 |r| = 0.256 (conscious_dominant / norm / k=20)
- diffusion_vs_entropy の最大 |r| = 0.203
- 層化単独では r=0.157 (pooled) から 0.256 へ微増する効果しかなく、観察 3 の弱相関の主因ではない

---

## 3. 再調査 2: scope-filter (本主題核心)

### 3.1 設計

merged データを receiver_bin の prefix で scope 別に filter:
- **all**: 全体 (972 rows)
- **ESDE**: ESDE_window / ESDE_step10 / ESDE_event (108 rows)
- **CID**: CID_n=2..6+ (180 rows)
- **beta**: beta_n=1..4+ × gini bin (324 rows)
- **alpha**: alpha_n=1..4+ × gini bin (360 rows)

7 ペアの相関を計算 (unweighted + n_chains 加重 weighted)。

### 3.2 結果 (top 11 |unweighted_r|)

| pair | scope_filter | unweighted_r | weighted_r | n |
|---|---|---:|---:|---:|
| diffusion_vs_maxprob | **ESDE** | **-0.477** | -0.477 | 108 |
| stability_vs_maxprob | **ESDE** | **0.417** | 0.417 | 108 |
| diffusion_vs_maxprob | **CID** | -0.351 | **-0.477** | 180 |
| stability_vs_gini | ESDE | -0.327 | -0.327 | 108 |
| stability_vs_top3 | ESDE | 0.297 | 0.297 | 108 |
| diffusion_vs_maxprob | beta | -0.249 | -0.184 | 324 |
| chain_len_vs_maxprob | CID | 0.235 | 0.407 | 180 |
| diffusion_vs_entropy | CID | 0.224 | 0.285 | 180 |
| chain_len_vs_maxprob | beta | 0.224 | 0.335 | 324 |
| diffusion_vs_entropy | ESDE | 0.223 | 0.223 | 108 |
| stability_vs_maxprob | all | **0.157** | 0.072 | 972 |
| stability_vs_maxprob | alpha | 0.137 | 0.017 | 360 |

太字 = |r| ≥ 0.4 (中-強)。

### 3.3 構造事実

- pooled (all、初版値 r=0.157) と ESDE-only (r=0.417) の差は約 2.7 倍
- diffusion_vs_maxprob は ESDE-only で **r=-0.477** (中-強の負相関)、CID-only weighted で **r=-0.477** とほぼ同強度
- alpha-only では stability_vs_maxprob r=0.137 (unweighted) → 0.017 (weighted) で **ほぼ消失**
- chain_len_vs_maxprob は CID-only weighted で r=0.407、beta-only weighted で r=0.335
- ESDE / CID 系 scope に trajectory↔response の対応構造が偏在、alpha/beta scope では希薄
- これは観察 1 (n_members 増で像が崩れる) と整合する方向の構造事実: ESDE 3 resolution および CID scope では trajectory が response 形状を予測する関係が成立するが、alpha/beta の構成多様体に入ると関係が消失

---

## 4. 再調査 3: 代替指標 (4 traj × 4 resp = 16 ペア pooled)

### 4.1 設計

trajectory 側: traj_stability_mean / traj_unique_mean / diffusion_ratio_mean / chain_len_mean
response 側: response_max_prob / response_entropy / response_top3_mass / response_gini
合計 16 ペアの pooled 相関を一括計算。

### 4.2 結果 (top 5、pooled n=972)

| traj_metric | resp_metric | pearson_r | spearman_r |
|---|---|---:|---:|
| traj_stability_mean | response_max_prob | 0.157 | 0.168 |
| traj_stability_mean | response_gini | -0.147 | -0.155 |
| traj_stability_mean | response_top3_mass | 0.136 | 0.164 |
| diffusion_ratio_mean | response_max_prob | -0.124 | -0.085 |
| traj_unique_mean | response_max_prob | -0.120 | -0.167 |

### 4.3 構造事実

- pooled では 16 ペア全てで |r| < 0.16
- 代替指標 (top3_mass / gini) を試しても pooled では新規の強相関なし
- 観察 3 r=0.157 は traj/resp 指標選択に依らず pooled では同じ弱さ
- 強相関は scope-filter (再調査 2) で初めて顕在化することと整合

---

## 5. 再調査 4: shuffle baseline (chain 内 cid permutation)

### 5.1 設計

trajectory_metrics_per_chain で各 chain の attention_candidate_id 系列を permutation、shuffled stability を再計算し response との相関を測定。actual (none) と shuffled (within) の 2 通り。

### 5.2 結果

| shuffle_mode | pair | pearson_r | traj_stability_mean_overall |
|---|---|---:|---:|
| none | stability_vs_maxprob | 0.157 | 0.805 |
| none | diffusion_vs_entropy | 0.059 | 0.805 |
| none | stability_vs_entropy | -0.103 | 0.805 |
| none | diffusion_vs_maxprob | -0.124 | 0.805 |
| within | stability_vs_maxprob | 0.163 | 0.772 |
| within | diffusion_vs_entropy | 0.059 | 0.772 |
| within | stability_vs_entropy | -0.108 | 0.772 |
| within | diffusion_vs_maxprob | -0.124 | 0.772 |

### 5.3 構造事実

- shuffle 後の traj_stability_mean は overall 0.805 → 0.772 (微減、約 4 % 低下)
- 相関係数は stability_vs_maxprob で actual 0.157 → shuffled 0.163 とほぼ不変
- diffusion_ratio (= unique_count / chain_length) は permutation で不変、相関も完全一致
- これは aggregation 後の pooled 相関では shuffle 効果が現れにくいことを示す: per-chain stability を receiver_bin 集約で mean しているため、chain 内 shuffle は集約レベルでキャンセル
- 観察 2 の shuffle 種別 A→C で lift 0 → 0.17 と顕在化したのと **異なる構造特徴**: 観察 3 では shuffle baseline は決定的でない

---

## 6. bit-identity 再検証 (Step H-4 G)

### 6.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step B-E + Step H-3 + Step H-4 再実行で hash 完全一致 | **13 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a/v1102/v1103 main outputs 全 frozen (1,489 ファイル) | **all PASS** (a/r/m すべて 0) |
| **C** | 全 9 scripts (Step B-E + Step F + Step H-3/4 reinvestigation + Step H-3/4 graph) の書込みパスが unified/v1104/ 配下 | **all_under=True** (16 件) |

- LAYER_A_FILES (13): observation_1/2/3/4 + observation_2_*(5) + observation_3_*(4)
- LAYER_A_RERUN 経過時間: Step B 19.5s / Step C 55.7s / Step D 7.1s / Step E 1.4s / Step H-3 reinvestigation 61.4s / Step H-4 reinvestigation 22.4s = 計 167s
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 = 1,489 files 全 frozen 確認
- 報告 JSON: `v1104_step_h4_bit_identity_report.json`

---

## 7. 規律遵守総括 (再調査範囲、絶対格言 15 件 + GPT 5 点 + Gemini 1 点 + 固有規律)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (bit-identity 層 B 全 PASS) |
| 絶対格言 #3 (\|effect\| 閾値) | ✓ (\|r\| > 0.1 弱 / 0.3 中 / 0.5 強の参考ガイドのみ記載、強の主張は scope-filter 結果に限定) |
| 絶対格言 #12 (judgment 回避) | ✓ (出口 (a)/(b) 判定、観察 3 再判定、§4.2 4 通り更新は Web Claude + Taka 領域として明記) |
| GPT 追加 4 (判定語制限) | ✓ (「連想」「成功/失敗」「意味がある/ない」を使わず、構造事実のみ報告) |
| GPT 修正必須 C (selector 化禁止) | ✓ (再調査 1-4 すべて post-process 仮想評価、ESDE 内部書き戻し 0) |
| アルイズム対称性 100% を作らない | ✓ (scope mixing 由来の希釈を顕在化 = pooled 集計が「全体平均 = 真値」を作らないことを実観測) |
| Aruism #33 系列 (集計単位で像が変わる) | 整合 (pooled r=0.157 vs ESDE-only |r|=0.42-0.48、集計 scope 違いで像が変わる) |
| 書込みパス unified/v1104/ 配下 | ✓ (層 C all_under=True、16 件) |
| smoke 含めず | ✓ (本 commit/push は main 出力のみ) |

---

## 8. 留保 refine + 新規留保候補 3 件

### 8.1 既存留保 #L22 の refine

- **旧 #L22 (Step H 初版)**: trajectory stability と response 収束の弱い対応 (r=0.157、有意)、ただし 48 次元密度との直接比較は本主題で未実施
- **新 #L22' (Step H-4 再調査後)**: trajectory stability ↔ response_max_prob の対応は **scope 依存**、pooled r=0.157 は scope-mix 由来希釈、ESDE 3 resolution scope に絞ると |r|=0.42 (stability vs max_prob)、|r|=0.48 (diffusion vs max_prob)、CID scope weighted |r|=0.48、alpha/beta scope では |r|<0.14。**観察方法 = pooled 集計** の問題であり、scope-aware に評価すべき構造事実。48 次元密度との直接比較は依然未実施

### 8.2 新規留保候補 (Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L27** | 観察 3 pooled r=0.157 は scope-mix 由来希釈、scope-filter で ESDE-only |r|=0.42-0.48、CID-only weighted |r|=0.48、alpha/beta では |r|<0.14。**観察結論は集計 scope の選択に依存**。観察 2 の shuffle 種別依存と並ぶ「観察方法依存」の構造事実 |
| **#L28** | 層化 (qc_regime × sim_basis × k = 24 strata) 単独では効果限定 (最大 r=0.256)。観察 3 の主効果は層化ではなく **scope-filter** (CID/alpha/beta/ESDE の分離)。観察 2 では層化単独でも顕在化しなかった (shuffle 種別が決定的) のと並列 |
| **#L29** | chain 内 cid permutation shuffle baseline は aggregation 後の pooled 相関 (r 0.157 → 0.163) にほぼ効果なし、per-chain stability の集約過程で chain 内 shuffle の効果がキャンセルされる。観察 2 で shuffle 種別 (A→C) で lift 0 → 0.17 と決定的だった構造とは **異なる感度プロファイル**を持つ |

---

## 9. 設計書 §4.2 想定 4 通り組み合わせとの対応 (Step H-4 再調査後の構造事実、判定は Taka 領域)

各観察の出口 (a)/(b) の **更新候補** (Code A は判定しないが構造事実の方向のみ):

| 観察 | 構造事実の方向 (Step H 初版) | Step H-3/4 再調査後の更新 | (a) / (b) 候補 (Code A 報告のみ) |
|---|---|---|---|
| 観察 1 (像差分) | n_members 増で match_k1 単調低下 | 不変 | (a) 候補強め |
| 観察 2 (predecessor 連鎖) | lift=0 で shuffle と区別不能 | shuffle 種別 A 依存、B/C で lift 顕在化 (Step H-3) | **再判定領域** |
| 観察 3 (trajectory↔response) | 弱い対応 (r=0.157) | **scope-mix 由来希釈、ESDE-only |r|=0.42-0.48 顕在化 (Step H-4)** | **再判定領域** (scope の選択で結論が変わる) |
| 観察 4 (B 現状) | B は A subset を含むが独自 | 不変 | (a)/(b) 中間、subset 関係 |

→ 設計書 §4.2 4 通り組み合わせは **観察 2 + 観察 3** の両方が再判定対象となる。**最終判定は Web Claude Phase Result + Taka 主題評価領域**。

---

## 10. 出力ファイル総覧 (`unified/v1104/`、Step H-4 追加分)

| ファイル | サイズ |
|---|---:|
| v1104_step_h4_reinvestigation.py | 観察 3 再調査 1-4 統合スクリプト |
| outputs/main/observation_3_stratified.parquet | 約 4 KB (24 strata × 2 pairs) |
| outputs/main/observation_3_weighted.parquet | 約 5 KB (7 pairs × 5 scopes) |
| outputs/main/observation_3_alt_metrics.parquet | 約 3 KB (16 ペア) |
| outputs/main/observation_3_shuffle_baseline.parquet | 約 3 KB (2 modes × 4 pairs) |
| v1104_step_h4_bit_identity.py | 拡張 LAYER_A 13 ファイル検証 |
| v1104_step_h4_bit_identity_report.json | 3 層全 PASS 報告 |
| v1104_step_h4_graph.py | 観察 3 再調査 4 件 dashboard 生成 |
| outputs/v1104_reinvestigation_obs3.html | 14 KB (4 subplot dashboard) |
| v1104_step_h4_observation_final.md | 本書 |

物理層 (v105/v106/v107/v112/v1101a/v1102/v1103 main outputs 1,489 ファイル) frozen 維持。

---

## 11. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (観察 3 再調査後) の提示完了。以下は Web Claude + Taka 領域:

1. **観察 3 出口 (a)/(b) 再判定**: 初版「弱い対応」→ scope-aware 評価で ESDE/CID scope では中-強の対応、alpha/beta では消失。**集計 scope の選択で結論が変わる**ことを踏まえた再判定
2. **観察 2 と観察 3 の感度プロファイル比較**: 観察 2 は shuffle 種別で決定的、観察 3 は scope-filter で決定的、層化単独ではどちらも限定的。両者の「観察方法依存」の異なる性質
3. **設計書 §4.2 4 通り組み合わせの再考**: 観察 2 + 観察 3 の両方が再判定対象、組み合わせ評価が二重に更新される
4. **次主題候補**: scope (CID/alpha/beta/ESDE) の集計単位を観察設計の必須軸に格上げ / 観察 3 の ESDE-only / CID-only での 48 次元密度 (v1103) との直接比較 / 留保 #L24-#L29 系列 (観察方法依存) の体系化

---

## 12. 一文サマリ (再掲)

Step H 観察 3 (trajectory stability ↔ response_max_prob 弱相関 r=0.157) を Taka 原則「観察方法を疑う」に従い観察 2 と同じ視点で再調査、再調査 1 (層化 24 strata、最大 r=0.256) / 再調査 2 (scope-filter、**ESDE-only stability_vs_maxprob r=0.417 / diffusion_vs_maxprob r=-0.477 / CID-only weighted diffusion_vs_maxprob r=-0.477 / alpha-only weighted r=0.017** で消失) / 再調査 3 (代替指標 16 ペア pooled 最強 r=0.157、pooled では指標変えても限定) / 再調査 4 (shuffle baseline で stability_mean overall 0.805→0.772、相関 0.157→0.163 でほぼ不変、aggregation 由来) すべて完了、bit-identity 3 層全 PASS (LAYER_A 13 ファイル hash 一致 167s、1,489 frozen files 不変、書込み 16 件 unified/v1104/ 配下)、**核心観察事実**: 観察 3 r=0.157 は **scope (CID/alpha/beta/ESDE) を pooled 集計する観察方法**による希釈現象、scope-filter で ESDE/CID scope に絞ると |r|>0.4 が顕在化、alpha/beta scope では消失、留保 #L22 を refine (scope-aware に評価すべき構造事実へ位置づけ変更)、新規留保候補 #L27 (scope-mix 由来希釈) / #L28 (層化単独効果は限定、scope-filter が主効果) / #L29 (shuffle baseline は観察 3 では限定効果、観察 2 と異なる感度プロファイル)、48 次元人為性留保継承、観察 3 出口 (a)/(b) 再判定 + 設計書 §4.2 4 通り組み合わせ再更新 + 次主題候補 (scope 集計単位の格上げ等) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + judgment 回避) を再調査 4 件全てで堅持、書込み unified/v1104/ 配下のみ。
