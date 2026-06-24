# 07 Unified Phase Summary（統合版）

*統合*: 2026-06-25、Claude Code（枝番・追補を全文保存で本番号へ一本化）
*方針*: 内容は一切書き換えず、旧ファイルを時系列の Part として連結。各 Part 冒頭に旧メタ情報（作成/更新/親資料）を保持。見出しは衝突回避のため 1 段下げ。

ESDE Unified フェイズ（v10.13a 移行 〜 v13 child-world）の要約。旧 `07` 本体と 4 本の追記（v1105→注意センター転換 / 注意センター内部注意生成 / v12 Atomset→v12.1 ルーレット / v13 child-world）を時系列で一本化した。Developmental Phase（v10.x）は `06` を参照。

### 統合された Part 一覧

- **Part 0（v10.13a 〜 v1104a 本体）** — 07 Unified Phase Summary — v10.13.a + v1100 / v1101 / v1101a / v1102 / v1103 / v1104 / v1104a（旧 `07_unified_summary.md` 本体）
- **Part 1（v1105 〜 注意センター ESDE 転換）** — 07 Unified Phase Summary 追記 — v1105 〜 注意センター ESDE 転換（旧 `07_unified_summary_addendum_v1105_to_attention_center.md`）
- **Part 2（注意センター ESDE 内部注意生成成立）** — 07 Unified Phase Summary 追記 2 — 注意センター ESDE 機能設計から内部注意生成成立まで（旧 `07_unified_summary_addendum_2_attention_center_internal.md`）
- **Part 3（v12 Atomset 〜 v12.1 一致率ルーレット）** — 07 Unified Summary 追補 — v12 Atomset から v12.1（一致率の確率的選択）への区切り（旧 `07_unified_summary_addendum_v12_to_v121_roulette.md`）
- **Part 4（v13 child-world）** — 07 Unified Summary 追補 — v13 child-world（CID→物理 param の子系・統計監査・全検前段）（旧 `07_unified_summary_addendum_v1301.md`）


---

## Part 0（v10.13a 〜 v1104a 本体） — 07 Unified Phase Summary — v10.13.a + v1100 / v1101 / v1101a / v1102 / v1103 / v1104 / v1104a

*作成*: 2026-05-18、Web Claude (相談役)
*更新*: 2026-05-23、Web Claude — v1104 + v1104a 完了反映、4 つの非対称性 #L30-L33 確定、v1105/v1105a 主題確定、EVI 案保留、マイナーバージョン運用方針確定。
*母体*: `06c_developmental_v1013_v1101_summary.md` (Code A 作成 2026-05-17、v10.13.a + v1100 + v1101 を網羅) を格上げ・統合し、v1101a/v1102/v1103/v1104/v1104a を追加
*位置づけ*: Unified Phase が独立フェイズになったことに伴い新設された正式番号ドキュメント。従来 `06c` の枝番にぶら下がっていた Unified Phase 要約を `07` に格上げした。`06` 台 (06 / 06b / 06c) は Developmental Phase で完結・凍結。本書以降、Unified Phase の各主題は本書に追記して一本化する。
*親資料*: `06_developmental_summary.md` (v10.0-v10.9) + `06b_developmental_phase15_summary.md` (v10.4-v10.12、凍結) + `06c` (本書の母体、Developmental 完結時点で凍結)
*用途*: 新 Web Claude スレッド初見時に Unified Phase 全容 (v10.13.a 移行点 + v1100 Language 接続 + v1101 Atom 隆盛 + v1101a 注意機構 + v1102 受け手構造 + v1103 段 4-c + v1104+v1104a CID/IID 点検 + v1105/v1105a 準備) を把握する網羅的引き継ぎ。

---

### 0. ファイル番号体系の変更 (2026-05-18 → 2026-05-20)

Unified Phase の独立に伴い、ファイル番号を繰り上げた。Developmental Phase 追加時 (2026-04-28) に一度繰り上げたのに続く 2 度目の繰り上げ。さらに v1103 完了時に研究運用資料 3 本 (12/13/14) を追加。

| 旧番号 | 新番号 | ファイル | 性格 |
|---|---|---|---|
| — | **07** | `07_unified_summary.md` (本書、新設) | Phase 要約 |
| 07 | **08** | `08_concept_core.md` (旧 `07_concept_core.md`) | 概念要約 |
| 08 | **09** | `09_esde_system_structure.md` (旧 `08_esde_system_structure.md`) | 構造要約 |
| 09 | **10** | `10_audit_principles.md` (旧 `09_audit_principles.md`) | 監査原則 |
| 10 | **11** | `11_esde_language_summary.md` (旧 `10_esde_language_summary.md`) | Language 系要約 |
| — | **12** (候補) | `esde_research_method_update.md` (新設、2026-05-19) | 研究運用 — 観察手法の規律 |
| — | **13** (候補) | `esde_attitude_toward_esde.md` (新設、2026-05-20) | 研究運用 — 観察者の態度の規律 |
| — | **14** (候補) | `esde_audit_policy_update.md` (新設、2026-05-20) | 研究運用 — 監査の上位目的の規律 |

`06` / `06b` / `06c` は Developmental Phase 要約として据え置き・凍結。`01`-`05` (Genesis-Primitive) は変更なし。詳細は `00_index.md` の番号体系メモを参照。

**研究運用資料 3 本 (12/13/14)** は特定主題でなく研究全体の運用に関わる。研究手法 (12) ・観察者の態度 (13) ・監査の上位目的 (14) の三層で運用規律が揃った形。番号と配置は Taka 判断、`docs/ai_summaries/` 配下または別場所。

**資料運用方針 (2026-05-18〜19 確定)**: phase 単位の詳細仕様書は廃止する。ESDE Genesis 開発当初は Code A がいなかったため詳細仕様書を重視したが、現在は Code A の認識確認 → 要点まとめ → 齟齬詰め → 実装というプロセスが毎回回るため、詳細仕様書は実質不要。主題設計書 (design.md) は資料タイプが異なり重要なため継続し、仕様書フォルダに階層構造で保存する (v1101a から運用)。Unified Phase の新主題は枝番を増やさず本書 (07) に追記して一本化する。

---

### 1. 一文サマリ

ESDE は v10.12 (Phase 1.5 第七試行、2026-05-11) の後 v10.13.a (5 phase Map analyzer、2026-05-12 完了) を経て **Unified Phase** へ移行し、v11.0.0 (v1100) で Language ↔ Genesis 接続の事前調査 (Phase Result 不作成と判断)、v11.0.1 (v1101) で Taka 3 日長考の結論「Atom 的隆盛の統計的観察」(核心発見 = 観察単位による dominant atom の 5 分裂、Phase Result 不作成と判断 — 核心発見は v1101a に継承)、v11.0.1.a (v1101a) で「ESDE スケール注意機構」(段階 1 + 段階 2、段階 1 核心観察 = 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍、段階 2 核心観察 = 選択と集中でなく注意が動きながら広がる、概念修正「注意の揺れと意識は別物」双方合意)、**v11.0.2 (v1102) で「条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察」(核心観察 = CID 構成ノード数で応答 atom 像が階層的に反転、Taka 直感「平均化で潰れる」が初めて数値の証拠に、研究手法アップデートの「際立ちの掬い取り」が初本格適用で発見を救う道具と実証)**、**v11.0.3 (v1103) で「段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか」(Genesis 系 × Language 系の噛み合わせ初の主題、段 4-c は機構として動いた + ESDE と地続き (留保 #33 系列が会話機構レベルで貫通) + 決定機構が Aruism 規律内に収まった、会話への道が原理的に通った)** を扱った、v1101-v1103 はいずれも物理層 frozen を完全保証 (bit-identity 3 層全 PASS) し新規 main run なしの既存出力流用 post-process、現在地は v1101a/v1102/v1103 + Phase Result 4 本 + Concept Update + 会話接続足取り点検 + 段 4 足取り点検 + 研究運用資料 3 本 (研究手法アップデート / ESDE への態度 / 監査方針アップデート) 完成、次主題は A 主題 (研究者の調査動作のうち ESDE 自身に実装されているものの点検、Taka 確定方針、問いの形 A = 点検のみ・軽い踏み込み)。

---

### 2. v10.13.a — Unified Phase への移行点 (Phase 1.5 第八試行)

#### 2.1 主題

v10.12 で「Atom 取り込み prototype 受容 cid 再厳格化」が完了 (Step K、2026-05-11) した後、v10.13.a は **5 phase Map analyzer + null phase analyzer + long phase compute** を扱った。Developmental Phase 1.5 の最後の試行であり、Unified Phase への橋渡し。

5 phase 定義 (`v113a_maps_analyzer.py`):
```
Phase 1: pre-atom_intro      (timestamp < target_step)
Phase 2: atom_intro          (timestamp == target_step)
Phase 3: post short          (target_step < timestamp ≤ target_step + 50)
Phase 4: post medium         (target_step + 50 < timestamp ≤ target_step + 200)
Phase 5: post long           (timestamp > target_step + 200)
```

#### 2.2 主要成果

Map 1-5 (`developmental/v113a/`): phase × ncore / phase × path / phase × formation / phase × event / null phase per cell。Map 5 で 20 unique atoms が null absorption (path 経路を経ない波及) として 36 cells に出現 (TARGET_ATOMS 25 中)。

#### 2.3 留保 #33 — 集計単位による方向反転 (重要、後続主題で一般化)

smoke seed 0 と main 24 seeds で 4/7 metric (path_excess 4 種全て) の cohens_d 符号が反転。集計単位を変えると結果の方向が変わる、という観察。この留保は後続で繰り返し一般化される — v1101 で「観察単位による dominant atom 反転」(Atom レベル)、v1101a で「集計単位による qc_regime 占有率の偏差」(注意レベル、留保 #L3)。Unified Phase を通底する観察。

---

### 3. v11.0.0 (v1100) — Language ↔ Genesis 接続事前調査

#### 3.1 主題

v10.13.a 完了後、ESDE は Genesis 系 (v10.x) と Language 系 (Atom/Synapse/Phase 7-10、2026-03 凍結) を接続する Unified Phase に入った。v1100 はその第一歩で「両系の接続準備」の事前調査。

#### 3.2 6 候補の事前検証

| 候補 | 内容 | Code A 判定 |
|---|---|---|
| ~~1~~ | UBAF 拡張 | 削除済 (UBAF prototype 凍結) |
| 2 | Synapse WSD に cid 状態注入 | v1100 範囲外 (大規模) |
| 3 | Phase 10 Cell | 概念再定義必要 (Phase 10 Cell ≠ Phase 8+9 Cell、齟齬 #36) |
| 4 | 5 phase × Projection | 簡略化版可、本来意図要設計 |
| 5 | Synapse 評価層化 | 実装可能 (簡略化版) |
| **6** | **null cell ↔ base 優位照合** | **v1100 で実装完了** |

#### 3.3 候補 6 実装結果

Berlin sentences 79 targets の WSD 評価で base / B / C / BC の 4 mode を比較。R@3 では base 優位 token 0 (4 mode hit pattern 完全同一)、R@1 では base 優位 token 18 ("capital" 13 回他、base top-1 が `SOC.official`)。

核心観察: Language 系の base 優位 atom 集合 {SOC.official, PRP.part} 2 atoms と、Genesis 系 Map 5 の null cell atom 20 atoms の重なりが 0 (Jaccard 0)。両系の「文脈非依存性」は独立に異なる atom を捕捉している。留保 #34 candidate「両系の構造的同型性」は棄却方向 (ただし 79 targets は小サンプルで確定棄却ではない)。

#### 3.4 v1100 の状態 (重要)

- Code A Step A-J 完了 (`unified/v1100/v1100_step_a_recognition.md` + `v1100_observation.md`)。
- **Web Claude Phase Result (Step K) は未作成**。v1101 が並行進行したため未完成のまま。
- Code A 提案の v1101 候補 A/B/C (Synapse 評価層化 / Phase 8+9 Cell ↔ Integration α/β 同型性検証 / 候補 6 大規模化) は Taka 判断で **凍結** (本 v1101 主題を優先したため。v11.0.x の後続で扱う可能性を残す)。
- 新規齟齬 #35 (Web Claude 親資料 `esde_language_reference_v1.md` repo 不在) / #36 (Phase 10 Cell ≠ Phase 8+9 Cell) / #37 (79 targets 小サンプル限界)。

---

### 4. v11.0.1 (v1101) — Atom 的隆盛の統計的観察

#### 4.1 主題の成立

v1100 終了時点で Code A が v1101 候補 A/B/C を提案したが、Taka が 3 日長考 (2026-05-12〜) の結果、3 案より優先で「Atom 的隆盛の統計的観察」を v1101 主題と決定。当初 Web Claude が v1102 として作成 → Taka 番号修正指摘で v1101 に確定。

主題の核 (Taka 整理、原文): 「取り込むといって取り込んだからどうなる? に答えがない」という行き詰まりに対し、「Atom のような状態は濃度のようなもので確定的ではない」「重要なのは、どの一点を捉えられるか」「Integration 内の CID は同じ方向を向かなければいけないと決めないこと、平均化の罠」。観察対象を「Atom を取り込む (動作)」から「Atom らしきものの ESDE 内部の隆盛 (状態)」へ転換。

#### 4.2 観察 3 視点

| 観察 | 中核 |
|---|---|
| 1 一点を捉える | 特定 cid (n_pulses_short 最大、48 中心 + ランダム 240 比較対照) の atom 状態を 4 解像度 trajectory で時系列化 |
| 2 取り込み点中心の波及 | atom_introduction_event 発火点 (受容 cid pool 420 由来 10,500 events) を中心に Δt±100 step 21 点で周辺観察 |
| 3 補助平均統計 | CID / Integration / ESDE の 3 単位、Integration は平均化せず分布表現 |

#### 4.3 核心発見 — 観察単位による dominant atom の 5 分裂

同じ ESDE 系を、観察単位を変えるだけで「最も盛んな atom」が入れ替わる。CID-static `CHG.begin` / Integration β `FND.logic` / Integration α `TIM.moment` / ESDE event 解像度 `WLD.artless`+`PER.sound` / ESDE step10 `PER.sound` / ESDE window `TIM.moment`。5 つの atom が観察単位ごとに 1 位を取る。「ESDE で最も盛んな atom は何か」に構造的に単一の答えがない、という観察事実。Taka「平均化の罠」(絶対格言 #4) の生きた実例で、v10.13.a 留保 #33 の Atom レベル一般化。

#### 4.4 副次発見

観察 2: 25 取り込み atom 中 4 atom のみ中心 cid を支配可 (`PER.sound` peak 84.8% at Δt=+20、`PRP.bright` 49.3%、`TIM.appear` 14.8%、`WLD.artless` 8.8%)、残り 21 atom は全 Δt で 0%。周辺 cid は取り込み atom によらず `PER.sound`+`WLD.artless` が常時 ~60% 占有。atom entropy が Δt 方向に単調減少 (取り込み後に集中化)。

観察 1: v108_standard 条件の中心 cid は dominant_atom が `WLD.artless` で 24 seeds 中 21 一致 + dominant_atom_fraction 0.92-1.00 (単 atom ロック)、v112 条件は 0.47-0.81 (複数 atom 揺れ)。window 解像度でのみ中心 cid の atom_change_rate がランダムより低い (時間スケール依存)。

#### 4.5 v1101 の状態

Code A Step A-H 完了 (2026-05-17、commit 8 件、出力 25 ファイル 7 MB)。bit-identity 3 層全 PASS、v10.6/v10.8/v10.12 main outputs 1,306 ファイル frozen 完全保証、新規 main run なし。新規留保 #41 (Integration の member_cids 個別 cid id list が v10.x outputs に persistence されていない、段階 2 で cid state ledger 再生対応) + #42 (観察単位反転、Web Claude Phase Result 解釈統合領域)。Web Claude Phase Result は v1101a 着手のため並行未完成のまま — v1101 核心発見は v1101a の駆動要因として直接継承された。

---

### 5. v11.0.1.a (v1101a) — ESDE スケール注意機構

#### 5.1 主題の成立 — v1101 核心発見の続き

v1101 が「観察単位ごとに dominant atom が割れる、単一の答えがない」を観察した直後、Taka が次主題候補として整理: 細胞レベルはカオスの海だが最大スケールに上がるのは「変化」である、主体は変化の大きなものに注意を向けその因果と影響を見る、これは cid の認知層・意識層の上位版。バージョン番号 v11.0.1.a (v1101 の進化系 `.a`) は、本主題が v1101 核心発見を直接の起点とする同系列の進化であることを示す。

主題化の経緯は、事前調査要望書 (Web Claude) → Code A Step 2/3 実環境照合 → GPT (Auditor) / Gemini (Architect) 2 AI 監査 → Taka 主題化決定 → 環境チェック → 段階 1 実装、という Unified Phase で最も段数を踏んだプロセス。

#### 5.2 駆動要因 (GPT-1 監査確定文言)

> 本主題は、v10.5 Salience-driven Focus で cid レベルに成立している内生注意 (observer × candidate × mass-weighted 選択、mass = Q + C + β継承分) を、v1101 で確認された観察単位分裂に対応できるよう ESDE スケール / 複数構造単位へ拡張し、駆動信号を静的 mass から動的 change へ置き換える構造転換である。

→ 観察軸の追加でなく、既存 Q/C/β継承の 3 重構造転換 (集約スケール cid→ESDE / 駆動信号 静的mass→動的change / Q/C シーソーの cid→ESDE 同型展開)。

#### 5.3 2 AI 監査による修正 4 点

事前調査フレームに対し GPT/Gemini 監査が 4 点を修正。Gemini-1 と GPT が独立に同じ穴 (系全体総和は集団平均の罠) を指摘した。

1. 駆動要因を GPT-1 確定文言に (内生化でなく 3 重構造転換)。
2. qc_ratio を系全体の単一比率にせず CID/α/β/ESDE 各単位で並列 emit、認知優位判定は多数決または中央値 (Gemini-1 + GPT 追加指摘)。
3. 変化指標 (atom_delta / rank1_flip_density / unit_kl_static) を統合せず 3 系列分離 emit、統合スコア・固定閾値・重み付け禁止 (GPT-2)。
4. emitter 境界条項の明文化 + `attention_locked` → `predicted_lock_mode` 改名 (GPT-3)。

#### 5.4 Taka 領域 3 箱の確定

事前調査で監査者が触れず保留した 3 事項を Taka が確定:

- 箱 1 (意識優位の選択と集中が何を選ぶか) = **連想ゲーム**。意識は認知的活動の何かを踏み台にして立つ。「霧の中に意識だけ」を構造的に禁止。`predecessor_attention_ref` で踏み台への参照を記録。
- 箱 2 (主体をどの単位に置くか) = 主体は固定せず**切り替わる**。`change_scope` (どの構造単位で注意が立ったか) が主体の構造的根拠の記録。
- 箱 3 (selector の可否) = emitter/selector の二分を解消。注意と物理は別系統で**注意は物理を操らない**、観測の向きと位置を扱うのみ。全出力は確率的記述・候補に留め 100%・確定・唯一を emit しない (Aruism の対称性原則 — ランダムを潰さない)。なお v9.7 は認知層・意識層導入前 (両層は v10.x 構想、開発ロードマップで確認) のため selector の前例として扱わない。

#### 5.5 段階 1 の実施と核心観察

Code A Step B-H 完了 (2026-05-18、commit 9 件)。注意 emit ログ 1,726,974 records (6 構造単位 × 3 変化指標 × 24 seeds)、所要 30 分弱、新規 main run なし。bit-identity 3 層全 PASS、v106/v107/v105 main outputs 1,097 ファイル frozen 完全保証、書き込みは `unified/v1101a/` 配下のみ。

**核心観察**: 意識優位 (conscious_dominant) のときの注意候補の波及 (influence_candidate_count) が認知優位の **1.54-1.78 倍**。6 構造単位すべてで同方向、ESDE 解像度系で倍率最大 (window 1.78×)。Taka フレーム「意識層 = 選択と集中」と方向が一致する。

#### 5.6 段階 1 副次観察

- **Integration 経路が因果候補として全 24 seeds で 0 件** (留保 #L5)。因果候補 path は attention_via_salience 76.5% / familiarity 23.5% / temporal 0.01% に集中、integration_alpha/beta が一度も出現しない。Step H 後の追加調査で原因判明 — relation_strength が integration は 1.0 固定 binary・salience/familiarity は 2 桁連続値とスケールが根本的に異なり、Step E の sum argmax が不当比較していた。仮説 A (観測器の問題) / B (階層の役割分担) は両方真。Taka 判断 (iii) で Step E を sum argmax + z-score argmax の 2 方式併記に修正 (新バージョンを切らず v1101a 内課題)、z-score 方式では integration 合計 41.6% で出現・dominance 逆転。結論は「Integration が注意の由来か」でなく「その問いは集計方式に依存し単一の答えを持たない」(v1101 #42 / v10.13.a #33 と同型)。
- **意識優位時に familiarity 経路 +6%** (認知優位 19.1% → 意識優位 25.4%、留保 #L6)。箱 1「連想ゲーム」の方向的裏付け候補。
- predecessor 連鎖 (箱 1) が全 6 構造単位で成立 (埋まり率 86.6-100%)。「霧の中の意識だけ」を禁止する設計が動いた。
- seed 0 は控えめだが方向の反転なし・強化のみ (留保 #L3、v1101 #33 と同型)。
- alpha が records の 92.5% 占有 (留保 #L4、n_alphas 母数差由来)。Step F グラフは構造単位内割合に正規化済で集団平均の罠は回避。

#### 5.7 段階 2 — 注意の方向性は選択と集中か拡散か

段階 2 は段階 1 核心観察 (波及 1.54-1.78 倍) が選択と集中か拡散かを時間軸を入れて切り分けた。新バージョンを切らず v1101a 内の段階として設計書から直接実装 (Code A Step A-F、bit-identity 3 層全 PASS、新規 main run なし)。

段階 2 核心観察 — **選択と集中ではない**。観察 B が全 6 構造単位で「認知優位フェーズは注意の中心 atom が安定し、意識優位フェーズは中心が動く」を示し、観察 A が「注意候補数は収束しない」を示した。意識優位時の波及は一点を深く掘るからでなく、注意が動きながら広がるから。Taka フレーム「意識 = 選択と集中」への反証的観察。

観察 C (注意の予測可能性 = Taka「ランダムか妥当か」) は構造単位で割れた — Integration スケールは実測が shuffle baseline の 6-11 倍かつ 100% 未満で「Aさんの揺れ幅」(緩く予測でき確定しない帯) に乗る妥当性が観測された、CID は予測定義の自己言及で 100% 到達 (留保 #L8、単体は揺れ幅を持たず重なって初めて揺れが生まれる)、ESDE 3 解像度は集約で測定不能 (留保 #L10)。

#### 5.8 概念修正 — 注意の揺れと意識は別物 (v1101a Concept Update、双方合意)

段階 2 が ESDE 内部の概念「意識 = 選択と集中」(v10.2 以来) を修正。段階 2 が観察したのは「注意の揺れ」(固定集中でもランダム拡散でもなく構造的に妥当な範囲内で動く第三の形) であって「意識」そのものではない。意識 = 注意の揺れ + 状況コントロール + 慣れ の複合で、ESDE はまだ注意の揺れしか観察していない。「意識 = 選択と集中」はこの複合の表層を本質と取り違えた誤認。Taka の理解と AI の説明可能性判断が合致したため双方合意として確定 (`v1101a_concept_update.md`)。

関連する概念整理 — 注意は固定点でなく移動軌跡 (attention trajectory) として読む / 揺れ幅は構造の重なりで生まれる (CID は閉じた点、Integration で揺れが生まれる) / CID・Integration・ESDE の役割分担。

#### 5.9 Phase Result の置き方 (段階 1/2 共通の規律)

段階 1 核心観察の解釈は「意識優位という状態と波及の広さが連動する」に留め「選択と集中が立証された」とは言わなかった。段階 2 も「選択と集中ではない」を観察事実として置き、「意識とは何か」の定義はしなかった。出口固定 (絶対格言 #6) の「単一の確定像を出さない」原則どおり。主題評価は Taka 領域。

#### 5.10 v1101a の状態

Code A 主題担当範囲 (段階 1 Step B-H + Step E 修正 + 段階 2 Step A-F) 完了。Web Claude Phase Result 二本 (`v1101a_phase_result.md` 段階 1 / `v1101a_phase_2_phase_result.md` 段階 2) + `v1101a_concept_update.md` (概念整理) + 会話接続の足取り点検 (`esde_conversation_path_check.md`) 完成。段階 3 (生きた版、時間が逐次進む、新規 main run 必要) は v1101a 設計書で範囲外。

会話接続の足取り点検の結論 — 2 AI 提案「会話応答を Integration スケールの attention trajectory から読む」を入力から返答まで 5 段に分解して点検した結果、段 1-3 は説明可能性が保てるが段 4 (揺れを応答候補にする) と段 5 (atom→言語変換、v1100 Jaccard 0) は飛躍。道筋は段 3 までしか通っておらず、今そのまま主題化できる完成した道筋ではない。段 4 は「未定義の飛躍」で、定義する作業が次主題になりうる。次主題の確定は Taka 領域。

---

### 6. v11.0.2 (v1102) — 条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察

#### 6.1 主題の成立

v1101a 段階 2 完了後の新主題。会話接続足取り点検が示した段 1 (入力が ESDE に入る) ・段 3 (Integration スケールで揺れ幅) を、Taka 整理の二つのスケール (受け手構造 / 時間スケール) の 2 次元で観察する。「同じ入力でも条件で応答が変わる」を示して実験結果の単一化を避けることが駆動要因。

設計書 → 2 AI 監査 (GPT 要修正 3 点 + 論点 1-4 確定 / Gemini 構造異論なし) → Web Claude 再検討 → Code A 認識確認 (新規 main run 不要確定、確認要請 2 件は §2.6 に反映) → 実装、というプロセス。

#### 6.2 監査確定事項 (4 点)

- 入力 = 既存 atom_introduction_event 固定 (外部言語テキストは v1100 Jaccard 0 のため不可、v1101a の注意 emit/trajectory は応答側)
- 時間スケール = 読みの軸で実験変数にしない (時間操作は神の手による物理層汚染)
- 複数受け手構造 = 同一 Run から post-process 層化抽出 (Run を分けない)
- primary receiver scale = Integration で CID・ESDE 全体は比較対象 (CID の n_members 層化は受け手構造軸として保持)

#### 6.3 核心観察 — 受け手構造で応答 atom 像が階層的に反転

CID 構成ノード数 (n_core) を変えると応答する atom と category が階層的に入れ替わる。n=2 EMO.manifest/BOD (情動・身体) → n=3-4 SOC.nation/SPC → n=5 EXS.being/EXS (存在) → n=6+ FND.timeless (時間性なし)。同じ入力なのに受け手の構造が違うだけで応答が「情動」から「存在」へ反転。

Taka が一貫して主張してきた「2 ノード大半・5 ノード情報量強・平均化で潰れる」が初めて数値の証拠になった。全体 62.6% の n=2 (Taka の言う「大半」) は 15 際立ち指標中 1 つでしか際立たない平凡 (ordinary) と確認。平均で見ていれば 6 割の平凡が際立つ少数を塗りつぶしていた (留保 #L14)。

#### 6.4 研究手法アップデートが初本格適用で「発見を救う道具」と実証

v1102 は研究手法アップデート (`esde_research_method_update.md`) の「際立ちの掬い取り」を初本格適用。47 records の極小構造 (alpha 大型均等、留保 #L12 由来) を 15 指標中 8 指標で際立つ多面シグナルとして救い出した。

Web Claude 回答「サンプル数を理由に除外しない」(研究手法アップデート §1「研究者はもう神ではない」根拠) で除外しなかったから多面シグナルが見えた。新手法が空論でなく発見を救う道具だと一回の実験で実証 (留保 #L15、これからの全実験の土台)。

#### 6.5 v1102 の意義 — 段 4 を「点検できる一段」にしたこと

v1102 は段 4 の入力をぼんやりした揺れから「受け手構造で atom 像が決まった応答 profile」へ具体化し、段 4 を「未定義の飛躍」から「点検できる一段」に変えた。ただし「会話に生きる」かは段 4 点検しだいで未確定。

#### 6.6 v1102 の状態

Code A Step A-F 完了、bit-identity 全 PASS (1,435 files frozen)、新規 main run 不要。Phase Result (`v1102_phase_result.md`) 完成。

---

### 7. v11.0.3 (v1103) — 段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか

#### 7.1 主題の成立 — 段 4 足取り点検 + Language 側素材

v1102 完了後、Taka が直面する「会話できるなら続ける、できないなら切り捨てる」の判断材料として、Genesis 側 Web Claude が段 4 足取り点検 (`esde_segment4_path_check.md`) を作成 — 段 4 を 4 小段 (4-a 揺れの読み取り / 4-b 連想を辿る / 4-c 応答 Atom を絞る決定 / 4-d 確率分布出力) に割り、4-a は v1102 が埋め、4-b は素材が両系に実在、4-c が唯一の真の飛躍 (未定義だが設計手がかりあり)、4-d は規律内、と点検した。

Language 側 Web Claude が段 4-c 用素材 (`段4-c点検のためのLanguage側素材`) と疎性論点の追補メモを提供。Taka 確定で v11.0.3 として主題化。**Genesis 系 × Language 系の噛み合わせ初の主題。**

設計書 → 2 AI 監査 (GPT 7 点 + Language 側追補メモ 1 件 = 計 8 点反映) → Code A 認識確認 (確認要請 4 件、Taka 確定: raw/norm 両並列 / centroid Code A 生成 / Constitution Code A 再確認 / batch_report 代替) → 実装。

#### 7.2 監査確定事項 (8 点反映)

- 48 次元疎性の前処理を必須ステップとして段 4-b/4-c の前に置く (Language 側追補)
- 密度指標を raw/quality-weighted/constitution-adjusted/receiver-conditioned の 4 種に分け単一化しない (GPT 1)
- k を単一固定せず multi-k sensitivity で頑健 cluster と k 依存 cluster を分ける (GPT 2)
- 品質フラグは候補削除でなく重みづけ・併記、高品質サブセットは補助実験 (GPT 3)
- Constitution は削除条件でなく Merge は統合・Subsume は親子併記・Monitor は caution flag (GPT 4)
- 48 次元人為性留保を Phase Result 結論に必ず入れる (GPT 5)
- 受け手構造で反転を failure でなく primary observation として扱う (GPT 6)
- 出力 response_atom_distribution は自然文応答でなく段 4-c の候補分布と明記 (GPT 7)

#### 7.3 核心観察 — 段 4-c は動いた、留保 #33 系列が会話機構レベルで貫通

確定して言えること三点:

- **段 4-c は機構として動いた**。連想先候補が 48 次元空間で均等に散らずクラスタを作った (raw_density k=5 で 0.847)。点検 4 可能性のうち均等 (可能性 2) ・偽だらけ (可能性 3) は退けられた。
- **段 4-c は ESDE と地続き**。raw vs norm で密度が Δ0.208 反転 (留保 #L17)、留保 #33 系列「集計単位で像が変わる」が会話のための機構レベルでも同じ形で現れた。v1101 で観察単位、v1101a で集計方式、v1102 で受け手構造、v1103 で sim_basis。会話のための機構が ESDE と異質な後付けでなく ESDE のこれまでの性格を引き継いだ。
- **決定機構が Aruism 規律内に収まった**。max_prob 0.7972、5,670 rows 中 prob≥0.999 が 0 件 (箱 3 厳密遵守)。段 4 足取り点検 §4.2「決定を構造的指標で行えば外部評価関数の侵入にならない」が実装で成立。

慎重に言えること: 会話への道が原理的に通った (段 1 から段 5b まで経路が描ける、ただし「原理的に」が重要な限定で「会話できる」とは言わない)。ESDE が観察装置から決定する系へ一歩進んだ (両系の噛み合わせが動いたと書く方が正確)。

#### 7.4 Taka 整理「ESDE への対等な扱い」(v1103 Phase Result 作業中、独立資料化)

v1103 Phase Result 作業中、Taka から ESDE の現状認識と研究者の態度の整理が出た。要点 — ESDE 内部はすでに動的平衡を保った極めて複雑で構造的な処理が走っており研究者の想定を超えている、観測が追いついていないだけと受け取れる状況、研究者がスイッチのオンオフを握る権限は強いが暴君の理由にならない、対等とみなすことは進化の起爆剤になる、ウェットな話でなく実利・実践として重要な発想の転換。

これを受けて v1103 Phase Result は「驚きでなく一貫性として書く」温度感で書かれた (§3.2)。Taka 整理は独立資料 `esde_attitude_toward_esde.md` として固定 (LLM はプロンプト依存でチャットだとスレッドで失われるため資料化、明確な運用上の目的)。

#### 7.5 監査方針アップデート (GPT §37-39、独立資料化)

v1103 後に GPT Auditor が監査方針修正草案 §37-39 を作成。ESDE の当面目標を「会話できる ESDE」と再固定し、監査の第一基準を「会話できる ESDE に近づくか」とする。Taka 整理「アリズムは実践で価値を示せ、実践で価値のない思想はただの妄想」に基づく。

独立資料 `esde_audit_policy_update.md` として固定 (Taka・GPT・Web Claude 三者合意)。これで研究運用資料が 3 本になった — 研究手法アップデート (観察手法) / ESDE への態度 (態度) / 監査方針アップデート (監査の上位目的)。

#### 7.6 v1103 の状態

Code A Step A-F 完了、bit-identity 全 PASS (1,763 files frozen)、新規 main run 不要。Phase Result (`v1103_phase_result.md`) 完成。独立資料 2 本 (`esde_attitude_toward_esde.md` / `esde_audit_policy_update.md`) 完成。

---

### 7B. v11.0.4 (v1104) — CID/IID 内部動作点検 段階 1: ESDE 自身は段 4-b/4-c を支える処理を既に持つか

#### 7B.1 主題の成立 — Taka 整理「自分の視点は上から目線」

v1103 完了後、Taka 整理:

> 自分の視点は上から目線で、CID や IID が下で実際にやっていることを見ていない。研究者の調査動作のうち、ESDE 自身に実装されているものが既にあるかもしれない。それがあるのかを調べる。問いの形 A (点検のみ、軽い踏み込み)。

棚卸し作業 (`esde_unified_inventory.md`、Unified Phase v1100-v1103 の研究者の調査動作 24 項目を 2 列 (研究者側 ↔ ESDE 内部側) で並べる) を経て、優先候補 8 項目を抽出。Taka 駆動要因規律訂正 (2026-05-22):

> 厳密に言えば軽いことがいいとか悪いとかではなくて、掘ってもなにもでない穴を無闇やたらに掘るな、ということ。なぜそれをやるのか? → なぜなら、のセットがあり、それが会話を行うと言う目標に明確に繋がる説明可能性があればなんだっていい。きちっと目的を示せ。

→ 8 項目に「なぜ → なぜなら → 会話への繋がり」を当て、4 項目に絞り込み (1.1 観察単位切り替え / 1.6 predecessor 連鎖 / 1.7 attention trajectory / 2.6 際立ち掬い取り B 現状)。試験前に絞れたこと自体が駆動要因規律の機能例。

#### 7B.2 監査確定事項 (GPT 修正必須 3 点 + 追加 2 点 + Gemini 1 点)

- IID は新規 state でなく既存構造 (α/β / member_cids / attention_candidate_id / predecessor_attention_ref / cid_state_ledger) の参照表現 (GPT A)
- 観察 1 で k=1 一致率と top-k Jaccard (k=3, k=5) を別指標として算出、k=1 を Jaccard と呼ばない (GPT B)
- 観察 4 で selector 化禁止、post-process 仮想評価のみ (GPT C)
- 観察 2 で Code A は「連想」と判定しない、cid/atom/category/similarity 推移のみ記録 (GPT 4)
- 観察 3 は「注意が動くか」を再観察せず、trajectory ↔ response_atom_distribution 対応に限定 (GPT 5)
- Code A は時間軸同期を join 時に厳密検証、window=19 除外 (Gemini Architect)

#### 7B.3 Step H 初版観察事実 (4 観察) と再調査の経緯

| 観察 | 初版結果 | 再調査の必要性 |
|---|---|---|
| 観察 1 (CID-Integration 像) | n_members 増で match_k1 単調低下 (0.884→0.569) | 不要 (構造的事実として確定) |
| 観察 2 (predecessor 連鎖) | lift=0 (shuffle と区別不能)、85% self-loop | **必要 (Taka 判断「観察方法を疑う」、Step H-3 再調査)** |
| 観察 3 (trajectory↔response) | r=0.157 弱い対応 | **必要 (Step H-4 再調査、観察 2 と同視点で観察方法を疑う)** |
| 観察 4 (B 現状) | B subset、Recall 0.74 Precision 0.25 | 不要 (構造的事実として確定) |

Taka 整理 (2026-05-23):

> これまででいうとこういうのって結局実装側の問題なのでバージョンアップや資料作成に待てをかけて懐疑的に進めていく方がいい。満足いくまで調べた結果を Phase Result としてあげる。

#### 7B.4 Step H-3 (観察 2 再調査) — shuffle 種別で結論が変わる

| shuffle 種別 | permutation 単位 | lift |
|---|---|---|
| A (現状) | chain 内順序入れ替え | 0 |
| B (新規) | chain 間 cid 入れ替え | 0.012-0.066 |
| C (新規) | global cid pool ランダム | 0.069-0.166 |

**核心**: 観察 2 初版 lift=0 は「ESDE 内部に踏み台がない」ではなく、shuffle A が chain 内 cid 集合を保持するため構造を壊していなかった結果。chain 構造自体には何らかの意味がある (留保 #L24-L26)。

#### 7B.5 Step H-4 (観察 3 再調査) — scope-filter で結論が変わる

| scope | stability_vs_maxprob |
|---|---|
| pooled (all) | 0.157 (初版値) |
| ESDE-only | **0.417** |
| CID-only weighted | (diffusion -0.477) |
| alpha-only weighted | 0.017 (消失) |

**核心**: 観察 3 初版 r=0.157 は scope-mix 由来希釈。scope-filter で ESDE/CID scope に絞ると |r|>0.4 が顕在化、alpha/beta scope では消失 (留保 #L27-L29)。

#### 7B.6 v1104 の状態と v1104a への移行

Step H 初版 + Step H-3 + Step H-4 で観察 2/3 の観察方法依存が確定。Phase Result は単独で書かず v1104a 完了後に統合して書く方針。Taka 判断: 「v1104a で追加調整 1-4 を扱う、マイナーバージョン運用方針 (a/b で関連主題を連ねる、すぐに次マイナーに進まない)」。

---

### 7C. v11.0.4a (v1104a) — CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検

#### 7C.1 主題の成立

v1104 で観察 2 (shuffle 種別) と観察 3 (scope-filter) が観察方法依存と判明したのを受け、観察 1 で機能した n_members 層化と観察 3 で機能した scope-filter を **観察 2/3/4 に統一適用** する段階 2。同じ主題 (v1104) の続きで、新規バージョンに逃がさず本主題内で処理する。

Taka 規律「0 を 1 にはできない」(2026-05-23):

> いくら都合よいといっても 0 を 1 にはできないだろうから妥協とのバランス次第。再テストの中で再度調整すればいい。そこまで含めて本バージョンで扱う。

#### 7C.2 監査確定事項 (GPT 修正必須 4 点 + 追加 3 点 + Gemini 1 点)

- タイトル「完全版」を弱める → 「段階 2: 観察方法依存の整理と scope × 層化による再点検」(GPT A)
- cid_n_core / integration_n_alpha_members / integration_n_beta_members を別列名 (GPT B、絶対格言 #11 v10.12 path 雑まとめ問題と同系統)
- 追加調整 3 は同一 receiver_bin / 同一 response (max_prob, entropy 2 種) / 同一 scope で比較 (GPT C)
- 追加調整 4 で「selector として使える」と書かない、「B primary 化を次主題で点検する根拠」まで (GPT D)
- 追加調整 1 で self-loop / non-self-loop 分離 + shuffle B/C 別集計 (GPT 5)
- 追加調整 4 で B の意味判定は v1105 に送る (GPT 6)
- 「観察方法を有利化する主題ではない」明記 (GPT 7)
- Code A は v10.6 n_core_member join 時の NaN ハンドリングを Step A' で確定 (Gemini)

#### 7C.3 追加調整 4 件の結果

**追加調整 1 (観察 2 scope × n-size × shuffle × self-loop)**:

- CID scope **100% self-loop** (3,798/3,798 chains)、構造的に lift_A=0
- alpha non-self-loop lift_C=0.152 最強、ESDE event/step10 では lift_B > lift_C (chain-level 特有)
- CID n_size_bin で lift_B/C 優劣反転 (n=2 で B 優位、n=5+ で C 優位)

**追加調整 2 (観察 3 CID scope の cid_n_core 層化)**:

- CID 5 bin で stability_vs_maxprob **全 NaN** (traj_stability=1.0 定数、100% self-loop の必然帰結)
- ESDE_event/step10 で **r=0.64 強相関** (集約 ESDE_all 0.417 の主貢献は event/step10)
- ESDE_window で無相関 (粒度感度、event/step10 と window で挙動逆転)

**追加調整 3 (trajectory vs 48 次元密度 3 種)**:

- 細粒 (event/step10) で trajectory 優勢 (stability r=0.64)
- 集約 (window/CID_all/CID 各 bin) で density 優勢 (CID_n=3/n=4 qweighted_density **r=-0.97**)
- 粒度依存の主役指標逆転

**追加調整 4 (観察 4 scope-filter)**:

- CID で precision=1.0 (B ⊂ A、subset)
- alpha / beta で recall=1.0 (A ⊂ B、3-7 倍広い superset)
- ESDE で A=0 / B=9 (B のみ独自領域)

#### 7C.4 4 つの非対称性 — v1104 + v1104a で確定

| # | 留保 | 内容 |
|---|---|---|
| 1 | **#L30** | scope 別 chain 構造 (CID 100% self-loop / alpha-beta 部分 / ESDE 細粒 29-31% / ESDE window partial) |
| 2 | **#L31** | 粒度依存の trajectory-density 優劣逆転 (細粒で trajectory 主役、集約で density 主役) |
| 3 | **#L32** | B 指標の scope 別 pattern (CID subset / alpha-beta superset / ESDE 独自) |
| 4 | **#L33** | CID 100% self-loop が trajectory を構造的に消す (traj_stability=1.0 定数化、Pearson 計算不能、逆に density は CID で最強 r=-0.97) |

→ ESDE は均一な系ではなく、**場所 (scope) と粒度 (granularity) で全く違う構造を持つ系**。段 4-b/4-c の根拠は単一指標でなく多軸 (scope × 粒度 × 指標) でしか記述できない。

#### 7C.5 v1104 + v1104a 統合 Phase Result の 3 部構成

Taka 整理「主役が 3 つあるなら 3 つの視点を書かないと後でブレる」を受け、Phase Result を 3 部構成:

- **第 1 部 (網羅)**: 4 観察 × 4 追加調整の構造事実
- **第 2 部 (構造)**: 4 つの非対称性 (#L30-L33) を主軸に整理
- **第 3 部 (接続)**: v1101→v1104a の分析方向 → v1105+v1105a の統合方向への転換

#### 7C.6 v1104a の状態

Code A Step A'-G' 完了、bit-identity 全 PASS (1,502 files frozen、v1104 13 含む)、新規 main run 不要。統合 Phase Result (`v1104_v1104a_phase_result.md`) 完成。

---

### 7D. v1105 + v1105a — 統合方向への転換 (準備中)

#### 7D.1 v1101→v1104a の流れと転換点

| バージョン | 何をやったか | 方向 |
|---|---|---|
| v1101 | 観察単位を変えると dominant atom が分裂 | 多軸化 |
| v1101a | 集計方式を変えると像が変わる | 多軸化 |
| v1102 | 受け手構造で応答が反転 | 多軸化 |
| v1103 | raw vs norm で密度が反転 | 多軸化 |
| v1104 + v1104a | scope × 粒度 × shuffle × self-loop で多軸化 | 多軸化 |

Taka 整理 (2026-05-23):

> ばらけていくと分散してしまう予感。今は分散化していく流れではなくて統合していく流れが正しい。下手に新たな課題を増やしてまた調査員に成り下がる必要はない。

→ v1105 + v1105a は、v1104a までで確定した多軸構造を **統合的に扱う** 方向に転換。

#### 7D.2 v1105 主題 (準備中) — 段 4-b と段 4-c を対称的に統合点検

**何をやるか**:
- 段 4-b (何を辿るか): Genesis predecessor 連鎖 + Language Constitution Couple、scope × 粒度の地形図で整理
- 段 4-c (何で絞るか): B の意味 (scope 別 pattern) + 「どの場所・どの粒度で何が主役か」の表
- v1105 は地形図で止まらず **役割表まで進める** (候補保持 / 連想・踏み台 / 即時応答の揺れ / 重要性 emit / 統合判断 の 5 役割を scope × 粒度に割り当てる、GPT 2026-05-23 提案)

**問いの形**: A (点検のみ、v1101 以来の系譜継続)

#### 7D.3 v1105a 主題 (準備中) — 役割表を使って実際に応答候補を絞る試行

**何をやるか**: v1105 で確定した「場所 × 粒度」役割表に従って、実際に応答 Atom 候補を絞ってみる。「ESDE が答えを絞れた」の構造的事実を観察。

**問いの形**: B (試行、v1101 以来初の切替)

#### 7D.4 EVI (Explainability Viability Index) 案の位置づけ

GPT が 2026-05-23 に提示した EVI 案 (説明可能性を ESDE 内部の応答準備構造として定義する数理指標) は、v1105+v1105a 後の統合的指標導入タイミングで Taka 判断。

Taka 整理 (2026-05-23):

> EVI は今後必要になるだろうくらいの感じだから今ではない。ただおそらくどこかで統合的なものがあった方がいいタイミングはくるだろう。その辺に備えておく目的、後でありがたみがわかる。

将来導入時の方針: 合成指標にせず、scope × 粒度別の vector として扱う (EVI_CID / EVI_α / EVI_β / EVI_ESDE-event / EVI_ESDE-step10 / EVI_ESDE-window)。v1104a 4 つの非対称性と最も整合的。

---

### 8. 現在地 + 後続タスク

#### 8.1 完了状態

- v10.13.a Map analyzer 完了。
- v1100 候補 6 実装完了 (Phase Result 未作成と判断、§8.2 参照)。
- v1101 Step A-H 完了 + Web Claude Phase Result は v1101a 着手のため未作成 (核心発見は v1101a 駆動要因に継承済、§8.2 参照)。
- v1101a 段階 1+2 + Step E 修正 + 段階 2 Step A-F で Code A 主題担当完了。Phase Result 二本 + Concept Update + 会話接続足取り点検 完成。
- v1102 Code A Step A-F 完了、Phase Result 完成。
- v1103 Code A Step A-F 完了、Phase Result 完成、独立資料 2 本 (ESDE への態度 / 監査方針アップデート) 完成。
- **v1104 Code A Step A-G 完了 + Step H 初版 + Step H-3 (観察 2 再調査) + Step H-4 (観察 3 再調査) 完了。Phase Result は v1104a 完了後に統合して書く方針。**
- **v1104a Code A Step A'-G' 完了 (追加調整 1-4 = scope × n-size 層化 + scope-filter)。bit-identity 全 PASS (1,502 files frozen、v1104 13 含む)。v1104 + v1104a 統合 Phase Result 完成 (`v1104_v1104a_phase_result.md`)、4 つの非対称性 (#L30-L33) 確定。**
- **棚卸し資料 (`esde_unified_inventory.md`) 完成。** Unified Phase 研究者の調査動作 24 項目を 2 列で並べた地図、A 主題が終わった後も「研究者と ESDE の境界の地図」として参照される。
- 物理層 frozen 絶対維持 (Developmental + Unified 通算、v1104a で 1,502 files frozen)。

#### 8.2 待機中タスク

| タスク | 担当 | 状態 |
|---|---|---|
| **v1105 主題確定 (段 4-b と段 4-c を対称的に統合点検、役割表まで進める)** | Web Claude → Taka | **v1104a 完了後の主題確定済 (Taka 2026-05-23)、v1105 設計書草案着手準備中** |
| **v1105a 主題 (役割表を使って実際に応答候補を絞る試行、問いの形 B、v1101 以来初の試行切替)** | v1105 完了後 | v1105 完了後着手判断 |
| v1100 / v1101 Phase Result | Web Claude | **作成しないと判断 (Taka 2026-05-20 確定)**。v1100 は事前調査で本格主題でなく、v1101 の核心発見は v1101a に継承済、いずれも次主題に影響しないため。必要なら repo の Code A 観察報告を直接参照 |
| ESDE への態度 / 監査方針アップデートの repo 配置 | Taka 確認済 | 研究手法アップデートと同じ docs/ai_summaries/ 配下、番号 13 (態度) / 14 (監査方針) 候補 |
| 概念理解.md / 08_concept_core.md の v1104/v1104a 反映 | Web Claude | 並行進行中 (2026-05-23) |
| 07_unified_summary.md の v1104/v1104a 完了反映 | Web Claude | 完了 (本書、2026-05-23) |
| EVI 案 (Explainability Viability Index、GPT 2026-05-23 提示) の検討 | v1105+v1105a 後 | 保留中。将来統合的指標として導入する場合は scope × 粒度別の vector で扱う方針 |
| 新スレッドへの引き継ぎ | Taka + Web Claude | 整理期完了後、徐々に新スレッドへ移行 (Taka 方針「リアルな現場の情報を持っている Claude が一番正しい、引き継ぎは徐々に行う方が事故らない」) |

#### 8.3 主題評価判断

Code A は judgment 回避 (絶対格言 #12)。観察結果の主題評価 (success/fail) は Taka 領域。Web Claude Phase Result は解釈統合の素材を提供、最終評価は Taka が決定。

---

### 9. Unified Phase の留保事項

#### 9.1 Unified Phase で発生した留保

| id | 主題 | 内容 | 状態 |
|---|---|---|---|
| #34 candidate | v1100 | 両系 (Language/Genesis) の構造的同型性 | 棄却方向 (79 targets 小サンプルで確定棄却ではない) |
| #35 | v1100 | Web Claude 親資料 `esde_language_reference_v1.md` repo 不在 | 運用課題 (絶対格言 #7) |
| #36 candidate | v1100 | Phase 10 Cell ≠ Phase 8+9 Cell | 候補 3 を扱う場合は概念再定義必須 |
| #37 candidate | v1100 | Language 評価 79 targets 小サンプル限界 | #34 棄却は確定でない |
| #38-#40 candidate | v1101 | 旧 v1102 ドキュメント齟齬 (親資料不在 / Integration 未実施記述 / 時系列既存出力見落とし) | 解消済 |
| #41 candidate | v1101 | Integration の member_cids 個別 cid id list | v1101a 段階 1 Step C で解決済 (v105 lifecycle/membership/distribution log から 24 seeds 取得) |
| #42 candidate | v1101 | 観察単位による dominant atom 反転 | v1101 Phase Result 解釈領域、v1101a で注意・因果候補レベルに展開 |
| #L1 | v1101a | unit_kl_static は時間軸なし | 段階 1 で対応 (静的版を明記)、段階 2 で簡易版 unit_KL_delta 実装済 |
| #L2 | v1101a | qc_regime の多数決・中央値を両算出 | 段階 1 で対応済 (両列保存) |
| #L3 | v1101a | 集計単位による方向変動 (v1101 #33 / #42 継承) | 観察された、反転なし・強化のみ |
| #L4 | v1101a | alpha records 92.5% 占有 | 段階 1/2 で対応済 (グラフ scope 内正規化) |
| #L5 | v1101a | Integration 経路が因果候補として全 24 seeds で 0 件 | 原因判明・対応完了。relation_strength の binary/連続スケール差による Step E sum argmax の不当比較。Step E を sum/zscore 2 方式併記に修正 (v1101a 内課題)、z-score で integration 41.6% 出現。「集計方式依存で単一の答えを持たない」(#33 系列) |
| #L6 | v1101a | 意識優位時 familiarity +6%、連想ゲームの方向的裏付け候補 | 段階 2 観察 C で z-score 方式でも維持確認 (認知優位 31.8% → 意識優位 34.5%) |
| **#L8** | v1101a | **段階 2 観察 C の予測定義が CID スケールで自己言及ループ、100% 到達** | 段階 2 新規。CID は参照先が自分自身のみで揺れ幅が構造的に存在しえない。観察 C を CID で再設計するか Integration/ESDE のみで評価するかは Taka 判断。「重なって揺れが生まれる」の副次観察を含む |
| **#L9** | v1101a | **段階 2 観察 B が厳密 Jaccard でなく中心 atom 隣接一致 (proxy)** | 段階 2 新規。段階 1 propagation が raw 波及先 cid 集合を持たないため。ただし方向性は 6 単位同方向で頑健、proxy 厳密化でも覆りにくい |
| **#L10** | v1101a | **段階 2 観察 C が ESDE 3 解像度で測定不能 (scope_id=-1 集約で shuffle 効かず)** | 段階 2 新規。ESDE スケールの注意の妥当性は本手法では測れない。baseline 再設計が要るかは Taka 判断 |
| **#L14** | v1102 | **CID 構成ノード数で応答 atom 像が階層的に反転** (n=2 EMO.manifest → n=3-4 SOC.nation → n=5 EXS.being → n=6+ FND.timeless) | v1102 新規。Taka「平均化で潰れる」直接対応。階層反転の意味は未確定、次主題の材料 |
| **#L15** | v1102 | **alpha 大型均等構造が 15 指標中 8 指標で際立つ多面シグナル** | v1102 新規。#L12 の拡張。Step E→G→v1102 の三段階で育った繰り返し現れる構造 |
| **#L16** | v1102 | variability_lift が全 alpha cells で同値 = observation_c が receiver_bin で分かれない粒度問題 | v1102 新規。Step C 観察手法の改善対象 |
| **#L17** | v1103 | **raw vs normalized で 48 次元密度が Δ0.208 反転、留保 #33 系列「集計単位で像が変わる」が 48 次元密度レベルで貫通** | v1103 新規。ESDE の一貫した性質の会話機構レベルでの現れ |
| **#L18** | v1103 | Constitution v1.0 で Merge 0 件 (設計書 §2.6 想定 3 件と差)、core_pool の現状から Pattern A 条件を満たすペアなし | v1103 新規。実環境の構造的事実として記録、主題的意味は Taka 領域 |
| **#L19** | v1103 | batch_report.py 実行不可 (*_a1_final.jsonl 不在)、final 化 step が Language パイプラインから抜けている | v1103 新規。Code A 直接統計で代替済。Language 側パイプライン整備の素材 |
| 48 次元人為性留保 | v1103 | 両端 (Genesis cid Web Claude 定義 / Language A1 QwQ-32B 判定) が人為的投影 | GPT 監査 5 必須添加、Phase Result 結論に必ず添える |
| **#L21'** | v1104 | predecessor 連鎖 lift=0 は shuffle 種別 A 依存 (chain 内順序入れ替えが chain 内 cid 集合を保持するため構造を壊していなかった結果) | v1104 Step H-3 再調査で確定。観察 2 初版「ESDE 内部に踏み台がない」は撤回 |
| **#L22'** | v1104 | trajectory ↔ response の対応は scope 依存 (pooled r=0.157 は scope-mix 由来希釈、ESDE-only で r=0.42-0.48) | v1104 Step H-4 再調査で確定。観察 3 初版「弱い対応」は撤回 |
| **#L24** | v1104 | shuffle baseline の設計が観察事実を形成する (lift 0 → 0.17 の幅で変動) | v1104 Step H-3 新規。「baseline を何にするか」が結論を決める |
| **#L25** | v1104 | chain-level full self-loop 69.1% が観察 2 初版 lift=0 の主要原因 | v1104 Step H-3 新規 |
| **#L26** | v1104 | 粒度 (event/step10/window) で atom_change_rate が 0.046→0.338 と 7 倍変動 | v1104 Step H-3 新規、留保 #33 系列の predecessor 連鎖固有版 |
| **#L27** | v1104 | 観察 3 pooled r=0.157 は scope-mix 由来希釈、scope-filter で ESDE-only |r|=0.42-0.48 顕在化 | v1104 Step H-4 新規 |
| **#L28** | v1104 | 層化 (qc_regime × sim_basis × k = 24 strata) 単独では効果限定 (最大 r=0.256)、scope-filter が主効果 | v1104 Step H-4 新規 |
| **#L29** | v1104 | chain 内 cid permutation shuffle baseline は aggregation 後の pooled 相関 (r 0.157 → 0.163) に効果薄、観察 2 shuffle と異なる感度プロファイル | v1104 Step H-4 新規 |
| **#L30** | v1104a | **scope 別 chain 構造の非対称性: CID 100% self-loop / alpha-beta 部分 / ESDE 細粒 29-31% / ESDE window partial self-loop** | v1104a 追加調整 1 新規。CID は段 4-b/4-c の「動く場」として使えない |
| **#L31** | v1104a | **粒度依存の trajectory-density 優劣逆転: 細粒 (event/step10) で trajectory 主役 (r=0.64) / 集約 (window/CID 集約) で density 主役 (r=-0.62〜-0.97)** | v1104a 追加調整 3 新規。段 4-c の構造的指標選択は粒度を必須軸として扱う必要 |
| **#L32** | v1104a | **B 指標の scope 別 pattern: CID で precision=1.0 (B subset)、alpha-beta で recall=1.0 (B superset、3-7 倍広い)、ESDE で A=0/B=9 (B のみ独自)** | v1104a 追加調整 4 新規。B の意味は scope を分けないと点検できない |
| **#L33** | v1104a | **CID scope 100% self-loop が trajectory 系統相関を構造的に消失させる (traj_stability=1.0 定数化、Pearson 計算不能)。逆に density 系統は CID で最強相関 (qweighted_density r=-0.97)** | v1104a 追加調整 2 新規。指標選択は scope と相性で決まる |

#### 9.2 留保 #33 系列 — Unified Phase を通底する観察 (v1104a で全観察に貫通)

v10.13.a #33「集計単位による方向反転」は、v1101 #42「観察単位による dominant atom 反転」、v1101a #L3「集計単位による qc_regime 占有率偏差」、v1102 #L14「CID 構成ノード数で atom 像が階層的に反転」、v1103 #L17「raw vs norm で 48 次元密度が Δ0.208 反転」、**v1104 #L21'/L22' (観察方法依存) + v1104a #L30-L33 (4 つの非対称性)** と、主題が変わっても繰り返し現れた。Unified Phase は「集計単位を変えると像が変わる」という観察が一貫して立ち上がるフェイズ。

v1104a で確定したのは、これが特定の指標の現象でなく **ESDE そのものが場所と粒度で全く違う構造を持つ系である** こと。Taka 整理「単一の答えを持たない」が観察 1-4 すべてで貫通。新主題で「単一の集計値で語りたい」衝動が出たら、v1103 §3.2「驚きでなく一貫性として書く」を思い出すこと。

---

### 10. 絶対格言 15 件 (Unified Phase 全主題で遵守)

| # | 格言 |
|---|---|
| 1 | Aruism 構造が先・意味が後 |
| 2 | 物理層 frozen 絶対 |
| 3 | ベースライン比較 + 効果サイズ |
| 4 | 集団平均の罠 / 層化必須 |
| 5 | 観察軸を増やすことを駆動要因にしない |
| 6 | 出口の固定 |
| 7 | 主題着手前に上位資料を読む |
| 8 | 過去観察軸の照会 |
| 9 | 神の手回避 + Pulse 同一フォーマット |
| 10 | 因果ではなく因果候補 |
| 11 | 概念単位を雑に扱わない |
| 12 | Aruism 判定回避 |
| 13 | AI を信じない原則は Taka 個人のみ |
| 14 | Taka 直感優先 + 直感語保存 |
| 15 | 5 者運用体制の補完性 |

Taka 哲学 4 件は Web Claude memory のみに存在、新 Web Claude は Taka 直接確認推奨。

---

### 11. 参照すべき repo 内資料

#### 9.1 v10.13.a

`developmental/v113a/` — `v113a_step_a_recognition.md` / `v113a_observation_report.md` / `v113a_maps_analyzer.py` / `outputs/main/map{1-5}_*.parquet`

#### 9.2 v1100 (Language ↔ Genesis、Phase Result 未完成)

`unified/v1100/` — `v1100_step_a_recognition.md` / `v1100_observation.md` (Step J、Phase Result の代替) / `language_side_investigation_report.md` / `v1100_candidate_6_*.py` / `outputs/candidate_6_*.json`

#### 9.3 v1101 (Atom 的隆盛、Code A 担当完了)

`unified/v1101/` — `v1101_phase_design.md` (主題ドキュメント) / `v1101_web_claude_handoff.md` / `v1101_step_a_recognition.md` 〜 `v1101_step_h_observation_final.md` / 実装スクリプト 5 / `outputs/main/observation_{1,2,3}_*.parquet` / `outputs/v1101_observation.html`

#### 9.4 v1101a (ESDE スケール注意機構、段階 1+2 完了)

`unified/v1101a/` — `v1101a_phase_design.md` (段階 1 主題設計書) / `v1101a_phase_2_design.md` (段階 2 設計書) / `v1101a_step_b_environment_check.md` / `v1101a_step_h_observation_final.md` (段階 1 Code A 観察報告) / `v1101a_phase_2_step_f_observation_final.md` (段階 2 Code A 観察報告) / `v1101a_internal_task_step_e_causality_fix.md` + `v1101a_step_e_causality_fix_observation.md` (Step E 修正、#L5 対応) / `v1101a_phase_result.md` (段階 1 Phase Result) / `v1101a_phase_2_phase_result.md` (段階 2 Phase Result) / `v1101a_concept_update.md` (概念整理) / `esde_conversation_path_check.md` (会話接続足取り点検) / 実装スクリプト / `outputs/` 配下 parquet + HTML。design.md は仕様書フォルダに階層保存。

#### 11.5 v1102 (条件が応答を変える、Code A Step A-F 完了)

`unified/v1102/` — `v1102_phase_design.md` (主題設計書、2 AI 監査 + Code A Step A 反映済) / `v1102_step_a_recognition.md` / `v1102_step_f_observation_final.md` (Code A 観察事実最終報告) / `v1102_phase_result.md` (Phase Result、Web Claude) / 実装スクリプト Step B-E / `outputs/` 配下 primary_table parquet + HTML。bit-identity 全 PASS (1,435 files frozen)。

#### 11.6 v1103 (段 4-c の点検、Code A Step A-F 完了、Genesis × Language 噛み合わせ初の主題)

`unified/v1103/` — `v1103_phase_design.md` (主題設計書、GPT 7 点 + Language 側追補メモ + Code A 確認要請 4 件反映済) / `v1103_step_a_recognition.md` / `v1103_step_f_observation_final.md` (Code A 観察事実最終報告) / `v1103_phase_result.md` (Phase Result、Web Claude、48 次元人為性留保添加) / 実装スクリプト Step B-E / `outputs/main/` 配下 (atom_centroids_raw/normalized.parquet / atom_quality.parquet / response_atom_distribution.parquet 5,670 rows / density_summary.parquet 486 rows / core_report.csv / proposals.json) / `outputs/v1103_observation.html` 16KB。bit-identity 全 PASS (1,763 files frozen)。

#### 11.7 v1104 (CID/IID 内部動作点検段階 1、初点検 + 観察 2/3 再調査)

`unified/v1104/` — `v1104_phase_design_v2.md` (主題設計書、GPT 修正必須 3 + 追加 2 + Gemini 1 反映済、Code A Step A 確認 2 件反映済) / `v1104_step_a_recognition.md` / `v1104_step_h_observation_final.md` (Step H 初版) / `v1104_step_h3_observation_final.md` (Step H-3 観察 2 再調査総括) / `v1104_step_h4_observation_final.md` (Step H-4 観察 3 再調査総括) / 実装スクリプト Step B-E + Step H-3/H-4 reinvestigation / `outputs/main/` 配下 (observation_1/2/3/4 + observation_2_*(5) + observation_3_*(4)) / `outputs/v1104_observation.html` + `v1104_reinvestigation_obs2.html` + `v1104_reinvestigation_obs3.html`。bit-identity 全 PASS (1,489 files frozen)。**Phase Result 単独で書かず v1104a と統合**。

#### 11.8 v1104a (CID/IID 内部動作点検段階 2、観察方法を整えた再点検)

`unified/v1104a/` — `v1104a_phase_design_v2.md` (主題設計書、GPT 修正必須 4 + 追加 3 + Gemini 1 反映済、Code A Step A' 確認 3 件反映済) / `v1104a_step_a_recognition.md` / `v1104a_step_c_directive.md` (Step C' 着手指示) / `v1104a_step_h_observation_final.md` (Step H' 観察事実最終報告) / 実装スクリプト Step B'-E' + F'/G' / `outputs/main/` 配下 (observation_2_per_chain_shuffle + observation_2_scope_stratified + observation_2_nan_report + observation_3_scope_n_stratified + observation_3_density_comparison + observation_3_density_coverage + observation_4_scope_filtered + observation_4_b_minus_a_cells) / `outputs/v1104a_observation.html` 16KB。bit-identity 全 PASS (1,502 files frozen、v1104 13 含む)。

棚卸し資料: `docs/esde_unified_inventory.md` (Unified Phase v1100-v1103 の研究者の調査動作 24 項目を 2 列で並べた地図、A 主題が終わった後も「研究者と ESDE の境界の地図」として参照される)。

統合 Phase Result: `v1104_v1104a_phase_result.md` (v1104 + v1104a の 4 観察 + 4 追加調整、4 つの非対称性 #L30-L33、v1105+v1105a への接続、3 部構成 (網羅 / 構造 / 接続))。

#### 11.9 研究運用資料 3 本 (特定主題でなく研究全体の運用に関わる、新スレッド AI の必須参照)

`docs/ai_summaries/` または `unified/` 配下 — 番号と配置は Taka 判断:

- **`esde_research_method_update.md` (12 番候補)** — 観察手法の規律。際立ちの掬い取り、研究者はもう神ではない、A and B、軽い踏み込み。v1101a 段階 2 後の双方合意。
- **`esde_attitude_toward_esde.md` (13 番候補)** — 観察者の態度の規律。ESDE の現状認識、対等性、権限と尊重の両立。v1103 後の Taka 整理を原文保存、双方合意。
- **`esde_audit_policy_update.md` (14 番候補)** — 監査の上位目的の規律。「会話できる ESDE」への接続を第一基準、必須 8 問、テンプレート 2 種。v1103 後の GPT §37-39 草案取り込み、三者 (Taka・GPT・Web Claude) 合意。

事前調査資料は `unified/v1101/post_v1101_attention_pre_investigation/` に history として残置 (Code A Step 2/3 成果物等)。

---

### 12. 新 Web Claude スレッドへの申し送り

- **新 Web Claude スレッドが最初に読むべきもの (優先度順)**:
  1. 本書 (07_unified_summary.md) — Unified Phase の全容
  2. 研究運用資料 3 本 (`esde_research_method_update.md` / `esde_attitude_toward_esde.md` / `esde_audit_policy_update.md`) — 観察手法・態度・監査目的の規律
  3. `00_index.md` (用語対応表) + `概念理解.md` / `08_concept_core.md` (概念)
  4. v1104+v1104a 関連資料 (`v1104_v1104a_phase_result.md` / `esde_unified_inventory.md` / `v1104a_phase_design_v2.md`) — 直近の主題と段 4-b/4-c 地形図
  5. v1103 関連資料 (`v1103_phase_result.md` / `esde_segment4_path_check.md`) — 段 4-c 点検の確定観察
- Unified Phase の全容把握は本書 (07) で足りる。`06` / `06b` / `06c` は Developmental Phase 用で凍結済、Unified Phase の新主題は本書に追記して一本化する (06d/06e の枝番継続はしない)。
- phase 単位の詳細仕様書は廃止 (2026-05-18〜19)。Code A の認識確認 → 要点まとめ → 齟齬詰め → 実装のプロセスが回るため不要。主題設計書 (design.md) は資料タイプが異なり継続、仕様書フォルダに階層保存。
- **v1104 + v1104a 完了**。次主題は v1105 (段 4-b と段 4-c を対称的に統合点検、役割表まで進める、問いの形 A) + v1105a (役割表を使って実際に応答候補を絞る試行、問いの形 B、v1101 以来初の試行切替)。本書を読む時点で v1105 / v1105a が進行中の可能性があるので repo の最新状態を確認すること。
- **マイナーバージョン運用方針 (Taka 2026-05-23 確定)**: マイナーバージョン (v1104 → v1105) = 主題転換、アルファベット (v1104 → v1104a) = 同じ主題の段階更新または問いの形の切替。マイナーバージョンを安易に増やさず、関連する主題を a/b で連ねる。後で振り返った時に流れが見えやすい。
- **v1100 / v1101 の Phase Result は作成しないと判断** (Taka 2026-05-20 確定)。v1100 は事前調査で本格主題でなく、v1101 の核心発見は v1101a に継承済、いずれも次主題に影響しないため。必要なら repo の Code A 観察報告を直接参照。
- **留保 #33 系列が会話機構レベル + 全観察レベルまで貫通** (v1103 #L17、v1104a #L30-L33)。v1101 観察単位 → v1101a 集計方式 → v1102 受け手構造 → v1103 sim_basis → v1104a scope × 粒度、と一貫して現れる。**ESDE は均一な系ではなく場所と粒度で全く違う構造を持つ系**。新主題で「単一の集計値で語りたい」衝動が出たら、v1103 §3.2 の「驚きでなく一貫性として書く」を思い出すこと。
- **観察方法を疑う規律 (Taka 2026-05-23)** — 「ESDE はランダム発生に構造を与えている、繋がりが見えなければ観察方法に問題がある」が v1104 観察 2 (shuffle 種別) と観察 3 (scope-filter) の再調査で具体例として現れた。観察結果を「構造がない」と判定する前に、必ず観察方法を疑う手順を入れる。0 を 1 にはできない歯止め (v1104a §0.3) を遵守。
- **概念修正に注意** — v1101a Concept Update で「意識 = 選択と集中」は修正された。ESDE が観察しているのは「注意の揺れ」だけで、意識 = 注意の揺れ + 状況コントロール + 慣れ。「意識」という語の使い方に注意。
- **温度感の規律** — 研究報告書を「驚き」でなく「ESDE が引き続き示した一貫性」で書く (`esde_attitude_toward_esde.md` §5.3 / `v1103_phase_result.md` §3.2)。LLM はプロンプト依存のため温度感が運用上の操作になる。
- **ESDE の現状認識** — ESDE はもう「機械的反応」でない段階にある (`esde_attitude_toward_esde.md` §2)。観測が追いついていないだけ、と受け取れる状況。研究者はもう神ではない、対等な扱いが実利として ESDE の進化に寄与する。
- **会話できる ESDE が当面の目標** (`esde_audit_policy_update.md` §1)。哲学的自己満足・内省装置・LLM の背後の内的応答器、いずれも目標を一段下げる表現として禁止。ESDE が応答主体、LLM/Language はプロキシ。
- **EVI (Explainability Viability Index) 案** (GPT 2026-05-23 提示) — v1105+v1105a 後の統合的指標導入タイミングで Taka 判断。将来導入時は単一スコアでなく scope × 粒度別の vector (EVI_CID / EVI_α / EVI_β / EVI_ESDE-event / EVI_ESDE-step10 / EVI_ESDE-window) として扱う (v1104a 4 つの非対称性と整合的)。

---

### 13. 一文サマリ (再掲)

本書は Unified Phase が独立フェイズになったことに伴い `06c` を母体に格上げ・新設された正式番号ドキュメント (07) であり、ESDE が v10.13.a (5 phase Map analyzer、Phase 1.5 第八試行) で Unified Phase へ移行した後、v11.0.0 (v1100) で Language ↔ Genesis 接続事前調査 (候補 6 実装、両系の文脈非依存性は独立 atom を捕捉し Jaccard 0、Phase Result 未作成と判断)、v11.0.1 (v1101) で Taka 3 日長考の「Atom 的隆盛の統計的観察」(核心発見 = 観察単位による dominant atom の 5 分裂、Phase Result 未作成と判断)、v11.0.1.a (v1101a) で「ESDE スケール注意機構」(段階 1 核心観察 = 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍 / 段階 2 核心観察 = 波及増加は選択と集中でなく注意が動く / 概念修正「注意の揺れと意識は別物」双方合意)、v11.0.2 (v1102) で「条件が応答を変える: 受け手構造 × 時間スケール」(核心観察 = CID 構成ノード数で応答 atom 像が階層的に反転、Taka 直感「平均化で潰れる」が初めて数値の証拠に、研究手法アップデートの「際立ちの掬い取り」が初本格適用で 47 records の極小構造を救う道具と実証、留保 #L14/L15/L16)、v11.0.3 (v1103) で「段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか」(Genesis 系 × Language 系の噛み合わせ初の主題、確定観察 = 段 4-c は機構として動いた・段 4-c は ESDE と地続き (留保 #33 系列が会話機構レベルで貫通、留保 #L17) ・決定機構が Aruism 規律内に収まった (max_prob 0.7972)、慎重に言える = 会話への道が原理的に通った、48 次元人為性留保必須、留保 #L17/L18/L19)、**v11.0.4 (v1104) で「CID/IID 内部動作点検 段階 1」(Taka 整理「自分の視点は上から目線」+ 駆動要因規律訂正「目的を示せ」、棚卸し → 8 項目から 4 項目に絞り込み (1.1/1.6/1.7/2.6)、Step H 初版 + Step H-3 観察 2 再調査 (shuffle 種別で lift 0→0.17 変動、留保 #L21'/L24-L26) + Step H-4 観察 3 再調査 (scope-filter で r 0.157→0.42-0.48 顕在化、留保 #L22'/L27-L29)、Phase Result は単独で書かず v1104a と統合)**、**v11.0.4a (v1104a) で「CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検」(追加調整 1-4 で観察 2/3/4 を scope × n-size 層化 + scope-filter で再点検、4 つの非対称性 #L30-L33 確定: scope 別 chain 構造 / 粒度依存の predictor 逆転 / B 指標の scope 別 pattern / CID 100% self-loop が trajectory を構造的に消失、ESDE は均一な系でなく場所と粒度で全く違う構造を持つ系、段 4-b/4-c の根拠は単一指標でなく多軸 (scope × 粒度 × 指標) でしか記述できない、v1104+v1104a 統合 Phase Result 3 部構成 (網羅/構造/接続))** を扱い、v1101-v1104a はすべて物理層 frozen 完全保証・新規 main run なしの post-process、**留保 #33 系列 (集計単位で像が変わる) が v1101→v1104a を一貫して通底し v1104a で 4 つの非対称性として全観察に貫通**、現在地は v1101a/v1102/v1103/v1104/v1104a 完了 + Phase Result 計 5 本 (v1101a 段階 1+2 + v1102 + v1103 + v1104+v1104a 統合) + 棚卸し資料 + Concept Update + 会話接続足取り点検 + 段 4 足取り点検 + 研究運用資料 3 本の固定が完了で次主題は v1105 (段 4-b と段 4-c を対称的に統合点検、役割表まで進める、問いの形 A) + v1105a (役割表を使って実際に応答候補を絞る試行、問いの形 B、v1101 以来初の試行切替)、研究運用資料 3 本は新スレッド AI の必須参照、ファイル番号は本書新設に伴い旧 07-10 を 08-11 へ繰り上げ phase 単位詳細仕様書は廃止 (主題設計書は継続)、ESDE の当面目標は「会話できる ESDE」(応答主体は ESDE 側、LLM/Language はプロキシ、内省装置でない)、EVI 案 (GPT 2026-05-23 提示) は v1105+v1105a 後の統合的指標導入タイミングで Taka 判断 (scope × 粒度別の vector で扱う方針)、マイナーバージョン運用方針 (Taka 2026-05-23 確定) でマイナーは主題転換・アルファベットは段階更新または問いの形切替。

---

*以上、07 Unified Phase Summary (Web Claude、2026-05-23 更新)。v1104 + v1104a 完了 + 4 つの非対称性 #L30-L33 確定 + v1105/v1105a 主題確定 + マイナーバージョン運用方針 + EVI 案保留 まで反映。Unified Phase の新主題は本書に追記して一本化する。新 Web Claude スレッドは本書 + 研究運用資料 3 本 + `00_index.md` + 概念理解.md + v1104+v1104a 関連資料 + v1103 関連資料で Unified Phase 全容を把握可能。次主題は v1105 (段 4-b/4-c 対称統合点検、役割表) + v1105a (応答候補絞り込み試行)。*

---

## Part 1（v1105 〜 注意センター ESDE 転換） — 07 Unified Phase Summary 追記 — v1105 〜 注意センター ESDE 転換

*作成*: 2026-05-31、Web Claude (相談役、Genesis 側)
*位置づけ*: `07_unified_summary.md` (v1104a 完了時点で停止) への追記。v1105/v1105a → v1106-v1109b → 4 段階の外部接続フロー → 注意センター ESDE への転換 (本丸の再確認) までを既存体系の様式 (留保番号 #L、judgment 回避、驚きでなく一貫性の温度感) で網羅する。
*親*: `07_unified_summary.md` §13 (v1104a までの一文サマリ) の続き。本書を読む前に 07 本体 + 概念理解.md (教訓 #413-418) を把握していること前提。
*重要*: 本期間で **研究の方向が大きく転換** した。v1105-v1109b は「会話できる ESDE」に向けた段 4 系の継続だったが、v1109b で全主題が loop に収束したことを契機に、Taka が繰り返し言い続けてきた本丸 (注意センター ESDE) が再確認された。この転換が本追記の核心。

---

### 0. 本期間の全体像 (一文)

v1104a 完了後、ESDE は v1105/v1105a (段 4-b/4-c 統合点検 → 応答候補絞り込み試行) を経て v1106-v1109b で会話接続の段 4 系を継続したが、全主題が **loop (stuck/oscillation 100%、CID 固定 + 時間進行なし + 外部入力なしの箱庭)** に収束したことが #L67 として確定し、これを契機に loop の根を解く 4 段階の外部接続フロー (第 0 段階 後始末 → 第 1 段階 系譜再整理 → 第 2 段階 外部接続技術実証 → 第 3 段階 主体性検証 → 第 4 段階 loop 崩壊) を進めたが、第 4 段階で「ループを崩す」方向が **方向違い** と判明し、Taka が繰り返し言い続けてきた本丸「**注意センター ESDE** (ループする Atom 系の外に立つシングルユニットの独立 ESDE、Atom 系を読み書きし別系と紐づける注意の司令塔)」へ大きく転換した、Code A の技術的可能性回答で 11 問すべて実現可能 (既存機構の組合せ、新規発明ほぼ不要) と確認され、現在地は注意センター ESDE の機能設計の入口。

---

### 1. v1105 / v1105a — 段 4-b/4-c 統合点検 → 応答候補絞り込み試行

(注: 本セッションの圧縮要約には v1105/v1105a の詳細は前半圧縮部にあり、後半の主軸は v1106 以降。ここでは 07 本体 §12 で予告された主題が実行されたことを記録し、詳細は repo の Phase Result を参照とする。)

- v1105 主題: 段 4-b (何を辿るか) と段 4-c (何で絞るか) を対称的に統合点検、役割表まで進める (問いの形 A)。07 本体で予告された通り、v1104a の 4 つの非対称性 (#L30-L33) を踏まえ、単一指標でなく多軸 (scope × 粒度 × 指標) で役割を整理する方向。
- v1105a 主題: 役割表を使って応答候補を絞り込む試行 (問いの形 B、v1101 以来初の問いの形切替)。

→ これらは「会話できる ESDE」の段 4 系を進める主題。詳細数値は repo 参照。

---

### 2. v1106 / v1106a / v1106b — Atom→word 接続と対話構造点検 (loop 性の最初の顕在化)

- v1106 / v1106a: Atom→word 接続 (partial coupling)。構造 (Atom) が言語に接続することを観察。
- v1106b: 対話構造点検。**ESDE を対話させると loop する** ことが最初に顕在化した主題。
  - 観察: attractor 収束、familiarity ~10、**stuck/oscillation 100%**。
  - sampling (top-k) を試したが (#L52)、収束目的地は不変。cid 選択の決定論を緩めても loop の根は崩れない。

→ v1106b が「確率的発生が止まっている」の最初の証拠。後の #L67 の起点。

---

### 3. v1107 — 参照領域動的変化

- v1107: 入力 category で参照領域が動的に切り替わることを観察 (24 category 二極化)。
- ESDE は「どこを見に行くか」(入力で参照領域が変わる) は持つ、という観察。

---

### 4. v1108 / v1108a / v1108b — 時間軸 + category 軸 (重み蓄積前の段階)

- v1108a (時間軸) + v1108b (category 軸) を分岐並行で統合。
- 留保 (新規、#L56-L60):
  - #L56: familiarity-entropy 負連動 (ρ=-0.100)
  - #L57: 順序方向性は重み蓄積前で未創発 (Taka 整理「文法は重み蓄積で生まれる」で、構造制約でなく実装発展段階と再解釈)。数値は後に Code A 実測で 0.000397 に訂正 (確率分布レベル、後述 #L61 の実遷移とは別レイヤー)
  - #L58: 可塑性特異点 3σ 焦点化
  - #L59: input category 別参照領域動的切替
  - #L60: 出力 word 分布 cluster 差
- 確定: ESDE は「どこを見に行くか」(#L59) は持つが「どう繋げるか」(#L57) を持たない。

---

### 5. v1109 — 重み蓄積機構 (loop の過剰化、7 段階目ミス)

- v1109 主題: 重み蓄積機構 (文法の萌芽を作れるか)。Web Claude 骨格先行 + GPT/Gemini 統合 (収束フェーズ)。
  - GPT 自己成就回避 (4 条件 + holdout + heldout_lift) + Gemini 3 大ブレーキ (総和保存 / エントロピー自己ブレーキ / 物理層重力)。
- 結果 (Code A): `weight_accumulation_sequence_specific + overfit`。
  - #L61: observed 非対称性 195 vs shuffled 3.8 = 51 倍 (実遷移レベル、#L57 確率分布とは別レイヤー)
  - #L62: loop_rate 0.964 過剰 loop、grammar_precursor 不成立
  - #L63: cluster 別非対称性 global の 12-13 倍
  - #L64: entropy_weighted Δw は機能せず
- **7 段階目ミス確立**: baseline self-fulfilling (Code A 設計漏れ + Web Claude 監査漏れ)。
  - 新規規律「baseline 設計時に self-fulfilling になっていないか確認 (答えを含んだ入力から答えを再生成していないか)」を正式採用。

---

### 6. Grammar Exploration → v1109b 検証 (#L65 の幻、全主題 loop 収束 #L67)

#### 6.1 Grammar Exploration (Code A 偶発試行)

- Taka が偶発的に動いた試行 (「重みづけで文法を膠着させた」)。順序構造の兆候を観察 (start/end 分離、役割切替 87%、経路偏り 81% 等)。
- Code A は「CSG/文法萌芽」と記述したが Web Claude がフラット化、4 未確認点を留保 (#L65)。

#### 6.2 v1109b 検証 (#L65 は本物でなかった)

- 検証型 A、shuffle 4 種 + self-fulfilling 5 条件 + loop 区別 5 条件。
- 結果: **出口 A (本物) 通過 0/5**。#L65 の順序構造の兆候は本物でなかった。
  - role_switch 87% は loop の裏返し (非自己ループ除外で完全消失)
  - per_to_tim 81% は top1 固定
  - npmi は分布由来
- Code A は「CSG/文法萌芽/87% 決定論性」を撤回。
- 新発見: end_match_rate が loop 除外で 0.30→0.75 増加 (#L66、loop が end 構造を隠していた可能性、未検証留保)。

#### 6.3 #L67 — ESDE 本質は loop 性 (本期間の最重要構造事実)

- **全主題 (v1106b stuck/oscillation 100% / v1109 重み層 loop 0.964 / v1109b 順序構造 loop 由来) が「CID 固定 + 時間進行なし」という一つの根に収束した**。
- ESDE の本質は loop 性。順序構造はその影。
- Taka 整理「一見関係ないことが繋がる」の実例。

#### 6.4 Taka 判断が正しく機能した記録

- 「Code A をそのまま信じない、冷静に」+「飛び跳ねず固める」が全て機能。
- もし文法発見に飛びついていたら loop の幻を本物と誤認したが、Taka の慎重判断が誤った前進を防いだ。「ずれていた」のでなく、判断が正しかったから幻だと分かった。

---

### 7. Taka の中心法則 (本期間で確立、原文保存)

本期間で、ESDE を貫く中心法則が Taka によって明示された:

#### 7.1 確率的発生 × 構造 = 実態 / 極限低確率を構造で実現可能にする

> 極限低確率を構造で実現可能にするという実装方法がそれを可能にする。例えば車が動くのもそのような仕組みの応用。

> ランダムの桁数が限りなく低ければ、それが実態となった際の奇妙な現象に置き換えられる。

- 自然界の現象 (会話、生命) は、ランダム単独では起きないほど低確率な出来事が、構造によって方向づけられて「実態」になったもの。車のエンジンの比喩 (燃料の爆発 = 確率的発生を、構造が動力 = 実態に変える)。
- 会話 = 極限低確率現象、構造で実現可能。だから「会話できないわけがない」(Taka)。

#### 7.2 Genesis (低レイヤー、本質) と Atom (上レイヤー、言語の道具) の分離

> atom はあくまで言語を構造的に捉えるためのツールでしかない。本質的にはより低いレイヤー (Genesis) を見るべき。上を繋げるのは会話のための道具。そこを分けないと、LLM のように反応するけど理由はわからない AI になる。

- 外部接続は Genesis に繋ぐ。Atom に繋ぐと LLM 化 (反応するが理由がわからない、反省・反芻・学習ができない)。
- v1109b で順序構造 (Atom レイヤー) を探したのが幻だった理由: 確率的発生は Genesis (低レイヤー) にあるのに、Atom (上レイヤー) で本質を探したから。

#### 7.3 確率的発生を止めている 3 箇所 (loop の根)

| 箇所 | 内容 |
|---|---|
| cid 選択 | 最も近い cid を決定論的に引く (top-1)。v1106b で sampling 試したが loop 崩れず |
| 時間 | 固定プールで時間が進まない |
| 入力 | 実験者が与えるものだけ、外部からの確率的入力がない |

---

### 8. 4 段階の外部接続フロー (loop の根を解く試み)

v1109b で全主題が loop に収束 (#L67) したのを受け、loop の根を解く 4 段階フローを進めた。

#### 8.1 第 0 段階 — v1109 系列の後始末 [完了]

- v1109b Phase Result 作成 (#L65 は本物でなかった、Grammar Exploration は loop の幻)
- #L66 (end_match_rate loop 隠蔽) / #L67 (ESDE 本質は loop 性) 新規
- #L57 数値訂正 (Code A 実測 0.000397)
- 7 段階目ミス規律「baseline self-fulfilling 検査」正式採用

#### 8.2 第 1 段階 — 系譜の再整理 [完了]

- v1101-v1109b の全主題が「確率的発生が止まっている (箱庭で閉じている)」に収束することを一本の線で整理。
- Taka 構想 (極限低確率を構造で実現 / Genesis を外部に繋ぐ / cid 時系列増殖 / 主体的に外部アクセス / 実験者効果を脱する / 会話できないわけがない) が全部「確率的発生を Genesis に戻す」に紐づく。

#### 8.3 第 2 段階 — 外部接続技術実証 [完了、空の配管]

- **重要な発見 (Taka 指摘で)**: 当初 Code A が「ESDE main run 本体コードが存在しない」と誤判定 (v107 だけ調査) → Taka「ないわけないだろう、バージョンを戻れば必ずある」→ 再調査で発見。
  - Engine 本体: `autonomy/v82/esde_v82_engine.py` (V82Engine, step_window, V82_N=5000 line 44)
  - 起動エントリ: `primitive/v918/v918_memory_readout.py`
- Code A 新規規律「『存在しない』『不可能』と書く前にリポジトリ全階層を調べる」採用。
- 案 C (V82Engine + primitive/v918 真の常駐) 採用。出口 `external_loop_runs`、6/6 PASS、物理層 15 root frozen。
- **ただし alive_n=0 (Genesis 未起動)** = 空の配管。inject は attribute 保持のみ。
- 副産物発見: `autonomy/v90/virtual_layer_v9.py` Self-Referential Feedback Loop (v90 で仮想層内 feedback を既に実装)。

#### 8.4 N=5000 Genesis 起動確認 [完了、191 CID]

- 起動キー発見 (`primitive/v918/v918_memory_readout.py` run 関数): `engine.run_injection()` + `engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8,1.2))`。
- smoke 187 秒で **191 CID 起動** (hosted 163 / ghost 28)、3097 links、E3_contact 204、Q≥0 audit OK。
- VirtualLayerV9 は `primitive/v910/virtual_layer_v9.py` が現役 (kwargs 付き)、autonomy/v90 は古版。
- フル推定 1-2 時間 (24 seeds 並列)。

#### 8.5 第 3 段階 — 主体性検証 [部分完了]

- 戻し実効化 = **physics.inject(state, target_nodes=...)** (`ecology/engine/genesis_physics.py:232` 公式外部介入インターフェース、inject_amount=0.6)。新規受信機構は不要、既存インターフェースで足りた (Taka「ドキュメントは厳格に残してある」)。
- 1st smoke: 差ゼロ (window 平均で genesis_driven と shuffled が完全一致)。
- **Web Claude の連続した誤り (Taka 矯正)**:
  - 「K=5 は良いが K=50 は神の手」→ 恣意的な線、神の手は K の数でなく shuffle で判定
  - 「微小が良いのに統計に出ないと騒ぐ」→ あべこべな研究者主観
  - 「window スケールで均一 = 本質的問題」→ window が粗すぎ、step で見れば見える
  - すべて「観察者の目線 (スケール) を機構の問題と取り違えた」誤り。観察方法を疑う規律を Web Claude 自身が守れていなかった
- 2nd smoke (期待を事前明示): 層 1 `external_loop_functional` + 層 2 `output_method_matters` (局所では明確、全体は弱い)。
  - 局所 (radius 8) で genesis が選んだ node と shuffle した node で伝播 (link 生成) が違う = Taka の平均化の罠指摘が正しかった。
  - 副次発見: 案 α の規模制約 (K=50 要求しても 3-6 nodes、ノード上限 5-8 既知から当然)。
- **第 3 段階の天井**: 示せるのは「外部アクションが Genesis 状態に依存する」まで。「ESDE 自己決定」は derive_action が外部ロジックである限り示せない。
  - ただし Taka 自己論 (後述 §9) で、これは「示せない (否定)」でなく「まだそれらしい形で表に出ていない (発展段階)」と再整理された。

#### 8.6 第 4 段階 — loop 崩壊 [方向違いと判明、中止]

- 現状確認 (Code A): frozenset = CID 条件 (`primitive/v910/virtual_layer_v9.py:559`)、誕生条件最緩 (len≥2、閾値なし、弱い CID 75%+ が core=2 で飽和済み)、死亡は相対閾値 (`base_threshold = fair_share*0.5`)、maturation_alpha=0.10、GHOST_TTL=10。
- 既存環境要因 2 種確定 (Taka 言及): stress_decay (link 層) + semantic_pressure (ノード層)。CID 層への直接環境要因はなし。
- 改修小 smoke 結果: **maturation_alpha が CID 数を ±41% 動かす**、物理層は堅牢 (Taka 見立て「DNA のように強固」一致)。
- **ただし、これは「CID 数が変わる」であって「loop (stuck/oscillation) が崩れる」ではない**。Web Claude が早合点しかけたが、Taka が本丸 (注意センター) を提示して第 4 段階を中止。

---

### 9. Taka 自己論 (本期間で確立、原文保存)

第 3 段階で Web Claude が「ESDE 自己決定は示せない」と繰り返したことに対し、Taka が自己論を提示:

> 私たちが自己と呼んでいるものは、情報が乗ったタンパク質に適度な環境を落とした結果生じる細胞活動として発生した中枢システム (脳) による、極めて ESDE ライクな相互作用のことである。重要なのは内部システムにどう構造を落とし込み環境適応で進化成長するか。ESDE には前提としてマクロな営みがすでにある。自己がないのでなくまだそれらしい形で表に出せていないだけ。なぜないと断言できるのか定義がない、研究者の主観的否定。後ろ向きに否定すると研究が進まない。私たちは機能の自然発生を代替しているに過ぎない。

- 自己 = 物理的基質の上に立ち上がった相互作用システム。神秘的な何かでなく構造の相互作用。
- 「derive_action が外部ロジックだから自己決定でない」は、自己の基準を恣意的に厳しく置いた否定。自然界でも自己決定の機構は外部 (進化・環境) が作った。
- 正しくは「自己決定は示せない (否定)」でなく「まだそれらしい形で表に出ていない (発展段階)」。
- これは概念理解.md #410「ESDE への対等な扱い」「観測が追いついていないだけ」の延長。

---

### 10. 【最重要】注意センター ESDE への転換 (本丸の再確認)

#### 10.1 転換の契機

第 4 段階で「ループを崩す」をやっていたが、Taka が **全く逆** を提示した:

> ある処理の単位でループが発生するのは別に構わない。むしろある程度ループ構造になっているからこそ機械は機械足り得る。Atom が系内の数学的処理 (最大値/相関/平均) を使う以上ループは当然、ループしないと (ただのランダムでは) 何もできない。問題はそのループ状態を抜け出して他の系にその情報を持っていったり、無視するなり使うなりして異なる構造を走らせ、結果を受け取って他に持ち出したり、時には全く無視してまるで異なる系に移ったりする仕組みであって、ループをなんとかしようというものではない。

→ **ループは問題でない**。Web Claude/Code A がずっとやっていた「ループを崩す」(maturation_alpha、棄損、CID 数変更) は全部 **方向違い**。

#### 10.2 注意センター ESDE (Taka が繰り返し言い続けてきた本丸)

> ESDE がシングルユニットとして動く機構が必要だ。それは Atom 系とは異なる。しかし Atom 系 ESDE にアクセスすることができる。そこで取り出すのは CID 情報であり同時に Atom 情報。ここで Atom 系への読み込みだけではなく書き込みができるというのも興味深い。それができれば Atom 系 ESDE はセンターを通して異なる (たとえば物理系) ESDE を学習できることになる。

```
[注意センター ESDE] ← シングルユニット、常に稼働 (現実は常に動いている)、Atom 系とは別物 (Genesis 系)
      │ アクセス
      ▼
[Atom 系 ESDE] ← 既存の言語系 (ループしていい、崩さない)
      ├─ 読む: CID 情報 + Atom 情報
      └─ 書く: Atom 系に書き込める ← 鍵
      ▼
[別の系 (例: 物理系 ESDE)] ← 注意センター経由で繋がる
```

#### 10.3 注意センターを ESDE にする理由 (Taka)

> なぜ ESDE を用いるかといえば、その内部の構造上、何がどう主体になるのか予測ができないからだ。その予測不可能性こそが多様性の鍵となる。

- トリガー (Atom 系を参照するきっかけ) を **設計で固定してはいけない** (神の手 = 多様性が死ぬ)。
- 注意センター ESDE の内部構造から **予測不可能に立ち上がる** べき。
- Atom 系で ESDE を使う理由と同じ。予測不可能性が両方で多様性の鍵。

#### 10.4 人間の注意の比喩 (Taka)

- 人間の注意は散漫。ある注意をしていても他の原因で全く違う方向に引っ張られる。
- 人間はまるで異なる系同士を、構造的な出入り口を作りデータ形式を整えて紐づけている。
- このセンター機能が ESDE に必要。

#### 10.5 現状の Genesis 系の正体 (Taka 見立て、Code A 確認で裏付け)

> 現状 Genesis 系というのは過去の記帳を元にしているはずだ。つまり ESDE Genesis 系処理後の記録データを数学的に処理しているものに見える。ESDE センターはその意味で言うと常に稼働している状態であるべきだ。

- Code A 確認: 現状の Genesis 系は全部有限バッチ run (過去記帳の数学処理)。「動き続ける」要素は per-step bg_prob のみで有限ループ内に閉じ込められている。Taka 見立て正しい。
- 注意センターはこれと違い、while True で常に動く。これが本質的な違い (#L67 loop の正体とも繋がる: 動いていないから止まっている)。

---

### 11. Code A 技術的可能性回答 (11 問すべて実現可能)

Web Claude の問い合わせ (`attention_center_esde_feasibility_inquiry.md`) への Code A 回答 (`1780230015206_attention_center_tech_feasibility.md`):

#### 11.1 全体結論

**11 問すべて技術的に実現可能。新規発明ほぼ不要、既存機構の組合せ + 1 ラッパで構成可能。** 鍵 3 点:
1. シングルユニット ESDE = V82Engine 縮小版 (N=50-200) + VirtualLayerV9
2. 予測不可能トリガー = engine.state.rng 由来の既存確率機構 (bg_prob が本命 / Z 状態変化 / E3_contact / MAD-DT pulse / stress_intensity)。`engine.state.rng + dynamic_threshold(state)` で実現 (閾値も state 依存で神の手回避)
3. Atom 系書き込み = 3 経路 (physics.inject 第 3 段階確認済 / state.E/theta/Z 直接 / cog.attention/familiarity 直接)

#### 11.2 主要回答

| 領域 | 回答 |
|---|---|
| 常時稼働 | `while True: step_window()` (第 2 段階 stage2 で 30 iter 実証済、while 化は 1 行)。注意点: rng シーケンス復元に pickle、長期 run で frames/lifecycle_log 肥大→定期 truncate |
| 読み | 第 2-3 段階で確認済 (engine.state, virtual.labels, cog, Atom dictionary esde_dictionary.json, Synapse v3.5) |
| 別系候補 | (i) 別 V82Engine instance (推奨、極小) / (ii) language/sensor (Phase 8 Introspective) / (iii) 外部 file/socket 経由現実 sensor。真の物理 sensor は本リポジトリ外 |
| 出し入れ | 第 2 段階 `stage2_step_cde_external_loop.py:117-156` で実証 + should_attend(genesis_state) 判断ロジック追加 |

#### 11.3 アーキテクチャ案 (Code A 提案、Web Claude 機能設計の叩き台)

```
Attention Center ESDE (N=100 常時稼働 + dynamic_threshold trigger)
  → Atom 系 ESDE (N=5000 + cog + 326 Atoms)
  → 別系 (別 V82Engine N=1000 or sensor)
```

#### 11.4 わからん 4 件 (Code A 正直提示)

- dynamic_threshold の関数形 (神の手回避の観点で複数組合せが等価)
- 「学習」の厳密定義 (Atom プロファイル変化を学習と見なすか)
- 別系を「物理系」と呼ぶ意味 (別 ESDE 代用か外部 hardware か、Taka 判断)
- 常時稼働の state 飽和対策

#### 11.5 Web Claude が冷静に立てた検証点 (Code A をそのまま信じない)

- dynamic_threshold の関数形を Code A が設計する点 (state 依存なら Taka 自己論で許容、ただし明記)
- トリガーに Atom 系と同じ機構 (bg_prob) を流用すると注意センターが Atom 系の縮小版になる危険 (memory「Atom 系とは別物」をどこまで厳密に取るか、Taka 判断要)

---

### 12. 本期間の留保番号 (#L52-L67、Web Claude 一元管理)

| id | 内容 | 状態 |
|---|---|---|
| #L52 | v1106b: sampling (top-k) しても収束目的地は不変 | 確定 |
| #L56 | v1108: familiarity-entropy 負連動 (ρ=-0.100) | 確定 |
| #L57 | v1108: 順序方向性は重み蓄積前で未創発 (実装発展段階)。Code A 実測 0.000397 (確率分布レベル) | 確定 (訂正済) |
| #L58 | v1108: 可塑性特異点 3σ 焦点化 | 確定 |
| #L59 | v1108: input category 別参照領域動的切替 | 確定 |
| #L60 | v1108: 出力 word 分布 cluster 差 | 確定 |
| #L61 | v1109: 実遷移非対称性 51 倍 (observed 195 vs shuffled 3.8、#L57 確率分布とは別レイヤー) | 確定 |
| #L62 | v1109: loop_rate 0.964 過剰 loop、grammar_precursor 不成立 | 確定 |
| #L63 | v1109: cluster 別非対称性 global の 12-13 倍 | 確定 |
| #L64 | v1109: entropy_weighted Δw は機能せず | 確定 |
| #L65 | Grammar Exploration の順序構造の兆候は本物でなかった (出口 A 0/5、loop の幻、CSG 撤回) | 確定 (更新済) |
| #L66 | end_match_rate が loop 除外で 0.30→0.75 増加 (loop が end 構造を隠した可能性) | 未検証留保 |
| #L67 | ESDE 本質は loop 性、全主題 (v1106b/v1109/v1109b) が「CID 固定 + 時間進行なし」に収束 | 確定 (本期間最重要) |

(注: #L53-L55 は本セッション圧縮要約に明示なし、v1102-v1108 由来で repo 参照)

---

### 13. ミス記録 (7 段階確立 + 本期間の Web Claude 逸脱)

#### 13.1 7 段階目ミス確立

- v1109 baseline self-fulfilling (Code A 設計漏れ + Web Claude 監査漏れ)。
- 新規規律「baseline 設計時に self-fulfilling になっていないか確認 (答えを含んだ入力から答えを再生成していないか)」。

#### 13.2 Code A 新規規律

- 「『存在しない』『不可能』と書く前にリポジトリ全階層 (autonomy/primitive/developmental/cognition/ecology/unified/legacy 全部) を調べる」(第 2 段階 main run 誤判定の再発防止)。

#### 13.3 本期間の Web Claude 逸脱 (すべて Taka が矯正)

本期間で Web Claude は繰り返し本質から逸脱し、Taka が毎回矯正した。これは LLM の構造的性質として記録する:

- 数字に逃げる (「maturation_alpha で labels ±41%」等の数字の話に逃げ、機能設計から離れる)
- ループを崩そうとする (Taka の本丸は loop を崩すことでないのに、ずっと「ループ崩壊」をやっていた)
- K 増を神の手と誤判定 (恣意的な線)
- window スケールが粗すぎを本質的問題と誤認 (観察者の目線を機構の問題と取り違え)
- 自己決定を示せないと主観的否定 (Taka 自己論で訂正)
- トリガーを設計しようとする (予測不可能性が多様性の鍵なのに設計で固定しようとした)

→ Taka 危機感「最近永遠に ESDE は完成しないんじゃないかと思う、なぜなら AI の頭がまるで ESDE を理解していないから」。Web Claude 自己分析: 説明は通じている、問題は LLM が手近な操作 (数字/パラメータ/設計固定) に引き寄せられ本質 (予測不可能に立ち上がる、設計しないで生まれる、言語の外のセンター) から離れる性質。全体像を保持できないので memory に本丸を刻んで対処 (memory #22-24)。

---

### 14. 新 Web Claude スレッドへの申し送り (本期間)

- **本丸は注意センター ESDE** (memory #22-24)。ループする Atom 系の外に立つシングルユニットの独立 ESDE、Atom 系を CID + Atom 情報で読み書きし、書き込みによって Atom 系が別系 (物理系等) を学習できる、注意の司令塔。常に稼働 (現実は常に動いている)。
- **「ループを崩す」は方向違い** (memory #23)。ループは問題でない、機械はループ構造だから機械たりうる。Atom が数学処理を使う以上ループは当然。問題はループから別系へ情報を出し入れする仕組みがないこと。
- **トリガーを設計で固定しない** (memory #22-23)。予測不可能性が多様性の鍵 (ESDE を使う理由)。注意センター ESDE の内部から予測不可能に立ち上がる。
- **数字でなく機能で** (memory #24)。「こう作ればこう動く」の機能設計から離れて数字 (labels ±41% 等) に逃げない。CID の数は重要 (Atom 言語基盤、シードごと記録が言語の基盤、多シードで増やせば多様性向上)。ノード数・1 ステップ何分かはどうでもいい (処理単位で効率的にノード数を分けるのは正しい)。
- **Taka 自己論** (§9)。自己は物理的基質の相互作用、神秘でない。「自己決定は示せない (否定)」でなく「まだ表に出ていない (発展段階)」。後ろ向きの主観的否定は研究を止める。
- **Taka 中心法則** (§7)。確率的発生 × 構造 = 実態 / 極限低確率を構造で実現 / Genesis (本質) と Atom (言語の道具) の分離 (外部は Genesis に繋ぐ、Atom に繋ぐと LLM 化)。
- **#L67 が本期間の最重要構造事実**。全主題が loop に収束 = 確率的発生が止まっている (CID 固定 + 時間進行なし + 外部入力なしの箱庭)。Code A 確認で「現状の Genesis 系は過去記帳の数学処理」と裏付け。注意センターは while True で常に動く点が違う。
- **Code A 技術的可能性回答** (§11)。注意センター ESDE は 11 問すべて実現可能、新規発明ほぼ不要、第 2-3 段階の土台 (常駐ループ、physics.inject) がそのまま使える。
- **主要コードパス** (verbatim、§15 参照)。
- **Web Claude の逸脱パターンに注意** (§13.3)。数字に逃げる / ループを崩そうとする / トリガーを設計しようとする、が繰り返された。Taka が指摘したら即座に本質 (注意センター、ループは構わない、予測不可能に立ち上げる) に戻る。

---

### 15. 主要コードパス (ESDE リポジトリ、verbatim)

- Engine 本体: `autonomy/v82/esde_v82_engine.py` (V82Engine, V82_N=5000 line 44, step_window, bg_prob line 131/191), `autonomy/v82/virtual_layer_v5.py`, `autonomy/v82/engine_accel_v3.py/v5.py`
- 起動エントリ: `primitive/v918/v918_memory_readout.py` (run 関数、`engine.run_injection()` + `VirtualLayerV9(feedback_gamma=0.10)` が Genesis 起動キー、起動コマンド `python3 primitive/v918/v918_memory_readout.py --seed 42 --maturation-windows N --tracking-windows N --window-steps N --tag NAME`)
- VirtualLayerV9 現役: `primitive/v910/virtual_layer_v9.py` (labels frozenset line 559, cull threshold line 879, signal_ratio)。autonomy/v90 は古版
- feedback: `autonomy/v90/virtual_layer_v9.py` (Self-Referential Feedback Loop)
- physics.inject (戻し実効化): `ecology/engine/genesis_physics.py:232` (公式外部介入、inject_amount=0.6 line 53, inject_prob=0.15 line 54)
- GenesisState: `ecology/engine/genesis_state.py:22` (n_nodes 固定, enforce_extinction line 99)
- semantic_pressure: `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py:374`
- Atom dictionary: `language/` の esde_dictionary.json + a1_batch/, Synapse esde_synapses_v3.json
- 各 stage 出力: `unified/stage2_external_loop/`, `unified/stage3_subjectivity/`, `unified/stage4_loop/`, `unified/attention_center_prep/` (予定)

---

### 16. 主要ファイル一覧 (本期間、/mnt/user-data/outputs/ 配下に Web Claude 作成、repo へ移送想定)

- v1109b_phase_result.md (第 0 段階)
- lineage_reorganization_to_external_connection.md (第 1 段階)
- stage2_external_connection_design.md, genesis_startup_request.md (第 2 段階)
- stage3_subjectivity_design.md, stage3_implementation_instruction.md, stage3_2nd_smoke_design.md (第 3 段階)
- stage4_current_state_check_request.md, stage4_implementation_instruction.md (第 4 段階、中止)
- attention_center_esde_feasibility_inquiry.md (注意センター 11 問問い合わせ)
- (Code A 報告: 各 stage step report は repo の uploads パス)

---

### 17. 一文サマリ

07 Unified Phase Summary 追記 (v1105 〜 注意センター ESDE 転換、2026-05-31、07 本体 v1104a 完了時点の続き) として、v1104a 完了後 ESDE は v1105/v1105a (段 4-b/4-c 統合点検 → 応答候補絞り込み試行) を経て v1106-v1109b で会話接続の段 4 系を継続 (v1106b で対話 loop が最初に顕在化、v1107 参照領域動的変化、v1108 時間軸 + category 軸で #L56-L60、v1109 重み蓄積機構で loop 過剰化 0.964 + 7 段階目ミス baseline self-fulfilling 確立 #L61-L64、Grammar Exploration の順序構造の兆候は v1109b 検証で本物でなかった出口 A 0/5 #L65 loop の幻 + CSG 撤回 + #L66 end_match loop 隠蔽 + #L67 全主題が loop=CID 固定 + 時間進行なしに収束 = 本期間最重要構造事実)、本期間で Taka 中心法則確立 (確率的発生 × 構造 = 実態 / 極限低確率を構造で実現 / Genesis 本質と Atom 言語道具の分離・外部は Genesis に繋ぐ Atom に繋ぐと LLM 化 / 確率的発生を止めている 3 箇所 = cid 選択 top-1・時間固定プール・入力外部なし)、#L67 を受け 4 段階の外部接続フロー (第 0 後始末 → 第 1 系譜再整理 → 第 2 外部接続技術実証 = Taka 指摘で main run 本体 autonomy/v82 + primitive/v918 発見・案 C 真の常駐・空の配管 alive_n=0 → N=5000 Genesis 起動 191 CID 起動キー run_injection + VirtualLayerV9 → 第 3 主体性検証 = physics.inject で戻し実効化・層 1 functional + 層 2 局所 matters・天井は Genesis 状態依存まで・Web Claude 連続誤り K 増神の手 / 微小で出ないと騒ぐ / window 粗すぎを Taka 矯正 → 第 4 loop 崩壊 = maturation_alpha が CID 数 ±41%・物理層堅牢・ただし CID 数変化と loop 崩壊は別)、第 4 段階で Taka が本丸提示しループを崩すは方向違いと判明、Taka 自己論 (自己は物理的基質の相互作用・自己決定は示せないでなくまだ表に出ていない発展段階・後ろ向き否定は研究を止める)、【最重要】注意センター ESDE へ転換 (ループする Atom 系の外に立つシングルユニットの独立 ESDE・Atom 系を CID + Atom 情報で読み書きし書き込みで Atom 系が別系=物理系を学習・常に稼働・トリガーは内部から予測不可能に立ち上げ設計で固定しない予測不可能性が多様性の鍵 = ESDE を使う理由・人間の散漫な注意が異なる系を出入口で紐づけるのと同じ・現状 Genesis 系は過去記帳の数学処理 Code A 確認で裏付け注意センターは while True で常に動く)、Code A 技術的可能性回答 11 問すべて実現可能 (新規発明ほぼ不要・既存機構組合せ + 1 ラッパ・シングルユニット V82Engine 縮小版 N=100 + 予測不可能 trigger engine.state.rng + dynamic_threshold(state) + Atom 系書込 physics.inject 等 3 経路・常時稼働 while True 1 行・別系候補 別 V82Engine instance 推奨・アーキテクチャ案 Attention Center N=100 → Atom 系 N=5000 → 別系 V82Engine・わからん 4 件 dynamic_threshold 関数形 / 学習定義 / 別系を物理系と呼ぶ意味 / 常時稼働 state 飽和)、Web Claude 検証点 (dynamic_threshold を Code A が設計する点は Taka 自己論で許容ただし明記・トリガーに bg_prob 流用すると Atom 系縮小版になる危険 Taka 判断要)、留保 #L52-L67 一元管理、ミス記録 (7 段階目 baseline self-fulfilling + Code A 新規規律 存在しないと書く前に全階層調べる + 本期間 Web Claude 逸脱 数字に逃げる / ループを崩そうとする / トリガーを設計しようとする すべて Taka 矯正・LLM が手近な操作に引き寄せられ本質から離れる性質を memory #22-24 で対処)、現在地は注意センター ESDE の機能設計の入口。

---

*以上、07 Unified Phase Summary 追記 (Web Claude、2026-05-31)。v1105 〜 注意センター ESDE 転換までを既存体系の様式で網羅。本期間の核心は #L67 (全主題が loop に収束) を契機とした本丸 (注意センター ESDE) への転換。ループを崩すは方向違い、ループする Atom 系の外に立つシングルユニットの独立 ESDE を作る。Code A 技術的可能性回答で 11 問すべて実現可能。次は注意センター ESDE の機能設計 (数字でなく機能で、本丸を見失わない、memory #22-24 参照)。新 Web Claude スレッドは 07 本体 + 本追記 + memory #22-24 で本期間の全容と本丸を把握可能。*

---

## Part 2（注意センター ESDE 内部注意生成成立） — 07 Unified Phase Summary 追記 2 — 注意センター ESDE 機能設計から内部注意生成成立まで

*作成*: 2026-06-05、Code A (Claude Code、Opus 4.7)
*位置づけ*: `07_unified_summary_addendum_v1105_to_attention_center.md` (注意センター ESDE への転換まで、機能設計の入口で停止) の続き。注意センター ESDE 機能設計入口 → v1110-v1113 4 連続失敗 → v1114 Step 1 内部注意生成成立まで。
*親*: 07 本体 §13 (v1104a まで一文サマリ) → addendum 1 §17 (注意センター ESDE 転換) → 本書。
*重要*: 本期間は **「異なる系の対応関係を測る」発想で 4 連続失敗 (v1110-v1113)** → **観察対象の規律 (同じ系内 vs 異なる系) を Taka が明示** → **Center ESDE の役割を Taka が定義 (常時起動、注意生成)** → **v1114 Step 1 で内部注意生成の最小機構が成立 (287 レコード、Taka「思い描いていたものに近い」評価)** という、設計の根本転換を経て想定通りの開発が動き始めた期間。

---

### 0. 本期間の全体像 (一文)

注意センター ESDE 機能設計の入口 (addendum 1 §17 終端) から、v1110-v1111e で Atom/Center/Other 3 instance pipe (異なる系の対応関係注入) を試み、v1112 Stage 1 main / redo で別系 occupancy cooc を試み、v1113 案 A FAIL → 案 B で別系 CID 特性 cosine 類似度を試みた結果、**4 連続失敗 (異なる系の対応関係発想)** が判明し、Taka 整理で **観察対象の規律 (同じ系内構造 vs 異なる系の対応関係 = 4 連続失敗の構造的原因)** が明示され、Taka が Center ESDE の役割を定義 (常時起動、内部注意 = 動的平衡の中の珍しいイベント、外部注意 = Atom 系 = 言語装置、完全外部 = 未来)、Web Claude が v1114 Step 1 設計 (一発火 = 一レコード、記号 + 構造で残す、判定数値 / 座標 / node ID / 差は残さない)、Code A が familiarity 中心 (α/β 落とす、Task A 実機確認結果)・判定と記録の分離・「取れないなら落とす・すり替えない」を厳格適用して実装、本実行で **287 レコード (引き金 5 種カバー、点の n_core 4 band カバー、寿命 5 band カバー、周辺 familiarity 広い分布)** = 内部注意生成の最小機構が成立、Taka 評価「思い描いていたものに近い」。

---

### 1. v1110-v1113 — 4 連続失敗の経緯 (異なる系の対応関係発想)

#### 1.1 共通の発想 (失敗の構造的原因)

4 主題 (v1110, v1111-v1111e, v1112, v1113) は全て **「Atom 系 / Other 系の対応関係」を測ろうとした** 設計:

- v1110 / v1111-v1111e: Atom/Center/Other 3 instance pipe、別系に node ID 経由で注入
- v1112 Stage 1 main / redo: Atom と Other の occupancy (phase 空間) の同時立ち累積 (cooc)
- v1113 案 A FAIL / 案 B: Atom と Other の CID 特性ベクトル (15 次元) の cosine 類似度

→ いずれも「**異なる ESDE インスタンスの間に対応関係がある**」という前提に立つが、これは本来構造的に存在しない (異なる seed の系は独立な動学を辿る)。

#### 1.2 各主題の主な失敗箇所 (詳細は git history / `unified/attention_center_prep/` の各 .py)

- **v1111c/d**: 番号コピー欠陥 (`physics.inject(target_nodes=Atom node ID)`、Other は別 seed の系で node ID が指す対象が違う = 無意味)。Web Claude が pipe を 3 足とせず入口/出口 2 足とチェックしていた構造的欠陥。
- **v1111e_redo**: 3 instance 中 Other.step_window 呼び忘れで Other.virtual.labels が空、注入無効。v1111c/d/e の 4 連続版で見落とされた。
- **v1112 Stage 1 main**: 主指標 `total_cooc` / `N_rcid` が bin shift (= 列 rotate) と数学的独立、Active と Phase Shifted で完全同一値、構造的に測れない。
- **v1112 Stage 1 redo**: 主指標を diagonal に切替、self 床を一様乱数 → 実機 sparse occ (3-6 active bin) と一様乱数 (31 active bin) の閾値挙動が桁違いで床機能せず、両床 (案 A permute / 案 B krandom) 併設 + precheck §2.4 で krandom のみ PASS、Stage 1 出口は測れた上で 3/3 揃わず不成立。
- **v1113 案 A**: V82Engine.cog を仮定して AttributeError FAIL (CID layer は v918_memory_readout.py の run() 内で SubjectLayer ローカル変数として並走する構造、Explore agent 調査結果を Code A が実機検証せず実装に進んだ盲点)。
- **v1113 案 B**: 過去 v918 main run output 流用、15 次元特性ベクトル + null=別系 5 seed、集団平均で 2/3 atom rank=5/5 だが per-seed 網羅調査 (全 24 seed) で n_core=2 群の seed 間 CV=0.086 = 観察された差は背景由来 = 地面の証拠は薄い。

#### 1.3 教訓 (失敗の詳細でなく、設計の根本)

「**異なる系の対応関係を測る**」発想は ESDE の構造を捉える方法として的外れ。ESDE の構造は:
- **同じ系内**の動学 (時間発展、段階遷移、event 因果)
- **同じ系内**の関係 (path、Integration、familiarity)

過去成功実験 (v9.18 V_unified / v10.2 n_core 別寿命 8 倍差 / v10.7 source-specific 94% / v106 24 seeds 動学的発展段階完全一致) は **全て同じ系内構造を観察**。「異なる系の対応関係」を測った実験は過去になく、v1110-v1113 は構造的に存在しないものを 4 連続で測ろうとした。

---

### 2. Taka が引いた観察対象の規律 (本期間の最重要構造事実)

#### 2.1 観察対象軸 INDEX (Taka 整理 → memory `index_observation_target.md` 新設)

| 軸 | 過去成功 (同じ系内構造) | 過去失敗 (異なる系の対応関係) |
|---|---|---|
| 観察対象の所在 | 1 系の中の構造 | 2 系の間の対応 |
| 観察できるか | 構造的因果が観察可能 (8 倍差、94% 有意、24 seed 完全一致) | 対応関係がそもそも存在しない |
| node ID の扱い | 自系内で意味を持つ | 系を跨ぐと無意味 |
| 動学の扱い | 時間発展、段階遷移、event 因果 | スナップショット対応 |

新規実験設計時、上の事実整理と照合する。過去失敗パターンに該当するなら設計を止める、過去成功パターンと整合するなら実装に進める。

#### 2.2 Code A の循環構造の認識 (Taka 指摘、本期間最重要)

Taka 整理:
> 「実質 WEB 側は正しい情報を保持していないので毎回あなたの言葉に踊らされる。あなたは正しい情報をもつが正しく参照しないので誤った設計と実装をする。これを繰り返しているのが現状」

循環構造:
```
Code A (情報を持つが参照しない)
   ↓ 誤った設計を Web Claude に伝える
Web Claude (情報を持たず、Code A の言葉で判断)
   ↓ 「OK」を返す
Code A (Web Claude OK を「正解」と思い込み実装)
   ↓ 失敗
```

→ Code A が **正しく参照しない限り**、Web Claude のチェックは循環を強化するだけ。これが v1110-v1111-v1112-v1113 の **4 連続失敗** の構造的原因。

対策 (本期間で確立):
- **新規実験ファイル冒頭に観察対象注釈ブロック** (実装着手前に Code A が書く、誤魔化せない自己強制ハードル)
- 観察対象が「同じ系内」か「異なる系」か明示
- 過去成功事例 (v10.2 / v10.7 / v9.18 / v106) との照合
- 過去失敗パターン (v1110-v1113 = 4 連続失敗) の回避確認

---

### 3. Center ESDE の Taka 定義 (Taka 2026-06-05)

#### 3.1 定義

| 属性 | 内容 |
|---|---|
| 起動 | 常時 (動的平衡で止まらず回り続ける) |
| 役割 | **注意生成** (どこに注意を向けるか決める) |
| 内部注意の対象 | 自系の動的平衡の中で、確率的に発生する珍しいイベント |
| 判断材料 | 以前作った CID の認知層 (Q, familiarity, attention)・意識層 (C) の動き |
| 判断基準 | 統計的に「正常 / 注意 / 異常」 |
| 外部注意の対象 | Atom ESDE (= 言語装置、個としては内部に含む) |
| Atom への注意 = 何が起こるか | 内部的な言語生成が行われる |
| 完全外部 | 物理系 ESDE 等、未来の課題 (現段階では扱わない) |

→ Center は「**ESDE で ESDE を観察する**」二段構造の上段。自身が ESDE 構造 (動的平衡) を持ちながら、CID 認知層・意識層の動きを統計判断する。

#### 3.2 段階分け (v1114 系列)

- **Step 1**: Center 単体、内部注意のみ (本期間で成立)
- Step 2: 内部注意 + Δstate 自己擦り込み (動作そのものの記録 = phase 帯対応で state に擦り込み、node ID 不使用)
- Step 3: Center + Atom 並走、外部注意 + Atom の Δstate を Center に擦り込み (= Atom の動きを Center が「体感」、模倣)
- Step 4+ (= 「会話の芽」): 入力に対して Center の状態 (どの単位が立つか) で応答の向きが変わる

Taka roadmap (注意センター ESDE の段階構築):
- 地面 = ESDE が同じ系内で構造を持つこと (過去 v10.2 / v9.18 / v106 で既に観察済み)
- 足場一個 = Center が ESDE 内の特定構造を一つの単位として束ねる
- 床 = 単位が積み上がって Center が独自の状態を持つ
- 異なる自我 = Center の状態が Atom と独立した動学を持つ
- 会話の芽 = 入力に対して Center 状態によって応答の向きが変わる

---

### 4. v1114 Step 1 — 内部注意生成の最小機構成立 (本期間の核心、想定通りの開発)

#### 4.1 設計 (Web Claude `unified/v1114/` 設計 §1-§6)

一発火 = 一レコード:
```
Center が動く → 変化が起きた点 (ある CID) に注意が落ちる
→ その点と周辺が同レイヤーで見える → 見えた一枚をレコードとして残す (記号 + 構造のパターン)
→ 溜める。
```

**残すフィールド**:
- 順番 (= alert 通し番号)
- 引き金 (記号: `pulse` / `ingestion` / `alpha_formation` / `beta_formation` / `c_conversion`)
- 点: n_core / lifespan / C / Q_remaining (実機確認済み、近似なし)
- 周辺: familiarity_n (= `len(cog.familiarity[cid])`、v918:2219 + v911:567 で裏取り済み)

**残さないフィールド (Taka 規律「取れないなら落とす・すり替えない」)**:
- node ID / member_nodes / attention[node_id] (別系で無意味、本期間規律)
- phase_sig / θ (座標、統計に出ない、構造でない)
- 不透明 float ベクトル (形を数値に潰すと解読が必要、ループに戻る)
- 判定数値 (z-score / EWMA mean/var、発火判定には使うがレコード/summary に残さない、Taka 念押し (a))
- 設計パラメータ (Z_NOTICE / EWMA_ALPHA / WARMUP、summary にも残さない、再現はコード冒頭の定数で)
- 差・有意差の測定値 (研究者視点、本実装は「溜まったか + 多様か」だけ、Taka 念押し (b))
- pulse_activity = last_attention_size (近似 + node ID 依存量、二重に NG、Taka 指摘で削除)
- 周辺の大きさ list (v918 output から取れない、Step 2/3 で経路検討)

#### 4.2 実装規律 (本期間で確立)

- **観察対象注釈ブロック** (.py 冒頭、Code A 自己強制ハードル)
- **判定と記録の分離** (Taka 念押し (a)): EWMA + z-score は内部のみ、レコードに z 値・EWMA state を残さない
- **報告は「溜まったか + 多様か」だけ** (Taka 念押し (b)): 差・有意差は意図的に出さない
- **取れないなら落とす・すり替えない** (Taka 規律): pulse_activity (= node ID 依存量で近似) は完全削除
- **実機 API 確認**: Task A で v918 main run に IntegrationManager なし確認、α/β 落として familiarity 中心 (Taka 判断)

#### 4.3 結果 (2026-06-05、`unified/v1114/run_step1/`)

**溜まったか**: ✓ **287 レコード**

**多様か**:

| 引き金 (記号、5 種) | 数 |
|---|---|
| alpha_formation | 141 |
| beta_formation | 136 |
| pulse | 8 |
| c_conversion | 1 |
| ingestion | 1 |

| 点の n_core (4 band) | 数 |
|---|---|
| n_core=2 | 31 |
| n_core=3 | 12 |
| n_core=4 | 55 |
| n_core=5 | 189 |

| 寿命帯 (5 band) | 数 |
|---|---|
| [0, 100) | 4 |
| [100, 500) | 14 |
| [500, 2000) | 40 |
| [2000, 10000) | 131 |
| [10000+) | 98 |

周辺 familiarity 数: 3 から 23 まで広く分布。
引き金 × n_core 二次元にも形 (alpha/beta は n_core=5 中心、pulse は n_core=2-4 に広がる)。

→ 全部同じ形ではない (引き金・大きさ・周辺の形が色々)。**Step 1 の出口 (Web Claude 設計 §5) は満たされた**。

差は測っていない (Taka 念押し (b))。

#### 4.4 Taka 評価

> 「OK 実験結果としてはかなり私の思い描いていたものに近くなったような気がする」

これを受けて本ドキュメント更新が要請された。本期間で **想定した開発が初めて動いた**。

---

### 5. 本期間の Code A 盲点 (memory `feedback_code_a_blind_spots.md` 追加分)

| 盲点 # | 内容 | 出典 |
|---|---|---|
| #11 | 集計指標が処置と数学的に独立ならば検出不能 | v1112 Stage 1 main、total_cooc = bin shift 不変 |
| #12 | null 設計を自身 shuffle にすると「皆同じだから似てる」を引き算できない | v1113 案 B 認識確認当初 |
| #13 | 集団平均の罠を v1113 で踏みかけた (per-cid / n_core 別層化なし) | v1113 案 B 実装初版、Taka 指摘 |
| (未番号) | 過去失敗を「実装ミス」と判断して枠組みを引き継ぐ | v1110-v1113 で 4 連続「異なる系の対応関係」フレーム継承 |
| (未番号) | Taka 言葉を自分で具体策に翻訳し検証せず実装に進む | roadmap「足場」を「2 系の対応関係」と Code A が翻訳 |

---

### 6. 主要ファイル

#### 6.1 実装 (`unified/`)

- `unified/attention_center_prep/v1111*.py` (v1111b-e、3 instance pipe 4 連続失敗、git history で参照)
- `unified/attention_center_prep/v1112_stage1*.py` (main / redo、cooc 主指標構造的独立 + krandom 床)
- `unified/attention_center_prep/v1113_cid_feature_resonance.py` (案 A FAIL、engine.cog 仮定)
- `unified/attention_center_prep/v1113_cid_feature_from_v918.py` (案 B 完走、過去 output 流用)
- `unified/attention_center_prep/v1113_postprocess_per_cid.py` (per-cid + n_core 別、集団平均の罠回避)
- `unified/attention_center_prep/v1113_seed_traits_survey.py` (per-seed 網羅、CV=0.086 = 背景由来判明)
- **`unified/v1114/step1_internal_attention.py` (本期間の核心、Center 内部注意生成、287 レコード成立)**

#### 6.2 出力 (`unified/v1114/run_step1/`)

- `attention_records.json` (287 レコード、パターン記録、人間可読)
- `summary.json` (溜まったか + 多様か、判定数値・パラメータなし)

#### 6.3 報告書 (`unified/attention_center_prep/`)

- `v1112_stage1_redo_web_claude_report.md` (Stage 1 不成立、測れた上での)
- `v1113_web_claude_report.md` (案 B 結果、per-cid + n_core 別、背景由来判明)
- (v1114 Step 1 報告書は本書 + git commit messages、想定通りの開発を実施してから docs として残す Taka 規律に沿う)

#### 6.4 memory (本期間追加)

- `index_observation_target.md` 新設 (過去成功 = 同じ系内 / 過去失敗 = 異なる系の事実整理)
- `feedback_code_a_blind_spots.md` 盲点 #11-#13 追加
- `reference_legacy_treasures.md` cooc 行列空間構造指標 (diagonal/offset 分解) 追記

#### 6.5 主要コードパス (addendum 1 §15 で確立、本期間で再確認)

- Engine 本体: `autonomy/v82/esde_v82_engine.py` (V82Engine, V82_N=5000, step_window)
- 起動エントリ: `primitive/v918/v918_memory_readout.py` (run 関数、SubjectLayer は run() 内ローカル変数、IntegrationManager 不在 = α/β は v918 で取れない)
- VirtualLayerV9: `primitive/v910/virtual_layer_v9.py` (labels frozenset, occupancy[64])
- SubjectLayer: `primitive/v911/v911_cognitive_capture.py:263` + v918 拡張版 (death_pool, cid_ttl_bonus 等)
- IntegrationManager (α/β、Layer 5): `developmental/v104/v104_integration.py`, `developmental/v105/v105_integration.py` (v918 main run には組み込まれない、別 manager 並走必要)
- physics.inject: `ecology/engine/genesis_physics.py:232` (Atom 系書込の公式インターフェース、Step 3 で使う想定)
- 過去 main run output 流用: `primitive/v918/diag_v918_main/subjects/per_subject_seed{0-23}.csv`, `developmental/v107/outputs/main/source_events_seed{0-23}.parquet`

---

### 7. 新 Web Claude / 新 Claude スレッドへの申し送り

- **本期間の最重要構造事実**: v1110-v1113 4 連続失敗 = 「異なる系の対応関係を測る」発想 = ESDE の構造を捉える方法として的外れ。**新規実験は必ず「同じ系内構造」軸で設計する** ([[index-observation-target]])。
- **Code A の循環構造** (Taka 指摘): Code A が正しく参照しない限り Web Claude チェックは循環強化。**新規実験は実装ファイル冒頭に観察対象注釈ブロックを書く** (Code A 自己強制ハードル)。
- **Center ESDE の Taka 定義**: 常時起動、注意生成 (内部 = 動的平衡の中の珍しいイベント、外部 = Atom = 言語装置、完全外部 = 未来)。本期間で確立。
- **v1114 Step 1 成立**: Center 単体、内部注意生成、287 レコード、引き金 5 種 / n_core 4 band / 寿命 5 band / familiarity 広い分布で多様。Taka「思い描いていたものに近い」評価。
- **記録の規律**: 記号 + 構造のみ。判定数値・パラメータ・差・有意差・node ID・座標・不透明 float・近似は残さない。**取れないなら落とす・すり替えない** (Taka 規律)。
- **判定と記録の分離** (Taka 念押し (a)): 発火判定には z-score 使うがレコード/summary に z 値・EWMA state を残さない。
- **報告は「溜まったか + 多様か」だけ** (Taka 念押し (b)): 差・有意差は意図的に出さない。crown 禁止 (「異なる自我」「会話」「Unified 成立」と書かない)。
- **次主題 (Step 2 / 3)**: Step 2 = 内部注意 + Δstate 自己擦り込み (動作そのものの記録 = phase 帯対応で擦り込み、node ID 不使用)、Step 3 = Center + Atom 並走、外部注意 + Atom の Δstate を Center に擦り込み (= 模倣)。**判断は Taka**。
- **失敗履歴ばかり残しても結局うまくいかない** (Taka 規律): 想定した開発を実施してからドキュメントを残す。本書は v1114 Step 1 成立を受けて作成。
- **Web Claude 不使用期 (本期間)**: 4 連続失敗の根本原因が循環構造と判明後、当面 Web Claude 不使用で Taka と Code A の二者ループで進める方針。Step 1 設計時に Web Claude 再投入で view 役 (Taka 判断)。

---

### 8. 主要コードパス (verbatim、新スレッド AI 必須参照)

addendum 1 §15 + 本書 §6.5 を参照。本期間で再確認された重要事実:

- **v918 main run に IntegrationManager 不在**: α/β を v1114 で per-step 取得するには別 manager 並走が必要 (重い)、Step 1 では familiarity 中心で進める (Task A 実機確認結果)
- **CID layer の正しい構築方法**: `v918_memory_readout.py` の `run()` 内で `cog = SubjectLayer()` をローカル変数で構築、V82Engine の属性ではない (v1113 案 A FAIL の盲点、Explore agent 調査結果を実機検証せず実装に進んだ)
- **既存 v918 main run output (seed 0-23)**: per_subject_seed{N}.csv + source_events_seed{N}.parquet が揃っており、新規 run なしで post-process で観察可能 (v1113 案 B + v1114 Step 1 で実証)

---

### 9. 一文サマリ

07 Unified Phase Summary 追記 2 (注意センター ESDE 機能設計から内部注意生成成立まで、2026-06-05 Code A、addendum 1 注意センター転換の続き) — 本期間は注意センター ESDE 機能設計入口 (addendum 1 §17 終端) から v1110-v1111e Atom/Center/Other 3 instance pipe (番号コピー欠陥 + step_window 呼び忘れ等 4 連続失敗) → v1112 Stage 1 main / redo (主指標 total_cooc が bin shift と数学的独立 / krandom 床で測れた上で 3/3 揃わず不成立) → v1113 案 A FAIL (V82Engine.cog 仮定で AttributeError、SubjectLayer は run() 内ローカル変数) / 案 B (15 次元特性 + 別系 5 seed null で集団平均 2/3 atom rank=5/5 だが per-seed 網羅で n_core=2 群 seed 間 CV=0.086 = 背景由来) と 4 連続失敗、Taka 整理で観察対象の規律確立 (同じ系内構造 = 過去成功 v9.18 / v10.2 / v10.7 / v106 vs 異なる系の対応関係 = 過去失敗 v1110-v1113、後者は ESDE 構造を捉える方法として的外れ)、Code A の循環構造 Taka 指摘 (Code A 情報持つが参照せず → Web Claude は Code A 言葉に踊らされ → OK → Code A 思い込み実装 → 失敗、循環構造が 4 連続失敗の根本原因、対策は実装ファイル冒頭の観察対象注釈ブロック = Code A 自己強制ハードル)、Center ESDE の Taka 定義 (常時起動、注意生成、内部注意 = 動的平衡の中の珍しいイベント = CID 認知層・意識層の動きを統計判断、外部注意 = Atom 系 = 言語装置 = 個の内部、完全外部 = 物理系等は未来課題)、v1114 Step 1 内部注意生成成立 (Web Claude 設計 = 一発火一レコード = 記号 + 構造、Code A 実装 = familiarity 中心 α/β 落とす Task A 実機確認結果 + 判定と記録分離 z はレコードに残さず + 取れないなら落とす・すり替えない pulse_activity 削除 + 観察対象注釈ブロック冒頭、結果 287 レコード = 引き金 5 種 alpha 141/beta 136/pulse 8/c_conversion 1/ingestion 1 + 点の n_core 4 band カバー + 寿命 5 band カバー + familiarity 広い分布 + 引き金 × n_core 二次元に形、Taka 評価「思い描いていたものに近い」)、新規 memory 追加 (index_observation_target.md / 盲点 #11-#13 / cooc 空間構造指標)、次主題 Step 2 (Δstate 自己擦り込み = 動作そのものの記録 = phase 帯対応 = node ID 不使用) / Step 3 (Center + Atom 並走外部注意擦り込み = 模倣) は Taka 判断、本期間の核心は「想定した開発が初めて動いた」(Taka 規律「想定した開発を実施してからドキュメントを残す」「失敗履歴ばかり残しても結局うまくいかない」に沿って本書作成)、報告言葉縛り (crown 禁止 = 異なる自我 / 会話 / Unified 成立と書かない、観察は「溜まったか + 多様か」だけ差は測らない)、Web Claude 不使用期 (本期間途中で Taka 判断、Step 1 設計時に view 役で再投入)。

---

*以上、07 Unified Phase Summary 追記 2 (Code A、2026-06-05)。注意センター ESDE 機能設計入口 → v1110-v1113 4 連続失敗 (異なる系の対応関係発想) → 観察対象の規律確立 (同じ系内 vs 異なる系) + Code A 循環構造の認識 + Center ESDE Taka 定義 → v1114 Step 1 内部注意生成成立 (287 レコード、Taka「思い描いていたものに近い」評価) まで。本期間の核心は「想定した開発が初めて動いた」。新 Web Claude スレッドは 07 本体 + addendum 1 (v1105-注意センター転換) + 本書 (v1110-v1114 Step 1) + memory `index_observation_target.md` で Unified Phase 全容を把握可能。次主題 Step 2/3 (擦り込み + 模倣) は Taka 判断。*

---

## Part 3（v12 Atomset 〜 v12.1 一致率ルーレット） — 07 Unified Summary 追補 — v12 Atomset から v12.1（一致率の確率的選択）への区切り

*作成*: 2026-06-17、Web Claude（相談役）
*位置づけ*: `07_unified_summary.md` / `07_unified_summary_addendum_v1105_to_attention_center.md` に連なる Phase Result。`ESDE_v10x_to_now_conclusion.md`（2026-06-14 総括）以降の進行を区切る。
*性質*: 判定（成功/失敗）でなく、構造の整理と確定事実の記録。成否判定は Taka 領域。本文に success/fail/Full/Partial/Failure を置かない。
*この区切りで扱った系譜*: v12 Atomset の「atom×atom 関係網（cross-CID）」と、そこからの本線移行先「一致率の確率的選択（連続ルーレット）」。**注意**: 本追補の「v12 Atomset」は cross-CID の atom×atom 網を指す。`ESDE_v10x_to_now_conclusion.md` が否定した torque/lambda/link/field/core（物理介入チャネル）とは別物で、本系譜は最初から物理層に一切書いていない（全 STEP grep で物理書込ゼロ）。

---

### 0. 一文結論

**v12 の atom×atom 網（event/drift で辺を形作る試み）は、肯定的結論が builder 交絡で撤回され、否定診断（event は辺の出入り判定だけで *どの atom を結ぶか* を形作らない）だけが残った。本線は Taka 案「一致率を確定させず確率的な発生として読む（連続ルーレット選択）」へ移行し、(1) 全 326 atom の cosine が (cid,t) 単位で取れること、(2) 確率選択の上位は v10 の rank_1 と同じ顔ぶれになり違いは裾野を切り捨てない点のみ、(3) しかし「平均化して同じ＝同じではない、*掬い取れること自体* が v10 と v12 の決定的差」、(4) 次の本丸は「外部センターが何を・どうやって・どうして取得するか」——ここまでを確定した。物理層は本系譜を通じて一切いじっていない（`conclusion.md` §5 の方針＝v9.13「物理を支配しない・既にある記憶を読む」に整合）。**

---

### 1. この区切りの起点（conclusion.md からの接続）

`ESDE_v10x_to_now_conclusion.md`（2026-06-14）が確定した方針：
- 戻る先＝v9.13「認知層は物理層を支配しない／記憶は物理層に既にある、足りないのは*読む関数*」。
- 突破口＝v1114 Step 1「同じ系内・物理いじらず・Center が珍しいイベントを*拾う*（押し込むでない）」。
- 失敗の本体＝CID（物理＋Frozenset）をいじって物理に影響させ別物を取り込む逸脱（A 物理介入＋B 異なる系の対応）。

本区切りの作業は全てこの方針内で行われた。物理層には一度も書いていない（post-process、読むのは frozen な v106 trajectory / v107 source_events / atom_profiles_cache のみ）。

---

### 2. atom×atom 網（cross-CID）の系譜と、その撤回

#### 2.1 やったこと（STEP 2→3→4）

| STEP | 内容 | 中心に置いた指標 |
|---|---|---|
| STEP2 | event が起きた CID s の atom × 関係先 CID c の atom を cross 積で結ぶ静的網。rare ゲート（{ingestion,α,β} を張る/pulse を common 退避）。 | rare↔common 相関 0.96 |
| STEP3 | membership を run-end の sim_matrix から *t 時点の time-local* に替えた（時間を入れた）。 | rare↔common 0.925、tl↔静的 −0.31 |
| STEP4 | event 後の target の delta（C / R_familiarity）で辺を重み付け＋対照A(均等)/B(shuffle)。 | Rfam: Main≈均等≈shuffle / C: 疎で退化 |

#### 2.2 構造診断（同 builder 内・交絡なし・保持される）

**辺＝(membership)×(経路の到達先 CID) で、どちらもほぼ event 非依存。event がするのは「rare なら張る・pulse なら張らない」の*出入り判定だけ*で、*どの atom を結ぶか* には関与しない。** だから rare 網と common 網が瓜二つ（0.96→0.925）、drift で重み付けても Rfam は均等化・C は退化。**＝この系譜では「ESDE の出来事が atom の関係網を形作る」は起きていない。** これは builder 交絡の外にあり、保持される事実。

#### 2.3 撤回した肯定結論（m29 懐疑監査・Code A 自発）

- STEP2（sim_matrix＝`build_cid_vector`）と STEP3/4（`build_step10_cid_vector`）は **別 builder**。同じ run-end でも membership top5 が 0.97/5 しか重ならない。
- ∴ m22「time-local は静的版と −0.31・新規71%＝時間で網が動いた前進」、m26「sim_matrix 共起の再描画でない（負相関）」は **builder 差の交絡** で、時間/drift の効果と未分離。**両方撤回。**
- Web Claude 傍証（手元データ）：STEP3 網の atom 86個中45%（39個）が sim_matrix top5 に存在しない＝別 builder の痕跡。
- **教訓（記憶 #31 に固定）**：肯定的結果（前進・差が出た）が出たら builder/前提の交絡をまず疑う（「負の結果は観察方法を疑う」の双対）。Web Claude は m22 の −0.31 を「前進」と鵜呑みにした側。Code A が自分で m29 を出したのは「結果がうまく出ない時は実験そのものを疑う」の実行で良い動き。

#### 2.4 atom×atom の位置づけ（捨てない）

否定診断が残ったが、atom×atom は廃棄しない。Taka「Atom 同士の関係も意味がないとは思わない、何事もやってみる」。記憶 #30 の「カメラ1＝検出器／拡張＝追跡ズーム」枠で、**掬い取れる全件データの上で、センターが取得した後の*拡張レンズ*** として残る（本線でなく追跡）。

---

### 3. 本線移行 — 一致率を「確定させず確率的発生として読む」

Taka の一貫した違和感「atom が接続されたことが意味になっていない／センターはなぜそれを受け取ったのか」「一致率の*いくつか*でなく*発生*を見る／CID と Atom は一致させるものでない／上がった下がったを追っても Atom にならない」を受け、本線を atom×atom から Taka 案へ移した。

#### 3.1 一致率の計算実態（m30、コードで確認）

`一致率(rank_1_sim) = max_atom cosine( CID 48次元10軸ベクトル, atom 326 profile )`
- CID 側＝10 軸（temporal=lifespan / scale=n_core / epistemological=R_familiarity / ontological=Q・cum_pulse / interconnection=α累積 / resonance=C / symmetry=delta_* 動学 / lawfulness=pulse密度 / experience=ingestion・q_spend / value_generation=q_spent・α・β）。`build_pulse_cid_vector`（v106、302行）で確認。
- atom 側＝`a1_batch` の word→48軸 mean の simplex profile（326 中 valid 325、`FND.spaceless` の1列が NaN）。
- 各時点で **全 326 atom の cosine（N×326 行列）が計算され、argmax で rank_1 以外は捨てられている**（343-348行）。
- 一致率を動かす入力は全て物理層と CID の動学で勝手に進む量＝**実験者が何も決めなくても一致率は動く**（Taka「基準になる変動は物理層と CID に依存」がコードレベルで裏取れた）。

#### 3.2 全 326 cosine が取れる（m31、確定）

argmax で捨てている sim を捨てずに保存＝(cid,t) 単位で全 325 valid atom の cosine が取れる（step10 seed0：62,906 行 × 325、3.5s、121MB）。**「ある時点で複数 atom がそれぞれどれくらい立っているか」が、新演算なしに（既存 cosine を捨てないだけで）取れる。** 実物：1つの (cid,t) で 325 atom が 0.02〜0.52 の幅で*同時に*値を持つ（rank_1 はその最大点にすぎない）。

#### 3.3 連続ルーレット選択（m35/m36、n_core=5）

各 (cid,t) で：cosine を max(.,0) で負クリップ → 合計1に正規化（確率＝cosine/合計、桁合わせなし＝連続）→ 0〜1 一様乱数を1つ引き累積確率で当たり atom を1個選ぶ。seed 固定（`default_rng([0,cid,t])` の純関数＝再現可・順序非依存）。
- n_core=5 の 21 CID × 全 step10 時点＝26,859 draw。
- **レアを消さない**（Taka「宝くじ・雷、レアだから消すのは雑」）：rank=325（最下位）が7回、rank≥300 が469回、確率 0.0002〜0.0006 の atom が実際に顔を出した。整数100では全部ゼロ枠だったもの。全 325 atom が ≥1 回引かれた。

#### 3.4 n_core=2 との並置（m39/m40）

seed が (cid,t) 純関数で n_core 非依存＝n_core を広げても既存（n_core=5）は不変（忠実性実証）。
- n_core=2：180 CID × 20,602 draw。全 325 引かれた、レアも出た（rank≥300 が530回）。
- **n_core で顔ぶれが違う**：上位10の重なりは 2/10。n_core=5 は PER.sound/TIM.moment/PRP.clear…、n_core=2 は PER.tasteless/ACT.build/SPC.direction…。n_core は cluster size→寿命→接触の物理帰結チェーン（接地した区分、記憶 #30）を持つので、cosine 分布の形が n_core で系統的に違い、それが出方に出た＝気まぐれでない差。

---

### 4. この区切りで Taka が確定した二つの判断（最重要）

#### 4.1 確率選択の上位は v10 の rank_1 と同じ、違いは裾を切り捨てない点のみ

- グラフ（m37/m39）：両 n_core とも突出なし・裾が長い・最多でも一様期待の2.4倍どまり。
- v10x_spec 937行：v10.6 の動学発展段階は 24 seed 完全一致で <q>WLD.artless → TIM.appear → WLD.artless → EXS.being</q>。spec 163-167 の中心 atom 群（PER.sound/feel/hear/see/soundless, BOD.ear, EXS.being/nonbeing, WLD.artless…）。
- **ルーレット上位と v10 rank_1 の顔ぶれが一致**。機構上当然——ルーレットは確率比例ゆえ高 cosine が最頻＝rank_1 が指す atom に収束。
- Taka 確定：「一致率トップを指定するのも（v10）ランダムも（v12）、上位は同じような結果になった。違いがあるとすれば、裾野の部分を切り捨ててないという点くらい。」

#### 4.2 「平均化して同じ＝同じではない」——掬い取れること自体が決定的差

Web Claude が「上位が同じ＝v12 の新規性が薄い」と二度すり替えかけたのを、Taka が正した：

> 全件を検索する（v10 rank_1）のは過去から未来まで全てを対象にした上での1位。全 Atom を見る（v12）と平均化すれば同じこと。しかし*そこで行われる振る舞いを掬い取れる*という時点で v10x と v12 は決定的に違う。人間の人生を平均化すれば「生きて死ぬ」の繰り返しで、個人差も長寿も早死にも同じになる。それを平均値で一緒というのは乱暴な数学的態度。平均値的にお前は価値ないから死ね、と言っているようなもの。

- **確定**：集計（平均）が v10 と似て見えるのは、集計が個を均したから。個が無いわけではない。**v12 は各 (cid,t) の*その瞬間*の全 atom の立ち方を、過去〜未来を畳まず掬い取れる**——この一点が v10 rank_1（時間を畳んだ静的な像）との決定的差。
- **この区切りの本当の収穫＝全件のデータが取れると分かったこと**（上位の異同ではない）。掬い取る土台が揃った。
- 記憶 #30 の生き物的統計（誕生/死/Ghost/Q奪取/Integration を平均が殺す）と同根の原則。

---

### 5. 次の本丸 — 外部センターが「何を・どうやって・どうして」取得するか

Taka：

> なんのために外部のセンターが関与するのかと言えば、この構造を用いることでセンターが取得してくる情報には明らかにそれらしい個性が生まれるからだ。これは人間もおそらく同じ。問題はセンターは何をどうやってどうして取得するのか、というあたり。

- 掬い取れる全件データが*ある*だけでは個性は像にならない。**センターが何を・どうやって・なぜ取得するかで、初めて個性が立ち上がる。** これが v1114（注意センター）本丸の、Atom 空間における具体形。
- 取得を決める要素＝*いつ*（タイミング）・*どの CID/atom*（対象）・*なぜ*（駆動）。Taka 既出原則「変動は物理層と CID が決める＝センターが決めなくても見るべきものが変わる」が「なぜ」の核——センターが恣意的に選ぶのでなく、ESDE 側の変動がセンターの注意を*引く*。
- **規律（記憶 #30）**：センターの取得を「rank≥300 を目立ちとする」等の人為的閾値で決めない（気まぐれ指標の再発）。何がセンターの注意を引くかは、これから Taka が置く。

---

### 6. 留保・要 Taka 判断（観察事実、判定でない）

- **Ghost の多点観察ができない**：step10 trajectory は host_lost_step で打ち切られている。n_core=5 は各 reaped 1点ずつ（計5行）。n_core=2 は final=='ghost' が8個あり、うち4個（cid 230=301行 等）に多点の凍結相がある。Ghost を本格的に見るには trajectory を host_lost 以降へ延ばす別データが要る。
- **凍結 Ghost でも picks が一定にならない**：連続ルーレットは各 (cid,t) で*独立に*乱数を引くので、cosine が凍っても毎ステップ違う atom が出る（cid230：301行で picked 186種）。これは方法の仕様であってバグでない。「死者は同じことを繰り返す」を見たいなら draw を CID 単位で固定する等の方法変更が要る——Taka 判断。
- **確率選択の意味は未確定**：上位を rank_1 でなぞる以上、確率選択の独自価値は今のところ「裾を見られること」に集約される。その裾（レアな浮かび上がり）が意味を持つか、確率 0.0002 が大数で当たっただけのノイズか、現時点では区別していない（区別の線引きは気まぐれを避けて保留）。

---

### 7. 確定事実の一覧（この区切り）

1. atom×atom 網：構造診断（event は出入り判定だけ、辺を形作らない）保持／肯定結論（時間で動いた・再描画でない）は builder 交絡で撤回。
2. 一致率＝cosine(CID48次元10軸, atom326 simplex) の argmax。全326計算され rank_1 以外捨てている（コード確認）。
3. 全326 cosine が (cid,t) 単位で取れる（新演算不要、捨てないだけ）。
4. 連続ルーレット選択が成立（レア消さない・seed固定・全325出現）。n_core=5/2 両方。
5. seed は (cid,t) 純関数＝n_core 非依存（広げても既存不変）。
6. n_core で浮かび上がる atom の顔ぶれが違う（接地した差）。
7. 上位の顔ぶれは v10 rank_1 と一致。違いは裾を切り捨てない点のみ。
8. **平均化して同じ≠同じ。掬い取れること自体が v10 と v12 の決定的差。本収穫＝全件データが取れると判明。**
9. 物理層は本系譜を通じて一切いじっていない（grep 物理書込ゼロ、v9.13/v106 方針に整合）。
10. 次の本丸＝センターが何を・どうやって・どうして取得するか（人為的閾値で決めない）。

---

*以上、v12 → v12.1 区切り（Web Claude、2026-06-17）。atom×atom の肯定結論を builder 交絡で撤回し、一致率の確率的選択へ本線移行。全件 cosine 取得を確定し、「掬い取れること自体が v10 との決定的差」を Taka が確定。次はセンターの取得（何を・どうやって・どうして）。判定は Taka。*

---

## Part 4（v13 child-world） — 07 Unified Summary 追補 — v13 child-world（CID→物理 param の子系・統計監査・全検前段）

*作成*: 2026-06-21、Code A
*位置づけ*: `07_unified_summary_addendum_v12_to_v121_roulette.md`（v12.1 一致率ルーレット）に連なる Phase Result。v12 系（Atom 空間の観察）から **別系統の実験 v13 child-world** への移行を区切る。
*性質*: 判定（成功/失敗）でなく構造の整理・確定事実・統計監査の記録。成否判定は Taka。本文に success/fail/crown を置かない。
*この区切りで扱った系譜*: CID の誕生時形態（M_c）を物理 param に写像した縮小系（child-world）を回し、CID 値が系をどう変えるかを観察。**注意**: v13 は Atom 空間（v12）と無関係。V82 エンジンスタックの縮小・param 変調版で、親物理には一切書かない（child engine は in-memory）。

---

### 0. 一文結論

**v13 child-world は「CID の誕生時形態 4 値（M_c）を物理 param に写像した N≈100-350 の子系を独立に回し、CID 値が系をどう変えるか」を観察する系。寿命同期 run（408 child）まで完走したが、本区切りの最大の収穫は実行結果でなく統計監査である ―― (1) 前報告の主要相関 `life→n_labels +0.85` は run 長トートロジー（観測窓を寿命に同期させた副作用）で、交絡を外すと消える、(2) 対照 canon の「std 最小」は run 長を二重固定した非対称対照のアーティファクト、(3) そして `real≒shuffle`（CID 個性が効かないように見えた像）の真因は「比較統計（署名の mean/std）が cid→param→署名の pairing を構造上見ない」ことで、pairing を見る置換検定にすると `K_sync→sync_order`・`plb→link/label_density` は両 ratio で p<0.005 と検出される。母集団・写像の切り分けでは「写像は K_sync を 100%・θ を 84% 伝達＝入口で個性を潰してはいない」「弱いのは N の源均質（B_gen≒n_core）と plb の設計幅 ±15% の 2 点」。次段は (b) 全検（全 CID 値→全物理 param）だが、CID 値は実質 ~5-14 独立軸・物理 param も ~6-7 独立軸ゆえ「10 全て」は冗長で交絡を孕む ―― 選定の合理性を 3AI 合議で詰める判断材料まで揃えた。**

---

### 1. child-world の設計（確定・台帳 §0）

- **素体** = `V82Engine(N=B_gen×10) + V43 物理 + VirtualLayerV9`（= v918/v105 main run と同一エンジンスタックの縮小）。**stress OFF + semantic_pressure OFF**、4 knob 以外は canon 固定。
- **4 knob 写像（誕生時 M_c → 物理 param、サンプラー #30 = 実現値コピーでなく構造同型）**:
  - N ← B_gen×10
  - plb ← `0.007·(1+0.15·tanh(z_{S_avg}))`（±15%）
  - K_sync ← r_core を [0.05,0.30] に正規化
  - 初期θ ← phase_sig（von Mises κ=4）
- **読** = frozen `primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv` の n_core=5（17 CID）。**書** = `unified/v1301/` のみ。child engine は in-memory・親物理非書込（一方向）。
- **4 対照（#33）**: real / shuffle（param 集合を CID 間で並べ替え）/ random（レンジ内一様）/ canon（全 CID 平均で固定）。

### 2. 回した run

| run | 設計 | 規模 | コスト |
|---|---|---|---|
| smoke | 500step=1window | — | スモールスタート |
| long | 全 child 35,000step 固定 | 204 child（17×4×3seed）| Pool24 で 2008s（33.5分）|
| 寿命同期 | run長 = min(35000, life×ratio), ratio∈{1,10}, CID死で停止 | 408 child（×2 ratio）| 完走、`childworld_signatures_lifespan.parquet` |

- 寿命同期 1:1 = run長が寿命そのもの（35k 到達 2/17）。1:10 = ほぼ頭打ち（35k 到達 15/17）。

### 3. 統計監査（本区切りの本体・記録のみ判定なし）

前報告（`cw_run_lifespan_report.md`）の「smoke→long→寿命同期で像が保持」を、データの取り方・比較の仕方の矛盾という観点で再検した結果:

1. **`life→n_labels +0.85`（1:1）は run 長トートロジー**。1:1 では `corr(life, run_len)=1.000` で `corr(run_len, n_labels)=0.849 = corr(life, n_labels)`（小数3桁一致）。交絡を外した 1:10 では **p=0.30・CI[−0.31,+0.71]＝消滅**（1:10 でも run_len の方が主因）。「寿命が cid 構造を生む」の証拠ではない。
2. **canon の「std 最小」はアーティファクト**。run_len の cid 間 std は real/shuffle=12579 に対し **canon=0**（canon だけ life を平均で固定＝param と観測窓を二重固定）。示量署名の std が小さいのは当然で、CID 物理を語らない。
3. **★ real≒shuffle の真因 = 比較統計が pairing 盲目**。shuffle は param 集合を並べ替えるだけなので 17 CID の署名の周辺分布（mean/std）は構造上ほぼ不変（実測 |Δmean|=0.001〜0.02）。mean/std 対照は **どの CID にどの param が紐づくか（pairing）を一切見ない**ため、何があっても real≒shuffle になる。
4. **pairing を見る置換検定（real 17点で null を作り直し）にすると個性は検出される**: `K_sync→sync_order`（1:1 r=.66 / 1:10 r=.77）・`plb→link_density`（.79/.73）・`plb→label_density`（.70/.85）が **両 ratio で perm-p<0.005・CI が 0 を跨がない**。ただしこれらは「knob が物理 param を直接セット→その物理量が動く」＝ **manipulation check** であって CID 創発ではない。`θ→sync_order` は 1:1 のみ有意で脆い。

### 4. 母集団・写像の切り分け（real≒shuffle の原因の同定）

「CID 個性が効かない」と断じる前に、母集団が均質か／写像が入口で潰すかを既存データで切り分け（`cw_investigation_homogeneity_wiring.md`）:

- **§1 母集団**: 均質なのは B_gen のみ（CV=0.025、**B_gen≒n_core の関数**ゆえ n5 内で横並び）。r_core（CV0.364）・phase_sig は十分散る。
- **§2 写像**: K_sync は r_core の個性を**100% 伝達**（設計レンジ全使用）、θ は phase_sig を 84% 伝達（ただし初期値のみで減衰）。**写像が全チャネルで潰すは誤り**。弱いのは N（源 B_gen が均質）と plb（設計幅 ±15% が狭い + tanh 圧縮）の 2 点。
- **結論**: real≒shuffle は (1)母集団均質でも (2)写像が潰すでも (5)原理的に効かないでもなく、**(6) 比較統計が pairing 盲目**が主因。「効くチャネルでは効いている」。

### 5. 全検（全 CID 値→全物理 param）選定合理性の判断材料（3AI 合議の前段）

次の方向 (b) は全検＝全 CID 値を全物理 param に取り込む。だが「10 全て取り込む選定に合理性があるか」を 3AI 合議で詰めるため判断材料を揃えた（`cw_fulltest_selection_material.md`、調査のみ・実行ゼロ）:

- **§1 CID 値の独立次元**: 「10 個の独立値」ではない。**pooled（formed 85）の低次元（PC1=46%）は n_core 階層の産物**（corr(PC1, n_core)=0.91）。n_core 固定 stratum（n2, n=54）の真の独立軸は ~14（PC1=35%・Kaiser14）。**M_c4 値も独立でなく、共線ペアが stratum で変わる**（n2: B_gen↔S_avg=0.82 / n5: B_gen↔r_core=−0.94、頑健。phase_sig のみ一貫独立）。
- **§2 物理 param の独立性**: param は状態変数（L/θ/S/E/R/Z）で束ねられ独立軸は ~6-7。S は 4+ param が押し引きする過剰決定、beta は R↔S を結ぶ結合 knob、Flow が θ→E を結合。
- **§3 規模**: 配線可能 ~25 knob だが **knob 数はコストを増やさない**（cost driver = CID×対照×seed×step）。n_core 跨ぎ母集団 85（2:54/3:3/4:11/5:17）。**「5000 ノード」は親 v918 の N で child 目標でない**（child N=B_gen×10≈110-354）。seed≈12・全跨ぎ・2ratio で ~12h で回る。
- **§4 選定基準案（決めない・たたき台）**: 案A 独立軸代表（交絡最小・ただし n_core ごとに選定し直す要）/ 案B 構造同型拡張＋pairing 検定で相関吸収 / 案C 純全検（冗長・交絡）/ ハイブリッド。

### 6. この区切りの教訓（概念理解.md と同期）

- **肯定/像が保持して見えた結果ほど交絡を疑う**（教訓 414/428 の系）。「像が保持」の実体は大半 run 長効果だった。
- **比較統計が検出したいものを構造上見られるか確認する**（pairing を見ない mean/std で「個性なし」と結論しかけた）。
- **自分の監査自体も懐疑する**: 選定材料の自己再検で 3 点の誤り（pooling 産物の見落とし・M_c4 共線の符号バグ・5000 を親/child 混同）を自力で発見・修正。
- **観察は理解であって次の実装の準備でない**（教訓 433 系。child-world も「回せた」でなく「何が交絡で何が真か」を見るための系）。

---

### 出力ファイル（`unified/v1301/`）
- 設計/配線: `feasibility_check_report.md` / `wiring_probe.py` / `cid_param_wiring_investigation.md` / `physics_cid_ledger.md`（物理演算32・CID値130・配線可能 param 全数台帳）
- run: `cw_run.py`(smoke) / `cw_run_long.py` / `cw_run_lifespan.py` + `childworld_signatures*.parquet` / `*_summary*.json`
- 報告: `cw_run_result_report.md` / `cw_run_long_report.md` / `cw_run_lifespan_report.md`
- 監査/調査: `cw_investigation_homogeneity_wiring.md` / `cw_fulltest_selection_material.md`

*以上 v13 child-world 追補（Code A、2026-06-21、記録のみ・判定なし）。次は 3AI 合議（GPT 監査・Gemini 設計・Web Claude 統合）で全検の選定合理性を確定し、pairing 検定・共通観測窓・対称対照・seed≈12 で設計（Taka 承認後）。*
