# v1304b 別 lens 再現 報告 — 自己確認外し（lens=R_density で primary 再現）

*作成*: 2026-07-03、Code A。**機構・統計・規模は full と完全同一・lens だけ `R_density` に差し替え（#5）。read-only・親物理 hash 検証・書込 `unified/v1304/outputs/` 配下・判定なし #12。判定と読みは Taka。**
*対象指示*: v1304b 別 lens 再現（Web Claude・2026-07-03・自己確認外し・R_density・解釈分岐 (a)/(b) 事前固定・§3 持続性診断必須）。
*成果物*: `v1304b_lens.py`（full の関数を import＝機構同一を保証）+ `outputs/v1304b_lens_R_density_{primary,tests,coverage,cidsalience,persistence,summary}.parquet/json`。
*規模*: 3M×T8×(R12+R12)＝**11,520 child**・**639秒**（24並列）。spread ガード通過（R_density std=0.045・20/20 子ユニーク＝珍しさ well-defined）。

---

## 0. 結論（先に・成果表現は full と同上限）

- **primary は R_density でも立った（レプリカ床超え）**：g=1 両 base で `(D_fb − D_null)` 正・**R=12 系列すべて（12/12）正・符号一貫性 1.0**（base0: diff 0.068・t=6.87・p=3e-5／base1: diff 0.121・t=3.73・p=0.003）。
- **事前固定の解釈分岐は (a)**：対応の効きは lens 非依存＝**ループの機構的性質**。**link_density の自己確認懸念（plb 写像の機械的濃淡）は外れた**。
- ただし2つ、Taka の読みに要る非自明：
  1. **効果量は link_density より小さい**（R_density diff 0.068/0.121 vs link_density 0.200/0.162）。base1 は最小系列 diff 0.0028＝薄いが正。
  2. **§3 診断が事前予想と食い違う**：R_density の per-cid salience 持続性は低い（split-half corr **0.26 / −0.01**）のに primary は立つ。指示 §3 の予想「効きは持続性に乗る」に反し、**base1 は持続性ほぼ 0 でも床超え**（diff 0.121）。＝**対応の効きは per-cid の持続的個体差を必須としない**（機構は round 内動態からも立つ）。持続性は効果量に効く可能性はあるが符号/存在には不要。

## 1. primary（lens=R_density・full と同一機構/統計・事前固定1本）

| lens | base | R | D_fb | D_null | **diff(=primary)** | t | p_raw | 符号一貫 | 全12系列>0 | min系列 |
|---|---|---|---|---|---|---|---|---|---|---|
| **R_density** | 0 | 12 | 0.955 | 0.887 | **0.068** | **6.87** | **3e-5** | **1.0** | **True** | 0.022 |
| **R_density** | 1 | 12 | 1.005 | 0.884 | **0.121** | **3.73** | **0.003** | **1.0** | **True** | 0.003 |
| （参考）link_density | 0 | 12 | 1.067 | 0.868 | 0.200 | 7.01 | 2e-5 | 1.0 | True | 0.041 |
| （参考）link_density | 1 | 12 | 1.058 | 0.896 | 0.162 | 5.86 | 1e-4 | 1.0 | True | 0.041 |

- D_null（対応なし発散床）は lens に依らず 0.88–0.90 でほぼ一定。R_density は D_fb がその上に薄く乗る（差 0.068–0.121）。**床超えの向きは全系列で保存**。
- secondary entropy 差も正（base0 mean 0.31・t=4.09／base1 0.76・t=3.69）＝feedback はレプリカより強く集中（lens 非依存）。独立 shuffle L1(fb,indep)=1.46（link_density の 1.51–1.56 とほぼ同水準）。

## 2. §3 診断 — per-cid salience 持続性（同一 feedback draws 上で両 lens・公平比較）

前半 round（t<4）vs 後半 round（t≥4）の cid_salience を cid 跨ぎで Pearson 相関（高い＝持続的個体差）。

| lens | base0 split-half corr | base1 split-half corr |
|---|---|---|
| **link_density** | **0.702** | **0.513** |
| **R_density** | **0.260** | **−0.012** |

- **link_density は per-cid 持続性が高い**（0.70/0.51）＝plb 固定→再現的な個体差。full の効きはこれに乗っていた（指示の予想通り）。
- **R_density は持続性が低い**（0.26/−0.01）。plb から一段遠く、率量ゆえ round ごとの子集団構成に強く依存し per-cid identity が薄い。
- **にもかかわらず primary は立つ**＝指示 §3 の予想「効きは持続性に乗る」を**部分的に否定**する非自明。持続性が高い方（link_density）が効果量も大きい（0.200 vs 0.068 @base0）点は予想と整合するが、**base1 は持続性ほぼ 0 で効果量はむしろ base0 より大きい**（0.121 vs 0.068）＝持続性と効果量は単調でない。**数字を並べて Taka に委ねる**（単一指標で読まない [[feedback_no_single_index_classification]]）。

## 3. 実装健全性・守った線（full から完全継続）

| 項目 | 結果 |
|---|---|
| 機構同一（full の関数を import・言い換え再実装なし） | OK（[[feedback_no_reworded_reimplementation]]） |
| lens 以外すべて不変（composition/両側−log10/cid単位平均/round正規化/α/eps floor/K10/primary/R12/T8/M20/base0,1/g1/now_theta init） | OK |
| parent physics hash 前後不変 | **OK**（read-only 実証） |
| 書込 v1304 配下のみ・provenance・round0 support 固定（cid_hash `a0ea…` full と一致） | OK |
| spread ガード（R_density 子間 spread 非潰れを最初の系列で確認してから全系列） | OK（std 0.045・unique 20/20） |
| レプリカ null は子ゼロ追加の算術 | OK |

## 4. 走らせていないもの・次段（Code A は判定しない）

- **未実施**：sync_order 第二ループ（θ側・plb 最遠）＝budget/次段送り（指示 §1 の通り optional）。複数親 seed（親 profile は依然 v1303 seed0 のみ）。持続性と効果量の関係の統計モデル化（本報告は数字併記まで）。
- **次段（承認後・Taka/Web Claude）**：(a) sync_order で三点目の再現、(b) 複数親 seed で床超えの一般化、(c) 「持続性を必須としない床超え」の機構解釈（round 内動態がどう対応を運ぶか）・揺れ・回数増・多 eye・Atom 接続。**別 lens 再現はここで停止**。

## 5. 一文サマリ

v1304b 別 lens 再現（自己確認外し・機構/統計/規模 full 同一・lens だけ R_density・判定なし #12）── link_density の自己確認リスク（plb 写像の機械的濃淡）を外すため率量 R_density で同一 primary（D_fb−D_null・R12 系列 paired 1標本 t・事前固定・K10 レプリカ null・base0/1・g1）を再現したところ **両 base で立った（レプリカ床超え・全12/12系列正・符号一貫 1.0・base0 diff0.068 t6.87 p3e-5／base1 diff0.121 t3.73 p0.003）＝事前固定の解釈分岐 (a)＝対応の効きは lens 非依存でループの機構的性質・link_density 自己確認懸念は外れた**、ただし効果量は link_density（0.200/0.162）より小さく（0.068/0.121）、§3 診断＝per-cid salience 持続性（前半vs後半 split相関・同一 feedback draws 上・両lens公平比較）が link_density 高い（0.70/0.51）R_density 低い（0.26/−0.01）で **R_density は持続性ほぼ 0 でも primary が立つ＝指示 §3 予想「効きは持続性に乗る」を部分否定（対応の効きは per-cid 持続的個体差を必須としない・base1 は持続性0で効果量むしろ大＝持続性と効果量は単調でない）**、11,520 child 639秒 24並列・spread ガード通過（R_density std0.045 unique20/20）・親物理 hash 前後不変（read-only 実証）・機構は full の関数 import で完全同一・provenance/round0 support/レプリカ null 子ゼロ追加すべて継続、成果表現は full と同上限（対応が weight 軌跡を方向づけた＝レプリカ床超えまで・学習/自律と言わない）、未実施＝sync_order 第二ループ（optional 次段送り）・複数親 seed で承認後 next へ自動前進せず停止、三点目再現・一般化・持続性非依存の機構解釈は Taka/Web Claude。
