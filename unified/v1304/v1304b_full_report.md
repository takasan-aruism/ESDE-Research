# v1304b full 報告 — feedback loop 本番（レプリカ null で primary を閉じる）

*作成*: 2026-07-03、Code A。**事前固定した1本の primary で「対応が weight 軌跡を方向づけたか」を統計的に決める本番。read-only・親物理 hash 前後検証・書込 `unified/v1304/outputs/` 配下・判定なし #12。判定と読みは Taka。**
*対象指示*: v1304b full（Web Claude・2026-07-03・レプリカ null・K=10・base0/1・g=1 primary / g=0.5 参考）。
*成果物*: `v1304b_full.py` + `outputs/v1304b_full_{primary,tests,salience,coverage,childsig,summary}.parquet/json`。
*規模*: 3M×T8×(R12+R12+R5)＝**13,920 child**・**779秒**（24並列・fork 決定性検証済＝直列と一致）。

---

## 0. 結論（先に・成果表現は指示 §4 の上限を厳守）

- **primary が立った（レプリカ床超え）**：事前固定 `(D_fb − D_null)` は g=1 の **両 base で正・R=12 系列すべて（12/12）正・符号一貫性 1.0**（base0: mean 0.200・t=7.01・p=2e-5／base1: mean 0.162・t=5.86・p=1e-4）。＝**feedback（正しい対応）の weight 軌跡が shuffle から離れる量が、対応なし同士の発散床（レプリカ null）を超える**。
- 言える上限（指示 §4）：**「対応（どの cid の子が珍しかったか）が weight 軌跡を方向づけた＝レプリカ床超え」まで**。「センターが学習した／自律注意が成立」とは**言わない**（L型）。
- 条件付き明記：**親 profile は v1303 final seed0 のみ**・**single lens=link_density**（自己確認リスクあり §3.3）・base は engine 系列（親 seed でない）。＝「親 seed0 に条件付けた結論」。main（複数親 seed）・別 lens は未実施（§4）。
- g=0.5 参考：同方向で弱い（diff 0.091・t=3.16・p=0.034・符号一貫 1.0）＝gain を下げても床超えの向きは保つ（判定に使わない）。

## 1. primary（事前固定1本・結果を見て指標/検定を変えていない）

`D_fb = mean_k mean_round L1(w_feedback, w_shuffle_k)`／`D_null = mean_{i<j} mean_round L1(w_shuffle_i, w_shuffle_j)`／系列ごと paired `D_fb − D_null` を R 系列 1標本 t。

| g | base | R | role | D_fb | D_null | **diff(=primary)** | t | p_raw | 符号一貫 | 全系列>0 |
|---|---|---|---|---|---|---|---|---|---|---|
| **1.0** | **0** | 12 | **primary** | 1.067 | 0.868 | **0.200** | **7.01** | **2e-5** | **1.0** | **12/12** |
| **1.0** | **1** | 12 | **primary** | 1.058 | 0.896 | **0.162** | **5.86** | **1e-4** | **1.0** | **12/12** |
| 0.5 | 0 | 5 | 参考 | 0.666 | 0.574 | 0.091 | 3.16 | 0.034 | 1.0 | 5/5 |

- **床超えの本体**：D_null（対応なし同士のランダムウォーク発散床）自体が 0.87–0.90 と大きい＝レプリカ同士も乗法更新で離れる。それでも **D_fb がさらに上**（1.06–1.07）で、差は最小系列でも正（base0 min 0.041・base1 min 0.041）。＝集中が「更新則が入れば何でも動く」だけなら D_fb=D_null になるはずだが、対応を保つと余分に離れる。
- **base0/1 再現**：符号・有意性ともに再現（diff 0.200 / 0.162）。base 間で効果量はやや異なるが向きは不変。

## 2. secondary（primary と混ぜない・descriptive 中心）

### 2.1 entropy 差（対応が集中を速めるか）
最終 round の `H(shuffle 平均) − H(feedback)`：g1 base0 mean **0.837**（t=9.81・p<1e-5）・base1 **0.960**（t=8.54）＝**feedback は shuffle レプリカより強く weight を集中**（entropy が低い）。primary と整合するが別量（判定は primary のみ）。

### 2.2 独立 composition shuffle（別の問い＝閉ループ同士の世界分岐）
自群 weight で M 体引く shuffle を1系統追加。最終 round の `L1(w_feedback, w_indep)` mean＝**1.51（base0）/ 1.56（base1）**＝feedback と独立閉ループは相乗り shuffle よりさらに離れた weight に至る。**相乗り null（primary）と別物**：これは「対応破壊」でなく「別の世界を歩んだ」差＝世界分岐の descriptive（判定は Taka・§4 次段）。

### 2.3 世界応答（注意が世界の組成を変える微候・descriptive）
feedback 子集団の link_density は round を追って上昇（t0 0.806→t6 0.830→t7 0.815）、indep_shuffle は下降（0.805→0.786）、no_feedback は横ばい（~0.80）。coverage は集中に伴い drawn_distinct 16→9・undrawn_rate 0.64→0.80。
> **自己確認リスク明記（指示 §4 / rev2 §7-6）**：link_density は plb 写像（s_avg→plb）の機械的濃淡を拾う量。feedback が高 link_density cid に weight を集中させれば子集団平均 link_density が上がるのは自然＝**世界応答の一部は写像の機械的帰結**。ゆえ「注意が世界を作り込んだ」の証拠として**単独では使えない**（full 前から明記の通り・別 lens=cycle_participation / R_positive_fraction は未実施 §4）。

## 3. 実装健全性・守った線（smoke から継続）

| 項目 | 結果 |
|---|---|
| parent physics hash 前後不変 | **OK**（PS/SCHEMA 不変＝親物理 read-only 実証） |
| 書込 v1304 配下のみ | OK（全出力 `unified/v1304/outputs`） |
| provenance 全保存・raw/rank 両保存（rank 監査のみ・更新に不混入） | OK |
| eps floor 正規化前・cid 単位平均・undrawn factor=1 | OK（rev4 準拠） |
| round0 support 固定（n=45・sum=1・entropy 3.78・cid_hash `a0ea…`） | OK（smoke と一致） |
| レプリカ null は子ゼロ追加の算術 | OK（K=10 は同一世界に相乗り・子 run 増やさず） |
| fork 並列の決定性 | OK（同一 (plb,seed) が直列と一致・micro 検証済） |

### 3.3 条件・限界（over-claim 防止）
- **親 profile は v1303 final seed0 のみ**（親 seed0 条件付き）。base0/1 は engine 系列で親 seed 変動でない。
- **single lens=link_density**（自己確認リスク §2.3）。並行 lens は未実施。
- g=1 primary・g=0.5 は参考（R5 base0 のみ）。

## 4. 走らせていないもの・次段（Code A は判定しない）

- **未実施**：複数親 seed（main）・並行 lens（cycle_participation / R_positive_fraction・別ループ）・独立 shuffle 世界分岐の統計判定（descriptive のみ）・揺れ（entropy 順位変化）の解釈・real/artifact の主題判定。
- **次段（承認後・Taka/Web Claude）**：(a) 別 lens で primary 再現（自己確認外しの本命）、(b) 複数親 seed で床超えの一般化、(c) 揺れの読み・回数増・多 eye・Atom 接続・独立 shuffle の世界分岐。**full はここで停止**。

## 5. 一文サマリ

v1304b full 報告（レプリカ null・事前固定 primary・判定なし #12）── K=10 の shuffle レプリカを feedback の同一世界（drawn/子/salience）に相乗りさせ子ゼロ追加で `D_fb=mean_k mean_round L1(fb,shuf_k)` と発散床 `D_null=mean_{i<j} L1(shuf_i,shuf_j)` を作り、系列 paired `D_fb−D_null` を R=12 系列 1標本 t で閉じたところ **g=1 の両 base で正・全系列 12/12 正・符号一貫性 1.0**（base0 diff0.200 t7.01 p2e-5／base1 diff0.162 t5.86 p1e-4・D_null 0.87–0.90 の床を D_fb 1.06–1.07 が超える）＝**「対応が weight 軌跡を方向づけた（レプリカ床超え）」まで**（学習/自律とは言わない・L型）、13,920 child 779秒 24並列（fork 決定性検証済）、secondary＝entropy 差も feedback がレプリカより強く集中（t8.5–9.8）・独立 composition shuffle は L1(fb,indep) 1.51–1.56 でさらに離れ閉ループの世界分岐候補（相乗り null と別物・descriptive）・世界応答は feedback 子集団 link_density が round で上昇（0.806→0.830）も **link_density は plb 写像の機械的濃淡を拾う自己確認リスクあり単独証拠に使えない**（別 lens 未実施）、実装健全性＝親物理 hash 前後不変（read-only 実証）・書込 v1304 配下・provenance/raw-rank/eps floor/cid単位平均/undrawn=1/round0 support 固定すべて継続、条件は親 profile v1303 seed0 のみ・single lens・g=1 primary/g=0.5 参考（同方向で弱い diff0.091 p0.034）、未実施＝複数親 seed/並行 lens/独立 shuffle 世界分岐の統計/揺れの解釈で承認後 next へ自動前進せず停止、別 lens 再現・複数親 seed 一般化・揺れ/回数増/多 eye/Atom 接続は Taka/Web Claude。
