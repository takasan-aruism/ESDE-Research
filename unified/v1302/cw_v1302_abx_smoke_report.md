# v1302 (A)+(B)+canon 並走 smoke 結果報告（Code A → Web Claude / Taka）
**3条件（canon / (A)scalar→plb / (B)topology 移植）を同一 step-0 枠で並走させた smoke を実装・実行。判定なし＝観察事実のみ。物理層 frozen・親 read-only 厳守。フル run は Taka 承認後。**

*実施*: 2026-06-23、Code A。前提 = `cw_v1302_abx_audit.md`（全項目緑・実装許可）。

---

## 自己規律宣言（4点）

**① 過去引用明記**
`cw_v1302_abx_audit.md`（(B) 移植レシピ＝alive_n 登録+E/θ fresh→add_link・shape-only(S/E 永続化なし)・R 内生・null は Mantel 行列置換で無料・caveat-1=(B) 移植は減衰する初期条件で step-0 transfer を担った plb=持続パラメータと機構違い）／`cw_v1302_seed_audit.md`（transfer は plb←s_avg 本体・K_sync/θ 幻雑音・structural-strength は S/R/conc）／`cw_v1302_design_audit.md`（runtime 3ノブ全滅＝topology 上流）／step-0（誕生時 seeding 枠・Mantel＋shuffle 無料・n_core 層化・創発署名・run 長35k）／§16（smoke 後 Taka 判断）。

**② Taka 逐語（原文）**
「AとBと同時にやればいいんじゃない？」「これまでの調査と合わせて間違いない方をえらんでくれりゃいい」「DNAみたいなもん…容易く改変できない」「CIDの強さは、ノード数だけでは決まらない」「まぁ結果出せればなんでもいいので進めてみて」。

**③ 判定は Taka**（success/fail を置かない、観察事実のみ）。**④ 集約語禁止。crown 禁止。**

---

## 観察対象注釈ブロック
- 同系内：親 seed0 CID 縮小子系（N≈B_gen×10, V82+V43 物理+VirtualLayerV9, stress/pressure OFF）。
- 読＝frozen：per_subject_seed0 / persistence / engine。書＝`unified/v1302/` のみ（コード・署名 parquet・summary・本 report）。**親 physics/inject/ledger/state/per_subject/persistence 非書込。** 移植は子 in-memory state への add_link のみ。
- bit-identity 確認済（同 seed 2回 run で署名 MD5 一致、9/9）。

---

## 結果サマリ（Mantel r：親 structural 距離[s_avg,r_core,conc] vs 子創発署名距離・無料 shuffle null）

| 層 | 条件 | late(35k) r / p | early(2k) r / p | early→late drift | t0 fingerprint(alive_n/l, loops, maxR) |
|---|---|---|---|---|---|
| **n2**(35) | canon | 0.03 / 0.331 | 0.061 / 0.273 | 3.21 | 120 / 111, 53, 4.72 |
| | **(A)** | **0.35 / 0.001** | 0.431 / 0.001 | 2.88 | 120 / 112, 51, 4.50 |
| | (B) | 0.102 / 0.146 | 0.036 / 0.318 | 2.24 | **12 / 10, 0, 0.0** |
| **n5**(7) | canon | −0.265 / 0.907 | −0.048 / 0.6 | 3.08 | 341 / 313, 125, 5.0 |
| | **(A)** | **0.717 / 0.006** | 0.347 / 0.05 | 2.93 | 341 / 317, 137, 5.0 |
| | (B) | −0.109 / 0.682 | 0.057 / 0.348 | 2.33 | **34 / 32, 1, 0.0** |

*cost: 252 child（42 CID×3 cond×2 seed）× 35k step = 960s（16分・46 workers）。shuffle 無料ゆえ null 再 run なし。*

---

## 観察（判定なし）

1. **(A) scalar→plb は transfer を出す**。n2 late r=0.35 p=0.001、**n5 late r=0.717 p=0.006**。canon（同 init・plb 一定）が r≈0 なのに対し (A) は有意。⇒ structural-strength(S/R/conc 合成)を*生きたレバー plb* に当てると親 identity が子の創発署名に伝わる。**seed_audit の的（plb 一本）が当たった**。

2. **(A) n5 は step-0 で出なかった transfer を出した**。step-0 の n5 は r=0.042（transfer なし、plb←s_avg のみ・K_sync←r_core 幻）。今回 (A) は S/R/**conc** を plb に合成して n5 r=0.717。⇒ r_core/conc は「情報が無い」のでなく「死レバー(K_sync)経由だった」だけで、plb 経由なら n5 でも効く——seed_audit の予想と整合。**ただし n5=7 CID は小標本**（21 ペア）ゆえ値は要追認。

3. **(B) topology 移植は transfer を出さない**。n2 r=0.102(n.s.)、n5 r=−0.109(n.s.)、early でも n.s.。**caveat-1 が実証された**：t0 fingerprint で (B) は alive_n=12-34・**loops=0-1・maxR=0**＝誕生時 field は tree（閉路なし＝R 無し）で、canon/(A) の injection（alive_n=120-341・loops 53-137・maxR~5）と桁違いに疎。移植した tree shape は run 中に canon plb の下で発達する構造に飲まれ、親 identity を残さない。

4. **減衰（early→late drift）は3条件で大差なし**（2.2-3.2）。(B) の drift がやや小さい（2.24/2.33）のは t0 構造が疎で動く幅が小さいため。**(B) の移植痕が「自己強化で残る」兆候は見えない**（caveat-1 の「auto_growth 自己強化 vs 減衰」は*減衰*側）。

5. **canon は対照として正常**（r≈0 / n5 は負）。

---

## structural-field 抽出の検証（§0 step1・最大リスク部）
- 抽出器 `cw_v1302_field.py`：`label_member_persistence`(CID→コア link) + `link_snapshot_log`(window→alive link) + birth_window snapshot、BFS `max_hops=n_core+1`、親 node→子 local remap。
- 検証（`cw_v1302_field_validation.parquet`）: n2 field_nodes med=11(2-36)/links med=9/**閉路 0/35**、n5 nodes med=21(5-108)/links med=19/**閉路 1/7**。
- **重要観察**：誕生時 structural field はほぼ tree（閉路ほぼ無し）。親の偏り R＝閉路は*誕生時には未形成で run 中に発達する*動的量ゆえ、誕生 topology の移植では R を運べない。これが (B) 不発の機構的理由（t0 maxR=0 と一致）。

---

## 報告とコードの対応（Web Claude 点検用 file:line）
| 設計項目 | 実装箇所 |
|---|---|
| structural-field 抽出（max_hops n_core+1・birth_window snapshot・remap） | `cw_v1302_field.py:build_fields`（max_hops=`n_core+1` L62, BFS L74-82, snapshot adjacency L70-72） |
| (A) plb 写像（S/R/conc 等重み z→tanh） | `cw_v1302_abx.py:strength_plb`（z 等重み平均 L95-100, `BASE_PLB*(1+0.3*tanh)` L101） |
| (B) 移植レシピ（alive_n 登録+E/θ fresh→add_link） | `cw_v1302_abx.py:transplant`（remap L120, `alive_n.add`+`E=E_FRESH` L122-124, `add_link(S_FRESH)` L126-127） |
| fresh 値（S=0.3/E=0.6 canon inject） | `cw_v1302_abx.py:L38`（`S_FRESH,E_FRESH=0.3,0.6`） |
| 2点署名（early 2000 / late 35k）＋t0 fingerprint | `cw_v1302_abx.py:worker`（fingerprint L171, early L173-175, late L177-179） |
| K_sync/θ canon 固定（幻/雑音） | `make_engine` で K_sync 既定 0.1・θ 上書きせず（A/canon は run_injection、B は θ 既定 uniform） |
| shuffle 無料 Mantel | `cw_v1302_abx.py:mantel`（`rng.permutation`+`np.ix_` L218-220、child 再 run なし） |
| 層化 n2 主+n5 補助 | `STRATA=['2','5']` L29、analyse は n_core 別 |
| bit-identity | `bit_identity` L233（同 seed 2回 署名 MD5 比較、結果 `cw_v1302_abx_bitid.json` 9/9 一致） |

---

## 不明点 / 次段の選択肢（Taka 判断材料・実装側は停止）
1. **(A) を本命に**：n2/n5 とも transfer。フル run（全 seed・n4 追加・seed 数増で n5 小標本を補強）に進むか。**n5 r=0.717 は 7CID ゆえ seed/層を増やして追認推奨**。
2. **(B) の扱い**：誕生時 topology 移植は不発（tree・R=0・transfer なし）。caveat-1 通り。選択肢＝(i) (B) を捨て (A) に集中、(ii) 移植 window を「R がピークの成熟期」に変える（"誕生時"でなくなるが偏り(閉路)を実際に持つ構造を移植）、(iii) topology 移植自体を畳む。**Web Claude/Taka 判断**。
3. **(A) のレバー拡張**：今 plb 一本・等重み。重み調整や別レバー併用は結果を見てから（今回は素直に等重み）。

**本 smoke は記録のみ。main run（フル）は Taka 承認後。判定は Taka。**

---

## 一文サマリ
v1302 (A)+(B)+canon 並走 smoke（Code A, 2026-06-23, 252child/16分・bit-identity 9/9 一致・親 read-only）── **(A) scalar→plb が transfer を出した**（n2 late r=0.35 p=0.001 / **n5 r=0.717 p=0.006**、canon r≈0 対照）＝structural-strength(S/R/conc)を生きたレバー plb に当てると親 identity が子創発署名へ伝わり、**step-0 で出なかった n5 も conc 合成で復活**（ただし n5=7CID 小標本・要追認）。**(B) topology 移植は不発**（n2 r=0.102/n5 −0.109 とも n.s.）＝caveat-1 実証：誕生時 structural field はほぼ tree（閉路 n2 0/35・n5 1/7、t0 maxR=0）で偏り R は誕生時未形成・run 中発達ゆえ移植では運べず canon 構造に飲まれる。減衰は3条件大差なく (B) 自己強化の兆候なし。**次段は (A) 本命でフル run(seed/層拡張で n5 追認)・(B) は捨てるか成熟期 window 移植に変えるかを Taka 判断**。main run は承認後。判定は Taka。
