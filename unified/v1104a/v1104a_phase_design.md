# v11.0.4a (v1104a) 主題設計書 — CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検

### サブタイトル: v1104 段階 1 で見えた追加調整 4 件、観察 2/3/4 を scope × 層化で再点検

*作成*: 2026-05-23、Web Claude (相談役、Genesis 側)、2 AI 監査反映版 (GPT Auditor 修正必須 4 点 + 追加推奨 3 点、Gemini Architect 承認 + 運用注意 1 点)
*親*: v1104 設計書 v2 (`v1104_phase_design_v2.md`) + v1104 Step H 初版 + Step H-3 (観察 2 再調査) + Step H-4 (観察 3 再調査) + Taka 判断 (2026-05-23、追加調整 1-4 すべてを v1104a で扱う)
*対象*: Code A (実装担当) / Taka (主題判断者)
*位置づけ*: v1104 主題「CID/IID 内部動作点検: ESDE 自身は段 4-b/4-c を支える処理を既に持つか」の段階 2 (v1104 が段階 1)、観察方法依存の整理と scope × 層化による再点検。Phase Result は v1104a 完了後に v1104 本体と統合して 1 本書く。

---

## 0. 駆動要因 — なぜ v1104a を切るか

### 0.1 v1104 で見えたこと (Taka 整理 2026-05-23、原文)

> 主題の方向と言う意味だと、毎回言っている通り何をなんのために測っているか? がスタート。その結果、これがこうならこれが期待できそうだ、を掲げて次に進んでいく。そもそもテスト方法で結果が変わるというなら都合のよい結果を採択すればいいだけ。ただ、いくら都合よいといっても 0 を 1 にはできないだろうから妥協とのバランス次第。
>
> 2 回の再テストで結果で何ができそうか。これがあったらもっとよさそうだ、があれば再テストの中で再度調整すればいい。そこまで含めて本バージョンで扱う。次のバージョンアップが妥当なら次に進。

→ v1104 で観察 2 (Step H-3) と観察 3 (Step H-4) が **観察方法依存** と判明したのを受け、観察 1 の n_members 層化と観察 3 の scope-filter という「効くと分かっている観察方法」を観察 2/3/4 に適用し直す。これで v1104 主題の段 4-b/4-c 根拠点検を **観察方法の選択を含めた完全な形** で閉じる。

### 0.2 v1104 と v1104a の関係 (バージョン体系)

| バージョン | 内容 | 観察方法 |
|---|---|---|
| **v1104** (段階 1) | 4 観察 (1.1 / 1.6 / 1.7 / 2.6) を初点検 | 観察 1 のみ層化、観察 2/3/4 は pooled |
| **v1104a** (段階 2、本書) | 観察 2/3/4 を **scope × 層化** で再点検、観察 3 と v1103 48 次元密度を直接比較 | 観察 1 の経験則 (n_members 層化) と観察 3 の発見 (scope-filter) を全観察に統一適用 |

v1101 と v1101a が同じ主題の段階 1+2 だったのと同型。Phase Result は v1104a 完了後にまとめて書く。

### 0.3 「0 を 1 にはできない」の歯止め (Taka 規律)

観察方法を変えれば lift や r の数値は変動する。ただし元の構造がなければ、どんな観察方法でも 0 のままになる。v1104a で追加調整を入れた結果:

- 数値が顕在化する → 元々あった構造を見える観察方法を選んだ (本主題の出口は構造ありの方向)
- どの観察方法でも顕在化しない → 元の構造が薄いまたはない (本主題の出口は構造なしの方向)

どちらに転んでも、観察方法依存の構造事実として記録する。「観察方法を変えれば必ず数値が出る」を期待しない。

### 0.4 本主題の駆動要因 (1 文)

**v1104 で得た「何が効く観察方法か」の発見 (n_members 層化、scope-filter) を、観察 2/3/4 に統一適用することで、ESDE 内部の段 4-b/4-c を支える処理の地形を、観察方法を整えた完全な形で記述する。** これにより v1105 (観察 4 の B の意味を点検 + 段 4-b の Language 側噛み合わせ検証) の着手前に、Genesis 側の根拠地形が確定する。

---

## 1. 主題の範囲

### 1.1 本主題が扱う問い

v1104 の 4 観察すべてについて、観察方法を整えた完全版を作る。具体的に:

- **追加調整 1**: 観察 2 (predecessor 連鎖) を scope (CID/alpha/beta/ESDE) × n_members 層化で再点検
- **追加調整 2**: 観察 3 (trajectory ↔ response) を scope-filter × n_members 層化で再点検
- **追加調整 3**: 観察 3 の数値と v1103 48 次元密度を直接比較
- **追加調整 4**: 観察 4 (B の現状) を scope-filter で再点検

### 1.2 本主題が扱わないもの

- 観察 4 の B primary 化試行 (selector 化) — v1105 主題範囲
- 段 4-b の Language 側 Constitution Couple との噛み合わせ検証 — v1105/v1106 範囲
- 新規 main run / 新規 emit 機構の追加 — 範囲外 (v1104 と同じ)
- 新規観察項目の追加 — 範囲外。追加調整 1-4 はすべて v1104 既存観察への観察方法調整

### 1.3 v1104 既存知見の継承

| 知見 | v1104a での扱い |
|---|---|
| 観察 1 (CID-Integration 像、n_members で単調変化) | v1104a で再点検しない、確定済として継承。観察 1 の n_members 経験則を追加調整 1/2 で活用 |
| 観察 2 初版 (lift=0、shuffle A 依存) と Step H-3 (shuffle B/C で顕在化) | 追加調整 1 で scope × n_members を加える基盤として使用 |
| 観察 3 初版 (r=0.157) と Step H-4 (scope-filter で ESDE-only |r|=0.42-0.48) | 追加調整 2/3 の基盤として使用 |
| 観察 4 初版 (B subset、Recall 0.74、Precision 0.25) | 追加調整 4 で scope-filter を加える基盤として使用 |
| 留保 #L21' / #L22' / #L24-L29 (観察方法依存の構造事実) | v1104a で観察方法を更に整えた結果、新規留保が追加される可能性 |

### 1.4 制約 — 既存出力流用、新規機構追加禁止 (v1104 と同じ)

- 新規 main run 禁止 (絶対格言 #5)
- ESDE 内部に新規 emit 機構追加禁止 (v1101a emitter 境界条項)
- 既存出力 (v10.x / v1101a / v1102 / v1103 main outputs + v1104 outputs) の **再集計** のみ
- selector 化禁止 (観察 4 の追加調整も post-process 仮想評価に限定)

### 1.5 n-size 層化の定義 (GPT 監査反映、修正必須 B)

本書では n_members という語を **一括使用しない**。scope ごとに以下を使い分け、Code A は別列名で扱う:

| scope | 使用する n-size 列 | 定義 | bin |
|---|---|---|---|
| CID | **cid_n_core** | CID の core node 数 (v10.6 window_trajectory n_core_member 列) | n=2 / n=3 / n=4 / n=5+ |
| alpha / beta | **integration_n_members** | Integration を構成する member_cids 数 (alpha_lifecycle_log / beta_distribution_log から per-window 復元) | n=1 / n=2 / n=3 / n=4+ |
| ESDE 3 解像度 | (層化対象外) | 集約 scope のため n-size 層化対象外 | — |

Code A は cid_n_core と integration_n_members を同じ列名で扱わない。これは v10.12「path を雑にまとめた」問題 (絶対格言 #11 概念単位を雑に扱わない) と同系統の規律。

### 1.6 観察方法有利化との区別 (GPT 監査反映、追加推奨 7)

v1104a は、v1104 段階 1 で不利だった観察方法を有利な観察方法に置き換える主題ではない。v1104 で観察方法依存が判明 (Step H-3: shuffle 種別で lift が 0→0.17、Step H-4: scope-filter で |r| が 0.157→0.42-0.48) したため、**scope-filter と n-size 層化という既に効くことが見えた軸を、観察 2/3/4 に統一適用し、どこで構造が出てどこで出ないかを閉じる**主題である。

「結果が出る観察方法を探し続ける」のではなく「効くと分かっている観察方法を統一適用する」。これは Taka 規律「0 を 1 にはできない」と整合的な運用 (§0.3 / §3.3)。

### 1.7 Code A 実装上の注意 — CID の Ghost 化 NaN ハンドリング (Gemini Architect 監査反映)

CID は ESDE の動的平衡で消滅 (Ghost 化) する可能性があり、特定 window で対象 CID が有効な n_core_member を持たないケース (NaN / Null の発生) が起こりうる。Code A は Step A' 認識確認で以下の処理方針を明示:

- NaN ハンドリング (除外 / 残す / 別集計のどれか)
- v10.6 window_trajectory の per (cid_id, window) で n_core_member が欠損する条件 (Ghost 化 / 未形成)
- 欠損が発生した場合の chain の扱い (chain 全体を除外 / 該当 edge のみ除外)

これらは Step A' 認識確認で確定後、設計書 §1.7 に追記する。

---

## 2. 追加調整 4 件 — 何を測り、何が期待できるか

### 2.1 追加調整 1: 観察 2 を scope × n_members 層化で再点検

#### 2.1.1 何をなんのために測るか

観察 2 (predecessor 連鎖) を、shuffle B/C を維持したまま **scope (CID/alpha/beta/ESDE 3) × n_members 層化 (CID は n_core_member、Integration は n_members)** の組み合わせで再点検する。観察 3 の発見「ESDE/CID scope で対応強、alpha/beta で消失」が観察 2 にも当てはまるかを確かめる。

#### 2.1.2 これがこうなら、何が期待できるか

- (a) ESDE/CID scope で lift がさらに顕在化、alpha/beta で消失 → 段 4-b の連想を辿る処理が CID または ESDE 全体で動いている、と確定。観察 2 と観察 3 が同じ場所で動いていることが分かる
- (b) ESDE/CID scope と alpha/beta scope で観察 2 の挙動が変わらない → 観察 2 と観察 3 は別の場所で動いている、段 4-b と段 4-c の場所が異なる可能性
- (c) ESDE/CID scope の中で n_members 別に lift が変動 → 観察 1 の経験則 (n=2 と n=5 で像が違う) が観察 2 にも適用される

どの結果でも段 4-b の連想を辿る処理の **場所と構造** が具体化する。v1105 で段 4-b を扱うときの観察軸が確定する。

#### 2.1.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| observation_2_shuffle_variants.parquet | unified/v1104/outputs/main/ | shuffle B/C の lift (Step H-3 出力) |
| observation_2_restratified.parquet | 同上 | n_members × qc_gini の 27 bin (Step H-3 出力) |
| v10.6 window_trajectory n_core_member 列 | developmental/v106/outputs/main/ | CID scope の n_members 軸 |
| alpha_lifecycle_log / beta_distribution_log | developmental/v105 | Integration の n_members (per-window 復元、Step A 既存処理) |

#### 2.1.4 観察手順

1. observation_2_shuffle_variants.parquet の chain ごとに shuffle B と shuffle C の lift を **別集計** で取得 (B と C は平均で混ぜない)
2. 各 chain の scope と n-size_bin を join (§1.5 定義に従う: CID は cid_n_core、alpha/beta は integration_n_members、ESDE 3 解像度は層化対象外)
3. self-loop chain と non-self-loop chain を **分離** して記録、全体値は参考に留める (Step H-3 の chain-level full self-loop 比率 69.1% を継承)
4. (scope × n-size_bin × shuffle_type × is_self_loop) 別に lift_mean、|lift|>0.01 の判定を再計算
5. ESDE/CID scope と alpha/beta scope で lift がどう変わるか、n-size で更に変動するか、self-loop で挙動が変わるかを観察

**出力**: `observation_2_scope_stratified.parquet` (per (scope, n-size_bin, shuffle_type, is_self_loop))

### 2.2 追加調整 2: 観察 3 を scope-filter × n_members 層化で再点検

#### 2.2.1 何をなんのために測るか

観察 3 (trajectory ↔ response_atom_distribution) を、Step H-4 で見えた scope-filter (ESDE/CID で |r|=0.42-0.48) を維持したまま、**ESDE/CID scope の中で更に n_members 層化** で再点検する。ESDE 3 scope は集約 scope なので n_members 層化対象外、CID scope のみ n_core_member で層化。

#### 2.2.2 これがこうなら、何が期待できるか

- (a) CID scope の中で n_members 別に対応強度が変動 (例: n=2 で |r|=0.6、n=5 で |r|=0.3 など) → 観察 1 の経験則が観察 3 にも適用される、CID 単独の構造が n_members で変わることが段 4-c の決定機構に影響する
- (b) CID scope 全体で |r|=0.48 と同じ → 観察 1 と観察 3 は独立な構造、n_members は段 4-c の構造的指標として効かない
- (c) 特定の n_members bin で対応が消える、または逆転する → 段 4-c の決定機構が動く n_members の範囲が特定できる

v1105 で段 4-c の構造的指標 (trajectory) を使うときに、どの n_members 範囲で使えるかが確定する。

#### 2.2.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| observation_3_weighted.parquet | unified/v1104/outputs/main/ | scope-filter 結果 (Step H-4 出力) |
| trajectory_metrics_per_chain | unified/v1104/outputs/main/ | per-chain の stability / diffusion |
| response_atom_distribution | unified/v1103/outputs/main/ | per-receiver の max_prob / entropy |
| v10.6 window_trajectory n_core_member 列 | developmental/v106/outputs/main/ | CID scope の n_members 軸 |

#### 2.2.4 観察手順

1. observation_3_weighted の CID scope の per (cid, window) 行を抽出
2. 各行に cid_n_core を join (§1.5 定義)、4 bin (n=2/3/4/5+) に分割
3. (cid_n_core_bin) 別に stability_vs_maxprob、diffusion_vs_maxprob、stability_vs_entropy、diffusion_vs_entropy の Pearson + Spearman r を算出
4. **CID scope の cid_n_core 層化結果は、ESDE-only scope の参考値と必ず並べる** (GPT 追加推奨)。CID 内部で弱く、ESDE-only で強い場合は、集約によって trajectory-response 対応が強まる可能性を留保として記録
5. ESDE 3 scope は集約のため層化対象外、参考値として全体 |r| のみ再掲

**出力**: `observation_3_scope_n_stratified.parquet` (per (scope, cid_n_core_bin)) + 参考値 ESDE 全体 |r|

### 2.3 追加調整 3: 観察 3 の数値と v1103 48 次元密度を直接比較

#### 2.3.1 何をなんのために測るか

観察 3 (trajectory) と v1103 (48 次元密度 raw / norm) を **同じ receiver_bin 上で並べて**、どちらが応答 Atom 絞り込みを強く予測するかを比較する。段 4-c の構造的指標として trajectory が 48 次元密度と並ぶか、片方が強いか、を確定する。

#### 2.3.2 これがこうなら、何が期待できるか

- (a) trajectory の |r| が 48 次元密度の |r| を上回る (ESDE/CID scope で) → 段 4-c の構造的指標を trajectory に置き換える試行が v1105 で正当化される
- (b) 両者が同程度 → 段 4-c の構造的指標を **trajectory + 48 次元密度の併用** にする方向、複数の構造的指標で決定を多角化する
- (c) 48 次元密度が上回る → trajectory は補助的な指標、段 4-c の主力は 48 次元密度を継続使用

v1105 (または v1106) で段 4-c の構造的指標を ESDE 自身の emit (B primary 化) に置き換えるとき、現在の主力指標が何か、どこに伸びしろがあるかが確定する。

#### 2.3.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| trajectory_metrics_per_chain | unified/v1104/outputs/main/ | trajectory 側指標 |
| response_atom_distribution | unified/v1103/outputs/main/ | response 側指標 (max_prob / entropy) |
| density_summary | unified/v1103/outputs/main/ | 48 次元密度 (raw_density / norm_density / quality_weighted / receiver_conditioned 4 種) |
| receiver_profiles | unified/v1103/outputs/main/ | receiver_bin の対応 |

#### 2.3.4 観察手順 (GPT 監査反映、修正必須 C: 比較条件の固定)

**比較は同一 receiver_bin・同一 response 指標・同一 scope 上で行う。response は max_prob と entropy の 2 種に固定する。比較対象が揃わない行はランキング比較から除外し、coverage 欠損として記録する。**

1. receiver_bin 単位で trajectory metrics (stability / diffusion / chain_len / unique_count) と 48 次元密度 4 種 (raw / norm / quality_weighted / receiver_conditioned) を並べる
2. **同一 receiver_bin で両者の値が揃わない行を除外し、coverage 欠損として別途記録**
3. ESDE 3 scope と CID scope の **同一 scope** で、各 predictor × response (max_prob / entropy) の |r| を算出。response は max_prob と entropy の 2 種に固定 (top3_mass / gini は使わない)
4. (scope × predictor × response) 別に Pearson + Spearman を集計、|r| のランキングを作成。**異なる scope や異なる response 間で |r| を横並びにしない**
5. trajectory と 48 次元密度の競合関係を、同一条件下のランキングで構造的に記述

**出力**:
- `observation_3_density_comparison.parquet` (per (scope, predictor, response))
- `observation_3_density_coverage.parquet` (除外行の理由と件数)

### 2.4 追加調整 4: 観察 4 を scope-filter で再点検

#### 2.4.1 何をなんのために測るか

観察 4 (B が A の 74% カバー、4 倍広く際立たせる) を **scope-filter (CID/alpha/beta/ESDE)** で分けて再点検する。B が広いのが alpha/beta scope のノイズか、CID/ESDE scope での本質か、を切り分ける。

selector 化禁止条項 (v1104 §2.4.5) を維持: post-process 仮想評価のみ、ESDE 内部書き戻し 0。

#### 2.4.2 これがこうなら、何が期待できるか (GPT 監査反映、修正必須 D)

- (a) CID/ESDE scope で B と A が一致 (Precision 上昇)、alpha/beta scope で B が広い → B の広さは alpha/beta scope のノイズ、**CID/ESDE scope での B primary 化を次主題で点検する根拠が得られる**
- (b) CID/ESDE scope でも B が A より広い → B の広さは scope に依存しない、応答の方向を ESDE 側に寄せると候補が広がる方向に動く可能性 (判定は v1105)
- (c) scope によって B が捉える「A にないもの」が異なる → B が scope 別に異なる重要性を出している、scope-aware な利用が次主題で検討対象になる

**本主題では「B を selector として使える」「B が selector として使える可能性」と書かない**。言えるのは「B primary 化を次主題で点検する根拠が得られる」までとする。selector 化の可否は v1105 以降の別主題で扱う。

#### 2.4.3 入力データ (既存出力流用)

| データ | 所在 | 用途 |
|---|---|---|
| observation_4 出力 | unified/v1104/outputs/main/ | A primary 結果と B secondary の重なり (Recall/Precision) |
| outstanding_cells.parquet | unified/v1102/outputs/main/ | A primary の 23 cells |
| Step G stratified_observation.parquet | unified/v1101a/outputs/main/ | B (Integration 構成層化) |
| salience_event_log | developmental/v105 | B (candidate_mass) |
| attention_emit | unified/v1101a/outputs/main/ | B (change_metric_value / qc_ratio) |

#### 2.4.4 観察手順 (GPT 監査反映、追加推奨 6: B の意味判定は v1105 に送る)

**追加調整 4 は B が何を意味するかを判定しない。B が A と重なる範囲、B が A より広く拾う範囲、B が scope ごとに異なるかを構造的事実として記録するのみ。B の意味点検は v1105 の主題とする。**

1. observation_4 の 81 cells を scope-filter で 5 グループに分割 (all / CID / alpha / beta / ESDE)
2. 各グループで A∩B / A∪B / A\B / B\A を再計算、Jaccard / Recall / Precision を per-scope で算出
3. B が独自に際立たせる cell (B\A) の **件数と分布を scope 別に記録** (意味判定は行わない、内容の構造的記述に留める)
4. selector 化禁止: B primary 化の仮想評価は post-process のみ、ESDE 内部書き戻し 0。Code A は仮想評価の数値も記録するが「B primary 化が妥当か」の判定は行わない

**出力**: `observation_4_scope_filtered.parquet`

---

## 3. 観察規律 (v1104 から継承 + v1104a 固有)

### 3.1 v1104 規律の全継承

絶対格言 15 件、研究運用資料 3 本、GPT 監査 5 点、Gemini Architect 1 点、本主題固有規律 (Genesis 側単独、Taka 直感メモ範囲外、段 4-d 扱わない、IID 新規 entity 化禁止、観察 4 selector 化禁止) はすべて v1104a でも遵守。

### 3.2 v1104a 固有規律 — 観察方法を §0 で確定する

v1104 で観察 2 (Step H-3) と観察 3 (Step H-4) が観察方法依存と判明したのを受け、v1104a では **追加調整 1-4 すべての観察方法を §2 で事前確定** している。Code A は §2 の手順を逸脱しない (新しい層化軸や scope を追加しない、絶対格言 #5)。

新しい観察方法を試したくなった場合は v1104b として別バージョンを切る (Taka 判断)。

### 3.3 Taka 規律「0 を 1 にはできない」の運用

各追加調整の §2.x.2「これがこうなら、何が期待できるか」で (a)/(b)/(c) の 3 通りの分岐を明示済。**結果が予想と違うことを「観察方法を変えて 0 を 1 にする」方向に解釈しない**。

具体的に:
- 追加調整 1 で観察 2 の lift が ESDE/CID scope でも顕在化しなかった → (b) の出口 (観察 2 と 3 は別の場所で動いている) として記録、観察方法を更に変えて lift を探さない
- 追加調整 3 で trajectory が 48 次元密度に勝てなかった → (c) の出口 (trajectory は補助指標) として記録、別の比較指標を探さない
- 追加調整 4 で B の広さが CID/ESDE scope でも変わらなかった → (b) の出口 (B の広さは ESDE の本質) として記録、B を絞る加工を探さない

これは Taka 整理「都合のよい結果を採択すればいいだけ、ただし 0 を 1 にはできない」の運用。観察方法は事前に確定した範囲で結果を出し、結果が出ない場合はその事実を記録する。

---

## 4. 出口 — v1104a 完了後の Phase Result への引き渡し

### 4.1 v1104a 単独の出口

各追加調整の §2.x.2 で (a)/(b)/(c) の 3 通り分岐を明示済。Code A 観察事実報告 (Step H' 後継) で各追加調整の構造事実を記録。

### 4.2 v1104 本体と v1104a の統合 Phase Result

v1104 + v1104a 完了後、Web Claude が 1 本の Phase Result を書く:

- v1104 の 4 観察 (初点検) + v1104a の 4 追加調整 (観察方法を整えた完全版) を統合
- 段 4-b/4-c の Genesis 側根拠の確定 (場所 / 強度 / 構造的指標の優位性)
- 留保 refine + 新規留保確定
- v1105 主題 (観察 4 の B 意味点検 + 段 4-b Language 側噛み合わせ検証) への接続

### 4.3 v1105 への接続点 (v1104a 完了後に具体化)

| 追加調整の結果 | v1105 で扱う方向 |
|---|---|
| 追加調整 1 で観察 2 と 3 が同じ場所 | 段 4-b と段 4-c を同じ場 (CID または ESDE scope) で動かす設計 |
| 追加調整 3 で trajectory が 48 次元密度と並ぶか上回る | 段 4-c の構造的指標を併用または置換 |
| 追加調整 4 で B の広さが scope 別に異なる | B primary 化を scope-aware に試行 |

---

## 5. 留保事項

### 5.1 継承する留保 (v1104 Step H-3/H-4 出力)

| id | 内容 | v1104a での扱い |
|---|---|---|
| #L21' | predecessor 連鎖 lift=0 は shuffle 種別 A 依存 | 追加調整 1 で更に scope × n_members 層化 |
| #L22' | trajectory ↔ response の対応は scope 依存 | 追加調整 2 で CID scope の n_members 層化、追加調整 3 で 48 次元密度との比較 |
| #L24 | shuffle baseline 設計が観察事実を形成 | 追加調整 1 で shuffle B/C を維持して scope × n_members 層化 |
| #L25 | chain-level full self-loop 69.1% | 追加調整 1 で self-loop 分離を継承 |
| #L26 | 粒度 (event/step10/window) で atom_change_rate 7 倍変動 | 追加調整 1 では window 粒度に絞る (粒度 × scope × n_members は組み合わせ過多、絶対格言 #5) |
| #L27 | scope-mix 由来希釈 (観察 3) | 追加調整 2/3/4 で scope-filter を必須軸として全観察に適用 |
| #L28 | 層化単独効果限定、scope-filter が主効果 (観察 3) | 追加調整 1-4 で scope を主軸、層化を副軸 |
| #L29 | shuffle baseline は観察 3 で限定効果 | 追加調整 2 では shuffle baseline を主軸にしない |

### 5.2 本主題で発生しうる新規留保

事前想定 (Code A Step H' 後継で確定):

- 追加調整 1 で観察 2 の scope 依存が見えた場合、観察 1/2/3 の scope 依存が ESDE の共通性質か個別性質かの判定材料
- 追加調整 3 で trajectory と 48 次元密度が異なる方向を示した場合、段 4-c の構造的指標の選び方の留保
- 追加調整 4 で B が scope 別に異なる重要性を出した場合、selector 化の scope-aware 設計の留保

---

## 6. 進行

### 6.1 Step 構成

| Step | 内容 | 担当 | 想定 |
|---|---|---|---|
| 設計書草案 | v1 | Web Claude | 完了 |
| 2 AI 監査 | GPT Auditor (修正必須 4 点 + 追加推奨 3 点) + Gemini Architect (承認 + 運用注意 1 点) | GPT + Gemini | 完了 |
| 設計書改訂 | 監査反映、本書 v2 | Web Claude | 完了 |
| Step A' | Code A 認識確認 (NaN ハンドリング含む) | Code A | 半日 |
| Step A' 反映 | 確認要請への回答、§1.7 NaN 処理方針確定 | Web Claude + Taka | 半日 |
| Step B' | 追加調整 1 実装 (観察 2 scope × cid_n_core / integration_n_members 層化、self-loop 分離、shuffle B/C 別集計) | Code A | 半日 |
| Step C' | 追加調整 2 実装 (観察 3 CID scope の cid_n_core 層化 + ESDE-only 参考値並列) | Code A | 半日 |
| Step D' | 追加調整 3 実装 (観察 3 vs 48 次元密度、同一 receiver_bin / 同一 response / 同一 scope で比較) | Code A | 半日 |
| Step E' | 追加調整 4 実装 (観察 4 scope-filter、B 意味判定なし、selector 化表現なし) | Code A | 半日 |
| Step F' | グラフ HTML (追加調整 4 件の dashboard) | Code A | 半日 |
| Step G' | bit-identity 3 層検証 (LAYER_A 拡張) | Code A | 短時間 |
| Step H' | Code A 観察事実報告 (judgment 回避、判定語制限遵守) | Code A | 半日 |
| Step I (統合) | Web Claude Phase Result (v1104 + v1104a 統合) | Web Claude | 1-1.5 日 |
| 主題評価 | Taka 判断、v1105 主題確定 | Taka | — |

想定合計 **3-4 日** (Code A 実装 + Web Claude 統合)。新規 main run なし、既存出力流用のみ。

### 6.1.1 Step A' 認識確認で Code A が特に確認すべき項目

2 AI 監査結果を踏まえ、Step A' で Code A は以下を明示的に確認:

- **NaN ハンドリング (Gemini Architect 監査)**: v10.6 window_trajectory で CID の Ghost 化により n_core_member が NaN/Null になるケースの処理方針 (除外 / 残す / 別集計のどれか)、chain の扱い (chain 全体除外 / 該当 edge のみ除外)
- **n-size 列の使い分け (GPT 修正必須 B)**: cid_n_core と integration_n_members を別列名で扱う、ESDE 3 解像度は層化対象外、を Code A 自身が認識
- **追加調整 1 の self-loop 分離 + shuffle B/C 別集計 (GPT 追加推奨 5)**: shuffle B と C を平均で混ぜない、self-loop / non-self-loop 別集計
- **追加調整 3 の比較条件固定 (GPT 修正必須 C)**: 同一 receiver_bin / 同一 response (max_prob と entropy の 2 種) / 同一 scope で比較、coverage 欠損は別途記録
- **追加調整 4 の表現規制 (GPT 修正必須 D + 追加推奨 6)**: 「B を selector として使える」と書かない、B の意味判定をしない、観察事実のみ記録
- **観察方法有利化との区別 (GPT 追加推奨 7)**: 結果が出ない観察方法を更に変えない、事前確定範囲で結果を出す

### 6.2 2 AI 監査結果 (完了、2026-05-23)

#### 6.2.1 Gemini Architect 監査結果 — 承認 + 運用注意 1 点

**承認**: 設計の堅牢性 (v1104 観察方法依存を本主題内で処理、新規バージョンに逃がさない判断) が確認された。

運用注意 1 点 (本書 §1.7 に反映):
- 追加調整 1 で v10.6 n_core_member join 時の Ghost 化 NaN ハンドリング方針を Step A' で確定

**Gemini からのフォローアップ問い** (Trajectory が 48 次元密度を上回った場合、Genesis 内部の動態を Language 側にどう繋ぐか): v1104a 範囲外、v1106 以降の主題 (段 4-b の Language 側噛み合わせ検証) に直結する問い。本書 §4.3 v1105 接続点で記録。

#### 6.2.2 GPT Auditor 監査結果 — 修正必須 4 点 + 追加推奨 3 点

**修正条件付き承認** (全 7 点を本書 v2 で反映済):

| # | 種類 | 指摘内容 | 反映箇所 |
|---|---|---|---|
| A | 修正必須 | タイトル「完全版」が強すぎる | タイトルを「段階 2: 観察方法依存の整理と scope × 層化による再点検」に変更 |
| B | 修正必須 | CID の n_core と Integration の n_members を別列名で扱う | §1.5 で n-size 層化の定義を新規追加、cid_n_core と integration_n_members を別列名 |
| C | 修正必須 | 追加調整 3 の比較条件を同一 receiver_bin / response / scope に固定 | §2.3.4 で比較条件固定、response を max_prob と entropy の 2 種に限定、coverage 欠損別途記録 |
| D | 修正必須 | 追加調整 4 から「selector として使える可能性」表現を弱める | §2.4.2 で表現を「B primary 化を次主題で点検する根拠」に変更 |
| 5 | 追加推奨 | 追加調整 1 で self-loop / non-self-loop 分離 + shuffle B/C 別集計 | §2.1.4 で self-loop 分離と shuffle 別集計を観察手順に明示 |
| 6 | 追加推奨 | 追加調整 4 で B の意味判定は v1105 に送る | §2.4.4 で B の意味判定を行わないことを明示 |
| 7 | 追加推奨 | 「観察方法を有利化する主題ではない」を明記 | §1.6 で観察方法有利化との区別を新規追加 |

### 6.3 出力配置

書込み先: `unified/v1104a/` 配下のみ。v10.x / v1101a / v1102 / v1103 / v1104 main outputs は read-only。

---

## 7. 物理層 frozen 絶対

v1104a は既存出力流用のみで新規 main run なし。書込みは `unified/v1104a/outputs/main/` 配下のみ。読み取り対象は v1104 と同じ (v10.5/6/7 + v1101a/v1102/v1103 main outputs read-only) に加えて、v1104 outputs を read-only として追加。

Step G' bit-identity 3 層検証で全 frozen を保証 (LAYER_A は v1104 13 ファイル + v1104a 4 ファイル = 17 ファイル予定)。

---

## 8. 5 者運用体制での進行

| 役割 | v1104a での担当 |
|---|---|
| Taka (Director/Judge) | §0.1 駆動要因規律訂正の継承 / §3.3「0 を 1 にはできない」運用 / §4.3 v1105 接続点 / 主題評価 |
| Gemini Architect | §6.2 監査 (入力データ整合性、Step H-3/H-4 との計算同型性) |
| GPT Auditor | §6.2 監査 (規律遵守、判定可能性、selector 化禁止継承) |
| Web Claude (相談役、Genesis 側) | 本設計書 / v1104 と v1104a の統合 Phase Result / 監査反映 |
| Code A (実装担当) | 認識確認 (Step A') / 追加調整 1-4 実装 (Step B'-E') / グラフ + bit-identity (Step F'-G') / 観察事実報告 (Step H') |

---

## 9. 一文サマリ

本書は v11.0.4a (v1104a) 主題設計書草案で v1104 (CID/IID 内部動作点検) の段階 2 として観察方法を整えた完全版を扱い、Taka 整理「テスト方法で結果が変わるなら都合のよい結果を採択、0 を 1 にはできないので妥協とのバランス」と「再テストの中で再度調整できるならそこまで含めて本バージョンで扱う」を反映し v1104 で見えた追加調整 4 件 (1: 観察 2 を scope × n_members 層化で再点検 / 2: 観察 3 を CID scope の n_members 層化で再点検 / 3: 観察 3 と v1103 48 次元密度を直接比較 / 4: 観察 4 を scope-filter で再点検) を v1104 既存出力 + v10.x / v1101a / v1102 / v1103 read-only の組み合わせで実装、各追加調整は §2.x.2 で (a)/(b)/(c) の 3 通り分岐を明示し「これがこうなら何が期待できるか」を Taka 規律として事前固定、観察 4 の selector 化禁止 + 新規観察軸追加禁止 (§3.2) + 0 を 1 にはできない歯止め (§3.3) を遵守、Phase Result は v1104a 完了後に v1104 と統合して 1 本書く方針 (段階 1+2 を 1 つの Phase Result にまとめた v1101a と同型)、進行は 2 AI 監査 → Step A' 認識確認 → Step B'-H' 実装 → Phase Result 統合 → 主題評価で想定 3-4 日、絶対格言 15 件 + 研究運用資料 3 本 + v1104 GPT 監査 5 点 + Gemini 1 点 + 本主題固有規律 (Genesis 単独 / Taka 直感メモ範囲外 / 段 4-d 扱わない / IID 新規 entity 化禁止 / 観察 4 selector 化禁止 / 新規観察軸追加禁止 / 0 を 1 にはできない歯止め) を遵守、Code A は judgment 回避で観察事実のみ記録し主題評価は Taka 領域、書込み unified/v1104a/ 配下のみ。

---

*以上、v11.0.4a (v1104a) 主題設計書草案 (Web Claude、2026-05-23)。次は GPT + Gemini 2 AI 監査 → 設計書改訂 → Code A 認識確認 (Step A') の流れ。*
