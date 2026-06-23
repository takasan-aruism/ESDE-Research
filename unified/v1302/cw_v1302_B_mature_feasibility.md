# v1302 (B) 成熟期 topology 移植 feasibility 報告（Code A → Web Claude / Taka）
**(B) を「誕生時」から「age_r≥τ link が閉路を成す成熟の盛り window」に組み直す前の feasibility 2点を read-only 確認。判定なし。ここで一旦停止＝合意ゲート。(B) 移植の実装はまだしていない。**

*実施*: 2026-06-23、Code A。前提 = `cw_v1302_abx_smoke_report.md`（(B) 誕生時移植 不発＝誕生時 field は tree・閉路 R は run 中発達）。(A) フル run は本書と独立に並行実行中。

---

## 自己規律宣言（4点）

**① 過去引用明記**
`cw_v1302_abx_smoke_report.md`（(B) 誕生時移植 不発 n2 r=0.102/n5 −0.109 n.s.・t0 maxR=0・誕生時 field はほぼ tree 閉路 n2 0/35・n5 1/7／(A) 成功 n2 r=0.35/n5 r=0.717）／指示書（移植元を age_r≥τ link 閉路数最大 window に・**τ=label 誕生と同値で神の手回避・全 CID 一律規則で ESDE 自己判定**・feasibility 2点先行→合意→実装）／09・01（age_r=連続 R>0 step・閉路は run 中発達・link_snapshot_log は window20-69）／§16（合意ゲート前停止）。

**② Taka 逐語（原文）**
「Bはその発想いいんじゃない？ 閉路の形成に合わせる。生物でも子を残すのは成熟した個体で未熟な発達段階で子を残すのはリスクが高い」「これまでの調査と合わせて間違いない方をえらんでくれりゃいい」「まぁ結果出せればなんでもいいので進めてみて」。

**③ 判定は Taka**。**④ 集約語禁止。crown 禁止。**

---

## 観察対象注釈ブロック
- 同系内：親 seed0 CID 縮小子系の (B) 移植元(成熟期)検討。読＝frozen persistence(`label_member_persistence`/`link_snapshot_log`[window,link_id,**age_r_current**])/per_label/per_subject。書＝`unified/v1302/`(本md・feasibility parquet)。**親 read-only・child run なし(前処理点検)**。
- 成熟 window 選択は**全 CID 一律規則**（age_r≥τ link の閉路ランク最大 window を argmax）＝ESDE の量(age_r・閉路)が主体・観察者が CID 個別に選ばない（神の手回避）。

---

## feasibility 結果（CID=47＝persistence にコアlinkある n2:35/n4:5/n5:7）

| 層 | 誕生時 has_cycle | τ=10 成熟閉路CID / 移植field has_cycle / 成熟w中央値 | τ=50 同 | τ=100 同 |
|---|---|---|---|---|
| n2(35) | **0/35** | 30/35 / 30/35 / w40 | **24/35 / 24/35 / w40** | 15/35 / 15/35 / w20 |
| n4(5) | 0/5 | 4/5 / 4/5 / w35 | 4/5 / 4/5 / w35 | 4/5 / 4/5 / w35 |
| n5(7) | 2/7 | 7/7 / 7/7 / w32 | **6/7 / 6/7 / w32** | 3/7 / 4/7 / w20 |

（成熟 window が範囲端 w==69 に張り付く割合は全 τ・全層で **0%**＝真のピークが範囲内に収まり切れていない）

### 点1: 成熟 window がログ範囲に収まるか・age_r 復元・範囲外扱い → **可**
- **age_r は復元不要**：`link_snapshot_log.age_r_current` に window×link 毎 直接記録（最大280・median0・≥50 は 0.2%）。
- **範囲内**：成熟 window（閉路ランク最大）中央値は τ=50 で w40(n2)/w35(n4)/w32(n5)＝life の中盤。**w==69 張付 0%** ＝ピークが範囲(20-69)で切れていない。範囲外 CID 問題は事実上なし。
- ただし **window20 未満で死ぬ/成熟する CID** はログに乗らない（snapshot は20開始）。今回 persistence にコアlinkある 47 CID は全て範囲内で閉路ランク評価できた。

### 点2: 成熟 window field で has_cycle が誕生時 tree から立つか → **立つ（劇的）**
- 誕生時 has_cycle = **n2 0/35・n4 0/5・n5 2/7**（前 smoke の不発理由）。
- 成熟 window（τ=50）= **n2 24/35・n4 4/5・n5 6/7** に閉路が立つ。τ=10 なら n2 30/35。
- ⇒ 成熟期に移植元を変えれば移植 field が閉路を持つ＝移植直後 t0 で loops>0・maxR>0 が立つ見込み（前 smoke の t0 maxR=0 が変わる＝(B) の生死がここで変わりうる）。

---

## τ の推奨と要確認（神の手回避の要）
- **推奨 τ=50**：n2 24/35・n5 6/7 に閉路成立＋成熟 window 中央値 w40（life 中盤＝真の「成熟の盛り」）。
- τ=100 は厳しすぎ（n2 15/35 に減・成熟 window が w20 に寄る＝mature link がほぼ無く argmax が早期に倒れる）。τ=10 は最も広い（n2 30/35）が age_r=10 は「成熟」として緩い。
- **要確認（実装前）**：指示書は「τ=label 誕生と同値」。だが**コード内で label 誕生の age_r 閾値定数を一意に特定できなかった**（`label_member_persistence.age_r_at_birth` は 10〜40 の例もあり 50/100 と断定不可、`compress_min_age=10` は別概念）。**label 誕生 τ の正確な源を Web Claude/Taka と確定してから実装したい**（神の手回避の主張は「τ=ESDE 自己基準」に依存するため、τ の出所が曖昧だと担保が弱る）。データ上は τ=50 が中庸で機能する。

## (B) 対象 CID と範囲外扱いの提案
- τ=50 で閉路成立 CID＝n2:24/n5:6（n4:4）。**閉路の立たない CID（n2:11/n5:1）は (B) から除外**を提案（成熟しても閉路を持たない＝成熟期移植仮説をそもそも試せない）。
- 公平な3条件 Mantel のため、(B) を回す層は **この閉路成立 CID 集合に揃える**（canon/(A) も同 CID で取り直すか、(A) は全 CID 版〔フル run〕とは別に (B) 比較用サブセットで対照を取る）。**n5=6 は Mantel 下限ぎりぎり**ゆえ n2 主・n5 参考。

---

## 報告とコードの対応（Web Claude 点検用 file:line）
| 項目 | 実装箇所 |
|---|---|
| age_r 直接取得（復元不要） | `probe_b_maturity_feasibility.py:snap`（`link_snapshot_log.age_r_current` を window×link で保持 L62-64） |
| 成熟 window 一律規則（age_r≥τ link 閉路ランク最大 argmax） | `probe_b_maturity_feasibility.py:main`（全 window ループ L102-108 で `cycle_rank(mature)` 最大 window を選択・CID 個別の手選択なし） |
| 閉路ランク E−V+C（union-find） | `cycle_rank` L40-52 |
| field = core から BFS max_hops n_core+1 | `field_at` L70-92（誕生時 smoke と同 BFS・tau で age_r フィルタ） |
| 誕生時 vs 成熟 has_cycle 対比 | `main` L96-99（birth_rank）vs L112（mat_full_rank） |

---

## 合意ゲート（ここで停止）
**feasibility 2点とも可**（成熟 window はログ範囲内・age_r 直接取得可・has_cycle が誕生時 0 から τ50 で n2 24/35・n5 6/7 に立つ）。**(B) 成熟期移植の実装は未着手＝合意待ち**。確認したい1点＝**τ の確定（label 誕生 τ の源・推奨 50）**。合意後に `cw_v1302_field.py` を成熟 window 抽出に拡張し、移植レシピ（前 smoke の `transplant` 不変）＋2点署名で smoke する。

---

## 一文サマリ
v1302 (B) 成熟期移植 feasibility（Code A, 2026-06-23, read-only・child run なし・親 read-only）── **2点とも可**：(1) age_r は `link_snapshot_log.age_r_current` に直接在り(復元不要)・成熟 window(age_r≥τ link 閉路ランク最大の一律 argmax)中央値は τ50 で w40/35/32＝life 中盤・**w==69 張付 0%** でピークが範囲(20-69)に収まる、(2) **誕生時 has_cycle 0/35(n2)・2/7(n5) が成熟 window で τ50 なら 24/35・6/7 に立つ**（誕生 tree→成熟期は閉路を持つ＝前 smoke の t0 maxR=0 が変わる見込み）。τ 推奨=50(中庸・成熟中盤)、τ=100 は厳しすぎ・τ=10 は緩い。**ただし label 誕生 τ の正確な源をコードで一意特定できず**(age_r_at_birth は 10-40 例あり)、神の手回避の担保(τ=ESDE 自己基準)のため**τ 確定を要相談**。(B) 対象は閉路成立 CID(n2:24/n5:6)に絞り非成立CIDは除外提案。**feasibility ここで停止＝合意待ち。(B) 実装未着手。(A) フル run は独立並行中。判定は Taka。**
