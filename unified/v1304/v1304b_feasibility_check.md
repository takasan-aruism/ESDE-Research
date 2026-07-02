# v1304b 実装可否チェック — feedback loop 最小実装（実コード突合・判定なし #12）

*作成*: 2026-07-03、Code A。**実装前の feasibility ゲート（実コード突合のみ・ループ smoke は未実施・read-only・物理非書込）。合意ゲート前で停止。**
*対象設計*: v1304b 設計 rev2（Web Claude・2026-07-03・feedback loop 最小実装／子世界をセンターの観察 scope に足す）。
*成果物*: 本報告のみ（実装未着手・§3 の設計判断を Taka/Web Claude 合意待ち）。
*突合対象コード*: `v1304a_stage3b.py`（composition①機構）・`v1304a_probe.py`（動的珍しさ②式）・`v1304a_smoke.py`（`signature`/`tbin`/`FORMAL_EYES`）・`v1303_final_attention_output_seed0.parquet`（初期 weight 源）。

---

## 0. 結論（先に）

- **強い再利用性**：v1304b が要る3部品のうち **①composition と ②動的珍しさは既存コードにそのまま在る**。①＝`stage3b.run_child(plb,seed)`＋`weights()`＋provenance 配列 `gw[g][j]`、②＝`probe.dyn_rarity_lift`（両側 −log10・floor `1/(2n)`）を子集団に適用。engine 自走は Stage3b で 7200 child 実走行済（feasibility は確立済）。
- **③更新則（唯一の新要素）は薄い派生で組める**が、実装ブロッカーが **1 点だけ**ある＝**M（draw あたり子数）< support(45) で毎 round 大半の cid が 0 子になり、乗法更新 `weight×(child_salience の cid 平均)^g` が未定義**（§3）。これは null の効き方も左右するため、実装前に Taka/Web Claude 合意が要る（v1304a の「写像形」と同格の唯一判断）。
- **timing**：Stage3b 実測 **0.915s/child**（N=150・300step・単スレッド）。smoke 規模（R5×T5×3群×M20＝1500 child）＝ **serial ≈ 23 分**。round は逐次依存だが round 内 M 子は並列化余地あり（§4.3）。
- 規律確認：親物理 read-only・書込 `unified/v1304/` 配下・group 間 seed match は Stage3b が既に満たす実装形（`eng_seeds` matched・`OUT` 限定書込）＝そのまま継承可（§5）。

## 1. §6 各項目の実機回答

| # | §6 の確認要請 | 判定 | 根拠（実コード） |
|---|---|---|---|
| 1 | ループ状態管理（weight round 持ち回り・child↔cid 由来対応）が Stage3b 派生で組めるか | **可** | 由来対応は Stage3b `gw[g][j]=crng.choice(support,size=M,p=weights)` が既に「各子のサンプル元 cid」を保持。weight の round 持ち回りは `weights()` の静的 lift を **round 間で更新される可変 state** に差し替えるだけ（in-memory・親非書込） |
| 2 | 子署名の per-round 珍しさ化（probe dyn_rarity と同式を子集団に）の実装 | **可** | `probe.dyn_rarity_lift` の両側 tail `two=(2·min(pct,1−pct)).clip(lower=1/(2n))`・`−log10(two)` を、round ごとの M 子の `signature()[link_density]` 分布に適用するだけ。式・floor そのまま流用（研究者ノブなし） |
| 3 | smoke 規模（M20×3群×R5×T5×300step）の所要 | **可（≈23分 serial）** | Stage3b 実測 6593s/7200child = **0.915s/child**（N=150・300step）。1500 child = **1373s ≈ 23分**（単スレッド）。round 内並列で短縮可（§4.3） |
| 4 | 親物理 read-only・書込 v1304 配下・group 間 seed match の維持 | **可** | Stage3b が既に：`eng_seeds=[BASE·1e7+r·1e4+j]` を群間 matched（paired）・書込は `OUT=unified/v1304/outputs` 限定・親 ledger/state 非書込。weight は in-memory state ゆえ親へ書かない |
| 5 | smoke 後停止・full/複数 lens/複数 g へ自動前進しない | 遵守 | feasibility は本報告のみ・smoke 未実施。合意後に smoke→停止→承認待ち（[[feedback_smoke_then_pause]]） |

## 2. Stage3b / probe → v1304b 再利用マップ

| v1304b が要る物 | 既存コードの既存物 | 差分 |
|---|---|---|
| ①composition（weight 比例で M 体サンプル・各子 plb←s_avg） | `stage3b.weights()`＋`run_child(plb,seed)`＋`gw=crng.choice(support,p=w)` | weight を静的 lift → 可変 state に。plb←s_avg 写像（`plb=0.007(1+0.15tanh(z))`）そのまま |
| child↔cid 由来対応 | `gw[g][j]`（サンプル元 cid 配列） | そのまま（provenance は既に在る） |
| ②子集団内の珍しさ（両側 −log10・単一 lens） | `probe.dyn_rarity_lift`（両側 tail・floor・`−log10`） | 適用先を「per-(cid,t) ledger」→「round の M 子 signature」に差し替え。lens=`link_density` 1本（`signature()` が返す） |
| ③更新則 weight←weight×(salience 平均)^g・再正規化 | **（無し・唯一の新要素）** | 新規。g 事前固定（1 primary/0.5 参考）・eps floor・再正規化。§3 の 0 子 cid 規則が要決定 |
| 初期 weight＝now_theta lift（45 支持） | schema `now_theta` の `p_select·eligible_count` を cid 集約（Stage3b `lift_elig`） | そのまま（now_theta は FORMAL_EYES・schema 両方に存在） |
| null 3群（feedback / no-feedback / shuffle-feedback） | Stage3b の canon/parent/shuffle 群構造・paired seed | shuffle-feedback＝child_salience を cid 間 shuffle（更新則は Stage3b の shuffle と同思想＝量保持・対応破壊） |
| 統計（R リサンプル・paired・Holm・base 2系列） | `stage3b.contrast()`＋`ttest_1samp`＋Holm＋`BASE` 2系列 | primary contrast を parent−shuffle → **feedback−shuffle の weight 軌跡距離**に。型そのまま |
| raw と rank 両保存（§7.1） | schema に `salience_raw` / `salience_pct_or_norm` 前例 | 子側 salience も raw と rank を両ログ（小改修） |

## 3. 唯一の設計判断（実装前に Taka/Web Claude 合意が要る）

**M（draw あたり子数）< support(45) ゆえ、毎 round に大半の cid が 0 子になり、乗法更新 `weight[cid] ← weight[cid] × (child_salience の cid 平均)^g` が 0 子 cid で未定義。**

- smoke 規模 M=20 で 45 support から **復元抽出**すると、1 round で子を持つ distinct cid は最大 ~20（実質 ≤17 程度）＝**残り ≥25 cid は salience 平均が空**。
- これは §7.2 の eps floor（salience の下限）とは**別の穴**：eps floor は「子が有るが salience が極小」を救うが、「そもそも子が無い」cid の更新則は未定。
- 実装可能な候補（Code A が確認・**採否は委ねる**）：
  - **候補 α（不動）**：0 子 cid は weight を据え置き（更新 factor=1）。実装最小・但し weight 上昇は「今 round 引かれた cid」のみに偏り、引かれ運の交絡が入る。
  - **候補 β（M を support 被覆へ）**：M ≥ support(45) にして毎 round 全 cid が期待的に子を持つ。交絡は減るが子数増（M45 なら smoke 1500→3375 child ≈52分）。
  - **候補 γ（round 内で weight を「サンプル確率」でなく「全 cid 一括評価」に）**：M 体を weight 比例で引くのでなく、全 support cid を各 round 1 体ずつ回して salience を全 cid に定義（M=support 固定・引き運の交絡なし）。最も交絡が小さいが「weight 比例サンプル」という設計①の形からは外れる（重みは salience にのみ効かせ、抽出は一様）。
- **null への波及**：shuffle-feedback は「child_salience を cid 間 shuffle」だが、0 子 cid が有ると shuffle 対象集合が round ごとに変わる＝shuffle の定義が候補 α/β/γ で変わる。**写像（0 子規則）を決めれば null も自動的に決まる**（v1304a と同構造）。

> Code A の所見（判定でない）：交絡最小は γ、設計①（weight 比例サンプル）の字義に忠実なのは α。β は中間で最も重い。smoke は「ループが回るか」の確認ゆえ α でも feasibility は言えるが、**§4.2 の primary（feedback−shuffle の weight 軌跡距離）を意味あるものにするには 0 子 cid の扱いが結果を左右する**ため、full 前に確定必須。

## 4. 交絡・規律の実機確認

### 4.1 循環（#CW7）・feedback write-back（v1302）
- 設計は **feedback＝物理 write-back でない**（子世界をセンターの観察 scope に足す）＝[[project_v12_experience_is_v97_pattern.md]] の「親物理へ書かない」線を維持。weight は in-memory state で親 ledger/state に触れない（Stage3b `run_child` は engine を都度新規構築・親非参照）。
- #CW7（作ったものを観測軸にする循環）：設計 §4-2 が「センターが子に注意した＝作りだから自明・非自明は shuffle との差だけ」と正しく分離。Code A は **成果候補を feedback−shuffle 差に限る**という設計の線を実装で担保できることを確認（Stage3b の 3群 paired 構造がそのまま使える）。

### 4.2 primary の事前固定（A型・単一指標）
- 設計 primary＝**feedback−shuffle の weight 軌跡距離**を事前固定・Holm・base 2系列＝Stage3b の統計型（`ttest_1samp`＋Holm＋BASE 2系列）を踏襲。gain g は事前固定2値（1/0.5）。**単一指標分類でない**（軌跡分岐・由来対応・揺れ・子集団応答の4レンズを並行観察・判定は Taka＝[[feedback_no_single_index_classification]]）。
- no-feedback は §7.3 どおり **参照群に降格**（weight 不動ゆえ差は定義上自明・成果判定に使わない）を実装で担保。

### 4.3 timing 精査（§6-3 の根拠）
- Stage3b 実測：7200 child / 6593s（base0）・6614s（base1）＝**0.915s/child**（N=150・300step・単スレッド）。
- v1304b smoke（M20×3群×R5×T5・単一 eye now_theta・g=1・lens link_density・base0）＝ **1500 child ≈ 1373s ≈ 23分**（serial）。
- round は逐次依存（weight[t+1] が weight[t] を要る）だが **round 内の M×3群 子は独立＝並列化余地**。候補 β（M45）なら 3375 child ≈52分。full（複数 g・複数 lens・base2）は Stage3b 級（~1.8h/base）に戻る。→ smoke は serial で許容内、full 前に並列化を検討。

### 4.4 その他規律
- **空 start 交絡なし**：`run_child` は `eng.run_injection()` を呼ぶ（stage3b.py:62）＝[[feedback_transplant_skip_injection_confound]] の injection skip 空 start を踏まない。
- **言い換え再実装でない**：③更新則は Stage3b/probe/仕様書に既存の機構でない（composition・珍しさは既存だが「珍しさを weight に乗法 feedback して次 round の composition を変える」ループは新規）＝[[feedback_no_reworded_reimplementation]] 照合で同型重複でないことを確認。ただし v1114（Center pull）・B_Gen（−log10）・A型（更新則ノブ）の思想の合成である点は設計 §自己規律①が既引用。

## 5. 本チェックで走らせていないもの（実装でない）

- v1304b のループ実験 run（weight 更新・3群 T rounds・軌跡距離・揺れ測定）は **一切していない**。
- ループ smoke（M20×R5×T5×3群）も **未実施**（合意後）。
- 実施したのは既存コード（stage3b.py / probe.py / smoke.py）と schema/summary の **read-only 突合と timing 算定のみ**。新 run・新 ledger・ファイル生成（本報告以外）なし。

## 6. 次段（Code A は判定しない・委ねる）

実装前に Taka/Web Claude 合意が要る：**§3 の 0 子 cid 更新則（候補 α 不動 / β M≥support / γ 全 cid 一様抽出＋weight は salience にのみ）＋ それに連動する shuffle-feedback null の定義**。合意後に v1304b 実装（stage3b.py 派生・now_theta 初期 weight・composition①そのまま・②probe 式・③更新則・null3群・raw/rank 両保存・eps floor・round0 support ログ固定 §7.4）→ seed0 smoke（停止成功条件6点 §7.5）→ 停止。軌跡の読み・揺れの判定・次段（回数増/多 eye/Atom 接続）は Taka。

## 7. 一文サマリ

v1304b 実装可否チェック（実コード突合・ループ smoke 未実施・判定なし #12）── feedback loop 最小実装の3部品のうち **①composition（`stage3b.run_child`＋`weights`＋provenance 配列 `gw[g][j]`）と ②子集団内の動的珍しさ（`probe.dyn_rarity_lift` の両側 −log10・floor `1/(2n)` を round の M 子 `signature[link_density]` に適用）は既存コードにそのまま在り**、engine 自走は Stage3b で 7200child 実走行済（0.915s/child・N150・300step）ゆえ smoke 規模 1500child≈23分 serial で許容内、初期 weight＝now_theta lift は FORMAL_EYES・v1303 schema 両方に存在、親物理 read-only・書込 `unified/v1304/` 配下・群間 seed match は Stage3b が既に満たす実装形ゆえ継承可、**③更新則（weight×(salience 平均)^g・唯一の新要素）は薄い派生で組めるが実装ブロッカー1点＝M(20)<support(45) で毎 round 大半の cid が 0 子になり乗法更新が未定義**（候補 α 不動/β M≥support/γ 全 cid 一様抽出＋weight は salience のみ・eps floor は「子が有るが極小」を救うが「子が無い」cid は別穴・null shuffle-feedback の定義も 0 子規則で変わる＝写像決めれば null 自動決定）で v1304a の「写像形」と同格の唯一判断ゆえ実装前に Taka/Web Claude 合意が要る、交絡確認＝feedback は物理 write-back でなく観察 scope 追加で親非書込（#CW7 は feedback−shuffle 差のみ成果・no-feedback は参照群降格）・run_injection 呼ぶゆえ空 start 交絡なし・言い換え再実装でない（珍しさを weight に乗法 feedback するループは新規）、実施は read-only 突合と timing 算定のみで実験 run/smoke/実装は未着手、0 子規則＋null 定義を合意後に stage3b.py 派生で実装→seed0 smoke（停止成功条件6点）→停止、軌跡の読み・揺れ・次段は Taka。
