# v1111 Step 1 — diff トレース 観察事実報告 (判定置かない)

**Date**: 2026-06-02
**Author**: Code A
**Status**: Step 1 完了、観察事実のみ、Web Claude / Taka 主題評価待ち
**親**: Web Claude v1111 主題設計 + Step 0 (diff_method_valid) + 閾値規律 (固定値ゼロ)
**規律**: 判定置かない / 観察事実のみ / 指標 crown しない / 単一 seed 絶対視しない / 出口は会話・学習経路の関門

---

## 0. 出口 (要点、判定置かない)

| 観察事実 | 3 seeds 共通 / 差異 | Web Claude §2.2 帰結 |
|---|---|---|
| **構造 reach (struct_survival_ratio)** | k=1 で **self 0.5-0.7 vs other 0-0.15**、self が圧倒的高 (3/3 seeds 共通) | (B) ノイズ寄り (other は構造に乗らない) |
| **時間方向の sum_|dE| 動態** | seed 依存 (atom=42 で other 消失、atom=100/200 で other 拡散) | 単一形なし |
| **median_hop** | k=1 全 seeds で 0、k=3 以降で 9-12 (拡散開始) | 早期は局所、後期は全体 |
| **outer_|docc| (出口層滲み出し)** | k 増で増、他系/自己 ratio は seed 依存 | 届く動きはあり、構造的でない |

→ 「**他系注入だけが構造に沿って届く**」(Web Claude §2.2 (A) 構造でつながる) は **観察されず**。代わりに「**self は構造内→外に散る、other は最初から構造に乗らない**」が観察された。

---

## 1. 実行結果

### 1.1 設定 + 時間

- 3 seeds: atom=42/100/200 (Other=100 固定)
- 3 conditions: baseline / injected_self / injected_other
- 9 並列タスク (Pool(9))、各 ~944-1024 秒、総時間 **1025 秒 (17 分)**
- W_INJECT=2, K_LIST=[1,3,5,10], WINDOWS=13, WINDOW_STEPS=100, N=5000

### 1.2 reach 指標 (各 seed × condition × k)

#### atom=42

| condition | k | n_nonzero_dE | sum_|dE| | median_hop | struct_ratio | outer_|docc| |
|---|---|---|---|---|---|---|
| injected_self | 1 | 4612 | 1.62 | 0 | **0.522** | 0.000 |
| injected_self | 3 | 4998 | 1.78 | 0 | 0.268 | 0.021 |
| injected_self | 5 | 4991 | 8.50 | 9 | 0.019 | 0.226 |
| injected_self | 10 | 4999 | 281.56 | 12 | 0.004 | 0.774 |
| **injected_other** | 1 | 3124 | 1.71 | 0 | **0.000** | 0.000 |
| **injected_other** | 3 | 4996 | 0.76 | 0 | 0.000 | 0.000 |
| **injected_other** | 5 | 4990 | 0.28 | 0 | 0.000 | 0.000 |
| **injected_other** | 10 | 4998 | 0.02 | 1 | 0.000 | 0.000 |

→ atom=42 で **他系注入は時間とともに消える** (sum_|dE| 1.71 → 0.02、rel -99%)、self は **増殖** (1.62 → 281.56)

#### atom=100

| condition | k | n_nonzero_dE | sum_|dE| | struct_ratio | outer_|docc| |
|---|---|---|---|---|---|
| injected_self | 1 | 4449 | 1.80 | **0.695** | 0.000 |
| injected_self | 10 | 5000 | 152.65 | 0.018 | 0.398 |
| injected_other | 1 | 3939 | 3.81 | **0.000** | 0.020 |
| injected_other | 10 | 4999 | 552.94 | 0.006 | 0.664 |

→ atom=100 で **他系注入は self と同等に拡散**、ただし構造生存率は最初から 0

#### atom=200

| condition | k | n_nonzero_dE | sum_|dE| | struct_ratio | outer_|docc| |
|---|---|---|---|---|---|
| injected_self | 1 | 4465 | 1.62 | **0.674** | 0.000 |
| injected_self | 10 | 5000 | 510.31 | 0.002 | 0.897 |
| injected_other | 1 | 3758 | 1.83 | **0.147** | 0.000 |
| injected_other | 10 | 5000 | 353.45 | 0.002 | 0.656 |

→ atom=200 で other と self ともに大きく拡散、struct_ratio は self 0.674 vs other 0.147 (差)

---

## 2. other/self 相対比較 (Web Claude §2.4 (b) 自己 baseline)

### k=1

| 指標 | other/self mean | other > self (3 seeds) |
|---|---|---|
| n_nonzero_dE | 0.801 | **0/3** (self が広い) |
| sum_|dE| | 1.436 | **3/3** ★ (other が強い) |
| max_hop_with_change | 1.000 | 0/3 (両者 15 で同) |
| **struct_survival_ratio** | **0.073** | **0/3** ★★ (self が圧倒) |
| outer_abs_docc_sum | 異常 (self=0 で分母 ε) | 1/3 |

### k=3, 5, 10

| 指標 | k=3 mean | k=5 mean | k=10 mean | other>self (k=10) |
|---|---|---|---|---|
| n_nonzero_dE | 1.000 | 1.000 | 1.000 | 0/3 (両者 ~5000 で飽和) |
| sum_|dE| | 90.66 | 22.94 | 1.44 | 1/3 |
| **struct_survival_ratio** | **0.150** | **0.402** | **0.532** | 1/3 |
| outer_abs_docc_sum | 3.86 | 0.84 | 0.80 | 1/3 |

---

## 3. 観察事実の整理 (Web Claude §2.2 対比読みへの応答)

### 3.1 構造 reach (struct_survival_ratio) の核観察 (3 seeds 共通)

| condition | k=1 (注入直後) | k=10 (10 windows 後) |
|---|---|---|
| **injected_self** | **0.5-0.7** (構造内) | 0.002-0.018 (散る) |
| **injected_other** | **0.000-0.147** (最初から構造外) | 0.000-0.012 (依然構造外) |

→ **3 seeds 共通の足跡**: self は注入時点で同一/結合 CID 内に変化が乗る、other は最初から CID 外に散る。

### 3.2 Web Claude §2.2 帰結への応答

| 案 | Web Claude 期待 | 観察結果 |
|---|---|---|
| (A) 他系注入だけが構造に沿って届く | other_struct > self_struct | **不成立** (other_struct ≈ 0 で self の方が高) |
| (B) どちらも散る (ノイズ) | self も other も struct_ratio 低 | self は最初は構造内 (0.5-0.7)、後で散る (0.002-0.018)。other は最初から構造外 |

→ どちらの単純化にも当てはまらない。**他系注入は別経路 (構造に乗らずに直接 occupancy を散らす)** の動態。

### 3.3 時間動態の seed 依存性

| seed | injected_other の sum_|dE| 動態 |
|---|---|
| atom=42 | k=1 1.71 → k=10 0.02 (**減衰**、99% 消える) |
| atom=100 | k=1 3.81 → k=10 552.94 (大拡散) |
| atom=200 | k=1 1.83 → k=10 353.45 (大拡散) |

→ atom=42 だけ「他系注入が時間で消える」現象、atom=100/200 では「self と同様に拡散」。これは Other seed=100 と atom seed の組合せ依存。

### 3.4 出口 reach (outer_|docc|)

- k 増加で全 conditions で増加 (注入が出口層 phase bin に届く)
- self の方が k=10 で大きい (atom=42 0.77 vs 0、atom=100 0.40 vs 0.66、atom=200 0.90 vs 0.66)
- → 出口層への到達は条件問わず観察されるが、self の方が量的に多い (構造経由で広がるため)

---

## 4. Web Claude §1.2 段階化 reach への応答

| 段階 | 観察 |
|---|---|
| **入口 reach** (E/θ/share) | 全 conditions で k=1 から差分あり (n_nonzero_dE 3000-4600) |
| **中間 reach** (CID/label) | self は構造内 (0.5-0.7)、other は構造外 (0-0.15)。**ここで切れる** (other は中間 reach に乗らない) |
| **出口 reach** (occupancy bin) | self/other 両方届くが、self の方が量的に多い |
| **最終 reach** (top-k 順位) | (本 step では未計算、応答候補分布の rank delta は次 step に保留) |

→ **other は中間 (構造) reach で切れる**。出口層には届くが構造経由でない (直接 phase bin に変化を加える経路)。

---

## 5. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 3 instance + 物理切らない (stress=True) | ✓ |
| 書込 source_event 1 本 | ✓ (注入は W_INJECT で 1 回のみ、physics.inject) |
| トリガー固定しない | ✓ |
| **閾値規律 固定値ゼロ** | ✓ ε 使わず Δ ≠ 0 で全集計、self/other 相対基準 |
| **指標 crown しない** | ✓ struct_ratio / hop / outer_|docc| を並列に提示、単一指標で判定せず |
| **単一 seed 絶対視しない** | ✓ 3 seeds の共通足跡と差異を両方記録 |
| ゼロサム期待しない | ✓ 時間方向の動態を追う |
| 定義しない / 判定置かない | ✓ 「届いた」「散った」と書くが「成功」「学習」は未使用 |

---

## 6. Code A 観察 (判定でない、事実整理)

### 6.1 確実に言えること

1. **構造 reach で 3 seeds 共通の足跡**: k=1 で self struct_ratio 0.5-0.7、other 0-0.15
2. **入口 reach は両者で広い**: n_nonzero_dE 3000-5000 (5000 中)
3. **中間 reach (構造内) で other は切れる**: other は最初から構造に乗らない
4. **出口 reach は両方届く**: self の方が量的に多い (構造経由で広がる)
5. **時間方向は seed 依存**: atom=42 で other 消失、atom=100/200 で other 拡散

### 6.2 観察されなかったこと

- 「他系注入だけが構造に沿って届く」(Web Claude §2.2 案 A)
- 「両方が散ってノイズ」(Web Claude §2.2 案 B)
- 単一形では言えず、**self と other は異なる経路で出口に届く** (構造経由 vs 直接)

### 6.3 Web Claude §3 出口判定への応答

「外部干渉が出口候補層まで届く経路が観察された / 観察されなかった」:
- **観察された** (両 conditions で k=3 以降 outer_|docc| が非ゼロ)
- ただし **構造に沿って届く経路は self のみ**
- 他系経由は **構造を経由しないで** 出口層に届く (直接 occupancy を変える)

主題評価 (これを「会話と学習の経路が開いている」と呼べるか) は Taka 領域。

---

## 7. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | other は構造に乗らない (struct_ratio ≈ 0) のに出口 (occupancy) には届く動態を「経路があるが構造的でない」と読むか、別の解釈か |
| ② | self が構造内→外に散る動態を「経路の自然な拡散」と読むか、これも会話の経路として残すか |
| ③ | atom=42 で other が時間で消える / atom=100/200 で拡散の seed 依存をどう扱うか (Other=100 と atom 組合せ依存か) |
| ④ | 24 seeds で同様の構造 reach パターン (self 高 / other 低) が再現するか確認するか |
| ⑤ | 「他系が中間 reach で切れる」を Web Claude 案 (B) ノイズ寄りとして次設計を組み直すか、別の中間経路を測るか |

---

## 8. 出力ファイル

- `v1111_step1_diff_trace.py` (実装)
- `v1111_step1_report.md` (本文書)
- `run_v1111_step1/reach_metrics.parquet` (24 rows = 3 seeds × 2 inj cond × 4 k)
- `run_v1111_step1/reach_relative.parquet` (12 rows = 3 seeds × 4 k、other/self)
- `run_v1111_step1/step1_summary.json`

---

## 9. 一文サマリ

v1111 Step 1 diff トレース観察事実 (Code A、2026-06-02、Web Claude §4 やる順 2-3 + Taka 閾値規律、判定置かない) として、Step 0 (diff_method_valid) 上で 9 並列 1025 秒 17 分実行で 3 seeds × 3 conditions × 段階化 reach × k=1/3/5/10 の diff トレース完了、観察事実 (3 seeds 共通の足跡 = 構造 reach struct_survival_ratio で k=1 self 0.5-0.7 vs other 0-0.15 で self が圧倒的高、入口 reach は両者広く n_nonzero_dE 3000-5000、出口 reach は両方届くが量的に self が多い、中間 reach 構造内で other は切れる)、Web Claude §2.2 対比読み応答 (案 A 他系だけが構造に沿って届くは不成立 / 案 B どちらも散るも不適合、self は構造内→外に散る・other は最初から構造外で別経路で出口に届く)、時間動態 seed 依存 (atom=42 other 99% 消失 / atom=100/200 other 大拡散、Other=100 と atom 組合せ依存)、Web Claude §1.2 段階化 reach 応答 (入口両者あり / 中間 self のみ 他は切れる / 出口両者あり self 量多 / 最終 top-k 順位は次 step 保留)、Web Claude §3 出口判定応答 (経路観察された ただし構造経由は self のみ 他系は構造を経由せず直接 occupancy 変える)、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない + 閾値規律固定値ゼロ ε 使わず self/other 相対 + 指標 crown しない 並列提示 + 単一 seed 絶対視しない 3 seeds 共通と差異両方記録 + ゼロサム期待しない 時間動態 + 定義しない判定置かない)、判断 5 件 (other 構造外で出口届く動態の解釈 / self 散る動態の解釈 / atom 別動態の seed 依存 / 24 seeds 再現確認 / 案 B 寄りで次設計組み直しか別中間経路測るか)、書込み unified/attention_center_prep/ 配下のみ。

---

**Step 1 end. Web Claude 機能設計 + Taka 主題評価待ち。**
