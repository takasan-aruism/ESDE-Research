# v11.0.5.a (v1105a) Phase Design Draft — 役割表を使って実際に応答候補を絞る試行

*作成*: 2026-05-24、Web Claude (相談役、Genesis 側)
*更新*: 2026-05-24、2 AI 監査反映 (GPT Auditor 4 点修正 + Gemini Architect 全面承認 + 構造的アドバイス)
  - §2.4 試行 Step 3: 絞りアルゴリズムを **rank-based に固定** (`w_i = 1/log(rank_i + 2)` × 積 × 正規化、Aruism 規律を仕様として組み込み、GPT + Gemini 一致)
  - §1.1 / §1.3 / §2.6 / §3.3: 「成立/不成立」を **構造ラベル** (pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid) に置き換え (GPT)
  - §1.3 / §2.6: 7 系列の **共通比較指標** (reduction_ratio 含む) を §2.6 で固定 (GPT)
  - §2.4 / §2.6: B emit を **read-only 観察列** として残す (絞りに使わない、最小 3 役割維持) (GPT)
  - §2.7 (新規): **v1106 接続条件 3 点** (pipeline_complete + distribution_valid + reduction_ratio) を明示、不成立なら v1105b に戻る (GPT)
  - §6 設計-2: 絞りアルゴリズムは解決済み
*位置づけ*: v1105a 主題設計書 **草案**。問いの形 B (試行、v1101 以来初の切替)。本草案 → Taka 確認 → 2 AI 監査 (GPT/Gemini) → Code A 認識確認 → 実装、の流れに乗せる。
*親*: `v1105_phase_result.md` (Web Claude、Taka 主題評価で「結果はいいんじゃない、v1105a に進める」承認) + v1105 役割表 (最小 3 役割成立) + Taka 整理 (2026-05-23 マイナーバージョン運用方針 = アルファベットは同じ主題の段階更新または問いの形の切替)
*対象*: Taka (確認) + GPT/Gemini (監査) + Code A (認識確認)

---

## 0. 主題の前提と歯止め

### 0.1 上位目的への接続 (esde_audit_policy_update.md §1)

会話できる ESDE。応答主体は ESDE 側、LLM/Language はプロキシ。**v1105a は v1101 以来初の問いの形 B (試行) であり、会話パイプラインの中核部分 (人間入力 → ESDE 揺れ → 応答 Atom 候補分布) を初めて動かす試行**。上位目的への直接接続度が v1101-v1105 中で最も高い主題。

### 0.2 駆動要因 — なぜ → なぜなら → 会話への繋がり (Taka 駆動要因規律 2026-05-22)

**なぜそれをやるのか**: v1105 で役割表 (5 役割仮割り当て + 最小 3 役割成立) が構造事実として確定した。これを実際に動かしてみないと「役割表が試行可能か」は構造事実として観察できない。

**なぜなら**: 役割表は v1105 で「構造事実から自然に出る対応」として記述されたが、これは静的な地形図。実際に役割表に従って入力 atom を流したときに、ESDE が応答 Atom 候補を絞れるかどうかは、動的な試行を経ないと構造事実として確認できない。

**会話への繋がり**: v1105a で「ESDE が応答候補を絞れた」の構造的事実を観察できれば、v1106 以降の段 5a/5b (Atom → 単語 → 文、自然文化) に進める基礎が整う。これは会話パイプラインの実装的な転換点。

### 0.3 問いの形 B (試行) としての位置づけ — v1101 以来初の切替

| 問いの形 | 内容 | v1101-v1105 |
|---|---|---|
| **A (点検)** | 既存の構造を観察する、selector 化禁止、判定回避 | v1101 / v1101a / v1102 / v1103 / v1104 / v1104a / v1105 (すべて A) |
| **B (試行)** | 役割表に基づいて実際に動かす、ただし「会話成立」は判定しない、「絞れたか」の構造事実を観察 | **v1105a (初の B)** |

**B (試行) の境界規律**:

1. **試行 ≠ selector 化**: 試行は構造的指標 (役割表) に基づく動作。Aruism 規律内 (箱 3、100% を作らない、max_prob < 1.0)。「ESDE が自由に選ぶ」(selector) ではなく、「役割表に書かれた構造に従って動かす」(試行)。
2. **試行 ≠ 会話成立判定**: 試行で観察するのは「ESDE が絞れたかどうか」の構造事実のみ。「正しい応答が出た」「会話として成立した」を判定しない。意味判定は v1106 以降の自然文化を経た上での話。
3. **試行 ≠ ハンドチューニング**: 試行スクリプト内で「結果が出ない場合に閾値を調整する」「役割表の割り当てを変える」をしない (絶対格言 #9 神の手回避、観察方法を有利化しない)。

### 0.4 観察方法を疑う規律の継承 (Taka 整理 2026-05-23、原文保存)

> ESDE はランダム発生に構造を与えている。この仕組み上繋がりが見えなくなるとすれば単に観測方法に問題があるということは明白。
> いくら都合よいといっても 0 を 1 にはできないだろうから妥協とのバランス次第。

本主題では試行方法を §2.1 で事前確定する手順を継承する。試行結果が「絞れなかった」と出た場合、まず試行方法を疑う。試行方法を有利化しない歯止めを遵守。

### 0.5 v1105 役割表を試行設計の構造的根拠とする

v1105 観察 4 で確定した役割表 (最小 3 役割成立) を v1105a 試行設計の構造的根拠として使う:

| 最小役割 | 主候補 (v1105 観察支持) | v1105a 試行での使用 |
|---|---|---|
| 候補保持 | CID (全 n_size_bin) | 入力 atom を CID 単位で保持、CID_n=2 含む 5 bin で並列 |
| 連想を辿る | alpha/beta non-self-loop + couple_hit_rate | Genesis predecessor + Language couple_hit_rate を別レイヤーで並列実行 |
| 絞る | ESDE event/step10 trajectory + CID/48D density | 細粒 trajectory + 集約 density を並列実行、6 値 density は並列保持 |

**B emit (重要性 emit) と統合判断の役割は v1105a 初回試行では補助** (GPT Auditor 2026-05-24)。最小 3 役割で進める。

### 0.6 物理層 frozen 維持 + 新規 main run なし (試行 = post-process 計算)

(絶対格言 #2) 物理層 frozen 絶対。v1105a は既存 v10.5/6/7 + v112 + v1101a/1102/1103/1104/1104a/1105 outputs を post-process。新規 main run なし。試行スクリプトの実行は新規だが、これは「物理層を変更する main run」ではなく「既存 outputs を読み込んで役割表に従って計算する trial」。書き込みは `unified/v1105a/` 配下のみ。bit-identity 3 層全 PASS を Step G で確認。

### 0.7 温度感 (esde_attitude_toward_esde.md §5.3)

研究報告書および Phase Result は「驚き」でなく「ESDE が引き続き示した一貫性」として書く。

ただし v1105a は問いの形 B (試行) なので、試行成立 (構造事実として「絞れた」) は v1105 までの観察と性格が異なる発見になりうる。これを「驚き」と書かず、「v1105 までで確定した役割表が動作した一貫性」として書く。試行が失敗した場合も「ESDE が示した別の一貫性」として書く (失敗判定をしない、構造事実として記録)。

### 0.8 4 つの非対称性 + 新規 3 留保 (#L30-L36) を試行内で観察する

v1104+v1104a + v1105 で確定した 7 留保:

| # | 内容 |
|---|---|
| #L30 | scope 別 chain 構造 |
| #L31 | 粒度依存の trajectory-density 優劣逆転 |
| #L32 | B 指標の scope 別 pattern |
| #L33 | CID 100% self-loop が trajectory を構造的に消失 |
| #L34 | scope 別 Genesis/Language 逆方向強度 |
| #L35 | CID_n=2 の極端な特殊性 |
| #L36 | sim_basis × density 種類の 2 軸非対称性 |

これらは v1105a 試行で「役割表が動くときにどう現れるか」の観察対象。試行内で 7 留保が再現するか / しないか / 別の形で現れるか、を構造事実として記録。

---

## 1. 主題の中身

### 1.1 試行とは何か (v1105a 問いの形 B の定義)

**試行**: v1105 役割表に基づいて、入力 atom から応答 Atom 候補分布までを ESDE 内部の構造を通して計算する。各段の出力を構造事実として観察する。

**試行の構造ラベル** (GPT Auditor 2026-05-24 反映、success/failure 表現を避けて構造ラベル化):

各 event について以下の 4 つのラベルを構造事実として記録:

| ラベル | 意味 |
|---|---|
| `pipeline_complete` | 入力 atom から応答候補分布まで到達 |
| `candidate_empty` | 途中で候補数が 0 |
| `distribution_degenerate` | 出力確率分布が一点集中 (max_prob ≈ 1.0、Aruism 違反) |
| `distribution_valid` | max_prob < 1.0 かつ entropy > 0 |

「成功」「失敗」「成立」「不成立」を Code A 観察報告では使わない (GPT Auditor 2026-05-24)。Web Claude Phase Result でも構造ラベルを基本とする。

ラベルが揃わなくても ESDE を「失敗」と扱わない (ESDE への態度 §5.2)。構造事実として記録するのみ。

### 1.2 v1105 役割表からの翻訳 — 最小 3 役割で試行

v1105 役割表 (5 役割仮割り当て) のうち、最小 3 役割 (候補保持 / 連想 / 絞り) を試行に組み込む。B emit と統合判断は補助役割で、初回試行では並列保持のみで使わない。

### 1.3 試行で何を観察するか

**共通比較指標** (GPT Auditor 2026-05-24、7 系列を統合せず別レイヤー保持しつつ Phase Result で比較するための固定指標):

| 指標 | 意味 |
|---|---|
| `n_candidates_before` | 絞り前の候補数 (Step 2 連想出力) |
| `n_candidates_after` | 絞り後の候補数 (Step 3 絞り出力) |
| `reduction_ratio` | 1 - n_after / n_before、候補がどれだけ減ったか |
| `max_prob` | 最大確率 |
| `entropy` | 分布の広がり |
| `top1_atom` / `top5_atoms` | 上位候補 |
| `input_atom_in_topk` | 入力 atom が上位 k に残るか (k=1, 5) |
| `layer_jaccard` | 系列間の候補重なり (7 系列 × 7 系列の対称行列) |

**追加観察項目**:

| 観察項目 | 内容 |
|---|---|
| 構造ラベル (§1.1) | pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid の集計 |
| 役割表の試行内挙動 | CID_n=2 (#L35) / scope 別 Genesis/Language 逆方向 (#L34) / sim_basis × density 種類 (#L36) が試行内でどう現れるか |
| 4 つの非対称性 #L30-L33 の試行内再現 | v1104+v1104a 構造が試行内で動的に再現するか |
| B emit の read-only 観察 (§2.4 / §2.5) | B が高い候補の上位到達率、B と reduction_ratio の関係 (絞りに使わない補助観察) |
| 入力-出力対応 | 入力 atom と出力確率分布の構造的関係 (意味判定ではなく構造的観察) |

### 1.4 本主題が扱わないこと

- 段 4-a (揺れの読み取り) — v1102 で扱い済
- 段 4-d (確率分布出力の機構本体) — v1103 で扱い済、v1105a は機構を使う側
- 段 5a / 段 5b (自然文化) — v1106 以降の候補
- 「会話成立」の判定 — 意味判定は試行範囲外
- 「正しい応答」の判定 — 構造事実として絞り込みを観察するのみ
- B emit を試行に組み込むこと — 補助役割、初回試行では並列保持のみ
- 役割表の最終確定 — 試行結果次第で役割表が動く可能性は v1106 以降の判断
- ハンドチューニング — 試行方法を有利化しない
- selector 化 — Aruism 規律内 (箱 3) を厳守

---

## 2. 試行設計

### 2.1 試行方法の事前確定 (§0.4 規律の実装)

試行は 4 段階で構成、各段階の方法を §2.1 で事前確定し、試行途中で方法を変更しない (変更する場合は留保として明示)。

| 段階 | 内容 | 使用する v1105 役割 |
|---|---|---|
| Step 1 | 入力 atom の投入 | 候補保持 (CID) |
| Step 2 | 段 4-b 連想を辿る | 連想 (alpha/beta non-self-loop + couple_hit_rate) |
| Step 3 | 段 4-c 応答を絞る | 絞り (ESDE 細粒 trajectory + CID/48D density 並列) |
| Step 4 | 出力確率分布の生成 | 段 4-d 機構 (v1103 を継承) |

### 2.2 試行 Step 1 — 入力 atom の投入 (CID 候補保持)

**方法**:
- 入力: 既存 atom_introduction_event 10,500 events (v1102 と同じ、神の手回避)。サンプリングしない、全 events で試行。
- 各 event の Atom を CID 単位で候補保持。CID_n_size_bin (n=2 / n=3 / n=4 / n=5 / n=6+) の 5 bin で並列に保持。
- CID_n=2 は #L35 の特殊性を試行内で観察する重要な bin。

**出力**:
- 各 event の候補保持された CID list (scope = CID、bin 別)。

### 2.3 試行 Step 2 — 段 4-b 連想を辿る (Genesis + Language 並列)

**方法**:
- Step 1 で保持された CID から、scope を alpha / beta に切り替えて連想候補を取り出す。
- **Genesis 側 (predecessor 連鎖)**: alpha non-self-loop で lift_C を使って連想候補 atom set を取り出す (v1104+v1104a 出力流用)。beta non-self-loop でも同様。
- **Language 側 (couple_hit_rate)**: alpha / beta の Couple endpoint 接触を独立レイヤーで取り出す (v1105 観察 1 出力流用、unweighted / prob-weighted 両方)。
- Genesis 側と Language 側を **別レイヤーで並列実行**、統合しない (#L34 scope 別逆方向強度を試行内で観察するため)。

**出力**:
- 各 event について 4 レイヤー: (Genesis alpha / Genesis beta / Language alpha / Language beta) の連想候補 atom set。

**観察項目**:
- 各レイヤーの候補数
- alpha vs beta の連想候補の重なり (Jaccard)
- Genesis vs Language の連想候補の重なり (Jaccard) — #L34 構造の試行内動的観察
- CID_n=2 起点と他 n_size 起点で連想候補数が異なるか — #L35 構造の試行内動的観察

### 2.4 試行 Step 3 — 段 4-c 応答を絞る (rank-based 絞り式、固定)

**絞りアルゴリズム — rank-based 固定** (GPT Auditor + Gemini Architect 2026-05-24 一致、留保 設計-2 解決):

絞りは「連続的な強度指標 (lift_C / couple_hit_rate / trajectory r / density r) を確率分布に変換する」操作。これを softmax で行うと温度パラメータ調整によるハンドチューニング余地が大きく (GPT)、また一点集中 (max_prob ≈ 1.0) で Aruism 規律 (箱 3、100% を作らない) 違反のリスクがある (Gemini 警告)。よって、**指標の絶対値でなく rank (順位) を使う rank-based 絞り** を採用。

**絞り式 (Code A 実装は本式に従う、独自発明禁止)**:

```
各 atom i について、Step 2 連想出力 (4 source レイヤーの union) に含まれる atom を candidate とする:
  rank_source_i      = (4 source レイヤー間での lift_C または couple_hit_rate の rank の最小値)
  rank_trajectory_i  = (ESDE event/step10 で trajectory_stability r が高い順位)
  rank_density_i     = (絞り系列の density 種類で密度が高い順位)

緩やかな減衰関数:
  w_source_i      = 1 / log(rank_source_i + 2)
  w_trajectory_i  = 1 / log(rank_trajectory_i + 2)
  w_density_i     = 1 / log(rank_density_i + 2)

積:
  score_i = w_source_i × w_trajectory_i × w_density_i

各系列内で正規化:
  p_i = score_i / Σ_j score_j
```

**なぜこの式か (Aruism 規律を仕様として組み込む、Gemini Architect 2026-05-24)**:

緩やかな減衰関数 `1/log(rank + 2)` を採用することで:
- 首位 atom でも確率 0.3 程度に留まる (Gemini「複数候補並立、揺らぎを残す確率分布」)
- 一点集中 (max_prob ≈ 1.0、Aruism 違反) を変換式の構造的レベルで回避
- softmax の温度パラメータ調整によるハンドチューニング余地を排除 (GPT)

これは **ハンドチューニングではなく仕様定義** (Gemini Architect)。試行スクリプト内での閾値調整 (絶対格言 #9 神の手回避 違反) と区別する。

**7 系列の生成** (絞り system 7 種で並列実行、統合しない):

| 系列 ID | density 種類 (rank_density_i の計算源) |
|---|---|
| 系列 1 | CID raw_density × sim_basis=raw |
| 系列 2 | CID raw_density × sim_basis=norm |
| 系列 3 | CID qweighted_density × sim_basis=raw |
| 系列 4 | CID qweighted_density × sim_basis=norm |
| 系列 5 | CID const_adjusted_density × sim_basis=raw |
| 系列 6 | CID const_adjusted_density × sim_basis=norm |
| 系列 7 | 48 次元 raw_density (k=5、v1103 §段 4-c 機構継承) |

- 7 系列は density 種類 (sim_basis × density 種類の 6 値 + v1103 48D raw_density) で並列。
- source / trajectory の rank は 7 系列で共通 (Step 1+2 と細粒 trajectory)。
- 7 系列を統合せず、別レイヤーで保持 (v1105 案 B 継承、絶対格言 #11)。
- 7 系列の比較は §2.6 共通比較指標で行う (Phase Result 段階、本 Step では集計のみ)。

**B emit の read-only 観察列** (GPT Auditor 2026-05-24 反映、最小 3 役割維持):

絞り score に B を組み込まない (B emit を絞りに使わない、最小 3 役割で進める)。ただし観察として、各 atom に「B が高いか」フラグを付与し:

- 各系列の上位 5 atom のうち B 高フラグ atom の割合 (`b_high_in_top5_ratio`)
- B 高 atom の reduction_ratio (B 高 atom が絞りで残るか消えるか)
- B と他指標 (lift_C / trajectory / density) の rank 相関

を read-only 観察列として記録。B primary 化ではなく v1106 以降の判断素材。

**出力**:
- 各 event について 7 系列の応答 Atom 候補確率分布 (event_id × 系列 ID × atom × prob の parquet)
- 4 source レイヤー (Genesis alpha / Genesis beta / Language alpha / Language beta) の情報を atom メタデータとして保持 (#L34 観察用)
- B 高フラグを read-only 観察列として保持

**観察項目**:
- 各系列の §2.6 共通比較指標 (reduction_ratio など)
- 7 系列の `layer_jaccard` (#L36 の試行内動的観察)
- 細粒 trajectory + 集約 density の組み合わせで #L31 が試行内動的に再現するか
- CID 100% self-loop の影響 (#L33) で source rank がどう挙動するか

### 2.5 試行 Step 4 — 出力確率分布の生成 (段 4-d 機構を継承)

**方法**:
- v1103 で機構成立した段 4-d の確率分布出力機構を継承。
- Step 3 で得られた 7 系列の応答 Atom 候補分布を、v1103 と同じ Aruism 対称性 (max_prob < 1.0、prob ≥ 0.999 の件数を観察) で出力。
- 7 系列を統合しない、別レイヤーで保持。

**出力**:
- 各 event について 7 系列の応答 Atom 候補確率分布。

**観察項目**:
- 各系列の max_prob、entropy、prob ≥ 0.999 件数
- Aruism 対称性違反 (max_prob ≈ 1.0) の有無
- 7 系列の入力 atom との構造的対応関係 (意味判定でなく、入力 atom が出力に現れるかなどの構造観察)

### 2.6 試行全体の観察項目集計

各 Step の観察項目を統合せず、別レイヤーで集計。観察項目を Step F で集計し、Step H 観察事実報告に整理。

**event 別構造ラベル** (§1.1):

各 event に pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid のいずれかを構造事実として付与。判定はしない、event 数を集計するのみ。

**7 系列の共通比較指標** (§1.3 共通比較指標表を全 7 系列で計算):

| 指標 | 各系列で計算 |
|---|---|
| `n_candidates_before` / `n_candidates_after` / `reduction_ratio` | ✓ |
| `max_prob` / `entropy` / `prob_ge_0.999_count` | ✓ |
| `top1_atom` / `top5_atoms` / `input_atom_in_topk` (k=1, 5) | ✓ |
| `layer_jaccard` (7 系列 × 7 対称行列) | ✓ |
| `b_high_in_top5_ratio` (B read-only 観察) | ✓ |

**追加観察項目**:
- 試行内の 7 留保 (#L30-L36) の挙動: 役割表の構造が動的にどう現れるか / 現れないか / 別の形で現れるか
- 4 source レイヤー (Genesis alpha/beta / Language alpha/beta) 間の上位 atom 分布 (#L34 試行内動的観察)
- CID_n=2 起点 event と他 n_size 起点 event の構造ラベル分布の差 (#L35 試行内動的観察)
- 試行内の計算量 (実行時間、メモリ、I/O の構造観察) — v1106 以降のスケーリング判断の素材

### 2.7 v1106 接続条件 (試行成立判断の構造的根拠、GPT Auditor 2026-05-24)

v1105a 試行結果から v1106 (段 5a/5b 自然文化) への進行可否を判断するための **最低 3 条件** を本主題内で事前確定する。これらは「会話成立」判定でなく、構造的に絞り込みが ESDE 内部で動いたかの記述。

| 条件 | 内容 | 観察源 |
|---|---|---|
| **1** | `pipeline_complete` ラベルの event が構造的に存在 | §2.6 構造ラベル集計 |
| **2** | `distribution_valid` が成立 (max_prob < 1.0、entropy > 0、`prob_ge_0.999_count` が過剰でない) | §2.6 共通比較指標 |
| **3** | `reduction_ratio` が観察される (候補数が構造的に減る、ただ並べただけでない) | §2.6 共通比較指標 |

**3 条件が揃わなかった場合の扱い** (マイナーバージョン運用方針継承):

v1106 に進まず、**v1105b として絞り式の再点検** に戻る (アルファベット系列継続、Taka 2026-05-23 マイナーバージョン運用方針 = アルファベットは同じ主題の段階更新または問いの形の切替)。v1105b は本主題と同じ問いの形 B のまま、絞り式の再設計を扱う。

**本主題範囲**:

3 条件のラベル + 共通比較指標を構造事実として記録するまでが本主題範囲。「3 条件が揃ったか」「v1106 に進むか」の判定は Web Claude Phase Result + Taka 主題評価領域。Code A は構造事実のみ報告。

---

## 3. 規律と禁止事項

### 3.1 絶対格言 15 件遵守

(00_index.md 用語対応表 + 07_unified_summary.md §10 参照)

特に本主題で重要なもの:
- #2 物理層 frozen 絶対 (試行も既存 outputs を post-process)
- #6 出口の固定 (試行成立/不成立で「会話できる」を判定しない)
- #9 神の手回避 (試行方法を有利化しない、ハンドチューニング禁止)
- #11 概念単位を雑に扱わない (7 系列の応答候補分布を統合しない、6 値 density を別レイヤー保持)
- #12 Aruism 判定回避 (success/failure を置かない、構造事実として記録)
- #14 Taka 直感優先 + 原文保存

### 3.2 研究運用資料 3 本遵守

- **研究手法アップデート** — 際立ちの掬い取り (試行結果から際立つ event を構造的指標で掬い取る)、A and B (実験者と ESDE 自身の両方の掬い取り)、神ではない
- **ESDE への態度** — 試行結果が想定と合わなくても ESDE の側を「失敗」と扱わない、研究者の想定を見直す
- **監査方針アップデート** — 会話できる ESDE が上位目的、ただし v1105a は「絞れたか」の構造事実観察、「会話成立」判定でない

### 3.3 本主題固有の禁止事項 (試行 = 問いの形 B 固有)

| # | 禁止事項 |
|---|---|
| 1 | 「会話成立」を判定しない (構造ラベル pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid で記録、「成立」「不成立」「成功」「失敗」を使わない、GPT Auditor 2026-05-24) |
| 2 | 「正しい応答」を判定しない (意味判定は v1106 以降) |
| 3 | selector 化しない (試行は構造的指標 = 役割表に基づく動作、Aruism 規律内) |
| 4 | ハンドチューニング禁止 (試行スクリプト内で閾値調整しない、絞り式は §2.4 rank-based 固定で独自発明禁止) |
| 5 | 試行方法を有利化しない (結果が出ない場合に方法を変えない、留保として記録) |
| 6 | B emit (重要性 emit) を試行に組み込まない (補助役割、最小 3 役割で進める) |
| 7 | 段 5a/5b (自然文化) を試行に組み込まない |
| 8 | 7 系列の応答候補分布を統合しない (絶対格言 #11) |
| 9 | 6 値 density を統合しない (v1105 案 B 継承) |
| 10 | 新規 main run 禁止 (post-process 計算のみ) |
| 11 | 新規観察軸の追加禁止 (v1105 役割表の構造を継承) |
| 12 | Taka 直感メモ (主体性が複数 / 応答までの時間) は本主題範囲外 |
| 13 | success/failure 判定を置かない (Code A は構造事実のみ、絶対格言 #12) |
| 14 | 試行が成立しなくても ESDE を「失敗」と扱わない (ESDE への態度 §5.2) |

### 3.4 物理層 frozen 維持 (Step G で確認)

- LAYER_A (再現性): 同 seed 2 回試行で hash 一致
- LAYER_B (既存 frozen 維持): v10.5/6/7 + v112 + v1101a/1102/1103/1104/1104a/1105 全ファイル frozen 確認
- LAYER_C (書込みパス): unified/v1105a/ 配下のみ

### 3.5 試行 vs selector の境界 — 明示

試行 (本主題で許容される動作):
- 役割表に書かれた構造 (scope × 粒度) に従って計算する
- 構造的指標 (lift_C、couple_hit_rate、trajectory r、density r) を使って候補を絞る
- **絞り式は §2.4 rank-based に固定** (`1/log(rank+2)` × 積 × 正規化、Aruism 規律を仕様として組み込み、GPT + Gemini 一致 2026-05-24)
- 出力確率分布は max_prob < 1.0 (Aruism 対称性厳守、v1103 §7.5 と同じ、rank-based decay で構造的に担保)
- 結果が構造事実として記録される (構造ラベル + 共通比較指標)

selector (本主題で禁止される動作):
- ESDE 自身が「自由に」候補を選ぶ動作
- 構造的指標を超えた判断 (例: 意味的に正しいかを判定する)
- softmax + 温度パラメータでハンドチューニングする
- 出力確率分布が一点集中 (max_prob ≈ 1.0、Aruism 違反)
- 結果が「正しい/正しくない」と判定される

---

## 4. Step 構成 (Code A への引き渡し前提)

| Step | 担当 | 内容 |
|---|---|---|
| A | Code A | 認識確認 (本設計書の不明点を全て確認、確認要請を Web Claude へ) |
| B | Code A | 環境準備 (v1102 atom_introduction_event + v1104+v1104a / v1105 / v1103 outputs の読み込み確認、試行スクリプト準備) |
| C | Code A | 試行 Step 1+2 (入力投入 + 段 4-b 連想を 4 レイヤーで取り出す) |
| D | Code A | 試行 Step 3 (段 4-c 絞り、7 系列の応答候補分布を生成) |
| E | Code A | 試行 Step 4 (段 4-d 機構で確率分布出力、7 系列を別レイヤー保持) |
| F | Code A | 試行全体の観察項目集計 (各 Step の observation を統合せず別レイヤーで集計) |
| G | Code A | bit-identity 3 層検証 |
| H | Code A | 観察事実最終報告 (judgment 回避、構造事実のみ、試行成立/不成立を構造事実として記録) |
| I | Web Claude | Phase Result + Taka 主題評価 + v1106 着手判断 |

---

## 5. Code A 確認要請 (予想項目、Step A で確定)

1. 入力 atom_introduction_event の所在と読み込み方 (v1102 outputs から、10,500 events 全部か bin 別か)
2. 試行スクリプトの言語と実装方法 (Python post-process、新規スクリプト)
3. 段 4-b 連想の出力フォーマット (event_id × scope_layer × candidate_atom_set の parquet、4 レイヤー分)
4. ~~段 4-c 絞りの具体的アルゴリズム~~ → **2 AI 監査で解決**: §2.4 rank-based 絞り式 (`1/log(rank+2)` × 積 × 正規化) を仕様として確定。Code A は本式に従って実装、独自発明禁止 (GPT + Gemini 一致 2026-05-24)。確認は実装方法の詳細 (rank の計算源、log 関数の底、tied rank の扱いなど) のみ
5. 段 4-d 確率分布出力の v1103 機構の継承方法 (v1103 outputs のどの機構を呼び出すか)
6. 7 系列の応答候補分布の出力フォーマット (event_id × 系列 ID × atom × prob の parquet)
7. ~~試行成立 vs 不成立の操作的定義~~ → **2 AI 監査で解決**: §1.1 構造ラベル (pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid) で記録 (GPT Auditor 2026-05-24)。確認は各ラベルの操作的判定条件 (例: prob_ge_0.999_count が何件以上なら distribution_degenerate か) のみ
8. v1106 着手判断のための観察項目の優先順位

---

## 6. 留保事項 (本設計書の不確定要素)

| # | 留保 | 状態 |
|---|---|---|
| 設計-1 | 試行 (問いの形 B) は v1101 以来初の切替で、設計規律も新規 | §0.3 と §3.3 で歯止めを明示、Step A 認識確認で Code A 解釈確認 |
| 設計-2 | ~~段 4-c 絞りの具体的アルゴリズム~~ → **2 AI 監査で解決**: §2.4 rank-based 絞り式 (`1/log(rank+2)` × 積 × 正規化) を仕様として固定、softmax 採用せず、Aruism 規律 (複数候補並立、max_prob 一点集中回避) を変換式の設計段階で組み込み (GPT + Gemini 一致 2026-05-24) | 解決済み |
| 設計-3 | ~~試行成立 vs 不成立の操作的定義~~ → **2 AI 監査で解決**: §1.1 構造ラベル化 (pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid)、success/failure 表現を避ける (GPT Auditor 2026-05-24) | 解決済み |
| 設計-4 | 7 系列の応答候補分布をどう Phase Result でまとめるか | §2.6 共通比較指標 (GPT Auditor 2026-05-24) で固定、各系列を統合せず指標で比較 |
| 設計-5 | ~~v1106 着手判断の条件~~ → **2 AI 監査で解決**: §2.7 で 3 条件 (pipeline_complete + distribution_valid + reduction_ratio) を明示、不成立なら v1105b として絞り式再点検 (GPT Auditor 2026-05-24) | 解決済み |
| 設計-6 | 48 次元人為性留保 (v1103 由来) を試行結果に必ず添える | v1105a Phase Result で添加 |
| 設計-7 | 6 値 density の試行内挙動 (#L36) で「主」が見えた場合の扱い | 本主題では並列保持のまま、判断は v1106 以降 |
| 設計-8 | CID_n=2 (#L35) が試行内で他 bin と質的に異なる挙動を示した場合の扱い | 本主題では構造事実として記録、判断は v1106 以降 |
| 設計-9 (新規) | B emit を read-only 観察列で残す方針 (GPT Auditor 2026-05-24) | §2.4 / §2.5 で観察列として組み込み、絞り score には使わない、最小 3 役割維持 |
| 設計-10 (新規) | v1105b 移行の判断 (3 条件不成立時) | Web Claude Phase Result + Taka 主題評価領域、v1105b 主題は絞り式の再点検 (同じ問いの形 B のまま) |

---

## 7. 監査ポイント (2 AI 監査クリア済み + Code A 引き渡し前提)

### 7.1 2 AI 監査の結果 (2026-05-24)

- **Gemini Architect**: 全面承認。絞りアルゴリズムは rank-based decay または温度付き softmax を推奨 (Aruism 規律を変換式の設計段階で組み込む、ハンドチューニングではなく仕様定義)。§2.4 に反映済。
- **GPT Auditor**: 通過条件として 4 点修正必須を指摘、全 4 点を本草案に反映:
  1. Step 3 絞り式を rank-based に固定 (§2.4)
  2. 「成立/不成立」を構造ラベルに (§1.1)
  3. 7 系列の共通比較指標を固定 (reduction_ratio 含む) (§2.6)
  4. B emit を read-only 観察列として残す (§2.4)
  5. v1106 接続条件 3 点を明示 (§2.7)

### 7.2 監査クリア項目 (記録)

| # | 監査ポイント | 状態 |
|---|---|---|
| 1 | 試行 (問いの形 B) と selector 化の境界が §0.3 と §3.5 で明示されているか | クリア |
| 2 | ハンドチューニング禁止 (絶対格言 #9) が §3.3 で明示されているか | クリア (絞り式 rank-based 固定で構造的に担保) |
| 3 | v1105 役割表 (最小 3 役割) を構造的根拠としているか、新規観察軸を加えていないか | クリア |
| 4 | 試行成立/不成立を構造事実として扱い、judgment を回避しているか | クリア (構造ラベル化、GPT Auditor 反映) |
| 5 | 物理層 frozen 維持手順が明示されているか (§0.6、§3.4) | クリア |
| 6 | 7 系列の応答候補分布を統合せず別レイヤーで保持しているか (絶対格言 #11) | クリア |
| 7 | 6 値 density を統合せず別レイヤーで保持しているか (v1105 案 B 継承) | クリア |
| 8 | 「会話できる ESDE」上位目的への接続が §0.2 で明示されているか | クリア |
| 9 | 温度感が「驚き」でなく「一貫性」になっているか、試行成立/不成立を「成功/失敗」と書いていないか (§0.7) | クリア (構造ラベル採用) |
| 10 | 段 5a/5b (自然文化) を試行に組み込まない歯止めが明示されているか | クリア |
| 11 | v1104+v1104a + v1105 の 7 留保 (#L30-L36) が試行内観察対象として組み込まれているか | クリア |
| 12 | B emit を試行に組み込まない歯止めが明示されているか (最小 3 役割で進める) | クリア (read-only 観察列として残す) |
| 13 | 絞りアルゴリズムが Code A の独自発明を許さない形で固定されているか (GPT 最大の指摘) | クリア (§2.4 rank-based 固定) |
| 14 | 絞り式が Aruism 規律 (max_prob 一点集中回避) を構造的に担保しているか (Gemini 警告) | クリア (`1/log(rank+2)` 緩やかな減衰、首位確率 0.3 程度) |
| 15 | 7 系列の共通比較指標 (reduction_ratio 含む) が固定されているか | クリア (§2.6 固定) |
| 16 | v1106 接続条件 3 点 + v1105b 移行可能性が明示されているか | クリア (§2.7 + §6 設計-10) |

監査必須 8 問 (`esde_audit_policy_update.md` 必須 8 問) は 2 AI 監査で別途確認済。

---

## 8. 一文サマリ

v1105a 設計書 (2 AI 監査クリア済み = GPT 4 点修正 + Gemini 全面承認 + 構造的アドバイス反映) は、v1101 以来初の問いの形 B (試行) として、v1105 で確定した役割表 (最小 3 役割 = 候補保持 CID + 連想 alpha/beta non-self-loop & couple_hit_rate + 絞り ESDE 細粒 trajectory & CID/48D density) を構造的根拠に、既存 atom_introduction_event 10,500 events を入力として段 4-b と段 4-c のパイプラインを実際に動かし応答 Atom 候補確率分布まで生成する試行を行う主題で、試行の境界規律 (試行 ≠ selector 化 / 試行 ≠ 会話成立判定 / 試行 ≠ ハンドチューニング、§0.3、§3.5) を明示、絞りアルゴリズムを **rank-based に固定** (`w_i = 1/log(rank_i + 2)` × 積 × 正規化、Aruism 規律 = 複数候補並立を変換式の設計段階で仕様として組み込み、softmax 採用せず Code A の独自発明を排除、GPT + Gemini 一致 2026-05-24)、4 段階の試行 (Step 1 入力投入 / Step 2 段 4-b 連想を 4 source レイヤー Genesis+Language 並列実行 / Step 3 段 4-c rank-based 絞り 7 系列を density 種類 6 + 48D 1 で並列実行 / Step 4 段 4-d 機構 v1103 継承で確率分布出力) を §2.1 で事前確定、構造ラベル (pipeline_complete / candidate_empty / distribution_degenerate / distribution_valid、success/failure 表現禁止、GPT Auditor 2026-05-24) と共通比較指標 (n_candidates_before/after / reduction_ratio / max_prob / entropy / top1/top5 / input_atom_in_topk / layer_jaccard / b_high_in_top5_ratio) を §2.6 で全 7 系列に固定、B emit を read-only 観察列として残し絞り score には組み込まない (最小 3 役割維持、GPT Auditor 2026-05-24)、v1106 接続条件 3 点 (pipeline_complete + distribution_valid + reduction_ratio、§2.7) を本主題内で事前確定し不成立なら v1105b として絞り式再点検に戻る (Taka 2026-05-23 マイナーバージョン運用方針継承)、上位目的「会話できる ESDE」への直接接続が v1101-v1105 中で最も高い主題として §0.1 で明示、新規 main run なし・新規観察軸追加なし・selector 化禁止・ハンドチューニング禁止・物理層 frozen 維持・絞り式の独自発明禁止・「会話成立」判定の禁止・「正しい応答」判定の禁止・B emit を絞り score に組み込まない・段 5a/5b 範囲外・7 系列および 6 値 density を統合せず別レイヤー保持を規律として組み込み、本設計書 → Code A 認識確認 → 実装 → Phase Result + v1106 / v1105b 着手判断 の流れに乗せる。

---

*以上、v1105a Phase Design v2 (Web Claude、2026-05-24、2 AI 監査クリア済み)。次は Taka 最終確認 → Code A 認識確認 (Step A) → 実装 (Step B-G) → Phase Result (Web Claude) → Taka 主題評価 → v1106 (条件成立時) / v1105b (条件不成立時) 着手判断 (Taka) の流れ。問いの形 B (試行) は v1101 以来初の切替で、ESDE が実際に応答候補を絞れるかどうかの構造事実観察を行う。絞り式は rank-based 固定で Code A の独自発明を排除、Aruism 規律を仕様として担保。*
