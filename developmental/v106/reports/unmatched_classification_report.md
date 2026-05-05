# v10.6 unmatched classification report

*genesis_unique / language_specific / partial_match の集計*

## 1. 全体集計

| classification | count |
|---|---|
| language_specific | 562 |
| partial_match | 372 |

## 2. genesis_unique cid (max_sim < 0.3)

全 24 seeds 合計: 0 cid (全 cid 5,224 中)
## 3. partial_match cid (0.3 <= max_sim < 0.5)

全 24 seeds 合計: 372 cid
全 cid 比率: 7.1%

description (final_state) 別:
- final_state=reaped: 198
- final_state=hosted: 170
- final_state=ghost: 4

## 4. language_specific atom (全 cid との max_sim < 0.3)

全 24 seeds 合計: 562 (atom 単位、重複あり)
異なる atom: 35

category 別 (BOD/EMO 細分化が浮上するか):
- EMO: 104
- VAL: 95
- REL: 55
- SOC: 52
- FND: 49
- STA: 48
- COM: 40
- CHG: 28
- ACT: 24
- ECO: 24
- LOG: 24
- ABS: 14
- WLD: 3
- EXS: 2

最頻出 unmatched atom (全 24 seeds で何 seed unmatched か):

| atom | unmatched seed 数 | category |
|---|---|---|
| ACT.destroy | 24 | ACT |
| COM.conflict | 24 | COM |
| CHG.decay | 24 | CHG |
| STA.danger | 24 | STA |
| STA.war | 24 | STA |
| EMO.despair | 24 | EMO |
| ECO.loss | 24 | ECO |
| FND.information | 24 | FND |
| EMO.hate | 24 | EMO |
| REL.different | 24 | REL |
| LOG.unreason | 24 | LOG |
| REL.together | 24 | REL |
| VAL.evil | 24 | VAL |
| VAL.sacred | 24 | VAL |
| SOC.attack | 22 | SOC |

## 5. max_sim 分布 (全 cid)

- count = 5224
- mean = 0.6081, median = 0.6239
- min = 0.4117, max = 0.6949
- 25% = 0.5943
- 75% = 0.6475

max_sim ヒストグラム:

| 範囲 | count | ratio |
|---|---|---|
| 0.0-0.1 | 0 | 0.0% |
| 0.1-0.2 | 0 | 0.0% |
| 0.2-0.3 | 0 | 0.0% |
| 0.3-0.4 | 0 | 0.0% |
| 0.4-0.5 | 372 | 7.1% |
| 0.5-0.6 | 1022 | 19.6% |
| 0.6-0.7 | 3830 | 73.3% |
| 0.7-0.8 | 0 | 0.0% |
| 0.8-0.9 | 0 | 0.0% |
| 0.9-1.0 | 0 | 0.0% |
