# 第 3 段階 Step B — smoke 報告 (gate)

**Date**: 2026-05-31
**Author**: Code A
**Status**: smoke 完了、**gate (止まって報告)**
**親**: 第 3 段階実装指示 (Web Claude、Taka 承認、physics.inject 採用、案 α、smoke は random_nodes)

---

## 0. 出口判定 (smoke 段階)

### **`subjectivity_signal_weak`** (兆候極めて弱い)

戻し実効化は OK だが、shuffle と genesis_driven で集計指標差は **完全ゼロ** (mean_E のみ Δ=-0.00025)。フル前に対策必要 (§5)。

---

## 1. 実行結果

### 1.1 設定 + 実行時間
- 1 seed (42)、maturation 3、tracking 1、window_steps 100、N=5000、K=5
- 2 conditions: genesis_driven (案 α) + shuffled_random_nodes
- 全体 352.3 秒 (1 condition 当たり ~176 秒、補足 187 秒と整合)

### 1.2 4 確認項目

| # | 確認 | 結果 |
|---|---|---|
| 1 | 統合 (起動 + 外部接続) 動くか | ✓ 両 condition 共に 191→164 CIDs を観察、4 window 完走 |
| 2 | physics.inject で戻し実効するか | ✓ target nodes の E が **0.20→1.0** に上昇 (両 condition) |
| 3 | genesis_driven vs shuffled の兆候 | **△ 差ほぼゼロ** (alive_l/labels/torque すべて完全一致) |
| 4 | 物理層 frozen (既存触らず) | ✓ unified/stage3_subjectivity/ 配下のみ書き込み |

### 1.3 集計指標 (両 condition、全 iter)

| condition | iter | alive_l | labels_non_macro | labels_active | torque_events | mean_E |
|---|---|---|---|---|---|---|
| genesis_driven | 0 | 3765 | 350 | 350 | 3372 | 0.5744 |
| genesis_driven | 1 | 3394 | 280 | 280 | 3142 | 0.3771 |
| genesis_driven | 2 | 3260 | 191 | 191 | 2466 | 0.2721 |
| genesis_driven | 3 | 3097 | 164 | 164 | 1625 | 0.2523 |
| shuffled_random | 0 | 3765 | 350 | 350 | 3372 | 0.5744 |
| shuffled_random | 1 | 3394 | 280 | 280 | 3142 | 0.3774 |
| shuffled_random | 2 | 3260 | 191 | 191 | 2466 | 0.2725 |
| shuffled_random | 3 | 3097 | 164 | 164 | 1625 | 0.2526 |

→ alive_l / labels_* / torque_events が **4 window すべて完全一致**。mean_E のみ第 4 桁で極小差。

### 1.4 inject の物理的効果 (両 condition で確認)

| condition | iter | target_first | pre_E_mean_target | post_E_mean_target | injected_count |
|---|---|---|---|---|---|
| genesis_driven | 0 | 250 | 0.988 | **1.000** | 3 |
| genesis_driven | 1 | 3696 | 0.998 | **1.000** | 5 |
| genesis_driven | 2 | 4833 | 0.572 | **1.000** | 5 |
| genesis_driven | 3 | 2563 | 0.538 | **1.000** | 5 |
| shuffled_random | 0 | 714 | 0.559 | **1.000** | 5 |
| shuffled_random | 1 | 382 | 0.343 | 0.939 | 5 |
| shuffled_random | 2 | 3091 | 0.236 | 0.836 | 5 |
| shuffled_random | 3 | 3602 | 0.204 | 0.804 | 5 |

- inject_amount = **0.6** (genesis_physics.py:53 default)
- inject_pair_radius = 8、inject_link_strength = 0.3
- inject が物理的に効いている (E が +0.6 されて clamp 1.0 でほぼ 1.0 になる)

---

## 2. 観察事実 (判定語制限遵守)

### 2.1 戻し実効化は動く

`physics.inject(state, target_nodes=...)` で:
- state.E が target で +0.6 加算 (clamp 1.0 上限)
- inject_pair_radius=8 内のペアに link 追加 (inject_link_strength=0.3)
- attribute (_stage3_external_inputs) も観察用に併用

これは **第 2 段階の attribute 保持のみとは違う動作** で、Genesis 物理に書き込んでいる。

### 2.2 集計指標に差が出ない理由 (推測)

**5 nodes (= N の 0.1%) の inject では、5000 nodes の集計指標を動かせない。**

両 condition で w=0,1,2,3 の alive_l/labels_active/torque_events が **完全一致**。これは:
- engine.rng (seed=42) で **両 condition は決定論的に同じ進化**
- inject が次 window の物理を変えていない or 変えても 5000 nodes 集計の粒度に埋もれている
- mean_E のみ第 4 桁で差 (極微小)

### 2.3 「神の手」判定リスク

shuffled でも下流指標が同じ → derive_action のロジックが集計指標を動かしていない = Genesis 状態依存と言える兆候が **smoke 範囲では出ていない**。

ただし以下の理由で「神の手確定」と判断するには早い:
- K=5 が小さすぎる (massive な物理スケールに対して埋もれる)
- 1 seed のみ (統計判定不能)
- window_steps=100 が短すぎる (inject 影響の伝播時間が不足)
- mean_E に微小差が出ていることは「物理層では差がある」傍証

---

## 3. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ 既存 developmental/v105 等触らず、新規 instance のみ |
| 全階層調べる | ✓ Step A で実施済、virtual_layer_v9 import 経路を v910 経由に修正 |
| 想定するな聞け | ✓ 兆候弱い理由 + 対策を §5 で Taka 提示 |
| 神の手回避 (shuffle で判定) | ✓ shuffle 比較実装、結果が「差なし」 |
| self-fulfilling baseline 検査 | ✓ smoke は σ 判定せず兆候のみ、フルで σ 2 倍 |
| 判定語制限 | ✓ 「成功/失敗」未使用、「動く/動かない」「差ある/なし」 |
| Atom と Genesis 分離 | ✓ Genesis state のみ使用 |
| smoke 後止まる | ✓ **本報告で gate** |
| 示せる範囲明記 | ✓ §2.3「Genesis 状態依存と言える兆候は smoke で出ていない」 |

---

## 4. Step A 不明点の smoke 確認結果

| Step A 不明 | smoke 実測 |
|---|---|
| inject_amount default | **0.6** (genesis_physics.py:53) |
| 二重発火 (background_seeding と) | 観察上は破綻なし、E は clamp 1.0 上限で安定 |
| 外部処理 identity | OK (本 smoke で identity 使用) |

### 4.1 副次発見

- VirtualLayerV9 は `autonomy/v90/virtual_layer_v9.py` ではなく **`primitive/v910/virtual_layer_v9.py`** が現役 (feedback_gamma/feedback_clamp kwargs 付き版)
- autonomy/v90/virtual_layer_v9.py は **kwargs 無し古版** (ハードコード値)
- v918_memory_readout.py は `from virtual_layer_v9 import VirtualLayer as VirtualLayerV9` で v910 を import
- Step A 認識確認では autonomy/v90/ を見て差を見落とした → smoke で発見、import 経路修正済 (stage3_step_b_smoke.py:30)

---

## 5. gate 判断要請 (Taka / Web Claude)

### 5.1 結論

smoke の `subjectivity_signal_weak` は「神の手確定」ではなく **「シグナルが集計の粒度に埋もれて見えない」可能性が高い**。

### 5.2 対策案 (フル前に検討)

| 案 | 内容 | 効果見込み |
|---|---|---|
| **A. K を増やす** (K=50 or 100) | inject の物理スケール拡大 | 集計指標が動きやすくなる |
| **B. inject_amount を 大** (custom params) | E の変化量倍増 | physics.inject の effect 強化、ただし既存 default 0.6 から外れる |
| **C. shuffle を state_E に変更** | E 値全シャッフルで top-K | Web Claude 指示書本命、より直接的な状態依存判定 |
| **D. window_steps を増やす** (200) | inject 影響の伝播時間確保 | フルでは ws=500 なので smoke でも 200-300 で確認 |
| **E. seed を増やす** (3 seeds smoke) | 統計的判断可能に | 1 seed では微小差を区別できない |
| **F. derive_action を別案 (β/γ)** | 案 α が局所過ぎ可能性 | β = phase_sig 中心 node、γ = alive_l ハブ node |

### 5.3 Code A 推奨

**A + C + D の組み合わせで 2nd smoke** を推奨:
- K=50 (10x スケール)
- shuffle を state_E に切り替え (Web Claude 指示書本命)
- window_steps=300 (現状 100 の 3x)
- これでも兆候出ない → 案 β/γ または現状の derive_action 設計を再検討
- 兆候出る → そのままフル設定 (24 seeds 並列)

### 5.4 計算量見積もり

| 設定 | 1 condition × 1 seed | 2 conditions × 1 seed | 2 conditions × 24 seeds 並列 |
|---|---|---|---|
| smoke (mat 3, track 1, ws 100, K=5) | 176 秒 | 352 秒 (実測) | - |
| 2nd smoke 案 (K=50, ws 300, 1 seed) | 推定 520 秒 | 推定 1,040 秒 (~17 分) | - |
| フル (mat 20, track 10, ws 500) | 推定 5,500 秒 (~92 分) | 推定 11,000 秒 (~3 時間) | **推定 3 時間** (24C48T 並列) |

→ 2nd smoke は ~17 分、フルは 24 seeds 並列で約 3 時間。

### 5.5 判断ポイント

| # | 判断要 |
|---|---|
| ① | 2nd smoke (K=50 + state_E + ws=300) で再確認するか、直接フルに進むか |
| ② | Code A 推奨 A+C+D で良いか、別案 (B / E / F) を加えるか |
| ③ | 2nd smoke 不要なら 24 seeds 並列フル直行で OK か |
| ④ | shuffle を state_E にする場合の実装方針 (E 値を全 node 間で permute → top-K 選択) で OK か |

---

## 6. 出力ファイル

- `stage3_step_b_smoke.py` (実装)
- `stage3_step_b_smoke_report.md` (本文書)
- `run_smoke/smoke_state.parquet` (8 rows、両 condition × 4 iter)
- `run_smoke/smoke_inject.parquet` (8 rows、inject effect 記録)
- `run_smoke/smoke_summary.parquet` (14 rows、metric × condition)
- `run_smoke/smoke_run_summary.json` (実行設定 + diffs_final_iter)
- `sandbox_smoke/state_{condition}_iter{w}.json` (8 ファイル、外部接続記録)

---

## 7. 一文サマリ

第 3 段階 Step B smoke 報告 (Code A、2026-05-31、Web Claude 第 3 段階実装指示準拠 physics.inject + 案 α + shuffle_random_nodes、Taka 承認案で 1 seed mat3 track1 ws100 K=5 N=5000 2 conditions 並行) として、出口 `subjectivity_signal_weak` (兆候極めて弱い)、4 確認項目結果 (統合動く ✓ / physics.inject で target_nodes E が 0.2→1.0 戻し実効 ✓ / shuffle 差ほぼゼロ alive_l・labels・torque すべて完全一致 mean_E のみ Δ=-0.00025 △ / 物理層 frozen ✓)、集計指標 4 iter で両 condition 完全一致 (engine seed=42 決定論 + 5 nodes inject が 5000 nodes massive 物理に埋もれた可能性)、inject 物理効果は両 condition で確認 (genesis_driven target E 0.54→1.0 / shuffled target E 0.20→0.94 と 0.6 加算 clamp 1.0 上限)、神の手判定リスクあるが確定でなく「シグナルが集計粒度に埋もれた」可能性高い、Step A 不明 3 件解消 (inject_amount=0.6 / 二重発火破綻なし / identity OK)、副次発見 (VirtualLayerV9 は primitive/v910 経由が現役、autonomy/v90 古版を Step A で見落とし → import 経路修正済)、対策 6 案 (A K=50 増 / B inject_amount 大 / C shuffle state_E / D window_steps 200-300 / E seed 増 / F derive_action 別案)、Code A 推奨 A+C+D 組合せで 2nd smoke 17 分 → 兆候出たらフル 24 seeds 並列 3 時間、計算量見積もり (2nd smoke 17 分・フル 24seeds 並列 3 時間)、規律遵守 (物理層 frozen + 全階層調査 + 想定せず提示 + 神の手回避 shuffle 比較 + self-fulfilling 検査 + 判定語制限 + Atom/Genesis 分離 + smoke 後止まる本報告 gate + 示せる範囲明記)、Taka 判断 4 件 (2nd smoke するか / Code A 推奨 OK か / 直行フル OK か / state_E shuffle 実装方針 OK か)、書込み unified/stage3_subjectivity/ 配下のみ。

---

**Step B smoke end. gate (Taka / Web Claude 判断待ち)。判断後 2nd smoke or フル 24 seeds 並列に進む。**
