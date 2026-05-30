# 第 3 段階 Step A — 認識確認 (主体性検証 設計受領 + 全階層調査結果)

**Date**: 2026-05-31
**Author**: Code A
**Status**: 認識確認、Taka 確認待ち
**親**: 第 3 段階 設計書 (Web Claude、2026-05-31)
**規律**: §0.2「全階層調べる」+ §4.1「わからんことは言えよな」

---

## 0. 認識確認の前提

設計書 §4.2 実装条件事前チェック 6 項目を、**全階層調査**で確認した結果を提示する。「無い」と書く前に autonomy / primitive / developmental / cognition / ecology を全部読んだ。

---

## 1. チェック 1 — 起動 Genesis + 外部接続の統合が動くか

### 認識: ✓ 動く (第 2 段階補足で確認済)

第 2 段階補足で `engine.run_injection()` + `VirtualLayerV9` + `step_window` ループが動くことを実証 (191 CID 生成)。第 3 段階の統合は補足の起動コードに第 2 段階 Step C-H の外部接続ループを追加するだけ。

統合スクリプト雛形:
```python
engine = V82Engine(seed=42, N=5000, encap_params=V82EncapsulationParams(
    stress_enabled=False, virtual_enabled=True))
engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
engine.virtual.torque_order = "age"
engine.virtual.deviation_enabled = True
engine.virtual.semantic_gravity_enabled = True
engine.run_injection()  # V43Engine.run_injection (INJECTION_STEPS の物理 prime)

for w in range(maturation_windows):
    engine.step_window(steps=window_steps)
    state = read_genesis_state(engine, w)
    external_payload = write_external(state)
    new_event = build_source_event(w, read_external())
    inject_to_engine(engine, new_event)  # ★ Part 2 (下で詳述)
```

---

## 2. チェック 2 — 戻しの実効化機構 (全階層調査結果)

### 認識: 既存の **「source_event 受信機構」は存在しない**。
ただし **`physics.inject(state, target_nodes=...)`** が **既存の公式外部介入インターフェース** として使える。これを「戻しの実効化」に使う。

### 2.1 調査範囲 (Taka 規律「全階層調べる」)

| 範囲 | 結果 |
|---|---|
| `autonomy/v82/esde_v82_engine.py` (V82Engine, 324 行 全文) | source_event 受信なし、step_window 内 background seeding のみ |
| `autonomy/v90/virtual_layer_v9.py` (VirtualLayerV9, 942 行) | _torque_multiplier は内部 feedback (signal_ratio)、外部入力受信ポートなし |
| `primitive/v918/v918_memory_readout.py` (3153 行) | run 関数は SubjectLayer cog + engine 駆動、source_event 受信機構なし |
| `primitive/v918/v918_orchestrator.py` (337 行) | v18_* 観察 read-only、書き戻しなし |
| `primitive/v918/v918_fetch_operations.py` (78 行) | CidSelfBuffer 生成のみ |
| `primitive/v918/v918_cid_self_buffer.py` (181 行) | 観察 read-only |
| `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py` | **`run_injection` 内で `physics.inject(state)` を呼ぶ** ← 公式 |
| `ecology/engine/genesis_physics.py:232` | **`def inject(state, target_nodes=None)` 公式インターフェース** |
| `developmental/v107/v107_event_aggregator.py` | post-process aggregator (記録専用、engine 入力ではない) |

### 2.2 発見: physics.inject(state, target_nodes=...) (genesis_physics.py:232)

```python
def inject(self, state, target_nodes=None):
    p = self.params
    if target_nodes is None:
        mask = state.rng.random(state.n_nodes) < p.inject_prob
        target_nodes = [i for i in range(state.n_nodes) if mask[i]]
    if not target_nodes:
        return target_nodes
    for nid in target_nodes:
        state.E[nid] = min(1.0, state.E[nid] + p.inject_amount)
        state.alive_n.add(nid)
    for a in range(len(target_nodes)):
        for b in range(a + 1, len(target_nodes)):
            ni, nj = target_nodes[a], target_nodes[b]
            if abs(ni - nj) <= p.inject_pair_radius:
                self._try_add_link(state, ni, nj, p.inject_link_strength)
    return target_nodes
```

これが **公式の外部介入機構**:
- `target_nodes` を外部から指定可能 (デフォルトは内部乱数)
- 指定 node の `state.E` を `inject_amount` だけ加算 + `alive_n` に追加
- 近傍ペア (inject_pair_radius 内) に link を作る
- run_injection / step_window から既に内部利用されているので副作用は理解されている

### 2.3 戻し実効化の設計

```python
def inject_to_engine(engine, source_event):
    """外部結果を Genesis に戻す (実効化)"""
    target_nodes = source_event['target_nodes']  # 外部側で決めた node リスト
    engine.physics.inject(engine.state, target_nodes=target_nodes)
    # attribute 保持も継続 (第 2 段階互換、観察用)
    if not hasattr(engine, '_stage3_external_inputs'):
        engine._stage3_external_inputs = []
    engine._stage3_external_inputs.append(source_event)
```

これで **戻しが次 step の Genesis (state.E, alive_n, links) を変える** = 実効する。第 2 段階の attribute 保持のみとの違いはここ。

### 2.4 留保

- physics.inject はもともと「物理層の確率的 seeding」用。第 3 段階で「外部由来の特定 target」を渡しても **物理的にはちゃんと動く** が、`inject_amount` (params default) で E が +α される。`inject_pair_radius` 内のペアに link が作られる。
- これらは Code A 視点では「物理層に書く = frozen 違反では?」と気にする所だが、**新規 engine instance (unified/stage3_subjectivity/ 配下)** に対する書込みなので **既存物理層 (developmental/v105 等)** には触らない。物理層 frozen の規律は維持。
- **新たな受信機構を実装するのではなく、既存の inject インターフェースを使う**。これは設計書 §0.2「無いと書く前に全階層調べる」の結果、既存で十分という結論。

---

## 3. チェック 3 — Genesis 状態から外部アクションを決めるロジック

### 認識: 設計可能。state の以下フィールドが使える

| フィールド | 型 | 利用案 |
|---|---|---|
| `state.E[i]` | dict float | node エネルギー (top-K 抽出で「最も活性な node」) |
| `state.theta[i]` | ndarray float | 位相角 (位相クラスタの中心 node) |
| `state.Z[i]` | ndarray int | Z 値 (役割タイプ) |
| `state.alive_n` | set int | 生存 node |
| `state.alive_l` | set tuple | 生存 link (次数集計で「ハブ node」) |
| `state.S[link]` | dict float | link 強度 (強い link の端点) |
| `state.R[link]` | dict float | resonance (共鳴している link の端点) |
| `engine.virtual.labels` | dict | label (CID) 群、`nodes`/`phase_sig`/`age` |
| `engine.virtual_stats` | dict | labels_active, torque_events, mean_omega 等 |

### 3.1 提案: 「最 active CID の core node を外部に送る」

```python
def derive_action_from_genesis(engine):
    """Genesis 状態 → 外部アクションを決める (genesis_driven)"""
    labels = engine.virtual.labels
    if not labels:
        return []
    # 最大 label (member node 数最多) を選ぶ
    largest_lid = max(labels, key=lambda l: len(labels[l]['nodes']))
    core_nodes = list(labels[largest_lid]['nodes'])
    # 上位 K nodes (E 値 top-K)
    K = 5
    return sorted(core_nodes, key=lambda n: -engine.state.E.get(n, 0))[:K]
```

この target_nodes が外部 (sandbox/state.json) に書かれ、外部結果として戻ってくる (実際の外部処理は固定で identity、第 3 段階では「Genesis 状態がそのまま戻る」)。

### 3.2 留保

- 「最大 label の core node top-K (E 値)」は **仮**。他案あれば Web Claude / Taka 判断:
  - 案 α: 上記 (label 最大、E top-K)
  - 案 β: 全 label から phase_sig 中心 node を 1 つずつ
  - 案 γ: alive_l ハブ node top-K
- どれを使っても、shuffle で乱数化すれば「Genesis 由来かどうか」を判定できる

---

## 4. チェック 4 — shuffle (主体性判定) の設計

### 認識: 2 条件を seed 単位で比較

| 条件 | 外部アクション決定 |
|---|---|
| **genesis_driven** | `derive_action_from_genesis(engine)` で Genesis 状態から target_nodes 決定 |
| **shuffled** | 同じ K 個の target_nodes を、**乱数 (alive_n からランダム選択)** で決定 |

### 4.1 shuffle 粒度 (Code A 提案)

3 パターン用意:
| shuffle 種類 | 内容 |
|---|---|
| shuffle_random_nodes | target_nodes を alive_n からランダム K 個 |
| shuffle_state_E | E 値を全 node 間でシャッフルしてから top-K |
| shuffle_label_membership | label の nodes 集合をシャッフルしてから処理 |

第 3 段階 smoke では **shuffle_random_nodes** から (最もシンプル、判定が明瞭)。

### 4.2 判定指標 (Code A 提案)

genesis_driven と shuffled で **以下が異なれば「Genesis 由来」**:
- 次 step の `labels_active` 変化量
- 次 step の `alive_l` 変化量
- 次 step の `torque_events` 変化量
- 5 step 累積で `E_top_K` の選ばれた node がどれだけ持続するか

判定閾値:
- 各指標で 24 seeds 平均の差が `|Δ| > σ_within_condition` → Genesis 由来
- 全指標で差が観察されない → 神の手
- 1-2 指標のみ差 → partial

### 4.3 留保

- 「神の手か判定する閾値」は事前固定 (σ 1 倍) で良いか、それとも事後決め?
- shuffle の seed は固定 (再現性) か、別 seed 24 個用意か (gradient 観察)

---

## 5. チェック 5 — smoke → フルの段取り

### 認識: smoke (3 分) で 6 項目確認 → フル (1-2 時間) で確定

| 段 | 設定 | 確認内容 | 想定時間 |
|---|---|---|---|
| 5-A | smoke (mat 3, track 1, ws 100, seed 42) | 統合動くか + 戻し実効するか + shuffle 比較が出るか | 3 分 |
| 5-B | smoke 検証 PASS なら Web Claude 報告 + Taka 判断 | フル前 gate | - |
| 5-C | フル (mat 20, track 10, ws 500, 24 seeds) | 主体性確定判定 | 1-2 時間 × 24 = 1 batch ? |

### 5.1 計算量見積もり

- smoke 1 seed: 187 秒 (補足で実測)
- フル 1 seed: 187 × (20/3) × (10/1) × (500/100) ≈ 100 分 × 補正で約 **1-2 時間/seed**
- **24 seeds 単一バッチ (Genesis 系規律) で 24-48 時間** → tmux 規模

### 5.2 留保

- 24 seeds 単一バッチ規律 (`24seeds_single_batch` memory) に従い、smoke で OK なら **24 seeds 一括 main run** が原則
- ただし「フル 1-2 時間 × 24 = 1-2 日」かかるので Taka 判断要

---

## 6. チェック 6 — 不足部分の事前提出

### 6.1 不足 (Taka / Web Claude 判断要)

| # | 不足項目 | 案 |
|---|---|---|
| 不足 1 | derive_action_from_genesis の具体ロジック (案 α/β/γ どれ) | Code A 推奨: 案 α (最大 label の E top-K)、smoke で挙動見て調整 |
| 不足 2 | shuffle 粒度 (random_nodes / state_E / label_membership) | Code A 推奨: smoke は random_nodes、フル前に Web Claude 判断 |
| 不足 3 | 判定指標と閾値 | Code A 推奨: 24 seeds 平均で σ 1 倍超え |
| 不足 4 | 外部側処理は何をするか (identity = Genesis state そのまま返す / 別ロジック?) | Code A 推奨: smoke は identity、本番で「外部 LLM 呼ぶ」等の発展可能 |
| 不足 5 | 第 2 段階 attribute 保持と第 3 段階 inject の併用方針 | Code A: 併用 (観察用に attribute も保持) |

### 6.2 わからん事 (規律「わからんことは言えよな」)

| # | 不明 | 仮定で進めるか / Taka 判断要 |
|---|---|---|
| 不明 1 | inject_amount default が `params.inject_amount` (V19g_canon の base_params 経由?) いくらか | 仮定で進める (smoke で確認) |
| 不明 2 | physics.inject を tracking 内で呼ぶと既存物理 (background_seeding) と二重発火しないか | 仮定: 二重 OK (E は clamp で 1.0 上限)、smoke で確認 |
| 不明 3 | 「外部処理」を identity 以外にしたい場合、何を呼ぶ (Atom dictionary? LLM?) | 第 3 段階スコープ外、第 4 段階以降 |

---

## 7. 規律遵守チェック

| 規律 | 遵守 |
|---|---|
| 物理層 frozen (既存 developmental/v105 等 1 byte も触らず) | ✓ unified/stage3_subjectivity/ 配下のみ |
| 「無いと書く前に全階層調べる」 | ✓ §2.1 で全 9 階層調査 |
| 「想定するな、聞け」 | ✓ §6.1, §6.2 で不足/不明を Taka 提示 |
| 「わからんことは言えよな」 | ✓ §6.2 |
| 主体性検証スコープ (loop 崩壊は第 4 段階) | ✓ §0 + §4 で限定 |
| 24 seeds 単一バッチ | ✓ §5 で記載 |
| smoke 後は必ず止まって報告 | ✓ §5-B で gate 明記 |
| 判定語制限 (「成功/失敗」を使わない) | ✓ 全文「動く/動かない」「異なる/同じ」で記述 |
| self-fulfilling baseline 検査 (7 段階目) | ✓ shuffle 比較が baseline、 genesis_driven と独立評価 |
| Atom と Genesis の分離 | ✓ Atom は使わず Genesis 状態のみ |

---

## 8. Code A 提案 (Taka / Web Claude 判断要)

### 8.1 進行案

1. **本認識確認に対する Taka 判断**を受領
2. 受領後 **smoke 統合スクリプト** (`stage3_step_b_smoke.py`) 実装
3. smoke 実行 → 結果報告 (5-B gate)
4. Taka / Web Claude 判断 → フル進行 or smoke 修正

### 8.2 Web Claude 判断ポイント

不足 1-5 (§6.1) について Web Claude 設計判断:
- 特に derive_action_from_genesis のロジックは「主体性検証の核心」なので Web Claude 判断重要
- shuffle 粒度も「神の手判定の正確さ」に直結
- 判定閾値も事前に決めると都合が良い (post-hoc 回避)

---

## 9. 一文サマリ

第 3 段階 Step A 認識確認 (Code A、2026-05-31、Web Claude 第 3 段階設計書受領後) として、6 項目チェック結果を提示: (1) 統合 = 第 2 段階補足の起動コードに第 2 段階 Step C-H 外部接続を追加するだけで動く、(2) 戻し実効化機構 = 全 9 階層調査の結果「source_event 受信機構は存在しない」が **既存の `physics.inject(state, target_nodes=...)` (ecology/engine/genesis_physics.py:232) が公式外部介入インターフェース** として使える、これで戻しが次 step Genesis (state.E, alive_n, links) を変える実効が出る、(3) Genesis 状態から外部アクション = state.E top-K、最大 label core node 等から決定 (案 α/β/γ、Code A 推奨 α 案 = 最大 label core node の E top-K)、(4) shuffle = random_nodes / state_E / label_membership の 3 粒度、smoke は random_nodes から、判定は labels_active/alive_l/torque_events の 24 seeds 平均差で σ 1 倍超え、(5) smoke (mat 3, track 1, 約 3 分) → 報告 gate → フル (mat 20, track 10, 24 seeds, 24-48 時間 tmux 規模)、(6) 不足 5 件 + 不明 3 件提示 (derive_action ロジック / shuffle 粒度 / 判定閾値 / 外部処理内容 / inject 二重発火等)、規律遵守 (物理層 frozen, 全階層調べる, 想定するな聞け, 主体性スコープ限定, 24seeds 単一バッチ, smoke 止まる, 判定語制限, self-fulfilling baseline 検査, Atom/Genesis 分離) ✓、書込み unified/stage3_subjectivity/ 配下のみ、提案進行: Taka 判断 → smoke 実装 → smoke 実行 → 報告 → フル判断。

---

**Step A 認識確認 end. Taka / Web Claude 判断待ち。判断後 smoke 統合スクリプト実装に進む。**
