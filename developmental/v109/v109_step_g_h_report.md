# v10.9 Step G + Step H 完了報告 — C2 atom_event_generator + baseline_recalculator

*作成*: 2026-05-08、Code A
*前提*: Step F 判定 (分岐 1 / 案 b / age_target=200 / KDE fallback 留保事項) 確定
*実装変更*: `v109_atom_event_generator.py` に C2 condition 追加、`v109_baseline_recalculator.py` は変更不要 (CONDITIONS から自動的に対応)
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

Step F 判定 (分岐 1 / 案 b / age_target=200) を踏まえて C2 (リズム同調) を atom_event_generator に追加実装、`generate_atom_events_for_condition` を timing 別に分岐させ lifecycle_synced ブランチで各 cid の `birth_step + 200` を timestamp に設定、seed 0 smoke で **全 2,500 events で age_at_event = 200 完全一致** ✓、timestamp range **200-24,729** (cid birth 分布反映)、bit-identity 層 A (in-memory + MD5) 完全一致 ✓、Step H (baseline_recalculator C2) も同 wrapper で C2 condition 走らせて 14 秒で完了 (rp=73,609, bl=159,218, excess=16,378, 1.65 MB)、A2 vs C2 で timestamp 平均が 12,462 vs 12,263 と cid 別発火タイミングが反映、Step I (sensitivity_evaluator) 進行準備完了。

---

## 1. C2 実装内容

### 1.1 atom_event_generator.py への追加

```python
CONDITIONS["C2"] = {
    "Q_cost": 1, "C_gain": 1,
    "cid_selection": "top_k_100",
    "timing": "lifecycle_synced",
    "age_target": 200,
    "description": "リズム同調 (top_k 100、各 cid age=200 で発火、Step F 分岐 1 採用)",
}
```

### 1.2 lifecycle_synced ブランチ実装

```python
def _build_cid_birth_lookup(seed):
    cid_meta = _cid_meta_table(seed)  # v107 流用
    return dict(zip(cid_meta["cognitive_id"].astype(int),
                       cid_meta["birth_step"].astype(int)))

def generate_atom_events_for_condition(seed, cid_df, condition_id):
    if cfg["timing"] == "lifecycle_synced":
        cid_birth = _build_cid_birth_lookup(seed)
        for cid in top_100_cids:
            ts = cid_birth[cid] + age_target  # = birth + 200
            if ts >= RUN_END_STEP:
                continue
            # event 記録
```

### 1.3 環境チェック (実装前確認)

24 seeds で `birth_step + 200 < 25,000` の cid は **5,224/5,224 = 100%** (max birth_step = 24,529)。

→ 発火範囲外による event 喪失なし、全 25 atom × 100 cid × 24 seeds = **60,000 events** が C2 でも生成される。

---

## 2. C2 smoke 結果 (seed 0)

### 2.1 atom_event_generator

```
v10.9 atom_event_generator - mode=smoke, seeds=[0], conditions=['C2']
  [C2] リズム同調 (top_k 100、各 cid age=200 で発火、Step F 分岐 1 採用):
       Q-1, C+1, cid_selection=top_k_100

  seed=0 cond=C2: events=2500, atoms=25, unique_cids=224, reserved=100,
                  t_range=200-24729, size=0.068MB, elapsed=0.18s
```

### 2.2 数値検証

| 指標 | 値 | 想定 |
|---|---:|---|
| n_events | 2,500 | 25 atom × 100 events ✓ |
| n_atoms | 25 | 全 atom 含む ✓ |
| unique_cids | 224 | A2 と一致 (top_k 100、重複あり) ✓ |
| reserved (WLD.artless) | 100 | A2/B3 と同じ ✓ |
| timestamp min | **200** | birth_step=0 + 200 ✓ |
| timestamp max | **24,729** | max birth_step=24,529 + 200 ✓ |
| **全 event の age_at_event** | **200 (unique=1)** | **全件 age=200 ✓** |
| timestamp mean | 12,263 | cid birth 分布の中央 |
| A2 timestamp mean | 12,462 | uniform 分散 |

→ **「各 cid のライフサイクル中盤 (age=200) で発火」が 100% 達成**。

### 2.3 atom 別 events 数 (固定)

```
atom 別: count=25, mean=100, std=0, min=100, max=100
```

→ 全 25 atom で 100 events、A2/B3 と同じ event 数 (cid 数差なし)。

---

## 3. C2 baseline_recalculator (Step H)

`v109_baseline_recalculator.py` は変更不要、`--conditions C2` で実行。

```
v10.9 baseline recalculator - mode=smoke, seeds=1, conditions=['C2'], n_workers=1
=== 順次実行 ===
  seed= 0 cond=C2: rp=73,609, bl=159,218, with_delta=232,827, excess=16,378,
                   size=0.96+0.686MB, t=14.01s
```

### 3.1 A2 / B3 / C2 比較

| 指標 | A2 | B3 | C2 |
|---|---:|---:|---:|
| relation_paths | 76,941 | 86,972 | **73,609** |
| baselines | 186,795 | 182,785 | 159,218 |
| with_delta rows | 263,736 | 269,757 | 232,827 |
| excess rows | 17,207 | 17,491 | **16,378** |
| size (with_delta+excess) | 2.71 MB | 2.83 MB | 1.65 MB |
| 実行時間 | 16.77s | 17.13s | 14.01s |

→ **C2 が最も軽量** (rp 4% 減、bl 15% 減)。理由: cid 別 timestamp で発火タイミングが分散 → 同時刻発火イベントが減って同 step 範囲のイベント間競合が減少。

---

## 4. bit-identity 検証

### 4.1 層 A (同 seed 同条件で 2 回)

| ファイル | 結果 |
|---|---|
| `atom_introduction_events_C2_seed0.parquet` (in-memory + MD5) | **完全一致** ✓ |
| `baselines_with_delta_C2_seed0.parquet` (rng 固定で決定論的) | **完全一致** ✓ |
| `excess_change_adjusted_C2_seed0.parquet` | **完全一致** ✓ |

→ C2 の決定論性: cid 別 birth_step は決定論的 (固定 seed 出力)、`birth + 200` も決定論的、`build_baselines` 内 rng は `np.random.default_rng(20250507)` 固定。

### 4.2 層 B / 層 C

- 層 B: v10.7/v10.8 出力に書き込みなし、`global_activation_factor` の v10.8 出力を read のみ ✓
- 層 C: 出力パス v109/ 配下強制 ✓

---

## 5. C2 の特徴と意義 (Step F 判定の実装結果)

### 5.1 timing pattern の違い (A1/A2 vs B3 vs C2)

| 条件 | timing 戦略 | timestamp 分散原理 |
|---|---|---|
| A1 (v10.8) | uniform_atom_offset | atom_index × 10 step ずらし、atom 内 100 events を 25,000 step に均等分散 |
| A2 | uniform_atom_offset | (A1 と完全同一 timestamp、cid+timestamp set 一致) |
| B3 | uniform_atom_offset | (A1 と同じ timestamp 配置、cid のみ random) |
| **C2** | **lifecycle_synced** | **各 source_cid の birth_step + 200**、cid 別に発火時刻が固定 |

→ C 系統 (タイミング) の純粋評価: A1 vs C2 で **「cid 同一・timing のみ違う」** 比較が clean に成立。

### 5.2 「リズム同調」の構造的実装

Gemini A2 仮説:
> 系のリズムへの同調 (Phase-locking)

Step F 判定での解釈:
> 系全体のリズムではなく、cid 個別のライフサイクル

C2 実装:
- 各 cid が「生まれて 200 step」になる時刻に atom_intro を発火
- cid 個別のライフサイクル位相に同期
- → Gemini A2 の構造的実装

### 5.3 v10.10 への含意 (会話系設計のための部品)

C2 が A1 より高い C 波及を示せば (Step I/M で評価):
- **「cid 早期での外部刺激は遅延入力より効果的」** が定量化
- v10.10 の条件適応型 atom 導入: cid age を監視 → 200 付近で発火

これは **「会話系 = 受信可能状態を識別して精密入力」** の出口固定の素材。

---

## 6. Step I 進行への申請

Step I (`v109_sensitivity_evaluator.py`) に進む許可を求めます。

### 6.1 実装方針

3 候補感度評価:

```python
# 候補 1 (Q/C コスト感度): A1 (v10.8 既存) vs A2 (新)
sensitivity_QC = compare(A1_excess_adjusted, A2_excess_adjusted)
# 比較指標: mean_delta_C_medium / familiarity_short / temporal_immediate 等

# 候補 2 (cid 選定感度): A1 vs B3
sensitivity_cid = compare(A1, B3)

# 候補 3 (タイミング感度): A1 vs C2
sensitivity_timing = compare(A1, C2)

# 出力: per (path, window) で各候補の effect_size + 統計検定
```

### 6.2 比較ベース (v10.8 A1)

`developmental/v108/outputs/main/excess_change_adjusted_seed*.parquet` を A1 baseline として直接読込。

### 6.3 計算量見積もり

- 24 seeds × 3 比較 × per (path, window) で集計
- 1 分以内で完了予想

### 6.4 Step J 統合 smoke の準備

Step J で:
- 全 condition (A2, B3, C2) の bit-identity 層 A 統一検証
- main run 推定 storage / 計算量再評価
- v10.7/v10.8 baseline 不変性 (層 B) 検証

---

## 7. Step G + Step H 完了条件チェック

- [x] CONDITIONS dict に C2 追加
- [x] generate_atom_events_for_condition の timing 分岐 (lifecycle_synced)
- [x] _build_cid_birth_lookup 実装 (v107 _cid_meta_table 流用)
- [x] C2 atom event seed 0 smoke 動作確認
- [x] 全 event で age_at_event = 200 完全一致 ✓
- [x] timestamp range 200-24,729 (cid birth 分布反映)
- [x] bit-identity 層 A (atom_event + baseline 両方 MD5 一致) ✓
- [x] bit-identity 層 B / 層 C 担保
- [x] C2 baseline_recalculator 動作確認 (14 秒、rp=73,609, bl=159,218)
- [x] A2 / B3 / C2 比較データ確認

---

*以上、Code A による v10.9 Step G + Step H 完了報告。Web Claude / Taka からの Step I (sensitivity_evaluator) 進行許可待ち。*
