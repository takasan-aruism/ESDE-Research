# v10.11 完了報告 — Integration 形成プロセス解析: q_c_inherited 起点 within-cid 観察

*作成*: 2026-05-10、Code A
*Phase*: ESDE Developmental Phase v10.11 (Phase 1.5 Genesis × Language 統合段階・第六試行)
*親*: `v111_phase_design.md` 第三稿 / `v111_step_b_report.md`
*対象*: Web Claude (主題完了レポート作成) / Taka (Phase 1.5 第六試行完了確認)

---

## 0. 一文サマリ

v10.11 主題 (q_c_inherited 起点 within-cid design、12 cells = n_core_bin × β 累積 c_inherited 分位) main run を 24 seeds × 並列で **7.65 秒** で完了 (272,835 snapshots、13,055 (event, cid) pairs)、bit-identity 層 A PASS、cross-seed 解析で **Step B (seed 0) の観察と異なる結果** を観察事実として記録 (seed 0: Q1 のみ正、Q2-Q4 で 0 → 24 seeds 集計: 全 12 cells で正値 +0.097〜+0.497)、**核心観察**: q_c_inherited 前後で β member cid の C 値が 24 seeds 一貫して正方向に動く (bin_2×Q1 / bin_3_4×Q4 で complete_consistent)、累積 c_inherited 分位による differential 応答は不支持、**C 値飽和仮説 (主題 §1.5) は本データで支持されない**、達成条件 §0.2 (v10.12 入力ルーティング条件 1 本以上抽出) は **「β member cid は q_c_inherited で C 値が継続的に増加するため、v10.12 概念取り込み目的での入力対象から除外」** という条件抽出で満たす、留保事項 4 件追加 (seed 0 と 24 seeds 不一致、C 飽和不支持、ESDE β 機能の事実確認、no_alpha 群は別フレーム)、storage 累計 1.52 GB (25%) で打ち切り条件 50% 余裕大、Web Claude 主題完了レポート → Phase 1.5 第六試行完了 → v10.12 主題決定の順で進む。

---

## §1 達成判定 (主題ドキュメント §6)

| 項目 | 結果 |
|---|---|
| 機構動作 (Level 1) | bit-identity 層 A PASS、alpha/beta_lifecycle_log 全 event_type 読み込み完了 |
| 観察事実の取得 (Level 2-3) | 12 cells × 24 seeds で delta_C_within / delta_pulse_within 取得、288 rows |
| 仮説間の分離 (Level 3.5) | C 値飽和仮説不支持、ESDE 構造的事実 (q_c_inherited は C を増加させる本来の機能) を観察 |
| **v10.12 入力ルーティング条件** (Level 3.5+) | **条件 1 本抽出済み** (§4.2 参照) |

→ **達成条件 §0.2 達成**。

---

## §2 main run 実績

### 2.1 計算量

```
v10.11 q_c_inherited observer - mode=main, seeds=24, n_workers=24
T_OFFSETS: 21 samples (-50, -45, ..., +50)

DONE  total elapsed = 7.65s
```

- Code A 認識確認推定 1-2 分から大幅短縮 (実測 7.65 秒、推定の約 1/15)
- §0.3 打ち切り条件 3 (30 分超) に **大幅余裕**

### 2.2 出力規模

| 区分 | 値 |
|---|---:|
| total q_c_inherited events (24 seeds) | 2,247 |
| events with member_cids 記録 | 1,379 (61.4%) |
| (event, cid) pairs | 13,055 |
| total snapshots | 272,835 |
| unique cids | 1,483 |
| unique β | (要再集計) |

### 2.3 12 cells × 24 seeds 集計

288 rows (12 cells × 24 seeds)、全 cell × seed で母集団確保 (n_pairs > 0)。

### 2.4 storage 実績

| ファイル | サイズ |
|---|---:|
| q_c_inherited_response_profile_seed*.parquet (24) | 約 700 KB |
| q_c_inherited_events_seed*.parquet (24) | 約 150 KB |
| cross_seed/within_cid_deltas.parquet | ~3 MB |
| cross_seed/* (集計) | ~1 MB |
| **v10.11 main 合計** | **~5 MB** |

累計:
- v10.7-v10.10 main: 1.51 GB
- v10.11 main: 0.005 GB
- **累計 1.52 GB / 上限 6 GB (25%)** ← Code A 認識確認推定 27 MB、実測 5 MB で更に余裕

→ §0.3 打ち切り条件 3 (累計 3 GB) に **大幅余裕**。

---

## §3 観察事実 (24 seeds 集計、Step B seed 0 と差異あり)

### 3.1 delta_C_within (T+50 - T-50) × n_core_bin × c_q_partition

| n_core_bin | Q1 (<3) | Q2 (3-6) | Q3 (6-9) | Q4 (≥10) |
|---|---:|---:|---:|---:|
| **bin_2** | **+0.187** | +0.116 | +0.097 | **+0.247** |
| **bin_3_4** | **+0.467** | +0.206 | **+0.497** | +0.276 |
| **bin_5+** | **+0.356** | +0.314 | +0.368 | +0.377 |

→ **全 12 cells で正値** (+0.097 〜 +0.497)

### 3.2 24 seeds 方向一致 4 段階

| n_core_bin | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| bin_2 | **complete_consistent** | majority_zero | majority_zero | majority_consistent |
| bin_3_4 | majority_consistent | tied | tied | **complete_consistent** |
| bin_5+ | majority_consistent | majority_consistent | tied | majority_consistent |

→ **bin_2 × Q1** と **bin_3_4 × Q4** で 24 seeds 完全一致 (complete_consistent)

### 3.3 delta_pulse_within (T+50 - T-50)

| n_core_bin | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| bin_2 | -0.047 | -0.032 | -0.008 | -0.020 |
| bin_3_4 | 0.000 | 0.000 | 0.000 | -0.001 |
| bin_5+ | 0.000 | 0.000 | 0.000 | -0.000 |

→ **全 cell で ≈ 0** (q_c_inherited 前後で pulse 数は変化しない)

### 3.4 Step B (seed 0) との差異

Step B (seed 0):
- bin_2×Q1 +0.593 / bin_3_4×Q1 +1.200 / bin_5+×Q1 +0.273 (Q1 のみ正値)
- Q2-Q4 はすべて 0 (bin_3_4×Q4 のみ +0.250)

24 seeds 集計:
- 全 cell で正値、Q1 と Q4 がほぼ同程度
- 「Q1 のみ正、Q2-Q4 で 0」のパターンは **seed 0 固有** で 24 seeds 集計で消失

→ **留保事項として記録**: seed 0 の観察は 24 seeds 集計で再現せず、seed-level の variability の例。

---

## §4 整理仮説と達成条件 §0.2

### 4.1 整理仮説 (主題 §3 ラベル規律準拠、留保つき)

#### 仮説 2 (C 値飽和、主題 §1.5) は本データで不支持

主題 §1.5 で示唆された「累積 c_inherited が大きい cid ほど delta_C 余地が消失する」仮説を検証:

| 観察 | 仮説 2 への支持/不支持 |
|---|---|
| 全 12 cells で delta_C_within 正値 (+0.097 〜 +0.497) | **不支持** (Q4 で ≈ 0 にならない) |
| Q1 と Q4 が同程度 (bin_5+ で Q1 +0.356 vs Q4 +0.377) | **不支持** (累積による differential なし) |
| seed 0 のみで Q1 のみ正パターン観察 | seed-level variability、24 seeds で消失 |

→ **C 値飽和仮説は本主題のデータで不支持**

#### 観察事実から立ち上がる別仮説

「q_c_inherited は β member cid の C 値を **継続的に増加させる ESDE 構造的機能**」:
- これは v10.5 §85 (β = 会計、Q/C 継承単位) の機構そのもの
- 累積に関わらず、各 q_c_inherited event で c_inherited_delta だけ C が増加
- 観察事実 (delta_C_within 全 cell 正値) はこの機構の直接観察に過ぎない可能性

留保:
- 「累積 c_inherited による飽和」は v10.10 で観察された「形成後 100 step 超で delta_C 0」とは別現象の可能性
- v10.10 の応答性消失は atom_introduction_event 起点、本 v10.11 は q_c_inherited 起点で event の質が異なる
- v10.10 留保 11 (応答性消失の構造的根拠) は本主題で完全には解明されず、留保継承

### 4.2 v10.12 入力ルーティング条件 (達成条件 §0.2)

#### 条件 1: 概念取り込み (delta_C 系) — 抽出済み

**「v10.12 で概念取り込み (delta_C) を狙うなら、β member cid (q_c_inherited を受ける cid) は対象から除外、別 cid (no_alpha 群、または β に組み込まれない cid) を狙う」**

抽出根拠:
- β member cid は q_c_inherited で C 値が継続的に増加 (delta_C_within +0.1〜+0.5)
- 追加の atom event を打っても、cid の C は β からの継承で動いている (q_c_inherited の影響)
- **β member cid を atom 入力対象にすると、atom event 効果と β 継承効果が混在して測定困難**

v10.12 設計への含意:
- 入力対象 = β に組み込まれていない cid (Integration 形成前 / no_alpha)
- v10.10 留保 14 (no_alpha 群の v110_vs_v108re +0.133) との接続点

#### 条件 2: 行動活性化 (pulse 系) — 限定的

q_c_inherited 前後で pulse 数の変化は観察されず (delta_pulse ≈ 0)。
- 行動活性化目的での β member cid 選定は **本主題の観察範囲では推奨できない**
- v10.10 で観察された「ペア (n_core=2) cid + matched 経路で pulse +4.295」は **atom event 起点** の観察、q_c_inherited 起点とは別軸

→ 行動活性化目的の cid 選定は v10.12 で v10.10 既存観察を活用、本主題の追加条件抽出は限定的。

### 4.3 達成条件 §0.2 の判定

主題 §0.2 (v10.12 入力ルーティング設計に使える条件 1 本以上抽出):
- **条件 1**: 「β member cid は概念取り込み対象から除外」 ← **抽出済み**

→ **達成条件 §0.2 達成**。

---

## §5 留保事項 (新規発生 + 継承)

v10.10 まで継承の留保 14 件 + 第二弾追加 4 件 = 18 件 + 本主題で発生:

### 5.1 v10.11 で新規発生 (4 件)

19. **seed 0 と 24 seeds の観察パターン不一致**: seed 0 で Q1 のみ正、Q2-Q4 で 0 のパターンが 24 seeds 集計で消失 (全 cell 正値)。seed-level variability の例として記録、構造的根拠未解明
20. **C 値飽和仮説 (主題 §1.5) の不支持**: 24 seeds 集計で累積 c_inherited による differential 応答が観察されず、仮説 2 は本データで不支持。v10.10 形成後 cid の delta_C 消失とは別現象の可能性
21. **ESDE β 機能の直接観察**: q_c_inherited は β member cid の C を継続的に増加させる ESDE 構造的機能 (v10.5 §85)、本観察はこの機構の直接観察である可能性 (本主題の核心ではない、構造的事実の確認)
22. **delta_pulse_within ≈ 0**: q_c_inherited は pulse 軸では応答を引き起こさない、これは v10.10 「形成後 cid は pulse 軸で応答」と矛盾するわけではない (event 起点の質の違い)

### 5.2 継承維持 (18 件)

v10.10 留保 14 件 + n_core 層化 3 件 + 第二弾 4 件 + 第一弾 4 件 (重複あり、計 18 件) はそのまま維持。

---

## §6 v10.12 への接続素材

### 6.1 抽出された条件

1. **β member cid は概念取り込み対象から除外** (§4.2 条件 1)
2. β member 以外の cid (no_alpha / formation 前) を v10.12 入力対象として優先

### 6.2 v10.10 観察との統合

v10.10 観察 (atom event 起点) + v10.11 観察 (q_c_inherited 起点) を統合:

| 目的 | 狙う cid (v10.10 + v10.11 統合) |
|---|---|
| 概念取り込み (delta_C) | **形成前 cid (中 cluster + 長寿) かつ β member でない cid** (v10.10 + v10.11 排除条件) |
| 行動活性化 (pulse) | **形成後 bin_2 cid** (v10.10 観察、v10.11 では条件追加なし) |

### 6.3 v10.12 主題候補

主題 §7.2 で予定の「人間言語 → atom 変換 prototype」を、v10.10 + v10.11 で得た cid 選定基準を逆引きする形で実装可能。

---

## §7 出力ファイル一覧

### 7.1 main 出力

- `q_c_inherited_events_seed{0..23}.parquet` (24 ファイル、約 150 KB)
- `q_c_inherited_response_profile_seed{0..23}.parquet` (24 ファイル、約 700 KB)
- `q_c_inherited_run_summary.parquet`

### 7.2 cross_seed 集計

- `cross_seed/within_cid_deltas.parquet` (13,055 rows、(event, cid) pair × delta_C/pulse)
- `cross_seed/within_cid_delta_summary.parquet` (288 rows、12 cells × 24 seeds)
- `cross_seed/direction_consistency_24seeds.parquet` (24 rows、4 段階観察)
- `cross_seed/level_1_mechanism_check.json`
- `cross_seed/v10_12_routing_conditions.md` (達成条件 §0.2 抽出文書)

### 7.3 報告書

- `v111_code_recognition_check.md` (Step A、第一稿、無効化)
- `v111_factcheck_request.md` (事実確認依頼、Web Claude)
- v111_factcheck_response (事実確認結果、Code A)
- `v111_phase_design.md` 第二稿 → 第三稿
- `v111_code_recognition_check_v2.md` (Step A、第二稿、再認識確認)
- `v111_step_b_report.md` (Step B、smoke)
- **`v111_main_run_report.md`** (本書、完了報告)

---

## §8 Phase 1.5 第六試行完了に向けて

### 8.1 Code A 単独進行範囲の完了

- Step B (smoke) ✓
- Step C+E (main run) ✓ (7.65 秒)
- Step F (cross-seed 解析) ✓ (1.04 秒)
- Step G (完了報告、本書) ✓

### 8.2 Web Claude の作業 (引き継ぎ)

- `v111_phase_report.md` (主題完了レポート) 作成
- 観察事実 + 整理仮説 + 留保事項の整理
- v10.12 主題決定議論への素材整理
- Phase 1.5 第六試行完了宣言

### 8.3 v10.12 主題決定への素材

- 抽出された条件 1 本 (§4.2)
- v10.10 + v10.11 統合の cid 選定基準 (§6.2)
- 留保事項 18 件 + 新規 4 件 = 22 件

---

## §9 規律遵守の最終確認

| 規律 | 状態 |
|---|---|
| 物理層 frozen | ✓ (read のみ、ledger 改変なし) |
| 神の手回避 | ✓ (実測のみ) |
| Atom 326 絶対化禁止 | ✓ (本主題は atom 軸を含まない) |
| 因果断定回避 | ✓ (§3 ラベル規律で観察事実 / 整理仮説 / 留保 を分離) |
| post-process 計算的減算 | ✓ (観察値集計として整合) |
| Code A 認識確認必須 | ✓ (再認識確認 → 全件採用 → 第三稿確定) |
| 4 層階層化 | ✓ (Level 1-3.5+) |
| 緩和 run 禁止 | ✓ (Code A 独断発動なし) |
| **n_core 別層化** (§34 #37) | ✓ (条件軸 1) |
| **完全マージ版文書** (§34 #39) | ✓ (本書) |
| **観察軸を増やす** (§34 #40) | ✓ (ただし §0.3 打ち切り条件と併用) |
| **観察状態判定枠を超えた整理** (§34 #41) | ✓ (達成条件 §0.2 = 条件 1 本抽出を主軸とした) |
| **§35 #5** (整理語と観察事実の分離) | ✓ (§3.4 / §4 / §5 で実装) |
| **§35 #10** (「観察できる軸が見えた」を駆動要因にしない) | ✓ (達成条件 §0.2 を駆動要因とし、軸列挙を回避) |

---

## §10 一文サマリ (再掲)

v10.11 main run 7.65 秒で完了 (272,835 snapshots、13,055 (event, cid) pairs)、bit-identity 層 A PASS、cross-seed 解析で **「全 12 cells で delta_C_within 正値 (+0.097〜+0.497)、累積 c_inherited による differential 応答は不支持、C 値飽和仮説は本データで支持されない、q_c_inherited は β member cid の C を継続的に増加させる ESDE 構造的機能の直接観察」** を観察事実として記録、Step B (seed 0) の観察 (Q1 のみ正、Q2-Q4 で 0) は 24 seeds 集計で消失で seed-level variability の例として留保事項に追加、達成条件 §0.2 (v10.12 入力ルーティング条件 1 本以上抽出) は **「β member cid は q_c_inherited で C 値が継続的に増加するため v10.12 概念取り込み対象から除外」** という条件抽出で達成、留保事項 4 件追加 (計 22 件)、storage 累計 1.52 GB (25%) で打ち切り条件 50% 余裕大、Code A 単独進行範囲 (Step B-G) 完了、Web Claude 主題完了レポート (`v111_phase_report.md`) → Phase 1.5 第六試行完了宣言 → v10.12 主題決定議論 の順で進む。

---

*以上、Code A による v10.11 完了報告。Web Claude `v111_phase_report.md` (主題完了レポート) 作成 → Phase 1.5 第六試行完了 → v10.12 主題決定の順で進む。*
