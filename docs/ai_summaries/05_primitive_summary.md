# Primitive — AI 向け要約

*原本*: docs/ESDE_Primitive_Report.md (746 行)
*要約時点*: v9.9 完了前 (2026-04-11)
*対象読者*: 未来の Claude

> **注**: 原本は v9.5 段階で記述終了。v9.6-v9.9 (subject reversal、introspection、information pickup、internal axis) は本要約で別途追記している (実装コード由来)。

---

## このフェーズが答えた問い

Cognition の「物理層は床」結論を踏まえ、その上に **存在層 + 認知層** をどう構築するか。物理層を一切触らずに、cid (cognitive id) が「世界を見る」「ノードを記憶する」「他者を認識する」「自分を内省する」段階を順に積み上げる。

---

## 用語

- **label**: frozenset 固定の魂 (Autonomy 由来)、解放しない
- **cid (cognitive id)**: v9.8a で導入された **観察主体**。label とは独立した識別子。同じ label でも host を失えば cid は ghost 化、TTL 経過で reaped
- **disposition**: cid のキャラクター 4 軸 (social, stability, spread, familiarity)
- **phase_sig**: label の思想、birth 時の平均 θ で固定
- **φ (認知位相)**: label が structural world に追従する角度 (Phase 1)
- **attention map**: ノード ID → 出現頻度。接触記憶。decay_rate=0.99
- **partner familiarity**: 他 label ID → 接触頻度。decay_rate=0.998
- **ghost / hosted / reaped**: cid の状態遷移 (v9.8a)
- **introspection tag**: gain_xxx / loss_xxx (v9.8b)
- **TTL bonus / death pool / pickup**: 死亡 label の情報プール拾得 (v9.8c)

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

## v9.5 — 3 層構造の確立

| 層 | 比喩 | 性質 | 動き |
|---|---|---|---|
| 物理層 | 波 | θ/S/リンク | 常に |
| 存在層 | 粒子 | frozenset + phase_sig | 固定 (魂) |
| 認知層 | 過程 | 波と粒子の間のパターン | 動的 |

**Phase 1 — 認知位相 φ**: α × sin(mean_theta_structural - φ)。全 label DETACHED (α≈0.097 で過追従)

**Phase 1.5 — 対称分析**: convergence moments で near_phase 34% (divergence は 18%)

**Phase 2 — Attention Map** (完了):
- structural set 内ノードを毎 step +1、全体 ×0.99 で減衰 (半減期 69 step)
- L101: entropy 低下 0.72 (小さな世界で集中記憶)
- Label 間 hotspot 共有: L3↔L76 で 268 ノード (共有経験の原型)

**Phase 3 — Partner Familiarity** (v9.5 時点で実行待ち、v9.6+ で実装): {other_label_id: float}。decay=0.998 (半減期 346 step)

---

## v9.6-v9.7 — 却下された方針

(原本未記述、コード履歴より):
- **v9.7 population 統計フィードバック** → 集団統計を主体に直接読ませる方向は cid 概念の純粋性を損なうため後退
- **disposition の閾値ベース介入** → torque/action への反映は Gemini freeze ruling で禁則化

---

## v9.8a Subject Reversal (cid の確立)

- **主体反転**: ラベル中心 → cid (cognitive id) 中心へ
- ghost 状態の導入: host (label) を失った cid は ghost 化、GHOST_TTL 経過で reaped
- cid は label とは別の識別子。同じ frozenset でも複数の cid が割り当てられうる
- 「魂は frozenset で固定、cid は経験で異なる」

## v9.8b Minimal Introspection

- **disposition 4 軸**: social, stability, spread, familiarity
- **gain_xxx / loss_xxx tag** の生成 (Stage 1、固定閾値)
- 閾値: `INTROSPECTION_THRESHOLD_SOCIAL/STABILITY/SPREAD = 0.1`、`FAMILIARITY = 2.0`
- **観察専用** (Gemini freeze ruling): torque/action に一切反映しない
- ghost は無視 (is_hosted ガード)、初回 window (prev=None) は早期 return

## v9.8c Information Pickup

- 死亡ラベルの「情報プール」: dead_lid と所属 cid 群
- **phase 距離による排他的競争**: hosted cid が phase 距離で picker を決定
- **効果は TTL 延長のみ** (`cid_ttl_bonus`)、物理層・vl・engine 不変
- GPT 監査条件遵守
- per_subject CSV: ttl_bonus, n_pickups_won/lost, effective_ttl

## v9.9 内的基準軸 (現在実装中、Long Run 進行中)

- **recent_tags**: deque(maxlen=5)、frozenset(tags) を append
- **recent_dispositions**: deque(maxlen=5)、4 軸 dict を append
- **Rule 1** (n<3): unformed
- **Rule 2** (lowest_std_axis): personal_range の 4 軸 std が最小の軸、EPS=1e-9 で tie 判定
- **Rule 3** (dominant +/- drift): drift カウント最大の軸、整数厳密一致、最大値=0 なら "none"、複数同率なら "tie"
- **drift 累積禁止**: 毎回 recent_tags からゼロ再構築
- per_subject CSV に **v99_ prefix 33 列追加**
- physics/vl/pickup ロジック完全不変、smoke で per_window CSV bit identical 確認済

---

## 確定した運用ルール

- **物理層への非介入**: 認知層は存在層に影響しない、torque は微小、支配的ではない
- **観察は cid の中で完結**: state.theta / S / R は一切変更しない
- **逐次化が最小変更で最大効果**: 計算式同じ、適用順序のみで NET 大幅改善
- **Age 順は自然な秩序**: 古い label が θ の地盤を整える
- **Frozenset は解放しない**: 魂は固定、動きは認知層内部状態から
- **同じ frozenset から異なるキャラが立ち上がる**: 経験差異が性格を生む
- **一次出力は構造語のみ** (v9.9): "formed"/"unformed"/"tie"/"none" — 数値解釈は analyzer 段階
- **cid は履歴を読まない、書き込みのみ** (v9.9): loop は閉じない、観察主体に徹する

---

## 次フェーズへの橋渡し

v9.9 完了後の v9.10+ で問われる:
- cid に「内的基準軸を読ませる」べきか (現状は書き込みのみ)
- 複数 cid 間の interaction (現状は孤立観察)
- v9.4 の戦国大名モデル (統率力 / 影響圏 / 三項創発) の実装可否
- spatial vs structural perception の認知層への組み込み

最終目標: 「神の手なしに認知・意味・社会性が創発するモデル」、当面のゴールは「会話できるシステム」。

---

## 原本を読むべきタイミング

- Torque/gravity の「二面性」「同時性攪乱」の発見プロセス詳細
- Step 粒度の temporal decomposition (A/B/C/D クラス) の数値
- Worldlog の spatial vs structural の詳細 (L87: 283 vs 47)
- v9.4 Perception Field 設計の Triad 議論 (概念理解.md と併読推奨)
