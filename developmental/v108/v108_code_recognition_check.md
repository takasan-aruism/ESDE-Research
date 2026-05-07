# v10.8 Code A 認識確認文書

*作成*: 2026-05-07、Code A
*親*: `v108_implementation_brief.md`
*目的*: 実装着手前の認識確認 (指示書 §0 の 12 項目を含む)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

v10.8 implementation brief を精読、実環境を事前確認した結果 **重大ブロッカー 2 点 + 設計の甘さ 5 点** を検出 (v10.7 で発見した 6 件と同種の前提条件不整合)、特に **「物理層 frozen と Q 消費 (§2.3) の論理的矛盾」** と **「26 atom 選定基準の不在 (主題ドキュメント repo 不在)」** が実装着手前の判断を要する、stretching baseline での storage 予算は v10.7 の 2-3 GB 増 (= 合計 2.5-3 GB、上限 6 GB 以内)、実装時間 12-15 時間予想、残課題は Web Claude / Taka に質問事項として §12 にまとめている。

---

## 1. 主題の理解 (項目 1)

**v10.8 の主題**: v10.7 の natural source_event 観察オービスを拡張し、**v10.6 atom 類似度上位 cid に "atom_introduction_event" を Pulse 同一フォーマットで人工的に注入** (= source_event 第 6 種、26 atom × 100 events × 24 seeds = 62,400 events)、その波及を 5 + 1 種 baseline + global activation 補正で評価し、Level 1-3 + Level 3.5 (introduced vs natural) の階層で「ESDE が atom 概念に対して特異な反応をするか」を観察。物理層は post-process で frozen、副次観察 3 件 (Whiteout / Small-World / 誤差分布) は主題判定外。

→ 認識は明確。実装の意味的目的は「外部 atom event を ESDE が natural event と区別して波及させるか」を観察すること。

---

## 2. atom_introduction_event の Pulse フォーマット同一性 (項目 2)

### 2.1 Pulse の実態 (環境確認)

`pulse_log_seed*.csv` は **35 列** の per-pulse record:

```
seed, cid, t, window, pulse_n, trigger, tags,
d_social, delta_social, theta_social, R_social,
d_stability, delta_stability, theta_stability, R_stability,
d_spread, delta_spread, theta_spread, R_spread,
d_familiarity, delta_familiarity, theta_familiarity, R_familiarity,
v11_b_gen, v11_delta, v11_d_n, v11_d_s, v11_d_r, v11_d_phase,
v11_p_capture, v11_captured, v11_n_local, v11_s_avg_local, v11_r_local,
v11_theta_avg_local
```

→ Pulse は 4 disposition 軸 × 4 フィールド (d / delta / theta / R) + v11 capture metrics。 atom_introduction_event はこれらの値を **どう設定するか** が指示書に記載なし。

### 2.2 「同一フォーマット」の現実

「Pulse と同一フォーマット」を厳密に取ると、atom_introduction_event は 35 列全部に値を入れる必要。具体的に:
- d_social / delta_social / theta_social / R_social: atom 注入で disposition は変わらないので 0?
- v11_b_gen 等の v11 系列: atom_introduction_event は cid の β-gen ad-hoc 評価とは無関係なので 'unformed'?
- trigger 列: 既存値は `MAD_DT_Major` 等。atom_introduction_event 用に新値 `atom_intro` を追加?

→ **実態は「Pulse 形式に近い source_event 第 6 種」**。完全同一は不可能。

### 2.3 v10.7 オービスとの整合

v10.7 の event_aggregator では Pulse 全列は使わず、**`(seed, cid, t)` 主キー + `R_familiarity` + `delta_*` のみ** を pre_event_state として merge_asof している。v10.8 でも同様の最小スキーマで十分。

→ **判定**: 「同一フォーマット」を **「v10.7 source_event スキーマ (event_id, source_cid, timestamp, pre_event_state) と互換」** と緩和して実装可能。Pulse 35 列全部は不要。Web Claude / Taka 確認願う (§12 Q1)。

---

## 3. Q/C エネルギーコストの実装方法 (項目 3)

### 3.1 重大ブロッカー A: 物理層 frozen と Q 消費の論理的矛盾

指示書 §2.3:
> Pulse と同等の Q/C 消費 (Pulse 1 回あたりの Q 消費 (例: -1) と同じ)

しかし指示書 §7.1:
> 既存 v10.5 / v10.6 / v10.7 出力ファイルを変更しない

→ post-process で **Q 消費すると物理層 (Q ledger) を変更することになり矛盾**。

### 3.2 解決案 (Code A 推奨)

**Q/C 消費は post-process 解析テーブル内のみ「計算的に減算」、実 v10.5 出力は不変**:

```python
# v108 解析テーブルで:
atom_event_record = {
    "source_cid": cid_X,
    "timestamp": t,
    "Q_pre": Q_real_at_t,        # v10.5 出力から merge_asof で取得
    "Q_after_atom_event": Q_real_at_t - 1,  # 計算的に -1 (実 ledger 不変)
    ...
}
```

これにより:
- v10.5 / v10.6 / v10.7 出力は完全 frozen (層 B PASS 維持)
- post-process 上で「動的平衡が維持されるかの観察」は可能
- 物理層改変なし

→ Web Claude / Taka 確認願う (§12 Q2)。

### 3.3 Pulse の Q 消費の実態

`per_event_audit_seed*.csv` の `v14_spend_flag == True` は spend event:
- spend events: 3,280/seed
- mean q_consumed (v14_q0 - v14_q_remaining): 10.4 (= cid lifetime 累積)

これは **per-event 単位の Q 消費** で、Pulse 1 回あたりの Q 消費は別物。pulse_log には Q 消費列がない。

→ Pulse 自体は disposition update であり、Q 消費は **balance_decisions で発火する別の event** (cognition / consciousness)。

→ atom_introduction_event の Q 消費を Pulse "同等" とする際、何を基準にするか不明確。**Web Claude / Taka 確認願う (§12 Q3)**。

---

## 4. 案 Q (top_k cid) で source_cid 選定 (項目 4)

### 4.1 環境確認 (使えるデータ)

`developmental/v106/outputs/main/atom_cid_topk_seed*.csv`:
- 325 atom × top 10 cid (各 atom について類似度上位 10 cid)
- 列: `seed, atom, rank_1_cid, rank_1_sim, ..., rank_10_cid, rank_10_sim`
- atom 視点 → 案 Q に直接利用可

### 4.2 指示書「目安 20」と実態「top 10」の差

指示書 §2.1:
> 類似度が高い top_k cid (k は Code A 判断、目安 20)

→ 実環境は **top 10 のみ保存**。20 を取るには v10.6 cid_atom_sim_matrix から再計算必要。

### 4.3 source_cid 候補 100 個 / atom

指示書 §2.1: 各 atom について **100 個の source_cid 候補** が必要。

実態:
- v10.6 atom_cid_topk: top 10 のみ
- 100 cid を確保するには、v10.6 cid_atom_sim_matrix (5,224 cid × 326 atom × 24 seeds) から **上位 100** を再抽出する必要

→ 24 seeds × 326 atom × 100 cid = 約 78 万 record の atom × cid mapping を v10.6 sim matrix から再計算可能。実装時間 +30 分。

### 4.4 source_cid の seed 越境問題

各 cid は seed-specific (seed 0 の cid 100 と seed 1 の cid 100 は別個体)。**atom × source_cid 候補は seed 単位で構築する**。
- 24 seeds × 26 atom × 100 cid = 62,400 candidates
- これは指示書の 26 × 100 × 24 = 62,400 events と一致 (各 atom × 各 cid で 1 event)

→ 設計と整合。

---

## 5. 案 α (均等分散発火) のスケジューリング (項目 5)

### 5.1 25,000 step の分散

26 atom × 100 events × 24 seeds = 62,400 events
- 1 atom あたり 100 events / seed = 25,000 step を 250 step 間隔で
- 26 atom 同時発火回避: atom_index × 9.6 step ずらし (250/26)

### 5.2 同時刻発火の最小化アルゴリズム

```python
for atom_index in range(26):
    base_offset = (atom_index * 9) % 250  # 9.6 ≈ 9
    timestamps = [base_offset + i * 250 for i in range(100)]
    # 各 atom は base_offset を起点に 100 events を 250 step 間隔
```

26 atom 全部で 2,600 events / seed が 25,000 step に分散、同時刻 ≤ 2 atom (確率的)。

### 5.3 cid x timestamp の整合

各 atom について source_cid 100 個 (top_k から選定) を 100 events に割り当て。1 cid = 1 event/atom (重複なし)。

→ 実装可能、Code A 判断で問題なし。

---

## 6. 5 + 1 種 baseline + global activation 補正 (項目 6)

### 6.1 v10.7 5 種 baseline は流用可能

`v107_baseline_constructor.py` の `build_baselines()` をそのまま流用。

### 6.2 6 種目 (natural source_event baseline) の実装

v10.7 の出力 `excess_change_seed*.parquet` に既に「relation_path_type が pulse / ingestion / alpha_formation / beta_formation / c_conversion」の各 source の delta が記録されている。

→ v10.8 では atom_introduction_event の delta を v10.7 の 5 source 種別ごとの mean delta と直接比較すれば良い。**新規 baseline 構築 0、v10.7 既存出力の集計のみ**。

### 6.3 global activation 補正

```python
global_activation_factor(step) = total_pulse_count(step) + total_event_count(step)
```

- pulse_log で step 単位 group_by して count
- ingestion_events / balance_decisions / alpha/beta_lifecycle も step 単位 count
- 25,000 step × 24 seeds = 600,000 step records → 軽量

実装可能。

### 6.4 補正の意味的妥当性

`adjusted_baseline_excess_change = raw - normalize(global_activation_factor(step))`

→ これは **時間相関の除去** だが、global activation factor 自体が baseline_excess_change と相関している場合 (= source_event は global activation の一部) **過剰補正のリスク**。

→ Code A 推奨: global activation を atom_introduction 自身を **除外** して計算 (= natural events のみ)。**Web Claude / Taka 確認願う (§12 Q4)**。

---

## 7. 副次観察 3 件の実装可能性 (項目 7)

### 7.1 Whiteout 監視 (Gemini A1)

**実装ロジック**: 26 × 26 atom ペアで 2-step time-window 内の波及プロファイル相関係数を計算。
- atom_a, atom_b の event timestamp が ± 5 step 以内のペアを抽出
- 両 event の post_event_delta vector で相関係数
- 0.7 以上で whiteout_flag

**計算量**: 26 × 26 = 676 ペア × 各 100 event ≈ 67,600 計算、軽量。

### 7.2 Small-World 維持確認 (Gemini A6)

**実装ロジック**: v10.8 main run の resonance_loops 集計値を v10.7 と比較。
- v10.8 で familiarity 経路の loop_2_hop / loop_3_hop は v10.7 と **完全同じ** (atom_introduction_event は familiarity edge を変更しない)
- → **本質的に変化なし** が保証される

→ **判定**: 副次観察として記録するが、変化が出ないことが構造的に確定。記録のみで主題判定外。

### 7.3 誤差分布の形状観察 (Gemini A5)

**実装ロジック**: 各 atom × relation_path × window で delta 分布を集計、**bimodality coefficient** (Sarle's 公式) と skewness/kurtosis を計算。

```python
b = (g^2 + 1) / (k + 3 * (n-1)^2 / ((n-2)*(n-3)))
# g: skewness, k: kurtosis, n: sample size
# b > 5/9 ≈ 0.555 で多峰性疑い
```

**計算量**: 26 atom × 7 path × 3 window = 546 records、軽量。

---

## 8. 環境チェック結果 (項目 8)

### 8.1 利用可能データ (確認済)

| データ | パス | 状態 |
|---|---|---|
| atom_cid_topk (atom × top 10 cid) | `developmental/v106/outputs/main/atom_cid_topk_seed*.csv` | ✓ 25 cols × 325 rows |
| atom_profiles_cache | `developmental/v106/outputs/main/atom_profiles_cache.npz` | ✓ (326, 48) float32 |
| cid_atom_sim_matrix (top 100 抽出用) | `developmental/v106/outputs/main/cid_atom_sim_matrix_seed*.parquet` | ✓ 24 seeds 全部 |
| v10.7 excess_change | `developmental/v107/outputs/main/excess_change_seed*.parquet` | ✓ 24 seeds (natural baseline 用) |
| v10.7 source_events | `developmental/v107/outputs/main/source_events_seed*.parquet` | ✓ |
| v10.7 流用関数 | `v107_event_aggregator.py`, `v107_path_analyzer.py`, `v107_baseline_constructor.py`, `v107_avalanche_monitor.py` | ✓ |

### 8.2 不在データ (= 設計の甘さ G)

| データ | 影響 |
|---|---|
| **v108_phase_design.md** (主題ドキュメント) | repo 不在、Web Claude のみ。**26 atom 選定基準が不明** |

### 8.3 26 atom 選定基準の不在

指示書 §1.2 / §2.1 で「26 atom 対象」と記載があるが、326 atom 中どの 26 を選ぶかの基準が不明:
- 主題ドキュメント (`v108_phase_design.md`) にあると思われるが repo 不在
- top 26 atom by 何? (出現頻度 / 接地度 / カテゴリ均等等)
- WLD.artless を除く 25 atom + 1 = 26 という意味?

→ **重大ブロッカー B**。Web Claude / Taka 確認必須 (§12 Q5)。

---

## 9. 設計の甘い部分 (項目 9、Code A 視点で 7 点)

### 9.1 重大ブロッカー (2 点、実装前に判断必須)

**A. 物理層 frozen と Q 消費の論理的矛盾** (§3 で既述)
→ 解決案: post-process 計算的減算のみ、実 ledger 不変

**B. 26 atom 選定基準の不在** (§8 で既述)
→ 主題ドキュメント参照 or 基準を Web Claude が指定要

### 9.2 設計修正必要 (5 点)

**C. Pulse 同一フォーマット の現実**: Pulse 35 列全部不要、v10.7 source_event スキーマ互換で十分 (§2 で既述)

**D. top_k cid 100 個の取得**: v10.6 atom_cid_topk は top 10 のみ、cid_atom_sim_matrix から再計算で 100 取得 (§4 で既述)

**E. global activation の自己補正リスク**: atom_introduction_event を除外した natural のみで factor 計算 (§6 で既述)

**F. Q/C 消費量の基準値**: pulse_log には Q 消費列なし、balance_decisions の cognition/consciousness の Q 消費を参考にすべきか? (§3 で既述)

**G. Small-World 維持の構造的保証**: atom_introduction_event は familiarity edge を変更しないため、本質的に v10.7 と同じ。観察として「変化なし」が記録される (§7 で既述)

---

## 10. 実装予想時間 (項目 10)

| ステップ | 予想時間 |
|---|---|
| 認識確認 (本文書) | **完了** (約 1 時間) |
| 環境チェック詳細 (`v108_environment_check_report.md`) | 30 分 |
| `v108_atom_event_generator.py` (案 Q + α) | 2 時間 |
| `v108_event_aggregator_extension.py` (第 6 種 source_event) | 1 時間 |
| `v108_global_activation_correction.py` | 1 時間 |
| `v108_whiteout_monitor.py` | 30 分 |
| `v108_smallworld_comparison.py` | 30 分 |
| `v108_error_distribution.py` (副次観察 3 件目) | 30 分 |
| `v108_post_process.py` (orchestrator、v10.7 流用) | 1 時間 |
| smoke test (seed 0) | 30 分 |
| 修正イテレーション | 1 時間 |
| main run (24 seeds 並列、v10.7 推定 4 分の 1.3 倍) | 5-10 分 |
| Level 1-3.5 reports + 総括 (6 reports) | 2.5 時間 |

**合計**: 12-13 時間 (1.5 日相当)

v10.7 の機構を最大限再利用できるため、新規実装は最小限。

---

## 11. ストレージ予算 (項目 11)

### 11.1 v10.7 実績

- 24 seeds 合計 428 MB (上限 6 GB の 7%)
- per-seed 17.8 MB (5 source_event × 5 path × 5 baseline + multi_hop + delta + ...)

### 11.2 v10.8 増分予想

**追加分**:
- atom_introduction_events: 26 atom × 100 events × 100 target × 18 fields × 8B / 24 seeds = **約 109 MB/seed**
  → parquet 圧縮後 **約 30-50 MB/seed**
- v10.7 全機構を atom_introduction_event について再実行: **約 18 MB/seed**
- 副次観察 (Whiteout / Small-World / 誤差分布): 各 1 MB/seed 以下、合計 **約 3 MB/seed**

**v10.8 合計**: 17.8 (v10.7 維持) + 50 (atom intro) + 3 (副次) = **約 71 MB/seed × 24 = 1.7 GB**

→ 上限 6 GB の **28%**。修正案 D (pulse 1/5 サブサンプリング) **不要**。

### 11.3 smoke で実測してから判断

- smoke seed 0 で実 storage 確認
- 70 MB/seed 以下なら v10.7 と同じ運用で十分
- 超過したら parquet 圧縮レベル up (snappy → gzip) で 20-30% 追加圧縮可能

---

## 12. Web Claude / Taka への質問・確認事項 (項目 12)

### 12.1 即決を要する判断 (実装着手前に確定)

1. **Pulse 同一フォーマットの解釈**: Pulse 35 列全部 vs v10.7 source_event 互換スキーマ → **後者で進めて良いか**
2. **Q/C 消費の実装場所**: 実 v10.5 ledger 不変 + post-process 計算的減算 → **これで物理層 frozen 規律を維持して良いか**
3. **Pulse の Q 消費基準値**: pulse_log には Q 消費列なし、何を「Pulse 1 回の Q 消費」と定義するか (例: balance_decisions.consciousness の Q_at_decision - q_remaining_after の中央値、あるいは固定 -1)
4. **global activation の自己補正回避**: atom_introduction_event 自身を除外した natural events のみで factor 計算 → これで合意して良いか
5. **26 atom 選定基準** (重大ブロッカー B): 主題ドキュメント `v108_phase_design.md` を repo に commit するか、Web Claude が選定基準を明示するか
6. **top_k cid 100 個の調達**: cid_atom_sim_matrix から再計算で取得して良いか (atom_cid_topk は 10 まで)

### 12.2 実装中の判断 (smoke 後に確認)

7. Whiteout 相関係数の閾値 (0.7 推奨)
8. error_distribution の bimodality 閾値 (Sarle's 5/9 ≈ 0.555 推奨)
9. Small-World 副次観察は **構造的に変化なし** が確定するため、観察として記録のみで主題判定から外す扱いで良いか
10. WLD.artless の atom_introduction_event を実際に発火させるか、最初から除外か (指示書では「他 atom と同様に発火、集計から除外」)

### 12.3 v10.8 範囲確認

11. v108_phase_design.md を repo に commit するか
12. **stretching baseline 命名**: 指示書 §1.3 では `same_step_random_baseline` 等の v10.7 命名を継承、v10.8 では同名で良いか (新規命名の意図がない場合)

---

## 13. Code A 推奨の進行手順 (修正版)

```
Step A: 本文書を Web Claude / Taka が確認、§12 即決 6 項目を確定
Step B: Code A が修正された設計で実装着手
Step C: 環境チェック詳細 (`v108_environment_check_report.md`)
Step D: atom_event_generator (案 Q + α、26 atom × 100 events × 24 seeds 生成)
Step E: source_event 第 6 種統合、v10.7 機構流用で全 path × baseline 集計
Step F: global activation 補正
Step G: 副次観察 3 件 (Whiteout / Small-World / 誤差分布)
Step H: 統合 smoke (seed 0、bit-identity 検証、storage 実測)
Step I: 24 seeds 並列 main run (multiprocessing 24 workers、v10.7 と同じ)
Step J: Level 1-3.5 reports + 総括 (6 reports)
```

各 Step で完了報告し、Web Claude / Taka 確認を取る。

---

## 14. 完了条件チェック (本文書の)

- [x] §0.1 の 12 項目を網羅
- [x] 主題の理解 (3-5 行)
- [x] Pulse フォーマット同一性の判定 + 修正案
- [x] Q/C 消費の実装方法判定 + 矛盾の指摘
- [x] 案 Q の実装可能性 + 修正案
- [x] 案 α のスケジューリング方法
- [x] 5 + 1 baseline + global activation の現実性
- [x] 副次観察 3 件の実装可能性
- [x] 環境チェック (利用可能 / 不在データ)
- [x] 設計の甘い部分 (7 点)
- [x] 実装予想時間 (12-13 時間)
- [x] ストレージ予算 (1.7 GB、上限 28%)
- [x] 質問事項 (12 項目)

---

*以上、Code A による v10.8 実装着手前認識確認文書。Web Claude / Taka の §12.1 即決 6 項目を待って実装着手します。*
