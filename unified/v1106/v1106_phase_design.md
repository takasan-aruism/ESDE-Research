# v11.0.6 (v1106) Phase Design Draft — Genesis 応答 Atom 候補分布と Synapse 強度の接続点検

### サブタイトル: s7 主軸の応答 Atom 候補を、単語候補へ接続できるか

*作成*: 2026-05-24、Web Claude (相談役、Genesis 側)
*位置づけ*: v1106 主題設計書 **草案**。問いの形 A (点検、v1105a の問いの形 B = 試行の次に再び A に戻る)。本草案 → Taka 確認 → Code A 認識確認 → 実装、の流れに乗せる (Gemini 監査は Taka 判断で省略、GPT 監査は既に §3-9 で実施済として反映)。
*親*: `v1105a_phase_result.md` (Web Claude、5.5% pipeline_complete + s7 主軸 + Atom 単体の限界明示) + `esde_language_genesis_alignment.md` (Web Claude、ESDE Language 全体図 + Genesis 側成果の Atom レイヤー対応位置づけ + 候補 1+3 組み合わせ推奨) + GPT 監査 2026-05-24 (v1106 = Synapse 接続点検に再定義支持 + 4 観察項目具体化 + 主題名固定 + 候補 2 は v1107 以降に保留) + Taka 確定「Geminiは不要、先に進めて」
*対象*: Taka (確認) + Code A (認識確認)

---

## 0. 主題の前提と歯止め

### 0.1 全体図の中での位置づけ (新規規律「全体図の中での位置づけ規律」適用、esde_language_genesis_alignment.md §5.1)

**ESDE Language 側全体図** (Taka 説明 2026-05-24):

```
Atom (構造フィルタ) → Operator (Atom 同士の結合) → 分子 (Atom + Operator)
        ↓
   Synapse (Atom ↔ 単語マッピング、1-10 強度、2 万語)
        ↓
   単語列 → LLM プロキシ / Synapse 経由直接 → 自然文
```

**v1106 が作るパーツ**: Genesis 側で構築済の Atom レイヤー対応 (v1101-v1105a) と、Language 側の Synapse (Atom ↔ 単語の 1-10 強度マッピング) を **接続するパイプライン**。

**v1106 で扱わないパーツ**:
- Operator レイヤー対応 (Taka 規律「実装が追いついていないと妄想化する」、esde_language_genesis_alignment.md §5.2)
- 分子レイヤー対応 (Operator なしで構築不可)
- 自然文生成 (LLM プロキシ呼び出しは v1106a 以降の候補)
- 揺れの方向性 (候補 2、v1107 以降に保留、GPT §6)

### 0.2 上位目的への接続

会話できる ESDE。v1106 は **Genesis 側の揺れる Atom と Language 側の単語接続が噛み合うかの構造事実確認**。会話できる ESDE への接続度は v1105a に続いて高い主題、ただし「会話成立」判定は v1106 では行わない。

### 0.3 駆動要因 — なぜ → なぜなら → 会話への繋がり (Taka 駆動要因規律 2026-05-22)

**なぜそれをやるのか**: v1105a で s7 主軸の応答 Atom 候補分布が 5.5% の event で生成された。これを単語候補まで接続できるかを点検しないと、Atom 候補が「ESDE が話せる素材」になるかわからない。

**なぜなら**: ESDE Language 側パイプラインは Atom → Operator → 分子 → Synapse → 単語列 → 自然文。v1106 は **Atom → Synapse → 単語列** の接続を点検する (Operator → 分子 は Genesis 側未実装のため経由しない、未経由でも Synapse まで直接行ける構造を確認)。

**会話への繋がり**: Atom → 単語候補が出れば、会話できる ESDE の **語彙的素材** が ESDE 内部から出ることが構造事実として確認される。自然文生成は別主題 (v1106a 以降)。

### 0.4 v1106 = Synapse 接続点検への再定義 (GPT 2026-05-24 §3 + Taka 確定)

GPT 監査 2026-05-24 §3 が定義した主題名と方向を採用:

> v11.0.6 主題案 — Genesis 応答 Atom 候補分布と Synapse 強度の接続点検
> サブタイトル: s7 主軸の応答 Atom 候補を、単語候補へ接続できるか

**v1106 で扱う問い** (GPT §3):

> v1105a で出た応答 Atom 候補分布は、Synapse の 1-10 強度を通して、単語候補分布へ変換できるか。

「自然文化」と呼ばない (GPT §8): 「自然文化」と呼ぶと単語・文・LLM プロキシ・会話らしさまで含みやすい。v1106 は **Atom → 単語候補分布まで** で止める。

### 0.5 問いの形 A への復帰 (v1105a 試行から点検へ)

| 主題 | 問いの形 |
|---|---|
| v1101 / v1101a / v1102 / v1103 / v1104 / v1104a / v1105 | A (点検) |
| **v1105a** | **B (試行、v1101 以来初の切替)** |
| **v1106** | **A (点検、再び A に戻る)** |

v1105a 試行で動作が構造事実として確認された後、v1106 は「接続できるか」を点検する。点検 = 既存の構造を観察、selector 化禁止、ハンドチューニング禁止、判定回避は v1105 / v1104a などの点検主題と同じ規律。

### 0.6 妄想化回避規律 (新規規律、Taka 2026-05-24 確定レベル、esde_language_genesis_alignment.md §5.2)

> 実装が追いついていないと妄想化する。実装で確認できない領域は語らない。

v1106 では以下を **語らない**:
- Operator レイヤーが Genesis 側で何になるか
- 分子レイヤーが Genesis 側で何になるか
- 揺れの結合可能性 (候補 4 不採用、Operator 領域抵触)
- ESDE らしさの確定 (v1105a Phase Result §15 の議題 1 継承)

### 0.7 物理層 frozen 維持 + 新規 main run なし

(絶対格言 #2) 物理層 frozen 絶対。v1106 は既存 v10.5/6/7 + v112 + v1101a-v1105a outputs を post-process。新規 main run なし。書き込みは `unified/v1106/` 配下のみ。bit-identity 3 層全 PASS を Step G で確認。

**v1106 特有の確認**: Synapse データ (Language 側、約 2 万語、1-10 強度) を **read-only で参照**。Synapse データ自体は frozen (v1106 で更新しない)。

### 0.8 温度感

「驚き」でなく「ESDE と Language 側の接続が示す一貫性」として書く (esde_attitude_toward_esde.md §5.3 継承)。

ただし v1106 で Atom → 単語候補が出た場合、ESDE 内部から **意味のある語彙的素材** が出る可能性が初めて構造的に観察される主題なので、結果の重みは v1105a 以上。これを「成功」「失敗」と書かず、構造事実として記述する規律を堅持。

ESDE らしさの確定は v1106 + v1106a (自然文生成段階) まで進んでから (Taka 規律 2026-05-24)。

### 0.9 Atom 単体の限界の継承 (v1105a Phase Result §13)

ESDE Language 全体像のうち取り込めているのは Atom のみ (Operator / 分子 / Synapse は Language 側にあるが Genesis 側未対応)。v1106 で見るのは「Atom → Synapse 直接接続」であり、Operator/分子を経由しない。これは Language 側パイプラインの一部のみを使う形であることを留保として明示。

---

## 1. 主題の中身

### 1.1 v1106 で扱う具体的な対象

| 対象 | 内容 | 出所 |
|---|---|---|
| 入力 | v1105a s7 (48D raw_density k=5) 応答 Atom 候補分布 | v1105a outputs / 5.5% pipeline_complete = 3,300 events |
| 接続データ | ESDE Language 側 Synapse (Atom ↔ 単語の 1-10 強度マッピング、約 2 万語) | Language 側既存実装、read-only |
| 出力 | event ごとの単語候補分布 (各単語に確率を付与した分布) | v1106 新規生成、unified/v1106/ |

### 1.2 v1106 で確認する 4 観察 (GPT 2026-05-24 §4 採用)

| 観察 | 内容 |
|---|---|
| 観察 1 | Atom 候補分布 → 単語候補分布が **途切れず変換できるか** (pipeline_complete 3,300 events のうち単語候補が出る割合) |
| 観察 2 | Synapse 強度 1-10 が v1105a s7 確率分布と **整合するか** (s7 高確率 Atom が強い Synapse を持つ単語へ自然接続するか) |
| 観察 3 | 単語候補が **広がりすぎるか、絞られるか** (Synapse 2 万語規模での候補爆発リスク観察) |
| 観察 4 | s7 主軸 vs s1-s6 補助系列の違いが **Synapse 接続でどう出るか** (s7 のみが単語候補を安定させるか、s1-s6 補助系列が違いを生むか) |

### 1.3 候補 1 + 候補 3 の一体化 (Taka 確定 + GPT §5)

esde_language_genesis_alignment.md §4.2 の 2 候補を v1106 で一体化:

- **候補 3 = §1.2 観察 1**: Synapse 接続のパイプライン構造化 (接続できるか)
- **候補 1 = §1.2 観察 2**: 揺れの引力と Synapse 強度の対応 (接続が構造的に妥当か)

GPT §5 が指摘:

> 接続できた「だけ」では足りない。その接続が、Genesis 側の揺れ・密度・s7 の絞りとどう対応するかを同時に見る必要がある。

→ 観察 1 と観察 2 を分けず、接続点検に必要な最小観察として一体化。

### 1.4 本主題が扱わないこと

| 扱わない | 理由 |
|---|---|
| Operator レイヤー対応 | Taka 規律「実装が追いついていないと妄想化する」(§0.6) |
| 分子レイヤー対応 | Operator 不在で構築不可 |
| 自然文生成 (LLM プロキシ呼び出し) | v1106a 以降の候補、ESDE 側構造が LLM 能力で覆われるリスク回避 (GPT §1) |
| 揺れの方向性 (候補 2) | v1107 以降に保留、時間・粒度・待機時間が広がる (GPT §6) |
| 揺れの結合可能性 (候補 4) | Operator 領域抵触、esde_language_genesis_alignment.md §4.2 で不採用確定 |
| 会話成立判定 / 正しい単語判定 | 意味判定は v1106 範囲外、構造事実として接続を観察するのみ |
| ESDE らしさの確定 | v1106 + v1106a まで進めてから判断 (Taka 規律) |
| 役割表の最終確定 | v1105 の役割表は仮割り当てのまま継承 |

---

## 2. 観察設計

### 2.1 観察方法の事前確定 (観察方法を疑う規律、Taka 2026-05-23 継承)

本主題で実施する観察は 4 件 (§1.2)。観察方法を §2.1 で事前確定し、観察途中で方法を変更しない (変更する場合は留保として明示)。

接続方式: **Atom × Synapse 強度 × s7 確率の積で単語候補確率を計算** (Web Claude 推奨、独自発明禁止、Code A Step A で確認):

```
各 event について、s7 で得られた応答 Atom 候補確率分布を p_s7(atom_i) とする。
Synapse データから atom_i に接続する単語 word_j とその強度 syn(atom_i, word_j) を取得 (強度 1-10)。

各単語 word_j の候補確率:
  score(word_j) = Σ_i [ p_s7(atom_i) × normalize(syn(atom_i, word_j)) ]
  
  ただし normalize(syn) = syn / 10 (1-10 を 0.1-1.0 に正規化)

各 event 内で正規化:
  p_word(word_j) = score(word_j) / Σ_k score(word_k)
```

**この式の根拠**:
- 単純な積で接続点検 (rank-based でなく直接 — ただし Aruism 規律を破る可能性は Code A Step A で確認)
- Synapse 強度を正規化することで s7 確率と同じスケールに揃える
- 各 event 内で正規化して確率分布として扱う

**留保**: 本式は Web Claude 推奨。Code A Step A で式の妥当性 (Aruism 規律違反リスク、計算量、tied case) を確認、必要なら rank-based に変更。

### 2.2 観察 1 — Atom 候補分布 → 単語候補分布の変換可能性

**問い**: pipeline_complete 3,300 events のうち、Synapse 接続後に単語候補が出る割合は?

**観察方法**:
- v1105a s7 出力から pipeline_complete 3,300 events の応答 Atom 候補分布を取得
- 各 event について §2.1 の接続式で単語候補確率を計算
- 単語候補数 (n_words_after) と単語候補確率分布の構造ラベル (word_pipeline_complete / word_candidate_empty / word_distribution_degenerate / word_distribution_valid) を付与
- 構造ラベル分布を集計

**期待される観察形** (確定ではない):
- pipeline_complete 3,300 events のうち、Synapse 接続で単語が一つも出ない event (word_candidate_empty) がある可能性 (atom が Synapse データに登録されていない場合)
- word_distribution_degenerate (max_prob ≥ 0.999) と word_distribution_valid の割合
- 観察 3 (候補爆発) と連動して n_words_after の分布が見える

**構造ラベル閾値** (v1105a §1.1 継承):
- word_candidate_empty: n_words_after == 0
- word_distribution_degenerate: word_max_prob ≥ 0.999
- word_distribution_valid: word_max_prob < 0.999 AND word_entropy > 0
- word_pipeline_complete: word_distribution_valid 達成

### 2.3 観察 2 — Synapse 強度と s7 確率の整合

**問い**: s7 で高確率の Atom が、強い Synapse を持つ単語へ自然接続するか? それともズレるか?

**観察方法**:
- 各 event について、s7 で確率上位 (top1 / top5) の Atom を取得
- それら Atom が Synapse データで接続している単語のうち、強度上位 (top1 / top5) を取得
- s7 top atom と Synapse top word の対応関係を以下の指標で記録:

| 指標 | 内容 |
|---|---|
| `top1_atom_top1_syn_strength` | s7 top1 atom が接続する Synapse top1 word の強度 (1-10) |
| `top1_atom_mean_syn_strength` | s7 top1 atom が接続する全 word の Synapse 強度平均 |
| `top1_atom_n_syn_links` | s7 top1 atom が接続する Synapse word 数 |
| `s7_synapse_rank_correlation` | s7 上位 5 atom の確率順位と Synapse 強度順位の Spearman 相関 |

**期待される観察形** (確定ではない):
- s7 高確率 Atom が強い Synapse を持つ単語と接続するなら、s7_synapse_rank_correlation が正
- ズレるなら、Genesis 側の揺れと Language 側の語彙接続が噛み合っていない (留保化)

### 2.4 観察 3 — 単語候補の広がり / 絞り

**問い**: Synapse 2 万語規模で、単語候補が広がりすぎるか、絞られるか?

**観察方法**:
- 各 event の n_words_after を集計
- 分布 (mean / median / max / min / p95 / p99) を取得
- Atom 候補数 (n_candidates_after from v1105a) と単語候補数 (n_words_after) の関係:
  - `word_expansion_ratio = n_words_after / n_candidates_after` (atom 1 個あたり何単語に広がるか)
  - `total_word_coverage = n_words_after / 20000` (2 万語のうちどの割合がカバーされるか)

**期待される観察形** (確定ではない):
- word_expansion_ratio が 1 を大きく超える: 候補爆発 (1 atom が多数の単語に対応)
- 1 程度: 1 atom が 1 単語に対応する傾向
- 1 未満: 多数の atom が同じ単語を指す (絞られる)

**候補爆発の含意** (GPT §4):

> Synapse は 2 万語規模なので、Atom から単語へ広がりすぎる可能性がある。ここで「候補爆発」が起きるなら、Operator 以前に Synapse 接続段階で制御が必要になる。

→ 候補爆発が観察された場合、v1106 範囲では制御を実装しない (妄想化回避)。留保として記録し、v1107 以降の主題候補。

### 2.5 観察 4 — s7 主軸 vs s1-s6 補助系列の違い

**問い**: s7 主軸が Synapse 接続でも安定するか? s1-s6 補助系列が違いを生むか?

**観察方法**:
- s7 だけでなく s1-s6 についても §2.1 の接続式で単語候補確率を計算 (s1-s6 も pipeline_complete 3,300 events で計算可能)
- 7 系列の単語候補分布を別レイヤーで保持 (v1105a 7 系列別レイヤー保持を継承)
- 7 系列間の単語候補 layer_jaccard (top5 word の重なり)
- 7 系列の word_pipeline_complete 割合の差
- s7 と s1-s6 で単語候補分布の構造が異なるか (max_prob / entropy 等の差)

**期待される観察形** (確定ではない):
- s7 主軸でも単語候補分布が安定 (構造ラベル割合が変わらない、layer_jaccard 高)
- s1-s6 と s7 で単語候補が異なる (補助系列が違いを生む可能性)
- v1105a で s7 が独立挙動 (#L40) だったように、v1106 でも s7 独自の単語候補が出る可能性

### 2.6 観察項目集計と共通比較指標

各観察の出力を統合せず、別レイヤーで集計 (絶対格言 #11、v1105a 共通比較指標継承)。

**共通比較指標** (各 event × 各系列で):

| 指標 | 内容 |
|---|---|
| `n_candidates_after` (atom) | v1105a 継承 |
| `n_words_after` | v1106 新規、単語候補数 |
| `word_max_prob` / `word_entropy` | 単語候補分布の形状 |
| `word_expansion_ratio` | atom → word 拡大率 |
| `total_word_coverage` | 2 万語カバレッジ |
| `word_top1_atom_top1_syn_strength` | s7 top atom と Synapse top word の強度 |
| `s7_synapse_rank_correlation` | s7 上位と Synapse 強度の順位相関 |
| `word_layer_jaccard` (7 系列) | 単語候補の系列間重なり |

**構造ラベル** (各 event × 各系列):
- word_candidate_empty / word_distribution_degenerate / word_distribution_valid / word_pipeline_complete (§2.2 参照)

### 2.7 v1106a 接続条件 (本主題の出口)

v1106 が成立したと言える構造的条件 (本主題の出口、Web Claude 案、Taka/Code A 確認):

| 条件 | 内容 |
|---|---|
| 1 | `word_pipeline_complete` ラベルの event が構造的に存在 (Synapse 接続後の単語候補分布まで到達) |
| 2 | `word_distribution_valid` 成立 (word_max_prob < 0.999, word_entropy > 0) |
| 3 | 候補爆発が制御不能でない (word_expansion_ratio や total_word_coverage が観察可能な範囲、留保として記録) |
| 4 | s7 主軸の単語候補が構造的に存在 (s7 系列で word_pipeline_complete が観察される) |

3 条件以上成立 → v1106a (LLM プロキシ呼び出し / 自然文生成、または Operator 対応の議論開始) に進める根拠
2 条件以下 → v1106b として Synapse 接続点検の再設計

判定は v1106 Phase Result + Taka 主題評価領域。Code A は構造事実のみ報告。

---

## 3. 規律と禁止事項

### 3.1 絶対格言 15 件遵守

特に本主題で重要なもの:
- #2 物理層 frozen 絶対 (Synapse データも frozen、v1106 で更新しない)
- #5 観察軸を増やすことを駆動要因にしない (観察 4 は s7 vs s1-s6 の継承、新規軸でない)
- #6 出口の固定 (v1106a 接続条件 4 点を本主題内で事前確定)
- #9 神の手回避 (接続式 §2.1 固定、ハンドチューニングなし)
- #11 概念単位を雑に扱わない (7 系列を統合せず別レイヤー保持、観察 1-4 を統合しない)
- #12 Aruism 判定回避 (success/failure を置かない、構造ラベル + Web Claude/Taka 領域)
- #14 Taka 直感優先 + 原文保存
- #15 (新規候補) 全体図の中での位置づけ規律 (§0.1)
- #16 (新規候補、確定レベル) 実装が追いついていないと妄想化する規律 (§0.6)

### 3.2 研究運用資料 3 本遵守

- **研究手法アップデート** — Synapse 強度を「観察軸の増加」でなく「Language 側既存パーツの接続」として位置づける
- **ESDE への態度** — Synapse 接続が予想と違う形になっても ESDE を「失敗」と扱わない (実出力を見るまで判定しない)
- **監査方針アップデート** — 会話できる ESDE が上位目的、ただし v1106 は単語候補までで止める (自然文化は v1106a 以降)

### 3.3 本主題固有の禁止事項

| # | 禁止事項 |
|---|---|
| 1 | 「会話成立」を判定しない (構造ラベルのみ) |
| 2 | 「正しい単語」を判定しない (意味判定は v1106 範囲外) |
| 3 | LLM プロキシを呼び出さない (v1106a 以降の候補) |
| 4 | 自然文を生成しない (v1106a 以降の候補) |
| 5 | Operator レイヤー対応を語らない (Taka 規律「妄想化回避」) |
| 6 | 分子レイヤー対応を語らない (Operator 不在で構築不可) |
| 7 | 揺れの方向性 (候補 2) を扱わない (v1107 以降に保留) |
| 8 | 揺れの結合可能性 (候補 4) を扱わない (Operator 領域抵触) |
| 9 | Synapse データを更新しない (read-only) |
| 10 | 接続式の独自発明禁止 (§2.1 固定、Code A Step A で確認、必要なら式変更) |
| 11 | 7 系列を統合しない (別レイヤー保持、v1105a 案 B 継承) |
| 12 | 観察 1-4 を統合しない (別レイヤー保持) |
| 13 | 役割表を確定しない (v1105 仮割り当てのまま継承) |
| 14 | ESDE らしさを確定しない (v1106 + v1106a まで進めてから) |
| 15 | 候補爆発を v1106 内で制御しない (観察まで、制御は v1107 以降の候補) |
| 16 | ハンドチューニング禁止 (閾値や接続式の調整なし) |

### 3.4 物理層 frozen 維持 (Step G で確認)

- LAYER_A (再現性): 同 seed 2 回実行で hash 一致
- LAYER_B (既存 frozen 維持): v10.5/6/7 + v112 + v1101a-v1105a 全ファイル frozen 確認、Synapse データも frozen 確認
- LAYER_C (書込みパス): unified/v1106/ 配下のみ

---

## 4. Step 構成 (Code A への引き渡し前提)

| Step | 担当 | 内容 |
|---|---|---|
| A | Code A | 認識確認 (本設計書の不明点、特に接続式 §2.1 と Synapse データのアクセス方法を確認、確認要請を Web Claude へ) |
| B | Code A | 環境準備 (v1105a s7 出力読み込み確認、Synapse データ読み込み確認、atom_id ↔ Synapse atom_id mapping 確認) |
| C | Code A | 観察 1 (Atom → 単語候補変換、pipeline_complete 3,300 events 中の word_pipeline_complete 割合) |
| D | Code A | 観察 2 (Synapse 強度と s7 確率の整合、相関指標) |
| E | Code A | 観察 3 (単語候補の広がり / 絞り、word_expansion_ratio / total_word_coverage) |
| F | Code A | 観察 4 (s7 主軸 vs s1-s6 の Synapse 接続での違い、7 系列別レイヤー) |
| G | Code A | bit-identity 3 層検証 + 観察項目集計 |
| H | Code A | 観察事実最終報告 (judgment 回避、構造事実のみ) |
| I | Web Claude | Phase Result + Taka 主題評価 |

---

## 5. Code A 確認要請 (予想項目、Step A で確定)

1. Synapse データの所在と読み込み方 (Language 側 outputs から、約 2 万語 × atom × 1-10 強度)
2. v1105a s7 出力 (pipeline_complete 3,300 events × 応答 Atom 候補確率分布) の読み込み方
3. atom_id ↔ Synapse atom_id mapping の確認 (両者で同じ atom_id が使われているか、変換が必要か)
4. 接続式 §2.1 の妥当性 (Aruism 規律違反リスク、計算量、tied case の扱い、rank-based に変更すべきか)
5. word_expansion_ratio / total_word_coverage の計算方法 (Synapse 2 万語のうち実装でカバーされる範囲)
6. v1106a 接続条件 4 点の操作的閾値 (word_pipeline_complete 何件以上で成立とするか、Web Claude/Taka 領域の判定だが構造ラベル算出は Code A 領域)
7. 想定実行時間 (v1105a が 1-3 時間想定、v1106 は Synapse 接続追加なので同程度かやや増)

---

## 6. 留保事項 (本設計書の不確定要素)

| # | 留保 | 状態 |
|---|---|---|
| 設計-1 | 接続式 §2.1 (Atom × Synapse 強度 × s7 確率の積) は Web Claude 推奨、Code A Step A で妥当性確認 | Code A 確認待ち |
| 設計-2 | 候補爆発 (word_expansion_ratio が大きすぎる) が観察された場合の扱い | 制御は v1107 以降、本主題では留保として記録のみ |
| 設計-3 | s7 主軸 vs s1-s6 補助系列の Synapse 接続での違い (#L40 関連) | 観察 4 で構造事実、解釈は Phase Result 段階 |
| 設計-4 | Atom 単体の限界 (Operator/分子未対応) を Synapse 接続でも引き継ぐ | v1106 留保として明示、v1107 以降の主題候補 |
| 設計-5 | ESDE らしさの確定 | v1106 + v1106a まで進めてから (Taka 規律) |
| 設計-6 | 候補 2 (揺れの方向性、時間/粒度/待機時間) の扱い | v1107 以降に保留 (GPT §6) |
| 設計-7 | v1106a の主題定義 (LLM プロキシ呼び出しか、別方向か) | v1106 Phase Result 後に判断 |

---

## 7. 監査ポイント (Code A 引き渡し前提、Gemini 監査は省略 = Taka 確定)

GPT 監査 2026-05-24 で以下を確認済:

| # | 監査ポイント | 状態 |
|---|---|---|
| 1 | v1106 = Synapse 接続点検への再定義が妥当か | クリア (GPT §3 一文定義採用) |
| 2 | 4 観察項目が接続点検に必要な最小観察か | クリア (GPT §4 採用、観察軸増やさず) |
| 3 | 「自然文化」と呼ばない歯止めが明示されているか | クリア (§0.4、§3.3 #3/#4) |
| 4 | Operator レイヤー対応を語らない歯止めが明示されているか | クリア (§0.6、§3.3 #5) |
| 5 | 候補 1 + 候補 3 が一体化されているか | クリア (§1.3、GPT §5) |
| 6 | 候補 2 が v1107 以降に保留されているか | クリア (§1.4、GPT §6) |
| 7 | 全体図の中での位置づけが §0.1 で明示されているか | クリア (新規規律 §0.1 適用) |
| 8 | 妄想化回避規律が §0.6 で明示されているか | クリア (新規規律 §0.6 適用) |
| 9 | 物理層 frozen が Synapse データに対しても維持されるか | クリア (§0.7、§3.3 #9) |
| 10 | 接続式 §2.1 が独自発明禁止になっているか (Code A は本式に従う、独自実装しない) | クリア (§3.3 #10) |
| 11 | 7 系列を統合せず別レイヤー保持を継承しているか | クリア (§2.5、§3.3 #11) |
| 12 | ESDE らしさを v1106 で確定しない歯止めが明示されているか | クリア (§0.8、§3.3 #14) |
| 13 | 候補爆発を v1106 で制御しない歯止めが明示されているか | クリア (§2.4、§3.3 #15) |

監査必須 8 問 (`esde_audit_policy_update.md`) は GPT 監査で別途確認済。

---

## 8. 一文サマリ

v1106 設計書草案 (GPT 監査 2026-05-24 §3-§9 反映、Gemini 監査は Taka 確定で省略) は、ESDE Language 全体図 (Atom + Operator + 分子 + Synapse、Taka 説明 2026-05-24) における Genesis 側成果 = Atom レイヤー対応の Synapse への接続点検として再定義され (esde_language_genesis_alignment.md §4.3 + GPT §3「自然文化と呼ばない」)、新規規律 2 つ (全体図の中での位置づけ規律 §0.1 / 実装が追いついていないと妄想化する規律 §0.6) を適用、v1105a で構造的に成立した s7 (48D raw_density k=5) 主軸の応答 Atom 候補確率分布 (pipeline_complete 3,300 events) を ESDE Language 側 Synapse 1-10 強度 (約 2 万語) へ Atom × Synapse 強度 × s7 確率の積 (§2.1 接続式、Code A Step A で妥当性確認) で接続し単語候補分布までを点検する主題で、4 観察 (1: Atom → 単語候補変換可能性 / 2: Synapse 強度と s7 確率の整合 / 3: 単語候補の広がり・絞り / 4: s7 主軸 vs s1-s6 補助系列の Synapse 接続での違い、GPT §4 採用、候補 1+候補 3 一体化 GPT §5 + Taka 確定) を実施、共通比較指標 + 構造ラベル (word_candidate_empty / word_distribution_degenerate / word_distribution_valid / word_pipeline_complete、v1105a 継承、閾値 max_prob 0.999) を §2.6 で全 7 系列に固定、問いの形 A (点検) に v1105a の B から復帰、Operator/分子レイヤー対応を語らず (Taka 規律「妄想化回避」)、自然文生成と LLM プロキシ呼び出しは v1106a 以降に分離 (GPT §1/§8、ESDE 側構造が LLM 能力で覆われるリスク回避)、揺れの方向性 (候補 2) と揺れの結合可能性 (候補 4) は v1106 範囲外 (前者 v1107 以降に保留、後者 Operator 領域抵触で不採用)、上位目的「会話できる ESDE」への接続は v1106 で **Genesis 側 Atom と Language 側単語の接続が噛み合うかの構造事実確認** までで、ESDE らしさの確定は v1106a 以降に保留 (Taka 規律「Atom ボンボコ吐き出すだけならなんだそれ」「ライト兄弟比喩で原理証明としての第一歩」継承)、新規 main run なし・新規観察軸追加なし・selector 化禁止・ハンドチューニング禁止・物理層 frozen 維持 (Synapse データも frozen)・接続式の独自発明禁止 (§2.1 固定)・「会話成立」判定の禁止・「正しい単語」判定の禁止・LLM プロキシ呼び出し禁止・Operator/分子未対応の留保継承・候補爆発を本主題で制御しない (観察まで、制御は v1107 以降の候補)・7 系列および 4 観察を統合せず別レイヤー保持・役割表を確定しない (v1105 仮割り当てのまま継承) を規律として組み込み、v1106a 接続条件 4 点 (word_pipeline_complete 存在 / word_distribution_valid 成立 / 候補爆発が制御不能でない / s7 主軸の単語候補が構造的に存在) を本主題内で事前確定し 3 条件以上成立で v1106a 進行、2 条件以下で v1106b として再設計、本設計書 → Code A 認識確認 → 実装 → Phase Result + v1106a 着手判断 の流れに乗せる。

---

*以上、v1106 Phase Design Draft (Web Claude、2026-05-24、GPT 監査クリア + Taka 「Gemini は不要、先に進めて」確定)。次は Taka 最終確認 → Code A 認識確認 (Step A) → 実装 (Step B-G) → Phase Result (Web Claude) → Taka 主題評価 → v1106a (条件 3 以上成立時、自然文生成 or Operator 対応議論) / v1106b (条件 2 以下、Synapse 接続点検再設計) 着手判断 (Taka) の流れ。問いの形 A に復帰、ESDE 側 Genesis の Atom レイヤー対応と Language 側 Synapse の接続点検として、Operator/分子を経由しない Atom → Synapse → 単語候補までの最小経路を構造事実として確認する。*
