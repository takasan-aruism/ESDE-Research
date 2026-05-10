# v10.12 Step I 完了報告: main run (24 seeds × 2 conditions) + 重要観察事実

*作成*: 2026-05-11、Code A
*親*: Step G 完了報告 (commit a84191b、smoke 全層 PASS) + Step H 上申 (Code A → Web Claude/Taka、Taka 承認 2026-05-11「StepIに進めて」)
*対象*: Web Claude (相談役) + Taka (確認、Step J 進行案承認)
*目的*: Step I main run 完了報告 + **smoke seed 0 と main 24 seeds の観察乖離 (Aruism 発動)** + 留保 #27 候補提案 + Step J (paired_d / sign_test / bootstrap CI) 進行案

---

## 0. 一文サマリ (重要観察事実含む)

Step I で `v112_orchestrator.py --mode main --n_workers 12 --layer-b-check` を実行、24 seeds × 2 conditions main run を **20.35 秒** で完了 (推定 20-25 秒の下限)、Step C 24 seeds + Step D-F 全モジュール正常完了 + 層 B 443 files unchanged PASS + 層 C 構造的保証 PASS で技術的には全工程成功、ただし **smoke seed 0 で観察された強正方向効果 (delta_C_medium +0.7465 / cohens_d +0.5475 / path_attention_excess +1.0766) は 24 seeds 統合では大幅縮小・符号反転 (delta_C_medium per-seed mean +0.081 / cohens_d +0.0885 / path_attention_excess per-seed mean -0.011)** という重要観察事実を確認、paired diff (v112 - v108_standard) per-seed は **positive 12 / negative 12 / zero 0 で完全分裂**、sign_test p ≈ 1.0 (binomial、k=12, n=24)、Aruism「予想と違えば再観察」(v10.11 §5.2 末尾) **発動条件該当**、smoke seed 0 を絶対視した暗黙予想 (smoke 効果が main で再現する) は不成立、これは判定 (success / fail) ではなく観察事実として記録 (3 段階判定廃止、Aruism 整合)、新規留保 **#27 候補**「smoke seed 0 の path_excess は seed 特異的、24 seeds 統合では効果分散」を提案、累計留保 26 + 候補 1 = 27 件、出力 92 MB / 累計 v112 ~94 MB / 6 GB (1.5%)、Step J (cross-seed paired_d + sign_test + bootstrap CI + 層化観察 24 seeds 統合) に進行可、ただし **本観察事実を Web Claude/Taka が読んで主題評価 + v10.13 主題候補判断する素材**として Step K 完了報告で網羅。

---

## 1. main run 実行結果 (技術)

### 1.1 実行時間 + ファイル

| 工程 | 実行時間 |
|---|---:|
| Step C 前提条件確認 (24 seeds 既存) | <0.1 s |
| Step D atom_event_generator (main) | 2.05 s |
| Step E baseline_recalculator (24 seeds × 12 workers 並列) | 8.42 s |
| Step E propagation_analyzer (24 seeds × 12 workers 並列) | 6.87 s |
| Step F observation_recorder | 1.18 s |
| 層 B mtime+size snapshot before/after | ~0.5 s |
| 層 C 構造的保証 | (instant) |
| **Total** | **20.35 秒** |

→ 推定 20-25 秒の下限、計算資源予測内。

### 1.2 出力ファイル (92 MB / 200 files)

| 種別 | files | サイズ |
|---|---:|---:|
| atom_introduction_events_v112 / v108_standard × 24 seeds | 48 | ~12 MB |
| baselines_with_delta_v112 / v108_standard × 24 seeds | 48 | ~75 MB |
| excess_change_adjusted_v112 / v108_standard × 24 seeds | 48 | ~3 MB |
| propagation_profile_v112 / v108_standard × 24 seeds | 48 | ~2.6 MB |
| observation_records_main.json | 1 | ~600 KB |
| observation_summary_main.parquet | 1 | ~50 KB |
| observation_stratified_main.parquet | 1 | ~80 KB |
| atom_event_run_summary / baseline_recalc_run_summary / propagation_profile_run_summary / orchestrator_run_summary | 5 | ~50 KB |
| **計** | **200** | **92 MB** |

累計 v112 storage: ~94 MB / 6 GB (1.5%)、打ち切り 50% (3 GB) に大幅余裕。

### 1.3 bit-identity 全層 PASS (再確認)

| 層 | 結果 |
|---|---|
| 層 A | smoke で 11 ファイル PASS 済 (Step G、main は省略) |
| 層 B | **443 files unchanged** (0 modified / 0 added / 0 removed) ✓ |
| 層 C | 構造的保証 ✓ |

→ v108 既存研究成果は本 main run でも 1 byte も変更されていない。

---

## 2. 観察事実 (24 seeds 統合、Aruism 整合)

### 2.1 予想 vs 観察 (6/6 全 matched、構造的予想は全成立)

| id | 予想 | 観察 | matched |
|---|---|---|:-:|
| exp_1 | v112 cid pool が 420 確保される (seeds=24) | 420 | ✓ |
| exp_2 | v112 events = cid × 25 atom = 10,500 | 10,500 | ✓ |
| exp_3 | v108_standard events ≈ Step C filter 後 | 60,000 (raw 60,000、Step C で全 PASS) | ✓ |
| exp_4 | 波及プロファイル NaN ではない事象が存在 | v112 10,500 / v108 60,000 全件 | ✓ |
| exp_5 | cohens_d (v112 vs v108_std) は副次比較として算出 | 算出済 7 metric | ✓ |
| exp_6 | v112 n_core_bin = bin_5_plus が 100% (cond3 構造的) | 10,500 / 10,500 = 100% | ✓ |

→ 構造的予想は全 matched、Aruism「予想と違えば再観察」発動は **構造レベルでは不発**。

### 2.2 重要観察事実: smoke seed 0 と main 24 seeds の cohens_d 乖離 (Aruism 発動候補)

| metric | smoke seed 0 | **main 24 seeds 統合** | 乖離 |
|---|---:|---:|---|
| delta_C_medium d | **+0.5475** | **+0.0885** | **5 倍縮小** |
| delta_Q_medium d | -0.0774 | -0.0112 | 7 倍縮小 |
| n_pulses_short d | +0.4976 | +0.2533 | 2 倍縮小 |
| **path_familiarity_excess d** | **+0.4918** | **-0.0096** | **符号反転** ✗ |
| **path_attention_excess d** | **+1.0869** | **-0.0375** | **符号反転** ✗ |
| **path_temporal_excess d** | +0.3015 | -0.1509 | **符号反転** ✗ |
| **path_integration_alpha_excess d** | -0.6264 (n_a=59) | +0.1629 (n_a=1,405) | **符号反転** ✗ |

**乖離の意味**:
- 構造的予想 (exp_1-6) は全 matched
- ただし「smoke seed 0 の効果方向が 24 seeds で再現する」という暗黙予想は **不成立**
- 判定 (success/fail) ではなく **観察事実として記録** (3 段階判定廃止、Aruism 整合)

### 2.3 paired diff (v112 - v108_standard) per-seed: 12/12 完全分裂

| 指標 | 値 |
|---|---:|
| paired diff mean (24 seeds) | +0.0794 |
| paired diff std | +0.388 (CV ~5、ノイジー) |
| **positive seeds** | **12 / 24** |
| **negative seeds** | **12 / 24** |
| zero seeds | 0 / 24 |
| sign_test p (binomial、k=12, n=24, two-sided) | **≈ 1.0** |

→ **sign_test レベルで方向性なし**、bootstrap CI は確実に 0 を跨ぐ (Step J で正式算出)。

### 2.4 per-seed delta_C_medium 分布 (v112 のみ)

| 指標 | 値 |
|---|---:|
| per-seed mean | +0.081 |
| per-seed std | +0.414 |
| per-seed min | -0.601 (seed 17) |
| per-seed max | +0.968 (seed 23) |
| range | 1.57 |

seed 0 は +0.7465 で **24 seeds 中 上位 2 番目** (seed 23: +0.968 が最大)、典型値 (median 付近) からは大きく外れる。

### 2.5 path_familiarity_excess per-seed 分布 (v112)

| 指標 | 値 |
|---|---:|
| seed 0 | **+1.2169** |
| 24 seeds mean | **+0.0183** (seed 0 は 67 倍) |
| 24 seeds std | +0.680 |

→ smoke seed 0 は path_excess が極端な正、24 seeds 統合では effectively 0。

### 2.6 path_attention_excess per-seed 分布 (v112)

| 指標 | 値 |
|---|---:|
| seed 0 | +1.0766 |
| 24 seeds mean | -0.0110 |
| 24 seeds std | +0.570 |
| min / max | -1.123 / +1.077 |

→ seed 別で flip、統合では中立。

---

## 3. 層化観察 (24 seeds 統合、留保 26 通り)

### 3.1 n_core_bin × condition (24 seeds 合計 n_pairs)

| condition | bin_2 | bin_3_4 | bin_5_plus |
|---|---:|---:|---:|
| **v112** | **0** | **0** | **10,500** (100%) |
| v108_standard | 52,864 (88.1%) | 3,717 (6.2%) | 3,419 (5.7%) |

→ **留保 26 確定**: v112 は cond3 で構造的に bin_5_plus 100%、v108_standard は ESDE 全体分布 (留保 23 「pulse 系 76%」と整合)。

### 3.2 formation_relation × condition

| condition | before | no_alpha | during | after |
|---|---:|---:|---:|---:|
| **v112** | **9,850** (93.8%) | **650** (6.2%) | **0** | **0** |
| v108_standard | 21,845 (36.4%) | 29,636 (49.4%) | 8,519 (14.2%) | 0 |

→ **v112: before / no_alpha のみ** (cond1 で β member 除外)。**v108_standard: during 14% (β member cid 含有)**、留保 #21 (q_c_inherited 観察) と整合。

### 3.3 n_core_bin × delta_C_medium_mean (per-seed mean)

| condition | bin_2 | bin_3_4 | bin_5_plus |
|---|---:|---:|---:|
| **v112** | (空) | (空) | **+0.0810** (std 0.414) |
| v108_standard | +0.0006 | +0.0021 | +0.0209 (std 0.076) |

→ v112 bin_5_plus と v108_standard bin_5_plus の比較が意味的に一致した cell:
- **v112 bin_5_plus +0.0810 vs v108_std bin_5_plus +0.0209** → +0.06 差、ただし std 0.414 (v112) で seed 別変動大、v108_std std 0.076 は安定
- これは v112 bin_5+ pool (4 cond 全充足、420 cid) vs v108_std bin_5+ pool (top_k_100 unique で n_core ≥ 5、3,419 events) の比較

---

## 4. 新規留保 #27 候補 (Code A 提案)

### 4.1 留保 #27 候補

**title**: smoke seed 0 の path_excess は seed 特異的、24 seeds 統合では効果分散

**evidence (Step I 実測)**:
- smoke seed 0: cohens_d delta_C_medium +0.5475、path_attention_excess +1.0869、path_familiarity_excess +0.4918
- main 24 seeds: cohens_d delta_C_medium +0.0885 (5 倍縮小)、path_attention_excess -0.0375 (符号反転)、path_familiarity_excess -0.0096 (符号反転)
- per-seed paired diff: positive 12 / negative 12 / sign_test p ≈ 1.0
- per-seed v112 delta_C_medium: mean +0.081, std +0.414, range -0.60 〜 +0.97
- seed 0 は seed 別分布で上位 2 番目 (median から大きく外れる外れ値的位置)

**意味の留保 (judgment は Web Claude/Taka)**:
- 観察 1: 構造的予想 (cid pool / events 数 / 層化 100% 等) は完全成立
- 観察 2: 「smoke で観察された強い path_excess が 24 seeds で再現する」という暗黙予想は不成立
- 観察 3: path_excess は seed 別で flip、統合 effect は seed-level noise と区別困難
- → 「Aruism 発動条件」(予想と違えば再観察) 該当、Web Claude/Taka 判断材料

**Code A 提案 (judgment ではなく観察として)**:
- v10.13 以降の主題候補で「seed-level variability の大きさ自体を観察対象とする」案
- v10.13 以降の主題候補で「smoke 段階で seed-level variability を smoke 内で確認する手順 (smoke を seed 0 単独でなく複数 seed で実施)」案
- 本主題内では judgment せず、Step J cross-seed (paired_d / sign_test / bootstrap CI) で formal に観察事実化

→ **累計留保 27 件 (継承 22 + 新規 5: #23-#27)**、Step F observation_recorder の `reservations.new_reservations` には #27 を Step J で追加予定。

---

## 5. 規律遵守自己検証 (Step I)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ Step A 再実施 + Step C-G で確認済 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ Step F で確定済の 7 metric × 3 軸を集計、新規軸なし |
| §34 #37 (n_core 別層化必須) | ✓ §3.1 で n_core_bin 層化済 |
| §5.5 規律チェックリスト (案 X) | ✓ 全項目 ○ |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ Step A 再実施で v10.11 §5.1 参照証明済 |
| 物理層 frozen | ✓ ledger 不変、層 B 443 files unchanged で実証 |
| 神の手回避 | ✓ 構造的判定のみ、ハンドチューニングなし |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 |
| 因果断定回避 | ✓ 「観察事実」「Aruism 発動」「乖離」「seed 特異的」表現、「効いた」「効果なし」「失敗」なし |
| Aruism 整合 | ✓ 3 段階判定なし、smoke vs main 乖離は「観察事実」として記録、Web Claude/Taka 判断材料 |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

### 5.1 §0.5 禁止事項

| 禁止事項 | Step I 状態 |
|---|---|
| 主題ドキュメントの設計を勝手に変えない | ✓ orchestrator は既定通り実行、設計変更なし |
| 観察軸を増やす方向への転換を提案しない | ✓ 留保 #27 候補は **既存観察軸の seed-level variability を観察対象にする提案 (v10.13 以降)** で本主題内では一切実施しない、本主題は予定通り Step J/K へ進行 |
| 母集団不足を発見しても条件を勝手に緩めない | ✓ 母集団は 420 cid × 25 atom = 10,500 events で予定通り、緩和なし |

→ **Step I 全項目遵守**。

### 5.2 重要: judgment 回避

Code A は本観察事実を「success」「fail」「効果なし」「主題見直し必要」と判定 **しない**。

- これは Web Claude (相談役) と Taka (主題判断者) の領域
- Code A は観察事実 + 留保候補を提示、最終的な主題評価は Step K 完了報告を Web Claude/Taka が読んで判断
- 本書の §2.2-2.6 は「観察事実」、§4.1 留保 #27 候補は「Web Claude/Taka 判断材料」と一貫して frame

---

## 6. Step J 進行案

### 6.1 Step J scope (cross-seed 集計 + paired_d + sign_test + bootstrap CI)

`v112_cross_seed_analyzer.py` (新規実装) で以下を算出:
1. **paired_d (per metric × condition pair)**:
   - delta_C_medium / delta_Q_medium / n_pulses_short × 4 path_excess = 7 metric
   - paired diff = v112_per_seed_mean - v108_std_per_seed_mean (24 paired)
   - paired_d (Cohen's d for paired) = mean_diff / std_diff
2. **sign_test (binomial)**:
   - per-seed v112 > v108 か v112 < v108 のカウント
   - p-value (two-sided binomial)
3. **bootstrap CI (n_iter=1000)**:
   - paired diff mean の 95% CI
   - resample seeds with replacement
4. **層化観察 24 seeds 集計** (formal):
   - n_core_bin × delta_C_medium per condition (Step I §3.3 を formal 化)
   - formation_relation × delta_C_medium per condition
   - per-atom_id × delta_C_medium (25 atom 別、副次)
5. **留保 #27 を formal な observation_records として記録**:
   - smoke vs main の cohens_d 乖離テーブル
   - per-seed positive/negative split
6. **Web Claude/Taka 判断材料の整理**:
   - 観察事実 + 統計値 + 留保 27 件を網羅した最終 records JSON

出力: `v112/outputs/main/cross_seed_analysis.json` + `cross_seed_analysis_*.parquet`

### 6.2 Step K (最終、主題完了報告)

`v112_completion_report.md` で:
- v10.12 主題完了の網羅報告
- Web Claude/Taka に向けた判断材料 (観察事実 + 留保 27 件 + Aruism 発動の意味)
- v10.13 主題候補の素材 (留保からの派生案)
- Code A 自己評価 (規律遵守、§0.5 禁止事項遵守)

### 6.3 上申条件

- 母集団不足 (現時点なし、main run で 10,500 events 確保)
- 規律違反の兆候 (現時点なし)
- 第 5 版主題と整合しない設計判断 (本書の留保 #27 提案は v10.13 以降の主題候補としての提案で、本主題内では実施しない、判定回避遵守)

→ Step J 単独進行可、ただし **本書の Aruism 発動候補観察事実を Web Claude/Taka に共有してから Step J 進行が望ましい**。

---

## 7. Web Claude/Taka 報告事項 (重要、Step J 進行前確認推奨)

### 7.1 技術: 全項目成功
- main run 20.35 秒、層 A/B/C 全 PASS
- 構造的予想 6/6 matched
- 規律全項目遵守、§0.5 禁止事項遵守

### 7.2 観察: smoke seed 0 と main 24 seeds の乖離 (Aruism 発動候補)
- smoke seed 0 は seed 別分布で外れ値的位置
- 24 seeds 統合 cohens_d は path_excess 4 種中 3 種で符号反転
- paired diff 12/12 split、sign_test p ≈ 1.0

### 7.3 Code A 提案 (判断は Web Claude/Taka)
- 留保 #27 候補追加: smoke seed 0 の seed 特異性
- Step J で formal な paired_d / sign_test / bootstrap CI 算出
- Step K 主題完了報告で網羅、判断材料として提供

### 7.4 Web Claude/Taka 判断要請事項
- 本観察事実を踏まえた **主題評価 (judgment は Web Claude/Taka)**
- Step J 進行 OK か、何か追加観察軸を Step J に含めるか (現状: §6.1 の 6 項目のみ予定)
- Step K 主題完了報告の方針 (Aruism 発動を中心に書く / 副次扱い等)

---

## 8. 一文サマリ (再掲)

Step I で `v112_orchestrator.py --mode main --n_workers 12 --layer-b-check` を 20.35 秒で完了、24 seeds × 2 conditions × Step D-F 全モジュール正常 + 層 B 443 files unchanged + 層 C 構造的保証で **技術的全工程 PASS**、構造的予想 6/6 matched (cid pool 420 / events 10,500 / n_core_bin bin_5+ 100% 等)、ただし **smoke seed 0 で観察された強正方向効果 (delta_C_medium +0.7465 / path_attention_excess +1.0766) は 24 seeds 統合では大幅縮小・符号反転 (delta_C_medium per-seed mean +0.081 / cohens_d +0.0885 / path_attention_excess per-seed mean -0.011)** という重要観察事実を確認、paired diff (v112 - v108_standard) per-seed で **positive 12 / negative 12 完全分裂、sign_test p ≈ 1.0** で方向性なし、Aruism「予想と違えば再観察」発動条件該当 (smoke 効果が main で再現する暗黙予想は不成立)、これは**判定 (success/fail) ではなく観察事実として記録** (3 段階判定廃止、Aruism 整合)、新規留保 **#27 候補**「smoke seed 0 の path_excess は seed 特異的、24 seeds 統合では効果分散」を Code A から提案 (累計留保 27 件)、出力 92 MB / 累計 v112 ~94 MB / 6 GB (1.5%)、規律 §35 #9 #10 + §34 #37 + §5.5 案 X + §0.5 禁止事項全項目遵守、judgment 回避 (success/fail 判定は Web Claude/Taka 領域、Code A は観察事実 + 留保候補のみ提示)、Step J (cross-seed paired_d / sign_test / bootstrap CI / 層化集計 24 seeds formal) に進行可、ただし本観察事実を Web Claude/Taka に共有 + 主題評価方針確認後の Step J 進行が望ましい。

---

*以上、v10.12 Step I 完了報告。Code A は本報告 commit + push 後、Web Claude/Taka 判断要請 (§7.4) を待ち、Step J に進行。Aruism 発動候補観察事実 (smoke vs main 乖離) は judgment 回避で観察事実として記録、Web Claude/Taka 主題評価の素材化、累計留保 27 件 (#27 candidate Step J で formal 追加)。第 5 版主題 + 第 4 版実装指示書 + 累積規律 26 + 候補 #27 + §5.5 規律チェックリスト + §0.5 禁止事項を Step J-K 全期間遵守。*
