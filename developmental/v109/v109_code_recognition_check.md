# v10.9 Code A 認識確認文書

*作成*: 2026-05-08、Code A
*親*: `v109_implementation_brief.md` + `v109_phase_design.md` + `v109_atom_residency_reservation.md`
*目的*: 実装着手前の認識確認 (指示書 §0 の 10 項目を含む)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

v10.9 implementation brief を精読、実環境を事前確認した結果 **設計の甘さ 7 点 + 重大ブロッカー 1 点** を検出 (v10.7 で 6 件、v10.8 で 7 件 + 重大 2 件と同種の前提条件不整合)、特に **重大ブロッカー A: 9 条件 (6 新条件) のストレージ予算が上限 72%** で要規模調整、Code A 推奨は **案 b (3 候補各 2 水準 = 6 条件のうち各候補 1 新条件 = 計 3 新条件)** で上限 18% に圧縮、bimodal 1,540 件解析と「系のリズム同調 (C2 水準)」は実装可能だが具体的アルゴリズムを Code A が確定して実装、出口固定 4 種設計表のフォーマットは Code A 判断で進める、Web Claude / Taka 即決事項 6 項目を §11 に整理、判定後に Step B (環境チェック詳細) → Step C-K へ。

---

## 1. 主題の理解 (項目 1)

**v10.9 の主題**: v10.8 で発見した 2 つの未解決点 (introduced < natural、bimodal 17.4%) を **「会話系設計のための部品調達」** として分離。寄与候補感度評価 (a、3 候補 × 2-3 水準で Q/C コスト / cid 選定 / 発火タイミング のノブを特定) + bimodal 構造解析 (d、1,540 件の二峰性で n_core 別 / Integration 内外 / ライフサイクル段階のどれに対応するかを特定) を post-process で実施、各変動条件で baseline 再計算 (新規規律)、4 層階層化 (L1-L3.5) を明示、出口固定として **v10.10 のための設計表 4 種** (感度 / 受信可能状態 / ルーティング / 自然さ) を成果物化。

→ 認識は明確。実装パスは v10.7/v10.8 の延長で見える。重大ブロッカー A (規模) と設計修正必要 6 件 (§9) を判断後、Step B 進行。

---

## 2. 9 条件の実装可能性と規模調整 (項目 2)

### 2.1 規模見積もり (実環境ベース)

v10.8 main run 実績から 6 倍推定:

| 案 | 新条件数 | events | storage | 実行時間 | 上限 6GB 比 |
|---|---:|---:|---:|---:|---:|
| **案 a (全 9 条件)** | 6 | 360K | **4.4 GB** | 32 分 | **72%** |
| 案 b (各候補 2 水準) | 3 | 180K | 2.2 GB | 16 分 | 37% |
| **案 c (各候補 1 水準ずつ動かす)** | 3 | 180K | 2.2 GB | 16 分 | 37% |

→ 案 a はストレージ上限 72% で **重大ブロッカー A** (打切閾値 50% 接近)。

### 2.2 Code A 推奨: 案 c (各候補 1 水準ずつ動かす、3 新条件)

理由:
- v10.8 標準 (A1, B1, C1) を流用、各候補で 1 つだけ別水準を試すミニマルセット
- 3 新条件: A2 (Q-2/C+2)、B3 (random cid)、C2 (リズム同調)
- 規模 v10.8 の 3 倍、storage 18% で十分余裕
- 各候補のノブの方向性を確認後、v10.10 で詳細水準を試せる
- 「第一試行は 2 水準か 3 水準に絞る」(GPT B1 規律) を遵守

→ Web Claude / Taka 確認願う (§11 Q1)。案 c 採用なら 3 新条件で進める。

### 2.3 規模調整の影響

3 新条件採用で:
- A1 (v10.8 標準) vs A2: Q/C コスト感度を 1 軸で評価
- B1 (v10.8 標準) vs B3: cid 選定の感度 (top_k vs random、Atom 326 絶対化禁止確認)
- C1 (v10.8 標準) vs C2: タイミング感度 (均等分散 vs リズム同調)

→ 3 候補それぞれで方向性は確認できる。中間水準 (A3 / B2 / C3) は v10.10 以降の射程。

---

## 3. 各変動条件で baseline 再計算 (項目 3、GPT B6 新規規律)

### 3.1 実装方針

各新変動条件で:
1. v10.7 baseline_constructor.build_baselines() を再実行 (該当条件の atom_introduction_event を含む)
2. global_activation_factor を再計算 (natural events のみ、atom_intro 除外、即決 §2.4 規律)
3. excess_change の adjusted_* 列を再計算

### 3.2 計算量

- 3 新条件 × 24 seeds × baseline 計算 87 秒 = 約 6,300 秒 (1.75 時間)
- 並列 24 workers で約 300 秒 (5 分)
- 全機構統合 main run で 16 分以内

### 3.3 流用元

- v107_baseline_constructor.py (build_baselines, compute_deltas)
- v108_global_activation_correction.py (compute_global_activation_factor)

→ 実装可能、新規実装は最小限。

---

## 4. bimodal 構造解析 (項目 4)

### 4.1 解析対象 (実環境確認済)

`developmental/v108/outputs/main/error_distribution_seed*.parquet`:
- 24 seeds 全合計: **8,835 rows**
- bimodal: **1,540 件 (17.4%)**
- 列: atom_id / relation_path_type / observation_window / n_samples / mean / std / skewness / kurtosis / bimodality_coefficient / distribution_shape_label

### 4.2 実装方針 (Code A 判断)

#### 4.2.1 2 ピーク位置の同定: KDE + scipy.signal.find_peaks

```python
from scipy.stats import gaussian_kde
from scipy.signal import find_peaks

# 各 (atom, path, window) で
kde = gaussian_kde(delta_values)
x_grid = np.linspace(min, max, 200)
density = kde(x_grid)
peaks, _ = find_peaks(density)
# 上位 2 ピーク を peak_high, peak_low として記録
```

代替: scipy.stats.gaussian_kde + 2-component GaussianMixture (sklearn) でより堅牢な mixture model。Code A 判断で決定。

#### 4.2.2 cid 構造特性との対応分析

各 bimodal 行で 2 ピークに属する cid を特定し、3 仮説で評価:

```python
for each bimodal row:
    high_cids = cids in upper peak
    low_cids = cids in lower peak
    # 仮説 1: n_core
    score_1 = abs(mean(high_cids.n_core) - mean(low_cids.n_core))
    # 仮説 2: Integration 内外
    score_2 = abs(prop(high_cids in alpha) - prop(low_cids in alpha))
    # 仮説 3: ライフサイクル段階
    score_3 = abs(mean(high_cids.lifespan) - mean(low_cids.lifespan))
    best_hypothesis = argmax([score_1, score_2, score_3])
```

→ 実装可能、各 bimodal 行で軽量計算。

### 4.3 cid 構造特性データソース

- n_core_member: per_subject_audit (固定値)
- Integration 内外: alpha_lifecycle event-by-event 再構築 (v10.6 流用)
- ライフサイクル: pulse_log 最初 t (v10.6 流用)

→ v10.7/v10.8 関数の流用で取得可能。

---

## 5. 「系のリズム同調」(C2 水準) の実装可能性 (項目 5)

### 5.1 Gemini A2 提案

> 対象 cid のライフサイクルや位相に同期させて Atom イベントを発火させる機構

### 5.2 実装の現実性

#### 5.2.1 リアルタイム同調は不可能

post-process なので run 中にリアルタイム同期はできない。Code A 解釈:
- v10.8 出力の bimodal 解析結果から「受信可能状態の cid 構造特性」を事前抽出
- v10.9 で C2 条件として、その特性を満たす cid x timestamp で発火

#### 5.2.2 具体的アルゴリズム (Code A 案)

```python
# Step F bimodal_analyzer の出力 receptivity_criteria を使う
# 例: bimodal 解析で「n_core 高 + age 1000+ が高ピーク (受信可能)」と判明したら
# C2 条件: source_cid が n_core>=5 かつ age>=1000 の cid のみ
# timestamp は cid のライフサイクル中盤 (age 1000-10000) に分散
```

依存関係:
- C2 水準実装には bimodal 解析 (Step F) の結果が先行必要
- 順序: bimodal_analyzer → atom_event_generator (C2 条件) → main run

→ 実装パス確定、依存関係を尊重して順次実行。

### 5.3 リスク

- bimodal 解析結果が「明確な受信可能状態」を示さなければ C2 条件は曖昧になる
- その場合、C1 (均等分散) と差が出ないリスク
- 代替: bimodal の高ピークに対応する cid に必ず発火、低ピーク cid をスキップ

→ Web Claude / Taka 確認願う (§11 Q2)。

---

## 6. 環境チェック結果 (項目 6)

### 6.1 利用可能データ (確認済)

| データ | パス | 状態 |
|---|---|---|
| v10.8 error_distribution (bimodal 1,540 件) | `developmental/v108/outputs/main/error_distribution_seed*.parquet` | ✓ 24 seeds 8,835 rows |
| v10.8 baselines_with_delta (delta 値の元データ) | `developmental/v108/outputs/main/baselines_with_delta_seed*.parquet` | ✓ |
| v10.8 source_events / atom_introduction_events | `developmental/v108/outputs/main/source_events_seed*.parquet` | ✓ |
| v10.8 excess_change | `developmental/v108/outputs/main/excess_change_seed*.parquet` | ✓ Level 3.5 比較用 |
| v10.6 cid_atom_sim_matrix (top_k 30 取得) | `developmental/v106/outputs/main/cid_atom_sim_matrix_seed*.parquet` | ✓ |
| v10.7 流用関数 | 4 モジュール | ✓ |
| v10.8 流用関数 | 4 モジュール (atom_event_generator 等) | ✓ |

### 6.2 PER.sound top_k 確認

- top 30 cid sim 0.414 - top
- top 100 cid sim 0.223 - top
- top 30 と top 100 で約 2 倍の sim 差 → B2 (top 30) は有意義に絞り込み可能

### 6.3 v10.8 storage

- 24 seeds 合計 **736 MB** (実測)
- v10.9 で 3 新条件 → +2.2 GB 推定 → 上限 18%

---

## 7. 設計の甘い部分 (項目 7、Code A 視点で 7 点)

### 7.1 重大ブロッカー (1 点、実装前に判断必須)

**A. 9 条件規模が上限 72% (打切閾値 50% 接近)**
→ Code A 推奨案 c (3 新条件、上限 18%) で進める

### 7.2 設計修正必要 (6 点)

**B. C2 「リズム同調」は bimodal 解析結果に依存**:
- bimodal_analyzer 完了後に atom_event_generator を再実行する順序が必要
- 並列実行で時間短縮の余地は限定的

**C. B3 (random cid) の母集団定義不明確**:
- 案 b1: seed 内 全 cid (= 約 200 cid) から random 100
- 案 b2: 24 seeds 合計 (5,224 cid) から random 100 を seed 別配分
- → Code A 推奨: 案 b1 (seed 内、v10.8 と同 cid プール)

**D. A3 (Q 0/C 0) の post-process 計算的減算との整合性**:
- v10.8 では Q-1/C+1 を実 ledger に書かず計算的減算
- A3 は 0 減算なので「何もしない」と等価、実装は trivial だが意味的に "刺激なし" の event をどう扱うか
- → Code A 推奨: A3 は記録のみで delta 計算スキップ (cost 0)

**E. 出口固定 4 種設計表のフォーマット不明確**:
- 表 1: sensitivity_summary、表 2: receptivity_detection_criteria、表 3: input_routing_criteria、表 4: natural_likeness_design_criteria
- 各表の columns 定義 (指示書 §7) を Code A が具体化して進める

**F. bimodal 解析手法 (KDE vs Mixture Model)**:
- Code A 判断、smoke で両者を比較してから決定

**G. bimodal 1,540 件は seed 0 単独で 67 件のみ**:
- 24 seeds 合計でようやく 1,540 件
- seed 単位の解析では情報不足、cross-seed 集計が主流

### 7.3 v10.7/v10.8 流用の確認

- v10.7 機構: event_aggregator / path_analyzer / baseline_constructor / avalanche_monitor
- v10.8 機構: atom_event_generator / global_activation_correction / subsidiary_observations
- v10.9 で新規実装: bimodal_analyzer / sensitivity_evaluator / design_table_compiler

→ 大半流用、新規実装は 3 モジュール + orchestrator。

---

## 8. 実装予想時間 (項目 8)

| ステップ | 予想時間 |
|---|---|
| 認識確認 (本文書) | **完了** (約 1 時間) |
| 環境チェック詳細 (`v109_environment_check_report.md`) | 30 分 |
| `v109_atom_event_generator.py` (3 新条件) | 1.5 時間 |
| `v109_baseline_recalculator.py` (3 条件 × baseline 再計算) | 1 時間 |
| `v109_bimodal_analyzer.py` (KDE + 仮説評価) | 1.5 時間 |
| `v109_sensitivity_evaluator.py` (3 候補感度) | 1 時間 |
| `v109_design_table_compiler.py` (4 種設計表) | 1 時間 |
| `v109_post_process.py` (orchestrator、v10.7/v10.8 流用) | 1 時間 |
| smoke test (seed 0、3 条件) | 30 分 |
| 修正イテレーション | 1 時間 |
| main run (24 並列、3 条件) | 15-20 分 |
| 7 種 reports + 出口固定 4 種設計表 | 3 時間 |

**合計**: 13-14 時間 (1.5-2 日)

v10.7/v10.8 流用で新規実装最小限。

---

## 9. ストレージ予算 (項目 9)

### 9.1 案 c (Code A 推奨、3 新条件)

| 区分 | 値 |
|---|---:|
| 3 新条件 atom_introduction_events 関連 (× v10.8 と同等 736 MB) | 約 2.2 GB |
| bimodal 解析結果 | 数 MB |
| 寄与候補感度評価 + 設計表 | 数 MB |
| **合計** | **約 2.2 GB** |

### 9.2 上限比

- 上限 6 GB
- v10.9 推定 2.2 GB = **上限 37%**
- v10.7 + v10.8 + v10.9 累計: 0.4 + 0.7 + 2.2 = 3.3 GB (累計でも上限内)

### 9.3 案 a (全 9 条件) の場合

- 4.4 GB = 上限 72% (打切閾値 50% 超過)
- 修正案 (parquet gzip 圧縮) で約 3.5 GB に圧縮可能だが、それでも余裕少ない

→ 案 c 採用が安全。

---

## 10. 質問・確認事項 (項目 10)

### 10.1 即決を要する判断 (実装着手前に確定)

1. **規模調整**: Code A 推奨 **案 c (3 新条件)** で進めて良いか、それとも案 a (全 6 新条件) を強行するか

2. **C2「リズム同調」のフォールバック**: bimodal 解析が明確な受信可能状態を示さない場合、C2 を C1 と同等扱いにするか別ロジック (例: 高 sim cid のみ) を採用するか

3. **B3 (random cid) の母集団**: seed 内 (約 200 cid から random 100) で進めて良いか

4. **A3 (Q 0/C 0) の意味**: コストなし event を「刺激なし」(delta 計算スキップ) として扱って良いか、それとも何らかの最小刺激として扱うか

5. **bimodal 解析手法**: KDE vs Mixture Model、Code A 判断で進める許可

6. **出口固定 4 種設計表のフォーマット**: 指示書 §7 を Code A が具体化して進める許可

### 10.2 実装中の判断 (smoke 後に確認)

7. bimodal 解析の最低サンプル閾値 (n_samples >= 10? 30?)
8. 仮説評価のスコア計算法 (effect size? p-value?)
9. 「best_hypothesis」が「該当なし」になる場合の扱い

### 10.3 v10.9 範囲確認

10. Atom 常駐留保ドキュメントは v10.10 主題決定で再議論、v10.9 では扱わない (即決済、確認のみ)

---

## 11. Web Claude / Taka への即決事項 6 項目 (整理版)

| # | 質問 | Code A 推奨 |
|---|---|---|
| 1 | 規模調整 (案 a 全 6 vs 案 c 3 新条件) | **案 c 採用** (storage 上限 18%) |
| 2 | C2 「リズム同調」フォールバック | bimodal 結果次第、smoke で動作確認後判断 |
| 3 | B3 random cid 母集団 | **seed 内 全 cid から random 100** (案 b1) |
| 4 | A3 (Q 0/C 0) の扱い | **delta 計算スキップ** (コスト 0 = 刺激なし) |
| 5 | bimodal 解析手法 | **KDE 第一試行、Mixture Model フォールバック** |
| 6 | 4 種設計表フォーマット | **Code A 具体化で進める** |

---

## 12. Code A 推奨の進行手順 (修正版)

```
Step A: 本文書を Web Claude / Taka が確認、§11 即決 6 項目を確定
Step B: Code A が修正された設計で実装着手
Step C: 環境チェック詳細 (`v109_environment_check_report.md`)
Step D: v109_atom_event_generator (3 新条件: A2, B3, C2)
   - C2 は bimodal 解析結果に依存、Step F 後に実行
Step E: v109_bimodal_analyzer (KDE + 3 仮説評価)
Step F: C2 条件を bimodal 結果から定義 + atom_event_generator 完了
Step G: v109_baseline_recalculator (3 条件で baseline 再計算)
Step H: v109_sensitivity_evaluator (3 候補感度)
Step I: 統合 smoke (seed 0、bit-identity 検証、storage 実測)
Step J: 24 seeds 並列 main run (3 新条件、推定 16 分)
Step K: cross-seed 解析 + Level 1-3.5 reports + 出口固定 4 種設計表 + 総括
```

各 Step で完了報告し、Web Claude / Taka 確認を取る。

---

## 13. 完了条件チェック (本文書の)

- [x] §0.1 の 10 項目を網羅
- [x] 主題の理解 (3-5 行)
- [x] 9 条件の実装可能性判定 + 規模調整提案
- [x] 各変動条件で baseline 再計算の実装方法
- [x] bimodal 構造解析の実装方法
- [x] C2「リズム同調」の実装可能性
- [x] 環境チェック (利用可能データ)
- [x] 設計の甘い部分 (7 点)
- [x] 実装予想時間 (13-14 時間)
- [x] ストレージ予算 (案 c で 2.2 GB、上限 37%)
- [x] 質問事項 (10 項目、即決 6)

---

*以上、Code A による v10.9 実装着手前認識確認文書。Web Claude / Taka の §11 即決 6 項目を待って実装着手します。*
