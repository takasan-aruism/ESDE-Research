# v1304b smoke 報告 — feedback loop 最小実装（実装健全性・ログ完全性のみ・判定なし #12）

*作成*: 2026-07-03、Code A。**smoke ＝実装が回るかの確認。統計判定しない（設計 §7c-4）。read-only・親物理非書込・書込 `unified/v1304/outputs/` 配下・seed0・base0・g=1・lens=link_density のみ。承認後 full へ自動前進しない（[[feedback_smoke_then_pause]]）。**
*対象設計*: v1304b rev4（Web Claude・2026-07-03・0子規則 α＋round正規化 確定 / cid単位平均・L1 primary・smoke は健全性のみ）。
*成果物*: `v1304b_smoke.py` + `outputs/v1304b_smoke_{weights,salience,coverage,childsig,primary,summary}_seed0_base0.{parquet,json}`。
*規模*: R5×T5×M20×2群自走＝**1000 child**（feedback 500 + no_feedback 500・shuffle は feedback の世界に相乗り）・**909秒**（0.91s/child・単スレッド）。

---

## 0. 結論（先に）

- **停止成功条件6点すべて OK**（§1）＝ループ実装が回った・weight 軌跡が保存された・3群が同 seed 条件で比較可能になった。**これが smoke の言える上限**（「反応成立」と言わない・[[feedback_no_single_index_classification]]）。
- 実装で1点、設計文の解釈を固定した（§4）：**shuffle-feedback は feedback の世界に相乗り**（同一 drawn/子/salience・正規化前 salience を drawn cid 間で permute＝対応のみ破壊）。これが設計の「更新量の分布が完全一致で対応のみ異なる null」を字義的に満たす読み。独立 composition を意図なら1行切替可（§4・Web Claude 確認事項）。
- descriptive な事実（**判定でない・単一 base seed0・統計なし**）：feedback は round を追って weight を集中させ（entropy 3.64→2.76）、**shuffle より強く集中**（t4 entropy 2.76 vs 3.23・max weight 0.286 vs 0.151）。primary L1(fb,shuffle) は 0.35→1.27 と単調増で全 round no_feedback 参照を上回った。＝**「差が観測された」までで停止**。real/artifact・揺れの読み・g/base 依存は Taka（§5）。

## 1. 停止成功条件6点（§7-5・実装健全性）

| # | 条件 | 結果 | 根拠 |
|---|---|---|---|
| i | 全 round・全群で child 生成 | **OK** | childsig 行数 = R·T·2 = 50・salience 行数 = R·T·M = 500。feedback/no_feedback が全 (r,t) で M 子自走・shuffle は feedback の世界を共有 |
| ii | cid provenance 欠落なし | **OK** | salience の drawn_cid 全非欠損（500/500） |
| iii | feedback/shuffle の seed matching 一致 | **OK** | shuffle は feedback の drawn/子/salience を相乗り＝定義上完全一致（§4） |
| iv | weight が NaN/全消滅しない | **OK** | 全 weight 非 NaN・各 (r,t,group) の Σweight=1（誤差<1e-9）・最集中でも max weight 0.286（1cid 独占なし） |
| v | parent physics hash 不変 | **OK** | PS(`4360e79a…`)・SCHEMA(`e6c17b4d…`）が run 前後で不変＝親物理 read-only 実証 |
| vi | 書込が v1304 配下のみ | **OK** | 全出力先 `OUT = unified/v1304/outputs`・親 ledger/state/inject 非書込 |

`all_pass = true`（summary json）。

## 2. 実装＝設計部品の対応（何を既存流用し・何が新規か）

| 設計部品 | 実装 | 出所 |
|---|---|---|
| ①composition（weight比例 M体sample・plb←s_avg） | `choice(support, M, p=weight)` + `run_child(plb)` | stage3b 機構そのまま |
| ②子集団内の珍しさ（両側−log10・floor 1/(2n)） | `rarity()`（`2·min(pct,1−pct)` clip `1/(2M)`・`−log10`） | probe `dyn_rarity_lift` 同式・適用先を「M子の link_density」に |
| ③更新則（唯一の新要素・rev4） | `update_factor()`：cid単位平均→`factor=(cid_sal/round_mean)^g`・undrawn=1 | 新規（rev4 §7c-1 準拠） |
| eps floor（正規化前・cutoff でない） | `sal_eff = max(sal_raw, 1e-6)` | rev2 §7-2 |
| salience raw + rank 両保存 | salience parquet に raw/eff/rank 3列（rank は監査のみ・更新に混ぜない） | rev2 §7-1 / rev4 §7c-2 |
| 初期 weight = now_theta lift（45支持） | schema now_theta の eligible lift・reindex support・正規化 | 設計 §2 |
| null 3群 | feedback / no_feedback(round0固定) / shuffle(対応 permute) | 設計 §3 |
| primary = L1(feedback,shuffle) 軌跡距離 | `L1_fb_shuffle`・事前固定・算出のみ | rev4 §7c-3 |

## 3. descriptive な観察事実（判定でない・単一 seed0/base0/g=1・統計なし）

> 以下は「実装が何を出したか」の事実記録。real/artifact・有意性・一般化は**一切主張しない**（設計 §7c-4：smoke は統計判定しない）。

### 3.1 coverage（0子規則 α が効く場面が実在）
| round | drawn_distinct(平均) | undrawn_rate | round_mean_salience |
|---|---|---|---|
| 0–4 | 14–16 / 45 | **0.64–0.70** | 0.37–0.43 |

- feasibility §3 で指摘した通り、**毎 round に 45 cid の約 2/3 が undrawn**（M=20<45）＝α（factor=1・観察の不在）が実際に大半の cid に適用された。round 正規化の分母は drawn 14–16 cid の salience 平均。

### 3.2 weight 軌跡（entropy・集中度・per-round L1）
| t | H(feedback) | H(shuffle) | H(no_fb) | max_w(fb) | max_w(shuf) | L1(fb,shuf) | L1(fb,no_fb) |
|---|---|---|---|---|---|---|---|
| 0 | 3.640 | 3.633 | 3.780 | 0.083 | 0.082 | 0.348 | 0.271 |
| 2 | 3.315 | 3.411 | 3.780 | 0.147 | 0.112 | 0.831 | 0.655 |
| 4 | **2.762** | **3.234** | 3.780 | **0.286** | 0.151 | **1.271** | 0.979 |

（H=Shannon entropy・init log45=3.807・no_feedback は weight 固定ゆえ 3.78 不動）

- **feedback は shuffle より強く集中**（t4：H 2.76<3.23・max_w 0.286>0.151）。両群とも init から集中する（乗法更新＋歪んだ factor 多重集合の rich-get-richer）が、**対応を保つ feedback の方が集中が速い**。この feedback−shuffle の差が #CW7 を超える成果候補（設計 §4-2）——**但し単一 base seed0・g=1・統計なしゆえ「差が観測された」で停止**。
- L1(fb,shuffle) は round 単調増（0.35→1.27）で全 round L1(fb,no_feedback) を上回る。no_feedback は参照（§7-3 降格・weight 不動ゆえ L1 は「feedback が init からどれだけ動いたか」）。

### 3.3 数値健全性
- salience_raw：min 0.0 / mean 0.42 / max 1.602（＝floor `−log10(1/40)`＝両側 tail 上限）。子集団内で正常分布・floor 到達も定義通り。
- lens link_density：min 0.62 / mean 0.80 / max 0.98＝子間に spread があり珍しさが well-defined（潰れていない）。

## 4. 実装で固定した解釈（Web Claude 確認事項・1行切替可）

**shuffle-feedback を「feedback の世界に相乗り」で実装した**：shuffle は feedback の drawn cid・子・salience をそのまま使い、**更新直前に drawn distinct cid 間で正規化前 cid_salience を permute**（対応のみ破壊）して別 weight ベクトルに積む。

- 根拠：設計 rev3「**更新量の分布が完全一致**で対応のみ異なる null」「世界（どの子が存在したか）は同一」は、shuffle が feedback と同一 salience 多重集合を持つときにのみ字義的に成立する。独立 composition だと weight 乖離後に salience 多重集合がずれ「完全一致」が崩れる。
- 帰結：shuffle は独立に子を生成しない（feedback の 500 子を共有）＝停止条件 i の「全群で child 生成」は feedback/no_feedback の 2 群自走＋shuffle 相乗りで解釈（子数 1000）。
- **もし独立 composition（shuffle も自群 weight で M体引く）を意図していれば**：`update_factor(drawn_fb,…)`→`update_factor(drawn_shuf,…)` の1行で切替可。その場合 shuffle も 500 子自走（総 1500 子・+8分）。**採否は Web Claude/Taka**。

## 5. 走らせていないもの・次段（Code A は判定しない）

- **走らせていない**：main（複数 seed）・複数 base・複数 g（0.5 参考）・並行 lens（cycle_participation / R_positive_fraction）・統計判定（Holm・有意性）・real/artifact 判定・揺れ（entropy 順位変化）の解釈。
- **次段（承認後・Taka/Web Claude）**：(a) §4 の shuffle 解釈（相乗り vs 独立）確認、(b) full（複数 base×g×lens・Stage3b 型統計で feedback−shuffle L1 の paired 検定）、(c) 揺れの読み・回数増・多 eye・Atom 接続。**smoke はここで停止**。

## 6. 一文サマリ

v1304b smoke 報告（feedback loop 最小実装・実装健全性のみ・判定なし #12）── 子世界をセンターの観察 scope に足すループ（weight=now_theta lift 45支持 entropy3.78 で初期化→composition〔stage3b 機構・plb←s_avg〕→子 M体自走→子集団内の両側−log10 珍しさ〔probe 同式・lens=link_density〕を由来 cid に返す→cid単位平均→`factor=(cid_sal/round_mean)^g` で乗法更新〔α不動・undrawn=1・eps floor 正規化前・rank は監査のみ〕→次 round×T5・null3群 feedback/no_feedback〔round0固定・参照降格〕/shuffle〔feedback の世界に相乗り・drawn cid間で対応 permute〕）を R5×T5×M20＝1000子 909秒で実走行し、**停止成功条件6点すべて OK**（全 round・全群 child 生成・provenance 欠落なし・seed match・weight NaN/全消滅なし〔max_w 0.286 で1cid独占なし〕・**parent physics hash 不変**〔read-only 実証〕・書込 v1304 配下のみ）＝ループ実装が回り weight 軌跡が保存され3群が同 seed 条件で比較可能になった、descriptive な事実として〔判定でない・単一 base seed0・g1・統計なし〕毎 round に 45cid の約2/3が undrawn で α が実際に大半へ適用され、feedback は round を追って weight を集中〔t4 entropy 2.76〕させ shuffle〔同 t 3.23〕より強く集中・primary L1(fb,shuffle) は 0.35→1.27 単調増で全 round no_feedback 参照を上回った＝**「差が観測された」までで停止**（real/artifact・有意性・揺れの読みは主張せず）、実装で固定した唯一の解釈＝shuffle は feedback の世界に相乗り〔設計「更新量分布が完全一致」を字義的に満たす読み・独立 composition 意図なら1行切替可〕を Web Claude 確認事項として明記、main/複数base/複数g/並行lens/統計判定は未実施で承認後 full へ自動前進せず停止、shuffle 解釈確認・full 統計・揺れ/回数増/多eye/Atom接続は Taka/Web Claude。
