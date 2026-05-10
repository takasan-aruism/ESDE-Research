# ESDE システム構造 (v9.18 現行、Developmental フェイズ v10.x 開始)

*作成*: v9.11 完了時点
*更新*: 2026-04-17 (v9.13 完了、S≥0.20 撤去、persistence-based birth 反映)、2026-04-18 (v9.14 完了、Layer B Shadow Ledger 追加)、2026-04-20 (v9.15 完了、CidSelfBuffer 追加、A/B 分離、event 駆動 Fetch)、2026-04-21 (v9.16 完了、観察サンプリング機構 = age_factor 比例サンプリング追加、Constitution 接続)、2026-04-23 (v9.17 段階 4 完了、他者読み + 接触体記録、CidView + InteractionLog、摂食行動の発見、GPT 監査運用指針 v1 導入)、2026-04-24 (v9.18 段階 5 完了、A+C 統合 = cumulative_cognitive_gain + V_unified + theta_distance、per_step 計算、意識の原資モデルの明確化)、**2026-04-24 (Primitive フェイズ完結、Developmental フェイズ (v10.x) 開始、ディレクトリ `developmental/v10X/`)**

> v9.18 時点の **実際に動いているもの** だけを記述する。
> 無効化された機能 (stress decay, compression, torque_factor, S≥0.20 hard threshold, Match Ratio 集約 v9.15 段階 1) は末尾に一覧のみ記載。
> v9.11 Cognitive Capture、v9.13 Persistence-based Birth、v9.14 Paired Audit (Layer A + Layer B)、v9.15 CidSelfBuffer (A/B 分離、event 駆動 Fetch)、v9.16 観察サンプリング機構 (age_factor 比例、missing 3 値化、独自 RNG)、v9.17 他者読み機構 (read_other_on_e3_contact、other_records、visible_ratio = 相手 age_factor) + InteractionLog (接触体記録の外部器、A 側、状態なし、frozenset で pair 識別) + CidView (cid 情報統合 dataclass、B 側 read-only)、**v9.18 A+C 統合 (cumulative_cognitive_gain = Q0 - Q_remaining、V_unified = Kuramoto オーダーパラメータ、theta_distance_from_birth = 生誕時分布との RMS 距離、coverage_ratio、per_step 計算、v18_window_trajectory 新規 CSV、v18_finalize_reason)** を反映。

---

## 全体像

```
Layer 4: Consciousness (意識、未実装、v10.x で着手予定)
  認知層の解釈 (誤差の埋め合わせ) を検証するだけ
  物理層・存在層・認知層に介入しない
  「埋め合わせは本当に正しいか」を問う

[B 領域 — Layer ではない] CidSelfBuffer (CID 主体、v9.15 新規)
  各 CID に紐づく独立メモリ領域
  生誕時 theta_birth / S_birth (不変) + 最新 theta_current / S_current
  段階 1: 50 step 固定 Fetch (廃止)、段階 2: event 駆動 Fetch (現行)
  研究者向け集約統計は持たない (mean/std 等は A 側で計算)
  Layer A/B には一切介入しない
  A/B 分離を四重 (ファイル/クラス/メモリ/命名) で担保

Layer 3: Subject (認知主体) — v9.14 で paired audit 構成
  ├─ Layer A (Fixed Pulse、50 step 周期):
  │    全体スナップショット・均一サンプリング
  │    cid 単位で phi / attention / familiarity を追跡
  │    4 軸の MAD-DT 検出、Cognitive Capture (v9.11)
  │    Information Pickup (死亡ラベル情報 → ghost TTL 延長)
  │
  └─ Layer B (Shadow Ledger、event 駆動、v9.14 新規、audit-only):
       Q0 = floor(B_Gen) を cid の初期原資として運用
       E1 (core link 死/生) / E2 (R-state 変化) / E3 (cid contact onset)
       event 発火ごとに spend packet 実行、Q -= 1
       virtual_attention / virtual_familiarity (Layer A と別メモリ、累積)
       Layer A に一切介入しない (bit-identity 維持)
       v9.15 段階 2: event 発火時に CidSelfBuffer.read_on_event を呼ぶ

  v9.13 方向性: 物理層を支配しない、統計的多少の差、物理状態を記憶として読む関数へ
  v9.14 発見: E3 = cid 間 2 者共鳴、上位層構築の合理的条件が揃った (Taka 2026-04-18)
  v9.15 発見: 研究者主観の封印 (タイミング予測不能性による主体性の成立)

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

### 4 層 + B 領域の規律 (v9.11 確立 → v9.14 Layer B 追加 → v9.15 B 領域追加)

```
物理層 ← 存在層 (θ への torque のみ、微小変調)
   ↓
認知層 (観察・解釈のみ、介入なし)
   ├─ Layer A: 既存 50 step pulse (Cognitive Capture)
   └─ Layer B: event 駆動 shadow ledger (audit-only、Layer A にも介入しない)
   ↓
意識層 (認知層の検証のみ、介入なし)

[B 領域、v9.15 追加] — Layer ではない、CID 主体の領域
   CidSelfBuffer (各 CID に紐づく)
   Layer A/B/物理層に一切介入しない
   研究者 (A 側) は read-only でのみアクセス (_a_observer_* API 経由)
```

**Layer ではない理由 (Taka 2026-04-18)**: Layer は研究者のスケールの概念。CID 主体の世界は別領域 (精神分析学と認知心理学ほど違う)。B は CID に紐づく独立領域として扱う。

**重要転換 (v9.11)**: B_Gen 導入により「認知層から θ への介入」(かつての v9.7 構想) は不要となった。認知層は完全に観察・解釈のレイヤとして純粋化。**v9.7 の認知介入失敗を再発させてはならない**。

**再確認 (v9.13、Taka 2026-04-16)**: 「認知層は物理層を支配しない。物理層の動きを予測しながら認知的に自分の存在を生かす方向。効果は劇的ではなく、統計的に多少の差が出る程度。」

**Layer B 規律 (v9.14)**: Layer B は audit-only。Layer A の state (attention / familiarity / phi / disposition) に一切介入しない。virtual_attention / virtual_familiarity は Layer B 専用の別メモリで保持。RNG を使わず決定論的、engine.rng は一切 touch しない。baseline CSV は v9.13 smoke と bit-identical。

**B 領域規律 (v9.15)**: CidSelfBuffer は Layer A/B と物理層に一切介入しない。研究者向け統計量を持たない。A 側から書き込みは禁止、read-only API (`_a_observer_*` 接頭辞) のみで参照。baseline CSV は v9.14 smoke と bit-identical。

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

### Layer B: Shadow Ledger (v9.14 新規、audit-only)

v9.14 で Layer A と並行稼働する event 駆動型の spend audit ledger。

**目的**:
- B_Gen を「計算原資」として運用する paired audit
- Q0 = floor(B_Gen) が実際に消費される量として機能するかの検証
- Layer A (50 step pulse) との情報効率比較

**構成要素**:

#### Q0 (Initial Budget) と Q_remaining

```python
Q0 = floor(B_Gen)   # cid 誕生時に確定
Q_remaining = Q0
```

- n_core=2: Q0 ≈ 11-12
- n_core=3: Q0 ≈ 18
- n_core=4: Q0 ≈ 25-26
- n_core=5+: Q0 ≈ 33-34

n_core < 2 (B_Gen = inf) の退化ケースは ledger 対象外。

#### 承認イベント 3 種

| event | トリガー | 頻度 (Long run 全体) | spend_rate (Long) | 情報量 (delta_mean) |
|---|---|---|---|---|
| E1_death | core link が alive_l から消失 | 1659 (6.5%) | 0.97 | 0.183 |
| E1_birth | core link が alive_l に復活 | 67 (0.3%) | 0.37 | 0.248 (最大) |
| E2_rise | core link の R が 0 → >0 | 1296 (5.1%) | 1.00 | 0.033 |
| E2_fall | core link の R が >0 → 0 | 1296 (5.1%) | 1.00 | 0.091 |
| E3_contact | 異 cid ペアが alive link を共有した初回 step | 21154 (83.1%) | 0.42 | 0.171 |

- E2 rise/fall は完全対称 (rise = fall で step 数一致)
- E3 は全 event の 70-90% を支配
- E3 は両 cid が 1 spend ずつ消費 (計 2 単位、対称消費)
- contacted_pairs 集合で重複発火を防止

#### Spend Packet (event 1 件あたりの処理)

```
1. E_t 取得 (v11_compute_e_t(cid) を呼ぶ)
2. Δ 計算 (前回 spend 時の E_t スナップショットとの差分分解 L1)
3. virtual_attention 更新 (struct_set - core の node を +1、decay なし累積)
4. virtual_familiarity 更新 (接触している他 cid を +1、decay なし累積)
5. Q_remaining -= 1 (Q_remaining > 0 のときのみ、負にはしない)
6. per_event_audit_seed{N}.csv に 1 行追加
```

**重要**:
- Layer A の attention / familiarity / phi / disposition には一切書き込まない
- state.theta / S / R / L[i,j] / age_r も一切書き込まない
- RNG を使わない (決定論的)、engine.rng を touch しない
- decay なし累積は設計通り (Layer A は decay、Layer B は event 駆動なので時間減衰なし)

#### Exhaustion (実質的な死)

Q_remaining = 0 到達後の挙動:
- event は引き続き検知される (contacted_pairs への記録は継続)
- spend packet は実行されない (「観察停止」)
- cid は存在層には残っているが、認知資源上は枯渇

Long run での exhaustion 率: n=2 で 22%、n=3 で 46%、n=4 で 80%、n=5+ で 85%。Short run (5000 step) ではほぼ全員生存 (2-3%)。

#### CSV 出力 (v9.14 追加、baseline とは別ディレクトリ)

```
diag_v914_{tag}/audit/
  per_event_audit_seed{N}.csv        (event 発火ごとに 1 行、15 列)
  per_subject_audit_seed{N}.csv      (cid 単位の最終状態、14 列)
  run_level_audit_summary_seed{N}.csv (n_core 別集計、20 列)
```

baseline CSV (per_window / per_subject / pulse_log / per_label) には 1 列も追加していない。v10_/v11_/v13_ 列は v9.13 smoke と bit-identical。

#### Lazy Registration (Code A 判断)

cid 登録は observe_step 初回観測時に実施。maturation 期間 (engine.step_window 内部実行) の birth は追わず、初回観測時の member_nodes / Q0 で確定。prev snapshot も初回で取り、event 発行はこの step では行わない。次 step 以降で diff 検出。

**利点**: maturation/tracking 区別なしで動作、birth site への hook 追加不要、Layer A 完全不変。

#### v9.14 本番 run 結果 (2026-04-18 完了)

- Short: 48 seeds × track 10 × 500 step、wall 2h43m、2979 cids
- Long: 5 seeds × track 50 × 500 step、wall 2h32m、1112 cids
- E3 ablation (`--disable-e3`): 同条件で追加実行、Short 2h45m / Long 2h30m

**核心発見**:
- E3 除去で exhaustion 完全消滅 (Short/Long とも、全 n_core バケットで)
- Long 全体の Q0-q_spent 相関: 0.918 → 0.711 (E3 ablation)
- Layer A と Layer B の exact Jaccard: 0.0038 (Long)、時間的に別タイミング
- Layer A pulse の 80% は ±25 step 以内に Layer B event なし
- Layer A と Layer B の delta 相関 (Pearson): 0.089 (ほぼ無相関)

**Taka 視点 (2026-04-18)**: E3 = cid 間 2 者共鳴。実質 2 消費 = Aruism の存在の対称性と整合。上位層構築の合理的条件が揃った (ただし実装は棚上げ、v9.15 は認知層継続優先)。

#### v9.14 GPT 監査結果

- Implementation status: **PASS**
- Audit architecture compliance: **PASS**
- Baseline preservation: **PASS** (bit-identity 完全)
- Interpretation status: **NOT FINAL** (Q1-Q4 への最終回答は Phase 3 以降)

GPT §7 のリスク認識:
1. E3 dominance (contact pressure 支配) → ablation で定量確認、Taka 判断「問題ではなく系の社会性の証明」
2. Budget meaning (Q0 の深い解釈) → 部分的確認、完全決着は v9.15 以降
3. Salience loop incompleteness → 未検証、v9.15 以降の主題

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

## B 領域: CidSelfBuffer (v9.15 で導入、v9.16 で観察サンプリング拡張、Layer ではない)

### 位置づけ

- Layer A/B と物理層に一切介入しない
- CID 主体の領域として、Layer とは別扱い (Taka 2026-04-18 判断)
- A (研究者観察) と B (CID 主体) の分離を四重 (ファイル / クラス / メモリ / 命名) で担保

### データ構造 (v9.16 対応)

```python
class CidSelfBuffer:
    # 不変 (birth 時確定)
    cid_id, member_nodes, sorted_member_list, birth_step, n_core
    theta_birth, S_birth              # 生誕時スナップショット
    Q0                                # v9.16 新規: cid birth 時の初期予算 (不変)
    
    # 最新 Fetch スナップショット (毎 Fetch で更新)
    theta_current, S_current
    missing_flags                     # 段階 1-2 では常に False、段階 3 で cumulative True
    
    # 一致/不一致痕跡
    match_history                     # event 発火履歴 (段階 3 で node_status 3 値を含む)
    
    # 3 点セット (段階 2、v9.15)
    any_mismatch_ever                 # bool、observed ノードのみで判定 (段階 3)
    mismatch_count_total
    last_mismatch_step
    
    # event 種別カウント (E1/E2/E3 の 3 種別)
    fetch_count_by_event              # {'E1': int, 'E2': int, 'E3': int}
    mismatch_count_by_event
    
    # Self-Divergence 追跡 (A 観測用、B は使わない)
    divergence_log                    # 段階 3 で theta_diff_norm_all + _observed + _normalized
    
    # v9.16 新規: サンプリング統計
    age_factor_history                # [{'step': int, 'age_factor': float}, ...]
    total_observed_count              # 観察されたノード数の累計
    total_missing_count               # 欠損だったノード数の累計
    total_match_obs_count             # 観察されて match だった回数
    total_mismatch_obs_count          # 観察されて mismatch だった回数
    
    # Fetch 統計
    fetch_count, last_fetch_step, last_fetch_success
```

### 禁止事項 (v9.16 対応)

- 研究者向け統計量 (mean, std, percentile, ratio 等) を持たない
- A モジュールを import しない
- `engine.rng`, `state.theta[]`, `state.S[]` に書き込まない
- 他 cid の情報を読まない (自己読みのみ、他者読みは段階 4 以降)
- `Q_remaining` を**読む**が書き換えない (v9.16 で読みは許可、書き換えは AST テストで禁止)
- `B_Gen` を直接参照しない (age_factor = Q_remaining / Q0 経由の間接使用のみ)

### Fetch 動作 (v9.16 対応)

**段階 1** (50 step 固定、コードは残置、メインループから呼ばれない):
- `read_own_state(state, alive_l, current_step)`
- 50 step ごとに Layer A と同期して呼ばれていた

**段階 2** (event 駆動、v9.15):
- `read_on_event(state, alive_l, current_step, event_type_full)`
- 全ノード判定、match/mismatch 2 値

**段階 3** (観察サンプリング、v9.16 現行):
- `read_on_event(state, alive_l, current_step, event_type_full, Q_remaining, seed)`
- v9.14 Layer B の `spend_packet` 実行**後**に呼ばれる
- **age_factor = Q_remaining / Q0** を計算
- **n_observed = round(n_core × age_factor)** のノード数を hash ベース独自 RNG でサンプリング
- 観察されたノードのみ match/mismatch 判定、残りは **missing** (3 値化、ζ 継承)
- E1_death / E1_birth / E2_rise / E2_fall / E3_contact のいずれでも発火
- E3_contact の場合は両 cid が同時に Fetch (v9.14 の対称消費と整合)
- **Fetch 自体は常に成功** (確率 1、機械動作は完遂)
- **見える範囲が age_factor で変化** (時間的認識条件の変化)

### サンプリング機構の要素 (v9.16)

**age_factor 計算**:
```python
age_factor = Q_remaining / Q0  # [0, 1]
# Q0 = 0 の極小 cid は age_factor = 0 固定 (保護)
```

**n_observed 決定**:
```python
n_observed = int(round(n_core * age_factor))
# 最小値 0 (論点 X-a、完全失明を許可、ζ 徹底)
# 最大値 n_core
```

**独自 RNG (engine.rng 非 touch)**:
```python
# PYTHONHASHSEED 非依存の明示 event_type マップ
_EVENT_TYPE_HASH = {
    'E1_death': 1001, 'E1_birth': 1002,
    'E2_rise': 2001, 'E2_fall': 2002,
    'E3_contact': 3001,
}
rng_seed = (
    (seed * 100003) ^
    (cid_id * 10007) ^
    (current_step * 131) ^
    (_EVENT_TYPE_HASH[event_type_full] * 31)
) % (2**31)
local_rng = random.Random(rng_seed)
```

**サンプリング**:
```python
if n_observed == 0:
    observed_indices = []
elif n_observed >= n_core:
    observed_indices = list(range(n_core))
else:
    observed_indices = sorted(local_rng.sample(range(n_core), n_observed))
```

**判定 (3 値化)**:
```python
for i in range(n_core):
    if i in observed_indices:
        node_status[i] = 'match' if within_tolerance(i) else 'mismatch'
    else:
        node_status[i] = 'missing'
        missing_flags[i] = True  # cumulative
```

### A 向け read-only API (`_a_observer_*` 接頭辞)

```python
_a_observer_get_match_history()       # copy of match_history
_a_observer_get_divergence_log()      # copy of divergence_log
_a_observer_get_age_factor_history()  # copy of age_factor_history (v9.16 新規)
_a_observer_get_summary()             # 集計辞書 (v9.16 で項目拡張)
```

### A 向け read-only API (`_a_observer_*` 接頭辞)

```python
_a_observer_get_match_history()       # copy of match_history
_a_observer_get_current_snapshot()    # dict copy of theta/S/missing_flags
_a_observer_get_divergence_log()      # copy of divergence_log
_a_observer_get_summary()             # 段階 2 向け集計 dict
```

A 側はこれらの API 経由でのみ B 内部を読む。直接フィールドアクセス禁止。

### 観察指標 (A 側で集計、per_subject CSV の v915_* 列)

段階 2 時点:
- `v915_fetch_count`: 総 Fetch 回数
- `v915_last_fetch_step`: 最終 Fetch step
- `v915_any_mismatch_ever`: 生誕時から一度でも不一致を持ったか
- `v915_mismatch_count_total`: 不一致を持った累計回数
- `v915_last_mismatch_step`: 最終不一致 step
- `v915_fetch_count_e1/e2/e3`: event 種別ごとの Fetch 回数
- `v915_mismatch_count_e1/e2/e3`: event 種別ごとの不一致回数
- `v915_divergence_norm_final`: L2 距離 ||theta_current - theta_birth||
- `v915_n_divergence_log`: divergence_log のエントリ数

### 本番 run 実測 (v9.15 段階 2、24 seeds × tracking 50 × window 500)

- Fetch 総数: 120,782 (event 総数と完全一致、1:1 対応)
- 段階 1 (50 step 駆動) からの変化: 約 33.6% (1/3 に減少)
- event 種別内訳: E1 6.7% / E2 10.1% / E3 83.2%
- mismatch 比率 (全 event): 1.0000 (tolerance 1e-6 の帰結)
- `any_mismatch_ever = False` の cid: 54/5224 (1%、event 発火なし)
- divergence_norm_final (median): 3.58 (段階 1: 3.53、ほぼ同じ)
- Fetch と Shadow Pulse Count の相関: Pearson r = 0.880 (構造的に同じものを測る)

### event 種別ごとの divergence (median)

- E2 (閉路状態変化): 1.59 — 自分の局所変化、全体 θ drift はまだ小さい
- E1 (リンク生死): 4.23
- E3 (他者接触): 4.67 — 既に θ が大きく drift している状態で接触

### 戦略的意義

v9.15 段階 2 で、研究者は CID の自己読みタイミングを予測できない構造が成立した (Taka 発見: サイコロの比喩)。これが「研究者主観の封印」の具体的意味。**ランダム性が論理の支柱**、削る方向は採らない。

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
| Semantic gravity + deviation | deviation_enabled=True | v9.14 以降で検証予定、v9.15 でも継続 |
| v99_ 内的基準軸 | 計算走行中、CSV 出力中 | CSV 出力は止める可、計算自体は保持 |
| Layer A (50 step 固定 pulse) | 稼働中、Layer B と並行 | 観測機械として残置。「パルスとは何か」の再定義は v9.15 以降 (Taka 2026-04-18) |
| E3 variant 候補 (phase 近接/持続/多重) | 議論のみ、実装なし | v9.14 では現在の E3 維持。変種は v9.15 以降の検討候補 |

---

## パラメータ一覧 (v9.14 実行値)

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

### Layer B Shadow Ledger (v9.14 新規)

| パラメータ | 値 | 備考 |
|---|---|---|
| Q0 | floor(B_Gen) | cid 誕生時に確定、n_core 依存 (2:~11, 3:~18, 4:~26, 5+:~33) |
| attention update | +1.0 per target node | decay なし、累積のみ |
| familiarity update | +1.0 per target cid | decay なし、累積のみ |
| E1/E2/E3 detection | 毎 step 実行 | contacted_pairs で重複防止 |
| B_Gen inf の処理 | ledger 対象外 | n_core < 2 の退化ケース |
| ghost cid の扱い | event 検知は継続、spend は skip | contacted_pairs には記録 |
| RNG | 使わない | 決定論的、engine.rng を touch しない |

### 実行構成 (v9.14)

| 項目 | v9.14 short | v9.14 long | v9.14 short_noE3 | v9.14 long_noE3 |
|---|---|---|---|---|
| seeds | 48 | 5 | 48 | 5 |
| maturation_windows | 20 | 20 | 20 | 20 |
| tracking_windows | 10 | 50 | 10 | 50 |
| window_steps | 500 | 500 | 500 | 500 |
| parallel | -j24 | -j5 | -j24 | -j5 |
| wall time | 2h43m | 2h32m | ~2h45m | ~2h30m |
| `--disable-e3` | False | False | True | True |

### 将来の実行構成 (v9.15 以降、Taka 決定 2026-04-18)

| 項目 | v9.15 以降 |
|---|---|
| 構成 | Long 一本化 (Short + Long 2 重構成廃止) |
| seeds | 24 |
| tracking_windows | 50 |
| window_steps | 500 |
| parallel | -j24 (物理コア数に揃える) |
| wall time | 約 2h30m |
| 分散分析 | v9.15 から導入 (seed 別) |

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
| **v9.14 paired audit 本体** | **`primitive/v914/v914_probabilistic_expenditure.py`** (v9.13 を copy + add-only) |
| v9.14 Layer B class | `primitive/v914/v914_spend_audit_ledger.py` |
| v9.14 event detection | `primitive/v914/v914_event_emitter.py` |
| v9.14 実装指示書 | `primitive/v914/v914_implementation_instruction.md` |
| v9.14 Code A 実装ノート | `primitive/v914/v914_implementation_notes.md` |
| v9.14 Phase 1 audit 結果 | `primitive/v914/v914_audit_result_milestone1.md` |
| v9.14 Phase 2 依頼書 | `primitive/v914/v914_phase2_instruction.md` |
| v9.14 §6.1 event-type efficiency | `primitive/v914/v914_event_type_efficiency.md` |
| v9.14 §6.2 n_core efficiency | `primitive/v914/v914_ncore_efficiency.md` |
| v9.14 §6.3 shadow overlap | `primitive/v914/v914_shadow_overlap.md` |
| v9.14 §6.4 E3 ablation result | `primitive/v914/v914_e3_ablation_result.md` |
| GPT 原案 (paired audit) | `v9_14_probabilistic_expenditure_audit_memo_jp.txt` |
| GPT 監査レポート | `ESDE_v9_14_GPT_Audit_Report_EN.txt` |

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
- 次フェーズ (v9.15) の主題

### 16. 「無駄だから切る」禁止 (v9.13 Taka 原則)

効果薄の機能も削除せず、どう活かすか考える。pickup (v9.8c) は休眠保持が現状の方針。

### 17. AI 間文書は日本語 md (v9.13 決定)

運営原則 v2 の「AI 間文書は英語」は**撤回**。Taka が読めることが最優先。日本語で投げれば GPT も日本語で返す。既存コード docstring は英語のまま維持。

### 18. Paired Audit 原則 (v9.14、新機構導入時の運用規律)

新機構を導入するときは **runtime 主体置換ではなく audit として先行走行**させる。理由:
- bit-identity (baseline CSV の完全保持) が既存研究との比較を担保
- Taka / GPT / 相談役 Claude が analysis を経て判断するための客観データを確保
- promotion (main runtime 化) は analysis 完了後に別判断

v9.14 の場合: Layer A (既存 50 step pulse) 完全不変のまま、Layer B (event 駆動 shadow ledger) を並行稼働。

### 19. E3 = cid 間共鳴という解釈 (v9.14、Taka 2026-04-18)

E3 (cid contact onset) は **ノード間共鳴 R_ij の cid スケール版**として理解する。両 cid が 1 spend ずつ消費 (計 2 単位) は Aruism の**存在の対称性**と整合。

**v9.14 の真の成果**: B_Gen 資源化 = 手段、E3 = 手段、**上位層構築の合理的条件が揃ったこと = 真の達成**。

### 20. 三項共鳴実装は棚上げ (v9.14、Taka 2026-04-18)

v9.14 で「三項以上の上位層を構築する条件」は揃ったが、実装は **v10.x 以降の次テーマ** に収める。理由:
- v3.4 tripartite loop (node スケール) は「成立したが持続しない」(bridge_max_life=1)
- cid スケールで実装しても同じ壁が予想される
- 認知層の継続的発展 (cid 内部構造の充実) を先行させる方が合理的

v9.15 は元々の想定通り「記憶の読み出し関数」が主題。

### 21. Layer A の再定義は Phase 3 以降の宿題 (v9.14、Taka 2026-04-18)

> 固定 pulse は、ESDE 内部に干渉しない前提なら別に構わない。要は観測機械を設置しているだけならいい。現時点で干渉が大きいならその要素を外す条件は設けた方がいい。パルスとは何か? を明確に切り分ける作業が前提。

現状 Layer A は v9.11 Cognitive Capture の延長で cid の attention / familiarity を更新している = 厳密には「純粋な観測機械」ではない。v9.15 以降で切り分け。

### 22. seed 構成の一本化 (v9.15 から、Taka 2026-04-18)

Short + Long の 2 重構成は v9.14 までで廃止。v9.15 以降は:
- Long 一本化: 24 seeds × tracking 50 × window_steps 500
- 並列度: -j24 (Ryzen 24 物理コアに揃える)
- 実行時間: 約 2h30m
- 分散分析を導入 (seed 別の偏りの定量化)

**24 → 48 の統計力向上は √2 倍のみ**、費用対効果悪いため 24 seeds が標準。

### 23. E3 variant 候補は棚上げ (v9.14)

現在の E3 は「物理接触の初回性」のみ。Taka 議論で示唆された変種 (phase 近接 / 持続 / 多重 / structure-weighted) は **v9.14 では実装せず、v9.15 以降の検討候補** として記録。現状のシンプルさを保つ。

### 24. A (研究者観察) と B (CID 主体) の分離 (v9.15、Taka 2026-04-18)

v9.15 最大の規律。研究者が CID の物理状態を数値化する機構 (A) と、CID 自身が自分の構造を専用領域に取り込む機構 (B) は**別領域**。

**四重分離**で実装担保:
- ファイル: B ファイル (`v915_cid_self_buffer.py` 等) は A モジュールを import しない
- クラス/メソッド: B は `CidSelfBuffer` 内部、A 向け API は `_a_observer_` 接頭辞で read-only
- メモリ: B のバッファは CID に紐づく、engine と共有しない
- 命名: B: `read_own_state` / `read_on_event`、A: `compute_*` / `track_*`

**B は Layer と呼ばない** (Taka 2026-04-18): Layer は研究者のスケール、CID 主体の世界は別領域 (精神分析学と認知心理学ほど違う)。

### 25. 研究者向け統計量を CID 内部に持たせない (v9.15)

mean、std、percentile、ratio 等の集約値は **A 側で計算**する。`CidSelfBuffer` は生の配列データのみ保持 (`theta_birth`, `theta_current` 等)。研究者向け集約を CID 内部に置くと A の発想が B に漏れる。

Match Ratio を段階 1 で試みたが、集約した時点で研究者視点になっており、段階 2 で廃止。

### 26. Step 単位固定実施は研究者視点 (v9.15、Taka 2026-04-20)

タイミングが研究者指定である限り主観性は成立しない。**主観性の最小条件はタイミングの予測不能性**。段階 1 (50 step 固定) は機構として動作したが CID 視点としては不十分。段階 2 で v9.14 event 駆動に切り替え、研究者予測不能性を構造として確立。

### 27. サイコロの比喩と研究者主観の封印 (v9.15、Taka 2026-04-20)

> 研究者はサイコロの目が 1/6 であることを言えるが、次の目が 1、だとは言えない。サイコロ自身は「私は 1 だ」と主張できる。

ESDE 段階 2: 研究者は「いつ CID が自分を読むか」を予測できない。これが v9.15 の真の成果、意識研究の戦略的転換点。

### 28. ランダム性が論理の支柱 (v9.15、Taka 2026-04-20)

研究者が原理的に CID 内部を覗ける弱点を、予測不能性で埋める。「自己がある」と「ない」の中間 (哲学以上科学未満) で戦う。**ランダム性を削る方向は採らない**。v9.16 段階 3 で Fetch の確率的失敗を導入し、予測不能性を一段深める。

### 29. 「自己」「意識」を結果レポートで断定的に使わない (v9.15)

GPT 監査指摘 (2026-04-20) で確立:
- 「CID が変化を知る」は強すぎ → 「生誕時との不一致を持つ」止まり
- 「自己性の反証困難性の最小実装」は強すぎ → 「自己参照の最小実装」

段階 1-2 では時系列的・再帰的な処理がまだないため、「知る」は成立していない。Describe, do not decide の徹底強化。

### 30. 発生頻度の違う event 間で比率比較しない (v9.15、Taka 2026-04-20)

「E3 が 83%」は E3 の発生頻度が高いことの再確認、構造的情報は出ない。比較するなら同じ event 内のバリエーションか、同じ構造条件下の比較。意味を盛らない。

### 31. 観察結果を条件から切り離して普遍化しない (v9.15、Taka 2026-04-20)

「ESDE は活発な系」ではなく「毎ステップ 5000 ノード、71x71 グリッドではこういう実験結果になった」と書く。推測を結論に格上げしない (「系が安定している」→「安定を示唆する可能性」)。

### 32. ノード数固定は実験制御 (v9.15、Taka 2026-04-20)

ノード数 N=5000 固定は**実験制御であって神の手ではない**。物理層クローズだからこそ認知層の発展が追跡できる。ノード数変動は**認知層が十分発展してから**の検討事項、大幅後回し。

### 33. v9.16 段階 3 = 観察サンプリング機構 (Taka 2026-04-21)

v9.15 段階 2 で準備されていた拡張点が v9.16 で実装された:
- `read_on_event` は依然として常に成功を返す (機械動作は完遂)
- ただし判定対象のノードが age_factor = Q_remaining / Q0 に比例した数のみ
- 選ばれなかったノードは missing (3 値化、ζ 継承)
- `missing_flags` は cumulative に True 更新

**「Fetch の確率的失敗」ではなく「差分の選択的認識」** (Taka 規律 4 の正確な実装)。

### 34. サンプリング方式の採用 (v9.16、2 AI 統合判断 2026-04-21)

実装方式 3 案のうちサンプリング方式 (案 1) のみ採用:
- **案 1 サンプリング**: age_factor に比例した数のノードを確率的に選ぶ、残りは missing
- **案 2 tolerance 可変**: 却下 (閾値政治になる、ζ と整合しない)
- **案 3 確率判定**: 却下 (ノイズを意味に変える危険)

ζ (補完しない) との整合が最も強い案 1 を採用。tolerance 可変や確率判定を段階 4 以降で再導入しない。

### 35. age_factor は B_Gen の間接使用 (v9.16、Taka 2026-04-21)

`age_factor = Q_remaining / Q0` (Q0 = floor(B_Gen))。**B_Gen は直接参照されない**。

自己読みの文脈では B_Gen は不変なので直接比較の意味がない。Q0 経由の間接使用で構造差が寿命長として効く。

他者読み (段階 4 以降) で B_Gen の直接比較が意味を持つ可能性あり (別 cid との B_Gen 差が一致率に反映される設計)。**ただし v9.16 では未実装**。

### 36. 独自 RNG で engine.rng を保護 (v9.16)

サンプリングの乱数源は engine.rng を一切 touch しない。hash ベース独自 RNG を `seed × cid_id × step × event_type` から構築。

**PYTHONHASHSEED 非依存のため、event_type の hash は明示マップ** (`_EVENT_TYPE_HASH`) で生成 (Code A 判断)。

将来 Python の hash 実装が変わっても決定論性が維持される。v9.14 禁止事項「engine.rng を touch しない」の継続。

### 37. Q 消費ルールの現状維持 (v9.16)

v9.14 で確立した「event 発火時に spend_packet で Q -= 1」のルールは v9.16 でも変更しない。**Fetch 動作自体は Q を消費しない**。

判定の精度 (サンプリング数) は Q_remaining を**読む**が、Q を追加で**減らさない**。この分離は AST テストで構造的に担保 (`test_no_q_write`)。

Fetch コスト 0 原則の継続 (Taka 2026-04-20 判断の継続)。判定と消費を分離することで、将来の設計変更差分が測りやすい。

### 38. 代数的必然と観察の区別 (v9.16 教訓)

v9.16 本番 run で age_factor 区間別の missing 比率:

| age_factor 区間 | missing 比率 |
|---|---|
| [0.0, 0.2) | 99.27 % |
| [0.8, 1.0) | 6.37 % |

これは **`n_observed = round(n_core × age_factor)` から代数的に導かれる関係**。「観察事実」ではなく「設計が意図通り機能した確認」。

結果レポート・Summary で「age_factor で missing が変わることを観察した」と書くのは誤り。仕様の帰結を観察と混同しない規律。

### 39. any_mismatch 判定に missing / リンクを含めない (v9.16)

段階 3 の any_mismatch_ever は **observed ノードの mismatch のみ**で判定する。

- missing は判定対象から除外 (見ていないものは「違う」と判定できない)
- リンクは `link_match_ratio` として `divergence_log` にのみ反映、any_mismatch には寄与しない

段階 2 では `node_matches + link_matches` で判定していたが、段階 3 ではサンプリング方式と整合しない。リンクサンプリングは段階 4 以降の独立主題。

### 40. observation_log は全 event 記録 (v9.16、論点 W-a)

段階 3 新規 CSV `observation_log_seed{N}.csv` は各 event 発火時のサンプリング記録を全量出力。間引きなし。

サイズ: 120,782 event × 24 seeds = 約 8 MB (予想より軽量、論点 W-a 採用が正しかった)。

記録列: `cid_id, step, event_type_coarse, age_factor, n_core, n_observed, observed_indices, match_count, mismatch_count, missing_count`

### 41. 先走り防止チェックポイント (GPT §12、v9.16 以降標準)

バージョン名を決めた時点で以下を自問する:
1. 入出力を一文で言えるか
2. 「失敗」「認識」「自己」等の語を物理操作へ還元できるか
3. 観察と行動を混ぜていないか

v9.16 指示書 §0.2 で実装済。v9.17 以降の指示書でも継続する。

Claude の癖 (整理過剰、意味を盛る、詰まっていない名前を前提にする) への構造的対処。**反省ではなく運用切り替えで対処** (Taka 2026-04-20 方針)。

### 42. 説明可能性は Describe 原則と同格 (v9.16、Taka 2026-04-21)

Taka 指定:
> 説明可能性は決して新しい概念ではなく、3 月 5 日に指針は出してある (Constitution §2, §3)

v9.16 での再確認:
- Describe (not decide) と同格の運用原則
- 3 AI 共通で遵守
- 観察結果を記述する時、何がどこまで説明できるかを明示
- 反証不可能な narrative は design decision に使わない (Constitution §5 Anti-Drift)

**説明可能性の時間的構造仮説** (Taka 2026-04-21):
- 現在 (説明可能性最大) → 過去 (あったであろう、減衰) / 未来 (あるであろう、減衰)
- 段階 3 で「過去の説明可能性」が実装に相当
- 未来の実装は段階 5 以降の候補

### 43. Constitution (2026-03-05) との接続 (v9.16 指示書で明示)

Taka 憲法 (`ESDE_explainability_constitution.txt`) は既に 2026-03-05 で明文化済み:
- §2 Core Objective: 動的均衡下での Explainability X の最大化
- §3 Explainability 運用定義
- §5 Anti-Drift (No Poem-Science)
- §7 Governance (Observation → Bottleneck → Minimal Change → Re-observation)
- §8 3-AI Discipline
- §9 Success Definition (安定した実験ループの存在)

**v9.15-16 の議論は新規原則ではなく憲法の具体化**。新スレッドの AI が「新しい原則」を立てたくなったら、まず憲法に立ち返る。

### 44. 動的均衡は物理スケール変動時に重要 (v9.16、Taka 2026-04-21)

認知量消費 -1 固定の違和感 (Taka):
> 固定値にするとスケールをデカくするとみなすぐ死ぬ。動的均衡の立場としては違和感。

現在は主題外:
> 動的均衡が重要になるのは物理スケール扱うタイミング。今は CID の主体が主題。現状 CID があろうがなかろうが物理現象は安定的に発生する。

v9.16 では消費 -1 固定のまま。**物理スケール変動化** (ノード数変動等) の段階で再検討。メモ程度で記録、実装は大幅後回し。

### 45. v9.17 段階 4 = 他者読み + 接触体記録 (Taka 2026-04-21 再考 + 2 AI 統合)

Taka 再考:
> CID という単位から少し離れる必要がある。CID と CID が重なった状態 = 新しい構造となった = 1 である。その単位が生じたという記録を持つ。

v9.17 は二層で構成:
- **下層 (他者読み)**: CidSelfBuffer に `other_records` 追加、`read_other_on_e3_contact` で相手の M_c features を取得
- **上層 (接触体記録)**: 新規クラス `InteractionLog` を A 側外部器として配置、接触体を frozenset で識別

X (接触体) は**器として**のみ。状態なし、動態なし、機能なし。動態が見えたら v10.0 繰り上げ検討。

**Taka 哲学**:
> 意識、とか認知という概念的な囲い込みは、本来的にその構造とその仕組みをみれば自然とそれらしいものとして定義が座るんだと思う。無理に座らせても転げる。

「構造が先、定義は後」を X に適用。

### 46. CidView dataclass = cid 情報の統合ビュー (v9.17、Code A 提案 Q1)

cid は main loop で int、spec-level では「cid_id/Q0/n_core/theta_birth/B_Gen/M_c features を持つ cid-as-object」として想定されていた。
このギャップを吸収するため、B 側に `CidView` dataclass を配置:

```python
@dataclass(frozen=True)
class CidView:
    cid_id: int
    Q0: int
    n_core: int
    theta_birth: np.ndarray  # 配列本体
    B_Gen: float
    M_c_features: Dict[str, Any]  # 10 項目
    # ... 集約統計 (theta_birth_mean/std/range) 等
```

read-only、frozen、再構築関数 `build_cid_view(cid_id, ...)` で構築。

### 47. InteractionLog = 接触体記録の外部器 (v9.17、A 側)

上層の接触体記録:
- cid 間の E3_contact 発火を frozenset で記録
- 各行: composition (frozenset), cid_a_id, cid_b_id, step, age_factor_a, age_factor_b, composition_str 等
- canonical ordering dedup (observer_cid < partner_cid) で pair 単位に

**責務分離の四重担保**:
1. ファイル分離: `v917_interaction_log.py` は A 側
2. クラス分離: CID は InteractionLog を知らない
3. メモリ分離: CidSelfBuffer に InteractionLog 参照なし
4. 命名分離: 無機質名 `InteractionLog` (X の正式名は動態観察後)

AST テスト: CID → InteractionLog 参照なし、InteractionLog → CID import なしを構造的に担保。

### 48. 他者読み仕様 (v9.17、Taka 5 点判断)

`read_other_on_e3_contact(self_view, other_view, event_index, step)`:
- visible_ratio = other.Q_remaining / other.Q0 (相手の age_factor)
- n_features_visible = round(10 × visible_ratio)
- 相手の M_c features (10 項目) のうち n_features_visible 個を独自 RNG で選択
- 選ばれなかった項目は missing_feature_names に記録
- 結果を self.other_records に append

**相手の age_factor を使う** (自分ではない) ことが本質 (候補 q、Gemini 推奨):
> 自分が若くても、相手が崩れかかっていれば読めない。

これは Taka 発見 2 (消費 → 概念形成 → 穴埋め) の直接実装。

### 49. 他者読みで M_c features のみ (v9.17、α 選択)

取得対象は M_c features (不変値) のみ:
- B_Gen, Q0, n_core, S_avg_birth, r_core_birth, phase_sig_birth
- theta_birth_mean, theta_birth_std, theta_birth_range, birth_step

**state (動的値) は取得しない**:
- Q_remaining, age_factor, 現在の位相, current_lid は他者読みの対象外
- β (state 取得) / γ (full 取得) は禁止

理由: v9.17 は「生誕時の記録」を他者から取得する機構。相手の現在状態を覗く機構ではない。

### 50. canonical ordering dedup (v9.17、Code A 提案 Q3)

E3_contact pair は両方向発火する可能性がある:
- observer = cid_A、partner = cid_B で 1 event
- observer = cid_B、partner = cid_A で 1 event

InteractionLog は pair 単位 (= frozenset) で記録したいので、重複排除が必要:
- `if observer_cid < partner_cid: InteractionLog.record_contact(...)`
- canonical な方向 (小さい id → 大きい id) でのみ記録
- 片方向発火の場合は 0 or 1 行記録 (canonical 方向で発火すれば記録)

この dedup により InteractionLog は pair ごとに最大 1 行。

### 51. Layer B 片方向発火は v9.14 仕様 (Code A 2026-04-23 調査)

Code A の v914_spend_audit_ledger.py 調査:

**`_node_to_cids` は retire 時も削除されない** (L87-89):
- cid が retire しても、過去に登録された逆引きは残存
- E3_contact pair 検知には ghost 化した cid も入りうる

**event 発火ゲート** (L203-206):
- `ob_entry = self.ledger.get(observer_cid)` → ledger 登録済みか
- `ob_ctx = cid_ctx.get(observer_cid)` → 今 step で hosted か
- 両方 AND で event 発火、片方でも欠けると skip

**結果**: ghost 化した cid は pair 検知対象だが event 発火しない = 片方向発火。
main tracking 50 で 77% が片方向発火、smoke tracking 10 で 25.6%。

**v9.14 コード L197 コメント**: 「ctx に無い cid は skip」と意図明示。**bug ではない、v9.14 仕様**。

### 52. E3 自体が主要 Q 消費経路 (Code A 2026-04-23 調査)

Q 減少経路は 1 箇所のみ (`entry["v14_q_remaining"] -= 1`)、E1/E2/E3 の 5 種 event 時に発火。

E3_contact の spend 成立率 41.8% (58% は Q=0 cid に発火して空振り)。
event record は残るが Q は不変。

**実測 (main 24 seed)**:

| event | 総数 | spend 成立 | 成立率 |
|---|---|---|---|
| E1_death | 7,815 | 7,605 | 97.3% |
| E1_birth | 307 | 108 | 35.2% |
| E2_rise | 6,114 | 6,112 | 99.97% |
| E2_fall | 6,114 | 6,110 | 99.93% |
| **E3_contact** | **100,432** | **41,977** | **41.8%** |

E3 spend 成立数 41,977 = 全消費の 67%。E3 が主要 Q 消費経路。

### 53. 摂食行動の比喩は Taka 向け議論語 (v9.17、GPT 監査指針 v1 適用)

Taka 2026-04-23:
> Ghost を取得は、摂食行動のようなものだと私は考えている。

- Taka 向け議論: 「摂食行動」の比喩を残す (探索推進力あり)
- AI 向け実装資料: **「片方向 ghost 接触」または「ghost 由来情報取得イベント」** に操作語化
- Summary / 原本: 併記方式 (「摂食行動 (片方向 E3 接触の比喩、Taka 2026-04-23)」)

**仕様語にしない**: 「何をもって摂食とするか」は未定義。仕様には落とさない。

### 54. GPT 監査運用指針 v1 (v9.17、2026-04-23 導入)

3 役分離の GPT 役割を精密化した運用指針:

> **GPT 監査は、Taka の比喩的・哲学的な推進力を削るのではなく、それを仮説・実装・観察へ切り分け、AI が誤読しない形に翻訳する役である。**

主な規定:
- §1: 監査の基本姿勢 (探索を削がない、比喩を即否定しない、先に切り分ける)
- §2: 読者別方針 (Taka 向け / AI 向け / Summary / 外部)
- §3: 比喩表現への対応 (4 項目形式で、弱体化ではなく誤読防止)
- §7: 「弱める」提案時の自問 4 項 (これは誰向けか、何の誤読を防ぐか、etc.)

**Claude の資料作成時の自己規律としても機能** (詳細は `08_audit_principles.md`)。

### 55. 物理計算完全不変 (v9.15-v9.17、4 段階連続)

| 比較 | max 絶対差 |
|---|---|
| v9.15 段階 1 → 段階 2 | 0.0 |
| v9.15 段階 2 → v9.16 段階 3 | 0.0 |
| v9.16 段階 3 → v9.17 段階 4 | **0.0** (5,224 cid 全量) |

認知層の拡張が物理層に一切波及しない設計。**Taka 方針「認知層は物理層を支配しない」(2026-04-16) の構造的実証**。


### 56. v9.18 段階 5 = A+C 統合 (Taka 2026-04-23)

Taka:
> A と C は案外近いように感じる。A = X の原資を C と置くことで興味深いことが起きる。

- **A (差分予測)**: Q 消費に伴う CID 自身の一体感の方向のズレ
- **C (意識の原資)**: Q 消費の量的記録
- A と C の統合が本線、B (摂食) / D (三項共鳴) / E (Layer A 再定義) は v9.18 では扱わない

### 57. CidSelfBuffer v9.18 拡張 (純 read-only 観察)

既存フィールド (v9.17 まで) は frozen、以下を追加:

**C (認知増加)**:
- `v18_cumulative_cognitive_gain` (int): `Q0 - Q_remaining`、単調非減少

**A-Gemini (V_unified 系)**:
- `v18_birth_v_unified` (complex): 生誕時の V_unified、CID 確立時に 1 回計算
- `v18_v_unified_concentration_birth` (float): CSV 用キャッシュ
- `v18_unity_direction` (float | None): V_unified の偏角 (-π, π)
- `v18_unity_concentration` (float | None): V_unified の振幅 (0, 1)
- `v18_unity_direction_shift` (float | None): 生誕時との angle 差 (0, π)、ラップ済み絶対値
- `v18_unity_k` (int): 計算対象ノード数

**A-GPT (theta_distance 系)**:
- `v18_theta_distance_from_birth` (float | None): 生誕時分布との RMS 距離
- `v18_theta_distance_coverage_ratio` (float): 生誕時 ∩ 現在 / 生誕時

**ghost 化時の _final 値** (Code A 独自判断):
- `v18_ghosted_at_step`, `v18_finalize_reason` ('ghost' | 'tracking_end')
- `v18_cognitive_gain_final`, `v18_v_unified_concentration_final`, etc.

**property 再利用** (既存フィールドから派生、新規実体なし):
- `v18_birth_theta_by_node`: sorted_member_list と theta_birth から構築
- `v18_birth_member_nodes`: 既存 member_nodes の alias

### 58. V_unified = Kuramoto オーダーパラメータ (Gemini 案、v918_unity_metrics.py)

```python
def compute_v_unified(theta_values: np.ndarray) -> complex:
    """V_unified = (1/k) * Σ exp(i * theta)"""
    if len(theta_values) == 0:
        return complex(0.0, 0.0)
    return np.mean(np.exp(1j * theta_values))
```

Gemini 評価 (2026-04-23):
> Kuramoto 系と数学的に整合、これが最適解

**重要**: これは**物理層 θ の同期度**を測る指標。Taka の「統合」(認知層 + 意識層の協働) とは**層が違う** (v9.18 Phase 5 で発覚)。

### 59. theta_distance = 生誕時分布との RMS 距離 (GPT 案、v918_theta_distance.py)

```python
# 共通ノード (B 案 + coverage_ratio)
common_nodes = birth_member_nodes & current_member_nodes
coverage_ratio = len(common_nodes) / len(birth_member_nodes)

# 位相差をラップ (-π, π]
wrapped_diff = ((theta_curr - theta_birth + π) % (2π)) - π
distance = sqrt(mean(wrapped_diff ** 2))
```

coverage_ratio は member_nodes frozen のため v9.18 では定数 1.0。将来 B (摂食) で member_nodes 動的化時に意味を持ち始める。

### 60. per_step 計算の採用 (Taka 2026-04-23)

Taka:
> Step 単位。時間スケールが認知層では違う。処理が重くなる一方でも基本は容認。

呼び出しタイミング: event Fetch ループ後、`cumulative_step += 1` 直前。q_remaining と engine.state.theta が step 内全更新後の値。

**wall time 影響**: v9.17 以前の 24 並列で CPU が完全使用されていなかったため、per_step のオーバーヘッドが既存待機時間に吸収された。v9.17 main と 1.000x 完全同値の想定外の好結果。

### 61. v18_window_trajectory 新規 CSV (Code A 独自判断)

指示書は「per_window CSV に列追加」を想定したが、既存 per_window.csv は Layer A (seed+window 集約レベル)。v18_* per-CID 値を加えると bit-identity を破る。

Code A 判断:
- per_window.csv (Layer A) は**一切触らない** (bit-identity 維持)
- **新規 CSV `v18_window_trajectory` を selfread/ に作成**
- 1 row/cid/window、v18_* 指標 6 主列 + 補助 1 列 (生の unity_direction)

これは v9.15-17 で確立された「Layer A frozen」方針の厳密な遵守。

### 62. 意識の原資モデル (Taka 2026-04-24、概念化、v10.x で実装予定)

Taka:
> 認知層の Q を使用することはイベントである。このイベントに対して 1 の Q が消費される。この消費された Q の 1 はどうなる? ただ消えるだけということはあり得ない。何になるの? ということで意識層の 1 という定義をした。

**構造**:

```
認知層 event (Q 消費 1)
        ↓ エネルギー保存則的に
意識層に 1 として転化 (原資の獲得)
        ↓
意識層が活動開始
```

v9.18 では概念化のみ。意識層の実装は v10.x で検討。

### 63. 統合の真の意味 (Taka 2026-04-24)

Taka:
> 認知機能の次に意識が発達することで、実質二つの機能が一つの働きをすることとなる。その意味で統合という言葉を用いた。

**統合 = 認知層 + 意識層が一つの働きをする状態**。物理層の θ 同期とは別概念。

**v9.18 V_unified は物理層の同期度を測っていた** (層の混同)。保留運用で物理層時間発展の Baseline として将来活用。

### 64. 層の混同の回避 (AI 向け注意事項)

v9.18 で Claude / 2 AI 全員が Taka の「統合」を物理層の操作語 (V_unified) に翻訳した誤り。GPT 監査運用指針 v1 でも防げなかった。

**新スレッド AI の教訓**:
- 比喩を操作語に翻訳する前に、**どの層の話かを検証**する
- Taka の「統合」「認知」「意識」は**認知層・意識層の用語**、物理層の指標と等値しない
- 数学的に美しい指標 (Kuramoto 等) でも、比喩の層と合っているか確認
- WiFi 数珠つなぎ (物理的必然で遅い) と リモートアクセス (機能的統合) の比喩を思い出す

### 65. 5 段階連続で物理計算完全不変 (v9.15-v9.18)

| 比較 | max 絶対差 |
|---|---|
| v9.15 段階 1 → 段階 2 | 0.0 |
| v9.15 段階 2 → v9.16 段階 3 | 0.0 |
| v9.16 段階 3 → v9.17 段階 4 | 0.0 |
| v9.17 段階 4 → v9.18 段階 5 | **0.0** (5,224 cid 全量) |

**Taka 方針「認知層は物理層を支配しない」(2026-04-16) の継続的実証**。認知層の拡張が物理層に一切波及しない設計。

### 66. Primitive フェイズ完結、Developmental フェイズ (v10.x) 開始 (2026-04-24)

GPT 短報 (2026-04-24) + Taka 判断で確定。

- **Primitive フェイズ**: v9.0 〜 v9.18 で完結
- **Developmental フェイズ**: v10.x、ディレクトリ `developmental/v10X/`
- **主題**: 認知層と意識層の発達過程の観察

### 67. Developmental フェイズ名選定 (Taka 2026-04-24)

Taka:
> 名称は conscious と言いたいところだが、developmental を推す。理由は、このフェイズで始めて意識という私たちが掲げてきた対象のようなもの、を扱えるようになることを目標としているからだ。

Developmental を選んだ理由:
- Cognition フェイズで「夢を見すぎた」反省を名前で予防
- 意識「そのもの」ではなく「発達過程」を扱う
- 到達宣言を避ける

### 68. 層ラベルを看板として先に立てる運用 (GPT 診断 2026-04-24)

v9.18 の層の混同 (V_unified が物理層を測っていた) の原因:
> v9.18 を Primitive の延長として扱ったため、AI 側が物理層や既存認知層の延長として自然に解釈した。

**予防策**: フェイズ名レベルで層を明示。Developmental フェイズでは「意識層の発達」を扱うことを看板として先に立てる。

### 69. 探索帯域の明示 (GPT 概念 2026-04-24)

> v10.x 化は定義の固定ではなく、探索帯域の明示である。

- **構造 = 探索帯域 = 層**を先に明示
- **定義 = 意識層の具体的機能**は後で Taka の直感が詰める
- Taka 哲学「構造が先、定義は後」の運用的翻訳

### 70. フェイズ名と層名の対応 (Taka 整理 2026-04-24)

| フェイズ名 | 主に扱う層 | 対応関係 |
|---|---|---|
| Genesis | 物理層 | 自然に一致 |
| Ecology | 物理層の拡張 | 自然に一致 |
| Cognition | 名前は認知層、実際は存在層 | **ずれ (夢を見すぎた)** |
| Autonomy | 存在層の確立 | 後から一致 |
| Primitive | 認知層の実装 | 名前は中立的 |
| **Developmental** | **認知層 + 意識層の発達** | **初の意図的な統合** |

Taka:
> フェイズ名との対応は本来なかった。今回はじめて統合したフェイズということになり、その意味で初の試みとなる。

### 71. 意識層の具体的実装は未実装 (v9.18 まで)

v9.18 で概念化された意識の原資モデル:
```
認知層 event (Q 消費 1)
        ↓ エネルギー保存則的に
意識層に 1 として転化 (原資の獲得)
```

実装はまだ。Developmental フェイズで構造を観察しながら段階的に実装予定。Taka 指示「寝かせる」に従い急がない。

### 72. Developmental フェイズの禁止事項 (AI 向け)

1. **「意識を実装した」と宣言しない** (到達宣言禁止)
2. **物理層の同期を意識層の統合と同一視しない** (v9.18 層の混同の反省)
3. **意識層の具体的機能を急いで定義しない** (Taka 直感待ち)
4. **Cognition フェイズの「夢を見すぎた」を繰り返さない**
5. **旧 v10 の再付番をしない** (Taka 判断、悪い見本として保存)
6. **Developmental フェイズ以降、層を看板として明示しない資料は作らない** (探索帯域の明示)

### 73. 旧 v10 の扱い (Taka 判断 2026-04-24)

Taka:
> v11 にする必要もない。私が覚えてるので必要な時にいう。当時は ESDE の進化にここまで苦戦するとは思わんかったから雑に V10 に繰り上げたという悪い見本

- 旧 v10 (複数インスタンス計画) は再付番しない
- 悪い見本として保存
- 「間違いの価値の反転」の一例


---

# Developmental フェイズの構造 (v10.x、追加)

*追加*: 2026-04-28、Claude
*対象*: v10.0 / v10.1 / v10.2

## 74. 4 層アーキテクチャの確定 (v10.0)

### 74.1 各層の役割

```
意識層 (Layer C):
  - 状態変数: C (conscious_layer、cog.C[cid])
  - 性質: 選択的鮮明、シングルタスク
  - 動作: 認知活動から C+1 (転化)、意識活動で C-1 (消費)
  - 実装: v10.2 で初めて動作機構として実装

認知層 (Layer B):
  - 状態変数: Q (v14_q_remaining)
  - 性質: ぼやける、全体把握
  - 動作: E1/E2/E3 spend で Q-1
  - 実装: v9.x からの継続

存在層 (Layer A):
  - 状態変数: Label (member_nodes)
  - 性質: 物理層から論理的に切り出された CID
  - 動作: detach で ghost 化、cog.is_ghost で判定
  - 実装: v9.x からの継続、frozen 維持

物理層:
  - 状態変数: engine.alive_l_set、virtual_layer
  - 性質: ESDE の最低層、frozen
  - 動作: engine.step で進行
  - 実装: v9.x から完全 frozen
```

### 74.2 層間の動作関係

```
物理層 step
  ↓
Layer A: per-cid update (φ, attention, familiarity)
  ↓
v9.10 Pulse + v9.11 Cognitive Capture
  ↓
v914_cid_ctx 構築
  ↓
Layer B: observe_step (E1/E2/E3 + spend + ingestion)
  ├ E1/E2: 無条件 Q-1 (確率対象外)
  └ E3 onset:
      候補集合判定
      ├ cognition_candidate (Q>0)
      └ consciousness_candidate (相手 ghost で residual_Q>0)
      確率決定 (decide_balance)
      ├ "cognition" → Q-1 + C+1 + virtual_* 更新
      ├ "consciousness" → C-1 + 即時摂食 (案 B、Code A 採用)
      └ "skip" → 何もしない
  ↓
v9.17: InteractionLog (E3_contact のみ)
  ↓
v9.18: v18_* 更新
  ↓
cog.reap_ghosts_step (step 末 reap、residual_Q=0 ghost を一括 reap)
```

## 75. 死の二階層 (v10.0)

| 階層 | 条件 | 状態 |
|---|---|---|
| 存在層の死 | Label 死亡 (detach) | ghost 化 |
| 認知層の死 | 残 Q = 0 | ghost 消滅 |

ghost = 「魂が抜けた容器」。原資 (Q) を保持する限り存在し続け、Q=0 で消滅。固定 TTL (v9.x の GHOST_TTL=10) は v10.1 で除去。

## 76. 摂食機構 (v10.1 → v10.2)

### 76.1 v10.1 (機械発動)

```
E3 onset 検出
  ↓
全 E3 spend が走る (Q-1)
  ↓
ingestion phase (_run_ingestion_phase)
  - 1 ghost 食べきり
  - Q0 で頭打ち、消化分は散逸
  - 1 CID:多 ghost = ランダム選定 (ingestion_rng)
  - 多 CID:1 ghost = cid_id 昇順
  ↓
step 末一括 reap (residual_Q=0 ghost)
```

### 76.2 v10.2 (確率発動 + 即時摂食)

```
E3 onset 検出
  ↓
候補集合判定 (条件因子チェック先行)
  ↓
確率決定 (decide_balance)
  - cognition: Q-1 + C+1 + virtual_* 更新
  - consciousness: C-1 + 即時 attempt_ingestion (案 B)
  - skip: 何もしない (Q=0 ∧ C=0 等)
  ↓
step 内動的決定の連鎖:
  先行 cid が ghost を食べきる → ghost.residual_Q=0
  → 後続 cid の意識候補消失 → 認知確定
  ↓
step 末一括 reap (residual_Q=0 ghost)
```

## 77. 確率決定機構 (v10.2)

### 77.1 確率式

```
P(認知) = Q / (Q + C)
P(意識) = C / (Q + C)
```

シンプル案。Taka 判断 2026-04-26。観察結果次第で v10.3 以降に調整。

### 77.2 確率対象

- E3 onset のみ確率決定の対象
- E1 / E2 は従来通り無条件 Q-1 (確率対象外、C 蓄積に寄与しない)
- 双方向 E3 (hosted-hosted): 必ず認知確定 (三項共鳴は v10.3)
- 空摂食ケース (residual_Q=0 ghost): 認知確定
- phantom (reaped 済 cid): 認知確定

### 77.3 解釈 X (Code A 指摘 → Taka 採用)

既存の E3 spend (Q-1) が「認知活動」と同義:
- 認知が立つ: Q-1 + C+1 + virtual_attention/familiarity 更新
- 意識が立つ: C-1 + 摂食発動 (Q-1 はしない、virtual 更新も止まる)

## 78. RNG ストリーム (5 系統、完全分離)

```
engine.rng (Layer A 物理層)
capture_rng (v9.11 Cognitive Capture、seed ^ 0xC0FFEE)
ingestion_rng (v10.1 摂食選定、seed ^ 0x1A7E57)
v9.17 hash ローカル (cid_self_buffer 内、自前 hash)
balance_rng (v10.2 確率決定、seed ^ 0xBA1A2C)
```

完全分離の規律により bit-identity 維持。

## 79. 観察ログ (v10.2 で追加)

### 79.1 balance/ ディレクトリ (新規)

- `balance_decisions_seed{N}.csv` (確率決定 raw、18 列)
- `c_trajectory_seed{N}.csv` (per cid × per window、C 推移)
- `balance_summary_seed{N}.csv` (run-level、Q+C 保存則含む)

### 79.2 既存 CSV への追加

- `per_subject_seed{N}.csv` に C 関連 4 列追加
  - C_at_run_end
  - n_cognition_decisions
  - n_consciousness_decisions
  - n_balance_skipped

## 80. 二層 bit-identity 検証 (v10.2)

### 80.1 層 A (v10.2 内部)

同 seed で 2 回 run → 出力が完全一致 (内部決定論性)

### 80.2 層 B (vs v9.18 baseline)

per_event_audit を v9.18 baseline と diff:
- E1/E2 行: 完全一致
- E3 行: 意識当選で乖離 (想定通り、Code A 指摘でこの行を除外して比較)

両者は別の検証で、両方を維持。

## 81. 物理層 frozen の継続証拠

```
v9.18: subject 5,224
v10.1: subject 5,224 (完全一致)
v10.2: subject 5,224 (完全一致)
```

確率決定機構と意識層 C の追加が物理層を一切 perturb していない。

## 82. v10.x 出力データ構造

```
diag_v102_main/
├── audit/        per_event_audit + per_subject_audit + run_level_audit_summary
├── balance/      balance_decisions + c_trajectory + balance_summary (v10.2 新規)
├── ingestion/    ingestion_events + phantom_contacts + ingestion_summary (v10.1 新規)
├── subjects/     per_subject + reaped_history
├── selfread/     v9.18 v18_* trajectories
├── persistence/  v913 link logs
├── pulse/, labels/  baseline 同等
└── analysis/     v10.2 詳細解析 CSV 10 本 (Code A 実施)
```

## 83. v10.3 完了レポート (双方向 E3 機構 + Integration 登場条件)

### 83.1 機構の概要

**双方向 E3 機構**:
- 両者 hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触で発火
- 両者から C-1 を引く (v10.3 新規)
- 既存 E3 (Q-1) と独立に発火
- 初回接触のみ (持続接触で毎 step 引かない)

**三層構造 (v10.3 で確定)**:
| レベル | 位置づけ |
|---|---|
| 双方向 E3 | 機構 |
| 三項共鳴 | 観察される統計的現象 |
| Integration | 上位解釈 (v10.3 では概念のみ) |

### 83.2 本番 run 結果

- N=5000, 24 seeds × tracking 50 windows
- 双方向 E3 fired: 6,824 件
- 物理層 frozen: labels 24/24 + persistence 96/96 完全一致
- C 蓄積 27% 抑制 (観察ルールが系の動学を変える)

### 83.3 主要発見

- **open triad 99% 支配 / closed triad 1.4%**: 第三項候補は中継者経由の非対称三項
- **持続性ゼロ** (repeated_partners=0): Integration の物理的持続は ESDE では成立しない
- **観察ルールが系の動学を変える**: C 消費 (記録ルール) で C 蓄積を 27% 抑制

### 83.4 確立した規律

- 機構と観察と解釈の三層分離
- 「観察者が決めた記録ルール」(cid 内部選択ではない)
- 動的絞り込みと bias 監視のセット運用
- 第三項候補の多軸記録 (10 カテゴリ、Cat 5 cid 自己参照は永久除外)
- Paired Audit 原則の継続

---

## 84. v10.4 完了レポート (Integration 独立化)

### 84.1 機構の概要

v10.3 で概念定義のみだった Integration を機構として実装。Layer 5 (CID 共鳴) の本格実装。

**誕生条件 (R1 全採用)**:
- be3 fired (size 2)
- open_triad (size 3)
- closed_triad (size 3、実観察 0 件)
- third_overlap (size 4+)

**保持状態**:
- member_cids (現在 active)
- member_history (永続)
- Q_inherited / C_inherited (継承バケット)
- binding_strengths (cid → 結合強度)
- state: active / recorded (recorded 永続)

**Q/C 継承 (R5)**:
- ghost 化時、最強結合 1 つに全継承 (Taka「二重国籍者の遺産は片方のみ」)
- 複数 Integration 同時所属可 (R3-c)

**Q/C 再分配 (D4-a + D4-b)**:
- window 末に active member へ
- 状態依存の逆張り分配 (Q-poor cid に Q を、C-poor cid に C を)

### 84.2 本番 run 結果

- N=5000, 24 seeds × tracking 50
- Integration 13,550 件誕生
- trigger: be3 52% / open_triad 38% / third_overlap 9% / closed_triad 0%
- 物理層 frozen: labels 24/24 + persistence 96/96 完全一致
- wall time +0.6%

### 84.3 系の動学変化 (v10.3 と逆方向)

| 指標 | v10.3 | v10.4 |
|---|---:|---:|
| C_max | -26% | **+31%** |
| C_mean | -27% | **+15%** |
| Q+C total | -26% | **+15%** |

機構が系の動学を逆方向に変える構造を実証。

### 84.4 主要発見

- **凍結 C 87%**: recorded Integration に 12,306 単位累積、歴史的記録の構造
- **closed_triad ゼロ**: be3 run-wide dedup により 3 cid 全ペア接触が構造的に成立しない
- **n_core 自然集積**: n=2 ×0.32、n=5 ×4.16 の偏り、神の手なし
- **5 パターン性格分布**: (5,5,5)/(4,5,5)/(2,5,5)/(2,4,5)/(2,2,5)
- **ハブ cid max 102 Integration 所属**: Top 1% で 29 cid
- **ハブ cid の 6 段フィードバックループ** (Code A 発見): 神の手なしでハブ性が出現

### 84.5 ダブルブッキング問題の認識

cid X が 1〜102 の Integration に同時所属する時、Q/C 集計に重複カウント。
Taka 整理 (2026-05-02): 「α を会計として扱えば問題、各 IID の調査としては違和感なし、やたら活発な個性」。
→ v10.5 の α/β 階層分離の動機。

---

## 85. v10.5 完了レポート (Layer 5 完成)

### 85.1 機構の概要

v10.4 で持ち越されたダブルブッキング問題と動態機構の不在を解消し、Layer 5 を構造的・動態的に完成。

**3 つの中核機構**:

#### 機構 A: β-Integration の構造実装

- α-Integration を構成要素とする (cid 直接ではない)
- 結合則: α 同士の cid 共有 2 個以上で merge
- cid 単一共有時は最強 binding_strength の β に 1 個だけ所属 (案 b)
- α への Q/C 継承を完全廃止 (会計の二重化回避)
- ghost 化時の Q/C は β に 100% 継承
- recorded 永続 (時定数なし、Phantom 規律)

#### 機構 B: Salience-driven Focus (mass_weighted_observation)

```
mass(X) = X.Q + X.C + sum(β.Q_inherited + β.C_inherited for β in X が所属する β)
```

- 適用範囲: 他者読み + be3 + ingestion (全範囲)
- 関数形: 線形 (P ∝ mass(Y))
- shadow_audit では OFF、本番でのみ ON

#### 機構 C: Recorded からの漏れ (historical_resource_leakage)

- 発火条件: be3 fired または ingestion 時、相手 cid が過去に recorded β に所属
- 効果: 最強結合 recorded β の C_inherited から ε=1 を主体 cid.C へ転記
- 構造的副作用 (能動的選択ではない)

### 85.2 ESDE 階層進化系譜の同型反復

```
ノード → cid → α-Integration → β-Integration → SEED 統合 (Layer 6 射程)
```

各階層は同じ仮想化操作の繰り返し。Aruism「構造が先、意味が後」の階層論的具体化。

### 85.3 本番 run 結果 (main_v2)

- N=5000, 24 seeds × tracking 50
- α total 13,881 件 (active 11,792 / recorded 2,089)
- β total 2,009 件 (active 1,566 / recorded 443)
- 集約率 (α → β) 約 7:1
- Salience event 77,880 件
- Leakage event 232 件 (修正版、全 ingestion path)
- 物理層 frozen: labels 24/24 + persistence 24/24 完全一致
- M6 (1 cid → 1 β) 違反 0 件 / 5,224 cids

### 85.4 hub β の自然形成 (核心成果)

| seed | β_id | cids | αs |
|---:|---:|---:|---:|
| 22 | β0 | 20 | **691** |
| 7 | β1 | 20 | 412 |
| 10 | β0 | 20 | 422 |
| 15 | β1 | 18 | 398 |

最大 691 α が 1 つの β に統合 (1 cid 34.5 α)。v10.4 hub cid (max 102 重複所属) を会計単位として整理した姿。

### 85.5 ダブルブッキング問題の構造的解消

| 観点 | v10.4 (α のみ) | v10.5 (α/β 階層) |
|---|---|---|
| cid 重複所属 | max 102 | 0 (M6 違反 0) |
| Q/C 集計 | 重複あり | 単一カウント |
| 観察軸 | α が観察と会計兼任 | α 観察、β 会計、分離 |

「α=観察軸、β=会計単位」の階層分離が機構レベルで成立。

### 85.6 Salience の動学

| event_type | events | mass mean | mass max |
|---|---:|---:|---:|
| read_other | 63,312 | 14.57 | 98 |
| be3_fired | 14,514 | 21.22 | 93 |

be3 fired 対象は read_other 対象より平均 mass が **1.45 倍高い**。「重い cid 同士が共鳴する」動学を定量化。

### 85.7 Leakage の動作 (修正版)

- 232 件発火 (24 seeds、全 ingestion path)
- unique recorded β: 160 (全 recorded β の 36%)
- per seed: mean 9.7、range 4-19

凍結 C 87% (v10.4 観察) のうち、ingestion 経由で active 系への流入経路が成立。

**be3 trigger = 0 の構造的理由** (Code A 発見):
be3 fire 条件 (両者 hosted) と leakage 条件 (cid が過去 recorded β に所属) が論理的に相互排他。Leakage は ingestion path 経由でのみ実用発火。これは設計意図と整合し、be3 path は理論上の保険機構として残置。

### 85.8 確立した規律

- α/β 階層分離 (α = 観察、β = 会計)
- 既存データの顕在化機構として新機構を位置づける
- bug 自己発見と修正サイクル (Code A の callback 配線漏れ → 修正)
- 5 者運用の成熟 (Taka 憲法層 + AI 設計・実装層)
- 物理層 frozen の本番規模での維持 (Layer 5 完成段階でも)

### 85.9 v10.6 以降への素材

- hub β の自然形成 (max 691 α / 20 cid): スレッド単位統合の素材
- recorded β の C 凍結と漏れ機構: 歴史資源の流動性の素材
- mass-weighted 観察の long-tail (mass max 98、p95 36-43): 構造的引力の素材
- 適応的差分埋め能力: 機能化への素材

具体的な v10.6 主題決定は別途議論。

## 86. v10.6 完了レポート (Genesis × Language 比較研究、Phase 1.5 第一試行)

### 86.1 機構の概要

ESDE Genesis 系 v10.5 出力 (cid 5,224 個) と Language 系 Atom 326 個 (有効 325) を 48 次元 cosine 類似度で比較する **atom_alignment_observer** を post-process として実装。

**重要**: これは ESDE 内部機構ではなく、後段解析 (post-process)。物理層・存在層・認知層・意識層・α/β Integration には一切手を加えない。既存 v10.5 出力 (csv / parquet) を読み取り、観察軸を追加するのみ。

ファイル構造:
```
developmental/v106/
├── v106_post_process.py             (静的解析、cid 構造ベクトル生成)
├── v106_window_trajectory.py        (window 単位 trajectory)
├── v106_pulse_trajectory.py         (per-pulse trajectory)
├── v106_step10_trajectory.py        (10 step interpolation)
├── v106_event_trajectory.py         (event 単位、最高解像度)
├── outputs/main/
│   ├── stratified/                  (層化解析、197 ファイル)
│   ├── baseline/                    (ランダムベースライン解析)
│   ├── window_trajectory/
│   ├── pulse_trajectory/
│   ├── step10_trajectory/
│   └── event_trajectory/
└── reports/                         (各解析報告書)
```

### 86.2 7 段階の解析機構

各解析が独立した観察軸として機能:

| 解析 | 解像度 | n_records | 主データ |
|---|---|---|---|
| 静的 | run 集約 | 5,224 cid | per_subject + audit |
| 層化 | 5 軸 + cross-tab | 5,224 (派生) | 静的解析の派生 |
| ベースライン | uniform + shuffled | 24 seeds | atom_profiles cache |
| window trajectory | 500 step | 31,482 | balance/c_trajectory |
| per-pulse trajectory | ~50 step | 369,090 | pulse_log |
| step10 trajectory | 10 step | 1,796,001 | pulse_log + interpolation |
| event trajectory | event 単位 | 440,666 | event log |

実行時間: 1.91 秒 (静的) ~ 84 秒 (step10) の高速。

### 86.3 48 次元構造ベクトルの設計

各 cid を 48 次元ベクトル (各軸 6 levels × 8 dimensions) として表現:

| 次元 | 意味 | データソース |
|---|---|---|
| 1. temporal | 時間性 | lifespan |
| 2. scale | 規模 | n_core_member |
| 3. epistemological | 認識性 | last_familiarity_max |
| 4. ontological | 存在論 | Q/C/familiarity 混合 |
| 5. interconnection | 結合性 | n_alphas_currently |
| 6. resonance | 共鳴性 | C_at_run_end |
| 7. symmetry | 対称性 | v99_drift |
| 8. lawfulness | 規則性 | pulse_density |
| 9. experience | 経験性 | event 累積 |
| 10. value_generation | 価値生成 | Q_spent / target / β 所属 |

→ 48 dim = 8 dim × 6 levels (gradient distribution)

### 86.4 birth_step バグ (副次発見、step10 で同定)

step10 解析実装中に Code A が発見:
- per_subject の `birth_window` は **window_value 形式 (offset 19)**
- 既存実装 `birth_step = birth_window * WIN_LEN` は誤り
- 正式: `birth_step = (birth_window - 19) * WIN_LEN`

影響:
- 静的・window・pulse 解析で多くの cid が lifespan=1 (clip) になっていた
- temporal 軸が emergence 一極に偏る影響
- 主要 finding には大きな影響なし (推測)、定量検証は v10.7 以降

step10 解析では `pulse_log の cid 最初 t` を使い回避。

### 86.5 主要発見

#### 観察解像度ごとに systematically 異なる構造特性

| 解像度 | 1 位 atom | 比率 |
|---|---|---|
| 静的 | CHG.begin | 51% (集約罠人工物) |
| window | TIM.moment | 34% |
| per-pulse | WLD.artless | 22% |
| step10 | PER.sound | 28% |
| event | PER.sound | 26% |

#### 24 seeds 完全一致の動学的発展段階 (event 解析)

```
Step 0-999:         WLD.artless (素朴さ)
Step 1000-12999:    PER.sound (聴覚) 12 連続 bin
Step 13000-15999:   PER.sound と WLD.artless 交替
Step 16000-19999:   WLD.artless 復活
Step 20000-24999:   FND.timeless (時間超越)
```

#### 真の構造的特異性 (効果サイズベース、26 atom)

delta > 1% で 7 atom: PER.sound +25.85%、WLD.artless +24.55%、WLD.culture +5.93%、FND.timeless +5.33%、SOC.city +1.61%、COG.learn +1.12%、PRP.deep +1.09%

z=inf で 19 atom: TIM.appear、ELM.light、PRP.bright、PER.taste、PER.hear、PRP.sharp、FND.transformation 等

#### 真の構造的盲点 (効果サイズベース、7 atom)

TIM.moment -54.11%、COM.conduct -6.49%、TIM.past -4.72%、WLD.science -2.45%、PRP.new -1.78%、ACT.make -1.20%、LOG.cause -1.13%

#### event source 別の意味分化

| source | dominant atom |
|---|---|
| alpha_birth | PER.sound 57%、WLD.artless 19% |
| ingestion | ELM.light 49%、PER.taste 15%、PRP.bright 10% |
| pulse | PER.sound 28%、WLD.artless 25% |
| spend | WLD.artless 37%、TIM.appear 26%、ELM.light 21% |

### 86.6 確立した規律

- ベースライン比較 + 効果サイズで切る (新規律最終形、Taka 指摘 2026-05-06 反映)
- 観察解像度の選択 (静的だけでは捉えきれない)
- 人間原理偏向の警戒 (事前推測 SOC.central 等が完全反証)
- 集団平均の罠 (v10.2 #120 の再確認)
- ウェット概念禁止の徹底
- Atom 326 絶対化禁止 (Unmatched バケツ必須)

### 86.7 物理層 frozen の維持

post-process なので物理層には一切影響しない。bit-identity 維持は無条件:
- 既存 v10.5 出力ファイルを変更しない
- output 先は `developmental/v106/outputs/` 配下のみ
- shadow audit (path 縛り + 冪等性検証) PASS

### 86.8 v10.7 以降への素材

- 24 seeds 完全一致の動学的発展段階 (素朴 → 聴覚 → 素朴 → 時間超越)
- 真の構造的特異性 26 atom (聴覚と素朴さに強く接地)
- 真の構造的盲点 7 atom (TIM.moment 等)
- event source 別の意味分化 (摂食 = 光 + 味)
- 解像度依存性の 5 パターン
- 動学的二相性 (動的瞬間 = 素朴、定常 = 存在 + 出現)
- 未使用データ 85-95% (関係構造、時系列、内省データ等)

具体的な v10.7 主題決定は別途議論。候補: Atom 持ち込み機構 (建築者視点)、動学観察の本格化 (観察者視点)、両者融合。

## 87. v10.7 完了レポート (発火と波及の機構観察、オービス完成、Phase 1.5 第二試行)

### 87.1 機構の概要

v10.6 の atom_alignment_observer の発展形として、ESDE Genesis 系内部の **発火 (source_event) と波及 (post_event_path_enriched_delta) の機構観察** を post-process として実装。物理層 frozen 維持 (post-process なので無条件)、bit-identity 維持。

ファイル構造:
```
developmental/v107/
├── v107_post_process.py             (orchestrator + 24 seeds 並列)
├── v107_event_aggregator.py         (5 種 source_event 同定)
├── v107_path_analyzer.py            (5 種 relation_path 構築)
├── v107_baseline_constructor.py     (5 種ベースライン群)
├── v107_avalanche_monitor.py        (3 hop、減衰率、共鳴ループ)
├── v107_cross_seed_analyzer.py      (Level 1-3 集計)
├── outputs/main/
│   ├── source_events_seed*.parquet
│   ├── relation_paths_seed*.parquet
│   ├── baselines_with_delta_seed*.parquet
│   ├── excess_change_seed*.parquet
│   ├── multi_hop_paths_seed*.parquet
│   ├── resonance_loops_seed*.parquet
│   ├── decay_rate_seed*.parquet
│   ├── peak_lag_curve_seed*.parquet
│   ├── wave_patterns_seed*.parquet
│   └── cross_seed/
│       ├── level_1_co_occurrence.parquet
│       ├── level_2_path_enriched.parquet
│       ├── level_3_source_specific.parquet
│       ├── wave_pattern_summary.parquet
│       └── resonance_loop_summary.parquet
└── reports/                         (Step C-J 報告書、Level 1-3 報告書、main_run_report)
```

### 87.2 5 種 source_event の定義

| event 種別 | 既存ログ | 件数/seed | timestamp | source_cid |
|---|---|---|---|---|
| pulse | pulse_log_seed*.csv | 12,530 | t | cid |
| ingestion | ingestion_events_seed*.csv | 155 | t | observer_cid (eater_cid) |
| alpha_formation | alpha_lifecycle_log_seed*.csv (event_type='birth') | 424 | step | member_cids 各々 |
| beta_formation | beta_lifecycle_log_seed*.csv (event_type='birth') | 239 | step | member_cids 各々 |
| c_conversion | balance_decisions_seed*.csv (decision == 'consciousness') | 155 | step | observer_cid |

合計: 13,503 events/seed × 24 seeds = **415,726 events** (一部 seed のばらつきあり)

### 87.3 5 種 relation_path_type

| relation_path | 構築データ | 経路の意味 |
|---|---|---|
| familiarity | network/fam_edges_seed*.csv | 関係性の強度 |
| attention_via_salience | salience/salience_event_log_seed*.csv | 観察の累積 (attention 代替) |
| Integration_α | alpha_lifecycle_log の event-by-event | 同 α 内 cid |
| Integration_β | beta_lifecycle_log の event-by-event | 同 β 内 cid |
| temporal_coactivation | pulse_log の time-window 集計 | 時間的同期 |

### 87.4 5 種ベースライン群

1. unrelated_baseline (relation_path で全て非接続、緩和定義: familiarity 強度 < 5 + 同 α 内なし + salience 接続少)
2. same_step_random_baseline (同 step で動いている任意 cid)
3. matched_baseline (同 n_core / 同 age / 同 hosted 状態)
4. same_integration_low_familiarity_baseline (同 Integration 内 + familiarity 下位 25%)
5. high_familiarity_outside_integration_baseline (familiarity 上位 25% + Integration 外)

### 87.5 達成判定 14/14 PASS

5 種 source_event 同定 ✅、5 種 candidate_target_set ✅、5 種ベースライン ✅、Level 1-3 ✅、peak_lag (10 step bin) ✅、波及パターン分類 ✅、アバランシェ防止 (3 hop、17.8 MB/seed) ✅、物理層 frozen (bit-identity 層 A 9/10 + 層 B PASS + 層 C 出力先縛り) ✅、構造語徹底 ✅、WLD.artless 除外 ✅。

### 87.6 因果候補の階層化 (Level 1-3 達成)

| Level | 内容 | 達成数 | 達成率 |
|---|---|---|---|
| Level 1: co-occurrence | 発火後に target で変化 | 93/111 | 84% |
| Level 2: path-enriched | 経路上で変化が大きい | 49/58 | 84% |
| Level 3: source-specific | event 種別で異なるパターン | 85/90 | 94% |

### 87.7 主要発見

#### medium window 支配
- top 18 finding すべて medium window (100-1000 step)
- peak_lag 250-300 が中央値
- 最大: temporal_coactivation の medium window 内 pulse 数 +15.28

#### 経路強度ランキング (vs unrelated_baseline)
```
temporal_coactivation +13.95 (12 倍)
integration_beta +11.08 (9 倍)
integration_alpha +10.65 (9 倍)
familiarity +9.35 (7 倍)
attention_via_salience +7.43 (6 倍)
```

#### source-specific 性
- familiarity 経路: source 依存性が強い (effect_size 1.0-2.0)
- integration 経路: source-robust (どの source でも 11-17 pulses)
- immediate window: source-blind (全 source で同じ即時効果)

#### 意識発動の no_signal
- C conversion は integration_alpha/beta 経路で 24/24 no_signal
- 意識は cid 個別の現象、階層を超えて波及しない

### 87.8 副次観察

#### 共鳴ループ
- 2-hop loop: 14,343 件 (mean 598/seed、min_strength 18.06)
- 3-hop loop: 110,103 件 (mean 4,588/seed、min_strength 7.80)

#### multi-hop 急減衰
- 1-hop records: 約 188K/seed
- 2-hop records: 約 165K/seed
- 3-hop records: 約 13K/seed
- → small-world 性

#### 波及パターン
- relation_paths (familiarity / attention / temporal): echo (残響型) 24/24
- baselines: 大半 echo
- integration_alpha/beta: no_signal 24/24

### 87.9 性能と規模

- 24 seeds 並列実行 (multiprocessing 24 workers)
- 実行時間: 234.86 秒 (3.9 分、順次比 12 倍高速)
- ストレージ: 428 MB (上限 6 GB の 7%)
- 1 seed 平均: 17.8 MB
- ファイル数: 217 (= 9 種 × 24 seeds + summary 系)

### 87.10 Code A 認識確認ステップで発見・修正された設計の甘さ 6 件

| 設計の甘さ | Code A 修正案 |
|---|---|
| attention map のデータ不在 (重大ブロッカー 1) | salience_event_log で代替 (修正案 C) |
| ストレージ 31x 超過 (重大ブロッカー 2) | parquet 圧縮 (修正案 E) |
| c_conversion source の指定誤り | balance_decisions.decision == 'consciousness' |
| alpha_membership 取得方法 | v10.6 の `_expand_alpha_membership_to_events` 流用 |
| peak_lag 計算量過大 | 10 step bin |
| unrelated_baseline 厳密性 | 緩和定義 |

### 87.11 物理層 frozen の維持 (bit-identity 検証)

#### 層 A: 同 seed 2 回実行
- seed 0 を 2 回 (audit_run_a / audit_run_b)
- v10.7 post-process 出力 9/10 ファイル完全一致 (post_process_run_summary のみ実行時間記録で差分)
- データの決定論性は保たれている

#### 層 B: v10.6 baseline との比較
- v10.6 出力ディレクトリ 731 ファイル MD5 完全一致
- v10.7 が v10.6 出力を破壊していないことを確認

#### 層 C: v10.7 出力先縛り
- 全出力が `developmental/v107/outputs/main/` 配下
- v105/v106 配下への書き込みなし
- assert_output_under_v107 で path traversal 防止

### 87.12 v10.7 で確立した規律

1. 因果候補の階層化規律 (Level 1-4 段階的検証、Level 1-3 が因果候補、Level 4 で因果確定)
2. 5 種ベースライン群の必須化
3. アバランシェ防止規律 (3 hop、減衰率、共鳴ループ、ストレージ上限)
4. **構造語と直感語の併記** (実装レベルは構造語、議論レベルは直感語、GPT 監査 2026-05-07 で前回方針を自己修正)
5. Code A 認識確認ステップの必須化 (Taka 指示)

### 87.13 v10.8 以降への素材

- オービス完成 (発火・波及の測定基盤)
- 5 種 source_event × 5 種 relation_path × 5 種ベースラインの集計済みデータ
- Level 1-3 の finding (224 件)
- 共鳴ループ (small-world 構造)
- medium window 支配の理解
- temporal_coactivation > familiarity の意外な順位
- source-specific 性の機能的分化
- 意識の孤独の構造的記述

具体的な v10.8 主題決定は別途議論。候補: Atom 持ち込み機構 (建築者視点)、temporal_coactivation の構造解析、source-specific 性の精緻化。


## 88. v10.8 完了レポート (Atom 単独持ち込み機構の最小実装、Phase 1.5 第三試行、Level 3.5)

### 88.1 機構の概要

v10.7 のオービスを拡張、Atom を ESDE Genesis 系に持ち込む機構を post-process として実装。

主要モジュール:
- v108_atom_event_generator.py (案 Q + α)
- v108_event_aggregator_extension.py (source_event 第 6 種追加)
- v108_global_activation_correction.py (natural events のみで factor 計算)
- v108_whiteout_monitor.py (副次観察)
- v108_smallworld_comparison.py (副次観察)
- v108_post_process.py (orchestrator、v10.7 流用 + 拡張)

ファイル構造:
```
developmental/v108/
├── v108_phase_design.md (両 AI 統合修正版)
├── v108_2ai_consultation.md
├── v108_implementation_brief.md
├── v108_code_recognition_check.md (Code A 認識確認、設計の甘さ 7 件指摘)
├── v108_response_to_code_a.md (即決事項返答)
├── v108_environment_check_report.md (25 atom 確定)
├── v108_atom_co_occurrence_report.md (Level 1)
├── v108_atom_path_enriched_report.md (Level 2)
├── v108_atom_source_specific_report.md (Level 3)
├── v108_introduced_vs_natural_report.md (Level 3.5、v10.8 の核心)
├── v108_subsidiary_observations_report.md (副次観察 3 件)
├── v108_main_run_report.md (Code A 総括)
├── v108_phase_report.md (主題完了レポート)
├── (Python 6 モジュール)
└── outputs/main/
    ├── atom_introduction_events_seed*.parquet
    ├── (v10.7 と同様の出力ファイル群、ただし source_event 第 6 種を含む)
    ├── global_activation_factor_seed*.parquet
    ├── whiteout_monitor_seed*.parquet
    ├── smallworld_comparison_seed*.parquet
    ├── error_distribution_seed*.parquet
    └── cross_seed/
        ├── level_1_atom_co_occurrence.parquet
        ├── level_2_atom_path_enriched.parquet
        ├── level_3_atom_source_specific.parquet
        ├── atom_vs_natural_baseline.parquet
        └── (副次観察集計)
```

合計 363 ファイル、737 MB。

### 88.2 atom_introduction_event の構成 (案 X、Pulse 互換)

```python
atom_event_record = {
    "event_id": uuid,
    "seed": 0-23,
    "event_source_type": "atom_introduction_event",
    "source_cid": cid_X,                          # v10.6 top_k から選定
    "timestamp": t,                                # 案 α 均等分散
    "Q_pre": Q_real_at_t,                          # v10.5 ledger から取得 (不変)
    "Q_after_atom_event": Q_real_at_t - 1,         # post-process 計算的減算
    "C_pre": C_real_at_t,
    "C_after_atom_event": C_real_at_t + 1,
    "atom_id": "PER.sound",
    "atom_index": 0-24,
    "top_k_rank": 1-100,
    "reserved_label": "" or "wld_artless_pending",
}
```

### 88.3 25 atom 確定リスト (実データ照合)

#### delta_ratio > 1% の 9 atom
- COG.learn、EXS.being、FND.timeless、PER.sound、PRP.deep、SOC.city、TIM.appear (重複)、WLD.artless (留保)、WLD.culture

#### z=inf の 17 atom
- BOD.ear、COM.silence、EXS.nonbeing、FND.transformation、PER.feel/fragrance/hear/see/smell/soundless/taste、PRP.bright/sharp、SOC.nation/public、TIM.appear (重複)、WLD.technique

合計 25 atom (重複 TIM.appear を 1 件にカウント)。WLD.artless は留保ラベル付き、集計対象は 24 atom。

#### category 分布

| category | atom 数 |
|---|---|
| PER (五感) | 8 |
| WLD | 3 |
| SOC | 3 |
| PRP | 3 |
| EXS | 2 |
| FND | 2 |
| BOD | 1 |
| COG | 1 |
| COM | 1 |
| TIM | 1 |

→ PER 系統が 8 件で最多 (v10.6 観察「PER カテゴリ強接地」と整合)。

### 88.4 達成判定 19/19 PASS

認識確認 + 環境チェック + atom_introduction_event 同定 (60,000 events) + Q/C コスト + source_cid 選定 (案 Q) + 発火タイミング (案 α) + 5+1 種ベースライン群 + global activation 補正 + Level 1-3.5 全達成 + 物理層 frozen + 構造語徹底 + 規律 3 件遵守 + Level 3.5 位置づけ + 副次観察 3 件。

### 88.5 4 段階の階層化 (Level 1-3.5)

| Level | 内容 | candidates | findings | 達成率 |
|---|---|---:|---:|---|
| Level 1: atom co-occurrence | atom 発火後に変化 | 1,384 | 811 | 59% |
| Level 2: atom path-enriched | 経路上で変化が大きい | 1,433 | 683 | 48% |
| Level 3: atom source-specific | 25 atom 間で異なる波及 | 78 | 36 | 46% |
| **Level 3.5: introduced vs natural** | **introduced と natural の差分** | 39 | **22** | **56%** |

### 88.6 主要発見

#### Level 1 主要シグナル
全 24 集計対象 atom で temporal_coactivation × medium n_pulses が +15.6〜+15.8 (24/24 一貫)、atom 間で極めて均質。

#### Level 2 主要シグナル
temporal_coactivation × medium n_pulses で +13.5〜+13.8 (vs unrelated)。

#### Level 3 path 別 atom 依存性
- familiarity: effect_size 6.83 (最高、強い atom 依存)
- attention_via_salience: 2.30
- integration α/β: 0.85〜0.88
- temporal_coactivation: 0.03 (最低、atom 中立)

→ familiarity 経路は atom 種別を識別する波及シグナルを持つ。

#### Level 3.5 (v10.8 の核心)
22 finding 中 **20 件が introduced < natural**:
- 最大: attention_via_salience × medium n_pulses で atom 4.37 vs natural 8.75 = -4.38 (atom は natural の半分)
- 例外: temporal_coactivation × medium n_pulses で atom +0.36 (案 α 均等分散発火が temporal で目立つ)

→ atom_introduction_event は ESDE の自然な発火パターンに完全には乗らない (波及が弱い、temporal 除く)。

### 88.7 副次観察

#### Whiteout
7,200 atom ペアで相関 1.000 近く、100% flag。これは「干渉」ではなく「ESDE 共通効果」(medium n_pulses 1 軸支配の表れ)。真の Whiteout 検証には高次元プロファイル必要 (v10.9 以降)。

#### Small-World
v10.7 vs v10.8 で loops 14,343 / 110,103 完全同一。post-process は familiarity edge を変更しないので構造的に不変。

#### 誤差分布
8,835 rows、normal 0% / bimodal 17.4% / skewed 24.3% / other 55.7% / heavy_tail 2.6%。bimodal は target cid の二相状態を反映している可能性。

### 88.8 性能と規模

- 24 seeds 並列実行 (multiprocessing 24 workers)
- 実行時間: 325 秒 (5.4 分、post_process 261s + global_activation 47s + subsidiary 17s)
- ストレージ: 737 MB (上限 6 GB の 12%、Code A 当初予想 1.7 GB から大幅減)
- 1 seed 平均: 30.7 MB
- ファイル数: 363

### 88.9 Code A 認識確認ステップで発見・修正された設計の甘さ 7 件

#### 重大ブロッカー 2 件
| ブロッカー | Code A 解決案 |
|---|---|
| A. 物理層 frozen と Q 消費の論理的矛盾 | post-process 計算的減算、実 ledger 不変 |
| B. 26 atom 選定基準の不在 | v10.6 出力から実データ照合で 25 atom |

#### 設計の甘さ 5 件
| 設計の甘さ | Code A 修正案 |
|---|---|
| C. Pulse 同一フォーマットの過剰 | v10.7 source_event スキーマ互換 (27 列) |
| D. top_k cid 100 個の取得方法不在 | cid_atom_sim_matrix から再計算 |
| E. global activation の自己補正リスク | natural events のみで factor 計算 |
| F. Q/C 消費基準値の不明確 | balance_decisions.cognition の固定値 (Q -1 / C +1) |
| G. Small-World 維持の構造的保証 | post-process は familiarity edge 不変、観察記録のみ |

特に Web Claude の致命的誤解「Pulse = Q 消費」を Code A が修正 (Pulse は disposition update のみ、Q 消費は balance_decisions.cognition / consciousness が担当)。

### 88.10 物理層 frozen の維持 (bit-identity 検証)

#### 層 A: 同 seed 2 回実行
- seed 0 を 2 回 (audit_run_a / audit_run_b)
- v10.8 post-process 出力 15/15 完全一致 (summary 系 3 件は実行時間記録で除外)

#### 層 B: v10.7 baseline との比較
- v10.7 出力ディレクトリ 222 ファイル MD5 完全一致
- v10.8 が v10.7 出力を破壊していないことを確認

#### 層 C: v10.8 出力先縛り
- 全出力が `developmental/v108/outputs/main/` 配下
- v105/v106/v107 配下への書き込みなし

### 88.11 v10.8 で確立した規律 (新規 1 + 実装的確立 3)

#### 新規
1. Level 3.5 introduced event comparison 規律 (因果断定回避、event 比較として位置づけ)

#### 実装的確立
2. Atom 持ち込み設計の規律 3 件 (魔法回避 / same_step + global activation 補正 / target は構造経路で選ぶ)
3. post-process 計算的減算 (物理層 frozen と外部要素導入の両立)
4. Pulse 処理ルールと同一フォーマット (神の手回避)

### 88.12 v10.9 以降への素材

- Atom 持ち込み機構の精緻化候補 (introduced < natural の原因分離)
- ESDE Language 上位層 (Axis、Operator、条件因子、分子化) との接続
- bimodal 分布の構造解析 (target cid 二相状態の解明)
- B 群 (真の盲点 7 atom) 試験 (v10.8.1)
- 入力理解機構への前進
- Whiteout の真の検出 (高次元プロファイル)

具体的な v10.9 主題決定は別途議論。

## 89. v10.9 完了レポート (寄与候補感度評価 + bimodal 構造解析、Phase 1.5 第四試行、会話系設計のための部品調達)

### 89.1 機構の概要

v10.7-v10.8 のオービスを拡張、v10.8 主要発見の 2 つの未解決点 (introduced < natural、bimodal 17.4%) を分離評価する 3 新条件 (A2 / B3 / C2) の post-process として実装。

主要モジュール:
- v109_atom_event_generator.py (3 新条件の atom_introduction_event 生成)
- v109_baseline_recalculator.py (各変動条件で baseline 再計算)
- v109_bimodal_analyzer.py (bimodal 1,540 件構造解析、KDE + median_split 代替)
- v109_sensitivity_evaluator.py (寄与候補感度評価、Cohen's d)
- v109_design_table_compiler.py (4 種設計表生成)
- v109_post_process.py (orchestrator、v10.7-v10.8 流用 + 拡張)

ファイル構造:
```
developmental/v109/
├── v109_phase_design.md             (主題ドキュメント、両 AI 統合修正版)
├── v109_2ai_consultation.md         (第一回 2 AI 意見聴取)
├── v109_2ai_followup_question.md    (Taka の問いに対する両 AI 再質問)
├── v109_atom_residency_reservation.md (Atom 常駐留保ドキュメント)
├── v109_implementation_brief.md     (Code A 実装指示書)
├── v109_code_recognition_check.md   (Code A 認識確認、設計の甘さ 7 件指摘)
├── v109_response_to_code_a.md       (即決事項返答)
├── v109_environment_check_report.md (Step B)
├── v109_step_c_report.md            (atom_event_generator A2/B3)
├── v109_step_d_report.md            (baseline_recalculator A2/B3)
├── v109_step_e_report.md            (bimodal_analyzer)
├── v109_step_f_report.md            (bimodal 24 seeds + C2 判定要請)
├── v109_step_f_judgment.md          (Web Claude 判定、4 決定事項)
├── v109_step_g_h_report.md          (C2 atom_event + baseline)
├── v109_step_i_report.md            (sensitivity_evaluator)
├── v109_step_j_k_report.md          (統合 smoke + main 判定要請)
├── v109_step_l_report.md            (24 seeds main run + 簡易集計)
├── v109_step_l_judgment.md          (Web Claude 判定、Q2/Q3 確定)
├── v109_main_run_report.md          (Code A 総括、Step N)
├── v109_phase_report.md             (主題完了レポート、Web Claude)
├── (Python 5 モジュール)
└── outputs/main/
    ├── (per-seed 出力 264 ファイル: atom_introduction_events / baselines / sensitivity / bimodal)
    └── cross_seed/
        ├── design_table_1_sensitivity.parquet
        ├── design_table_2_receptivity.parquet
        ├── design_table_3_routing.parquet
        ├── design_table_4_naturalness.parquet
        ├── level_1_mechanism_check.json
        ├── level_2_condition_diff.parquet
        ├── level_3_sensitivity.parquet
        ├── level_3_5_structural_integration.parquet
        ├── structural_integration_path_bimodal_timing.parquet
        └── v109_reservations.json
```

合計 277 files、190 MB。

### 89.2 3 新条件の構成

#### A2: Q -2 / C +2 (Q/C コスト変動)

```python
atom_event_record_A2 = {
    "Q_after_atom_event": Q_real_at_t - 2,  # post-process 計算的減算
    "C_after_atom_event": C_real_at_t + 2,
    "condition_id": "A2",
    "varied_factor": "Q_cost",
    "varied_level": 2,
}
```

A1 (Q-1/C+1) との比較で Q/C コスト感度を評価。

#### B3: random cid (cid 選定変動)

```python
atom_event_record_B3 = {
    "source_cid": random_cid_from_seed_pool,  # seed 内全 cid から random 100
    "top_k_rank": -1,
    "condition_id": "B3",
    "varied_factor": "cid_selection",
    "varied_level": 3,
}
```

B1 (top_k 100) との比較で cid 選定感度を評価。Atom 326 絶対化禁止規律の確認。

#### C2: リズム同調 (発火タイミング変動)

Step F bimodal 解析結果を踏まえた Web Claude 判定 (Q2 案 b 採用):
```python
atom_event_record_C2 = {
    "source_cid": cid_in_top_k_100,
    "timestamp": cid.t_birth + 200,  # 各 cid が age=200 で発火
    "condition_id": "C2",
    "varied_factor": "timing",
    "varied_level": 2,
}
```

C1 (案 α 均等分散) との比較で発火タイミング感度を評価。Gemini A2 Phase-locking の構造的実装。

### 89.3 25 atom (v10.6 → v10.8 → v10.9 で継承)

v10.8 で確立した 25 atom リストを継承。WLD.artless 留保ラベル付き、集計対象 24 atom。category 分布: PER 8、WLD 3、SOC 3、PRP 3、EXS 2、FND 2、BOD 1、COG 1、COM 1、TIM 1。

### 89.4 達成判定 17/17 PASS

認識確認 + 環境チェック + 3 新条件 main run + 各変動条件 baseline 再計算 + bimodal 構造解析 + C2 案 b 採用 + 寄与候補 3 つの感度評価 + 4 階層 reports + 4 種設計表 + 構造的統合 + natural baseline 比較 + 留保 3 件明記 + 24 seeds 単一バッチ + smoke 後止まって報告 + 同一ターン commit + push = 全項目クリア。

### 89.5 4 段階の階層化 (新規明示、GPT B5)

| Level | 内容 | 主結果 |
|---|---|---|
| L1: 機構動作確認 | 全 conditions で安定発火 | 12,960 sensitivity_rows、欠損なし |
| L2: 条件差確認 | 条件間で systematic な差 | timing × n_pulses 全 win 0.714 (大効果量) |
| **L3: 寄与候補感度評価** | 各候補のノブ定量化 | timing 0.300 圧倒、QC_cost 0.005 評価不能 |
| **L3.5: 構造的説明候補整合** | d と a の整合 | 「bimodal 支配性 ≠ 感度の強さ」 |

### 89.6 主要発見 4 件

#### 発見 1: 「強反応する cid は若い cid」 (Step F、構造)

bimodal 1,540 件のうち genuine_bimodal 918、その中で **H3_lifecycle が 553 (60.2%) で支配**:
- 高 delta 群 cid age = mean 224 / median 227
- 低 delta 群 cid age = mean 5,612
- 99% 方向一致、effect_size 0.85

#### 発見 2: timing > cid_selection > QC_cost の感度階層

| comparison | abs_mean | n_large_effect |
|---|---:|---:|
| timing | **0.141** | **757** |
| cid_selection | 0.024 | 18 |
| QC_cost | 0.005 | 0 (留保) |

#### 発見 3: 「Integration 外の高 familiarity cid」が最強・最 robust の入力経路 (新発見)

| path | mean | std |
|---|---:|---:|
| **high_fam_out_integ** | **0.222** | **0.079** |
| unrelated | 0.205 | 0.065 |
| familiarity | 0.044 | 0.218 |
| temporal | 0.015 | 0.220 |
| attention | 0.010 | 0.128 |

#### 発見 4: C2 で pulse 活動が大効果量で活発化

mean_n_pulses_in_window short 0.97、medium 0.75。

### 89.7 Level 3.5 構造的統合 (核心発見)

| path | bimodal 支配仮説 | timing 感度 | label |
|---|---|---:|---|
| high_fam_out | (なし) | 0.222 | sensitivity_strong_structure_weak |
| unrelated | (なし) | 0.205 | sensitivity_strong_structure_weak |
| temporal | H3 (74%) | 0.015 | structure_strong_sensitivity_weak |
| attention | H1 (48%) | 0.010 | structure_strong_sensitivity_weak |
| familiarity | H3 (59%) | 0.044 | marginal |

→ **「bimodal 支配性 ≠ 感度の強さ」** = ESDE Genesis 系の **構造的多重性**。

### 89.8 4 種設計表 (出口の固定)

#### 表 1: sensitivity_summary (540 rows)
- 3 比較 × 6 metrics × 10 paths × 3 windows
- timing × n_pulses × short = 0.97 (大効果量)

#### 表 2: receptivity_detection_criteria (核心、4 rows)
| criterion | operator | value | effect_size |
|---|---|---|---:|
| **cid_age** | <= | 560 | 0.864 |
| **in_integration** | == | 0 | 0.222 |
| **familiarity_max** | >= | top_quartile | 0.222 |
| n_core_member (副) | >= | 4.67 | 1.112 |

→ v10.10「受信可能状態」検出ルール: `if cid.age <= 560 AND cid.in_integration == False AND cid.familiarity_max >= top 25%: receptive`

#### 表 3: input_routing_criteria (10 rows)
| rank | path | recommendation |
|---:|---|---|
| 1 | high_familiarity_outside_integration_baseline | PREFER |
| 2 | unrelated_baseline | PREFER |
| 3+ | (他経路) | NEUTRAL |

#### 表 4: natural_likeness_design_criteria (180 rows)
- 全 180 cells のうち C2 が natural に近づいた cells: 84 (47%)
- unrelated: 16/18 (89%)、high_fam_out: 12/18 (67%)

### 89.9 性能と規模

- 24 seeds 並列実行 (multiprocessing 24 workers)
- main run: 112.74 秒 (smoke 込みで 約 150 秒)
- ストレージ: 190 MB (累計 v107+v108+v109 = 1.29 GB / 上限 21%)
- ファイル数: 277

### 89.10 Code A 認識確認ステップで発見・修正された設計の甘さ 7 件

#### 重大ブロッカー 1 件
- A. 9 条件 6 新条件のストレージ 4.4 GB = 上限 72% (打切閾値 50% 超過) → 案 c (3 新条件、上限 18%) で圧縮

#### 設計の甘さ 6 件
- B. C2 リズム同調が bimodal 解析依存 → bimodal 完了後に再実行
- C. B3 random cid 母集団 → seed 内全 cid から random 100
- D. A3 (Q 0/C 0) post-process 整合 → delta 計算スキップ (実施せず留保)
- E. 出口固定 4 種設計表のフォーマット → Code A 具体化
- F. bimodal 解析手法 → KDE 第一試行 + Mixture Model フォールバック (実際は KDE fallback 100% で median_split 代替)
- G. bimodal 1,540 件は seed 0 単独で 67 件のみ → cross-seed 集計が主流

連続 v10.7-v10.9 で合計 20 件の設計の甘さを Code A が補完。手戻りゼロ連続 4 段階。

### 89.11 物理層 frozen の維持 (bit-identity 検証)

#### 層 A: 同 seed 2 回実行
seed 0 を 2 回 (audit_run_a / audit_run_b)、v10.9 post-process 出力完全一致。

#### 層 B: v10.7/v10.8 baseline との比較
v10.7 出力 222 ファイル + v10.8 出力 368 ファイル = 590 files MD5 完全一致。

#### 層 C: v10.9 出力先縛り
全出力が `developmental/v109/outputs/main/` 配下、v105/v106/v107/v108 配下への書き込みなし。

### 89.12 v10.9 で確立した規律 (新規 4 + 継承)

#### 新規 4 件

1. **出口の固定規律** (GPT 提案): 成果物を v10.10 のための設計表 4 種として明示
2. **「原因」ではなく「寄与候補の感度評価」と呼ぶ命名規律** (GPT B3): 因果断定回避
3. **各変動条件で baseline 再計算規律** (GPT B6): 流用しない、比較可能性
4. **4 層階層化の明示規律** (GPT B5): L1/L2/L3/L3.5 を独立記録

#### 継承

v10.7 / v10.8 の規律全て継承。

### 89.13 留保事項 3 件

- 留保 1: bimodal 解析の手法的限界 (KDE fallback 100%、全件 median_split 代替)
- 留保 2: QC_cost (Q/C コスト) は v10.9 で評価不能 (post-process 限界、A1 vs A3 比較未実施)
- 留保 3: high_fam_out_integ 経路が最強の理由は構造的に未解明

### 89.14 v10.10 以降への素材

- 4 種設計表 (v10.10 主題決定の素材セット)
- 「条件適応型 atom 導入」の具体内容: cid age <= 500 + Integration 外 + 高 familiarity + age=200 timing
- v10.10 主題候補: 条件適応型 atom 導入 (第一推奨) / high_fam_out 構造解明 / Atom 常駐アンカー / B 群試験 / QC_cost 本格評価

具体的な v10.10 主題決定は別途議論。
