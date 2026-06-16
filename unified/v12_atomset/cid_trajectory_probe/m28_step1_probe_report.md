# Taka 案 課題#1 — 一致率の時間更新で「何が拾えるか」(dump のみ) 報告

## 自己規律宣言（Code A）
① 過去引用済: **#30（接地・Ghost 二役＝死後もスロットが観測者/食料の二役、死は大変化のはず／誕生・Q奪取・Integration は個性的イベントのはず）**、m19（4 粒度の per-(cid,t) rank_1_atom + rank_1_sim 在: event~50step / pulse / step10 10step / window 500step）、source_events の birth_step/host_lost_step/reaped_step/final_state（step 単位の死判定）。
② Taka 逐語（原文）: 「ESDE Atom にどんな多様性が生まれ、センターが拾えるか」「誕生/Q奪取/Integration は個性的イベントのはず」「閾値を決めない・網を組まない・センター接続しない・CID投影しない」「大きく見る/安く見るの両方を Taka が見られる形」「統計を出すが、統計が目的でない」。
③ 成否判定は Taka（success/fail/Full/Partial/Failure 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-16、Code A。*コード*: `m27_step1_trajectory_probe.py`。*出力*: `cid_trajectory_probe/`（probe_summary.json + top_jumps_{grain}.parquet）。閾値・網・センター接続・CID 投影は**していない**。

---

## 0. コスト実測（「自然閾値はコスト高」への事前情報）

| 粒度 | n_rows(24seed) | 所要 |
|---|---|---|
| event(~50step) | 440,666 | 0.9s |
| pulse | 359,110 | 0.8s |
| step10(10step) | 1,796,001 | 2.2s |
| window(500step) | 31,482 | 0.3s |
| **計** | — | **~4s** |

→ 観察事実: rank_1（1位 atom + sim）での 4 粒度全 CID dump は**安い（計 ~4s）**。（フル 326 次元一致率は本 STEP では出していない＝次。）

## 1. Δsim 分布（閾値を引かず分位で）

| 粒度 | alive Δsim \|mean\| | p50 | p95 | p99 | atom 切替率 alive |
|---|---|---|---|---|---|
| event | 0.0144 | -0.00 | 0.043 | 0.072 | 16.1% |
| pulse | 0.0160 | -0.00 | 0.046 | 0.070 | 25.5% |
| step10 | 0.0039 | -0.0001 | 0.014 | 0.050 | 4.7% |
| window | 0.0189 | -0.0003 | 0.047 | 0.084 | 33.7% |

→ 観察事実: 粒度が細かいほど Δsim は小さい（step10 \|mean\| 0.004 < window 0.019）、atom 切替率も細かいほど低い（step10 4.7% < window 33.7%）。「大きい」の線は引いていない（分布のまま）。

## 2. Ghost 分離（#30、必須）

| 粒度 | ghost 行数 | ghost Δsim \|mean\| | ghost 切替率 | alive→ghost 遷移 Δsim \|mean\| (n) |
|---|---|---|---|---|
| step10 | 15,279 | 0.0020 | 0.57% | 0.0062 (4,429) |
| event/pulse/window | 0 | — | — | — |

→ 観察事実: **ghost 行を捉えたのは step10 のみ**（10step 固定 grid が死後も続くため。event/pulse/window は死後に行が無い＝event 駆動 or grid が死で終了）。step10 で **ghost は alive より平ら**（Δsim \|mean\| 0.0020 < alive 0.0039、切替率 0.57% < 4.7%）＝#30 の「Ghost-平ら行」が dump で見える。**alive→ghost 遷移の Δsim（0.0062）は steady alive（0.0039）より大きい**＝#30 の「死は大変化」が遷移行で見える。

## 3. 大跳ね × 演算イベント対応（#30 の核、判定でなく対応 dump）

各粒度の |Δsim| 上位 300 に居た source_events 種別（複数可）:

| 粒度 | 上位300 の演算イベント内訳 | ghost割合 | birth/death割合 |
|---|---|---|---|
| event | pulse 300, alpha_birth 4, beta_birth 4 | 0 | 0 |
| pulse | pulse 300, alpha_formation 73, beta_formation 66 | 0 | 0 |
| step10 | pulse 289, alpha 15, beta 14, none 11 | 0.3% | 0.3% |
| window | pulse 300, alpha 38, beta 36 | 0 | 0 |

→ 観察事実: **大跳ね上位は全粒度で pulse がほぼ全行に同居**、alpha/beta_formation は同居するが少数、**ingestion(Q奪取)・誕生・死はほぼ上位に出ない**。
→ **重要な留保（base-rate）**: pulse は event 総数の最多（24seed 平均 pulse 12,530 vs alpha 1,067 / beta 478 / ingestion 155）。よって上位への pulse 同居は頻度効果でも起こりうる＝「pulse が大跳ねを作る」とは言えない。rate 正規化（イベント種別あたりの大跳ね率）は**本 STEP では出していない**（やらないこと）。#30 の「誕生/Q奪取/Integration が大跳ね」は raw 対応では上位に目立たない、という観察のみ（判定でない）。

## 4. 生死層化（#30、ハードに焼かない）

| 粒度 | Δsim \|mean\| 生死含む | 生死除く |
|---|---|---|
| event | 0.0144 | 0.0144 |
| pulse | 0.0160 | 0.0160 |
| step10 | 0.0039 | 0.0039 |
| window | 0.0189 | 0.0189 |

→ 観察事実: 誕生行は Δsim を持たない（最初の行＝前点なし）ため自動的に除外され、死行は少数で、含む/除くで \|mean\| はほぼ不変。大きく見ても安く見ても分布の中心は動かない（分布の裾＝top_jumps_*.parquet は別途）。

## 5. やらなかったこと（明示）
閾値の決定・「大きい変化」の確定・網形成・atom×atom 拡張・センター接続・CID 投影・effect_size・rate 正規化・フル 326 次元一致率は**していない**。すべて課題#1 の次。

## 6. 一方向保証
読む=frozen（v106 trajectory / source_events）、書く=`cid_trajectory_probe/` のみ。grep: physics/inject/ledger 書込 **0 件**。

---

*以上 課題#1（Code A、2026-06-16）。コスト: rank_1 4粒度全CID は ~4s で安い。Δsim 分布は細粒度ほど小(step10 0.004〜window 0.019)、切替率も(4.7%〜33.7%)。Ghost(#30): step10 のみ ghost 捕捉、ghost は alive より平ら(0.002 vs 0.004)、遷移は大(0.006)。大跳ね上位300: pulse がほぼ全行同居だが pulse 最頻の base-rate 留保あり(rate 正規化は未)、誕生/Q奪取/死は上位に目立たず。生死層化は \|mean\| ほぼ不変。閾値・判定・網は出さない。次は Web Claude/Taka。*
