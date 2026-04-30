# v10.3 smoke 1 結果レポート (動作確認 + bit-identity 検証)

*作成*: 2026-04-30、Code A
*対象*: v10.3 双方向 E3 + 観察軸機構の smoke 1 検証
*親資料*: `claude_code_v103_implementation_instruction.md` (実装指示書)
*位置づけ*: 実装指示書 §8.1 smoke 1 通過判定。本番 run の前段。

---

## 0. 一行サマリ

v10.3 smoke 1 通過 (実装指示書 §12 完了判定 1)。**双方向 E3 機構が正常に動作**、**Layer A bit-identity 29/29 完全一致**、**Layer B (v10.2 baseline 比較) 23/23 完全一致**、**wall time オーバーヘッド -0.1% (実質ゼロ、shadow audit モード)**。本番 run へ進行可。

---

## 1. 実装範囲

### 1.1 新規ファイル

```
developmental/v103/
├── v103_memory_readout.py          (v102 から fork、ledger 入れ替え + --be3-shadow-audit)
├── v103_spend_audit_ledger.py      (v914 から fork、E3 detect 後に be3 hook 追加)
├── v103_observation_target.py      (ObservationTargetTracker、Stage 1/2/3)
├── v103_be3_postprocess.py         (window 末 / run 末で triad 検出 + 集計)
└── v103_smoke1_report.md           (本レポート)
```

v102 から継承 (内部不変):
- v102_cid_self_buffer.py、v102_fetch_operations.py、v102_orchestrator.py、v102_theta_distance.py、v102_unity_metrics.py
- v914_event_emitter.py
- v917_a_observer.py、v917_cid_self_buffer.py、v917_cid_view.py、v917_divergence_tracker.py、v917_interaction_log.py

### 1.2 v103_spend_audit_ledger.py の変更点 (v914 fork)

実装指示書 §3 step 4 通り、`observe_step` の以下の位置に be3 phase を挿入:

```
... E3 detection (detect_e3_new_pairs) 完了
... v9.14 disable_e3 チェック
+++ v10.3 双方向 E3 phase ←追加
... balance_decision (cid_a → cid_b と cid_b → cid_a の 2 視点)
... ingestion 処理
```

加えて:
- `__init__` に `be3_target_tracker`、`be3_shadow_audit`、`be3_disable` 引数追加
- `_n_consciousness_per_cid` 累積カウンタ (Stage 1 判定用)
- balance loop で consciousness 当選時に counter +1
- `flush_run` に `bidirectional/` ディレクトリへの 3 CSV 出力追加

---

## 2. smoke 1 実行条件

実装指示書 §8.1 通り:

| 項目 | 値 |
|---|---|
| seeds | 1 (smoke 用) |
| N | 5000 (本番と同じ) |
| maturation | 20 |
| tracking | 10 (短縮) |
| window_steps | 500 |
| 並列 | -j1 (smoke は 1 seed) |
| be3_shadow_audit | True (C 消費なし、log のみ) |

### 2.1 同条件で 3 つ run

- **smoke1a** (v103 shadow audit、Layer A 検証用 1 回目)
- **smoke1b** (同条件、Layer A 検証用 2 回目)
- **v102 baseline** (v10.2 で同条件、Layer B 検証用)

---

## 3. 結果

### 3.1 機構動作確認

smoke1a 出力:
```
v10.3 bidirectional E3 CSVs written to diag_v103_smoke1a/bidirectional/
    bidirectional_e3_log: 128 rows (47 fired, 81 skipped)
    bidirectional_e3_member_nodes: 47 rows
    bidirectional_e3_summary: 1 file
```

**fired 47 件 / skipped 81 件**で計 128 entries。tracking 10 windows × 1 seed なので、本番想定 (50 windows × 24 seeds) では **~5,640 件 / 1 seed 換算 ~235 件/seed** 規模。

#### skip 理由の分布

| 理由 | 件数 |
|---|---:|
| c_zero_a (cid_a の C=0) | 28 |
| c_zero_b (cid_b の C=0) | 12 |
| ghost_a (cid_a が ghost) | 16 |
| ghost_b (cid_b が ghost) | 25 |
| **合計** | **81** |

C=0 (40 件) と ghost (41 件) が均等で、設計通り「C 蓄積がない cid」と「ghost 化済 cid」が双方向 E3 に参加しない自然フィルタが機能。

#### post-process 結果

```
$ python3 v103_be3_postprocess.py diag_v103_smoke1a 0
  128 rows (47 fired)
  Detecting triads per window...
  47 pair-level flags
  10 window stats
  wrote bidirectional_e3_3rd_cid_log: 38 rows
  updated bidirectional_e3_log with has_3rd_* flags
  wrote per_window summary: 10 rows
  wrote per_subject summary: 33 rows
```

- **Cat 1a (closed triad): 0 件** (smoke 規模で発生せず)
- **Cat 1b (open triad): 38 件** (open intermediary 形態)
- **window 別**: 後半 window (27, 29) で open triad 増加 (5-6 件) — 主役同士の反復接触の兆候

### 3.2 Layer A bit-identity (smoke1a vs smoke1b)

**29/29 ファイル完全一致** ✅

| ディレクトリ | 一致 / 全件 |
|---|---:|
| audit | 3 / 3 |
| aggregates | 1 / 1 |
| balance | 3 / 3 |
| ingestion | 2 / 2 |
| labels | 1 / 1 |
| persistence | 4 / 4 |
| selfread | 7 / 7 |
| subjects | 2 / 2 |
| **bidirectional (post-process 後)** | **6 / 6** |
| **合計** | **29 / 29** |

bidirectional の 6 ファイル (本流 log、3rd_cid log、member_nodes log、summary、window_summary、per_subject) すべてが両 run で完全一致。**v10.3 機構の決定論性確認**。

### 3.3 Layer B bit-identity (v103 shadow audit vs v102 baseline)

**23/23 ファイル完全一致** ✅

bidirectional/ を除く全 CSV が v10.2 baseline と完全一致。

| 検証項目 | 結果 |
|---|---|
| 物理層列 (per_event_audit, per_window, persistence) | **identical** |
| 認知層 (balance_decisions, c_trajectory, balance_summary) | **identical** |
| 摂食層 (ingestion_events, ingestion_summary) | **identical** |
| Layer C (selfread, divergence_log) | **identical** |
| ラベル (per_label, per_subject) | **identical** |

→ **v103 shadow audit モードでは v10.2 と完全に同じ動作**。これは:
- 双方向 E3 を log するが C 消費しない (shadow audit)
- → cog.C が変わらない
- → balance_decision の確率計算が変わらない (Q/(Q+C))
- → 全認知層動作が v10.2 と完全一致
- → 副次的に物理層動作も完全一致

これにより v10.3 が「v10.2 + 双方向 E3 観察 log」という関係であることが数値的に保証された。

### 3.4 wall time 比較

| run | wall time | 倍率 (vs v102 baseline) |
|---|---:|---:|
| v102 baseline | 3,839 s (64.0 min) | 1.000 |
| v103 smoke1a | 3,835 s (63.9 min) | **0.999** |
| v103 smoke1b | 3,743 s (62.4 min) | 0.975 |

**v103 shadow audit のオーバーヘッドは実質ゼロ (-0.1%)**。Code A 第二次応答での試算 +20-30% は過大見積もりだった。

理由:
- be3 phase は per-step で `new_e3_pairs` を 0-3 件しか走査しない
- log 記録は軽量 (per-step 1-3 entries)
- shadow audit モードは C 消費なし → cog state 一切変えない → 認知層動作完全同一

本番 (shadow audit OFF、C 消費あり) では C 状態変化に応じた balance_decision の経路差異が生じるが、それでも実 overhead は数 % 以内と推定。

---

## 4. 規模試算 (smoke 1 → smoke 2 / 本番判断)

実装指示書 §8.2 の 4 metric:

| metric | 閾値 | smoke1 実測 | 判定 |
|---|---|---|---|
| **M1**: target 比 | ≤ 15% | **0%** (tracking 10 で主役条件未達、想定通り) | ✅ |
| **M2**: events/step | ≤ 10 | 128 / 5,000 step = 0.026 | ✅ |
| **M3**: CSV 合計 | ≤ 200 MB | bidirectional/ で ~30 KB | ✅ |
| **M4**: wall ratio | ≤ 1.3 | **0.999** | ✅ |

**全 metric 大幅クリア**。本番 run へ進行可。

ただし注意:
- **M1 = 0%** は tracking 10 では主役条件 (n_consciousness ≥ 5) に届かないため。本番 (tracking 50) では主役 cid が現れる
- shadow audit モードでは log は target 内外関係なく全件記録 (= 5/3 で修正)
- 本番モードでは target 内のみ詳細記録

---

## 5. bidirectional_e3_log の例

`fired=True` の代表例:

```
window=20, step=248: cid_a=2 (n_core=5), cid_b=22 (n_core=5)
  q_a=31, q_b=32, c_a=1, c_b=1 → 全条件満たす
  link=(3092,3480), age_a=1, age_b=1
```

`skip` の代表例:

```
window=20, step=0: cid_a=0, cid_b=41
  c_a=0, c_b=0 → skip_reason=c_zero_a (cid_a 側を先に判定)
  
window=21, step=419: cid_a=9, cid_b=66
  c_a=0, c_b=1 だが cid_b は ghost → skip_reason=ghost_b
```

post-process で検出された open intermediary 例 (window 22):

```
cid_a=9, cid_b=68, cid_c=22 (open intermediary)
  → 9-68 が双方向 E3、9-22 も双方向 E3、しかし 68-22 は未発火
  → 22 は 9 と 68 の中継者として登場
```

---

## 6. 規律確認 (実装指示書 §10)

- [x] 物理層 frozen (engine 一切 touch しない) — Layer B 確認
- [x] Layer A bit-identity (v10.2 物理層列と一致) — Layer B 確認
- [x] cid 内部に新規状態を追加しない (M_c 不変、Q/C のみ既存) — `_n_consciousness_per_cid` は ledger 内
- [x] 神の手を入れない (物理接触 + 両者生存のみで発火、選別なし) — fired 47 件すべて条件満たし
- [x] 第三項候補は実験者観測軸として記録、cid 内部に持たせない
- [x] C 消費は記録ルール、判定機構ではない (shadow audit で確認)
- [x] balance_rng と be3_rng は engine.rng から独立 (be3_rng は現状未使用)
- [x] 既存 CSV 列を変更しない (列追加のみ) — Layer B 23/23 で確認
- [x] 「嗜好」「三項共鳴」を機構名に含めない (be3 / triad 中立名)
- [x] target 外も全体集計で監視 (n_be3_target_outer)

---

## 7. 次のステップ

1. **本レポートの Taka レビュー**
2. (Taka 承認後) **shadow audit 本番** (実装指示書 §8.3)
   - N=5000、tracking 50、24 seeds
   - C 消費なし (shadow audit モード)
   - 想定 wall ~3-4h
   - 観察項目: 物理層 list, 既存 E3 件数, be3 発火件数, skip 理由分布, target 内/外比率, 第三項カテゴリ重なり
3. (shadow audit 通過後) **本番 run** (実装指示書 §8.4)
   - 同条件で C 消費あり
   - 想定 wall ~13-15h

---

## 8. 出力ファイル一覧

```
developmental/v103/
├── v103_memory_readout.py
├── v103_spend_audit_ledger.py
├── v103_observation_target.py
├── v103_be3_postprocess.py
├── v103_smoke1_report.md (本レポート)
├── diag_v103_smoke1a/   (1 回目 run、29 CSV)
├── diag_v103_smoke1b/   (2 回目 run、29 CSV)
└── run_logs_smoke/      (実行ログ)

developmental/v102/
└── diag_v102_v102baseline_for_v103/  (Layer B 比較用 v10.2 baseline run)
```

---

## 9. 結論

v10.3 smoke 1 通過判定:

1. ✅ **機構動作**: 双方向 E3 が物理接触 onset で 47 件 fired、skip 81 件 (理由内訳健全)
2. ✅ **Layer A bit-identity**: smoke1a vs smoke1b 完全一致 (29/29)
3. ✅ **Layer B bit-identity**: v103 shadow audit vs v10.2 baseline 完全一致 (23/23)
4. ✅ **wall time**: -0.1% オーバーヘッド (実質ゼロ)
5. ✅ **post-process**: open triad 38 件検出、closed triad 0 件 (規模相当)
6. ✅ **regulation**: 実装指示書 §10 全項目満たす

本番 (shadow audit + 本番 run) へ進行可。Taka 承認待ち。

---

*以上、v10.3 smoke 1 結果レポート。Taka レビューを待つ。*
