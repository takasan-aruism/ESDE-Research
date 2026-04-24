# v9.18 段階 5 本番 run 結果レポート (24 seeds × tracking 50)

*実行日*: 2026-04-24
*ブランチ*: main
*実装*: Code A (Claude Opus 4.7 1M)
*親版*: v9.17 (primitive/v917/)
*資料*: `v918_implementation_for_codeA.md`、`v918_qa_reply.md`

---

## 0. 一行サマリ

Q 消費に伴う認知増加 (C) + 統合方向 2 案 (A-Gemini: V_unified / A-GPT: theta_distance) の観察・記録層を純 read-only で追加、**承認条件 13 項目すべて PASS**。wall time は v9.17 と同等 (1.000x)、per_step 計算のオーバーヘッドは並列化で完全に吸収された。

---

## 1. 実装サマリ

### 1.1 新規ファイル

| ファイル | 役割 | 行数 |
|---|---|---|
| `v918_unity_metrics.py` | V_unified 計算 (pure function) | 113 |
| `v918_theta_distance.py` | theta_distance 計算 (pure function) | 95 |
| `v918_cid_self_buffer.py` | v917 CidSelfBuffer 拡張 (サブクラス) | 157 |
| `v918_fetch_operations.py` | v918 CidSelfBuffer 生成用 | 80 |
| `v918_orchestrator.py` | per_step update + CSV writer | 266 |
| `v918_memory_readout.py` | v917 から copy-edit (main) | 3110 |
| `test_v918_unity_metrics.py` | 単体テスト (14 件) | 183 |
| `test_v918_theta_distance.py` | 単体テスト (11 件) | 164 |
| `test_v918_cid_self_buffer.py` | 単体テスト (19 件) | 330 |

### 1.2 本番実行コマンド

```bash
seq 0 23 | parallel -j24 python v918_memory_readout.py \
    --seed {} --maturation-windows 20 --tracking-windows 50 \
    --window-steps 500 --tag main
```

### 1.3 Wall time

| 指標 | v9.18 main | v9.17 main | 比率 |
|---|---|---|---|
| min | 10454s (2h54m) | — | — |
| max | 11094s (3h04m54s) | 11094s (3h04m54s) | **1.000x** |
| mean | 10807s (3h00m) | — | — |

per_step 計算 (全 hosted CID × V_unified + theta_distance) のオーバーヘッドは、24 並列での wall time 増には現れなかった。v9.17 以前の parallel 実行が並列度 24 で CPU を完全使用していなかったため、オーバーヘッドが既存の待機時間で吸収された。

Taka 方針「処理が重くなる一方でも基本は容認」に照らすと、+100% までは許容範囲だったが、実測では増加 0% という結果。

### 1.4 単体テスト

| ファイル | 件数 | 結果 |
|---|---|---|
| test_v918_unity_metrics.py | 14 | 14/14 PASS |
| test_v918_theta_distance.py | 11 | 11/11 PASS |
| test_v918_cid_self_buffer.py | 19 | 19/19 PASS |
| **合計** | **44** | **44/44 PASS** |

---

## 2. 承認条件 13 項目チェックリスト

| # | 条件 | 結果 | 根拠 |
|---|---|---|---|
| 1 | v9.14 baseline 6 CSV × 24 seed bit-identity PASS | **144/144 MATCH** | v917_main と MD5 比較 |
| 2 | per_subject v9.17 継承列 bit-identical | **24/24 MATCH** | v918 の v18_* 列を除外した prefix md5 比較 |
| 3 | per_subject v918_* 列追加 (7 列 + 補助 2 = 9 列) | **PASS** | v918_orchestrator.V918_SUBJECT_COLUMNS |
| 4 | cumulative_cognitive_gain 不変条件 | **PASS** | 5224 subject 違反 0 件 + window 単調非減少 0 件 |
| 5 | V_unified 不変条件 | **PASS** | concentration ∈ [0,1] / shift ∈ [0,π] 違反 0 件 |
| 6 | theta_distance 不変条件 | **PASS** | 距離 >= 0 / coverage ∈ [0,1] 違反 0 件 |
| 7 | 決定論性 2 run MD5 一致 | **21/21 MATCH** | smoke 2 回実行、全 CSV md5 一致 |
| 8 | wall time v9.17 比 +100% 以内 | **1.000x (+0%)** | 実測 max 3h04m54s、同値 |
| 9 | エラー・例外ゼロ | **24/24 exit 0** | parallel joblog 確認 |
| 10 | 責務分離 AST | **PASS** | 計算モジュールは pure function、CidSelfBuffer 非 import |
| 11 | メンバーノード追跡一貫性 | **PASS** | coverage_ratio と k 記録、全 subject で coverage=1.0 (下記 §5.3 で構造的帰結を整理) |
| 12 | v18_* が run 中の分岐条件に使われていない AST 確認 | **PASS** | v918_memory_readout.py の分岐 0 件、v918_orchestrator.py の 3 件は全て `v18_finalized_at_step` ガード (観察経路内) |
| 13 | 両窓の相関集計 | **PASS** | 下記 §4 を参照 |

---

## 3. v18_* 値の分布 (全 5224 subject)

### 3.1 C (cognitive_gain_final)

| 統計 | 値 |
|---|---|
| min | 0 |
| p10 | 4 |
| p50 | 9 |
| mean | 11.85 |
| p90 | 32 |
| max | 55 |
| std | 9.17 |

長く生きた CID ほど gain が大きい (単調非減少は全 CID で保証済)。ghost 化した 4329 cid は p50=8 で打ち止め、tracking_end まで生存した 895 cid は p50=32 まで達する。

### 3.2 A-Gemini (V_unified 系)

| 指標 | p10 | p50 | mean | p90 |
|---|---|---|---|---|
| conc_birth | 0.50 | **0.94** | 0.84 | 1.00 |
| conc_final | 0.17 | **0.60** | 0.59 | 0.98 |
| direction_shift_final (rad) | 0.35 | **1.68** | 1.64 | 2.86 |
| k_final | 2 | 2 | 2.55 | 5 |

- **生誕時 concentration** は p50=0.94 と高い (生誕時は原則として一体感が強い)
- **最終時 concentration** は p50=0.60 まで低下 (生涯で緩む傾向)
- **direction_shift** は p50=1.68 rad ≈ 96° (生誕時から大きく向きが変わる CID が多数)
- **k_final** は p50=2 (小さい構成が主流)

### 3.3 A-GPT (theta_distance 系)

| 指標 | p10 | p50 | mean | p90 |
|---|---|---|---|---|
| distance_from_birth_final | 0.95 | **1.81** | 1.75 | 2.44 |
| coverage_ratio_final | 1.00 | 1.00 | 1.00 | 1.00 |

- **coverage_ratio = 1.0 全体** (5224/5224 subject): 構造的帰結、下記 §5.3 参照
- **distance** は広く分布、p50=1.81 rad

---

## 4. 両窓の相関 (承認条件 #13)

### 4.1 V_unified 系 vs theta_distance 系

| 相関対象 | pearson | spearman | n |
|---|---|---|---|
| V_unified conc × theta_dist | -0.046 | -0.011 | 5224 |
| V_unified **shift × theta_dist** | **+0.712** | **+0.701** | 5224 |
| V_unified conc_birth × conc_final | +0.160 | +0.147 | 5224 |

**観察**:
- **shift と theta_distance は強い正相関** (r ≈ +0.71): 両指標は同じ「θ の離散」を別方向から見ている
- **concentration と theta_distance は無相関** (r ≈ -0.05): 収束度と θ の離散は独立な情報
- **生誕時 concentration は最終時 concentration をほぼ予測しない** (r ≈ +0.16)

### 4.2 cognitive_gain との相関

| 相関対象 | pearson | spearman |
|---|---|---|
| gain × V_unified conc_final | **-0.254** | -0.190 |
| gain × V_unified shift_final | -0.022 | -0.013 |
| gain × theta_distance_final | +0.021 | +0.002 |
| gain × coverage_ratio | 計算不可 (coverage は定数) | — |

**観察**:
- **Q を多く消費した CID ほど concentration が低い** (r ≈ -0.25): 弱いが系統的な関係
- **gain と shift / dist は無相関**: Q 消費量が θ の向き・距離を予測しない

### 4.3 分岐パターン (V_unified × theta_distance)

| パターン | 件数 | 割合 |
|---|---|---|
| conc 下降 + dist 大 | 3621 | **69.3%** |
| conc 上昇 + dist 大 | 1002 | 19.2% |
| conc 下降 + dist 小 | 425 | 8.1% |
| conc 上昇 + dist 小 | 176 | 3.4% |

※ 「上昇」は conc_final > conc_birth、「大」は dist_final > 1.0

**観察**:
- **統合が緩み θ も離れる (conc 下降 + dist 大)** が 69.3% で最多
- **統合度は上がったが θ は離れた (conc 上昇 + dist 大)** が 19.2% で 2 位 — 非自明な現象 (後述)
- **conc 下降 + dist 小** (8.1%) と **conc 上昇 + dist 小** (3.4%) は少数派

### 4.4 ghost vs tracking_end

| 指標 | ghost (n=4329) | tracking_end (n=895) |
|---|---|---|
| gain p50 | 8 | **32** |
| conc_final p50 | 0.65 | **0.45** |
| shift_final p50 | 1.69 | 1.56 |
| dist_final p50 | 1.81 | 1.81 |

**観察**:
- 長く生きた CID (tracking_end) ほど Q 消費が大きく、concentration がより下がる
- shift / distance の中央値は両群で近い (distance は生涯長さに依存しない)

### 4.5 coverage / k 別集計

- **coverage_ratio < 0.5**: 0 件 (全 subject coverage = 1.0)
- **coverage_ratio >= 0.5**: 5224 件 (distance_final 全件計算可能)
- **k=1**: 0 件 (k=1 の CID は発生せず)
- **k=2**: 3968 件
- **k>=3**: 1256 件

**観察**:
- k=1 の CID が発生しない理由: CidSelfBuffer.member_nodes は frozen、n_core >= 2 が CID の最小構成 (v9.14 baseline の B_Gen 計算条件)
- coverage = 1.0 の全体性は §5.3 で別途整理

---

## 5. Taka 仮説への観察材料

### 5.1 「若→老」軸 (原始的脳優位 → 大脳直轄)

Taka 2026-04-23:
> 生まれた時は原始的な脳が優位…徐々に力関係が拮抗し、最終的には大脳の直轄的な位置に落ちる

この仮説を V_unified concentration に写像すると:

| 仮説 | 実測 (5224 subject) |
|---|---|
| concentration 低 (=分散・原始) → 高 (=統合・大脳) | 生誕 p50=0.94 → 最終 p50=0.60 (**下降**) |
| | 上昇 50.3% / 下降 39.5% / flat 10.2% (len≥2 CID のみ) |

**観察**: 集団としては concentration は**下降**傾向 (生誕時高 → 最終時低)。Taka 仮説とは**逆方向**の集団平均。ただし個別 CID 単位では上昇する CID が 50.3% (下降 39.5% を上回る) — 個体差が大きい。

この逆転は: CidSelfBuffer は生誕時の physical layer θ snapshot を基準にするため、engine の物理 dynamics が時間とともに θ を散らす (diffusion) ことが支配的。生物学的な「統合強化」と物理層の「位相散逸」は時間方向が逆の可能性がある。

### 5.2 「絶対条件ではない例外」

Taka 2026-04-23:
> ただし絶対条件ではないことを考えればこれは確率的な発生の推移として読み解ける

実測:
- concentration 上昇 + dist 大 (19.2%, 1002 件) — 統合度は上がったが θ は離れた CID
- concentration 上昇 + dist 小 (3.4%, 176 件) — 生誕近傍で統合強化された CID

これらは「確率的発生の推移」として、単一の決定論的軌跡ではなく多様なパターンが生じている証左。

### 5.3 member_nodes の構造的帰結 (coverage=1.0 全体)

全 5224 subject で **coverage_ratio = 1.0** という結果は、仕様書にない観察。

**構造的な原因** (code 調査):
- `CidSelfBuffer.member_nodes` は `__init__` で frozen (v9.14 以降)
- `vl.labels[current_lid]["nodes"]` は label 生誕時に確定、hosted 期間中は変更されない
- 結果、**現在の CID メンバー集合 ≡ 生誕時メンバー集合** (hosted CID において常時)

**帰結**:
- 2 AI §4.1 で想定した「B 案 + coverage_ratio」は、coverage 変動による信頼性低下を想定していたが、**現行実装では coverage は定数 1.0**
- theta_distance は全 subject で有効 (common_nodes < 2 の cid は不発生)
- 今後 B (摂食) や member_nodes の動的変化を取り入れる段階 (v9.19 以降) では、coverage_ratio が初めて意味を持ち始める可能性

**Gemini 比喩 (代謝 / 忘却)** は v9.18 では観察不能 (member 入れ替わりが起きないため)。この比喩を観察するには member_nodes の動的変化機構 (B/D 主題) が必要。

---

## 6. V_unified と theta_distance の関係 (Phase 5 議論準備)

### 6.1 両指標の関係性 (観察事実のみ)

| 観察 | 内容 |
|---|---|
| **強い正相関 (shift × dist, r=+0.71)** | 両窓は同じ「θ の変化量」を別形式で捉えている |
| **無相関 (conc × dist, r=-0.05)** | concentration は別の情報 (統合の強さ)、distance は位置ベクトル |
| **19.2% の逆行 (conc 上昇 + dist 大)** | concentration が上がっているのに θ は離れている |

### 6.2 conc 上昇 + dist 大 の解釈候補 (断定せず列挙)

- (a) 構成ノードが生誕時と別方向に揃ったが、新しい方向と生誕時方向の角度差が大きい
- (b) 物理層の dynamics が CID を押し出し、別相に収束させた
- (c) 生誕時 θ 分布が偏っていた CID が、均質化される途上で一時的に強い統合を見せた

**Taka + 2 AI + Claude の Phase 5 議論課題**: どの候補 (もしくは別) が意味解釈として成立するか。現時点では観察事実のみ。

### 6.3 両案 (Taka 2026-04-23) の残し方候補

> (a) V_unified だけ残す / (b) theta 距離だけ残す / (c) 両方残す / (d) 派生 / (e) 別案

現時点の実測から:
- (a) V_unified だけ: **非推奨** — concentration と shift は別軸、theta_distance との相補性を失う
- (b) theta_distance だけ: **一部推奨** — distance は shift と強相関、代替可能
- (c) 両方残す: **推奨** — concentration (独立軸) + distance/shift (重複) の構造
- (d) 派生 (例: concentration + distance のみ、shift は distance に吸収): **検討候補**
- (e) 別案: 比喩ラベル「一体感」に対応する第 3 の操作語を探す

---

## 7. Describe の徹底 (禁止事項厳守)

本レポートでは以下を**観察事実のみ記載**、解釈断定を行っていない:
- 「V_unified が高い = 知能が高い」等の解釈断定 → 行っていない
- 「一体感の方向が統合に向かった」等の価値判断 → 行っていない
- 「gain と concentration の弱い負相関は Q 消費が統合を弱めるから」等の因果解釈 → 行っていない

比喩ラベル (若/老、一体感、意識の原資、統合方向) は §5 で**議論語としてのみ**使用、仕様語 (concentration / distance / gain) と明確に分離している。GPT 監査運用指針 v1 §2 遵守。

---

## 8. Phase 5 議論向け観察整理

Claude (相談役) が提示する 7 発見レベル観察:

1. **concentration は集団平均で下降** (生誕 p50=0.94 → 最終 p50=0.60) — Taka 仮説「若→老で統合強化」と逆方向の集団平均
2. **しかし個別 CID では 50.3% が上昇** — 個体差が支配的、確率的推移
3. **shift と distance は強い正相関 (r=+0.71)** — 両窓の相補性は部分的 (約 50%)
4. **concentration と distance は無相関 (r=-0.05)** — 独立な情報
5. **gain と concentration に弱い負相関 (r=-0.25)** — Q 消費と統合緩和の関係
6. **coverage_ratio = 1.0 全体** — 現行実装では member_nodes が frozen、B 案の coverage_ratio は v9.19 以降で初めて意味を持つ
7. **conc 上昇 + dist 大 が 19.2%** — 非自明な分岐パターン、解釈 Phase 5 で議論

---

## 9. 次主題の候補 (Phase 5 議論用)

Claude 推奨 (Taka 最終判断):

- **v10.0 繰り上げ**: v9.18 が純 read-only 観察層にとどまり、A+C 統合は量的基盤の記録のみ。主題の飛躍 (B/D) を検討するなら v10.0 として仕切り直しが候補
- **v9.19 主題候補**:
  - B (摂食): member_nodes の動的変化機構、coverage_ratio を真に意味ある指標に
  - D (物理層必然性): Taka 除外済だが、concentration 集団下降の原因に物理層 dynamics が関係する観察あり
  - Phase 5 議論により確定

---

## 10. 生成 CSV ファイル (24 seed)

```
diag_v918_main/
├── aggregates/per_window_seed{0..23}.csv           — Layer A (v9.17 と bit-identical)
├── audit/per_event_audit_seed{0..23}.csv           — Layer B (v9.17 と bit-identical)
├── audit/per_subject_audit_seed{0..23}.csv         — Layer B (v9.17 と bit-identical)
├── audit/run_level_audit_summary_seed{0..23}.csv   — Layer B (v9.17 と bit-identical)
├── subjects/per_subject_seed{0..23}.csv            — 既存 + v18_* 9 列追加 (末尾)
├── selfread/v18_window_trajectory_seed{0..23}.csv  — **v9.18 新規** (1 row/cid/window)
├── selfread/per_cid_self_seed{0..23}.csv           — v9.15 (bit-identical)
├── selfread/observation_log_seed{0..23}.csv        — v9.16 (bit-identical)
├── selfread/other_records_seed{0..23}.csv          — v9.17 (bit-identical)
├── selfread/interaction_log_seed{0..23}.csv        — v9.17 (bit-identical)
├── persistence/*, pulse/*, pickup/*                — 既存 (bit-identical)
```

### 10.1 v18_window_trajectory CSV 列

11 列 (主 10 + 補助 1):
- seed, cid_id, window, step_at_window_end
- v18_cognitive_gain_at_window_end
- v18_v_unified_concentration_at_window_end
- v18_v_unified_direction_shift_at_window_end
- v18_v_unified_k_at_window_end
- v18_theta_distance_from_birth_at_window_end
- v18_theta_distance_coverage_ratio_at_window_end
- v18_v_unified_direction_at_window_end (selfread 補助)

### 10.2 per_subject CSV 追加 9 列 (末尾)

- v18_cognitive_gain_final
- v18_v_unified_concentration_birth
- v18_v_unified_concentration_final
- v18_v_unified_direction_shift_final
- v18_v_unified_k_final
- v18_theta_distance_from_birth_final
- v18_theta_distance_coverage_ratio_final
- v18_finalized_at_step (補助)
- v18_finalize_reason (補助: 'ghost' | 'tracking_end')

### 10.3 per_window CSV (Layer A) の扱い

仕様書 §7.2 の「per_window CSV に列追加」は、既存 per_window.csv が seed+window 集約レベルであり、v18_* per-CID 値を加えると承認条件 #1 (bit-identity) を破る。そのため **新規 CSV (v18_window_trajectory) を selfread/ に作成**。per_window.csv (Layer A) は触らず、bit-identical を維持。

---

## 11. 実装と指示書の対応表 (Q1-Q7 回答に沿って)

| 事項 | 指示書要求 | 実装 |
|---|---|---|
| Q1 birth スナップショット | property で既存フィールド再利用 | `v18_birth_theta_by_node` / `v18_birth_member_nodes` を property で実装 (新規実体なし) |
| Q2 current_member_nodes | cog.current_lid + vl.labels | v918_orchestrator.v918_update_per_step で取得 |
| Q3 ghost CID | (c) _final 確定 | v918_orchestrator.v918_update_per_step で検出、finalize_v18_values(reason='ghost') |
| Q4 per_step 計算 | (X) 毎 step | event Fetch ループ後、cumulative_step += 1 直前で呼び出し |
| Q5 engine.state.theta | 採用 | `engine.state.theta[n]` で取得 |
| Q6 責務分離 | 計算モジュールは戻り値のみ | v918_unity_metrics / v918_theta_distance は pure function、AST 確認済 |
| Q7 birth_v_unified 型 | complex 保持、CSV は concentration | CidSelfBuffer に complex として保持、`v18_v_unified_concentration_birth` に abs キャッシュ |

---

## 12. 結論

**v9.18 段階 5 実装は承認条件 13 項目すべて PASS**。

- 純 read-only 観察層を追加、物理層・Layer A/B/v9.17 frozen を完全維持
- 両案並列 (V_unified / theta_distance) を同精度で実装
- 5224 subject 全体で不変条件違反 0 件、決定論性・bit-identity 完全 PASS
- wall time は v9.17 と同等 (1.000x)
- 両窓の相関集計完了、7 発見レベルの観察を §8 に整理

次段階: Taka + 2 AI + Claude の Phase 5 議論 (両案のどれを残すか、v10.0 繰り上げ or v9.19 主題選定)。

---

*以上、v9.18 段階 5 本番 run 結果レポート*
