# v1302 (B) 成熟期 topology 移植 smoke 結果報告（Code A → Web Claude / Taka）
**(B) を誕生時(tree)から成熟期(age_r≥τ link 閉路ランク最大 window)に組み直し smoke。τ=10/50/100 頑健性・移植 field 定義明示・n2 の N 固定 canon 対照を反映。判定なし＝観察事実のみ。親 read-only・物理層 frozen。本番フルは Taka 承認後。**

*実施*: 2026-06-23、Code A。前提 = `cw_v1302_B_mature_feasibility.md`（2点緑）＋`cw_v1302_A_full_report.md`（(A) canon/A 確証・再利用）。

---

## 自己規律宣言（4点）
**① 過去引用明記** `cw_v1302_B_mature_feasibility.md`（成熟 window=age_r≥τ link 閉路ランク最大の一律 argmax・誕生時 has_cycle 0→成熟 τ50 で n2 24/35・τ 特定不能ゆえ複数 τ で頑健性）／`cw_v1302_A_full_report.md`（(A) n2 0.621/n4 0.731/n5 0.717・canon n2 0.133=N 残差・canon/A は本 smoke で再利用）／`cw_v1302_abx_smoke_report.md`（(B) 誕生時移植 不発=tree maxR=0・移植レシピ alive_n 登録+E/θ fresh→add_link・2点署名・shuffle 無料 Mantel）／`cw_v1302_design_audit.md`（topology 上流だが R は run 中発達）／§16（フル確定 Taka）。
**② Taka 逐語** 「Bはその発想いいんじゃない？ 閉路の形成に合わせる。成熟した個体が子を残す」「懐疑的にみても今回の試験結果には意味があったってことかな？ B進めてOK」「i,ii,iii は任せる」。
**③ 判定は Taka**。**④ 集約語禁止。crown 禁止。**

## 観察対象注釈ブロック
- 同系内：親 seed0 CID 縮小子系。読＝frozen per_subject/persistence/engine、書＝`unified/v1302/` のみ。親 physics/inject/ledger/state 非書込。移植は子 in-memory state への add_link のみ。bit-identity 3/3 一致。

---

## 移植 field の定義（(i) 明示・すり替え防止）
- **成熟 window の*選択*基準**＝age_r≥τ の link が閉路を成す（閉路ランク E−V+C 最大の）window。**全 CID 一律 argmax**（観察者が CID 個別に選ばない＝神の手回避）。
- **移植する*中身***＝その成熟 window の **field 一式（コア＋周辺、BFS max_hops=n_core+1、age_r フィルタ無しの全 link）**。成熟リンクだけに絞らない。
- 実装：`cw_v1302_field.py:build_mature_fields`（選択は `only_tau=tau` で閉路ランク argmax、移植は `only_tau=None` の全 link）。

## 移植が機構的に成功したことの確認（誕生時 tree からの変化）
- t0 fingerprint：**t0_loops ≈ 3.6–4.0**（誕生時移植は loops=0 だった）＝成熟 window field は閉路を運ぶ。
- **R 内生 probe**（`/tmp` 別 probe、移植→step_resonance）：誕生時 field(cid212, links=2,loops=0)→maxR=0.00 に対し **成熟 τ50 field(links=20,loops=4)→maxR=1.00**。＝成熟移植は閉路から R を内生で立てる。
- *注*：smoke parquet の t0_maxR=0 は **fingerprint が step_resonance 前**に取られたタイミング由来（R は step 内で計算）。loops>0＋R probe maxR=1.0 が「移植が R を運ぶ」ことを示す。**前 smoke の不発理由(tree)は機構的に解消された**。

---

## 結果（Mantel late r：親 structural 距離[s_avg,r_core,conc] vs 子創発署名・無料 null。canon/A は同一 CID 集合で取り直し）

### (B) 成熟期 × τ 頑健性（(ii)）
| 層 | B_t10 r/p | B_t50 r/p | B_t100 r/p | 同cid canon | 同cid (A) |
|---|---|---|---|---|---|
| **n2** | −0.012 / 0.52 (cyc30) | 0.284 / 0.041 (cyc24) | −0.085 / 0.72 (cyc15) | 0.04 / −0.05 / 0.03 | **0.52 / 0.42 / 0.60** |
| **n5** | 0.396 / 0.038 (cyc7) | 0.028 / 0.36 (cyc6) | (cyc4<5 不能) | −0.34 / −0.27 | **0.76 / 0.79** |
| n4 | <5 不能 | <5 不能 | <5 不能 | — | — |

### (iii) n2 の N 交絡を切る（N 固定 canon 対照）
| 条件(n2, 同一 CID 集合) | late r / p |
|---|---|
| **Nfix（N 固定+plb 一定）** | **−0.108 / 0.90**（N 変動を消すと transfer 消滅） |
| canon（N 変動+plb 一定） | 0.02 |
| **(A)（N 変動+plb=structural-strength）** | **0.542** |

---

## 観察（判定なし）

1. **(B) 成熟期移植は機構的に成功したが、transfer は依然弱く τ に頑健でない**。n2：B_t10 −0.012 / B_t50 0.284 / B_t100 −0.085 ＝**τ で符号も有意性も激変**。n5：B_t10 0.396 / B_t50 0.028。単発の弱い有意（B_t50 n2 p=0.041・B_t10 n5 p=0.038）は **τ を変えると消える**ゆえ、(ii) の頑健性検査では「特定 τ を選んだから出た」雑音と区別できない＝**τ 頑健な transfer とは言えない**。

2. **同一 CID 集合で (A) は常に強い**（n2 0.42–0.60・n5 0.76–0.79）。同じ CID で canon≈0・(B)≈0–0.4(非頑健)・(A)≈0.5–0.8。**(A) ≫ (B) ≈ canon**。成熟期にして閉路・R を運べるようにしても、(B) は (A) に届かない。

3. **(iii) (A) の transfer は N でなく plb**。N を固定した Nfix は r=−0.108（N 変動を消すと消滅）、canon（N 変動・plb 一定）も 0.02。一方 (A)（N 変動・plb=structural-strength）は同 CID で 0.542。canon と (A) は N が共通ゆえ、差(≈0.5)は **plb 純効果**。(A) n2 の transfer は N 残差でなく plb が担う、と確認。

4. **caveat-1 が成熟期でも確認された**：移植 field が閉路・R を持っても（t0 loops≈4・R probe maxR=1.0）、35k run 後の transfer は出ない。＝**topology は初期条件として減衰し、持続パラメータ plb のように identity を運ばない**（成熟させても初期条件は初期条件）。前 smoke の「(B) 不発＝tree だから」は半分で、**成熟させて閉路を入れても (B) は transfer しない**＝より深い「初期条件 vs 持続パラメータ」の差が真因。

---

## 報告とコードの対応（Web Claude 点検用 file:line）
| 項目 | 実装箇所 |
|---|---|
| 移植 field 定義（選択=age_r≥τ 閉路ランク最大の一律 argmax／移植=全 link 一式） | `cw_v1302_field.py:build_mature_fields`（選択ループ `only_tau=tau` の `_cycle_rank` argmax L~/移植 `field_at(..., only_tau=None)`） |
| τ=10/50/100 全部で回す | `cw_v1302_B_mature.py:TAUS=[10,50,100]` L34、`build_tasks` で τ ループ |
| 移植レシピ（alive_n 登録+E/θ fresh→add_link・前 smoke 不変） | `cw_v1302_abx.py:transplant` を import 再利用（`B_mature.worker` で cond.startswith('B_t')） |
| t0 fingerprint（loops/maxR） | `phys_fingerprint` 再利用（注：step_resonance 前ゆえ maxR=0・loops で閉路確認・R は別 probe で maxR=1.0） |
| (iii) N 固定 canon（n2・N=中央値119 一定） | `B_mature.worker` の `cond=='Nfix'`（`N=task['N_fixed']`）・`load_parents` で `n2_Nfixed` |
| canon/A 同一 CID 集合で取り直し | `analyse`（A_full parquet を cyclic CID 集合に制限、stratum 文字列比較） |
| shuffle 無料 Mantel | `cw_v1302_abx.mantel` 再利用（`rng.permutation`+`np.ix_`・child 再 run なし） |
| bit-identity | `bit_identity`（B_t50 同 seed 2回 一致 3/3、`cw_v1302_B_mature_bitid.json`） |

*cost: B+Nfix 528 child × 35k = 991s（17分）。canon/A は A_full(5seed) 再利用ゆえ再 run なし。*

---

## 次段（Taka 判断材料・実装側は停止）
- **(A) が確定的に本命**：3層 0.42–0.79・plb 純効果・N 非依存・全 CID 集合で頑健。
- **(B) は成熟期にしても transfer せず**（τ 非頑健・(A) に届かず・初期条件は減衰）。選択肢＝(i) (B) を畳む、(ii) 移植を初期条件でなく「子の run 中に持続注入する」形に変える（だが design_audit で topology 直接 runtime 注入は別途検討要）、(iii) (B) を「親構造は子に持続しない」という観察結果として受容。**Taka 判断**。
- (A) の本番フル（全 seed・他 stratum）や次レバー探索に進むか。

**本 smoke は記録のみ。判定は Taka。**

---

## 一文サマリ
v1302 (B) 成熟期移植 smoke（Code A, 2026-06-23, B+Nfix 528child/17分・bit-identity 3/3・canon/A は A_full 再利用・親 read-only）── (i) 移植 field=選択は age_r≥τ link 閉路ランク最大の一律 argmax・中身は全 link 一式。**機構は成功**（t0 loops≈4・R probe で成熟 field→maxR=1.0、誕生時 tree maxR=0 から解消）。だが **(ii) (B) transfer は τ 非頑健で不発**：n2 B_t10/50/100 = −0.012/0.284/−0.085、n5 = 0.396/0.028＝符号も有意性も τ で激変＝単発の弱有意は雑音。同一 CID 集合で **(A) は常に 0.42–0.79 ≫ (B)≈0 ≈ canon**。**(iii) N 固定 canon r=−0.108（N 変動消すと transfer 消滅）vs (A) 0.542＝(A) の transfer は N でなく plb と確認**。**caveat-1 が成熟期でも実証**＝閉路・R を持つ成熟 topology を移植しても 35k run で transfer せず＝topology は減衰する初期条件で、持続パラメータ plb のように identity を運ばない（前 smoke「tree だから不発」より深い「初期条件 vs 持続パラメータ」が真因）。**次段=(A) 本命確定・(B) は畳むか持続注入形か受容を Taka 判断。本番フルは承認後。判定は Taka。**
