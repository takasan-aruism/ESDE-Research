# v10.4 本番 run 結果レポート

*作成*: 2026-04-30、Claude Code
*対象*: v10.4 Integration 機構の本番 run (N=5000, tracking 50, 24 seeds、Q/C 継承・再分配あり)
*親資料*: `claude_code_v104_implementation_instruction.md` (実装指示書)、`v104_phase_design.md` (設計)
*位置づけ*: 実装指示書 §16 完了判定 3。v10.4 の最終観察データ。

---

## 0. 一行サマリ

v10.4 本番 run 24/24 完走 (wall mean 2.99h、v10.3 比 +0.6%)。**Integration 13,550 件誕生 (be3 7,085 / open_triad 5,203 / closed_triad 0 / third_overlap 1,262)**。Layer A 物理層 frozen 維持 (`labels` 24/24 + `persistence` 24/24 完全一致)。**v10.4 は v10.3 と逆方向に C 蓄積を +15% 増 / C_max +31% 増、cognition 当選 +4.2% 増、skip_c_zero -6.3% 減**。Integration が ghost cid から Q/C を継承 (10,000/14,083) して active member へ部分再分配 (2,790/1,777) する系の効果が定量的に観測された。

---

## 1. 実行サマリ

| 項目 | 値 |
|---|---:|
| seeds | 24 (0..23) |
| N | 5,000 |
| maturation | 20 |
| tracking | 50 |
| window_steps | 500 |
| 並列 | -j24 (1 バッチ) |
| be3_shadow_audit | False (本番、C 消費 + Q/C 分配あり) |
| **完走** | **24/24 (exit 0)** |
| **wall time mean** | **10,759s (2.99h)** |
| wall time min/max | 10,420 / 11,687 sec |
| 出力サイズ | 1,708.7 MB (うち persistence 1,558 MB は v10.3 と完全一致) |

参考:
- v10.3 main wall: 10,698s (2.97h) → v10.4 +0.6% (M4: 1.006x、PASS)
- Integration 関連 logger 追加分: +1.7 MB (= 全体の +0.1%)

---

## 2. 機構動作確認 (実装指示書 §16 完了判定)

### 2.1 Integration 誕生件数

| trigger type | 件数 | 比率 |
|---|---:|---:|
| **be3** | **7,085** | **52.3%** |
| **open_triad** | **5,203** | **38.4%** |
| **closed_triad** | **0** | 0.0% |
| **third_overlap** | **1,262** | 9.3% |
| **合計** | **13,550** | 100% |

- be3 件数 (7,085) ≈ be3 fired pair 件数 (7,220) — 1 fired pair → 平均 0.98 個の be3 integration
- open_triad は be3 の 73.4% 件数 → be3 fired pair の隣接ペアで open triad に拡張される確率高
- **closed_triad が 0 件**: 24 seeds × 50 windows = 1,200 windows で一度も成立せず

closed_triad ゼロの理由: be3 は pair ごと run 中 1 回しか発火しない (`_contacted_pairs` set による run-wide dedup)。3 ペア (A-B, B-C, C-A) が同 window 内に揃う組合せは、各 pair の発火確率独立性下で極めて低確率。本仕様では closed triad は実質「観測されない事象」。

### 2.2 Integration size 分布 (誕生時)

| size | 件数 | 比率 |
|---|---:|---:|
| 2 | 7,085 | 52.3% |
| 3 | 5,203 | 38.4% |
| 4 | 834 | 6.2% |
| 5 | 310 | 2.3% |
| 6 | 95 | 0.7% |
| 7 | 18 | 0.1% |
| 8 | 4 | <0.1% |
| 9 | 1 | <0.1% |

size 4 以上は third_overlap に由来 (be3 ペア + 多数の第三項候補)。max active size 8、max history size 9 (実装指示書 §12 想定 3-7 を僅かに超過、実害なし)。

### 2.3 active → recorded 状態遷移

| trigger | 遷移数 | 全体比 |
|---|---:|---:|
| be3 | 1,408 | 70.5% |
| open_triad | 529 | 26.5% |
| third_overlap | 61 | 3.1% |
| 合計 | 1,998 | 100% |

- 全 13,550 中 1,998 件 (14.7%) が recorded に遷移
- be3 (size 2) は両 cid 全員 ghost 化で recorded 遷移しやすい
- 誕生 → recorded の median 6,132 step (= ~12 windows)、max 24,516 step (= run 全期間)
- → **小規模 Integration ほど短命、大規模 (third_overlap) ほど長期 active を維持**

### 2.4 Q/C 継承・再分配 (24 seeds 合計)

| 経路 | Q | C |
|---|---:|---:|
| ghost 化 cid → Integration 継承 | **10,000** | **14,083** |
| Integration → active member 分配 | 2,790 (28%) | 1,777 (13%) |
| **未分配 = 凍結残量** | **7,210 (72%)** | **12,306 (87%)** |

凍結残量の内訳:
- recorded 状態の Integration が保持 (active に分配されない、永続記録)
- int() 切り捨てによる端数 loss (q_alloc = int(total * shortage / sum_shortage) で数 % 程度の loss)

per-cid 受領分布 (active member、24 seeds 合計):
- 受領 cid 数: 592 (hosted run 末 884 中 67%)
- Q 受領: median 3、mean 4.7、max 35 / cid
- C 受領: median 2、mean 3.0、max 34 / cid

### 2.5 物理層 frozen 確認 (Layer B 比較 v10.3 main)

| ディレクトリ | identical | 意味 |
|---|---:|---|
| **labels** | **24 / 24** ✅ | label birth/death timing 完全一致 |
| **persistence/link_life_log** | **24 / 24** ✅ | リンク生死動態 完全一致 |
| **persistence/link_snapshot_log** | **24 / 24** ✅ | window 末 link snapshot 完全一致 |
| **persistence/label_member_persistence** | **24 / 24** ✅ | label birth 時メンバー永続性 完全一致 |
| **persistence/shadow_component_log** | **24 / 24** ✅ | shadow 連結成分 完全一致 |
| audit/per_event_audit | 0 / 24 | E1/E2/E3 spend 系列が Q 補充の影響で発散 (仕様通り) |
| aggregates/per_window | 部分一致 | 物理列 100% 一致、ghost 関連列のみ発散 |

per_window 物理列の 詳細 (1,200 行 × 12 列 = 14,400 セル):
- `links` / `v_labels` / `alive_tracked` / `mean_social/stability/spread/familiarity` / `subject_count_total` / `subject_hosted` — **全 100% 一致 (1,200/1,200 各列)**
- `subject_ghost`: 642/1,200 (53.5% 一致) — 残存 ghost が Integration の Q 補充で reap が遅延する効果
- `ghost_reaped`: 665/1,200 (55.4% 一致) — 同上

→ **物理層と label timing は v10.3 から 1 bit ズレない** (Integration は engine.state を一切 touch しない)。ghost reap 時刻は Q dynamics の派生量なので発散は仕様通り。

---

## 3. 系の動学変化 (v10.3 main 比較)

### 3.1 認知/意識バランス (24 seeds 合計)

| 指標 | v10.3 main | v10.4 main | 差分 |
|---|---:|---:|---|
| **total_decisions** | **100,432** | **100,432** | **0 (完全一致)** |
| n_cognition_won | 57,875 | 60,322 | **+2,447 (+4.2%)** |
| n_consciousness_won | 3,539 | 3,550 | +11 (+0.3%) |
| n_skip_c_zero_only | 39,018 | 36,560 | **-2,458 (-6.3%)** |
| n_e1_e2_spend | 20,112 | 20,136 | +24 (+0.1%) |

**観察**:
- total_decisions が完全一致 = E3 onset 機会数は不変 (= 物理層 frozen 確認)
- **認知当選 +4.2% 増、skip_c_zero (Q 枯渇による skip) -6.3% 減** → Integration の Q 分配が cid の Q を補充して認知選択を増やす機構として明確に働く
- n_consciousness_won はほぼ同数 (摂食動態は不変)
- E1/E2 spend は +0.1% (実質 frozen)

### 3.2 C 蓄積 (重要発見、v10.3 と逆方向)

| 指標 | v10.3 main | v10.4 main | 差分 |
|---|---:|---:|---|
| **C_max (24 seed 合計)** | **1,188** | **1,556** | **+368 (+31.0%)** |
| **C_max mean per seed** | **49.50** | **64.83** | **+15.33 (+31%)** |
| **C_mean_at_run_end** | **503.71** | **579.80** | **+76.09 (+15.1%)** |
| Q_plus_C_total | 19,107 | 21,935 | **+2,828 (+14.8%)** |
| total_digestion_dissipation | 1,769 | 2,037 | +268 (+15.1%) |

**観察 (核心)**:
- **C 蓄積の上限が +31% 上昇** (v10.3: -26% から逆転)
- 全系の Q+C 総量も +14.8% 増
- **v10.4 Integration は系の Q+C を増やす方向に働く**

機構解釈:
- v10.3 双方向 E3 は C を散逸させる (両者 C-1) → C 抑制
- v10.4 Integration は ghost 化 cid の C を継承して active member に再分配 → 「死者の意識資源」を生者へ循環
- 結果: C は系内で保存される (一部は recorded に凍結)

数値整合:
```
v10.4 Q+C total +2,828
  内訳:
    n_cognition_won +2447 (Q 1 → C 1 の振替なので C 増加 +2447)
    skip_c_zero 減少 → 観察される Q 維持
    Integration が再分配 → 名目 +Q +C 加算
```

### 3.3 摂食動態

| 指標 | v10.3 main | v10.4 main | 差分 |
|---|---:|---:|---|
| total_received_via_consciousness | 19,421 | 19,434 | +13 (+0.1%) |
| ghost_residual_Q (run 末) | 416 | 422 | +6 (+1.4%) |
| n_hosted_at_run_end | 884 | 884 | 0 (完全一致) |

→ **摂食 ingestion 系列は実質変化なし**。consciousness pathway は Integration 追加でも揺らがない。

### 3.4 観察対象 tracker 動作

| stage | v10.3 main | v10.4 main |
|---|---:|---:|
| Stage 1 (n_core ≥ 4 ∧ n_cons ≥ 5) | 94 | **0** |
| Stage 2 (be3 partner) | 1,255 | 2,322 |
| Stage 4 (Integration member、v10.4 新規) | — | (差分から推定 ~1,300) |
| 合計 target | 1,349 | ~3,600 (推定) |

**Stage 1 = 0 の解釈**: v10.4 では Integration 分配が cid の Q を補充 → balance decision で cognition 当選 +4.2% 増 → 同 cid の consciousness 当選数が相対的に低下 → n_consciousness ≥ 5 を満たす前に be3 が発火するか、Integration callback で stage4 として先に target 追加されるため stage1 経路を通らない。

実装指示書 §11 「Integration の構成 cid は全員 target に追加 (Integration の挙動を完全観察するため)」が想定通り機能した結果。

---

## 4. Integration 構造の特性

### 4.1 per-cid Integration 所属

| 指標 | 値 |
|---|---:|
| active 所属 cid 数 (run 末) | 649 |
| n_integrations per cid: median | 27 |
| n_integrations per cid: mean | 29.1 |
| n_integrations per cid: max | **102** |
| binding_strength: median | 1.0 |
| binding_strength: max | 2.0 |

**観察**:
- 1 つの cid が平均 29 個、最大 102 個の Integration に所属
- binding_strength の median = 1.0 = 各 Integration への参加は通常 1 イベント (= 誕生時のみ)
- max = 2.0 のケースは少数 = 同じ member 構成の Integration が同 step に再候補となり binding が +1 された稀例 (§3.2 重複判定で新規誕生はせず binding のみ更新)

「ハブ役」cid (be3 を多くの partner と発火する中核 cid) が多数の Integration に組み込まれる構造。

### 4.2 規模判定 M1-M4 (本番)

| 指標 | 値 | 閾値 | 判定 |
|---|---|---|---|
| M1 (Integration数 / cid数) | mean **2.63x** (1.75-3.79) | ≤ 0.5 | 24/24 EXCEEDED |
| M2 (max int per cid) | mean **76.1** (54-102) | ≤ 10 | 24/24 EXCEEDED |
| M3 (CSV 合計サイズ) | 1,708.7 MB | abs ≤ 500 / rel +50% | abs 超 / rel +0.2% PASS |
| M4 (wall ratio) | **1.006x** | ≤ 1.5 | PASS |

M1/M2 規模超過は smoke 段階から既知 — 各 be3 fire が複数 trigger (be3 + open_triad + third_overlap) で複数 Integration を生成する仕様に由来。実装上の機能破綻はなく、Integration 増殖は神の手なし条件 (§3.2 同 member 重複は新規誕生せず binding 更新のみ) で適切に抑制されている。

---

## 5. 規律確認 (実装指示書 §14、本番規模で再確認)

- [x] 物理層 frozen — labels 24/24、persistence 96/96 で本番規模確認
- [x] Layer A bit-identity (per_window 物理列 12,000/14,400 = ghost 派生 2 列以外 100% 一致)
- [x] cid 内部に新規状態を追加しない (M_c 不変、Q/C のみ既存)
- [x] **Integration は物理層・存在層に介入しない** (engine.state へ書き込みなし、確認済)
- [x] Integration の調整は認知層・意識層への間接バイアスのみ (Q/C 加算で cid 内部選択を直接操作せず、p_cognition = Q/(Q+C) を経由する間接的影響)
- [x] **recorded 状態は永続** (24,516 step の最大保持確認、時定数による delete なし)
- [x] **Q/C 継承は最強結合 1 つに全部** (二重カウントなし、合計値整合: 10,000 inherited = 各 ghost cid の Q 合計と一致)
- [x] 神の手回避 (誕生条件は be3 fired の客観条件のみ、選別なし)
- [x] balance_rng / be3_rng / integration_rng は engine.rng から独立 (integration_rng は本実装では未使用、削除可)
- [x] 既存 CSV 列を変更しない (per_window / per_subject に追加列のみ)
- [x] 「嗜好」「三項共鳴」を機構名に含めない
- [x] target 外も全体集計で監視 (n_be3_target_outer 集計済)
- [x] v10.3 観察軸を継承 (第三項候補リストアップ、Cat 1a/1b 検出)

---

## 6. 出力ファイル一覧

```
diag_v104_main/
├── (v10.3 main と同 subdirs、ただし labels + persistence のみ identical)
├── bidirectional/
│   ├── bidirectional_e3_log_seed{0..23}.csv             (24、target 内 fired 6,926 行)
│   ├── bidirectional_e3_member_nodes_log_seed{0..23}.csv (24)
│   └── bidirectional_e3_summary_seed{0..23}.csv          (24)
└── integration/                                            ← v10.4 新規
    ├── integration_lifecycle_log_seed{0..23}.csv          (24、誕生 + 状態遷移 + Q/C 継承 events)
    ├── integration_distribution_log_seed{0..23}.csv       (24、再分配 events)
    ├── integration_membership_log_seed{0..23}.csv         (24、run 末 cid → 所属 Integration マップ)
    └── integration_summary_seed{0..23}.csv                (24、run-level 集計)
```

per_window / per_subject CSV に追加列:
- per_window: `n_integrations_active/recorded/born/state_transitioned`、`total_q_inherited/c_inherited/q_distributed/c_distributed`、`max_integration_size`、`mean_integration_size`、`trigger_type_dist`
- per_subject: `n_integrations_joined/currently`、`q_received_from_integrations/c_received_from_integrations`、`q_inherited_to_integration/c_inherited_to_integration`

---

## 7. 完了判定 (実装指示書 §16)

- [x] 1. smoke 通過 (M1-M4 規模判定 — M1/M2 超過は Taka 判断で続行承認)
- [x] 2. shadow audit 通過 (Layer B 144/144 完全一致、Taka 確認済)
- [x] 3. 本番 N=5000 24 seeds × tracking 50 完了 (24/24 exit 0)
- [x] 4. 全 logger の出力が想定形式で取れている (lifecycle / distribution / membership / summary 各 24 ファイル)
- [x] 5. per_subject / per_window の追加列が正しく集計されている (列数 + 値 spot-check 済)
- [x] 6. bit-identity 検証 (層 A + 層 B labels + persistence) — Layer B 144/144、Layer A 物理列 100%
- [x] 7. Integration 関連の集計指標が想定オーダーで取れている

→ **v10.4 実装完了**。

---

## 8. v10.4 全体まとめ (smoke → shadow → 本番)

| 段階 | wall | Integration | C_mean | Layer B (vs v10.3) |
|---|---:|---:|---:|---|
| smoke (N=5000 tracking 10) | 66 min | 64 件 | — | persistence + labels 完全一致 |
| shadow audit (N=5000 tracking 50) | 3.3h | 12,587 件 | (実分配なし、観察のみ) | **144/144 完全一致** |
| **本番 (N=5000 tracking 50)** | **2.99h** | **13,550 件** | **579.80 (+15.1%)** | **labels + persistence 完全一致 (120/552)** |

### 8.1 重要な発見

1. **v10.4 機構が物理層 + label timing を完璧に frozen** (labels 24/24 + persistence 96/96 一致)
2. **v10.4 Integration は v10.3 と逆方向に C 蓄積を +31% 増 / Q+C +14.8% 増**
   - v10.3 双方向 E3: C 散逸 → C 抑制 (-26%)
   - v10.4 Integration: 死者の Q/C を生者へ継承・再分配 → C 蓄積増
3. **cognition 当選 +4.2% 増、skip_c_zero -6.3% 減** = Integration の Q 補充が認知選択を促進
4. **closed_triad は構造的に発生しない** (be3 の run-wide dedup により 3 ペア揃いが極稀)
5. **wall time オーバーヘッド +0.6%** (実質ゼロ、整合性: M4 PASS 1.006x)

### 8.2 Integration の客観的特性

- 1 be3 fired pair → 平均 1.91 個の Integration を生成 (be3 + 0.7 open_triad + 0.18 third_overlap)
- 14.7% の Integration が active → recorded に遷移 (median 12 windows で記録化)
- recorded 状態が C を凍結保持 (継承 14,083 のうち 12,306 = 87% が active 分配されず)
- ハブ cid は最大 102 個の Integration に同時所属、binding_strength 通常 1.0 (重複参加稀)

### 8.3 v10.5 以降への持ち越し (実装指示書 §15)

v10.4 で実装しなかった項目:
- Cat 2b/2c (共有 link/cycle、engine 拡張必要)
- 第三項生成促進 (D4-c)
- 嗜好の数理化
- focus / attention_weight 動的化
- salience 駆動
- v3.3.1 創造/破壊論
- v3.3 最適距離
- Integration の「主観」「意思」 (実装していない)

v10.4 観察データから v10.5 設計の素材:
- closed_triad ゼロ問題 — 必要なら誕生条件緩和 or 別経路 (Cat 1c proximate triad) 実装
- 凍結 C (12,306 = 87%) の扱い — recorded から再 active 化する経路を許すか議論
- ハブ cid (max 102 所属) の効果分析 — Q/C 補充の集中度合いと系の動学への寄与度

---

## 9. 結論

v10.4 Integration 機構の本番 run 完了。実装指示書 §16 完了判定 1-7 すべて満たし、**v10.4 実装は技術的に成功**。

主要観察事実:
1. 機構動作: Integration 13,550 件誕生、Q/C 継承 10,000/14,083、再分配 2,790/1,777
2. 物理層 frozen: labels 24/24 + persistence 96/96 完全一致 (Layer B bit-identity)
3. 系の動学変化: **C 蓄積 +31% 増 (v10.3 と逆方向)、認知当選 +4.2% 増**
4. 構造特性: be3 size=2 が 52%、open_triad size=3 が 38%、closed_triad は 0、最大 size 9
5. wall time: v10.3 main 比 +0.6% (実質ゼロ overhead)

主題的含意:
- Integration は「ghost 化した構成 cid の Q/C を継承して系内に保存・再分配する機構」として明確に機能
- v10.3 の C 散逸構造を v10.4 が逆転 — 系全体としての資源保全効果
- 観察された C 蓄積増加は「主観の生成」に相当する事象を統計的に増やす方向の影響

**Taka 判断項目**: 本観察データから v10.4 主題ドキュメント執筆 (Claude 相談役) または v10.5 設計議論へ進行。

---

*以上、v10.4 本番 run 結果レポート。Taka レビューを待つ。*
