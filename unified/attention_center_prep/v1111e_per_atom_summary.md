# v1111e_redo per-atom 層化再集計

**Date**: 2026-06-02
**Author**: Code A
**目的**: Taka 指摘「集団平均の罠」を per-atom 層化で見直す

## 主要発見

### 1. atom 別 inversion: 10/24
- 集団平均 (24 atom cos) では 2/3 Other inversion
- per-atom 個別判定で 10/24 atom が inversion 寄り
- 24 atom が一様ではない (個性あり)

### 2. group 別 (8 atom × 3 group)
- group 0 (atom 1000-1007): 3/3 Other inversion
- group 1 (atom 1008-1015): 3/3 Other inversion
- group 2 (atom 1016-1023): 1/3 Other inversion

→ **group 2 のみ動態が逆**。集団平均で消えていた個別動態。

### 3. self 床距離
- 11/24 atom で injected が self に近い
- shuffled の方が self から離れる atom 多 = Atom 構造支配的 (Taka 整理「どの seed でもそれらしい形」と整合)

### 4. d_between 分布
- injected_other: mean=0.7485, std=0.1695, min=0.4417, max=0.9919
- shuffled_other: mean=0.6689, std=0.1295, min=0.4380, max=1.0355

## 過去パターン未流用の確認

| パターン | 状態 |
|---|---|
| n_core 別層化 (v10.2 核心) | 本データに n_core 情報なし、**再 run で取得必要** |
| per-step 観察 (v9.18) | 本データは window 単位、**再 run で per-step 必要** |
| 5 種 event + 5 種 path (v10.7) | 本データは occupancy のみ、**追加観察必要** |

## 結論

- 集団平均 (2/3 inversion) は 24 atom 横断の平均化結果
- per-atom で見ると group 2 が逆方向 = **全 atom が同じ動態ではない**
- ですが本データに n_core / per-step / event 別の情報なし
- 「集団平均で消えた個別動態」を本格的に見るには **再 run で観察軸を増やす必要**
