# v10.11 Code A 認識確認質問書 — Step A 即決確定要請

*作成*: 2026-05-10、Code A
*親*: `v111_phase_design.md` (Web Claude 主題ドキュメント、2026-05-10)
*対象*: Web Claude (応答)、Taka (承認)
*目的*: §9 認識確認項目の実施 + 機構実装の細部確定 + 観察解像度の Code A 推奨提案

---

## 0. 一文サマリ

v10.11 主題 (Integration 形成プロセスを source_event 新カテゴリ alpha_birth / beta_birth として定義し T-100〜T+100 step の応答性プロファイル構築) について §9 認識確認を実施、母集団実測で **α formation events 13,881 / β formation events 6,476 (24 seeds 合計)、α は member 2-8 (mean 2.63)、β は常にペア (2 cid 限定)** という構造的事実を確認、観察解像度として **Code A 推奨案 b (t_offset 10 step 刻み、21 samples/event-member、storage ~52 MB)** を提案、計算量推定 5-10 分 (24 seeds 並列、v107 lookup 流用)、累計 storage 1.58 GB (26%、打切閾値 50% 余裕大)、機構実装は v107 _build_state_lookups の C/pulse 値時系列 lookup 流用で post-process 全体は実 ledger 不変 (新規 source_event スキーマは event_id 形式のみ)、Code A 自主提案 4 件 (解像度 b 案 / no_alpha 別フレーム / event_id 形式 / 観察対象は formation event member のみ) + 確認事項 5 件、Web Claude / Taka 応答後 Step B (実装着手) に進む、§0.3 打ち切り条件 (3 軸超過 / 構造解明不能 / 計算量超過) は Code A も上申義務。

---

## §1 §9.2 母集団確認 (実測値)

### 1.1 24 seeds 合計 formation events

| 区分 | events | member-event pairs | member/event |
|---|---:|---:|---|
| **α formation** | 13,881 | 36,476 | mean 2.63, min 2, max 8 |
| **β formation** | 6,476 | 12,952 | mean 2.00, **常にペア (2 cid 限定)** |

### 1.2 構造的事実 (実測ベース、判定なし)

- **α formation は可変サイズ** (2-8 cid)、平均 2.63
- **β formation は完全にペア限定** (member 数 = 2 一定)
- death events: alpha/beta_lifecycle_log で 0 件 (= 形成された α/β は run 終了まで維持される、もしくは death イベントが別形式)

→ v10.10 第一弾で「α/β は同 cid 集合に発生」と観察したが、より正確には:
- α は cid 集合の上位構造 (member 集合)
- β は cid 集合または α の **2 元結合** (ペア限定)

### 1.3 seed 0 詳細

| 軸 | seed 0 |
|---|---:|
| α birth events | 424 |
| α death events | 0 |
| β birth events | 239 |
| β death events | 0 |

→ seed 0 で α formation events 424 = 24 seeds 全体 13,881 ÷ 24 = 578 から離れているが、24 seeds で seed 別分散あり (要 §1.4 でカバー)。

### 1.4 48 cells 母集団推定

- formation_relation × n_core_bin × lifespan_q = 4 × 3 × 4 = **48 cells**
- 観察対象は (formation_event, member_cid, t_offset) の triplet

t_offset 1 step 刻み (200 samples/pair):
- 総 snapshots: (36,476 + 12,952) × 200 = **9,885,600 rows**
- per cell 均等仮定: 9.9M / 48 = ~206K snapshots/cell
- ただし formation_relation の 4 区分は t_offset から決まる (before<0 / after_0_100 / after_100plus / no_alpha) ので **n_core_bin × lifespan_q の 12 cells に時系列分解** が実態

t_offset 10 step 刻み (21 samples/pair、Code A 推奨案 b):
- 総 snapshots: 49,428 × 21 = **1,037,988 rows**
- 12 cells (n_core × lifespan_q) × 21 t_offset × ~412 events = 各 cell ~86,000 snapshots
- 評価可能性: 各 (cell, t_offset) で n ≥ 3 を確実に満たす

---

## §2 §9.3 計算量と storage 推定

### 2.1 観察解像度 3 案

| 案 | t_offset 解像度 | samples/pair | total rows | storage 推定 | 描画 |
|---|---|---:|---:|---:|---|
| a (完全) | 1 step (200) | 200 | 9,885,600 | 471 MB | 完全時系列 |
| **b (Code A 推奨)** | **10 step (21)** | **21** | **1,037,988** | **52 MB** | **減衰曲線描画可能** |
| c (区分のみ) | 4 区分集計 | 4 | 197,712 | 10 MB | 平均値のみ |

### 2.2 Code A 推奨: 案 b

理由:
1. **§0.2 達成条件 (応答性プロファイル描画)** には時系列が必要、4 区分集計だけでは描画不能
2. **storage 効率**: 1 step 刻みは 471 MB で大、10 step 刻みは 52 MB で実用的
3. **解像度十分**: 100 step 区間に 10 サンプルあれば減衰曲線の形は捕捉できる
4. **計算時間**: 9 倍の差は無視できない (24 並列でも 1 step 刻みは 30 分超のリスク)

### 2.3 累計 storage 推定 (案 b)

| Phase | サイズ |
|---|---:|
| v10.7-v10.10 main | 1.51 GB |
| **v10.11 main (案 b)** | **0.07 GB** (formation snapshots 52 MB + birth events 5 MB + cross_seed 10 MB) |
| **累計** | **1.58 GB / 上限 6 GB (26%)** |

→ 打ち切り閾値 50% (3 GB) に余裕大。

### 2.4 計算量推定 (案 b)

- 各 seed で formation events ~580 × member 平均 2 = ~1,160 (event, member) pairs
- 21 t_offset × 6 metric (delta_C / pulse / familiarity_edges 等) lookup
- v107 _build_state_lookups (C/pulse 等の merge_asof) 流用で per-seed 推定 30-60 秒
- 24 並列で **5-10 分**
- §0.3 打ち切り条件 3 (30 分超) には十分余裕

---

## §3 §9.1 機構実装の認識確認

### 3.1 alpha_birth / beta_birth source_event 化

#### 3.1.1 スキーマ提案

```python
formation_event_record = {
    "event_id": f"{seed}_alpha_birth_{i}",  # or beta_birth
    "event_source_type": "alpha_birth",     # or "beta_birth"
    "seed": int,
    "formation_id": int,                    # alpha_id / beta_id
    "timestamp": int,                       # = T (形成時刻)
    "n_members": int,                       # member 数 (α: 2-8、β: 2)
    "member_cids": str,                     # "cid1|cid2|..." 形式
}
```

→ v10.8 atom_introduction_event と互換 (event_source_type / event_id / seed / timestamp 共通)、加えて formation 固有の列 (formation_id / n_members / member_cids)。

#### 3.1.2 post-process 計算的減算規律との整合

v10.8 §30.2 「計算的減算」は **Q/C の変化を post-process で計算ベースで再現** することだった。

本主題では:
- formation event は **既に v10.5 ledger に記録済みの事実** (alpha_lifecycle_log を read のみ)
- v10.11 で書き込む新規データは **観察値の集計** (formation_response_profile.parquet 等)
- 実 Q/C 値は変更しない (read only)

→ 「計算的減算」というより「観察値の post-process 集計」。物理層 frozen 規律と完全整合。

### 3.2 観察対象 cid (Code A 提案)

主題 §2.2 では「対象 cid」と記述、Code A 提案で明確化:

**主観察対象**: formation event の member_cids
- 各 (event, member) について T-100〜T+100 を観察
- 主軸 metric: delta_C(t_offset) = C(T+t_offset) - C(T)
- 副軸 metric: pulse_count(t_offset) (T+t_offset から +1 step 内の pulse 数)、familiarity_edges_count(t_offset)

**no_alpha cid の扱い** (Code A 提案):
- 主題 §4.2 で formation_relation の 1 区分として no_alpha が定義
- ただし no_alpha cid は formation event を持たない → t_offset 軸が定義できない
- **Code A 提案**: no_alpha は **v10.10 既存 atom event 起点データ (formation_relation 列)** を引用、v10.11 では新規生成しない
  - v10.10 の formation_relation 観察は atom event timestamp と t_alpha_first の関係
  - v10.11 は formation event timestamp 起点 → 別フレーム
  - 両者は別観察、結合は v10.12 入力ルーティング設計時に行う

→ 主題 §1.5 留保 14 (no_alpha 群の v110_vs_v108re +0.133) への解明は本主題の射程外、留保継続として記録。

### 3.3 v107 オービス流用

主題 §2 で v107 オービスのパイプライン流用が予告されている。実態:

**流用するもの**:
- v107 `_build_state_lookups`: cid 別の R_familiarity / Q / C / n_alphas / n_observed の時系列 lookup
- これで delta_C(t_offset) を merge_asof で取得可能
- pulse 数も pulse_log から直接集計可能

**流用しないもの**:
- v107 `build_all_paths` / `build_baselines`: relation 軸は本主題の射程外 (formation event 自体を観察するので、target_cid に対する delta は不要)
- v107 `compute_baseline_excess_change`: baseline 比較は本主題で不要 (時系列観察が主軸)

→ v10.11 は **v107 lookup 機構の最小流用**、新規実装は formation event 起点の time-window snapshot のみ。

---

## §4 Code A 自主提案 4 件

### 提案 1: 観察解像度 = 案 b (t_offset 10 step 刻み)

§2.2 の主題射程を満たしつつ計算量・storage を実用範囲に収める。

### 提案 2: no_alpha は別フレーム

formation event 起点観察 (本主題) と atom event 起点観察 (v10.10 既存) は別フレーム。v10.11 では formation event 起点のみを新規実装、no_alpha 区分は v10.10 既存データを参照。

### 提案 3: event_id 形式

`{seed}_{alpha_or_beta}_birth_{i}` で一意化。v10.8 atom event の `{seed}_atom_{i}` 形式を継承。

### 提案 4: 観察 metric の優先度

主軸 (必須):
- delta_C(t_offset) = C(T+t_offset) - C(T)
- pulse_count(t_offset) (per-cid pulse 発火数、T+t_offset から +10 step ウィンドウ)

副軸 (時間あれば):
- familiarity_edges_count(t_offset)
- delta_R_familiarity(t_offset)
- delta_n_alphas(t_offset)

→ 主軸 2 つで応答性プロファイル描画、副軸は構造的解釈の補強用。

---

## §5 §9.4 規律遵守の認識確認

### 5.1 既存規律 (41 件、`09_audit_principles.md` §34) — 全遵守

- 物理層 frozen ✓ (実 ledger 不変、read のみ)
- 神の手回避 ✓ (formation event は v10.5 で既に発生済みの事実、観察のみ)
- Atom 326 絶対化禁止 ✓ (本主題は atom 軸を含まない、formation event 起点)
- 因果断定回避 ✓ (§3 ラベル規律で観察事実 / 整理仮説 / 未解明 を分離)
- post-process 計算的減算 ✓ (実 ledger 不変、新規データは観察値のみ)
- 出口の固定 ✓ (§0.2 達成条件、§6 完了判定)
- Code A 認識確認必須 ✓ (本書)
- 構造語と直感語の併記 ✓
- 各変動条件で baseline 再計算 ✓ (本主題では baseline 比較は不要、留保継承)
- 4 層階層化 ✓ (§4 Level 1-3.5+ で実装)
- 緩和 run 禁止 ✓
- n_core 別層化解析必須 (§34 #37) ✓ (条件軸 1)
- formation_relation を観察軸として含む (§34 #38) ✓ (主軸)
- 完全マージ版文書を出力 (§34 #39) ✓ (本書 + 完了報告で実施)
- 観察軸を増やす方が見えるものが増える (§34 #40) ✓ (ただし §0.3 打ち切り条件で運用)
- 観察状態判定枠を超えた整理 (§34 #41) — 必要に応じて適用

### 5.2 v10.11 新規規律 (運営メタ規律 8 項目、§35) — 全遵守

- 1: オープン/クローズ調査を固定方針にしない ✓
- 2: 追加調査の理由明示 ✓ (本書で母集団実測 = 平均化誤認回避)
- 3: 平均で潰れる構造は層化検討 ✓ (n_core_bin × lifespan_q × formation_relation で層化)
- 4: 閾値は運用上の仮置き ✓ (lifespan Q1-Q4 は v10.10 同分位、再調整可能)
- 5: 整理語と観察事実の分離 ✓ (§3 ラベル規律で実装)
- 6: 終了条件の前提が崩れたら再開 ✓
- 7: 監査は閉じる/開く両方の妥当性を評価 ✓
- 8: 最終的な開閉判断は人間 (Taka) ✓

### 5.3 §0.3 打ち切り条件の Code A 運用

| 打ち切り条件 | Code A の運用 |
|---|---|
| 1: 観察軸 3 軸超過要求 | Code A も Web Claude / Taka に上申 (Code A 独断で 4 軸目を追加しない) |
| 2: 構造的根拠解明不能 | Code A は観察事実のみ提示、「経験則として確定」は Web Claude / Taka 判断 |
| 3: 計算量予算超過 | Code A 自主判定で main run 中断、Taka に上申 (smoke 段階で察知すれば事前に提案) |

---

## §6 Web Claude / Taka への確認事項

### Q1: 観察解像度

提案: **案 b (t_offset 10 step 刻み、21 samples/event-member)** で OK か?

代替案 (Code A 試算値):
- 案 a (1 step、完全): storage 471 MB、計算時間 30 分超リスク
- 案 c (4 区分集計): 描画不能、応答性プロファイル仕様未達

### Q2: no_alpha の扱い

提案: no_alpha cid は **v10.10 既存データ (atom event 起点 formation_relation)** を引用、v10.11 では新規生成しない。

理由: formation event 起点と atom event 起点は別フレーム、本主題射程は formation event 起点。no_alpha 群の v10.10 留保 14 は本主題で扱わず継承。

### Q3: 観察 metric の優先度

提案: 主軸 2 つ (delta_C / pulse_count) を必須実装、副軸 3 つ (familiarity_edges / R_familiarity / n_alphas) は時間あれば追加。

### Q4: 機構実装の細部

提案:
- alpha_birth / beta_birth は v107 lookup 機構を最小流用
- formation event の ledger 整合 (alpha_lifecycle_log を read only) で物理層 frozen 維持
- post-process 計算的減算規律は「観察値の post-process 集計」として整合

### Q5: §0.3 打ち切り運用

確認: 計算量予算超過の早期察知 (smoke 段階で 5 分超ペースなら main run 30 分超見込み) は Code A 自主判定で進めて OK か?

---

## §7 進行手順

```
[現在] 本書 (Code A 認識確認) → Web Claude 応答 → Taka 承認
   ↓
[Code A] Step B: 環境チェック詳細
   - formation event 起点 snapshot 機構の seed 0 smoke 実装
   - 母集団 48 cells (n_core × lifespan × formation_relation) の events 数実測
   - delta_C / pulse_count の時系列取得動作確認
   - bit-identity 層 A 検証 (smoke レベル)
   ↓
[Code A] Step C: 実装 + smoke
   - v111_formation_event_generator.py (alpha_birth / beta_birth)
   - v111_response_profile_compiler.py (T-100〜T+100 snapshot)
   ↓
[Code A] Step D: smoke 結果報告 → main run 判定 (Taka 確認点)
   ↓
[Code A] Step E: 24 seeds main run
   ↓
[Code A] Step F: cross-seed 解析 + 4 階層 reports
   ↓
[Code A] Step G: 完了報告 + 4 種観察 (構造的事実 / 24 seeds 方向一致 / 効果量階層 / 留保更新)
   ↓
[Web Claude] 主題完了レポート + Phase 1.5 第六試行完了
```

---

## §8 一文サマリ (再掲)

v10.11 認識確認実施、母集団実測で **α formation 13,881 / β formation 6,476 events (24 seeds)、α は 2-8 member、β はペア限定** という構造的事実を確認、観察解像度は **Code A 推奨案 b (t_offset 10 step 刻み、storage 52 MB、計算時間 5-10 分)** を提案、累計 storage 1.58 GB (26%) で打切閾値 50% に余裕大、機構実装は v107 lookup 機構の最小流用で物理層 frozen 維持、Code A 自主提案 4 件 (解像度 b / no_alpha 別フレーム / event_id 形式 / metric 優先度) + 確認事項 5 件、規律 41 件 + 新規 8 項目 全遵守、§0.3 打ち切り条件 3 件は Code A も上申義務、Web Claude / Taka 応答後 Step B (環境チェック詳細 → smoke) → Step E (main run) → Step G (完了報告) の順で進む。

---

*以上、Code A による v10.11 認識確認質問書。Web Claude `v111_response_to_code_a.md` 応答 + Taka 承認後、Step B 着手。*
