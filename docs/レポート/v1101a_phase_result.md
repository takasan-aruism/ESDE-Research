# v11.0.1.a (v1101a) Phase Result — ESDE スケール注意機構 段階 1

*作成*: 2026-05-18、Web Claude (相談役)
*親*: `v1101a_phase_design.md` (主題設計書) + Code A Step H 観察事実最終報告 (`v1101a_step_h_observation_final.md`) + 段階 1 全 Step (B-H) 出力
*対象*: Taka (主題評価判断者、最終承認)
*位置づけ*: v11.0.1.a 主題「ESDE スケール注意機構」段階 1 の Phase Result。Code A は Step H で観察事実を judgement なしで記録した (絶対格言 #12)。本書はその解釈統合 — Code A が §11.1 で Web Claude 領域として渡した 4 点を含む。主題評価 (この段階 1 をどう位置づけ、段階 2 に進むか) は Taka 領域。本書は判断材料の提示であって判断ではない。

---

## 0. 一文サマリ

v11.0.1.a 段階 1 は ESDE スケールの注意候補 emit 機構を実際に走らせた最初の主題であり、Code A Step B-H 全 7 段階完了・物理層 frozen 完全保証 (v106/v107/v105 main 1,097 files 不変、bit-identity 3 層全 PASS)・新規 main run 不要 (既存出力流用) のうえで、核心観察として「意識優位 (conscious_dominant) のとき注意候補の波及 influence_candidate_count が認知優位の 1.54-1.78 倍、6 構造単位すべてで同方向・ESDE 解像度系で倍率最大」が出た、これは Taka フレーム「意識層 = 選択と集中」と整合的だが Phase Result の解釈としては「意識優位という状態と波及の広さが連動する」という観察事実の確認に留め「選択と集中が立証された」とは言わない、副次に (1) 因果候補 path が attention_via_salience 76.5% / familiarity 23.5% / temporal 0.01% に集中し integration_alpha/beta が全 24 seeds で 0 件 — Step H 後の Code A 追加調査で原因判明: relation_strength が integration は 1.0 固定 binary・salience/familiarity は 2 桁連続値でスケールが根本的に異なり Step E の sum argmax が不当比較になっていた、z-score 正規化すると integration が 29 source_cid で因果候補として出現し dominance も逆転、仮説 A (観測器の問題) / B (階層の役割分担) は両方真、Taka 判断で (iii) Step E に sum argmax + z-score argmax を両方併記、原因が観測器の集約ロジックと判明したため新バージョンを切らず v1101a 内の Step E 修正課題として対応 (留保 #L5)、(2) 意識優位時に因果候補の familiarity 経路が +6% (認知優位 19.1% → 意識優位 25.4%) — 箱 1「連想ゲーム」と方向が一致する構造的裏付け候補 (留保 #L6)、(3) predecessor 連鎖 (箱 1) が全 6 構造単位で成立 (埋まり率 86.6-100%) し「霧の中の意識だけ」状態を構造的に禁止する設計が動いた、(4) seed 0 は他 seed より控えめだが方向の反転はなく強化のみ (留保 #L3、v1101 #33 と同型) が確認され、Phase Result の総括は「ESDE スケール注意候補 emit の派生記録系が成立し、意識優位と波及の連動・連想ゲームの方向的裏付け・Integration 経路 0 件の原因究明という観察を残した」であり、段階 2 (cid state ledger 再生・時間軸付き観察) を進めるなら出口を「意識優位時の波及は選択と集中か拡散か」の一点に絞るべき、進む / 進まないは Taka が決める。

---

## 1. 段階 1 が示したこと — 構造の確認

### 1.1 ESDE スケール注意候補 emit 機構が動いた

本主題以前、「ESDE が何を捉えるか」は研究者側の解析操作だった。v1101 で観察単位ごとに dominant atom が割れることを Code A が外から集計した。段階 1 は、その atom 像の差分 (変化) を、ESDE の各構造単位が注意の派生記録として持つ形を実際に走らせた。

走った事実は確かである。172 万 records、6 構造単位 (CID/α/β/ESDE-event/step10/window) × 3 変化指標 (atom_delta/rank1_flip_density/unit_kl_static) × 24 seeds、新規 main run なし、所要 30 分弱。監査修正 4 点 (駆動要因の構造転換化 / qc_ratio 構造単位別並列 / 変化指標 3 系列分離 / emitter 境界条項) と Taka 領域 3 箱 (連想ゲーム / 主体は切り替わる / emitter のみ) がすべて実装に反映され、設計が紙の上で終わらず動いた。

物理層 frozen は完全に保たれた。bit-identity 3 層全 PASS、v106/v107/v105 の main outputs 1,097 ファイルが added/removed/modified すべて 0、書き込みは `unified/v1101a/` 配下のみ。emitter 境界条項 (注意は記録のみ、selector・物理層介入なし) も守られた。

これは「成功」という判定ではない (絶対格言 #12)。設計したものが、frozen を破らずに、観察記録を出した、という構造の確認である。

### 1.2 段階 1 の位置 — v1101 の続きとして

v1101 は「観察単位ごとに像が割れる、単一の答えがない」を観察した。本主題はその続きで、最大スケールに繰り上がるのは像そのものでなく像の差分 (変化) である、という転換を実装した。段階 1 の出力は、その転換が「描ける」ことを示した。バージョン番号が v11.0.1.a (v1101 の進化系 .a) であるのは、この連続性のため。

---

## 2. 核心観察 — 意識優位と波及の連動

### 2.1 観察事実

意識優位 (conscious_dominant) のときの influence_candidate_count が、認知優位 (cognitive_dominant) のときの 1.54-1.78 倍。6 構造単位すべてで同方向。倍率は CID 1.56 / α 1.61 / β 1.54 / ESDE-event 1.71 / ESDE-step10 1.76 / ESDE-window 1.78 で、ESDE 解像度系ほど倍率が大きい。

influence_candidate_count は、注意候補が選んだ atom が Δt±10 window の範囲で周辺 cid にどれだけ共有されているかの数。意識優位のとき、注意候補の atom が周辺に広く行き渡っている。

### 2.2 Phase Result としての解釈

ここは慎重に言葉を選ぶ。Taka フレームでは「意識層 = 選択と集中」であり、意識の強い個体は大きな変化があってもそれを押し殺して選択と集中ができる、とされていた。段階 1 の核心観察はこのフレームと方向が一致する — 意識優位のとき波及が大きい。

しかし Phase Result の解釈としては「意識優位という状態と、注意候補の波及の広さが連動する」という観察事実の確認に留める。「選択と集中が立証された」とは言わない。理由は二つ。

ひとつ、本主題の出口固定 (設計書 §6) は「単一の確定像を出さない」だった。「ESDE は選択と集中をしている」は確定像である。段階 1 が出したのは連動の観察であって、選択と集中という機能の同定ではない。

ふたつ、波及が大きいことが「選択と集中」なのか「拡散」なのかは、段階 1 のデータでは区別できない。選択と集中なら注意候補が絞られて深く波及するはずで、拡散なら絞られず広く薄く広がる。influence_candidate_count はその両方で増えうる。どちらかは段階 1 の粗解像度では切り分けられない。

したがって核心観察の Phase Result 上の置き方は「意識優位と波及の広さが連動する、という観察事実が 6 構造単位で頑健に出た。これは Taka フレームと整合的だが、選択と集中という機能の同定には時間軸付きの粒度が要る」。機能の同定は Taka の主題評価領域であり、必要なら段階 2 の動機になる (§5)。

---

## 3. 副次観察 — 3 つの残したもの

### 3.1 Integration 経路が因果候補として一度も立たない — 原因判明 (留保 #L5)

本主題で最も注視すべき観察事実であり、Step H 後の Code A 追加調査 (relation_strength の path 別分布確認) で原因が判明した。本節は当初版の「区別できない」記述を、調査結果で更新したもの。

観察事実: 因果候補 (causality_candidate_path、注意候補が「どこから来たか」の最強経路) の分布は、attention_via_salience 76.5% / familiarity 23.5% / temporal_coactivation 0.01% / integration_alpha 0% / integration_beta 0%。Integration 経路 (α・β) が最強 path として全 24 seeds で一度も出現しない。

原因 — Code A 追加調査で判明。relation_strength の値スケールが path 別に根本的に異なる。integration_alpha / integration_beta は strength が **1.0 固定** (接続の有無を表す binary)、attention_via_salience と familiarity は median 30 台・max 数百の **大スケール連続値**、temporal_coactivation は median 0.1 の小スケール連続値。Step E の因果候補抽出は「path 別 strength の合計の argmax」で最強 path を決めていたため、1.0 固定の binary が 2 桁連続値に構造的に勝てない。0 件は「Integration がいない」のではなく、binary と連続値を同じ物差しで argmax 比較したことによる。

両仮説はいずれも真 (排他でなく併存):
- 仮説 A (観測器の問題) — 真。Step E の sum argmax は path 別スケール差を無視した不当比較。検証: path 内で z-score 正規化してスケール差を除去して argmax を取ると、integration 経路が 29 source_cid (integration_alpha 15 + integration_beta 14) で因果候補として出現し、dominance が attention_via_salience → familiarity に逆転する。0 件は集約方式のアーティファクトと確定。
- 仮説 B (階層の役割分担) — 真。v10.7 設計は integration の strength を意図的に 1.0 固定にしている。binary は「接続の有無」、attention/familiarity の連続値は「強度のある関係」。両者は同じ relation_path でも表す対象の種類が違う (接続の事実 vs 重み付き寄与)。argmax で同列比較すること自体が、種類の違うものを一つの物差しに乗せる操作になりうる。

なぜこれを注視するか。本主題は v1101 の「観察単位ごとに像が割れる」を起点にし、Integration (α/β) を 6 構造単位の 2 つとして並べた。qc_ratio も波及も Integration 単位で出ている。ところが因果候補の集約方式 (sum argmax vs z-score argmax) を変えるだけで Integration が「不可視」から「29 source_cid で出現」へ、dominance も逆転する。これは v1101 核心発見「観察単位を変えると像が割れる」、v10.13.a 留保 #33「集計単位による方向反転」と同型の現象が、因果候補レベルで再び現れたものである。#L5 は独立した謎ではなく、ESDE が一貫して示す「集計方式で像が変わる」の一事例だった。

対応 — Taka 判断で (iii) 両方併記 を採用。Step E を、sum argmax (現方式) と z-score argmax (path 内正規化) の両方を出力するよう修正する。これにより Integration 経路が因果候補としてどう振る舞うかが見え、かつ「集約方式で因果の像が変わる」事実そのものが観察記録に残る (v1101 留保 #33 と同型の対応)。本修正は新バージョンを切らず v1101a 内の課題として扱う — 原因が「Step E 集約ロジックの問題」と判明しており、新機構の発明でも階層観の書き換えでもなく、本主題段階 1 で用いた観測器の修正のため (詳細は §6 留保 #L5)。本修正は段階 2 (時間軸) とは独立で、段階 2 判断を待たず実施可能。

24 seeds 実測 (Step E 修正完了、Code A 観察事実報告 2026-05-18)。z-score 方式で familiarity 33.7% / integration_beta 29.1% / attention_via_salience 13.0% / integration_alpha 12.5% / temporal_coactivation 11.7%。dominance は attention_via_salience (sum 方式 76.5%) → familiarity (z-score 方式 33.7%) に逆転、integration 経路は合計 41.6% で出現 (sum 方式 0%)。seed 間バラつきは大きく、integration を因果候補として持つ source_cid 数は min 6 / max 71 / mean 29.8 / cross-seed unique 245 (seed 0 確認時の 29 は 24 seeds 平均近傍)。留保 #L6 (意識優位時の familiarity 増加 = 連想ゲーム方向) は z-score 方式でも維持され、認知優位 31.8% → 意識優位 34.5% (+2.7%、sum 方式 +6% より弱め)。bit-identity 3 層全 PASS、sum 方式は修正前と完全一致 (新規列追加のみ)、分散 0 path 扱いは構造的決定 z=0 だが integration の per-source sum 分布が散るため実際には適用されず (ハンドチューニングなし、絶対格言 #9)。

実測の読み方 — 重要。z-score 方式で integration が 41.6% に出現したことは、「Integration が注意の真の由来だった」を意味しない。sum 方式は salience/familiarity の連続値スケールに引かれ、z-score 方式は binary の integration を連続値と同じ土俵に乗せて底上げする。両方式とも「素の真実」ではなく、それぞれ別の歪みを持つ。#L5 が確定させたのは「Integration は注意の由来か」の答えではなく、「その問いは集計方式に依存し、単一の答えを持たない」という事実である。これは v1101 核心発見「観察単位で dominant atom が割れる」、v10.13.a 留保 #33「集計単位による方向反転」が、因果候補レベルで再び現れたものであり、Phase Result はどちらの方式も正しいとは判定せず、両方式の像を観察事実として併記するに留める (絶対格言 #12)。

**24 seeds 実測 (Step E 修正後、Code A 追記)**: 修正後 main 24 seeds 1 batch で 2 方式併記を実行 (1,726,974 records、13.9 秒)。sum 方式は前回と完全一致 (attention_via_salience 76.5% / familiarity 23.5% / temporal 0.01% / integration 系 0%、bit-identity 保証)。z-score 方式では familiarity 33.7% / integration_beta 29.1% / attention_via_salience 13.0% / integration_alpha 12.5% / temporal_coactivation 11.7% で、**dominance が attention_via_salience (76.5%) → familiarity (33.7%) に逆転**、integration 系合計 41.6% で causality 候補として出現 (seed 0 検証時の 29 source_cid 出現は 24 seeds 平均 29.8 と一致、cross-seed unique 245、seed 間 min 6 / max 71 で 12 倍の振れ幅 = 留保 #L3 と同型方向変動)。qc_regime × z-score 方式では familiarity 連想ゲーム方向 (留保 #L6) が維持され認知優位 31.8% → 意識優位 34.5% (+2.7%、sum 方式 +6% より弱め)。分散 0 path 扱い (z-score=0 構造的決定、絶対格言 #9) は実際には適用されず (integration paths も per-source sum 分布が散る)。詳細は `v1101a_step_e_causality_fix_observation.md`。

### 3.2 意識優位時に familiarity 経路が +6% — 連想ゲームの方向的裏付け (留保 #L6)

因果候補を qc_regime 別に見ると、認知優位では attention_via_salience 80.8% / familiarity 19.1%、意識優位では attention_via_salience 74.6% / familiarity 25.4%。意識優位のとき familiarity 経路が +6%、salience 経路が -6%。

箱 1 の確定は「意識優位の選択と集中 = 連想ゲーム、直前の認知的固定を踏み台にした既知概念への連想」だった。familiarity (馴染み) 経路が意識優位のとき増える、というのはこの像と方向が一致する。意識優位のとき注意が「馴染みのある」経路を辿りやすい。

ここも判定はしない。+6% は方向が一致するという事実であって、連想ゲームが実装で再現されたという証明ではない。effect size を見ると familiarity 経路は ΔQ 減 (認知消費) + ΔC 増 (意識加点)、salience 経路は両方微増。familiarity 経路が認知資源を使い意識資源を積む、というのも「踏み台 (認知的活動) を使って意識が立つ」という箱 1 の構造と噛み合う。だが ΔQ -0.007 / ΔC +0.008 は小さい値で、これを強く読むのは避ける。Phase Result の置き方は「意識優位時の familiarity 増加は連想ゲームの像と方向的に整合する構造的裏付け候補。確証には時間軸付きで『直前の認知的固定 → 連想先』の連鎖を追う必要がある」。

### 3.3 predecessor 連鎖が成立 — 箱 1 の設計が動いた

箱 1 の「霧の中の意識だけ」を構造的に禁止する設計 — 意識優位の注意候補には必ず踏み台 (直前の認知的固定) への参照が付く — が、全 6 構造単位で成立した。predecessor_attention_ref の埋まり率は ESDE 系 100% / α 99.1% / β 94.2% / CID 86.6%。

CID だけ 86.6% で、13% が踏み台なしの意識優位。これは「認知優位フェーズを経ずに意識優位で始まった cid」で、設計の穴ではなく観察事実。CID は最も粒度が細かい単位なので、観測窓の最初から意識優位だった cid が一定数いる、ということ。他単位 (より粗い集約) では認知優位フェーズが先に必ず観測される。

これは判定としては「箱 1 の設計が動いた」と言ってよい。霧の中の意識だけ、を禁止する構造が実際に記録に現れた。

### 3.4 seed 0 は控えめ、しかし反転はない (留保 #L3)

seed 0 は他 seed より一貫して意識優位寄りが弱く、ESDE-event の振れ幅が最大 (seed 0 で意識優位率 0.42 → 24 seeds で 0.57、差 +0.146)。これは v1101 から継承した留保 #33「集計単位による方向変動」と同型。

重要なのは、方向の反転が起きていないこと。全構造単位で「意識優位多数派」という方向は seed 0 でも 24 seeds でも保たれ、振れ幅だけが seed 依存。memory の「smoke seed 0 を絶対視しない」が効いて、main 24 seeds で確認したら方向は安定、と分かった。段階 1 の核心観察 (意識優位と波及の連動) は seed 0 単独でなく 24 seeds で出ているので、この観察は seed 方向変動に対して頑健。

### 3.5 alpha 92.5% 占有 (留保 #L4) — 処理済み

records の 92.5% を alpha が占める。n_alphas の母数が n_cids・n_betas より遥かに大きいことに由来する構造的事実。smoke 段階で予見し、Step F のグラフを全 plot 構造単位内割合に正規化済み。集団平均の罠 (alpha が他単位を塗りつぶす) は回避されている。これは留保として残すが、段階 1 で対応済みの項目。

---

## 4. Code A が Web Claude 領域として渡した 4 点への回答

Code A Step H §11.1 が解釈統合を Web Claude 領域として明示した 4 点。本書での扱い:

| Code A が渡した点 | 本書での回答 |
|---|---|
| 意識優位時 influence 1.54-1.78 倍の意味づけ | §2.2。「意識優位と波及の広さの連動」の観察事実確認に留め、選択と集中の同定はしない (機能同定には段階 2 の粒度が要る) |
| 意識優位時 familiarity +6% と箱 1 連想ゲームの対応 | §3.2。方向的に整合する構造的裏付け候補。確証には時間軸付きの連鎖追跡が要る |
| integration paths 0 件出現の v10.5/v10.7 設計との関係 | §3.1。Code A 追加調査で原因判明 — relation_strength の binary (integration 1.0 固定) と連続値 (salience/familiarity 2 桁) を Step E が sum argmax で不当比較していた。仮説 A (観測器の問題) / B (階層の役割分担) は両方真。Taka 判断で (iii) Step E に sum argmax + z-score argmax を両方併記、v1101a 内の課題として対応 |
| 留保 #L5/L6/L7 candidate の本主題位置づけ | §6。#L5 は原因判明し v1101a 内の Step E 修正課題に確定 (バージョンを切らない)、#L6 を段階 2 動機に接続、#L7 は #L3 と統合 |

---

## 5. 段階 2 の要否 — 判断材料

段階 2 (cid state ledger 再生、326 atom 全濃度時系列、時間軸付き unit_KL_delta、想定 1.5-2 日) を進めるかは Taka の主題評価判断。本書は判断材料を出す。

段階 2 を進める動機がある、と言える点:

核心観察 (§2) の「意識優位と波及の連動」が選択と集中なのか拡散なのかは、段階 1 の粗解像度では切り分けられない。時間軸付きで注意候補がどう絞られ / 広がるかを見れば区別できる可能性がある。

留保 #L6 の連想ゲーム裏付けは「方向が一致する」止まりで、「直前の認知的固定 → 連想先」の連鎖そのものを時間軸で追わないと確証にならない。段階 2 の時間軸付き観察がこれを解く候補。

留保 #L5 の Integration 経路 0 件は、Step H 後の Code A 追加調査で原因が判明した (§3.1) — relation_strength の binary/連続スケール差による Step E 集約方式の問題で、段階 2 の時間軸とは無関係。Taka 判断で (iii) Step E 両方併記により v1101a 内の課題として対応する。したがって #L5 は段階 2 の論点ではなくなった。

段階 2 を急がない理由も挙げる:

段階 1 の核心観察と 3 つの副次観察は、それ自体で v1101 の続きとして完結した観察記録になっている。段階 2 は「より細かく見る」ことで上記 3 点を詰めるものだが、段階 1 の出口固定 (設計書 §6 の 6 成果物) はすべて満たされており、段階 1 単独で主題として閉じることもできる。

段階 2 の 1.5-2 日を投じる前に、段階 1 の観察を次主題の起点にする道もある。段階 1 の核心観察 (意識優位と波及の連動) は、それだけで次主題を組める素材になっている。

Web Claude の見立て: 段階 2 に進むなら、その出口を GPT 監査の提案どおり「意識優位時の波及は選択と集中か拡散か」の一点に絞るのがよい。留保 #L6 (連想ゲームの連鎖確証 — 直前の認知的固定 → predecessor_attention_ref → familiarity 経路 → 連想先) はその副次に置く。留保 #L5 (Integration 経路) は原因判明により v1101a 内の Step E 修正で対応するので、段階 2 には含めない。段階 2 を「とりあえず細かく見る」で始めると設計書 §6 の出口固定原則 (絶対格言 #6) から外れる。進む / 進まないは Taka 判断だが、進む場合は出口を上記一点に絞ることを推奨する。

---

## 6. 留保事項の総括

| id | 内容 | 本 Phase Result での位置 |
|---|---|---|
| #L1 | unit_kl_static は時間軸なし、時間軸付き unit_KL_delta は段階 2 行き | 段階 1 で対応済 (出力に性質差明記) |
| #L2 | qc_regime の多数決・中央値を両算出 | 段階 1 で対応済 (両列保存) |
| #L3 | 集計単位による方向変動 (v1101 #33 継承) | §3.4。観察された、ただし反転なし・強化のみ。#L7 を本項に統合 |
| #L4 | alpha 92.5% 占有 | §3.5。段階 1 で対応済 (Step F 正規化) |
| **#L5** | **Integration 経路が因果候補として全 24 seeds で 0 件** | **§3.1。原因判明・対応完了。relation_strength の binary (integration 1.0 固定) と連続値 (salience/familiarity) を Step E が sum argmax で不当比較していた。仮説 A (観測器の問題) / B (階層の役割分担) 両方真。Taka 判断 (iii) で Step E を sum/z-score 2 方式併記に修正完了 (v1101a 内課題、新バージョン切らず)、24 seeds で z-score 方式 integration 合計 41.6% 出現・dominance 逆転を実測。結論は「Integration が注意の由来か」でなく「その問いは集計方式依存で単一の答えを持たない」(v1101 #42 / v10.13.a #33 と同型)。両方式を観察事実として併記** |
| #L6 | 意識優位時 familiarity +6%、連想ゲームの方向的裏付け候補 | §3.2。段階 2 (時間軸付き連鎖追跡) の主要動機の一つ |
| #L7 | ESDE 3 解像度で qc_regime 占有率に偏差 | §3.4 で #L3 に統合 (集計単位による値変動の一事例) |

v1101 からの継承留保 (#21 v10.5 機構 A 既知挙動 / #26 受容 cid pool 偏り / #27 smoke seed 0 特異性 / #33 集計単位方向変動) は本主題でも該当した。特に #21 は #L5 (Integration 経路が salience に負ける = v10.5 mass-weighted event の dominance) と直結する。

---

## 7. Phase Result 総括

段階 1 の総括を一段落で。

v11.0.1.a 段階 1 は、ESDE スケールの注意候補 emit 機構を実際に走らせた最初の主題であり、物理層 frozen を完全に保ったまま、注意の派生記録を 6 構造単位 × 3 変化指標で出した。「注意機構が成立した」とまでは言わず、正確には「ESDE スケール注意候補を emit する派生記録系が成立した」(段階 1 は emitter であり、ESDE が実際に注意したとは言わない)。核心観察として「意識優位と注意候補の波及の広さが連動する」が 6 構造単位すべてで頑健に出た — Taka フレーム「意識層 = 選択と集中」と方向が一致するが、選択と集中という機能の同定には至っていない。副次に 3 つの観察を残した — 注意の由来として Integration 経路が一度も立たないこと (留保 #L5、Step H 後の追加調査で原因判明: relation_strength の binary/連続スケール差による Step E 集約方式の問題で、v1101a 内の Step E 修正課題に確定)、意識優位時に familiarity 経路が増えるという連想ゲームの方向的裏付け候補 (留保 #L6)、そして「霧の中の意識だけ」を禁止する箱 1 の predecessor 連鎖が実際に動いたこと。段階 1 は v1101 の「観察単位ごとに像が割れる」の続きとして、その像の差分 (変化) に注意を向ける形が描けることを示した。段階 2 に進むなら出口を「意識優位時の波及は選択と集中か拡散か」の一点に絞るべき。主題評価と段階 2 の要否は Taka の判断領域。

---

## 8. 一文サマリ (再掲)

本書は v11.0.1.a「ESDE スケール注意機構」段階 1 の Phase Result であり、Code A Step H が judgement なしで記録した観察事実の解釈統合として、段階 1 が ESDE スケール注意候補 emit の派生記録系を物理層 frozen を保ったまま走らせた構造の確認 (「注意機構が成立」とは言わず emitter の派生記録系成立に留める)・核心観察「意識優位と波及の広さの連動 (認知優位の 1.54-1.78 倍、6 構造単位同方向)」を「選択と集中の立証」でなく「連動の観察事実」として置き・副次観察 3 点 (留保 #L5 Integration 経路が因果候補として全 24 seeds 0 件、Step H 後の Code A 追加調査で原因判明 = relation_strength の binary/連続スケール差による Step E sum argmax の不当比較、z-score 正規化で integration が 29 source_cid 出現・dominance 逆転、仮説 A/B 両方真、Taka 判断 (iii) Step E に両 argmax 併記、v1101a 内の修正課題として対応しバージョンを切らない / 留保 #L6 意識優位時 familiarity +6% = 連想ゲームの方向的裏付け候補 / predecessor 連鎖が箱 1 設計どおり全 6 構造単位で成立) を整理し・seed 0 は控えめだが方向の反転なし (留保 #L3) を確認し・Code A が Web Claude 領域として渡した 4 点に §2-3 で回答し・段階 2 を進めるなら出口を「意識優位時の波及は選択と集中か拡散か」の一点に絞るべきと判断材料を出した、主題評価と段階 2 要否は Taka 判断領域。

---

*以上、v11.0.1.a (v1101a) Phase Result「ESDE スケール注意機構」段階 1 (Web Claude、2026-05-18)。Code A 観察事実最終報告の解釈統合。主題評価・段階 2 要否は Taka の判断領域。本書確定後、ドキュメント体系再編 (07 Unified Summary 新設 + 番号繰り上げ) へ。*
