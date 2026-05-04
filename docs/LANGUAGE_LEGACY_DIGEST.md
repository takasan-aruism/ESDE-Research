# ESDE Language Legacy Digest (融合準備資料)

*作成*: 2026-05-05、Claude (相談役、Taka 監修待ち)
*目的*: `Research/language/` (= ESDE 原型・言語系) の凍結時点 (2026-03) の状態を、
将来 Claude が `developmental/v10x` (= 現役、ESDE Genesis 系) との **融合検討時** に
即把握できるよう整理する。

---

## 0. 一文サマリ

`language/` は **ESDE の原点であり、326 Atoms × 48 スロット意味座標系を中心に
言語層を構築した系**。2026-02 に Lexicon v2 A1 観測 99.7% 完了直後の 2026-03 で
凍結し、開発主軸は `developmental/v10x` (Genesis 系: 物理→cid→α/β の階層動学)
に移行した。**Atom 概念と Synapse 接地は Developmental 認知層の意味化に転用候補。**

---

## 1. ESDE の 2 系統と現在位置

```
ESDE 開発の歴史
  │
  ├── 言語系 (Research/language/)         ← 原点、2026-03 凍結
  │     - 326 Atoms × 48 スロット
  │     - Synapse (WordNet ↔ Atom 橋)
  │     - Lexicon v2 A1 観測 (LLM 駆動)
  │     - Phase 7-10 多層観測
  │     - 「テキストの意味構造を多角的に観測」
  │
  └── Genesis 系 (Research/genesis/, developmental/v10x/)   ← 現役
        - 物理層 (engine.state, theta/S/R)
        - cid (5-node 認知主体)
        - α (cid 観察軸) / β (会計単位)  ← v10.5 で完成
        - Salience / Leakage 機構
        - 「物理から認知が emergent する動学を再現」
```

両者は **問題意識の方向が逆**:
- 言語系: テキスト → 意味座標へ **下降**
- Genesis 系: 物理 → 認知へ **上昇**

→ **Atom 概念は両者の中間言語になりうる**。これが Taka 構想中の融合点。

---

## 2. 凍結時点の状態 (2026-03)

### 2.1 哲学的基盤 (不変)

- **Aruism (アリズム)**: 「ある」は、ある (Aru wa, Aru)
- **存在の対称性**: 全概念は対を持つ (好↔嫌、生↔死)。**163 対称ペア**
- **記述せよ、しかし決定するな** (Describe, but do not decide)
- **十分な説明**: 完璧でなく、役に立つ程度の意味地図

### 2.2 Foundation Layer (確定)

| 要素 | 内容 | 数 |
|---|---|---|
| **Atoms** | 24 カテゴリ × 8〜46 atom = **326 atom** (+ `_summary` の 327 file) | 326 |
| **対称ペア** | atom 同士の意味対 | 163 |
| **軸** | temporal / scale / epistemological / ontological / interconnection / resonance / symmetry / lawfulness / experience / value_generation | **10 軸** |
| **スロット** | 各軸が 3〜7 レベル | 計 **48 スロット** |
| **共鳴度モデル** | 旧バイナリ → **連続値 0-10** (2026-02-15 Taka 承認) | — |

カテゴリ内訳 (`atoms/a1_batch/` から):
```
ABS 8, ACT 28, BEI 8, BOD 8, CHG 7, COG 13, COM 12, ECO 12,
ELM 12, EMO 30, EXS 11, FND 25, LOG 4, MAT 6, NAT 4, PER 20,
PRP 46, REL 4, SOC 22, SPC 6, STA 11, TIM 7, VAL 10, WLD 12
```

### 2.3 Synapse (WordNet ↔ Atom 接地辞書)

- Base: `language/synapse/esde_synapses_v3.json` (= v3.0 想定)
- Overlay patches (`language/synapse/patches/`):
  - v3.1 (+5.8pt 動詞接地)
  - v3.2 (+2.0pt)
  - v3.3 / v3.3_hotfix
  - v3.4 (capital fix)
  - **v3.5 (2026-03-04、最新、missing-sense patch)**
- 動詞接地率: ~63% → 63%+α (パッチ累積)

### 2.4 Lexicon v2 A1 観測

- **325 / 326 atom 完了** (FND_spaceless のみ未完)
- 観測者: QwQ-32B (LLM)、各語に 48 スロット連続値 (0-10)
- 出力: `language/lexicon/data/mapper_output/*_a1.jsonl` (325 file)
- 構造: `{word, pos, atom, raw_scores (48), normalized_scores, entropy_norm, focus_rate, status, top5, evidence}`
- 品質: nz_mean 13.6 / OK 率 97.3% (score inflation 修正済)
- Constitution v1.0 確定 (17 proposals: 3 merge / 1 subsume / 6 couple / 7 monitor)

### 2.5 Phase 実装状況

| Phase | 名称 | 状態 (凍結時) | コード |
|---|---|---|---|
| 7 | Unknown Resolution | 7B+ / 7C / 7C' / 7D 全実装済 | `data/unknown_queue_*.jsonl` あり |
| 8 | Introspective Engine (強い意味) | V2.0.0 modular facade 稼働 | `language/sensor/` |
| 8 (Projection) | WSD 改善実験 | 2026-03-21、**B/C/BC は base 未満**で失敗 | `language/projection/` |
| Obs C | Relation Pipeline (SVO 抽出) | v0.2.0 (grounding 55%) | `language/relations/` |
| 9 | Weak Axis Statistics | Overview 上は **完了**、language/ 内に **コード見当たらず** ← 要確認 | 不明 |
| 10 | Cell Architecture | **設計のみ** (v2.3、2026-02-08)、実装未着手 | `docs/.../esde_cell_architecture.md` |

### 2.6 Substrate Layer 0

- 観測の生記録 (意味的判断なし、append-only)
- ContextRecord (context_id, traces) を蓄積
- Phase 9 統計の入力源
- `language/sensor/audit_trace.py` 等

### 2.7 Harvester / Content Gateway

- 外部データ取得 (Wikipedia 等)
- `language/harveste/`
- キャッシュ済 artifacts: city (5 都市) + military (~10 人物) + lit / phil / sci / tech

---

## 3. ファイル所在マップ (再起動時の起点)

```
Research/language/
├── atoms/
│   ├── a1_batch/         326 atom × lexicon entry JSON (Core/Deviation)
│   └── esde_dictionary.json  Atom 定義の master
├── lexicon/
│   ├── mapper_a1.py      A1 観測 (LLM 駆動、QwQ-32B)
│   ├── auditor_a1.py     構造監査 C1-C5 + Re-observe
│   ├── batch_report.py   品質メトリクス集計
│   ├── wn_*.py           WordNet 語彙供給 (auto_seed → batch_expand
│   │                       → lexicon_entry → core_stats → proposal_gen)
│   ├── synapse_v4_*.py   Synapse v4 比較・タスク
│   └── data/
│       ├── lexicon_entries/  326 atom × Core/Deviation JSON
│       ├── mapper_output/    325 atom × A1 観測 jsonl ← **本番出力**
│       ├── definitions/      atom 定義
│       └── expanded/         WordNet 展開中間データ
├── synapse/
│   ├── store.py          SynapseStore (Base + Overlay 統合)
│   ├── schema.py         SynapsePatchEntry / RewritePack 等
│   ├── proposer.py       SynapseEdgeProposer (4-Pack Rewrite)
│   ├── cli.py            propose-synapse / evaluate-synapse-patch
│   ├── diagnostic.py
│   ├── esde_synapses_v3.json   Base
│   └── patches/synapse_v3.{1,2,3,3_hotfix,4,5}.json
├── sensor/               Phase 8 V2 (Atom → Molecule)
├── relations/            Observation C (SVO Relation Pipeline)
├── projection/           Phase 8 Projection Operator 実験 (失敗)
├── harveste/             外部データ取得
├── data/
│   ├── audit_runs/       Phase 8 / 8.5 integration report
│   ├── audit_*7c*.jsonl  Phase 7C / 7C' / 7D 監査
│   ├── unknown_queue_*.jsonl  Phase 7 Unknown Queue
│   ├── artifacts/        Harvester キャッシュ
│   └── 保管/             archive (旧 versions、参考のみ)
├── tests/                test_mapper_a1 / test_projection / test_qwen3
├── cache/                embedding cache (MiniLM)
└── esde/projection.py    4 operator 実装 (base/B/C/BC)

Research/docs/ESDE language/  ← 文書群 (mtime 2026-03-21、内容は各 doc の date 参照)
├── ESDE_Overview.md          ★ 最初に読むべき
├── ESDE_Detailed_Design.md   v5.4.8-MIG.2 (2026-01-25)
├── ESDE_Technical_Specification.md  100KB、最大詳細
├── ESDE_Module_Reference.md  v5.7.0 (2026-02-11)
├── ESDE_Module_Reference_Lexicon_v2.md
├── ESDE_Glossary.md          v5.7.0、用語辞典 40KB
├── esde_cell_architecture.md  v2.3 (2026-02-08)、Phase 10 設計
├── ESDE_Essence_v02.md
├── COMMAND_REFERENCE_v2.md
├── DESIGN_NOTE_Resonance_Scoring.md
├── ESDE_Briefing_Synapse_Expansion_via_Phase7.md
├── ESDE_Vision_LLM_Symmetric_Integration.md
├── Project_Lexicon_Unified_Implementation_Spec.md
├── README.md                 Phase 8 Projection Operator 実験 (2026-03-03)
└── 旧/                        さらに古い PDF 等、原則無視可
```

---

## 4. 凍結時の未解決問題・落とし穴

### 4.1 不整合 / 不明点

- **Phase 9 (Weak Axis Statistics) のコード所在不明**
  - Overview / Detailed Design では「**完了**」記載
  - `language/` 内に該当ディレクトリ見当たらず (`statistics/pipeline/` 等)
  - 別 repo / archive / 別ブランチの可能性
  - **再起動時は最初に Phase 9 コードを発見・確認すべき**

- **Phase 10 (Cell) は設計のみ、実装未着手**
  - `esde_cell_architecture.md` v2.3 で詳細設計済
  - これが「強い意味 (Phase 8) + 弱い意味 (Phase 9)」を結合する野心的な統合層
  - **Developmental 融合の目線では Cell の構想こそ最も価値が高い**

### 4.2 失敗・限界

- **Projection Operator B/C/BC が base に劣る** (2026-03-21 実験):
  | Mode | R@1 | R@3 |
  |---|---:|---:|
  | base | 0.329 | 0.329 |
  | B/C/BC | 0.266 | 0.329 |
  - sentence-context embedding を Synapse atom 重み付けに使う試みが効かず
  - WSD (capital → SOC.official が SOC.city より優先) の根本解決には至らず
  - 別アプローチ (context window 拡大 / fine-tune / Atom 連続値プロファイル直接利用) が要検討

- **動詞接地率の限界**: v3.5 までの overlay patch で +α、しかし
  - 高頻度かつ embedding 親和性高い動詞は解消、残余は score < 0.55 で自動提案困難 (逓減パターン)

- **Lexicon v2 A1 残 1 atom**: FND_spaceless のみ未完。完了で 326/326 達成

### 4.3 開発の文脈

- mtime 一律 2026-03-21 (= git checkout 時刻と推定)
- 凍結直前の進捗:
  - 2026-02-08: Cell Architecture v2.3 + Synapse Expansion v3.2 完走
  - 2026-02-11: Lexicon v2 Constitution v1.0 確定
  - 2026-02-15: 連続値共鳴度モデル正式承認
  - 2026-03-04: Synapse v3.5 patch
  - 2026-03-21: Projection Operator 実験 (失敗)
- → 多層観測の機能拡張が頭打ちになり、より基底の Genesis 系開発へ重心移動

---

## 5. Developmental v10.x との融合候補 (Taka 構想の言語化、推測含む)

### 5.1 構造的対応の仮説

| 言語系 (language/) | Genesis 系 (developmental/v10x/) | 対応の可能性 |
|---|---|---|
| Atom (326 個、意味の周期表) | β (会計単位) のラベル | **β に Atom 共鳴度プロファイルを付与** |
| 48 スロット連続値 (~mass) | β.Q_inherited / C_inherited | スロット値で β の質的内容を記述 |
| Synapse (synset → atom 接地) | cid (5-node) → atom 接地 | cid の意味的アンカリング |
| 対称ペア 163 組 | β-merge の対 (同型/対立) | β 融合動学に対称性原理導入 |
| Phase 8 強い意味 (atomic anchor) | β (会計単位、原子核) | 直接の同型 |
| Phase 9 弱い意味 (統計パターン) | Salience (mass-weighted 観察) | 直接の同型 |
| **Phase 10 Cell (強+弱 統合)** | **β + Salience 統合** | **v10.5 が既に部分実現** |
| Substrate Layer 0 (記述のみ) | engine.state (frozen 物理層) | 同じ「記述のみ」哲学 |

### 5.2 最有望の融合アイデア

1. **β に Atom プロファイルを付与する**
   - 各 cid の member_nodes ↔ 単語 (synset) ↔ atom の経路を作る
   - β = 構成 cid の atom プロファイル平均/和
   - hub β (例 seed22 β0、691 α 統合) が Atom 空間でどんなプロファイルを持つか観測

2. **Cell Architecture を v10.5 で実装**
   - Phase 10 設計書 (esde_cell_architecture.md v2.3) は強+弱の統合を提案
   - v10.5 の β + Salience は既にこの構造に対応している
   - Atom 軸を加えれば「Cell = β + Salience + Atom anchoring」として実現可能

3. **Synapse v3.5 を v10.x の意味接地に流用**
   - cid を「semantic role を持つ主体」として記述
   - Observation C の SVO 抽出を v10.x の cid 間相互作用に転用

4. **対称ペア原理を β-merge に導入**
   - 現状の β-merge は `min ID` 規則。Atom 対称ペア (好↔嫌) を導入すれば、
     対立 β の融合 vs 同型 β の融合を区別できる

### 5.3 融合時の注意点

- **物理層 frozen 規律は v10.x で必須**: language 系は LLM 駆動で観測が動的だが、
  v10.x は engine.rng を一切 touch しない。Atom 観測 (LLM 経由) を入れる場合は
  認知層への副作用に留め、物理層に逆流させない設計が必要
- **連続値共鳴度のスケール**: Atom 0-10 と β.C_inherited (例 0-32) は数値レンジが
  異なる。正規化方針を Cell 統合時に決定
- **Phase 9 のコード**を発見しないと Cell 統合は不完全

---

## 6. 再起動時 Checklist (Future Claude 向け)

`language/` 関連の作業を再開する時、以下の順で確認:

1. **本 digest を読む** (= この文書)
2. `docs/ESDE language/ESDE_Overview.md` を読む (高レベル設計、最新 2026-02-11 内容)
3. `docs/ESDE language/esde_cell_architecture.md` v2.3 を読む (Phase 10 設計、融合の中核)
4. **Phase 9 コードの所在を Taka に確認** (本 digest §4.1 参照)
5. `language/lexicon/data/mapper_output/` で A1 観測の実例を確認
6. `language/atoms/a1_batch/_summary.json` で atom 統計確認
7. Synapse 最新 patch (v3.5) を `language/synapse/patches/` で確認
8. 融合検討なら `developmental/v105/v105_main_v2_run_report.md` も参照

---

## 7. 永続的な疑問 (将来検討材料)

- Atom 326 個は「人間言語」由来、Genesis 系の cid は「物理から emergent」。
  両者の対応は本当に可能か? (Aruism 的には「ある」→「言語化される」の連続性
  あり、しかし数理的には gap)
- 連続値 0-10 の共鳴度を、cid の theta / S / R 軸とどう接合するか?
- Phase 10 Cell の「条件因子で結合する」原則は、v10.5 の β-cohort edges と同じ?
- 凍結期間中 (2026-03 → 現在 2026-05) に v10.x で得られた知見 (β-merge 二極化、
  Leakage 機構など) は、language 系を再起動する際にどう反映できるか?

---

## 8. メタ情報

- 本 digest はTaka 監修待ちの **第一稿**
- Taka が「ここは違う / ここを足してほしい」を指摘 → 私が修正
- 修正後 commit → auto-memory にこの digest への pointer を保存
- 将来 Claude (新会話) は memory から本 digest を発見し、必要時に読み込む

---

*以上、`Research/language/` 凍結時点状態の整理。融合検討の起点として供す。*
