# v1302 誕生時 seeding 設計監査資料（Code A → Web Claude / Taka）
**pivot 設計（runtime 駆動を捨て step-0 系譜の誕生時 seeding に戻す／seed 元を B_gen から member S/R/E の structural-strength へ）を検証＋step-0 transfer のチャネル分解＋structural-strength feasibility。child run / smoke / 実装は実行ゼロ。read-only ＋最小 probe のみ。合意ゲート前で停止。**

*監査実施*: 2026-06-23、Code A。前提 = `cw_v1302_design_audit.md`（runtime 駆動3ノブが偏りを増幅しない＝topology 上流を実機確認）。判定（success/fail）は置かない＝一致/不一致と可否のみ。

---

## 自己規律宣言（4点）

**① 過去引用明記**
`cw_v1302_design_audit.md`（§1-3 K_sync↑→loop/R 不伝播・§1-5 auto_growth は統合ノブで R と size 逆・β 非単調＝runtime 駆動で偏り増幅不可・topology 上流／§1-6 B_gen 同 n_core 内不変 CV0.02-0.05・§2-2 member S/R/E は割れる CV 大／§2-1 coherence は window 解像度・n2 平坦）／step-0 `cw_step0.py`（誕生時に親 M_c→子 birth param、Mantel＋shuffle 行列置換=無料、n_core 層化、**n2 r=0.49**／強チャネルと目された K_sync が topology に効かない＝channel 帰属の要再検証）／§16（smoke 後停止、本書は smoke 前）。

**② Taka 逐語（原文）**
「DNAみたいなもん…容易く改変できない」「偏りがはっきり出る要素をその偏りをそもそも出している物理演算に変数として加えれば偏りが際立つ」「CIDの強さは、ノード数だけでは決まらない」「直接CID側の計算式を変えないで子ESDE用の計算式だけ一時的に変える手もあり」「まぁ結果出せればなんでもいいので進めてみて」。

**③ 判定は Taka**（success/fail を置かない、一致/不一致と可否のみ）。

**④ 集約語禁止。crown 禁止。**

---

## 観察対象注釈ブロック

- 読＝frozen：engine ソース（`esde_v82_engine.py` / `esde_v43_engine.py` / `genesis_physics.py` / `genesis_state.py` / `realization.py`）、`v101_unity_metrics.py`、`_compute_pbirth.py`、`per_subject_seed0.csv`、step-0 出力（`unified/v1301/cw_step0_signatures.parquet` / `cw_step0_summary.json` / `cw_step0.py`）。
- 書＝本監査資料＋ probe（`probe_step0_channel_ablation.py`、stdout のみ・データファイル非生成）。
- **child の実験 run（real/shuffle・smoke・署名生成・新規 Mantel 実験 run・親軌跡駆動）は一切走らせていない。** step-0 の*既存*署名 parquet の read-only 再解析のみ（新規 child run でない）。親 physics/inject/ledger/state 非書込。

---

## 結論サマリ

| 区分 | 項目 | 判定 |
|---|---|---|
| §1-1 | step-0 枠の再利用＋shuffle 無料復帰 | **一致（可）**。seed 元差替で枠不変、shuffle は行列置換で無料 |
| **§1-2** | **step-0 transfer のチャネル分解** | **plb←s_avg が transfer 本体・K_sync←r_core は幻チャネル確定・θ 寄与ゼロ・N は plb と共線で entangle** |
| §1-3 | structural-strength 構成＋一意性 | **可（条件付）**。S/R/concentration は per-CID 在＆割れる、**member E は clean な集約なし**（代理要） |
| §1-4 | topology 直接移植（feasibility のみ） | **可**。`state.add_link` で親 member link を子初期 link 集合に instantiate 可 |

**設計の的（§1-2 が決めた）**: transfer は **plb（リンク誕生＝topology レバー）** に乗る。**K_sync は外す**（幻）。structural-strength は「効いたレバー plb / member-S 軸」を richer にする方向＝member R・E を *plb 側へ* 折り込む試み（R は step-0 で K_sync 死レバー経由ゆえ痕を残さなかった＝情報が無いのでなくレバーが死んでいた、を分けて読む）。

---

## §1 設計監査

### §1-1 step-0 枠の再利用＋shuffle 無料復帰 → 一致（可）
- `cw_step0.py`: `worker()` が `transform(c,st)` で親値→子 birth param（N←b_gen / plb←s_avg / K_sync←r_core / θ←phase_sig）を set し child を run、`analyse()` が cid 平均署名で Mantel。
- **seed 元差替**: `transform()` の `N=int(round(c['b_gen']*10))` を structural-strength スカラ由来に差し替えるだけ。Mantel・署名・層化は無変更で枠は壊れない。
- **shuffle 無料復帰**: `mantel()`（`:156-167`）は `perm=rng.permutation(n); Dpp=Dp[np.ix_(perm,perm)]` ＝ D_parent 行列の置換で null を作る。**child 再 run しない**（`:13` コメントも明記）。dynamic 版で発生した「null 毎に子再 run」コストは消える。

### §1-2【最重要】step-0 transfer のチャネル分解 → plb 本体・K_sync 幻
既存署名 parquet の read-only 再解析（`probe_step0_channel_ablation.py`）。D_child は全チャネル稼働下の step-0 署名で固定、D_parent 側を1チャネル抜いて Mantel を引き直す（association 分解）。チャネル↔親記述子: N↔b_gen / plb↔s_avg / K_sync↔r_core / θ↔phase_sig。

**n2（cid=54、transfer 層）:**
```
full(N+plb+Ksync+theta): r=0.583 p=0.001
 −N     : r=0.490 (Δ−0.093)      ← N 抜くと step-0 公称 Mc 値 0.49 に一致
 −plb   : r=0.398 (Δ−0.185)      ← 最大の落差＝plb が本体
 −Ksync : r=0.575 (Δ−0.008)      ← ほぼ不変＝K_sync は寄与せず
 −theta : r=0.631 (Δ+0.048)      ← 抜くと上がる＝θ は雑音
単独  only plb=0.639(p.001) / only N=0.587(p.001) / only Ksync=0.108(p.108 n.s.) / only theta=0.060
共線  b_gen/s_avg=−0.82  b_gen/r_core=−0.17  s_avg/r_core=0.13  r_core/phase=−0.02
```
- **plb←s_avg が transfer 本体**（単独 0.639、抜くと最大落差）。
- **K_sync←r_core は幻チャネル**（単独 0.108 n.s.、抜いても Δ−0.008）。r_core は他軸と共線でない（corr~0）ので「共線に隠れて見えない」のでなく**真に痕を残していない**＝§1-3 design_audit（K_sync は topology に効かない）と完全整合。
- **θ←phase_sig は寄与ゼロ**（単独 0.060、抜くと r 上昇）。
- **N と plb は共線**（b_gen/s_avg=−0.82）＝N と plb は n2 でほぼ同一軸。transfer は「s_avg≈−b_gen 軸」に乗り、N/plb を分離はできない。

**n4（cid=11）:** full r=0.337。plb 主（only plb=0.337）。ただし入力が総共線（b_gen/s_avg=−0.86, b_gen/r_core=−0.87, s_avg/r_core=0.56）で帰属困難。K_sync は −0.029 / only 0.219(n.s.)＝n2 同様弱い。
**n5（cid=17）:** full r=0.012＝transfer なし（step-0 と一致）。only plb=0.202 が辛うじて最大だが n.s.。

**含意（観察）**: step-0 の n2 transfer は **plb（=topology レバー＝リンク誕生確率）に乗る**。これは design_audit「topology が上流」と一貫。**K_sync/θ は設計から外してよい**（幻/雑音）。richer 化の的は plb / member-S 軸。

### §1-3 structural-strength 構成＋一意性 → 可（条件付・member E に注意）
- **同 n_core 内分散（§2-2 確定）**: CV=std/|mean| で n2: B_gen=0.047(極小) / s_avg=1.306 / r_core=0.165 / conc_final=0.464、member *数* k_final=0.000（=n_core で不変）。⇒ 一意性は member S/R/concentration にあり、ノード数には無い（Taka「強さはノード数だけで決まらない」と整合）。
- **可用列**: S=`v11_m_c_s_avg`、R=`v11_m_c_r_core`、concentration(θ集中度)=`v18_v_unified_concentration_birth` は per-CID frozen にある。
- **member E は clean な per-CID 集約が per_subject に無い**（候補は `v18_cognitive_gain_final` だが認知 gain＝E そのものでない）。member node E の真の分布が要るなら `network/`・ledger の追加読み or 代理採用が要る＝**要設計変更点**（E を諦め S/R/concentration の3軸で作る、が現実的）。
- **structural-strength スカラ = f(S, R, concentration)**（member 量の合成）で同 n_core 内一意性は出せる。式・重みは実装時 Web Claude 合意（ここで確定しない）。

### §1-4 topology 直接移植（feasibility のみ）→ 可
- `genesis_state.py:73 add_link(i,j,strength)` が存在し、`add_link` 内でノードを `alive_n` に追加（`:105`）。`state.E[i]` 直接代入も可（§8/前 probe で実証）。
- ⇒ child engine を fresh random でなく **親 member の link 集合（どのノード対がどの S か）を初期状態として instantiate** できる（各 member link に `add_link` + 各 member node に E set）。R は閉路から計算ゆえ直接 set 不要（topology を入れれば R は内生）。
- **可**。採否は scalar seeding の結果を見て Taka（今回は実装しない）。

---

## §2 feasibility（seeding 算出）
1. **structural-strength → 子 N/初期構造の写像**: per_subject の `v11_m_c_s_avg` / `v11_m_c_r_core` / `v18_v_unified_concentration_birth` で per-CID スカラを合成可（member E は欠＝S/R/conc で代替）。これを子の N や **初期 plb**（§1-2 で効いたレバー）へ当てる。scaling 値はここで確定しない。**設計示唆**: §1-2 より N より plb 側に当てる方が transfer レバーと一致。
2. **創発署名**: step-0 の `worker()` 末尾署名（n_labels/mean_size/std_size/share_gini/mean_age/lifecycle_events、入力の写しでない創発人口統計）をそのまま再利用可。n_core 別層化も既存。**可**。

---

## §3 step-0 からの再確認（inherited）
- **shuffle 無料化**: §1-1 で確認（行列置換、child 再 run なし）。dynamic 版の最大コスト（null 毎再 run）が消える。
- **コスト**: child は real のみ（shuffle は統計置換）。step-0 実績 = 1002 child（n2/4/5 × 12 seeds + canon）を seed12 で完走。pivot も同オーダー＝Pool24 で step-0 と同程度。smoke 規模は seed/層を縮小して概算更新（実 run せず確定は承認後）。

---

## §4 不一致 / 不可時の帰結（勝手に代替実装せず合意待ち）
1. **K_sync は幻チャネル（§1-2 確定）→ 設計から外す。** structural-strength は plb（効いたレバー）/ member-S 軸へ。θ も雑音ゆえ縮小可。
2. **transfer は plb=s_avg≈−b_gen 軸に乗り、N と plb は n2 で共線**。structural-strength を N と plb の両方に当てると冗長。**plb 側に集約**を推奨（topology レバー）。
3. **member E は clean な集約なし → S/R/concentration の3軸で structural-strength を作る**（E 諦め or 代理）。要 Web Claude 合意。
4. **richer が step-0 を超えるかは未知**: r_core は K_sync 死レバー経由で痕を残さなかった＝情報無しでなくレバー死。R/E を*生きたレバー plb* に折り込めば transfer を足す*可能性*はあるが、既存データからは断定不可＝smoke で見る対象。超えなければ topology 移植（§1-4）か step-0 受容を Taka 判断。

**いずれも実装せず、本資料を差し戻して合意を待つ。**

---

## 一文サマリ
v1302 誕生時 seeding 設計監査（Code A, 2026-06-23, child run/smoke/実装ゼロ・read-only＋最小 probe）── pivot（runtime 駆動を捨て step-0 系譜の誕生時 seeding に戻す／seed 元を B_gen から member S/R/E の structural-strength へ）を検証。**§1-1 step-0 枠は seed 元差替で再利用可・shuffle は行列置換で無料復帰**（dynamic の null 再 run コスト消滅）。**最重要 §1-2 step-0 transfer のチャネル分解（既存署名の read-only 再解析）= plb←s_avg が n2 transfer 本体（単独 r=0.639/抜くとΔ−0.185）、K_sync←r_core は幻チャネル確定（単独 0.108 n.s./抜いてもΔ−0.008・r_core は非共線ゆえ真に痕なし）、θ 寄与ゼロ、N は plb と共線(−0.82)で entangle**＝design_audit「topology 上流」と整合し richer の的は plb/member-S 軸、K_sync/θ は外す。§1-3 structural-strength は S(`v11_m_c_s_avg`)/R(`v11_m_c_r_core`)/concentration(`v18_..._birth`)で同 n_core 内一意に作れる（member 数 k=n_core は CV0 で不可・**member E は clean 集約なしで要代理**）。§1-4 topology 移植は `state.add_link` で feasible（採否は Taka）。**差し戻し: K_sync/θ を外し structural-strength を plb 側へ集約、E は S/R/conc で代替、richer が step-0 超えるかは smoke 対象。child run は合意後。判定は Taka。**
