# v1303d Step A〜F — 手本(θ高同期)を ESDE 内在量で置換できる候補の重なり 観察事実報告（判定なし）

*作成*: 2026-06-28、Code A。
*位置づけ*: v1303d 主題設計（手本→離脱の離脱本体）の Step A〜F。既存 v1303a ledger + v1303c event_ledger の**後処理のみ**（再走/write-back なし）で、researcher_template θ高同期（salience）が拾った際立ち時点を、ESDE 内在量から作る endogenous candidate がどれだけ同じ cid/t 近傍で拾えるかを cid 内 percentile + shuffle 比で読んだ。**(a)/(a')/(b) 判定はしない（#12）。** 「ESDE が自律注意した」「手本を外せた」とは言わず「離脱候補を読めた」まで。判定は Web Claude / Taka。
*成果物*: `v1303d_detach_candidates.py` / `outputs/v1303d/v1303d_overlap_seed0.parquet`（cid×候補×重なり）/ `v1303d_distributions.html`。

---

## 0. Step A 認識確認（実装前突合・全一致 + 1制約）
設計の経験的前提を seed0 で実装前に突合（前回の「時間位置を見ない見落とし」を反省し先回り）：
| 前提 | 実データ | |
|---|---|---|
| B_Gen static（cid内 unique=1） | unique max=1 ✓ | **但し数値B_Genは45cid・183cidは'unformed'**（B_Gen層別は45cidのみ） |
| C/Q delta は window境界(500の倍数)のみ | cid=0 [500,2000,4500…] 全て500倍数 ✓ | C/Q を時点トリガーから除外する根拠が正しい |
| Atom固定cid=6（切替候補なし） | 6 / eligible222 ✓ | atom_switch を eligible分離 |
| circular shift(131) vs full shuffle(1497) | 観測130 ✓ | circular採用が正しい（局所構造保存） |
| sim変動の独立性 | atom非切替時も\|Δsim\|>0（全cid）✓ | sim_delta は独立候補 |

→ 実装可能。唯一の制約＝B_Gen層別は45cid（健全性2を限定・ブロッカーでない）。

## 1. 観察設計（候補別・cid内percentile・shuffle比・合成しない）
- 手本 = v1303c salience（cid内 θ_resultant q95上位5%時点）。実装後突合で v1303c salience と cid単位一致を確認（ルーブリック）。
- 内生候補（三分類・C/Q は時点トリガーから除外＝window粒度の偽スパイク回避）：
  - **primary（非θ系・離脱の主証拠）**：`atom_switch`（rank_1_atom 切替時点・二値）、`sim_delta_high`（\|Δsim\| cid内上位5%）。
  - **secondary（θ系・補助＝同義反復ゆえ弱い）**：`theta_jump_high`（\|Δθ\| 上位5%）、`theta_maddt_high`（\|θ−中央値\|/MAD 上位5%）。
- 重なり = θ-high時点 ∩ 候補時点（exact と ±1 step10 を分離・両方向）／ **shuffle比**（full=時間順破壊・circular=位相ずらしで局所構造保存）で偶然超えを判定。**合成スコアにしない**（候補別）。

## 2. 【コード自己検証】中央値が n_core 異質性を潰す問題を検出・修正
ユーザ指示「自分のコードに問題ないか確認」に従い検証：
- **計算の正しさ**：cid=0 の atom_switch exact=11・pm1=29 が独立手計算と**完全一致**。ルーブリック7項目（手本=v1303c salience一致・atom固定cid ineligible・primary/secondary分類・C/Q非候補・合成なし・ineligible NaN）**全PASS**。
- **発見した報告上の問題**：当初の「集約中央値」は **n_core 逆向き挙動を混合**。例 `theta_maddt_high` は cid=0(n5) で ratio=**8.17** だが全体中央値=**0.00**（n2は θ天井飽和で MAD偏差が「低下時点」を拾い θ-high と逆・n5は分散で高θ＝高偏差で重複）。中央値だけ見ると「θ系は重ならない」と**逆の結論**を報告する所だった。→ **per-n_core + イベント十分subset で再報告**（下記）。これは計算バグでなく集約の過圧縮。

## 3. 観察事実（per-n_core・shuffle比 ratio_circular 中央値）
| 候補 | 分類 | n2 | n3 | n4 | n5 |
|---|---|---|---|---|---|
| atom_switch | 非θPRI | 0.00※ | 0.77 | 0.90 | 0.94 |
| sim_delta_high | 非θPRI | 1.10※ | 0.75 | 0.90 | 1.03 |
| theta_jump_high | θSEC | 0.00※ | 0.98 | 1.46 | 2.53 |
| theta_maddt_high | θSEC | 0.00※ | 6.96 | 8.08 | 8.45 |

※n2（cid 180体・θ-high中央3点/候補4点）は**イベントが疎すぎて重なり測定不能**（overlap_pm1 中央0・91/174がゼロ）＝「重ならない」でなく「測れない」。解釈は n4/n5 で行う。

### イベント十分subset（n_theta_high≥10 & n_candidate≥10・71 cid・大半 n4/n5）
| 候補 | 分類 | ratio_circular med | >1.0 cid | θ→候補 | 候補→θ |
|---|---|---|---|---|---|
| atom_switch | 非θPRI | **0.92** | 20/51 | 0.150 | 0.111 |
| sim_delta_high | 非θPRI | **0.95** | 33/71 | 0.150 | 0.128 |
| theta_jump_high | θSEC | 1.15 | 37/71 | 0.157 | 0.140 |
| theta_maddt_high | θSEC | **6.92** | 41/71 | 0.900 | 0.800 |

## 4. 観察の要点（記述・判定しない）
- **非θ系 primary（atom_switch・sim_delta_high）は ratio_circular ≈ 0.9–1.0 ＝ circular shift 対照と同等以下**。θ-high と独立な基準（Atom切替・sim変動）は、θ高同期の際立ち時点を偶然超えて拾っていない（両方向被覆率も 0.11–0.15 と低い）。
- **θ系 secondary は重なる**：`theta_maddt_high` は ratio 6.9（θ→候補 0.90）＝θ-high⊂θ_maddt の**準同義反復**（同じ θ レンズの言い換え）、`theta_jump_high` は 1.15（n5で2.53）＝θが急変する時点と高同期時点は部分的に重なる。
- **B_Gen 層別（45cid）**：low/high で primary に明確差なし（atom 0.98/0.94・sim 0.91/1.12）。
- これは設計の出口表現では **(a')「θ系候補だけが重なる＝手本の内部再記述に留まる（離脱でない）」** に対応する向きの観察事実（**判定は委ねる**）。非θ系が shuffle 比で明確に上回る (a) は seed0 では観察されず、どの候補も区別不能 (b) でもない（θ系は重なる）。

## 5. 健全性 sanity check（主題の出口にしない）
- **健全性1（非対称）**：両方向被覆率を記録（θ→候補 / 候補→θ）。予測値を当てにいかず非対称の向きのみ観察（primary はほぼ対称・低い／theta_maddt は θ→候補0.90>候補→θ0.80）。
- **健全性2（B_Gen層別）**：45cid（unformed 183除外）で層別記録。明確差なし。新発見扱いしない。
- **健全性3（eligible）**：atom_switch eligible=222 / atom固定6cid を「候補なし」として分離（「重ならない」に混ぜない・D型回避）。

## 6. 言えること / 言えないこと
- **言える（観察事実）**：θ高同期手本を、非θ系内生量（Atom切替・sim変動）は偶然超えで拾えない（ratio≈0.9-1.0）。θ系内生量（θ_maddt・θ_jump）は重なるが同じレンズの再記述。n2 は疎で測定不能。これは「離脱候補（θ独立な内生基準で同じ際立ちを拾う）」が seed0 では強く立たない、を指す観察。
- **言わない**：「ESDE が自律注意した」「手本を外せた／外せない」「自律注意成立」「経験成立」とは言わない。「離脱できた／できない」でなく「離脱候補を読めた（非θ系では弱い・θ系は同義反復）」まで。Atom 意味解釈しない。(a)/(a')/(b) 判定は委ねる。

## 7. 規律遵守
- A型/#CW7: 内生候補は ESDE 内在量に限り**合成指標を作らない**（神の手回避）。手本タグ event_source の離脱ポインタは v1303c から継続。
- C型: 重なりは絶対値でなく shuffle比（full+circular）。**θ系の重なりを離脱証拠にしない**（secondary・同義反復）。予測を当てにいかない。**コード自己検証で中央値の過圧縮を検出し per-n_core に修正**（観察方法を疑う規律の実行）。
- D型: cid内 percentile（n2偏り回避）・cid個別/n_core別・B_Gen層別・eligible分離。#11: 候補合成しない・θ系/非θ系分離・C/Q(window)を時点に混ぜない。
- #12/J型: 判定せず観察事実のみ・手本と候補の重なり1観察・seed0。L型: Atom 意味解釈しない。F型: anchor=v105_v2。

## 8. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（cid内 percentile・shuffle比・両方向・per-n_core の生データ再確認、特に theta_maddt の準同義反復性と n2 疎問題）→ Phase Result → Taka 主題評価。離脱の実行（endogenous だけで salience 再定義）・外部照合は次段以降。多シードは離脱候補が立つか見てから（seed0 では非θ系は弱い）。

---

## 9. 一文サマリ
v1303d（既存 v1303a ledger + v1303c event_ledger 後処理・再走/write-back なし・seed0・anchor v105_v2）で researcher_template θ高同期手本を ESDE 内在量で置換できる候補の重なりを候補別・cid内percentile上位5%・shuffle比(full+circular)・両方向で読んだ結果、Step A 突合で B_Gen が static(数値は45cid・183 unformed)・C/Q が window境界スパイク(時点トリガーから除外)・atom固定6cid(eligible222)・circular shift が局所構造保存を実装前確認し、**コード自己検証で cid=0 手計算一致(exact11/pm1 29)とルーブリック7項目PASSを確認しつつ集約中央値が n_core 逆向き挙動を潰す問題(theta_maddt cid=0 ratio8.17 vs 中央0)を検出して per-n_core+イベント十分subsetに修正**(中央値だけなら逆結論を報告する所だった)、観察事実＝**非θ系primary(atom_switch/sim_delta)は ratio_circular≈0.9-1.0で circular対照と同等以下(θ独立基準では θ高同期時点を偶然超えて拾わない)・θ系secondary は theta_maddt 6.9(θ-high⊂θ_maddtの準同義反復)/theta_jump 1.15で重なる(同レンズ再記述)・n2は θ-high中央3点で疎すぎ測定不能・B_Gen層別45cidで差なし**、これは設計出口の (a')「θ系だけ重なる＝手本の内部再記述に留まる(離脱でない)」を指す向き(判定は委ねる・(a)非θ系明確超えは seed0 で観察されず)、「ESDE自律注意・手本を外せた・経験成立」とは言わず「離脱候補を読めた(非θ系で弱い)」まで、健全性1(非対称両方向記録)・2(B_Gen層別45cid差なしassertせず)・3(atom固定6cid分離)、合成指標なし・θ系/非θ系分離・cid内percentile(D型回避)、判定はWeb Claude/Taka。
