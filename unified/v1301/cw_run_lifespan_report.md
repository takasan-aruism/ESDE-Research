# CID-conditioned child-world 寿命同期版（1:1 / 1:10・並列）結果 + long 比較（記録のみ・判定なし）

## 自己規律宣言（Code A）
① 過去引用済: `cw_run_long_report.md`（35,000step 固定 long の結果）／`cw_run_result_report.md`（smoke=1window）／確定設計（実装設計 §0-11）／台帳 §0（stress OFF・semantic_pressure OFF・最新 V82 箱庭）／**Taka 確定「本体の時間経過を反映＝child の run 長を CID 寿命に合わせる」**／feedback「24 seeds 単一バッチ・Pool+OMP=1」「smoke seed0 を絶対視しない」／#30（写像=サンプラー）／#33（複数対照）。
② Taka 逐語（確定）: run 長 = CID 寿命 × 倍率（1:1, 1:10）, 上限35000, CID が死んだら停止。param（4 knob）は誕生 M_c のまま据え置き。
③ 成否判定は Taka。④ 集約語なし。crown 禁止。

## 観察対象注釈ブロック
各 child は親 CID ごとの独立子系。観察＝同系内動学＋集計（3 seed 平均→17 CID）。今回の差分は **run 長を CID 寿命に同期**（long は全 child 35,000step 固定だった）。寿命 = `(host_lost_window∧70 − birth_window)×500`。run 長 = `min(35000, life × ratio)`。param 導出＝親 CID 形態の read-only 写像（実現値コピーでない＝死線回避）。書込＝`unified/v1301/` のみ・child engine は in-memory・親物理非書込。

*作成*: 2026-06-20、Code A。*コード*: `cw_run_lifespan.py`（並列・寿命同期）。*出力*: `childworld_signatures_lifespan.parquet`（408行 = 17 CID × 4対照 × 3 seed × 2 ratio）+ `childworld_summary_lifespan.json`。

> 注: 前セッションは生 run（408 child）完走・parquet 保存まで成功し、`main()` の集計段で **`real` の agg に `theta_mu` を入れ忘れたまま `real.theta_mu.corr` を呼び落ちた**だけ。生データは無傷。本セッションでスクリプトを修正（`theta_mu=('theta_mu','first')` を agg に追加）し、保存済み parquet から集計し直した（再 run なし）。

---

## 1. やったこと（寿命同期・並列）
- **17 CID × 4対照 × 3 seed × 2 ratio ＝ 408 child**。long との唯一の差分は **run 長**:
  - **1:1** … run 長 = CID 寿命そのもの（median 17,000step, min 1,000 / max 35,000, **35000 到達は 2/17 CID のみ**）。
  - **1:10** … run 長 = 寿命×10 を 35,000 で頭打ち（**35000 到達は 15/17 CID**＝ほぼ上限に張り付き）。
- 設計は long と同一（4 knob: N=B_Gen×10 / plb←S_avg / K_sync←r_core / 初期θ←phase_sig、他 canon 固定、stress OFF + semantic_pressure OFF、写像=サンプラー#30、4対照#33）。

## 2. 入力 knob → 出力署名 の素の相関（real 17点・記述のみ・解釈しない）
| 入力 knob（CID 由来） | 出力署名 | long(35k固定) | 1:1（寿命） | 1:10（寿命×10∧35k） |
|---|---|---|---|---|
| CID 寿命 life | n_labels | （未測） | **+0.849** | +0.265 |
| K_sync ← r_core | sync_order | +0.804 | +0.656 | **+0.772** |
| plb ← S_avg | link_density | +0.824 | +0.791 | +0.726 |
| plb ← S_avg | label_density | +0.900 | +0.697 | **+0.848** |
| 初期θ ← phase_sig | sync_order | +0.291 | **+0.537** | +0.251 |

→ 素の記述（判定しない）:
- **life→n_labels は 1:1 で +0.85 と強いが、1:10 で +0.27 に落ちる**。1:1 は run 長が寿命に比例（長命 CID ほど多く回る）、1:10 はほぼ全 child が 35,000 で頭打ち（run 長がもう寿命を反映しない）── という run 長の差と整合する記述。「寿命が cid 構造数を決める」とは書かない。
- K_sync→sync_order・plb→label_density は **1:10 で long 寄りに強まる**（時間が伸びると long の像へ寄る、という素の並置）。
- 初期θ→sync_order は **1:1 で +0.54 と最大**、1:10 / long では弱まる（短い run ほど初期位相の痕跡が残る、という記述）。

## 3. 4 対照の素の分布（3 seed 平均→17 CID 集計, 判定なし）

**ratio 1:1（run 長 = 寿命）**
| 署名 | real | shuffle | random | canon |
|---|---|---|---|---|
| sync_order | 0.119/**0.066** | 0.113/0.055 | 0.099/0.070 | 0.086/**0.013** |
| R_density | 0.042/0.019 | 0.044/0.026 | 0.049/0.016 | 0.052/0.018 |
| link_density | 0.734/0.093 | 0.737/0.094 | 0.771/0.067 | 0.788/**0.029** |
| label_density | 0.087/0.049 | 0.088/0.052 | 0.106/0.034 | 0.106/**0.010** |
| n_labels | 29.1/**16.2** | 29.6/17.2 | 36.0/11.6 | 35.8/**3.3** |
| mean_label_ncore | 3.92/0.75 | 3.78/0.80 | 4.13/0.54 | 4.03/0.17 |

**ratio 1:10（run 長 = 寿命×10∧35k）**
| 署名 | real | shuffle | random | canon |
|---|---|---|---|---|
| sync_order | 0.131/**0.073** | 0.127/0.064 | 0.104/0.046 | 0.085/0.029 |
| R_density | 0.043/0.015 | 0.039/0.014 | 0.047/0.016 | 0.046/0.011 |
| link_density | 0.785/0.049 | 0.807/0.057 | 0.816/0.044 | 0.826/0.039 |
| label_density | 0.123/0.029 | 0.125/0.028 | 0.134/0.025 | 0.133/**0.009** |
| n_labels | 41.3/9.4 | 42.0/8.9 | 45.3/8.2 | 44.8/**2.9** |
| mean_label_ncore | 4.59/0.37 | 4.56/0.27 | 4.53/0.17 | 4.65/0.16 |

→ 素の記述（判定しない）:
- **canon（CID 変化なし）が両 ratio で std 最小**（long と同じ関係を保持）。
- **sync_order の std は両 ratio とも real が4対照中最大**（1:1 0.066・1:10 0.073）── long（0.073）と一致。
- **1:1 では real/shuffle の n_labels・label_density の std が著しく大（n_labels std 16.2/17.2 vs random 11.6 / canon 3.3）**。1:1 は run 長が CID ごとにバラける（寿命依存）ため child 間のばらつきが大きい、という記述。1:10 では頭打ちで run 長が揃い、ばらつきが縮む。
- real が shuffle/random と区別つくか（CID 値が効いているか）は対照の並置で、勝ち負け判定は置かない（Taka）。

## 4. long（35k固定）の像は寿命同期で保つか
- 素の事実: §2 の入力→出力相関は **符号は全て保持**。強さは run 長で動く（1:1 は短い → 初期θ痕跡↑・成熟系相関↓、1:10 は長い → long の像へ寄る）。§3 の std も **canon 最小・real sync_order std 最大** の関係を両 ratio で保持。
- ＝ long の像は寿命同期で**反転していない**。**ただしこれは相関・std の並置であって「real が CID 由来で効いている」「物理条件→性質」の判定・解釈ではない（次は Taka）。**

## やらないこと / 一方向
- やらないこと: 親物理書き戻し、写像を「正しい一つ」に確定、real の勝ち/負け判定、物理条件→性質の因果解釈、crown、4 knob 以外を CID で振る・n_core 跨ぎ（次段）、familiarity を cog 全回しで強行。
- 一方向: 読＝frozen（per_subject_seed0 / 現行 engine 構成）。書＝`unified/v1301/` のみ。child engine は in-memory。親 physics/inject/ledger/state 非書込。

---

## 一文サマリ
CID-conditioned child-world 寿命同期版（Code A、2026-06-20、記録のみ判定なし）── Taka 確定「child の run 長を CID 寿命に合わせる」を受け、408 child を **run 長 = min(35000, life×ratio), ratio∈{1,10}** で並列実走（1:1 は寿命そのもの・35k 到達2/17、1:10 はほぼ頭打ち・35k 到達15/17）。**life→n_labels は 1:1 で +0.85・1:10 で +0.27**（run 長が寿命比例→頭打ちへ移る差と整合）。K_sync→sync_order・plb→label_density は 1:10 で long 寄りに強化、初期θ→sync_order は 1:1 で +0.54 最大。4対照: canon std 最小・real sync_order std 最大を両 ratio で保持、1:1 は寿命バラつきで n_labels std 大。long の像は寿命同期で反転せず保持。ただし相関/std の並置であり「CID が効いているか/物理条件→性質」の判定・解釈は書かず Taka。前セッションの集計バグ（`theta_mu` を agg 未投入）を修正し保存済み parquet から再集計（再 run なし）。出力 = signatures_lifespan.parquet + summary_lifespan.json。
