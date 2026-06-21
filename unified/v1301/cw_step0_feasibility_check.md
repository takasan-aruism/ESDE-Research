# v13 child-world step-0 §8 実装可否・既存矛盾チェック（Code A → Web Claude / Taka）

## 自己規律宣言（Code A）
**① 過去引用明記**: 物理_cid_台帳（パート3 配線可能 param 全数）／4 knob テスト（CID は系を大きく変えるが real≈shuffle は mean/std が pairing 盲目だった撤回済み教訓）／技術仕様書 §3.2 op7（decay_node=clean な E 減衰・decay_link で S 過剰決定）・§3.3（β は R↔S 結合で R を駆動しない）・§574 診断（K_sync 100%・θ 84% 伝達、弱は N 源均質と plb ±15%）・§5.3（M_c 4 要素・B_gen 直入れ可否）・§16（baseline 自己成就・集団平均の罠・smoke 後停止）／#30（写像=サンプラーだが選定に合理性要）・#33（同状態変数を2 param に当てない）／6/14（child は走行中物理でなく初期条件差替ゆえ別物）／cw 実コスト（204×35k=2008s/Pool24）。
**② Taka 逐語**: 「step 0（CID 値が子に情報を渡せているか）だけ固める」／「6−7 に広げる…追加候補の妥当性も検証」／「内部の内部の方が筋がいい…傾向が分かればメイン ESDE に反映＝実質外部からの変化…180度転換」／「ノードごとにしないと平均化の罠…ノード数は構造的に違う、混ぜてよくない」。
**③ 判定は Taka**（success/fail 置かず観察事実のみ）。
**④ 集約語禁止・crown 禁止。**

## 観察対象注釈ブロック
**同系内**（child は親 seed0 CID の縮小版＝異系対応でない、§15 v1110–v1113 の轍を踏まない。過去成功 v10.2/v10.7/v9.18/v106 と同型＝同系内動学の観察）。読＝frozen（`per_subject_seed0`・技術仕様書・`v19g_canon`・cw 既存コード）。書＝本文書（`unified/v1301/`）のみ。**本チェックは read-only**（engine を1体だけ in-memory で instantiate し属性確認、step 実行・本 run はしない）。親 physics/inject/ledger/state 非書込。

---

## 結論（先出し）
- **§8.1 6 param 配線は clean・矛盾なし**。child のデフォルト decay は canon 値（node 0.005 / link 0.05）で transform の base と一致。
- **§8.2 が最大ブロッカー・かつ §4 と矛盾**: child は**存在層 label しか持たず認知層 M_c を持たない**。§4 の「formed-CID の M_c（n_core, S_avg, r_core, phase_sig）」は label から再構成するしかなく、**その再構成は入力チャネルの写しを含む**（phase_sig は初期θ←親 phase_sig の直写し）＝§4 が禁じた manipulation-check 交絡が署名側に再混入する。→ 署名定義の見直しが実装前に必要（Taka 判断）。
- **設計の不整合 2 点**を発見（§8.6）: (a) 入力 6 チャネルなのに D_parent は M_c 4 値のみ＝V1/V2 駆動分が D_child に入り相関を希釈、(b) step-0 は run 長を共通固定にすべき（寿命同期だと観測窓非対称＝監査の交絡再発）。
- V1/V2 候補（§8.4）とコスト（§8.5）は算出済。real+canon は seed=3 で実時間 ~0.4h と安価。

---

## §8.1 cw spawn の実 interface（6 param の child init 配線）
既存 `cw_run_lifespan.py` worker() の配線を確認し、6 param 全てが書込可能なことを実機で検証:

| param | 配線先 | 既存4knob | child デフォルト（実測） |
|---|---|---|---|
| N | `V82Engine(N=…)` constructor | ✅既存 | — |
| plb | `V82Engine(plb=…)` constructor | ✅既存 | — |
| K_sync | `eng.physics.params.K_sync` | ✅既存 | 0.1 |
| 初期θ | `eng.state.theta[:]` (vonmises) | ✅既存 | — |
| **decay_node** | `eng.physics.params.decay_rate_node` | 新規 | **0.005（=canon NODE_DECAY ✓、dataclass 既定 0.05 でない）** |
| **decay_link** | `eng.physics.params.decay_rate_link` | 新規 | **0.05（=spec ✓）** |

→ **矛盾なし**。decay 2 本は K_sync と同じ `physics.params` 後書きで追加でき、child は canon 値から始まるので §2 の transform base（NODE_DECAY=0.005, link_decay=0.05）と一致する。β=1.0 は frozen のまま（書かない）。

## §8.2 署名の可否（最大ブロッカー — §4 と矛盾）
child stack = `V82Engine + VirtualLayerV9` で、**認知層（v911+ の capture/pulse/M_c）は回っていない**。`VirtualLayerV9.labels` の実体は dict:
```
self.labels[lid] = {"nodes": frozenset, "phase_sig": float, "share": 0.0, "born": window, "prev_alignment": 0.0}
```
＝**存在層 label のみ。認知層 CID も M_c（n_core, S_avg, r_core, phase_sig の認知定義）も child には存在しない。**

label から取れる量と、§4「formed-CID の M_c」との対応:
| §4 が欲しい量 | child label から | 入力チャネルとの結合 |
|---|---|---|
| n_core | `len(nodes)` ✓直接 | 比較的独立（創発的な cluster サイズ）|
| phase_sig | `label["phase_sig"]`（core 平均θ）✓直接 | **初期θ←親 phase_sig の直写し＝入力コピー** ⚠ |
| r_core | label に無し／state.R から内部 link を集計して導出要 | K_sync←r_core 入力と結合 ⚠ |
| S_avg | label に無し／state.S から内部 link を集計して導出要 | plb/decay_link 入力と結合 ⚠ |

→ **§4 自身が禁じた「入力の写し（manipulation-check / §16 baseline 自己成就）」が、署名を child-M_c で作ると再混入する**。特に phase_sig は最悪（初期θに直結）。
- **label 数は十分**: long run 実測で real の n_labels ≈ 42.5（std 8.1）@35k ＝分布を作るに足る。
- **入力の写しでない創発署名の候補（推奨・Taka 判断）**: label 個体群の**人口統計** = {label 数 / label サイズ(n_core)分布の形 / share 集中度（上位寡占）/ born 回転率（誕生–消滅の turnover）}。これらは「親 CID の個性が child の育てる label 群の*人口構造*に表れるか」になり、個々の label の M_c 値（入力に遡れる）を使わずに済む。r_core/S_avg を入れるなら入力結合を明記し補助扱い。
- → **署名定義は実装前に確定が必要**（§4 の child-M_c をそのまま使うと test が manipulation-check に退化）。

## §8.2b run 長（監査の交絡を繰り返さない）
step-0 の Mantel は D_child の cid 間比較ゆえ**観測窓を揃える必要**（監査教訓「示量署名を異なる run 長で比較しない」）。→ **全 child 共通の固定 run 長（35k）を推奨**。寿命同期（ratio 1/10）は step-0 では使わない（×2 不要・コスト半減）。

## §8.4 V1 / V2 候補（非 M_c・層内 CV・頑健性。Code A 算出、選定は Taka）
全3層（n2/n4/n5）で変動する非 M_c カラム 100 個から、ゼロ過多で CV が偽膨張していない頑健な候補:

| 候補 | min層内CV | ゼロ率(n2/n4/n5) | 一意値(n2/n4/n5) | 性格・構造同型の根拠 |
|---|---|---|---|---|
| **v11_mean_delta** | 中 | 0/0/0% | 54/11/17（フル）| 捕捉ミスマッチ。台帳で decay_node 候補（ミスマッチ→減衰傾向）。**E 軸 V1 第一候補** |
| **v11_capture_rate** | 中 | 0/0/0% | 25/11/17 | 捕捉率。活動の質。S/E 下流 |
| delta_stability | 高 | 0/0/0% | 29/10/16 | v99 安定軸の変化量。intrinsic dynamics |
| delta_familiarity | 中 | 0/0/0% | 29/10/16 | 親密度変化。**S 軸 V2 候補** |
| v10_R_familiarity_last | 高 | 0/0/0% | 54/11/17 | 共鳴(親密)。フル populated だが heavy-tail |
| v11_n_captured | 中 | 0/0/0% | 22/11/16 | 捕捉数。lifecycle/露出≒n_core 相関（caveat c）|

**避けるべき（ゼロ過多で CV 偽膨張）**: ghost_duration（31–94% ゼロ）・v915_min_age_factor（50–94%）・v10_R_social_last（37–53%）。
**推奨ペア案（たたき台、決めない）**: V1（decay_node, E 軸）= `v11_mean_delta`、V2（decay_link, S 軸）= `delta_familiarity` か `v11_capture_rate`。いずれも V1≠V2・全層変動・ゼロ過多なし。**caveat（記録）**: 非 M_c は lifecycle 由来で n_core 相関を持つものが多い（§7-1 のとおり層内伝達は強2本に乗ったままになりうる）。

## §8.5 実コスト（real 82 + canon、shuffle は行列置換で無料）
共通 run 長 35k・per-child は N 比例（n2 N≈120 は安い）:
| seed | real82+canon | Pool24 実時間 |
|---|---|---|
| seed=3（smoke）| ~9.4 cpu-h | **~0.4 h** |
| seed=12 | ~37.6 cpu-h | **~1.6 h** |

→ 安価。**seed=3 smoke → 承認待ち**（§16）。寿命同期×2 をやめれば指示書見積の半分。

## §8.6 発見した設計の不整合（report vs design、要 Taka/Web Claude 判断）
1. **D_parent の次元と入力チャネルの不一致**: §2 は入力 6 チャネル（M_c4＋V1/V2）だが §5 の D_parent は **M_c 4 値のみ**。V1/V2 で振った child の差は D_child に入るのに D_parent に無い → V1/V2 駆動分が **D_parent と無相関なノイズとして corr を希釈**。
   - 対処案（決めない）: D_parent を**実際に注入した 6 入力 CID 値ベクトル**にする。または D_parent を「M_c4 のみ」と「6 入力」の**2 通り**で出し、V1/V2 が伝達を足すか引くかを見る（Taka「追加候補の妥当性も検証」に対応）。
2. **run 長**: §8.2b のとおり共通固定（35k）に（寿命同期は使わない）。
3. **署名**: §8.2 のとおり child-M_c から人口統計署名へ（manipulation-check 退化回避）。

## §8.3 child 壊れない上限（s_plb 0.3–0.4 / s_dn / s_dl）
配線は実機確認済だが、tanh 拡幅でのリンク爆発・全消滅・反応ゼロの上限は**実 step を回す smoke が要る**。§8.2/§8.6 の署名・D_parent・run 長を確定してからでないと smoke スクリプトが書けない（署名抽出コードが変わる）ため、**順序は「①署名・D_parent・run 長を Taka が確定 → ②breaking-point + seed=3 smoke → ③承認待ち → ④seed 拡張」**を提案。今は smoke を回していない（gating 遵守）。

---

## やらないこと / 一方向
- やらない: 本 run・本実装（署名定義の確定前）、マップ作成（出口2）、選定確定（Taka）、success/fail 判定、beta/Z 投入、shuffle 用 child 再 run、crown。
- 一方向: 読＝frozen。書＝`unified/v1301/` のみ。本チェックは engine 1 体を in-memory instantiate して属性確認したのみ（step 非実行）。親 physics/inject/ledger/state 非書込。

## 一文サマリ
step-0 §8 点検（Code A、2026-06-21、判定なし）── **6 param 配線は clean**（decay 2 本は physics.params 後書き可、child は canon 値 0.005/0.05 から始まり transform base と一致）。**最大ブロッカー＝署名**: child は存在層 label のみで認知層 M_c を持たず、§4 の「formed-CID M_c」を label から作ると **phase_sig（←初期θ←親 phase_sig）等が入力の直写し＝§4 が禁じた manipulation-check 交絡を署名側に再混入**する → 入力の写しでない**人口統計署名**（label 数・サイズ分布・share 集中・turnover）への変更を推奨（Taka 判断）。**設計不整合 2 件**: D_parent が M_c4 のみで入力 6 チャネルと不一致（V1/V2 が corr を希釈、D_parent を 6 入力に or 2 通り出す）／step-0 は run 長共通固定 35k に（寿命同期は使わず観測窓の交絡を回避）。V1/V2 候補は v11_mean_delta（E 軸）・delta_familiarity/v11_capture_rate（S 軸）等を CV＋頑健性で提示（選定は Taka）。コストは real+canon・seed=3 で ~0.4h と安価。**順序提案: 署名/D_parent/run 長を Taka が確定 → smoke → 承認待ち**。本 run・smoke は未実行（gating 遵守）。
