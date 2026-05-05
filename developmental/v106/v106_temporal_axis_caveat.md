# v10.6 時間軸混在 caveat

*作成*: 2026-05-06、Code A (Taka 指摘 2026-05-06 を受けて)
*位置づけ*: v10.6 の全結果 (smoke / stratified / baseline) に共通する **時間軸の制約** を整理した補足文書。
*参照される側*: `v106_smoke_main_run_report.md` §X、`v106_stratified_run_report.md` §X、`v106_baseline_run_report.md` §X (いずれも本書を参照)

## 0. 一文サマリ

v10.6 cid 構造ベクトルは ESDE Genesis 系の 25,000 step run のうち **3 種類のタイミング (誕生時固定値 1 列 + run 終了スナップショット 5 列 + run 全体集約 残り)** が 48 次元に同居しており、**ESDE の動学的 (step 単位) な振る舞いは捕捉していない** ため、本 v10.6 の atom alignment 結果は「run 集約 + 終了スナップショット時点の cid と Atom の対応関係」として解釈すべきであり、特に **動学的 atom (TIM.moment、ACT.destroy 等の瞬間性・瞬発性概念) は本ベクトル化では構造的に出にくい**。

---

## 1. 各軸の時間タイミング棚卸し

`v106_post_process.py` の cid 構造ベクトル生成コードを軸ごとに精査:

| 軸 | 入力データ | タイミング種別 | 補足 |
|---|---|---|---|
| 1. temporal | `lifespan_steps` (= 計算: birth_window × WIN_LEN → host_lost_step / reaped_step / RUN_END_STEP) | **集約スカラー** | cid 一生の長さ、1 値 |
| 2. scale | `n_core_member` (audit) | **誕生時固定値** | registered_step 時点、以後不変 |
| 3. epistemological | `last_familiarity_max` (per_subject) | **最後の pulse 時点** | per_subject の `last_*` 列は最終 pulse 時の値 |
| 4. ontological | mix: `v14_q_remaining/q0`, `v14_virtual_familiarity_entries`, `n_alphas_currently`, `n_core_member`, `C_at_run_end` | **run 終了スナップショット混合** | structural のみ誕生時、他 4 つは run 終了時 |
| 5. interconnection | `n_alphas_currently` | **run 終了スナップショット** | 「現在所属している α 数」 |
| 6. resonance | `C_at_run_end` | **run 終了スナップショット** | 文字通り run 終了時の C |
| 7. symmetry | `v99_drift_*_positive/negative/neutral` (4 軸 × 3 方向) | **run 全体集約** | window ごと drift カウントの run 全体合算 |
| 8. lawfulness | `v10_pulse_count / lifespan` | **run 全体集約** | pulse 密度 = 累積 / 寿命 |
| 9. experience | `n_ingestions_as_eater`, `n_phantom_contacts_as_eater`, `n_ingested_as_ghost_food`, `v10_n_normal`, `v10_n_major` | **run 全体累積** | event 経験回数の総和 |
| 10. value_generation | `v14_q_spent`, `n_observed_as_target`, `q_received_from_beta`, `c_received_from_beta`, `n_betas_joined` | **run 全体累積** | 累積消費・累積受領・累積所属 |

→ 48 次元の内訳: **誕生時固定 6 dim (scale 6 levels)** + **run 終了スナップショット 14 dim** (epistemological 5 + ontological 4 + interconnection 5) + **run 全体集約 28 dim** (resonance 4 + symmetry 5 + lawfulness 4 + experience 3 + value_generation 4 + temporal 7 + ontological.structural 1)。

---

## 2. 構造的バイアス

### 2.1 短寿命 vs 長寿命の不公平性

- **短寿命 cid (reaped at step 200)**: lifespan=200、累積指標は 200 step 分のみ
- **長寿命 cid (hosted at step 25,000)**: 25,000 step 分の累積
- → 同じ 0-1 正規化空間で比較されるが、データ生成期間が **最大 125 倍違う**
- 累積指標 (experience 軸 / value_generation 軸 / symmetry 軸 / lawfulness 軸) は **時間に応じて単調増加** しがちで、長寿命 cid が見かけ上「豊か」に見える
- → 層化解析の「long-lived cid のみが COG.enlightenment 接地」「hub cid (= long-lived の純粋集合) の 54.7% が partial_match」は **このバイアスの直接的帰結** の可能性

### 2.2 死後の状態混入

- `n_alphas_currently` は run 終了時の値
- reaped cid は run 中に消滅 → run 終了時 `n_alphas_currently = 0`
- → 80% 以上の cid (reaped) で interconnection 軸が **「isolated」レベル 1.0 一極**
- 集団平均の罠の根本要因の 1 つ

### 2.3 動学の代表点を選べていない

- 「最も活発だった時の cid」「初期成長期」「衰退期」「ピーク α 所属時」のような特徴時点を選べない
- 例: 「cid 487 が step 5000 で α 50 個に同時所属していた peak」を捕まえられない (run 終了時に 0 まで落ちていれば)

### 2.4 時系列動学の完全消失

- pulse_log には per-pulse のフル状態 (theta_*, R_*, delta_*, v11_m_c_*, capture など) があるが、cid ベクトル化では **lawfulness 軸の pulse 数のみ** 使用
- ESDE が「step ごとに状態が変わる」ことが本質的特徴 (Taka 指摘 2026-05-06) なのに、それは構造ベクトルから完全に消えている

---

## 3. 各 finding への影響

ベースライン解析の結果 (`v106_baseline_run_report.md`) を時間軸混在 caveat の観点で再解釈:

### 3.1 BOD/PER の正の z-score (above_baseline) — 影響少

身体部位 (eye/ear/mouth/face/head/hand/hip) と五感 (taste/smell/see/hear/...) は **run 集約や終了スナップショットでも安定的に出る軸** (cid の n_core / disposition / pulse 構成の組み合わせで反映される)。**時間軸混在の影響を受けにくく、本 finding は信頼できる**。

### 3.2 TIM.moment が観察値 < uniform baseline — 影響大

「moment (瞬間)」を表現したい cid は **誕生直後の短時間でアクティブ** だったはずだが、現状の cid ベクトルは run 集約 + 終了スナップショットを取るため **「瞬間」の特徴は集約過程で薄まる**。Atom.moment の 48 軸プロファイルは temporal.emergence/indication が高い (= 瞬間性) だが、cid 側はそれと対応する「特定 step での瞬間状態」を持たない。
→ TIM.moment の z-score は **時間軸混在による下方バイアス** の可能性が高い。本来の動学観察ベクトルなら正の z-score を取る可能性あり。

### 3.3 ACT.destroy の z-23.68 (shuffled) — 影響大

「破壊」は **1 step 内で発生する出来事**。ESDE では event ログ (ingestion / reap / ghost 化) で **間接的に「破壊された側」のみ** 記録される。reaped cid 自身が「破壊した」を表現する軸は構造ベクトルに無い。
→ ACT.destroy の極端な負 z は **動学観察の欠如によるアーティファクト** の可能性が支配的。Genesis 系が本当に破壊概念を表現できないかは、**event ログを集約した accumulator 軸を加えないと判定できない**。

### 3.4 集団平均「全 cid 51% が CHG.begin」 — 影響中

CHG.begin の Atom プロファイルは temporal.emergence/indication が支配的 (= 始まり)。短寿命 cid (76% が n=2、89% が short-lived) は **誕生してすぐ集計対象になり、短期間の状態が run 集約値として固定** されるため、temporal 軸が emergence 寄りになり、結果として CHG.begin に近づく。
→ ベースライン解析で uniform z+6.12 / shuffled z+0.43 だったのは「軸内分布だけで決まる人工物」と判明済だが、根本原因はこの **「短寿命 cid の集約 = 誕生直後の偏った snapshot」** という時間軸混在の影響。

### 3.5 ハブ cid → COG.enlightenment / FND.timeless / EXS.being — 影響大

COG.enlightenment / FND.timeless の Atom プロファイルは temporal.permanence や resonance.essential が高い。長寿命 cid (lifespan ≥ 10000) のみが run 集約値で permanence/essential 寄りになる構造的特徴を持つ。
→ ハブ cid = long-lived cid という事実上の同義は、層化解析でも確認済。ベースライン解析でこれら atom が above_baseline でなく **hub-cid 内では顕著に出るが全 cid 平均では消える** という現象は、「ハブ cid の特殊性」と「全 cid の集約バイアス」の両方が絡み合っている。

### 3.6 真の構造的盲点 176 atom — 影響混在

|z|>2 で 24-seed 一貫の盲点群 (EMO 21 / PRP 19 / FND 14 / ACT 11 / SOC 11 / ...) は、以下 2 種混在:
- **(A) 真の構造的欠落**: ESDE が概念的に持たないもの (例: VAL.evil / VAL.sacred / LOG.unreason / FND.information / REL.together など、価値判断・論理性・関係性概念)
- **(B) 動学観察欠如アーティファクト**: 1 step 内の出来事や瞬間性概念 (例: ACT.destroy / TIM.now / TIM.past / EMO.fear のような瞬間的感情)

両者を区別するには動学観察軸 (window-by-window cid trajectory) が必要。現状は **両者が混在した盲点リスト** として記録される。

---

## 4. 結論: v10.6 結果の解釈確定

本 v10.6 の atom alignment 結果は:

**「ESDE Genesis 系 v10.5 の 25,000 step run 終了時点 + run 全体集約値で表現された cid 5,224 個と、Language 系 Atom 325 個のプロファイル間の cosine 類似度」** として解釈する。

特に以下の 4 点に注意:
1. **動学的 (step 単位) な ESDE の振る舞いは捕捉されていない**
2. **短寿命 cid (76%) は誕生直後の集約値が支配** → CHG.begin 集中の根本要因
3. **長寿命 cid (= ハブ cid) は 25,000 step 累積値が支配** → COG.enlightenment / FND.timeless 偏り
4. **瞬間性・瞬発性概念 atom (TIM.moment, ACT.destroy, EMO.fear, TIM.now/past など) は本ベクトル化では構造的に出にくい**

→ ベースライン解析の真の finding 223 atom (above 47 / below 176) は、このタイミング前提のもとでの finding。

→ BOD/PER の正の z-score は **時間軸混在の影響を受けにくく信頼できる finding**。

→ 動学観察を含めた解析は v10.6.1 (window 単位 cid trajectory) または v10.7 (関係構造と並列に時間軸) の射程。本 v10.6 では実施しない (Taka 判断 2026-05-06)。

---

## 5. 利用可能な時系列データ (今後の参考)

window 単位 cid trajectory を生成する場合に使える既存データ:

| ファイル | 粒度 | 内容 |
|---|---|---|
| `pulse/pulse_log_seed*.csv` | per-pulse | theta_*, R_*, delta_*, v11_b_gen, v11_m_c_*, capture |
| `balance/c_trajectory_seed*.csv` | window | C_at_window_end, Q_remaining_at_window_end |
| `selfread/v18_window_trajectory_seed*.csv` | window | v18_cognitive_gain, v_unified_*, theta_distance |
| `introspection/introspection_log_seed*.csv` | window | disposition 4 軸 + tags + state |
| `integration/alpha_lifecycle_log_seed*.csv` | per-event | α 加入・離脱の step ごとの event log |
| `audit/per_event_audit_seed*.csv` | per-event | Q spend / event 全件 |

これらを使えば cid 5,224 × ~50 windows = 約 26 万データポイントで cid trajectory が生成可能 (軽量)。実装は v10.7 以降に検討。

---

*以上、v10.6 時間軸混在 caveat。Taka 判断「処理軽く現状確定」(2026-05-06) を反映。*
