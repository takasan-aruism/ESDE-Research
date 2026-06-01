# v1111c 確認 5 点回答 — 左右対称優先

**Date**: 2026-06-02
**Author**: Code A
**Status**: 確認回答 + 実装直前
**親**: Web Claude v1111c 設計 (出口も一致率に、入口・出口左右対称化)
**規律**: §2 左右対称チェック最優先 / 固定値ゼロ / 番号コピー赤信号

---

## 0. §2 左右対称チェック (Code A 認識確認、最優先)

| 項目 | 入口 (center→Atom) | **出口 (Other→Atom) v1111c** | 対称? |
|---|---|---|---|
| 何で照合 | phase (circular_distance) | **phase (circular_distance)** | ✓ |
| 一致率の式 | w=exp(-λ_in · d) | **w=exp(-λ_out · d)** | ✓ |
| λ の出所 | state 由来 (center) | **state 由来 (other)** | ✓ |
| 渡すもの | テーマ (target_phase)、番号でない | **テーマ (other_theme_phase)、番号でない** | ✓ |

**全項目で揃う**、片側番号コピーが残らない。赤信号なし。Code A 認識確認 OK。

---

## 1. 確認 1: 左右対称 (最優先)

§0 の表で全項目「揃う」が達成。

実装で番号コピー (`new_targets = trans_other(other, K)` → そのまま inject) を **削除**し、phase 一致率に置き換える。

---

## 2. 確認 2: 出口の一致率 (入口の機構をそのまま流用)

```python
# Other の活性を phase で表す (top-K node の円周平均)
def derive_other_theme_phase(other_engine, K=K_TARGET):
    """Other top-K E node の phase 群を円周平均で 1 つの phase に集約"""
    alive = sorted(other_engine.state.alive_n)
    if not alive: return None
    e_vals = {n: float(other_engine.state.E.get(n, 0.0)) for n in alive}
    top_K = sorted(alive, key=lambda n: -e_vals[n])[:K]
    thetas = [float(other_engine.state.theta[n]) for n in top_K]
    if not thetas: return None
    cs = sum(math.cos(t) for t in thetas)
    ss = sum(math.sin(t) for t in thetas)
    return math.atan2(ss/len(thetas), cs/len(thetas)) % (2*math.pi)

# Atom label と一致率で照合 (入口の compute_label_weights をそのまま流用)
def derive_atom_targets_from_other_phase(atom, other_theme_phase, lambda_out, K=K_TARGET):
    """Other のテーマ phase と Atom label の一致率で w 計算 → top-K w label の core nodes"""
    weights = compute_label_weights(atom, other_theme_phase, lambda_out)  # 入口流用
    return derive_targets_from_weights(weights, atom, K)  # 入口流用
```

入口の `compute_label_weights` + `derive_targets_from_weights` を **そのまま流用**。新規発明なし。

---

## 3. 確認 3: 書き戻し (Atom 自身の label の node、source_event 1 本)

```python
# 書き戻し: w で重み付けで選んだ Atom 自身の label の node を physics.inject
atom_targets_writeback = derive_atom_targets_from_other_phase(
    atom, other_theme_phase, lambda_out, K)
if atom_targets_writeback:
    atom.physics.inject(atom.state, target_nodes=atom_targets_writeback)
```

- **Atom 自身の label の node** を target_nodes に渡す (Other の生 occupancy 直接書込なし)
- source_event 1 本 (physics.inject のみ)
- 「形」を直接書く経路は使わない (Web Claude §3 規律)

---

## 4. 確認 4: 測り直し (v1111b 計測修正と同じ 3 参照点)

| 参照点 | v1111c での扱い |
|---|---|
| baseline | 注入なし (同じ) |
| injected_self | center が決めた target を Atom に直接 inject (Other 通さず、変更なし) |
| **injected_other** | **v1111c で出口を一致率に変更**: Other→Atom phase 一致率で target 決定 |
| **shuffled_other** | **v1111c で random phase を Other テーマの代わりに使う** (一致率機構は通す) |

### 4.1 shuffled_other の実装方針

```python
# shuffled では「Other は build するが、出口は random phase」
# = 中身を捨てるが、一致率機構は通す (入口・出口対称を維持)
def shuffled_theme_phase(atom_seed, other_seed):
    """random theme phase (state 由来 seed)"""
    sf_seed = (atom_seed * 13 + other_seed + 7) % (2**32)
    rng = np.random.default_rng(seed=sf_seed)
    return rng.uniform(0, 2*math.pi)
```

shuffled の λ_out は **other 由来** (other instance を build & run するため)。
入口は同じ、出口の phase だけ random。これで「Other の中身を捨てた純粋な一致率機構」がテストされる。

---

## 5. 確認 5: λ 出口の state 由来

**λ_out = `compute_lambda_dynamic(other)`** (Other 側の labels phase 分散から)

- 入口 λ_in = `compute_lambda_dynamic(center)` (center 側、Taka 2026-06-01 指示)
- 出口 λ_out = `compute_lambda_dynamic(other)` (other 側、対称)
- **両者 state 由来、固定値ゼロ**

赤信号なし。

---

## 6. 実装変更点 (v1111b 計測修正 → v1111c)

| 場所 | v1111b 計測修正 | v1111c |
|---|---|---|
| injected_other 出口 | `new_targets = trans_other(other, K)` (番号コピー) | **`other_theme_phase` → 一致率 → Atom label の core nodes** |
| shuffled_other | alive_n からランダム K (中身ゼロ、機構未経由) | **other を build/run、出口の phase だけ random** (機構通す) |
| 入口 (injected_self / injected_other) | 変更なし | 変更なし |
| baseline / 3 参照点 | 変更なし | 変更なし |

---

## 7. 構成

- 24 tasks (3 atom × 8 conditions)、W_INJECT=2 固定 (v1111b 計測修正と同じ)
- Pool(24) 並列、推定 ~15 分

---

## 8. 一文サマリ

v1111c Code A 確認 5 点回答 (2026-06-02、Web Claude v1111c 設計、左右対称最優先) — §2 左右対称チェック全項目「揃う」(入口・出口とも phase で照合 / w=exp(-λd) / λ state 由来 / テーマ phase で番号でない、片側番号コピー残らず赤信号なし)、(1) 左右対称 OK、(2) 出口一致率 = Other top-K node phase の円周平均 = other_theme_phase + 入口の compute_label_weights / derive_targets_from_weights そのまま流用新規発明なし、(3) 書き戻しは Atom 自身 label の core nodes (Other 生 occupancy 直接書込なし source_event 1 本)、(4) 測り直し = v1111b 計測修正と同じ 3 参照点 (self 床 / shuffled / atom 横断一貫性) shuffled は other build & run するが出口の phase だけ random (中身捨てつつ一致率機構通す = 入口・出口対称維持)、(5) λ_out = compute_lambda_dynamic(other) other 側 state 由来 入口 λ_in = center 側 state 由来で両者 state 由来固定値ゼロ赤信号なし、変更点 (v1111b 計測修正 → v1111c で injected_other 出口を番号コピーから一致率に + shuffled_other を一致率機構通す random phase に)、24 tasks × Pool(24) 推定 ~15 分、左右対称規律遵守、書込み unified/attention_center_prep/ 配下のみ。

---

**確認回答 end. 左右対称チェック OK → 実装に進む。**
