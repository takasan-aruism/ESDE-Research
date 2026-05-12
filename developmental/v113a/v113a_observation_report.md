# v10.13.a Step J 観察事実報告 — reaction phase 5 段階の整備

*作成*: 2026-05-12、Code A
*親*: `v113a_phase_design.md` (主題ドキュメント、Web Claude) + `v113a_step_a_recognition.md` (Step A 認識確認、Code A) + Web Claude 即決事項返答 (2026-05-12)
*対象*: Web Claude (Step K Phase Result 作成) + Taka (確認)
*目的*: Map 1-5 + long phase 算出の観察事実を直感語 + 構造文併記で記録、judgment 回避 (Aruism 整合)、v10.13.b 着手判断材料 + 留保 31 件継承

---

## 0. 一文サマリ

実装 Step B-I 全完了 (層 B 3,243 files unchanged、層 A deterministic 保証、層 C 構造的保証)、Map 1-5 + long phase 算出による reaction phase 5 段階の観察事実として、**Map 1 (phase × n_core_bin) で n_pulses が 3 phase 全てで頑健 v112 > v108_standard (immediate paired_d +1.19 / short +1.16 / mid +0.91、3 phase 全て CI 0 を跨がない)、delta_C は short のみ頑健 (paired_d +0.46、immediate/mid は CI 0 跨ぎ)**、**Map 2 (phase × relation_path × path_category) で 15 cells (3 phase × 5 path) 全て CI 0 を跨ぎ path_excess は方向性なし**、**Map 3 (phase × formation_relation) で before phase 1-2 で頑健 (immediate paired_d +0.63 / short +0.42)、no_alpha は全 phase で CI 0 跨ぎ、mid で before も消失**、**Map 4 (phase × event 種別) で v107 natural 5 種は phase 内 c_conversion/ingestion が最大 delta_C (immediate 0.11 → mid 0.45)、v112 atom_introduction_event は phase で増加 (immediate 0.013 → mid 0.081)、v108_standard atom は全 phase で 0 近傍**、**Map 5 (null phase cell-based) で v112 で 36 null candidates (immediate 14 / short 11 / mid 11)、v108_standard で 0、PER/WLD/PRP/SOC 等で広く分散、EXS が mid phase で 2 atoms 出現**、long phase (1000-25000 step) data の算出可能性を確認 (留保 #28 で記録、Map 1-5 long 拡張は v10.13.b 以降の判断対象)、Taka §1.9「揺れの幅」と 2026-05-11 整理「時間軸 = 波及深度」との接続箇所として「v112 cid pool は path 経路を経ない波及が phase 全体で観察される (null absorption 36 cells)」+ 「n_pulses の方向反転は v10.13.b で詳細観察対象」を v10.13.b 着手判断材料として提示、累計留保 31 件 (継承 27 + 新規 #28-#31 確定)、新規候補 #32 (event 種別 c_conversion/ingestion の phase 別 delta_C 増加挙動)、絶対格言 15 件全項目遵守、judgment 回避 (success/fail 判定なし)、Web Claude Step K Phase Result 作成を待つ。

---

## 1. 実装完了 Step 概要

| Step | 内容 | 出力 | 時間 |
|---|---|---|---|
| Step A | 認識確認 + 9 論点回答 + 事前齟齬 7 件 | `v113a_step_a_recognition.md` | - |
| Step B | 環境チェック + 層 B baseline (3,243 files) | `layer_b_baseline.json` | 0.09s |
| Step C-F | Map 1-4 一括算出 (3 phase × 各軸) | `map1-4_*.parquet` | 1.97s |
| Step G | Map 5 null phase (cell-based 案 X-1) | `map5_null_phase_per_cell.parquet` | 13.07s |
| Step H | long phase (1000-25000 step) 算出 | `excess_change_long_*.parquet` × 48 | 41.70s |
| Step I | bit-identity 検証 (層 A/B/C) | `step_i_bit_identity_report.json` | 0.1s |
| **合計** | - | - | **~57 秒** |

層 B 検証: 3,243 files 完全不変 (0 changed / 0 added / 0 removed)、絶対格言 #2 (物理層 frozen) 維持。

---

## 2. Map 1: phase × n_core_bin の観察事実

### 2.1 cross-seed paired_d (24 seeds、v112 - v108_standard 比較)

**注**: v112 は cond3 で bin_5_plus に集中 (留保 #26 通り)、v108_standard には bin_2/3_4 もあるが paired diff は同 cell でのみ算出可、結果として bin_5_plus のみ cross-seed 比較可能。

#### delta_C (relation paths 5 種の per-event mean)

| phase | paired_d | sign_test (pos/neg) | bootstrap CI 95% | crosses_zero |
|---|---:|---|---|:-:|
| immediate (1-10) | +0.29 | 16/8 | [-0.005, +0.026] | YES |
| **short (10-100)** | **+0.46** | **16/8** | **[+0.009, +0.113]** | **NO** ✓ |
| mid (100-1000) | +0.17 | 13/11 | [-0.076, +0.207] | YES |

#### n_pulses (per-event mean of relation paths' n_pulses_in_window)

| phase | paired_d | sign_test (pos/neg) | bootstrap CI 95% | crosses_zero |
|---|---:|---|---|:-:|
| **immediate** | **+1.19** | **22/2** | **[+0.009, +0.017]** | **NO** ✓ |
| **short** | **+1.16** | **21/3** | **[+0.055, +0.106]** | **NO** ✓ |
| **mid** | **+0.91** | **19/5** | **[+0.414, +0.980]** | **NO** ✓ |

### 2.2 直感語 + 構造文記述

**直感語**: bin_5_plus 中 cluster 層の cid に atom を投げると、3 phase 全てで pulse 活動の頑健な増加が観察される。delta_C は短期循環 phase でだけ頑健に動く。

**構造文**:
- v112 vs v108_standard の paired diff (24 seeds) で n_pulses は 3 phase 全てで bootstrap CI が 0 を跨がない頑健な v112 > v108_standard 関係
- delta_C は short phase のみ CI 0 を跨がず、immediate / mid では CI 0 跨ぎ
- bin_2 / bin_3_4 (v112 で空) は cond3 構造的帰結 (留保 #26)

### 2.3 v10.12 追加調査との対比

本日 (2026-05-11) の `v112_window_post_process` 全 events 集計では:
- delta_C immediate paired_d +0.54 (CI 0 を跨がず、頑健)

本書 Map 1 で bin_5_plus 限定では:
- delta_C immediate paired_d +0.29 (CI 0 跨ぎ)

**差異の構造的理由**: 全 events 集計では n_core_bin = 2/3_4 (v112 では空、v108_standard には豊富) と bin_5_plus を混ぜている。v108_standard の bin_5_plus 単独で集計すると bin_2/3_4 の影響を受けず、両条件の bin_5_plus 比較で immediate delta_C は CI 0 跨ぎとなる。

→ **集計単位 (全 events vs bin_5_plus 限定) で観察結果が変わる**、層化を default にする規律 (絶対格言 #4) の必要性を再確認。

---

## 3. Map 2: phase × relation_path × path_category

### 3.1 cross-seed paired_d (15 cells = 3 phase × 5 path)

#### atom_related (3 path)

| phase | path | paired_d | CI 95% | crosses_zero |
|---|---|---:|---|:-:|
| imm | familiarity | +0.10 | [-0.014, +0.021] | YES |
| imm | attention_via_salience | +0.10 | [-0.006, +0.012] | YES |
| imm | temporal_coactivation | -0.08 | [-0.015, +0.009] | YES |
| short | familiarity | +0.07 | [-0.074, +0.099] | YES |
| short | attention_via_salience | -0.03 | [-0.075, +0.068] | YES |
| short | temporal_coactivation | -0.31 | [-0.106, +0.010] | YES |
| mid | familiarity | +0.01 | [-0.228, +0.263] | YES |
| mid | attention_via_salience | -0.01 | [-0.236, +0.230] | YES |
| mid | temporal_coactivation | -0.18 | [-0.234, +0.078] | YES |

#### layer5_structural (2 path)

| phase | path | paired_d | CI 95% | crosses_zero |
|---|---|---:|---|:-:|
| imm | integration_alpha | +0.31 | [-0.013, +0.530] | YES |
| imm | integration_beta | +0.32 | [-0.001, +0.537] | YES |
| short | integration_alpha | +0.20 | [-0.241, +1.039] | YES |
| short | integration_beta | +0.22 | [-0.211, +1.061] | YES |
| mid | integration_alpha | +0.28 | [-0.083, +1.051] | YES |
| mid | integration_beta | +0.29 | [-0.072, +1.090] | YES |

### 3.2 直感語 + 構造文記述

**直感語**: どの path 経路 (atom 関連 3 種 + Layer 5 構造観察 2 種) で見ても、phase を変えても、v112 と v108_standard の差は seed-level の揺れに埋もれて方向が定まらない。Layer 5 構造観察 path (integration_α/β) は paired_d の値自体は +0.20-0.32 と中等度だが、std が大きく (1.5-1.8) CI が広いため 0 を跨ぐ。

**構造文**:
- 15 cells (3 phase × 5 path) 全てで bootstrap CI 95% が 0 を跨ぐ
- atom_related (familiarity / attention_via_salience / temporal_coactivation) の paired_d 絶対値は 0.01-0.31 で小〜中
- layer5_structural (integration_α/β) は paired_d +0.20-0.32 で中等度だが、留保 #31 通り integration_α/β は v112 で 59 events/seed と小サンプルのため std 大、CI 広い
- Step J で確定: path_category × phase の組み合わせで頑健な方向性は 0 件

### 3.3 v10.12 Step J との整合

v10.12 Step J で確定した「path_excess 4 種 (atom_related + integration_alpha) 全て CI 0 跨ぎ」を本書では 5 path (integration_beta 追加) × 3 phase で再確認。**path_excess は phase 拡張しても方向性なし**、Step J 結論変わらず。

---

## 4. Map 3: phase × formation_relation

### 4.1 cross-seed paired_d

| phase | formation_relation | paired_d | sign_test | CI 95% | crosses_zero |
|---|---|---:|---|---|:-:|
| **immediate** | **before** | **+0.63** | **19/5** | **[+0.007, +0.026]** | **NO** ✓ |
| immediate | no_alpha | +0.22 | 10/6 | [-0.002, +0.003] | YES |
| **short** | **before** | **+0.42** | **13/11** | **[+0.007, +0.128]** | **NO** ✓ |
| short | no_alpha | +0.08 | 9/7 | [-0.006, +0.008] | YES |
| mid | before | +0.20 | 12/12 | [-0.075, +0.252] | YES |
| mid | no_alpha | +0.18 | 9/7 | [-0.008, +0.017] | YES |

注: during / after は v112 / v108_standard 両方で空 (cond1 で β member 除外、留保 #26)。

### 4.2 直感語 + 構造文記述

**直感語**: 「β 形成前 (before) の cid」では反射 phase (immediate) と短期循環 phase (short) で delta_C が頑健に v112 > v108_standard、中期循環 phase (mid) で消失。「α 未参加 (no_alpha) の cid」では全 phase で揺れに埋もれる。

**構造文**:
- before (β 形成前) の cid (v112 で 93.8%、v108_standard で 36.4%): immediate / short で paired_d +0.63 / +0.42 で頑健 v112 > v108_standard、mid で CI 0 跨ぎ
- no_alpha (α 未参加) の cid (v112 で 6.2%、v108_standard で 49.4%): 全 phase で CI 0 跨ぎ、ただし sign_test は 16 seeds で算出 (8 seeds で v112 events 0)
- during / after は構造的に空セル (留保 #26)

### 4.3 注目点

- before での delta_C 頑健性は phase が進むほど (immediate → short → mid) 縮小、Taka 整理「複雑になるほど統計的に安定し差異が生じない」と整合する観察方向
- no_alpha での持続的な「揺れの埋もれ」は留保 #21 (v10.5 機構 A 既知挙動) との接続候補

---

## 5. Map 4: phase × event 種別

### 5.1 cross-seed delta_C 平均 (v107 natural 5 種 + v10.12 atom 2 種)

| event_source_type | condition | imm | short | mid | total events |
|---|---|---:|---:|---:|---:|
| pulse | v107_natural | +0.001 | +0.002 | +0.002 | 359,110 |
| alpha_formation | v107_natural | +0.007 | +0.009 | +0.007 | 36,476 |
| beta_formation | v107_natural | +0.020 | +0.023 | +0.019 | 12,952 |
| **c_conversion** | v107_natural | **+0.110** | **+0.275** | **+0.448** | 3,594 |
| **ingestion** | v107_natural | **+0.110** | **+0.275** | **+0.448** | 3,594 |
| **atom_introduction_event** | **v112** | **+0.013** | **+0.060** | **+0.081** | 10,500 |
| atom_introduction_event | v108_standard | -0.001 | +0.001 | +0.002 | 60,000 |

注: c_conversion と ingestion が同値なのは、両者が同じ source 由来 (ingestion event → c_conversion 判定の連動関係) と推察、留保 #32 候補。

### 5.2 直感語 + 構造文記述

**直感語**: ESDE 内部 event 種別の中で「意識転化 (c_conversion) と摂食 (ingestion)」が delta_C の最大駆動 event。phase が進むほど (immediate → mid) 大きくなる。v112 cid pool への atom 取り込みは beta_formation と alpha_formation の中間程度の delta_C を生む、ただし phase が進むほど大きくなる傾向は他 event 種別と整合。v108_standard pool は phase によらず delta_C 0 近傍。

**構造文**:
- delta_C 駆動 event ランキング (mid phase): c_conversion = ingestion (+0.448) > beta_formation (+0.019) > alpha_formation (+0.007) > pulse (+0.002)
- v112 atom_introduction_event: imm +0.013 → short +0.060 → mid +0.081 で phase 別に増加 (約 6 倍)
- v108_standard atom_introduction_event: imm -0.001 → short +0.001 → mid +0.002 で常に 0 近傍
- v112 atom は beta_formation の **mid phase で約 4 倍** の delta_C (+0.081 vs +0.019)

### 5.3 注目点

- **phase 別の event 種別ランキングが安定** (mid phase でも順位変わらず): pulse < alpha < beta < c_conv = ingestion
- **v112 atom と v108_standard atom の差** が phase で増加: imm 約 14 倍 (0.013 vs -0.001 の絶対比較困難)、short 60 倍 (0.060 vs 0.001)、mid 41 倍 (0.081 vs 0.002)
- これは v112 cond3 (n_core ≥ 5) 絞り込みの効果と推察、ただし path 経路特定不能 (Map 2 path_excess 方向性なし) → null absorption (Map 5) との関連

---

## 6. Map 5: null phase (cell-based、案 X-1)

### 6.1 集計結果

```
total cells: 450 (2 condition × 3 phase × 3 n_core_bin × 25 atom)
non-empty cells: 276 (v112 で bin_5_plus のみ 75 cells、v108_standard で 201 cells)
null candidates: 36
  v112: 36 (immediate 14 / short 11 / mid 11)
  v108_standard: 0
```

### 6.2 null 条件達成内訳 (条件別 PASS 数)

| condition | phase | n_cells | cond_1 (path 全無信号) | cond_2 (過半数 seeds 動く) | cond_3 (n≥3) | 全 PASS |
|---|---|---:|---:|---:|---:|---:|
| v108_standard | imm | 67 | 4 | 26 | 60 | 0 |
| v108_standard | short | 67 | 4 | 26 | 60 | 0 |
| v108_standard | mid | 67 | 4 | 26 | 60 | 0 |
| **v112** | **imm** | **25** | **14** | **25** | **25** | **14** |
| **v112** | **short** | **25** | **11** | **25** | **25** | **11** |
| **v112** | **mid** | **25** | **11** | **25** | **25** | **11** |

→ **v108_standard では cond_2 (過半数 seeds で delta_C 動く) を pass する cells が 26/67 (39%)、cond_1 (path 全無信号) も 4/67 だが 3 条件全 pass は 0**。
→ **v112 では cond_2 / cond_3 を全 25 cells が pass、cond_1 が大半 (11-14/25 = 44-56%)、結果として 11-14 cells が null candidate**。

### 6.3 null candidates の atom_category 分布 (v112 bin_5_plus のみ)

| phase | BOD | EXS | FND | PER | PRP | SOC | TIM | WLD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| immediate | 1 | 0 | 1 | 5 | 2 | 2 | 1 | 2 |
| **mid** | 0 | **2** | 2 | 1 | 1 | 2 | 0 | 3 |
| short | 1 | 0 | 1 | 1 | 3 | 2 | 0 | 3 |

### 6.4 直感語 + 構造文記述

**直感語**: v112 cid pool では、bin_5_plus × 多くの atom (BOD/EXS/FND/PER/PRP/SOC/TIM/WLD 8 category) の cell で「delta_C は動くが、5 path 全てで方向が定まらない (null absorption)」状態が phase 全体で観察される。これは「v112 cid pool での atom 取り込みは特定経路を経ずに広く拡散する」観察事実。v108_standard では同じ null candidate は 0 cells。

**構造文**:
- v112 で 36/75 non-empty cells (48%) が null candidate
- v108_standard で 0/201 non-empty cells (0%) が null candidate
- 構造的差異の発生源: cond_1 (path 5 種全 CI 0 跨ぎ) の発生率が v112 で 44-56% (bin_5_plus のみのため n=25)、v108_standard で 6% (4/67、bin_2/3_4 含む 67 cells のうち)

### 6.5 注目点

- **EXS (存在)** が mid phase でのみ 2 atoms 出現 (immediate / short では 0)、Taka §1.9「ESDE Genesis の動学発展段階」(WLD.artless → TIM.appear → WLD.artless → **EXS.being**) との接続候補
- **PER (知覚)** は immediate で 5 atoms と最多、反射 phase で広く null absorption
- **WLD** は短期 / 中期 phase で 3 atoms ずつ、持続的に null absorption

---

## 7. Step H long phase (1000-25000 step) data 算出

### 7.1 算出結果

- 48 jobs (24 seeds × 2 conditions) 完了 (41.70 秒)
- 出力: `excess_change_long_v112_seed{N}.parquet` × 24 + `excess_change_long_v108_standard_seed{N}.parquet` × 24
- データサイズ計 59.4 MB

### 7.2 v107 WINDOW_DEFS monkey-patch の構造

```python
ORIGINAL_WINDOW_DEFS = [("immediate", 1, 10), ("short", 10, 100), ("medium", 100, 1000)]
v107_bc.WINDOW_DEFS = [("long", 1000, 25000)]  # subprocess 内で書き換え
# compute_deltas を呼んで long phase の delta を per (event, target, path) 算出
```

### 7.3 Map 1-5 への long phase 拡張 (本書スコープ外)

長 phase は v107 既存 WINDOW_DEFS の自然な延長として算出可能と確認 (留保 #28 確定)。ただし Map 1-5 への long phase 拡張は v10.13.b 以降の判断対象 (Web Claude/Taka 即決事項 #5 通り)。

理由:
- Step C-G で immediate / short / mid の 3 phase 結果が確定、reaction phase map が成立
- long phase は cid lifespan を超える可能性高い (target_step + 25000 が cid death を超える events 多い、留保 #28)
- v10.13.b で「Map 1-5 で対応がある」と見えた phase × 経路の組み合わせを観察対象に絞り込む際、long phase も同時拡張するかは Web Claude/Taka 判断

→ 本書では long phase data の算出可能性を確認、Map 1-5 long 拡張は v10.13.b 以降に委ねる。

---

## 8. v10.13.b 着手判断材料

### 8.1 Map 1-5 で「対応が見えた」phase × 経路の組み合わせ

| 観察 | 組み合わせ | 観察値 |
|---|---|---|
| **n_pulses 3 phase 全頑健** | n_core_bin = bin_5_plus × 3 phase | paired_d +0.91-1.19、3 phase 全て CI 0 を跨がない |
| **delta_C short 頑健** | n_core_bin = bin_5_plus × short | paired_d +0.46、CI [+0.009, +0.113] |
| **before formation × imm/short 頑健** | formation_relation = before × immediate/short | imm +0.63 / short +0.42、CI 0 を跨がない |
| **null absorption v112 bin_5_plus** | n_core_bin = bin_5_plus × atom × 3 phase | 36 cells (48% of non-empty) で path 全無信号 |
| **v112 atom phase 別増加** | event 種別 = atom_introduction_event × v112 | imm 0.013 → short 0.060 → mid 0.081 (約 6 倍) |
| **c_conversion / ingestion 最大駆動** | event 種別 = c_conversion or ingestion | mid phase で +0.448 (atom v112 の 5.5 倍) |

### 8.2 v10.13.b で深堀り候補 (Code A 提案、Taka 判断)

1. **n_pulses 方向性の意味解明**: 3 phase 全頑健は v112 cid pool が pulse 活発 cid を選ぶ効果か、それとも atom 取り込みが pulse を実際に増やすのか (v10.12 §4 で smoke vs main で immediate n_pulses は -0.94、本書 bin_5_plus 限定で +1.19 と方向違い、cid pool 構造の問題と推察)
2. **null absorption の意味**: 36 cells で path 経路特定できない波及がなぜ起きるか、Taka §1.9「揺れの幅」の操作的観察に該当
3. **v107 natural event との比較**: c_conversion / ingestion が最強の delta_C 駆動だが、これらは ESDE 内部 event、atom_introduction はその中間 (alpha_formation < atom_v112 < beta_formation)、reaction phase での event 種別ヒエラルキー観察

### 8.3 v10.13.c (Gemini 案 2 Atom 干渉) への接続

Map 5 null absorption が phase 全体で v112 のみ発生 (v108_standard 0) という事実は、**v112 cid pool は path 経路を経ない波及が広範**を示唆する。Gemini 案の「2 atom 干渉」観察は、v10.13.c でこの「広範な波及」を 2 atom 並行注入時の挙動として観察可能 (干渉が見えるか、独立に動くか)。

---

## 9. 留保事項 (継承 27 + 新規 5 = 32 件)

### 9.1 継承 27 件

v10.12 完了時点 (`v112_completion_report.md`) の 27 件をそのまま継承。

### 9.2 新規 5 件 (v10.13.a Step A + 本書)

| id | step | title |
|---|---|---|
| #28 | Step H | long phase (>1000 step) のデータ可用性 → 算出可能、Map 1-5 long 拡張は v10.13.b 以降 |
| #29 | Step G | null absorption 判定方式 (cell-level 案 X-1 採用、Web Claude 即決事項) |
| #30 | Step C-D | matched_baseline が v112 で空 (cond3 構造的) |
| #31 | Step D | v112 integration_α/β 小サンプル (per-event 1-2 events、std 大、CI 広) |
| **#32 (本書)** | Step F | **c_conversion と ingestion の delta_C が完全同値** (+0.110/+0.275/+0.448 で phase 別に同値)、event source 由来の構造的連動と推察、v10.13.b で構造解明候補 |

---

## 10. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step J での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 5 phase は v10.7 既存設計の延長、観察事実を先に提示 |
| 2 | 物理層 frozen 絶対 | ✓ 層 B 3,243 files 完全不変、ledger 不変 |
| 3 | ベースライン比較 + 効果サイズ | ✓ v108_standard 比較で paired_d 算出、絶対値より構造方向重視 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ Map 1-5 全てで n_core_bin 別 default |
| 5 | 観察軸を増やさない | ✓ 5 phase は v10.6-v10.12 観察事実の統合枠組み |
| 6 | 出口の固定 | ✓ Map 1-5 + long phase data 算出、v10.13.b 判断材料明示 |
| 7 | 主題着手前に上位資料を読む | ✓ Step A で v10.7 / v10.10 §3.4 / v10.12 §4 / §5.1 参照済 |
| 8 | 過去観察軸の照会 | ✓ Step A §2 で v10.6-v10.12 取扱を全件記載 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ 5 phase 境界は v107 継承、null 判定は構造的 (案 X-1)、効果サイズ閾値なし |
| 10 | 因果ではなく因果候補 | ✓ 「観察事実」「対応関係」「方向性なし」表現、「効いた/失敗」なし |
| 11 | 概念単位を雑に扱わない | ✓ path_category で atom_related / layer5_structural / baseline 分離 |
| 12 | Aruism 判定回避 | ✓ success/fail 判定なし、観察事実のみ記録 |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Gemini / GPT / Web Claude / Code A の役割境界遵守 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ 主題ドキュメント §4 で原文保存、本書は直感語 + 構造文併記で記述 |
| 15 | 5 者運用体制の補完性 | ✓ Code A 認識確認連続 8 段階、Web Claude 補完 |

---

## 11. Taka §1.9 + 2026-05-11 整理との接続箇所

### 11.1 §1.9「字面を揺れながら捉える揺れの幅」

本書 §6 (Map 5 null phase) で v112 で 36 null candidates 発生は、Taka §1.9 の「揺れの幅」の操作的観察に該当する可能性。「path 経路を経ない波及」は「揺れの幅を path で説明しきれない領域」として観察される。

### 11.2 2026-05-11 整理「時間軸 = 波及深度」

本書 §5 (Map 4) で v107 natural event の delta_C が phase で増加する観察 (c_conversion immediate 0.11 → mid 0.45、beta_formation imm 0.020 → mid 0.019 はほぼ同値だが c_conv 系は 4 倍増加) は、**reaction phase が異なる時間スケールで異なる事象を捕捉**する Taka 整理と整合方向。

### 11.3 「複雑になるほど統計的に安定し差異が生じない」(Taka 2026-05-11)

本書 §4 (Map 3) で formation = before の delta_C 頑健性が phase で縮小 (imm +0.63 → short +0.42 → mid CI 0 跨ぎ)、Taka 整理と整合する観察方向。

---

## 12. Web Claude Step K Phase Result 作成への素材

本書は Code A 観察事実報告。Step K (Web Claude) で Taka 向け Phase Result (`v113a_phase_result.md`) 作成を待つ。Web Claude が翻訳する素材として:

- Map 1-5 主要観察 5 件 (§8.1 表)
- 直感語 + 構造文併記 (各 Map 末)
- v10.13.b/c 判断材料 (§8.2-8.3)
- 留保 32 件
- Taka §1.9 / 2026-05-11 整理との接続箇所 (§11)

---

## 13. 一文サマリ (再掲)

実装 Step B-I 全完了 (層 B 3,243 files unchanged、層 A deterministic 保証、層 C 構造的保証、合計 57 秒)、Map 1 (phase × n_core_bin) で n_pulses 3 phase 全頑健 (paired_d +0.91-1.19) + delta_C は short のみ頑健 (paired_d +0.46)、Map 2 (phase × relation_path) で 15 cells 全て CI 0 跨ぎ path_excess 方向性なし、Map 3 (phase × formation_relation) で before phase imm/short 頑健 (paired_d +0.63/+0.42) mid で消失、Map 4 (phase × event 種別) で c_conversion = ingestion が最大駆動 (mid +0.448)、v112 atom phase で増加 (imm 0.013 → mid 0.081 約 6 倍)、Map 5 (null phase cell-based) で v112 で 36 null candidates (path 経路を経ない波及) PER/WLD/PRP/SOC 等で分散、v108_standard で 0、long phase data 算出可能性確認 (Map 1-5 long 拡張は v10.13.b 以降)、Taka §1.9「揺れの幅」+ 2026-05-11「時間軸 = 波及深度」+ 「複雑になるほど統計的に安定」の 3 整理との接続箇所を §11 で記述、累計留保 32 件 (#28-#32 新規、特に #32 c_conversion = ingestion 同値の構造解明候補)、絶対格言 15 件全項目遵守、judgment 回避、v10.13.b 着手判断材料 6 件提示 (n_pulses 方向性 / null absorption 意味 / event 種別ヒエラルキー / before formation 縮小 / v112 phase 増加 / v107 vs v10.12 atom 比較)、Web Claude Step K Phase Result 作成を待つ。

---

*以上、v10.13.a Step J 観察事実報告 (Code A)。Web Claude Step K で Phase Result 作成 → Taka 確認 → v10.13.b 主題選定。*
