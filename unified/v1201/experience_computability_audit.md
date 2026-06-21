# v12 Atomset — 経験(特徴度ベース一致率更新)の計算可能性 監査

日付: 2026-06-11 / **調査のみ。M5 実装に入っていない。** / 担当: Code A
対象: Taka 案「新しい一致率 = 元の一致率 ×(1 + 特徴度)」の計算可能性を実コード・実データで確認
根拠データ: `developmental/v107/outputs/smoke/source_events_seed0.parquet`(14385 events / 228 CID)、
`developmental/v101/diag_v101_main/ingestion/ingestion_events_seed0.csv`、`m4_first_divergence` の per-CID tag。
再現器: `experience_computability_audit.py`(新 run を回さず既存ログのみ読む)。

> **⚠️ Rev1 訂正済(2026-06-11、Taka/Web Claude 指摘)。** 下記 §0〜§5 は **Rev1=smoke seed0 のみ + ingestion(完食)チャネルだけ** を見た判定で、「出会い系は 7%・枯渇・主柱になれない」は **二重の誤り**。本番 24 seeds + 正しいチャネル(E3_contact)で取り直した結論は **§6 (Rev2)** にある。要点: **出会い系(E3_contact)は全 CID の ~84% で σ 定義可能 = 自己系と並ぶ柱になれる。** Rev1 の格下げは撤回。

---

## 0. 結論(先に・正直に)【Rev1=要訂正、§6 参照】

| 確認項目 | 自己系 (pulse/α/β/c_conv) | 出会い系 (ingestion/contact) |
|---|---|---|
| (1) per-CID 過去の平均・分散が蓄積できるか | **✅ 取れる。pulse が全 228 CID に 10〜500 サンプル(中央値 20)** | **⚠️ 原理上は取れるが激しくデータ不足。228 CID 中 173 は一度も出会わない。蓄積≥3 は 16 CID(7%)のみ** |
| (2) 特徴度 \|x−μ\|/σ が壊れないか | **✅ pulse 経由なら全 CID で σ 健全**(α/β/c_conv 単体は疎で要 fallback) | **❌ そのままでは壊れる。出会う 55 CID の 30 が「ちょうど 1 回」=σ 未定義** |
| (3) 一致率を ×(1+特徴度) で更新・保持できるか | **✅ 機構は自明**(label/cog の per-CID dict に置けば反復・永続可) | 同左。ただし両系共通の**安定性の壁あり**(後述 §3) |
| (4) イベント直前の凍結 snapshot で計算できるか | **✅ 既に在る。v107 が per-event の `*_pre` を記録済**(R_familiarity_pre/Q_pre/C_pre/n_alphas_pre/n_observed_pre/lifespan_so_far) | 同左。相手は ghost(host-loss 時点で凍結)なので本質的に pre-event |

**総括**: 自己系は**ほぼ完全に計算可能**(既存ログだけで post-process 検証まで可能)。
出会い系は**相手の特定は可能だが(audit B.2 は方向は正しく、ファイル経路だけ誤り)、サンプルが構造的に枯渇**しており、特徴度を定義できる CID は 7% に留まる。
バラつきゼロは**実在する深刻な問題**で、Taka が先回りした安全策(記録が浅いうちは特徴度=0=一致率を動かさない)が**必須**。
さらに ×(1+特徴度) の反復には**頻度が裏口から復活する**安定性問題があり(§3)、これが M4 の near-universal を別形で再発させる最大のリスク。

---

## 1. per-CID 過去蓄積(平均・分散)— system 別の実測

`experience_computability_audit.py` 出力(smoke seed0):

```
system/type         total  CIDs>=1  CIDs==1  CIDs<=2  CIDs>=3
pulse               12530      228        0        0      228   ← 自己系の主柱、全 CID 健全
alpha_formation      1067      129       27       46       83
beta_formation        478      129       60       85       44
c_conversion          155       55       30       39       16
ingestion             155       55       30       39       16   ← 出会い系、激しく疎
```
- **自己系**: 蓄積≥3 = **228/228**。pulse は最小でも 1 CID 10 回。平均・分散は全 living CID で安定に取れる。
- **出会い系**: 蓄積≥3 = **16/228(7%)**。**173 CID は ingestion ゼロ**(出会い系の特徴度が原理的に未定義)。出会う 55 CID も 30 が 1 回・39 が ≤2 回。

### 1.1 相手 CID の特定可能性(audit B.2 を実データで訂正)
前回 audit B.2 は「ghost_cid は `ingestion_events_seed*.csv` に在る」とした。**ファイル経路は誤り**(v107 `source_events` には `source_cid` だけで partner 列なし。`ingestion_events_seed*.csv` という名のファイルも v107 側に無い)。だが**主張の中身は正しい**:
- 実コード `v105_memory_readout.py:762` `attempt_ingestion(self, observer_cid, ghost_cid, ledger)` が **eater↔相手の CID ペアを引数で持つ**。
- `SubjectLayer._ingestion_log`(`:521`)が `{step, observer, ghost, ...}` を **live で逐次記録**。
- 実出力 `developmental/v101/.../ingestion_events_seed0.csv` の列 = `observer_cid, ghost_cid, link_id, ...`(**相手 CID も link も記録済**、152 行)。
- 相手は ghost(host-loss で inert 化・履歴は保持 `:544`)→ **相手の cid_vec は host-loss 時点で凍結された値で再構築可能**。

→ **出会い相手の特定と相手ベクトルの再構築は可能**。ただし v107 の event 表は partner を落としているので、特徴度を出すには v101 ingestion ログ(observer/ghost)を join するか、M5 で partner を記帳に足す必要がある。

### 1.2 自己ベクトルの「動き」の計算可能性
自己系の「今回の値」= `dist(current_self_vec, historical_self_vec)`。cid_vec の入力は live に揃う:
- live で取れる(M2/M4 が既に読んでいる): lifespan(`born_at`)、n_core(`label['nodes']`)、pulse(`v10_pulse_count`)、C、α/β membership、q_remaining(ledger)。
- v107 が per-event 既算出(= 取れる証拠): `R_familiarity_pre / Q_pre / C_pre / n_alphas_pre / n_observed_pre`。
- 要 live 配線 or 簡略化: symmetry 軸の v99 drift、value_generation の一部(q_spent, β受領)。**全 48 次元を使わず縮約ベクトルでも可**(設計判断、計算可能性の壁ではない)。

**留保(quantization)**: v106 cid_vec は 10 軸中 ~6 軸が gradient bucket / one-hot(audit A.1)。bucket 軸は**境界を跨いだ時だけ跳ぶ**ので、自己移動距離は「ほぼ 0 → たまに跳躍」のゼロ膨張になりやすい。連続軸(ontological/value_generation/experience/symmetry の単体正規化)は滑らかに動く(C_pre/R_familiarity_pre の実トラジェクトリで確認済み)。→ 自己距離は連続軸主体で測るのが安全。

---

## 2. 特徴度 \|x−μ\|/σ の zero-variance 問題(核心)

**実在し、深刻。** Taka の懸念は実データで裏付けられた。
- **出会い系**: σ を定義できるのは 16/228 CID(7%)のみ。30 CID は 1 回きり(σ 未定義)、173 CID は 0 回。**そのままでは大半で割り算が成立しない。**
- **自己系(pulse)**: σ は全 CID 健全(≥10 サンプル)。問題は**各 CID の最初の 1〜2 イベント**(履歴ゼロ→σ 未定義)と、α/β/c_conv 単体の疎さ。
- **bucket quantization 由来の σ≈0**: 自己移動が「0 の山+稀な跳躍」になると σ がほぼ 0 になり、跳躍 1 個が見かけ上 ∞σ の外れ値になる(偽の巨大特徴度)。

### 安全策(Taka 案を採るなら必須・要設計確定)
1. **記録が浅いうちは特徴度=0**(Taka 案そのまま): per-CID per-system のサンプル数 `n < k`(例 k=3)なら特徴度=0=一致率を動かさない。**これが無いと 7〜100% の CID で NaN/暴発。**
2. **σ 下限(floor)**: `σ_eff = max(σ, σ_min)`。bucket quantization と若年 CID の σ≈0 を両方守る。Welford でオンライン平均・分散(pre-event 更新)。
3. **特徴度の clip**: `z = clip(|x−μ|/σ_eff, 0, z_max)`(例 z_max=3)。単発の桁外れで一致率が吹っ飛ぶのを防ぐ(§3 と直結)。
4. **出会い系は「保留にしない」が、データが無いものは 0**: 出会わない 173 CID は出会い系特徴度=0(忘却ではなく「出会っていないだけ」)。自己系で個性化を担う設計が現実的。

---

## 3. 一致率の更新・保持(×(1+特徴度) の反復)と安定性の壁

- **機構は自明**: M2 の `label['atomset_bonus']`(scalar、per-CID 永続)を `match_rate` に置換し、イベントごとに `match_rate *= (1 + z)` するだけ。**ghost を跨いで永続させるなら label でなく cog の per-cid dict に置く**(ghost 化で `current_lid[cid]=None`、label↔cid リンクが切れるため。cog データは保持される `:544`)。反復・保持は問題なし。
- **⚠️ 最大のリスク=頻度の裏口復活**: `×(1+z)` を**イベント数だけ反復**するので、典型イベントでも z>0 が少しでも残ると、cid0(32 イベント)は 32 回・pulse 500 回の CID は 500 回掛かり、**「忙しい CID が勝つ」= M4 の near-universal が乗算形で再発**する。
  - 設計の肝は「**典型イベントは特徴度≒0(×1=不動)、外れイベントだけ一致率を動かす**」を**実際に成立させる**こと。これは「z の分布が本当に 0 中心か」に懸かる(平均を引く定義なので構造的には 0 中心のはずだが、σ floor と quantization でバイアスが残ると frequency が漏れる)。
  - 対策候補: **閾値更新**(\|z\|>z_thr のイベントだけ更新、それ以下は完全に ×1)/ **log 空間で加算**(`log_rate += log(1+z)`、減衰付き)/ z の符号を残す(平均超え=+、平均未満=−)で平均回帰させる。**ここは M5 設計で要確定。**

---

## 4. pre-event 凍結 snapshot(GPT 指摘への回答)

- **既に存在する**。v107 `attach_pre_event_state` が per-event で `*_pre`(merge_asof backward = イベント時刻以前の状態)を添付済み: `R_familiarity_pre / Q_pre / C_pre / n_alphas_pre / n_observed_pre / lifespan_so_far / n_core_member`。実トラジェクトリも確認(CID0 の C_pre = [16,41,27,...]、lifespan_so_far = [1,50,100,...])。
- live 実装では M2/M4 が既に持つ「last-chunk の状態キャッシュ」(delta 検出用 `last_*`)を pre-event snapshot として流用すればよい。**イベント後ベクトルの混入は回避可能。**
- **⚠️ 留保(window 粒度)**: cid_vec 入力の一部は window 末値(`C_at_window_end`, `Q_remaining_at_window_end`)で**window 内では更新されない**。同一 window 内の event では pre/post がこれらの軸で同値になりうる。per-step 軸(lifespan, pulse)は問題なし。→ 時間分解能は window 粒度が下限。

---

## 5. M5 に入る前に Web Claude / Taka へ返す論点(実装はしない)

1. **個性化の主柱は自己系に置くのが現実的**(出会い系は 7% の CID しか特徴度を持てない、構造的データ不足)。出会い系は「在れば加点、無ければ 0(保留せず動かさない)」の従。
2. **zero-variance 安全策 4 点(§2)は必須**。特に「n<k で特徴度=0」(Taka 案)は採用前提。σ floor・z clip・Welford pre-event も要確定。
3. **頻度の裏口復活(§3)が今回の核心リスク**。`×(1+z)` を全イベントに掛けると M4 の near-universal が乗算で再発する。**「典型イベント=×1、外れだけ動く」を閾値更新 or log 空間 or 符号付き(平均回帰)で担保**するのが M5 設計の中心。
4. **自己ベクトルは連続軸主体で**(bucket quantization の偽外れ値回避)。全 48 次元か縮約かは別途。
5. **出会い系を入れるなら partner を記帳に追加**(v107 event 表は partner を落としている。v101 observer/ghost を join するか M5 で記帳)。
6. **検証は新 run 前に post-process で先行可能**: 自己系の z 分布・一致率トラジェクトリは**既存 v107 `*_pre` 列だけで試算でき**、頻度漏れ(§3)が起きるかを安く先に見られる。

---

## 6. Rev2 — 本番スケール再監査(Taka/Web Claude 指摘を受け、出会い系の格下げを撤回)

日付: 2026-06-11 / トリガ: Taka/Web Claude「出会い系の『7%・枯渇』は smoke が短いせいで本来構造でない。本番では出会い(特に摂食的接触)が主流」。
再計算: 本番 24 seeds(window 500 × tracking 50 = 25,000 step、N=5,224)の既存ログ。再現器に `--rev2` を追加。

### 6.1 Rev1 の誤りは二重(率直に)
1. **seed0 一本で判定した**(§1 は 1 seed)。本番は 24 seeds 集計で見るべき。
2. **出会い系を「ingestion(完食)」一チャネルに矮小化した**。実際は **出会い系に 2 チャネル**ある:
   - **E3_contact(出会った=物理リンク共有の初回接触)= 100,432 件/24seeds、dense。** これが「出会い」。`primitive/v917/diag_v917_main/selfread/other_records_seed*.csv`(cid_id, other_cid_id)。
   - **ingestion(食べた=完食)= 3,588 件、sparse。E3 接触の 7.4% しか完食に至らない。** Rev1 が誤って唯一の出会いと見なしたチャネル。
   - (出典: `primitive/v917/v917_stage4_result.md:46,242`、`developmental/v101/v101_minimal_ingestion_result.md:109,203`)

### 6.2 本番 24 seeds 実測 — σ 定義可能(per-CID ≥3 サンプル)率
| チャネル | σ 定義可能 CID 率 | per-CID 分布 | 判定 |
|---|---|---|---|
| **E3_contact(出会い、正しいチャネル)** | **4,398/5,124 = 85.8%(接触 CID 中)≈ 全 CID の 84%** | contacts/CID: min1 / **中央値6** / 平均19.6 / max159、distinct partner も同数 | **柱になれる** |
| ingestion(完食、Rev1 の誤チャネル) | 499/5,224 = **9.6%** | sparse | 従(完食は稀) |
| pulse(自己) | **5,224/5,224 = 100%** | 全 CID ~500 | 柱 |
| α/β/c_conv(自己の副) | 39〜68% | 中疎 | 補助 |

→ **出会い系(E3_contact)は全 CID の ~84% で平均・分散が取れる。自己系と並ぶ「両方を柱に」が本番では成立。Rev1 の「出会いは主柱になれない・自己系を主柱に」は撤回。** distinct partner 数 = contact 数(other_records は unique pair 初回接触を記録)なので、**per-CID の partner-距離分布が 84% の CID で定義可能** = 出会い系特徴度が大半の CID で計算できる。

### 6.3 なぜ smoke で「枯渇」に見えたか(tracking 長依存)
`v917_stage4_result.md:242`: **片方向発火(摂食的接触)率 = smoke(tracking10) 25.6% → 本番(tracking50) 77.0%**(ghost が時間で累積し片方向接触が主流化)。smoke 5 window は **出会いが始まる前の最初期**。→ **per-CID 蓄積を smoke で見て「枯渇」と判定してはいけない**(Taka 指摘を採用、規律化)。Taka の従来整理「ESDE の主流は対話でなく摂食」と整合。

### 6.4 zero-variance 安全策(本番でも必要、ただし意味が変わる)
- 本番では「大半の CID でデータ不足」ではない(84〜100% で σ 定義可能)。**残る問題は『立ち上がり』のみ**: どの CID も最初の 1〜2 接触/pulse は履歴ゼロ、E3_contact <3 の 14% の CID、α/β/c_conv の疎な部分。
- → **「記録が浅いうちは特徴度=0(一致率を動かさない)」は両系で必要**(Taka 指摘どおり、枯渇対策でなく最初期対策として)。σ floor・z clip・Welford pre-event も据え置き。

### 6.5 §3「頻度の裏口」リスクを本番で再評価(撤回せず、むしろ強化)
- **自己(pulse)**: 全 CID が ~500 回更新で均一 → **CID 間の頻度差バイアスは小**。だが 500 回の累乗で **magnitude 暴走**(全体一様)→ bound 必須。
- **出会い(E3_contact)**: per-CID 1〜159 と**広い**(max/中央値 ≈ 26 倍)→ `×(1+z)` を接触数だけ掛けると **159 回更新の CID が 6 回の CID を大きく圧倒 = M4 の near-universal が「接触頻度」経由で再発**。
- → **§3 対策(典型イベント=×1・外れだけ動く / 閾値更新 / log 空間 / 符号付き平均回帰)は本番でも必須、特に出会い系で重要。** これは Rev1 から不変、むしろ本番の広い接触分布で深刻度が増す。

### 6.6 計算可能性 確定(本番)
1. **per-CID 過去蓄積**: 自己 ○(100%)、**出会い ○(84%、E3_contact)**。Rev1 の出会い × は誤り。
2. **特徴度 \|x−μ\|/σ**: 両系で σ 定義可能(立ち上がり対策のみ要)。「n<k で特徴度=0」採用前提。
3. **更新・保持**: 自明。本番出会い系での §3 calibration が最重要設計点。
4. **pre-event snapshot**: 既存。自己=v107 `*_pre`、出会い=partner は ghost(host-loss 時点で凍結)+ `bidirectional_e3_log` に接触時点の partner 状態(ncore/phase/s_avg/r_core/q/c)が記録済 → **partner ベクトルは接触時点 snapshot で再構築可**。

### 6.7 留保(M5 設計判断へ)
- **E3_contact を live で M5 に流せるか**: 接触検知は engine 内に在り(v105 は `v917_a_observer`=`CidSelfBuffer.other_records` を import 済、E3 onset が leakage を駆動)、partner(`other_cid_id`)も記録される。**post-hoc では完全に取得済**、live 配線は要確認だが壁は低い。
- **出会い event の定義**: 「出会い」= E3_contact(接触、片方向=摂食的接触を含む)を採るのが Taka framing と本番データに整合。ingestion(完食)はその稀な部分集合。**どちらを match-rate 更新トリガにするかは設計判断**(接触=dense で個性化圧、完食=rare で強い意味)。
- **次アクション**: 自己系 z 分布・一致率トラジェクトリ・§3 頻度漏れの試算は **既存 v107 `*_pre` + v917 `other_records` だけで新 run なしに post-process 先行可能**。M5 実装は Web Claude/Taka 判断後。

## ファイル
- `experience_computability_audit.py`(再現器、`--rev2` で本番 24 seeds 集計、新 run なし)/ `experience_computability_audit.md`(本書)
- 参照: `projection_audit_report.md`(§B match 定義)、`m4_report.md`(near-universal)、`m2_smoke.py`(現 atomset_bonus 機構)
- 実コード: `developmental/v105/v105_memory_readout.py:762`(`attempt_ingestion`)/`:521`(`_ingestion_log`)、
  `developmental/v106/v106_event_trajectory.py:235`(`build_event_cid_vector`)、`developmental/v107/v107_event_aggregator.py`(`*_pre`)
