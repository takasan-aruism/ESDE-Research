# v9.9 4-軸 閾値監査 (Stage 1)

*Generated*: 2026-04-12
*Source*: `diag_v99_internal_axis_short/introspection/` (48 seeds, read-only)
*目的*: 4 軸 (social/stability/spread/familiarity) の実変動幅と閾値の対応関係を数値で把握する

---

## 1. 4 軸の計算式 (並列比較)

**場所**: `primitive/v98c/v98c_information_pickup.py` 行 1046-1049 (呼び出し)、SubjectLayer 内 (定義)

### 呼び出しブロック (行 1046-1049):
```python
d_social      = cog.get_n_partners(cid) / max_partners
d_stability   = 1.0 / (1.0 + st_std / (st_mean + EPS))
d_spread      = cog.get_attention_entropy(cid)
d_fam         = cog.get_familiarity_mean(cid)
```

### 各軸の定義

**social** — 呼び出しローカル計算 (行 1046):
```python
# cog.get_n_partners(cid) = len(self.familiarity[cid])
# max_partners = その window 内の hosted cid 全体での最大
d_social = cog.get_n_partners(cid) / max_partners
```

**stability** — 呼び出しローカル計算 (行 1047):
```python
# st_sizes = その cid の window 内 structural set サイズのリスト
st_mean = np.mean(st_sizes) if st_sizes else 0
st_std  = np.std(st_sizes) if st_sizes else 0
d_stability = 1.0 / (1.0 + st_std / (st_mean + EPS))
```

**spread** — `SubjectLayer.get_attention_entropy(cid)` (行 338-351):
```python
def get_attention_entropy(self, cid):
    att = self.attention.get(cid, {})
    vs = list(att.values())
    s = sum(vs)
    ps = [v / s for v in vs if v > 0]
    H = -sum(p * math.log(p) for p in ps)
    max_H = math.log(len(ps)) if len(ps) > 1 else 1.0
    return H / max_H if max_H > 0 else 0.0
```

**familiarity** — `SubjectLayer.get_familiarity_mean(cid)` (行 353-357):
```python
def get_familiarity_mean(self, cid):
    fam = self.familiarity.get(cid, {})
    if not fam:
        return 0.0
    return float(np.mean(list(fam.values())))
```

### 単位・スケールの比較

| 軸 | 計算 | 理論範囲 | 単位 |
|---|---|---|---|
| social      | n_partners / max_partners        | [0, 1]      | 正規化比率 |
| stability   | 1/(1 + std/mean)                 | (0, 1]      | 正規化比率 |
| spread      | Shannon H / log(n)               | [0, 1]      | 正規化比率 |
| familiarity | mean(familiarity values)         | [0, ∞)      | **絶対値** (attention-like 累積量) |

→ ★ social/stability/spread は [0,1] 正規化、**familiarity だけ非正規化の絶対値**

## 2. 閾値定義

`primitive/v98c/v98c_information_pickup.py` 行 116-119:
```python
INTROSPECTION_THRESHOLD_SOCIAL      = 0.1
INTROSPECTION_THRESHOLD_STABILITY   = 0.1
INTROSPECTION_THRESHOLD_SPREAD      = 0.1
INTROSPECTION_THRESHOLD_FAMILIARITY = 2.0
```

**tag 生成条件** (全軸共通、行 501-545 で軸ごとに 1 ブロック):
```python
d_axis = curr['axis'] - prev['axis']  # 絶対 delta
if d_axis > THRESHOLD_AXIS:
    tags.append('gain_axis')
elif d_axis < -THRESHOLD_AXIS:
    tags.append('loss_axis')
```

**単位**: 全軸とも **絶対 delta** (前 window からの差分)
- social/stability/spread: [0,1] スケールに対する絶対 delta 0.1 = 10% ポイント変化
- familiarity: 絶対値スケールに対する絶対 delta 2.0 (スケール非正規化)

## 3. 4 軸の current 値と |delta| の分布 (introspection log 全 48 seeds 集約)

### 3-1. social

**current_social** (n=8953):

| 統計量 | 値 |
|---|---:|
| min    | 0.0000 |
| p25    | 0.2500 |
| median | 0.6750 |
| p75    | 0.8636 |
| p90    | 0.9565 |
| p99    | 1.0000 |
| max    | 1.0000 |
| mean   | 0.5851 |

**|delta_social|**:

| 統計量 | 値 |
|---|---:|
| min    | 0.0000 |
| p25    | 0.0160 |
| median | 0.0358 |
| p75    | 0.0678 |
| p90    | 0.1110 |
| p99    | 0.2288 |
| max    | 0.4706 |
| mean   | 0.0497 |

**閾値 = 0.1 → 超過率: 12.38%**

### 3-2. stability

**current_stability** (n=8953):

| 統計量 | 値 |
|---|---:|
| min    | 0.5268 |
| p25    | 0.6450 |
| median | 0.6686 |
| p75    | 0.6903 |
| p90    | 0.7104 |
| p99    | 0.7460 |
| max    | 0.7813 |
| mean   | 0.6676 |

**|delta_stability|**:

| 統計量 | 値 |
|---|---:|
| min    | 0.0000 |
| p25    | 0.0150 |
| median | 0.0321 |
| p75    | 0.0549 |
| p90    | 0.0792 |
| p99    | 0.1282 |
| max    | 0.2046 |
| mean   | 0.0382 |

**閾値 = 0.1 → 超過率: 3.89%**

### 3-3. spread

**current_spread** (n=8953):

| 統計量 | 値 |
|---|---:|
| min    | 0.4855 |
| p25    | 0.7958 |
| median | 0.8333 |
| p75    | 0.8540 |
| p90    | 0.8658 |
| p99    | 0.8822 |
| max    | 0.9236 |
| mean   | 0.8223 |

**|delta_spread|**:

| 統計量 | 値 |
|---|---:|
| min    | 0.0000 |
| p25    | 0.0108 |
| median | 0.0228 |
| p75    | 0.0412 |
| p90    | 0.0672 |
| p99    | 0.1305 |
| max    | 0.2577 |
| mean   | 0.0305 |

**閾値 = 0.1 → 超過率: 3.21%**

### 3-4. familiarity

**current_familiarity** (n=8953):

| 統計量 | 値 |
|---|---:|
| min    | 0.0000 |
| p25    | 7.6787 |
| median | 10.7034 |
| p75    | 14.3260 |
| p90    | 19.9542 |
| p99    | 81.5080 |
| max    | 228.0341 |
| mean   | 13.3429 |

**|delta_familiarity|**:

| 統計量 | 値 |
|---|---:|
| min    | 0.0000 |
| p25    | 1.2129 |
| median | 2.6311 |
| p75    | 5.3160 |
| p90    | 12.3282 |
| p99    | 81.4221 |
| max    | 257.8568 |
| mean   | 6.6002 |

**閾値 = 2.0 → 超過率: 59.89%**

## 4. 一覧表: 閾値が分布のどこにあるか

| 軸          | 閾値 | \|delta\| p50 | \|delta\| p75 | \|delta\| p90 | \|delta\| p99 | 閾値の位置 | tag 発生率 |
|---|---:|---:|---:|---:|---:|---|---:|
| social      | 0.1 | 0.0358 | 0.0678 | 0.1110 | 0.2288 | p75-p90 (87.6%ile) | 12.38% |
| stability   | 0.1 | 0.0321 | 0.0549 | 0.0792 | 0.1282 | p90-p99 (96.1%ile) |  3.89% |
| spread      | 0.1 | 0.0228 | 0.0412 | 0.0672 | 0.1305 | p90-p99 (96.8%ile) |  3.21% |
| familiarity | 2.0 | 2.6311 | 5.3160 | 12.3282 | 81.4221 | p25-p50 (40.1%ile) | 59.89% |

## 5. 一次判定

判定基準 (tag 発生率ベース):
- **粗すぎ**: tag 発生率 < 5% → 閾値が p95+ に位置、構造語がほぼ出ない
- **OK**:     tag 発生率 5-30% → 閾値が p70-p95 に位置、意味ある変動のみ拾う
- **細かすぎ**: tag 発生率 > 30% → 閾値が p70 以下、ノイズ級の変動も拾う

| 軸          | 閾値 | tag 発生率 | 判定 |
|---|---:|---:|---|
| social      | 0.1 | 12.38% | **OK** |
| stability   | 0.1 |  3.89% | **粗すぎ** |
| spread      | 0.1 |  3.21% | **粗すぎ** |
| familiarity | 2.0 | 59.89% | **細かすぎ** |
