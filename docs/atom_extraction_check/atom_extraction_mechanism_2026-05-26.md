# ESDE Atom 抽出仕組み 記録文書

*作成*: 2026-05-26、Code A (実環境照合)
*親*: Web Claude 確認依頼「ESDE Atom 抽出仕組みの確認依頼 + 仕組み記録文書」(2026-05-25) + Taka 質問 (2026-05-25 原文「現在どんな仕組みで ESDE 内で Atom が抽出されるようになってるの? この抽出は Atom a = Atom a なのか、Atom a = Atom a x y (100% 一致はない。揺れている状態) ということなのか。Atom は表記上 Atom.xxx (軸) みたいな記述方法になると思ったけどその辺含めてどうなってんのかな、と。」)
*位置づけ*: 将来の Claude / Taka が読み返せる仕組み記録文書。v1106a 主題外の独立記録、データ取り違え防止規律 (v1106 §22.5) の **Atom 抽出ロジック版**。

---

## 1. Atom 抽出の全体像 (わかりやすい説明、初見の Claude / Taka 向け)

ESDE で「Atom」と呼ばれるものは **2 種類** 存在し、両者の関係を理解することが本文書の主目的:

### 1.1 2 種類の「Atom」

| 種類 | 何か | 出処 | 件数 | 例 |
|---|---|---|---|---|
| **A: Atom 概念 (固定)** | Language 側で事前定義された語彙的構造単位 | `language/atoms/esde_dictionary.json` (326 atom 固定定義) | **326 (固定)** | `ACT.build`, `FND.ahistorical`, `SOC.official` 等 |
| **B: cid (Cognitive ID、揺れる)** | ESDE 内部で実行時に動的生成される認知的単位 | Genesis main run (v10.5/6/7 等) で seed × cid_id の integer index として生成 | seed ごとに変動 (~13-19 cid/seed、24 seeds 合計 316) | seed=0, cid_id=0 等 (integer) |

**両者の関係**:
- cid (B、動的) は atom (A、固定) との **類似度** を持つ
- v106/cid_atom_sim_matrix_seed{N}.parquet で `cid × atom の 0-1 連続 sim 値` として記録
- つまり「cid は atom 326 個に対して揺れる関係を持つ存在」

### 1.2 Taka 質問への構造的回答

> Atom a = Atom a なのか、Atom a = Atom a x y (100% 一致はない、揺れている) なのか

**回答**: **両方の側面がある (ハイブリッド構造)**

- **atom (Language 側固定定義) は Atom a = Atom a** (326 個の固定リスト、esde_dictionary.json で永続的に定義)
- **cid (ESDE 内部動的生成) は cid = cid × atom_1 × atom_2 × ... × atom_326 の揺れる関係** (cid_atom_sim_matrix の各行 = その cid から 326 atoms 各々への sim 値の分布)

つまり:
- 「atom 自体は固定された 326 個」
- 「ESDE 内部で生成される cid が、それら 326 atom に対してどう揺れるか」が ESDE Atom 抽出の動的部分

### 1.3 表記 `XXX.yyy` の意味

> Atom は表記上 Atom.xxx (軸) みたいな記述方法

**回答**: **Atom 表記 `XXX.yyy` は「軸」ではない、`category.atom_name`**

| 部分 | 何 | 種類数 | 例 |
|---|---|---|---|
| **XXX (prefix)** | **category (大分類)** | 24 種類 (PRP/EMO/ACT/FND/SOC/PER/COG/COM/ECO/ELM/WLD/EXS/STA/VAL/BOD/BEI/ABS/TIM/CHG/SPC/MAT/NAT/REL/LOG) | `ACT`, `FND`, `SOC` |
| **yyy (suffix)** | **atom 名 (concept name)** | 各 category 内で複数 (8-46 個) | `build`, `ahistorical`, `official` |

**重要な区別**: Atom 表記 `XXX.yyy` (= category.name) と、48 axes の `axis.level` (例 `temporal.emergence`, `ontological.material`) は **別の概念階層**:

| 階層 | 件数 | 例 | 役割 |
|---|---|---|---|
| Atom 表記 `XXX.yyy` | category 24 × 平均 13.6 = 326 | `ACT.build`, `FND.spaceless` | atom 識別子 |
| 48 axes `axis.level` | 10 軸 × levels = 48 | `temporal.emergence`, `ontological.material` | 各 atom の **48 次元座標の軸** |

→ つまり **各 atom (例 `ACT.build`) は 48 axes 上の点として記述される** (これが atom_centroids_48d.parquet)。

---

## 2. ソースコード所在

### 2.1 Atom 概念 (A、固定 326) の定義元

| ファイル | 役割 |
|---|---|
| `language/atoms/esde_dictionary.json` | 326 atom + 10 axes + 48 levels の定義 (固定マスタ) |
| `language/ESDE_LANGUAGE_FROZEN_SPEC.md` | 仕様文書 (atom 体系の全体図) |

esde_dictionary.json の構造:
```json
{
  "meta": {"version": "2.0", "total_concepts": 326, "total_axes": 10},
  "axes": {
    "temporal": {"id": "temporal", "description": "時間的条件",
                 "levels": ["emergence", "indication", "influence",
                            "transformation", "establishment", "continuation",
                            "permanence"]},
    "scale": {..., "levels": ["individual", "community", "society",
                              "ecosystem", "stellar", "cosmic"]},
    ...  # 10 軸
  },
  "concepts": {
    "FND.ahistorical": {
      "id": "FND.ahistorical", "category": "FND", "name": "ahistorical",
      "symmetric_pair": "FND.history",
      "definition_en": "Existing outside of or without reference to history.",
      "triggers_en": [...], "anti_triggers_en": [...], ...
    },
    ...  # 326 atoms
  }
}
```

### 2.2 cid (B、動的) の抽出ソース

| ファイル | 役割 |
|---|---|
| `developmental/v109/v109_atom_event_generator.py` | cid → atom sim 計算 (cid_atom_sim_matrix を read-only で使用) |
| `developmental/v106/v106_*.py` | v10.6 main run で cid を生成 (event_trajectory 等) |
| `developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet` | cid × atom の sim 行列 (24 seeds × ~13 cid × 326 atoms) |

### 2.3 v1103 atom_centroids 生成元

| ファイル | 役割 |
|---|---|
| `unified/v1103/v1103_step_b_atom_centroids.py` | mapper_output から atom 別の 48 axes centroid を集約 |

主要コード抜粋 (v1103 step_b):
```python
MAPPER_DIR = REPO_ROOT / 'language/lexicon/data/mapper_output'

for fp in files:  # *_a1.jsonl × 325 atom
    atom = fp.stem.replace('_a1', '').replace('_', '.', 1)  # e.g. ACT_build → ACT.build
    words = [json.loads(ln) for ln in open(fp)]
    # 各 word の raw_scores (48 axes) と normalized_scores (48 axes) を mean で集約
    raw_cent[k] = mean(words[*].raw_scores[k]) for each of 48 axes k
    norm_cent[k] = mean(words[*].normalized_scores[k])
# 出力: atom_centroids_48d_raw.parquet (325 atom × 48 axes)
```

---

## 3. 抽出フロー (図解)

```
[Language 側 固定マスタ]
   esde_dictionary.json (326 atoms + 10 axes + 48 levels 定義)
        │
        │ 326 atoms (ACT.build 等の固定名) + 48 axes 定義
        ▼
[Lexicon Core pool 生成 (1 億トークン LLM、約 8 日間)]
   mapper_a1.py → mapper_output/*_a1.jsonl (325 atom × 数百 word)
        │  各 entry に 48 axes 全部の raw_scores (0-10) + normalized_scores (0-1)
        ▼
[Atom centroids 集約 (v1103 step B)]
   atom_centroids_48d_raw.parquet (325 atom × 48 axes、word の mean)
        │
        │
[Genesis 側 main run (v10.5/6/7)]
   ESDE 内部で cid (cognitive_id) を実行時に動的生成
        │  seed × cid_id (integer)、24 seeds 合計 316 cid
        ▼
[cid × atom sim 計算 (v10.6)]
   cid_atom_sim_matrix_seed{N}.parquet (cid × 326 atom の 0-1 sim 値)
        │  cid_atom_sim_matrix で「cid がどの atom に近いか」を 0-1 連続値で記述
        ▼
[v1101a 以降の解析]
   attention_emit で per-window で「最も近い atom (= attention_candidate_id)」を選択
   v1102 で receiver_bin × time_scale × atom 分布等を集計
   v1103 で response_atom_distribution、density 算出
   v1104+ で trajectory / predecessor 連鎖等
```

**重要**: cid 自体は「ESDE 内部で生成される動的単位」、atom 自体は「Language 側で事前定義された固定 326 個」、両者の接続 = **sim 行列** (cid_atom_sim_matrix)。

---

## 4. Atom 表記 `XXX.yyy` の意味

### 4.1 24 category prefix 集計 (esde_dictionary.json 実体)

| prefix | atom 数 |
|---|---:|
| PRP | 46 |
| EMO | 30 |
| ACT | 28 |
| FND | 25 |
| SOC | 22 |
| PER | 20 |
| COG | 13 |
| COM | 12 |
| ECO | 12 |
| ELM | 12 |
| WLD | 12 |
| EXS | 11 |
| STA | 11 |
| VAL | 10 |
| BOD | 8 |
| BEI | 8 |
| ABS | 8 |
| TIM | 7 |
| CHG | 7 |
| SPC | 6 |
| MAT | 6 |
| NAT | 4 |
| REL | 4 |
| LOG | 4 |
| **合計** | **326** |

→ **24 prefix × 平均 13.6 atom = 326 atoms** (esde_dictionary.json _meta.total_concepts = 326 と一致)

### 4.2 prefix の意図 (推測、実装コードからは読み取れない)

prefix 名から推測すると (推測である旨明示):
- PRP = Property、EMO = Emotion、ACT = Action、FND = Foundation、SOC = Society、PER = Perception、COG = Cognition、COM = Communication、ECO = Ecology、ELM = Element、WLD = World、EXS = Existence、STA = State、VAL = Value、BOD = Body、BEI = Being、ABS = Abstract、TIM = Time、CHG = Change、SPC = Space、MAT = Material、NAT = Nature、REL = Relation、LOG = Logic

**実装コードでは prefix を独立に処理するロジックは見当たらず、`XXX.yyy` は単に atom 識別子として使われている** (例: `concept_id` カラム、`atom_id` カラム)。prefix での category 別処理は esde_dictionary.json で各 atom の `category` フィールドにより明示されている。

### 4.3 48 axes (mapper_output / atom_centroids) との関係

48 axes は `axis.level` 形式:
```
temporal.emergence, temporal.indication, ..., temporal.permanence       (7 levels)
scale.individual, scale.community, ..., scale.cosmic                     (6 levels)
epistemological.perception, ..., epistemological.creation                (5 levels)
ontological.material, ..., ontological.semantic                          (5 levels)
interconnection.independent, ..., interconnection.resonant               (5 levels)
resonance.superficial, ..., resonance.existential                        (4 levels)
symmetry.destructive, ..., symmetry.cyclical                             (5 levels)
lawfulness.predictable, ..., lawfulness.necessary                        (4 levels)
experience.discovery, experience.creation, experience.comprehension      (3 levels)
value_generation.functional, ..., value_generation.sacred                (4 levels)

合計: 7+6+5+5+5+4+5+4+3+4 = 48 levels (axes)
```

**Atom 表記 `XXX.yyy` の `XXX` (category) と 48 axes の `axis` (temporal 等) は別の階層**:
- `XXX` (例: `ACT`) は category (大分類、24 種)
- 48 axes の `axis` (例: `temporal`) は座標軸 (10 種)
- 両者は概念的に独立

つまり **各 atom (例 `ACT.build`) は 48 axes 上の 48 次元座標として記述される**。atom_centroids_48d_raw.parquet の各行は (atom × 48 axes の score) で、これが atom の固有座標。

---

## 5. Atom a = Atom a か、Atom a = Atom a x y か (パターン判定)

### 5.1 パターン判定: **A + B のハイブリッド**

| 階層 | パターン | 説明 |
|---|---|---|
| **Atom 概念 (A、Language 側固定)** | **パターン A (固定)** | esde_dictionary.json で永続的に 326 個定義、`ACT.build` は常に `ACT.build`、揺れない |
| **cid (B、Genesis 内部動的)** | **パターン B (揺れる)** | seed ごとに動的生成、cid 1 つは 326 atoms に対して 0-1 連続 sim 値で接続 = atom set 全体に対して「揺れる」関係 |

### 5.2 構造事実 (実環境照合結果)

- atom (326 個) は **完全固定** (esde_dictionary.json の `concepts` 326 件、seed や run に依らず不変)
- cid (実行時生成) は **atom 集合との sim で揺れる** (cid_atom_sim_matrix の各行 = その cid の 326 atom に対する 0-1 sim 分布)
- v1102 で確認された「受け手で像が変わる」(留保 #L34 系列) は cid 側の動的性質ではなく、**観察方法 (scope / 粒度 / 集計方式) の側に由来** (留保 #33 系列「集計単位で像が変わる」が本質)

### 5.3 v1102/v1103/v1104 で見える「揺れ」の正体

| 観察された揺れ | 揺れの所在 |
|---|---|
| receiver_bin で像が変わる (#L34) | observation 方法 (scope / 粒度集計) |
| n_members 増で match_rate 低下 (#L14) | 観察方法 (集約単位) |
| CID 100% self-loop (#L33) | cid の構造的性質 (chain で同じ cid に戻る) |
| raw vs norm sign_flip (#L17, #L36) | 観察軸 (sim_basis / density 種類) |
| Synapse v3 weight=1.0 普遍化 (#L41) | データ構造 (Synapse v3 特性) |

つまり **揺れの大半は観察方法側にあり、atom 自体は固定**。cid は atom に対して「sim という連続値で関係を持つ」だけで、cid 自身が揺れる存在ではない (cid は seed × integer で確定)。

---

## 6. v1103 atom_centroids 325 の集約単位

### 6.1 325 の意味

| 数 | 出処 |
|---|---|
| 326 (esde_dictionary.json `concepts` 全件) | Atom 固定マスタ |
| **325 (v1103 atom_centroids 実体)** | **mapper_output の 325 jsonl** から集約 |
| 1 件欠落 = `FND.spaceless` | mapper_output に `FND.spaceless` の jsonl が存在しない (= a1_batch では `zero_core_atoms: 1` で記録) |

### 6.2 集約ロジック

```python
for fp in mapper_output/*_a1.jsonl × 325 files:  # FND.spaceless 除く 325 atom
    atom_name = filename → "ACT.build" 等
    words = jsonl の全行 (各 word が 48 axes × 0-10 raw_scores を持つ)
    raw_centroid[axis_k] = mean of words[*].raw_scores[axis_k]  # axis k = 1..48
    norm_centroid[axis_k] = mean of words[*].normalized_scores[axis_k]
# 出力: 325 atom × 48 axes の centroid matrix
```

→ **atom_centroids_48d_raw.parquet の各行 = その atom に紐づく word 全部の 48 axes raw_scores 平均** = その atom の「典型的な 48 次元座標」

### 6.3 FND.spaceless が欠落する理由 (v1106 §22.5 #L43 の構造的原因)

- esde_dictionary.json には `FND.spaceless` 定義あり (326 中の 1 件)
- mapper_output には `FND_spaceless_a1.jsonl` が存在しない (325 中に含まれない)
- a1_batch では `FND_spaceless.json` が存在 (status: proposed) だが core_pool words = 0 (`zero_core_atoms: 1` と一致)
- 推測: LLM が FND.spaceless に対して word を生成できなかった / Diffuse / 失敗で除外された

→ **mapper_output 段階で FND.spaceless は除外済**、v1103 atom_centroids も 325 atom (FND.spaceless 含まず) で生成 = **v1106 #L43「FND.spaceless が v1103 atom_centroids に欠落する理由」は mapper_output 段階での欠落が原因**。v1106 が古い Synapse v3 を使ったときは FND.spaceless が Synapse v3 内に存在 (Synapse v3 = sentence-BERT で別ロジック生成) して mapper_output - v1103 差分が顕在化、v1106a で mapper_output ベースなら差分 0 (構造的解消)。

---

## 7. mapper_output 48 axes と Atom 内部構造の対応

### 7.1 48 axes 名一覧

mapper_output の raw_scores keys (48 axes、`axis.level` 形式、§4.3 参照):

```
temporal.emergence, temporal.indication, temporal.influence,
temporal.transformation, temporal.establishment, temporal.continuation,
temporal.permanence,  # temporal 7

scale.individual, scale.community, scale.society, scale.ecosystem,
scale.stellar, scale.cosmic,  # scale 6

epistemological.perception, epistemological.identification,
epistemological.understanding, epistemological.experience,
epistemological.creation,  # epistemological 5

ontological.material, ontological.informational, ontological.relational,
ontological.structural, ontological.semantic,  # ontological 5

interconnection.independent, interconnection.catalytic,
interconnection.chained, interconnection.synchronous,
interconnection.resonant,  # interconnection 5

resonance.superficial, resonance.structural, resonance.essential,
resonance.existential,  # resonance 4

symmetry.destructive, symmetry.inclusive, symmetry.transformative,
symmetry.generative, symmetry.cyclical,  # symmetry 5

lawfulness.predictable, lawfulness.emergent, lawfulness.contingent,
lawfulness.necessary,  # lawfulness 4

experience.discovery, experience.creation, experience.comprehension,
  # experience 3

value_generation.functional, value_generation.aesthetic,
value_generation.ethical, value_generation.sacred  # value_generation 4
```

合計: **48 axes** (esde_dictionary.json axes の 10 軸 × 各 levels の合計と一致)

### 7.2 Atom 表記 `XXX.yyy` の `yyy` 一覧と 48 axes の対応

**対応関係の型**: **別構造 (両者は別の階層)**

| | Atom 表記 `XXX.yyy` の `yyy` | 48 axes の `axis.level` |
|---|---|---|
| 件数 | 各 category 内で 1 atom = 1 unique yyy (326 atom 全部で重複あり、例: `ACT.create`, `EXS.creation`) | 48 unique (固定リスト) |
| 例 | `build`, `ahistorical`, `official`, `manifest`, `nonbeing` | `temporal.emergence`, `ontological.material` 等 |
| 関係 | atom の具体名 (語彙的概念) | atom の **座標軸** (48 次元空間の軸) |

→ **`yyy` (atom 名) と 48 axes の `level` は別物**:
- `ACT.build` の `build` ≠ 48 axes の何か
- 各 atom (例 `ACT.build`) は **48 axes 上の 48 次元座標を持つ点として記述される** (atom_centroids_48d_raw.parquet)
- つまり「`build`」という atom 名そのものは座標を持たず、`build` の **48 次元座標 = `ACT.build` を構成する word 群の raw_scores 平均**

### 7.3 v1106a 接続式への含意

v1106a 接続式 (案 X / 案 Y / 案 Z) で扱う「48 axes」は atom 自体の内部構造ではなく、**atom × word の関係を記述する座標軸**:

- 案 X (`raw_scores_max`): 各 word の 48 axes 中の最大 score を取って word の代表値とする
- 案 Y (`axis 単位`): 48 axes 各々で atom × word の関係を保持
- 案 Z (`normalized_scores_max`): 案 X の正規化版

→ 案 Y で「axis 単位」と書いた axis は **48 axes (= mapper_output の axes、座標軸)** であり、**Atom 表記 `XXX.yyy` の `XXX` (category) ではない**。両者を混同しないこと。

---

## 8. 揺れの記述 (パターン B 部分の実装上の扱い)

### 8.1 cid の揺れの記述方法

cid (B、Genesis 内部動的) の揺れは **cid × atom sim 行列** (cid_atom_sim_matrix) で記述:

```python
# v106/cid_atom_sim_matrix_seed0.parquet 構造
columns: ['seed', 'cid', 'ABS.bound', 'ABS.exempt', ..., 'WLD.uncultured']  # 326 atom 列
rows: 各 seed × 各 cid_id (例: seed=0 で 13 cid)
values: 0-1 連続 sim 値 (cosine_sim 系)
```

→ 各 cid (1 行) は 326 atoms に対する **0-1 連続 sim 値の分布** を持つ
→ これが「cid の atom に対する揺れ」の数学的記述

### 8.2 揺れの幅と境界条件

実装上の境界条件 (v1101a-v1104a で観察):
- per-window で **top_1_atom = argmax sim** (per window の rank_1)
- attention_emit の `attention_candidate_id` = 整数 index (sim_matrix の atom 列 index に対応)
- **「これは Atom である」と判定する閾値は明示的に存在しない** (sim の連続値で扱われ、上位 k 個を候補として保持する形)

### 8.3 揺れの観察軸 (48 axes との関係)

- cid_atom_sim_matrix の各値は **cosine sim** (cid embedding と atom centroid embedding の)
- atom centroid は **48 次元 (mapper_output 由来、§6.2)**
- cid embedding も同じ 48 次元空間にマップされている (v106 内部、実装詳細は本確認では追跡せず)
- → **揺れは 48 次元空間内の距離として記述** されており、48 axes と揺れは密接に関係

### 8.4 「Atom a = Atom a × x × y」の x, y に相当するもの

| 揺れ要因 | 実装上の対応 |
|---|---|
| 受け手 (x) | cid 自身 (cid_id ごとに sim 分布が異なる) |
| 状況 (y) | window / scope / metric (per-window で観察される atom が変動) |
| 揺れの結果 | cid × atom × window で観察される sim 値の変動 |

→ **「Atom a = Atom a × x × y」は cid × atom × (window/scope/metric) の関係として実装上扱われている**

---

## 9. 構造事実サマリ (3-5 行で要点)

1. **「Atom」には 2 種類ある**: Language 側固定の 326 atom (esde_dictionary.json) と Genesis 内部動的の cid (cognitive_id、実行時生成)。両者の接続が cid_atom_sim_matrix (cid × atom の 0-1 sim)。
2. **atom 自体は固定**、揺れているのは「cid の atom に対する sim 値分布」と「観察方法 (scope/粒度/集計)」の側。
3. **Atom 表記 `XXX.yyy`** = category (24 種) + atom 名で、**48 axes の `axis.level` (10 軸 × levels = 48) とは別階層**。各 atom は 48 次元座標 (atom_centroids_48d) で記述される。
4. **v1103 atom_centroids 325 atom** = mapper_output 325 jsonl から集約 (FND.spaceless 欠落、a1_batch zero_core_atoms と一致)。
5. **mapper_output 48 axes と Atom 内部 yyy は別物** (axes = 座標軸 10 種 × levels = 48、yyy = atom 名)、v1106a 接続式の「axis 単位」(案 Y) は 48 axes のこと。

---

## 10. v1106a 進行への影響評価

### 10.1 パターン判定結果と v1106a 修正

| 確認 | 結果 |
|---|---|
| Atom a = Atom a か Atom a × x × y か | **A + B のハイブリッド** (atom 固定 + cid 揺れる) |
| 48 axes と Atom 内部 yyy 一致か | **別構造** (axes = 座標軸、yyy = atom 名) |

**Web Claude §3.2 の v1106a 修正候補との対応**:
- パターン A (Atom 固定) + 48 axes 別構造 → **v1106a 現状設計のまま進行**

→ **v1106a 現状設計 (接続式案 X 主軸 + 案 Z 補助) のまま Step B から進行可能**

### 10.2 v1106a で追加で意識すべき点 (本確認で得た理解)

- 接続式の「48 axes」は mapper_output の座標軸 (10 軸 × levels = 48) であり、Atom category prefix (24 種) ではない
- 「Atom 候補分布」(v1105a 出力) の atom は **326 固定の atom 名** (`ACT.build` 等の string)
- 「Atom 候補 → word 接続」は **atom (固定) × word の関係** を mapper_output で取得する

これらは v1106 / v1106a 設計と整合的 (修正不要)。

### 10.3 v1107 以降の主題候補 (本確認で明確化)

- 「Atom が揺れる」現象を扱う場合、対象は **cid 側** (atom 自体は固定)
- cid の揺れの観察 = cid_atom_sim_matrix の per-cid 分布の解析 (まだ深く扱われていない)
- これは v1107 以降の主題候補として記録 (本主題 v1106a 範囲外)

---

## 11. 規律遵守確認

| 規律 | 遵守 |
|---|:---:|
| Code A は構造事実報告のみ | ✓ (判定は Web Claude/Taka 領域) |
| 実環境照合で確認できない箇所は明示 | ✓ (§4.2 prefix の意図、§8.2 揺れの境界条件、§8.3 cid embedding 実装詳細は「本確認では追跡せず」と明示) |
| 妄想化回避 (Web Claude 推測でなく実環境照合) | ✓ (全項目で esde_dictionary.json / mapper_output / v1103 スクリプトの実体を確認) |
| データ取り違え防止規律 (v1106 §22.5) の Atom 抽出ロジック版 | ✓ (本文書は将来の Claude/Taka が読み返せる仕組み記録として位置づけ) |
| 字面保存 (Taka 質問原文) | ✓ (§0 親 + §1.2) |
| 物理層 frozen | ✓ (本確認は read-only、書き込みは本文書のみ) |
| 全体図位置づけ規律 (v1106 §0.1) | ✓ (Atom レイヤーの内部構造を確認、v1106a 接続式の前提条件) |

---

## 12. 報告書の保存場所

`docs/atom_extraction_check/atom_extraction_mechanism_2026-05-26.md` (本文書)

理由: v1106a 主題外の独立記録、Code A 判断で `docs/` 配下 (将来の Claude / Taka が読み返せる場所)。`unified/v1106a/` 配下でなく `docs/` 配下にすることで「主題 v1106a 内のサブ文書」でなく「ESDE 全体の参考記録」として位置づけ明確化。

---

*以上、ESDE Atom 抽出仕組み 記録文書 (Code A、2026-05-26)。Taka 問い「Atom a = Atom a か Atom a × x × y か、表記 XXX.yyy の意味は何か」への構造的回答 = atom 自体は 326 固定 (esde_dictionary.json)、cid (ESDE 内部動的) が atom に対して sim で揺れる、`XXX.yyy` は category.atom_name で 48 axes の axis.level とは別階層。v1106a 現状設計のまま進行可能 (修正不要)、cid 揺れの解析は v1107 以降の主題候補。*
