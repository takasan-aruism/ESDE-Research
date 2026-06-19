# CID-conditioned child-world — 実装可能性チェック報告（調査のみ・実装はチェック後）

## 自己規律宣言（Code A）
① 過去引用済（実コード/実データ突合）:
- `cid_internal_mini_esde_design.md`（前ターン設計討議）→ 本仕様（Web Claude 設計、3者一致）。
- V82Engine（`autonomy/v82/esde_v82_engine.py:110` `__init__(seed,N,plb,rate,encap_params,…,maturation_alpha,rigidity_beta)`）、VirtualLayerV9（`primitive/v910`）、`v19g_canon`（K_sync/BIAS はモジュール定数 :40 import）。
- CID 形態 = `per_subject_seed0.csv` の `v11_m_c_s_avg/r_core/phase_sig/n_core`（M_c）。意味層 = `developmental/v106/v106_pulse_trajectory.py:302 build_pulse_cid_vector`。
- 死線（#20 CID を外から置く=核decouple / #26 物理書込は torque/inject/環境要因のみ / 番号コピー欠陥）、#33（集計単位で像が変わる）、注意センター v1114（観察のみ・書き戻し保留）。

② Taka/Web Claude 逐語（仕様原文・要所）:
- 「親 ESDE の n_core=5 各 CID の形態を物理法則 param（v19g_canon）の変異に写し、同一 Frozen 条件・異なる物理演算法則の child-world を 500 step 回す。生成された多様性が安定な署名でクラスタするかを 4 対照で見る」。
- 「『CID 内部ミニESDE』と呼ばない…『CID-conditioned child-world』。CID の中に ESDE があるのでなく、親 CID 形態を読んで別の小型 ESDE の物理 param を条件づけ、子系を独立に回して署名を見る」。
- 「まず書き戻さない…CID→child-world→signature→CID feature(readout) まで」。
- 「§10 の5点を調査し、実装可能性・コスト・既存との矛盾・落ちうる所・言い換えでないかを報告。問題なければ実装に進む」。

③ 成否判定は Taka。④ 集約語なし。crown 禁止。

## 観察対象注釈ブロック
- 同系/異系: 各 child-world は親 CID ごとの**独立子系**。観察＝各 child の*同系内*動学（生存/構造）＋*集計*署名。child 同士・親との*座標/node ID 対応*はしない（番号コピー欠陥の再帰回避）。
- param 導出＝親 CID 形態の**構造特徴を read-only で読み param に写すのみ**（実現値コピーでない＝死線回避、前ターン §3 と整合）。書込は child engine（in-memory）と新規 `unified/v13_childworld/` のみ。親物理 非書込。

*作成*: 2026-06-19、Code A。*この段*: **調査＋実装可能性チェックのみ・実装ゼロ**。再現 smoke = `feasibility_smoke.py`。

---

## 1. 結論 ── 実装可能（GO）。ただし合意を要する精緻化 3 点（§7）
§10 の5領域すべて実コード/実走で確認。**ブロッカーなし。** child-world は standalone で回り・生存し・**plb 変調で構造的多様性を出す**（make-or-break に有利な初期シグナル）。母集団・意味層・param 注入口に**設計どおりでない箇所が3つ**あり、そこだけ合意したい。

## 2. §10.1 実装可能性・コスト（実走）── GO・軽い
`V82Engine(N=100)+VirtualLayerV9+run_injection(300)+500step` を実走:

| 条件 | 時間 | alive_n | alive_l | labels(=child の CID) | label の n_core |
|---|---|---|---|---|---|
| canon (plb 0.007) | 5.82s | 100 | 75 | **12** | 2×6,4,5×4,7 |
| plb+20% (0.0084) | 6.15s | 100 | 80 | **21** | 2 主体 |
| plb−20% (0.0056) | 5.75s | 100 | 70 | **6** | 2,2,2,4,5,5 |

- メモリ ~2MB/child（無視可）。**コスト概算: 17CID×3seed×4対照 = 204 child × ~5.8s ≈ 20 分**（物理+virtual。意味層は別途 §5）。

## 3. §10.2 写像の実装可能性 ── GO（要修正2点）
- **CID 形態は取れる**: `v11_m_c_s_avg/r_core/phase_sig` を per_subject から read-only。string 格納なので `to_numeric` 必要。値は**多様**（s_avg [0.274,0.464] / r_core [0.219,0.900] / phase_sig [−2.877,2.376]）＝サンプラーとして良い。
- **【要合意①】母集団は 21 でなく 17**: M_c n_core=='5' は 17 個（'unformed' 143）。source_events n_core=5 の 21 と積集合＝**17**（残り4は M_c 未形成で形態が無い）。→ **形態が取れる n_core=5 CID = 17 個**を母集団に。
- **【要合意②】param 注入口**: **plb は constructor 引数で per-child 即変調可**（実証済）。だが **K_sync / BIAS は v19g_canon のモジュール定数**で per-instance に通らない（Gemini 写像の r_core→K_sync が直撃）。初手は **plb（S_avg）+ 初期θ分布（phase_sig→von Mises を child.state.theta に init 書込＝子の自前 init で死線でない）+ maturation_alpha / rigidity_beta（constructor）** の4–5 knob で回し、**K_sync/BIAS は後段に保留**（canon への追加配管が要る）。

## 4. §10.3 既存との矛盾 ── なし
- #20（CID を外から置く）と矛盾せず: **CID を置かず param で条件づけ子に発芽させる**。
- #26（物理書込）と矛盾せず: 書込は**別インスタンスの child engine のみ**。親 state/physics/inject/ledger 非書込（実装では grep 物理書込ゼロを保証可）。
- 新しい物理法則を発明していない: child は **autonomy/v82 の既存ルール**を param 変調して回すだけ。
- v1114 と整合: 観察のみ・親への書き戻しなし（センターの現 read-only 段と同じゾーン）。

## 5. §10.4 落ちうる所
- **habitable band ── GO**: ±20% plb で**生存維持**（alive_n=100、崩壊なし）。即死だらけにならない。
- **ラベル(CID)形成 ── GO**: 500step/N=100 で **6〜21 ラベル**形成。しかも **plb で数・n_core 構成が変わる**（多様性が構造的＝ノイズでなく param 依存の初期証拠）。
- **【要合意③】意味層(48次元署名) ── CAUTION・未解決**: `build_pulse_cid_vector` は per-CID の**trajectory 特徴**（cum_pulse/R_familiarity 等）を要求。本 smoke は物理+virtual(ラベル)までで、**認知層パイプライン（SubjectLayer+capture+v106 集約）は未走**。6〜21 CID/500step だと 48 次元 profile が疎/ノイズになる懸念。→ **初手 smoke は物理署名のみ（lifespan_rate/final_density/sync_order）で 4 対照クラスタ判定を行い、物理署名が束ねに乗ると確認できてから意味層を 2nd pass で足す**ことを推奨（最大の未知を切り離して de-risk）。
- 3-seed ── GO（決定論的・安価、符号反転対策に十分）。

## 6. §10.5 Feedback/pickup 言い換えチェック ── 言い換えでない
- Feedback Loop（`virtual_layer_v9` turnover EMA→torque 変調）は**親が自分の集計を自分の存在層に戻す**機構。本案は**親 CID 形態を読み別の独立子系を param 条件づけして回し署名を束ねる** ── 構造が別。pickup（ghost TTL）も無関係。生きている新規性「CID 形態→物理法則 param→独立子系→署名束ね」を外していない。

## 7. 合意を要する 3 点（Code A 推奨・Taka/3-AI 確認）
1. **母集団 21 → 17**（M_c 形態が取れる n_core=5 CID）。
2. **初手の param knob = plb + 初期θ + maturation_alpha + rigidity_beta**（per-instance 確実）。**K_sync/BIAS は後段**（canon 配管が要る）。
3. **初手 smoke = 物理署名のみでクラスタ判定**（survival/density/sync_order の3物理次元、4対照）。**意味層(48次元)は物理クラスタ確認後の 2nd pass**。理由＝意味層が最大の未知（認知パイプライン要・短run/小N で疎の懸念）で、物理署名だけで make-or-break（束ねるかノイズか）は先に測れる。

## 8. やらないこと / 一方向保証
- やらないこと: 親物理への書き戻し（readout 留め）、「child は CID の内面/夢」読み、単一写像/単一束ね方の正解化、crown、対照なしの「多様に回った」結論、本段での実装。
- 一方向: 読＝frozen（per_subject_seed0 / source_events_seed0 / atom_profiles_cache / build_pulse_cid_vector）。書＝`unified/v13_childworld/` のみ。親 physics/inject/state/ledger 非書込。

---

## 一文サマリ
CID-conditioned child-world 実装可能性チェック（Code A、2026-06-19、調査のみ・実装ゼロ）── 実走で **GO（ブロッカーなし）**: `V82Engine(N=100)+VirtualLayerV9` standalone 5.8s/child・生存維持・**plb 変調で 6〜21 ラベルと構造が変わる**（束ね有利な初期シグナル）、コスト 204 child(17×3×4)×5.8s≈20 分。既存矛盾なし（CID を置かず param 条件づけ＝#20回避、child engine のみ書込＝#26回避、新法則なし、観察のみ）。Feedback/pickup の言い換えでない。**合意を要する3点**＝①母集団 21→17（M_c 形態が取れるもの）②初手 knob は plb/初期θ/maturation_alpha/rigidity_beta（K_sync/BIAS は canon 定数で後段）③初手 smoke は物理署名のみでクラスタ判定し意味層48次元は 2nd pass（最大未知を de-risk）。判定・実装着手は Taka 合意後。
