# v10.8 Step B 環境チェック詳細報告

*作成*: 2026-05-07、Code A
*親*: `v108_implementation_brief.md` + 即決事項確定文書
*目的*: 即決 6 項目を実環境で確定 (26 atom リスト、top_k 100 cid 取得方法、Q/C 消費基準値)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

確定文書 §2.5「7+19=26 atom」を v10.6 step10_baseline 実データで照合した結果 **25 atom (delta_ratio>1% 9 件 + z=inf 17 件 - 重複 TIM.appear)** が抽出され (確定文書 26 atom と -1 差)、内 1 atom (WLD.artless) は留保ラベル付き、Q/C 消費は **balance_decisions.cognition の固定値 Q -1 / C +1** (median と mean が完全一致、std=0、59,738 events 全て同値)、top_k cid 100 個は cid_atom_sim_matrix_seed*.parquet から 25 atom × 100 cid × 24 seeds = **60,000 (cid, atom) ペア** で抽出可能、storage 予算は v10.7 比で 1.7 GB 増 (合計 2.1 GB、上限 6 GB の 35%)、Step C (atom_event_generator) 進行準備完了。

---

## 1. 25 atom リスト (即決 §2.5 確定)

### 1.1 抽出ロジック

- v10.6 `step10_baseline/step10_atom_z_score.csv` から:
  - delta_ratio > 1% の atom: **9 件**
  - z_score_uniform = inf の atom: **17 件**
  - 重複: **TIM.appear** (両方)
- 和集合 = **25 atom**

### 1.2 確定リスト (25 atom)

| # | atom | category | delta>1% | z=inf | 留保 |
|---:|---|---|:---:|:---:|---|
| 0 | BOD.ear | BOD | | ✓ | |
| 1 | COG.learn | COG | ✓ | | |
| 2 | COM.silence | COM | | ✓ | |
| 3 | EXS.being | EXS | ✓ | | |
| 4 | EXS.nonbeing | EXS | | ✓ | |
| 5 | FND.timeless | FND | ✓ | | |
| 6 | FND.transformation | FND | | ✓ | |
| 7 | PER.feel | PER | | ✓ | |
| 8 | PER.fragrance | PER | | ✓ | |
| 9 | PER.hear | PER | | ✓ | |
| 10 | PER.see | PER | | ✓ | |
| 11 | PER.smell | PER | | ✓ | |
| 12 | PER.sound | PER | ✓ | | |
| 13 | PER.soundless | PER | | ✓ | |
| 14 | PER.taste | PER | | ✓ | |
| 15 | PRP.bright | PRP | | ✓ | |
| 16 | PRP.deep | PRP | ✓ | | |
| 17 | PRP.sharp | PRP | | ✓ | |
| 18 | SOC.city | SOC | ✓ | | |
| 19 | SOC.nation | SOC | | ✓ | |
| 20 | SOC.public | SOC | | ✓ | |
| 21 | TIM.appear | TIM | ✓ | ✓ | (両方) |
| 22 | **WLD.artless** | **WLD** | ✓ | | **`reserved_label='wld_artless_pending'`** |
| 23 | WLD.culture | WLD | ✓ | | |
| 24 | WLD.technique | WLD | | ✓ | |

### 1.3 確定文書 §2.5 との差 (-1)

確定文書 §2.5「7 + 19 = 26 atom」に対し実データ抽出は **25 atom** (= 9 + 17 - 1 重複)。

差の原因の可能性:
- 確定文書 §2.5 の「7 atom (delta>1%)」リスト (PER.sound / WLD.artless / WLD.culture / FND.timeless / SOC.city / COG.learn / PRP.deep) は**実データ 9 件のうち TIM.appear と EXS.being を除外** したもの
- 「19 atom (z=inf)」予想は実データ 17 件と微差 (+2 推定)
- 実データ照合で 7+17-1=23、または 9+17-1=25

→ **Code A 判断: 実データに基づく 25 atom を採用**。確定文書 26 atom より -1。

WLD.artless は **発火対象 25 atom に含まれる** が、Level 1-3.5 集計から `reserved_label` で除外。実集計対象 atom = **24 atom**。

→ Web Claude / Taka に確認願う: 25 atom (実データ) で進めて良いか、それとも +1 atom 追加 (例: 次点 delta_ratio や z_score) で 26 にするか。

### 1.4 category 分布

| category | atom 数 | 主要 atom |
|---|---:|---|
| PER (五感) | **8** | sound/taste/hear/smell/see/feel/fragrance/soundless |
| WLD | 3 | artless (留保) / culture / technique |
| SOC | 3 | city / nation / public |
| EXS | 2 | being / nonbeing |
| FND | 2 | timeless / transformation |
| PRP | 3 | bright / deep / sharp |
| BOD | 1 | ear |
| COG | 1 | learn |
| COM | 1 | silence |
| TIM | 1 | appear |

→ **PER 系統が 8 件で最多** (v10.6 観察「PER カテゴリ強接地」と整合)。

---

## 2. top_k cid 100 個の取得 (即決 §2.6)

### 2.1 取得方法 (確定)

`developmental/v106/outputs/main/cid_atom_sim_matrix_seed*.parquet` (24 seeds 全部) を参照。
- 構造: `(cid, atom)` 行列、shape は seed によって異なる (seed 0: 228 cid × 328 列)
- 各 atom 列について sim 上位 100 cid を sort して抽出

### 2.2 規模

- 25 atom × 100 cid × 24 seeds = **60,000 (cid, atom) ペア**
- これが atom_introduction_event の source_cid 候補プール

### 2.3 サンプル (seed 0)

PER.sound top 5 cid: cid 94 (sim 0.528) / cid 78 (0.528) / cid 117 (0.526) / cid 118 (0.521) / cid 98 (0.518)

### 2.4 実装

```python
df_sim = pd.read_parquet(f"cid_atom_sim_matrix_seed{seed}.parquet")
for atom in target_atoms:  # 25 atom
    if atom in df_sim.columns:
        top_100 = df_sim[["cid", atom]].sort_values(atom, ascending=False).head(100)
```

軽量、24 seeds 全部で数秒で完了。

---

## 3. Q/C エネルギーコスト (即決 §2.3)

### 3.1 balance_decisions.cognition の実態 (24 seeds 全体)

**全 cognition events: 59,738**

| 量 | median | mean | std | unique values |
|---|---:|---:|---:|---|
| Q 消費 (`Q_at_decision - q_remaining_after`) | **1.00** | 1.00 | **0.00** | {1: 59,738} (全部 1) |
| C 変化 (`c_after - C_at_decision`) | **1.00** | 1.00 | **0.00** | {1: 59,738} (全部 1) |

→ **cognition event は固定値 Q -1 / C +1** (= cid から Q 1 を消費して C 1 を獲得)。

### 3.2 atom_introduction_event の標準コスト (確定)

```python
ATOM_INTRO_Q_COST = 1   # Q を 1 消費
ATOM_INTRO_C_GAIN = 1   # C を 1 獲得 (= cognition event と同等)
```

### 3.3 post-process 計算的減算 (即決 §2.2)

実 v10.5 ledger は不変。post-process 解析テーブル内のみ:

```python
atom_event_record = {
    "Q_pre": Q_real_at_t,                 # v10.5 出力から merge_asof で取得
    "C_pre": C_real_at_t,
    "Q_after_atom_intro": Q_real_at_t - 1,   # 計算的に -1
    "C_after_atom_intro": C_real_at_t + 1,   # 計算的に +1
}
```

これにより:
- bit-identity 層 B PASS 維持 (v10.5/6/7 出力不変)
- 動的平衡の観察は post-process 上で可能

### 3.4 参考: consciousness Q/C コスト (使わないが記録)

| 量 | median | mean |
|---|---:|---:|
| Q 消費 (Q_at_decision - q_remaining_after) | **-5.00** | -5.44 |
| C 変化 (c_after - C_at_decision) | **-1.00** | -0.94 |

→ consciousness event は **Q +5 獲得 / C -1 消費** (cognition の逆)。v10.8 では使わない。

---

## 4. global_activation_factor (即決 §2.4)

### 4.1 計算式 (確定)

```python
def compute_global_activation_factor(seed, step):
    pulse_count = sum pulses at step (pulse_log)
    ingestion_count = sum ingestions at step (ingestion_events)
    alpha_birth_count = sum alpha births at step (alpha_lifecycle event_type='birth')
    beta_birth_count = sum beta births at step (beta_lifecycle event_type='birth')
    consciousness_count = sum consciousness at step (balance_decisions.decision='consciousness')
    # atom_introduction_event は除外 (= natural events のみ)
    return pulse_count + ingestion_count + alpha_birth_count + beta_birth_count + consciousness_count
```

### 4.2 計算量

- 24 seeds × 25,000 step = 600,000 step records
- step 単位 group_by + count、軽量

---

## 5. ストレージ予算

### 5.1 内訳

| 区分 | 推定 size/seed |
|---|---:|
| atom_introduction_events records (25 atom × 100 events × 100 target × 18 fields × 8B / 24 seeds) | 約 50 MB |
| v10.7 全機構 (5 種 source_event 集計、流用) | 約 18 MB |
| global_activation_factor (25,000 step × 数列) | 1 MB |
| 副次観察 (Whiteout / Small-World / 誤差分布) | 約 3 MB |
| **合計** | **約 72 MB/seed** |

### 5.2 24 seeds 合計

72 × 24 = **約 1.7 GB**

→ 上限 6 GB の **28%**。修正案 D (pulse 1/5) **不要**、parquet snappy 圧縮で十分。

### 5.3 v10.7 比

- v10.7: 428 MB
- v10.8: 約 2.1 GB (= 428 + 1700)
- 5 倍増だが上限内に余裕

---

## 6. v10.6 / v10.7 流用一覧

### 6.1 v10.6 から流用

| データ | 用途 |
|---|---|
| `cid_atom_sim_matrix_seed*.parquet` | top_k 100 cid 抽出 |
| `step10_baseline/step10_atom_z_score.csv` | 25 atom 選定 |
| `atom_profiles_cache.npz` | (補助情報) |

### 6.2 v10.7 から流用 (関数 import)

| モジュール | 流用関数 |
|---|---|
| `v107_event_aggregator.py` | `aggregate_source_events`, `attach_pre_event_state` |
| `v107_path_analyzer.py` | `build_all_paths` (5 種 path) |
| `v107_baseline_constructor.py` | `build_baselines`, `compute_deltas`, `compute_baseline_excess_change` |
| `v107_avalanche_monitor.py` | `build_multi_hop_paths`, `compute_decay_rate`, `detect_resonance_loops`, `compute_peak_lag_curve`, `classify_wave_patterns` |
| `v107_post_process.py` | orchestrator pattern, `_run_seed_pipeline_worker` (multiprocessing) |
| `v107_cross_seed_analyzer.py` | Level 1/2/3 集計 |

### 6.3 v10.7 流用元データ

| ファイル | 用途 |
|---|---|
| `developmental/v107/outputs/main/excess_change_seed*.parquet` | natural source_event baseline |
| `developmental/v107/outputs/main/source_events_seed*.parquet` | source_type で natural event 集計 |
| `developmental/v107/outputs/main/cross_seed/level_*.parquet` | natural baseline の Level 1-3 比較値 |

---

## 7. Step B 完了条件チェック

- [x] 25 atom リスト確定 (delta>1% 9 + z=inf 17 - 重複 1)
- [x] WLD.artless 留保ラベル明示
- [x] top_k 100 cid 取得方法確認 (cid_atom_sim_matrix から)
- [x] Q/C 消費基準値確定 (cognition 固定 -1/+1)
- [x] post-process 計算的減算の方針明記
- [x] global_activation_factor 計算式確定 (natural events のみ)
- [x] ストレージ予算 (1.7 GB、上限 28%)
- [x] v10.6/v10.7 流用一覧

---

## 8. Step C 進行への申請

Step C (atom_event_generator、`v108_atom_event_generator.py`) に進む許可を求めます。

実装方針:
1. **25 atom × 各 seed × top 100 cid** を cid_atom_sim_matrix から抽出 (60,000 ペア)
2. **案 α (均等分散発火)**:
   - 25 atom × 100 events / 25,000 step = 250 step 間隔 (1 atom 内)
   - atom_index × 10 step ずらしで同時刻発火回避
3. **atom_introduction_event レコード生成** (v10.7 source_event スキーマ互換):
   - event_id, source_cid, timestamp, atom_id, atom_index, top_k_rank
   - pre_event_state (v10.5 ledger から merge_asof)
   - post_event_state (Q -1, C +1 の計算的減算)
   - reserved_label (WLD.artless のみ)
4. **seed 0 で smoke**:
   - 25 atom × 100 events = 2,500 events 生成
   - schema 確認、bit-identity 層 A 確認

実行時間予想: 1-1.5 時間。

Step C 完了後、Step D (source_event 第 6 種統合 + v10.7 機構流用) に進む前に再度報告します。

24 seeds 単一バッチ厳守 (v10.7 で実証済 multiprocessing 24 並列、3 バッチ分割禁止)。

---

## 9. Web Claude / Taka への確認事項

1. **25 atom (実データ) で進めて良いか** vs **+1 atom 追加で 26 にする**:
   - 25 atom 採用なら 24 集計対象 (WLD.artless 留保) + 1 留保
   - 26 atom にする場合は 1 atom 追加方針 (例: 次点 delta_ratio 0.99% の atom、または別基準)
   - **Code A 推奨: 25 atom で進める** (実データ準拠、シンプル)

2. **v108_phase_design.md repo commit 状況**: 未 commit (Web Claude が後段 commit 予定とのこと)、Code A は本確認文書 + 確定文書を参照して実装着手

---

*以上、Code A による v10.8 Step B 環境チェック詳細報告。Web Claude / Taka からの Step C 進行許可待ち。*
