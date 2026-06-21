# v13 child-world step-0 seed=3 smoke 結果（記録のみ・判定なし・承認待ち）

## 自己規律宣言（Code A）
**① 過去引用**: step-0 指示書（Web Claude）/ §8 実装可否チェック `cw_step0_feasibility_check.md`（署名は人口統計・D_parent 2通り・run長共通35k・V1/V2 は非Mc）/ 4 knob 教訓（real≈shuffle は mean/std が pairing 盲目）/ #33（同情報を2 param に当てない）/ §16（baseline 自己成就・集団平均の罠・smoke 後停止）/ #30（写像=サンプラー）。
**② Taka 逐語**: 「step 0（CID 値が子に情報を渡せているか）だけ固める」「6−7 に広げる…追加候補の妥当性も検証」「ノードごと…混ぜてよくない」。
**③ 判定は Taka**（success/fail 置かず観察事実のみ）。
**④ 集約語禁止・crown 禁止。**

## 観察対象注釈ブロック
同系内（child=親 seed0 CID の縮小版、異系対応でない）。読=frozen（per_subject_seed0・v19g_canon・仕様書）。書=`unified/v13_childworld/` のみ。child engine は in-memory、親 physics/inject/ledger/state 非書込。**本 run は seed=3 smoke（承認後 seed 拡張）**。

*実行*: 2026-06-21、`cw_step0.py`、264 child（real 246 + canon 18）、run_len=35000、Pool24、**1609s**。出力 = `cw_step0_signatures.parquet` / `cw_step0_summary.json`。

---

## 1. 設計（確定版・§8 点検後）
- **問い**: stratum 内で real child の署名距離が親 CID 距離に対応するか（= CID 情報が child に伝わるか）。Mantel + 置換 null（K=999、片側）。shuffle は child 再 run せず Mantel 置換で表現。
- **6 チャネル**: N←B_gen / plb←S_avg(s_plb=0.3 拡幅) / K_sync←r_core / 初期θ←phase_sig / decay_node←V1 / decay_link←V2。beta=1.0 frozen。
- **V1/V2（非 M_c・完全populated・M_c から独立）**: V1=`v11_capture_rate`（M_c |r|≤0.30）、V2=`v11_n_captured`（≤0.28、V1 と 0.26=別物）。※当初案 v11_mean_delta は S_avg と r=0.73=M_c 二重注入、delta_familiarity は n2 で 25/54 NaN ゆえ精査で差替（#33／データ欠損回避）。decay_node/link への割当は構造同型弱く暫定（Taka 可変）。
- **署名（創発人口統計・入力の直写し禁止）**: n_labels / mean_size / std_size / share_gini / mean_age / lifecycle_events。phase_sig・sync_order は不使用。
- **D_parent 2通り**: Mc(S_avg, r_core, phase_sig〔cos/sin〕) と 6入力(＋B_gen, V1, V2)。n_core は層内一定ゆえ除外。
- 母集団 formed 82（n2:54 / n4:11 / n5:17）。n_core 別・合算なし。

## 2. 主結果（Mantel、観察事実）
| stratum | Mantel(Mc) r / p | Mantel(6入力) r / p |
|---|---|---|
| **n2 (54 CID)** | 0.424 / **0.001** | 0.548 / **0.001** |
| **n4 (11 CID)** | 0.471 / **0.003** | 0.604 / **0.001** |
| n5 (17 CID) | 0.076 / 0.251 | 0.099 / 0.212 |

- n2/n4 で real の署名距離が親 CID 距離に対応（置換 null を超える）。n5 は超えない。
- **6入力 > Mc が一貫**（n2 0.548>0.424、n4 0.604>0.471）= 非 M_c 軸（capture_rate, n_captured）を足すと対応が増える（Taka「追加候補の妥当性」への観察）。

## 3. 結果の検証（鵜呑みにせず確かめた・「強引な導出」回避）
**(a) manipulation 連鎖でないか** — 署名 n_labels は plb←S_avg の下流（長 run で plb↔label 数 r≈0.9）。これが Mantel を駆動しているだけかを確認:
| stratum | 全6dim | n_labels 除く | 創発のみ(size/gini/age系) |
|---|---|---|---|
| n2 | r=0.548 p=0.001 | r=0.530 p=0.001 | **r=0.453 p=0.001** |
| n4 | r=0.604 p=0.001 | r=0.570 p=0.001 | **r=0.543 p=0.001** |
| n5 | r=0.099 p=0.191 | r=0.071 p=0.273 | r=0.049 p=0.320 |
→ **n2/n4 の対応は n_labels を外しても、入力の写しでない創発次元（サイズ多様性・share 集中・年齢）だけでも生存**。＝S_avg→plb→label 数 の manipulation 連鎖だけで説明されない。署名各次元の入力結合は s_avg/V1/V2 等に分散（単一入力支配でない）。

**(b) signal/noise（公平版に訂正）** — 当初の「3seed平均 real vs 1seed canon」は footing 不一致で雑音過大。同一標準化での within-CID(seed 雑音) vs between-CID:
| stratum | between(cid) | within(seed) | signal/noise |
|---|---|---|---|
| n2 | 2.36 | 2.60 | **0.91** |
| n4 | 2.85 | 2.02 | 1.41 |
| n5 | 2.65 | 2.30 | 1.15 |
→ **n2 は seed=3 で between≈within（境界）**。Mantel は seed 平均署名の*構造*対応ゆえ有意でも、絶対分離は seed 雑音と同程度。**seed 拡張で改善見込み**（§4 見積で sync/link 系は ~10-14 seed 要）。n4/n5 は between>within。

## 4. caveat（観察として記録・判定しない）
1. **n5 非有意**は「伝達なし」と断定しない。候補要因（未確定）: n5 は M_c が層内で共線（既調査 B_gen↔r_core=−0.94）＝親が互いに似て D_parent の構造が薄い／17 CID と少数／N≈340 と大きく 35k で平衡寄りで署名が収束。**4 knob テスト（n5）で K_sync→sync_order 等が効いたのは直接 manipulation 署名**で、本 step-0 は創発署名ゆえ別物（manipulation は効くが創発人口は親 identity に組織化されない、という像）。
2. **n2 は seed=3 で signal≈noise** ＝ smoke の Mantel p は予備的。seed 拡張前に「効いた」と確定しない。
3. これは「real が shuffle(=置換 null)より親に対応するか」の観察であって、「どの物理設定がどの CID 系を作るか」のマップ（出口2）ではない。

## 5. 次段（Taka 承認待ち・勝手に進めない）
- **seed=12 へ拡張**（§8.4 見積、n2 の signal/noise を seed 雑音以上へ）。スクリプトは `CW_SEEDS=12` で同一。signal/noise は公平版に修正済（次 run から反映）。
- 拡張後も n5 が非有意なら、n5 の D_parent 共線（母集団側）を観察方法として疑う（#29「観察方法を疑う」）。
- マップ作成（出口2）・Atom 接続・選定確定・beta/Z 投入はしない。

## 6. コード懐疑再点検（2026-06-21、Taka 指示）
回す前の精査に加え、結果のコードを矛盾・隠れバグ・意図しない挙動・強引な意味づけの観点で再点検。机上12点 + 実機3点を確認、**いずれも問題なし**:
| 点検 | 結果 |
|---|---|
| (A) compression で `macro_nodes` に逃げた label が `n_labels`(active のみ) から漏れ署名を歪めるか | **漏れ0%**（n2/n5 典型・n5 plb高=80 labels でも macro_nodes=0、compression 非発火）。n_labels は全安定構造を捕捉 |
| (B) canon の6 param が層内一定か（純 seed 雑音床の前提）| **全層で param 一意数=1**（theta_mu=nan）。canon は seed のみ異なる=正しい雑音床 |
| (C) Mantel null が正しく中心0か | **null 平均≈0**（+0.002/−0.001/+0.003）。n2 r=0.55≫null97.5%=0.18 p=0.001、n5 r=0.10 は null 内 p=0.20=真に null。machinery 健全 |
| seed 衝突 | real `cid*100+s` と canon `900000+nc*100+s` は衝突なし。各 child 独立・再現可 |
| D_parent↔D_child のリーク | 親値は署名に直接コピーされない（phase_sig 除外・署名は創発量）。唯一の経路は6 param チャネル=因果 |
| 6入力>Mc は次元追加の機械的水増しか | No（雑音次元なら r は下がる。上がった=追加軸が aligned signal） |
| 低分散署名次元（mean_size CV0.03 等）の z 標準化 | 雑音に等重み=Mantel を**保守側**にするのみ（有意性を水増ししない）。創発のみ部分集合でも n2/n4 生存ゆえ無害 |
| 仕様曖昧の強引な意味づけ | 署名を M_c→創発人口統計に変えた点は §8.2 で根拠明記・Taka 可変と明示。n5 候補要因は「未確定」と明記。6入力>Mc は r 値の直接観察。過剰意味づけなし |

→ **修正を要するバグなし**。signal/noise の footing 不一致のみ前 commit で公平版へ修正済（データ再取得は不要、Mantel は内部一貫ゆえ smoke 結果は有効）。

## やらないこと / 一方向
- やらない: seed 拡張を承認前に実行、マップ作成、success/fail 判定、crown。
- 一方向: 読=frozen。書=`unified/v13_childworld/` のみ。child in-memory、親非書込。

## 一文サマリ
step-0 seed=3 smoke（Code A、2026-06-21、判定なし・承認待ち）── 264 child・1609s。**n2/n4 で real 署名距離が親 CID 距離に対応（Mantel p≤0.003）・6入力>Mc 一貫（非 M_c 軸が対応を増やす）・n5 非有意**。検証: 対応は **n_labels(plb連鎖)を外し創発次元のみでも n2/n4 生存（r=0.45/0.54 p=0.001）＝manipulation 連鎖でない**。ただし **signal/noise 公平版で n2=0.91（seed=3 で境界）** ＝ Mantel は予備的、seed 拡張で要確認。n5 非有意は母集団 M_c 共線（B_gen↔r_core−0.94）等を候補に観察方法から疑う（断定しない）。次は seed=12（Taka 承認後）。
