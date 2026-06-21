# 物理層演算・CID 値・対応可能性 全数台帳（設計フェーズ・実行ゼロ）

## 自己規律宣言（Code A）
① 過去引用済（実コード読解）: `genesis_physics.py`(5力+inject) / `realization.py` / `autogrowth.py` / `intrusion.py` / `chemistry.py` / `genesis_state.py` / `esde_v82_engine.py`(step_window 実行順・背景注入・BIAS) / `v19g_canon.py`(全定数) / `esde_v43_engine.py`(param 構築・semantic_pressure)。CID 値＝`per_subject_seed0.csv`(130 カラム)。配線＝前回 `wiring_probe.py`(plb=constructor / physics.params 後書き / state init / BIAS=module global / grid=N従属)。
② Taka 逐語（仕様）: 「物理層の演算を一つ残らず一行ずつ／CID が持つ値を一つ残らず一行ずつ／固定値の一つ一つについて変数化できるか・CID のどの値を当てられそうか・散るか。網羅優先。**処理を回すな、台帳を作るだけ**。N=B_Gen×10（確定）も入れる」。
③ 成否判定は Taka。④ 集約語なし。crown 禁止。写像を「正しい一つ」に決めない（候補を全数）。

## 観察対象注釈ブロック
設計フェーズの台帳。child-world を**回さない・立てない・smoke しない・効果を測らない**。配線確認は read-only probe レベルのみ（前回 `wiring_probe.py` で実施済、本資料は新規実行なし）。読＝frozen（v19g_canon / genesis_physics.py 他 / per_subject_seed0）。書＝本 md のみ。親 physics/inject/ledger/state 非書込。

*作成*: 2026-06-20、Code A。値表記: 「**実行時値**（dataclass 既定と異なる場合は併記）」。実行時値は V43Engine が `BASE_PARAMS`/canon 定数を注入したもの。canon→各 Params の配線が未確認の箇所は ⚠ で明示。

---

## 0. child-world の位置づけ（文書上で固定・現行技術仕様とのズレの扱い）
**child-world = V82 系既存箱庭の縮小・param 変調版。** 具体的に `V82Engine(N≈100) + V43 物理 + VirtualLayerV9` ＝ **現行 v918 main run と同一のエンジンスタック**を N と param だけ変えたもの。**純 ecology/engine Genesis（5力7オペレータ）の独立再実装ではない。**
- ∴ child-world は **V43/V82 層の付加（環境要因 semantic_pressure 常時ON / BIAS 背景 seeding）を継承する**。これらは核 Genesis 物理（ecology/engine）でなく run-path 層。
- **semantic_pressure の位置づけ（慎重に）**: V43 定義（`esde_v43_engine.py:374`）の node 層環境要因で、`V82.step_window:226` で常時呼ばれる＝**現行 v918 main run でも常時 ON**。純 Genesis 物理法則ではない。child-world は V82 箱庭なので**継承する**（OFF 化は Taka 設計判断＝下記）。
- **この台帳の読み方**: 「現行 Genesis 仕様そのもの」ではなく、**child-world 実験用の実装候補台帳（V82/V43/Genesis の配線実態）**。エンジンレベルでは「現行Genesis縮小版」と「V82系子系」は同一（どちらも V82Engine）＝区別は仕様レベル（純ecology/engine 物理 vs run-path 付加込み実装）。本台帳は後者（実装実態）を扱う。
- **パート1 の層タグ**: 核 Genesis（ecology/engine, op 1-26 + 32）と V43/V82 run-path 付加（op 27-31: BIAS seeding / stress(現行OFF) / semantic_pressure(常時ON)）を区別する（下表「層」列）。
- **確定（Taka 2026-06-20 ＋ 実 run 全数確認）**: 方針「その後の試験がどちらで回ったかに合わせる／思いっきり Genesis 系に戻さず可能な限り最新版」に基づき素体を固定:
  - **2 環境要因の対応**: 「全体に影響する天候(global)」＝ **stress_decay**（link 層・`stress_intensity=links/link_ema` ＝系全体の好不況）／「局所的に発生(local)」＝ **semantic_pressure**（node 層・per-node θ 摂動＋近傍 latent）。
  - **stress（天候/global）＝ OFF 確定**。実 run 全数で OFF：`v918:1536` / `v105:1502` / stage3 / v1114 step2a(v105 run 経由) すべて `stress_enabled=False`。**off の経緯**＝v9.3+ で「**二重平衡干渉解消**」のため明示的に切った（θ空間最適化とリンク密度最適化の基準競合＝global な link 圧が θ 動学と destructive に干渉、NET +0.06・崩壊なしに改善。`05_primitive:102` / `09:768`）。＝realism/diversity 意図の放棄でなく、global 因子が core 動学を不安定化したための技術的撤去。
  - **semantic_pressure（局所/local）＝ ON 確定**。実 run 全数で常時 ON（`v82:226` 無条件呼び、無効化箇所なし）。その後の試験はすべて local 因子 ON で回っている。
  - **child-world 素体 ＝ 最新 V82 箱庭**（`V82Engine + VirtualLayerV9`、**stress OFF + semantic_pressure ON ＝ v918/v105 main run と同一設定**の縮小・param 変調）。**核 ecology/engine のみの最小 Genesis には戻さない**（Taka「思いっきり Genesis 系にすると意図が違いすぎる、可能な限り最新版」）。
  - **補足（Taka 意図との接続）**: 当時望んだ「2 因子で多様性飛躍／物理をより柔軟に」のうち global 因子(stress)は dual-equilibrium で撤去された経緯。child-world の **per-CID param 変異**は、その「柔軟な物理で多様性を出す」意図を**別ルート**（環境摂動でなく法則変異・各 child 独立＝干渉なし）で実現する手段にあたる。

---

# パート1 — 物理層演算 全数（per-step 実行順 + 周辺）

| # | 演算 | 何をするか（式） | 関与状態 | 使う固定値（実行時値） | コード位置 |
|---|---|---|---|---|---|
| 起動 | run_injection | INJECTION_STEPS 回 physics.inject 反復で点火 | E,alive_n,S | INJECTION_STEPS=300, INJECT_INTERVAL=3 | v19g_canon:71 / v43 run_injection |
| 1 | Realization-A 潜在補充 | 500 pair: `L[k]=min(1, L[k]+|randn|·rate·mean(F_i,F_j))` | L,F | latent_refresh_rate=0.003(canon)⚠/0.002(既定), 500 cap | realization.py:50-61 |
| 2 | Realization-B リンク誕生 | 各 alive node が3候補: `p=plb·L_ij; rng<p→add_link(thr), L-=thr` | L,alive_l | p_link_birth=0.007, latent_to_active_threshold=0.07(canon)⚠/0.05, candidates=3 | realization.py:63-82 |
| 3 | Phase Rotation A1 自然回転 | `dθ[i]=ω[i]+alpha·E[i]` | θ,ω,E | alpha=0.0 | genesis_physics.py:122-123 |
| 4 | Phase Rotation A2 Kuramoto同期 | `dθ[i]+=K_sync·Σ_j sin(θj-θi)/len(nbrs)` | θ,近傍 | **K_sync=0.1** | genesis_physics.py:126-133 |
| 5 | Phase Rotation A3 適用 | `θ+=dθ; θ%=2π` | θ | — | genesis_physics.py:135-136 |
| 6 | Flow B1 位相係数 | `pf=clip(0.5+0.5·gamma·cos(θj-θi),0,1)` | θ | gamma=1.0 | genesis_physics.py:157-159 |
| 7 | Flow B2 エネルギー流 | `f=flow_coeff·S·(Ej-Ei)·pf; flows[li]+=f,[lj]-=f` | S,E,θ | flow_coefficient=0.1 | genesis_physics.py:163-165 |
| 8 | Flow B3 適用 | `E[i]=clip(E[i]+net,0,1)` | E | — | genesis_physics.py:167-168 |
| 9 | Chemistry 種化 | 注入Dust prob `p_seed`→A/B(`ab_ratio`) | Z | p_seed=0.1, ab_ratio=0.5 | chemistry.py:70-80 |
| 10 | Chemistry 崩壊探索 R3 | C(Z=3) かつ `E<E_low`→崩壊候補 | Z,E | E_low=0.2 | chemistry.py:136-142 |
| 11 | Chemistry 崩壊適用(発熱) | `Z=0; E+=exothermic_release` | Z,E | exothermic_release=0.17(canon)⚠/0.15 | chemistry.py:103-106 |
| 12 | Chemistry 候補ゲート | `S≥S_thr & E≥E_thr(両端) & cos(Δθ)≥P_thr` | S,E,θ,Z | S_thr=0.3, E_thr=0.26(canon?)⚠/0.3, P_thr=0.7 | chemistry.py:152-172 |
| 13 | Chemistry R1 合成 A+B→CC | `Z=3,Z=3; +E_yield_syn` | Z,E | E_yield_syn=0.08(canon)⚠/0.0 | chemistry.py:114-120 |
| 14 | Chemistry R2 自触媒 C+A→CC | `Z→3; +E_yield_auto` | Z,E | E_yield_auto=0.0 | chemistry.py:121-129 |
| 15 | Chemistry 貪欲マッチ | 各 node ≤1 反応/step | Z | — | chemistry.py:194-206 |
| 16 | Resonance C1 閉路探索 | 10step毎 `find_all_cycles(≤5)` | alive_l | resonance_interval=10, max_cycle_length=5 | genesis_physics.py:172-178 |
| 17 | Resonance C2 R蓄積 | `R_new[lk]+=cycle_weights[len]` {3:1,4:.5,5:.25} | R | cycle_weights | genesis_physics.py:181-193 |
| 18 | Resonance C3 R上限 | `R=min(val, beta_max/beta=5.0)` | R | beta_max=5.0, beta=1.0 | genesis_physics.py:195-197 |
| 19 | Auto-Growth | R>0: `a=min(rate·R, L, 1-S); S+=a; L-=a` | S,R,L | auto_growth_rate=0.03(canon)⚠/0.02 | autogrowth.py:58-63 |
| 20 | Intrusion 島判定 | 連結成分 `S≥S_STRONG, size≥3` | S | S_STRONG=0.30 | intrusion.py:23-41 |
| 21 | Intrusion 境界swap | 境界node prob `intrusion_rate`: `a=min(δ,S[intra]-.01); S[intra]-=a,S[out]+=a` | S | intrusion_rate=0.002(canon)/0.001, delta_swap=0.02 | intrusion.py:103-166 |
| 22 | Decay D1 ノードE減衰 | `E[i]*=(1-decay_rate_node)` | E | decay_rate_node=0.005(NODE_DECAY)/0.05(既定) | genesis_physics.py:206 |
| 23 | Decay D2 リンクS減衰(共鳴抑制) | `eff=decay_rate_link/(1+beta·R); S*=(1-eff)` | S,R | decay_rate_link=0.05, beta=1.0 | genesis_physics.py:210-211 |
| 24 | Exclusion E1 排他 | `ΣS[i]>c_max`→最弱link kill until ≤c_max | S,alive_l | c_max=C_MAX=1.0 | genesis_physics.py:215-228 |
| 25 | Extinction ノード死 | `E<EXTINCTION→E=0,alive_n除外` | E,alive_n | EXTINCTION=link_death_threshold=0.007 | genesis_state.enforce_extinction |
| 26 | Extinction リンク死 | `S<0.007→kill_link` | S,alive_l | 0.007 | genesis_state |
| 27 | Background BIAS選択 | `pd=(1-BIAS)·uniform+BIAS·成長スコア確率` | (選択) | **BIAS=0.7**(module) | esde_v82_engine.py:179-184 |
| 28 | Background 注入 | alive node prob `bg_prob`→target: `E=min(1,E+0.3)` | E | background_injection_prob=0.003(module), +0.3(literal) | esde_v82_engine.py:191-199 |
| 29 | Background Z分化 | 注入Dust prob 0.5→A/B | Z | 0.5(literal) | esde_v82_engine.py:200-202 |
| 30 | stress_decay（現行OFF） | `stress_intensity=links/link_ema`→link取捨 | S,alive_l | stress_enabled=False(main) | esde_v82_engine.py:58,205 |
| 31 | semantic_pressure（常時ON） | prob `pressure_prob`: `θ[n]+=strength·U(-1,1)`; 近傍latent`+latent_boost`; 島内部shield | θ,L | pressure_prob=0.005, latent_boost=0.05, pressure_strength, 島shield | v43:374 / v82:226 |
| 32 | physics.inject（外部I/F） | target: `E+=inject_amount, alive_n追加`; pair link(radius内) | E,S,alive_n | inject_amount=0.6, inject_prob=0.15, inject_pair_radius=8, inject_link_strength=0.3 | genesis_physics.py:232 |

> ⚠＝canon 定数（BASE_PARAMS）と dataclass 既定が異なり、V43Engine による canon→Params 配線が本台帳では未確認の箇所（実装時に要確認）。「漏れていた」と後で分かるよう明示。
>
> **層タグ（§0 参照）**: op **1-26 + 32** ＝ **核 Genesis 物理（`ecology/engine/`）**＝純 Genesis 仕様。op **27-29 BIAS背景 seeding / 30 stress(現行OFF) / 31 semantic_pressure(常時ON)** ＝ **V43/V82 run-path 付加**（純 Genesis 物理でなく、V82 箱庭の付加層。現行 v918 main run も同じくこれらを伴う）。child-world を「核 ecology/engine 物理のみ」に作るなら op 27-31 を外す選択肢があり、「V82 箱庭縮小」とするなら継承する＝§0 の Taka 設計判断。

---

# パート2 — CID 値 全数（per_subject_seed0 の130カラム）

*固定/時変*: M_c・B_Gen・birth_window・phase_sig は誕生時固定、他は時変。*散る*: n_core=5 の17 CID で CV>0.1=○。*由来*: 値が出る層。

| # | カラム | 固定/時変 | n5値域 | CV(n5) | 散る | 由来層 |
|---|---|---|---|---|---|---|
| 1 | seed | 固定 | 0 | - | × | 識別子 |
| 2 | cognitive_id | 固定 | [0,273] | 0.741 | ○ | 識別子 |
| 3 | birth_window | 固定 | [0,68] | 0.747 | ○ | 存在層(生死) |
| 4 | host_lost_window | 時変 | 59/NaN | - | × | 存在層(生死) |
| 5 | reaped_window | 時変 | (空多) | - | × | 存在層(生死) |
| 6 | final_state | 時変 | hosted/ghost | - | × | 存在層(生死) |
| 7 | ghost_duration | 時変 | [0,10] | 4.123 | ○ | 存在層(生死) |
| 8 | original_phase_sig | 固定 | [-2.877,2.376] | 18.302 | ○ | 存在層→認知(birth) |
| 9 | last_n_partners | 時変 | [30,64] | 0.220 | ○ | 認知層(familiarity数) |
| 10 | last_familiarity_max | 時変 | [30.3,500] | 1.359 | ○ | 認知層(disposition) |
| 11 | last_attention_size | 時変 | [465,2092] | 0.320 | ○ | 認知層(attention) |
| 12 | last_tag_window | 時変 | [59,69] | 0.037 | × | 認知層 |
| 13 | prev_social | 時変 | [0.516,1.0] | 0.158 | ○ | 認知層(disposition) |
| 14 | prev_stability | 時変 | [0.59,0.722] | 0.050 | × | 認知層 |
| 15 | prev_spread | 時変 | [0.794,0.876] | 0.027 | × | 認知層 |
| 16 | prev_familiarity | 時変 | [4.38,23.07] | 0.377 | ○ | 認知層(familiarity) |
| 17 | current_social | 時変 | [0.516,1.0] | 0.160 | ○ | 認知層 |
| 18 | current_stability | 時変 | [0.606,0.718] | 0.046 | × | 認知層 |
| 19 | current_spread | 時変 | [0.805,0.877] | 0.023 | × | 認知層 |
| 20 | current_familiarity | 時変 | [6.42,23.35] | 0.368 | ○ | 認知層(familiarity) |
| 21 | delta_social | 時変 | [-0.042,0.113] | 1.397 | ○ | 認知層 |
| 22 | delta_stability | 時変 | [-0.058,0.115] | 11.812 | ○ | 認知層 |
| 23 | delta_spread | 時変 | [-0.03,0.061] | 12.469 | ○ | 認知層 |
| 24 | delta_familiarity | 時変 | [-2.47,2.04] | 3.352 | ○ | 認知層(familiarity) |
| 25 | generated_tags | 時変 | gain_/loss_… | - | × | 認知層 |
| 26 | state_at_window | 時変 | hosted | - | × | 存在層(生死) |
| 27 | ttl_bonus | 時変 | [0,9] | 0.842 | ○ | 認知層(pickup v9.8c) |
| 28 | n_pickups_won | 時変 | [0,9] | 0.842 | ○ | 認知層(pickup) |
| 29 | n_pickups_lost | 時変 | [0,19] | 0.720 | ○ | 認知層(pickup) |
| 30 | effective_ttl | 時変 | [10,19] | 0.222 | ○ | 認知層(pickup) |
| 31 | v99_formation_status | 時変 | formed/unformed | - | × | 認知層(内部軸 v9.9) |
| 32 | v99_trace_len | 時変 | [0,5] | 0.263 | ○ | 認知層(内部軸) |
| 33-48 | v99_range_{social,stability,spread,familiarity}_{min,max,mean,std} | 時変 | (各) | 0.015〜0.65 | 一部○ | 認知層(disposition 範囲) |
| 49-63 | v99_drift_{axis}_{positive,negative,neutral} + v99_lowest_std_axis / dominant_*_drift_axis | 時変 | [0,5]/記号 | 0.05〜2.31 | 一部○ | 認知層(内部軸 drift) |
| 64 | v10_pulse_count | 時変 | [10,500] | 0.666 | ○ | 認知層(pulse v9.10) |
| 65 | v10_tag_trigger_last | 時変 | Normal/both/none | - | × | 認知層(pulse) |
| 66 | v10_n_normal | 時変 | [6,417] | 0.680 | ○ | 認知層(pulse) |
| 67 | v10_n_major | 時変 | [5,164] | 0.619 | ○ | 認知層(pulse) |
| 68-71 | v10_theta_{social,stability,spread,familiarity}_last | 時変 | (各) | 0.20〜0.73 | ○ | 認知層(MAD-DT 閾) |
| 72-75 | v10_R_{axis}_last | 時変 | (各, familiarity CV=13.9) | 1.7〜13.9 | ○ | 認知層(MAD-DT 驚き) |
| 76-83 | v10_R_max/min_{axis} | 時変 | (各) | 0.29〜0.54 | ○ | 認知層(MAD-DT) |
| 84 | v11_b_gen | 固定 | **[32.58,35.37]** | **0.025** | **×** | 認知層(Capture; **物理birth由来=固有値**) |
| 85 | v11_m_c_n_core | 固定 | 5 | - | × | 認知層(Capture; 物理birth由来) |
| 86 | v11_m_c_s_avg | 固定 | [0.274,0.464] | 0.147 | ○ | 認知層(Capture; 物理birth由来) |
| 87 | v11_m_c_r_core | 固定 | [0.219,0.900] | 0.364 | ○ | 認知層(Capture; 物理birth由来) |
| 88 | v11_m_c_phase_sig | 固定 | [-2.877,2.376] | 18.302 | ○ | 認知層(Capture; 物理birth由来) |
| 89 | v11_n_pulses_eval | 時変 | [7,497] | 0.673 | ○ | 認知層(Capture) |
| 90 | v11_n_captured | 時変 | [2,171] | 0.680 | ○ | 認知層(Capture) |
| 91 | v11_capture_rate | 時変 | [0.207,0.421] | 0.199 | ○ | 認知層(Capture) |
| 92-96 | v11_mean_delta / d_n / d_s / d_r / d_phase | 時変 | (各, d_r CV=0.49) | 0.09〜0.49 | 一部○ | 認知層(Capture Δ) |
| 97-116 | v915_* (fetch/divergence/mismatch/age_factor/observed/missing 計20) | 時変 | (各, min_age_factor CV=4.1) | 0.04〜4.1 | 多く○ | 認知層B(自己読み v9.15-16) |
| 117-121 | v917_total_other_contacts / features_fetched / features_missing / avg_visible_ratio / unique_contacts | 時変 | (各) | 0.23〜0.56 | ○ | 認知層(他者読み v9.17) |
| 122 | v18_cognitive_gain_final | 時変 | [23,35] | 0.082 | × | 認知/意識層(=C=消費Q, A+C v9.18) |
| 123 | v18_v_unified_concentration_birth | 固定相当 | [0.219,0.900] | 0.364 | ○ | 物理層同期(Kuramoto, v9.18) |
| 124 | v18_v_unified_concentration_final | 時変 | [0.043,0.763] | 0.461 | ○ | 物理層同期 |
| 125 | v18_v_unified_direction_shift_final | 時変 | [0.172,2.964] | 0.555 | ○ | 物理層同期 |
| 126 | v18_v_unified_k_final | 時変 | 5 | - | × | 物理層同期(node数) |
| 127 | v18_theta_distance_from_birth_final | 時変 | [1.03,2.41] | 0.195 | ○ | 物理層θ距離 |
| 128 | v18_theta_distance_coverage_ratio_final | 時変 | 1.0 | - | × | 物理層(member凍結) |
| 129 | v18_finalized_at_step | 時変 | [20000,25000] | 0.049 | × | 記録時刻 |
| 130 | v18_finalize_reason | 時変 | tracking_end/ghost | - | × | 存在層(生死) |

> 散る列（CV>0.1）= **90 / 数値110**（前回 wiring_probe で確認）。**B_Gen と n_core は n5 で散らない**（CV=0.025／一定＝n_core 決定）。familiarity 系（last_familiarity_max / current_familiarity / R_familiarity / delta_familiarity）は散る。33-121 の範囲行は群でまとめ（各列は wiring_probe.py 全数出力で確認可）。

---

# パート3 — 固定値→変数化 ＋ CID 対応可能性（全数）

各物理固定値について: 配線（per-child 変調法）／CID 候補（複数・構造同型の根拠）／候補が n5 で散るか／注意。
**共通注意**: physics.params/realizer/grower/chem の後書きは「**書ける**は wiring_probe で確認、**効くか**は別（未測定、設計フェーズなので測らない）」。

| 物理固定値（実行時値） | 配線（per-child） | CID 候補（複数, 根拠） | 候補 n5 散る | 注意 |
|---|---|---|---|---|
| **N=5000** | constructor ✅ | **B_Gen×10（Taka確定）** / n_core | B_Gen×: n5横並び✗ / cross-n_core○ | grid は N 従属（独立不可）。下記 N 節 |
| **plb=0.007**（リンク誕生） | constructor ✅ | S_avg(結合強度→誕生) / last_familiarity_max(接触) / v11_n_captured(活動) | ○ | 効くか別 |
| **K_sync=0.1**（同期） | physics.params ✅ | r_core(同期度) / v18_v_unified_concentration(同期) / v10_R_familiarity | ○ | 効くか別 |
| **beta=1.0**（共鳴減衰抑制） | physics.params ✅ | r_core / v11_mean_d_r(共鳴ズレ) / v10_R_max_* | ○ | 効くか別 |
| **beta_max=5.0**（R上限） | physics.params ✅ | v10_R_max_familiarity / v11_n_captured | ○ | 効くか別 |
| **decay_rate_node=0.005**（E減衰） | physics.params ✅ | v11_mean_delta(捕捉ズレ) / ghost_duration / v915_divergence | ○ | 効くか別 |
| **decay_rate_link=0.05**（S減衰） | physics.params ✅ | v915_divergence_norm / v99_range_*_std | ○ | 効くか別 |
| **flow_coefficient=0.1**（流量） | physics.params ✅ | current_social / last_attention_size | ○ | 効くか別 |
| **gamma=1.0**（位相-流影響） | physics.params ✅ | v18_v_unified_concentration / r_core | ○ | 効くか別 |
| **alpha=0.0**（E-ω結合） | physics.params ✅ | v10_pulse_count / v11_capture_rate | ○ | alpha=0 は「安定開始」設計、上げると不安定化 |
| **resonance_interval=10** | physics.params ✅ | v10_pulse_count（離散・整数化要） | ○ | 効くか別 |
| **max_cycle_length=5** | physics.params ✅ | n_core(整数) | n5一定✗ | n_core 跨ぎでのみ |
| **cycle_weights{3:1,4:.5,5:.25}** | physics.params ✅ | (構造写像難) | — | 候補薄 |
| **auto_growth_rate=0.03** | grower.params ✅ | v11_n_captured / v10_n_major(活動→成長) | ○ | 効くか別 |
| **latent_refresh_rate=0.003** | realizer.params ✅ | last_attention_size / v915_fetch_count | ○ | 効くか別 |
| **latent_to_active_threshold=0.07** | realizer.params ✅ | v11_mean_delta / v915_final_missing_fraction | ○ | 効くか別 |
| **intrusion_rate=0.002**（境界摂動） | intruder 属性 ✅ | v99_drift_*（変動性） / delta_familiarity | ○ | 効くか別 |
| **delta_swap=0.02** | intruder 属性 ✅ | v99_range_*_std | ○ | 効くか別 |
| **S_STRONG=0.30**（島閾） | find_islands 既定引数 ⚠ | (per-call 既定, 後書き要工夫) | — | module 寄り・配線弱 |
| **chem E_thr=0.26/S_thr=0.3/P_thr=0.7/E_low=0.2** | chem.params ✅ | v11_mean_delta / v11_capture_rate / r_core | ○ | 効くか別 |
| **exothermic_release=0.17** | chem.params ✅ | v18_cognitive_gain(消費) | ×(CV0.08) | 候補散らず |
| **E_yield_syn=0.08 / E_yield_auto=0.0** | chem.params ✅ | v11_n_captured | ○ | 効くか別 |
| **p_seed=0.1 / ab_ratio=0.5**（種化） | chem.params ✅ | v11_capture_rate / current_social | ○ | 効くか別 |
| **inject_amount=0.6 等**（外部I/F） | physics.params ✅ | (外部注入用, 子init用途薄) | — | child では rate/plb 優先 |
| **rate（run_injection率）** | constructor ✅ | v10_pulse_count(活動) / v11_n_pulses_eval | ○ | 効くか別 |
| 初期θ分布（uniform[0,2π]） | state.theta init ✅ | **phase_sig（位相署名→von Mises）** | ◎ | 子の自前init=死線でない |
| ω分布（uniform[0.05,0.3]） | state.omega init ✅ | v10_pulse_count(発火) / R_*_last | ○ | 効くか別 |
| F 肥沃度（flat 1.0） | state.F init ✅ | v917_unique_contacts / last_attention_size | ○ | 効くか別 |
| c_max=1.0 | state.c_max ✅(属性) | n_core / last_n_partners(結合容量) | 一部○ | 効くか別 |
| EXTINCTION=0.007 | state 属性（後書き可?）⚠ | ghost_duration(死にやすさ) | ○ | 配線要確認 |
| **BIAS=0.7** | **module global ❌** | — | — | per-instance 不可（monkey-patch=sequential のみ） |
| **bg_prob=0.003** | **module(BASE_PARAMS) ❌** | — | — | step_window で BASE_PARAMS 直読み＝per-instance 不可 |
| 背景 E+0.3 / Z分化0.5 | **literal ❌** | — | — | ハードコード、変数化にコード改変要 |

## N について（N=B_Gen×10, Taka 確定）
- **配線**: ✅ `V82Engine(N=…)` constructor。
- **B_Gen 値域**: n5 で [32.58, 35.37]・**CV=0.025**（=n_core 決定で帯狭）。→ **N=B_Gen×10 = [326, 354]＝17 child で横並び**（n5 では N が散らない）。
- **cross-n_core**: B_Gen は n=2≈12 / n=3≈20 / n=4≈28 / n=5≈35（帯）→ N≈120 / 200 / 280 / 350（約3×）。**N を桁で振るには母集団を n_core 跨ぎにする**必要。
- **grid 幅**: `build_substrate(N)` で **N 従属**＝N を決めれば grid も決まる（独立 knob 不可）。
- **交絡**: B_Gen を N に使ったら、B_Gen を他 param に併用しない（同一 CID 値→2 param 禁止）。

## 全数の「できない／弱い」配線（網羅）
- ❌ **BIAS / bg_prob**: module global（per-instance 不可、monkey-patch=sequential のみ）。
- ❌ **背景 E+0.3 / Z分化0.5**: literal ハードコード（変数化にコード改変要）。
- ❌ **grid 幅**: N 従属（独立 knob 不可）。
- ⚠ **S_STRONG（島閾）**: find_islands の既定引数（per-instance 後書きに工夫要）。
- ⚠ **EXTINCTION / canon→Params 配線（latent/exothermic/E_yield/E_thr）**: 後書き/配線が本台帳で未確認（実装時に要確認）。
- 散らない候補（n5）: B_Gen / n_core / exothermic 候補(v18_cognitive_gain CV0.08) → n5 では物理条件を散らせない（cross-n_core 限定）。

---

## やらないこと / 一方向保証
- やらないこと: child-world を回す/立てる/smoke する、効果・傾向・クラスタを測る、設計を確定する、写像を1つに決める、crown。
- 一方向: 読＝frozen（v19g_canon / 物理オペレータ各 .py / per_subject_seed0）。書＝本 md のみ。コード実行は前回 probe の read-only 確認のみ（本資料で新規実行なし）。親 physics/inject/ledger/state 非書込。

## 一文サマリ
物理層演算・CID 値・対応可能性 全数台帳（Code A、2026-06-20、設計フェーズ・実行ゼロ）── **位置づけ（§0）**: child-world ＝ V82 系既存箱庭の縮小・param変調版（= 現行 v918 main run と同一エンジンスタック）であり、本台帳は「現行 Genesis 仕様そのもの」でなく **child-world 実装候補台帳（V82/V43/Genesis 配線実態）**。op 1-26+32 ＝核 Genesis（ecology/engine）、op 27-31（BIAS seeding / stress / **semantic_pressure**）＝ V43/V82 run-path 付加。**確定（Taka+実run全数確認）: stress(天候/global)＝OFF、semantic_pressure(局所/local)＝ON、素体＝最新 V82 箱庭（v918/v105 main と同一設定）。核 ecology/engine 最小 Genesis には戻さない。** stress off は v9.3+ 二重平衡干渉解消の技術的撤去（realism 放棄でない）。── **パート1**: 物理演算 32（起動 inject / Realization 2 / Phase Rotation 3 / Flow 3 / Chemistry 7 / Resonance 3 / Auto-Growth / Intrusion 2 / Decay 2 / Exclusion / Extinction 2 / Background 3 / stress(OFF) / semantic_pressure / inject）を式・状態・実行時値・行番号で全数。**パート2**: per_subject 130 カラム全数（固定/時変・n5 値域・CV・散る・由来層、familiarity 系散る・B_Gen CV=0.025 散らず）。**パート3**: 固定値ごとに 配線（**physics.params/realizer/grower/chem の後書き＝大半 per-child 可**、N/plb/rate=constructor、初期θ/ω/F=state init、**BIAS/bg_prob/literal/grid=不可**）／CID 候補複数（構造同型）／n5 で散るか／「書けるが効くは別」注意。N=B_Gen×10 は配線可だが n5 横並び（cross-n_core で約3×）。設計確定・実行はしない。判定は Taka。
