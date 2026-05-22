# v1104 観察 2 再調査指示 — Code A 宛

*作成*: 2026-05-23、Web Claude (相談役、Genesis 側)
*親*: `v1104_phase_design_v2.md` + `v1104_step_a_recognition.md` + `v1104_step_h_observation_final.md` + Taka 判断 (2026-05-23、観察方法を疑う方針)
*対象*: Code A (実装担当)
*位置づけ*: v1104 主題 Step H 観察事実 (観察 2、lift=0、85% self-loop) について Taka が「構造的に作ってきたものが構造を辿れないなら観察方法を疑う」と判断。Phase Result (Step I) は本書の再調査結果を待ってから書く。バージョンアップ・資料作成に待てがかかった状態。

---

## 0. Taka 整理 (2026-05-23、原文)

> これまででいうとこういうのって結局実装側の問題なのでバージョンアップや資料作成に待てをかけて懐疑的に進めていく方がいい。満足いくまで調べた結果を PhaseResult としてあげる。その結果がどうだったとしてそれは仕方ないけど怪しいなと言う感情のまま先に進むといいことない。

→ v1104 Phase Result + 次主題 (v1105 候補) は **再調査結果が揃うまで保留**。観察 2 の結果が「ESDE の事実」か「観察方法がランダムの穴に落ちた結果」かを切り分ける。

## 1. 駆動要因 — なぜ再調査するか

### 1.1 構造的疑念

留保 #33 系列 (集計単位で像が変わる) と整合的な v10.13.a 以来の経験則から、観察 1 が n_members × qc_gini 層化で像が変わることを示した (match_k1 が n=1 で 0.884 → n=4+ で 0.569、Δ-0.315 単調低下)。

観察 2 の predecessor 連鎖は同じ ESDE 構造の中で動いているにもかかわらず、全 6 scope で lift=0 (shuffle と統計的に区別不能)、85% self-loop。これは:

- (a) ESDE の事実 (predecessor は「連想を辿る」構造でなく「注意が同じ場所に留まる」現象を記録)
- (b) 観察方法がランダムの穴に落ちた結果 (構造があるのに観察方法が平らに均してしまった)

の二択。Taka 判断「構造的に作ってきたものが構造を辿れないなら観察方法を疑う」に従い、(b) の可能性を潰してから (a) を確定する。

### 1.2 観察 1 と観察 2 の非対称

観察 1 は n_members × qc_gini で層化、観察 2 は scope 別のみで未層化。同じ ESDE 構造を扱うのに観察軸の対称性が欠けている (絶対格言 #11 概念単位を雑に扱わない の延長違反候補)。

---

## 2. 再調査ポイント 4 件 (優先順)

### 2.1 再調査 1 — n_members × qc_gini での層化 (最優先)

**問い**: 観察 1 で決定的だった層化軸 (n_members × qc_gini) を観察 2 にも適用したら、どの bin で lift > 0 が出るか。

**手順**:
1. `observation_2_predecessor_chain.parquet` (39,537 chains) を読み込み
2. 各 chain の alpha_id (または beta_id) から n_members_bin (n=1 / n=2 / n=3 / n=4+) と qc_gini_bin (low / mid / high) を引く
3. CID scope は cid_id に対応する全 alpha/beta の n_members 分布が出るので、CID scope は「所属する alpha/beta の n_members の中央値」または「所属する最大の Integration の n_members」を bin に使う (どちらを採用するかは Code A 判断、本書 §4 確認要請で報告)
4. ESDE 3 scope は n_members の概念が直接適用できないので層化対象外 (理由: ESDE scope は全 cid の集約で層化軸を持たない)
5. 各 (scope, n_members_bin, qc_gini_bin) 別に以下を再算出:
   - chain 数
   - mean_sim_along_chain
   - shuffle_baseline_sim_mean
   - **lift_over_baseline (= sim - baseline)**
   - atom_changes / chain
   - category_changes / chain
   - self_loop_rate
6. lift > 0.01 (効果サイズ閾値、絶対格言 #3) の bin を抽出

**出力**: `observation_2_restratified.parquet` (per (scope, n_members_bin, qc_gini_bin))

**期待される結果**: どこかの bin で lift > 0 が出れば、観察 2 の (b) の可能性が浮上。全 bin で lift ≒ 0 なら (a) の確度が上がる。

### 2.2 再調査 2 — shuffle baseline の単位の明示と再算出

**問い**: shuffle baseline の permutation 単位を明示し、複数の単位で算出して比較する。現状 lift=0 が「shuffle が構造を壊していない」のか「sim_matrix が平らで shuffle に意味がない」のか切り分ける。

**手順**:
1. 現状の shuffle baseline の permutation 単位を Code A 自身が確認 (実装スクリプト `v1104_step_c_observation_2.py` を参照)
2. 以下 3 種類の shuffle baseline を per (scope, seed) で算出し並列出力:
   - **shuffle 種別 A — chain 内 permutation**: 各 chain 内の cid 順を入れ替える。chain 構造 (長さ・self-loop 率) を保ちながら順序だけ shuffle
   - **shuffle 種別 B — chain 間 permutation**: chain をまたいで cid を入れ替える。chain 構造を壊しながら shuffle
   - **shuffle 種別 C — global cid pool permutation**: per (scope, seed) で全 cid プールから一様ランダムに引く。chain 構造を完全に無視
3. sim_matrix が平らかどうかの確認指標として、cid_atom_sim_matrix_seed{N}.parquet の per (scope) cid ペア sim 分布の以下を出力:
   - mean / median / std
   - 5/25/50/75/95 percentile
4. global cid pool permutation (shuffle 種別 C) でも lift=0 なら、sim_matrix 自体が平らで shuffle に意味がない可能性が高い

**出力**: `observation_2_shuffle_variants.parquet` (per (scope, seed, shuffle_type) で lift) + `cid_sim_matrix_distribution.parquet` (per (scope) で sim 分布)

**期待される結果**:
- shuffle A/B/C で lift がほぼ変わらず ≒ 0 → sim_matrix 平らが原因 (観察 2 の数値自体が指標として無効)
- shuffle A で lift ≒ 0、shuffle C で lift > 0 → chain 内構造に意味があり observation の単位を見直す必要
- shuffle A/B/C で大きく異なる → permutation 単位の選定が結果を決めていた

### 2.3 再調査 3 — chain の粒度 (window → step → event)

**問い**: chain を window 単位 (連続 conscious window) で見ているが、もっと細かい単位 (step10、event) で見ると注意が動いている可能性。v10.6 の 4 解像度 trajectory (event / pulse / step10 / window) を活用。

**手順**:
1. v10.6 の event 解像度 trajectory を入力に追加。各 event の rank_1_atom と attention_candidate の対応を確認
2. window 解像度の chain (現状) と、step10 解像度の chain、event 解像度の chain の 3 階層で chain を構築:
   - **window 解像度**: 現状の chain (39,537 chains、length 平均 29.67)
   - **step10 解像度**: 同じ conscious 区間を step10 単位で割って chain を構成。chain length が約 10 倍長く、注意の細かい動きが見える
   - **event 解像度**: event 単位 (各 cid 形成・更新・ghost 化など) で chain を構成
3. 各解像度で:
   - chain_length 分布
   - n_unique_destinations 分布
   - self_loop_rate
   - mean_sim_along_chain と shuffle_baseline_sim_mean (shuffle A 適用)
   - lift_over_baseline
   - atom_changes / chain
4. 解像度が細かくなるにつれて self_loop_rate が下がる、または lift > 0 が出るかを観察

**出力**: `observation_2_resolution.parquet` (per (scope, seed, resolution))

**期待される結果**:
- 解像度が細かくなると lift > 0 → window 単位での平均化が構造を均していた (観察 2 (b) 候補強め)
- 解像度を変えても lift ≒ 0 → 解像度の問題でない (観察 2 (a) 候補強め)

### 2.4 再調査 4 — self-loop の意味の分離

**問い**: self-loop 85% を「踏み台でない」と判定する前に、self-loop の意味を分ける。v1101a で確認した「踏み台 = 直前の認知的固定先への参照」は、必ずしも個体移動でなく、同じ個体への参照の連続も含む可能性。

**手順**:
1. self-loop chain (predecessor == attention_candidate の連続) と non-self-loop chain (predecessor ≠ attention_candidate の連続) を分離
2. それぞれで以下を算出:
   - chain 数
   - chain_length 分布
   - atom_changes / chain (self-loop でも atom が変わるか)
   - category_changes / chain
   - mean_sim_along_chain と shuffle_baseline_sim_mean (per (scope, seed))
   - lift_over_baseline
3. self-loop chain 内で「同じ cid だが rank_1_atom が変わる」ケースを抽出 (= cid 内部の atom 濃度が更新されている = 「同じ場所に留まりながら見え方が変わる」現象):
   - 該当 chain 数 / 全 self-loop chain 数 の割合
   - 該当 chain での atom_changes 分布
4. non-self-loop chain (5,930 chains 想定、15%) の lift を per (scope, n_members_bin) で算出

**出力**: `observation_2_self_loop_split.parquet` (per (scope, seed, is_self_loop))

**期待される結果**:
- self-loop chain でも atom が変わる割合が高い → 「同じ個体に留まる」でなく「同じ個体内で意味が動く」現象 (踏み台の別の形)
- non-self-loop chain (15%) で lift > 0 → 「個体移動を伴う踏み台」は 15% に存在
- self-loop も non-self-loop も lift ≒ 0 → どちらでも構造なし (観察 2 (a) 確度上がる)

---

## 3. 規律 — 再調査でも遵守すべき項目

### 3.1 既存出力流用のみ (絶対格言 #5)

新規 main run は禁止。本再調査は以下の既存出力の **再集計** のみ:
- `observation_2_predecessor_chain.parquet` (Step C 出力、39,537 chains)
- `attention_emit_seed{N}.parquet` (v1101a main、1.73M records)
- `alpha_membership_log_seed{N}.csv` / `alpha_lifecycle_log_seed{N}.csv` (v10.5)
- `cid_atom_sim_matrix_seed{N}.parquet` (v10.6)
- v10.6 trajectory (event / pulse / step10 / window 4 解像度)

### 3.2 物理層 frozen 絶対 (絶対格言 #2)

書込みは `unified/v1104/outputs/main/` 配下のみ。v10.x / v1101a / v1102 / v1103 main outputs は read-only。

### 3.3 判定語制限 (GPT 追加 4 継承)

Code A は本再調査でも「連想」と判定しない。cid / atom / category / similarity 推移と shuffle baseline 比較値の構造的事実のみ記録。

### 3.4 selector 化禁止 (GPT 修正必須 C 継承、本再調査では発生しないはず)

本再調査は観察 2 の再集計、観察 4 (B 現状確認) には触れない。selector 化リスクなし。

### 3.5 効果サイズで切る (絶対格言 #3)

|lift| > 0.01 を「有意」の閾値とする。z-score 単独評価は使わない。

### 3.6 集団平均の罠 / 層化必須 (絶対格言 #4)

再調査 1 の n_members × qc_gini 層化が本書の中核。層化軸を適用しない集計は本再調査では補助 (比較対照) としてのみ提示。

---

## 4. 確認要請 (Code A → Web Claude / Taka、Step A 同型)

### 4.1 確認要請 1 — CID scope の n_members_bin 引き方

再調査 1 で CID scope の chain を層化する際、cid_id に対応する n_members_bin を以下のいずれで引くか:
- (i) 所属する全 alpha / beta の n_members の中央値
- (ii) 所属する最大の Integration (alpha or beta) の n_members
- (iii) cid 単独の n_core_member (= cid 形成時の構成 cid 数、ESDE Genesis 由来)

Code A 仮所見は本書受領後、実環境照合の上で報告。

### 4.2 確認要請 2 — shuffle baseline 現状実装の単位

`v1104_step_c_observation_2.py` の shuffle baseline 実装で permutation 単位 (chain 内 / chain 間 / global) のどれを採用していたか、Code A 自身が確認して報告。

### 4.3 確認要請 3 — event 解像度の入力データの所在

v10.6 の event 解像度 trajectory が `developmental/v106/outputs/main/` 配下のどのファイルか、Code A 実環境で確認。`event_trajectory_seed{N}.parquet` のような命名と推測。

---

## 5. 進行 — Step H 再調査の流れ

| Step | 内容 | 想定 |
|---|---|---|
| Step H-2 認識確認 | 本書受領後、§4 確認要請 3 件への回答 + 再調査実装計画 | 半日 |
| Step H-2 反映 | 確認要請への Web Claude / Taka 回答後、最終確定 | 半日 |
| Step H-3 実装 1 | 再調査 1 (n_members × qc_gini 層化) | 半日 |
| Step H-3 実装 2 | 再調査 2 (shuffle baseline 3 種) | 半日 |
| Step H-3 実装 3 | 再調査 3 (chain 粒度 3 階層) | 1 日 |
| Step H-3 実装 4 | 再調査 4 (self-loop 分離) | 半日 |
| Step H-3 グラフ | 4 再調査の dashboard 追加 | 半日 |
| Step H-3 bit-identity | 既存 Step G に 4 再調査出力を追加検証 | 短時間 |
| Step H-3 観察事実報告 | judgment 回避 + 判定語制限遵守、再調査結果総括 | 半日 |

想定合計 **3-4 日**。本書の確認要請 3 件への回答後に着手。

---

## 6. 想定される再調査結果と Phase Result への影響

再調査 4 件すべての結果から、観察 2 の解釈が以下のように分かれる:

| パターン | 観察 2 の解釈 | Phase Result 方向 | 次主題 (v1105) 方向 |
|---|---|---|---|
| α: 再調査で lift > 0 が出る (層化 or 解像度 or non-self-loop で) | 観察 2 の元結果は観察方法の問題、ESDE 内部に踏み台はある | 観察 2 を (a) に修正、4 観察すべて (a) 寄り | 段 4-b Language 側噛み合わせ検証 |
| β: 全再調査で lift ≒ 0 | 観察 2 (a) 確定、ESDE 内部に「連想を辿る」構造はない | 観察 2 を (b) 確定、Phase Result 通り | 段 4-b 別機構 (relation_path 5 種) で再構築 |
| γ: self-loop で atom 変化が高頻度 (= 「同じ場所に留まりながら意味が動く」) | 踏み台の概念定義の見直し、個体移動を伴わない別の形 | 観察 2 を「連想とは別の構造」として再記述 | 段 4-b の概念再定義から始める新主題 |
| δ: sim_matrix が平らで shuffle が無効 | 観察 2 の数値自体が指標として機能していない、再観察設計が必要 | 観察 2 は判定保留、観察 1/3/4 のみで Phase Result 暫定 | 観察 2 の再設計 (sim 以外の指標) |

実際にどのパターンに落ちるかは Step H-3 実装結果次第。本設計書では事前判定を置かない。

---

## 7. Taka へのフィードバック (Phase Result 待機中の運用)

v1104 Phase Result (Step I) は本再調査の Step H-3 完了まで保留。次バージョン (v1105 候補) の主題確定も保留。

Taka が直接 Phase Result を急ぐ場合は、観察 1 / 3 / 4 のみで暫定 Phase Result を出すことも可能だが、Taka 判断「怪しいなと言う感情のまま先に進むといいことない」に従い、観察 2 の解釈が確定するまで全体保留が筋。

---

## 8. 一文サマリ

v1104 主題 Step H で観察 2 (predecessor 連鎖、lift=0、85% self-loop) について Taka が「構造的に作ってきたものが構造を辿れないなら観察方法を疑う」と判断し Phase Result + 次バージョンに待てがかかった状態で本書を Code A に発出、再調査 4 件 (1: n_members × qc_gini 層化を観察 2 にも適用 / 2: shuffle baseline の単位を chain 内・chain 間・global の 3 種で並列算出 + sim_matrix 平坦性確認 / 3: chain 粒度を window から step10 / event の 3 階層に細分化 / 4: self-loop chain と non-self-loop chain を分離して atom 変化と lift を別途算出) を既存出力流用のみで新規 main run なしで実施、規律 (絶対格言 #2/3/4/5 + GPT 追加 4 判定語制限 + GPT 修正必須 C selector 化禁止) を堅持、想定実装 3-4 日、確認要請 3 件 (CID scope の n_members_bin 引き方 / shuffle baseline 現状実装単位 / v10.6 event 解像度ファイル所在) への Code A 仮所見 + Web Claude 回答後に着手、想定結果は α (lift > 0 検出 → 観察 2 観察方法問題) / β (全 lift ≒ 0 → 観察 2 ESDE 事実確定) / γ (self-loop で atom 変化 → 踏み台概念再定義) / δ (sim_matrix 平坦で shuffle 無効 → 観察 2 判定保留) の 4 パターンで Phase Result と次バージョン方向が決まる、書込み unified/v1104/outputs/main/ 配下のみ、判定 (どのパターンか) は Code A は記録のみで Web Claude Phase Result + Taka 主題評価領域。

---

*以上、v1104 観察 2 再調査指示 (Web Claude、2026-05-23)。Code A 受領後、§4 確認要請 3 件への仮所見回答 → Web Claude / Taka 確定 → Step H-3 再調査実装の流れ。Phase Result + 次バージョンは本再調査完了まで保留。*
