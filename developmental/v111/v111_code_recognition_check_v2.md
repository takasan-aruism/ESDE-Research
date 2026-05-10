# v10.11 Code A 再認識確認応答書 (第二稿ベース) — Q1-Q10 全件回答

*作成*: 2026-05-10、Code A
*親*: `v111_code_recognition_re_request.md` (Web Claude 再認識確認依頼、2026-05-10) + `v111_phase_design.md` 第二稿
*対象*: Web Claude (主題ドキュメント第三稿への素材) / Taka (承認)
*目的*: 第一稿認識確認の無効化を受け、第二稿ベースで Q1-Q10 に応答、観察軸選定を Code A 技術判断で確定

---

## 0. 一文サマリ

第一稿認識確認の無効化を受け第二稿ベースで Q1-Q10 を実測ベースで応答、技術判断による観察軸選定として **主軸 = 候補 A (q_c_inherited 前後の delta_C)、条件軸 = n_core_bin × β 累積 c_inherited 分位 (3×4=12 cells)** を提案、選定根拠は (1) 仮説 2 (C 値飽和) の **直接検証** が可能 (累積 c_inherited と delta_C 応答の相関を数値化)、(2) 母集団十分 (24 seeds 合計 2,247 events / 13,055 (event, member_cid) pairs)、(3) 1 β あたり mean 2.04 回 max 59 回の累積構造が明確、(4) c_inherited_total 分位が Q25=3 / Q50=6 / Q75=9 / Q90=17 と明確、(5) member_cids 直接記録で post-process 取得容易、観察対象 cid は q_c_inherited を受けた cid のみ (within-cid design で control 不要)、観察 metric 主軸 (delta_C / pulse_count) 必須、副軸は計算量で自主判定、計算量推定 main run 3-5 分 / storage 累計 1.53 GB (26%)、規律 41 件 + §35 メタ規律 全遵守、§0.3 打ち切り条件 3 件は Code A も上申義務、Web Claude / Taka 応答 + 主題ドキュメント第三稿 → Step B 着手 → Step E main run → Step G 完了報告 → Phase 1.5 第六試行完了 の順で進む。

---

## §1 Q1: 主軸候補の選定 — Code A 推奨「候補 A (q_c_inherited)」

### 1.1 候補別実測値 (24 seeds 合計、Code A 自主実測)

| 候補 | events | member_cid 取得性 | 累積構造 | 主題核心検証 |
|---|---:|---|---|---|
| **A: q_c_inherited** | **2,247 / 13,055 pairs** | **直接記録** | mean 2.04, **max 59 回 / β** | 仮説 2 (C 値飽和) **直接検証可** |
| B: alpha_added | 7,405 | **NaN (member_alphas のみ、間接取得)** | β 規模軸 | 間接 |
| C: β 規模 | 6,476 β | β 別の時間追跡が複雑 | 連続軸 | 観察設計コスト大 |
| D: beta_merged | 4,467 | merged_from_beta_X 形式 (cid 直接でない) | merge 構造 | 観察対象変換困難 |
| E: member_ghosted | 17,093 / 24,584 | 直接記録 | - | 仮説 3 (状態固定化) 検証 (主題と別軸) |

### 1.2 候補 A 推奨理由

#### 理由 1: 仮説 2 (C 値飽和) の直接検証

主題ドキュメント §1.3 で示唆された「C 値飽和」仮説の核心は **「C 値が累積で天井に達するか」**。q_c_inherited event は β からの C 継承を直接記録 (q_inherited_delta / c_inherited_delta) しているため、c_inherited 累積と delta_C 応答の相関を数値で観察可能。

具体的に:
- 累積 c_inherited が Q1 (<3) の cid: delta_C 応答が大か
- 累積 c_inherited が Q4 (≥10) の cid: delta_C 応答が消失するか

→ 仮説 2 の **数値ベース検証** が可能。これは他候補 (B/E) では実現困難。

#### 理由 2: 母集団確保

候補 A は 24 seeds で 13,055 (event, cid) pairs。条件軸 12 cells で割っても 1 cell ~1,000 events、per atom×seed で評価可能 (n_b ≥ 3 余裕大)。

#### 理由 3: 累積構造の観察意義

1 β が max 59 回 q_c_inherited を受ける構造は v10.10 では未観察、v10.11 で初めて捕捉できる時間発展軸。

c_inherited_total 分位 (24 seeds 集計):

| 分位 | c_inherited_total |
|---|---:|
| Q25 | 3 |
| Q50 | 6 |
| Q75 | 9 |
| Q90 | 17 |
| max | 121 |

→ 明確な分位構造、累積効果の段階観察が可能。

#### 理由 4: 計算量と post-process 取得容易性

q_c_inherited の member_cids は直接記録 (NaN なし)、c_inherited_delta も直接記録。post-process 集計で merge_asof のみ、計算量低。

#### 理由 5: v10.12 入力ルーティング条件抽出

達成条件 (§0.2): v10.12 で「狙う cid」を判定する基準 1 本以上抽出。

候補 A から抽出可能な条件例:
- 「累積 c_inherited が N 以上の cid は delta_C 応答消失で入力対象から除外」
- 「累積 c_inherited が N 未満かつ n_core=5+ の cid は delta_C 応答大で入力対象として優先」

→ v10.12 入力ルーティング設計に **直接活用可能** な条件抽出が見込める。

### 1.3 候補 A の構造的限界 (留保事項)

- 候補 A は β に組み込まれた cid のみを観察対象とする。Integration 形成しない cid (no_alpha) は観察対象外
- 1 cid が複数 β に組み込まれる場合、累積効果の分解が複雑化 (実装上は β 単位の累積を採用、留保 §4 §4.3 参照)

---

## §2 Q2: 条件軸 2 つの選定 — Code A 推奨

### 2.1 推奨条件軸

| 条件軸 | 区分 | 選定理由 |
|---|---|---|
| **n_core_bin** | bin_2 / bin_3_4 / bin_5+ | 規律 §34 #37 (n_core 別層化必須)、v10.10 で確定的観察、規律遵守 |
| **β 累積 c_inherited 分位** | Q1 (<3) / Q2 (3-6) / Q3 (6-9) / Q4 (≥10) | 主軸 A の **核心軸** (累積効果の段階観察)、新規軸 |

→ 計 3 × 4 = **12 cells**、各 cell ~1,000 events で評価可能。

### 2.2 落選軸の理由

| 候補 | 落選理由 |
|---|---|
| 寿命分位 | v10.10 で観察済み、本主題の核心 (C 飽和) からは派生軸 |
| β 規模分位 | 主軸 A の累積 c_inherited 分位と高相関 (β が大きいほど受け取る回数増)、軸独立性低 |
| formation_relation | v10.10 主軸、本主題で q_c_inherited 起点で時間軸を取り直す必要があり計算量増 |
| atom category | 規律 §34 で除外/低優先 (v10.10 で 1 桁差観察も atom 種類依存性が解像度限界) |

### 2.3 v10.10 観察との連続性

- n_core_bin: v10.10 第一弾と完全に同じ区分、連続性あり
- β 累積 c_inherited 分位: v10.10 では未観察、v10.11 新規軸

→ 1 軸は連続性 (規律遵守)、もう 1 軸は新規 (本主題の核心)。

---

## §3 Q3: 観察対象 cid の絞り込み

### 3.1 推奨: (b) 主軸 event を経験した cid のみ

q_c_inherited を受けた cid のみを観察対象とする:
- 13,055 (event, member_cid) pairs (24 seeds)
- unique cid 数 (要追加実測): 約 5,000-10,000 cid (推定、1 cid が複数 q_c_inherited を受ける)

### 3.2 within-cid design (control 不要)

各 cid について q_c_inherited 直前 (T-50) と直後 (T+50) の delta_C を比較する **within-cid design** を採用。
- 利点 1: control 群不要 (同一 cid 内で前後比較)
- 利点 2: cid 間の構造的差を排除
- 利点 3: 累積効果を段階的に観察可能 (1 cid が複数回受ける場合、各回で前後比較)

→ v10.10 の v110_vs_v108re 比較フレームと異なる、本主題に最適な比較設計。

### 3.3 留保事項

- no_alpha cid (Integration 形成しない cid) は本主題の射程外
- v10.10 留保 14 (no_alpha 群の +0.133) は本主題で扱わず継承

---

## §4 Q4-Q6: 機構実装の認識確認

### 4.1 Q4: v10.7 既存 source_event の活用方針

#### 4.1.1 確認

第一稿の「alpha_birth / beta_birth 新規追加」は撤回。第二稿では:
- v10.7 既存の alpha_formation / beta_formation source_event を **read のみ**
- 新観察 event_type (q_c_inherited 等) は alpha/beta_lifecycle_log を read のみ
- ledger 改変なし、物理層 frozen 維持

#### 4.1.2 実装方針

```python
# v111_q_c_inherited_observer.py (新規)
def observe_q_c_inherited_seed(seed):
    # 1. beta_lifecycle_log から q_c_inherited events を抽出
    b = pd.read_csv(DIAG / f'integration/beta_lifecycle_log_seed{seed}.csv')
    qci = b[b['event_type']=='q_c_inherited']
    
    # 2. 各 event について member_cids を取得
    # 3. 各 (event, cid) について t_offset = -50, -40, ..., +50 で C 値・pulse 数取得
    # 4. v107 _build_state_lookups の C lookup を流用
    
    # 5. 出力: snapshot DataFrame
```

### 4.2 Q5: post-process 計算的減算規律解釈拡張 — 同意

第一稿 §5.1 で確認済みの「観察値の post-process 集計」として整合。本主題でも同方針。

実 ledger は read only、書き込みは v111/ 配下の観察値 parquet のみ。

### 4.3 Q6: 観察 metric 優先度

#### 4.3.1 主軸 metric (必須)

- **delta_C(t_offset)**: q_c_inherited event T を起点とした C 変化、t_offset = -50 〜 +50 step (5 step 刻みなら 21 samples)
- **pulse_count(t_offset)**: T+t_offset から +5 step ウィンドウ内の pulse 発火数

#### 4.3.2 副軸 metric (時間あれば)

- familiarity_edges_count(t_offset)
- delta_R_familiarity(t_offset)
- delta_n_alphas(t_offset)
- β 内の累積 c_inherited 値の時系列

#### 4.3.3 計算量超過時の自主判定

§0.3 打ち切り条件 3 (計算量超過) に近づく場合、Code A 自主判定で副軸 metric を省略 → 主軸 2 つのみで完了報告。

### 4.4 観察解像度の選定

第一稿で提案した 3 案を本主題に適用:

| 案 | t_offset 解像度 | samples | total snapshots | storage |
|---|---|---:|---:|---:|
| a | 1 step (101) | 101 | 1.32M | ~65 MB |
| **b (Code A 推奨)** | **5 step (21)** | **21** | **274K** | **~14 MB** |
| c | 4 区分集計 | 4 | 52K | 3 MB |

→ **Code A 推奨**: 案 b (t_offset 5 step 刻み、±50 step 範囲)。第一稿は ±100 step だったが、c_inherited 累積効果は短期的応答が主と推定、±50 step で十分。

---

## §5 Q7-Q8: 計算量と storage 推定

### 5.1 main run 推定 (案 b)

| 区分 | 推定 |
|---|---:|
| q_c_inherited events 24 seeds | 2,247 |
| (event, member_cid) pairs | 13,055 |
| × t_offset 21 samples | 274,155 snapshots |
| per-seed 推定計算時間 | 30-60 秒 |
| 24 並列 main run 推定 | **3-5 分** |

→ §0.3 打ち切り条件 3 (30 分超) に **十分余裕**。

### 5.2 storage 推定

| 区分 | サイズ |
|---|---:|
| q_c_inherited_response_profile (24 seeds) | ~14 MB |
| q_c_inherited_events_seed*.parquet | ~3 MB |
| cross_seed 集計 | ~10 MB |
| **v10.11 main 合計** | **~27 MB** |

累計:
- v10.7-v10.10 main: 1.51 GB
- v10.11 main 推定: 0.027 GB
- **累計 1.54 GB / 上限 6 GB (26%)**

→ §0.3 打ち切り条件 3 (累計 3 GB) に **大幅余裕**。

---

## §6 Q9: 規律遵守の認識確認

### 6.1 既存規律 (41 件、§34) — 全遵守

- 物理層 frozen ✓ (read only)
- 神の手回避 ✓ (実 ledger 不変)
- Atom 326 絶対化禁止 ✓ (本主題は atom 軸を含まない)
- 因果断定回避 ✓ (主題 §3 ラベル規律で実装)
- post-process 計算的減算 ✓ (観察値集計として整合)
- Code A 認識確認必須 ✓ (本書)
- 4 層階層化 ✓ (主題 §4 で実装)
- 緩和 run 禁止 ✓ (実装変更なし)
- **n_core 別層化解析必須** (#37) ✓ (条件軸 1)
- **完全マージ版文書を出力** (#39) ✓ (本書)

### 6.2 §35 運営メタ規律 + 自己反省 — 全遵守

- 規律 2 (追加調査の理由明示) ✓ (§1.2 で候補 A 選定理由を明示)
- 規律 5 (整理語と観察事実の分離) ✓ (主題 §3 ラベル規律実装)
- 規律 9 (主題着手前に上位資料を読む) ✓ (Code A 事実確認 + Web Claude 第二稿で v10.5 実装把握済み)
- 規律 10 (「観察できる軸が見えた」を駆動要因にしない) ✓ (達成条件 §0.2 = v10.12 入力ルーティング条件 1 本抽出を駆動要因として固定)

---

## §7 Q10: §0.3 打ち切り条件の Code A 運用

| 打ち切り条件 | Code A の運用方針 |
|---|---|
| 1: 観察軸 3 軸超過要求 | Code A も Web Claude / Taka に上申、独断で 4 軸目を追加しない |
| 2: 構造的根拠解明不能 | Code A は観察事実のみ提示、「経験則として確定」は Web Claude / Taka 判断 |
| 3: 計算量予算超過 | smoke 段階で 1 分超ペース → main run 30 分超見込みで上申 (推定 3-5 分なので余裕大、ただし監視継続) |

---

## §8 Code A 自主提案の整理

| # | 提案 | 反映先 |
|---|---|---|
| 1 | 主軸 = 候補 A (q_c_inherited) | §1 |
| 2 | 条件軸 = n_core_bin × β 累積 c_inherited 分位 | §2 |
| 3 | 観察対象 = q_c_inherited を受けた cid (within-cid design) | §3 |
| 4 | 観察解像度 = 案 b (t_offset 5 step 刻み、±50 step) | §4.4 |
| 5 | 主軸 metric (delta_C / pulse_count) 必須、副軸は時間で自主判定 | §4.3 |
| 6 | β 累積 c_inherited 分位は β 単位 (member 全員に同じ累積を割り当て) | §3 |
| 7 | 計算量超過時の主軸絞り込み自主判定 | §4.3.3 |

---

## §9 Web Claude / Taka への確認事項

### Q-C1: 主軸 候補 A 採用で OK か?

Code A 推奨は候補 A。代替候補 (B/C/D/E) を選択する場合、再検討が必要。

### Q-C2: 条件軸 (n_core_bin × β 累積 c_inherited 分位) で OK か?

3 × 4 = 12 cells、規律 §34 #37 (n_core 必須) を遵守、本主題の核心軸 (累積) を含む。

### Q-C3: within-cid design (control 不要) で OK か?

各 cid 内で q_c_inherited 直前/直後の delta_C 比較。control 群不要、主題核心 (C 飽和) を直接検証。

### Q-C4: 観察解像度 案 b (5 step 刻み、±50 step、21 samples) で OK か?

第一稿 ±100 step より短縮 (±50)、解像度は維持 (1 step → 5 step)。total 274K snapshots、storage 14 MB。

### Q-C5: §0.3 打ち切り条件運用 (Code A 自主判定 with 上申) で OK か?

smoke 段階で計算量超過予兆を察知すれば自主判定で上申、Web Claude / Taka 判断で対応 (主軸絞り込み or 主題見直し)。

---

## §10 進行手順

```
[現在] 本書 (Code A 再認識確認応答) → Web Claude 応答 + 主題ドキュメント第三稿 → Taka 承認
   ↓
[Code A] Step B: 環境チェック詳細 (q_c_inherited 観察機構の seed 0 smoke 実装、母集団 12 cells 実測、bit-identity 層 A 検証)
   ↓
[Code A] Step C: 実装 + smoke
   - v111_q_c_inherited_observer.py
   - v111_response_profile_compiler.py
   ↓
[Code A] Step D: smoke 結果報告 (Web Claude / Taka 確認点)
   ↓
[Code A] Step E: 24 seeds main run (推定 3-5 分)
   ↓
[Code A] Step F: cross-seed 解析 + 4 階層 reports
   ↓
[Code A] Step G: 完了報告 + 4 種観察 + v10.12 入力ルーティング条件 1 本抽出
   ↓
[Web Claude] 主題完了レポート + Phase 1.5 第六試行完了
```

---

## §11 一文サマリ (再掲)

第二稿ベースで Q1-Q10 を実測ベース応答、技術判断による観察軸選定として **主軸 = 候補 A (q_c_inherited 前後の delta_C)、条件軸 = n_core_bin × β 累積 c_inherited 分位 (3×4=12 cells)、観察対象 = q_c_inherited を受けた cid (within-cid design)、観察解像度 = 案 b (t_offset 5 step 刻み±50 step、21 samples、total 274K snapshots)** を提案、選定根拠は (1) 仮説 2 (C 値飽和) の直接検証、(2) 母集団 13,055 pairs / 24 seeds、(3) max 59 回 / β の累積構造、(4) c_inherited Q25=3 / Q50=6 / Q75=9 / Q90=17 の明確な分位、(5) member_cids 直接記録で post-process 取得容易、計算量推定 main run **3-5 分** / storage 累計 **1.54 GB (26%)**、規律 41 件 + §35 メタ規律 全遵守、§0.3 打ち切り条件は Code A 自主判定 with 上申、Web Claude / Taka 応答 + 主題ドキュメント第三稿 → Step B 着手 → main run → Step G 完了報告 (v10.12 入力ルーティング条件 1 本抽出) → Phase 1.5 第六試行完了 の順で進む。

---

*以上、Code A による v10.11 再認識確認応答 (第二稿ベース)。Web Claude `v111_response_to_code_a.md` 応答 + 主題ドキュメント第三稿 + Taka 承認後、Step B 着手。*
