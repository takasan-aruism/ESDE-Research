# v10.10 Step B' 完了報告 — Multi-gate 母集団全実測 + Q-A1-A4 回答

*作成*: 2026-05-09、Code A
*親*: `v110_response_to_code_a.md` (Web Claude 2026-05-09)
*対象*: Web Claude (主題ドキュメント書き換えへの素材) / Taka

---

## 0. 一文サマリ

Multi-gate 設計の母集団を 11 種 gate (ABC/ABc/aBC/AB/AC/BC/A/B/C/Bc/all_pass) × 3 timing (age=200/300/500) で 24 seeds 実測 (12.67 秒)、**重要発見: a (age<=1000) と A (age<=560) は age=200 発火では完全同値 (両方とも cid lifespan>=200 を満たす全 cid を許可)、Web Claude 試案の若年緩和軸は age_target を変える timing 軸 (200/300/500) として再構成すべき**、age=200 で per (atom×seed) >= 3 を満たす gate は **ABc 3.62 / AB 7.38 / B 7.38 / Bc 3.62 / A 8.71 / all_pass 8.71** の 6 種、age=500 では cid 早期死亡で events 急減 (ABC 1,106 → 310、-72%)、Code A 推奨実用 set は **9 gate × age=200 + v108_re** の 10 conditions で main run 推定 5-10 分 / 累計 storage 1.7 GB (28%)、Q-A1-A4 全件回答完了、Web Claude の主題ドキュメント書き換え待ち。

---

## §1 全実測結果 (11 gate × 3 timing × 24 seeds)

### 1.1 events 数 (24 seeds 合計、per atom × seed)

| gate | age=200 | age=300 | age=500 |
|---|---:|---:|---:|
| ABC | 1,106 (p1.84) | 1,024 (p1.71) | 310 (p0.52) |
| ABc | 2,175 (p3.62) | 1,993 (p3.32) | 802 (p1.34) |
| **aBC** | **1,106** | **1,024** | **310** |
| AB  | 4,425 (p7.38) | 4,096 (p6.83) | 1,988 (p3.31) |
| AC  | 1,331 (p2.22) | 1,331 (p2.22) | 493 (p0.82) |
| BC  | 1,106 (p1.84) | 1,024 (p1.71) | 310 (p0.52) |
| A   | 5,224 (p8.71) | 5,224 (p8.71) | 3,031 (p5.05) |
| B   | 4,425 (p7.38) | 4,096 (p6.83) | 1,988 (p3.31) |
| C   | 1,331 (p2.22) | 1,331 (p2.22) | 493 (p0.82) |
| Bc  | 2,175 (p3.62) | 1,993 (p3.32) | 802 (p1.34) |
| all_pass | 5,224 (p8.71) | 5,224 (p8.71) | 3,031 (p5.05) |

### 1.2 重要発見: aBC = ABC (a 緩和軸は無効)

**「age <= 560 (A)」と「age <= 1,000 (a)」は age=200 発火では完全同値**:
- 両方とも cid lifespan >= 200 を満たす全 cid を許可
- 仕様 §2.1 の `is_receptive(cid, t)` で `t = birth + 200` なので age = 200 < 560 < 1000 で常に成立
- → Web Claude 試案の **a 緩和軸 (Q-A3 で問われた緩和線) は無意義**

### 1.3 timing 軸 (age_target) として再構成

a 緩和の代替として「age_target を 200 / 300 / 500 で変動」が実質的な timing 軸の観察になる:
- age=200: cid 強反応中央 (Step F median 227)
- age=300: 中央から +76 step
- age=500: 上限 560 寄り (短命 cid 除外で events 急減)

→ 主題ドキュメント書き換え時に **「age_target を gate 軸として明示する」** ことを推奨。

### 1.4 cid 寿命分布 (a 閾値判断材料)

```
n=5,224 cids (24 seeds 合計)
min  451, max 25,000
25%  481
50%  977 (median)
75%  2,485
mean 3,413, std 6,030

>= 200 (age=200 通過): 5,224 / 5,224 = 100.0%
>= 1,000:              2,258 / 5,224 = 43.2%
>= 1,500:              1,775 / 5,224 = 34.0%
>= 5,000:                762 / 5,224 = 14.6%
```

→ cid 寿命分布から age_target=500 は短命 cid を除外する効果が出始める。age_target=1,000 にすると約 57% の cid が脱落 (寿命不足で age 1000 通過不能)。

---

## §2 最低実行線判定 (per >= 3、推奨 >= 5)

### 2.1 age=200 で PASS する gate (Code A 推奨実用 set)

| gate | events | per | min(>=3) | recommend(>=5) |
|---|---:|---:|---|---|
| **AB** | 4,425 | 7.38 | PASS | **PASS** |
| **B** | 4,425 | 7.38 | PASS | **PASS** |
| **A** | 5,224 | 8.71 | PASS | **PASS** |
| **all_pass** | 5,224 | 8.71 | PASS | **PASS** |
| ABc | 2,175 | 3.62 | PASS | FAIL |
| Bc | 2,175 | 3.62 | PASS | FAIL |
| ABC (標準) | 1,106 | 1.84 | **FAIL** | FAIL |
| AC | 1,331 | 2.22 | FAIL | FAIL |
| BC | 1,106 | 1.84 | FAIL | FAIL |
| C | 1,331 | 2.22 | FAIL | FAIL |

### 2.2 観察意義 vs 実行可能性のトレードオフ

| gate | 観察意義 | 実行可能性 | 採用判定 |
|---|---|---|---|
| **ABC** (標準 3 条件) | v10.9 受信可能状態の核心 | per 1.84 で sensitivity 評価困難、ただし「評価不能」自体が観察結果 | **採用** (標準として記録) |
| **ABc** (緩和) | top 25% → top 50% で母集団 2 倍化 | per 3.62 で評価可能 | **採用** |
| **AB** (2 条件、fam 不問) | 「若年 + Integration 外」だけで何が見えるか | per 7.38 で十分 | **採用** |
| **AC** (Integration 不問) | familiarity だけで Integration 軸の影響を見る | per 2.22 で困難 | △ 観察用に記録 |
| **BC** (age 不問) | Integration 外 + 高 fam の age=200 制約解除 | per 1.84 で困難 | △ 観察用に記録 |
| **B** (Integration 外のみ) | age=200 発火 + Integration 外で何が起きるか | per 7.38 で十分 | **採用** |
| **A** (age=200 発火のみ) | controls (どの cid に発火しても age=200 効果はあるか) | per 8.71 で十分 | **採用** (controls) |
| **C** (familiarity top 25% のみ) | familiarity だけで何が見えるか | per 2.22 で困難 | △ 観察用に記録 |
| **Bc** (中間緩和) | Integration 外 + top 50% | per 3.62 | **採用** (B vs Bc で familiarity 段階差) |
| **all_pass** (制約なし) | controls (age=200 で発火する全 cid) | per 8.71 で十分 | **採用** (controls) |

### 2.3 Code A 推奨 Multi-gate 実用 set (9 conditions)

採用 (○ 6 件): **ABC, ABc, AB, B, Bc, A, all_pass**
観察用 (△ 4 件): **AC, BC, C** (sensitivity 評価困難だが観察結果として記録)

**実用 set 9 conditions**: ABC / ABc / AB / AC / BC / B / Bc / A / all_pass + v108_re = **10 conditions**

C only は「Integration 内+外混在で familiarity top 25%」で AC/BC と独立軸ないので除外候補。Web Claude 判断要請。

---

## §3 ストレージ予算再見積もり

### 3.1 Multi-gate 設計での累計予算

per (seed, condition):
- atom_events parquet: ~0.1-0.3 MB (events 数比例)
- baselines_with_delta: 0.5-4 MB (events 数比例)
- excess_change_adjusted: 0.4-3 MB (events 数比例)
- 合計 per (seed, condition): ~1-7 MB

per seed × 10 conditions:
- 平均 4 MB × 10 = ~40 MB / seed
- 24 seeds: ~960 MB ← 修正

これは Step A 推定 220 MB を大幅に超える。原因: gate 数増加 (1 → 10)。

### 3.2 修正試算 (各 gate の events 比例で再計算)

events 数比例で baselines / excess の容量を見積もる (v10.8 60,000 events → 7.5 MB/seed の比):

| gate | events 24 seeds | per seed | size/seed est. |
|---|---:|---:|---:|
| ABC | 1,106 | 46 | 0.18 MB (= 7.5 × 46/2500) |
| ABc | 2,175 | 90 | 0.36 MB |
| AB | 4,425 | 184 | 0.74 MB |
| AC | 1,331 | 55 | 0.22 MB |
| BC | 1,106 | 46 | 0.18 MB |
| B | 4,425 | 184 | 0.74 MB |
| Bc | 2,175 | 90 | 0.36 MB |
| A | 5,224 | 217 | 0.87 MB |
| all_pass | 5,224 | 217 | 0.87 MB |
| **9 conds 合計** | **26,346** | **1,098** | **~4.4 MB / seed** |
| v108_re (60,000) | 60,000 | 2,500 | 7.5 MB / seed |
| **総 per seed** | **86,346** | **3,598** | **~12 MB / seed** |

24 seeds: **288 MB**
+ cross_seed: ~10 MB
**v10.10 合計: ~300 MB**

### 3.3 累計

| Phase | サイズ |
|---|---:|
| v10.7 main | 0.40 GB |
| v10.8 main | 0.69 GB |
| v10.9 main | 0.20 GB |
| **v10.10 main (推定)** | **0.30 GB** |
| **累計** | **1.59 GB / 上限 6 GB (27%)** |

→ 打切閾値 50% (3 GB) に大幅余裕。

---

## §4 Q-A1-A4 回答

### Q-A1: Step B' の実装可能性

- **実装規模**: 11 gate × 3 timing × 24 seeds の母集団実測 = **12.67 秒で完了** ✓
- **per gate × 24 seeds 時間**: 約 0.4 秒 / gate (極軽量、cid_meta_table と alpha/beta intervals の構築コスト主)
- **Step B' 全体**: **本書作成時点で完了**

### Q-A2: gate 候補追加提案 (Code A)

| gate | 理由 | 採用 |
|---|---|---|
| **Bc** (Integration 外 + top 50%) | B vs Bc で familiarity 段階差を観察 | **追加** |
| **all_pass** (条件なし) | controls (age=200 timing のみ) | **追加** |
| age_target 軸 (200/300/500) | a 緩和の代替、timing 軸 | **age=200 採用** (300/500 は副参考) |
| ~aBC (a 緩和)~ | ABC と完全同値で意義なし | **却下** |

→ Code A 推奨実用 set: **ABC / ABc / AB / AC / BC / B / Bc / A / all_pass + v108_re** = **10 conditions**

### Q-A3: a (若年緩和) 閾値

**回答: a 緩和軸は無効**。

- A (age <= 560) と a (age <= 1,000) は age=200 発火では **完全同値** (実測で確認、両方 1,106 events)
- 仕様 §2.1 の age 条件は age=200 << 560 で常に成立
- 代替として **timing 軸 (age_target=200/300/500)** で「発火時刻」を変える形が観察意義あり
- 主題ドキュメント書き換え時に「a 緩和軸を timing 軸に置換」を推奨

### Q-A4: ストレージ予算

- **v10.10 推定**: 約 300 MB (10 conditions、Step A 推定 220 MB から増加)
- **累計**: 1.59 GB / 上限 6 GB (**27%**)
- 打切閾値 50% (3 GB) に大幅余裕、絞り込み不要
- 計算時間 (推定): main run 24 並列で **5-10 分** (10 conditions × 24 seeds)

---

## §5 Code A 推奨の最終 Multi-gate set

### 5.1 採用 9 gate + v108_re

| condition_id | 内容 | events | per | 観察意義 | 採用区分 |
|---|---|---:|---:|---|---|
| **v110_ABC** | 標準 3 条件 (A∧B∧C) | 1,106 | 1.84 | v10.9 受信可能状態の核心 | **主軸** |
| **v110_ABc** | 緩和 a (top 50%) | 2,175 | 3.62 | familiarity 緩和効果 | **主軸** |
| **v110_AB** | 2 条件 (age + Integ 外) | 4,425 | 7.38 | 「若年 + Integ 外」のみ | **主軸** |
| **v110_AC** | 2 条件 (age + fam) | 1,331 | 2.22 | Integ 軸を外す影響 | △観察用 |
| **v110_BC** | 2 条件 (Integ 外 + fam) | 1,106 | 1.84 | age 軸を外す影響 (= age=200 強制を解除) | △観察用 |
| **v110_B** | 1 条件 (Integ 外) | 4,425 | 7.38 | Integ 外単独効果 | **主軸** |
| **v110_Bc** | 1 条件 + top 50% | 2,175 | 3.62 | 段階差観察 | **主軸** |
| **v110_A** | 1 条件 (age=200) | 5,224 | 8.71 | controls (age=200 効果のみ) | **controls** |
| **v110_all** | 制約なし (age=200 で全 cid 発火) | 5,224 | 8.71 | controls (gate なし) | **controls** |
| **v108_re** | v10.8 標準再実行 | 60,000 | 100 | bit-identity 検証 | **bit-identity** |

→ 主軸 5 + 観察用 2 + controls 2 + bit-identity 1 = 10 conditions

### 5.2 各 gate の comparison 設計 (sensitivity_evaluator)

baseline は **v110_all (age=200 で全 cid 発火、controls)** または **v108_re** を使用。

主要比較:
- v110_ABC vs v110_all: 受信可能状態 gate の効果
- v110_AB vs v110_all: 若年 + Integ 外 gate の効果
- v110_B vs v110_all: Integ 外単独
- v110_AC vs v110_all: Integ 軸を外す影響
- v110_BC vs v110_all: age 軸を外す影響
- (副) v110_ABC vs v108_re: v10.10 受信可能状態 vs v10.8 標準
- (副) gate 間: ABC vs ABc (familiarity 段階)、ABC vs AB (familiarity 軸)

### 5.3 観察対象指標 (Level 3、24 seeds 方向一致)

主観察 3 指標 (主題ドキュメント §4.4 継承):
1. **timing 感度**: v10.10 = age=200 固定、v10.8 = uniform、両 condition の比較で timing 効果
2. **high_fam_out 経路の感度**: 各 gate × high_fam_out_integ baseline path
3. **natural_closer ratio**: v10.7 natural baseline と各 gate の delta 距離

---

## §6 主題ドキュメント書き換えへの素材

Web Claude が主題ドキュメントを書き換える際の素材 (Code A から):

### 6.1 §2.1 受信可能状態の判定 (書き換え案)

```
v10.10 では single gate ではなく Multi-gate 観察設計を採用。

主軸 gate (採用 9 種):
  - ABC: 3 条件 and (age<=560 + Integ 外 + fam top 25%)
  - ABc: 緩和 (top 50%)
  - AB / AC / BC: 2 条件
  - A: 単独 (age=200 controls)
  - B: 単独 (Integ 外)
  - Bc: 1 条件 + top 50%
  - all_pass: 制約なし (age=200 controls)

加えて v108_re: v10.8 標準の再実行 (bit-identity 検証用)
```

### 6.2 §2.2 timing (書き換え案)

```
全 gate で age_target=200 を採用 (Step F median=227 中央)。
a 緩和軸 (age<=1000) は ABC と同値で無意味なため削除。
将来 v10.11 以降で timing 軸 (age=200 / 300 / 500) を独立観察候補として残す。
```

### 6.3 §6.5 緩和 run 規律 (Web Claude §4.3 案を採用)

Web Claude 応答書 §4.3 の更新案を主題ドキュメントに反映。Multi-gate は緩和 run ではなく観察軸の追加であることを明示。

### 6.4 §Z Code A 確認事項 (本報告書を反映)

主要点:
- a 緩和軸の無効性
- timing 軸 (age_target) の追加候補
- 推奨 Multi-gate set 10 conditions
- ストレージ累計 1.59 GB (27%)

---

## §7 Step C 以降の進行 (主題ドキュメント書き換え後の予定)

```
[現在] Step B' 完了 (本書) → Web Claude が主題ドキュメント書き換え → Taka 確認
   ↓
[次] Step A 再認識確認 (Multi-gate 設計版)
   ↓
   Taka 承認
   ↓
Step C: atom_event_generator (10 conditions、CONDITIONS dict 拡張)
Step D: baseline_recalculator (10 conditions 各々 baseline 再計算)
Step E: sensitivity_evaluator (新 COMPARISONS、各 gate vs all_pass / vs v108_re)
Step F: smoke 結果報告 (1 seed × 10 conditions、bit-identity 検証)
Step G: 24 seeds main run (推定 5-10 分)
Step H: cross-seed 解析 + Level 1-3.5 reports + 4 種観察 + 構造的統合
Step I: 完了報告 + 観察状態 A/B/C 確定
```

---

## §8 一文サマリ (再掲)

11 gate × 3 timing × 24 seeds (12.67 秒) の Multi-gate 母集団全実測で **a 緩和軸 (age<=1000) は A (age<=560) と age=200 発火では完全同値で無意味** と判明、代替 timing 軸 (age_target=200/300/500) を提示、age=200 で per>=3 PASS 6 種 + per>=5 PASS 4 種、Code A 推奨実用 set は **9 gate (ABC/ABc/AB/AC/BC/B/Bc/A/all_pass) + v108_re = 10 conditions** で main run 5-10 分 / 累計 storage 1.59 GB (27%)、Q-A1-A4 全件回答完了 (Step B' 12.67 秒で完了 / Code A 提案 Bc + all_pass 追加 / a 軸 timing 軸へ置換 / 累計 27% で余裕)、主題ドキュメント書き換え (§2.1 Multi-gate 設計 / §2.2 a 軸削除と timing 軸残置 / §6.5 緩和 run 規律更新 / §Z Code A 確認事項反映) の素材を提供、Web Claude の書き換え + Taka 確認 + Code A 認識確認 (再) → Step C 以降再開へ。

---

*以上、Code A による v10.10 Step B' 完了報告。Web Claude `v110_phase_design.md` 主題ドキュメント書き換え + 実装指示書書き換え + Taka 確認 + Code A 認識確認 (再) の順で Step C 進行へ。*
