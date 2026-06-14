# v12 Atomset cid_align — STEP 0 報告: v1114 Step1 の入力単位確認

**指示書**: `実装指示書（Web Claude 2026-06-15）` STEP 0。コードを読むだけ・実装しない・報告のみ・pause。
**目的**: STEP 2 関門（準・循環性）の相関を*正しい単位*で取るため、v1114 が何を入力に発火するかを事実確認。

*作成*: 2026-06-15、Code A。*読んだコード*: `unified/v1114/step1_internal_attention.py` 全 297 行 + `developmental/v107/outputs/main/source_events_seed0.parquet` 実カラム。
**crown なし。観察事実のみ。**

---

## 0. 一文結論 + 【要・Web Claude 判断】

v1114 の**発火判定の入力は「系全体 per-10step の event_source_type 別カウント（5 種）」＝ per-CID ではない**。per-CID 量（n_core/lifespan/C/Q_remaining/familiarity_n）は**発火後にレコードへ貼る付帯情報**であって、発火判定には使われていない。**→ 指示書 STEP 2 が前提した「v1114 入力＝per-CID per-時間単位の生イベントカウント」と、実コードの単位がズレている。** STEP 2 の相関単位を Web Claude が確定する必要あり（下 §4 に選択肢）。

---

## 1. 発火判定に使う入力シグナル（事実）

| 項目 | 実コード事実 | 行 |
|---|---|---|
| 発火の入力 | `event_source_type` の **per-chunk 発生数**（count） | L152, L171-172 |
| event 種別 | **5 種**: `alpha_formation` / `beta_formation` / `c_conversion` / `ingestion` / `pulse`（実データで確認、14385 events） | L146, データ確認 |
| 集計単位 | **系全体（system-wide）**: `groupby(['chunk','event_source_type']).size()` ＝その chunk の全 CID 合算。**per-CID ではない** | L152 |
| 発火機構 | 各 event_type のカウントを EWMA に通し z-score、`abs(z) > Z_NOTICE` で発火 | L169-174 |
| 発火後 | その chunk・その type の最初の event（timestamp 順）の **代表 CID 1 個**を取りレコード化 | L177-186 |

**＝発火の引き金は「系全体で、ある event 種が普段より多く/少なく出た chunk」**。どの CID かは発火後に代表を 1 個選ぶだけ。

## 2. 時間粒度（事実）

| 項目 | 値 | 行 |
|---|---|---|
| chunk 幅 | **10 step**（`N_PER_CHUNK=10`、`chunk = timestamp // 10`） | L66, L144 |
| 動学長 | timestamp 0–24998 → 約 2500 chunks | データ確認 |

設計書の「10-step 解像度」と一致。

## 3. EWMA + z-score パラメータ（事実）

| パラメータ | 値 | 行 |
|---|---|---|
| EWMA_ALPHA | **0.2**（過去 ~5 chunk 重み 67%） | L67 |
| Z_NOTICE（注意発火） | **2.0** | L68 |
| Z_ANOMALY（異常発火） | 3.0（コード上定義のみ、L174 は Z_NOTICE で発火） | L69 |
| WARMUP_CHUNKS | **10**（warmup 中は z=0 で発火せず、var 下限 0.1） | L70, L101-106 |
| 更新式 | `mean += α·delta; var = (1-α)·(var + α·delta²); z = delta/√var` | L107-112 |

## 4. 【Web Claude 判断要】STEP 2 の相関単位 — 実コードとのズレ

指示書 STEP 2 は「STEP 0 で確認した v1114 入力（生イベントカウント、**per-CID per-時間単位**）の時系列」を既存入力シグナルとし、cid_align 変化量（per-CID per-時間単位）と個別 CID で相関を取る、とある。だが上記の通り **v1114 の実発火入力は per-CID でなく系全体カウント**。整合させる選択肢：

- **選択肢 A（per-CID 版を自作）**: events_df は `source_cid` を持つ（per-CID×type 集計可能＝596 グループ、データ確認済）。**per-CID per-10step の event_type 別カウント（5 列）を自分で作り**、それを説明変数に、cid_align 変化量（per-CID per-10step）を目的変数に重回帰 R²。→ 「cid_align は、その CID 自身の生イベントカウントの遅延コピーか」を per-CID で問える。**指示書の意図（per-CID 相関）に最も忠実。** ただし v1114 の*実際の*発火入力（系全体）とは別物を作ることになる（＝「v1114 が実際に拾う系全体シグナル」でなく「per-CID 生カウント」との循環性を見る）。
- **選択肢 B（系全体に合わせる）**: v1114 の実発火入力＝系全体カウントに合わせ、cid_align も系全体に集約して相関。→ 但し集約は絶対格言 #4 に反し、個別 CID が見えない。**非推奨。**
- **選択肢 C（両方）**: per-CID 版（A）を主、系全体版（B）を副で併記。

**Code A の見立て（判断は Web Claude/Taka）**: 落ち4 の本質は「cid_align が*その CID の*生イベント履歴の焼き直しか」なので、**選択肢 A（per-CID 自作カウント）が問いに最も合う**。v1114 の実発火が系全体なのは「出口（STEP 4）で Center が拾うか」の話で別段階。STEP 2 関門は「cid_align という per-CID 量が、per-CID 生カウントから独立か」を A で見るのが筋。

**この単位確定を待って STEP 1 へ。** 実装はしていない（本書は報告のみ）。

---

## 5. 付随確認（STEP 1 の前提として）

- v107 source_events は `source_cid` を持ち per-CID×event_type 集計可能（596 グループ）→ STEP 1 の per-CID cid_align 構築・STEP 2 選択肢 A の per-CID カウント、両方 offline で組める ✓。
- event 種別は 5 種で確定（alpha/beta/c_conversion/ingestion/pulse）。

---

*以上 STEP 0 完了（Code A、2026-06-15）。発火入力＝系全体 per-10step event_type カウント（5 種）、per-CID でない。EWMA α=0.2/Z_NOTICE=2.0/warmup=10/chunk=10step。指示書 STEP 2 の「per-CID 入力」前提と単位がズレ → STEP 2 相関単位を Web Claude が確定要（推奨=選択肢 A: per-CID 生カウント自作）。実装せず・pause。*
