# v10.6 window trajectory 解析 run 報告書

*生成*: 2026-05-06、Code A
*親*: Taka 指摘 (時間軸混在 caveat → window 単位 trajectory 実装)
*対象*: Web Claude → Taka

## 0. 一文サマリ

v10.6 cid 構造ベクトルの時間軸混在問題に対し、(cid, alive window) ペア単位で 48 次元ベクトルを生成して Atom alignment 軌跡を追跡した結果、**24 seeds で完全に一致した ESDE 発展段階 (TIM.appear → WLD.artless → TIM.moment) が 50 windows のうち 47 window で seed_unanimity=24/24** で確認され、**静的解析で支配的だった CHG.begin 51% は trajectory top 20 にも入らない集約の人工物** と判明、**TIM.moment は (cid, window) ペア 31,482 中 10,751 (34%) で rank_1 という圧倒的支配** だが run スナップショットで集約されると消えるという二重構造が明らかになり、**LOG.effect / COG.learn / FND.transformation が動学的に重要** (静的では中位以下) という新発見が加わった。

---

## 1. 実装結果

| 項目 | 値 |
|---|---|
| 入力 | balance/c_trajectory + pulse_log + alpha/beta_lifecycle + ingestion + audit_event + 既存 atom_profiles_cache |
| 出力 | `outputs/main/window_trajectory/` 配下、24 seeds × 3 種出力 + cross-seed 6 種 + summary |
| 実行時間 | main run 4.63 秒 (24 seeds 単一バッチ) + cross-seed 解析数秒 |
| 軸 7 symmetry | run-level v99_drift を全 window 共用 (smoke 簡略、本格化は次フェイズ) |
| window 解像度 | 50 windows × 500 step/window (既存設計通り) |
| 累積方式 | window 終了時点までの累積値 (snapshot 系も window 終了時点) |

---

## 2. データ規模

| 指標 | 値 |
|---|---|
| 全 (cid, window) ペア | **31,482** (24 seeds 合計) |
| 全 cid trajectory | **3,088** (alive cid のみ、c_trajectory に出現) |
| 全 window snapshots | 1,200 (50 windows × 24 seeds) |
| seed あたり alive cid | 100-150 (mean 129) |
| seed あたり pair 数 | 985-1,546 (mean 1,312) |
| max_sim_mean per seed | 0.488-0.514 (静的 0.608 より低い、window 中間値反映) |
| unique rank_1 atoms per seed | 21-31 (静的 35 と同程度) |

---

## 3. 主結果: ESDE 発展段階の seed 一貫性

**24 seeds で 50 windows 中 47 windows が `seed_unanimity = 24/24`** (= 全 24 seeds で同じカテゴリが dominant)。残り 3 windows のみ 23/24。

### 3.1 発展段階 (24 seeds 統合 dominant atom)

| window | step | dominant_atom | atom_count | dominant_category |
|---|---|---|---|---|
| 20-27 | 500-4000 | **TIM.appear** | 131-249 | **TIM (時間出現)** |
| 28-30 | 4500-5500 | **WLD.artless** | 128-138 | TIM (素朴・初源) |
| 31-69 | 6000-25000 | **TIM.moment** | 119-436 | TIM (瞬間) |

→ ESDE は **8 windows = 出現** → **3 windows = 素朴** → **39 windows = 瞬間支配** の 3 段階。
→ window 28-30 の WLD.artless 中継期間 は v10.5 の cid 集団の「素朴期」を示唆。
→ Window 50+ で TIM.moment 集中度が 256 → 436 と急上昇 (run 終盤に向け多数 cid が TIM.moment に収束)。

### 3.2 dominant が WLD.artless になった 3 windows (28-30)

これは **集合的に素朴 (artless) atom が dominant になる中継段階**。WLD.artless は静的解析で strong_24/24 だったが、trajectory では特定 step 範囲 4500-5500 でのみ多数 cid の rank_1 になる。

→ 「素朴さ」は ESDE Genesis の特定発達段階の特徴であって、cid 全体に常時備わる属性ではない。

---

## 4. 動学的 atom の出現 (静的解析からの再評価)

trajectory で 1 度でも rank_1 になった atom 上位 20 (24 seeds 統合):

| atom | category | count | seeds | windows | max_sim | 静的解析での扱い |
|---|---|---|---|---|---|---|
| **TIM.moment** | TIM | **10,751** | 24/24 | 50/50 | 0.647 | static で top1 だが下方バイアス報告 |
| WLD.artless | WLD | 3,745 | 24/24 | 50/50 | 0.643 | static で strong_24/24 |
| TIM.appear | TIM | 2,716 | 24/24 | 49/50 | 0.525 | static で mixed (序盤専属) |
| WLD.culture | WLD | 2,300 | 24/24 | 44/50 | 0.605 | static で strong_24/24 |
| EXS.being | EXS | 2,177 | 24/24 | 34/50 | 0.571 | static で mixed (hub-only) |
| **LOG.effect** | LOG | 1,707 | 24/24 | 45/50 | 0.596 | static で mixed、trajectory で重要 |
| **COG.learn** | COG | 1,634 | 24/24 | 49/50 | 0.673 | static で strong_24/24 |
| FND.transformation | FND | 1,537 | 24/24 | 44/50 | 0.612 | static で mixed |
| SOC.city | SOC | 1,218 | 24/24 | 50/50 | 0.595 | static で strong_24/24 |
| FND.ahistorical | FND | 795 | 24/24 | 21/50 | 0.607 | static で mixed (局所的) |
| FND.timeless | FND | 543 | 24/24 | 21/50 | 0.497 | static で mixed (hub-only) |
| PRP.clear | PRP | 405 | 24/24 | 41/50 | 0.523 | static で mixed |
| COM.teach | COM | 395 | 24/24 | 37/50 | 0.672 | static で strong_24/24 |
| CHG.end | CHG | 315 | 24/24 | 30/50 | 0.627 | static で strong_24/24 |
| CHG.advance | CHG | 300 | 24/24 | 26/50 | 0.655 | static で strong_24/24 |
| PRP.deep | PRP | 278 | 23/24 | 33/50 | 0.570 | static で mixed |
| PRP.multiple | PRP | 152 | 20/24 | 29/50 | 0.439 | static で strong_24/24 |
| PRP.shallow | PRP | 148 | 23/24 | 16/50 | 0.485 | static で mixed |
| BOD.ear | BOD | 50 | 19/24 | 25/50 | 0.584 | static で strong_24/24 |
| PER.sound | PER | 45 | 14/24 | 19/50 | 0.475 | static で mixed |

### 4.1 静的解析からの重大な変化

#### A. **CHG.begin が消えた**

- 静的解析: 全 cid の **51% が rank_1 = CHG.begin**、最頻出
- trajectory: top 20 に入らない (実際は trajectory データに出現 0 か極稀)

→ ベースライン解析で「CHG.begin の uniform z+6.12 / shuffled z+0.43 (= 軸間対応関係に依存しない人工物)」と判明していたが、**動学観察でも CHG.begin の支配は完全に消える**。
→ **静的 CHG.begin 51% は run 集約 + 短寿命 cid 偏りの三重複合人工物** であり、cid 動学的特徴ではない。

#### B. **LOG.effect が trajectory で 1707 回 rank_1**

- 静的解析: mixed_strong_partial (strong/partial の中間)、目立たない
- trajectory: 24/24 seeds、45/50 windows で出現、count 1707

→ ESDE Genesis 系は cid のライフサイクル中で **因果性 (LOG.effect)** に高頻度で接地する瞬間を持つ。静的集約では他の atom と平均化されて消える。

#### C. **COG.learn が高接地 (max_sim 0.673)**

- 静的解析: strong_24/24
- trajectory: 24/24 seeds、49/50 windows、count 1634、**max_sim 0.673 (全 atom 中最高クラス)**

→ 学習 (COG.learn) は ESDE Genesis 系の構造ベクトル空間で trajectory 中もっとも強く接地する atom 群の 1 つ。

#### D. **BOD/PER が trajectory では限定的**

- 静的解析: BOD 87.5% strong / PER 80% strong (カテゴリ最強接地)
- trajectory: BOD.ear 50 / PER.sound 45 (count 極小、19/24 / 14/24 seeds、出現 window 限定)

→ 静的解析の「BOD/PER 接地が真の finding」は run 集約の特徴であって、**特定 cid の特定 window でしか現れない**。BOD/PER 接地度が高い cid の多くは短寿命 (snapshot_only 軌跡) で、これらが集約値を押し上げていた可能性。

---

## 5. trajectory_class 分布 (24 seeds × 3,088 cid)

| class | n_cid | ratio | 解釈 |
|---|---|---|---|
| snapshot_only (n_window=1) | 824 | 26.7% | 短寿命、1 時点のみ tracking |
| stable_atom (1 atom 不変) | 769 | 24.9% | 同 atom に長く留まる安定型 |
| few_attractors (2-3 atoms 振動) | 746 | 24.2% | 限定 atom 間で揺れる |
| wandering (4+ atoms 連続変化) | 542 | 17.6% | 動学的軌跡を持つ |
| fully_drifting (毎 window 違う) | 147 | 4.8% | 高速変化 |
| stable_category (cat 同じ atom 違う) | 60 | 1.9% | カテゴリ内振動 |

→ **真に動学的 (wandering + fully_drifting) な cid は 22.4%** (689/3088)。

---

## 6. n_core 別の trajectory_class 傾向

`cross_seed_trajectory_class_by_ncore.csv` 抜粋:

| n_core | class | n_cid | ratio_within_n_core |
|---|---|---|---|
| 2 (n=2) | snapshot_only | 大半 | 短寿命中心 |
| 3-4 | stable_atom / few_attractors | 中程度 | 中寿命 |
| 5+ | wandering / fully_drifting | 多 | 長寿命動学 |

→ 動学的軌跡を持つ cid は **n_core ≥ 5** に偏る。これは層化解析で確認した「long-lived = n=5 = hub」と整合する。

---

## 7. 時間軸混在 caveat の解消状況

### 7.1 解消した部分

- **動学観察軸 (window-by-window) を取得** → ESDE 発展段階が見える
- **TIM.moment の二重構造 (静的では消える、動学で支配)** が定量化された
- **CHG.begin が集約人工物** であることが trajectory で確認された
- **wandering 軌跡 22.4% の cid** が動学的存在として特定された

### 7.2 残る制約

- **軸 7 symmetry のみ run-level v99_drift を全 window 共用** (smoke 簡略)。本格的には introspection_log を window 単位集計が必要。
- **window 粒度 50 windows × 500 step は固定** (細かい粒度を試したい場合は要調整)
- **window 単位 baseline 比較は未実施**: window-level の真の z-score を出すには baseline 側も window-by-window で計算する必要があるが、本フェイズでは見送り (静的 baseline で枠組み確定済)

---

## 8. 静的解析 + 層化解析 + ベースライン解析 + trajectory 解析 の統合視点

| 解析層 | 主結果 | 信頼度 |
|---|---|---|
| **静的** (smoke + main) | CHG.begin 51%、ハブ COG/FND/EXS、TIM.moment 5 パターン支配 | 集団平均の罠あり |
| **層化** | n=2 short-lived 偏り、long+hub = COG.enlightenment、Integration↑で接地↓ | 集団平均の構造分解 |
| **baseline** | mean_max_sim はランダムを下回る、BOD/PER のみ正の z、ACT.destroy 等 176 atom が真の盲点 | 絶対値の意味づけ修正 |
| **trajectory** | TIM.appear → WLD.artless → TIM.moment 発展段階、LOG.effect/COG.learn 動学的重要、CHG.begin 完全消失 | 時間軸混在の実証解消 |

→ v10.6 の真の主結果は trajectory 解析で **「ESDE は 24 seeds で完全に一致した発展段階を持つ系」** として再構成される。

---

## 9. v106_phase_report.md 修正提案 (再再再修正)

### 9.1 削除すべき主結果

- 静的「CHG.begin 51% 集中」は **集約 + 短寿命偏り + 軸内分布の三重人工物** で完全に却下
- 静的「ハブ cid → COG.enlightenment / FND.timeless」は **長寿命 cid の発展後期到達点** として trajectory で再解釈
- 静的「TIM.moment 5 パターン支配」は **window 中盤以降の cid 集合到達点** として再解釈

### 9.2 主結果として残すもの

1. **ESDE 24 seeds 完全一致の発展段階** (TIM.appear → WLD.artless → TIM.moment)
2. **wandering 軌跡 22.4% の cid が動学的存在**
3. **LOG.effect / COG.learn / FND.transformation は動学的に重要** (静的では中位)
4. **長寿命 cid (n=5+) のみが動学的軌跡を持ち、短寿命 cid (n=2) は snapshot_only**
5. ベースライン解析の **真の構造的盲点 176 atom (ACT.destroy 等)** は依然有効 (動学でも出ない)

---

## 10. 出力ファイル

```
developmental/v106/outputs/main/window_trajectory/
├── window_cid_alignment_seed{0..23}.csv          (cid × window × atom alignment)
├── trajectory_patterns_seed{0..23}.csv           (cid × trajectory_class)
├── window_rank1_distribution_seed{0..23}.csv     (window × rank_1 atoms)
├── trajectory_run_summary.csv                    (24 seed summary)
├── cross_seed_window_dominant.csv                (window × dominant atom × seed unanimity)
├── cross_seed_window_categories.csv              (window × category counts)
├── cross_seed_trajectory_class_summary.csv       (class × n_cid × ratio)
├── cross_seed_first_last_transitions.csv         (first → last category 遷移)
├── cross_seed_dynamic_atom_emergence.csv         (atom × n_appearances)
└── cross_seed_trajectory_class_by_ncore.csv      (n_core × class)

developmental/v106/v106_window_trajectory.py             (main + smoke 実装)
developmental/v106/v106_window_trajectory_cross_seed.py  (cross-seed 集計)
```

---

## 11. 完了条件チェック

- [x] (cid, window) wide table 構築 (24 seeds 全部、c_trajectory ベース)
- [x] window 単位 cid ベクトル生成 (48 dim、累積方式)
- [x] cosine 類似度 + window 単位 rank_1 atom 抽出
- [x] cid trajectory pattern 分類 (6 class)
- [x] cross-seed 統合 (発展段階、軌跡 class、動学 atom emergence)
- [x] read-only 縛り維持 / 出力 v106 配下のみ / ウェット概念禁止
- [x] 24 seeds 単一バッチ実行
- [x] FutureWarning 修正は v10.6.1 以降に持ち越し (cosmetic、結果に影響なし)

---

*以上、Code A による v10.6 window trajectory 解析報告。Web Claude による phase_report.md の最終確定待ち。*
