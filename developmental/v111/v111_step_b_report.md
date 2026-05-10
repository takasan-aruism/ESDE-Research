# v10.11 Step B 完了報告 — 環境チェック + seed 0 smoke

*作成*: 2026-05-10、Code A
*親*: `v111_phase_design.md` 第三稿
*対象*: Taka (main run 進行判定)

---

## 0. 一文サマリ

q_c_inherited observer 実装 (within-cid design、t_offset ±50 step 5 step 刻み 21 samples)、seed 0 smoke 0.55 秒で動作確認、12 cells (n_core_bin × β 累積 c_inherited 分位) 全セル母集団 > 0、bit-identity 層 A PASS、**核心観察**: seed 0 で **Q1 (累積 c<3) のみ delta_C 正値 (+0.273〜+1.200)、Q2-Q4 で delta_C ≈ 0** と C 値飽和仮説と整合する初期観察 (整理仮説、留保: seed 0 のみ、24 seeds で確認必須)、main run 推定 1-2 分 / storage 累計 1.54 GB (26%) で打ち切り条件大幅余裕、Taka 承認後 24 seeds main run → cross-seed 解析 → 完了報告 → Phase 1.5 第六試行完了の順で進む。

---

## §1 実装内容

### 1.1 v111_q_c_inherited_observer.py

実装方針 (主題ドキュメント第三稿 §4.0 within-cid design 準拠):

```python
T_OFFSETS = list(range(-50, 51, 5))  # -50, -45, ..., +50 (21 samples)

def observe_seed(seed):
    # 1. q_c_inherited events 抽出
    qci = beta_lifecycle_log[event_type='q_c_inherited']
    
    # 2. β 別累積 c_inherited 計算 (event 順)
    qci['cumulative_c_before_event'] = groupby(beta_id).c_inherited_delta.cumsum().shift(0)
    qci['c_q_partition'] = cumulative → Q1/Q2/Q3/Q4
    
    # 3. (event, member_cid) ペア生成 (member_cids NaN 除外)
    # 4. 各 (event, cid) × t_offset で snapshot
    #    - C 値: balance_decisions の global_step + C_at_decision を merge_asof
    #    - pulse 数: pulse_log から [t_obs, t_obs+5) で count
    # 5. 出力: q_c_inherited_events / response_profile parquet
```

### 1.2 v107 lookup の解決

主題ドキュメント §Z.3 (Web Claude 知識の穴と Code A 認識確認):
- v107 `_build_state_lookups` の bd_q は step 列 (window 内 step 0-499) を使用
- v111 では **balance_decisions の global_step 列** を直接使う独自 lookup を実装
- 既存 v107 出力には書き込まず、v111 内独立処理で物理層 frozen 維持

→ v107 lookup の挙動とは無関係に、v111 で C 値時系列を正しく取得。

---

## §2 seed 0 smoke 結果

### 2.1 機構動作

```
v10.11 q_c_inherited observer - mode=smoke, seeds=1
  T_OFFSETS: 21 samples, ±50 step, 5 step 刻み

seed=0:
  n_qci_events: 102
  n_qci_with_member: 52 (50.0% 欠損、v10.5 設計と整合)
  n_snapshots: 2,100
  n_unique_cids: 52
  total (event, cid) pairs: 100

DONE  total elapsed = 0.55s
```

### 2.2 12 cells 母集団 ((event, cid) pair 単位、seed 0)

| n_core_bin | Q1 (<3) | Q2 (3-6) | Q3 (6-9) | Q4 (≥10) |
|---|---:|---:|---:|---:|
| bin_2 | 27 | 9 | 6 | **3** |
| bin_3_4 | 10 | 4 | **2** | 8 |
| bin_5+ | 11 | 6 | 4 | 10 |

→ 全 12 cells > 0、最小 2 (bin_3_4 × Q3、seed 0) / 最大 27 (bin_2 × Q1、seed 0)

24 seeds 集計推定:
- 24 seeds × seed 0 母集団比率で各 cell ~50-650 pairs
- 最小予想 cell (bin_3_4 × Q3): 24 × 2 = 48 pairs
- 最大予想 cell (bin_2 × Q1): 24 × 27 = 648 pairs
- per atom×seed の必要性は本主題に該当せず (atom 軸を含まない)

### 2.3 bit-identity 層 A 検証

| ファイル | 結果 |
|---|---|
| q_c_inherited_events_seed0.parquet | **PASS** ✓ |
| q_c_inherited_response_profile_seed0.parquet | **PASS** ✓ |

→ 同 seed で 2 回実行、MD5 完全一致。物理層 frozen 維持、決定論的処理。

---

## §3 核心観察 (seed 0 only、整理仮説 + 留保)

### 3.1 within-cid delta_C の n_core_bin × c_q_partition (cohens_d_mean ではなく raw delta_C 平均)

| n_core_bin | Q1 (<3) | Q2 (3-6) | Q3 (6-9) | Q4 (≥10) |
|---|---:|---:|---:|---:|
| **bin_2** | **+0.593** | 0.000 | 0.000 | 0.000 |
| **bin_3_4** | **+1.200** | 0.000 | 0.000 | +0.250 |
| **bin_5+** | **+0.273** | 0.000 | 0.000 | 0.000 |

### 3.2 観察事実 (記述のみ、判定なし)

- Q1 列 (累積 c < 3) でのみ delta_C が正値 (+0.273 〜 +1.200)
- Q2 / Q3 列 (累積 c 3-9) で delta_C はすべて 0.000
- Q4 列 (累積 c ≥ 10) で delta_C はほぼ 0、bin_3_4 × Q4 のみ +0.250
- bin_3_4 × Q1 で delta_C が最大 (+1.200)
- bin_5+ × Q1 で delta_C は最小の正値 (+0.273)

### 3.3 整理仮説 (主題ドキュメント §3 ラベル規律準拠、留保つき)

「累積 c_inherited が小さい cid (Q1) のみが q_c_inherited 直前/直後で delta_C 正方向に応答する。累積 c_inherited が一定以上の cid (Q2-Q4) では delta_C 応答が消失する」という観察事実。

整理仮説候補 (構造的根拠未確認):
- 仮説 2 (C 値飽和、主題 §1.3): β からの C 継承累積が cid の C 値を高水準に維持し、追加刺激の delta_C 余地が消失。Q1 (累積少) では C 余地が残る → 観察事実と整合
- 反証する観察: 本データでは見当たらない (Q1 のみ正、それ以外 ≈0)

留保事項:
- seed 0 のみの観察、24 seeds 集計で確認必須
- bin_3_4 × Q4 の +0.250 は seed 別変動の可能性 (n=8 pairs)
- delta_C の正値は cohens_d ではなく raw mean (seed 別 std 評価が必要)

→ 構造的根拠は v10.11 main run + cross-seed 解析で再確認、判定は Web Claude 主題完了レポートで実施。

---

## §4 計算量・ストレージ

### 4.1 main run 推定

- seed 0 smoke 0.55 秒
- 24 並列 main run 推定: **1-2 分** (Code A 認識確認 §5.2 推定 3-5 分より速い、I/O が主因)
- §0.3 打ち切り条件 3 (30 分超) に **大幅余裕**

### 4.2 storage

- seed 0 smoke 出力:
  - q_c_inherited_events_seed0.parquet: ~5 KB
  - q_c_inherited_response_profile_seed0.parquet: ~30 KB
- 24 seeds main 推定: events ~150 KB + profiles ~720 KB ≒ **~1 MB** (Code A 認識確認推定 27 MB より大幅小)
- + cross_seed_summary 集計 ~5 MB
- v10.11 main 合計: **~6 MB**
- 累計: **1.51 + 0.006 = 1.52 GB / 上限 6 GB (25%)** で打ち切り条件 50% 余裕大

→ Code A 認識確認推定より大幅小。snapshot 数が seed 別で予想より少ない (52 (event, cid) pair × 21 t_offset = 2,100 snapshots/seed) ため。

---

## §5 規律遵守の確認

| 規律 | 状態 |
|---|---|
| 物理層 frozen | ✓ (read のみ、ledger 改変なし) |
| 神の手回避 | ✓ (実測のみ) |
| Atom 326 絶対化禁止 | ✓ (本主題は atom 軸を含まない) |
| 因果断定回避 (§3 ラベル規律) | ✓ (§3.3 で観察事実 / 整理仮説 / 留保 を分離) |
| post-process 計算的減算 (§Q5) | ✓ (観察値集計として整合) |
| Code A 認識確認必須 | ✓ (再認識確認応答 → Web Claude 全件採用 → 第三稿確定) |
| 4 層階層化 (§4) | △ Step C / Step F で Level 2-3.5 集計実装予定 |
| 緩和 run 禁止 | ✓ |
| n_core 別層化 (§34 #37) | ✓ (条件軸 1) |
| **完全マージ版文書を出力** (§34 #39) | ✓ (本書) |
| 規律 §35 #5 (整理語と観察事実の分離) | ✓ (§3.2 / §3.3 で実装) |
| 規律 §35 #10 (観察できる軸が見えたを駆動要因にしない) | ✓ (達成条件 §0.2 = v10.12 入力ルーティング条件 1 本抽出を駆動要因として固定) |

---

## §6 Step C / E 進行判定要請 (Taka)

### 6.1 main run 計画 (Step C+E 統合実行)

```bash
python3 v111_q_c_inherited_observer.py --mode main --n_workers 24
```

推定:
- 計算時間: 1-2 分 (24 seeds 並列)
- ストレージ: ~6 MB (累計 1.52 GB / 25%)

### 6.2 Step F (cross-seed 解析) の予告

main run 完了後、`v111_response_profile_compiler.py` 実装で:
- 12 cells × 24 seeds の集計
- 24 seeds 方向一致 4 段階観察 (complete / majority / tied)
- delta_C / pulse_count cohens_d
- v10.10 と同じ within-cid design 解析フレーム

### 6.3 Step G (完了報告) の達成条件 §0.2

達成条件 (主題 §0.2): **v10.12 入力ルーティング設計に使える条件 1 本以上抽出**

seed 0 smoke 結果から見込まれる条件 (整理仮説、24 seeds で確認後確定):
- 「累積 c_inherited が 3 未満の cid (n_core 任意) は q_c_inherited 前後で delta_C 正応答、累積 3 以上で応答消失」
- v10.12 で「狙う cid」の条件として: 累積 c_inherited Q1 群 (β 累積 < 3) が概念取り込み (delta_C) の対象

### 6.4 Taka 確認事項

- **Q1**: main run (Step C+E 統合) 進行許可
- **Q2**: Step F (cross-seed 解析、`v111_response_profile_compiler.py` 実装) を main run 後に Code A 単独進行で OK か
- **Q3**: Step G (完了報告) を Code A 単独で書き上げ → Web Claude 主題完了レポート の手順で OK か

memory rule (smoke 後止まって報告) 厳守、Q1 承認後 main run 1 コマンド実行。

---

## §7 出力ファイル

- `developmental/v111/v111_q_c_inherited_observer.py` (実装)
- `developmental/v111/outputs/smoke/q_c_inherited_events_seed0.parquet` (102 events)
- `developmental/v111/outputs/smoke/q_c_inherited_response_profile_seed0.parquet` (2,100 snapshots)
- `developmental/v111/outputs/smoke/q_c_inherited_run_summary.parquet` (1 row)
- 本書: `v111_step_b_report.md`

---

## §8 一文サマリ (再掲)

q_c_inherited observer 実装 (within-cid design、within-cid 比較は **balance_decisions の global_step を直接使う独自 lookup** で v107 lookup の window 内 step 解釈問題を回避)、seed 0 smoke 0.55 秒で動作確認 (102 events、52 events に member_cids 記録、100 (event, cid) pairs、2,100 snapshots)、12 cells 全セル母集団 > 0 (最小 2 / 最大 27)、bit-identity 層 A PASS (2 ファイル MD5 完全一致)、**核心観察**: Q1 (累積 c<3) のみ delta_C 正値 (+0.273〜+1.200)、Q2-Q4 で delta_C ≈ 0 と C 値飽和仮説と整合する初期観察 (seed 0 のみ、24 seeds 確認必須、整理仮説として留保)、main run 推定 1-2 分 / storage 累計 1.52 GB (25%) で打ち切り条件大幅余裕、規律遵守 (物理層 frozen / §3 ラベル規律 / §35 #5 #10)、Taka 承認 (Q1 main run + Q2 Step F 単独進行 + Q3 完了報告 Code A 単独) 後に main run → cross-seed 解析 (Step F) → 完了報告 (Step G、達成条件 §0.2 の v10.12 入力ルーティング条件 1 本抽出) → Phase 1.5 第六試行完了の順で進む。

---

*以上、Code A による v10.11 Step B 完了報告。Taka 承認待ち。memory rule (smoke 後止まって報告) 厳守、Q1 承認後 main run 1 コマンド実行。*
