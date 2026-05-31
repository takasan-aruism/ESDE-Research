# 注意センター ESDE — Step C smoke 観察事実報告 (判定置かない)

**Date**: 2026-06-01
**Author**: Code A
**Status**: smoke 完了、観察事実のみ、Web Claude 機能設計 + Taka 主題評価待ち
**親**: Step C 機能設計 + Taka 「A→B ゼロサム期待捨てる、何度も信号 → 振り分け」
**規律**: 判定置かない / 観察事実のみ (向きも事実) / 主題評価は Taka 領域 / source_event 1 本 / 物理層 frozen

---

## 0. 観察事実 (要点)

### 時間方向の差分的残留 (Web Claude §2 本命指標)

high_low_ratio = (よく触れた帯 occ) / (触れてない帯 occ)

| condition | initial (w=0) | final (w=14) | Δ (last - first) | |
|---|---|---|---|---|
| no_center | 0.795 | 0.691 | -0.10 | 自然減衰 |
| **center_no_other** (別系飛ばし) | 0.800 | **0.485** | **-0.32** | 触れた帯が**散らされる** |
| **center_other** (フルループ) | 0.800 | **0.796** | **-0.004** | **ほぼ維持** |

→ **別系ありでだけ「狙った帯が時間とともに保たれる」が観察された**。
別系なしでは、繰り返し触れるとかえって帯が散らされる (Δ=-0.32)。

### 帰属差分 (center_other - center_no_other、最終 window)

| 指標 | Δ | rel |
|---|---|---|
| **strat_high_low_ratio** | **+0.312** | **+64.34%** |
| strat_high_occ_sum (高接触帯) | +0.023 | +12.77% |
| strat_low_occ_sum (低接触帯) | -0.115 | -31.38% |
| labels_total | -9 | 12.16% |
| share_max | -0.008 | -17.83% |
| torque_events | -146 | -15.96% |
| alive_l_count | -18 | -0.58% |

→ 別系経由で **高接触帯と低接触帯の差が rel +64% 大きく保たれる**。

---

## 1. 実行構成 + 時間

- 3 conditions × 15 windows × 100 steps × N=5000、1 seed (atom=42, center=99, other=100)
- windows=15 根拠: FAMILIARITY_DECAY=0.998 半減期 ~3.5 window × ~4 で累積効果
- 計算時間: 39 分 (no_center 454s + center_no_other 901s + center_other 992s)

---

## 2. 接触頻度マップの動態

| condition | 最終 contact_max (1 bin の最大接触回数) | 発火 |
|---|---|---|
| no_center | 0 (発火なし) | -- |
| center_no_other | 5 | 15/15 |
| center_other | 5 | 15/15 |

- center 系 2 conditions で同じ繰り返し回数 (Web Claude §3 同一向き先・頻度)
- target_phase 履歴で同じ phase 帯が複数回 (max 5 回) 接触

---

## 3. 時系列の動態 (差分的残留)

### 3.1 no_center (自然減衰)

```
w=0: ratio 0.795
w=4: ratio 1.111 (一時上昇)
w=9: ratio 1.296 (最大)
w=14: ratio 0.691 (収束)
Δ = -0.10
```
→ 注意がない自然進化、ratio は揺らぐが overall 微減。

### 3.2 center_no_other (繰り返し注意かき混ぜ)

```
w=0: ratio 0.800
w=4: ratio 0.599 (急減)
w=7: ratio 0.407 (最低)
w=14: ratio 0.485
Δ = -0.32
```
→ 「狙った帯」の occupancy が時間とともに **散らされる**。15 windows で ratio が **40% 下落**。

### 3.3 center_other (別系経由フルループ)

```
w=0: ratio 0.800
w=5: ratio 1.148 (一時上昇)
w=8: ratio 0.767
w=14: ratio 0.796
Δ = -0.004
```
→ 揺らぐが overall ほぼ **不変**、初期 ratio が **15 windows 経過しても維持**。

---

## 4. Web Claude §3 「別系帰属の最小対比」への応答

「`center_other` に出て `center_no_other` には出ない差分的残留」 = **観察された**:

| 観察 | center_no_other | center_other |
|---|---|---|
| 繰り返し触れた帯の occupancy | 時間とともに薄まる (散らし) | 保たれる |
| 触れてない帯の occupancy | 増える (kick out された分が逃げる) | あまり増えない |
| high_low_ratio の時間変化 | Δ -0.32 (大きく下落) | Δ -0.004 (維持) |
| 帰属差分 | -- | +64.34% rel (center_other 優位) |

→ **別系を通したときだけ、「狙った帯が選択的に残る」現象が観察された**。

主題評価 (これを「振り分け」「学習の手がかり」と呼べるか) は Taka 領域。Code A は **観察事実として「center_other でだけ ratio が維持され、center_no_other では散らされる」を記録**。

---

## 5. CID 構造 (付随観察)

| condition | final labels | torque_events | share_max |
|---|---|---|---|
| no_center | 79 | 1437 | 0.0440 |
| center_no_other | 74 | 1062 | 0.0455 |
| center_other | 65 | 916 | 0.0374 |

- center_other で **labels 最少** (-14 vs no_center)
- 同時に center_other で high_occ_sum は最大維持 → **labels 数は少ないが、狙った帯の occupancy は保たれる**
- これは「label が少なく、その分が高接触帯に集中している」と読めるが、解釈は Taka 領域

---

## 6. 物理層 (堅牢、第 4 段階 + Step B と整合)

| condition | final alive_l | stress_intensity |
|---|---|---|
| no_center | ~3120 | 0.97-1.00 動的 |
| center_no_other | ~3100 | 0.97-1.00 |
| center_other | ~3082 | 0.97-1.00 |

→ 3 conditions で物理層はほぼ不変 (Δ < 1%)、ratio の動態は CID 層 / phase 層で起こっている。

---

## 7. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 3 instance + 物理切らない | ✓ stress_enabled=True 継承 |
| 書込 source_event 1 本 (physics.inject) | ✓ |
| トリガー固定しない | ✓ z_score + stress + λ_dyn + target_phase 全て state 由来 |
| 定義しない | ✓ 「学習」「振り分け」未使用 |
| **判定置かない (向きも事実)** | ✓ Δ=-0.32 と Δ=-0.004 を観察事実として記録、「成功」「失敗」未使用 |
| 無視動作は記録だけ (バー手いじり禁止) | ✓ 発火 15/15 のまま、バー変更なし |
| 観察軸を増やすことを駆動要因にしない | ✓ 駆動 1 文 (差分的残留) を守り、観察軸は 1 つ (高低 occ_ratio) |

---

## 8. Code A 観察 (判定でない、観察事実の整理)

### 8.1 観察された 3 事実

1. **3 conditions で時間方向に高低 occ_ratio の動態が異なる**:
   - no_center: 自然減衰 Δ -0.10
   - center_no_other: 大きく下落 Δ -0.32
   - center_other: ほぼ維持 Δ -0.004
2. **帰属差分 (別系ありでだけ出る差)**: high_low_ratio rel +64.34%、high_occ_sum +12.77%、low_occ_sum -31.38%
3. **CID 構造**: 別系経由で labels 数が最少 (-14 vs no_center) になるが、occupancy パターンは保たれる

### 8.2 観察されなかったこと

- 無視動作 (3 conditions 中の発火 conditions で 15/15、常時発火継続)
- 多 seed の再現性
- 「Atom プロファイル変化」(Web Claude スコープ外確定)

### 8.3 増減の向きについて (Web Claude §0 規律準拠)

- center_no_other の Δ -0.32 (散らし方向) と center_other の Δ -0.004 (維持方向) は、両方とも観察事実
- Taka 指示「向きを成功基準にしない」遵守
- 「散らされる方が悪い、維持される方が良い」のような判定は Taka 領域

---

## 9. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | center_other で ratio 維持 (Δ -0.004) と center_no_other で大きく下落 (Δ -0.32) の差を「別系経由で狙った帯が選択的に残る」と読むか、別解釈か |
| ② | 帰属差分 high_low_ratio rel +64% は本丸の「中身を運ぶ/学習する」の入口の手がかりとなるか |
| ③ | center_other で labels 数が最少 (-14) なのは「効率化」「情報集約」と読めるか、それとも単に label 死亡が早かっただけか (もっと長い run で見るか) |
| ④ | 多 seed (3-5 seeds) で再現性確認するか、別の機能設計 (機能 4 = 注意の循環、保持機構等) に進むか |
| ⑤ | 無視動作は記録だけ規律で 15/15 常時発火のまま、これは今回は問わないが、次のレバーとして残す |

---

## 10. 出力ファイル

- `stage5_step_c_smoke.py` (実装)
- `stage5_step_c_smoke_report.md` (本文書)
- `run_smoke_c/smoke_c_full.parquet` (45 rows = 3 cond × 15 win)
- `run_smoke_c/smoke_c_loop_log.parquet` (30 rows、発火動態)
- `run_smoke_c/smoke_c_run_summary.json` (contact_maps 含む)

---

## 11. 一文サマリ

注意センター Step C smoke 観察事実 (Code A、2026-06-01、Web Claude Step C 機能設計 + Taka「A→B ゼロサム期待捨てる何度も信号→振り分け」+ 判定置かない規律) として、駆動 1 文「繰り返し接触の中で別系に関係するものが選択的に残るか」に対し、3 conditions × 15 windows × N=5000 × 39 分実行で時間方向の差分的残留 high_low_ratio が (no_center Δ -0.10 自然減衰 / center_no_other Δ **-0.32** 散らし / center_other Δ **-0.004** ほぼ維持) と異なる動態を観察、帰属差分 (center_other - center_no_other) で strat_high_low_ratio rel **+64.34%** strat_high_occ_sum +12.77% strat_low_occ_sum -31.38% labels -9 share_max -17.83% torque -15.96% alive_l -0.58%、Web Claude §3「center_other に出て center_no_other には出ない差分的残留」が観察された (別系経由でだけ狙った帯が選択的に残る)、CID 構造 (center_other で labels 最少 -14 だが狙った帯の occupancy は維持 = label 集約)、物理層 3 conditions で堅牢 (alive_l, stress 微変)、発火 15/15 常時 (無視動作未観察規律で手いじりせず)、規律遵守 (物理層 frozen + 同型 + source_event 1本 + トリガー固定しない z_score/stress/λ_dyn/target_phase 全て state 由来 + 定義しない + 判定置かない向きも事実 + 無視はバー手いじり禁止 + 観察軸増やさず駆動 1 文守る)、Code A 観察 (3 conditions 時間動態異なる + 帰属差分は別系ありでだけ + CID 構造 labels 数最少だが occupancy 維持)、増減の向きは観察事実として両方記録 Taka 規律準拠、判断 5 件 (ratio 維持/下落差を別系経由帰属と読むか / +64% 帰属差分は本丸入口手がかりか / labels -14 は効率化か単純な死亡早期化か / 多 seed か次機能か / 無視動作は次のレバー残す)、書込み unified/attention_center_prep/ 配下のみ。

---

**Step C smoke 観察事実 end. Web Claude 機能設計 + Taka 主題評価待ち。**
