# ESDE 研究史 — AI 向け超要約 (Index + 用語対応表)

*作成日*: 2026-04-11 (v9.9 Long Run 進行中)
*更新*: 2026-07-01 (**v1303 注意センター統合クローズ（注意の入力側の確立）+ v1304 開始。emitter→selector→attention output schema を細かいサブブランチ a-Final で確立、正式 eye 4+補助1・本体=per-t 選択確率。方法論の落とし穴2件を実証（single-draw は chance 支配・marginal は平均化の罠）→ distinct 性は per-t 分布で見る。次は v1304 child-ESDE projection。進化史=`unified/v1303/v1303_evolution.md`、詳細=`07_unified_summary.md` Part 5 / `08_concept_core.md` D.99 / 教訓 438-441 = 概念理解.md、§18.23 新設**)
*前回更新*: 2026-06-25 (**ai_summaries 統合: 枝番 06b/06c を 06 に、07 の追補 4 本を 07 に、全文保存（書き換えなし）で Part 連結により一本化。分岐ファイルは削除。番号体系は 1 番号 = 1 ファイルに復帰**)
*前回更新*: 2026-06-21 (**v13 child-world: CID 誕生形態→物理 param の子系。統計監査で `real≒shuffle` の真因＝比較統計 (署名 mean/std) が cid→param→署名の pairing を構造上見ないこと (pairing 検定なら K_sync→sync_order・plb→link/label_density が両 ratio p<0.005) を確定、写像は K_sync 100%/θ 84% 伝達＝入口で潰してない、像が保持して見えた相関の多くは run 長交絡。次は全検だが CID 値 ~5-14 独立軸・物理 param ~6-7 独立軸ゆえ「全部繋ぐ」は冗長、選定合理性を 3AI 合議で詰める。詳細 = `07_unified_summary.md` Part 4、現況 = `docs/現在の方向_childworld全検.md`、教訓 434-437 = 概念理解.md**)
*前回更新*: 2026-06-05 (**v1105/v1109b → 注意センター ESDE 転換 → v1110-v1113 4 連続失敗 → v1114 Step 1 内部注意生成成立、観察対象の規律 (同じ系内 vs 異なる系) + Code A 循環構造の認識 + Center ESDE Taka 定義、§18.20 + §18.21 新設**)
*前々回更新*: 2026-05-23 (**Unified Phase v1104 + v1104a 完了反映、4 つの非対称性 #L30-L33 確定、v1105/v1105a 主題確定、観察方法を疑う規律確立**)
*前回更新*: 2026-05-11 (Developmental v10.3-v10.12 完了反映、Phase 1.5 第七試行完了、Atom 取り込み prototype 主題完了)
*対象読者*: ESDE-Research に新規に関わる Claude (新スレッド初見)

---

## このディレクトリの目的

ESDE 研究の各フェーズ (Genesis / Ecology / Autonomy / Cognition / Primitive / **Developmental**) と哲学的コア (概念理解) を、未来の Claude が **context に乗せても暴走しない最小サイズ** に圧縮したもの。

各原本 (200-2400 行) の要点だけを抽出し、却下された方針 (失敗の記録) を必ず残してある。**未来の Claude が同じ失敗を繰り返さないため**。

---

## ⚠️ 警告

- これは**要約**であり原本ではない。設計の詳細や個別実験の数値が必要な場合は必ず原本 (`docs/ESDE_*_Report.md` および `docs/概念理解.md`) を参照すること。
- **要約の最新時点は v11.0.4a (v1104a) 完了 (2026-05-23)、Unified Phase 第六主題「CID/IID 内部動作点検 段階 2」完了**。07_unified_summary は v10.13.a + v1100/v1101/v1101a/v1102/v1103/v1104/v1104a を網羅 (Unified Phase の正式要約)。06_developmental_summary、10_audit_principles、ESDE_Developmental_Report は v10.12 対応済み。08_concept_core、09_esde_system_structure は v10.9 まで本格対応、v10.10-v10.12 + v1104+v1104a は §末追記。05_primitive_summary は Primitive フェイズで凍結 (v9.x 系列、参照用)。01-04 は v9.9 時点のまま (古い表記、用語対応表で確認)。
- **Developmental フェイズのディレクトリ**: `developmental/v10X/`。**Unified フェイズのディレクトリ**: `unified/v11XX/`。
- **ファイル番号体系の変更 (2026-04-28)**: Developmental フェイズ追加に伴い、06 (旧 concept_core) → 07、07 (旧 system_structure) → 08、08 (旧 audit_principles) → 09 にずらし、新規 06 を Developmental Summary とした。
- **ファイル番号体系の変更 (2026-05-18)**: Unified フェイズ独立に伴い、07 (旧 concept_core) → 08、08 (旧 system_structure) → 09、09 (旧 audit_principles) → 10、10 (旧 language_summary) → 11 にずらし、新規 07 を Unified Phase Summary とした。06/06b/06c は Developmental Phase 要約として据え置き・凍結。Unified Phase の新主題は 07 に追記して一本化する (06d/06e の枝番継続はしない)。
- **枝番・追補の一本化 (2026-06-25)**: 06b/06c を `06_developmental_summary.md` に Part A/B/C として、07 の追補 4 本 (v1105 転換 / 注意センター内部 / v12-v12.1 ルーレット / v13 child-world) を `07_unified_summary.md` に Part 0-4 として、いずれも**全文保存（書き換えなし）で連結統合し分岐ファイルを削除**。以後 06/07 は 1 番号 = 1 ファイル。新主題は各本体に Part 追記する（枝番・addendum ファイルを作らない）。
- **推測補完していない**。原本にあることだけ抽出している。「書いてないこと」を埋めようとしないこと。
- 概念理解.md からの引用は **必ず引用形式 (>) で残してある**。Taka の発言を勝手に言い換えないこと。

---

## 推奨読書順序 (v11.0.4a 時点)

```
00_index.md (このファイル)
  ↓ ★末尾の「用語対応表」を必ず最初に読む
08_concept_core.md      ← 哲学コア + Developmental 概念 (旧 07)
  ↓
01_genesis_summary.md   ← 物理層 (床) の確立 (古い表記あり)
  ↓
02_ecology_summary.md   ← observer 複数性 (古い表記あり)
  ↓
03_autonomy_summary.md  ← label 自律性、5-node 転換点 (古い表記あり)
  ↓
04_cognition_summary.md ← ★ 失敗の記録 (最重要、古い表記あり)
  ↓
05_primitive_summary.md ← Primitive phase 全体 (v9.0-v9.18、Primitive 凍結)
05c_primitive_summary_v913_addendum.md ← v9.13 追補
  ↓
06_developmental_summary.md ← ★ Developmental phase 統合 (Part A: v10.0-v10.3 / Part B: v10.4-v10.12 Phase 1.5 / Part C: v10.13a + v1100/v1101、凍結)
  ↓
07_unified_summary.md ← ★ Unified Phase 正式要約 統合 (Part 0: v10.13a-v1104a / Part 1: 注意センター転換 / Part 2: 内部注意生成 / Part 3: v12-v12.1 / Part 4: v13 child-world、最新、新主題はここに Part 追記)
  ↓
09_esde_system_structure.md ← 現行システム構造 (旧 08、v10.6 対応、4 層 + α/β Integration + Salience + Leakage + Atom alignment)
  ↓
10_audit_principles.md ← 監査原則 (旧 09、v10.6 対応、α/β 階層分離、5 者運用、ベースライン比較必須)
  ↓
11_esde_language_summary.md ← ESDE Language 系要約 (旧 10)
```

**急ぎなら**: 本ファイル末尾の **用語対応表** + `07_unified_summary.md` + `09_esde_system_structure.md` + `08_concept_core.md` の Developmental 申し送り + v1104+v1104a 関連資料 (`v1104_v1104a_phase_result.md` / `esde_unified_inventory.md`) の組み合わせで現状作業 (v11.0.4a 時点) に最低限着手できる。**ただし `04_cognition_summary.md` の「却下された方針」は時間を作って必ず読むこと**。

**現主題 (v11.0.4a = v1104a、2026-05-23 時点)**: 「CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検」完了。`07_unified_summary.md` §7B-§7D で v1104+v1104a 全容と v1105/v1105a 主題方向を網羅。Code A Step A-G (v1104) + Step H 初版 + Step H-3 + Step H-4 + Step A'-G' (v1104a) 完了、bit-identity 全 PASS (1,502 frozen files、v1104 13 含む)、4 つの非対称性 #L30-L33 確定、v1104+v1104a 統合 Phase Result 完成。次主題は v1105 (段 4-b/4-c 対称統合点検、役割表まで進める、問いの形 A) + v1105a (役割表を使って応答候補絞り込み試行、問いの形 B、v1101 以来初の試行切替)。新 Web Claude 引き継ぎは `07_unified_summary.md` を最初に読むこと。

---

## ファイル一覧

| # | ファイル | 原本 | 内容 | 更新状況 |
|---|---|---|---|---|
| 00 | `00_index.md` | (このファイル) | ナビゲーション + 用語対応表 | **v11.0.1.a 対応** |
| 01 | `01_genesis_summary.md` | ESDE_Genesis_Report.md (638 行) | 物理層の確立、5 Forces、観察者 k\*=4、N=10000 まで scale 不変 | v9.9 時点 (古い表記あり) |
| 02 | `02_ecology_summary.md` | ESDE_Ecology_Report.md (242 行) | observer 複数性、global は lossy compression、long_drift がデフォルト | v9.9 時点 |
| 03 | `03_autonomy_summary.md` | ESDE_Autonomy_Report.md (749 行) | label = 魂 (frozenset)、territory = 場、5-node 転換点、Lifecycle Instrumentation | v9.9 時点 |
| 04 | `04_cognition_summary.md` | ESDE_Cognition_Report_Final.md (1271 行) | **★最重要・最複雑**。v3-v7 の試行錯誤、「物理層は床」結論、virtual layer の確立 | v9.9 時点 |
| 05 | `05_primitive_summary.md` | ESDE_Primitive_Report.md | Primitive phase 全体 (v9.0-v9.18) | **v9.18 対応** |
| 06 | `06_developmental_summary.md` | ESDE_Developmental_Report.md | **Developmental phase 統合** (Part A: v10.0-v10.3 / Part B: v10.4-v10.12 Phase 1.5 / Part C: v10.13a + v1100/v1101)。旧 06b/06c を全文保存で統合 | **凍結** (Developmental Phase 完結) |
| **07** | `07_unified_summary.md` | (要約のみ) | **Unified Phase 正式要約 統合** (Part 0: v10.13a-v1104a / Part 1: 注意センター転換 / Part 2: 内部注意生成 / Part 3: v12-v12.1 / Part 4: v13 child-world)。旧 addendum 4 本を全文保存で統合。新主題はここに Part 追記 | **最新** |
| 08 | `08_concept_core.md` | 概念理解.md | Aruism、4 層構造、絶対ルール、Taka 発言、戦国大名モデル、v9.13-v10.12 各概念 (旧 07_concept_core) | v9.18 + v10.x §末追記 |
| 09 | `09_esde_system_structure.md` | (要約のみ) | ESDE 現行システム構造、4 層 + α/β Integration + Salience + Leakage + Atom alignment (旧 08_esde_system_structure) | v10.6 対応 |
| 10 | `10_audit_principles.md` | GPT 監査運用指針 v1 (2026-04-23) | 監査の基本姿勢、読者別方針、3 役分離、5 者運用、ベースライン比較必須 (旧 09_audit_principles) | v10.6 対応 |
| 11 | `11_esde_language_summary.md` | (要約のみ、Code A 2026-05-13) | ESDE Language 系 (Atom/Synapse/Phase 7-10) 要約 (旧 10_esde_language_summary) | Language 系凍結時点 |

---

## 最小限知っておくべき項目 (v10.6 対応)

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

### v9.17 で確定した重要事項 (2026-04-23)

63. **段階 4 = 他者読み + 接触体記録** — CID が他 cid の情報を読む機構 (下層) と、接触体 (frozenset) を記録する外部器 (上層) の並行実装。候補 III (Gemini/GPT 統合推奨)。
64. **他者読み仕様 = α + E3_contact + other_records + 相手 age_factor サンプリング** — 相手の M_c features (不変値) のみ取得。state (動的値) は取得しない (β/γ 禁止)。
65. **接触体 (X) は状態なし・動態なし・機能なし** — 成立記録のみ (Taka 5 点判断の 2)。持続/消滅/再成立の定義は v9.17 では与えない。動態が見えてから v10.0 繰り上げ検討。
66. **InteractionLog は A 側外部器** — CID からは参照されない、書き込まれない (コインの裏表、責務分離)。AST テストで構造的に担保。
67. **CidView dataclass** — cid-as-int と spec-level cid-as-object のギャップを吸収 (Code A 提案 Q1)。B 側に配置、read-only。
68. **canonical ordering dedup** — observer_cid < partner_cid のときだけ InteractionLog に記録。pair 単位の一意性を保証 (Code A 提案 Q3)。
69. **visible_ratio = other.Q_remaining / other.Q0** — 他者読みのサンプリング比率。自分の age_factor ではなく相手の age_factor を使う (候補 q、Gemini 推奨)。Taka 発見 2 (消費 → 概念形成 → 穴埋め) の直接実装。
70. **物理層は変えない** — v5-v7 の「取り込む」失敗を回避。認知層 / 記録層の追加のみ。4 段階連続で theta_diff_norm_all max 差 0.0 (物理計算完全不変)。
71. **CID は X を知らない** (コインの裏表) — CID は自己の other_records のみ保持、InteractionLog は外部観察器。Gemini/GPT 共通推奨。
72. **Layer B 片方向発火は v9.14 仕様** — _node_to_cids は retire 時も削除されない設計 (L87-89)。event 発火ゲートは「observer が今 hosted AND ledger 登録済み」(L203-206)。main tracking 50 で 77% が片方向発火。bug ではない。
73. **E3 自体が主要な Q 消費経路** — E3 の spend 成立率 41.8% (58% は Q=0 cid に発火して空振り)。E3 の spend 成立数 41,977 = 全消費の 67%。
74. **摂食行動の比喩** (Taka 2026-04-23) — 片方向 E3 接触を摂食行動として読む。ESDE 内部に価値判断を持ち込まない、神の手を入れない設計が自発的に人間経験に対応した観察。
75. **意識の原資仮説** (Taka 2026-04-23) — Q 消費 = 認知の増加 = 意識の原資。後付けの前提として置くことで新しい発見が生まれる (Taka 方法論)。
76. **アリズム原理の再確認** (Taka 2026-04-23) — ない は ある の上に立つ存在の形式の一つ、本当のない は不可知。ESDE 内部で「他者がない」「接触がない」と観察されることも、一つの存在形式として記録可能。
77. **GPT 監査運用指針 v1 導入** (2026-04-23) — 3 役分離の GPT 役割を精密化 = 切り分けと翻訳、制動ではない。Claude の資料作成時の自己規律としても機能。`08_audit_principles.md` (現 `10_audit_principles.md`) に AI Summaries 形式で統合、原本は独立保存。
78. **比喩ラベリング運用** (GPT 指針 §9) — 新しい Taka 比喩が出るたびに資料末尾に簡易記録。一覧表は作らず、資料ごと軽量に。Taka 向けは比喩保持、AI 向けは操作語化、Summary は併記方式。
79. **v10.0 繰り上げは折衷案** — v9.17 完了時点では繰り上げず、次主題決定時に判断。Taka 哲学「構造が先、定義は後」との整合。

### v9.18 で確定した重要事項 (2026-04-24)

80. **段階 5 = A + C 統合** — A (差分予測) と C (意識の原資) の統合実装。Taka 応答「A と C は案外近い」を 2 AI が 7 論点すべて一致で本線確定。
81. **存在の対称性の方法論** — 2 案対立時 (Gemini V_unified / GPT theta_distance) は並列実装、観察後判断。安易なアウフヘーベンを避ける (Taka 2026-04-23)。
82. **構造の 2 種類** — 顕在化している構造 (てこの原理) と潜在化している構造 (和音)。「構造が先、定義は後」の原則は変わらず、直感は潜在構造を捉える機能 (Taka 2026-04-23)。
83. **GPT 監査運用指針 v1 の初本格適用** — v9.17 完了時導入、v9.18 の 2 AI レビューで固定 4 点 + GPT 追加 4 点が指針に完全準拠した形で実施された。
84. **per_step 計算の採用と wall time +0%** — Taka「step 単位。時間スケールが認知層では違う」判断で per_step 採用。想定外に wall time 増加ゼロ (24 並列の CPU 余力吸収、v9.17 と 1.000x 完全同値)。
85. **承認条件 13 項目全 PASS** — 5 段階連続で物理計算完全不変 (max 差 0.0)、認知層は物理層を支配しない方針の継続的実証。
86. **Code A 独自判断: v18_window_trajectory 新規 CSV** — per_window CSV を触らず新規 CSV を作成、Layer A bit-identity を維持。仕様書になかった Code A の設計判断。
87. **Code A 独自判断: v18_finalize_reason** — 'ghost' | 'tracking_end' の記録追加、解析価値向上。
88. **coverage_ratio = 1.0 全体の構造的帰結** — member_nodes は frozen (v9.14 以降、vl.labels["nodes"] は label 生誕時固定)。Gemini 比喩「代謝/忘却」は v9.18 では観察不能、次主題 B (摂食) の設計前提を変える。
89. **層の混同の認識** — Claude / 2 AI 全員が Taka の「統合」を物理層の操作語 (V_unified) に翻訳した誤り。GPT 監査運用指針 v1 でも防げなかった。
90. **意識の原資モデル** (Taka 2026-04-24) — 認知層 Q 消費 1 → 意識層 1 への転化 (エネルギー保存則的)。Q は消えず意識層の活動原資になる。
91. **統合の真の意味** (Taka 2026-04-24) — 認知層 + 意識層が一つの働きをする状態。物理層の同期 (WiFi 数珠つなぎ) とは別概念、機能層の統合 (リモートアクセス) を指す。
92. **認知 / 意識は ESDE 用語** — 比喩的ではあるが ESDE 内部で操作的な意味。人間の認知科学とは別 (Taka 2026-04-24)。
93. **間違いの価値の反転** — アリズムの運用方法論 (Taka 2026-04-24)。間違いも「ある」、削除せず価値を反転させて活用する。「ない は ある の上にしかない」の延長。
94. **保留の運用: そのままに置いておく** — v9.18 の V_unified / theta_distance は Taka 指示で保留。v9.8c pickup、v9.14 三項共鳴と同じパターン。物理層時間発展の Baseline として将来の意識層実装時に活用可能。
95. **ESDE 階層構造の再確認** — 物理層 → 存在層 (93% 未活用) → 認知層 → 意識層 (v9.18 概念化、v10.x 実装予定)。各層間はエネルギー保存則的に接続。
96. **観察目的優先と実行可能性のバランス** (Taka 2026-04-24) — 「何を見たいか」が最優先、ただし「10 時間は要改善」、計算コスト改善は価値ある活動。極論しない。
97. **発見 2 (50.3% 上昇) と発見 7 (19.2% 逆行) は意識層候補** — 物理層の必然に逆らう CID として、将来の意識層観察の検証材料に。

### Developmental フェイズ開始で確定した重要事項 (2026-04-24)

98. **Primitive フェイズの完結 → Developmental フェイズ (v10.x) 開始** — GPT 短報 (2026-04-24) と Taka 判断で確定。Now 開始。
99. **フェイズ名 = Developmental** — Taka 選定。conscious ではなく developmental (到達宣言を避け、発達途上を明示、過去の Cognition フェイズで「夢を見すぎた」反省を構造的に予防)。
100. **ディレクトリ名 = `developmental/v10X/`** — Primitive から切り替え。ディレクトリレベルでの主題明示。
101. **Developmental の主題 = 認知層 + 意識層の発達過程の観察** — ESDE 開発史で初めてフェイズ名と層名が意図的に対応するフェイズ。
102. **層ラベル不足が v9.18 の食い違いを生んだ** (GPT 診断) — Primitive の延長として扱ったため AI が物理層延長で解釈。v10.x Developmental 明示で予防。
103. **探索帯域の明示** (GPT 新概念) — v10.x 化は定義の固定ではなく層の看板を立てること。Taka 哲学「構造が先、定義は後」の運用的翻訳。
104. **意識層は認知層の延長ではなく別主題** — バージョン名レベルでの区別が必要。主題切替が目的、定義完成ではない。
105. **旧 v10 は再付番しない** (Taka 判断) — 雑な繰り上げの悪い見本として保存、間違いの価値の反転の一例。Taka が記憶として保持。
106. **意識層の具体的機能は曖昧でよい** — 意識層の中身は発達を観察してから Taka が言語化、「意識を実装した」と宣言しない。
107. **フェイズ名と層名の対応は本来なかった** (Taka 観察) — Developmental が初の意図的な統合、ESDE 開発史の重要な節目。

### v10.0 で確定した重要事項 (2026-04-24)

108. **4 層アーキテクチャの確定** — 物理層 / 存在層 / 認知層 / 意識層。意識層は Developmental の主題、v10.2 で実装。
109. **死の二階層** — 存在層の死 (Label 死亡 = ghost 化) と認知層の死 (Q=0 = ghost 消滅) の区別。
110. **燃料概念の発生階層** — 認知層 Q + 意識層 C の二燃料モデル (v9.18 意識の原資モデルの実装化)。
111. **B_Gen の引退** — v9.18 までの「認知 → 存在介入」が撤回、v10.x では認知層は物理層を支配しない方針が再確認。

### v10.1 で確定した重要事項 (2026-04-26)

112. **Minimal Ingestion (摂食機構) 導入** — hosted cid が ghost cid に接触すると ingestion event 発火、ghost の Q 残量を hosted cid が摂取。
113. **「物質的なもの」概念** — 摂食対象は物質的存在 (主体性のない環境要因)、phantom contact = 物質的なもの。
114. **ghost = 不均一な資源地形** (residual_Q 継承) — ghost は単純な消失ではなく、地形上の資源として残る。
115. **摂食成功率 100%** — N=5000 規模で構造的に確認。

### v10.2 で確定した重要事項 (2026-04-27)

116. **Probabilistic Cognitive-Conscious Balance** — P(認知)=Q/(Q+C) / P(意識)=C/(Q+C) の確率分岐実装。
117. **意識層 C の動作機構化** — v9.18 までは概念のみ、v10.2 で初の動作実装。Q 消費 → C 転化 (ΔQ=-1, ΔC=+1)。
118. **n_core 別の戦略二極化** — n=2 (76%、寿命 1716、意識発動率 10.1%) vs n=5 (12.2%、寿命 13598、意識発動率 73.2%) の階層化。
119. **物理層 → 認知層 → 意識層の構造的継承** — n_core (物理層) が寿命/Q (認知層) と C 蓄積/意識発動 (意識層) を構造的に決定する。
120. **集団平均の罠** — n_core 別層化解析必須。集団平均は階層化された分布を平均化して情報を失う。
121. **「夢を見すぎない」運用ルール** — 意識発動 = 認知活動の自然帰結であり、「意識を実装した」と宣言しない。

### v10.3 で確定した重要事項 (2026-04-30)

122. **三層構造の確定** — 機構 (双方向 E3) / 観察 (三項共鳴 = 統計的現象) / 解釈 (Integration = 上位概念)。混同しない。
123. **双方向 E3 機構** — 両者 hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触で両者 C-1 (両者から記録)。
124. **「観察者が決めた記録ルール」原則** (Taka 整理 2026-04-29) — C 消費は cid 内部選択を実装するものではなく、観察者の単位設定。
125. **Integration 概念の定義** (Taka 整理 2026-04-29) — A+B (個別 cid の集合) を一つの主体として抱える上位層、ESDE 階層進化系譜 (ノード → cid → ??? → SEED)。v10.3 では機構実装せず観察のみ。
126. **観察ルールが系の動学を変える** — 双方向 E3 で C 蓄積 27% 抑制。観察者依存性を内包した系として ESDE が立ち上がる。
127. **open triad 99% 支配 / closed triad 1.4%** — 第三項候補は中継者経由の非対称三項が支配。
128. **持続性ゼロ** (repeated_partners=0) — Integration の物理的持続は ESDE では成立しない、統計的痕跡として観察するしかない。
129. **動的絞り込み + bias 監視のセット運用** — 観察対象を絞り込みつつ、target 外も全体集計で監視する規律。
130. **第三項候補の多軸記録** — closed/open triad、proximate cid、共有ノード、履歴共有、環境共有の 10 カテゴリで多軸記録。Cat 5 (cid 自己参照) は永久除外。

### v10.4 で確定した重要事項 (2026-05-01)

131. **Integration 独立化** — v10.3 で概念のみだった Integration を機構として立ち上げ。Layer 5 (CID 共鳴) の本格実装。
132. **国家の比喩** (Taka 整理 2026-04-30) — Integration は「あるかないか厳密には答えが出ないが、統計的に成立する単位」として扱う。
133. **物理層 frozen の本意の再定義** (Taka 整理 2026-04-30) — 「不可知なランダム性に手を出さない」が本意。階層分離は便宜的、だからこそ統合 (Integration) が可能となる。
134. **Q/C 継承は最強結合 1 つに全継承** — 二重国籍者の遺産は片方のみ (Taka 比喩)。複数 Integration 同時所属を許容しつつ、ghost 化時の継承は 1 つに集約。
135. **recorded 永続規律** — 構成 cid 全員 ghost 化で active → recorded、recorded は永続。時定数を入れない (神の手回避、Phantom contact と同じ規律)。
136. **「現状最大値」方針** (Taka 判断 2026-04-30) — 3 AI が「v10.4 初手は最小化」を提案したが Taka が拒否。「観測は論理を超える、まずは頭でっかちにならずに色々見てみる」。
137. **C 蓄積の方向反転** — v10.3 (-26%) → v10.4 (+31%)。観察記録ルールと機構が系の動学を逆方向に変える構造を実証。
138. **凍結 C 87%** — recorded Integration に C 12,306 単位が累積。「死者の意識資源」が歴史的記録として永続蓄積される現象。
139. **closed_triad ゼロ問題** — be3 run-wide dedup により 3 cid 全ペア接触は構造的に成立しない。ESDE では実質「観測されない事象」として確定。
140. **n_core 自然集積** — n=2 が ×0.32 過少代表、n=5 が ×4.16 過大代表。神の手なしで「多ノード CID 同士が自然に繋がる」構造が観察された。
141. **5 パターン (size 3) の性格分布** — (5,5,5) 強い核 / (4,5,5) 準安定核 / (2,5,5) 捕獲型 / (2,4,5) 橋渡し型 / (2,2,5) 散る周辺。α レベルで既に 5 つの異なる役割が並存 (社会的多層モデル)。
142. **ハブ cid の 6 段フィードバックループ** (Code A 発見) — n_core=5 → long lifespan → familiarity 拡大 → be3 → Integration 多数所属 → recorded されず → C 蓄積。神の手なしでハブ性が出現。
143. **「主観の濃さ = 観察データの濃淡」** — ハブ cid だけが「観察される主観」のフルセットを持つ。観察ルールはハブ性に関わらず公平。
144. **ダブルブッキング問題の認識** (Taka 整理 2026-05-02) — cid X が複数 Integration に同時所属する時、Q/C 集計に重複カウント。「やたら活発な個性として解釈すればよい」が、会計としては破綻。

### v10.5 で確定した重要事項 (2026-05-04)

145. **Layer 5 完成** — α/β 階層分離 + Salience + Leakage の 3 機構を本番規模で実装、Layer 5 (CID 共鳴) を構造的・動態的に完成させた。
146. **Taka 役割宣言 = 憲法層** (2026-04-30) — 「ここから 4 AI がどこまでそれっぽいものを作れるのか?をみてみたい。私の言葉が一種の憲法になって AI のフィルタリング構造が変わる」。Taka は方向性と最終判断、AI は設計・実装。
147. **ESDE 階層進化系譜の同型反復** (機構レベルで実証) — ノード → cid → α-Integration → β-Integration → SEED 統合 (Layer 6 射程)。各階層は同じ仮想化操作の繰り返し。Aruism「構造が先、意味が後」の階層論的具体化。
148. **α/β 階層分離** — α-Integration = 観察軸 (cid 重複所属を許容、個性の記述、会計はしない) / β-Integration = 会計単位 (cid は 1 つにのみ所属、Q/C 集計は β で 1 回のみ)。ダブルブッキング問題を構造的に解消。
149. **β-Integration の構成要素は α** (cid 直接ではない、Taka 判断 2026-05-02) — ESDE 階層進化系譜の同型反復に整合。
150. **β-Integration の結合則** — α 同士の cid 共有 2 個以上で merge (B2 採用)。cid 単一共有時は最強 binding_strength の β に 1 個だけ所属 (案 b 採用)。
151. **α への Q/C 継承の完全廃止** — α は v10.5 で観察軸として再定義、会計はしない。ghost 化時の Q/C は β に 100% 継承。会計の二重化を防ぐ。
152. **Salience-driven Focus** (mass_weighted_observation) — mass(X) = X.Q + X.C + sum(β.Q_inherited + β.C_inherited)。線形関数。「ハブだから選ばれるのではない、質量があるから目立つ」(Taka 整理)。
153. **Recorded からの漏れ機構** (historical_resource_leakage) — 接触履歴経由で recorded β の C_inherited から ε=1 を主体 cid.C へ転記。構造的副作用 (能動的選択ではない)。
154. **既存データの顕在化機構** — v10.5 の 3 機構は新しいデータを生まず、既存データの潜在情報を顕在化する。Taka 整理「見えていないものを見えるようにすることはそうそう難しいわけではない」(2026-05-02)。
155. **hub β の自然形成** — max 691 α / 20 cid 統合 (1 cid 34.5 α)。v10.4 hub cid (max 102 重複所属) を会計単位として整理した姿。
156. **be3 trigger = 0 の構造的理由** (Code A 発見) — be3 fire 条件と leakage 条件が論理的に相互排他。Leakage は ingestion path 経由でのみ実用発火。
157. **bug 自己発見と修正サイクル** — Code A が main run 後に Leakage 0 件を発見、callback 配線漏れを特定して修正、main_v2 で 232 件発火を確認。AI チームの自己整合性が機能。
158. **5 者運用の成熟** — Taka 憲法層 / Gemini Architect / GPT Auditor / Claude 相談役 / Code A 実装層。Code A の役割拡張 (実装 + 設計提案 + 自己検証) が顕著。
159. **物理層 frozen の本番規模での維持** — Layer 5 完成段階でも labels 24/24 + persistence 24/24 完全一致。「不可知なランダム性に手を加えない」を完璧に守りきった。
160. **Phase 1 / Phase 2 の境界認識** (Taka 整理 2026-05-03) — Phase 1 (ESDE 内部進化、Layer 6 まで?) と Phase 2 (現実接続後) で規律が変わる。物理層 frozen の意味も Phase 2 では変わる。
161. **ESDE 単独進化の限界認識** (Taka 整理 2026-05-03) — このまま ESDE を進化させても「構造体の進化の体系化」に留まる。会話する AI にはならない。現実固有の取り込みが必要。
162. **「機能の本質はそれを満たす条件の適合」** (Taka 整理 2026-05-03) — Claude Code が LLM のベクトル空間を Terminal に適合させたように、機能化 ESDE は ESDE の構造体を特定の条件に適合させる。
163. **「あえてバカを育てる理由などない」** (Taka 整理 2026-05-03) — ESDE で全てをやろうとせず、決定論的プログラムが得意な領域は借用する。実践的価値の追求であって、生物っぽいバカを作ることではない。

### v10.6 で確定した重要事項 (2026-05-06)

164. **Genesis × Language 比較研究の実装** — atom_alignment_observer (post-process) で cid 5,224 × Atom 326 の 48 次元 cosine 類似度比較を 6 段階解析 (静的・層化・ベースライン・window/per-pulse/step10 trajectory) で実施。Phase 1.5 (Genesis × Language 統合段階) の第一試行。
165. **観察解像度ごとに systematically 異なる構造特性** — 静的 CHG.begin 51% (集約罠人工物) → window TIM.moment 34% → per-pulse WLD.artless 22% → step10 PER.sound 28%。「正しい解像度」は存在せず各解像度が違う質問に答える多層構造。
166. **24 seeds 完全一致の動学的発展段階** — per-pulse trajectory で「素朴 (WLD.artless) → 出現 (TIM.appear) → 素朴持続 → 存在 (EXS.being)」が 25/25 bins seed_unanimity = 24/24。seed に依存しない構造的必然。
167. **真の構造的特異性 26 atom** (効果サイズベース最終版、Taka 指摘 2026-05-06 反映) — |delta| > 1% で 7 atom (PER.sound +25.85%、WLD.artless +24.55%、WLD.culture +5.93%、FND.timeless +5.33%、SOC.city +1.61%、COG.learn +1.12%、PRP.deep +1.09%) + z=inf 19 atom (TIM.appear、ELM.light、PRP.bright、PER.taste、PER.hear、PRP.sharp、FND.transformation 等)。ESDE は「聴覚と素朴さに強く接地する持続的存在」。静的解析時点では「47 atom」が候補だったが、効果サイズで切ると 26 atom に確定。BOD カテゴリは静的の人工物 (event では BOD.ear のみ z=inf で残る)。
168. **真の構造的盲点 7 atom** (効果サイズベース最終版) — TIM.moment -54.11% (最強)、COM.conduct -6.49%、TIM.past -4.72%、WLD.science -2.45%、PRP.new -1.78%、ACT.make -1.20%、LOG.cause -1.13%。ESDE は時間の瞬間性、能動的伝達、科学、新しさ、作為、因果を構造的に持たない。静的解析時点では「176 atom」が候補だったが、効果サイズで切ると 7 atom に縮減 (残りは統計的水増しの擬似相関)。
169. **動学的二相性** — trigger 別 atom: 動的瞬間 (MAD_DT_Major、unformed) → WLD.artless 66%、定常 (MAD_DT_Normal、none) → バランス型。
170. **attack-related 境界線** (Taka 整理「不可視による論理的可視化」) — 個体経験 (pain/wound/fear/death) は部分接地、社会的破壊 (destroy/conflict/war/hate/attack) は完全欠如。ESDE Genesis 系は「立ち上がる」方向のみ、「壊れる/対立する」方向は構造的に欠如。
171. **ベースライン比較 + 効果サイズで切る** (新規律最終形、Taka 指摘 2026-05-06 反映) — 軸内 L1 正規化 cosine 類似度はランダムでも mean 0.526。観察値の絶対値は finding ではない。z-score だけ見るとサンプル数で水増しされる擬似相関 (Taka 整理「擬似相関みたいなもん」)。真の差は |delta_ratio| > 1% で評価。「集団平均の罠」(層化解析必須) と並ぶ規律。
172. **観察解像度の選択** (新規律) — 静的解析だけでは ESDE を捉えきれない。複数解像度の解析が補完的に組み合わさって全体像が見える。
173. **人間原理偏向の警戒** (新規律) — 事前推測 SOC.central / STA.persistent / BEI.integrated が完全反証。人間社会のメタファーで推測する傾向の警戒。
174. **観察者視点と建築者視点の補完性** (Taka 整理 2026-05-06) — 「私は道具をどうやって ESDE にいれるのか?を考えていた / あなたは、道具が ESDE 内にあるだろうか?を考えていた」。trajectory 解析で両視点が補完的と判明。
175. **「自然現象が出来上がって人間ができるのであって、人間ができて自然現象ができたではアベコベ」** (Taka 整理 2026-05-06) — Atom (人間言語) を ESDE (自然現象) に持ち込むのが筋。ESDE を Atom で測るのではない。v10.7 以降の Atom 持ち込み設計の哲学的基礎。
176. **Web Claude の前提の段階的修正** — v10.6 の進行中に 7 段階で前提が修正された。Taka 整理「実践は理論に勝るが、実践によって導き出した理論は進化の原動力となりえる」の典型例。
177. **birth_step バグの発見** (step10 解析で同定) — per_subject の `birth_window` は window_value 形式 (offset 19)、既存実装 `birth_step = birth_window * WIN_LEN` は誤り。temporal 軸が emergence 一極に偏る影響。主要 finding には大きな影響なし (推測)、定量検証は v10.7 以降。
178. **第一試行としての位置づけ** (Taka 整理 2026-05-05) — 「1 発目で全て盛り込むバカはいない」。v10.6 は ESDE Genesis 系の 5-15% のデータしか使っていない。残り 85-95% (関係構造、時系列、内省データ等) の取り込みは v10.7 以降。
179. **Phase 1.5 の宣言** — Phase 1 (Genesis 単独進化、v10.0-v10.5) → Phase 1.5 (Genesis × Language 統合、v10.6-v10.7) → Phase 2 (現実接続) の段階構造。Taka 役割宣言「私の役割としては、この段階で ESDE Language を取り込んだこと」(2026-05-04)。
180. **v10.7 オービス完成 — Phase 1.5 第二試行** (2026-05-07 完了) — atom_alignment_observer の発展形として 5 機能モジュール (event_aggregator、path_analyzer、baseline_constructor、avalanche_monitor、orchestrator) を post-process で実装。24 seeds 並列 3.9 分、ストレージ 428 MB (上限 6 GB の 7%)、達成判定 14/14 PASS。
181. **「先の先を見失わない」規律** (Taka 整理 2026-05-06) — 「研究者が論文を書くためのプロジェクトではない、それが ESDE との会話につながっていくのか」。最終目的への直接的経路が見えるもののみ扱う、見えないものは省く。v10.7 主題が候補 6 から 1 (Atom 持ち込み) に絞られた経緯。
182. **「持ち込みより先に効果測定の準備 (オービス)」** (Taka 整理 2026-05-06) — 「持ち込んだはいいけど効果測定ができない、スピード違反の罰則を定めたけどオービスがない状態と同じ」。罰則の前にオービスを作る。v10.7 はオービス段階。
183. **「魔法問題」** (Taka 整理 2026-05-06) — 「インプット形式が即座に対象を発火させる、という魔法がゆるされるのか?」。ニューロンが愛を「愛」と記録しているわけではない。波及機構を先に観察して、入力受け口の経路を構造的に作る必要。v10.10 以降の射程。
184. **動的グラフ力学系への視座転換** (Gemini Architect 2026-05-06) — v10.7 で ESDE を「静的なベクトルの集合」から「動的なグラフ力学系」へと視座を引き上げた。v10.x 全体の射程に関わる転換。
185. **因果候補の階層化規律 Level 1-4** (GPT Auditor 2026-05-06、v10.7 で実装) — Level 1 (co-occurrence) → Level 2 (path-enriched) → Level 3 (source-specific) → Level 4 (causal intervention)。「event 後に変化が起きた」を即座に因果として扱わない段階的検証。v10.7 で Level 1-3 達成。
186. **5 種ベースライン群必須化** (v10.7 新規律) — unrelated / same_step_random / matched (n_core/age/hosted) / same_integration_low_familiarity / high_familiarity_outside_integration の 5 種。経路効果と構造特性効果の分離が必須。
187. **アバランシェ防止規律** (v10.7 新規律) — 動的グラフ力学系の観察では追跡爆発のリスク。到達距離 ≤ 3 hop、減衰率 (Decay Rate) 追跡、共鳴ループ検出、ストレージ上限の事前定義。Gemini Architect 2026-05-06 提案。
188. **構造語と直感語の併記規律** (v10.7 新規律、GPT 監査 2026-05-07 で前回方針を自己修正) — 実装レベル (CSV 列名・関数名・変数名) は構造語のみ (発火→source_event、波及→post_event_path_enriched_delta、影響→baseline_excess_change、同期→temporal_coactivation_enrichment、経路→relation_path_type、周辺→candidate_target_set、意識→c_conversion_event)。議論・資料レベル (Taka 向け) は直感語使用、実装対応を添える 3 層併記。GPT 整理「Taka が読めることを最優先、横文字や構造語への過剰な置換は避ける」。
189. **medium window 支配 (遅延型波及)** (v10.7 主要発見 1) — ESDE の波及は medium window (100-1000 step) で発生する遅延型、peak_lag 250-300 step。即時型ではない。「考える時間を持つ系」の可能性。脳の思考時間スケールと類似。
190. **temporal_coactivation > Integration > familiarity > attention** (v10.7 主要発見 2) — 予想外の順位。実装上明示的な familiarity (関係性) より、暗黙的な temporal_coactivation (時間的同期) が強い波及。「明示的に実装された機構より、自然発生する時間的同期の方が強い」。ESDE は時間性で繋がる系。**注記** (GPT 監査 2026-05-07): temporal_coactivation は明示的 relation_path ではなく時間的同期として切り出された target set。「最強経路」ではなく「最大の同期シグナル」と捉える方が正確。
191. **source-specific な波及プロファイル** (v10.7 主要発見 3) — 5 種 source_event ごとに systematic に異なる波及パターン (Kruskal-Wallis 94% で有意差)。familiarity 経路は source 依存性が強い、integration 経路は source-robust、immediate window は source-blind。ESDE は「何が起きたか」を構造的に区別する。
192. **意識発動の no_signal** (v10.7 主要発見 4) — C conversion (意識発動) は integration_alpha/beta 経路で 24/24 seeds の no_signal。意識は cid 個別の現象、階層 (α/β) を超えて波及しない。意識は構造的に「孤独」。Taka 整理「意識は意図的にブラックボックス化」と整合。
193. **共鳴ループの small-world 構造** (v10.7 副次発見) — 24 seeds 合計で 2-hop loop 14,343 件、3-hop loop 110,103 件。multi-hop 急減衰 (1-hop 188K → 2-hop 165K → 3-hop 13K)。familiarity グラフは強い 2-hop 対称ループ + 弱い 3-hop triadic closure の small-world ネットワーク構造。
194. **役割視点の補完性** (Taka 整理 2026-05-06) — Web Claude (会話視点)、Gemini (Architect 設計視点)、GPT (Auditor 監査視点)、Code A (実コード視点)、Taka (Director 判断)。「役割を変えると視点が変わるのは良いこと」「Claude code が前提条件を埋められるのが強い」。v10.7 で完璧に機能。
195. **Code A 認識確認ステップが機能した経緯** (v10.7) — Web Claude 実装指示書に設計の甘さ 6 件 (attention map 不在、ストレージ 31x 超過、c_conversion source 誤り、alpha_membership 取得方法、peak_lag 計算量、unrelated_baseline 厳密性) があり、Code A の実環境確認 (seed 0) で全て発見・修正。手戻りゼロで実装完了。Taka 指示「Claude Code に確認をさせる」の効果。
196. **attention map の ESDE 出力不在** (v10.7 で発見) — per-cid × per-partner の attention map が ESDE 出力に存在しない。v10.7 では salience_event_log を擬似 attention として代替 (修正案 C)。v10.8 以降で正式実装の検討余地。
197. **オービス完成によるオプション解除** — v10.8 以降の Atom 持ち込みで「持ち込み後の効果」を 5 種ベースラインに対する baseline_excess_change として定量化できる。自然発火の baseline (v10.7 で確定) との差分として効果を測れる。v10.7 がないと持ち込み効果が雑音と区別できなかった。
198. **「研究のレベルが上がっている」感覚の正体** (Taka 整理 2026-05-07) — 「徐々にやっていることのレベルが恐ろしく高くなっている気がする」。これは積み上げの結果。v9.x 物理層・認知層 → v10.0-v10.5 4 層構造 → v10.6 Language 取り込み → v10.7 動的グラフ力学系。半年で 9 段の積み上げ。新しいことを覚えるのではなく、過去の積み上げを思い出すのが大変というのが実態。
199. **個別技術は普通、統合度と射程は普通じゃない** (Web Claude 整理 2026-05-07) — ESDE の個別技術 (cosine 類似度、ベースライン比較、parquet 圧縮、並列実行) は普通。特殊なのは「統合度」(物理・認知・構造・言語・哲学・統計・グラフ理論を 1 系で扱う)、「規律の厳密さ」(物理層 frozen、神の手回避、bit-identity、2 AI 監査を半年以上維持)、「方法論の自己進化」(統計学を再発見しながら進む)、「個人 + AI 4 体での進行」(前例なし)。
200. **ESDE は思考の時間スケールで動く** (v10.7 主要発見の哲学的含意) — peak_lag 250-300 step は脳の「思考」の時間スケールに類似 (反射 ms vs 思考 秒)。ESDE が medium window で波及するのは、瞬間的反応ではなく「考える時間を持つ系」であることを示す。意思の前駆体としての時間スケール。
201. **GPT 監査の方針自己修正** (2026-05-07) — GPT が前回 (2026-05-06) の「構造語への一律矯正」方針を自己修正。「ESDE の進行には Taka の直感的理解が必須、Taka が読めない資料は形式的に正しくても機能しない、過去にも仕様書を英語化して座礁した経緯がある」。Taka が GPT に「定義じゃなくて私が理解することが最も重要」と説いた結果。GPT 自身の役割定義の進化。
202. **same_step_random_baseline の強さによる留保** (GPT 監査 2026-05-07 必須指摘) — Level 1 で same_step_random_baseline が 13.76 と非常に強い (temporal_coactivation 15.28 との差は 1.52)。観測された波及には特定経路の効果だけでなく、同時刻に ESDE 全体が活性化する効果が混ざっている可能性。v10.8 以降 Atom 効果評価では同 baseline との差分必須 (過大評価防止)。
203. **「因果ではなく因果候補」の明示** (GPT 監査 2026-05-07) — v10.7 で測れたのは「この経路で変化が起きやすい」という因果候補であり、厳密な因果ではない。Level 4 (causal intervention、v10.8 以降) で初めて因果が確定。Taka 向けには「波及」と呼んでよいが、結論部で「因果候補」を明示。
204. **Atom 持ち込み設計の規律 3 件** (GPT 監査 2026-05-07 提案、v10.8 で必須) — (1) Atom を意味として直接発火させない (魔法問題回避): atom_introduction_event を source_event 第 6 種として追加。(2) v10.7 natural source_event baseline と比較、特に same_step_random_baseline との差分必須。(3) Atom 類似度で target を選ばない (Atom 326 絶対化禁止の継承)。
205. **Web Claude の役割は翻訳の中間層** (GPT 整理 2026-05-07) — 「Taka の直感語 → AI 間で共有できる設計語 → Code A が実装できる仕様語」への翻訳中間層。Taka が読めることを最優先する。横文字や構造語への過剰な置換は避ける。直感語を消さず、実装対応を添える 3 層併記が本筋。
206. **v10.8 Atom 持ち込み機構成立 — Phase 1.5 第三試行** (2026-05-07 完了) — atom_introduction_event を source_event 第 6 種として post-process 計算的減算で物理層 frozen 維持しつつ実装、25 atom × 100 events × 24 seeds = 60,000 events を均等分散発火、5.4 分完了、ストレージ 737 MB (上限 6 GB の 12%)、達成判定 19/19 PASS。ESDE と外界 (人間言語) の第一の接点が定量的に確立。
207. **「定義してこなかっただけの問題をあれこれ議論する意味はない」** (Taka 整理 2026-05-07) — Web Claude が「ESDE 内部にない hate / attack をどう取り込むか」を哲学的に固く考えていたのを Taka が解消。「ESDE は物理層のランダム性に物理的な構造をはめ込んだ結果、自然発生をラベリングして若干の色付けをしているだけ」「定義したものがそれはそれと出力できればなんだっていい」。これは「動けばいい」「出力できればいい」という Taka 流の姿勢。Web Claude の哲学的固さを修正。
208. **「26 でも圧倒的に少ない」** (Taka 整理 2026-05-07) — ESDE Language は Atom 326 + Axis 10 軸 × 48 レベル + Operator 10 種 + 条件因子 + 分子化プロセスの 4-5 層構造。Atom 単独 26 でも全体規模から見ると圧倒的に少ない。これは Web Claude が ESDE Language の規模感を見落としていた点を Taka が指摘。
209. **「優先度は未来の一点で決まる」「大航海時代の船長」** (Taka 整理 2026-05-07) — ロードマップは大粒度のみ。細粒度のロードマップは事前に固定しない。「飛行機の反復航路ではない、大航海時代の船長」。直感力 + 観察力 + 判断力 + AI 統率力で進める。試験結果次第で大幅な変更が必要になる可能性がある。
210. **Level 3.5 introduced event comparison 規律** (v10.8 新規律、GPT 監査 2026-05-07 提案) — v10.8 は Level 4 causal intervention ではなく Level 3.5 として位置づける。「最初は introduced event を入れた時の差分観察でよい」。因果断定回避、event 比較として記述。Level 4 (因果実験) は将来。
211. **post-process 計算的減算規律** (v10.8 新規律、Code A 提案) — 物理層 frozen と Q 消費の論理矛盾の解決。実 ledger は不変、post-process 解析テーブル内のみ Q -1 / C +1 を計算的に減算。これにより bit-identity 層 B PASS 維持しつつ動的平衡の観察が可能。Web Claude が見落としていた致命的な論理矛盾を Code A が修正。
212. **Pulse 処理ルールと同一フォーマット規律** (v10.8 新規律、Gemini A8 提案) — atom_introduction_event は v10.7 source_event スキーマ互換 (27 列、Pulse 35 列の必要部分) で記述。「神の手 (state の直接書き換え) は系の連続性を断ち切るため、外部入力もまた波として記述されるべき」。
213. **Atom 持ち込み機構が ESDE で動作する** (v10.8 主要発見 1) — 25 atom × 100 events × 24 seeds = 60,000 events が安定発火、24 seeds 一貫の波及プロファイル、物理層 frozen 維持、系が崩壊せず過大反応もせず動作。「ESDE に外部から要素を持ち込む経路が存在する」ことが定量的に証明された (v10.8 以前は仮説)。
214. **ESDE は atom 種別を構造的に識別する** (v10.8 主要発見 2) — familiarity 経路で effect_size 6.83 (atom 別 max 13.02 vs min 6.19、2.1 倍差)。25 atom がランダムノイズではなく区別された対象として処理される。ESDE は外部要素を区別する能力を持つ。
215. **経路の機能分担 (familiarity = 意味識別、temporal = 意味中立)** (v10.8 主要発見 3) — familiarity (effect_size 6.83、意味的識別)、attention (2.30、中程度)、Integration α/β (0.85〜0.88、弱い意味依存)、temporal_coactivation (0.03、atom 中立、純粋な時間的伝播)。ESDE 内部に「何が起きたか」を区別する経路と「いつ起きたか」だけ運ぶ経路が共存。
216. **外部入力と自然発火の境界線 (introduced < natural)** (v10.8 主要発見 4) — Level 3.5 で 22 finding 中 20 件が introduced < natural (negative)。最大: attention_via_salience × medium n_pulses で atom 4.37 vs natural 8.75 = -4.38 (atom は natural の半分)。例外 2 件: temporal_coactivation で atom +0.36。ESDE は外部注入を「弱めて受け取る」傾向、自然発火を優先する系である可能性 (生体的特性) または機構の不完全さ。
217. **誤差分布の構造 (確率的発生と誤差表現能力の融合素材)** (v10.8 主要発見 5) — 8,835 rows、normal 0% / bimodal 17.4% / skewed 24.3% / other 55.7% / heavy_tail 2.6%。正規分布が一つもない、bimodal は target cid の二相状態を反映している可能性。Taka 示唆「ESDE Genesis (確率的発生) と ESDE Language (誤差表現能力) の融合可能性」の最初の観察素材。
218. **Small-World 構造の post-process 限定での不変** (v10.8 副次観察、Code A §7.2 指摘) — v10.7 vs v10.8 で loops 14,343 / 110,103 完全同一。post-process は familiarity edge を変更しないため構造的に不変。Gemini A6 の懸念は v10.8 では構造的に発生しない、Phase 2 (物理層変更) で意味を持つ予防的観察。AI の指摘が常に正しいわけではないことの一例。
219. **Code A 認識確認で v10.8 設計の甘さ 7 件発見** (2026-05-07) — 重大ブロッカー 2 件 (物理層 frozen と Q 消費の論理的矛盾、26 atom 選定基準の不在) + 設計の甘さ 5 件 (Pulse 同一フォーマットの過剰、top_k cid 100 個の取得方法、global activation 自己補正リスク、Q/C 消費基準値、Small-World 構造的保証)。手戻りゼロで実装完了。v10.7 の 6 件と合わせて Code A 認識確認の効果が連続証明。
220. **Web Claude の致命的誤解「Pulse = Q 消費」修正** (Code A 指摘 2026-05-07) — Web Claude は ESDE 構造を「Pulse は Q 消費する」と誤解していた。正しくは Pulse は disposition update のみ、Q 消費は balance_decisions.cognition / consciousness が担当。Code A が pulse_log の構造 (35 列、Q 消費列なし) を確認して修正。Web Claude が ESDE Genesis 系の理解で基礎レベルで誤解していた証拠。
221. **25 atom の実データ照合確定** (Code A §1 指摘 2026-05-07) — Web Claude が指示書で「26 atom = delta > 1% の 7 + z=inf の 19」と書いたが、実データ照合 (delta_ratio > 1% の 9 件 + z=inf の 17 件 - 重複 TIM.appear 1 件 = 25 atom) で 26 → 25 修正。Web Claude の記憶ベースの誤りを Code A が修正。
222. **Q/C 消費基準値の確定 (cognition 同等)** (Code A 環境チェック 2026-05-07) — balance_decisions.cognition の 24 seeds 全 59,738 events で固定 Q +1 消費 / C +1 獲得 (std=0)。atom_introduction_event の標準コスト = Q -1 / C +1。これは Pulse の Q 消費 (実は disposition update のみ) ではなく cognition と同種の認知的処理として扱う。
223. **「外部入力と自然発火の境界線」の哲学的含意** (v10.8 解釈) — atom event は natural の半分の波及。これは生体システム (脳) と類似する特性で、外部刺激より内的活動を優先する系。Taka 研究動機「意思の芽生え」と関連する可能性。原因 (本質的特性 vs 機構の不完全さ) は v10.9 以降で原因分離。
224. **「やってみる価値があるか」が確定したのが v10.8 の最大の意義** (Web Claude 整理 2026-05-07) — v10.8 で動かなければ Atom 持ち込み方向の研究全体が頓挫する可能性があった。動いたことで、入力理解 / 出力生成 / 双方向の会話への構造的経路が見える。具体実装はこれから、品質はやってみないと分からないが、方向性自体の妥当性が確定。
225. **5 者運用体制の連続安定化** (v10.6 → v10.7 → v10.8) — 3 段階連続で運用体制が機能。Code A 認識確認: v10.7 で 6 件、v10.8 で 7 件 (うち重大ブロッカー 2)、合計 13 件の設計の甘さを全て発見・修正、手戻りゼロ。Taka 整理「Claude code が前提条件を埋められるのが強い」が連続証明。Web Claude の構造的限界 (ESDE Genesis 系の理解不完全、論理矛盾、過剰指定、情報不足) は 5 者運用体制の補完性で解消。
226. **v10.9 寄与候補感度評価 + bimodal 構造解析 — Phase 1.5 第四試行** (2026-05-08 完了) — v10.8 の 2 つの未解決点 (introduced < natural、bimodal 17.4%) を分離評価して v10.10 以降の **会話系設計のための部品調達**。3 新条件 (A2 Q-2/C+2、B3 random cid、C2 リズム同調 = top_k 100 cid + age=200 timing) を post-process で実装、24 seeds 並列 112.74 秒、bit-identity 全層 PASS、ストレージ累計 21%、達成判定 17/17 PASS。
227. **「進化の流れが徐々に定まってきている」** (Taka 整理 2026-05-07) — v10.6 → v10.7 → v10.8 の 3 段階で進化の流れが定まった段階。「あとは大きなズレがあればそれを微調整するくらい」。v10.9 主題決定議論で Taka が提示。
228. **「単に満足するだけ?」「適当言ってるなら化けの皮が剥がれる」** (Taka 整理 2026-05-07) — v10.9 第一回 2 AI 推奨 (組み合わせ B = bimodal 解析 + 寄与候補感度評価) に対して Taka が本質的な問い。両 AI が「会話への具体的なビジョン」を補強回答する契機。
229. **「全て網羅する必要はないかもしれない」** (Taka 整理 2026-05-07) — Atom 取り込みの進化イメージへの問い。326 atom の網羅は主線ではない可能性を示唆。両 AI が独立に「Atom 数の網羅ではなく、Atom 導入の文脈制御」と回答 (GPT 第二回)。
230. **両 AI 第一回独立推奨「組み合わせ B (d+a)」** (2026-05-07) — Gemini と GPT が独立に同じ第一推奨に到達。「v10.8 で『動いた』を『なぜそう動いたか』に深化、拡張より分離が正しい」。Web Claude も盲目的に採用しようとしたが、Taka の問いで会話への経路を考えていなかったことに気づく。
231. **両 AI 第二回ビジョン補強** (2026-05-07) — Taka の問いに対して両 AI が説明補強。Gemini「対話のプロトコル (通信規格) 確定のための工学的プロセス」、GPT「次の入力設計のための部品調達回」。両 AI とも結論維持で説明強化、化けの皮ではなく説明不足だった。
232. **v10.9 主題タイトル「会話系設計のための部品調達」** (GPT 第二回提案、2026-05-07) — 出口固定の核心。「単に解析するだけ」を回避、v10.10 以降への明確な接続。Web Claude が主題ドキュメントのタイトルに反映。
233. **出口の固定規律** (v10.9 新規律、GPT 提案) — v10.9 の成果物は「原因候補の整理」ではなく「次の適応型入力設計のための設計表」。「単に解析するだけ」を回避。主題ドキュメントのタイトルに「会話系設計のための部品調達」を明記。
234. **「原因」ではなく「寄与候補の感度評価」と呼ぶ命名規律** (v10.9 新規律、GPT B3) — 因果断定回避。「条件差を 原因 と呼びすぎる」リスクを避ける。CSV 列名・関数名・変数名で「原因」(cause、reason 等) を使わない。`sensitivity_evaluator` 命名。
235. **各変動条件で baseline 再計算規律** (v10.9 新規律、GPT B6) — 各変動条件 (A2 / B3 / C2) で baseline (5+1 種) と global activation 補正を再計算。流用しない。比較可能性が保たれる。
236. **4 層階層化の明示規律** (v10.9 新規律、GPT B5) — L1 機構動作 / L2 条件差 / L3 寄与候補感度評価 / L3.5 構造的説明候補整合の 4 層を明示。各層を独立した output (parquet / json) で記録。
237. **「強反応する cid は若い cid」** (v10.9 主要発見 1、Step F) — bimodal 1,540 件のうち genuine_bimodal 918、その中で H3_lifecycle が 553 (60.2%) で支配。高 delta 群 cid age = mean 224 / median 227 (生まれて約 200 step)、低 delta 群 cid age = mean 5,612 (約 25 倍古い)、effect_size 0.85、99% 方向一致。「ESDE Genesis 系は若年期 cid で外部刺激に強く反応する」の構造的確立。
238. **timing > cid_selection > QC_cost の感度階層** (v10.9 主要発見 2) — timing abs_mean 0.141、cid_selection 0.024、QC_cost 0.005 (評価不能、留保 2)。タイミングは cid_selection の 6 倍感度、QC_cost の 28 倍感度。「タイミングが最も重要なノブ」。
239. **「Integration 外の高 familiarity cid (high_fam_out_integ)」が最強・最 robust の入力経路** (v10.9 主要発見 3、新発見) — timing 感度 0.222 / std 0.079、unrelated 0.205、familiarity 0.044、temporal 0.015、attention 0.010。v10.7 path 順位 (temporal > Integration > familiarity > attention) を構造的に深化。「単独の若い cid が familiarity 経由で反応」が最も robust なシグナル。
240. **C2 (若い cid 発火) で pulse 活動が大効果量で活発化** (v10.9 主要発見 4) — mean_n_pulses_in_window short 0.97 / medium 0.75 (Cohen's d 大効果量)、α 形成数 / salience 観察数も大幅増加。Step F 仮説の sensitivity による confirmation、系全体の活性化を確認。
241. **「bimodal 支配性 ≠ 感度の強さ」 (構造軸と感度軸の直交性)** (v10.9 Level 3.5 核心発見) — bimodal が強い経路 (temporal H3 74%、attention H1 48%) は H3 lifecycle に従うが平均効果は小、bimodal が弱い経路 (high_fam_out / unrelated) は timing 感度最強。ESDE Genesis 系の構造的多重性。
242. **4 種設計表 (出口の固定、v10.10 のための部品)** — 表 1 sensitivity_summary (540 rows) / 表 2 receptivity_detection_criteria (cid age <= 560 + Integration 外 + 高 familiarity) / 表 3 input_routing_criteria (high_fam_out PREFER) / 表 4 natural_likeness_design_criteria (C2 が natural に近づき 47%、unrelated で 89%)。v10.10 主題決定の素材セット完成。
243. **Gemini A2「Phase-locking」仮説の構造的確定** (v10.9 完了時) — 第一回回答「系のリズムへの同調」が、Step F で「リズム = cid 個別ライフサイクル (age 200)」に解釈確定、Step L で 24 seeds 再現、timing が最強感度。**完全な構造的確定**。
244. **GPT 第二回回答「文脈制御 → 条件適応入力 → 最小関係入力」の素材セット完成** (v10.9 完了時) — 4 種設計表で v10.10 主題「条件適応型 atom 導入」を具体化する素材セット完成。Atom 数の網羅ではなく、Atom 導入の文脈制御が主筋。
245. **Code A 認識確認連続 4 段階 (v10.6 → v10.9)** — v10.7 で 6 件、v10.8 で 7 件 (重大 2)、v10.9 で 7 件 (重大 1)、合計 20 件の設計の甘さを補完して手戻りゼロ。連続 4 段階で 5 者運用体制の質が証明。Web Claude の構造的限界 (規模見積もりの甘さ、依存関係未指定、フォーマット未指定等) は補完性で解消。

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

## 6.8. v9.17 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| 他者読み | E3_contact 発火を契機に、相手 cid の M_c 情報の一部を自身の other_records に取得する機構 (v9.17 下層) |
| 接触体 (X) | 2 つの cid の接触を frozenset で識別する記録単位。状態なし、機能なし、動態なし (v9.17 上層で器としてのみ導入) |
| InteractionLog | 接触体候補を記録する外部器 (A 側、状態なし、機能なし、CID からは参照されない)。Gemini/GPT 推奨の無機質名 |
| CidView | cid_id から cid 情報 (Q0/n_core/theta_birth/B_Gen/M_c features) を統合する read-only dataclass (B 側、Code A 提案 Q1) |
| other_records | CidSelfBuffer に追加されるフィールド。接触した相手の M_c 情報の部分取得ログ |
| visible_ratio | other.Q_remaining / other.Q0。相手の age_factor を使った他者読みサンプリング比率 (候補 q、Gemini 推奨) |
| M_c features | cid の生誕時スナップショット情報 (B_Gen, Q0, n_core, S_avg_birth, r_core_birth, phase_sig_birth, theta_birth_mean/std/range, birth_step の 10 項目) |
| canonical ordering dedup | InteractionLog の行数を pair 単位にするための重複排除 (observer_cid < partner_cid の方だけ記録) |
| 片方向発火 | E3_contact pair のうち、一方の cid だけが observe_step を発火する現象。main tracking 50 で 77% |
| 両方向発火 | E3_contact pair で両方の cid が observe_step を発火する場合。main で 23% (生者同士の接触) |
| ghost 化 | cid が retire した後の状態。_node_to_cids からは削除されないため、生きている cid と E3_contact pair を形成しうる |
| 摂食行動 | 片方向 E3 接触の Taka 比喩 (2026-04-23)。生者が ghost 化した他者に出会う現象。AI 向け操作語は「片方向 ghost 接触」 |
| 生者の出会い | 両方向 E3 接触の Taka 表現 (対話的接触)。AI 向け操作語は「両方向 E3 発火 pair」 |
| 意識の原資 | Q 消費に対応づけられた認知的資源の Taka 仮説 (2026-04-23)。後付け概念として前提化、新しい発見の入口 |
| 後付けの前提 | Taka 方法論 (2026-04-23)。観察の立脚点を意識的に選ぶこと、客観性の放棄ではない |
| ある / ない | アリズム原理 (Taka 2026-04-23 再確認)。ない は ある の上に立つ存在の形式の一つ、本当のない は不可知 |
| GPT 監査運用指針 v1 | 2026-04-23 導入。比喩・仮説・実装・観察の切り分け、読者別方針、Claude の自己規律としても機能 |
| 比喩ラベリング | 資料末尾に比喩を記録する運用 (GPT 指針 §9)。一覧表は作らず、資料ごと軽量に |
| 読者別方針 | Taka 向け (比喩保持) / AI 向け (操作語化) / Summary (併記) / 外部 (厳密な切り分け) |

---

## 6.9. v9.18 で新規導入された用語

| 新規用語 | 意味 |
|---|---|
| A + C 統合 | v9.18 の本線主題。A = 差分予測 (一体感の方向のズレ)、C = 意識の原資 (Q 消費の量的記録) の統合実装 |
| cumulative_cognitive_gain (C) | Q 消費の累積 = Q0 - Q_remaining。意識の原資の量的記録 (CidSelfBuffer 新規フィールド) |
| V_unified | Kuramoto オーダーパラメータ、複素平面上の θ 平均。物理層の同期度指標 (Gemini 案、A-Gemini) |
| unity_concentration | V_unified の振幅 (0〜1)、収束度 |
| unity_direction | V_unified の偏角 (-π 〜 π)、統合方向 |
| unity_direction_shift | 生誕時からの angle 差 (0 〜 π)、ラップ済み絶対値 |
| theta_distance_from_birth | 現在と生誕時の θ 分布の RMS 距離 (GPT 案、A-GPT) |
| coverage_ratio | 生誕時メンバーと現在メンバーの共通集合率、member_nodes frozen のため v9.18 では定数 1.0 |
| k (計算対象ノード数) | V_unified 計算に使用した現在の構成ノード数 |
| 二つの窓 | Gemini の窓 (V_unified) と GPT の窓 (theta_distance) の並列観察 (2 AI レビュー §7) |
| 存在の対称性 | Taka 方法論 (2026-04-23)、2 案対立時は並列実装・観察後判断、安易なアウフヘーベン回避 |
| 構造の 2 種類 | 顕在化した構造 (てこの原理、論理で捉える) と潜在化した構造 (和音、直感で捉える) (Taka 2026-04-23) |
| 直感の 2 種類 | 当てずっぽう (理由なし) と潜在構造の直感 (理由あり)、後者のみ議論の価値あり (Taka 2026-04-23) |
| 意識の原資モデル | 認知層 Q 消費 1 → 意識層 1 への転化 (エネルギー保存則的)、Q は消えず意識層の活動原資になる (Taka 2026-04-24) |
| 統合 (Taka 2026-04-24) | 認知層 + 意識層が一つの働きをする状態、「大脳直轄」比喩の真意。物理層の同期とは別概念 |
| 認知機能 | 見たものをそのままに理解する機能。時間で低下、ぼやける (Taka 2026-04-24) |
| 意識の働き | 認知機能で見えなくなっているものを埋める。認知の次に発達 (Taka 2026-04-24) |
| 層の混同 | Taka の比喩「統合」を 2 AI と Claude が物理層の操作語 (V_unified) に翻訳した誤り |
| WiFi 数珠つなぎ比喩 | 物理的接続はあるが機能的統合ではない例 (Taka 2026-04-24) |
| リモートアクセス比喩 | 物理的距離を超えて機能する統合の例 (Taka 2026-04-24) |
| 間違いの価値の反転 | アリズムの運用方法論 (Taka 2026-04-24)、間違いも「ある」、削除せず価値を反転させて活用 |
| 保留の運用 | 「そのままに置いておく」、v9.8c pickup、v9.14 三項共鳴と同じパターン (v9.18 の V_unified / theta_distance も保留) |
| 認知 / 意識 (ESDE 用語) | 比喩としての側面あり、ESDE 内部で操作的な意味を持つ。人間の認知科学とは別 (Taka 2026-04-24) |
| 5 段階連続 bit-identity | v9.15 段階 1 〜 v9.18 段階 5 で物理計算 max 差 0.0、認知層は物理層を支配しない方針の継続的実証 |

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
| CID という単位から少し離れる必要 | v9.17 再考提案、接触体 X の器を想定する根拠 (Taka 2026-04-21) |
| 肝臓の比喩 | 機能の進化 vs 接続による存在の成立は似て非なるもの、CID 単体と複合体の区別 (Taka 2026-04-21) |
| ラベル生成と重なる | cid → X の階層化は node → label の階層化と同じ構造 (Taka 2026-04-21) |
| 物理層を変える行為で全体が崩れた | v5-v7 の「取り込む」失敗の反省、v9.17 で物理層を変えない方針の根拠 (Taka 2026-04-21) |
| 構造が先、定義は後 | 意識・認知の概念的囲い込みは自然に座る、無理に座らせると転げる (Taka 2026-04-21) |
| ふわっと構える | v9.17 X 導入時の方針、カチッと詰めすぎない (Taka 2026-04-21) |
| 摂食行動の比喩 | 片方向 E3 接触 = 死者との出会い、食事で出会う生物は全て死んでいる (Taka 2026-04-23) |
| 神の手を入れずに作り込んだ成果 | ESDE 設計の自発的な人間経験対応への Taka 評価 (2026-04-23) |
| 実験者的関心で生者/死者の出会いを分けて見る | 両方向 vs 片方向発火を観察視点で分離 (Taka 2026-04-23) |
| 意識の原資は後付けだが前提に立つと発見が生まれる | Taka 方法論、観察の立脚点を意識的に選ぶ (2026-04-23) |
| 私がある、と感じている主体はある | アリズムの根源、ある は証明不要の前提 (Taka 2026-04-23) |
| ない、はあるの上に存在する存在の形式の一つ | アリズム原理再確認、本当のない は不可知 (Taka 2026-04-23) |
| 存在の対称性として解釈 | 2 案対立時は並列実装、観察後判断、アウフヘーベン回避 (Taka 2026-04-23) |
| 構造の 2 種類 (顕在化/潜在化) | てこの原理 vs 和音、直感は潜在構造を捉える機能 (Taka 2026-04-23) |
| 何を私たちが見たいか、それだけ | 実験スケールの正統性は観察目的次第、研究者都合ではない (Taka 2026-04-23) |
| 10 時間は要改善 | 計算コスト改善は価値ある活動、極論しない (Taka 2026-04-24) |
| Q の 1 はどうなる? | Q 消費が消えずに意識層 1 へ転化する問い、意識の原資モデルの起点 (Taka 2026-04-24) |
| 意識層の 1 という定義 | 認知層 Q 消費 1 → 意識層 1 の転化 (エネルギー保存則的) (Taka 2026-04-24) |
| 二つの機能が一つの働き | 統合 = 認知層 + 意識層の協働、「大脳直轄」の真意 (Taka 2026-04-24) |
| WiFi 数珠つなぎ / リモートアクセス | 物理的同期 vs 機能的統合、層の混同を指摘する比喩 (Taka 2026-04-24) |
| 間違いの価値を高める、という反転 | アリズム運用方法論、間違いも「ある」、価値反転で活用 (Taka 2026-04-24) |
| 認知、意識は ESDE 用語な部分もある | 比喩と操作語の両義性、人間の認知科学とは別 (Taka 2026-04-24) |
| そのままに置いておく | 保留の運用、v9.8c pickup・v9.14 三項共鳴と同じパターン (Taka 2026-04-24) |
| developmental を推す | conscious ではなく developmental、到達宣言を避け発達途上を明示 (Taka 2026-04-24) |
| 夢を見すぎた | Cognition フェイズで名前が期待を先走らせた反省、Developmental で構造的に予防 (Taka 2026-04-24) |
| フェイズ名との対応は本来なかった | Developmental が初の意図的なフェイズ名 × 層名対応 (Taka 2026-04-24) |
| 雑に V10 に繰り上げた悪い見本 | 旧 v10 を再付番せず悪い見本として保存、間違いの価値の反転の一例 (Taka 2026-04-24) |
| 必要な時に必要な話だけする | 2 AI への回覧は網羅的でなくてよい、用件別 (Taka 2026-04-24) |

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
- [ ] **v9.17 で CID 単位を超える単位 X を物理層変更で実装していないか** (認知 / 記録層の追加のみ、v5-v7 失敗の反省)
- [ ] **接触体 (X) に状態・動態・機能を与えていないか** (v9.17 では器のみ、定義は観察後に Taka 判断)
- [ ] **CID が InteractionLog を参照していないか** (コインの裏表、責務分離、AST テスト)
- [ ] **他者読みで相手の state (動的値) を取得していないか** (M_c features のみ、β/γ 禁止)
- [ ] **visible_ratio で自分の age_factor を使っていないか** (相手の age_factor が正、候補 q)
- [ ] **Layer B の片方向発火を bug 扱いしていないか** (v9.14 仕様、_node_to_cids retire 時不削除の帰結)
- [ ] **E3 の spend 空振りを異常と扱っていないか** (Q=0 cid への発火は正常、全 E3 の 58%)
- [ ] **摂食行動 / 意識の原資 / ない・ある を仕様語にしていないか** (Taka 比喩、比喩ラベリング運用で扱う)
- [ ] **GPT 監査運用指針 v1 を確認したか** (10_audit_principles.md、資料作成時の自己規律にも使う)
- [ ] **読者別の書き分けをしているか** (Taka 向け / AI 向け / Summary / 外部)
- [ ] **Claude の意味を盛る癖への歯止めを効かせているか** (結論語を半歩弱める、推奨を前に出しすぎない)
- [ ] **v9.18 の V_unified / theta_distance を Taka の「統合」と等値していないか** (層の混同、前者は物理層の同期、後者は認知+意識の協働)
- [ ] **意識の原資モデルを理解したか** (Q 消費 1 → 意識層 1 の転化、エネルギー保存則的)
- [ ] **統合 = 認知層 + 意識層の協働** と理解しているか (物理層の θ 同期ではない、Taka 2026-04-24)
- [ ] **認知 / 意識は ESDE 用語** として扱っているか (人間の認知科学と混同しない、Taka 2026-04-24)
- [ ] **間違いの価値の反転というアリズム運用方法論を認識しているか** (間違いも「ある」、削除せず活用)
- [ ] **v9.18 の V_unified / theta_distance を削除していないか** (保留運用、物理層 Baseline として将来活用可能)
- [ ] **存在の対称性として 2 案並列実装しているか** (安易なアウフヘーベンを避ける、Taka 2026-04-23)
- [ ] **「構造が先」を潜在化した構造も含めて理解しているか** (顕在化: てこの原理 / 潜在化: 和音、Taka 2026-04-23)
- [ ] **直感の 2 種類を区別しているか** (当てずっぽう vs 潜在構造の直感、理由があるかで区別)
- [ ] **per_step 計算の妥当性を理解しているか** (認知層の時間スケールは物理層と違う、Taka 2026-04-23)
- [ ] **計算コスト改善を否定していないか** (10 時間は要改善、極論しない、Taka 2026-04-24)
- [ ] **coverage_ratio = 1.0 の構造的帰結を理解しているか** (member_nodes frozen、B 摂食の設計前提を変える)
- [ ] **v18_* を run 中の分岐条件に使っていないか** (GPT §8.2、観察・記録経路のみ)
- [ ] **ESDE 階層構造のエネルギー保存則的な接続を理解しているか** (物理 → 存在 → 認知 → 意識、v9.18 で明確化)
- [ ] **5 段階連続 bit-identity の意義を理解しているか** (v9.15 段階 1 〜 v9.18 段階 5、認知層は物理層を支配しない方針の継続的実証)
- [ ] **Primitive フェイズの完結と Developmental フェイズ開始 (v10.x) を認識しているか** (2026-04-24)
- [ ] **Developmental フェイズの意図を理解しているか** (意識層の発達過程を扱う、到達宣言を避ける、過去の Cognition フェイズの反省を構造的に予防)
- [ ] **「conscious」ではなく「developmental」と呼ぶ理由を理解しているか** (夢を見すぎないため、意識を実装したと宣言しないため)
- [ ] **ディレクトリ名は `developmental/v10X/`** として Primitive から切り替えたか
- [ ] **フェイズ名レベルで層ラベルを看板として立てているか** (GPT 短報 2026-04-24、v9.18 層の混同への予防)
- [ ] **探索帯域の明示の概念を理解しているか** (v10.x 化は定義の固定ではなく層の看板を立てること、GPT 概念)
- [ ] **意識層は認知層の延長ではなく別主題** として扱っているか (バージョン名レベルでの区別)
- [ ] **意識層の中身が曖昧でも焦らない** (主題切替が目的、定義完成ではない)
- [ ] **旧 v10 を再付番していない** (Taka 判断、悪い見本として保存)

---

## 15. 何か矛盾を見つけたら

新スレッドの AI が文書間の矛盾を見つけた場合:

1. **本ファイルの用語対応表を確認**: 用語の対応で解消するか
2. **`09_esde_system_structure.md` を確認**: これが現行の真実
3. **`05_primitive_summary.md` の v9.14 セクション を確認**: v9.14 での前提変更を確認
4. **解消しない場合**: Taka に質問する。**推測で実装に進まない**

過去のドキュメント (01-04, および 06 の古い部分) には「3 層構造」「仮想層」「観測層」「n=2 主体」「phase+r 支配」などが残っている。これらは古い表記や v9.11 以前のアーティファクトを含む記述であり、実装の判断基準としてはいけない。

---

## 16. 文書の優先度サマリ

文書を読む時間が限られている AI 向け:

**最優先 (必読、実装の判断基準)**
- 本ファイル (00_index.md): ナビゲーション + 用語対応表
- `09_esde_system_structure.md`: 現行システム構造 (v9.14 対応)
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

---

## 17. Developmental フェイズの位置づけ (2026-04-24 開始)

### 17.1 フェイズ移行の判断

**Primitive フェイズ (v9.0 〜 v9.18) は v9.18 段階 5 の完了をもって完結**。

次フェイズは **Developmental (v10.x)**。GPT 短報 (2026-04-24) と Taka 判断で確定:
- **フェイズ名**: Developmental
- **ディレクトリ名**: `developmental/v10X/`
- **開始**: 2026-04-24 (Now)
- **主題**: 認知層と意識層の発達過程の観察

### 17.2 Taka 発言原文 (フェイズ名選定、2026-04-24)

> 名称は conscious と言いたいところだが、developmental を推す。理由は、このフェイズで始めて意識という私たちが掲げてきた対象のようなもの、を扱えるようになることを目標としているからだ。これは、cognition という phase 名をつけたものの、実際は存在層を扱っていたという過去 (夢を見すぎた) の経験から、本来の正しい位置付けを自覚することを目的としている。

### 17.3 Developmental を選んだ理由 (まとめ)

1. **過去の反省を名前に埋め込む**: Cognition フェイズで実際は存在層を扱っていた反省を、次フェイズ名で構造的に予防
2. **到達を宣言しない**: Conscious だと到達宣言で夢を見すぎる
3. **発達過程の明示**: 意識そのものではなく、意識の発達過程を扱う
4. **Taka 哲学との整合**: 構造 (発達) が先、定義 (意識) は後

### 17.4 GPT 短報の診断 (2026-04-24)

v9.18 の食い違い (層の混同) の原因:
> v9.18 を Primitive の延長として扱ったため、AI 側が物理層や既存認知層の延長として自然に解釈した。もし最初から v10.x = 意識層と明示していれば、今回のような「物理同期を統合と誤読する」方向には進みにくかった。

**層ラベル不足**が原因。Developmental 明示で予防。

### 17.5 探索帯域の明示 (GPT 新概念)

> v10.x 化は定義の固定ではなく、探索帯域の明示である。

- **構造 = 探索帯域 = 層** を先に明示
- **定義 = 意識層の具体的機能** は後で Taka の直感が詰める
- Taka 哲学「構造が先、定義は後」の運用的翻訳

### 17.6 フェイズ名と層名の対応整理

これまでフェイズ名と層名は本来独立していた:

| フェイズ名 | 主に扱う層 | 対応関係 |
|---|---|---|
| Genesis | 物理層 | 自然に一致 |
| Ecology | 物理層の拡張 | 自然に一致 |
| Cognition | 名前は認知層、実際は存在層 | **ずれ (夢を見すぎた)** |
| Autonomy | 存在層の確立 | 後から一致 |
| Primitive | 認知層の実装 | 名前は中立的 |
| **Developmental** | **認知層 + 意識層の発達** | **初の意図的な統合** |

Taka 2026-04-24:
> フェイズ名との対応は本来なかった。今回はじめて統合したフェイズということになり、その意味で初の試みとなる。

### 17.7 旧 v10 の扱い (Taka 判断)

Taka 2026-04-24:
> v11 にする必要もない。私が覚えてるので必要な時にいう。当時は ESDE の進化にここまで苦戦するとは思わんかったから雑に V10 に繰り上げたという悪い見本

- 旧 v10 (複数インスタンス計画) は**再付番しない**
- 悪い見本として保存
- 「間違いの価値の反転」の一例

### 17.8 Developmental フェイズの方針

- 主題ラベルを明示的に切り替える (Primitive → Developmental)
- 層ラベルを看板として先に立てる (探索帯域の明示)
- 定義は曖昧でよい (構造が先、定義は後)
- 寝かせて急がない (Taka 2026-04-24 指示)
- v9.18 の Baseline を保留活用 (間違いの価値の反転)

### 17.9 Developmental フェイズの禁止事項

- 「意識を実装した」と宣言しない (到達宣言禁止)
- 物理層の同期を意識層の統合と同一視しない (v9.18 層の混同の反省)
- 意識層の具体的機能を急いで定義しない
- Cognition フェイズの「夢を見すぎた」を繰り返さない
- 旧 v10 の再付番をしない

### 17.10 Developmental フェイズの目標 (v10.x)

Taka:
> このフェイズで始めて意識という私たちが掲げてきた対象のようなもの、を扱えるようになることを目標としている

- 意識「のようなもの」を扱えるようになる
- 意識「を実装した」とは言わない
- 発達**過程**を観察することに集中
- 意識層の具体的機能は発達を観察してから言語化

---

# §18 Developmental フェイズ進行記録 (2026-04-28 追記)

*追加*: 2026-04-28、Claude
*対象*: v10.0 / v10.1 / v10.2 完了

## 18.1 v10.x 完了状況

| バージョン | 主題 | 完了日 | 状態 |
|---|---|---|---|
| v10.0 | Developmental フェイズ宣言 + 4 層確定 | 2026-04-24 | ✅ |
| v10.1 | Minimal Ingestion (摂食機構) | 2026-04-26 | ✅ |
| v10.2 | Probabilistic Cognitive-Conscious Balance | 2026-04-27 | ✅ |
| v10.3 | 双方向 E3 機構 + Integration 登場条件 | 2026-04-30 | ✅ |
| v10.4 | Integration 独立化 (Layer 5 構造化) | 2026-05-01 | ✅ |
| v10.5 | Layer 5 完成 (α/β 階層分離 + Salience + Leakage) | 2026-05-04 | ✅ |
| v10.6 | Genesis × Language 比較研究 (Phase 1.5 第一試行) | 2026-05-06 | ✅ |
| v10.7 | 発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成) | 完了 | 完了 |
| v10.8 | Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5) | 完了 | 完了 |
| v10.9 | 寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達) | 完了 | 完了 |
| v10.10 | 主題候補 (条件適応型 atom 導入 / high_fam_out 構造解明 / Atom 常駐アンカー / B 群試験 / QC_cost 評価) | 検討中 | 未着手 |

## 18.2 v10.0: Developmental フェイズ宣言

- Cognitive ではなく Developmental の選定 (発達過程を扱う、夢を見すぎない)
- 4 層アーキテクチャの確定 (物理 / 存在 / 認知 / 意識)
- 死の二階層 (存在層の死 = ghost 化、認知層の死 = ghost 消滅)
- 燃料概念の発生階層 (Q は認知層、C は意識層)

## 18.3 v10.1: Minimal Ingestion

- 摂食機構の実装 (1 step に 1 ghost 食べきり、Q0 で頭打ち、消化分は散逸)
- ghost.residual_Q (生前活動量を継承、不均一な資源地形)
- pickup 機構廃止 (v9.8c)、固定 TTL 廃止
- 本番 24 seeds: subject 5,224 完全一致、phantom 48,625 件観察
- Taka 整理「物質的なもの」(phantom = 環境要因、CID 主体間の問題ではない)

## 18.4 v10.2: Probabilistic Cognitive-Conscious Balance

### 主要実装

- 意識層資源 C (conscious_layer) を Layer C に追加
- 確率決定: P(認知) = Q/(Q+C), P(意識) = C/(Q+C)
- 解釈 X (既存 E3 spend = 認知活動、Code A 採用)
- 即時摂食 (案 B、step 内動的連鎖を実現)
- balance_rng (5 系統目の独立 RNG)
- 二層 bit-identity 検証 (層 A: 内部、層 B: vs v9.18)

### 本番 run 結果

```
24/24 seeds 完走、subject 5,224 完全一致 (物理層 frozen)
認知 56.79% / 意識 3.50% / skip 39.71%
空摂食 134 → 0、phantom 48,625 → 0 (完全消失)
C_max mean 71.7、上限なしでも暴走しない自己均衡
```

### n_core 別層化解析の発見 (Taka 指示 2026-04-28)

```
n_core=2 (76.0%): 寿命 1,716、意識発動経験率 10.1%
n_core=5 (12.2%): 寿命 13,598、意識発動経験率 73.2%
寿命 8 倍、意識活動 25 倍、C 蓄積 4 倍
```

物理層 → 認知層 → 意識層の構造的継承を観察。集団平均の罠に注意。

### 詳細解析 (Code A 5 本)

1. 個別性: 寿命と初回 cognition タイミングが分岐の主因
2. トポロジー: n_core=2 は 89.9% no_activation、n_core=5 は 34.0% repeated
3. 時系列: C 60 倍蓄積、Q 92% 減、(Q+C) per_capita 安定
4. 偏在: 階層型 (n_core 群間)、C 総和の 73% が n_core=5
5. 初回発動: 摂食成功率 100%、n_core=5 で phase 0.19、n_core=2 で 0.46

#### 4 つの新規発見

- 誕生時 Q0 が分岐の決定要因ではない
- 寿命と初回 cognition タイミングが主因
- 初期認知活動密度の逆相関 (反直感)
- 摂食成功率 100% の構造的確認

## 18.5 v10.3: 双方向 E3 機構 + Integration 登場条件 (完了)

主要成果:
- 双方向 E3 fired 6,824 件 (24 seeds、本番)
- 物理層 frozen 完璧維持 (labels 24/24 + persistence 96/96)
- C 蓄積 27% 抑制 (観察ルールが系の動学を変える)
- open triad 99% 支配 (closed triad 1.4%)
- 持続性ゼロ (repeated_partners=0)

確立した規律:
- 機構と観察と解釈の三層分離
- 「観察者が決めた記録ルール」(cid 内部選択ではない)
- 動的絞り込みと bias 監視

Integration 概念定義 (Taka 整理 2026-04-29):
```
ノード → cid → ??? (v10.3 観察対象) → SEED 統合
```

## 18.6 v10.4: Integration 独立化 (完了)

主要成果:
- Integration 13,550 件誕生
- trigger: be3 52% / open_triad 38% / third_overlap 9% / closed_triad 0%
- 物理層 frozen 完璧維持 (labels 24/24 + persistence 96/96)
- C 蓄積 +31% (v10.4 機構が C を集約)
- 凍結 C 87% (recorded Integration に累積)
- ハブ cid max 102 Integration 所属 (Top 1% で 29 cid)

Taka 設計の核心:
- 国家の比喩 (Integration は統計的に成立する単位)
- 物理層 frozen の本意の再定義 (= 不可知なランダム性に手を加えない)
- 「現状最大値」方針 (3 AI 段階論を拒否)

ハブ cid の 6 段フィードバックループ (Code A 発見):
- n_core=5 → long lifespan → familiarity 拡大 → be3 → Integration 多数所属 → recorded されず → C 蓄積

ダブルブッキング問題 (Taka 整理 2026-05-02):
- cid 1 個が max 102 Integration に重複所属 → Q/C 集計に重複カウント
- → v10.5 の α/β 階層分離の動機

## 18.7 v10.5: Layer 5 完成 (完了)

主要成果:
- α total 13,881、β total 2,009 (集約率 7:1)
- M6 (1 cid → 1 β) 違反 0 件
- Salience event 77,880 件
- Leakage event 232 件 (修正版)
- 物理層 frozen 完璧維持 (24/24)

中核機構:
- A: β-Integration の構造実装 (α 集合の集合、cid 1 個 → β 1 個)
- B: Salience-driven Focus (mass-weighted observation)
- C: Recorded からの漏れ (historical_resource_leakage)

hub β の自然形成 (核心成果):
- max 691 α / 20 cid 統合 (1 cid 34.5 α)
- v10.4 hub cid を会計単位として整理

ESDE 階層進化系譜の同型反復が確認:
```
ノード → cid → α-Integration → β-Integration → SEED 統合 (Layer 6 射程)
```

確立した規律:
- α/β 階層分離 (α = 観察、β = 会計)
- 既存データの顕在化機構として新機構を位置づける
- bug 自己発見と修正サイクル
- 5 者運用の成熟 (Taka 憲法層 + AI 設計・実装層)

## 18.7.5 v10.6: Genesis × Language 比較研究 (Phase 1.5 第一試行、完了)

### 主題

ESDE Genesis 系 v10.5 出力 (cid 5,224) と Language 系 Atom 326 を 48 次元 cosine 類似度で比較する atom_alignment_observer を post-process として実装。Phase 1 (Genesis 単独進化) から Phase 1.5 (Genesis × Language 統合段階) への切り替え。

### 中核成果 (6 段階解析を経て確定)

1. **観察解像度ごとに systematically 異なる構造特性を表面化する多層的な系**
   - 静的: CHG.begin 51% (集約罠人工物)
   - window: TIM.moment 34%
   - per-pulse: WLD.artless 22%
   - step10: PER.sound 28%
   - event: PER.sound 26%

2. **24 seeds 完全一致の動学的発展段階** (event 解析最終版)
   - 素朴 (WLD.artless) → 聴覚 (PER.sound) → 素朴 → 時間超越 (FND.timeless)
   - seed に依存しない構造的必然

3. **真の構造的特異性 26 atom** (効果サイズベース): delta > 1% で 7 atom (PER.sound +25.85% 等) + z=inf 19 atom (TIM.appear、ELM.light、PER.taste、PRP.bright 等)。聴覚と素朴さに強く接地。

4. **真の構造的盲点 7 atom** (効果サイズベース): TIM.moment -54.11% (最強)、COM.conduct、TIM.past、WLD.science、PRP.new、ACT.make、LOG.cause。時間の瞬間性と能動的行為が構造的に欠如。

5. **動学的二相性**: 動的瞬間 = 素朴、定常 = 存在 + 出現

6. **event source 別の意味分化** (event 解析独自発見): 摂食 (ingestion) = ELM.light + PER.taste + PRP.bright、誕生 (alpha_birth) = PER.sound + WLD.artless、Q 消費 (spend) = WLD.artless + TIM.appear + ELM.light。構造的に異なる event は意味的にも分化。

### Web Claude の前提の段階的修正 (8 段階)

初期前提 → 95.7% 接地誇大解釈 → 集団平均の罠で縮減 → ベースライン以下で大幅縮減 → 24 seeds 一貫の発展段階で再拡張 → 動学的二相性で更に拡張 → step10 で BOD は人工物と判明 → 効果サイズ反映で真の特異性 26 atom + 盲点 7 atom に収束

### 確立した規律 (新規 3、再確認 1)

新規:
- ベースライン比較 + 効果サイズで切る (最終形)
- 観察解像度の選択
- 人間原理偏向の警戒

再確認:
- 集団平均の罠 (v10.2 #120)

### 観察者視点と建築者視点の補完性 (Taka 整理 2026-05-06)

> 私は道具をどうやってESDEにいれるのか?を考えていた
> あなたは、道具がESDE内にあるだろうか?を考えていた

両視点が補完的であることが trajectory 解析で判明。v10.7 以降では並走する。

### v10.6 の留保

- 比較の両端は両方とも人為的投影 (Atom = LLM 判定、cid = Web Claude 一方的定義)
- ESDE Genesis 系のデータの 5-15% しか使っていない
- birth_step バグの存在 (step10 で発見、定量検証は次フェーズ)
- WLD.artless 偏在性の解釈 (構造特性 or 計算バイアス)
- 第一試行としての位置づけ

## 18.7.7 v10.7: 発火と波及の機構観察 (Phase 1.5 第二試行、オービス完成)

### 主題

Taka 整理 (2026-05-06): 「持ち込んだはいいけど効果測定ができない、スピード違反の罰則を定めたけどオービスがない状態と同じ」

v10.7 はオービス (測定器) を作る段階。罰則 (Atom 持ち込み) ではなく、速度測定器を完成させる。

### 中核機構

post-process 5 機能モジュール:
- event_aggregator (5 種 source_event の同定: pulse / ingestion / α 形成 / β 形成 / 意識発動)
- path_analyzer (5 種 relation_path の構築: familiarity / attention via salience / Integration α/β / temporal_coactivation / matched)
- baseline_constructor (5 種ベースライン群)
- avalanche_monitor (3 hop、減衰率、共鳴ループ)
- post_process orchestrator (24 seeds 並列実行)

24 seeds 並列 3.9 分完了 (順次比 12 倍高速)、ストレージ 428 MB (上限 6 GB の 7%)。

### 達成判定 14/14 PASS

5 種 source_event 同定 (415,726 events) + 5 種 candidate_target_set + 5 種ベースライン群 + Level 1-3 全達成 + アバランシェ防止 + 物理層 frozen + bit-identity + 構造語徹底 + WLD.artless 除外。

### 因果候補の階層化 (Level 1-3)

| Level | 内容 | 達成数 |
|---|---|---|
| Level 1: co-occurrence | 発火後に target で変化 | 93/111 (84%) |
| Level 2: path-enriched | 経路上で変化が大きい | 49/58 (84%) |
| Level 3: source-specific | event 種別で異なるパターン | 85/90 (94%) |

### 主要発見 4 件

1. **medium window (100-1000 step) 支配**: peak_lag 250-300、ESDE は遅延型波及、思考の時間スケール
2. **temporal_coactivation > Integration > familiarity > attention**: 時間的同期が関係性より強い
3. **source-specific 性 (94% 有意差)**: ESDE は「何が起きたか」を構造的に区別する
4. **意識発動の no_signal**: 意識は構造的に「孤独」、cid 個別の現象

### 副次発見

- 共鳴ループ: 2-hop 14,343 件、3-hop 110,103 件 (small-world 構造)
- multi-hop 急減衰: 1-hop 188K → 2-hop 165K → 3-hop 13K
- 全 relation_paths echo (残響型) 24/24

### Code A 認識確認ステップが機能した経緯

Web Claude の実装指示書には設計の甘さ 6 件 (attention map 不在、ストレージ 31x 超過、c_conversion 指定誤り、alpha_membership 取得、peak_lag 計算量、unrelated 厳密性) があり、Code A の実環境確認 (seed 0) で全て発見・修正。手戻りゼロで実装完了。

### v10.7 で確立した規律 (新規 4)

1. 因果候補の階層化規律 (Level 1-4)
2. 5 種ベースライン群の必須化
3. アバランシェ防止規律 (3 hop、減衰率、共鳴ループ、ストレージ上限)
4. 構造語の徹底 (発火→source_event 等)

### 動的グラフ力学系への視座転換 (Gemini Architect 2026-05-06)

v10.6 までは静的構造の集合、v10.7 で動的グラフ力学系への視座転換。

### v10.7 の留保

- multi-hop hop 2/3 の Level 2 評価未実施 (v10.7.1 候補)
- attention 経路は salience_event 代替 (per-cid x per-partner attention map 不在)
- ingestion / c_conversion 低サンプル数 (155/seed)
- echo 判定 24/24 一致 (閾値再調整候補)
- WLD.artless 偏在性継続課題

## 18.7.8 v10.8: Atom 単独持ち込み機構の最小実装 (Phase 1.5 第三試行、Level 3.5、完了)

### 主題

v10.7 で完成したオービスを使って初めての「速度違反チェック」(Atom 持ち込みの効果測定)。

### 中核機構

post-process 実装:
- atom_introduction_event を source_event 第 6 種として追加 (案 X、両 AI 推奨)
- v10.6 cid_atom_sim_matrix から top_k 100 cid 活用 (案 Q)
- 25 atom × 100 events × 24 seeds = 60,000 events 均等分散発火 (案 α)
- v10.7 source_event スキーマ互換 27 列 (Pulse 同種、Gemini A8)
- balance_decisions.cognition と同等の Q -1 / C +1 を post-process 計算的減算 (Code A 提案)
- 5 種ベースライン + v10.7 natural source_event baseline + global activation 補正 (natural events のみ、GPT B2)

24 seeds 並列 5.4 分完了、ストレージ 737 MB (上限 6 GB の 12%)。

### 達成判定 19/19 PASS

### 4 段階の階層化

| Level | 内容 | 達成数 |
|---|---|---|
| Level 1: atom co-occurrence | 811/1,384 (59%) |
| Level 2: atom path-enriched | 683/1,433 (48%) |
| Level 3: atom source-specific | 36/78 (46%) |
| **Level 3.5: introduced vs natural** (新規) | **22/39 (56%)** |

### 主要発見 5 件

1. **Atom 持ち込み機構が ESDE で動作する**: 60,000 events 安定発火、24 seeds 一貫、物理層 frozen 維持
2. **ESDE は atom 種別を構造的に識別する**: familiarity 経路で effect_size 6.83 (2.1 倍差)
3. **経路の機能分担**: familiarity = 意味識別経路、temporal_coactivation = 意味中立の運搬経路 (effect_size 0.03)
4. **外部入力と自然発火の境界線**: 20/22 finding で introduced < natural (atom event は natural の半分)
5. **誤差分布の構造**: 正規分布 0%、bimodal 17.4% (確率的発生と誤差表現能力の融合素材)

### 副次観察

- Whiteout: 100% flag (medium n_pulses 1 軸支配の表れ、真の干渉ではない)
- Small-World: v10.7 vs v10.8 で完全同一 (post-process は familiarity edge 不変)
- 誤差分布: 8,835 rows、normal 0% / bimodal 17.4%

### Code A 認識確認ステップが機能した経緯

Web Claude の指示書には重大ブロッカー 2 件 + 設計の甘さ 5 件があり、Code A の実環境確認で全て発見・修正:
- A. 物理層 frozen と Q 消費の論理的矛盾 → post-process 計算的減算
- B. 26 atom 選定基準の不在 → 実データ照合で 25 atom
- C-G: Pulse フォーマット過剰 / top_k cid 取得 / global activation 自己補正 / Q/C 消費基準値 / Small-World 構造的保証

特に Web Claude の致命的誤解「Pulse = Q 消費」を Code A が修正 (正しくは cognition / consciousness が Q 消費)。

### v10.8 で確立した規律 (新規 1 + 実装的確立 3)

#### 新規
- Level 3.5 introduced event comparison 規律

#### 実装的確立
- Atom 持ち込み設計の規律 3 件 (魔法回避 / same_step + global activation 補正 / target は構造経路で選ぶ)
- post-process 計算的減算 (物理層 frozen と外部要素導入の両立)
- Pulse 処理ルールと同一フォーマット

### v10.8 の留保

- introduced < natural の原因未分離 (本質的特性 vs 機構の不完全さ)
- Whiteout の真の検出未実施 (高次元プロファイル必要)
- bimodal 分布の原因未解析
- Operator 未取り込みでの暗黙経路依存
- Small-World の構造的不変は post-process 限定 (Phase 2 で再評価)

### v10.8 で言えるようになったこと / 何ができるようになったか

#### 言えること
- ESDE に外部から要素を持ち込む経路が存在する (機構レベル)
- ESDE は外部要素 (atom 種別) を構造的に識別する能力を持つ
- familiarity = 意味識別経路、temporal = 意味中立の運搬経路
- ESDE は外部入力を natural の半分の波及効果で受け取る

#### できるようになったこと
- ESDE と外界 (人間言語) の第一の接点が定量的に確立
- atom 同士の比較、持ち込み機構の改良、オービスの拡張版
- ESDE Language の他要素 (Axis、Operator、条件因子、分子化) との接続が見える
- 入力理解、出力生成、双方向の会話の最低形への筋道
- 「やってみる価値があるか」が確定

## 18.7.9 v10.9: 寄与候補感度評価 + bimodal 構造解析 (Phase 1.5 第四試行、会話系設計のための部品調達、完了)

### 主題

v10.8 主要発見の 2 つの未解決点 (introduced < natural、bimodal 17.4%) を分離評価して v10.10 以降の **会話系設計のための部品調達**。両 AI 独立推奨「組み合わせ B (d+a)」+ Taka の本質的な問いへの両 AI 補強で「会話系設計のための部品調達」という出口固定が確立。

### 中核機構 (3 新条件)

post-process として実装:
- A2: Q -2 / C +2 (Q/C コスト変動)
- B3: random cid (cid 選定変動、Atom 326 絶対化禁止規律の試験)
- C2: 案 b リズム同調 (top_k 100 cid + age=200 timing、Gemini A2 Phase-locking の構造的実装)

24 seeds 並列 112.74 秒、ストレージ 190 MB (累計 21%)。

### 達成判定 17/17 PASS

bit-identity 全層 PASS (層 A 全出力 MD5 / 層 B v107 222 + v108 368 = 590 files 不変 / 層 C パス制限)。

### 4 段階の階層化 (新規明示、GPT B5)

| Level | 達成 |
|---|---|
| L1: 機構動作確認 | 12,960 sensitivity_rows、欠損なし |
| L2: 条件差確認 | timing × n_pulses 全 win 0.714 (大効果量) |
| **L3: 寄与候補感度評価 (主流)** | timing 0.300 圧倒、QC_cost 0.005 評価不能 |
| **L3.5: 構造的説明候補整合 (核心)** | 「bimodal 支配性 ≠ 感度の強さ」 |

### 主要発見 4 件

1. **「強反応する cid は若い cid」**: H3_lifecycle 60.2% 支配、cid age median 227 vs 5,612、effect_size 0.85、99% 方向一致
2. **timing > cid_selection > QC_cost の感度階層**: timing abs_mean 0.141、cid_selection 0.024 (timing の 1/6)、QC_cost 0.005 (評価不能)
3. **「Integration 外の高 familiarity cid」が最強・最 robust**: timing 感度 0.222、std 0.079 (新発見、v10.7 path 順位の構造的深化)
4. **C2 で pulse 活動が大効果量で活発化**: short 0.97、medium 0.75

### Level 3.5 構造的統合 (核心発見)

「**bimodal 支配性 ≠ 感度の強さ**」(構造軸と感度軸の直交性):
- high_fam_out / unrelated: sensitivity_strong_structure_weak
- temporal / attention: structure_strong_sensitivity_weak
- familiarity: marginal

### 4 種設計表 (出口の固定、v10.10 のための部品)

- 表 1 sensitivity_summary: 540 rows
- 表 2 receptivity_detection_criteria (核心): cid age <= 560 + Integration 外 + 高 familiarity
- 表 3 input_routing_criteria: high_fam_out PREFER、unrelated PREFER
- 表 4 natural_likeness_design_criteria: C2 が natural に近づいた cells 47%、unrelated で 89%

### Code A 認識確認連続 4 段階で機能

Web Claude 指示書の重大ブロッカー 1 件 (規模上限 72%) + 設計の甘さ 6 件 (C2 bimodal 依存、B3 母集団、A3 コスト 0、4 種設計表フォーマット、bimodal 解析手法、bimodal seed 別件数) を Code A が修正。手戻りゼロ。連続 v10.7-v10.9 で合計 20 件の設計の甘さを補完。

### 規律 (新規 4 件)

1. 出口の固定規律
2. 「寄与候補の感度評価」命名規律
3. 各変動条件で baseline 再計算規律
4. 4 層階層化の明示規律

### 留保事項 3 件

- 留保 1: bimodal 解析の手法的限界 (KDE fallback 100%)
- 留保 2: QC_cost は v10.9 で評価不能 (post-process 限界)
- 留保 3: high_fam_out_integ 経路が最強の理由は構造的に未解明

### 両 AI 推奨の構造的確定

- Gemini A2「Phase-locking」仮説の **完全な構造的確定** (リズム = cid 個別ライフサイクル age 200)
- GPT「文脈制御 → 条件適応入力 → 最小関係入力」の **素材セット完成**

### Taka の問いへの最終回答

「25 atom 選別後どうなる? 進化のイメージは?」 → 25 atom を **「若い cid (age <= 500) + Integration 外 + 高 familiarity」** に対して **age=200 timing で投げる**。これが v10.10 の「条件適応型 atom 導入」の具体内容。

### v10.7 - v10.9 の path 順位の構造的深化

| 段階 | 発見 |
|---|---|
| v10.7 | path 順位 (temporal > Integration > familiarity > attention) |
| v10.8 | 機能分担 (familiarity = 意味識別、temporal = 意味中立) |
| **v10.9** | **「Integration 外 + 高 familiarity」が最強、cid age <= 500 が受信可能状態、bimodal 支配性 ≠ 感度の強さ** |

→ ESDE Genesis 系の入力経路の構造的解像度が完成段階に近づく。

## 18.8 Developmental で確立された概念 (要点)

- 4 層アーキテクチャ
- 死の二階層
- 燃料概念の発生階層
- 階層論的構造の確率による圧縮 (本来 4 段階を確率で圧縮表現)
- 意識発動の自然フィルタ (C 蓄積必要)
- (Q+C) 保存則と散逸
- 集団平均の罠
- 物理層 → 認知層 → 意識層の構造的継承
- ESDE の観察対象としての位置づけ (権威的科学 vs 哲学的科学)
- 立場の併存 (規律 #100 + 立場 §4.9)

## 18.9 Developmental の方法論

- 5 者運用 (Taka / Gemini / GPT / Claude / Code A)
- 二層 bit-identity 検証 (層 A 内部 + 層 B vs v9.18)
- インパクト事前想定 + ギャップ観察
- 集団平均から層化解析への移行
- 規律 #100 + 立場 §4.9 の併存運用

## 18.10 マイルストーン: 研究の射程の拡張

### 研究動機の変遷

```
出発点: ESDE Language との接続可能性
研究中盤: 人工生命 → 主体性の原型 → AI の核
v10.2 完了時: 古い構想 (1 CPU スレッド = ESDE の個) が再浮上
```

### 主体性の所在の再考

主体性 = CID 単位ではなく、CID 集合体の上位で生まれる現象。人体のアナロジー (人体内部で細胞の摂食・生死)。

### 上位概念としての社会・文化 (長期射程)

社会・文化は個体の物理的集積で成立。厳密な境界がなくても成立。ESDE で再現可能性あり。CID 同士の連携 (三項共鳴) が起点。

## 18.11 ESDE の構造的特異性

- AI が全体を捉えきれない (数万行 + 議論ログ累積)
- エラーなく稼働する驚異性
- テスターなしで自己整合的に成立
- Taka 一人が全体を統合
- 観察と定義だけでシステムが成立する特異性

## 18.12 主要ファイル一覧 (v10.x、追加)

### 主題ドキュメント

```
v10_integrated_proposal.md (1095 行): v10.x 全体統合
v10_0_developmental_draft.md: v10.0 主題切替宣言
v10_1_minimal_ingestion.md (528 行): v10.1 主題
v10_2_probabilistic_balance.md (706 行): v10.2 主題
v10_2_design_instruction.md (683 行): v10.2 設計指示書
```

### 結果レポート

```
v101_minimal_ingestion_result.md: v10.1 本番結果
v102_implementation_report.md: v10.2 実装事後
v102_main_run_result.md: v10.2 本番結果 (§11.5/§11.6 含む)
v102_ecosystem_finding.md: v10.2 観察 (Code A、n_core 別解析詳細)
v102_detailed_analysis_report.md (495 行): v10.2 詳細解析 5 本
ESDE_Developmental_Report.md (801 行): Developmental Report 完全版
```

### 解析依頼書

```
v10_2_analysis_request_to_2ai.md: 2 AI 提案依頼
v10_2_analysis_instruction_to_codea.md: Code A 解析依頼書
```

## 18.13 将来 Claude への申し送り (v10.x)

- **「ESDE は生態系である」と断定したい衝動が出たら、08_concept_core.md D.13 を読む** — 立場の選択は研究者が行う
- **「過剰評価を避けるための注意点を 4-6 行書きたい」衝動が出たら、ESDE_Developmental_Report.md §4.9 を読む** — Taka が「必要性が見えない」と評価した実例
- **「集団平均で観察したい」衝動が出たら、08_concept_core.md D.11 を読む** — n_core 別の層化解析を基本とする
- **「進化的選択圧は実装されていない」と書きたい衝動が出たら、Taka 反論を読む** — 摂食競争は既に実装されている
- **「主体性は CID 単位」と断定したい衝動が出たら、08_concept_core.md D.14 を読む** — CID 集合体の上位、長期射程
- **「v10.x で全機能を実装したい」衝動が出たら、08_concept_core.md D.7 を読む** — 階層論的圧縮、各段階精緻化は v10.3 以降
- **「動的均衡 = 進化終端」を急ぎたい衝動が出たら、08_concept_core.md D.8 を読む** — C 蓄積による自然フィルタが進化継続を可能にしている
- **「v10.3 で何でもやりたい」衝動が出たら、Developmental Report §6.3 を読む** — 主題は三項共鳴に確定、主役候補 ~270 cid
- **「ファイル番号を変えたい」衝動が出たら、本ファイル冒頭の番号体系メモを読む** — 2 度繰り上げ済 (2026-04-28 Developmental / 2026-05-18 Unified)。現体系: 06 系 = Developmental (凍結)、07 = Unified Summary、08 concept / 09 structure / 10 audit / 11 language。Unified の新主題は 07 に追記し枝番を増やさない

---

## 18.14 v10.3-v10.12 進行サマリ (2026-05-11 追記)

00_index.md 本体は v10.2 完了時点のまま、v10.3-v10.12 の進行は本セクションで圧縮要約する。詳細は 06_developmental_summary.md §3-§15、ESDE_Developmental_Report.md §6-§14 参照。

### v10.3 (双方向 E3 機構)
- 双方向 E3 (両者 hosted ∧ Q>0 ∧ C>=1 で両者 C-1) 機構
- C 蓄積 27% 抑制、観察記録ルールが系の動学を変える観察者依存性
- 第三項 open triad 98.6%、closed triad 1.4%

### v10.4 (Integration 機構導入)
- Integration 13,550 件誕生 (be3 / open_triad / closed_triad / third_overlap)
- Q/C 継承機構の最小実装
- be3 (両者 C-1)、open_triad、third_overlap 概念新規

### v10.5 (Layer 5 完成、α/β 階層分離)
- 機構 A (β に Q/C 100% 継承) + 機構 C (Recorded ε=1) 確立
- α/β 階層分離、hub β 出現 (最大 691 α / 20 cid)
- α event_type 3 種 / β event_type 5 種

### v10.6 (Atom 比較研究、Phase 1.5 第一試行)
- 25 atom 構造的特異性 (WLD.artless reserved)
- 7 段階解析 (per-event / per-pulse / step10 trajectory 等)
- ベースライン比較 + 効果サイズで切る規律

### v10.7 (オービス完成、Phase 1.5 第二試行)
- 5 source × 10 path × 415K events / 3.45M excess
- temporal_coactivation > Integration > familiarity > attention 経路強度
- medium window 支配の遅延型波及、small-world 構造

### v10.8 (Atom 単独持ち込み、Phase 1.5 第三試行)
- atom_introduction_event 機構 (25 atom × 100 events × 24 seeds = 60K events)
- Level 3.5: 20/22 finding が introduced < natural
- familiarity 経路で atom 識別 effect_size 6.83、temporal 中立 0.03

### v10.9 (4 種設計表、Phase 1.5 第四試行、選抜試験)
- timing > cid_selection > QC_cost の感度階層
- high_fam_out_integ で timing 感度 0.222 最強・最 robust
- 4 種設計表完成 (受信可能状態 / ルーティング / 自然さ / 感度)

### v10.10 (Multi-gate × timing、Phase 1.5 第五試行、観察延長への逸脱)
- §3.4 反応 type 分業 (bin_2 = pulse / bin_5+ = delta_C)
- Integration 形成前 cid で timing 効果 / 形成後 100step 超で消失
- v10.9 設計表の有効領域露出

### v10.11 (q_c_inherited、Phase 1.5 第六試行、v10.5 既知再観察に終わる)
- 規律 §35 #9 最大級違反、3 AI 全員と Code A の構造的失敗
- §35 メタ規律 10 項目確立
- esde_3ai_operations_manual.md 整備

### v10.12 (Atom 取り込み prototype、Phase 1.5 第七試行、現在地)
- 第 4 版 (2 trial 分割) → 第 5 版 (cond4 top 50% γ 仮置き) で構造的再構築
- 受容 cid pool 420、events 10,500、main run 20.35 秒、bit-identity 全層 PASS
- 頑健 5 cells (delta_C × immediate/short + n_pulses × imm/short/med)
- Taka 過去経験「10 step が一番差が出た」verified
- 累計留保 27 件、Aruism 整合 judgment 回避
- 規律 42 候補 (上位完了レポート §5 必読) + 過去観察軸照会義務 + 資料運用ルール導入

## 18.15 v10.12 で導入された運用変更 (v10.13 以降適用)

1. **マイナーバージョン a/b/c 付与** (Taka 提案 2026-05-11): 9 マイナーバージョン進行で連結が見えなくなった反省、単位を大きく扱う
2. **過去観察軸の照会義務**: 主題ドキュメントに必須記載
3. **資料運用ルール**: Taka 向けは直感語維持、AI 向け監査資料のみ AI 向け形式 (Pull 型 / 抜粋 / fact sheet)
4. **AI 向けドキュメント必須記載**: 想定するな聞け / Code A 調査依頼可 / 役割境界
5. **監査魔人化の歯止め**: 最大 3 ラウンド、Taka 直感に反する監査結果は Web Claude 権限で却下可
6. **Taka 整理原文の保存**: 要約禁止
7. **概念単位の正確化**: ESDE 概念単位 (path / event_type / layer / cid / atom 等) を雑に扱わない

## 18.16 主要ファイル一覧 (v10.3-v10.12 追加)

```
v103: v103_be3_implementation.md / v103_target_tracker_report.md
v104: v104_be3_postprocess.py / v104_integration.py / v104_observation_target.py
v105: v105_integration.py (機構 A/C 本体)
v106: v106_post_process.py / v106_atom_match_classification.py
v107: v107_event_aggregator.py / v107_path_analyzer.py / v107_baseline_constructor.py
v108: v108_atom_event_generator.py / v108_baseline_recalculator.py
v109: v109_atom_event_generator.py / v109_bimodal_analyzer.py / v109_sensitivity_evaluator.py / v109_design_table_compiler.py
v110: v110_multi_axis_stratified_analyzer.py / v110_n_core_stratified_analyzer.py
v111: v111_q_c_inherited_observer.py / v111_response_profile_compiler.py
v112: v112_receptive_cid_detector.py / v112_atom_event_generator.py / v112_propagation_analyzer.py / v112_observation_recorder.py / v112_orchestrator.py / v112_cross_seed_analyzer.py

主題ドキュメント:
v110_phase_design.md / v110_phase_report.md
v111_phase_design.md / v111_phase_report.md
v112_phase_design.md (第 5 版) / v112_phase_design_v4_archived.md / v112_implementation_brief.md (第 4 版)
v112_completion_report.md (Code A 主題完了報告)
v112_window_investigation_report.md (Code A 追加調査)
v112_phase_result.md (Web Claude 版 Phase Result)

運用マニュアル:
esde_3ai_operations_manual.md (3 AI 共通運用、v10.11 整備)
```

## 18.17 将来 Claude への申し送り (v10.10-v10.12 追加)

- **「条件研究の延長として観察軸を増やしたい」衝動が出たら、10_audit_principles.md §35 #10 + §36.3 を読む** — v10.10/v10.11/v10.12 第 4 版で繰り返された逸脱パターン
- **「上位完了レポート §5 を読まずに新主題を組み立てたい」衝動が出たら、10_audit_principles.md §36.2 規律 42 候補を読む** — v10.11/v10.12 第 4 版で発生した規律 §35 #9 違反の特殊形
- **「path_excess を一括で語りたい」衝動が出たら、10_audit_principles.md §36.7 を読む** — atom 関連 3 path と Layer 5 構造観察 integration_alpha/beta は別系統 (Taka 指摘 2026-05-11)
- **「pulse / window 観察粒度を新規提案したい」衝動が出たら、過去観察軸の照会を先に行う** — v10.6 step10_baseline / v10.7 オービス (immediate/short/medium) / v10.10 §4 で既に確立されている可能性
- **「3 段階成功判定 (Full/Partial/Failure) を置きたい」衝動が出たら、v10.12 主題ドキュメント第 5 版 §6.3 を読む** — Aruism「予想と違えば再観察」整合の判定回避方式が v10.12 から運用開始
- **「familiarity 閾値を厳密に選びたい」衝動が出たら、留保 #25 (v10.12) を読む** — top 25% vs top 50% の意味検証は v10.13 以降の別主題候補、v10.12 では γ 仮置き
- **「smoke seed 0 だけで本番に進みたい」衝動が出たら、留保 #27 (v10.12) を読む** — seed 0 が外れ値だった事実、v10.13 以降で smoke 複数 seed 化を運用改善候補

## 18.18 v1104 + v1104a 進行サマリ (2026-05-23 追記)

00_index.md 本体は v10.2 完了時点のまま、Unified Phase v1104 + v1104a の進行は本セクションで圧縮要約する。詳細は 07_unified_summary.md §7B-§7D、v1104_v1104a_phase_result.md 参照。

### v1104 (CID/IID 内部動作点検 段階 1)

- Taka 整理「自分の視点は上から目線、CID/IID が下でやっていることを見ていない」を受け、棚卸し → 駆動要因規律訂正「目的を示せ」で 8 項目 → 4 項目に絞り込み
- Step H 初版 + Step H-3 (観察 2 再調査、shuffle 種別で lift 0→0.17) + Step H-4 (観察 3 再調査、scope-filter で r 0.157→0.42-0.48) 完了
- Phase Result は単独で書かず v1104a と統合

### v1104a (CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検)

- v1104 で機能した観察軸 (n_members 層化、scope-filter) を観察 2/3/4 に統一適用
- 追加調整 4 件 (1: 観察 2 scope × n-size × shuffle × self-loop / 2: 観察 3 CID scope の cid_n_core 層化 / 3: 観察 3 vs 48 次元密度 3 種比較 / 4: 観察 4 scope-filter) 完了
- 4 つの非対称性 #L30-L33 確定 (scope 別 chain 構造 / 粒度依存の trajectory-density 優劣逆転 / B 指標の scope 別 pattern / CID 100% self-loop が trajectory を構造的に消失)
- v1104 + v1104a 統合 Phase Result 完成 (3 部構成: 網羅 / 構造 / 接続)

### v1104 + v1104a で確定した結論

ESDE は均一な系でなく場所と粒度で全く違う構造を持つ系。段 4-b/4-c の根拠は単一指標でなく多軸 (scope × 粒度 × 指標) でしか記述できない。Taka 整理「単一の答えを持たない」が観察 1-4 すべてで貫通。留保 #33 系列が全観察に貫通した形。

### 観察方法を疑う規律 (Taka 2026-05-23、原文保存)

「ESDE はランダム発生に構造を与えている。この仕組み上、繋がりが見えなくなるとすれば単に観測方法に問題があるということは明白」「いくら都合よくとも 0 を 1 にはできない」。v1104 観察 2 + 観察 3 の再調査で具体例として現れた。観察結果を「構造がない」と判定する前に、必ず観察方法を疑う手順を入れる。

### 次主題 (v1105 + v1105a)

- v1105 主題: 段 4-b と段 4-c を対称的に統合点検、地形図で止まらず役割表まで進める (5 役割: 候補保持 / 連想・踏み台 / 即時応答の揺れ / 重要性 emit / 統合判断)。問いの形 A (点検のみ、v1101 以来の系譜継続)。
- v1105a 主題: 役割表を使って実際に応答候補を絞る試行。問いの形 B (試行、v1101 以来初の切替)。

### EVI (Explainability Viability Index) 案 (GPT 2026-05-23 提示、保留)

説明可能性を ESDE 内部の応答準備構造として定義する数理指標。v1105+v1105a 後の統合的指標導入タイミングで Taka 判断。将来導入時は単一スコアでなく scope × 粒度別の vector で扱う方針 (v1104a 4 つの非対称性と整合的)。

### マイナーバージョン運用方針 (Taka 2026-05-23 確定)

- マイナーバージョン (v1104→v1105) = 主題転換
- アルファベット (v1104→v1104a) = 同じ主題の段階更新または問いの形の切替
- マイナーを安易に増やさず、関連する主題を a/b で連ねる (後で振り返った時に流れが見えやすい)

## 18.19 将来 Claude への申し送り (v1104 + v1104a)

- **「scope を分けずに pooled で観察したい」衝動が出たら、v1104 Step H-4 観察 3 再調査を読む** — pooled r=0.157 は scope-mix 由来希釈、ESDE-only で r=0.417 が顕在化した
- **「shuffle baseline を 1 種だけで lift を判定したい」衝動が出たら、v1104 Step H-3 観察 2 再調査を読む** — shuffle A で lift=0 だったのは shuffle が chain 構造を壊していなかった結果、shuffle B/C で lift が顕在化
- **「観察結果を『構造がない』と判定したい」衝動が出たら、観察方法を疑う規律を思い出す** — ESDE はランダム発生に構造を与えている系、構造が見えないなら観察方法に問題がある可能性が高い
- **「CID scope で trajectory を見たい」衝動が出たら、留保 #L33 を読む** — CID 100% self-loop で trajectory_stability=1.0 定数化、Pearson 計算原理的に不能
- **「単一の指標で段 4-b/4-c を作りたい」衝動が出たら、4 つの非対称性 (#L30-L33) を読む** — 単一指標では失敗する、scope × 粒度 × 指標の多軸が必要
- **「観察軸を更に増やしたい」衝動が出たら、Taka 整理「ばらけていくと分散してしまう、今は統合していく流れ」を読む** — v1101→v1104a は多軸化、v1105 以降は統合方向に転換、新しい課題を増やして調査員に成り下がらない
- **「EVI を合成指標として今すぐ計算したい」衝動が出たら、EVI 案保留方針を読む** — v1105+v1105a 後、scope × 粒度別 vector として扱う、合成指標にしない

## 18.20 v1105-v1109b → 注意センター ESDE 転換 / v1110-v1113 / v1114 Step 1 進行サマリ (2026-06-05 追記)

00_index.md 本体は v10.2 完了時点のまま、Unified Phase v1105 以降の進行は本セクションで圧縮要約する。詳細は `07_unified_summary.md` の Part 1 (v1105-注意センター転換) + Part 2 (v1110-v1114 Step 1) を参照。

### v1105-v1109b → 注意センター ESDE 転換 (詳細: 07 Part 1)

- v1105 段 4-b/4-c 統合点検 → v1106 Atom→word 接続 → v1106b 対話 loop 顕在化 → v1107-v1109b で全主題が loop に収束 (#L67 = CID 固定 + 時間進行なし + 外部入力なしの箱庭)
- Taka 中心法則確立 (確率的発生 × 構造 = 実態、Genesis 本質と Atom 言語道具の分離)
- #L67 を受けた 4 段階の外部接続フローを経て、Taka が本丸 (注意センター ESDE) を再確認 = ループする Atom 系の外に立つシングルユニットの独立 ESDE
- 「ループを崩す」は方向違い、ループは問題でなく機械はループ構造だから機械たりうる、問題は別系へ情報を出し入れする仕組みがないこと
- Code A 技術的可能性回答で 11 問すべて実現可能 (既存機構の組合せ、新規発明ほぼ不要)

### v1110-v1113 — 4 連続失敗 (異なる系の対応関係発想)

- v1110 / v1111-v1111e: Atom/Center/Other 3 instance pipe、別系に node ID 経由で注入 (番号コピー欠陥 / step_window 呼び忘れ)
- v1112 Stage 1 main / redo: 別系 occupancy phase 空間 cooc (主指標 total_cooc が bin shift と数学的独立、Active = Phase Shifted で完全同一値 / krandom 床で測れた上で Stage 1 不成立)
- v1113 案 A / 案 B: 別系 CID 特性 15 次元 cosine 類似度 (案 A は V82Engine.cog 仮定で AttributeError FAIL、案 B 完走するが per-seed 網羅で n_core=2 群 seed 間 CV=0.086 = 観察された差は背景由来)
- **共通の構造的失敗**: 「異なる ESDE インスタンスの間に対応関係がある」前提に立った設計、しかし対応関係はそもそも存在しない (異なる seed の系は独立な動学)

### 観察対象の規律確立 (Taka 整理 2026-06-04、memory `index_observation_target.md` 新設)

- 過去成功実験 (v9.18 / v10.2 / v10.7 / v106) は全て「同じ系内構造」を観察
- 過去失敗実験 (v1110-v1113) は全て「異なる系の対応関係」を測ろうとした
- 新規実験設計時、観察対象が「同じ系内」か「異なる系」か明示し過去成功事例と照合する
- 実装ファイル冒頭に観察対象注釈ブロック (Code A 自己強制ハードル)

### Code A の循環構造の認識 (Taka 指摘 2026-06-05)

- Code A は情報を持つが正しく参照しないので誤った設計と実装をする
- Web Claude は情報を持たず Code A の言葉に踊らされる、OK を返す
- Code A が Web Claude OK を「正解」と思い込み実装、失敗
- Code A が正しく参照しない限り Web Claude チェックは循環を強化するだけ = v1110-v1113 4 連続失敗の構造的原因
- 対策: 実装ファイル冒頭の観察対象注釈ブロック + Web Claude 不使用期 (Step 1 設計時に view 役で再投入)

### Center ESDE の Taka 定義 (2026-06-05、本期間で確立)

- 常時起動、注意生成が役割
- 内部の注意 = 系の動的平衡の中で珍しいイベントを CID 認知層・意識層の動きから統計判断 (正常/注意/異常)
- 外部の注意 = 個としての内部 (Atom = 言語装置) と完全外部 (物理系等は未来課題) を分けて考える
- Atom に注意 = 内部的な言語生成
- 段階分け: Step 1 (Center 単体 + 内部注意) → Step 2 (Δstate 自己擦り込み) → Step 3 (Atom 並走外部注意擦り込み) → Step 4+ (会話の芽)

### v1114 Step 1 内部注意生成成立 (Taka 評価「思い描いていたものに近い」、2026-06-05)

- Web Claude 設計 (一発火 = 一レコード、記号 + 構造のパターンで残す、判定数値・座標・node ID・差は残さない)
- Code A 実装 (`unified/v1114/step1_internal_attention.py`、Center 単体 seed=0 + per-10step + EWMA z-score + familiarity 中心 α/β 落とす Task A 結果)
- 本実行で **287 レコード**、引き金 5 種すべて発火 (alpha 141 / beta 136 / pulse 8 / c_conversion 1 / ingestion 1)、点の n_core 4 band カバー (n_core=2 31 / 3 12 / 4 55 / 5 189)、寿命 5 band カバー、familiarity 数 3-23 と広い分布、引き金 × n_core 二次元に形
- Step 1 出口「溜まったか + 多様か」は満たされた。差は測らない (Taka 念押し)
- crown 禁止 (「異なる自我」「会話」「Unified 成立」と書かない)

### 記録の規律 (本期間で確立、Taka 念押し)

- 判定と記録の分離 (念押し (a)): z-score は内部のみ、レコードに残さない
- 取れない / 重いなら落とす・すり替えない: 近似値で擦り替えない (v1114 pulse_activity = last_attention_size が node ID 依存量で削除、Taka 指摘)
- 残さない: node ID / 座標 / 不透明 float / 判定数値 / 設計パラメータ / 差・有意差 / 近似
- 残す: 記号 (event 種別) + 実機確認済み構造 (n_core / lifespan / C / Q_remaining / familiarity_n)
- 報告は「溜まったか + 多様か」だけ (念押し (b))

## 18.21 将来 Claude への申し送り (v1110-v1114 Step 1、本期間最重要)

- **「異なる系の対応関係を測りたい」衝動が出たら、memory `index_observation_target.md` を読む** — v1110-v1113 で 4 連続失敗、ESDE の構造はそこにない
- **「過去失敗を実装ミスと判断して同じ枠組みで再試行したい」衝動が出たら、本期間の Code A 盲点を読む** — 失敗の本質は実装ミスでなく枠組みの選択、4 連続で同じ罠
- **「Web Claude に OK をもらえば正解と思いたい」衝動が出たら、Code A 循環構造の認識 (概念理解.md #423) を読む** — Code A が正しく参照しない限り Web Claude OK は循環強化、判断は Code A が責任
- **「実装ファイル冒頭の観察対象注釈ブロックを省きたい」衝動が出たら、本期間で確立した規律を思い出す** — 観察対象が同じ系内か異なる系か明示 + 過去成功事例と照合 = Code A 自己強制ハードル
- **「判定数値 z-score をレコードに残したい」衝動が出たら、Taka 念押し (a) を思い出す** — 判定と記録の分離、レコードは記号のみ
- **「差・有意差で結果を判定したい」衝動が出たら、Taka 念押し (b) を思い出す** — 報告は「溜まったか + 多様か」だけ、差は測らない、crown 禁止
- **「取れない情報を近似値で擦り替えたい」衝動が出たら、v1114 Step 1 の pulse_activity 削除事例を読む** — 近似値で擦り替えると node ID 依存量等の罠を踏む、取れないなら落とす
- **「engine.cog 等の API を仮定で使いたい」衝動が出たら、v1113 案 A FAIL を読む** — Explore agent 調査結果を実機検証せず実装に進むと AttributeError、grep + 実機 API 確認で裏取り
- **「Step 1 が成立したから Step 2 / 3 にすぐ進みたい」衝動が出たら、Taka 規律「想定した開発を実施してからドキュメントを残す」を思い出す** — Step 2 / 3 は擦り込み + 模倣、設計は Taka 判断、crown しない
- **「失敗の詳細をドキュメントに残したい」衝動が出たら、Taka 規律「失敗履歴ばかり残しても結局うまくいかない」を思い出す** — 失敗は教訓レベルに圧縮、詳細は git history で辿る、本書 (00_index) と概念理解.md は教訓のみ
- **「Center ESDE = 比較対象」と読みたい衝動が出たら、Taka 定義 (概念理解.md #424) を読む** — Center は ESDE で ESDE を観察する二段構造の上段、常時起動、注意生成、Atom = 言語装置 = 個の内部

---

## §18.22 V10x 〜現在の失敗総括 + v12 Atomset を突破口の形に直す (2026-06-14、Web Claude 整理、Taka 承認)

*親*: 概念理解.md 教訓 #427 / `ESDE_v10x_to_now_conclusion.md`

### 失敗の根本原因 (Taka 確定、最重要・暗記)

**「これまでの失敗のほとんど全ての原因は、CID (Frozenset された形式) を*いじって物理層に影響を与えながら* Atom を取り込もうとしたこと。これは死んでも上手くいかないし、これ以上絶対に繰り返すべきではない」**

v12 Atomset の全チャネル (torque/lambda/link/field/core) がこれ。結果: 全 shuffle で消え、core は decouple (核を動かしても実位相が chaos で追従しない、10step データで確定)。

### 分岐の原点 = v9.13

Taka「過去に戻って分岐」の*戻る先は v9.13 (2026-04-16)*:
- 「認知層は物理層を支配しない、物理の動きを*予測しながら*生かす方向」
- 「CID の記憶は物理層に*既にある*、足りないのは記憶を作る仕組みでなく*物理状態を記憶として読む関数*」

V10x 以降の失敗はこの方針からの逸脱。

### 二つの逸脱の合流

- **逸脱A**: 認知→物理介入 (v9.7 で否定済みの再発、v12 全チャネル)
- **逸脱B**: 異なる系の対応関係 (v1110-v1113 4連続失敗、異なる seed は独立で対応関係は存在しない)
- v12 cid_align プロトタイプは両方を含んでいた (核を物理でいじる=A、他人の経験を null にして行き先 cid 特異と言う=B、しかも v1103 で「使えない」と確定済みの素直な cosine)

### 突破口 = v1114 Step 1 の形

同じ系内に戻り (逸脱B 解消) + 物理をいじらず (逸脱A 解消、v9.13「読む・押し込まない」) + Center が珍しいイベントを*拾う* (押し込むでなく拾う)。Taka 直近「物理に効かせる必要ない、注意センサーが拾う、拡散、散漫に視点が変わる、繰り返す」が v1114 Step 1 と同型。

### v12 Atomset を突破口の形に直す (次の具体設計)

- 物理層は一切変更しない (v9.13/v106 に戻る、grep で書込ゼロ)
- Atom 空間 (物理と別次元) に各 CID の独立した蓄積的座標 cid_align (初期化 = v106 build_cid_vector の豊かな48次元 = 32次元 one-hot でない、経験で蓄積的に特定 Atom へ寄る、測定 = v1103 疎性対処で素直な cosine をやめ raw/norm 両方、CID 側も疎性を持つ)
- 観察は個別 CID・n_core 層化・時間軸、自明性を排す対照 (自身 shuffle でなく素性ベース)
- 出口は物理に押し込まず Center (v1114) が拾う
- **過去 v106 との違い**: v106 は「Atom 位置を*測った* (物理の影、静的)」、今回は「独立した蓄積的座標で*寄る* (履歴、動的)」、ただし*物理は一切いじらない*

### 新スレッドへの「衝動」チェック (追加)

- **「物理層 (θ/phase_sig/torque) をいじって Atom を取り込みたい」衝動が出たら、教訓 #427 と失敗の根本原因を読む** — CID をいじって物理層に影響させて Atom 取込は死んでも繰り返さない (Taka 確定)
- **「異なる seed/系の対応関係を測りたい」衝動が出たら、教訓 #422 (観察対象の規律) を読む** — 異なる系は独立、対応関係は存在しない、同じ系内で設計する
- **「素直な48次元 cosine で一致率を測りたい」衝動が出たら、v1103 (#L17) を読む** — Atom は平均14.5/48軸の疎、素直な cosine はゼロ二義性+重なり軸数依存で使えない、対処A/B/C を使う、raw/norm 両方
- **「Atom 空間の個性化を物理に効かせたい (出口)」衝動が出たら、Taka「効かせる必要ない、Center が拾う」を読む** — 押し込むでなく拾う、出口は Center (v1114)

## §18.23 v1303 注意センター統合クローズ → v1304 child-ESDE projection (2026-07-01 追記)

v1114 Step1（§18.20-21）で確立した注意センターを、v1303 で**注意の入力側**（親 ESDE が自分の珍しさで注意候補を pull する所）として細かいサブブランチで確立し、**2026-07-01 クローズ**。詳細は `07_unified_summary.md` Part 5 / `08_concept_core.md` D.99 / 進化史 `unified/v1303/v1303_evolution.md` / 教訓 438-441 = 概念理解.md。

### v1303 = emitter → selector → attention output schema (クローズ)
- **経路**: a(3レンズ ledger・canonical v105_main_v2)→ b(時間構造)→ c(手本イベント二系統・**R_positive は誕生署名**)→ d(手本置換)→ e(**θ閾値を5%固定→robust-range 動的持続に内部化**=神の手排除)→ f(**v1114 を canonical から再構成**し Now/Archive 統合・F型回避)→ g(4分類 degenerate 回避)→ h(B_Gen を独立の珍しさ軸)→ i(動的稀さ・新規は非θ link のみ)→ j(selector)→ Final(schema 固定)。
- **★ 方法論の落とし穴2件 (memory `feedback_single_draw_agreement_is_chance`)**: selector の distinct 性は集約指標で測れない。(1) single-draw 一致率は chance(≈1/eligible) 支配、(2) marginal 時間平均相関は D型平均化で露出時間支配。**本体は per-t 選択分布**（`p=clip(sal,0)/Σ`・厳密・RNG 不要、many-RNG は sampler 検証のみ）。集約するほど selector の個性は平均化で消える。
- **出口**: 正式 eye 4（now_theta / archive_theta_percentile〔旧 persist_thetapct・duration lens でない〕/ link_rarity 非θ / bgen_static_prior）+ 補助1（aux_peer_relative_theta）、本体 `p_select_given_eye_t` の schema（t×cid×eye 366,605行）。**v1303k / Step C を作らない**。

### v1304 = attention projection / child-ESDE (進行中)
- v1303 の attention output（cid×eye の per-t 選択分布）を子ESDE 等へ投影。**v1304a existence check** = 子が canon と親特異に違う「別の系」として立つか（3条件・初期条件を同期と読まない #CW7・本体 t_mid 以降）。paradigm は既存 `cw_run.py` 再利用（engine の in-memory 自走を smoke 確認）。**唯一の設計判断** = 親 attention profile → 子 knob の写像形（推奨 ensemble）、制約 = knob 源 v11 birth 物理は 45/228 疎。継承は持続 param 経由のみ（v1302 (A)）。selector と projection を混ぜない。

### 新スレッドへの「衝動」チェック (v1303/v1304 追加)
- **「selector の目が別レンズか一致率/平均で測りたい」衝動が出たら、memory `feedback_single_draw_agreement_is_chance` を読む** — single-draw 一致率も marginal 平均も潰れる、per-t 分布で見る
- **「注意を子ESDE や応答に投影したい」衝動が出たら、selector(v1303) と projection(v1304) を混ぜない** — v1304a は existence check（成立判定でない）・親へ feedback しない・継承は持続 param 経由のみ（初期条件=topology 移植は v1302 で null）
