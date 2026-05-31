# 注意センター ESDE — Step B smoke 観察事実報告 (判定置かない)

**Date**: 2026-06-01
**Author**: Code A
**Status**: smoke 完了、観察事実のみ、Web Claude 機能設計待ち
**親**: Step B 機能設計 + 確認 4 点 + Taka 「λ の元を center 側の phase まとまりに差し替え、あとは進めて」
**規律**: 判定置かない / 観察事実のみ / 主題評価は Taka 領域 / source_event 1 本 / 物理層 frozen

---

## 0. 観察事実 (要点、最終 window)

| 指標 | no_center | with_center | Δ rel | 部位 |
|---|---|---|---|---|
| **near_occ_sum** (狙った phase 近傍) | 0.1147 | 0.0647 | **-43.56%** | 近傍 |
| **far_occ_sum** (狙った phase 遠方) | 0.8853 | 0.9353 | +5.64% | 遠方 |
| **near_far_ratio** | 0.1296 | 0.0692 | **-46.57%** | 比率 |
| labels_total | 144 | 152 | +5.56% | CID |
| share_max | 0.025 | 0.034 | **+34.63%** | CID |
| torque_events | 1429 | 1516 | +6.09% | CID |
| occ_max (全体集中) | 0.062 | 0.062 | +0.01% | 全体 |
| alive_l_count | 3139 | 3132 | -0.22% | 物理 |

**発火 5/5** (常時発火、無視動作未観察)
**max_w 0.982-0.998** (Step A の overlap=0 問題は解消、ある label が target_phase に非常に近い)
**target_phase**: 3.09-5.44 rad (毎 window 動的)
**λ_dynamic**: center 側 phase まとまりから (Taka 2026-06-01 指示)

---

## 1. Step A → Step B 変更点 (実装)

| 項目 | Step A | Step B |
|---|---|---|
| stress_enabled | False (stress=1.0 固定) | **True** (stress 0.95-1.00 動的) |
| 向き先 | node ID overlap → ほぼ 0 多発 | **phase 連続一致率 w = exp(-λ·d)、max_w 0.99** |
| λ_dyn の元 | (Code A 初版: Atom 系) | **center 側 phase まとまり** (Taka 2026-06-01) |
| 観察 | 全体集計のみ | **+ 近傍/遠方分解 (K_NEAR=3, ±7 bins)** |

---

## 2. 1 往復動態 (loop_log)

| window | fire | stress | z_score | target_phase | max_w | atom_inject_n |
|---|---|---|---|---|---|---|
| 0 | True | 1.000 | 5.49 | 5.33 | 0.997 | 5 |
| 1 | True | 0.965 | 6.07 | 5.44 | 0.998 | 5 |
| 2 | True | 0.951 | 7.40 | 3.09 | 0.988 | 5 |
| 3 | True | 0.958 | 6.89 | 4.03 | 0.997 | 5 |
| 4 | True | 0.973 | 6.78 | 5.35 | 0.982 | 5 |

- target_phase が毎 window 異なる (3.09-5.44) = 動的、固定でない
- max_w がほぼ 1.0 = 「ある label が target_phase に非常に近い」 = 狙い撃ちが効いている
- 発火条件は z_score (5.49-7.40) vs stress (0.95-1.00)、両者動的だが z_score が常に大きく上回り = 5/5 常時発火

---

## 3. 観察事実の詳細

### 3.1 近傍/遠方分解 (狙い撃ちか盲目か、Web Claude §3 の本命指標)

| 指標 | no_center | with_center | Δ |
|---|---|---|---|
| near_occ_sum (target_phase ±3 bins ≈ ±17°) | 0.1147 | 0.0647 | **-43.56% rel** |
| far_occ_sum (それ以外の bins) | 0.8853 | 0.9353 | +5.64% rel |
| near_occ_mean / bin | 0.0164 | 0.0092 | -43.56% rel |
| far_occ_mean / bin | 0.0155 | 0.0164 | +5.64% rel |
| near_far_ratio | 0.1296 | 0.0692 | **-46.57% rel** |

**観察事実**:
- 狙った phase 近傍の occupancy が **大きく減少** (-43.56%)
- 狙った phase 遠方は **微増** (+5.64%)
- 全体 occ_max は **ほぼ不変** (+0.01%)

→ 全体集計では区別不能だった「狙った所の偏った変化」が、近傍/遠方分解で見える。

### 3.2 CID 構造

| 指標 | no_center | with_center | Δ rel |
|---|---|---|---|
| labels_total | 144 | 152 | +5.56% |
| n_core_mean | 2.09 | 2.08 | -0.54% |
| pct_n_core_2 | 95.83% | 96.71% | +0.92% |
| pct_n_core_5plus | 2.08% | 1.97% | -5.26% |
| share_mean | 0.0069 | 0.0066 | -5.49% |
| **share_max** | 0.0249 | 0.0336 | **+34.63%** |
| torque_events | 1429 | 1516 | +6.09% |

- labels 数 +8 (注意センター介入で labels 維持/増加)
- share_max が rel +34.63% 増 = 最大 share label が際立つ
- pct_5plus 微減

### 3.3 物理層 (同型 fork 検証)

| 指標 | Δ rel | 観察 |
|---|---|---|
| alive_n_count | 不変 | 5000 固定 |
| alive_l_count | -0.22% | ほぼ不変 |
| stress_intensity | +0.20% | ほぼ不変 |
| occ_max (全体) | +0.01% | 不変 |
| occ_mean | 不変 | -- |

→ 物理層は条件変動に対して堅牢 (Taka 言及 + 第 4 段階 smoke と一致)。

---

## 4. Step A との比較 (3 つの直しの成立)

| 直し | Step A 結果 | Step B 結果 | 評価 (Code A、観察視点) |
|---|---|---|---|
| ① 向き先 phase 連続一致率 | overlap=0 (w=0-3) | max_w 0.99 (5/5) | **配管成立** (二値の全滅消えた) |
| ② 発火両辺 state 動的 | stress=1.0 固定 | stress 0.95-1.00 動的 | 両辺動的化 ✓、ただし z_score 5-7 vs stress ~1 で **常時発火継続** |
| ③ 狙い撃ち / 盲目区別 | 全体集計のみ | 近傍/遠方分解 ★ | **近傍 -43.56% / 遠方 +5.64% で偏り** = 狙った所が動いた候補 |

→ Step A の盲目突き (overlap=0 フォールバック) から、Step B で **狙い撃ちの形が観察された**。

### 4.1 留保 (観察事実のみ、判定なし)

- **近傍が「減った」** = 狙った所の occupancy が下がった = 「押し込み」でなく「散らし」とも読める
  - 解釈は Taka 領域 (Code A は判定置かない)
- **発火 5/5 のまま** = 無視動作はまだ出ていない (z_score がいつも stress を大きく上回る)
- **1 seed のみ** = 多 seed で再現性確認は別 smoke

---

## 5. 規律遵守確認 (Web Claude §6)

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 3 instance | ✓ 全部 V82+VirtualLayerV9 + N=5000 |
| 書込 source_event 1 本 (physics.inject) | ✓ state 直接 / cog 直接書込なし |
| トリガー固定しない | ✓ z_score + stress + λ_dyn + target_phase 全て state 由来 |
| **定義しない / 判定置かない** | ✓ 「成功」「失敗」「学習」未使用 |
| 主題評価は Taka 領域 | ✓ Code A は観察事実のみ |

---

## 6. Code A 観察 (判定でない、観察事実の整理)

### 6.1 観察された 3 事実

1. **狙い撃ちの形が観察された**: 近傍 occupancy -43.56% / 遠方 +5.64% / 全体 occ_max +0.01% → 集計差が近傍に偏って局在
2. **配管は完全に通った**: max_w 0.99、overlap=0 問題消えた、target_phase 動的、λ_dyn = center 側 phase まとまり由来
3. **選択性 (無視) はまだ出ていない**: 発火 5/5、z_score >> stress で常時発火

### 6.2 観察されなかったこと

- 無視 (should_attend = False) 動作
- 多 seed での再現性
- 「Atom プロファイル変化」 (Web Claude §0 で本回はスコープ外確定)

### 6.3 Web Claude §3 の判別への応答

「**狙った phase 近傍に偏って変化が出れば狙って効いた候補 / 全体均一なら盲目**」に対する観察:
- 近傍に偏った変化 (近傍 rel -43.56% / 遠方 rel +5.64%)
- 全体は不変 (occ_max +0.01%、stress 微変、alive_l 微変)
- → **狙い撃ちの形** に該当 (Code A は判定置かないため「該当する」とだけ言える、「狙って効いた」と断定しない)

---

## 7. Web Claude / Taka 判断要請

| # | 問い (Code A 提示のみ、判断は Taka) |
|---|---|
| ① | 近傍 -43.56% を「狙って効いた候補」と見るか、別解釈 (押し込みでなく散らし、または偶然) を疑うか |
| ② | 発火 5/5 (無視動作未観察) は機能設計上 OK か、別案 (発火閾値強化や別バー) で無視動作を出すか |
| ③ | share_max +34.63% (最大 share label 際立つ) は CID 構造側の付随変化として記録するか、別観察軸を加えるか |
| ④ | 多 seed (3-5 seeds) で再現性確認するか、機能 (機能 4 = 別系の上っぱり扱い等) を先に設計するか |
| ⑤ | λ_dyn を center 側にした効果 (target_phase 動的、max_w 0.99) は意図通りか |

---

## 8. 出力ファイル

- `stage5_step_b_check.md` (確認 4 点回答)
- `stage5_step_b_smoke.py` (実装、Taka 2026-06-01 修正反映)
- `stage5_step_b_smoke_report.md` (本文書)
- `run_smoke_b/smoke_b_full.parquet` (10 rows = 2 cond × 5 win)
- `run_smoke_b/smoke_b_loop_log.parquet` (5 rows、発火動態)
- `run_smoke_b/smoke_b_run_summary.json`

---

## 9. 一文サマリ

注意センター Step B smoke 観察事実 (Code A、2026-06-01、Web Claude Step B 機能設計 + Taka 「λ の元を center 側の phase まとまりに差し替え、あとは進めて」+ 判定置かない規律) として、実行 (3 instance 同型 V82+VirtualLayerV9 N=5000、Atom seed=42 / Center seed=99 / Other seed=100、stress_enabled=True で stress 動的化、2 conditions × 5 windows × 100 steps、658 秒)、観察事実 (要点 = 近傍/遠方分解で **near_occ_sum rel -43.56%** + **far_occ_sum rel +5.64%** + **near_far_ratio rel -46.57%**、全体 occ_max +0.01% 不変、share_max rel +34.63%、labels rel +5.56%、torque +6.09%、物理層 alive_l rel -0.22% 不変、発火 5/5 常時 max_w 0.99 で Step A overlap=0 問題解消、target_phase 3.09-5.44 動的)、Step A→B 3 つの直し (① 向き先 phase 連続一致率 ✓ overlap=0 消えた max_w 0.99 / ② 発火両辺 state 動的 △ stress 動的化したが z_score>>stress で常時発火継続 / ③ 狙い撃ち/盲目区別 ★ 近傍偏り出た)、留保 (近傍が「減った」は押し込みでなく散らしとも読める判定は Taka 領域 / 発火 5/5 で無視動作未観察 / 1 seed)、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない z_score/stress/λ_dyn/target_phase 全て state 由来 + 定義しない判定置かない + 主題評価 Taka 領域)、Code A 観察 (狙い撃ちの形に該当 但し断定しない / 配管完全に通った / 選択性無視まだ出ていない)、Web Claude §3 判別への応答 (近傍に偏った変化で狙い撃ち候補に該当)、判断 5 件 (近傍-43.56% の解釈 / 無視動作 OK か / share_max +34.63% 記録 / 多 seed か機能設計か / λ_dyn center 側 OK か)、書込み unified/attention_center_prep/ 配下のみ。

---

**Step B smoke 観察事実 end. Web Claude 機能設計 + Taka 主題評価待ち。**
