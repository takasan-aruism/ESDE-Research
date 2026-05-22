# v11.0.4 (v1104) Step H-3 観察 2 再調査 観察事実最終報告 — Code A

*作成*: 2026-05-23、Code A
*親*: `v1104_step_h_observation_final.md` (Step H 初版) + `v1104_observation_2_reinvestigation_directive.md` (Web Claude 再調査指示) + `v1104_step_h2_recognition.md` (Code A 再調査認識、Taka 承認済) + Step H-3 再調査 1-4 出力
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価)
*位置づけ*: v1104 主題「CID/IID が下でやっていることの点検 — 段 4-b/4-c を支える ESDE 内部処理の確認」**Step H 観察 2 (predecessor 連鎖 lift=0) の再調査総括**。本書は Step H 初版を上書きせず、観察 2 部分のみを再調査結果で更新する追補。**judgment 回避** (絶対格言 #12)、**判定語制限** (「連想」「成功/失敗」「意味がある/ない」を使わない、GPT 追加 4)、**selector 化禁止遵守**、**観察方法問題の構造事実化**。

---

## 0. 一文サマリ

Step H 初版で観察 2 (predecessor 連鎖) lift=0 / 85% self-loop の構造事実を留保 #L21 として記録した後、Taka より「構造的に作ってきたものが構造を辿れないなら観察方法を疑う」原則で再調査指示、Web Claude 指示書 + §4 確認回答 (4.1 (iii) n_core_member 採用 / 4.2 種別 A 確認 + B/C 追加 / 4.3 event_trajectory 採用) を受領、再調査 1 (n_members × qc_gini 27 bin 層化、0/27 significant、|lift_max| 0.005)、再調査 2 (shuffle 種別 3 種比較 — A 現状 chain内 permutation / B chain間 入れ替え / C global cid pool、決定的数値 = **shuffle A: alpha 0.000 / beta 0.0002 / CID 0.000 / ESDE_window -0.0002 (現状再現)、shuffle B: alpha 0.023 / beta 0.046 / CID 0.066 / ESDE_window 0.012、shuffle C: alpha 0.166 / beta 0.139 / CID 0.143 / ESDE_window 0.127** — shuffle 種別を変えると lift が顕在化、cid_sim_matrix 分布は mean 0.937 / std 0.068 で flat ではない)、再調査 3 (粒度 3 階層 = event 平均 atom_change_rate 0.181 / step10 0.046 / window 0.338、粒度で像変化)、再調査 4 (chain-level full self-loop 比率 69.1%、self-loop 内 atom_change_rate=0 = 構造的零、non-self-loop でも scope 別 |lift|<0.01) すべて完了、bit-identity Step H-3 再検証 3 層全 PASS (LAYER_A_FILES 9 ファイル全 hash 一致、Step H-3 reinvestigation 自体も deterministic 61.4s、1,489 frozen files 不変、書込み全 11 件 unified/v1104/ 配下) を確認、**核心観察事実 (judgment なし)**: 観察 2 初版 lift=0 は **shuffle 種別 A (chain内 permutation) が chain 内 cid 集合を保存する性質** に由来する shuffle 方法依存の現象であり、chain 間入れ替え (B) または global cid pool (C) で shuffle すると alpha/beta/CID/ESDE_window 全 scope で |lift| ≥ 0.01 が顕在化、初版留保 #L21「predecessor 連鎖は類似度地形と区別不能、ランダム walk と等価な可能性」は **shuffle 方法に依存する構造事実 (留保 #L21')** へ refine、新規留保候補 #L24「shuffle 種別 (within-chain / between-chain / global pool) によって lift が 0 → 0.17 の幅で変動」/ #L25「chain 完全 self-loop 69.1% は per-window rank_1_atom 固定の構造的零、観察 2 lift=0 の主要原因の 1 つ」/ #L26「粒度 (event/step10/window) で atom_change_rate が 0.05 → 0.34 まで変動、留保 #33 系列『集計単位で像が変わる』と整合」、48 次元人為性留保継承、最終判定 (観察 2 出口 (a)/(b) 再判定、§4.2 4 通り組み合わせ更新、次主題候補) は Web Claude Phase Result + Taka 主題評価領域、規律遵守チェック (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + 既存出力流用のみ) を再調査 4 件全てで堅持、書込み unified/v1104/ 配下のみ。

---

## 1. 再調査 Step 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| H-2 | 再調査認識確認 (Web Claude §4 確認 3 項回答受領後) | 完了 (Taka 承認) | v1104_step_h2_recognition.md |
| H-3 R1 | 層化再調査 (n_alpha × n_beta × gini_27 bin) | 完了 (5s) | observation_2_restratified.parquet (27 bins) |
| H-3 R2 | shuffle 3 種比較 (A 現状 / B chain間 / C global pool) | 完了 (38s) | observation_2_shuffle_variants.parquet + cid_sim_matrix_distribution.parquet |
| H-3 R3 | 粒度 3 階層 (window/step10/event) | 完了 (12s) | observation_2_resolution.parquet (72 rows) |
| H-3 R4 | self-loop / non-self-loop 分離 | 完了 (6s) | observation_2_self_loop_split.parquet (11 rows) |
| H-3 G | bit-identity 再検証 (LAYER_A 拡張 9 ファイル) | 完了 (all PASS、約 146s) | v1104_step_h3_bit_identity_report.json |
| H-3 F | グラフ拡張 (再調査 4 件 dashboard) | 完了 | v1104_reinvestigation.html (13 KB) |
| H-3 H | 観察事実最終報告 (本書) | 本書 | v1104_step_h3_observation_final.md |
| I | Phase Result (観察 2 再判定 + 4 観察統合) | 待ち | Web Claude 担当 |

---

## 2. 再調査 1: n_members × qc_gini 層化 (27 bin)

### 2.1 設計 (Web Claude §4.1 (iii) n_core_member 採用)

chain ごとに `n_alpha_min, n_beta_min, qc_gini` を集計 (Step G 既存 stratification 流儀踏襲)、3 × 3 × 3 = 27 bin に分割、各 bin 内で shuffle baseline (chain 内 cid permutation = shuffle A) との lift_over_baseline を計算。

### 2.2 結果

| change_scope | n_bin | lift_mean (bin 内平均) | |lift_max| | 有意 bin |
|---|---:|---:|---:|---:|
| CID | 5 | 0.00000 | 0.00000 | 0 / 5 |
| alpha | 10 | 0.00025 | 0.00167 | 0 / 10 |
| beta | 9 | 0.00070 | 0.00511 | 0 / 9 |
| ESDE_event | 1 | 0.00001 | 0.00001 | 0 / 1 |
| ESDE_step10 | 1 | -0.00002 | 0.00002 | 0 / 1 |
| ESDE_window | 1 | -0.00022 | 0.00022 | 0 / 1 |
| **合計** | **27** | — | **0.005** | **0 / 27** |

### 2.3 構造事実

- 全 27 bin で |lift| < 0.01 (絶対格言 #3 基準)
- 27 bin の最大 |lift| = 0.005 (beta scope の 1 bin)
- 層化は観察 2 初版 lift=0 を変えなかった — ただし本再調査はあくまで shuffle 種別 A (chain 内 permutation) を維持した層化であり、shuffle 方法に由来する性質はそのまま残った
- 留保 #L21 (predecessor 連鎖は shuffle baseline と区別不能) は本再調査の範囲では維持されるが、**再調査 2 で別 shuffle 種別では区別可能**になることが判明したため、後述する refine 対象となる

---

## 3. 再調査 2: shuffle 種別 3 種比較 (本主題核心)

### 3.1 設計 (Web Claude §4.2 種別 A 確認 + B/C 追加方針通り)

shuffle 種別を 3 種定義し、各 chain ごとに 3 種すべての lift を計算:

- **A**: chain 内 cid 集合の permutation (現行、初版 Step C と完全等価)
- **B**: chain 間 cid 入れ替え (chain サイズ保存、全体 cid 分布保存)
- **C**: global cid pool からの一様サンプル (chain 構造完全破壊)

各 shuffle 種別ごとに actual chain の atom_change_rate (per-scope) と shuffle 後の atom_change_rate を比較、`lift = actual - baseline` を計算。

### 3.2 結果 (scope-wise lift 平均、全 24 seeds 集計)

| change_scope | shuffle A (現状) | shuffle B (chain間) | shuffle C (global pool) |
|---|---:|---:|---:|
| **CID** | 0.0000 | **0.0663** | **0.1427** |
| **alpha** | 0.0000 | **0.0229** | **0.1664** |
| **beta** | 0.0002 | **0.0463** | **0.1393** |
| **ESDE_event** | 0.0000 | **0.0587** | **0.0764** |
| **ESDE_step10** | -0.0000 | **0.0549** | **0.0693** |
| **ESDE_window** | -0.0002 | **0.0125** | **0.1274** |

- |lift|>0.01 = 絶対格言 #3 基準
- 太字 = |lift| ≥ 0.01 (基準超過)

### 3.3 cid_sim_matrix 分布 (パターン δ 排除確認)

| 統計量 | 値 |
|---|---:|
| mean | 0.9366 |
| median | 0.9681 |
| std | 0.0680 |
| p5 | 0.7872 |
| p95 | 0.9931 |
| p5–p95 spread | 0.2059 |

- mean は高い (0.937) が std 0.068 / p5–p95 spread 0.206 で **flat ではない** — pattern δ (sim matrix が完全 flat なため shuffle と区別不能) は **排除**

### 3.4 構造事実

- shuffle A (chain 内 permutation) は **chain 内 cid 集合をそのまま保存**するため、cid 由来の per-window rank_1_atom 集合は shuffle 前後で変わらず、atom_change_rate も保存 → lift ≒ 0
- shuffle B (chain 間 cid 入れ替え) で alpha 0.023 / beta 0.046 / CID 0.066 / ESDE_window 0.012、全 scope で |lift| ≥ 0.01 が顕在化
- shuffle C (global pool) で alpha 0.166 / beta 0.139 / CID 0.143 / ESDE_window 0.127 と更に増大
- cid_sim_matrix は flat ではない (std 0.068、spread 0.206) ため、shuffle C で得られた lift は cid_sim 地形の局所性に由来する構造事実と整合的
- **初版 Step C lift=0 は shuffle 種別 A 固有の性質 (chain 内集合保存) に由来する観察方法依存の現象**であることが確定 (Code A 報告、judgment は Web Claude + Taka 領域)

---

## 4. 再調査 3: 粒度 3 階層 (window / step10 / event)

### 4.1 設計 (Web Claude §4.3 event_trajectory 採用)

predecessor 連鎖を 3 階層で評価:
- **window**: per-window rank_1_atom (Step C 既存)
- **step10**: 10 step 単位 majority vote
- **event**: ESDE event 単位 majority vote (event_trajectory 使用、計算量 NG 時 Web Claude 報告 → 計算可能だったため採用)

### 4.2 結果 (24 seeds 平均)

| resolution | atom_change_rate | mean_inter_cid_sim | n_records (per seed avg) |
|---|---:|---:|---:|
| event | 0.1808 | 0.9366 | 15,504 |
| step10 | 0.0458 | 0.9368 | 73,798 |
| window | 0.3382 | 0.9164 | 1,312 |

### 4.3 構造事実

- atom_change_rate は粒度で 0.046 (step10) → 0.181 (event) → 0.338 (window) と変動
- inter_cid_sim は粒度に依存せずほぼ一定 (0.917-0.937)
- 留保 #33 系列「集計単位で像が変わる」と整合的な構造事実
- window 粒度 (Step C 既存) は atom 変化が最も多く検出される粒度であり、初版 Step C の lift 計算粒度はあくまで window だった点を改めて確認

---

## 5. 再調査 4: self-loop / non-self-loop 分離

### 5.1 設計

chain-level full self-loop (全 edge で predecessor_cid == current_cid) を分離、その内外で per-scope の atom_change_rate と lift を計算。

### 5.2 結果

| change_scope | is_full_self_loop | atom_chg_rate | lift_mean | 有意 |
|---|:---:|---:|---:|:---:|
| CID | True | 0.0000 | — | — |
| alpha | False | 9.38 (※) | <0.01 | False |
| alpha | True | 0.0000 | — | — |
| beta | False | 7.65 | <0.01 | False |
| beta | True | 0.0000 | — | — |
| ESDE_event | False | 6.98 | <0.01 | False |
| ESDE_event | True | 0.0000 | — | — |
| ESDE_step10 | False | 6.26 | <0.01 | False |
| ESDE_step10 | True | 0.0000 | — | — |
| ESDE_window | False | 14.49 | <0.01 | False |
| ESDE_window | True | 0.0000 | — | — |

※ atom_chg_rate は per-chain の categorical 変化総数 (rate ではなく count) を示す raw 量、scope 比較目的のみ

### 5.3 構造事実

- chain-level full self-loop 比率: **69.1%** (24 seeds 集計、初版 Step C で報告した「edge-level 85% self-loop」とは集計単位が異なる、chain-level でも 7 割弱)
- self-loop chain 内の atom_change_rate は **構造的に 0** (同じ cid なら per-window rank_1_atom は同じであり、atom_changes は定義上 0)
- non-self-loop でも全 scope で |lift|<0.01 (shuffle A に対して)、これは shuffle A が chain 内 cid 集合を保存する性質ゆえ
- 留保 #L21 が示した「lift=0」のうち少なくとも 69.1% は self-loop による構造的零 + 残りも shuffle A の集合保存性質に由来する人為性で説明可能

---

## 6. bit-identity 再検証 (Step H-3 G)

### 6.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step B-E + Step H-3 reinvestigation 再実行で hash 完全一致 | **9 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a/v1102/v1103 main outputs 全 frozen (1,489 ファイル) | **all PASS** (a/r/m すべて 0) |
| **C** | 全 7 scripts (Step B-E + Step F + Step H-3 reinvestigation + Step H-3 graph) の書込みパスが unified/v1104/ 配下 | **all_under=True** (11 件) |

- LAYER_A_FILES (9): observation_1/2/3/4 + observation_2_restratified + observation_2_shuffle_variants + cid_sim_matrix_distribution + observation_2_resolution + observation_2_self_loop_split
- LAYER_A_RERUN 経過時間: Step B 19.2s / Step C 56.5s / Step D 7.2s / Step E 1.4s / Step H-3 reinvestigation 61.4s = 計 146s
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 = 1,489 files 全 frozen 確認
- 報告 JSON: `v1104_step_h3_bit_identity_report.json`

---

## 7. 規律遵守総括 (再調査範囲、絶対格言 15 件 + GPT 5 点 + Gemini 1 点 + 固有規律)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.5/6/7、v1101a、v1102、v1103 read-only、bit-identity 層 B 全 PASS) |
| 絶対格言 #3 (\|lift\|>0.01 効果サイズ基準) | ✓ (再調査全 4 件で太字判定基準として明示) |
| 絶対格言 #12 (judgment 回避) | ✓ (出口 (a)/(b) 判定、観察 2 再判定、§4.2 4 通り更新は Web Claude + Taka 領域として明記) |
| GPT 追加 4 (判定語制限) | ✓ (「連想」「成功/失敗」「意味がある/ない」を使わず、構造事実のみ報告) |
| GPT 修正必須 C (selector 化禁止) | ✓ (再調査 1-4 すべて post-process 仮想評価、ESDE 内部書き戻し 0) |
| アルイズム対称性 100% を作らない | ✓ (shuffle 種別 A: chain 内集合 100% 保存、を回避すべく B/C を追加検証) |
| Aruism #33 系列 (集計単位で像が変わる) | 整合 (再調査 3 粒度で atom_change_rate 7 倍変動) |
| 書込みパス unified/v1104/ 配下 | ✓ (層 C all_under=True、11 件) |
| smoke 含めず | ✓ (本 commit/push は main 出力のみ) |

---

## 8. 留保 refine + 新規留保候補 3 件

### 8.1 既存留保 #L21 の refine

- **旧 #L21 (Step H 初版)**: predecessor 連鎖は cid_atom_sim_matrix 類似度地形と shuffle baseline で区別不能 (lift=0、85% self-loop)、ランダム walk と等価な可能性
- **新 #L21' (Step H-3 再調査後)**: predecessor 連鎖の lift=0 は **shuffle 種別 A (chain 内 permutation)** が chain 内 cid 集合を保存する性質に由来する shuffle 方法依存の現象。shuffle 種別 B (chain 間入れ替え) で |lift| 0.012-0.066、種別 C (global pool) で |lift| 0.069-0.166 と顕在化。**観察方法依存の構造事実** へ位置づけ変更。「ランダム walk と等価」の文言は撤回 (構造を持つ可能性が高いが Code A 判定領域外、Web Claude + Taka 解釈領域)

### 8.2 新規留保候補 (Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L24** | shuffle 種別 (within-chain / between-chain / global pool) によって lift が 0 → 0.17 の幅で変動。観察結論は **shuffle baseline 設計の感度関数**であり、baseline 選択が観察事実そのものを形成する。アルイズム「100% を作らない」と整合的な観察方法批判材料 |
| **#L25** | chain-level full self-loop 69.1% (edge-level では 85%) は per-window rank_1_atom が cid に固定される構造に由来する零、shuffle A における観察 2 lift=0 の主要原因の 1 つ。non-self-loop 30.9% でも shuffle A 由来 |lift|<0.01 が残るのは集合保存性質ゆえ |
| **#L26** | 粒度 (event/step10/window) で atom_change_rate が 0.046 → 0.181 → 0.338 と最大 7 倍変動。留保 #33 系列「集計単位で像が変わる」の predecessor 連鎖固有版。観察 2 の結論は粒度感度関数 |

---

## 9. 設計書 §4.2 想定 4 通り組み合わせとの対応 (再調査後の構造事実、判定は Taka 領域)

各観察の出口 (a)/(b) の **更新候補** (Code A は判定しないが構造事実の方向のみ):

| 観察 | 構造事実の方向 (初版) | 再調査後の更新 | (a) / (b) 候補 (Code A 報告のみ) |
|---|---|---|---|
| 観察 1 (像差分) | n_members 増で match_k1 単調低下 | 不変 | (a) 候補強め (初版維持) |
| 観察 2 (predecessor 連鎖) | lift=0 で shuffle と区別不能 | **shuffle 種別 A 依存、種別 B/C で lift 顕在化** | 初版 (b) 候補強め → **再判定領域** (shuffle 種別の選択で結論が変わる、Web Claude + Taka 領域) |
| 観察 3 (trajectory↔response) | 弱い対応 (r=0.157) | 不変 | (a)/(b) 中間 |
| 観察 4 (B 現状) | B は A subset を含むが独自 | 不変 | (a)/(b) 中間、subset 関係 |

→ 設計書 §4.2 「1+3 (a) / 2 (b) / 4 不明」または「全 (b)」の組み合わせは、**観察 2 の再判定** により再考対象となる。**最終判定は Web Claude Phase Result + Taka 主題評価領域**。

---

## 10. 出力ファイル総覧 (`unified/v1104/`、Step H-3 追加分)

| ファイル | サイズ |
|---|---:|
| v1104_step_h2_recognition.md | 再調査前認識 |
| v1104_step_h3_reinvestigation.py | 再調査 1-4 統合スクリプト |
| outputs/main/observation_2_restratified.parquet | 9 KB (27 bin × 6 scope) |
| outputs/main/observation_2_shuffle_variants.parquet | 15 KB (shuffle A/B/C × scope) |
| outputs/main/cid_sim_matrix_distribution.parquet | 7 KB (cid_sim 分布統計) |
| outputs/main/observation_2_resolution.parquet | 6 KB (window/step10/event × seed) |
| outputs/main/observation_2_self_loop_split.parquet | 7 KB (self-loop × scope × is_full_self_loop) |
| v1104_step_h3_bit_identity.py | 拡張 LAYER_A 9 ファイル検証 |
| v1104_step_h3_bit_identity_report.json | 3 層全 PASS 報告 |
| v1104_step_h3_graph.py | 再調査 4 件 dashboard 生成 |
| outputs/v1104_reinvestigation.html | 14 KB (4 subplot 再調査 dashboard) |
| v1104_step_h3_observation_final.md | 本書 |

物理層 (v105/v106/v107/v112/v1101a/v1102/v1103 main outputs 1,489 ファイル) frozen 維持。

---

## 11. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (再調査後) の提示完了。以下は Web Claude + Taka 領域:

1. **観察 2 出口 (a)/(b) 再判定**: 初版 (b) 候補強め → shuffle 種別 A 依存と判明、shuffle B/C で lift 顕在化。chain 構造は何らかの意味を持つ可能性が高いが、本主題内では判定領域外
2. **shuffle baseline 設計の感度関数性**: アルイズム「100% を作らない」と整合的な観察方法批判材料、次主題候補
3. **設計書 §4.2 4 通り組み合わせの再考**: 観察 2 再判定を反映した組み合わせ評価
4. **次主題候補**: shuffle baseline の標準化 / 粒度感度関数の系統的調査 / 留保 #33 系列「集計単位で像が変わる」拡張 / 観察方法批判 (留保 #L24)

---

## 12. 一文サマリ (再掲)

Step H 観察 2 (predecessor 連鎖 lift=0) を Taka 原則「構造的に作ってきたものが構造を辿れないなら観察方法を疑う」に従い再調査、再調査 1 (層化 27 bin、0/27 significant、|lift_max| 0.005) / 再調査 2 (shuffle 3 種比較、**shuffle A: |lift|<0.001、shuffle B: |lift| 0.012-0.066、shuffle C: |lift| 0.069-0.166**、cid_sim_matrix std 0.068 で flat 排除) / 再調査 3 (粒度 3 階層、atom_change_rate 0.046-0.338 で 7 倍変動) / 再調査 4 (chain-level full self-loop 69.1%、self-loop 内 atom_changes 構造的零) すべて完了、bit-identity 3 層全 PASS (LAYER_A 9 ファイル hash 一致 146s、1,489 frozen files 不変、書込み 11 件 unified/v1104/ 配下)、**核心観察事実**: 観察 2 初版 lift=0 は shuffle 種別 A (chain 内 permutation、chain 内 cid 集合保存) 固有の **観察方法依存の構造事実**、shuffle 種別を変えると lift が 0 → 0.17 の幅で顕在化、留保 #L21 を refine (「ランダム walk 等価」撤回、観察方法依存へ位置づけ変更)、新規留保候補 #L24 (shuffle baseline 設計が観察事実を形成) / #L25 (self-loop 69.1% が lift=0 主要原因) / #L26 (粒度で atom_change_rate 7 倍変動)、48 次元人為性留保継承、観察 2 出口 (a)/(b) 再判定 + 設計書 §4.2 4 通り組み合わせ更新 + 次主題候補 (shuffle baseline 標準化等) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + judgment 回避) を再調査 4 件全てで堅持、書込み unified/v1104/ 配下のみ。
