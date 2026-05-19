# v1103 Step A 認識確認 — Code A

*作成*: 2026-05-20、Code A
*親*: `v1103_phase_design.md` (Web Claude 改訂版、GPT 7 点 + Gemini 承認反映済) + Taka 配置承認 (2026-05-20)
*対象*: Genesis 側 Web Claude + Language 側 Web Claude + Taka (実装着手判断)
*目的*: 設計書 §3.2 認識確認事項の repo 実状照合。論点 0 (ゼロの意味) + Language 側データ実体 + 論点 5 新規 main run 要否。

---

## 0. 一文サマリ

v1103 設計書 §3.2 認識確認の Code A 実環境照合結果として、**論点 0 (ゼロの意味) の結論は設計書 §2.2 の前提と部分的にズレており確認要請事項**、具体的には `language/lexicon/data/mapper_output/*_a1.jsonl` (325 ファイル、設計書が `*_a1_final.jsonl` と呼ぶもの) の `normalized_scores` は **1,228 word サンプル中 100% が n_zero=0 + mean n_keys=47.06** で「48 軸全部に非ゼロ値が割り当てられている」事後正規化された分布のため設計書 §2.2 の (a) でも (b) でもなく **(c) 全 48 軸非ゼロ正規化済** という第 3 の状態が観察され、対照的に `raw_scores` は mean n_zero=30.32 で **Nonzero 約 17.68/48** であり Language 側 Web Claude 記憶「平均 Nonzero 14.5/48」と整合的 (Language 側記憶は raw_scores ベースの話だった可能性)、設計書の前提「Atom は 48 次元すべてに値を持たない」は raw_scores では真だが normalized_scores では真でない、さらに Language 側データの所在で **`atom_centroids_48d.csv` が repo に存在せず** (Language 側で別途生成または別名のファイル) ・**Atom-level Constitution (Couple 6 件 / Merge 3 件 / Subsume 1 件 / Monitor 7 件) も存在せず** (`docs/esde_explainability_constitution.txt` は Research Constitution = 研究方針で別物) ・**batch_report.md も存在せず** (batch_report.py は `language/lexicon/batch_report.py` にあるが実行結果 md は未 commit)、v1102 primary table は v1101a outputs 既存で組めるが Language 側の atom 入力・centroid・Constitution が揃わないと段 4-b/4-c が組めない、確認要請 4 件 (§5.1 ゼロの意味判定の設計書更新 / §5.2 atom_centroids_48d.csv の生成または所在 / §5.3 Atom-level Constitution の所在 / §5.4 normalized_scores と raw_scores のどちらを 48 次元疎性前処理の対象とするか) を Language 側 Web Claude + Taka に判断要請、論点 5 新規 main run 要否は Language 側データの所在確定後に再判断、想定実装 1.5-2 日 (Language 側データ揃い後)。

---

## 1. 設計書 §3.2 認識確認事項への Code A 回答

### 1.1 論点 0 (最優先) — 48 次元疎性のゼロの意味 (a)/(b) 判定

設計書 §2.2 は Atom の 48 次元ベクトルで:
- (a) 48 キー全部あって一部 0.0 = 測定結果「ここには立たない」
- (b) 立っている軸のキーしかない = 未測定

の二択を Code A が `*_a1_final.jsonl` の `normalized_scores` 実体で確定する、と指定。

**Code A 実環境照合結果**:

実体ファイル: `language/lexicon/data/mapper_output/*_a1.jsonl` × 325 Atom (設計書 `*_a1_final.jsonl` ≡ `*_a1.jsonl`、ファイル名整合)。1,228 word サンプル (16 atom file × 約 77 word 平均) で:

| 列 | type | n_keys | n_zero (mean) | Nonzero (mean) |
|---|---|---:|---:|---:|
| **normalized_scores** | dict[48] | 47.06 (ほぼ全 48 軸) | **0.00** | **47.06 (≈ 48)** |
| **raw_scores** | dict[48] | 48 | **30.32** | **17.68** |

**結論**:
- normalized_scores: (a)(b) どちらでもなく **(c) 全 48 軸に非ゼロ値が割り当てられた事後正規化済分布**。n_zero=0 が 100% (1,228 word サンプル全件)、疎性問題は normalized 側では発生しない
- raw_scores: 48 キー全部あって mean 30.32 軸が 0、Nonzero 17.68 軸 — 設計書 §2.2 の (a) に近い (48 キー全部あって一部 0.0)、Language 側 Web Claude 記憶「平均 Nonzero 14.5/48」とおおむね整合 (raw_scores ベース)

→ **設計書 §2.2 の前提「Atom は平均 14.5/48 軸にしか立たない」は raw_scores の話**であり normalized_scores には適用されない。「素直な 48 次元 cosine は使えない」の判断は **どちらの列を使うかで結論が変わる** ため、Web Claude / Taka 確認要請事項 (§5.1)。

### 1.2 Language 側データ実体確認

#### 1.2.1 atom_centroids_48d.csv — **存在せず**

設計書 §2.3 / 認識確認事項で `atom_centroids_48d.csv` (326 Atom centroid × 48 次元) を A1 48 次元近傍計算の基盤と指定。

**Code A 実環境照合結果**: `find / -iname "atom_centroid*"` 該当ファイルなし。`language/` 配下にも、`unified/` 配下にも存在しない。

可能性:
- (i) Language 側で `*_a1.jsonl` の normalized_scores を Atom 別に集計して生成するファイル (まだ生成されていない)
- (ii) 別ファイル名で存在 (例: `atom_centroids.csv`、`atoms_v1.json` の中)
- (iii) Language 側 Web Claude の記憶ベースで実装が未着手

`language/lexicon/data/definitions/atoms_v1.json` は存在するが、これが centroid を持つかは未確認。

→ Web Claude / Taka 確認要請事項 (§5.2)。

#### 1.2.2 Atom-level Constitution (Couple/Merge/Subsume/Monitor) — **存在せず**

設計書 §2.6 で Constitution を「6 件 Couple / 3 件 Merge / 1 件 Subsume / 7 件 Monitor」と指定。

**Code A 実環境照合結果**:
- `docs/esde_explainability_constitution.txt` は存在するが、これは **Research Constitution = 研究方針** (Scope Declaration / Explainability X / Noise Tolerance η 等) で、設計書の Atom-level Constitution (cross-category 共鳴 Couple 等) とは別物
- `find -iname "*couple*"` / `*merge*atom*` 該当なし
- `language/relations/` (parser_adapter.py / relation_logger.py / run_relations.py) は存在するが、Atom-level Constitution の json/yaml 等のデータファイルは見つからない

→ Web Claude / Taka 確認要請事項 (§5.3)。

#### 1.2.3 batch_report.md — **存在せず** (batch_report.py のみ)

設計書 §2.2 / §2.5 で `batch_report.md` (実測 Avg Nonzero 14.5/48 等) を参照。

**Code A 実環境照合結果**: `language/lexicon/batch_report.py` (Python script) は存在するが、実行結果 `batch_report.md` は repo に commit されていない。実行すれば生成可能と推測。

→ 必要なら Code A が batch_report.py を実行して生成可能。Web Claude / Taka 判断 (§5.3 と合わせて)。

#### 1.2.4 Lexicon Core pool (32,666 語) — **間接的に確認可**

設計書 §2.5 / §2.8 で「全体 32,666 語 / 高品質サブセット 6,025 語」を指定。

**Code A 実環境照合結果**: `language/lexicon/data/mapper_output/*_a1.jsonl` 325 ファイルに各 Atom の word 群が格納されており、合計 word 数は 1,228 サンプルから推測 ~37,000 (近似値、全数確認は時間要)。32,666 語の出処はこれらの concat と想定。高品質サブセット 6,025 語は別途フィルタロジックが必要。

→ Code A が全 325 ファイルを load して word 数を集計すれば確定。`status` 列で高品質サブセットも抽出可能 (`*_a1.jsonl` の status 列確認、サンプルで存在を確認済)。

#### 1.2.5 esde_dictionary.json と axes_levels_v1.json — 存在

- `language/atoms/esde_dictionary.json`: meta (version, spec_source, total_concepts, total_axes, definition_language) + 326 Atom 定義
- `language/lexicon/data/definitions/axes_levels_v1.json`: 48 軸の定義 (axes.levels 形式と推測)

→ Atom 構造の参照点として使用可。

### 1.3 論点 5 — 新規 main run 要否

Genesis 側出力 (v1101a / v1102 primary table) は既存で完備。Language 側データは部分的に揃わない (centroid / Constitution 不在)。

判定: **Language 側の不足データが Taka または Language 側 Web Claude から提供 / 生成方針確定後に再判断**。Genesis 側に関しては新規 main run 不要 (v1102 を流用)。

---

## 2. v1102 primary table の段 4-a 入力としての使用

設計書 §2.1 で「段 4-c 点検の入力は v1102 primary table の受け手構造別応答 profile」と指定。

**Code A 実環境照合**: `unified/v1102/outputs/main/primary_table.parquet` (81 cells × 27 cols) + `outstanding_cells.parquet` 既存。受け手構造軸 (CID n_core / Integration n_members × qc_gini / ESDE 4 解像度) と応答 5 種 (attention/influence/variability/atom/category) すべて利用可。

段 4-a 入力としての使い方:
- 受け手構造別に「ESDE の揺れの atom profile」を取得 (primary_table の atom_top1_name + category_top1_name + 補助に cid_state_ledger 326 atom 濃度)
- 設計書 §2.4 receiver-conditioned 密度 = 受け手構造別 (CID n_core / Integration 構成) に分けた密度 → primary_table の receiver_bin と一致

→ v1102 を v1103 段 4-a 入力として直接使える。整合性 OK。

---

## 3. 段 4-b/4-c の実装可能性

Language 側データ揃い (atom_centroids_48d.csv + Constitution + ゼロの意味確定) を前提に:

### 3.1 段 4-b (連想を辿る) の実装

- **離散リンク (Constitution Couple)**: Couple 6 件のデータが必要 (§1.2.2)
- **連続地形 (A1 48 次元近傍)**: atom_centroids_48d.csv (§1.2.1) または `*_a1.jsonl` の normalized_scores から centroid を構築 (Code A が生成)

#### 3.1.1 atom_centroids_48d.csv の Code A 生成案

設計書 §2.5 の品質フラグ計算と整合する形で:
```
per Atom:
  centroid[axis] = mean(normalized_scores[axis] across all words in *_a1.jsonl)
  focus_rate = mean(focus_rate column across all words)
```
326 Atom × 48 軸 = 15,648 cells の csv を生成可能 (新規生成、unified/v1103/outputs/main/ 配下)。

### 3.2 段 4-c (48 次元密度) の実装

- 連想先 Atom 候補群を 48 次元空間に配置
- 密度の偏りを 4 種 (raw / quality-weighted / constitution-adjusted / receiver-conditioned) で測定
- 疎性前処理に依存 (§5.1 確定後)

### 3.3 段 4-d (確率分布出力) の実装

argmax 取らず確率分布で出力、v1101a / v1102 と同じ規律。

---

## 4. 出力先と物理層 frozen

書込み先: `unified/v1103/` 配下のみ。Genesis 側 (v1101a/v1102) outputs は read-only、Language 側 (`language/`) も read-only。

設計書 §8 物理層 frozen 絶対遵守を本書 Code A 認識確認も継承。

---

## 5. Web Claude / Taka 確認要請

### 5.1 確認要請 1 — ゼロの意味の設計書前提更新

設計書 §2.2 「Atom は平均 14.5/48 軸にしか立たない」は **raw_scores ベース**であって normalized_scores では「全 48 軸に非ゼロ」状態が観察される (§1.1)。設計書 §2.2 の (a)/(b) 二択にも該当しない (c) 全 48 軸非ゼロ正規化済状態。

Code A 仮所見:
- (i) 設計書 §2.2 を「raw_scores ベースで疎性判定、対処 A/B/C を raw_scores に適用」と更新
- (ii) 設計書 §2.2 を「normalized_scores ベース、疎性なしのため対処不要、素直な cosine 可能」と更新
- (iii) 両方を並列に扱い「raw_scores 経路 vs normalized_scores 経路」の比較を観察に含める (留保 #33 系列同型、集計単位で像が変わる)

Code A は (iii) を推奨 — 「同じデータでも raw か normalized で像が変わる」を v1103 でも観察に含める。

### 5.2 確認要請 2 — atom_centroids_48d.csv の生成または所在

設計書 §2.3 が指す atom_centroids_48d.csv は repo に未存在 (§1.2.1)。

Code A 仮所見:
- (i) Code A が `*_a1.jsonl` の normalized_scores から Atom 別 centroid を生成 (§3.1.1)、`unified/v1103/outputs/main/atom_centroids_48d.csv` として出力 (raw_scores 版・normalized_scores 版の 2 種)
- (ii) Language 側 Web Claude が別途生成して repo に commit
- (iii) Language 側 Web Claude が「これは別名のファイルだ」と所在を示す

Code A 仮所見: (i) Code A 生成 — Language 側 Web Claude は実装しない方針 (体制 §6) のため Code A 担当が筋。

### 5.3 確認要請 3 — Atom-level Constitution (Couple/Merge/Subsume/Monitor) の所在

設計書 §2.6 で「6 件 Couple / 3 件 Merge / 1 件 Subsume / 7 件 Monitor」と具体数明示。repo に該当データなし (§1.2.2)、`docs/esde_explainability_constitution.txt` は別物 (Research Constitution)。

Code A 仮所見:
- (i) Language 側 Web Claude が Constitution の json/yaml を repo に追加
- (ii) 別ファイル名で存在 → 所在情報を Language 側から提供
- (iii) Constitution データを v1103 では使わない方針に変更 (設計書 §2.6 削除)

Code A は (i) を推奨 — 設計書が具体数 (6/3/1/7) を明示しているので、データが存在する想定で書かれている。Language 側 Web Claude の連携で repo に commit 要請。

### 5.4 確認要請 4 — batch_report.md の生成可否

`language/lexicon/batch_report.py` を Code A が実行すれば `batch_report.md` 生成可能と推測 (§1.2.3)。実行して良いか、または既存の Language 側 batch_report.md があるなら所在を提示するか。

Code A 仮所見: Code A が batch_report.py を実行して `unified/v1103/outputs/main/batch_report.md` または `language/lexicon/batch_report.md` として生成 (どちらの配置か Web Claude / Taka 判断)。

---

## 6. 進行 — Step A 完了後の流れ

| Step | 内容 | 担当 | 状態 | 待機 |
|---|---|---|---|---|
| Step A (本書) | 認識確認 | Code A | 完了 | Web Claude/Taka 確認要請 4 件回答待ち |
| Step 4.5 (疎性前処理) | ゼロの意味確定 + 対処 A/B/C 選定 (§5.1 確定後) | Code A | — | §5.1 |
| Step B 実装 1 | atom_centroids 生成 (§5.2 確定後) + Constitution 取得 (§5.3 確定後) | Code A | — | §5.2 / §5.3 |
| Step C 実装 2 | 段 4-b 連想 + 段 4-c 密度 + 品質フラグ + Constitution 制約 + 段 4-d 確率分布 | Code A | — | Step B 後 |
| Step D | グラフ HTML | Code A | — | Step C 後 |
| Step E | bit-identity 3 層 | Code A | — | Step D 後 |
| Step F | 観察事実報告 (4 可能性のどれが観察されたか) | Code A | — | Step E 後 |
| Step G | Phase Result | Genesis 側 Web Claude | — | Step F 後 |

想定合計 1.5-2 日 (Language 側データ揃い後)。

---

## 7. 規律遵守自己点検 (本 Step A)

| # | 格言 | 遵守 |
|---|---|---|
| 2 | 物理層 frozen | 本書は read-only 調査、書込み unified/v1103/ 配下のみ、Genesis / Language 側 outputs 不変 |
| 5 | 観察軸を増やすことを駆動要因にしない | 既存出力 (v1101a / v1102) + Language 側既存データの照合のみ |
| 11 | 概念単位を雑に扱わない | normalized_scores と raw_scores の区別、Research Constitution と Atom-level Constitution の区別を §1 で明示 |
| 12 | Aruism 判定回避 | 本書は事実記録、(i)(ii)(iii) の判定は Web Claude / Taka |
| 13 | AI を信じない原則は Taka 個人 | §5 確認要請 4 件、Code A 仮所見と最終判断を区別 |
| 14 | Taka 直感優先 | Taka 整理 (決定は裏切りでない、実践価値が前提) を §0 / §3 で継承 |

---

## 8. 一文サマリ (再掲)

v1103 設計書 §3.2 認識確認の Code A 実環境照合結果として論点 0 (ゼロの意味) は設計書 §2.2 の (a)(b) 二択でなく **(c) normalized_scores は全 48 軸非ゼロ正規化済 / raw_scores は mean Nonzero 17.68/48 で設計書前提と整合** の二系統が存在する第 3 の状態 (1,228 word サンプル)、Language 側データの所在確認で **atom_centroids_48d.csv 未存在 (Language 側生成不在)** + **Atom-level Constitution (Couple/Merge/Subsume/Monitor) 未存在 (Research Constitution は別物)** + **batch_report.md 未存在 (batch_report.py のみ実行で生成可能)** が判明、v1102 primary table は段 4-a 入力として直接使用可で受け手構造軸も整合、Genesis 側に関しては新規 main run 不要だが Language 側データ不足のため段 4-b/4-c 着手前に Web Claude/Taka 確認要請 4 件 (§5.1 ゼロの意味設計書前提更新は raw/normalized どちらをベースにするか / §5.2 atom_centroids_48d.csv の Code A 生成または Language 側提供 / §5.3 Atom-level Constitution の所在または取得 / §5.4 batch_report.md 生成可否) を整理、Code A 仮所見 (§5.1 raw/normalized 両方並列で観察に含める = 留保 #33 系列同型 / §5.2 Code A が `*_a1.jsonl` から生成 / §5.3 Language 側 Web Claude 提供を推奨 / §5.4 Code A が batch_report.py 実行) は最終判断 Web Claude/Taka に委ねる、想定実装 1.5-2 日 (確認要請 4 件回答後)。

---

*以上、v1103 Step A 認識確認 (Code A、2026-05-20)。確認要請 4 件への Web Claude / Taka 回答後、Step 4.5 疎性前処理 + Step B 実装 1 (atom_centroids 生成 + Constitution 取得) に着手可。*
