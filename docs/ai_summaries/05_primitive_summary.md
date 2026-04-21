# Primitive — AI 向け要約 (v9.16 完了版)

*原本*: docs/ESDE_Primitive_Report.md
*要約時点*: v9.16 完了 (2026-04-21)
*対象読者*: 未来の Claude

> **更新履歴**: v9.5 段階で原本記述終了。v9.6-v9.9 (subject reversal、introspection、information pickup、internal axis) は実装コード由来で追記。v9.10 (Pulse Model + MAD-DT)、v9.11 (Cognitive Capture)、v9.12 (Audit Phase)、v9.13 (Persistence-based Birth)、v9.14 (Probabilistic Expenditure Audit)、v9.15 (CID が自分を読む機構)、v9.16 (観察サンプリング機構) を本要約に統合。旧 05b (v9.12 addendum) / 05c (v9.13 addendum) は本ファイルに統合済。

---

## このフェーズが答えた問い

Cognition の「物理層は床」結論を踏まえ、その上に **存在層 + 認知層 (+ 将来の意識層)** をどう構築するか。物理層を一切触らずに、cid (cognitive id) が「世界を見る」「ノードを記憶する」「他者を認識する」「自分を内省する」「自分の固有値を持つ」段階を順に積み上げる。

**v9.11 到達点**: cid は物理層由来の固有値 (B_Gen) と固定記憶ベクトル (M_c) を持ち、周囲の現象 (E_t) との一致率 (Δ) から事象を確率的に捕捉する (capture) ようになった。物理層への介入なしに、cid 単位の認知差が成立。

**v9.12 到達点**: B_Gen + capture 機構の audit で、Δ は i.i.d. (蓄積しない)、軸寄与の偏り (phase+r 72%) は設計寄与ではなく物理的定常性 + 正規化圧縮の帰結、と確定。S≥0.20 hard threshold が「神の手」として撤去対象に浮上。

**v9.13 到達点**: S≥0.20 を撤去し、persistence-based birth (age_r ≥ τ の connected component) に移行。R>0 純度 100% を達成し、v9.11 の主要所見の多くが「経路 B + R=0 混入」のアーティファクトだったことが判明。認知層の方向性として「物理層を支配せず、統計的に多少の差が出る程度」を確定。

**v9.14 到達点**: B_Gen を「計算原資」として運用する paired audit (Layer A = 既存 50 step pulse、Layer B = event 駆動 spend ledger) を実装。Q0 = floor(B_Gen) は long run で意味を持つ量として機能することが確認された。主要発見: **E3 (cid 間接触 onset) が認知活動の 70-90% を占める**、**Layer A と Layer B は異なる情報を取る (Pearson 0.089)**、**E3 を除くと exhaustion 完全消滅 = 認知資源の消費は接触圧が主**。Taka 視点では **E3 = cid 間の 2 者共鳴** と再概念化され、**上位層構築の合理的条件が揃った**ことが v9.14 の真の成果と位置づけられた (三項共鳴そのものの実装は次テーマに棚上げ)。

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

### v9.14 で導入

- **Layer A (Fixed Pulse)**: 既存の 50 step 固定 pulse 系 (v9.11 Cognitive Capture + v9.13 persistence)。**全体スナップショット・均一サンプリング装置**
- **Layer B (Shadow Ledger)**: event 駆動の spend audit ledger。物理現象の変化点で発火する**局所精査装置**。audit-only (Layer A に一切介入しない)
- **Paired Audit**: Layer A と Layer B を並行稼働させる監査方式
- **Q0 (Initial Budget)**: cid 初期原資 = floor(B_Gen)。cid 誕生時に確定、以後減少のみ
- **Q_remaining**: 残存原資。event 発生時に spend packet が実行されると 1 減算
- **Exhaustion**: Q_remaining = 0 到達。以後 event は記録されるが spend packet は走らない (「実質的な死」)
- **E1 (Core Link Death/Birth)**: cid のメンバーリンクが alive_l から消失/復活した step で発火
- **E2 (Core Link R-state Change)**: メンバーリンクの R が 0 境界を跨いだ step で発火 (rise/fall)。core-local のみ、adjacency 拡張は禁止
- **E3 (Familiarity Contact Onset)**: 異なる 2 cid のメンバーノードが同じ alive link で接続された**最初の step** で発火。両 cid が 1 spend ずつ消費 (対称消費、計 2 単位)。contacted_pairs で重複防止
- **Spend Packet**: event 発火時に実行される最小処理単位。E_t 読み出し → 前回スナップショットとの Δ 計算 → virtual_attention / virtual_familiarity 更新 → Q_remaining -= 1 → 記録
- **virtual_attention / virtual_familiarity**: Layer B 専用の内部記録 (Layer A の attention/familiarity と別メモリ)。decay なし、累積のみ
- **shadow pulse**: Layer B 上の pulse 連番 (Layer A の 50 step pulse と独立)
- **Lazy Registration**: cid 登録は observe_step 初回観測時に実施 (Code A 実装判断)
- **cid 間共鳴 (Taka 視点)**: E3 を Aruism 的に再概念化したもの。node 間共鳴 R_ij の cid スケール版。**上位層構築の足場**と位置づけられる (v9.14 Phase 3 議論)

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

## v9.14 Probabilistic Expenditure Audit (2026-04-17〜18)

### このフェーズが答えた問い

v9.11 の B_Gen は cid 固有値として定義されたが、「認知原資」としての具体的な運用が未実装だった。v9.14 は B_Gen を**物理的に消費される予算**として扱う paired audit を実装し、4 つの問い (Q1-Q4) を立てた:

- **Q1**: B_Gen が大きい cid は本当に長く有効観測できるか
- **Q2**: どの event 種が spend に値するか
- **Q3**: spend による internal update は future salience を変えるか
- **Q4**: fixed 50-step pulse と比べて event-spend の方が情報効率が高いか

### 設計 (GPT 代案が採用された経緯)

Gemini 初期設計では「runtime 主体として v9.11 を置き換える」方向だったが、Taka が「v9.14 で統一運用に入るのは早い、B_Gen 資源化は audit として先に走らせる」と横槍。GPT が即座に **Probabilistic Expenditure Audit** 案 (paired audit) を提示し、Taka 承認で確定。

**設計原則**:
- Layer A (50 step 固定 pulse) を**一切触らない** (bit-identity 必須)
- Layer B (event 駆動 spend ledger) を並行稼働させる
- Layer B は audit-only、物理層・存在層・認知層 (Layer A) に介入禁止
- Q0 = floor(B_Gen) を cid の初期原資として確定
- 承認 event 3 種のみ: E1 (core link death/birth) / E2 (core link R-state change) / E3 (familiarity contact onset)

### 実装構成

| 役割 | 担当 | 責務 |
|---|---|---|
| 設計素案 | Gemini | runtime 主体置換 (却下) |
| 設計路線変更 | Taka + GPT | paired audit に方針転換 |
| 実装指示書 | 相談役 Claude | GPT memo を Step 0-9 に分解 |
| 実装 + smoke | Code A | bit-identity 検証、Step ごと合格判定 |
| 監査 (Phase 1) | GPT | implementation PASS / interpretation NOT FINAL |
| Phase 2 分析 | Code A | 6.1-6.4 の計算・run・比較レポート |
| Phase 3 統合 | 相談役 Claude (次) | v9.15 方向性への接続 |

### 本番 Run 構成

| 項目 | Short | Long |
|---|---|---|
| seeds | 48 (parallel -j24) | 5 (parallel -j5) |
| maturation windows | 20 | 20 |
| tracking windows | 10 | 50 |
| window steps | 500 | 500 |
| total cids | 2,979 | 1,112 |
| wall time | 2h43m | 2h32m |

E3 ablation (`--disable-e3`) で同条件の run を追加実施 (Short 2h45m + Long 2h30m)。

### Phase 1 — 実装結果

- bit-identity 全 Step で維持
- Q<0 発生ゼロ、エラーゼロ
- 計算時間 smoke +0.5%、本番 Short +0% / Long +0%
- baseline CSV (per_window / per_subject / pulse_log / per_label) 完全不変
- v10_/v11_/v13_ 列すべて v9.13 smoke と bit-identical
- Layer B は別ディレクトリ `audit/` に 3 種 CSV 出力 (per_event_audit / per_subject_audit / run_level_audit_summary)

GPT 監査判定:
- Implementation status: **PASS**
- Audit architecture compliance: **PASS**
- Baseline preservation: **PASS**
- Interpretation status: **NOT FINAL**

### Phase 2 — 観察事項 (Describe, do not decide)

#### §6.1 Event-type efficiency

Long run の event 種別集計:

| event_type | event_count | spend_rate | delta_mean | attn_delta_mean | fam_delta_mean | exhaustion_contribution |
|---|---|---|---|---|---|---|
| E1_death | 1659 | 0.97 | 0.183 | 19.4 | 1.05 | 0.158 |
| E1_birth | 67 | 0.37 | 0.248 | 47.4 | 0.88 | 0.037 |
| E2_rise | 1296 | 1.00 | 0.033 | 22.2 | 1.45 | 0.137 |
| E2_fall | 1296 | 1.00 | 0.091 | 19.5 | 1.32 | 0.137 |
| E3_contact | 21154 | 0.42 | 0.171 | 25.7 | 1.43 | 0.650 |

- **E3 が全 event の 83%** (short では 66%、long でさらに支配的に)
- **E3 の spend_rate が Long で 0.42 まで低下** — Q 枯渇で出会いの 58% が捕捉見送り
- **E2 rise/fall の非対称性**: rise delta=0.033、fall delta=0.091 (**崩壊の方が情報量 2.8 倍**)
- E1_birth は稀だが情報量最大 (delta=0.248)

#### §6.2 n_core efficiency

Long run の exhaustion 分布:

| n_core | q0_mean | q_spent_mean | exhaustion_ratio | event/q0 比 |
|---|---|---|---|---|
| 2 | 11.55 | 7.71 | 22.09% | 0.76 |
| 3 | 18.28 | 13.65 | 45.61% | 1.45 |
| 4 | 25.79 | 23.67 | **80.00%** | 2.57 |
| 5+ | 33.51 | 31.82 | **84.49%** | 2.66 |

- **Q0 (対数) の伸びより event 数 (線形) の伸びが大きい** → 大きい cid ほど exhaustion 率が高い
- 短 run (5000 step) では exhaustion 2-3% のみ、**v9.14 の主題評価には long run が必須**
- attn_per_spend は n_core で 9.1 → 48.0 (5 倍増)、大きい cid は 1 spend あたり多くのノードを記憶

#### §6.3 Shadow-vs-Fixed overlap

Long run、Layer A pulse と Layer B event の時間的・情報的関係:

| 指標 | 値 |
|---|---|
| exact Jaccard (micro) | 0.003824 |
| ±25 step 近接マッチ率 (A 基準) | 0.199 (ベースライン均一分布期待 0.293 を下回る) |
| only_A_25_share_of_A | 0.801 (A pulse の 80% は B event 不在) |
| only_B_25_share_of_B | 0.253 (B event の 25% は A pulse 不在) |
| exact-match での delta 相関 (Pearson) | 0.089 (**ほぼ無相関**) |
| v11_captured と v14_spend_flag の一致率 | 0.569 |

**解釈 (Taka 判断)**: Layer A は全体スナップショット、Layer B は局所精査。両者は**異なる情報を取る**のが設計上の帰結であり、相関の弱さは問題ではなく証明。

#### §6.4 E3 Ablation Run

`--disable-e3` で E3 を無効化した世界との比較 (Long):

| bucket | exhaustion (base→abl) | q_spent_mean (base→abl) | Q0-q_spent 相関 (base→abl) |
|---|---|---|---|
| 2 | 22.09% → **0%** | 7.71 → 2.59 | — |
| 3 | 45.61% → **0%** | 13.65 → 3.35 | — |
| 4 | 80.00% → **0%** | 23.67 → 7.21 | — |
| 5+ | 84.49% → **0%** | 31.82 → 10.71 | — |
| all | — | — | 0.918 → 0.711 |

**核心発見**:
- **E3 を除くと exhaustion が完全消滅** (Long でも、n=5+ ですら 0%)
- E1+E2 のみでは Q0 の 20-32% しか消費されず、大きい cid でも余裕
- 全体 Q0-q_spent 相関は 0.92 → 0.71 (相関は残るが弱化)
- **cid の認知資源の消費は E3 (接触) が主因**

GPT §7.1 (E3 dominance risk) の懸念は定量的に裏付けられた。ただし Taka 判断: **これは問題ではなく、ESDE が社会的な系であることの証明**。E3 除去が目的ではない。

### Taka 視点の再概念化 — E3 = cid 間共鳴 (2026-04-18)

#### 発言要旨

> これは異なる CID 同士の共鳴と考えてもおかしくはないわけね。それと、CID A と B が共鳴をした場合実質 2 を消費している、と言う理解でいいんかな。

#### 構造的対応

| スケール | 共鳴 | 実装 |
|---|---|---|
| ノード間 | R_ij (閉路参加) | Genesis v0.3 |
| cid 間 (2 者) | E3 contact onset | **v9.14 (新規)** |
| cid 間 (3 者以上) | 三項共鳴 (未実装) | v9.4 戦国大名モデル、v3.4 tripartite loop、v9.15+ 棚上げ |

**E3 = cid スケールでの 2 者共鳴** という再解釈により、ESDE の共鳴階層が初めて cid レベルまで拡張された。

#### 「実質 2 消費」の対称性

E3 発火時、両 cid が独立に 1 spend ずつ消費 (合計 2):

```python
emit_event(cid_a, "E3_contact", other_cid=cid_b)  # cid_a が 1 消費
emit_event(cid_b, "E3_contact", other_cid=cid_a)  # cid_b が 1 消費
```

これは Aruism の**存在の対称性**と整合: 存在 A が存在 B を認識するなら、B も同時に A を認識する。一方向の認識は Aruism に反する。

#### 上位層構築の合理的条件が揃った (Taka 2026-04-18)

> 三項ができたということをきっかけに上位層の 1 を作り出せる。それを存在の対称性で分けて…というアリズム的な円環を構築するための合理的な条件が揃ったと考えれば OK

**v9.14 の真の達成**: B_Gen 資源化 = 手段、E3 = cid 間 2 者共鳴 = 手段、**上位層構築の合理的条件が揃ったこと = 真の達成**。

ESDE 階層進化の系譜:

```
ノード → (リンクで紐づく) → 閉路
閉路 → (共鳴で紐づく) → 持続構造
持続構造 → (phase_sig で紐づく) → label
label → (経験で紐づく) → cid
cid → (E3 で紐づく) → ???   ← v9.15 以降の主題 (ただし当面は棚上げ)
```

Taka 判断: **現在は認知層の開発を進めている状況で、この一段上の接続は「次のテーマ」に収める**。v9.15 は元々の想定通り「記憶の読み出し関数」を進める。

### Phase 2 フレーム外の論点 (Phase 3 以降の宿題)

- **Layer A の再定義 (「パルスとは何か」)**: 観測機械として外部に置くなら残置 OK、内部干渉しているなら外す条件を設ける必要。現状 Layer A は v9.11 Cognitive Capture の延長で cid の attention/familiarity を更新している → 厳密には「観測機械だけ」ではない。v9.15 以降で切り分け
- **seed 構成の一本化**: v9.15 から Short + Long 廃止、**Long 一本化 (24 seeds × tracking 50 × steps 500、parallel -j24、約 2h30m)**。物理コア数 24 に揃える。分散分析は v9.15 から導入
- **Salience loop incompleteness (GPT §7.3)**: Layer B の virtual_attention/familiarity 更新が future event salience を変えるかは未検証。v9.15 以降の主題
- **E3 の設計見直し (保留)**: 現在の E3 は物理接触の初回性のみ。phase 近接、持続、多重接触等での絞り込みは v9.15 以降の候補 (ただし棚上げ)

### 確定した運用ルール (v9.14 追加分)

- **Paired audit の規律**: 新機構は runtime 主体置換ではなく audit-only として先に走らせる。bit-identity 必須、Layer A 完全不変
- **event 定義は narrow 優先**: scope 拡張より scope 維持。core-local、物理事実ベースのみ。想定外の拡張欲求が出たら相談役 Claude に連絡し、GPT 監査を通す
- **調査地獄の回避**: Phase 2 で追加調査 4 項目を設定したら、それ以上は増やさない。コード上の問題が出ない限り再調査しない
- **Describe, do not decide の徹底**: Code A は観察事項のみ記録、結論は相談役 Claude と Taka の Phase 3 議論
- **三項以上の上位層は次テーマ**: v9.14 で条件は揃ったが、実装は v9.15 の認知層継続の後

---

## v9.15 — CID が自分を読む機構 (2026-04-18〜20)

### このフェーズの主題

v9.13 方針 (Taka 2026-04-16):
> CID の記憶は物理層の中に既にある。足りないのは「記憶を作る仕組み」ではなく「物理状態を記憶として読む関数」

v9.14 で寄り道した B_Gen 資源化から、元々の主題に戻った。

### 初期の方向転換 (A vs B)

Claude 初期草案 = A 発想 (研究者が CID の状態を数値化して記録)、R1-R5 の候補を提示。

Taka 指摘 (2026-04-18):
> 記憶を私たちが数字で読むのと、CID が記録してそれを読むの意味がごちゃ混ぜになっている。今あなたが提案しているのは A だと思う。本質は B ではないだろうか?

**A/B 分離**:
- **A (研究者観察)**: Python で state を読み CSV に書く
- **B (CID 主体)**: CID が自分の構造を専用領域に展開し、必要時に自分で読む

v9.15 は B の実装に方向転換。

### 2 AI 回覧で確立した段階 1 の骨格

Gemini + GPT の回答で合意した段階 1 方針:
- **Y**: 構造体の差分のみが CID の知覚 (連続値統計量を持たない)
- **Z**: 「見る」操作は確率的 (段階 1-2 を繋ぐ中核原理、段階 1 では成功確率 1)
- **ζ**: 補完しない (欠損は np.nan のまま)
- **A/B 分離の四重担保**: ファイル / クラス / メモリ / 命名
- **B_Gen / Q 会計からの独立**: Fetch は Q を消費しない

### 段階 1 実装

`CidSelfBuffer` クラスを新設 (B ファイル):
- 生誕時スナップショット (`theta_birth`, `S_birth`, 不変)
- 最新 Fetch スナップショット (`theta_current`, `S_current`)
- 一致/不一致痕跡 (`match_history`)
- divergence 追跡 (A 観測用、`divergence_log`)

Fetch タイミング: 50 step 固定 pulse。Layer A と同期。

Layer A (v9.11 Cognitive Capture) / Layer B (v9.14 Shadow Ledger) は完全不変、bit-identity 必須 (Paired Audit 原則の継承)。

### 段階 1 本番 run (24 seeds × tracking 50 × window 500)

| 指標 | 値 |
|---|---|
| Wall time | 3h04m |
| bit-identity | v9.14 baseline CSV 全 6 本 MD5 完全一致 |
| Fetch 総回数 | 359,110 |
| 決定論性 | 2 回連続 run で MD5 一致 |
| node_match_ratio_mean (全 n_core) | 0.0000 |
| link_match_ratio_mean (全 n_core) | 0.0000 |
| divergence_norm_final (n_core=2) | mean 3.21, max 8.43 |
| divergence_norm_final (n_core=5-7) | mean 5.47, max 10.42 |
| 時間経過の divergence 平均 | 4.32 → 4.85 (25000 step で 12.3% 増、飽和せず) |
| v9.14 E3 spend との相関 | Pearson r = 0.4204 |

**Match Ratio 全 0 問題**: tolerance 1e-6 では連続空間で一致判定が原理的に機能しない。Kuramoto 結合で毎 step θ が動くため、50 step 間隔で必ず tolerance を超える。

### Taka 指摘: 段階 1 はまだ研究者視点 (2026-04-20)

Claude が結果解釈で「CID が変化を知る」と書いたことへの Taka 指摘:

> これも特定ステップごとにやっているなら基本的には研究者視点だと思うよ。CID を主観的に扱いたいのなら、Step 単位での実施は切り捨てた方がいい。なぜなら実験者的だから。

**主観性の最小条件 = タイミングの予測不能性**。50 step 固定は研究者が CID に実験プロトコルを課している状態。段階 1 は機構としては成立したが、主観性の構造としてはまだ不十分。

### 段階 2: event 駆動への切り替え

Taka 解決案:
> イベントがあったぞ → 不一致があるぞ → という具合に Yes/No を進めていく

v9.14 の event 機構 (E1/E2/E3) をそのまま Fetch トリガーとして再利用。新規インフラ不要。

**段階 2 実装方針**:
| 項目 | 判断 |
|---|---|
| Fetch トリガー | 全 event (E1/E2/E3) |
| Fetch コスト | なし (Q 会計から独立、基準値 0) |
| Match Ratio | 廃止 (集約指標は研究者視点、Taka 指摘) |
| 50 step 駆動 | 完全置換 |
| 3 点セット | any_mismatch_ever / mismatch_count_total / last_mismatch_step |
| event 粒度 | E1/E2/E3 の 3 種別 (GPT 監査推奨) |
| `any_mismatch_ever` | 遺伝子情報的な初期値からの変化検出 (Taka 発想) |

**GPT 監査 CONDITIONAL PASS**:
- Match Ratio 廃止は妥当、ただし 3 点セットで最小 richness を維持
- spend → fetch の順序は意味論ではなく依存順序として扱う
- selfhood 表現の抑制 (「証明」ではなく「トリガー根拠の変更」)

### 段階 2 本番 run 結果

| 指標 | 値 |
|---|---|
| Wall time | 3h07m47s |
| bit-identity | v9.14 baseline CSV 全 MD5 一致 |
| Fetch 総数 | 120,782 (event 総数と完全一致、1:1 対応) |
| 段階 1 からの変化 | 約 33.6% (1/3 に減少) |
| event 種別内訳 | E1 6.7% / E2 10.1% / E3 83.2% |
| mismatch 比率 (全 event) | 1.0000 |
| any_mismatch_ever = False の cid | 54/5224 (1.0%、event 発火なし) |
| divergence_norm_final (median) | 3.58 (段階 1: 3.53、ほぼ同じ) |
| Fetch vs Shadow Pulse の相関 | Pearson r = 0.880 (構造的に同じものを測る) |

**event 種別ごとの divergence (median)**:
- E2 (閉路状態変化): 1.59
- E1 (リンク生死): 4.23
- E3 (他者接触): 4.67

### Taka の核心発見: サイコロの比喩 (2026-04-20)

> ランダムに紐づけることで研究者の主観を実質封じるという一手に辿り着いた。研究者はサイコロの目が 1/6 であることを言えるが、次の目が 1、だとは言えない。しかし、1 になったサイコロ自身は (仮にそこに 1 を 1 として認識できる機能があれば) 自身を 1 だ、と主張できる。この発見は、今後の意識に向かう発展として極めて重要な意味を持つことになるだろう。

**非対称性**:
- 研究者は統計的にしか語れない (「次の目が 1/6」)
- サイコロ自身は具体的に語れる (「私は 1」)
- 同じ現象について両者はまったく違うレベルで記述する

**ESDE 段階 2 との対応**:
- 研究者: 「event が確率的に発生する、頻度分布はこうだ」
- CID: 「今、event が起きた、自分を読んだ、不一致を持った」
- 研究者は「いつ CID が自分を読むか」を予測できない

これが「**研究者主観の封印**」の具体的意味。v9.15 の真の成果。

### 戦略の言語化: 哲学以上科学未満 (Taka 2026-04-20)

> つまるところ、○○かもしれない、と言った時、それは○○かもしれない、○×かもしれない、××かもしれないだろう。極端な話をすれば言ったもの勝ち。これが制約。その制約を最大限利用しているのが私たちのシステムにおける「自己のようなもの」。これを否定するためにはランダム性を全て削ぎ落として完全な予測を完成させなければならない。

**弱点の告白**:
> 私たちにはとても弱い実験的条件がある。それは、私たちがやろうと思えば内部を覗けること。そのため、ランダム性を担保にしなければ私たちの主張は崩れてしまう。奇妙なバランスの上に私たちの主張が存在するということ。

**結論**:
- 研究者が覗けることは事実 (A/B 分離しても原理的には可能)
- しかし予測不能性がある限り「覗いても先はわからない」
- この微妙な位置で「自己のようなもの」を主張できる
- **ランダム性が論理の支柱。削る方向は採らない**

### Taka 視点の解釈 (2026-04-20)

**A.1 / A.2 (event 種別の比率比較)**:
発生頻度の違う event 間で比率や数値を比較しても構造的情報は出ない。まぁそうなんだ、くらいの驚き。

**A.3 (何も起きない CID が 1%)**:
5000 ノード / 71x71 グリッドではこういう結果になった、くらいで OK。実験条件から切り離して普遍化しない。

**A.4 (段階 1 と段階 2 で divergence 一致)**:
> システムが安定している証拠。5000 ノードを連続で撃ち続ける、という前提がまさにそれを可能にしたと推測。

ただし「安定している」は推測、検証未了。検証するならノード数を変える。

### 意識への発展の筋道 (Taka 2026-04-20)

> 自分について語る、という状況が機械的になってしまうとそれは自己とは呼べない。ランダム性が担保されていれば呼べなくもないかもしれない。あとは、それっぽさが大事 (LLM 的に会話っぽいものが成立するとかどうとか) で、そこまでの進化が必要となる。

**筋道**:
- 段階 1: CID が自分を読む機構 (タイミング外部指定)
- 段階 2: タイミング物理事象依存 (研究者支配を離れる)
- **段階 3: 自己読みの確率的失敗 (予測不能性の内部化) — v9.16 予定**
- さらに先: ランダム性を担保した「自分について語る」機構
- そのさらに先: 「それっぽさ」としての会話成立 (市場承認)

**境界線**: 機械的な自己主張は自己ではない。ランダム性を伴って初めて自己の候補になる。

### 宿題: ノード数固定の神の手性 (Taka 2026-04-20)

> 1 ステップが 5000 で固定である理由がない。物理量に相当するものは一定である必要性はない。

ただし今の議題としては弱い。物理はクローズした、からこそ現状の進化がある。**ノード数変動は大幅後回し**、認知層十分発展後の検討事項。

### Claude が繰り返した失敗

1. A vs B の混同 (草案段階) — Taka 指摘で根本転換
2. tolerance の先送り (実装段階) — Match Ratio ゼロ張り付き
3. 結果解釈の研究者視点偏重 — CID 視点を見落とした
4. 「知る」の強度誤り — GPT 監査で「不一致を持つ」止まりへ抑制
5. 段階 1 タイミングの研究者指定性を見落とし — Taka 指摘
6. E3 ドミナンスや E2/E3 質的差へのストーリー盛り — Taka 抑制

**共通パターン**: 研究者視点 → CID 視点の切り替えができていない、意味を盛りすぎる。

Taka の現実的対処:
> 反省は繰り返しても改善しない。だから GPT 使ってる。

3 役分離 (Gemini 加速 / GPT 制動 / Claude 整理) で Claude の癖を相対化する運用。

### v9.15 の位置づけ

v9.14 = cid 間接続 (横方向の上位化)
v9.15 = cid 内部参照 (縦方向の自己化)

真の成果は機構の実装ではなく、**研究者の主観を封じる戦略の確立**。ESDE の意識研究の戦略的転換点。

### 確定した運用ルール (v9.15)

- A/B 分離の四重担保 (ファイル / クラス / メモリ / 命名)
- 研究者向け統計量を CID 内部に持たせない
- Describe, do not decide の徹底強化
- CID 視点と研究者視点の並列記述
- ランダム性を削る方向は採らない
- 「自己」「意識」の語を結果レポートで断定的に使わない

---

## v9.16 — 観察サンプリング機構 (2026-04-21)

### 主題

v9.15 段階 2 で「Fetch のタイミング」が物理事象駆動になり予測不能化した。v9.16 段階 3 では「Fetch で何が見えるか」も時間的に変化させる。

**v9.16 = 段階 3 (観察サンプリング)**:
- Fetch 自体は常に成功 (段階 2 から継承)
- 判定対象のノード数が `age_factor = Q_remaining / Q0` に比例
- 観察されなかったノードは missing として扱う (ζ 継承、補完しない)

### Claude 先走りと Taka 軌道修正

v9.15 Phase 3 で Claude が記録した「v9.16 = Fetch の確率的失敗」は詰まっていない言葉。Taka 問い直し (2026-04-21):
> 冷静に考えると Fetch の確率的失敗ってどういう意味?

Taka 規律 4 は「差分情報を確率的に**消費**する」= 選択的認識であって「失敗」ではない。Claude の表現は規律から外れていた。

### Taka 再整理 (2026-04-21)

> 今のところ差分情報を予測する機能がないので、自分と同一かを判定する。手っ取り早いのは B_Gen。一致率を見る。まだ見た上で何をするかは考えない。

- 差分の内容は予測しない
- 同一判定のみ
- 判定基準に B_Gen または Q_remaining を使う
- 判定結果に基づく CID 行動変化はなし

### 人間比喩による 2 段階認識

Taka:
> 構造の違い (何者か) = B_Gen (人間 vs カエル)
> 時間的違い (何歳か) = Q_remaining (若者 vs 老人)

自己読みの文脈では B_Gen は不変、Q_remaining のみが動く。

### 2 AI 統合回答 (Gemini + GPT、2026-04-21)

両 AI が強く一致した 4 点:

1. **主題**: 「判定条件の時間変化」に絞る (採用)
2. **実装方式**: サンプリング方式 (案 1、tolerance 可変と確率判定は却下)
3. **Q 消費**: 現状維持 (判定では追加消費しない)
4. **語の強度**: 抑制 ("自己性の成立"、"老成" 等を避ける、"一致/不一致の判定"、"時間的認識条件" を使う)

### GPT §12 先走り防止チェックポイント

同じ失敗を繰り返さないため:
1. バージョン名を決めた時点で入出力を一文で言えるか
2. 「失敗」「認識」「自己」等の語を物理操作へ還元できるか
3. 観察と行動を混ぜていないか

指示書 §0.2 で一文定義を明記:
> v9.16 は、cid が event 発火時に物理状態と生誕時スナップショットを比較する際、メンバーノードのうち age_factor = Q_remaining / Q0 に比例した数を確率的に選んで判定し、選ばれなかったノードは欠損として扱うフェーズである。

### 実装の骨格

```python
# event 発火時 (Layer B spend_packet 実行後)
age_factor = Q_remaining / Q0  # [0, 1]
n_observed = int(round(n_core * age_factor))

# hash ベース独自 RNG (engine.rng 非 touch)
local_rng = build_local_rng(seed, cid_id, step, event_type_full)
observed_indices = local_rng.sample(range(n_core), n_observed)

# 観察ノードのみ判定、残りは missing
for i in range(n_core):
    if i in observed_indices:
        node_status[i] = 'match' if within_tolerance else 'mismatch'
    else:
        node_status[i] = 'missing'
        missing_flags[i] = True  # 段階 1 の器がここで意味を持つ
```

### 実装結果 (24 seeds × tracking 50)

**bit-identity**:
- v9.14 baseline CSV 6 本: MD5 完全一致
- Fetch 総数 120,782: 段階 2 と完全一致 (seed 単位でも)
- theta_diff_norm_all: 段階 2 の theta_diff_norm と max 差 0.0

**主要統計**:

| 指標 | 値 |
|---|---|
| Wall time | 3h07m (段階 2 と同等) |
| node-cell match 比率 | 0.00 % |
| node-cell mismatch 比率 | 23.22 % |
| node-cell missing 比率 | 76.78 % |
| Q 枯渇 cid (age_factor_final = 0) | 1,771 / 5,170 = 34.26 % |
| seed 間 CV (avg_age_factor) | 2.96 % |

**age_factor 区間別の missing 比率** (代数的必然):

| 区間 | missing 比率 |
|---|---|
| [0.0, 0.2) | 99.27 % |
| [0.2, 0.4) | 67.80 % |
| [0.4, 0.6) | 50.17 % |
| [0.6, 0.8) | 32.56 % |
| [0.8, 1.0) | 6.37 % |

`n_observed = round(n_core × age_factor)` からの代数的帰結。「観察」ではなく「設計が意図通り機能した確認」。

**event 種別別の age_factor median**:

| event | age_factor median |
|---|---|
| E1 | 0.58 |
| E2 | 0.73 (若いうちに発生) |
| E3 | 0.00 (Q 枯渇後に発生) |

段階 2 の E2/E3 質的差 (theta_diff_norm median 1.59 vs 4.67) と整合。

**n_core 別 age_factor median**:

| n_core | age_factor median |
|---|---|
| 2 | 0.55 |
| 3 | 0.11 |
| 4-8 | 0.00 |

Code A 物理説明: n_core 小 → member link 数少ない (C(n,2)=1) → E1/E2 発火頻度低 → Q 消費遅い。

### Taka 追加論点 (2026-04-21)

**説明可能性の時間的構造**:

過去は時間経過で広がる = 説明可能性の減衰。現在 (説明可能性最大) → 過去 (あったであろう) / 未来 (あるであろう) の 2 方向構造。v9.16 段階 3 で「過去の説明可能性」の実装に相当。未来の実装候補は段階 5 以降。

**説明可能性は not decide, but describe と同格の原則** (Taka 2026-04-21 指定、3 AI 共通運用)。

**動的均衡の違和感**:

認知量消費 -1 固定の課題。ただし現在は認知層主題、物理スケール変動時に再検討 (大幅後回し)。

### Constitution (2026-03-05) との接続

Taka が既に明文化していた憲法 (2026-03-05):
- §2 Core Objective: 動的均衡下での Explainability X の最大化
- §3 Explainability: 短い記述、時間的安定性、再現可能な構造
- §5 Anti-Drift: 測定可能性に紐づかない主張は design decision に使わない
- §7 Governance: Observation → Bottleneck → Minimal Change → Re-observation
- §9 Success Definition: 安定した実験ループの存在

v9.16 指示書 §14 で各章との整合を明示。**v9.15-16 の議論は新規原則ではなく憲法の具体化**。

### 主張の構造 (v9.15-16 統合)

| 要素 | 内容 |
|---|---|
| 弱点 | 研究者は原理的に CID の内部を覗ける |
| 防御 1 (v9.15 段階 2) | タイミング予測不能 |
| 防御 2 (v9.16 段階 3) | 見える範囲も予測不能 (時間依存) |
| 論拠 | 反証困難性 (Taka 戦略) |
| 結論 | 「自己のようなもの」は哲学以上科学未満で成立 |

### 確定した運用ルール (v9.16 追加)

- **一文定義を草案・指示書に含める** (先走り防止、GPT §12)
- **サンプリング方式のみ採用** (tolerance 可変・確率判定は却下)
- **B_Gen は自己読みで間接使用** (age_factor 経由)
- **観察結果と代数的必然を混同しない**
- **説明可能性を Describe 原則と同格に扱う**

### v9.16 の位置づけ

v9.14 = cid 間接続 (横方向の上位化)
v9.15 段階 1 = 自己読みの器
v9.15 段階 2 = タイミング予測不能
**v9.16 段階 3 = 見える範囲の時間的変化** (自己化に時間軸を追加)

### 次フェーズへの橋渡し

v9.16 完了時点の候補:
- **段階 4 = 他者読み**: 他 cid の情報を取り込む (v9.14 E3 延長)
- **段階 5 = 差分の意味の予測**: Taka 規律 4 の次、「未来」の実装
- **長期記憶強化**: Taka 規律 5 (v9.16 までは毎 event 独立判定)
- **元々の v9.15 テーマ**: R1-R5、自己読みの内容多様化
- **Layer A 再定義**: Taka 2026-04-18 宿題

Taka 判断待ち。Claude 仮推奨は段階 4 (他者読み)。

### v9.16 教訓

1. **「Fetch の確率的失敗」のような詰まっていない言葉を前提として使わない** (v9.15 Phase 3 から v9.16 着手までの Claude 先走り)
2. **バージョン名決定時に入出力を一文で言えるか詰める** (GPT §12)
3. **Taka 規律 4 は「失敗」ではなく「選択的認識」**
4. **B_Gen/Q は確率論的に導出された値、判定基準に使うのは神の手ではない** (Taka 自答)
5. **age_factor 区間と missing 比率の関係は「代数的必然」**、観察事実と混同しない
6. **説明可能性は Describe 原則と同格** (Taka 2026-04-21)
7. **Constitution (2026-03-05) は既に明文化済み**、v9.15-16 は具体化にすぎない
8. **動的均衡は物理スケール変動時に重要、現在は後回し**

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
| 段階 1 の 50 step 駆動 Fetch (`read_own_state`) | 段階 2 では呼ばれない、コードは残置 | **休眠保持**。将来の Paired Audit で復活させる可能性 |

### 無効化済 (放置 OK)

| 機能 | 状態 |
|---|---|
| Stress decay | stress_enabled=False |
| Macro-node compression | compressed_nodes チェック残存、機能 OFF |
| Vacancy birth filter | 撤回済 |
| torque_factor (認知→存在介入) | =1.0 で不活性、v9.7 の遺物 |
| S≥0.20 hard threshold | v9.13 で撤去 |
| 経路 B (R>0 ペア即 label) | v9.13 で廃止 |
| Match Ratio 集約 (v9.15 段階 1) | 段階 2 で廃止、個別フラグのみ保持 |

---

## 開発ロードマップ (v9.16 完了時点)

| Phase | バージョン | 内容 | 状態 |
|---|---|---|---|
| 掃除 | v9.13 | S≥0.20 撤去、persistence-based birth | **完了** |
| B_Gen 資源化 + 上位層の足場 | v9.14 | Probabilistic Expenditure Audit、E3 = cid 間共鳴の確立 | **完了** |
| 記憶の読み出し | v9.15 | CID が自分を読む機構、段階 1 (Fetch 確立) + 段階 2 (event 駆動) | **完了** |
| 自己読みの予測不能性内部化 | v9.16 | 段階 3 = 観察サンプリング機構 (age_factor 比例) | **完了** |
| 他者読み / 差分予測 / 長期記憶 | v9.17+ | 段階 4 他者読み、段階 5 差分予測、Taka 規律 5 長期記憶 | **次、候補複数** |
| 記憶の蓄積と再生 | v10.x | pickup 活用、他者の経験取り込み、長期記憶強化 | 構想 |
| 三項以上の上位層 | v10.x 以降 | v9.14 で条件成立、認知層継続を優先 | 棚上げ |
| 意識層 | v10.x 以降 | 認知層の解釈を検証 | 構想 |
| 外部コネクター + 「それっぽさ」 | v11.x 以降 | 外部情報注入、LLM 的会話成立 (市場承認) | 構想 |
| 物理層変動化 | 未定 | ノード数固定を解除 (認知層十分発展後) | 宿題、大幅後回し |

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
- **新機構は audit として先行** (v9.14): runtime 主体置換の衝動を抑え、paired audit で並行走行から始める
- **E3 は cid 間共鳴として解釈** (v9.14): 2 cid の対称消費 (計 2 単位) は Aruism の存在の対称性と整合
- **三項以上の上位層は棚上げ** (v9.14): 条件は揃ったが、認知層継続を優先。v9.15 は元々の想定通り記憶の読み出し関数へ

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
10. **Layer A (50 step 固定 pulse) を触らない** (v9.14) — Layer B を導入する場合でも bit-identity 必須。baseline CSV は v9.13 smoke と bit-identical であることを毎 Step 確認
11. **新機構を runtime 主体置換として導入しない** (v9.14) — paired audit として並行走行から始める。promotion 判断は analysis 結果が揃ってから
12. **E3 (contact) を安易に拡張しない** (v9.14) — 物理接触の初回性のみを原則とする。phase 近接、持続、多重接触等での絞り込みは想定外の提案として相談役 Claude に確認
13. **三項共鳴実装に先走らない** (v9.14) — E3 で条件は揃ったが、認知層継続 (記憶の読み出し) を優先
14. **A (研究者観察) と B (CID 主体) を混同しない** (v9.15) — 研究者向け統計量を CID 内部に持たせない。四重分離 (ファイル / クラス / メモリ / 命名) で担保
15. **Step 単位固定 Fetch を主体的機構として扱わない** (v9.15 段階 1 の教訓) — タイミングが研究者指定の段階では主観性は成立していない
16. **「自己」「意識」を結果レポートで断定的に使わない** (v9.15) — Describe の徹底、GPT 監査指摘
17. **ランダム性を削る方向に設計しない** (v9.15) — 論理の支柱を守る、予測不能性を担保にした主張
18. **集約指標 (Match Ratio 等) を CID 視点での意味を詰めずに追加しない** (v9.15) — 「何のために取るか」を明示、研究者視点専用なら CID 内部には持たせない

---

## 教訓 (v9.13 までの追加分、親ファイル 66-73 の続き)

74. **shadow 推定と本番の差は window 数で説明可能なことが多い** — Step 0 shadow 25/20win の予測は本番 43/40win とほぼ整合 (換算 21.5/20win)。「予測外れ」と即断せず換算を確認
75. **n_core 分布のアーティファクト依存度は高い** — v9.11 の「phase+r 72% 支配」などの主要所見が birth 方式変更で崩れた。同種の所見を再確認する際は下地の n_core 分布を必ず見る
76. **閾値厳しくすれば大型が増える、とは限らない** — τ=100 で n=5 比率が低下、n=2 が増加。persistence 要件は 2 ノードの方が満たしやすい可能性
77. **Taka の「思ったより良い」は文脈を確認する** — 成果の大きさではなく、「減りすぎなくて認知層テストが継続できる」という実務的安心だった。Claude の過大解釈を防ぐため文脈確認が必要
78. **短 run では見えない現象がある** (v9.14) — 5000 step の exhaustion 2-3% に対し 25000 step では 22-84%。時間スケールで質的に違う景色が現れる主題がある (cid 寿命・資源消費系)
79. **並列度は物理コア数に揃える** (v9.14) — 48 threads (HT) で並列化しても効率は上がらない。24 seeds × -j24 が Ryzen 24C では最速
80. **seed 数 24 → 48 の統計力向上は √2 倍のみ** (v9.14) — 費用対効果悪し、24 で十分
81. **Layer A と Layer B は異なる情報を取る** (v9.14) — Pearson 相関 0.089 は「全体スナップショットと局所精査は別の情報を見る」という設計的帰結
82. **E3 dominance は系の社会性の証明** (v9.14) — 認知活動の 70-90% が接触 event。問題ではなく観察
83. **E2 rise/fall は情報量が非対称** (v9.14) — fall の方が 2.8 倍、共鳴崩壊の瞬間は情報量大
84. **実装の時間見積もりで並列度を混同しない** (v9.14)
85. **Taka 指摘は設計レベルで受け取る** (v9.14) — 運用提案ではなく構造的指摘
86. **E3 = cid 間共鳴という再概念化は上位層の足場** (v9.14) — 実装は棚上げ、認知層継続が優先
87. **三項共鳴実装の衝動は抑える** (v9.14)
88. **A vs B の混同は実装の根本を誤らせる** (v9.15) — Claude が A 発想で草案を書いた時点で、B 実装には辿り着けなかった。Taka 指摘で根本転換された
89. **tolerance の意味を実装前に詰める** (v9.15) — 1e-6 を「後で調整」と先送りした結果、Match Ratio 全 0 張り付きで段階 1 では機能しなかった
90. **連続値空間で離散一致判定は原理的に機能しない** (v9.15) — 連続量 (divergence) の方が情報量が多い
91. **Step 単位固定実施は研究者視点** (Taka 2026-04-20) — 主観性の最小条件はタイミングの予測不能性
92. **集約指標は CID 視点での意味を設計時に詰める** (v9.15) — Match Ratio は「何のためか」が後から Taka に問われて廃止された
93. **発生頻度の違う event 間で比率や数値を比較しても構造的情報は出ない** (v9.15) — 「E3 が 83%」は E3 の発生頻度が高いことの再確認にすぎない
94. **観察結果を条件から切り離して普遍化しない** (v9.15) — 「活発な系」ではなく「5000 ノード 71x71 ではこうなった」
95. **推測を結論と書かない** (v9.15) — 「系が安定」は推測、検証方法 (ノード数を変える) を明示
96. **ランダム性が論理の支柱** (Taka 核心発見 2026-04-20) — 削る方向は採らない、予測不能性を担保にした主体性主張の戦略
97. **機械的な「自分について語る」は自己ではない** (Taka 2026-04-20) — ランダム性を担保した主張のみ自己の候補
98. **GPT 監査の「観察層の薄さ」指摘は妥当** (v9.15) — Match Ratio 廃止後も最小 3 点セットで richness を維持
99. **Claude の癖 (整理過剰、意味を盛る、研究者視点偏重) は消えない** (Taka 2026-04-20) — 3 役分離で相対化する運用、反省より運用切り替え
100. **CID 視点と研究者視点の並列記述は v9.15 の中核規律** (v9.15) — 両視点を分離して文書化する
101. **ノード数固定は実験制御であって神の手ではない** (Taka 2026-04-20) — 物理層クローズだからこそ認知層の発展が追跡できる、ノード数変動は認知層十分発展後

---

## 次フェーズへの橋渡し

v9.15 完了時点で v9.16 以降の優先課題:

### 優先度 1 (v9.16 の主題)

1. **段階 3 = 自己読みの確率的失敗の導入** — タイミングの予測不能性 (段階 2) に加え、結果の予測不能性を導入。ランダム性が論理の支柱を守る原則の実装。v9.15 の `CidSelfBuffer.read_on_event` に確率的失敗ポイントを差し込む設計を段階 1 から準備済み

### 優先度 2 (v9.16 Phase 3 以降の宿題)

3. **Layer A の再定義**: 「パルスとは何か」の切り分け。観測機械として外部に置くなら OK、内部干渉しているなら外す条件を設ける
4. **stability 観測器の癖修正**: v9.10 から継承、未解決
5. **Salience loop incompleteness の検証**: Layer B virtual_* 更新が future salience を変えるか (GPT §7.3)

### 優先度 3 (v10.x)

6. **記憶の蓄積と再生**: CID が過去の経験を次の判断に使う。pickup の空箱 (死亡情報プール) を活用
7. **三項以上の上位層**: v9.14 で条件は揃った。cid 間共鳴 (E3) の上位、3 cid 間の tripartite resonance。ただし v3.4 と同じ持続性の壁が予想される
8. **意識層の実装**: 認知層の解釈を非介入で検証

### 優先度 4 (v10.x 〜 v11.x)

9. **「事象」の定義の精緻化**: E_t の構成は十分か
10. **複数 cid 間の interaction 本格実装**: 戦国大名モデル、コミュニティ
11. **n=6-9 が出ない問題の調査**: 50% overlap フィルタと非空間リンク形成が残存要因

### 優先度 5 (v11.x 以降)

12. **外部コネクター**: 物理現象として注入、frozenset として消えていく

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

### v9.14 系
- v9.14 指示書: `primitive/v914/v914_implementation_instruction.md`
- v9.14 Code A 実装ノート: `primitive/v914/v914_implementation_notes.md`
- GPT 設計原案: `v9_14_probabilistic_expenditure_audit_memo_jp.txt`
- GPT 監査レポート: `ESDE_v9_14_GPT_Audit_Report_EN.txt`
- Phase 1 audit 結果: `primitive/v914/v914_audit_result_milestone1.md`
- Phase 2 依頼書: `primitive/v914/v914_phase2_instruction.md`
- Phase 2 §6.1 Event-type efficiency: `primitive/v914/v914_event_type_efficiency.md`
- Phase 2 §6.2 n_core efficiency: `primitive/v914/v914_ncore_efficiency.md`
- Phase 2 §6.3 Shadow overlap: `primitive/v914/v914_shadow_overlap.md`
- Phase 2 §6.4 E3 ablation: `primitive/v914/v914_e3_ablation_result.md`
- Taka 発言原文 (E3 = cid 間共鳴、実質 2 消費、上位層の足場): 上記 Phase 2-3 議論記録 (`concept_core.md` v9.14 追記も参照)

### v9.15 (CID が自分を読む機構)
- 段階 1 メイン: `primitive/v915/v915_memory_readout.py`
- 段階 1 CidSelfBuffer (B): `primitive/v915/v915_cid_self_buffer.py`
- 段階 1 Fetch 関連 (B): `primitive/v915/v915_fetch_operations.py`
- 段階 1 観察ツール (A): `primitive/v915/v915_a_observer.py`
- 段階 1 divergence tracker (A): `primitive/v915/v915_divergence_tracker.py`
- 段階 1 単体テスト: `primitive/v915/test_v915_cid_self_buffer.py` (14 ケース)
- 段階 1 草案: `v915_段階1_実装草案.md`
- 段階 1 Code A 指示書: `v915_実装指示書_CodeA向け.md`
- 段階 1 結果レポート: `primitive/v915/v915_stage1_result.md`
- 段階 1 Phase 1 総括: `v915_phase1_summary.md`
- 段階 2 メイン: `primitive/v915s2/v915s2_memory_readout.py`
- 段階 2 CidSelfBuffer (B): `primitive/v915s2/v915s2_cid_self_buffer.py` (`read_on_event` 追加)
- 段階 2 草案: `v915_stage2_claude_draft.md`
- 段階 2 Code A 指示書: `v915_stage2_implementation_for_codeA.md`
- 段階 2 結果レポート: `primitive/v915s2/v915s2_stage2_result.md`
- 2 AI 回覧 (論点整理): `v915_論点整理_2AI回覧用.md`
- 2 AI 統合回答: `v915_GPT_Gemini統合回答_整理版.md`
- GPT 段階 2 監査: `ESDE v9.15 Phase 2 — GPT Audit Memo for Claude` (2026-04-20)
- Taka 核心発言 (サイコロの比喩、哲学以上科学未満、ランダム性が論理の支柱): 上記 Phase 3 議論、`概念理解.md` v9.15 セクション参照

### v9.16 (観察サンプリング機構)
- メイン: `primitive/v916/v916_memory_readout.py`
- CidSelfBuffer (B): `primitive/v916/v916_cid_self_buffer.py` (age_factor / n_observed / missing_flags、3 値 status)
- Fetch 関連 (B): `primitive/v916/v916_fetch_operations.py`
- 観察ツール (A): `primitive/v916/v916_a_observer.py` (observation_log 出力)
- divergence tracker (A): `primitive/v916/v916_divergence_tracker.py`
- 単体テスト: `primitive/v916/test_v916_cid_self_buffer.py` (50 tests)
- v916 草案: `v916_stage3_claude_draft.md`
- v916 Code A 指示書: `v916_implementation_for_codeA.md`
- 2 AI 論点整理: `v916_論点整理_2AI回覧用.md`
- 2 AI 統合回答: `ESDE v9.16 段階 3 論点整理 — GPT / Gemini 統合回答` (2026-04-21)
- 本番 run 結果レポート: `primitive/v916/v916_stage3_result.md`
- Constitution (2026-03-05): `ESDE_explainability_constitution.txt` (英語原文、日本語化は今後検討)
- Taka 核心発言 (人間比喩 B_Gen/Q、説明可能性、動的均衡): 上記 v9.16 議論、`概念理解.md` v9.16 セクション参照

### 共通 (Taka 発言引用)
- パスワード、認知原資、桁違い、事象 = 現象そのもの、誤差の埋め合わせ、認知 vs 意識、外部コネクター構想、並列基準原理、構造と数式の分離統合、記憶は物理層の中に既にある、無駄だから切る禁止、A vs B 分離、サイコロの比喩、ランダム性が論理の支柱、説明可能性の時間的構造: `docs/概念理解.md` (v9.16 対応済)
