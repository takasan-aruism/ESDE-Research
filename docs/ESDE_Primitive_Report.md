# ESDE Primitive Report

*Phase: Primitive (v9.0–v9.13、**v9.13 完了**)*
*Status: **中間目標1達成。** v9.11 Cognitive Capture 確立。v9.12 audit 完了。**v9.13 で S≥0.20 hard threshold 撤去、persistence-based birth 確立**。次フェーズ (v9.14/v10.0) は「CID が物理状態を記憶として読む関数」の設計。*
*Team: Taka (Director/Philosopher) / Claude (Implementation) / Gemini (Architecture) / GPT (Audit)*
*Started: March 30, 2026*
*Last updated: April 17, 2026 (v9.13 完了)*
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
| 1 | **単一 ESDE を「母体」として成立させる** | **達成** | 物理層動的平衡 ✓、仮想層フィードバック ✓、label ecology自律 ✓、Stress OFF で仮想層が平衡肩代わり ✓、External Wave 耐性 ✓ |
| 2 | **複数インスタンスの相互作用** | **設計中** | 複数 seed を隣接空間に配置、相互作用経路の設計と実装 |
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
| v9.3 | 04-02 | Deviation Detection → Sequential Torque | 偏り検知（31%改善）→スケール問題→contention gate→**逐次化**。NET -3.09→-0.82。バッチ処理が攪乱の主因。torque/gravity正常 |
| v9.3+ | 04-02 | Age順 + Longer Window | age順でNET初の正転（+0.08）。500 step/winでNET -0.09（完全平衡）。2相サイクル消滅 |
| v9.3+ | 04-03 | Stress OFF + External Wave耐性テスト | Stress OFFでNET +0.06（二重平衡干渉の解消）。5-seed比較でlinks同等、5n強化。Ext Wave A=0.5でも崩壊せず。**中間目標1達成** |
| v10.0a | 04-03 | Membrane Coupling Sanity Check | 1-State N=10000で実装。cross link問題（膜なしでA-B間2800本）。膜は即死（θ差1.54 rad）。**保留** |
| v9.4 | 04-04 | Coupling Probe + Perception Field | label間カップリング計測→ほぼゼロ（1-hopでは影響圏が重ならない）。方針転換: N-hop Perception（知覚圏）を先に定義。wrap-around torus |
| v9.4 | 04-04 | Continuity Observation | world_J=0.988、partner_J=0.81。labelは時間をまたいで世界像と社会関係を保持。type persistence（L87: 10/10 STABLE） |
| v9.4 | 04-05 | Worldlog v1→v2 | spatial(固定) vs structural(激変)の発見。spatial=283, structural=17-173。structural worldはstep単位で崩壊・再生。1本のリンクが数十ノードの変化を引き起こす |
| v9.5 | 04-05 | 3層構造確立 + 認知Phase 1（φ） | 物理=波、存在=粒子、認知=過程。φ = α×sin(mean_θ_structural - φ)。全label DETACHED → αが高すぎた |
| v9.5 | 04-05 | Phase 1.5 対称二項分析 | Δ_phase分布が一様。self-sideとworld-sideに相関なし。convergence moments（|Δ|<0.3）は10%存在 |
| v9.5 | 04-06 | Convergence Detail | convergence時near_phase=34%、divergence時18%（2倍）。**偏りの実体はノード位置ではなくθ分布**。認知の手がかり |
| v9.5 | 04-06 | Phase 2 Attention Map | 接触記憶として機能。near/far bias非蓄積（接触記憶であり価値記憶ではない）。L101集中記憶。label間hotspot共有（L3↔L76: 268ノード）。成長→飽和パターン |
| v9.5 | 04-06 | Phase 3 Partner Familiarity | 実装完了。decay=0.998（半減期346 step）。実行待ち |

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

## v9.3 — Deviation Detection → Sequential Torque

### 目的

v9.2 で判明した torque の 2 相サイクル（攪乱→回復）の原因を特定し、解決する。

### Phase A-C: 偏り検知 + 局所返し

GPT 提案: ESDE 自身が偏りを検知し、弱い返しをかけ、結果を記録する最小ループ。
原始的脳機能の入口。

**実装:**
- D1: phase_drift（phase_sig と θ 平均の乖離）重み 0.5
- D2: link_loss（前 window からの territory 減少率）重み 0.3
- D3: torque_exposure（前 window の torque 適用量）重み 0.2
- gravity_factor = 1.0 - score → 偏りが大きい label ほど gravity を自制

**window 粒度結果:**
```
gravity ON (v9.2):   NET = -3.09
gravity OFF (v9.2):  NET = -0.65
deviation (v9.3):    NET = -2.13（31% 改善）
```

偏り検知は機能。pos0 の攪乱が -1.92 → -1.18 に減少。pos1 で即回復（+1.61）。
しかし pos2 で再悪化（-1.71）。gravity OFF の -0.65 には届かない。

### step 粒度の試行と失敗

D1 の step 粒度更新 → 効果なし（D1 が 5 step 間で動かない）。
label 本体リンク変化 → 効果なし（5 ノード/30 リンクが小さすぎる）。
label + 1-hop パッチ → 効果なし。

**原因特定:** 全 label の同時適用。70 label が一斉に torque をかけるため、
個体の影響が全体に埋没し、個体レベルの因果検知が不可能。
これは計測器の問題でもスケールの問題でもなく、**同時性の問題**。

### 機能不整合リスク監査

torque と同じパターン（目的変更→実装未追従）の候補を全メカニズムで追跡。

| # | メカニズム | リスク |
|---|---|---|
| 1 | torque | **確定** — 攪乱として機能（後にバッチ処理が原因と判明）|
| 2 | semantic gravity | **要検証** — frozenset で目的不可能なのに残存（後に正常と判明）|
| 3 | phase_sig 固定 | **確定** — torque 不整合の根本原因の一つ |
| 4-7 | share/cull/prev_alignment/recurrence | 低リスク |

### semantic gravity ON/OFF 比較

gravity OFF で NET = -0.65。gravity が攪乱の 80% を占めると判断。
しかし後に**バッチ処理が真の原因**と判明。

### 仮想層バッチ処理問題の発見

全メカニズム（birth/share/torque/cull）が「全 label 同時処理」。
個体の因果関係が構造的に消失。偏り検知も局所応答も将来の戦略的行動も、
この同時性に制約されていた。

### contention gate（Taka 案 1）

Git 的発想: 同じノードを 2 label 以上が引く場合はスキップ。
結果: ほぼ効果なし。frozenset が排他的なので core torque に競合が発生しない。
問題は「競合」ではなく「同期的集団攪乱」と判明。

### 逐次化（Taka 案 2: 最終解答）

Taka の洞察: 「えいやで一気に回したから壊れた」。
各 label が 1 体ずつ torque を計算→即適用。次の label は更新後の θ を見る。
label 順序は window ごとにシャッフル（決定論的）。

**結果:**

| 条件 | pos0 | NET | gravity |
|---|---|---|---|
| batch gravity ON | -1.92 | **-3.09** | ON |
| batch gravity OFF | -1.98 | **-0.65** | OFF |
| deviation (window) | -1.18 | **-2.13** | ON (弱化) |
| contention gate | -2.43 | **-2.24** | ON (ゲート) |
| **sequential** | **-0.20** | **-0.82** | **ON** |

**pos0 の攪乱: -1.92 → -0.20。gravity ON のまま gravity OFF 水準に到達。**

### 結論

v9.0-v9.2 の「torque は系に効かない」「torque は攪乱器」という結論は
**バッチ処理のアーティファクトだった**。

torque も semantic gravity も正常に機能している。
壊していたのは 70 label の同時適用。1 体ずつ適用すれば、
各 label は自分のノードの θ を適度に揃え（torque）、
周囲を適度に引き寄せ（gravity）、リンク構造を維持する。

### Age順 + Longer Window

**age順:** 古い label（弱い torque）が先に動き、θ 空間の「地盤」を整える。
若い label（強い torque）はその上で行動する。生態系の自然な秩序。

| 順序 | NET |
|---|---|
| random run1 | -1.97 |
| random run2 | -0.42 |
| share | -1.91 |
| **age** | **+0.08** |

age順で**初めて NET が正に転じた**。torque が系を壊さず建てている。

**Longer Window（総ステップ 10,000 固定）:**

| step/win | windows | stress介入 | NET |
|---|---|---|---|
| 50 | 200 | 200回 | -1.63 |
| 200 | 50 | 50回 | -0.67 |
| **500** | **20** | **20回** | **-0.09** |

500 step/window で NET = -0.09。**2相サイクルが完全に消滅。**
全 pos が ±0.5 以内。仮想層が stress の支配から解放され、自律的に平衡に向かう。

### Stress OFF 比較

Taka の予測: 「二重の平衡処理が不安定を生んでいる」。

| 条件 | NET | links | vLb |
|---|---|---|---|
| Stress ON | -0.09 | 2958 | 23 |
| **Stress OFF** | **+0.06** | **3080** | **23** |

**Stress OFF で NET が正に転じた。** リンク 3080 で崩壊なし。
仮想層（θ空間）と Stress（リンク密度）が異なる基準で最適化し、互いの成果を壊していた。

5-seed 比較:

| 指標 | Stress ON | Stress OFF |
|---|---|---|
| links | 2799 ± 100 | 2795 ± 90 |
| v_labels | 33.4 ± 5.3 | 33.3 ± 5.0 |
| 5n surv | 76.6% | **83.3%** |
| 4n surv | 71.4% | 50.9% |

リンク数と label 数は同等。5n は Stress OFF で強化。4n は弱体化
（Stress の calcification ブーストが消えたため）。

### External Wave 耐性テスト（Stress OFF）

bg_prob に sin 変調: A=0.3 で ±30%、A=0.5 で ±50% のエネルギー注入変動。

| 条件 | links | v_labels | 5n surv |
|---|---|---|---|
| baseline | 2862 | 30.8 | 83.3% |
| A=0.3 | 2906 | 22.8 | 87.5% |
| A=0.5 | 2631 | 29.2 | 82.1% |

**A=0.5 でも崩壊しない。** 3n/4n の survival はむしろ改善（少数精鋭化）。
External Wave は破壊ではなく選別圧として機能。

---

## 中間目標1: 達成

完了条件:
- 物理層動的平衡 ✓（Stress なしでも仮想層が肩代わり）
- 仮想層フィードバック ✓（逐次 torque + age 順 + deviation）
- label ecology 自律 ✓（5n survival 82-87% で安定）
- 環境変動耐性 ✓（External Wave A=0.5 でも崩壊せず）

### v9.0 → v9.3 全経路まとめ

| # | 変更 | NET |
|---|---|---|
| 1 | batch gravity ON (v9.2 baseline) | -3.09 |
| 2 | batch gravity OFF | -0.65 |
| 3 | batch + deviation (window 粒度) | -2.13 |
| 4 | sequential only（逐次化） | -0.82 |
| 5 | seq + age + dev ON | +0.08 |
| 6 | seq + age + dev, 500 step/win | -0.09 |
| 7 | **seq + age + dev, 500 step, Stress OFF** | **+0.06** |

**torque 計算式を一切変えず、4 つの構造変更（逐次化・age 順・longer window・Stress OFF）だけで達成。**

---

## v10.0a — Membrane Coupling（保留）

中間目標2（複数インスタンス接続）の第一歩として、
2つの独立生態系を物理的に接続する Synaptic Membrane を実装。

設計: 1-State N=10000。Seed A(0-4999) と Seed B(5000-9999)。
20ペアの sparse membrane（S_init=0.05）で成熟後に接続。

**結果：2つの構造問題が判明。**

1. **Cross link 問題:** 膜なしの段階で A-B 間に 2800 本のリンクが存在。
   1-State では Genesis の latent field が Seed 境界を越えてリンクを生成する。
   「独立な2世界」が物理的に成立していなかった。

2. **膜即死:** 初期 phase_diff = 1.54 rad（約88度）。S=0.05 の弱いリンクは
   θ差による decay で 1 window 以内に全滅（0/20）。

→ **v10.0a は保留。** シード間接続より先にシード内のlabel間相互作用を検証すべき
（GPT方針転換メモ）。

## v9.4 — Label間カップリング → Perception Field

### Coupling Probe（失敗）

逐次torqueのlabel単位分解で、各labelの torque が他 label のθにどう影響するかを計測。

**結果:** 50 actor のうち 40 が影響ゼロ。意味のあるペアは grid 上で偶然隣接した1組のみ。

**原因:** semantic gravity の到達範囲が 1-hop（上下左右4マス）しかない。
5000ノードに70 label が散在。各labelの影響圏（5ノード + 近傍20ノード）は
他 label と重ならない。**label は孤島。**

### 方針転換: N-hop Gravity → N-hop Perception

Taka/GPT 判断: N-hop で作用させる前に、まず label が「何を見ているか」を定義する。
「周囲に作用する主体」の前に「世界を見ている主体」として定義する。

### Perception Field の設計

- **知覚範囲:** label の alive node 数 = hop数（5-node → 5-hop）
- **世界幾何:** wrap-around torus（端バイアス排除）
- **観測専用:** state.theta / S / R は一切変更しない

計測項目:
- 可視総ノード数、hop 別分布
- 内訳: wild（無所属）/ other label core / self core
- θ統計: variance、phase_sig との距離、near/far phase
- リンク強度統計
- **label 間の知覚圏重なり**（pairwise overlap）→ 境界候補の特定

### 影響圏モデルの将来像（Taka提案、未実装）

- label = キャラクタ（戦国大名）。frozenset が家臣、phase_sig が思想
- 統率力 = n_nodes × mean_S_territory → gravity の hop 数を導出
- 影響圏の重なり = 境界 = 取り合いの現場
- A と B の境界から第三勢力 C が生まれる = **三項創発**
- torque にコスト導入（label がθ場を張ることで share が微減する）→ 将来候補

### Continuity Observation（存在層の継続活動）

同じ label を複数 window にわたって追跡。

- **world_J = 0.988:** label は 99% 同じ世界を見続けている
- **partner_J = 0.81:** 見える相手の 80% が前 window と同じ
- **19 ペアが 70% 以上の window で共存:** 境界が持続的
- **type persistence:** L87 は 10/10 window で social|wide STABLE

→ 認知層は新規設計不要かもしれない。存在層が既に認知の基礎を持っている。

### Worldlog: Spatial vs Structural の発見

spatial（torus BFS）= 1/window、structural（alive link BFS）= 毎 step で追跡。

- **spatial と structural はほぼ別世界。** L87: spatial 283, structural 47, overlap 8
- **spatial は安定（283→283）、structural は激変（17→173）**
- **1 本のリンクの生死が数十ノードの structural 変化を引き起こす（critical transition）**
- emerged ≈ disappeared（動的平衡が step 粒度でも見える）

→ 「見える」（spatial）と「触れる」（structural）は 2 つの異なる知覚。

---

## v9.5 — 3層構造と認知層の芽

### 3層構造（Taka の設計原則）

| 層 | 比喩 | 性質 | 変化 |
|---|---|---|---|
| 物理層 | 波 | θ、S、リンクの運動 | 常に動く |
| 存在層 | 粒子 | frozenset + phase_sig | 固定（魂） |
| 認知層 | 過程 | 波と粒子の間に生まれるパターン | 動的 |

- 存在層は物理層にほとんど影響しない（torque は微小）
- 認知層は存在層に影響しない
- **frozenset は解放しない。魂は固定**
- 動きは認知層の内部状態の変化として生まれる
- 同じ魂（frozenset）から、経験の違いで異なるキャラクターが立ち上がる

### Phase 1: 認知位相 φ

label に φ（角度）を 1 つ追加。structural world の平均θ方向に追従。

  φ += α × sin(mean_theta_structural - φ)
  α = 0.1 × (1.0 - mean_S_structural)（Gemini 裁定）

**結果: 全 label が DETACHED（φ が phase_sig から大きく離れた）。**
mean_S ≈ 0.03 → α ≈ 0.097（ほぼ最大感度）。structural world の激しい変動に
φ が全力で追従 → 風見鶏状態。記憶がない。

**しかし発見あり:** phase_sig が全く違う label 同士（L4 と L113）の φ が収束（差 0.004）。
「魂が違っても同じ世界を見ていると同じ方向を向く」。

### Phase 1.5: 対称二項分析

GPT 方針転換: φ の α 調整ではなく、自己側（phase_sig）と世界側（mean_theta_structural）の
対称表現を立て、その差分を直接観測。

- **Δ_phase 分布が完全に一様。** self-side と world-side にランダムな関係
- **convergence moments（|Δ| < 0.3）は L87 で 10.8% 存在**
- しかし structural size との相関がない → αチューニングでは解決しない

### Convergence Detail（偏り検出）★★

convergence moments の structural set の中身を分析。

**核心の発見: convergence 時の near_phase 比率が divergence 時の 2 倍。**

| Label | conv near_phase | div near_phase | 比率 |
|---|---|---|---|
| L87 | 34.3% | 18.1% | **1.9x** |
| L101 | 53.8% | 8.8% | **6.1x** |
| L112 | 35.2% | 17.0% | **2.1x** |

自己と世界が近づく時には、structural set に phase_sig に近い θ のノードが多い。
convergence はランダムではない。因果がある。

**偏りの実体はノード位置ではなく θ 分布。** conv_only ノードは 509 個存在するが分散。
特定のノードが毎回 convergence を起こすのではなく、θ の質が一致した時に起きる。
convergence 間 Jaccard = 0.35（構成は変わるが 35% は共通）。

### Phase 2: Attention Map（接触記憶）

label に {node_id: float} を追加。structural set に入ったノードに毎 step +1、全体を × 0.99 で減衰。
半減期 69 step。リンクが消えても認知層に痕跡が残る。

**結果:**

- **near/far bias は蓄積されない。** convergence detail の偏り（conv 34% vs div 18%）は
  attention に残らない。全 step の structural 出現を等しく +1 するため、convergence の偏りが
  希釈される。attention は「接触記憶」であり「価値記憶」ではない。GPT 裁定: この定義を維持すべき
- **L101 の entropy 低下（0.72-0.79）。** 他の label は 0.83-0.87。小さな世界の中で同じノードに
  繰り返し接触するため注意が集中。**世界の大きさがキャラクターの記憶の質を変えている**
- **label 間 attention hotspot 共有。** L3↔L76: 268 ノード、L3↔L112: 151、L76↔L112: 150。
  同じ地域の label は同じノードを記憶する。**共有経験の原型**
- **attention map の成長パターン。** L87: 17→1306→2194→1610。急速に世界を覚え、その後は
  新規追加と prune が釣り合う飽和状態

### Phase 3: Partner Familiarity（人の記憶）— 実行待ち

label に {other_label_id: float} を追加。他 label の core が structural set に見えたら +1、
decay = 0.998（半減期 346 step）。場所の記憶の 5 倍長く覚える。

分析予定: reciprocal pairs（互いを知る関係）、familiarity vs attention overlap、
L87 の social network 内部化。

---

## v9.8 trilogy — Subject Reversal + Introspection + Information Pickup

v9.5 で確立した 3 層構造の上に、label 中心から **cid (cognitive_id) 中心** へ主体を反転させる。
3 段階 (a/b/c) で段階的に追加。全段で物理層不変を維持。

### v9.8a — Subject Reversal

**目的:** 認知層の主体を label_id (lid) から cognitive_id (cid) に反転。cid は単調増加 int で再利用しない。

**設計:**
- `SubjectLayer` クラスを新設（旧 CognitiveLayer の置き換え）
- Lifecycle: birth(lid) → cid 発番 / detach(lid) → ghost 化 / reap_ghosts() → TTL 超過で完全削除
- ghost 状態: perception 更新停止 (inert)、ただし他 cid の familiarity dict には残る（= 死んだ人を覚えている）
- GHOST_TTL = 10 (provisional engineering value、理論的主張ではない)
- **核心:** label が死んでも cid は即座に死なない。label 死亡 ≠ cid 死亡

**結果:** 48-seed short + 5-seed long で実行。per_window CSV は v9.5 と bit identical を確認（物理層不変）。

### v9.8b — Minimal Introspection

**目的:** cid に「自分の変化に気づく」機能を追加。disposition 4 軸の window 間 delta で gain/loss タグを生成。

**設計:**
- disposition 4 軸 (Stage 1、固定閾値):
  - social = n_partners / max_all_partners（[0,1] 正規化比率）
  - stability = 1/(1 + std/mean of structural set sizes)（[0,1]）
  - spread = Shannon entropy of attention map / log(n)（[0,1] 正規化）
  - familiarity = mean(familiarity values)（[0,∞) **非正規化**）
- 閾値: SOCIAL=0.1, STABILITY=0.1, SPREAD=0.1, FAMILIARITY=2.0
- 条件: delta > threshold → gain_xxx / delta < -threshold → loss_xxx
- **Gemini freeze ruling:** 観察専用。torque/action に一切反映しない。ghost は is_hosted ガードでスキップ

### v9.8c — Information Pickup

**目的:** 死亡 label の「情報プール」から、hosted cid が排他的競争で拾得。

**設計:**
- 死亡 label → death pool に deposit（所属 cid 群の情報）
- hosted cid が phase 距離で競争、最近者が勝つ
- **効果は TTL 延長のみ** (cid_ttl_bonus += 1)。物理層不変。GPT 監査条件遵守
- per_subject CSV: ttl_bonus, n_pickups_won/lost, effective_ttl 列追加

**結果:** 48-seed short + 5-seed long で per_window CSV bit identical 維持。

---

## v9.9 — 内的基準軸の骨格 (exploration build)

**目的:** v9.8b の内省タグを使い、cid 自身が「自分にとっての通常」を持つ構造を作る。window 基準、固定閾値のまま。

### 設計

cid に以下の状態を追加（SubjectLayer 内、engine.state に触れない）:
- `recent_tags`: deque(maxlen=5)、frozenset(tags) を append
- `recent_dispositions`: deque(maxlen=5)、4 軸 dict を append
- `personal_range`: 4 軸 × {min,max,mean,std}
- `drift`: 4 軸 × {positive_count, negative_count, neutral_count}

generate_introspection_tags() 末尾に hook を挿入:
- **Rule 1** (n<3): 全派生量 = "unformed"
- **Rule 2** (lowest_std_axis): std が最小の軸、EPS=1e-9、同率なら "tie"
- **Rule 3** (dominant +/- drift): positive/negative count 最大の軸、0 なら "none"、同率なら "tie"
- drift は毎回 recent_tags からゼロ再構築（**累積禁止**）

per_subject CSV に v99_ prefix 33 列追加。ghost は関数先頭で早期 return（freeze）。

### 本番結果

- 48 seeds short + 5 seeds long で per_window CSV **bit identical** (v98c と完全一致)
- per_subject の v98c 既存列も mismatches=0
- v99_ 列 33 個、全 seed 出力確認

### 3 所見 (short 48 seeds 集約)

**所見 1: familiarity negative drift 82.7% 支配**

dominant_negative_drift_axis (formed のみ):
- familiarity 82.7% (953/1152)
- none 9.5%, tie 5.2%, social 1.6%, stability 0.8%, spread 0.2%

**所見 2: spread 沈黙 (lowest_std_axis = spread が 67.6%)**

formed cid の 67.6% で spread が「最も変化しない軸」。familiarity は 0%（最小 std にならない）。

**所見 3: effective_ttl ≥12 → 100% formed**

seed 0 で effective_ttl 12 以上の cid は全て formed。ただし後続の lifetime 統制で境界効果と判明。

### Lifetime 統制分析

v9.8c+ の lifetime_controlled.py と同じ bin 定義 (L01-L06、introspection history 長) で統制:

- **所見 1 (familiarity 支配)**: L02-L05 で 79-96% 維持。**L06 (36+ win) で 54.8% に低下**、"none" が 34.2% に急増。entropy: L02=0.301 → L06=1.471。残差あり
- **所見 2 (spread 沈黙)**: L02=54%, L06=74%。**lifetime でほぼ説明されない、全 bin で spread 最頻**
- **所見 3 (ttl 12+ → formed)**: LONG で見ると L02 は ttl 12+ でも 46%。**境界効果、棄却**

### 4 軸閾値監査 (Stage 1)

4 軸の |delta| 分布と閾値の対応:

| 軸 | 閾値 | |delta| p50 | |delta| p90 | 閾値位置 | tag 発生率 | 判定 |
|---|---:|---:|---:|---|---:|---|
| social | 0.1 | 0.036 | 0.111 | p85-p90 | 12.4% | OK |
| stability | 0.1 | 0.032 | 0.079 | p96 | 3.9% | **粗すぎ** |
| spread | 0.1 | 0.023 | 0.067 | p97 | 3.2% | **粗すぎ** |
| familiarity | 2.0 | 2.631 | 12.33 | p40 | 59.9% | **細かすぎ** |

**結論:** spread 沈黙 = 閾値アーティファクト（INTROSPECTION_THRESHOLD_SPREAD=0.1 が実変動幅より大きい）。familiarity 支配 = 閾値 2.0 が分布の中央以下で tag が乱発。4 軸の閾値バランスが破綻。

> Taka の判断: 「Stage 2 (固定閾値の数値再調整) を飛ばして Stage 3 (動的閾値) に直行する」

---

## v9.10 — Pulse Model & Subjective Surprise (exploration build)

**目的:** v9.9 の window 基準 + 固定閾値 → **Pulse 基準 + MAD-DT (主観的驚き動的閾値)** に観測方式を変更。v99_ 列は一切改変せず v10_ 列を新設併存。

### 設計 (全て確定値、変更禁止)

**Pulse 式:** `is_pulse = (t % 50) == (cid % 50)`。各 cid は自分の ID に応じて 50 step ごとに観測。決定論的（乱数禁止）。

**動的閾値 MAD-DT:**
```
theta = mean(|delta_history|)         # 日常的な揺れ幅
R = delta_current / (theta + epsilon) # 主観的驚き指数
```

**タグ判定:**
- R > +1.0 → gain_xxx (Normal)、R < -1.0 → loss_xxx (Normal)
- R が過去 K=20 パルスの R_max 更新 → major_gain_xxx (Major)
- Normal と Major は排他でなく併存しうる

**Cold Start:** Pulse 1-3 回目は unformed（タグ生成なし、pulse_tags に push しない）。4 回目以降 R 計算開始。

**Ghost:** pulse 判定スキップ、履歴保持、re-host 時 reset 禁止、reap 時破棄。

### 実装

- `primitive/v910/v910_pulse_model.py` (2,073 行): v99 ベースに v10 層を ADD ONLY
- SubjectLayer に v10 dicts 13 個追加、on_pulse() メソッド新設
- per-step ループ内に pulse 発火統合
- per_subject CSV に v10_ 20 列追加、pulse/pulse_log_seed*.csv 新規出力
- v99_ 33 列は完全保持（1 バイトも触らない）

### 本番結果

- 5 seeds long + 48 seeds short で per_window CSV **bit identical** (v99 と全 53 seed 一致)
- per_subject v99_ 列 mismatches = 0
- v10_ 列 20 個、全 seed 出力確認
- pulse 発火数: 理論値 (tracking_steps / 50) と完全一致

### L06 長命群の核心的発見

v9.9 (fixed threshold、per-window):
- L06 dominant negative: familiarity 54.8%, none 34.2%, entropy 1.471

v9.10 (MAD-DT、per-pulse、L06 active 33,671 pulses):

| 軸 | Normal gain+loss | 比率 |
|---|---:|---:|
| social | 14,313 | **28.2%** |
| spread | 13,668 | **27.0%** |
| familiarity | 13,739 | **27.1%** |
| stability | 8,964 | **17.7%** |

**familiarity 支配は消えた。** v9.9 の 54.8% → v9.10 の 27.1%。4 軸均等状態 (25% = 理想的均等) に接近。spread 沈黙も消えた (27.0%)。**v9.9 の所見は fixed threshold のアーティファクト**であることが実測で確定。

唯一の残差: stability (17.7%) が他 3 軸より低い。

### Stability 残差の切り分け (Stage A)

stability の計算式: `1/(1 + std/mean of window_st_sizes)`

| 所見 | 数値 | 解釈 |
|---|---|---|
| |R|≤1 率 | stability 75.0% (他軸 61-68%) | R が ±1 に収まりやすい→Normal 発火しにくい |
| |delta| p50 | stability 0.0145 (spread 0.0067 より大) | delta 自体は小さくないが theta も大きい |
| 全 bin 沈黙 | L01=16.7% → L06=26.6% | L06 特有でなく全域で一貫して最下位 |

**観測器の癖の候補あり:**
1. `window_st_sizes` は window 先頭でリセット → ノコギリ波特性 (pulse 位置依存)
2. `1/(1+x)` 圧縮 → std 安定期に 1.0 張り付き → delta 微小化
3. ESDE 性質の可能性は否定できない (Stage B/C 未実施)

---

## 4 要素の現状（Primitive Phase）

| 要素 | 状態 |
|------|------|
| 現在 | 存在（物理層 + 存在層）。自己参照ループ成立（v9.0）。逐次化 + age 順で torque/gravity 正常化（v9.3）。Stress OFF で存在層が平衡肩代わり。知覚圏の持続性確認（v9.4） |
| 過去 | 導入済（maturation + rigidity）|
| 未来 | 確定: Future = n→n+1 差分 |
| 外部 | v8.4 局所波 + v9.0 フィードバック + v9.3 deviation detection + External Wave 耐性確認済 |
| **認知（新）** | Phase 1（φ）完了。Phase 1.5 対称分析完了。convergence の θ 偏り発見。Phase 2（attention map）完了: 接触記憶、label 間 hotspot 共有。Phase 3（partner familiarity）実行待ち |

---

## 設計上の教訓（Primitive 以降）

Autonomy の教訓 1-40 は ESDE_Autonomy_Report.md に記載。
以下は Primitive フェーズで追加。

41. 中間目標なしの実験はふらふらと繰り返すだけになる。.x バージョンごとに目標共有を必須とする
42. パラメータの固定値議論（0.1 か 0.2 か）に時間を使わない。系から導出する設計に移行する
43. 「次に何をやるか」の前に「それは何に繋がるか」を問う
44. torque の「二面性」（label 内を揃えて label 外を乱す）はバッチ処理のアーティファクトだった。逐次化で正常動作を確認。**現象を見た時にメカニズムを疑う前に実行方式を疑え**
45. phase_sig の birth 時固定は「記憶」として機能するが、物理層の θ が変動する以上、古い記憶に基づく torque は攪乱として作用しうる（ただし逐次化後は影響が微小）
46. 仕組みの目的が途中で変わった場合（v7.0→v7.3）、力の計算式も見直すべきだった。目的だけ変えて実装を引き継ぐと、意図しない効果が蓄積する
47. ミスマッチが見つかっても即座に削除しない。失敗した意図も選択環境の一部として残す。これは ESDE の設計思想そのもの
48. window レベルの要約では隠れるシグナルが step 粒度にある。step-first 開発が必要
49. 70 label の同時バッチ適用は「集団同期攪乱」を起こす。個体の因果関係が消失する。「別ファイルを別人が同時編集 → merge は通るがプロジェクトが壊れる」（Taka/Git 的比喩）
50. 「競合排除」と「同時性排除」は別の問題。frozenset 排他で競合はほぼゼロでも同時性が攪乱を起こす
51. 逐次化は最小変更で最大効果を生む場合がある。torque 計算式は一切変えず、適用順序だけで NET が -3.09 → -0.82
52. 物理層と仮想層で適切な時間スケールが異なる。50 step/window は物理層に最適化されていた。仮想層には 500 step/window 以上が必要
53. stress の介入頻度は仮想層の自律性を決める。介入 200 回 → 仮想層は奴隷。介入 20 回 → 仮想層は自律
54. torque 計算式を一切変えず、4 つの構造変更（逐次化・age 順・longer window・Stress OFF）だけで NET -3.09 → +0.06
55. Stress は仮想層が未成熟な時代の安定装置。仮想層が成熟すれば役割は縮小可能
56. 二重平衡は安定ではなく干渉を生みうる。θ 空間とリンク密度という 2 つの最適化基準が競合すると互いの成果を壊す
57. 安全装置を外すテストは仮想層を十分に成熟させてから行う。逆順では崩壊する
58. label の影響範囲が狭すぎると label 間カップリングは生じない。個が孤島であれば社会は生まれない
59. 境界（影響圏の重なり）は破壊の場であると同時に創発の場。A 対 B の二項対立から C が生まれる三項創発
60. 「作用させる」前に「見えているか」を確認する。知覚なき作用は検証不能
61. 1-State で N を増やしても Genesis の latent field が境界を無視する。物理的分離は 1-State では保証されない
62. frozenset は魂。動かさない。動きは認知層で生まれる
63. 物理層 = 波（常に動く）、存在層 = 粒子（固定）、認知層 = 過程（波と粒子の間に生まれるパターン）
64. 同じ魂（frozenset）から、経験の違いで異なるキャラクターが立ち上がる
65. 認知層の最初の仕事は「世界に作用すること」ではなく「世界を知ること」。物理や原子のような波形型の動きでは認知にならない。偏りを追いかけることで得られるものがある
66. label の死亡とキャラクター (cid) の死亡は別の事象。cid は ghost として残り、他 cid の記憶にも残る。「種子と実」の分離
67. 固定閾値は観測器のバイアスを作る。spread=0.1 は実変動幅 (p90=0.067) より大きく沈黙を生み、familiarity=2.0 は p40 で乱発を生む。**パラメータの数値議論ではなく、観測方式の転換で解決する** (教訓 42 の実践)
68. 動的閾値 (MAD-DT) は各 cid が「自分にとっての通常」を基準にするため、軸のスケール差を自動補正する。v9.9 で見えた familiarity 支配 82.7% は v9.10 で 27.1% (4 軸均等) に変わった。**所見の「意味」は観測器が決める**
69. Stage 2 (固定閾値の再調整) を飛ばして Stage 3 (動的閾値) に直行する判断は正しかった。中間ステップは「あとで調整する」ための安心感を与えるが、多くの場合その安心感自体が前進を遅延させる
70. stability 軸の特異性 (17.7%) は計算式由来 (window_st_sizes リセット = ノコギリ波) の可能性と ESDE 自体の性質の可能性が未分離。**観測器の癖と本物の信号を切り分けてから次に進む**

---

## 開発ロードマップ

### v9.x — 単一 ESDE の母体化（中間目標 1）— **達成**

| Step | 内容 | 状態 | 中間目標との接続 |
|---|---|---|---|
| 9.0 | Self-Referential Feedback Loop Phase 1 | **完了** | ループ成立確認 |
| 9.1 | Gamma Regime Sweep (Stage A + B) | **完了** | torque は系を支配しない。clamp 解放でも壊れない |
| 9.2 | Dual-Time Clock Separation + Step Probe | **完了** | torque の 2 相サイクル発見。設計意図と観測の不一致確認 |
| 9.3 | Deviation Detection → Sequential Torque | **完了** | 偏り検知 31% 改善。バッチ処理が攪乱の主因と特定。逐次化で NET -3.09→-0.82 |
| 9.3+ | Age順 + Longer Window | **完了** | age順で NET 初の正転（+0.08）。500 step/win で NET -0.09（完全平衡）|
| 9.3+ | Stress OFF + External Wave 耐性 | **完了** | Stress OFF で NET +0.06。Ext Wave A=0.5 でも崩壊せず。**中間目標1達成** |
| 9.4 | Label間カップリング + Perception Field | **完了** | coupling probe: 影響ゼロ（1-hop孤島問題）。perception field: 知覚圏定義。case study（L87/L101/L112） |
| 9.4 | Continuity + Worldlog | **完了** | world_J=0.988。spatial vs structural発見。step粒度追跡。存在層が認知の基礎を持つことを確認 |
| 9.5 | 3層構造 + 認知Phase 1（φ）| **完了** | 全label DETACHED。αが高すぎた。しかし異なるphase_sigのlabelのφが収束する発見 |
| 9.5 | Phase 1.5対称分析 + Convergence Detail | **完了** | Δ_phase一様分布。convergence時near_phase 34% vs divergence 18%。偏りの実体はθ分布 |
| 9.5 | Phase 2 Attention Map | **完了** | 接触記憶。near/far bias非蓄積。L101集中記憶。label間hotspot共有268ノード |
| 9.5 | Phase 3 Partner Familiarity | **完了** | decay=0.998。reciprocal pairs、familiarity network |
| 9.5+ | Phase 4 Disposition Vector | **完了** | 4 軸 (social/stability/spread/familiarity) 実装 (v9.8b) |
| 9.8a | Subject Reversal | **完了** | cid 主体反転、ghost/hosted/reaped lifecycle |
| 9.8b | Minimal Introspection | **完了** | 固定閾値 gain/loss tag、4 軸 disposition |
| 9.8c | Information Pickup | **完了** | death pool 拾得、TTL 延長、phase 距離競争 |
| 9.9 | Internal Axis (骨格) | **完了** | Rule 1-3、personal_range、drift、v99_ 33 列。4 軸閾値 audit で破綻判明 |
| 9.10 | Pulse Model & Subjective Surprise | **完了** | MAD-DT 動的閾値、50-step pulse、v10_ 20 列。L06 で 4 軸均等化確認 |

### v10.x — 複数インスタンス（中間目標 2-3）— **保留**

| Step | 内容 | 状態 | 中間目標との接続 |
|---|---|---|---|
| 10.0a | Membrane Coupling (1-State N=10000) | **保留** | cross link 問題 + 膜即死。label間カップリング確立後に再開 |
| 10.1 | seed 間情報伝達の観測 | 未着手 | 意思の疎通の前段階 |

### v11.x 以降 — 認知・言語（中間目標 4-6）

認知層のPhase 1-4完了後に設計。v9.5の認知層実験が先行。

---

## 現在の ESDE アーキテクチャ概要

### 物理層（Genesis canon、凍結）= 波

- 5000 ノード、71×71 グリッド
- 各ノード: E（エネルギー）、θ（位相）、ω（固有周波数）
- リンク: S（強度）、R（共鳴値）
- 5 つの力: 位相回転 → エネルギー流 → 共鳴 → 減衰 → 排除
- stress equilibrium: リンク数の EMA による動的平衡（後景化。存在層が肩代わり可能と確認）

### 存在層（virtual_layer_v9）= 粒子

- label: frozenset（ノード群への主張）。birth 時に固定。**魂。解放しない**
- torque: phase_sig に向けてノードの θ を引っ張る（**逐次適用、age 順**）
- semantic gravity: label 外近傍にも θ を引き寄せる（deviation-gated）
- share: territory に基づく存在の重み
- cull: share < threshold で死亡
- **v9 追加:** 系全体の died_share_sum → EMA → torque modulation
- **v9.3 追加:** deviation detection（D1/D2/D3 → gravity_factor）、逐次適用、age 順、500 step/window

### 認知層（v9.5〜v9.10）= 過程

- **存在層を根拠とし、存在層に影響しない純追加レイヤー**
- φ（認知位相）: α × sin(mean_theta_structural - φ)。Phase 1 完了。全label DETACHED
- attention map: 知覚圏内ノードごとの出現頻度。decay_rate = 0.99。**Phase 2 完了**: 接触記憶。label間hotspot共有
- partner familiarity: 他label との接触頻度。decay_rate = 0.998。**Phase 3 完了**
- disposition 4 軸: social/stability/spread/familiarity。**v9.8b で実装**
- **v9.8a:** cid 主体反転。label死亡 ≠ cid死亡。ghost 状態 (TTL 10 window)
- **v9.8c:** death pool pickup、TTL 延長。物理層不変
- **v9.9:** 内的基準軸の骨格 (Rule 1-3, v99_ 33列)。固定閾値の限界判明
- **v9.10:** Pulse Model + MAD-DT (v10_ 20列)。動的閾値で 4 軸均等化を確認

### 計測層（calibrate 側）

- local wave: decay sin 勾配（oasis/penalty 地形）
- C-light / D-light: 代表 label の内部状態追跡
- thaw pressure: frozenset 解凍圧の仮想測定
- resistance pattern: label 個体の抵抗様式分類

---

*v9.0 で自己参照フィードバックループを導入。v9.1-v9.2 で torque の 2 相サイクルを発見。
v9.3 で偏り検知 → バッチ処理の同時性問題を特定 → 逐次化 + age 順 + longer window + Stress OFF で中間目標1達成。
v10.0a の Membrane 接続は cross link 問題と膜即死で保留。
v9.4 で label 間影響ゼロを確認（1-hop 孤島問題）→ N-hop perception で知覚圏を定義。
continuity で world_J=0.988 / partner_J=0.81 を確認。存在層が認知の基礎を持つ。
worldlog で spatial(固定) vs structural(激変) を発見。「見える」と「触れる」は別の知覚。
v9.5 で3層構造確立: 物理=波、存在=粒子（frozenset固定）、認知=過程。
Phase 1（φ）は全label DETACHED → Phase 1.5 対称分析 → convergence detail で
near_phase偏り発見（conv 34% vs div 18%）。偏りの実体はノード位置ではなくθ分布。
Phase 2（attention map）は接触記憶として機能。near/far biasは蓄積されないが、
L101の集中記憶やlabel間hotspot共有268ノード（共有経験の原型）を確認。
認知は波形的な均質な動きではなく、偏りの追跡から生まれる。
v9.8 trilogy で cid 主体反転 (a)、固定閾値内省 (b)、death pool 拾得 (c) を段階追加。
v9.9 で内的基準軸の骨格 (Rule 1-3) を実装し、4 軸閾値の破綻を発見。
Taka 判断で Stage 2 (閾値再調整) を飛ばし Stage 3 (動的閾値) に直行。
v9.10 の Pulse Model + MAD-DT で L06 長命群が 4 軸均等 (soc 28%, sta 18%, spr 27%, fam 27%) に接近。
v9.9 の「familiarity 支配 82.7%」「spread 沈黙 67.6%」は固定閾値アーティファクトと確定。
stability 残差 (17.7%) の切り分け進行中。

---

## v9.11 — Cognitive Capture (事象捕捉フィルタの確立)

**目的:** cid が誕生時の構造 (M_c) と現在の環境 (E_t) を比較し、個体ごとに異なる確率で事象を捕捉する。物理層・存在層への介入なし。

### B_Gen と M_c

label birth 時に 1 回だけ算出し固定:

```
Pbirth = (1 / C(5000, n_core)) × ρ^(n-1) × r_core^(n-1) × S_avg^(n-1)
B_Gen  = -log10(Pbirth)
M_c    = (n_core, S_avg, r_core, phase_sig)
```

B_Gen バンド構造: n=2→12, n=3→19, n=4→26, n=5→34。バンド間ギャップ ≈7、n_core (組み合わせ項) が支配。

B_Gen は capture に直接入力しない (GPT 補正)。ログ指標として保持。

### E_t と Δ と capture

pulse ごとに知覚圏 (structural field, n_core hops) から自動抽出:

```
E_t    = (n_local, s_avg_local, r_local, θ_avg_local)
Δ      = Σ w_i × |M_c_i - E_t_i| / norm_i  (Weighted L1, phase は circular)
P(cap) = 0.9 × exp(-2.724 × Δ)
```

重み均等 (0.25×4)。cold start (pulse 1-3) は判定保留。

### 4 層構造の確認

| 層 | 役割 | v9.11 での確立 |
|---|---|---|
| 物理層 | 生成基盤 | 不変 |
| 存在層 | θ torque のみ | 不変 |
| 認知層 | 観察・比較・捕捉 | **B_Gen + capture で確立** |
| 意識層 (将来) | 認知の検証 | v10.x 以降 |

B_Gen の導入により「認知層から θ への介入」の誘惑が構造的に消滅した。

### 結果 (48 seeds short + 5 seeds long)

- capture_rate mean ≈ 0.38 (設計通り)
- 軸寄与: phase 39% + r 34% = 72%、n 14%、s 13%
- L06 長命群 (114 cids): capture_rate 0.307、n_core=5 が 61%、Δ mean 0.414
- B_Gen バンド短長一致、λ=2.724 運用妥当

---

## v9.12 — Audit Phase (実装変更ゼロ)

v9.12 は新機構の実装ゼロ、既存データの分析と設計文書化のみ。

### Phase 1: L06 時系列分析

**Δ は i.i.d.** — 自己相関 ≈ 0 (全 lag)。mismatch は蓄積しない。L06 capture 低下は n_core 構成効果 (n_core=5 は構造的に Δ ≈ 0.43 で定常)。

spike (Δ 上位 10%) → capture 15.4%、low → 50.9%。乖離と capture の逆相関は明確。

### Phase 2A: コード解析

1. **phase+r 72% の原因**: NORM_N=86 による d_n 圧縮 (C 仮説確定) + S_avg の物理的定常性 (A 仮説確定)。d_r と d_phase は無相関 (r=0.008)。B 仮説 (E_t 定義偏り) 否定。
2. **n≥6 欠落**: S≥0.20 連結成分の接続性 (主因) + 50% overlap フィルタ (副因)。コードに上限なし、動力学的帰結。

### Phase 4: 未決境界問題

Taka 発言「並列基準原理」と「構造と数式の分離統合」を設計原理として記録。認知/意識の境界に関する 5 つの未決問題をリスト化。詳細: `docs/v912_unresolved_boundary_questions.md`。

### v9.13 への方針転換

Taka 判断: 「S≥0.20 は神の手。動的均衡の哲学がある以上どこかで切り捨てなければならない。後回しにするほど調整が大変」

→ v9.13 = **S≥0.20 hard threshold の撤去、Pbirth ベースの確率的 birth への移行**。Gemini に architecture 設計を依頼 (`docs/v913_gemini_design_request.md`)。

---

## 教訓 (v9.11-v9.12 追加)

66. B_Gen を capture に直接入力しない判断が v9.11 の最大の architectural 成果。n_core バンド支配が capture 差を飲み込む
67. Δ が i.i.d. なら retention の価値は「予測」ではなく「主観的基準形成」
68. NORM_N (正規化定数) の過大設定は軸寄与を構造的に歪める。audit は実験前にコードを読むのが先
69. 「修正すべき」と即断せず、L06 のような観測結果を asset として活用する視点
70. 設計定数 (S≥0.20) の撤去は早い方が上位層への波及が少ない
71. 実験回すより先にコード解析。原因がコードに見えたら実験は確認に格下げ

---

## v9.13 — Persistence-based Birth (S≥0.20 撤去完了)

v9.12 で Taka が明示した「S≥0.20 hard threshold は神の手」を撤去し、Genesis 原理 (閉路=共鳴=構造の核) に直接基づく birth 条件を確立。

### Birth 条件の変更

**v9.11 まで** (2 経路):
1. S≥0.20 島 (連結成分)
2. R>0 ペア即 label (経路 B)

**v9.13**:
1. 各 link の age_r (連続 R>0 step 数) を追跡
2. age_r ≥ τ の link の connected component (size≥2) を label 化
3. 経路 B 廃止、50% overlap フィルタは維持
4. τ = 50 / 100 の 2 条件を試験

### Step 0 Audit の発見 (2026-04-16)

- 全 link の **99.64% は一度も R>0 に参加しない** (R=0 のまま死ぬ)
- 残り 0.36% のみが閉路に参加
- v9.11 label の約 **2/3 が R=0 リンク構成の「見かけ構造」** だったことが判明

Taka 判断: **「数より純度。結果を受け入れる。」**

### 本番 Run 結果 (2026-04-17)

| 項目 | v9.11 short | v9.13 τ=50 | v9.13 τ=100 |
|---|---|---|---|
| seeds | 48 | 24 | 24 |
| total labels | 3,165 | 1,034 | 832 |
| labels/seed | 65.9 | 43.1 | 34.7 |
| **R>0 純度 (birth 時)** | — | **100.0%** | **100.0%** |
| age_r_min mean | — | 122.1 | 159.1 |
| lifespan mean | 6.6w | 12.0w | 13.2w |

### n_core 分布の激変

| n_core | v9.11 short | v9.13 τ=50 | v9.13 τ=100 |
|---|---|---|---|
| 2 | 67.1% | 22.5% | 27.8% |
| 3 | 7.4% | 19.3% | 20.4% |
| 4 | 9.1% | 19.8% | 20.8% |
| 5 | 16.3% | 38.1% | 30.9% |

v9.11 の n=2 主体 (67%) は経路 B + R=0 混入のアーティファクトだったことが確定。純粋な Genesis 原理下では n=5 が最頻、n=2 は 22-28%。

### 軸寄与の均等化

| 軸 | v9.11 | τ=50 | τ=100 |
|---|---|---|---|
| n | 13.5% | 26.8% | 25.1% |
| s | 13.4% | 9.9% | 11.0% |
| r | 34.0% | 29.7% | 30.6% |
| phase | 39.1% | 33.7% | 33.3% |
| phase+r | 73.0% | 63.4% | 63.9% |

**v9.11 の「phase+r 72% 支配」も n_core 構成効果だったことが判明**。n_core 分布が均されると n 軸寄与が約 2 倍に。

### B_Gen バンドの上方シフト

n≥3 で v9.11 比 +1.3〜+1.9 のシフト。同じ n_core でも persistence 要件を満たす component は構造階層が深い。τ=50 と τ=100 の差は微小。

### capture_rate

| 指標 | v9.11 | τ=50 | τ=100 |
|---|---|---|---|
| capture_rate 全体 | 0.397 | 0.346 | 0.345 |

全体値の低下は n_core 構成効果 (v9.11 は capture しやすい n=2 が 67%)。n_core 別に見ると n=3, 4, 5 で τ=50 はむしろ向上、τ=100 は n=2 で 0.442→0.454 に向上。

### n≥6 欠落は解決せず

S≥0.20 撤去後も大型 label の出現頻度は v9.11 と同水準 (各 τ で 1-2 個)。v9.12 指摘の 3 要因のうち、**50% overlap フィルタと非空間的リンク形成が残存制約**として効いている。

### 副次的発見 (断定せず記録)

τ=100 で n=5 比率が減り (38%→31%)、n=2 が増加した (23%→28%)。素朴には「閾値が厳しくなれば大型構造が残る」と予想するが逆。2 ノードの簡潔な結合の方が persistence 要件を満たしやすい可能性。

### τ 選定

両 τ とも機能的に妥当。両 R>0 純度 100%、capture ほぼ同値、軸寄与同一。決定打はなく、Taka 判断待ち。

---

## v9.13 — 認知層の方向性確定 (Taka 2026-04-16)

### 基本原則

> 認知層は物理層を支配しない。物理層の動きを予測しながら認知的に自分の存在を生かす方向。

**効果は統計的に多少の差**。Taka の比喩: 健康に気をつけても寿命は 10 倍 100 倍変わらない、だが個体差はある。ESDE の認知層もその程度。

### CID の記憶の所在

> **CID の記憶は物理層の中に既にある。足りないのは「記憶を作る仕組み」ではなく「物理状態を記憶として読む関数」。**

- 外部 dict への蓄積は「私たちの記録」であって「CID の記憶」ではない
- cid のメンバーノードの θ 分布、メンバーリンクの S/R 分布自体が物理的痕跡
- 次フェーズ (v9.14/v10.0) の主題

### 次ステップの候補

検討順序: 候補3 → 候補1 → 候補2

| 候補 | 内容 | Aruism 整合度 |
|---|---|---|
| **候補3** | 物理状態そのものを記憶の読み出し関数で解釈 | 最高 |
| 候補1 | M_c を毎 pulse で物理状態から再読み込み | 高 |
| 候補2 | 過去の E_t を移動平均として保持 | 中 |

### 既存機能の棚卸し

**Taka 原則: 「無駄だから切る」は無駄な発想**

| 機能 | 方針 |
|---|---|
| pickup (v9.8c) | 効果薄だが **休眠保持**。将来の記憶蓄積実装で活用候補 |
| Semantic gravity + deviation | v9.14 以降で検証予定、保持 |
| Stress decay, Compression, Torque Factor | 無効化済 (OFF のまま) |

### AI 間文書の言語ルール (Taka 2026-04-16 撤回)

運営原則 v2 の「AI 間文書は英語」を撤回。全資料を日本語 md に統一。

### 開発ロードマップ

| Phase | バージョン | 内容 | 状態 |
|---|---|---|---|
| 掃除 | v9.13 | S≥0.20 撤去、persistence-based birth | **完了** |
| 記憶の読み出し | v9.14 or v10.0 | 物理状態を記憶として読む関数 | 次 |
| 記憶の蓄積と再生 | v10.x | pickup 活用、他者の経験取り込み | 構想 |
| 意識層 | v10.x 以降 | 認知層の解釈を検証 | 構想 |
| 外部コネクター | v11.x 以降 | 外部情報を物理現象として注入 | 構想 |

---

## 教訓 (v9.13 追加)

72. shadow 推定と本番の差は window 数で説明可能なことが多い。「予測外れ」と即断せず換算を確認する
73. n_core 分布のアーティファクト依存度は高い。v9.11 の「phase+r 72% 支配」などの主要所見が birth 方式変更で崩れた。同種の所見を再確認する際は下地の n_core 分布を必ず見る
74. 閾値を厳しくすれば大型構造が増えるとは限らない。τ=100 で n=5 比率が低下、n=2 が増加。persistence 要件は 2 ノードの方が満たしやすい可能性
75. Taka の感想を過大解釈しない。「思ったより良い」は成果の大きさではなく「認知層テスト継続に十分な母数」という実務的安心だった
76. 「無駄だから切る」禁止。機能削除より「どう活かすか」を考える (Taka 原則)
77. 認知層の効果は劇的にしない。統計的に多少の差が自然 (Taka 原則)
78. CID の記憶は物理層の中に既にある、外部 dict に蓄積しない (Taka 方針転換)

---

最終目標は「神の手を介さずに認知・意味・社会性が創発するモデル」。
当面のゴールは「私たちと会話ができるシステム」。

v9.13 で S≥0.20 の神の手を撤去、Genesis 原理に沿った label 選別を確立。v9.11 の主要所見の多くが前提を改めて再解釈された。次フェーズ (v9.14/v10.0) は「CID が物理状態を記憶として読む関数」の設計に向かう。*
