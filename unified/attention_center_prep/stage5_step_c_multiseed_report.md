# 注意センター Step C 多 seed 再現確認 観察事実 (判定置かない)

**Date**: 2026-06-01
**Author**: Code A
**Status**: 多 seed 並列実行完了、観察事実のみ、Web Claude / Taka 判断待ち
**親**: Step C smoke (1 seed で +64.34% 観察) + Taka 指示「多 seed で +64% の再現を先に固める」 + Taka 指示「24 コア並列」
**規律**: 判定置かない / 観察事実のみ (向き・再現失敗も事実) / 主題評価は Taka 領域

---

## 0. 出口 (観察事実)

| 指標 | 1 seed (smoke) | 3 seeds 平均 ± std | same_sign | 再現? |
|---|---|---|---|---|
| **high_low_ratio (本命)** | +64.34% | **-14.29% ± 42.93%** | **False** | **再現せず** |
| high_occ_sum | +12.77% | -17.40% ± 20.96% | False | 再現せず |
| low_occ_sum | -31.38% | +4.37% ± 25.80% | False | 再現せず |
| **labels_total** | -12.16% | **+7.68% ± 8.68%** | **True** | **同方向** |
| **torque_events** | -15.96% | **+9.75% ± 10.60%** | **True** | **同方向 (符号逆)** |
| **share_max** | -17.83% | **-20.50% ± 15.24%** | **True** | **同方向** |
| alive_l_count | -0.58% | -0.03% ± 2.61% | False | 物理層 堅牢 |

注: 1 seed と 3 seeds 平均で同方向は **share_max のみ** (-17.83% vs -20.50%)。
labels_total と torque_events は **符号が逆** (1 seed で減、3 seeds で増)。

---

## 1. 並列実行 (Taka 「24 コア並列」)

- multiprocessing.Pool(9) で 9 並列実行
- OMP/MKL/OPENBLAS thread = 1 で thread 競合回避
- 各 process ~17-19 分 (no_center 533s, center_no_other 1054s, center_other 1158s)
- **総時間 1159 秒 (19.3 分)** = 直列予想 2 時間の **1/6**

---

## 2. seed 別 high_low_ratio (本命指標)

| seed | no_center | center_no_other | center_other | Δ (co - cn) | rel |
|---|---|---|---|---|---|
| 42  | 0.690 | 0.485 | 0.649 | +0.164 | **+33.87%** |
| 100 | 0.700 | 1.590 | 0.818 | -0.772 | **-48.53%** |
| 200 | 0.482 | 2.024 | 1.453 | -0.571 | **-28.22%** |

→ **seed 42 と seed 100/200 で符号が逆**。Step C smoke (1 seed=42) の +64% は seed 42 特有の方向。

### 2.1 seed 42 (Step C smoke と同じ)

- center_no_other (0.485) < center_other (0.649) < no_center (0.690)
- Step C smoke で 0.485 vs 0.796 = +64% だったが、再 run では 0.485 vs 0.649 = +33.87%
- 同じ seed でも実行ごとに揺らぐ可能性 (engine.rng の seed は固定だが、何らかの非決定性?)

### 2.2 seed 100

- center_no_other (1.590) > center_other (0.818) > no_center (0.700)
- center_no_other が最大 (Step C smoke の seed 42 と逆現象)

### 2.3 seed 200

- center_no_other (2.024) > center_other (1.453) > no_center (0.482)
- center_no_other が最大、center_other より大

---

## 3. CID 構造側で再現 (副次指標)

| 指標 | seed 42 rel | seed 100 rel | seed 200 rel | mean ± std | same_sign |
|---|---|---|---|---|---|
| labels_total | +1.35% | +17.57% | +4.11% | +7.68% ± 8.68% | **True (全 +)** |
| torque_events | +2.08% | +21.84% | +5.33% | +9.75% ± 10.60% | **True (全 +)** |
| share_max | -10.03% | -37.98% | -13.48% | -20.50% ± 15.24% | **True (全 -)** |

→ **3 seeds 全部で同方向**:
- center_other で **labels 増、torque 増、share_max 減** (1 seed と符号逆だが、3 seeds で一貫)
- これは「別系経由で CID 構造に再現性ある変化」 = nothing でない

---

## 4. 1 seed (smoke) と 3 seeds の差

Step C smoke (1 seed = 42) と多 seed の差:

| 指標 | smoke (seed 42) | 多 seed 再 run (seed 42) | 多 seed 3 平均 |
|---|---|---|---|
| high_low_ratio | center_other=0.796, ratio=+64% | 0.649, ratio=+33% | -14% (バラバラ) |
| labels_total | -9 | +1 | +12 (+7.68%) |
| torque_events | -146 | +12 | +44 (+9.75%) |

→ 同 seed でも実行間で差。multiprocessing fork での内部 RNG/state の非決定性が原因の可能性 (要調査)。

---

## 5. 観察事実の整理 (判定置かない)

### 5.1 確実に言えること

1. **本命指標 high_low_ratio の +64% は 3 seeds で再現しない**:
   - same_sign=False、std 42.93% (mean -14%)
   - seed 42 (Step C smoke と同) でも再 run で +34% に減
2. **CID 構造側 3 指標が 3 seeds で同方向に動く**:
   - labels_total / torque_events 増、share_max 減
   - same_sign=True
3. **物理層は 3 seeds で堅牢** (alive_l_count rel ±0.03%)

### 5.2 観察事実から確実に言えないこと

- 「狙った帯が選択的に残る」(Step C 主張) は seed 42 の Step C smoke で観察された特定パターン、3 seeds では再現しない
- CID 構造の同方向変化は再現するが、それが「学習」「振り分け」と呼べるかは Taka 領域

### 5.3 再現性の解釈 (Code A 観察視点)

- 高 occupancy 帯と低 occupancy 帯の **絶対量** は seed 依存だが、変化の **方向** は CID 側で一貫
- Step C smoke で「ratio 維持」が観察された seed 42 では今回も同方向 (+33%)
- 他 seeds では center_no_other で逆に ratio が増 (1.5-2.0)、center_other で減る
- これは「seed ごとに contact_map と labels phase 分布の関係が異なる」が原因 (構造的)

---

## 6. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 + 物理切らない (stress=True) | ✓ |
| 書込 source_event 1 本 | ✓ |
| トリガー固定しない | ✓ (z_score/stress/λ_dyn/target_phase 全て state 由来) |
| 定義しない / 判定置かない | ✓ 「成功」「失敗」「学習」未使用 |
| **再現しなくても観察事実として記録** | ✓ 「再現せず」を率直に提示 |
| Taka 規律「smoke seed 0 を絶対視しない」 | ✓ 本報告で実証 (seed 42 は seed 100/200 と異なる方向) |

---

## 7. Code A 観察 (判定でない、事実整理)

### 7.1 主要観察

1. **本命指標 high_low_ratio の +64% は再現性なし** (1 seed のマグレ可能性)
2. **CID 構造側 3 指標は 3 seeds で同方向に再現**
3. **物理層は seed に関わらず堅牢**

### 7.2 想定外 (Taka 規律「結果が想定と合わなければ想定を見直す」)

- Step C smoke の「center_other で帯が保たれる」 = 1 seed 特有のパターン
- 3 seeds 平均では center_no_other で ratio が **増える** seed もある (smoke と逆方向)
- 「別系経由で残る」の主張は再考要

### 7.3 残った再現現象

CID 構造側 (labels_total +、torque_events +、share_max -) は **再現性あり**:
- これが「別系経由で何かが起こる」の手がかりとして残るか
- それとも単に center 計算の overhead が CID 寿命に効くだけか
- 判定は Taka / Web Claude 領域

---

## 8. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | 本命 high_low_ratio +64% が再現しなかったことを受けて、Step C の「狙った帯が残る」主張を撤回するか、別観察に切り替えるか |
| ② | CID 構造側 3 指標 (labels_total + / torque_events + / share_max -) の同方向再現を「別系経由の再現性ある変化」として記録するか |
| ③ | seed 42 で smoke (+64%) と再 run (+33%) で同 seed でも差が出た原因 (multiprocessing fork での非決定性か、別要因か) を調査するか |
| ④ | 24 seeds フル (Taka memory「24 seeds 1 バッチ」規律) でさらに固めるか、別の機能設計に進むか |
| ⑤ | Step C の「散らし vs 維持」観察は捨てて、CID 構造変化 (labels 増) を本命指標に切り替えるか |

---

## 9. 出力ファイル

- `stage5_step_c_multiseed_par.py` (並列実装)
- `stage5_step_c_multiseed_report.md` (本文書)
- `run_smoke_c_multiseed/multiseed_full.parquet` (135 rows = 3 seeds × 3 cond × 15 win)
- `run_smoke_c_multiseed/multiseed_diffs.parquet` (3 rows、帰属差分)
- `run_smoke_c_multiseed/multiseed_run_summary.json`

---

## 10. 一文サマリ

注意センター Step C 多 seed 再現確認 (Code A、2026-06-01、Taka 指示「+64% の再現を先に固める」+「24 コア並列」+ multiprocessing.Pool 9 並列、判定置かない規律) として、並列 19.3 分実行 (直列予想 2h の 1/6) で 3 seeds (atom=42/100/200, center=99/157/217, other=101/158/218) × 3 conditions × 15 windows 完了し、(本命) high_low_ratio rel **3 seeds 平均 -14.29% ± 42.93% same_sign=False で +64% **再現せず**、seed 42 は +33.87% (同 seed でも smoke の +64% より小)、seed 100 -48.53%、seed 200 -28.22% で **符号バラバラ**、(副次) CID 構造側で **labels_total rel +7.68% ± 8.68% / torque_events +9.75% ± 10.60% / share_max -20.50% ± 15.24%** が **3 seeds 全部 same_sign=True で再現** (ただし 1 seed smoke と符号逆)、物理層 alive_l rel -0.03% で seed に関わらず堅牢、Step C smoke の「狙った帯が選択的に残る」主張は 1 seed のマグレ可能性 (Taka 規律「smoke seed 0 を絶対視しない」を実証)、副次 CID 構造変化は再現性あるが「学習」「振り分け」と呼べるかは Taka 領域、判断 5 件 (本命撤回するか / CID 構造再現を本命に / 同 seed 内差の調査 / 24 seeds フル / 観察軸切り替え)、書込み unified/attention_center_prep/ 配下のみ。

---

**Step C 多 seed 再現確認 end. Web Claude / Taka 判断待ち。**
