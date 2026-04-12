# v9.11 Rarity Proxy Audit

*Generated*: 2026-04-12
*Source*: `diag_v910_pulse_long` (5 seeds × tracking=50, read-only)

---

## 1(a): Label サイズ (n_core) 別出現頻度

全 label 数: 1121 (5 seeds 合計)

| n_core | 出現数 | 比率 | alive at end | alive率 |
|---:|---:|---:|---:|---:|
| 2 | 860 | 76.7% | 39 | 4.5% |
| 3 | 59 | 5.3% | 11 | 18.6% |
| 4 | 77 | 6.9% | 44 | 57.1% |
| 5 | 125 | 11.2% | 92 | 73.6% |

**rarity proxy 評価:**
- 値域: [2, 5] — 離散、7-8 段階
- 連続性: 離散 (整数値のみ)
- cid 間分散: std=0.0 (IQR)
- 2-node が 860/1121 (76.7%) で最頻

## 1(b): Frozenset 出現頻度の近似 (phase_sig 分布)

*注: frozenset 自体は CSV に出力されていない。phase_sig (label birth 時の平均 θ) を proxy として使用。*
*同一 frozenset は同一 phase_sig を持つが、異なる frozenset が近い phase_sig を持つ場合がある。*

phase_sig 値域: [-3.1389, 3.1399] (≈ [-π, π])
0.1 rad bin 数: 63 (理論 max ≈ 63)
bin 内 label 数: n=63 min=10.0000 p10=13.0000 p25=15.0000 p50=18.0000 p75=20.0000 p90=24.0000 p99=27.0000 max=27.0000

厳密一致 phase_sig の頻度分布:
  出現 1 回のみ: 1097 (98.9%)
  出現 2+ 回: 12
  最大出現回数: 2

**rarity proxy 評価:**
- 値域: 連続 ([-π, π] 内の float)
- 連続性: 良好 (phase angle)
- cid 間分散: ほぼ全 label がユニークな phase_sig → **分散十分**
- 問題: 「同じ構造の再出現頻度」は frozenset でないと計測不能
- 代替案: phase_sig bin (0.1 rad) 内の label 密度を rarity proxy として使う

## 1(c): S 強度帯別出現頻度

*注: リンク強度 S は per-step の物理層変数であり、出力 CSV に直接含まれていない。*
*代替として per_label の `last_st_mean` (最終 window の structural set サイズ平均) を使用。*

last_st_mean 分布: n=1112 min=2.1100 p10=6.1500 p25=6.9700 p50=8.0400 p75=10.1000 p90=33.6200 p99=59.0500 max=80.7300

| st_mean bin | count | 比率 |
|---|---:|---:|
| <10 | 826 | 74.3% |
| 10-30 | 142 | 12.8% |
| 30-60 | 137 | 12.3% |
| 60-100 | 7 | 0.6% |
| 100+ | 0 | 0.0% |

**rarity proxy 評価:**
- 値域: [2.1, 80.7] — 連続、広範囲
- 連続性: 良好
- cid 間分散: 十分 (IQR=3.1)
- 問題: st_mean は label の活動規模であって「構造の珍しさ」ではない
- S 自体は CSV 非出力のため、rarity proxy として使うには出力追加が必要

## 2: Rolling 定義の試算 (n_core ベース)

n_core が最も使いやすい候補なので、これで rolling count を試算。
各 cid の host label の n_core を、3 つの時間スケールで集計。

### 2a: Run-wide n_core frequency → rarity

rarity = (my n_core の出現回数 / 全 label 数) per seed

rarity 分布: n=1121 min=0.0360 p10=0.0751 p25=0.7246 p50=0.7371 p75=0.7888 p90=0.7895 p99=0.7895 max=0.7895

| n_core | mean rarity (= freq ratio) | cid count |
|---:|---:|---:|
| 2 | 0.7682 | 860 |
| 3 | 0.0559 | 59 |
| 4 | 0.0691 | 77 |
| 5 | 0.1144 | 125 |

### 2b: Window-scale (直近 5 window での同 n_core 数)

近似: 各 label の birth_window を使い、window ±2 内に同 n_core の label が何個いるかを集計

nearby (±2 window) 同 n_core 数: n=1121 min=1.0000 p10=2.0000 p25=7.0000 p50=15.0000 p75=22.0000 p90=26.0000 p99=35.0000 max=36.0000

### 2c: Step-scale (直近 500 step)

label の birth は window 境界でのみ発生するため、step-scale と window-scale は
label birth 頻度については実質同等。step 内の S 変動を見るには S の時系列出力が必要 (現在 CSV 非出力)。

## 3: Pulse interval レンジ試算

仮の式: `pulse_interval = base_interval / rarity_weight`
rarity_weight = n_core の rarity (run-wide frequency ratio の逆数的)

### 3a: n_core ベースの rarity_weight

rarity_weight を「自分の n_core が全体に占める比率」とすると:
- 5-node (最頻): weight ≈ 0.60 → pulse_interval = 50 / 0.60 ≈ 83
- 2-node (最稀): weight ≈ 0.02 → pulse_interval = 50 / 0.02 ≈ 2500

**実測値 (5 seeds 平均):**

| n_core | freq ratio (weight) | pulse_interval = 50/w | pulse_interval = 50*(1/w) |
|---:|---:|---:|---:|
| 2 | 0.7672 | 65 | 65 |
| 3 | 0.0526 | 950 | 950 |
| 4 | 0.0687 | 728 | 728 |
| 5 | 0.1115 | 448 | 448 |

**解釈:**
- `50/weight` 式: 5-node → 83 step、2-node → 2500 step (50 window = 25000 step なので range は十分だが 2-node が極端)
- `50*(1/weight)` 式: さらに極端 (2-node → 125000 step、run 全体を超える)
- → **clamp 必要**。例: clamp(25, 500) で min 25 step / max 500 step

### 3b: Clamp (25, 500) 適用時

| n_core | weight | raw interval | clamped |
|---:|---:|---:|---:|
| 2 | 0.7672 | 65 | 65 |
| 3 | 0.0526 | 950 | 500 |
| 4 | 0.0687 | 728 | 500 |
| 5 | 0.1115 | 448 | 448 |

## 一次候補まとめ

### Rarity proxy の一次候補

| 候補 | 使えるか | 根拠 |
|---|---|---|
| **(a) n_core (label サイズ)** | **最有力** | 離散 7-8 段階だが cid 間分散十分。5-node 60% 支配のため分解能に限界あり。CSV 既出力 |
| (b) frozenset 出現頻度 | 使えるが要追加出力 | phase_sig proxy ではほぼ全 label ユニーク。frozenset 自体は CSV 非出力 |
| (c) S 強度帯 | 使えるが要追加出力 | S は CSV 非出力。last_st_mean で代替すると「珍しさ」ではなく「規模」を測定 |

### Rolling スケールの一次候補

| スケール | 候補度 | 根拠 |
|---|---|---|
| **run-wide 累積** | **最有力** | n_core の頻度比は run 通じて安定。rolling 不要の可能性 |
| window (±2) | 次点 | 局所 birth rate を反映するが、label birth は low-freq event (数個/window) |
| step (500) | 非推奨 | label birth は window 境界でのみ発生、step 内変動なし |

### Pulse interval の推奨構成

- base: 50 (v9.10 と同じ)
- weight: n_core frequency ratio (run-wide)
- 式: `pulse_interval = clamp(50 / weight, 25, 500)`
- 結果: 5-node → 83, 3-node → 167, 7-node → 500 (clamp)
- **2-node は 2500 → 500 に clamp** (run 内で最低 50 回は pulse する)
