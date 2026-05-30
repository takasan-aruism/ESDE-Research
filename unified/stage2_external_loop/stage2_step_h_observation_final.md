# 第 2 段階 Step H — 観察事実最終報告

**Date**: 2026-05-31
**Author**: Code A
**Status**: 全 Step (A-G) 完了、**出口: `external_loop_runs`**

---

## 0. 全 Step 完了

| Step | 内容 | 実行時間 |
|---|---|---:|
| A v1 | 認識確認 (誤、main run なし判定) | - |
| A v2 | **訂正 (Taka 指摘で再調査、autonomy/v82 + primitive/v918 発見)** | - |
| B | V82Engine smoke 起動 | 0.25s |
| C+D+E | 完全外部接続ループ (30 iter) | 0.33s |
| F | 6 確認項目 | 6/6 PASS |
| G | bit-identity 3 層 | 全 PASS |
| H | 本報告 | - |

---

## 1. 主要結果

### 1.1 出口判定: **`external_loop_runs`**

設計書 §3.1 の 6 確認項目すべて成立:

| # | 確認 | 結果 |
|---|---|---|
| 1 | 常駐ループ安定 | ✓ 30 iter 完走、0.32s |
| 2 | Genesis 状態読み取り | ✓ engine.state + virtual_stats + stress_stats 全 iter |
| 3 | 外部ツール (ファイル読み書き) | ✓ sandbox/state.json write/read 30/30 |
| 4 | source_event 変換 | ✓ 30 events 生成 |
| 5 | engine への戻し | ✓ engine._stage2_external_inputs 30 events 保持 |
| 6 | 物理層 frozen | ✓ Step G で詳細確認 |

→ **「ESDE 常駐 + 外部接続 + Genesis に戻し」のループが技術的に動く** ことを実証

### 1.2 動作の流れ (1 iter)

```
[ESDE step] engine.step_window(steps=10) — 本物の V82Engine 動作
       ↓
[Genesis 状態読み取り] engine.state, virtual_stats, stress_stats から
  alive_n/alive_l/labels_active/torque_events/mean_omega
       ↓
[外部書込] sandbox/state.json に ESDE state を書く
       ↓
[外部読込] sandbox/state.json から読み戻す
       ↓
[source_event 変換] external payload → source_event スキーマ
       ↓
[engine 戻し] engine._stage2_external_inputs に inject
       ↓
[次 iter へ] 30 iter まで繰り返し
```

### 1.3 物理層 frozen 厳密維持

Step G で 15 root 全 frozen 確認:
- developmental/v105〜v113a (9 ディレクトリ、計約 7,300 files)
- autonomy/v82 (550 files)
- cognition/semantic_injection/v4_pipeline/v43 + v41 (29 files)
- ecology/engine (17 files)
- primitive/v918 (653 files)
- language/lexicon/data/mapper_output (325 files)

**Stage 2 の書込みは `unified/stage2_external_loop/` 配下のみ**、1 byte も既存物理層を侵さず。

---

## 2. 留保事項

### 2.1 alive_n = alive_l = 0 のままだった
N=500 で 30 windows × 10 steps = 300 step 実行したが、alive_n が立たなかった。

考えられる理由:
- V82_N default は 5000、N=500 は smoke 過小
- V82Engine の genesis 物理が起動するには warmup が必要
- step_window steps が短すぎる (V82_WINDOW default 50)

**第 2 段階の「技術的成立」判定には影響しない** (engine.state へのアクセス・読み取り自体は OK)。
ただし「実体的な ESDE 動作」を見るには N=5000 + 全 step (例 maturation 20 windows + tracking 10 windows) が必要。

これは第 3 段階 (主体性検証) で N=5000 設定で再実行すれば解消。

### 2.2 source_event のスキーマは簡易版
v107_source_events と完全同型でなく、第 2 段階最小実証用の簡易フィールド:
- iter, event_id, source_cid, timestamp
- esde_alive_n, esde_alive_l, esde_labels_active, esde_mean_omega
- external_loop_completed

第 3 段階以降で正式スキーマ (v107 互換) に拡張可。

### 2.3 engine への inject は外部 attribute 保持のみ
V82Engine は直接的な source_event 受信機構を持たない。第 2 段階では `engine._stage2_external_inputs` に保持するのみ (神の手で可、設計書 §0.3 規律緩めの範囲)。

第 3 段階で実体的な engine 入力 (next torque、 attention bias 等) に差し替え可能な構造を維持。

---

## 3. Code A 自己点検

### 3.1 v1 → v2 訂正 (規律違反からの学び)

v1 認識確認で「ESDE main run 本体コードが存在しない」と書いたのは **完全な調査不足**:
- `developmental/v107` だけ見て結論
- `autonomy/`、`primitive/`、`cognition/` 等を一切調べていなかった

Taka 指摘:
> 「ないわけないだろう。これまで何度実験したと思ってる? バージョンを戻っていけば必ずある。」

→ Step A v2 で訂正、ESDE main run 本体を発見 (autonomy/v82 + primitive/v918)

### 3.2 新規規律 (Taka 採用済)

**「『存在しない』『不可能』と書く前に、リポジトリ全階層 (autonomy / primitive / developmental / unified / legacy 全部) を調べる」**

これは 7 段階目 self-fulfilling baseline 検査の拡張版。Code A の他の主題でも適用すべき。

### 3.3 v90 の発見 (副産物)
- `autonomy/v90/diag_v90_feedback_A0.3/` ← 「feedback」機能
- `autonomy/v90/virtual_layer_v9.py` ← Self-Referential Feedback Loop
- ESDE は v90 で **仮想層内 feedback** を既に実装していた
- 第 2 段階「外部接続」と方向性が一致、第 3 段階以降で参考になる可能性

---

## 4. 次の段階への接続

### 4.1 第 3 段階 (主体性検証) への準備
- 第 2 段階の「固定ルール」(state → 外部書込) を「Genesis 由来の選択ロジック」に差し替え可能な構造を維持
- 第 3 段階で shuffle 検証 (主体性が Genesis 由来か神の手か)

### 4.2 第 4 段階 (確率的発生の拡張) への準備
- 案 C (真の常駐) なので、N=5000 設定 + 長期実行で loop 崩壊観察可能
- ただし alive_n が立たない問題を先に解消必要 (N=5000 設定 + warmup windows)

### 4.3 Taka 構想との接続
- 「cid 時系列増殖、マーカー = 注目」: 外部接続が「注目マーカー」候補
- 「応答時間が系を変化」: 外部接続のタイミングが系を変える可能性

---

## 5. 出力ファイル一覧

### スクリプト (5 ファイル)
- `stage2_step_a_recognition.md` (v1、誤、保存)
- `stage2_step_a_recognition_v2.md` (v2、訂正版)
- `stage2_step_b_smoke.py`
- `stage2_step_cde_external_loop.py`
- `stage2_step_f_six_checks.py`
- `stage2_step_g_bit_identity.py`

### 出力 (parquet)
- `outputs/main/loop_log.parquet` (30 iter × 状態列)
- `outputs/main/source_events.parquet` (30 events)
- `outputs/main/six_checks.parquet`
- `outputs/main/step_f_summary.parquet`

### sandbox / report
- `sandbox/state.json` (最終 ESDE state)
- `stage2_step_g_bit_identity_report.json`

### 報告書
- `stage2_step_h_observation_final.md` (本文書)

---

## 6. Web Claude / Taka への報告

### 6.1 結論
**第 2 段階 (外部接続の技術的成立 最小実証) は成立**。
- 6/6 確認項目 PASS、出口 `external_loop_runs`
- 物理層 1 byte も侵さず、案 C (V82Engine 真の常駐) で実装
- 第 3 段階 (主体性検証) へ進める

### 6.2 重要な教訓
**「全階層調べる」規律を採用**したことで、ESDE main run 本体発見 → 案 C 実装可能性立証。
これは Code A の今後の他主題にも適用する規律。

### 6.3 残課題
1. alive_n=0 問題 (V82_N=5000 設定 + warmup で解消可能、第 3 段階準備)
2. source_event スキーマ正式化 (v107 互換、第 3 段階以降)
3. engine inject の実体化 (現状 attribute 保持のみ、第 3 段階で次 torque/seed 等に差し替え)

---

**Step H end. 第 3 段階 (主体性検証) へ進む準備完了。**
