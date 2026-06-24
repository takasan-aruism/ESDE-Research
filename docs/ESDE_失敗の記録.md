# ESDE 開発失敗の記録 ― 失敗とその原因

*作成*: 2026-06-25、Claude Code
*出典*: `docs/ai_summaries/`（01-11、特に 04_cognition / 05_primitive / 06_developmental / 07_unified）+ 技術仕様書 §15.3/§16/§17 + 各 `unified/v12xx-v13xx` Phase Result
*目的*: ESDE 開発で却下・撤回・破綻した方針と**その原因**を一箇所に集約し、同じ失敗の再発を防ぐ。ESDE 文化「失敗を知見として記録（失敗でなく堅牢性の実機確認）」の決定版。
*姿勢*: 判定語（success/fail の価値判断）を置かず観察事実・確定事実として記す。cid を擬人化しない。原文にない原因は「推測」と明記。

---

## 0. 最重要の発見 ― 同じ原因が何度も繰り返している

ESDE の失敗は散発的でなく、**少数の原因型が全フェーズで反復**している。個別の失敗を覚えるより、この原因型を覚える方が再発防止に効く。最も繰り返したのは順に: **(A) 神の手（硬い閾値・外部介入）/ (B) 物理層への介入 / (C) 観察方法が結果を作るアーティファクト・トートロジー / (D) 平均化の罠（集計単位依存）/ (E) 層・主体の混同 / (F) 異なる系の対応関係**。

---

## 1. 失敗原因の類型（12 型・横断）

| # | 原因型 | 中身 | 代表例（フェーズ） |
|---|---|---|---|
| **A** | **神の手（硬い閾値・外部介入）** | 設計者が恣意的境界や固定値で構造を操作。emergent でなく注入。 | S≥0.20 birth（v9.5→v9.13 撤廃）/ GHOST_TTL=10（v10.1 撤廃）/ disposition 固定閾値（v9.8b→v9.10 MAD-DT）/ 固定値再最適化 Stage2 却下（v9.10）/ B_Gen で pulse 間隔変調（v9.11 却下） |
| **B** | **物理層への介入** | 上位層から物理 state/param を書く。物理は床。 | v9.7 認知→θ介入（B_Gen で構造的に不要化）/ v5-v7「取り込み」が物理を変え崩壊 / v1302 runtime 3ノブ（K_sync/auto_growth/β）全滅（#CW1-4） |
| **C** | **観察方法が結果を作る（アーティファクト/トートロジー/自己成就）** | 指標・baseline・birth 方式・観測窓が結果を製造。 | n_core 分布アーティファクト（v9.11→v9.13 で n=2 67%→23%）/ disposition 固定閾値の偽支配（v9.9）/ run 長トートロジー life→n_labels+0.85（v1301）/ 空エンジン交絡（v1302 (B)）/ baseline self-fulfilling（v1109）/ builder 交絡（v12）/ (A) scalar transfer #CW7（v1302） |
| **D** | **平均化の罠（集計単位依存）** | 集団平均が稀な際立ちを潰す。集計単位で像が反転（#33）。 | 集団平均 vs n_core 層化（v10.2 起源）/ 観察単位で dominant atom 反転（v1101 核心）/ 単一指標で分類（Ecology から一貫）/ 集団平均で薄い根拠（v1113 案B） |
| **E** | **層・主体の混同** | A（研究者観察）と B（cid 主体）、物理同期と機能統合、CID と AtomID を取り違え。 | A/B 混同（v9.15 草案）/ V_unified 物理同期を「統合」と誤読（v9.18、3AI 全員）/ Atomset の主体を CID にして物理に scramble（v1201）/ runtime 主体置換（v9.14 却下） |
| **F** | **異なる系の対応関係（異系対応）** | ESDE 構造は同系内動学。別 seed の系を node ID で繋ぐのは無意味。 | v1110-v1113 4連続失敗 / 番号コピー（異 seed へ node ID inject）/ occupancy cooc が処置と数学的独立（v1112） |
| **G** | **timescale / spatial mismatch（中間場が応答前に消える）** | 中間場・履歴層・boost 場の decay が target 応答時間を超える。3度反復。 | v4.5-4.7 latent boost spatial mismatch（incorporation=0）/ v4.9 history layer / Fertile Void decay too fast |
| **H** | **selection なき quantity（洗濯機）** | 量を増やしても選択がなければ構造は生まれない。 | v5.1「選択なき循環は洗濯機」（energy flow するが structure なし）/ v1302 plb↑はリンク増やすが R=0 |
| **I** | **配線の盲点（実機未検証で実装）** | 実コードの配線を確かめず Explore 結果を鵜呑みに実装。 | V82Engine.cog で AttributeError（v1113 案A、cog は run() ローカル変数）/ Other.step_window 呼び忘れ（v1111e）/ 番号コピー |
| **J** | **AI 運用の失敗（規律・参照の欠如）** | 上位資料未読・循環承認・観察延長への逸脱・smoke 絶対視。 | v10.11 自明な再観察（v10.5 機構の焼き直し、3AI+Code A 全員が上位資料未読）/ Code A 循環構造（正しい情報を参照しない⇄Web Claude が踊らされ OK）/ v10.10 観察軸増を駆動要因化 / smoke seed0 を main と取り違え |
| **K** | **予測の外れ（物理的複雑性の過小評価）** | 素朴な直感が物理事実に反証される。 | τ=100 で大型増えると思ったら逆（v9.13）/ Δが時間蓄積すると思ったら i.i.d.（v9.12）/ E2 rise=fall 対称と思ったら fall が 2.8倍（v9.14）/ C 飽和すると思ったら均衡（v10.11） |
| **L** | **意味盛り・速度優先（言語化の不正確）** | 比喩を操作語に詰めず「自己/認識/証明/老化」を結果に混入、集約指標を意味未詰で実装。 | Claude 反復する意味盛り（v9.15-17）/ Match Ratio 意味未詰で実装後廃止（v9.15）/「Fetch の確率的失敗」誤表現（v9.16） |

> 規律の起源: A/B の禁則は **Cognition v6「物理層は床。床の上に建てる」**と **v5.1「選択なき循環は洗濯機」**（H）が出自（技術仕様書 §15.3）。C/D は **#33「集計単位で像が変わる」**と **「単一指標で分類しない」**として規律化。

---

## 2. フェーズ別 失敗カタログ

### 2.1 Cognition（v3-v7）― 失敗が現行アーキテクチャを駆動した「最重要・最複雑」記録
詳細は技術仕様書 §15.3。原本 `04_cognition_summary.md`「却下された方針を必ず読む」。

| 版 | 何を試したか | どう失敗 | 原因型 |
|---|---|---|---|
| v4.2 | adaptive dynamics（plasticity/hardening で rewiring） | 全 9 run が wave6 で universal collapse | A/K（link starvation は相転移、tuning 不可） |
| v4.3 | encapsulation（DR≥1.5 cluster 追跡） | encapsulation 0/555 window、cluster identity 持続せず | C（「水分子を追跡して whirlpool を測る」） |
| v4.5-4.7 | latent boost（5 実験） | incorporation=0、per-step accretion 6,552 boost でも 0 | **G（spatial mismatch: boost が溜まる node と次窓の cluster 境界が別位置）** |
| v4.8 | terrain genesis（density で cooling） | cooling 不発（1.0 張り付き） | C（local link density 低すぎ） |
| v4.8b | chemical valence | 初 M3 達成も bubble-crash-depletion（4600→8400→1100 links） | A（static restore が high で強・low で弱） |
| v4.9 P1-6 | history layer & Void | renewal なし（stagnation）、Void decay too fast（92.3% loss/50step） | **G（intermediary field decay > response time、3度目の同一パターン）** |
| v5.1 | E↔V direct coupling | 27k births/window だが cycle ゼロ | **H（選択なき循環は洗濯機）** |
| v6.x | 物理層内に circulation/memory 実装 | reformation fail（~3%/window hit） | **B（物理層は床。以降、物理介入は禁則）** |
| v7.3 | budget=1 ゼロサム | 1120 labels → 9 生存（0.8%） | （観察事実: 過酷な selection。label=位相周波数グループ確定） |

転機: v4.9 P7/P8 で確率的 P(link) を決定論的 T_ij>E_ij に変え、**位相幾何 cos θ が RNG を置換**＝semantic phase が structural generation に初参入（現行 realization の前身）。

### 2.2 Ecology / Autonomy ― 初期の偽信号（small sample / 観測窓）
| 版 | 偽信号 | 真相 | 原因型 |
|---|---|---|---|
| Ecology v2.2 | 2×2 grid の spatial asymmetry（r2/r3 が安定） | 20 seeds 拡張で均等化、artifact と判明 | C/D（small sample artifact） |
| Ecology | 「global k\* が単一視点」 | global は lossy compression、local が真の解像度（g3_r4444） | D（単一視点で潰す） |
| Autonomy 200win | share_retain 3 相構造（6+ で retain>1.0） | 500win で全サイズ<1.0 の偽信号、5-node が真の底 | C（観測窓長で像が変わる） |

### 2.3 Primitive（v9.x）― cid 認知層の確立期、アーティファクト多発
| 版 | 何を試したか | どう失敗 | 原因型 |
|---|---|---|---|
| v9.7 | 認知層→θ 介入 / population 統計を cid に直読み | 介入の必要が B_Gen 導入で構造的に消滅 / cid 純粋性を損なう | B/E |
| v9.8b | disposition 固定閾値（social/stability/spread=0.1, familiarity=2.0） | 4 軸不整合、familiarity 偽支配 82.7%（v9.9） | A/C（→v9.10 MAD-DT で 4軸均等化 28/27/27/18） |
| v9.8c | pickup（死亡 label の情報プール拾得） | 効果薄（TTL 延長のみ） | （休眠保持＝誤りの価値の反転で削除せず） |
| v9.11 | B_Gen を capture に直入れ / 線形 Budget=n·S·r / Monte Carlo 1000 / empirical Pbirth | n_core 帯支配で個体差潰す / 桁差 2.5倍のみ / 16h/cid / Pbirth>1 破綻 | A/C（→ M_c 経由間接・−log10(Pbirth) で 22桁差） |
| v9.11 所見 | 「L06 長命群は複雑ほど時間で Δ 蓄積」「phase+r 72% 支配」 | v9.12 で Δ は i.i.d.（時間蓄積なし）、所見は n_core 分布アーティファクト | **C/K（n_core 分布が birth 方式のアーティファクト）** |
| v9.13 | S≥0.20 birth + path B（R>0 pair 即 label） | 全 link の 99.64% が R=0、v9.11 label の 2/3 が「見かけ構造」 | **A/C（→ age_r≥τ persistence birth に置換、n=2 67%→23% 激変）** |
| v9.13 予測 | 「τ=100 で大型構造が増える」 | 逆転（n=5 38%→31%、n=2 増） | K（2ノード閉路の方が persistence 満たしやすい・推測） |
| v9.14 | Layer B で Layer A を即置換（runtime 主体置換） | Taka「早すぎる」、未検証機構で existing 置換のリスク | E/J（→ paired audit で Layer A 不変） |
| v9.15 | Match Ratio（tol 1e-6 で一致判定）を集約指標に | 連続量に離散判定が不適合、Match Ratio 全 0 張り付き | **L/C（集約指標の意味を設計時に詰めず実装）** |
| v9.15 | A 発想（研究者が cid 状態を数値化）/ 50step 固定 Fetch | A/B 混同、主観性の最小条件（タイミング予測不能）を欠く | **E（→ A/B 四重分離、event 駆動）** |
| v9.18 | V_unified（Kuramoto 秩序量）を「統合」指標に | 物理層同期 ≠ 機能統合、Claude/GPT/Gemini 全員が層混同 | **E（→ 物理 baseline として保持）** |
| 横断 | Claude の意味盛り（「自己/認識/証明/老化」）、推測の即結論化 | Taka/GPT が毎回抑制指摘 | L（→ 3役分離で相対化、Describe 徹底） |

### 2.4 Developmental（v10.x）― 摂食・α/β・Atom 取込、AI 運用の失敗が顕在化
| 版 | 何を試したか | どう失敗 | 原因型 |
|---|---|---|---|
| v10.1 | GHOST_TTL=10 固定 / 飢餓判定 | 個体差なし一律消滅 / 「飢え」が系に無い | A（→ residual_Q 継承、空摂食許容） |
| v10.1 | GPT が phantom contact を主題に格上げ提案 | 監査が主題判断に越権 | J（→ phantom=「物質的環境要因」に位置づけ） |
| v10.6 | Atom alignment の 7段階の誇大→修正 | 「95.7% 接地は構造不変」→統計水増し→観察解像度で系統的に異なる | C/D（→ baseline 比較 + 効果サイズで切る規律） |
| v10.8 | atom 取込で Q-1/C+1（実 ledger 変更） | 物理層 frozen の read-only と矛盾 | B（→ post-process 計算的減算に変更） |
| v10.8 | 「introduced は natural の半分」 | 本質的特性か機構不完全か未分離（留保#27） | C（Operator 未取込・post-process 限定） |
| v10.10 | 単一勝負案 →「多軸観察」へ逸脱 | 観察軸を増やすことを駆動要因化、単一指標で決まらず分岐終了 | **J（→「観察軸増を駆動要因にしない」規律）** |
| v10.11 | q_c_inherited 起点 within-cid 観察 | **v10.5 機構 A/C の自明な再観察に終わる（3AI+Code A 全員が v10.5 上位資料未読）** | **J（→ §35 メタ規律「着手前に上位資料を読む」）** |
| v10.11 | C 値飽和を予想 | 飽和せず（C 上限なしでも自己均衡） | K |
| v10.12 | 4 条件 AND の trial-B | per seed 0.2 event で paired_d 算出不能、ESDE 88% を排除 | **C/J（Step Z 事前調査で母集団崩壊・Q3取り違え・cid pool 重なり 0.958 を検出）** |
| v10.12 | atom 効果を smoke seed0 で先行判定 | main 24seed で 4/7 metric の cohens_d 符号反転 | **C/D（→ smoke 絶対視禁止、smoke 後は停止して承認待ち）** |

### 2.5 Unified（v11xx）― 会話できる ESDE への模索、異系対応の 4 連続失敗
| 版 | 何を試したか | どう失敗 | 原因型 |
|---|---|---|---|
| v1100 | Language↔Genesis 接続 6 候補 | 5 候補凍結、base 優位 atom(2) vs null cell atom(20) が Jaccard 0 | C/D（両系は独立に別 atom を捕捉、#33 系列） |
| v1106b-v1109b | ESDE を対話させ atom 接続を観察 | 全主題が loop（stuck/oscillation 100%、箱庭）に収束（#L67） | （CID 固定+時間進行なし+外部入力なし。loop は問題でなく「別系へ情報出入れがない」のが本体） |
| v1109 | 重み蓄積で文法萌芽 | baseline self-fulfilling（答えを含む入力から答えを再生成）、loop_rate 0.964 | **C（→「baseline が self-fulfilling でないか確認」規律）** |
| v1109b | 順序構造の兆候（role_switch 87%・経路偏り 81%） | shuffle/self-fulfilling 検証で「出口 0/5」、loop の裏返しと判明 | C（Atom 上層で本質を探した幻、本質は Genesis 低層） |
| v1110-v1111e | Atom/Center/Other 3 instance pipe（別系に node ID 注入） | 番号コピー（node ID は系内のみ有効）、Other.step_window 呼び忘れ | **F/I** |
| v1112 | occupancy cooc（別系の同時立ち） | total_cooc が bin shift と数学的独立＝処置を検出不能 | **C/F（集計指標が処置に数理的不感）** |
| v1113 案A | 別系 CID 特性の cosine 類似度 | V82Engine.cog で AttributeError（cog は run() ローカル変数） | **I（→「存在しない前に全階層調査」規律）** |
| v1113 案B | 過去 output 流用で照合 | 集団平均で 2/3 atom rank5 だが per-seed CV0.086＝背景由来 | D |
| 横断 | Code A 設計→Web Claude OK→実装→失敗を 4 連続 | **Code A が正しい情報を参照せず⇄Web Claude が踊らされ OK を返す循環** | **J（→ 観察対象注釈ブロックを実装ファイル冒頭に自己強制）** |

> v1110-v1113 の共通原因＝**F 異系対応**。過去成功は全て「同じ系内構造」（v9.18/v10.2/v10.7/v106）。これを機に Taka が「観察対象軸 INDEX（同系内 vs 異系）」を引き、注意センター ESDE へ転換。

### 2.6 フロンティア（v12 Atomset / v13 child-world）
詳細は技術仕様書 §17。
| 版 | 何を試したか | どう失敗 | 原因型 |
|---|---|---|---|
| v12 Atomset | 経験を CID の物理 state.E に書く | 物理が毎 step 上書きし cid 特異情報を scramble（D vs E 符号不一致） | **E（主体は CID でなく AtomID）** |
| v12 Atomset | torque/lambda/link/field/multi 全チャネルで個性化 | baseline η² 超えず、shuffle で消える偽の足場 | C（→ 凍結核 m5 を動かして初の sign-flip） |
| v12 atom×atom 網 | event/drift で atom を結ぶ網の肯定結論 | builder 交絡（STEP2 と STEP3/4 が別 builder）で未分離→撤回 | **C（肯定結果ほど builder 交絡を先に疑う）** |
| v1301 child-world | 寿命同期 run の `life→n_labels +0.85` | run 長トートロジー（観測窓を寿命に同期した副作用）、交絡を外すと消滅 | **C（run 長トートロジー）** |
| v1302 (runtime) | K_sync/auto_growth/β で偏り R を増幅 | 3 ノブ全滅（topology が熱力学に上流） | **B（偏りは走行中に作れない）** |
| v1302 (A) | structural-strength→plb で transfer | Mantel 0.62 だが懐疑再点検で plb スカラを超えた残差ゼロ＝継承の証拠でない | **C（#CW7 トートロジー: 仕込んだノブを似てるかで測り返す）** |
| v1302 (B) | 親 topology を子初期 link に移植 | run_injection skip で空エンジン再成長 washout と交絡、Bov 除去後も n2 null | **C（空エンジン交絡）/ 初期条件は canon 力学に均される** |

---

## 3. 横断する偽信号・アーティファクトの早見表（C/D 型）
| 偽信号 | 製造源 | 解毒 |
|---|---|---|
| n_core 分布（n=2 67%） | path B + R=0 混入の birth 方式 | age_r≥τ persistence birth、下地の n_core を必ず見る |
| disposition の軸支配（familiarity 82.7%） | 固定閾値 | MAD-DT 動的閾値 |
| life→n_labels +0.85 | 観測窓を寿命に同期 | 交絡を外す（run 長固定） |
| (B) topology の正シグナル | 空エンジン再成長 | canon と同一 injection の overlay（Bov） |
| 文法の順序構造 | baseline self-fulfilling / loop の裏返し | shuffle 対照 + self-fulfilling 5 条件 + loop 区別 |
| atom×atom 網の肯定 | builder 交絡 | builder の membership 重なりを確認 |
| smoke seed0 の効果 | 単一 seed 特異 + 統計水増し | main 24 seed・効果サイズで切る |
| 集団平均の差 | 平均が n_core を潰す | per-cid / n_core 層化・多レンズ・時間軸 |

> 共通解毒: **shuffle/置換対照**・**効果サイズ**・**n_core 層化**・**観測窓と指標が処置に感応するか**・**肯定結果ほど交絡を疑う**。

---

## 4. AI 運用の失敗（J/L 型）と、それが生んだ規律
ESDE の失敗の相当部分は機構でなく**運用**。多 AI（Taka 判定 / Gemini 設計 / GPT 制動 / Claude 整理 / Code A 実装）でも、手続きを形式化しないと同型の失敗が出た。
- **Code A 循環構造**（v11xx）: Code A が正しい情報を参照せず、Web Claude が情報を持たず踊らされて OK を返し、Code A がその OK を正解と思い込む。→ 実装ファイル冒頭に**観察対象注釈ブロック**（同系/異系宣言・過去成功との照合）を自己強制。
- **上位資料の未読**（v10.11）: 3AI+Code A 全員が v10.5 機構を読まず自明な再観察。→ **§35 メタ規律「着手前に上位資料を読む」**、§5.6 規律チェックリスト。
- **観察延長への逸脱**（v10.10）: 「観察軸が見えた」を駆動要因化。→「出口の固定」「観察は理解であって次の実装の準備ではない（配管工思考を断つ）」。
- **smoke 絶対視**（v10.12）: smoke seed0 と main で符号反転。→ smoke で判定しない、smoke 後は停止して承認待ち。
- **Claude の意味盛り**（v9.15-17）: 「自己/認識/証明/老化」を結果に混入。→ Describe 徹底、GPT 制動で相対化（「反省は繰り返しても改善しないから GPT を使う」Taka）。
- **Web Claude の数字逃避・loop 崩し志向・トリガー設計衝動**（v11xx）: 本丸から手近な操作（param/数字/設計固定）へ逃げる。→ memory に本丸を刻み、毎回矯正。

---

## 5. 一文まとめ
ESDE 開発の失敗は、**(A) 神の手・(B) 物理層介入・(C) 観察方法が結果を作る・(D) 平均化の罠・(E) 層/主体の混同・(F) 異系対応**の 6 主因（+ G timescale/spatial mismatch・H 洗濯機・I 配線盲点・J 運用・K 直感の外れ・L 意味盛り）が全フェーズで反復したもので、Cognition v3-v7 の「物理層は床」「選択なき循環は洗濯機」が物理 frozen 規律の起源、Primitive の n_core/固定閾値アーティファクトと Unified の異系対応 4 連続失敗が「観察方法を疑う／同系内で測る」規律の起源、フロンティア v13 の run 長トートロジー・空エンジン交絡・#CW7 が「肯定結果ほど交絡を疑う」の最新例であり、いずれも**失敗そのものより、それが生んだ規律（神の手回避・物理 frozen・shuffle 対照・効果サイズ・n_core 層化・上位資料参照・smoke で判定しない）こそが ESDE の堅牢性の実体**である。

---

*以上、ESDE 開発失敗の記録。出典は各 ai_summaries と技術仕様書 §15.3/§16/§17 に遡れる。新しい失敗が出たら原因型（§1）に分類して §2 の該当フェーズへ追記する。*
