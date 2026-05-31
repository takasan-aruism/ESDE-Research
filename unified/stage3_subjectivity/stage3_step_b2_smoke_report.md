# 第 3 段階 Step B2 — 2nd smoke 報告 (gate)

**Date**: 2026-05-31
**Author**: Code A
**Status**: 2nd smoke 完了、**gate (止まって報告)**
**親**: Web Claude 2nd smoke 設計 + Step B2 期待事前明示 + Web Claude 3 誤り訂正

---

## 0. 出口判定 (2nd smoke)

| 層 | 出口 | 補足 |
|---|---|---|
| **層 1 (戻し機能)** | **`external_loop_functional`** | 全 6 conditions で物理層変化、戻し実効化機能 |
| **層 2 (出し方が系違いを生む)** | **`output_method_matters` (条件付)** | 局所スケールでは明確、global では弱い、案 α の規模制約あり |

→ Web Claude 期待 (層 1 functional / 層 2 partially matters) と一致。ただし **副次発見 (案 α 規模制約)** で本命設計の見直しが必要。

---

## 1. 実行結果

### 1.1 設定 + 時間

- 6 conditions: 3 出し方 (genesis_driven / shuffled_state_E / shuffled_random_nodes) × 2 K (5, 50)
- 1 seed (42)、maturation 3 + tracking 2 = **5 windows**、window_steps 100、N=5000、INJECT_RADIUS=8
- 全体 **1195.6 秒 (19.9 分)**、Web Claude 想定 (20-40 分) 内
- 各 condition ~195-204 秒

### 1.2 副次発見 (重要): 案 α の規模制約

**genesis_driven 案 α は K=50 を要求しても実際は 3-6 nodes しか返らない**:

| window | n_injected (K=5) | n_injected (K=50) | n_local_pool (K=50) |
|---|---|---|---|
| 0 | 3 | **3** | 45 |
| 1 | 5 | 5 | 85 |
| 2 | 5 | 5 | 85 |
| 3 | 5 | 5 | 85 |
| 4 | 5 | **6** | 102 |

理由: 案 α = 「最大 label の core node の E top-K」 → 最大 label の core node 数 (n_core) が 3-6 程度のため K=50 要求しても返らない。

- shuffled_state_E / shuffled_random_nodes は K=50 で 50 nodes 取れる
- → **K=50 比較は不公平** (genesis は実質 K=3-6 のまま)
- Web Claude 期待「K=50 で全体差出る」が **案 α では物理的に成立しない**

### 1.3 6 conditions × 5 windows の局所 inject 効果

| condition | K | window | n_inj | l_pre_E | l_post_E | d_E | d_link |
|---|---|---|---|---|---|---|---|
| genesis_driven | 5 | 0 | 3 | 0.604 | 0.605 | +0.0008 | 0 |
| genesis_driven | 5 | 4 | 5 | 0.228 | 0.231 | +0.0036 | 0 |
| shuffled_state_E | 5 | 0 | 5 | 0.576 | 0.602 | +0.0254 | 0 |
| shuffled_state_E | 5 | 4 | 5 | 0.188 | 0.224 | +0.0353 | 0 |
| shuffled_random | 5 | 0 | 5 | 0.568 | 0.598 | +0.0299 | 1 |
| shuffled_random | 5 | 4 | 5 | 0.242 | 0.274 | +0.0317 | 0 |
| genesis_driven | 50 | 4 | 6 | 0.227 | 0.231 | +0.0038 | 0 |
| shuffled_state_E | 50 | 4 | 50 | 0.213 | 0.253 | +0.0398 | **7** |
| shuffled_random | 50 | 4 | 50 | 0.220 | 0.258 | +0.0383 | 4 |

観察:
- genesis_driven は **inject 直後の E 変化 (d_E) が小さい** (0.0008-0.0272) → 既に E が高い node を選ぶため clamp 1.0 まで余地がない
- shuffled は **d_E が大きい** (0.025-0.04) → 低 E node も選ぶため余地大
- K=50 で shuffled は新規 link 生成 (d_link +3〜+7) が起こる、genesis は 0 (target_n が小さい)

---

## 2. 期待 vs 結果 (Taka 規律§4 比較表)

| 観察軸 | 期待 (実装前 §3.1-3.3) | 実際の結果 | 一致? |
|---|---|---|---|
| inject 直前→直後の局所 E (両 condition) | 両 condition で +0.6 程度 | **小**: genesis +0.001〜+0.027、shuffled +0.025〜+0.04 (clamp 1.0 で余地依存) | △ (一律 +0.6 ではなく、pre_E に依存) |
| 1 window 後の局所 E (genesis) | inject 後の高 E が周辺に拡散 | 各 window 末の l_pre_E は前 window の inject 効果消滅後、共通の物理進化結果 | × (拡散観察できず、window 内で平準化) |
| 1 window 後の局所 E (shuffled) | 孤立した E 上昇のまま拡散しにくい | 上と同じく window 末で平準化 | × |
| K=5 全体差ほぼゼロ | genesis vs shuffled で alive_l/labels/torque ほぼ同じ | g_post Δ rel 1-6% 小、想定通り | ✓ |
| K=50 全体で差出る (規模効果) | genesis vs shuffled の alive_l/labels 等で差 | **× 期待外れ**: rel 1-3% のみ。**理由は案 α が K=50 を実現できない (3-6 のまま)** | × (期待外れ、副次発見) |
| 局所で genesis ≠ shuffled | l_post_local_* で明確差 | ✓ K=5 で l_post_local_link_count Δ +5、K=50 で pool size 違いから Δ -69 | ✓ |
| state_E vs random_nodes | 両方とも genesis と差を出す方向は同じ、state_E は破壊度大 | ✓ K=5 で genesis-state_E Δ alive_l=-33、genesis-random Δ alive_l=+5 (符号も違う) | ✓ |
| 出し方で系反応違う (層 2) | 局所では明確差、global は弱い | ✓ K=5 local_link_count Δ=+5 (genesis-state_E)、global は rel 6% | ✓ |
| genesis_driven 案 α が機能 | K=50 でも 50 nodes 選べる | **× K=50 で target_n が 3-6**、案 α 規模制約露呈 | × (本命設計の限界) |

→ 主に **(a) K=50 全体差期待外れ** と **(b) 案 α 制約発見** が想定外。Taka 規律「想定見直し」が必要。

---

## 3. K 別 出し方差 比較 (Δ)

### K=5

| 比較 | g_alive_l | g_labels_active | g_mean_E | l_local_link_count | l_local_link_S | d_local_E |
|---|---|---|---|---|---|---|
| genesis - shuffled_state_E | -33 (1.05%) | -9 (6.00%) | -0.011 (5.76%) | +5 (100%) | +1.02 (100%) | -0.032 (877%) |
| genesis - shuffled_random | +5 (0.16%) | +3 (2.00%) | -0.016 (8.13%) | +4 (80%) | +0.90 (88%) | -0.028 (777%) |

### K=50

| 比較 | g_alive_l | g_labels_active | g_mean_E | l_local_link_count | l_local_link_S | d_local_E |
|---|---|---|---|---|---|---|
| genesis - shuffled_state_E | -27 (0.86%) | -5 (3.33%) | -0.025 (12.80%) | **-69** (986%) | -2.59 (210%) | -0.036 (953%) |
| genesis - shuffled_random | +33 (1.05%) | -1 (0.67%) | -0.025 (13.04%) | **-77** (1100%) | -2.33 (188%) | -0.035 (913%) |

注: K=50 の Δ は genesis (target_n 3-6) と shuffled (target_n 50) の **pool size 差**が混入。公平比較ではない。

---

## 4. 層 1 / 層 2 判定 (Web Claude §5)

### 4.1 層 1 (基本): 外部書き出し→取り込み機能するか

**`external_loop_functional`** ✓

- 全 6 conditions で physics.inject が物理層 (state.E / alive_n / 一部 link) を変化させる
- inject 前後で local_mean_E が変化、local_link_count が +0〜+7 変化
- 第 2 段階 attribute 保持のみとは違う、戻しが Genesis に効く

### 4.2 層 2 (踏み込み): 出し方の違いが系の違いを生むか

**`output_method_matters` (条件付)** ✓

- 局所スケール (radius=8) では出し方ごとに **明確な差** (l_post_local_link_count Δ 大、l_post_local_link_S Δ 大、d_local_mean_E Δ 大)
- ただし条件:
  - global window 末では弱い (rel 1-6%)
  - 案 α の規模制約で K=50 不公平比較
  - 「Genesis 由来 (主体性) で違う」なのか「Genesis 状態を反映した結果として違う」なのか、derive_action が Code A 外部ロジックである以上区別不能

### 4.3 第 4 段階 (loop 崩壊) への含意

`output_method_matters` が成立した → 第 4 段階で「どう出せば loop 崩れるか」の作業に進められる:
- 出し方変えれば系反応変わる = loop 崩壊の操作変数あり
- 案 α 制約のため derive_action 案 β/γ への切り替えで本命比較が必要

---

## 5. Web Claude 3 誤りの訂正 (§0) の検証

| 誤り | 訂正の妥当性 (2nd smoke 結果より) |
|---|---|
| 「K=5 は良いが K=50 は神の手」 | ✓ 訂正正しい (K の数は神の手と無関係、shuffle で判定)、ただし **案 α では K=50 が物理的に成立しない** 新制約発見 |
| 「微小なら出ないのは期待通り」 | ✓ 訂正正しい (K=5 全体差ほぼゼロは想定通り) |
| 「window スケールが粗すぎた」 | △ window 末でも局所 (radius 8) なら出し方差は明確、ただし step 単位記録は v82 制約で実装困難。局所スケールで代替可能 |

→ 3 誤り訂正の方向性は正しいが、**「v82 step_window の制約で per-step 記録不可」** を Code A が補足発見。期待事前明示 §2 で代替手法 (局所 + 5 windows) を採用、結果として「window 末でも局所なら差見える」を実証。

---

## 6. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 観察方法を疑う (Web Claude 3 誤り訂正) | ✓ §5 で訂正の検証、局所観察で代替 |
| 集団平均の罠 (空間 + 時間) | ✓ 局所 (radius 8) + 全体 + 5 windows |
| 期待/目的を先に明示 | ✓ stage3_step_b2_expectations.md で事前確定 |
| 結果が想定と合わなければ想定見直し | ✓ §2 で K=50 期待外れ + 案 α 制約を提示 |
| 結果がでない想定を潰す | ✓ §4.3 第 4 段階の作業に進める足場 |
| 神の手回避 | ✓ shuffle 3 種で多角検証 |
| 物理層 frozen | ✓ unified/stage3_subjectivity/ 配下のみ |
| 判定語制限 | ✓ 機能する/差ある/出ない |
| Atom と Genesis 分離 | ✓ Genesis state のみ |
| smoke 後止まる | ✓ **本報告 gate** |

---

## 7. 副次発見 + Taka 判断要請

### 7.1 副次発見: 案 α の規模制約

| 観察 | 含意 |
|---|---|
| genesis_driven K=50 で n_injected が 3-6 | 「最大 label の E top-K」は label core size に律速 |
| 結果として K=50 比較は不公平 | global Δ が pool size 差を反映 |
| Web Claude 期待「K で規模効果」が崩壊 | 案 α では K を大きくできない |

### 7.2 derive_action 案 β/γ への切り替え検討

| 案 | 内容 | K 上限 |
|---|---|---|
| **β: 全 label から phase_sig 中心 node を 1 つずつ** | 各 label の代表 node を集める | labels 数 (現状 150-350) |
| **γ: alive_l の次数 ハブ node 上位 K** | リンク次数 (degree) 上位 | alive_n 全体 |
| **δ: 上位 K labels から各 1 node** | label を share でソート、上位 K label の代表 | labels 数 |
| **ε: phase_sig が密集している領域から K** | phase クラスタの中心領域 | alive_n 全体 |

### 7.3 判断ポイント (Taka / Web Claude)

| # | 判断要 |
|---|---|
| ① | 2nd smoke の出口 (層 1 functional + 層 2 matters) で第 3 段階 終了か、3rd smoke で案 β/γ 検証か |
| ② | フル 24 seeds 並列に進む前に、derive_action を案 β/γ に切り替えるか (フル前 smoke が必要) |
| ③ | 第 4 段階「どう出せば loop 崩れるか」に直接進むか、第 3 段階で derive_action 探索を続けるか |
| ④ | 「Genesis 状態依存」と「ESDE 内部機構による自己決定」の区別 (Web Claude §1 で明記) について、本 smoke で「Genesis 状態依存」までは確認、ESDE 内部機構の検証は別段階か |

### 7.4 Code A 推奨

**推奨 1**: 3rd smoke で **案 β (全 label phase_sig 中心 1 nodes ずつ)** + **案 γ (alive_l 次数ハブ K)** を K=50 で実行 → 案 α と比較
- 計算量: 2 案 × 1 seed × 5 windows ≈ 10 分
- これで案 α 制約を超えた「公平な K=50 比較」が可能

**推奨 2**: 3rd smoke 結果次第:
- 案 β/γ で K=50 全体差出る → 規模効果あり、案 α 制約だったと確定 → フル進行
- 案 β/γ でも全体差出ない → 規模効果なし、第 4 段階で別操作変数を探す

---

## 8. 出力ファイル

- `stage3_step_b2_smoke.py` (実装)
- `stage3_step_b2_expectations.md` (事前期待)
- `stage3_step_b2_smoke_report.md` (本文書)
- `run_smoke2/smoke2_full.parquet` (30 rows = 6 cond × 5 win)
- `run_smoke2/smoke2_last_window.parquet`
- `run_smoke2/smoke2_diffs.parquet`
- `run_smoke2/smoke2_run_summary.json`

---

## 9. 一文サマリ

第 3 段階 Step B2 2nd smoke 報告 (Code A、2026-05-31、Web Claude 2nd smoke 設計 + Web Claude 3 誤り訂正 + Taka 「観察を細かく + 期待/目的セットで明示 + 出し方の重要性で第 4 段階を先に潰す」準拠、Step B2 期待事前明示後実装) として、6 conditions (3 出し方 × K 2 種) × 5 windows × N=5000 で 1195 秒 (19.9 分、想定 20-40 分内)、出口 (層 1 = `external_loop_functional` ✓ 全 conditions で physics.inject で state.E/alive_n/link 変化 / 層 2 = `output_method_matters` 条件付 ✓ 局所スケール radius=8 で l_post_local_link_count Δ +5 や K=5 で genesis-state_E rel 100% など明確差、ただし global は rel 1-6% 弱い + 案 α 規模制約で K=50 比較不公平)、副次発見 (重要 = **案 α が K=50 要求しても n_injected 3-6 のまま** で最大 label core node 数に律速、Web Claude 期待「K で規模効果」が物理的に成立せず)、期待 vs 結果比較表 §2 (inject 局所 E 増加は pre_E 依存で一律 +0.6 でなく △ / 1 window 後の拡散観察不可 window 内平準化で × / K=5 全体差ほぼゼロは想定通り ✓ / K=50 全体差は案 α 制約で × 期待外れ / 局所差 ✓ / shuffle 種別差 ✓ / 出し方差 ✓ / 案 α 機能 ×)、Web Claude 3 誤り訂正の検証 §5 (K=5/50 神の手無関係 ✓ / 微小は出ない期待通り ✓ / window スケール粗すぎは局所観察で代替可能 △ Code A が v82 step_window 制約 per-step 不可を補足発見)、規律遵守 (観察方法疑う + 局所/全体 + 期待先出し + 想定見直し + 第 4 段階足場 + 神の手回避 + frozen + 判定語制限 + Atom/Genesis 分離 + smoke 後止まる本報告 gate)、Taka 判断 4 件 + Code A 推奨 (3rd smoke で案 β phase_sig 中心 1 ノードずつ + 案 γ alive_l 次数ハブ K=50 で公平比較、10 分予測、結果で案 α 制約裏付けかフル進行か第 4 段階直行か)、書込み unified/stage3_subjectivity/ 配下のみ。

---

**Step B2 2nd smoke end. gate (Taka / Web Claude 判断待ち)。判断後 3rd smoke (案 β/γ) または フル直行または 第 4 段階移行に進む。**
