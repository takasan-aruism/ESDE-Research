# v1302 (B) 交絡除去 smoke — overlay 条件による再検証

## 動機：懐疑チェックで見つけた交絡
元 (B) 移植 smoke（`cw_v1302_abx.py` / `cw_v1302_B_mature.py`）の worker は、B 条件で
`run_injection()` を**丸ごとスキップ**し、`transplant()` が移植 subgraph のノードだけを
`alive_n` に登録していた（`cw_v1302_abx.py:137-139`、`cw_v1302_B_mature.py:56-63`）。

実測 t0 fingerprint：

| 条件 | t0_alive_n (n2) | t0_alive_n (n5) | 容量 N | 初期化 |
|---|---|---|---|---|
| canon / A / Nfix | 120 | 338 | 同左 | `run_injection()` フル |
| **B（移植）** | **12〜20** | **34〜50** | 同左 | injection skip・移植のみ |

→ B は「canon＋親topology」ではなく、**容量 N の 80〜85% が空のエンジンに小さな移植
subgraph を置いてゼロ近くから再成長させたもの**。late 署名は再成長を駆動する N(=b_gen×10)
と汎用 plb に支配され、移植 topology（19/120）は希釈・上書きされる。
**B の Mantel≈0 を「topology は identity を運ばない」と解釈できない**（空start再成長の washout と交絡）。

バグ（コードが意図と違う動作）ではない。B と対照条件が baseline population を共有していない
**推論上の交絡**。

## 修正：Bov(overlay) 条件
同一 `make_engine` / RUN_LEN(35k) / N / seed offset で 3 条件並走（`cw_v1302_B_overlay.py`）：

- **canon** : `run_injection()` のみ（canonical baseline, plb=BASE_PLB）。
- **B** : 元レシピ = injection skip + transplant 置換（交絡あり版を継続性のため保持）。
- **Bov** : `run_injection()`（canon と同一 baseline）+ 親 topology を `add_link` で overlay
  grafting。E/θ は触らない（baseline を壊さない）。`transplant_overlay` は親 field_nodes を
  「現在 alive な node」へ写像し配線のみ上乗せ。

topology source = mature field τ=50（成熟 window・閉路あり、元 smoke で唯一正 blip を出した τ）。
covered = n2:35 / n5:7（cyclic n2:24 / n5:6）。seeds=3。bit-identity 一致（B/Bov とも 2回再現）。

## 結果

| stratum | 条件 | late r | p | t0_alive_n | t0_loops | t0_maxR | +links |
|---|---|---|---|---|---|---|---|
| **n2 (35cid)** | canon | 0.146 | 0.069 | 119.9 | 50.9 | 4.46 | 0 |
| | B（旧・置換） | 0.066 | 0.238 | **19.6** | 2.7 | 0.0 | 18.3 |
| | **Bov（overlay）** | 0.076 | 0.21 | **119.9** | 186.4 | 4.57 | 16.8 |
| **n5 (7cid)** | canon | −0.014 | 0.452 | 340.7 | 136.6 | 4.96 | 0 |
| | B（旧・置換） | **0.402** | 0.055 | **50.4** | 3.1 | 0.0 | 49.7 |
| | **Bov（overlay）** | −0.196 | 0.798 | **340.7** | 314.7 | 4.92 | 48.3 |

### 交絡除去の証明 ✓
- Bov の t0_alive_n は **canon と完全一致**（119.9 / 340.7）。空start交絡は除去された。
- 親 topology の grafting も成功：loops が canon 比 ~2.3倍（n2 50.9→186.4 / n5 136.6→314.7）、
  +links 16.8/48.3。「同一 baseline に親の閉路 topology を上乗せした」状態が確実に作れている。

### 結論（交絡抜き）
1. **頑健な n2（35cid）では canon ≈ B ≈ Bov ≈ 0.07–0.15、全て非有意。**
   baseline を揃えても親 topology の上乗せは transfer をまったく増やさない。
2. **旧 B の唯一の正シグナル（n5 r≈0.4）は空エンジン start の artifact だった。**
   baseline を揃えた Bov では n5 r=−0.196 に反転消失。前回報告の「弱いが正の blip
   （B_t50 n2=0.284 / B_t10 n5≈0.4）」は *弱い topology transfer* ではなく、
   **空start再成長の偽シグナル**（空start は outcome の N 依存を増幅し、N=b_gen×10 が親 scalar を
   一部含むため見かけの相関が出る）。
3. 元結論「topology は identity を運ばない」は**正しく、交絡を抜くとより明確**。
   成熟・閉路ありの field を full canonical baseline に grafting しても null。

## 残る caveat（Taka 判断・本smokeでは未対応）
- **Mantel の親側ベクトルが scalar 成熟量 [s_avg, r_core, conc]**（A の plb を作るのと同じ vector）。
  topology が *この scalar vector と直交する* 形で transfer した場合は原理的に見えない。
  厳密な topology-transfer 検定には親 *topology* 距離（隣接/閉路構造）×子 *topology* 署名が要る。
  本smokeは「空start交絡」という具体的欠陥の切り分けに限定。
- **A の transfer は一部トートロジー的**：`strength_plb` が plb を親ベクトルの単調関数として設定し、
  Mantel はまさにその親ベクトルと相関を測る。「親強度比例ノブ→ノブが効く」は半ば自明で、
  A vs B のコントラストを誇張している可能性。A 本命の解釈時に留意。
- n5 は covered 7cid で原理的に低パワー。数値の揺れ（B +0.4 / Bov −0.2 / canon −0.01）は
  n=7 の雑音と整合。決定は n2（35cid）で行うべき。

## 判定
判定なし（Taka / Web Claude）。実装側は smoke 完了で停止、main run へは進まない。
file:line 対応は上記に明記（ズレ点検用）。
