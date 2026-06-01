# v1111d 確認 5 点回答 — 左右対称チェック (粒度の意図的非対称)

**Date**: 2026-06-02
**Author**: Code A
**Status**: 確認回答 + 実装直前
**親**: Web Claude v1111d 設計

---

## 0. 左右対称チェック (§2、最優先、Code A 認識確認)

### 原理 (phase / exp(-λd) / λ state 由来 / テーマ) → **全部揃う ✓**

| 項目 | 入口 | 出口 v1111d | 対称? |
|---|---|---|---|
| 何で照合 | phase | phase | ✓ |
| カーネル | exp(-λd) | exp(-λd) | ✓ |
| λ 出所 | state (center) | state (other) | ✓ |
| 渡すもの | テーマ (phase) | テーマ (**phase 分布**) | ✓ |
| **粒度** | **一点 (狙い)** | **分布 (中身)** | **意図的非対称** |

→ **原理は揃い、粒度だけ意図的非対称** (入口=狙い → 一点、出口=中身 → 分布)。
→ v1111c のバグ (番号 vs 一致率 = 原理違い) と区別される。**赤信号なし**。

---

## 1. 確認 1: 左右対称 + 粒度非対称が意図通りか

§0 で全項目「揃う」または「意図的非対称」を確認。

意図的非対称の根拠:
- **入口**: 「Atom のどこを狙って Other に送るか」= 狙い → 一点 (target_phase = 円周平均)
- **出口**: 「Other が何をしたか」= 中身 → 分布 (全 active node の E 重み付き phase 分布)
- → 仕事が違うので粒度が違う

**原理片側崩れていない** (両者とも phase + exp(-λd) + state 由来 + テーマ phase)。

---

## 2. 確認 2: 出口の分布計算

```python
def compute_label_excitations_dist(atom, other, lam_out):
    """各 Atom label の励起度 = Σ_n E[n]·exp(-λ·d(label.phase_sig, θ[n]))
    v1111c の一点版を「和」に広げるだけ、exp(-λd) カーネル流用、numpy vectorize"""
    alive = sorted(other.state.alive_n)
    if not alive:
        return {}
    E_arr = np.array([float(other.state.E.get(n, 0.0)) for n in alive])
    theta_arr = np.array([float(other.state.theta[n]) for n in alive])
    
    macro = set(atom.virtual.macro_nodes)
    weights = {}
    for lid, lab in atom.virtual.labels.items():
        if lid in macro: continue
        ps = lab['phase_sig']
        # circular distance (vectorized)
        d = np.abs(theta_arr - ps) % (2*np.pi)
        d = np.minimum(d, 2*np.pi - d)
        # 励起度 = Σ_n E[n] · exp(-λd)
        exc = float(np.sum(E_arr * np.exp(-lam_out * d)))
        weights[lid] = {'w': exc, 'nodes': list(lab['nodes'])}
    return weights
```

- 計算量: alive_other (~5000) × labels (~150-350) = 1-2M の演算 / inject 1 回
- numpy vectorize で **<0.1s** per inject

---

## 3. 確認 3: 書き戻し (Atom 自身の label の node、source_event 1 本)

```python
# 励起度高い Atom label の core node を target_nodes に
targets_out = derive_targets_from_weights(weights_out, atom, K_TARGET)
if targets_out:
    atom.physics.inject(atom.state, target_nodes=targets_out)
```

- Atom 自身の label の node を渡す (Other 生 occupancy 直接書込なし)
- source_event 1 本

---

## 4. 確認 4: 測り直し (v1111c と同じ 3 参照点、shuffled 拡張)

| 参照点 | v1111d での扱い |
|---|---|
| baseline | 注入なし (同じ) |
| injected_self | center 一点 → Atom 直接 inject (変更なし) |
| **injected_other** | **入口は一点、出口は分布版** (新規) |
| **shuffled_other** | **Other の phase 分布を random phase 分布に置換** (E 重みは Other 由来、phase だけ random) |

### 4.1 shuffled_other 実装

```python
def compute_label_excitations_dist_shuf(atom, other, lam_out, sa, so):
    """shuffled: Other の phase 分布を random phase で置換、E 重みは Other 由来"""
    alive = sorted(other.state.alive_n)
    if not alive:
        return {}
    E_arr = np.array([float(other.state.E.get(n, 0.0)) for n in alive])
    
    # random phase 分布 (state 由来 seed)
    sf_seed = (sa * 13 + so + 7) % (2**32)
    rng = np.random.default_rng(seed=sf_seed)
    theta_arr = rng.uniform(0, 2*np.pi, size=len(alive))
    
    macro = set(atom.virtual.macro_nodes)
    weights = {}
    for lid, lab in atom.virtual.labels.items():
        if lid in macro: continue
        ps = lab['phase_sig']
        d = np.abs(theta_arr - ps) % (2*np.pi)
        d = np.minimum(d, 2*np.pi - d)
        exc = float(np.sum(E_arr * np.exp(-lam_out * d)))
        weights[lid] = {'w': exc, 'nodes': list(lab['nodes'])}
    return weights
```

E 重みは保ち、**phase だけ random で「Other の中身を捨てる」**。一致率機構 (exp(-λd) + 分布の和) は通す。

---

## 5. 確認 5: λ 出口 state 由来

`lam_out = compute_lambda_dynamic(other)` (other 側の labels phase 分散から)
- state 由来、固定値ゼロ
- v1111c と同じ
- 赤信号なし

---

## 6. 実装変更点 (v1111c → v1111d)

| 場所 | v1111c (一点) | v1111d (分布) |
|---|---|---|
| Other の活性表現 | top-K node の phase 円周平均 (1 つの phase) | **active node 全部の E 重み付き phase 分布** |
| Atom label 励起度計算 | exp(-λ·d(label, theme_phase)) (一点距離) | **Σ_n E[n]·exp(-λ·d(label, θ[n])) (分布との重なり)** |
| shuffled の phase | random theme phase (1 つ) | **random phase 分布 (全 active node)** |
| 入口 | 変更なし (一点) | 変更なし (一点、意図的非対称) |

---

## 7. 一文サマリ

v1111d Code A 確認 5 点回答 (2026-06-02、Web Claude v1111d 設計「出口を一点でなく phase 分布の形で運ぶ」、左右対称チェック最優先) — §0 左右対称チェックで原理 (phase/exp(-λd)/λ state 由来/テーマ phase) 全項目「揃う」+ 粒度の意図的非対称 (入口=狙い→一点・出口=中身→分布) で v1111c バグの番号 vs 一致率 = 原理違いと区別、赤信号なし、(1) 左右対称 + 粒度非対称意図通り、(2) 出口分布計算 = Σ_n E[n]·exp(-λ·d(label, θ[n])) numpy vectorize で alive(5000) × labels(150-350) <0.1s per inject、(3) 書き戻しは Atom 自身 label の core node を physics.inject (Other 生 occupancy 書込なし source_event 1 本)、(4) 測り直し = v1111c と同じ 3 参照点 shuffled は Other phase 分布を random phase 分布に置換 E 重みは Other 由来で中身捨て機構通す、(5) λ_out = compute_lambda_dynamic(other) state 由来固定値ゼロ赤信号なし、変更点 = v1111c の一点版を Σ_n に広げるだけ exp(-λd) カーネル流用新発明なし、24 tasks × Pool(24) 推定 ~15 分 (計算量は v1111c とほぼ同等)、書込み unified/attention_center_prep/ 配下のみ。

---

**確認回答 end. 左右対称チェック ✓ (原理揃い + 粒度非対称意図通り) → 実装に進む。**
