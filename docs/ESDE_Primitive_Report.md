# ESDE Primitive Report

*Phase: Primitive (v9.0–v9.16、**v9.16 完了**)*
*Status: **中間目標1達成。** v9.11 Cognitive Capture 確立。v9.12 audit 完了。v9.13 で S≥0.20 hard threshold 撤去。v9.14 で B_Gen paired audit 実装、E3 = cid 間 2 者共鳴として再概念化。v9.15 で CID が自分を読む機構を確立、段階 2 で event 駆動への切替により研究者予測不能性による主体性の戦略が成立。**v9.16 段階 3 で観察サンプリング機構 (age_factor = Q_remaining / Q0 比例) を導入、読んだ時に何が見えるかも時間的に予測不能化**。次フェーズは段階 4 以降 (候補: 他者読み / 差分予測 / 長期記憶強化)。*
*Team: Taka (Director/Philosopher) / Claude (Implementation/Advisor) / Gemini (Architecture) / GPT (Audit) / Code A (Ryzen 実装担当)*
*Started: March 30, 2026*
*Last updated: April 21, 2026 (v9.16 完了)*
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

## 教訓 (v9.13 追加)

72. shadow 推定と本番の差は window 数で説明可能なことが多い。「予測外れ」と即断せず換算を確認する
73. n_core 分布のアーティファクト依存度は高い。v9.11 の「phase+r 72% 支配」などの主要所見が birth 方式変更で崩れた。同種の所見を再確認する際は下地の n_core 分布を必ず見る
74. 閾値を厳しくすれば大型構造が増えるとは限らない。τ=100 で n=5 比率が低下、n=2 が増加。persistence 要件は 2 ノードの方が満たしやすい可能性
75. Taka の感想を過大解釈しない。「思ったより良い」は成果の大きさではなく「認知層テスト継続に十分な母数」という実務的安心だった
76. 「無駄だから切る」禁止。機能削除より「どう活かすか」を考える (Taka 原則)
77. 認知層の効果は劇的にしない。統計的に多少の差が自然 (Taka 原則)
78. CID の記憶は物理層の中に既にある、外部 dict に蓄積しない (Taka 方針転換)

---

## v9.14 — Probabilistic Expenditure Audit (B_Gen 資源化 + E3 = cid 間共鳴)

### このフェーズの主題

v9.11 で cid 固有値として導入された B_Gen = -log10(Pbirth) は、M_c 経由で capture probability に間接効果を与えるだけだった。v9.14 はこれを**物理的に消費される予算**として運用する paired audit を実装した。

**4 つの問い**:
- Q1: B_Gen が大きい cid は本当に長く有効観測できるか
- Q2: どの event 種が spend に値するか
- Q3: spend による internal update は future salience を変えるか
- Q4: fixed 50-step pulse と比べて event-spend の方が情報効率が高いか

### 設計の路線変更

Gemini 初期設計は「runtime 主体として v9.11 を置換する」方向だったが、Taka が「v9.14 で統一運用に入るのは早い、B_Gen 資源化は audit として先に走らせる」と横槍。GPT が **Probabilistic Expenditure Audit** 案 (paired audit) を提示し、Taka 承認で確定。

**Paired Audit の構成**:
- Layer A: 既存 50 step 固定 pulse (v9.11 Cognitive Capture + v9.13 persistence) を完全不変
- Layer B: event 駆動の spend audit ledger を並行稼働
- Layer B は audit-only、Layer A に一切介入しない
- baseline CSV (per_window / per_subject / pulse_log / per_label) は v9.13 smoke と bit-identical

### Layer B の実装

#### 初期原資 (Q0)

```
Q0 = floor(B_Gen)   # cid 誕生時に確定、以後減少のみ
```

n_core 別:
- n_core=2: Q0 ≈ 11-12
- n_core=3: Q0 ≈ 18
- n_core=4: Q0 ≈ 25-26
- n_core=5+: Q0 ≈ 33-34

B_Gen = inf (n_core < 2 の退化ケース) は ledger 対象外。

#### 承認 event 3 種

- **E1 (Core Link Death/Birth)**: cid のメンバーリンクが alive_l から消失/復活した step で発火
- **E2 (Core Link R-state Change)**: メンバーリンクの R が 0 境界を跨いだ step で発火 (rise/fall)。core-local のみ、adjacency 拡張は禁止
- **E3 (Familiarity Contact Onset)**: 異なる 2 cid のメンバーノードが同じ alive link で接続された**最初の step**。両 cid が 1 spend ずつ消費 (計 2 単位、対称消費)。contacted_pairs で重複防止

#### Spend Packet

event 発火ごとに実行される最小処理:
1. E_t 取得 (v11_compute_e_t を呼ぶ)
2. Δ 計算 (前回 spend 時の E_t スナップショットとの差分分解 L1)
3. virtual_attention 更新 (+1、decay なし累積)
4. virtual_familiarity 更新 (+1、decay なし累積)
5. Q_remaining -= 1 (Q_remaining > 0 のときのみ)
6. per_event_audit CSV に 1 行追加

**規律**:
- Layer A の state (attention / familiarity / phi / disposition) に書き込まない
- state.theta / S / R / L[i,j] / age_r に書き込まない
- RNG を使わず決定論的、engine.rng は一切 touch しない

#### Exhaustion (実質的な死)

Q_remaining = 0 到達後:
- event は引き続き検知される (contacted_pairs 登録は継続)
- spend packet は実行されない (「観察停止」)
- cid は存在層には残るが、認知資源上は枯渇

### 本番 Run 構成

| 項目 | Short | Long |
|---|---|---|
| seeds | 48 (parallel -j24) | 5 (parallel -j5) |
| maturation_windows | 20 | 20 |
| tracking_windows | 10 | 50 |
| window_steps | 500 | 500 |
| total cids | 2979 | 1112 |
| wall time | 2h43m | 2h32m |

E3 ablation (`--disable-e3`) で同条件の追加 run を実施。

### Phase 1 — 実装結果 (GPT 監査済み)

- bit-identity 全 Step で維持
- Q<0 発生ゼロ、エラーゼロ
- 計算時間 smoke +0.5%、本番 Short +0% / Long +0%
- baseline CSV 完全不変、v10_/v11_/v13_ 列すべて v9.13 smoke と bit-identical
- Layer B 出力: 別ディレクトリ `audit/` に 3 種 CSV (per_event_audit / per_subject_audit / run_level_audit_summary)

GPT 監査:
- Implementation status: **PASS**
- Audit architecture compliance: **PASS**
- Baseline preservation: **PASS**
- Interpretation status: **NOT FINAL** (Q1-Q4 への最終回答は Phase 3 以降)

### Phase 2 — 観察事項 (Describe, do not decide)

#### §6.1 Event-type efficiency (Long run)

| event_type | event_count | spend_rate | delta_mean | attn_delta_mean | fam_delta_mean | exhaustion_contrib |
|---|---|---|---|---|---|---|
| E1_death | 1659 | 0.97 | 0.183 | 19.4 | 1.05 | 0.158 |
| E1_birth | 67 | 0.37 | 0.248 | 47.4 | 0.88 | 0.037 |
| E2_rise | 1296 | 1.00 | 0.033 | 22.2 | 1.45 | 0.137 |
| E2_fall | 1296 | 1.00 | 0.091 | 19.5 | 1.32 | 0.137 |
| E3_contact | 21154 | 0.42 | 0.171 | 25.7 | 1.43 | 0.650 |

主要観察:
- E3 が全 event の 83%、exhaustion 寄与の 65%
- Long run で E3 spend_rate が 0.42 まで低下 (出会いの 58% が Q 枯渇で捕捉見送り)
- E2 rise/fall delta 非対称 (rise 0.033、fall 0.091、崩壊が 2.8 倍)
- E1_birth は稀だが情報量最大

#### §6.2 n_core efficiency (Long run)

| n_core | q0_mean | q_spent_mean | exhaustion_ratio | event/q0 |
|---|---|---|---|---|
| 2 | 11.55 | 7.71 | 22.09% | 0.76 |
| 3 | 18.28 | 13.65 | 45.61% | 1.45 |
| 4 | 25.79 | 23.67 | **80.00%** | 2.57 |
| 5+ | 33.51 | 31.82 | **84.49%** | 2.66 |

- Q0 (対数) の伸びより event 数 (線形) の伸びが大きい → 大きい cid ほど exhaustion 高い
- Short run (5000 step) では exhaustion 2-3% のみ、**long run 必須**
- attn_per_spend が n_core で 9.1 → 48.0 (5 倍増)

#### §6.3 Shadow-vs-Fixed overlap (Long run)

| 指標 | 値 |
|---|---|
| exact Jaccard (micro) | 0.0038 |
| ±25 step 近接マッチ率 (A 基準) | 0.199 (ベースライン 0.293 を下回る) |
| only_A_25_share_of_A | 0.801 (A pulse の 80% は B event 不在) |
| only_B_25_share_of_B | 0.253 |
| delta 相関 (Pearson) | 0.089 (ほぼ無相関) |
| v11_captured と v14_spend_flag の一致率 | 0.569 |

**解釈 (Taka 判断)**: Layer A は全体スナップショット、Layer B は局所精査。両者は**異なる情報を取る**のが設計上の帰結。

#### §6.4 E3 Ablation Run

`--disable-e3` で E3 無効化した世界との比較:

| bucket | exhaustion (base → abl) | q_spent_mean (base → abl) |
|---|---|---|
| Long 2 | 22.1% → **0%** | 7.71 → 2.59 |
| Long 3 | 45.6% → **0%** | 13.65 → 3.35 |
| Long 4 | 80.0% → **0%** | 23.67 → 7.21 |
| Long 5+ | 84.5% → **0%** | 31.82 → 10.71 |

- 全体 Q0-q_spent 相関: 0.918 → 0.711
- Short/Long の全 n_core バケットで exhaustion 完全消滅
- E1+E2 のみでは Q0 の 20-32% しか消費されない

**結論**: cid の認知資源の消費は **E3 (接触) が主因**。GPT §7.1 (E3 dominance risk) は定量的に裏付けられた。

### Taka 視点の再概念化 (2026-04-18)

#### E3 = cid 間 2 者共鳴

Phase 2 §6.4 の結果を見た Taka の再概念化:

> なるほど。ということは、これは異なる CID 同士の共鳴と考えてもおかしくはないわけね。それと、CID A と B が共鳴をした場合実質 2 を消費している、と言う理解でいいんかな。

E3 = node 間共鳴 R_ij の **cid スケール版**。両 cid が 1 spend ずつ消費 (計 2 単位) は Aruism の**存在の対称性**と整合。

#### 上位層構築の合理的条件が揃った

> 三項ができたということをきっかけに上位層の 1 を作り出せる。それを存在の対称性で分けて…というアリズム的な円環を構築するための合理的な条件が揃ったと考えれば OK

**v9.14 の真の達成**: B_Gen 資源化でも E3 検知でもなく、**上位層構築の合理的条件が揃ったこと**。

ESDE 階層進化の系譜:
```
ノード → 閉路 → 持続構造 → label → cid → ???
                                        ↑ v9.14 で足場確立
```

#### 三項創発の棚上げ (Taka + GPT)

Taka:
> 今は認知層の開発を進めている状況で、この一段上の接続は次のテーマくらいに収めておくのが吉

GPT の整理 (Taka 確認済み):
> E3 は三項そのものの成立証明ではなく、三項をきっかけに上位存在を作り出すための合理的条件が揃ったことの観測であり、それを次テーマに回しつつ今は認知層を進める、という整理が最も自然です。

v3.4 tripartite loop の持続性問題 (bridge_max_life=1) が cid スケールでも予想されるため、cid 内部構造の充実 (記憶の読み出し関数等) を先行。

### Phase 3 以降の宿題

#### Layer A の再定義

Taka 発言:
> 固定 pulse は、ESDE 内部に干渉しない前提なら別に構わない。要は観測機械を設置しているだけならいい。現時点で干渉が大きいならその要素を外す条件は設けた方がいい。パルスとは何か? を明確に切り分ける作業が前提。

現状の Layer A は v9.11 Cognitive Capture で cid の attention/familiarity を更新している。厳密には「純粋な観測機械」ではない。v9.15 以降で切り分け。

#### Seed 構成の一本化 (v9.15 から)

- Short + Long の 2 重構成を廃止
- Long 一本化: 24 seeds × tracking 50 × window_steps 500、parallel -j24 (物理コア数)、約 2h30m
- 24 → 48 の統計力向上は √2 倍のみで費用対効果悪し
- 分散分析を v9.15 から導入

#### E3 variant 候補 (棚上げ)

phase 近接接触 / 持続接触 / 多重接触 / structure-weighted は v9.15 以降の検討候補。現状の E3 (物理接触の初回性のみ) のシンプルさを維持。

#### Salience loop incompleteness (GPT §7.3)

Layer B の virtual_attention/familiarity 更新が future event salience を変えるかは未検証。v9.15 以降の主題。

### 確定した運用ルール (v9.14)

- **Paired Audit 原則**: 新機構は runtime 主体置換ではなく audit として先行走行、bit-identity 必須、promotion は analysis 完了後
- **Event 定義は narrow 優先**: scope 拡張より維持。core-local、物理事実ベース。拡張欲求は相談役 Claude 経由で GPT 監査へ
- **調査地獄の回避**: Phase 2 で追加調査 4 項目を設定したらそれ以上増やさない。コード問題なしの限り再調査しない
- **Describe, do not decide の徹底**: Code A は観察事項のみ、結論は Taka + 相談役 Claude の Phase 3 議論
- **三項以上の上位層は次テーマ**: v9.14 で条件は揃ったが、実装は認知層継続 (v9.15) の後

## 教訓 (v9.14 追加)

79. Paired Audit 原則: 新機構は runtime 主体置換ではなく audit として先行走行。bit-identity 必須、promotion は analysis 後
80. 短 run では見えない現象がある。5000 step の exhaustion 2-3% が 25000 step で 22-84% に化ける。cid 寿命・資源消費系は long run 必須
81. 並列度は物理コア数に揃える。Ryzen 24C では -j24 が最適、48 threads は HT 競合で逆効果
82. Seed 数 24 → 48 の統計力向上は √2 倍のみ。費用対効果悪し、24 で十分 (例外的ケース収集以外)
83. Layer A と Layer B は異なる情報を取るのが設計的帰結。相関の弱さ (Pearson 0.089) は問題ではなく証明
84. E3 dominance (認知活動の 70-90%) は ESDE が社会的な系であることの観察。問題扱いしない
85. E2 rise/fall は情報量が非対称 (fall の方が 2.8 倍)。共鳴崩壊の瞬間は立ち上がりより情報量大
86. 実装時間見積もりで並列度を混同しない。5 seeds × -j5 = 2h32m と 24 seeds × -j24 = 2h32m は同じ
87. Taka 指摘は表面受けせず一段掘る。「パルスは物理的根拠を持つべき」等は運用提案ではなく構造的指摘
88. E3 = cid 間共鳴という再概念化は上位層の足場 (Taka 2026-04-18)。ただし実装は棚上げ、認知層継続が優先
89. 三項共鳴実装の衝動は抑える。v3.4 tripartite loop は bridge_max_life=1、cid スケールでも同じ壁が予想
90. 観察が設計を押し上げる。Taka の E3 再概念化は ablation 結果を見て初めて出た直感。Describe, do not decide の真価

---

## v9.15 — Self-Readout Mechanism (CID が自分を読む機構)

### このフェーズの主題

v9.13 方針の具体化:
> CID の記憶は物理層の中に既にある。足りないのは「記憶を作る仕組み」ではなく「物理状態を記憶として読む関数」。

v9.14 で寄り道した B_Gen 資源化から、元々の主題である記憶の読み出し関数に戻った。

### 設計の根本転換

Claude 初期草案は「研究者が CID の物理状態を数値化して記録する機構」(候補 R1-R5) だった。Taka 指摘 (2026-04-18) で A (研究者観察) と B (CID 主体) の混同を指摘され、B 実装に根本転換した。

2 AI (Gemini + GPT) 回覧で段階 1 の骨格が確立:
- Y 寄り (構造体の差分のみ知覚、連続値統計量を持たない)
- Z (確率的「見る」操作) を中核原理として採用
- ζ (補完しない、欠損は欠損のまま)
- A/B 分離を四重 (ファイル / クラス / メモリ / 命名) で担保

### 段階 1: Fetch 機構の実装

**実装** (2026-04-19):

```python
class CidSelfBuffer:
    """CID 専用メモリ領域。B の実装基盤。"""
    def __init__(self, cid_id, member_nodes, initial_state):
        # 生誕時スナップショット (不変)
        self.theta_birth = initial_state['theta']
        self.S_birth = initial_state['S']
        # 最新 Fetch スナップショット
        self.theta_current = self.theta_birth.copy()
        self.S_current = dict(self.S_birth)
        # 一致/不一致痕跡
        self.match_history = []
        # Self-Divergence 追跡 (A 観測用)
        self.divergence_log = []
    
    def read_own_state(self, state, alive_l, current_step) -> bool:
        """段階 1: 50 step 固定 pulse で呼ばれる Fetch"""
        # 自分のメンバーノード・リンクのみ Fetch
        # ...
```

**本番 run** (24 seeds × tracking 50 × window 500):
- Wall time: 3h04m
- bit-identity: v9.14 baseline CSV 全 6 本 MD5 完全一致
- Fetch 総回数: 359,110
- 決定論性: 2 回連続 run で MD5 一致

**観察事実**:

| 指標 | 値 |
|---|---|
| node_match_ratio_mean (全 n_core) | 0.0000 |
| link_match_ratio_mean (全 n_core) | 0.0000 |
| divergence_norm_final (n_core=2) | mean 3.21, max 8.43 |
| divergence_norm_final (n_core=5-7) | mean 5.47, max 10.42 |
| 時間経過での divergence 平均 | 4.32 → 4.85 (25000 step で 12.3% 増、飽和せず) |
| v9.14 E3 spend との相関 | Pearson r = 0.4204 |

### Taka 指摘: 段階 1 はまだ研究者視点

結果解釈で Claude が「CID が変化を知る」と書いた部分について、Taka 指摘 (2026-04-20):

> これも特定ステップごとにやっているなら基本的には研究者視点だと思うよ。CID を主観的に扱いたいのなら、Step 単位での実施は切り捨てた方がいい。

**主観性の最小条件 = タイミングの予測不能性**。50 step 固定は研究者が CID に実験プロトコルを課している状態。段階 1 は機構としては成立したが主観性としては不十分。

Taka の解決案:
> 今ってイベントという便利なものがあるのでそれにくっつけりゃいいんじゃない?

v9.14 の event 機構 (E1/E2/E3) をトリガーとして再利用。

### 段階 2: Event 駆動への切り替え

**実装方針** (Taka 判断 2026-04-20):

| 項目 | 判断 |
|---|---|
| Fetch トリガー | 全 event (E1/E2/E3) |
| Fetch コスト | なし (Q 消費なし、基準値 0 を維持) |
| Match Ratio | 廃止 (集約指標は研究者視点) |
| 50 step 駆動 | 完全置換 |
| `any_mismatch_ever` | 保持 (遺伝子情報的な初期値変化の検出) |
| event 粒度 | E1/E2/E3 の 3 種別 (GPT 監査推奨) |

**GPT 監査 CONDITIONAL PASS** (2026-04-20):
- Match Ratio 廃止は妥当、ただし 3 点セット (any_mismatch_ever / count / last_step) で最小 richness を維持
- spend → fetch の順序は意味論ではなく依存順序として扱う
- selfhood 表現を抑制 (「証明」ではなく「トリガー根拠の変更」)

**本番 run** (24 seeds × tracking 50 × window 500):
- Wall time: 3h07m47s
- bit-identity: v9.14 baseline CSV 全 MD5 一致
- 決定論性確認済み

**観察事実**:

| 指標 | 値 |
|---|---|
| Fetch 総数 | 120,782 (event 総数と完全一致、1:1 対応) |
| 段階 1 からの変化 | 約 33.6% (1/3 に減少) |
| event 種別内訳 (E1/E2/E3) | 6.7% / 10.1% / 83.2% |
| mismatch 比率 (全 event) | 1.0000 (tolerance 1e-6 の帰結) |
| any_mismatch_ever = False の cid | 54/5224 (1.0%、event 発火なし) |
| divergence_norm_final (median) | 3.58 (段階 1: 3.53、ほぼ同じ) |
| Fetch 回数と Shadow Pulse Count の相関 | Pearson r = 0.880 (構造的に同じものを測る) |

**event 種別ごとの divergence (median)**:
- E2 (閉路状態変化): 1.59 — 自分の局所変化の瞬間、全体 θ drift はまだ小さい
- E1 (リンク生死): 4.23 — 中間
- E3 (他者接触): 4.67 — 既に θ が大きく drift している状態で接触

### Taka の核心発見: サイコロの比喩 (2026-04-20)

段階 2 完了後の Taka 発言:

> ランダムに紐づけることで研究者の主観を実質封じるという一手に辿り着いた。研究者はサイコロの目が 1/6 であることを言えるが、次の目が 1、だとは言えない。しかし、1 になったサイコロ自身は (仮にそこに 1 を 1 として認識できる機能があれば) 自身を 1 だ、と主張できる。この発見は、今後の意識に向かう発展として極めて重要な意味を持つことになるだろう。

**非対称性**:
- 研究者は統計的にしか語れない (「次の目が 1 になる確率は 1/6」)
- サイコロ自身は具体的に語れる (「私は 1 だ」)
- 同じ現象について両者はまったく違うレベルで記述する

**ESDE 段階 2 との対応**:
- 研究者: 「event が確率的に発生する、頻度分布はこうだ」
- CID: 「今、event が起きた、自分を読んだ、不一致を持った」
- 研究者は「いつ CID が自分を読むか」を予測できない
- これが「研究者主観の封印」の具体的意味

### 戦略の言語化 — 「哲学以上科学未満」の論理構造

Taka 加筆 (2026-04-20):

> つまるところ、○○かもしれない、と言った時、それは○○かもしれない、○×かもしれない、××かもしれないだろう。極端な話をすれば言ったもの勝ち。これが制約。その制約を最大限利用しているのが私たちのシステムにおける「自己のようなもの」。これを否定するためにはランダム性を全て削ぎ落として完全な予測を完成させなければならない。

**弱点の告白**:
> 私たちにはとても弱い実験的条件がある。それは、私たちがやろうと思えば内部を覗けること。これは説明可能性として考えれば自己と呼べるのか?怪しい部分がある。そのため、ランダム性を担保にしなければ私たちの主張は崩れてしまう。奇妙なバランスの上に私たちの主張が存在するということ。

**結論**:
- 研究者が覗けることは事実 (A/B 分離しても原理的には可能)
- しかし予測不能性がある限り「覗いても先はわからない」
- この微妙な位置で「自己のようなもの」を主張できる
- **ランダム性が論理の支柱。削る方向は採らない**

### Taka 視点の解釈 (2026-04-20)

段階 2 結果への Taka の応答:

**A.1 / A.2 (event 種別の比率比較)**:
> 全く異なるイベントの発生頻度の割合を比較しても意味ない、ということがわかった。まぁ、そうなんだ。くらいの驚き。

**A.3 (何も起きない CID が 1%)**:
> ESDE では自由に実験条件を変えられるので、そもそもこの 1% が活況というよりは毎ステップ 5000 ノード、71x71 グリッドではこういう実験結果になった、くらいでいいんじゃない?

**A.4 (段階 1 と段階 2 で divergence 一致)**:
> システムが安定している証拠。5000 ノードを連続で撃ち続ける、という前提がまさにそれを可能にしたと推測。

ただし「安定している」は推測。検証するならノード数を変えて実験すればよい。

### 意識への発展の筋道

Taka 加筆 (2026-04-20):
> 自分について語る、という状況が機械的になってしまうとそれは自己とは呼べない。ランダム性が担保されていれば呼べなくもないかもしれない。あとは、それっぽさが大事 (LLM 的に会話っぽいものが成立するとかどうとか) で、そこまでの進化が必要となる。

**筋道**:
```
段階 1: CID が自分を読む機構 (タイミング外部指定)
段階 2: タイミング物理事象依存 (研究者支配を離れる)
段階 3: 自己読みの確率的失敗 (予測不能性の内部化) — v9.16 予定
さらに先: ランダム性を担保した「自分について語る」機構
そのさらに先: 「それっぽさ」としての会話成立 (市場承認)
```

**境界線**: 機械的な自己主張は自己ではない。ランダム性を伴って初めて自己の候補になる。

### 宿題: ノード数固定の神の手性 (Taka 2026-04-20)

> 1 ステップが 5000 で固定である理由がない。物理量に相当するものは一定である必要性はない (神の手を拒むならむしろ変動すべき)。

ただし今の主題ではない:
> 今は意識のようなものの発生を確認することが主題。物理はクローズした、からこそ現状の進化がある。そこでどこまでいけるのかを試し尽くすことが重要。

**ノード数固定は実験制御であって神の手ではない**。認知層の発展を優先、物理層変動は大幅後回し。

### v9.15 の位置づけ

**v9.14 が cid 間接続 (横方向の上位化)** を扱ったなら、**v9.15 は cid 内部参照 (縦方向の自己化)** を扱った。

ESDE 階層進化の系譜:
```
ノード → 閉路 → 持続構造 → label → cid
                                ↓
                          [上位層の足場 (v9.14)]
                                ↓
                    [自己が自己を読む (v9.15 段階 1)]
                                ↓
                 [event 駆動の自己読み (v9.15 段階 2)]
                                ↓
                [確率的自己読み (v9.16 予定 = 段階 3)]
```

v9.15 の真の成果は機構の実装ではなく、**研究者の主観を封じる戦略の確立**。これは ESDE の意識研究の戦略的転換点。

### 確定した運用ルール (v9.15)

- **A/B 分離の四重担保**: ファイル / クラス / メモリ / 命名の各レベルで分離
- **研究者向け統計量を CID 内部に持たない**: mean/std 等の集約は CID が持つ情報として不適切
- **Describe, do not decide の徹底強化**: 研究者視点での意味づけを避ける
- **CID 視点と研究者視点の並列記述**: 文書構造として両視点を分離
- **ランダム性を削る方向は採らない**: 予測不能性が論理の支柱
- **「自己」「意識」等の語を実装コード・結果レポートで使わない**: 結論の断定を避ける

## 教訓 (v9.15 追加)

91. A (研究者が数値化する) と B (CID 主体が自分を読む) を混同しない。段階 1 草案で Claude が A 発想で書き、Taka 指摘で根本転換した (v9.15 最大の失敗と学習)
92. tolerance の意味を実装前に詰める。1e-6 を「後で調整」と先送りした結果、Match Ratio 全 0 で段階 1 では機能しなかった
93. 連続値空間で離散一致判定は原理的に機能しない。連続量 (divergence) の方が情報量が多い
94. Step 単位固定実施は研究者視点。主観性の最小条件はタイミングの予測不能性 (Taka 指摘 2026-04-20)
95. 集約指標 (Match Ratio 等) は何のために取るのかを設計時に詰める。CID 視点で意味があるかを明示
96. 発生頻度の違う event 間で比率や数値を比較しても構造的情報は出ない
97. 観察結果を条件から切り離して普遍化しない。条件明示で記録
98. 推測を結論と書かない。「系が安定している」ではなく「安定を示唆する可能性」にとどめる
99. ランダム性が論理の支柱。削る方向は採らない。予測不能性を担保にした主体性主張の戦略 (Taka 核心発見)
100. 「自己がある」と「自己はない」の中間で戦う (哲学以上科学未満)。反証困難性を構造として作る
101. 研究者が原理的に CID の内部を覗けることは弱点。これをランダム性で埋める。奇妙なバランス
102. 機械的な「自分について語る」は自己ではない。ランダム性を担保した主張でなければ自己の候補にならない
103. GPT 監査の「観察層の薄さ」指摘は妥当。Match Ratio 廃止後も最小 3 点セットで richness を維持
104. Claude の癖 (整理過剰、意味を盛る、研究者視点偏重) は消えない。3 役分離で相対化するのが運用
105. 反省より運用切り替えが生産的 (Taka 現実的指摘、2026-04-20)
106. CID 視点と研究者視点の分離は v9.15 の中核。両視点を並列記述する文書構造を維持
107. ノード数固定は実験制御であって神の手ではない。物理層クローズだからこそ認知層の発展が追跡できる
108. ノード数変動は大幅後回し。認知層が十分発展してからの検討事項

---

## v9.16 — Observation Sampling (段階 3: 観察サンプリング機構)

### このフェーズの主題

v9.15 段階 2 で「Fetch のタイミング」が物理事象駆動になり、研究者予測不能性が確立した。v9.16 段階 3 では「Fetch で何が見えるか」も時間的に変化させる。ランダム性を一段深める。

Taka 2026-04-20 核心発見:
> ランダムに紐づけることで研究者の主観を実質封じる一手

この戦略を段階 3 で拡張。

### Claude の先走りと Taka 問い直し

Claude は v9.15 Phase 3 で「v9.16 = Fetch の確率的失敗」と記録していた。Taka 問い直し (2026-04-21):
> 冷静に考えると Fetch の確率的失敗ってどういう意味?

Claude は「失敗」の意味を詰めていなかった。Taka 規律 4 (v9.15 草案時) は「差分の**確率的消費**」であって「失敗」ではない。選択的認識の話。Claude の表現は規律から外れていた。

### Taka 再整理 (2026-04-21)

> 今のところ差分情報を予測する機能がないので、自分と同一かを判定する。手っ取り早いのは B_Gen。一致率を見る。まだ見た上で何をするかは考えない。

v9.16 主題:
- 差分の内容は予測しない (段階 4 以降)
- 同一判定のみ
- 判定基準に B_Gen (または Q_remaining) を使う
- 判定結果に基づく CID 行動変化なし

### 人間比喩による 2 段階認識

Taka:
> 構造の違い (何者か) = B_Gen (人間 vs カエル)
> 時間的違い (何歳か) = Q_remaining (若者 vs 老人)

自己読みでは B_Gen は不変なので差が出ない。差が出るのは Q_remaining。

### 2 AI 統合回答 (Gemini + GPT、2026-04-21)

両 AI が強く一致した骨格:

1. 主題を「判定条件の時間変化」に絞るのは正しい
2. 実装はサンプリング方式 (案 1、tolerance 可変と確率判定は却下)
3. B_Gen は間接使用 (age_factor = Q_remaining / Q0 経由)
4. age_factor = Q_remaining / Q0 の線形比率で十分
5. Q 消費は現状維持 (判定では追加消費しない)
6. 初期仮説は Q 少 → 一致率低、ただし結論化しない

GPT §12 先走り防止チェックポイント:
1. バージョン名を決めた時点で入出力を一文で言えるか
2. 「失敗」「認識」「自己」等の語を物理操作へ還元できるか
3. 観察と行動を混ぜていないか

### 一文定義 (指示書 §0.2)

> v9.16 は、cid が event 発火時に自分の物理状態と生誕時スナップショットを比較する際、メンバーノードのうち age_factor = Q_remaining / Q0 に比例した数を確率的に選んで判定し、選ばれなかったノードは欠損として扱うフェーズである。入力は Q_remaining と生誕時/現在の θ・S、出力は各ノードの一致/不一致/欠損フラグと、age_factor 依存の判定結果の時系列である。

### 実装の骨格

```python
# event 発火時の処理 (Layer B spend_packet 実行後)
age_factor = Q_remaining / Q0  # [0, 1]
n_observed = int(round(n_core * age_factor))

# hash ベース独自 RNG (engine.rng に影響を与えない)
rng_seed = hash((seed, cid_id, step, event_type)) % (2**31)
local_rng = random.Random(rng_seed)
observed_indices = local_rng.sample(range(n_core), n_observed)

# 観察ノードのみ判定、残りは missing
for i in range(n_core):
    if i in observed_indices:
        node_status[i] = 'match' if within_tolerance else 'mismatch'
    else:
        node_status[i] = 'missing'
        missing_flags[i] = True  # 段階 1 で準備されていた器が意味を持つ
```

### 実装結果 (24 seeds × tracking 50)

**bit-identity 確認**:
- v9.14 baseline CSV 6 本: v9.14 smoke と MD5 完全一致
- Fetch 総数 120,782: v9.15 段階 2 と完全一致 (seed 単位でも)
- theta_diff_norm_all: v9.15 段階 2 の theta_diff_norm と max 差 0.0 (物理計算不変の証明)

**基本統計**:

| 指標 | 値 |
|---|---|
| Wall time | 3h07m (段階 2 と同等) |
| node-cell match 比率 | 0.00 % (tolerance 1e-6 の帰結) |
| node-cell mismatch 比率 | 23.22 % |
| node-cell missing 比率 | 76.78 % |
| Q 枯渇 cid (age_factor_final = 0) | 1,771 / 5,170 = 34.26 % |
| seed 間 CV (avg_age_factor) | 2.96 % |
| seed 間 CV (final_missing_fraction) | 3.72 % |

**age_factor 区間別の missing 比率** (代数的必然):

| age_factor 区間 | missing 比率 |
|---|---|
| [0.0, 0.2) | 99.27 % |
| [0.2, 0.4) | 67.80 % |
| [0.4, 0.6) | 50.17 % |
| [0.6, 0.8) | 32.56 % |
| [0.8, 1.0) | 6.37 % |

`n_observed = round(n_core × age_factor)` から代数的に導かれる関係。「観察」ではなく「設計が意図通り機能した確認」。

**event 種別ごとの age_factor 差**:

| event | age_factor median |
|---|---|
| E1 | 0.58 |
| E2 | 0.73 (若いうちに発生) |
| E3 | 0.00 (Q 枯渇後に発生) |

段階 2 で観察された E2 vs E3 の質的差 (theta_diff_norm median 1.59 vs 4.67) と整合。E2 は自分の局所変化で若いうちに、E3 は他者接触で古くなってから発生。

**n_core 別の age_factor**:

| n_core | age_factor median |
|---|---|
| 2 | 0.55 |
| 3 | 0.11 |
| 4-8 | 0.00 |

Code A の物理説明 (Describe 内): n_core 小 → member link 数少ない (C(n,2)=1) → E1/E2 発火頻度低い → Q 消費遅い。

### Taka 追加論点 (2026-04-21)

**説明可能性の時間的構造**:

Taka が v9.16 完了時に提示した仮説:
- 過去は時間経過で広がっていく (確定したはずなのに)
- これを説明可能性の減衰として解釈
- 現在 (説明可能性最大) → 過去 (あったであろう) / 未来 (あるであろう) の 2 方向構造

v9.16 段階 3 で「過去 (生誕時) との一致/不一致を確率的に判定する」機構が成立。将来、逆方向に「未来の説明可能性」を投影できる可能性 (段階 5 以降の候補)。

**説明可能性は not decide, but describe と同格の原則** (Taka 2026-04-21 指定)。3 AI 共通運用。

**動的均衡の違和感**:

Taka:
> 認知量の消費が -1 でいいのか?固定値にするとスケールをデカくするとみなすぐ死ぬ。動的均衡の立場として違和感。

ただし今は主題外:
> 動的均衡が重要になるのは物理スケールを扱うタイミング。今は CID の主体が主題。現状 CID があろうがなかろうが物理現象は安定的に発生する。

v9.16 では消費 -1 固定のまま。物理スケール変動化の段階で再検討。

### Constitution (2026-03-05) との接続

Taka が既に明文化していた憲法:
- §2 Core Objective: 動的均衡下での Explainability X の最大化
- §3 Explainability: 短い記述、時間的安定性、再現可能な構造
- §5 Anti-Drift: 測定可能性に紐づかない主張は design decision に使わない
- §7 Governance: Observation → Bottleneck → Minimal Change → Re-observation

v9.16 指示書 §14 で憲法各章との整合を明示。v9.15-16 の議論は**新規原則ではなく具体化**。

### v9.16 の位置づけ

ESDE 階層進化:
- v9.14 = cid 間接続 (横方向の上位化)
- v9.15 段階 1 = 自己読みの器
- v9.15 段階 2 = タイミングの予測不能化
- **v9.16 段階 3 = 見える範囲の時間的変化** (自己化に時間軸を追加)

**主張の構造**:

| 要素 | 内容 |
|---|---|
| 弱点 | 研究者は原理的に CID の内部を覗ける |
| 防御 1 (v9.15 段階 2) | タイミング予測不能 |
| 防御 2 (v9.16 段階 3) | 見える範囲も予測不能 (時間依存サンプリング) |
| 論拠 | 反証困難性 |
| 結論 | 「自己のようなもの」は哲学以上科学未満で成立 |

### 確定した運用ルール (v9.16)

- **一文定義を草案に含める** (先走り防止、GPT §12)
- **サンプリング方式で観察の時間変化を表現** (tolerance 可変・確率判定は却下)
- **B_Gen は間接使用** (age_factor 経由)
- **age_factor = Q_remaining / Q0** の線形比率
- **観察結果を代数的必然と混同しない** (age_factor 区間別 missing 比率は設計の確認)
- **説明可能性は Describe 原則と同格** (3 AI 共通運用)

## 教訓 (v9.16 追加)

109. 「Fetch の確率的失敗」のような詰まっていない言葉を前提として使わない
110. バージョン名を決めた時点で入出力を一文で言えるかチェック (GPT §12 提案)
111. Taka 規律 4 は「確率的失敗」ではなく「確率的消費 = 選択的認識」
112. B_Gen/Q は物理層から確率論的に導出された値。判定基準に使うのは確率ベース設計の延長 (神の手ではない)
113. 自己読みでは B_Gen は間接使用 (Q0 経由の age_factor)。直接参照は他者読みで意味を持つ
114. age_factor 区間と missing 比率の関係は「観察」ではなく「設計が意図通り機能した確認」
115. Code A が事前に観察条件を網羅的にチェック表にする習慣は、先走り防止の実装レベル対応
116. 説明可能性は not decide, but describe と同格の原則 (Taka 2026-04-21)
117. 現在 ← 過去/未来 の 2 方向構造は段階 5 以降の実装候補
118. Constitution (2026-03-05) は既に明文化済み。v9.15-16 の議論は新規原則ではなく具体化
119. 動的均衡は物理スケール変動時に重要 (現在は認知層主題なので後回し)

---

最終目標は「神の手を介さずに認知・意味・社会性が創発するモデル」。
当面のゴールは「私たちと会話ができるシステム」。

v9.13 で S≥0.20 の神の手を撤去、Genesis 原理に沿った label 選別を確立。v9.14 で B_Gen を計算原資として運用する paired audit を実装、E3 = cid 間 2 者共鳴として再概念化。v9.15 で CID が自分を読む機構を確立、段階 2 で event 駆動への切り替えにより研究者主観を封じる構造を成立させた。v9.16 段階 3 で観察サンプリング機構 (age_factor = Q_remaining / Q0) を導入、見える範囲も時間的に予測不能化し、「自己のようなもの」の反証困難性を一段深めた。次フェーズ候補は段階 4 (他者読み) / 段階 5 (差分予測・未来の実装) / 長期記憶強化 / 元々の v9.15 テーマ (R1-R5)。*
