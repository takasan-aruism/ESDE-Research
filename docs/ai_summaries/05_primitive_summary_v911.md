# Primitive — AI 向け要約 (v9.11 完了版)

*原本*: docs/ESDE_Primitive_Report.md
*要約時点*: v9.11 完了 (2026-04-15)
*対象読者*: 未来の Claude

> **更新履歴**: v9.5 段階で原本記述終了。v9.6-v9.9 (subject reversal、introspection、information pickup、internal axis) は実装コード由来で追記。v9.10 (Pulse Model + MAD-DT)、v9.11 (Cognitive Capture) を本要約に統合。

---

## このフェーズが答えた問い

Cognition の「物理層は床」結論を踏まえ、その上に **存在層 + 認知層 (+ 将来の意識層)** をどう構築するか。物理層を一切触らずに、cid (cognitive id) が「世界を見る」「ノードを記憶する」「他者を認識する」「自分を内省する」「自分の固有値を持つ」段階を順に積み上げる。

**v9.11 到達点**: cid は物理層由来の固有値 (B_Gen) と固定記憶ベクトル (M_c) を持ち、周囲の現象 (E_t) との一致率 (Δ) から事象を確率的に捕捉する (capture) ようになった。物理層への介入なしに、cid 単位の認知差が成立。

---

## 用語

### 基本 (Cognition から継承)

- **label**: frozenset 固定の魂 (Autonomy 由来)、解放しない
- **cid (cognitive id)**: v9.8a で導入された **観察主体**。label とは独立した識別子。同じ label でも host を失えば cid は ghost 化、TTL 経過で reaped
- **disposition**: cid のキャラクター 4 軸 (social, stability, spread, familiarity)
- **phase_sig**: label の思想、birth 時の平均 θ で固定
- **φ (認知位相)**: label が structural world に追従する角度 (Phase 1)
- **attention map**: ノード ID → 出現頻度。接触記憶。decay_rate=0.99
- **partner familiarity**: 他 label ID → 接触頻度。decay_rate=0.998
- **ghost / hosted / reaped**: cid の状態遷移 (v9.8a)
- **TTL bonus / death pool / pickup**: 死亡 label の情報プール拾得 (v9.8c)

### v9.10 で導入

- **Pulse**: window から切り離された cid の観測タイミング。`is_pulse = (t % 50) == (cid % 50)`、cid ごとに分散、決定論的
- **PULSE_INTERVAL**: 50 step 固定
- **K**: 各 cid が保持する直近 pulse 履歴長、20 固定
- **MAD-DT (Mean Absolute Delta — Dynamic Threshold)**: `theta = mean(|Δx|)` を cid 履歴から自動算出、固定閾値を置換
- **R (主観的驚き指数)**: `R = Δx_current / (theta + epsilon)`、epsilon=1e-6
- **Normal tag**: `R > +1.0` で gain、`R < -1.0` で loss
- **Major tag**: 過去 K 回の R_max/R_min を更新した時に発火
- **tag_trigger**: Normal / Major / both / none / unformed の区別
- **Cold Start**: Pulse 1〜3 回目は unformed、タグ生成なし

### v9.11 で導入

- **B_Gen (Genesis Budget)**: cid 固有値 = -log10(Pbirth)。cid の発生確率の桁数。「ほぼ一意のパスワード + 認知原資」(Taka 構想)
- **M_c (Memory Core)**: cid の記憶ベクトル = (n_core, S_avg, r_core, phase_sig)。birth 時に固定
- **E_t (Experience)**: 各 pulse 時の事象ベクトル = (n_local, s_avg_local, r_local, theta_avg_local)
- **Δ (Delta)**: M_c と E_t の差分分解型 Weighted L1 一致率
- **Capture probability**: P(capture) = P_MAX × exp(-λ × Δ)
- **Capture**: cid が周囲の現象を「捕まえた」結果 (TRUE/FALSE/cold_start)

---

## v9.0-v9.3+ (存在層の確立)

1. **自己参照フィードバックループ成立** (v9.0): died_share_sum → EMA → torque modulation M。M=0.993 の微小変調で系は壊れない
2. **Torque は系を支配しない** (v9.1-v9.2): gamma -1.0~+1.0、clamp 解放でも survival ≈61%。物理層が支配的
3. **Torque の 2 相サイクル発見** (v9.2): pos0 攪乱→pos1-2 余波→pos3-4 回復、NET=-3.09 の負転
4. **Batch 処理が同時性攪乱の主因** (v9.3): 70 label 一斉適用で個体因果消失。逐次化で NET -3.09→-0.82
5. **Age 順が神の設計** (v9.3+): 古い label が θ 空間の「地盤」を整える。age 順で NET 初の正転 +0.08
6. **Longer window が仮想層を自律化** (v9.3+): 500 step/window で stress 介入 20 回に減少。仮想層が奴隷から自律へ
7. **Stress OFF で二重平衡干渉解消** (v9.3+): θ 空間とリンク密度の最適化基準競合を解消。NET +0.06、links 3080 で崩壊なし
8. **5-node は最も neutral** (Autonomy 継承): 全条件 survival ≈82-87%
9. **Territory 比は全サイズ 1.3× 一定**: 場の性質
10. **External Wave A=0.5 でも耐性**: ±50% エネルギー変動を破壊ではなく選別圧として吸収

---

## v9.4 Perception Field (知覚圏の発見)

- **Label 間カップリング probe 失敗**: 1-hop semantic gravity では label は孤島、影響圏が重ならない (5000 ノードに 70 label 散在)
- **方針転換**: 「何に作用するか」の前に「何を見ているか」を定義
- **Perception field**: label の alive ノード数 = hop 数 (5-node → 5-hop) で知覚範囲決定
- **Continuity observation**: world_J=0.988 (同じ世界を 99% 見続ける)、partner_J=0.81 (相手の 80% は同じ)
- **Worldlog**: spatial (固定 283) vs structural (激変 17-173) の発見

---

## v9.5 — 3 層構造の確立 (現在は 4 層に進化)

| 層 | 比喩 | 性質 | 動き |
|---|---|---|---|
| 物理層 | 波 | θ/S/リンク | 常に |
| 存在層 (旧称: 仮想層) | 粒子 | frozenset + phase_sig | 固定 (魂) |
| 認知層 | 過程 | 波と粒子の間のパターン | 動的 |

**※ v9.11 で意識層 (Layer 4) が概念化され、現在は 4 層構造**。意識層は認知層の解釈を検証する非介入レイヤとして v10.x で実装予定。

**Phase 1 — 認知位相 φ**: α × sin(mean_theta_structural - φ)。全 label DETACHED (α≈0.097 で過追従)

**Phase 1.5 — 対称分析**: convergence moments で near_phase 34% (divergence は 18%)

**Phase 2 — Attention Map** (完了):
- structural set 内ノードを毎 step +1、全体 ×0.99 で減衰 (半減期 69 step)
- L101: entropy 低下 0.72 (小さな世界で集中記憶)
- Label 間 hotspot 共有: L3↔L76 で 268 ノード (共有経験の原型)

**Phase 3 — Partner Familiarity** (v9.6+ で実装): {other_label_id: float}。decay=0.998 (半減期 346 step)

---

## v9.6-v9.7 — 却下された方針

(原本未記述、コード履歴より):
- **v9.7 population 統計フィードバック** → 集団統計を主体に直接読ませる方向は cid 概念の純粋性を損なうため後退
- **disposition の閾値ベース介入** → torque/action への反映は Gemini freeze ruling で禁則化

**重要**: v9.7 で「認知層から θ への介入」が試みられて失敗した経緯がある。v9.11 で B_Gen が導入されたことにより、この介入の必要性が**構造的に消滅**した。**将来の Claude は v9.7 的介入を再導入してはならない**。

---

## v9.8a Subject Reversal (cid の確立)

- **主体反転**: ラベル中心 → cid (cognitive id) 中心へ
- ghost 状態の導入: host (label) を失った cid は ghost 化、GHOST_TTL 経過で reaped
- cid は label とは別の識別子。同じ frozenset でも複数の cid が割り当てられうる
- 「魂は frozenset で固定、cid は経験で異なる」

## v9.8b Minimal Introspection

- **disposition 4 軸**: social, stability, spread, familiarity
- **gain_xxx / loss_xxx tag** の生成 (Stage 1)
- **観察専用** (Gemini freeze ruling): torque/action に一切反映しない
- ghost は無視 (is_hosted ガード)、初回 window (prev=None) は早期 return

**v9.8b の閾値 (v9.10 で動的化により廃止)**:
- 旧固定値: social=0.1, stability=0.1, spread=0.1, familiarity=2.0
- 4 軸不整合 (stability/spread=粗すぎ、familiarity=細かすぎ) が問題化
- v9.10 MAD-DT で自動補正

## v9.8c Information Pickup

- 死亡ラベルの「情報プール」: dead_lid と所属 cid 群
- **phase 距離による排他的競争**: hosted cid が phase 距離で picker を決定
- **効果は TTL 延長のみ** (`cid_ttl_bonus`)、物理層・vl・engine 不変
- GPT 監査条件遵守
- per_subject CSV: ttl_bonus, n_pickups_won/lost, effective_ttl

## v9.9 内的基準軸

- **recent_tags**: deque(maxlen=5)、frozenset(tags) を append
- **recent_dispositions**: deque(maxlen=5)、4 軸 dict を append
- **Rule 1** (n<3): unformed
- **Rule 2** (lowest_std_axis): personal_range の 4 軸 std が最小の軸、EPS=1e-9 で tie 判定
- **Rule 3** (dominant +/- drift): drift カウント最大の軸、整数厳密一致、最大値=0 なら "none"、複数同率なら "tie"
- **drift 累積禁止**: 毎回 recent_tags からゼロ再構築
- per_subject CSV に **v99_ prefix 33 列追加**
- physics/vl/pickup ロジック完全不変、smoke で per_window CSV bit identical 確認済

**所見 (v9.9)**: familiarity 負方向 drift 82.7% 支配、spread 沈黙 67.6%、L06 での familiarity 支配崩壊。これらが cid の内的特性か固定閾値アーティファクトか不明 → v9.10 で答えを出す。

---

## v9.10 Pulse Model & MAD-DT (exploration build、2026-04-12 完了)

### このフェーズが答えた問い

v9.9 所見は cid の内的特性か、それとも v9.8b 固定閾値のアーティファクトか。

**答え**: 固定閾値アーティファクト。cid 履歴ベースの動的閾値に置き換えると、L06 で familiarity 支配 54.8% が 27.1% に下がり 4 軸が均等化した。spread 沈黙も解消。

### 確定したこと

1. **v9.9 所見は固定閾値アーティファクトだった**: L06 での familiarity 54.8% 支配が v9.10 MAD-DT では 27.1% に半減、4 軸均等化 (social 28.2% / spread 27.0% / familiarity 27.1% / stability 17.7%)
2. **per_window CSV bit identical 維持**: LONG 5/5、SHORT 48/48、engine / VL / pickup 完全不変
3. **v99_/v10_ 列併存**: v9.9 観測系 (v99_ 33 列) を 1 バイトも触らずに v10_ 20 列を追加
4. **閾値問題解消**: v9.8b 固定閾値の 4 軸不整合が動的閾値で自動補正されることが実測で確認

### 却下された方針 (v9.10)

- **Stage 2 (母集団 p90 基準での固定閾値再設定)**: Taka 判断で skip。GPT 方針「固定値の最適化に入らない」と整合
- **R > 1.0 の閾値を最終形と扱うこと**: GPT 監査で明示的に禁止
- **遅延評価 (Lazy Evaluation)**: 当初 Gemini 案に含まれていたが実装時に破棄

### 残課題 (v9.11 へ申し送り済、未解決)

**stability 観測器の癖**: v9.10 で 4 軸均等化した後も stability のみ 17.7% と他 3 軸より低い:
- 原因: `window_st_sizes` が window 先頭でリセット、stability だけ「ノコギリ波」特性
- 数値証拠: |R|≤1.0 率が stability=75.0%、他軸 60.7〜68.0%
- **判定**: 観測器の癖の候補あり (ESDE 性質の可能性は否定できない)
- **状態**: v9.11 でも未修正、v9.12+ で要対応

### このフェーズで確立した運用ルール

- **「最初は固定、最終的には動的平衡」の実証**: 以後、固定閾値に戻らない
- **observation-regime shift comparison**: 観測方式が変わるバージョン間の比較は別観測系として扱う
- **v99_/v10_ 列併存パターン**: 観測方式変更時は旧系を残して併存
- **exploration build の明示**: 多変更時は tag_trigger 列で発火源切り分け
- **観測器の癖 vs ESDE 性質の切り分け規律**: (a) 計算式読み直し → (b) 分布詳細 → (c) 物理層相関、の順

---

## v9.11 Cognitive Capture (exploration build、2026-04-15 完了)

### このフェーズが答えた問い

cid の個体差を物理層介入なしにどう表現するか。「同じ cid 集団でも cid ごとに違う認知能力を持つ」を実装可能か。

**答え**: できる。cid の誕生条件 (n_core, S_avg, r_core) から計算される B_Gen (発生確率の桁数) と、それを 4 要素ベクトル (M_c) として保持し、周囲の現象 (E_t) との一致率 (Δ) から事象を捕捉確率 P(capture) で取捨選択する設計で達成。

### 4 層構造の確立 (v9.11)

物理層 / 存在層 / 認知層に **意識層 (将来)** を加えた 4 層構造として整理:
- 物理層: 上位層からの介入を受けない (存在層以外)
- 存在層: θ への torque のみ (微小変調)
- 認知層: 介入なし、観察のみ。**B_Gen 導入で「認知層から θ への介入」の必要性が消えた**
- 意識層: v10.x 以降、介入なし、認知層の検証のみ

「認知層は物理層に書き込まない」が**鉄則として確立**。grep で確認可能。

### 確定したこと

1. **B_Gen バンド構造**: 実測で n=2 → 12、n=3 → 19、n=4 → 26、n=5 → 34。short と long で Δ<0.05 で一致
2. **同 n_core 内の個体差**: バンド内 σ ≈ 0.4-0.8、cid ごとに違う B_Gen を持つ。Taka 構想「ほぼ一意のパスワード」達成
3. **桁違いの個体差**: 2-node 最強 vs 5-node 最強で 22 桁差 (Pbirth で 10^-11 vs 10^-33)
4. **B_Gen は capture の直接入力ではない**: M_c を経由する間接効果のみ。直接入力は n_core バンド支配で個体差を潰す (GPT 補正)
5. **L06 長命群の発見**: 上位 10% 長命 cid は n=5 優勢 (61.4%)、capture rate が overall より低い (0.307 vs 0.379)。「複雑構造ほど追跡困難、時間で Δ 蓄積」を自然再現
6. **per_window CSV bit identical 維持**: smoke で v9.10 と完全一致
7. **v99_/v10_/v11_ 列併存**: v11_ prefix で末尾追加のみ

### 確定した計算式

```
ρ        = links_total / C(N, 2)            (N = 5000)
Pbirth   = (1 / C(N, n_core)) × ρ^(n-1) × r_core^(n-1) × S_avg^(n-1)
B_Gen    = -log10(Pbirth)

M_c      = (n_core, S_avg, r_core, phase_sig)     [birth 時固定]
E_t      = (n_local, s_avg_local, r_local, theta_avg_local)  [pulse 時抽出]

Δ_n      = |n_core - n_local| / NORM_N           (NORM_N = 86)
Δ_s      = |S_avg - s_avg_local| / NORM_S        (NORM_S = 1.0)
Δ_r      = |r_core - r_local| / NORM_R           (NORM_R = 1.0)
Δ_phase  = |circular_diff(phase_sig, theta_avg_local)| / π

Δ        = 0.25 × (Δ_n + Δ_s + Δ_r + Δ_phase)    [均等重み暫定]
P(capture) = 0.9 × exp(-2.724 × Δ)              [Variant A]
```

### GPT 監査による補正 (採用済)

1. Variant A 採用 (smooth、推論可能)
2. phase は circular_diff / π で正規化
3. similarity は cosine ではなく差分分解型 Weighted L1
4. B_Gen は capture 計算に直接入れない (バイアス回避)
5. 各軸 (d_n/d_s/d_r/d_phase) を per_subject CSV に個別記録

### 却下された方針 (v9.11)

- **Empirical frequency Pbirth (Nlookback=100)**: n=2 で Pbirth>1 破綻
- **Combinatorial probability with lattice**: 二重トポロジー発見で破綻
- **Genesis Budget = n × S × r (線形)**: 桁差わずか 2.5 倍で「桁違い個体差」未達
- **Monte Carlo (1000 並列宇宙)**: 計算重すぎ (1 cid あたり 16 時間)
- **B_Gen による Pulse Interval 変調**: 「行動を命令する」設計は神の手、capture probability に置換

### Taka 構想の確認 (v9.11 実測で達成)

> ここで得られる数値は暗号化されたパスワードのようなもので、ほぼ一意で同じものはなく、かつ発生の確率の低さがその個体の行動を起因する原資を持つ。

→ B_Gen バンド構造 + バンド内分散で実装。

> 必然的に 5 ノードは 4 ノードよりも確率は低い。

→ 7 桁差で実装 (n=4 → 26、n=5 → 34)。

> ESDE の場合は桁数で具体的に階層が示される。これが強み。

→ 22 桁差 (n=2 vs n=5) で実装。アメーバと人間の世界の差を桁数で表現。

### 残課題 (v9.12+ へ申し送り)

**1. 軸寄与の偏り (要 audit)**:
- phase + r で 72-73%、n + s で 27-28%
- 仮説 A: ESDE 物理本性 (phase/r が支配的)
- 仮説 B: NORM_N=86 が大きすぎて d_n 圧縮
- 仮説 C: M_c/E_t 設計が phase/r 寄り
- **対応**: 重み変更前に NORM 感度分析を実施

**2. 内部記憶の不在**:
- capture は CSV ログのみ、cid 自身は覚えていない
- v10.x 意識層の前提条件
- 最小限 (EMA など) は v9.12 で着手候補

**3. n=6-9 が出ない**:
- v8.x Autonomy では n=9 まで観測
- v9.x で頭打ち、原因要調査
- v9.13 以降の課題

**4. stability 観測器の癖** (v9.10 から継承、未解決)

### 運用ルールの確立 (v9.11)

- **Claude Code A/B 分担**: A=実装+audit、B=コードチェック (read only)
- **チェック依頼書必須**: `xx_check_request.md` → `xx_check_approved.md` or `xx_check_needfix.md`
- **並列化必須**: 複数 seed run は parallel 化、sequential 禁止
- **OMP/MKL/OPENBLAS_NUM_THREADS=1 必須**: numpy 内部スレッドと parallel の競合回避
- **system_structure ドキュメント必読**: 新スレッドの相談役 Claude は必ず最初に読む
- **AI の誤読が測定器**: Triad のズレが Taka の直感の輪郭抽出に役立つ (Taka 発言)

---

## 確定した運用ルール (v9.11 までの累積)

- **物理層への非介入**: 認知層は物理層・存在層に書き込まない。torque は微小、支配的ではない
- **観察は cid の中で完結**: state.theta / S / R は一切変更しない
- **逐次化が最小変更で最大効果**: 計算式同じ、適用順序のみで NET 大幅改善
- **Age 順は自然な秩序**: 古い label が θ の地盤を整える
- **Frozenset は解放しない**: 魂は固定、動きは認知層内部状態から
- **同じ frozenset から異なるキャラが立ち上がる**: 経験差異が性格を生む
- **一次出力は構造語のみ** (v9.9): "formed"/"unformed"/"tie"/"none" — 数値解釈は analyzer 段階
- **cid は履歴を読まない、書き込みのみ** (v9.9): loop は閉じない、観察主体に徹する
- **固定閾値に戻らない** (v9.10): MAD-DT 以降、動的閾値が原則
- **B_Gen は capture に直接入れない** (v9.11): M_c 経由の間接効果のみ
- **M_c は 4 要素固定** (v9.11): 次元の呪いを避ける
- **phase は circular distance で扱う** (v9.11): 単純実数差禁止
- **similarity は差分分解型** (v9.11): コサイン類似度は使わない
- **誤差は per_subject CSV に記録** (v9.11): 「埋め合わせ」は v9.12 以降
- **新運用 A/B 分担** (v9.11): 実装と検証を分離、チェック依頼書必須

---

## 次フェーズへの橋渡し

v9.11 完了時点で v9.12 以降の優先課題:

### 優先度 1 (v9.12 で扱う候補)

1. **軸寄与の偏り audit**: NORM 感度分析、軸相関、E_t 妥当性 (GPT 推奨)
2. **stability 観測器の癖修正**: v9.10 から継承、未解決

### 優先度 2 (v9.12 後半 〜 v9.13)

3. **第 3 層 (出来事の客観的価値)** の設計開始: Taka 3 層構造の残り
4. **「事象」の定義の精緻化**: E_t の構成は十分か
5. **cid の最小限の内部記憶** (Δ の EMA など): 意識層への前提

### 優先度 3 (v9.13 〜 v9.14)

6. **Variant 進化 (B → C)**: 事象定義が固まってから
7. **n=6-9 が出ない問題の調査**: v8.x との run 条件比較

### 優先度 4 (v10.x 以降)

8. **意識層の実装**: 認知層の解釈を非介入で検証
9. **複数 cid 間の interaction**: 戦国大名モデル、コミュニティ
10. **外部コネクター**: 物理現象として注入、frozenset として消えていく

最終目標 (Taka 構想): 「神の手なしに認知・意味・社会性が創発するモデル」、当面のゴールは「会話できるシステム」。**ESDE は投資**、結果が出ないなら撤退判断もありうる (Taka スタンス)。

---

## 原本を読むべきタイミング

- Pulse Model & MAD-DT の数式詳細や cold start 境界条件
- L06 の 4 軸均等化の数値 (v9.9 比較表)
- stability 観測器の癖の |delta|/theta/R 詳細分布
- Triad (Gemini 設計 → GPT 監査 → Claude 実装) の議論経緯
- v99_/v10_/v11_ 列併存の具体的な列構成
- v9.11 capture probability の 3 variant (A/B/C) 比較
- B_Gen の Pbirth 式の導出 (組み合わせ確率 + 物理条件)
- 4 層構造の介入規律の詳細 (意識層の哲学的立場含む)
- Taka 発言の引用 (パスワード、認知原資、桁違い、事象 = 現象そのもの、誤差の埋め合わせ、認知 vs 意識、外部コネクター構想)
- v9.11 本番 run 結果 (B_Gen 分布、capture rate、L06 解釈)
- v9.12+ への論点 (軸寄与の偏り、第 3 層、内部記憶、変分進化)
