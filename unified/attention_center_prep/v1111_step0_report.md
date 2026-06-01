# v1111 Step 0 — diff 法成立確認 報告

**Date**: 2026-06-01
**Author**: Code A
**Status**: Step 0 完了、**verdict = diff_method_valid** ✓、v1111 本実装に進める
**親**: Web Claude v1111 §4.1 (Step 0 で崩れたら先に進まない)

---

## 0. 出口

### **`diff_method_valid`** ✓

- 全 5 windows で **完全 bit-identical** (max_diff = 0.00e+00 全フィールド)
- → `injected - baseline` は注入だけの効果を分離する因果足跡として扱える
- → v1111 本実装 (diff トレース + reach 段階) に進める

---

## 1. 実行結果

### 1.1 設定 + 時間

- atom=42, center=99, other=100 (同 seed)
- WINDOWS=5, WINDOW_STEPS=100, N=5000
- baseline 2 回連続実行 (シングルプロセス、multiprocessing 不使用)
- 各 run ~591 秒 (起動 ~194s + 5 windows ~397s)
- 総時間 **1185 秒 (19.7 分)**

### 1.2 完全一致確認 (全 5 windows)

| 比較対象 | match | max_diff |
|---|---|---|
| E (5000 nodes) | True | **0.00e+00** |
| theta (5000 ndarray) | True | **0.00e+00** |
| alive_n (set) | True | diff_size=0 |
| alive_l (set) | True | diff_size=0 |
| S (link strength) | True | **0.00e+00** |
| labels.share | True | **0.00e+00** |
| labels.phase_sig | True | (keys match) |
| occupancy (64 bins) | True | **0.00e+00** |

→ **全 windows、全フィールドで完全 bit-identical**。浮動小数誤差すら出ない。

---

## 2. diff 法成立の根拠

Web Claude §1.1 の前提:
> 同 seed・同設定なら完全再現するからこそ injected − baseline が注入由来と読める

Step 0 で確認された:
1. **同 seed (42, 99, 100) で build_engine が同一 instance を再現** → 初期化決定的
2. **5 windows の step_window 後も全 state が一致** → 進化決定的
3. **VirtualLayerV9 (cog なし) の進化も決定的** → 仮想層も決定的

→ **injected と baseline の差分 = その 1 注入の効果に完全に帰属する**。
他の要素 (rng の揺らぎ、numpy 並列誤差等) は介入しない。

### 2.1 シングルプロセス + OMP_NUM_THREADS=1 の効果

- multiprocessing 不使用 = process fork の非決定性なし
- OMP/MKL/OPENBLAS thread=1 = numpy 内部の並列 reduction 順序の非決定性なし
- → 完全な再現性

---

## 3. 閾値規律遵守 (Web Claude §2.4)

| 隠れ閾値 | Step 0 で確認 | 結果 |
|---|---|---|
| Step 0 許容誤差 | bit-identical 期待 | **完全 0.00e+00** で達成 |
| ε (有意差分) | Δ ≠ 0 で集計 (ε 使わず) | Δ_baseline=0 が baseline 床 |
| reach 判定 | reach_other / reach_self > 1 | (本実装で適用) |

→ **固定数値完全ゼロ**を維持、Step 0 自身も固定値ゼロ判定。

---

## 4. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 + 物理切らない (stress=True) | ✓ |
| 書込 source_event 1 本 | ✓ (Step 0 は注入なしなので未使用) |
| トリガー固定しない | ✓ (Step 0 はセンター発火させず) |
| 定義しない / 判定置かない | ✓ |
| **閾値規律 (§2.4) 固定値ゼロ** | ✓ Step 0 で確認、本実装でも継承 |
| 単一 seed を絶対視しない | ✓ (本実装で 3 seeds 並行) |

---

## 5. v1111 本実装の根拠

Step 0 で diff 法が成立したので、Web Claude §4 やる順 2-5 に進める:

| 順 | 内容 | 次の Step |
|---|---|---|
| 2 | diff トレース機構を作る | Step 1 |
| 3 | 3 seeds 並行で 3 conditions (baseline/injected_self/injected_other) × 段階化 reach × k=1/3/5/10 | Step 1 |
| 4 | 他系注入だけが構造に沿って伸びるか / 出口まで届くか観察 | Step 2 |
| 5 | 24 seeds で再現 | Step 3 |

### 5.1 Step 1 設計案 (Code A)

- 注入 window: w_inject (例: w=2、ATTENTION 半減期 0.69w 超で適度な早期)
- 観察 window: w_inject + k for k in [1, 3, 5, 10]
- 総 windows: 12 (w_inject=2 + max_k=10)
- 3 conditions × 3 seeds = 9 並列タスク
- 推定時間: 各 ~30-35 分 (12 windows × 100 steps + 3 instance + inject overhead)、並列 9 で 35 分

### 5.2 Step 1 観察軸 (3 reach × 4 k × 3 conditions × 3 seeds)

- 空間 reach: ΔE node の BFS 距離分布 (注入 node から hop=0,1,2,3,...)
- 構造 reach: 同一/結合 CID 内の Δ エネルギー割合
- 出口 reach: 注入帯外 phase bin の Δocc 和
- 各 k window で測定 + 時間方向の旅程記録

---

## 6. 一文サマリ

v1111 Step 0 diff 法成立確認 (Code A、2026-06-01、Web Claude §4.1 「崩れたら先に進まない」) として、atom=42 center=99 other=100 で baseline 2 回連続実行 (シングルプロセス + OMP_NUM_THREADS=1) を 5 windows × 100 steps で実施し全 windows × 全フィールド (E 5000 nodes / theta 5000 ndarray / alive_n / alive_l / S link strength / labels.share / labels.phase_sig / occupancy 64 bins) で **max_diff = 0.00e+00 完全 bit-identical** 達成、出口 **`diff_method_valid`** ✓、injected − baseline はその 1 注入の効果に完全帰属、根拠 (build_engine 初期化決定的 + step_window 進化決定的 + VirtualLayerV9 仮想層も決定的、multiprocessing 不使用 + OMP/MKL/OPENBLAS thread=1 で並列 reduction 非決定性なし)、閾値規律 Step 0 許容誤差は完全 0.00e+00 で達成し固定値ゼロ維持、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない + 定義しない判定置かない + 閾値規律固定値ゼロ + 単一 seed 絶対視しない)、総時間 1185 秒 19.7 分、v1111 本実装に進める根拠成立で Step 1 (diff トレース + 3 conditions × 3 seeds × 段階化 reach × k=1/3/5/10) に進める、書込み unified/attention_center_prep/ 配下のみ。

---

**Step 0 end. verdict = diff_method_valid。v1111 本実装 (Step 1) に進む。**
