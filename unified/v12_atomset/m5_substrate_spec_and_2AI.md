# v12 Atomset M5 — 並行試行 substrate ビルド仕様 + 2AI 質問

日付: 2026-06-12 / Taka 判断: **(い)真ん中（Atomset を E/L）と(ろ)橋（言語→Atom→inject）を両方、同じ substrate で。**
噛み合わせ: 橋で入った入力が真ん中の個性化を実際に動かすかを見る＝「孤立した二つの系にするな」を*場所*でなく*実接続*まで。橋も真ん中も **E/L** に載るので同じ通貨で出会う。
**両方やるからこそ E-crosstalk（入力 E と経験 E が混ざる）が guard②「本物か」に直結 → 混線見分けの計装を必須にする。**

実装着手前の仕様（2AI/Web Claude レビュー用、500 行書く前に design を晒す＝Code A 盲点対策）。

---

## 1. 全体図（一つの v105 run の中で）

```
(ろ)橋 INPUT:  外部 Atom → atom_centroids[48d] → theme_phase(投影) → label_weights(phase_sig 一致)
                  → targets → physics.inject(E,L)  ［tag=INPUT］
(い)真ん中 EXP: per-chunk で経験計算(robust_z+種類分け+衰退+floor、live) →
                  SELF経験→自分の node E 加算、OTHER経験→他者との link(L) 加算  ［tag=EXP］
出力 READ:     位相励起 exc[CID]=Σ_n E[n]·exp(-λ d(phase_sig,θ[n]))  ［E,θ,phase_sig を読む］
混線見分け:    INPUT_E_delta[cid] と EXP_E_delta[cid] を別台帳でタグ集計（同じ E でも由来を分離）
```

## 2. (ろ) 橋（最小）— atom → 撃つ node

- **atom → theme_phase 投影**（最小・決定論）: 326×48 の atom_centroids の主成分 2 軸へ射影 → `atan2(pc2,pc1)` → 各 Atom に固定 phase。＝「語ごとの位相署名」の最小版（本物の意味投影は将来）。
- 以降は v1111c 流用: `label_weights(atom, theme_phase, λ_dyn)` → `targets_from_w` → `physics.inject(state, target_nodes)`（E+0.6 / link）。**tag=INPUT**。
- 入力系列: 数 Atom を所定 window で順に inject（人間語の代理。最小で「入力が入る」を成立させる）。
- **正直な留保**: 「人間語→Atom」自体は既存 mapper（language/lexicon）で語→Atom は可能だが今回は Atom 直接列で代替。投影は placeholder。

## 3. (い) 真ん中（経験を E/L に、live）

- 経験計算は post-process と同一の式（**robust_z + 種類分け + 衰退 λ=0.95-0.99 + per-axis floor 10×**）を **live hook（per-10step）** に移植。per-CID per-axis に直近値 buffer（deque）を持ち、median/MAD を buffer 上で算出（pre-event = 当該 event を除く）。
- **SELF 軸経験 → 自分の node E**: `state.E[n] += α·g·(r_self−1)` を CID の node に。**tag=EXP**。
- **OTHER 軸経験 → 他者との link L**: OTHER 経験が高い CID は接触相手との latent L を加算（`set_latent`）。**tag=EXP**。
- **別通貨で混線低減**: SELF=E、OTHER=L に分ける（種類分けが混線対策にもなる、Taka 指摘）。

## 4. 混線見分け（guard②、必須）

- **タグ台帳**: 各 window、CID ごとに `input_E_added`（橋 inject 由来）と `exp_E_added`（経験由来）を別々に積算。同じ state.E でも「入力で動いた分」と「経験で育った分」を分離記録。
- **shuffle 対照**: 経験の cid→値 割当をランダム入替（橋 INPUT は入替えない）。**期待: 橋由来 E は shuffle でも残る、経験由来 E（と個性化）だけ消える** → 見分け成立。残れば反射型（偽）。
- **二重確認**: 経験で育った OTHER 軸が 5 パターン（捕獲/橋渡し）と相関、SELF 軸が強い核と相関（過去資産・独立系統）。

## 5. 評価軸（4 つ）と計装

| 軸 | 測り方 |
|---|---|
| ①個性化 | per-CID の結果動態（lifespan/coherence/n_core/励起分布）が分かれるか、n_core 別層化 |
| ②本物か（混線見分け含む） | real vs shuffle で経験分だけ消えるか／input_E と exp_E のタグ分離／5パターン独立一致 |
| ③θ NaN | 毎 window θ の NaN/inf 監視（記録が死ぬ一線、slight に保つ） |
| ④接続性 | 育てた量＝inject が書く量(E/L)か・励起が読む量(E,θ)か（実コードで判定済: E★★★/L★★/θ★★、Z/F/H 落とす） |

## 6. 方法（並行）

| 方法 | 経験→口 | 橋 | 備考 |
|---|---|---|---|
| **M-E** | 経験集約→E | あり | 入力 E と経験 E が同通貨＝混線最大、見分け試金石 |
| **M-split-conn** | SELF→E, OTHER→L | あり | 別通貨で混線低減、種類分け＋会話一体（本命） |
| **M-T**（対照） | 経験集約→torque(θ) | あり | v9.7 の口、slight 限定、比較 |
| baseline/shuffle | 各方法 × shuffle | あり | 混線見分けの対照 |

multiprocessing.Pool（24 並列）で（方法 × shuffle × seed）。smoke first → θ 監視 → pause。

## 7. ビルド順（増分・検証付き、盲点対策）
1. **増分1**: live 経験計算 + EXP→E + タグ台帳 + θ 監視、橋なし・1 condition smoke で「動く・θ 生存・タグ分離」を検証。
2. **増分2**: 橋（atom→phase→inject、tag=INPUT）を足し、input_E と exp_E の分離を確認。
3. **増分3**: M-split-conn（OTHER→L）+ shuffle 対照 + 多 seed Pool。
4. 各増分で報告、Taka/2AI レビュー。

---

## 8. 2AI 質問（Taka 並行ルート用）

### GPT（監査視点）— E 混線の見分け設計に穴はないか
1. M-E では入力（橋 inject）と経験が同じ state.E を加算する。**input_E_delta / exp_E_delta のタグ台帳 + shuffle（経験のみ入替）で「入力で動いた分」と「経験で育った分」を分離**しようとしている。この見分けに統計的な穴はあるか？（例: 入力→E→そのCIDが活発化→経験イベント増→経験E増、という*間接経路*でタグが汚れないか。間接経路をどう切り分けるか）
2. shuffle 対照は「経験分だけ消える」を期待するが、**入力 E が個性化を作り経験は乗っているだけ**なら shuffle で個性化が残る＝経験は偽。これを「経験が*独自に*個性化を足したか」まで言うには、入力ありなし × 経験ありなし の 2×2 が要るか？最小の対照設計は？
3. v9.7 の反射型自己言及（cid 純粋性汚染）を、このタグ＋shuffle で十分に検出できるか。効果量を「slight（統計的多少差）」に保つ監視指標は何が適切か。

### Gemini（設計視点）— 橋と種類分けの階層整合
1. 橋の addressing は **theme_phase を label.phase_sig に一致**で撃つ（exp(-λd)）。真ん中は **SELF経験→E / OTHER経験→L**。この「位相で相手を選び、E/L で効かせる」と「自己軸→存続(E)／関係軸→結合(L)」は ESDE の存在/関係階層に整合するか？
2. atom 48d→theme_phase の最小投影（主成分 2 軸→atan2）は妥当な placeholder か。より階層整合する atom→phase（例: atom の意味軸のどれを phase に対応させるか）の指針は？
3. 橋（入力＝E/L 注入）と真ん中（経験＝E/L 育成）が同じ通貨で出会う設計は、将来の「人間語→Atom→ESDE→応答→人間」全パイプラインと整合するか。出力（位相励起）まで含めて穴は？

## ファイル
- 参照: `m5_sensor_response_connectivity.md`（経路・④）、`m5_port_inventory_and_plan.md`（口・v9.7）、`m5_typesplit_decay_report.md`（経験式）
- 流用: `v1111c.py:120-141`（addressing）、`genesis_physics.py:240`（inject）
