# v1304a Stage 3 観察報告 — lift × per-cid composition（smoke・停止・判定なし #12）

*作成*: 2026-07-02、Code A。**feasibility + smoke で停止（§7 指示）。full/3条件統計/判定に進まない。read-only・親へ feedback なし・物理非書込・#12。**
*成果物*: `v1304a_stage3_smoke.py` + `outputs/v1304a_stage3_*`（lift/composition/signatures/spread）。M=30・3群（canon/parent/shuffle）×正式4eye・360 child。

---

## 0. 結論（先に）
- **composition は per-cid の plb 変動を保った**（Stage 2 の mean-collapse を機構的に回避）：全群で plb 分布が ±15% 全域（min 0.00602 / max 0.00800）を張る。
- **だが親特異な集団構造乖離は立たない**：parent の集団署名は shuffle とほぼ同じ（parent−shuffle は概ね noise 床以下・符号も eye 間で不一致）。
- **機構的理由が判明**：**注意（lift）と s_avg（子物理に届く唯一のチャネル）が直交**（now_theta corr +0.07）→ lift 構成の plb 分布が uniform 構成とほぼ同じ → 集団が分かれない。
- ＝設計出口 **(b) 寄り（lift の量はわずかに効くが cid↔lift 対応は効かない）〜(c)**。判定は Taka。

## 1. feasibility（実測）
- **lift = mean_t(p_select×eligible)**：per-cid の濃淡が本物（now [0.37,1.74] std 0.20 / archive [0.19,1.09] / link [0.42,1.00] / bgen [0.00,2.16] std 0.48）。marginal で消えていた濃淡が残る（Step B 降格量の是正）。
- **45 支持内 lift 質量**：now 0.198 / archive 0.259 / link 0.234 / bgen 1.000（外れ質量を報告・45 はセンターの選別でなく記録の疎性）。
- **plb←s_avg per-cid 変換**：[0.00602, 0.00802]（±15%・cw_run 式）。

## 2. composition は per-cid 変動を保った（Stage 2 collapse 回避の確認）
群別 plb 分布（各子が自分の cid の s_avg から自分の plb）：
```
eye/group        mean     std      min      max
now_theta canon  0.00704  0.00067  0.00602  0.00801
now_theta parent 0.00707  0.00069  0.00602  0.00802
now_theta shuffle0.00712  0.00063  0.00602  0.00802
```
- 全群で plb が ±15% 全域を張る＝**Stage 2（1 群 1 scalar に潰れ母平均化）を回避**。狙い通り per-cid 変動は保たれた。
- **だが群間の plb 平均はほぼ同一**（canon 0.00704 / parent 0.00707 / shuffle 0.00712）＝lift 構成が plb 分布を uniform と分けていない。

## 3. なぜ分かれないか（注意 ⊥ s_avg・核心）
`corr(lift[eye,·], s_avg)` over 45 支持、と lift 加重 s_avg 平均 vs uniform：
| eye | corr(lift, s_avg) | lift加重 s_avg | uniform | 差 |
|---|---|---|---|---|
| now_theta | **+0.070** | 0.3020 | 0.2997 | +0.0023 |
| archive_theta_percentile | +0.288 | 0.3167 | 0.2997 | +0.0171 |
| link_rarity | +0.289 | 0.3111 | 0.2997 | +0.0114 |
| bgen_static_prior | −0.545 | 0.2497 | 0.2997 | −0.0499 |
- **注意（lift）は高 s_avg（＝高 plb）cid を優先選択しない**（now_theta はほぼ直交 0.07）。→ lift 比例で構成しても plb 分布は uniform 構成とほぼ同じ → 集団構造が分かれない。
- **センターが際立ちとして拾う軸（θ/link 稀さ）が、子物理に届く唯一の実証チャネル s_avg と直交している**のが根本。archive/link は弱い正相関（0.29）ゆえ僅かに plb がずれ、§4 の marginal な差に対応。

## 4. 個体群署名（parent−canon / parent−shuffle vs canon SE・t_mid 本体）
分離幅に期待値を置かず noise 床（canon の集団平均 SE = std/√M）との比で記述のみ（v3.2 規律）：
- **parent−canon**：多くの量で SE 以下。SE を超えるのは archive/link の link_density（~1.1×SE）・link の sync_order（~2×SE）・now/archive の mean_label_ncore（~1.4×SE）程度で**限定的・符号も eye 間で不一致**（link_density は archive/link 正・bgen 負、sync_order は now 正・他 負）。
- **parent−shuffle（親特異＝cid↔lift 対応が信号か）**：**概ね SE 以下**（now link −0.001 / sync −0.008、archive link −0.004 など）。数少ない例外（archive の mean_label_ncore ~2×SE）も一貫方向でない。
- ⇒ **わずかな差は lift の「量」（構成の集中度）由来で、cid↔lift「対応」由来でない**（parent と shuffle が分かれない）。設計出口 (b)。しかもその量効果自体が注意⊥s_avg ゆえ小さい。

## 5. 読み（判定でなく事実・#12）
- composition は狙い（per-cid 変動の保存）を機構的に達成したが、**今のセンターの濃淡（lift）は子集団を分けるほどの方向づけを持たない**（smoke first-look）。
- 根本は **注意が拾う軸（salience）と子物理に届くチャネル（s_avg→plb）の直交**。composition の形の問題でなく、「センターの注意が構造的個性化のチャネルに乗っていない」という**内容**の問題。
- これは設計 §6 の出口 (c)「濃淡は集団を分けるほどの方向づけを持たない＝それ自体が発見（動的統計・feedback の必要性に還る）」に接続する事実。ただし smoke ゆえ full（M 増・3条件分布距離・n_core 層化・other-parent）で確認前。判定は Taka。

## 6. 実施範囲・停止
- 実施：lift feasibility・composition smoke（360 child・M=30・3群×4eye・300step）・注意⊥s_avg 機構確認。read-only・親へ feedback なし・物理非書込・seed0・first-look。
- **していない**：full（M=45–90）・3条件分布距離統計・per-t 乖離推移・n_core 層化・other-parent null・成立判定（#12）。
- §7 通り feasibility+smoke で**停止**。full 自動進行しない。次（composition を full で確認 / 注意⊥s_avg を踏まえチャネル再考 / 出口(b)(c) と読む）は Taka/Web Claude 判断。

## 7. 一文サマリ
v1304a Stage 3 smoke（composition・read-only・停止・#12）── profile を lift(mean_t p×eligible・now[0.37,1.74]で濃淡本物)に置換し lift 比例で cid を M体サンプルし各子は v1302 実証チャネル plb←自分の s_avg(±15%)で per-cid knob にした結果、**composition は per-cid plb 変動を全群で保った(Stage2 の mean-collapse を機構的に回避)が、群間 plb 平均はほぼ同一で親特異な集団署名乖離は立たず(parent−shuffle は概ね noise 床以下・符号不一致・parent−canon も限定的)**、機構的理由は **corr(lift,s_avg)=now +0.07(直交)/archive・link +0.29/bgen −0.55＝注意(lift)が高s_avg(高plb)cid を優先選択せず lift 構成の plb 分布が uniform とほぼ同じ**＝センターが拾う salience 軸が子物理に届く唯一チャネル s_avg と直交、ゆえ composition の形でなく「注意が構造的個性化チャネルに乗っていない」内容の問題で設計出口(b)寄り〜(c)(濃淡は集団を分けるほどの方向づけを持たない=発見)、v3.2 規律で分離幅に期待値置かず noise床比で記述・smoke first-look ゆえ full 前・判定と次路線は Taka。
