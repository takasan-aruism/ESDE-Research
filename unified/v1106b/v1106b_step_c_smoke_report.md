# v1106b Step C — 観察 1 smoke 報告

**Date**: 2026-05-28
**Author**: Code A
**Status**: smoke 完了、Web Claude / Taka 確認待ち (memory rule: smoke 後 pause)
**親**: Step A 認識確認 + Step B 環境準備 (案 E 採用)

---

## 0. smoke 実行条件

| 項目 | 値 |
|---|---|
| 対象 seed | 0 (smoke seed) |
| 開始 CID 数 | 33 (案 E 7 bin × 各 CID 数) |
| N turn | 15 |
| 接続式 | top-1 自己対話 (Code A 介在なし、ESDE 発話を ESDE 自身に投げる) |
| 停止条件 | N turn 完走 (中断なし)、stuck/oscillation はラベル記録のみ |
| 実行時間 | **1.3 秒** (リソース load 0.7s + 自己対話 0.6s) |

開始 CID bin 分布 (seed=0):
- ghost mid: 3, ghost high: 5
- hosted mid: 5, hosted high: 5
- reaped low: 5, reaped mid: 5, reaped high: 5
- 合計: 33

---

## 1. 主要観察事実

### 1.1 familiarity 巻き戻り (rollback) — **構造特性として再確認**

| 指標 | 値 |
|---|---:|
| **rollback (20%+ 低下) 率** | **75.8% (25/33)** |
| start_familiarity 平均 | 115.45 |
| end_familiarity 平均 | 21.96 |
| min_familiarity 平均 | 17.98 |
| 平均最大低下幅 | **97.47** (115 → 18) |

→ Step P の 1 事例 (T0=116 → T6=6.1) は **特異事例でなく構造特性**。smoke 33 CID 中 75.8% で発生。

### 1.2 final_state 別 rollback 率

| final_state | n_start | rollback 率 | start_fam mean | min_fam mean |
|---|---:|---:|---:|---:|
| hosted | 10 | **100.0%** | 93.4 | 24.0 |
| ghost | 8 | 75.0% | 155.6 | 20.6 |
| reaped | 15 | 60.0% | 108.7 | 12.6 |

→ **hosted (生存中) 100% rollback** — 生存中 CID も自己対話で familiarity 低下、Step P の hosted 不到達と整合。

### 1.3 stuck / oscillation 検出 — **全 CID で発生**

| 検出 | 件数 |
|---|---:|
| stuck (同 CID 連続 K=3) | **33/33 (100%)** |
| oscillation (直近 W=5 turn で unique CID ≤ 2) | **33/33 (100%)** |

→ ESDE 自己対話は **数 turn 以内に固定 / 振動状態に入る構造**。Step P の T10 (反復停滞)、T12 (循環復帰) と整合。

---

## 2. per_seed × bin 確保数 (Taka 指示反映)

### 2.1 全 24 seeds × 7 bin の選定 CID 数 (案 E)

(`unified/v1106b/outputs/main/observation_1_smoke_per_seed_bin_counts.parquet`)

平均 28.4 CID/seed (目標 33)、不足は主に ghost mid/high。

### 2.2 ghost 合計 < 5 の seed (構造ラベル候補)

| seed | ghost_total | seed | ghost_total |
|---:|---:|---:|---:|
| 5 | 1 | 19 | 3 |
| 10 | 1 | 6 | 3 |
| 8 | 2 | 13 | 3 |
| 3 | 2 | 9 | 4 |
| 12 | 2 | 4 | 4 |
| 16 | 2 | 23 | 4 |
| 7 | 3 | (他) | |
| 2 | 3 | | |
| 15 | 3 | | |

→ **24 seeds 中 15 seeds で ghost 合計 < 5**。

### 2.3 ghost 希少性の構造事実

- ghost CID は per_seed 平均 4-6 個 (mid + high 合算)
- 一部 seed (5, 10) では ghost 合計 1 個のみ
- これは ESDE 内部の物理から自然に生じる ghost の希少性 (Taka 表現)
- **Phase Result 議題化候補**: 「ESDE の意識構造において ghost (消滅進行中) 状態は希少」

---

## 3. main run 観察時の構造ラベル方針 (Taka 指示反映)

観察 1/2 集計時に以下の構造ラベルを明示:

| ラベル | 適用条件 | 注意点 |
|---|---|---|
| `ghost_bin_low_n` | ghost mid または ghost high で per_seed n < 3 | 統計値の有意性に注意 |
| `seed_with_low_ghost_total` | seed 単位で ghost 合計 < 5 | 該当 15 seeds |
| `stuck_at_turn` | 同 CID 連続 K=3 検出 | smoke で 100%、turn 数を記録 |
| `oscillation_at_turn` | 直近 W=5 turn unique CID ≤ 2 | smoke で 100%、turn 数を記録 |
| `rollback_20pct` | min_fam < start_fam × 0.8 | familiarity 巻き戻り判定 |

---

## 4. Step P (1 事例) との対比

| 観察 | Step P (T0=116 cid=143) | Step C smoke (33 CID 平均) |
|---|---|---|
| start_fam | 116 | 115.45 |
| min_fam | 6.1 (T6) | 17.98 |
| rollback 率 | 100% (1 事例) | 75.8% (33 CID 集約) |
| stuck/oscillation | 反復停滞 + 離脱循環あり | 全 CID で検出 |

→ Step P 事例の現象は **構造特性として一般化**。ただし min_fam 6.1 は smoke 平均 18 より深い (Step P の特定 CID は特異深度)。

---

## 5. Code A から Web Claude / Taka への確認

| 項目 | Code A 提案 |
|---|---|
| smoke 結果妥当性 | rollback 75.8%、stuck/oscillation 100% は予想通りの構造観察 (Step P と整合) |
| Step D (main run、24 seeds × 681 CID × 15 turn = 10,215 turn) 進行 | 想定実行時間 5-10 分、Code A 自走 (Taka 指示) で進行 OK か |
| 構造ラベル方針 (§3) | 採用 OK か、追加ラベル必要か |
| ghost 希少性の Phase Result 議題化 | Taka 指示通り議題化候補として記録 OK |
| 観察 4 で stuck/oscillation 100% が見えた場合 | sampling モード (top-3) で多様性が出るか観察、Code A 予測 |

---

## 6. 想定される Step D-H の進行

| Step | 内容 | 想定時間 |
|---|---|---|
| D | 観察 1 main (24 seeds × 681 CID × 15 turn = 10,215 turn) | 5-10 分、Code A 自走 |
| E | 観察 2 (循環構造 attractor 検出) | 数秒 |
| F | 観察 3 (verification_a 高/低 cos_sim event 特性) | 数秒 |
| F.5 | 観察 4 実装方針報告 → Web Claude 確認 | 待ち |
| G | 観察 4 smoke (1 seed × 33 CID × 40 turn = 1,320 turn) | 2-5 分、pause |
| H | 観察 4 main (24 seeds × 681 CID × 40 turn = 27,240 turn) | 15-30 分、Code A 自走 |

---

## 7. 出力ファイル

| ファイル | 内容 |
|---|---|
| `unified/v1106b/outputs/main/observation_1_familiarity_trajectory_smoke.parquet` | 528 rows (33 CID × 16 turn) |
| `unified/v1106b/outputs/main/observation_1_smoke_per_seed_bin_counts.parquet` | seed × bin 別 CID 数 |

---

**Step C smoke 報告 end. Web Claude / Taka 確認後に Step D main run 進行。**
