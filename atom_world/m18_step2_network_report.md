# v12 Atomset（atom×atom 関係網）STEP 2 — 網形成 報告

## 自己規律宣言（Code A）
① 過去引用済: STEP1 調査 `m15`（Q1 経路で到達 CID 変わる/Q2 sim_matrix membership・join 可/Q3 source_events だけで rarity_z/Q4 書込禁止先/Q5 event 駆動 atom 網は過去に無し）、`relation_paths_seed{N}`（event_id join）、ingestion≡c_conversion 完全一致（152, 検証済）、sim_matrix coverage 100%、cid_align の robust_z clip（MAD=0 爆発の前例）。
② Taka 逐語（原文）: 「atom×atom 網を育てるまで」「辺を単一スカラーにしない（揺れの幅・whiteout 回避）」「s 内 atom 同士は結ばない」「物理書込ゼロ」「post-process。読むのは frozen、書くのは atom_world/ のみ」「これらは観察を見て Taka が変える前提。Code A は値を勝手に変えない」。
③ 成否判定は Taka（本報告に success/fail/Full/Partial/Failure を置かない、観察事実のみ）。
④ 集約語（効いた/失敗/個性化成立 等）なし。

*作成*: 2026-06-16、Code A。*コード*: `m16_step2_build_atom_network.py`（網形成）、`m17_step2_gate_diagnostics.py`（GATE）。*出力*: `atom_world/`（新規、16M、72 parquet + json）。

---

## 0. 一文（観察事実のみ）

設計書どおり atom×atom 網を 24 seed で形成（cross-CID のみ・rare ゲート・(path×channel×n_core) 層別保持・pulse は common 層に退避）。物理書込ゼロ。GATE 4 項目を観察事実として出す（判定は Taka）。要点の数値: main↔static rank 相関 0.33（main の対の 78% は static 共起に無い）、main↔common 0.96、対あたり層数 中央 12（HHI 0.17）、node top1 9%・pair プロファイル相関 中央 0.59。

---

## 1. 形成結果（24 seed）

| 項目 | 値（seed0 / 範囲） |
|---|---|
| main 辺セル（rare ゲート, 層別） | 23,710 / 19,459–28,873 |
| main の distinct atom 対 | 1,606 / 1,388–1,865 |
| node 数（参加 atom） | 63 / 56–66（全 atom 325 中） |
| common 層セル（pulse, 除去対照） | 10,829 / 8,899–12,652 |
| membership 被覆 src/tgt | 100% / 全 seed 100% |

**辺の作り方（実装＝設計書どおり）**: チャネル {pulse, alpha_formation, beta_formation, ingestion_cc}（ingestion≡c_conversion を dedup→ingestion_cc、c_conversion drop）。rare {ingestion_cc, beta_formation, alpha_formation} のみ main で辺、pulse は common 層。各 gated event の各経路 p の到達 target_cid（relation_paths, event_id join）に対し、source atom(top5, sim 重み) × target atom(top5) の cross product、i==j 除去、無向 canonical、**s 内 atom 同士は結ばない**。各辺を (path×channel×n_core_bin) で層別保持（1 スカラーに潰さない）。

**出力スキーマ**: `atom_edges_seed{N}.parquet` [seed, atom_i, atom_j, path, channel, n_core_bin, weight, n_events, rarity_z_mean] / `atom_nodes_seed{N}` [seed, atom_id, total_weight, n_distinct_partners] / `common_layer_edges_seed{N}` / `coverage_seed{N}.json`。

**knob（Taka 上書き可、勝手に変えない）**: D1 top-k=5・sim 重み / D2 ゲート=type ベース・各辺に rarity_z tag（source_cid 履歴の n_observed_pre robust_z=MAD-DT、ゲートに使わず tag 保持）/ D3 n_core_bin=2/3-4/5+。

**バグ修正（途中）**: rarity_z（MAD-DT）が MAD=0（定数 n_observed_pre）の CID で爆発（-1e9 観測）→ cid_align 同様に clip ±5・MAD floor 1e-3 を入れて再ビルド。weight/n_events/edges/nodes は影響なし、tag 列のみ修正。

---

## 2. GATE 診断（観察事実、判定しない。seed0/1/2 で一貫）

### (1) v106 再描画度（網 vs sim_matrix 静的共起）
- main↔static の rank 相関（Spearman）: **0.33 / 0.33 / 0.33**（seed0/1/2）。
- main の atom 対のうち static 共起（within-CID top-k 同居）に**無い**割合: **78–80%**（main 対数 ~1,600 vs static 対数 ~360）。
- → 観察事実: 網は static 共起と rank 相関が低く、対の大半は static に無い（cross-CID 構築で static に無い対を作っている）。

### (2) 除去対照（main rare vs common pulse vs static）
- main↔common の rank 相関: **0.96 / 0.965 / 0.96**（高い）。
- common↔static: 0.38 / 0.38 / 0.35（low）、main↔static: 0.33（low）。
- path 別 weight 比（seed0）: temporal_coactivation 0.35 / attention_via_salience 0.27 / familiarity 0.17 / integration_alpha 0.12 / integration_beta 0.09。
- → 観察事実: rare ゲートと pulse は**畳んだ対 weight が高相関（0.96）**＝どの atom 対に重みが乗るかはゲートでほぼ変わらない（経路構造が共有のため）。一方 main も common も static とは低相関。timing 由来（temporal）35% / run-wide 静的（attn+fam）44% / integration 21%。
- **未実施（明記）**: 設計書 (b)「temporal を run-wide 扱いで組み直す」除去対照は**まだやっていない**。本報告の除去対照は (a) ゲート OFF 相当（common=pulse との比較）まで。temporal-runwide 版が要るなら次に組む。

### (3) 分布の幅（層を畳むと同形か）
- atom 対あたりの層数（path×channel×n_core）: 中央 **12**、max 41、単層のみ **1.4%**。
- 対あたり層 weight の HHI 中央 **0.17**（1=1層集中、低=層に分散）。
- → 観察事実: 同じ atom 対が多層（中央 12 層）に跨り、weight は1層に集中していない（HHI 0.17）。層を畳むと別パターンが消える構造。

### (4) whiteout（1支配相関に潰れるか）
- node top1 weight share 9%、top5 39%（63 node に分散）。
- 上位 200 対の層プロファイル間 相関: 中央 **0.59**、>0.95 の割合 **6%**。
- → 観察事実: 単一 node/相関が全体を支配せず、対プロファイルは相互に中程度の相関（中央 0.59）で、>0.95（ほぼ同一）は 6%。

---

## 3. やらなかったこと（明示）
CID 投影・low-dim 埋め込み・GATE を超える effect_size/cohens_d・cid pool 確定 は**していない**。除去対照の (b) temporal-runwide 版は未実施（上 §2 明記）。

## 4. 一方向保証（構造的）
- 読む: frozen（source_events / relation_paths / cid_atom_sim_matrix）。書く: `atom_world/` のみ。
- grep: `state.theta / .E[] / .inject( / ledger / phase_sig` への書込 **0 件**（build・GATE 両スクリプト）。atom 世界→CID/物理の書込経路を構造的に持たせていない。

---

*以上 STEP 2 網形成（Code A、2026-06-16）。24 seed で atom×atom 網形成（cross-CID・rare ゲート・層別保持）、物理ゼロ。GATE 観察事実: main↔static 0.33・main の 78% は static に無い対 / main↔common 0.96 / 対あたり層数中央12・HHI0.17 / node top1 9%・pairプロファイル相関中央0.59。除去対照(b)temporal-runwide は未実施。判定は Taka。*
