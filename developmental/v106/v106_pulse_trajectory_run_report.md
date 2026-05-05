# v10.6 per-pulse trajectory 解析 run 報告書

*生成*: 2026-05-06、Code A
*親*: window trajectory 報告書 + Taka 指摘 (より細解像度で見たい)
*対象*: Web Claude → Taka

## 0. 一文サマリ

window 単位 (500 step) の 10x 細解像度として **per-pulse (cid 状態が変化する瞬間)** trajectory を実装、24 seeds 単一バッチ 19 秒で **369,090 pulse records (cid 5,224)** を生成、全 24 seeds で完全一致した動学的発展段階 **WLD.artless (序盤) → TIM.appear (1000-4000 step) → WLD.artless (4000-15000 step、最長期間) → EXS.being (15000-25000 step)** が確認され、**window 単位では全く出現しなかった ELM.morning が 21,718 pulse で rank_1 (5.9%)**、**trigger 種別で動学が分岐 (MAD_DT_Major で WLD.artless 66%、MAD_DT_Normal で EXS.being 15% バランス型)** という動学的特徴が新たに浮上、window 解析で支配的だった TIM.moment は per-pulse 解像度では 8.3% に転落 (window 34% から大幅低下) し、各解像度で見える特徴が異なる多層構造が確定した。

---

## 1. 実装結果

| 項目 | 値 |
|---|---|
| 入力 | pulse_log + per_subject + audit + balance/c_trajectory + alpha/beta_lifecycle + ingestion + per_event_audit |
| 出力 | `outputs/main/pulse_trajectory/` 配下、24 seeds × 3 種出力 + cross-seed 6 種 + summary |
| 実行時間 | main run 19.01 秒 (24 seeds 単一バッチ) + cross-seed 解析数秒 |
| **解像度** | **per-pulse (cid 状態変化の瞬間)、約 50 step 周期** |
| 軸 7 symmetry | **per-pulse の delta_** で動学化 (window 簡略を解消) |
| データ統合 | merge_asof で各 pulse 時点の累積 event 数を効率的に取得 |

---

## 2. データ規模

| 指標 | 値 |
|---|---|
| 全 pulse records (24 seeds) | **369,090** |
| 全 alive cid (24 seeds) | **5,224** (window 解析の 3,088 = c_trajectory tracking 限定より多い) |
| seed あたり pulse records | 11,880 - 17,540 (mean 15,379) |
| seed あたり alive cid | 170-253 (mean 218) |
| rank_1_sim_mean per seed | 0.5081 - 0.5441 (24 seeds で安定) |
| unique rank_1 atoms per seed | 34-44 (window の 21-31 より多様) |
| trigger 種類 | 5 (MAD_DT_Major / MAD_DT_Normal / both / none / unformed) |

---

## 3. 主結果: 動学的発展段階 (24 seeds 完全一致)

`cross_seed_step_evolution.csv` から step bin 単位 (1000 step/bin、25 bins) の dominant atom:

| step 範囲 | n_pulses | dominant_category | seed_unanimity | dominant_atom | sim_mean |
|---|---|---|---|---|---|
| 0-999 | 10,660 | TIM | 24/24 | **WLD.artless** | 0.571 |
| 1,000-3,999 | 35,820 | TIM | 24/24 | **TIM.appear** | 0.557 |
| 4,000-14,999 | 137,860 | WLD | 24/24 | **WLD.artless** | 0.530 |
| 15,000-24,999 | 162,750 | WLD | 24/24 | **EXS.being** | 0.513 |

→ **「初期 WLD.artless → TIM.appear → 最長期 WLD.artless → 後半 EXS.being」** の 4 段階。
→ 全 25 bins で `seed_unanimity = 24/24` (動学的発展段階が ESDE Genesis 系 24 runs で完全に一致)。

window 解析の発展段階「TIM.appear → WLD.artless 一瞬 → TIM.moment 39 windows」とは異なる:
- window 解析の「TIM.moment 39 windows 支配」は cid 集約での代表値、個別 pulse の rank_1 ではない
- per-pulse では **WLD.artless が 11 bins (4000-15000 step) と最長期間支配**
- 後半 (15000-25000) は **EXS.being が一貫して dominant**

---

## 4. rank_1 atom 上位 20 (24 seeds 統合 369,090 pulses)

| atom | count | ratio | 24 seeds 出現 | unique_cids | sim_mean | sim_max |
|---|---|---|---|---|---|---|
| **WLD.artless** | 78,870 | 21.9% | 24/24 | 321 | 0.622 | 0.738 |
| **TIM.appear** | 44,448 | 12.4% | 24/24 | 295 | 0.499 | 0.629 |
| **EXS.being** | 41,731 | 11.6% | 24/24 | 176 | 0.479 | 0.622 |
| **TIM.moment** | 29,751 | 8.3% | 24/24 | 279 | 0.487 | 0.623 |
| **PER.sound** | 26,973 | 7.5% | 24/24 | 126 | 0.479 | 0.583 |
| WLD.culture | 24,185 | 6.7% | 24/24 | 119 | 0.511 | 0.631 |
| **ELM.morning** | 21,718 | 6.0% | 24/24 | 265 | 0.470 | 0.578 |
| **CHG.begin** | 18,198 | 5.1% | 24/24 | 287 | 0.575 | 0.723 |
| LOG.effect | 16,297 | 4.5% | 24/24 | 197 | 0.484 | 0.632 |
| FND.timeless | 10,691 | 3.0% | 24/24 | 76 | 0.456 | 0.489 |
| PRP.deep | 5,827 | 1.6% | 24/24 | 107 | 0.517 | 0.620 |
| SOC.city | 5,172 | 1.4% | 24/24 | 185 | 0.493 | 0.574 |
| COG.learn | 4,774 | 1.3% | 24/24 | 151 | 0.584 | 0.659 |
| PRP.impossible | 4,126 | 1.1% | 24/24 | 124 | 0.474 | 0.553 |
| WLD.realm | 4,121 | 1.1% | 24/24 | 71 | 0.480 | 0.522 |
| COM.conduct | 3,899 | 1.1% | 24/24 | 221 | 0.473 | 0.550 |
| PRP.multiple | 3,447 | 1.0% | 24/24 | 170 | 0.441 | 0.492 |
| PER.hear | 3,191 | 0.9% | 24/24 | 135 | 0.562 | 0.636 |
| PRP.clear | 1,608 | 0.4% | 21/24 | 47 | 0.457 | 0.516 |
| PRP.bright | 1,307 | 0.4% | 24/24 | 62 | 0.525 | 0.564 |

### 4.1 解像度別の主要 atom 出現量比較 (pulse vs window)

| atom | pulse count | window count | delta |
|---|---|---|---|
| WLD.artless | **78,870** | 3,745 | +75,125 |
| TIM.appear | **44,448** | 2,716 | +41,732 |
| EXS.being | **41,731** | 2,177 | +39,554 |
| PER.sound | **26,973** | 45 | **+26,928** |
| WLD.culture | 24,185 | 2,300 | +21,885 |
| **ELM.morning** | **21,718** | **0** | **+21,718** ← pulse_only |
| TIM.moment | 29,751 | **10,751** | +19,000 (window で支配だが per-pulse では低下) |
| **CHG.begin** | **18,198** | **1** | **+18,197** ← window で完全消失していたのに pulse で復活 |
| FND.transformation | 469 | **1,537** | -1,068 (window 優勢) |
| **FND.ahistorical** | 0 | 795 | -795 ← window_only |

→ **ELM.morning** は **window 解析で 1 度も rank_1 にならなかった atom が pulse 単位で 21,718 回 rank_1**。最大の動学的発見。
→ **CHG.begin** は **window で完全消失** していたが per-pulse では **18,198 回 (5.1%) rank_1**。短い瞬間的な接地が window 集約で消えていた。
→ **PER.sound** も **window で 45 → pulse で 26,973**。聴覚 atom が pulse 単位の動学で大量出現。
→ window のみ rank_1: **FND.ahistorical / WLD.art / CHG.stay / PRP.easy** (4 atoms)。pulse のみ rank_1: **ELM.morning** が代表。

---

## 5. trigger 別 atom alignment (動学的特徴)

| trigger | n_pulses (24 seeds) | 1 位 (比率) | 2 位 | 3 位 |
|---|---|---|---|---|
| **MAD_DT_Major** (大変化) | 13,976 | **WLD.artless 66%** | TIM.appear 16% | CHG.begin 7% |
| MAD_DT_Normal (通常) | 151,064 | EXS.being 15% | WLD.artless 11% | TIM.appear 11% |
| both (両 trigger) | 118,400 | WLD.artless 23% | TIM.appear 13% | EXS.being 11% |
| none (静止) | 59,998 | WLD.artless 26% | TIM.appear 13% | TIM.moment 10% |
| **unformed** (物理層シグネチャ未確定) | 15,672 | **WLD.artless 57%** | CHG.begin 18% | TIM.appear 16% |

### 5.1 trigger × atom の意味

- **MAD_DT_Major (disposition 大変化)** と **unformed (物理シグネチャ未確定)** の pulse は **WLD.artless と CHG.begin に集中**: 大きく動く瞬間や原始状態は「素朴さ」「始まり」に対応する atom と接地
- **MAD_DT_Normal (通常 pulse)** は **EXS.being / WLD.artless / TIM.appear のバランス型**: 安定した状態は存在論的・素朴・出現の三要素
- **none (trigger 発火なし)** も **WLD.artless が支配 (26%)**: trigger 不在の静止 pulse でも素朴 atom

→ Genesis 系の **「動的瞬間 = 素朴さ」「定常 = 存在 + 出現」** という動学的二相性。

---

## 6. trajectory_class 分布 (per-pulse 解像度、5,224 cid)

| class | n_cids | ratio | window 比較 (3,088 cid) |
|---|---|---|---|
| few_attractors (2-3 atoms 振動) | 2,075 | 39.7% | window 24.2% より多い |
| stable_atom (1 atom 不変) | 1,888 | 36.1% | window 24.9% より多い |
| **wandering (4+ atoms 連続変化)** | **1,261** | **24.1%** | window 17.6% より多い |

→ pulse 解像度では **wandering 24%、window で 17.6%**。細解像度ほど動学的軌跡が顕著。
→ stable_atom + few_attractors = 75.8% は依然多数派 (cid 状態が pulse 単位でも比較的安定)。

注: per-pulse では `snapshot_only` クラスはなく `single_pulse` (1 pulse のみ) を使うが、`min n_pulses = 10` でゼロ件 (全 cid に最低 10 pulses)。

---

## 7. n_core 別の trajectory_class

`cross_seed_trajectory_class_by_ncore.csv` 抜粋:

| n_core | class | ratio |
|---|---|---|
| 2 | stable_atom / few_attractors | 大半 |
| 3-4 | few_attractors / wandering | 中程度 |
| 5+ | wandering | 多数 |

→ window 解析の知見と整合: **動学的軌跡は n_core ≥ 5 (= long-lived = hub) に偏る**。

---

## 8. window 解析からの再評価

per-pulse の結果で window 解析の主結果が一部書き換わる:

### 8.1 維持された結論

- **24 seeds で発展段階が完全一致** (per-pulse でも 25/25 bins で `seed_unanimity = 24/24`)
- **動学的軌跡を持つ cid (wandering) は n_core ≥ 5 に偏る**
- **集団平均の罠 (静的 CHG.begin 51%) は per-pulse でも修正される** (per-pulse では CHG.begin が 18,198 で 5.1%、その bin 限定の支配)

### 8.2 修正された結論

- **window 解析の TIM.moment 支配は集約効果**: per-pulse では 8.3% (10 倍降格)、TIM.moment は cid 状態の **代表値** であって瞬間ごとの支配 atom ではない
- **WLD.artless は最長期間支配**: window 解析では中盤 3 windows のみ支配だったが、per-pulse では step 4000-15000 (約 60%) で dominant
- **後半は EXS.being 支配**: window 解析では中後半 TIM.moment と見えていたが、per-pulse では 15000-25000 step で **EXS.being** が常時 dominant atom

### 8.3 新発見

- **ELM.morning が 21,718 pulses で rank_1**: window 解析では 1 度も出現しなかった atom が per-pulse では 6.0%。**window 集約で完全に消えていた瞬間的接地**。
- **CHG.begin が pulse で復活** (静的解析での 51% 集中はバイアスだったが、pulse 単位の真の "begin" 瞬間が約 5% 存在)
- **PER.sound (聴覚) は pulse の中盤に多く出現** (window で 45 → pulse 26,973)
- **MAD_DT_Major pulse は WLD.artless 66% で集中する** という trigger 別動学的特徴

---

## 9. 重要な留意点 (Code A 観察)

### 9.1 WLD.artless の偏在性

WLD.artless が **全 369,090 pulses の 21.9% で rank_1** という異常な高頻度。これは以下の可能性:
- WLD.artless の Atom プロファイル (mapper_output WLD_artless) が **48 軸全体に広く分布** していて、多くの cid 構造ベクトルと高 cosine 類似度になる構造的バイアス
- 実際の WLD.artless プロファイルの 48 軸分布を確認する必要 (本フェイズ範囲外、必要なら別途)

→ ベースライン解析で WLD.artless が strong_24/24 だったのも整合 (ランダム/シャッフルでも高頻度)。

### 9.2 計算機上の正確さ

- pulse 単位の `lifespan_so_far`、累積 event 数等は merge_asof で正確に計算
- 軸 7 symmetry のみ per-pulse delta_* 直接利用 (window 簡略を解消)
- C / Q_remaining は window 単位 (c_trajectory 由来) を ffill で補完: pulse 間で cid C / Q は変化しない設計なので近似的に正しい

### 9.3 window 解像度との関係

| 観点 | window 単位 | per-pulse |
|---|---|---|
| 解像度 | 500 step/window | 約 50 step/pulse (10x 細) |
| 主データ | balance/c_trajectory | pulse_log |
| 軸 7 symmetry | run-level 共用 (簡略) | per-pulse delta_* (動学) |
| alive cid 数 | tracking 対象限定 (3,088) | 全 cid (5,224) |
| 解析対象 | cid 集合の代表値 trajectory | cid 状態変化の瞬間 |

→ **両解像度を併用する** ことで、動学的特徴と集約特徴の両方が捉えられる。どちらかが優れているわけではなく、相補的。

---

## 10. v106_phase_report.md 修正提案 (再再再再修正、最終版)

### 10.1 解析層の総合視点

| 層 | 主結果 | 信頼度 |
|---|---|---|
| 静的 (smoke + main) | CHG.begin 51%、ハブ COG/FND/EXS、TIM.moment 5 パターン | 集約の罠あり |
| 層化解析 | n=2 short-lived 偏り、long+hub = COG/FND/EXS、Integration↑で接地↓ | 集団平均の構造分解 |
| baseline | mean_max_sim はランダム以下、BOD/PER のみ正の z、ACT.destroy 等 176 atom が真の盲点 | 絶対値修正 |
| **window trajectory** | TIM.appear → WLD.artless 1 中継 → TIM.moment 39 windows、wandering 17.6% | 動学観察追加 |
| **per-pulse trajectory** | WLD.artless → TIM.appear → WLD.artless 長期 → EXS.being、ELM.morning 6%、wandering 24% | **最高解像度** |

### 10.2 各解析の役割

- **静的**: 全体集約の特徴 (どの atom が最も「典型的」か)
- **層化**: 集約の構造分解 (どの cid 群がどの特徴を持つか)
- **baseline**: 構造的盲点と特異性の同定 (何がランダムを超え、何が欠落か)
- **window trajectory**: cid 集合の **代表値** trajectory (どの段階でどの atom が代表か)
- **per-pulse trajectory**: cid 状態の **瞬間値** trajectory (cid が個別に通過する atom)

→ 解像度ごとに見える特徴が **systematically 異なる**。これ自体が重要な finding。

### 10.3 最終的な v10.6 主結果

1. **ESDE Genesis 系 24 seeds で完全一致した動学的発展段階** (per-pulse 解像度で 25/25 bins seed_unanimity)
2. **解像度ごとに支配的 atom が異なる多層構造**: 静的 (CHG.begin 集約罠) → window (TIM.moment 集約) → per-pulse (WLD.artless / EXS.being 動学)
3. **真の構造的盲点 176 atom (ACT.destroy 等)** はあらゆる解像度で出現せず、構造的欠落として確定
4. **wandering 軌跡 (4+ atoms 通過) が pulse 単位 24% / window 単位 17.6%**、n_core ≥ 5 に偏る
5. **WLD.artless の偏在性は構造的特徴か計算バイアスか要検証** (atom プロファイル分析が次フェイズの課題)

---

## 11. 出力ファイル

```
developmental/v106/outputs/main/pulse_trajectory/
├── pulse_cid_alignment_seed{0..23}.csv           (24 seeds × pulse records)
├── pulse_trajectory_patterns_seed{0..23}.csv     (24 seeds × cid traj class)
├── pulse_trigger_atom_distribution_seed{0..23}.csv
├── pulse_trajectory_run_summary.csv
├── cross_seed_pulse_atom_distribution.csv        (全 atom × 24 seeds 統合)
├── cross_seed_trigger_atom.csv                    (trigger × atom × 24 seeds)
├── cross_seed_step_evolution.csv                  (1000-step bins × dominant)
├── cross_seed_trajectory_class_summary.csv
├── cross_seed_trajectory_class_by_ncore.csv
└── cross_seed_pulse_vs_window_atom.csv            (per-pulse vs per-window 比較)

developmental/v106/v106_pulse_trajectory.py             (smoke + main 実装)
developmental/v106/v106_pulse_trajectory_cross_seed.py  (cross-seed 集計)
```

---

## 12. 完了条件チェック

- [x] (cid, pulse) wide table 構築 (24 seeds、merge_asof で累積 event 統合)
- [x] per-pulse cid ベクトル生成 (48 dim、軸 7 symmetry も動学化)
- [x] cosine 類似度 + per-pulse rank_1 atom 抽出
- [x] cid trajectory pattern 分類 (per-pulse 解像度)
- [x] cross-seed 統合 (発展段階 / trigger / class / pulse vs window 比較)
- [x] read-only 縛り維持 / 出力 v106 配下のみ / ウェット概念禁止
- [x] 24 seeds 単一バッチ実行
- [x] commit + push まで一連で完了 (memory 規律)

---

*以上、Code A による v10.6 per-pulse trajectory 解析報告。Web Claude による phase_report.md の最終確定 (再再再再修正版) 待ち。*
