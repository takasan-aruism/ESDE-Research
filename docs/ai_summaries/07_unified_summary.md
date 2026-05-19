# 07 Unified Phase Summary — v10.13.a + v1100 / v1101 / v1101a

*作成*: 2026-05-18、Web Claude (相談役)
*母体*: `06c_developmental_v1013_v1101_summary.md` (Code A 作成 2026-05-17、v10.13.a + v1100 + v1101 を網羅) を格上げ・統合し、v1101a を追加
*位置づけ*: Unified Phase が独立フェイズになったことに伴い新設された正式番号ドキュメント。従来 `06c` の枝番にぶら下がっていた Unified Phase 要約を `07` に格上げした。`06` 台 (06 / 06b / 06c) は Developmental Phase で完結・凍結。本書以降、Unified Phase の各主題は本書に追記して一本化する。
*親資料*: `06_developmental_summary.md` (v10.0-v10.9) + `06b_developmental_phase15_summary.md` (v10.4-v10.12、凍結) + `06c` (本書の母体、Developmental 完結時点で凍結)
*用途*: 新 Web Claude スレッド初見時に Unified Phase 全容 (v10.13.a 移行点 + v1100 Language 接続 + v1101 Atom 隆盛 + v1101a 注意機構) を把握する網羅的引き継ぎ。

---

## 0. ファイル番号体系の変更 (2026-05-18)

Unified Phase の独立に伴い、ファイル番号を繰り上げた。Developmental Phase 追加時 (2026-04-28) に一度繰り上げたのに続く 2 度目の繰り上げ。

| 旧番号 | 新番号 | ファイル |
|---|---|---|
| — | **07** | `07_unified_summary.md` (本書、新設) |
| 07 | **08** | `08_concept_core.md` (旧 `07_concept_core.md`) |
| 08 | **09** | `09_esde_system_structure.md` (旧 `08_esde_system_structure.md`) |
| 09 | **10** | `10_audit_principles.md` (旧 `09_audit_principles.md`) |
| 10 | **11** | `11_esde_language_summary.md` (旧 `10_esde_language_summary.md`) |

`06` / `06b` / `06c` は Developmental Phase 要約として据え置き・凍結。`01`-`05` (Genesis-Primitive) は変更なし。詳細は `00_index.md` の番号体系メモを参照。

**資料運用方針 (2026-05-18〜19 確定)**: phase 単位の詳細仕様書は廃止する。ESDE Genesis 開発当初は Code A がいなかったため詳細仕様書を重視したが、現在は Code A の認識確認 → 要点まとめ → 齟齬詰め → 実装というプロセスが毎回回るため、詳細仕様書は実質不要。主題設計書 (design.md) は資料タイプが異なり重要なため継続し、仕様書フォルダに階層構造で保存する (v1101a から運用)。Unified Phase の新主題は枝番を増やさず本書 (07) に追記して一本化する。

---

## 1. 一文サマリ

ESDE は v10.12 (Phase 1.5 第七試行、2026-05-11) の後 v10.13.a (5 phase Map analyzer、2026-05-12 完了) を経て **Unified Phase** へ移行し、v11.0.0 (v1100) で Language ↔ Genesis 接続の事前調査 (6 候補検証 + 候補 6 実装、両系の文脈非依存性は独立な atom を捕捉し Jaccard 0、Phase Result 未完成のまま残課題 A/B/C は Taka 判断で凍結)、v11.0.1 (v1101) で Taka 3 日長考の結論「Atom 的隆盛の統計的観察」(観察 1 一点を捉える / 観察 2 取り込み点中心の波及 / 観察 3 補助平均統計、Code A Step A-H 完了、核心発見 = 観察単位による dominant atom の 5 分裂)、v11.0.1.a (v1101a) で v1101 核心発見を起点とする「ESDE スケール注意機構」(v10.5 Salience-driven Focus を ESDE スケール・変化駆動へ 3 重構造転換、事前調査 → 2 AI 監査 → Taka 領域 3 箱確定 → 段階 1 + 段階 2 の Code A 担当完了、段階 1 核心観察 = 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍、段階 2 核心観察 = その波及増加は選択と集中でなく注意が動きながら広がる形、概念修正「注意の揺れと意識は別物」を Taka と AI の双方合意で確定) を扱った、v1101 と v1101a はいずれも物理層 frozen を完全保証 (bit-identity 3 層全 PASS) し新規 main run なしの既存出力流用 post-process、現在地は v1101a 段階 1 + 段階 2 + Phase Result 二本 + Concept Update 完成・会話接続の足取り点検まで完了し次主題を Taka が判断する段階。

---

## 2. v10.13.a — Unified Phase への移行点 (Phase 1.5 第八試行)

### 2.1 主題

v10.12 で「Atom 取り込み prototype 受容 cid 再厳格化」が完了 (Step K、2026-05-11) した後、v10.13.a は **5 phase Map analyzer + null phase analyzer + long phase compute** を扱った。Developmental Phase 1.5 の最後の試行であり、Unified Phase への橋渡し。

5 phase 定義 (`v113a_maps_analyzer.py`):
```
Phase 1: pre-atom_intro      (timestamp < target_step)
Phase 2: atom_intro          (timestamp == target_step)
Phase 3: post short          (target_step < timestamp ≤ target_step + 50)
Phase 4: post medium         (target_step + 50 < timestamp ≤ target_step + 200)
Phase 5: post long           (timestamp > target_step + 200)
```

### 2.2 主要成果

Map 1-5 (`developmental/v113a/`): phase × ncore / phase × path / phase × formation / phase × event / null phase per cell。Map 5 で 20 unique atoms が null absorption (path 経路を経ない波及) として 36 cells に出現 (TARGET_ATOMS 25 中)。

### 2.3 留保 #33 — 集計単位による方向反転 (重要、後続主題で一般化)

smoke seed 0 と main 24 seeds で 4/7 metric (path_excess 4 種全て) の cohens_d 符号が反転。集計単位を変えると結果の方向が変わる、という観察。この留保は後続で繰り返し一般化される — v1101 で「観察単位による dominant atom 反転」(Atom レベル)、v1101a で「集計単位による qc_regime 占有率の偏差」(注意レベル、留保 #L3)。Unified Phase を通底する観察。

---

## 3. v11.0.0 (v1100) — Language ↔ Genesis 接続事前調査

### 3.1 主題

v10.13.a 完了後、ESDE は Genesis 系 (v10.x) と Language 系 (Atom/Synapse/Phase 7-10、2026-03 凍結) を接続する Unified Phase に入った。v1100 はその第一歩で「両系の接続準備」の事前調査。

### 3.2 6 候補の事前検証

| 候補 | 内容 | Code A 判定 |
|---|---|---|
| ~~1~~ | UBAF 拡張 | 削除済 (UBAF prototype 凍結) |
| 2 | Synapse WSD に cid 状態注入 | v1100 範囲外 (大規模) |
| 3 | Phase 10 Cell | 概念再定義必要 (Phase 10 Cell ≠ Phase 8+9 Cell、齟齬 #36) |
| 4 | 5 phase × Projection | 簡略化版可、本来意図要設計 |
| 5 | Synapse 評価層化 | 実装可能 (簡略化版) |
| **6** | **null cell ↔ base 優位照合** | **v1100 で実装完了** |

### 3.3 候補 6 実装結果

Berlin sentences 79 targets の WSD 評価で base / B / C / BC の 4 mode を比較。R@3 では base 優位 token 0 (4 mode hit pattern 完全同一)、R@1 では base 優位 token 18 ("capital" 13 回他、base top-1 が `SOC.official`)。

核心観察: Language 系の base 優位 atom 集合 {SOC.official, PRP.part} 2 atoms と、Genesis 系 Map 5 の null cell atom 20 atoms の重なりが 0 (Jaccard 0)。両系の「文脈非依存性」は独立に異なる atom を捕捉している。留保 #34 candidate「両系の構造的同型性」は棄却方向 (ただし 79 targets は小サンプルで確定棄却ではない)。

### 3.4 v1100 の状態 (重要)

- Code A Step A-J 完了 (`unified/v1100/v1100_step_a_recognition.md` + `v1100_observation.md`)。
- **Web Claude Phase Result (Step K) は未作成**。v1101 が並行進行したため未完成のまま。
- Code A 提案の v1101 候補 A/B/C (Synapse 評価層化 / Phase 8+9 Cell ↔ Integration α/β 同型性検証 / 候補 6 大規模化) は Taka 判断で **凍結** (本 v1101 主題を優先したため。v11.0.x の後続で扱う可能性を残す)。
- 新規齟齬 #35 (Web Claude 親資料 `esde_language_reference_v1.md` repo 不在) / #36 (Phase 10 Cell ≠ Phase 8+9 Cell) / #37 (79 targets 小サンプル限界)。

---

## 4. v11.0.1 (v1101) — Atom 的隆盛の統計的観察

### 4.1 主題の成立

v1100 終了時点で Code A が v1101 候補 A/B/C を提案したが、Taka が 3 日長考 (2026-05-12〜) の結果、3 案より優先で「Atom 的隆盛の統計的観察」を v1101 主題と決定。当初 Web Claude が v1102 として作成 → Taka 番号修正指摘で v1101 に確定。

主題の核 (Taka 整理、原文): 「取り込むといって取り込んだからどうなる? に答えがない」という行き詰まりに対し、「Atom のような状態は濃度のようなもので確定的ではない」「重要なのは、どの一点を捉えられるか」「Integration 内の CID は同じ方向を向かなければいけないと決めないこと、平均化の罠」。観察対象を「Atom を取り込む (動作)」から「Atom らしきものの ESDE 内部の隆盛 (状態)」へ転換。

### 4.2 観察 3 視点

| 観察 | 中核 |
|---|---|
| 1 一点を捉える | 特定 cid (n_pulses_short 最大、48 中心 + ランダム 240 比較対照) の atom 状態を 4 解像度 trajectory で時系列化 |
| 2 取り込み点中心の波及 | atom_introduction_event 発火点 (受容 cid pool 420 由来 10,500 events) を中心に Δt±100 step 21 点で周辺観察 |
| 3 補助平均統計 | CID / Integration / ESDE の 3 単位、Integration は平均化せず分布表現 |

### 4.3 核心発見 — 観察単位による dominant atom の 5 分裂

同じ ESDE 系を、観察単位を変えるだけで「最も盛んな atom」が入れ替わる。CID-static `CHG.begin` / Integration β `FND.logic` / Integration α `TIM.moment` / ESDE event 解像度 `WLD.artless`+`PER.sound` / ESDE step10 `PER.sound` / ESDE window `TIM.moment`。5 つの atom が観察単位ごとに 1 位を取る。「ESDE で最も盛んな atom は何か」に構造的に単一の答えがない、という観察事実。Taka「平均化の罠」(絶対格言 #4) の生きた実例で、v10.13.a 留保 #33 の Atom レベル一般化。

### 4.4 副次発見

観察 2: 25 取り込み atom 中 4 atom のみ中心 cid を支配可 (`PER.sound` peak 84.8% at Δt=+20、`PRP.bright` 49.3%、`TIM.appear` 14.8%、`WLD.artless` 8.8%)、残り 21 atom は全 Δt で 0%。周辺 cid は取り込み atom によらず `PER.sound`+`WLD.artless` が常時 ~60% 占有。atom entropy が Δt 方向に単調減少 (取り込み後に集中化)。

観察 1: v108_standard 条件の中心 cid は dominant_atom が `WLD.artless` で 24 seeds 中 21 一致 + dominant_atom_fraction 0.92-1.00 (単 atom ロック)、v112 条件は 0.47-0.81 (複数 atom 揺れ)。window 解像度でのみ中心 cid の atom_change_rate がランダムより低い (時間スケール依存)。

### 4.5 v1101 の状態

Code A Step A-H 完了 (2026-05-17、commit 8 件、出力 25 ファイル 7 MB)。bit-identity 3 層全 PASS、v10.6/v10.8/v10.12 main outputs 1,306 ファイル frozen 完全保証、新規 main run なし。新規留保 #41 (Integration の member_cids 個別 cid id list が v10.x outputs に persistence されていない、段階 2 で cid state ledger 再生対応) + #42 (観察単位反転、Web Claude Phase Result 解釈統合領域)。Web Claude Phase Result は v1101a 着手のため並行未完成のまま — v1101 核心発見は v1101a の駆動要因として直接継承された。

---

## 5. v11.0.1.a (v1101a) — ESDE スケール注意機構

### 5.1 主題の成立 — v1101 核心発見の続き

v1101 が「観察単位ごとに dominant atom が割れる、単一の答えがない」を観察した直後、Taka が次主題候補として整理: 細胞レベルはカオスの海だが最大スケールに上がるのは「変化」である、主体は変化の大きなものに注意を向けその因果と影響を見る、これは cid の認知層・意識層の上位版。バージョン番号 v11.0.1.a (v1101 の進化系 `.a`) は、本主題が v1101 核心発見を直接の起点とする同系列の進化であることを示す。

主題化の経緯は、事前調査要望書 (Web Claude) → Code A Step 2/3 実環境照合 → GPT (Auditor) / Gemini (Architect) 2 AI 監査 → Taka 主題化決定 → 環境チェック → 段階 1 実装、という Unified Phase で最も段数を踏んだプロセス。

### 5.2 駆動要因 (GPT-1 監査確定文言)

> 本主題は、v10.5 Salience-driven Focus で cid レベルに成立している内生注意 (observer × candidate × mass-weighted 選択、mass = Q + C + β継承分) を、v1101 で確認された観察単位分裂に対応できるよう ESDE スケール / 複数構造単位へ拡張し、駆動信号を静的 mass から動的 change へ置き換える構造転換である。

→ 観察軸の追加でなく、既存 Q/C/β継承の 3 重構造転換 (集約スケール cid→ESDE / 駆動信号 静的mass→動的change / Q/C シーソーの cid→ESDE 同型展開)。

### 5.3 2 AI 監査による修正 4 点

事前調査フレームに対し GPT/Gemini 監査が 4 点を修正。Gemini-1 と GPT が独立に同じ穴 (系全体総和は集団平均の罠) を指摘した。

1. 駆動要因を GPT-1 確定文言に (内生化でなく 3 重構造転換)。
2. qc_ratio を系全体の単一比率にせず CID/α/β/ESDE 各単位で並列 emit、認知優位判定は多数決または中央値 (Gemini-1 + GPT 追加指摘)。
3. 変化指標 (atom_delta / rank1_flip_density / unit_kl_static) を統合せず 3 系列分離 emit、統合スコア・固定閾値・重み付け禁止 (GPT-2)。
4. emitter 境界条項の明文化 + `attention_locked` → `predicted_lock_mode` 改名 (GPT-3)。

### 5.4 Taka 領域 3 箱の確定

事前調査で監査者が触れず保留した 3 事項を Taka が確定:

- 箱 1 (意識優位の選択と集中が何を選ぶか) = **連想ゲーム**。意識は認知的活動の何かを踏み台にして立つ。「霧の中に意識だけ」を構造的に禁止。`predecessor_attention_ref` で踏み台への参照を記録。
- 箱 2 (主体をどの単位に置くか) = 主体は固定せず**切り替わる**。`change_scope` (どの構造単位で注意が立ったか) が主体の構造的根拠の記録。
- 箱 3 (selector の可否) = emitter/selector の二分を解消。注意と物理は別系統で**注意は物理を操らない**、観測の向きと位置を扱うのみ。全出力は確率的記述・候補に留め 100%・確定・唯一を emit しない (Aruism の対称性原則 — ランダムを潰さない)。なお v9.7 は認知層・意識層導入前 (両層は v10.x 構想、開発ロードマップで確認) のため selector の前例として扱わない。

### 5.5 段階 1 の実施と核心観察

Code A Step B-H 完了 (2026-05-18、commit 9 件)。注意 emit ログ 1,726,974 records (6 構造単位 × 3 変化指標 × 24 seeds)、所要 30 分弱、新規 main run なし。bit-identity 3 層全 PASS、v106/v107/v105 main outputs 1,097 ファイル frozen 完全保証、書き込みは `unified/v1101a/` 配下のみ。

**核心観察**: 意識優位 (conscious_dominant) のときの注意候補の波及 (influence_candidate_count) が認知優位の **1.54-1.78 倍**。6 構造単位すべてで同方向、ESDE 解像度系で倍率最大 (window 1.78×)。Taka フレーム「意識層 = 選択と集中」と方向が一致する。

### 5.6 段階 1 副次観察

- **Integration 経路が因果候補として全 24 seeds で 0 件** (留保 #L5)。因果候補 path は attention_via_salience 76.5% / familiarity 23.5% / temporal 0.01% に集中、integration_alpha/beta が一度も出現しない。Step H 後の追加調査で原因判明 — relation_strength が integration は 1.0 固定 binary・salience/familiarity は 2 桁連続値とスケールが根本的に異なり、Step E の sum argmax が不当比較していた。仮説 A (観測器の問題) / B (階層の役割分担) は両方真。Taka 判断 (iii) で Step E を sum argmax + z-score argmax の 2 方式併記に修正 (新バージョンを切らず v1101a 内課題)、z-score 方式では integration 合計 41.6% で出現・dominance 逆転。結論は「Integration が注意の由来か」でなく「その問いは集計方式に依存し単一の答えを持たない」(v1101 #42 / v10.13.a #33 と同型)。
- **意識優位時に familiarity 経路 +6%** (認知優位 19.1% → 意識優位 25.4%、留保 #L6)。箱 1「連想ゲーム」の方向的裏付け候補。
- predecessor 連鎖 (箱 1) が全 6 構造単位で成立 (埋まり率 86.6-100%)。「霧の中の意識だけ」を禁止する設計が動いた。
- seed 0 は控えめだが方向の反転なし・強化のみ (留保 #L3、v1101 #33 と同型)。
- alpha が records の 92.5% 占有 (留保 #L4、n_alphas 母数差由来)。Step F グラフは構造単位内割合に正規化済で集団平均の罠は回避。

### 5.7 段階 2 — 注意の方向性は選択と集中か拡散か

段階 2 は段階 1 核心観察 (波及 1.54-1.78 倍) が選択と集中か拡散かを時間軸を入れて切り分けた。新バージョンを切らず v1101a 内の段階として設計書から直接実装 (Code A Step A-F、bit-identity 3 層全 PASS、新規 main run なし)。

段階 2 核心観察 — **選択と集中ではない**。観察 B が全 6 構造単位で「認知優位フェーズは注意の中心 atom が安定し、意識優位フェーズは中心が動く」を示し、観察 A が「注意候補数は収束しない」を示した。意識優位時の波及は一点を深く掘るからでなく、注意が動きながら広がるから。Taka フレーム「意識 = 選択と集中」への反証的観察。

観察 C (注意の予測可能性 = Taka「ランダムか妥当か」) は構造単位で割れた — Integration スケールは実測が shuffle baseline の 6-11 倍かつ 100% 未満で「Aさんの揺れ幅」(緩く予測でき確定しない帯) に乗る妥当性が観測された、CID は予測定義の自己言及で 100% 到達 (留保 #L8、単体は揺れ幅を持たず重なって初めて揺れが生まれる)、ESDE 3 解像度は集約で測定不能 (留保 #L10)。

### 5.8 概念修正 — 注意の揺れと意識は別物 (v1101a Concept Update、双方合意)

段階 2 が ESDE 内部の概念「意識 = 選択と集中」(v10.2 以来) を修正。段階 2 が観察したのは「注意の揺れ」(固定集中でもランダム拡散でもなく構造的に妥当な範囲内で動く第三の形) であって「意識」そのものではない。意識 = 注意の揺れ + 状況コントロール + 慣れ の複合で、ESDE はまだ注意の揺れしか観察していない。「意識 = 選択と集中」はこの複合の表層を本質と取り違えた誤認。Taka の理解と AI の説明可能性判断が合致したため双方合意として確定 (`v1101a_concept_update.md`)。

関連する概念整理 — 注意は固定点でなく移動軌跡 (attention trajectory) として読む / 揺れ幅は構造の重なりで生まれる (CID は閉じた点、Integration で揺れが生まれる) / CID・Integration・ESDE の役割分担。

### 5.9 Phase Result の置き方 (段階 1/2 共通の規律)

段階 1 核心観察の解釈は「意識優位という状態と波及の広さが連動する」に留め「選択と集中が立証された」とは言わなかった。段階 2 も「選択と集中ではない」を観察事実として置き、「意識とは何か」の定義はしなかった。出口固定 (絶対格言 #6) の「単一の確定像を出さない」原則どおり。主題評価は Taka 領域。

### 5.10 v1101a の状態

Code A 主題担当範囲 (段階 1 Step B-H + Step E 修正 + 段階 2 Step A-F) 完了。Web Claude Phase Result 二本 (`v1101a_phase_result.md` 段階 1 / `v1101a_phase_2_phase_result.md` 段階 2) + `v1101a_concept_update.md` (概念整理) + 会話接続の足取り点検 (`esde_conversation_path_check.md`) 完成。段階 3 (生きた版、時間が逐次進む、新規 main run 必要) は v1101a 設計書で範囲外。

会話接続の足取り点検の結論 — 2 AI 提案「会話応答を Integration スケールの attention trajectory から読む」を入力から返答まで 5 段に分解して点検した結果、段 1-3 は説明可能性が保てるが段 4 (揺れを応答候補にする) と段 5 (atom→言語変換、v1100 Jaccard 0) は飛躍。道筋は段 3 までしか通っておらず、今そのまま主題化できる完成した道筋ではない。段 4 は「未定義の飛躍」で、定義する作業が次主題になりうる。次主題の確定は Taka 領域。

---

## 6. 現在地 + 後続タスク

### 6.1 完了状態

- v10.13.a Map analyzer 完了。
- v1100 候補 6 実装完了 (Phase Result 未完成)。
- v1101 Step A-H 完了 + Web Claude Phase Result は v1101a 着手のため未作成 (核心発見は v1101a 駆動要因に継承済)。
- v1101a 段階 1 (Step B-H + Step E 修正) + 段階 2 (Step A-F) で Code A 主題担当完了。Phase Result 二本 + Concept Update + 会話接続足取り点検 完成。
- 物理層 frozen 絶対維持 (Developmental + Unified 通算)。

### 6.2 待機中タスク

| タスク | 担当 | 状態 |
|---|---|---|
| 次主題の選定 | Taka | v1101a 完了、会話接続足取り点検が判断材料。道 A (段 4 主題化) / B (atom 変換) / C (器官の切り分け) / D (Taka 直感) |
| v1100 Step K (Phase Result) | Web Claude | 未完成、扱うか後回しか未定 |
| v1101 Step J (Phase Result) | Web Claude | 未作成 (核心発見は v1101a に継承済、独立 Phase Result を別途作るかは未定) |
| v1100 残課題 A/B/C | 未定 | 凍結中、v11.0.x 後続で扱う可能性 |
| v1101a 段階 3 (生きた版) | 未定 | v1101a 設計書で範囲外、新規 main run 必要、後段主題 |

### 6.3 主題評価判断

Code A は judgment 回避 (絶対格言 #12)。観察結果の主題評価 (success/fail) は Taka 領域。Web Claude Phase Result は解釈統合の素材を提供、最終評価は Taka が決定。

---

## 7. Unified Phase の留保事項

### 7.1 Unified Phase で発生した留保

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

### 7.2 留保 #33 系列 — Unified Phase を通底する観察

v10.13.a #33「集計単位による方向反転」は、v1101 #42「観察単位による dominant atom 反転」、v1101a #L3「集計単位による qc_regime 占有率偏差」と、主題が変わっても繰り返し現れた。Unified Phase は「集計単位を変えると像が変わる」という観察が一貫して立ち上がるフェイズになっている。v1101a の qc_ratio 構造単位別並列・変化指標 3 系列分離 (監査修正 #2 #3) は、この観察を設計に折り込んだ結果。

---

## 8. 絶対格言 15 件 (Unified Phase 全主題で遵守)

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

## 9. 参照すべき repo 内資料

### 9.1 v10.13.a

`developmental/v113a/` — `v113a_step_a_recognition.md` / `v113a_observation_report.md` / `v113a_maps_analyzer.py` / `outputs/main/map{1-5}_*.parquet`

### 9.2 v1100 (Language ↔ Genesis、Phase Result 未完成)

`unified/v1100/` — `v1100_step_a_recognition.md` / `v1100_observation.md` (Step J、Phase Result の代替) / `language_side_investigation_report.md` / `v1100_candidate_6_*.py` / `outputs/candidate_6_*.json`

### 9.3 v1101 (Atom 的隆盛、Code A 担当完了)

`unified/v1101/` — `v1101_phase_design.md` (主題ドキュメント) / `v1101_web_claude_handoff.md` / `v1101_step_a_recognition.md` 〜 `v1101_step_h_observation_final.md` / 実装スクリプト 5 / `outputs/main/observation_{1,2,3}_*.parquet` / `outputs/v1101_observation.html`

### 9.4 v1101a (ESDE スケール注意機構、段階 1+2 完了)

`unified/v1101a/` — `v1101a_phase_design.md` (段階 1 主題設計書) / `v1101a_phase_2_design.md` (段階 2 設計書) / `v1101a_step_b_environment_check.md` / `v1101a_step_h_observation_final.md` (段階 1 Code A 観察報告) / `v1101a_phase_2_step_f_observation_final.md` (段階 2 Code A 観察報告) / `v1101a_internal_task_step_e_causality_fix.md` + `v1101a_step_e_causality_fix_observation.md` (Step E 修正、#L5 対応) / `v1101a_phase_result.md` (段階 1 Phase Result) / `v1101a_phase_2_phase_result.md` (段階 2 Phase Result) / `v1101a_concept_update.md` (概念整理) / `esde_conversation_path_check.md` (会話接続足取り点検) / 実装スクリプト / `outputs/` 配下 parquet + HTML。design.md は仕様書フォルダに階層保存。事前調査資料は `unified/v1101/post_v1101_attention_pre_investigation/` に history 残置。

事前調査資料は `unified/v1101/post_v1101_attention_pre_investigation/` に history として残置 (Code A Step 2/3 成果物等)。

---

## 10. 新 Web Claude スレッドへの申し送り

- Unified Phase の全容把握は本書 (07) で足りる。`06` / `06b` / `06c` は Developmental Phase 用で凍結済、Unified Phase の新主題は本書に追記して一本化する (06d/06e の枝番継続はしない)。
- phase 単位の詳細仕様書は廃止 (2026-05-18〜19)。Code A の認識確認 → 要点まとめ → 齟齬詰め → 実装のプロセスが回るため不要。主題設計書 (design.md) は資料タイプが異なり継続、仕様書フォルダに階層保存。
- v1101a は段階 1+2 完了。次主題は未定 — `esde_conversation_path_check.md` が判断材料 (会話接続は段 3 まで通り、段 4-5 は未定義の飛躍)。道 A (段 4 主題化) / B (atom 変換) / C (器官の切り分け) / D (Taka 直感)。本書を読む時点で次主題が決まっている可能性があるので repo の最新状態を確認すること。
- 留保 #33 系列 (集計単位を変えると像が変わる) は Unified Phase を通底する。v1101a 段階 2 の観察 C (注意の妥当性が構造単位で割れる) も同型。新主題で「単一の集計値で語りたい」衝動が出たら、v1101 核心発見と v1101a 監査修正 #2 #3 を読むこと。
- 概念修正に注意 — v1101a Concept Update で「意識 = 選択と集中」は修正された (`v1101a_concept_update.md`)。段階 2 が観察したのは「注意の揺れ」であって「意識」ではない (意識 = 注意の揺れ + 状況コントロール + 慣れ)。新主題で「意識」という語を使うときは、ESDE が実際に観察しているのが注意の揺れだけであることに注意。
- v1100 / v1101 の Phase Result が未完成のまま。Unified Phase は Phase Result の作成が後回しになりやすい。後続で整理が要る。

---

## 11. 一文サマリ (再掲)

本書は Unified Phase が独立フェイズになったことに伴い `06c` を母体に格上げ・新設された正式番号ドキュメント (07) であり、ESDE が v10.13.a (5 phase Map analyzer、Phase 1.5 第八試行) で Unified Phase へ移行した後、v11.0.0 (v1100) で Language ↔ Genesis 接続事前調査 (候補 6 実装、両系の文脈非依存性は独立 atom を捕捉し Jaccard 0、Phase Result 未完成・残課題 A/B/C 凍結)、v11.0.1 (v1101) で Taka 3 日長考の「Atom 的隆盛の統計的観察」(観察 1/2/3、Code A Step A-H 完了、核心発見 = 観察単位による dominant atom の 5 分裂)、v11.0.1.a (v1101a) で v1101 核心発見を起点とする「ESDE スケール注意機構」(v10.5 Salience-driven Focus の 3 重構造転換、事前調査 → 2 AI 監査修正 4 点 → Taka 領域 3 箱確定 → 段階 1 + 段階 2 の Code A 担当完了、段階 1 核心観察 = 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍、段階 2 核心観察 = その波及増加は選択と集中でなく注意が動きながら広がる形、留保 #L5 は Step E 修正で「集計方式依存」と決着、概念修正「注意の揺れと意識は別物」を双方合意で確定)、を扱い、v1101/v1101a はいずれも物理層 frozen 完全保証・新規 main run なしの post-process、留保 #33 系列 (集計単位を変えると像が変わる) が Unified Phase を通底し、現在地は v1101a 段階 1+2 + Phase Result 二本 + Concept Update + 会話接続足取り点検 完成で次主題を Taka が判断する段階、ファイル番号は本書新設に伴い旧 07-10 を 08-11 へ繰り上げ phase 単位詳細仕様書は廃止 (主題設計書は継続)。

---

*以上、07 Unified Phase Summary (Web Claude、2026-05-19 更新)。`06c` を母体に v1101a 段階 1+2 完了まで反映。Unified Phase の新主題は本書に追記して一本化する。新 Web Claude スレッドは本書 + `00_index.md` 用語対応表 + v1101a 関連資料で Unified Phase 全容を把握可能。*
