# child-world 調査: 母集団均質性・写像配線・real≒shuffle の真因（記録のみ・判定なし）

## 自己規律宣言（Code A）
① 過去引用済: `cw_run_lifespan_report.md`（寿命同期 run）／`cw_run_long_report.md`（35k long）／本セッションの統計監査（交絡3点）／Taka・Web Claude 指示（§1 17 CID の中身・§2 写像配線・§3 交絡修正、再 run は §1/§2 の後）／feedback「観察方法を疑う #29」「smoke seed0 を絶対視しない」「単一指標で分類するな」。
② Taka/Web Claude 逐語趣旨: 「real≒shuffle を『CID 個性が効かない』と結論する前に、母集団が均質か／写像が入口で個性を潰しているかを、再 run なしで切り分ける」。
③ 成否判定は Taka。④ 集約語なし。crown 禁止。⑤ 「原理的に効かない」とまだ結論しない（§1-4 を潰す前に断じない）。

## 観察対象注釈ブロック
読＝frozen（`primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv` の n_core=5 17 CID／`childworld_signatures_lifespan.parquet`／`cw_run_lifespan.py` の写像式）。書＝本文書 + `unified/v1301/` のみ。再 run なし（既存データ + 写像式の検証のみ）。親 physics/inject/ledger/state 非書込。

*作成*: 2026-06-20、Code A。*再 run*: なし。

---

## §1 母集団は均質か（17 CID の写像入力4値の散らばり）

17 CID（n_core=5）の写像入力実値:

| cid | B_gen | S_avg | r_core | phase_sig | life |
|---|---|---|---|---|---|
| 代表レンジ | 32.6〜35.4 | 0.274〜0.464 | 0.219〜0.900 | −2.88〜2.38 | 1000〜35000 |

散らばり（CV = std/|mean|）:
| 入力 | CV | range/mean | 判定 |
|---|---|---|---|
| **B_gen** | **0.025** | 0.083 | **ほぼ均質**（17 CID が横並び）|
| S_avg | 0.147 | 0.526 | 中程度 |
| **r_core** | **0.364** | 1.125 | **よく散る** |
| **phase_sig** | 大（mean≈0）| 全周 | **よく散る** |
| life | 0.724 | 1.956 | よく散る |

→ 素の記述: **均質なのは B_gen だけ**。r_core・phase_sig は十分に CID 個性がある。「17 CID 母集団が全体に均質」は成り立たない（B_gen 軸のみ均質）。

## §2 写像は入口で個性を潰すか（入力CV → 出力param CV の伝達）

写像（`cw_run_lifespan.py` load()）= N=B_gen×10 / plb=0.007·(1+0.15·tanh(z_Savg)) / K_sync=0.05+norm(r_core)·0.25 / θ_mu=phase_sig。

| 写像 | in_CV | out_CV | 伝達比 | 設計レンジ使用率 | 判定 |
|---|---|---|---|---|---|
| B_gen→N | 0.024 | 0.025 | 1.01 | 幅28＝mean比 **8%** | 写像は忠実。**源(§1)が均質**で N が動かない |
| S_avg→plb | 0.142 | 0.091 | 0.64 | レンジ([±15%])の **94%** | **設計レンジが ±15% と狭い**＋tanh で圧縮（伝達比0.64）|
| r_core→K_sync | 0.353 | 0.409 | **1.16** | [0.05,0.30] の **100%** | **個性を完全伝達** ✅ |
| phase_sig→θ_mu | 17.8 | 17.8 | 1.00 | [−π,π] の 84% | **伝達するが初期θのみで run 中に減衰** |

→ 素の記述: **「写像が全チャネルで個性を潰す」は誤り**。K_sync は r_core の個性を100%伝え、θ は phase_sig を84%伝える。弱いのは2点だけ:
- **N**: 写像でなく**源（B_gen）が均質**（§1）。
- **plb**: 写像式の **±15% という設計幅が狭い**（個性があっても物理 plb は ±15% しか動けない）＋ tanh の圧縮。

裏付け: 個性を伝えているチャネルでは knob→署名相関が生きている（§3 監査の置換検定: `k_sync→sync_order` perm-p=.0001、`plb→link/label_density` perm-p<.001、両 ratio）。配線は「効くチャネルでは効いている」。

## ★ real≒shuffle の真因（5仮説のどれでもない第6の点）

**shuffle は param 集合を 17 CID 間で並べ替えただけ** → 17 CID の署名の**周辺分布（mean/std）は構造上ほぼ不変**:

| 署名（ratio 1:10）| real mean/std | shuffle mean/std | \|Δmean\| |
|---|---|---|---|
| sync_order | 0.131/0.073 | 0.127/0.064 | 0.0039 |
| link_density | 0.785/0.049 | 0.807/0.057 | 0.0225 |
| label_density | 0.123/0.029 | 0.125/0.028 | 0.0020 |
| n_labels | 41.3/9.4 | 42.0/8.9 | 0.67 |

→ **前報告の「real≒shuffle」は、mean/std という統計が cid→param→署名の pairing を一切見ていないために起きる構造的トートロジー**。shuffle は周辺分布を保存するので、この統計では**原理的に個性を検出できない**。
- pairing を見る正しい検定（knob→署名の置換検定, real 17点で null を作り直し）では `k_sync→sync_order`・`plb→link/label_density` が**両 ratio で p<0.005**＝個性は検出される。
- ＝ 「CID 個性が効かない」を mean/std real≒shuffle から結論するのは**統計の選び方の誤り**。検定を pairing 基準にすると個性は出る。

## 5仮説の切り分け（データ判定。「原理的に効かない」とまだ結論しない）

| 仮説 | データ判定 |
|---|---|
| (1) 母集団が均質 | **部分的** — B_gen のみ均質。r_core/phase_sig は散る（§1）|
| (2) 写像が個性を潰す | **No** — K_sync 100%・θ 84% 伝達。弱いのは plb の設計幅(±15%)と N の源（§2）|
| (3) 観測窓・対照の交絡 | **Yes** — n_labels=run_len トートロジー、canon 二重固定（本セッション監査で既証）|
| (4) 伝播が細い（4数値のみ）| 構造的に真（親の生きた状態を継がない。別件・前ターン論点）|
| (5) 原理的に効かない | **No（少なくとも未支持）** — pairing 検定で有意（★）|
| ★(6) 比較統計が pairing 盲目 | **Yes・real≒shuffle の主因** — mean/std は shuffle で不変 |

## §4 seed 見積もり（再 run 設計用。real ratio10）

| 署名 | within(seed)std | between(cid)std | 信号/ノイズ@3seed | SE<信号/4 に要 seed |
|---|---|---|---|---|
| sync_order | 0.057 | 0.073 | 2.22 | **≈10** |
| link_density | 0.045 | 0.049 | 1.90 | **≈14** |
| label_density | 0.012 | 0.029 | 4.28 | ≈3 |
| n_labels | 3.95 | 9.35 | 4.10 | ≈3 |

→ 3 seed は境界。**sync_order/link_density は ~10〜14 seed 必要**、label_density/n_labels は 3 で可。再 run は ~12 seed を目安。

## §3 再 run 設計（§1/§2 を踏まえた修正案。実装は Taka 承認後）
1. **比較を pairing 基準に**: real vs shuffle を署名 mean/std でなく、knob→署名の paired 相関 + 多数置換 null（perm-p/CI）で。mean/std 対照は廃止または補助。
2. **観測窓を揃える**: 示量署名（n_labels）を異なる run_len で cid 間比較しない。共通窓スナップショット or run_len 正規化（示強量）or 定常後。
3. **対照を対称に**: canon も run_len 可変（今は canon のみ固定＝二重固定）。全対照を同一観測窓に。
4. **写像の弱チャネルを補強検討**: N は源（B_gen）が均質ゆえ別軸要検討、plb の ±15% 設計幅の拡大可否（Taka 判断）。
5. **seed ≈12**（§4）。
6. 過剰精度（3桁）をやめ perm-p/CI を付す。manipulation check（knob→直接物理）と CID 創発を報告で区別。

## やらないこと / 一方向
- やらないこと: 「CID 個性が原理的に効かない」と結論（§1-4 未消化で断じない）、親物理書き戻し、crown、監査結果を「失敗」と記述（交絡は観察事実として記録、判定は Taka）、§1/§2 の前に再 run。
- 一方向: 読＝frozen（per_subject_seed0・既存 parquet・写像式）。書＝本文書 + `unified/v1301/` のみ。親 physics/inject/ledger/state 非書込。

---

## 一文サマリ
child-world 調査（Code A、2026-06-20、再 run なし・判定なし）── real≒shuffle を「CID 個性が効かない」と結論する前に切り分け: **§1 母集団は B_gen のみ均質（CV0.025）で r_core/phase_sig は十分散る**。**§2 写像は K_sync を100%・θ を84% 伝達＝入口で全部潰してはいない**（弱いのは plb の設計幅±15% と N の源均質の2点のみ）。**★ real≒shuffle の主因は第6の点＝比較統計（署名 mean/std）が pairing を見ず shuffle で構造上不変**になること（\|Δmean\|=0.001〜0.02）。pairing を見る置換検定にすると `k_sync→sync_order`・`plb→link/label_density` は両 ratio で p<0.005＝個性は検出される。5仮説判定: (1)部分・(2)No・(3)Yes・(4)構造的真・(5)未支持、(6)Yes が主因。§4 seed は sync/link で ~10〜14 必要。「原理的に効かない」とは結論せず、再 run は pairing 基準・共通観測窓・対称対照・seed≈12 で（Taka 承認後）。
