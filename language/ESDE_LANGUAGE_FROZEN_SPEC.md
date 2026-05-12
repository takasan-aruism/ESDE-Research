# ESDE Language 凍結状態仕様書 — 何をやって何ができるか

*作成*: 2026-05-13、Code A (3 Explore agent 並行調査の統合報告)
*対象*: AI (Web Claude / 他 Code Agent / Code A 自身) 参照用、Taka 依頼「ESDE Language やっていたときの最新状態」
*位置づけ*: `legacy/` および `docs/ESDE language/旧/` の外側 = 凍結時点で生きている (現役相当の) ESDE Language 実装スナップショット。凍結日 2026-03-03、最終 mtime 2026-03-21 (一括コピー由来)
*関連*: `docs/LANGUAGE_LEGACY_DIGEST.md` (Genesis 接続時の起点) + `docs/ai_summaries/06_developmental_summary.md` (Genesis 側) + `developmental/v10x_implementation_spec.md` (Genesis 側技術仕様)

---

## 0. このドキュメントの位置づけ

- **凍結時点の最新スナップショット**: `language/` 配下 + `docs/ESDE language/` 直下 (旧/ 除外) の実体
- **何をやって何ができるか** を 1 本で答える、AI 参照用、無駄削減
- Taka 整理 (2026-05-13)「最新以外の使わなさそうなものを `legacy/` または `旧/` に入れる運用ルール」に基づき、それ以外は **生きている (= 現役の凍結状態)**
- **Code A 以前の認識訂正**: 「Phase 10 Cell ≠ Phase 8+9 統合 Cell」と書いた留保 #36 は **誤り**。正しくは `esde_cell_architecture.md` v2.3 が Phase 10 Cell の設計書、実装は未着手

---

## 1. ESDE Language は何ができるか (5 機能、高位視点)

### 1.1 意味座標化 (Phase 8 + Lexicon v2)

- テキスト → **326 Atoms × 10 軸 × 48 レベル** の多次元座標へ接地
- Synapse (WordNet 経由) + Lexicon v2 (共鳴度 0-10) で自然言語を定量的に観測
- 共鳴度 Auditor により「焦点の定まった観測」vs「拡散した観測」を自動判定

### 1.2 未知領域の可視化 (Phase 7)

- テキスト中の未知語 → 4 仮説並列評価 (A/B/C/D)
- Unknown Queue へ蓄積、Phase 7 Route C で Synapse gap 自動発見
- Relation Pipeline により verb-level gap を corpus-scale で診断可能

### 1.3 統計的パターン発見 (Phase 9)

- Section ベースの意味的類似性を Lens (Structure / Semantic / Hybrid) で観測
- Mutual-kNN + k-sweep により「相転移点」を自動検出
- Island (書き方が統計的に類似したセクション群) をクラスタリング

### 1.4 強い意味↔弱い意味の統合観測 (Phase 10 Cell、設計完了・実装未着手)

- Phase 8 Molecule (確定的意味構造) と Phase 9 Island (統計的パターン) を混ぜずに統合
- 条件因子 (source_type / document_section 等) が「引力」となり両者を結合
- `esde_cell_architecture.md` v2.3 (2026-02-08) で設計完了、Python 実装は repo 不在

### 1.5 自動拡張メカニズム (Synapse Expansion Phase 1-3、実走 v3.1/v3.2)

- Phase 7 evidence + Relation Pipeline diagnostics から SynapseEdgeProposer が gap を自動提案
- 4-Pack Rewrite により WordNet synset → 326 Atoms への edge を仮説生成
- 実走 v3.1 (+5.8pt: 55.2%→61.0%) / v3.2 (+2.0pt: 61.0%→63.0%) で逓減パターン観察

### 1.6 重要な制約

- ESDE は「**評価も意思決定も行わない**」(Aruism 原則「記述せよ決定するな」)
- Grounder は **Lexicon Core のみ参照** (Deviation/Proposal/Patch は不参照)
- 「**勝者を決めない**」設計により複数仮説の並行保持、不確実性は有効な結果
- Policy × Version × Scope ごとに統計は完全分離 (再現性 + トレーサビリティ)

---

## 2. 全体構造

### 2.1 Phase 進捗 (凍結時点 2026-03-03)

| Phase | 状態 | 内容 | 主要文書 |
|---|---|---|---|
| Phase 7 | ✅ 実装完了 | Unknown Resolution (7A/7B+/7C/7C'/7D) | `ESDE_Detailed_Design.md` + `ESDE_Briefing_Synapse_Expansion_via_Phase7.md` |
| Phase 8 | ✅ 実装完了 | Sensor (Molecule 生成) + Projection (Recall@k 実験中) | `ESDE_Module_Reference.md` + `README.md` (Projection 実験) |
| Lexicon v2 | ✅ 完成 | Constitution v1.0、A1 Mapper / Auditor 完成 | `ESDE_Module_Reference_Lexicon_v2.md` |
| Phase 9 | ✅ 完了 | Statistics v2.0、Lens 統合、k-sweep | `COMMAND_REFERENCE_v2.md` (Phase 9 完了時点) |
| Synapse Expansion | ✅ Phase 1-3 完了 | v3.1 / v3.2 実走、Audit Gate (PASS/WARN/FAIL) | `ESDE_Briefing_Synapse_Expansion_via_Phase7.md` |
| Phase 10 Cell | ⏳ 設計完了、実装未着手 | Phase 8 ↔ 9 統合、Mutual-kNN + k-sweep | `esde_cell_architecture.md` v2.3 |

### 2.2 326 Atoms × 10 軸 × 48 レベルの座標系

**326 atoms** = 24 カテゴリ × 平均 13.6 atoms (`esde_dictionary.json`)

カテゴリ: ABS / ACT / BEI / BOD / CHG / COG / COM / ECO / ELM / EMO / EXS / FND / LOG / MAT / NAT / OBJ / PER / PHY / PRP / REL / SOC / SPA / SPC / STA / TIM / VAL / WLD 等

**10 軸** × 各軸のレベル数 = **48 スロット** (mapper_a1 定義):

| 軸 ID | 説明 | レベル数 | 主要レベル |
|---|---|---:|---|
| temporal | 時間的条件 | 7 | emergence / transformation / permanence |
| scale | スケール条件 | 6 | individual / community / society / cosmic |
| epistemological | 認識論 | 5 | perception / identification / creation |
| ontological | 存在論 | 5 | material / informational / semantic |
| interconnection | 連動性 | 5 | independent / catalytic / resonant |
| resonance | 共鳴深度 | 4 | superficial / structural / existential |
| symmetry | 対称性 | 5 | destructive / inclusive / generative |
| lawfulness | 法則性 | 4 | predictable / emergent / necessary |
| experience | 経験的質 | 3 | discovery / creation / comprehension |
| value_generation | 価値生成 | 4 | functional / aesthetic / ethical / sacred |

### 2.3 データフロー全体

```
[1] esde_dictionary.json (326 atom 定義)
    ↓
[2] wn_auto_seed.py → seeds.json
    ↓
[3] wn_batch_expand.py (12 WordNet relations 展開)
    → data/expanded/{atom}.json (327 files)
    ↓
[4] wn_lexicon_entry.py (Core/Deviation 分離)
    → data/lexicon_entries/{atom}.json (327 files)
    ↓
[5] mapper_a1.py (QwQ-32B、48 スロット共鳴度観測)
    → data/mapper_output/{atom}_a1.jsonl (325 files)
    ↓
[6] auditor_a1.py (5 checks C1-C5)
    → audit_output/{atom}_audit.jsonl (PASS/REVISE)
    ↓
[7] batch_report.py
    → batch_report.md (全 326 atom 統計集約)
    ↓
[8] atoms/a1_batch/{atom}.json (326 files、proposed status)
    ↓ (Sensor / Synapse / Projection で参照)
[9] テキスト入力 → Sensor → Molecule
       → Synapse → Atom 接地
       → Projection → top-k 候補
```

---

## 3. Phase 8 系統 — Sensor / Synapse / Projection

### 3.1 `language/sensor/` (Phase 8 Sensor、9 files、78 KB)

**役割**: 自然言語テキストから ESDE Atom を抽出し、意味分子 (Molecule) を生成

| ファイル | 主要 class / 関数 | 機能 |
|---|---|---|
| **`molecule_generator_live.py`** (30KB) | `MoleculeGeneratorLive.generate(text, candidates) → molecule_dict` | LLM (QwQ-32B) ベース Molecule 生成、Zero-Chatter 出力契約 |
| **`validator_v83.py`** (16KB) | `MoleculeValidatorV83(glossary, allowed_atoms).validate(molecule) → ValidationResultV83` | 正規形スキーマ検証 (axis/level flat)、Synapse hash 記録 |
| `esde_sensor_v2_modular.py` (10KB) | `ESDESensorV2.analyze(text) → {candidates, meta}` | Facade、Glossary / Synapse / LLM 統合 |
| `rank_candidates.py` (5.6KB) | `CandidateRanker(top_k).rank(concept_scores) → List[Dict]` | 候補スコアリング集約、決定論的 Top-K ソート |
| `extract_synset.py` (2.5KB) | `SynsetExtractor(max_synsets, allowed_pos).extract_all(tokens) → {token: [synset_ids]}` | WordNet synset 抽出 (NLTK)、POS フィルタ |
| `loader_synapse.py` (3.3KB) | `SynapseLoader.get_instance().get_edges(synset_id) → List[edge_dict]` | Synapse JSON ロード、Singleton |
| `glossary_validator.py` (4.2KB) | `GlossaryValidator(glossary).is_valid_atom(atom)` | Glossary 検証、axis/level 定義確認 |
| `audit_trace.py` (4.3KB) | `AuditTracer().build_meta(engine, version, ...)` | 監査証跡、hash 計算 |
| `constants.py` (1.3KB) | (定数定義) | **15 演算子定義** + LLM endpoint + Top-K=5 |

#### Sensor パイプライン

```
Input Text
  ↓ tokenize + lemmatize
  ↓ SynsetExtractor → {token: [synset_ids]} (max 3 synsets/token, POS in {n,v,a,r,s})
  ↓ SynapseLoader → {synset: edges}
  ↓ CandidateRanker.aggregate_scores() → score = Σ(raw_score × weight) per concept_id
  ↓ CandidateRanker.rank() → Top-K=5 (DESC by score, ASC by concept_id)
  ↓ MoleculeGeneratorLive (optional LLM refine, max retries=2)
  ↓ MoleculeValidatorV83 (atom integrity, coordinate validity, span validity)
Output: Molecule + Meta (determinism_hash, counters, timestamp)
```

#### 15 演算子 (`constants.py`)

| 族 | 演算子 | 意味 |
|---|---|---|
| 結合 | `×`, `▷`, `→` | connection / action / transition |
| 並置 | `⊕`, `\|`, `◯`, `↺` | juxtaposition / condition / target / recursion |
| 階層 | `〈`, `〉` | open / close |
| 同値 | `≡`, `≃`, `¬` | equivalence / practical equivalence / negation |
| 創発 | `⇒`, `⇒+`, `-\|>` | emergence / creative emergence / destructive emergence |

### 3.2 `language/synapse/` (Synapse v3.5、WordNet ↔ Atom mapping)

**役割**: WordNet synset から ESDE Atom への双方向マッピング、Patch オーバーレイで段階的拡張

| ファイル | 種別 | 機能 |
|---|---|---|
| **`esde_synapses_v3.json`** (5.3MB) | データ | 137K+ synset → {concept_id, axis, level, raw_score, weight} |
| `synapse_profiles.json` | データ | 3 プロファイル: projection (v3.4) / relation (v3.1-3.3) / full |
| `patches/synapse_v3.*.json` | Patch | v3.1 (+42 edges, +5.8pt) / v3.2 (+27 edges, +2.0pt) / v3.3 (tombstone) / v3.4 (noun) / v3.5 |
| `store.py` (16KB) | class `SynapseStore` | 統一ストア、Base + Patch オーバーレイ (disable_edge tombstone) |
| `schema.py` (3.0KB) | class `SynapsePatchEntry` | Patch スキーマ: `edge_key="synset_id::atom_id"`、op={add_edge\|disable_edge} |
| `proposer.py` (15KB) | class `SynapseEdgeProposer` | Edge 提案生成、4-Pack Rewrite、embedding 比較 |
| `diagnostic.py` (7.8KB) | class `DiagnosticResult` | 診断結果ラッパー、grounding_rate / coverage_gap / category_mismatch |
| `cli.py` (23KB) | CLI | propose-synapse / evaluate-synapse-patch (Phase 3 ワークフロー) |

#### Synapse Edge スキーマ

```json
{
  "synset_id": "kill.v.01",
  "edges": [
    {"concept_id": "ACT.destroy", "axis": "ontological", "level": "fundamental",
     "lemma": "kill", "pos": "v", "raw_score": 0.87, "weight": 1.0, "rank": 1}
  ]
}
```

#### Patch スキーマ

```json
{"patches": [
  {"op": "add_edge", "edge_key": "kill.v.01::ACT.destroy",
   "synset_id": "kill.v.01", "atom": "ACT.destroy", "score": 0.87,
   "reason": "auto_proposal_v2.0", "metadata": {"rewrite_pack_id": "verb_aug_v1"}}
]}
```

#### Overlay 規則

1. Load order: Base → Patch v3.1 → v3.2 → ... (順序確定的)
2. `edge_key = "{synset_id}::{atom_id}"` で一意識別
3. `disable_edge` wins (tombstone 記録、結果に含めない)
4. `add_edge` duplicate は last-one-wins
5. Conflict log: `[OVERLAY_CONFLICT]` で DEBUG 出力

#### Patch プロファイル

| プロファイル | 用途 | Patch | 説明 |
|---|---|---|---|
| **projection** | Phase 8 Projection | v3.4 | 名詞 WSD 専用、動詞 grounding なし |
| **relation** | Observation C Relation | v3.1, v3.2, v3.3 | 動詞 grounding 重視 |
| **full** | Integration test | v3.1-3.4 統合 | 全 patch 統合 |

### 3.3 `language/projection/` (Projection v3.5、4 mode Recall@k)

**役割**: Molecule 中の各 Atom に対し埋め込み空間で類似度スコアを計算、Top-3 候補を返す

| ファイル | 機能 |
|---|---|
| **`run_projection_experiment.py`** (27KB) | 4 mode (base/B/C/BC) を 50 Berlin 文で実行、`detail.jsonl` / `token_diagnostics.jsonl` 出力 |
| **`projection_eval.py`** (8.2KB) | Recall@k 計算、GT atoms × pred atoms マッチ、hit@1 / hit@3 集計 |
| `eval_data/berlin_sentences.jsonl` (98KB) | 入力文 (Berlin 記事 613 文、id/sentence) |
| `eval_data/ground_truth_50.jsonl` (20KB) | 50 文 × 79 span の GT (synapse_top1 + atoms_top3) |
| `output_v35/{base,B,C,BC}/` | 評価結果 (`pred_50.jsonl`, `detail.jsonl`, `token_diagnostics.jsonl`) |

#### Mode 定義

- **base**: Synapse 直接 (no projection)
- **B**: Field-First Projection (Atom field embedding のみ)
- **C**: Weak-Measurement Projection (事前分布なし、部分観測)
- **BC**: Hybrid (B + C 統合)

#### 評価結果 (`output_v35/report.md` および v1100 Code A 実測)

| Mode | Recall@1 | Recall@3 | Time (s) | ms/sent |
|---|---:|---:|---:|---:|
| **base** | **0.9630** | **0.9630** | 112.95 | 184.3 |
| B | 0.7778 | 0.9630 | 133.95 | 210.0 |
| C | 0.7778 | 0.9630 | 129.4 | 206.6 |
| BC | 0.7778 | 0.9630 | 132.43 | 211.4 |

注: README.md には Recall@3 = 0.329 と記載 (異なる評価軸)、v1100 Code A 実測の atoms_top3 マッチでは 0.96。最高は base (Projection 不要化の可能性、Synapse 直接が優位)。

#### 入出力スキーマ

**Ground Truth**:
```json
{"id": "berlin_0001", "targets": [
  {"span_text": "capital", "pos": "NOUN",
   "synapse_top1": "STA.wealth",
   "atoms_top3": ["SOC.official", "SOC.city", "SPC.place"]}
]}
```

**Prediction**:
```json
{"id": "berlin_0001", "targets": [
  {"span_text": "capital",
   "pred_top3": ["SOC.official", "SOC.city", "STA.wealth"],
   "scores_top3": [0.9, 0.8, 0.7317]}
]}
```

---

## 4. Lexicon v2 系統 — A1 観測 + WordNet 語彙供給

### 4.1 `language/lexicon/` 概要

**Lexicon v2 は 2 段パイプライン** (`ESDE_Module_Reference_Lexicon_v2.md` v5.7.0 記述):

| 段 | パイプライン | ファイル | 用途 |
|---|---|---|---|
| 1 | **WordNet 語彙供給** (`lexicon_wn/` ドキュメント上、実装は `lexicon/`) | `wn_*.py` 11 files | 326 atom × WordNet 12 relation 展開 |
| 2 | **A1 観測** (`integration/lexicon/` ドキュメント上、実装は `lexicon/`) | `mapper_a1.py` + `auditor_a1.py` + `batch_report.py` | Core Pool 各語に 48D 共鳴度プロファイル (QwQ-32B 観測 + 監査) |

**実装の実態**: ドキュメントが言及する `lexicon_wn/` および `integration/lexicon/` は実環境に **存在しない**、`language/lexicon/` 単一に統合済。

### 4.2 WordNet 語彙供給層 (`wn_*.py` 11 files)

| ファイル | 役割 | 入出力 |
|---|---|---|
| **`wn_auto_seed.py`** (7.5KB) | WordNet seed synset 自動抽出、初期化 | `esde_dictionary.json` → `seeds.json` |
| **`wn_batch_expand.py`** (13KB) | 全 326 atom の WordNet 展開 (12 relation) | `seeds.json` → `data/expanded/*.json` × 327 |
| **`wn_lexicon_entry.py`** (11KB) | Core/Deviation 分離、Lexicon Entry 生成 | `expanded/` → `data/lexicon_entries/*.json` × 327 |
| **`wn_core_stats.py`** (9KB) | Core-only 統計 (監査) | `lexicon_entries/` → `core_report.csv` |
| **`wn_cross_stats.py`** (14KB) | 全体統計 (Jaccard, 対称ペア漏洩等) | `expanded/` → `report.csv` |
| **`wn_proposal_gen.py`** (11KB) | Constitution v1.0 → Proposal 自動生成 | `core_report.csv` → `proposals.json` |
| **`wn_apply_proposals.py`** | Proposal 適用 | `proposals.json` → `lexicon_entries/` 更新 |
| **`wn_max_expand.py`** (15KB) | 単一 atom 詳細展開 (デバッグ用) | `atom_id` → 詳細 JSON |

#### 12 WordNet relations (`wn_batch_expand.py`)

| relation | 内容 | 主要用途 |
|---|---|---|
| `0_seed` | 核定義 (seed synset) | 起点 |
| `2_hypernym_d1` | hypernym depth 1 | 上位概念 |
| `3_hyponym_d1`, `_d2`, `_d3` | hyponym depth 1-3 | 下位概念 |
| `6_derivational` | 派生形 (品詞違い) | 形態変化 |
| `7_similar_to`, `8_also_see` | 同義・関連 | 類似性 |
| `9_antonym` | 対義語 | symmetric_pair |
| `10_sibling` | 同親語 | **主要汚染源** |
| `11_pertainym`, `12_verb_group` | 散発的関連 | 補完 |

### 4.3 A1 観測パイプライン (`mapper_a1` / `auditor_a1` / `batch_report`)

| ファイル | 主要関数 | 機能 |
|---|---|---|
| **`mapper_a1.py`** (25KB) | `build_a1_prompt()`, `call_qwq()`, `parse_qwq_response()`, `softmax()`, `focus_rate()` | Core Pool 各語を QwQ-32B で **48 スロット観測** |
| **`auditor_a1.py`** (47KB) | `PreScreenResult`, `call_qwq_audit()`, `classify_single_record()` | 構造的品質監査 (5 checks: C1-C5) |
| **`batch_report.py`** (13KB) | `load_final_records()`, `load_audit_records()`, `analyze()` | 全 atom 統計集約 |

#### 設計原則 (Aruism 整合)

「**Describe, do not decide**」 — winner=null 維持、スロット間での勝者選定なし

#### Auditor 5 checks (`auditor_a1.py`)

| Check | 内容 |
|---|---|
| **C1** Distribution anomaly | 全 0、全高、インフレーション |
| **C2** Symmetric pair leak | 対義語が逆軸の例外以外で高スコア |
| **C3** Evidence-score mismatch | evidence テキスト vs 実スコア不一致 |
| **C4** Axis-generic inflation | entire axis 一律高 (generic) |
| **C5** POS coherence | 品詞と軸の不一致 |

### 4.4 Synapse v4 比較層 (`synapse_v4_*.py` 3 files)

| ファイル | 役割 |
|---|---|
| **`synapse_v4_compare.py`** (42KB) | Synapse (embedding-based) vs A1 (empirical 48D) 検証、Task 1-4 (原子重心構築、Word-Atom 距離、Synapse Edge 比較) |
| **`synapse_v4_task3.py`** (18KB) | Task 3 単体 (Synapse Edge 比較) |
| **`synapse_v4_tasks12.py`** (27KB) | Task 1-2 (重心計算、cosine 距離) |

注: Synapse v4 では SLOT_IDS 定義が `mapper_a1` と異なる (`compare.py` line 38-61)、要 Web Claude 確認。

### 4.5 lexicon/data/ サブディレクトリ

| パス | 内容 | files |
|---|---|---:|
| `data/definitions/` | WordNet 定義キャッシュ | 3 |
| `data/expanded/` | WordNet 展開結果 (全 relation) | 327 |
| `data/lexicon_entries/` | Core/Deviation 分離後 Lexicon Entry | 327 |
| `data/mapper_output/` | Mapper JSONL 出力 (48D 共鳴度) | 325 (1 件差分、原因不明) |

### 4.6 `language/atoms/`

| パス | 内容 |
|---|---|
| `atoms/esde_dictionary.json` | 326 atom 定義 (10 軸 × 48 レベル + symmetric_pair + definition + triggers) |
| `atoms/a1_batch/{ATOM_ID}.json` × 326 | A1 batch (proposed status、core_pool 含む) |

#### `esde_dictionary.json` スキーマ

```json
{
  "meta": {"version": "2.0", "total_concepts": 326, "total_axes": 10},
  "axes": { /* 10 軸定義 */ },
  "atoms": {
    "ABS.bound": {
      "id": "ABS.bound", "category": "ABS", "name": "bound",
      "symmetric_pair": "ABS.release",
      "definition_en": "Tied or restricted; ...",
      "triggers_en": ["constrain", "restrict"],
      "anti_triggers_en": ["free", "release"],
      "examples_en": {"positive": [...], "negative": [...]}
    }
  }
}
```

#### `a1_batch/{ATOM}.json` スキーマ (proposed status)

```json
{
  "atom": "ABS.bound", "category": "ABS",
  "status": "proposed",
  "symmetric_pair": "ABS.release",
  "core_pool": {
    "rules": ["0_seed", "3_hyponym_d1", "6_derivational", "7_similar_to", "9_antonym"],
    "count": 186,
    "words": [
      {"w": "bind", "pos": "v", "src": "0_seed",
       "definition": "fasten or secure with a rope...",
       "path_count": 2, "sources": ["0_seed"]}
    ]
  }
}
```

---

## 5. 関係系統 — Relations / Harveste / Phase 9 / Phase 10 設計

### 5.1 `language/relations/` (Observation C: Relation Pipeline)

**役割**: 自然言語テキストから SVO (Subject-Verb-Object) を抽出し、Atom に接地

| ファイル | 主要 class | 機能 |
|---|---|---|
| **`parser_adapter.py`** (15KB) | `SVOTriple`, `ParserAdapter.extract_svo()` | spaCy dependency parsing で SVO 抽出 |
| `relation_logger.py` | `SynapseGrounder`, `RelationLogger` | SVO → Atom grounding (WordNet → Synapse lookup) |
| `run_relations.py` | (パイプラインランナー) | Wikipedia articles 等を入力、`clean_wiki_text()` / `split_into_sections()` |

#### Grounding v0.3.2 Filters

1. **Primary-Lemma Guard**: primary synset に Synapse edge がある場合のみ secondary 許可
2. **Secondary Fallback Penalty**: secondary candidates は `score *= 0.9`
3. **POS Guard**: noun categories (NAT/MAT/PRP/SPA) をブロック
4. **Light Verb Stoplist**: have/make/be 等は `UNGROUNDED_LIGHTVERB`
5. **Score Threshold**: `min_score` 以下はドロップ

**Operator**: `▷` (ACT) のみ (プロトタイプ段階)

### 5.2 `language/harveste/` (Wikipedia / 外部データ収集)

データハーベスタ。`data/datasets/{mixed,warlords}/` に成果物。

### 5.3 `language/esde/`

| ファイル | 役割 |
|---|---|
| `projection.py` | `language/projection/` とは別 path、役割の詳細未測定 |

### 5.4 Phase 9 (Statistics、`COMMAND_REFERENCE_v2.md` 完了記録)

**ドキュメント内記述** (`ESDE_Detailed_Design.md` + `COMMAND_REFERENCE_v2.md` v2.0):
- Status: COMPLETE - Phase 9 ended at W6
- Harvest → Analyze ワークフロー
- Lens (Structure / Semantic / Hybrid) で観測角度切替
- Mutual-kNN + k-sweep による相転移検出 (k=3→4 で gcr=0.13→0.66 等)
- Threshold modes (fixed / quantile)
- Island クラスタリング

**Python 実装の repo 内所在**: **検出されず** (`grep "EdgePolicyResolver|Mutual.kNN|Island|Lens|Weak Axis|k_sweep"` で 0 件)

→ 状態: **ドキュメント上 Phase 9 完了、Python 実装は repo 内に存在しない** (別 repo / 未移植 / 設計のみのいずれかは判定不能)

### 5.5 Phase 10 Cell (設計完了、実装未着手)

**設計書**: `docs/ESDE language/esde_cell_architecture.md` v2.3 (2026-02-08)

#### Cell の定義

> Phase 8 (強い意味系) + Phase 9 (弱い意味系) の統合アーキテクチャ

#### 核心的洞察

- Phase 8 と Phase 9 は **別々の系**、混ぜてはならない
- **条件因子 (Condition Factor)** が「引力」として機能、両者を結合
- 条件因子は外部メタデータではなく、**テキスト内部構造** (セクション名等) から抽出

#### v2.0 以降の追加要素

- **Lens (レンズ)**: 同じデータを異なる観点 (構造/意味/混合) で観測可能
- **Island**: 書き方が統計的に類似したセクション群のクラスタ
- **Mutual-kNN + k-sweep**: 閾値・エッジ選択・クラスタリングを動的・トレーサブルに

#### v2.2 追加: SynapseStore (Overlay 機構)

- Phase 1 実装完了 (Design Spec v2.1、Gemini 設計 + GPT 監査)
- 監査チェックリスト 10/10 通過

#### v2.3 追加: Synapse Expansion Phase 2-3

- `SynapseEdgeProposer` (4-Pack Rewrite による Edge 自動生成)
- CLI (propose-synapse / evaluate-synapse-patch)
- Audit Gate (PASS/WARN/FAIL 機械判定)
- v3.1 (+5.8pt) / v3.2 (+2.0pt) 実走、逓減パターン発見

#### Cell スキーマと Phase 10

`esde_cell_architecture.md` line 622:
> Cell スキーマは設計段階。Phase 10 以降の課題

→ Cell Architecture v2.3 は **Phase 10 Cell の設計書**、実装は未着手 (Code A 以前の認識訂正)

---

## 6. 主要データ構造

### 6.1 326 Atoms 座標系

- 326 atoms × 10 軸 × 48 レベル = 326 × 48 = 15,648 (atom × slot) ペア
- 共鳴度スコア 0-10 の連続値 (binary ではない、`DESIGN_NOTE_Resonance_Scoring.md` Approved 2026-02-15)
- Focus rate 計算で「焦点の定まった観測」vs「拡散した観測」を分類

### 6.2 a1_batch (326 files、proposed status)

各 atom の `core_pool` に約 100-200 語の WordNet 由来語彙、各語に 48D 共鳴度プロファイル想定 (実体は `mapper_output/` に jsonl で出力)

### 6.3 Synapse v3 (5.3MB、137K+ synsets)

WordNet synset → atom edge、各 edge に raw_score / weight / rank。
6 patches (v3.1-v3.5) のオーバーレイで段階的拡張。

### 6.4 Projection v35 (4 mode 評価結果)

50 Berlin 文 × 79 span × top-3 atoms × 4 mode = 評価サンプル数 ~316。
出力は per-token (`token_diagnostics.jsonl`) + per-sentence (`pred_50.jsonl`) + 詳細 (`detail.jsonl`) の 3 段階。

---

## 7. 凍結時点での状態整理

### 7.1 ✅ 機能完成 (実装 + 検証済)

| 機能 | 主要モジュール | 検証 |
|---|---|---|
| Phase 7 Unknown Resolution | (詳細未測定、設計書 `ESDE_Detailed_Design.md`) | 完了表記 |
| Phase 8 Sensor (Molecule 生成) | `language/sensor/` 9 files | Strict output contract、determinism_hash |
| Phase 8 Projection (Recall@k) | `language/projection/` | 4 mode 評価完了、base 優位確認 |
| Lexicon v2 (A1 観測パイプライン) | `language/lexicon/` 14+ .py | 326 atoms proposed status 完了 |
| Synapse v3.5 (WordNet ↔ Atom) | `language/synapse/` + patches | v3.1/v3.2 実走完了、Audit Gate |
| Observation C (SVO 抽出) | `language/relations/` 3 files | Grounding v0.3.2 完成 |

### 7.2 ⏳ 設計完了・実装未着手

| 機能 | 設計書 |
|---|---|
| Phase 10 Cell (Phase 8 ↔ 9 統合) | `esde_cell_architecture.md` v2.3 |

### 7.3 ❓ Python 実装が repo 内に検出されない (要確認)

| 機能 | 状況 |
|---|---|
| Phase 9 Statistics (EdgePolicyResolver / Mutual-kNN / Island / Lens / Weak Axis / k-sweep) | ドキュメント上は完了 (`COMMAND_REFERENCE_v2.md` v2.0)、Python 実装は repo 内 grep で 0 件 |

→ 別 repo / 未移植 / ドキュメントが先行 のいずれかは Code A 判定不能、Taka 確認対象

### 7.4 機能完成の総括

凍結 2026-03-03 時点で:
- **テキスト → Atom** (Phase 8 Sensor) 動作
- **Atom × Atom 共鳴度プロファイル** (Lexicon v2 A1) 326 atoms 完成
- **WordNet ↔ Atom** (Synapse v3.5 + patches) 拡張機構完成
- **WSD 評価** (Projection 4 mode) Recall@1=0.96 (base) 達成

未達:
- **Cell 統合** (Phase 10) 設計のみ
- **大規模 Wikipedia corpus** での自動拡張 (Phase 7 evidence + Synapse Expansion はプロトタイプ規模)

---

## 8. ドキュメント索引 (`docs/ESDE language/` 14 .md、現役)

| # | ドキュメント | バージョン | 役割 | 用途 |
|---|---|---|---|---|
| 1 | `README.md` | v0.1.0 (2026-03-03) | Phase 8 Projection 実験記録 | WSD bottleneck 99.5% FAIL → 80% 目標 |
| 2 | `ESDE_Overview.md` | (日付なし) | ESDE 全体の日本語解説 | 哲学から実装まで概観 |
| 3 | **`ESDE_Essence_v02.md`** | v0.2 (GPT Audit Passed) | **設計思想 (Aruism 原理)** | 「記述せよ決定するな」の核心 |
| 4 | **`ESDE_Detailed_Design.md`** | v5.4.8-MIG.2 (2026-01-25) | 詳細アーキテクチャ | Substrate Layer / Migration Phase 2 / Phase 7-9 フロー |
| 5 | **`ESDE_Technical_Specification.md`** | v5.4.8-MIG.2 | 形式的仕様書 | 326 Atoms / 10 軸 × 48 レベル / Axiom 0/E/L/Eq/C/U/ε/T |
| 6 | **`ESDE_Glossary.md`** | **v5.7.0** (2026-02-11) | **用語統合索引 (最新)** | 216 用語、Constitution v1.0、Proposal パターン A-D |
| 7 | **`ESDE_Module_Reference.md`** | **v5.7.0** | **9 コアパッケージ実装ガイド** | esde_engine / sensor / synapse / lexicon_wn / Observation C |
| 8 | **`ESDE_Module_Reference_Lexicon_v2.md`** | **v5.7.0 追加** | **Lexicon v2 詳細** | 2 段パイプライン (語彙供給 + A1 観測) |
| 9 | `ESDE_Vision_LLM_Symmetric_Integration.md` | Conceptual (2026-02-22) | 将来ビジョン | LLM 対称統合 (Mirror → GPS → Dynamic) |
| 10 | `ESDE_Briefing_Synapse_Expansion_via_Phase7.md` | 2026-02-05 | Synapse 自動拡張提案 | Phase 7 Route C → Synapse v3 拡張パス |
| 11 | **`Project_Lexicon_Unified_Implementation_Spec.md`** | **v1.1.1** (2026-02-09) | **Lexicon 統一実装仕様** | 三資産分離 (Definition/Master/Index)、Constitution v1.0 |
| 12 | `COMMAND_REFERENCE_v2.md` | v2.0 (2026-02-02) | Phase 9 実行ガイド | Harvest → Analyze、Lens、k-sweep |
| 13 | **`DESIGN_NOTE_Resonance_Scoring.md`** | Approved 2026-02-15 | **共鳴度 0-10 モデル設計決定** | binary → continuous、Auditor 5 checks |
| 14 | **`esde_cell_architecture.md`** | **v2.3** (2026-02-08) | **Phase 10 Cell 設計書** | Phase 8 ↔ 9 統合、Mutual-kNN + k-sweep |

### 8.1 推奨読書順

1. 哲学・概観: `ESDE_Essence_v02.md` → `ESDE_Overview.md`
2. 用語: `ESDE_Glossary.md` (v5.7.0 最新)
3. 詳細設計: `ESDE_Detailed_Design.md` + `ESDE_Technical_Specification.md`
4. 実装地図: `ESDE_Module_Reference.md` (+ `_Lexicon_v2`)
5. 個別実装仕様: `Project_Lexicon_Unified_Implementation_Spec.md` / `DESIGN_NOTE_Resonance_Scoring.md`
6. Phase 9 実行: `COMMAND_REFERENCE_v2.md`
7. 統合・展望: `esde_cell_architecture.md` + `ESDE_Vision_LLM_Symmetric_Integration.md`

### 8.2 各文書のサイズ感

| 文書 | 概算行数 | 重要度 (AI 参照) |
|---|---:|---|
| Glossary v5.7.0 | 大 (216 用語) | **最重要** |
| Detailed_Design v5.4.8 | 大 | 重要 |
| Module_Reference + _Lexicon_v2 | 中 | 重要 |
| Cell_Architecture v2.3 | 中 (43KB) | 重要 (Phase 10) |
| Technical_Specification | 中 | 重要 |
| Essence_v02 | 小 | 重要 (哲学) |
| Project_Lexicon_Spec | 小 | 中 |
| DESIGN_NOTE_Resonance | 小 | 中 |
| COMMAND_REFERENCE | 小 | 中 (Phase 9) |
| Vision_LLM_Symmetric | 中 | 低 (展望) |
| Briefing_Synapse_Expansion | 小 | 低 (歴史) |
| Overview | 小 | 低 (概観) |
| README | 小 | 低 (実験記録) |

---

## 9. Genesis 側との接続点 (Unified Phase 用)

### 9.1 共有基盤

| 概念 | Language 側 | Genesis 側 |
|---|---|---|
| **326 atoms** | `esde_dictionary.json` の concepts | `cid_atom_sim_matrix` の列 (v10.6 で 326 → 25 atoms 抽出) |
| **48D 座標** | A1 batch normalized_scores (10 axes × 48 levels) | cid vector (v10.6 で 10 axes × 48 levels) |
| **WordNet → atom** | Synapse v3.5 + Lexicon core_pool | (Genesis 側に対応なし、v1100 候補 1 で接続候補) |
| **動的補正** | UBAF (corpus 由来) | atom_introduction_event 経由 activation (v10.8) |
| **統合体** | Phase 10 Cell (未実装) | Integration α/β (v10.4-v10.5 実装済) |
| **時間軸** | なし (一回的処理) | 5 phase (v10.13.a: immediate/short/mid/long/null) |

### 9.2 Genesis TARGET_ATOMS 25 個との分布

Genesis v10.6 で 326 atom 中 25 atoms を構造的特異性 (δ > 1% × 9 + z-score ∞ × 17) で抽出。Language 側 24 categories のうち 10 category に分布:
- 含まれる: BOD / COG / COM / EXS / FND / PER / PRP / SOC / TIM / WLD
- 含まれない 14 category: EMO / ACT / CHG / LOG / MAT / NAT / ABS / BEI / ECO / ELM / REL / SPC / STA / VAL

→ Genesis cid 状態空間で「構造的特異性を持つ」のが知覚 (PER) と存在論 (EXS) と社会 (SOC) と世界 (WLD) に偏在。

### 9.3 v1100 で確認された接続候補の状態

v1100 Code A 候補 6 (null cell ↔ base 優位照合) で:
- Language base 優位 atom (R@1) = {SOC.official, PRP.part} 2 atoms
- Genesis Map 5 null cell atom = 20 atoms (PER/WLD/EXS/PRP/SOC/TIM/BOD/FND)
- **重なり 0、Jaccard 0** = 両系は独立に異なる「文脈非依存性」を捕捉

---

## 10. 最終一文

ESDE Language 凍結時点 (2026-03-03、最終 mtime 2026-03-21) で **生きている (現役相当の) 実装** は `language/` 配下の Phase 8 Sensor (sensor/ 9 files、Molecule 生成) + Synapse v3.5 (`synapse/esde_synapses_v3.json` 5.3MB + 6 patches、WordNet ↔ Atom mapping) + Projection v3.5 (`projection/output_v35/` 4 mode 評価、base R@1=0.96 最高) + Lexicon v2 (`lexicon/` 14+ .py、A1 観測 2 段パイプライン + 5-check Auditor + 326 atoms proposed status 完成) + Observation C (`relations/` 3 files、SVO 抽出 + Grounding v0.3.2) + Synapse Expansion Phase 1-3 (v3.1/v3.2 実走、+5.8pt/+2.0pt 逓減パターン)、326 atoms × 10 軸 × 48 レベル座標系を共通基盤として、テキスト → atom 接地 (Phase 8) + 多義性解消 (Projection 4 mode) + 共鳴度プロファイル (A1) + 自動拡張 (Synapse Expansion) を機能完成、Phase 10 Cell は `esde_cell_architecture.md` v2.3 で設計完了 (Phase 8 ↔ 9 統合、条件因子を「引力」とする Mutual-kNN + k-sweep + Island 検出) だが Python 実装は未着手、Phase 9 Statistics (EdgePolicyResolver / Mutual-kNN / Island / Lens / Weak Axis / k-sweep) はドキュメント上完了表記だが Python 実装は repo 内 grep 0 件 (別 repo / 未移植 / 設計のみ のいずれかは判定不能)、Aruism 原則「記述せよ決定するな」+ 「勝者を決めない」設計 + 「Grounder は Lexicon Core のみ参照」を全 Phase で遵守、326 atoms + 48D 座標 + 25 atoms (Genesis TARGET) + Integration α/β ↔ Phase 10 Cell の構造的同型観察候補が Genesis 側との接続点として確認済 (v1100 候補 6 で R@1 base 優位 2 atoms と Genesis null cell 20 atoms の重なり 0 を実測、両系は独立に異なる「文脈非依存性」を捕捉)、本書は Code A 3 Explore agent 並行調査 (Phase 8 / Lexicon v2 / docs 14 文書) を統合した凍結時点スナップショット、AI 参照用、Code A 以前の認識「Phase 10 Cell ≠ Phase 8+9 Cell」は誤りで正しくは Cell Architecture v2.3 = Phase 10 Cell 設計書を訂正記録。

---

*以上、ESDE Language 凍結状態仕様書。AI 参照用、Taka 依頼「ESDE Language やっていたときの最新状態 (何をやって何ができるか)」への 1 本回答。詳細追求時は §8.1 推奨読書順で `docs/ESDE language/` 14 文書を参照。*
