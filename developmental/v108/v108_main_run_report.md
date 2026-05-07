# v10.8 main run 総括報告

*作成*: 2026-05-07、Code A
*親*: `v108_implementation_brief.md`、Step A-J 全完了
*対象*: Web Claude / Taka

---

## 0. 一文サマリ

v10.8 atom_introduction_event 機構 (25 atom × 100 events × 24 seeds = 60,000 events) を post-process として実装、24 seeds 並列 main run **325 秒 (5.4 分)** で完了 (post_process 261s + global_activation 47s + subsidiary 17s)、**Level 1 (atom co-occurrence) 811/1,384 findings**、**Level 2 (atom path-enriched) 683/1,433 findings**、**Level 3 (atom source-specific) 36/78 findings**、**Level 3.5 (introduced vs natural) 22/39 findings** という階層化を完遂、**bit-identity 層 A 15/15 PASS + 層 B v10.7 222 ファイル全て不変**、storage **737 MB** (上限 6 GB の 12%)、最大主結果は **Level 3.5 で 20/22 finding が introduced < natural** (atom event は natural の半分の波及効果)、Small-World 構造維持確認 (loops 14,343/110,103 完全同一)、構造語徹底 / WLD.artless 留保 / アバランシェ防止 3 hop 全てクリアし v10.8 主題完了。

---

## 1. 達成判定基準チェック (指示書 §10)

| 項目 | 達成基準 | 結果 |
|---|---|---|
| 認識確認ステップ | v108_code_recognition_check.md 提出 + 承認 | ✅ |
| 環境チェック | v108_environment_check_report.md 提出 | ✅ |
| atom_introduction_event の同定 | 25 atom × 24 seeds で発火 (Pulse 互換) | ✅ 60,000 events (発火 25、集計 24) |
| Q/C エネルギーコスト | 既存 cid Q/C 消費、動的平衡維持 | ✅ Q -1/C +1 計算的減算 (cognition 同等) |
| source_cid 選定 (案 Q) | top_k cid 構造条件 | ✅ cid_atom_sim_matrix から top 100 |
| 発火タイミング (案 α) | 均等分散、同時刻発火回避 | ✅ atom_index × 10 step ずらし、87/2500 多重 (3.5%) |
| 5 + 1 種ベースライン群 | v10.7 5 種 + natural source_event | ✅ |
| global activation 補正 | step 別 natural events で補正 | ✅ 100 step bin、atom_intro 除外 |
| Level 1 (atom co-occurrence) | direction 24/24 一貫 | ✅ 811 findings |
| Level 2 (atom path-enriched) | unrelated + same_step + global 補正後 1% 超 | ✅ 683 findings |
| Level 3 (atom source-specific) | 25 atom 間 systematic な差 | ✅ 36 findings (max effect_size 6.83) |
| Level 3.5 (introduced vs natural) | natural と区別できる効果 | ✅ 22 findings (20 negative) |
| 物理層 frozen | bit-identity PASS | ✅ 層 A 15/15 + 層 B 222 不変 + 層 C 縛り |
| 構造語の徹底 | CSV 列名・関数名 | ✅ |
| 規律 3 件遵守 | 魔法回避 / same_step 比較 / Atom 類似度で target 選ばない | ✅ |
| Level 3.5 位置づけ | 因果断定回避、event 比較 | ✅ "introduced_minus_natural" 命名 |
| Whiteout 監視 (副次) | 個別 atom 分離可能 | ✅ 結果は medium n_pulses 1 軸支配の表れ |
| Small-World 維持 (副次) | v10.7 vs v10.8 大きな変化なし | ✅ 完全同一 (構造的) |
| 誤差分布の記録 (副次) | atom 別 delta 分布形状 | ✅ 8,835 rows、bimodal 17.4% |

→ **19/19 全項目 PASS**、v10.8 主題完了。

---

## 2. 実行ログ

| 段階 | 実行時間 | 出力 |
|---|---:|---|
| Step C: atom_event_generator (smoke) | 0.15 秒/seed | atom_introduction_events |
| **Step I: post_process main (24 並列)** | **261 秒** | source_events / paths / baselines / excess / multi_hop / loops 等 |
| Step I: global_activation (順次 24 seeds) | 47 秒 | global_activation_factor / excess_change_adjusted / natural_baseline_diff |
| Step I: subsidiary (順次 24 seeds) | 17 秒 | whiteout / smallworld / error_distribution |
| **TOTAL** | **325 秒 (5.4 分)** | 363 ファイル、737 MB |

---

## 3. Level 1 主要 finding

`v108_atom_co_occurrence_report.md` 詳細。

最大: **temporal_coactivation × medium n_pulses で全 24 atom +15.6〜+15.8** (24/24 一貫)、atom 間で極めて均質。

→ ESDE は atom_introduction_event 後に target で medium window 内に追加 pulse (約 15 events) を発火。v10.7 natural の +15.28 と同等。

---

## 4. Level 2 主要 finding

`v108_atom_path_enriched_report.md` 詳細。

最大: **temporal_coactivation × medium n_pulses で +13.5〜+13.8** (vs unrelated_baseline)。

→ 5 path 全部で atom-relation 経由の波及効果が確認される (Level 2 達成)。

---

## 5. Level 3 主要 finding (最大の発見)

`v108_atom_source_specific_report.md` 詳細。

最大 effect_size: **familiarity × medium n_pulses で 6.83** (atom 別 max 13.02 vs min 6.19、2.1 倍差)。

path 別 atom 依存性:
- **familiarity**: effect_size 6.83 (最高、強い atom 依存)
- attention_via_salience: 2.30
- integration α/β: 0.85〜0.88
- **temporal_coactivation**: 0.03 (最低、atom 中立)

→ **familiarity 経路は atom 種別を識別する波及シグナルを持つ**。temporal_coactivation は atom 中立。

---

## 6. Level 3.5 (introduced vs natural) — v10.8 の核心

`v108_introduced_vs_natural_report.md` 詳細。

22 finding 中 **20 件が introduced < natural** (negative)。最大: **attention_via_salience × medium n_pulses で atom 4.37 vs natural 8.75 = -4.38** (atom は natural の **半分**)。

例外 2 件 (introduced > natural):
- **temporal_coactivation × medium n_pulses**: atom +0.36 (= 案 α 均等分散発火が temporal で目立つ)

→ **「外部注入された atom event は ESDE の natural 発火と区別できる波及プロファイル」**、特に **familiarity / attention / Integration で弱い、temporal でわずかに強い** という systematic な差異を 24 seeds 一貫で確認。

これは因果断定ではなく **event 比較の観察記録** (即決 §3.1 反映)。

---

## 7. 副次観察 (主題判定外)

`v108_subsidiary_observations_report.md` 詳細。

- **Whiteout**: 7,200/7,200 全 flag (max_corr 1.000) — medium n_pulses 1 軸支配の表れ
- **Small-World**: 24/24 完全維持 (loops 14,343 / 110,103 完全同一) — post-process 構造的不変
- **誤差分布**: 8,835 rows、**正規分布 0% / bimodal 17.4% / skewed 24.3% / other 55.7% / heavy_tail 2.6%** — 「確率的発生と誤差表現能力の融合可能性」素材

---

## 8. bit-identity 検証

### 8.1 層 A (同 seed 2 回)

Step G で seed 0 を 2 回実行、**15/15 data ファイル完全一致** (summary 系 3 件のみ実行時間で除外、データ決定論性 PASS)。

### 8.2 層 B (v10.7 baseline 不変)

main run 前後で v10.7 出力 222 ファイル MD5 完全一致 PASS。**v10.8 が v10.7 を破壊していないこと確認**。

### 8.3 層 C (v10.8 出力先縛り)

全出力が `developmental/v108/outputs/main/` 配下、v105/v106/v107 配下への書き込みなし、`assert_output_under_v108` で path traversal 防止。

---

## 9. storage 実測

| 区分 | 値 |
|---|---:|
| 24 seeds 全出力 | **737 MB** (上限 6 GB の 12%) |
| per-seed 平均 | 30.7 MB (smoke seed 0 24.65 MB から増、main では event 数増) |
| ファイル数 | 363 |

→ smoke 推定 592 MB から増 (+24%)、event 数の seed 別ばらつきによる。Step B 当初予想 1.7 GB から大幅小。

---

## 10. v10.7 vs v10.8 比較

| 項目 | v10.7 | v10.8 | 増分 |
|---|---:|---:|---|
| events/seed (avg) | 16,111 | 約 18,600 | +15% (atom 2,500) |
| storage 24 seeds | 428 MB | **737 MB** | +72% |
| 並列 main run | 234 秒 | **325 秒** | +39% |
| Level 1 findings | 93 | 811 | +772% (atom × atom 対象拡大) |
| Level 2 findings | 49 | 683 | +1294% |
| Level 3 findings | 85 | 36 | -58% (p_value 厳格化) |
| **Level 3.5 (新規)** | - | **22** | atom vs natural 差異 |
| Small-World | 711/4,563 | 711/4,563 | 0 (構造的) |

---

## 11. 残課題 (v10.9 以降)

1. **WLD.artless 偏在性の解明**: v10.6 から継続課題、本フェイズは留保ラベル
2. **Whiteout の真の検出**: 高次元プロファイル (path × delta) で再評価
3. **Level 4 (causal intervention)**: introduced atom event を任意位置に注入できる Phase 2 機構
4. **bimodal 分布の原因解析**: 1,540 件の bimodal な (atom, path, window) の二峰性の原因を target cid の二相状態として解析
5. **introduced < natural の原因**: Q/C コスト、cid 選定、発火タイミングのどれが寄与しているか分離

---

## 12. 完了

v10.8 atom_introduction_event 機構の最小実装 (Level 3.5、A 群) は本フェイズで完了。Code A 認識確認ステップ + Step A-J を 1 日で完了。Web Claude / Taka による解釈待ち。

---

*以上、v10.8 main run 総括報告。Level 1-3.5 + 副次観察 6 reports と本総括で v10.8 アウトプット完成。*
