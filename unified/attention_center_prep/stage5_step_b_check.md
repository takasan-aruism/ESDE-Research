# 注意センター Step B — Code A 確認 4 点回答 (実装直前)

**Date**: 2026-05-31
**Author**: Code A
**Status**: 確認 4 点回答、実装に進む
**親**: Web Claude Step B 機能設計

---

## 0. 全体結論

**4 点すべて流用可、新規発明ゼロ**。実装に進む。

---

## 1. 確認 1: phase 取得経路 (実在)

| 対象 | 場所 | 形 |
|---|---|---|
| `center.state.theta[n]` | `ecology/engine/genesis_state.py:33` で uniform(0, 2π) 初期化、ndarray | float, 0..2π |
| `label.phase_sig` | `primitive/v910/virtual_layer_v9.py:247` で birth 時平均 θ 計算 | float, -π..π (math.atan2 由来) |
| `MacroNode.phase_core_theta` | virtual_layer_v9.py:43 = phase_sig alias | float |
| v918 per_subject の `original_phase_sig` | `primitive/v918/v918_memory_readout.py` で同じ phase_sig を保存 | 一致 |

→ **両方 0..2π 系の連続スカラー**、circular distance で照合可能 (一部 phase_sig は atan2 由来で -π..π、絶対値 + modulo で吸収)。

---

## 2. 確認 2: exp(-λd) 流用 + λ 形提案

### 2.1 既存流用

`primitive/v911/v911_cognitive_capture.py:1634`:
```python
p_capture = V11_P_MAX * math.exp(-V11_LAMBDA * delta)
```
- V11_P_MAX = 0.9
- V11_LAMBDA = 2.724 (smoke n=150 eval pulses から決定)

→ **そのまま流用可能**、形は同形 (`w = exp(-λ · circular_distance)`)。

### 2.2 Code A 提案: λ を state 由来 (固定値回避)

```python
def compute_lambda_dynamic(atom_engine):
    """λ を Atom 系 labels の phase_sig 分散から導出 (state 由来)"""
    macro = set(atom_engine.virtual.macro_nodes)
    phase_sigs = [lab['phase_sig'] for lid, lab in atom_engine.virtual.labels.items()
                  if lid not in macro]
    if len(phase_sigs) < 2:
        return 1.0
    # 円周分散 (circular standard deviation の代替)
    cos_mean = np.mean([math.cos(p) for p in phase_sigs])
    sin_mean = np.mean([math.sin(p) for p in phase_sigs])
    r = math.sqrt(cos_mean**2 + sin_mean**2)  # mean resultant length
    # circular std ~ sqrt(-2 ln r)
    if r < 1e-9:
        circular_std = math.pi
    else:
        circular_std = math.sqrt(-2 * math.log(max(r, 1e-9)))
    # λ = 1 / circular_std (分散小なら λ 大 = 厳しい、分散大なら λ 小 = 緩い)
    return 1.0 / (circular_std + 1e-9)
```

- **両辺 state 量**: λ は labels の phase 分散 (動的)、Δ は label と target の距離 (動的)
- 固定数値なし (1e-9 は数値安定化のみ)
- 「分布が散らばっているときは緩く、集中しているときは鋭く狙う」自然な意味

### 2.3 Web Claude 神の手回避点検依頼

| 点検項目 | 案 (λ_dynamic) |
|---|---|
| 固定値 (定数 λ) を埋めているか | **いいえ** (λ は labels の phase 分散の関数) |
| state-dependent か | **はい** (atom_engine.virtual.labels の phase_sig 集合) |
| 入力が予測不可能か | **はい** (labels は per_window 動的) |

---

## 3. 確認 3: 近傍/遠方分解 (解析経路)

### 3.1 既存の phase bin 構造

`primitive/v910/virtual_layer_v9.py:70`:
- N_BINS = 64
- BIN_WIDTH = 2π / 64 ≈ 0.098 rad ≈ 5.6°
- `occupancy[b]` = 各 bin の現在 occupancy
- `_phase_bin(theta)` で theta → bin index 変換

### 3.2 近傍/遠方分解の実装案

```python
def phase_near_far_decomposition(atom_engine, target_phase, K_NEAR=3):
    """target_phase 近傍 (±K_NEAR bins) / 遠方の occupancy 集計"""
    target_bin = atom_engine.virtual._phase_bin(target_phase)
    occ = atom_engine.virtual.occupancy
    N_BINS = atom_engine.virtual.N_BINS
    near_bins = set()
    for d in range(-K_NEAR, K_NEAR + 1):
        b = (target_bin + d) % N_BINS  # 円周 wrap
        near_bins.add(b)
    near_sum = sum(occ[b] for b in near_bins)
    far_sum = sum(occ[b] for b in range(N_BINS) if b not in near_bins)
    return {
        'target_bin': target_bin,
        'near_bins_count': len(near_bins),  # 2*K_NEAR + 1
        'near_occ_sum': float(near_sum),
        'far_occ_sum': float(far_sum),
        'near_occ_mean': float(near_sum / len(near_bins)),
        'far_occ_mean': float(far_sum / (N_BINS - len(near_bins))),
    }
```

- K_NEAR=3 で 7 bins (≈39°) 近傍
- no_center vs with_center で `near_occ_sum` の差 / `far_occ_sum` の差 を比較
- 近傍で偏った差 → 狙い撃ち候補
- 全体均一の差 → 盲目

---

## 4. 確認 4: 発火バー両辺 state 形

### 4.1 Step A の問題

案 A `z_score > stress_intensity`、しかし `stress_enabled=False` で `stress=1.0` 固定 → 片側定数。

### 4.2 修正 (Code A 提案、シンプル)

**stress_enabled=True に変更** (機能設計 v1 確定 ② 「物理切らない」と整合):

```python
encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
```

- stress_intensity = current_links / link_ema (link 動態で動的)
- 案 A `z_score > stress_intensity` の両辺が完全動的になる
- 第 4 段階 smoke で stress_enabled=True 確認 (stress_intensity 0.9711 観察、動的)

これで「発火/無視」が分かれる動態を期待。

### 4.3 Web Claude 神の手回避点検依頼

| 点検項目 | 修正 (stress_enabled=True) |
|---|---|
| 固定値を埋めているか | **いいえ** (両辺 state-dependent) |
| 両辺 state 由来か | **はい** (z_score = E 分布 / stress = link 動態) |
| 発火/無視が分かれるか | smoke で確認 (期待: stress 0.95-1.05 範囲動く、z_score 5-10 動く → 重なる範囲で無視出る可能性) |

---

## 5. 実装内容 (確認 5 点まとめ)

### 5.1 変更点 (Step A → Step B)

| | Step A | Step B |
|---|---|---|
| stress_enabled | False | **True** (両辺動的) |
| 向き先 | derive_attention_targets (node ID top-K) | **derive_center_target_phase + compute_label_weights (phase 連続一致率)** |
| overlap 判定 | 二値 (overlap=0 多発) | **w = exp(-λ·d) 連続重み** |
| inject 選択 | overlap_nodes or target_ids (フォールバック) | **top-K w labels の core nodes** |
| 観察 | 全体集計 (occ_max / occ_nonzero) | **+ 近傍/遠方分解** |

### 5.2 1 往復フロー (Step B)

```
[センター発火 (両辺 state 動的)]
  should_attend = z_score > stress_intensity  ← 両辺動的
       ↓ (発火時のみ)
[center_target_phase 計算]
  E top-K node の theta 平均円周方向 (state 由来)
       ↓
[Atom 系 labels の連続一致率]
  λ = 1 / circular_std(labels.phase_sig)  ← state 由来
  for each label:
    d = circular_distance(label.phase_sig, target_phase)
    w = exp(-λ · d)
       ↓ 各 label に w
[top-K w labels の core nodes を別系へ inject]
  別系 step (5 steps)
       ↓
[別系結果 → Atom 系へ書き戻し (source_event 1 本)]
[近傍/遠方分解で観察]
```

---

## 6. 一文サマリ

注意センター Step B Code A 確認 4 点回答 (2026-05-31) — (1) phase 取得: center.state.theta と label.phase_sig 共に 0..2π 系連続スカラー実在、circular distance で照合可能 / (2) exp(-λd) 流用: v911 V11_P_MAX×exp(-V11_LAMBDA×Δ) そのまま流用、λ は state 由来 = 1/circular_std(labels.phase_sig) 提案、両辺 state 量で固定値なし / (3) 近傍/遠方分解: phase bin N_BINS=64 (BIN_WIDTH≈5.6°)、target_bin ±K_NEAR=3 で 7 bins 近傍、near_occ_sum vs far_occ_sum 比較で狙い/盲目区別 / (4) 発火バー: stress_enabled=True に修正で stress_intensity 動的化、案 A z_score > stress_intensity の両辺動的、機能設計 v1 確定 ②「物理切らない」と整合、Step A の片側定数問題解消、Web Claude 神の手回避点検依頼 (λ + 発火バー両者 state 由来固定なし)、書込み unified/attention_center_prep/ 配下のみ、次は実装 + smoke + 近傍/遠方分解観察。

---

**Confirmation end. 実装に進む (stage5_step_b_smoke.py)。**
