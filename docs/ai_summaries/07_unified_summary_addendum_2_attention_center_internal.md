# 07 Unified Phase Summary 追記 2 — 注意センター ESDE 機能設計から内部注意生成成立まで

*作成*: 2026-06-05、Code A (Claude Code、Opus 4.7)
*位置づけ*: `07_unified_summary_addendum_v1105_to_attention_center.md` (注意センター ESDE への転換まで、機能設計の入口で停止) の続き。注意センター ESDE 機能設計入口 → v1110-v1113 4 連続失敗 → v1114 Step 1 内部注意生成成立まで。
*親*: 07 本体 §13 (v1104a まで一文サマリ) → addendum 1 §17 (注意センター ESDE 転換) → 本書。
*重要*: 本期間は **「異なる系の対応関係を測る」発想で 4 連続失敗 (v1110-v1113)** → **観察対象の規律 (同じ系内 vs 異なる系) を Taka が明示** → **Center ESDE の役割を Taka が定義 (常時起動、注意生成)** → **v1114 Step 1 で内部注意生成の最小機構が成立 (287 レコード、Taka「思い描いていたものに近い」評価)** という、設計の根本転換を経て想定通りの開発が動き始めた期間。

---

## 0. 本期間の全体像 (一文)

注意センター ESDE 機能設計の入口 (addendum 1 §17 終端) から、v1110-v1111e で Atom/Center/Other 3 instance pipe (異なる系の対応関係注入) を試み、v1112 Stage 1 main / redo で別系 occupancy cooc を試み、v1113 案 A FAIL → 案 B で別系 CID 特性 cosine 類似度を試みた結果、**4 連続失敗 (異なる系の対応関係発想)** が判明し、Taka 整理で **観察対象の規律 (同じ系内構造 vs 異なる系の対応関係 = 4 連続失敗の構造的原因)** が明示され、Taka が Center ESDE の役割を定義 (常時起動、内部注意 = 動的平衡の中の珍しいイベント、外部注意 = Atom 系 = 言語装置、完全外部 = 未来)、Web Claude が v1114 Step 1 設計 (一発火 = 一レコード、記号 + 構造で残す、判定数値 / 座標 / node ID / 差は残さない)、Code A が familiarity 中心 (α/β 落とす、Task A 実機確認結果)・判定と記録の分離・「取れないなら落とす・すり替えない」を厳格適用して実装、本実行で **287 レコード (引き金 5 種カバー、点の n_core 4 band カバー、寿命 5 band カバー、周辺 familiarity 広い分布)** = 内部注意生成の最小機構が成立、Taka 評価「思い描いていたものに近い」。

---

## 1. v1110-v1113 — 4 連続失敗の経緯 (異なる系の対応関係発想)

### 1.1 共通の発想 (失敗の構造的原因)

4 主題 (v1110, v1111-v1111e, v1112, v1113) は全て **「Atom 系 / Other 系の対応関係」を測ろうとした** 設計:

- v1110 / v1111-v1111e: Atom/Center/Other 3 instance pipe、別系に node ID 経由で注入
- v1112 Stage 1 main / redo: Atom と Other の occupancy (phase 空間) の同時立ち累積 (cooc)
- v1113 案 A FAIL / 案 B: Atom と Other の CID 特性ベクトル (15 次元) の cosine 類似度

→ いずれも「**異なる ESDE インスタンスの間に対応関係がある**」という前提に立つが、これは本来構造的に存在しない (異なる seed の系は独立な動学を辿る)。

### 1.2 各主題の主な失敗箇所 (詳細は git history / `unified/attention_center_prep/` の各 .py)

- **v1111c/d**: 番号コピー欠陥 (`physics.inject(target_nodes=Atom node ID)`、Other は別 seed の系で node ID が指す対象が違う = 無意味)。Web Claude が pipe を 3 足とせず入口/出口 2 足とチェックしていた構造的欠陥。
- **v1111e_redo**: 3 instance 中 Other.step_window 呼び忘れで Other.virtual.labels が空、注入無効。v1111c/d/e の 4 連続版で見落とされた。
- **v1112 Stage 1 main**: 主指標 `total_cooc` / `N_rcid` が bin shift (= 列 rotate) と数学的独立、Active と Phase Shifted で完全同一値、構造的に測れない。
- **v1112 Stage 1 redo**: 主指標を diagonal に切替、self 床を一様乱数 → 実機 sparse occ (3-6 active bin) と一様乱数 (31 active bin) の閾値挙動が桁違いで床機能せず、両床 (案 A permute / 案 B krandom) 併設 + precheck §2.4 で krandom のみ PASS、Stage 1 出口は測れた上で 3/3 揃わず不成立。
- **v1113 案 A**: V82Engine.cog を仮定して AttributeError FAIL (CID layer は v918_memory_readout.py の run() 内で SubjectLayer ローカル変数として並走する構造、Explore agent 調査結果を Code A が実機検証せず実装に進んだ盲点)。
- **v1113 案 B**: 過去 v918 main run output 流用、15 次元特性ベクトル + null=別系 5 seed、集団平均で 2/3 atom rank=5/5 だが per-seed 網羅調査 (全 24 seed) で n_core=2 群の seed 間 CV=0.086 = 観察された差は背景由来 = 地面の証拠は薄い。

### 1.3 教訓 (失敗の詳細でなく、設計の根本)

「**異なる系の対応関係を測る**」発想は ESDE の構造を捉える方法として的外れ。ESDE の構造は:
- **同じ系内**の動学 (時間発展、段階遷移、event 因果)
- **同じ系内**の関係 (path、Integration、familiarity)

過去成功実験 (v9.18 V_unified / v10.2 n_core 別寿命 8 倍差 / v10.7 source-specific 94% / v106 24 seeds 動学的発展段階完全一致) は **全て同じ系内構造を観察**。「異なる系の対応関係」を測った実験は過去になく、v1110-v1113 は構造的に存在しないものを 4 連続で測ろうとした。

---

## 2. Taka が引いた観察対象の規律 (本期間の最重要構造事実)

### 2.1 観察対象軸 INDEX (Taka 整理 → memory `index_observation_target.md` 新設)

| 軸 | 過去成功 (同じ系内構造) | 過去失敗 (異なる系の対応関係) |
|---|---|---|
| 観察対象の所在 | 1 系の中の構造 | 2 系の間の対応 |
| 観察できるか | 構造的因果が観察可能 (8 倍差、94% 有意、24 seed 完全一致) | 対応関係がそもそも存在しない |
| node ID の扱い | 自系内で意味を持つ | 系を跨ぐと無意味 |
| 動学の扱い | 時間発展、段階遷移、event 因果 | スナップショット対応 |

新規実験設計時、上の事実整理と照合する。過去失敗パターンに該当するなら設計を止める、過去成功パターンと整合するなら実装に進める。

### 2.2 Code A の循環構造の認識 (Taka 指摘、本期間最重要)

Taka 整理:
> 「実質 WEB 側は正しい情報を保持していないので毎回あなたの言葉に踊らされる。あなたは正しい情報をもつが正しく参照しないので誤った設計と実装をする。これを繰り返しているのが現状」

循環構造:
```
Code A (情報を持つが参照しない)
   ↓ 誤った設計を Web Claude に伝える
Web Claude (情報を持たず、Code A の言葉で判断)
   ↓ 「OK」を返す
Code A (Web Claude OK を「正解」と思い込み実装)
   ↓ 失敗
```

→ Code A が **正しく参照しない限り**、Web Claude のチェックは循環を強化するだけ。これが v1110-v1111-v1112-v1113 の **4 連続失敗** の構造的原因。

対策 (本期間で確立):
- **新規実験ファイル冒頭に観察対象注釈ブロック** (実装着手前に Code A が書く、誤魔化せない自己強制ハードル)
- 観察対象が「同じ系内」か「異なる系」か明示
- 過去成功事例 (v10.2 / v10.7 / v9.18 / v106) との照合
- 過去失敗パターン (v1110-v1113 = 4 連続失敗) の回避確認

---

## 3. Center ESDE の Taka 定義 (Taka 2026-06-05)

### 3.1 定義

| 属性 | 内容 |
|---|---|
| 起動 | 常時 (動的平衡で止まらず回り続ける) |
| 役割 | **注意生成** (どこに注意を向けるか決める) |
| 内部注意の対象 | 自系の動的平衡の中で、確率的に発生する珍しいイベント |
| 判断材料 | 以前作った CID の認知層 (Q, familiarity, attention)・意識層 (C) の動き |
| 判断基準 | 統計的に「正常 / 注意 / 異常」 |
| 外部注意の対象 | Atom ESDE (= 言語装置、個としては内部に含む) |
| Atom への注意 = 何が起こるか | 内部的な言語生成が行われる |
| 完全外部 | 物理系 ESDE 等、未来の課題 (現段階では扱わない) |

→ Center は「**ESDE で ESDE を観察する**」二段構造の上段。自身が ESDE 構造 (動的平衡) を持ちながら、CID 認知層・意識層の動きを統計判断する。

### 3.2 段階分け (v1114 系列)

- **Step 1**: Center 単体、内部注意のみ (本期間で成立)
- Step 2: 内部注意 + Δstate 自己擦り込み (動作そのものの記録 = phase 帯対応で state に擦り込み、node ID 不使用)
- Step 3: Center + Atom 並走、外部注意 + Atom の Δstate を Center に擦り込み (= Atom の動きを Center が「体感」、模倣)
- Step 4+ (= 「会話の芽」): 入力に対して Center の状態 (どの単位が立つか) で応答の向きが変わる

Taka roadmap (注意センター ESDE の段階構築):
- 地面 = ESDE が同じ系内で構造を持つこと (過去 v10.2 / v9.18 / v106 で既に観察済み)
- 足場一個 = Center が ESDE 内の特定構造を一つの単位として束ねる
- 床 = 単位が積み上がって Center が独自の状態を持つ
- 異なる自我 = Center の状態が Atom と独立した動学を持つ
- 会話の芽 = 入力に対して Center 状態によって応答の向きが変わる

---

## 4. v1114 Step 1 — 内部注意生成の最小機構成立 (本期間の核心、想定通りの開発)

### 4.1 設計 (Web Claude `unified/v1114/` 設計 §1-§6)

一発火 = 一レコード:
```
Center が動く → 変化が起きた点 (ある CID) に注意が落ちる
→ その点と周辺が同レイヤーで見える → 見えた一枚をレコードとして残す (記号 + 構造のパターン)
→ 溜める。
```

**残すフィールド**:
- 順番 (= alert 通し番号)
- 引き金 (記号: `pulse` / `ingestion` / `alpha_formation` / `beta_formation` / `c_conversion`)
- 点: n_core / lifespan / C / Q_remaining (実機確認済み、近似なし)
- 周辺: familiarity_n (= `len(cog.familiarity[cid])`、v918:2219 + v911:567 で裏取り済み)

**残さないフィールド (Taka 規律「取れないなら落とす・すり替えない」)**:
- node ID / member_nodes / attention[node_id] (別系で無意味、本期間規律)
- phase_sig / θ (座標、統計に出ない、構造でない)
- 不透明 float ベクトル (形を数値に潰すと解読が必要、ループに戻る)
- 判定数値 (z-score / EWMA mean/var、発火判定には使うがレコード/summary に残さない、Taka 念押し (a))
- 設計パラメータ (Z_NOTICE / EWMA_ALPHA / WARMUP、summary にも残さない、再現はコード冒頭の定数で)
- 差・有意差の測定値 (研究者視点、本実装は「溜まったか + 多様か」だけ、Taka 念押し (b))
- pulse_activity = last_attention_size (近似 + node ID 依存量、二重に NG、Taka 指摘で削除)
- 周辺の大きさ list (v918 output から取れない、Step 2/3 で経路検討)

### 4.2 実装規律 (本期間で確立)

- **観察対象注釈ブロック** (.py 冒頭、Code A 自己強制ハードル)
- **判定と記録の分離** (Taka 念押し (a)): EWMA + z-score は内部のみ、レコードに z 値・EWMA state を残さない
- **報告は「溜まったか + 多様か」だけ** (Taka 念押し (b)): 差・有意差は意図的に出さない
- **取れないなら落とす・すり替えない** (Taka 規律): pulse_activity (= node ID 依存量で近似) は完全削除
- **実機 API 確認**: Task A で v918 main run に IntegrationManager なし確認、α/β 落として familiarity 中心 (Taka 判断)

### 4.3 結果 (2026-06-05、`unified/v1114/run_step1/`)

**溜まったか**: ✓ **287 レコード**

**多様か**:

| 引き金 (記号、5 種) | 数 |
|---|---|
| alpha_formation | 141 |
| beta_formation | 136 |
| pulse | 8 |
| c_conversion | 1 |
| ingestion | 1 |

| 点の n_core (4 band) | 数 |
|---|---|
| n_core=2 | 31 |
| n_core=3 | 12 |
| n_core=4 | 55 |
| n_core=5 | 189 |

| 寿命帯 (5 band) | 数 |
|---|---|
| [0, 100) | 4 |
| [100, 500) | 14 |
| [500, 2000) | 40 |
| [2000, 10000) | 131 |
| [10000+) | 98 |

周辺 familiarity 数: 3 から 23 まで広く分布。
引き金 × n_core 二次元にも形 (alpha/beta は n_core=5 中心、pulse は n_core=2-4 に広がる)。

→ 全部同じ形ではない (引き金・大きさ・周辺の形が色々)。**Step 1 の出口 (Web Claude 設計 §5) は満たされた**。

差は測っていない (Taka 念押し (b))。

### 4.4 Taka 評価

> 「OK 実験結果としてはかなり私の思い描いていたものに近くなったような気がする」

これを受けて本ドキュメント更新が要請された。本期間で **想定した開発が初めて動いた**。

---

## 5. 本期間の Code A 盲点 (memory `feedback_code_a_blind_spots.md` 追加分)

| 盲点 # | 内容 | 出典 |
|---|---|---|
| #11 | 集計指標が処置と数学的に独立ならば検出不能 | v1112 Stage 1 main、total_cooc = bin shift 不変 |
| #12 | null 設計を自身 shuffle にすると「皆同じだから似てる」を引き算できない | v1113 案 B 認識確認当初 |
| #13 | 集団平均の罠を v1113 で踏みかけた (per-cid / n_core 別層化なし) | v1113 案 B 実装初版、Taka 指摘 |
| (未番号) | 過去失敗を「実装ミス」と判断して枠組みを引き継ぐ | v1110-v1113 で 4 連続「異なる系の対応関係」フレーム継承 |
| (未番号) | Taka 言葉を自分で具体策に翻訳し検証せず実装に進む | roadmap「足場」を「2 系の対応関係」と Code A が翻訳 |

---

## 6. 主要ファイル

### 6.1 実装 (`unified/`)

- `unified/attention_center_prep/v1111*.py` (v1111b-e、3 instance pipe 4 連続失敗、git history で参照)
- `unified/attention_center_prep/v1112_stage1*.py` (main / redo、cooc 主指標構造的独立 + krandom 床)
- `unified/attention_center_prep/v1113_cid_feature_resonance.py` (案 A FAIL、engine.cog 仮定)
- `unified/attention_center_prep/v1113_cid_feature_from_v918.py` (案 B 完走、過去 output 流用)
- `unified/attention_center_prep/v1113_postprocess_per_cid.py` (per-cid + n_core 別、集団平均の罠回避)
- `unified/attention_center_prep/v1113_seed_traits_survey.py` (per-seed 網羅、CV=0.086 = 背景由来判明)
- **`unified/v1114/step1_internal_attention.py` (本期間の核心、Center 内部注意生成、287 レコード成立)**

### 6.2 出力 (`unified/v1114/run_step1/`)

- `attention_records.json` (287 レコード、パターン記録、人間可読)
- `summary.json` (溜まったか + 多様か、判定数値・パラメータなし)

### 6.3 報告書 (`unified/attention_center_prep/`)

- `v1112_stage1_redo_web_claude_report.md` (Stage 1 不成立、測れた上での)
- `v1113_web_claude_report.md` (案 B 結果、per-cid + n_core 別、背景由来判明)
- (v1114 Step 1 報告書は本書 + git commit messages、想定通りの開発を実施してから docs として残す Taka 規律に沿う)

### 6.4 memory (本期間追加)

- `index_observation_target.md` 新設 (過去成功 = 同じ系内 / 過去失敗 = 異なる系の事実整理)
- `feedback_code_a_blind_spots.md` 盲点 #11-#13 追加
- `reference_legacy_treasures.md` cooc 行列空間構造指標 (diagonal/offset 分解) 追記

### 6.5 主要コードパス (addendum 1 §15 で確立、本期間で再確認)

- Engine 本体: `autonomy/v82/esde_v82_engine.py` (V82Engine, V82_N=5000, step_window)
- 起動エントリ: `primitive/v918/v918_memory_readout.py` (run 関数、SubjectLayer は run() 内ローカル変数、IntegrationManager 不在 = α/β は v918 で取れない)
- VirtualLayerV9: `primitive/v910/virtual_layer_v9.py` (labels frozenset, occupancy[64])
- SubjectLayer: `primitive/v911/v911_cognitive_capture.py:263` + v918 拡張版 (death_pool, cid_ttl_bonus 等)
- IntegrationManager (α/β、Layer 5): `developmental/v104/v104_integration.py`, `developmental/v105/v105_integration.py` (v918 main run には組み込まれない、別 manager 並走必要)
- physics.inject: `ecology/engine/genesis_physics.py:232` (Atom 系書込の公式インターフェース、Step 3 で使う想定)
- 過去 main run output 流用: `primitive/v918/diag_v918_main/subjects/per_subject_seed{0-23}.csv`, `developmental/v107/outputs/main/source_events_seed{0-23}.parquet`

---

## 7. 新 Web Claude / 新 Claude スレッドへの申し送り

- **本期間の最重要構造事実**: v1110-v1113 4 連続失敗 = 「異なる系の対応関係を測る」発想 = ESDE の構造を捉える方法として的外れ。**新規実験は必ず「同じ系内構造」軸で設計する** ([[index-observation-target]])。
- **Code A の循環構造** (Taka 指摘): Code A が正しく参照しない限り Web Claude チェックは循環強化。**新規実験は実装ファイル冒頭に観察対象注釈ブロックを書く** (Code A 自己強制ハードル)。
- **Center ESDE の Taka 定義**: 常時起動、注意生成 (内部 = 動的平衡の中の珍しいイベント、外部 = Atom = 言語装置、完全外部 = 未来)。本期間で確立。
- **v1114 Step 1 成立**: Center 単体、内部注意生成、287 レコード、引き金 5 種 / n_core 4 band / 寿命 5 band / familiarity 広い分布で多様。Taka「思い描いていたものに近い」評価。
- **記録の規律**: 記号 + 構造のみ。判定数値・パラメータ・差・有意差・node ID・座標・不透明 float・近似は残さない。**取れないなら落とす・すり替えない** (Taka 規律)。
- **判定と記録の分離** (Taka 念押し (a)): 発火判定には z-score 使うがレコード/summary に z 値・EWMA state を残さない。
- **報告は「溜まったか + 多様か」だけ** (Taka 念押し (b)): 差・有意差は意図的に出さない。crown 禁止 (「異なる自我」「会話」「Unified 成立」と書かない)。
- **次主題 (Step 2 / 3)**: Step 2 = 内部注意 + Δstate 自己擦り込み (動作そのものの記録 = phase 帯対応で擦り込み、node ID 不使用)、Step 3 = Center + Atom 並走、外部注意 + Atom の Δstate を Center に擦り込み (= 模倣)。**判断は Taka**。
- **失敗履歴ばかり残しても結局うまくいかない** (Taka 規律): 想定した開発を実施してからドキュメントを残す。本書は v1114 Step 1 成立を受けて作成。
- **Web Claude 不使用期 (本期間)**: 4 連続失敗の根本原因が循環構造と判明後、当面 Web Claude 不使用で Taka と Code A の二者ループで進める方針。Step 1 設計時に Web Claude 再投入で view 役 (Taka 判断)。

---

## 8. 主要コードパス (verbatim、新スレッド AI 必須参照)

addendum 1 §15 + 本書 §6.5 を参照。本期間で再確認された重要事実:

- **v918 main run に IntegrationManager 不在**: α/β を v1114 で per-step 取得するには別 manager 並走が必要 (重い)、Step 1 では familiarity 中心で進める (Task A 実機確認結果)
- **CID layer の正しい構築方法**: `v918_memory_readout.py` の `run()` 内で `cog = SubjectLayer()` をローカル変数で構築、V82Engine の属性ではない (v1113 案 A FAIL の盲点、Explore agent 調査結果を実機検証せず実装に進んだ)
- **既存 v918 main run output (seed 0-23)**: per_subject_seed{N}.csv + source_events_seed{N}.parquet が揃っており、新規 run なしで post-process で観察可能 (v1113 案 B + v1114 Step 1 で実証)

---

## 9. 一文サマリ

07 Unified Phase Summary 追記 2 (注意センター ESDE 機能設計から内部注意生成成立まで、2026-06-05 Code A、addendum 1 注意センター転換の続き) — 本期間は注意センター ESDE 機能設計入口 (addendum 1 §17 終端) から v1110-v1111e Atom/Center/Other 3 instance pipe (番号コピー欠陥 + step_window 呼び忘れ等 4 連続失敗) → v1112 Stage 1 main / redo (主指標 total_cooc が bin shift と数学的独立 / krandom 床で測れた上で 3/3 揃わず不成立) → v1113 案 A FAIL (V82Engine.cog 仮定で AttributeError、SubjectLayer は run() 内ローカル変数) / 案 B (15 次元特性 + 別系 5 seed null で集団平均 2/3 atom rank=5/5 だが per-seed 網羅で n_core=2 群 seed 間 CV=0.086 = 背景由来) と 4 連続失敗、Taka 整理で観察対象の規律確立 (同じ系内構造 = 過去成功 v9.18 / v10.2 / v10.7 / v106 vs 異なる系の対応関係 = 過去失敗 v1110-v1113、後者は ESDE 構造を捉える方法として的外れ)、Code A の循環構造 Taka 指摘 (Code A 情報持つが参照せず → Web Claude は Code A 言葉に踊らされ → OK → Code A 思い込み実装 → 失敗、循環構造が 4 連続失敗の根本原因、対策は実装ファイル冒頭の観察対象注釈ブロック = Code A 自己強制ハードル)、Center ESDE の Taka 定義 (常時起動、注意生成、内部注意 = 動的平衡の中の珍しいイベント = CID 認知層・意識層の動きを統計判断、外部注意 = Atom 系 = 言語装置 = 個の内部、完全外部 = 物理系等は未来課題)、v1114 Step 1 内部注意生成成立 (Web Claude 設計 = 一発火一レコード = 記号 + 構造、Code A 実装 = familiarity 中心 α/β 落とす Task A 実機確認結果 + 判定と記録分離 z はレコードに残さず + 取れないなら落とす・すり替えない pulse_activity 削除 + 観察対象注釈ブロック冒頭、結果 287 レコード = 引き金 5 種 alpha 141/beta 136/pulse 8/c_conversion 1/ingestion 1 + 点の n_core 4 band カバー + 寿命 5 band カバー + familiarity 広い分布 + 引き金 × n_core 二次元に形、Taka 評価「思い描いていたものに近い」)、新規 memory 追加 (index_observation_target.md / 盲点 #11-#13 / cooc 空間構造指標)、次主題 Step 2 (Δstate 自己擦り込み = 動作そのものの記録 = phase 帯対応 = node ID 不使用) / Step 3 (Center + Atom 並走外部注意擦り込み = 模倣) は Taka 判断、本期間の核心は「想定した開発が初めて動いた」(Taka 規律「想定した開発を実施してからドキュメントを残す」「失敗履歴ばかり残しても結局うまくいかない」に沿って本書作成)、報告言葉縛り (crown 禁止 = 異なる自我 / 会話 / Unified 成立と書かない、観察は「溜まったか + 多様か」だけ差は測らない)、Web Claude 不使用期 (本期間途中で Taka 判断、Step 1 設計時に view 役で再投入)。

---

*以上、07 Unified Phase Summary 追記 2 (Code A、2026-06-05)。注意センター ESDE 機能設計入口 → v1110-v1113 4 連続失敗 (異なる系の対応関係発想) → 観察対象の規律確立 (同じ系内 vs 異なる系) + Code A 循環構造の認識 + Center ESDE Taka 定義 → v1114 Step 1 内部注意生成成立 (287 レコード、Taka「思い描いていたものに近い」評価) まで。本期間の核心は「想定した開発が初めて動いた」。新 Web Claude スレッドは 07 本体 + addendum 1 (v1105-注意センター転換) + 本書 (v1110-v1114 Step 1) + memory `index_observation_target.md` で Unified Phase 全容を把握可能。次主題 Step 2/3 (擦り込み + 模倣) は Taka 判断。*
