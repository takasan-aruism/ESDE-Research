# CID-conditioned child-world Long（本スケール・並列）結果 + smoke 比較（記録のみ・判定なし）

## 自己規律宣言（Code A）
① 過去引用済: `cw_run_result_report.md`（smoke=500step=1window の結果）／確定設計（実装設計 §0-11）／台帳 §0（stress OFF・semantic_pressure OFF・最新 V82 箱庭）／**Taka 指摘「500step=1window=スモールスタート、通常 long はもっと長い、並列で速い」**／feedback「24 seeds 単一バッチ・Pool+OMP=1」「smoke seed0 を絶対視しない」／#30（写像=サンプラー）／#33（複数対照）。
② Taka 逐語: 「並列処理すれば早いでしょ？通常並列処理で 5000 ノードクラスの ESDE をぶん回しても3時間ちょっとで Long 終わる」。
③ 成否判定は Taka。④ 集約語なし。crown 禁止。

## 観察対象注釈ブロック
各 child は親 CID ごとの独立子系。観察＝同系内動学＋集計（3 seed 平均→17 CID）。param 導出＝親 CID 形態の read-only 写像（実現値コピーでない＝死線回避）。書込＝`unified/v13_childworld/` のみ・child engine は in-memory・親物理非書込。

*作成*: 2026-06-20、Code A。*コード*: `cw_run_long.py`（並列・long）。*出力*: `childworld_signatures_long.parquet`（204行）+ `childworld_summary_long.json`。

---

## 1. やったこと（並列 long）
- **17 CID × 4対照 × 3 seed ＝ 204 child を「通常 long」= maturation20 + tracking50 = 70 window × 500 = 35,000 step/child**。
- 並列: `multiprocessing.Pool(24)` + `OMP/MKL/OPENBLAS_NUM_THREADS=1`（48 論理=24 物理 Ryzen 24C, HT 利得なし）。**実時間 2008s（約33.5分）**（serial 概算 ~10h を並列化）。
- 設計は smoke と同一（4 knob: N=B_Gen×10 / plb←S_avg / K_sync←r_core / 初期θ←phase_sig、他 canon 固定、stress OFF + semantic_pressure OFF）。

## 2. 成熟度（smoke 500step → long 35,000step）── 500step は確かに1window=小始
real 平均で:
| | smoke(500step) | long(35,000step) |
|---|---|---|
| n_labels（child の cid 数） | 15.7 | **42.5** |
| mean_label_ncore（cid サイズ） | 3.26 | **4.67** |
| sync_order | 0.086 | 0.130 |
| link_density | 0.63 | 0.79 |
→ long で child の cid 構造が成熟（label 約2.7倍・cid サイズ増）。物理署名は平衡まで回った像。

## 3. 入力 knob → 出力署名 の素の相関（smoke → long, 記述のみ・解釈しない, real 17点）
| 入力 knob（CID 由来） | 出力署名 | smoke | → long |
|---|---|---|---|
| K_sync ← r_core | sync_order | +0.635 | **+0.804** |
| plb ← S_avg | link_density | +0.896 | +0.824 |
| plb ← S_avg | label_density | +0.873 | **+0.900** |
| N ← B_Gen×10 | label_density | −0.548 | −0.468 |
| 初期θ ← phase_sig | sync_order | +0.079 | **+0.291** |

→ 素の記述: 相関は long でも**保ち**、K_sync→sync_order と 初期θ→sync_order は**強まった**（初期θは smoke で≈0 だったのが long で +0.29）。「だからこの物理条件がこの性質を生む」とは書かない（判定は Taka）。

## 4. 4 対照の素の分布（long, 3 seed 平均→17 CID 集計, 判定なし）
| 署名 | real (mean/std) | shuffle | random | canon |
|---|---|---|---|---|
| sync_order | 0.130/**0.073** | 0.133/0.061 | 0.104/0.052 | 0.085/**0.029** |
| R_density | 0.045/0.014 | 0.039/0.014 | 0.043/0.013 | 0.046/0.011 |
| link_density | 0.792/0.042 | 0.814/0.049 | 0.823/0.030 | 0.826/0.040 |
| label_density | 0.126/0.025 | 0.127/0.025 | 0.133/0.013 | 0.133/**0.008** |
| n_labels | 42.5/8.1 | 42.7/7.9 | 45.6/4.5 | 44.8/**2.9** |
| mean_label_ncore | 4.67/0.13 | 4.61/0.15 | 4.65/0.11 | 4.65/0.16 |

→ 素の記述: **canon（CID 変化なし）が sync_order/label_density/n_labels で std 最小**。sync_order の std は long で **real(0.073) が4対照中最大**（smoke では real 0.037 は中位だった）。real が shuffle/random と区別つくか（CID 値が効いているか）は対照の並置で、勝ち負け判定は置かない（Taka）。

## 5. smoke（1 window）の像は long（本スケール）で保つか
- 素の事実: §3 の入力→出力相関は long でも**符号・強さとも保持**（K_sync→sync_order・初期θ→sync_order はむしろ強化）。§4 の std も canon 最小・real/shuffle/random 大の関係を保持。
- ＝ smoke の像は long で**反転していない**（smoke seed0 を絶対視しない の規律に対し、本スケールでも崩れていない）。**ただしこれは相関・std の並置であって「real が CID 由来で効いている」「物理条件→性質」の判定・解釈ではない（次は Taka）。**

## やらないこと / 一方向
- やらないこと: 親物理書き戻し、写像を「正しい一つ」に確定、real の勝ち/負け判定、物理条件→性質の因果解釈、crown、5 knob 以外を CID で振る・n_core 跨ぎ（次段）、familiarity を cog 全回しで強行（cid サイズ分布で代理、familiarity 本体は別途 cog 要）。
- 一方向: 読＝frozen（per_subject_seed0 / 現行 engine 構成 / v19g_canon）。書＝`unified/v13_childworld/` のみ。child engine は in-memory。親 physics/inject/ledger/state 非書込。

---

## 一文サマリ
CID-conditioned child-world Long 並列（Code A、2026-06-20、記録のみ判定なし）── 500step=1window=スモールスタートを受け、204 child を「通常 long」=35,000step/child で **Pool(24)+OMP=1 並列・実時間 33.5分**（serial ~10h を並列化, Taka 指摘どおり）。long で成熟（real: n_labels 15.7→42.5, mean_label_ncore 3.26→4.67）。**入力→出力 素の相関は smoke→long で保持・一部強化（K_sync→sync_order +0.64→+0.80, plb→label_density +0.87→+0.90, 初期θ→sync_order +0.08→+0.29）**。4対照: canon の std 最小・real/shuffle/random 大、sync_order std は long で real 最大。smoke の像は long で反転せず保持。ただし相関/std の並置であり「CID が効いているか/物理条件→性質」の判定・解釈は書かず Taka。出力 = signatures_long.parquet + summary_long.json。
