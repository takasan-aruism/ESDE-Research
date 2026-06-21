# 課題#1 下準備 — 一致率がどう計算されているかの見積もり（調査のみ・読解と dump）

## 自己規律宣言（Code A）
① 過去引用済: m19（4 粒度 trajectory: event~50step/pulse/step10 10step/window 500step、per-(cid,t) rank_1）、#30（演算的帰結を問え・気まぐれ指標禁止）、m29 監査（build_step10 と build_cid_vector の builder 差＝membership top5 0.97/5）、STEP3 cid_align で確認の atom_profiles_cache slot_keys 整合。
② Taka 逐語（原文）: 「一致率という確率的発生の存在のしかたを見る」「その前提として、一致率がそもそもどう計算されているかを正確に把握する。ここを取り違えると後段が全部崩れる」「演算を新たに当てない・指標を作らない・閾値を決めない・分布や Δ や濃度を計算しない」「具体的な数字があればそれで示してくれるとありがたい」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-17、Code A。*この STEP*: コードを読んで「何がどう一致率になるか」を事実で出すだけ。演算・指標・閾値・分布・網は作っていない。書込なし（parquet も書いていない）。

---

## 1. 一致率の定義（全経路：入力→演算→数）

`一致率(rank_1_sim) = max_atom cosine( CID 48次元ベクトル, atom profile 48次元 )`

### (1) CID 側ベクトル（48 次元・10 軸）
`build_{event,pulse,step10,window}_cid_vector(row, seed_max)` が **48 次元**を 10 軸で組む（各軸が `_gradient_distribute` の soft one-hot か simplex 正規化）:
- event/pulse/step10 は**同一の trajectory エンコーダ**（`temporal_vec, scale_vec, epistemological_vec(R_familiarity), ontological_vec, interconnection_vec, resonance_vec, symmetry_vec_pulse, lawfulness_vec, experience_vec, value_generation_vec`、`v106_pulse_trajectory.py`）。
- window のみ `_w` 変種（`epistemological_vector_w(window_fam_max)` 等。`window_fam_max` は R_familiarity を window 集約しただけ、境界 `EPISTEMOLOGICAL_BOUNDARIES=[10,30,60,150]` は共通）＝同じ 10 軸を window 集約値で組む。
- 軸順は `slot_keys()`(=AXES_ORDER) で固定（temporal 先頭）。

### (2) atom 側プロファイル（`atom_profiles_cache.npz`）
- shape **(326, 48)**＝326 atom × 48 軸。**valid 325 / 326**（1 atom は NaN 行＝除外）。
- 各 atom profile の 48 軸の**和 = 1.0（simplex）**。
- 作り方: `a1_batch` の各 word の 48 軸 `normalized_scores` を、その atom に属する word 内で **mean**（`v106_post_process.py:185-206 load_atom_profile`）。＝atom の「意味プロファイル」（言語側 A1 由来）。

### (3) 一致 = 正規化 cosine
- `sklearn cosine_similarity(vecs, atom_profiles[valid])`（`run_seed_{grain}` 各粒度共通、event:276 / pulse:345 / step10:258 / window:375）＝**両ベクトルを内部で L2 正規化した cosine**。
- CID ベクトルは「軸内 simplex」だが 48 次元全体は単位長でない → cosine が正規化を担う。atom profile は simplex。
- **raw / normalized の別出力は無い**（v1103 の raw/norm 二系列とは別物。ここは cosine 一本）。
- `rank_1_sim = その行の cosine の最大値`、`rank_1_atom = argmax の atom`。
- **具体数**: step10 seed0 先頭行 = cid 0 / t=10 / rank_1_atom=`TIM.appear` / **rank_1_sim=0.5159**（cid 48 次元 ⋅ atom profile の cosine 最大値）。

## 2. rank_1 だけか、全 326 atom か

- 各時点で**全 valid atom の sim を計算**する（`sim` は N×326 行列、`cosine_similarity(vecs, atom_profiles[valid])`）。
- **出力は rank_1 のみ**: step10/event/pulse の出力列は `rank_1_atom, rank_1_sim` だけ。window は加えて `max_sim, mean_sim`（集約値、per-atom ではない）。
- → **全 326 atom それぞれの一致率は「計算はされるが出力で捨てられている」。再計算で取得可能**（同じ vec × atom_profiles の cosine 行列をそのまま保持すれば全 326 が出る）。「ある時点で複数 atom がそれぞれどれくらい立っているか」は**現出力に無いが再計算で取れる**（計算はしていない＝在/無の確認のみ）。

## 3. 時間方向の実態（どの時点の CID 状態か）+ builder 差の所在

| 粒度 | 一致率の時点 | その時点の CID 状態 | builder |
|---|---|---|---|
| event | 各 event の t | t までの累積（lifespan_so_far, cum_pulse/alpha/beta/ingest, C_at_window_end ffill, R_familiarity asof） | trajectory 族 |
| pulse | 各 pulse の t | 同上（pulse 時点） | trajectory 族 |
| step10 | 10step grid の t | 同上（t まで、pulse 間は実質凍結） | trajectory 族 |
| window | window(500step) 末 | window 集約（window_fam_max 等） | trajectory `_w` 変種 |

- **4 粒度はいずれも「その時点まで／その window 内」の CID 状態から計算**（run-end 固定ではない）。
- **builder 差（m29 の所在を明示）**: 上記 4 粒度は全て **build_step10 族（trajectory エンコーダ: epistemological=R_familiarity, ontological informational=cum_pulse, symmetry=delta_pulse …）**。一方 **静的 `cid_atom_sim_matrix`（STEP2 が使用）は `build_cid_vector`（run-end 版: epistemological=last_familiarity_max〔count〕, informational=virt_fam_entries, symmetry=v99_drift …）で別族**。
  → m29 で観測した「sim_matrix と build_step10 が run-end でも top5 0.97/5 しか重ならない」は、この**別族（軸の入力が違う）**が原因。**4 粒度 trajectory 同士は同族**（window だけ集約変種）なので、粒度間比較は builder 交絡しない。sim_matrix(STEP2 静的) と trajectory(4 粒度) を跨ぐ比較だけが交絡する。

## 4. 何が一致率を動かすか（CID ベクトル各軸の依存先）

| 軸(48次元の区画) | 依存する物理層/CID 量 |
|---|---|
| temporal(0-6) | `lifespan_so_far`（CID 年齢） |
| scale(7-12) | `n_core_member`（構造サイズ） |
| epistemological(13-17) | `R_familiarity`（馴染み z） |
| ontological(18-22) | `Q_remaining/q0`・`cum_pulse`・`cum_alpha`・`n_core`・`C_at_window_end` |
| interconnection(23-27) | `cumulative_n_alphas`（α 累積） |
| resonance(28-31) | `C_at_window_end`（C 値） |
| symmetry(32-36) | pulse の `delta_social/stability/spread/familiarity` |
| lawfulness(37-40) | `pulse_density`（cum_pulse/lifespan） |
| experience(41-43) | `cum_ingestions`・`cum_q_spend`・`cum_pulse` |
| value_generation(44-47) | `q_spent`・`cum_ingest`・`cum_alpha`・`cum_beta` |

→ 観察事実: 一致率（cosine）は、この 10 軸経由で **lifespan / n_core / R_familiarity / Q / C / pulse 数 / α・β 数 / ingestion(Q奪取) 数 / q_spent** に依存する。これらは pulse 発火・摂食(Q奪取)・α/β 形成・C 変換・n_core 変化など**物理層と CID の動学で勝手に進む量**＝実験者が決めなくても一致率は動く（具体的にどの量経由かは上表）。

## 5. やらなかったこと（明示）
Δ・分布・濃度・浮かび上がり・spike の計算、閾値、網形成、CID 投影、センター接続、effect_size、位相化、全 326 sim の実計算は**していない**。本 STEP は「一致率がどう計算されるか」の読解と最小 dump のみ。

## 6. 一方向保証
読む=frozen（v106 trajectory コード/出力・atom_profiles_cache・step10 出力 csv）。**書込なし**（parquet も書いていない、本 md のみ）。物理/inject/ledger 非書込。

---

*以上 課題#1 下準備（Code A、2026-06-17）。一致率=cosine(CID48次元, atom profile48次元) の argmax(=rank_1_sim, 例 0.5159)。CID 側は 10 軸 trajectory エンコーダ(event/pulse/step10 同族, window は _w 集約変種)、atom 側は a1_batch word→48軸 mean の simplex profile(326 中 325 valid)。全326 sim は計算されるが出力は rank_1 のみ(再計算で全取得可)。4 粒度は「その時点まで」の状態、builder は全て build_step10 族(sim_matrix=STEP2 のみ build_cid_vector 別族=跨ぎ比較が m29 交絡)。一致率は lifespan/n_core/R_familiarity/Q/C/pulse/α β/ingestion/q_spent に 10 軸経由で依存。判定は Taka。*
