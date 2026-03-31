# ESDE Autonomy Report

*Phase: Autonomy (v8.0–)*
*Status: v8.4 Local Wave 完了。空間的偏りに対するサイズ別応答を確認。density independence の空間版を観測。*
*Team: Taka (Director) / Claude (Implementation) / Gemini (Architecture) / GPT (Audit)*
*Started: March 21, 2026*
*Last updated: March 28, 2026*
*Prerequisites: Cognition complete (see ESDE_Cognition_Report_Final.md)*

---

## Cognition からの引き継ぎ

| 事実 | 検証規模 |
|------|---------|
| 物理層は動的平衡を自律維持 (sI ≈ 1.0) | 12 seeds, N=10000 |
| R+ ≈ 8 は N にスケールしない | N=5000 vs N=10000 |
| label は位相周波数グループ | 空間分析, seed=42 |
| label 生存法則: 遅い + 静か + 5 ノード | 1120 born → 9 survived |
| 動的平衡は seed 非依存（普遍） | 12 seeds 全一致 |
| budget=1 は配分比率であってエネルギーではない | v7.3 実装分析 |
| N は重要でない。ルールが構造を生む | v7.4 スケーリング |

---

## Version Changelog

| Version | Date | Core Addition | Key Result |
|---------|------|---------------|------------|
| v8.0 | 03-21 | Lifecycle logging | 48-seed 51,163 labels。niche isolation |
| v8.1 | 03-22 | Macro-node compression | Tripartite architecture |
| v8.1b | 03-22 | E4 hardcoded 撤去 | Constitution §3 修正 |
| v8.1c | 03-23 | S>=0.20 条件撤去 | 圧縮発動。仮想 -16% 問題 |
| v8.1d | 03-24 | alive_n 除外撤去 | 「速い label」化。48-seed PASS (+4.2%) |
| v8.2 A | 03-25 | O/H/V 観測 | vacancy = 死亡地帯。filter 撤回 |
| v8.2 B | 03-26 | maturation + rigidity | 相転移: 12→60 labels |
| accel v5 | 03-26 | L dict sharding | 速度劣化解消。13s/win 一定 |
| α test | 03-27 | α=0.05 感度テスト (48-seed) | trio 77%減。数量はα依存、性質はα非依存 |
| budget | 03-27 | Trio 局所予算解析 | suppression は density-driven。trio 固有作用なし |
| size | 03-27 | 単体サイズ質的分析 | 5-node は density-independent（非還元的差分） |
| dimension | 03-27 | ノード次元遷移分析 | 全 n→n+1 が質的相転移。各サイズが異なる存在様式 |
| v8.3 wave | 03-28 | External wave (bg_prob sin変調) | 48-seed。好況でlabel減、不況で増。5-node波非依存（T=10: 0.99×） |
| v8.3 collapse | 03-28 | 崩壊閾値スイープ (A=0.3-1.0) | 4段階: 平衡→再編→stress→collapse。物理層消滅で連鎖全滅 |
| 500win | 03-28 | 500win baseline 48-seed | share_retain 3相構造は偽信号（撤回）。6+を6/7/8/9に分解。5-nodeがretain底 |
| 6-9分解 | 03-28 | 6/7/8/9個別n→n+1差分 | 2つのフェーズ: 2→5手放す、6→9取り戻す。5-nodeが転換点 |
| v8.4 | 03-29 | Local Wave (Static Micro-Climate) | decay sin勾配。48-seed。3-nodeが最もoasis依存、5-nodeが最もneutral。territory比1.3×全サイズ一定 |

---

## v8.0 — Lifecycle (48-Seed, 51,163 labels)

**Niche Isolation（47/48 seed）:**
生存者の nearest_dist = 0.213（死亡者 0.084 の 2.5×）

**サイズ生存率:** 5-node 7.11%, 2-node 0.22%（32×）
**Carrying Capacity:** K = 12 ± 3.5
**認知的結合:** 5 ノードに物理的接続なし。frozenset で主張を維持。

**E1-E6:**

| ID | 名称 | Status |
|----|------|--------|
| E1 | 生存確率 sigmoid | PROVISIONAL |
| E2 | サイズ生存率 | SAFE |
| E3 | Carrying capacity K=12 | Phase B で K≈60 に変化 |
| E4 | Territory scaling | 参考値 |
| E5 | Coherence decay | QUARANTINED |
| E6 | Maturation contamination | PROVISIONAL |

---

## v8.1 圧縮 — 根本原因と修正

### 根本原因（48-seed 診断）

GPT 4 仮説:
- A. share 固定が主因 → **否定**（top_share 7.2% 低下）
- B. timing が主因 → **否定**（38/48 seed で同方向）
- C. macro-node 存在が ecology を変える → **肯定（根本原因）**
- D. R+ 二次効果 → **否定**（+2.6% で自然変動内）

```
alive_n からノード除外 → 物理層凍結 → macro-node が niche 永久占有
  → regular label -30.9%
```

### v8.1d 修正

macro-node を「強い label」から「速い label」に変更。
ノードは alive_n に残す。share は通常 link count。
48-seed 検証: +4.2%（PASS）。

---

## v8.2 Phase A — Vacancy 仮説の否定

| 指標 | 生存者 | 死亡者 |
|------|--------|--------|
| bin_occupancy | 0.112 | 0.041 |
| bin_vacancy | 0.317 | 0.528 |

生存者は占有された場所に生まれる。余白は死亡地帯。

Cross-tab:
| | occupied | empty |
|---|---|---|
| isolated | 5.2% | 0.6% |
| crowded | 3.1% | 0.1% |

### 概念と実装解釈の区別

Taka の原文は「未来 = 可能性の余白」としか言っていない。
「余白 = 生存に有利」は Claude の誤った拡大解釈。

vacancy birth filter: **撤回。**

---

## v8.2 Phase B — 生態系の相転移

maturation α=0.10, rigidity β=0.10（Phase A データから導出）。

|                  | Phase A | Phase B | 変化 |
|------------------|---------|---------|------|
| v_labels/seed    | 11.0    | 59.9    | 5.5× |
| survivors/seed   | 11.7    | 67.3    | 5.8× |
| occupied bins    | 12.2/64 | 41.9/64 | 3.4× |
| top_share        | 0.16    | 0.03    | 0.2× |
| birth rate       | 6/win   | 2.4/win | 0.4× |
| macro survived   | 0.0     | 13.7    | ∞    |

「少数の強い覇者」→「多数の弱い共存者」。

**Taka の解釈:**
「過去と現在しかなければ弱い支配が続くのは最も自然。
 過去に固執する人は現在の安定を強く意識する」

GPT 監査: Phase B は「Past は有効な存在論的要素である」ことが通った点が重要。

---

## 主体サイズ差の観測

| nodes | survived | rate | mean_age(surv) | role |
|-------|----------|------|----------------|------|
| 2 | 102 | 0.24% | 3.1 | prey |
| 3 | 112 | 3.82% | 38.9 | — |
| 4 | 544 | 23.2% | 81.3 | predator |
| 5 | 2,456 | 57.2% | 98.1 | apex predator |
| 6+ | 27 | 79.4% | 140+ | apex（母数不足） |

2-node = 高回転の泡。5-node = 系の骨格。質的に別の存在。

---

## Label 間関係 — 上位構造の自発的出現

### 基本構造

| 観測 | 結果 |
|------|------|
| 共存期間 | mean 53.8 win（長期共存） |
| 死亡の 92.6% | 他 label 近傍（競合） |
| 生存者分布 | gap ratio 368×（クラスタ化） |

### Stable Trio / Quad

| 構造 | 件数 | 平均共存 | 出現 |
|------|------|----------|------|
| Trio | 4,397 | 86.5 win | 48/48 seed |
| Quad | 6,383 | 78.2 win | — |

### Trio Quality

- 100% intact at w200（崩壊ゼロ）
- 内部に階層なし（center/edge 1.02×）
- Wide spread 0.2 rad（近接の偶然ではない）
- 合計 territory = 17.6 links

---

## Trio 監査（GPT 5 Questions）

### Q1. 形成条件
- 形成 window: median w120
- 34% のメンバーが形成時に newborn。82% が 5-node

### Q2. 死
- 200 window では崩壊ゼロ。228/1764 が death threshold 付近

### Q3. Trio 同士の競争
- 24% の trio ペアが 0.1 rad 以内。close trio 間に kill zone

### Q4. Birth suppression の原因（最重要発見）

| 因子 | 効果 |
|------|------|
| trio 近傍 | 1.5× |
| vacancy | **3.2×** |

**→ vacancy が支配因子。trio の抑圧は副次的。**

Cross-tab:
| | low vacancy | high vacancy |
|---|---|---|
| near trio | 9.93% | 3.29% |
| far from trio | 17.03% | 4.45% |

### Q5. 役割分化
- Early: 1.007× → Late: 1.002×。**分化なし。**

---

## Trio の本質（α感度テストによる判定）

### α=0.05 感度テスト結果（48-seed）

| 指標 | α=0.10 (baseline) | α=0.05 (test) | 変化 |
|---|---|---|---|
| Trios/seed | 161.4 | 37.2 | **-77%** |
| Survivors/seed | 67.5 | 42.9 | -36% |
| Trio member 率 | 90% | 68% | -22pt |
| Solo survivors | 334 (10%) | 660 (32%) | +97% |
| Formation window | w120 | w117 | 同等 |
| Displacement enrichment | 2.8× | 3.1× | 同等 |
| Trio effect (Q4) | 1.5× | 1.4× | 同等 |
| Vacancy effect (Q4) | 3.2× | **5.3×** | ↑↑ |
| Role differentiation | 1.002× | 0.988× | なし |
| Share CV (young/old) | 0.234/0.234 | 0.232/0.228 | 同等 |
| Near death (<0.005) | 228/1764 (13%) | 8/339 (2%) | ↓ |

### 判定: Case A 寄りの AB 混合

GPT 判定基準:
- Case A: trio 大幅減 → 副産物
- Case B: trio 残る → 構造的

結果は純粋な A でも B でもない。

**αが制御するもの: trio の「数量」**
- trio 数 77% 減（161→37/seed）
- trio member 率 90%→68%
- solo survivor が 2 倍に増加
- baseline の「生存 ≈ trio 所属」は α=0.10 の副産物

**αが制御しないもの: trio の「性質」**
- 残った trio は 100% intact、displacement 3.1×、形成時期同一
- Share CV（安定性）は α に非依存
- Vacancy effect はむしろ強化（3.2×→5.3×）

**結論:**
trio という関係パターン自体は構造的に存在する。
しかし「ほぼ全員が trio に属する」という現象は α の副産物。
trio は「生存の標準形態」ではなく「高 maturation 下での標準形態」。

### GPT アリズムメモとの接続

GPT §6 の指摘: 「trio の前に、単体サイズ差を差分として整理せよ」

α 感度テストはこれを裏付けた。
- trio 数は α で激変するが、5-node の生存優位性は両条件で支配的
- 差分の本質は trio 以前に、単体サイズにある可能性が高い
- trio は上位構造の「証明」ではなく「候補を探す観測対象」（GPT 結論と一致）

---

## Trio 局所予算解析（GPT 監査指示）

### 問い

trio 近傍で新参 label が死にやすいのは、trio が固有の関係作用を持つからか、
それとも trio の 3 label が局所 share/occupancy を消費して資源不足を作っているだけか？

### 結果（両条件で一致）

| 指標 | α=0.10 | α=0.05 |
|---|---|---|
| Trio budget footprint | 4.94% | 7.91% |
| Trio share effect | 1.3× | 1.5× |
| **Occupancy effect** | **3.2×** | **4.4×** |
| Death mechanism (near/far) | 同一 | 同一 |

### 2×2 テーブル（baseline）

| | low occ | high occ |
|---|---|---|
| low trio share | 3.5% | **14.8%** |
| high trio share | 3.8% | 9.4% |

### 判定: density-driven

Case A（trio share 圧迫）でも Case B（trio 固有作用）でもない。

- trio は budget の 5% しか食っていない → share 圧迫は主因でない
- near/far で death mechanism が同一 → trio 固有の kill はない
- occupancy が圧倒的支配因子 → **suppression は位相空間の密度構造そのもの**

**結論:** trio は「高密度領域に現れる安定 relation pattern」。
上位主体でも資源占有者でもなく、密度の結果として自然に生じる構造。
trio 追加分析は打ち止め。

---

## ノード次元遷移分析（最重要発見）

### 存在様式プロファイル（α=0.10 / α=0.05 両条件で安定）

| | 2-node | 3-node | 4-node | 5-node | 6+ |
|---|---|---|---|---|---|
| survival | 0.2% | 2-4% | 10-23% | 39-57% | 79-88% |
| mean_age | 3 | 9-39 | 58-81 | 91-98 | 126-140 |
| occ_dep | 1.5-2.0× | 0.8-1.3× | 0.9-1.1× | 0.9-1.0× | 1.2-1.5× |
| align_last | 0.60-0.62 | 0.38-0.49 | 0.30 | 0.26 | 0.22 |
| share_retain | ~1.0 | ~1.0 | 0.83-0.91 | 0.58-0.63 | 1.2-2.8 |

### 存在様式の型（GPT Task 2）

| size | 型 | 記述 |
|---|---|---|
| 2-node | environment-dependent bubble | 短命（age 3）。高 alignment。密度依存。環境なしに生存不能 |
| 3-node | unstable transitional | 中間寿命。alignment 低下開始。gap を見つけて生きるが脆い |
| 4-node | threshold phase | 長寿命開始（age 58-81）。密度非依存化。領土を長期保持可能 |
| 5-node | self-maintaining subject | 長命（age 91-98）。density-independent。**自分で生存条件を作る** |
| 6+ | higher-order candidate | 最長命。share が増える。母数不足（n=27-35） |

### n→n+1 遷移: 全遷移が質的相転移

| 遷移 | 獲得する能力 | baseline判定 | α=0.05判定 |
|---|---|---|---|
| 2→3 | **生存率** (+1000-1470%) | PHASE TRANSITION | PHASE TRANSITION |
| 3→4 | **寿命** (+100-500%). alignment 0.30 許容 | strong shift | PHASE TRANSITION |
| 4→5 | **density independence**. share を失う代償 | partial shift | PHASE TRANSITION |
| 5→6+ | **share 蓄積** (+113-339%) | PHASE TRANSITION | PHASE TRANSITION |

### share_retain の3相構造

- 2-3 node: share ≈ 1.0（手放せない。手放したら死ぬ）
- 4-5 node: share 0.6-0.9（**手放しても生きられる**）
- 6+: share > 1.0（**自然に集まる**）

### 核心の発見: 5-node の非還元的差分

**5-node が持っていて 2-node が持っていないもの = density independence。**

§2 テーブル（baseline）:
- 5-node survival: very low occ 59.1%, medium 57.6% → **帯間差なし**
- 2-node survival: very low 0.2%, medium 0.6% → **環境依存**

5-node は「share を失う代わりに、どこでも生きられる」。
2-node は「share を維持するが、良い場所にいないと死ぬ」。

アリズム的に: 2-node は「環境に存在させてもらっている」。5-node は「自分で存在している」。

### 4→5 の死に方

死亡者の share_last, align_last, terr_last は 4-node と 5-node で**同一**。
死に方は同じ。違いは「死ぬ確率」であって「死に方」ではない。

---

## v8.3 External Wave — 環境変動への応答

### 実装

bg_prob に sin 波を乗せた: `bg_prob = 0.003 × (1 + A × sin(2πw/T))`
engine 変更ゼロ。calibrate の window ループ内で BASE_PARAMS を毎 window 書き換え、step 後に復元。

Taka の比喩: T=10 は天候、T=50 は季節変動、T=100 は気候変動。データと整合。

### 48-Seed 結果（A=0.3, T=10/50/100）

**§1 物理層は短い波を吸収する**

| 条件 | alive_links | baseline 比 |
|---|---|---|
| baseline | 2966 | — |
| T=10 | 2960 | -0.2% |
| T=50 | 2853 | -3.8% |
| T=100 | 2834 | -4.5% |

stress dynamic equilibrium が波を食う。T=10 はほぼ完全吸収。T=100 で 4.5% 減。

**§2 Label 数は逆相関 — 好況で減り、不況で増える**

| 条件 | peak v_labels | trough v_labels | 差 |
|---|---|---|---|
| T=10 | 60.3 | 61.1 | -0.7 |
| T=50 | 55.6 | 59.7 | -4.1 |
| T=100 | 54.1 | 62.9 | **-8.8** |

好況 = リンク増 = 競争激化 = label 減。不況 = 既存 label 温存。

**§3 2-node は好況期に壊滅、4-5-node はむしろ安定化**

T=100 死亡 peak/trough ratio:

| size | ratio | 解釈 |
|---|---|---|
| 2-node | **2.09×** | 好況期に 2 倍死ぬ |
| 3-node | 1.06× | ほぼ無影響 |
| 4-node | 0.75× | 好況期にむしろ死ににくい |
| 5-node | **0.66×** | 好況期にむしろ死ににくい |

T=100 peak 生まれの 2-node: **全滅（4720 体中 0 体生存）**。
T=100 peak 生まれの 5-node: 51.7% 生存。

**§4 5-node の density independence は波周期に依存する**

| 条件 | peak survival | trough survival | ratio |
|---|---|---|---|
| T=10 | 58.03% | 58.35% | **0.99×**（波非依存） |
| T=50 | 53.24% | 60.02% | 0.89× |
| T=100 | 51.71% | 60.65% | 0.85× |

短い変動には完全に耐えるが、生涯スケール（T=100）の変動には応答する。
ただし「応答する」であって「消える」ではない。

**§5 周期と生涯スケールの一致が応答を決める**

5-node 寿命 98 win ≈ T=100。波の周期が生涯に一致すると応答最大。
2-node 寿命 3 win。T=10 でも人生 3 回分の変動。どの周期でも影響される。

### 崩壊閾値スイープ（T=100 固定、A=0.3/0.5/0.7/1.0、3 seed sanity）

| 振幅 | links | v_labels | 5n_surv | 6+_surv | 5n_wave | 判定 |
|---|---|---|---|---|---|---|
| baseline | 2966 | 59.8 | 57.2% | 79.4% | — | — |
| A=0.3 | 2834 | 58.4 | 55.6% | 94.4% | 0.85× | **STABLE** |
| A=0.5 | 2327 | 55.3 | 47.8% | 100% | 0.56× | **STRESS** |
| A=0.7 | 1374 | 44.4 | 31.7% | 66.7% | 0.49× | **STRESS** |
| A=1.0 | 19 | 4.1 | 0.0% | 0.0% | 0.00× | **COLLAPSE** |

### 崩壊の 4 段階

**段階 1: 平衡（A=0.3）** — 季節変動。ecology ほぼ無傷。

**段階 2: 再編（A=0.5）** — 異常気象。5-node の波非依存性が崩壊（0.56×）。
存在はするが「いつ生まれるか」が生存を左右するようになる。

**段階 3: Stress（A=0.7）** — 地球規模気候変動。5-node 半減（31.7%）。
ecology は縮小しつつも機能する。

**段階 4: Collapse（A=1.0）** — 大絶滅。links = 19（物理層消滅）。
仮想層は物理層なしに存在できない。全サイズ全滅。

**最重要発見: collapse は label ecology の内部崩壊ではなく、物理層の消滅による連鎖消滅。** 教訓 1「物理層は床」の直接証明。A=0.7 まで仮想層は「縮小するが機能する」。床が消えた瞬間に全てが消える。

---

## 500-Win 検証 — 観測長の影響

### 目的

200 window で得た結論が観測長に依存するかを検証する。
「500win が正しい」ではなく「何が変わり、何が変わらないか」を見る。

### 6+ 分解: 6/7/8/9 の実態（500win, 48-seed）

6+ をまとめていたことで構造が隠れていた。

| nodes | total | survived | rate | mean_age | share_retain |
|---|---|---|---|---|---|
| 5 | 10,075 | 3,382 | 33.6% | 190 | 0.537 |
| 6 | 40 | 19 | 47.5% | 296 | 0.609 |
| 7 | 19 | 15 | 78.9% | 339 | 0.761 |
| 8 | 11 | 11 | 100% | 241 | 0.742 |
| 9 | 3 | 3 | 100% | 247 | 0.622 |

n→n+1 の相転移パターンは 6 以降も続いている。
6+ でまとめたことで 6-node の 47.5% と 8-node の 100% が混ざっていた。

### share_retain 3 相構造: 撤回

200win で「相3（6+: retain > 1.0）」と報告したが、500win で全サイズ retain < 1.0。
**share が集まるサイズは存在しない。全員が失いながら生きている。**

| nodes | 200win retain | 500win retain | 判定 |
|---|---|---|---|
| 3 | 0.991 | 0.775 | 200win の偽信号 |
| 4 | 0.827 | 0.664 | 低下 |
| 5 | 0.571 | **0.537（最低）** | 底 |
| 6 | 1.456 | 0.609 | **200win の偽信号** |
| 7 | 0.911 | 0.761 | 回復 |
| 8 | 0.351 | 0.742 | 回復 |
| 9 | 1.649 | 0.622 | **200win の偽信号（n=2→3）** |

**500win で見える真のパターン:**
retain は 2→5 で単調減少。**5-node が底**（0.537）。
6→7→8 で回復する（0.609→0.761→0.742）。

「share が集まる」のではなく「5-node ほど失わない」。
5-node は「最も share を手放す」サイズ。

### 200win → 500win: 何が変わったか

**変わったもの（観測長に依存）：**
- survival 率: 全サイズで低下（5-node: 57.2% → 33.6%）。200win の偽生存者が剥がれた
- mean_age: 全サイズで上昇（5-node: 98 → 190）。真の長期生存者が見えた
- share_retain: 6+ の retain > 1.0 は偽信号。500win では全サイズ < 1.0
- 3 相構造: 存在しない。retain の連続的勾配がある

**変わらないもの（観測長に非依存）：**
- 存在様式の 5 型（bubble / transitional / threshold / self-maintaining / higher-order）
- n→n+1 遷移パターン（全て PHASE TRANSITION）
- displacement 階層（5-node が捕食頂点）
- density independence（5-node occ_dep ≈ 0.9×）
- retain の順序（2n > 3n > 4n > 5n、5n が底、6+ で回復）

### 教訓

**「存在の全体長が見えていない」（Taka）。**
200win は系の一部しか見ていなかった。
500win でも全体長が見えている保証はない。
観測長に依存する数値（survival 率、retain の絶対値）と
依存しない構造（型、遷移パターン、順序）を区別すべき。

---

## v8.4 Local Wave — 空間的偏りへの応答

### 実装

物理層の decay にx座標ベースの sin 勾配を適用。
`local_multiplier[i] = 1.0 + A × sin(2πx/side)`（x = i % 71）。
A=0.3（±30% decay bias）。全体平均 = 1.0（mean-preserving）。

oasis (mult < 1.0): x ≈ 0, 70 付近。decay 遅延。
penalty (mult > 1.0): x ≈ 35 付近。decay 加速。

engine / virtual_layer 変更ゼロ。genesis_physics._decay を monkey-patch。

### 48-Seed 結果

**§1 Survival — 中上位サイズの生存率が上昇**

| size | baseline | local A=0.3 |
|---|---|---|
| 2-node | 0.24% | 0.2%（変化なし） |
| 3-node | 3.82% | **5.2%**（+36%） |
| 5-node | 57.2% | **62.0%**（+8%） |
| 8-node | — | 100%（n=6） |

**§2 地理的分布 — サイズ別の空間偏り**

| size | mean_local_mult | 解釈 |
|---|---|---|
| 3-node | **0.900** | 最も oasis 依存 |
| 5-node | **0.955** | 最も neutral に近い（density independence の空間版） |
| 7-node | **1.010** | penalty 側にも存在 |
| 8-node | **1.007** | penalty 側にも存在 |

3-node = 最良の場所に集中。5-node = 場所を選ばない。7-8 node = penalty にすら存在。

5-node の空間分布: oasis 29.1%、neutral 64.9%、penalty **6.0%**。

**§3 frozenset内ノードの物理状態（主観 vs 客観）**

全サイズで oasis 側ノードの方がリンクが多い。ただしサイズが大きいほど差が縮まる。

| size | oasis_links/penalty_links ratio |
|---|---|
| 3-node | **2.9×**（oasis 側だけが実質的に生きている） |
| 5-node | 1.9× |
| 7-8 node | **1.3×**（penalty 側も物理的に機能） |

frozenset は不変だが、物理的な「重み」が oasis 側に偏る。
大きな label ほど偏りが小さい = penalty 側ノードも生きている。

**§4 territory 空間比率 — 全サイズで 1.3× 一定**

territory の oasis/penalty 比率が 2-node から 9-node まで**全て 1.3×**。
territory は「場の性質」であり、サイズに依存しない。
一方、ノードリンク比率はサイズ依存（§3）。
territory は場、リンクは主体。

**§5 frozenset 制約**

Gemini H2（Active Displacement / Migration）は現行モデルでは発生しない。
label のノード構成は birth 時に frozenset として固定。
「移動」に見えるのは選択的生存（粘菌と同構造）。

---

## 4 要素の現状

| 要素 | 状態 |
|------|------|
| 現在 | 存在（物理層 + 仮想層） |
| 過去 | 導入済（maturation + rigidity。相転移確認） |
| 未来 | **確定**: Future = n→n+1 差分。各遷移の具体的内容を観測的に記述済み |
| 外部 | **v8.4 局所波完了**。時間的変動（v8.3）+ 空間的偏り（v8.4）。次は動的勾配または第3次元 |

### Future（確定: 差分 = Future）

Taka 判断: **差分 = Future**。これは最初からそのつもりで置いている。
GPT 定義: 「上位機能次元が下位機能次元に対して持つ新しい行動可能性」

ここでいう次元は幾何学的次元ではなく、主体が持つ機能・行動様式の階層差を指す。

| 遷移 | Future（新しく可能になったこと） | 代償 | 信頼度 |
|---|---|---|---|
| 2→3 | alignment 低下耐性。寿命桁違い延長 | なし | レベル3 |
| 3→4 | share_retain < 1.0（保持資源減少耐性の開始）。寿命 50+ win | territory 縮小開始 | レベル3 |
| 4→5 | **density independence**（短周期で完全、長周期で応答するが消えない）。share_retain が底（0.54） | share が全サイズ中最大の減少 | レベル3 |
| 5→6 | **alignment 最低点**（0.264→0.181）。位相的最大分散で存在可能に。寿命 190→296 | 母数少（n=40） | レベル2 |
| 6→7 | **share retain 回復**（0.609→0.736）。死は二値的（share=0, terr=0 まで追い込まれる） | 母数少（n=19） | レベル1 |
| 7→8 | **territory 保持**の獲得（terr_last 6.9→9.3、+35%）。全生存 | 母数極小（n=11） | レベル1未満 |
| 8→9 | **territory 支配**（terr_last 9.3→16.3、terr_retain 0.83）| 母数極小（n=3） | 判定不能 |

**Future は時間の右側ではなく、機能次元の上側にある。**

**2 つのフェーズ:**
- **2→5: 手放すフェーズ。** alignment が下がり、share を失い、density independence を獲得する
- **6→9: 取り戻すフェーズ。** alignment が底を打ち、retain が回復し、territory を保持する

5-node が 2 つのフェーズの転換点。

share_retain の真のパターン（500win で確定、3 相構造は撤回）:
- 2→5 node: retain が単調減少。5-node が底（0.537）
- 6→8 node: retain が回復（0.609→0.742）
- **全サイズが share を失う。「集まる」サイズは存在しない**
- 差は「どれだけ失うか」の程度差のみ

### 6/7/8/9 の個別観測と n→n+1 差分（500win, 48-seed）

6+ をまとめることで構造が隠れていた。分解により n→n+1 相転移は 9-node まで継続。

| nodes | total | survival | mean_age | retain | align_last | terr_last |
|---|---|---|---|---|---|---|
| 5 | 10,075 | 33.6% | 190 | 0.547 | 0.264 | 6.2 |
| 6 | 40 | 47.5% | 296 | 0.609 | **0.181** | 6.9 |
| 7 | 19 | 78.9% | 317 | **0.736** | 0.199 | 6.9 |
| 8 | 11 | 100% | 241 | 0.742 | 0.217 | **9.3** |
| 9 | 3 | 100% | 247 | 0.622 | 0.247 | **16.3** |

**5→6:** alignment が 0.264→0.181 に急低下（QUALITATIVE）。位相的に最もバラけた状態で存在可能に。死亡者の age が 82→186 で死ぬまでの時間が 2 倍以上に延長。

**6→7:** share retain が 0.609→0.736 に回復。死亡時は share=0, terr=0 まで完全に追い込まれる。「生きるか完全消滅か」の二値的な生死。

**7→8:** terr_last が 6.9→9.3（+35%, QUALITATIVE）。territory を持ったまま長期存在する最初のサイズ。全生存（n=11）。

**8→9:** terr_last が 9.3→16.3（+76%, QUALITATIVE）。terr_retain 0.826（全サイズ中最高）。birth 時の territory をほぼ保持する。ただし n=3 で判定不能。

### 最大ノード数の成長（200win vs 500win）

| seed-max | 200win | 500win |
|---|---|---|
| 5-node | 50% | 21% |
| 6-node | 27% | 27% |
| 7-node | 17% | 27% |
| 8-node | 2% | 19% |
| 9-node | 4% | 6% |
| **mean** | **5.8** | **6.6** |

系は時間があれば大きな label を作り続ける。最大ノード数に天井があるかは現在のデータでは不明。

### 自我仮説（弱い保持、意味づけ保留）

GPT: 「自我は差分を保持し、その差分に基づく行動を継続することで立ち上がる可能性がある」

直接実装はしない。意味づけは保留し、観測記述を優先する。

---

## 速度改善

L dict が毎 window 100 万件ずつ肥大化。
Taka 提案: sharding + shard 内サンプリング。
結果: **13s/win 一定。16h → 3h。**
GPU は realizer の構造（rng.choice + dict）に向かず断念。

---

## 設計上の教訓

1. 物理層は床。床に手を加えると仮想層が荒れる
2. 48-seed データなしの設計は危険
3. 4 seed と 48 seed で解釈が逆転する
4. 概念定義を実装予測に変換する際に元の発言にない因果を付加しない
5. 設計すると間違える。観測すると正しい
6. Past のみの系は安定した弱者共存になる
7. vacancy は生存を予測しない。isolation は予測する
8. ESDE は「層を分ける」ことで前進してきた
9. v4.9 の失敗は層の誤配置
10. macro-node は「速い label」。「強い label」にしてはいけない
11. trio の数量は α の副産物。trio の性質は構造的（α 感度テスト判定済み）
12. 観測結果を人間的価値観で評価しない
13. 「90% が trio 所属」は α=0.10 下の現象。α=0.05 では 68%（α 依存）
14. α は trio の「数」を制御するが「質」は制御しない
15. vacancy effect は α 非依存（3.2×→5.3×）。位相空間構造は物理層由来
16. 差分の本質は trio 以前に単体サイズにある可能性が高い（GPT §6）
17. suppression は trio 固有作用ではなく density-driven（局所予算解析で確定）
18. trio budget footprint は 5-8%。suppression の主因と呼ぶには小さい
19. ノード数は量ではなく「存在様式の次元」。各 n→n+1 が質的相転移
20. 5-node の非還元的差分 = density independence（自分で存在する能力）
21. share_retain < 1.0 でも生存する能力は 4-node で開始し 5-node で顕著。意味づけは保留
22. 物理層の stress equilibrium は短い波を吸収する（T=10: links -0.2%）。長い波は吸収しきれない（T=100: -4.5%）
23. label ecology は環境変動と逆相関。好況で label 減、不況で label 増
24. 2-node は好況期に壊滅する。T=100 peak 生まれの 2-node 全滅（4720 体中 0 体）
25. 4-5-node は好況期にむしろ死ににくい。2-node 大量死で競争が緩和される間接効果
26. 5-node の density independence は条件付き: 短周期で完全（0.99×）、長周期で応答（0.85×）。消えるのではなく「応答する」
27. collapse は ecology の内部崩壊ではなく物理層の消滅による連鎖。A=0.7 まで仮想層は縮小するが機能する（教訓 1 の直接証明）
28. share_retain の 3 相構造は 200win の maturation contamination による偽信号。500win で撤回
29. 6+ をまとめると 6-node(47.5%) と 8-node(100%) の差が潰れる。今後は 6/7/8/9 を個別に扱う
30. 5-node は share_retain の底（0.537）。「最も手放す」サイズ。6+ は回復する
31. 観測長（window 数）に依存する数値（survival 率、retain 絶対値）と非依存の構造（型、遷移パターン、順序）を区別すべき
32. n→n+1 差分は 2 つのフェーズに分かれる: 2→5 は「手放す」（alignment 低下、share 喪失、density independence 獲得）。6→9 は「取り戻す」（alignment 回復、retain 回復、territory 保持）。5-node が転換点
33. 全 run をデフォルト並列化。逐次実行はクラッシュ確認の 3 window のみ。Taka の待ち時間は実験コスト。速度改善は超重要
34. territory の空間偏りはサイズ非依存（全サイズ 1.3×）。場の性質はサイズを問わない
35. oasis/penalty ノードリンク比率はサイズ依存（3-node 2.9× → 7-8 node 1.3×）。大きい label ほど penalty 側も物理的に機能する
36. frozenset 制約により label は移動しない。「移動に見える」のは選択的生存（粘菌と同構造）

---

## 開発ロードマップ

| Step | 内容 | 状態 |
|------|------|------|
| 1 | L dict sharding | **完了** |
| 2 | Relation layer 観測 | **完了** |
| 3 | Trio 監査 | **完了** — density-driven。trio 固有作用なし |
| 4 | α 感度テスト (α=0.05) | **完了** — trio 数量は α 依存、性質は α 非依存 |
| 5 | Trio 局所予算解析 | **完了** — suppression は density-driven |
| 6 | 単体サイズ差の質的分析 | **完了** — 5-node = density-independent（非還元的差分） |
| 7 | ノード次元遷移分析 | **完了** — 全 n→n+1 が質的相転移。存在様式の型を確定 |
| 8 | Future 設計 | **確定** — 差分 = Future（Taka 判断）。観測的記述完了 |
| 9 | External（全体波） | **完了** — 48-seed mass + 崩壊閾値。4 段階を特定 |
| 10 | External（局所波） | **完了** — decay sin勾配。48-seed。density independence 空間版を確認 |
| 11 | 動的勾配 or 第3次元 | **次** — 静的→動的。物理濃度場の検討 |
| 12 | 動的平衡の判断 | 全要素後 |

---

*v8.0 で生存法則を数式化。v8.1 で「物理層を凍らせると仮想層が荒れる」を発見。
v8.2 で Past を導入し生態系が相転移。trio 監査で suppression は density-driven と確定。
単体サイズ差の質的分析で全 n→n+1 が質的相転移、
5-node の非還元的差分 = density independence。Future = n→n+1 差分として確定。
v8.3 で External wave（bg_prob sin 変調）を導入。48-seed mass test で
天候/季節/気候変動に対応する 3 周期の応答差を確認。
崩壊閾値スイープで 4 段階を特定: 平衡→再編→stress→collapse。
collapse は物理層消滅による連鎖全滅（教訓 1 の直接証明）。
500win 検証で share_retain 3 相構造を撤回（200win の maturation contamination）。
6/7/8/9 を個別分解し、n→n+1 差分に 2 つのフェーズを発見。
v8.4 で Local Wave（decay sin 勾配）を導入。48-seed で空間的偏りへの応答を確認:
3-node が最も oasis 依存（0.900）、5-node が最も neutral（density independence 空間版）、
7-8 node が penalty 側にも存在。territory 比率は全サイズ 1.3× 一定（場の性質）。
oasis/penalty ノードリンク比率はサイズ依存（主体の性質）。
frozenset 制約により label は移動しない。「移動に見える」のは選択的生存。
次は動的勾配（物理濃度場）または第3次元設計。*
