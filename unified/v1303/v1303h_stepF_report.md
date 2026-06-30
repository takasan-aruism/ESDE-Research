# v1303h Step F — 注意センター Phase2本番：B_Gen際立ち(n_core内珍しさ)を独立軸に + Familiar精緻化 観察事実報告（判定なし）

*作成*: 2026-06-30、Code A。
*位置づけ*: 注意センター Phase2 本番（v1303h 設計）の Step A〜F。前段 v1303g の2留保（Familiar軸の粗さ・B_Genが背景層別止まり）を直し、**B_Gen（Taka本命の「際立ち＝珍しさ」）を n_core内正規化で独立の際立ち軸に据え、Familiar軸を再発度合いで精緻化**。後処理のみ・物理非書込・判定なし（#12）。「Comparator完成／珍しさで自律注意」とは言わない。判定は Web Claude / Taka。
*成果物*: `v1303h_bgen_salience.py` / `outputs/v1303h/v1303h_bgen_salience_seed0.parquet` / `v1303h_distributions.html`。

---

## 0. B_Gen の扱い（Taka指摘 × 実機確認・すり合わせ確定）
- **Taka指摘**：B_Gen は log10 で桁を丸め同一n_core内の差が消え n_core で実質決まる・log10外してよい。
- **実機確認**：ledger の `v11_b_gen` は **floorされてない連続値**で同一n_core内に差がある（n2:11.00–13.08 で19cid全部違う / n5:32.58–35.37 で16cid全部違う）。floor は Q を作る時だけ。→ **log10外す作業は不要**。
- **すり合わせ**：Taka核心「n_coreで実質決まる」は正しい（**raw bgen vs n_core 相関 0.997**＝帯が n_core で決まる）。**解＝n_core内正規化**（`bgen_pct_in_ncore`）で帯を除けば「実質一意の珍しさ」が拾える（**bgen_pct vs n_core 相関 0.001**）。Q の顔（floor後・資源量）とは分ける＝**二つの顔を分離**。

## 1. 限界（Step A・隠さず明記）
- **数値 B_Gen は 45/228cid のみ**（183 unformed・n3 は1cid のみ）＝**珍しさ軸（bgen_pct_in_ncore）は疎**（構造的イベント 2,546件中 1,183件＝46%が数値あり）。bgen_salience_status=numeric/unformed_no_bgen でタグ。

## 2. 観察 — 際立ちを「θ・イベント・珍しさ」の複数の目で並べる（合成しない #11）
- **B_Gen際立ち列**（別列）：`bgen_continuous`（連続値）/ `bgen_pct_in_ncore`（n_core内 percentile＝珍しさ）/ `bgen_salience_status`。
- **Familiar精緻化列**（別列・粗さ補正）：`recur_count`（何回目・0=初回）/ `recur_recency`（直近同種からの間隔）。
- **θ際立ち**（stable_flag）・**イベント際立ち**（trigger種・Familiar/Novel）は v1303g 継承。**合成して一つのスコアにしない**。

## 3. 出口の核心 — 珍しさ は θ・イベント と別の情報か（独立性）
| 相関（event単位・数値B_Gen） | 値 | 含意 |
|---|---|---|
| **bgen_pct vs θ帯(stable_flag)** | **−0.005** | **ほぼ完全に独立**＝珍しさは θ(同期)と別の目 |
| bgen_pct vs Novel(Familiar軸) | 0.092 | ≈独立＝珍しさは Familiar/Novel と別 |
| bgen_pct vs recur_count | −0.274 | 弱い負（珍しいcidはやや再発少） |
- → **B_Gen際立ち（珍しさ）は θ際立ち・Familiar軸と概ね独立**＝**θ・イベント・珍しさ が並ぶ独立の際立ち軸として持てた**（出口 **(a') の向き**・判定は委ねる）。「n_core や θ の言い換え」(b') ではない（n_core 相関0.001・θ 相関−0.005）。

## 4. B_Gen際立ち × 4象限（n_core内で珍しいcidの分布・観察事実）
| | n | Familiar-Unstable | Familiar-Stable | Novel-Random | Novel-Coherent |
|---|---|---|---|---|---|
| 珍しい(pct≥0.8) | 153 | 0.51 | 0.26 | 0.15 | 0.08 |
| ありふれ(pct≤0.2) | 405 | 0.62 | 0.32 | 0.03 | 0.03 |
- n_core内で珍しいcid（pct≥0.8）は **Novel側が多め**（0.23 vs ありふれ0.06）＝珍しいcidは初回イベントが相対的に多い（観察事実・判定しない）。

## 5. Familiar精緻化（粗さ補正・素直さ確認）
| trigger | recur_count med/max | recur_recency med |
|---|---|---|
| cid_birth | 0 / 0 | NaN（1回のみ・素直） |
| alpha_formation | 7 / 58 | 0 |
| beta_formation | 2 / 30 | 510 |
| c_conversion | 3 / 28 | 500 |
- birth=初回のみ(recur0)・α/β/c は再発回数で「既知の度合い」を粗さなく持てた（past_same 2値の粗さを補正）。

## 6. 検証ゲート（全PASS・自己確認）
gate1_bgen_pct_independent_of_ncore（|corr|<0.05）/ gate2_bgen_pct_in_0_1 / gate3_birth_recur0 / gate4_two_faces_separated（連続値正規化とQ floorを分離）/ gate5_no_composite / gate6_bgen_status_tagged — **全PASS**。

## 7. 言えること / 言えないこと
- **言える（観察事実）**：B_Gen を n_core内正規化（bgen_pct_in_ncore）で「実質一意の珍しさ」として取り出し、**θ際立ち・イベント際立ちと概ね独立な（corr≈0）独立の際立ち軸として別列で持てた**。Familiar軸を再発度合い（recur_count/recency）で精緻化した。珍しいcidは Novel 側がやや多い。
- **言わない**：「Comparator が完成した」「注意センターが珍しさで自律的に注意した」とは言わない。**bgen_pct_in_ncore は『n_core内のB_Genのpercentile』であって ESDE が珍しいと感じたのではない**（L型）。合成して一つの際立ちスコアにしない（#11・複数の目のまま）。珍しさ軸は45/228cidで疎。(a')/(b') 判定は委ねる。

## 8. 規律遵守
- **Taka B_Gen指摘**：二つの顔を分離（Q=floor後資源量 / 際立ち=連続値n_core正規化）・n_coreで決まる量(raw)を際立ちにそのまま使わない。#11: B_Gen/θ/イベント際立ちを合成しない（別列・複数の目）。#4/D: cid個別/n_core別/n_core内正規化。#2/B: 後処理・物理非書込。#12/J: 判定せず観察事実のみ・**前段の留保を直すのが本番（観察軸を増やすためでない）**。#CW7: n_core内正規化(percentile)は研究者選択ゆえ `bgen_salience_tag` 明示。F: 228宇宙。
- **信頼問題の継続**：Step A で限界(45/228)と独立性を先回り確認→ゲートで二つの顔分離/独立性/素直さを機械確認してから完了。

## 9. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（n_core内正規化・独立性 corr・45/228限界・Familiar精緻化の生データ再確認）→ Phase Result → Taka。候補：Comparator 本体（4分類確定＋B_Gen際立ちを並べた多レンズ）・near_archive 分解・珍しさ軸の疎さ(45cid)を補う別の珍しさ指標・閾値内部化。

## 10. 一文サマリ
v1303h Phase2本番（v1303g後処理・seed0・判定なし#12）── 前段の2留保(Familiar軸粗さ・B_Genが背景層別止まり)を直し、Taka指摘×実機確認のすり合わせ(ledger v11_b_genはfloorなし連続値で同一n_core内に差ありゆえlog10外す作業不要・但しTaka核心「n_coreで実質決まる」は正しい=raw bgen vs n_core相関0.997)で**B_Genをn_core内正規化(bgen_pct_in_ncore・vs n_core相関0.001)し「実質一意の珍しさ」を取り出しQの顔(floor後)と分離(二つの顔)**、**出口核心=珍しさはθ・イベントと別の情報か→bgen_pct vs θ帯相関-0.005/vs Novel 0.092=ほぼ完全に独立=θ・イベント・珍しさが並ぶ独立の際立ち軸として持てた(出口a'の向き・n_coreやθの言い換えでない)**、B_Gen際立ち×4象限で珍しいcid(pct≥0.8)はNovel側やや多め(0.23 vs ありふれ0.06)、Familiar軸をrecur_count(birth0/α med7/β c med2-3)で精緻化し粗さ補正、限界=数値B_Genは45/228cidで珍しさ軸は疎(明記)、検証ゲート6項目全PASS(二つの顔分離/独立性/素直さ機械確認)、出口は「珍しさをθ・イベントと並ぶ独立の際立ち軸として別列で持てた+Familiar精緻化」まで(Comparator完成/珍しさで自律注意とは言わない・bgen_pctはpercentileでありESDE感覚でない・合成しない複数の目のまま)、Taka本命「際立ち=珍しさ」を正しい形(n_core内正規化・二つの顔分離・合成しない)で注意センターに据えた、判定はWeb Claude/Taka。
