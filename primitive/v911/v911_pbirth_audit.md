# v9.11 Pbirth (birth-rarity proxy) Audit

*Generated*: 2026-04-12
*Source*: `diag_v910_pulse_long` (5 seeds × tracking=50, read-only)
*命名規律*: 「Pbirth」は正式名称ではなく **birth-rarity proxy** として扱う (GPT 監査)

---

## 3.1 Label birth 本来の条件 (コード引用)

**重要発見**: 指示書の「3 条件 AND (S + E + cos Δθ)」は Genesis の化学反応条件であり、
**label birth 条件とは異なる**。label birth は以下 2 経路:

### 経路 A: Island 検出 (n_core ≥ 3)
`ecology/engine/intrusion.py:23-41`, `autonomy/v82/esde_v82_engine.py:231`
```python
# esde_v82_engine.py 行 231:
isl_m = find_islands_sets(self.state, 0.20)

# intrusion.py 行 23-41:
def find_islands_sets(state, s_thr=0.30):
    # Connected components on edge subgraph S >= s_thr, size >= 3
    adj = defaultdict(set)
    for k in state.alive_l:
        if state.S[k] >= s_thr:  # ★ S 閾値 = 0.20 (呼び出し側で指定)
            adj[k[0]].add(k[1]); adj[k[1]].add(k[0])
    # BFS connected components, size >= 3
```
→ **S ≥ 0.20 のリンクで連結されたノード群、サイズ ≥ 3**

### 経路 B: R > 0 ペア (n_core = 2)
`virtual_layer_v9.py:512-518`
```python
for lk in state.alive_l:
    r = state.R.get(lk, 0.0)
    if r > 0:  # ★ R > 0 = 閉路参加
        pair = frozenset(lk)
        if pair not in self.recurrence:
            cluster_list.append(pair)
```
→ **R > 0 (共鳴正、閉路に参加) のリンクの 2 端点**

### 共通フィルタ
```python
# virtual_layer_v9.py:539-546
for cluster_nodes in cluster_list:
    # 既存 label と 50% 以上重複 → 棄却
    for label in self.labels.values():
        overlap = label['nodes'] & cluster_nodes
        if len(overlap) > len(cluster_nodes) * 0.5:
            already_labeled = True
```

**まとめ**: label birth = (S ≥ 0.20 island ∪ R > 0 pair) − 既存 label 50%+ overlap
E 閾値・cos(Δθ) 閾値は label birth に直接関与しない。

## 3.2 Pbirth 算出手順

**制約**: S/R の per-step 時系列は CSV 非出力。retroactive な micro-level Pbirth は不可。
**近似**: 同一 n_core の label birth が lookback window 内に何回発生したかを macro proxy とする。

```
count = (bw - Nlookback, bw) の間に同 n_core で born した label 数
Pbirth = (count + 1) / (Nlookback + 1)    # Laplace 平滑化
I = -log10(Pbirth)
```

*注: これは「この n_core サイズの label がどれくらい頻繁に生まれるか」の proxy。
frozenset-specific ではなく n_core-specific。*

## 3.3 Pbirth と I の分布 (Nlookback=10)

全 label: 1121

**Pbirth**: n=1121 min=0.0909 p10=0.2727 p25=0.4545 p50=2.3636 p75=3.0909 p90=3.7273 max=4.9091
**I = -log10(Pbirth)**: n=1121 min=-0.6910 p10=-0.5714 p25=-0.4901 p50=-0.3736 p75=0.3424 p90=0.5643 max=1.0414

### n_core 別

| n_core | n | Pbirth p10 | Pbirth p50 | Pbirth p90 | I p10 | I p50 | I p90 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 860 | 1.2727 | 2.7273 | 4.0000 | -0.6021 | -0.4357 | -0.1047 |
| 3 | 59 | 0.0909 | 0.1818 | 0.4545 | 0.3424 | 0.7404 | 1.0414 |
| 4 | 77 | 0.0909 | 0.2727 | 0.4545 | 0.3424 | 0.5643 | 1.0414 |
| 5 | 125 | 0.1818 | 0.3636 | 0.6364 | 0.1963 | 0.4393 | 0.7404 |

## 3.4 Pulse Interval 試算

式: `pulse_interval = 50 / (1 + alpha * I)`

| alpha | PI p10 | PI p25 | PI p50 | PI p75 | PI p90 | PI min | PI max | ratio p90/p10 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 32.0 | 37.2 | 79.8 | 98.1 | 116.7 | 24.5 | 161.8 | 3.65 |
| 2 | -651.2 | 16.2 | 32.8 | 227.2 | 689.8 | -9344.5 | 2521.7 | inf |
| 5 | -72.0 | -42.4 | -30.6 | 13.1 | 18.4 | -267.7 | 913.8 | inf |
| 10 | -22.7 | -16.4 | -11.7 | 5.9 | 9.3 | -1055.9 | 182.2 | inf |

### Clamp(10, 200) 適用時 (alpha=5)

raw:    n=1121 min=-267.6594 p10=-72.0365 p25=-42.4217 p50=-30.5989 p75=13.0844 p90=18.4358 max=913.7624
clamped: n=1121 min=10.0000 p10=10.0000 p25=10.0000 p50=10.0000 p75=13.0844 p90=18.4358 max=200.0000

## 3.5 Nlookback 感度

| Nlookback | Pbirth p10 | Pbirth p50 | Pbirth p90 | I p10 | I p50 | I p90 | I range |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.3333 | 2.1667 | 4.0000 | -0.6021 | -0.3358 | 0.4771 | 1.5682 |
| 10 | 0.2727 | 2.3636 | 3.7273 | -0.5714 | -0.3736 | 0.5643 | 1.7324 |
| 20 | 0.1905 | 2.4286 | 3.4762 | -0.5411 | -0.3854 | 0.7202 | 1.9494 |
| 50 | 0.0980 | 1.1765 | 2.8627 | -0.4568 | -0.0706 | 1.0086 | 2.2833 |

## 一次推奨候補

### birth 条件の修正 (重要)
指示書の「3 条件 AND (S + E + cos Δθ)」は label birth ではなく Genesis 化学反応の条件。
label birth = (S ≥ 0.20 island ∪ R > 0 pair) − overlap 50%+。
Pbirth 式の設計はこの実際の birth 条件に基づくべき。

### Pbirth proxy の限界
- CSV 出力に S/R の per-step 時系列がないため、micro-level Pbirth は不可
- macro proxy (n_core 別 birth rate) は **n_core = 2 が 77% を占めるため分解能低い**
- 2-node と 3+ node で birth 経路が異なる (R>0 vs S≥0.20 island) ため、単一式での統一が困難

### ★ 致命的な問題: Pbirth > 1.0 による I 負値化

n_core=2 labels は 10 window 内に 10+ 回生まれるため、Pbirth = (count+1)/(Nlookback+1) >> 1.0。
結果として I = -log10(Pbirth) < 0 となり、50/(1+alpha*I) のデノミネータが負に → PI 負値。

**alpha ≥ 2 では 77% の labels で PI が負値または非常な極端値** (n_core=2 が全体の 77%)。
**alpha = 1 のみが全 PI 正値** (range [24.5, 161.8], p90/p10 = 3.65)。

### 数値根拠に基づく候補

| パラメータ | 一次候補 | 根拠 |
|---|---|---|
| alpha | **1** (唯一の安全値) | alpha=1 で全 PI 正値、range [25, 162]、ratio 3.65x。alpha≥2 では PI 負値多発 |
| clamp | **(25, 200)** | alpha=1 で raw 24.5-161.8 なので clamp は安全マージン程度 |
| Nlookback | **10 window** | I range 1.73 で分散最大かつ安定 |
| birth-rarity proxy | **n_core 別 macro birth rate** | CSV 既出力で唯一実行可能。micro は要コード変更 |

### 根本的な設計判断 (Taka 向け)

1. **Pbirth ≤ 1.0 clamp**: I = -log10(min(Pbirth, 1.0)) とすれば I ≥ 0 が保証される。ただし n_core=2 の 77% が I=0 (全員同じ interval) になり、rarity が機能しない
2. **Pbirth 正規化**: Pbirth = count / max_count で [0,1] に正規化。ただし max_count が seed 依存
3. **n_core 自体を直接使う**: I = log10(max_ncore / n_core) = log10(5/2)=0.40, log10(5/5)=0。単純で安定
4. **Pbirth 式自体を再設計**: Taka + 相談役 Claude の設計判断