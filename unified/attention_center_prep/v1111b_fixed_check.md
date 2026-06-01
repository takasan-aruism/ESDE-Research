# v1111b 計測修正 — Code A 確認 5 点回答

**Date**: 2026-06-02
**Author**: Code A
**Status**: 確認回答 + 実装直前
**親**: Web Claude v1111b 計測修正設計

---

## 0. 全体結論

5 点すべて既存機構で組める。δ_repeat を作らない構成で固定値・factor 完全ゼロを維持。

---

## 1. 確認 1: タイミング固定 (δ_repeat 作らない)

**組める**。

```python
W_INJECT_FIXED = 2  # 全条件で固定、ロバスト性確認で W_INJECT=3 別 run
# 全 tasks で同じ w_inject を使う
# 反復ブレを人工生成しない (engine 決定的なので同 task は同 ΔP)
```

- W_INJECT=2 で 24 tasks (3 atom × 8 conditions)
- ロバスト性: W_INJECT=3 で別 run (24 tasks)
- **W_INJECT 間の差は物差しに使わない** (各 w 内で完結、Web Claude §4 やる順 4)

---

## 2. 確認 2: atom 横断一貫性 (δ_repeat の代替)

**組める**、phase 64 bin 空間で変位ベクトル比較。

```python
def compute_displacement(atom_dp_other, atom_dp_self):
    """各 Other の変位 V_other = ΔP(other) - ΔP(self)"""
    return np.asarray(atom_dp_other) - np.asarray(atom_dp_self)

def atom_consistency(V_per_atom, other_seed):
    """同 Other が atom=42/100/200 で同じ向きに変位するか
    cos 距離 (向き) で測る、量 (norm) でなく形"""
    atoms = list(V_per_atom.keys())  # [42, 100, 200]
    cos_pairs = []
    for i in range(len(atoms)):
        for j in range(i+1, len(atoms)):
            d = distance_pair(V_per_atom[atoms[i]], V_per_atom[atoms[j]])
            cos_pairs.append({
                'atom_pair': f'{atoms[i]}_vs_{atoms[j]}',
                'cos': d['cos'],
            })
    return {
        'other_seed': other_seed,
        'cos_mean': float(np.mean([c['cos'] for c in cos_pairs])),
        'cos_max': float(max([c['cos'] for c in cos_pairs])),
        'cos_pairs': cos_pairs,
    }
```

- 3 atom seeds で同 Other の変位ベクトル V_other_i を比較
- cos 距離小 (~0) → atom 横断で向きが一貫 = Other 中身の署名
- cos 距離大 (~1) → atom ごとにバラけ = 相互作用ノイズ

---

## 3. 確認 3: real vs shuffled (同タイミング)

**組める**、shuffle seed は state 由来。

```python
# shuffle seed (v1111b と同じ state 由来計算)
def get_shuffle_seed(atom_seed, other_seed):
    return (atom_seed * 13 + other_seed + 7) % (2**32)

def compute_d_between(dp_by_other):
    """Other ペア間の距離 (cos)"""
    seeds = sorted(dp_by_other.keys())
    cos_pairs = []
    for i in range(len(seeds)):
        for j in range(i+1, len(seeds)):
            d = distance_pair(dp_by_other[seeds[i]], dp_by_other[seeds[j]])
            cos_pairs.append({'pair': f'{seeds[i]}_vs_{seeds[j]}', 'cos': d['cos']})
    return {
        'cos_mean': float(np.mean([c['cos'] for c in cos_pairs])),
        'cos_min': float(min([c['cos'] for c in cos_pairs])),
        'cos_pairs': cos_pairs,
    }

# 比較: real vs shuffled (同 atom 内)
# d_between_real > d_between_shuffled → 中身が構造足す
# d_between_real ≈ d_between_shuffled → 違う注入だけの差 (ノイズ)
```

- 同タイミング (W_INJECT=2) で injected_other と shuffled_other を取る
- d_between_real / d_between_shuffled 比較
- v1111b で「real ≈ shuffled」だったが、タイミング混入下の結果。タイミング固定で測り直す。

---

## 4. 確認 4: self 床

**組める**、injected_self を 1 つ作るだけ。

```python
# self 床 = injected_self (Other 通さず狙った node 直接 inject) の ΔP
# 各 atom で 1 つ
def self_floor_distance(dp_other, dp_self):
    """Other が self 床からどれだけ離れるか"""
    return distance_pair(dp_other, dp_self)
```

- atom ごとに self 床 ΔP_self を取得
- 各 Other について cos(ΔP_other, ΔP_self) と norm distance を記録
- 「Other が self 床から離れる向き・量が特徴的か」を §2.3 で観察

---

## 5. 確認 5: 別 w でロバスト性

**組める**、別 W_INJECT で同じ比較を回す。

- main: W_INJECT=2 で 24 tasks
- robustness: W_INJECT=3 で 24 tasks (別 run、独立完結)
- **W_INJECT 間の比較を物差しに使わない** (これが v1111b の失敗)
- 各 w 内で結論 (atom 横断一貫性 / real>shuffled / self 床) が成立するかを独立に判定
- 両 w で結論が一致 → 結論ロバスト
- 不一致 → タイミング依存

---

## 6. 実装構成

### 6.1 Tasks (per W_INJECT)

| condition | 数 / atom | 内訳 |
|---|---|---|
| baseline | 1 | Other/wi 不要 |
| injected_self | 1 | wi=W_INJECT 固定、Other 不要 |
| injected_other | 3 | 3 Other |
| shuffled_other | 3 | 3 Other |
| 計 / atom | 8 | |

3 atom seeds × 8 = **24 tasks per W_INJECT**

### 6.2 並列

- Pool(24) で 24 tasks 同時実行 (1 Wave)
- 推定 ~15 分 (Step 1 の k=5 観察時間と類推)
- ロバスト性 (W_INJECT=3): 別 run で 24 tasks、+~15 分
- 合計 main + robustness ≈ **30 分**

### 6.3 集計

各 W_INJECT で:
- §2.1 atom 横断一貫性: 各 Other で cos 距離 (3 atom 間ペア)
- §2.2 real vs shuffled: d_between cos
- §2.3 self 床: 各 Other の self 床からの cos 距離

両 W_INJECT で結論一致するか比較。

---

## 7. 規律遵守

| 規律 | 確認 |
|---|---|
| **δ_repeat 作らない** | ✓ タイミング固定で人工的反復ブレなし |
| **factor 不使用** | ✓ 距離は生の cos、相対比較のみ |
| **固定値ゼロ** | ✓ W_INJECT は実験定数 (N=5000 同列)、閾値でない |
| 物理層 frozen | ✓ |
| 同型 + 物理切らない | ✓ stress=True |
| 書込 source_event 1 本 | ✓ |
| トリガー固定しない | ✓ |
| 単一 seed 絶対視しない | ✓ 3 atom 横断 |
| **判定置かない** | ✓ |
| 新しい問い足さない | ✓ 同じ駆動 1 文「出口偏りの形が Other 次第か」、参照点を変えただけ |

---

## 8. 一文サマリ

v1111b 計測修正 Code A 確認 5 点回答 (2026-06-02、Web Claude δ_repeat 捨て系が出す参照点で測り直し設計) — (1) タイミング固定: W_INJECT=2 で 24 tasks、ロバスト性は別 W=3 で 24 tasks、各 w 内完結 / (2) atom 横断一貫性: 変位 V_other = ΔP(other) - ΔP(self) を atom=42/100/200 で取り cos 距離小なら向き一貫 = Other 中身署名 / (3) real vs shuffled 同タイミング: d_between_real vs d_between_shuffled、shuffle seed は (atom×13+other+7) で state 由来 / (4) self 床: injected_self の ΔP を atom ごとに 1 つ、各 Other の cos 距離 + norm 距離記録 / (5) 別 w ロバスト性: W_INJECT=3 で独立 run、両 w で結論一致確認、w 間差は物差しに使わない、実装構成は per W_INJECT で 3 atom × 8 conditions = 24 tasks Pool(24) 1 Wave 推定 15 分 + ロバスト性 15 分 = 30 分、δ_repeat 作らず固定値・factor 完全ゼロ、書込み unified/attention_center_prep/ 配下のみ。

---

**確認回答 end. 実装に進む (W_INJECT=2 main 24 tasks、結果見てから W=3 ロバスト確認)。**
