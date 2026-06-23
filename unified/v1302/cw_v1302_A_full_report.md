# v1302 (A) scalar→plb フル run 追認 報告（Code A → Web Claude / Taka）
**前 smoke で効いた (A) を設計変更なし・全 CID(n2/n4/n5)・seed5 でフル run 追認。判定なし＝観察事実のみ。親 read-only・物理層 frozen。本番確定は Taka 承認後。**

*実施*: 2026-06-23、Code A。設計 = `cw_v1302_abx.py:strength_plb`（そのまま import・同一性担保）。(B) 成熟期は別途 feasibility 報告で合意待ち（独立）。

---

## 自己規律宣言（4点）
**① 過去引用明記** `cw_v1302_abx_smoke_report.md`（(A) smoke: n2 r=0.35/n5 r=0.717〔7CID 小標本〕・canon 対照 r≈0・structural-strength=S/R/conc 等重み z→tanh→plb）／指示書（(A) は設計変更なし・seed/n4 拡張で追認・特に n5 が小標本の偶然でないか）／`cw_v1302_seed_audit.md`（transfer は plb 本体・N は plb と共線）／§16（フル確定は Taka）。
**② Taka 逐語** 「Aはそのままでいい」「これまでの調査と合わせて間違いない方をえらんでくれりゃいい」「まぁ結果出せればなんでもいいので進めてみて」。
**③ 判定は Taka**。**④ 集約語禁止。crown 禁止。**

## 観察対象注釈ブロック
- 同系内：親 seed0 CID 縮小子系。読＝frozen per_subject_seed0/engine。書＝`unified/v1302/` のみ。親 physics/inject/ledger/state 非書込。field 不要(移植しない)ゆえ全 stratum 全 CID 使用。bit-identity は smoke で確認済(同一 worker 機構)。

---

## 結果（Mantel late r：親 structural 距離[s_avg,r_core,conc] vs 子創発署名・無料 shuffle null、seed5 平均）

| 層 | canon r / p | **(A) r / p** | smoke(2seed,intersection) → full(5seed,全CID) |
|---|---|---|---|
| **n2** | 0.133 / 0.049 | **0.621 / 0.001** | r 0.35(35CID) → **0.621(54CID)**：seed 増で強化 |
| **n4** | 0.012 / 0.456 | **0.731 / 0.001** | 新規（smoke 未実施）：強い transfer |
| **n5** | 0.034 / 0.415 | **0.717 / 0.001** | r 0.717(7CID) → **0.717(17CID)**：全 CID で同値＝小標本の偶然でない |

*cost: 820 child（82 CID×2 cond×5 seed）× 35k step = 4300s（72分・46 workers）。shuffle 無料ゆえ null 再 run なし。*

---

## 観察（判定なし）
1. **(A) transfer は追認された。3層すべて A r≈0.62-0.73 / p=0.001**。canon（plb 一定・同 init）は n4/n5 ≈0、n2 のみ 0.133（後述）。(A) が canon を明確に上回る＝structural-strength(S/R/conc)を plb に当てた効果は実在。
2. **seed 増で transfer が強まった（n2 0.35→0.621）**。smoke 2seed は seed 雑音で過小評価していた（step-0「単一 child は seed 雑音優位」と整合）。
3. **n5 r=0.717 は小標本の偶然でない**。smoke は persistence intersection 7CID だったが、フルの 17CID・5seed でも r=0.717 p=0.001。n5（step-0 で transfer 出なかった層）が conc 合成 plb で安定に transfer。
4. **n4 も強い（0.731）**。
5. **canon n2 のみ r=0.133（p=0.049）**：canon は plb 一定だが N=b_gen×10 が CID で変わり、b_gen は s_avg と共線(seed_audit −0.82)ゆえ **N チャネル残差**が n2 で僅かに出る。A の 0.621 と比べ小さく、(A) 効果は N 残差を大きく超える。

---

## 報告とコードの対応（Web Claude 点検用 file:line）
| 項目 | 実装箇所 |
|---|---|
| (A) plb 写像（前 smoke と同一・等重き） | `cw_v1302_A_full.py` が `from cw_v1302_abx import strength_plb` で**そのまま再利用**（`cw_v1302_abx.py:strength_plb` L93-101：S/R/conc 層内 z 等重み平均→`BASE_PLB*(1+0.3*tanh)`） |
| 全 CID（n4 追加・n5 を 17 に） | `cw_v1302_A_full.py:load_all`（`STRATA=['2','4','5']` L27・field 不要で dropna のみ） |
| canon=plb 一定対照 | `worker` L72（cond!='A' は BASE_PLB） |
| seed5 | `N_SEEDS=5` L29 |
| shuffle 無料 Mantel | `cw_v1302_abx.mantel` 再利用（`rng.permutation`+`np.ix_`・child 再 run なし） |
| 署名（late35k） | `signature` 再利用（創発人口統計・入力の写しでない） |

---

## 次段（Taka 判断材料・実装側は停止）
- **(A) は3層で安定 transfer 確認**。本番フル（さらに seed 増/全 seed・他 stratum）に進むか、(A) を確定として次の問い（plb 以外のレバー併用・重み調整・別の親量）に進むかは Taka。
- canon n2 の N 残差(0.133)を消すなら N も canon 固定する対照を足せる（今は step-0 同様 N=b_gen×10）。
- (B) 成熟期は別 feasibility 報告で合意待ち（独立）。

**本 run は記録のみ。判定は Taka。**

---

## 一文サマリ
v1302 (A) フル run 追認（Code A, 2026-06-23, 820child/72分・親 read-only・設計変更なし strength_plb 再利用）── **(A) scalar→plb の transfer を追認**：n2 r=0.621/n4 0.731/n5 0.717（全 p=0.001、canon は n4/n5≈0・n2 0.133=N チャネル残差）。**seed 増で n2 が 0.35→0.621 と強化**（smoke 2seed は seed 雑音で過小評価）、**n5 は 7CID→全17CID・5seed でも r=0.717＝小標本の偶然でないと確認**。structural-strength(S/R/conc)を生きたレバー plb に当てる設計は3層で安定に親 identity を子創発署名へ伝える。**本番フルや次レバーは Taka 判断・記録のみ。(B)成熟期は別途合意待ち。**
