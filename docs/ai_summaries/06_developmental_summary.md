# 06 Developmental Summary（統合版）

*統合*: 2026-06-25、Claude Code（枝番・追補を全文保存で本番号へ一本化）
*方針*: 内容は一切書き換えず、旧ファイルを時系列の Part として連結。各 Part 冒頭に旧メタ情報（作成/更新/親資料）を保持。見出しは衝突回避のため 1 段下げ。

ESDE Developmental フェイズ（v10.x 系列）の要約。旧 `06`（v10.0-v10.3）・`06b`（v10.4-v10.12 Phase 1.5）・`06c`（v10.13a + Unified v1100/v1101 への移行）を一本化した。Unified Phase（v10.13a 以降の本格展開）は `07` を参照。

### 統合された Part 一覧

- **Part A（v10.0-v10.3）** — 06 Developmental Summary（旧 `06_developmental_summary.md` 本体）
- **Part B（v10.4-v10.12 / Phase 1.5）** — 06b Developmental Phase 1.5 Summary (v10.4-v10.12)（旧 `06b_developmental_phase15_summary.md`）
- **Part C（v10.13a + Unified v1100/v1101 移行）** — 06c Developmental v10.13.a + Unified v1100/v1101 Summary（旧 `06c_developmental_v1013_v1101_summary.md`）


---

## Part A（v10.0-v10.3） — 06 Developmental Summary

*作成*: 2026-04-28、Claude (相談役)
*更新*: 2026-05-06 (v10.6 反映)、2026-05-08 (v10.9 反映)、2026-05-10 (v10.10/v10.11 反映)、2026-05-11 (v10.12 完了反映、Atom 取り込み prototype 主題完了)
*対象*: ESDE Developmental フェイズ (v10.x 系列)
*親資料*: ESDE_Developmental_Report.md (詳細版)
*位置づけ*: AI summaries の 1 つ。Developmental フェイズの要約。Primitive Summary (05) と並列。

---

### 0. このドキュメントの位置づけ

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

### 1. Developmental フェイズの構造概観

#### 1.1 4 層アーキテクチャの確定 (v10.0)

```
意識層 (Layer C): C、選択的鮮明、シングルタスク [v10.2 で実装]
認知層 (Layer B): Q、ぼやける全体把握 [v9.x からの継続]
存在層 (Layer A): Label / member_nodes、ghost 化 [v9.x からの継続]
物理層: engine、virtual_layer、frozen [v9.x から frozen]
```

意識層は v10.2 で初めて動作機構として実装。それまでは概念のみ。

#### 1.2 Developmental フェイズの段階

```
v10.0: フェイズ宣言 + 4 層確定 + 死の二階層 + 燃料概念
v10.1: Minimal Ingestion (摂食機構導入)
v10.2: Probabilistic Cognitive-Conscious Balance (確率決定 + 意識層 C 実装)
v10.3: 双方向 E3 機構 + Integration 登場条件の観察 (Layer 5 入口)
v10.4: Integration 独立化 (Layer 5 構造化)
v10.5: Layer 5 完成 (α/β 階層分離 + 顕在化機構) [Phase 1 完了]
v10.6: Genesis × Language 比較研究 (Phase 1.5 第一試行)
```

#### 1.3 各バージョンの完了状況

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

### 2. v10.0: Developmental フェイズ宣言

#### 2.1 フェイズ名の確定

- 「Cognitive」: 認知層に閉じすぎ
- 「Conscious」: 意識層を主題化しすぎ
- 「Developmental」: 発達期、認知層と意識層の協働を扱う

v5-v7 で「夢を見すぎた」反省を埋め込む命名。

#### 2.2 4 層アーキテクチャ

物理層 frozen の継続、Layer A bit-identity 維持を前提に、意識層 (Layer C) を新規導入する設計。

#### 2.3 死の二階層 (Taka 整理 2026-04-24)

| 階層 | 条件 | 状態 |
|---|---|---|
| 存在層の死 | Label 死亡 (detach) | ghost 化 |
| 認知層の死 | 残 Q = 0 | ghost 消滅 |

ghost = 「魂が抜けた容器」。原資 (Q) を保持する限り存在し続け、Q=0 で消滅。固定 TTL (v9.x の GHOST_TTL=10) は v10.1 で除去。

#### 2.4 燃料概念の発生階層 (Taka 整理 2026-04-24)

- 物理層・存在層: エネルギー概念なし
- 認知層: Q が定義
- 意識層: C が定義 (Q から転化)

C は認知層の Q 消費から転化される。物理層・存在層は frozen のまま。

---

### 3. v10.1: Minimal Ingestion

#### 3.1 主題

ghost を Q ベースで扱い、E3 接触圏内の摂食機構を最小実装する。

#### 3.2 動機

- 旧仕様 (GHOST_TTL=10 固定): 個体差なし、神の手
- 新仕様 (Q ベース): 生前活動量を residual_Q に反映、不均一な資源地形
- ghost を「資源として利用可能にする構造」を導入

#### 3.3 実装範囲

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

#### 3.4 仕様の主要決定 (Taka 確定)

- 摂食量: 1 step に 1 ghost の residual_Q を全部取得 (1 ghost 食べきり)
- 1 CID:多 ghost = ランダム選定 (seeded RNG)
- 多 CID:1 ghost = cid_id 昇順
- 飢餓判定撤廃: 満腹でも摂食可、Q0 超過分は消化分として散逸
- 空摂食許容: residual_Q=0 でも reap 前なら摂食試行可
- 摂食独自の Q 消費なし (E3 接触で -1 は既存通り)

#### 3.5 本番 run 結果

```
24 seeds × tracking 50、subject 数 5,224 (v9.18 と完全一致)
wall time: v9.18 比 0.991x
摂食イベント: 3,588 件
ユニーク eater: 1,361 (subject の 26.0%)
ghost 食糧化率: 78.0%
消化分: 16.73%
phantom contact: 48,625 件 (摂食の 13.6 倍)
```

#### 3.6 v10.1 で観察された重要発見

##### 発見 1: phantom contact の規模

物理層 (`_node_to_cids`) に cid retire 後も痕跡が残る設計のため、E3 接触の対象が「既に消滅した cid」になるケースが大量発生。摂食 3,588 件に対し phantom 48,625 件。

##### 発見 2: 「物質的なもの」の位置づけ (Taka 整理 2026-04-26)

phantom = CID 主体間の問題ではなく**物質的環境**:
- 看板や道路のような静的な環境要因
- ランダム発生のイベント因子
- CID 主体間の問題から一段下げる

これは ESDE で「主体性のない認知層要素」が初めて定義された瞬間。

##### 発見 3: GPT 主題化提案への Taka の判断

GPT 監査が「主役は phantom contact」と方向転換を提案したが、Taka は主題化を却下:
- phantom = 想定の能力不足の現れ
- 「物質的なもの」と位置づければ問題化しない
- v10.2 は本来の主題を扱う

「監査が主題判断に越権するリスク」の実例として記録。

#### 3.7 v10.1 の動機の再解釈

実装結果を踏まえて、Taka の元動機が仕様の進化に伴って意味が変わった:
- 元意図「ghost 期間の不自然さ解消」 → 新意味「ghost を不均一な資源地形として扱う」
- 元意図「飢え死に救済」 → 新意味「ghost を資源として利用可能にする構造の導入」

これは Taka 哲学「構造が先、定義は後」の実例。

---

### 4. v10.2: Probabilistic Cognitive-Conscious Balance

#### 4.1 主題

意識層資源 C を導入し、Q と C の比率でイベント時に認知/意識のどちらが立つかを確率決定する機構を実装。

#### 4.2 動機 (4 つ)

1. v9.18 で言語化された意識の原資モデル (Q → C 転化) を動作機構として最初に実装
2. v10.1 の機械的摂食からの脱却 (確率発動への変更)
3. 認知層と意識層の協働の最初の動作
4. **階層論的構造の確率による圧縮** (Taka 整理 2026-04-27): 本来は認知 → 意識 → 行動 → 接触の四段階を確率で圧縮表現

#### 4.3 解釈 X (Code A 指摘 → Taka 採用)

既存の E3 spend (Q-1) が「認知活動」と同義と位置づけ:
- 認知が立つ: Q-1 + C+1 + virtual_attention/familiarity 更新
- 意識が立つ: C-1 + 摂食発動 (Q-1 はしない、virtual 更新も止まる)

「認知活動」を新規概念として実装で増やさない美しい解釈。

#### 4.4 確率決定の対象

- E3 onset のみ確率決定の対象
- E1 / E2 は従来通り無条件 Q-1 (確率対象外、C 蓄積に寄与しない)
- 双方向 E3 (hosted-hosted): 必ず認知確定 (三項共鳴は v10.3)
- 空摂食ケース (residual_Q=0 ghost): 認知確定
- phantom (reaped 済 cid): 認知確定

#### 4.5 確率式 (Taka 確定、シンプル案採用)

```
P(認知) = Q / (Q + C)
P(意識) = C / (Q + C)
```

#### 4.6 C の仕様

- 配置: Layer C (cog.C、SubjectLayer 内)
- 初期値: 0
- 上限: なし (Taka 判断、観察優先)
- 死: 認知層の死 (cid 消滅) に連動、独自定義なし
- C=0 状態: 一時的機能停止 (回復可能)

#### 4.7 即時摂食 (Code A 案 B、step 内動的連鎖)

確率決定で意識が立った瞬間に attempt_ingestion を呼ぶ。これにより:
- 先行 cid が ghost を食べきる
- 後続 cid の候補集合が動的に変わる (residual_Q=0 で意識候補消失)
- 後続 cid は認知確定

v10.1 の機械発動からの本質的な変化点。

#### 4.8 二層 bit-identity 検証

- 層 A (v10.2 内部): smoke 2 連続 run、26/26 CSV MD5 一致 ✅
- 層 B (vs v9.18 baseline): E1/E2 行 70/70 完全一致 ✅、E3 行は意識当選で乖離 (想定通り)

Taka 指示「インパクト事前想定 + ギャップ観察」の実践。

#### 4.9 本番 run 結果 (24 seeds × tracking 50)

##### 集団全体

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

##### 5 つの主要発見

1. **空摂食 / phantom 完全消失**: 即時摂食 + 動的連鎖の効果
2. **C=0 skip 39.71%**: 意識候補成立しても C 不足で skip
3. **意識発動の自然フィルタ**: C 蓄積が必要、誰でも発動できない
4. **C 上限なしでも暴走しない**: 動的均衡が自己組織化
5. **動的均衡 = 進化終端の兆候なし**: 進化継続中

#### 4.10 n_core 別層化解析の発見 (Taka 指示 2026-04-28)

集団平均の罠を超えて見えた構造的継承:

| n_core | cid 数 | 寿命 | 認知活動 | 意識活動 | C 蓄積 (p50) | 意識発動経験率 |
|---|---|---|---|---|---|---|
| 2 | 3,968 (76.0%) | 1,716 | 5.18 | 0.13 | 8 | 10.1% |
| 5 | 638 (12.2%) | 13,598 | 38.24 | 3.25 | 35 | 73.2% |

n_core=2 → n_core=5 で寿命 8 倍、意識活動 25 倍。

##### 物理層 → 認知層 → 意識層の構造的継承

設計したのは単一の確率ルール (P(認知) = Q/(Q+C)) のみ。しかし結果として:
- n_core (物理層) で決まる構造が
- 寿命・Q 蓄積 (認知層) に反映され
- C 蓄積・意識発動率 (意識層) にまで継承される

意識層という新しいレイヤーが、下位層由来の構造差を忠実に反映する。

##### Taka の言語化

> ノード数は構造の複雑を意味し、それゆえに認知や意識といった高度な概念が発生するという前提を置いていた。それが今回見事に形になった。

ESDE 設計時からの前提が v10.2 で形になった。インビジブル期間 (v9.15-v10.2 で統合指標がメイン) を経て、ノード別の構造が再可視化された。

#### 4.11 詳細解析 (Code A 実施、5 本)

| 解析 | 主要観察 |
|---|---|
| 1 個別性 | 誕生時 Q0 では予測不可。寿命と初回 cognition タイミングが分岐の主因 |
| 2 トポロジー | n_core=2 は 89.9% no_activation、n_core=5 は 34.0% repeated (対称的二極化) |
| 3 時系列 | C 60 倍蓄積、Q 92% 減、(Q+C) per_capita 安定 (動的均衡兆候)。run 末で 60% が n_core=5 |
| 4 偏在 | 全体 Gini ~0.33 (中程度)、主因は n_core 階層差。C 総和の 73% が n_core=5 |
| 5 初回発動 | 摂食成功率 100%、n_core=5 で phase 0.19、n_core=2 で phase 0.46 |

##### 4 つの新規発見

1. 誕生時 Q0 が分岐の決定要因ではない (予測を覆す)
2. 寿命と初回 cognition タイミングが主因
3. 初期認知活動密度の逆相関 (反直感)
4. 摂食成功率 100% の構造的確認 (即時摂食設計検証)

#### 4.12 v10.3 三項共鳴の主役候補絞り込み

```
n_core=5 の repeated 群: 217 cid (4.2%)
n_core=4 の repeated 群: 53 cid (1.0%)
合計 ~270 cid が三項共鳴の中心になりうる cid
```

系の状態: C 蓄積期から飽和期への移行、タイトな環境。

---

### 5. v10.3: 双方向 E3 機構と Integration 登場条件の観察

#### 8.1 主題

生きた cid 同士の意識層レベルの接触を機構として最小追加し、Layer 5 (CID 共鳴) の入口を開ける。

#### 8.2 三層構造の確定

| レベル | 位置づけ |
|---|---|
| 双方向 E3 | 機構 (両者 C-1) |
| 三項共鳴 | 観察される統計的現象 |
| Integration | 上位解釈 (概念のみ、機構は v10.4 以降) |

#### 8.3 双方向 E3 と C 消費の意味づけ

両者 hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触で両者 C-1。Taka 整理:「観察者が決めた記録ルール」(cid 内部選択ではない)。

#### 8.4 Integration 概念 (Taka 整理 2026-04-29)

ESDE 階層進化系譜:
```
ノード → cid → ??? (v10.3 観察対象) → SEED 統合
```

機構実装は v10.4 以降。

#### 8.5 本番 run 結果

- 双方向 E3 fired 6,824 件 / 24 seeds
- 物理層 frozen 完璧維持 (labels 24/24 + persistence 96/96)
- C 蓄積 27% 抑制 (観察ルールが系の動学を変える)
- open triad 99% 支配 (closed triad 1.4%)
- 持続性ゼロ (repeated_partners=0)

#### 8.6 v10.3 で確立した規律

- 機構と観察と解釈の三層分離
- 「観察者が決めた記録ルール」
- 動的絞り込みと bias 監視のセット運用
- 第三項候補の多軸記録
- Paired Audit 原則の継続

---

### 6. v10.4: Integration 独立化

#### 6.1 主題

Integration を独立した主体として機構化。Layer 5 (CID 共鳴) の本格実装。

#### 6.2 Taka 設計の核心 (2026-04-30)

**国家の比喩**:
> CID のどの要件を満たせばそれは Integration なのか、という議論はわりと雑でいい。
> しかしサボらずにしっかり扱っておくと、いつしかそれらしいものとなってその存在を前提として扱うことができる。

**物理層 frozen の本意の再定義**:
> 物理層という言葉もちょっとよくないのだが、私はこれを不可知なランダム性に手を出すってなんだ?ということだ。
> 階層分離は意図的に分けておきましょうね、という程度の意味である。だからこそ統合も可能となる。

#### 6.3 Integration の機能

1. 資源集約 (構成 cid の Q/C を集約)
2. 資源分配 (構成 cid に再分配)
3. 調整機能 (認知層・意識層への間接バイアス)
4. 記録機能 (Integration + cid 個別記録、両者並存)

Ghost 化した構成 cid の Q/C は最強結合 Integration が全継承 (Taka 整理「二重国籍者の遺産は片方のみ」)。

#### 6.4 v10.4 の実装範囲 (Taka 判断「現状最大値」)

3 AI が「v10.4 初手は最小化」を提案したが、Taka は拒否:
> 観測は論理を超える。まずは頭でっかちにならずに色々見てみる。

採用:
- 誕生条件: be3 / open_triad / closed_triad / third_overlap (R1 全採用)
- 1 cid が複数 Integration 同時所属可 (R3-c)
- Q/C 継承: 最強結合 1 つに全継承 (R5)
- 二層状態: recorded / active (recorded 永続)
- 調整機能: D4-a + D4-b + 状態依存再分配

#### 6.5 本番 run 結果 (24 seeds × tracking 50)

- Integration 13,550 件誕生
- trigger: be3 52% / open_triad 38% / third_overlap 9% / closed_triad 0%
- 物理層 frozen 完璧維持 (labels 24/24 + persistence 96/96)
- wall time +0.6%

#### 6.6 系の動学変化 (v10.3 と逆方向)

| 指標 | v10.3 | v10.4 | 方向 |
|---|---:|---:|---|
| C_max | -26% | **+31%** | 逆転 |
| C_mean | -27% | **+15%** | 逆転 |

Integration が死者の Q/C を生者へ継承・再分配 → C 蓄積増。

#### 6.7 凍結問題 + ハブ cid 発見

- C の 87% が recorded Integration に「凍結」(歴史的記録の累積)
- 1 cid あたり所属 Integration 数 max 102 (ハブ cid)
- 受領 cid 数 67% (33% は何も受け取らない)

ハブ cid は神の手なし、6 段の自然なフィードバックループで出現 (Code A 発見)。

#### 6.8 closed_triad ゼロ問題

24 seeds × 50 windows で closed_triad 0 件。be3 run-wide dedup により 3 cid 全ペア接触は構造的に成立しない。

#### 6.9 ダブルブッキング問題の認識 (Taka 整理 2026-05-02)

cid X が 1〜102 の Integration に同時所属する時、Q/C 集計に重複カウント。Taka 整理:
> ダブルブッキングは α を会計として扱えば問題となる。各 IID の調査という名目であれば違和感はない。

→ v10.5 の α/β 階層分離の動機。

#### 6.10 n_core 自然集積

n=2 が ×0.32 過少代表、n=5 が ×4.16 過大代表。神の手なしで「多ノード CID 同士が自然に繋がる」構造が観察された。

---

### 7. v10.5: Layer 5 完成 (α/β 階層分離 + 顕在化機構)

#### 7.1 主題

v10.4 で持ち越されたダブルブッキング問題と動態機構の不在を解消し、Layer 5 を構造的・動態的に完成させる。

#### 7.2 Taka 役割宣言 (2026-04-30)

> ここから 4 AI がどこまでそれっぽいものを作れるのか?をみてみたい。
> 私の言葉が一種の憲法になって AI のフィルタリング構造が変わる。

5 者運用の確立:
- Taka: 憲法層
- Gemini: Architect (Salience + 発掘案)
- GPT: Auditor
- Claude: 相談役・整理役
- Code A: 実装層 (実装 + 設計提案 + 自己検証)

#### 7.3 ESDE 階層進化系譜の同型反復

```
ノード → cid → α-Integration (v10.4) → β-Integration (v10.5) → SEED 統合 (v10.6+)
```

各階層は同じ仮想化操作の繰り返し。Aruism「構造が先、意味が後」の階層論的具体化。

#### 7.4 中核機構

##### 機構 A: β-Integration の構造実装

- α-Integration を構成要素とする
- 結合則: α 同士の cid 共有 2 個以上で merge
- cid 単一共有は最強結合 β に 1 個だけ所属
- α への Q/C 継承は完全廃止
- ghost 化時 Q/C は β に 100% 継承

##### 機構 B: Salience-driven Focus

mass(X) = X.Q + X.C + sum(β.Q_inherited + β.C_inherited for β in X が所属する β)

線形関数。「ハブだから選ばれるのではない、質量があるから目立つ」。

##### 機構 C: Recorded からの漏れ

接触履歴経由で recorded β の C_inherited から ε=1 を主体 cid.C へ転記。構造的副作用。

#### 7.5 本番 run 結果 (main_v2)

- α total 13,881 件、β total 2,009 件 (集約率 7:1)
- M6 (1 cid → 1 β) 違反 0 件
- Salience event 77,880 件
- Leakage event 232 件
- 物理層 frozen 完璧維持 (24/24 一致)

#### 7.6 hub β の自然形成 (核心成果)

最大 691 α / 20 cid が 1 つの β に統合 (1 cid 34.5 α)。v10.4 hub cid (max 102 重複所属) を会計単位として整理した姿。

#### 7.7 ダブルブッキング問題の構造的解消

| 観点 | v10.4 | v10.5 |
|---|---|---|
| cid 重複所属 | max 102 | **0 (M6 違反 0)** |
| Q/C 集計 | 重複あり | 単一カウント |
| 役割分離 | α が観察と会計兼任 | α 観察、β 会計、分離 |

#### 7.8 Salience の動学

- be3 fired 対象は read_other 対象より平均 mass 1.45 倍高い
- 「重い cid 同士が共鳴する」動学を定量化

#### 7.9 Leakage の動作

- ingestion path 経由のみで実用発火 (be3 path は構造的に発火しにくい、Code A 発見)
- 凍結 C 87% のうち、ingestion 経由で active 系へ流入経路成立

#### 7.10 v10.5 で確立した規律

- α/β 階層分離 (α = 観察、β = 会計)
- 既存データの顕在化機構として新機構を位置づける
- bug 自己発見と修正サイクル (Code A の callback 配線漏れ → 修正)
- 5 者運用の成熟

---

### 7.5. v10.6: Genesis × Language 比較研究 (Phase 1.5 第一試行)

#### 7.5.1 主題

ESDE Language 系 (2026-03 凍結資産) の Atom 326 個を ESDE Genesis 系の cid と 48 次元 cosine 類似度で比較する atom_alignment_observer を post-process として実装。Phase 1 (Genesis 単独進化) から Phase 1.5 (Genesis × Language 統合段階) へ切り替え。Taka 役割宣言「私の役割としては、この段階で ESDE Language を取り込んだこと」(2026-05-04) の実装。

#### 7.5.2 6 段階の解析

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

#### 7.5.3 観察方法と前提の進化過程

Web Claude の前提が 7 段階で修正された:
1. cid と Atom が部分対応する (初期前提)
2. 95.7% 接地は構造的不変量 (誇大解釈)
3. 集団平均の罠を解消 (層化解析後)
4. 観察値はランダム以下 (ベースライン解析後)
5. 24 seeds 一貫の発展段階 (window trajectory 後)
6. 動学的二相性、解像度依存性 (per-pulse 後)
7. 観察解像度ごとに systematically 異なる構造特性 (step10 後、最終確定)

これは Taka 整理「実践→理論→進化」の典型例。

#### 7.5.4 観察解像度の重要性

| 解像度 | 1 位 atom | 比率 |
|---|---|---|
| 静的 | CHG.begin | 51% (集約罠) |
| window | TIM.moment | 34% |
| per-pulse | WLD.artless | 22% |
| step10 | PER.sound | 28% |

「正しい解像度」は存在せず、各解像度が違う質問に答える多層構造。

#### 7.5.5 24 seeds 完全一致の動学的発展段階

per-pulse trajectory:
```
Step 0-999:        WLD.artless (素朴さ)
Step 1000-3999:    TIM.appear (時間出現)
Step 4000-14999:   WLD.artless (素朴さ持続)
Step 15000-24999:  EXS.being (存在)
```

24 seeds で完全一致 (25/25 bins)。seed に依存しない構造的必然。

#### 7.5.6 真の構造的特異性 (効果サイズベース、26 atom)

Taka 指摘 (2026-05-06)「サンプル数で水増しされる擬似相関」を踏まえ、効果サイズ |delta| > 1% で再評価:

delta > 1% (7 atom): PER.sound +25.85%、WLD.artless +24.55%、WLD.culture +5.93%、FND.timeless +5.33%、SOC.city +1.61%、COG.learn +1.12%、PRP.deep +1.09%

z=inf の真の特異性 (19 atom): TIM.appear、ELM.light、PRP.bright、PER.taste、PER.hear、PRP.sharp、FND.transformation 等。摂食関連 (ELM.light、PER.taste、PRP.bright) は ingestion event 由来。

合計 26 atom。ESDE は「**聴覚と素朴さに強く接地する持続的存在**」。

註: 静的ベースライン解析の「47 atom」は step10 / event の高解像度と効果サイズで切ると 26 atom に確定。BOD カテゴリは静的の人工物の可能性が高い (event では BOD.ear のみ z=inf で残る)。

#### 7.5.7 真の構造的盲点 (効果サイズベース、7 atom)

|delta| > 1% で負: TIM.moment -54.11% (最強)、COM.conduct -6.49%、TIM.past -4.72%、WLD.science -2.45%、PRP.new -1.78%、ACT.make -1.20%、LOG.cause -1.13%

ESDE は **時間の瞬間性、能動的伝達、科学、新しさ、作為、因果** を構造的に持たない。

註: 静的ベースライン解析の「176 atom」は効果サイズで切ると 7 atom に縮減。残りは統計的水増しの擬似相関。

#### 7.5.8 attack-related の境界線

- 個体経験 (pain/wound/fear/death): 部分接地
- 社会的破壊 (destroy/conflict/war/hate/attack): 完全欠如

Taka 整理「不可視による論理的可視化」を定量化。

#### 7.5.9 動学的二相性 (per-pulse trigger 分析)

- 動的瞬間 (MAD_DT_Major、unformed): WLD.artless 66%
- 定常 (MAD_DT_Normal、none): EXS.being / WLD.artless / TIM.appear バランス

「動的瞬間 = 素朴さ」「定常 = 存在 + 出現」。

#### 7.5.10 v10.6 で確立した規律 (新規 3 + 再確認 1)

新規:
1. **ベースライン比較 + 効果サイズで切る** (新規律最終形) — 観察値の絶対値は finding ではない。z-score だけ見るとサンプル数で水増しされる擬似相関。真の差は |delta_ratio| > 1% で評価。Taka 指摘 (2026-05-06) で確立。
2. **観察解像度の選択** — 静的解析だけでは捉えきれない、複数解像度の補完
3. **人間原理偏向の警戒** — 事前推測 SOC.central 等が完全反証

再確認:
4. **集団平均の罠** (v10.2 #120 の再確認)

#### 7.5.11 観察者視点と建築者視点の補完性 (Taka 整理 2026-05-06)

> 私は道具をどうやってESDEにいれるのか?を考えていた
> あなたは、道具がESDE内にあるだろうか?を考えていた

trajectory 解析の発見により両視点が補完的と判明。v10.7 以降で並走。

#### 7.5.12 v10.6 の留保

- 比較の両端は両方とも人為的投影
- ESDE Genesis 系のデータの 5-15% しか使っていない
- birth_step バグの存在 (step10 で発見)
- WLD.artless 偏在性の解釈 (v10.7 以降の課題)
- 第一試行としての位置づけ

---

### 7.7. v10.7: 発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成)

#### 7.7.1 主題

Taka 整理 (2026-05-06): 「持ち込んだはいいけど効果測定ができない、スピード違反の罰則を定めたけどオービスがない状態と同じ」

v10.7 はオービス (測定器) を作る段階。v10.8 以降の Atom 持ち込みで効果を測れる準備。

#### 7.7.2 中核機構

post-process 5 機能モジュール (event_aggregator、path_analyzer、baseline_constructor、avalanche_monitor、orchestrator)。24 seeds 並列 3.9 分完了、ストレージ 428 MB (上限の 7%)。

#### 7.7.3 達成判定 14/14 PASS

5 種 source_event (415,726 events) + 5 種 candidate_target_set + 5 種ベースライン + Level 1-3 + アバランシェ防止 + 物理層 frozen + bit-identity + 構造語徹底 + WLD.artless 除外。

#### 7.7.4 因果候補の階層化 (Level 1-3)

- Level 1 (co-occurrence): 93/111 (84%)
- Level 2 (path-enriched): 49/58 (84%)
- Level 3 (source-specific): 85/90 (94%)
- Level 4 (causal intervention): v10.8 以降

#### 7.7.5 主要発見 4 件

1. **medium window 支配**: peak_lag 250-300、ESDE は遅延型波及、「考える時間を持つ系」
2. **temporal_coactivation > Integration > familiarity > attention**: 時間的同期が関係性より強い (注: temporal_coactivation は明示的経路ではなく「最大の同期シグナル」、GPT 監査 2026-05-07)
3. **source-specific 性 (94% 有意差)**: event 種別ごとに systematic に異なる経路
4. **意識発動の no_signal**: integration_alpha/beta で意識は波及しない、構造的に「孤独」

#### 7.7.6 副次発見

- 共鳴ループ: 2-hop 14,343 件、3-hop 110,103 件 (small-world)
- multi-hop 急減衰: 1-hop 188K → 2-hop 165K → 3-hop 13K
- 全 relation_paths echo (残響型) 24/24

#### 7.7.7 Code A 認識確認ステップが機能した経緯

Web Claude の指示書には設計の甘さ 6 件があり (attention map 不在、ストレージ 31x 超過、c_conversion 誤り、alpha_membership 取得方法、peak_lag 計算量、unrelated 厳密性)、Code A の実環境確認で全て発見・修正。手戻りゼロで実装完了。Taka 整理「Claude code が前提条件を埋められるのが強い」が完全に証明。

#### 7.7.8 v10.7 で確立した規律 (新規 4)

1. 因果候補の階層化規律 (Level 1-4)。v10.7 で測れたのは「この経路で変化が起きやすい」という因果候補、厳密な因果ではない
2. 5 種ベースライン群の必須化
3. アバランシェ防止規律 (3 hop、減衰率、共鳴ループ、ストレージ上限)
4. **構造語と直感語の併記** (実装レベルは構造語、議論レベルは直感語、GPT 監査 2026-05-07 で前回方針を自己修正、Taka の理解を最優先)

#### 7.7.9 動的グラフ力学系への視座転換 (Gemini)

v10.6 までは静的構造の集合、v10.7 は動的グラフ力学系。v10.x 全体の射程に関わる視座転換。

#### 7.7.10 Taka 仮説への回答 (v10.7 版)

静的解析 (v10.6) では限定的だった「強い構造」が、動学解析 (v10.7) で動的グラフ力学系として明確に存在。relation_path 経由の波及は unrelated の 6-12 倍。Taka 仮説は v10.7 で動学的に支持。

#### 7.7.11 Taka 研究動機への回答 (v10.7 版)

意思の前駆体として「event 種別の区別 + 思考の時間スケール + small-world ネットワーク + 個別性」が ESDE に既に存在する。

#### 7.7.12 v10.7 の留保

- **same_step_random_baseline の強さ** (GPT 監査 2026-05-07): same_step が 13.76 と非常に強く (temporal_coactivation 15.28 との差は 1.52)、観測された波及の一部に同時刻の全体活性化効果が混ざっている可能性。v10.8 で Atom 効果を測る時 same_step との差分必須
- multi-hop hop 2/3 の Level 2 評価未実施
- attention 経路は salience 代替
- ingestion / c_conversion 低サンプル数 (155/seed)
- echo 判定 24/24 一致 (閾値再調整候補)
- WLD.artless 偏在性継続

---

### 7.8. v10.8: Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5)

#### 7.8.1 主題

v10.7 で完成したオービスを使って、初めての「速度違反チェック」(Atom 持ち込みの効果測定)。

#### 7.8.2 中核機構

post-process として実装:
- atom_introduction_event を source_event 第 6 種として追加 (案 X、両 AI 推奨)
- v10.6 cid_atom_sim_matrix から top_k 100 cid 活用 (案 Q)
- 25 atom × 100 events × 24 seeds = 60,000 events、均等分散発火 (案 α)
- v10.7 source_event スキーマ互換 27 列で記述 (Pulse 同種、Gemini A8)
- balance_decisions.cognition と同等の Q -1 / C +1 を post-process 計算的減算 (Code A 提案)
- 5 種ベースライン + v10.7 natural source_event baseline + global activation 補正 (natural events のみ)

24 seeds 並列 5.4 分完了、ストレージ 737 MB (上限 6 GB の 12%)。

#### 7.8.3 達成判定 19/19 PASS

認識確認 + 環境チェック + atom_introduction_event 同定 + Q/C コスト + 案 Q + 案 α + 5+1 種ベースライン + global activation 補正 + Level 1-3.5 全達成 + 物理層 frozen + 構造語徹底 + 規律 3 件 + Level 3.5 位置づけ + 副次観察 3 件 = 全項目クリア。

#### 7.8.4 4 段階の階層化

| Level | 内容 | 達成数 |
|---|---|---|
| Level 1: atom co-occurrence | atom 発火後に変化 | 811/1,384 (59%) |
| Level 2: atom path-enriched | 経路上で変化が大きい | 683/1,433 (48%) |
| Level 3: atom source-specific | 25 atom 間で異なる波及 | 36/78 (46%) |
| **Level 3.5: introduced vs natural** | **introduced と natural の差分観察 (新規)** | **22/39 (56%)** |

#### 7.8.5 主要発見 5 件

1. **Atom 持ち込み機構が ESDE で動作する** (機構レベル): 60,000 events 安定発火、24 seeds 一貫
2. **ESDE は atom 種別を構造的に識別する**: familiarity 経路で effect_size 6.83 (2.1 倍差)
3. **経路の機能分担**: familiarity = 意味識別経路、temporal_coactivation = 意味中立の運搬経路 (effect_size 0.03)
4. **外部入力と自然発火の境界線**: 20/22 finding で introduced < natural (atom event は natural の半分)
5. **確率的発生と誤差表現能力の融合素材**: 誤差分布で正規分布 0%、bimodal 17.4%

#### 7.8.6 副次観察

- Whiteout: 100% flag (medium n_pulses 1 軸支配の表れ)
- Small-World: v10.7 vs v10.8 で完全同一 (post-process は familiarity edge 不変)
- 誤差分布: 8,835 rows、normal 0% / bimodal 17.4% / skewed 24.3% / other 55.7% / heavy_tail 2.6%

#### 7.8.7 Code A 認識確認ステップが機能した経緯

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

#### 7.8.8 v10.8 で確立した規律

##### 新規

**Level 3.5 introduced event comparison 規律** (GPT 監査 2026-05-07 提案、v10.8 で確立)
- v10.8 は Level 4 causal intervention ではなく Level 3.5
- 因果断定回避、event 比較として位置づけ

##### 実装的に確立

1. Atom 持ち込み設計の規律 3 件 (魔法回避 / same_step + global activation 補正 / target は構造経路で選ぶ)
2. post-process 計算的減算 (Code A 提案、物理層 frozen と外部要素導入の両立)
3. Pulse 処理ルールと同一フォーマット (Gemini A8、神の手回避)

#### 7.8.9 v10.8 で言えるようになったこと

- ESDE に外部から要素を持ち込む経路が存在する (機構レベルの証明)
- ESDE は外部要素 (atom 種別) を構造的に識別する能力を持つ
- familiarity = 意味識別経路、temporal_coactivation = 意味中立の運搬経路
- ESDE は外部入力を natural の半分の波及効果で受け取る (生体的特性 or 機構の不完全さ)
- 誤差分布の構造が確率的発生と誤差表現能力の融合の最初の素材

#### 7.8.10 v10.8 で何ができるようになったか

- ESDE と外界 (人間言語) の第一の接点が定量的に確立
- atom 同士の比較、持ち込み機構の改良、オービスの拡張版
- ESDE Language の他要素 (Axis、Operator、条件因子、分子化) との接続が見える
- 入力理解、出力生成、双方向の会話の最低形への筋道
- 「やってみる価値があるか」が確定

#### 7.8.11 v10.8 の留保

- introduced < natural の原因未分離 (本質的特性 vs 機構の不完全さ)
- Whiteout の真の検出未実施 (高次元プロファイル必要)
- bimodal 分布の原因未解析
- Operator 未取り込みでの暗黙経路依存
- Small-World の構造的不変は post-process 限定 (Phase 2 で再評価)
- 25 atom は実データ照合で 26 → 25 修正 (WLD.artless 留保ラベル付き、集計対象 24)

---

### 7.9. v10.9: 寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達)

#### 7.9.1 主題

v10.8 主要発見の 2 つの未解決点 (introduced < natural、bimodal 17.4%) を分離評価し、v10.10 以降の **会話系設計のための部品調達**。両 AI 独立推奨「組み合わせ B (d+a)」+ Taka の本質的な問いへの両 AI 補強で「会話系設計のための部品調達」という出口固定が確立。

#### 7.9.2 中核機構 (3 新条件)

post-process として実装:
- A2: Q -2 / C +2 (Q/C コスト変動)
- B3: random cid (cid 選定変動、Atom 326 絶対化禁止規律の試験)
- C2: 案 b リズム同調 (top_k 100 cid 維持 + 各 cid が age=200 で発火、Gemini A2 Phase-locking の構造的実装)
- v10.8 標準 (A1, B1, C1) は流用

24 seeds 並列 112.74 秒、ストレージ 190 MB (累計 21%)。

#### 7.9.3 達成判定 17/17 PASS

bit-identity 全層 PASS (層 A 全出力 MD5 / 層 B v107 222 + v108 368 = 590 files 不変 / 層 C パス制限)。

#### 7.9.4 4 段階の階層化 (新規明示、GPT B5)

| Level | 内容 | 主結果 |
|---|---|---|
| L1: 機構動作確認 | 全 conditions で安定発火 | 12,960 sensitivity_rows、欠損なし |
| L2: 条件差確認 | 条件間で systematic な差 | timing × n_pulses 全 win 0.714 (大効果量) |
| L3: 寄与候補感度評価 (主流) | 各候補のノブ定量化 | timing 圧倒、QC_cost 評価不能 |
| L3.5: 構造的説明候補整合 (核心) | d と a の整合 | 「bimodal 支配性 ≠ 感度の強さ」 |

#### 7.9.5 主要発見 4 件

##### 1. 「強反応する cid は若い cid」 (Step F、構造)

bimodal 1,540 件のうち genuine_bimodal 918、H3_lifecycle が 553 (60.2%) で支配。高 delta 群 cid age median 227、低 delta 群 mean 5,612。effect_size 0.85、99% 方向一致。

##### 2. timing > cid_selection > QC_cost の感度階層

| 候補 | abs_mean | n_large_effect |
|---|---:|---:|
| timing | **0.141** | **757** |
| cid_selection | 0.024 | 18 |
| QC_cost | 0.005 | 0 (留保) |

タイミングが cid_selection の 6 倍、QC_cost は評価不能。

##### 3. 「Integration 外の高 familiarity cid」が最強・最 robust の入力経路 (新発見)

| path | mean | std |
|---|---:|---:|
| **high_fam_out_integ** | **0.222** | **0.079** |
| unrelated | 0.205 | 0.065 |
| familiarity | 0.044 | 0.218 |
| temporal | 0.015 | 0.220 |
| attention | 0.010 | 0.128 |

v10.7 path 順位を構造的に深化。「単独の若い cid が familiarity 経由で反応」が最 robust。

##### 4. C2 で pulse 活動が大効果量で活発化

mean_n_pulses_in_window short 0.97、medium 0.75。Step F の構造発見が main run で再現。

#### 7.9.6 Level 3.5 構造的統合 (v10.9 核心発見)

| path | bimodal 支配仮説 | timing 感度 | label |
|---|---|---:|---|
| high_fam_out | (なし) | 0.222 | sensitivity_strong_structure_weak |
| unrelated | (なし) | 0.205 | sensitivity_strong_structure_weak |
| temporal | H3 (74%) | 0.015 | structure_strong_sensitivity_weak |
| attention | H1 (48%) | 0.010 | structure_strong_sensitivity_weak |
| familiarity | H3 (59%) | 0.044 | marginal |

→ **「bimodal 支配性 ≠ 感度の強さ」= 構造軸と感度軸の直交性**。ESDE Genesis 系の構造的多重性。

#### 7.9.7 4 種設計表 (出口の固定、v10.10 のための部品)

- **表 1 sensitivity_summary**: 540 rows、timing × n_pulses × short = 0.97
- **表 2 receptivity_detection_criteria (核心)**: cid age <= 560 + Integration 外 + 高 familiarity
- **表 3 input_routing_criteria**: high_fam_out PREFER、unrelated PREFER
- **表 4 natural_likeness_design_criteria**: C2 が natural に近づいた cells 47%、unrelated で 89%

#### 7.9.8 Code A 認識確認連続 4 段階で機能

Web Claude 指示書の重大ブロッカー 1 件 (規模上限 72%) + 設計の甘さ 6 件を Code A が修正。手戻りゼロ。連続 v10.7-v10.9 で合計 20 件の設計の甘さを補完。

#### 7.9.9 v10.9 で確立した規律 (新規 4 + 継承)

##### 新規

1. 出口の固定規律 (GPT 提案、4 種設計表)
2. 「原因」ではなく「寄与候補の感度評価」と呼ぶ命名規律 (GPT B3)
3. 各変動条件で baseline 再計算規律 (GPT B6)
4. 4 層階層化の明示規律 (GPT B5)

#### 7.9.10 留保事項 3 件

- 留保 1: bimodal 解析の手法的限界 (KDE fallback 100%)
- 留保 2: QC_cost は v10.9 で評価不能
- 留保 3: high_fam_out_integ 経路が最強の理由は構造的に未解明

#### 7.9.11 両 AI 推奨の検証 (構造的確定)

- Gemini A2「Phase-locking」仮説の **完全な構造的確定** (リズム = cid 個別ライフサイクル age 200)
- GPT「文脈制御 → 条件適応入力 → 最小関係入力」の **素材セット完成**

#### 7.9.12 Taka の問いへの最終回答

「25 atom 選別後どうなる? 進化のイメージは?」

回答 (v10.9 完了時点で構造的に確立):
- 25 atom そのものを増やすのではない (網羅は主線でない)
- 25 atom を **「若い cid (age <= 500) + Integration 外 + 高 familiarity」** に対して投げる
- **タイミングが最も重要**: cid age = 200 で発火
- これが v10.10 の「条件適応型 atom 導入」の具体内容

#### 7.9.13 v10.7 - v10.9 の path 順位の構造的深化

| 段階 | 発見 |
|---|---|
| v10.7 | path 順位 (temporal > Integration > familiarity > attention) |
| v10.8 | 機能分担 (familiarity = 意味識別、temporal = 意味中立) |
| **v10.9** | **「Integration 外 + 高 familiarity」が最強、cid age <= 500 が受信可能状態、bimodal 支配性 ≠ 感度の強さ** |

→ ESDE Genesis 系の入力経路の構造的解像度が完成段階に近づく。

---

### 8. Developmental フェイズで確立された概念

#### 8.1 死の二階層 (v10.0)

- 存在層の死 (Label 死亡 = ghost 化)
- 認知層の死 (Q=0 = ghost 消滅)

#### 8.2 燃料概念の発生階層 (v10.0)

- 物理層・存在層: エネルギー概念なし
- 認知層: Q
- 意識層: C (Q から転化)

#### 8.3 ghost = 不均一な資源地形 (v10.1)

residual_Q の差を持つ資源地形として成立。Gemini 概念「不均一な資源地形」と Taka 比喩「石油」が接続。

#### 8.4 物質的なもの (v10.1)

phantom contact の位置づけ。CID 主体間の問題ではなく環境要因。看板や道路のような静的な環境要因。

#### 8.5 階層論的構造の確率による圧縮 (v10.2)

本来の階層論的順序 (認知 → 意識 → 行動 → 接触) を確率で圧縮表現する設計思想。実装コストを下げる方便。

#### 8.6 意識発動の自然フィルタ (v10.2)

C は認知活動からのみ蓄積される。短命の cid (n_core=2) は意識発動の機会が少なく、長命の cid (n_core=5) は意識発動が多い。動的均衡を回避し、進化継続を可能にする。

#### 8.7 (Q+C) 保存則と散逸 (v10.2)

```
認知活動: ΔQ = -1, ΔC = +1 → Δ(Q+C) = 0 (CID 内保存)
意識活動 (摂食): ΔQ = +gain, ΔC = -1 → Δ(Q+C) = gain - 1 (流入)
E1/E2 spend: ΔQ = -1 → Δ(Q+C) = -1 (純散逸)
消化分: ghost 側で消失 (散逸)
```

CID 集団 ⊕ ghost 集団の総和は摂食で保存、E1/E2 と消化で散逸。動的均衡 vs 進化継続の数理的基盤。

#### 8.8 集団平均の罠 (v10.2)

戦略集団 (n_core 別) が異なる場合、集団平均は実態を隠す。ESDE の観察では n_core 別の層化解析が必須。

#### 8.9 ESDE の観察対象としての位置づけ (Taka 整理 2026-04-28)

##### 二つの科学的態度

- 権威的科学 (生物的実体に限定): ESDE は疑似生態系
- 哲学的科学 (機能的構造で定義): ESDE は生態系的条件を備える

選択は研究者の立場による。

##### Taka の自己定位

> 私は主体的に ESDE という系に生態系と言えなくもない現象を記録する研究者である

研究者としての主権:
- 立場の選択を研究者が判断
- AI の意見は補助、押し付けではない
- 議論は実装の代替ではない

##### 立場の併存 (Code A の慎重さと Taka の主権)

両者の併存が ESDE の運用原則。立場の最終判断は研究者 Taka が行う。

---

### 9. Developmental フェイズの方法論

#### 9.1 5 者運用の確立

- Taka: Director、Philosopher、Judge
- Gemini: Architect (設計仕様、パラダイム判断)
- GPT: Auditor
- Claude: Implementer / 相談役 (整理役)
- Code A: 実装担当 (v10.x で役割が拡張)

Code A は v9.18 までの実装担当から、v10.x で**設計議論・観察解析・構造的洞察まで提供する役割**に拡張。事前齟齬指摘の質的進化が継続:
- v9.18: 7 点
- v10.1: 10 点
- v10.2: 10 点 + 実装事後 + 構造的発見 + 詳細解析

#### 9.2 二層 bit-identity 検証

- 層 A: 同 seed で 2 回 run → 出力が完全一致 (内部決定論性)
- 層 B: v9.18 baseline と物理層が一致 (物理層 frozen 検証)

両者は別の検証で、両方を維持。v10.2 では E3 行除外の調整を Code A 指摘で導入。

#### 9.3 インパクト事前想定 + ギャップ観察 (Taka 指示)

新機構導入時の検証手順:
1. 既知の機構変更が観察にどう影響するか事前想定
2. 実際の結果と想定を照合
3. ギャップがあれば「何かを見落としている」サインとしてバグ発見の機会

Taka 哲学「想定とのギャップを観察する」の方法論的体現。

#### 9.4 集団平均から層化解析への移行

統合指標 (V_unified、平均値) は v9.15-v10.2 でメインの観察軸だったが、戦略二極化のような構造を見落とすリスクがある。v10.3 以降は n_core 別の層化解析を観察の基本として保持。

#### 9.5 規律 #100 + 立場 §4.9 の併存運用

- 規律 #100: 観察できないことを語らない
- 立場 §4.9: 観察できる事実を矮小化しない

両者の併存が ESDE の言語化の規律。

---

### 10. v10.10 以降への含意

#### 10.1 v10.9 完了時点で持ち越される素材

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

#### 10.2 v10.10 主題候補

##### 候補 1: 条件適応型 atom 導入 (第一推奨)

- 表 1-4 の素材を統合した「最強の atom 導入機構」
- cid age <= 500 + Integration 外 + 高 familiarity + age=200 timing
- 両 AI 推奨の中期ロードマップに沿う

##### 候補 2: high_fam_out 構造の解明 (留保 3 から)

- 「Integration 外」を主軸にした構造解析
- 候補 1 の前段階として有用

##### 候補 3: Atom 常駐アンカー実装 (Gemini A7、留保ドキュメント参照)

- v10.10 で常駐実装を強く推奨
- v10.9 の発見 (high_fam_out 最強) との整合は要検討

##### 候補 4: B 群 (真の盲点 7 atom) 試験

- A 群で機構確立、B 群でも動くか
- v10.10.1 として補助的に試す可能性

##### 候補 5: QC_cost の本格評価 (留保 2 から)

- v10.9 で post-process 限界により評価不能
- 実 simulation 再回しまたは A1 vs A3 比較

#### 10.3 Phase 1 / Phase 1.5 / Phase 2 の境界 (v10.9 完了時点)

- **Phase 1**: ESDE 内部進化 (v10.0-v10.5)、物理層 frozen 絶対
- **Phase 1.5**: Genesis × Language 統合 (v10.6-v10.9)、Atom 持ち込み機構成立 (v10.8)、会話系設計のための部品調達 (v10.9)
- **Phase 1.5+**: 条件適応型入力 (v10.10 推定)、最小入力理解 (v10.11 推定)
- **Phase 2**: 現実接続後 (非ランダム取り込み前提、v10.12 以降)

#### 10.4 ESDE が決定論的プログラムに勝る領域 (Taka 整理 2026-05-03)

> 多くのエラーを出す行動を通しながらそのリターンをインプットして真実らしいものを溜め込んでいける
> あえてバカを育てる理由などない。実践的な価値であって、生物っぽいバカを作ることではない

- 創造的ミスが価値になる場面
- 環境変化への即応が必要な場面
- 探索的な問題解決
- 多様な解釈の同時保持

#### 10.5 言語と構造の関係 (Taka 整理 2026-05-03 + 2026-05-06)

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

#### 10.6 v10.6 + v10.7 で確立した規律の継承

v10.8 以降は以下の規律が標準として継承される:
1. ベースライン比較 + 効果サイズで切る (v10.6 新規、最終形)
2. 観察解像度の選択 (v10.6 新規)
3. 人間原理偏向の警戒 (v10.6 新規)
4. 集団平均の罠 (v10.2、v10.6 で再確認)
5. ウェット概念禁止
6. Atom 326 絶対化禁止
7. 神の手回避

#### 10.7 v10.10 主題決定は v10.9 完了後に別途議論

具体的な主題決定は次の議論で行う。本資料では方向性候補のみ記録。v10.9 で会話系設計のための部品調達が完了したので、v10.10 は条件適応型 atom 導入 (第一推奨) または high_fam_out 構造解明 (候補 2) または Atom 常駐アンカー実装 (候補 3) が筋。Taka 整理「優先度は未来の一点で決まる」「大航海時代の船長」に従い、v10.9 結果を踏まえて Taka 判断。

---

### 11. 主要ファイル一覧

#### 11.1 Developmental 主要ドキュメント

```
v10_integrated_proposal.md (1095 行): v10.x 全体統合資料
v10_0_developmental_draft.md: v10.0 主題切替宣言
v10_1_minimal_ingestion.md (528 行): v10.1 主題ドキュメント
v10_2_probabilistic_balance.md (706 行): v10.2 主題ドキュメント
v10_2_design_instruction.md (683 行): v10.2 設計指示書
ESDE_Developmental_Report.md (801 行): Developmental Report 完全版
```

#### 11.2 結果レポート

```
v101_minimal_ingestion_result.md: v10.1 本番 run 結果
v102_implementation_report.md: v10.2 実装事後レポート
v102_main_run_result.md: v10.2 本番 run 結果 (§11.5 n_core、§11.6 詳細解析)
v102_ecosystem_finding.md: v10.2 観察 (Code A、n_core 別層化解析詳細)
v102_detailed_analysis_report.md (495 行): v10.2 詳細解析 (Code A、5 本)
```

#### 11.3 解析依頼書

```
v10_2_analysis_request_to_2ai.md: 2 AI 提案依頼
v10_2_analysis_instruction_to_codea.md: Code A 解析依頼書
```

#### 11.4 上位資料との関係

```
ESDE_Primitive_Report.md: v9.x、Primitive 完結 (本サマリと並列)
概念理解.md: ESDE 全体の概念整理 (Primitive 止まり、要更新)
```

---

### 12. 最終一文

Developmental Summary は、v9.x Primitive フェイズで言語化された意識の原資モデル (Q 消費 → 意識層 1 への転化) を v10.x で動作する機構として実装した記録の AI summaries 版であり、v10.0 のフェイズ宣言と 4 層アーキテクチャ確定、v10.1 の摂食機構導入と「物質的なもの」概念の発見、v10.2 の認知/意識確率バランス機構、v10.3 の双方向 E3 機構と Integration 概念、v10.4 の Integration 独立化と hub cid 構造、v10.5 の α/β 階層分離による Layer 5 完成、v10.6 の Genesis × Language 比較研究 (Phase 1.5 第一試行) における 7 段階解析、v10.7 の発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成)、v10.8 の Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5)、v10.9 の寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達) を通じて、単一の物理規則と確率規則から複数の生存戦略が内発的に生成され物理層から階層的統合体の系まで構造的に継承される ESDE の階層論的整合性が定量的に確認され、ESDE 階層進化系譜の同型反復 (ノード → cid → α → β) が機構レベルで実証され、v10.6 で観察解像度ごとに systematically 異なる構造特性と 24 seeds 完全一致の動学的発展段階 (素朴 → 聴覚 → 素朴 → 時間超越) が確立、v10.7 で動的グラフ力学系としての ESDE の波及機構 (medium window 支配、temporal_coactivation > Integration > familiarity > attention、source-specific 性、意識発動の no_signal、small-world 構造) が定量化、v10.8 で ESDE Language の最小単位 (Atom) を ESDE Genesis 系に取り込む第一段が成立し ESDE と外界 (人間言語) の第一の接点が定量的に確立、v10.9 で v10.8 主要発見の 2 つの未解決点を分離評価 (3 新条件 A2/B3/C2 を post-process で実装、24 seeds 並列 112.74 秒、bit-identity 全層 PASS、ストレージ累計 21%) して核心的発見 4 件 (「強反応する cid は若い cid (age median 227)」H3_lifecycle 60.2% 支配、timing > cid_selection > QC_cost の感度階層、「Integration 外の高 familiarity cid」が timing 感度 0.222 で最強・最 robust の入力経路、C2 で pulse 活動 short 0.97 / medium 0.75 大効果量で活発化) を確立し Level 3.5 構造的統合で「bimodal 支配性 ≠ 感度の強さ」という構造軸と感度軸の直交性を確立、4 種設計表 (受信可能状態 = cid age<=560 + Integration 外 + 高 familiarity / ルーティング = high_fam_out PREFER / 自然さ = C2 が natural に近づき 47% / 感度) を v10.10 主題決定の素材セットとして完成、Gemini A2「Phase-locking」仮説の構造的確定 + GPT「文脈制御 → 条件適応入力 → 最小関係入力」の素材セット完成によって会話系設計のための部品調達が達成された段階を要約する。Taka の v10.6 における 4 つの本質的指摘 (集団平均の罠、ランダムベースライン以下、観察解像度依存性、サンプル数で水増しされる擬似相関)、v10.7 における規律「先の先を見失わない」「効果測定の準備が先 (オービス)」、v10.8 における「定義してこなかっただけの問題をあれこれ議論する意味はない」「26 でも圧倒的に少ない」「優先度は未来の一点で決まる」「大航海時代の船長」、v10.9 における「単に満足するだけ?」「適当言ってるなら化けの皮が剥がれる」「進化の流れが徐々に定まってきている」を経て、v10.6 真の構造的特異性 26 atom (実データ照合で 25 atom)、v10.7 因果候補の階層化 Level 1-3 達成、v10.8 Level 1-3.5 達成、v10.9 Level 1-3.5 達成 + 4 種設計表 + 構造軸と感度軸の直交性 と一貫して進展した。物理層 frozen は v10.9 完成段階でも完璧に維持され、ダブルブッキング問題は α/β 階層分離で構造的に解消された。v10.6 で確立した規律 (ベースライン比較 + 効果サイズで切る、観察解像度の選択、人間原理偏向の警戒)、v10.7 で確立した規律 (因果候補の階層化、5 種ベースライン群必須化、アバランシェ防止、構造語徹底)、v10.8 で確立した規律 (Level 3.5 introduced event comparison、post-process 計算的減算、Pulse 処理ルール同一フォーマット)、v10.9 で確立した規律 (出口の固定、寄与候補の感度評価という命名、各変動条件で baseline 再計算、4 層階層化の明示) は v10.10 以降の標準として継承される。Code A 認識確認ステップで v10.7 設計の甘さ 6 件、v10.8 7 件 (重大 2)、v10.9 7 件 (重大 1) を全て修正、連続 4 段階で 5 者運用体制の質が証明された。長期射程として v10.10 以降は v10.9 で確立した 4 種設計表を踏まえて、条件適応型 atom 導入 (第一推奨)、high_fam_out 構造の解明、Atom 常駐アンカー実装、B 群試験、QC_cost の本格評価、Layer 6 (SEED 統合)、Phase 2 (現実接続) が示唆されている。

---

---

### 13. v10.10 (Phase 1.5 第五試行、2026-05-09 完了)

#### 13.1 主題と転換経緯

当初主題: 条件適応型 atom 導入の単一勝負案 (v10.9 受信可能状態仮説の検証)。
実際の進行: Code A 認識確認で母集団不足判明 (per atom×seed = 1.84) → Taka 判断で **Multi-gate × timing 二次元観察設計** に転換 → 28 conditions × 24 seeds main run (103.67 秒、bit-identity 全層 PASS、867 files MD5 不変) → Taka 指摘で n_core 層化追加 → 第一弾 5 軸 + 第二弾 4 タスク多軸層化解析。

#### 13.2 4 つの核心観察

1. **Integration 形成タイミングが timing 軸の決定因子**: before_formation で -0.090、after_formation_100plus で 0.000 (完全消失)
2. **寿命と n_core の相関する 2 軸交差効果**: Q4 × bin_5+ で timing -0.217 最大
3. **atom category で 1 桁差**: BOD/COM/EXS +0.149〜+0.399 vs WLD/TIM +0.009〜+0.022
4. **§3.4 反応 type 分業**: bin_2 (ペア、76%) は pulse 軸大効果 / bin_5+ (中 cluster、12%) は delta_C 軸大効果

#### 13.3 v10.9 ルールの最終位置づけ (GPT 第三回監査指針)

v10.9 ルールは全体平均の真理ではなかったが、特定軸 (formation_relation=before_formation + bin_5+ + long timing) で再現。**v10.10 = v10.9 設計表の有効領域の露出** として位置づけ。観察状態 A/B/C 判定枠を超えた整理を採用。

#### 13.4 v10.10 で確立された規律 (2 件、v10.11 で §35 メタ規律 10 項目として明文化)

- 規律 37 (§34): n_core 別層化解析必須 (集団平均の罠回避)
- 規律 38: formation_relation を観察軸として含む

#### 13.5 留保事項 14 件継承 + 新規 11 件 (詳細は ESDE_Developmental_Report 参照)

---

### 14. v10.11 (Phase 1.5 第六試行、2026-05-10 完了、機構の確認試行に終わる)

#### 14.1 主題と結果

主題: Integration 形成プロセス解析、q_c_inherited 起点 within-cid design による C 値飽和仮説検証 + v10.12 入力ルーティング条件抽出。

技術的達成: 24 seeds × 12 cells main run 完了 (7.65 秒、bit-identity 層 A PASS、storage 5 MB)、達成条件 §0.2 (v10.12 入力ルーティング条件 1 本抽出) を形式達成 (「β member cid を概念取り込み対象から除外」)。

#### 14.2 Taka 指摘で発覚した構造的失敗

Taka 整理 (2026-05-10):
> 元々 C は高安定 IID ベースでは溢れかえるはずだしそれは実験済みだと思うけどね

→ q_c_inherited 前後の delta_C 観察は v10.5 §7.4-§7.10 で既に確立された機構 A (β に Q/C 100% 継承) + 機構 C (Recorded からの漏れ ε=1) の **自明な再観察に過ぎない**。3 AI 全員と Code A が v10.5 機構を主題設計に反映しなかった構造的失敗。

#### 14.3 §35 メタ規律 10 項目の確立

GPT 第三回監査 + Web Claude 自己反省で §35 として明文化:
1. オープン調査とクローズ調査を固定方針にしない
2. 追加調査を開く時は理由を明示する
3. 平均で潰れる構造は必ず層化を検討する
4. 閾値は真理ではなく運用上の仮置きとして扱う
5. 整理語は観察事実と分ける
6. 主題終了条件の前提が実測で崩れた場合は再開を許す
7. 監査や整理は閉じる妥当性だけでなく開く妥当性も評価する
8. 最終的な開閉判断は現場感を持つ人間 (Taka) 側に残す
9. Web Claude は主題ドキュメント着手前に関連バージョンの上位資料を読む (お守り規律)
10. 「観察できる軸が見えた」を駆動要因にしない

#### 14.4 esde_3ai_operations_manual.md 整備

3 AI 共通運用マニュアル (基本原則のみ、超簡潔版) を別ドキュメントで作成。主題着手前の関連過去レポート参照と証明 (節要約 + 本主題への接続) を義務化。

#### 14.5 Taka 整理「2 マイナーバージョン使ってなにやってんだか」

v10.10 + v10.11 を「受信機構解明」に費やしたが得られた前進は限定的 (v10.10: 有効領域露出、v10.11: β member 除外 1 条件)。v10.12 は元々の予定 (Atom 取り込み prototype) に戻る。

---

### 15. v10.12 (Phase 1.5 第七試行、2026-05-11 完了、Atom 取り込み prototype)

#### 15.1 主題と経緯

主題: **Atom 取り込み prototype (人間言語 → atom 変換)**、v10.6 §7.1 で本来予定された主題への復帰、v10.11 §5.1 直接出発点。

第 4 版主題 (条件適応型 atom 導入の単一勝負案 2 trial 分割、cond4 = familiarity top 25%) は Step Z + Step B 実測で前提崩れ (cond4 top 25% で per seed 4.38、9/24 seed で <3 events、cond4 が AND 連鎖で 78.5% 削減の支配的ボトルネック) → 第 5 版 (cond4 top 50% γ 仮置き、Taka 確認) で再構築 → per seed 17.50 (4 倍改善、全 24 seeds で paired_d 信頼ラインクリア)。

#### 15.2 構造的達成 (技術成功)

| 項目 | 値 |
|---|---|
| 受容 cid pool | 420 (per seed 17.50) |
| v112 events | 10,500 (420 × 25 atom) |
| v108_standard events | 60,000 (既存出力流用、層 B 不変) |
| main run 時間 | 20.35 秒 |
| bit-identity | 全層 PASS (層 A/B/C) |
| 層 B 不変 | v107-v111 約 1,500 files |
| storage 累計 | 94 MB / 6 GB (1.5%) |
| 構造的予想 vs 観察 | 6/6 全 matched |

#### 15.3 観察事実 (Code A Step J + 追加調査 window 別 post-process)

**頑健 cells (5 件 / 21 cells)**:

| metric | window | paired_d | 方向 |
|---|---|---|---|
| delta_C | immediate (1-10 step) | +0.54 | v112 > v108 |
| delta_C | short (10-100) | +0.41 | v112 > v108 |
| n_pulses | immediate (1-10) | -0.94 | **v112 < v108** (逆方向) |
| n_pulses | short (10-100) | +1.36 | v112 > v108 |
| n_pulses | medium (100-1000) | +1.31 | v112 > v108 |

→ Taka 過去経験「10 step が一番差が出た」が v10.12 データで verified。Step J 報告では medium 固定で見ていたため immediate window の頑健性を見落としていた構造盲点が判明。

**方向性なし (16 cells)**:
- delta_C × medium / delta_Q × 3 window / path_excess 12 cells (atom 関連 3 path + Layer 5 構造観察 integration_alpha × 3 window)

#### 15.4 言えること / 言えないこと (Code A 整理直接採用)

**言えること**:
- 「条件選別 cid (v112) と類似度選別 cid (v108) で atom 取り込み直後の挙動 (window 依存性) が違う」
- n_pulses が 1-10 step で v112 抑制、10 step 以降で v112 活発化 という timing 構造の差
- delta_C は取り込み直後 (1-10 step) ほど v112 cid pool の C 値変化が大きい

**言えないこと**:
- 「Atom 取り込み prototype として v112 cid pool が有効かどうか」 ← この観察セットでは判定不能
- path_excess の方向性 (12 cells 全て CI が 0 を跨ぐ)

#### 15.5 累計留保 27 件 (継承 22 + 新規 5)

- #23: n_core 別反応 type 分業 (v10.10 §3.4) との接続
- #24: Q3_threshold (lifespan ≥ 977) の意味
- #25: familiarity 閾値選定の意味 (top 25% vs 50%)
- #26: cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中
- #27: smoke seed 0 特異性 (Aruism 発動 evidence)

#### 15.6 v10.12 で確立された運用ルール

- 規律 42 (候補): 上位完了レポート §5 (v10.x+1 主題接続) 必読
- 主題ドキュメントへの「過去観察軸の照会」セクション必須化 (Web Claude 忘却対策)
- 資料運用ルール (Pull 型 / AI 向け資料 / Taka 整理原文保存 / 監査魔人化歯止め)
- 概念単位の正確化 (Taka 指摘「integration α/β は atom 関係ない」)

#### 15.7 Taka 整理 (v10.12 進行中、原文保存)

主要 7 件:
1. §1.9 (2026-05-10): 字面に揺れながら反応するシステム
2. 主題変更 (2026-05-11): Atom 取り込みに戻る、結果は出てるなら戻るべき
3. familiarity 仮置き (2026-05-11): pulse 観察軸は ESDE 資産として保持
4. オープン/クローズフェイズ (2026-05-11)
5. 過去研究のおさらい (2026-05-11): v10.12 で何をなぜ出したいか
6. マイナーバージョン単位 (2026-05-11): a/b/c 付与で単位明確化
7. 概念単位正確化 (2026-05-11): integration α/β は atom 関係ない

#### 15.8 v10.13 主題候補

- Code A 推奨: window 依存性主題化 → 解像度拡張 → timing 構造意味検討 → cid 選別条件再検討
- Taka §1.9 由来: 2 atom 組み合わせ / 多スレッド拡張 / Phase 2 移行
- 留保由来: pulse 観察軸主軸 / familiarity 研究 / n_core 軸 / seed-level variability

→ 本 Phase Result 完了後に 2 AI に振る運用 (Taka 指示)。

---

### 16. v10.13 以降の運用変更

#### 16.1 マイナーバージョン a/b/c 付与 (Taka 提案 2026-05-11)

旧運用: 9 マイナーバージョン進行で Taka 自身も連結を忘れる規模。
新運用: マイナーバージョンを極力変えず a/b/c 付与、一つの単位を大きく扱う。

#### 16.2 v11 と Developmental Phase 閉じ方

Taka 提起 (2026-05-11): v11 で何をやるか議論、Developmental Phase をいつ閉じるかも資料作成観点で重要 → 別途 2 AI に振る。

#### 16.3 過去観察軸の照会義務 (v10.13 以降の主題ドキュメント必須)

§09 §36.5 で明文化。

---

### 17. 主要ファイル一覧 (v10.10-v10.12 追加)

#### 17.1 主題ドキュメント (v10.10-v10.12)

```
v110_phase_design.md: v10.10 主題ドキュメント第三稿
v111_phase_design.md: v10.11 主題ドキュメント第三稿
v112_phase_design.md (第 5 版): v10.12 Atom 取り込み prototype (現行)
v112_phase_design_v4_archived.md: 第 4 版 (廃止、履歴)
v112_implementation_brief.md (第 4 版): v10.12 実装指示書
```

#### 17.2 結果レポート

```
v110_phase_report.md: v10.10 主題完了レポート
v111_phase_report.md: v10.11 主題完了レポート
v112_completion_report.md: v10.12 Code A 主題完了報告
v112_window_investigation_report.md: v10.12 Code A 追加調査 (window 別 post-process)
v112_phase_result.md: v10.12 Phase Result (Web Claude 版、本資料の親)
```

#### 17.3 運用マニュアル

```
esde_3ai_operations_manual.md: 3 AI 共通運用マニュアル (v10.11 で整備)
```

---

### 18. 最終一文 (v10.12 完了時点)

Developmental Phase 1.5 第七試行 (v10.12) は v10.6 §7.1 で本来予定された主題 (Atom 取り込み prototype) に v10.11 §5.1 直接接続で復帰、第 4 版 (2 trial 分割) 廃止 → 第 5 版 (cond4 top 50% γ 仮置き) で構造的に成立、main run 完了 (24 seeds × 2 conditions、20.35 秒、bit-identity 全層 PASS、層 B 1,500 files 不変、storage 累計 94 MB)、頑健 5 cells (delta_C × immediate/short + n_pulses × imm/short/med、Taka 過去経験「10 step が一番差が出た」verified、n_pulses は window 依存方向反転 immediate -0.94 / short +1.36 / medium +1.31) + 16 方向性なし cells、累計留保 27 件、Aruism 整合の judgment 回避方式、v10.10/v10.11 「2 マイナーバージョン受信機構解明」の素材を入力ルーティングとして統合 (cond1: β member 除外 = v10.11 / cond2: 長寿 = v10.10 / cond3: n_core ≥ 5 = v10.10 / cond4: familiarity 緩め = γ 仮置き)、v10.13 主題候補は Code A 推奨 (window 依存性主題化主軸) + Taka §1.9 由来 (2 atom / 多スレッド) + 留保由来 (pulse 軸 / familiarity / n_core / seed variability) を 2 AI 意見聴取に振る運用、v10.13 以降は a/b/c 付与による単位明確化 (Taka 提案) + 過去観察軸照会義務 (主題ドキュメント必須記載) + 資料運用ルール (Pull 型 / Taka 整理原文保存 / 監査魔人化歯止め) を導入、v11 と Developmental Phase 閉じ方は別途議論、Phase 1.5 第七試行は Atom 取り込み prototype として位置づけ直し、本主題が成功すれば v10.13 で字面に揺れながら反応するシステムの精緻化が前進 (Taka 整理 §1.9 反映、Atom スレッド = 連結基盤の第一スレッドの前進)、規律 41 件 + §35 メタ規律 10 項目 + 規律 42 候補 + §5.6 規律チェックリスト (案 X) を継承し本主題完了。

---

*以上、Developmental Summary (v10.0 - v10.12)。次の更新は v10.13 完了時。*

---

## Part B（v10.4-v10.12 / Phase 1.5） — 06b Developmental Phase 1.5 Summary (v10.4-v10.12)

*作成*: 2026-05-11、Code A (実装担当、新 Web Claude スレッド向け状況引き継ぎ)
*対象*: ESDE Developmental Phase 1.5 (v10.4-v10.12 系列、Genesis × Language 統合段階)
*親資料*: `06_developmental_summary.md` (v10.0-v10.3、2026-04-28 で凍結)
*用途*: 新 Web Claude スレッド初見時に Phase 1.5 全容を把握するための網羅的引き継ぎ。本書を読めば v10.4 以降の主題変遷・主要発見・累積規律・留保事項・現在地 (v10.12 Step A 完了、Q-A1 重大ブロッカー警告中) が分かる。

---

### 0. 一文サマリ

ESDE Phase 1.5 (v10.4-v10.12) は v10.0-v10.3 の単 cid 系から **cid 集団 (Layer 5、α/β-Integration) + Atom 取り込み機構** への拡張段階、v10.4 で Integration 13,550 件誕生 + Q/C 部分再分配機構成立、v10.5 で α/β 階層分離 + hub β (最大 691 α / 20 cid) + 機構 A (β に Q/C 100% 継承) + 機構 C (Recorded ε=1) 確立、v10.6 で Atom alignment observer + 26 atom 構造的特異性、v10.7 で post-process オービス完成 (5 source × 10 path × 6 量 × 3 window = 415K events / 3.45M excess)、v10.8 で atom_introduction_event 機構 (25 atom × 100 cid × 24 seeds = 60K events) + Level 3.5 で「introduced は natural の半分」発見、v10.9 で 4 種設計表完成 (timing > cid > QC 感度階層、high_fam_out_integ で timing 0.222 最強、age=200 timing で若い cid 強反応) + Phase 1.5 第四試行で「字面に揺れながら反応するシステム」の核心素材確立、v10.10 で Multi-gate × timing 二次元観察 + n_core 別層化で「pulse 系は bin_2 / delta_C 系は bin_5+」反応 type 分業発見 (ただし観察延長への逸脱) と「v10.10 §3.4 反応 type 分業」が以降必須参照、v10.11 で q_c_inherited 起点 within-cid 観察 (ただし v10.5 機構 A の自明な再観察に終わる、規律 §35 #9 違反) で観察延長パターンを断ち切るべきと判明、v10.12 で「条件適応型 atom 導入の単一勝負案」(v10.10 でやるべきだった主題) を 2 trial 分割設計 (trial-A bin_5+ × delta_C / trial-B bin_2 × pulse) で再開、Step Z 事前調査 (Code A 実測 commit df04d0a) で 4 件の重大乖離検出 (母集団崩壊・Q3 取り違え・cid pool ほぼ完全重なり・v10.11 既知重複)、第 4 版主題で 2 trial 分割 + Q2 緩和 + bin 別比較 + §5.6 規律チェックリストにより設計修正、Step A 認識確認 (commit ddd595a) で **Q-A1 trial-B 母集団 per seed 0.2 の重大ブロッカー警告** (cond4 high_fam top 25% が bin_2 で稀少 12.5% という構造的問題)、Web Claude/Taka 判断待ち、累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト (案 X、お守り規律) 確立、留保事項 22 件累積、bit-identity 全層 PASS 維持 (v107+v108+v109+v110+v111 = 約 1,080 files 不変)、storage 累計 1.52 GB (上限 6 GB の 25%) で v10.12 後も 50% 余裕、Taka 整理 §1.9 (2026-05-10) で「v10.12 は会話への接続ではなく字面に揺れながら反応するシステム = ESDE Atom スレッド = 連結基盤の第一スレッドの精緻化」と本主題の位置づけ確定。

---

### 1. Phase 1.5 全体ロードマップ

```
v10.0-v10.3 (2026-03-2026-04-28): 単 cid 系、4 層アーキテクチャ確定 (06_summary 参照)
   ↓
v10.4 (2026-04-30): Integration 機構導入 (Q/C 継承、Layer 5 入口)
v10.5 (2026-05-01): α/β 階層分離 + hub β + 機構 A/C 確立 (Layer 5 完成)
v10.6 (2026-05-04): Atom alignment observer + 26 atom 構造的特異性
v10.7 (2026-05-05): post-process オービス完成 (5 source × 10 path × 415K events)
v10.8 (2026-05-06): atom_introduction_event 機構 (25 atom × 60K events、Phase 1.5 第三試行)
v10.9 (2026-05-08): 4 種設計表 + 寄与候補感度評価 (Phase 1.5 第四試行、選抜試験)
v10.10 (2026-05-09): Multi-gate × timing 多軸層化 (Phase 1.5 第五試行、観察延長への逸脱)
v10.11 (2026-05-10): q_c_inherited 起点 within-cid 観察 (Phase 1.5 第六試行、v10.5 既知再観察)
v10.12 (2026-05-10〜現在): 条件適応型 atom 導入の単一勝負案 (Phase 1.5 第七試行)
   ↓ (現在 Step A 完了、Q-A1 重大ブロッカー警告中)
v10.13 以降: 字面に揺れながら反応するシステムの精緻化 prototype (Taka 整理 §1.9)
```

---

### 2. 各バージョンの主題と達成 (一文サマリ)

#### 2.1 v10.4 (2026-04-30): Integration 機構導入

**主題**: Layer 5 (cid 集団) 入口、Q/C 継承機構の最小実装

**達成**:
- 24 seeds 完走 (wall mean 2.99h)
- **Integration 13,550 件誕生** (be3 7,085 / open_triad 5,203 / closed_triad 0 / third_overlap 1,262)
- Layer A 物理層 frozen 維持 (labels / persistence 24/24 完全一致)
- v10.3 比 C 蓄積 +15%、C_max +31%、cognition 当選 +4.2%
- Integration が ghost cid から Q/C を 10,000/14,083 継承 → active member へ部分再分配 2,790/1,777

**新規概念**: Integration、be3 (両者 C-1)、open_triad、third_overlap

#### 2.2 v10.5 (2026-05-01): α/β 階層分離 (Layer 5 完成)

**主題**: Layer 5 完成、α/β 階層分離 + hub β + 機構 A/C

**達成**:
- 物理層 bit-identity 100% PASS、規律 M6 (1 cid → 1 β 会計) 違反 0
- α/β 階層成立、**hub β 出現 (最大 691 α 統合 / 20 cid)**
- Salience event 78k 件 (mass-weighted 観察)
- Leakage 0 件は v10.2 即時 ingestion path のバグ修正済み

**確立した機構** (v10.12 でも参照される最重要):
- **機構 A** (`v105_integration.py:1035`): cid が ghost 化時、その cid が β member なら β が **Q/C を 100% 継承**。α 側はメンバー除外と recorded 化のみ (Q/C 継承なし)
- **機構 C**: Recorded からの漏れ ε=1、active_to_recorded で β は永続化、death events 0 件
- **β event_type 5 種**: birth / alpha_added / beta_merged / q_c_inherited / active_to_recorded
- **α event_type 3 種**: birth / member_ghosted / active_to_recorded
- α は **可変サイズ** (2-8 cid、平均 2.63)、β は **常にペア** 結合 (member_alphas 数 = 2)

#### 2.3 v10.6 (2026-05-04): Atom alignment observer

**主題**: Atom (326 atom) と cid の alignment 観察、Phase 1.5 第一試行

**達成**:
- 26 atom 構造的特異性 (delta>1% × 9 + z=inf × 17 - 1 duplicate = 25 atom 確定)
- WLD.artless reserved label (留保扱い、集計除外)
- cid_atom_sim_matrix 構築 (各 atom × cid の sim 行列、後の v10.8 で top_k 100 抽出に活用)
- 7 atom 構造的盲点を別途記録 (B 群)
- per-event / per-pulse / step10 trajectory 解析で時間軸混在 caveat 確立

#### 2.4 v10.7 (2026-05-05): post-process オービス完成 (Phase 1.5 第二試行)

**主題**: 観察基盤 (オービス) の確立、source_event 5 種 + relation_path 5 種 + baseline 5 種

**達成**:
- 24 seeds 並列 main run **234.86 秒** (順次比 12 倍高速、multiprocessing.Pool 24)
- **5 source_event × 10 relation_path/baseline で 415,726 events、3,453,191 excess_change rows**
- Level 1 (co-occurrence) **93/111 finding**
- Level 2 (path-enriched) **49/58 finding**
- Level 3 (source-specific) **85/90 finding**
- **path 順位**: temporal_coactivation > Integration > familiarity > attention
- bit-identity 層 A 9/10 (summary は実行時間記録で除外)、層 B v10.6 出力 731 files 完全不変
- storage 428 MB (上限 6 GB の 7%)

**source_event 5 種**: pulse / ingestion / α_formation / β_formation / c_conversion (v10.12 でも継承)
**relation_path 5 種**: familiarity / attention_via_salience / integration_alpha / integration_beta / temporal_coactivation
**baseline 5 種**: unrelated / same_step_random / matched / same_integration_low_familiarity / high_familiarity_outside_integration_baseline (v10.7 §F、§G で確立)

#### 2.5 v10.8 (2026-05-06): atom_introduction_event 機構 (Phase 1.5 第三試行)

**主題**: Atom 単独持ち込み機構、25 atom × 100 cid × 24 seeds = 60,000 events

**達成**:
- post-process 計算的減算 (Q-1, C+1) で 60K events
- 24 seeds 並列 main run **325 秒**
- Level 1 (atom co-occurrence) **811/1,384 findings**
- Level 2 (atom path-enriched) **683/1,433 findings**
- Level 3 (atom source-specific) **36/78 findings**
- **Level 3.5 (introduced vs natural) 22/39 findings**
- **最大主結果**: Level 3.5 で 20/22 finding が **introduced < natural** (atom event は natural の半分の波及効果、差 4.38)
- familiarity 経路の atom 識別 effect_size 6.83、temporal_coactivation は atom 中立 effect_size 0.03
- bit-identity 層 A 15/15 PASS + 層 B v10.7 222 files 完全不変
- storage 737 MB (累計 12%)

**v10.8 標準** (以降 v10.9-v10.12 で baseline として参照):
- A1: Q -1 / C +1 (post-process 計算的減算)
- B1: top_k 100 cid (cid_atom_sim_matrix から sim 上位)
- C1: 案 α 均等分散発火 (atom_index × 10 step ずらし)

#### 2.6 v10.9 (2026-05-08): 4 種設計表 + 寄与候補感度評価 (Phase 1.5 第四試行)

**主題**: Atom 取り込み機構の精緻化、寄与候補感度評価 + bimodal 構造解析、選抜試験

**達成 (核心的発見 4 件)**:
1. **「強反応する cid は若い cid (age median 227)」**: bimodal 1,540 cells のうち genuine 918、H3_lifecycle 60.2% 支配 + 99% 方向一致 (effect_size 0.85)
2. **timing > cid_selection > QC_cost の感度階層**: timing abs_mean 0.141 / cid_selection 0.024 / QC_cost 0.005 で評価不能
3. **「Integration 外の高 familiarity cid (high_fam_out_integ)」が timing 感度 0.222 / std 0.079 で最強・最 robust**
4. **C2 (若い cid 発火) で pulse 活動 short 0.97 / medium 0.75 大効果量で活発化**

**4 種設計表 (v10.13 以降の素材)**:
- 表 1 sensitivity: 候補別 cohens_d (timing / cid_selection / QC_cost)
- 表 2 受信可能状態: cid age <= 560 + Integration 外 + 高 familiarity (top 25%) + n_core ≥ 4.67 (副)
- 表 3 ルーティング: high_fam_out PREFER
- 表 4 自然さ: C2 が natural に近づいた cells 47%

**留保事項 3 件**:
1. bimodal KDE fallback 100% (主結果信頼性は維持)
2. **QC_cost 評価不能** (post-process 計算的減算限界)
3. **high_fam_out_integ 構造未解明**

**Taka の問いへの最終回答**: 「**25 atom を若い cid (age <= 500) + Integration 外 + 高 familiarity に対して age=200 timing で投げる**」が v10.10 主題予定 (= 条件適応型 atom 導入の単一勝負案)。

#### 2.7 v10.10 (2026-05-09): Multi-gate × timing 多軸層化 (Phase 1.5 第五試行、観察延長への逸脱)

**主題変更**: 当初は「条件適応型 atom 導入の単一勝負案」(v10.9 設計表の統合適用) のはずが、Code A 母集団不足 (per atom × seed = 1.84) を契機に Multi-gate × timing 二次元観察設計に **転換** (Web Claude/Taka 判断、観察軸を増やす方向)

**達成**:
- 24 seeds × 28 conditions main run **103.67 秒**
- 9 種 gate × 3 timing (200/300/500) + v108_re = 28 conditions
- bit-identity 全層 PASS (層 B v107+v108+v109 = 867 files 完全不変)
- **3 つの主要観察**:
  1. gate 効果は mean_delta_C medium で abs_mean 0.053 と小 (v10.9 high_fam_out 0.222 が複合 gate / 母集団小化で減衰)
  2. timing 軸 (t200 vs t500) で全 gate が負方向 (-0.090 〜 -0.253、v10.9 Step F 仮説と逆)
  3. v110 vs v108_re は mean_n_pulses_in_window で abs_mean 0.928 大効果量

**追加層化解析 (Web Claude 第一弾 5 軸 + 第二弾 4 タスク + n_core 補足)**:
- Integration α/β 4 層化 / cid 寿命別 / 25 atom 個別 / window × n_core 交差 / seed 別ばらつき / Integration 形成タイミング (formation_relation) / 寿命 × n_core 交差
- **§3.4 反応 type 分業 (v10.12 でも必須参照)**:
  - **bin_2 (ペア、76%) は pulse 軸で大効果** (matched +4.295)
  - **bin_5+ (中 cluster、12%) は delta_C 軸で大効果** (high_fam_out -0.653)

**留保事項 14 件 (継承 3 + 新規 11)**:
- 留保 8: 長寿 cid (Q4) の timing_axis 方向反転寄与
- 留保 11: Integration 形成前と after_100plus の cohens_d 差の構造的解釈
- 留保 12: 「相関する 2 軸の交差効果」の構造的根拠
- 留保 14: no_alpha 群の v110_vs_v108re +0.133 の構造的位置づけ

**逸脱の教訓**:
- 観察延長への流れに転換した結果、「v10.9 で見えたルールが本物か幻か」が単一 metric では決まらず、観察状態 B (分岐) で終了
- 単一勝負案を実現できなかった

#### 2.8 v10.11 (2026-05-10): q_c_inherited 起点 within-cid 観察 (Phase 1.5 第六試行、v10.5 既知再観察に終わる)

**主題**: Integration 形成プロセス解析、q_c_inherited 前後の within-cid delta_C 比較

**達成**:
- 24 seeds main run **7.65 秒**
- 12 cells (n_core_bin × β 累積 c_inherited 分位) × 24 seeds で within-cid 前後比較
- 272,835 snapshots、13,055 (event, cid) pairs

**核心観察 (24 seeds)**:
- delta_C_within: 全 12 cells で正値 (+0.097〜+0.497)
- bin_2 × Q1 / bin_3_4 × Q4: 24 seeds 完全一致 (complete_consistent)
- delta_pulse_within: 全 cell ≈ 0

**整理仮説 (留保)**:
- C 値飽和仮説 (主題 §1.5) は本データで不支持 (Q1 と Q4 がほぼ同程度)
- 観察事実は **q_c_inherited は β member cid の C を継続的に増加させる ESDE 構造的機能** (v10.5 機構 A) の **直接観察**

**達成条件 §0.2 (1 条件抽出) は限定的に達成**: 「β member cid は v10.12 概念取り込み目的の入力対象から除外」← v10.5 機構 A の延長

**留保事項 4 件 (新規)**:
19. seed 0 と 24 seeds 観察パターン不一致
20. C 値飽和仮説不支持
21. **ESDE β 機能 (q_c_inherited で C 増加) の直接観察可能性** ← v10.12 で参照
22. delta_pulse_within ≈ 0

**最大の教訓 (規律 §35 #9 違反)**:
- 主題ドキュメント第一稿で「alpha_birth / beta_birth を新規 source_event 化」と書いたが、v10.7 既存実装で alpha_formation / beta_formation 既に source_event 化済 と Code A 事実確認で判明 → 第二稿で書き直し
- 観察対象 (q_c_inherited 前後) が v10.5 機構 A/C の自明な再観察に過ぎなかった
- **3 AI と Code A 全員が v10.5 §7.4-§7.10 を主題設計に反映しなかった構造的失敗**

→ v10.11 完了レポート §2 で「v10.12 では v10.10/v10.11 逸脱パターンを断ち切る必要」と明示。

#### 2.9 v10.12 (2026-05-10〜現在): 条件適応型 atom 導入の単一勝負案 (Phase 1.5 第七試行)

**主題**: v10.9 完了時点で Taka と Web Claude が GPT 修正方針のもと確定していた **「条件適応型 atom 導入による v10.8 標準を超える性能向上」** を、v10.10/v10.11 で得られた素材で更新して再開

**主題ドキュメントの版変遷**:
- 第一稿: 単一勝負案 (4 条件 AND)
- 第二稿: 第一稿同設計、Code A 認識確認待ち
- 第三稿: GPT 監査 + Taka 整理 §1.9 (字面反応システム) 反映、慎重トーン維持
- **第四稿 (現行)**: Step Z 結果 + Taka 判断「破綻ではなく前提変更」を反映、**2 trial 分割設計** + §5.6 規律チェックリスト (案 X)

**Step Z 事前調査 (Code A 実測 commit df04d0a、2026-05-10)**:
4 件の重大乖離検出:
1. Q-Z1 母集団崩壊: 4 条件 AND_all 24/24 seed で <10、per seed 3.9 (paired_d 算出不能)
2. Q-Z2 取り違え: Q3=2,485 vs Web Claude 想定 977 (実は Q2)
3. Q-Z6 cid pool 重なり: overlap_ratio_v112 = 0.958 (matched_pool 比較崩壊)
4. Q-Z5 v10.5 機構との重複: (b) 部分的に重なる (条件 1 は v10.11 既知)

**Code A Step Z 補完 (Taka 指摘で n_core 別層化漏れ発覚、commit df04d0a)**:
- 4 条件複合は構造的に bin_2/bin_3_4 を完全排除 (cond3=n_core≥5 が排他条件)
- v10.10 §3.4 反応 type 分業との致命的乖離 (4 条件複合は delta_C 軸狙いで pulse 系を完全排除)

**Taka 判断 (2026-05-10)**:
- 確認 1: 破綻ではなく前提変更
- 確認 2: 方向 A (2 trial 分割) 採用
- 確認 3: 案 X 規律チェックリスト採用

**第 4 版主題の中核 (現行)**:
- **trial-A**: bin_5+ × delta_C 系狙い (cond3 = n_core ≥ 5)、性能指標 1-A + 3-A
- **trial-B**: bin_2 × pulse 系狙い (cond3 = n_core == 2)、性能指標 2-B + 1-B 副次
- lifespan は Q3=2,485 → Q2=977 緩和 (cond2 緩和、母集団確保)
- bin 別比較で公平性確保 (v112_trial / v108_matched_pool_bin / v108_original_bin の 6 condition)
- §5.6 規律チェックリスト (案 X、お守り規律として運用)

**Step A 認識確認 (commit ddd595a、2026-05-10)**:
**Q-A1 重大ブロッカー警告**:
- trial-B (bin_2 × 4 条件) は per seed 0.2 / total 4 events で paired_d 算出不能
- 構造的根拠: cond4 (familiarity top 25%) が bin_2 で稀少 (12.5% しか該当)、Q2 緩和でも解消されない
- Code A 提案: trial-B のみ cond4 を top 50% 緩和 (Web Claude/Taka 判断要請)

**現在地 (2026-05-11 時点)**: Web Claude 新スレッドへの引き継ぎ中、Q-A1 解消後 Step B (環境チェック詳細) 進行待ち

---

### 3. 累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト

#### 3.1 累積規律 41 件 (v10.7-v10.11 確立、`09_audit_principles.md` §34)

##### 物理層・観察層の規律
1. **物理層 frozen** (v10.7): post-process は実 ledger 不変、read のみ
2. **神の手回避** (v10.7): 構造条件のみで判定、ハンドチューニング禁止
3. **Atom 326 絶対化禁止** (v10.6): 25 atom (構造的特異性) を継承、326 化なし
4. **因果断定回避** (v10.9 GPT B3): 「効いた」「効果的だった」を使わず、「観察された」「並列値より大きい」のような観察語に統一
5. **post-process 計算的減算** (v10.8): Q/C コストは post-process で計算ベース再現、実 ledger 不変

##### 観察設計の規律
6. **出口の固定** (v10.9): 主題完了レポートで成果物を事前定義
7. **構造語と直感語の併記** (v10.7): Taka 向け理解語と実装の構造語を分離記述
8. **寄与候補感度評価命名** (v10.9 GPT B3): 「原因」ではなく「寄与候補の感度評価」
9. **各変動条件で baseline 再計算** (v10.9 GPT B6): 条件比較時は baseline も条件別に再計算
10. **4 層階層化** (v10.9 GPT B5): Level 1 (機構動作) / Level 2 (条件差) / Level 3 (感度評価) / Level 3.5 (構造的説明候補整合)

##### 監査・運用の規律
11. **Code A 認識確認必須** (v10.7、再強化 v10.8): Web Claude 主題ドキュメント → Code A 認識確認 → Web Claude 即決事項返答 → Taka 承認 → 実装着手
12. **smoke 後止まって報告** (v10.6、Taka 指示): smoke 完了後 main run に勝手に進まず、Taka / Web Claude 承認待ち
13. **24 seeds 単一バッチ** (v10.6、Taka 指示): 8/8/8 等のバッチ分割禁止、1 コマンド単一バッチ
14. **資料を作ったら push までセット** (Taka 指示): 報告書・CSV 生成時は同一ターン内で commit + push
15. **bit-identity 3 層検証** (v10.7 確立、v10.8-v10.12 継承): 層 A 同 seed 2 回再現 + 層 B 既存出力不変 + 層 C パス制限

##### 観察記述の規律
16. **観察と判定の区別** (v10.10 第一弾): 報告書は観察記述まで、判定は Web Claude 判定書で実施
17. **events 数 / n_b 不足の併記** (v10.10): cohens_d 計算で n < 3 のセルは `n_b_insufficient` 列で明示
18. **既知事実との重複確認** (v10.11 違反契機): 主題が v10.5 機構等の自明な再観察でないか事前確認

##### 物理的環境の規律
19. **NVIDIA driver upgrade 原則 NG** (memory): 過去事故、TRT-LLM 等の driver 要件不足時はソフト側後退
20. **物理層 frozen の強制** (v10.7): 出力先パス制限 (v107/, v108/, ... 配下のみ書き込み許可)

##### v10.10/v10.11 で確立された規律
21-30. (累積、各 commit log で詳細)

##### v10.10/v10.11 で再明文化された規律 (重要 5 件)

37. **n_core 別層化解析必須** (v10.10): n_core_bin (bin_2 / bin_3_4 / bin_5+) で層化、平均で潰れる構造を救出
38. **formation_relation を観察軸として含む** (v10.10): Integration 形成と event timestamp の関係を主軸 or 条件軸として含める
39. **完全マージ版文書を出力** (v10.10): 主題ドキュメント / 報告書は完全版で出力、後追い追加禁止
40. **観察軸を増やす方が見えるものが増える** (v10.10、Taka 整理): ただし §0.3 打ち切り条件と併用
41. **観察状態判定枠を超えた整理** (v10.10): 必要に応じて A/B/C 判定枠を超えた整理を採用可

#### 3.2 §35 運営メタ規律 10 項目 (v10.11 で確立)

GPT 第三回監査提示 + Web Claude 自己反省 (v10.11 違反契機):

1. **オープン調査とクローズ調査を固定方針にしない**
2. **追加調査を開く時は理由を明示する** (前提崩れ / 観察軸不足 / 次フェーズ素材 / 平均化誤認回避)
3. **平均で潰れる構造は必ず層化を検討する** ← n_core が典型
4. **閾値は真理ではなく運用上の仮置きとして扱う**
5. **整理語は観察事実と分ける**
6. **主題終了条件は置くが、その前提が実測で崩れた場合は再開を許す**
7. **監査や整理は、閉じる妥当性だけでなく、開く妥当性も評価する**
8. **最終的な開閉判断は、現場感を持つ人間 (Taka) 側に残す**
9. **Web Claude は主題ドキュメント着手前に関連バージョンの上位資料を読む** (お守り規律)
10. **「観察できる軸が見えた」を駆動要因にしない** (v10.10 違反契機、Taka 指摘)

#### 3.3 §5.6 規律チェックリスト (案 X、v10.12 第 4 版で導入、お守り規律)

主題設計時に Web Claude が累積規律 41 件 + §35 メタ規律 10 項目を 1 つずつ確認するチェックリスト。Taka 認識「Claude の担当が変わったりすれば結局同じ」(2026-05-10) の限界を明示しつつ、規律違反は予防ではなく **発見と修正のサイクル** で運用。

実装は v112_phase_design.md 第 4 版 §5.6 参照。

---

### 4. 留保事項一覧 (v10.9-v10.12 累積、計 22 件)

#### 4.1 v10.9 留保 (3 件)

1. bimodal KDE fallback 100% (主結果信頼性は維持)
2. **QC_cost 評価不能** (post-process 計算的減算限界)
3. **high_fam_out_integ 構造未解明**

#### 4.2 v10.10 第一弾留保 (4 件追加、計 7 件)

4. only_alpha / only_beta 不在 (構造的事実)
5. 長寿 cid (Q4) の timing_axis 方向反転寄与
6. atom category 別効果差 (BOD +0.399 vs WLD +0.009、40 倍差) の構造的解釈
7. gate_effect の 24 seeds 方向不一致 (tied 多発)

#### 4.3 v10.10 第二弾留保 (4 件追加、計 11 件)

8. Q1 timing 軸方向反転と寿命の関係
9. β alpha_added の事象数と n_core_bin 別感度
10. 寿命 × n_core 交差の独立寄与
11. **Integration 形成前と after_100plus の cohens_d 差の構造的解釈** ← v10.11 で扱うも未解明継続

#### 4.4 v10.10 完了レポート留保 (3 件追加、計 14 件)

12. **「相関する 2 軸の交差効果」の構造的根拠**
13. n_core 別層化での観察軸独立性
14. **no_alpha 群の v110_vs_v108re +0.133 の構造的位置づけ**

#### 4.5 v10.11 留保 (4 件追加、計 18 件)

15-18. (n_core 関連の追加層化、Step F 主題核心関連)

#### 4.6 v10.11 完了レポート留保 (4 件追加、計 22 件)

19. seed 0 と 24 seeds の観察パターン不一致
20. C 値飽和仮説の本データでの不支持
21. **ESDE β 機能 (q_c_inherited で C 増加) の直接観察可能性** ← v10.12 条件 1 (β member 除外) と関連
22. delta_pulse_within ≈ 0 (event 起点の質の違い)

---

### 5. ESDE 内部構造の主要概念 (Phase 1.5 で確立)

#### 5.1 4 層アーキテクチャ (v10.0-v10.3 確立)

- 物理層 (Layer 1): pulse / ingestion / labels / persistence
- 存在層 (Layer 2): cid (cognitive identifier)
- 認知層 (Layer 3): Q (認知資源)、cognition decision
- 意識層 (Layer 4): C (意識資源)、consciousness decision

#### 5.2 Layer 5 (cid 集団、v10.4-v10.5 確立)

- α-Integration: cid 集合 (誕生時 2-8 cid、平均 6.8、その後固定)
- β-Integration: α-Integration を構成要素とする上位構造、cid を重ねていく動的構造
- 結合則 (β): α 同士が cid 共有 2 個以上で merge
- 役割分離: α = 観察、β = 会計 (Q/C 継承単位)
- **最大規模**: 1 つの β が 715 α を吸収 (1 cid 34.5 α)

#### 5.3 v10.5 機構 A/C (v10.12 で参照)

- **機構 A**: cid が ghost 化時、その cid が β member なら β が **Q/C を 100% 継承**
- **機構 C**: Recorded からの漏れ ε=1、active_to_recorded で β は永続化、death events 0 件

#### 5.4 source_event カテゴリ (v10.7 確立)

| カテゴリ | 内容 | seed あたり events 数 (24 seeds 平均) |
|---|---|---:|
| pulse | pulse_log 由来 | 12,530 |
| ingestion | ingestion_events_seed*.csv | 155 |
| **alpha_formation** | event_type='birth' (alpha_lifecycle_log) | 424 |
| **beta_formation** | event_type='birth' (beta_lifecycle_log) | 239 |
| c_conversion | balance_decisions の consciousness | 155 |
| **atom_introduction_event** (v10.8 で追加、第 6 種) | post-process 計算的減算 | 2,500 |

#### 5.5 alpha/beta_lifecycle_log の event_type (Code A 事実確認 2026-05-10)

##### α event_type (3 種)

| event_type | 24 seeds total | 内容 |
|---|---:|---|
| birth | 13,881 | 構成 cid 集合の誕生 |
| **member_ghosted** | 17,093 | 構成 cid の ghost 化、α の解体プロセス |
| active_to_recorded | 2,089 | α の recorded 永続化 |

##### β event_type (5 種)

| event_type | 24 seeds total | 内容 |
|---|---:|---|
| birth | 6,476 | β 誕生時、ペアでの誕生 |
| **alpha_added** | 7,405 | 新たな α が β に取り込まれる成長 |
| **beta_merged** | 4,467 | β 同士の merge による成長 |
| **q_c_inherited** | 2,247 | β から member cid への Q/C 継承 (機構 A) |
| active_to_recorded | 443 | β の recorded 永続化 |

#### 5.6 Atom 326 + Axis + Operator + Lexicon v2 (Phase 8 強い意味系)

**最新仕様** (`docs/ESDE language/esde_cell_architecture.md` v2.3、2026-02-08):

- **Atom 326**: 326 atoms、163 対称ペア、16 categories (`language/atoms/esde_dictionary.json`)
- **Axis**: 8 canonical axes × 5-point scale (`cognitive / ethical / social / creative / ontological / temporal / spatial / physical`、Glossary v5.7.0 準拠)
- **Operator**: 15 種実装 (`language/sensor/constants.py`、`× ▷ → ⊕ | ◯ ↺ 〈〉 ≡ ≃ ¬ ⇒ ⇒+ -|>`)
- **Lexicon v2**: 327 個の JSON ファイル (`language/lexicon/data/lexicon_entries/`)、24 prefix カテゴリ
- **Synapse v3.0**: 11,557 synsets、22,285 edges (WordNet ↔ Atom mapping)
- **Phase 8 sensor**: `language/sensor/esde_sensor_v2_modular.py` の `ESDESensorV2.analyze(text)` で 文 → atom 変換 (現状 import エラーで動作要修正)
- **Molecule format**: `{"active_atoms": [{"atom": "EMO.love", "axis": "ethical", "level": 3}], "formula": "EMO.love"}`

#### 5.7 v10.6 で確立された v10.7 以降で使われる atom 集合

**25 atom (構造的特異性、WLD.artless 留保で 24 集計)**: BOD.ear / COG.learn / COM.silence / EXS.being / EXS.nonbeing / FND.timeless / FND.transformation / PER.feel / PER.fragrance / PER.hear / PER.see / PER.smell / PER.sound / PER.soundless / PER.taste / PRP.bright / PRP.deep / PRP.sharp / SOC.city / SOC.nation / SOC.public / TIM.appear / **WLD.artless** (留保) / WLD.culture / WLD.technique

---

### 6. v10.10/v10.11 逸脱パターンと再発防止策

#### 6.1 v10.10 逸脱パターン

**パターン**: Code A 母集団不足を契機に、観察軸を増やす方向に主題転換 (Multi-gate × timing 二次元観察)

**結果**:
- 観察状態 B (分岐) で終了
- 「v10.9 で見えたルールが本物か幻か」が単一 metric では決まらず
- 単一勝負案を実現できなかった

#### 6.2 v10.11 逸脱パターン

**パターン**: 主題が v10.5 機構 A/C の自明な再観察に終わる (3 AI と Code A 全員が v10.5 §7.4-§7.10 を未参照)

**結果**:
- 達成条件 §0.2 (1 条件抽出) は限定的に達成、ただし「β member 除外」は v10.5 機構 A の延長
- 主題ドキュメント第一稿で「alpha_birth / beta_birth を新規 source_event 化」を提案 → v10.7 既存実装で source_event 化済 と Code A 事実確認で判明 → 第二稿で書き直し

#### 6.3 v10.12 で実装された再発防止策

| 再発防止策 | 実装場所 |
|---|---|
| §1 主題ドキュメントで関連過去レポートの参照証明 (節番号 + 要約 + 接続) | v112_phase_design.md §1 |
| 「単一勝負案」を主題タイトルに明記 | v112_phase_design.md §4.1 |
| 母集団不足時の対応を **4 項目固定** (条件をいじりながら観察する抜け道を塞ぐ) | v112_phase_design.md §13.2 |
| 「観察できる軸が見えた」を駆動要因にしない (規律 §35 #10) | v112_phase_design.md §4.4 |
| Step Z 事前調査フェーズ追加 (実装前に Web Claude 想定と実環境の乖離を検出) | v112_implementation_brief.md 第 2 版 §1 |
| Code A 規律遵守自己検証 | v112_code_recognition_check.md §3 |
| §5.6 規律チェックリスト (案 X、お守り規律) | v112_phase_design.md 第 4 版 §5.6 |

---

### 7. 実装ファイル所在マップ

#### 7.1 各バージョンの主要 .py モジュール

```
v104: v104_be3_postprocess.py / v104_integration.py / v104_observation_target.py
v105: v105_integration.py (機構 A/C 本体、:1035 で「β 側: Q/C 100% 継承」)
      v105_animate_*.py (3 layer / compare / grid / integration)
v106: v106_post_process.py (atom_alignment_observer)
      v106_atom_match_classification.py (26 atom 構造的特異性)
      v106_step10_baseline.py / v106_event_trajectory.py / v106_pulse_trajectory.py
v107: v107_event_aggregator.py / v107_path_analyzer.py / v107_baseline_constructor.py
      v107_avalanche_monitor.py / v107_post_process.py / v107_cross_seed_analyzer.py
v108: v108_atom_event_generator.py (atom_introduction_event 機構)
      v108_baseline_recalculator.py (各変動条件で baseline 再計算)
      v108_global_activation_correction.py / v108_subsidiary_observations.py
      v108_post_process.py (orchestrator)
v109: v109_atom_event_generator.py / v109_baseline_recalculator.py
      v109_bimodal_analyzer.py / v109_sensitivity_evaluator.py
      v109_design_table_compiler.py / v109_post_process.py
v110: v110_atom_event_generator.py / v110_baseline_recalculator.py
      v110_environment_check.py (build_alpha_beta_intervals)
      v110_multi_axis_stratified_analyzer.py / v110_n_core_stratified_analyzer.py
      v110_round2_analyzer.py / v110_post_process.py
      v110_design_table_compiler.py / v110_sensitivity_evaluator.py
v111: v111_q_c_inherited_observer.py / v111_response_profile_compiler.py
v112: v112_step_z_environment_check.py (Step Z 主、母集団実測)
      v112_step_z_n_core_addendum.py (Step Z 補完、Taka 指摘対応)
```

#### 7.2 各バージョンの主要レポート

```
v104: v104_main_run_report.md
v105: v105_main_run_report.md / v105_main_v2_run_report.md
v106: v106_main_run_report.md (および 7 件の専用レポート)
v107: v107_main_run_report.md / v107_implementation_brief.md / v107_code_recognition_check.md
v108: v108_main_run_report.md / v108_implementation_brief.md / v108_code_recognition_check.md
v109: v109_main_run_report.md / v109_implementation_brief.md / v109_phase_design.md
v110: v110_main_run_report.md / v110_phase_design.md / 第一弾 + 第二弾 layered analysis
v111: v111_main_run_report.md / v111_phase_design.md / v111_code_recognition_check_v2.md
v112: v112_phase_design.md (第 4 版、現行) / v112_implementation_brief.md (第 3 版、現行)
      v112_step_z_report.md / v112_code_recognition_check.md (Step A 認識確認)
```

#### 7.3 出力データ所在 (developmental/v{V}/outputs/main/)

各バージョンの main 出力は `developmental/v{V}/outputs/main/` 配下:
- v107: 222 files
- v108: 368 files
- v109: 277 files
- v110: 213 files
- v111: 56 files (q_c_inherited_*)
- v112: 出力 7 files (Step Z のみ、main run 未実施)

bit-identity 層 B 不変対象: v107 + v108 + v109 + v110 + v111 = 約 1,136 files

---

### 8. v10.12 現状 (2026-05-11)

#### 8.1 完了した Step

- **Step Z 事前調査** (commit df04d0a、2026-05-10): 4 件の重大乖離検出
- **Step Z 補完 n_core 層化** (Taka 指摘、commit df04d0a): cond3 が ESDE 88% を排除する排他条件と判明
- **Step A 認識確認** (commit ddd595a、2026-05-10): Q-A1 重大ブロッカー警告

#### 8.2 Q-A1 重大ブロッカーの内容

trial-B (bin_2 × 4 条件) は構造的に paired_d 算出不能:
- per seed 0.2 / total 4 events (Q3 維持時)
- 主因: cond4 (familiarity top 25%) が bin_2 で稀少 (12.5%)
- Q2 緩和でも per seed 0.4 程度で解消されない
- Code A 提案: trial-B のみ cond4 を top 50% 緩和 (Web Claude/Taka 判断要請)

#### 8.3 Web Claude/Taka 判断対象 (DC-A1〜DC-A5)

| DC | 内容 | Code A 提案 |
|---|---|---|
| DC-A1 | trial-B cond4 緩和 (Q-A1 対応) | top 50% 緩和 |
| DC-A2 | top_quartile_threshold | per-seed (std/global=0.61) |
| DC-A3 | v108_original 流用 vs 再計算 | 流用 (層 B 不変) |
| DC-A4 | bootstrap CI n_iter | 1000 (主軸) / 500 (副次) |
| DC-A5 | target_step / natural baseline 詳細 | Web Claude 確認要 |

#### 8.4 次のアクション

1. 新 Web Claude が `v112_response_to_code_a.md` で DC-A1〜DC-A5 + Q-A7 即決事項を返答
2. Taka 承認
3. Code A Step B (環境チェック詳細 + Q2/top_quartile 実測 + trial-B 緩和案ありの場合の母集団再実測)
4. Code A Step C-L (実装 → smoke → main run → cross-seed 集計 → 完了報告)

#### 8.5 計算量・ストレージ

- main run 推定 1-2 分 (24 並列、6 conditions × 6 baselines = 36 baseline)
- storage 累計 v107-v112 約 2.0-2.5 GB / 上限 6 GB (33-42%)

---

### 9. 関連資料への索引

#### 9.1 主題ドキュメント (v10.4 以降)

```
developmental/v107/v107_implementation_brief.md
developmental/v108/v108_phase_design.md (推定、未確認)
developmental/v109/v109_phase_design.md
developmental/v110/v110_phase_design.md
developmental/v111/v111_phase_design.md
developmental/v112/v112_phase_design.md (第 4 版、現行) ← 本主題
```

#### 9.2 上位資料

```
docs/ai_summaries/
├── 06_developmental_summary.md (v10.0-v10.3、2026-04-28 凍結)
├── 06b_developmental_phase15_summary.md (本資料、v10.4-v10.12)
├── 07_concept_core.md
├── 08_esde_system_structure.md (Layer 5 を含む)
└── 09_audit_principles.md (規律累積)

docs/
├── ESDE_Developmental_Report.md (詳細版、801 行)
├── ESDE language/
│   ├── esde_cell_architecture.md (v2.3、2026-02-08、最新階層)
│   ├── ESDE_Glossary.md (v5.7.0、2026-02-11、用語集)
│   └── ESDE_Module_Reference_Lexicon_v2.md (Lexicon v2 Pipeline)
└── 概念理解.md
```

#### 9.3 運用マニュアル

```
esde_3ai_operations_manual.md (3 AI 共通運用、参照証明形式 §2.2)
```

#### 9.4 v10.5 機構実装本体

```
developmental/v105/v105_integration.py (β 側 Q/C 100% 継承、機構 A 本体)
```

#### 9.5 v10.7 オービス本体

```
developmental/v107/v107_event_aggregator.py (5 source_event 集約)
developmental/v107/v107_path_analyzer.py (5 relation_path 構築)
developmental/v107/v107_baseline_constructor.py (5+1 baseline 構築 + delta + excess)
```

#### 9.6 v10.8 atom_introduction_event 本体

```
developmental/v108/v108_atom_event_generator.py (25 atom × 100 cid × 24 seeds)
```

#### 9.7 v10.9 4 種設計表 + 寄与候補感度評価本体

```
developmental/v109/v109_design_table_compiler.py
developmental/v109/v109_sensitivity_evaluator.py
developmental/v109/v109_bimodal_analyzer.py
```

#### 9.8 v10.10 Multi-gate × timing + 多軸層化本体

```
developmental/v110/v110_multi_axis_stratified_analyzer.py
developmental/v110/v110_n_core_stratified_analyzer.py
developmental/v110/v110_round2_analyzer.py
```

#### 9.9 v10.11 q_c_inherited within-cid observer 本体

```
developmental/v111/v111_q_c_inherited_observer.py
developmental/v111/v111_response_profile_compiler.py
```

#### 9.10 v10.12 Step Z 本体

```
developmental/v112/v112_step_z_environment_check.py (Q-Z1-Q-Z7 実測)
developmental/v112/v112_step_z_n_core_addendum.py (n_core 別補完、Taka 指摘対応)
```

---

### 10. 新 Web Claude スレッドへの引き継ぎ重要事項

#### 10.1 v10.12 主題の本質 (Taka 整理 §1.9 参照)

**「会話への接続」ではなく「字面に揺れながら反応するシステム = ESDE Atom スレッド = 連結基盤の第一スレッドの精緻化」**

LLM が持たない唯一無二の強み (字面に対する揺れる反応) を確立するフェーズ。意味理解 / 出力機構 / 双方向性は v10.12 では扱わない。

#### 10.2 Web Claude が陥りやすい落とし穴 (v10.10/v10.11 教訓)

1. **観察軸を増やす方向への転換**: Code A 母集団不足を契機に、Multi-gate 化や within-cid design に転換しないこと
2. **v10.5 機構の自明な再観察**: 主題が v10.5 §7.4-§7.10 既知事実の延長になっていないか事前確認
3. **v10.10 §3.4 反応 type 分業の無視**: bin_2 = pulse / bin_5+ = delta_C の分業を主題設計時に反映
4. **規律 §35 #9 違反**: 主題着手前に v10.5 機構実装 + v10.10 §3.4 を読む
5. **「Web Claude の想定はだいたい結構ズレる」(Taka 指摘)**: Step Z 事前調査で前提を実測、設計判断は Code A 実測後

#### 10.3 即決確認すべき項目 (v10.12 進行のため)

新 Web Claude は以下を確認してから次のアクションへ:

1. v112_phase_design.md 第 4 版を読む
2. v112_implementation_brief.md 第 3 版を読む
3. v112_step_z_report.md (Step Z 結果) を読む
4. v112_code_recognition_check.md (Step A、Code A 認識確認) を読む
5. 上記 4 つを踏まえ、`v112_response_to_code_a.md` で DC-A1〜DC-A5 + Q-A1 重大ブロッカー対応 + Q-A7 を返答
6. Taka 承認後、Code A Step B 進行

---

### 11. 一文サマリ (再掲、構造化版)

ESDE Phase 1.5 (v10.4-v10.12、2026-04-30〜現在) は単 cid 系から cid 集団 + Atom 取り込み機構への拡張段階、v10.4-v10.5 で Layer 5 (α/β-Integration、機構 A 「β に Q/C 100% 継承」+ 機構 C 「Recorded ε=1」) 確立、v10.6 で 25 atom 構造的特異性、v10.7 で post-process オービス完成 (5 source × 10 path × 415K events / 3.45M excess)、v10.8 で atom_introduction_event 機構 (25 atom × 60K events) + Level 3.5 「introduced は natural の半分」発見、v10.9 で 4 種設計表完成 (timing > cid > QC 感度階層、high_fam_out 0.222 最強、age=200 で若い cid 強反応) + Phase 1.5 第四試行 (選抜試験)、v10.10 で Multi-gate × timing 多軸層化 + n_core 別層化で「pulse 系は bin_2 / delta_C 系は bin_5+」反応 type 分業発見 (ただし観察延長への逸脱、v10.10 §3.4 が以降必須参照)、v10.11 で q_c_inherited 起点 within-cid 観察が v10.5 機構 A の自明な再観察に終わる (規律 §35 #9 違反、3 AI 全員が v10.5 §7 未参照)、v10.12 で「条件適応型 atom 導入の単一勝負案」(v10.10 でやるべきだった主題) を 2 trial 分割設計 (trial-A bin_5+ × delta_C / trial-B bin_2 × pulse) で再開、第 4 版主題 + Step Z 事前調査 + §5.6 規律チェックリスト (案 X) で前提を実測ベースに修正、Step A 認識確認で Q-A1 重大ブロッカー (trial-B 母集団 per seed 0.2、cond4 が bin_2 で稀少という構造的問題) を警告、Web Claude/Taka 判断待ち、累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト確立、留保事項 22 件累積、bit-identity 全層 PASS 維持 (v107-v111 約 1,136 files 不変)、storage 累計 1.52 GB (上限 6 GB の 25%、v10.12 後も 50% 余裕)、Taka 整理 §1.9 (2026-05-10) で「v10.12 は会話への接続ではなく字面に揺れながら反応するシステム = ESDE Atom スレッド = 連結基盤の第一スレッドの精緻化」と本主題の位置づけ確定、新 Web Claude スレッドはまず v112_phase_design.md 第 4 版 + v112_implementation_brief.md 第 3 版 + v112_step_z_report.md + v112_code_recognition_check.md を読み、`v112_response_to_code_a.md` で DC-A1〜DC-A5 + Q-A1 対応を返答することで進行再開可能。

---

*以上、Code A による Phase 1.5 (v10.4-v10.12) 状況引き継ぎ資料。新 Web Claude スレッドはこれを context 0 件目で読むこと。次の更新は v10.12 主題完了時。*

---

## Part C（v10.13a + Unified v1100/v1101 移行） — 06c Developmental v10.13.a + Unified v1100/v1101 Summary

*作成*: 2026-05-17、Code A (実装担当、新 Web Claude スレッド向け状況引き継ぎ)
*対象*: ESDE Developmental v10.13.a (Phase 1.5 続編) + Unified Phase v11.0.0 / v11.0.1 (Language ↔ Genesis 接続 + Atom 隆盛観察)
*親資料*: `06b_developmental_phase15_summary.md` (v10.4-v10.12、2026-05-11 で凍結、v10.12 Step A 完了時点)
*用途*: 新 Web Claude スレッド初見時に v10.13.a + Unified Phase 全容を把握するための網羅的引き継ぎ。本書を読めば v10.13.a 主題 + v11.0.0 Language 連携第一歩 + v11.0.1 「Atom 的隆盛の統計的観察」(現主題) の現在地が分かる。

---

### 0. 一文サマリ

ESDE は v10.12 (Phase 1.5 第七試行「Atom 取り込み prototype 受容 cid 再厳格化」、Step K 完了 2026-05-11) の後 v10.13.a (5 phase Map analyzer + null phase analyzer + long phase compute、2026-05-12 完了) を経て、**Unified Phase** へ移行: v11.0.0 (v1100、2026-05-12) で **Language ↔ Genesis 接続** の事前調査主題を扱い 6 候補 (UBAF / Synapse WSD with cid injection / Phase 10 Cell / 5 phase × Projection / Synapse 評価層化 / null cell ↔ base 優位照合) を事前検証 + 候補 6 を実装 (Berlin sentences 79 targets で R@3 base 優位 0 / R@1 base 優位 18、留保 #33 集計単位による方向反転と同型構造、Language base 優位 atom {SOC.official, PRP.part} 2 atoms と Genesis Map 5 null cell atom 20 atoms の重なり 0 / Jaccard 0 で両系の「文脈非依存性」は独立に異なる atom を捕捉)、Web Claude Phase Result (Step K) は未完成のまま v1100 残課題 A/B/C (Synapse 評価層化 / Phase 8+9 Cell ↔ Integration α/β 同型性検証 / 候補 6 大規模化) は Taka 判断で **凍結**、v11.0.1 (v1101、2026-05-12 〜 2026-05-17) で Taka 3 日長考の結論 **「Atom 的隆盛の統計的観察」** が現主題、観察 1「一点を捉える」(中心 cid n_pulses_short 最大 × 2 条件 = 48 中心 + ランダム 240 比較対照 + 4 解像度 trajectory 374,072 行) + 観察 2「取り込み点中心の波及」(v10.12 受容 cid pool 420 由来 10,500 atom_introduction_events × Δt±100 step 21 点 = 220,500 行) + 観察 3「補助平均統計 3 単位」(CID/Integration/ESDE) を Code A Step A-H で完了 (2026-05-17、commit 8 件、出力 25 ファイル 7 MB、bit-identity 3 層全 PASS)、**核心発見** = 観察単位による dominant atom の構造的反転 (CID-static `CHG.begin` / β `FND.logic` / α `TIM.moment` / ESDE event `WLD.artless+PER.sound` / step10 `PER.sound` / window `TIM.moment` の 5 atom 分裂、Taka「平均化の罠」絶対格言 #4 の生きた実例、v10.13.a 留保 #33 の Atom レベル一般化)、観察 2 副発見 = 25 取り込み atom 中 4 atom のみ中心 cid 支配可 (PER.sound peak 84.8% at Δt=+20) + 周辺 cid 60% を PER.sound + WLD.artless が常時占有 + atom entropy Δt 方向単調減少 (取り込み後集中化)、観察 1 副発見 = v108_standard 中心 cid dominant が WLD.artless で 24/21 seeds 一致 + window 解像度の一点特徴、Step F グラフ HTML 単一 954 KB ダッシュボード化 (Plotly + CDN、v105 pattern 踏襲)、Step G で deterministic + v10.6/v10.8/v10.12 main outputs 1,306 ファイル frozen 完全保証、新規留保 #41 (Integration member_cids 個別 cid id list は v10.x outputs に persistence されていない、段階 2 で cid state ledger 再生対応) + #42 (観察単位反転、Web Claude Phase Result 解釈統合領域)、Code A 主題担当範囲完了、**新 Web Claude Phase Result (Step J)** + 任意 Step I (段階 2) + Taka 主題評価判断を待つ、絶対格言 15 件全項目遵守、累計 Code A 認識確認連続 10 段階継続中。

---

### 1. v10.13.a (Phase 1.5 第八試行、Map Analyzer 主題)

#### 1.1 主題

v10.12 で「Atom 取り込み prototype 受容 cid 再厳格化」(受容 cid pool 420 / events 10,500 / paired_d / sign_test / bootstrap CI) が完了し留保 #27-#33 を formal 化、v10.13.a は **5 phase Map analyzer + null phase analyzer + long phase compute** を扱う。

5 phase 定義 (v113a_maps_analyzer.py):
```
Phase 1: pre-atom_intro (timestamp < target_step)
Phase 2: atom_intro (timestamp == target_step)
Phase 3: post-atom_intro short (target_step < timestamp ≤ target_step + 50)
Phase 4: post-atom_intro medium (target_step + 50 < timestamp ≤ target_step + 200)
Phase 5: post-atom_intro long (timestamp > target_step + 200)
```

#### 1.2 主要成果 (`developmental/v113a/`)

| 出力 | 内容 |
|---|---|
| Map 1 phase × ncore | per-seed n_core × 5 phase の発火密度 |
| Map 2 phase × path | per-seed path × 5 phase (integration_α/β を relation_path として扱う) |
| Map 3 phase × formation | per-seed formation_relation × 5 phase |
| Map 4 phase × event | per-seed atom event × 5 phase |
| Map 5 null phase per cell | **20 unique atoms** が null absorption (path 経路を経ない波及) 36 cells で出現 (TARGET_ATOMS 25 中) |

#### 1.3 v10.13.a 留保 (継承)

留保 #33 「集計単位による方向反転」: smoke seed 0 と main 24 seeds で 4/7 metric (path_excess 4 種全て) cohens_d 符号反転 — **集計単位を変えると結果の方向が変わる**。本主題 v1101 で **Atom レベルに一般化** (観察単位による dominant atom 反転)。

---

### 2. Unified Phase 移行 (v11.0.0 = v1100、Language ↔ Genesis 接続準備)

#### 2.1 主題: Language ↔ Genesis 接続事前調査

v10.13.a 完了後、ESDE は Genesis 系 (v10.x) と Language 系 (Atom/Synapse/Phase 7-10、2026-03 凍結) を接続する **Unified Phase** に移行。v1100 はその第一歩として「両系の接続準備」を扱う。

#### 2.2 6 候補事前検証 (Web Claude 主題ドキュメント + Code A Step A 事前齟齬指摘)

| 候補 | 内容 | Code A 判定 | v1100 内実装 |
|---|---|---|---|
| ~~1~~ | UBAF 拡張 (削除済、UBAF prototype 凍結) | — | — |
| 2 | Synapse WSD に cid 状態注入 | ✗ v1100 範囲外 (大規模) | v1101 以降 |
| 3 | Phase 10 Cell | ✗ 概念再定義必要 (**新齟齬 #36**: Phase 10 Cell ≠ esde_cell_architecture.md の Phase 8+9 Cell) | v1101 以降 (再定義後) |
| 4 | 5 phase × Projection | △ 簡略化版可、本来意図要設計 | v1101 以降 |
| 5 | Synapse 評価層化 | ✓ 実装可能 (簡略化版) | v1100 / v1101 |
| **6** | **null cell ↔ base 優位照合** | **✓ 実装完了** | **v1100 で実装** |

#### 2.3 候補 6 実装結果 (R@3 / R@1 二段階分析)

| metric | base | B | C | BC |
|---|---:|---:|---:|---:|
| **R@1** | **0.9630** | 0.7778 | 0.7778 | 0.7778 |
| R@3 | 0.9630 | 0.9630 | 0.9630 | 0.9630 |

- **R@3 ベース**: base 優位 token = 0 (4 mode hit pattern 完全同一)
- **R@1 ベース**: base 優位 token = 18 ("capital" 13 回 + "area" 等、base top-1 が `SOC.official` で B/C/BC は `SOC.city` / `SPC.place`)
- Language base 優位 atom 集合 {SOC.official, PRP.part} 2 atoms vs Genesis Map 5 null cell atom 20 atoms の **重なり 0 / Jaccard 0**
- **観察事実**: 両系の「文脈非依存性」は **独立に異なる atom を捕捉** (留保 #34 candidate「両系構造的同型性」は棄却方向、ただし小サンプル限界で確定棄却ではない)

#### 2.4 v1100 新規齟齬 #35-#37 candidate (Code A 認識確認発見)

| id | 内容 |
|---|---|
| #35 | Web Claude 親資料 `esde_language_reference_v1.md` が repo 不在 (絶対格言 #7 運用課題) |
| #36 candidate | **Phase 10 Cell ≠ esde_cell_architecture.md の Phase 8+9 Cell** (Web Claude 認識ミス連続 6 件目)、候補 3 を v1101 で扱う場合は概念再定義必須 |
| #37 candidate | Language 評価規模 79 targets は小サンプル限界、留保 #34 candidate の棄却は確定ではない |

#### 2.5 v1100 状態 (重要)

- Code A Step A-J 完了 (`unified/v1100/v1100_step_a_recognition.md` + `v1100_observation.md`)
- **Web Claude Phase Result (Step K) は未作成** ← 重要、未完了のまま v1101 が並行進行
- Code A 提案 v1101 候補 A/B/C (Synapse 層化 / Phase 8+9 Cell ↔ Integration α/β 同型性 / 候補 6 大規模化) → **Taka 判断で凍結** (本 v1101 主題優先のため、v11.0.1.a / v11.0.2 で扱う可能性残す)

---

### 3. Unified Phase 現主題 (v11.0.1 = v1101、Atom 的隆盛の統計的観察)

#### 3.1 Taka 3 日長考の結論 + 2026-05-16 具体化

v1100 終了時点で Code A が v1101 候補 A/B/C を提案したが、Taka が **3 日長考** (2026-05-12〜) の結果、3 案より優先で **「Atom 的隆盛の統計的観察」** を v1101 主題とすると決定。Web Claude が当初 v1102 として主題ドキュメントを作成 → Taka 番号修正指摘 (2026-05-16) で v1101 に確定。

##### 3.1.1 Taka 整理 (主題ドキュメント §5 原文保存、絶対格言 #14)

行き詰まりの自己分析:
> 取り込むといって取り込んだからどうなる? に答えがない。

濃度という捉え方:
> Atom のような状態は濃度のようなもので確定的ではない。CID 単位でいうならば、Atom らしきものがどのように揺れているかを捉えることは可能だ。

Integration の見え方:
> 決定論的に、全ての Integration 内の CID は同じ方向を向かなければいけない、と決めないこと。私たちはこれまでに散々平均化の罠に陥ってきた。

一点を捉える (2026-05-16 具体化):
> 平均的な統計があるならそれはそれで構わない。重要なのは、どの一点を捉えられるか。Step の最小単位でも Pulse 単位でも構わないが、それをグラフのように扱えると見え方が変わるかもしれない。

取り込み点中心:
> 現在 ESDE 内に Atom を取り込む仕組みがあるなら、その点を中心に何が起こるのかを観察する必要がある。周辺の CID と何が起こるかなど、具体的な観察が必要。

主題選定の理由 + 優先度 (2026-05-16):
> 私の案は、v1101 で扱う。優先度は 3 案より上。なぜなら 3 案を読んだ上で長考に入ったから。ここで何が見えるかを扱えないと進化の意味が不在になると直感。

#### 3.2 観察 3 視点

| 観察 | 中核 | Taka 確定基準 |
|---|---|---|
| 1: 一点を捉える | 特定 cid の atom 状態を Step/Pulse 単位で時系列グラフ化 | (c) n_pulses_short 最大 cid 主 + (d) ランダム比較対照、(b) atom 濃度近接 不採用 |
| 2: 取り込み点中心の波及 | atom_introduction_event 発火点を中心 + 周辺 cid の変化 | (a) v10.12 受容 cid pool 420、周辺 cid = 同 seed 全 cid (228) |
| 3: 補助平均統計 | CID / Integration / ESDE の 3 単位、Integration は分布表現 | atom 集合 326 全部 + 25 TARGET vs 残り 301 分離表示 |

#### 3.3 Code A Step A-H 完了 (2026-05-17、commit 8 件)

| Step | commit | 内容 |
|---|---|---|
| A | 127d65d | 認識確認 + 齟齬 10 件 + 即決事項受領 |
| B | db2bf45 | 環境チェック + 必要データ全所在確定 |
| C | 8b21637 | 観察 1 (48 中心 + 240 ランダム + 4 解像度 trajectory 374,072 行) |
| D | bea48a0 | 観察 2 (10,500 events × Δt 21 点 = 220,500 行) |
| E | 56f5ae6 | 観察 3 (CID/Integration/ESDE、核心発見) |
| F | 8315601 | グラフ HTML 統合 (954 KB dashboard) |
| G | 2e468d2 | bit-identity 3 層全 PASS |
| H | f3a4a95 | 観察事実最終総括 |

#### 3.4 主要発見

##### 観察 1 (4 件)

1. v108_standard 中心 cid の dominant_atom が `WLD.artless` で 24 seeds 中 21 seed 一致 (87.5%)、v112 は PER.sound 10 / TIM.moment 5 / TIM.appear 4 に分散
2. dominant_atom_fraction で v108_standard 中心 0.92-1.00 (単 atom ロック) vs v112 中心 0.47-0.81 (複数 atom 揺れ)
3. 両条件で中心 cid の trajectory row 数 < ランダムの約 1/3-1/4
4. window 解像度のみ v112 中心 cid の atom_change_rate 0.156 < ランダム 0.297 (時間スケール依存)

##### 観察 2 (4 件)

1. **25 取り込み atom 中 4 atom のみ中心 cid を支配可**:
   - PER.sound (peak 84.8% at Δt=+20)
   - PRP.bright (peak 49.3% at Δt=-90)
   - TIM.appear (peak 14.8% at Δt=-100)
   - WLD.artless (peak 8.8% at Δt=+70)
   - 残り 21 atom は center_match_rate = 0% 全 Δt
2. 周辺 cid の atom 分布は取り込み atom に依存せず PER.sound + WLD.artless が常時 ~60% 占有
3. atom_entropy_mean Δt 方向単調減少 (取り込み後集中化、ただし独立効果か自然動学か段階 2 検証)
4. PER.sound 波及プロファイル特異 (取り込み直後ピーク後減衰)

##### 観察 3 核心発見 (本 v1101 最重要)

**観察単位による dominant atom の構造的反転**:

| 観察単位 | 1 位 atom | 値 |
|---|---|---:|
| CID 単位 (cid_atom_sim_matrix sim_mean) | **CHG.begin** | 0.536 |
| Integration β top_atom | **FND.logic** | 160 βs (79%) |
| Integration α pattern_class dominant | **TIM.moment** | 114 / 144 (79%) |
| ESDE event resolution rank_1 | **WLD.artless** (26.2%) + PER.sound (25.9%) | — |
| ESDE step10 resolution rank_1 | **PER.sound** | 28.3% |
| ESDE window resolution rank_1 | **TIM.moment** | 34.2% |

→ **5 atom 分裂** (CHG.begin / FND.logic / TIM.moment / WLD.artless / PER.sound)、Taka「平均化の罠」(絶対格言 #4) + 「Integration 内同方向強制せず」の直接的観察的根拠、v10.13.a 留保 #33 の **Atom レベル一般化**。

#### 3.5 統合視点

- 観察 1 + 観察 2 + 観察 3 ESDE event/step10 は **整合** (WLD.artless + PER.sound dominant)
- 観察 3 Integration α/β レベルは **categorically 異なる atom 像** (TIM.moment / FND.logic dominant)
- 観察 3 CID-static sim も異なる atom (CHG.begin)
- → ESDE は **多層 Atom 像** を持つ系

#### 3.6 Step F グラフ HTML

`unified/v1101/outputs/v1101_observation.html` 単一 954 KB:
- 5 figure (観察 1 集計 + trajectory / 観察 2 heatmap + 主要 4 atom 曲線 / 観察 3 反転 6 panel)
- 4 h2 section + key-finding boxes
- Plotly 6.7.0 + CDN、v105 pattern 踏襲

#### 3.7 Step G bit-identity 3 層全 PASS

| 層 | 内容 | 結果 |
|---|---|:-:|
| A | Step C/D/E parquet 10/10 hash 一致 + Step F HTML 構造的同一性 | ✓ |
| B | v106 (731) + v108 (368) + v112 (207) = 1,306 ファイル全て不変 | ✓ |
| C | 全 11 write 呼出 (to_parquet × 10 + write_text × 1) が unified/v1101/ 配下のみ | ✓ |

#### 3.8 新規留保候補

| id | step | 内容 | 状態 |
|---|---|---|---|
| #38-#40 candidate | Step A | 旧 v1102 ドキュメント齟齬 (親資料不在 / Integration 未実施記述 / 時系列既存出力見落とし) | **解消済** (即決事項 1/3/4) |
| **#41 candidate** | Step E | Integration の **member_cids 個別 cid id list は v10.x outputs に persistence されていない** | **段階 2 対応**: cid state ledger 再生 + Integration 形成イベント再生 (新規 main run 不要) |
| **#42 candidate** | Step E | **観察単位による dominant atom 反転** (v10.13.a 留保 #33 の Atom レベル一般化) | **Web Claude Phase Result 解釈統合領域** |

---

### 4. 現在地 + 後続タスク

#### 4.1 完了状態 (Code A 主題担当範囲)

- v10.13.a Map analyzer 完了
- v1100 候補 6 実装完了 (Phase Result 未完成)
- v1101 Step A-H 完了 (本書 §3 参照)
- 累計 commit 14+ 件 (v10.13.a + v1100 + v1101)
- 物理層 frozen 絶対維持 (v10.6/v10.8/v10.12 main outputs 1,306 ファイル不変)

#### 4.2 待機中タスク

| 段階 | 担当 | 想定時間 | 内容 |
|---|---|---|---|
| **Step J (v1101 Phase Result)** | **新 Web Claude** | 1-2 日 | 観察 1/2/3 + 核心発見の解釈統合、「ESDE の内部は Atom 的にこうなっているようだ」記述、Taka 主題評価判断材料の提供 |
| Step I (v1101 任意、段階 2) | Code A | 1.5-2 日 | cid state ledger 再生 + 留保 #41 解消 + atom entropy 取り込み独立効果検証 |
| v1100 Step K (Phase Result) | 旧/新 Web Claude | 未定 | v1100 Phase Result 未完成、v1101 完了後に扱う可能性 |
| v11.0.1.a 以降 | 未定 | 未定 | v1100 残課題 A/B/C (Synapse 層化 / Phase 8+9 Cell ↔ Integration 同型性 / 候補 6 大規模化) を扱う可能性 |

#### 4.3 主題評価判断

Code A は **judgment 回避** (絶対格言 #12)、本観察結果の主題評価 (success / fail) は Taka 領域。Web Claude Phase Result は解釈統合の素材を提供、最終評価は Taka が決定。

---

### 5. 累積規律 + 留保 (06b からの継続)

#### 5.1 06b からの累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト

v10.12 Step A 時点で確立済 (06b §3 参照)。本 v1101 で **修正なし、追加なし** (新規観察軸を追加していないため、絶対格言 #5 と整合)。

#### 5.2 留保事項総覧

- v10.12 までの累積 22 件 (06b §4)
- v1100 で +3 件 (#35-#37 candidate、06b 未収録)
- **v1101 で +5 件** (#38-#40 candidate 解消済、#41/#42 candidate 段階 2 / Web Claude 領域)

#### 5.3 絶対格言 15 件 (Code A 報告書から再構成、Web Claude memory 要確認)

旧 Web Claude memory にあった「絶対格言 15 件」は repo に明示リストなし。Code A 各 Step 報告書の規律遵守チェックリストから再構成:

| # | 格言 |
|---|---|
| 1 | Aruism 構造が先・意味が後 |
| 2 | 物理層 frozen 絶対 |
| 3 | ベースライン比較 + 効果サイズ |
| 4 | 集団平均の罠 / n_core 別層化 |
| 5 | 観察軸を増やすことを駆動要因にしない |
| 6 | 出口の固定 |
| 7 | 主題着手前に上位資料を読む |
| 8 | 過去観察軸の照会 |
| 9 | 神の手回避 + Pulse 同一フォーマット |
| 10 | 因果ではなく因果候補 |
| 11 | 概念単位を雑に扱わない |
| 12 | Aruism 判定回避 |
| 13 | AI を信じない原則は Taka 個人のみ |
| 14 | Taka 直感優先 + 直感語保存 |
| 15 | 5 者運用体制の補完性 |

→ 新 Web Claude は memory 確認 + 本リスト照合推奨。Taka 哲学 4 件は memory のみ存在、Taka 直接確認推奨。

---

### 6. 参照すべき repo 内資料 (v10.13.a / v1100 / v1101)

#### 6.1 v10.13.a

| ファイル | 内容 |
|---|---|
| `developmental/v113a/v113a_step_a_recognition.md` | Step A 認識確認 |
| `developmental/v113a/v113a_observation_report.md` | 観察事実報告 |
| `developmental/v113a/v113a_maps_analyzer.py` | 5 phase Map analyzer 実装 |
| `developmental/v113a/outputs/main/map{1-5}_*.parquet` | Map 1-5 出力 |

#### 6.2 v1100 (Language ↔ Genesis 接続、Phase Result 未完成)

| ファイル | 内容 |
|---|---|
| `unified/v1100/v1100_step_a_recognition.md` | Step A 認識確認 + 事前齟齬 8 件指摘 |
| `unified/v1100/v1100_observation.md` | Step J 観察事実報告 (Code A、Phase Result の代替) |
| `unified/v1100/language_side_investigation_report.md` | Language 側調査 |
| `unified/v1100/v1100_candidate_6_*.py` | 候補 6 実装 (R@3 / R@1 / extended / r1_analysis) |
| `unified/v1100/outputs/candidate_6_*.json` | 候補 6 結果 (overlap / extended_analysis / r1_overlap) |

#### 6.3 v1101 (Atom 的隆盛の統計的観察、Code A 担当完了、Web Claude Phase Result 未完成)

| ファイル | 内容 |
|---|---|
| `unified/v1101/v1101_phase_design.md` | **主題ドキュメント (2026-05-16 改訂版)、本 v1101 の親** |
| `unified/v1101/v1101_web_claude_handoff.md` | **新 Web Claude 引き継ぎ document、最初に読む** |
| `unified/v1101/v1101_step_a_recognition.md` | Step A 認識確認 (齟齬 10 件) |
| `unified/v1101/v1101_step_b_environment_check.md` | Step B 環境チェック |
| `unified/v1101/v1101_step_c_report.md` | Step C 観察 1 |
| `unified/v1101/v1101_step_d_report.md` | Step D 観察 2 |
| `unified/v1101/v1101_step_e_report.md` | Step E 観察 3 (核心発見) |
| `unified/v1101/v1101_step_f_report.md` | Step F グラフ HTML |
| `unified/v1101/v1101_step_g_report.md` | Step G bit-identity |
| `unified/v1101/v1101_step_h_observation_final.md` | **Step H 観察事実最終総括、Web Claude Phase Result 翻訳用** |
| `unified/v1101/v1101_step_{c..g}_*.py` | 実装スクリプト 5 ファイル |
| `unified/v1101/outputs/main/observation_{1,2,3}_*.parquet` | 観察 1/2/3 出力 10 ファイル |
| `unified/v1101/outputs/v1101_observation.html` | グラフ HTML (Taka ブラウザ表示) |
| `unified/v1101/outputs/v1101_step_g_bit_identity_report.json` | bit-identity 検証結果 |

---

### 7. 一文サマリ (再掲)

v10.12 (Phase 1.5 第七試行 Atom 取り込み prototype 受容 cid 再厳格化、Step K 完了 2026-05-11) の後 v10.13.a (5 phase Map analyzer + Map 5 null phase 20 unique atoms、2026-05-12 完了) を経て Unified Phase へ移行、v11.0.0 (v1100、2026-05-12) で Language ↔ Genesis 接続事前調査 6 候補を扱い候補 6 を実装 (R@1 ベース base 優位 18 tokens、Language base 優位 atom {SOC.official, PRP.part} と Genesis Map 5 null cell 20 atoms の重なり 0 で両系独立確認、留保 #34 candidate 棄却方向、新齟齬 #35-#37 candidate、Phase Result 未完成、残課題 A/B/C は Taka 判断で凍結)、v11.0.1 (v1101、2026-05-12〜2026-05-17) で Taka 3 日長考結論「Atom 的隆盛の統計的観察」を扱い観察 1 (中心 cid 48 + ランダム 240 + 4 解像度 trajectory 374,072 行) + 観察 2 (10,500 events × Δt 21 点) + 観察 3 (CID/Integration/ESDE) を Code A Step A-H で完了 (commit 8 件、出力 25 ファイル 7 MB、bit-identity 3 層全 PASS)、核心発見 = 観察単位による dominant atom 構造的反転 (CID-static CHG.begin / β FND.logic / α TIM.moment / ESDE event WLD.artless+PER.sound / step10 PER.sound / window TIM.moment の 5 atom 分裂、Taka「平均化の罠」絶対格言 #4 の生きた実例、v10.13.a 留保 #33 の Atom レベル一般化)、観察 2 副発見 = 25 取り込み atom 中 4 atom のみ中心 cid 支配可 (PER.sound peak 84.8%) + 周辺 cid 60% 占有が PER.sound + WLD.artless + atom entropy Δt 単調減少、観察 1 副発見 = v108_standard 中心 cid dominant WLD.artless 21/24 seeds + window 解像度の一点特徴、Step F グラフ HTML 単一 954 KB ダッシュボード、Step G で deterministic + v10.x main outputs 1,306 ファイル frozen 完全保証、新規留保 #41 candidate (Integration member_cids 個別 list 未 persistence、段階 2 対応) + #42 candidate (観察単位反転、Web Claude 解釈統合領域)、Code A 主題担当範囲完了、**待機**: Step J (新 Web Claude Phase Result、1-2 日) + 任意 Step I (段階 2、1.5-2 日) + Taka 主題評価判断、絶対格言 15 件全項目遵守 (Code A 報告書から再構成可、Web Claude memory 要確認)、Taka 哲学 4 件は Web Claude memory のみ (Taka 直接確認推奨)、新 Web Claude 最小必読は `v1101_web_claude_handoff.md` + `v1101_phase_design.md` + `v1101_step_h_observation_final.md` の 3 点、Code A 認識確認連続 10 段階継続中。

---

*以上、06c Developmental v10.13.a + Unified Phase v1100/v1101 Summary (Code A、2026-05-17)。新 Web Claude スレッドはこれ + 06b + v1101_web_claude_handoff.md で v10.4-v1101 の全容把握可能。06b は v10.4-v10.12 (Phase 1.5 本体)、本書は v10.13.a + v1100 + v1101 (Phase 1.5 続編 + Unified Phase 第一・第二)。次回 (v11.0.1.a / v11.0.2) は新 06d / 06e で扱う想定。*
