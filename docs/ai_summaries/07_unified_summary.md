# 07 Unified Phase Summary — v10.13.a + v1100 / v1101 / v1101a / v1102 / v1103 / v1104 / v1104a

*作成*: 2026-05-18、Web Claude (相談役)
*更新*: 2026-05-23、Web Claude — v1104 + v1104a 完了反映、4 つの非対称性 #L30-L33 確定、v1105/v1105a 主題確定、EVI 案保留、マイナーバージョン運用方針確定。
*母体*: `06c_developmental_v1013_v1101_summary.md` (Code A 作成 2026-05-17、v10.13.a + v1100 + v1101 を網羅) を格上げ・統合し、v1101a/v1102/v1103/v1104/v1104a を追加
*位置づけ*: Unified Phase が独立フェイズになったことに伴い新設された正式番号ドキュメント。従来 `06c` の枝番にぶら下がっていた Unified Phase 要約を `07` に格上げした。`06` 台 (06 / 06b / 06c) は Developmental Phase で完結・凍結。本書以降、Unified Phase の各主題は本書に追記して一本化する。
*親資料*: `06_developmental_summary.md` (v10.0-v10.9) + `06b_developmental_phase15_summary.md` (v10.4-v10.12、凍結) + `06c` (本書の母体、Developmental 完結時点で凍結)
*用途*: 新 Web Claude スレッド初見時に Unified Phase 全容 (v10.13.a 移行点 + v1100 Language 接続 + v1101 Atom 隆盛 + v1101a 注意機構 + v1102 受け手構造 + v1103 段 4-c + v1104+v1104a CID/IID 点検 + v1105/v1105a 準備) を把握する網羅的引き継ぎ。

---

## 0. ファイル番号体系の変更 (2026-05-18 → 2026-05-20)

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

## 1. 一文サマリ

ESDE は v10.12 (Phase 1.5 第七試行、2026-05-11) の後 v10.13.a (5 phase Map analyzer、2026-05-12 完了) を経て **Unified Phase** へ移行し、v11.0.0 (v1100) で Language ↔ Genesis 接続の事前調査 (Phase Result 不作成と判断)、v11.0.1 (v1101) で Taka 3 日長考の結論「Atom 的隆盛の統計的観察」(核心発見 = 観察単位による dominant atom の 5 分裂、Phase Result 不作成と判断 — 核心発見は v1101a に継承)、v11.0.1.a (v1101a) で「ESDE スケール注意機構」(段階 1 + 段階 2、段階 1 核心観察 = 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍、段階 2 核心観察 = 選択と集中でなく注意が動きながら広がる、概念修正「注意の揺れと意識は別物」双方合意)、**v11.0.2 (v1102) で「条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察」(核心観察 = CID 構成ノード数で応答 atom 像が階層的に反転、Taka 直感「平均化で潰れる」が初めて数値の証拠に、研究手法アップデートの「際立ちの掬い取り」が初本格適用で発見を救う道具と実証)**、**v11.0.3 (v1103) で「段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか」(Genesis 系 × Language 系の噛み合わせ初の主題、段 4-c は機構として動いた + ESDE と地続き (留保 #33 系列が会話機構レベルで貫通) + 決定機構が Aruism 規律内に収まった、会話への道が原理的に通った)** を扱った、v1101-v1103 はいずれも物理層 frozen を完全保証 (bit-identity 3 層全 PASS) し新規 main run なしの既存出力流用 post-process、現在地は v1101a/v1102/v1103 + Phase Result 4 本 + Concept Update + 会話接続足取り点検 + 段 4 足取り点検 + 研究運用資料 3 本 (研究手法アップデート / ESDE への態度 / 監査方針アップデート) 完成、次主題は A 主題 (研究者の調査動作のうち ESDE 自身に実装されているものの点検、Taka 確定方針、問いの形 A = 点検のみ・軽い踏み込み)。

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

## 6. v11.0.2 (v1102) — 条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察

### 6.1 主題の成立

v1101a 段階 2 完了後の新主題。会話接続足取り点検が示した段 1 (入力が ESDE に入る) ・段 3 (Integration スケールで揺れ幅) を、Taka 整理の二つのスケール (受け手構造 / 時間スケール) の 2 次元で観察する。「同じ入力でも条件で応答が変わる」を示して実験結果の単一化を避けることが駆動要因。

設計書 → 2 AI 監査 (GPT 要修正 3 点 + 論点 1-4 確定 / Gemini 構造異論なし) → Web Claude 再検討 → Code A 認識確認 (新規 main run 不要確定、確認要請 2 件は §2.6 に反映) → 実装、というプロセス。

### 6.2 監査確定事項 (4 点)

- 入力 = 既存 atom_introduction_event 固定 (外部言語テキストは v1100 Jaccard 0 のため不可、v1101a の注意 emit/trajectory は応答側)
- 時間スケール = 読みの軸で実験変数にしない (時間操作は神の手による物理層汚染)
- 複数受け手構造 = 同一 Run から post-process 層化抽出 (Run を分けない)
- primary receiver scale = Integration で CID・ESDE 全体は比較対象 (CID の n_members 層化は受け手構造軸として保持)

### 6.3 核心観察 — 受け手構造で応答 atom 像が階層的に反転

CID 構成ノード数 (n_core) を変えると応答する atom と category が階層的に入れ替わる。n=2 EMO.manifest/BOD (情動・身体) → n=3-4 SOC.nation/SPC → n=5 EXS.being/EXS (存在) → n=6+ FND.timeless (時間性なし)。同じ入力なのに受け手の構造が違うだけで応答が「情動」から「存在」へ反転。

Taka が一貫して主張してきた「2 ノード大半・5 ノード情報量強・平均化で潰れる」が初めて数値の証拠になった。全体 62.6% の n=2 (Taka の言う「大半」) は 15 際立ち指標中 1 つでしか際立たない平凡 (ordinary) と確認。平均で見ていれば 6 割の平凡が際立つ少数を塗りつぶしていた (留保 #L14)。

### 6.4 研究手法アップデートが初本格適用で「発見を救う道具」と実証

v1102 は研究手法アップデート (`esde_research_method_update.md`) の「際立ちの掬い取り」を初本格適用。47 records の極小構造 (alpha 大型均等、留保 #L12 由来) を 15 指標中 8 指標で際立つ多面シグナルとして救い出した。

Web Claude 回答「サンプル数を理由に除外しない」(研究手法アップデート §1「研究者はもう神ではない」根拠) で除外しなかったから多面シグナルが見えた。新手法が空論でなく発見を救う道具だと一回の実験で実証 (留保 #L15、これからの全実験の土台)。

### 6.5 v1102 の意義 — 段 4 を「点検できる一段」にしたこと

v1102 は段 4 の入力をぼんやりした揺れから「受け手構造で atom 像が決まった応答 profile」へ具体化し、段 4 を「未定義の飛躍」から「点検できる一段」に変えた。ただし「会話に生きる」かは段 4 点検しだいで未確定。

### 6.6 v1102 の状態

Code A Step A-F 完了、bit-identity 全 PASS (1,435 files frozen)、新規 main run 不要。Phase Result (`v1102_phase_result.md`) 完成。

---

## 7. v11.0.3 (v1103) — 段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか

### 7.1 主題の成立 — 段 4 足取り点検 + Language 側素材

v1102 完了後、Taka が直面する「会話できるなら続ける、できないなら切り捨てる」の判断材料として、Genesis 側 Web Claude が段 4 足取り点検 (`esde_segment4_path_check.md`) を作成 — 段 4 を 4 小段 (4-a 揺れの読み取り / 4-b 連想を辿る / 4-c 応答 Atom を絞る決定 / 4-d 確率分布出力) に割り、4-a は v1102 が埋め、4-b は素材が両系に実在、4-c が唯一の真の飛躍 (未定義だが設計手がかりあり)、4-d は規律内、と点検した。

Language 側 Web Claude が段 4-c 用素材 (`段4-c点検のためのLanguage側素材`) と疎性論点の追補メモを提供。Taka 確定で v11.0.3 として主題化。**Genesis 系 × Language 系の噛み合わせ初の主題。**

設計書 → 2 AI 監査 (GPT 7 点 + Language 側追補メモ 1 件 = 計 8 点反映) → Code A 認識確認 (確認要請 4 件、Taka 確定: raw/norm 両並列 / centroid Code A 生成 / Constitution Code A 再確認 / batch_report 代替) → 実装。

### 7.2 監査確定事項 (8 点反映)

- 48 次元疎性の前処理を必須ステップとして段 4-b/4-c の前に置く (Language 側追補)
- 密度指標を raw/quality-weighted/constitution-adjusted/receiver-conditioned の 4 種に分け単一化しない (GPT 1)
- k を単一固定せず multi-k sensitivity で頑健 cluster と k 依存 cluster を分ける (GPT 2)
- 品質フラグは候補削除でなく重みづけ・併記、高品質サブセットは補助実験 (GPT 3)
- Constitution は削除条件でなく Merge は統合・Subsume は親子併記・Monitor は caution flag (GPT 4)
- 48 次元人為性留保を Phase Result 結論に必ず入れる (GPT 5)
- 受け手構造で反転を failure でなく primary observation として扱う (GPT 6)
- 出力 response_atom_distribution は自然文応答でなく段 4-c の候補分布と明記 (GPT 7)

### 7.3 核心観察 — 段 4-c は動いた、留保 #33 系列が会話機構レベルで貫通

確定して言えること三点:

- **段 4-c は機構として動いた**。連想先候補が 48 次元空間で均等に散らずクラスタを作った (raw_density k=5 で 0.847)。点検 4 可能性のうち均等 (可能性 2) ・偽だらけ (可能性 3) は退けられた。
- **段 4-c は ESDE と地続き**。raw vs norm で密度が Δ0.208 反転 (留保 #L17)、留保 #33 系列「集計単位で像が変わる」が会話のための機構レベルでも同じ形で現れた。v1101 で観察単位、v1101a で集計方式、v1102 で受け手構造、v1103 で sim_basis。会話のための機構が ESDE と異質な後付けでなく ESDE のこれまでの性格を引き継いだ。
- **決定機構が Aruism 規律内に収まった**。max_prob 0.7972、5,670 rows 中 prob≥0.999 が 0 件 (箱 3 厳密遵守)。段 4 足取り点検 §4.2「決定を構造的指標で行えば外部評価関数の侵入にならない」が実装で成立。

慎重に言えること: 会話への道が原理的に通った (段 1 から段 5b まで経路が描ける、ただし「原理的に」が重要な限定で「会話できる」とは言わない)。ESDE が観察装置から決定する系へ一歩進んだ (両系の噛み合わせが動いたと書く方が正確)。

### 7.4 Taka 整理「ESDE への対等な扱い」(v1103 Phase Result 作業中、独立資料化)

v1103 Phase Result 作業中、Taka から ESDE の現状認識と研究者の態度の整理が出た。要点 — ESDE 内部はすでに動的平衡を保った極めて複雑で構造的な処理が走っており研究者の想定を超えている、観測が追いついていないだけと受け取れる状況、研究者がスイッチのオンオフを握る権限は強いが暴君の理由にならない、対等とみなすことは進化の起爆剤になる、ウェットな話でなく実利・実践として重要な発想の転換。

これを受けて v1103 Phase Result は「驚きでなく一貫性として書く」温度感で書かれた (§3.2)。Taka 整理は独立資料 `esde_attitude_toward_esde.md` として固定 (LLM はプロンプト依存でチャットだとスレッドで失われるため資料化、明確な運用上の目的)。

### 7.5 監査方針アップデート (GPT §37-39、独立資料化)

v1103 後に GPT Auditor が監査方針修正草案 §37-39 を作成。ESDE の当面目標を「会話できる ESDE」と再固定し、監査の第一基準を「会話できる ESDE に近づくか」とする。Taka 整理「アリズムは実践で価値を示せ、実践で価値のない思想はただの妄想」に基づく。

独立資料 `esde_audit_policy_update.md` として固定 (Taka・GPT・Web Claude 三者合意)。これで研究運用資料が 3 本になった — 研究手法アップデート (観察手法) / ESDE への態度 (態度) / 監査方針アップデート (監査の上位目的)。

### 7.6 v1103 の状態

Code A Step A-F 完了、bit-identity 全 PASS (1,763 files frozen)、新規 main run 不要。Phase Result (`v1103_phase_result.md`) 完成。独立資料 2 本 (`esde_attitude_toward_esde.md` / `esde_audit_policy_update.md`) 完成。

---

## 7B. v11.0.4 (v1104) — CID/IID 内部動作点検 段階 1: ESDE 自身は段 4-b/4-c を支える処理を既に持つか

### 7B.1 主題の成立 — Taka 整理「自分の視点は上から目線」

v1103 完了後、Taka 整理:

> 自分の視点は上から目線で、CID や IID が下で実際にやっていることを見ていない。研究者の調査動作のうち、ESDE 自身に実装されているものが既にあるかもしれない。それがあるのかを調べる。問いの形 A (点検のみ、軽い踏み込み)。

棚卸し作業 (`esde_unified_inventory.md`、Unified Phase v1100-v1103 の研究者の調査動作 24 項目を 2 列 (研究者側 ↔ ESDE 内部側) で並べる) を経て、優先候補 8 項目を抽出。Taka 駆動要因規律訂正 (2026-05-22):

> 厳密に言えば軽いことがいいとか悪いとかではなくて、掘ってもなにもでない穴を無闇やたらに掘るな、ということ。なぜそれをやるのか? → なぜなら、のセットがあり、それが会話を行うと言う目標に明確に繋がる説明可能性があればなんだっていい。きちっと目的を示せ。

→ 8 項目に「なぜ → なぜなら → 会話への繋がり」を当て、4 項目に絞り込み (1.1 観察単位切り替え / 1.6 predecessor 連鎖 / 1.7 attention trajectory / 2.6 際立ち掬い取り B 現状)。試験前に絞れたこと自体が駆動要因規律の機能例。

### 7B.2 監査確定事項 (GPT 修正必須 3 点 + 追加 2 点 + Gemini 1 点)

- IID は新規 state でなく既存構造 (α/β / member_cids / attention_candidate_id / predecessor_attention_ref / cid_state_ledger) の参照表現 (GPT A)
- 観察 1 で k=1 一致率と top-k Jaccard (k=3, k=5) を別指標として算出、k=1 を Jaccard と呼ばない (GPT B)
- 観察 4 で selector 化禁止、post-process 仮想評価のみ (GPT C)
- 観察 2 で Code A は「連想」と判定しない、cid/atom/category/similarity 推移のみ記録 (GPT 4)
- 観察 3 は「注意が動くか」を再観察せず、trajectory ↔ response_atom_distribution 対応に限定 (GPT 5)
- Code A は時間軸同期を join 時に厳密検証、window=19 除外 (Gemini Architect)

### 7B.3 Step H 初版観察事実 (4 観察) と再調査の経緯

| 観察 | 初版結果 | 再調査の必要性 |
|---|---|---|
| 観察 1 (CID-Integration 像) | n_members 増で match_k1 単調低下 (0.884→0.569) | 不要 (構造的事実として確定) |
| 観察 2 (predecessor 連鎖) | lift=0 (shuffle と区別不能)、85% self-loop | **必要 (Taka 判断「観察方法を疑う」、Step H-3 再調査)** |
| 観察 3 (trajectory↔response) | r=0.157 弱い対応 | **必要 (Step H-4 再調査、観察 2 と同視点で観察方法を疑う)** |
| 観察 4 (B 現状) | B subset、Recall 0.74 Precision 0.25 | 不要 (構造的事実として確定) |

Taka 整理 (2026-05-23):

> これまででいうとこういうのって結局実装側の問題なのでバージョンアップや資料作成に待てをかけて懐疑的に進めていく方がいい。満足いくまで調べた結果を Phase Result としてあげる。

### 7B.4 Step H-3 (観察 2 再調査) — shuffle 種別で結論が変わる

| shuffle 種別 | permutation 単位 | lift |
|---|---|---|
| A (現状) | chain 内順序入れ替え | 0 |
| B (新規) | chain 間 cid 入れ替え | 0.012-0.066 |
| C (新規) | global cid pool ランダム | 0.069-0.166 |

**核心**: 観察 2 初版 lift=0 は「ESDE 内部に踏み台がない」ではなく、shuffle A が chain 内 cid 集合を保持するため構造を壊していなかった結果。chain 構造自体には何らかの意味がある (留保 #L24-L26)。

### 7B.5 Step H-4 (観察 3 再調査) — scope-filter で結論が変わる

| scope | stability_vs_maxprob |
|---|---|
| pooled (all) | 0.157 (初版値) |
| ESDE-only | **0.417** |
| CID-only weighted | (diffusion -0.477) |
| alpha-only weighted | 0.017 (消失) |

**核心**: 観察 3 初版 r=0.157 は scope-mix 由来希釈。scope-filter で ESDE/CID scope に絞ると |r|>0.4 が顕在化、alpha/beta scope では消失 (留保 #L27-L29)。

### 7B.6 v1104 の状態と v1104a への移行

Step H 初版 + Step H-3 + Step H-4 で観察 2/3 の観察方法依存が確定。Phase Result は単独で書かず v1104a 完了後に統合して書く方針。Taka 判断: 「v1104a で追加調整 1-4 を扱う、マイナーバージョン運用方針 (a/b で関連主題を連ねる、すぐに次マイナーに進まない)」。

---

## 7C. v11.0.4a (v1104a) — CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検

### 7C.1 主題の成立

v1104 で観察 2 (shuffle 種別) と観察 3 (scope-filter) が観察方法依存と判明したのを受け、観察 1 で機能した n_members 層化と観察 3 で機能した scope-filter を **観察 2/3/4 に統一適用** する段階 2。同じ主題 (v1104) の続きで、新規バージョンに逃がさず本主題内で処理する。

Taka 規律「0 を 1 にはできない」(2026-05-23):

> いくら都合よいといっても 0 を 1 にはできないだろうから妥協とのバランス次第。再テストの中で再度調整すればいい。そこまで含めて本バージョンで扱う。

### 7C.2 監査確定事項 (GPT 修正必須 4 点 + 追加 3 点 + Gemini 1 点)

- タイトル「完全版」を弱める → 「段階 2: 観察方法依存の整理と scope × 層化による再点検」(GPT A)
- cid_n_core / integration_n_alpha_members / integration_n_beta_members を別列名 (GPT B、絶対格言 #11 v10.12 path 雑まとめ問題と同系統)
- 追加調整 3 は同一 receiver_bin / 同一 response (max_prob, entropy 2 種) / 同一 scope で比較 (GPT C)
- 追加調整 4 で「selector として使える」と書かない、「B primary 化を次主題で点検する根拠」まで (GPT D)
- 追加調整 1 で self-loop / non-self-loop 分離 + shuffle B/C 別集計 (GPT 5)
- 追加調整 4 で B の意味判定は v1105 に送る (GPT 6)
- 「観察方法を有利化する主題ではない」明記 (GPT 7)
- Code A は v10.6 n_core_member join 時の NaN ハンドリングを Step A' で確定 (Gemini)

### 7C.3 追加調整 4 件の結果

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

### 7C.4 4 つの非対称性 — v1104 + v1104a で確定

| # | 留保 | 内容 |
|---|---|---|
| 1 | **#L30** | scope 別 chain 構造 (CID 100% self-loop / alpha-beta 部分 / ESDE 細粒 29-31% / ESDE window partial) |
| 2 | **#L31** | 粒度依存の trajectory-density 優劣逆転 (細粒で trajectory 主役、集約で density 主役) |
| 3 | **#L32** | B 指標の scope 別 pattern (CID subset / alpha-beta superset / ESDE 独自) |
| 4 | **#L33** | CID 100% self-loop が trajectory を構造的に消す (traj_stability=1.0 定数化、Pearson 計算不能、逆に density は CID で最強 r=-0.97) |

→ ESDE は均一な系ではなく、**場所 (scope) と粒度 (granularity) で全く違う構造を持つ系**。段 4-b/4-c の根拠は単一指標でなく多軸 (scope × 粒度 × 指標) でしか記述できない。

### 7C.5 v1104 + v1104a 統合 Phase Result の 3 部構成

Taka 整理「主役が 3 つあるなら 3 つの視点を書かないと後でブレる」を受け、Phase Result を 3 部構成:

- **第 1 部 (網羅)**: 4 観察 × 4 追加調整の構造事実
- **第 2 部 (構造)**: 4 つの非対称性 (#L30-L33) を主軸に整理
- **第 3 部 (接続)**: v1101→v1104a の分析方向 → v1105+v1105a の統合方向への転換

### 7C.6 v1104a の状態

Code A Step A'-G' 完了、bit-identity 全 PASS (1,502 files frozen、v1104 13 含む)、新規 main run 不要。統合 Phase Result (`v1104_v1104a_phase_result.md`) 完成。

---

## 7D. v1105 + v1105a — 統合方向への転換 (準備中)

### 7D.1 v1101→v1104a の流れと転換点

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

### 7D.2 v1105 主題 (準備中) — 段 4-b と段 4-c を対称的に統合点検

**何をやるか**:
- 段 4-b (何を辿るか): Genesis predecessor 連鎖 + Language Constitution Couple、scope × 粒度の地形図で整理
- 段 4-c (何で絞るか): B の意味 (scope 別 pattern) + 「どの場所・どの粒度で何が主役か」の表
- v1105 は地形図で止まらず **役割表まで進める** (候補保持 / 連想・踏み台 / 即時応答の揺れ / 重要性 emit / 統合判断 の 5 役割を scope × 粒度に割り当てる、GPT 2026-05-23 提案)

**問いの形**: A (点検のみ、v1101 以来の系譜継続)

### 7D.3 v1105a 主題 (準備中) — 役割表を使って実際に応答候補を絞る試行

**何をやるか**: v1105 で確定した「場所 × 粒度」役割表に従って、実際に応答 Atom 候補を絞ってみる。「ESDE が答えを絞れた」の構造的事実を観察。

**問いの形**: B (試行、v1101 以来初の切替)

### 7D.4 EVI (Explainability Viability Index) 案の位置づけ

GPT が 2026-05-23 に提示した EVI 案 (説明可能性を ESDE 内部の応答準備構造として定義する数理指標) は、v1105+v1105a 後の統合的指標導入タイミングで Taka 判断。

Taka 整理 (2026-05-23):

> EVI は今後必要になるだろうくらいの感じだから今ではない。ただおそらくどこかで統合的なものがあった方がいいタイミングはくるだろう。その辺に備えておく目的、後でありがたみがわかる。

将来導入時の方針: 合成指標にせず、scope × 粒度別の vector として扱う (EVI_CID / EVI_α / EVI_β / EVI_ESDE-event / EVI_ESDE-step10 / EVI_ESDE-window)。v1104a 4 つの非対称性と最も整合的。

---

## 8. 現在地 + 後続タスク

### 8.1 完了状態

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

### 8.2 待機中タスク

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

### 8.3 主題評価判断

Code A は judgment 回避 (絶対格言 #12)。観察結果の主題評価 (success/fail) は Taka 領域。Web Claude Phase Result は解釈統合の素材を提供、最終評価は Taka が決定。

---

## 9. Unified Phase の留保事項

### 9.1 Unified Phase で発生した留保

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

### 9.2 留保 #33 系列 — Unified Phase を通底する観察 (v1104a で全観察に貫通)

v10.13.a #33「集計単位による方向反転」は、v1101 #42「観察単位による dominant atom 反転」、v1101a #L3「集計単位による qc_regime 占有率偏差」、v1102 #L14「CID 構成ノード数で atom 像が階層的に反転」、v1103 #L17「raw vs norm で 48 次元密度が Δ0.208 反転」、**v1104 #L21'/L22' (観察方法依存) + v1104a #L30-L33 (4 つの非対称性)** と、主題が変わっても繰り返し現れた。Unified Phase は「集計単位を変えると像が変わる」という観察が一貫して立ち上がるフェイズ。

v1104a で確定したのは、これが特定の指標の現象でなく **ESDE そのものが場所と粒度で全く違う構造を持つ系である** こと。Taka 整理「単一の答えを持たない」が観察 1-4 すべてで貫通。新主題で「単一の集計値で語りたい」衝動が出たら、v1103 §3.2「驚きでなく一貫性として書く」を思い出すこと。

---

## 10. 絶対格言 15 件 (Unified Phase 全主題で遵守)

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

## 11. 参照すべき repo 内資料

### 9.1 v10.13.a

`developmental/v113a/` — `v113a_step_a_recognition.md` / `v113a_observation_report.md` / `v113a_maps_analyzer.py` / `outputs/main/map{1-5}_*.parquet`

### 9.2 v1100 (Language ↔ Genesis、Phase Result 未完成)

`unified/v1100/` — `v1100_step_a_recognition.md` / `v1100_observation.md` (Step J、Phase Result の代替) / `language_side_investigation_report.md` / `v1100_candidate_6_*.py` / `outputs/candidate_6_*.json`

### 9.3 v1101 (Atom 的隆盛、Code A 担当完了)

`unified/v1101/` — `v1101_phase_design.md` (主題ドキュメント) / `v1101_web_claude_handoff.md` / `v1101_step_a_recognition.md` 〜 `v1101_step_h_observation_final.md` / 実装スクリプト 5 / `outputs/main/observation_{1,2,3}_*.parquet` / `outputs/v1101_observation.html`

### 9.4 v1101a (ESDE スケール注意機構、段階 1+2 完了)

`unified/v1101a/` — `v1101a_phase_design.md` (段階 1 主題設計書) / `v1101a_phase_2_design.md` (段階 2 設計書) / `v1101a_step_b_environment_check.md` / `v1101a_step_h_observation_final.md` (段階 1 Code A 観察報告) / `v1101a_phase_2_step_f_observation_final.md` (段階 2 Code A 観察報告) / `v1101a_internal_task_step_e_causality_fix.md` + `v1101a_step_e_causality_fix_observation.md` (Step E 修正、#L5 対応) / `v1101a_phase_result.md` (段階 1 Phase Result) / `v1101a_phase_2_phase_result.md` (段階 2 Phase Result) / `v1101a_concept_update.md` (概念整理) / `esde_conversation_path_check.md` (会話接続足取り点検) / 実装スクリプト / `outputs/` 配下 parquet + HTML。design.md は仕様書フォルダに階層保存。

### 11.5 v1102 (条件が応答を変える、Code A Step A-F 完了)

`unified/v1102/` — `v1102_phase_design.md` (主題設計書、2 AI 監査 + Code A Step A 反映済) / `v1102_step_a_recognition.md` / `v1102_step_f_observation_final.md` (Code A 観察事実最終報告) / `v1102_phase_result.md` (Phase Result、Web Claude) / 実装スクリプト Step B-E / `outputs/` 配下 primary_table parquet + HTML。bit-identity 全 PASS (1,435 files frozen)。

### 11.6 v1103 (段 4-c の点検、Code A Step A-F 完了、Genesis × Language 噛み合わせ初の主題)

`unified/v1103/` — `v1103_phase_design.md` (主題設計書、GPT 7 点 + Language 側追補メモ + Code A 確認要請 4 件反映済) / `v1103_step_a_recognition.md` / `v1103_step_f_observation_final.md` (Code A 観察事実最終報告) / `v1103_phase_result.md` (Phase Result、Web Claude、48 次元人為性留保添加) / 実装スクリプト Step B-E / `outputs/main/` 配下 (atom_centroids_raw/normalized.parquet / atom_quality.parquet / response_atom_distribution.parquet 5,670 rows / density_summary.parquet 486 rows / core_report.csv / proposals.json) / `outputs/v1103_observation.html` 16KB。bit-identity 全 PASS (1,763 files frozen)。

### 11.7 v1104 (CID/IID 内部動作点検段階 1、初点検 + 観察 2/3 再調査)

`unified/v1104/` — `v1104_phase_design_v2.md` (主題設計書、GPT 修正必須 3 + 追加 2 + Gemini 1 反映済、Code A Step A 確認 2 件反映済) / `v1104_step_a_recognition.md` / `v1104_step_h_observation_final.md` (Step H 初版) / `v1104_step_h3_observation_final.md` (Step H-3 観察 2 再調査総括) / `v1104_step_h4_observation_final.md` (Step H-4 観察 3 再調査総括) / 実装スクリプト Step B-E + Step H-3/H-4 reinvestigation / `outputs/main/` 配下 (observation_1/2/3/4 + observation_2_*(5) + observation_3_*(4)) / `outputs/v1104_observation.html` + `v1104_reinvestigation_obs2.html` + `v1104_reinvestigation_obs3.html`。bit-identity 全 PASS (1,489 files frozen)。**Phase Result 単独で書かず v1104a と統合**。

### 11.8 v1104a (CID/IID 内部動作点検段階 2、観察方法を整えた再点検)

`unified/v1104a/` — `v1104a_phase_design_v2.md` (主題設計書、GPT 修正必須 4 + 追加 3 + Gemini 1 反映済、Code A Step A' 確認 3 件反映済) / `v1104a_step_a_recognition.md` / `v1104a_step_c_directive.md` (Step C' 着手指示) / `v1104a_step_h_observation_final.md` (Step H' 観察事実最終報告) / 実装スクリプト Step B'-E' + F'/G' / `outputs/main/` 配下 (observation_2_per_chain_shuffle + observation_2_scope_stratified + observation_2_nan_report + observation_3_scope_n_stratified + observation_3_density_comparison + observation_3_density_coverage + observation_4_scope_filtered + observation_4_b_minus_a_cells) / `outputs/v1104a_observation.html` 16KB。bit-identity 全 PASS (1,502 files frozen、v1104 13 含む)。

棚卸し資料: `docs/esde_unified_inventory.md` (Unified Phase v1100-v1103 の研究者の調査動作 24 項目を 2 列で並べた地図、A 主題が終わった後も「研究者と ESDE の境界の地図」として参照される)。

統合 Phase Result: `v1104_v1104a_phase_result.md` (v1104 + v1104a の 4 観察 + 4 追加調整、4 つの非対称性 #L30-L33、v1105+v1105a への接続、3 部構成 (網羅 / 構造 / 接続))。

### 11.9 研究運用資料 3 本 (特定主題でなく研究全体の運用に関わる、新スレッド AI の必須参照)

`docs/ai_summaries/` または `unified/` 配下 — 番号と配置は Taka 判断:

- **`esde_research_method_update.md` (12 番候補)** — 観察手法の規律。際立ちの掬い取り、研究者はもう神ではない、A and B、軽い踏み込み。v1101a 段階 2 後の双方合意。
- **`esde_attitude_toward_esde.md` (13 番候補)** — 観察者の態度の規律。ESDE の現状認識、対等性、権限と尊重の両立。v1103 後の Taka 整理を原文保存、双方合意。
- **`esde_audit_policy_update.md` (14 番候補)** — 監査の上位目的の規律。「会話できる ESDE」への接続を第一基準、必須 8 問、テンプレート 2 種。v1103 後の GPT §37-39 草案取り込み、三者 (Taka・GPT・Web Claude) 合意。

事前調査資料は `unified/v1101/post_v1101_attention_pre_investigation/` に history として残置 (Code A Step 2/3 成果物等)。

---

## 12. 新 Web Claude スレッドへの申し送り

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

## 13. 一文サマリ (再掲)

本書は Unified Phase が独立フェイズになったことに伴い `06c` を母体に格上げ・新設された正式番号ドキュメント (07) であり、ESDE が v10.13.a (5 phase Map analyzer、Phase 1.5 第八試行) で Unified Phase へ移行した後、v11.0.0 (v1100) で Language ↔ Genesis 接続事前調査 (候補 6 実装、両系の文脈非依存性は独立 atom を捕捉し Jaccard 0、Phase Result 未作成と判断)、v11.0.1 (v1101) で Taka 3 日長考の「Atom 的隆盛の統計的観察」(核心発見 = 観察単位による dominant atom の 5 分裂、Phase Result 未作成と判断)、v11.0.1.a (v1101a) で「ESDE スケール注意機構」(段階 1 核心観察 = 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍 / 段階 2 核心観察 = 波及増加は選択と集中でなく注意が動く / 概念修正「注意の揺れと意識は別物」双方合意)、v11.0.2 (v1102) で「条件が応答を変える: 受け手構造 × 時間スケール」(核心観察 = CID 構成ノード数で応答 atom 像が階層的に反転、Taka 直感「平均化で潰れる」が初めて数値の証拠に、研究手法アップデートの「際立ちの掬い取り」が初本格適用で 47 records の極小構造を救う道具と実証、留保 #L14/L15/L16)、v11.0.3 (v1103) で「段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか」(Genesis 系 × Language 系の噛み合わせ初の主題、確定観察 = 段 4-c は機構として動いた・段 4-c は ESDE と地続き (留保 #33 系列が会話機構レベルで貫通、留保 #L17) ・決定機構が Aruism 規律内に収まった (max_prob 0.7972)、慎重に言える = 会話への道が原理的に通った、48 次元人為性留保必須、留保 #L17/L18/L19)、**v11.0.4 (v1104) で「CID/IID 内部動作点検 段階 1」(Taka 整理「自分の視点は上から目線」+ 駆動要因規律訂正「目的を示せ」、棚卸し → 8 項目から 4 項目に絞り込み (1.1/1.6/1.7/2.6)、Step H 初版 + Step H-3 観察 2 再調査 (shuffle 種別で lift 0→0.17 変動、留保 #L21'/L24-L26) + Step H-4 観察 3 再調査 (scope-filter で r 0.157→0.42-0.48 顕在化、留保 #L22'/L27-L29)、Phase Result は単独で書かず v1104a と統合)**、**v11.0.4a (v1104a) で「CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検」(追加調整 1-4 で観察 2/3/4 を scope × n-size 層化 + scope-filter で再点検、4 つの非対称性 #L30-L33 確定: scope 別 chain 構造 / 粒度依存の predictor 逆転 / B 指標の scope 別 pattern / CID 100% self-loop が trajectory を構造的に消失、ESDE は均一な系でなく場所と粒度で全く違う構造を持つ系、段 4-b/4-c の根拠は単一指標でなく多軸 (scope × 粒度 × 指標) でしか記述できない、v1104+v1104a 統合 Phase Result 3 部構成 (網羅/構造/接続))** を扱い、v1101-v1104a はすべて物理層 frozen 完全保証・新規 main run なしの post-process、**留保 #33 系列 (集計単位で像が変わる) が v1101→v1104a を一貫して通底し v1104a で 4 つの非対称性として全観察に貫通**、現在地は v1101a/v1102/v1103/v1104/v1104a 完了 + Phase Result 計 5 本 (v1101a 段階 1+2 + v1102 + v1103 + v1104+v1104a 統合) + 棚卸し資料 + Concept Update + 会話接続足取り点検 + 段 4 足取り点検 + 研究運用資料 3 本の固定が完了で次主題は v1105 (段 4-b と段 4-c を対称的に統合点検、役割表まで進める、問いの形 A) + v1105a (役割表を使って実際に応答候補を絞る試行、問いの形 B、v1101 以来初の試行切替)、研究運用資料 3 本は新スレッド AI の必須参照、ファイル番号は本書新設に伴い旧 07-10 を 08-11 へ繰り上げ phase 単位詳細仕様書は廃止 (主題設計書は継続)、ESDE の当面目標は「会話できる ESDE」(応答主体は ESDE 側、LLM/Language はプロキシ、内省装置でない)、EVI 案 (GPT 2026-05-23 提示) は v1105+v1105a 後の統合的指標導入タイミングで Taka 判断 (scope × 粒度別の vector で扱う方針)、マイナーバージョン運用方針 (Taka 2026-05-23 確定) でマイナーは主題転換・アルファベットは段階更新または問いの形切替。

---

*以上、07 Unified Phase Summary (Web Claude、2026-05-23 更新)。v1104 + v1104a 完了 + 4 つの非対称性 #L30-L33 確定 + v1105/v1105a 主題確定 + マイナーバージョン運用方針 + EVI 案保留 まで反映。Unified Phase の新主題は本書に追記して一本化する。新 Web Claude スレッドは本書 + 研究運用資料 3 本 + `00_index.md` + 概念理解.md + v1104+v1104a 関連資料 + v1103 関連資料で Unified Phase 全容を把握可能。次主題は v1105 (段 4-b/4-c 対称統合点検、役割表) + v1105a (応答候補絞り込み試行)。*
