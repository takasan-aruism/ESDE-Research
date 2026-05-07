# v10.8 Step F 報告 — 副次観察 3 件 + smoke

*作成*: 2026-05-07、Code A
*親*: `v108_step_e_report.md` (Step E 完了)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

`v108_subsidiary_observations.py` で 3 副次観察 (Whiteout / Small-World / 誤差分布) を seed 0 で **0.77 秒** で smoke、**Small-World 完全維持** (v107/v108 共に loop_2=711, loop_3=4,563、ratio 1.0)、**誤差分布 18% bimodal** (375 rows 中 67 件)、**Whiteout は 300 ペア全部 flag (max_corr=1.000)** という異常パターン (medium window n_pulses への全 atom 同方向集約による)、解釈は Step J で詳細検討要、Step G (smoke 統合判定 + bit-identity 層 A 再確認) 進行準備完了。

---

## 1. smoke 結果 (seed 0、0.77 秒)

| 副次観察 | 出力 rows | 主要結果 |
|---|---:|---|
| **Whiteout** (correlation 25 atom × 25 atom) | 300 ペア | 300/300 flag、max_corr **1.000** ← 異常 |
| **Small-World** (v10.7 vs v10.8) | 1 row/seed | l2 711=711、l3 4,563=4,563、**完全維持** ✓ |
| **誤差分布** (25 atom × 5 path × 3 win) | 375 rows | other 205 / skewed 95 / **bimodal 67 (17.9%)** / heavy_tail 8 |

---

## 2. Whiteout 監視 (要解釈)

### 2.1 結果

300 ペア中 **300 ペア (100%) が whiteout_flag = True** (correlation_coefficient ≥ 0.7)。

→ 全 atom ペアで delta vector が **完全相関 (1.000)**。

### 2.2 原因解析

集計方法:
- 各 atom の medium window 6 delta 量 (R_familiarity / Q / C / n_alphas / n_observed / n_pulses) を mean
- 25 atom × 6 dim プロファイルベクトル
- 25 × 25 atom 相関係数

→ **medium window n_pulses_in_window が全 atom で支配的** (Level 1 finding: 24/24 direction 一貫、+10〜15 events) のため、6 dim ベクトルが事実上 n_pulses 1 軸に支配される → atom 間で完全相関。

これは **Whiteout (干渉) ではなく Level 1 一貫性の表れ**。 Whiteout 元仮説 (同時刻多重発火による波及干渉) は 87 step (3.5%) のみで発生 (Step C で確認済) のため、本質的に存在しない。

### 2.3 Step J で詳細検討

修正案 (Step J で実装):
- profile vector を **(path × delta_field) = 5 path × 6 量 = 30 dim** に拡張
- path 別の atom 独立性を測定
- 相関閾値の再検討

本 Step F の smoke 結果は **「medium window で全 atom が同方向 (= ESDE 共通効果)」** という Level 1 整合の観察として記録、 Step J で path 別に再分析。

---

## 3. Small-World 維持 (確認 PASS)

### 3.1 結果

| 量 | v10.7 | v10.8 | ratio |
|---|---:|---:|---:|
| loop_2_hop (双方向 fam) | 711 | 711 | 1.000 |
| loop_3_hop (三角閉路) | 4,563 | 4,563 | 1.000 |

→ **完全に同一値、Small-World 構造は post-process では構造的に変更不可能** (familiarity edge は v10.5 出力 = read-only)。

### 3.2 Gemini A6 懸念の v10.8 での無効性

Code A 認識確認文書 §7.2 で指摘した通り:
- v10.8 は post-process、familiarity edge を変更しない
- → loop は構造的に維持される
- → Gemini A6 の「Small-World 崩壊リスク」懸念は v10.8 では **構造的に発生しない**

これは Phase 2 (物理層を変更する段階) で再評価する観察項目。v10.8 では記録のみで主題判定外。

---

## 4. 誤差分布の形状観察

### 4.1 形状ラベル分布 (seed 0、375 rows = 25 atom × 5 path × 3 window)

| shape_label | count | ratio |
|---|---:|---:|
| other (skewness 0.5-1.0、または条件外) | 205 | 54.7% |
| skewed (\|skewness\| > 1.0) | 95 | 25.3% |
| **bimodal (Sarle's > 5/9)** | **67** | **17.9%** |
| heavy_tail (kurtosis > 3) | 8 | 2.1% |
| normal (\|skew\|<0.5、\|kurt\|<1.0) | 0 | 0% |

→ **正規分布の atom × path × window はゼロ**。最頻 shape は other (= 中度に skewed)、続いて strongly skewed、bimodal が 18%、heavy_tail が 2%。

### 4.2 Bimodal 67 件の意味 (Taka 示唆「確率的発生と誤差表現能力の融合可能性」)

Bimodal 分布 = 2 つのピーク = 2 種類の異なる効果が混在している分布。

考えられる原因:
- target cid の n_core 別 (n=2 vs n=5) で異なる反応
- atom_introduction_event の前後で cid 状態が二相状態
- relation_path 上での近接 cid と遠方 cid の二極

→ Step J で bimodal な (atom, path, window) の具体例を抽出して詳細解析の素材として記録。

---

## 5. Step F 完了条件チェック

- [x] Whiteout 監視 (300 ペア、相関係数、flag) — 結果は要解釈 (Step J)
- [x] Small-World 維持確認 (v107/v108 同一、構造的不変) — PASS
- [x] 誤差分布形状観察 (375 rows、Sarle's bimodality) — 18% bimodal 検出
- [x] read-only / v108 出力 path 縛り維持
- [x] 24 seeds 単一バッチ実行可能性 (0.77 × 24 = 19 秒、超軽量)
- [x] 副次観察は **記録のみ、主題判定外** (即決事項 §3.3 確定)

---

## 6. 出力ファイル

```
developmental/v108/
├── v108_subsidiary_observations.py
├── v108_step_f_report.md
└── outputs/smoke/
    ├── whiteout_monitor_seed0.parquet           (300 rows、25 × 25 atom 相関)
    ├── smallworld_comparison_seed0.parquet      (1 row、v107/v108 比較)
    ├── error_distribution_seed0.parquet         (375 rows、25 × 5 × 3 形状)
    └── step_f_run_summary.parquet
```

---

## 7. Step G 進行への申請

Step G (統合 smoke + bit-identity 層 A/C 検証) に進む許可を求めます。

実装方針:
1. **層 A 検証**: seed 0 を 2 回実行して全機構出力の md5 比較 (summary 系除く)
2. **層 C 検証**: 全出力が v108/ 配下のみで v105/v106/v107 配下に書き込みなし
3. **層 B 検証**: smoke 前後の v10.7 出力不変性 (Step D で既に PASS)
4. **storage 統合確認**: smoke 全機構合計 (Step C-F の 13+ ファイル) の size 実測
5. smoke 結果サマリの作成 → Step I main run 進める判定

実行時間予想: 30 分 (smoke 2 回実行 + md5 比較 + storage 集計)。

Step G 完了後、Step I (24 seeds 並列 main run) に進みます:
- v10.7 で実証済 multiprocessing 24 workers
- 推定 3-5 分
- bit-identity 層 B 検証

24 seeds 単一バッチ厳守 (3 バッチ分割禁止)。

---

*以上、Step F 報告。Web Claude / Taka からの Step G 進行許可待ち。*
