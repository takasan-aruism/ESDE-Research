# 11 ESDE Language Summary

*ファイル番号変更 (2026-05-18)*: Unified Phase 独立に伴い `10_esde_language_summary.md` → `12_esde_language_summary.md` に繰り上げ。新規 `07` は `07_unified_summary.md`。内容は変更なし。
*作成*: 2026-05-13、Code A
*対象*: ESDE Language 系 (`language/` + `docs/ESDE language/` 直下) の凍結時点 (2026-03-03) スナップショット
*親資料*: `language/ESDE_LANGUAGE_FROZEN_SPEC.md` (技術仕様、636 行) + `unified/v1100/language_side_investigation_report.md` (Web Claude Language 側依頼への調査報告書、466 行)
*位置づけ*: AI summaries の 1 つ。`06_developmental_summary.md` (Genesis 側) + `06b_developmental_phase15_summary.md` (Phase 1.5) と並列で、**ESDE Language 系の要約**。詳細追求時は親資料へ

---

## 0. このドキュメントの位置づけ

### 0.1 ESDE は 2 系統で運用

| 系統 | 主題 | 主要主体 | 凍結状態 |
|---|---|---|---|
| **Genesis 系** | cid / α/β-Integration / 4 層アーキテクチャ | 観察者 (Taka) が記録する量 | **現役** (v10.x 進行中、v10.13.a 完了) |
| **Language 系** | Atom / Synapse / Lexicon v2 / Phase 7-10 | テキスト → 意味座標 | **2026-03 凍結** (本書対象) |

本書は **Language 系専用の要約**。Genesis 側との接続点は §6 で記述。

### 0.2 「凍結」の運用ルール (Taka 整理 2026-05-13)

> 最新以外の使わなさそうなものを `legacy/` または `旧/` に入れる

- `legacy/` (Genesis v9.x simulator + PDF) / `docs/ESDE language/旧/` (Language v5.31-v5.44 等) の **外側にあるものは凍結時点で生きている (現役相当)**
- `language/` 配下 + `docs/ESDE language/` 直下 14 .md は **全て現役相当の凍結状態**

---

## 1. ESDE Language は何ができるか (5 機能)

### 機能 1: 意味座標化 (Phase 8 + Lexicon v2)

テキスト → **326 Atoms × 10 軸 × 48 レベル** の多次元座標へ接地。Synapse (WordNet 経由) + Lexicon v2 (共鳴度 0-10) で自然言語を定量的に観測、共鳴度 Auditor で「焦点の定まった観測」vs「拡散した観測」を自動判定。

### 機能 2: 未知領域の可視化 (Phase 7)

テキスト中の未知語 → 4 仮説並列評価 (A/B/C/D)、Unknown Queue へ蓄積、Phase 7 Route C で Synapse gap 自動発見、Relation Pipeline により verb-level gap を corpus-scale で診断可能。

### 機能 3: 統計的パターン発見 (Phase 9)

Section ベースの意味的類似性を Lens (Structure / Semantic / Hybrid) で観測、Mutual-kNN + k-sweep により「相転移点」を自動検出、Island (書き方が統計的に類似したセクション群) をクラスタリング。

### 機能 4: 強い意味↔弱い意味の統合観測 (Phase 10 Cell、設計完了・実装未着手)

Phase 8 Molecule (確定的意味構造) と Phase 9 Island (統計的パターン) を **混ぜずに統合**、条件因子 (source_type / document_section 等) が「引力」となり両者を結合。`esde_cell_architecture.md` v2.3 で設計完了、Python 実装は repo 不在。

### 機能 5: 自動拡張メカニズム (Synapse Expansion Phase 1-3、実走 v3.1/v3.2)

Phase 7 evidence + Relation Pipeline diagnostics から `SynapseEdgeProposer` が gap を自動提案、4-Pack Rewrite により WordNet synset → Atom edge を仮説生成。実走 v3.1 (+5.8pt: 55.2%→61.0%) / v3.2 (+2.0pt: 61.0%→63.0%) で逓減パターン観察。

### 重要な制約 (Aruism 原則)

- 「**評価も意思決定も行わない**」(「記述せよ決定するな」)
- Grounder は **Lexicon Core のみ参照** (Deviation / Proposal / Patch は不参照)
- 「**勝者を決めない**」設計、複数仮説の並行保持、不確実性は有効な結果
- Policy × Version × Scope ごとに統計は完全分離 (再現性 + トレーサビリティ)

---

## 2. 主要 5 系統 (実装ファイル概要)

### 2.1 Phase 8 Sensor (`language/sensor/`、9 files、78KB)

テキスト → Molecule (原子列挙)。`molecule_generator_live.py` (30KB、LLM QwQ-32B) + `validator_v83.py` (16KB、正規形スキーマ検証) を中心に、SynsetExtractor + CandidateRanker + GlossaryValidator を結合。**15 演算子** (`×`/`▷`/`→`/`⊕`/`|`/`◯`/`↺`/`〈〉`/`≡`/`≃`/`¬`/`⇒`/`⇒+`/`-|>`) を `constants.py` で定義。Strict output contract + determinism_hash で再現性保証。

### 2.2 Synapse v3.5 (`language/synapse/`、5.3MB + 6 patches)

WordNet ↔ ESDE Atom mapping。`esde_synapses_v3.json` (137K+ synsets) を base に、v3.1-v3.5 の patches を **Overlay 機構** (add_edge / disable_edge tombstone) で適用。`SynapseStore` (16KB)、`SynapseEdgeProposer` (15KB、4-Pack Rewrite)、CLI (propose-synapse / evaluate-synapse-patch、23KB)。3 プロファイル (projection / relation / full) で用途別に patch 切替。

### 2.3 Projection v3.5 (`language/projection/`、4 mode 評価)

Molecule 中の各 Atom に対し埋め込み空間で類似度スコアを計算、Top-3 を返す。`run_projection_experiment.py` (27KB) + `projection_eval.py` (8KB) + Berlin sentences 50 文の Ground Truth (atoms_top3 + synapse_top1)。4 mode (base / B / C / BC) で Recall@1/@3 評価、**base R@1=0.96 が最高** (Projection 不要化の可能性示唆)。

### 2.4 Lexicon v2 (`language/lexicon/`、14+ .py、2 段パイプライン)

**WordNet 語彙供給** (`wn_*.py` 11 files、12 relation 展開) + **A1 観測** (`mapper_a1.py` 25KB / `auditor_a1.py` 47KB / `batch_report.py` 13KB)。326 atoms × Core/Deviation 分離 → QwQ-32B で 48 スロット共鳴度観測 → 5 checks (C1-C5) で構造的品質監査 → batch_report 集約。**326 atoms 全てが `proposed` status** (a1_batch/{ATOM}.json 326 files で完了)。

### 2.5 Observation C / Relations (`language/relations/`、3 files)

SVO (Subject-Verb-Object) 抽出 + Atom grounding。`parser_adapter.py` (15KB、spaCy dependency parsing) + `relation_logger.py` (Grounding v0.3.2、5 filter: Primary-Lemma Guard / Fallback Penalty / POS Guard / Light Verb Stoplist / Score Threshold) + `run_relations.py` (Wikipedia articles 入力)。

---

## 3. 凍結時点の状態 (機能完成 vs 設計のみ vs 実装不在)

### 3.1 ✅ 機能完成 (実装 + 検証済)

| 機能 | 主要モジュール |
|---|---|
| Phase 8 Sensor | `language/sensor/` 9 files、Molecule 生成 + determinism_hash |
| Phase 8 Projection | `language/projection/` 4 mode 評価、base R@1=0.96 |
| Synapse v3.5 | `language/synapse/` + 6 patches、Overlay 機構 |
| Lexicon v2 (A1 観測) | `language/lexicon/` 14+ .py、326 atoms proposed 完了 |
| Observation C (SVO 抽出) | `language/relations/` 3 files、Grounding v0.3.2 |
| Synapse Expansion Phase 1-3 | v3.1/v3.2 実走、+5.8pt/+2.0pt 逓減パターン |
| Phase 7 Unknown Resolution | `ESDE_Detailed_Design.md` で完了表記 (7A/7B+/7C/7C'/7D) |

### 3.2 ⏳ 設計完了・実装未着手

| 機能 | 設計書 |
|---|---|
| **Phase 10 Cell** | `esde_cell_architecture.md` v2.3 (2026-02-08、Phase 8 ↔ 9 統合) |

#### Phase 10 Cell の核心 (設計のみ)

> Phase 8 (強い意味系) と Phase 9 (弱い意味系) は別々の系、混ぜてはならない。**条件因子 (Condition Factor) が「引力」として機能し両者を結合**。

- 条件因子は **テキスト内部構造** (セクション名 / ドキュメント名) から抽出
- Lens (Structure / Semantic / Hybrid 観測角度) + Island (書き方が統計的に類似したセクション群)
- Mutual-kNN + k-sweep で動的・トレーサブル

### 3.3 ❓ Python 実装が repo 内に検出されない

| 機能 | 状況 |
|---|---|
| **Phase 9 Statistics** (EdgePolicyResolver / Mutual-kNN / Island / Lens / Weak Axis / k-sweep) | ドキュメント上は **完了表記** (`COMMAND_REFERENCE_v2.md` v2.0)、Python 実装は repo 内 grep で **0 件ヒット** |

→ 別 repo / 未移植 / 設計のみ のいずれかは判定不能、Taka 確認対象。

---

## 4. 326 Atoms × 10 軸 × 48 レベル座標系

### 4.1 326 Atoms (24 カテゴリ)

カテゴリ例: ABS / ACT / BEI / BOD / CHG / COG / COM / ECO / ELM / EMO / EXS / FND / LOG / MAT / NAT / OBJ / PER / PHY / PRP / REL / SOC / SPA / SPC / STA / TIM / VAL / WLD 等

### 4.2 10 軸 × 48 スロット (`mapper_a1` 定義)

| 軸 | 説明 | レベル数 |
|---|---|---:|
| temporal | 時間的条件 | 7 |
| scale | スケール条件 | 6 |
| epistemological | 認識論 | 5 |
| ontological | 存在論 | 5 |
| interconnection | 連動性 | 5 |
| resonance | 共鳴深度 | 4 |
| symmetry | 対称性 | 5 |
| lawfulness | 法則性 | 4 |
| experience | 経験的質 | 3 |
| value_generation | 価値生成 | 4 |
| **合計** | - | **48** |

### 4.3 共鳴度スコア (0-10 連続値、`DESIGN_NOTE_Resonance_Scoring.md` Approved 2026-02-15)

binary → continuous の設計転換、Auditor 5 checks (C1 Distribution / C2 Symmetric leak / C3 Evidence mismatch / C4 Axis-generic inflation / C5 POS coherence)、Focus rate 計算で「拡散した観測」を自動検出。

---

## 5. ドキュメント索引 (`docs/ESDE language/` 14 .md、推奨読書順)

### 5.1 最重要 4 文書 (AI 参照時)

| # | 文書 | バージョン | 用途 |
|---|---|---|---|
| 1 | `ESDE_Glossary.md` | **v5.7.0** (2026-02-11) | 用語統合索引、216 用語、最新 |
| 2 | `ESDE_Detailed_Design.md` | v5.4.8-MIG.2 | Substrate Layer / Migration Phase 2 / Phase 7-9 フロー |
| 3 | `ESDE_Module_Reference_Lexicon_v2.md` | v5.7.0 追加 | Lexicon v2 2 段パイプライン |
| 4 | `esde_cell_architecture.md` | **v2.3** (2026-02-08) | **Phase 10 Cell 設計** (Phase 8↔9 統合) |

### 5.2 推奨読書順

1. 哲学・概観: `ESDE_Essence_v02.md` → `ESDE_Overview.md`
2. 用語: `ESDE_Glossary.md` (v5.7.0)
3. 詳細設計: `ESDE_Detailed_Design.md` + `ESDE_Technical_Specification.md`
4. 実装地図: `ESDE_Module_Reference.md` + `_Lexicon_v2`
5. 個別実装: `Project_Lexicon_Unified_Implementation_Spec.md` + `DESIGN_NOTE_Resonance_Scoring.md`
6. Phase 9 実行: `COMMAND_REFERENCE_v2.md`
7. 統合・展望: `esde_cell_architecture.md` + `ESDE_Vision_LLM_Symmetric_Integration.md`

### 5.3 14 文書一覧

`README.md` / `ESDE_Overview.md` / `ESDE_Essence_v02.md` / `ESDE_Detailed_Design.md` / `ESDE_Technical_Specification.md` / `ESDE_Glossary.md` / `ESDE_Module_Reference.md` / `ESDE_Module_Reference_Lexicon_v2.md` / `ESDE_Vision_LLM_Symmetric_Integration.md` / `ESDE_Briefing_Synapse_Expansion_via_Phase7.md` / `Project_Lexicon_Unified_Implementation_Spec.md` / `COMMAND_REFERENCE_v2.md` / `DESIGN_NOTE_Resonance_Scoring.md` / `esde_cell_architecture.md`

---

## 6. Genesis 側との接続点 (Unified Phase 用)

### 6.1 共有基盤

| 概念 | Language 側 | Genesis 側 |
|---|---|---|
| **326 atoms** | `esde_dictionary.json` の concepts | `cid_atom_sim_matrix` (v10.6 で 326 → 25 atoms 抽出) |
| **48D 座標** | A1 batch normalized_scores (10 axes × 48 levels) | cid vector (v10.6 で 10 axes × 48 levels) |
| **WordNet → atom** | Synapse v3.5 + Lexicon core_pool | (なし、v1100 候補 1 で接続候補だったが UBAF 凍結で削除) |
| **動的補正** | UBAF (corpus 由来、prototype 10 atom 凍結) | atom_introduction_event (v10.8) |
| **統合体** | Phase 10 Cell (未実装、設計のみ) | Integration α/β (v10.4-v10.5 実装済) |
| **時間軸** | なし (一回的処理) | 5 phase (v10.13.a: immediate / short / mid / long / null) |

### 6.2 Genesis TARGET_ATOMS 25 個との分布

Genesis v10.6 で 326 atom 中 **25 atoms** を構造的特異性 (δ > 1% × 9 + z-score ∞ × 17) で抽出。Language 側 24 categories のうち **10 category に分布**:
- 含まれる: BOD / COG / COM / EXS / FND / PER / PRP / SOC / TIM / WLD
- 含まれない 14 category: EMO / ACT / CHG / LOG / MAT / NAT / ABS / BEI / ECO / ELM / REL / SPC / STA / VAL

→ Genesis cid 状態空間での構造的特異性は **知覚 (PER) / 存在論 (EXS) / 社会 (SOC) / 世界 (WLD) に偏在**。

### 6.3 v1100 で確認された接続実測

v1100 候補 6 (null cell ↔ base 優位照合):
- Language base 優位 atom (R@1) = `{SOC.official, PRP.part}` 2 atoms
- Genesis Map 5 null cell atom = 20 atoms (PER/WLD/EXS/PRP/SOC/TIM/BOD/FND)
- **重なり 0、Jaccard 0**

→ 両系は独立に異なる「文脈非依存性」を捕捉 (Language = WSD 確定的射影、Genesis = path 経路を経ない波及)。

### 6.4 Phase 10 Cell ↔ Integration α/β 構造的同型観察候補

`esde_cell_architecture.md` v2.3 で:
- Phase 8 強い意味系 (Atom × Synapse 確定的射影) ↔ Genesis **β-Integration** (会計、確定的)
- Phase 9 弱い意味系 (Lens / Island 動的観測) ↔ Genesis **α-Integration** (観察、複数所属許容)
- 条件因子の「引力」 ↔ Genesis **Salience** mass-weighted 選択

→ Integration α/β が「言語接続時の階層化機構の先取り」(Taka 整理 2026-05-12) として位置づけ可能、v10.13.b 以降の主題候補。

---

## 7. Code A 調査経緯と訂正履歴

### 7.1 v1100 (Unified phase 第一歩、2026-05-12)

Web Claude (Genesis 側) が Language 側 §8 で提示した 6 接続候補を Code A が実環境調査:
- 候補 6 (null cell ↔ base 優位照合) 実装完了
- 候補 1 (UBAF 拡張) は **UBAF 自体が prototype 凍結 + 移行実態未確認** で削除
- 候補 2/3/4/5 は v1101 以降の主題候補

### 7.2 Language 側調査 (2026-05-13)

Web Claude (Language 側、凍結スレッド) からの調査依頼を Code A が実地調査:
- 重大度 高 (構想・記憶ベース、実装不在):
  - Phase 9 系全キーワード (`EdgePolicyResolver` / `Mutual-kNN` / `Island` / `Lens` / `Weak Axis` / `k-sweep` / W0-W6) **grep で 0 件**
  - `*_a1_final.jsonl` / `atom_centroids_48d.csv` は実体不在、実体は `a1_batch/{ATOM}.json` 326 件 + `mapper_output/{ATOM}_a1.jsonl` 325 件
- 重大度 中 (path 命名のズレ): `integration/lexicon/` 不在、実体は `language/lexicon/` 単一

### 7.3 Code A 認識訂正 (本書で確定)

| 元判定 | 訂正後 |
|---|---|
| Phase 10 Cell ≠ Phase 8+9 Cell (v1100 留保 #36) | **誤り**。`esde_cell_architecture.md` v2.3 = Phase 10 Cell の設計書。Phase 10 Cell = Phase 8 ↔ 9 統合 Cell |

---

## 8. 最終一文

ESDE Language は 326 Atoms × 10 軸 × 48 レベルの意味座標系を共通基盤として、Phase 8 Sensor (テキスト → Molecule)、Synapse v3.5 (WordNet ↔ Atom mapping、5.3MB + 6 patches)、Projection v3.5 (4 mode 評価、base R@1=0.96 最高)、Lexicon v2 (A1 観測 + WordNet 語彙供給、326 atoms proposed 完了)、Observation C (SVO 抽出 + Grounding v0.3.2)、Synapse Expansion Phase 1-3 (v3.1/v3.2 実走、+5.8pt/+2.0pt 逓減パターン) の 6 系統で機能完成、Phase 10 Cell は `esde_cell_architecture.md` v2.3 (2026-02-08) で設計完了 (Phase 8 ↔ 9 統合、条件因子を「引力」として Mutual-kNN + k-sweep + Island 検出) だが Python 実装は未着手、Phase 9 Statistics の Python 実装は repo 内 grep で 0 件 (ドキュメント上完了表記との乖離、別 repo / 未移植 / 設計のみのいずれかは判定不能)、Aruism 原則「記述せよ決定するな」+「勝者を決めない」設計 + 「Grounder は Lexicon Core のみ参照」を全 Phase で遵守、Genesis 側 v10.x との接続点は 326 atoms + 48D 座標 + 25 atoms (Genesis TARGET) の共有基盤 + Phase 10 Cell ↔ Integration α/β の構造的同型観察候補 (v1100 候補 6 で R@1 base 優位 2 atoms と Genesis null cell 20 atoms の重なり 0 を実測、両系は独立に異なる「文脈非依存性」を捕捉)、本書は AI 参照用要約で詳細は `language/ESDE_LANGUAGE_FROZEN_SPEC.md` (636 行) + `docs/ESDE language/` 14 .md (`ESDE_Glossary.md` v5.7.0 が最重要) を参照、凍結 2026-03-03、最終 mtime 2026-03-21 (一括コピー由来)。

---

*以上、10 ESDE Language Summary。詳細追求時は `language/ESDE_LANGUAGE_FROZEN_SPEC.md` (技術仕様) + `unified/v1100/language_side_investigation_report.md` (調査経緯) + `docs/ESDE language/` 14 .md を参照。Genesis 側 (v10.x) との接続は v1100 → v11.0.1 以降の Unified phase 主題で進行中。*
