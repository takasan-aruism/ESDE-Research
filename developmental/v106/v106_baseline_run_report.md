# v10.6 random-baseline 解析 run 報告書

*生成*: 2026-05-06、Code A
*親*: `v106_baseline_analysis_brief.md` (Web Claude 依頼書) + Taka 指摘 (2026-05-05)
*対象*: Web Claude → Taka

## 0. 一文サマリ

軸内 L1 正規化 48 次元 cosine 類似度はランダムでも mean 0.526 を取る性質があるため観察値の絶対値は finding ではない、という Taka 指摘を **uniform 一様分布 + 実 cid 軸内シャッフル の 2 種ベースライン × 24 seeds 単一バッチ** で定量検証した結果、**観察値 atom 平均 0.462 はランダムベースライン (uniform 0.526 / shuffled 0.516) を下回り**、strong_24/24 atom も observed 100 < uniform 123 (ランダムの方が多い) という逆転が判明、|z|>2 かつ 24-seed 一貫の真の finding は **above_baseline 47 atom (PER 12 / BOD 5 / ACT 5 等の身体感覚系)** と **below_baseline 176 atom (EMO 21 / PRP 19 / FND 14 等)** に分かれ、**ESDE 構造ベクトルは身体感覚カテゴリ (BOD z+2.48 / PER z+2.27) でのみランダムを有意に上回り、論理 (LOG z-8.28) / 価値 (VAL z-7.84) / 空間 (SPC z-7.54) / 存在論 (EXS z-5.39) / 時間概念 (TIM z-4.69) / コミュニケーション (COM z-4.63) / 関係 (REL z-4.14) などほぼすべてのカテゴリでランダムを有意に下回る** という結果になった。

---

## 1. 実装

| 項目 | 値 |
|---|---|
| 入力 | 既存 atom_profiles_cache.npz、cid_atom_topk_seed*.csv、cid_structure_profile_seed*.csv |
| 出力 | `outputs/main/baseline/` 配下 30 ファイル + `reports/baseline_analysis_report.md` |
| 実行時間 | **1.38 秒** (24 seeds 単一バッチ) |
| baseline 方式 | uniform (一様分布 + 軸内 L1 正規化) + shuffled (実 cid 軸内シャッフル) の 2 種 |
| ランダム seed | numpy seed = 106 (本番 seed と分離、再現性担保) |
| 真の finding 基準 | \|z\| > 2.0 かつ 24 seeds direction 一貫 (uniform OR shuffled いずれか満たせば候補) |

---

## 2. ベースライン分布の検証

### 2.1 全 325 atom × 24 seeds の rank_1_sim mean

| 集計 | mean | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|
| **observed** | **0.462** | - | - | - | - | - | - |
| uniform baseline | **0.526** | 0.085 | 0.336 | 0.464 | 0.518 | 0.589 | 0.763 |
| shuffled baseline | **0.516** | 0.070 | 0.318 | 0.469 | 0.531 | 0.567 | 0.656 |

→ **観察値は両ベースラインより低い** (uniform 比 -0.065、shuffled 比 -0.054)。

### 2.2 strong_24/24 atom 数

| 区分 | atom 数 |
|---|---|
| observed | 100 |
| **uniform baseline** | **123** |
| shuffled baseline | 85 |

→ uniform baseline では **ランダムでも 123 atom が常に strong**。観察 100 はそれを下回る。

### 2.3 24/24 unmatched atom 数 (max_sim < 0.3 を全 24 seeds で達成)

| 区分 | atom 数 |
|---|---|
| observed | 14 |
| uniform baseline (strong-rate=0) | 27 |
| shuffled baseline (strong-rate=0) | 49 |

→ ランダムなら 27-49 atom 程度の「欠落」は普通に発生。観察 14 はむしろ少ない。

---

## 3. category-level z-score (uniform baseline 比)

z_uniform 順 (低い順、構造的盲点ほど上):

| category | n_atoms | obs_strong | unif_strong | shuf_strong | delta_atoms | z_uniform | z_shuffled |
|---|---|---|---|---|---|---|---|
| LOG | 4 | 0 | 3 | 3 | -3 | **-8.28** | -4.56 |
| VAL | 10 | 0 | 4 | 0 | -4 | **-7.84** | -5.20 |
| SPC | 6 | 1 | 6 | 3 | -5 | **-7.54** | -3.13 |
| EXS | 11 | 0 | 7 | 6 | -7 | **-5.39** | -4.44 |
| TIM | 7 | 3 | 6 | 3 | -3 | **-4.69** | -0.81 |
| COM | 12 | 5 | 8 | 4 | -3 | -4.63 | -2.21 |
| REL | 4 | 0 | 0 | 0 | 0 | -4.14 | -4.51 |
| CHG | 7 | 4 | 5 | 3 | -1 | -4.08 | -1.73 |
| WLD | 12 | 7 | 10 | 4 | -3 | -3.87 | -1.49 |
| ELM | 12 | 3 | 5 | 3 | -2 | -3.63 | -1.53 |
| ABS | 8 | 2 | 3 | 4 | -1 | -3.37 | -3.96 |
| FND | 24 | 4 | 12 | 10 | -8 | -3.11 | -2.45 |
| STA | 11 | 1 | 2 | 3 | -1 | -3.07 | -3.03 |
| EMO | 30 | 1 | 3 | 8 | -2 | -2.61 | -4.72 |
| NAT | 4 | 0 | 0 | 0 | 0 | -2.44 | +0.49 |
| ECO | 12 | 8 | 7 | 3 | +1 | -2.21 | -0.77 |
| BEI | 8 | 4 | 3 | 3 | +1 | -1.76 | -1.01 |
| PRP | 46 | 12 | 13 | 7 | -1 | -1.68 | +0.04 |
| ACT | 28 | 14 | 11 | 6 | +3 | -1.50 | -0.45 |
| SOC | 22 | 7 | 8 | 4 | -1 | -1.48 | -1.91 |
| COG | 13 | 4 | 5 | 5 | -1 | -0.24 | -1.76 |
| MAT | 6 | 1 | 0 | 0 | +1 | -0.05 | +1.20 |
| **PER** | **20** | **12** | 1 | 3 | **+11** | **+2.27** | +1.18 |
| **BOD** | **8** | **7** | 1 | 0 | **+6** | **+2.48** | +1.65 |

→ **ランダムを有意に上回るのは BOD と PER のみ**。
→ それ以外のすべてのカテゴリでランダムを下回るか有意差なし。

特筆:
- **VAL (z-7.84)**: ランダムなら 4 atom strong、観察は 0 atom。価値判断は ESDE で表現できない。
- **LOG (z-8.28)**: ランダムなら 3 atom strong (cause/effect/reason 系)、観察も 3 atom が mixed だが strong_24/24 では 0 atom。
- **EMO (z-2.61)**: 30 atom 中 strong ランダム 3 / 観察 1 (manifest のみ)。感情系列は Genesis 系で表現困難。
- **TIM (z-4.69)**: TIM.moment が観察結果で頻出していたが、実は **ランダムベースラインの方が高い接地度** (uniform 0.763 > observed 0.612)。

---

## 4. 真の finding atoms — uniform AND shuffled 両方で |z|>2

223 atom が真の finding (47 above + 176 below)。**両ベースラインで一貫: 105 atom**。

### 4.1 above_baseline (47 atom) — ESDE 構造の真の特異性

カテゴリ内訳:

| category | n |
|---|---|
| PER | 12 |
| SOC | 6 |
| BOD | 5 |
| ACT | 5 |
| COG | 4 |
| PRP | 4 |
| EMO | 2 |
| その他 11 cats | 各 1 |

**両ベースラインで真の finding (Y/Y)**:
- **五感**: PER.smell (z+6.46/+3.46), PER.see (+6.13/+2.46), PER.odorless (+5.41/+3.10), PER.taste (+4.37/+3.30)
- **身体部位**: BOD.hip (+4.28/+2.44), BOD.face (+2.82/+3.06)
- **時間出現**: TIM.appear (+4.94/+2.68)
- **物性**: PRP.young (+3.56/+2.23), PRP.small (+3.38/+3.09)
- **元素**: ELM.light (+2.20/+2.54)

**uniform 単独で finding (CHG.begin など)**:
- CHG.begin (z+6.12 uniform / +0.43 shuffled): **shuffled では消える**。集団平均 51% で支配的だったが、軸間対応関係には依存しない (= 軸ごとの値分布だけで決まる)。
- TIM.moment: 同様。

→ 「身体感覚 (BOD/PER) は ESDE 構造ベクトルが軸間対応関係を含めて捉えている」ことが確認された。CHG.begin の優位は実は軸内分布だけで説明できる「擬似的な」優位だった。

### 4.2 below_baseline (176 atom) — 真の構造的盲点

カテゴリ内訳:

| category | n | 主要 atom |
|---|---|---|
| EMO | 21 | despair, hate, love, fear, joy, hope, anger, ... ほぼ全感情 |
| PRP | 19 | strong, weak, near, far, hot, cold, light, heavy, ... |
| FND | 14 | language, languageless, temporality, history, time, ... |
| ACT | 11 | destroy, fall, sink, agitate, abandon, dissolve, ... |
| SOC | 11 | criticize, attack, family, individual, request, ... |
| EXS | 10 | void, death, life, presence, absence, spirit, ... |
| ELM | 10 | sun, fire, water, wind, earth, star, darkness, ... |
| VAL | 9 | incorrect, truth, falsehood, profane, evil, sacred, good, ... |
| WLD | 9 | nonscience, religion, outer_realm, ... |
| COM | 9 | conduct, conflict, cooperate, secret, announce, ... |
| SPC | 6 | place, inside, outside, nowhere, reverse, ... |
| ABS | 6 | exempt, foolish, self, responsibility, ... |
| ECO | 5 | loss, currency, waste, price, ... |
| TIM | 5 | past, now, period, indefinite, come |
| STA | 5 | danger, war, illness, poverty, wealth |
| BEI | 5 | plant, root, parent, ... |
| CHG | 5 | decay, retreat, end, stay, advance |
| LOG | 4 | unreason, cause, effect, reason |
| COG | 4 | confusion, forget, ignorance, mindless |
| REL | 3 | together, different, same |
| NAT | 3 | flower, tree, sea (? river は below ではない) |
| MAT | 1 | naked |
| PER | 1 | numb |

最強の盲点 (両ベースラインで |z|>5):
- VAL.incorrect (-15.82/-6.08), VAL.truth (-15.74/-5.49)
- EXS.void (-14.47/-8.09), FND.language (-12.74/-3.24)
- TIM.past (-12.11/-2.65), TIM.now (-12.10/-3.98)
- COM.conflict (-11.83/-7.57), STA.danger (-11.67/-13.05)
- LOG.unreason (-11.35/-12.22), ECO.loss (-11.17/-12.05)
- STA.war (-11.02/-12.20)
- **ACT.destroy (-10.08/-23.68)** ← shuffled で z-23.68、構造的に最も強い盲点

---

## 5. v10.6 phase_report.md 修正提案

### 5.1 削除すべき主結果

- **「mean_max_sim 0.608」を主結果から外す**: ランダムベースラインの 0.526 と同程度であり、絶対値としては finding ではない
- **「24/24 unmatched 14 atom が構造的盲点」も慎重に**: ランダムベースラインでも 27 atom 程度の unmatched は発生する。ただし z>2 で「観察値の方が baseline 平均より顕著に低い」atom は構造的盲点として確定 (上記 176 atom リスト)
- **「全 cid の 51% が CHG.begin に集中」も再評価必要**: CHG.begin は uniform baseline で z+6.12 だが shuffled で z+0.43 → **軸間対応関係に依存しない** = 「集中」は構造的特徴ではなく軸内分布だけで起きる人工物
- **「TIM.moment が 5 パターン支配」も再評価**: TIM.moment は uniform baseline で観察値の方が低い (z-10.07)。ランダムなら TIM.moment との接地はもっと高いはずで、観察された支配は **ランダムを下回った中での相対的支配** に過ぎない

### 5.2 真の主結果として残すもの

1. **BOD/PER 両カテゴリだけが正の z-score**: ESDE Genesis 系は身体部位 (eye/ear/mouth/face/head/hand/hip) と五感 (taste/smell/see/hear/sweet/salty/...) を **軸間対応関係も含めて構造化** している唯一のカテゴリ。
2. **本当の構造的盲点 176 atom**: |z|>2 で 24-seed 一貫の盲点。特に EMO 21 / PRP 19 / FND 14 / ACT 11 / SOC 11 件。
3. **ACT.destroy z-23.68 (shuffled)**: 「破壊」概念が ESDE 構造ベクトル空間で最も強い構造的欠落。Taka 整理「不可視による論理的可視化」の最強事例。
4. **集団平均の罠の二重重ね**: v10.6 smoke で「集団平均 51% CHG.begin」を検出 → 層化解析で「short-lived 偏り」と判明 → ベースライン解析で「軸間対応に依存しない人工物」と判明。観察値の解釈は **3 段階の検証** が必要だった。

### 5.3 v10.7 以降への含意

- 関係構造取り込み時もベースライン比較を必須化
- cosine 類似度の絶対値は意味を持たない。常に z-score / delta / direction 一貫性で評価
- 「ESDE が表現できる」とは「ランダムベースラインを軸間対応含めて有意に上回る」と再定義

---

## 6. 出力ファイル一覧

```
developmental/v106/outputs/main/baseline/
├── baseline_atom_alignment_seed{0..23}.csv  (24 file、uniform + shuffled 統合)
├── baseline_atom_summary.csv                (atom × method × 24-seed 集計、650 行)
├── baseline_category_summary.csv            (24 cat × method)
├── observed_vs_baseline_atom.csv            (atom × z-score)
├── observed_vs_baseline_category.csv        (= baseline_category_summary)
├── true_finding_atoms.csv                   (223 atom: 47 above + 176 below)
└── baseline_summary.json                    (実行メタ情報)

developmental/v106/reports/
└── baseline_analysis_report.md              (本解析レポート)
```

---

## 7. 完了条件チェック

### 7.1 機能完了
- [x] ランダムベースライン生成 (24 seeds × per-seed cid 数 × 48 dim、uniform + shuffled 2 種)
- [x] ベースライン atom alignment 計算 (325 atom × 24 seeds × 2 method)
- [x] observed vs baseline 比較 (z-score、delta、direction 一貫)
- [x] カテゴリレベル比較 (z-score 24 cats)
- [x] 真の finding atom 同定 (|z|>2 かつ 24-seed 一貫)

### 7.2 規律完了
- [x] v105 配下に書き込みなし (path 縛り維持)
- [x] 出力先 v106/outputs/main/baseline/ 配下のみ
- [x] 仮説に影響されない実装 (仮説 A-D は事前提示されたが実装は数値計算のみ)
- [x] ウェット概念禁止維持 (科学的記述に統一)
- [x] 24 seeds 単一バッチで実行

### 7.3 出力検証
- [x] 各 CSV が想定スキーマで生成
- [x] baseline_analysis_report.md 生成
- [x] z-score 分布が妥当 (極端外れ値: ACT.destroy z-23.68、VAL.incorrect z-15.82 等は実データ由来として確認)

---

*以上、Code A による v10.6 ランダムベースライン解析 run 報告。Web Claude が phase_report.md 修正に反映する。*

---

## 8. 時間軸混在 caveat (Taka 指摘 2026-05-06、追記)

本 v10.6 cid 構造ベクトルは **誕生時固定値 + run 終了スナップショット + run 全体集約** の 3 種タイミングが 48 次元に同居しており、**ESDE の動学的振る舞いは捕捉していない**。本ベースライン解析の z-score は「run 集約 + 終了スナップショット時点の cid と Atom の対応関係」として解釈すべき。

特に:
- **BOD/PER の正の z は時間軸混在の影響を受けにくく信頼できる**
- **TIM.moment / ACT.destroy の極端な負 z は動学観察欠如のアーティファクト混入の可能性**
- **構造的盲点 176 atom は (A) 真の構造的欠落と (B) 動学観察欠如アーティファクトの混在**

詳細整理: → `v106_temporal_axis_caveat.md` 参照

