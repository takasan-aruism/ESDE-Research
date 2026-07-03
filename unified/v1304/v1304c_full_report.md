# v1304c full 報告 — 揺れの直接測定（固定 probe 法）：前提ずれは標本ゆらぎ床内（事前登録 (b)）

> ⚠️ **訂正あり（2026-07-04・`v1304c_correction.md`）**：本報告の結論「前提ずれは床内(b)・揺れは起きない」は **測定アーティファクト**（primary の参照が M=20 で検出力不足）と判明。参照を 220 標本に広げると **link_density の前提ずれは両 base で立つ**（p≤0.001・進行的）。R_density の床内は ICC=0.02 の**構造的ゼロ**（この lens では原理的に揺れようがない）。ただし「v1304b の効き≠前提ずれ（記憶は weight 軌跡側）」は変わらず（v1304b は lens 非依存・前提ずれは lens 依存）。詳細は訂正書。以下は訂正前の記録として残す。

*作成*: 2026-07-04、Code A。**事前固定 primary で「珍しさの前提が注意由来の組成変化でずれるか」を直接測定。read-only・親物理 hash 検証・書込 `unified/v1304/outputs/` 配下・判定なし #12。判定と読みは Taka。**
*対象指示*: v1304c rev2（Web Claude・2026-07-03・固定 probe 法・primary＝premise_drift_fb − premise_drift_nofb・予登録読み (a)立つ/(b)立たない）。
*成果物*: `v1304c.py`（機構は v1304b 関数 import で完全同一）+ `outputs/v1304c_full_{pop,cidsalience,weightchange,drift,rankswaps,mechcorr,tests,summary}.parquet/json`。
*規模*: 2 lens × 2 base × R12 × T8 × 3世界 × M20 ＝**23,040 child**・**1264秒**（24並列）・parent hash 前後不変・ログ欠損なし（pop 23040＝期待）。

---

## 0. 結論（先に・事前登録どおり読む）

- **primary は立たない**：`premise_drift_fb − premise_drift_nofb` は **4条件（2 lens×2 base）すべて有意でない**（p=0.35〜0.79・符号一貫性 0.42〜0.58＝chance 近傍・all_series_pos すべて False）。premise_drift_fb ≈ premise_drift_nofb（両者 0.15〜0.17）。
- ＝**事前登録の読み (b)：珍しさの前提ずれは静的組成の標本ゆらぎ床内**。落胆材料でなく**条件の特定**（指示 §2 の予登録どおり）：**v1304b の効き（対応が weight 軌跡を方向づけた・持続性非依存）は「珍しさの母集団が注意でずれる」経路が担っているのではない**。
- 帰結（v1304b との接続）：v1304b で「持続性ゼロでも効く＝記憶は weight 軌跡側に宿り得る」とした非自明の**本体は前提ずれではない**。記憶は **weight 軌跡（履歴・経路）そのもの**に宿り、珍しさの物差し（母集団相対性）の移動は標本ノイズと区別できない。＝**動的な統計＝「時間で前提がずれる」は、この計器・この規模では実証されない**（言える上限を守り「動的な統計が成立」とは言わない・確定名は Taka）。

## 1. primary（事前固定・premise_drift_fb − premise_drift_nofb・t=1..T-1 mean・R=12 系列 paired）

| lens | base | drift_fb | drift_nofb | **diff(primary)** | t | p_raw | 符号一貫 | 全系列>0 |
|---|---|---|---|---|---|---|---|---|
| link_density | 0 | 0.170 | 0.160 | +0.0098 | 0.98 | 0.35 | 0.583 | False |
| link_density | 1 | 0.169 | 0.172 | −0.0022 | −0.27 | 0.79 | 0.583 | False |
| R_density | 0 | 0.159 | 0.152 | +0.0067 | 0.75 | 0.47 | 0.417 | False |
| R_density | 1 | 0.164 | 0.159 | +0.0053 | 0.47 | 0.65 | 0.417 | False |

- 全条件で feedback の前提ずれが no_feedback（w0 固定・M=20 標本ゆらぎ）の床を有意に超えない。符号は3/4で正だが微小（≤0.01）かつ系列内で一貫しない（chance 近傍）。**base 間再現もなし**（link_density は base0 +0.010 / base1 −0.002 で符号反転）。
- 対比：v1304b の weight 軌跡 primary は両 base で 12/12 系列正・p≤1e-4 で明瞭に立った。**同じループで、weight 軌跡は方向づくが、珍しさの前提は床内**＝効きの所在が weight 軌跡側であることの傍証。

## 2. secondary（各成分を別々に・合成しない #11・すべて primary と整合）

### 2.1 地形（feedback 子集団 lens 値の round 推移・median）
- link_density base0：median 0.808→0.847（t6）→0.827（t7）＝**上昇**（v1304b 世界応答と同じ・高 link_density cid への集中の機械的帰結＝plb 写像の自己確認）。
- R_density base0：median 0.153→0.145＝**ほぼ不動**。
- ＝link_density では地形の平均は動くが、**その移動は前提ずれ（rarity 物差しの床超え移動）を生まない**（mean-shift は分布形を保てば probe の珍しさをさほど動かさない）。R_density は地形自体動かない。

### 2.2 rank 入れ替わり（連続 round cid_salience Spearman・fb vs nofb）
| lens | base | feedback | no_feedback |
|---|---|---|---|
| link_density | 0 | 0.136 | **0.223** |
| link_density | 1 | 0.093 | 0.135 |
| R_density | 0 | 0.029 | 0.069 |
| R_density | 1 | 0.121 | 0.059 |
- cid_salience の round 間順位相関は**全条件で低い**（0.03〜0.22）＝salience 順位は round ごとに大きく入れ替わる（v1304b の低持続性と整合）。**feedback が no_feedback より順位を安定させるわけでもない**（多くで nofb ≥ fb）。

### 2.3 機構 targeted（corr(引かれ回数 mult, cid_salience)・GPT 同梱・局所相関の単独解釈をしない）
- 全条件で **near-zero**（feedback: link +0.038/+0.062・R_density +0.029/+0.008／no_feedback も ±0.02 前後）。multiplicity（引かれ回数）は cid_salience をほぼ説明しない。v1304b で link +0.115 と報告された局所相関は本 run（multiplicity 保存）では +0.04〜0.06 と弱い。**単独解釈しない**（指示どおり 1–3 と並べて読む）。

### 2.4 循環の閉じ（descriptive・因果候補表現・断定しない）
- corr(weight_L1_change, drift_fb) は **near-zero/符号混在**（link base0 −0.19・base1 +0.05・R_density base0 +0.09・base1 −0.06）。「前提ずれが注意（weight 変化）に戻る」の相関的痕跡は**見えない**（前提ずれ自体が床内なので当然だが記録）。

## 3. 実装健全性・守った線

| 項目 | 結果 |
|---|---|
| 機構 v1304b 同一（関数 import・言い換え再実装なし） | OK（[[feedback_no_reworded_reimplementation]]） |
| parent physics hash 前後不変 | **OK**（read-only 実証） |
| 書込 v1304 配下・provenance・ログ欠損なし（pop 23040＝期待） | OK |
| rev2 5点固定（smoothed rarity・同一 probe・単一基準・t=0 除外・median 保存） | OK（smoke 検算 self-drift=0 済） |
| 合成しない（#11・4 secondary を別々・lens 別ループ） | OK |
| 単一指標で分類しない | OK（primary＋4 secondary を並置・判定は Taka） |

## 4. 走らせていないもの・次段（Code A は判定しない）

- **未実施**：T=12 の飽和確認（指示 §4 optional・drift が T8 で飽和/未飽和かは地形推移から未判断）・複数親 seed（依然 v1303 seed0）・「効きが weight 軌跡側に宿る」の直接検証（本 run は前提ずれの否定までで、軌跡側の機構同定はしていない）。
- **次段（承認後・Taka/Web Claude）**：(a) v1304b の効きの所在（weight 軌跡の履歴・経路依存）を直接測る計器の設計、(b) 前提ずれが立たない条件の意味（系の多様性 M・T・親 seed 依存）、(c) T 延長で飽和確認。**full はここで停止**。

## 5. 一文サマリ

v1304c full 報告（揺れの直接測定・固定 probe 法・判定なし #12）── 機構は v1304b 関数 import で完全同一に保ち、各系列 round-0 の feedback 子 M体 lens 値を固定 probe とし各 round 子集団に対し珍しさを smoothed tail rarity（rev2 固定）で再計算して前提ずれ `premise_drift = mean_probe|rarity(probe|pop_t)−rarity_0|` を測り、事前固定 primary `mean_{t≥1}(drift_fb − drift_nofb)` を R12 系列 paired 1標本t で閉じたところ **4条件(2lens×2base)すべて有意でない（p0.35〜0.79・符号一貫0.42〜0.58 chance近傍・全系列正でない・base 間再現なし・drift_fb≈drift_nofb 0.15〜0.17）＝事前登録の読み (b)＝珍しさの前提ずれは静的組成の標本ゆらぎ床内**、secondary も整合＝地形は link_density median 上昇（0.808→0.847・plb 集中の機械的帰結）だが前提ずれを生まず R_density は地形不動・rank 入れ替わりは全条件低く（0.03〜0.22）feedback が no_feedback より安定もせず・機構 targeted corr(引かれ回数,salience) は near-zero（±0.06・v1304b の +0.115 は multiplicity 保存で弱化）・循環の閉じ corr(weight変化,drift) は near-zero 符号混在、＝**v1304b の効き（対応が weight 軌跡を方向づけ・持続性非依存）は「珍しさの母集団が注意でずれる」経路が担うのではなく記憶は weight 軌跡（履歴・経路）側に宿る**（同じループで weight 軌跡 primary は 12/12 系列正 p≤1e-4 だが前提ずれは床内という対比が傍証）、23,040 child 1264秒・parent hash 前後不変（read-only 実証）・rev2 5点固定（smoke self-drift=0 検算済）・#11 合成なしで 4 secondary 別々、言える上限を守り「動的な統計が成立」と言わず前提ずれ否定を条件特定の発見として記録、未実施＝T12 飽和確認・複数親 seed・軌跡側機構の直接同定で承認後 next へ自動前進せず停止、効きの所在（weight 軌跡の経路依存）計器設計・前提ずれ不成立の条件の意味・T 延長は Taka/Web Claude。
