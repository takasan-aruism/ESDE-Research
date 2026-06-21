# CID 値 ↔ 物理層 param 対応表 — 配線可能性調査（案出し・実装ゼロ）

## 自己規律宣言（Code A）
① 過去引用済（実コード/実走/実データ突合）:
- `feasibility_check_report.md`（GO+合意3点。**K_sync を「保留」としたが本調査で訂正＝設定可**）、`cid_internal_mini_esde_design.md`、`docs/ESDE_技術仕様書.md §3`（物理 param）。
- 実コード: `esde_v43_engine.py:446 __init__(seed,N,plb,rate)` / `:461 PhysicsParams(beta,decay,K_sync,…)` / `genesis_physics.py:30 @dataclass PhysicsParams`(frozen でない, step 時 `self.params.X` 読み) / `v19g_canon.py:73 BIAS/BETA/NODE_DECAY`(モジュール定数) / `build_substrate(N)`(grid は N 従属) / `genesis_state.py:33 theta`,`:51 F` / `per_subject_seed0.csv`(130 カラム) / v1114 step2a(`cog.familiarity` を live 読み, 7353 partners)。
- 規律: #30（写像の正しさを結論の土台にしない＝サンプラー）、#33（複数案）、#26（物理書込口は torque/inject/環境要因のみ・親非書込）、交絡注意（同じ CID 値を2 param に使わない）。

② Taka 逐語（仕様 §0・要所）:
- 「見たいのは『物理条件 → CID 性質』の傾向（例: Familiarity を高める物理条件は何か）。CID の多様な値で物理層を一気に色々変えてサンプリングし傾向を探る。写像『CID 値→物理 param』はサンプラーで、最終的に見たいのは逆向き『物理条件→生まれた CID 性質』。だから写像の正しさは問わない（#30）」。

③ 成否判定は Taka。④ 集約語なし。crown 禁止。

## 観察対象注釈ブロック
各 child-world は親 CID ごとの独立子系。観察＝各 child の同系内動学＋集計。param 導出＝親 CID 形態の構造特徴を read-only で読むのみ（実現値コピーでない＝死線回避）。書込は child engine（in-memory）と `unified/v1301/` のみ。親 physics/inject/ledger/state 非書込。

*作成*: 2026-06-20、Code A。*この段*: 配線可能性調査のみ・実装ゼロ。再現＝`wiring_probe.py`。

---

## A. CID 側 ── 何が取れるか・n_core=5 の 17 CID で散るか
`per_subject_seed0.csv` に **130 カラム**。数値 110 列のうち **90 列が CV>0.1 で散る**（17 CID で多様）。傾向探索に効く主な CID 値:

| 分類 | CID 値（カラム） | n5 値域 | n5 で散るか |
|---|---|---|---|
| **M_c（固有値・構造）** | phase_sig | [−2.88, 2.38] | ◎ 散る |
| | S_avg | [0.274, 0.464] | ○ 散る |
| | r_core | [0.219, 0.900] | ○ 散る |
| | n_core | 5 固定 | ✗ 母集団フィルタ |
| | **B_Gen** | [32.58, 35.37] | **✗ CV=0.025（n_core 決定で帯狭）** |
| **familiarity（readout 標的・かつ散る）** | last_familiarity_max | [30.3, 500] | ◎ 散る |
| | R_familiarity_last / delta_familiarity / current_familiarity | (各) | ◎ 散る |
| **活動量** | v11_n_pulses_eval / v10_pulse_count | [7, 497] | ○ 散る |
| | v11_n_captured / v11_capture_rate / v11_mean_delta | | ○ 散る |
| **Q/C** | v14_q0(Q0) / v18_cognitive_gain_final(=消費 Q=C) | | ○ 散る |
| **自己/他者読み** | v915_divergence_norm_final / v917_unique_contacts / avg_visible_ratio | | ○ 散る |
| **v18** | v_unified_concentration / theta_distance | | ○ 散る |

→ **入力 knob は豊富**（90 列散る）。ただし **B_Gen と n_core は n5 で散らない**（n_core 決定）＝17 CID では物理条件を散らせない（cross-n_core でのみ効く、§C-Taka）。
**注（交絡）**: familiarity は **readout 標的**でもあるので、familiarity 系を *入力 knob* に使うと「親 familiarity が子 familiarity に echo しただけか、物理条件の効果か」分離不能。**familiarity 標的の傾向探索では、入力に非 familiarity 値（S_avg/r_core/phase_sig/pulse/Q 等）を使う**。

## B. 物理側 ── 何が per-child で変調できるか（配線・実走確認）
| 物理 param | 配線方法 | per-child 可? |
|---|---|---|
| **N（ノード数）** | `V82Engine(N=…)` constructor | ✅ |
| **plb（リンク誕生確率）** | `V82Engine(plb=…)` constructor → realizer | ✅ |
| **rate（注入/realization 率）** | `V82Engine(rate=…)` constructor | ✅ |
| **K_sync（Kuramoto 結合）** | `engine.physics.params.K_sync=…`（構築後書込） | ✅ **実走確認**（前回保留を訂正） |
| **beta（共鳴減衰抑制）/ beta_max** | `engine.physics.params.beta=…` | ✅ |
| **decay_rate_node（E 減衰）/ decay_rate_link（S 減衰）** | `engine.physics.params.decay_rate_*=…` | ✅ |
| **初期 θ 分布** | `engine.state.theta[:]=…`（子の自前 init） | ✅ |
| **F（肥沃度地形）** | `engine.state.F[:]=…` | ✅ |
| maturation_alpha / rigidity_beta | constructor | ✅ |
| **BIAS（seeding 偏り）** | モジュール定数（`v82:179`/`v43:528` で global 読み） | ❌ **per-instance 不可**（monkey-patch のみ＝sequential 限定） |
| **grid 幅** | `build_substrate(N)` で **N 従属** | ❌ **独立 knob 不可**（N に連動） |

→ **大半が per-child 変調可**（N/plb/rate/K_sync/beta/decay×2/初期θ/F/maturation/rigidity）。**通らないのは BIAS（module global）と grid 幅（N 従属）の2つだけ**。

## C. 対応表の案（複数・#33・「正しい一つ」を主張しない）
原則: 散る CID 値(A) → 変調可 param(B) を **1:1**（交絡回避）、構造同型、n5 で散る。

**案1（M_c 同型・全配線可・推奨第一）**
| CID 値 | → 物理 param | 根拠(同型) | 配線 | n5 で散る |
|---|---|---|---|---|
| S_avg | plb | 結合強度→リンク誕生 | ✅ | ○ |
| r_core | K_sync | 同期度→Kuramoto 結合 | ✅ | ○ |
| phase_sig | 初期θ分布(von Mises) | 位相署名→初期位相クラスタ | ✅ | ◎ |
| v11_n_pulses_eval | rate | 活動量→注入率 | ✅ | ○ |

**案2（共鳴・減衰系を効かせる）**
| CID 値 | → 物理 param | 根拠 | 配線 | 散る |
|---|---|---|---|---|
| r_core | beta | 同期→共鳴減衰抑制 | ✅ | ○ |
| S_avg | plb | 結合強度→リンク誕生 | ✅ | ○ |
| phase_sig | 初期θ | 位相署名→初期位相 | ✅ | ◎ |
| v11_mean_delta | decay_rate_node | 捕捉ズレ→E 減衰 | ✅ | ○ |

**案3（活動・自己読み系）**: v10_pulse_count→rate / v915_divergence_norm_final→decay_rate_link / v917_unique_contacts→F(肥沃度) / phase_sig→初期θ。配線可・散る。

> 3 案とも全 param が per-child 配線可・全入力が n5 で散る・1:1 で交絡なし。「正しい一つ」を選ばず、real 対照が写像を変えてもクラスタが保たれるか（CID が前提として効いているか）を複数案で見る（#33 の写像版）。

**§C-Taka 案評価（B_Gen×10=N, B_Gen/2=grid 幅）**
- **B_Gen×10 = N**: 配線 ✅（N は constructor）。だが **B_Gen は n5 で [32.6,35.4]・CV=0.025**（実測）→ N=[326,354]＝**17 child で横並び（散らない）**。cross-n_core でのみ有効（n=2: B_Gen≈12→N≈120 / n=5: ≈35→N≈350、約3×。Taka の「n_core を跨げば桁で変わる」は方向として正、実際は約3×）。
- **B_Gen/2 = grid 幅**: ❌ **不成立**。grid は `build_substrate(N)` で **N 従属**＝独立 knob でない。かつ B_Gen を N と grid の両方に使えば**交絡**（同一 CID 値→2 param 禁止）。
- → **試験（n_core=5 固定）では B_Gen/n_core は物理条件を散らせない**。これらを効かせたいなら **母集団を n_core 跨ぎ**にする必要（その場合 N が約3×振れる）。

## readout ── 子世界の CID 性質（特に familiarity）が取れるか
最終目的「物理条件→生まれた CID 性質」のため、子の **born-CID 性質**が読めるかが鍵。
- **物理署名（survival / final_density / sync_order / label の n_core 分布）**: ✅ **安価・確認済**（`feasibility_smoke.py` で直接取得、cog 不要）。
- **CID 性質（familiarity / Q / C / 寿命 / n_core 分布）**: ⚠️ **cog/SubjectLayer を子で回す必要**。
  - 配線は原理的に可（precedent: v1114 step2a が `cog.familiarity[cid]` を live 読み、7353 partners）。
  - **だが既存 run() entrypoint は N=5000 hardcode（N 引数なし）** → N=100 で cog を回すには **cog ループの抽出**が要る（step2 提案の重い部分）。
  - **かつ N=100/500step では cid・E3 接触が少なく familiarity が疎**になる懸念（feasibility で 6〜21 ラベル/500step）。
  - → **familiarity readout は物理署名より重く・小N で疎＝未確定**。物理 proxy（label 間の node 共有＝接触密度）で近似する道はあるが、真の familiarity は cog 要。

## できないこと（正直に・配線上の限界）
1. **BIAS** の per-child 変調（module global、monkey-patch=sequential 限定）。
2. **grid 幅**の独立変調（N 従属）。
3. **B_Gen / n_core** で物理条件を散らす（n_core=5 固定では横並び、cross-n_core 限定）。
4. **familiarity readout** を物理署名と同じ手軽さで取る（cog 抽出が要る＋小N で疎、要 cog smoke で先に確認）。

## やらないこと / 一方向保証
- やらないこと: 写像を「正しい一つ」に確定、親物理への書き戻し、stress 投入、机上の意味づけのみで対応決定、crown、本段での実装。
- 一方向: 読＝frozen（per_subject_seed0 / 現行 engine 構成 / v19g_canon）。書＝`unified/v1301/` のみ。親 physics/inject/ledger/state 非書込。

---

## 一文サマリ
CID 値↔物理 param 対応表 配線可能性調査（Code A、2026-06-20、調査のみ・実装ゼロ、写像はサンプラー#30）── (A) per_subject 130 カラム・数値110中90が n5 で散る（familiarity 系 last_familiarity_max[30,500]・M_c phase_sig/S_avg/r_core も散る、**B_Gen は CV=0.025 で散らない=n_core 決定**）。(B) **大半が per-child 配線可**＝N/plb/rate(constructor)・**K_sync/beta/decay×2(`physics.params` 構築後書込、実走確認、前回保留を訂正)**・初期θ/F(state init)・maturation/rigidity、**通らないのは BIAS(module global) と grid 幅(N 従属) の2つ**。(C) 対応表3案（全 param 配線可・全入力 n5 で散る・1:1 交絡なし、#33 で複数）＋ Taka 案評価（B_Gen×10=N は配線可だが n5 で横並び＝cross-n_core 限定、B_Gen/2=grid は N 従属で不成立）。readout＝物理署名は安価確認済だが **familiarity は cog 抽出要+小N で疎＝未確定（要 cog smoke）**。familiarity 標的時は入力に非 familiarity 値を使う(交絡回避)。判定・実装は Taka。
