# 課題#1 — 全326 cosine の直感グラフ3種（n_core=5・CID選択可・Ghost分離）報告

## 自己規律宣言（Code A）
① 過去引用済: m31（`full_cosine_step10_seed0.parquet` = argmax 前の全 325 cosine）、#30（気まぐれ指標禁止・Ghost 分離・生き物的統計）、m27 監査（is_ghost = t≥host_lost_step、reaped の死後相も含む）。
② Taka 逐語（原文）: 「m31 で出した全 cosine をそのまま可視化するだけ」「濃度・spike・Δ・分布・閾値・集中度などの計算は一切しない（色/線/棒に載せるのは生の cosine のみ）」「CIDを選出してしまうとおもろくない、選べるように」「だいたい5ノード系が多様性ある」「Ghost 区間を見分けられるように（伏せない）」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-17、Code A。*コード*: `m33_cosine_viz.py`。*出力*: `cosine_viz/`（HTML + CID 一覧）。**グラフに載せたのは生 cosine のみ。計算（濃度/spike/Δ/分布/閾値/集中度）は一切していない。**

---

## 1. 母集団と選択（Taka 指定どおり）
- 母集団 = **n_core_member==5 の CID（seed0、21 個）**。n_core は cid 内で安定（0/228 が変動）。一覧 = `n_core5_cid_list.csv`（cid / 寿命 / イベント数 / final）。
- **CID は固定選出せず引数で選べる**: `python m33_cosine_viz.py <cid>`（任意の n_core=5 cid を描画）。`index.html` に一覧 + 描画済リンク。
- サンプル描画: cid 0 / 42 / 107 / 178（hosted）+ **cid 26（reaped＝Ghost 相在）**。

## 2. グラフ3種（1 CID につき、生 cosine のみ）
1 つの HTML（`cosine_viz_cid{cid}.html`）に縦 4 段:
- **A1 ヒートマップ 全 325 atom**（縦=atom、横=t〔step10〕、色=生 cosine）。
- **A2 ヒートマップ 上位 40 atom**（潰れ対策。atom を生 cosine の最大で並べた表示選択のみ、値は生のまま）。
- **B 重ね折れ線 上位 10 atom**（生 cosine、いつ立ち上がり/沈み/入替）。
- **C 立ち方プロファイル**（選んだ t で 325 atom を cosine 値順に棒、**t スライダ**で形が変わるのが見える。スライダラベルに `[Ghost]` 表示）。

## 3. Ghost の扱い（#30・必須）
- 各 (cid,t) の Ghost 判定 = `t ≥ host_lost_step`（source_events、m27 監査の定義。reaped の死後相も含む）。
- **Ghost 区間を赤の網掛け（vrect, opacity 0.12）+ 遷移点に赤破線（vline）**で A1/A2/B に表示＝「動かない帯」を変化と誤読しないため伏せず明示。
- サンプルで Ghost 相が在るのは **cid 26（reaped、host_lost で遷移）**。hosted（0/42/107/178）は Ghost 相なし（=赤網なし）と分かる。

## 4. 計算を足していない（grep で提示）
- `m33_cosine_viz.py` を grep（`spike|entropy|threshold|concentrat|濃度|np.std|.std(|variance|gini|delta|diff(|percentile|histogram`）→ **実コード 0 件**（一致は docstring の「一切なし」記述のみ）。
- グラフに載るのは生 cosine と、表示用の `argsort`（atom を cosine 値で並べる選択）と Ghost 網掛け（host_lost_step の frozen 参照）のみ。Δ・分布・濃度・閾値・集中度は**算出していない**。

## 5. やらなかったこと（明示）
濃度・spike・Δ・分布・エントロピー・集中度・閾値・「大きい/小さい」判定・atom×atom・CID 投影・センター接続・effect_size・位相化は**一切していない**。「こう読めば濃度」も書かない。

## 6. 一方向保証 + 出力
読む=frozen（full_cosine_step10_seed0 / source_events で生死判定）、書く=`cosine_viz/` のみ。grep: physics/inject/ledger 書込 **0 件**。
HTML 計 44MB（5 CID）。Taka が直接開いて見られるよう commit。任意 cid は `m33 <cid>` で再生成可。

---

*以上 課題#1 可視化（Code A、2026-06-17）。n_core=5(seed0, 21CID) を引数で選べ、A ヒートマップ(全325/上位40)・B 重ね折れ線(上位10)・C 立ち方プロファイル(t スライダ) を生 cosine のみで描画。Ghost 区間は赤網掛け+遷移破線で明示(cid26 reaped に在)。計算(濃度/spike/Δ/閾値)は grep で 0 件確認。解釈・次手段は書かない。判定は Taka。*
