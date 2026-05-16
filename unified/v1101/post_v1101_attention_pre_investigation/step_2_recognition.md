# v1101 後継主題候補「ESDE スケール注意機構」事前調査 — Code A Step 2 認識確認 + 事前齟齬指摘

*作成*: 2026-05-17、Code A
*親*: Web Claude 事前調査要望書 (本会話 2026-05-17 受領、未 repo 化)
*位置*: 要望書 §5.4 進行案 Step 2「Code A 認識確認 + 事前齟齬指摘」
*成果範囲*: 本書フレームと repo 実状の事前齟齬のみ。要望書 §2.A-G 本調査は Step 3 で別途
*バージョン番号*: 未確定 (Web Claude 要望書 §4 + §5.5 で Taka 主題確定後に決定)、仮配置 `unified/v1101/post_v1101_attention_pre_investigation/`

---

## A. 認識確認 (要望書要点)

| # | 項目 | 私の理解 |
|---|---|---|
| 1 | 本書性質 | **調査要望書** (設計書ではない)。Code A は判定回避 (success/fail なし)、§3 の 7 項目を 2 AI 監査入力資料として出す |
| 2 | 駆動要因 | 観察軸追加ではなく、v1101 で外から読み取った atom 像を ESDE 内部構造が **内生的に立ち上げる構造転換**。ただし「軸追加でないか」自体が監査論点 (§2.B + §5.2) |
| 3 | 最重要照会 | §2.B (v10.5 Salience-driven Focus / v10.7 attention_via_salience / v10.4 focus 候補との関係)。ここの結論が駆動要因の妥当性に直結 |
| 4 | frozen 境界 | §2.D の「派生記録に留める案」vs「構造形成フィードバック案」(v9.7 撤回前例) は Code A が両案の実装差を出すのみ、採否は Taka |
| 5 | Taka 領域 | §4 の 4 項目 (選択と集中対象 / 主体単位 / 構造形成 fb / バージョン番号) は Code A 埋めない |
| 6 | 範囲外 | 「生きた版」(時間が逐次進む) は今回範囲外、§2.F は簡易見立てのみ |

→ 認識相違なし、要望書フレームを Step 3 本調査の起点として受容可。

---

## B. 実環境軽照合 (Step 3 本調査前の予備)

`developmental/` 配下を 600 語以内の事実確認に絞って照合 (Explore agent 経由)。

| 照会 | 実在 | 所在 |
|---|---|---|
| v10.5 Salience mass = X.Q + X.C + β継承分 | **完全実在** | `developmental/v105/v105_salience.py:60-79` に式明記、`v105/diag_v105_main/salience/salience_event_log_seed*.csv` × 24 seeds 各 ~3,115 行 (7 列: seed/step/observer_cid/candidate_cid/candidate_mass/selected/event_type) |
| v10.5 salience 適用場面 | 実在 | `v105_salience.py:4-24` に **read_other / be3_fired / ingestion 摂食** の 3 系統明記、ingestion は mass-weighted random 選択 |
| v10.7 attention_via_salience path | 実在 | `developmental/v107/v107_path_analyzer.py:104-131` `build_attention_via_salience_targets()`、relation_strength = salience_mass_sum を observer×candidate 単位で run 全体累積 |
| v10.4 focus/attention 動的化候補 | **未発見** | `developmental/v104/v104_integration_alpha_beta_proposal.md` は **n_core 別 Integration bias** が主題で focus/attention 動的化記述なし |
| Q_at_decision / C_at_decision (balance_decisions) | 実在 | `v105/diag_v105_main/balance/balance_decisions_seed*.csv` (9 列) |
| Q_remaining_at_window_end / C_at_window_end (c_trajectory) | 実在 | `v105/diag_v105_main/balance/c_trajectory_seed*.csv` (9 列) |
| v10.7 attach_pre_event_state | **ファイル名相違** | `v107/` 配下に該名称なし、`baselines_with_delta_seed*.parquet` (11-18 MB/seed) が近い実体 |
| v10.13.a 5 phase 波及 | **3 phase で実装** | `developmental/v113a/` は immediate (1-10) / short (10-100) / mid (100-1000) の **3 phase**、5 phase 表記は実装に無い |
| ΣQ/ΣC 系全体集約 (per-step) | 直接出力なし | balance_decisions の cid 別 Q/C + v107/v108 event-level から post-process で算出可 |

---

## C. 事前齟齬指摘 (要望書フレーム vs repo 実状) — 5 件

v1101 Step A が齟齬 10 件を出したのと同型の作業。今回は **5 件**。

### 齟齬 1 (重要): v10.5 Salience は既に「内生的注意」を実装している

**要望書記述**: §0.2「v1101 で外から読み取った atom 像を ESDE 自身が内生的に持つ転換」(駆動要因)、§2.B「v10.5 が既存の cid レベル注意機構である可能性」

**実環境**: v10.5 Salience-driven Focus は **既に内生的注意機構として動作中**。`mass = Q + C + β継承分` を用いて read_other / ingestion / be3 の 3 場面で **mass-weighted 選択** を行っており、これは「ESDE が自分の内部状態に基づいて何を見るかを自動で決めている」構造。`salience_event_log` × 24 seeds が persistence 済。

**影響**: 要望書 §2.B が「最重要照会項目」と位置づけた通り。**駆動要因 (§0.2) の妥当性判定はこの一点に集約される**。v10.5 が既に answer に近いなら、本フレームは「v10.5 の cid → ESDE スケール集約 + 変化駆動拡張」であり、駆動要因の言葉を「内生化」から「スケール集約 + 変化軸の追加」に修正する必要がある可能性。これは Step 3 §2.B 本調査の結論待ち。

### 齟齬 2: v10.4「focus/attention 動的化主題候補」は repo 上未確認

**要望書記述**: §2.B「v10.4 主題候補に挙がっていた『focus/attention 動的化』」(駆動要因 §0.2 でも言及)

**実環境**: v10.4 の主題候補ドキュメント `v104_integration_alpha_beta_proposal.md` は **n_core 別 Integration bias** (be3 size 2 vs 3 の cluster 過大代表 ×4.16) が主題で、focus/attention 動的化の主題候補記述は **未発見**。`docs/ai_summaries/06b_developmental_phase15_summary.md` でも未確認。

**影響**: Web Claude memory に存在するが repo に persistence されていない可能性 (v1101 handoff §3.1 が同型問題を指摘済 — Taka 哲学 4 件も memory only)。Step 3 §2.B 本調査で確認、なければ駆動要因の根拠を 1 つ削る (絶対格言 #8 — 過去観察軸の照会で確認できなかった旨を明示)。

### 齟齬 3: v10.13.a は「5 phase 波及」ではなく「3 phase」

**要望書記述**: §2.C「v10.13.a の 5 phase 波及観察が変化測定のテンプレートとして流用できるか」

**実環境**: `developmental/v113a/` の Map 1-5 は **immediate / short / mid の 3 phase**。「5 phase」は Map 出力数 (5 ファイル) と phase 数 (3) の混同の可能性。

**影響**: Step 3 §2.C 本調査での流用検討に影響。実数は 3 phase。

### 齟齬 4: v10.7 attach_pre_event_state のファイル名相違

**要望書記述**: §2.A「v10.7 attach_pre_event_state の Q_pre / C_pre」

**実環境**: `v107/` 配下に `attach_pre_event_state` という名称のファイル/関数は無く、`baselines_with_delta_seed*.parquet` (event-level、Q_pre/C_pre 相当列含む可能性) が近い実体。

**影響**: 微細。Step 3 §2.A 本調査で正しいファイル名で参照する。

### 齟齬 5 (構造的、重要): 「主体を ESDE スケールに一つ置く」と v1101 核心発見の整合性

**要望書記述**: §1.6 構造化「ESDE 全体に注意機構を **一つ** 置く」、§4 で「主体をどの単位に置くか」を Taka 領域に箱出し

**実環境**: v1101 核心発見 (Step E / Step H) は「観察単位 (CID-static / β / α / ESDE event/step10/window) ごとに dominant atom が **5 つに分裂**」(CHG.begin / FND.logic / TIM.moment / WLD.artless+PER.sound / TIM.moment)。**ESDE スケール単一注意機構を置くことは「単位ごとに像が違う」を 1 つの像に潰す操作になる**。

**影響**: 構造的衝突の可能性。Taka 領域だが Code A は構造的事実として明示すべき (絶対格言 #11 — 概念単位を雑に扱わない)。Step 3 §2.D の「emitter / selector」境界調査 + §4 Taka 領域「主体単位」の判断に直接接続。**全構造単位 (cid / α / β / ESDE) が一律に注意記録を吐く emitter** に留めれば衝突回避可能だが、設計選択は Taka 領域。

---

## D. 本書自体への私からのフィードバック (Taka §3 OK 確認済)

Taka 判断 (2026-05-17): D-1〜D-5 は **Step 3 成果物作成段階で反映**、Web Claude へは渡さず Code A が成果物の中で反映する。

### D-1: §0.4 / §6 の一文サマリは超長文 (約 800 字)、未確定要素が多い調査要望書段階で確定済みのように読めるリスク。Step 3 成果物では緩い形を採用検討。

### D-2: §2.A-G が並列に書かれているが、§2.B 結論次第で他項目の意味づけが変わる。Step 3 進行を「§2.B 先行 → 結論を踏まえて §2.A / §2.C-G」の 2 段にする (E-2 で反映)。

### D-3: §3 成果物項目 7「駆動要因の検証」が末尾だが、最重要観察事実 (齟齬 1 参照)。Step 3 成果物では **#1 or #2** に置く。

### D-4: 要望書に v10.5 mass 式が事前記述されており、Code A の独立照合の意味が弱まる懸念。実環境照合では完全一致を確認したので結果オーライ。今後の同型調査要望書への提案として記録のみ。

### D-5: 「事前」調査と「本調査」の境界が要望書内で明示されていない。Step 2 で「軽い事前齟齬指摘」を求めているが §2.A-G を軽く照会するのか別の予備項目があるのか曖昧。今回は Code A 判断で §2.B / §2.A 一部のみ軽く照合した。今後の同型調査要望書への提案として記録のみ。

---

## E. Step 3 (本調査) 進行案 (Taka 1 OK 確定)

### E-1: 本調査進行は OK

齟齬 5 件は本調査の **障害ではなく、本調査で深掘りすべき方向** を絞った形。特に齟齬 1 (v10.5 が既存内生注意) と齟齬 5 (v1101 核心発見との整合性) は §2.B + §2.D 本調査で結論を出すべき項目。

### E-2: 本調査の進行順 (D-2 反映案、Taka 1 OK)

| 順 | 項目 | 内容 | 想定時間 |
|---|---|---|---:|
| 1 | §2.B 先行 | v10.5 Salience / v10.7 attention_via_salience / v10.4 focus 候補との関係を深掘り、駆動要因の妥当性を構造的に整理 | 1-2 時間 |
| 2 | §2.B 結論 trigger | 「v10.5 拡張なのか別物なのか」を明示 | (1 と同時) |
| 3 | §2.A / §2.E | Q/C 集約の実装可能性 + 因果/影響観察の既存基盤 (v10.7 流用可否) | 1-2 時間 |
| 4 | §2.C | 変化抽出の実装可能性 (4 解像度 trajectory + 連鎖・同期測定) | 1-2 時間 |
| 5 | §2.D | post-process 実装位置 + frozen 境界 + emitter/selector | 1 時間 |
| 6 | §2.F | 時間軸 (簡易見立てのみ) | 30 分 |
| 7 | §2.G | 新規 main run 要否 + 段階区分 + 想定時間 | 30 分 |
| 8 | §3 成果物作成 | 7 項目を markdown 化、§3 #7「駆動要因の検証」を最初に置く (D-3 反映) | 1-2 時間 |
| **合計** | | | **6-9 時間** |

新規 main run は不要見込み (既存出力で組める)。

### E-3: バージョン番号 + repo 配置先

要望書 §4 + §5.5 通り、Code A はバージョン番号を確定しない。Step 3 本調査終了後、Taka が **v11.0.1.a / v11.0.2** のいずれかを判断 → 配置先確定。Step 3 までは仮配置 `unified/v1101/post_v1101_attention_pre_investigation/` で進める。

### E-4: Taka 領域は埋めない

§4 の 4 項目 (選択と集中対象 / 主体単位 / 構造形成 fb / バージョン番号) は Step 3 本調査でも Code A は触れない。齟齬 5 (主体単位 vs v1101 核心発見) は構造的事実として明示するが、判断は Taka に渡す。

---

## F. 規律遵守チェック (絶対格言 15 件抜粋)

| # | 格言 | 本書での遵守 |
|---|---|---|
| 5 | 観察軸を増やすことを駆動要因にしない | 齟齬 1 で駆動要因の構造的問い直しを Step 3 §2.B 本調査の論点として明示 |
| 8 | 過去観察軸の照会 | §B 実環境軽照合で v10.5 / v10.7 / v10.4 の既存実装を所在 + 行番号で確認 |
| 11 | 概念単位を雑に扱わない | 齟齬 5 で「主体を一つに置く」操作の意味を v1101 核心発見と接続 |
| 12 | Aruism 判定回避 | 齟齬指摘は構造的事実のみ、success/fail なし、駆動要因の判定は Step 3 本調査 + Taka に委ねる |
| 13 | 主題判断は Taka | §4 Taka 領域 4 項目を Code A 埋めない宣言 |
| 14 | Taka 直感優先 + 直感語保存 | 要望書 §1 Taka 原文整理を引用形でなく要点参照のみ、原文は要望書本体 (未 repo 化) で保持 |

---

*以上、ESDE スケール注意機構 事前調査 Code A Step 2 認識確認 + 事前齟齬指摘 (Code A 2026-05-17)。Taka 確認後、E-2 進行順で Step 3 §2.B 先行 → §3 成果物作成 へ進む。仮配置 `unified/v1101/post_v1101_attention_pre_investigation/`、バージョン番号は Taka 主題確定後に決定。*
