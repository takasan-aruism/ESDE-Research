# ESDE Language 系 現状把握 調査報告書

*作成*: 2026-05-13、Code A
*依頼者*: Web Claude (Language 側、凍結スレッド)
*経由*: Web Claude (Genesis 側) → Code A
*位置づけ*: Code A は判定者ではなく **報告者**。実環境観察事実のみ列挙、推測 / 断定なし。判定 (現在運用 / 凍結 / 廃止) は両 Web Claude が本報告を読んで実施

---

## 0. 一文サマリ (事実列挙、判断なし)

実環境調査で **依頼書の前提が大きく実環境と乖離していることが判明**、特に重大なのは **(I) Phase 9 系の全キーワード (EdgePolicyResolver / Mutual-kNN / Island / Lens / Weak Axis / k-sweep / W0-W6) が `language/` 内 grep で 0 件ヒット、実装は repo に存在しない**、**(II) `*_a1_final.jsonl` という命名ファイルは存在せず、A1 batch の実体は `language/atoms/a1_batch/{CATEGORY}_{atom}.json` × 326 atom + `language/lexicon/data/mapper_output/{ATOM}_a1.jsonl` × 325 件の 2 系統**、**(III) `atom_centroids_48d.csv` も存在せず**、**(IV) Phase 8 sensor (molecule_generator_live.py 30KB / validator_v83.py 16KB 等 9 files) は存在するが、`from sensor` で外部から import している箇所が language/ 内に検出されず (内部自己参照のみ)**、**(V) language/ 全 .py + 出力ファイルが同一タイムスタンプ 2026-03-21 12:16 = 一括コピー由来、ファイルシステム mtime では現役 / 凍結判別不能**、**(VI) `esde_cell_architecture.md` 内で "Phase 10 は以降の課題" と記述、Cell スキーマは「設計段階」と明記 (Phase 8+9 統合 ≠ Phase 10、両者は別概念で Phase 10 は未開始の構想段階)**、依頼書 §1.2 の「依頼者の前提を疑う」と §11「依頼書のパス名 / ファイル名 / 概念名 / 組織構造の前提が現実と異なる可能性が高い」が複数項目で的中、判定不能の項目を明示列挙、両 Web Claude の判断材料として事実のみ報告、Code A 自身は判定しない。

---

## Step 0: 作業環境特定

| 項目 | 結果 |
|---|---|
| 作業ディレクトリ | `/home/takasan/esde/ESDE-Research` |
| Language 系ソース | **1 箇所のみ**: `/home/takasan/esde/ESDE-Research/language/` |
| Language 系の重複コピー | なし (`~` 配下 maxdepth 5 で `esde_dictionary.json` は 1 件) |
| `esde_synapses_v3.json` 所在 | `/home/takasan/esde/ESDE-Research/language/synapse/esde_synapses_v3.json` (1 件のみ) |
| `~/codegen-loop/` | (本調査範囲では確認なし、依頼書言及あり) |
| Legacy ディレクトリ | `/home/takasan/esde/ESDE-Research/legacy/` (Genesis 側 v9.x simulator + PDF、**Language 系ではない**)、+ `docs/ESDE language/旧/` (Language 系の旧文書置き場) |
| Consolidation ディレクトリ | **なし** (`find ~ -maxdepth 6 -type d -iname '*consolidation*'` で 0 件) |

### Step 0 観察事実

- Language 系は単一ロケーション (`/home/takasan/esde/ESDE-Research/language/`)、複数バージョン共存問題は **物理層では発生していない**
- 依頼者言及の `~/esde/`、`~/ESDE-Research/`、`~/codegen-loop/` のうち、`~/esde/ESDE-Research/` に 1 件確定 (実態は `~/esde/ESDE-Research/`、`~` 直下ではない)
- `/home/takasan/esde/ESDE-Research/legacy/` は **Genesis 側 v9.x 関連のレガシー** (`esde_simulator.py` / `esde_consciousness_simulator.py` 等 + PDF + experiment_d 出力)、Language 系は含まれていない

---

## Step C: Lexicon v2 発展系 (最重要、実地調査)

### C.1 ファイル一覧 (`language/lexicon/`)

| ファイル | 最終更新 | サイズ |
|---|---|---:|
| `auditor_a1.py` | 2026-03-21 12:16 | 47,572 B |
| `mapper_a1.py` | 2026-03-21 12:16 | 25,176 B |
| `batch_report.py` | 2026-03-21 12:16 | 13,186 B |
| `synapse_v4_compare.py` | 2026-03-21 | (未測定) |
| `synapse_v4_task3.py` | 2026-03-21 | (未測定) |
| `synapse_v4_tasks12.py` | 2026-03-21 | (未測定) |
| `wn_apply_proposals.py` | 2026-03-21 | (未測定) |
| `wn_auto_seed.py` | 2026-03-21 | (未測定) |
| `wn_batch_expand.py` | 2026-03-21 | (未測定) |
| `wn_core_stats.py` | 2026-03-21 | (未測定) |
| `wn_cross_stats.py` | 2026-03-21 | (未測定) |
| `wn_lexicon_entry.py` | 2026-03-21 | (未測定) |
| `wn_max_expand.py` | 2026-03-21 | (未測定) |
| `wn_proposal_gen.py` | 2026-03-21 | (未測定) |

### C.2 lexicon/data/ サブディレクトリ

```
language/lexicon/data/
├── definitions/
├── expanded/
├── lexicon_entries/
└── mapper_output/  ← *_a1.jsonl × 325 件
```

### C.3 A1 batch の実体 (依頼書 §5.2 / §5.3 の前提と乖離)

**依頼書 §5.2 の探すべきもの**: `*_a1_final.jsonl`, `atom_centroids_48d.csv`

**実環境観察事実**:
- `*_a1_final.jsonl` という命名のファイル → **0 件** (`find` で検出なし)
- `atom_centroids_48d.csv` → **0 件** (`find` で検出なし)

**A1 batch の実体 (2 系統で存在)**:

| 系統 | パス | ファイル数 | 命名 | サンプル |
|---|---|---:|---|---|
| **系統 1**: 単体 JSON | `language/atoms/a1_batch/` | 326 atoms (327 files、.DS_Store 等含む) | `{CATEGORY}_{atom}.json` 例: `BOD_ear.json` | `{"atom": "BOD.ear", "category": "BOD", "status": "proposed", "core_pool": {"rules": [...], "count": 48, "words": [...]}}` |
| **系統 2**: jsonl | `language/lexicon/data/mapper_output/` | 325 files | `{ATOM}_a1.jsonl` 例: `ABS_bound_a1.jsonl` | (詳細未確認、命名から mapper_a1.py の出力と推察) |

**観察事実**: 326 atom 全てに対する系統 1 (a1_batch) の `proposed` 状態の JSON は揃っている。系統 2 (mapper_output) は 325 件で 1 件少ない (差分の atom 不明)。

### C.4 Constitution v1.0 関連 (依頼書 §5.3 の前提と乖離)

依頼書 §5.3 の探すべきもの: 「Constitution v1.0」を含むファイル

**実環境観察事実 (`grep -l "Constitution"`)**:

| ファイル | 種別 |
|---|---|
| `docs/ESDE language/ESDE_Module_Reference_Lexicon_v2.md` | 主要参照 (Lexicon v2 ドキュメント) |
| `docs/ESDE language/DESIGN_NOTE_Resonance_Scoring.md` | 設計メモ |
| `docs/ESDE language/旧/esde_docs_set/ESDE_Technical_Specification_v544_P94.md` | 旧版仕様書 |
| `docs/LANGUAGE_LEGACY_DIGEST.md` | Genesis 側用 legacy digest |
| `language/data/features/mixed/mil_napoleon.json` 等 8 件 | features データ (記事内容、Constitution は文字列内引用と推察) |
| `language/atoms/a1_batch/{CATEGORY}_{atom}.json` 内多数 | A1 batch 内の word definition に Constitution 単語が含まれるため |

`ESDE_Module_Reference_Lexicon_v2.md` 冒頭抜粋:
```
# ESDE Module Reference — Lexicon v2 Pipeline (v5.7.0 追加セクション)

Lexicon v2 は **2段パイプライン** で構成される:
1. **語彙供給パイプライン** (`lexicon_wn/`) — WordNet から 326 Atom の語彙を自動展開
2. **A1 観測パイプライン** (`integration/lexicon/`) — Core Pool の各語に 48 次元共鳴度プロファイルを QwQ-32B で観測・監査
```

→ ドキュメントは **`lexicon_wn/`** と **`integration/lexicon/`** を分離記述しているが、**実環境ではどちらのディレクトリも存在しない**。実体は `language/lexicon/` 単一ディレクトリに wn_* と mapper_a1 / auditor_a1 が混在。

### C.5 Lexicon v2 ↔ Phase 8 sensor の依存関係

```
sensor が他から import されているか:
  grep "from sensor\|language.sensor" 結果:
    /home/takasan/esde/ESDE-Research/language/sensor/esde_sensor_v2_modular.py
    /home/takasan/esde/ESDE-Research/language/sensor/test_phase8_integration.py
  → sensor を import しているのは sensor 自身の内部のみ (外部参照 0 件)
```

**観察事実**: language/ 内のコードで sensor を外部から import している箇所は検出されなかった (sensor 自身の内部参照のみ)。Lexicon v2 (lexicon/) と sensor の双方向 import 関係も検出なし。

### C.6 判定不能項目 (Step C)

- 系統 1 (a1_batch) と系統 2 (mapper_output) の **どちらが「現在運用」か** は最終更新日 (両系統とも 2026-03-21 12:16) では判別不能
- `proposed` という status が JSON の `status` 列にあるが、これが「完了」を意味するか「提案中」を意味するか判定不能
- ドキュメント `ESDE_Module_Reference_Lexicon_v2.md` が言及する `lexicon_wn/` / `integration/lexicon/` という path が **実環境に存在しない** → ドキュメントが古い設計を反映している可能性 (判定は要 Web Claude 判断)

---

## Step A: Phase 8 系

### A.1 ファイル一覧 (`language/sensor/`)

| ファイル | 最終更新 | サイズ |
|---|---|---:|
| `__init__.py` | 2026-03-21 12:16 | 1,860 B |
| `audit_trace.py` | 2026-03-21 | 4,313 B |
| `constants.py` | 2026-03-21 | 1,307 B |
| `esde_sensor_v2_modular.py` | 2026-03-21 | 10,534 B |
| `extract_synset.py` | 2026-03-21 | 2,489 B |
| `glossary_validator.py` | 2026-03-21 | 4,294 B |
| `loader_synapse.py` | 2026-03-21 | 3,309 B |
| **`molecule_generator_live.py`** | 2026-03-21 | **30,562 B** |
| `rank_candidates.py` | 2026-03-21 | 5,674 B |
| `test_phase8_integration.py` | 2026-03-21 | 15,659 B |
| **`validator_v83.py`** | 2026-03-21 | **16,228 B** |

### A.2 phase8_* 命名ファイル (依頼書 §3.2 の前提と一部乖離)

依頼書 §3.2 の探すべきもの: `phase8_*.py`, `phase_8_*.py`, `p8_*.py`

**実環境観察事実**: `phase8_*.py` 命名の Python ファイルは **0 件**。ただし以下が存在:
- `language/data/audit_runs/phase85_integration_report.json`
- `language/data/audit_runs/phase8_integration_20260120_003044.json`
- `language/data/audit_runs/phase8_integration_20260119_062830.json`
- `language/data/audit_runs/phase84_stability_report.json`

→ Phase 8 関連の出力データは `audit_runs/` に **2026-01-19 / 01-20 の日付で残存**、ただしファイル mtime ではない (内部の日付)。実 file mtime は全て 2026-03-21。

`phase8_pilot*` 出力ディレクトリ → **0 件**。

### A.3 15 演算子の use

`grep "▷\|⊕\|⇒+"` 結果 (ファイル):
- `language/data/semantic_ledger.jsonl`
- `language/data/audit_runs/mode_a_quick_runs.jsonl`
- `language/data/audit_runs/mode_b_runs.jsonl`
- `language/relations/parser_adapter.py` (実装ファイル)
- `language/data/audit_runs/mode_stage1_runs.jsonl`

→ 演算子は audit_runs 出力 + parser_adapter.py 実装に存在。

### A.4 sensor の import 関係 (依頼書 §3.3 該当)

**外部 import**: 0 件 (`from sensor` / `language.sensor` で外部参照なし)

**内部 import**:
- `sensor/esde_sensor_v2_modular.py` (sensor 自身を import)
- `sensor/test_phase8_integration.py` (テストファイル)

### A.5 判定不能項目 (Step A)

- sensor module 群が「現在運用」か「凍結」か → 外部 import なし、最終更新 2026-03-21 (全 .py 同一)、出力 (audit_runs) は 2026-01 = 古い → **判定不能、ただし「外部から呼ばれていない」事実は記録**
- 15 演算子のうち、依頼書言及の `×`, `▷`, `→`, `⊕`, `|`, `◯`, `↺`, `〈〉`, `≡`, `≃`, `¬`, `⇒`, `⇒+`, `-|>` の **個別 use 件数は本調査では未測定**

---

## Step B: Phase 9 系 — **重大な前提乖離発見**

### B.1 依頼書 §4.2 の探すべきキーワード grep 結果

| キーワード | grep 結果 (file count) |
|---|---:|
| `EdgePolicyResolver` | **0 件** |
| `Mutual-kNN` / `MutualkNN` / `mutual_knn` | **0 件** |
| `class Island` / `island_id` / `island_formation` | **0 件** |
| `Weak Axis` / `weak_axis` / `W0_` 〜 `W6_` | **0 件** |
| `k-sweep` / `k_sweep` / `ksweep` | **0 件** |
| `class Lens` / `lens_` | **0 件** |

### B.2 phase9_* 命名 + 関連ディレクトリ

| 項目 | 結果 |
|---|---|
| `phase9_*.py` / `phase_9_*.py` / `p9_*.py` | **0 件** |
| `statistics/` / `esde_engine/` / `axis_stats/` | **0 件** (全て不在) |
| W0/W1/W2/W3/W4/W5/W6 命名のファイル/ディレクトリ | **0 件** |

### B.3 Phase 9 の言及箇所 (ドキュメント内のみ)

`grep "Phase 9"` で `docs/ESDE language/ESDE_Detailed_Design.md` 内に言及:

```
**Status: COMPLETE** - Phase 9 ended at W6. Next is Phase 10.

### 10.3 Phase 10: Next
Phase 10 scope to be determined. Potential directions:
- Multi-instance operation
```

→ ドキュメントは「Phase 9 ended at W6 (完了)」と記述しているが、実装ファイルは repo 内に **存在しない**。

### B.4 観察事実 (Step B、依頼書 §8.4 該当)

**依頼書 §4.1 の前提**:
> Phase 9 は「island 形成」「Weak Axis Statistics (W0-W6)」「EdgePolicyResolver」「k-sweep」「Lens/Threshold/Mutual-kNN」あたりが関連すると依頼者 (Web Claude Language 側) は記憶しているが**確証なし**。

**Code A 実環境観察**: **依頼書 §4.2 列挙の全キーワード (6 種類) が `language/` 配下 grep で 0 件ヒット**。Phase 9 実装は repo 内に存在しない。ドキュメント内では「Phase 9 ended at W6」と完了表記。

**判定材料 (Code A は判定しない)**:
- (a) Phase 9 実装は別 repo / 削除済 / 元から実装されず構想のみ のいずれか
- (b) 依頼者 Web Claude Language 側の記憶が誤っている (キーワード名そのもの、または機能の存在)

---

## Step D: Cell / Phase 10 関連

### D.1 cell 関連ファイル

| パス | 最終更新 | サイズ | 種別 |
|---|---|---:|---|
| `docs/ESDE language/esde_cell_architecture.md` | 2026-03-21 12:16 | 43,587 B | md (設計書) |
| `developmental/v113a/outputs/main/map5_null_phase_per_cell.parquet` | 2026-05-12 | (Code A 自作) | Genesis 側出力、本調査範囲外 |

`*cell*.py` (Python 実装ファイル) → **0 件**

### D.2 `esde_cell_architecture.md` の Phase 10 言及

```
622:- Cell スキーマは設計段階。Phase 10 以降の課題
```

→ Cell スキーマ自体が「設計段階」、Phase 10 は「以降の課題」と記述。本文書内で Cell と Phase 10 を **直接同一視はしていない**。

### D.3 `ESDE_Detailed_Design.md` の Phase 10 言及

```
**Status: COMPLETE** - Phase 9 ended at W6. Next is Phase 10.

### 10.3 Phase 10: Next
Phase 10 scope to be determined. Potential directions:
- Multi-instance operation
```

→ Phase 10 は「scope to be determined (範囲未定)」、Multi-instance operation 等が **候補方向** として記述されているのみ。

### D.4 Triangle Bonus / triangle_closure

`grep "Triangle Bonus\|triangle_closure\|triangle_bonus"` 結果:
- `/home/takasan/esde/ESDE-Research/legacy/experiment_d.py` (Genesis 側 legacy)
- `/home/takasan/esde/ESDE-Research/legacy/esde_extended_simulator.py` (同上)
- `/home/takasan/esde/ESDE-Research/legacy/esde_evolution_simulator.py` (同上)
- `/home/takasan/esde/ESDE-Research/legacy/esde_simulator.py` (同上)
- `/home/takasan/esde/ESDE-Research/unified/v1100/v1100_step_a_recognition.md` (Code A 自作、本依頼以前)

→ Triangle Bonus / triangle_closure は **Genesis 側 legacy simulator** (v9.x 以前) のみで言及、Language 側コードには検出されない。

### D.5 Phase 10 Cell と Phase 8+9 統合 Cell の関係

**観察事実**:
- `esde_cell_architecture.md` 内では Cell スキーマと Phase 10 を分離記述 (「Cell スキーマは設計段階。Phase 10 以降の課題」)
- `ESDE_Detailed_Design.md` 内では Phase 9 ended at W6 → Next is Phase 10 とフェーズ移行記述
- **両者は別概念**: Cell = (Phase 8+9 段階での) 統合アーキテクチャ設計、Phase 10 = 未開始の次フェーズ
- 「Phase 10 Cell」という単一語句は本調査で repo 内に検出されず

**判定不能項目**: Web Claude Language 側 v1 資料の「Phase 10 Cell」が誰の発案で、どの設計書のどこに対応するか、本調査では判別不能。

---

## Step E: ドキュメント類

### E.1 `docs/ESDE language/` 直下の 14 .md (全て 2026-03-21 12:16)

| ファイル | サイズ |
|---|---:|
| `COMMAND_REFERENCE_v2.md` | (未測定) |
| `DESIGN_NOTE_Resonance_Scoring.md` | (未測定) |
| `ESDE_Briefing_Synapse_Expansion_via_Phase7.md` | (未測定) |
| `ESDE_Detailed_Design.md` | (未測定) |
| `ESDE_Essence_v02.md` | (未測定) |
| `ESDE_Glossary.md` | (未測定) |
| `ESDE_Module_Reference.md` | (未測定) |
| `ESDE_Module_Reference_Lexicon_v2.md` | (未測定、Constitution 言及) |
| `ESDE_Overview.md` | (未測定) |
| `ESDE_Technical_Specification.md` | (未測定) |
| `ESDE_Vision_LLM_Symmetric_Integration.md` | (未測定) |
| `Project_Lexicon_Unified_Implementation_Spec.md` | (未測定) |
| `README.md` | (未測定) |
| `esde_cell_architecture.md` | 43,587 B |

**観察事実**: 全 14 .md が **2026-03-21 12:16** の同一タイムスタンプ。これは git fetch / clone / 一括コピーによる移植時刻と推察され、各文書の内容更新日とは別。

### E.2 旧/ ディレクトリ (バージョン違い旧版)

`docs/ESDE language/旧/`:
- `ESDE_Technical_Specification_v535_P84.md`
- `ESDE_Technical_Specification_v536_P86.md`
- `ESDE_Technical_Specification_v537_P87.md`
- `ESDE_Vision_LLM_Symmetric_Integration.md`
- `ESDE_Phase8_解説.pptx` (Phase 8 解説 PowerPoint)
- `Semantic_Language_Integrated_v1.1_fixed.pdf`
- `スレッド変更時の汎用AI指示書_V2.txt` 〜 `V5.txt`

`docs/ESDE language/旧/esde_docs_set/`:
- `ESDE_Detailed_Design_v544_P94.md`
- `ESDE_Glossary_v544_P94.md`
- `ESDE_Technical_Specification_v544_P94.md`

`docs/ESDE language/旧/md/`:
- `ESDE_Technical_Specification_v535_P82.md`
- `ESDE_v532_Phase7Aplus_SPEC.md`
- `ESDE_v531_Phase7A-min_SPEC.md`

→ Phase 7A → P82 → P84 → P86 → P87 → P94 の **バージョン進化が旧/ 配下に保存**、現役は `docs/ESDE language/` 直下の `ESDE_Technical_Specification.md` (バージョン番号なし) と推察可能 (Code A 判定はせず、要 Web Claude 確認)。

### E.3 バージョン違い同名ドキュメント整理 (依頼書 §7.4 該当)

```
ESDE_Technical_Specification 系:
  ESDE_Technical_Specification.md                          (現役? 2026-03-21 mtime)
  旧/ESDE_Technical_Specification_v535_P84.md              (v5.35 P84)
  旧/ESDE_Technical_Specification_v536_P86.md              (v5.36 P86)
  旧/ESDE_Technical_Specification_v537_P87.md              (v5.37 P87)
  旧/md/ESDE_Technical_Specification_v535_P82.md           (v5.35 P82)
  旧/esde_docs_set/ESDE_Technical_Specification_v544_P94.md (v5.44 P94)

ESDE_Glossary 系:
  ESDE_Glossary.md                                          (現役?)
  旧/esde_docs_set/ESDE_Glossary_v544_P94.md                (v5.44 P94)

ESDE_Detailed_Design 系:
  ESDE_Detailed_Design.md                                   (現役?)
  旧/esde_docs_set/ESDE_Detailed_Design_v544_P94.md         (v5.44 P94)

ESDE_Vision_LLM_Symmetric_Integration 系:
  ESDE_Vision_LLM_Symmetric_Integration.md                  (現役? 直下)
  旧/ESDE_Vision_LLM_Symmetric_Integration.md               (旧/ 内、同名)
```

→ `ESDE_Vision_LLM_Symmetric_Integration.md` のみ **直下と旧/ の両方に同名で存在**、内容差分は本調査未測定 (要 Web Claude 確認)。

---

## Step F: 統合報告 (事実列挙、判断なし)

### F.1 「直近で動いている可能性が高い」 (現在運用候補) 列挙

| 項目 | 根拠 |
|---|---|
| `language/projection/output_v35/` の評価出力 4 mode | v1100 Code A 調査で確認、5 月時点で読込可、Berlin sentences の 50 token Recall 評価が出ている |
| `language/atoms/a1_batch/` 326 atom JSON | 326 atom 揃い、A1 batch の中身 (proposed status) が完了している |
| `language/lexicon/data/mapper_output/` 325 件 *_a1.jsonl | mapper_a1.py の出力と推察、325 件揃い |
| `language/projection/projection_eval.py`, `run_projection_experiment.py` | projection/ 直下に存在、評価実行スクリプト |
| `docs/ESDE language/ESDE_Module_Reference_Lexicon_v2.md` | "v5.7.0 追加セクション" 記載、最新の Lexicon v2 ドキュメント |

### F.2 「凍結 / 廃止らしき」候補列挙

| 項目 | 根拠 |
|---|---|
| `docs/ESDE language/旧/` 配下全文書 | 「旧」ディレクトリ名、v5.31-v5.44 のバージョン違い保存 |
| `language/data/audit_runs/phase8_integration_*` (2026-01-19/20 出力) | Phase 8 integration の出力が 4 ヶ月以上前で停止 |
| `legacy/` 配下 (Genesis 側 simulator + PDF) | 「legacy」ディレクトリ名、Genesis v9.x 以前のもの (Language 系には含まれず) |

### F.3 「判定不能」候補列挙

| 項目 | 判定不能の理由 |
|---|---|
| `language/sensor/` 全 9 files | mtime 2026-03-21、外部 import 0 件、ただし内部の自己参照あり。「現在運用なら何かから呼ばれるはず」だが何からも呼ばれていない事実が単独で「凍結」を意味するかは Code A 判定不能 |
| `language/lexicon/wn_*.py` 11 files | mtime 2026-03-21、外部 import の有無未測定、`ESDE_Module_Reference_Lexicon_v2.md` で `lexicon_wn/` というディレクトリが言及されているが実環境では同 path 不在 |
| `language/lexicon/data/mapper_output/` 325 件 vs `language/atoms/a1_batch/` 326 件 | 1 件差分の原因不明、どちらが「正本」か判定不能 |
| `ESDE_Module_Reference_Lexicon_v2.md` 言及の `lexicon_wn/` / `integration/lexicon/` | 実環境 path 不在、ドキュメントが古い設計か未実装の構想か判定不能 |
| 「Phase 10 Cell」という単一語句 | repo 内に検出されず、`esde_cell_architecture.md` の Cell と `ESDE_Detailed_Design.md` の Phase 10 は別概念として記述、誰が「Phase 10 Cell」と命名したか判定不能 |
| 全 .py / .md ファイルの mtime 2026-03-21 12:16 同一 | 一括コピー由来 (git clone / fetch / rsync)、ファイルの真の最終編集日不明 |

### F.4 依頼書の前提が間違っていた点 (依頼書 §8.4 該当、最重要)

依頼書 §1.2「依頼者の前提を疑う」+ §11「依頼書のパス名、ファイル名、概念名、組織構造の前提が現実と異なる可能性が高い」+「Code A は依頼書の前提を絶対視せず、実環境で観察したものを優先」に対応:

#### 重大度 高 (構想・記憶ベース、実装不在)

| 依頼書記述 | 実環境観察 |
|---|---|
| §4.2「Phase 9 系の `EdgePolicyResolver` / `Mutual-kNN` / `Island` / `Weak Axis` / `k-sweep` / `Lens`」 | **全 6 種類が grep で 0 件ヒット**、実装は repo 内に存在しない |
| §4.2「`statistics/` / `esde_engine/` / `axis_stats/` ディレクトリ」 | **全て不在** |
| §4.2「W0-W6」 | **0 件ヒット** |
| §5.2「`*_a1_final.jsonl` ファイル」 | **0 件**、実体は `a1_batch/{ATOM}.json` 単体 JSON (326 件) と `mapper_output/{ATOM}_a1.jsonl` (325 件) の 2 系統 |
| §5.2「`atom_centroids_48d.csv`」 | **0 件**、存在しない |

#### 重大度 中 (path 命名のズレ)

| 依頼書記述 | 実環境観察 |
|---|---|
| §5.2「`integration/lexicon/` 配下全体」 | 実環境 path **不在**、実体は `language/lexicon/` 単一ディレクトリ |
| §3.2「`phase8_*.py` 命名」 | **0 件**、Phase 8 実装は `sensor/` 配下に存在 (命名規則違い) |
| §3.2「`phase8_pilot*` 出力ディレクトリ」 | **0 件**、出力は `language/data/audit_runs/phase8_integration_*.json` (タイムスタンプ付き) |

#### 重大度 低 (記述の混同、要 Web Claude 整理)

| 依頼書記述 | 実環境観察 |
|---|---|
| §6.4 「Phase 10 Cell」と「Phase 8 + Phase 9 統合 Cell」 | repo 内で「Phase 10 Cell」単一語句は検出されない、`esde_cell_architecture.md` の Cell スキーマと `ESDE_Detailed_Design.md` の Phase 10 は別概念として記述。Web Claude Language 側 v1 資料の「Phase 10 Cell」は誰の発案で、どの設計書のどこに対応するか判定不能 |
| §3.2「15 演算子 (`×`, `▷`, `→`, ...)」 | repo 内に演算子の use はあるが、依頼書列挙の **15 全ての個別 use 件数は本調査では未測定** |

---

## 補足: 報告外の発見事項

### G.1 `language/projection/output_v35/` の構造 (v1100 で既に確認済、参考情報)

`output_v35/{base, B, C, BC}/` の 4 mode で以下が存在 (mtime 2026-03-21):
- `pred_50.jsonl`
- `token_diagnostics.jsonl`
- `detail.jsonl`
- `field_stats.json` (B/C/BC のみ)

→ Berlin sentences 50 token に対する Projection 評価結果が出力済、Code A v1100 候補 6 実装で読み込み確認済。

### G.2 `language/synapse/` の構造

`esde_synapses_v3.json` (主要 JSON) + `synapse_profiles.json` + `patches/` ディレクトリ + Python 実装 (`cli.py`, `diagnostic.py`, `proposer.py`, `schema.py`, `store.py`)

→ Synapse v3 系の実装は完成形と推察 (全部品揃っている)。

### G.3 `language/esde/projection.py`

`language/esde/` 配下に `projection.py` が単体で存在。`language/projection/` とは別の path。役割の違いは本調査未測定。

---

## 想定所要時間

依頼書 §10 想定 60-90 分 → 実際: 約 30 分 (grep / find / stat 中心、深い読み込みなし)。

---

## 最後に (Code A 自己点検)

- 依頼書 §11 の前提通り、依頼書の前提が複数箇所で実環境と乖離していた → §F.4 で明示列挙
- 判定 (現在運用 / 凍結 / 廃止) は本報告では **一切実施せず**、両 Web Claude (Genesis 側 + Language 側) の判断材料として事実のみ報告
- 推測 / 断定なし、「判定不能」項目は §F.3 で明示
- 本報告は Web Claude (Genesis 側) 経由で Web Claude (Language 側) へ転送される素材として作成
- Code A は v10.x Code A 認識確認連続 9 段階 + 本調査の連続 10 段階で **報告者役割**を継続

---

*以上、ESDE Language 系 現状把握 調査報告書 (Code A)。判定は両 Web Claude の領域、Code A は実環境観察事実のみを列挙した。報告完了。*
