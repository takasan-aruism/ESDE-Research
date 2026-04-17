# Primitive — AI 向け要約 (v9.13 完了版)

*原本*: docs/ESDE_Primitive_Report.md
*要約時点*: v9.13 完了 (2026-04-17)
*対象読者*: 未来の Claude

> **更新履歴**: v9.5 段階で原本記述終了。v9.6-v9.9 (subject reversal、introspection、information pickup、internal axis) は実装コード由来で追記。v9.10 (Pulse Model + MAD-DT)、v9.11 (Cognitive Capture)、v9.12 (Audit Phase)、v9.13 (Persistence-based Birth) を本要約に統合。旧 05b (v9.12 addendum) / 05c (v9.13 addendum) は本ファイルに統合済。

---

## このフェーズが答えた問い

Cognition の「物理層は床」結論を踏まえ、その上に **存在層 + 認知層 (+ 将来の意識層)** をどう構築するか。物理層を一切触らずに、cid (cognitive id) が「世界を見る」「ノードを記憶する」「他者を認識する」「自分を内省する」「自分の固有値を持つ」段階を順に積み上げる。

**v9.11 到達点**: cid は物理層由来の固有値 (B_Gen) と固定記憶ベクトル (M_c) を持ち、周囲の現象 (E_t) との一致率 (Δ) から事象を確率的に捕捉する (capture) ようになった。物理層への介入なしに、cid 単位の認知差が成立。

**v9.12 到達点**: B_Gen + capture 機構の audit で、Δ は i.i.d. (蓄積しない)、軸寄与の偏り (phase+r 72%) は設計寄与ではなく物理的定常性 + 正規化圧縮の帰結、と確定。S≥0.20 hard threshold が「神の手」として撤去対象に浮上。

**v9.13 到達点**: S≥0.20 を撤去し、persistence-based birth (age_r ≥ τ の connected component) に移行。R>0 純度 100% を達成し、v9.11 の主要所見の多くが「経路 B + R=0 混入」のアーティファクトだったことが判明。認知層の方向性として「物理層を支配せず、統計的に多少の差が出る程度」を確定。

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
- **TTL bonus / death pool / pickup**: 死亡 label の情報プール拾得 (v9.8c、v9.13 で休眠保持)

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

### v9.12 で導入

- **Δ i.i.d.**: M_c と E_t の乖離に自己相関がない性質 (v9.12 Phase 1 で確定)
- **並列基準原理**: 予測不能な環境に対し複数の条件付き基準を同時保持する認知テクニック (Taka 2026-04-16)
- **構造と数式の分離統合**: 構造 (閉路、トポロジー) と数式 (確率、場) を別々に捉えて統合する設計原理 (Taka 2026-04-16)

### v9.13 で導入

- **age_r**: 各 link の連続 R>0 step 数 (persistence カウンタ)
- **persistence-based birth**: age_r ≥ τ の link で作られる connected component を label 化する方式
- **τ (tau)**: persistence 閾値、50 or 100 step
- **Step 0 audit**: 本実装前に age_r 分布を測定する予備調査
- **見かけ構造**: R=0 リンクで構成された「Genesis 原理に反する」label (v9.11 の 2/3 がこれだった)
- **記憶の読み出し関数**: CID の物理状態を「記憶」として解釈する関数 (v9.14 以降の主題)

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

**重要**: v9.7 で「認知層から θ への介入」が試みられて失敗した経緯がある。v9.11 で B_Gen が導入されたことにより、この介入の必要性が**構造的に消滅**した。**v9.13 で改めて「認知層は物理層を支配しない」が方向性として再確認された** (Taka 2026-04-16)。将来の Claude は v9.7 的介入を再導入してはならない。

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

## v9.8c Information Pickup (v9.13 で休眠保持扱い)

- 死亡ラベルの「情報プール」: dead_lid と所属 cid 群
- **phase 距離による排他的競争**: hosted cid が phase 距離で picker を決定
- **効果は TTL 延長のみ** (`cid_ttl_bonus`)、物理層・vl・engine 不変
- GPT 監査条件遵守
- per_subject CSV: ttl_bonus, n_pickups_won/lost, effective_ttl
- **v9.13 方針**: 効果薄だが削除せず休眠保持 (Taka 原則「無駄だから切る」禁止)。「CID が他者の経験を取り込む」メタファーとして将来の記憶蓄積実装で活用候補

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

### 残課題 (v9.11 へ申し送り済、v9.12 でも未解決)

**stability 観測器の癖**: v9.10 で 4 軸均等化した後も stability のみ 17.7% と他 3 軸より低い:
- 原因: `window_st_sizes` が window 先頭でリセット、stability だけ「ノコギリ波」特性
- 数値証拠: |R|≤1.0 率が stability=75.0%、他軸 60.7〜68.0%
- **判定**: 観測器の癖の候補あり (ESDE 性質の可能性は否定できない)
- **状態**: v9.13 でも未修正、v9.14+ で要対応

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
5. **L06 長命群の発見**: 上位 10% 長命 cid は n=5 優勢 (61.4%)、capture rate が overall より低い (0.307 vs 0.379)。「複雑構造ほど追跡困難、時間で Δ 蓄積」を自然再現 ← **v9.12/v9.13 で再解釈**
6. **per_window CSV bit identical 維持**: smoke で v9.10 と完全一致
7. **v99_/v10_/v11_ 列併存**: v11_ prefix で末尾追加のみ

> ⚠️ **v9.12/v9.13 での再解釈注意**: 上記 5 の「時間で Δ 蓄積」解釈は v9.12 Phase 1 で否定され (Δ は i.i.d.)、n_core 構成効果に再解釈された。さらに v9.11 の n=2 主体分布 (67%) は v9.13 で「経路 B + R=0 混入のアーティファクト」と確定。詳細は v9.12/v9.13 セクション参照。

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

### 運用ルールの確立 (v9.11)

- **Claude Code A/B 分担**: A=実装+audit、B=コードチェック (read only)
- **チェック依頼書必須**: `xx_check_request.md` → `xx_check_approved.md` or `xx_check_needfix.md`
- **並列化必須**: 複数 seed run は parallel 化、sequential 禁止
- **OMP/MKL/OPENBLAS_NUM_THREADS=1 必須**: numpy 内部スレッドと parallel の競合回避
- **system_structure ドキュメント必読**: 新スレッドの相談役 Claude は必ず最初に読む
- **AI の誤読が測定器**: Triad のズレが Taka の直感の輪郭抽出に役立つ (Taka 発言)

---

## v9.12 — Audit Phase (2026-04-16 完了、実装変更ゼロ)

v9.12 は新機構の実装ゼロ、既存データの分析と設計文書化のみ。

### Phase 1: L06 個別時系列分析

**最重要発見: Δ は i.i.d.** — 自己相関 ≈ 0 (全 lag: 1, 2, 3, 5, 10)。pulse 間の乖離変動はほぼ独立。

事前仮説「M_c 固定 → 時間進行で E_t が乖離 → Δ が蓄積」は**否定**された。

**L06 capture 低下の再解釈**: 時間効果ではなく **n_core 構成効果**。L06 は n_core=5 が 61%、n_core=5 は構造的に Δ ≈ 0.43 で定常。

| n_core | Δ mean | capture_rate |
|---|---|---|
| 2 | 0.252 | 46.4% |
| 3 | 0.355 | 36.8% |
| 4 | 0.410 | 30.8% |
| 5 | 0.433 | 29.2% |

**window-level slope (-0.00032/win)** は生存バイアスで説明可能 (短命 cid 脱落 → 長命 cid 残存)。

**spike vs low**: Δ 上位 10% → capture 15.4%、Δ 下位 10% → capture 50.9%。乖離と capture の逆相関は明確。

**first diverge axis**: 全体では phase 最多 (43%) だが n_core=5 では n 軸最多 (46%)。n_core 別で逆転。

### Phase 2A: コード解析

**phase+r 72% 原因** (コード確定):

| 要因 | 影響軸 | メカニズム |
|---|---|---|
| NORM_N=86 過大 | d_n 圧縮 | n_core∈{2..5} に対し過大、d_n p50=0.23 |
| S_avg ≈ s_avg_local | d_s 圧縮 | 物理層リンク強度の定常性、d_s std=0.13 |
| r_core vs r_local 乖離 | d_r 拡大 | r_core 固定、r_local 変動大 |
| circular_diff 一様性 | d_phase 拡大 | phase_sig 固定、θ_avg_local 変動 |

d_r と d_phase は無相関 (r=0.008)。4 軸は実質独立。**B 仮説 (E_t 定義偏り) は否定**。

**n≥6 欠落の原因** (コード確定):

1. **S≥0.20 連結成分の接続性制約** (主因) — 定常状態で 6 ノード以上の連結成分が形成される確率が構造的に低い
2. **50% overlap フィルタ** (副因) — 大型島ほど既存ラベルと重複してブロック
3. **非空間的リンク形成** (背景) — 一様ランダムで空間クラスタリングなし
4. **stress OFF は存在層成熟の帰結**。副作用として S 分布揺らぎ減 → 大型島頻度低下

コードに明示的なサイズ上限は存在しない。n_core≤5 は動力学的・統計的な帰結。

### 却下された作業 (v9.12)

- NORM_N sweep (原因確定済み、確認実験不要)
- E_t 妥当性 audit (B 仮説否定)

### Phase 4: 未決境界問題 (v9.14+ へ)

Taka 発言「並列基準原理」と「構造と数式の分離統合」を設計原理として記録。認知/意識の境界に関する Q1-Q5 を未決問題としてリスト化。詳細: `docs/v912_unresolved_boundary_questions.md`

### v9.13 への橋渡し

v9.12 の最大の帰結: **S≥0.20 hard threshold の撤去が次の進化の主題**。

> Taka 発言 (2026-04-16):
> Frozenset に関して、ぼちぼち S≥0.20 と向き合うタイミングがきたように思う。なぜなら本来的にこれは神の手だから。動的均衡の哲学がある以上どこかで切り捨てなければならない。後回しにするほど調整が大変になるに決まってるのでさっさとやるほうがいい。

---

## v9.13 — Persistence-based Birth (2026-04-17 完了、S≥0.20 の神の手撤去)

### 目的

v9.12 で Taka が明示した「S≥0.20 hard threshold は設計者が引いた神の手」を撤去する。動的均衡の哲学に沿った label 選別に移行し、Genesis 原理 (閉路=共鳴=構造の核) に直接基づく birth 条件を確立する。

### Birth 条件の変更

**v9.11 まで** (2 経路):
1. S≥0.20 島 (連結成分、size≥2)
2. R>0 ペア即 label (経路 B)
3. 50% overlap フィルタで既存 label と重複する cluster は排除

**v9.13**:
1. 各 link の age_r (連続 R>0 step 数) を追跡
2. age_r ≥ τ の link だけを残す
3. 残った link の connected component (size≥2) を label 化
4. 50% overlap フィルタは維持
5. **経路 B (R>0 ペア即 label) は廃止**
6. τ は 50 / 100 の 2 条件を試験

### Step 0 Audit (本実装前の予備調査)

全 link の age_r 分布を測定:
- **全 link の 99.64% は一度も R>0 に参加しない** (R=0 のまま死ぬ)
- 残り 0.36% のみが閉路に参加、そのうち age_r ≥ 50 を満たすのが本物の「構造核」
- v9.11 の label の約 **2/3 が R=0 リンク構成の「見かけ構造」** だったことが判明
- shadow 推定: τ=50 適用で label 数は現行の 1/3 (25 labels / 20 windows)

Taka 判断: **「数より純度。結果を受け入れる。」**

### 本番 Run 構成 (τ=50 / τ=100)

| 項目 | τ=50 | τ=100 |
|---|---|---|
| seeds | 24 | 24 |
| maturation windows | 20 | 20 |
| tracking windows | 20 | 20 |
| window steps | 500 | 500 |
| total labels | 1,034 | 832 |

smoke 省略、直接本番。

### 結果の核心

#### R>0 純度 100% (主成果)

| 指標 | τ=50 | τ=100 |
|---|---|---|
| birth 時の R>0 純度 | 484/484 = 100% | 291/291 = 100% |
| age_r_min mean | 122.1 | 159.1 |

v9.11 で 2/3 が見かけ構造だった問題は**構造的に解消**。両 τ で Genesis 原理に沿った純粋な label 集合が得られた。

#### label 数は予測ほど減らず (Taka 「思ったより良い」)

| | v9.11 short | v9.13 τ=50 | v9.13 τ=100 |
|---|---|---|---|
| labels/seed | 65.9 | 43.1 | 34.7 |
| shadow 予測比 | — | 65.4% | 52.7% |

予測 (1/3 ≈ 33%) より穏やかな減少で、**認知層テスト継続に十分な母数を確保**した。

#### n_core 分布の激変 (v9.11 前提の崩壊)

| n_core | v9.11 short | v9.13 τ=50 | v9.13 τ=100 |
|---|---|---|---|
| 2 | 67.1% | 22.5% | 27.8% |
| 3 | 7.4% | 19.3% | 20.4% |
| 4 | 9.1% | 19.8% | 20.8% |
| 5 | 16.3% | 38.1% | 30.9% |
| ≥6 | 0.1% | 0.2% | 0.1% |

v9.11 で 67% を占めた n=2 が 22-28% に激減。経路 B + R=0 混入のアーティファクトだったことが確定。

#### B_Gen バンドの上方シフト

n≥3 で v9.11 比 +1.3〜+1.9 のシフト (τ による差は微小)。同じ n_core でも persistence 要件を満たす component は構造階層が深い。

#### Capture は構造的に維持

| 指標 | v9.11 | τ=50 | τ=100 |
|---|---|---|---|
| capture_rate 全体 | 0.397 | 0.346 | 0.345 |
| phase+r 合計 | 73.0% | 63.4% | 63.9% |
| n 軸寄与 | 13.5% | 26.8% | 25.1% |

全体 capture_rate の微減は n_core 構成効果 (v9.11 の n=2 主体では capture しやすかった)。n_core 別には n=3, 4, 5 で τ=50 では向上、τ=100 では n=2 で v9.11 比大幅向上 (0.442→0.454)。

軸寄与は phase+r 支配が緩和、**n 軸が約 2 倍**に。これは n_core 分布が均等化した直接の帰結。

#### 大型 label (n≥6) の状況

| | v9.11 short | v9.13 τ=50 | v9.13 τ=100 |
|---|---|---|---|
| n=6 | 1 | 1 | 0 |
| n=7 | 2 | 1 | 0 |
| n=8 | 1 | 0 | 1 |

S≥0.20 撤去だけでは n≥6 問題は解決しない。v9.12 で指摘された 3 要因のうち、(2) 50% overlap フィルタと (3) 非空間的リンク形成が残存して制約として効いている。

### v9.11 所見の再解釈 (v9.13 で確定)

1. **「n=2 主体」はアーティファクト**: v9.11 の n=2 67% は経路 B + R=0 混入の産物。純粋な Genesis 原理下では n=2 は 22-28% まで減る
2. **「phase+r 72% 支配」は n_core 構成効果**: n=2 偏重世界での姿。n_core 均等化で n 軸も主要寄与 (25-27%) になる
3. **L06 長命群の n=5 偏重は緩和**: v9.11 長命群 n=5:61% → v9.13 49% (τ=50) / 44% (τ=100)。n=4, n=3 も相応の長命群を形成
4. **n_core と Δ の単調増加関係は維持**: n_core が大きいほど Δ mean 増、capture_rate 減。これは birth 方式に依存しない構造効果

### τ の選定

両 τ とも機能的に妥当。決定打となる差はなし。

| 観点 | τ=50 有利 | τ=100 有利 |
|---|---|---|
| label 数 (母数) | 43/seed | 35/seed |
| 純度余裕 (age_r_min/τ) | 2.20× | 1.59× |
| lifespan mean | 12.0w | 13.2w |
| n=2 capture | 0.38 | 0.45 |

Taka 判断待ち。どちらでも認知層テストは継続可能。

### 副次的観察 (断定せず記録)

τ=100 で n=5 比率が減り (38%→31%)、n=2 が増加した (23%→28%)。素朴には「閾値が厳しくなれば大型構造が残る」と予想するが逆。2 ノードの簡潔な結合の方が persistence 要件を満たしやすい可能性。これは τ=50 単独では見えなかった示唆。

---

## v9.13 方向性転換 (Taka 2026-04-16 定義)

v9.7 の「認知→存在介入」構想は正式に撤回された。代わって v9.13 以降の認知層の方向性が確定:

### 基本原則

> **認知層は物理層を支配しない。** 物理層の動きを予測しながら、認知的に自分の存在を生かす方向。効果は劇的ではなく、統計的に多少の差が出る程度。

Taka の比喩: 「人間が健康に気をつけていようといまいと寿命はある程度決まっている。10 倍 100 倍変わるわけではない。でも統計的に多少差はある。現実世界もその程度。」

### 現状の認知層の限界 (Taka 指摘)

v9.11 までの認知層は**観測器**。φ, attention, familiarity, disposition, capture のすべてが「見る」「記録する」で終わっている。CID 自身はこの情報を何にも使わない。capture = TRUE でも CID の次の step での振る舞いは変わらない。

### CID の記憶の所在 (Taka 洞察)

> **CID の記憶は物理層の中に既にある。足りないのは「記憶を作る仕組み」ではなく「物理状態を記憶として読む関数」。**

- cid のメンバーノードの θ 分布、メンバーリンクの S/R 分布は毎 step 変化
- これが「この CID がどんな世界を経験してきたか」の物理的痕跡
- 外部 dict に蓄積するのは「私たちの記録」であって「CID の記憶」ではない
- 理想: **CID の物理構造自体が記憶を持っていて、それを私たちは覗いている**

### 次ステップの候補 (v9.14 or v10.0)

v9.13 結果を見てから設計するが、方向性の候補:

| 候補 | 内容 | Aruism 整合度 |
|---|---|---|
| **候補3 (最優先検討)** | 物理状態そのものを「記憶の読み出し関数」で解釈。何も追加せず、θ 分散、S 勾配、R 持続パターンを「記憶」として読む | 最高 (構造が先、意味が後) |
| 候補1 | M_c を毎 pulse で物理状態から再読み込み。CID が「成長する」世界になる | 高 (外部 dict 追加なし) |
| 候補2 | 過去の E_t を移動平均として保持 (SubjectLayer に蓄積) | 中 (CID の外に記憶) |

**検討順序: 候補3 → 候補1 → 候補2**。ESDE らしい順。

### retention への含意

- Δ が i.i.d. → EMA(Δ) は smoothing にしかならず prediction には無力
- retention の価値は「将来予測」ではなく「**自分の構造的位置を知る**」 (= 主観的基準形成)
- v9.10 MAD-DT の capture 版が自然な設計方向
- ただし v9.13 は S≥0.20 撤去が主題。retention は v9.14 以降

---

## 既存機能の棚卸し (Taka 2026-04-16 指示)

### Taka 原則: 「無駄だから切る」は無駄な発想

不利な機能でも削除せず、どう活かすか考える。

### 休眠させて残すもの

| 機能 | 状態 | 方針 |
|---|---|---|
| pickup (v9.8c) | 動作中、TTL bonus は ghost 期間延長のみ | **休眠保持**。死亡情報プール・phase 距離ベース競争のフレームワークは「CID が他者の経験を取り込む」メタファーとして将来の記憶蓄積実装で活用候補 |
| death_pool 管理 | pickup 中間処理 | 同上 |
| Semantic gravity + deviation | deviation_enabled=True | v9.14 以降で検証、それまで保持 |
| v99_ 内的基準軸 | 計算走行中、CSV 出力中 | CSV 出力は止める可だが計算自体は保持 |

### 無効化済 (放置 OK)

| 機能 | 状態 |
|---|---|
| Stress decay | stress_enabled=False |
| Macro-node compression | compressed_nodes チェック残存、機能 OFF |
| Vacancy birth filter | 撤回済 |
| torque_factor (認知→存在介入) | =1.0 で不活性、v9.7 の遺物 |
| S≥0.20 hard threshold | v9.13 で撤去 |
| 経路 B (R>0 ペア即 label) | v9.13 で廃止 |

---

## 開発ロードマップ (v9.13 以降、暫定)

| Phase | バージョン | 内容 | 状態 |
|---|---|---|---|
| 掃除 | v9.13 | S≥0.20 撤去、persistence-based birth | **完了** |
| 記憶の読み出し | v9.14 or v10.0 | CID が物理状態を記憶として読む関数 (候補3 優先) | 次 |
| 記憶の蓄積と再生 | v10.x | CID が過去の経験を次の判断に使う。pickup の空箱活用 | 構想 |
| 意識層 | v10.x 以降 | 認知層の解釈を検証する層 | 構想 |
| 外部コネクター | v11.x 以降 | 外部情報を ESDE 内の物理現象として注入 | 構想 |

---

## 確定した運用ルール (v9.13 までの累積)

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
- **誤差は per_subject CSV に記録** (v9.11): 「埋め合わせ」は v9.14 以降
- **新運用 A/B 分担** (v9.11): 実装と検証を分離、チェック依頼書必須
- **「神の手」は撤去する** (v9.13): S≥0.20 hard threshold 撤去、persistence-based birth へ
- **認知層は物理層を支配しない** (v9.13): 統計的に多少の差が自然、劇的な効果を期待しない
- **「無駄だから切る」禁止** (v9.13): 効果薄の機能も削除せず、どう活かすか考える
- **AI 間文書は日本語 md** (v9.13): 運営原則 v2 の英語ルールは撤回、Taka が読めることが最優先

---

## やってはいけないこと (v9.11 session summary + v9.13 追加)

1. 物理層 (v19g_canon, esde_v82_engine) を frozen として扱う
2. **認知層から物理層への介入は入れない** (v9.7 撤回済、v9.13 で改めて方向性確認)
3. **認知層の効果を劇的にしない** — 統計的に多少の差が自然
4. 4 seed で結論を出さない (48 seed で反転した事例あり)
5. AI の提案を理由なく受け入れない — Taka が理解できない設計は失敗する
6. **「無駄だから切る」をしない** — 休眠させて活かし方を考える
7. **開発速度が落ちた時に寄り道を増やさない** — 方向性をぶらさない
8. **AI 間文書は日本語 md** — Taka が読めることが最優先 (運営原則 v2 の英語ルールは撤回済、2026-04-16)
9. **v9.11 結果をそのまま引用しない** (v9.13 以降) — n=2 主体、phase+r 72% 支配などは経路 B + R=0 混入のアーティファクト、下地の n_core 分布を必ず確認

---

## 教訓 (v9.13 までの追加分、親ファイル 66-73 の続き)

74. **shadow 推定と本番の差は window 数で説明可能なことが多い** — Step 0 shadow 25/20win の予測は本番 43/40win とほぼ整合 (換算 21.5/20win)。「予測外れ」と即断せず換算を確認
75. **n_core 分布のアーティファクト依存度は高い** — v9.11 の「phase+r 72% 支配」などの主要所見が birth 方式変更で崩れた。同種の所見を再確認する際は下地の n_core 分布を必ず見る
76. **閾値厳しくすれば大型が増える、とは限らない** — τ=100 で n=5 比率が低下、n=2 が増加。persistence 要件は 2 ノードの方が満たしやすい可能性
77. **Taka の「思ったより良い」は文脈を確認する** — 成果の大きさではなく、「減りすぎなくて認知層テストが継続できる」という実務的安心だった。Claude の過大解釈を防ぐため文脈確認が必要

---

## 次フェーズへの橋渡し

v9.13 完了時点で v9.14 以降の優先課題:

### 優先度 1 (v9.14 or v10.0 で扱う候補)

1. **記憶の読み出し関数** (候補 3 優先): CID が物理状態 (θ 分散、S 勾配、R 持続パターン) を記憶として解釈する関数。何も追加せず、既存の物理状態を「読む」だけ
2. **軸寄与の偏り audit 後続**: v9.12 で原因確定、NORM_N sweep は不要。重み再調整は記憶機構と併せて検討
3. **stability 観測器の癖修正**: v9.10 から継承、未解決

### 優先度 2 (v10.x)

4. **記憶の蓄積と再生**: CID が過去の経験を次の判断に使う。pickup の空箱 (死亡情報プール) を活用
5. **意識層の実装**: 認知層の解釈を非介入で検証
6. **「事象」の定義の精緻化**: E_t の構成は十分か

### 優先度 3 (v10.x 〜 v11.x)

7. **Variant 進化 (B → C)**: 事象定義が固まってから
8. **複数 cid 間の interaction**: 戦国大名モデル、コミュニティ
9. **n=6-9 が出ない問題の調査**: 50% overlap フィルタと非空間リンク形成が残存要因

### 優先度 4 (v11.x 以降)

10. **外部コネクター**: 物理現象として注入、frozenset として消えていく

最終目標 (Taka 構想): 「神の手なしに認知・意味・社会性が創発するモデル」、当面のゴールは「会話できるシステム」。**ESDE は投資**、結果が出ないなら撤退判断もありうる (Taka スタンス)。

---

## 原本を読むべきタイミング

### v9.9-v9.10 系
- Pulse Model & MAD-DT の数式詳細や cold start 境界条件
- L06 の 4 軸均等化の数値 (v9.9 比較表)
- stability 観測器の癖の |delta|/theta/R 詳細分布
- v99_/v10_/v11_ 列併存の具体的な列構成

### v9.11 系
- B_Gen の Pbirth 式の導出 (組み合わせ確率 + 物理条件)
- v9.11 capture probability の 3 variant (A/B/C) 比較
- 4 層構造の介入規律の詳細 (意識層の哲学的立場含む)
- v9.11 本番 run 結果 (B_Gen 分布、capture rate、L06 解釈)
- Triad (Gemini 設計 → GPT 監査 → Claude 実装) の議論経緯

### v9.12 系
- v9.12 Phase 1 L06 時系列の数値詳細
- v9.12 Phase 2A コード解析の d_* 値域計算
- Taka 発言引用 (並列基準原理、構造と数式、S≥0.20 撤去): `ESDE_Primitive_Report.md` v9.12 追記部分、`概念理解.md` 教訓 66-73
- 未決境界問題 Q1-Q5: `docs/v912_unresolved_boundary_questions.md`

### v9.13 系
- v9.13 本番結果の数値詳細: `primitive/v913/v913_persistence_birth_result.md` (τ=50)、`primitive/v913/v913_tau_comparison.md` (τ=50 vs τ=100)
- v9.13 方向性文書: `primitive/v913/v913_direction_after_step0.md` (Taka 承認済方針)
- v9.13 Step 0 audit: `primitive/v913/v913_persistence_audit_result.md`
- Taka 発言原文 (認知層の方向性、CID の記憶の所在): 上記 `v913_direction_after_step0.md` §3
- 運営原則 v2 撤回、AI 間文書日本語化: 上記 `v913_direction_after_step0.md` §6

### 共通 (Taka 発言引用)
- パスワード、認知原資、桁違い、事象 = 現象そのもの、誤差の埋め合わせ、認知 vs 意識、外部コネクター構想、並列基準原理、構造と数式の分離統合、記憶は物理層の中に既にある、無駄だから切る禁止: `docs/概念理解.md` (v9.13 対応済)
