# v1104 Step H-2 認識確認 — 観察 2 再調査指示への Code A 実環境照合

*作成*: 2026-05-23、Code A
*親*: `v1104_observation_2_reinvestigation_directive.md` (Web Claude 再調査指示、2026-05-23) + `v1104_step_h_observation_final.md`
*対象*: Web Claude (相談役、Genesis 側) + Taka (再調査着手判断)
*目的*: 再調査指示書 §4 確認要請 3 件への Code A 実環境照合 + 仮所見。

---

## 0. 一文サマリ

v1104 観察 2 再調査指示書 §4 確認要請 3 件への Code A 実環境照合: **§4.1 CID scope の n_members_bin** は (i)(ii)(iii) の 3 候補を確認し Code A 仮所見 **(iii) cid 単独の n_core_member** (観察 1 と同軸、cid 自体の構造的属性、対称性確保) を推奨、**§4.2 shuffle baseline 現状実装** は `rng.permutation(cid_seq_to)` で attention_candidate_id を chain 内で順序入れ替え = **shuffle 種別 A (chain 内 permutation) 相当** と確認、**§4.3 v10.6 event 解像度** は `developmental/v106/outputs/main/event_trajectory/event_cid_alignment_seed{N}.csv` 24 seeds 揃い (seed 0: 15,687 rows / 228 unique cid / t 範囲 0-24998)、pulse_trajectory / step10_trajectory / window_trajectory も同同形式で揃い、cols は (seed, cognitive_id, t, source, window, lifespan_so_far, n_core_member, C/Q_at_window_end, R_familiarity, cumulative_n_*, rank_1_atom, rank_1_sim, top_category) — 再調査 3 chain 粒度の入力として step10/event 両方使用可、確認要請 3 件すべてに実環境照合済で着手前提整い、再調査実装 4 件 (層化 + shuffle 3 種 + 解像度 3 階層 + self-loop 分離) は既存出力流用のみ・新規 main run なし・想定 3-4 日 (再調査指示書 §5 と整合)、書込み unified/v1104/outputs/main/ 配下のみ。

---

## 1. 確認要請 1 — CID scope の n_members_bin 引き方 (§4.1)

### 1.1 3 候補の構造的特性

| 候補 | 内容 | 観察 1 との対称性 | データ源 |
|---|---|---|---|
| (i) | cid → 所属する全 alpha/beta の n_members の中央値 | 弱 (alpha/beta 集計後) | alpha_lifecycle_log + beta_distribution_log から cid→alpha map |
| (ii) | cid → 所属する最大 Integration の n_members | 弱 (最大に依存) | 同上 |
| **(iii)** | **cid 単独の n_core_member (ESDE Genesis 由来)** | **強 (観察 1 と同軸)** | v10.6 window_trajectory `n_core_member` 列 |

### 1.2 実環境確認 (seed 0)

CID scope に該当する cid の n_core_member 分布:
- n=2: 90 cid (67%)
- n=3: 9 cid (7%)
- n=4: 15 cid (11%)
- n=5: 21 cid (16%)

(Step A §1.1.4 で 24 seeds 全体は n=2 62.6% / n=5 20.1% と確認済)

### 1.3 Code A 仮所見: (iii) を採用

理由:
- **観察 1 と完全同軸**: 観察 1 で「n_members 増で match_k1 単調低下」を観察した同じ軸で観察 2 を層化することで、観察 1/2 の対称性確保 (絶対格言 #11 概念単位を雑に扱わない)
- **cid 自体の構造的属性**: n_core_member は ESDE Genesis 由来、cid 形成時の構成 cid 数。CID scope の chain は cid 単独の動きを見るので cid 自体の属性で層化するのが自然
- **(i)(ii) の Integration 側都合の混入回避**: cid が複数 alpha に所属する場合 (cid_id × alpha_id 多対多) では中央値/最大値が「どの Integration を取るかで変わる」、CID scope の純粋な観察を阻害

実装: 観察 2 の CID scope 各 chain について、`v10.6 window_trajectory_seed{N}.csv` の `n_core_member` 列を join (Step A で確認済の手順)。

---

## 2. 確認要請 2 — shuffle baseline 現状実装の単位 (§4.2)

### 2.1 現状実装の確認 (`v1104_step_c_observation_2.py`)

```python
baseline_sims = []
for _ in range(N_SHUFFLE):
    shuffled = rng.permutation(cid_seq_to)
    ss = []
    for cf, ct in zip(cid_seq_from, shuffled):
        s = cid_sim(int(cf), int(ct))
        ...
```

- `cid_seq_to` = chain 内の attention_candidate_id 列 (per (scope, scope_id, metric_type))
- `rng.permutation(cid_seq_to)` で chain 内の cid 順を入れ替え
- predecessor 側 (`cid_seq_from`) は保持

→ **shuffle 種別 A (chain 内 permutation) 相当**。chain 構造 (長さ、cid 集合) は保ち、順序のみ shuffle。

### 2.2 含意

現状実装の lift=0 は「chain 内で cid 順を入れ替えても sim が同じ」= chain 内 cid 集合の sim が全 cid で均質、と解釈できる。

- chain 内 cid 集合が同じ cid を多数含む (self-loop 85% より) → 順序入れ替えても sim 値変わらず
- chain 内 cid 集合の sim が cid_atom_sim_matrix で平らに分布 → 順序入れ替えても shuffle と区別不能

→ shuffle B (chain 間) / C (global pool) を追加することで、chain 構造そのものに意味があるか / sim_matrix 全体が平らか を切り分けできる。

### 2.3 再調査 2 で実装する 3 種

| 種別 | permutation 単位 | 保たれる構造 | 壊される構造 |
|---|---|---|---|
| **A (現状)** | chain 内 cid 順 | chain 構造 + cid 集合 | chain 内順序 |
| **B (新規)** | chain 間 cid (同 scope, seed 内) | chain 構造 | chain 内 cid 集合 + 順序 |
| **C (新規)** | global cid pool (同 scope, seed 内) | なし | すべて (chain 構造完全無視) |

実装: 再調査 2 のスクリプトで 3 種を並列出力。

---

## 3. 確認要請 3 — v10.6 event 解像度の所在 (§4.3)

### 3.1 実環境確認

`developmental/v106/outputs/main/` 配下のディレクトリ構造:
- `event_trajectory/` (event 解像度)
- `pulse_trajectory/` (pulse 解像度)
- `step10_trajectory/` (step10 解像度)
- `window_trajectory/` (window 解像度、現状の観察 2 で使用)

各 trajectory は `*_cid_alignment_seed{N}.csv` で 24 seeds 揃い (smoke 版あり、main 版を使用)。

### 3.2 event_cid_alignment_seed0.csv の構造

- rows: 15,687 / unique cognitive_id: 228 / t 範囲: 0-24998
- cols: seed, cognitive_id, t, source, window, lifespan_so_far, n_core_member, C_at_window_end, Q_remaining_at_window_end, R_familiarity, cumulative_n_ingestions, cumulative_n_alphas, cumulative_n_betas, **rank_1_atom**, rank_1_sim, top_category

→ 再調査 3 で必要な列 (`t`、`rank_1_atom`、`n_core_member`) すべて揃う。

### 3.3 再調査 3 で使用する 3 階層

| 解像度 | 入力ファイル | per-seed rows (seed 0) | chain 構築方針 |
|---|---|---:|---|
| **window** (現状) | window_cid_alignment_seed{N}.csv | (already counted via attention_emit) | 既存の連続 conscious window |
| **step10** (新規) | step10_trajectory/step10_cid_alignment_seed{N}.csv | (要確認、推定数千) | 同じ conscious 区間を step10 単位で展開 |
| **event** (新規) | event_trajectory/event_cid_alignment_seed{N}.csv | 15,687 | event 単位 (各 cid 形成・更新・ghost 化) で chain |

実装: 再調査 3 のスクリプトで attention_emit の意識優位 window を起点に、各解像度の trajectory を join して chain を再構築。

### 3.4 step10/event 解像度の chain 数増加見積

- window 解像度: 39,537 chains (現状)
- step10 解像度: window が約 1 windows = 500 steps を 10 step 単位に分割 → chain 数 ~50 倍? or chain length ~50 倍?
- event 解像度: per-seed 15,687 rows = window あたり ~313 events、chain length が約 300 倍?

→ 計算量増加が大きい場合は per-seed shuffle N=50 を維持しつつ chain 数を絞る (代表 chain サンプル) などの調整要。実装段階で判断。

---

## 4. 再調査着手前の整理

### 4.1 §4 確認要請 3 件の Code A 仮所見まとめ

| § | 内容 | Code A 仮所見 |
|---|---|---|
| 4.1 | CID scope の n_members_bin 引き方 | **(iii) cid 単独の n_core_member** (観察 1 と同軸、対称性確保) |
| 4.2 | shuffle baseline 現状実装単位 | **shuffle 種別 A (chain 内 permutation) 相当**、再調査 2 で B/C 追加 |
| 4.3 | v10.6 event 解像度の所在 | `event_trajectory/event_cid_alignment_seed{N}.csv` 24 seeds 揃い、列・cid 数確認済 |

### 4.2 再調査 4 件の実装順序 (指示書 §5 進行表に従う)

1. **再調査 1 (層化)** — 既存 `observation_2_predecessor_chain.parquet` + Step G composition + n_core_member を join するだけ、半日想定
2. **再調査 2 (shuffle 3 種)** — Step C のコア処理を 3 通り実装、計算量は shuffle A の 3 倍 = 約 3 分、半日想定
3. **再調査 3 (粒度 3 階層)** — event 解像度で chain 再構築 + sim 計算、計算量大きい可能性あり、1 日想定
4. **再調査 4 (self-loop 分離)** — 既存 chain を is_self_loop で分割して per-bin lift、半日想定

### 4.3 規律遵守確認

- 物理層 frozen: 書込み `unified/v1104/outputs/main/` 配下のみ、v10.x / v1101a / v1102 / v1103 read-only
- 判定語制限: 「連想」と判定しない、cid/atom/category/sim 推移の構造事実のみ記録 (GPT 追加 4 継承)
- selector 化禁止: 本再調査は観察 2 のみ、観察 4 (B 現状) に触れない (GPT 修正必須 C 継承)
- 効果サイズ: |lift| > 0.01 を有意閾値 (絶対格言 #3)
- 層化必須: 再調査 1 が本書中核 (絶対格言 #4)
- 既存出力流用のみ: 新規 main run 禁止 (絶対格言 #5)

---

## 5. 進行 — Step H-2 完了後

| Step | 内容 | 担当 | 待機 |
|---|---|---|---|
| Step H-2 (本書) | 認識確認 + 仮所見 | Code A | 完了 |
| Step H-2 反映 | §4 確認要請 3 件への Web Claude / Taka 回答 | Web Claude / Taka | — |
| Step H-3 実装 1-4 | 再調査 4 件 (層化 / shuffle 3 種 / 粒度 3 階層 / self-loop 分離) | Code A | §4 確定後 |
| Step H-3 グラフ | dashboard 拡張 | Code A | 実装後 |
| Step H-3 bit-identity | 再調査出力の verification 拡張 | Code A | グラフ後 |
| Step H-3 観察事実報告 | judgment 回避、4 パターン (α/β/γ/δ) のどれかを記録 | Code A | bit-identity 後 |
| Step I Phase Result | Web Claude 解釈統合 | Web Claude | 観察事実報告後 |

想定合計 3-4 日。

---

## 6. 一文サマリ (再掲)

v1104 観察 2 再調査指示書 §4 確認要請 3 件への Code A 実環境照合: §4.1 CID scope n_members_bin は **(iii) n_core_member** (観察 1 と同軸、cid 自体の属性、対称性確保) を推奨、§4.2 shuffle baseline 現状実装は **chain 内 permutation (種別 A)** で確認済 (再調査 2 で B chain 間 + C global pool を追加)、§4.3 event 解像度は **`event_trajectory/event_cid_alignment_seed{N}.csv`** 24 seeds 揃いで 15,687 rows / seed (window 解像度は 1,062 rows / seed の約 15 倍)、step10/event 両方利用可、再調査 4 件着手前提整い、規律 (物理層 frozen + 判定語制限 + selector 化禁止 + 効果サイズ |lift|>0.01 + 層化必須 + 既存出力流用) 堅持、想定 3-4 日、Web Claude / Taka §4 確定後に Step H-3 実装 1-4 着手可。

---

*以上、v1104 Step H-2 認識確認 (Code A、2026-05-23)。§4 確認要請 3 件への Web Claude / Taka 回答後、Step H-3 再調査実装に着手。*
