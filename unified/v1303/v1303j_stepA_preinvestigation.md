# v1303j Step A 事前調査（実装可能性チェック）— emitter→selector 設計を実コードで突合

*作成*: 2026-07-01、Code A。**実装前の feasibility check（設計でなく突合・判定なし #12）。read-only・物理非書込・seed0 のみ。** 採否・目の選定・cross-eye pull の可否は Web Claude / Taka。
*対象設計*: 「v1303j 設計 — emitter→selector（珍しさで pull・研究者 cutoff なし）」（Web Claude・2026-07-01）。
*成果物*: 本報告のみ（実装は未着手・Taka 承認待ちで停止）。

---

## 0. 調査の問い
v1303j 設計が指定する 5 つの目（瞬間θ/持続θ/非θ link 稀さ/cross-cid θ位置/静的 B_Gen）を、設計通りの**列名・グリッド・alive 定義**で実機 parquet から組めるか。組めない箇所と、着手前に Taka 判定が要る設計レベルの問題を、Explore でなく**実コード／実 parquet で**突合する（設計 §8 の確認要請に回答）。

## 1. 結論（先に）
- **機構は実装可能**：(い) 珍しさ比例ルーレット 1 本引き＋(あ) 全順位＋cross-eye 並置は、4 ソースが 10 倍数 t グリッド・228 cid で整合するため組める。
- ただし **設計の literal 列名は大半が不一致**（§2）であり、**2 件は着手前に Taka 判定が要る設計レベルの問題**（§3 の A・B）を実測で検出した。
- alive 定義は設計の「v1303i 既定」では成立せず、**per_subject から組む必要**がある（§4）。

## 2. 実列名の突合（設計の想定 vs 実機・要修正）
| 目 | 設計の想定列 | 実列名（実測） | 状態 |
|---|---|---|---|
| 瞬間θ (v1303f_attention_center) | "Now θ salience" | **`theta_resultant_length`**（nonnull 1.00・範囲 0–1）。`z_like_deviation`/`trigger_rate_ewma` は nonnull **0.44** で不適 | 名称未確定・推奨は theta_resultant_length |
| 持続θ (v1303e_persistence) | "persistence salience"・粒度=区間 | **`theta_cid_percentile`**（nonnull 1.00・0.13–1.0）。粒度は区間でなく**区間内 per-t**（med 40 行/cid） | 名称・粒度ずれ |
| 非θ link 稀さ (v1303i) | `rarity_internal_link` | **`rarity_internal_link_within_ncore`**（raw θ と corr **0.108** ＝独立✓） | 名前違いのみ・採用可 |
| cross-cid θ位置 (v1303i) | within_ncore / global の θ位置 | `rarity_theta_within_ncore` / `rarity_theta_global` | **⚠ §3-A 参照** |
| 静的 B_Gen (v1303h) | `bgen_pct_in_ncore` | **`bgen_pct_in_ncore`**（実在✓・per-cid 定数）。v1303i の `static_bgen_pct` でも per-(cid,t) broadcast 可 | 採用可 |

## 3. 着手前に Taka 判定が要る 2 件（実測検出）

### A. cross-cid θ位置は「瞬間θの言い換え」になっている（#11 / L 違反の恐れ）
v1303f の raw θ（`theta_resultant_length`）と v1303i の各 θ 稀さ列を (cid,t) で内部結合（merged **33,545** 行）した相関：

| 列 | raw θ との corr |
|---|---|
| `rarity_theta_global` | **0.990**　← ほぼ瞬間θそのもの |
| `rarity_theta_within_ncore` | **0.826** |
| `rarity_theta_within_cid` | 0.807 |
| `rarity_internal_link_within_ncore`（参考） | 0.108（独立） |

- 設計 §2 は自ら「θ味の稀さ（生θと 0.88＝既存θ際立ちの言い換え）は使わない」と除外基準を立てている。だが採用予定の within_ncore/global も**同じく高θ相関**で、特に **global(0.99) は瞬間θの目を別名で 2 本足す**ことに等しい（#11 合成禁止の精神＝同じ信号を別名で重複・L 言い換え）。[[feedback_no_reworded_reimplementation]]
- **事実のみ提示・判定は委ねる**：global を落とすか／位置情報として残すなら within_ncore のみにするか／目ごと軌跡を見てから決めるか は Taka 領域。

### B. v1303i の生成 .py がリポジトリに無い（grid 再現・監査不能）
- `v1303i_dynamic_rarity_seed0.parquet`（62,015 行×14 列）は存在するが、**生成スクリプトが repo 内に見当たらない**（`dynamic_rarity` / `rarity_internal_link_within_ncore` を含む .py が 0 件）。
- parquet 自体は read-only 入力として使えるが、設計は v1303i の (cid,t) を**共通グリッドに固定**する。グリッド構築ロジックが再現・監査できないまま base にするのはリスク。
- **推奨**：Step B 化の前に生成元を特定／コミット（または v1303j 側でグリッドを per_subject から明示再構築）。

## 4. グリッド整合・alive 定義（§8.1 / §8.3 への回答）
- **グリッド整合（成立）**：4 ソースとも 10 倍数 t・t∈[0,25000]・228 cid。v1303i(62,015 行)が最密だが per-cid 全点ではなく**生存&計測点のみ**（45–2500 行/cid・med 98）。merge は設計通り「イベント＝merge_asof backward／持続＝区間内 per-t／B_Gen＝cid broadcast」で寄せられる。
- **alive 定義（要修正）**：出所は **`developmental/v105/diag_v105_main_v2/subjects/per_subject_seed0.csv`**。`host_lost_step`（step 単位＝t 単位・500–25000）と `birth_window` を保持。final_state は **reaped 183 / hosted 37 / ghost 8**。
  - 設計の「`is_ghost = t ≥ host_lost_step`（**v1303i 既定**）」は不正確 — **v1303i に host_lost 列は無い**。alive/ghost タグは per_subject 由来で付ける必要がある。
- **ghost 検査の空振り注意**：v1303i は既に alive 区間を尊重済（host_lost を持つ **191 cid** のうち t≥host_lost_step に行を持つもの **0**）。よって設計 §7「ghost が pull を不当に占有していないか」は、i-グリッドの目では**そもそも ghost 行が母集合に居ない**ため空振りになり得る。ghost 構成を見るなら母集合を per_subject の生存定義から別途構築する要あり。

## 5. 既存規律との整合（§8.4）
- read-only・物理非書込・228 宇宙・同一 seed0 v105 main_v2 は崩していない。新規実装は **書込を `unified/v1303j/` 配下のみ**に限れば bit-identity 層 C を維持。
- F 型でない（同一 seed0・同系内 cross-cid・異 seed node inject でない）点は設計通りで実機とも一致。

## 6. 規模・停止方針（§8.5）
- seed0 のみ・最大 6.2 万行×5 目×~2,500 t のルーレット＝**数秒〜数分**。compute は問題なし。
- **smoke 後停止・main へ自動前進しない・smoke seed0 を絶対視しない**を遵守。[[feedback_smoke_then_pause]] [[feedback_smoke_seed0_not_absolute]]

## 7. 言えること / 言えないこと
- **言える（突合事実）**：機構は実装可能。グリッドは整合し alive は per_subject から組める。link 稀さ(corr 0.108)・静的 B_Gen・瞬間θ(theta_resultant_length)・持続θ(theta_cid_percentile)は実列として成立。
- **言わない（判定しない #12）**：「ESDE が注意した／選んだ」「selector に到達した」とは言わない。(あ)(い) 採否・cross-eye pull の可否・どの目を「動く軌跡」として価値ありと読むかは Taka 領域。global/within_ncore を残すか落とすかも Taka 判定（事実は §3-A の相関のみ提示）。

## 8. 次段（Code A は判定しない・委ねる）
着手前に Taka 承認が要る 4 点：(1) §3-A の cross-cid θ位置（global 0.99／within_ncore 0.83 の θ言い換え）の扱い、(2) §3-B の v1303i 生成元欠落、(3) §2 の実列名確定、(4) §4 の alive を per_subject から組む点。これらの承認後に実装着手。承認まで停止。

## 9. 一文サマリ
v1303j Step A 事前調査（実装前 feasibility・実コード突合・seed0・判定なし #12）── emitter→selector 設計の 5 目を実機 parquet で突合した結果、**機構（珍しさ比例ルーレット 1 本引き＋全順位＋cross-eye 並置）は実装可能**（4 ソースが 10 倍数 t・t∈[0,25000]・228 cid で整合・merge 可）だが、**設計の literal 列名は大半が不一致**（瞬間θ=`theta_resultant_length`／持続θ=`theta_cid_percentile`／link 稀さ=`rarity_internal_link_within_ncore`／B_Gen=`bgen_pct_in_ncore`）、かつ着手前に Taka 判定が要る **2 件を実測検出**＝**(A) cross-cid θ位置の `rarity_theta_global` は raw θ と corr 0.990・within_ncore も 0.826 ＝瞬間θの言い換えで設計自身の除外基準（θ味の稀さは使わない）に反する恐れ（#11/L）**、**(B) v1303i の生成 .py が repo に無く grid 再現・監査不能**、さらに **alive は設計の「v1303i 既定」では不可で per_subject_seed0.csv の host_lost_step から組む必要**・v1303i は既に alive 区間尊重済ゆえ §7 ghost 占有検査は空振りになり得る、read-only/物理非書込/228 宇宙は維持・書込は `unified/v1303j/` 配下のみ・smoke 後停止、(A)(B)＋実列名確定＋alive 再構築の 4 点を Taka 承認後に着手・承認まで停止（採否・cross-eye pull・どの目を動く軌跡と読むかは Taka 領域）。
