# v1302 設計監査資料（Code A → Web Claude / Taka）
**改訂設計（K_sync←coherence 単一チャネル + N←子専用 structural-strength）の機構主張をコードで検証＋新規2点 feasibility＋§8 差分再確認。child run / smoke / 実装は実行ゼロ。read-only ＋最小 probe のみ。合意ゲート前で停止。**

*監査実施*: 2026-06-22、Code A。前提 = `cw_v1302_feasibility_check.md`（旧3チャネル案の §8 点検）。設計はその後改訂。判定（success/fail）は置かない＝一致/不一致と可否のみ。

> **ディレクトリ命名注**: 指示書 §6 は出力先を `unified/v1302_childworld_dynamic/` とするが、確定した命名規律（版はディレクトリ `v1302` が担う・`docs/最低限規律.md`）に従い `unified/v1302/` に置いた。

---

## 自己規律宣言（4点）

**① 過去引用明記**
`cw_v1302_feasibility_check.md`（旧3チャネル案 plb←Q / K_sync←R_familiarity / decay_link←n_core_member は本書で撤回、K_sync runtime可・10step駆動・子寿命=親寿命・コスト構造は流用）／step-0（K_sync←r_core 100%伝達・phase_sig←初期θ 84%・capture_rate→decay は n4/n5 で r_core 共線で不合格）／§6.1・§14（物理 Kuramoto 秩序量は認知/意識統合と別物＝層取り違え注意）／§16（smoke 後停止、本書は smoke *前*）。

**② Taka 逐語（原文）**
「物理的な演算の偏りを拾ってるのがCID。その偏りがはっきり出る要素をその偏りをそもそも出している物理演算に変数として加えれば偏りが際立ったESDEの物理世界ができる」「10ノードのCIDができるかもしれないし、偏りがより偏りのあるCIDを作ることになるだろう」「Qの計算方法には問題があった…私が重要視したのはB_Genの桁数ではなくて、数字の一意さ」「CIDの強さは、ノード数だけでは決まらない」「直接CID側の計算式を変えないで子ESDE用の計算式だけ一時的に変える手もあり」「v1302」。

**③ 判定は Taka**（success/fail を置かない、観察事実＝一致/不一致と可否のみ）。

**④ 集約語禁止。crown 禁止。**

---

## 観察対象注釈ブロック

- 読＝frozen：engine ソース（`ecology/engine/genesis_physics.py`〔step-0 と同 sys.path 上で実 import される active 版〕 / `cognition/.../v43/esde_v43_engine.py` / `autonomy/v82/esde_v82_engine.py` / `ecology/engine/autogrowth.py` / `realization.py`）、`ecology/engine/v19g_canon.py`、`developmental/v101/v101_unity_metrics.py`、`primitive/v911/_compute_pbirth.py`、`per_subject_seed0.csv`、`v18_window_trajectory_seed0.csv`、`step10_trajectory/`、`cw_step0.py`。
- 書＝本監査資料（`cw_v1302_design_audit.md`）＋ probe（`probe_ksync_loop_r.py` / `probe_data_properties.py`、stdout のみ・データファイル非生成）。
- **child の実験 run（real/time-shuffle/canon・smoke・署名生成・Mantel・親軌跡駆動）は一切走らせていない。** 親 physics/inject/ledger/state 非書込。
- probe 粒度＝§8 と同等：engine import → param を runtime/構築時セット → 数百 step → loop/R/kuramoto/alive を観察。署名/Mantel/実験データ生成なし、ファイル非生成。

---

## 結論サマリ

| 区分 | 項目 | 判定 |
|---|---|---|
| §1-1 | K_sync 差込点（op2 Kuramoto） | **概ね一致・ただし主張に過大表現**（全node/生Σ でなく *neighbors 限定＋近傍数で正規化*） |
| §1-2 | 偏りエンジン連鎖（op4/op5/op7） | **一致**（child スタックで実稼働確認。R cap だけ `min(R,5)` でなく `beta_max/beta`＝canon で5） |
| **§1-3** | **【最優先】K_sync↑→loop/R↑** | **不一致（設計の核が崩れる）**。K_sync 10倍でも loop/R/cluster 不変。kuramoto_r は上がる（ノブ生）が topology に伝播せず |
| §1-4 | V_unified=mean(exp(iθ)) over member＝per-CID | **一致** |
| §1-5 | auto_growth/β frozen・runtime 可否 | **両方 runtime 書換可**（(B) 案 feasible・Taka 判断材料） |
| §1-6 | B_Gen の n_core 支配（structural-strength 根拠） | **一致**（B_gen_CV 0.02-0.05・member 系 CV 大でデータ確認） |
| §2-1 | coherence 駆動ログ可否＋性質 | **要設計変更**（window=500step 解像度のみ・**n2 は弧45%/中央値2点で順序問えず・弧は n4/n5**） |
| §2-2 | structural-strength 算出＋同 n_core 内分散 | **可（条件付）**（member S/R/E 集約は割れる・member *数* は k=n_core で割れない CV=0） |
| §3 | K_sync runtime 単一形・コスト | **可・ただし効果微弱**（transform 域 [0.07,0.13] では kuramoto_r ≈0.04-0.06 でほぼ動かず、§1-3 と合わせ二重に弱い） |

**最重要差し戻し**: §1-3 が**不一致**＝改訂設計の中心因果（coherence→K_sync→偏り増幅）がエンジンで成立しない。勝手に直さず Web Claude へ差し戻す（§4）。

---

## §1 設計監査（各主張＝一致/不一致＋実コード）

### §1-1 K_sync 差込点 → 概ね一致・主張に過大表現
- op2 `step_pre_chemistry`（`genesis_physics.py:77-81`）が `_phase_rotate`→`_flow_and_sync` を毎 step 呼ぶ。
- `_phase_rotate`（`:106-136`）: `freq=omega[i]+alpha·E[i]`（canon alpha=0）、Kuramoto 項 `:126-133`。
- **不一致点**: 主張「毎 step・*全 node*・`K_sync·Σ_j sin(θ_j−θ_i)`」に対し、実コードは
  ```python
  nbrs = state.neighbors(i)              # ← 全 node でなく「リンク先 neighbors」限定
  for j in nbrs: sync_sum += sin(θ_j−θ_i)
  d_theta[i] += K_sync * sync_sum / max(len(nbrs),1)   # ← 生Σでなく近傍数で正規化(平均場)
  ```
  K_sync はリンク済み近傍に対する*平均*位相引力。**結合は既存リンク topology に媒介される**（後述 §1-3 の機構ギャップに直結）。

### §1-2 偏りエンジン連鎖 → 一致（child スタックで実稼働）
- **child が実際に回すか**: `esde_v82_engine.py:144-164` step_window が毎 step `realizer.step → step_pre_chemistry → chem.step → step_resonance → grower.step → step_decay_exclusion` を実行。連鎖は in-memory child で稼働。
- op4 Resonance（`genesis_physics.py:172-196`）: 閉路で `R_new[lk]+=w`、`w=cycle_weights={3:1.0,4:0.5,5:0.25}`（`:62-63`）、`max_cycle_length=5`。**cap は `beta_max/max(beta,0.001)`（`:195`）**＝canon `beta_max=5.0/beta=1.0`→ **5.0**。主張 `min(R,5)` は canon で数値一致だが機構は parametric（β を上げると cap=5/β は*下がる*副作用）。
- op7 Decay（`:205-210`）: `eff=decay_rate_link/(1+beta·r); S*=(1-eff)` ＝主張と**完全一致**（R が減衰保護）。
- op5 Auto-Growth（`autogrowth.py:58-59`）: `desired=auto_growth_rate·r; actual=min(desired,l_ij,1-S)` ＝主張と**一致**（R が成長駆動）。canon `auto_growth_rate=0.03`。
- 連鎖（高R link→減衰減＋成長→閉路に残り更にR）の各式は実装通り。**ただし R は閉路＝リンク topology の関数**（§1-3 で効いてくる）。

### §1-3【最優先 probe】K_sync↑→loop/R↑ → 不一致（核が崩れる）
`probe_ksync_loop_r.py`（N=200・同 seed・静的 K_sync 3水準・300/600step、署名/駆動/shuffle なし）:
```
300step  K_sync=0.03: loops=0 meanR=0.0  | labels=16 mean_size=4.19 top5=[6,6,6,5,5]
         K_sync=0.1 : loops=0 meanR=0.0  | labels=17 mean_size=3.88 top5=[6,6,6,5,5]
         K_sync=0.3 : loops=0 meanR=0.0  | labels=17 mean_size=4.12 top5=[6,6,6,5,5]
600step  K_sync=0.03: loops=4 meanR=0.062 maxR=1.0 | mean_size=4.33 top5=[6,6,6,5,5]
         K_sync=0.1 : loops=4 meanR=0.062 maxR=1.0 | mean_size=4.24 top5=[6,6,6,5,5]
         K_sync=0.3 : loops=4 meanR=0.062 maxR=1.0 | mean_size=4.22 top5=[6,6,6,5,5]
```
**K_sync を10倍動かしても loop 数・meanR・maxR・cluster サイズ分布が不変。**

probe 妥当性の切り分け（ノブが死んでいる説を排除）— kuramoto 秩序量は K_sync で確実に動く:
```
K_sync=0.0:r=0.038  0.03:0.034  0.1:0.056  0.3:0.209  1.0:0.556
```
⇒ **K_sync は位相同期(kuramoto_r)を確かに上げる。が、その同期は loop/R/cluster に伝播しない。**

**機構ギャップ（観察）**: loop/R は `find_all_cycles`＝*リンク topology* の関数。リンク誕生は realization `p_realize=plb·L_ij`（`engine_accel_v5.py:263`）＝*位相非依存*。K_sync が動かす θ は flow の `phase_factor=0.5+0.5γcos(Δθ)`（`genesis_physics.py:157`）経由で*エネルギー配分*にだけ効き、リンク生成に入らない。主張の鎖「K_sync↑→閉路↑→R↑→cluster大」は**最初の矢印（位相→topology）で切れている**。
**判定なし（観察事実）。** 設計の核がここに乗るため §4 で差し戻す。

### §1-4 V_unified / concentration 定義 → 一致
`v101_unity_metrics.py`: `compute_v_unified(θ)=mean(exp(1j·θ))`（`:46`）、`unity_concentration=|v_current|`（`:75-111`、`current_member_nodes` 上で `abs`）。**per-CID・member node 集合の上**で主張通り。birth 時 V_unified は1回計算し以降不変（`:67`）。

### §1-5 auto_growth / β frozen・runtime 可否 → 両方書換可（(B)案 feasible）
- canon: `auto_growth_rate=0.03`（`v19g_canon.py:80`）、`beta=1.0`。いずれも非frozen dataclass。
- runtime パス: `eng.grower.params.auto_growth_rate`（step が毎回読む `esde_v82_engine.py:152`）、`eng.physics.params.beta`（decay/cap が毎 step 読む）。**両方 runtime 書換可**。
- ⇒ Taka 保留の **(B) 案＝子限定 unfreeze で R を直接増幅** は機構上 feasible（auto_growth↑ で成長加速、β↑ で減衰保護強化、ただし β↑ は R cap=5/β を下げる副作用）。今回は採らないが判断材料として記録。R は §1-3 の通り plb 由来 topology に依存する点に注意。

### §1-6 B_Gen の n_core 支配 → 一致（データ確認）
- 式（`_compute_pbirth.py`）: `Pbirth=(1/C(5000,n))·rho^(n-1)·r_core^(n-1)·s_avg^(n-1)`、`B=-log10(Pbirth)`。同 n_core 内では `C(5000,n)` 定数ゆえ B 変動は rho/r_core/s_avg のみ。
- データ（`probe_data_properties.py`, §2-2 表）: **B_gen_CV = 0.047/0.018/0.025（n2/n4/n5）＝極小**。member 系 CV は大。⇒「同 n_core 内で B_Gen ほぼ不変、一意性は member 量にある」を確認。structural-strength 置換の根拠は成立。

---

## §2 新規 feasibility

### §2-1 coherence 駆動ログ＋性質 → 要設計変更
- **所在/解像度**: `v18_v_unified_concentration_*` は `per_subject`（birth/final の2点）と **`selfread/v18_window_trajectory_seed0.csv`（window=500step 解像度）**にある。**step10_trajectory には無い**。⇒ coherence 駆動は **500step cadence**（旧3チャネル案の 10step でなく）。10step ドライバ（n_core_member 等）と混用するなら解像度差を hold で吸収する設計が要る。
- **性質（弧 vs 平坦・n_core 別、seed0）**:
  ```
  n2: CID=31(/54) 点数med=2  弧あり(>=3pts&std>1e-3)=14/31 (45%)
  n4: CID=11      点数med=11 弧あり= 9/11 (82%)
  n5: CID=17      点数med=33 弧あり=16/17 (94%)
  ```
  **n2 は coherence が疎**（54 中 31 CID しか形成せず・中央値2点・弧45%）＝**順序(time-shuffle)を問えない**。**弧は n4/n5 にある**（中央値11/33点・弧82/94%）。
- **帰結**: 旧 §8 の smoke 想定「n2 のみ」は coherence チャネルと**不整合**。coherence の弧で経路依存を見るなら **smoke 対象を n5（次点 n4）に変更**すべき。n2 は driver が平坦ゆえこの設計では順序効果を観察できない。

### §2-2 structural-strength 算出＋同 n_core 内分散 → 可（条件付）
- **同 n_core 内分散 CV=std/|mean|**:
  ```
  n2(54): B_gen=0.047  s_avg=1.306 r_core=0.165 conc_final=0.464 k_final=0.000
  n4(11): B_gen=0.018  s_avg=0.185 r_core=0.187 conc_final=0.385 k_final=0.000
  n5(17): B_gen=0.025  s_avg=0.147 r_core=0.364 conc_final=0.461 k_final=0.000
  ```
- **member *数* は割れない**: `v18_v_unified_k_final` の CV=0（k_final＝n_core で同層一定）。Taka「CIDの強さはノード数だけでは決まらない」と整合＝N をノード数だけで決めると一意性が出ない。
- **member S/R/E 集約は割れる**: s_avg / r_core / concentration の CV は十分大。⇒ structural-strength を **member link S・core R・concentration（=member θ の集中度）から作れば同 n_core 内で一意**。per_subject 集約（s_avg, r_core, v18_concentration_birth）で算出可。per-member 分布（std）が要るなら `labels/per_label`・`network/` の追加読みが要る（未検証・実装時）。
- **可、ただし「member 数でなく S/R/E 量で作る」が必須条件**。N への scaling 値はここで確定しない（実装時 Web Claude 合意）。

---

## §3 §8 からの再確認（設計変更が触る点のみ）
- **K_sync runtime 単一形**: `K_sync(t)=0.1·(1+0.3·tanh(z))` は域 [0.07, 0.13]。runtime 書換可・alive 非破綻は §8 で実証済。**ただし**この域では kuramoto_r ≈ 0.04-0.06 でほぼ動かず（§1-3 表 K_sync=0.03→0.034 / 0.1→0.056）、しかも §1-3 で loop/R に伝播しない。⇒ チャネルは*技術的に可だが効果が二重に微弱*。
- **コスト再見積**: 動的1本化で param 更新は減。coherence が 500step 解像度ゆえ駆動更新点は親の window 数（n5 中央値33・最大50）。time-shuffle 構造（real + shuffle K×・null 毎再 run）不変。**smoke を n5（17CID）に変えると** child/CID=real(1)+shuffle(K=10)=11、子長=window数×500step。総 child-steps ≈ Σ_CID 11×(windows×500)。n5 windows 合計を粗く（17CID×median33×500×11）≈ 約3.1M child-steps＝§8 の n2 案(0.8M)より大きいが、約352 steps/sec・Pool24 で十数分オーダー（実 run せず計算）。確定は smoke 承認後。

---

## §4 不一致 / 不可時の帰結（勝手に代替実装せず合意待ち）

1. **【最重要】§1-3 が不一致 → 設計の核が崩れる**。coherence→K_sync は写像が clean でも *偏りを増幅しない*（K_sync は位相を揃えるが loop/R/cluster に伝播しない）。Taka の駆動原理「偏りを生む物理演算に変数を戻して偏りを増幅」を満たすには、**偏り（R/loop/cluster）を実際に動かすノブ**＝§1-3 の機構上 **plb（リンク誕生＝topology）** か **(B)案 auto_growth/β（R を直接掛ける、§1-5 で runtime 可）** が候補。K_sync（位相）はこの目的に対し空振り。**Web Claude へ差し戻し**: 単一チャネルを K_sync から *plb←coherence*（旧案で plb runtime 可は実証済）か *auto_growth/β←coherence* に張り替える設計再検討を要する。
2. **§2-1 coherence が n2 で平坦 → smoke 対象を n5（次点 n4）へ**。n2 は driver に弧が無く順序を問えない。
3. **§2-2 structural-strength は member 数でなく S/R/E で作る**（数は k=n_core で割れない）。
4. **§1-5 (B)案は runtime 可**＝R 直接増幅は技術的に可能。採否は Taka。

**いずれも実装せず、本資料を差し戻して合意を待つ。** child run / smoke は §1-3 の核問題が解けてから。

---

## 一文サマリ
v1302 設計監査（Code A, 2026-06-22, child run/smoke/実装ゼロ・read-only＋最小 probe）── 改訂設計の機構主張をコード検証。一致: §1-2 偏りエンジン連鎖（op4 R+=Σw閉路 / op7 S*=(1-decay/(1+βR)) / op5 ΔS=min(growth·R,L,1-S)）は child スタック(V82Engine.step_window:144-164)で実稼働・§1-4 V_unified=mean(exp(iθ)) over member は per-CID・§1-6 B_Gen は同n_core内ほぼ不変(CV0.02-0.05)。**不一致（核崩れ）＝§1-3: K_sync を10倍にしても loop/R/cluster 不変**（kuramoto_r は 0.034→0.209 と上がる＝ノブ生だが、loop/R はリンク topology=plb 由来で位相非依存ゆえ伝播しない／機構ギャップ）。過大表現＝§1-1 K_sync は全node生Σでなく近傍限定＋正規化、R cap は min(R,5)でなく beta_max/β。新規: §2-1 coherence は window(500step)解像度のみ・**n2 は弧45%/中央値2点で順序問えず弧は n4/n5**(smoke を n5 へ)、§2-2 structural-strength は member S/R/E で作れば同n_core内で割れる(member 数 k=n_core は CV0 で割れない)。§1-5 auto_growth/β は runtime 書換可((B)案 feasible)。**差し戻し: 単一チャネルを K_sync(位相・空振り) から plb か auto_growth/β(偏り=Rを実際に動かす) へ張替を要検討。child run は核解決後。判定は Taka。**
