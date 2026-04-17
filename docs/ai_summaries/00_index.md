# ESDE 研究史 — AI 向け超要約 (Index + 用語対応表)

*作成日*: 2026-04-11 (v9.9 Long Run 進行中)
*更新*: 2026-04-17 (v9.13 完了、S≥0.20 撤去による前提変更を反映、05b/05c addendum を 05 に統合)
*対象読者*: ESDE-Research に新規に関わる Claude (新スレッド初見)

---

## このディレクトリの目的

ESDE 研究の各フェーズ (Genesis / Ecology / Autonomy / Cognition / Primitive) と哲学的コア (概念理解) を、未来の Claude が **context に乗せても暴走しない最小サイズ** に圧縮したもの。

各原本 (200-1300 行) の要点だけを抽出し、却下された方針 (失敗の記録) を必ず残してある。**未来の Claude が同じ失敗を繰り返さないため**。

---

## ⚠️ 警告

- これは**要約**であり原本ではない。設計の詳細や個別実験の数値が必要な場合は必ず原本 (`docs/ESDE_*_Report.md` および `docs/概念理解.md`) を参照すること。
- **要約の最新時点は v9.13 完了 (2026-04-17)**。05, 06, 07 は v9.13 対応済み (05 は旧 05b/05c addendum を統合済み)。01-04 は v9.9 時点のまま (古い表記が含まれる、本ファイル末尾の用語対応表で確認)。
- **推測補完していない**。原本にあることだけ抽出している。「書いてないこと」を埋めようとしないこと。
- 概念理解.md からの引用は **必ず引用形式 (>) で残してある**。Taka の発言を勝手に言い換えないこと。

---

## 推奨読書順序

```
00_index.md (このファイル)
  ↓ ★末尾の「用語対応表」を必ず最初に読む
06_concept_core.md      ← 哲学コアと絶対ルールを把握 (v9.13 対応)
  ↓
01_genesis_summary.md   ← 物理層 (床) の確立 (古い表記あり)
  ↓
02_ecology_summary.md   ← observer 複数性 (古い表記あり)
  ↓
03_autonomy_summary.md  ← label 自律性、5-node 転換点 (古い表記あり)
  ↓
04_cognition_summary.md ← ★ 失敗の記録 (最重要、古い表記あり)
  ↓
05_primitive_summary.md ← Primitive phase 全体 (v9.0-v9.13、v9.13 対応、旧 05b/05c 統合済)
  ↓
07_esde_system_structure.md ← 現行システム構造 (v9.13 対応)
```

**急ぎなら**: 本ファイル末尾の **用語対応表** + `07_esde_system_structure.md` + `05_primitive_summary.md` の v9.13 セクション の組み合わせで現状作業に最低限着手できる。**ただし `04_cognition_summary.md` の「却下された方針」は時間を作って必ず読むこと**。

---

## ファイル一覧

| # | ファイル | 原本 | 内容 | 更新状況 |
|---|---|---|---|---|
| 00 | `00_index.md` | (このファイル) | ナビゲーション + 用語対応表 | **v9.13 対応** |
| 01 | `01_genesis_summary.md` | ESDE_Genesis_Report.md (638 行) | 物理層の確立、5 Forces、観察者 k\*=4、N=10000 まで scale 不変 | v9.9 時点 (古い表記あり) |
| 02 | `02_ecology_summary.md` | ESDE_Ecology_Report.md (242 行) | observer 複数性、global は lossy compression、long_drift がデフォルト | v9.9 時点 |
| 03 | `03_autonomy_summary.md` | ESDE_Autonomy_Report.md (749 行) | label = 魂 (frozenset)、territory = 場、5-node 転換点、Lifecycle Instrumentation | v9.9 時点 |
| 04 | `04_cognition_summary.md` | ESDE_Cognition_Report_Final.md (1271 行) | **★最重要・最複雑**。v3-v7 の試行錯誤、「物理層は床」結論、virtual layer の確立 | v9.9 時点 |
| 05 | `05_primitive_summary.md` | ESDE_Primitive_Report.md | Primitive phase 全体 (v9.0-v9.13): 4 層構造、cid、内省 tag、pickup、内的基準軸、Pulse + MAD-DT、Cognitive Capture (B_Gen/M_c/E_t/Δ)、v9.12 audit、v9.13 persistence-based birth、S≥0.20 撤去、認知層方向性確定 | **v9.13 対応 (旧 05b/05c 統合済)** |
| 06 | `06_concept_core.md` | 概念理解.md (1305 行) | Aruism、4 層構造、絶対ルール、Taka 直接発言、戦国大名モデル、spatial vs structural、v9.12 並列基準、v9.13 記憶の所在 | **v9.13 対応** |
| 07 | `07_esde_system_structure.md` | (要約のみ) | ESDE 現行システム構造、4 層、各層パラメータ、コード参照 | **v9.13 対応** |

---

## 最小限知っておくべき項目 (v9.13 対応)

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
18. **CID の記憶は物理層の中に既にある** (Taka 2026-04-16) — 足りないのは「記憶を作る仕組み」ではなく「物理状態を記憶として読む関数」。次フェーズ (v9.14/v10.0) の主題。
19. **「無駄だから切る」禁止** (Taka 2026-04-16) — 不利な機能でも削除せず、どう活かすか考える。pickup は休眠保持。
20. **AI 間文書は日本語 md** (Taka 2026-04-16) — 運営原則 v2 の英語ルールは撤回。Taka が読めることが最優先。既存コード docstring は英語のまま維持。

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
| 介入規律 | 「認知層は物理層に書き込まない」 | 「認知層・意識層は物理層・存在層に書き込まない」 | v9.13 で再確認 |
| label の魂 | frozenset 固定 | 同じ (変更なし) | — |
| cid | label 死亡で消滅 | ghost 化、TTL 経過で reaped (v9.8a で拡張) | — |
| label の birth | S≥0.20 島 + R>0 ペア (経路 B) | 同じ | **age_r ≥ τ の connected component のみ** (v9.13) |
| CID の記憶 | 外部 dict (SubjectLayer) への蓄積構想 | 同じ | **物理層の中に既にある、読む関数が足りないだけ** (Taka 2026-04-16) |

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
| 記憶の読み出し関数 | CID の物理状態を「記憶」として解釈する関数 (v9.14 以降の主題) |

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
| Primitive | v9.1 - v9.13 | **v9.13 完了** |
| 記憶の読み出し | v9.14 or v10.0 | 次 |
| 記憶の蓄積と再生 | v10.x | 構想 |
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
| Semantic gravity + deviation | deviation_enabled=True | v9.14 以降で検証予定 |
| v99_ 内的基準軸 | 計算走行中、CSV 出力中 | — |

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

---

## 15. 何か矛盾を見つけたら

新スレッドの AI が文書間の矛盾を見つけた場合:

1. **本ファイルの用語対応表を確認**: 用語の対応で解消するか
2. **`07_esde_system_structure.md` を確認**: これが現行の真実
3. **`05_primitive_summary.md` の v9.13 セクション を確認**: v9.13 での前提変更を確認
4. **解消しない場合**: Taka に質問する。**推測で実装に進まない**

過去のドキュメント (01-04, および 06 の古い部分) には「3 層構造」「仮想層」「観測層」「n=2 主体」「phase+r 支配」などが残っている。これらは古い表記や v9.11 以前のアーティファクトを含む記述であり、実装の判断基準としてはいけない。

---

## 16. 文書の優先度サマリ

文書を読む時間が限られている AI 向け:

**最優先 (必読、実装の判断基準)**
- 本ファイル (00_index.md): ナビゲーション + 用語対応表
- `07_esde_system_structure.md`: 現行システム構造 (v9.13 対応)
- `05_primitive_summary.md`: Primitive phase 全体 (v9.13 対応)。特に **v9.13 セクション (persistence-based birth、認知層方向性)** と **v9.12 セクション (Δ i.i.d.、phase+r 原因)** は必読

**次優先 (文脈理解)**
- `06_concept_core.md`: Taka 哲学コア (v9.13 対応)

**次優先 (失敗の記録、必ず時間を作って読む)**
- `04_cognition_summary.md`: v3-v7 の試行錯誤、「物理層は床」結論

**参考 (背景理解)**
- `01_genesis_summary.md` 〜 `03_autonomy_summary.md`: 過去の phase 概要

**実装時参照**
- `primitive/v913/v913_persistence_audit.py`: v9.13 本体 (v9.11 を丸ごとコピーして追加のみで実装)
- `primitive/v911/v911_cognitive_capture.py`: v9.11 cognitive capture 実装 (v9.13 が基底として継承)
- `primitive/v911/v911_capture_param_audit.md`: v9.11 パラメータ決定根拠
- `docs/概念理解.md`: Taka 用あんちょこ (v9.13 対応済)
- `docs/ESDE_Primitive_Report.md`: Primitive phase 全体レポート (v9.13 対応済)
