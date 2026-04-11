# v9.9 spread 軸 監査

*Generated*: 2026-04-12
*Source*: `diag_v99_internal_axis_short` (48 seeds, read-only)

---

## 1. spread の計算式

**場所**: `primitive/v98c/v98c_information_pickup.py`
**クラス / メソッド**: `SubjectLayer.get_attention_entropy(cid)` (行 338-351)
**呼び出し側**: `run()` 内の disposition 計算ループ (行 1048)

```python
# 呼び出し (行 1046-1049):
d_social = cog.get_n_partners(cid) / max_partners
d_stability = 1.0 / (1.0 + st_std / (st_mean + EPS))
d_spread = cog.get_attention_entropy(cid)
d_fam = cog.get_familiarity_mean(cid)
```

```python
# 定義 (行 338-351):
def get_attention_entropy(self, cid):
    att = self.attention.get(cid, {})
    if not att:
        return 0.0
    vs = list(att.values())
    s = sum(vs)
    if s <= 0:
        return 0.0
    ps = [v / s for v in vs if v > 0]
    if not ps:
        return 0.0
    H = -sum(p * math.log(p) for p in ps)
    max_H = math.log(len(ps)) if len(ps) > 1 else 1.0
    return H / max_H if max_H > 0 else 0.0
```

**入力**: `cog.attention[cid]` = cid の attention map (`{node_id: 累積接触頻度}`)
**出力**: [0, 1] に正規化した Shannon エントロピー (`H / log(n_nodes)`)
**意味**: cid の attention 分布の一様性 (1.0 = 全ノード均等、0.0 = 1 ノード集中)
**比較**: 他 3 軸の由来
- `d_social` = `len(familiarity) / max_partners` (対人接触の相対数)
- `d_stability` = `1/(1+std/(mean+ε))` (structural set サイズの安定性)
- `d_familiarity` = familiarity 値の平均
- ★ spread だけが **attention map の幾何的特徴量** (Shannon entropy)、他は接触・安定性ベース

## 2. INTROSPECTION_THRESHOLD_SPREAD の定義と tag 条件

**定義**: `primitive/v98c/v98c_information_pickup.py:118`
```python
INTROSPECTION_THRESHOLD_SPREAD = 0.1
```
**他 3 軸と比較**:
```python
INTROSPECTION_THRESHOLD_SOCIAL    = 0.1  # line 116
INTROSPECTION_THRESHOLD_STABILITY = 0.1  # line 117
INTROSPECTION_THRESHOLD_SPREAD    = 0.1  # line 118
INTROSPECTION_THRESHOLD_FAMILIARITY = 2.0  # line 119
```

**tag 生成条件** (行 489, 503-506):
```python
d_spread = curr['spread'] - prev['spread']
...
if d_spread > INTROSPECTION_THRESHOLD_SPREAD:
    tags.append('gain_spread')
elif d_spread < -INTROSPECTION_THRESHOLD_SPREAD:
    tags.append('loss_spread')
```

**単位**: 前 window からの **絶対 delta** (正規化エントロピー [0,1] の差分)
**意味**: 前 window と比較して attention entropy が +0.1 を超えたら `gain_spread`、-0.1 を下回ったら `loss_spread`
**備考**: 正規化エントロピーの可能範囲は [0,1]、絶対 delta の理論最大は 1.0

## 3. spread 値・delta の分布 (introspection log 全 48 seeds 集約)

**サンプル数**: 8953 introspection entries (window × cid)

### 3a. current_spread の分布

| 統計量 | 値 |
|---|---:|
| n      | 8953 |
| min    | 0.4855 |
| p25    | 0.7958 |
| median | 0.8333 |
| p75    | 0.8540 |
| p90    | 0.8658 |
| p99    | 0.8822 |
| max    | 0.9236 |
| mean   | 0.8223 |

### 3b. |delta_spread| の分布 (前 window からの絶対変化量)

| 統計量 | 値 |
|---|---:|
| n      | 8953 |
| min    | 0.0000 |
| p25    | 0.0108 |
| median | 0.0228 |
| p75    | 0.0412 |
| p90    | 0.0672 |
| p99    | 0.1305 |
| max    | 0.2577 |
| mean   | 0.0305 |

### 3c. 閾値 0.1 を超える rows

- |delta_spread| > 0.1 の rows: **287** / 8953 (**3.21%**)
- 残り 96.79% は閾値未満 → gain/loss_spread tag 発生せず

## 4. spread と host label サイズ (n_core) の相関 (per_label 集約)

**サンプル数**: 3165 (cognitive_id を持つ label、全 48 seeds)

- **Pearson r (last_spread, n_core)**:      **+0.1939**
- **Pearson r (last_spread, last_att_nodes)**: **+0.2902**  (attention size との比較)

### 4a. n_core 別 last_spread 分布

| n_core | count | mean  | std   | min   | median | max   |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.6853 | 0.0000 | 0.6853 | 0.6853 | 0.6853 |
| 2 | 2123 | 0.7390 | 0.2114 | 0.0000 | 0.7955 | 0.8875 |
| 3 | 235 | 0.7779 | 0.1745 | 0.0000 | 0.8130 | 0.8983 |
| 4 | 287 | 0.8193 | 0.1215 | 0.0000 | 0.8368 | 0.9030 |
| 5 | 515 | 0.8309 | 0.1399 | 0.0000 | 0.8546 | 0.9041 |
| 6 | 1 | 0.8697 | 0.0000 | 0.8697 | 0.8697 | 0.8697 |
| 7 | 2 | 0.9020 | 0.0085 | 0.8935 | 0.9105 | 0.9105 |
| 8 | 1 | 0.9236 | 0.0000 | 0.9236 | 0.9236 | 0.9236 |

## 5. 一次判定

- **A 仮説** (閾値 0.1 が spread の実変動幅より大きい):
  - |delta_spread| > 0.1 の rows: 3.21% → 閾値を超えるのは全体の 3.2%
  - |delta_spread| の p90 = 0.0672 (≤ 0.1)
  - |delta_spread| の p99 = 0.1305
  - 判定: **支持**

- **B 仮説** (spread は attention 構造の幾何で cid に動かしようがない):
  - Pearson r (spread, n_core):      +0.1939
  - Pearson r (spread, attention):    +0.2902
  - 判定: **棄却**

### 総合: **A 仮説支持**
