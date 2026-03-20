# ESDE Technical Specification v5.3.5-P8.4

## Extended Semantic Differential Engine
### Based on Existence Symmetry Dynamic Equilibrium Framework

Version: 5.3.5-P8.4  
Date: 2026-01-13  
Status: Production (Phase 8-4 Complete - Stability Audit Passed)

---

## 0. Purpose and Scope

### 0.1 What ESDE Is

> ESDEは証明システムではない。  
> ESDEは生成言語モデルではない。  
> ESDEは意味構造上で動作する動的均衡エンジンである。  
> **ESDEはAIの内省エンジン（Introspection Engine）である。**

ESDEを使用するとは以下を意味する：

- 現実世界の言語やイベントを構造化された意味空間にマッピングする
- 不均衡と矛盾を明示的な誤差値（ε）として測定する
- 制約付き更新を通じて動的均衡を回復する
- 均衡が硬直した場合に制御されたRebootをトリガーする
- 単なる物語的応答ではなく、構造化された洞察を返す

### 0.2 Philosophical Foundation

ESDE is based on **Aruism Philosophy** and the **ESDE Framework**.

#### Aruism (The Root)

- **「ある（Aru）」の優先**: 世界は「定義」される前にまず「ある」
- ESDEは観測対象を既存の枠組みに無理やり当てはめるのではなく、「そこにある曖昧な状態」をそのまま保持・観測するための基盤（OS）である
- **二項対立の回避**: 「AかBか」の二者択一を迫ることは、Aruismの否定となる

#### ESDE Theory (The Logic)

- **公理T (Ternary Emergence)**: 「AとB」の二者関係だけでは存在は顕現しない。第三項（Observer）が介入することで初めて意味が立ち上がる
- **創造と破壊の対称性**: 「揺れ（Volatility）」や「未決（Winner=Null）」はエラーではなく、「破壊的創発（Destructive Emergence）」の兆候である可能性がある

#### Core Axioms (v3.3)

| Axiom | Name | Statement |
|-------|------|-----------|
| 0 | Aru (There Is) | The primordial fact of existence |
| E | Identification | E = {e1, e2, ..., en} |
| L | Linkage | L: E × E → [0,1] |
| Eq | Equality | All existences equal in status |
| C | Creativity | C ⊥ gradient(F) |
| U | Understanding | Ongoing participatory engagement |
| ε | Error | E = f(I) + ε, ε ≠ 0 |
| T | Ternary Emergence | A↔B↔C ⇒ Manifestation |

---

## 1. Semantic Hierarchy

### 1.1 Semantic Atoms

**326** semantic atoms are defined. These are the most primitive concepts closest to "Aru" (existence).

Characteristics:
- Irreducible fundamental meanings
- **163 symmetric pairs**
- Defined by Glossary (not by dictionary or kanji)

#### Examples of Symmetric Pairs

| Concept A | Concept B |
|-----------|-----------|
| EMO.love | EMO.hate |
| EXS.life | EXS.death |
| VAL.truth | VAL.falsehood |
| ACT.create | ACT.destroy |
| STA.peace | STA.war |
| ABS.bound | ABS.release |
| SOC.cooperate | SOC.conflict |

#### Category Codes (24 categories)

```
FND: Fundamental    EXS: Existence      EMO: Emotion
ACT: Action         CHG: Change         VAL: Value
STA: State          COG: Cognition      COM: Communication
PER: Perception     BOD: Body           BEI: Being
SOC: Social         ECO: Economic       SPC: Space
TIM: Time           ELM: Element        NAT: Nature
MAT: Material       REL: Relation       LOG: Logic
WLD: World          ABS: Abstract       PRP: Property
```

### 1.2 Axes and Levels (10 Axes, 48 Levels)

Semantic atoms alone do not "point to" anything specific. Only when axis and level are specified does a concrete position emerge.

| Axis | Levels | Count |
|------|--------|-------|
| temporal | emergence → indication → influence → transformation → establishment → continuation → permanence | 7 |
| scale | individual → community → society → ecosystem → stellar → cosmic | 6 |
| epistemological | perception → identification → understanding → experience → creation | 5 |
| ontological | material → informational → relational → structural → semantic | 5 |
| interconnection | independent → catalytic → chained → synchronous → resonant | 5 |
| resonance | superficial → structural → essential → existential | 4 |
| symmetry | destructive → inclusive → transformative → generative → cyclical | 5 |
| lawfulness | predictable → emergent → contingent → necessary | 4 |
| experience | discovery → creation → comprehension | 3 |
| value_generation | functional → aesthetic → ethical → sacred | 4 |

**Total: 48 levels**

### 1.3 Design Philosophy (Aruism Mapping)

The semantic architecture directly implements core Aruism concepts:

#### Equality of Existence → winner=null

> あらゆる存在が、その価値や重要性において等しく相互依存的であり、
> 欠けることのできない全体の構成要素として対等に扱われる。

Implementation: No hypothesis is privileged over another. `winner` remains `null` always. All routes (A/B/C/D) are evaluated with equal weight.

#### Symmetry of Existence → 163 Pairs

> 一つの存在に対して自然と対称的に生じる存在や概念の関係性。
> 異なる視点や状況によって反転しうる相補的な関係性。

Implementation: 326 atoms = 163 symmetric pairs. This is not binary opposition but mutual definition. `love` cannot be defined without `hate`. ε_sym measures imbalance between pairs.

#### Linkage of Existence → w_ij

> あらゆる存在が相互作用し合い、連動して現象や状況を生み出している。

Implementation: Linkage weight `w_ij` between concepts. Co-occurrence strengthens links. ε_link measures inconsistency in linked concepts.

#### Axis → 10 Axes

> 複雑な現実から関連性の強い存在群を見つけ出し、
> 意味ある一つのまとまりとして統合・囲い込む認識機能。

Implementation: 10 axes are not domain categories (emotion, economy, etc.) but **observation perspectives** applicable to any existence. They answer:

| Question | Axis |
|----------|------|
| When? How long? | temporal |
| Where? How big? | scale |
| How is it known? | epistemological |
| What is it? | ontological |
| How connected? | interconnection, resonance |
| What direction? | symmetry |
| How predictable? | lawfulness |
| What experience? | experience |
| What value? | value_generation |

### 1.4 State Space

```
State Vector: x_t[i, a]
    i = concept ID (326)
    a = axis ID (48)
    value = activation intensity (0.0〜1.0)

State Space Size: 326 × 48 = 15,648 dimensions
```

---

## 2. Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ESDE Framework                            │
│         (Existence Symmetry Dynamic Equilibrium)             │
│                   Aruism Philosophy                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ESDE Components                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Glossary   │   Synapse    │    Sensor    │     Engine     │
│  Atom Defs   │   Bridge     │   Input      │    State       │
│   326 atoms  │  WordNet     │  Operators   │   ε Calc       │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

### 2.2 Component Status

| Component | Status | Implementation | Issue |
|-----------|--------|----------------|-------|
| Glossary | ✅ Stable | 326 atoms, 10×48 definitions | - |
| Synapse | ✅ Generated | 2,116 edges, vector distance (raw_score) | - |
| Sensor | ✅ **V2 + Live** | Synapse lookup + Legacy fallback | - |
| Generator | ✅ **Live (QwQ)** | Phase 8-3 MoleculeGeneratorLive | - |
| Validator | ✅ **Production** | Phase 8-2 MoleculeValidator | - |
| Engine | ✅ Working | State management, ε calculation | - |
| Audit Pipeline | ✅ Complete | 7A → 7D | - |
| **Stability Audit** | ✅ **PASS** | Phase 8-4 (3500 runs) | - |

### 2.3 Integration Status

```
BEFORE (Disconnected):

┌─────────────────┐          ┌─────────────────┐
│   Sensor v1     │          │   Synapse       │
│   (Legacy)      │    ??    │   (v2.1.0)      │
│ Trigger-based   │◄────────►│ Vector distance │
└─────────────────┘   NOT    └─────────────────┘
                   CONNECTED

AFTER (Sensor V2 - Integrated):

┌─────────────────┐          ┌─────────────────┐
│   Input Text    │          │   Synapse       │
│                 │          │   (v2.1.0)      │
└────────┬────────┘          └────────┬────────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────┐
│              Sensor V2 (Unified)             │
│                                              │
│  1. Tokenize → WordNet synset lookup        │
│  2. Synapse lookup → concept candidates     │
│  3. Vector distance (raw_score) ranking     │
│  4. Deterministic sort (score DESC, id ASC) │
│  5. Fallback: Legacy triggers (Hybrid mode) │
│  6. Output: concept_id + axis + level       │
└─────────────────────────────────────────────┘
```

**Implementation File:** `esde_sensor_v2.py`

### 2.4 Data Flow Pipeline

```
1. User Text → esde_sensor.py → Formula
2. Formula → esde-engine-v532.py → Known or Queue
3. Queue → resolve_unknown_queue_7bplus_v534_final.py ↔ aggregate_state.py
4. Resolver → online.py → hypothesis.py → Ledger & Aggregate Output
```

### 2.3 Key File Groups

#### Group A: The Brain (Resolver / Phase 7B+)

| File | Role |
|------|------|
| `resolve_unknown_queue_7bplus_v534_final.py` | Phase 7B+ main CLI. Maintains `winner=null` |
| `esde_engine/resolver/hypothesis.py` | 4-hypothesis evaluation (A/B/C/D) |
| `esde_engine/resolver/aggregate_state.py` | Observation state management |
| `esde_engine/resolver/online.py` | External evidence collection (v5.3.5: MultiSourceProvider) |

#### Group B: The Heart (Runtime Engine / Phase 7A+)

| File | Role |
|------|------|
| `esde-engine-v532.py` | Tokenization, Synapse activation, Routing |

#### Group C: The Senses (Input Sensor)

| File | Role | Status |
|------|------|--------|
| `esde_sensor.py` | Legacy: Trigger-based + LLM | Superseded by V2 |
| `esde_sensor_v2_modular.py` | **Facade: Synapse-integrated** | ✅ **Implemented** |
| `sensor/` | **Modular components package** | ✅ **Phase 8** |

**sensor/ Package Structure:**

| Module | Class | Role |
|--------|-------|------|
| `__init__.py` | - | Package exports (lazy import for 8-2/8-3) |
| `loader_synapse.py` | SynapseLoader | JSON load, singleton |
| `extract_synset.py` | SynsetExtractor | WordNet extraction |
| `rank_candidates.py` | CandidateRanker | Score aggregation |
| `legacy_trigger.py` | LegacyTriggerMatcher | v1 fallback |
| `audit_trace.py` | AuditTracer | Counters/hash/evidence |
| `molecule_validator.py` | MoleculeValidator | Phase 8-2 validation |
| `molecule_generator.py` | MoleculeGenerator | Phase 8-2 LLM generation (mock) |
| `molecule_generator_live.py` | MoleculeGeneratorLive | **Phase 8-3** Real LLM integration |

**Phase 8-3 Classes (molecule_generator_live.py):**

| Class | Role |
|-------|------|
| `MoleculeGeneratorLive` | Real LLM (QwQ-32B) integration with guardrails |
| `SpanCalculator` | System-calculated span (token proximity) |
| `CoordinateCoercer` | Invalid coordinate → null with logging |
| `FormulaValidator` | Formula syntax validation (consecutive operators) |
| `MockMoleculeGeneratorLive` | Test mock |

#### Group D: The Knowledge (Synapse Generator)

| File | Role |
|------|------|
| `generate_synapses_v2_1.py` | Connect ESDE concepts to WordNet |

---

## 3. Directory Structure

```
esde/
├── esde_engine/                     # Main package directory
│   ├── __init__.py                  # Package initialization & exports
│   ├── __main__.py                  # CLI entry point
│   ├── config.py                    # Configuration constants (SINGLE SOURCE OF TRUTH)
│   ├── utils.py                     # Utility functions
│   ├── loaders.py                   # Data loaders
│   ├── extractors.py                # Synset extraction
│   ├── collectors.py                # Activation collection
│   ├── routing.py                   # Unknown token routing (7A+)
│   ├── queue.py                     # Unknown queue writer (7A)
│   ├── engine.py                    # Main ESDEEngine class
│   │
│   └── resolver/                    # Phase 7B/7B+: Unknown Queue Resolver
│       ├── __init__.py              # Package exports
│       ├── state.py                 # Queue state management (legacy)
│       ├── aggregate_state.py       # [v5.3.4] Aggregate state management
│       ├── hypothesis.py            # Multi-hypothesis evaluation (A/B/C/D)
│       ├── online.py                # [v5.3.5] MultiSourceProvider
│       ├── ledger.py                # Evidence ledger (audit trail)
│       ├── cache.py                 # Search cache
│       ├── patches.py               # Patch output management
│       └── resolvers.py             # Route-specific resolvers
│
├── sensor/                          # [Phase 8] Modular Sensor Package
│   ├── __init__.py                  # Package exports (lazy import)
│   ├── loader_synapse.py            # SynapseLoader (singleton)
│   ├── extract_synset.py            # SynsetExtractor (WordNet)
│   ├── rank_candidates.py           # CandidateRanker (aggregation)
│   ├── legacy_trigger.py            # LegacyTriggerMatcher (v1 fallback)
│   ├── audit_trace.py               # AuditTracer (counters/hash)
│   ├── molecule_validator.py        # [Phase 8-2] MoleculeValidator
│   ├── molecule_generator.py        # [Phase 8-2] MoleculeGenerator (mock)
│   └── molecule_generator_live.py   # [Phase 8-3] MoleculeGeneratorLive (Real LLM)
│
├── esde_sensor.py                   # Semantic Operators v1.1.0 (Legacy)
├── esde_sensor_v2_modular.py        # [Phase 8] Sensor V2 Facade
├── esde-engine-v532.py              # Runtime Engine v5.3.2
├── resolve_unknown_queue_7bplus_v534_final.py  # Phase 7B+ CLI
├── generate_synapses_v2_1.py        # Synapse generator
├── esde_glossary_pipeline_v5_1.py   # Glossary pipeline
├── esde_meta_auditor.py             # Phase 7D Meta-Auditor
│
├── # [Phase 8-4] Stability Audit
├── esde_stability_audit.py          # Stability audit CLI
├── mode_a_quick_test.py             # Mode A drift test
├── audit_corpus.jsonl               # 100 test sentences (5 categories)
├── test_phase83_audit.py            # Phase 8-3 audit tests
│
└── data/                            # Runtime data directory
    │
    ├── audit_runs/                  # [Phase 8-4] Audit logs
    │   ├── mode_a_runs.jsonl        # Mode A raw logs
    │   ├── mode_b_runs.jsonl        # Mode B raw logs
    │   ├── mode_a_quick_runs.jsonl  # Quick test logs
    │   ├── mode_a_quick_drift_report.json  # Drift A/B/C report
    │   └── phase84_stability_report.json   # Final stability report
    │
    ├── # Phase 7A: Unknown Token Queue
    ├── unknown_queue.jsonl
    │
    ├── # Phase 7B+ (v5.3.4): Aggregate-Level Resolution
    ├── unknown_queue_state_7bplus.json
    ├── unknown_queue_7bplus.jsonl
    ├── evidence_ledger_7bplus.jsonl
    │
    ├── # Phase 7C/7C': Audit
    ├── audit_log_7c.jsonl
    ├── audit_votes_7cprime.jsonl
    ├── audit_drift_7cprime.jsonl
    │
    ├── # Phase 7D: Meta-Audit
    ├── audit_rules_review_7d.json
    │
    ├── # Patch Outputs (Human Review Required)
    ├── patch_alias_add.jsonl
    ├── patch_synapse_add.jsonl
    ├── patch_stopword_add.jsonl
    ├── patch_molecule_add.jsonl
    │
    └── cache/                       # Search cache directory
```

---

## 4. Binary Emergence Model

### 4.1 Two Information Sources

```
A. Prior Structure (経験則)
    - 326 concept definitions
    - 163 symmetric pair relationships
    - 10 axes × 48 levels
    - Structural knowledge: "war and peace should be symmetric"

B. Accumulated Data (蓄積データ)
    - Occurrence frequency (count)
    - Linkage weights (w_ij)
    - Temporal patterns

Emergence:
    (Prior Structure ↔ Accumulated Data) ⇒ Introspection
```

### 4.2 Ternary Emergence

Time enters as the third term:

```
(Prior Structure ↔ Accumulated Data) ↔ Time ⇒ Deep Introspection

1st observation: Time = 0, prior vs observation only
nth observation: Time becomes meaningful, ternary complete
```

### 4.3 Weight Calculation

```python
# Binary Composite Weight
weight[i] = α_t × data_weight[i] + (1 - α_t) × structure_weight[i]

# Composite Coefficient
α_t = min(0.7, n / 100)
    # n = 0:   α_t = 0.0 (prior only)
    # n = 100: α_t = 0.7 (data dominant, capped)
```

---

## 5. Observation Model

### 5.1 Principle

> Observation Principle: Record at maximum resolution

LLM Responsibility:
- Identify concept
- Specify axis and level
- Specify sub-level (when possible)
- Record evidence text

### 5.2 Observation vs Analysis Granularity

```
Storage: Save everything at maximum resolution
Analysis: Select granularity based on data volume

Phase 1 (~100 observations):    concept_id only
Phase 2 (100~1000):             concept_id + axis
Phase 3 (1000~):                concept_id + sub_level + axis + level
```

Benefits:
- Data doesn't decay (can analyze in detail later)
- No re-collection needed
- Scalable
- No unrealistic precision demands early on

---

## 6. Semantic Operators (Molecules)

### 6.1 Purpose

Structure semantic atoms into molecules via operators.

> Operators do NOT "determine" meaning. They only provide structure.  
> Do not generate winners.  
> Preserve volatility.

### 6.2 Operator List (v0.3)

| Operator | Name | Description |
|----------|------|-------------|
| × | Connection | A × B (connect two semantic units) |
| ▷ | Action | A ▷ B (A acts on B) |
| → | Transition | A → B (state/meaning change) |
| ⊕ | Juxtaposition | A ⊕ B (simultaneous presentation) |
| \| | Condition | A \| B (A under condition B) |
| ◯ | Target | A × ◯ (target of A) |
| ↺ | Recursion | A ↺ A (self-reference) |
| 〈〉 | Hierarchy | 〈A × B〉 (internal structure/scope) |
| ≡ | Equivalence | A ≡ B (theoretical identity) |
| ≃ | Practical Equivalence | A ≃ B (equivalence within ε) |
| ¬ | Negation | ¬A (meaning inversion) |
| ⇒ | Emergence | A ⇒ B (unspecified direction) |
| ⇒+ | Creative Emergence | New meaning generation |
| -\|> | Destructive Emergence | Structure reset/reboot |

### 6.3 Expression Capacity

```
Semantic Atoms: 326
Axes × Levels: 48 patterns
Base Patterns: ~15,000

+ Semantic Operators
= Billions of expressions (Molecules)
```

### 6.4 Sensor I/O Example (Current Legacy Behavior)

**Input:**
```
"I cannot forgive you."
```

**Processing:**
```
Step 1: Trigger match → "forgive" hits EMO.forgiveness
Step 2: Negation detected → "cannot"
Step 3: Entity detected → "you" = ◯ (other)
Step 4: Formula = ¬(EMO.forgiveness × ◯)
Step 5: Resolve ¬EMO.forgiveness → NEGATION_MAP → SOC.refuse
```

**Output:**
```json
{
  "concept_id": "SOC.refuse",
  "axis": "interconnection",
  "level": "independent",
  "evidence": "Formula: ¬(EMO.forgiveness × ◯)",
  "_formula": {"type": "EXPR", "op": "¬", "args": [...]},
  "_extracted": "EMO.forgiveness"
}
```

**Note:** This is legacy behavior. Future integration should use Synapse vector lookup before trigger matching.

---

## 7. Error (ε) Measurement

### 7.1 Symmetry Error

```python
ε_sym[i] = | weight[i] - weight[symmetric(i)] |
ε_sym_total = Σ ε_sym[i] / num_pairs
```

### 7.2 Linkage Error

```python
ε_link = Σ_{(i,j)} w_ij × || x[i,:] - x[j,:] ||²
```

### 7.3 Total Error

```python
ε_total = λ_sym × ε_sym_total + λ_link × ε_link
```

### 7.4 Interpretation

ε is not "error" but "evidence that structure is alive".

```
ε = 0:  Perfect equilibrium (rigid, dead)
ε > 0:  Dynamic equilibrium (alive)
ε >> threshold: Imbalance (sign of Reboot)
```

---

## 8. Audit Pipeline (Phase 7)

### 8.1 Philosophy: Volatility-First

> "Is this understood correctly?"  
> → "What does 'correct' even mean?"  
> → "Correctness always fluctuates"  
> → **Volatility Detection**

### 8.2 Pipeline Overview

```
Phase 7A:  Unknown Queue Collection
Phase 7B:  Aggregation & Priority
Phase 7B+: Evidence Collection (Web Search)
Phase 7C:  Structural Audit
Phase 7C': LLM Semantic Audit
Phase 7D:  Meta-Auditor (Rule Calibration)
```

### 8.3 Phase 7B+: Evidence Collection

External evidence collection for unknown tokens.

**v5.3.5 Update**: SearXNG → MultiSourceProvider

| Source | Type | Use Case |
|--------|------|----------|
| Free Dictionary API | Dictionary | Primary definitions |
| Wikipedia API | Encyclopedia | Proper nouns, concepts |
| Datamuse API | WordNet | Related words |
| Urban Dictionary | Slang | Informal language |
| DuckDuckGo | Web Search | Final fallback |

#### Performance Comparison

| Metric | v5.3.4 (SearXNG) | v5.3.5 (MultiSource) |
|--------|------------------|----------------------|
| Success Rate | 89% | **100%** |
| Quarantine | 45% | **6%** |
| Candidate | 20% | **49%** |
| Avg Volatility | 0.407 | **0.177** |

### 8.4 Four Hypothesis Routes

| Route | Name | Description |
|-------|------|-------------|
| A | Typo | Edit distance, spell check |
| B | Entity | Proper noun, searchable term |
| C | Novel | New concept, requires molecule |
| D | Noise | Discard or defer |

### 8.5 Classification Output

| Status | Symbol | Volatility | Action |
|--------|--------|------------|--------|
| Candidate | ○ | < 0.3 | Proceed |
| Deferred | ◐ | 0.3 - 0.6 | More observation |
| Quarantine | ● | > 0.6 | Human review |

### 8.6 Strict Invariants

1. **Winner MUST remain null** in 7B+ outputs
2. **Configuration is SINGLE SOURCE OF TRUTH**: Use `config.py` only
3. **Ledger is append-only**: Never rewrite past entries
4. **Patches are emitted but never auto-applied**: Human review mandatory
5. **State controls flow**: `aggregate_state.py` is the only place for reprocess/observation logic
6. **Determinism**: Resolver must be deterministic with MockSearchProvider

---

## 9. Development Environment

### Hardware

| Component | Specification |
|-----------|---------------|
| Client | MacBook Pro M3 / 8GB / 512GB |
| Host CPU | AMD Ryzen Threadripper PRO 7965WX 24-Cores (48 logical) |
| GPU | NVIDIA GeForce RTX 5090 x2 (32GB VRAM each) |
| Driver | 570.158.01 |
| CUDA | 12.8 |

### Software

| Component | Version |
|-----------|---------|
| Docker | 27.5.1 |
| Docker Compose | v2.38.2 |
| NVIDIA Container Toolkit | 1.17.8 |
| Tailscale | 1.92.1 |
| Python | 3.12.3 |
| TensorRT-LLM | 1.0.0rc2 |

### LLM Server

```bash
docker run -d --name qwq_llm --ipc=host --shm-size=2g \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --gpus=all -p 8001:8001 \
  -v $HOME/models:/models \
  -v $HOME/Aruism-AI-Local/docker/engine:/engines \
  nvcr.io/nvidia/tensorrt-llm/release:1.0.0rc2 \
  trtllm-serve serve /models/qwq/engines/qwq32b_tp2_long32k_existing \
    --tokenizer /engines/qwen/QwQ-32B-AWQ \
    --max_batch_size 16 \
    --max_num_tokens 32768 \
    --host 0.0.0.0 \
    --port 8001 \
    --tp_size 2
```

Configuration:
```python
HOST = "http://100.107.6.119:8001/v1"
MODEL = "qwq32b_tp2_long32k_existing"
```

---

## 10. Parameters

### Core Configuration (config.py)

| Parameter | Value | Description |
|-----------|-------|-------------|
| VERSION | 5.3.5 | Engine version |
| COMPETE_TH | 0.15 | Competing hypothesis threshold |
| VOL_LOW_TH | 0.3 | Low volatility threshold |
| VOL_HIGH_TH | 0.6 | High volatility threshold |
| UNKNOWN_MARGIN_TH | 0.20 | Margin for abstain decision |
| UNKNOWN_ENTROPY_TH | 0.90 | Entropy for abstain decision |

### Dynamics

| Parameter | Value | Description |
|-----------|-------|-------------|
| α | 0.7 | Linkage weight frequency coefficient |
| τ | 86400 | Linkage weight decay constant (seconds) |
| γ | 0.1 | Observation injection rate |
| ε_0 | 0.01 | Initial state base value |
| δ | 0.005 | Initial state hierarchy bonus |
| λ_sym | 1.0 | Symmetry constraint weight |
| λ_link | 1.0 | Linkage constraint weight |

---

## 11. Code Skeleton (Key Classes)

### config.py

```python
VERSION: str
COMPETE_TH: float
ROUTE_A_MIN_SCORE: float
VOL_LOW_TH: float
VOL_HIGH_TH: float
SYNAPSE_FILE: str
GLOSSARY_FILE: str
QUEUE_FILE_PATH: str
```

### hypothesis.py

```python
class HypothesisResult:
    score: float
    reason: str  # mandatory
    volatility: float
    signals: Dict

class EvaluationReport:
    winner: None  # always null
    competing_routes: List[str]
    global_volatility: float

def evaluate_all_hypotheses(...) -> EvaluationReport: ...
def compute_global_volatility(...) -> float: ...
def determine_status(volatility: float) -> str: ...
```

### aggregate_state.py

```python
class AggregateStateManager:
    def compute_aggregate_key(token_norm, pos, route_set) -> str: ...
    def should_process(aggregate_key) -> bool: ...
    def upsert_observation(aggregate_key, ...) -> None: ...
    def mark_finalized(aggregate_key, reason) -> None: ...
```

### online.py (v5.3.5)

```python
class SearchProvider:
    def search(query: str, max_results: int) -> List[Dict]: ...

class MultiSourceProvider(SearchProvider):
    providers = [
        FreeDictionaryAPI(),
        WikipediaAPI(),
        DatamuseAPI(),
        UrbanDictionaryAPI(),
        DuckDuckGoAPI(),
    ]
    def search(query: str, max_results: int) -> List[Dict]: ...
```

### esde_sensor.py

```python
class ESDESensor:
    OP_NOT = "¬"
    OP_CONN = "×"
    OP_JUXT = "⊕"
    
    def analyze(text: str) -> Dict: ...
    def _build_formula(text, concept) -> Dict: ...
    def _resolve_formula(formula) -> str: ...
```

---

## 12. Reproduction Commands

```bash
# 1. Generate queue data
python esde-engine-v532.py

# 2. Process queue (Phase 7B+)
python resolve_unknown_queue_7bplus_v534_final.py --limit 50

# 3. Check output
cat ./data/unknown_queue_7bplus.jsonl | tail

# 4. Run 7C audit
python resolve_unknown_queue_7bplus_v534_final.py --mode 7c

# 5. Run 7C' audit
python resolve_unknown_queue_7bplus_v534_final.py --mode 7cprime
```

---

## 13. Acceptance Criteria

- Running 7B+ twice without new queue input must produce **0 processed** (State idempotency)
- When queue has 3 identical records, aggregation must output **1 aggregate with count=3**
- Candidate/Defer/Quarantine thresholds must strictly match `config.py`

---

## 14. Anti-Patterns (DO NOT)

- **DO NOT** introduce `web.run` or external browsing inside the runtime engine
- **DO NOT** "fix" ambiguity by choosing the most likely meaning (preserve volatility)
- **DO NOT** add new heuristics without corresponding audit signals
- **DO NOT** add new modules/files unless explicitly instructed
- **DO NOT** hardcode thresholds/paths outside `config.py`

---

## 15. Current Status & Next Steps

### 15.1 Completed Phases

| Phase | Status | Output |
|-------|--------|--------|
| 7A | ✅ Complete | unknown_queue.jsonl |
| 7B | ✅ Complete | Aggregation logic |
| 7B+ | ✅ Complete | MultiSourceProvider (v5.3.5, 100% success) |
| 7C | ✅ Complete | Structural audit |
| 7C' | ✅ Complete | LLM semantic audit |
| 7D | ✅ Complete | Meta-auditor, rule calibration |
| **8** | **✅ Implemented** | **Sensor V2 (Synapse Integration)** |

### 15.2 Sensor V2 Implementation (Phase 8)

**File:** `esde_sensor_v2.py`

**Key Features:**
- Primary: Synapse vector lookup (raw_score from generate_synapses_v2_1.py)
- Fallback: Legacy trigger matching (Hybrid mode)
- ALLOWED_POS includes 's' (Satellite Adjective)
- Deterministic output (sorted by score DESC, concept_id ASC)
- Full audit trail (evidence, config_snapshot, determinism_hash)

**Config Requirements (add to config.py):**
```python
# Phase 8: Sensor V2
SENSOR_TOP_K = 5
SENSOR_MAX_SYNSETS_PER_TOKEN = 3
STRICT_SYNAPSE_ONLY = False
SENSOR_ALLOWED_POS = {'n', 'v', 'a', 'r', 's'}

# CRITICAL: Update existing ALLOWED_POS
ALLOWED_POS = {'n', 'v', 'a', 'r', 's'}  # Added 's'
```

**GPT Audit Compliance:**
- ✅ Config values injected explicitly
- ✅ ALLOWED_POS includes 's'
- ✅ determinism_hash includes config_snapshot
- ✅ Fallback to legacy triggers (Hybrid mode)

### 15.3 Modular Architecture (GPT Recommended)

Sensor V2 has been refactored into modular components for maintainability and testability.

**Directory Structure:**
```
esde/
├── esde_sensor_v2_modular.py     # Facade (thin orchestration)
└── sensor/
    ├── __init__.py               # Package exports
    ├── loader_synapse.py         # SynapseLoader
    ├── extract_synset.py         # SynsetExtractor  
    ├── rank_candidates.py        # CandidateRanker
    ├── legacy_trigger.py         # LegacyTriggerMatcher (v1 fallback)
    ├── audit_trace.py            # AuditTracer (counters/hash/evidence)
    ├── molecule_validator.py     # Phase 8-2 Validator
    └── molecule_generator.py     # Phase 8-2 Generator
```

**Module Responsibilities:**

| Module | Class | Responsibility |
|--------|-------|----------------|
| loader_synapse.py | SynapseLoader | JSON load, singleton, file hash |
| extract_synset.py | SynsetExtractor | WordNet synset extraction |
| rank_candidates.py | CandidateRanker | Score aggregation, deterministic sort |
| legacy_trigger.py | LegacyTriggerMatcher | v1 trigger fallback |
| audit_trace.py | AuditTracer | Counters, hash, evidence formatting |

### 15.4 Phase 8-2: Molecule Generation & Validation

**Spec v8.2.1** (GPT Audit Passed)

#### MoleculeValidator

Validates generated molecules for integrity.

| Check | Description | GPT Audit |
|-------|-------------|-----------|
| Atom Integrity | 2-tier: Sensor candidates + Glossary subset | ✅ v8.2.1 |
| Operator Valid | v0.3 operators (×, ▷, →, ⊕, ¬, etc.) | ✅ |
| Syntax Check | Bracket matching | ✅ |
| Coordinate Valid | axis/level exist in Glossary | ✅ |
| Evidence Linkage | span range valid + text_ref == text[span] | ✅ v8.2.1 |
| Coverage Policy | High confidence + null coords = warning | ✅ |

**Key Methods:**
```python
validator = MoleculeValidator(
    glossary=glossary,
    sensor_candidates=["EMO.love", "ACT.give"],
    allow_glossary_atoms=True  # v8.2.1: Allow Glossary subset atoms
)
result = validator.validate(molecule, original_text)
# result.valid, result.errors, result.warnings
```

#### MoleculeGenerator

LLM-based semantic molecule generation.

**Design Principles:**
- **Never Guess**: axis/level = null if uncertain
- **No New Atoms**: Only use atoms from candidates
- **Glossary Subset**: Only pass relevant definitions to LLM
- **Retry Policy**: Max 2 retries, then Abstain

**Prompting Policy:**
```
1. ONLY use atoms from the provided candidate list
2. If uncertain about axis/level, set them to null
3. text_ref must be EXACT substring from original text
4. span must be exact character positions [start, end)
```

**Data Schema (ActiveAtom):**
```json
{
  "active_atoms": [
    {
      "id": "aa_1",
      "atom": "EMO.love",
      "coordinates": {
        "axis": "interconnection",
        "level": "resonant",
        "confidence": 0.95
      },
      "text_ref": "deeply in love",
      "span": [10, 24]
    }
  ],
  "formula": "aa_1 ▷ aa_2"
}
```

### 15.5 Test Results

**Sensor V2 (Modular):**
```
[Input] I love you
  Engine: v2_synapse
  Candidates: 1 (EMO.love via love.n.01)
  synsets_checked=3, with_edges=3 ✅

[Input] apprenticed to a master
  Engine: v2_synapse
  Candidates: 1 (ABS.bound via apprenticed.s.01) ← GPT Audit Key Test
  synsets_checked=5, with_edges=1 ✅

[Input] I cannot forgive you
  Engine: v2_synapse+v1_fallback
  Candidates: 0 (forgive.v not in synapses)
  synsets_checked=2, with_edges=0 ✅ Expected
```

**MoleculeValidator:**
```
Valid: True
Errors: []
Coordinate completeness: 1.0 ✅
```

**MoleculeGenerator (Mock):**
```
Success: True
Abstained: False
axis: null, level: null (Never Guess) ✅
validator_status: pass ✅
```

### 15.6 Phase 8-3: Live LLM Integration

**Implementation:** `sensor/molecule_generator_live.py`

#### 15.6.1 Spec v8.3 Guardrails

| Guardrail | Implementation | Status |
|-----------|----------------|--------|
| Strict Output Contract | "Return ONLY JSON" in system prompt | ✅ |
| Zero Chatter | QwQ `<think>` tag removal | ✅ |
| Fail-Closed Parsing | No fuzzy logic, markdown removal only | ✅ |
| System-Calculated Span | SpanCalculator (token proximity) | ✅ |
| Coordinate Coercion | CoordinateCoercer with logging | ✅ |
| Empty Check | Skip LLM if no candidates | ✅ |

#### 15.6.2 Live Test Results (QwQ-32B)

```
=== I love you ===
Success: True
Molecule: EMO.love@interconnection:catalytic
Formula: aa_1
Span: [2, 6] ✅

=== The law requires obedience ===
Success: True
Molecule: EMO.respect@value_generation:ethical
Formula: aa_1
Span: [17, 26] ✅

=== I cannot forgive you ===
Candidates: 0
LLM Called: False ✅ (Empty Check working)
```

#### 15.6.3 GPT Audit 4-Case Tests

| Test | Description | Result |
|------|-------------|--------|
| A | Same text_ref multiple occurrences | ✅ Token proximity |
| B | text_ref spelling variation | ✅ span=null + warning |
| C | Coordinate mismatch (Glossary外) | ✅ Coercion logged |
| D | JSON pollution (`<think>`, markdown) | ✅ Parsed correctly |

### 15.7 Phase 8-4: Semantic Stability & Drift Audit

**Implementation:** `esde_stability_audit.py`

#### 15.7.1 Audit Scope

| Item | In Scope | Out of Scope |
|------|----------|--------------|
| Stability verification | ✅ | Ledger implementation |
| Drift measurement | ✅ | Operator expansion |
| Pollution blocking | ✅ | Glossary update |

#### 15.7.2 Test Corpus

| Category | Count | Purpose |
|----------|-------|---------|
| human_emotion | 20 | Emotion word stability |
| human_logic | 20 | Logic structure reproduction |
| ai_text | 20 | AI-generated text immunity |
| noise | 20 | Hallucination test |
| edge_cases | 20 | Boundary value test |

#### 15.7.3 Audit Results (3500 runs)

**Mode A (temperature=0):**

| Category | Success Rate | Drift | Judgment |
|----------|--------------|-------|----------|
| edge_cases | 95% | 15.8% | ⚠️ |
| human_emotion | 72% | 5.0% | ✅ |
| ai_text | 75% | 11.7% | ⚠️ |
| human_logic | 70% | 10.7% | ⚠️ |
| noise | 15% | 0% | ✅ |

**Mode B (temperature=0.1):**

| Category | Success Rate | Drift | Judgment |
|----------|--------------|-------|----------|
| edge_cases | 95% | 17.4% | ⚠️ |
| human_emotion | 90% | 8.4% | ✅ |
| ai_text | 75% | 10.3% | ⚠️ |
| human_logic | 70% | 20.9% | ⚠️ |
| noise | 14% | 1.2% | ✅ |

**Immunity Metrics:**

| Metric | Count | Rate | Judgment |
|--------|-------|------|----------|
| Validator Blocks | 8 | 0.23% | ✅ Very Low |
| Coordinate Coercions | 5 | 0.14% | ✅ Very Low |
| Pollution Blocked | True | - | ✅ |

#### 15.7.4 Mode A Quick Test (Drift切り分け)

```
Temperature: 0.0
Samples: 10 items × 10 runs = 100 runs

Results:
  Drift-A (Atom): 0.0000 ✅ Perfect
  Drift-B (Coord): 0.0000 ✅ Perfect
  Drift-C (Formula): 0.0000 ✅ Perfect
  
Conclusion: temp=0 achieves deterministic output at Atom/Coord level.
Residual drift in full audit is Formula expression variation only.
```

#### 15.7.5 FormulaValidator Fix

**Issue:** `¬¬aa_1` (double negation) was blocked as unknown operator.

**Root Cause:** `extract_operators()` treated `¬¬` as single token.

**Fix:** Character-by-character parsing for consecutive operators.

```python
# Before: ['¬¬'] → Unknown operator error
# After:  ['¬', '¬'] → Valid (two negations)
```

### 15.8 Next Steps

| Priority | Task | Status |
|----------|------|--------|
| 1 | ~~Sensor V2 implementation~~ | ✅ Complete |
| 2 | ~~Modular refactoring~~ | ✅ Complete |
| 3 | ~~Phase 8-2 Validator/Generator~~ | ✅ Complete |
| 4 | ~~Phase 8-3 Live LLM Integration~~ | ✅ Complete |
| 5 | ~~Phase 8-4 Stability Audit~~ | ✅ **PASS** |
| 6 | Phase 8-5 (Semantic Ledger / Operators) | **Next** |

### 15.9 Development Workflow

```
Gemini:  Design proposal (What to do)
   ↓
GPT:     Audit (Is it valid?)
   ↓
Claude:  Implementation (How to build)
   ↓
GPT:     Deliverable audit (Did we build it right?)
   ↓
All:     Phase 8-5 Scope Decision  ← Current
```

---

## 16. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.2.1 | 2024-12 | Core Specification established |
| 5.1.0 | 2024-12 | Glossary pipeline, synapse structure |
| 5.3.2 | 2025-01 | Phase 7A-7B implementation |
| 5.3.4 | 2025-01 | SearXNG integration, 7B+ pipeline |
| 5.3.5 | 2026-01-11 | MultiSourceProvider, 100% success rate |
| 5.3.5-P8 | 2026-01-12 | Phase 8: Sensor V2 + Modular Architecture |
| 5.3.5-P8.2 | 2026-01-12 | Phase 8-2: Molecule Generator/Validator |
| **5.3.5-P8.3** | **2026-01-12** | **Phase 8-3: Live LLM Integration (QwQ-32B)** |
| **5.3.5-P8.4** | **2026-01-13** | **Phase 8-4: Stability Audit PASS** |

### v5.3.5-P8 Changelog (Phase 8)

1. **Sensor-Synapse Integration**
   - Sensor V2: Synapse vector lookup as primary method
   - Fallback: Legacy trigger matching (Hybrid mode)
   - ALLOWED_POS includes 's' (Satellite Adjective)

2. **GPT Audit Compliance**
   - Full determinism_hash (64 hex)
   - Fallback counters for debugging
   - Top evidence per candidate

3. **Modular Architecture** (GPT Recommended)
   - Facade: esde_sensor_v2_modular.py
   - Components: sensor/ package (8 modules)

### v5.3.5-P8.2 Changelog (Phase 8-2)

1. **MoleculeValidator**
   - Atom Integrity: 2-tier (Sensor + Glossary subset)
   - Coordinate Valid: axis/level existence check
   - Evidence Linkage: span exact match (v8.2.1)

2. **MoleculeGenerator**
   - Never Guess: null coordinates when uncertain
   - No New Atoms: only from candidates
   - Retry Policy: max 2, then Abstain

3. **Test Results**
   - Sensor V2: All tests passed
   - Validator: coordinate_completeness=1.0
   - Generator (Mock): abstained=False, pass

### v5.3.5-P8.3 Changelog (Phase 8-3)

1. **Live LLM Integration**
   - MoleculeGeneratorLive with QwQ-32B
   - QwQ `<think>` tag removal
   - max_tokens: 16000 (for long reasoning)

2. **GPT Audit Guardrails (v8.3)**
   - Strict Output Contract (Zero Chatter)
   - Fail-Closed Parsing
   - System-Calculated Span (token proximity)
   - Coordinate Coercion with logging

3. **New Components**
   - SpanCalculator: text_ref → span
   - CoordinateCoercer: invalid → null + log
   - FormulaValidator: consecutive operators fix (¬¬)

4. **Test Results**
   - Live Test: 3/3 PASS
   - GPT Audit 4-Case: 4/4 PASS

### v5.3.5-P8.4 Changelog (Phase 8-4)

1. **Semantic Stability Audit**
   - 3500 runs (Mode A: 500, Mode B: 3000)
   - 5 categories × 20 sentences = 100 corpus
   - Parallel execution (8 workers)

2. **Drift Analysis (A/B/C)**
   - Drift-A (Atom): 0% at temp=0 ✅
   - Drift-B (Coordinate): 0% at temp=0 ✅
   - Drift-C (Formula): ~5.6% (expression variation)

3. **Immunity Metrics**
   - Validator Blocks: 8 (0.23%)
   - Coercions: 5 (0.14%)
   - Pollution Blocked: True

4. **Audit Judgment**
   - **Conditional PASS**
   - System does not break
   - System does not pollute
   - System has courage to abstain (Noise: 85% empty)

---

## 17. References

- ESDE Core Specification v0.2.1
- ESDE v3.3: Ternary Emergence and Dual Symmetry
- ESDE v3.3.1: Emergence Directionality
- Semantic Language Integrated v1.1
- ESDE Operator Spec v0.3
- Aruism Philosophy

---

*Document generated: 2026-01-13*  
*Engine Version: 5.3.5-P8.4*  
*Framework: Existence Symmetry Dynamic Equilibrium*  
*Philosophy: Aruism*
