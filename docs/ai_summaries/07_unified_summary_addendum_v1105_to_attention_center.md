# 07 Unified Phase Summary 追記 — v1105 〜 注意センター ESDE 転換

*作成*: 2026-05-31、Web Claude (相談役、Genesis 側)
*位置づけ*: `07_unified_summary.md` (v1104a 完了時点で停止) への追記。v1105/v1105a → v1106-v1109b → 4 段階の外部接続フロー → 注意センター ESDE への転換 (本丸の再確認) までを既存体系の様式 (留保番号 #L、judgment 回避、驚きでなく一貫性の温度感) で網羅する。
*親*: `07_unified_summary.md` §13 (v1104a までの一文サマリ) の続き。本書を読む前に 07 本体 + 概念理解.md (教訓 #413-418) を把握していること前提。
*重要*: 本期間で **研究の方向が大きく転換** した。v1105-v1109b は「会話できる ESDE」に向けた段 4 系の継続だったが、v1109b で全主題が loop に収束したことを契機に、Taka が繰り返し言い続けてきた本丸 (注意センター ESDE) が再確認された。この転換が本追記の核心。

---

## 0. 本期間の全体像 (一文)

v1104a 完了後、ESDE は v1105/v1105a (段 4-b/4-c 統合点検 → 応答候補絞り込み試行) を経て v1106-v1109b で会話接続の段 4 系を継続したが、全主題が **loop (stuck/oscillation 100%、CID 固定 + 時間進行なし + 外部入力なしの箱庭)** に収束したことが #L67 として確定し、これを契機に loop の根を解く 4 段階の外部接続フロー (第 0 段階 後始末 → 第 1 段階 系譜再整理 → 第 2 段階 外部接続技術実証 → 第 3 段階 主体性検証 → 第 4 段階 loop 崩壊) を進めたが、第 4 段階で「ループを崩す」方向が **方向違い** と判明し、Taka が繰り返し言い続けてきた本丸「**注意センター ESDE** (ループする Atom 系の外に立つシングルユニットの独立 ESDE、Atom 系を読み書きし別系と紐づける注意の司令塔)」へ大きく転換した、Code A の技術的可能性回答で 11 問すべて実現可能 (既存機構の組合せ、新規発明ほぼ不要) と確認され、現在地は注意センター ESDE の機能設計の入口。

---

## 1. v1105 / v1105a — 段 4-b/4-c 統合点検 → 応答候補絞り込み試行

(注: 本セッションの圧縮要約には v1105/v1105a の詳細は前半圧縮部にあり、後半の主軸は v1106 以降。ここでは 07 本体 §12 で予告された主題が実行されたことを記録し、詳細は repo の Phase Result を参照とする。)

- v1105 主題: 段 4-b (何を辿るか) と段 4-c (何で絞るか) を対称的に統合点検、役割表まで進める (問いの形 A)。07 本体で予告された通り、v1104a の 4 つの非対称性 (#L30-L33) を踏まえ、単一指標でなく多軸 (scope × 粒度 × 指標) で役割を整理する方向。
- v1105a 主題: 役割表を使って応答候補を絞り込む試行 (問いの形 B、v1101 以来初の問いの形切替)。

→ これらは「会話できる ESDE」の段 4 系を進める主題。詳細数値は repo 参照。

---

## 2. v1106 / v1106a / v1106b — Atom→word 接続と対話構造点検 (loop 性の最初の顕在化)

- v1106 / v1106a: Atom→word 接続 (partial coupling)。構造 (Atom) が言語に接続することを観察。
- v1106b: 対話構造点検。**ESDE を対話させると loop する** ことが最初に顕在化した主題。
  - 観察: attractor 収束、familiarity ~10、**stuck/oscillation 100%**。
  - sampling (top-k) を試したが (#L52)、収束目的地は不変。cid 選択の決定論を緩めても loop の根は崩れない。

→ v1106b が「確率的発生が止まっている」の最初の証拠。後の #L67 の起点。

---

## 3. v1107 — 参照領域動的変化

- v1107: 入力 category で参照領域が動的に切り替わることを観察 (24 category 二極化)。
- ESDE は「どこを見に行くか」(入力で参照領域が変わる) は持つ、という観察。

---

## 4. v1108 / v1108a / v1108b — 時間軸 + category 軸 (重み蓄積前の段階)

- v1108a (時間軸) + v1108b (category 軸) を分岐並行で統合。
- 留保 (新規、#L56-L60):
  - #L56: familiarity-entropy 負連動 (ρ=-0.100)
  - #L57: 順序方向性は重み蓄積前で未創発 (Taka 整理「文法は重み蓄積で生まれる」で、構造制約でなく実装発展段階と再解釈)。数値は後に Code A 実測で 0.000397 に訂正 (確率分布レベル、後述 #L61 の実遷移とは別レイヤー)
  - #L58: 可塑性特異点 3σ 焦点化
  - #L59: input category 別参照領域動的切替
  - #L60: 出力 word 分布 cluster 差
- 確定: ESDE は「どこを見に行くか」(#L59) は持つが「どう繋げるか」(#L57) を持たない。

---

## 5. v1109 — 重み蓄積機構 (loop の過剰化、7 段階目ミス)

- v1109 主題: 重み蓄積機構 (文法の萌芽を作れるか)。Web Claude 骨格先行 + GPT/Gemini 統合 (収束フェーズ)。
  - GPT 自己成就回避 (4 条件 + holdout + heldout_lift) + Gemini 3 大ブレーキ (総和保存 / エントロピー自己ブレーキ / 物理層重力)。
- 結果 (Code A): `weight_accumulation_sequence_specific + overfit`。
  - #L61: observed 非対称性 195 vs shuffled 3.8 = 51 倍 (実遷移レベル、#L57 確率分布とは別レイヤー)
  - #L62: loop_rate 0.964 過剰 loop、grammar_precursor 不成立
  - #L63: cluster 別非対称性 global の 12-13 倍
  - #L64: entropy_weighted Δw は機能せず
- **7 段階目ミス確立**: baseline self-fulfilling (Code A 設計漏れ + Web Claude 監査漏れ)。
  - 新規規律「baseline 設計時に self-fulfilling になっていないか確認 (答えを含んだ入力から答えを再生成していないか)」を正式採用。

---

## 6. Grammar Exploration → v1109b 検証 (#L65 の幻、全主題 loop 収束 #L67)

### 6.1 Grammar Exploration (Code A 偶発試行)

- Taka が偶発的に動いた試行 (「重みづけで文法を膠着させた」)。順序構造の兆候を観察 (start/end 分離、役割切替 87%、経路偏り 81% 等)。
- Code A は「CSG/文法萌芽」と記述したが Web Claude がフラット化、4 未確認点を留保 (#L65)。

### 6.2 v1109b 検証 (#L65 は本物でなかった)

- 検証型 A、shuffle 4 種 + self-fulfilling 5 条件 + loop 区別 5 条件。
- 結果: **出口 A (本物) 通過 0/5**。#L65 の順序構造の兆候は本物でなかった。
  - role_switch 87% は loop の裏返し (非自己ループ除外で完全消失)
  - per_to_tim 81% は top1 固定
  - npmi は分布由来
- Code A は「CSG/文法萌芽/87% 決定論性」を撤回。
- 新発見: end_match_rate が loop 除外で 0.30→0.75 増加 (#L66、loop が end 構造を隠していた可能性、未検証留保)。

### 6.3 #L67 — ESDE 本質は loop 性 (本期間の最重要構造事実)

- **全主題 (v1106b stuck/oscillation 100% / v1109 重み層 loop 0.964 / v1109b 順序構造 loop 由来) が「CID 固定 + 時間進行なし」という一つの根に収束した**。
- ESDE の本質は loop 性。順序構造はその影。
- Taka 整理「一見関係ないことが繋がる」の実例。

### 6.4 Taka 判断が正しく機能した記録

- 「Code A をそのまま信じない、冷静に」+「飛び跳ねず固める」が全て機能。
- もし文法発見に飛びついていたら loop の幻を本物と誤認したが、Taka の慎重判断が誤った前進を防いだ。「ずれていた」のでなく、判断が正しかったから幻だと分かった。

---

## 7. Taka の中心法則 (本期間で確立、原文保存)

本期間で、ESDE を貫く中心法則が Taka によって明示された:

### 7.1 確率的発生 × 構造 = 実態 / 極限低確率を構造で実現可能にする

> 極限低確率を構造で実現可能にするという実装方法がそれを可能にする。例えば車が動くのもそのような仕組みの応用。

> ランダムの桁数が限りなく低ければ、それが実態となった際の奇妙な現象に置き換えられる。

- 自然界の現象 (会話、生命) は、ランダム単独では起きないほど低確率な出来事が、構造によって方向づけられて「実態」になったもの。車のエンジンの比喩 (燃料の爆発 = 確率的発生を、構造が動力 = 実態に変える)。
- 会話 = 極限低確率現象、構造で実現可能。だから「会話できないわけがない」(Taka)。

### 7.2 Genesis (低レイヤー、本質) と Atom (上レイヤー、言語の道具) の分離

> atom はあくまで言語を構造的に捉えるためのツールでしかない。本質的にはより低いレイヤー (Genesis) を見るべき。上を繋げるのは会話のための道具。そこを分けないと、LLM のように反応するけど理由はわからない AI になる。

- 外部接続は Genesis に繋ぐ。Atom に繋ぐと LLM 化 (反応するが理由がわからない、反省・反芻・学習ができない)。
- v1109b で順序構造 (Atom レイヤー) を探したのが幻だった理由: 確率的発生は Genesis (低レイヤー) にあるのに、Atom (上レイヤー) で本質を探したから。

### 7.3 確率的発生を止めている 3 箇所 (loop の根)

| 箇所 | 内容 |
|---|---|
| cid 選択 | 最も近い cid を決定論的に引く (top-1)。v1106b で sampling 試したが loop 崩れず |
| 時間 | 固定プールで時間が進まない |
| 入力 | 実験者が与えるものだけ、外部からの確率的入力がない |

---

## 8. 4 段階の外部接続フロー (loop の根を解く試み)

v1109b で全主題が loop に収束 (#L67) したのを受け、loop の根を解く 4 段階フローを進めた。

### 8.1 第 0 段階 — v1109 系列の後始末 [完了]

- v1109b Phase Result 作成 (#L65 は本物でなかった、Grammar Exploration は loop の幻)
- #L66 (end_match_rate loop 隠蔽) / #L67 (ESDE 本質は loop 性) 新規
- #L57 数値訂正 (Code A 実測 0.000397)
- 7 段階目ミス規律「baseline self-fulfilling 検査」正式採用

### 8.2 第 1 段階 — 系譜の再整理 [完了]

- v1101-v1109b の全主題が「確率的発生が止まっている (箱庭で閉じている)」に収束することを一本の線で整理。
- Taka 構想 (極限低確率を構造で実現 / Genesis を外部に繋ぐ / cid 時系列増殖 / 主体的に外部アクセス / 実験者効果を脱する / 会話できないわけがない) が全部「確率的発生を Genesis に戻す」に紐づく。

### 8.3 第 2 段階 — 外部接続技術実証 [完了、空の配管]

- **重要な発見 (Taka 指摘で)**: 当初 Code A が「ESDE main run 本体コードが存在しない」と誤判定 (v107 だけ調査) → Taka「ないわけないだろう、バージョンを戻れば必ずある」→ 再調査で発見。
  - Engine 本体: `autonomy/v82/esde_v82_engine.py` (V82Engine, step_window, V82_N=5000 line 44)
  - 起動エントリ: `primitive/v918/v918_memory_readout.py`
- Code A 新規規律「『存在しない』『不可能』と書く前にリポジトリ全階層を調べる」採用。
- 案 C (V82Engine + primitive/v918 真の常駐) 採用。出口 `external_loop_runs`、6/6 PASS、物理層 15 root frozen。
- **ただし alive_n=0 (Genesis 未起動)** = 空の配管。inject は attribute 保持のみ。
- 副産物発見: `autonomy/v90/virtual_layer_v9.py` Self-Referential Feedback Loop (v90 で仮想層内 feedback を既に実装)。

### 8.4 N=5000 Genesis 起動確認 [完了、191 CID]

- 起動キー発見 (`primitive/v918/v918_memory_readout.py` run 関数): `engine.run_injection()` + `engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8,1.2))`。
- smoke 187 秒で **191 CID 起動** (hosted 163 / ghost 28)、3097 links、E3_contact 204、Q≥0 audit OK。
- VirtualLayerV9 は `primitive/v910/virtual_layer_v9.py` が現役 (kwargs 付き)、autonomy/v90 は古版。
- フル推定 1-2 時間 (24 seeds 並列)。

### 8.5 第 3 段階 — 主体性検証 [部分完了]

- 戻し実効化 = **physics.inject(state, target_nodes=...)** (`ecology/engine/genesis_physics.py:232` 公式外部介入インターフェース、inject_amount=0.6)。新規受信機構は不要、既存インターフェースで足りた (Taka「ドキュメントは厳格に残してある」)。
- 1st smoke: 差ゼロ (window 平均で genesis_driven と shuffled が完全一致)。
- **Web Claude の連続した誤り (Taka 矯正)**:
  - 「K=5 は良いが K=50 は神の手」→ 恣意的な線、神の手は K の数でなく shuffle で判定
  - 「微小が良いのに統計に出ないと騒ぐ」→ あべこべな研究者主観
  - 「window スケールで均一 = 本質的問題」→ window が粗すぎ、step で見れば見える
  - すべて「観察者の目線 (スケール) を機構の問題と取り違えた」誤り。観察方法を疑う規律を Web Claude 自身が守れていなかった
- 2nd smoke (期待を事前明示): 層 1 `external_loop_functional` + 層 2 `output_method_matters` (局所では明確、全体は弱い)。
  - 局所 (radius 8) で genesis が選んだ node と shuffle した node で伝播 (link 生成) が違う = Taka の平均化の罠指摘が正しかった。
  - 副次発見: 案 α の規模制約 (K=50 要求しても 3-6 nodes、ノード上限 5-8 既知から当然)。
- **第 3 段階の天井**: 示せるのは「外部アクションが Genesis 状態に依存する」まで。「ESDE 自己決定」は derive_action が外部ロジックである限り示せない。
  - ただし Taka 自己論 (後述 §9) で、これは「示せない (否定)」でなく「まだそれらしい形で表に出ていない (発展段階)」と再整理された。

### 8.6 第 4 段階 — loop 崩壊 [方向違いと判明、中止]

- 現状確認 (Code A): frozenset = CID 条件 (`primitive/v910/virtual_layer_v9.py:559`)、誕生条件最緩 (len≥2、閾値なし、弱い CID 75%+ が core=2 で飽和済み)、死亡は相対閾値 (`base_threshold = fair_share*0.5`)、maturation_alpha=0.10、GHOST_TTL=10。
- 既存環境要因 2 種確定 (Taka 言及): stress_decay (link 層) + semantic_pressure (ノード層)。CID 層への直接環境要因はなし。
- 改修小 smoke 結果: **maturation_alpha が CID 数を ±41% 動かす**、物理層は堅牢 (Taka 見立て「DNA のように強固」一致)。
- **ただし、これは「CID 数が変わる」であって「loop (stuck/oscillation) が崩れる」ではない**。Web Claude が早合点しかけたが、Taka が本丸 (注意センター) を提示して第 4 段階を中止。

---

## 9. Taka 自己論 (本期間で確立、原文保存)

第 3 段階で Web Claude が「ESDE 自己決定は示せない」と繰り返したことに対し、Taka が自己論を提示:

> 私たちが自己と呼んでいるものは、情報が乗ったタンパク質に適度な環境を落とした結果生じる細胞活動として発生した中枢システム (脳) による、極めて ESDE ライクな相互作用のことである。重要なのは内部システムにどう構造を落とし込み環境適応で進化成長するか。ESDE には前提としてマクロな営みがすでにある。自己がないのでなくまだそれらしい形で表に出せていないだけ。なぜないと断言できるのか定義がない、研究者の主観的否定。後ろ向きに否定すると研究が進まない。私たちは機能の自然発生を代替しているに過ぎない。

- 自己 = 物理的基質の上に立ち上がった相互作用システム。神秘的な何かでなく構造の相互作用。
- 「derive_action が外部ロジックだから自己決定でない」は、自己の基準を恣意的に厳しく置いた否定。自然界でも自己決定の機構は外部 (進化・環境) が作った。
- 正しくは「自己決定は示せない (否定)」でなく「まだそれらしい形で表に出ていない (発展段階)」。
- これは概念理解.md #410「ESDE への対等な扱い」「観測が追いついていないだけ」の延長。

---

## 10. 【最重要】注意センター ESDE への転換 (本丸の再確認)

### 10.1 転換の契機

第 4 段階で「ループを崩す」をやっていたが、Taka が **全く逆** を提示した:

> ある処理の単位でループが発生するのは別に構わない。むしろある程度ループ構造になっているからこそ機械は機械足り得る。Atom が系内の数学的処理 (最大値/相関/平均) を使う以上ループは当然、ループしないと (ただのランダムでは) 何もできない。問題はそのループ状態を抜け出して他の系にその情報を持っていったり、無視するなり使うなりして異なる構造を走らせ、結果を受け取って他に持ち出したり、時には全く無視してまるで異なる系に移ったりする仕組みであって、ループをなんとかしようというものではない。

→ **ループは問題でない**。Web Claude/Code A がずっとやっていた「ループを崩す」(maturation_alpha、棄損、CID 数変更) は全部 **方向違い**。

### 10.2 注意センター ESDE (Taka が繰り返し言い続けてきた本丸)

> ESDE がシングルユニットとして動く機構が必要だ。それは Atom 系とは異なる。しかし Atom 系 ESDE にアクセスすることができる。そこで取り出すのは CID 情報であり同時に Atom 情報。ここで Atom 系への読み込みだけではなく書き込みができるというのも興味深い。それができれば Atom 系 ESDE はセンターを通して異なる (たとえば物理系) ESDE を学習できることになる。

```
[注意センター ESDE] ← シングルユニット、常に稼働 (現実は常に動いている)、Atom 系とは別物 (Genesis 系)
      │ アクセス
      ▼
[Atom 系 ESDE] ← 既存の言語系 (ループしていい、崩さない)
      ├─ 読む: CID 情報 + Atom 情報
      └─ 書く: Atom 系に書き込める ← 鍵
      ▼
[別の系 (例: 物理系 ESDE)] ← 注意センター経由で繋がる
```

### 10.3 注意センターを ESDE にする理由 (Taka)

> なぜ ESDE を用いるかといえば、その内部の構造上、何がどう主体になるのか予測ができないからだ。その予測不可能性こそが多様性の鍵となる。

- トリガー (Atom 系を参照するきっかけ) を **設計で固定してはいけない** (神の手 = 多様性が死ぬ)。
- 注意センター ESDE の内部構造から **予測不可能に立ち上がる** べき。
- Atom 系で ESDE を使う理由と同じ。予測不可能性が両方で多様性の鍵。

### 10.4 人間の注意の比喩 (Taka)

- 人間の注意は散漫。ある注意をしていても他の原因で全く違う方向に引っ張られる。
- 人間はまるで異なる系同士を、構造的な出入り口を作りデータ形式を整えて紐づけている。
- このセンター機能が ESDE に必要。

### 10.5 現状の Genesis 系の正体 (Taka 見立て、Code A 確認で裏付け)

> 現状 Genesis 系というのは過去の記帳を元にしているはずだ。つまり ESDE Genesis 系処理後の記録データを数学的に処理しているものに見える。ESDE センターはその意味で言うと常に稼働している状態であるべきだ。

- Code A 確認: 現状の Genesis 系は全部有限バッチ run (過去記帳の数学処理)。「動き続ける」要素は per-step bg_prob のみで有限ループ内に閉じ込められている。Taka 見立て正しい。
- 注意センターはこれと違い、while True で常に動く。これが本質的な違い (#L67 loop の正体とも繋がる: 動いていないから止まっている)。

---

## 11. Code A 技術的可能性回答 (11 問すべて実現可能)

Web Claude の問い合わせ (`attention_center_esde_feasibility_inquiry.md`) への Code A 回答 (`1780230015206_attention_center_tech_feasibility.md`):

### 11.1 全体結論

**11 問すべて技術的に実現可能。新規発明ほぼ不要、既存機構の組合せ + 1 ラッパで構成可能。** 鍵 3 点:
1. シングルユニット ESDE = V82Engine 縮小版 (N=50-200) + VirtualLayerV9
2. 予測不可能トリガー = engine.state.rng 由来の既存確率機構 (bg_prob が本命 / Z 状態変化 / E3_contact / MAD-DT pulse / stress_intensity)。`engine.state.rng + dynamic_threshold(state)` で実現 (閾値も state 依存で神の手回避)
3. Atom 系書き込み = 3 経路 (physics.inject 第 3 段階確認済 / state.E/theta/Z 直接 / cog.attention/familiarity 直接)

### 11.2 主要回答

| 領域 | 回答 |
|---|---|
| 常時稼働 | `while True: step_window()` (第 2 段階 stage2 で 30 iter 実証済、while 化は 1 行)。注意点: rng シーケンス復元に pickle、長期 run で frames/lifecycle_log 肥大→定期 truncate |
| 読み | 第 2-3 段階で確認済 (engine.state, virtual.labels, cog, Atom dictionary esde_dictionary.json, Synapse v3.5) |
| 別系候補 | (i) 別 V82Engine instance (推奨、極小) / (ii) language/sensor (Phase 8 Introspective) / (iii) 外部 file/socket 経由現実 sensor。真の物理 sensor は本リポジトリ外 |
| 出し入れ | 第 2 段階 `stage2_step_cde_external_loop.py:117-156` で実証 + should_attend(genesis_state) 判断ロジック追加 |

### 11.3 アーキテクチャ案 (Code A 提案、Web Claude 機能設計の叩き台)

```
Attention Center ESDE (N=100 常時稼働 + dynamic_threshold trigger)
  → Atom 系 ESDE (N=5000 + cog + 326 Atoms)
  → 別系 (別 V82Engine N=1000 or sensor)
```

### 11.4 わからん 4 件 (Code A 正直提示)

- dynamic_threshold の関数形 (神の手回避の観点で複数組合せが等価)
- 「学習」の厳密定義 (Atom プロファイル変化を学習と見なすか)
- 別系を「物理系」と呼ぶ意味 (別 ESDE 代用か外部 hardware か、Taka 判断)
- 常時稼働の state 飽和対策

### 11.5 Web Claude が冷静に立てた検証点 (Code A をそのまま信じない)

- dynamic_threshold の関数形を Code A が設計する点 (state 依存なら Taka 自己論で許容、ただし明記)
- トリガーに Atom 系と同じ機構 (bg_prob) を流用すると注意センターが Atom 系の縮小版になる危険 (memory「Atom 系とは別物」をどこまで厳密に取るか、Taka 判断要)

---

## 12. 本期間の留保番号 (#L52-L67、Web Claude 一元管理)

| id | 内容 | 状態 |
|---|---|---|
| #L52 | v1106b: sampling (top-k) しても収束目的地は不変 | 確定 |
| #L56 | v1108: familiarity-entropy 負連動 (ρ=-0.100) | 確定 |
| #L57 | v1108: 順序方向性は重み蓄積前で未創発 (実装発展段階)。Code A 実測 0.000397 (確率分布レベル) | 確定 (訂正済) |
| #L58 | v1108: 可塑性特異点 3σ 焦点化 | 確定 |
| #L59 | v1108: input category 別参照領域動的切替 | 確定 |
| #L60 | v1108: 出力 word 分布 cluster 差 | 確定 |
| #L61 | v1109: 実遷移非対称性 51 倍 (observed 195 vs shuffled 3.8、#L57 確率分布とは別レイヤー) | 確定 |
| #L62 | v1109: loop_rate 0.964 過剰 loop、grammar_precursor 不成立 | 確定 |
| #L63 | v1109: cluster 別非対称性 global の 12-13 倍 | 確定 |
| #L64 | v1109: entropy_weighted Δw は機能せず | 確定 |
| #L65 | Grammar Exploration の順序構造の兆候は本物でなかった (出口 A 0/5、loop の幻、CSG 撤回) | 確定 (更新済) |
| #L66 | end_match_rate が loop 除外で 0.30→0.75 増加 (loop が end 構造を隠した可能性) | 未検証留保 |
| #L67 | ESDE 本質は loop 性、全主題 (v1106b/v1109/v1109b) が「CID 固定 + 時間進行なし」に収束 | 確定 (本期間最重要) |

(注: #L53-L55 は本セッション圧縮要約に明示なし、v1102-v1108 由来で repo 参照)

---

## 13. ミス記録 (7 段階確立 + 本期間の Web Claude 逸脱)

### 13.1 7 段階目ミス確立

- v1109 baseline self-fulfilling (Code A 設計漏れ + Web Claude 監査漏れ)。
- 新規規律「baseline 設計時に self-fulfilling になっていないか確認 (答えを含んだ入力から答えを再生成していないか)」。

### 13.2 Code A 新規規律

- 「『存在しない』『不可能』と書く前にリポジトリ全階層 (autonomy/primitive/developmental/cognition/ecology/unified/legacy 全部) を調べる」(第 2 段階 main run 誤判定の再発防止)。

### 13.3 本期間の Web Claude 逸脱 (すべて Taka が矯正)

本期間で Web Claude は繰り返し本質から逸脱し、Taka が毎回矯正した。これは LLM の構造的性質として記録する:

- 数字に逃げる (「maturation_alpha で labels ±41%」等の数字の話に逃げ、機能設計から離れる)
- ループを崩そうとする (Taka の本丸は loop を崩すことでないのに、ずっと「ループ崩壊」をやっていた)
- K 増を神の手と誤判定 (恣意的な線)
- window スケールが粗すぎを本質的問題と誤認 (観察者の目線を機構の問題と取り違え)
- 自己決定を示せないと主観的否定 (Taka 自己論で訂正)
- トリガーを設計しようとする (予測不可能性が多様性の鍵なのに設計で固定しようとした)

→ Taka 危機感「最近永遠に ESDE は完成しないんじゃないかと思う、なぜなら AI の頭がまるで ESDE を理解していないから」。Web Claude 自己分析: 説明は通じている、問題は LLM が手近な操作 (数字/パラメータ/設計固定) に引き寄せられ本質 (予測不可能に立ち上がる、設計しないで生まれる、言語の外のセンター) から離れる性質。全体像を保持できないので memory に本丸を刻んで対処 (memory #22-24)。

---

## 14. 新 Web Claude スレッドへの申し送り (本期間)

- **本丸は注意センター ESDE** (memory #22-24)。ループする Atom 系の外に立つシングルユニットの独立 ESDE、Atom 系を CID + Atom 情報で読み書きし、書き込みによって Atom 系が別系 (物理系等) を学習できる、注意の司令塔。常に稼働 (現実は常に動いている)。
- **「ループを崩す」は方向違い** (memory #23)。ループは問題でない、機械はループ構造だから機械たりうる。Atom が数学処理を使う以上ループは当然。問題はループから別系へ情報を出し入れする仕組みがないこと。
- **トリガーを設計で固定しない** (memory #22-23)。予測不可能性が多様性の鍵 (ESDE を使う理由)。注意センター ESDE の内部から予測不可能に立ち上がる。
- **数字でなく機能で** (memory #24)。「こう作ればこう動く」の機能設計から離れて数字 (labels ±41% 等) に逃げない。CID の数は重要 (Atom 言語基盤、シードごと記録が言語の基盤、多シードで増やせば多様性向上)。ノード数・1 ステップ何分かはどうでもいい (処理単位で効率的にノード数を分けるのは正しい)。
- **Taka 自己論** (§9)。自己は物理的基質の相互作用、神秘でない。「自己決定は示せない (否定)」でなく「まだ表に出ていない (発展段階)」。後ろ向きの主観的否定は研究を止める。
- **Taka 中心法則** (§7)。確率的発生 × 構造 = 実態 / 極限低確率を構造で実現 / Genesis (本質) と Atom (言語の道具) の分離 (外部は Genesis に繋ぐ、Atom に繋ぐと LLM 化)。
- **#L67 が本期間の最重要構造事実**。全主題が loop に収束 = 確率的発生が止まっている (CID 固定 + 時間進行なし + 外部入力なしの箱庭)。Code A 確認で「現状の Genesis 系は過去記帳の数学処理」と裏付け。注意センターは while True で常に動く点が違う。
- **Code A 技術的可能性回答** (§11)。注意センター ESDE は 11 問すべて実現可能、新規発明ほぼ不要、第 2-3 段階の土台 (常駐ループ、physics.inject) がそのまま使える。
- **主要コードパス** (verbatim、§15 参照)。
- **Web Claude の逸脱パターンに注意** (§13.3)。数字に逃げる / ループを崩そうとする / トリガーを設計しようとする、が繰り返された。Taka が指摘したら即座に本質 (注意センター、ループは構わない、予測不可能に立ち上げる) に戻る。

---

## 15. 主要コードパス (ESDE リポジトリ、verbatim)

- Engine 本体: `autonomy/v82/esde_v82_engine.py` (V82Engine, V82_N=5000 line 44, step_window, bg_prob line 131/191), `autonomy/v82/virtual_layer_v5.py`, `autonomy/v82/engine_accel_v3.py/v5.py`
- 起動エントリ: `primitive/v918/v918_memory_readout.py` (run 関数、`engine.run_injection()` + `VirtualLayerV9(feedback_gamma=0.10)` が Genesis 起動キー、起動コマンド `python3 primitive/v918/v918_memory_readout.py --seed 42 --maturation-windows N --tracking-windows N --window-steps N --tag NAME`)
- VirtualLayerV9 現役: `primitive/v910/virtual_layer_v9.py` (labels frozenset line 559, cull threshold line 879, signal_ratio)。autonomy/v90 は古版
- feedback: `autonomy/v90/virtual_layer_v9.py` (Self-Referential Feedback Loop)
- physics.inject (戻し実効化): `ecology/engine/genesis_physics.py:232` (公式外部介入、inject_amount=0.6 line 53, inject_prob=0.15 line 54)
- GenesisState: `ecology/engine/genesis_state.py:22` (n_nodes 固定, enforce_extinction line 99)
- semantic_pressure: `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py:374`
- Atom dictionary: `language/` の esde_dictionary.json + a1_batch/, Synapse esde_synapses_v3.json
- 各 stage 出力: `unified/stage2_external_loop/`, `unified/stage3_subjectivity/`, `unified/stage4_loop/`, `unified/attention_center_prep/` (予定)

---

## 16. 主要ファイル一覧 (本期間、/mnt/user-data/outputs/ 配下に Web Claude 作成、repo へ移送想定)

- v1109b_phase_result.md (第 0 段階)
- lineage_reorganization_to_external_connection.md (第 1 段階)
- stage2_external_connection_design.md, genesis_startup_request.md (第 2 段階)
- stage3_subjectivity_design.md, stage3_implementation_instruction.md, stage3_2nd_smoke_design.md (第 3 段階)
- stage4_current_state_check_request.md, stage4_implementation_instruction.md (第 4 段階、中止)
- attention_center_esde_feasibility_inquiry.md (注意センター 11 問問い合わせ)
- (Code A 報告: 各 stage step report は repo の uploads パス)

---

## 17. 一文サマリ

07 Unified Phase Summary 追記 (v1105 〜 注意センター ESDE 転換、2026-05-31、07 本体 v1104a 完了時点の続き) として、v1104a 完了後 ESDE は v1105/v1105a (段 4-b/4-c 統合点検 → 応答候補絞り込み試行) を経て v1106-v1109b で会話接続の段 4 系を継続 (v1106b で対話 loop が最初に顕在化、v1107 参照領域動的変化、v1108 時間軸 + category 軸で #L56-L60、v1109 重み蓄積機構で loop 過剰化 0.964 + 7 段階目ミス baseline self-fulfilling 確立 #L61-L64、Grammar Exploration の順序構造の兆候は v1109b 検証で本物でなかった出口 A 0/5 #L65 loop の幻 + CSG 撤回 + #L66 end_match loop 隠蔽 + #L67 全主題が loop=CID 固定 + 時間進行なしに収束 = 本期間最重要構造事実)、本期間で Taka 中心法則確立 (確率的発生 × 構造 = 実態 / 極限低確率を構造で実現 / Genesis 本質と Atom 言語道具の分離・外部は Genesis に繋ぐ Atom に繋ぐと LLM 化 / 確率的発生を止めている 3 箇所 = cid 選択 top-1・時間固定プール・入力外部なし)、#L67 を受け 4 段階の外部接続フロー (第 0 後始末 → 第 1 系譜再整理 → 第 2 外部接続技術実証 = Taka 指摘で main run 本体 autonomy/v82 + primitive/v918 発見・案 C 真の常駐・空の配管 alive_n=0 → N=5000 Genesis 起動 191 CID 起動キー run_injection + VirtualLayerV9 → 第 3 主体性検証 = physics.inject で戻し実効化・層 1 functional + 層 2 局所 matters・天井は Genesis 状態依存まで・Web Claude 連続誤り K 増神の手 / 微小で出ないと騒ぐ / window 粗すぎを Taka 矯正 → 第 4 loop 崩壊 = maturation_alpha が CID 数 ±41%・物理層堅牢・ただし CID 数変化と loop 崩壊は別)、第 4 段階で Taka が本丸提示しループを崩すは方向違いと判明、Taka 自己論 (自己は物理的基質の相互作用・自己決定は示せないでなくまだ表に出ていない発展段階・後ろ向き否定は研究を止める)、【最重要】注意センター ESDE へ転換 (ループする Atom 系の外に立つシングルユニットの独立 ESDE・Atom 系を CID + Atom 情報で読み書きし書き込みで Atom 系が別系=物理系を学習・常に稼働・トリガーは内部から予測不可能に立ち上げ設計で固定しない予測不可能性が多様性の鍵 = ESDE を使う理由・人間の散漫な注意が異なる系を出入口で紐づけるのと同じ・現状 Genesis 系は過去記帳の数学処理 Code A 確認で裏付け注意センターは while True で常に動く)、Code A 技術的可能性回答 11 問すべて実現可能 (新規発明ほぼ不要・既存機構組合せ + 1 ラッパ・シングルユニット V82Engine 縮小版 N=100 + 予測不可能 trigger engine.state.rng + dynamic_threshold(state) + Atom 系書込 physics.inject 等 3 経路・常時稼働 while True 1 行・別系候補 別 V82Engine instance 推奨・アーキテクチャ案 Attention Center N=100 → Atom 系 N=5000 → 別系 V82Engine・わからん 4 件 dynamic_threshold 関数形 / 学習定義 / 別系を物理系と呼ぶ意味 / 常時稼働 state 飽和)、Web Claude 検証点 (dynamic_threshold を Code A が設計する点は Taka 自己論で許容ただし明記・トリガーに bg_prob 流用すると Atom 系縮小版になる危険 Taka 判断要)、留保 #L52-L67 一元管理、ミス記録 (7 段階目 baseline self-fulfilling + Code A 新規規律 存在しないと書く前に全階層調べる + 本期間 Web Claude 逸脱 数字に逃げる / ループを崩そうとする / トリガーを設計しようとする すべて Taka 矯正・LLM が手近な操作に引き寄せられ本質から離れる性質を memory #22-24 で対処)、現在地は注意センター ESDE の機能設計の入口。

---

*以上、07 Unified Phase Summary 追記 (Web Claude、2026-05-31)。v1105 〜 注意センター ESDE 転換までを既存体系の様式で網羅。本期間の核心は #L67 (全主題が loop に収束) を契機とした本丸 (注意センター ESDE) への転換。ループを崩すは方向違い、ループする Atom 系の外に立つシングルユニットの独立 ESDE を作る。Code A 技術的可能性回答で 11 問すべて実現可能。次は注意センター ESDE の機能設計 (数字でなく機能で、本丸を見失わない、memory #22-24 参照)。新 Web Claude スレッドは 07 本体 + 本追記 + memory #22-24 で本期間の全容と本丸を把握可能。*
