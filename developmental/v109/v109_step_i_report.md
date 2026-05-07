# v10.9 Step I 完了報告 — sensitivity_evaluator (smoke seed 0)

*作成*: 2026-05-08、Code A
*実装*: `developmental/v109/v109_sensitivity_evaluator.py`
*出力*: `developmental/v109/outputs/smoke/sensitivity_evaluation_seed0.parquet`、`sensitivity_evaluation_all.parquet`
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

3 候補感度評価 (A1 vs A2 = Q/C コスト / A1 vs B3 = cid 選定 / A1 vs C2 = タイミング) を Cohen's d で実装、seed 0 smoke 0.19 秒で 540 rows (3 比較 × 10 path × 3 win × 6 metric)、**主要発見: 「timing > cid_selection > QC_cost」の感度階層が判明**、C2 (lifecycle 同調) で familiarity/attention/high_fam_out 経路に **Cohen's d 0.13-0.18 の小〜中効果量** (Step F 仮説の動作確認)、**QC_cost は全 path で effect 0** (post-process 計算的減算のみで実 ledger 不変、v10.10 の limit)、cid_selection は意外にも小さい effect (top_k 100 vs random 100 で大差なし)、Step J (統合 smoke + bit-identity 検証) 進行準備完了。

---

## 1. 実装内容

### 1.1 比較設計

```python
COMPARISONS = {
    "QC_cost":       {"a": "A1", "b": "A2"},  # Q/C コスト感度
    "cid_selection": {"a": "A1", "b": "B3"},  # cid 選定感度
    "timing":        {"a": "A1", "b": "C2"},  # タイミング感度
}
```

### 1.2 入力データ

- **A1 (baseline)**: v10.8 main の `excess_change_adjusted_seed*.parquet` から atom_introduction_event のみフィルタ (17,207 rows / seed)
- **A2 / B3 / C2**: v10.9 smoke or main の `excess_change_adjusted_{cond}_seed*.parquet`

### 1.3 評価対象

- 10 paths × 3 windows (immediate/short/medium) × 6 metrics = **180 cells / 比較**
- 6 metrics: `mean_delta_R_familiarity`, `mean_delta_Q`, `mean_delta_C`, `mean_delta_n_alphas`, `mean_delta_n_observed`, `mean_n_pulses_in_window`
- 3 比較 × 180 = **540 rows / seed**

### 1.4 統計指標

- Cohen's d (pooled std で正規化、符号は `b - a` 方向)
- mean_a / mean_b / std_a / std_b / delta_mean / n_a / n_b

---

## 2. smoke 結果 (seed 0、540 rows)

### 2.1 主要メトリック (mean_delta_C_medium、Cohen's d)

| path | QC_cost (A1→A2) | cid_selection (A1→B3) | **timing (A1→C2)** |
|---|---:|---:|---:|
| **attention_via_salience** | 0.000 | 0.028 | **0.126** |
| **familiarity** | 0.000 | -0.083 | **0.161** |
| **high_familiarity_outside_integration_baseline** | 0.030 | 0.012 | **0.177** |
| **unrelated_baseline** | -0.032 | -0.024 | **0.177** |
| matched_baseline | 0.001 | -0.003 | -0.070 |
| same_integration_low_familiarity_baseline | 0.000 | -0.053 | **-0.153** |
| same_step_random_baseline | 0.000 | 0.005 | -0.063 |
| temporal_coactivation | 0.000 | 0.005 | -0.062 |
| integration_alpha | 0.000 | 0.000 | 0.000 |
| integration_beta | 0.000 | 0.000 | 0.000 |

### 2.2 観察

#### 観察 1: 感度階層 「timing > cid_selection > QC_cost」

- **timing (C2 lifecycle 同調) が最大の感度**: 主要経路で 0.13-0.18 (小〜中効果量)
- cid_selection (B3 random) は path 別にばらつくが小さい (max 0.083)
- QC_cost (A2 Q-2/C+2) はほぼ全 path で 0 (max 0.032)

#### 観察 2: C2 で「正方向」と「負方向」が混在

- 正方向 (b > a、C2 で C 増): familiarity (0.161)、attention (0.126)、high_fam_out (0.177)、unrelated (0.177)
- 負方向 (b < a、C2 で C 減): same_int_low_fam (-0.153)、temporal (-0.062)、same_step (-0.063)
- → Step F 仮説の構造的解釈: 若い cid に発火するとき、**familiarity 経路が活発化、Integration 内 (same_int_low_fam) は逆に減少**

#### 観察 3: QC_cost 感度ゼロの構造的理由

A2 は Q コスト 2、C 獲得 2 で計算的減算のみ、実 ledger 不変。`delta_C` は実 ledger の C 変化なので、Q/C コスト変更の影響を受けない (post-process 仕様の限界)。

→ **v10.10 で「実 simulation を回す」必要があるか?** (要検討)。本 v10.9 段階では「Q/C コスト感度はほぼ判定不能」と記録。

#### 観察 4: cid_selection 感度の小ささ

B3 (random cid) で top_k 100 と大差なし。可能性:
- atom_intro 後の 100 cid 選定では sim 上位と random で平均的な C 波及が変わらない
- ただし bimodal の構造 (Step F) は出ている → 高 delta cid (= 若い cid) は両条件で同程度に存在
- → cid 選定は「平均的 C 波及」では見えず、「特定 cid 群の感度」(Step M で要分析) で差が出る可能性

#### 観察 5: integration α/β 全条件で 0

v10.8 既知の no_signal フラグ。Q/C コスト変更でも cid 選定変更でも timing 変更でも、Integration 経路では C 変化 0。

→ v10.10 への含意: Integration 系統での入力理解は別の機構 (例: relation_strength や hop_distance) で評価する必要。

---

## 3. 主要発見の含意 (Step F + Step I 統合)

### 3.1 Step F (構造) と Step I (感度) の対応

| Step F (bimodal 構造) | Step I (sensitivity) | 整合 |
|---|---|---|
| H3_lifecycle 60.2% で支配 | C2 (lifecycle 同調) timing で最大感度 | ✓ |
| H3 99% で「高 delta = 若い cid」 | C2 で familiarity/attention で正方向 | ✓ |
| temporal で H3 が 74% (圧倒) | timing 感度は temporal で僅か (-0.062) | △ |

**△ の理由**: 「temporal_coactivation で H3 支配」は **bimodal 構造** (高 delta cid と低 delta cid の差)、「C2 で C 増」は **平均効果量**。
- C2 で若い cid に発火 → 高 delta 群は強くなるが、低 delta 群は無反応のまま
- 平均すると相殺されて感度小さい
- → bimodal 解析と感度解析は補完関係 (Step M で詳細解析)

### 3.2 出口固定 (4 種設計表) への素材

#### 表 1: sensitivity_summary (Step I の主要結果)

| comparison | metric | path | window | cohens_d (seed 0) |
|---|---|---|---|---:|
| timing | mean_delta_C | familiarity | medium | 0.161 |
| timing | mean_delta_C | high_fam_out | medium | 0.177 |
| timing | mean_delta_C | attention | medium | 0.126 |
| QC_cost | (全 path × win) | (no signal、limit 記録) | - | ~0 |
| cid_selection | (全 path) | (small effect) | - | <0.1 |

→ 24 seeds 集計 (Step M) で安定性を確認。

#### 表 4: 自然さの設計基準への素材

C2 vs A1 で familiarity / attention で 0.13-0.18 効果量 → **「lifecycle 早期 cid への精密入力」が natural に近づく方向の素材** (Step M で natural baseline と比較)。

---

## 4. 計算量と main 推定

### 4.1 smoke 実測

- seed 0、540 rows、0.19 秒
- A1 atom 抽出 (v108 read + filter): 約 0.1 秒
- 比較計算: 約 0.05 秒

### 4.2 main 推定

- 24 seeds × 0.2 秒 = **5 秒順次** / 並列 1 秒未満
- ストレージ: 540 rows/seed × 24 = 12,960 rows ≒ **<200 KB**
- A1 baseline は v10.8 main から read のみ (新規生成不要)

### 4.3 main 実行タイミング

- Step J 統合 smoke で 1 seed × 3 conditions の動作確認
- Step L (24 seeds main run) 後の Step M で本格集計

---

## 5. 制約と留保事項

### 5.1 QC_cost 感度評価の限界 (新規留保)

```
v10.9 留保事項: Q/C コスト感度の post-process 限界

- A2 (Q-2/C+2) は計算的減算 (Q_after = Q_pre - 2) のみ、実 ledger 不変
- delta_C は実 ledger の C 変化なので、Q/C コスト変更の影響なし
- 結果: QC_cost 感度が全 path で ~0 (effect 不検出)
- 解釈: 「Q/C コスト感度評価は post-process では不能」
- v10.10 への含意: 実 simulation を再回す必要があるか? (主題決定時に再議論)
```

これは v10.7 で確立した「物理層 frozen」の規律と整合。post-process だけでは見えない感度がある。

### 5.2 cid_selection 感度の小ささ

平均的 C 波及では top_k vs random で差が出ない。Step M で:
- atom 別に分けて解析
- 高 sim cid と低 sim cid の差を取る
- bimodal 解析と統合する (Step F の H1_n_core 仮説と組合せ)

→ 真の cid 選定感度は「per-cid 解析」で見える可能性。

---

## 6. Step J 進行への申請

Step J (統合 smoke + bit-identity 全層検証 + storage / 計算量実測) に進む許可を求めます。

### 6.1 Step J の作業内容

```
1. 全 condition (A2, B3, C2) を seed 0 で smoke 統合実行
   - atom_event_generator → baseline_recalculator → sensitivity_evaluator
   - 計算量実測 (smoke)
2. bit-identity 検証
   - 層 A: 同 seed 同 condition で 2 回回して MD5 一致
   - 層 B: v10.7/v10.8 main 出力の MD5 が変わらない
   - 層 C: 出力パス v109/ 配下強制
3. storage 実測 (smoke seed 0)
   - main run 推定 (24 seeds × 3 conditions)
4. Step K で smoke 結果報告 → Web Claude / Taka が main run 判定
```

### 6.2 Step J スクリプト (orchestrator)

`v109_post_process.py` (新規) を Step J で作成、v108_post_process.py をベースに:
- 3 conditions (A2, B3, C2) 順次 / 並列実行
- bit-identity 層 A/B/C 統合検証
- 全 step (atom_event → baseline → sensitivity) を 1 コマンドで

---

## 7. Step I 完了条件チェック

- [x] v109_sensitivity_evaluator.py 実装
- [x] 3 比較 (QC_cost / cid_selection / timing) ロジック確立
- [x] 6 metrics × 3 windows × 10 paths = 180 cells/比較
- [x] Cohen's d 計算
- [x] seed 0 smoke 0.19 秒で完了 (540 rows)
- [x] 主要発見 (timing > cid > QC) を抽出
- [x] QC_cost 感度ゼロを留保事項として記録
- [x] storage 軽量 (<200 KB / 24 seeds)

---

*以上、Code A による v10.9 Step I 完了報告。Web Claude / Taka からの Step J (統合 smoke + bit-identity) 進行許可待ち。*
