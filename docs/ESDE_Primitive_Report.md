# ESDE Primitive Report

*Phase: Primitive (v9.0–)*
*Status: **中間目標1達成。** v9.4 Perception Field実装中。label間カップリングの前提としてlabelの「見える世界」を定義。v10.0a Membrane接続は保留（1-State cross link問題）。*
*Team: Taka (Director/Philosopher) / Claude (Implementation) / Gemini (Architecture) / GPT (Audit)*
*Started: March 30, 2026*
*Last updated: April 4, 2026*
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

---

## 4 要素の現状（Primitive Phase）

| 要素 | 状態 |
|------|------|
| 現在 | 存在（物理層 + 仮想層）。自己参照ループ成立（v9.0）。逐次化 + age 順で torque/gravity 正常化（v9.3）。Stress OFF で仮想層が平衡肩代わり |
| 過去 | 導入済（maturation + rigidity）|
| 未来 | 確定: Future = n→n+1 差分 |
| 外部 | v8.4 局所波 + v9.0 フィードバック + v9.3 deviation detection + External Wave 耐性確認済 |

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
| 9.4 | Label間カップリング + Perception Field | **進行中** | coupling probe: 影響ゼロ（1-hop孤島問題）。perception field: 知覚圏定義 |
| 9.4+ | N-hop Gravity（影響圏拡張）| **次候補** | 知覚圏の結果を見て統率力→hop数導出。境界カップリング・三項創発 |

### v10.x — 複数インスタンス（中間目標 2-3）— **保留**

| Step | 内容 | 状態 | 中間目標との接続 |
|---|---|---|---|
| 10.0a | Membrane Coupling (1-State N=10000) | **保留** | cross link 問題 + 膜即死。label間カップリング確立後に再開 |
| 10.1 | seed 間情報伝達の観測 | 未着手 | 意思の疎通の前段階 |

### v11.x 以降 — 認知・言語（中間目標 4-6）

未設計。v10.x の結果を見てから。

---

## 現在の ESDE アーキテクチャ概要

### 物理層（Genesis canon、凍結）

- 5000 ノード、71×71 グリッド
- 各ノード: E（エネルギー）、θ（位相）、ω（固有周波数）
- リンク: S（強度）、R（共鳴値）
- 5 つの力: 位相回転 → エネルギー流 → 共鳴 → 減衰 → 排除
- stress equilibrium: リンク数の EMA による動的平衡（後景化。仮想層が肩代わり可能と確認）

### 仮想層（virtual_layer_v9）

- label: frozenset（ノード群への主張）。birth 時に固定
- torque: phase_sig に向けてノードの θ を引っ張る（**逐次適用、age 順**）
- semantic gravity: label 外近傍にも θ を引き寄せる（deviation-gated）
- share: territory に基づく存在の重み
- cull: share < threshold で死亡
- **v9 追加:** 系全体の died_share_sum → EMA → torque modulation
- **v9.3 追加:** deviation detection（D1/D2/D3 → gravity_factor）、逐次適用、age 順、500 step/window

### 計測層（calibrate 側）

- local wave: decay sin 勾配（oasis/penalty 地形）
- C-light / D-light: 代表 label の内部状態追跡
- thaw pressure: frozenset 解凍圧の仮想測定
- resistance pattern: label 個体の抵抗様式分類

---

*v9.0 で自己参照フィードバックループを導入。v9.1-v9.2 で torque の 2 相サイクルを発見。
v9.3 で偏り検知 → バッチ処理の同時性問題を特定 → 逐次化 + age 順 + longer window + Stress OFF で中間目標1達成。
v10.0a の Membrane 接続は cross link 問題と膜即死で保留。
GPT 方針転換: シード間接続の前にシード内 label 間カップリングを検証すべき。
v9.4 coupling probe で label 間影響がほぼゼロと判明（1-hop 孤島問題）。
方針: N-hop gravity の前にまず N-hop perception（知覚圏）を定義。
labelを「作用する主体」の前に「世界を見ている主体」として定義する。
将来: 統率力 → 影響圏 → 境界 → 三項創発（A 対 B から C が生まれる）。
最終目標は「神の手を介さずに認知・意味・社会性が創発するモデル」。
当面のゴールは「私たちと会話ができるシステム」。*
