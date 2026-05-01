# Integration α/β 設計案 — 並存型 vs 統合成長型

*作成*: 2026-05-02、Claude Code
*位置づけ*: v10.4 観察結果を踏まえた v10.5 以降の設計議論素材。3 AI 共同アイディア出しの後、Web Claude へのインプットとして使う。
*親資料*: `v104_main_run_report.md`、`v104_integration_capabilities.md`、`v104_phase_design.md`

---

## 0. 議論の背景 (前提共有用)

### 0.1 ESDE とは

物理層 (engine.state)、cognitive id (CID)、Integration の 3 段階で構成される仮想的な構造実験プロジェクト。

- **物理層**: ノード・リンク・theta・S・R 等の数理オブジェクト (engine.state、frozen)
- **CID**: label を主体として ID を発番、Q (cognitive layer) と C (consciousness layer) を ledger 列として保持
- **Integration** (v10.4 新規): 複数 CID を「ひとまとまりの主体」として扱う仮想構造体

CID と Integration は **実験者が事前に定義した仮想的な命名**。「認知層」「意識層」も実験者が「cid が受信できる範囲」「決定に関わる範囲」として先回りに定義したもの。現実認知との混同は避ける (虚構の構造実験)。

### 0.2 v10.4 Integration の実装

CID 同士の双方向 E3 fired (両者 hosted ∧ Q>0 ∧ C≥1 で発火) を起点として、4 つの trigger で Integration を誕生させる:

- **be3**: fired pair `{a, b}` で size 2
- **open_triad**: be3 + 同 window 内の片側隣接で size 3
- **closed_triad**: be3 + 同 window 内の両側隣接で size 3 (実観察 0 件)
- **third_overlap**: be3 + 第三項候補 2+ 個で size 4+

CID が ghost 化すると、最強結合 Integration 1 つに Q/C を全継承。window 末に active member へ再分配 (Q-poor/C-poor の不足側に逆張り)。member 全員 ghost で active → recorded に永続移行。

### 0.3 観察された n_core パターン (本提案の動機)

v10.4 main run (24 seeds × 50 windows × N=5000) で得られたデータ:

**全 cid の n_core 分布** (888 cids):
- n_core=2: 22.0% (極小 cid)
- n_core=3: 5.2%
- n_core=4: 18.6%
- n_core=5: 54.1% (最頻)
- n_core=7,8: 各 0.1% (極稀)

**Integration 構成 cid の n_core 分布** (18,934 構成員 = 13,550 件 × mean 1.4):
- n_core=2: 0.7% (×0.03、極端な過少代表)
- n_core=3: 3.2% (×0.63)
- n_core=4: 20.3% (×1.09)
- n_core=5: 75.4% (×1.40)
- n_core=7: 0.3% (×2.67、ハブ的活躍)

**be3 (size 2) の組合せ Top**:
- (5, 5): 55.3%
- (4, 5): 29.7%
- (4, 4) + (3, 5): 10%
- → 90% が `{4, 5}` の組合せ

**Integration 内の n_core 同質性**:
- min n_core 平均 4.59 / max n_core 平均 4.85
- 1 つの Integration 内では n_core が大きく違わない

**この観察の含意**:
- 神の手なし (誕生条件は be3 fired という客観条件のみ、n_core フィルタなし) で **自然と n_core 4-5 中心の集合に収束**
- 極小 cid (n_core=2) は人口 22% ありながら Integration からほぼ排除される
- Q/C 動学から自然にこの偏りが出る (実験者が事前にバイアスを設けていない)

→ 「**多ノード CID 同士が自然に繋がる**」構造が観察された。これが α/β 議論の出発点。

---

## 1. α 型 (v10.4 現状) — 並列集合モデル

### 1.1 設計

- member set (frozenset) が異なれば別 IID
- 同じ member set の Integration を 2 個作らない (binding_strength のみ更新、§3.2 重複判定)
- 1 つの cid は **複数 Integration に同時所属**
- merge しない (集合の重なりがあっても並存)

### 1.2 観察された振る舞い (v10.4 main、24 seeds)

| 指標 | 値 |
|---|---:|
| Integration 総数 | 13,550 |
| active / recorded | 11,552 / 1,998 |
| size 2-3 が占める比率 | 90.7% |
| max size | 9 (極稀、24 seeds で 1 件) |
| 1 cid あたり所属 max | **102** |
| 1 cid あたり所属 mean | 29.1 |
| recorded への遷移 | 14.7% (median 12 windows で記録化) |
| Q 継承 → 分配 | 10,000 → 2,790 (28%、72% は recorded に凍結) |
| C 継承 → 分配 | 14,083 → 1,777 (13%、87% は凍結) |

### 1.3 アナロジー (人間社会のグループ所属)

- 同じ人が「家族」「会社」「サークル」「友人グループ」に並列所属
- グループは小さく数が多い、人を介して間接的に繋がる
- グループ単位で人が出入りしても、他のグループは独立に存続

### 1.4 研究射程として答えられる問い

- 「同時に何個の集まりに属しているか」の統計
- ハブ cid (max 102 所属) が Integration 跨ぎで Q/C 流通する効果
- 小集団が大量並存することによる系全体への影響
- 集団単位の「死 (recorded 遷移)」が局所的に積み上がる過程

### 1.5 限界

- 「主観の連続性」「Self の成長」を機構として表現できない
- 巨大な単位 (size 50, 100) は構造的に出てこない
- 集合の境界は明確に切れる (絡み合った大きな単位は表現不能)
- 「家族 + 会社」のような複合的アイデンティティは多重所属で間接表現するしかない

---

## 2. β 型 (新規提案) — 統合成長モデル

### 2.1 設計の核

**共有 member を持つ Integration を merge して 1 つに育てる**。member set は単調増加。

### 2.2 merge 規則の候補

複数案あり、どれを採用するかは設計議論の対象:

#### 案 B1: 共有 member 1 個以上で merge
- (X, Y) と (X, Z) は X を共有 → merge して `{X, Y, Z}`
- 結果: ハブ cid が含まれる Integration はすぐ巨大化
- 懸念: 1 個の超巨大 Integration が全 active cid を吸収する暴走シナリオ

#### 案 B2: 共有 member 2 個以上で merge
- (X, Y, Z) と (X, Y, W) は {X, Y} を共有 → merge して `{X, Y, Z, W}`
- (X, Y) と (X, Z) は X のみなので merge しない
- 結果: triad ベースの育成、be3 単独では merge されない
- 観察: closed_triad/open_triad が共有 edge を持つペアで merge

#### 案 B3: 候補集合の交叉率閾値で merge
- jaccard 距離など定量的閾値 (例: |A ∩ B| / |A ∪ B| ≥ 0.5)
- 閾値次第で挙動が決まる、調整パラメータ多い
- 神の手回避との親和性: 閾値選定が恣意的にならないか

#### 案 B4: 構造条件 + member 全員 hosted で merge
- 案 B2 + 「merge 候補の両 Integration の active member が全員 hosted」
- ghost 化進行中の Integration は merge されない
- 観察: 「生きている集まり同士が合流する」自然なモデル

→ どれを採用するか議論。本提案では **B2 (共有 2 member で merge)** を主候補とする (be3 単独 merge を避ける、triad に到達した時点で初めて merge を許容)。

### 2.3 merge 時の状態合算ルール

merge する Integration A と B から新 Integration C (または A を残して B を吸収) を作る時:

| 属性 | 合算ルール (案) |
|---|---|
| `member_cids` | A ∪ B (active member) |
| `member_history` | A ∪ B (履歴含む) |
| `Q_inherited` | A.Q + B.Q (合算) |
| `C_inherited` | A.C + B.C (合算) |
| `binding_strengths` | per-cid に A + B の値を合算 |
| `birth_step` | 早い方 (= 系の連続性を尊重) |
| `trigger_type` | 起源混合をどう記録するか (議論点、`"merged"` という新タイプ追加? 起源リスト保持?) |
| `state` | 両者 active のみ merge 許容 (recorded 同士、active と recorded の merge は不可) |

### 2.4 想定される振る舞い (実装前の見積もり)

| 指標 | 推定値 (B2 採用時) |
|---|---:|
| Integration 総数 | **数百〜千程度** (現状 13,550 から大幅減) |
| 1 個あたり mean size | **5〜15** (現状 1.4) |
| 1 個あたり max size | **50〜100** (ハブ cid 周りで巨大化) |
| 1 cid あたり所属 max | **3〜10 程度** (現状 102 から激減) |
| recorded 遷移率 | **数 %** (大集合は全員 ghost が稀) |
| Q/C 凍結率 | 現状 87%、β では 60-70% に減 |

### 2.5 アナロジー (生物学的階層化)

- 細胞が組織を形成 → 組織が器官を形成 → 器官が個体を形成
- 一度大きくなった単位は、内部要素が入れ替わっても保持される
- 「Self」が時間とともに大きくなり外部要素を取り込む

### 2.6 研究射程として答えられる問い

- 「主観の連続性」の機構的表現 (大 Integration が長期保持される)
- 構成要素の入れ替わりに対する単位の頑健性
- 巨大 Integration の C 蓄積が系の動学に与える影響
- 「Self の成長」の数理的記述 (size の時系列)
- merge 履歴から見る「同一性の系譜」

### 2.7 リスク

- 1 個の超巨大 Integration が全 active cid を吸収する **degenerate な挙動** に陥る可能性 (特に B1 採用時)
- merge 時の trigger_type 起源情報の失われ (混合をどう記録するか)
- recorded 遷移が極端に減る → 系内資源が永続的に増え続ける (Q+C +14.8% 効果がさらに大きくなる)
- 規律 §14「神の手回避」との緊張: merge 規則自体が実験者の事前判断を強く反映する

---

## 3. α/β トレードオフ比較表

| 観点 | α (v10.4 現状) | β (提案) |
|---|---|---|
| Integration 数 | 多 (13,550) | 少 (推定 100〜1,000) |
| 1 個あたり size | 小 (mean 1.4、max 9) | 大 (mean 5〜15、max 50〜100) |
| 1 cid 所属数 | 多 (max 102) | 少 (max 3〜10) |
| Q/C 蓄積場所 | 多バケット分散 | 少バケット集約 |
| recorded の意味 | 「小さな繋がりの記録」が大量 | 「巨大な記憶単位」が少数 |
| ハブ cid 役割 | 複数小集団の節点 | 巨大 Integration の中核 |
| 「死」の局所性 | 局所的 (1 集合の終了) | 大規模化 (巨大 Integration の終了は大事件) |
| 「主観の境界」 | 多数の小境界、明確 | 1 つの大境界、輪郭ぼやける |
| C 蓄積効果 | +31% (v10.3 比) | より大きい (推定 +50% 以上) |
| 暴走リスク | 低 (size 上限 9) | 中〜高 (B1 で 1 巨大 Integration) |
| 神の手懸念 | 小 (集合一致のみ判定) | 中 (merge 規則の選定) |
| 観察データ量 | 大 (Integration 数多) | 中 (1 個あたり情報密度高) |

---

## 4. β 実装スケッチ (B2 採用時)

### 4.1 修正箇所

`v104_integration.py` の `_maybe_birth` を以下のように拡張:

```python
def _maybe_birth(self, *, members, trigger_type, ...):
    # §3.2 完全一致チェック (α と同じ)
    if frozenset(members) in self._active_members_index:
        # 既存に binding 更新のみ
        return None

    # β 新規: 共有 member 2 個以上の active Integration を検索
    candidates = []
    for iid, integ in self.integrations.items():
        if integ.state != "active":
            continue
        shared = members & integ.member_cids
        if len(shared) >= 2:
            candidates.append((iid, len(shared)))

    if candidates:
        # 最大共有数の Integration を 1 つ選ぶ (tie は id 最小)
        candidates.sort(key=lambda x: (-x[1], x[0]))
        target_iid, _ = candidates[0]
        target = self.integrations[target_iid]
        # merge: 新 cid を吸収
        new_members = members - target.member_cids
        for cid in new_members:
            target.member_cids.add(cid)
            target.member_history.add(cid)
            target.binding_strengths[cid] = 1.0
            self.cid_to_integrations[cid].add(target_iid)
        # 既存 member の binding を +1
        for cid in members & target.member_cids:
            target.binding_strengths[cid] += 1.0
        # 起源混合の記録 (trigger_type をリスト化、または "merged" 追加)
        if not hasattr(target, 'trigger_origins'):
            target.trigger_origins = [target.trigger_type]
        target.trigger_origins.append(trigger_type)
        # active_members_index 更新
        # (既存 frozenset エントリを削除、新 frozenset で再登録)
        ...
        return None

    # 新規誕生 (α と同じ)
    ...
```

### 4.2 merge イベント logger 追加

`integration_lifecycle_log` に新 event_type `"merged"` を追加:

```
event_type: "merged"
target_iid: 取り込み先 (= 残る) Integration
absorbed_iid: ... (ただし B2 では別 IID を absorb しない、新規候補を既存に取り込むだけ)
new_members: 追加された cid のリスト
```

### 4.3 merge と新規誕生の境界

- 共有 member が 0 または 1 → 新規 IID 誕生 (= α と同じ)
- 共有 member が 2 以上 → merge (新規 IID は作らない)

→ be3 単独 (size 2) では merge は起きない。triad/overlap が他の triad/overlap と共有 edge を持つ時に merge する。

### 4.4 検証実験

- α (v10.4 現状) と β を **同 seeds で並列 run** して比較
- bit-identity: 物理層・labels は両モードで完全一致するはず
- 比較指標:
  - Integration 総数、size 分布
  - C 蓄積、Q+C total
  - recorded 遷移率
  - 1 cid あたり所属数

---

## 5. v10.5 として β 実装する場合の段取り (案)

| Phase | 内容 | 想定 wall |
|---|---|---|
| 0. 設計確認 | merge 規則 (B1/B2/B3/B4) を Taka + AI 共同で確定 | (議論時間) |
| 1. β 実装 | v104 → v105 fork、`_maybe_birth` に merge 経路追加、logger 拡張 | 1 日 |
| 2. smoke (1 seed) | 動作確認、bit-identity (物理層) 維持を確認 | 30 分 |
| 3. shadow audit (24 seed) | C 消費・継承・分配を記録のみ、α と比較 | 3-4 h |
| 4. 本番 (24 seed) | β 本番 run、α と比較解析 | 3-4 h |
| 5. レポート | α/β 並列比較レポート | (執筆時間) |

---

## 6. 議論したい点 (3 AI + Taka 向け)

### 6.1 merge 規則の選定

- B1 (共有 1 で merge): degenerate リスクあり
- **B2 (共有 2 で merge)**: 推奨、triad ベース育成
- B3 (jaccard 閾値): 調整パラメータ多
- B4 (構造 + 全員 hosted): 自然だが merge 機会減
- 他の案?

### 6.2 trigger_type の起源混合

merge した Integration の trigger_type をどう記録するか:

- 案 1: 最初の trigger を残す
- 案 2: `"merged"` 新タイプを導入
- 案 3: `trigger_origins: list[str]` を持たせる
- 観察解析でどれが有用か?

### 6.3 recorded 状態の再定義

β では巨大 Integration が稀にしか recorded にならない。これは:
- 望ましい (= 「巨大な記憶単位の連続性」を表現)
- 望ましくない (= 系内資源が永続的に増え続ける)
どちらか?  recorded 条件を「全員 ghost」から「過半数 ghost」等に変更する余地は?

### 6.4 α と β の関係

- β を α の置換として進む (v10.5 = β、α は廃止)
- α と β を並走させ比較する (v10.5 として両方を実装、フラグで切替)
- α の上に β を重ねる (β は α の Integration 群をさらに統合する meta-Integration として)

### 6.5 主題ドキュメント上の位置づけ

- α は「人間社会の所属モデル」のメタファ
- β は「生物学的個体形成」のメタファ
- ESDE 主題における「主観の生成過程」は α/β どちらに近いか?
- 両モデルが意味するものを Taka の主題的な言葉でどう記述するか?

---

## 7. 観察解析の比較設計案

α と β を実装した場合、以下の比較が可能:

| 比較指標 | α 期待値 | β 期待値 |
|---|---|---|
| Integration 総数 | 13,550 | 100〜1,000 |
| size 分布の skewness | 強く右傾 (size 2 が 52%) | より均等 (size 5-20 帯がメイン) |
| 1 cid 所属数 max | 102 | 3〜10 |
| C_max (24 seeds 合計) | 1,556 | 推定 2,500+ |
| recorded 比率 | 14.7% | 数 % |
| 「ハブ cid」の存在感 | 多数の小集団を介して間接結合 | 少数の巨大 Integration の中核 |
| 双方向 E3 fired 件数 | 7,220 | 同等 (物理層 frozen) |
| 物理層 bit-identity | 維持 | 維持 (はず) |

→ 「同じ物理層の上で、Integration 統合規則だけを変えた時に系の動学がどう変わるか」を観察できる。

---

## 8. 結論

v10.4 で実装した α 型は、**多数の小集団の並存** モデルとして機能している。観察された n_core 4-5 中心の自然集積は、α/β どちらの研究にとっても示唆深い。

β 型 (統合成長モデル) は v10.5 以降の射程として実装可能。**merge 規則の選定 (推奨: B2)** と **trigger_type 起源情報の扱い** が主要な設計議論点。

α/β は **どちらが正しいか** ではなく、**何を観察したいか** によって選ぶべきモデル。両者を並走比較する設計が最も情報量が多い。

---

*以上、α/β 設計案。3 AI + Web Claude + Taka 議論の素材として使う。*
