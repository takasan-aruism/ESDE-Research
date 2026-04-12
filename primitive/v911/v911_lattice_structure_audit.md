# v9.11 Lattice Structure Audit

> 目的: Pbirth 設計の基礎として、ESDE 物理層の空間構造を正確に把握する

---

## 1. 格子の形状

### 1.1 ノード数: N = 5000

```python
# autonomy/v82/esde_v82_engine.py:44
V82_N = 5000
```

### 1.2 格子サイズ: 71 × 71 (5041 スロット、末尾 41 は欠番)

```python
# primitive/v910/v910_pulse_model.py:166-177
def build_torus_substrate(N):
    side = int(math.ceil(math.sqrt(N)))   # ceil(sqrt(5000)) = 71
    adj = {}
    for i in range(N):
        r, c = i // side, i % side
        nbs = []
        nbs.append(((r - 1) % side) * side + c)
        nbs.append(((r + 1) % side) * side + c)
        nbs.append(r * side + ((c - 1) % side))
        nbs.append(r * side + ((c + 1) % side))
        adj[i] = [nb for nb in nbs if nb < N]
    return adj
```

- ノード i → 行 `r = i // 71`, 列 `c = i % 71`
- スロット 5000–5040 (行 70 の列 25–70) は `nb < N` フィルタで除外される
- **結果**: 最終行は 25 列しかない不完全行。行 70 のノードは上下方向ラップで
  行 0 のノード (列 0–24 のみ) と接続される

### 1.3 境界条件: トーラス (周期境界)

モジュロ演算 `(r - 1) % side`, `(c + 1) % side` 等により上下左右すべてラップする。
ただし `nb < N` フィルタにより、行 70 付近ではラップ先が存在しないケースがあり、
一部ノードは近傍 3 個になる。

**結論**: 概ねトーラスだが、N = 5000 は 71² = 5041 の完全正方でないため
端部に微小な非対称が存在する。6000 ノード版は確認できなかった。

---

## 2. 隣接関係

### 2.1 空間隣接: 4 近傍 (von Neumann)

上記コードで各ノードに対し上・下・左・右の 4 方向のみ追加。
8 近傍 (Moore) ではない。

### 2.2 リンク形成: 空間制約なし（任意ペア間）

```python
# ecology/engine/realization.py:63-82
# B. Realization — sample 3 candidates per node
k_samples = min(3, n_alive - 1)
alive_arr = np.array(alive_list)

for i in alive_list:
    candidates = state.rng.choice(alive_arr, size=k_samples + 1, replace=False)
    for j in candidates:
        j = int(j)
        if j == i:
            continue
        link_key = state.key(i, j)
        if link_key in state.alive_l:
            continue
        l_ij = state.get_latent(i, j)
        p_realize = p.p_link_birth * l_ij
        if state.rng.random() < p_realize:
            state.add_link(i, j, p.latent_to_active_threshold)
```

**重要な発見**: `rng.choice(alive_arr)` で全生存ノードから一様ランダムにサンプルする。
空間距離・トーラス隣接は参照されない。

→ リンクは格子上の任意の 2 ノード間に形成されうる（長距離リンクが支配的）。

### 2.3 二重トポロジー構造

ESDE は **2 つの隣接構造** を同時に保持する:

| 層 | 構造 | 用途 |
|---|---|---|
| 空間 (torus_sub) | 71×71 格子 4 近傍、固定 | `compute_spatial()` で field 拡張に使用 |
| リンク (alive_l) | 任意ペア、動的 | リンク強度 S, 抵抗 R, 島検出, label 形成 |

```python
# primitive/v910/v910_pulse_model.py:1070-1086
def compute_spatial(state, label, torus_sub, max_hops):
    core = frozenset(n for n in label["nodes"] if n in state.alive_n)
    # ... BFS on torus_sub (spatial grid) ...
```

```python
# primitive/v910/v910_pulse_model.py:1046-1051
def build_link_adj(state):
    adj = defaultdict(set)
    for lk in state.alive_l:
        adj[lk[0]].add(lk[1])
        adj[lk[1]].add(lk[0])
    return adj
```

---

## 3. リンク密度 ρ の実測

### 3.1 全ステップ平均

| データセット | 平均リンク数 | σ | min | max | ρ |
|---|---|---|---|---|---|
| long run (5 seeds × 50 windows) | 2721.1 | 120.8 | 2425 | 2982 | 2.18 × 10⁻⁴ |
| short run (48 seeds × 10 windows) | 2872.9 | 62.3 | — | — | 2.30 × 10⁻⁴ |

ρ = links / (N(N-1)/2) = 2721 / 12,497,500 ≈ **0.022%**

→ 極度にスパースなネットワーク。各ノードの平均次数 ≈ 2 × 2721 / 5000 ≈ **1.09**。

### 3.2 Birth 近傍のリンク密度

per_window CSV の `links` 列を label birth window と対照:

| seed | birth-window 平均 links | 全体平均 links | 差 |
|---|---|---|---|
| 0 | 2721.5 | 2731.6 | −10.1 |
| 1 | 2750.8 | 2743.3 | +7.5 |
| 2 | 2713.9 | 2703.7 | +10.2 |
| 3 | 2729.1 | 2721.7 | +7.4 |
| 4 | 2731.6 | 2705.0 | +26.6 |

**結論**: birth 近傍のリンク密度に有意な偏りは見られない。
birth はリンク密度の変動とは独立に起きている。

---

## 4. Label の空間構造

### 4.1 label ノードの由来

Label の `nodes` は以下のいずれかから生成される:

1. **島 (island)**: `find_islands_sets()` が返す S ≥ 0.20 のリンクで接続された連結成分 (size ≥ 3)
2. **R > 0 リンクペア**: 抵抗値が正のリンクの両端ノード (size = 2)

```python
# primitive/v910/virtual_layer_v9.py:501-520
if islands:
    for iid, info in islands.items():
        nodes = frozenset(info.nodes)
        if len(nodes) >= 2:
            cluster_list.append(nodes)

for lk in state.alive_l:
    r = state.R.get(lk, 0.0)
    if r > 0:
        pair = frozenset(lk)
        cluster_list.append(pair)
```

### 4.2 ポリオミノではない

**核心的な発見**: label のノード集合は **リンク接続** で定義されており、
**空間隣接 (torus_sub)** は参照されない。

リンクは `rng.choice(alive_arr)` で形成されるため、label のコアノードは
71×71 格子上に **散在** する。例えば n_core=3 のラベルの 3 ノードが
(行 5, 列 12), (行 42, 列 67), (行 18, 列 3) のように配置されうる。

→ ポリオミノ (格子上の連結タイル) という概念は **ESDE の label には適用できない**。

### 4.3 n_core の分布

#### Long run (5 seeds, 1121 labels)

| n_core | count | 比率 |
|---|---|---|
| 2 | 860 | 76.7% |
| 3 | 59 | 5.3% |
| 4 | 77 | 6.9% |
| 5 | 125 | 11.2% |

#### Short run (48 seeds, 3165 labels)

| n_core | count | 比率 |
|---|---|---|
| 1 | 1 | 0.0% |
| 2 | 2123 | 67.1% |
| 3 | 235 | 7.4% |
| 4 | 287 | 9.1% |
| 5 | 515 | 16.3% |
| 6 | 1 | 0.0% |
| 7 | 2 | 0.1% |
| 8 | 1 | 0.0% |

**支配的パターン**: n_core = 2 が 67–77% を占める (R > 0 リンクペア由来)。
n_core ≥ 3 は島由来で、n_core = 5 が n_core = 3,4 より多い
(島サイズ ≥ 3 から入るが、5 ノード程度の島が安定しやすい模様)。

### 4.4 理論上の種類数 vs 実測

ポリオミノの概念が適用できないため、「形の種類」は格子上の幾何ではなく
**リンクトポロジー上の連結グラフの形** として考える必要がある。

| n_core | ポリオミノ種類数 (参考) | 実際の構造 |
|---|---|---|
| 2 | 1 (ドミノ) | リンク 1 本で結ばれた 2 ノード。格子上の距離は任意 |
| 3 | 2 (トリオミノ) | S ≥ 0.20 リンクの連結成分。パス or 三角形 |
| 4 | 5 (テトロミノ) | 連結グラフ。パス, スター, サイクル, etc. |
| 5 | 12 (ペントミノ) | 連結グラフ。多数の形が可能 |

ただし ESDE の島は強リンクの連結成分なので、実際にどのグラフ形状が
実現されているかはリンクトポロジーのログがないと特定できない
(現在の CSV には n_core のみ記録、ノード座標やリンク構造は未記録)。

---

## 5. Pbirth 設計へのインプリケーション

### 5.1 「空間」の二重性を意識する

Pbirth が「近傍のリンク密度」に依存する場合:
- **空間近傍** (torus 4-neighbor) を使うか
- **リンク近傍** (alive_l の隣接) を使うか

で意味が全く異なる。`compute_spatial()` はトーラスを使い、
label の birth 自体はリンクトポロジーに依存する。

### 5.2 リンク密度は一様に低い

ρ ≈ 0.022%、平均次数 ≈ 1.09。birth 時に特異的なリンク密度上昇はない。
Pbirth をリンク密度に条件付ける場合、グローバル ρ ではなく
**局所 ρ** (特定ノード周辺のリンク数) が必要。

### 5.3 n_core = 2 が支配的

label の 3/4 は 2 ノードペア。Pbirth モデルが n_core に依存する場合、
n_core = 2 のケースを主軸に設計し、n_core ≥ 3 を拡張として扱うのが妥当。

### 5.4 ノード座標は散在

n_core ≥ 3 の label コアノードは格子上で隣接している保証がない。
「空間的なコンパクトさ」を Pbirth の因子にする場合、
コアノード間の格子距離 (Manhattan or torus shortest path) を
明示的に計算する必要がある。

---

## Appendix: コード参照一覧

| 項目 | ファイル | 行 |
|---|---|---|
| V82_N = 5000 | `autonomy/v82/esde_v82_engine.py` | 44 |
| build_torus_substrate | `primitive/v910/v910_pulse_model.py` | 166–177 |
| RealizationOperator.step | `ecology/engine/realization.py` | 38–84 |
| find_islands_sets | `ecology/engine/intrusion.py` | 22–40 |
| VirtualLayerV9.step (label birth) | `primitive/v910/virtual_layer_v9.py` | 470–567 |
| compute_spatial (BFS on torus) | `primitive/v910/v910_pulse_model.py` | 1070–1086 |
| build_link_adj | `primitive/v910/v910_pulse_model.py` | 1046–1051 |
| n_core 定義 | `primitive/v910/v910_pulse_model.py` | 1195–1196 |
| per_window CSV (links 列) | `diag_v910_pulse_long/aggregates/per_window_seed*.csv` | — |
| per_label CSV (n_core 列) | `diag_v910_pulse_long/labels/per_label_seed*.csv` | — |
