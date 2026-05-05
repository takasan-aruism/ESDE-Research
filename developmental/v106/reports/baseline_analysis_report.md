# v10.6 random-baseline analysis report

*生成*: v106_baseline_analysis.py、Code A
*baseline 設定*: 一様分布 + 軸内 L1 正規化 (uniform) と 実 cid 軸内シャッフル (shuffled) の 2 種、numpy seed = 106

## 1. ランダムベースライン分布 (24 seeds 集計)

### uniform

- 全 atom × 24 seeds の rank_1_sim mean: **0.5264** (std 0.0847)
- 25%/50%/75% quantile: 0.4642 / 0.5175 / 0.5885
- min=0.3361, max=0.7629
- baseline で strong_24/24 達成 atom: **123** / 325
- baseline で 24/24 unmatched atom: **0** / 325

### shuffled

- 全 atom × 24 seeds の rank_1_sim mean: **0.5157** (std 0.0697)
- 25%/50%/75% quantile: 0.4694 / 0.5309 / 0.5666
- min=0.3176, max=0.6555
- baseline で strong_24/24 達成 atom: **85** / 325
- baseline で 24/24 unmatched atom: **0** / 325

## 2. 観察値 vs ベースライン (atom-level)

- 全 325 atom 平均 observed rank_1_sim: **0.4617**
- 全 325 atom 平均 uniform baseline rank_1_sim: **0.5264**
- 全 325 atom 平均 shuffled baseline rank_1_sim: **0.5157**

→ 観察値 - uniform = -0.0647
→ 観察値 - shuffled = -0.0540

### strong_24/24 atom 数の比較

- observed: **100** atoms
- uniform baseline: **123** atoms
- shuffled baseline: **85** atoms

### 24/24 unmatched atom 数の比較 (max_sim < 0.3 を全 24 seeds で達成)

- observed: **14** atoms
- uniform baseline strong-rate=0 atom 数: **27** atoms
- shuffled baseline strong-rate=0 atom 数: **49** atoms

## 3. category-level z-score

| category | n_atoms | obs_strong | uniform_strong | shuf_strong | obs - unif (atoms) | z_uniform | z_shuffled |
|---|---|---|---|---|---|---|---|
| LOG | 4 | 0 | 3 | 3 | -3 | -8.28 | -4.56 |
| VAL | 10 | 0 | 4 | 0 | -4 | -7.84 | -5.20 |
| SPC | 6 | 1 | 6 | 3 | -5 | -7.54 | -3.13 |
| EXS | 11 | 0 | 7 | 6 | -7 | -5.39 | -4.44 |
| TIM | 7 | 3 | 6 | 3 | -3 | -4.69 | -0.81 |
| COM | 12 | 5 | 8 | 4 | -3 | -4.63 | -2.21 |
| REL | 4 | 0 | 0 | 0 | +0 | -4.14 | -4.51 |
| CHG | 7 | 4 | 5 | 3 | -1 | -4.08 | -1.73 |
| WLD | 12 | 7 | 10 | 4 | -3 | -3.87 | -1.49 |
| ELM | 12 | 3 | 5 | 3 | -2 | -3.63 | -1.53 |
| ABS | 8 | 2 | 3 | 4 | -1 | -3.37 | -3.96 |
| FND | 24 | 4 | 12 | 10 | -8 | -3.11 | -2.45 |
| STA | 11 | 1 | 2 | 3 | -1 | -3.07 | -3.03 |
| EMO | 30 | 1 | 3 | 8 | -2 | -2.61 | -4.72 |
| NAT | 4 | 0 | 0 | 0 | +0 | -2.44 | +0.49 |
| ECO | 12 | 8 | 7 | 3 | +1 | -2.21 | -0.77 |
| BEI | 8 | 4 | 3 | 3 | +1 | -1.76 | -1.01 |
| PRP | 46 | 12 | 13 | 7 | -1 | -1.68 | +0.04 |
| ACT | 28 | 14 | 11 | 6 | +3 | -1.50 | -0.45 |
| SOC | 22 | 7 | 8 | 4 | -1 | -1.48 | -1.91 |
| COG | 13 | 4 | 5 | 5 | -1 | -0.24 | -1.76 |
| MAT | 6 | 1 | 0 | 0 | +1 | -0.05 | +1.20 |
| PER | 20 | 12 | 1 | 3 | +11 | +2.27 | +1.18 |
| BOD | 8 | 7 | 1 | 0 | +6 | +2.48 | +1.65 |

## 4. 真の finding atom (|z| > 2.0 かつ direction 24-seed 一貫)

- above_baseline (= ESDE が ランダムよりも特定 atom と接地): **47** atoms
- below_baseline (= ESDE が ランダムよりも特定 atom と非接地、構造的盲点): **176** atoms

### above_baseline (上位 z-score、ESDE 構造の真の偏り)

| atom | obs_mean | unif_baseline_mean | z_uniform | z_shuffled | both? |
|---|---|---|---|---|---|
| PER.smell | 0.616 | 0.466 | +6.46 | +3.46 | Y |
| PER.see | 0.608 | 0.467 | +6.13 | +2.46 | Y |
| CHG.begin | 0.660 | 0.560 | +6.12 | +0.43 | N |
| PER.odorless | 0.578 | 0.454 | +5.41 | +3.10 | Y |
| PER.hear | 0.579 | 0.469 | +5.19 | +1.47 | N |
| TIM.appear | 0.602 | 0.479 | +4.94 | +2.68 | Y |
| PER.taste | 0.627 | 0.522 | +4.37 | +3.30 | Y |
| BOD.ear | 0.606 | 0.512 | +4.33 | +1.53 | N |
| BOD.hip | 0.611 | 0.518 | +4.28 | +2.44 | Y |
| BOD.eye | 0.609 | 0.516 | +4.07 | +1.82 | N |
| PRP.young | 0.618 | 0.484 | +3.56 | +2.23 | Y |
| PER.blind | 0.550 | 0.459 | +3.53 | -0.28 | N |
| PRP.small | 0.608 | 0.528 | +3.38 | +3.09 | Y |
| ACT.leave | 0.551 | 0.477 | +3.30 | +1.85 | N |
| ACT.stand | 0.537 | 0.454 | +3.06 | +1.73 | N |
| BOD.face | 0.581 | 0.511 | +2.82 | +3.06 | Y |
| SOC.nation | 0.483 | 0.397 | +2.80 | +1.31 | N |
| BOD.head | 0.542 | 0.473 | +2.77 | +0.70 | N |
| STA.healing | 0.625 | 0.558 | +2.65 | +1.69 | N |
| PRP.weak | 0.468 | 0.396 | +2.62 | +0.47 | N |
| WLD.unskilled | 0.453 | 0.357 | +2.52 | -0.39 | N |
| PER.deaf | 0.523 | 0.465 | +2.45 | -1.38 | N |
| COG.mindless | 0.452 | 0.361 | +2.44 | -1.12 | N |
| SOC.individual | 0.450 | 0.363 | +2.42 | +0.45 | N |
| PRP.single | 0.481 | 0.397 | +2.39 | -1.64 | N |
| PER.soundless | 0.589 | 0.528 | +2.39 | +0.90 | N |
| SOC.rest | 0.541 | 0.457 | +2.37 | -0.01 | N |
| PER.touch | 0.524 | 0.455 | +2.37 | +1.82 | N |
| PER.feel | 0.530 | 0.491 | +2.26 | +0.05 | N |
| SOC.sleep | 0.499 | 0.415 | +2.22 | -0.58 | N |
| ELM.light | 0.570 | 0.511 | +2.20 | +2.54 | Y |
| SOC.public | 0.471 | 0.403 | +2.11 | -0.06 | N |
| SOC.awake | 0.488 | 0.411 | +2.08 | -0.95 | N |
| ACT.emit | 0.550 | 0.494 | +1.86 | +2.83 | N |
| ACT.sit | 0.565 | 0.518 | +1.86 | +2.28 | N |
| ECO.withdraw | 0.592 | 0.542 | +1.40 | +2.05 | N |
| COG.unlearned | 0.394 | 0.347 | +1.29 | -4.26 | N |
| COM.muteness | 0.379 | 0.336 | +1.14 | -6.21 | N |
| PER.numb | 0.392 | 0.353 | +1.05 | -4.08 | N |
| FND.unconscious | 0.459 | 0.424 | +1.04 | -3.58 | N |

### below_baseline (下位 z-score、構造的盲点)

| atom | obs_mean | unif_baseline_mean | z_uniform | z_shuffled | both? |
|---|---|---|---|---|---|
| VAL.incorrect | 0.291 | 0.534 | -15.82 | -6.08 | Y |
| VAL.truth | 0.385 | 0.624 | -15.74 | -5.49 | Y |
| EXS.void | 0.330 | 0.580 | -14.47 | -8.09 | Y |
| COM.conduct | 0.526 | 0.723 | -13.61 | -1.94 | N |
| FND.language | 0.425 | 0.619 | -12.74 | -3.24 | Y |
| TIM.past | 0.516 | 0.722 | -12.11 | -2.65 | Y |
| TIM.now | 0.436 | 0.619 | -12.10 | -3.98 | Y |
| COM.conflict | 0.280 | 0.560 | -11.83 | -7.57 | Y |
| STA.danger | 0.196 | 0.535 | -11.67 | -13.05 | Y |
| VAL.falsehood | 0.313 | 0.588 | -11.61 | -5.96 | Y |
| LOG.unreason | 0.219 | 0.501 | -11.35 | -12.22 | Y |
| ECO.loss | 0.235 | 0.533 | -11.17 | -12.05 | Y |
| WLD.nonscience | 0.344 | 0.632 | -11.16 | -6.49 | Y |
| STA.war | 0.223 | 0.530 | -11.02 | -12.20 | Y |
| FND.temporality | 0.447 | 0.627 | -10.60 | -5.13 | Y |
| EXS.death | 0.350 | 0.572 | -10.35 | -5.77 | Y |
| VAL.profane | 0.320 | 0.587 | -10.35 | -5.41 | Y |
| EMO.compassion | 0.317 | 0.585 | -10.32 | -5.45 | Y |
| ACT.destroy | 0.116 | 0.417 | -10.08 | -23.68 | Y |
| TIM.moment | 0.612 | 0.763 | -10.07 | -0.31 | N |
| ELM.sun | 0.488 | 0.648 | -9.84 | -3.65 | Y |
| FND.languageless | 0.396 | 0.643 | -9.72 | -5.01 | Y |
| VAL.evil | 0.179 | 0.484 | -9.44 | -12.24 | Y |
| EXS.life | 0.386 | 0.621 | -9.34 | -5.31 | Y |
| FND.time | 0.426 | 0.623 | -9.21 | -4.27 | Y |
| SPC.inside | 0.362 | 0.603 | -9.16 | -6.76 | Y |
| SPC.nowhere | 0.443 | 0.641 | -9.15 | -4.93 | Y |
| STA.peace | 0.439 | 0.658 | -9.04 | -4.65 | Y |
| EMO.love | 0.287 | 0.497 | -9.02 | -8.04 | Y |
| EXS.being | 0.484 | 0.681 | -9.01 | -4.82 | Y |
| WLD.religion | 0.340 | 0.588 | -8.97 | -5.87 | Y |
| EXS.presence | 0.406 | 0.601 | -8.94 | -4.54 | Y |
| SOC.criticize | 0.273 | 0.525 | -8.94 | -8.65 | Y |
| PRP.whole | 0.516 | 0.684 | -8.91 | -1.89 | N |
| CHG.retreat | 0.485 | 0.664 | -8.81 | -2.50 | Y |
| SOC.attack | 0.276 | 0.540 | -8.76 | -10.41 | Y |
| PRP.long | 0.457 | 0.581 | -8.48 | -2.56 | Y |
| EMO.hate | 0.222 | 0.434 | -8.35 | -15.30 | Y |
| SPC.reverse | 0.471 | 0.628 | -8.30 | -2.77 | Y |
| PRP.multiple | 0.514 | 0.672 | -8.15 | -0.70 | N |

## 5. v106_phase_report.md 修正提案

- 「mean_max_sim 0.608」を主結果から外す。 baseline (uniform) の rank_1_sim mean が同等以上の値を取り得るため、絶対値としては finding ではない。
- 真の finding は **観察値 - baseline の方向と大きさ**:
  - ESDE 観察値 (0.462) < uniform baseline (0.526) → ESDE 構造ベクトルは Atom と **ランダム期待値より低い類似度** を持つ。これ自体が観察。
- カテゴリ別 z-score 上位は: SOC, COG, MAT, PER, BOD
- カテゴリ別 z-score 下位は: LOG, VAL, SPC, EXS, TIM
- 真の finding atom (|z|>2 一貫): above 47 件、below 176 件

## 6. 出力ファイル一覧

```
outputs/main/baseline/
├── baseline_atom_alignment_seed{0..23}.csv (uniform + shuffled 統合)
├── baseline_atom_summary.csv               (atom × method × 24-seed 集計)
├── baseline_category_summary.csv           (category × method)
├── observed_vs_baseline_atom.csv           (atom レベル z-score 比較)
├── observed_vs_baseline_category.csv       (= category_summary)
├── true_finding_atoms.csv                  (|z|>2 かつ一貫した atom)
└── baseline_summary.json                   (実行メタ情報)
```
