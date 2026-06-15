# v12 Atomset STEP 3 — 時間局所 membership 版 atom×atom 網 報告

## 自己規律宣言（Code A）
① 過去引用済: STEP2 `m16`(辺ロジック)/`m18`(main↔common 0.96=出来事が網を方向づけてない)、STEP3 土台調査 `m19`(時間局所 4 粒度在/rank1のみ/top5は再計算可)、STEP3 cid_align で確認の `atom_profiles_cache.npz` slot_keys 整合（アルファベット順 v1103 は使わない=軸 scramble 回避）、`build_step10_table`/`build_step10_cid_vector`。
② Taka 逐語（原文）: 「全部読んで変える系なら何やったって変化しないに決まってる。時間の概念をいれるならそれが Step なり Window なり、何 Step にするか」「変えるのは membership の時間性だけ」「Atom が接続されたことが意味になっていない／センターはなぜそれを受け取ったのか」「全部やってみて。他は任せる」「（0.96 が）下がること自体は目的でない＝ランダム化でも下がる、対照との差が要る」。
③ 成否判定は Taka（success/fail/Full/Partial/Failure を置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-16、Code A。*コード*: `m20_step3_build_timelocal_network.py`、`m21_step3_timelocal_gate.py`。*出力*: `atom_world/timelocal/`（178M、24 seed）。

---

## 0. 一文（観察事実）

membership を「run 終わり sim_matrix（一点）」から「t 時点の time-local top-5（step10 で再計算）」に替え、辺ロジックは STEP 2 不変・window 列追加で 24 seed 形成（物理ゼロ）。GATE 観察（seed0/1/2 一貫）: 時間局所網は STEP2 静的版と **rank 相関 -0.31・新規対 67-71%・distinct 対 +49%**（substantially 別物）、一方 rare↔common は 0.96→**~0.90**（modest 低下）、連続窓で top 辺の 2/3 が入れ替わり（Jaccard 0.33）、**~21% の対が 1 窓に集中（event 的 spike）**・辺は run 全体で誕生、whiteout なし。判定は Taka。

---

## 1. 実装（変えたのは membership の時間性だけ）

- **membership**: run 終わり sim_matrix → **t 時点の time-local top-5**。step10（10step）粒度の `build_step10_table` を `build_step10_cid_vector` で t 行ごとに 48 次元再計算 → `atom_profiles_cache`(slot_keys 整合) と cosine → top-5（sim 重み）。source_event(s,t) は s と target c の **t 時点（直近 grid, backward asof）** membership を引く。
- **辺ロジック（STEP2 不変）**: cross-CID のみ・rare ゲート{ingestion_cc,beta,alpha}・(path×channel×n_core_bin) 層別・i≠j・無向 canonical・pulse は common 層。
- **追加**: `window` 列（event の t//500）＝「いつ どの atom がつながったか」。
- 24 seed: main ~20万 cell（窓×層）/ distinct 対 ~2,400 / 窓数 ~46 / common ~32万 cell / membership grid ~36万行。1 seed 12-20s。

**注（granularity 判断）**: Taka「何 Step にするか」を委任されたので step10（最細・全列在・10-step 志向）を採用。粒度を window 等に替えれば結果は変わりうる（未実施）。

## 2. GATE 観察（判定しない。STEP2 静的との対比。seed0/1/2）

| 項目 | seed0 | seed1 | seed2 | STEP2 静的 |
|---|---|---|---|---|
| **A. rare↔common** | 0.925 | 0.902 | 0.877 | 0.96 |
| **B. tl↔STEP2静的 rank相関** | **-0.313** | -0.248 | -0.314 | — |
| B. tl 新規対割合 | 71% | 67% | 67% | — |
| B. distinct 対数 | 2,395 | 2,473 | 2,216 | 1,606/1,724/1,579 |
| **C. 連続窓 pair相関 中央** | 0.769 | 0.771 | 0.750 | （窓なし） |
| C. top20 連続窓 Jaccard | 0.333 | 0.379 | 0.333 | — |
| **D. pair 最大窓 share 中央** | 0.416 | 0.400 | 0.418 | — |
| D. 1窓集中(>0.8)割合 | 23% | 20% | 21% | — |
| D. 辺誕生窓数 | 47 | 43 | 45 | — |
| **E. tl↔sim_matrix共起** | -0.227 | -0.207 | -0.226 | (STEP2: +0.33) |
| E. 層数中央 | 29 | 28 | 34 | (STEP2: 12) |
| E. node数 / top1 / top5 | 86/13%/38% | 84/13%/40% | 78/14%/41% | 63/9%/39% |

### 観察事実（各項、判定しない）
- **A（0.96 下がるか）**: 0.96 → ~0.90。下がったが modest（Taka 留保どおり「下がること自体は目的でない、対照差が要る」＝下げ幅だけでは何も言えない）。time-local 内でも rare と pulse は collapsed 対 weight が高相関（共有の経路構造＋membership 時間が効く先が同じため）。
- **B（静的版との差）**: time-local 網は STEP2 静的版と **rank 相関が負（-0.31）**、対の **67-71% は静的に無い新規**、distinct 対 +49%。＝membership 時間局所化で**結ぶ atom 対の構成が大きく変わった**（静的では高 weight だった対が time-local では低位、の傾向）。
- **C（時間で動くか）**: 連続窓の bulk pair weight は中程度に類似（0.75-0.77）だが、**top20 辺は連続窓で 2/3 入れ替わる（Jaccard 0.33）**＝上位の辺は時間で動く。窓ごとに違う網。
- **D（センター拾う基準=Taka 留保）**: 対の weight 時系列で **~21% が 1 窓に集中（>0.8、event 的 spike）**、辺の誕生は特定窓に偏らず run 全体（誕生窓 43-47, top1 9-10%）。＝「ある窓で急に繋がる」spike 構造は**在る**（Center の拾う候補基準になりうる構造は観察される）。「それが意味か」は Taka 領域、本報告は構造の有無のみ。
- **E（再描画/whiteout/幅）**: tl は sim_matrix 静的共起と**負相関（-0.22）**＝静的共起の再描画ではない。層数中央 29（STEP2 12 より厚い、窓追加分）。node 78-86 に分散、top1 13-14%＝whiteout なし。

## 3. 正直な留保（観察、判定でない）
- **B/E の負相関**: time-local は早期/過渡の窓（数が多い）の membership を多く含む。run 終わり sim_matrix（成熟・安定）と負相関なのは、**過渡期の未成熟 membership が time-local を支配している**可能性がある（＝「時間で動く」が「過渡ノイズ」の可能性と区別できていない）。Taka「対照との差が要る」に照らすと、対照（例: membership を窓内シャッフル／別 seed）との差を見るまで「出来事が網を動かした」とは言えない。本 STEP では対照未実施。
- A の 0.90 も同様、ランダム化対照なしでは下げ幅の意味は確定しない。

## 4. やらなかったこと（明示）
CID 投影・low-dim 埋め込み・GATE を超える effect_size・cid pool 確定・Taka 案（326次元一致率の時間変動 直接ルート）・対照（membership シャッフル/別 seed）・粒度スイープ（window 等）は**していない**。

## 5. 一方向保証
読む=frozen（v105 diag logs / relation_paths / source_events / atom_profiles_cache）、書く=`atom_world/timelocal/` のみ。grep: physics/inject/ledger 書込 **0 件**（build・GATE 両方）。

**出力の扱い**: timelocal 全体 178M。repo 肥大回避のため code+gate+coverage+report+**seed0 サンプル parquet** のみ commit、seed1-23 はローカル+再生成可（`m20` を引数なしで再 run、~6分）。全 seed が要れば push します。

---

*以上 STEP 3 time-local（Code A、2026-06-16）。membership 時間性だけ替え（step10 top-5 再計算）、辺ロジック不変+window列。GATE: tl は STEP2静的と rank相関 -0.31・新規対 71%・distinct +49%（別物）、rare↔common 0.96→~0.90（modest）、top辺は窓で 2/3 入替、~21% 対が1窓 spike、whiteout なし、tl↔静的共起 負。留保: 過渡 membership 支配の可能性・対照未実施で「出来事が動かした」は未確定。判定は Taka。*
