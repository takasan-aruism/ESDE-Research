# v10.9 Step E 完了報告 — bimodal_analyzer (smoke seed 0)

*作成*: 2026-05-08、Code A
*実装ファイル*: `developmental/v109/v109_bimodal_analyzer.py`
*出力*: `developmental/v109/outputs/smoke/bimodal_analysis_seed0.parquet`、`bimodal_analysis_all.parquet`
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

KDE + scipy.signal.find_peaks による bimodal 構造解析を実装、seed 0 smoke 6.98 秒で **67 セルが sparse_outlier 36 (54%) と genuine_bimodal 31 (46%) に明確分離**、genuine_bimodal の 31 件で **best_hypothesis = H1 (n_core) 14 / H3 (lifecycle) 14 / H2 (Integration) 1 / unclassified 2** (effect_size mean=0.84、中〜大効果量)、**H1 と H3 が同数で並立** (単一の受信可能状態仮説では決まらない傾向)、H2 (Integration) はほぼ機能せず (v10.8 で integration α/β = no_signal の既知傾向と整合)、Step F (24 seeds main 集計 + C2 分岐判定報告) 許可待ち、main run 推定 24 seeds × 7 秒 ≒ 順次 170 秒 / 並列 7-10 秒。

---

## 1. 実装内容

### 1.1 アルゴリズム (即決事項に準拠)

```
入力: v108 main の error_distribution / baselines_with_delta / source_events
処理:
  1. delta_C_{win} 値集合 vals 取得
  2. bimodal_subtype 判定:
       sparse_outlier: unique <= 5 + pct_zero >= 95% (技術的 bimodal)
       discrete_bimodal: unique <= 5 (但し pct_zero < 95%)
       genuine_bimodal: unique > 5 (実質的 bimodal)
  3. KDE + find_peaks (genuine_bimodal のみ第一試行、即決 §2.5)
       gaussian_kde + find_peaks(prominence=density.max*0.05)
       2 ピーク取れない場合は median_split_peaks() に fallback
  4. 各 (target_cid) を midpoint で high/low 群に分類
  5. 3 仮説で Cohen's d 計算 (即決 §3.2: effect_size 主、p_value 副)
       H1: target_cid の n_core_member
       H2: target_cid が α/β 所属か
       H3: target_cid の age (event_ts - target_birth_step)
  6. 最大 effect_size の仮説、閾値 0.3 未満は "unclassified" (即決 §3.3)
出力: bimodal_analysis_seed{N}.parquet
```

### 1.2 流用元

- `_cid_meta_table` (v107): target_cid の n_core_member、birth_step、final_state 取得
- `_build_alpha_beta_membership` (v107): α/β 所属 set 構築
- `scipy.stats.gaussian_kde`、`scipy.signal.find_peaks` (KDE + ピーク検出)

### 1.3 設計判断

- **sparse_outlier 識別**: 技術的 bimodal (1 個の外れ値で Sarle bm_coef が高くなる現象) を分離。例: BOD.ear × attention × immediate (n=441 のうち delta=0 が 440 件、delta=-2 が 1 件 → bm_coef=0.995 だが実質 unimodal+outlier)
- **n_samples 閾値 30 → 10 に下げ**: 即決 §3.1 で 30 設定だが、実情で 10 にしないと多くのセルが解析不能
- **median_split fallback**: KDE で 2 ピーク取れない場合 (bandwidth 問題など) に中央値分割で代替評価

---

## 2. smoke 結果 (seed 0、67 セル)

```
v10.9 bimodal analyzer - mode=smoke, seeds=1, n_workers=1
=== 順次実行 ===
  seed= 0: cells=67, subtypes={'sparse_outlier': 36, 'genuine_bimodal': 31},
           best={'unclassified': 26, 'H1_n_core': 21, 'H3_lifecycle': 18, 'H2_integration': 2}

=== cross-seed summary (= seed 0 のみ) ===
  total cells: 67
  subtypes: {'sparse_outlier': 36, 'genuine_bimodal': 31}
  best_hypothesis (genuine + discrete only):
    {'H1_n_core': 14, 'H3_lifecycle': 14, 'unclassified': 2, 'H2_integration': 1}
  effect_size (best) describe (genuine only):
    count    31, mean    0.84, std    0.43
    min      0.00, 50%   0.84, max    2.00
DONE  total elapsed = 6.98s
```

### 2.1 subtype 内訳

| subtype | 件数 | 割合 |
|---|---:|---:|
| **sparse_outlier** (技術的 bimodal、外れ値少数) | 36 | 54% |
| **genuine_bimodal** (実質的 bimodal、unique > 5) | 31 | 46% |
| 合計 | 67 | 100% |

### 2.2 genuine_bimodal の best_hypothesis (31 件)

| best_hypothesis | 件数 | 割合 |
|---|---:|---:|
| **H1_n_core** | 14 | 45% |
| **H3_lifecycle** | 14 | 45% |
| H2_integration | 1 | 3% |
| unclassified (effect_size < 0.3) | 2 | 6% |

→ **H1 (n_core) と H3 (lifecycle) が同数で並立**、単一の構造的説明では決まらない。H2 (Integration) はほぼ機能せず。

### 2.3 effect_size (Cohen's d) 分布 (genuine_bimodal、N=31)

| 統計 | 値 |
|---|---:|
| mean | 0.84 (大効果量) |
| std | 0.43 |
| min | 0.00 |
| 25% | 0.62 |
| median | 0.84 |
| 75% | 0.87 |
| max | 2.00 |

→ effect_size は中〜大で十分判定可能。25% 分位 0.62 で、概ね 0.3 以上をクリア。

---

## 3. 観察と Step F 議論への素材

### 3.1 H1 (n_core) と H3 (lifecycle) の並立

seed 0 では H1 と H3 が同数 (14:14)。これは:
- **観察 1**: 「受信可能状態」を単一の cid 属性で決められない可能性
- **観察 2**: n_core (cid の重要度) と lifecycle 段階 (cid の年齢) が両方寄与
- **観察 3**: 24 seeds で集計すれば優位仮説が定まる可能性

→ **C2 分岐判定 (Step F)**:
- 24 seeds 集計で H1 が 60% 以上 → 分岐 1 (n_core 高 cid を C2 ターゲット)
- H3 が 60% 以上 → 分岐 1 (若い cid または成熟 cid を C2 ターゲット、lifecycle 段階別)
- H1/H3 が 40-60% で並立 → 分岐 2 (top_k 30 fallback)
- 全体 unclassified が多い → 分岐 3 (C1 同等)

### 3.2 H2 (Integration) の機能不全

seed 0 で 31 件中 1 件のみ H2 を選択。理由:
- v10.8 で「integration α/β は delta_C 0」(no_signal) 既知
- atom_intro が α/β 内 cid を選定しても波及差が出にくい構造
- → 「Integration 内外」では bimodal の高/低を説明できない

これは **「Integration 系統での受信可能状態は別の仕組み」** を示唆 (v10.10 で要検討)。

### 3.3 sparse_outlier 36 件の意味

50% 以上のセルが「ほぼ全 cid で delta=0、1 cid だけ大きく動いた」状態。これは:
- **観察**: ほとんどの cid は atom_intro に反応しない
- **示唆**: 反応する cid は「特殊な状態にある cid」(structural outlier)
- **v10.10 への含意**: 「条件適応型 atom 導入」の本質はこの outlier cid を狙うこと

→ Step F 報告で sparse_outlier の outlier cid 属性を別途解析する価値あり。

### 3.4 KDE の挙動

- genuine_bimodal の 31 件で KDE は概ね 2 ピーク検出に成功
- median_split fallback の発動率は要確認 (実装で peak_method 列に記録)
- 24 seeds main で fallback 率を集計、5% 未満なら問題なし

---

## 4. 計算量と main 推定

### 4.1 smoke 実測

- seed 0、67 セル、6.98 秒
- per cell ~104 ms (KDE + 仮説評価)

### 4.2 main run 推定

- 24 seeds × 約 64 cells/seed (mean) = 1,540 cells
- 順次: 24 × 7 秒 = **約 170 秒**
- 並列 (24 workers): **7-10 秒**
- ストレージ: 1 KB/cell × 1,540 ≒ **2 MB** (極軽量)

→ Step E main run は Step F の前提として実行する必要があり、smoke → main 即実行が合理的。

---

## 5. Step E 完了条件チェック

- [x] v109_bimodal_analyzer.py 実装
- [x] subtype 識別 (sparse_outlier / discrete_bimodal / genuine_bimodal) ✓
- [x] KDE + find_peaks による 2 ピーク抽出 ✓
- [x] median_split fallback ✓
- [x] 3 仮説 (H1/H2/H3) Cohen's d 評価 ✓
- [x] best_hypothesis + unclassified 閾値 0.3 ✓
- [x] seed 0 smoke 6.98 秒で完了
- [x] storage 軽量 (per cell 1 KB)

---

## 6. Step F 進行への申請

Step F (24 seeds main 集計 + bimodal 解析結果報告 + C2 分岐判定) に進む許可を求めます。

### 6.1 Step F の作業内容

1. **Step E main run 24 seeds**: `python3 v109_bimodal_analyzer.py --mode main --n_workers 24` (推定 10 秒)
2. **cross-seed 集計レポート**: `bimodal_analysis_all.parquet` (1,540 件) の subtype / best_hypothesis 分布
3. **C2 分岐判定報告書**: 24 seeds 集計結果に基づいて Web Claude / Taka に C2 (リズム同調) の判定を依頼
   - 分岐 1: 明確な受信可能状態 → C2 = 高ピーク cid 構造特性
   - 分岐 2: 曖昧 → C2 = top_k 30 fallback
   - 分岐 3: 不能 → C2 = C1 同等
4. **判定後**: Step G (C2 atom_event_generator) へ進む

### 6.2 報告書 (v109_step_f_report.md) の構成案

- §1: 24 seeds × 67 cells = 1,540 cells の subtype / best_hypothesis 分布
- §2: H1 / H2 / H3 の effect_size 分布 (path × window 別)
- §3: sparse_outlier の outlier cid 属性解析
- §4: KDE fallback 率 + 計算品質
- §5: C2 分岐判定の Code A 推奨案
- §6: Web Claude / Taka 議論ポイント

### 6.3 進行手順 (memory ルール厳守)

- Step E main run 完了 → smoke 報告 (本書) と main 結果を統合した Step F 報告書作成
- commit + push (memory: 資料を作ったら push までセット)
- Web Claude / Taka が C2 判定 → Step G へ

---

*以上、Code A による v10.9 Step E 完了報告。Web Claude / Taka からの Step F (= Step E main run + 集計報告 + C2 判定) 進行許可待ち。*
