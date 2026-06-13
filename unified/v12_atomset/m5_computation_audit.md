# v12 Atomset — 実コードの計算方法まとめ（Web Claude 精査用）

日付: 2026-06-13 / Taka 問い「生まれた時の特性＋環境要因＋一致率の前提なのに、なぜ差が出ない？」
→ **実コード（`m5_substrate_atom.py`）で何をどう計算しているかを忠実に記述**。記憶でなくコード。

## 0. 結論（先に）

- **Taka の記憶が正しい**。設計の核は「**一致率（atomset プロファイル）を経験で更新し続ける：新しい一致率 = 元の一致率 ×(1+特徴度)**」だった（`experience_computability_audit.md`）。
- **しかし実コードにこの「一致率の更新ループ」は入っていない。** 実装は次の3つが**バラバラ**:
  - ① 生まれた時の特性 = 誕生時 atom（n_core+phase_sig から固定、**以後不変**）
  - ② 環境要因 = atom_rate（経験の蓄積、**per-Atom 群**）
  - ③ 一致率 = phase 一致率 exp(-λ·d(phase_sig, …))（**phase_sig は誕生時固定**、経験で更新されない）
- **①②③ が結合して「進化する一致率」になっていない。** cid の identity（phase_sig）は誕生時に凍結、経験はそれを更新せず別チャネル（torque 係数等）で乗るだけ。→ **経験が cid の一致率/identity を作り替える経路が無い＝差が cid 特異に出ない。**

---

## 1. ① 生まれた時の特性（atom 割当）— `rank1_atom()` 

```python
n = len(label['nodes'])          # n_core (構造サイズ)
ps = label['phase_sig']          # 誕生時の位相署名
vec = zeros(48)
vec[7 + min(max(n-2,0),5)] = 1.0       # scale 軸: n_core で one-hot (6 段)
vec[min(int(|ps|/π * 7), 6)] = 1.0     # temporal 軸: |phase| で one-hot (7 段)
atom = argmax(ATOM_MATRIX @ vec/|vec|) # 48d を atom_centroids に cosine、最近接 atom
```

- **入力は (n_core, phase_sig) の 2 つだけ。** 48 次元中 2 次元しか立たない（残り 46 はゼロ）。
- → **誕生時 atom は (n_core × phase) の粗い 2D 写像。実測で異なる atom は 8-10 種**。
- **この atom は誕生時に一度決まり、以後不変**（`H['cid_atom']` に固定、更新コード無し）。
- ＝「静的素質」。だが **2 量しか使わない**ので、cid の豊かな個性を担えない。

## 2. ② 環境要因（経験 = atom_rate）— `cid_boost()` + atom 集約

**入力軸**（`cid_axis_values`、v2 で lifespan 除去）:
```python
{n_core, C(意識資源), fam_mean(親密度平均), n_partners(相手数), att_entropy(注意エントロピー)}
```

**per-cid 経験強度**（`cid_boost`、robust_z）:
```python
for axis in AXES:
    value = |v - runmean[cid][axis]|                       # その軸の「動き」
    f = clip((value - median(buf)) / max(10*MAD(buf), 1e-3), ±4)   # 個体内 robust_z (特徴度)
    rate[cid][axis] = max(0.1, (1 + 0.97*(rate-1)) * (1 + 0.5*f))   # 衰退+驚きで更新
boost[cid] = mean over axes of (rate[cid][axis] - 1)        # その cid の経験強度
```

**per-Atom 集約**（環境要因を atom 群に集める）:
```python
atom_rate[a] = 1 + 0.9*(atom_rate[a]-1) + 0.5 * mean(boost of その atom の cid 群)
```

- **特徴度（robust_z f）は per-cid per-axis で計算されている**（Taka の「特徴度」はここ）。
- **だが boost を atom に集約して atom_rate にする**＝**個体の経験を群（atom）に均す**。同 atom の cid は同じ atom_rate を共有（per-Atom 主体、筋3 で選んだ）。
- → **cid 固有の経験が atom 群レベルに均され、cid 特異性が消える。**

## 3. ③ 一致率（match rate）— phase 一致率 exp(-λ·d)

**橋 addressing / 出力励起の両方で使う**（`m5_substrate_atom.py:158, 349`）:
```python
w[lid] = exp(-λ · d(label['phase_sig'], theme_phase))    # 入力: どの cid に入力が降るか
exc[cid] = Σ_n E[n] · exp(-λ · d(phase_sig or cpa, θ[n])) # 出力: cid の励起
```

- **これが「一致率」。だが d() の基準は `phase_sig`＝誕生時固定の位相署名。**
- **経験（atom_rate）はこの一致率を更新しない。** phase_sig は誕生時のまま、exp(-λd) の形も固定。
- 出力だけ Gemini 指摘で `current_phase_avg`（今の平均位相）に変えたが、**addressing と atom 割当は依然 固定 phase_sig**。

---

## 4. 設計（あるべき）vs 実装（現状）の乖離 ＝「なぜ差が出ない」のコード的理由

| 設計（Taka/Web Claude、当初） | 実コード（現状） |
|---|---|
| 一致率（atomset プロファイル）を経験で**更新**: `新一致率 = 元一致率 ×(1+特徴度)` | **この更新ループが無い**。一致率(phase exp(-λd))は phase_sig 固定で不変 |
| 特徴度が**一致率そのもの**を動かす | 特徴度→atom_rate に蓄積、**別チャネル（torque 係数等）**で乗るだけ |
| cid の一致率＝cid 固有の進化する identity | cid の identity(phase_sig)は**誕生時凍結**、経験で変わらない |
| 経験は cid 固有 | 経験は**atom 群に集約**（per-Atom）＝cid 特異性が均される |

**コード的な「差が出ない」3 つの理由:**
1. **誕生時特性が 2 量(n_core,phase_sig)で粗い**＝素質の解像度が低い。
2. **経験が一致率を更新せず、atom 群に均される**＝「元の一致率 ×(1+特徴度)」の核が未実装。cid 固有性が消える。
3. **cid の identity(phase_sig)が誕生時固定**＝経験がどれだけ蓄積しても、cid が世界に示す一致率は変わらない。応答(励起)が cid 特異に育たない。

→ **生まれた特性と環境要因が「一致率の進化」として結合していない。3 つが別々に存在し、経験が identity を作り替える経路が無い。** これが「前提（特性＋環境＋一致率）なのに差が出ない」のコードレベルの答え。

---

## 5. Web Claude 精査用の論点

- **設計の核（一致率 ×(1+特徴度) の更新ループ）を実装すべきでは？** 現状は特徴度→atom_rate→torque係数 にすり替わっている。一致率（cid の atom alignment）そのものを経験で更新し、それが addressing/出力に直結すれば、cid 固有の identity が育つ可能性。
- **誕生時 atom が 2 量で粗い**: n_core+phase_sig でなく、もっと多軸（cid_vec 全体）で誕生時素質を付与すべきか。
- **per-Atom（群）か per-cid（固有）か**: 筋3(per-Atom)を選んだ理由は CID-物理衝突回避だが、cid 特異性を消す副作用。一致率を cid 固有に持ち、文化として atom 経由で緩く共有する二層（筋1+筋3 折衷）が要るか。
- **phase_sig 固定の是非**: cid の identity を経験で更新可能にする（current_phase_avg を addressing/atom にも使う、または一致率を別途持って更新）。

## 参照コード
- `m5_substrate_atom.py`: `rank1_atom`(①)、`cid_boost`+atom集約(②)、`bridge_inject`/出力(③ exp(-λd))
- 設計: `experience_computability_audit.md`(一致率×(1+特徴度))、`m5_typesplit_decay_report.md`、`m5_channel_investigation.md`
