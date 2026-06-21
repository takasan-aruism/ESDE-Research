# v12 Atomset — 懐疑主義 0ベース実装監査（STEP2-4 横断）

## 自己規律宣言（Code A）
① 過去引用済: STEP2 `m16`/`m18`(sim_matrix membership・rare↔common 0.96)、STEP3 `m20`/`m22`(build_step10 recompute time-local・tl↔静的 −0.31)、STEP4 `m24`/`m26`(drift・ctrlB shuffle)、STEP3 cid_align で確認の atom_profiles_cache slot_keys 整合、課題#1 m28 監査(ghost 訂正)。
② Taka 逐語（原文）: 「結果がうまく出ない時は実験そのものを疑う。想定が想定通り動いてるか」「この際懐疑主義で調べて」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-16、Code A。*目的*: 結論を左右する隠れ前提を実データで疑う。

---

## 0. 一文

4 点監査。**A(atom名前空間)・D(ctrlB shuffle) は問題なし**、**C/E(rare↔common) は交絡なしで核心保持**。**B(builder 交絡) が重大**: STEP2(sim_matrix) と STEP3/4(build_step10_cid_vector) は同 run-end でも membership が top5 0.97/5 しか重ならない＝**「time-local vs STEP2静的 −0.31/新規71%」(m22) と「edges vs sim_matrix共起 負」(m26) は時間/drift でなく builder 差の交絡**。同 builder の static baseline は未測。

---

## 1. 監査A — atom 名前空間の一致（cross-GATE の前提）

**疑い**: STEP3/4 の edge atom 名は `atom_profiles_cache`、STEP2 edge と GATE 共起は `cid_atom_sim_matrix` 列名。ズレてれば GATE の相関は名前マッチ失敗の artifact。
**結果**: cache 326 atom と sim_matrix 326 atom 列は **完全同名（共通 326、片側のみ 0）**。→ **artifact でない。PASS。**

## 2. 監査B — builder 不一致の交絡【重大】

**疑い**: STEP2 membership = `cid_atom_sim_matrix`（v106 **build_cid_vector**＝run-end版: informational=virt_fam, epistemological=last_familiarity_max count, symmetry=v99_drift…）。STEP3/4 = **build_step10_cid_vector**（trajectory版: informational=cum_pulse, epistemological=R_familiarity, symmetry=delta_pulse…）。別 builder なら「time-local vs static」は時間でなく builder 差を測る。
**結果（実データ, seed0, 228 cid）**: 各 cid の**最終 grid 点で build_step10 recompute した top5** と **sim_matrix top5** の重なり: **mean 0.97/5、中央 1、完全一致 0%、重なり 0 が 38%**。
→ **同じ run-end 時点でも 2 builder の membership はほぼ別物（1/5 しか共有しない）**。
→ **含意（訂正対象）**:
- `m22` GATE B「tl↔STEP2静的 rank相関 −0.31・新規対 71%」は **時間局所化の効果でなく大半が builder 差**。時間の効果は分離できていない（同 builder の run-end static baseline ＝ build_step10 を run-end 固定 membership で組む、を測っていない）。
- `m26` GATE E「main↔sim_matrix共起 負相関」も cross-builder 交絡（edges=build_step10, cooc=sim_matrix builder）。
- 私の `m22`「STEP2 の sim_matrix は build_step10 time-local の run-end 版」という記述は**誤り**（0.97/5 で別物）。

## 3. 監査C/E — rare↔common は交絡してないか【核心は保持】

**疑い**: rare↔common(0.96/0.925) が builder 交絡で意味を失ってないか。
**結果**: STEP3 の rare(`atom_edges_tl`) と common(`common_layer_edges_tl`) は**両方 m20 の同一 timelocal_membership(build_step10) 由来**＝**同 builder 内**。STEP4 の Main/ctrlA/ctrlB も全て build_step10 内。
→ **rare↔common と Main/ctrlA/ctrlB の比較は builder 内＝交絡なし。** 核心の観察（rare↔common が 0.96→0.925→Rfam 0.90 と高いまま＝event は出入り判定だけ、drift で Rfam が均等≈shuffle）は**保持される**。

## 4. 監査D — ctrlB shuffle が per-event 内か（Web Claude 明示要求）

**疑い**: 対照B の drift shuffle が per-(event,path) 内で正しく行われているか（global shuffle や no-op でないか）。
**結果**: 54,985 の (event,path) 群（target≥2）**全てで d_norm と d_shuf が多重集合一致**（値は保存、並びのみシャッフル）＝**per-(event,path) 内シャッフル正しい**。実際に並びが変わったのは 1,183 群＝drift が varied な群のみ（C は疎なので大半が同値=0 でシャッフルしても不変＝STEP4 の C の B 対照が seed で 0.61-0.89 と振れた一因）。→ **実装は正しい。PASS。**

---

## 5. 監査でどの結論が動くか（事実、判定は Taka）

| 結論 | 監査結果 |
|---|---|
| rare↔common が高い(event は出入り判定だけ) | **保持**（builder 内、交絡なし） |
| drift で Rfam≈均等≈shuffle / C 疎で退化 | **保持**（builder 内） |
| ctrlB shuffle | **正しい** |
| GATE の atom 名前マッチ | **正しい**（A PASS） |
| **「time-local が STEP2静的と大きく違う(−0.31/71%新規)」= 時間の効果** | **交絡で不成立** → 大半は builder 差。時間の効果は同builder baseline で測り直し要 |
| **「edges は sim_matrix共起の再描画でない(負相関)」** | **cross-builder 交絡**（負相関は builder 差込み） |
| 課題#1 ghost「平ら」(m28) | 既に訂正済（flat-frozen でない） |

## 6. 一方向保証
本監査は frozen を読むのみ（書込なし、parquet も書いていない）。grep 物理書込ゼロ。

---

*以上 懐疑監査（Code A、2026-06-16）。A名前空間=PASS, D shuffle=正しい, C/E rare↔common=builder内で交絡なし(核心保持)。B が重大: STEP2(sim_matrix) と STEP3/4(build_step10) は run-end でも membership top5 0.97/5 しか重ならず、「time-local vs 静的 −0.31」(m22)・「vs共起 負」(m26) は builder 交絡で時間/drift の効果と未分離。同builder static baseline で測り直しが要る。判定は Taka。*
