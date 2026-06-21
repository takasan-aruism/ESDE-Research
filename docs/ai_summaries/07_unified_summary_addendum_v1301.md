# 07 Unified Summary 追補 — v13 child-world（CID→物理 param の子系・統計監査・全検前段）

*作成*: 2026-06-21、Code A
*位置づけ*: `07_unified_summary_addendum_v12_to_v121_roulette.md`（v12.1 一致率ルーレット）に連なる Phase Result。v12 系（Atom 空間の観察）から **別系統の実験 v13 child-world** への移行を区切る。
*性質*: 判定（成功/失敗）でなく構造の整理・確定事実・統計監査の記録。成否判定は Taka。本文に success/fail/crown を置かない。
*この区切りで扱った系譜*: CID の誕生時形態（M_c）を物理 param に写像した縮小系（child-world）を回し、CID 値が系をどう変えるかを観察。**注意**: v13 は Atom 空間（v12）と無関係。V82 エンジンスタックの縮小・param 変調版で、親物理には一切書かない（child engine は in-memory）。

---

## 0. 一文結論

**v13 child-world は「CID の誕生時形態 4 値（M_c）を物理 param に写像した N≈100-350 の子系を独立に回し、CID 値が系をどう変えるか」を観察する系。寿命同期 run（408 child）まで完走したが、本区切りの最大の収穫は実行結果でなく統計監査である ―― (1) 前報告の主要相関 `life→n_labels +0.85` は run 長トートロジー（観測窓を寿命に同期させた副作用）で、交絡を外すと消える、(2) 対照 canon の「std 最小」は run 長を二重固定した非対称対照のアーティファクト、(3) そして `real≒shuffle`（CID 個性が効かないように見えた像）の真因は「比較統計（署名の mean/std）が cid→param→署名の pairing を構造上見ない」ことで、pairing を見る置換検定にすると `K_sync→sync_order`・`plb→link/label_density` は両 ratio で p<0.005 と検出される。母集団・写像の切り分けでは「写像は K_sync を 100%・θ を 84% 伝達＝入口で個性を潰してはいない」「弱いのは N の源均質（B_gen≒n_core）と plb の設計幅 ±15% の 2 点」。次段は (b) 全検（全 CID 値→全物理 param）だが、CID 値は実質 ~5-14 独立軸・物理 param も ~6-7 独立軸ゆえ「10 全て」は冗長で交絡を孕む ―― 選定の合理性を 3AI 合議で詰める判断材料まで揃えた。**

---

## 1. child-world の設計（確定・台帳 §0）

- **素体** = `V82Engine(N=B_gen×10) + V43 物理 + VirtualLayerV9`（= v918/v105 main run と同一エンジンスタックの縮小）。**stress OFF + semantic_pressure OFF**、4 knob 以外は canon 固定。
- **4 knob 写像（誕生時 M_c → 物理 param、サンプラー #30 = 実現値コピーでなく構造同型）**:
  - N ← B_gen×10
  - plb ← `0.007·(1+0.15·tanh(z_{S_avg}))`（±15%）
  - K_sync ← r_core を [0.05,0.30] に正規化
  - 初期θ ← phase_sig（von Mises κ=4）
- **読** = frozen `primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv` の n_core=5（17 CID）。**書** = `unified/v13_childworld/` のみ。child engine は in-memory・親物理非書込（一方向）。
- **4 対照（#33）**: real / shuffle（param 集合を CID 間で並べ替え）/ random（レンジ内一様）/ canon（全 CID 平均で固定）。

## 2. 回した run

| run | 設計 | 規模 | コスト |
|---|---|---|---|
| smoke | 500step=1window | — | スモールスタート |
| long | 全 child 35,000step 固定 | 204 child（17×4×3seed）| Pool24 で 2008s（33.5分）|
| 寿命同期 | run長 = min(35000, life×ratio), ratio∈{1,10}, CID死で停止 | 408 child（×2 ratio）| 完走、`childworld_signatures_lifespan.parquet` |

- 寿命同期 1:1 = run長が寿命そのもの（35k 到達 2/17）。1:10 = ほぼ頭打ち（35k 到達 15/17）。

## 3. 統計監査（本区切りの本体・記録のみ判定なし）

前報告（`cw_run_lifespan_report.md`）の「smoke→long→寿命同期で像が保持」を、データの取り方・比較の仕方の矛盾という観点で再検した結果:

1. **`life→n_labels +0.85`（1:1）は run 長トートロジー**。1:1 では `corr(life, run_len)=1.000` で `corr(run_len, n_labels)=0.849 = corr(life, n_labels)`（小数3桁一致）。交絡を外した 1:10 では **p=0.30・CI[−0.31,+0.71]＝消滅**（1:10 でも run_len の方が主因）。「寿命が cid 構造を生む」の証拠ではない。
2. **canon の「std 最小」はアーティファクト**。run_len の cid 間 std は real/shuffle=12579 に対し **canon=0**（canon だけ life を平均で固定＝param と観測窓を二重固定）。示量署名の std が小さいのは当然で、CID 物理を語らない。
3. **★ real≒shuffle の真因 = 比較統計が pairing 盲目**。shuffle は param 集合を並べ替えるだけなので 17 CID の署名の周辺分布（mean/std）は構造上ほぼ不変（実測 |Δmean|=0.001〜0.02）。mean/std 対照は **どの CID にどの param が紐づくか（pairing）を一切見ない**ため、何があっても real≒shuffle になる。
4. **pairing を見る置換検定（real 17点で null を作り直し）にすると個性は検出される**: `K_sync→sync_order`（1:1 r=.66 / 1:10 r=.77）・`plb→link_density`（.79/.73）・`plb→label_density`（.70/.85）が **両 ratio で perm-p<0.005・CI が 0 を跨がない**。ただしこれらは「knob が物理 param を直接セット→その物理量が動く」＝ **manipulation check** であって CID 創発ではない。`θ→sync_order` は 1:1 のみ有意で脆い。

## 4. 母集団・写像の切り分け（real≒shuffle の原因の同定）

「CID 個性が効かない」と断じる前に、母集団が均質か／写像が入口で潰すかを既存データで切り分け（`cw_investigation_homogeneity_wiring.md`）:

- **§1 母集団**: 均質なのは B_gen のみ（CV=0.025、**B_gen≒n_core の関数**ゆえ n5 内で横並び）。r_core（CV0.364）・phase_sig は十分散る。
- **§2 写像**: K_sync は r_core の個性を**100% 伝達**（設計レンジ全使用）、θ は phase_sig を 84% 伝達（ただし初期値のみで減衰）。**写像が全チャネルで潰すは誤り**。弱いのは N（源 B_gen が均質）と plb（設計幅 ±15% が狭い + tanh 圧縮）の 2 点。
- **結論**: real≒shuffle は (1)母集団均質でも (2)写像が潰すでも (5)原理的に効かないでもなく、**(6) 比較統計が pairing 盲目**が主因。「効くチャネルでは効いている」。

## 5. 全検（全 CID 値→全物理 param）選定合理性の判断材料（3AI 合議の前段）

次の方向 (b) は全検＝全 CID 値を全物理 param に取り込む。だが「10 全て取り込む選定に合理性があるか」を 3AI 合議で詰めるため判断材料を揃えた（`cw_fulltest_selection_material.md`、調査のみ・実行ゼロ）:

- **§1 CID 値の独立次元**: 「10 個の独立値」ではない。**pooled（formed 85）の低次元（PC1=46%）は n_core 階層の産物**（corr(PC1, n_core)=0.91）。n_core 固定 stratum（n2, n=54）の真の独立軸は ~14（PC1=35%・Kaiser14）。**M_c4 値も独立でなく、共線ペアが stratum で変わる**（n2: B_gen↔S_avg=0.82 / n5: B_gen↔r_core=−0.94、頑健。phase_sig のみ一貫独立）。
- **§2 物理 param の独立性**: param は状態変数（L/θ/S/E/R/Z）で束ねられ独立軸は ~6-7。S は 4+ param が押し引きする過剰決定、beta は R↔S を結ぶ結合 knob、Flow が θ→E を結合。
- **§3 規模**: 配線可能 ~25 knob だが **knob 数はコストを増やさない**（cost driver = CID×対照×seed×step）。n_core 跨ぎ母集団 85（2:54/3:3/4:11/5:17）。**「5000 ノード」は親 v918 の N で child 目標でない**（child N=B_gen×10≈110-354）。seed≈12・全跨ぎ・2ratio で ~12h で回る。
- **§4 選定基準案（決めない・たたき台）**: 案A 独立軸代表（交絡最小・ただし n_core ごとに選定し直す要）/ 案B 構造同型拡張＋pairing 検定で相関吸収 / 案C 純全検（冗長・交絡）/ ハイブリッド。

## 6. この区切りの教訓（概念理解.md と同期）

- **肯定/像が保持して見えた結果ほど交絡を疑う**（教訓 414/428 の系）。「像が保持」の実体は大半 run 長効果だった。
- **比較統計が検出したいものを構造上見られるか確認する**（pairing を見ない mean/std で「個性なし」と結論しかけた）。
- **自分の監査自体も懐疑する**: 選定材料の自己再検で 3 点の誤り（pooling 産物の見落とし・M_c4 共線の符号バグ・5000 を親/child 混同）を自力で発見・修正。
- **観察は理解であって次の実装の準備でない**（教訓 433 系。child-world も「回せた」でなく「何が交絡で何が真か」を見るための系）。

---

## 出力ファイル（`unified/v13_childworld/`）
- 設計/配線: `feasibility_check_report.md` / `wiring_probe.py` / `cid_param_wiring_investigation.md` / `physics_cid_ledger.md`（物理演算32・CID値130・配線可能 param 全数台帳）
- run: `cw_run.py`(smoke) / `cw_run_long.py` / `cw_run_lifespan.py` + `childworld_signatures*.parquet` / `*_summary*.json`
- 報告: `cw_run_result_report.md` / `cw_run_long_report.md` / `cw_run_lifespan_report.md`
- 監査/調査: `cw_investigation_homogeneity_wiring.md` / `cw_fulltest_selection_material.md`

*以上 v13 child-world 追補（Code A、2026-06-21、記録のみ・判定なし）。次は 3AI 合議（GPT 監査・Gemini 設計・Web Claude 統合）で全検の選定合理性を確定し、pairing 検定・共通観測窓・対称対照・seed≈12 で設計（Taka 承認後）。*
