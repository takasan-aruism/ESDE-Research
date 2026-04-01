# ESDE Primitive Report

*Phase: Primitive (v9.0–)*
*Status: v9.2 Dual-Time Clock Separation完了。torqueは「調整器」ではなく「攪乱→回復の2相サイクル」と判明。step-first開発に移行。*
*Team: Taka (Director/Philosopher) / Claude (Implementation) / Gemini (Architecture) / GPT (Audit)*
*Started: March 30, 2026*
*Last updated: April 1, 2026*
*Prerequisites: Autonomy complete (see ESDE_Autonomy_Report.md)*

---

## 最終目標

「神の手（人間の設計した意味やルール）」を介さずに、物理的な動的平衡の底から、
自発的に「認知」「意味」「他者との関係性（社会性）」が創発する
人工生命/人工意識のモデル（ESDE）を完成させること。

当面のゴール: **私たちと会話ができるシステム。**
その先は ESDE エンジンを用いた AI 開発に合流する。

---

## 中間目標

| # | 目標 | 状態 | 完了条件 |
|---|---|---|---|
| 1 | **単一 ESDE を「母体」として成立させる** | **進行中** | 物理層動的平衡 ✓、仮想層フィードバック ✓、label ecology自律 ✓、系全体の固有状態記述（未） |
| 2 | **複数インスタンスの相互作用** | 未着手 | 複数 seed を隣接空間に配置、相互作用経路の設計と実装 |
| 3 | **意思の疎通** | 未着手 | seed 間で情報伝達が発生するかの観測。戦略的アプローチの前段階 |
| 4 | **認知・意味の創発** | 未着手 | ESDE 内部で「認知」に類する構造が自発的に出現 |
| 5 | **社会性の創発** | 未着手 | 複数 ESDE 間で協調・競争・交渉に類する振る舞い |
| 6 | **言語的コミュニケーション** | 未着手 | ESDE が外部（人間/他の AI）と情報交換可能 |

**原則:**
- パラメータは系から導出する。手動チューニングで 0.1 か 0.2 かの議論はしない
- 実験重視。実験場では柔軟な態度を取る
- .x バージョンが上がるごとに進捗と目標を共有する（必須運用）
- 前人未到のプロジェクトであり暗中模索だが、方向性を失わない

---

## Version Changelog

| Version | Date | 内容 | 主要発見 |
|---|---|---|---|
| v9.0 | 03-30 | Self-Referential Feedback Loop Phase 1 | ループ成立。M=0.993（微小変調）。系は壊れない。v8.5とほぼ同一の結果 |
| v9.1 | 03-31 | Gamma Regime Sweep (Stage A + B) | Stage A: clampが支配的。gamma変えても差なし。Stage B: clamp完全解放でも系は壊れない。torqueは系を支配していない |
| v9.2 | 04-01 | Dual-Time Clock Separation | step-probeでtorqueの2相サイクル発見（攪乱→回復）。torqueは「調整器」ではなく「再構成圧力」。設計意図と観測結果の不一致 |

---

## Autonomy Phase からの引き継ぎ

Autonomy（v8.0-v8.5）で確立した知見の要約。
詳細は ESDE_Autonomy_Report.md を参照。

### 確立された事実

1. **物理層は「存在の床」として機能する。** 純物理ではなく実存の土台（v8.1, v8.3）
2. **全 n→n+1 が質的相転移。** 各ノード数は異なる存在様式（v8.2）
3. **5-node = density independence。** 自分で存在する能力。転換点（v8.2）
4. **2→5 は「手放す」、6→9 は「取り戻す」。** 2 つのフェーズ（暫定、母数少）（500win）
5. **collapse は物理層消滅による連鎖全滅。** 教訓 1 の直接証明（v8.3）
6. **3-node が最も oasis 依存、5-node が最も neutral。** density independence の空間版（v8.4）
7. **territory 比率は全サイズ 1.3× 一定。** 場の性質（v8.4）
8. **2-node は実質 1-node。** penalty 側 alive=0.05。主張と現実の乖離が最大（v8.5 C-light）
9. **label 個体に resistance pattern がある。** 2-node に 4 つの性格。volatile が中高次で支配的（v8.5 RP）
10. **naive frozenset 解凍は identity 崩壊。** 方向性は否定されていない。計測器の感度問題（v8.5 thaw）
11. **認知的結合。** 物理的接続なしに関係を主張する能力。既存理論で扱えない（v8.0）

### 持ち越し課題

- frozenset 解凍: 未成熟。「同サイズ入れ替え」型の再設計が候補
- 物理濃度場（physical presence field）: アイデア保持。現行層の限界が見えてから
- 注意構造（attention hierarchy）: 将来設計メモあり。自己認識の次段階
- gamma 等の固定パラメータ: 系から導出する方法に移行すべき

---

## v9.0 — Self-Referential Feedback Loop

### 目的

ESDE が自分自身の全体状態を自分へ返す最小の自己参照ループを作る。
stress equilibrium（物理層）の仮想層版。

**中間目標 1 への位置づけ:** 「系全体のフィードバックがある母体」の実現。

### 設計

Gemini 設計 + GPT 監査修正。

**掬い取る値:** died_share_sum（CULL 直前に回収した死亡 label の share 合計）

**EMA:** stress equilibrium と同構造。
```
turnover_ema = alpha × died_share_sum + (1 - alpha) × turnover_ema
signal_ratio = died_share_sum / turnover_ema
```

**torque 変調:**
```
M = 1.0 + gamma × (signal_ratio - 1.0)
M = clamp(M, 0.8, 1.2)
torque_mag = energy × rigidity_factor × M
```

- gamma = 0.1（GPT 修正: Gemini 案 0.2 → 0.1）
- clamp = [0.8, 1.2]（GPT 修正: Gemini 案 [0.5, 2.0] → [0.8, 1.2]）
- warmup = 20 window（M=1.0 固定、EMA は更新）

**意味:** 死亡が多い激動期 → torque 強化 → label がまとまろうとする。
穏やかな時期 → torque 弱化 → label が緩む。

### 実装

- virtual_layer_v9.py: v5 + 約 43 行。torque への 1 行乗算 + CULL 前 26 行集計
- genesis_physics / engine: 変更ゼロ
- v8.5 の全計器（C-light, D-light, thaw pressure）を継承

### 48-Seed 結果（v8.5 との比較）

**フィードバック信号:**
```
signal_ratio: mean=0.938  std=0.794  range=[0.000, 4.991]
multiplier M: mean=0.993  std=0.077  range=[0.900, 1.200]
died_share:   mean=0.0056
```

ループは動作している。M は平均 0.993 で ±1% 程度の変調。
clamp の両端（0.9, 1.2）に到達するケースがある。

**survival:**

| size | v8.5 | v9.0 | 変化 |
|---|---|---|---|
| 2 | 0.2% | 0.3% | +28% |
| 3 | 5.2% | 5.7% | +9% |
| 5 | 62.0% | 60.7% | -2% |
| 7 | 88.9% | 83.3% | -6% |

差は統計的ノイズの範囲。フィードバックで系が大きく変わっていない。

**label 数:** v8.5 71.1 → v9.0 71.9（同等）

**空間分布:** v8.5 とほぼ同一。

### 評価

Phase 1 として成功。自己参照ループは成立し、系は壊れていない。
「ループが存在するか」を見る試験であり、
「ループで系が変わるか」は Phase 2 以降。

---

## v9.1 — Gamma Regime Sweep

### 目的

フィードバック強度（gamma）を正負に振り、応答レジームを把握する。
v8.3 崩壊閾値スイープの仮想層版。動的 gamma 設計の入力データ取得。

### Stage A: gamma sweep（clamp=[0.8, 1.2] 固定）

8 条件（0.0, 0.1, 0.3, 0.5, 1.0, -0.3, -0.5, -1.0）× 3 seed。

**結果: 全条件で系は壊れない。**
- gamma=-1.0 でも links=3038, v_labels=70.7, 5n survival 61.5%
- **clamp が支配的。** gamma=1.0 で 52.5% が clamp 下限張り付き
- 5-node survival 全条件で ≈ 61%。差が出ない

### Stage B: clamp 感度（gamma=±0.5, clamp 3 段階）

6 条件 × 3 seed。

**結果: clamp 完全解放でも系は壊れない。**
- gamma=-0.5, clamp=[0.0, 10.0] で M=0.000（torque 完全停止）まで落ちても
  links=3052, 5n survival 61.7%
- gamma=+0.5, clamp=[0.0, 10.0] で M=2.627（torque 2.6 倍）でも
  links=3041, 5n survival 65.2%

**結論: torque を 0 にしても 2.6 倍にしても系はほとんど変わらない。**
torque は系の動態を支配していない。物理層（decay/resonance/exclusion）が支配的。

---

## v9.2 — Dual-Time Clock Separation

### 目的

Taka 仮説: torque が弱いのではなく、仮想層の作用が物理層の粗い時間単位（window=50step）
に同期させられているために効果が見えにくい。

### window レベル結果（interval=50/10/5 × 3 seed）

5-node survival: interval=50 で 61.9%、10 で 60.2%、5 で 60.9%。差なし。

### step-probe: torque の 2 相サイクル発見

window 内の step 毎の推移を計測。GPT temporal decomposition（A/B/C/D クラス）を適用。

**interval=5 のサイクル内プロファイル:**
```
pos0 (torque): link_delta = -1.92  (攪乱)
pos1 (after):  link_delta = -1.00  (余波)
pos2:          link_delta = -1.57  (余波続く)
pos3:          link_delta = +0.29  (回復開始)
pos4:          link_delta = +1.11  (回復)
Cycle NET: -3.09
```

**interval=10 のサイクル内プロファイル:**
```
pos0-5: 負が続く (-2.40, -1.38, -2.05, -1.62, -0.25, -2.60)
pos6-9: 回復 (+0.62, -0.45, +2.45, +1.98)
Cycle NET: -5.70
```

**失われたリンクの品質:**
- S_lost ≈ 0.008（全体平均 S_all ≈ 0.028 の約 29%）
- R+ リンクも少数だが失われる（R+_lost ≈ 0.15/step）
- ゴミリンクだけが消えているのではない。弱いが非ゼロのリンクが広く剪定される

### Torque 設計経緯分析

GPT 監査: 「torque-as-adjuster 仮説は現在の観測と不一致」

**根本原因 3 つ:**

1. **torque の二面性。** θ を phase_sig に引くと、label 内のリンクは維持されるが、
   label 外のリンクは破壊される。正負が相殺するので gamma をどう振っても系全体が変わらない

2. **phase_sig の凍結。** birth 時の θ 平均で固定。物理層の θ は毎 step 変動する。
   古い記憶に基づく torque は攪乱として作用しうる

3. **v7.0→v7.3 の断絶。** v7.0 では「torque 成功 = label 強化」の自己強化ループがあった。
   v7.3 で代謝モデルに切り替わった時、ループが消えたが力の式 sin(phase_sig - θ) は同じまま

### 方針転換（Taka / GPT 合意）

**torque は削除しない。** ミスマッチが見つかったからといって即座に削除するのは ESDE 的ではない。
「失敗した意図」も選択環境の一部として残す。

**torque の再解釈:** 「検証済みの調整器」ではなく「内部の選択圧の一つ」。
label がその圧力の下でどう振る舞うかを観測する。

**step-first 開発に移行。** window レベルの要約ではなく、step スケールの振る舞いを主軸に。
stress が window スケールで多くの効果を平滑化するため、
意味のあるシグナルは step 粒度にある。

**longer window の検討。** 50 step → 100 → 200。
window 内の滞在時間が長いほど、label の行動選択がより具体的に観測可能になる。

---

## 4 要素の現状（Primitive Phase）

| 要素 | 状態 |
|------|------|
| 現在 | 存在（物理層 + 仮想層）。自己参照ループ成立（v9.0）|
| 過去 | 導入済（maturation + rigidity）|
| 未来 | 確定: Future = n→n+1 差分 |
| 外部 | v8.4 局所波 + v9.0 フィードバック。torque は「内部選択圧」に再解釈 |

---

## 設計上の教訓（Primitive 以降）

Autonomy の教訓 1-40 は ESDE_Autonomy_Report.md に記載。
以下は Primitive フェーズで追加。

41. 中間目標なしの実験はふらふらと繰り返すだけになる。.x バージョンごとに目標共有を必須とする
42. パラメータの固定値議論（0.1 か 0.2 か）に時間を使わない。系から導出する設計に移行する
43. 「次に何をやるか」の前に「それは何に繋がるか」を問う
44. torque は「θ を揃える力」として設計されたが、実際には「label 内を揃えて label 外を乱す」二面的な力。正負が相殺するため、強さを変えても系全体に効かない
45. phase_sig の birth 時固定は「記憶」として機能するが、物理層の θ が変動する以上、古い記憶に基づく torque は攪乱として作用しうる
46. 仕組みの目的が途中で変わった場合（v7.0→v7.3）、力の計算式も見直すべきだった。目的だけ変えて実装を引き継ぐと、意図しない効果が蓄積する
47. ミスマッチが見つかっても即座に削除しない。失敗した意図も選択環境の一部として残す。これは ESDE の設計思想そのもの
48. window レベルの要約では隠れるシグナルが step 粒度にある。step-first 開発が必要

---

## 開発ロードマップ

### v9.x — 単一 ESDE の母体化（中間目標 1）

| Step | 内容 | 状態 | 中間目標との接続 |
|---|---|---|---|
| 9.0 | Self-Referential Feedback Loop Phase 1 | **完了** | ループ成立確認 |
| 9.1 | Gamma Regime Sweep (Stage A + B) | **完了** | torque は系を支配しない。clamp 解放でも壊れない |
| 9.2 | Dual-Time Clock Separation + Step Probe | **完了** | torque の 2 相サイクル発見。設計意図と観測の不一致確認 |
| 9.3 | step-first 開発 + longer window 検討 | **次** | label の step スケール行動観測 |
| 9.4 | broader mechanism audit | **次候補** | torque 以外の仕組みも意図通りか検証 |
| 9.5 | フィードバック返し先再検討（share / birth-death） | 後 | torque 以外の経路でフィードバックを返す |

### v10.x — 複数インスタンス（中間目標 2-3）

| Step | 内容 | 状態 | 中間目標との接続 |
|---|---|---|---|
| 10.0 | 複数 seed の同一/隣接空間配置 | 未着手 | 相互作用経路の確立 |
| 10.1 | seed 間情報伝達の観測 | 未着手 | 意思の疎通の前段階 |
| 10.2 | 戦略的アプローチの観測 | 未着手 | 社会性の萌芽 |

### v11.x 以降 — 認知・言語（中間目標 4-6）

未設計。v10.x の結果を見てから。

---

## 現在の ESDE アーキテクチャ概要

### 物理層（Genesis canon、凍結）

- 5000 ノード、71×71 グリッド
- 各ノード: E（エネルギー）、θ（位相）、ω（固有周波数）
- リンク: S（強度）、R（共鳴値）
- 5 つの力: 位相回転 → エネルギー流 → 共鳴 → 減衰 → 排除
- stress equilibrium: リンク数の EMA による動的平衡

### 仮想層（virtual_layer_v9）

- label: frozenset（ノード群への主張）。birth 時に固定
- torque: phase_sig に向けてノードの θ を引っ張る
- share: territory に基づく存在の重み
- cull: share < threshold で死亡
- **v9 追加:** 系全体の died_share_sum → EMA → torque modulation

### 計測層（calibrate 側）

- local wave: decay sin 勾配（oasis/penalty 地形）
- C-light / D-light: 代表 label の内部状態追跡
- thaw pressure: frozenset 解凍圧の仮想測定
- resistance pattern: label 個体の抵抗様式分類

---

*v9.0 で ESDE に初の自己参照フィードバックループを導入。
died_share_sum → EMA → torque 変調。ループは成立し、系は安定。
v9.1 で gamma/clamp を正負に振ったが、torque の強弱は系に影響しなかった。
v9.2 で step-probe により torque の 2 相サイクル（攪乱→回復）を発見。
torque は「調整器」ではなく「再構成圧力」として機能していた。
設計経緯分析で 3 つの根本原因を特定（二面性、phase_sig 凍結、v7.0→v7.3 断絶）。
Taka 方針: torque は削除せず「内部選択圧」として保持。step-first 開発に移行。
ミスマッチを即座に削除するのではなく、選択環境の一部として残す。
次は step スケールの行動観測、longer window 検討、broader mechanism audit。
最終目標は「神の手を介さずに認知・意味・社会性が創発するモデル」。
当面のゴールは「私たちと会話ができるシステム」。*
