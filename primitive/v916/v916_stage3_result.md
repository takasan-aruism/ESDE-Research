# v9.16 Stage 3 — Observation-Sampling Self-Readout Result

*作成: 2026-04-21、Code A*
*Describe only、結論を書かない*
*Phase 2 output、24 seeds × tracking 50 windows × 500 steps*

---

## 1. 実装サマリ

### 1.1 実行条件

| 項目 | 値 |
|---|---|
| コマンド | `seq 0 23 \| parallel -j24 "python v916_memory_readout.py --seed {} --maturation-windows 20 --tracking-windows 50 --window-steps 500 --tag main"` |
| OMP/MKL/OpenBLAS threads | 1 |
| PYTHONHASHSEED | 0 |
| 実行日時 | 2026-04-21 16:47–19:54 JST |
| 実時間 (wall) | **187m4.5s (3h7m)** |
| user 時間合計 | 4333m52.4s ≈ 24 seeds × 180min |
| Parallel 効率 | ほぼ 100% (48 cores の半分使用) |
| 全 24 seeds exit code | 0 (エラー・例外なし) |

指示書 §10.3 想定「段階 2 と同等 3h 前後」に準拠。

### 1.2 Bit-identity Check (v9.14 long 6 本)

比較対象: `primitive/v914/diag_v914_long/` の seed0 CSV 6 本と
`primitive/v916/diag_v916_main/` の seed0 CSV 6 本。

| ファイル | MD5 判定 |
|---|---|
| `aggregates/per_window_seed0.csv` | **OK** |
| `pulse/pulse_log_seed0.csv` | **OK** |
| `labels/per_label_seed0.csv` | **OK** |
| `audit/per_event_audit_seed0.csv` | **OK** |
| `audit/per_subject_audit_seed0.csv` | **OK** |
| `audit/run_level_audit_summary_seed0.csv` | **OK** |

Layer A / Layer B が frozen であることを示す (段階 3 の改変は Layer C のみ)。

### 1.3 段階 2 からの変更点

| 項目 | 段階 2 (v9.15s2) | 段階 3 (v9.16) |
|---|---|---|
| サンプリング | 全ノード観察 | `age_factor = Q_remaining / Q0` に比例した数のみ観察 |
| node 状態 | match / mismatch (2 値) | match / mismatch / **missing** (3 値) |
| any_mismatch 判定 | ノード or リンクの mismatch | **観察ノードの mismatch のみ** (リンク不寄与) |
| 乱数源 | `engine.rng` 非参照 | `engine.rng` 非参照 + hash ベース独自 RNG |
| divergence_log | `theta_diff_norm` (全ノード) | `theta_diff_norm_all` (全) + `theta_diff_norm_observed` (観察のみ) |
| 新規出力 | — | `observation_log_seed{N}.csv` (event × cid 単位) |

### 1.4 Fetch 総数 (段階 2 との整合)

| 項目 | v9.16 (main) | v9.15 段階 2 (main) |
|---|---|---|
| Σ fetch_count (24 seeds 合算) | **120,782** | **120,782** |
| observation_log 総行数 | 120,782 | — |
| 一致 | **True** (seed 別でも全 24 seed 一致) | |

event 駆動の継承が seed 単位で維持されている。Fetch 総数が段階 2 と bit-level で一致する。

---

## 2. Basic Statistics (24 seeds 合算)

### 2.1 age_factor 分布

全 120,782 event 行の age_factor 分布:

| 統計 | 値 |
|---|---|
| min | 0.0000 |
| q25 | 0.0000 |
| median | **0.0000** |
| mean | 0.2770 |
| q75 | 0.5555 |
| max | 0.9818 |

半数以上の event は `age_factor = 0.0` で発火している (Q 枯渇後の event も Layer B 側でカウントされ続けるため)。

### 2.2 観察と欠損の分布

node-cell レベル (= Σ fetch_count × n_core):

| 状態 | cell 数 | 比率 |
|---|---|---|
| match | 0 | **0.00 %** |
| mismatch | 107,783 | 23.22 % |
| missing | 356,436 | **76.78 %** |
| 合計 | 464,219 | — |

観察されたノードはすべて `NODE_MATCH_TOLERANCE = 1e-6` を超えて drift していた (match=0.0% は smoke と同傾向)。missing が 3/4 を占める。

### 2.3 age_factor 区間別の 3 値比率

| age_factor 区間 | event 行数 | match | mismatch | missing |
|---|---|---|---|---|
| [0.0, 0.2) | 68,057 | 0.00 % | 0.73 % | **99.27 %** |
| [0.2, 0.4) | 10,136 | 0.00 % | 32.20 % | 67.80 % |
| [0.4, 0.6) | 14,108 | 0.00 % | 49.83 % | 50.17 % |
| [0.6, 0.8) | 14,347 | 0.00 % | 67.44 % | 32.56 % |
| [0.8, 1.0) | 14,134 | 0.00 % | **93.63 %** | 6.37 % |

age_factor が減ると missing 比率が単調に上がる。これは指示書 §5 pseudocode の
`n_observed = round(n_core × age_factor)` 実装が意図通り機能した結果である (構造的に必ずこの関係になる設計)。

---

## 3. age_factor と判定結果の関係

### 3.1 n_core 別 age_factor 分布

| n_core | event 行数 | min | median | mean | max |
|---|---|---|---|---|---|
| 2 | 35,348 | 0.0000 | **0.5455** | 0.4945 | 0.9286 |
| 3 | 6,846 | 0.0000 | 0.1111 | 0.3034 | 0.9500 |
| 4 | 19,694 | 0.0000 | 0.0000 | 0.1891 | 0.9655 |
| 5 | 58,519 | 0.0000 | 0.0000 | 0.1727 | 0.9730 |
| 6 | 48 | 0.0000 | 0.3875 | 0.4062 | 0.9750 |
| 7 | 172 | 0.0000 | 0.0000 | 0.1395 | 0.9796 |
| 8 | 155 | 0.0000 | 0.0000 | 0.1742 | 0.9818 |

`n_core = 2` は median=0.55 で他サイズより高い。`n_core ≥ 4` は median=0.0。

### 3.2 event 種別別 age_factor 分布

| event | 行数 | median | mean |
|---|---|---|---|
| E1 | 8,122 | 0.5833 | 0.5874 |
| E2 | 12,228 | **0.7273** | 0.7115 |
| E3 | 100,432 | **0.0000** | 0.1990 |

E3_contact は median=0.0 (発火時点で Q 枯渇が進んでいる cid が多数)。E2 は median=0.73 で最も高い。

### 3.3 event 種別別 3 値分布

| event | total cells | match | mismatch | missing |
|---|---|---|---|---|
| E1 | 27,136 | 0.00 % | 58.20 % | 41.80 % |
| E2 | 39,392 | 0.00 % | **73.62 %** | 26.38 % |
| E3 | 398,809 | 0.00 % | 15.86 % | **84.14 %** |

E3_contact は missing が 84% (age_factor 分布と一致)。E2 は mismatch が最多 (73.62%)、E3 は最小 (15.86%)。

### 3.4 Q 枯渇 cid の観察

| 集計 | 値 |
|---|---|
| registry 総 cid | 5,759 |
| fetched cid (fetch_count ≥ 1) | **5,170** |
| `any_mismatch_ever = True` の cid | 5,170 (fetched の 100 %) |
| `total_missing_count > 0` の cid | 4,952 (fetched の **95.78 %**) |
| 全 fetch で `total_observed_count = 0` の cid | 0 |
| `age_factor_final = 0.0` の cid | **1,771 (fetched の 34.26 %)** |

fetched cid のうち:
- 95.78 % が少なくとも 1 event 分の missing を経験
- 34.26 % が Q を完全枯渇 (age_factor = 0 到達)
- `any_mismatch_ever = False` の cid は 0 (指示書 §13.3 に抵触しない)

### 3.5 Q0 分布 (ハイライト)

| Q0 | cid 数 |
|---|---|
| 10 | 135 |
| 11 | 2,575 |
| 12 | 2,714 |
| 13 | 51 |
| 18 | 239 |
| 19 | 115 |
| 25 | 144 |
| 26 | 173 |
| 33 | 303 |
| ... | |
| 55 | 1 |

Q0=11 / Q0=12 に大きな山 (合計 5,289 cid、全 cid の 92%)。これは B_Gen の分布で
`n_core = 2` の cid が支配的に多いことを反映している (n_core 小 → B_Gen 大 → Q0 大)。
ただし fetched cid 5,170 中、Q0 ≥ 25 の大型 cid も 1,119 存在する。

---

## 4. 段階 2 との比較

### 4.1 theta_diff_norm_all の比較 (seed0 全 cid 全 event)

| 項目 | 値 |
|---|---|
| v9.16 `divergence_log_seed0.csv` 行数 | 4,318 |
| v9.15s2 `divergence_log_seed0.csv` 行数 | 4,318 |
| 共通 key (cid × step × event) | 4,318 |
| **max |v916.theta_diff_norm_all − v915s2.theta_diff_norm|** | **0.000000** |
| mean |差分| | 0.000000 |

v9.16 の `theta_diff_norm_all` は v9.15s2 の `theta_diff_norm` と **完全一致** (全 4,318 件で 0 差)。
これは物理層・event 駆動・全ノード L2 の計算ロジックが不変であることの傍証。

### 4.2 theta_diff_norm_observed の新規分布 (n_observed > 0 の event のみ)

| 項目 | theta_diff_norm_observed | 正規化 (observed/n_observed) |
|---|---|---|
| n | 54,054 | 54,054 |
| min | 0.0001 | 0.0001 |
| q25 | — | — |
| median | 1.9239 | 1.1473 |
| mean | 2.4008 | 1.4001 |
| q75 | — | — |
| max | 10.7518 | 6.2577 |

n_observed = 0 の event (Q 枯渇後など) 66,728 行は 0.0 として除外済。
observed の 54,054 行での分布。segment ノードが多くなるほど絶対値が大きくなるため、正規化版 (ノード 1 点あたりの drift) も併記。

### 4.3 Fetch 総数の確認 (seed 別)

24 seeds で v9.16 と v9.15s2 の `Σ fetch_count`:

| seed | v9.16 | v9.15s2 | 一致 |
|---|---|---|---|
| 0 | 4,318 | 4,318 | ✓ |
| 1 | 4,821 | 4,821 | ✓ |
| ... | ... | ... | ✓ |
| 12 | 6,178 | 6,178 | ✓ |
| ... | ... | ... | ✓ |
| 23 | 4,856 | 4,856 | ✓ |
| 合計 | **120,782** | **120,782** | **全 24 seed 一致** |

event 駆動の継承が seed 単位まで確認できる。

---

## 5. Seed 別分散分析

各 seed の `avg_age_factor` 平均値 (fetched cid 平均):

| 集計 | 値 |
|---|---|
| seed 別 avg_age_factor 平均 の min | 0.5096 |
| seed 別 avg_age_factor 平均 の max | 0.5590 |
| seed 別 CV | **0.0296** (= 2.96%) |

各 seed の `final_missing_fraction` 平均値 (fetched cid 平均):

| 集計 | 値 |
|---|---|
| seed 別 final_missing_fraction 平均 の min | 0.4220 |
| seed 別 final_missing_fraction 平均 の max | 0.4756 |
| seed 別 CV | **0.0372** (= 3.72%) |

24 seeds 間の統計的ばらつきは CV 3–4% に収まる (seed 固有性よりも統計的集中が強い)。

---

## 6. 観察事項 (Describe, do not decide)

以下は 24 seeds × 50 tracking windows × 500 steps の run で **計測された事実** の列挙のみ。
指示書 §11.3 に基づき「自己」「意識」「老成」「成熟」「経験的安定」等の語を避ける。

- **Fetch 総数 120,782 が段階 2 と完全一致**。段階 3 の改変によって event 駆動の発火頻度そのものは変化していない。
- **`theta_diff_norm_all` が v9.15s2 の `theta_diff_norm` と max 差 0.0**。物理層の drift 計算は改変されていない。
- **node-cell レベルで match = 0.00 %**。smoke の 5,000 step でも main の 35,000 step でも、観察された node は NODE_MATCH_TOLERANCE=1e-6 を超えて生誕時 theta から乖離している。
- **missing 比率 76.78 %、mismatch 23.22 %、match 0 %** (node-cell level)。観察粒度が Q 消耗に応じて粗くなる設計が大規模に効いている。
- **age_factor 区間別の missing 比率が単調**: [0,0.2) で 99.27 %、[0.8,1.0) で 6.37 %。これは `n_observed = round(n_core × age_factor)` から代数的に導かれる関係。
- **event 種別別の age_factor 差**: E2=0.73 (median)、E1=0.58、E3=0.00。E3 発火時は大半の cid が Q を既に消費している。
- **fetched cid の 34.26 % が `age_factor_final = 0.0`** (run 終了時点で Q を完全消費)。smoke では 0 件だったが、tracking 50 windows で顕著に出現。
- **全 fetched cid (5,170) で `any_mismatch_ever = True`**。指示書 §13.3 の「1% より大きい場合報告」には抵触しない。
- **Q0 分布のピーク**: Q0=11, 12 (合計 5,289 cid、92 %)。これは B_Gen の分布で `n_core=2` が支配的な構造に由来。
- **seed 間変動 CV 3–4 %**。統計的集中が強く、24 seeds 合算値は個別 seed と実質同じ傾向を示す。
- **`n_core = 2` cid の age_factor median が他サイズの 5 倍**: n_core=2 は median=0.5455、n_core≥4 は median=0.0。これは n_core 小 → member link 数が少ない (C(n,2)=1) → E1/E2 発火頻度が低い → Q 消費遅い、という論理で説明可能。

---

## 7. 指示書 §8.3 承認条件 12 項目 (main run 対応版)

本番 run は smoke の 5 倍規模だが、以下はすべて再確認可能:

| # | 条件 | 結果 |
|---|---|---|
| 1 | v9.14 baseline 6 本 MD5 一致 (vs v9.14 long) | **PASS** |
| 2 | per_subject v9.14 96 列 bit-identical | (seed0 smoke で確認済) |
| 3 | v915_* 20 列の存在 | (smoke と同実装) |
| 4 | age_factor ∈ [0, 1] | **PASS** (全 120,782 行) |
| 5 | 0 ≤ n_observed ≤ n_core | **PASS** |
| 6 | n_observed == round(n_core × age_factor) | **PASS** |
| 7 | total_missing が observation_log と整合 | **PASS** (5,759 cid) |
| 8 | match_obs + mismatch_obs == observed | **PASS** |
| 9 | 決定論 (smoke 2 回 run) | PASS (smoke で確認済) |
| 10 | 実行時間 | 3h7m (段階 2 とほぼ同等) |
| 11 | エラー/例外ゼロ | **PASS** (全 24 seeds) |
| 12 | observation_log サイズ | 120,782 rows × 24 files、各 160 KB 前後、総計 ~8 MB |

---

## 8. 生成ファイル

```
primitive/v916/diag_v916_main/
├── aggregates/per_window_seed{0..23}.csv         # v9.14 baseline (24 seeds)
├── pulse/pulse_log_seed{0..23}.csv               # v9.14 baseline
├── labels/per_label_seed{0..23}.csv              # v9.14 baseline
├── audit/
│   ├── per_event_audit_seed{0..23}.csv           # 24 seeds, 総 120,782 rows
│   ├── per_subject_audit_seed{0..23}.csv
│   └── run_level_audit_summary_seed{0..23}.csv
├── subjects/per_subject_seed{0..23}.csv          # 96 v9.14 cols + 20 v915_* cols
├── selfread/
│   ├── per_cid_self_seed{0..23}.csv              # 28 cols, 総 5,759 cids
│   ├── divergence_log_seed{0..23}.csv            # 11 cols, event 駆動
│   ├── observation_log_seed{0..23}.csv           # 11 cols, 120,782 rows (段階 3 新規)
│   └── class_divergence_seed{0..23}.csv          # 10 cols (段階 2 継承)
└── ... (pickup / representatives / network / introspection / persistence)
```

集計 JSON: `primitive/v916/analyze_stage3_main_output.json` (全統計値を JSON で保存)。

---

## 9. 本番 run で確認された Phase 3 議論への入口

以下の事実を元に、段階 1 + 段階 2 + 段階 3 の統合議論 (Phase 3) を進める下地が整った:

1. 段階 3 でも Layer A / Layer B frozen が維持される (Fetch 総数 / baseline 6 本とも bit-identity)
2. `theta_diff_norm_all` が段階 2 の `theta_diff_norm` と完全一致 (物理計算の不変)
3. age_factor × missing の単調関係 (構造的に自明、しかし実測確認)
4. Q 枯渇 cid が 34.26 % 現れる (段階 3 のサンプリング機構が大規模 run で有意に効いている)
5. seed CV 3–4 % (統計的集中、24 seeds 合算値の代表性)

Phase 3 着手は Taka 承認待ち。

---

*以上、v9.16 段階 3 本番 run 観察報告。結論なし、観察事実のみ。*
