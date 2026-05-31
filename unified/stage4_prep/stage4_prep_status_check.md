# 第 4 段階準備 — 現状確認報告 (Code A、推測ゼロ)

**Date**: 2026-05-31
**Author**: Code A
**Status**: 現状確認のみ、実装ゼロ、Taka 確認待ち
**親**: Web Claude 第 4 段階準備依頼 (2026-05-31)、Taka 「正確には分からん、現状確認、確実に言えることを出す」

---

## 0. 規律遵守

- **わからんことは「わからん」と書く** (推測で埋めない)
- **存在しないと書く前に全階層調べる** (autonomy / primitive / cognition / ecology / developmental / unified 全部 grep)
- 実装ゼロ (本依頼は現状確認のみ)

---

## 1. 存在層 frozenset 条件 (項目 1-4、CID の定め、本命)

### 1.1 項目 1: 定義場所 (確実)

**`primitive/v910/virtual_layer_v9.py:559`**:
```python
self.labels[lid] = {
    "nodes": frozenset(cluster_nodes),
    "phase_sig": phase_sig,
    "share": 0.0,
    "born": window_count,
    "prev_alignment": 0.0,
}
```

frozenset の生成源は 3 か所 (line 504, 526, 559)、すべて `cluster_nodes` から。`cluster_nodes` は 2 つの seed source:
- **island**: `for iid, info in islands.items(): nodes = frozenset(info.nodes); if len(nodes) >= 2:` (line 504-505)
- **link pair**: `for lk in state.alive_l: if R > 0: pair = frozenset(lk)` (line 512-515)

→ **CID = 存在層 label = 2 つ以上のノードの frozenset**。Taka 「frozenset = CID 条件」が確実に正しい。

### 1.2 項目 2: 閾値の有無 (確実)

**誕生に閾値なし** (Taka 言及「閾値を排除してきた」と一致):
- 唯一の条件: `len(nodes) >= 2` (line 505, 525)
- 他に絶対閾値 (size / energy / familiarity 等) なし

**死亡 (cull) には相対閾値あり** (line 879-891):
```python
fair_share = 1.0 / max(1, total_entities)
base_threshold = fair_share * 0.5
threshold_i = base_threshold / (1.0 + self.maturation_alpha * age)
if label["share"] < threshold_i:
    dead
```
- これは「平均の半分以下なら死」(相対値)、絶対閾値ではない
- maturation_alpha (デフォルト 0.10) で年齢補正、年寄りほど死ににくい (age=20 → threshold/3)

注: `MIN_C_NODES_FOR_VALID = 5` (cognition_v30〜v38, primitive/v910/virtual_layer_v9.py:787) は **別物**:
- これは「cognitive marker (ng) リストが 5 個以上で k_star 集計」の集計条件
- CID 誕生条件ではない (esde_v82_engine.py:258 で使用)

### 1.3 項目 3: 条件と CID 数の関係 (確実 + 実測)

**実測** (第 2 段階補足 191 CID、stage2_n5000 per_subject):
- 75% の CID が **core node 数 = 2** (`v11_m_c_n_core` の Q25/Q50/Q75 すべて 2)
- mean 2.05、max 5
- → **ほぼ全 CID が「弱い構造」(最小可能サイズ)** で誕生

**含意**: 現状の条件「len(nodes) ≥ 2」は最も緩いので、これ以上緩めることは原理上不可能。条件を **厳しくする** (例: `>= 3`) ことで弱い CID 数が激減すると確実に言える (これは実験前の論理的予測)。

「条件を緩めると弱い CID が増える」は **現状の最緩条件では飽和済み**。むしろ death 側 (`base_threshold * 0.5`) を緩めて弱い CID の生存を延ばす方向が変化を生む。

### 1.4 項目 4: 変化させる差し込み口 (確実)

| 場所 | 機構 | 効果 |
|---|---|---|
| `find_islands_sets(state, 0.20/0.30/0.10)` (autonomy/v82/esde_v82_engine.py:231) | island 検出 S 閾値 | island に含まれるノード集合の変化 |
| `base_threshold = fair_share * 0.5` (primitive/v910/virtual_layer_v9.py:879) | cull base | 「0.5」を上下で death rate 変動 |
| `maturation_alpha = 0.10` | 年齢補正係数 (V82Engine kwarg) | 老 CID の生残力強弱 |
| `_n_phase_neighbors(threshold=0.3)` (line 378) | phase 近傍判定 | label 内部構造の決定 |

→ いじる場所は明確。死亡 threshold (`base * 0.5` の 0.5) と maturation_alpha が主軸候補。

---

## 2. 物理層ノード数 (項目 5-7、環境要因、両方やる)

### 2.1 項目 5: N=5000 設定場所 (確実)

**`autonomy/v82/esde_v82_engine.py:44`**:
```python
V82_N = 5000
```

**V82Engine constructor** (line 110): `def __init__(self, seed=42, N=V82_N, ...)` → N で受け取り、調整可能。

**GenesisState** (`ecology/engine/genesis_state.py:22`):
```python
def __init__(self, n_nodes: int, c_max: float = 1.0, seed: int = 42):
    self.n_nodes = n_nodes
    self.E: Dict[int, float] = {i: 0.0 for i in range(n_nodes)}
    self.theta: np.ndarray = self.rng.uniform(0, 2 * np.pi, n_nodes)
    self.omega: np.ndarray = self.rng.uniform(0.05, 0.3, n_nodes)
    self.Z: np.ndarray = np.zeros(n_nodes, dtype=int)
    self.F: np.ndarray = np.ones(n_nodes)
```

→ n_nodes は constructor で **1 回設定**、`state.theta/omega/Z/F` は固定サイズ ndarray、`state.E` は固定サイズ dict。

### 2.2 項目 6: ノード数動的変動の差し込み口 (確実)

**現状なし** (Taka 確認規律「無いと書く前に全階層調べる」を実行した結果):

| 確認 | 結果 |
|---|---|
| state.theta/omega/Z/F の resize 機構 | **なし** (ndarray は init で固定サイズ) |
| state.E dict の動的追加 | 可能だが、関連 ndarray と整合性失う |
| ノード追加 API (add_node 等) | **なし** (grep `def add_node\|append_node` で発見ゼロ) |
| alive_n の動的増減 | **あり** (inject で `.add()`, enforce_extinction で再構築) — ただし「n_nodes 全体」は固定、その中の「生きてる数」だけが動的 |

→ 「n_nodes 5000 自体を動的に変える」差し込み口は **存在しない**。実装するなら ndarray を resize する API を新規実装する必要 (genesis_state.py に add_node メソッド追加、または resize 関数)。

**代替**: `alive_n` (生存ノードの subset) は inject で増、enforce_extinction で減 (E < EXTINCTION=0.001 で死)。これを「ノード数動的変動」と解釈すれば既存機構で可能。

### 2.3 項目 7: ノード棄損 (一方向死亡) を入れる場所 (確実)

**現状なし** (永久死亡フラグは未実装):

- `enforce_extinction` (genesis_state.py:99) は E < EXTINCTION (0.001) で alive_n から除外するが、後で inject で E を上げれば **復活可能**
- 「一度死んだら永久に戻れない」フラグ・set は実装ゼロ (grep で発見せず)

実装するなら:
- `state.permanent_dead: set = set()` を genesis_state に追加
- enforce_extinction で「死亡ノードを permanent_dead に追加」
- inject で permanent_dead を除外 (再活性化を禁止)

または:
- 確率的に「コピーミス = 復活しないノード」を発生させるロジックを kill_node 経路で実装

差し込み口 = `genesis_state.py:99 enforce_extinction` + `genesis_physics.py:240 inject` を改修。

---

## 3. 既存の環境要因 (項目 8-9、Taka 言及「2 種類」)

### 3.1 項目 8: 既に取り込まれている 2 種類 (確実、Taka 言及と整合)

#### (a) **stress_decay** (link 層の動的環境圧)

**`autonomy/v82/esde_v82_engine.py:58 apply_stress_decay`**:
```python
def apply_stress_decay(state, stress_intensity):
    # stress_intensity = current_links / link_ema (動的、EMA tau=20)
    global_pressure = stress_intensity - 1.0
    for lk in alive_l:
        omega_ratio = deg(lk) / mean_omega
        vulnerability = 1.0 - R(lk)
        penalty = S(lk) * global_pressure * omega_ratio * vulnerability
        if penalty > 0:
            state.S[lk] -= penalty  # link 弱化、EXTINCTION 以下で死
        elif penalty < 0:
            state.S[lk] += min(-penalty, 1-s)  # link 強化 (calcified)
```

- 制御: `V82EncapsulationParams(stress_enabled=True/False)`
- 効果: link 数 EMA 比で link 取捨を圧迫 (link が増えるほど弱い link が死ぬ)

#### (b) **semantic_pressure** (ノード層の摂動 + 近傍 latent_boost)

**`cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py:374 apply_semantic_pressure`**:
```python
def apply_semantic_pressure(state, substrate, params, tracker, rng):
    shielded = encapsulated islands の interior
    for n in alive_n:
        if n in shielded: continue
        if rng.random() > params.pressure_prob: continue
        d = rng.uniform(-1, 1)
        state.theta[n] += params.pressure_strength * d  # θ 摂動
        for nb in substrate[n]:
            state.set_latent(n, nb, +params.latent_boost)  # 近傍 link 引きずり込む
```

- パラメータ: `pressure_prob`, `pressure_strength`, `latent_boost=0.05`
- 効果: ノードに θ ランダム摂動 + 近傍 latent 引上げ (link 生成促進)、encapsulated 中の interior は免疫

### 3.2 項目 9: それらの所在 (確実)

| 環境要因 | 階層 | 何に効くか |
|---|---|---|
| stress_decay | link 層 (state.S / alive_l) | link の S 値を上下、EXTINCTION 以下で kill_link |
| semantic_pressure | ノード層 (state.theta + latent) | ノードの θ 摂動、近傍 latent 引上げ |

CID 層 (label) には **間接的に効く** (link 死亡 → island 解体 → label cull、θ 摂動 → phase_sig 変化 → label 再構築)。直接 CID を操作する環境要因は **なし**。

---

## 4. ベースライン (項目 10-11、実測)

### 4.1 項目 10: CID/IID αβ層の現状寿命 (確実、コード + 実測)

#### CID (label) cull
- **base_threshold = fair_share × 0.5** (相対値、平均の半分以下で死)
- **maturation_alpha = 0.10** (年齢補正、年寄りほど生残力強)
- 例: age 0 → base、age 20 → base/3 (3 倍残りやすい)

#### CID (cog) 寿命
- **GHOST_TTL = 10** (`primitive/v910/v910_pulse_model.py:109`)
- effective_ttl = GHOST_TTL + cid_ttl_bonus (拾得イベントで蓄積)
- ghost 化後 TTL window 経過で reap (registry から削除)

#### IID αβ層
- **わからん**: コード内で「IID αβ」を直接示す変数を発見できなかった。grep で `IID\|alpha_layer\|beta_layer` がヒットせず。Taka が言う「IID αβ層」は CID 層 (cog) と別物か、または cog の subset (v98c の `pickup_log` 関連?) か、判別できず。Taka に問合せる項目。

### 4.2 項目 11: 弱い CID の現状割合 (確実、実測)

**第 2 段階補足 (stage2_n5000_genesis_smoke、N=5000, mat 3, track 1)**:
- 191 CID 生成 (hosted 163 + ghost 28)
- `v11_m_c_n_core` (生誕時 core node 数) 分布:

| 統計 | 値 |
|---|---|
| count | 191 |
| mean | **2.05** |
| std | 0.34 |
| min | 2 |
| **25%** | **2** |
| **50%** | **2** |
| **75%** | **2** |
| max | 5 |

→ **75%+ の CID が core node 数 2** (最低値)。最大 5 でも 1% 未満。

`last_n_partners` (現在の partner 数):
- mean 2.72、median 2、max 31
- 多くは弱い、稀に強い (max 31) CID

→ Taka 「弱い構造の CID」が現状 **CID 群の大多数**。条件 (cull threshold) を緩めればさらに増え、厳しくすれば激減する。

注: これは smoke 規模 (mat 3) の結果。**フル (mat 20)** では cull 累積でもっと減るはず、実測未確認。

---

## 5. わからん事 (推測しない、Taka に問合せ)

| # | 不明 | わからん理由 |
|---|---|---|
| 5-1 | Taka 言及「IID αβ層」の正確な所在 | コード内に IID/alpha_layer/beta_layer の直接実装が見つからない。cog (CID) と別物か subset か判別不能 |
| 5-2 | 「動的ランダム変動が本命」の具体的設計 | ノード数の動的変動 (resize) を新規実装するか、既存の alive_n 動的増減 (inject + enforce_extinction) を活用するかで方向違う |
| 5-3 | ノード棄損率の目標値 (1% は弱い?) | 現状未実装、Taka 「固定 1% は弱い」と言うが、実装後の比較で初めて分かる |
| 5-4 | 第 4 段階の出口判定基準 | 「loop が崩れる」を何で測るか (CID lifespan / 弱い CID 割合 / labels_active の振動 等) |

---

## 6. 確実に言える結論

### 6.1 frozenset 条件 (本命)

- 誕生条件は **最緩** (len(nodes)≥2 のみ)、Taka 設計通り閾値は排除済
- 死亡条件は **相対閾値** (share < fair_share × 0.5 / (1+α×age))
- **いじる場所明確**: `base_threshold * 0.5` の 0.5 + `maturation_alpha = 0.10`
- 弱い CID は実測で **75%+**、現状でほぼ全 CID が最小サイズ (2 core node)

### 6.2 物理層ノード数

- **N=5000 自体を動的に変える機構は無い** (ndarray 固定サイズ)
- 実装するなら新規 API (resize / add_node) が必要
- 既存の **alive_n 動的増減** (inject + enforce_extinction) は既に動的
- ノード棄損 (一方向死亡) は **未実装**、permanent_dead set 追加で実装可

### 6.3 既存環境要因

- **2 種類確実に既存**: (a) stress_decay (link 層)、(b) semantic_pressure (ノード層)
- CID 層への直接環境要因は **なし** (link/node 経由で間接的)

### 6.4 ベースライン

- CID GHOST_TTL = 10 windows
- maturation_alpha = 0.10
- 弱い CID 割合 = 75%+ (実測)
- IID αβ層は **不明** (Taka 確認要)

---

## 7. 第 4 段階の設計に向けて (Code A 観察、判断は Taka)

### 7.1 確認後に分かったこと

- 「条件を緩めて弱い CID 増やす」は **誕生側では飽和済** (既に最緩)、死亡側 (`base * 0.5`) を緩める方向が変化を生む
- 「ノード数動的変動」は新規 API が要る大改修
- 既存の alive_n (inject + enforce_extinction) で「動的な node の生死」は既にある
- 既存環境要因 2 種類 (stress + semantic_pressure) を変動させる方が改修が小さい

### 7.2 軸の整理 (Code A 観察、Taka 判断)

| 軸 | A (現状維持) | B (変動) | 改修コスト |
|---|---|---|---|
| frozenset 死亡 threshold | base × 0.5 | base × 0.3 〜 0.7 (動的) | **小** (係数変更のみ) |
| maturation_alpha | 0.10 | 0.05 〜 0.20 | **小** |
| GHOST_TTL | 10 | 5 〜 20 | **小** |
| ノード数 (n_nodes) | 5000 固定 | 動的 resize | **大** (新規 API) |
| ノード棄損 (一方向死亡) | なし | permanent_dead 追加 | **中** (state + inject 改修) |
| stress_decay (link 環境) | enabled=False (現状 V82EncapsulationParams default は True、smoke では False) | 動的変動 | **小** (params 動的変更) |
| semantic_pressure (ノード環境) | 既存 | pressure_prob 動的変動 | **小** |

→ Taka 言及「frozenset と ノード数変動を両方やる」のうち:
- frozenset 側 = **改修小** (threshold 係数調整)
- ノード数変動 = **改修大** (resize 新規 API)、または **改修小** (既存 alive_n 動的増減 + 棄損)

---

## 8. 一文サマリ

第 4 段階準備 現状確認報告 (Code A、2026-05-31、Web Claude 依頼 + Taka 「正確には分からん、確実に言えること出す」、推測ゼロ規律) として、項目 11 件確認結果: (1) frozenset 定義は `primitive/v910/virtual_layer_v9.py:559 self.labels[lid]["nodes"] = frozenset(cluster_nodes)` で確実 / (2) 誕生条件は **最緩 len(nodes)≥2 のみ、絶対閾値なし** Taka 設計通り、死亡 cull は相対閾値 `fair_share×0.5/(1+α×age)` / (3) 弱い CID は実測で **75%+ が core node=2** 最小サイズ stage2_n5000 191 CID 中、現状 飽和済み / (4) 差し込み口は death threshold `base*0.5` の 0.5 + maturation_alpha 0.10 + find_islands_sets S 閾値 / (5) N=5000 設定は autonomy/v82/esde_v82_engine.py:44 V82_N=5000 / (6) **ノード数動的変動の差し込み口なし** ndarray 固定、新規 API 要 ただし alive_n は inject+enforce_extinction で動的 / (7) **ノード棄損なし** enforce_extinction は復活可能、permanent_dead set 追加で実装可 / (8) **既存環境要因 2 種類確定** = stress_decay (autonomy/v82:58 link 層 動的 EMA 比) + semantic_pressure (v43_engine.py:374 ノード θ 摂動+近傍 latent_boost) / (9) 所在 link 層 + ノード層、CID 層への直接環境要因なし / (10) CID 寿命 GHOST_TTL=10 + cid_ttl_bonus、maturation_alpha=0.10、**IID αβ層わからん Taka 確認要** / (11) 弱い CID 75%+ 実測、わからん 4 件 (IID αβ層所在 / 動的変動具体設計 / 棄損率目標値 / 第 4 段階出口判定)、確実な結論 (frozenset 誕生最緩死亡相対、ノード数動的は新規 API 大改修・alive_n は既に動的、環境要因 2 種類既存、ベースライン実測値あり)、第 4 段階軸整理 (frozenset death threshold 小改修・GHOST_TTL 小・ノード数動的大改修・棄損中改修・既存環境要因動的化小)、書込み unified/stage4_prep/ 配下のみ、本報告 → Taka 確認 → 第 4 段階設計の流れ。

---

**Step 現状確認 end. Taka / Web Claude 確認待ち。わからん 4 件 (特に IID αβ層) について Taka に問合せ要。**
