# v10.6 prediction vs observation report

*v106_phase_design.md §7 の事前推測 vs 実観測*

## 1. ハブ cid の atom 偏り

**事前推測 (v106_phase_design.md §7.1)**: SOC.central / STA.persistent / BEI.integrated に偏る

**実観測**:

category 出現順 (rank_1 atom):

| category | count |
|---|---|
| COG | 35 |
| FND | 15 |
| EXS | 10 |
| WLD | 5 |
| PRP | 1 |

具体 atom (rank_1 atom 出現順):

| atom | count |
|---|---|
| COG.enlightenment | 35 |
| FND.timeless | 15 |
| EXS.being | 10 |
| WLD.culture | 5 |
| PRP.multiple | 1 |

**事前推測との比較**:
- SOC: **観測なし**
- STA: **観測なし**
- BEI: **観測なし**

→ 観測上の支配的 category: **COG** (count=35)

## 2. 5 パターン の atom 傾向

**事前推測**: 各 n_core 組み合わせ (5,5,5)/(2,5,5)/... ごとに異なる atom 傾向が出るはず

**実観測**:

| pattern | dominant top_atom | 出現 seed 数 |
|---|---|---|
| bridge | TIM.moment | 24/24 |
| capture | TIM.moment | 24/24 |
| core | FND.logic | 9/24 |
| near_core | TIM.moment | 11/24 |
| other | TIM.moment | 24/24 |
| peripheral | TIM.moment | 24/24 |

→ パターン間で top_atom が分岐するか否かで「n_core 組み合わせが atom alignment を分ける」仮説の検証可能。

## 3. mean_max_sim の seed 一貫性

- 24 seeds の mean_max_sim: mean=0.6078, std=0.0045
- → 極めて安定 (std < 0.02)。Genesis 系 v10.5 出力は seed をまたいで
    Atom 軸への接地度が一定。これは事前推測「seed ごとに大きくばらつく」とは逆。
