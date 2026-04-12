# ESDE システム構造 (v9.10 現行)

> v9.11 以降の設計基盤として、**実際に動いているもの** だけを記述する。
> 無効化された機能 (stress decay, compression, torque_factor) は末尾に一覧のみ記載。

---

## 全体像

```
Layer 3: Subject (認知主体)
  cid 単位で phi / attention / familiarity を追跡
  Pulse Model (50 step 周期) → 4 軸の MAD-DT 検出
  Information Pickup (死亡ラベル情報の拾得 → ghost TTL 延長)

Layer 2: Virtual (ラベル)
  island / R>0 ペアから label を seed
  label ごとに phase_sig, share, torque を管理
  Feedback Loop (全体 turnover → torque 倍率)

Layer 1: Physics (物理)
  5000 ノード × 動的リンク on 71×71 トーラス
  7 オペレータが毎 step 順番に実行
```

---

## Layer 1: Physics

### 空間構造

- **ノード数**: N = 5000
- **格子**: 71 × 71 トーラス (4 近傍 von Neumann)
  - 5041 スロット中 5000 のみ使用 (末尾 41 欠番)
- **リンク**: 格子に依存しない。全生存ノードからランダムサンプルで形成
  - 平均リンク数 ≈ 2700、ρ ≈ 0.022%、平均次数 ≈ 1.1

### 状態変数

| 変数 | 対象 | 意味 | 範囲 |
|---|---|---|---|
| θ[i] | ノード | 位相角 | [0, 2π) |
| ω[i] | ノード | 固有振動数 (固定) | [0.05, 0.3] |
| E[i] | ノード | エネルギー | [0, 1] |
| Z[i] | ノード | 化学状態 | 0=Dust, 1=A, 2=B, 3=C |
| F[i] | ���ード | 肥沃度 (固定地形) | mean=1.0 |
| S[k] | リンク | 強度 | [0, 1] |
| R[k] | リンク | 共鳴値 (ループ参加度) | [0, 5] |
| L[i,j] | ノードペア | 潜在ポテンシャル (疎) | [0, 1] |

**消滅閾値**: E < 0.007 のノード死亡、S < 0.007 のリンク死亡

### Step 実行順序と力学方程式

**1. Realization** — 潜在→リンク誕生
```
各生存ノード i につき 3 ノードをランダムサンプル
P(リンク誕生) = p_link_birth × L[i,j]     (p_link_birth = 0.007)
誕生時: S += 0.07, L -= 0.07
潜在リフレッシュ: L += |N(0,1)| × 0.003 × F_avg  (毎step 500 ペア)
```

**2. Physics: Pre-Chemistry** — 位相回転とエネルギー流
```
θ[i] += ω[i] + K_sync × Σ_j sin(θ[j] − θ[i])    (K_sync = 0.1)
flow_ij = 0.1 × S[k] × (E[j] − E[i]) × (0.5 + 0.5×cos(Δθ))
E[i] += Σ flow_ij                                   (clamp [0,1])
```

**3. Chemistry** — 化学反応
```
合成:   A + B → C + C   (S ≥ 0.3, E ≥ 0.26, cos(Δθ) ≥ 0.7)
自触媒: C + A → C + C   (同条件)
崩壊:   C → Dust         (E < 0.2, 放出 0.17)
```

**4. Physics: Resonance** — 共鳴検出 (10 step ごと)
```
長さ 3–5 のループを探索
R[k] += Σ weight[L]        (weight: L=3→1.0, L=4→0.5, L=5→0.25)
R[k] = min(R[k], 5.0)
```

**5. Auto-Growth** — ループ駆動のリンク強化
```
R > 0 のリンクのみ:
ΔS = min(0.03 × R[k], L[i,j], 1 − S[k])
S[k] += ΔS, L[i,j] -= ΔS
```

**6. Boundary Intrusion** — 島境界の摂動
```
S ≥ 0.30 の連結成分 (島) の境界ノードで:
P(swap) = 0.002/step
島内リンクの S を δ=0.02 減らし、島外リンクの S を δ 増やす
```

**7. Physics: Decay + Exclusion** — 減衰と排除
```
E[i] *= (1 − 0.005)
S[k] *= (1 − 0.05 / (1 + R[k]))     ← 共鳴が減衰を抑制
排除: ノード i の Σ S > 1.0 なら弱いリンクから順に kill
消滅: E < 0.007 → ノード死、S < 0.007 → リンク死
```

**背景注入** (step ごと、オペレータ間ではなく decay 後)
```
各生存ノードに P=0.003 でエネルギー +0.3 注入
注入先は growth score で重み付け (BIAS=0.7)
Z=0 のノードは 50% で A or B にランダム分化
```

---

## Layer 2: Virtual (ラベル)

### ラベルの一生

**誕生条件** (window ごと):
1. **島**: S ≥ 0.20 のリンクの連結成分 (size ≥ 2)
2. **R>0 ペア**: 共鳴リンクの両端ノード (size = 2)
- 既存ラベルと 50% 以上重複するクラスタは無視

**ラベル状態**:
- `nodes`: コアノード集合 (frozenset、誕生時に固定)
- `phase_sig`: 誕生時の平均位相 atan2(Σsin, Σcos)
- `share`: 全リンクに対する所有リンクの割合

**死亡条件**: share が 0 に落ちた window で死亡

### Torque (位相引力)

```
各ラベルの各コアノードに対して:
  torque = rigidity × share × cos(θ[n] − phase_sig)
  rigidity = 1 / (1 + 0.10 × age)
  θ[n] += torque × feedback_multiplier

Semantic Gravity (ラベル周辺ノードへの弱い引力):
  grav = torque_mag / |nodes| × gravity_factor
  格子上の隣接ノード (4 近傍) にも適用
```

### Feedback Loop

```
turnover_ratio = (died_share / total_share) の EMA
feedback_multiplier = clamp(1 + 0.10 × (ratio − 1), 0.8, 1.2)
最初 20 window は warmup (M=1.0 固定)
```

### Deviation Detection (v9.3)

各ラベルの位相偏差スコアを計算し、局所的な gravity_factor を調整。

---

## Layer 3: Subject (認知主体)

### ライフサイクル

```
Label 誕生 → cid 割当 (hosted)
Label 死亡 → ghost 化 (cid 維持、TTL=10 window)
TTL 超過 → reap (cid 消滅)
```

### Per-cid 状態

| 変数 | 更新頻度 | 意味 |
|---|---|---|
| phi | 毎 step | structural field の平均 θ と平均 S |
| attention | 毎 step | ノード頻度分布 (decay=0.99) |
| familiarity | 毎 step | 他 cid との相互認識強度 (decay=0.998) |
| disposition | 毎 window | social, stability, spread, familiarity の 4 値 |

### Structural / Spatial フィールド

```
compute_spatial():  コアノードから torus 4-近傍で BFS (max_hops = n_core)
compute_structural(): コアノードから link 隣接で BFS (max_hops = n_core)
```
→ 空間フィールド (格子ベース) とリンクフィールド (トポロジーベース) は別物。

### Introspection (v9.8b)

window 間の disposition 変化量が閾値を超えたらタグ発行:
`gain_social`, `loss_stability`, etc.
閾値: social=0.1, stability=0.1, spread=0.1, familiarity=2.0

### Information Pickup (v9.8c)

```
Label 死亡 → death_pool に投入 (寿命 3 window)
Ghost cid がプール内の情報を拾得:
  winner = argmin(phase距離), 閾値 = π/8
  効果: ghost TTL += 1 (物理層には影響なし)
```

### Pulse Model (v9.10)

```
発火条件: cumulative_step % 50 == cid % 50  (決定論的)
cold start: 最初 3 回は "unformed"、4 回目以降 "active"
4 軸: social, stability, spread, familiarity
MAD-DT: K=20 window の履歴で mean absolute deviation を計算
  MAD_Δ ≥ 1.0 → resonate (主観的サプライズ)
```

---

## n_core の実測分布

| n_core | 比率 (long) | 由来 |
|---|---|---|
| 2 | 76.7% | R > 0 リンクペア |
| 3 | 5.3% | 島 (S≥0.20 連結成分) |
| 4 | 6.9% | 島 |
| 5 | 11.2% | 島 |

ラベルのコアノードは格子上に **散在** する (リンクが空間制約なしのため)。

---

## 無効化された機能 (コードは存在)

| 機能 | 無効化方法 | 理由 |
|---|---|---|
| Stress Decay | `stress_enabled=False` | v910 で明示的に切り |
| Compression → MacroNode | `compression_enabled=False` | デフォルト無効 |
| Torque Factor (v9.7) | `torque_factor` 未設定 (=1.0) | "v9.7 の機構は使わない" |

---

## パラメータ一覧 (v9.10 実行値)

### Physics (v19g_canon.py で freeze)

| パラメータ | 値 | 意味 |
|---|---|---|
| N | 5000 | ノード数 |
| p_link_birth | 0.007 | リンク誕生確率係数 |
| latent_refresh_rate | 0.003 | L リフレッシュレート |
| latent_to_active_threshold | 0.07 | L→S 変換量 |
| auto_growth_rate | 0.03 | 共鳴リンク成長レート |
| intrusion_rate | 0.002 | 境界摂動レート |
| K_sync | 0.1 | Kuramoto 結合定数 |
| NODE_DECAY | 0.005 | ノード減衰率 |
| link_decay_rate | 0.05 | リンク基本減衰率 |
| BETA (resonance) | 1.0 | 共鳴保護係数 |
| C_MAX (exclusion) | 1.0 | 排除上限 |
| EXTINCTION | 0.007 | 消滅閾値 |
| BIAS | 0.7 | 背景注入の growth 重み |
| bg_injection_prob | 0.003 | 背景注入確率 |
| E_thr (chemistry) | 0.26 | 反応エネルギー閾値 |
| exothermic_release | 0.17 | 崩壊時放出エネルギー |

### Virtual

| パラメータ | 値 |
|---|---|
| island_threshold (S) | 0.20 |
| feedback_gamma | 0.10 |
| feedback_clamp | [0.8, 1.2] |
| rigidity_beta | 0.10 |
| torque_order | "age" |

### Subject

| パラメータ | 値 |
|---|---|
| GHOST_TTL | 10 windows |
| ATTENTION_DECAY | 0.99 |
| FAMILIARITY_DECAY | 0.998 |
| PULSE_INTERVAL | 50 steps |
| K_PULSE (history) | 20 windows |
| R_THRESHOLD (MAD) | 1.0 |
| INFORMATION_LIFETIME | 3 windows |
| AFFINITY_THRESHOLD | π/8 |
| TTL_BONUS_PER_PICKUP | 1 window |

### 実行構成

| 項目 | 値 |
|---|---|
| maturation_windows | 20 (long), 20 (short) |
| tracking_windows | 50 (long), 10 (short) |
| window_steps | 500 |
| injection_steps | 300 |

---

## コード参照

| コンポーネント | ファイル |
|---|---|
| エンジン本体 | `autonomy/v82/esde_v82_engine.py` |
| V43 基底ク���ス | `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py` |
| 凍結パラメータ | `ecology/engine/v19g_canon.py` |
| 状態オブジェクト | `ecology/engine/genesis_state.py` |
| 物理オペレータ | `ecology/engine/genesis_physics.py` |
| 化学オペレータ | `ecology/engine/chemistry.py` |
| リンク誕生 | `ecology/engine/realization.py` |
| 自動成長 | `ecology/engine/autogrowth.py` |
| 境界侵入 | `ecology/engine/intrusion.py` |
| 仮想層 (v9) | `primitive/v910/virtual_layer_v9.py` |
| v9.10 パルスモデル | `primitive/v910/v910_pulse_model.py` |
