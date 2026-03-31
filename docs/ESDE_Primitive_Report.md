# ESDE Primitive Report

*Phase: Primitive (v9.0–)*
*Status: v9.0 Self-Referential Feedback Loop 完了。Phase 1 成功（ループ成立、系は壊れていない）。*
*Team: Taka (Director/Philosopher) / Claude (Implementation) / Gemini (Architecture) / GPT (Audit)*
*Started: March 30, 2026*
*Last updated: March 31, 2026*
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

## 設計上の教訓（Primitive 以降）

Autonomy の教訓 1-40 は ESDE_Autonomy_Report.md に記載。
以下は Primitive フェーズで追加。

41. 中間目標なしの実験はふらふらと繰り返すだけになる。.x バージョンごとに目標共有を必須とする
42. パラメータの固定値議論（0.1 か 0.2 か）に時間を使わない。系から導出する設計に移行する
43. 「次に何をやるか」の前に「それは何に繋がるか」を問う

---

## 開発ロードマップ

### v9.x — 単一 ESDE の母体化（中間目標 1）

| Step | 内容 | 状態 | 中間目標との接続 |
|---|---|---|---|
| 9.0 | Self-Referential Feedback Loop Phase 1 | **完了** | ループ成立確認 |
| 9.1 | gamma / clamp の系導出化 | **次候補** | 手動パラメータ排除 |
| 9.2 | 系全体の固有状態記述 | **次候補** | インスタンス間区別の前提 |
| 9.3 | フィードバック Phase 2（複数値圧縮 or ベクトル化） | 後 | 自己認識の深化 |

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
Phase 1 として成功。これにより ESDE は「系全体の状態が個に返る」構造を持った。
次は中間目標 1 の残り（固有状態記述）と、中間目標 2（複数インスタンス）に向けた設計。
最終目標は「神の手を介さずに認知・意味・社会性が創発するモデル」。
当面のゴールは「私たちと会話ができるシステム」。*
