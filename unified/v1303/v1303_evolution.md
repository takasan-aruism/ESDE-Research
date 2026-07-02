# v1303 進化史 — 注意センター統合（emitter → selector → attention output schema）

*作成*: 2026-07-01、Code A。**v1303 の細かいサブブランチ（a→b→c→d→e→f→g→h→i→j Step A/B→Final）の具体的進化を一本に集約した記録。read-only 観察と固定作業の連なり・判定なし #12。**
*性質*: 各段の「何を・どのデータで・何を見つけ・何を次に繋いだか」の乾いた事実。crown・成立語を置かない。
*位置づけ*: v1303 = **ESDE 注意の入力側の確立**。親 ESDE が自分の珍しさで「何に注意を向ける候補にするか」を pull する所まで。投影（応答方向）・子ESDE は v1304+（`v1303_close_memo.md §6`）。

---

## 0. 一望（v1303 が辿った道）

```
[基盤]     v1303a  3レンズ ledger を canonical(v105_main_v2 seed0)で構築・frozen 検証
              │    ・レンズ = CID固有値 / Atom一致率(rank_1) / phys_core(θ/link/R…)
[時間構造]  v1303b  同一CID内で3レンズが時間方向にどう反復・安定・同時変動するか(観察A-E)
              │    → rank_1 は時間構造を持つ / θ は短期慣性のみ / レンズは概ね独立に動く
[手本event] v1303c  「手本イベント」二系統を event_class で分離保持
              │    ・birth_signature(R_positive=誕生署名) / salience_template(θ高同期)
              │    → R_positive は稀な結節でなく誕生署名(onset は観測不能・offset のみ)
[手本置換]  v1303d  θ高同期手本を ESDE 内在量で置換できる離脱候補の重なりを読む
              │    → 非θ系は弱い / θ系は重なるが「同じレンズの再記述(言い換え)」
[θ内部化]  v1303e  θ高同期閾値を「研究者の5%固定」→「内部履歴由来の動的閾値」に置換
              │    ・robust-range(θ≥q05+0.6·(q95−q05)) 連続3点持続 = 神の手排除
[Now/Arch] v1303f  v1114 注意センター設計を canonical から再構成し Archive-persistence と統合
              │    ・v1114 の別run(F型・退化バグ)を直接使わず同228cid宇宙で再構成
[4分類]    v1303g  Comparator 4分類 dry(Familiar/Novel × Stable/Unstable)
              │    → literal 定義は degenerate(92%1象限) → 構成的改善B'で4象限分離
[珍しさ軸]  v1303h  静的 B_Gen を n_core内 percentile に正規化 = θ/イベントと独立の珍しさ軸
              │    → 珍しさ・θ・イベントを「複数の目」として別列で並べる(合成しない)
[動的稀さ]  v1303i  各cid/tの物理状態の稀さ(動的構造稀さ)を経験分布から read-only 計算
              │    → 全228cidに付く/静的B_Genと独立/但し新規は link稀さ・cross-cidθ位置のみ
[selector]  v1303j  emitter(複数の目) → 珍しさ比例で1つ pull する selector-prototype
              │Step A: ルーレット1本引き(研究者cutoffなし) → 単発は chance支配で読めない
              │Step B: per-t 選択分布を本体に(marginal は平均化の罠) → 目はper-tでdistinct
[Final]    v1303   attention output schema + eye registry 固定 = v1303 クローズ(7条件)
                   ・正式eye 4 + 補助1・本体=per-t p_select・投影/子ESDEは v1304+ stub
```

**貫く原理**：read-only・物理非書込・同一 seed0 v105_main_v2・228 cid 宇宙・#12（判定は Taka）・#11（合成しない・目は別列）・A型回避（研究者 cutoff を入れず ESDE の値/null 差で判定）・L型回避（「注意した」と言わない）。

---

## 1. 基盤 — v1303a（3レンズ ledger の確立）

| 段 | 事実 |
|---|---|
| stepA inventory | 3レンズ（①per_subject CID固有値・②step10 alignment の Atom一致率 rank_1・③engine.state phys_core）を file:line で棚卸し。**canonical が割れており v105_main_v2 に固定**（v1302 は v918 別系ゆえ不使用）。rank_1 は全24seed既算出・③生 θ/link/R は決定論再走が必須。 |
| stepBF smoke | seed0 で (cid, t=step10) に3レンズを揃え **ledger 62,906行×40列**。3レンズ揃う率 98.58%。hosted 62,015行の link 三分類＝no_internal_link 97.8% / R0 382 / R_positive 1,002。frozen＝per_subject/pulse/per_window/per_label が main_v2 と byte 一致（計装が canonical を汚さない）。 |
| cost finding | ③再走コストの前提「~5min/seed」は v918(N小)の値で、**v105_main_v2(N=5000)は実測 ~2.7h/seed**（30倍）。コストは N=5000 が支配。→ 以降は seed0 smoke を基準に、24seed 本番は分離。 |

**残したもの**：`v1303_ledger_seed0.parquet`（以降の全段の共通土台）。anchor = v105_main_v2 に統一（F型混入の予防）。

---

## 2. 時間構造 — v1303b（同一CID内3レンズの反復・安定・同時変動）

- **前提突合**：設計の4主張（min_points45・ghost遷移163・cid0 θ autocorr・run_length崩壊）が seed0 ledger と**完全一致**。228 cid 全採用（n2=180/n3=12/n4=15/n5=21）。
- **観察A-E（後処理・shuffle 2種=within-cid time / within-ncore peer 対照）**：
  - A（rank_1 再出現）：run_length med 15.67–19.08・pctl med 1.000 → **Atom は時間構造を持つ**。
  - B（θ 自己相関）：lag1 med 0.59–0.77 だが lag5+ は shuffle 並み → **θ は短期慣性のみ**。
  - C（同時変動）：θ_jump@atom変化 ≈ baseline → **レンズは独立に振る舞う**。
  - D（ghost 前）：atom run_length 12.67→9.00 に低下・θ は保持 → **崩壊は非対称**。
  - E（補助）：R_positive 稀瞬間は θ 高同期(0.889)・atom変化増。
- **出口**：「経験候補として読める時間構造」まで（経験成立とは言わない）。→ v1303c（手本イベントへ）。

---

## 3. 手本イベント — v1303c（二系統を event_class 分離）

- **重大所見（設計-現実差）**：R_positive を持つ140 cid の**全てが誕生時の最初の hosted 行で既に R_positive>0**（onset_at_birth=140）。tracking 窓内に立ち上がり(onset)は無く offset(崩壊)のみ観測可能 → **R_positive は稀な結節でなく「誕生署名（founding cycle の減衰痕）」**。設計通りだと観測不能な onset を強引にラベル付け＝説明可能性崩壊。→ event_type を **present_at_birth/active/offset** に再定義。
- **実装**：二系統を read-only 検出し event_class で分離保持。
  - **birth_signature**（R_positive 誕生署名）1,002行（present_at_birth140/active743/offset119・140 cid）
  - **salience_template**（θ高同期・cid内 q95 上位5%）3,220行（全228 cid）
  - 重なり 270行を event_class で分けて保持。説明可能性ルーブリック7項目 PASS。
- **出口**：注意センター前段の記録配線＝離脱可能な構造が完成。→ v1303d。

---

## 4. 手本置換 — v1303d（θ手本を内在量で離脱できるか）

- **候補**：atom_switch・sim_delta_high（非θ）・theta_jump_high・theta_maddt_high（θ）を percentile+shuffle 比で読む。
- **観察**：**非θ系 primary は ratio_circular ≈0.9–1.0**（θ独立基準では θ高同期時点を拾わない）／**θ系 secondary は重なるが同じレンズの再記述**（theta_maddt 6.9・theta_jump 1.15）。n2 は疎すぎて測定不能。独立検証（陽性対照4.73/陰性1.00）で実装妥当を確認。
- **出口(a')**：「θ系だけ重なる＝手本の内部再記述に留まる」。θ独立な内生基準は seed0 では弱く立たず。→ v1303e（θそのものを内部化する方向へ）。

---

## 5. θ内部化 — v1303e（研究者の5%固定を撤去）

- **問い**：Frozen 神の手排除の2法（MAD-DT / persistence）を θ高同期閾値5%固定に応用できるか。
- **調査**：MAD-DT(値版)は n2 で 174–179/180 空振り（θ が std0.3 で激変し構造的に壊れる）。persistence(θ≥median 連続3点)は全 n_core で空振り0。
- **実装 v2（修正）**：v1(median またぎ=緩すぎ)を **robust-range 正規化（θ≥q05+0.6·(q95−q05)）連続3点持続**に変更。θ<0.5 を n2–4 で0%・n5 で0.6%（v1 の29%から解消）、拾う θ 中央 0.67–0.91。**18,809行（寿命の約48%）・q95 と Jaccard 0.11**（別の像＝多様性拡張）。検証ゲート全 PASS。
- **性質の明記**：これは θ系の言い換え・準同義反復の側面を持つ（正直記録）。→ v1303f。

---

## 6. Now/Archive 統合 — v1303f（v1114 を canonical で再構成）

- **重大発見（F型回避）**：v1114（注意センター6トリガー設計）の443 JSON は **t を持たず**（order のみ・40件重複で一意化不能）、かつ **v1114-only の9 cid は per_subject に存在しない別 run（退化バグ付き）** → 直接統合は F型（異系対応）。
- **Taka 判断**：v1114 の設計・ロジックは継承するが、**canonical ログ（pulse_log/lifecycle/c_trajectory/per_subject）から v1114 型イベントを t+cid 付き・同228cid 宇宙で再構成**。
- **実装**：Now-event 再構成 15,076行 + Archive-persistence（v1303e）18,809行＝**統合 33,885行**・宇宙外0（F型回避実証）。自己チェックで death が ghost 行に当たり θ=0.00 を検出 → hosted-only backward asof で「死ぬ直前の最後の hosted 状態」に修正（point_source_t/point_lag で透明化）。検証ゲート8項目 PASS。
- **出口**：過去(v1114 設計)と現在(v1303e 持続)を同じ宇宙で event_class 分けて統合。→ v1303g。

---

## 7. Comparator 4分類 — v1303g（degenerate を回避）

- **Step A 事前調査**：literal 定義（近傍Archive・過去同種・θ近さ・Atom安定・B_Gen層）は **degenerate**（Familiar-Stable 92.1% / Novel-Random 0.0%）。原因＝near_archive 飽和(0.996)・past_same が pulse 再発で自明(0.931)・atom_changed が稀(12%)。**degenerate のまま進めない**（信頼問題）。
- **改善 B'**：pulse 分離・Stable=θ帯・Familiar=past_same のみ → **4象限すべて立つ**（25.5/42.7/18.1/13.7・Novel 32%）。trigger 別＝誕生/死は Novel率1.00、α/β/c は Familiar 寄り。n_core 別 Novel率 n2=0.63→n5=0.09（長命高 n_core ほど再発で Familiar 化）。検証ゲート7項目 PASS。
- **出口**：照合列を別列で付け（合成しない）4象限を分離。カテゴリは pull 次元でなく後段のタグへ。→ v1303h。

---

## 8. 珍しさの独立軸 — v1303h（B_Gen を n_core内正規化）

- **方針確定**：Taka 指摘（B_Gen log10 で桁丸め）× 実機確認（ledger v11_b_gen は floor なし連続値で n_core 内に差あり）→ **B_Gen を n_core 内 percentile（bgen_pct_in_ncore）に正規化＝「実質一意の珍しさ」**。
- **独立性**：珍しさは θ際立ち・イベント際立ちと**独立**（bgen_pct vs θ帯 −0.005 / vs Novel 0.092）。B_Gen 珍しい cid(pct≥0.8)は Novel 側やや多め(0.23 vs 0.06)。
- **限界（明記）**：数値 B_Gen は **45/228 cid**（疎）。
- **出口**：珍しさ・θ・イベントを「複数の目」として別列で並べる土台。Comparator はまだ本体でない。→ v1303i。

---

## 9. 動的構造稀さ — v1303i（今の物理状態の稀さ）

- **問い**：静的 B_Gen（誕生時・疎）とは別に、各 cid/t の**物理状態の稀さ**を経験分布から read-only 計算できるか。
- **観察（GPT7項目 全達成）**：全228cid に付く（疎さ解消）・cid内/ncore内/global の3種計算可・静的 B_Gen と独立（corr −0.013）・n_core で壊れず・static_dynamic_delta 15.6% で |delta|>0.5。
- **3留保（正直記録）**：(1) θ味の稀さは既存θ際立ちと相関0.79＝**言い換え**、(2) R_positive 稀さは98%欠損で**退化**、(3) C/Q 稀さは相関−0.76で**冗長**。
- **新規に効く列**：非θの **rarity_internal_link**・**cross-cid θ位置（within_ncore/global）**・**228 coverage**。素朴に全部「稀さ列」にすると半分は言い換え/退化/冗長。→ v1303j。

---

## 10. selector — v1303j（emitter → 珍しさで pull）

emitter（複数の目）を、**研究者 cutoff なしで ESDE 固有の珍しさが 1 つ pull する selector の形**にする段。

### Step A（selector-prototype・ルーレット1本引き）
- 各 t・各目で珍しさ比例ルーレット 1 本引き（v12.1 同型・cutoff なし・目ごと並行 trajectory・合成なし）。grid/alive を **per_subject + c_trajectory(window→step=500) から自前再構築**（v1303i 生成元欠落に非依存）。
- **事前突合で 2 件を Taka に上げた**：(A) cross-cid θ位置 `rarity_theta_global` は raw θ と corr 0.990＝瞬間θの言い換え → 落とす／within_ncore は prove-by-trajectory で保持、(B) v1303i 生成 .py が repo に無く grid 監査不能 → per_subject から自前再構築。
- **落とし穴1（実証）**：pulled-cid の single-draw 一致率は目の異同に関係なく **chance(≈1/eligible≈0.04) に支配**され distinct 判定に使えない（now×peer 0.044 ≈ uniform 0.037）。

### Step B（per-t 分布読み・distribution audit）
- **核心 insight**：選択確率は正規化 salience で厳密（`p=clip(sal,0)/Σ`・RNG 不要）。freq=mean_t p を厳密算出＝単発 chance 支配が原理的に消える。many-RNG(N=200) は sampler 検証で **corr_emp_exact 0.9999**（バグなし）。
- **落とし穴2（実証）**：設計が「本体」とした **marginal（時間平均）分布相関は D型平均化の罠**で露出時間支配 → θ/link/peer が全て uniform と ~0.99。→ **本体を per-t に移設**。
- **per-t（本体）で読める事実**：目は per-t で distinct（now×peer 0.55 / now×link 0.48 / now×persist 0.43 / now×bgen −0.05）かつ全 eye が uniform と区別可（per-t KL>0）。**persist は duration lens でない**（pulled/eligible seglen 0.955・corr(pullprob,seglen) −0.14）→ Archive 内 θ-percentile lens。

---

## 11. Final — v1303 クローズ（attention output schema 固定）

- **eye registry（Taka + GPT 判断を固定）**：正式4 = `now_theta`（瞬間同期）/ `archive_theta_percentile`（旧 persist_thetapct・改名＝duration lens でない）/ `link_rarity`（非θ物理稀さ）/ `bgen_static_prior`（誕生時 prior）。補助1 = `aux_peer_relative_theta`（θ-family ゆえ本体に数えず保持）。不採用（global/within_cid θ・R_positive・C-Q）は戻さない。
- **attention output schema**：`t × cid × eye`（366,605行）。**本体 = `p_select_given_eye_t`**（per-t 選択確率・各(eye,t)で Σ_cid=1）。marginal=参考・single-draw=例示のみ。
- **構造の正直な記述**：5独立系でなく **dynamic physical cluster（now/archive_θ/link/peer・per-t corr 0.43–0.77）+ static prior（bgen・直交）**。多系性は薄いが link は非θ＝物理側の別軸。軸数を成果に数えない（DNA=4記号に相当）。
- **クローズ7条件充足**（emitter 棚卸し・重複整理・selector 実装・per-t 本体確定・eye 決定・schema 固定・次版 stub）→ v1303 クローズ。**v1303k / Step C を作らない**。

---

## 12. v1303 が残した知見（次版が継ぐもの）

1. **注意の入力側の部品**：どの cid が・どの目で・どれだけ引かれやすいか（per-t 選択確率）を固定した schema（`v1303_final_attention_output_seed0.parquet`）。これが v1304 projection の入力。
2. **方法論の落とし穴 2 件**（memory `feedback_single_draw_agreement_is_chance` に固定）：(1) single-draw 一致率は chance 支配、(2) marginal 平均化は selector の個性を洗い流す。**selector の distinct 性は per-t 分布/値 corr/many-RNG で見る**。
3. **F型回避の実践**：v1114 の別 run を直接使わず canonical から同宇宙で再構成（v1303f）。異系対応の再発を防いだ。
4. **神の手排除の実践**：θ閾値5%固定 → 内部履歴由来の動的閾値（v1303e）／cutoff を入れず null 差で判定（v1303j）。
5. **正直な留保の連鎖**：θ系の稀さ/位置は「θの言い換え」になりやすい（v1303d/i/j で一貫検出）。新規に効いたのは非θの link 稀さのみ。

---

## 13. 次段（v1303 非対象・v1304+）

- **v1304 = attention projection / child-ESDE interface**：per-t の p_select（cid×eye 分布）を子ESDE 生成・選別・再演算の入力にする（`v1304a_feasibility_check.md`＝cw_run.py 再利用で存在チェック実装可・写像形のみ Taka 合意待ち）。
- selector（v1303・何を注意候補にするか）と projection（v1304・注意→応答方向）を混ぜない。子ESDE・Atom 意味接続・内部環境・外部入力・cross-eye 合成 pull はすべて v1304+ の主題。

---

## 14. 一文サマリ

v1303 進化史 ── 3レンズ ledger(a)→同一CID内時間構造(b)→手本イベント二系統の event_class 分離(c・R_positive は誕生署名と判明)→θ手本を内在量で離脱できるか(d・θ系は言い換え)→θ高同期閾値を5%固定から robust-range 動的持続へ内部化(e)→v1114 を canonical で再構成し Now/Archive 統合(f・F型回避)→Comparator 4分類の literal degenerate を改善B'で回避(g)→B_Gen を n_core内正規化で θ/イベントと独立の珍しさ軸に(h)→動的構造稀さは全228cidで計算可だが新規は非θ link 稀さのみ(i)→emitter を研究者 cutoff なしで珍しさが pull する selector-prototype(j Step A)→単発は chance 支配で読めず per-t 選択分布を本体に(j Step B・marginal は平均化の罠)→正式eye 4+補助1・per-t p_select を本体とする attention output schema を固定し 7条件で v1303 クローズ、貫く原理は read-only・物理非書込・同228cid宇宙・#11 合成しない・A型/L型回避・#12 判定は Taka、残した部品は attention 入力側の schema(v1304 projection の入力)と方法論の落とし穴2件、次段は v1304 = child-ESDE projection(selector と projection を混ぜない)。
