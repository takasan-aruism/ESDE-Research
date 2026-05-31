# Step C — Other seed 4 runs 観察事実報告 (判定置かない)

**Date**: 2026-06-01
**Author**: Code A
**Status**: 4 runs 並列完了、観察事実のみ、Web Claude/Taka 判断待ち
**親**: Step C smoke (+64.34%) + 多 seed 再現失敗 + Taka 「abc 全て実施」
**規律**: 判定置かない / 観察事実のみ / 主題評価は Taka 領域

---

## 0. 出口 (要点)

| Run | 設定 | 結果 |
|---|---|---|
| **Run 1 再現** | atom=42, center=99, **other=100** | **+64.34%** (Step C smoke と完全一致 ✓) |
| Run 2 案 a (Other=Atom+58) | 3 seed_sets | -2.45% ± 59.22% (same_sign=False) |
| Run 3 案 b (Other=100 固定) | 3 seed_sets | +23.74% ± 67.91% (2/3 同方向 +60% 程度) |
| **Run 4 案 c (Other 変動)** | atom=42, center=99 固定 | **Other=100 +64.34% / Other=101/102 +33.87%** |

### 主要発見

1. **同じ設定なら +64.34% は完全に再現する** (Run 1) → 前回「multiprocessing 非決定性」仮説は誤り、撤回
2. **Other seed が小さく変わっても rel が大きく変動** (Run 4: 100→101 で +64% → +33%)
3. **Other=100 が特異** (Run 3 で atom=42/100 ともに +60% 台、Run 4 で other=100 だけ +64%)
4. **share_max は安定** (Run 2 で same_sign=True、-21.20% ± 15.37%)

---

## 1. 並列実行 (Taka 「24 コア並列」)

- 17 unique tasks を Pool(17) で並列実行
- OMP/MKL/OPENBLAS thread=1 で thread 競合回避
- 総時間 **1217 秒 (20.3 分)**
- 各タスク ~17-20 分 (max=20m → 並列で完了)

---

## 2. Run 1: 再現確認 ✓

| condition | high_low_ratio | labels_total | share_max |
|---|---|---|---|
| no_center | 0.6905 | 79 | 0.0481 |
| center_no_other | **0.4845** | 74 | 0.0453 |
| center_other | **0.7963** | 65 | 0.0372 |

**帰属差分 high_low_ratio rel = +64.34%** (Step C smoke と完全一致)

→ Step C smoke の +64.34% は **再現する事実**。前回 multiprocessing 非決定性仮説は誤り。

---

## 3. Run 2: 案 a (Other = Atom + 58)

| (atom, center, other) | high_low_ratio rel | labels rel | torque rel | share_max rel |
|---|---|---|---|---|
| (42, 99, 100) | **+64.34%** | -12.16% | -15.96% | -17.83% |
| (100, 157, 158) | -48.53% | +17.57% | +21.84% | -37.98% |
| (200, 217, 258) | -23.16% | -8.22% | -12.90% | -7.80% |
| **3 seeds 平均** | -2.45% ± 59.22% | -0.94% ± 16.15% | -2.34% ± 21.00% | **-21.20% ± 15.37%** |
| same_sign | False | False | False | **True** ★ |

→ high_low_ratio は seed ごとにバラバラ。share_max のみ全 seed で同方向。

---

## 4. Run 3: 案 b (Other = 100 固定)

| (atom, center, other) | high_low_ratio rel | labels rel | torque rel | share_max rel |
|---|---|---|---|---|
| (42, 99, 100) | **+64.34%** | -12.16% | -15.96% | -17.83% |
| (100, 157, 100) | **+61.55%** | +22.97% | +21.49% | -29.81% |
| (200, 217, 100) | -54.66% | -5.48% | +1.78% | +2.86% |
| **3 seeds 平均** | +23.74% ± 67.91% | +1.78% ± 18.66% | +2.44% ± 18.73% | -14.93% ± 16.52% |

→ **atom=42 と atom=100 で +60% 程度 (同方向)**、atom=200 のみ逆方向 (-54.66%)。
2/3 が同方向だが、atom=200 で大きく逆。

---

## 5. Run 4: 案 c (Other 影響度直接観察、atom=42/center=99 固定)

baseline: center_no_other ratio=0.4845, labels=74, torque=915

| Other | ratio | Δrel vs cn | labels Δrel | torque | share_max |
|---|---|---|---|---|---|
| **100** | **0.7963** | **+64.34%** | -12.16% | 769 | 0.0372 |
| **101** | 0.6486 | **+33.87%** | +1.35% | 934 | 0.0407 |
| **102** | 0.6486 | **+33.87%** | -6.76% | 928 | 0.0511 |

→ **Other=100 だけが +64%、Other=101/102 は両方 +33%** (偶然完全に同値)。
Other seed の 1 つの変動が rel を **半減** させる強い影響。

### 5.1 Other=100 の特異性

- 全 4 runs で Other=100 + atom=42 の組合せは **+64.34%** を再現
- Other=101 or 102 では +33.87% (両方同値)
- 「Other=100 が atom=42 と特に整合する」現象

---

## 6. 観察事実の整理

### 6.1 再現性 (Code A 判定置かない)

- **同じ (atom, center, other, condition) なら完全再現**:
  - Run 1 と Run 2 (42, 99, 100, *)、Run 3 (42, 99, 100, *)、Run 4 (42, 99, 100, *) すべて同値
  - 例: high_low_ratio 0.4845 / 0.7963 が全 instance で一致
- これは「同じ seed 設定 + 同じコード経路なら decidable」が確認された
- 前回「multiprocessing 非決定性」は **誤った推測、撤回**

### 6.2 Other seed の影響

- Other=100 (atom=42, center=99) → +64.34%
- Other=101, 102 → +33.87% (両方同値)
- Other=Atom+58 で他 seed (100→158, 200→258) → 大きく逆方向
- → **Other seed の選び方で結果が大きく変わる**、Other=100 が atom=42 に特異

### 6.3 share_max の安定 (再現的)

- Run 2 で share_max rel: -17.83% / -37.98% / -7.80% (all negative、same_sign=True)
- 3 seeds 平均 -21.20% ± 15.37%
- → 「**別系経由で share_max が下がる**」は seed に依存しない再現現象

### 6.4 「狙った帯が残る」現象の限界

- **(atom=42, other=100)** の組合せでだけ +64% が出る
- **同じ atom でも Other 違うと +33%** (Other=101/102) → +30 ポイントの大差
- **同じ Other=100 でも atom=200 だと -54%** (逆方向)
- → 「狙った帯が残る」は **特定 seed 組合せの現象**、一般化できない

---

## 7. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 + 物理切らない | ✓ |
| 書込 source_event 1 本 | ✓ |
| トリガー固定しない | ✓ |
| 定義しない / 判定置かない | ✓ |
| **同 seed 完全再現の確認** | ✓ Run 1 で +64.34% 完全一致 |
| 前回誤推測の撤回 | ✓ §6.1 で multiprocessing 非決定性仮説撤回 |

---

## 8. Code A 観察 (判定でない、事実整理)

### 8.1 確実に言えること

1. **同 seed 完全再現** (Run 1 で Step C smoke の +64.34% 完全一致)
2. **Other seed が rel を強く左右する** (Run 4 で +64% → +33% の半減)
3. **Other=100 + atom=42 が特異な組合せ** (4 runs 全部で +64%)
4. **share_max は 3 seeds で同方向** (-21.20% ± 15.37%、Run 2)

### 8.2 残った疑問

- Other=100 と atom=42 が偶然整合した可能性 (特異点)
- 24 seeds フルで share_max の再現性を確認するか
- 「狙った帯が残る」は本当に「学習」「振り分け」と呼べる現象か、それとも特定 seed 組合せの artifact か

### 8.3 前回報告との差

- 前回多 seed 報告: 「multiprocessing 非決定性可能性」と書いたが **誤り**
- 真の原因 = Other seed の小さな変動が rel を半減 (Run 4 で確証)

---

## 9. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | +64% が「Other=100 + atom=42」固有の特異現象であることを受けて、Step C の「狙った帯が残る」主張を保留にするか |
| ② | share_max の安定変化 (Run 2 で -21% ± 15%、3 seeds 同方向) を本命指標に切り替えるか |
| ③ | Run 4 の Other=100 vs 101/102 の特異性 (なぜ Other 100 だけ +64% か) を構造的に調査するか |
| ④ | Other seed の選び方を体系化するか (例: Other を全 atom と独立にする random、または Other を Atom と Center の関数で固定) |
| ⑤ | 24 seeds フルで share_max の再現性を確認するか、それとも別の機能設計に進むか |

---

## 10. 出力ファイル

- `stage5_step_c_other_seed_4runs.py` (実装)
- `stage5_step_c_other_seed_4runs_report.md` (本文書)
- `run_other_seed_4runs/other_seed_4runs_full.parquet` (255 rows = 17 tasks × 15 win)
- `run_other_seed_4runs/other_seed_4runs_summary.json`

---

## 11. 一文サマリ

Step C Other seed 4 runs 並列観察事実 (Code A、2026-06-01、Taka「abc 全て実施」+ 24 コア並列、17 unique tasks 20.3 分実行、判定置かない) として、Run 1 再現確認で同設定 (atom=42, center=99, other=100) で **+64.34% 完全再現** → 前回多 seed 報告での「multiprocessing 非決定性可能性」推測は誤り撤回、Run 2 案 a (Other=Atom+58) で 3 seeds の high_low_ratio rel は -2.45% ± 59.22% same_sign=False (seed 依存大) ただし share_max rel **-21.20% ± 15.37% same_sign=True で 3 seeds 同方向**、Run 3 案 b (Other=100 固定) で 2/3 seeds (atom=42 +64.34% / atom=100 +61.55%) 同方向 +60% 程度だが atom=200 のみ -54.66% で逆、Run 4 案 c (atom=42/center=99 固定 Other 変動) で **Other=100 +64.34% / Other=101 +33.87% / Other=102 +33.87%** Other seed 1 つの変動で rel が半減し Other=101 と 102 が偶然完全同値、主要発見 (同 seed 完全再現/Other seed の影響大/Other=100+atom=42 が特異組合せ/share_max は安定再現)、解釈 (狙った帯が残るは特定 seed 組合せの現象で一般化できない、share_max -21% は再現性ある別系経由効果、Other=100 が atom=42 に特異整合した可能性)、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない + 定義しない判定置かない + 同 seed 完全再現確認 + 前回誤推測撤回)、判断 5 件 (Step C 主張保留 / share_max を本命に切替 / Other=100 特異性調査 / Other seed 選び方体系化 / 24 seeds フルか別機能設計)、書込み unified/attention_center_prep/ 配下のみ。

---

**Step C Other seed 4 runs end. Web Claude/Taka 判断待ち。**
