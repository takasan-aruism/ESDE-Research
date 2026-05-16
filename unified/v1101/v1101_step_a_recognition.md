# v11.0.1 (v1101) Step A 認識確認 — Code A 事前齟齬指摘 + 既存出力照会結果

*作成*: 2026-05-16、Code A
*番号修正*: 2026-05-17、旧 v11.0.2 (v1102) から v11.0.1 (v1101) へ番号修正 (Taka 判断、v1100 系列内の話としての位置づけ確定、bookkeeping fix)
*親*: `v1101_phase_design.md` (主題ドキュメント「Atom 的隆盛の統計的観察」、Web Claude 2026-05-16 改訂版、旧 v1102_phase_design.md)
*対象*: Web Claude (相談役、即決事項返答済 2026-05-16) + Taka (承認済 2026-05-17)
*目的*: 本書読了 + 論点 1 実環境データ可用性確認 + 事前齟齬指摘 (本書 §0.1 指示 + Web Claude 認識確認連続継続)

---

## 0.0 番号修正 + 即決事項返答受領 (2026-05-17 追記)

本書は当初 v11.0.2 (v1102) として作成され `unified/v1102/v1102_step_a_recognition.md` に配置された。Taka 判断 (2026-05-17) で v11.0.1 (v1101) へ番号修正、`unified/v1101/v1101_step_a_recognition.md` へ git mv 済。理由: 主題ごとにバージョンを繰り上げたのが誤りで、本主題は v1100 系列内の話、v1100 Phase Result は未完成のまま並列扱い。

Web Claude 即決事項返答 (2026-05-16) で本書齟齬 10 件全てに判断確定:
- A (親資料) / D (Integration 集約) / E (時系列 trajectory) / F (確定値 vs 揺れ) / G (Integration α/β) / H (atom 集合) / I (出口物領域) / J (新規 main run): **採用** (本書記述通り処理)
- B (空白表現): 「観察フレームの空白」に訂正、採用
- C (v1100 残課題 A/B/C): **凍結** (棄却ではない、v11.0.1.a / v11.0.2 で扱う可能性残す)

Taka 追加判断 (2026-05-17):
- 観察 1「一点」: (c) n_pulses_short 最大 cid 主 + (d) ランダム比較対照
- 観察 2「中心」: (a) v10.12 受容 cid pool 420 中心
- 観察 1/2 の (b) atom 濃度近接 cid: **不採用**
- 旧 v1101 (AI の限界記録): repo 未存在で正しい、Code A は探さない

→ 本書の以下記述は番号修正後も齟齬指摘内容は **歴史的記録として保持** (本書発見時点の事実)。Web Claude 改訂版 v1101_phase_design.md (§2.2 / §3.1 / §4) が反映済みのため、Step B 以降は改訂版を参照する。

---

## 0. 一文サマリ

実環境調査で **10 件の事前齟齬を発見**、特に重大なのは:
- **齟齬 A (重大)**: 本書冒頭で「親」と記載された `v1100_phase_result.md` と `v1101_phase_design.md` は **どちらも存在しない** (v1100 は Code A Step J `v1100_observation.md` のみ存在、Web Claude Step K Phase Result 未作成、v1101 は完全未着手)、本書は v1100 提案の v1101 候補 A/B/C (候補 5 層化 / 候補 3 概念再定義 / 候補 6 大規模化) + v1100 新規留保 #36/#37 candidate を一切継承せず別主題へ完全 pivot
- **齟齬 D (重大)**: 本書 §2.3 「Integration を atom 濃度分布として見る観察は v10.x で実施されていない」は **事実誤認**、v10.6 main outputs に `beta_atom_aggregate_seed{N}.csv` (per-β-Integration の top_atom + top5_atoms + max_atom_sim) と `alpha_atom_aggregate_stratified_seed{N}.csv` (per-α-pattern_class の dominant_atom + top5_atoms) が **24 seeds 揃って存在**、本主題の新規貢献は「top-K 集約 → 完全分布」の解像度向上であって「未実施 → 新規実施」ではない
- **齟齬 E (重大)**: 本書 §3.1 論点 1 (時系列をどう得るか) の 3 案 (a 静的 / b cid vector 再計算 / c v10.13.a 5 phase 波及代理) は **既存の時系列出力を見落としている**、v10.6 main outputs に `event_cid_alignment_seed{N}.csv` (per-cid per-t の rank_1_atom + rank_1_sim、seed 0 で 15,687 行) + `pulse_trajectory` + `step10_trajectory` + `window_trajectory` の **4 解像度時系列出力が既存**、案 d (既存 trajectory 流用) を追加すべき

その他、齟齬 B (v10.8 = Atom 取り込みは正しいが v10.9-v10.13.a の具体観察省略過多)、齟齬 C (v1100 残課題完全欠落)、齟齬 F (§3.1 濃度確定値 vs §3.3 揺れの不整合)、齟齬 G (Integration の seed 横断 / per-seed 選択不明)、齟齬 H (atom 集合の定義不明: 326 全部 / 25 TARGET / 上位)、齟齬 I (出口物 #5「Atom 的にこうなっているようだ」の領域帰属不明)、齟齬 J (新規 main run は既存出力で大部分代替可能、新規 post-process のみ必要)。

主題自体 (Atom 的隆盛の統計的観察、3 単位フレーム) は v10.6 既存出力の解像度向上 + 新規分布化として **30 分〜数時間の post-process で大部分実装可能**、ただし上記齟齬を Web Claude/Taka が確認しないと本書 §3 操作的定義素案が機能しない。物理層 frozen 絶対 (絶対格言 #2)、書き込みは `unified/v1101/` 配下のみ。

Code A 認識確認連続継続、Web Claude/Taka 即決事項返答 5 件 (親資料の解釈 / v1100 残課題の扱い / Integration 既存集約との関係 / 時系列既存出力との関係 / atom 集合定義) を要請。

---

## 1. 実環境調査結果

### 1.1 本書「親」資料の所在 (齟齬 A)

| 本書 §冒頭で記載 | 実体の所在 | 状態 |
|---|---|---|
| `v1100_phase_result.md` | **存在せず** (v1100 ディレクトリ存在: `unified/v1100/`) | **齟齬 A-1** |
| `v1101_phase_design.md` | **存在せず** (v1101 ディレクトリも存在せず) | **齟齬 A-2** |
| 実在: `unified/v1100/v1100_observation.md` | Code A Step J 観察事実報告 (2026-05-12) | (本書「親」と認識ズレ) |
| 実在: `unified/v1100/v1100_step_a_recognition.md` | Code A Step A 認識確認 (2026-05-12) | (本書「親」と認識ズレ) |
| 実在: `unified/v1100/language_side_investigation_report.md` | Language 側調査報告 | (本書「親」と認識ズレ) |

#### 1.1.1 v1100 の実体 (Code A Step J 報告 `v1100_observation.md` より)

v11.0.0 (v1100) は **Language ↔ Genesis 接続準備の第一歩** として「6 候補事前検証 + 候補 6 (null cell ↔ base 優位照合) 実装」を扱った主題。Code A 実装結果:
- R@3 ベース: base 優位 token = 0 (4 mode hit pattern 完全同一)
- R@1 ベース: base 優位 token = 18 (R@1=0.96 vs B/C/BC=0.78)
- Language base 優位 atom 集合 {SOC.official, PRP.part} 2 atoms vs Genesis Map 5 null cell atom 集合 20 atoms の **重なり 0 / Jaccard 0**
- 新齟齬 #36 (Phase 10 Cell ≠ Phase 8+9 Cell)、留保 #37 (小サンプル限界)

#### 1.1.2 v1100 提案の v1101 主題候補 (Code A `v1100_observation.md` §7)

| 候補 | 内容 | 実装スケール |
|---|---|---|
| A | 候補 5 (Synapse 評価層化、簡略化版) | 30-60 分 |
| B | 候補 3 概念再定義 (Phase 8+9 Cell ↔ Integration α/β 同型性検証) | 1-2 日 |
| C | 候補 6 大規模化 (Berlin 以外 domain で再評価、留保 #37 解消) | 中規模 |

→ **本書はこれら 3 候補のいずれにも言及せず、完全に別主題 (Atom 的隆盛、純 Genesis 観察) へ pivot**。これは Taka 3 日長考の結論として正当性はある (本書 §0.3、§5.6) が、v1100 残課題との関係明示が必要。

### 1.2 Genesis 側既存出力照会 (絶対格言 #8)

#### 1.2.1 cid × atom 類似度 (本書 §3.1 濃度素案の基盤)

| 出力 | 所在 | 状態 |
|---|---|---|
| `cid_atom_sim_matrix_seed{N}.parquet` | `developmental/v106/outputs/main/` × 24 seeds | ✓ 全 seeds 揃い、seed 0 で 228 cids × 326 atom cosine 類似度 (静的) |

形式 (seed 0):
```
shape: (228, 328)
cols: [seed, cid, ABS.bound, ABS.exempt, ..., 326 atoms]
example: cid=0 → ABS.bound 0.193, ABS.exempt 0.109, ...
```

→ **本書 §3.1 「Atom 濃度 = v10.6 cid_atom_sim_matrix[c][a]」の素案は実環境で算出可能** (静的、1 seed 1 値)。

#### 1.2.2 per-cid per-t 時系列出力 (齟齬 E の根拠)

| 出力 | 所在 | 内容 |
|---|---|---|
| `event_cid_alignment_seed{N}.csv` | `developmental/v106/outputs/main/event_trajectory/` × 24 seeds | per-cid per-event 時系列 16 列、seed 0 で **15,687 行** |
| `pulse_cid_alignment_seed{N}.csv` | `developmental/v106/outputs/main/pulse_trajectory/` × 24 seeds | per-cid per-pulse 時系列 |
| `step10_cid_alignment_seed{N}.csv` | `developmental/v106/outputs/main/step10_trajectory/` × 24 seeds | per-cid per-10step 時系列 |
| `window_cid_alignment_seed{N}.csv` | `developmental/v106/outputs/main/window_trajectory/` × 24 seeds | per-cid per-window 時系列 |

#### 1.2.3 event_cid_alignment 形式 (実測、seed 0)

```
shape: (15687, 16)
cols: ['seed', 'cognitive_id', 't', 'source', 'window',
       'lifespan_so_far', 'n_core_member',
       'C_at_window_end', 'Q_remaining_at_window_end', 'R_familiarity',
       'cumulative_n_ingestions', 'cumulative_n_alphas', 'cumulative_n_betas',
       'rank_1_atom', 'rank_1_sim', 'top_category']
example row: cid=0, t=0, window=19, lifespan=1, n_core=5,
             C=0.0, Q=33.0, R=0.0,
             rank_1_atom='TIM.appear', rank_1_sim=0.517, top_category='TIM'
```

→ **per-cid の atom 濃度 (rank 1 のみ) は時間 t に紐づいて 15,687 行存在**。本書 §3.1 論点 1 案 (a 静的) は誤り、(b cid vector 再計算 / c 5 phase 波及代理) は既存 trajectory より優先する根拠なし。

#### 1.2.4 cross-seed 時系列集約 (24 seeds 全体観察済)

| 出力 | 内容 |
|---|---|
| `cross_seed_event_step_evolution.csv` | event 解像度の step 進化 (24 seeds 統合) |
| `cross_seed_event_atom_distribution.csv` | event 解像度の atom 分布 |
| `cross_seed_event_atom_z_score.csv` | atom 別 z-score (動学的特性) |
| `cross_seed_step10_step_evolution.csv` | step10 解像度の step 進化 |
| `cross_seed_dynamic_atom_emergence.csv` | window 解像度の dynamic 出現 atom |
| `cross_seed_all_resolution_compare.csv` | 4 解像度比較表 (69 行 × 10 列) |

→ **24 seeds 横断の atom 動学観察は v10.6 で大量に既存**、本書 §4.3 ESDE 単位観察の素材は揃っている。

#### 1.2.5 Integration 単位 atom 集約 (齟齬 D の根拠)

| 出力 | 所在 | 内容 |
|---|---|---|
| `beta_atom_aggregate_seed{N}.csv` | `developmental/v106/outputs/main/` × 24 seeds | per-β-Integration の n_member_cids + n_member_alphas + **top_atom + top5_atoms + max_atom_sim** |
| `alpha_atom_aggregate_stratified_seed{N}.csv` | `developmental/v106/outputs/main/stratified/` × 24 seeds | per-α-pattern_class の n_alphas + n_member_cid_observations + **dominant_atom + dominant_atom_sim + top5_atoms** |
| `cross_tab_lifespan_integration_seed{N}.csv` | `developmental/v106/outputs/main/stratified/` × 24 seeds | Integration × lifespan の cross-tab |

beta_atom_aggregate_seed0.csv 例 (実測):
```
seed,beta_id,n_member_cids,n_member_alphas,top_atom,top5_atoms,max_atom_sim
0,0,1,1,FND.timeless,"FND.timeless,COG.enlightenment,EXS.being,EXS.nonbeing,FND.logic",0.476
0,1,2,16,FND.timeless,"FND.timeless,EXS.being,COG.enlightenment,EXS.nonbeing,PRP.clear",0.468
```

alpha_atom_aggregate_stratified_seed13.csv 例 (実測):
```
seed,pattern_class,n_alphas,n_member_cid_observations,dominant_atom,dominant_atom_sim,top5_atoms
13,bridge,28,84,TIM.moment,0.461,"TIM.moment,SPC.direction,COG.learn,WLD.science,TIM.period"
13,capture,22,66,TIM.moment,0.447,"TIM.moment,SPC.direction,FND.logic,COG.learn,WLD.science"
```

→ **本書 §2.3「Integration 単位 atom 観察は v10.x 未実施」は事実誤認**、v10.6 で **top-K 集約形式の Integration atom 観察が 24 seeds 揃って完了している**。本主題の新規貢献は「top-K → 完全分布 (member_cids 全部の atom ベクトル保持)」の解像度向上であって「未実施 → 新規実施」ではない。

### 1.3 取り込み機構 (本書 §1.3「変更しない」と明言) の実体確認

| バージョン | 実体 |
|---|---|
| v10.8 (v108) | `atom_introduction_event` 機構初実装、25 atom × 100 cid × 24 seeds = 60,000 events、bit-identity 全層 PASS、Level 1-3.5 分析完了 (`v108_main_run_report.md`) |
| v10.12 (v112) | 受容 cid pool 再厳格化 (4 条件複合 ¬β + lifespan ≥ 977 + n_core ≥ 5 + fam ≥ top 50%) → 420 cid × 25 atom = 10,500 events (v112) + v108_standard 60,000 events の対比 |

→ 本書 §1.3「取り込み機構は v10.8、変更しない」は v10.8 + v10.12 (再実装) の **両者を「同じ取り込み機構」として括る前提が必要**、本書では v10.12 受容 cid pool 再厳格化への言及なし。

### 1.4 v10.9-v10.13.a の「取り込んだ後どうなるか」観察 (齟齬 B の根拠)

本書 §1.1 表は「v10.9-v10.13.a = 取り込みの感度・波及を観察」「『取り込んだ後どうなるか』が空白」と記述。Code A 実環境照合:

| バージョン | 主要観察軸 | 出力 |
|---|---|---|
| v10.9 (v109) | bimodal 分析 + baseline 再計算 | `v109_bimodal_analyzer.py`, `v109_baseline_recalculator.py` |
| v10.10 (v110) | sensitivity 評価 + multi-axis 層化 + n_core 層化 + round2 分析 | 5 種 analyzer + `v110_main_run_report.md` |
| v10.11 (v111) | q_c_inherited 観察 + response profile 集計 | `v111_q_c_inherited_observer.py`, `v111_response_profile_compiler.py` |
| v10.12 (v112) | 受容 cid 再厳格化 + atom_event_generator (再実装) + baseline_recalc + propagation_analyzer | 10 段階完了、唯一 n_pulses_short のみ paired_d +1.36 で頑健、他 6 metric は方向性なし |
| v10.13.a (v113a) | 5 phase (PHASES) Map analyzer + null phase analyzer + long phase compute | `v113a_maps_analyzer.py`, `v113a_observation_report.md` |

→ **「取り込んだ後どうなるか」は v10.9-v10.13.a で **大量に観察されている**、本書の「空白」表現は不正確**。正確には: 観察はされた、ただし「Atom らしさそのものの隆盛 (濃度の地形)」として捉え直す **観察フレーム** が空白だった。これは観察軸の空白 (絶対格言 #5 違反) ではなく **観察フレームの空白** (絶対格言 #5 と整合) であり、これを明示しないと駆動要因記述 (§0.2) と矛盾する。

---

## 2. 論点 1 (時系列をどう得るか) 実環境データ可用性 (本書 §0.1 第 1 指示の本体)

### 2.1 本書 §3.1 論点 1 の 3 案

| 案 | 内容 | 実環境可用性 |
|---|---|---|
| (a) v10.6 類似度を静的に使う | cid_atom_sim_matrix を時系列なしで扱う | ✓ 既存、ただし「揺れ」(§3.3) と矛盾 |
| (b) cid vector を時系列で再計算 | cid 状態が変化するため再計算必要 | △ 要新規 post-process (cid state ledger 経由)、実装規模中 |
| (c) atom_introduction_event 波及を時系列代理 | v10.13.a 5 phase を時系列の代理に | △ 5 phase は段階分類、時系列ではない |

### 2.2 案 d (Code A 提案): 既存 trajectory 流用

| 出力 | 時系列粒度 | 内容 |
|---|---|---|
| `event_cid_alignment` | per-event (cid 起点 event の発火時 t) | rank_1_atom + rank_1_sim、seed 0 で 15,687 行 |
| `pulse_cid_alignment` | per-pulse | 同上 |
| `step10_cid_alignment` | per-10step | 同上 |
| `window_cid_alignment` | per-window | 同上 |

→ **per-cid の rank_1_atom (dominant atom) 時系列は既に存在**、本書 §3.3 揺れ素案 (時系列での濃度変動 / 分散 / 変化率 / 方向反転回数) のうち、

- **方向反転回数** (rank_1_atom が連続 t で変わる回数): 既存出力で算出可能、新規 post-process 不要
- **分散** (rank_1_sim の t 沿いの分散): 既存出力で算出可能
- **変化率** (rank_1_sim の差分): 既存出力で算出可能

ただし限界:
- 既存 trajectory は **rank 1 のみ** 記録、326 atom 全部の濃度ベクトルではない (たとえば「2 位 atom と僅差」の状況は捨象)
- 完全な「全 atom 濃度の時間変化」は、案 (b) cid vector 再計算が必要

### 2.3 Code A 推奨 (Web Claude/Taka 判断要請)

論点 1 を **2 段階** で扱う:
- **段階 1 (低コスト、30 分-1 時間)**: 案 (d) 既存 trajectory 流用で「rank 1 atom の揺れ」を観察、§4.1 CID 単位の素材として活用
- **段階 2 (中コスト、半日-1 日)**: 必要なら案 (b) cid vector 再計算で「326 atom 全濃度の時間変化」を後付け

段階 1 で本書 §6.1 出口物 #1 (CID 単位 Atom 濃度・揺れの観察結果) の **粗解像度版は実装可能**、段階 2 が必要かは段階 1 後に判断。

### 2.4 cid vector の時間変化が起きるか (案 b の前提)

v106 の cid_atom_sim_matrix は cid 軸毎の 48D 表現 × 326 atom 48D 表現の cosine 類似度。cid の 48D 表現は run 中に変化する (cognitive state)、ただし v10.6 出力は **end-of-run snapshot のみ**。run 中の cid state は ledger に記録されているはず (`v10x_implementation_spec.md` 要参照)、案 (b) 実装には:
- cid state ledger の所在確認
- ledger から t 別 cid vector 構築の post-process 設計

が必要。Web Claude/Taka 判断要請事項。

---

## 3. 事前齟齬指摘リスト (重大度順)

### 3.1 重大度 高 (Step B 着手前に Web Claude/Taka 即決事項とすべき)

#### 齟齬 A: 「親」資料 `v1100_phase_result.md` + `v1101_phase_design.md` が repo に不在

- **本書記述**: 冒頭で「親」として 2 資料を記載
- **実体**: どちらも不在、v1100 は `v1100_observation.md` (Code A) のみ、v1101 は完全未着手
- **Code A 提案**: Web Claude 確認要請 — 本書の「親」は (i) Web Claude memory 内の言及か、(ii) 別場所か、(iii) `v1100_observation.md` の誤記か。v1101 は完全未着手の事実認識共有が必要

#### 齟齬 C: v1100 残課題 (v1101 候補 A/B/C + 留保 #36/#37) の完全欠落

- **v1100 結論**: v1101 候補 A (候補 5 層化) / B (候補 3 概念再定義 = Phase 8+9 Cell ↔ Integration α/β 同型性) / C (候補 6 大規模化)、新規留保 #36 candidate (Phase 10 Cell ≠ Phase 8+9 Cell) + #37 candidate (小サンプル限界)
- **本書**: これら一切言及なしで完全 pivot
- **Code A 提案**: Web Claude/Taka 確認要請 — v1101 候補 A/B/C は (i) 棄却、(ii) 凍結、(iii) 並行検討のどれか。v1100 留保 #36/#37 は本書 §10 留保継承で「継承」明記だが §1.4-1.5 で扱う v10.6 関連留保のみ列挙、新規留保 #36/#37 への言及なし

#### 齟齬 D: §2.3「Integration 単位 atom 観察は v10.x 未実施」は事実誤認

- **本書記述**: §2.3 表「Integration を atom 濃度分布として見る観察は v10.x で実施されていない、本主題の Integration 単位観察は新しい観察フレーム」
- **実体**: v10.6 main outputs に `beta_atom_aggregate_seed{N}.csv` (per-β-Integration の top_atom / top5_atoms / max_atom_sim) + `alpha_atom_aggregate_stratified_seed{N}.csv` (per-α-pattern_class の dominant_atom / top5_atoms) が **24 seeds 揃って存在**
- **Code A 提案**: 本書 §2.3 表記述を **「v10.6 で top-K 集約形式の Integration atom 観察は完了済、本主題は集約 → 完全分布 (member_cids 全部の atom ベクトル保持) への解像度向上」** に修正要請。新規性は「未実施 → 実施」ではなく「集約 → 分布」

#### 齟齬 E: §3.1 論点 1 の 3 案が既存 trajectory を見落とし

- **本書記述**: 案 (a) 静的 / (b) cid vector 再計算 / (c) v10.13.a 5 phase 波及代理
- **実体**: v10.6 main outputs に `event_cid_alignment` + `pulse_cid_alignment` + `step10_cid_alignment` + `window_cid_alignment` の **4 解像度時系列出力が既存** (per-cid per-t の rank_1_atom + rank_1_sim、seed 0 で 15,687 行)
- **Code A 提案**: 案 (d) 既存 trajectory 流用を追加要請。段階 1 (既存 trajectory) → 段階 2 (必要なら cid vector 再計算) の 2 段階アプローチを推奨

### 3.2 重大度 中

#### 齟齬 B: §1.1 表「v10.9-v10.13.a 取り込んだ後どうなるかが空白」は省略過多

- **本書記述**: v10.9-v10.13.a の状態欄「『取り込んだ後どうなるか』が空白」
- **実体**: v10.9 (bimodal/baseline_recalc) → v10.10 (sensitivity/multi-axis 層化) → v10.11 (q_c_inherited/response profile) → v10.12 (受容 cid 再厳格化 + propagation_analyzer) → v10.13.a (5 phase Map analyzer) で大量観察済、特に v10.12 で paired_d / sign_test / bootstrap CI / 留保 #27 formal まで完遂
- **Code A 提案**: 表を「観察はされた、ただし『Atom らしさそのものの隆盛 (濃度の地形)』として捉え直す観察フレームが空白だった」に修正要請。これは絶対格言 #5 (観察軸を増やすことを駆動要因にしない) と整合的な「観察フレーム転換」であり、本書 §0.2 駆動要因記述と一致する正確な表現

#### 齟齬 F: §3.1 Atom 濃度の確定値素案 vs §3.3 揺れの不整合

- **本書 §3.1**: 「cid c の atom a に対する濃度 = v10.6 cid_atom_sim_matrix[c][a] (cosine 類似度、-1〜1)」 = **確定値**
- **本書 §3.3**: 「揺れ = 時系列での濃度の変動」 = 時系列前提
- **本書 §1.2**: 「濃度は確定的でなく、揺れている」 = §3.1 確定値素案と矛盾
- **Code A 提案**: 論点 1 解決前は素案として機能しない、論点間依存性を §3 に明示要請。または濃度素案を「v10.6 静的値 = 系の初期/平均濃度、揺れ = 動学観察で別軸」と二段定義に分離

#### 齟齬 G: §3.4 Integration 単位 — seed 横断 vs per-seed の選択不明

- **本書記述**: Integration を「どの cid を捉え、その cid 群がどの atom と似て / 異なるか」の分布で示す
- **不明点**: (i) seed 0-23 のどれを使うか、(ii) seed 内 Integration を横断するか per-seed か、(iii) α (観察軸) と β (会計単位) のどちらか / 両方か
- **v10.4-v10.5 機構**: β は per-seed 単一所属、α は per-seed 複数所属、Integration 数は seed 間で変動
- **Code A 提案**: Web Claude/Taka 確認要請 — 推奨は (Code A 仮所見) per-seed × {α, β} 両方を観察、cross-seed は集計 (`cross_seed_*` 形式) で別途、Integration の「同一性」は seed 横断で保証されない (各 seed で独立に生成される) 前提を明示

#### 齟齬 H: atom 集合の定義不明 (326 全部 / 25 TARGET / 上位)

- **本書記述**: 「Atom 濃度」「Atom 隆盛」と総称、対象 atom 集合不明
- **可能性**: (i) Language 側 326 atom 全部、(ii) v10.8/v10.12 取り込み 25 TARGET_ATOMS、(iii) 隆盛上位のみ
- **v10.6 cid_atom_sim_matrix**: 326 atom 全部を保持
- **v10.8/v10.12 取り込み**: 25 TARGET_ATOMS subset (`v108_atom_event_generator.py` 定数)
- **v10.13.a Map 5 null candidates**: 20 unique atoms
- **Code A 提案**: Web Claude/Taka 確認要請 — 推奨は (Code A 仮所見) §4.1 CID 単位は 326 全部、§4.2 Integration 単位は 326 全部、§4.3 ESDE 単位は 326 全部 + 25 TARGET vs 残り 301 の分離表示

### 3.3 重大度 低

#### 齟齬 I: §6.1 出口物 #5「ESDE の内部は Atom 的にこうなっているようだ」の領域帰属不明

- **本書記述**: §6.3「『意味』『自律性』『会話』への到達判定」は Taka 領域、§6.1 出口物 #5「『ESDE の内部は Atom 的にこうなっているようだ』の記述」
- **不明点**: 出口物 #5 は Code A 観察事実領域か、Web Claude 翻訳領域か、Taka 直感領域か
- **Code A 提案**: Web Claude 確認要請 — Code A は観察事実 (3 単位の数値 + 分布記述) のみ、「Atom 的にこうなっているようだ」の解釈統合は Web Claude 担当 (Phase Result) と切り分けるのが Aruism 判定回避 (絶対格言 #12) と整合

#### 齟齬 J: §6.4 新規 main run 要否

- **本書記述**: 「Code A 認識確認 (Step A) で論点 1 の実環境データ可用性を確認してから新規 main run の要否を確定」
- **Code A 確認結果**: v10.6 main outputs (cid_atom_sim_matrix + beta_atom_aggregate + alpha_atom_aggregate_stratified + cross_tab_lifespan_integration + event/pulse/step10/window trajectory + cross_seed_*) で本書 §6.1 出口物 #1-#3 の **段階 1 (粗解像度) は新規 main run なしで実装可能**
- **Code A 提案**: 段階 1 は新規 post-process のみ、段階 2 (cid vector 全 326 atom 時系列再計算) のみ新規 main run の可能性あり、これも cid state ledger の事後再生で実現できる可能性あり (実 ledger 不変、絶対格言 #2 遵守)

#### 齟齬 K: §10.1 留保 #38 candidate「cid vector の時間変化が可能か」

- **本書記述**: 「v10.6 cid × atom 類似度の時系列化が可能か (cid vector の時間変化) → Code A Step A で確認」
- **Code A 確認結果**: §2.4 (本書) — cid state ledger の所在 + ledger から t 別 cid vector 構築の post-process 設計が必要、ただし `event_cid_alignment` の `C_at_window_end`/`Q_remaining_at_window_end`/`R_familiarity` 等の状態列は per-t 既存、これらから 48D cid vector 再構築可否は要検証
- **Code A 提案**: 留保 #38 candidate を「ledger 再生可能性 + rank 1 既存出力との解像度差」の 2 部に分けて Web Claude/Taka 判断

---

## 4. 本主題 §4 (3 単位) の実装可能性 (Code A 視点、実環境照合)

### 4.1 CID 単位 (本書 §4.1)

| 素案項目 | 既存出力で実現 | 新規 post-process 要 |
|---|---|---|
| 各 cid の 326 atom 濃度プロファイル (静的) | ✓ v10.6 cid_atom_sim_matrix (228 cids × 326 atom × 24 seeds) | なし |
| 各 cid の rank 1 atom 時系列 | ✓ event/pulse/step10/window_cid_alignment | なし、解像度選択のみ |
| 各 cid の 326 atom 全濃度時間変化 | ✗ | cid state ledger 再生 + cid vector 構築 (中規模) |

**判定**: ✓ 段階 1 (rank 1 時系列) 実装可能 (30 分-1 時間)、段階 2 (326 atom 全時系列) は要設計

### 4.2 Integration 単位 (本書 §4.2)

| 素案項目 | 既存出力で実現 | 新規 post-process 要 |
|---|---|---|
| Integration の member_cids | ✓ end-of-run snapshot は v10.6 内 (beta_atom_aggregate の n_member_cids、ただし cid id 列なし) | member_cids の具体 cid id 取得は要再生 |
| Integration の top_atom / top5_atoms / max_atom_sim | ✓ beta_atom_aggregate_seed{N}.csv (24 seeds) | なし |
| Integration α の dominant_atom / top5_atoms (pattern_class 別) | ✓ alpha_atom_aggregate_stratified_seed{N}.csv (24 seeds) | なし |
| Integration の **member_cids 全部の atom ベクトル分布** (集約せず) | ✗ | member_cids cid id list + cid_atom_sim_matrix 結合 (簡単、30 分) |
| Integration の atom 分布の時系列推移 | ✗ | 案 (b) cid vector 再計算依存 (中規模) |

**判定**: ✓ 段階 1 (per-seed × {α, β} の member_cids 全 atom 分布、静的) 実装可能 (1-2 時間)、段階 2 (時系列) は要設計

### 4.3 ESDE 単位 (本書 §4.3)

| 素案項目 | 既存出力で実現 | 新規 post-process 要 |
|---|---|---|
| 系全体 (全 cid) の atom 濃度の集計 | ✓ cid_atom_sim_matrix を 24 seeds 集約 | 30 分 |
| 系全体の atom 隆盛の時系列推移 | ✓ cross_seed_event_step_evolution + cross_seed_step10_step_evolution | なし |
| どの atom が盛んかの変化 | ✓ cross_seed_dynamic_atom_emergence + cross_seed_event_atom_distribution | なし |

**判定**: ✓ 既存出力で大部分実装可能 (集計のみ、30 分)

### 4.4 操作的定義の論点 (本書 §3.6) との接続

| 論点 | Code A 提案解 |
|---|---|
| 論点 1 (時系列をどう得るか) | 段階 1 案 (d) 既存 trajectory 流用、段階 2 案 (b) cid vector 再計算 |
| 論点 2 (隆盛を何で測るか) | 神の手回避のため、Code A は **3 指標を併記** (濃度総和 / 上位濃度集中度 / 閾値超 cid 数) し、Web Claude 翻訳で取捨選択を提案 |
| 論点 3 (Integration 分布の記述形式) | 段階 1: top-K (既存) + member_cids 全 atom ベクトル分布 (生データ) + 分布特徴量 (分散 / 歪度 / 上位 atom 集合) の 3 層併記 |

---

## 5. Step B-K 進行案 (Code A 推奨、Web Claude/Taka 承認後発動)

| Step | 内容 | 想定時間 |
|---|---|---|
| Step A (本書) | 認識確認 + 事前齟齬指摘 10 件 + 論点 1 実環境可用性確認 + 段階 1/2 設計 | (完了) |
| Step B | 環境チェック (v10.6 cid_atom_sim_matrix + beta_atom_aggregate + alpha_atom_aggregate_stratified + 4 解像度 trajectory + cross_seed_* の read-only 確認、書き込みなし) | 10 分 |
| Step C | CID 単位段階 1 — 各 cid の 326 atom 濃度プロファイル統計 (24 seeds 集約) + rank 1 atom 時系列 (4 解像度) | 1-2 時間 |
| Step D | Integration 単位段階 1 — per-seed × {α, β} の member_cids 全 atom ベクトル分布、top-K 集約 (既存) との対比 | 1-2 時間 |
| Step E | ESDE 単位段階 1 — 系全体 atom 隆盛集計 + 4 解像度時系列推移 | 1 時間 |
| Step F | 3 単位の観察事実統合表 (Web Claude Phase Result 用素材) | 30 分 |
| Step G | bit-identity 検証 (新規 post-process、書き込み `unified/v1101/` 配下のみ、v10.6 main outputs 不変) | 30 分 |
| Step H | 観察事実報告 (Code A、3 単位の段階 1 結果 + judgment 回避 + Web Claude 翻訳要素材) | Code A 作業時間 4-6 時間 |
| Step I | (Optional) 段階 2 (cid vector 326 atom 全時系列再計算 + Integration 分布時系列) — Step H 結果次第 | 半日-1 日 |
| Step J | Phase Result (Web Claude 担当) | Web Claude 作業 |

**合計時間 (Step B-H 段階 1 のみ)**: 約 6-8 時間 (Code A 作業)、新規 main run **不要** (v10.6 既存出力流用)、bit-identity 全層 PASS (v10.6 main outputs 不変、書き込み `unified/v1101/` 配下のみ)。

段階 2 (Step I) は段階 1 結果次第、Web Claude/Taka 判断対象。

---

## 6. チェーン接続 4 問への自己点検 (本書 §1 + §6 への返答)

### 6.1 v1101 はチェーンのどこに寄与するか

**本書記述**: v10.8 以降「Atom を取り込む」枠組みの行き詰まり (取り込んだ後どうなるか空白) を Atom 的隆盛の観察フレームで解消、Unified phase の主題
**Code A 自己点検**: △ 「v1100 Language ↔ Genesis 接続」と「v1101 Genesis 単独 Atom 隆盛観察」が **同じ Unified phase 内で並列か、v1101 が v1100 を吸収する pivot か** が不明 (即決事項 2 で「v1100 残課題 A/B/C は凍結、v11.0.1.a / v11.0.2 で扱う可能性残す」と確定)

### 6.2 v1101 がないと何が破綻するか

**本書記述**: 取り込み後の Atom 的傾向の把握ができない、ESDE 単位での Atom 観察フレームが空白
**Code A 自己点検**: ✓ ただし v10.6 cross_seed_event_step_evolution + v10.12 propagation_analyzer + v10.13.a 5 phase Map で **部分的観察は既存**、v1101 の新規性は「3 単位 (CID/Integration/ESDE) を統一フレームで分布解像度に並べる」点に絞られる (Web Claude 改訂版で観察 1「一点」+ 観察 2「取り込み点中心」が中核に追加され、3 単位は補助に降格)

### 6.3 v1101 があることで何が言えるか

**本書記述**: 「ESDE の内部は Atom 的にこうなっているようだ」が 3 単位で言える
**Code A 自己点検**: ✓ ただし出口物 #5 の領域帰属 (Code A 観察事実 vs Web Claude 翻訳 vs Taka 直感) を §6.1 で明示要請 (齟齬 I)

### 6.4 新規性開発の留保 (Taka 指摘 2026-05-12)

「歯抜けになることや前後逆転すること、謎は謎なままの状態の維持、どれも重要」
**Code A 自己点検**: ✓ 本書で齟齬 A (親資料不在) + 齟齬 C (v1100 残課題欠落) + 齟齬 E (時系列既存出力見落とし) を「謎は謎のまま」記録、推測で断言せず Web Claude/Taka 上申。

---

## 7. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step A での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 実環境調査を §1-2 で先実施、解釈は §4-5 で構造記述 |
| 2 | 物理層 frozen 絶対 | ✓ v1101 は v10.6 既存出力 read-only、書き込み `unified/v1101/` 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | (本書 §3 規律遵守チェック #3「操作的定義確定時に検討」を継承、本 Step A では該当なし) |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ §3.1 齟齬 D で「集約 (top-K) → 分布」解像度向上を主題核心と確認、本書 §3.4 平均化回避を §4.2 で実装可能性確認済 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ §1.4 齟齬 B で「観察フレームの空白 (絶対格言 #5 整合) vs 観察軸の空白 (絶対格言 #5 違反)」を区別 |
| 6 | 出口の固定 | ✓ §0 / §5 で 11 項目 (事前齟齬 10 件 + Step B-J 進行案) を出口物として固定 |
| 7 | 主題着手前に上位資料を読む | ✓ §1 で v1100 実体 (`v1100_observation.md` + `v1100_step_a_recognition.md`) + v10.6/v10.8/v10.12/v10.13.a 出力を実環境照合済 |
| 8 | 過去観察軸の照会 | ✓ §1.2-1.4 で v10.4-v10.13.a の観察軸 (cid_atom_sim_matrix / 4 解像度 trajectory / beta_atom_aggregate / alpha_atom_aggregate_stratified / cross_seed_*) を照合、齟齬 D/E の根拠 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ §4.4 論点 2 で 3 指標併記提案 (神の手回避)、本書 §3.2 神の手回避規律を継承 |
| 10 | 因果ではなく因果候補 | ✓ §3 齟齬指摘で「~の可能性」「~は事実誤認」表現、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ Integration α/β / pattern_class / β-Integration / member_cids / atom 濃度 / 隆盛 / 揺れ を §1-3 で区別 |
| 12 | Aruism 判定回避 | ✓ §3.3 齟齬 I で「Atom 的にこうなっているようだ」の領域帰属 (Code A 観察 vs Web Claude 翻訳 vs Taka 直感) を Web Claude 確認要請、Code A は判定回避 |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Web Claude 親資料不在 (齟齬 A) + Integration 観察未実施記述誤認 (齟齬 D) + 時系列既存出力見落とし (齟齬 E) を事実として記録、信頼性判断なし |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka 3 日長考の結論 (本書 §5) は原文保存済 (本書側)、Code A は実装可能性検証のみ |
| 15 | 5 者運用体制の補完性 | ✓ Code A 認識確認連続 10 段階 (v110 Step A + v110 Step J + v1100 Step A + v1100 Step J + v1101 Step A = 5 主要点、最後の v1101 Step A は当初 v1102 として実施、Taka 2026-05-17 番号修正)、Web Claude 親資料不在 + 観察軸照会不足 + 既存出力見落とし を補完 |

→ **15 格言全項目遵守** (#3 のみ操作的定義確定時に適用検討、本書 §8 規律チェックと整合)。

---

## 8. 留保事項 (継承 35 件 + 新規候補 3 件)

### 8.1 継承 35 件

v1100 Phase Result (`v1100_observation.md` Step J) の留保 35 件 (継承 32 + 新規 3: #35 親資料不在 / #36 candidate Phase 10 Cell ≠ Phase 8+9 Cell / #37 candidate 小サンプル限界) を継承。本主題に特に関連する留保:

| id | 内容 | 本主題との接続 |
|---|---|---|
| #21 | v10.5 機構 A 既知挙動 | §4.2 Integration 単位観察で member_cids の Q/C 継承挙動を要参照 |
| #26 | cond3 構造的帰結 (受容 cid pool 偏り) | §4.3 ESDE 単位の隆盛観察で受容 cid pool の偏りを考慮 |
| #27 | smoke seed 0 特異性 | §4.1 CID 単位観察で seed 0 の特異性を考慮 (smoke 後 main 24 seeds で確認、memory feedback_smoke_seed0_not_absolute) |
| #33 | 集計単位による方向反転 | §4.2 Integration 単位で同じ atom が異なる単位で異なる隆盛を示す可能性 (本書 §10 留保 #33 と整合) |

### 8.2 新規候補 3 件 (本書 Step A 由来)

| id | step | title | 状態 |
|---|---|---|---|
| **#38 candidate** | v1101 Step A | 本書「親」資料 `v1100_phase_result.md` + `v1101_phase_design.md` の repo 不在 (v1100_observation.md 実体、v1101 完全未着手)、Web Claude 認識ミス連続パターン継続 (絶対格言 #7 運用課題) | 既出 (齟齬 A) |
| **#39 candidate** | v1101 Step A | 本書 §2.3「Integration 単位 atom 観察は v10.x 未実施」記述誤認、v10.6 main outputs に beta_atom_aggregate + alpha_atom_aggregate_stratified が 24 seeds 揃って存在 (絶対格言 #8 過去観察軸照会不足) | 既出 (齟齬 D) |
| **#40 candidate** | v1101 Step A | 本書 §3.1 論点 1 の 3 案が v10.6 main outputs の 4 解像度 trajectory (event/pulse/step10/window) 既存出力を見落とし、案 (d) 既存 trajectory 流用を追加要請 | 既出 (齟齬 E) |

### 8.3 v1100 留保 #36/#37 candidate の状態

本書では言及なし。Code A 判断: 本主題 (純 Genesis Atom 隆盛観察) は v1100 candidate 1/3 (UBAF / Phase 10 Cell) と独立、ただし候補 5 (Synapse 評価層化) / 候補 6 大規模化との関係は **並行検討の余地あり**、Web Claude/Taka 確認要請。

---

## 9. Web Claude/Taka 即決事項返答要請

### 9.1 即決事項 (Step B 着手前に必要)

1. **「親」資料の解釈** (齟齬 A): `v1100_phase_result.md` + `v1101_phase_design.md` は repo 不在、`v1100_observation.md` (Code A Step J) で代替可能か Web Claude 確認要請。v1101 完全未着手の事実認識共有
2. **v1100 残課題の扱い** (齟齬 C): v1101 候補 A (候補 5 層化) / B (候補 3 概念再定義 Phase 8+9 Cell ↔ Integration α/β) / C (候補 6 大規模化) は (i) 棄却 / (ii) 凍結 / (iii) 並行検討のどれか、Web Claude/Taka 判断
3. **Integration 既存集約との関係** (齟齬 D): 本書 §2.3 記述を「v10.6 で top-K 集約完了、本主題は集約 → 完全分布の解像度向上」に修正可否、Web Claude 確認
4. **時系列既存出力との関係** (齟齬 E): 本書 §3.1 論点 1 に案 (d) 既存 trajectory 流用 追加可否、段階 1 (既存 trajectory) → 段階 2 (cid vector 再計算) の 2 段階アプローチ承認可否、Web Claude/Taka 判断
5. **atom 集合の定義** (齟齬 H): 326 全部 / 25 TARGET / 上位の選択、推奨は (Code A 仮所見) 326 全部 + 25 TARGET vs 残り 301 の分離表示、Web Claude/Taka 判断
6. **出口物 #5 の領域帰属** (齟齬 I): 「Atom 的にこうなっているようだ」記述は Code A 観察 / Web Claude 翻訳 / Taka 直感 のどこか、推奨は Web Claude 翻訳領域、Web Claude 確認
7. **Integration 単位の選択** (齟齬 G): per-seed × {α, β} 両方の観察可否、cross-seed 集約方法、Web Claude/Taka 判断

### 9.2 Step B 着手判断

上記 #1-#7 が確定すれば §5 Step B-H 進行案 (合計 Code A 作業 6-8 時間、新規 main run 不要) で進行可能。段階 2 (Step I) は段階 1 結果次第。

### 9.3 物理層 frozen 絶対保証 (絶対格言 #2)

- v10.6 main outputs (cid_atom_sim_matrix + beta_atom_aggregate + alpha_atom_aggregate_stratified + 4 解像度 trajectory + cross_seed_*): **read-only**、本主題で 1 byte も変更しない
- v10.8 / v10.12 / v10.13.a 既存出力: **read-only**
- 書き込みは `unified/v1101/outputs/` 配下のみ、bit-identity 層 A (smoke 2 回実行 hash 一致) + 層 B (既存 outputs 全 mtime+size 不変) + 層 C (構造的書き込み制限) を Step G で保証

---

## 10. 一文サマリ (再掲)

実環境調査で 10 件の事前齟齬を発見、特に重大なのは齟齬 A (本書「親」記載 `v1100_phase_result.md` + `v1101_phase_design.md` は repo 不在、実体は `v1100_observation.md` Code A Step J 観察事実報告のみ、v1101 完全未着手) + 齟齬 D (本書 §2.3「Integration 単位 atom 観察 v10.x 未実施」は事実誤認、v10.6 main outputs に beta_atom_aggregate_seed{N}.csv + alpha_atom_aggregate_stratified_seed{N}.csv が 24 seeds 揃って存在、本主題の新規性は「top-K 集約 → 完全分布」の解像度向上) + 齟齬 E (本書 §3.1 論点 1 の 3 案が v10.6 main outputs の 4 解像度 trajectory event/pulse/step10/window_cid_alignment_seed{N}.csv 既存出力を見落とし、案 d 既存 trajectory 流用を追加すべき)、他 齟齬 B (v10.9-v10.13.a の取り込み後観察大量既存、表記述「空白」は不正確) + 齟齬 C (v1100 残課題 v1101 候補 A/B/C 完全欠落) + 齟齬 F (§3.1 確定値素案 vs §3.3 揺れ時系列前提の不整合) + 齟齬 G (Integration の seed 横断 / per-seed / α-β 選択不明) + 齟齬 H (atom 集合 326 / 25 / 上位の選択不明) + 齟齬 I (出口物 #5 領域帰属不明) + 齟齬 J (新規 main run 不要、新規 post-process のみ)、本主題の 3 単位観察 (CID/Integration/ESDE) は v10.6 既存出力 + 新規 post-process で **段階 1 (粗解像度) 6-8 時間で実装可能**、段階 2 (cid vector 326 atom 全時系列) は cid state ledger 再生で実現候補、Web Claude/Taka 即決事項返答 7 件 (親資料解釈 / v1100 残課題扱い / Integration 既存集約関係 / 時系列既存出力関係 / atom 集合定義 / 出口物 #5 領域帰属 / Integration 単位選択)、絶対格言 15 件全項目遵守、Code A 認識確認連続 10 段階継続、新規留保 #38-#40 candidate (本書親資料不在 / Integration 観察未実施記述誤認 / 時系列既存出力見落とし)、v1100 留保 #36/#37 candidate (Phase 10 Cell ≠ Phase 8+9 Cell / 小サンプル限界) は本書言及なしで継承状態不明、物理層 frozen 絶対 (v10.x 既存出力 read-only、書き込み `unified/v1101/` 配下のみ、bit-identity 層 A/B/C 全層 PASS を Step G で保証)、Web Claude/Taka 返答後に Step B 環境チェック着手。

---

*以上、v11.0.1 (v1101) Step A 認識確認 (Code A、2026-05-16 作成、2026-05-17 番号修正)。Web Claude/Taka 即決事項返答受領済 (齟齬 10 件全採用、観察 1/2 選定基準確定、v1100 残課題 A/B/C 凍結)、Step B 環境チェックに進む。事前齟齬 10 件 + 留保候補 3 件 (#38-#40) + 3 単位実装可能性 + 規律 15 格言遵守確認 を本書に整理。Code A 認識確認連続 10 段階継続。*
