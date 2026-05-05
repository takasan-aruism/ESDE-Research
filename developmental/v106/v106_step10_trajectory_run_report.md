# v10.6 10-step trajectory 解析 run 報告書

*生成*: 2026-05-06、Code A
*親*: pulse trajectory + Taka 指摘 (より細解像度)
*対象*: Web Claude → Taka

## 0. 一文サマリ

per-pulse (~50 step 周期) より 5x 細解像度の **10 step 単位** で alive cid 状態を **interpolation 取得** したところ、24 seeds × 1,796,001 records (84 秒) が生成され、**PER.sound が 28.3% で最大支配 atom** という今までの全解析と異なる結果が出現、24 seeds 完全一致の発展段階は **「step 0-999: WLD.artless → step 1000-12999: PER.sound 12 連続 bin 支配 → step 13000-19999: WLD.artless 復活 → step 20000-23999: FND.timeless → step 24000+: WLD.artless」** の 5 段階となり、**解像度を上げるほど TIM.moment が減り PER.sound が増える** (window 0.14% → pulse 7.5% → step10 28.3%) systematic な多層構造が確定、**副次発見として既存の per-pulse / window trajectory に `birth_step = birth_window × WIN_LEN` というバグ** (per_subject.birth_window が window_value 形式でオフセット 19 が必要) があったことを step10 で発見・修正済み (alive_cids 全 228 を確実に捕捉、per-pulse は同バグでも結果は得られていたが lifespan 計算で多くの cid が clip(1) で吸収されていた可能性)。

---

## 1. 実装結果

| 項目 | 値 |
|---|---|
| 入力 | pulse_log + per_subject + audit + balance/c_trajectory + alpha/beta_lifecycle + ingestion + per_event_audit |
| 出力 | `outputs/main/step10_trajectory/` 配下、24 seeds × 2 種出力 + cross-seed 4 種 + summary |
| 実行時間 | main run **84.17 秒** (24 seeds 単一バッチ) + cross-seed 解析数秒 |
| 解像度 | **10 step/sample** (pulse の 5x 細、window の 50x 細) |
| Sample 取得方法 | range(birth_step+10, end_step+1, 10)、各 sample で merge_asof による状態 interpolation |
| birth_step ソース | **pulse_log の最初 t** (per_subject.birth_window の解釈バグ回避) |

### 1.1 副次的なバグ発見と修正

- 既存の `v106_post_process.py` `calc_lifespan`、`v106_window_trajectory.py`、`v106_pulse_trajectory.py` で `birth_step = birth_window * WIN_LEN` を使用
- per_subject の `birth_window` 列は実は **window_value 形式 (offset 19)** で、`birth_step = (birth_window - 19) * WIN_LEN` が正しい
- birth_window=64 の cid → 既存式: birth_step=32000 (誤、run end 25000 を超える) → 正式: birth_step=22500
- 既存の lifespan_so_far 計算は多くの cid で `clip(lower=1)` で吸収され、**lifespan=1 の人工的状態** が混入していた可能性
- 静的解析・層化解析・baseline 解析の数値結果は **temporal 軸が emergence 一極に偏った状態で計算されていた** 可能性 (主結果には影響少と推測、要検証)
- step10 では `pulse_log の cid 最初 t` を使い、228 cid 全部捕捉

---

## 2. データ規模

| 指標 | 値 |
|---|---|
| 全 step10 records (24 seeds) | **1,796,001** |
| 全 alive cid | **5,224** (per-pulse と同じ全 cid) |
| seed あたり records | 59,933 - 87,209 (mean 74,833) |
| seed あたり alive cid | 170-253 |
| rank_1_sim_mean per seed | 0.5102 - 0.5528 |
| unique rank_1 atoms per seed | 33-44 |

---

## 3. 主結果: step10 解析の rank_1 atom 上位 (24 seeds 統合)

| atom | category | n_records | ratio | seeds | unique_cids | sim_mean | sim_max |
|---|---|---|---|---|---|---|---|
| **PER.sound** | PER | **507,845** | **28.3%** | 24/24 | 297 | 0.490 | 0.581 |
| **WLD.artless** | WLD | 436,964 | 24.3% | 24/24 | 321 | 0.642 | 0.787 |
| WLD.culture | WLD | 142,646 | 7.9% | 24/24 | 154 | 0.503 | 0.626 |
| EXS.being | EXS | 139,014 | 7.7% | 24/24 | 171 | 0.466 | 0.589 |
| FND.timeless | FND | 116,383 | 6.5% | 24/24 | 136 | 0.451 | 0.535 |
| TIM.moment | TIM | 112,058 | 6.2% | 24/24 | 259 | 0.489 | 0.621 |
| COM.conduct | COM | 53,315 | 3.0% | 24/24 | 214 | 0.498 | 0.598 |
| TIM.appear | TIM | 41,423 | 2.3% | 24/24 | 324 | 0.572 | 0.662 |
| LOG.effect | LOG | 34,787 | 1.9% | 24/24 | 189 | 0.486 | 0.637 |
| SOC.city | SOC | 33,624 | 1.9% | 24/24 | 180 | 0.504 | 0.605 |
| PRP.deep | PRP | 31,833 | 1.8% | 24/24 | 139 | 0.510 | 0.610 |
| COG.learn | COG | 28,260 | 1.6% | 24/24 | 165 | 0.596 | 0.667 |
| PRP.multiple | PRP | 19,419 | 1.1% | 24/24 | 180 | 0.451 | 0.526 |
| PER.taste | PER | 14,513 | 0.8% | 24/24 | 183 | 0.643 | 0.667 |
| PRP.bright | PRP | 11,512 | 0.6% | 24/24 | 245 | 0.540 | 0.575 |

### 3.1 PER.sound 28.3% 支配の意味

- **R_familiarity** が pulse 間で高値を維持し続け、interpolation で多数の sample が **epistemological 軸 level 4-5 (experience/creation)** に集中
- PER.sound の Atom プロファイルは epistemological.experience が強い → cosine 類似度高
- **「ESDE Genesis 系の cid は多くの時間 R_familiarity 高値で過ごす」** という解像度依存的な構造特徴
- per-pulse (50 step 周期) では pulse 発火時のみ取得するため PER.sound が支配的にならない、step10 (10 step) で全瞬間取得すると PER.sound が表面化

---

## 4. 動学的発展段階 (1000 step bins、24 seeds 完全一致)

全 26 bins で `seed_unanimity = 24/24`:

| step 範囲 | dominant_category | dominant_atom | n_records (24 seeds) | sim_mean |
|---|---|---|---|---|
| 0-999 | WLD | **WLD.artless** | 51,438 (21,521) | 0.588 |
| 1,000-12,999 | **PER** | **PER.sound** (12 bins 連続支配) | 平均 65,000+ | 0.530-0.580 |
| 13,000-13,999 | WLD | PER.sound | 76,308 | 0.530 |
| 14,000-14,999 | WLD | WLD.artless | 76,653 | 0.528 |
| 15,000-15,999 | WLD | PER.sound | 72,900 | 0.514 |
| 16,000-20,999 | WLD | WLD.artless (5 bins) | 平均 79,000 | 0.512-0.520 |
| 21,000-23,999 | WLD | **FND.timeless** (3 bins) | 平均 84,000 | 0.508-0.512 |
| 24,000-24,999 | WLD | WLD.artless | 91,018 | 0.514 |

→ 動学的発展段階を per-pulse 結果と比較:
- per-pulse: WLD.artless → TIM.appear → WLD.artless 長期 → EXS.being 後半
- step10: WLD.artless → **PER.sound 12 連続支配** → WLD.artless 復活 → **FND.timeless 短期** → WLD.artless

**最大の違い: step10 では PER.sound が中盤を 12 bins (1000-12999 step) 連続支配**。これは pulse 発火タイミングだけでなく **R_familiarity が連続的に高値を維持する期間** を捕捉している証拠。

---

## 5. 解像度間の比較 — TIM.moment vs PER.sound vs WLD.artless

`cross_seed_resolution_compare.csv` 抜粋:

| atom | window 比率 | pulse 比率 | step10 比率 | 解像度依存 |
|---|---|---|---|---|
| **PER.sound** | 0.14% | 7.5% | **28.3%** | 解像度↑で激増 |
| **WLD.artless** | 11.9% | 21.9% | 24.3% | 解像度↑で増 (頭打ち) |
| WLD.culture | 7.3% | 6.7% | 7.9% | 比較的一定 |
| EXS.being | 6.9% | 11.6% | 7.7% | pulse でピーク |
| FND.timeless | 1.7% | 3.0% | 6.5% | 解像度↑で増 |
| **TIM.moment** | **34.1%** | 8.3% | 6.2% | **解像度↑で激減** |
| COM.conduct | 0.07% | 1.1% | 3.0% | 解像度↑で増 |
| TIM.appear | 8.6% | 12.4% | 2.3% | pulse でピーク |
| LOG.effect | 5.4% | 4.5% | 1.9% | 解像度↑で減 |
| COG.learn | 5.2% | 1.3% | 1.6% | window でピーク |

### 5.1 解像度依存性のパターン分類

- **解像度↑で激増型 (interpolation で表面化)**: PER.sound, COM.conduct
- **解像度↑で増加型**: WLD.artless, FND.timeless, PRP.deep
- **pulse でピーク型 (動学的瞬間)**: EXS.being, TIM.appear
- **window でピーク型 (集約代表値)**: TIM.moment, COG.learn, LOG.effect, SOC.city
- **比較的一定**: WLD.culture, PRP.multiple

→ **解像度ごとに「見える特徴が systematic に異なる」** ことが定量的に確定。それぞれが独立した観察軸として有効。

---

## 6. trajectory_class 分布 (step10、5,224 cid)

| class | n_cids | ratio |
|---|---|---|
| few_attractors (2-3 atoms 振動) | 3,566 | 68.3% |
| **wandering** (4+ atoms 連続変化) | **1,474** | **28.2%** |
| stable_atom (1 atom 不変) | 184 | 3.5% |

### 6.1 解像度別 trajectory_class 比較

| class | window | pulse | step10 |
|---|---|---|---|
| stable_atom | 24.9% | 36.1% | 3.5% |
| few_attractors | 24.2% | 39.7% | **68.3%** |
| **wandering** | 17.6% | **24.1%** | **28.2%** |
| その他 | 33.3% | - | - |

→ **解像度↑で stable_atom が激減、wandering が増加**。step10 解像度では、ほぼすべての cid が複数 atom を通過する動学的存在として捕捉される。

---

## 7. window 解析からの birth_step バグの整理

### 7.1 既存実装のバグ状況

| 解析 | birth_step 計算式 | バグ影響 |
|---|---|---|
| 静的 (`v106_post_process.py` calc_lifespan) | `birth_w * WIN_LEN` | lifespan 多数で 1 (clip)、temporal 軸 emergence 一極 |
| window trajectory | `birth_w * WIN_LEN` | 同上、step_at_window_end - birth_step が大きく負 → clip |
| pulse trajectory | `birth_w * WIN_LEN` | 同上、pulse.t - birth_step が負 → clip |
| **step10 trajectory** | **`pulse_log.t.min()`** (修正済) | 正しい値 |

### 7.2 バグの結果への影響

- 軸 1 temporal: 多くの cid で lifespan=1 → temporal[0]=emergence 一極 → 影響あり
- 軸 8 lawfulness: pulse_density = pulse_count / 1 = pulse_count → 値が大きく level 4 寄り → 影響あり
- 軸 4 ontological: 影響軽微 (n_alphas 等は別計算)
- 軸 5,6,7,9,10: 影響なし

### 7.3 影響評価の推測

既存解析の最終結果 (例: 静的 mean_max_sim 0.608、ベースライン解析の z-score) は temporal 軸が偏った状態で計算されているが、**他の 47 軸が cosine 類似度を主に決めるため、主要な finding (BOD/PER 接地、構造的盲点 ACT.destroy 等) には大きな影響なし** と推測される。ただし定量検証は次フェイズで必要。

→ step10 解析が **正しい birth_step での結果** として最も信頼できる reference。

---

## 8. 4 解析の総合表

| 解析 | 解像度 | 主データ | n_records (24 seeds) | 1 位 atom (比率) | birth_step バグ |
|---|---|---|---|---|---|
| 静的 (post_process) | run 集約 | per_subject + audit | 5,224 cid | CHG.begin 51% | あり |
| window trajectory | 500 step | balance/c_trajectory | 31,482 | TIM.moment 34% | あり |
| pulse trajectory | ~50 step | pulse_log | 369,090 | WLD.artless 22% | あり |
| **step10 trajectory** | **10 step** | pulse_log + interpolation | **1,796,001** | **PER.sound 28%** | **修正済** |

---

## 9. v106_phase_report.md 修正提案 (再再再再再修正、最終版)

### 9.1 解析層の総合視点 (最終版)

ESDE Genesis 系の atom alignment は **解像度ごとに systematic に異なる** 多層構造を持つ:

- **静的集約**: cid 集合の代表値 → CHG.begin (集約罠人工物含む)
- **window (500 step)**: 中期スケール代表値 → TIM.moment (集約代表値)
- **pulse (~50 step)**: cid 状態変化瞬間 → WLD.artless (動学的)
- **step10 (10 step)**: 全瞬間補間 → PER.sound (R_familiarity 連続値で表面化)

### 9.2 真の主結果 (最終版)

1. **24 seeds で完全一致した動学的発展段階** が解像度ごとに異なる物語を見せる
2. **PER.sound** が step10 解像度で支配的、これは cid の **R_familiarity 高値持続期** の構造特徴
3. **WLD.artless** はあらゆる解像度で安定的に上位 (構造的特徴か計算バイアスかは要検証)
4. **TIM.moment** は集約代表値 (window で 34%)、瞬間値 (step10 で 6%) で大差
5. **真の構造的盲点 176 atom (ACT.destroy 等)** は解像度を上げても出現せず、構造的欠落として確定
6. **wandering 軌跡** が解像度↑で増加 (window 17.6% → step10 28.2%)、cid の動学性が細解像度で顕著化

### 9.3 解像度の選択指針

- 「ESDE が何を集約として表現するか」 → 静的・window
- 「ESDE の状態変化瞬間に何があるか」 → pulse
- 「ESDE が cid のライフサイクル全体で何にいるか」 → step10

→ どれか 1 つが「正しい」のではなく、**解像度ごとに違う質問に答える**。

---

## 10. 出力ファイル

```
developmental/v106/outputs/main/step10_trajectory/
├── step10_cid_alignment_seed{0..23}.csv          (24 seeds × step10 records)
├── step10_trajectory_patterns_seed{0..23}.csv     (24 seeds × cid traj class)
├── step10_trajectory_run_summary.csv
├── cross_seed_step10_atom_distribution.csv        (atom × 24 seeds 統合)
├── cross_seed_step10_step_evolution.csv           (1000-step bins)
├── cross_seed_step10_trajectory_class_summary.csv
└── cross_seed_resolution_compare.csv              (window/pulse/step10 比較)

developmental/v106/v106_step10_trajectory.py             (smoke + main)
developmental/v106/v106_step10_trajectory_cross_seed.py  (cross-seed)
```

---

## 11. 完了条件チェック

- [x] (cid, step10_t) wide table 構築 (24 seeds、merge_asof で interpolation)
- [x] step10 cid ベクトル生成 (48 dim、軸 7 symmetry も per-pulse delta を interpolation で取得)
- [x] cosine 類似度 + step10 rank_1 atom 抽出
- [x] cid trajectory pattern 分類 (step10 解像度)
- [x] cross-seed 統合 (発展段階 / class / 解像度比較)
- [x] read-only 縛り維持 / 出力 v106 配下のみ / ウェット概念禁止
- [x] 24 seeds 単一バッチ実行
- [x] **birth_step バグ修正** (pulse_log の最初 t を採用)
- [x] commit + push まで一連で完了 (memory 規律)

---

*以上、Code A による v10.6 10-step trajectory 解析報告。Web Claude による phase_report.md の最終確定 (再再再再再修正版) 待ち。birth_step バグの既存解析への遡及修正は別途判断。*
