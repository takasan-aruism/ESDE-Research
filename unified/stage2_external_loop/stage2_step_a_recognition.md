# 第 2 段階 Step A — Code A 認識確認

**Date**: 2026-05-31
**Author**: Code A
**Status**: Step A 認識確認、**重大な前提確認事項あり**

---

## 0. 受領内容認識

第 2 段階主題: 外部接続の技術的成立 最小実証

中心問い: ESDE を常駐させ、Genesis 状態を読んで外部ツール 1 つ実行、結果を source_event で戻すループが動くか

## 1. 「わからんことは言えよな」原則で最初に提示すべき重大事項

### 1.1 **ESDE main run の本体コードが現リポジトリに存在しない**

実環境照合結果:
```
developmental/v107/ にあるもの:
  - v107_post_process.py
  - v107_baseline_constructor.py 等 post_process スクリプト
  - v107_main_run_report.md (run の report)
  ★ v107_main_run.py や v107_run.py 等の main run 本体は不在
```

source_event は `source_events/source_events_seed{N}.parquet` の **frozen データ** (過去 main run の出力)。

→ Code A が触れるのは **past main run の出力データ + post_process** のみ。**「ESDE main run の常駐」はコードがない限り Code A 単独では実装不可能**。

### 1.2 設計書の意図解釈 3 案 (Web Claude / Taka 判断要)

| 案 | 内容 | 物理層 frozen との整合 |
|---|---|---|
| **A (リプレイ案)** | 既存 source_events を時系列順に **疑似常駐ループ** で再生、各 step で外部ツール実行、結果を新 source_event に追加 | ✓ 既存物理層は読むだけ、新ディレクトリで実装 |
| **B (擬似 ESDE 案)** | Genesis の挙動を模した **pseudo-ESDE を新規実装** (簡易物理シミュレーション)、常駐ループで回す | ✓ 既存物理層は読むだけ、Pseudo は別物 |
| **C (main run 取得案)** | ESDE main run コードを別途取得して実装 | × Code A が main run コードを持たない、要 Taka 提供 |

**Code A 推奨: 案 A (リプレイ案)**
- 既存データ frozen 維持
- 「ESDE 1 step 動く」を「次の event を読む」で代用
- 「Genesis 状態を読む」は既存 per_subject 等から
- 「source_event を Genesis に戻す」は新規 parquet を作って次 step の入力にする
- 物理層 frozen 厳密、書込み新ディレクトリのみ

### 1.3 案 A の最小実装プラン

```python
# 疑似常駐ループ
for step in range(N):  # while でなく for で停止条件明確化
    # 1. Genesis 状態を読む (frozen データから)
    cid_state = read_existing_cid_state(seed, step)  # frozen v106 等から

    # 2. 固定ルールで外部ツール実行
    ext_input = some_genesis_value(cid_state)
    ext_output = run_external_tool(ext_input)  # ファイル読み書き

    # 3. ext_output を新 source_event に変換
    new_event = build_source_event(step, ext_output)

    # 4. 新 source_event を append (新ディレクトリの parquet に)
    append_to_new_source_events(new_event)

    # 5. 次 step は new_event を含めた状態で動く (リプレイ + 追加)
```

物理層は読むだけ、外部書込みは新ディレクトリ + 用意したファイルのみ。

---

## 2. Code A 実装条件チェック (設計書 §4.2)

### 2.1 Q1: ESDE main run を常駐ループで回せるか

**現状: できない** (main run コードなし)。
案 A (リプレイ疑似常駐) で代用可能。

### 2.2 Q2: Genesis 状態 (cid/familiarity/注意の軌跡) を 1 step ごとに読み出せるか

**できる**:
- cid: `developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv`
- familiarity: `developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv`
- 注意 (attention emit): `unified/v1101a/outputs/main/attention_emit_seed{N}.parquet`

→ 全 frozen データから 1 step ずつ読み出し可能。

### 2.3 Q3: source_event スキーマ互換

**確認可**: `developmental/v107/outputs/main/source_events/source_events_seed{N}.parquet` の列構造を読み取り、新 event を同スキーマで生成する。

Step B で実体スキーマを確認、互換 parquet を作成。

### 2.4 Q4: 物理層 frozen 維持

**案 A で完全維持可能**:
- 既存 v105/v106/v107 等は read-only
- 書込みは `unified/stage2_external_loop/` 配下のみ
- 外部ツール対象ファイルも `unified/stage2_external_loop/sandbox/` 配下

bit-identity 検証で機械的確認。

### 2.5 Q5: 最初のツール (ファイル読み書き) で良いか

**良い、ただし具体を Code A で提案**:
- 例: `sandbox/external_state.json` に Genesis の cid 物理量 (familiarity 等) を書き、次 step で読んで source_event の field に乗せる
- 「ESDE が外部に書き → 外部が ESDE に戻る」の最小ループ
- 代替案: 時刻取得 (システム時間を入れる) も可

Code A 推奨: **ファイル読み書き** (確実、判定明確)。

### 2.6 Q6: 不足部分

| 不足 | 内容 |
|---|---|
| ESDE main run 本体コード | Code A 持たず、Taka 提供 or 案 A (リプレイ) で代用 |
| source_event 完全スキーマ | Step B で実体確認後に決定 |
| 固定ルール (状態 → ツール) の具体 | Step B で Code A 提案、後で主体性差し替え可能な構造 |

---

## 3. 案 A 採用前提での Step 分解

| Step | 内容 |
|---|---|
| A | 本文書、認識確認 + 案 A/B/C 判断要請 |
| B | 環境準備 (既存 source_events スキーマ確認、リプレイ可能性確認) |
| C | 疑似常駐ループ実装 (N step 固定) |
| D | 外部ツール実装 (ファイル読み書き) |
| E | source_event 変換 + 戻し |
| F | 6 確認項目 (設計書 §3.1) チェック |
| G | bit-identity (物理層 1 byte も侵さず) |
| H | 観察事実最終報告 + 出口判定 |

---

## 4. 重要な留保

### 4.1 案 A は「真の常駐」でない

- 案 A はリプレイ + 外部接続追加 = **疑似常駐**
- 「本当に ESDE が動いて外部と接続している」を実証するには案 B (pseudo-ESDE 新規) または案 C (main run コード) が必要
- 設計書 §1.2 の「ESDE を常駐させる」が「真の常駐」を意味するなら案 A では不十分

### 4.2 第 3 段階 (主体性検証) との接続

- 案 A: 固定ルール部分を「Genesis 状態由来の選択ロジック」に差し替え可能、第 3 段階で shuffle 検証可
- 案 B/C: 同様
- → どの案でも第 3 段階接続は確保

### 4.3 第 4 段階 (確率的発生拡張) との接続

- 案 A: リプレイなので「loop が崩れる」は再現できない (既存データ 1 回再生のみ)
- 案 B: pseudo-ESDE が時間進行を持てば loop 崩壊検証可
- 案 C: main run 常駐なら長期実行で loop 崩壊観察可能

→ **第 4 段階を本格的に検証するなら案 B か C が必要**

---

## 5. Web Claude / Taka 確認事項

| Q | Code A 提案 | 判断 |
|---|---|---|
| **a** | **案 A/B/C どれで進めるか** | **Web Claude / Taka 判断要 (最重要)** |
| b | 案 A 採用なら最初のツールはファイル読み書きで OK か | OK / 別ツール希望 |
| c | 案 B/C 採用なら ESDE main run コード提供あるか | Taka 確認要 |
| d | 「真の常駐」か「疑似常駐」で第 2 段階成立か | Web Claude / Taka 判断要 |

---

## 6. Code A 推奨

**案 A (リプレイ疑似常駐) で進めるのが最小実装の趣旨に合う**:
- v1109 教訓「精緻に作りすぎて失敗」を踏まえ最小
- 物理層 frozen 完全維持
- 第 3 段階 (主体性検証) に十分接続可能
- 第 4 段階 (loop 崩壊) は別途検証 (案 A の限界として明示)

→ **「外部接続が技術的に動くか」だけなら案 A で十分**、loop 崩壊検証は第 4 段階で別実装

---

**Step A end. 案 A/B/C 判断 + Q b/c/d 確認後、Step B 進行。**
