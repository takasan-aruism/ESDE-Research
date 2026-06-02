# v1111e 作り直し — いま走っている処理の具体説明 (Taka 向け)

**Date**: 2026-06-02
**Author**: Code A
**目的**: 何をどう動かしているか、コードを読まなくても分かるように説明

---

## 1. 全体像

### 1.1 用意する V82Engine instance (3 種類)

```
[Atom 系]     V82Engine + VirtualLayerV9    seed=1000〜1023 (24 種)
              役割: 観察対象。Other の中身が出口に届くかをここで測る

[Center]      V82Engine + VirtualLayerV9    seed=2000〜2023 (24 種、Atom と 1:1)
              役割: 注意の起点。「いつ・どの phase を狙うか」を出す

[Other 系]    V82Engine + VirtualLayerV9    seed=100, 101, 102 (3 種)
              役割: 別系の中身を生む。注意の橋渡し先
```

3 instance とも同じ V82Engine (N=5000 ノード) + VirtualLayerV9 + run_injection() で起動。**違うのは seed だけ** (同型 fork)。

### 1.2 やる実験の単位

24 種類の Atom seed × 8 種類の条件 = **192 個の task** を Pool(24) で 8 Wave 並列実行。

8 種類の条件:
| 条件 | 中身 |
|---|---|
| baseline | Atom 単独で 7 window 動かすだけ (Center も Other も使わない、注入なし) |
| injected_self | Atom + Center、W=2 で Center が決めた phase を Atom に直接 inject |
| injected_other × 3 Other | 3 instance 全部、W=2 で「Center → Other 経由 → Atom」のフルループ |
| shuffled_other × 3 Other | 同上、ただし Other → Atom の書き戻し時に Other の phase 分布を **乱数で置き換える** (中身を捨てる) |

---

## 2. 1 つの task のタイムライン

1 task = 1 engine instance を 8 window 動かして、特定の 1 window で「**注入**」を入れる。

### 2.1 共通の進行

```
window 0       Atom 系を 100 step 進める
window 1       Atom 系を 100 step 進める
window 2       Atom 系を 100 step 進める ← W_INJECT、ここで注入が起きる (baseline 以外)
window 3       Atom 系を 100 step 進める ← 注入後 1 window
window 4       Atom 系を 100 step 進める
window 5       Atom 系を 100 step 進める
window 6       Atom 系を 100 step 進める
window 7       Atom 系を 100 step 進める ← W_INJECT + K_OBSERVE = 2+5、ここで観察
```

- 1 window = 100 step、その中で物理層 (theta, E, link) が進化する
- Center / Other がある条件は、両者も毎 window 100 step ずつ並行進化
- 注入は window 2 で 1 回だけ
- window 7 で Atom 系の `virtual.occupancy` (= phase 64 bin の現在の埋まり具合) を記録 → 後で解析に使う

### 2.2 1 task の実行時間

- Atom 単独 (baseline): 約 6-7 分 (起動 60 秒 + 8 window × 30-40 秒)
- 3 instance フル (injected_other / shuffled_other): 約 13-14 分

---

## 3. window 2 で起きる「注入」の具体動作

ここが今回のミスを直した部分。**3 本足の配管**を順に通す。

### 3.1 baseline (注入なし)

何もしない。Atom 系がそのまま 100 step 進化するだけ。

### 3.2 injected_self (Center が決めて Atom に直接)

```
[Center]                                    [Atom 系]
  ↓ 100 step 進化済                            ↓ 100 step 進化済
  
  足 1: Center → Atom 読み
  ───────────────────────────────────────────→
  「Center の E が高い上位 5 ノードの theta の円周平均」 = tp_in (一点)
  この tp_in が「今ここを見ろ」というテーマ
  
  Atom 系の各 label について重み計算:
    w(label) = exp(- λ_in × phase距離(label.phase_sig, tp_in))
    ※ λ_in は Center の labels の phase 分散から動的に計算
  
  重みの高い上位 5 ノード (Atom 自身の label の core node) を選び、
  そこに physics.inject (E を 0.6 加算 + 近傍にリンク作成)
```

つまり「Center が示したテーマに近い Atom の label を狙って、Atom 自身を inject」。Other は使わない (これが self の意味)。

### 3.3 injected_other (フルループ、3 本足全部)

```
[Center]                  [Other 系]                  [Atom 系]

足 1: Center → Atom 読み (上の self と同じ)
tp_in = Center 由来のテーマ (一点 phase)

足 2: テーマを Other に渡し、Other 自身を立てる ← ★ここを直した
                                                    
[Other の各 label] について重み計算:
  w_other(label) = exp(- λ_in_other × phase距離(label.phase_sig, tp_in))
  ※ λ_in_other は Other の labels の phase 分散から動的に計算
  
重みの高い上位 5 ノード = Other 自身の node を選び、
                          ──────────────
Other に physics.inject (Other の node 番号、Atom の node ではない)
        ↓
Other を 5 step 進化させる (テーマで突かれた Other が反応する)
        ↓

足 3: Other の中身を Atom の出口に翻訳して書き戻し

Other の active node 全部について E と theta を集める
[Atom の各 label] について励起度を計算:
  excitation(label) = Σ_n E[n] × exp(- λ_out × phase距離(label.phase_sig, theta[n]))
  ※ n は Other の active node 全部 (5000 ノード規模)
  ※ λ_out は Other の labels の phase 分散から動的に計算
  ※ 一点の Center テーマと違って、Other の分布全体で Atom label を励起
  
励起度の高い上位 5 ノード = Atom 自身の core node を選び、Atom に physics.inject
```

**3 本足ともテーマ phase で照合 + exp(-λd) カーネル + 各系自身の node を inject**。番号を他系に渡さない。

### 3.4 shuffled_other (中身だけ捨てる)

```
足 1: Center → Atom 読み (同じ)
足 2: テーマ phase を Other に渡し、Other 自身を立てて inject (injected_other と同じ)
       ↓
       Other を 5 step 進化させる (同じ)
       ↓
足 3: ★ここだけ違う

Other の active node の E 重みは保つが、theta だけ乱数で置き換える:
  theta_random[n] = uniform(0, 2π)   ※ seed = (atom_seed × 13 + other_seed + 7) で決まる
  
[Atom の各 label] について励起度:
  excitation(label) = Σ_n E[n] × exp(- λ_out × phase距離(label.phase_sig, theta_random[n]))
                                                                         ─────────
                                                                         乱数化された theta
励起度上位 5 ノード = Atom 自身を inject
```

意図: 足 1・足 2 は injected_other と完全に同じにして、**足 3 の「Other の phase 分布の中身」だけ捨てる**。これで「Other の中身が出口に効いているか」が分離される。

---

## 4. 観察と集計

### 4.1 各 task で取るもの

window 7 の時点で、Atom 系の `virtual.occupancy` を 1 個だけ記録する。

occupancy は phase 64 bin (0〜2π を 64 等分) の現在の埋まり具合。各 bin に label がどれだけ立っているかの数値ベクトル (64 次元)。

これを 192 個分集める → 192 × 64 = 12288 個の数値。

### 4.2 ΔP (差分) の計算

各 Atom seed について、baseline (注入なし) の occupancy を基準にして差分を取る:

```
ΔP_self  = injected_self の occupancy − baseline の occupancy   (各 atom で 1 個)
ΔP_other = injected_other の occupancy − baseline の occupancy  (各 atom × 3 Other で 3 個)
ΔP_shuf  = shuffled_other の occupancy − baseline の occupancy  (各 atom × 3 Other で 3 個)
```

各 ΔP は 64 次元ベクトル (phase 分布の「動き」の方向)。

### 4.3 主役 §2.1 「24 atom 横断一貫性」

各 Other について、「Other の中身に由来する変位」を抜き出す:

```
V_other = ΔP_other − ΔP_self    (各 atom × 3 Other で 3 個)
V_shuf  = ΔP_shuf  − ΔP_self    (各 atom × 3 Other で 3 個)
```

V は「Center が決めた狙い (self) を差し引いた、Other の中身が足した分」。

これを 24 atom seed で集めて、**全ペア (24×23/2 = 276 ペア) の cos 距離** を取る:

```
cos(V[atom_i], V[atom_j]) = 1 − dot(V[i], V[j]) / (|V[i]| × |V[j]|)
```

- cos = 0 → 完全に同方向 (一貫)
- cos = 1 → 直交 (向きが無関係)
- cos = 2 → 反対方向

これを Other ごと、injected と shuffled で別々に計算 → **6 つの数字**:

```
injected_cos(Other=100), injected_cos(Other=101), injected_cos(Other=102)
shuffled_cos(Other=100), shuffled_cos(Other=101), shuffled_cos(Other=102)
```

### 4.4 inversion 判定 (主役の判定)

各 Other について「injected_cos < shuffled_cos か」を判定:

```
inversion(Other=100) = (injected_cos(100) < shuffled_cos(100))
inversion(Other=101) = (injected_cos(101) < shuffled_cos(101))
inversion(Other=102) = (injected_cos(102) < shuffled_cos(102))
```

意味: injected の方が cos が小さい = injected の方が atom 横断で一貫している = Other の中身が seed 共通の変位方向を生んでいる。

**3 Other 中で inversion が何回出るか** が判定:
- 3/3 → 強再現性、共通の足跡確定 → 第二段 (Other ごとの個性) へ進める
- 2/3 → 中
- 1/3 → 弱
- 0/3 → 共通の足跡なし、別の経路を疑う

### 4.5 §2.2 / §2.3 (補足、今は判定に使わない)

- §2.2: 同じ atom 内で 3 Other 間の cos 距離 (Other 個性)
- §2.3: 各 Other が self 床からどれだけ離れるか

これも parquet に保存するが、Web Claude の二段手順では「§2.1 共通が固まってから読む」と決めているので、今回は計算するだけで判定には使わない。

---

## 5. 期待される動き (見当、合否ラインでない)

### 5.1 もし Other の中身が Atom 出口に届いているなら

- 同じ Other (例 Other=100) は、どの Atom seed でも似た phase 帯を励起する
- → 24 atom の V_other(100) が似た方向を向く
- → 全ペア cos が小さい
- → injected_cos が小さくなる
- 一方 shuffled_other は中身を捨てているので、24 atom で V_shuf がバラバラ
- → shuffled_cos は cos~1 (直交)
- → **injected_cos < shuffled_cos の inversion が 3 Other 全部で出る**

### 5.2 もし届いていないなら

- V_other は各 atom seed で独自方向 (Atom 系の内部進化に支配される)
- V_shuf も同様
- 両者の cos が同じくらい (両方 cos~1)
- → inversion が 3 Other で揃わない

---

## 6. 旧 v1111e (足 2 が番号コピー) との違い

| 場所 | 旧 v1111e | 作り直し v1111e |
|---|---|---|
| 足 2 で Other に inject する node | Atom 側で選んだ node の ID | **Other 自身の label から phase 一致率で選んだ node** |
| Other が受け取るもの | Atom の node 番号 (Other 空間では無意味) | **テーマ phase に近い Other 自身の node** |
| 期待効果 | Other は意味のない刺激を受ける | **Other は「これを見ろ」というテーマを自分の構造で受け止める** |

旧版では Other の中身が「何でもない突き」で揺さぶられていたので、Other → Atom 書き戻しで何を見ても解釈不能だった。直した版で初めて「Other がテーマで反応した結果」を Atom に書き戻している。

---

## 7. いま実行中の規模と時間

| 項目 | 値 |
|---|---|
| Tasks | 192 (24 atom × 8 条件) |
| 並列 | Pool(24)、8 Wave |
| 1 task | 約 13-14 分 |
| 全体 | **約 1.5-2 時間**、24 cores 並列 |
| 出力 | run_v1111e_redo/ 配下に parquet 群 |

主役の結論は「3 Other 中の inversion が何回出るか」。サブグループ確認 (8 atom × 3 group = 9 サブグループ) も併記。

---

## 8. 終わったら出すもの

1. inversion 数 (3/3, 2/3, 1/3, 0/3 のどれか)
2. injected_cos / shuffled_cos の絶対値 (cos~1 なら向きが揃っても弱い)
3. 旧 v1111e (1/3、gap -0.0009) との比較
4. §2.2 / §2.3 は parquet に保存するだけ (二段手順遵守、判定不使用)

→ Web Claude が結果を読んで次の機能設計、Taka が主題評価。

---

*以上、いま走っている v1111e 作り直しの具体処理。3 本足 (Center→Atom 読み / Atom→Other 注入 / Other→Atom 書き戻し) を全部 phase テーマで揃え、24 atom seed で seed 共通の inversion が出るかを見る。1.5-2 時間後に結果が出る。*
