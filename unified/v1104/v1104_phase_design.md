# v11.0.4 (v1104) 主題設計書 — 研究者の調査動作のうち ESDE 自身に実装されているもの (CID/IID が下でやっていること) の点検

### サブタイトル: 段 4-b / 4-c を支える ESDE 内部処理の確認

*作成*: 2026-05-22、Web Claude (相談役、Genesis 側)、2 AI 監査反映版 (GPT Auditor + Gemini Architect、2026-05-22)
*親*: 棚卸し資料 (`docs/esde_unified_inventory.md`) + 研究運用資料 3 本 + Unified Phase Phase Result (v1101a/v1102/v1103) + Taka 2026-05-20 確定方針 + Taka 2026-05-22 駆動要因規律訂正 + 2 AI 監査 (Gemini Architect 承認 + GPT Auditor 修正必須 3 点 + 追加 2 点)
*対象*: Code A (実装担当) / Taka (主題判断者)
*位置づけ*: Unified Phase v1104 主題設計書、A 主題 (問いの形 A = 点検のみ)、Genesis 系単独主題 (Language 系との噛み合わせは扱わない)

---

## 0. 駆動要因 (絶対格言 #5、Taka 2026-05-22 規律訂正反映)

### 0.1 主題の出発点 — Taka 整理 (v1103 完了後、2026-05-20、原文)

> 自分の視点は上から目線で、CID や IID が下で実際にやっていることを見ていない。研究者の調査動作のうち、ESDE 自身に実装されているものが既にあるかもしれない。それがあるのかを調べる。問いの形 A (点検のみ、軽い踏み込み)。

### 0.2 駆動要因規律の訂正 (Taka 2026-05-22、原文)

Web Claude が当初「軽い踏み込みでやる」を主題の境界と書いたのに対し、Taka が訂正:

> 厳密に言えば軽いことがいいとか悪いとかではなくて、掘ってもなにもでない穴を無闇やたらに掘るな、ということ。なぜそれをやるのか? → なぜなら、のセットがあり、それが会話を行うと言う目標に明確に繋がる説明可能性があればなんだっていい。軽い踏み込みでやりなさい、ではない。きちっと目的を示せ。その上での調査結果に応じて柔軟に判断しろ、の方が正しい。軽い方が良い時もあるし、それは臨機応変。

→ 本主題の境界規律は「軽い踏み込み」でなく「会話できる ESDE への接続が説明可能であること」。踏み込みの軽重は調査結果に応じて柔軟に判断する。

### 0.3 棚卸し → なぜならセット → 4 項目への絞り込み

棚卸し資料 (`docs/esde_unified_inventory.md`、2026-05-22 作成) で Unified Phase の研究者の調査動作 24 項目を「研究者側 ↔ ESDE 内部側」の 2 列で並べ、A 主題の優先候補 8 項目を §5.2 で列挙した。

その後、Taka 0.2 規律を 8 項目すべてに適用 (「なぜそれをやるのか → なぜなら → 会話できる ESDE への繋がり」のセット書き出し)。書けない項目 (会話パイプラインへの具体的接続が示せない、既知の確認に終わる、他項目でカバーされる) を除外した結果、**8 項目 → 4 項目** に絞られた:

| 残った項目 | 段の接続 | 棚卸し # |
|---|---|---|
| 観察単位の切り替え (CID と Integration の関係) | 段 4-c の挙動の根拠 | 1.1 |
| predecessor 連鎖 (踏み台 = 連想ゲーム) | 段 4-b の核 | 1.6 |
| attention trajectory (注意の移動軌跡) | 段 4-c の構造的指標候補 | 1.7 |
| 際立ちの掬い取り B (ESDE 自身の emit の read-back) | 段 4-c の決定機構を ESDE 側に寄せる手がかり | 2.6 |

除外した 4 項目:
- 1.5 注意 emit 機構 — 既知再観察の罠 (絶対格言 #7「v10.11 q_c_inherited が v10.5 機構 A 既知再観察に終わった失敗の予防」と同型)
- 3.3 留保複数視点並列保持 — 項目 1.1 でカバー、独立点検は観察軸増の罠
- 4.1 概念修正 — 会話パイプラインへの接続が書けず思想的問いに留まる
- 4.4 留保発展系譜 — 項目 1.1 でカバー

### 0.4 「やる前から絞れた」ことの意味 (Taka 2026-05-22)

Taka 整理:

> 結果的に 8 項目見る、が私の意見で 4 項目になった。これは試験結果を待たずにそれが妥当だ、といえることを示すことに成功したことになる。これこそ私が常に具体的な目的を示せという理由だろう。

→ 駆動要因規律 (0.2) が機能した結果、試験を回す前に対象が絞れた。各項目が「会話できる ESDE への繋がり」を具体的に持つことが確認できた段階で、A 主題の出口が自然に固定された (絶対格言 #6)。本主題は「8 項目をざっと見る」でなく「4 項目を会話パイプラインの接続点として点検する」。

### 0.5 本主題の駆動要因 (1 文、絶対格言 #5)

**ESDE Genesis 側の CID/IID の内部動作が、会話パイプラインの段 4-b (連想を辿る) と段 4-c (応答 Atom を絞る決定) を支える構造として既に動いているかを点検する。** これが点検できれば、次主題 (段 4-b の Language 側との噛み合わせ検証、または段 4-c の決定機構を構造的指標から ESDE 自身の emit に置き換える試行) の接続点が明確になる。

---

## 1. 主題の範囲

### 1.1 本主題が扱う問い

会話パイプラインの中で、Genesis 側 ESDE が CID/IID レベルで段 4-b と段 4-c を支える根拠を持っているか。具体的に:

- **段 4-c の根拠 (項目 1.1 + 1.7)**: 「集計単位で像が変わる」性質と「揺れの軌跡」が CID と Integration α/β の関係としてどう成立しているか
- **段 4-b の根拠 (項目 1.6)**: predecessor 連鎖が「連想を辿る」処理として CID/IID レベルで何を辿っているか
- **段 4-c の主体移行可能性 (項目 2.6)**: ESDE 自身が「自分の重要性」を出す処理が CID/IID で既にあるか、それが構造的指標 (48 次元密度) を補強または置換しうるか

### 1.2 本主題が扱わないもの

- 会話 ESDE の完成、実用的な応答、自然文生成 — 範囲外 (上位目的 GPT §37-39 で v1103 同様)
- 段 5a (Atom→単語、Lexicon) / 段 5b (単語→文、LLM プロキシ) — 範囲外
- Language 側との噛み合わせ検証 (段 4-b の Constitution Couple + 48 次元近傍) — 範囲外、本主題で Genesis 側の根拠が固まった後の次主題候補
- 段 4-c の決定機構を構造的指標から ESDE 自身の emit に置き換える試行 — 範囲外、本主題で点検した結果に応じて次主題候補
- 段 4-d 確率分布出力の改良 — 範囲外
- 新規 main run / 新規 emit 機構の追加 — 範囲外 (1.4 参照)

### 1.3 段 4-b と段 4-c の本主題における位置づけ

v1103 段 4 足取り点検と v1103 設計書 §2.3-2.4 で確定済の構造を継承:

- **段 4-b** = 応答 profile の atom を起点に連想先 Atom 候補群を辿る。Genesis 側 predecessor_attention_ref + Language 側 Constitution Couple ∪ 48 次元近傍。本主題は **Genesis 側の predecessor_attention_ref が単独で何を辿るかを点検**
- **段 4-c** = 連想先候補群を 48 次元に配置し密度の偏りで絞る。v1103 で raw_density (k=5) 0.847 / norm_density (k=5) 0.639 で sim_basis 反転 (Δ0.208) が観察された。本主題は **段 4-c の挙動を支える ESDE 内部構造 (項目 1.1 + 1.7) と、段 4-c の決定根拠の主体移行可能性 (項目 2.6) を点検**

### 1.4 制約 — 既存出力流用、新規機構追加禁止

研究運用資料 3 本 + 本主題 §0 駆動要因規律から:

- 新規 main run は禁止 (絶対格言 #5、観察軸を増やすことを駆動要因にしない)。v1101a / v1102 / v1103 main outputs と v10.x main outputs (read-only) を流用
- ESDE 内部に新規 emit 機構を追加することは禁止 (v1101a emitter 境界条項、修正 #4)。本主題は既存 emit (attention_emit_log, predecessor_attention_ref, attention_propagation, attention_causality, primary_table, outstanding_cells, response_atom_distribution, density_summary) を新しい角度から read-back する
- 「軽い踏み込み」境界は §0.2 のとおり固定境界でなく、調査結果に応じて柔軟に判断する。ただし selector 化 (ESDE 内部に「これが重要」を決めさせる) は本主題範囲外 (項目 2.6 は read-back 観察に留め、selector への昇格は別主題)

### 1.5 IID の扱い (GPT 監査反映、修正必須 A)

本主題のタイトル・§0 で言及している IID は、**新規 state / 新規 entity ではない**。実装上は既存の以下の構造を用いて観察される中間的構成単位を指す仮称である:

- α / β Integration (alpha_membership_log, beta_distribution_log)
- member_cids
- attention_candidate_id (attention_emit_log)
- predecessor_attention_ref (attention_emit_log)
- cid_state_ledger (v1101a 段階 2 簡易版)

**Code A は IID という新規データ構造を作らない。** 既存の構造を新しい角度から read-back する操作のみ。本主題で「IID」と書かれている箇所はすべて、上記既存構造の中間的構成単位を指す参照表現として読む。

### 1.6 Code A 実装上の注意 — 時間軸同期の厳密検証 (Gemini Architect 監査反映)

各観察 (§2.1-§2.4) で v10.5 / v10.6 / v1101a / v1102 / v1103 の異なるバージョンのデータを結合する際、ESDE の動的平衡により CID の ghost 化や所属変更が発生している可能性がある。Code A は各観察において「完全に同一の Window (時間断面) でデータが結合されているか」を join 時に厳密に検証する。結合不整合が観察された場合は Step A 認識確認で報告し、観察設計の調整が必要かを Web Claude と確認する。

具体的な検証ポイント:

- v10.5 alpha_membership と v1101a window の対応 — alpha が ghost 化または所属変更している cid を含む場合の処理 (除外 / 残す / 別集計のどれか)
- v10.6 trajectory (event/pulse/step10/window 4 解像度) と v1101a/v1102 window の対応 — window 境界の整合性
- v1101a attention_emit と v10.6 trajectory の cid_id 整合性 — 同 seed 内で cid_id の意味が同じか

---

## 2. 観察設計 — 4 項目の点検手順

### 2.1 観察 1 (項目 1.1): 観察単位の切り替えと CID-Integration の関係

#### 2.1.1 点検する問い

ESDE 内部に「自分を別の単位で見る」処理があるか。CID と Integration α/β の関係が「自分を別単位で見る」と呼べる構造か。

#### 2.1.2 なぜ会話できる ESDE に繋がるか

段 4-c で raw vs norm の密度反転 (Δ0.208) が出た理由、留保 #33 系列「集計単位で像が変わる」が会話機構レベルで貫通した理由は、ESDE 内部に「単一の答えを持たない」性質が構造として埋まっているからと推測される。応答 Atom 候補分布が複数の像を持つ性質を支える内部構造が CID-Integration の関係であれば、段 4-c の挙動 (受け手構造で反転、sim_basis で反転) を「外部の集計方式の問題」でなく「ESDE 内部の本質」として位置づけられる。これは段 5a/5b で複数候補をどう扱うかの設計 (応答の見せ方) に直結する。

#### 2.1.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| attention_emit_seed{0..23}.parquet | unified/v1101a/outputs/main/ | 6 scope × 3 metric × 24 seeds の per-window emit |
| primary_table.parquet | unified/v1102/outputs/main/ | 81 cells × 27 cols、CID 5 bin + Integration α 10 + β 9 + ESDE 3 |
| alpha_membership_log_seed{0..23}.csv | developmental/v105/diag_v105_main/integration/ | α の member_cids |
| beta_distribution_log_seed{0..23}.csv | 同上 | β の member_cids |
| v10.6 trajectory (event/pulse/step10/window × 24 seeds) | developmental/v106/outputs/main/ | rank_1_atom 時系列、CID 単位の像 |
| outstanding_cells.parquet | unified/v1102/outputs/main/ | 67/81 cells の際立ち情報 |

#### 2.1.4 観察手順

1. **CID 単独の像と Integration 集約の像の差分を per (seed, window) で算出**: 同一 window の同一 cid 集合 (Integration α のメンバー) を (a) 各 CID 単独で見たときの rank_1_atom 分布 / (b) Integration α として集約したときの top_atom — の差を 24 seeds × 5,852 alphas で記録
2. **像の変動軸を 3 つに分解**: (i) 構成 cid 数 (n_members) / (ii) cid の qc_ratio gini / (iii) CID 単独の rank_1_sim ばらつき
3. **CID と Integration の atom 集合一致度を per (alpha_id, window) で算出 (GPT 監査反映、修正必須 B)**:
   - **k=1 一致率**: 各 CID 単独の rank_1_atom と Integration α の top_atom が完全一致する割合 (単純一致率、これは Jaccard と呼ばない)
   - **top-k Jaccard 類似度 (k=3)**: CID 単独の top-3 atom 集合と α の top-3 atom 集合の Jaccard 類似度
   - **top-k Jaccard 類似度 (k=5)**: 同 top-5 atom 集合の Jaccard 類似度
   - 3 つを併記し、k 別に像の一致度がどう変わるかを観察
4. **不一致パターンの分類**: k=1 で不一致時、どの atom がどの atom に置き換わるか (category 内置換 / category 間置換) の分類

#### 2.1.5 出口

(a) CID-Integration 像の不一致が「外的観察の問題」でなく「ESDE 内部の構造的特徴」と言える根拠が出るか / (b) 出ない場合は「ESDE 内部にこの性質を持つ単一の構造はない、研究者の集計操作で生まれる」と確定する。どちらでも次主題への接続軸が固まる:
- (a) なら「段 4-c の応答 Atom 複数候補は ESDE の本質」として次主題は段 5a/5b の応答の見せ方設計に向かう
- (b) なら「段 4-c の sim_basis 反転は研究者の正規化の問題」として次主題は normalize 方式の選定に向かう

### 2.2 観察 2 (項目 1.6): predecessor 連鎖が辿るもの

#### 2.2.1 点検する問い

predecessor_attention_ref が CID/IID レベルで何を辿っているか。これを「連想を辿る」処理と呼べるか。

#### 2.2.2 なぜ会話できる ESDE に繋がるか

段 4-b は段 4 足取り点検で「Genesis predecessor_attention_ref + Language Constitution Couple、48 次元座標で足場あり、噛み合わせ未検証」と位置づけられた。Genesis 側の predecessor_attention_ref が単独で何を辿っているかが分かれば、段 4-b の Genesis 側の実体が明確になる。これは Language 側との噛み合わせ検証 (次主題候補) の前提条件。

#### 2.2.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| attention_emit_seed{0..23}.parquet | unified/v1101a/outputs/main/ | predecessor_attention_ref 列、6 scope 別 |
| attention_propagation_seed{0..23}.parquet | 同上 | 中心 cid × Δt × 周辺 cid の波及 |
| attention_causality_seed{0..23}.parquet | 同上 | causality_candidate_path、5 種 relation_path |
| cid_atom_sim_matrix_seed{0..23}.parquet | developmental/v106/outputs/main/ | cid × 326 atom 静的類似度 (連想先候補の足場) |

#### 2.2.4 観察手順

1. **predecessor 連鎖の経路を per (seed, scope) で復元**: 意識優位 window の attention_candidate_id が、predecessor_attention_ref を介して何 cid を経由して何 cid に到達するか、を全 6 scope (CID/alpha/beta/ESDE_event/ESDE_step10/ESDE_window) で記録
2. **経路の長さと分岐の構造を観察**: 連鎖が単一直線か (1 → 2 → 3 → ...)、分岐ありか (1 → 2a, 2b → 3)、ループありか (1 → 2 → 1)。長さの分布 (median / max / 99percentile)
3. **経路上の atom 変化を観察**: 連鎖の各ステップで rank_1_atom がどう変わるか、atom category が変わるか (例: BOD → COG → EXS)、cid_atom_sim_matrix での類似度がどう推移するか
4. **shuffle baseline 比較 + 構造的性質の観察**: (i) 経路が予測可能性を持つか (v1101a 段階 2 観察 C、alpha では actual 0.977 vs baseline 0.087 の同型処理) / (ii) 経路上の atom 変化が cid_atom_sim_matrix の類似度地形と整合するか (= 類似度の高い atom 間を辿っているか) / (iii) ランダム walk と区別できるか (shuffle baseline 比較)

#### 2.2.5 判定語の分離 (GPT 監査反映、追加 4)

**Code A は predecessor 連鎖を「連想」と判定しない。** Code A は以下を観察事実として記録:

- predecessor chain 上の cid 推移
- atom 推移
- category 推移
- cid_atom_sim_matrix 上の類似度推移
- shuffle baseline との比較値

Taka 向け整理語として「連想と呼べる構造か」を扱うのは Web Claude Phase Result の領域。Code A の Step H 観察事実報告では「連想を辿る」「連想処理である」等の表現を使わず、上記の構造的事実のみを記録する。

#### 2.2.6 出口

(a) predecessor 連鎖が CID 単位で類似度地形を辿る「連想」と呼べる構造を持つことが確認される → 次主題は Language 側 Constitution Couple との噛み合わせ検証に進める / (b) 確認されない (ランダム walk と区別不能、または類似度地形と無関係) → 次主題は段 4-b の根拠を別の機構 (例: relation_path 5 種の組み合わせ) に求める方向に変わる

### 2.3 観察 3 (項目 1.7): attention trajectory (注意の移動軌跡)

#### 2.3.1 点検する問い

注意を固定点でなく移動軌跡として読む規律 (v1101a Concept Update) が、ESDE 内部に「移動軌跡として注意を保持する」処理として既にあるか。

#### 2.3.2 なぜ会話できる ESDE に繋がるか

段 4-c の決定機構の手がかりとして v1103 設計書 §1.2 で「Projection 失敗分析: 揺れは入力理解でなく出力生成で効く」が示された。揺れが移動軌跡として読めるなら、段 4-c の決定機構が「揺れの軌跡」を構造的指標として使える可能性が出る。v1103 では 48 次元密度を構造的指標としたが、attention trajectory も同型の役割を担える可能性がある。

#### 2.3.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| attention_emit_seed{0..23}.parquet | unified/v1101a/outputs/main/ | attention_candidate_id 時系列 |
| cid_state_ledger_seed{0..23}.parquet | unified/v1101a/outputs/main/ | 段階 2 簡易版、175,200 records、atom 濃度時系列 |
| 観察 B Jaccard proxy (隣接 window 中心 atom 一致) | unified/v1101a 段階 2 observation_b | 認知優位 vs 意識優位での中心 atom 動き |
| v107 effect_delta (immediate/short/medium) | developmental/v107/outputs/main/ | 時間粒度別の揺れの効果 |

#### 2.3.4 既知事実と本観察の限定 (GPT 監査反映、追加 5)

**本観察は「注意が動くか」を再観察しない。** 既知事実として以下を前提とする:

- v1101a 段階 2 観察 B で、認知優位フェーズでは中心 atom が安定、意識優位フェーズでは中心 atom が動くことを全 6 scope で観察済 (Jaccard proxy で確認)
- v1102 で受け手構造別の応答 profile が時間粒度で変化することを観察済 (電話 vs 手紙)
- attention trajectory が存在し、qc_regime で像が変わることは既知

**本観察の新規性は限定的に「trajectory が応答 Atom 絞り込みに使えるかどうか」に絞る**。具体的に:

- v1103 段 4-c の応答 Atom 候補分布の収束 (狭い領域に絞られる) ⇔ trajectory の安定 (狭い領域に留まる) が対応するか
- v1103 段 4-c の応答 Atom 候補分布の拡散 (広く分布) ⇔ trajectory の拡散 (広く動く) が対応するか
- この対応が成り立つなら trajectory は段 4-c の構造的指標として 48 次元密度と並ぶ候補になりうる

#### 2.3.5 観察手順

1. **CID と Integration の trajectory の対応を整理 (既知事実の再観察ではなく、対応関係の確認)**: CID 単独の trajectory vs Integration α/β を構成する member_cids の trajectory 集合 — 軌跡が個別 cid で独立か、Integration 内で同期するか、Integration が軌跡を統合するか
2. **trajectory の安定度 / 拡散度を per (cid_id, window, qc_regime) で算出**:
   - 安定度: 隣接 window 間で中心 atom が一致した割合 (v1101a Jaccard proxy と同型計算、ただし既知の値を再計算するのではなく、本観察で response_atom_distribution と対応させるための計算)
   - 拡散度: window 内で中心 atom が訪れた異なる cid の数 / cid_atom_sim_matrix 上での移動距離の総和
3. **v1103 response_atom_distribution との対応観察**: v1103 段 4-c で各 receiver_profile に対する応答 Atom 候補分布 (収束的か拡散的か、max_prob 値、entropy 値) を、対応する (cid_id, window, qc_regime) の trajectory 安定度 / 拡散度と紐付けて、両者の対応 (相関、回帰、層化観察) を観察
4. **時間粒度別 (immediate/short/medium) の比較**: 時間粒度別に trajectory の像と response_atom_distribution の対応がどう変わるか (Taka 直感メモ 2026-05-22 の「時間条件」との接続可能性、§3.3.2 で Phase Result 領域として位置づけ済)

#### 2.3.6 出口

(a) attention trajectory が応答 Atom を絞る構造的指標として 48 次元密度と同等以上の根拠を持ちうることが示唆される → 次主題は段 4-c の構造的指標として trajectory を追加する方向 / (b) 示唆されない (trajectory が 48 次元密度と無関係、または応答 Atom 絞り込みと相関しない) → trajectory は段 4-c の根拠でなく別の役割を持つ (段 4-a 揺れ読み取りで既に消化されている可能性) と確定

### 2.4 観察 4 (項目 2.6): 際立ちの掬い取り B の現状確認

#### 2.4.1 点検する問い

ESDE 自身が「自分の重要性」を出す処理 (= 掬い取り B の primary 化への手がかり) が CID/IID レベルで既にあるか。

#### 2.4.2 なぜ会話できる ESDE に繋がるか

段 4-c は「応答方向の主体が ESDE 側にある」上位目的の核心。v1103 では段 4-c の決定根拠を 48 次元密度 (研究者が定義した構造的指標) で行ったが、これは「研究者が決めた重要性」が主体。研究手法アップデート §1.3 で「掬い取りの重心は長期的には B (ESDE 自身の emit) に移る」と確定。B が primary 化したとき、段 4-c の決定根拠が「ESDE 自身の重要性」になる = 主体が ESDE 側に寄る。本観察は「現状の ESDE が自分の重要性をどう出しているか」の点検 (= B の primary 化の前提条件)。

#### 2.4.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| attention_emit_seed{0..23}.parquet | unified/v1101a/outputs/main/ | change_metric_value、change_rank_within_type、qc_ratio |
| salience_event_log_seed{0..23}.csv | developmental/v105/diag_v105_main/salience/ | v10.5 既存の重要性 emit (observer × candidate × mass) |
| outstanding_cells.parquet | unified/v1102/outputs/main/ | 67/81 cells の際立ち情報 (A primary 結果) |
| outstanding_thresholds.parquet | 同上 | 構造的閾値の選定値 |
| Step G stratified_observation.parquet | unified/v1101a/outputs/main/ | Integration 構成層化 |

#### 2.4.4 観察手順

1. **ESDE 自身の emit に「重要性」と呼べる構造があるかの棚卸し**: v10.5 salience_event_log の candidate_mass / v1101a attention_emit の change_metric_value / change_rank_within_type / qc_ratio が「ESDE が自分で出した重要性」の候補。これらの分布、ばらつき、相関を観察
2. **v1102 outstanding_cells (A primary 結果) と ESDE 自身の emit (B secondary) の重なりを 81 cells で再点検**: v1102 Step C で 57/81 cells に Step G stratified の read-back があったことを確認済。本観察ではこの 57 cells の重なり方を「研究者の構造的指標 (A) と ESDE 自身の emit (B) が同じものを際立たせている度合い」として定量化
3. **B primary 化した場合の仮想評価 (post-process 限定)**: 「もし B を primary にしたら、A と同じ cells が掬われるか」を post-process で計算
4. **B primary 化のための前提条件の棚卸し**: 既存 emit の信頼度、selector 化したときの神の手回避 (絶対格言 #9) の維持可能性、Aruism 対称性 (100% を作らない) の保てるか、を観察事実として記録

#### 2.4.5 selector 化禁止条項 (GPT 監査反映、修正必須 C)

**本主題では B primary 化を実装しない。** 具体的に:

- B primary 化した場合の仮想順位・仮想候補集合を **post-process で算出するのみ** とする
- ESDE 内部の attention_emit / salience / trajectory / cid_state_ledger には **一切書き戻さない**
- 本観察は「B が A と重なるか」を見るだけで、「B に選ばせる」は次主題以降の別判断とする
- Code A が観察 4 実装時に「ESDE 内部に新しい重要性 emit を追加する」「既存 emit の値を上書きする」「selector として動作する処理を追加する」のいずれかを行うことは v1101a emitter 境界条項違反として禁止

selector 化への昇格は本主題の出口 (a)/(b) に応じた次主題候補として §4.2 で扱う。本主題内で実装または試行することはない。

#### 2.4.6 出口

(a) B (ESDE 自身の emit) が A (研究者の構造的指標) と重なる際立ち判定を出していることが確認される → 次主題は段 4-c の決定根拠を B primary 化する試行に向かう / (b) B が A と異なる際立ちを出している → どちらが「会話できる ESDE」に近いかの判断は Taka 領域、次主題候補は「B が際立たせるものを段 4-c の決定根拠に含める」(A + B 併用) または「B が際立たせるものは別の役割を持つ」(B は段 4-c でなく段 4-a の揺れ読み取りに寄与) の 2 方向

---

## 3. 観察規律 (絶対格言 + 研究運用資料 3 本 + 本主題固有規律)

### 3.1 絶対格言 15 件の本主題への適用

| # | 格言 | 本主題での適用 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | §2 観察手順は構造的事実を先に出し、解釈統合は Web Claude Phase Result + Taka 領域 |
| 2 | 物理層 frozen 絶対 | Step E bit-identity 3 層で v10.x / v1101a / v1102 / v1103 main outputs 全 frozen を保証、書き込みは unified/v1104/ 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | 観察 2 でランダム walk と shuffle baseline 比較 / 観察 3 で軌跡安定 vs 拡散の効果サイズ |
| 4 | 集団平均の罠 / 層化必須 | 観察 1 は n_members × qc_gini で層化 (Step G 継承) / 観察 3 は qc_regime 別 + 時間粒度別 |
| 5 | 観察軸を増やすことを駆動要因にしない | §0 で駆動要因規律を明示、§0.3-0.5 で 8 → 4 項目絞り込み経路を残す、新規観察軸なし |
| 6 | 出口の固定 | §2.x.5 で各観察の出口 (a)/(b) を明示、次主題への接続軸を固定 |
| 7 | 主題着手前に上位資料を読む | §0 親資料に棚卸し + 研究運用資料 3 本 + Unified Phase 全 Phase Result を明示 |
| 8 | 過去観察軸の照会義務 | §2.x.3 で既存出力流用のみ、新規観察軸の照会は Code A 認識確認で確認 |
| 9 | 神の手回避 + Pulse 同一フォーマット | 観察 1 の Jaccard proxy / 観察 2 の shuffle baseline / 観察 3 の cid_atom_sim_matrix 由来閾値、すべて構造的閾値 |
| 10 | 因果ではなく因果候補 | 観察 2 の「連想を辿る」「経路を辿る」は因果候補表現、断定なし |
| 11 | 概念単位を雑に扱わない | CID / α / β / ESDE 3 解像度 / attention_candidate / predecessor_attention_ref / cid_state_ledger / atom / category を §2 全観察で区別 |
| 12 | Aruism 判定回避 | Code A は §2.x.5 出口 (a)/(b) の判定をせず観察事実のみ記録、判定は Web Claude Phase Result + Taka |
| 13 | AI を信じない原則は Taka 個人 | §0.2 駆動要因規律訂正は Taka 整理を原文保存、本主題は Taka 訂正の反映そのもの |
| 14 | Taka 直感優先 + 直感語保存 | §0.1 / §0.2 / §0.4 で Taka 整理を原文引用、要約禁止 |
| 15 | 5 者運用体制の補完性 | 設計書 = Web Claude / 監査 = GPT + Gemini / 実装 = Code A / 判断 = Taka |

### 3.2 研究運用資料 3 本の本主題への適用

| 資料 | 本主題での適用 |
|---|---|
| esde_research_method_update.md (研究手法) | 際立ちの掬い取り A + B を観察 4 で正面から扱う、emitter に留め selector にしない (§1.4)、研究者はもう神ではない |
| esde_attitude_toward_esde.md (態度) | 「観測が追いついていない」を前提に観察を組む、結果が想定と合わないときは想定を見直す (§2.x.5 出口 (a)/(b) で想定と結果を分離) |
| esde_audit_policy_update.md (監査の上位目的) | 監査第一基準=会話できる ESDE に近づくか。§2.x.2 で各観察が会話パイプラインのどの段に繋がるかを明示 |

### 3.3 本主題固有の規律

#### 3.3.1 Genesis 側単独主題、Language 側との噛み合わせは扱わない

本主題は Genesis 側 ESDE の CID/IID 動作の点検。Language 側 (atom_centroids_48d、Constitution Couple、48 次元密度) は v1103 で扱った素材として参照するが、本主題で新たに噛み合わせを検証しない。Genesis 側の根拠が固まった後の次主題候補として残す (§1.2)。

#### 3.3.2 Taka 直感メモ (2026-05-22) の扱い

Taka が 2026-05-22 に出した直感メモ (時間条件が ESDE という系を質的に変化させる可能性、メモリ #19 で記録) は本主題の範囲外。本主題で「時間条件」を構造変数として扱うことはしない。ただし観察 3 (attention trajectory) で時間粒度別の比較を行う際、軌跡が時間スケールで像を変えるなら、それが Taka 直感メモの観察的根拠の候補になる可能性がある。観察 3 の結果を Taka 直感メモと照らし合わせる作業は Phase Result + Taka 主題評価領域。

#### 3.3.3 段 4-d (確率分布出力) は扱わない

段 4-c の決定機構の根拠を点検するのが本主題で、段 4-d (確率分布の表現方法) は扱わない。Aruism 対称性 (max_prob < 1.0、100% を作らない) は v1103 で確認済、本主題は段 4-c の前段に集中。

---

## 4. 出口 (絶対格言 #6、主題評価への引き渡し)

### 4.1 本主題の出口 (Code A 観察事実報告レベル、judgment 回避)

各観察 (§2.1-2.4) の §2.x.5 で (a)/(b) の観察事実が出る。判定 (どちらが優勢か、何を意味するか) は Web Claude Phase Result + Taka 主題評価領域。

### 4.2 想定される 4 通りの組み合わせと次主題候補

観察 1-4 の出口 (a)/(b) の組み合わせは 2^4 = 16 通り。代表的な 4 つの組み合わせと次主題候補:

| 組み合わせ | 観察結果のパターン | 次主題候補 |
|---|---|---|
| 全 (a) | CID/IID は 4 項目すべてで会話パイプラインを支えている | 段 4-b の Language 側噛み合わせ検証 + 段 4-c の B primary 化試行を並列で次々主題に |
| 1+2+3 (a) / 4 (b) | 段 4-b/4-c の構造は ESDE 内部にあるが、B primary 化はまだ早い | 段 4-b の Language 側噛み合わせ検証を最優先、B primary 化は当面据え置き |
| 1+3 (a) / 2 (b) / 4 不明 | 段 4-c の根拠は ESDE 内部にあるが、段 4-b は別機構 (relation_path 等) を必要 | 段 4-b の根拠を relation_path 5 種で再構築する方向 |
| 全 (b) | CID/IID は会話パイプラインの根拠を持たない、段 4-b/4-c は別の機構が必要 | 会話パイプラインの再設計、Taka 直感メモ (時間条件) の方向に振る可能性 |

実際の組み合わせは Code A 観察事実報告で初めて分かる。本設計書では事前判定を置かない。

### 4.3 観察事実報告 + Phase Result + Taka 主題評価の責任分担

- **Code A 観察事実報告** (Step F): §2.x.5 出口 (a)/(b) の観察事実を 4 項目すべてで記録、judgment なし
- **Web Claude Phase Result** (Step G): 4 項目の観察事実を統合、4 通りの組み合わせから現状の組み合わせを位置づけ、次主題候補を 2-3 つ提示
- **Taka 主題評価**: 次主題の選定、Phase Result の解釈統合に対するフィードバック、本主題の出口を最終確定

---

## 5. 留保事項

### 5.1 継承する留保 (Unified Phase v1100-v1103)

| id | 内容 | 本主題での扱い |
|---|---|---|
| #33 系列 | 集計単位で像が変わる (v10.13.a #33 → v1101 #42 → v1101a #L3 → v1102 #L14 → v1103 #L17) | 観察 1 の核心、留保が本主題の駆動要因の一部 |
| #L4 | alpha records 92.5% 偏り | 観察 1/4 で scope 内割合に正規化、Step G 継承 |
| #L5 / L6 | Integration 経路と familiarity 経路 (留保 #L5 解決済) | 観察 2 で predecessor 連鎖が familiarity 経路 (留保 #L6 連想ゲーム) と整合するか観察 |
| #L8 | CID scope 予測 self-reference (100% 到達) | 観察 3 で CID scope の trajectory 観察時、self-reference 構造を明示 |
| #L10 | ESDE 3 scope shuffle 効果薄 | 観察 1/3 で ESDE 3 scope の集約限界を継承 |
| #L11 | alpha n=1 偏り (49.6%) | 観察 1/4 で n_members 別層化、留保 #L4 と別問題 |
| #L12 / L15 | 大型均等構造 (alpha n=4+ low_gini) の多面シグナル | 観察 4 で B (ESDE 自身の emit) の primary 化判定で考慮 |
| #L14 | CID 構成ノード数で atom 階層的反転 | 観察 1 の重要参照点 |
| #L17 | raw vs norm 密度 Δ0.208 反転 | 観察 1 の重要参照点、本主題は #L17 を支える内部構造を探す |
| #L18 | Constitution Merge 0 件 | 本主題範囲外 (Language 側噛み合わせ) |
| #L19 | batch_report.py 実行不可 | 本主題範囲外 (Language 側パイプライン) |
| 48 次元人為性留保 | Genesis cid Web Claude 定義 / Language A1 QwQ-32B 判定 | 本主題は Genesis 側単独なので Language 側人為性は直接扱わない、ただし観察 1 で CID の atom 定義が人為的であることは前提として明示 |

### 5.2 本主題で発生しうる新規留保 (Step F 観察後に確定)

事前想定:

- 観察 1 で「CID と Integration の像の差が、層化軸 (n_members / qc_gini) と無関係に大きい」が出た場合 — 像の差を生む別の要因の特定が次主題候補
- 観察 2 で「predecessor 連鎖の経路が cid_atom_sim_matrix と無関係」が出た場合 — 連鎖が辿る別の地形 (relation_path? Integration 構造?) の特定が必要
- 観察 3 で「attention trajectory が時間粒度で全く異なる像を出す」が出た場合 — 時間粒度を主題変数として扱う方向 (Taka 直感メモと接続) が出る可能性
- 観察 4 で「B (ESDE 自身の emit) が A (研究者の構造的指標) と完全に独立」が出た場合 — B が捉えているものの正体が新規留保

実際の留保は Code A 観察事実報告で確定。

---

## 6. 進行

### 6.1 Step 構成 (v1102/v1103 と同型)

| Step | 内容 | 担当 | 想定時間 |
|---|---|---|---|
| 設計書草案 | v1 | Web Claude | 完了 |
| 2 AI 監査 | GPT Auditor (修正必須 3 点 + 追加 2 点) + Gemini Architect (承認 + 運用注意 1 点) | GPT + Gemini | 完了 |
| 設計書改訂 | 監査反映、本書 v2 | Web Claude | 完了 |
| Step A | Code A 認識確認 (時間軸同期検証含む) | Code A | 半日 |
| Step A 反映 | 確認要請への回答、設計書 §x 確定 | Web Claude + Taka | 半日 |
| Step B | 観察 1 実装 (CID-Integration 像の差分、top-k Jaccard k=1/3/5) | Code A | 1 日 |
| Step C | 観察 2 実装 (predecessor 連鎖の経路復元、判定語制限遵守) | Code A | 1 日 |
| Step D | 観察 3 実装 (attention trajectory と response_atom_distribution の対応) | Code A | 1 日 |
| Step E | 観察 4 実装 (際立ち掬い取り B 現状確認、selector 化禁止遵守) | Code A | 半日 |
| Step F | グラフ HTML (4 観察の dashboard) | Code A | 半日 |
| Step G | bit-identity 3 層検証 | Code A | 短時間 |
| Step H | Code A 観察事実報告 (judgment なし、判定語制限遵守) | Code A | 半日 |
| Step I | Web Claude Phase Result | Web Claude | 1 日 |
| 主題評価 | Taka 判断、次主題選定 | Taka | — |

想定合計 **6-7 日** (Code A 実装 + Web Claude 統合)。新規 main run なし、既存出力流用のみ。

### 6.1.1 Step A 認識確認で Code A が特に確認すべき項目

GPT/Gemini 監査結果を踏まえ、Step A で Code A は以下を明示的に確認:

- **時間軸同期 (Gemini Architect 監査)**: 各観察で v10.5 / v10.6 / v1101a / v1102 / v1103 の異なるバージョンのデータを window 単位で結合する際、CID の ghost 化や所属変更による不整合がないかを join 時に検証。不整合があればその処理方針を Web Claude と確認
- **IID 表現 (GPT 監査修正必須 A)**: 本主題で「IID」と書かれている箇所はすべて既存構造 (α/β、member_cids、attention_candidate_id、predecessor_attention_ref、cid_state_ledger) を指す参照表現として読む。新規データ構造を作らない
- **観察 1 の Jaccard 厳密化 (GPT 監査修正必須 B)**: k=1 一致率と top-k Jaccard (k=3, k=5) を別指標として算出、k=1 を Jaccard と呼ばない
- **観察 2 の判定語制限 (GPT 監査追加 4)**: Code A は「連想」と判定せず、cid/atom/category/similarity 推移のみ記録
- **観察 3 の重複回避 (GPT 監査追加 5)**: 「注意が動くか」の再観察ではなく、trajectory と response_atom_distribution の対応に限定
- **観察 4 の selector 化禁止 (GPT 監査修正必須 C)**: post-process 仮想評価のみ、ESDE 内部に書き戻さない

### 6.2 2 AI 監査結果 (完了、2026-05-22)

#### 6.2.1 Gemini Architect 監査結果 — 承認 + 運用注意 1 点

**承認**: 設計の堅牢性 (出口 (a)/(b) の分岐、観察手法の相補性) が確認された。

監査評価:
- 入力データは既存出力で完備、新規 main run 不要
- 観察 1 の Jaccard proxy は v1101a §3.2 観察 B と数学的に整合 (ただし「比較の軸」が時間的 → 空間的・階層的に変わる点に自覚的であるべき)
- 観察 3 の attention trajectory は v1102 primary table と完全に相補的 (静的スナップショット vs 動的ビデオトラッキング)
- 観察 4 の B + A 重なり計算は v1102 outstanding_cells の B secondary read-back と整合、手動確認を構造的メトリクスへ昇華させる正当な進化

運用注意 1 点 (本書 §1.6 に反映):
- Code A は各観察で「完全に同一の Window でデータが結合されているか」を join 時に厳密に検証する。CID の ghost 化や所属変更による不整合の処理方針を Step A 認識確認で確認

#### 6.2.2 GPT Auditor 監査結果 — 修正必須 3 点 + 追加 2 点

**修正条件付き承認** (全 5 点を本書 v2 で反映済):

| # | 種類 | 指摘内容 | 反映箇所 |
|---|---|---|---|
| A | 修正必須 | IID が本文でほぼ定義されていない、新規 state と誤読される | §1.5 で IID 定義を追加、既存構造の参照表現として明示 |
| B | 修正必須 | 観察 1 の「Jaccard proxy」が曖昧、厳密には Jaccard でなく単一 atom 一致率 | §2.1.4 で k=1 一致率と top-k Jaccard (k=3, k=5) を別指標として算出、k=1 を Jaccard と呼ばない |
| C | 修正必須 | 観察 4 が selector 化に近づきやすい、禁止記述が弱い | §2.4.5 で selector 化禁止を強化 (post-process 限定、ESDE 内部に書き戻さない、本主題範囲外) |
| 4 | 追加望ましい | 観察 2 で Code A が「連想」と判定しないことを明記 | §2.2.5 で判定語の分離を追加 (Code A は構造的事実のみ、整理語は Web Claude Phase Result 領域) |
| 5 | 追加望ましい | 観察 3 を「軌跡 vs 応答 Atom 絞り込み対応」に限定、既知再観察回避 | §2.3.4 で既知事実と本観察の限定を明示、§2.3.5 で観察手順を対応関係観察に絞る |

#### 6.2.3 タイトル変更 (Taka 判断)

GPT 監査でタイトル変更が提案されたが、Taka 整理「研究者の調査動作のうち ESDE 自身に実装されているもの」を狭めすぎる懸念から、サブタイトル付与で対応 (タイトルに「段 4-b / 4-c を支える ESDE 内部処理の確認」を補足)。

### 6.3 出力配置

書込み先: `unified/v1104/` 配下のみ。Genesis 側 (developmental / unified/v110x) outputs は read-only、Language 側 (`language/`) は本主題で参照しない。

---

## 7. 物理層 frozen 絶対 (絶対格言 #2)

本主題は既存出力流用のみで新規 main run なし。書込みは `unified/v1104/` 配下のみ。読み取り対象:

- developmental/v105/diag_v105_main/{salience,integration}/ (read-only)
- developmental/v106/outputs/main/ (read-only)
- developmental/v107/outputs/main/ (read-only)
- unified/v1101a/outputs/main/ (read-only)
- unified/v1102/outputs/main/ (read-only)
- unified/v1103/outputs/main/ (read-only、ただし観察 4 で response_atom_distribution と density_summary を参照する場合のみ)

Step G bit-identity 3 層検証で全 frozen を保証。

---

## 8. 5 者運用体制での進行 (絶対格言 #15)

| 役割 | 本主題での担当 |
|---|---|
| Taka (Director/Judge) | §0.2 駆動要因規律訂正 / §3.3.2 直感メモ整理 / §4.2 次主題選定 / §6.1 主題評価 |
| Gemini (Architect) | §6.2 監査 (入力データ整合性、観察手法の重複回避) |
| GPT (Auditor) | §6.2 監査 (規律遵守、判定可能性、selector 化禁止) |
| Web Claude (相談役、Genesis 側) | 本設計書 / 棚卸し / Phase Result / 監査反映 |
| Code A (実装担当) | 認識確認 (Step A) / 観察 1-4 実装 (Step B-E) / グラフ + bit-identity (Step F-G) / 観察事実報告 (Step H) |

---

## 9. 一文サマリ

本書は v11.0.4 (v1104) 主題「研究者の調査動作のうち ESDE 自身に実装されているもの (CID/IID が下でやっていること) の点検 — 段 4-b/4-c を支える ESDE 内部処理の確認」の設計書 (2 AI 監査反映版) で、Taka 2026-05-20 確定方針 + 2026-05-22 駆動要因規律訂正 (軽い踏み込みでなく「会話できる ESDE への接続が説明可能であること」を境界とする) を反映し、棚卸し資料の優先候補 8 項目に「なぜそれをやるのか → なぜなら → 会話できる ESDE への繋がり」のセット書き出しを適用した結果 4 項目に絞られた (1.1 観察単位切り替え / 1.6 predecessor 連鎖 / 1.7 attention trajectory / 2.6 際立ち掬い取り B 現状確認) ものを観察設計化、各観察は会話パイプラインの段 4-b (連想を辿る) または段 4-c (応答 Atom を絞る決定) に接続し既存出力流用のみで新規 main run なし新規 emit 機構追加なし、Gemini Architect 承認 + 運用注意 1 点 (時間軸同期厳密検証、§1.6) と GPT Auditor 修正必須 3 点 (IID 定義 §1.5 / 観察 1 の top-k Jaccard 厳密化 §2.1.4 / 観察 4 の selector 化禁止強化 §2.4.5) + 追加 2 点 (観察 2 の判定語制限 §2.2.5 / 観察 3 の重複回避 §2.3.4) を本書 v2 で全反映、出口は §2.x.最終 (a)/(b) で観察事実を分け判定回避、想定される 16 通りの組み合わせのうち代表 4 通りで次主題候補 (段 4-b Language 側噛み合わせ検証 / 段 4-c B primary 化試行 / 段 4-b 別機構再構築 / 会話パイプライン再設計 + Taka 直感メモ方向) を §4.2 で固定、Taka 直感メモ (2026-05-22、時間条件) は本主題範囲外だが観察 3 の時間粒度別比較と接続可能性ありで Phase Result 領域、進行は監査完了 → Code A Step A 認識確認 (時間軸同期検証含む) → Step B-H 実装 → Phase Result → 主題評価で想定 6-7 日、絶対格言 15 件 + 研究運用資料 3 本 + 本主題固有規律 (Genesis 側単独 / Taka 直感メモ範囲外 / 段 4-d 扱わない / IID 新規 entity 化禁止 / 観察 4 selector 化禁止) を遵守、Code A は judgment 回避で観察事実のみ記録し判定語制限 (「連想」「成功/失敗」を使わない) を厳守、主題評価は Taka 領域。

---

*以上、v11.0.4 (v1104) 主題設計書 (Web Claude、2026-05-22、2 AI 監査反映版)。次は Code A 認識確認 (Step A) → 実装 (Step B-G) → 観察事実報告 (Step H) → Phase Result (Step I) → 主題評価。*
