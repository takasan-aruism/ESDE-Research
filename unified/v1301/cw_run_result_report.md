# CID-conditioned child-world 本番結果 — 物理 param → 生まれた ESDE 性質（記録のみ・判定なし）

## 自己規律宣言（Code A）
① 過去引用済: 確定設計（実装設計 §0-11）／台帳 `physics_cid_ledger.md §0`（確定: stress OFF・semantic_pressure OFF・最新 V82 箱庭縮小）／`feasibility_check_report`（GO）／`wiring_probe`（physics.params 後書き可・K_sync 設定可）／#30（写像＝サンプラー・正しさを結論の土台にしない）／#33（複数対照・一つを正解にしない）／N 正規化（GPT）。
② Taka 逐語（仕様 §11）: 「n_core=5 の17 CID で 4 knob（N=B_Gen×10／plb←S_avg／同期系←r_core／初期θ←phase_sig）、他 canon 固定・stress/semantic_pressure 切る・現行 main 縮小。まず少数で回るか＋§5 の『効く』1点確認 → 17×3seed×4対照。物理署名（N 正規化込み）＋位相状態を取り、『物理 param→ESDE 性質』の対応を見る。判定・解釈は書かない」。
③ 成否判定は Taka（success/fail 置かない）。④ 集約語なし。crown 禁止（「自我/会話/良い設計」と書かない）。

## 観察対象注釈ブロック
各 child は親 CID ごとの独立子系。観察＝各 child の同系内動学＋集計（3 seed 平均→17 CID）。child 同士・親との座標対応はしない。param 導出＝親 CID 形態（B_Gen/S_avg/r_core/phase_sig）を read-only で param に写すのみ（実現値コピーでない＝死線回避）。

*作成*: 2026-06-20、Code A。*コード*: `cw_verify.py`（検証）/ `cw_run.py`（本番）。*出力*: `childworld_signatures.parquet`（204行）+ `childworld_summary.json`。

---

## 1. 実走の設定（確定設計どおり）
- 母集団 = **n_core=5 の17 CID（seed0, M_c 形態取得可）**。**4 対照（real / shuffle / random / canon）× 3 seed ＝ 204 child**、各 **500 step**。
- 4 knob（real, サンプラー #30）: **N=B_Gen×10**[326,354] / **plb←S_avg**[0.0060,0.0080]（canon 0.007 の ±15%・強 knob なので小幅）/ **K_sync←r_core**[0.05,0.30]（同期系を採用, gamma でなく K_sync）/ **初期θ←phase_sig**（von Mises κ=4, 世界の初期条件）。他 param は **canon 固定**。
- **stress OFF ＋ semantic_pressure OFF**（pressure_prob=0）。本体 main との差は §5 で明記。
- 対照: real＝CID 値で4 knob ／ shuffle＝CID 値を固定置換で入れ替え ／ random＝同範囲ランダム ／ canon＝元 param 固定（N=mean(B_Gen)×10=334, plb=0.007, K_sync=0.1, θ 一様）。

## 2. 検証フェーズ（§8 本番前）── 全項目パス
- **4 knob 立つ** ✓ ／ **stress・semantic_pressure OFF** ✓（stress_enabled=False, pressure_prob=0.0）。
- **§5「効く」1点確認** ✓: K_sync を 0.05 vs 0.50 で **sync_order 0.0068→0.0970（差0.090）**＝後書き K_sync は step で読まれ実際に効く（「書けても読まれねば無視」を排除）。
- コスト 3.1s/child → 204 child 実測 **642s（約11分）**。

## 3. 本番結果 ── 物理 param（入力）→ 生まれた ESDE 性質（出力）
全 child **alive_ratio = 1.0（崩壊なし）**。real の per-cid 入力→出力（3 seed 平均・素の記録）:

| cid | N | plb | K_sync | → sync_order | R_density | label_density | link_density | mean_label_ncore |
|---|---|---|---|---|---|---|---|---|
| 0 | 331 | 0.0066 | 0.265 | 0.0697 | 0.0197 | 0.0463 | 0.5509 | 3.587 |
| 2 | 326 | 0.0076 | 0.300 | 0.1380 | 0.0453 | 0.0481 | 0.6687 | 3.490 |
| 19 | 354 | 0.0067 | 0.050 | 0.0404 | 0.0271 | 0.0414 | 0.5499 | 3.280 |
| 26 | 336 | 0.0065 | 0.187 | 0.0651 | 0.0211 | 0.0347 | 0.5605 | 3.158 |
| 41 | 342 | 0.0080 | 0.090 | 0.0618 | 0.0444 | 0.0653 | 0.7739 | 3.154 |
| 42 | 326 | 0.0079 | 0.297 | 0.1850 | 0.0497 | 0.0777 | 0.7321 | 3.781 |
| 86 | 330 | 0.0070 | 0.296 | 0.1446 | 0.0283 | 0.0515 | 0.6444 | 3.316 |
| 107 | 337 | 0.0075 | 0.168 | 0.0901 | 0.0168 | 0.0544 | 0.6281 | 3.080 |
| 128 | 339 | 0.0071 | 0.157 | 0.0607 | 0.0403 | 0.0541 | 0.6618 | 2.920 |
| 167 | 338 | 0.0061 | 0.222 | 0.0829 | 0.0348 | 0.0355 | 0.5927 | 2.885 |
| 178 | 334 | 0.0072 | 0.234 | 0.0840 | 0.0279 | 0.0449 | 0.6577 | 3.438 |
| 207 | 351 | 0.0060 | 0.107 | 0.0774 | 0.0280 | 0.0266 | 0.5451 | 2.722 |
| 228 | 335 | 0.0065 | 0.250 | 0.0823 | 0.0188 | 0.0408 | 0.5791 | 3.388 |
| 237 | 350 | 0.0068 | 0.089 | 0.0851 | 0.0372 | 0.0400 | 0.6010 | 3.227 |
| 239 | 333 | 0.0080 | 0.206 | 0.0462 | 0.0099 | 0.0541 | 0.7277 | 3.604 |
| 240 | 350 | 0.0061 | 0.106 | 0.0822 | 0.0267 | 0.0314 | 0.5571 | 3.219 |
| 273 | 336 | 0.0068 | 0.239 | 0.0739 | 0.0227 | 0.0476 | 0.6677 | 3.202 |

**入力 knob × 出力署名 の素の相関（記述のみ・解釈しない, real 17点）**:
- corr(**K_sync←r_core**, sync_order) = **+0.635**
- corr(**plb←S_avg**, link_density) = **+0.896** ／ corr(plb, label_density) = **+0.873**
- corr(**N←B_Gen×10**, label_density) = **−0.548**
- corr(**初期θ←phase_sig**, sync_order) = **+0.079**
- corr(K_sync, R_density) = +0.015

> これは入力 knob と出力署名の**素の相関の並置**。「だからこの物理条件がこの性質を生む」とは書かない（判定・解釈は Taka）。位相 readout 注: Familiarity は位相で決まる（Taka）ので sync_order を位相手がかりとして取得。重い cog 全回しはしていない。

## 4. 4 対照の素の分布（3 seed 平均→17 CID 集計, 判定なし）
| 署名 | real (mean/std) | shuffle | random | canon |
|---|---|---|---|---|
| alive_ratio | 1.000/0.000 | 1.000/0.000 | 1.000/0.000 | 1.000/0.000 |
| sync_order | 0.086/**0.037** | 0.107/0.054 | 0.100/0.036 | 0.071/**0.028** |
| R_density | 0.029/0.011 | 0.037/0.017 | 0.037/0.015 | 0.035/0.013 |
| link_density | 0.629/0.071 | 0.630/0.071 | 0.657/0.055 | 0.633/**0.035** |
| label_density | 0.047/0.013 | 0.050/0.013 | 0.048/0.010 | 0.047/**0.006** |
| n_labels | 15.7/4.0 | 16.8/4.3 | 16.4/3.6 | 15.8/**2.0** |
| mean_label_ncore | 3.26/0.27 | 3.37/0.27 | 3.40/0.29 | 3.34/0.28 |

> 素の記述: 平均は4対照とも近い帯。std（17 CID で散る幅）は **canon（CID 変化なし）が各署名で最小**（label_density 0.006 / n_labels 2.0 / link_density 0.035 / sync_order 0.028）、real/shuffle/random は大きい。**real が shuffle/random と区別つくか（CID 値が効いているか）は対照を並置しただけで、勝ち負け判定は置かない（Taka 判断）。**

## 5. 本体 main との差（明記）
本 child = 現行 v918/v105 main 構成の縮小・param 変調だが:
- **stress OFF**（main も OFF＝同じ）。
- **semantic_pressure OFF**（**main は ON＝ここが差**）。初手は CID param の効果を clean に見るため semantic_pressure を切った（θ 背景ノイズ除去）。本体に揃えて位相ノイズ込みで見るなら `pressure_prob` を戻す。

## やらないこと / 一方向
- やらないこと: 親物理への書き戻し（readout 留め）、写像を「正しい一つ」に確定（サンプラー）、real が勝ち/負けの判定、crown、5 knob 以外を CID で振る・n_core 跨ぎ（次段）、cog 全回し（位相で代理）。
- 一方向: 読＝frozen（per_subject_seed0 / 現行 engine 構成 / v19g_canon）。書＝`unified/v1301/` のみ。child engine は in-memory。親 physics/inject/ledger/state 非書込。

---

## 一文サマリ
CID-conditioned child-world 本番（Code A、2026-06-20、確定設計の実走・記録のみ判定なし）── n_core=5 の17 CID×4対照(real/shuffle/random/canon)×3 seed=204 child を 500 step、4 knob(N=B_Gen×10/plb←S_avg/K_sync←r_core/初期θ←phase_sig)、stress OFF+semantic_pressure OFF(現行 main 縮小・main との差は後者)。検証で 4 knob 立ち・OFF 確認・§5 K_sync 効く(0.05→sync0.007/0.50→0.097)・コスト642s。全 child alive_ratio=1.0(崩壊なし)。**入力→出力 素の相関(記述のみ): corr(K_sync,sync_order)=+0.635 / corr(plb,link_density)=+0.896 / corr(plb,label_density)=+0.873 / corr(N,label_density)=−0.548 / corr(初期θ,sync_order)=+0.079**。4対照: 平均は近い帯、std は canon 最小・real/shuffle/random 大。判定(real が CID 由来で区別つくか/物理条件→性質の解釈)は書かず Taka。出力 = signatures.parquet + summary.json。
