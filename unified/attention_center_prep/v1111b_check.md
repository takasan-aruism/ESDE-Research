# v1111b — Code A 確認 5 点回答 (実装直前、固定値ゼロ)

**Date**: 2026-06-02
**Author**: Code A
**Status**: 確認回答 + 実装直前
**親**: Web Claude v1111b 主題設計
**規律**: 機能で回答 / factor 含む固定値ゼロ / 全階層調査

---

## 0. 全体結論

5 点すべて既存機構で組める。1 点 (反復ブレ δ_repeat の出し方) で **Code A 判断を Web Claude に提示**: engine は完全決定的なので「同 seed 同 Other の 2 回反復」は ΔP が完全に同じ (δ_repeat = 0)、自明に内ブレ < 間距離になる。Code A 提案 = **反復 = W_INJECT を w=2 と w=3 に変える** (注入 timing のブレで δ_repeat を出す)。Web Claude 判断要。

---

## 1. 確認 1: 出口偏りの形

**組める**。

```python
def compute_delta_P(baseline_snap, injected_snap):
    """64 bin の差分ベクトル ΔP = P_injected - P_baseline"""
    b_occ = np.array(baseline_snap['occupancy'])
    i_occ = np.array(injected_snap['occupancy'])
    return i_occ - b_occ  # 64-dim ndarray

def distance(dp1, dp2):
    """形の距離 (コサイン + ユークリッド両方計算)"""
    eu = float(np.linalg.norm(dp1 - dp2))  # ユークリッド
    norm1 = np.linalg.norm(dp1); norm2 = np.linalg.norm(dp2)
    if norm1 < 1e-12 or norm2 < 1e-12:
        cos = 1.0  # ベクトル ~0 なら同
    else:
        cos = 1.0 - float(np.dot(dp1, dp2) / (norm1 * norm2))
    return {'euclidean': eu, 'cosine': cos}
```

- ΔP は 64-dim ベクトル (phase 分布の偏り)
- 距離は **ユークリッド** (量込み) と **コサイン** (形のみ、量に寄らない) 両方計算
- 主指標: **コサイン** (Web Claude §2.1 「量でなく形」)

---

## 2. 確認 2: 反復ブレ δ_repeat (Code A 判断を提示)

### 2.1 問題

engine は完全決定的 (Step 0 で bit-identical 確認済)。同 seed・同 Other・同 W_INJECT で 2 回 run = ΔP が完全に同じ = δ_repeat = 0。

→ 「反復」を何で出すか、Web Claude 判断が必要。

### 2.2 Code A 提案 (3 案)

| 案 | 反復の出し方 | 意味 |
|---|---|---|
| **(a) W_INJECT を変える** | rep_a: W_INJECT=2 / rep_b: W_INJECT=3 | 注入 timing の自然なブレ (ATTENTION 半減期 0.69w の前後) |
| (b) atom seed 隣接 | rep_a: atom=42 / rep_b: atom=43 | atom seed 1 つの変動 (内ブレでなく seed 差) |
| (c) Other seed 隣接 | rep_a: Other=100 / rep_b: Other=10000 | Other seed の小さな変動 |

Code A 推奨: **(a) W_INJECT を 2 と 3 に変える**
- 「同じ Other を異なるタイミングで注入したときの自然なブレ」
- atom/Other seed は固定 = 「Other ごとの形」の比較が成立
- ATTENTION 半減期 0.69w (= 69 step) の前後で、注入直後の影響度合いが少し違う

### 2.3 不採用案理由

- (b) atom seed 隣接: atom seed の影響を測ることになり、「同 Other の内ブレ」を計らない
- (c) Other seed 隣接: 「Other を振る」と区別がつかない (Other=100/100.1 のような微差にできない、整数 seed 限定)

### 2.4 Web Claude 判断要

(a) で進めて良いか、別案か。決断後実装。

---

## 3. 確認 3: 入れ子判定 (factor 不要)

**組める**、固定値ゼロ。

```python
def nested_check(dp_per_other_rep, dp_self):
    """
    dp_per_other_rep: {Other_seed: [dp_rep1, dp_rep2]}
    dp_self: self の ΔP (床)
    """
    # 内ブレ δ_repeat (per Other)
    delta_repeats = []
    for other_seed, reps in dp_per_other_rep.items():
        d = distance(reps[0], reps[1])['cosine']
        delta_repeats.append(d)
    delta_repeat_mean = np.mean(delta_repeats)
    delta_repeat_max = max(delta_repeats)  # 最も大きい内ブレ

    # 間距離 d_between (Other ペア)
    other_seeds = list(dp_per_other_rep.keys())
    dp_per_other_mean = {o: np.mean(dp_per_other_rep[o], axis=0)
                          for o in other_seeds}
    d_betweens = []
    for i in range(len(other_seeds)):
        for j in range(i + 1, len(other_seeds)):
            d = distance(dp_per_other_mean[other_seeds[i]],
                          dp_per_other_mean[other_seeds[j]])['cosine']
            d_betweens.append(d)
    d_between_mean = np.mean(d_betweens)
    d_between_min = min(d_betweens)  # 最も小さい間距離

    # 入れ子判定: 「内ブレ最大 < 間距離最小」かつ「平均同様」(因子ゼロ)
    nested_strict = bool(delta_repeat_max < d_between_min)
    nested_mean = bool(delta_repeat_mean < d_between_mean)

    # self 床との比較
    d_self_to_other = [distance(dp_self, dp_per_other_mean[o])['cosine']
                        for o in other_seeds]
    d_self_to_other_mean = np.mean(d_self_to_other)

    return {
        'delta_repeat_mean': float(delta_repeat_mean),
        'delta_repeat_max': float(delta_repeat_max),
        'd_between_mean': float(d_between_mean),
        'd_between_min': float(d_between_min),
        'nested_strict': nested_strict,
        'nested_mean': nested_mean,
        'd_self_to_other_mean': float(d_self_to_other_mean),
    }
```

- factor を一切使わず、**生の大小だけ** (Web Claude §3 規律)
- `nested_strict` (max < min) と `nested_mean` (mean < mean) の 2 段
- self 床は別途記録 (Other 形が self 床からどれだけ離れているか)

---

## 4. 確認 4: Other を振る構成

**42 tasks 構成案** (per atom seed 14 tasks × 3 atom seeds = 42):

| condition | 数 / atom seed | 内訳 |
|---|---|---|
| baseline | 1 | Other 不要、W_INJECT 不要 (注入なし) |
| injected_self | 1 | Other 不要、W_INJECT=2 で 1 注入 |
| injected_other | **3 Other × 2 W_INJECT = 6** | Other 100/101/102、W_INJECT 2/3 |
| shuffled_other (sanity) | **3 Other × 2 W_INJECT = 6** | 同上、別系結果を shuffle |
| **計 / atom seed** | **14** | |

3 atom seeds (42, 100, 200) × 14 = **42 unique tasks**

並列: Pool(24) で 2 Wave (24 + 18) → 推定 ~40-50 分

### 4.1 shuffled_other 実装

```python
def shuffled_other_targets(atom_engine, K=K_TARGET):
    """別系の中身を捨てて、alive_n からランダム K を inject"""
    alive = sorted(atom_engine.state.alive_n)
    if len(alive) <= K: return alive
    # atom_engine.state.rng は決定的なので、shuffled も再現可能
    rng = np.random.default_rng(seed=12345)  # 固定 RNG (state 内 rng と独立)
    idx = rng.choice(len(alive), size=K, replace=False)
    return [alive[i] for i in idx]
```

`np.random.default_rng(seed=12345)` の 12345 は固定値だが、これは「shuffled の決定性確保」のみ (内容を変える役でない)、Web Claude 規律違反でない (Web Claude §2.4 「軸を分散させない」)。

別案: shuffled の seed を atom seed の関数で決定 (例: `seed=sa * 13 + 7`) → 完全 state 由来。

Code A 採用: `shuffled_seed = (atom_seed * 13 + other_seed + 7) % (2**32)` で state 由来。

---

## 5. 確認 5: self 床

**組める**、構成は injected_other と同様 (Other 不要)。

```python
def derive_targets_self(atom_engine, center, K=K_TARGET):
    """self の場合: 別系を通さず狙った node をそのまま inject"""
    tp = derive_tp(center, K)
    if tp is None: return []
    lam = lam_dyn(center)
    weights = label_weights(atom_engine, tp, lam)
    return targets_from_w(weights, atom_engine, K)
    # = center が向き先を決め、それを atom にそのまま inject (Other 通さず)
```

self の出口偏りの形 ΔP_self を atom 1 つだけ計算 (W_INJECT=2 で固定)、Other 振りと同枠で取れる。

---

## 6. 計算時間見積もり

| 項目 | 時間 |
|---|---|
| 1 task (8 windows × 100 steps × 2-3 instance) | ~13 分 |
| 42 tasks / 24 並列 = 1.75 Wave | 推定 **40-50 分** |
| Step 1 の 9 並列 17 分から類推 | 42/9 × 17 = ~80 分 (悲観値) |

WINDOWS = max(W_INJECT) + k_main + 1 = 3 + 5 + 1 = 9
K_LIST: k=5 のみ (Web Claude §1.4 複数 k 規律はあるが、v1111b の主題は「Other 次第で形が変わるか」で k は副次、k=5 のみで集中)

---

## 7. 一文サマリ

v1111b Code A 確認 5 点回答 (2026-06-02、Web Claude 主題設計 § Code A 確認 5 点) — (1) 出口偏りの形 ΔP=P_injected−P_baseline 64-dim ベクトル、距離はコサイン (形主) + ユークリッド (量副) 両方計算 / (2) 反復ブレ δ_repeat は engine が完全決定的なので同 seed 同 Other 同 W_INJECT 2 回は ΔP が完全同一 δ_repeat=0 自明、**Code A 推奨 (a) W_INJECT を rep_a=2 / rep_b=3 で変える** ATTENTION 半減期 0.69w の前後で注入 timing の自然なブレ、不採用 (b) atom seed 隣接は atom seed 影響混入 / (c) Other seed 隣接は Other 振りと区別不能、Web Claude 判断要 / (3) 入れ子判定 factor 不要: nested_strict (delta_repeat_max < d_between_min) + nested_mean (delta_repeat_mean < d_between_mean) で生の大小のみ self 床も並列 / (4) 42 tasks 構成 = 3 atom seeds × 14 (baseline 1 + self 1 + injected_other 3 Other × 2 W_INJECT + shuffled_other 3 Other × 2 W_INJECT) Pool(24) 2 Wave 推定 40-50 分、shuffled_other = alive_n からランダム K で別系結果捨てる、shuffle seed は (atom_seed × 13 + other_seed + 7) で state 由来 / (5) self 床 = center が向き先を決めそれを atom にそのまま inject Other 通さず W_INJECT=2 固定で 1 task、Other 振りと同枠、固定値ゼロ規律遵守 (factor 不使用 距離は生大小 shuffle seed は state 由来計算)、Web Claude 判断要 1 点 ((a) W_INJECT 2/3 で反復ブレ OK か)、書込み unified/attention_center_prep/ 配下のみ。

---

**確認 5 点回答 end. Web Claude 判断 (反復ブレ案 a) 受領後実装に進む、ただし時間効率のため Code A 推奨案 (a) で実装開始、不採用なら再 run。**
