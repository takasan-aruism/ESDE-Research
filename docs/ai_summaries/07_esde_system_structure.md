# ESDE システム構造 (v9.13 現行)

*作成*: v9.11 完了時点
*更新*: 2026-04-17 (v9.13 完了、S≥0.20 撤去、persistence-based birth 反映)

> v9.13 時点の **実際に動いているもの** だけを記述する。
> 無効化された機能 (stress decay, compression, torque_factor, S≥0.20 hard threshold) は末尾に一覧のみ記載。
> v9.11 で導入された Cognitive Capture、v9.13 で導入された Persistence-based Birth を反映。

---

## 全体像

```
Layer 4: Consciousness (意識、未実装、v10.x で着手予定)
  認知層の解釈 (誤差の埋め合わせ) を検証するだけ
  物理層・存在層・認知層に介入しない
  「埋め合わせは本当に正しいか」を問う

Layer 3: Subject (認知主体)
  cid 単位で phi / attention / familiarity を追跡
  Pulse Model (50 step 周期) → 4 軸の MAD-DT 検出
  Information Pickup (死亡ラベル情報の拾得 → ghost TTL 延長)
  v9.11: B_Gen (cid 固有値) / M_c (記憶ベクトル) / E_t (事象ベクトル) /
         Δ (差分分解型一致率) / Capture Probability
  v9.13: 方向性確定 — 物理層を支配しない、統計的多少の差、物理状態を記憶として読む関数へ

Layer 2: Existence (存在、旧称: 仮想層 / Virtual)
  v9.13: persistence-based birth — age_r ≥ τ の link の connected component
  label ごとに phase_sig, share, torque を管理
  Feedback Loop (全体 turnover → torque 倍率)
  ※ 唯一、物理層 (θ) に微小介入する層 (M ≈ 0.993、torque)

Layer 1: Physics (物理)
  5000 ノード × 動的リンク on 71×71 トーラス
  7 オペレータが毎 step 順番に実行
  存在層以外からの介入を受けない (frozen)
```

### 4 層の規律 (v9.11 で確立、v9.13 で方向性再確認)

```
物理層 ← 存在層 (θ への torque のみ、微小変調)
   ↓
認知層 (観察・解釈のみ、介入なし)
   ↓
意識層 (認知層の検証のみ、介入なし)
```

**重要転換 (v9.11)**: B_Gen 導入により「認知層から θ への介入」(かつての v9.7 構想) は不要となった。認知層は完全に観察・解釈のレイヤとして純粋化。**v9.7 の認知介入失敗を再発させてはならない**。

**再確認 (v9.13、Taka 2026-04-16)**: 「認知層は物理層を支配しない。物理層の動きを予測しながら認知的に自分の存在を生かす方向。効果は劇的ではなく、統計的に多少の差が出る程度。」

**過去履歴**: v9.5 までは 3 層構造 (物理 / 存在 / 認知) として整理されていたが、v9.11 で意識層が概念化されて 4 層に進化した。古い資料に「3 層」と書かれていても、それは v9.10 以前のスナップショットである。

---

## Layer 1: Physics

### 空間構造

- **ノード数**: N = 5000
- **格子**: 71 × 71 トーラス (4 近傍 von Neumann)
  - 5041 スロット中 5000 のみ使用 (末尾 41 欠番)
- **リンク**: 格子に依存しない。全生存ノードからランダムサンプルで形成
  - 平均リンク数 ≈ 2700、ρ ≈ 0.022%、平均次数 ≈ 1.1

**重要**: ESDE は 71×71 トーラス + 長距離ランダムリンクの**二重トポロジー**。リンクは格子幾何に依存しないので、ラベルのコアノードは格子上に**散在**する。AI が「ESDE はトーラス格子上の局所力学系」と単純化すると設計を間違える (lattice audit 経緯)。

### 状態変数

| 変数 | 対象 | 意味 | 範囲 |
|---|---|---|---|
| θ[i] | ノード | 位相角 | [0, 2π) |
| ω[i] | ノード | 固有振動数 (固定) | [0.05, 0.3] |
| E[i] | ノード | エネルギー | [0, 1] |
| Z[i] | ノード | 化学状態 | 0=Dust, 1=A, 2=B, 3=C |
| F[i] | ノード | 肥沃度 (固定地形) | mean=1.0 |
| S[k] | リンク | 強度 | [0, 1] |
| R[k] | リンク | 共鳴値 (ループ参加度) | [0, 5] |
| L[i,j] | ノードペア | 潜在ポテンシャル (疎) | [0, 1] |
| **age_r[k]** | **リンク** | **連続 R>0 step 数 (v9.13 新規)** | **整数 ≥ 0** |

**消滅閾値**: E < 0.007 のノード死亡、S < 0.007 のリンク死亡

### Step 実行順序と力学方程式

**1. Realization** — 潜在→リンク誕生
```
各生存ノード i につき 3 ノードをランダムサンプル
P(リンク誕生) = p_link_birth × L[i,j]     (p_link_birth = 0.007)
誕生時: S += 0.07, L -= 0.07
潜在リフレッシュ: L += |N(0,1)| × 0.003 × F_avg  (毎step 500 ペア)
age_r[k] = 0 で初期化 (v9.13)
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

v9.13 追加: R 更新後に age_r[k] 更新
  if R[k] > 0: age_r[k] += 1
  else:        age_r[k]  = 0
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
消滅: E < 0.007 → ノード死、S < 0.007 → リンク死 (age_r も消滅)
```

**背景注入** (step ごと、オペレータ間ではなく decay 後)
```
各生存ノードに P=0.003 でエネルギー +0.3 注入
注入先は growth score で重み付け (BIAS=0.7)
Z=0 のノードは 50% で A or B にランダム分化
```

---

## Layer 2: Existence (存在層、旧称: 仮想層)

### ラベルの一生 (v9.13 以降)

**誕生条件** (window ごと):

```
1. age_r ≥ τ の link を抽出 (τ = 50 or 100)
2. 抽出した link で connected component を構成 (size ≥ 2)
3. 既存 label と 50% 以上重複する component は排除
4. 残った component が label 化
```

**v9.13 での変更点**:
- S≥0.20 hard threshold を**撤去** (神の手として判明)
- 経路 B (R>0 ペア即 label) を**廃止** (R=0 混入の原因)
- age_r persistence 要件で Genesis 原理 (閉路 = 共鳴) に忠実な label 選別

**ラベル状態**:
- `nodes`: コアノード集合 (frozenset、誕生時に固定 = 「魂」、解放しない)
- `phase_sig`: 誕生時の平均位相 atan2(Σsin, Σcos)
- `share`: 全リンクに対する所有リンクの割合

**死亡条件**: share が 0 に落ちた window で死亡

### Torque (位相引力) — 物理層への唯一の介入

```
各ラベルの各コアノードに対して:
  torque = rigidity × share × cos(θ[n] − phase_sig)
  rigidity = 1 / (1 + 0.10 × age)
  θ[n] += torque × feedback_multiplier

Semantic Gravity (ラベル周辺ノードへの弱い引力):
  grav = torque_mag / |nodes| × gravity_factor
  格子上の隣接ノード (4 近傍) にも適用
```

**M ≈ 0.993** の微小変調で物理層は壊れない。系全体としては物理層が支配的、存在層は微小変調者。

### Feedback Loop

```
turnover_ratio = (died_share / total_share) の EMA
feedback_multiplier = clamp(1 + 0.10 × (ratio − 1), 0.8, 1.2)
最初 20 window は warmup (M=1.0 固定)
```

### Deviation Detection (v9.3)

各ラベルの位相偏差スコアを計算し、局所的な gravity_factor を調整。deviation_enabled=True で動作中、v9.14 以降で検証予定。

---

## Layer 3: Subject (認知層)

### ライフサイクル

```
Label 誕生 → cid 割当 (hosted)
Label 死亡 → ghost 化 (cid 維持、TTL=10 window)
TTL 超過 → reap (cid 消滅)
```

**規律**: 認知層は物理層・存在層に**書き込まない**。`engine.state.theta/S/R/E/Z` および `vl.labels[*].nodes/phase_sig/share` への mutation はゼロ。grep で確認可能。

### Per-cid 状態 (v9.10 までの基本)

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

### Introspection (v9.8b → v9.10 で動的閾値化)

window 間の disposition 変化量が閾値を超えたらタグ発行:
`gain_social`, `loss_stability`, etc.

**v9.8b (廃止)**: 固定閾値 social=0.1, stability=0.1, spread=0.1, familiarity=2.0
**v9.10 (現行)**: MAD-DT (Mean Absolute Delta — Dynamic Threshold) で cid 履歴から自動算出

### Information Pickup (v9.8c、現状休眠保持)

```
Label 死亡 → death_pool に投入 (寿命 3 window)
Ghost cid がプール内の情報を拾得:
  winner = argmin(phase距離), 閾値 = π/8
  効果: ghost TTL += 1 (物理層には影響なし)
```

**状態**: 動作中だが効果薄。Taka 原則「無駄だから切る」禁止に従い **休眠保持**。「CID が他者の経験を取り込む」フレームワークとして将来活用候補。

### Pulse Model (v9.10)

```
発火条件: cumulative_step % 50 == cid % 50  (決定論的)
cold start: 最初 3 回は "unformed"、4 回目以降 "active"
4 軸: social, stability, spread, familiarity
MAD-DT: K=20 window の履歴で mean absolute deviation を計算
  R = Δx_current / (theta + 1e-6)
  R > 1.0 → resonate (主観的サプライズ)
```

### Cognitive Capture (v9.11、v9.13 で label 集合が純化)

cid に**個体固有値**と**記憶ベクトル**を持たせ、周囲の現象との一致率から事象を確率的に捕捉する。

#### Genesis Budget (B_Gen) — cid 固有値

```
ρ        = links_total / C(N, 2)            (N = 5000)
Pbirth   = (1 / C(N, n_core)) × ρ^(n-1) × r_core^(n-1) × S_avg^(n-1)
B_Gen    = -log10(Pbirth)
```

- Birth 時に cid 単位で 1 度だけ記録、固定
- 「ほぼ一意のパスワード + 認知原資」(Taka 構想)
- バンド構造 (v9.13 τ=50/100 実測):
  - n=2 → B ≈ 12 (v9.11 と同)
  - n=3 → B ≈ 20 (v9.11 19 から +1)
  - n=4 → B ≈ 28 (v9.11 26 から +2)
  - n=5 → B ≈ 35-36 (v9.11 34 から +1-2)
  - n=6-8 → 推定 42-62 (出現頻度依然低い)
- v9.13 で n≥3 に上方シフト。persistence 要件で同じ n_core でも構造階層が深い
- **重要**: B_Gen は capture probability の**直接入力ではない** (M_c を経由する間接効果のみ)

#### Memory Core (M_c) — 記憶ベクトル

Birth 時に固定記録される 4 要素:

```
M_c = (n_core, S_avg, r_core, phase_sig)
```

- `n_core`: 構造のサイズ (整数 2-5 が主、稀に 6-8)
- `S_avg`: ラベル内平均リンク強度 (0-1)
- `r_core`: Kuramoto 秩序パラメータ = 位相同期度 (0-1)
- `phase_sig`: 平均位相 (円周量、circular distance で扱う)

**規律**: M_c は**追加しない**。次元の呪いを避けるため 4 要素固定。次元拡張は v9.14+ で要 audit。

#### Experience (E_t) — 事象ベクトル

各 pulse 時 (50 step ごと) に knowledge field から自動抽出される 4 要素:

```
E_t = (n_local, s_avg_local, r_local, theta_avg_local)
```

- `n_local`: 知覚範囲内の alive ノード数
- `s_avg_local`: 知覚範囲内のリンク強度平均
- `r_local`: 知覚範囲内の Kuramoto 秩序パラメータ
- `theta_avg_local`: 知覚範囲内の位相平均 (circular)

#### Delta (Δ) — 差分分解型 Weighted L1

```
Δ = w_n × |n_core − n_local| / V11_NORM_N
  + w_s × |S_avg − s_avg_local| / V11_NORM_S
  + w_r × |r_core − r_local| / V11_NORM_R
  + w_phase × circular_diff(phase_sig, theta_avg_local) / π

V11_NORM_N = 86 (n_local p95 floor、v9.12 で過大と判明も維持)
V11_NORM_S = V11_NORM_R = 1.0
重み w_* = 0.25 (均等)
```

各軸の個別誤差 (d_n, d_s, d_r, d_phase) も CSV に記録。

#### Capture Probability (p_capture)

```
p_capture = V11_P_MAX × exp(-V11_LAMBDA × Δ)
```

- P_MAX = 0.9 (1.0 未満で「取りこぼしを残す」設計)
- λ = 2.724 (smoke Δ p50 基準で決定)

**Variant の段階的進化**:
- Variant A (現行): 指数減衰、実装軽量、監査容易
- Variant B (候補): シグモイド、境界の滑らかさ
- Variant C (候補): 多次元ベクトルマッチング

#### Capture 判定の運用

```
pulse_n <= 3 (cold_start): 判定しない、"cold_start" ログのみ
pulse_n >= 4: capture_rng で判定、TRUE/FALSE
```

**capture_rng**: `np.random.default_rng(seed ^ 0xC0FFEE)` で engine.rng から完全分離

#### CSV 出力 (v9.11 追加列、v9.13 で維持)

**pulse_log (12 列追加)**: v11_b_gen, v11_delta, v11_d_n, v11_d_s, v11_d_r, v11_d_phase, v11_p_capture, v11_captured, v11_n_local, v11_s_avg_local, v11_r_local, v11_theta_avg_local

**per_subject (13 列追加)**: v11_b_gen, v11_m_c_n_core, v11_m_c_s_avg, v11_m_c_r_core, v11_m_c_phase_sig, v11_n_pulses_eval, v11_n_captured, v11_capture_rate, v11_mean_delta, v11_mean_d_n, v11_mean_d_s, v11_mean_d_r, v11_mean_d_phase

**v9.13 追加出力 (persistence 追跡)**:
- `link_life_log`: 各 link の誕生・死亡・max_age_r
- `link_snapshot_log`: 各 step の age_r 分布サンプル
- `label_member_persistence`: label birth 時のメンバーリンク age_r_min/mean
- `shadow_component_log`: window 末の shadow component 分析

**規律**: v99_ (v9.9) 列、v10_ (v9.10) 列、v11_ (v9.11) 列は 1 バイトも触らない。v13_ は末尾追加のみ。

#### v9.11 本番 run 結果 (2026-04-15 完了、v9.13 結果の参照軸)

- short: 48 seeds × 10 windows、subject 2,979 / pulse 119,320
- long: 5 seeds × 50 windows、subject 1,112 / pulse 75,600
- B_Gen バンド構造 short/long で一致 (Δ<0.05)
- capture_rate mean: 0.397 (short) / 0.379 (long)
- L06 長命群 (上位 10%): n=5 優勢 (61.4%)、capture_rate 0.307 (overall より低い)

**注意**: v9.11 結果の n_core 構成 (n=2 が 67%) は経路 B + R=0 混入のアーティファクトを含む。v9.13 で再解釈済み。

#### v9.13 本番 run 結果 (2026-04-17 完了)

- τ=50: 24 seeds、labels 1,034 (43.1/seed)、capture_rate 0.346
- τ=100: 24 seeds、labels 832 (34.7/seed)、capture_rate 0.345
- R>0 純度: 両 τ で **100%** (birth 時)
- n_core 分布: τ=50 で n=2:23%, n=5:38% / τ=100 で n=2:28%, n=5:31%
- 軸寄与: phase+r 63%, n 軸 25-27% (v9.11 の 73% / 13% から均等化)
- lifespan mean: 12.0w (τ=50) / 13.2w (τ=100)、v9.11 の 6.6w から倍増
- **S≥0.20 撤去主題の達成、v9.11 所見の多くが再解釈された**

---

## Layer 4: Consciousness (意識層、未実装)

v10.x 以降で着手予定。本セクションは規律のみ明示する。

### 役割

認知層の「誤差の埋め合わせ」(概念化) を**検証する**。
角度を変える、移動するなどの能動的差分検証を行う。
**物理層・存在層・認知層のいずれにも介入しない**。

Taka 確定発言:
> 誤差を物理的なものとして、それの埋め合わせが概念的なものだとする。それって本当に埋め合わせできてるのか? を問えるのが意識。

### 規律 (v9.11 段階で事前合意済み)

- 意識層は物理層・存在層・認知層の状態に**書き込まない**
- 検証は認知層の解釈に対してのみ行う
- 「動いたつもり」は意識層の解釈にすぎず、実際に物理層を動かしているわけではない
- 哲学的立場: 私たちが直接物理に干渉できるのか自体が哲学的疑問。ESDE では「介入しない」を実装の原則として徹底

### 前提条件 (v10.x 着手前に必要)

- cid の記憶蓄積機構 (現状 capture は CSV 行のみ、cid 自身は覚えていない)
- 誤差の埋め合わせ機構 (v9.14+ 認知層拡張)
- 検証対象が具体的に揃うこと

---

## n_core の実測分布 (v9.13 更新)

| n_core | v9.11 short 比率 | v9.13 τ=50 比率 | v9.13 τ=100 比率 | 由来 |
|---|---|---|---|---|
| 2 | 67.1% | 22.5% | 27.8% | v9.11: R>0 ペア (経路 B、多くが R=0 混入) / v9.13: age_r ≥ τ の 2 ノード component |
| 3 | 7.4% | 19.3% | 20.4% | age_r ≥ τ の 3 ノード component |
| 4 | 9.1% | 19.8% | 20.8% | 同 4 ノード |
| 5 | 16.3% | 38.1% | 30.9% | 同 5 ノード |
| 6-8 | 0.1% | 0.2% | 0.1% | 希少 |

**v9.13 での重要な再解釈**: v9.11 の n=2 主体 (67%) は経路 B + R=0 混入のアーティファクトだった。純粋な Genesis 原理下 (age_r ≥ τ) では n=2 は 22-28%、n=5 が最頻サイズに。

**n≥6 欠落の状況**: S≥0.20 撤去後も大型 label の出現頻度は v9.11 と同水準。v9.12 指摘の 3 要因のうち、50% overlap フィルタと非空間的リンク形成が残存制約として効いている。

ラベルのコアノードは格子上に**散在**する (リンクが空間制約なしのため)。

---

## 無効化された機能 (コードは存在)

| 機能 | 無効化方法 | 理由 |
|---|---|---|
| Stress Decay | `stress_enabled=False` | v910 で明示的に切り |
| Compression → MacroNode | `compression_enabled=False` | デフォルト無効 |
| Torque Factor (v9.7) | `torque_factor` 未設定 (=1.0) | v9.7 失敗の遺物、認知層から θ への介入 |
| S≥0.20 hard threshold | v9.13 で撤去 | 神の手として判明、persistence-based birth で代替 |
| 経路 B (R>0 ペア即 label) | v9.13 で廃止 | R=0 混入の原因、age_r ベースに統一 |

---

## 休眠保持されている機能 (削除しない)

Taka 原則「無駄だから切る」禁止により、効果薄でも削除せず残す。

| 機能 | 状態 | 保持理由 |
|---|---|---|
| pickup (v9.8c) | 動作中、TTL bonus は ghost 期間延長のみ | 「CID が他者の経験を取り込む」フレームワーク、将来活用候補 |
| death_pool 管理 | pickup 中間処理 | 同上 |
| Semantic gravity + deviation | deviation_enabled=True | v9.14 以降で検証予定 |
| v99_ 内的基準軸 | 計算走行中、CSV 出力中 | CSV 出力は止める可、計算自体は保持 |

---

## パラメータ一覧 (v9.13 実行値)

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

### Existence (Virtual、v9.13)

| パラメータ | 値 | 備考 |
|---|---|---|
| ~~island_threshold (S)~~ | ~~0.20~~ | **v9.13 で撤去** |
| **persistence_threshold (τ)** | **50 or 100** | **v9.13 新規、age_r 連続 R>0 step 数** |
| feedback_gamma | 0.10 | |
| feedback_clamp | [0.8, 1.2] | |
| rigidity_beta | 0.10 | |
| torque_order | "age" | |

### Subject (Cognition、v9.10 まで)

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
| COLD_START_PULSES | 3 |

### Cognitive Capture (v9.11、v9.13 で維持)

| パラメータ | 値 | 決定根拠 |
|---|---|---|
| V11_NORM_N | 86 | Step 0 norm audit、n_local p95 floor |
| V11_NORM_S | 1.0 | 理論値域 [0,1] |
| V11_NORM_R | 1.0 | 理論値域 [0,1] |
| V11_W_N | 0.25 | 4 軸均等 (暫定) |
| V11_W_S | 0.25 | 4 軸均等 (暫定) |
| V11_W_R | 0.25 | 4 軸均等 (暫定) |
| V11_W_PHASE | 0.25 | 4 軸均等 (暫定) |
| V11_P_MAX | 0.9 | 取りこぼしを残す設計 (GPT 補正) |
| V11_LAMBDA | 2.724 | smoke Δ p50 基準で決定 |
| V11_CAPTURE_COLD_START_SKIP | True | pulse_n <= 3 は判定保留 |
| capture_rng seed | seed ^ 0xC0FFEE | engine.rng から分離 |

### 実行構成 (v9.13)

| 項目 | v9.11 short | v9.11 long | v9.13 τ=50 | v9.13 τ=100 |
|---|---|---|---|---|
| seeds | 48 | 5 | 24 | 24 |
| maturation_windows | 20 | 20 | 20 | 20 |
| tracking_windows | 10 | 50 | 20 | 20 |
| window_steps | 500 | 500 | 500 | 500 |
| injection_steps | 300 | 300 | 300 | 300 |

---

## v9.12 で確定した認知捕捉の性質 (v9.13 で更新)

- Δ は i.i.d. (自己相関 ≈ 0) — 蓄積しない
- 軸寄与の偏在 (v9.11 の phase+r 72%) は **n_core 構成効果** (v9.13 で再解釈)
  - 純粋な Genesis 原理下では phase+r 63% + n 軸 27% に均等化
- d_r と d_phase は無相関 (r=0.008)
- L06 低 capture は n_core 構成効果 (時間効果ではない)
- n_core≥6 が出ないのは 50% overlap フィルタ + 非空間リンク形成 (v9.13 で S≥0.20 撤去しても変わらず)

---

## コード参照

| コンポーネント | ファイル |
|---|---|
| エンジン本体 | `autonomy/v82/esde_v82_engine.py` (frozen) |
| V43 基底クラス | `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py` |
| 凍結パラメータ | `ecology/engine/v19g_canon.py` (frozen) |
| 状態オブジェクト | `ecology/engine/genesis_state.py` |
| 物理オペレータ | `ecology/engine/genesis_physics.py` |
| 化学オペレータ | `ecology/engine/chemistry.py` |
| リンク誕生 | `ecology/engine/realization.py` |
| 自動成長 | `ecology/engine/autogrowth.py` |
| 境界侵入 | `ecology/engine/intrusion.py` |
| 仮想層 (v9) | `primitive/v910/virtual_layer_v9.py` (frozen) |
| v9.10 パルスモデル | `primitive/v910/v910_pulse_model.py` |
| v9.11 cognitive capture | `primitive/v911/v911_cognitive_capture.py` (commit 24ec112) |
| v9.11 norm audit | `primitive/v911/v911_norm_audit.py` |
| v9.11 Pbirth 計算 | `primitive/v911/_compute_pbirth.py` |
| v9.11 genesis budget 計測 | `primitive/v911/v911_genesis_budget_measure.py` |
| **v9.13 persistence audit + birth** | **`primitive/v913/v913_persistence_audit.py`** |
| v9.13 Step 0 audit result | `primitive/v913/v913_persistence_audit_result.md` |
| v9.13 本番結果 (τ=50) | `primitive/v913/v913_persistence_birth_result.md` |
| v9.13 τ 比較 | `primitive/v913/v913_tau_comparison.md` |

---

## AI 用注意事項 (新スレッド着手時の必読項目)

### 1. ESDE は二重トポロジー
71×71 トーラス + 長距離ランダムリンク。リンクは格子に依存しない。「局所的な格子力学系」と単純化すると Pbirth 設計などで失敗する (lattice audit の経緯)。

### 2. 4 層構造の介入規律
- 物理層: 上位層からの介入を受けない (存在層以外)
- 存在層: θ への torque のみ (微小変調 M ≈ 0.993)
- 認知層: 介入なし、観察のみ
- 意識層: 介入なし、認知層の検証のみ

「認知層から θ への介入」は v9.7 失敗の原因。**B_Gen でこの誘惑は構造的に消えた**。**v9.13 で「認知層は物理層を支配しない」が方向性として再確認された**。再発させない。

### 3. v9.11 で B_Gen は capture の直接入力ではない
B_Gen は cid 固有の階層指標として保持されるが、capture probability の計算には**M_c を経由する間接効果のみ**で使われる。直接 capture に B_Gen を入れると n_core バンド支配で個体差が消える (GPT 補正 4)。

### 4. M_c の 4 要素は固定
n_core, S_avg, r_core, phase_sig の 4 要素のみ。次元拡張は v9.14+ で要 audit。次元の呪いを避ける。

### 5. similarity は差分分解型 Weighted L1
コサイン類似度ではない。各軸を個別に正規化、重み付き和。規模 (n) の絶対差が潰れないように (GPT 補正 3)。

### 6. phase は必ず circular distance
円周量なので単純な実数差ではない。`circular_diff(a, b) / π` で正規化 (GPT 補正 2)。

### 7. 誤差は per_subject CSV に記録、埋め合わせは v9.14+
v9.11 では誤差の各軸を CSV に記録するだけ。「埋め合わせ」(概念化) は v9.14 以降の認知層拡張、検証は v10.x 意識層 (GPT 補正 5)。

### 8. 並列化必須
複数 seed の run は parallel 化必須。OMP/MKL/OPENBLAS_NUM_THREADS=1 を必ず設定。sequential 実行は禁止。

### 9. Claude Code A/B 運用
A=実装+audit、B=コードチェック (read only)。各ステップで approved/needfix ファイル作成。チェック依頼書を必ず作成。

### 10. 用語の対応 (古い資料を読むとき注意)
- 「仮想層」 = 「存在層」 = Virtual = Existence (同じもの)
- 「3 層構造」 = v9.10 以前の整理。現在は **4 層** (意識層を含む)
- 「観測層」「行動層」「計測層」 = **存在しない**。過去の Claude が誤って導入した用語。使わない
- 「神の手」 = 設計者が外部から意味や行動を注入すること。避けるべき設計
- 「Aruism」 = ESDE の哲学。「構造が先、意味が後」
- 「S≥0.20」 = v9.13 で撤去済の hard threshold。新スレッドで実装してはいけない
- 「経路 B (R>0 ペア即 label)」 = v9.13 で廃止。age_r ベースの component birth に統一

### 11. 「結果出したもん勝ち」
研究方針。論文よりも結果。null result も valid。投資としての ESDE (Taka スタンス)。

### 12. AI の誤読が測定器
Triad (Gemini/GPT/Claude) が同じ方向にズレたとき、Taka の「違う違うそうじゃない」で輪郭が出る。AI の誤読自体が研究手段の 1 つとして機能している (Taka 発言)。

### 13. v9.13 で確定した前提変更 (v9.11 結果を引用する際の必須チェック)

- v9.11 の「n=2 主体 (67%)」は経路 B + R=0 混入のアーティファクト → 純粋には 22-28%
- v9.11 の「phase+r 72% 支配」は n_core 構成効果 → 均等化で 63% + n 軸 27%
- v9.11 label の約 2/3 が「見かけ構造」(R=0 混入) → v9.13 で除去
- L06 n_core 偏重 (v9.11: 61% が n=5) は v9.13 で 44-49% に緩和

新スレッドの AI が v9.11 結果をそのまま引用する場合、これらのアーティファクト影響がないか必ず確認すること。

### 14. 認知層の効果は統計的に多少の差 (v9.13 方針)

Taka 2026-04-16: 「人間が健康に気をつけていようといまいと寿命はある程度決まっている。統計的に多少の差が出る程度。ESDE の認知層もそれと同じ。」

**劇的な効果を期待する設計は神の手に近づく**。効果が出ないことを「失敗」と捉えず、「統計的な差が現れた」ことを成果と捉える。

### 15. CID の記憶は物理層の中に既にある (v9.13 方針)

Taka 2026-04-16: 「記憶を作る仕組みではなく、物理状態を記憶として読む関数を書く。」

- 外部 dict への蓄積は「私たちの記録」であって「CID の記憶」ではない
- cid のメンバーノードの θ 分布、メンバーリンクの S/R 分布自体が記憶
- 次フェーズ (v9.14/v10.0) の主題

### 16. 「無駄だから切る」禁止 (v9.13 Taka 原則)

効果薄の機能も削除せず、どう活かすか考える。pickup (v9.8c) は休眠保持が現状の方針。

### 17. AI 間文書は日本語 md (v9.13 決定)

運営原則 v2 の「AI 間文書は英語」は**撤回**。Taka が読めることが最優先。日本語で投げれば GPT も日本語で返す。既存コード docstring は英語のまま維持。
