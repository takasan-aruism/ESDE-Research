# v1111e 作り直し — Code A 認識確認 (3 本足の左右対称、最優先)

**Date**: 2026-06-02
**Author**: Code A
**Status**: 認識確認 + 実装直前
**親**: Web Claude 「v1111e 作り直し指示」(足 2 番号コピー欠陥)

---

## 0. 自己点検 — Code A も見逃していた

Code A の前回自己点検 (ATOM_SEEDS 選択ミスを指摘) では、**足 2 (Atom→Other 注入) の番号コピー欠陥に気づかなかった**:

- v1111c で「左右対称チェック」を入口 (足 1) と出口 (足 3) の 2 本足だけで見ていた
- 中央の足 2 (Atom→Other 注入) は v1110 以来 ずっと `targets_in` = Atom 側の node ID を Other に inject していた
- Atom と Other は別 seed (= 別 instance、別 RNG 進化) なので、Atom の node 番号は Other 空間で無意味
- → **Web Claude / Code A 共に 4 連続のチェック (v1111b/c/d/e) で見落とし**

これは規律「左右対称チェックを最初に確認」を **2 本足だけで実施した実装上の誤り**。

---

## 1. 3 本足の左右対称チェック (実装前、必須)

| 項目 | 足 1 (center→Atom) | 足 2 (テーマ→Other) | 足 3 (Other→Atom) | 3 本揃う? |
|---|---|---|---|---|
| 渡すもの | テーマ phase (tp_in) | **テーマ phase (tp_in)** | テーマ (Other phase 分布) | ✓ 番号なし |
| 照合 | phase circular distance | phase circular distance | phase circular distance | ✓ |
| カーネル | exp(-λd) | exp(-λd) | exp(-λd) | ✓ |
| **inject 先 node** | **Atom 自身 (injected_self)** | **Other 自身** | **Atom 自身** | ✓ 各系が自分の node を立てる |
| λ 出所 | state (center) | state (other) | state (other) | ✓ 全部 state 由来 |

→ **3 本足とも揃う、どこにも他系 node 番号のまたがりなし** ✓ 赤信号なし

---

## 2. 確認 1: 足 2 の inject node は Other 自身か

### 2.1 現 v1111e (欠陥)

```python
# 足 1: center → Atom 読み
weights_in = label_weights_point(atom, tp_in, lam_in)  # Atom label を tp_in 一致率
targets_in = targets_from_w(weights_in, atom, K)  # ← Atom の core node

# 足 2: ★欠陥
other.physics.inject(other.state, target_nodes=list(targets_in))  # ← Atom の node 番号を Other に
```

`targets_in` は `targets_from_w(weights_in, atom, ...)` で **Atom の node ID**。
それを `other.physics.inject(target_nodes=targets_in)` で Other に渡す → 番号コピー。

### 2.2 v1111e 作り直し (修正)

```python
# 足 1: center → Atom 読み (変更なし)
weights_in = label_weights_point(atom, tp_in, lam_in)
targets_in = targets_from_w(weights_in, atom, K)  # ← Atom の core node (injected_self で使う)

# injected_self の場合 (足 2/3 なし、Atom に直接 inject、変更なし)
if cond == 'injected_self':
    atom.physics.inject(atom.state, target_nodes=targets_in)

# 足 2 (修正): テーマ phase を Other に渡し、Other 自身の node を立てる
elif cond in ('injected_other', 'shuffled_other'):
    lam_in_other = lam_dyn(other)  # ← Other 側の state 由来 λ
    weights_in_other = label_weights_point(other, tp_in, lam_in_other)  # ← Other label を tp_in 一致率
    targets_in_other = targets_from_w(weights_in_other, other, K)  # ← Other の core node
    if targets_in_other:
        other.physics.inject(other.state, target_nodes=targets_in_other)  # ← Other 自身の node
        other.step_window(steps=OTHER_STEPS)
        # 足 3: 出口 (v1111d 流用、変更なし)
        ...
```

`targets_in_other` は `targets_from_w(weights_in_other, other, ...)` で **Other の node ID**。
これを `other.physics.inject(target_nodes=targets_in_other)` で Other に渡す → Other 自身の node。

**確認**: 足 2 で渡る `target_nodes` は **Other 自身の alive node** (Atom の node でない)、確実に。

---

## 3. 確認 2: 足 2 実装 (テーマ phase 渡す経路)

```python
# 足 2: label_weights_point を Atom 用から Other 用に流用
# label_weights_point(engine, theme_phase, lam) は engine.virtual.labels を見て
# 各 label の phase_sig と theme_phase の cdist を測り、exp(-λd) で重み付け
# → engine=other を渡せば Other の label を tp_in 一致率で重み付け

weights_in_other = label_weights_point(other, tp_in, lam_in_other)
#                                      ^^^^^  ^^^^^
#                                      Other  center のテーマ
#
# Other の各 label について exp(-lam_in_other * cdist(label.phase_sig, tp_in))
# → tp_in 近い phase_sig の Other label が高重み
# → その label の core node を inject 候補に

targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
#                                                  ^^^^^
#                                                  Other の core node を返す
```

これで「テーマ phase (tp_in) を渡し、Other 自身の labels を tp_in に近い phase で立てる」が成立。

---

## 4. 確認 3: shuffled の足 2 も揃える (比較成立)

shuffled_other は「Other の中身を捨てる」が目的。**入口 (足 2) を injected_other と同じにすると、足 3 (出口) の random phase の影響だけ見える**。

```python
elif cond == 'shuffled_other':
    # 足 2: injected_other と同じ (テーマ phase で Other 自身の label を立てる)
    lam_in_other = lam_dyn(other)
    weights_in_other = label_weights_point(other, tp_in, lam_in_other)
    targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
    if targets_in_other:
        other.physics.inject(other.state, target_nodes=targets_in_other)  # ← 同じ Other 自身 node
        other.step_window(steps=OTHER_STEPS)
        # 足 3: random phase 分布 (中身捨て、v1111d shuffle 機構)
        lam_out = lam_dyn(other)
        weights_out = label_excitations_dist_shuf(atom, other, lam_out, sa, so)
        targets_out = targets_from_w(weights_out, atom, K_TARGET)
        if targets_out:
            atom.physics.inject(atom.state, target_nodes=targets_out)
```

入口を揃えないと「injected vs shuffled の比較」が「入口の違い vs 出口の違い」の混合になる。揃えれば足 3 (出口の中身有無) のみの効果。

---

## 5. 確認 4: 他は v1111e のまま (変更なし)

| 項目 | v1111e (現行) | v1111e 作り直し |
|---|---|---|
| ATOM_SEEDS | [1000-1023] | 同 |
| CENTER_SEEDS | [2000-2023] | 同 |
| OTHER_SEEDS | [100, 101, 102] | 同 |
| W_INJECT | 2 | 同 |
| K_OBSERVE | 5 | 同 |
| 3 参照点 (主役 §2.1、§2.2/§2.3 記録のみ) | 同 | 同 |
| 二段手順 | 同 | 同 |

ATOM_SEEDS の v1111d seed 含める議論は、足 2 を直してから (v1111d も同じ番号コピー欠陥の上)。

---

## 6. 確認 5: 固定値ゼロ (lam 全部 state 由来)

| λ | 出所 |
|---|---|
| lam_in (足 1) | compute_lambda_dynamic(center) — center state 由来 |
| **lam_in_other (足 2、新規)** | **compute_lambda_dynamic(other) — Other state 由来** |
| lam_out (足 3) | compute_lambda_dynamic(other) — Other state 由来 |

全 λ が state 由来、固定値・factor なし。**赤信号なし**。

---

## 7. 規律違反の自己点検 (Code A 反省)

| 規律 | v1111c/d/e で違反した? |
|---|---|
| 左右対称チェックを最初に確認 | **△ 2 本足だけで実施、足 2 を見落とし** (Web Claude も Code A も) |
| 番号でなくテーマで運ぶ | **✗ 足 2 で Atom の node 番号を Other に渡していた** |
| 単一 seed 絶対視しない | ✓ 24 atom 横断 |
| 判定置かない | ✓ |
| 固定値ゼロ | ✓ |

→ 「左右対称チェック」を 2 本足で済ませた規律違反の上で、4 連続 (v1111b/c/d/e) の結果が出ていた。**結果は信用できず、保留**。

---

## 8. 一文サマリ

v1111e 作り直し Code A 認識確認 (2026-06-02、Web Claude 指示「足 2 番号コピー欠陥」、3 本足左右対称最優先) — 自己点検 (Code A 前回点検は ATOM_SEEDS ミスを指摘するも足 2 番号コピー欠陥見落とし、v1111c で左右対称チェックを入口出口 2 本足だけで実施し中央の足 2 を見落とし規律違反、Web Claude も Code A も 4 連続 v1111b/c/d/e でチェック漏れ)、3 本足チェック (§1 表で全項目揃う: 渡すものテーマ phase 番号なし / 照合 phase circular distance / カーネル exp(-λd) / inject 先 node 各系自身 / λ 全 state 由来、赤信号なし)、(1) 足 2 inject node = Other 自身確認 (現 v1111e は targets_in = Atom node を other.inject で番号コピー欠陥、修正は label_weights_point(other, tp_in, lam_in_other) → targets_from_w(..., other, ...) で Other 自身 core node)、(2) 足 2 実装はテーマ phase tp_in を渡し Other label を tp_in 一致率で重み付け Atom 用機構を Other に流用、(3) shuffled の足 2 は injected_other と同じテーマ phase で Other 自身 node 立て出口だけ random で比較成立、(4) 他は不変 ATOM_SEEDS[1000-1023]/W_INJECT=2/3 参照点/主役 §2.1/§2.2/§2.3 記録のみ二段手順 v1111d seed 含める議論は足 2 直してから (v1111d も同じ穴)、(5) 固定値ゼロ lam_in/lam_in_other/lam_out 全 state 由来赤信号なし、規律違反反省 (左右対称チェック 2 本足見落とし規律違反 4 連続結果信用できず保留)、書込み unified/attention_center_prep/ 配下のみ、192 tasks Pool(24) 8 Wave 推定 1.5-2 時間。

---

**認識確認 end. 3 本足対称 ✓ → 実装に進む。**
