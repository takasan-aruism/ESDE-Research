# v1302 (A)+(B)+canon 並走 smoke 設計監査資料（Code A → Web Claude / Taka）
**3条件（canon=無 / (A)scalar=親 structural-strength を初期 plb に / (B)topology=親コア+周辺 structural field を add_link 移植）を同じ step-0 枠で並走させる設計を検証＋(B) feasibility（field 抽出・add_link 移植・R 内生・null）＋(A) 確認。child run / smoke / 実装は実行ゼロ。read-only ＋最小 probe のみ。合意ゲート前で停止。**

*監査実施*: 2026-06-23、Code A。前提 = `cw_v1302_seed_audit.md`（step-0 transfer は plb に乗る・K_sync/θ 幻雑音・topology 移植は add_link で feasible）。判定（success/fail）は置かない。

---

## 自己規律宣言（4点）

**① 過去引用明記**
`cw_v1302_seed_audit.md`（§1-2 transfer は plb←s_avg 本体・K_sync←r_core 幻チャネル（単独0.108 n.s./非共線で真に痕なし）・θ 雑音・N は plb と共線−0.82／§1-3 structural-strength は S `v11_m_c_s_avg`/R `v11_m_c_r_core`/conc `v18_v_unified_concentration_birth` で一意・member E は clean 集約なし／§1-4 add_link で移植 feasible）／`cw_v1302_design_audit.md`（runtime 3ノブ全滅＝topology 上流・偏り R は閉路＝topology の関数）／step-0 `cw_step0.py`（誕生時 seeding 枠・Mantel＋shuffle 行列置換=無料・n_core 層化・創発署名）／`compute_structural(core,max_hops,link_adj,alive_n)`（`v918_memory_readout.py:1318` member から link 隣接 BFS）。§16（smoke 後停止、本書は smoke 前）。

**② Taka 逐語（原文）**
「AとBと同時にやればいいんじゃない？」「これまでの調査と合わせて間違いない方をえらんでくれりゃいい」「DNAみたいなもん…容易く改変できない」「CIDの強さは、ノード数だけでは決まらない」「子ESDE用の計算式だけ一時的に変える手もあり」「まぁ結果出せればなんでもいいので進めてみて」。

**③ 判定は Taka**。**④ 集約語禁止。crown 禁止。**

---

## 観察対象注釈ブロック
- 読＝frozen：engine ソース（`esde_v82_engine.py`/`esde_v43_engine.py`/`genesis_physics.py`/`genesis_state.py`/`realization.py`/`virtual_layer_v9.py`）、`v918_memory_readout.py`(compute_structural)、`per_subject_seed0.csv`、persistence（`link_life_log`/`label_member_persistence`/`link_snapshot_log`）、step-0 出力（`unified/v1301/cw_step0*`）。
- 書＝本監査資料＋ probe（`probe_b_transplant.py`、stdout のみ・データファイル非生成）。
- **child 実験 run（real/shuffle・smoke・署名生成・新規 Mantel run・親軌跡駆動）一切なし。** 親 physics/inject/ledger/state 非書込。probe は子 in-memory state への add_link のみ。

---

## 結論サマリ

| 区分 | 項目 | 判定 |
|---|---|---|
| §1-1 | 3条件が同一 step-0 枠に乗るか | **一致（可）**。worker 内条件分岐で同署名・同 Mantel・同層化 |
| §1-2 | (B) structural-field 抽出（frozen から） | **可（条件付）**。topology は復元可、**S・E は frozen に無い→shape-only 移植** |
| §1-3 | **(B) add_link 移植で R 内生・非破綻** | **可（レシピ確定）**。R は閉路から内生・要「alive_n 明示登録＋E/θ fresh」 |
| §1-4 | (B) の null | **無料（Mantel 行列置換）**。再 run 不要。構造 scramble null は別物・任意・別コスト |
| §1-5/§2-1 | (A) scalar 写像＋列 | **可**。S/R/conc 在り、plb 側集約 |
| §1-6 | 創発署名が移植の写しにならないか | **可・要 run 長**。移植閉路は減衰（probe で loops 6→0）ゆえ長 run で創発署名は seed の写しでない |

**総括的方向のチェック（Taka 要請）**: 「topology 上流→誕生時 seeding→3条件並走」の流れはコードと整合し**実装に進んでよい**。ただし**重要な caveat 2点**を下に明記（(B) 移植は減衰する初期条件＝step-0 transfer を担った plb は*持続パラメータ*で別物・(A) は step-0 の単一 DOF 微増強）。

---

## §1 設計監査

### §1-1 3条件が同一 step-0 枠に乗るか → 一致（可）
`cw_step0.py` の `worker(task)` に `task['cond']∈{canon,A,B}` を足し分岐：canon=現状の fresh init、(A)=`transform()` の plb を structural-strength 由来に差替、(B)=`run_injection()` を skip し親構造を instantiate（§1-3 レシピ）。署名（`worker` 末尾）・`analyse()` Mantel・n_core 層化は3条件共通で無変更。枠は壊れない。

### §1-2 (B) structural-field 抽出（frozen から）→ 可（shape-only）
- `compute_structural`（`v918_memory_readout.py:1318`）は **live state の `link_adj`＋`alive_n` 上の BFS**（core から max_hops 隣接を集める）。node 集合を返す（**S は返さない**）。
- **frozen からの復元**:
  - **コアリンク**: `label_member_persistence`（`label_id→link_id`・birth_window・n_core）＋ `link_life_log`（`link_id→node1,node2`）で **CID のコア node 対**が取れる。✓
  - **structural field（コア＋周辺）**: `link_snapshot_log`（window→alive link_id）＋ `link_life_log` を join すれば**当該 window の全 alive 隣接**が再構成でき、offline で `compute_structural` BFS 可。✓（join＋BFS の前処理が要る）
  - **S（リンク強度）と E（ノード E）は永続化されていない**（persistence にあるのは `age_r`＝R 系のみ）。⇒ **移植できるのは *形(node 対の配線)* だけ。S・E は fresh 値で埋める**（E fresh は設計既定、S も同様に fresh）。
- ⇒ (B) は「親の*道路網の形*を移植・S/E は新品」。閉路構造（R の源）は形に宿るので保たれる。**可、ただし shape-only と明記**。

### §1-3【最重要 probe】(B) add_link 移植で R 内生・非破綻 → 可（レシピ確定）
`probe_b_transplant.py`（2三角形+ブリッジ+周辺＝閉路含む9node/10link を子に instantiate、S=0.1 fresh、E=0.5 fresh）:
```
移植直後(step前): add_link 全成立=True alive_n=9 alive_l=10 | find_all_cycles loops=6
step_resonance 1回後: loops=6 maxR=3.0 meanR=1.8     ← R が移植閉路から内生で立つ(確認)
300step後: alive_n=9 alive_l=6 loops=0 maxR=0 meanR=0 labels=1 | alive非破綻=True
```
- **R は移植した形から内生計算される**（step_resonance で maxR=3.0）＝移植は R を運ばなくてよい（設計通り）。**確認**。
- **レシピ確定**: `add_link` は link を `alive_l` に入れるが **`alive_n` には登録しない**（engine_accel 版）。⇒ 移植は (1) `state.alive_n.add(n)` でノード明示登録＋`state.E[n]`/`theta` fresh、(2) `add_link(i,j,S_fresh)`、の順が要る。これを欠くとノード支持なしで崩壊（最初の probe で alive_n=0・labels=0 を実観測）。
- **非破綻**: 正しいレシピで alive_n=9 維持・label 形成。
- **観察された caveat（減衰）**: 孤立小 seed では移植閉路が 300step で loops 6→0 に減衰（後述 §1-6・総括 caveat）。

### §1-4 (B) の null → 無料（Mantel 行列置換）
- step-0 の null は D_parent 行列の置換（`cw_step0.py:163-164`）＝child 再 run なし。(B) も **同型で無料**: 親ごとに1子を topology-seed して D_child（署名距離）を得、D_parent（親の structural-field 距離 or M_c）と Mantel、null は D_parent 置換。**再 instantiate 不要**。
- 指示書 §1-4 の懸念「別親で再 instantiate」は**別種の null**＝「特定の配線 vs 次数保存ランダム配線」を問う **構造 scramble null**。これは子再 run が要る（有料）が、基本 transfer 検定には不要。**任意の追加対照**として別コスト計上すればよい。
- ⇒ **3条件すべて shuffle 無料**。コストは canon+(A)+(B) の real 子のみ（下記 §2）。

### §1-5 (A) scalar 写像 → 可（§2-1 と同）
per_subject の S(`v11_m_c_s_avg`)/R(`v11_m_c_r_core`)/conc(`v18_v_unified_concentration_birth`) で per-CID スカラ合成→**初期 plb**（§1-2 で効いたレバー、N は共線ゆえ避け plb 集約）。member E 欠は S/R/conc で代替。式・重みは実装時 Web Claude 合意。**算出列は揃う**。

### §1-6 創発署名が移植の写しにならないか → 可・要 run 長
- 署名は `worker` 末尾の創発人口統計（n_labels/mean_size/std_size/share_gini/mean_age、入力の写しでない）。(B) でも *run 後*の構造を見る。
- **移植 seed は減衰する**（probe: 孤立 seed で 300step に loops 6→0）。step-0 の run 長 35000step では初期 seed は遥か昔に消え、署名は創発＝移植の直写しでない。**run 長を step-0 並み（35k）に保てば写し懸念は回避**。

---

## §2 feasibility（(A) 側・コスト）
1. **(A) scalar 写像**: §1-5 の通り可、列揃う。
2. **コスト**: 3条件すべて shuffle 無料（§1-4）。child は real のみ：canon(数 seed)＋(A)(全 CID×seed)＋(B)(全 CID×seed)。step-0 実績 = 1002 child（n2/4/5×12seed+canon）を Pool24 完走。**3条件並走 ≈ step-0 の約2-3倍の real 子**（(A)+(B) で 2 系統、canon 少数）＝Pool24 で step-0 の2-3倍時間。**(B) の structural-field 抽出は前処理（persistence join＋BFS＋node remap）で1回計算・child run でない**。smoke は seed 小・n2 か n5 1層で概算（§4 で要相談）。

---

## §3 総括 caveat（実装に進む前に明示・判定でなく観察）

**caveat-1（最重要）: (B) の移植は*減衰する初期条件*で、step-0 transfer を担った plb は*持続パラメータ*＝機構が違う。**
step-0 の n2 transfer は plb（毎 step リンク誕生を一定にバイアスし続ける*持続*量）に乗った。(B) の移植 topology は誕生時の*一回きりの初期条件*で、probe では数百 step で減衰した。移植後の (B) 子は全員 canon plb で進化するので、seed の効果が消えると canon へ収束しうる。**∴ 機構上 (B) は (A) より持続 transfer が弱い可能性**。救いは auto_growth（`ΔS=growth·R`）が*移植閉路の高 R を掴んで S を太らせ自己強化*しうること（孤立 probe では減衰したが、実 child の realization 下で自己強化が勝つかは smoke 領域）。**これは設計の前提に関わるので smoke で必ず「(B) 子の seed 痕が run 後も残るか」を見る対象に。**

**caveat-2: (A) は step-0 の単一 DOF 微増強。** step-0 は既に plb←s_avg で r=0.49。(A)=plb←f(S,R,conc) はその plb スカラに R/conc を足すだけ（1 DOF に圧縮）。r_core は step-0 で K_sync 死レバー経由ゆえ痕なしだったが、生レバー plb 経由なら効く*可能性*はある（断定不可・smoke 対象）。**(A) が step-0 を大きく超える保証はない**＝過大期待しない。

**caveat-3: (B) は shape-only**（S/E 移植元なし・fresh）。親の S 値の大小は継がない。継ぐのは配線=閉路パターン。

---

## §4 不明点 / 実装影響範囲（事前報告）

**掘り出した不明点（Web Claude/Taka と詰めたい）:**
1. **smoke の層**: §1-2 seed_audit で transfer は n2、だが coherence(conc)は n2 で疎（前監査）。(A) の conc 成分を使うなら n4/n5、plb/s_avg 主なら n2。**smoke 第一層を n2 と n5 どちらにするか**（私見: transfer 実績の n2 を主、conc は S/R 主の補助に）。
2. **(B) の移植範囲の max_hops**: `compute_structural` の max_hops を n_core にすると n2 は 2-hop で小範囲。閉路を確実に含むため hop をもう1段広げるか。
3. **(B) structural-field の S/E fresh 値**: canon inject 値（S≈inject_link_strength, E≈inject_amount）に揃えるか、(A) と公平にするための初期化を統一するか。
4. **構造 scramble null（§1-4 の有料 null）を (B) に付けるか**: 「特定配線 vs ランダム配線」を分けたいなら要、コスト増。基本 Mantel だけなら不要。

**実装影響範囲（想定）:**
- **新規**: `unified/v1302/cw_v1302_abx.py`（3条件 worker・step-0 から fork）。**最大の新規 piece = structural-field 抽出前処理**（`label_member_persistence`＋`link_life_log`＋`link_snapshot_log` の join → offline BFS → 親→子 node remap）。ここが実装の主リスク（正しい window・正しいリンク・remap の取り違え）。
- **再利用（無変更）**: Mantel/shuffle/署名/n_core 層化（step-0 から）。
- **小変更**: (A)=`transform()` の plb 源差替。(B)=worker の init 分岐（run_injection skip→alive_n 登録＋add_link）。
- **書込先**: `unified/v1302/` のみ。親 frozen（per_subject＋persistence）は read-only。
- **リスク**: (i) structural-field 抽出の正しさ、(ii) caveat-1（(B) seed 減衰で transfer 出ない可能性）、(iii) (B) 署名の写し（run 長 35k で回避）。
- **コスト**: step-0 の約2-3倍（shuffle 無料維持）、Pool24。前処理は1回。

---

## 一文サマリ
v1302 (A)+(B)+canon 並走 smoke 設計監査（Code A, 2026-06-23, child run/smoke/実装ゼロ・read-only＋最小 probe）── 3条件を同一 step-0 枠で並走させる設計はコードと整合し**実装可**。§1-3 最重要 probe で **(B) add_link 移植は R を移植閉路から内生計算（maxR=3.0）・alive 非破綻**＝feasible、ただしレシピは「alive_n 明示登録＋E/θ fresh→add_link」（add_link 単体では alive_n 入らず崩壊を実観測）。§1-2 **structural-field は frozen(persistence join＋BFS)から *形* は復元可だが S・E は永続化されず＝shape-only 移植**。§1-4 **(B) null は Mantel 行列置換で無料**（構造 scramble null は別物・任意・有料）＝3条件すべて shuffle 無料で step-0 の約2-3倍コスト。**総括 caveat: (B) の移植は*減衰する初期条件*で step-0 transfer を担った plb=*持続パラメータ*と機構が違う＝(B) は持続 transfer が弱い可能性（auto_growth 自己強化が勝つかは smoke 対象）／(A) は step-0 plb←s_avg の単一 DOF 微増強で過大期待しない／(B) は shape-only**。実装の主リスク＝structural-field 抽出前処理（persistence join＋BFS＋node remap）。不明点＝smoke 層(n2/n5)・max_hops・fresh 初期値・scramble null の要否。**実装に進んでよいが上記 caveat と不明点を Web Claude/Taka と詰めてから。child run は合意後。判定は Taka。**
