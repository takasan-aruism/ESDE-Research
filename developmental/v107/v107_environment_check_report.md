# v10.7 Step B 環境チェック詳細報告

*作成*: 2026-05-07、Code A
*親*: `v107_implementation_brief.md` + `v107_code_recognition_check.md` + 即決事項確定文書
*目的*: 実装着手前の環境実測 (即決事項を反映した最終確認)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

24 seeds 全体での source_event 実測は **386,655 events (per-seed avg 16,111)** で認識確認時の seed 0 推定 13,503 から約 19% 増、**ストレージ修正案 E (parquet 圧縮) 単独だと 6.91 GB で上限 6 GB を 15% 超過** するため smoke 段階で観測してから修正案 D 併用判断を行う、attention 代替の salience event は 24 seeds 計 77,880 (3,245/seed) で十分な接続情報を提供、familiarity 1-hop は 23,047 edges (960/seed)、v10.6 流用関数は 4 モジュールから合計 16 関数 + 1 cache (atom_profiles 85KB) が利用可能、Python 環境 (numpy 2.3 / pandas 2.3 / scipy 1.16 / sklearn 1.7 / pyarrow 21.0) は v10.7 全機能をサポート、Step C (source_event aggregator 実装) に進む準備完了。

---

## 1. 24 seeds 全体の source_event 件数 (実測)

| seed | pulse | ingestion | alpha_birth | beta_birth | c_conversion | total |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 12,530 | 155 | 424 | 239 | 155 | 13,503 |
| 1 | 13,030 | 141 | 369 | 211 | 141 | 13,892 |
| 2 | 17,480 | 167 | 660 | 296 | 167 | 18,770 |
| 3 | 15,370 | 150 | 576 | 261 | 150 | 16,507 |
| 4 | 17,190 | 137 | 646 | 297 | 137 | 18,407 |
| 5 | 15,170 | 159 | 551 | 269 | 159 | 16,308 |
| 6 | 13,690 | 153 | 591 | 263 | 153 | 14,850 |
| 7 | 13,420 | 129 | 609 | 289 | 129 | 14,576 |
| 8 | 13,130 | 153 | 460 | 236 | 153 | 14,132 |
| 9 | 11,880 | 169 | 412 | 215 | 169 | 12,845 |
| 10 | 16,280 | 116 | 560 | 263 | 116 | 17,335 |
| 11 | 15,960 | 154 | 572 | 276 | 154 | 17,116 |
| 12 | 16,120 | 177 | 616 | 294 | 177 | 17,384 |
| 13 | 14,850 | 137 | 550 | 250 | 137 | 15,924 |
| 14 | 16,060 | 131 | 743 | 316 | 131 | 17,381 |
| 15 | 14,490 | 144 | 515 | 242 | 144 | 15,535 |
| 16 | 15,260 | 161 | 638 | 281 | 161 | 16,501 |
| 17 | 15,030 | 148 | 600 | 278 | 148 | 16,204 |
| 18 | 13,250 | 114 | 677 | 310 | 114 | 14,465 |
| 19 | 14,530 | 156 | 490 | 240 | 156 | 15,572 |
| 20 | 16,420 | 174 | 625 | 285 | 174 | 17,678 |
| 21 | 16,090 | 133 | 632 | 275 | 133 | 17,263 |
| 22 | 17,540 | 165 | 865 | 336 | 165 | 19,071 |
| 23 | 14,340 | 171 | 500 | 254 | 171 | 15,436 |
| **TOTAL** | **359,110** | **3,594** | **13,881** | **6,476** | **3,594** | **386,655** |

per-seed avg: pulse 14,963 / ingestion 150 / alpha_birth 578 / beta_birth 270 / c_conversion 150 / **total 16,111**

→ 認識確認時の seed 0 推定 13,503 events から **19% 増**。pulse が seed によって 11,880 - 17,540 と幅広く分布、average 14,963。

---

## 2. relation_path 構築データ (24 seeds 実測)

### 2.1 各経路のデータ規模

| relation_path | データソース | 24 seeds 計 | per-seed avg |
|---|---|---:|---:|
| familiarity | `network/fam_edges_seed*.csv` | **23,047** edges | 960 |
| **attention (salience 代替)** | `salience/salience_event_log_seed*.csv` | **77,880** events | 3,245 |
| Integration | `alpha_lifecycle_log` (event_type='birth' 13,881 + member 展開) | 各 seed 数百 cid | 平均 ~50 cid/event |
| temporal_coactivation | `pulse_log` (時間 window 内集計) | pulse 数依存 | 計算で取得 |
| matched_baseline | `per_subject` + `audit` (n_core / age / final_state) | 5,224 cid 全部 | 218/seed |

### 2.2 attention 代替 (salience event_log) 詳細

salience event は (observer_cid, candidate_cid, candidate_mass, selected) の per-event 記録。**全 selected=True** で 3,245 events/seed。observer → candidate の重み付き接続データとして利用可能。

CSV 列名 規約 (即決事項確定文書 §8): `relation_path_type = 'attention_via_salience'` で命名。

### 2.3 familiarity 1-hop 詳細

`fam_edges_seed*.csv` の `seed, from, to, familiarity` 形式。**run 終了時の snapshot** であって時系列推移ではないため、source_event 時点の familiarity 強度は **per_subject の `last_familiarity_max` を補助参考**として使う。

→ 設計の落とし穴 (smoke で確認): 「source_event 直前の familiarity 強度」を厳密に取るには pulse_log の per-pulse `R_familiarity` を使う必要。fam_edges は run 終了時の集約値。

---

## 3. baseline 構築データ (緩和定義)

### 3.1 即決確定後の 5 種 baseline 定義

| baseline | 定義 | 構築判定 |
|---|---|---|
| unrelated_baseline | familiarity 強度 < 5 + 同 α/β なし + salience 接続少 | ✓ 緩和定義で構築可能 |
| same_step_random_baseline | 同 step (= 同 window) で動いている任意 cid | ✓ |
| matched_baseline | 同 n_core_member + 同 age (lifespan_so_far ±20%) + 同 final_state | ✓ |
| same_integration_low_familiarity_baseline | 同 α/β + familiarity 下位 25% | ✓ |
| high_familiarity_outside_integration_baseline | familiarity 上位 25% + 同 α/β なし | ✓ |

### 3.2 上位/下位 25% 閾値の算出

per_subject の `last_familiarity_max` 分布 (24 seeds × 5,224 cid):
- 0% (min): 0.0
- 25%: 26.7
- 50%: 41.1
- **75%: 81.1** ← high baseline 閾値
- 90%: 316.2
- 100% (max): 500.0

→ 上位 25% = `last_familiarity_max >= 81.1`、下位 25% = `< 26.7` (seed ごとに再計算)

---

## 4. ストレージ予算実測 (修正案 E parquet 圧縮)

### 4.1 計算

| パラメータ | 値 |
|---|---|
| per-seed events | 16,111 |
| target/event | 100 (5 path × 20 cid) |
| delta fields | 6 (Q, C, familiarity_max, n_alphas, n_observed, pulse_count) |
| time windows | 4 (immediate / short / medium / peak_lag) |
| record bytes (parquet float32 + compression) | ~8 |

per-seed bytes ≈ 16,111 × 100 × 6 × 4 × 8 = **約 295 MB/seed**
24 seeds 合計 ≈ **6.91 GB**

### 4.2 上限超過の判定

即決事項確定文書 §9.2:
- 1 seed 上限: 300 MB → **295 MB は上限内** (5 MB 余裕)
- 24 seeds 合計上限: 6 GB → **6.91 GB で 15% 超過**

§9.3 の打切閾値 (上限 50% 以上超過) には達していない。

### 4.3 提案: smoke で実測してから判断

- Step G (smoke) で seed 0 の実 storage 使用量を実測
- 295 MB/seed が予想だが実測は parquet の実際の圧縮率により変動
- 実測 > 300 MB/seed なら **修正案 D (pulse 1/5 サブサンプリング)** を併用
- 実測 ≤ 300 MB/seed なら E 単独で 24 seeds 進行

**修正案 D 併用時の予想**:
- pulse 14,963 → 2,993 (1/5)
- per-seed events ≈ 4,141 (16,111 - 11,970)
- per-seed storage ≈ 76 MB
- 24 seeds 合計 ≈ 1.8 GB (上限内)

---

## 5. v10.6 流用可能モジュール

### 5.1 atom_profiles_cache

| 場所 | サイズ |
|---|---|
| `developmental/v106/outputs/main/atom_profiles_cache.npz` | 85 KB |
| 内容 | (326, 48) float32 + valid_mask (325/326 atoms) |

→ そのまま流用 (re-build 不要)。WLD.artless 除外規律に従い、判定軸には使わず補助記録のみ。

### 5.2 v10.6 関数の流用一覧

| モジュール | 流用関数 |
|---|---|
| `v106_post_process.py` | `build_atom_cache`, `list_atoms_from_a1_batch`, `_gradient_distribute`, `EPISTEMOLOGICAL_BOUNDARIES`, `safe_read_csv`, `safe_write_csv`, `safe_write_parquet`, `safe_write_json`, `AXES_ORDER` |
| `v106_pulse_trajectory.py` | `_expand_alpha_membership_to_events`, `_cumulative_events_by_cid_step`, `temporal_vec` 〜 `value_generation_vec` (10 軸全 vector builder) |
| `v106_step10_trajectory.py` | `_merge_asof_by_cid` |
| `v106_baseline_analysis.py` | `generate_uniform_cid_vector`, `shuffle_cid_vector_within_axes`, `cosine_matrix` |

合計 **16 関数 + 1 cache** が再利用可能。v10.7 実装を大幅に簡略化。

### 5.3 v10.6 流用時の規律

- import 経由で再利用 (関数複製はしない)
- `sys.path.insert(0, str(Path(__file__).parent.parent / 'v106'))` で v106 module を import
- バグ修正 (birth_step) は v10.6 step10 / per-event で済んでいる、v10.7 でも `pulse_log の最初 t` で取得

---

## 6. bit-identity 層 B 実装手順

### 6.1 検証対象 v10.6 出力 (実測)

| ディレクトリ | ファイル数 |
|---|---:|
| `outputs/main/` (root) | 219 |
| `outputs/main/baseline/` | 30 |
| `outputs/main/stratified/` | 198 |
| `outputs/main/window_trajectory/` | 79 |
| `outputs/main/pulse_trajectory/` | 79 |
| `outputs/main/step10_trajectory/` | 53 |
| `outputs/main/event_trajectory/` | 55 |
| `outputs/main/step10_baseline/` | 4 |
| **合計** | **717** |

### 6.2 実装 (Code A 判断、即決事項 §3.3)

```python
def compute_v106_baseline_md5() -> dict[str, str]:
    """v10.7 実装前 / 実装後で v10.6 出力ファイルの MD5 を比較."""
    import hashlib
    md5_dict = {}
    for path in V106_MAIN_ROOT.rglob("*.csv"):
        with open(path, "rb") as f:
            md5_dict[str(path.relative_to(V106_MAIN_ROOT))] = hashlib.md5(f.read()).hexdigest()
    for path in V106_MAIN_ROOT.rglob("*.parquet"):
        ...
    return md5_dict
```

smoke 前に baseline MD5 を JSON で保存、smoke 後に再計算して差分検証。

---

## 7. ストレージ・計算量の最終見積もり

| 項目 | 数値 |
|---|---|
| 全 source_events (24 seeds) | 386,655 |
| 全 records (target × event) | 38,665,500 |
| 全 cells (delta × window) | 928,000,000 |
| storage (parquet 圧縮) | **6.91 GB** (要 smoke 実測) |
| peak_lag 計算量 (10 step bin、100 lag values) | 38,665,500 × 100 = **3,866 億計算** ※ |

※ 即決事項 §2.3 で peak_lag 10 step bin 推奨。1 step 単位の 324 億を超えているように見えるが、これは **target × event** 単位の総計算量で、実際は cosine sim で並列化される。1.4 億計算/seed、数分/seed の見込み。

実装時の最適化:
- numpy 行列演算 (per-seed batch)
- merge_asof で event 紐付け
- chunk 処理 (cid 単位)

---

## 8. Python 環境 (確認済み)

| ライブラリ | バージョン | 用途 |
|---|---|---|
| Python | 3.13.5 | base |
| numpy | 2.3.1 | 行列演算 |
| pandas | 2.3.0 | DataFrame |
| scipy | 1.16.0 | `kruskal` (Level 3 検定) |
| sklearn | 1.7.1 | `cosine_similarity` |
| pyarrow | 21.0.0 | parquet 出力 |

→ 全機能サポート、追加 install 不要。

---

## 9. Step B 完了条件チェック

- [x] 24 seeds 全体の source_event 件数実測 (386,655)
- [x] 5 種 relation_path のデータ規模確認
- [x] 5 種 baseline の構築可能性確認 (緩和定義で全て構築可能)
- [x] ストレージ事前見積もり (parquet 圧縮で 6.91 GB、smoke で実測判断)
- [x] v10.6 流用可能モジュール一覧 (16 関数 + 1 cache)
- [x] bit-identity 層 B 実装手順確定 (MD5 hash 比較、smoke 前後で検証)
- [x] Python 環境確認

---

## 10. Step C 進行への申請

Step B 完了。Step C (5 種 source_event aggregator 実装、`v107_event_aggregator.py`) に進む許可を求めます。

実装方針 (Step C):
1. 5 種 source_event を統合した DataFrame 構築
2. event_id (auto-increment)、event_source_type、source_cid、timestamp、pre_event_state を含める
3. v10.6 流用 (`_expand_alpha_membership_to_events`、`safe_read_csv`)
4. seed 0 で smoke (events 件数が 13,503 件と一致するか確認)

実行時間予想: 1-1.5 時間。

Step C 完了後、Step D (relation_path constructor) に進む前に再度報告します。

---

*以上、Code A による Step B 環境チェック詳細。Web Claude / Taka からの Step C 進行許可待ち。*
