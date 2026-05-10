# v10.12 Step J 完了報告: cross-seed paired_d / sign_test / bootstrap CI + 留保 #27 formal 化

*作成*: 2026-05-11、Code A
*親*: Step I 完了報告 (commit 7f1c500、24 seeds main run + Aruism 発動候補) + Taka 承認 (2026-05-11「OK　StepJに進めて」)
*対象*: Web Claude (相談役) + Taka (確認、Step K 主題完了報告へ進行)
*目的*: cross-seed 統合分析 + paired_d / sign_test / bootstrap CI 算出 + 層化観察 24 seeds formal + smoke vs main 乖離 evidence + 留保 #27 formal 追加 + Step K (主題完了報告) 進行案

---

## 0. 一文サマリ

Step J で `v112_cross_seed_analyzer.py` を 274 行で実装、24 seeds × 2 conditions の per-seed mean に対し paired_d / sign_test (binomial) / bootstrap CI 95% (n_iter=1000、deterministic random_seed=12112) を 7 metric で算出、**唯一 `n_pulses_short` のみ paired_d +1.36 / sign_test p=0.0000 (22 positive / 2 negative) / bootstrap CI [+0.054, +0.094] (0 を跨がない) で頑健な v112 > v108_standard 観察、他 6 metric (delta_C_medium / delta_Q_medium / 4 path_excess) は全て bootstrap CI が 0 を跨ぎ sign_test p > 0.3 で方向性なし、smoke vs main 乖離は 4/7 metric (path_excess 4 種全て) で cohens_d 符号反転を formal evidence 化、層化観察 24 seeds 統合で v112 bin_5_plus 100% × before 93.8% / no_alpha 6.2% (留保 26 通り) + v108_standard formation_relation during 14% (β member 含、留保 #21 整合) 確定、留保 #27 formal 追加 (累計 27 件)、Step J 実行時間 0.11 秒 + 出力 cross_seed_analysis.json (~30 KB) + paired_analysis.parquet + stratified_24seeds.parquet、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項 全項目遵守、judgment 回避 (success/fail 判定なし、Aruism 整合)、Step K (主題完了報告 v112_completion_report.md) で v10.12 全体総括 + Web Claude/Taka に向けた判断材料 (n_pulses_short 唯一頑健 + 他 6 metric 方向性なし + 留保 27 件) を網羅、v10.13 主題候補の素材として留保 #27 派生案 (a)-(d) を提示。

---

## 1. paired_d + sign_test + bootstrap CI (24 seeds、formal 統計)

### 1.1 全 7 metric の結果

| metric | paired_diff mean | paired_diff std | paired_d | sign_test (pos/neg/zero) | sign_p | bootstrap CI 95% | crosses_zero |
|---|---:|---:|---:|---|---:|---|:-:|
| delta_C_medium | +0.0794 | 0.396 | +0.20 | 12/12/0 | **1.000** | [-0.067, +0.240] | **YES** |
| delta_Q_medium | -0.0168 | 0.304 | -0.06 | 11/13/0 | 0.839 | [-0.138, +0.100] | YES |
| **n_pulses_short** | **+0.0733** | **0.054** | **+1.36** | **22/2/0** | **0.0000** | **[+0.054, +0.094]** | **NO** ✓ |
| path_familiarity_excess | +0.0069 | 0.627 | +0.01 | 11/13/0 | 0.839 | [-0.233, +0.241] | YES |
| path_attention_excess | -0.0033 | 0.558 | -0.01 | 9/15/0 | 0.308 | [-0.214, +0.229] | YES |
| path_temporal_excess | -0.0685 | 0.384 | -0.18 | 13/11/0 | 0.839 | [-0.218, +0.079] | YES |
| path_integration_alpha_excess | +0.4309 | 1.559 | +0.28 | 7/3/14 | 0.344 | [-0.068, +1.107] | YES |

### 1.2 解釈 (観察事実、judgment は Web Claude/Taka)

**唯一頑健 metric**:
- **n_pulses_short** (per-event の short window 内 pulse 数 mean):
  - paired_d +1.36 (大効果)
  - sign_test p = 0.0000 (binomial、22/24 seeds で v112 > v108_standard)
  - bootstrap CI 95% [+0.054, +0.094] **0 を跨がない**
  - → **24 seeds で頑健な v112 > v108_standard 観察**

→ これは観察事実として記録、judgment は Web Claude/Taka:
- 解釈候補 (Code A 提案、確定なし): cond4 (familiarity ≥ top 50%) + cond3 (n_core ≥ 5) で選ばれた cid pool は target_step 直前に **pulse 活動が活発 cid** が選ばれている
- これは「人間言語 → atom 変換」prototype の主題への含意は不明確 (pulse 活発 cid に atom 取り込みを突発させると n_pulses が高い、というだけかもしれない)

**他 6 metric (方向性なし)**:
- 全て bootstrap CI が 0 を跨ぐ
- sign_test p > 0.3
- delta_C_medium / delta_Q_medium / 4 path_excess 全て seed-level variability に埋もれる

→ **「v112 受容 cid pool は v108_standard top_k_100 pool より delta_C / path_excess が強い」という暗黙予想は 24 seeds で不成立**、observation_records にて記録。

---

## 2. smoke vs main cohens_d 乖離 (留保 #27 formal evidence)

### 2.1 全 7 metric の比較

| metric | smoke seed 0 cohens_d | main 24 seeds cohens_d | 符号反転 |
|---|---:|---:|:-:|
| delta_C_medium | +0.5475 | +0.0885 | - (同符号、5 倍縮小) |
| delta_Q_medium | -0.0774 | -0.0112 | - (同符号、7 倍縮小) |
| n_pulses_short | +0.4976 | +0.2533 | - (同符号、2 倍縮小) |
| **path_familiarity_excess** | +0.4918 | -0.0096 | **YES** ✗ |
| **path_attention_excess** | +1.0869 | -0.0375 | **YES** ✗ |
| **path_temporal_excess** | +0.3015 | -0.1509 | **YES** ✗ |
| **path_integration_alpha_excess** | -0.6264 (n_a=59) | +0.1629 (n_a=1,405) | **YES** ✗ |

### 2.2 集計

- **4/7 metrics で符号反転** (path_excess 4 種**全て**)
- 残り 3 metric (delta_C/Q/n_pulses) は同符号維持だが大幅縮小
- → **smoke seed 0 は path_excess に関して seed 特異的な観察結果**
- 留保 #27 (Step J で formal 追加) の核心 evidence

---

## 3. 層化観察 24 seeds 統合 (formal)

### 3.1 n_core_bin × condition

| stratify_axis | condition | stratum | n_seeds_with_data | total_n_pairs | delta_C_medium per-seed mean |
|---|---|---|---:|---:|---:|
| n_core_bin | v112 | bin_2 | **0/24** | 0 | NaN |
| n_core_bin | v112 | bin_3_4 | **0/24** | 0 | NaN |
| n_core_bin | v112 | bin_5_plus | 24/24 | 10,500 | **+0.0810** (std 0.414) |
| n_core_bin | v108_standard | bin_2 | 24/24 | 52,864 | +0.0006 |
| n_core_bin | v108_standard | bin_3_4 | 24/24 | 3,717 | +0.0021 |
| n_core_bin | v108_standard | bin_5_plus | 24/24 | 3,419 | +0.0209 |

→ **意味的に対応する cell**: v112 bin_5_plus +0.0810 vs v108_std bin_5_plus +0.0209 (差 +0.06、ただし v112 std 0.414 で seed-level noise が大)。

### 3.2 formation_relation × condition

| stratify_axis | condition | stratum | n_seeds_with_data | total_n_pairs | delta_C_medium per-seed mean |
|---|---|---|---:|---:|---:|
| formation_relation | v112 | before | 24/24 | 9,850 | +0.0853 |
| formation_relation | v112 | no_alpha | 16/24 | 650 | 0.0000 |
| formation_relation | v112 | during | **0/24** | 0 | NaN |
| formation_relation | v112 | after | **0/24** | 0 | NaN |
| formation_relation | v108_standard | before | 24/24 | 21,845 | +0.0032 |
| formation_relation | v108_standard | during | 24/24 | 8,519 | +0.0094 |
| formation_relation | v108_standard | no_alpha | 24/24 | 29,636 | -0.0021 |
| formation_relation | v108_standard | after | 0/24 | 0 | NaN |

→ **v112 before** (主流 93.8%): +0.0853、v108_std before: +0.0032 → 差 +0.08 (seed-level noise 内)
→ **v112 no_alpha** (16/24 seeds で出現): 0.0000、v108_std no_alpha (49.4%): -0.0021 → 同等
→ **v108_std during** (β member、14.2%): +0.0094 (最も低い q_c_inherited 効果? 留保 #21 整合)

---

## 4. 留保事項 27 件 (Step J で #27 formal 追加)

### 4.1 全件サマリ

| id 範囲 | 件数 | 由来 |
|---|---:|---|
| 1-22 | 22 | v10.9-v10.11 継承 (本主題で再評価対象外) |
| **23** | 1 | Step Z (n_core 反応 type 分業) |
| **24** | 1 | Step B (Q3_threshold 977) |
| **25** | 1 | Step B (familiarity 閾値 top 50%) |
| **26** | 1 | Step A 再実施 (cond1/cond3 絞り込み bin_5+ × before/no_alpha 集中) |
| **27** | 1 | **Step I/J (Aruism evidence、smoke vs main 乖離)** |
| **計** | **27** | |

### 4.2 留保 #27 formal (Step J で確定)

**title**: smoke seed 0 の path_excess は seed 特異的、24 seeds 統合では効果分散

**evidence (formal)**:
- smoke seed 0 cohens_d: delta_C_medium +0.5475 / path_attention_excess +1.0869 / path_familiarity_excess +0.4918
- main 24 seeds 統合 cohens_d: delta_C_medium +0.0885 (5 倍縮小) / path_attention_excess -0.0375 (符号反転) / path_familiarity_excess -0.0096 (符号反転)
- main 24 seeds paired_d (per-seed): n_pulses_short のみ +1.36 (頑健)、他 6 metric は CI が 0 を跨ぐ
- paired diff per-seed: positive 12 / negative 12 / sign_test p ≈ 1.0 (delta_C_medium)
- v112 delta_C_medium per-seed: mean +0.081, std 0.414, range -0.60 〜 +0.97
- seed 0 (+0.7465) は seed 別分布で **上位 2 番目** (外れ値的位置)
- 4/7 metric (path_excess 4 種全て) で smoke vs main で符号反転

**decision**:
- 本主題内では judgment せず観察事実として記録
- Aruism「予想と違えば再観察」発動候補
- Web Claude/Taka が主題評価 + v10.13 主題候補判断する素材

**future_subject (Code A 提案、Web Claude/Taka 判断)**:
- **(a)** seed-level variability 自体を観察対象とする主題
- **(b)** smoke 段階で複数 seed (例 3 seeds) で確認する手順への変更
- **(c)** cohens_d の seed 平均ではなく per-seed paired_d を主観察にする設計
- **(d)** cid pool 定義 (4 cond) の選定根拠を再検討する主題

---

## 5. 規律遵守自己検証 (Step J)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 + Step C-I で確認済 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ Step F で確定済 7 metric × 3 軸の集計のみ、新規軸なし |
| §34 #37 (n_core 別層化必須) | ✓ §3.1 で n_core_bin 24 seeds 統合 |
| §5.5 規律チェックリスト (案 X) | ✓ 全項目 ○ |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ ledger 不変、層 B 443 files unchanged は Step I で実証済 |
| 神の手回避 | ✓ scipy.stats.binomtest + numpy bootstrap、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 |
| 因果断定回避 | ✓ 「観察事実」「頑健」「方向性なし」「seed-level variability」「乖離」表現、「効いた」「効果なし」「失敗」なし |
| Aruism 整合 | ✓ 3 段階判定なし、留保 #27 formal evidence 化、judgment 材料として Web Claude/Taka に提示 |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

### 5.1 §0.5 禁止事項

| 禁止事項 | Step J 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ paired_d / sign_test / bootstrap CI は Step Z 設計通り (累計規律) |
| 観察軸を増やす方向への転換を提案しない | ✓ 留保 #27 future_subject (a)-(d) は v10.13 以降の候補、本主題内では一切実施しない |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ 母集団 10,500 events / 60,000 events で全 24 seeds 確保、緩和なし |

→ **Step J 全項目遵守**。

### 5.2 重要: judgment 回避

Code A は **n_pulses_short 唯一頑健 + 他 6 metric 方向性なし** という観察事実を「main subject 成功」「失敗」と判定 **しない**。

- これは Web Claude (相談役) と Taka (主題判断者) の領域
- Code A は観察事実 + 統計値 + 留保候補を提示、最終的な主題評価は Step K 完了報告を Web Claude/Taka が読んで判断
- 本書の §1.2 解釈候補も「Code A 提案、確定なし」と明記

---

## 6. Step K 進行案 (主題完了報告)

### 6.1 Step K scope (`v112_completion_report.md` 作成)

主題完了報告として以下を網羅:
1. **v10.12 全体総括** (Step Z → J、commit chain)
2. **構造的成果** (cid pool 420 / events 10,500 / 全工程 PASS / 層 A/B/C 不変保証)
3. **観察事実総覧** (paired_d / sign_test / bootstrap CI / 層化 24 seeds / smoke vs main 乖離)
4. **留保事項 27 件** (継承 22 + 新規 5、特に #27 を formal 化)
5. **Web Claude/Taka 判断材料**:
   - n_pulses_short 唯一頑健の意味
   - 他 6 metric 方向性なしの意味
   - smoke seed 0 の seed 特異性
6. **v10.13 主題候補の素材** (留保 #27 (a)-(d) ほか)
7. **Code A 自己評価**:
   - 規律遵守
   - §0.5 禁止事項遵守
   - judgment 回避遵守
   - Aruism 整合
   - smoke 後 main 自動進行回避 (Taka 承認待機遵守、過去 v10.6 違反教訓)
8. **資料リンク** (Step Z-J 全 commit + 報告書 + 出力 JSON)

### 6.2 Step K 完了で v10.12 終了

```
Step Z 完了 (commit df04d0a)
Step B 完了 (commit 9d755ec)
Step A 再実施完了 (commit 8b3d3e3)
Step C 完了 (commit 8880574)
Step D 完了 (commit b790d56)
Step E 完了 (commit df95646)
Step F 完了 (commit 431e59e)
Step G 完了 (commit a84191b)
Step I 完了 (commit 7f1c500)
Step J 完了 (本書)
   ↓
Step K (主題完了報告) で v10.12 終了
   ↓ Web Claude/Taka 評価
v10.13 主題選定 (留保 #27 派生案ほか)
```

### 6.3 上申条件

- 母集団不足 (なし、10,500 / 60,000 events)
- 規律違反の兆候 (なし)
- 第 5 版主題と整合しない設計判断 (なし、Step J も第 5 版設計通り)

→ Step K 単独進行可、Web Claude/Taka 承認後 v10.13 主題選定に進む。

---

## 7. 計算資源 (Step J)

| 区分 | 値 |
|---|---:|
| Step J 実行時間 | **0.11 秒** |
| 出力 cross_seed_analysis.json | ~30 KB |
| 出力 paired_analysis.parquet | ~5 KB |
| 出力 stratified_24seeds.parquet | ~10 KB |
| 累計 v112 storage (Z-J) | ~94 MB / 6 GB (1.5%) |

→ Step J は最軽量、main run 比で 200 倍速 (0.11 vs 20.35 秒)。

---

## 8. 一文サマリ (再掲)

Step J で `v112_cross_seed_analyzer.py` を 274 行で実装 + 0.11 秒で実行、24 seeds × 2 conditions × 7 metric × paired_d / sign_test (binomial) / bootstrap CI 95% (n_iter=1000、deterministic random_seed=12112) を formal 算出、**唯一 n_pulses_short のみ paired_d +1.36 / sign_test p=0.0000 (22 positive / 2 negative) / bootstrap CI [+0.054, +0.094] で 0 を跨がず頑健な v112 > v108_standard 観察、他 6 metric (delta_C_medium / delta_Q_medium / 4 path_excess) は全て CI が 0 を跨ぎ sign_test p > 0.3 で方向性なし**、smoke vs main 乖離は 4/7 metric (path_excess 4 種全て) で cohens_d 符号反転、層化観察 24 seeds 統合で v112 bin_5_plus 100% × before 93.8% / no_alpha 6.2% (留保 #26 通り、空セル `n_pairs=0` 明示) + v108_standard formation_relation during 14.2% (β member 含、留保 #21 整合)、留保 #27 formal 追加で累計 27 件 (継承 22 + 新規 5: #23-#27)、留保 #27 future_subject に v10.13 主題候補 4 案 (a) seed-level variability / (b) smoke 複数 seed / (c) per-seed paired_d 主観察 / (d) cid pool 定義再検討、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項 全項目遵守、judgment 回避 (n_pulses_short 頑健 / 他 6 metric 方向性なしを「成功/失敗」と判定せず観察事実として記録)、Step K (v10.12 主題完了報告 v112_completion_report.md) に進行可、Step K 完了で v10.12 終了、Web Claude/Taka 評価 → v10.13 主題選定。

---

*以上、v10.12 Step J 完了報告。Code A は本報告 commit + push 後、Step K (主題完了報告) に進む。Step K で v10.12 全体総括 + Web Claude/Taka 判断材料 + v10.13 主題候補素材を網羅、Step K 完了で v10.12 終了。第 5 版主題 + 第 4 版実装指示書 + 累積規律 27 件 + §5.5 規律チェックリスト + §0.5 禁止事項 + judgment 回避を Step K 全期間遵守。*
