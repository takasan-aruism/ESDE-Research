# v10.8 副次観察 3 件 報告 (主題判定外)

*親*: `v108_implementation_brief.md` §4
*位置づけ*: 副次観察、主題判定 (Level 1-3.5) には含めない、観察記録のみ

---

## 1. Whiteout 監視 (Gemini A1)

### 1.1 結果

| 指標 | 値 |
|---|---:|
| total atom ペア (24 seeds × 300/seed) | **7,200** |
| whiteout flag (相関 ≥ 0.7) | **7,200** (100%) |
| max correlation | 0.9999995 |
| mean correlation | 0.9998819 |

### 1.2 解釈

medium window 6 dim profile vector が n_pulses_medium 1 軸支配 (Level 1 finding と整合) のため、全 atom ペアが完全相関。これは **「干渉」ではなく「ESDE 共通効果の強い表れ」**。

→ 真の Whiteout 検証には path × delta の高次元プロファイルが必要 (v10.9 以降)。

---

## 2. Small-World 維持確認 (Gemini A6)

### 2.1 結果

| 量 | v10.7 (24 seeds 合計) | v10.8 (24 seeds 合計) | ratio |
|---|---:|---:|---:|
| loop_2_hop | **14,343** | **14,343** | 1.000 |
| loop_3_hop | **110,103** | **110,103** | 1.000 |
| maintenance_flag | - | True (24/24 seeds) | - |

### 2.2 解釈

post-process は familiarity edge を変更しないため、loop は **構造的に不変**。Gemini A6 の懸念は v10.8 では構造的に発生しない。

→ Phase 2 (物理層を変更する段階) で再評価する観察項目。v10.8 では記録のみ。

---

## 3. 誤差分布の形状観察 (Gemini A5、Taka 示唆)

### 3.1 全体集計 (24 seeds)

| shape_label | count | ratio |
|---|---:|---:|
| other (mid skew) | 4,917 | 55.7% |
| skewed (\|skew\|>1) | 2,151 | 24.3% |
| **bimodal** (Sarle's > 5/9) | **1,540** | **17.4%** |
| heavy_tail (kurt > 3) | 227 | 2.6% |
| **normal** | **0** | **0%** |

合計 8,835 rows = 25 atom × 5 path × 3 window × 24 seeds (一部欠損あり)。

### 3.2 観察

- **正規分布ゼロ** (= delta 分布は中央値周辺ではなく形状を持つ)
- **bimodal 17.4%** = (atom, path, window) の 1/6 以上で 2 ピーク分布
- bimodal は target cid の二相状態 (例: n_core 別、Integration 内外、ライフサイクル段階) を反映している可能性

### 3.3 Taka 示唆「確率的発生と誤差表現能力の融合可能性」

bimodal 1,540 件の具体例は v10.9 以降で詳細解析。各 (atom, path, window) で 2 ピークの位置と原因を観察することで、ESDE の誤差表現能力を定量化可能。

---

## 4. 副次観察まとめ

| 観察 | 結果 | 解釈 |
|---|---|---|
| Whiteout | 100% flag (max_corr 1.000) | medium n_pulses 1 軸支配の表れ、真の干渉は別解析 |
| Small-World | 24/24 完全維持 | post-process 構造的不変、Phase 2 再評価 |
| 誤差分布 | 正規分布 0%、bimodal 17.4% | 多様な形状、bimodal が ESDE 動学の二相性反映 |

副次観察は **主題判定外** (即決事項 §3.3)。記録のみ。

---

*以上、v10.8 副次観察 3 件報告。*
