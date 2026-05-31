# 注意センター ESDE 機能設計 v1 — Code A 確認回答

**Date**: 2026-05-31
**Author**: Code A
**Status**: Web Claude 機能設計 v1 §5 への確認回答、実装ゼロ
**親**: Web Claude 機能設計 v1 + Taka 両 fork 確定 (同型、定義しない)
**規律**: 機能で回答 / 全階層調査 / わからん 4 件提示

---

## 0. 全体結論

**確認 1, 2, 3 すべて流用可、ただし確認 3 で 1 制約あり**:
- (1) 向き先マップ = Atom 系 `engine.virtual.labels[lid]["nodes"]` (frozenset) との overlap 計算で組める、cog.attention は補助
- (2) build_source_event = 第 2 段階版 + 第 3 段階 target_nodes 拡張版がそのまま流用可
- (3) **比較対象は CID 構造 (v918 per_subject) が現実的、Atom プロファイル動的比較は Phase 10 Cell 実装後**

---

## 1. 確認 1: 向き先マップ経路

### 1.1 cog.attention の実態 (全階層調査)

`primitive/v918/v918_memory_readout.py:777 update_attention`:
```python
def update_attention(self, cid, struct_set, core):
    if cid not in self.attention: return
    if not self.is_hosted(cid): return
    att = self.attention[cid]
    # decay
    for k in list(att.keys()):
        att[k] *= ATTENTION_DECAY
        if att[k] < 0.01: del att[k]
    # add (excluding core nodes)
    for n in struct_set:
        if n in core: continue
        att[n] = att.get(n, 0.0) + 1.0
```

→ `self.attention[cid] = {node_id: float}`、core 除外 + decay 付き、各 cid が「周辺どの node に注意を向けているか」を per_step で更新。v910/v911/v913/v914/v918 で同構造 (cognitive layer 共通)。

### 1.2 センター → Atom 系 向き先マップ (state 由来で組める)

**Code A 提案** (神の手回避、設計で固定しない):

```python
# センター state から「際立つ node ID 集合」を抽出 (state 由来、固定でない)
def derive_attention_targets(center_engine, K=5):
    # E top-K (state-driven、derive_action_genesis_driven と同じパターン)
    alive = sorted(center_engine.state.alive_n)
    e_vals = {n: center_engine.state.E.get(n, 0.0) for n in alive}
    return sorted(alive, key=lambda n: -e_vals[n])[:K]

# Atom 系 labels (CID 領域) との overlap で「向き先 CID 群」を決定
def map_to_atom_cids(atom_engine, target_node_ids):
    """センターが指した node ID 集合 → 同じ node ID を含む Atom 系 label の集合"""
    macro = set(atom_engine.virtual.macro_nodes)
    pointed_labels = []
    target_set = set(target_node_ids)
    for lid, lab in atom_engine.virtual.labels.items():
        if lid in macro: continue
        overlap = lab['nodes'] & target_set
        if overlap:
            pointed_labels.append({
                'lid': lid,
                'cid': cog.cid_for_lid(lid) if cog else None,
                'overlap_count': len(overlap),
                'overlap_nodes': list(overlap),
            })
    return pointed_labels
```

→ **設計で固定でなく state 由来**: target_node_ids がセンター state の関数、overlap 計算は決定的だが入力が予測不可能 (Q5 設計通り)。

### 1.3 cog.attention 流用可否

- cog.attention は **Atom 系の側の cid 内部状態** (Atom 系自身の注意)
- センター → Atom 系の「向き先マップ」には **必要ない** (上の overlap 計算で十分)
- ただし Atom 系の cog.attention を **読んで参考にする** (例: 既に Atom 系がよく見ている領域は重み増) ことは可能

**結論**: cog.attention は補助、本筋は **labels[lid]["nodes"] と overlap**。

### 1.4 node ID 空間問題

| 構成 | センター N | Atom 系 N | node ID 空間 |
|---|---|---|---|
| (a) 同 N | 5000 | 5000 | 共通、直接 overlap 可 |
| (b) センター小 | 100 | 5000 | **ID マッピング関数要** (例: hash, modulo, 任意写像) |

Web Claude 提案 (機能設計 v1 §1 機能 1) は「同型 V82Engine を 1 個、Atom 系とは別 instance」+ 「縮小版 (N=100)」。両方混在 → センター N=100 の場合 ID マッピングが必要。

**Code A 観察**: 単純化するなら **同 N (両者 5000)** が ID 空間共通で最も素直。「シングルユニット」を「**N=5000 だが seed が違うので独立動作**」と解釈可能。これは Taka 「同型」確定とも整合 (骨格同一)。

---

## 2. 確認 2: source_event 流用

### 2.1 既存 build_source_event (流用可)

**第 2 段階版** (`stage2_step_cde_external_loop.py:83-100`):
```python
def build_source_event(iter_id, external_payload):
    es = external_payload['esde_state']
    return {
        'iter': iter_id,
        'event_id': f'ext_loop_{iter_id}',
        'source_cid': iter_id,
        'timestamp': external_payload['timestamp'],
        'esde_alive_n': es['alive_n'], ...
    }
```

**第 3 段階版** (`stage3_step_b_smoke.py:83-100`、target_nodes 拡張):
```python
return {
    'condition': condition, 'iter': iter_id,
    'event_id': f'{condition}_iter_{iter_id}',
    'timestamp': external_payload['timestamp'],
    'target_nodes': external_payload['target_nodes'],
}
```

### 2.2 target_nodes エンコード道筋

```python
# 別系の結果を target_nodes に翻訳
def translate_other_to_atom(other_engine, other_step_count=5):
    """別系で active になった node 群を target_nodes に翻訳"""
    other_engine.step_window(steps=other_step_count)
    # 別系 state の「結果」 = active node の上位
    e_vals = {n: other_engine.state.E.get(n, 0.0)
              for n in other_engine.state.alive_n}
    top_K = sorted(e_vals.keys(), key=lambda n: -e_vals[n])[:K]
    return top_K  # この list が source_event['target_nodes']

# Atom 系へ書込 (第 3 段階 inject_to_engine そのまま)
def inject_to_atom(atom_engine, source_event):
    atom_engine.physics.inject(atom_engine.state,
                                target_nodes=source_event['target_nodes'])
```

→ **第 2 段階 + 第 3 段階パターンがそのまま流用可**、新規実装ほぼ不要。

### 2.3 1 往復のフロー (Web Claude 機能設計 §1 機能 3)

```
[センター発火 derive_attention_targets(center_engine)]
       ↓ target_node_ids
[map_to_atom_cids(atom_engine, target_node_ids)]
       ↓ pointed_labels (cid + overlap_nodes)
[overlap_nodes を source_event 形式で別系に入力]
  source_event = {target_nodes: overlap_nodes, ...}
       ↓
[別系 (other_engine) で source_event を inject + 数 step]
  other_engine.physics.inject(other_engine.state, target_nodes=overlap_nodes)
  other_engine.step_window(steps=5)
       ↓
[translate_other_to_atom(other_engine)]
       ↓ new target_nodes (別系の結果)
[Atom 系へ書き戻し]
  atom_engine.physics.inject(atom_engine.state, target_nodes=new_targets)
       ↓
[Atom 系次 step で物理変化 → CID 再構築]
```

→ 機能 3 全フロー が **第 2-3 段階の組合せ** で実装可能。

---

## 3. 確認 3: 無し/有り 比較の既存解析経路

### 3.1 既存解析の現状

#### 利用可能な比較経路 (CID 構造)

| 解析 | 経路 | 比較対象 |
|---|---|---|
| v918 per_subject CSV | `unified/stage2_external_loop/run_n5000/diag_v918_genesis_smoke/subjects/per_subject_seed42.csv` | final_state / lifespan / last_n_partners / original_phase_sig / last_familiarity_max |
| v107 baseline | `developmental/v107/outputs/main/baselines_with_delta_seed*.parquet` | source_event との delta (24 seeds) |
| v107 cross_seed | `v107_cross_seed_analyzer.py` | seeds 横断統計 |
| v104 integration | `developmental/v104/v104_integration.py` IntegrationManager | Integration 構成 cid (Q/C 継承) |
| v918 aggregates | `aggregates/per_window_seed*.csv` | window 末集計 (labels_active, alive_l, etc.) |

→ **CID 構造の無し/有り比較は既存解析でできる** (第 4 段階改修小 smoke でも実証)。

#### Atom プロファイル比較 (制約あり)

`language/lexicon/data/mapper_output/*_a1.jsonl` (325 atoms × 48 スロット連続値):
- **これは LLM 駆動の静的観測**、ESDE run 中に変化しない
- ESDE run 中に Atom プロファイル変化を測るには **cid と Atom の bridge** が要る
- 現状の bridge は **Phase 10 Cell の構想 (未実装)** + **β に Atom プロファイル付与 (融合候補、`docs/LANGUAGE_LEGACY_DIGEST.md` §5.2)** で、**動的測定機構は実装されていない**

### 3.2 Code A 観察 (制約と回避案)

**制約**: 「Atom 系の出力」を Atom プロファイル変化で測るのは **現状機構では不能**。

**回避案** (機能で代替):

| 比較対象 | 何を測るか | 既存経路 |
|---|---|---|
| (a) **CID 構造の動的変化** | labels 数、n_core 分布、寿命、n_partners、final_state | v918 per_subject (実証済) |
| (b) **Integration 出力** | n_integrations_active / cid 構成 / Q/C 継承 | v104 IntegrationManager |
| (c) **応答候補分布** | label の phase_sig 分布、bin 占有度 (VirtualLayer occupancy/history) | virtual_stats / phase_snapshots |
| (d) **β 動学 (v105)** | β-merge 履歴、β.Q_inherited / C_inherited | v105_integration.py |

→ **(a) (b) (c) で「Atom 系出力の差」を測れる**。Web Claude §3「同じ seed でセンター無し / 有り run、Atom 系出力が変わるか」は (a)+(b)+(c) で実装可能、(d) は v105 機構を利用。

(Atom プロファイル変化を含む詳細比較は Phase 10 Cell 実装後の別作業。)

### 3.3 比較 smoke の構造

```python
# 同じ seed で 2 run
for run_name in ['no_center', 'with_center']:
    atom_engine = build_atom_engine(seed=42)  # 共通起動 (補足 §1.1 パターン)
    if run_name == 'with_center':
        center_engine = build_center_engine(seed=99)  # 別 seed
        other_engine = build_other_engine(seed=100)
    for w in range(N_WINDOWS):
        atom_engine.step_window(steps=100)
        if run_name == 'with_center':
            # 機能 3 1 往復
            run_attention_loop(center_engine, atom_engine, other_engine)
        # Atom 系の出力を記録
        record(atom_engine, w, run_name)
# 比較: no_center vs with_center で labels 数 / n_core / phase 分布 / β
```

→ **改修小** (compare 関数追加のみ)、第 4 段階 smoke パターン (6 conditions × 5 windows) と類似構造。

---

## 4. わからん 4 件 (推測しない)

| # | 不明 | わからん理由 |
|---|---|---|
| 4-1 | センター N と Atom 系 N の関係 | 同 N (5000) なら ID 空間共通で素直、しかし「シングルユニット」感がない。N=100 なら ID マッピング関数要。Taka / Web Claude 判断 |
| 4-2 | 別系 (素の物理系) の上っぱり「無し」の度合い | V82Engine は標準で virtual_layer (cog なし)、これで「素」か。または stress_enabled=False / pressure_prob=0 等で更に裸にするか |
| 4-3 | 比較 baseline の condition 数 | 改修小 smoke は 6 conditions (mat_alpha 等)、注意センター比較は最小 2 (無し / 有り) で良いか、複数 seed が必要か |
| 4-4 | dynamic_threshold (Q5、Web Claude §1 機能 2) の関数形 | 「state 由来で固定値置かない」の具体形 (例: stress_intensity 比、mean_E top-K の境界等) は Web Claude 設計か Code A 提案か |

---

## 5. Code A 観察 (機能視点)

### 5.1 機能設計 v1 の実装可否

| 機能 | 実装難易度 | 流用元 |
|---|---|---|
| 機能 1 自走 | 極小 | 第 2 段階補足 V82Engine 起動手順 |
| 機能 2 発火 | 小 | 新規 derive_attention_targets + dynamic_threshold (Code A 提案) |
| 機能 3 橋渡し | 極小 | 第 2 段階 stage2 + 第 3 段階 stage3 そのまま |
| 比較 (無し/有り) | 小 | 第 4 段階 smoke パターン + v918 per_subject 集計 |

→ **全体改修コスト = 小**、新規発明なし、既存パターンの組合せ。

### 5.2 同型 (Taka fork) の帰結

- センター / Atom 系 / 別系 は **同じ V82Engine + VirtualLayerV9**
- 違うのは:
  - センター = while True 常駐、N 小 (?)
  - Atom 系 = 既存 (cog + Atom dictionary + Synapse)
  - 別系 = 素 (cog なし、Atom なし)
- 骨格同一 → 「センター無し / 有り」比較が成立 (Taka 格言 #3)

### 5.3 第 4 段階 smoke 結果 (mat_alpha 効く) の活用

- mat_alpha = 「CID 寿命操作」、注意センター実験では **mat_alpha は触らない方が baseline 安定**
- 第 4 段階の改修小 smoke は **注意センター実験の基盤になる** (各 engine の起動パターン + 比較構造)
- → 無駄でない、ただし注意センター本実装には別軸 (機能 1-3)

---

## 6. Web Claude / Taka 判断要請

| # | 判断要 |
|---|---|
| ① | センター N: 同 N (5000) で ID 空間共通、または N 縮小 (100) で ID マッピング |
| ② | 別系 (素の物理系) の上っぱり: 標準 V82Engine (virtual_layer 含む) でいいか、更に裸にするか |
| ③ | 比較 condition: 最小 2 (無し / 有り)、または複数 seed (24 seeds) |
| ④ | dynamic_threshold 関数形: Code A 提案で OK か、Web Claude 設計か |
| ⑤ | Atom プロファイル比較は今回スコープ外 (CID 構造 + Integration + phase 分布で代用) で OK か |

---

## 7. 一文サマリ

注意センター ESDE 機能設計 v1 確認回答 (Code A、2026-05-31、Web Claude §5 3 確認点 + Taka 同型 fork) として、確認 1 向き先マップ (cog.attention は補助、本筋は Atom 系 labels[lid]["nodes"] frozenset との overlap、センター state.E top-K → overlap で state 由来固定でなく組める、node ID 空間問題は同 N で共通か N 縮小で写像 4-1 不明) / 確認 2 source_event (第 2 段階 build_source_event + 第 3 段階 target_nodes 拡張がそのまま流用可、別系結果 → top-K E → target_nodes 翻訳、第 3 段階 inject_to_engine の physics.inject そのまま、1 往復フロー全部第 2-3 段階組合せで実装可) / 確認 3 比較経路 (CID 構造比較は v918 per_subject 実証済、Integration v104 IntegrationManager、応答候補 phase 分布 virtual.occupancy で可、Atom プロファイル動的比較は **Phase 10 Cell 未実装で現状不能**、回避案 (a) CID 構造 (b) Integration (c) phase 分布 (d) β 動学で代用、第 4 段階改修小 smoke パターン流用)、わからん 4 件 (センター N 5000 vs 100 / 別系裸度 / 比較 condition 数 / dynamic_threshold 関数形)、Code A 観察 (機能 1-3 全部改修小・新規発明なし・第 2-3 段階組合せ、同型 fork で比較成立、第 4 段階 mat_alpha 知見は基盤として活用)、判断 5 件 (N / 別系裸度 / condition 数 / dynamic_threshold 設計者 / Atom プロファイル比較スコープ)、書込み unified/attention_center_prep/ 配下のみ。

---

**Code A 確認回答 end. Web Claude / Taka 判断後、実装に進む。**
