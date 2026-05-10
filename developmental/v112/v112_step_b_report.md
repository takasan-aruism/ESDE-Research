# v10.12 Step B 完了報告 — 環境チェック詳細 + Step C 進行可否判定要請

*作成*: 2026-05-11、Code A
*親*: `v112_response_to_code_a.md` (即決事項返答 2026-05-11) + 第 4 版主題ドキュメント
*対象*: Web Claude (判断材料整理)、Taka (Step C 進行可否判定)
*位置づけ*: 即決事項返答で確定した trial-A 単独運用の **環境レベル最終確認**。実測結果から trial-A も母集団境界状態と判明、Step C 進行可否を上申。

---

## 0. 一文サマリ

即決事項返答 (2026-05-11、trial-B 不実施 / trial-A 単独 / Q2=977 緩和 / per-seed top_quartile / v108_original 流用) 全採用で Step B 環境チェック実施 (8.57 秒)、**実測 7 項目** (Q2_threshold 977 確認 / top_quartile per-seed mean 94.34 std 50.77 / trial-A 4 条件母集団 per seed mean **4.38** min 0 max 10 / formation_relation 取得 OK / v108_original bin_5+ 抽出 OK / natural baseline 5 種 per seed 16,111 events / 規模見積もり 1-2 分 + storage 2.1-2.4 GB) 完了、**Step A Q-A1 警告と異なる新規懸念 2 件発見**: (1) **trial-A も母集団境界状態** (per seed mean 4.38、9/24 seed で <3 events、14/24 seed で <5 events、§13.2 #2 母集団不足での判定不能ライン該当の可能性)、(2) **v108_original_bin_5+ (per seed ~21) vs v112_trial_A (per seed 4.38) の規模差 5 倍** (paired_d 比較の対称性に新規懸念)、Code A は §0.5 禁止事項に従い設計判断せず Web Claude/Taka 上申のみ、Step C (実装着手) 進行可否を判定要請、main 判定で seed 別 paired_d 信頼性が大きくばらつく見込み (24 seeds 内で母集団 0-10 events の幅)、Q-Z1 (Q3 維持時 per seed 3.9) から Q2 緩和で **わずか +0.5 events 改善のみ** で構造的母集団不足は解消されていないことが判明、留保事項 24 (新規) として「trial-A 4 条件 cond4 も bin_5+ 内で構造的に厳しい」を §3.3 で記録。

---

## §1 実測結果 7 項目

### 1.1 Q2_threshold 確認 (DC-A5)

| 統計 | 値 |
|---|---:|
| Q1 | 481 |
| **Q2 (median)** | **977** |
| Q3 | 2,485 |
| max | 25,000 |
| n | 5,224 |
| Q2_THRESHOLD_used | 977 (即決事項採用) |

→ Q2 = 977 で実測一致確認。

### 1.2 top_quartile_threshold per-seed (DC-A2)

| 統計 | 値 |
|---|---:|
| per_seed mean | 94.34 |
| per_seed std | 50.77 |
| per_seed min | 58.41 |
| per_seed max | 316.24 (seed 23 が外れ値) |

→ per-seed 採用が妥当 (std/mean = 0.54)、即決事項通り。

### 1.3 trial-A 4 条件母集団 (cond2 = Q2 緩和反映、最重要)

#### 24 seeds 集計

| 指標 | 値 |
|---|---:|
| **per seed mean** | **4.38** |
| per seed std | 2.89 |
| per seed min | **0** |
| per seed max | 10 |
| 24 seeds total | **105 events** |
| **< 3 events seeds** | **9/24** (37.5%) |
| **< 5 events seeds** | **14/24** (58.3%) |

#### per seed 詳細 (head 5)

| seed | n_total | cond1 | cond2 (Q2) | cond3 | cond4 | AND_1_2_3 | **trial_A_4cond** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 228 | 190 | 119 | 21 | 57 | 18 | **2** |
| 1 | 207 | 174 | 104 | 27 | 53 | 19 | **5** |
| 2 | 246 | 206 | 120 | 28 | 62 | 20 | **4** |
| 3 | 221 | 190 | 115 | 24 | 57 | 19 | **3** |
| 4 | 210 | 172 | 111 | 29 | 53 | 23 | **8** |

#### AND 連鎖 (24 seeds 合計、絞り込みプロセスの可視化)

| 段階 | events | 削減率 |
|---|---:|---:|
| 全 cid | 5,224 | - |
| cond1 (¬β) | 4,425 | 84.7% |
| AND_1_2 (+ Q2 long) | 2,249 | 50.8% (cond1 比) |
| AND_1_2_3 (+ n_core ≥ 5) | 488 | 21.7% (1_2 比) |
| **trial_A_4cond (+ top_quartile)** | **105** | **21.5% (1_2_3 比)** |

→ cond4 (top_quartile) で **78.5% 削減**、bin_5+ × 高 fam の同時要求が厳しい。

### 1.4 Q-Z1 vs Step B 比較 (Q3 維持 vs Q2 緩和)

| 指標 | Q-Z1 (Q3=2,485 維持) | Step B (Q2=977 緩和) | 改善 |
|---|---:|---:|---:|
| per seed mean | 3.9 | **4.38** | +0.5 events のみ |
| 24 seeds total | 94 | **105** | +11 events のみ |

→ **Q2 緩和でほとんど改善せず、構造的母集団不足は解消されていない**。原因は cond4 (top_quartile) が bin_5+ 内でも厳しいこと。

### 1.5 formation_relation 取得方法の動作確認 (DC-A5)

- seed 0: 129 cids with β intervals
- build_alpha_beta_intervals (v110/v112_step_z 流用) で取得 OK
- is_beta_member_at(cid, t, intervals) で target_step 時点判定 OK

### 1.6 v108_original bin_5+ 抽出動作確認 (DC-A3)

| seed 0 | 値 |
|---|---:|
| v108_original (top_k_100) total | 224 cid |
| bin_5+ filter 後 | **21 cid** (9.4%) |
| → per seed events 推定 | 21 × 25 atom = **525 events** |
| 24 seeds 推定 | ~12,600 events |

→ v108_original_bin_5+ は per seed mean ~21 cid (525 events)、v112_trial_A の per seed mean 4.38 (109 events) と **規模差 5 倍**。

### 1.7 natural baseline events 数 (per seed mean)

| source_event | events |
|---|---:|
| pulse | 14,963 |
| ingestion | 150 |
| alpha_formation | 578 |
| beta_formation | 270 |
| c_conversion | 150 |
| **total natural** | **16,111** |

→ natural baseline 計算は per seed 16K events 規模、performance_evaluator で参照可能。

### 1.8 規模見積もり再実測

| 区分 | 値 |
|---|---|
| v112_trial_A events total | 2,625 (105 × 25 atom) |
| v108_matched_pool_bin_5+ | 2,625 (同 cid pool) |
| v108_original total | 60,000 (v10.8 既存) |
| **total events 3 conditions** | **65,250** |
| baseline 計算 | 3 cond × 6 baseline × 24 seeds = **432 baseline runs** |
| main run 時間推定 | 1-2 分 (24 並列、v10.10 の 10.7% 規模) |
| storage per seed | ~25-35 MB |
| storage main total | ~600-840 MB |
| **累計 v107-v112** | **~2.1-2.4 GB** / 上限 6 GB (35-40%) |
| 打ち切り条件 50% | 大幅余裕 |

---

## §2 新規懸念 (Step A Q-A1 と異なる)

### 2.1 trial-A も母集団境界状態

#### 観察事実

| 評価軸 | 値 | 含意 |
|---|---|---|
| per seed mean | 4.38 | paired_d 信頼性懸念ライン |
| seed 別最小 | 0 | 一部 seed で main 判定不能 |
| **9/24 seed で <3 events** | 37.5% | §13.2 #2 (判定不能) 該当の可能性 |
| **14/24 seed で <5 events** | 58.3% | paired_d 推奨ラインを過半数の seed で下回る |

#### 構造的根拠

cond3 (n_core ≥ 5) と cond4 (top_quartile) の同時要求が bin_5+ 内でも厳しい:
- bin_5+ 全体で per seed 約 27 cid (cond3 該当)
- そのうち top_quartile (cond4) を満たすのは約 4-5 cid (per seed mean 4.38)
- → **bin_5+ × top_quartile = ESDE 全体の 1.7%** という極めて狭い集合

### 2.2 v108_original_bin_5+ vs v112_trial_A の規模差

| 区分 | per seed events | per cid 数 | 24 seeds total |
|---|---:|---:|---:|
| **v112_trial_A** | 109 (= 4.38 × 25) | 4.38 cid | 2,625 |
| v108_matched_pool_bin_5+ | 109 | 4.38 cid (同 pool) | 2,625 |
| **v108_original_bin_5+** | **525** (= 21 × 25) | **21 cid** | **12,600** |

→ paired_d 比較で **v112_trial_A vs v108_original_bin_5+ の n が 5 倍違う**。paired_d は per (seed, atom, path, window) で取るため n の絶対値差は影響しないが、**v108_original 内の cid 構造的多様性 (5 倍多い cid pool) と v112_trial_A の 1.7% 限定 cid pool の比較公平性** に新規懸念。

### 2.3 paired_d 信頼性の seed 別分布予想

per seed events 数:
- seed 0: **2 events** (n_b 不足)
- seed 1: 5
- seed 2: 4
- seed 3: 3
- seed 4: 8
- ...
- seed 別最小 0、最大 10、std 2.89

paired_d は v112_trial_A (105 events) vs v108_matched (105 events) 同 cid pool で計算するため計算自体は可能だが、**per seed の差分の std が小さい seed ほど paired_d 値の不安定性大** (n=2 では cohens_d ≈ 0/0 で計算不能、n=10 でも小サンプル)。

**main 判定では sign_test (n_improved_seeds) と bootstrap CI が指標 4 として加わる** ため、paired_d 単独の不安定性は集約される。ただし 9 seed が n<3 で paired_d 算出不能セルが多発する見込み。

### 2.4 §13.2 4 項目固定との関係

| #1 primary 条件不変 | trial-A 4 条件は変更しない、遵守 |
| **#2 母集団不足なら判定不能** | **9/24 seed で該当の可能性、要 Web Claude/Taka 判断** |
| #3 条件緩和版 appendix 化 | 緩和実装しない、遵守 |
| #4 緩和版混入なし | 該当なし、遵守 |

→ #2 への該当判断 (Step C 着手前 vs main run 後) を Web Claude/Taka に上申。

---

## §3 Code A 規律遵守の自己検証 (継続)

### 3.1 §0.5 禁止事項チェック

- [x] 主題ドキュメントの設計を勝手に変えていない
- [x] 観察軸を増やす方向への転換提案なし (本書は実測結果の警告)
- [x] 母集団不足を発見しても条件を勝手に緩めていない
- [x] 上申のみで実装に進んでいない (Step C 着手は Web Claude/Taka 承認後)

### 3.2 §35 メタ規律遵守

- §35 #9 (上位資料読了): 即決事項返答 + 第 4 版主題 + Step Z 結果 + Step A 認識確認を読了
- §35 #10 (観察軸を駆動要因にしない): 本書は単一勝負案 (trial-A) の母集団警告のみ、新観察軸提案なし

### 3.3 新規留保事項 24 (記録のみ、深掘りしない)

**留保 24**: trial-A 4 条件 cond4 (top_quartile) は bin_5+ 内でも厳しい構造

数値根拠 (Step B):
- bin_5+ × top_quartile = ESDE 全体の 1.7%
- AND_1_2_3 → trial_A_4cond で 78.5% 削減 (cond4 が主因)

**観察候補 (留保、深掘りしない)**:
- 候補 a: bin_5+ (中 cluster) cid は familiarity が中庸である傾向 (top_quartile に達する cid が少ない)
- 候補 b: top_quartile が seed 別に高めに出る場合の影響 (per seed std 50.77 で大きい)
- 候補 c: 上記の複合

→ v10.13 以降で「bin_5+ × familiarity 構造」の主題が立った場合の素材として記録、本主題では深掘りしない。

---

## §4 Step C 進行可否判定要請 (Web Claude/Taka)

### 4.1 候補 a: 規律 §13.2 #2 該当判断、main 判定で「判定不能」を許容しつつ Step C に進む

- main 判定で 9/24 seed の paired_d 不安定を観察事実として記録
- sign_test (n_improved_seeds) + bootstrap CI で集約評価、判定不能セルは除外
- 失敗パターン分析 (§7) で「母集団境界での paired_d 不安定」を記録
- **Code A 推奨**: 規律遵守と素材獲得の両立、即決事項返答 §1.3 (4 項目完全整合) を維持

### 4.2 候補 b: Step C 着手前に主題変更 (規律 §35 #6、終了条件前提崩れによる再開)

- trial-A も母集団境界と判明 → 主題前提が再度崩れた可能性
- 候補: cond4 を緩和、cond3 を緩和、別の cond 構造、または v10.12 主題自体の見直し
- ただし即決事項返答 §1.3 で「§13.2 #1 primary 条件不変」を遵守する場合、緩和は禁則
- 規律 §35 #6「前提崩れによる再開」は本ケースに適用可、要 Taka 判断

### 4.3 候補 c: trial-A も中止、v10.12 主題見直し or 中止

- trial-A も実用的でないと判断する場合
- v10.13 で別アプローチ (常駐アンカー、QC_cost、B 群) を検討
- ESDE 構造的事実として「v10.9 4 種設計表の 4 条件複合は paired_d 算出には母集団絶対不足」を確定

### 4.4 Code A 提案

**候補 a を推奨** (即決事項返答との整合性、規律 §13.2 完全遵守、観察事実獲得):
- 9/24 seed の paired_d 不安定は **観察事実として記録**、§13.2 #2 該当を main 判定で記述
- main run で trial-A 単独の sign_test + bootstrap CI を集約評価
- 失敗パターン (§7) で「母集団境界状態」「v10.9 4 種設計表の構造的制約」を素材化
- v10.13 主題候補で 4 種設計表の見直し or pulse 観察軸活用を Taka 判断

ただし設計判断は Web Claude/Taka、Code A は実測結果と候補提示のみ。

---

## §5 Step C 進行時の実装計画 (候補 a 採用時、参考)

### 5.1 主要モジュール

```
v112_receptive_cid_detector.py (trial-A 単独)
v112_atom_event_generator.py (3 種類: v112_trial_A / v108_matched_pool_bin_5plus / v108_original_bin_5plus)
v112_baseline_recalculator.py (3 condition × 6 baseline = 18 baseline)
v112_performance_evaluator.py (paired_d + sign_test + bootstrap CI、n_b 不足セル除外)
v112_success_judgment.py (trial-A 単独判定 = v10.12 全体判定)
v112_post_process.py (orchestrator、24 seeds 並列、trial-A 単独)
```

### 5.2 母集団不足セル (n_b < 3) の扱い

- paired_d 計算時に n_b 不足セルは exclude
- 集約 sign_test では n_evaluable_seeds として記録
- bootstrap CI も n_evaluable に基づく
- 主題完了報告で「seed 別 evaluable 状況」を §11 で記述

---

## §6 一文サマリ (再掲)

即決事項返答 (2026-05-11) 全採用で Step B 環境チェック 7 項目実施 (Q2_threshold 977 確認 / top_quartile per-seed mean 94.34 / **trial-A 4 条件母集団 per seed mean 4.38、9/24 seed で <3 events、14/24 seed で <5 events、24 seeds total 105 events** / formation_relation 取得 OK / v108_original bin_5+ 抽出 OK / natural baseline 16,111 events/seed / 規模 1-2 分 + 2.1-2.4 GB)、**Q2 緩和で per seed +0.5 events のみ改善で構造的母集団不足は解消されず**、AND 連鎖で cond4 (top_quartile) が 78.5% 削減の主因と判明 (bin_5+ × top_quartile = ESDE 全体の 1.7%)、Step A Q-A1 警告と異なる **2 件の新規懸念**: (1) trial-A も §13.2 #2 母集団不足での判定不能ライン該当の可能性、(2) v108_original_bin_5+ (per seed 21) vs v112_trial_A (4.38) の規模差 5 倍で paired_d 比較公平性に懸念、留保事項 24 (新規、bin_5+ × top_quartile の構造的厳しさ) を §3.3 で記録、Code A は §0.5 禁止事項遵守で設計判断せず Web Claude/Taka に Step C 進行可否を上申、判定対象は候補 a (規律 §13.2 #2 該当判断、判定不能を許容しつつ Step C 進行、Code A 推奨) / 候補 b (主題変更、規律 §35 #6 前提崩れ再開) / 候補 c (trial-A 中止、v10.12 主題見直し)、上記 3 候補から Web Claude/Taka 判断後に Step C (実装着手) または主題見直しに進む、Step B 完了条件チェック 7 項目すべて達成、Code A 提案は候補 a (即決事項返答との整合性 + 規律完全遵守 + 観察事実獲得)、ただし最終判断は Taka に委ねる。

---

*以上、Code A による v10.12 Step B 完了報告 + Step C 進行可否判定要請。Web Claude/Taka 判断後に Step C 実装着手 or 主題見直しに進む。Code A は規律遵守で設計判断せず、上申のみ。*
