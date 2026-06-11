# v12 Atomset M5 (post-process) — 特徴度の式をデータで選ぶ工程

日付: 2026-06-11 / **新 run ゼロ**（既存 `v107 *_pre` + `v917 other_records` + `v101 ingestion`、24 seeds）
方法: `m5_formula_selection.py`（4 秒で完走）。机上で式を決めず候補 5 式を同一ログに通して比較（Gemini 4 次元説の轍＝推測を避ける）。
**live M5 hook は未着手。式が Web Claude/Taka 確定後に入る（合意フロー）。**

---

## 0. 結論（先に）

- **成功条件（GPT）を満たす式は `robust_z`（median/MAD ベースの符号付き個体内標準化）だけ。** 推奨が**実データで確認**された。
  - 成功条件 = `corr(contact数, bonus)` が十分低い **かつ** 特徴度分散が非ゼロ。
  - robust_z: self `Pearson=0.004 / Spearman=−0.268`、E3 `Pearson=0.015 / Spearman=−0.401`、**var_feat=1.62/1.71（全式中最大）**、高接触 CID の bonus 独占 **0.00/0.02**。seed 間も `−0.27±0.08`（self）/`−0.41±0.14`（E3）で再現。
- **他の 4 式は全て頻度の裏口**：原案 `linear_z` は Pearson こそ低い（0.05）が **Spearman 0.98**＝bonus が rank で完全に contact 数に従属、**top10% 接触 CID が bonus を 100% 独占**＝M4 の `event_count` 問題が `contact_count` に名を変えて再発。`signed_mr` は過補正で強い**負**相関（−0.94、今度は「接触が少ないほど得」の逆裏口）。`logcount_z` は Pearson 0.99 で最悪。
- **ただし式選定だけでは閉じない（診断 #7）：** robust_z でも **product 累積だと自己系の magnitude が暴走**（self bonus p99=22,941、mean=183,341 vs E3 mean=4.98）＝自己系が出会い系を ~3000 倍支配。count 相関は消えたが、**累積（product）の大きさの裾**が残る。→ **「式 = robust_z」確定の上で、累積の bound/正規化を 1 つ決める判断**が要る（§3）。

---

## 1. 候補式比較（24 seeds、406,908 self events / 91,447 E3 / 3,497 ingestion）

矢印 = 良い方向。**↓ は低いほど良い（裏口なし）、↑ は高いほど良い（差を保持）。**

### self（pulse/α/β/c_conv、ingestion 除く）
| 式 | Pearson(count,bonus)↓ | Spearman↓ | var_feat↑ | top10%が独占する bonus | zero% | seed Spearman |
|---|---|---|---|---|---|---|
| linear_z（Taka 原案・絶対値） | 0.054 | **0.976** | 0.440 | **1.00** | 0.00 | 0.98±0.00 |
| clipped_z | 0.054 | **0.976** | 0.402 | **1.00** | 0.00 | 0.97±0.00 |
| logcount_z | **0.996** | 0.961 | 0.440 | 0.51 | 0.00 | 0.96±0.01 |
| signed_mr（符号付き平均回帰） | −0.464 | **−0.937** | 0.955 | 0.12 | 0.00 | −0.94±0.01 |
| **robust_z（median/MAD・推奨）** | **0.004** | **−0.268** | **1.620** | **0.00** | 0.00 | −0.27±0.08 |

### encounter — E3_contact（主チャネル）
| 式 | Pearson↓ | Spearman↓ | var_feat↑ | top10% bonus | zero% |
|---|---|---|---|---|---|
| linear_z | 0.060 | **0.992** | 0.397 | **1.00** | 0.30 |
| clipped_z | 0.060 | **0.992** | 0.382 | **1.00** | 0.30 |
| logcount_z | **0.991** | 0.982 | 0.397 | 0.33 | 0.30 |
| signed_mr | −0.738 | **−0.959** | 0.961 | 0.15 | 0.30 |
| **robust_z** | **0.015** | **−0.401** | **1.710** | **0.02** | 0.30 |

### encounter — ingestion（希少サブタイプ、別集計）
| 式 | Pearson↓ | Spearman↓ | var_feat↑ | zero% |
|---|---|---|---|---|
| linear_z | 0.368 | 0.968 | 0.336 | 0.65 |
| **robust_z** | **0.218** | **0.084** | **1.281** | 0.65 |

（ingestion は zero% 0.65＝接触が <3 件の CID が 65%。希少なので大半は立ち上がり扱い。robust_z は count 相関ほぼゼロ）

---

## 2. 8 診断（Taka 指定）の結果（robust_z）

1. **contact 数 vs bonus 相関**: self Pearson 0.004 / E3 0.015 ＝ **頻度の裏口なし**（GPT 判定基準クリア）。
2. **特徴度適用後 bonus と contact 数**: 同上（Spearman も −0.27/−0.40 と弱、linear_z の 0.98 と対照的）。
3. **典型接触で倍率≈1**: 倍率の中央値 ≈1（median bonus: self 0.989 = rate ≈2 over a life、E3 0.947、ing 0.629）。※「|倍率−1|<0.05」厳密帯は 9%（MAD 基準が鋭いため）。**ネットでは典型 CID は穏やかに育つ、裾だけ動く**。
4. **稀な接触だけ正負に動く**: robust_z は符号付き＝外れ event のみ ± に振れる。var_feat 1.62/1.71（最大）＝差を保持。
5. **E3 1〜2 件 CID を 0 扱い（K_MIN=3）した対象率**: E3 で zero% 0.30（30% が立ち上がり 0、70% が active）、ingestion 0.65、self 0.00。
6. **高接触 CID の bonus 独占**: robust_z は top10% が bonus の **0.00（self）/0.02（E3）**。linear_z は **1.00**（完全独占）。→ robust_z は独占しない。
7. **自己系 vs 出会い系の支配（合成時）**: ⚠️ **問題あり**。robust_z bonus magnitude:
   | system | median | p90 | p99 | mean |
   |---|---|---|---|---|
   | self | 0.989 | 30.7 | **22,941** | **183,341** |
   | encounter_E3 | 0.947 | 3.99 | 48.6 | 4.98 |
   | encounter_ingestion | 0.629 | 1.39 | 5.68 | 0.150 |
   → 中央値は近い（~1）が、**self の裾が爆発**（数百 event の product が一部 CID で発散）。**合成すると self が出会いを支配**。
8. **seed 間で分布形状が再現**: robust_z seed Spearman self −0.27±0.08 / E3 −0.41±0.14 ＝ **符号も大きさも seed 横断で一貫**。

---

## 3. 残る 1 つの判断（式確定の上で、Web Claude/Taka へ）

**式 = `robust_z` は確定候補（成功条件を満たす唯一）。** だが診断 #7 が示すとおり、**累積 `Π(1+α·f)` のままだと自己系 magnitude が発散**（p99 ~23,000）。count 相関は消えたが「数百 event を掛け続ける」ことで大きさの裾が残り、自己＋出会いの合成で self が支配する。式とは別に **累積の bound を 1 つ決める**必要がある:

- (a) **per-event 倍率は据え置き＋最終 bonus を clip/正規化**（例: cid ごと bonus を log で潰す、または上限）。
- (b) **log 空間 + 減衰累積**（`log_rate += log(1+α·f)`、古い event を減衰）＝発散を構造的に抑える。
- (c) **per-CID で event 数正規化**（幾何平均＝`(Π)^(1/n)`）＝大きさを event 数から外す。ただし「経験を積むほど育つ」意図と相反。
- (d) **自己と出会いを別レンジに正規化してから合成**（#7 の支配を直接是正）。

推奨: **(b) log 空間 + 減衰**（発散抑制と「最近の経験ほど効く」を両立、robust_z の符号性を保つ）。ただし**これも post-process で (a)〜(d) を同じログで比較してから確定**すべき（机上で決めない原則を累積側にも適用）。

---

## 4. 確定事項と次アクション

- **確定（データ選定）**: 特徴度の式 = **robust_z**（median/MAD・符号付き・clip Z=4・scale floor・K_MIN=3 で立ち上がり 0）。成功条件クリア、頻度の裏口なし、独占なし、seed 再現。
- **次（同じ post-process 内）**: 累積の bound (a)〜(d) を同ログで比較し #7（self 支配）を解消する式を選ぶ。
- **その後**: Web Claude/Taka が「robust_z + 累積方式」を確定 → **live M5 hook（機械的）**。**post-process が #7 まで通るまで live に入らない**（合意フロー遵守）。
- 計装の前提（pre-event 凍結）は満たし済み（partner 状態は merge_asof backward、self は過去平均）。

## ファイル
- `m5_formula_selection.py`（式比較、新 run なし）/ `run_m5/formula_selection.json`
- 参照: `experience_computability_audit.md` §6（出会い系チャネル）、`m4_report.md`（near-universal の元問題）
