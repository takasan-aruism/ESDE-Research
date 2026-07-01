# v1304a 実装可否チェック — child-ESDE existence check（実コード突合）

*作成*: 2026-07-01、Code A。**実装前の feasibility ゲート（実コード突合・判定なし #12）。child 実験 run は走らせていない・最小 engine smoke のみ。read-only・物理非書込。合意ゲート前で停止。**
*対象設計*: v1304a 設計（Web Claude・2026-07-01・child-ESDE projection existence check）。
*成果物*: 本報告のみ（実装未着手・Taka/Web Claude の写像判断待ち）。

---

## 0. 結論（先に）
- **強い再利用性**：v1304a が要求する paradigm は **既存 `unified/v1301/cw_run.py`（child-world）にほぼ揃っている**。engine は現環境で in-memory 起動・自走を smoke で確認（50 node×100 step ≈ 0.19s）。
- **実装ブロッカーなし**。ただし **1 点だけ設計判断が要る**＝**親 attention profile（eye 別・cid 上 p_select 分布）→ 子 knob（N/plb/k_sync/theta_mu）の写像形**。これが nulls の定義も決めるため、実装前に Taka/Web Claude 合意が要る（§3）。
- feasibility 制約 1 件：**knob 源列（v11 birth 物理）は 45/228 cid でしか非欠損**（bgen と同じ疎性）＝写像は 45 cid 支持の attention mass に限られる（§3.3）。

## 1. §8 各項目の実機回答
| # | 項目 | 判定 | 根拠（実コード/smoke） |
|---|---|---|---|
| 1 | 子 engine を read-only 再利用できるか | **可** | `cw_run.py build_child(N,plb,k_sync,theta_mu,seed)` が V82Engine を in-memory 構築。smoke で import 0.2s・child 走行 0.19s・`run_injection()` 動作確認 |
| 2 | 親 profile → 子 seed の一回写し | **可（写像形は未定・§3）** | build_child の 4 knob が seed レバー。smoke で親偏り child（theta_mu=1.2/k_sync=0.25）が canon と別署名（sync 0.57/labels 6 vs 0.12/2）＝knob で構造差が出る。runtime 連続注入なし＝v1302 生存 paradigm（persistent-param）と一致 |
| 3 | 構造 readout が取れるか | **可** | `signature(eng)` が alive_ratio / link_density / R_density / sync_order / n_labels / label_density / mean_label_ncore を返す（§3.1 の構造量に対応）。**Atom は入れない**（設計通り） |
| 3' | 時間区分（t0/short/mid/late） | **可（小改修）** | cw_run は終端 1 点署名のみ。smoke で **step_window ごとに署名取得**を実証済＝window 単位で記録すれば t 区分時系列は構造変更小 |
| 4 | null 群のコスト | **可（軽い）** | cw_run 実績 = 17CID×4対照×3seed=204child×500step が数分。smoke は 50node×100step 0.19s。eye4×群5 でも seed0 のみなら数分内 |
| 5 | 既存矛盾（read-only/非書込/feedback なし） | **可** | build_child は in-memory・親 physics/ledger/state 非書込。書込は `unified/v1304/` 配下に限定可。親へ feedback なしは実装で担保 |
| 6 | smoke 後停止 | 遵守 | seed0 存在チェック→main/複数 seed へ自動前進しない |

## 2. cw_run.py → v1304a の再利用マップ
| v1304a が要る物 | cw_run.py の既存物 | 差分 |
|---|---|---|
| 子 engine（in-memory 自走） | `build_child` + V82Engine | そのまま |
| 対照 canon / shuffle / uniform | `canon` / `shuffle` / `random` 対照 | そのまま（命名対応） |
| other-parent null | （無し） | 別 seed 親の knob を追加（比較基準・F 型でない） |
| parent-seed child | `real`（per-CID 物理 knob） | **attention profile 由来 knob に置換（§3 の写像）** |
| 構造署名 | `signature()` 7 量 | そのまま（+ event_class 系は label で近似） |
| t 区分 | 終端 1 点 | window 毎記録に小改修 |
| 循環回避 #CW7 | — | 本体を t_mid 以降にする（実装で担保） |

## 3. 唯一の設計判断（実装前に Taka/Web Claude 合意が要る）
**親 attention profile（eye 別・cid 上の p_select 分布）→ 子 knob（N/plb/k_sync/theta_mu）の写像形が未定。** cw_run は knob を per_subject 物理列（v11_b_gen/s_avg/r_core/phase_sig）から **per-CID** で作るが、v1304a の親は cid 上の**注意分布**ゆえ写像が要る。実装可能な候補（Code A が確認・採否は委ねる）：

- **候補 A（attention-weighted aggregate・eye ごと 1 child）**：eye E の p_select を重みに、attended cid 群の birth 物理を集約して 1 組の knob（N=Σp·B_gen×10 / theta_mu=p 重み phase_sig 循環平均 / plb←p 重み s_avg / k_sync←p 重み r_core）。単純だが分布を潰す。
- **候補 B（attention-weighted ensemble・cw_run 型を継ぐ）**：cw_run 通り per-CID child を作り、**ensemble を p_select[E,cid] で重み付け/サンプル**して canon（一様重み）と署名分布を比較。分布を保持・#11 とも整合（eye 別 child）。**推奨**（cw_run 最小改修・attention は「どの cid の子を重く見るか」）。
- **候補 C（初期θ biasing・§2.2 第一候補）**：child 初期 θ 分布を attention-weighted phase_sig で偏らせる。ただし phase_sig も疎（§3.3）。

**null の対応**：shuffle-parent = p_select を cid 間 shuffle（量保持・対応破壊）／other-parent = 別 seed の attention profile／uniform = p_select 一様。→ 写像を決めれば null も自動的に決まる。

### 3.3 feasibility 制約（写像に直結）
- knob 源列（v11_b_gen/s_avg/r_core/phase_sig）は **45/228 cid でしか非欠損**（bgen と同じ疎性）。⇒ birth 物理由来の knob 写像（A/B/C いずれ）は **45 cid 支持の attention mass** に限られる。attention が 45 cid 外に置く質量の扱い（除外して再正規化 / 別の denser 源）を写像決定時に決める要あり。
- 源は **v105 main_v2 per_subject**（v1303 の cid 源と一致）を使う（cw_run は v918 を使用・v1304a は v1303 整合で v105 に揃える）。

## 4. 交絡・規律の実機確認
- **空 start 交絡なし**：build_child は `run_injection()` を呼ぶ（cw_run.py:55・smoke で確認）＝v1302 (B) 移植の injection skip 空 start 交絡（[[feedback_transplant_skip_injection_confound]]）を踏まない。
- **persistent-param 一回のみ**：knob は構築時に一回写すだけ・runtime 連続注入なし＝v1302 で唯一生存した paradigm。runtime-driving（全滅）はしない。
- **E 型回避**：親 cid と子 cid を identity 一致させない。親 cid 物理は集約 knob の源としてのみ使い、子は独自 N node・構造署名で比較。
- **read-only / 物理非書込**：子 in-memory・親へ書き戻さない・feedback しない。書込は `unified/v1304/` 配下のみ。

## 5. 本チェックで走らせていないもの（実装でない）
- v1304a の実験 run（canon/null/parent × eye × t 区分の署名生成）・親→子 写像の実装・乖離/親特異/自走維持の測定は**一切していない**。
- 実施したのは engine import + 最小 child 2 本（canon 相当・親偏り相当）× 100step の smoke（署名が取れるか・時間区分が取れるか・環境で動くかの確認）のみ。ファイル非生成（本報告のみ）。

## 6. 次段（Code A は判定しない・委ねる）
実装前に Taka/Web Claude 合意が要る：**§3 の写像形（A/B/C・推奨 B）＋ 45/228 疎性の attention mass 扱い**。合意後に v1304a 実装（cw_run.py 派生・eye 別 child・canon+null3+other-parent・window 毎署名・t_mid 本体・3条件測定）→ seed0 smoke → 停止。3条件充足判定・(a)(b)(c) は Taka。

## 7. 一文サマリ
v1304a 実装可否チェック（実コード突合・engine 最小 smoke・判定なし #12）── child-ESDE existence check の paradigm は既存 `cw_run.py`（build_child 4knob + canon/shuffle/random 対照 + signature 7 構造量 + run_injection）にほぼ揃い、engine は現環境で in-memory 自走を確認（child 0.19s・親偏りで別署名・time-binned 署名可）ゆえ**実装ブロッカーなし**、ただし**唯一の設計判断＝親 attention profile（eye 別 cid 上 p_select）→ 子 knob（N/plb/k_sync/theta_mu）の写像形が未定**（候補 A aggregate / B ensemble〔cw_run 最小改修・推奨〕/ C 初期θbias・null は写像で自動決定）で、feasibility 制約＝**knob 源の v11 birth 物理は 45/228 cid でしか非欠損**（attention mass の 45 cid 外扱いを写像決定時に要決定）・源は v1303 整合で v105 per_subject に揃える、交絡確認＝run_injection 呼ぶゆえ空 start 交絡なし・persistent-param 一回のみで v1302 生存 paradigm・E 型回避（親子 identity 一致させず構造で比較）・read-only/物理非書込/feedback なし、実施は engine smoke のみで実験 run/写像実装/3条件測定は未着手、写像形＋疎性扱いを Taka/Web Claude 合意後に実装→seed0 smoke→停止、3条件充足・(a)(b)(c) は Taka 主題評価。
