# ESDE 研究史 — AI 向け超要約 (Index + 用語対応表)

*作成日*: 2026-04-11 (v9.9 Long Run 進行中)
*更新*: 2026-04-21 (v9.16 完了、観察サンプリング機構で見える範囲の時間的予測不能化、v9.15-16 で主体性の戦略が一段深まる)
*対象読者*: ESDE-Research に新規に関わる Claude (新スレッド初見)

---

## このディレクトリの目的

ESDE 研究の各フェーズ (Genesis / Ecology / Autonomy / Cognition / Primitive) と哲学的コア (概念理解) を、未来の Claude が **context に乗せても暴走しない最小サイズ** に圧縮したもの。

各原本 (200-1300 行) の要点だけを抽出し、却下された方針 (失敗の記録) を必ず残してある。**未来の Claude が同じ失敗を繰り返さないため**。

---

## ⚠️ 警告

- これは**要約**であり原本ではない。設計の詳細や個別実験の数値が必要な場合は必ず原本 (`docs/ESDE_*_Report.md` および `docs/概念理解.md`) を参照すること。
- **要約の最新時点は v9.14 完了 (2026-04-18)**。05, 06, 07 は v9.14 対応済み (05 は旧 05b/05c addendum を統合済み、v9.14 セクション追加)。01-04 は v9.9 時点のまま (古い表記が含まれる、本ファイル末尾の用語対応表で確認)。
- **推測補完していない**。原本にあることだけ抽出している。「書いてないこと」を埋めようとしないこと。
- 概念理解.md からの引用は **必ず引用形式 (>) で残してある**。Taka の発言を勝手に言い換えないこと。

---

## 推奨読書順序

```
00_index.md (このファイル)
  ↓ ★末尾の「用語対応表」を必ず最初に読む
06_concept_core.md      ← 哲学コアと絶対ルールを把握 (v9.14 対応)
  ↓
01_genesis_summary.md   ← 物理層 (床) の確立 (古い表記あり)
  ↓
02_ecology_summary.md   ← observer 複数性 (古い表記あり)
  ↓
03_autonomy_summary.md  ← label 自律性、5-node 転換点 (古い表記あり)
  ↓
04_cognition_summary.md ← ★ 失敗の記録 (最重要、古い表記あり)
  ↓
05_primitive_summary.md ← Primitive phase 全体 (v9.0-v9.14、v9.14 対応、旧 05b/05c 統合済)
  ↓
07_esde_system_structure.md ← 現行システム構造 (v9.14 対応)
```

**急ぎなら**: 本ファイル末尾の **用語対応表** + `07_esde_system_structure.md` + `05_primitive_summary.md` の v9.14 セクション の組み合わせで現状作業に最低限着手できる。**ただし `04_cognition_summary.md` の「却下された方針」は時間を作って必ず読むこと**。

---

## ファイル一覧

| # | ファイル | 原本 | 内容 | 更新状況 |
|---|---|---|---|---|
| 00 | `00_index.md` | (このファイル) | ナビゲーション + 用語対応表 | **v9.16 対応** |
| 01 | `01_genesis_summary.md` | ESDE_Genesis_Report.md (638 行) | 物理層の確立、5 Forces、観察者 k\*=4、N=10000 まで scale 不変 | v9.9 時点 (古い表記あり) |
| 02 | `02_ecology_summary.md` | ESDE_Ecology_Report.md (242 行) | observer 複数性、global は lossy compression、long_drift がデフォルト | v9.9 時点 |
| 03 | `03_autonomy_summary.md` | ESDE_Autonomy_Report.md (749 行) | label = 魂 (frozenset)、territory = 場、5-node 転換点、Lifecycle Instrumentation | v9.9 時点 |
| 04 | `04_cognition_summary.md` | ESDE_Cognition_Report_Final.md (1271 行) | **★最重要・最複雑**。v3-v7 の試行錯誤、「物理層は床」結論、virtual layer の確立 | v9.9 時点 |
| 05 | `05_primitive_summary.md` | ESDE_Primitive_Report.md | Primitive phase 全体 (v9.0-v9.16): 4 層構造、cid、Cognitive Capture、v9.13 persistence-based birth、v9.14 Paired Audit + E3 = cid 間共鳴、v9.15 CidSelfBuffer + event 駆動 Fetch + サイコロの比喩、v9.16 観察サンプリング + age_factor + 説明可能性仮説 | **v9.16 対応** |
| 06 | `06_concept_core.md` | 概念理解.md | Aruism、4 層構造、絶対ルール、Taka 発言、戦国大名モデル、v9.13 記憶の所在、v9.14 E3 = cid 間共鳴、v9.15 A/B 分離 + 研究者主観の封印、v9.16 サンプリング + 時間的認識 + Constitution 接続 | **v9.16 対応** |
| 07 | `07_esde_system_structure.md` | (要約のみ) | ESDE 現行システム構造、4 層、Layer B (Shadow Ledger)、Layer 外 CidSelfBuffer (v9.15)、v9.16 段階 3 サンプリング機構 | **v9.16 対応** |

---

## 最小限知っておくべき項目 (v9.16 対応)

未来の Claude が要約を読む前に最低限把握すべきこと:

1. **物理層には介入しない**。Cognition v5.x で「選択なき循環は洗濯機」と確定。**認知層・意識層も介入しない** (v9.11 で 4 層規律確立、v9.13 で方向性として再確認)。介入するのは存在層のみ (θ への torque)。
2. **label = frozenset の魂**、解放しない。cid (v9.8a 以降) は label とは別の観察主体。
3. **観察者は複数**。global は lossy compression、local が真。
4. **5-node が転換点**。density independent な唯一のサイズ (Autonomy で確定)。
5. **数値解釈は analyzer 段階で**。一次出力 (per_window/per_subject CSV) は構造語のみ ("formed"/"unformed"/"tie"/"none")。
6. **cid は B_Gen と M_c を持つ** (v9.11 新規)。物理層由来の固有値で個体差が立ち上がる。
7. **B_Gen は capture probability の直接入力ではない** (v9.11 規律)。M_c 経由の間接効果のみ。
8. **「事象」= 周囲の現象そのもの** (Taka 構想)。設計者が定義する外部のラベルではない。
9. **4 層構造** (v9.11 確立): 物理 / 存在 / 認知 / 意識。
10. **新運用ルール** (v9.11): Claude Code A/B 分担、チェック依頼書必須、並列化必須。

### v9.12 で追加された重要事項 (2026-04-16)

11. **Δ は i.i.d.** — M_c と E_t の乖離は蓄積しない。各 pulse 独立。L06 capture 低下は n_core 構成効果 (時間効果ではない)。
12. **phase+r 72% 支配の原因は正規化圧縮 + 物理的定常性** — NORM_N=86 による d_n 圧縮 (C 仮説) + S_avg の物理的安定性 (A 仮説)。E_t 定義偏り (B 仮説) は否定。
13. **S≥0.20 hard threshold は神の手** — Taka 判断で撤去が v9.13 の主題に。

### v9.13 で確定した重要事項 (2026-04-17)

14. **S≥0.20 撤去完了、persistence-based birth 採用** — age_r ≥ τ の connected component のみが label 化。τ=50/100 両条件で R>0 純度 100% 達成。経路 B (R>0 ペア即 label) は廃止。
15. **v9.11 の主要所見の多くはアーティファクト** — 「n=2 主体 (67%)」は経路 B + R=0 混入の産物で、純粋には 22-28%。「phase+r 72% 支配」も n_core 構成効果で、均等化すると 63% + n 軸 27% に。v9.11 結論を無批判に引用しないこと。
16. **n≥6 欠落は S≥0.20 撤去だけでは解決しない** — 50% overlap フィルタと非空間的リンク形成が残存要因。大型 label の出現頻度は v9.11 と同水準。
17. **認知層は物理層を支配しない** (Taka 2026-04-16 定義) — 効果は劇的ではなく統計的に多少の差。v9.7 の「認知 → 存在介入」は撤回済、これを再発させない。
18. **CID の記憶は物理層の中に既にある** (Taka 2026-04-16) — 足りないのは「記憶を作る仕組み」ではなく「物理状態を記憶として読む関数」。次フェーズ (v9.15 想定) の主題。
19. **「無駄だから切る」禁止** (Taka 2026-04-16) — 不利な機能でも削除せず、どう活かすか考える。pickup は休眠保持。
20. **AI 間文書は日本語 md** (Taka 2026-04-16) — 運営原則 v2 の英語ルールは撤回。Taka が読めることが最優先。既存コード docstring は英語のまま維持。

### v9.14 で確定した重要事項 (2026-04-18)

21. **Paired Audit 原則** — 新機構は runtime 主体置換ではなく audit として先行走行させる。bit-identity 必須。Layer A (既存 50 step pulse) を完全不変のまま、Layer B (event 駆動 spend ledger) を並行稼働。promotion 判断は analysis 結果が揃ってから。
22. **B_Gen 資源化の実装達成** — Q0 = floor(B_Gen) を cid の初期原資として、event 発生時に spend (1 消費)。long run で Q0 が実際の消費量として機能することを確認。short run (5000 step) では exhaustion 2-3% のみ、long run (25000 step) で 22-84% へ顕在化。
23. **E3 (cid 間接触) が認知活動の主因** — 全 event の 70-90% が E3、E3 除去で exhaustion 完全消滅。認知資源の消費は接触圧が主。これは問題ではなく ESDE が社会的な系であることの証明。
24. **E3 = cid 間 2 者共鳴** (Taka 2026-04-18) — ノード間共鳴 R_ij の cid スケール版として再概念化。両 cid が 1 spend ずつ消費 (計 2 単位) は Aruism の存在の対称性と整合。
25. **上位層構築の合理的条件が揃った** (Taka 2026-04-18) — v9.14 の真の達成は B_Gen 資源化でも E3 でもなく、「三項以上の上位層を構築する足場」が整ったこと。ただし実装は棚上げ、v9.15 は認知層継続 (記憶の読み出し関数) を優先。
26. **三項共鳴実装に先走らない** (v9.14) — v3.4 tripartite loop は「成立したが持続しない」系 (bridge_max_life=1)。cid スケールで実装しても同じ壁が予想される。
27. **Layer A と Layer B は異なる情報を取る** — Pearson 相関 0.089 は「全体スナップショットと局所精査は別の情報を見る」という設計的帰結。Layer B が Layer A を置き換える議論は早計。
28. **E2 rise/fall は情報量が非対称** — rise delta 0.033、fall delta 0.091 (2.8 倍)。共鳴崩壊の瞬間の方が情報量が大きい。
29. **Layer A 再定義の宿題** (Taka 2026-04-18) — 固定 pulse は観測機械として残置 OK、ただし現状 v9.11 Cognitive Capture で cid 内部状態を更新しているため「純粋な観測機械」ではない。v9.15 以降で切り分け。
30. **seed 構成の一本化 (v9.15 から)** — Short + Long 廃止、Long 24 seeds × tracking 50 × steps 500 × -j24 に統一。約 2h30m。24 → 48 の統計力向上は √2 倍のみで費用対効果悪し。分散分析は v9.15 から導入。
31. **E3 variant 候補は棚上げ** — phase 近接接触、持続接触、多重接触等の絞り込みは v9.15 以降の検討候補として記録。現在の E3 (物理接触の初回性のみ) のシンプルさを v9.14 では維持。

### v9.15 で確定した重要事項 (2026-04-20)

32. **A (研究者観察) と B (CID 主体) の分離** — 研究者が CID の物理状態を数値化する機構 (A) と、CID 自身が自分の構造を専用領域に取り込む機構 (B) は根本的に別物。Claude が A 発想で草案を書き Taka 指摘で根本転換した経緯。v9.15 は B 実装。A/B を混同しない。
33. **A/B 分離の四重担保** — ファイル / クラス / メモリ / 命名の各レベルで A と B を分ける。B ファイルは A モジュールを import しない、A ファイルは B から read-only でのみ読む。研究者向け統計量 (mean, std 等) を CID 内部に持たせない。
34. **CidSelfBuffer クラスの確立** — CID 専用メモリ領域。生誕時スナップショット (theta_birth, S_birth) + 最新 Fetch スナップショット + 一致/不一致痕跡。研究者向け集約指標は持たない。
35. **段階 1 (50 step 固定 Fetch) は研究者視点** (Taka 2026-04-20) — タイミングが研究者指定である限り主観性は成立しない。主観性の最小条件はタイミングの予測不能性。
36. **段階 2 = event 駆動 Fetch** — v9.14 の全 event (E1/E2/E3) をトリガーに Fetch を発動。Fetch コストなし (Q 会計から独立、基準値 0 を維持)。Match Ratio 廃止 (集約指標は研究者視点)、3 点セット (any_mismatch_ever / mismatch_count_total / last_mismatch_step) + E1/E2/E3 別カウント。
37. **Layer 構造の拡張禁止** (Taka 判断 2026-04-18) — B の世界は「Layer」と呼ばない。Layer は研究者のスケールの概念、CID 主体の世界は別領域 (精神分析学と認知心理学ほど違う領域)。
38. **サイコロの比喩 — 研究者主観の封印** (Taka 核心発見 2026-04-20) — 研究者は「次の目が 1/6」と言えるが「次の目が 1」とは言えない。サイコロ自身は「私は 1」と主張できる。ESDE 段階 2 で、研究者は CID の自己読みタイミングを予測できない構造が成立した。これが ESDE の意識研究の戦略的転換点。
39. **ランダム性が論理の支柱** (Taka 2026-04-20) — 研究者は原理的に CID 内部を覗ける (A/B 分離しても)。この弱点を予測不能性で埋める。「自己がある」と「自己はない」の中間 (哲学以上科学未満) で戦う。ランダム性を削る方向は採らない。
40. **機械的「自分について語る」は自己ではない** (Taka 2026-04-20) — 決定論的な自己主張は単なる計算機。ランダム性を伴って初めて自己の候補になる。自己の条件は「予測不能性を伴って主張できること」。「それっぽさ」(LLM 的会話) は市場承認の条件、v11.x 以降。
41. **v9.16 = 段階 3 (確率的 Fetch 失敗)** — Taka 判断 2026-04-20 で確定。タイミングの予測不能性 (段階 2) に加え、結果の予測不能性を導入する。ランダム性を削る方向は採らない原則の実装。
42. **CID 視点と研究者視点の並列記述** — v9.15 の文書作成ルール。両視点を分離して記録する。「CID が変化を知る」は強すぎ、「生誕時との不一致を持つ」止まり (GPT 監査指摘)。
43. **tolerance 1e-6 の離散一致は連続空間で原理的に機能しない** — 段階 1 で Match Ratio 全 0 となり、段階 2 で比率集約を廃止。連続量 (divergence_norm) の方が情報量が多い。
44. **段階 1 と段階 2 で divergence ほぼ同じ** — median 3.53 vs 3.58。タイミング変更は divergence を変えない (物理層が支配)。ESDE の系の安定性を示唆する可能性 (断定しない、検証するならノード数を変えて実験)。
45. **ノード数固定は実験制御であって神の手ではない** (Taka 2026-04-20) — 物理層クローズだからこそ認知層の発展が追跡できる。ノード数変動は大幅後回し、認知層十分発展後の検討事項。
46. **発生頻度の違う event 間で比率や数値を比較しても構造的情報は出ない** (Taka 2026-04-20) — 観察の規律。「E3 が 83%」は E3 の発生頻度が高いことの再確認、意味を盛らない。
47. **Claude の癖 (整理過剰、意味を盛る、研究者視点偏重) は消えない** (Taka 2026-04-20) — 3 役分離 (Gemini 加速 / GPT 制動 / Claude 整理) で相対化する運用。反省より運用切り替えが生産的。

### v9.16 で確定した重要事項 (2026-04-21)

48. **段階 3 = 観察サンプリング** — age_factor = Q_remaining / Q0 に比例した数のノードのみ観察、残りは missing。「Fetch の確率的失敗」ではなく「差分の選択的認識」(Taka 規律 4 の実装)。
49. **age_factor = Q_remaining / Q0** — 線形比率で十分 (2 AI 統合回答)。B_Gen は間接使用 (Q0 = floor(B_Gen) 経由)。
50. **サンプリング方式** — 2 AI 統合判断で案 1 (サンプリング) 採用。tolerance 可変 (案 2) と確率判定 (案 3) は却下。ζ (補完しない) と最も整合。
51. **任意 RNG の独立** — engine.rng を一切 touch しない、hash ベース独自 RNG で局所サンプリング。PYTHONHASHSEED 非依存のため明示 event_type マップを使う (Code A 判断)。
52. **Q 消費は現状維持** — v9.14 event spend のみ、v9.16 判定では追加消費しない。Fetch コスト 0 原則の継続。将来の変更差分を測りやすく維持。
53. **missing は any_mismatch_ever に含めない** — 観察されたノードのみで判定。missing はリンク同様 any_mismatch の集約から除外。リンクは link_match_ratio として divergence_log にのみ残る (段階 2 から変更、段階 3 禁止事項 #24)。
54. **観察結果と代数的必然の区別** — age_factor 区間別 missing 比率の単調関係は「観察」ではなく「`n_observed = round(n_core × age_factor)` から代数的に導かれる設計の確認」。観察事実と仕様の帰結を混同しない。
55. **Q 枯渇 cid 34.26 %** — tracking 50 windows で 1/3 の fetched cid が age_factor=0 到達。smoke (tracking 10) では 0 件、long run で顕在化する現象。
56. **段階 1-2-3 で theta_diff_norm 完全一致** — 物理層の drift 計算は段階間で不変 (max 差 0.0)。Layer C の改変が物理計算に影響していないことの構造的証明。
57. **説明可能性の時間的構造** (Taka 2026-04-21 仮説) — 過去は時間経過で広がっていく = 説明可能性の減衰。現在 → 過去/未来 の 2 方向に説明可能性が減衰。未来の定義候補として段階 5 以降で実装検討。
58. **説明可能性は not decide, but describe と同格の原則** (Taka 2026-04-21 指定) — 3 AI 共通運用。憲法 §3 (Explainability) の具体化。
59. **Constitution (2026-03-05) は既に明文化済み** — v9.15-16 の議論は新規原則ではなく憲法の具体化。§2 Core Objective、§3 Explainability、§5 Anti-Drift、§7 Governance、§9 Success Definition が現在の運用を規定している。
60. **動的均衡の違和感は物理スケール扱う段階で重要** (Taka 2026-04-21) — 現在 (認知層主題) は消費 -1 固定で問題なし。物理層クローズが現在の発展を可能にしている。
61. **先走り防止チェックポイント** (GPT §12) — バージョン名決定時点で入出力を一文で言えるか、「失敗」「認識」「自己」等を物理操作へ還元できるか、観察と行動を混ぜていないか。Claude の癖への構造的対処。
62. **指示書に一文定義を含める** — v9.16 指示書 §0.2 で導入済、v9.17 以降も継続。

---

## このディレクトリの更新ポリシー

- **既存レポート (`docs/ESDE_*_Report.md`、`docs/概念理解.md`) は編集 OK** だが、**常に完全 merge document として出力**すること。パッチ形式で出さない。
- v9.10 以降の確定事項は 05 (旧 05b/05c 統合済) と 06/07 に反映済み。01-04 は v9.9 時点のまま (本ファイル末尾の用語対応表で吸収)。
- 要約の質に疑問がある時は、まず原本を読み直して照合すること。要約だけで判断しないこと。
- **Taka の承認なしに勝手に書き換えない**。新規追記は OK だが、既存要約の改変は Taka の確認を取る。

---

# ===== ここから用語対応表 (古い記述を読む時の混乱防止) =====

## 0. なぜこの対応表が必要か

ESDE は v1 から v9.13 まで進化する過程で、概念の整理が何度か変わっている。古いドキュメント (01-04 や docs/概念理解.md の古い部分など) には**今は廃止された用語**や**意味が変わった用語**が含まれる。

新スレッドの AI が古い記述を読んで「観測層」「3 層構造」などをそのまま実装すると、v9.7 のような事故が起きる。本対応表はその予防のため。

---

## 1. 名称が変わった用語

| 古い用語 | 現行用語 (v9.13) | 備考 |
|---|---|---|
| 仮想層 | 存在層 (Existence Layer) | Layer 2 を指す。同じもの、名称変更のみ |
| Virtual Layer | Existence Layer | 同上 (英語表記) |
| VL | Existence Layer | コード上は `vl` のまま (略称は変えない) |

---

## 2. 廃止された / 存在しない用語

過去の Claude が誤って導入した用語。**使用禁止**。

| 廃止用語 | 状態 | なぜ廃止 |
|---|---|---|
| 観測層 | 存在しない | 過去の Claude が「観察層」「観測層」を 4 層目として勝手に導入。実際は「認知層」の機能の一部 |
| 行動層 | 存在しない | 過去の Claude が「能動層」を勝手に導入。ESDE には行動を能動的にする層はない |
| 計測層 | 存在しない | 同上の誤導入 |
| Phase 4 / Phase 5 (認知層内) | 該当なし | 認知層内の Phase 1 (φ) / Phase 2 (attention) / Phase 3 (familiarity) は存在するが、Phase 4 以降は概念化されていない |
| S≥0.20 hard threshold | 撤去済 (v9.13) | 神の手として撤去。persistence-based birth (age_r ≥ τ) に移行 |
| 経路 B (R>0 ペア即 label) | 廃止 (v9.13) | R=0 混入の原因。age_r ベースの component birth に統一 |

新スレッドで「観測層」「行動層」「計測層」が文書に出てきたら、それは**誤り**。現行の 4 層 (物理 / 存在 / 認知 / 意識) のいずれかに対応している。

---

## 3. 概念が拡張された用語

| 用語 | v9.10 以前の意味 | v9.11 以降の意味 | v9.13 での補足 |
|---|---|---|---|
| 3 層構造 | 物理 / 存在 / 認知 の 3 層整理 | 過去のスナップショット。**現在は 4 層** (意識層を含む) | — |
| 4 層構造 | 概念化されていない | 物理 / 存在 / 認知 / 意識 の 4 層 (v9.11 で確立) | v9.13 で方向性確定 |
| 認知層 | observation のみ、出力なし | observation + B_Gen + M_c + capture (v9.11 で拡張) | 「物理層を支配しない、予測して生かす」(Taka 2026-04-16) |
| 意識層 | 概念化されていない | 認知層の解釈を非介入で検証する層 (v10.x で実装予定) | 実装前提: 記憶の蓄積機構が先 |
| 介入規律 | 「認知層は物理層に書き込まない」 | 「認知層・意識層は物理層・存在層に書き込まない」 | v9.13 で再確認、v9.14 で **Layer B も audit-only (Layer A 不介入)** |
| label の魂 | frozenset 固定 | 同じ (変更なし) | — |
| cid | label 死亡で消滅 | ghost 化、TTL 経過で reaped (v9.8a で拡張) | v9.14 で Q0 = floor(B_Gen) の予算を持つ主体として拡張 |
| label の birth | S≥0.20 島 + R>0 ペア (経路 B) | 同じ | **age_r ≥ τ の connected component のみ** (v9.13) |
| CID の記憶 | 外部 dict (SubjectLayer) への蓄積構想 | 同じ | **物理層の中に既にある、読む関数が足りないだけ** (Taka 2026-04-16) |
| cid の認知活動 | 50 step pulse での一律観測 (Layer A のみ) | 同じ | v9.14 で Layer B (event 駆動) 追加。**両者は並行稼働、異なる情報を取る** |
| 共鳴 (Resonance) | ノード間 R_ij (閉路参加、Genesis) | 同じ | v9.14 で **cid 間共鳴 (E3) へ階層拡張** (Taka 2026-04-18) |
| 事象 (event) | pulse の意味での観測単位 | M_c と E_t の比較点 (v9.11) | v9.14 で **物理的な変化点 (E1/E2/E3) としても定義** |

---

## 4. v9.11 で新規導入された用語

これらは古い文書 (01-04) には出てこない:

| 新規用語 | 意味 |
|---|---|
| B_Gen (Genesis Budget) | cid 固有値 = -log10(Pbirth)。発生確率の桁数 |
| Pbirth | cid の発生確率 = (1/C(N,n)) × ρ^(n-1) × r^(n-1) × S^(n-1) |
| M_c (Memory Core) | cid の記憶ベクトル = (n_core, S_avg, r_core, phase_sig) |
| E_t (Experience) | 各 pulse 時の事象ベクトル = (n_local, s_avg_local, r_local, theta_avg_local) |
| Δ (Delta) | M_c と E_t の差分分解型一致率 |
| Capture | cid が周囲の現象を「捕まえた」結果 (TRUE/FALSE/cold_start) |
| Capture probability | P(capture) = P_MAX × exp(-λ × Δ) |
| 4 層構造 | 物理 / 存在 / 認知 / 意識 |
| Aruism | ESDE の哲学。「構造が先、意味が後」 |
| 神の手 | 設計者が外部から意味や行動を注入する設計。避けるべき |
| 二重トポロジー | ESDE のリンク構造 = 71×71 トーラス + 長距離ランダムリンク |
| 結果出したもん勝ち | Taka の研究方針。論文よりも結果優先 |
| Triad | Gemini (設計) + GPT (監査) + Claude (実装) の 3 AI 協調体制 |
| パスワード性 | cid が一意の数値で識別される性質 (Taka 表現) |
| 認知原資 | B_Gen が cid に与える「認知能力の桁数」(Taka 表現) |

---

## 5. v9.12 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| Δ i.i.d. | M_c と E_t の乖離に自己相関がない性質 (v9.12 Phase 1 で確定) |
| 並列基準原理 | 予測不能な環境に対し複数の条件付き基準を同時保持する認知テクニック (Taka 2026-04-16) |
| 構造と数式の分離統合 | 構造 (閉路、トポロジー) と数式 (確率、場) を別々に捉えて統合する設計原理 (Taka 2026-04-16) |

---

## 6. v9.13 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| age_r | 各 link の連続 R>0 step 数 (persistence カウンタ) |
| persistence-based birth | age_r ≥ τ の link で作られる connected component を label 化する方式 |
| τ (tau) | persistence 閾値。50 or 100 step |
| Step 0 audit | 本実装前に age_r 分布を測定する予備調査 (v9.13 Step 0) |
| 見かけ構造 | R=0 リンクで構成された「Genesis 原理に反する」label (v9.11 の 2/3 がこれだった) |
| 記憶の読み出し関数 | CID の物理状態を「記憶」として解釈する関数 (v9.15 以降の主題) |

---

## 6.5. v9.14 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| Layer A (Fixed Pulse) | 既存の 50 step 固定 pulse 系 (v9.11 + v9.13)。全体スナップショット・均一サンプリング装置 |
| Layer B (Shadow Ledger) | event 駆動の spend audit ledger。物理現象の変化点で発火する局所精査装置。audit-only |
| Paired Audit | Layer A と Layer B を並行稼働させる監査方式。新機構導入の運用原則 |
| Q0 (Initial Budget) | cid 初期原資 = floor(B_Gen)。cid 誕生時に確定、以後減少のみ |
| Q_remaining | 残存原資。event 発生時に spend packet で 1 減算 |
| Exhaustion | Q_remaining = 0 到達。以後 event は記録されるが spend packet は走らない (「実質的な死」) |
| Spend Packet | event 発火時に実行される最小処理単位。E_t 読み出し → Δ 計算 → virtual_* 更新 → Q -= 1 → 記録 |
| E1 (Core Link Death/Birth) | cid のメンバーリンクが alive_l から消失/復活した step で発火する event |
| E2 (Core Link R-state Change) | メンバーリンクの R が 0 境界を跨いだ step で発火する event (rise/fall)。core-local のみ |
| E3 (Familiarity Contact Onset) | 異なる 2 cid のメンバーノードが同じ alive link で接続された最初の step で発火する event |
| virtual_attention / virtual_familiarity | Layer B 専用の内部記録。Layer A のものと別メモリ、decay なし累積 |
| shadow pulse | Layer B 上の pulse 連番 (Layer A の 50 step pulse と独立) |
| contacted_pairs | 既に接触した cid ペアの集合。E3 の重複発火防止 |
| Lazy Registration | cid 登録は observe_step 初回観測時に実施 (Code A 実装判断) |
| cid 間共鳴 | E3 を Aruism 的に再概念化したもの。ノード間共鳴 R_ij の cid スケール版 (Taka 2026-04-18) |
| 上位層の足場 | 三項以上の共鳴を構築する合理的条件。v9.14 で成立、実装は棚上げ |

---

## 6.6. v9.15 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| A (研究者観察) | 研究者が CID の物理状態を数値化して記録する機構。py で state を読み CSV に書く。CID 視点ではない |
| B (CID 主体) | CID 自身が自分の構造を専用領域に展開し、必要時に読む機構。v9.15 の主題 |
| CidSelfBuffer | CID 専用メモリ領域。生誕時スナップショット + 最新 Fetch + 不一致痕跡 + divergence log。B 側 |
| 四重分離 | A/B 分離の実装担保レベル。ファイル / クラス / メモリ / 命名の 4 つ |
| Fetch (段階 1) | 50 step 固定 pulse で CID が自分の物理状態を読む動作 (`read_own_state`) |
| Fetch (段階 2) | v9.14 event 発火時に CID が自分を読む動作 (`read_on_event`)。タイミング物理事象依存 |
| Self-Divergence | 生誕時 theta_birth と現在 theta_current の L2 距離。CID の自己変化の連続量 |
| Self-Divergence Trajectory | 同クラス cid ペアの自己認識乖離の時系列 (Gemini 提案、v9.15 多様性指標) |
| any_mismatch_ever | CID が一度でも生誕時と不一致を持ったかを示す bool。遺伝子情報的な初期値変化検出 (段階 2) |
| Match Ratio | node/link 一致率の集約指標。段階 1 で全 0 張り付き、段階 2 で廃止 |
| Y (選択肢) | CID は構造体、差分のみ知覚。Aruism 的に段階 1 で採用 |
| Z (選択肢) | 「見る」操作が確率的、失敗を含む。段階 1-2 を繋ぐ中核原理 |
| ζ (zeta) | 補完しない。見えなかった部分は欠損のまま保持。段階 1 で採用 |
| 研究者主観の封印 | 段階 2 で成立した構造。研究者が CID の自己読みタイミングを予測できない |
| サイコロの比喩 | Taka 核心発見 (2026-04-20)。研究者は統計的、サイコロ自身は具体的に語れる非対称性 |
| 哲学以上科学未満 | Taka の立場。「○○かもしれない」の反証困難性を利用した主張。「自己がある」と「ない」の中間で戦う |
| 奇妙なバランス | 覗ける弱点を予測不能性で埋める、v9.15 主張の論理構造 |
| 段階 1 / 段階 2 / 段階 3 | v9.15 の実装段階区分。v9.16 = 段階 3 (確率的 Fetch 失敗) |

---

## 6.7. v9.16 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| age_factor | Q_remaining / Q0。cid の時間的な「若さ」を表す [0, 1] の比率。生誕直後 1.0、Q 枯渇で 0.0 |
| n_observed | event 発火時に実際に判定されるノード数 = round(n_core × age_factor) |
| サンプリング方式 | age_factor に比例した数のノードを確率的に選んで判定する方式 (v9.16 段階 3 採用、2 AI 統合判断) |
| 観察サンプリング | v9.16 段階 3 の機構名。Fetch 全体は成功するが、判定の粒度が時間的に変化 |
| missing (3 値の 1 つ) | 観察対象から外れたノードの状態。match/mismatch と並ぶ段階 3 の 3 値の 1 つ。欠損として扱われる (ζ) |
| 独自 RNG (hash ベース) | engine.rng を touch しない、hash ベースの局所乱数源。seed × cid_id × step × event_type で決定論的 |
| 明示 event_type マップ | _EVENT_TYPE_HASH のように event 種別を明示的な int にマップ。PYTHONHASHSEED 非依存のため (Code A 判断) |
| Q 枯渇 cid | age_factor_final = 0 に到達した cid。v9.16 実測で fetched cid の 34.26 % |
| theta_diff_norm_all | 全ノードで計算した theta 差分 L2 ノルム。段階 2 の theta_diff_norm と同じ計算 |
| theta_diff_norm_observed | 観察ノードのみで計算した theta 差分 L2 ノルム (段階 3 新規、論点 Z-c で両方記録) |
| observation_log | 段階 3 新規出力 CSV。各 event 発火時のサンプリング記録 (cid_id, step, age_factor, n_observed, observed_indices, match/mismatch/missing count) |
| 先走り防止チェックポイント | GPT §12 提案の 3 項目。バージョン名決定時に詰める |
| 一文定義 | v9.16 指示書 §0.2 で導入。バージョンの入出力を一文で書く先走り防止装置 |
| 説明可能性仮説 | Taka 2026-04-21。現在 → 過去/未来 の 2 方向に説明可能性が減衰する時間構造 |
| 動的均衡の違和感 | 認知量消費 -1 固定の課題。物理スケール変動化の段階で再検討 (Taka 2026-04-21) |

---

## 7. v9.10 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| Pulse | window から切り離された cid の観測タイミング |
| PULSE_INTERVAL | 50 step 固定 |
| MAD-DT | Mean Absolute Delta — Dynamic Threshold、cid 履歴ベース動的閾値 |
| R (主観的驚き指数) | R = Δx / (theta + epsilon) |
| Cold Start | Pulse 1〜3 回目、unformed として扱う |
| K (履歴長) | 各 cid が保持する直近 pulse 数、20 固定 |
| MAD | Mean Absolute Deviation、平均絶対偏差 |
| Tag (Normal / Major) | gain_xxx, loss_xxx の発火条件区分 |

---

## 8. v9.8 系で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| cid (cognitive id) | label とは独立した観察主体の識別子 (v9.8a) |
| ghost | host (label) を失った cid の状態 |
| hosted | label に紐付いている cid の状態 |
| reaped | TTL 経過で消滅した cid |
| GHOST_TTL | ghost 状態の最大持続時間 = 10 windows |
| disposition | cid のキャラクター 4 軸 (social, stability, spread, familiarity) |
| Introspection | window 間の disposition 変化からタグ生成 (v9.8b) |
| gain_xxx / loss_xxx | introspection tag |
| death_pool | 死亡 label の情報プール (v9.8c) |
| Information Pickup | ghost cid が death_pool から情報を拾得 (v9.8c) |
| TTL_BONUS | pickup 成功で ghost TTL が延長される量 |

---

## 9. 認知層内の Phase 区分 (v9.5 以降)

これは「層」ではなく、認知層**内部**の機能区分。

| Phase | 機能 | 状態 |
|---|---|---|
| Phase 1 | 認知位相 φ | 完了 (v9.5) |
| Phase 1.5 | convergence/divergence 対称分析 | 完了 (v9.5) |
| Phase 2 | Attention Map | 完了 (v9.5) |
| Phase 3 | Partner Familiarity | 完了 (v9.6+) |
| Phase 4 以降 | **存在しない** | 過去の Claude が誤って参照することがあるが、定義されていない |

---

## 10. 層と Phase の混同に注意

「Phase 1」「Phase 2」は**認知層内部の機能区分**。
「Layer 1」「Layer 2」は**4 層構造の階層**。
**全くの別概念**。混同すると設計を誤る。

| 表記 | 意味 |
|---|---|
| Layer 1 | 物理層 |
| Layer 2 | 存在層 |
| Layer 3 | 認知層 |
| Layer 4 | 意識層 (v10.x 予定) |
| Phase 1 (認知層内) | φ |
| Phase 2 (認知層内) | Attention |
| Phase 3 (認知層内) | Familiarity |

---

## 11. Phase / フェーズの別の用法 (バージョン区分)

ESDE のバージョン進行も「phase」と呼ばれる:

| Phase 名 | バージョン範囲 | 状態 |
|---|---|---|
| Genesis | v1 - v6 | 完了 |
| Ecology | v7 | 完了 |
| Cognition | v8.0 - v8.7 (旧称) | 完了 |
| Autonomy | v8.8 - v9.0 (旧称) | 完了 |
| Primitive | v9.1 - v9.14 | **v9.14 完了** |
| 記憶の読み出し | v9.15 | 次 |
| 記憶の蓄積と再生 | v10.x | 構想 |
| 三項以上の上位層 | v10.x 以降 | v9.14 で条件成立、実装棚上げ |
| 意識層 | v10.x 以降 | 構想 |
| 外部コネクター | v11.x 以降 | 構想 |
| Language | 未着手 | 構想のみ |

「Phase 1」「Phase 2」と「Genesis Phase」「Cognition Phase」と「Layer 1」「Layer 2」は**全部別概念**。文脈で判断する必要がある。

---

## 12. 廃止 / 無効化された機能 (コードは残存)

| 機能 | 状態 | 復活させてはいけない理由 |
|---|---|---|
| Stress Decay | OFF | 二重平衡干渉の原因、v9.3+ で無効化 |
| Compression → MacroNode | OFF | 過剰な構造圧縮、v9.x で無効化 |
| Torque Factor (v9.7) | =1.0 (実質 OFF) | v9.7 失敗の原因、認知層から θ への介入 |
| 認知層の Pulse Interval 変調 | 未採用 | 「行動を命令する」設計、神の手、capture probability で代替 |
| 認知層から θ への介入 | 禁止 | v9.7 失敗の根本原因、B_Gen で必要性消滅、v9.13 で方向性として再確認 |
| 固定閾値 (v9.8b) | 廃止 | 4 軸不整合、v9.10 MAD-DT で動的化 |
| S≥0.20 hard threshold | 撤去 (v9.13) | 神の手。persistence-based birth で代替 |
| 経路 B (R>0 ペア即 label) | 廃止 (v9.13) | R=0 混入の原因。age_r ベースに統一 |

新スレッドの AI が「これを再導入すれば改善する」と提案しても、**全部過去に試して却下されている**。

### 休眠保持されているもの (削除しない)

| 機能 | 状態 | 理由 |
|---|---|---|
| pickup (v9.8c) | 動作中、効果薄 | 「CID が他者の経験を取り込む」フレームワーク、将来活用候補 (Taka 原則「無駄だから切る」禁止) |
| Semantic gravity + deviation | deviation_enabled=True | v9.14 以降で検証予定、v9.15 でも継続 |
| v99_ 内的基準軸 | 計算走行中、CSV 出力中 | — |
| Layer A (50 step 固定 pulse) | 稼働中、Layer B と並行 | v9.14 時点では観測機械として残置。「パルスとは何か」の再定義は v9.15 以降 (Taka 2026-04-18) |
| E3 variant 候補 (phase 近接/持続/多重) | 議論のみ、実装なし | v9.14 では現在の E3 (物理接触の初回性) を維持。変種は v9.15 以降の検討候補 |

---

## 13. 重要な発言・コンセプト (Taka 由来)

文書を読む時、これらの表現が出てきたら Taka 由来:

| 表現 | 意味 |
|---|---|
| 結果出したもん勝ち | 論文より結果。null result も valid |
| 神の手なし | 設計者が意味や行動を注入しない |
| 構造が先、意味が後 | Aruism の核 |
| パスワード | cid の一意性 (B_Gen) |
| 認知原資 | B_Gen が与える計算能力の桁数 |
| 桁違いの個体差 | n_core で B_Gen が桁単位で違う |
| 事象 = 周囲の現象そのもの | E_t の定義、外部ラベルではない |
| 誤差の埋め合わせ | 認知層の概念化機能 (v9.12+) |
| 埋め合わせの検証 | 意識層の機能 (v10.x) |
| 投資としての ESDE | 結果出ないなら撤退ありうる |
| アメーバの世界 | 単純な cid の認知 (n=2 など) |
| 人間の世界 | 複雑な cid の認知 (n=5 以上) |
| 物理現象として注入 | 外部コネクターの設計原則 |
| frozenset として消えていく | 注入物は cid 化せず消える |
| AI の誤読が測定器 | Triad のズレが直感の言語化に役立つ |
| 数より純度 | v9.13 S≥0.20 撤去時の Taka 判断 |
| 健康管理の比喩 | 認知層の効果は統計的に多少の差、劇的ではない (v9.13) |
| 無駄だから切るは無駄な発想 | 機能を削除せず活かし方を考える (v9.13) |
| 記憶は物理層の中に既にある | 外部 dict ではなく物理状態そのもの (v9.13) |
| cid 間の共鳴 | E3 contact を node 間共鳴 R_ij の cid スケール版として解釈 (v9.14) |
| 実質 2 消費 | E3 発火時に両 cid が 1 spend ずつ = Aruism の存在の対称性 (v9.14) |
| 上位層の足場 | 三項以上の共鳴を構築する合理的条件が揃った = v9.14 の真の達成 (v9.14) |
| 一段上の接続は次のテーマ | 三項共鳴実装は棚上げ、認知層継続を優先 (v9.14) |
| パルスとは何か | Layer A (50 step 固定) の再定義は v9.15 以降の宿題 (v9.14) |
| A と B の混同 | 研究者観察 (A) と CID 主体 (B) を混ぜない、v9.15 の最大の転換 (Taka 2026-04-18) |
| 帳簿の裏の仕事 | 覗けない作業で自律性を示す比喩、v9.15 の主題の原型 (Taka 2026-04-18) |
| 差分が見えないけどおそらくこうだ | 認知層で最大のポイント、段階 3 以降の検討 (Taka 2026-04-18) |
| Step 単位固定は研究者視点 | 主観性の最小条件はタイミングの予測不能性 (Taka 2026-04-20) |
| イベントにくっつける | v9.14 の event 機構を段階 2 Fetch トリガーに再利用 (Taka 2026-04-20) |
| サイコロの比喩 | 研究者は「1/6」サイコロは「1 だ」と語れる非対称性、v9.15 核心 (Taka 2026-04-20) |
| ランダム性が論理の支柱 | 削る方向は採らない、予測不能性を担保にした主張の戦略 (Taka 2026-04-20) |
| 奇妙なバランス | 覗ける弱点を予測不能性で埋める、哲学以上科学未満の位置 (Taka 2026-04-20) |
| 哲学以上科学未満 | Taka の立場、「使える論拠」のレンジで主張する (Taka 2026-04-20) |
| 機械的な自分語りは自己ではない | ランダム性を担保した主張のみ自己の候補、「それっぽさ」は市場承認 (Taka 2026-04-20) |
| ノード固定は実験制御 | 神の手ではない、物理層クローズだからこそ認知層を追跡できる (Taka 2026-04-20) |
| 反省は繰り返しても改善しない | だから GPT 使ってる、Claude の癖は前提にする運用 (Taka 2026-04-20) |
| Fetch の確率的失敗ってどういう意味? | Taka 問い直し、詰まっていないバージョン名の中身を詰めさせる (2026-04-21) |
| 手っ取り早いのは B_Gen | v9.16 主題の起点、判定基準に B_Gen/Q を使う構想 (Taka 2026-04-21) |
| 人間の比喩 (構造 vs 時間) | B_Gen = 種の違い、Q_remaining = 年齢の違いの 2 段階認識 (Taka 2026-04-21) |
| 言い訳っぽいなぁと思いつつも | B_Gen を判定基準に使うのは確率ベース設計の延長、神の手ではない自答 (Taka 2026-04-21) |
| 確率を元に構造化することまで否定してはいない | Taka の許容範囲、v9.16 設計の根拠 (2026-04-21) |
| 現在 → 過去/未来 の説明可能性減衰 | Taka 時間構造仮説、未来の定義候補 (2026-04-21) |
| 説明可能性は not decide, but describe と同格 | 3 AI 共通の運用原則として Taka 指定 (2026-04-21) |
| 過去は時間経過で広がる | 説明可能性減衰の傍証、Taka 時間仮説の核 (2026-04-21) |
| 動的均衡が重要になるのは物理スケール扱う時 | 現在は CID 主体が主題、消費 -1 固定で OK (Taka 2026-04-21) |
| 物理はクローズしたからこそ現状の進化がある | 実験制御の意義、神の手との区別 (Taka 2026-04-21) |
| 先のプロジェクトでやることってアバウトで始まるのは仕方ない | 標語でも足場になる、雑でいい場面の認識 (Taka 2026-04-21) |

---

## 14. 誤った推論を避けるためのチェックリスト

新スレッドの AI が ESDE を理解する時、以下を確認:

- [ ] 4 層構造の介入規律を理解した (物理 ← 存在のみ介入、認知・意識は介入しない)
- [ ] B_Gen が capture の直接入力ではない (M_c 経由)
- [ ] M_c は 4 要素固定 (拡張禁止 v9.11 段階)
- [ ] phase は circular distance で扱う
- [ ] similarity はコサイン類似度ではなく差分分解型
- [ ] 「観測層」「行動層」「計測層」は存在しない
- [ ] Phase (層内機能) と Phase (バージョン区分) と Layer (層) を混同しない
- [ ] 「3 層構造」は古い、現在は 4 層
- [ ] 「仮想層」と「存在層」は同じもの (名称変更)
- [ ] 廃止された機能 (Stress, Compression, Torque Factor, 固定閾値, S≥0.20, 経路 B) を復活させない
- [ ] 認知層から θ への介入は絶対にやらない (v9.7 失敗、v9.13 再確認)
- [ ] PI 変調はやらない (PULSE_INTERVAL=50 固定)
- [ ] 並列化必須、sequential 禁止
- [ ] Claude Code A/B 分担、チェック依頼書必須
- [ ] **v9.11 の所見を引用する際、S≥0.20 + 経路 B アーティファクトの影響を受けていないか確認する** (v9.13 で多くが再解釈された)
- [ ] **認知層の効果を「劇的」に設計しようとしていないか** (統計的に多少の差が Taka 方針)
- [ ] **「無駄だから切る」と判断していないか** (休眠保持が原則)
- [ ] **AI 間文書を英語で書いていないか** (日本語 md 統一、2026-04-16 撤回済)
- [ ] **Layer A (50 step 固定 pulse) を触っていないか** (v9.14 paired audit 原則、bit-identity 必須)
- [ ] **新機構を runtime 主体置換として導入していないか** (v9.14 paired audit で先行、promotion は analysis 後)
- [ ] **E3 を拡張していないか** (現状は物理接触の初回性のみ、variant 候補は v9.15 以降の検討)
- [ ] **三項共鳴の実装に先走っていないか** (v9.14 で足場、実装は棚上げ、認知層継続を優先)
- [ ] **seed 構成を認識しているか** (v9.15 から 24 seeds × -j24、Short+Long 2 重構成は廃止)
- [ ] **A と B を混同していないか** (研究者観察と CID 主体は別領域、v9.15 最大の規律)
- [ ] **研究者向け統計量を CID 内部に持たせていないか** (mean/std 等は A 側、CID 内部には生の配列のみ)
- [ ] **A/B 分離が四重 (ファイル / クラス / メモリ / 命名) で担保されているか**
- [ ] **Fetch の発動タイミングを理解しているか** (段階 1=50 step 固定、段階 2=event 駆動、段階 3=確率的失敗)
- [ ] **「自己」「意識」を結果レポートで断定的に使っていないか** (Describe 規律、GPT 監査指摘)
- [ ] **「○○を知る」と書いていないか** (段階 1-2 では「不一致を持つ」止まり、GPT 監査抑制)
- [ ] **集約指標を安易に追加していないか** (「何のために取るか」を CID 視点で詰める、Match Ratio 失敗の教訓)
- [ ] **発生頻度の違う event を比率比較していないか** (構造的情報は出ない、Taka 指摘)
- [ ] **観察結果を条件から切り離して普遍化していないか** (「活発な系」ではなく「5000 ノード 71x71 ではこうなった」)
- [ ] **推測を結論と書いていないか** (「系が安定」ではなく「安定を示唆する可能性」)
- [ ] **ランダム性を削る方向に設計していないか** (v9.15 以降、論理の支柱を守る)
- [ ] **v9.16 の age_factor 計算式 (Q_remaining / Q0) を変えていないか** (2 AI 統合判断で確定)
- [ ] **サンプリング方式 (案 1) 以外の実装 (tolerance 可変、確率判定) を導入していないか** (却下済)
- [ ] **B_Gen を自己読みで直接参照していないか** (間接使用のみ、age_factor 経由)
- [ ] **observation のタイミングを event 駆動以外にしていないか** (50 step 駆動は v9.15 段階 2 で廃止済)
- [ ] **Fetch コストを 0 から変えていないか** (v9.14 以降、基準値 0 を維持)
- [ ] **missing を any_mismatch_ever のカウントに含めていないか** (段階 3 禁止事項)
- [ ] **age_factor 区間別 missing 比率の単調関係を「観察」と書いていないか** (代数的必然、仕様の帰結)
- [ ] **バージョン名を決めた時点で入出力を一文で言えるか詰めているか** (GPT §12 先走り防止)
- [ ] **「失敗」「認識」「自己」等の語を物理操作へ還元しているか** (詰まっていない名前を前提にしない)
- [ ] **Constitution (2026-03-05) §2/§3/§5/§7/§9 との整合をチェックしたか** (新規原則を立てる前に既存憲法を確認)
- [ ] **説明可能性原則を Describe 原則と同格に扱っているか** (Taka 2026-04-21 指定、3 AI 共通)

---

## 15. 何か矛盾を見つけたら

新スレッドの AI が文書間の矛盾を見つけた場合:

1. **本ファイルの用語対応表を確認**: 用語の対応で解消するか
2. **`07_esde_system_structure.md` を確認**: これが現行の真実
3. **`05_primitive_summary.md` の v9.14 セクション を確認**: v9.14 での前提変更を確認
4. **解消しない場合**: Taka に質問する。**推測で実装に進まない**

過去のドキュメント (01-04, および 06 の古い部分) には「3 層構造」「仮想層」「観測層」「n=2 主体」「phase+r 支配」などが残っている。これらは古い表記や v9.11 以前のアーティファクトを含む記述であり、実装の判断基準としてはいけない。

---

## 16. 文書の優先度サマリ

文書を読む時間が限られている AI 向け:

**最優先 (必読、実装の判断基準)**
- 本ファイル (00_index.md): ナビゲーション + 用語対応表
- `07_esde_system_structure.md`: 現行システム構造 (v9.14 対応)
- `05_primitive_summary.md`: Primitive phase 全体 (v9.14 対応)。特に **v9.14 セクション (Paired Audit、E3 = cid 間共鳴、上位層の足場)**、**v9.13 セクション (persistence-based birth、認知層方向性)**、**v9.12 セクション (Δ i.i.d.、phase+r 原因)** は必読

**次優先 (文脈理解)**
- `06_concept_core.md`: Taka 哲学コア (v9.14 対応)

**次優先 (失敗の記録、必ず時間を作って読む)**
- `04_cognition_summary.md`: v3-v7 の試行錯誤、「物理層は床」結論、特に v3.4 tripartite loop の持続性問題 (bridge_max_life=1) は v9.14 以降の三項共鳴検討の前提

**参考 (背景理解)**
- `01_genesis_summary.md` 〜 `03_autonomy_summary.md`: 過去の phase 概要

**実装時参照**
- `primitive/v914/v914_probabilistic_expenditure.py`: v9.14 本体 (v9.13 を丸ごとコピーして add-only で Layer B を実装)
- `primitive/v914/v914_spend_audit_ledger.py`: Layer B 核心 class
- `primitive/v914/v914_event_emitter.py`: E1/E2/E3 検知ロジック
- `primitive/v914/v914_implementation_notes.md`: Code A 実装ノート (lazy registration 等の判断記録)
- `primitive/v914/v914_audit_result_milestone1.md`: Phase 1 audit レポート
- `primitive/v914/v914_phase2_instruction.md`: Phase 2 依頼書
- `primitive/v914/v914_event_type_efficiency.md` (§6.1)
- `primitive/v914/v914_ncore_efficiency.md` (§6.2)
- `primitive/v914/v914_shadow_overlap.md` (§6.3)
- `primitive/v914/v914_e3_ablation_result.md` (§6.4)
- `primitive/v913/v913_persistence_audit.py`: v9.13 本体 (v9.14 の親)
- `primitive/v911/v911_cognitive_capture.py`: v9.11 cognitive capture 実装 (v9.14 が基底として継承)
- `primitive/v911/v911_capture_param_audit.md`: v9.11 パラメータ決定根拠
- `docs/概念理解.md`: Taka 用あんちょこ (v9.14 対応予定)
- `docs/ESDE_Primitive_Report.md`: Primitive phase 全体レポート (v9.14 対応予定)
