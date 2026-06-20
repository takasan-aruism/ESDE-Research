# 全検（全 CID 値→全物理 param）選定合理性の判断材料（3AI 合議の前段・調査のみ・実行ゼロ・選定確定なし）

## 自己規律宣言（Code A）
① 過去引用済: `physics_cid_ledger.md`（パート1 物理演算32 / パート2 CID値130 / パート3 配線可能 param 全数）／`cw_investigation_homogeneity_wiring.md`（§1 母集団・§2 写像配線・real≒shuffle 真因＝比較統計が pairing 盲目）／本セッション統計監査（交絡3点）／`per_subject_seed0.csv`（130カラム）／long run 実測コスト（204child×35k=2008s/Pool24）。
② Taka/合議 趣旨: 「次は (b) 全検＝全 CID 値を全物理 param に取り込み系がどう変わるか、その後 n_core 跨ぎ。**だが 10 全てを取り込む選定に合理性があるか**が譲れない（3AI 合議＋Taka で確定）」。
③ 本依頼は**調査のみ・実行ゼロ・選定を確定しない**。判定は Taka。④ 集約語なし。crown 禁止。
⑤ child-world を回さない・smoke しない・効果を測らない。read-only（相関計算・配線確認）のみ。

## 観察対象注釈ブロック
読＝frozen（per_subject_seed0 の formed 85 / n5 17・台帳パート1-3・既存 parquet・配線情報）。書＝本文書のみ。コード実行＝相関/PCA/コスト計算（read-only）まで、child-world 非実行。親 physics/inject/ledger/state 非書込。

*作成*: 2026-06-21、Code A。*再 run*: なし（既存データ + 台帳の読解）。

---

## §1 CID 値同士の相関構造（合議の土台・最重要）

per_subject_seed0 の **formed 85 subject**（n_core 2-5、n=17 だと 90 変数の相関は不安定なので formed 全体で算出）、分散のある **73 カラム**で相関行列・クラスタ・PCA。

### |r|≥0.9 の相関クラスタ（実質「同じことを測る CID 値の束」）
| 束 | 規模 | 代表メンバ | 解釈 |
|---|---|---|---|
| **活動/露出 軸** | **16** | birth_window, v10_pulse_count, v10_n_normal/major, v11_n_pulses_eval, v11_n_captured, v915_fetch_count, n_pickups_lost … | 長く生きた/活動した → pulse・捕捉・fetch が全部増える。本質 **1 軸** |
| **規模 軸** | **10** | v11_b_gen, **v11_m_c_n_core**, last_n_partners, last_attention_size, v11_mean_d_n, v915_mismatch/observed_count … | 認知構造が大きい → partner/観測/mismatch が増える。**B_gen と n_core が同束**（B_gen≒n_core の関数） |
| 終端時刻 | 3 | ghost_duration, v915_last_fetch_step, v18_finalized_at_step | いつ終わったか |
| TTL | 3 | ttl_bonus, n_pickups_won, effective_ttl | 寿命延長系 |
| phase_sig | 2 | original_phase_sig ≈ v11_m_c_phase_sig | 位相署名（同一物の別記録）|
| S_avg | 2 | v11_m_c_s_avg ≈ v11_mean_d_s | 結合強度 |
| r_core | 2 | v11_m_c_r_core ≈ v18_v_unified_concentration_birth | 同期/共鳴度 |

→ **|r|≥0.9 で 73 → 40 に圧縮**（多重クラスタ9・単独31）。

### 独立次元数の目安（PCA, formed 85・73変数）
| 基準 | 軸数 |
|---|---|
| 第1軸の説明率 | **46%**（1軸が支配的＝活動/規模が連動）|
| 上位3軸 | 60% / 上位5軸 69% / 上位10軸 81% |
| 90% 説明 | 17 軸 |
| 95% 説明 | 23 軸 |
| Kaiser（固有値>平均）| **14 軸** |

→ 素の記述: **130 カラム（分散ある 73）は実質 ~5〜14 の独立軸**（第1軸で 46%、|r|0.9 で 40、Kaiser 14、5軸で 69%）。**「10 個の独立な CID 値」ではない**。相関した CID 値（活動16束・規模10束）を別々の物理 param に当てると、**実質同じ軸を複数回入れる＝交絡**。M_c4 値（B_gen/S_avg/r_core/phase_sig）も、B_gen は規模束に、S_avg/r_core/phase_sig は各々ほぼ独立束で、4 値中 3 値が独立軸に乗る。

## §2 物理 param 同士の独立性・干渉（台帳パート1 実行順による）

配線可能 param（パート3 ✅）を、**作用する状態変数**で分類（同じ状態変数を奪い合う＝干渉）:

| 状態変数 | そこに効く param（op#）| 干渉度 |
|---|---|---|
| **L 潜在** | latent_refresh_rate(1 +) / latent_to_active_threshold(2 gate) / **plb(2 消費)** / auto_growth(19 L−=) | 中（plb と latent_rate は L を奪い合う）|
| **θ 位相** | **K_sync(4 同期)** / gamma(6 流位相係数) / flow_coefficient(7 θ 使用) / [初期θ・semantic_pressure(31)] | 中（K_sync と gamma が位相系で競合）|
| **E エネルギー** | flow_coefficient(7 E 移動) / **decay_rate_node(22 E*=)** / 化学 exothermic・E_yield(11,13,14 E+) / E_low・E_thr ゲート | 中 |
| **S リンク強度** | auto_growth(19 +=) / intrusion_rate(21 swap) / **decay_rate_link(23 *=)** / c_max(24 排他) / 化学 S_thr ゲート / flow 間接 | **高（4+ param が S を押し引き＝最も過剰決定）** |
| **R 共鳴** | **beta(18 上限 + 23 リンク減衰の両方)** / beta_max(18 上限) | beta は**2 演算に出現＝本質的な結合 knob** |
| **Z 化学種** | p_seed・ab_ratio(9) / E_thr・S_thr・P_thr・E_low(10,12 ゲート) / E_yield・exothermic(11,13,14) | 高（化学内で連動）|

**step 内の逐次結合（別状態を跨ぐ干渉）**:
- Flow が **θ → E** を結合（op6→7）。
- beta が **R ↔ S** を結合（op18 で R 上限、op23 で R が S 減衰を抑制）。
- Auto-Growth が **R, L → S** を結合（op19）。
- ＝ **S は最下流で過剰決定**（auto_growth/decay_link/intrusion/c_max + 上流 R,L,θ,E から流入）。

→ 素の記述: **物理 param は独立でない**。状態変数（L/θ/S/E/R/Z）ごとに束ねられ、同じ状態変数に効く param を同時に CID で振ると**効果が分離できない**。**独立に効く軸 ≈ 6〜7**: {N（基盤）}・{L 軸：plb か latent_rate のどちらか}・{θ 軸：K_sync}・{E 軸：decay_node}・{S 軸：auto_growth/intrusion/decay_link/c_max の1つ}・{R 軸：beta}・{Z 軸：化学を1束}。**beta は2演算に出るので「独立軸」でなく「結合 knob」**として別扱い要。

→ **§1（CID 値 ~5-14 独立軸）と §2（物理 param ~6-7 独立軸）は同オーダー**。合理的全検は「独立な CID 軸 → 独立な物理軸」の ~6-7 対応であって、20+ knob ではない、という材料。

## §3 「全検」の現実的規模・回るか・n_core 跨ぎ母集団

### 配線可能 knob 数（パート3 ✅ 全部1対1）
plb / latent_refresh_rate / latent_to_active_threshold / K_sync / beta / beta_max / decay_rate_node / decay_rate_link / flow_coefficient / gamma / alpha / resonance_interval / max_cycle_length / cycle_weights / auto_growth_rate / intrusion_rate / 化学(E_thr,S_thr,P_thr,E_low,exothermic,E_yield_syn,E_yield_auto,p_seed,ab_ratio) / c_max / N / 初期θ ＝ **約 25〜28 knob**（配線不可: grid幅[N従属]・BIAS・bg_prob・literal）。

### ★ コスト構造の重要事実（合議の前提を正す）
- **knob 数は child 数を増やさない**。child を1本回すコストは step 数と N で決まり、param を init で何個セットしても変わらない。**全検(25 knob) と 4 knob の per-run コストはほぼ同じ**。
- ＝ 合議の前提「204 × knob 数の計算量」は誤り。**cost driver は CID数 × 対照 × seed × step（× N）**。膨らむのは **n_core 跨ぎ（CID 増）と seed 数**。

### n_core 跨ぎ母集団（formed 85）
| n_core | CID 数 | B_gen → N |
|---|---|---|
| 2 | **54** | 11.0〜13.1 → N 110〜131 |
| 3 | **3**（少なすぎ）| 18.3〜19.7 → N 183〜197 |
| 4 | 11 | 25.2〜27.0 → N 252〜270 |
| 5 | 17 | 32.6〜35.4 → N 326〜354 |
| 計 | **85** | 全 N 110〜354（**最大 3.2×**）|

→ **B_gen は n_core にほぼ連動**（n_core 内で横並び、跨ぐと段階的）。**「N=5000」は未達**（max N=354）。5000 ノードにこだわる理由は本データ上は見当たらない（B_gen が桁で振れない＝max/min 3.2 倍）。n_core 跨ぎで N は約 3 倍動くが桁ではない。**n_core=3 は 3 CID しかなく相関/検定に不足**。

### 計算量見積（4対照・35k step・per-child 236 cpu-sec@N338 基準、N 比例で補正）
| seed | 全 child（85×4×seed×2ratio）| Pool24 実時間 |
|---|---|---|
| seed=3 | 2,040 | **~3.0 h** |
| seed=12（§4 推奨）| 8,160 | **~12.2 h** |

→ **回る**（Taka「並列で 5000 ノードでも 3 時間ちょっと」の範囲）。seed=12・n_core 全跨ぎ・2ratio で ~12h。knob を 4→25 に増やしてもこの数字は変わらない。

## §4 選定合理性の候補基準（合議のたたき台・複数・決めない）

| 案 | 内容 | 長所 | 短所 |
|---|---|---|---|
| **案A 独立軸代表** | §1 相関クラスタごとに代表1値を選び、§2 独立な物理軸（~6-7）に1対1で当てる | **交絡最小**・効果が状態変数ごとに分離可・CID軸数(~5-14)と物理軸数(~6-7)が整合・解釈明快 | 「全検」でない（束内の特定値を捨てる＝代表選択の恣意）・束内で個別に効く値を見逃す恐れ |
| **案B 構造同型拡張＋対照吸収** | 台帳の構造同型写像（S_avg→plb 等）を全 param に拡張、相関は **pairing 検定/多数置換 shuffle** で統計的に吸収 | 台帳の原理的写像を活かす・チャネル多い・相関を除外でなく検定で扱う | 相関入力→干渉 param は**効果空間でなお交絡**（チャネル別 pairing は妥当でも「どの CID 値が駆動か」は不明瞭のまま）|
| **案C 純全検** | 配線可能 25 knob を全部1対1、解釈はチャネル別 pairing 検定で個別に | 最大網羅・事前除外なし（Taka「全部取り込む」に忠実）・何も見逃さない | 25 knob を 6-7 独立物理軸に詰める＝**大量冗長/交絡**・効果分離不能・「系がどう変わった」を特定要因に帰属できない・S への過剰決定で何が効いたか言えない |
| （ハイブリッド）| 第1段＝案A 規模で独立軸スクリーン → 信号の出た束だけ第2段で束内全検 | 段階的・コスト効率・案C の網羅性を信号箇所に集中 | 2段で設計複雑・第1段の代表選択が第2段を縛る |

**合議で詰める核心**（材料として提示、決めない）:
1. 「全検」の定義 = 全 knob を繋ぐ(案C) か / 独立軸を網羅する(案A) か。**§1-2 から「独立軸 ~6-7」が実体**で、25 knob は冗長。
2. real≒shuffle の真因は **比較統計が pairing 盲目**（前調査）＝ knob を増やしても mean/std 対照では検出されない。**pairing 検定が前提**。
3. cost driver は knob でなく **CID×seed**。全検の追加コストはほぼゼロ、n_core 跨ぎと seed=12 が効く。

## やらないこと / 一方向保証
- やらないこと: child-world を回す・smoke・効果測定、選定確定（3AI 合議＋Taka）、写像を「正しい一つ」に決定、crown。
- 一方向: 読＝frozen（per_subject_seed0・台帳・既存 parquet・配線情報）。書＝本文書のみ。コード実行は read-only（相関/PCA/コスト計算）。親 physics/inject/ledger/state 非書込。

---

## 一文サマリ
全検 選定合理性の判断材料（Code A、2026-06-21、調査のみ・実行ゼロ・選定確定なし）── **§1 CID 値は実質 ~5〜14 独立軸**（formed 85・73変数、第1軸46%、|r|0.9 で73→40、Kaiser14、巨大クラスタ＝活動/露出16束・規模10束で B_gen と n_core は同束）＝「10 個の独立値」ではなく相関値を別 param に当てると交絡。**§2 物理 param も独立でなく状態変数(L/θ/S/E/R/Z)で束ねられ独立軸 ~6〜7**（S が過剰決定、beta は R↔S 結合 knob、Flow が θ→E 結合）＝ CID 軸数と同オーダー。**§3 配線可能 ~25 knob だが knob 数はコストを増やさない**（cost driver=CID×対照×seed×step、合議前提「204×knob」は誤り）、n_core 跨ぎ母集団 85（2:54/3:3/4:11/5:17、N 110〜354＝3.2倍で桁でなく**5000 ノード未達**）、seed12・全跨ぎ・2ratio で **~12h で回る**。**§4 基準案 A(独立軸代表・交絡最小)/B(構造同型＋pairing 吸収)/C(純全検・冗長交絡)＋ハイブリッド**を長短で提示。核心: 独立軸 ~6-7 が実体ゆえ 25 knob は冗長、real≒shuffle 回避に pairing 検定が前提、コストは knob でなく CID×seed。選定確定・実行はせず 3AI 合議＋Taka へ。
