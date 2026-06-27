# v1303c Step A — 認識確認 + 説明可能性ルーブリック（実装前・一部 Web Claude 再調整要）

*作成*: 2026-06-28、Code A。
*位置づけ*: v1303c 主題設計 §7 の Step A（認識確認）。設計の配線前提を seed0 ledger で突合し、**各 event_ledger 列/処理の説明可能性(explainability)を自分で設定**、低説明可能性＝強引な解釈が入る箇所を洗い出す。**重大な設計-現実の差を1件検出（§2）→ Web Claude 再調整に回す**。判定はしない（#12）。
*対象データ*: 既存 `unified/v1303/outputs/v1303_ledger_seed0.parquet`（後処理・再走なし・Step E 不要）。

---

## 1. 配線前提の突合（feasibility・設計と一致した項目）
| 設計前提 | 実データ（seed0 ledger） | 判定 |
|---|---|---|
| R_positive を ledger から抽出（再走不要） | `core_internal_R_positive_count>0` = **1,002行 / 140 cid** | ✓ |
| 健全性1: R_positive 行は全件 hosted | phys_core_status / cid_status とも **全1,002行 hosted_available**（ghost/reaped=0） | ✓ assert 通る |
| 連続 R_positive を segment 化（持続を複数誤カウントしない） | t 歯抜けなし（hosted中 step10 連続）・**segment数=140**・segment長 med=7/max=27 | ✓（ただし §2 の含意大） |
| pre/post 文脈の紐づけ | 直後行あり=**100%** / 直前行あり=**86.0%**（残14%=§2の誕生時行） | ✓（欠損は null 記録） |
| event_strength = r_positive_count 等 | r_positive_count 値域 1–5（med1）/ internal_link_count 1–5（med1）/ R_max 1–3（med1.5） | ✓（ほぼ定数=1・§5で注記） |

## 2. 【重大・Web Claude 再調整要】onset は観測されない＝R_positive は「誕生署名」
**実測**：R_positive を持つ **140 cid 全てで、最初の hosted 行（=誕生直後の最初の step10 snapshot）で既に R_positive>0**（`onset_at_birth=140`）。segment数=cid数=140＝**各 cid は R_positive を生涯に一度きり、誕生時から持ち、持続後に消える（offset）**。再度立ち上がる cid は 0。

**含意（設計の中核と食い違う）**：
- 設計は `event_onset_flag` で「R_positive が**立ち上がった瞬間(onset)**＝結節が立った瞬間」を注意センター手本の最重要とした（§2.2/§3.3）。
- だが **0→>0 の立ち上がり遷移は tracking 窓内に一度も存在しない**（誕生前=maturation で既に閉路が立っている）。観測できる遷移は **offset（>0→0＝閉路の崩壊）のみ**。
- これは v1303a「label は閉路で生まれ位相で生きる」(§4.6) の物理署名：**label は誕生時の founding cycle（閉路）から生まれ、その内部リンクが S 減衰で R→0 になり、以後は位相同期だけで生きる**。R_positive は「稀に立つ結節」でなく「**誕生時の founding cycle が減衰していく痕跡**」。
- ∴ 設計通り `event_onset_flag` を実装すると、**観測されない onset を全140件「立ち上がった」と強引にラベル付け**することになる＝説明可能性が崩れる（ユーザ指摘の「強引な解釈」）。

**Code A からの選択肢（判定せず Web Claude/Taka に委ねる）**：
- (A) event_type を実データに合わせ **`present_at_birth`（誕生時から在）/ `active`（持続中）/ `offset`（崩壊した瞬間）** に再定義。観測可能な遷移＝offset を主に。onset は「観測不能（pre-tracking）」と明記。
- (B) 手本を「立ち上がり」でなく「**founding cycle の持続区間（segment）そのもの**」とする（誕生→崩壊の1区間＝140イベント）。
- (C) R_positive 手本の妥当性を再検討（誕生署名であって自律的結節でないなら、手本としての意味づけを変える）。
- → **どれを採るかは設計の意図（注意センター手本に何を求めるか）に依存するため、実装前に Web Claude 再調整を要請**。器(event_ledger)の列は作れるが、**event_type の意味づけを実データに整合させないと L型(意味盛り)/強引解釈になる**。

## 3. 健全性2（Gemini 予測2）の予測は成り立たない可能性
- 設計予測：R_positive 行の rank_1 entropy は全体と効果サイズ |d|<0.2（差なし）＝手本が個の際立ちを平均化で潰していない。
- 実測（group entropy）：**n_core=2 で 1.026→1.333（増）/ n_core=5 で 2.366→0.471（大幅減）** ＝ R_positive 行の atom 分布は全体と**強く異なり n_core 依存で逆向き**（n5 は64行と小標本）。
- → 健全性2 は「差なし」でなく「**差あり・n_core 依存**」。設計は健全性2を「主題の出口にしない・新発見扱いしない」としたので**ブロッカーではない**が、**「|d|<0.2 を assert する」実装はしない**（観察事実として効果サイズを記録するに留める）。Web Claude へ予測修正の情報提供。

## 4. v1114 の扱い（§4 確認結果）→ 新規構築
- v1114 は `primitive/v918/diag_v918_main/subjects/per_subject_seed{N}.csv` を読む（`step1_internal_attention.py:72` 他）＝**v918 anchor**。step2a は `/tmp/v105_step2a_seed0_main`（main_v2 でない一時 v105）。
- → **v105_v2（v1303 anchor）と CID 宇宙不一致＝F型**。Gemini「1セルでも不一致なら流用即時却下」に該当。
- → v1303c は **v105_v2 上で event_ledger を新規構築**（v1303a/b と同一 anchor）。v1114 は参考資料扱い（流用しない）。設計 §4 が想定した通り。

## 5. 【ユーザ指示の核心】説明可能性ルーブリック（列/処理ごと）
各列に **説明可能性レベル** と **乾いた操作定義** を設定。LOW＝強引な解釈が入りうる箇所＝実装前に潰す/明示する。
| 列 / 処理 | 説明可能性 | 操作定義（これ以外の解釈を許さない） | 強引解釈リスクと対処 |
|---|---|---|---|
| seed, cid, t, n_core, theta_resultant_length, rank_1_atom, rank_1_sim, C, Q, phys_core_status, r_positive_count, internal_link_count | **HIGH** | v1303a ledger からの直接コピー（変換なし） | なし（出所＝ledger 行） |
| event_source=`researcher_template:R_positive` / template_version=`r_positive_v1` | **HIGH** | 定数リテラル（手本であることの明示・離脱用ポインタ） | なし（隠さないことが A型回避） |
| event_segment_id | **HIGH** | 同一 cid 内で R_positive>0 が step10 連続する塊に通し番号 | なし（連続性は機械的） |
| ledger_source_id, pre_t/post_t, pre/post_context_id | **HIGH** | 元 ledger 行の (cid,t) と隣接 step10 行 (t±10) への参照ポインタ。**context_window=±1 step10 に固定**（恣意排除） | 窓幅を可変にしない＝固定で明示 |
| **event_type** | **LOW→要再定義** | 設計の onset/active/offset。**onset が観測不能(§2)ゆえ現状は強引** | §2-(A) で `present_at_birth/active/offset` に再定義してから実装 |
| **event_onset_flag** | **LOW** | 「0→>0 立ち上がり」だが該当0件・全140が誕生時在 | §2: `present_at_birth_flag` に置換し「onsetは観測不能」と明記。立ち上がりを捏造しない |
| **event_strength** | **MEDIUM** | r_positive_count（共鳴する内部リンク数）。**ほぼ定数1**（med1・max5） | 「強さ」という語を避け **`resonating_internal_link_count`（生カウント）**で記録。強度の含意を盛らない |

**ルーブリックの使い方（ユーザ指示）**：実装後、生成された event_ledger を本ルーブリックと突合し、各列が操作定義通りか（例：present_at_birth_flag が本当に i=0 行のみか、segment_id が連続塊と一致か）を検証して整合性をさらに高める（Step C/F で実施）。

## 6. Step A 結論（Code A）
- **配線は可能**（R_positive 抽出・全hosted・segment・pre/post 紐づけ・新規 anchor v105_v2 すべて feasible）。後処理のみ・再走不要。
- **ただし event_type/onset の意味づけが実データと食い違う（§2）**＝設計通り実装すると強引解釈になる。**実装前に Web Claude 再調整を要請**（event_type を §2-(A/B/C) のどれにするか）。
- 健全性2 は予測修正（§3・assert しない）、v1114 は新規構築（§4）。説明可能性ルーブリック（§5）で LOW 3列を明示・対処方針を提示済。

## 7. 一文サマリ
v1303c Step A 認識確認（Code A, 2026-06-28）── 設計の配線前提を seed0 ledger で突合し R_positive 抽出(1,002行/140cid・**全件 hosted**＝健全性1 assert 通る)・segment化(140区間)・pre/post紐づけ(post100%/pre86%)・後処理のみ(再走不要)は feasible と確認した一方、**重大所見：R_positive を持つ140cid 全てが誕生時の最初のhosted行で既に R_positive>0(onset_at_birth=140・segment数=cid数)＝『立ち上がる瞬間(onset)』は tracking窓内に一度も観測されず観測可能なのは offset(閉路の崩壊)のみ＝R_positive は稀な結節でなく v1303a「閉路で生まれ位相で生きる」の誕生署名(founding cycle の減衰痕)**であり、設計の中核 `event_onset_flag`（onset=結節が立った瞬間を手本）を設計通り実装すると観測不能な立ち上がりを全140件強引にラベル付け＝説明可能性崩壊になるため event_type を present_at_birth/active/offset へ再定義(案A)か segment全体を手本(案B)か手本妥当性再検討(案C)を **Web Claude 再調整に要請**、健全性2 は rank_1 entropy が R_positive で全体と強く相違・n_core依存逆向き(n2 1.026→1.333/n5 2.366→0.471)で「|d|<0.2差なし」予測は成立せず assert せず観察記録に留める、v1114 は v918 anchor で v105_v2 と CID宇宙不一致(F型)ゆえ流用せず v105_v2 上に新規構築、**説明可能性ルーブリックを全列に設定**(直接コピー列/event_source/segment_id/context=HIGH、event_strength=MEDIUM[「強さ」を避け resonating_internal_link_count の生カウントで記録]、event_type/onset_flag=LOW→present_at_birth へ再定義)、実装後にルーブリックと突合して整合性を高める方針、配線自体は可能だが event_type の意味づけ確定を待って Step B 実装、判定は Web Claude/Taka。
