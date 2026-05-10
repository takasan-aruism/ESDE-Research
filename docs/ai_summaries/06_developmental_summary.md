# 06 Developmental Summary

*作成*: 2026-04-28、Claude (相談役)
*更新*: 2026-05-06 (v10.6 反映)
*対象*: ESDE Developmental フェイズ (v10.x 系列)
*親資料*: ESDE_Developmental_Report.md (詳細版)
*位置づけ*: AI summaries の 1 つ。Developmental フェイズの要約。Primitive Summary (05) と並列。

---

## 0. このドキュメントの位置づけ

ESDE_Primitive_Summary.md (05) が v9.x までの Primitive フェイズの要約だったのに対し、本ドキュメントは v10.x 以降の Developmental フェイズの要約である。

Primitive フェイズで確立されたもの (簡略):
- 物理層 / 存在層 / 認知層 (3 層) の動作機構
- 意識の原資モデル (v9.18 で言語化)
- 死の二階層 / 燃料概念の発生階層 (v10.x 接続用に整理)

Developmental フェイズの主題:
- 意識層 C の動作機構化
- 摂食機構の導入
- 認知/意識の確率的バランス
- 物理層から意識層までの構造的継承の観察

---

## 1. Developmental フェイズの構造概観

### 1.1 4 層アーキテクチャの確定 (v10.0)

```
意識層 (Layer C): C、選択的鮮明、シングルタスク [v10.2 で実装]
認知層 (Layer B): Q、ぼやける全体把握 [v9.x からの継続]
存在層 (Layer A): Label / member_nodes、ghost 化 [v9.x からの継続]
物理層: engine、virtual_layer、frozen [v9.x から frozen]
```

意識層は v10.2 で初めて動作機構として実装。それまでは概念のみ。

### 1.2 Developmental フェイズの段階

```
v10.0: フェイズ宣言 + 4 層確定 + 死の二階層 + 燃料概念
v10.1: Minimal Ingestion (摂食機構導入)
v10.2: Probabilistic Cognitive-Conscious Balance (確率決定 + 意識層 C 実装)
v10.3: 双方向 E3 機構 + Integration 登場条件の観察 (Layer 5 入口)
v10.4: Integration 独立化 (Layer 5 構造化)
v10.5: Layer 5 完成 (α/β 階層分離 + 顕在化機構) [Phase 1 完了]
v10.6: Genesis × Language 比較研究 (Phase 1.5 第一試行)
```

### 1.3 各バージョンの完了状況

| バージョン | 主題 | 完了 |
|---|---|---|
| v10.0 | Developmental フェイズ宣言 | ✅ |
| v10.1 | Minimal Ingestion | ✅ |
| v10.2 | Probabilistic Cognitive-Conscious Balance | ✅ |
| v10.3 | 双方向 E3 機構 + Integration 登場条件 | ✅ |
| v10.4 | Integration 独立化 | ✅ |
| v10.5 | Layer 5 完成 (α/β 階層分離 + Salience + Leakage) | ✅ |
| v10.6 | Genesis × Language 比較研究 (Phase 1.5 第一試行) | ✅ |
| v10.7 | 発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成) | 完了 |
| v10.8 | Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5) | 完了 |
| v10.9 | 寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達) | 完了 |
| v10.10 | 主題候補 (条件適応型 atom 導入 / high_fam_out 構造解明 / Atom 常駐アンカー / B 群試験 / QC_cost 評価) | 検討中 |

---

## 2. v10.0: Developmental フェイズ宣言

### 2.1 フェイズ名の確定

- 「Cognitive」: 認知層に閉じすぎ
- 「Conscious」: 意識層を主題化しすぎ
- 「Developmental」: 発達期、認知層と意識層の協働を扱う

v5-v7 で「夢を見すぎた」反省を埋め込む命名。

### 2.2 4 層アーキテクチャ

物理層 frozen の継続、Layer A bit-identity 維持を前提に、意識層 (Layer C) を新規導入する設計。

### 2.3 死の二階層 (Taka 整理 2026-04-24)

| 階層 | 条件 | 状態 |
|---|---|---|
| 存在層の死 | Label 死亡 (detach) | ghost 化 |
| 認知層の死 | 残 Q = 0 | ghost 消滅 |

ghost = 「魂が抜けた容器」。原資 (Q) を保持する限り存在し続け、Q=0 で消滅。固定 TTL (v9.x の GHOST_TTL=10) は v10.1 で除去。

### 2.4 燃料概念の発生階層 (Taka 整理 2026-04-24)

- 物理層・存在層: エネルギー概念なし
- 認知層: Q が定義
- 意識層: C が定義 (Q から転化)

C は認知層の Q 消費から転化される。物理層・存在層は frozen のまま。

---

## 3. v10.1: Minimal Ingestion

### 3.1 主題

ghost を Q ベースで扱い、E3 接触圏内の摂食機構を最小実装する。

### 3.2 動機

- 旧仕様 (GHOST_TTL=10 固定): 個体差なし、神の手
- 新仕様 (Q ベース): 生前活動量を residual_Q に反映、不均一な資源地形
- ghost を「資源として利用可能にする構造」を導入

### 3.3 実装範囲

```
新規:
  ghost.residual_Q (ghost 化時点の Q_remaining 完全継承)
  摂食機構 (1 step に 1 ghost を食べきり、Q0 で頭打ち、消化分は散逸)
  step 末一括 reap (空摂食許容)
  pickup 機構廃止 (v9.8c で導入されたもの)
  ingestion_rng (摂食ランダム選定用、seed ^ 0x1A7E57)

維持:
  物理層 frozen
  Layer A bit-identity
```

### 3.4 仕様の主要決定 (Taka 確定)

- 摂食量: 1 step に 1 ghost の residual_Q を全部取得 (1 ghost 食べきり)
- 1 CID:多 ghost = ランダム選定 (seeded RNG)
- 多 CID:1 ghost = cid_id 昇順
- 飢餓判定撤廃: 満腹でも摂食可、Q0 超過分は消化分として散逸
- 空摂食許容: residual_Q=0 でも reap 前なら摂食試行可
- 摂食独自の Q 消費なし (E3 接触で -1 は既存通り)

### 3.5 本番 run 結果

```
24 seeds × tracking 50、subject 数 5,224 (v9.18 と完全一致)
wall time: v9.18 比 0.991x
摂食イベント: 3,588 件
ユニーク eater: 1,361 (subject の 26.0%)
ghost 食糧化率: 78.0%
消化分: 16.73%
phantom contact: 48,625 件 (摂食の 13.6 倍)
```

### 3.6 v10.1 で観察された重要発見

#### 発見 1: phantom contact の規模

物理層 (`_node_to_cids`) に cid retire 後も痕跡が残る設計のため、E3 接触の対象が「既に消滅した cid」になるケースが大量発生。摂食 3,588 件に対し phantom 48,625 件。

#### 発見 2: 「物質的なもの」の位置づけ (Taka 整理 2026-04-26)

phantom = CID 主体間の問題ではなく**物質的環境**:
- 看板や道路のような静的な環境要因
- ランダム発生のイベント因子
- CID 主体間の問題から一段下げる

これは ESDE で「主体性のない認知層要素」が初めて定義された瞬間。

#### 発見 3: GPT 主題化提案への Taka の判断

GPT 監査が「主役は phantom contact」と方向転換を提案したが、Taka は主題化を却下:
- phantom = 想定の能力不足の現れ
- 「物質的なもの」と位置づければ問題化しない
- v10.2 は本来の主題を扱う

「監査が主題判断に越権するリスク」の実例として記録。

### 3.7 v10.1 の動機の再解釈

実装結果を踏まえて、Taka の元動機が仕様の進化に伴って意味が変わった:
- 元意図「ghost 期間の不自然さ解消」 → 新意味「ghost を不均一な資源地形として扱う」
- 元意図「飢え死に救済」 → 新意味「ghost を資源として利用可能にする構造の導入」

これは Taka 哲学「構造が先、定義は後」の実例。

---

## 4. v10.2: Probabilistic Cognitive-Conscious Balance

### 4.1 主題

意識層資源 C を導入し、Q と C の比率でイベント時に認知/意識のどちらが立つかを確率決定する機構を実装。

### 4.2 動機 (4 つ)

1. v9.18 で言語化された意識の原資モデル (Q → C 転化) を動作機構として最初に実装
2. v10.1 の機械的摂食からの脱却 (確率発動への変更)
3. 認知層と意識層の協働の最初の動作
4. **階層論的構造の確率による圧縮** (Taka 整理 2026-04-27): 本来は認知 → 意識 → 行動 → 接触の四段階を確率で圧縮表現

### 4.3 解釈 X (Code A 指摘 → Taka 採用)

既存の E3 spend (Q-1) が「認知活動」と同義と位置づけ:
- 認知が立つ: Q-1 + C+1 + virtual_attention/familiarity 更新
- 意識が立つ: C-1 + 摂食発動 (Q-1 はしない、virtual 更新も止まる)

「認知活動」を新規概念として実装で増やさない美しい解釈。

### 4.4 確率決定の対象

- E3 onset のみ確率決定の対象
- E1 / E2 は従来通り無条件 Q-1 (確率対象外、C 蓄積に寄与しない)
- 双方向 E3 (hosted-hosted): 必ず認知確定 (三項共鳴は v10.3)
- 空摂食ケース (residual_Q=0 ghost): 認知確定
- phantom (reaped 済 cid): 認知確定

### 4.5 確率式 (Taka 確定、シンプル案採用)

```
P(認知) = Q / (Q + C)
P(意識) = C / (Q + C)
```

### 4.6 C の仕様

- 配置: Layer C (cog.C、SubjectLayer 内)
- 初期値: 0
- 上限: なし (Taka 判断、観察優先)
- 死: 認知層の死 (cid 消滅) に連動、独自定義なし
- C=0 状態: 一時的機能停止 (回復可能)

### 4.7 即時摂食 (Code A 案 B、step 内動的連鎖)

確率決定で意識が立った瞬間に attempt_ingestion を呼ぶ。これにより:
- 先行 cid が ghost を食べきる
- 後続 cid の候補集合が動的に変わる (residual_Q=0 で意識候補消失)
- 後続 cid は認知確定

v10.1 の機械発動からの本質的な変化点。

### 4.8 二層 bit-identity 検証

- 層 A (v10.2 内部): smoke 2 連続 run、26/26 CSV MD5 一致 ✅
- 層 B (vs v9.18 baseline): E1/E2 行 70/70 完全一致 ✅、E3 行は意識当選で乖離 (想定通り)

Taka 指示「インパクト事前想定 + ギャップ観察」の実践。

### 4.9 本番 run 結果 (24 seeds × tracking 50)

#### 集団全体

```
24/24 seeds 完走、wall time +0.4%
subject 5,224 完全一致

確率決定:
  認知当選: 56.79%
  意識当選: 3.50%
  skip (C=0 で意識候補のみ): 39.71%

摂食動態 (v10.1 比):
  空摂食: 134 → 0 (完全消失)
  phantom: 48,625 → 0 (完全消失)
  eater 比率: 26.0% → 22.2%
  total_received: +7.2%、total_digested: -25.6%

C 蓄積:
  C_max mean: 71.7、C_p50: 24.5、p95: 62.3
  上限なしでも暴走しない自己均衡
```

#### 5 つの主要発見

1. **空摂食 / phantom 完全消失**: 即時摂食 + 動的連鎖の効果
2. **C=0 skip 39.71%**: 意識候補成立しても C 不足で skip
3. **意識発動の自然フィルタ**: C 蓄積が必要、誰でも発動できない
4. **C 上限なしでも暴走しない**: 動的均衡が自己組織化
5. **動的均衡 = 進化終端の兆候なし**: 進化継続中

### 4.10 n_core 別層化解析の発見 (Taka 指示 2026-04-28)

集団平均の罠を超えて見えた構造的継承:

| n_core | cid 数 | 寿命 | 認知活動 | 意識活動 | C 蓄積 (p50) | 意識発動経験率 |
|---|---|---|---|---|---|---|
| 2 | 3,968 (76.0%) | 1,716 | 5.18 | 0.13 | 8 | 10.1% |
| 5 | 638 (12.2%) | 13,598 | 38.24 | 3.25 | 35 | 73.2% |

n_core=2 → n_core=5 で寿命 8 倍、意識活動 25 倍。

#### 物理層 → 認知層 → 意識層の構造的継承

設計したのは単一の確率ルール (P(認知) = Q/(Q+C)) のみ。しかし結果として:
- n_core (物理層) で決まる構造が
- 寿命・Q 蓄積 (認知層) に反映され
- C 蓄積・意識発動率 (意識層) にまで継承される

意識層という新しいレイヤーが、下位層由来の構造差を忠実に反映する。

#### Taka の言語化

> ノード数は構造の複雑を意味し、それゆえに認知や意識といった高度な概念が発生するという前提を置いていた。それが今回見事に形になった。

ESDE 設計時からの前提が v10.2 で形になった。インビジブル期間 (v9.15-v10.2 で統合指標がメイン) を経て、ノード別の構造が再可視化された。

### 4.11 詳細解析 (Code A 実施、5 本)

| 解析 | 主要観察 |
|---|---|
| 1 個別性 | 誕生時 Q0 では予測不可。寿命と初回 cognition タイミングが分岐の主因 |
| 2 トポロジー | n_core=2 は 89.9% no_activation、n_core=5 は 34.0% repeated (対称的二極化) |
| 3 時系列 | C 60 倍蓄積、Q 92% 減、(Q+C) per_capita 安定 (動的均衡兆候)。run 末で 60% が n_core=5 |
| 4 偏在 | 全体 Gini ~0.33 (中程度)、主因は n_core 階層差。C 総和の 73% が n_core=5 |
| 5 初回発動 | 摂食成功率 100%、n_core=5 で phase 0.19、n_core=2 で phase 0.46 |

#### 4 つの新規発見

1. 誕生時 Q0 が分岐の決定要因ではない (予測を覆す)
2. 寿命と初回 cognition タイミングが主因
3. 初期認知活動密度の逆相関 (反直感)
4. 摂食成功率 100% の構造的確認 (即時摂食設計検証)

### 4.12 v10.3 三項共鳴の主役候補絞り込み

```
n_core=5 の repeated 群: 217 cid (4.2%)
n_core=4 の repeated 群: 53 cid (1.0%)
合計 ~270 cid が三項共鳴の中心になりうる cid
```

系の状態: C 蓄積期から飽和期への移行、タイトな環境。

---

## 5. v10.3: 双方向 E3 機構と Integration 登場条件の観察

### 8.1 主題

生きた cid 同士の意識層レベルの接触を機構として最小追加し、Layer 5 (CID 共鳴) の入口を開ける。

### 8.2 三層構造の確定

| レベル | 位置づけ |
|---|---|
| 双方向 E3 | 機構 (両者 C-1) |
| 三項共鳴 | 観察される統計的現象 |
| Integration | 上位解釈 (概念のみ、機構は v10.4 以降) |

### 8.3 双方向 E3 と C 消費の意味づけ

両者 hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触で両者 C-1。Taka 整理:「観察者が決めた記録ルール」(cid 内部選択ではない)。

### 8.4 Integration 概念 (Taka 整理 2026-04-29)

ESDE 階層進化系譜:
```
ノード → cid → ??? (v10.3 観察対象) → SEED 統合
```

機構実装は v10.4 以降。

### 8.5 本番 run 結果

- 双方向 E3 fired 6,824 件 / 24 seeds
- 物理層 frozen 完璧維持 (labels 24/24 + persistence 96/96)
- C 蓄積 27% 抑制 (観察ルールが系の動学を変える)
- open triad 99% 支配 (closed triad 1.4%)
- 持続性ゼロ (repeated_partners=0)

### 8.6 v10.3 で確立した規律

- 機構と観察と解釈の三層分離
- 「観察者が決めた記録ルール」
- 動的絞り込みと bias 監視のセット運用
- 第三項候補の多軸記録
- Paired Audit 原則の継続

---

## 6. v10.4: Integration 独立化

### 6.1 主題

Integration を独立した主体として機構化。Layer 5 (CID 共鳴) の本格実装。

### 6.2 Taka 設計の核心 (2026-04-30)

**国家の比喩**:
> CID のどの要件を満たせばそれは Integration なのか、という議論はわりと雑でいい。
> しかしサボらずにしっかり扱っておくと、いつしかそれらしいものとなってその存在を前提として扱うことができる。

**物理層 frozen の本意の再定義**:
> 物理層という言葉もちょっとよくないのだが、私はこれを不可知なランダム性に手を出すってなんだ?ということだ。
> 階層分離は意図的に分けておきましょうね、という程度の意味である。だからこそ統合も可能となる。

### 6.3 Integration の機能

1. 資源集約 (構成 cid の Q/C を集約)
2. 資源分配 (構成 cid に再分配)
3. 調整機能 (認知層・意識層への間接バイアス)
4. 記録機能 (Integration + cid 個別記録、両者並存)

Ghost 化した構成 cid の Q/C は最強結合 Integration が全継承 (Taka 整理「二重国籍者の遺産は片方のみ」)。

### 6.4 v10.4 の実装範囲 (Taka 判断「現状最大値」)

3 AI が「v10.4 初手は最小化」を提案したが、Taka は拒否:
> 観測は論理を超える。まずは頭でっかちにならずに色々見てみる。

採用:
- 誕生条件: be3 / open_triad / closed_triad / third_overlap (R1 全採用)
- 1 cid が複数 Integration 同時所属可 (R3-c)
- Q/C 継承: 最強結合 1 つに全継承 (R5)
- 二層状態: recorded / active (recorded 永続)
- 調整機能: D4-a + D4-b + 状態依存再分配

### 6.5 本番 run 結果 (24 seeds × tracking 50)

- Integration 13,550 件誕生
- trigger: be3 52% / open_triad 38% / third_overlap 9% / closed_triad 0%
- 物理層 frozen 完璧維持 (labels 24/24 + persistence 96/96)
- wall time +0.6%

### 6.6 系の動学変化 (v10.3 と逆方向)

| 指標 | v10.3 | v10.4 | 方向 |
|---|---:|---:|---|
| C_max | -26% | **+31%** | 逆転 |
| C_mean | -27% | **+15%** | 逆転 |

Integration が死者の Q/C を生者へ継承・再分配 → C 蓄積増。

### 6.7 凍結問題 + ハブ cid 発見

- C の 87% が recorded Integration に「凍結」(歴史的記録の累積)
- 1 cid あたり所属 Integration 数 max 102 (ハブ cid)
- 受領 cid 数 67% (33% は何も受け取らない)

ハブ cid は神の手なし、6 段の自然なフィードバックループで出現 (Code A 発見)。

### 6.8 closed_triad ゼロ問題

24 seeds × 50 windows で closed_triad 0 件。be3 run-wide dedup により 3 cid 全ペア接触は構造的に成立しない。

### 6.9 ダブルブッキング問題の認識 (Taka 整理 2026-05-02)

cid X が 1〜102 の Integration に同時所属する時、Q/C 集計に重複カウント。Taka 整理:
> ダブルブッキングは α を会計として扱えば問題となる。各 IID の調査という名目であれば違和感はない。

→ v10.5 の α/β 階層分離の動機。

### 6.10 n_core 自然集積

n=2 が ×0.32 過少代表、n=5 が ×4.16 過大代表。神の手なしで「多ノード CID 同士が自然に繋がる」構造が観察された。

---

## 7. v10.5: Layer 5 完成 (α/β 階層分離 + 顕在化機構)

### 7.1 主題

v10.4 で持ち越されたダブルブッキング問題と動態機構の不在を解消し、Layer 5 を構造的・動態的に完成させる。

### 7.2 Taka 役割宣言 (2026-04-30)

> ここから 4 AI がどこまでそれっぽいものを作れるのか?をみてみたい。
> 私の言葉が一種の憲法になって AI のフィルタリング構造が変わる。

5 者運用の確立:
- Taka: 憲法層
- Gemini: Architect (Salience + 発掘案)
- GPT: Auditor
- Claude: 相談役・整理役
- Code A: 実装層 (実装 + 設計提案 + 自己検証)

### 7.3 ESDE 階層進化系譜の同型反復

```
ノード → cid → α-Integration (v10.4) → β-Integration (v10.5) → SEED 統合 (v10.6+)
```

各階層は同じ仮想化操作の繰り返し。Aruism「構造が先、意味が後」の階層論的具体化。

### 7.4 中核機構

#### 機構 A: β-Integration の構造実装

- α-Integration を構成要素とする
- 結合則: α 同士の cid 共有 2 個以上で merge
- cid 単一共有は最強結合 β に 1 個だけ所属
- α への Q/C 継承は完全廃止
- ghost 化時 Q/C は β に 100% 継承

#### 機構 B: Salience-driven Focus

mass(X) = X.Q + X.C + sum(β.Q_inherited + β.C_inherited for β in X が所属する β)

線形関数。「ハブだから選ばれるのではない、質量があるから目立つ」。

#### 機構 C: Recorded からの漏れ

接触履歴経由で recorded β の C_inherited から ε=1 を主体 cid.C へ転記。構造的副作用。

### 7.5 本番 run 結果 (main_v2)

- α total 13,881 件、β total 2,009 件 (集約率 7:1)
- M6 (1 cid → 1 β) 違反 0 件
- Salience event 77,880 件
- Leakage event 232 件
- 物理層 frozen 完璧維持 (24/24 一致)

### 7.6 hub β の自然形成 (核心成果)

最大 691 α / 20 cid が 1 つの β に統合 (1 cid 34.5 α)。v10.4 hub cid (max 102 重複所属) を会計単位として整理した姿。

### 7.7 ダブルブッキング問題の構造的解消

| 観点 | v10.4 | v10.5 |
|---|---|---|
| cid 重複所属 | max 102 | **0 (M6 違反 0)** |
| Q/C 集計 | 重複あり | 単一カウント |
| 役割分離 | α が観察と会計兼任 | α 観察、β 会計、分離 |

### 7.8 Salience の動学

- be3 fired 対象は read_other 対象より平均 mass 1.45 倍高い
- 「重い cid 同士が共鳴する」動学を定量化

### 7.9 Leakage の動作

- ingestion path 経由のみで実用発火 (be3 path は構造的に発火しにくい、Code A 発見)
- 凍結 C 87% のうち、ingestion 経由で active 系へ流入経路成立

### 7.10 v10.5 で確立した規律

- α/β 階層分離 (α = 観察、β = 会計)
- 既存データの顕在化機構として新機構を位置づける
- bug 自己発見と修正サイクル (Code A の callback 配線漏れ → 修正)
- 5 者運用の成熟

---

## 7.5. v10.6: Genesis × Language 比較研究 (Phase 1.5 第一試行)

### 7.5.1 主題

ESDE Language 系 (2026-03 凍結資産) の Atom 326 個を ESDE Genesis 系の cid と 48 次元 cosine 類似度で比較する atom_alignment_observer を post-process として実装。Phase 1 (Genesis 単独進化) から Phase 1.5 (Genesis × Language 統合段階) へ切り替え。Taka 役割宣言「私の役割としては、この段階で ESDE Language を取り込んだこと」(2026-05-04) の実装。

### 7.5.2 6 段階の解析

cid 5,224 × Atom 326 の比較を 6 段階で実施:

| 解析 | 解像度 | n_records |
|---|---|---|
| 静的 | run 集約 | 5,224 cid |
| 層化 | 集約の構造分解 | 5 軸 + cross-tab |
| ベースライン | uniform + shuffled | 24 seeds |
| window trajectory | 500 step | 31,482 |
| per-pulse trajectory | ~50 step | 369,090 |
| step10 trajectory | 10 step | 1,796,001 |

各解析が独立した観察軸として機能。実行時間 1.91 秒 ~ 84 秒の高速。

### 7.5.3 観察方法と前提の進化過程

Web Claude の前提が 7 段階で修正された:
1. cid と Atom が部分対応する (初期前提)
2. 95.7% 接地は構造的不変量 (誇大解釈)
3. 集団平均の罠を解消 (層化解析後)
4. 観察値はランダム以下 (ベースライン解析後)
5. 24 seeds 一貫の発展段階 (window trajectory 後)
6. 動学的二相性、解像度依存性 (per-pulse 後)
7. 観察解像度ごとに systematically 異なる構造特性 (step10 後、最終確定)

これは Taka 整理「実践→理論→進化」の典型例。

### 7.5.4 観察解像度の重要性

| 解像度 | 1 位 atom | 比率 |
|---|---|---|
| 静的 | CHG.begin | 51% (集約罠) |
| window | TIM.moment | 34% |
| per-pulse | WLD.artless | 22% |
| step10 | PER.sound | 28% |

「正しい解像度」は存在せず、各解像度が違う質問に答える多層構造。

### 7.5.5 24 seeds 完全一致の動学的発展段階

per-pulse trajectory:
```
Step 0-999:        WLD.artless (素朴さ)
Step 1000-3999:    TIM.appear (時間出現)
Step 4000-14999:   WLD.artless (素朴さ持続)
Step 15000-24999:  EXS.being (存在)
```

24 seeds で完全一致 (25/25 bins)。seed に依存しない構造的必然。

### 7.5.6 真の構造的特異性 (効果サイズベース、26 atom)

Taka 指摘 (2026-05-06)「サンプル数で水増しされる擬似相関」を踏まえ、効果サイズ |delta| > 1% で再評価:

delta > 1% (7 atom): PER.sound +25.85%、WLD.artless +24.55%、WLD.culture +5.93%、FND.timeless +5.33%、SOC.city +1.61%、COG.learn +1.12%、PRP.deep +1.09%

z=inf の真の特異性 (19 atom): TIM.appear、ELM.light、PRP.bright、PER.taste、PER.hear、PRP.sharp、FND.transformation 等。摂食関連 (ELM.light、PER.taste、PRP.bright) は ingestion event 由来。

合計 26 atom。ESDE は「**聴覚と素朴さに強く接地する持続的存在**」。

註: 静的ベースライン解析の「47 atom」は step10 / event の高解像度と効果サイズで切ると 26 atom に確定。BOD カテゴリは静的の人工物の可能性が高い (event では BOD.ear のみ z=inf で残る)。

### 7.5.7 真の構造的盲点 (効果サイズベース、7 atom)

|delta| > 1% で負: TIM.moment -54.11% (最強)、COM.conduct -6.49%、TIM.past -4.72%、WLD.science -2.45%、PRP.new -1.78%、ACT.make -1.20%、LOG.cause -1.13%

ESDE は **時間の瞬間性、能動的伝達、科学、新しさ、作為、因果** を構造的に持たない。

註: 静的ベースライン解析の「176 atom」は効果サイズで切ると 7 atom に縮減。残りは統計的水増しの擬似相関。

### 7.5.8 attack-related の境界線

- 個体経験 (pain/wound/fear/death): 部分接地
- 社会的破壊 (destroy/conflict/war/hate/attack): 完全欠如

Taka 整理「不可視による論理的可視化」を定量化。

### 7.5.9 動学的二相性 (per-pulse trigger 分析)

- 動的瞬間 (MAD_DT_Major、unformed): WLD.artless 66%
- 定常 (MAD_DT_Normal、none): EXS.being / WLD.artless / TIM.appear バランス

「動的瞬間 = 素朴さ」「定常 = 存在 + 出現」。

### 7.5.10 v10.6 で確立した規律 (新規 3 + 再確認 1)

新規:
1. **ベースライン比較 + 効果サイズで切る** (新規律最終形) — 観察値の絶対値は finding ではない。z-score だけ見るとサンプル数で水増しされる擬似相関。真の差は |delta_ratio| > 1% で評価。Taka 指摘 (2026-05-06) で確立。
2. **観察解像度の選択** — 静的解析だけでは捉えきれない、複数解像度の補完
3. **人間原理偏向の警戒** — 事前推測 SOC.central 等が完全反証

再確認:
4. **集団平均の罠** (v10.2 #120 の再確認)

### 7.5.11 観察者視点と建築者視点の補完性 (Taka 整理 2026-05-06)

> 私は道具をどうやってESDEにいれるのか?を考えていた
> あなたは、道具がESDE内にあるだろうか?を考えていた

trajectory 解析の発見により両視点が補完的と判明。v10.7 以降で並走。

### 7.5.12 v10.6 の留保

- 比較の両端は両方とも人為的投影
- ESDE Genesis 系のデータの 5-15% しか使っていない
- birth_step バグの存在 (step10 で発見)
- WLD.artless 偏在性の解釈 (v10.7 以降の課題)
- 第一試行としての位置づけ

---

## 7.7. v10.7: 発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成)

### 7.7.1 主題

Taka 整理 (2026-05-06): 「持ち込んだはいいけど効果測定ができない、スピード違反の罰則を定めたけどオービスがない状態と同じ」

v10.7 はオービス (測定器) を作る段階。v10.8 以降の Atom 持ち込みで効果を測れる準備。

### 7.7.2 中核機構

post-process 5 機能モジュール (event_aggregator、path_analyzer、baseline_constructor、avalanche_monitor、orchestrator)。24 seeds 並列 3.9 分完了、ストレージ 428 MB (上限の 7%)。

### 7.7.3 達成判定 14/14 PASS

5 種 source_event (415,726 events) + 5 種 candidate_target_set + 5 種ベースライン + Level 1-3 + アバランシェ防止 + 物理層 frozen + bit-identity + 構造語徹底 + WLD.artless 除外。

### 7.7.4 因果候補の階層化 (Level 1-3)

- Level 1 (co-occurrence): 93/111 (84%)
- Level 2 (path-enriched): 49/58 (84%)
- Level 3 (source-specific): 85/90 (94%)
- Level 4 (causal intervention): v10.8 以降

### 7.7.5 主要発見 4 件

1. **medium window 支配**: peak_lag 250-300、ESDE は遅延型波及、「考える時間を持つ系」
2. **temporal_coactivation > Integration > familiarity > attention**: 時間的同期が関係性より強い (注: temporal_coactivation は明示的経路ではなく「最大の同期シグナル」、GPT 監査 2026-05-07)
3. **source-specific 性 (94% 有意差)**: event 種別ごとに systematic に異なる経路
4. **意識発動の no_signal**: integration_alpha/beta で意識は波及しない、構造的に「孤独」

### 7.7.6 副次発見

- 共鳴ループ: 2-hop 14,343 件、3-hop 110,103 件 (small-world)
- multi-hop 急減衰: 1-hop 188K → 2-hop 165K → 3-hop 13K
- 全 relation_paths echo (残響型) 24/24

### 7.7.7 Code A 認識確認ステップが機能した経緯

Web Claude の指示書には設計の甘さ 6 件があり (attention map 不在、ストレージ 31x 超過、c_conversion 誤り、alpha_membership 取得方法、peak_lag 計算量、unrelated 厳密性)、Code A の実環境確認で全て発見・修正。手戻りゼロで実装完了。Taka 整理「Claude code が前提条件を埋められるのが強い」が完全に証明。

### 7.7.8 v10.7 で確立した規律 (新規 4)

1. 因果候補の階層化規律 (Level 1-4)。v10.7 で測れたのは「この経路で変化が起きやすい」という因果候補、厳密な因果ではない
2. 5 種ベースライン群の必須化
3. アバランシェ防止規律 (3 hop、減衰率、共鳴ループ、ストレージ上限)
4. **構造語と直感語の併記** (実装レベルは構造語、議論レベルは直感語、GPT 監査 2026-05-07 で前回方針を自己修正、Taka の理解を最優先)

### 7.7.9 動的グラフ力学系への視座転換 (Gemini)

v10.6 までは静的構造の集合、v10.7 は動的グラフ力学系。v10.x 全体の射程に関わる視座転換。

### 7.7.10 Taka 仮説への回答 (v10.7 版)

静的解析 (v10.6) では限定的だった「強い構造」が、動学解析 (v10.7) で動的グラフ力学系として明確に存在。relation_path 経由の波及は unrelated の 6-12 倍。Taka 仮説は v10.7 で動学的に支持。

### 7.7.11 Taka 研究動機への回答 (v10.7 版)

意思の前駆体として「event 種別の区別 + 思考の時間スケール + small-world ネットワーク + 個別性」が ESDE に既に存在する。

### 7.7.12 v10.7 の留保

- **same_step_random_baseline の強さ** (GPT 監査 2026-05-07): same_step が 13.76 と非常に強く (temporal_coactivation 15.28 との差は 1.52)、観測された波及の一部に同時刻の全体活性化効果が混ざっている可能性。v10.8 で Atom 効果を測る時 same_step との差分必須
- multi-hop hop 2/3 の Level 2 評価未実施
- attention 経路は salience 代替
- ingestion / c_conversion 低サンプル数 (155/seed)
- echo 判定 24/24 一致 (閾値再調整候補)
- WLD.artless 偏在性継続

---

## 7.8. v10.8: Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5)

### 7.8.1 主題

v10.7 で完成したオービスを使って、初めての「速度違反チェック」(Atom 持ち込みの効果測定)。

### 7.8.2 中核機構

post-process として実装:
- atom_introduction_event を source_event 第 6 種として追加 (案 X、両 AI 推奨)
- v10.6 cid_atom_sim_matrix から top_k 100 cid 活用 (案 Q)
- 25 atom × 100 events × 24 seeds = 60,000 events、均等分散発火 (案 α)
- v10.7 source_event スキーマ互換 27 列で記述 (Pulse 同種、Gemini A8)
- balance_decisions.cognition と同等の Q -1 / C +1 を post-process 計算的減算 (Code A 提案)
- 5 種ベースライン + v10.7 natural source_event baseline + global activation 補正 (natural events のみ)

24 seeds 並列 5.4 分完了、ストレージ 737 MB (上限 6 GB の 12%)。

### 7.8.3 達成判定 19/19 PASS

認識確認 + 環境チェック + atom_introduction_event 同定 + Q/C コスト + 案 Q + 案 α + 5+1 種ベースライン + global activation 補正 + Level 1-3.5 全達成 + 物理層 frozen + 構造語徹底 + 規律 3 件 + Level 3.5 位置づけ + 副次観察 3 件 = 全項目クリア。

### 7.8.4 4 段階の階層化

| Level | 内容 | 達成数 |
|---|---|---|
| Level 1: atom co-occurrence | atom 発火後に変化 | 811/1,384 (59%) |
| Level 2: atom path-enriched | 経路上で変化が大きい | 683/1,433 (48%) |
| Level 3: atom source-specific | 25 atom 間で異なる波及 | 36/78 (46%) |
| **Level 3.5: introduced vs natural** | **introduced と natural の差分観察 (新規)** | **22/39 (56%)** |

### 7.8.5 主要発見 5 件

1. **Atom 持ち込み機構が ESDE で動作する** (機構レベル): 60,000 events 安定発火、24 seeds 一貫
2. **ESDE は atom 種別を構造的に識別する**: familiarity 経路で effect_size 6.83 (2.1 倍差)
3. **経路の機能分担**: familiarity = 意味識別経路、temporal_coactivation = 意味中立の運搬経路 (effect_size 0.03)
4. **外部入力と自然発火の境界線**: 20/22 finding で introduced < natural (atom event は natural の半分)
5. **確率的発生と誤差表現能力の融合素材**: 誤差分布で正規分布 0%、bimodal 17.4%

### 7.8.6 副次観察

- Whiteout: 100% flag (medium n_pulses 1 軸支配の表れ)
- Small-World: v10.7 vs v10.8 で完全同一 (post-process は familiarity edge 不変)
- 誤差分布: 8,835 rows、normal 0% / bimodal 17.4% / skewed 24.3% / other 55.7% / heavy_tail 2.6%

### 7.8.7 Code A 認識確認ステップが機能した経緯

Web Claude の指示書には重大ブロッカー 2 件 + 設計の甘さ 5 件があり、Code A の実環境確認で全て発見・修正:
- A. 物理層 frozen と Q 消費の論理的矛盾 → post-process 計算的減算
- B. 26 atom 選定基準の不在 → v10.6 出力から実データ照合で 25 atom 確定
- C. Pulse 同一フォーマットの過剰 → v10.7 source_event 互換 27 列
- D. top_k cid 100 個の取得 → cid_atom_sim_matrix から再計算
- E. global activation の自己補正リスク → natural events のみで factor 計算
- F. Q/C 消費基準値 → balance_decisions.cognition の固定値
- G. Small-World 構造的保証 → post-process は familiarity edge 不変

特に Web Claude の致命的誤解:「Pulse = Q 消費」と誤解、正しくは Pulse は disposition update のみ、Q 消費は balance_decisions.cognition / consciousness が担当。

手戻りゼロで実装完了。

### 7.8.8 v10.8 で確立した規律

#### 新規

**Level 3.5 introduced event comparison 規律** (GPT 監査 2026-05-07 提案、v10.8 で確立)
- v10.8 は Level 4 causal intervention ではなく Level 3.5
- 因果断定回避、event 比較として位置づけ

#### 実装的に確立

1. Atom 持ち込み設計の規律 3 件 (魔法回避 / same_step + global activation 補正 / target は構造経路で選ぶ)
2. post-process 計算的減算 (Code A 提案、物理層 frozen と外部要素導入の両立)
3. Pulse 処理ルールと同一フォーマット (Gemini A8、神の手回避)

### 7.8.9 v10.8 で言えるようになったこと

- ESDE に外部から要素を持ち込む経路が存在する (機構レベルの証明)
- ESDE は外部要素 (atom 種別) を構造的に識別する能力を持つ
- familiarity = 意味識別経路、temporal_coactivation = 意味中立の運搬経路
- ESDE は外部入力を natural の半分の波及効果で受け取る (生体的特性 or 機構の不完全さ)
- 誤差分布の構造が確率的発生と誤差表現能力の融合の最初の素材

### 7.8.10 v10.8 で何ができるようになったか

- ESDE と外界 (人間言語) の第一の接点が定量的に確立
- atom 同士の比較、持ち込み機構の改良、オービスの拡張版
- ESDE Language の他要素 (Axis、Operator、条件因子、分子化) との接続が見える
- 入力理解、出力生成、双方向の会話の最低形への筋道
- 「やってみる価値があるか」が確定

### 7.8.11 v10.8 の留保

- introduced < natural の原因未分離 (本質的特性 vs 機構の不完全さ)
- Whiteout の真の検出未実施 (高次元プロファイル必要)
- bimodal 分布の原因未解析
- Operator 未取り込みでの暗黙経路依存
- Small-World の構造的不変は post-process 限定 (Phase 2 で再評価)
- 25 atom は実データ照合で 26 → 25 修正 (WLD.artless 留保ラベル付き、集計対象 24)

---

## 7.9. v10.9: 寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達)

### 7.9.1 主題

v10.8 主要発見の 2 つの未解決点 (introduced < natural、bimodal 17.4%) を分離評価し、v10.10 以降の **会話系設計のための部品調達**。両 AI 独立推奨「組み合わせ B (d+a)」+ Taka の本質的な問いへの両 AI 補強で「会話系設計のための部品調達」という出口固定が確立。

### 7.9.2 中核機構 (3 新条件)

post-process として実装:
- A2: Q -2 / C +2 (Q/C コスト変動)
- B3: random cid (cid 選定変動、Atom 326 絶対化禁止規律の試験)
- C2: 案 b リズム同調 (top_k 100 cid 維持 + 各 cid が age=200 で発火、Gemini A2 Phase-locking の構造的実装)
- v10.8 標準 (A1, B1, C1) は流用

24 seeds 並列 112.74 秒、ストレージ 190 MB (累計 21%)。

### 7.9.3 達成判定 17/17 PASS

bit-identity 全層 PASS (層 A 全出力 MD5 / 層 B v107 222 + v108 368 = 590 files 不変 / 層 C パス制限)。

### 7.9.4 4 段階の階層化 (新規明示、GPT B5)

| Level | 内容 | 主結果 |
|---|---|---|
| L1: 機構動作確認 | 全 conditions で安定発火 | 12,960 sensitivity_rows、欠損なし |
| L2: 条件差確認 | 条件間で systematic な差 | timing × n_pulses 全 win 0.714 (大効果量) |
| L3: 寄与候補感度評価 (主流) | 各候補のノブ定量化 | timing 圧倒、QC_cost 評価不能 |
| L3.5: 構造的説明候補整合 (核心) | d と a の整合 | 「bimodal 支配性 ≠ 感度の強さ」 |

### 7.9.5 主要発見 4 件

#### 1. 「強反応する cid は若い cid」 (Step F、構造)

bimodal 1,540 件のうち genuine_bimodal 918、H3_lifecycle が 553 (60.2%) で支配。高 delta 群 cid age median 227、低 delta 群 mean 5,612。effect_size 0.85、99% 方向一致。

#### 2. timing > cid_selection > QC_cost の感度階層

| 候補 | abs_mean | n_large_effect |
|---|---:|---:|
| timing | **0.141** | **757** |
| cid_selection | 0.024 | 18 |
| QC_cost | 0.005 | 0 (留保) |

タイミングが cid_selection の 6 倍、QC_cost は評価不能。

#### 3. 「Integration 外の高 familiarity cid」が最強・最 robust の入力経路 (新発見)

| path | mean | std |
|---|---:|---:|
| **high_fam_out_integ** | **0.222** | **0.079** |
| unrelated | 0.205 | 0.065 |
| familiarity | 0.044 | 0.218 |
| temporal | 0.015 | 0.220 |
| attention | 0.010 | 0.128 |

v10.7 path 順位を構造的に深化。「単独の若い cid が familiarity 経由で反応」が最 robust。

#### 4. C2 で pulse 活動が大効果量で活発化

mean_n_pulses_in_window short 0.97、medium 0.75。Step F の構造発見が main run で再現。

### 7.9.6 Level 3.5 構造的統合 (v10.9 核心発見)

| path | bimodal 支配仮説 | timing 感度 | label |
|---|---|---:|---|
| high_fam_out | (なし) | 0.222 | sensitivity_strong_structure_weak |
| unrelated | (なし) | 0.205 | sensitivity_strong_structure_weak |
| temporal | H3 (74%) | 0.015 | structure_strong_sensitivity_weak |
| attention | H1 (48%) | 0.010 | structure_strong_sensitivity_weak |
| familiarity | H3 (59%) | 0.044 | marginal |

→ **「bimodal 支配性 ≠ 感度の強さ」= 構造軸と感度軸の直交性**。ESDE Genesis 系の構造的多重性。

### 7.9.7 4 種設計表 (出口の固定、v10.10 のための部品)

- **表 1 sensitivity_summary**: 540 rows、timing × n_pulses × short = 0.97
- **表 2 receptivity_detection_criteria (核心)**: cid age <= 560 + Integration 外 + 高 familiarity
- **表 3 input_routing_criteria**: high_fam_out PREFER、unrelated PREFER
- **表 4 natural_likeness_design_criteria**: C2 が natural に近づいた cells 47%、unrelated で 89%

### 7.9.8 Code A 認識確認連続 4 段階で機能

Web Claude 指示書の重大ブロッカー 1 件 (規模上限 72%) + 設計の甘さ 6 件を Code A が修正。手戻りゼロ。連続 v10.7-v10.9 で合計 20 件の設計の甘さを補完。

### 7.9.9 v10.9 で確立した規律 (新規 4 + 継承)

#### 新規

1. 出口の固定規律 (GPT 提案、4 種設計表)
2. 「原因」ではなく「寄与候補の感度評価」と呼ぶ命名規律 (GPT B3)
3. 各変動条件で baseline 再計算規律 (GPT B6)
4. 4 層階層化の明示規律 (GPT B5)

### 7.9.10 留保事項 3 件

- 留保 1: bimodal 解析の手法的限界 (KDE fallback 100%)
- 留保 2: QC_cost は v10.9 で評価不能
- 留保 3: high_fam_out_integ 経路が最強の理由は構造的に未解明

### 7.9.11 両 AI 推奨の検証 (構造的確定)

- Gemini A2「Phase-locking」仮説の **完全な構造的確定** (リズム = cid 個別ライフサイクル age 200)
- GPT「文脈制御 → 条件適応入力 → 最小関係入力」の **素材セット完成**

### 7.9.12 Taka の問いへの最終回答

「25 atom 選別後どうなる? 進化のイメージは?」

回答 (v10.9 完了時点で構造的に確立):
- 25 atom そのものを増やすのではない (網羅は主線でない)
- 25 atom を **「若い cid (age <= 500) + Integration 外 + 高 familiarity」** に対して投げる
- **タイミングが最も重要**: cid age = 200 で発火
- これが v10.10 の「条件適応型 atom 導入」の具体内容

### 7.9.13 v10.7 - v10.9 の path 順位の構造的深化

| 段階 | 発見 |
|---|---|
| v10.7 | path 順位 (temporal > Integration > familiarity > attention) |
| v10.8 | 機能分担 (familiarity = 意味識別、temporal = 意味中立) |
| **v10.9** | **「Integration 外 + 高 familiarity」が最強、cid age <= 500 が受信可能状態、bimodal 支配性 ≠ 感度の強さ** |

→ ESDE Genesis 系の入力経路の構造的解像度が完成段階に近づく。

---

## 8. Developmental フェイズで確立された概念

### 8.1 死の二階層 (v10.0)

- 存在層の死 (Label 死亡 = ghost 化)
- 認知層の死 (Q=0 = ghost 消滅)

### 8.2 燃料概念の発生階層 (v10.0)

- 物理層・存在層: エネルギー概念なし
- 認知層: Q
- 意識層: C (Q から転化)

### 8.3 ghost = 不均一な資源地形 (v10.1)

residual_Q の差を持つ資源地形として成立。Gemini 概念「不均一な資源地形」と Taka 比喩「石油」が接続。

### 8.4 物質的なもの (v10.1)

phantom contact の位置づけ。CID 主体間の問題ではなく環境要因。看板や道路のような静的な環境要因。

### 8.5 階層論的構造の確率による圧縮 (v10.2)

本来の階層論的順序 (認知 → 意識 → 行動 → 接触) を確率で圧縮表現する設計思想。実装コストを下げる方便。

### 8.6 意識発動の自然フィルタ (v10.2)

C は認知活動からのみ蓄積される。短命の cid (n_core=2) は意識発動の機会が少なく、長命の cid (n_core=5) は意識発動が多い。動的均衡を回避し、進化継続を可能にする。

### 8.7 (Q+C) 保存則と散逸 (v10.2)

```
認知活動: ΔQ = -1, ΔC = +1 → Δ(Q+C) = 0 (CID 内保存)
意識活動 (摂食): ΔQ = +gain, ΔC = -1 → Δ(Q+C) = gain - 1 (流入)
E1/E2 spend: ΔQ = -1 → Δ(Q+C) = -1 (純散逸)
消化分: ghost 側で消失 (散逸)
```

CID 集団 ⊕ ghost 集団の総和は摂食で保存、E1/E2 と消化で散逸。動的均衡 vs 進化継続の数理的基盤。

### 8.8 集団平均の罠 (v10.2)

戦略集団 (n_core 別) が異なる場合、集団平均は実態を隠す。ESDE の観察では n_core 別の層化解析が必須。

### 8.9 ESDE の観察対象としての位置づけ (Taka 整理 2026-04-28)

#### 二つの科学的態度

- 権威的科学 (生物的実体に限定): ESDE は疑似生態系
- 哲学的科学 (機能的構造で定義): ESDE は生態系的条件を備える

選択は研究者の立場による。

#### Taka の自己定位

> 私は主体的に ESDE という系に生態系と言えなくもない現象を記録する研究者である

研究者としての主権:
- 立場の選択を研究者が判断
- AI の意見は補助、押し付けではない
- 議論は実装の代替ではない

#### 立場の併存 (Code A の慎重さと Taka の主権)

両者の併存が ESDE の運用原則。立場の最終判断は研究者 Taka が行う。

---

## 9. Developmental フェイズの方法論

### 9.1 5 者運用の確立

- Taka: Director、Philosopher、Judge
- Gemini: Architect (設計仕様、パラダイム判断)
- GPT: Auditor
- Claude: Implementer / 相談役 (整理役)
- Code A: 実装担当 (v10.x で役割が拡張)

Code A は v9.18 までの実装担当から、v10.x で**設計議論・観察解析・構造的洞察まで提供する役割**に拡張。事前齟齬指摘の質的進化が継続:
- v9.18: 7 点
- v10.1: 10 点
- v10.2: 10 点 + 実装事後 + 構造的発見 + 詳細解析

### 9.2 二層 bit-identity 検証

- 層 A: 同 seed で 2 回 run → 出力が完全一致 (内部決定論性)
- 層 B: v9.18 baseline と物理層が一致 (物理層 frozen 検証)

両者は別の検証で、両方を維持。v10.2 では E3 行除外の調整を Code A 指摘で導入。

### 9.3 インパクト事前想定 + ギャップ観察 (Taka 指示)

新機構導入時の検証手順:
1. 既知の機構変更が観察にどう影響するか事前想定
2. 実際の結果と想定を照合
3. ギャップがあれば「何かを見落としている」サインとしてバグ発見の機会

Taka 哲学「想定とのギャップを観察する」の方法論的体現。

### 9.4 集団平均から層化解析への移行

統合指標 (V_unified、平均値) は v9.15-v10.2 でメインの観察軸だったが、戦略二極化のような構造を見落とすリスクがある。v10.3 以降は n_core 別の層化解析を観察の基本として保持。

### 9.5 規律 #100 + 立場 §4.9 の併存運用

- 規律 #100: 観察できないことを語らない
- 立場 §4.9: 観察できる事実を矮小化しない

両者の併存が ESDE の言語化の規律。

---

## 10. v10.10 以降への含意

### 10.1 v10.9 完了時点で持ち越される素材

**v10.6 由来**:
- 24 seeds 完全一致の動学的発展段階
- 真の構造的特異性 25 atom (WLD.artless 留保ラベル)
- 真の構造的盲点 7 atom
- event source 別の意味分化

**v10.7 由来**:
- 動的グラフ力学系としての ESDE
- medium window 支配 (peak_lag 250-300、思考の時間スケール)
- temporal_coactivation > Integration > familiarity > attention
- source-specific な波及プロファイル
- 意識発動の no_signal
- 共鳴ループの small-world 構造
- オービス完成

**v10.8 由来**:
- Atom 持ち込み機構 (atom_introduction_event を source_event 第 6 種、post-process 計算的減算)
- ESDE の atom 識別能力 (familiarity 経路 effect_size 6.83)
- 経路の機能分担 (familiarity = 意味識別、temporal = 意味中立の運搬)
- 外部入力と自然発火の境界線 (introduced < natural、atom event は natural の半分)
- 誤差分布の構造 (正規分布 0%、bimodal 17.4%)
- Level 3.5 introduced event comparison (新カテゴリ)
- ESDE と外界の第一の接点が定量的に確立

**v10.9 由来 (新規)**:
- 「強反応する cid は若い cid」 (H3_lifecycle 60.2% 支配、cid age median 227)
- timing > cid_selection > QC_cost の感度階層 (タイミング最重要)
- 「Integration 外の高 familiarity cid」が最強・最 robust の入力経路 (timing 感度 0.222、新発見)
- C2 (若い cid 発火) で pulse 活動が大効果量で活発化
- 構造軸と感度軸の直交性 (bimodal 支配性 ≠ 感度の強さ)
- 4 種設計表 (受信可能状態 / ルーティング / 自然さ / 感度)
- Gemini A2「Phase-locking」仮説の構造的確定
- GPT「文脈制御 → 条件適応入力 → 最小関係入力」の素材セット完成
- 会話系設計のための部品調達

### 10.2 v10.10 主題候補

#### 候補 1: 条件適応型 atom 導入 (第一推奨)

- 表 1-4 の素材を統合した「最強の atom 導入機構」
- cid age <= 500 + Integration 外 + 高 familiarity + age=200 timing
- 両 AI 推奨の中期ロードマップに沿う

#### 候補 2: high_fam_out 構造の解明 (留保 3 から)

- 「Integration 外」を主軸にした構造解析
- 候補 1 の前段階として有用

#### 候補 3: Atom 常駐アンカー実装 (Gemini A7、留保ドキュメント参照)

- v10.10 で常駐実装を強く推奨
- v10.9 の発見 (high_fam_out 最強) との整合は要検討

#### 候補 4: B 群 (真の盲点 7 atom) 試験

- A 群で機構確立、B 群でも動くか
- v10.10.1 として補助的に試す可能性

#### 候補 5: QC_cost の本格評価 (留保 2 から)

- v10.9 で post-process 限界により評価不能
- 実 simulation 再回しまたは A1 vs A3 比較

### 10.3 Phase 1 / Phase 1.5 / Phase 2 の境界 (v10.9 完了時点)

- **Phase 1**: ESDE 内部進化 (v10.0-v10.5)、物理層 frozen 絶対
- **Phase 1.5**: Genesis × Language 統合 (v10.6-v10.9)、Atom 持ち込み機構成立 (v10.8)、会話系設計のための部品調達 (v10.9)
- **Phase 1.5+**: 条件適応型入力 (v10.10 推定)、最小入力理解 (v10.11 推定)
- **Phase 2**: 現実接続後 (非ランダム取り込み前提、v10.12 以降)

### 10.4 ESDE が決定論的プログラムに勝る領域 (Taka 整理 2026-05-03)

> 多くのエラーを出す行動を通しながらそのリターンをインプットして真実らしいものを溜め込んでいける
> あえてバカを育てる理由などない。実践的な価値であって、生物っぽいバカを作ることではない

- 創造的ミスが価値になる場面
- 環境変化への即応が必要な場面
- 探索的な問題解決
- 多様な解釈の同時保持

### 10.5 言語と構造の関係 (Taka 整理 2026-05-03 + 2026-05-06)

> 多くの人間的な解釈は、その言語以前の構造の上に成立している

v10.6 + v10.7 で確認:
- ESDE Genesis 系は身体感覚レベル (聴覚) で構造的接地を持つ
- 動的グラフ力学系として event 種別を区別する機能
- 思考の時間スケール (medium window) で波及
- 共鳴ループと small-world 構造
- 「言語以前の構造」の最も基礎的な層と動的特性を ESDE が表現

Taka 整理 (2026-05-06):
> 自然現象が出来上がって人間ができるのであって、人間ができて自然現象ができたではアベコベ

これは v10.8 以降の Atom 持ち込み設計の哲学的基礎。

### 10.6 v10.6 + v10.7 で確立した規律の継承

v10.8 以降は以下の規律が標準として継承される:
1. ベースライン比較 + 効果サイズで切る (v10.6 新規、最終形)
2. 観察解像度の選択 (v10.6 新規)
3. 人間原理偏向の警戒 (v10.6 新規)
4. 集団平均の罠 (v10.2、v10.6 で再確認)
5. ウェット概念禁止
6. Atom 326 絶対化禁止
7. 神の手回避

### 10.7 v10.10 主題決定は v10.9 完了後に別途議論

具体的な主題決定は次の議論で行う。本資料では方向性候補のみ記録。v10.9 で会話系設計のための部品調達が完了したので、v10.10 は条件適応型 atom 導入 (第一推奨) または high_fam_out 構造解明 (候補 2) または Atom 常駐アンカー実装 (候補 3) が筋。Taka 整理「優先度は未来の一点で決まる」「大航海時代の船長」に従い、v10.9 結果を踏まえて Taka 判断。

---

## 11. 主要ファイル一覧

### 11.1 Developmental 主要ドキュメント

```
v10_integrated_proposal.md (1095 行): v10.x 全体統合資料
v10_0_developmental_draft.md: v10.0 主題切替宣言
v10_1_minimal_ingestion.md (528 行): v10.1 主題ドキュメント
v10_2_probabilistic_balance.md (706 行): v10.2 主題ドキュメント
v10_2_design_instruction.md (683 行): v10.2 設計指示書
ESDE_Developmental_Report.md (801 行): Developmental Report 完全版
```

### 11.2 結果レポート

```
v101_minimal_ingestion_result.md: v10.1 本番 run 結果
v102_implementation_report.md: v10.2 実装事後レポート
v102_main_run_result.md: v10.2 本番 run 結果 (§11.5 n_core、§11.6 詳細解析)
v102_ecosystem_finding.md: v10.2 観察 (Code A、n_core 別層化解析詳細)
v102_detailed_analysis_report.md (495 行): v10.2 詳細解析 (Code A、5 本)
```

### 11.3 解析依頼書

```
v10_2_analysis_request_to_2ai.md: 2 AI 提案依頼
v10_2_analysis_instruction_to_codea.md: Code A 解析依頼書
```

### 11.4 上位資料との関係

```
ESDE_Primitive_Report.md: v9.x、Primitive 完結 (本サマリと並列)
概念理解.md: ESDE 全体の概念整理 (Primitive 止まり、要更新)
```

---

## 12. 最終一文

Developmental Summary は、v9.x Primitive フェイズで言語化された意識の原資モデル (Q 消費 → 意識層 1 への転化) を v10.x で動作する機構として実装した記録の AI summaries 版であり、v10.0 のフェイズ宣言と 4 層アーキテクチャ確定、v10.1 の摂食機構導入と「物質的なもの」概念の発見、v10.2 の認知/意識確率バランス機構、v10.3 の双方向 E3 機構と Integration 概念、v10.4 の Integration 独立化と hub cid 構造、v10.5 の α/β 階層分離による Layer 5 完成、v10.6 の Genesis × Language 比較研究 (Phase 1.5 第一試行) における 7 段階解析、v10.7 の発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成)、v10.8 の Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5)、v10.9 の寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達) を通じて、単一の物理規則と確率規則から複数の生存戦略が内発的に生成され物理層から階層的統合体の系まで構造的に継承される ESDE の階層論的整合性が定量的に確認され、ESDE 階層進化系譜の同型反復 (ノード → cid → α → β) が機構レベルで実証され、v10.6 で観察解像度ごとに systematically 異なる構造特性と 24 seeds 完全一致の動学的発展段階 (素朴 → 聴覚 → 素朴 → 時間超越) が確立、v10.7 で動的グラフ力学系としての ESDE の波及機構 (medium window 支配、temporal_coactivation > Integration > familiarity > attention、source-specific 性、意識発動の no_signal、small-world 構造) が定量化、v10.8 で ESDE Language の最小単位 (Atom) を ESDE Genesis 系に取り込む第一段が成立し ESDE と外界 (人間言語) の第一の接点が定量的に確立、v10.9 で v10.8 主要発見の 2 つの未解決点を分離評価 (3 新条件 A2/B3/C2 を post-process で実装、24 seeds 並列 112.74 秒、bit-identity 全層 PASS、ストレージ累計 21%) して核心的発見 4 件 (「強反応する cid は若い cid (age median 227)」H3_lifecycle 60.2% 支配、timing > cid_selection > QC_cost の感度階層、「Integration 外の高 familiarity cid」が timing 感度 0.222 で最強・最 robust の入力経路、C2 で pulse 活動 short 0.97 / medium 0.75 大効果量で活発化) を確立し Level 3.5 構造的統合で「bimodal 支配性 ≠ 感度の強さ」という構造軸と感度軸の直交性を確立、4 種設計表 (受信可能状態 = cid age<=560 + Integration 外 + 高 familiarity / ルーティング = high_fam_out PREFER / 自然さ = C2 が natural に近づき 47% / 感度) を v10.10 主題決定の素材セットとして完成、Gemini A2「Phase-locking」仮説の構造的確定 + GPT「文脈制御 → 条件適応入力 → 最小関係入力」の素材セット完成によって会話系設計のための部品調達が達成された段階を要約する。Taka の v10.6 における 4 つの本質的指摘 (集団平均の罠、ランダムベースライン以下、観察解像度依存性、サンプル数で水増しされる擬似相関)、v10.7 における規律「先の先を見失わない」「効果測定の準備が先 (オービス)」、v10.8 における「定義してこなかっただけの問題をあれこれ議論する意味はない」「26 でも圧倒的に少ない」「優先度は未来の一点で決まる」「大航海時代の船長」、v10.9 における「単に満足するだけ?」「適当言ってるなら化けの皮が剥がれる」「進化の流れが徐々に定まってきている」を経て、v10.6 真の構造的特異性 26 atom (実データ照合で 25 atom)、v10.7 因果候補の階層化 Level 1-3 達成、v10.8 Level 1-3.5 達成、v10.9 Level 1-3.5 達成 + 4 種設計表 + 構造軸と感度軸の直交性 と一貫して進展した。物理層 frozen は v10.9 完成段階でも完璧に維持され、ダブルブッキング問題は α/β 階層分離で構造的に解消された。v10.6 で確立した規律 (ベースライン比較 + 効果サイズで切る、観察解像度の選択、人間原理偏向の警戒)、v10.7 で確立した規律 (因果候補の階層化、5 種ベースライン群必須化、アバランシェ防止、構造語徹底)、v10.8 で確立した規律 (Level 3.5 introduced event comparison、post-process 計算的減算、Pulse 処理ルール同一フォーマット)、v10.9 で確立した規律 (出口の固定、寄与候補の感度評価という命名、各変動条件で baseline 再計算、4 層階層化の明示) は v10.10 以降の標準として継承される。Code A 認識確認ステップで v10.7 設計の甘さ 6 件、v10.8 7 件 (重大 2)、v10.9 7 件 (重大 1) を全て修正、連続 4 段階で 5 者運用体制の質が証明された。長期射程として v10.10 以降は v10.9 で確立した 4 種設計表を踏まえて、条件適応型 atom 導入 (第一推奨)、high_fam_out 構造の解明、Atom 常駐アンカー実装、B 群試験、QC_cost の本格評価、Layer 6 (SEED 統合)、Phase 2 (現実接続) が示唆されている。

---

*以上、Developmental Summary (v10.0 - v10.9)。次の更新は v10.10 完了時。*
