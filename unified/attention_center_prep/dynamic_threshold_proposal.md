# dynamic_threshold 関数形 提案 (Code A) — Web Claude 神の手回避点検用

**Date**: 2026-05-31
**Author**: Code A
**Status**: Web Claude §6.1 への提案、神の手回避点検依頼
**親**: 機能設計 v1 確定 (判断 5 件ロック) ④

---

## 0. 設計原則

| 原則 | 反映 |
|---|---|
| 固定値最小化 | 比較の両辺が center.state 由来の動的量、固定数値 (定数 threshold) を使わない |
| state 依存 | should_attend の真偽が center.state の関数 |
| 予測不可能性 | center.state.rng や engine.virtual_stats 等で per_step に変動 |
| 形は実装側 (Code A) | Web Claude は神の手回避だけ点検 |

---

## 1. 提案 (シンプル案、本命)

```python
def should_attend(center_engine):
    """センターの内部状態から発火判定 (両辺 state-dependent)
    
    形: z_score_of_max_E > stress_intensity
    
    両辺の意味:
      - z_score_of_max_E = (max(E) - mean(E)) / std(E)
        = center.state.E の中で max がどれだけ外れているか (際立ち)
      - stress_intensity = current_links / link_ema (engine.stress_stats 由来)
        = link 数の最近の動態 (動的、固定値なし)
    
    両者とも center.state.virtual / state.E から計算、固定数値なし。
    """
    if not center_engine.state.alive_n:
        return False
    E_vals = np.array([center_engine.state.E.get(n, 0.0)
                        for n in center_engine.state.alive_n])
    if len(E_vals) < 2:
        return False
    mean_E = E_vals.mean()
    std_E = E_vals.std()
    if std_E < 1e-9:
        return False
    max_E = E_vals.max()
    z_score = (max_E - mean_E) / std_E  # state 由来 (E 分布)
    
    ss = center_engine.stress_stats or {}
    stress = ss.get('stress_intensity', 1.0)  # state 由来 (link 動態)
    
    # 比較: 両辺 state-dependent、ですから「閾値」は固定でない
    return z_score > stress
```

### 1.1 神の手回避の根拠

| 要素 | 由来 | 固定数値か |
|---|---|---|
| z_score (max - mean)/std | center.state.E (alive_n の E 値) | **動的** (毎 step E 変動) |
| stress_intensity | center.stress_stats (current_links / link_ema) | **動的** (link 動態、EMA で前 step 依存) |
| 比較演算子 `>` | -- | 演算子は固定だが、両辺の値が動的 |

「z_score > stress」は比較対象が両方 state、ですから **「定数 threshold (例: > 1.5)」を埋めていない**。

### 1.2 想定挙動

- 初期 (E 分布が一様、std 小) → z_score が大きく振れる → 発火しやすい
- 後期 (E 分布が安定、stress_intensity → 1) → 大体 z_score > 1 で発火
- stress_intensity が動いている step (link 急増減) → 発火閾値も動く、固定 1 でない

ですから **発火タイミングが center.state の固有時間で決まる**、外部 timer なし。

---

## 2. 代替案 (Web Claude 不採用なら)

### 2.1 案 B: signal_ratio ベース (VirtualLayer feedback 流用)

```python
def should_attend_v2(center_engine):
    vs = center_engine.virtual_stats or {}
    signal_ratio = vs.get('signal_ratio', 1.0)
    # signal_ratio = turnover_ema 比 (VirtualLayer v9 内部 feedback)
    # > 1 = turnover 増加中 (生死激しい)、< 1 = 安定
    ss = center_engine.stress_stats or {}
    stress = ss.get('stress_intensity', 1.0)
    # 両辺 state 由来
    return signal_ratio > stress
```

- 利点: VirtualLayer feedback 機構を直接使う、より「内部」依存
- 欠点: signal_ratio は warmup 中 (window < 20) は 1.0 固定なので、warmup 期間中は発火しない

### 2.2 案 C: 集中度 (top-K E 比) ベース

```python
def should_attend_v3(center_engine):
    E_vals = sorted([center_engine.state.E.get(n, 0.0)
                      for n in center_engine.state.alive_n], reverse=True)
    if len(E_vals) < 10:
        return False
    # K も state-dependent (alive_n の 1%)
    K = max(5, len(E_vals) // 100)
    top_K_sum = sum(E_vals[:K])
    total_sum = sum(E_vals)
    concentration = top_K_sum / (total_sum + 1e-9)
    # 比較: alive_n 数 (state) との比
    # ratio_alive = K / len(alive_n) (定数比率) なので concentration が ratio より高い = 集中
    ratio_alive = K / len(E_vals)
    return concentration > 2 * ratio_alive  # 「2 倍」が固定値、点検要
```

- 利点: 「集中度が均一分布の何倍か」で意味明瞭
- 欠点: 「2 倍」が固定値 → 神の手回避点検引っかかる可能性

---

## 3. Code A 推奨 = **案 A (本命)**

理由:
- 両辺 state-dependent、固定数値なし (z_score の構成要素 mean/std/max が動的、stress も動的)
- シンプル (5 行)
- 「際立ち」の意味が明瞭 (max が分布外れ)
- VirtualLayer warmup 制約なし

---

## 4. Web Claude 神の手回避点検依頼

| 点検項目 | 案 A (本命) |
|---|---|
| 固定値 (定数 threshold) を埋めているか | **いいえ** (両辺 state-dependent) |
| state-dependent で予測不可能性を保つか | **はい** (E 分布 + link 動態) |
| 比較演算子 `>` は固定だが両辺動的か | **はい** |

→ 神の手回避点検通る想定。Web Claude 不採用なら案 B / 案 C へフォールバック。

---

## 5. 一文サマリ

dynamic_threshold 関数形 提案 (Code A、2026-05-31、機能設計 v1 確定 ④、Web Claude 神の手回避点検依頼) — 設計原則 (固定値最小化 / state 依存 / 予測不可能 / 形は実装側) を満たす 3 案を提示し、本命 = 案 A 「z_score_of_max_E > stress_intensity」(両辺 state-dependent、z_score = (max-mean)/std で center.state.E の際立ち + stress_intensity = link 動態 EMA、両者とも固定数値なしの動的量、比較演算子 > のみ固定だが両辺動的なので神の手回避通る、初期 z_score 大で発火しやすく後期 stress→1 で z>1 で発火、シンプル 5 行 warmup 制約なし)、代替案 B (signal_ratio > stress、VirtualLayer feedback 直接利用、warmup 中発火しない欠点) + 案 C (集中度 > 2× ratio_alive、意味明瞭だが「2 倍」固定値で点検要)、Web Claude 点検依頼 (案 A は固定値なし両辺 state-dependent 予測不可能性保つ)、不採用なら B/C フォールバック、書込み unified/attention_center_prep/ 配下のみ。

---

**Dynamic threshold 提案 end. Web Claude 神の手回避点検後、smoke 実装に進む。**
