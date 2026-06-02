# v1111e 第一段 — Code A 確認 5 点回答

**Date**: 2026-06-02
**Author**: Code A
**Status**: 確認回答 + 実装直前
**親**: Web Claude v1111e 設計 第一段 (共通を統計で固める、24 seed で §2.1 inversion 再現)

---

## 0. 全体結論

5 点すべて流用可。配管は v1111d そのまま、24 atom seed に拡張。**§2.1 主役一本に絞る** (§2.2/§2.3 は記録だが判定不使用)。

---

## 1. 確認 1: 24 seed 構成

### 1.1 ATOM_SEEDS / CENTER_SEEDS / OTHER_SEEDS

```python
ATOM_SEEDS = list(range(1000, 1024))    # 24 seeds: 1000-1023
CENTER_SEEDS = list(range(2000, 2024))  # 24 seeds: 2000-2023
OTHER_SEEDS = [100, 101, 102]           # 固定 (v1111c/d 継承)
```

- Atom と Other を完全に重複しない範囲に分離 (前回 atom=100 と Other=100 重複を回避)
- 各 Atom seed sa に対応する Center seed sc = 2000 + (sa - 1000) (1 対 1 対応)

### 1.2 Tasks 構成

24 atom × 8 conditions = **192 unique tasks**:
- baseline 24
- injected_self 24
- injected_other 72 (24 × 3 Other)
- shuffled_other 72 (24 × 3 Other)

### 1.3 並列 + 時間

- Pool(24) で 192 tasks
- 自動で 24 batches (= 192 / 24 = 8 Wave)
- 各 task ~13 分 (v1111d 813s / 24 = 34s? いや 1 task の中で W_INJECT+K_OBSERVE = 8 windows × ~100s = 800s)
- 計算量: 各 task ~800s、8 Wave 並列 → 8 × 800s = **6400s ≈ 107 分 (1.8 時間)**

memory 「24 seeds は 1 バッチ」規律遵守。

---

## 2. 確認 2: §2.1 集計 (向きが seed 群で揃うか、factor なし)

### 2.1 計算

```python
# 24 atom 横断 cos の集計 (per Other × condition)
def compute_atom_consistency_cos(V_per_atom):
    """24 atom の変位ベクトルの全ペア cos (276 pairs = C(24,2))"""
    atoms = sorted(V_per_atom.keys())
    cos_pairs = []
    for i in range(len(atoms)):
        for j in range(i+1, len(atoms)):
            d = distance_pair(V_per_atom[atoms[i]], V_per_atom[atoms[j]])
            cos_pairs.append(d['cos'])
    return {
        'cos_mean': float(np.mean(cos_pairs)),
        'cos_median': float(np.median(cos_pairs)),
        'cos_std': float(np.std(cos_pairs)),
        'cos_min': float(min(cos_pairs)),
        'cos_max': float(max(cos_pairs)),
        'n_pairs': len(cos_pairs),
    }
```

### 2.2 inversion 判定 (factor なし)

```python
# Other ごとに injected_other と shuffled_other の atom 横断 cos を比較
# inversion = injected_cos < shuffled_cos
inversion_per_other = {}
for so in OTHER_SEEDS:
    inj_cos = atom_consistency['injected_other'][so]['cos_mean']
    shuf_cos = atom_consistency['shuffled_other'][so]['cos_mean']
    inversion_per_other[so] = bool(inj_cos < shuf_cos)

# 3 Other 中の inversion 数 (再現性指標)
n_inversion = sum(inversion_per_other.values())
# n_inversion = 3 (3/3 全 Other で inversion) → 強再現性
# n_inversion = 2 (v1111d 3 seeds と同) → 中再現性
# n_inversion = 1 or 0 → 不再現
```

→ 24 seed で 3 Other 中いくつで inversion が出るかが「向きの揃い」指標。**固定閾値・factor 不使用**。

---

## 3. 確認 3: cos 絶対値 (弱さを別途記録)

向きが揃っても cos~1 なら「方向は seed 共通だが弱い」(Web Claude §2)。

```python
# 弱さ記録
weakness = {
    'injected_cos_mean': injected_cos_mean,  # cos~1 なら弱い
    'shuffled_cos_mean': shuffled_cos_mean,
    'gap': shuffled_cos_mean - injected_cos_mean,  # inversion の幅
}
# v1111d 3 atom: injected 0.965 / shuffled 1.019 / gap +0.054 (弱い)
# 24 seed で gap がどうなるか
```

→ 強さは第二段以降の論題、第一段では gap を記録するだけ。

---

## 4. 確認 4: 局所を読まない (§2.1 主役分離)

### 4.1 実装上の分離

- §2.1 計算: メインで実施、結論判定に使う
- §2.2 (Other 間 d_between): 記録するが判定不使用 (parquet に保存)
- §2.3 (self 床): 記録するが判定不使用

### 4.2 結論の書き方

第一段の結論は **§2.1 inversion が seed 群で揃うか** だけで判定:
- 揃う (3/3 Other) → 共通土台確定 → 第二段へ
- 部分的 (1-2/3 Other) → 弱い再現性、Taka 判断
- 揃わない (0/3 Other) → 共通でも届かない、別粒度/経路

§2.2/§2.3 は「土台が固まってから」(Web Claude §3 規律)。

---

## 5. 確認 5: atom 横断 cos の集計 (24 atom)

### 5.1 全ペア平均 vs 代表統計

Code A 推奨: **全ペア平均 + median + std**
- C(24,2) = **276 ペア** per (Other, condition)
- 24 atom 全ペア cos の **mean** が主指標
- median (頑健性確認) + std (バラつき) も記録

### 5.2 グループ分けでの再現性確認 (副次)

```python
# 24 atom を 3 groups (8 seed each) に分け、グループ内 cos 計算
# 3 group で injected < shuffled が何回出るか
group_a = ATOM_SEEDS[0:8]    # [1000-1007]
group_b = ATOM_SEEDS[8:16]   # [1008-1015]
group_c = ATOM_SEEDS[16:24]  # [1016-1023]
# 各 group × Other × condition で cos_mean → inversion 判定
# 3 group × 3 Other = 9 サブグループで inversion 数
```

これで「24 atom 全部」 + 「8 atom × 3 group」の 2 ビューで再現性確認。

---

## 6. 一文サマリ

v1111e 第一段 Code A 確認 5 点回答 (2026-06-02、Web Claude 共通を統計で固める設計、24 seed で §2.1 inversion 再現確認) — (1) 24 seed 構成 ATOM_SEEDS=[1000-1023] / CENTER_SEEDS=[2000-2023] / OTHER_SEEDS=[100/101/102] 完全重複なし、192 unique tasks (3 atom 拡張)、Pool(24) で 8 Wave 並列 推定 1.5-2 時間、(2) §2.1 集計 = 24 atom 全ペア cos 276 pairs の mean を主指標 median + std 副、inversion 判定 = injected_cos < shuffled_cos の 3 Other 中の回数 factor なし固定閾値なし、(3) cos 絶対値 = injected/shuffled cos_mean + gap を記録弱さは第二段以降論題、(4) §2.1 主役分離 = §2.2/§2.3 は記録するが判定不使用 第一段の結論は §2.1 揃うか だけで判定、(5) 24 atom 横断集計 = 全ペア平均主指標 + 8 atom × 3 group のサブグループ再現性確認、Web Claude 不変条件遵守 (物理層 frozen + 同型 + source_event 1 本 + 左右対称 + 固定値ゼロ + 共通固まるまで局所読まない二段手順 + 単一 seed 絶対視しない 24 atom 横断主役 + 判定置かない揃った/揃わない記述 + 駆動 1 文)、書込み unified/attention_center_prep/ 配下のみ。

---

**確認回答 end. 192 tasks 8 Wave 並列、推定 1.5-2 時間で実行。**
