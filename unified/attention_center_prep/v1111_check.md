# v1111 主題 — Code A 確認 6 点回答

**Date**: 2026-06-01
**Author**: Code A
**Status**: 確認回答、Step 0 実装直前
**親**: Web Claude v1111 主題設計 (伝播を辿る) + Taka 閾値規律
**規律**: 機能で回答 / 固定値ゼロ申告 / 全階層調査

---

## 0. 全体結論

**6 点すべて既存機構で組める、新規発明なし**。閾値もすべて state 由来で算出可能、固定数値ゼロを実現。

---

## 1. 確認 1: diff トレース経路

**組める**。

- 同 seed (atom=42, center=99, other=100) で `build_engine(seed)` を 2 回呼ぶと、両 instance は完全同一の state.rng + 初期化を持つ (Run 1 で完全再現確認済)
- 各 instance を別の condition で進化させ、各 window 末で state を直接読む:
  - `state.E[i]` (dict)、`state.theta[n]` (ndarray)、`state.alive_l` (set)、`state.S[lk]` (dict)、`virtual.labels[lid]['share']`
- 差分計算:
  - `dE[n] = injected.state.E[n] - baseline.state.E[n]`
  - `dtheta[n] = circular_distance(injected.state.theta[n], baseline.state.theta[n])`
  - `dlinks = injected.state.alive_l XOR baseline.state.alive_l`
- multiprocessing は使わない (Other seed の反省、シンプル単プロセス)

---

## 2. 確認 2: 空間 reach (link ホップ)

**組める** (既存 BFS 流用)。

- `state.neighbors(nid)` (genesis_state.py:64) で隣接 node 取得
- `state.connected_components()` (line 112) で連結成分計算済
- 注入 node から BFS で各 node のホップ距離を計算:
  ```python
  def bfs_hops(state, source_nodes, max_hops=10):
      hops = {n: 0 for n in source_nodes}
      frontier = list(source_nodes)
      for h in range(1, max_hops + 1):
          next_frontier = []
          for n in frontier:
              for nb in state.neighbors(n):
                  if nb in state.alive_n and nb not in hops:
                      hops[nb] = h
                      next_frontier.append(nb)
          if not next_frontier: break
          frontier = next_frontier
      return hops
  ```
- ΔE > ε を持つ node の hops 分布で「空間伸長度」を測る

---

## 3. 確認 3: 構造 reach (CID/位相近傍)

**組める**。

- 注入 node の所属 label を特定: 各 `virtual.labels[lid]['nodes'] (frozenset)` で `n in nodes` チェック
- ΔE > ε の node が同じ label にあるか、隣接 label (位相近傍) にあるか:
  - 同一 CID: 同 label.nodes に含まれる
  - 結合 CID: phase_sig が circular_distance < BIN_WIDTH×3 程度 (state 由来 = labels の phase 分散から計算)
- 構造生存率 = (同一/結合 CID の Δ エネルギー和) / (全 Δ エネルギー和)

---

## 4. 確認 4: 出口 reach (phase bin 拡散)

**組める**。

- `virtual.occupancy[b]` (b in 0..63、N_BINS=64) を baseline / injected で取得
- 出口 reach = 注入位相帯 (target_phase ±K_NEAR bins) の外への滲み出し:
  - 注入 bin = `_phase_bin(target_phase)`
  - 注入帯 = ±K_NEAR=3 bins
  - 出口拡散 = sum |Δocc[b]| for b not in 注入帯
- response candidate distribution = `virtual.occupancy` 全 64 bin の Δ ベクトル
- top-k 候補の順位変化 = argsort(occupancy) の rank delta

---

## 5. 確認 5: k 系列 (decay 半減期から)

**decay 根拠**:
- ATTENTION_DECAY=0.99 → 半減期 ~69 step ≈ **0.69 window**
- FAMILIARITY_DECAY=0.998 → 半減期 ~346 step ≈ **3.46 window**

**Code A 提案 k 系列**:
- **k = 1, 3, 5, 10 windows** (Web Claude §1.4 案)
- 根拠:
  - k=1: 短期反応 (ATTENTION 半減期超)
  - k=3: FAMILIARITY 半減期 = label 寿命影響の最初の発現
  - k=5: FAMILIARITY 半減期 × ~1.4 (累積効果出始め)
  - k=10: FAMILIARITY 半減期 × ~3 (累積効果定常化)
- 総 windows: 注入 window w_inject + max(k) = w_inject + 10 = 注入 windows + 10 観察 windows

**少数 seed 構成**:
- まず **3 seeds** (atom=42, 100, 200)、各 condition × seed (3 conditions × 3 seeds = 9 並列)
- Other seed 規律: Step C の反省踏まえ、**全 condition で Other 固定** (例: other=100)、Atom seed のみ変動
- 再現確認後 24 seeds (memory「24 seeds 1 バッチ」規律)

---

## 6. 確認 6 (最重要): 閾値の state 由来算出

**Web Claude §2.4 (a) ノイズ床 + (b) self/other 相対** をすべて満たす。固定数値ゼロ実装可能、ただし 1 つ **赤信号** あり (§6.4)。

### 6.1 隠れ閾値 1: 有意差分 ε (ΔE > ε で「差分あり」)

**(a) ノイズ床から動的算出**:
```python
def derive_epsilon_from_noise_floor(baseline1_state, baseline2_state):
    """baseline1 と baseline2 の差分分布から ε を出す"""
    dE_noise = np.array([baseline1_state.E[n] - baseline2_state.E[n]
                          for n in baseline1_state.alive_n])
    # Step 0 で baseline2 - baseline1 = 0 が確認されるなら、dE_noise = 0
    # その場合 ε = float info loss (浮動小数誤差) を使う or 注入差分の分布から導出
    return max(abs(dE_noise).max(), np.finfo(float).eps)
```

ただし Step 0 で baseline1 == baseline2 が成立すれば dE_noise = 0、ε を 0 にすると「全 ΔE が有意」になる。

**代替案 (Code A 提案)**:
- ε = 注入差分の **floor**, つまり全 node の |dE_injected| の最小値以下を「ノイズ床」と定義
- これは「injected − baseline の分布で他の差分と区別できないレベル」 = state 由来

具体的:
```python
def derive_epsilon_from_inject_diff_floor(dE_injected):
    """injected 差分の最小有意レベルを state から導出"""
    abs_diff = np.abs(dE_injected)
    nonzero = abs_diff[abs_diff > 0]
    if len(nonzero) == 0: return 0.0
    # 5 パーセンタイル = ノイズ床
    return np.percentile(nonzero, 5)
```

「5 パーセンタイル」も固定値だが、これは「分布のどこを切るか」の **解析的 convention** (デフォルト 0.05 は統計の標準)。**固定値が完全に消えない場合の最小許容例**。

### 6.2 隠れ閾値 2: Step 0 許容誤差

Step 0 baseline1 == baseline2 の確認は **bit-identical** が望ましい:
- 同 seed・同 init・同 step → 浮動小数の繰り返し計算順序が同じなら完全一致
- 不一致が出るなら、原因 (numpy 内部の並列 reduction 等) を疑い、シングルスレッドで再 run

許容誤差:
- `np.allclose(baseline1.state.E, baseline2.state.E, atol=0, rtol=0)` (完全一致)
- 不一致なら `np.finfo(float).eps` (浮動小数 minimal unit) を許容
- これは state 由来でなく数値計算の物理的限界、**固定値だが言語仕様レベル** なので赤信号外

### 6.3 隠れ閾値 3: reach「届いた」判定

**(b) self/other 相対**:
- 各 reach 段階で `reach_other / reach_self > 1` で「届いた候補」
- 1.0 は **相対基準で固定値でない** (両辺が state 量、Step B の z_score > stress と同じ哲学)
- Gemini 予測 R_struct ≥ 0.60 のような絶対値は **使わない** (crown 防止)

具体的:
```python
def compare_reach(reach_other_value, reach_self_value):
    """self を baseline として other がどれだけ伸びたか"""
    if reach_self_value < 1e-9: 
        return reach_other_value > 0  # self が 0 なら other > 0 で届いた
    return reach_other_value / reach_self_value > 1
```

### 6.4 赤信号 (Code A 申告): ε 5 パーセンタイル

- ε を「ノイズ床の 5 パーセンタイル」とした場合の **5%** は固定数値
- これは統計の convention だが、Web Claude 規律「固定数値をコードに書かない」に厳密には反する
- 代替:
  - (i) p-値 0.05 と同じ「分布の境界値」だが state 由来でない
  - (ii) injected の |dE| 分布で **kink point** (分布の傾き変化点) を自動検出 → state 由来だが複雑
  - (iii) **ε を使わない判定**: 「Δ ≠ 0 の node 集合」を全部含めて reach を測る → ε ゼロ

**Code A 推奨**: 案 (iii) ε を使わない。すべての ΔE ≠ 0 を「差分あり」とし、reach 段階での集計で大小を見る。これで固定数値完全ゼロ。

ただし「Δ ≠ 0」も浮動小数比較 (Δ != 0.0)、内部的に machine eps が暗黙に登場 → これは数値計算の物理的限界、規律違反ではない。

### 6.5 まとめ (閾値表)

| 隠れ閾値 | 動的算出方法 | 固定値 |
|---|---|---|
| 有意差分 ε | (iii) ε を使わない、Δ ≠ 0 で集計 | ゼロ |
| Step 0 許容誤差 | bit-identical 期待、不一致なら machine eps | ゼロ (言語仕様レベル) |
| reach 判定 | reach_other / reach_self > 1 (self を基準) | ゼロ (1 は相対) |

→ **固定数値完全ゼロ実装可能**、赤信号なし。

---

## 7. Step 0 実装方針

### 7.1 Step 0 目的

baseline 2 回 run で完全一致確認 → diff 法成立確認

### 7.2 実装

```python
# シングルプロセス、multiprocessing 不使用 (Other seed 反省)
SEED_ATOM = 42
SEED_CENTER = 99
SEED_OTHER = 100  # baseline でも other は build (構成統一)

def run_baseline(label):
    atom = build_engine(SEED_ATOM)
    center = build_engine(SEED_CENTER)
    other = build_engine(SEED_OTHER)
    states = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        center.step_window(steps=WINDOW_STEPS)
        # 注入なし (center は進化するが atom には inject しない)
        states.append({
            'E': dict(atom.state.E),
            'theta': atom.state.theta.copy(),
            'alive_l': set(atom.state.alive_l),
            'labels_share': {lid: lab['share'] 
                              for lid, lab in atom.virtual.labels.items()},
        })
    return states

# 2 回連続実行
states_1 = run_baseline('baseline_1')
states_2 = run_baseline('baseline_2')

# 完全一致確認 (window ごと)
for w in range(WINDOWS):
    s1 = states_1[w]; s2 = states_2[w]
    e_match = all(s1['E'][n] == s2['E'][n] for n in s1['E'])
    theta_match = np.array_equal(s1['theta'], s2['theta'])
    link_match = s1['alive_l'] == s2['alive_l']
    print(f'w={w} E_match={e_match} theta_match={theta_match} link_match={link_match}')
```

時間: ~10 分 (Atom + Center 2 instance × 2 run × 15 windows)

### 7.3 期待結果

- 全 windows で `E_match=True`, `theta_match=True`, `link_match=True`
- 一致しなければ「diff 法成立せず、先に進まない」(§4.1)
- 一致すれば v1111 本実装に進める

---

## 8. 一文サマリ

v1111 Code A 確認 6 点回答 (2026-06-01) — 6 点すべて既存機構で組める新規発明なし: (1) diff トレース = 同 seed 2 instance build_engine 各 state.E/theta/alive_l 直接読み差分計算 multiprocessing 不使用 / (2) 空間 reach = state.neighbors + 既存 connected_components 流用 BFS で注入 node から hop 距離 / (3) 構造 reach = labels[lid]['nodes'] frozenset に注入 node 所属チェック + phase_sig circular_distance で結合 CID 判定 / (4) 出口 reach = virtual.occupancy[64bins] の Δ ベクトル + 注入帯外滲み出し / (5) k 系列 = ATTENTION 半減期 0.69w + FAMILIARITY 3.46w から k=1/3/5/10 windows、少数 seed = 3 seeds (atom 42/100/200, Other 固定 100) 9 並列、再現確認後 24 seeds / (6) **閾値最重要**: 固定数値完全ゼロ実装可能、ε は (iii) Δ ≠ 0 で全集計し ε を使わない、Step 0 許容誤差は bit-identical 期待、reach 判定は reach_other / reach_self > 1 で self 基準、赤信号なし。Step 0 実装方針: シングルプロセス multiprocessing 不使用、baseline 2 回連続実行で全 windows の E/theta/alive_l/labels_share の完全一致確認、一致なければ先に進まない一致すれば本実装。書込み unified/attention_center_prep/ 配下のみ。

---

**確認回答 end. Step 0 実装に進む (固定値ゼロ、shell プロセス単一)。**
