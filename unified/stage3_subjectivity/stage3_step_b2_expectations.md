# 第 3 段階 Step B2 — 期待/目的の事前明示 (Taka 規律準拠)

**Date**: 2026-05-31
**Author**: Code A
**Status**: 実装前、期待を確定するための事前文書
**親**: Web Claude 2nd smoke 設計書 §4

---

## 0. なぜ事前に書くか

Taka 規律「期待しているものとそうする目的をセットでまとめ、実際の結果と比較する」。期待を事後に書くと post-hoc 合理化に陥る。実装前に確定する。

## 1. 過去 V10 台「少ない刻み」実績 (確認結果)

| 文書 | 刻み実績 |
|---|---|
| `developmental/v111/v111_code_recognition_check_v2.md` | t_offset ±50 step、**5 step 刻み、21 samples**、274K snapshots |
| `developmental/v10x_implementation_spec.md:705` | beta_lifecycle q_c_inherited event 起点で T-50 vs T+50 を 5 step 刻み |
| `primitive/v913/v913_persistence_birth.py:1506` | cumulative_step 概念 (per-step トラッキング) |

→ 「5 step 刻み」が標準実績。

## 2. ただし v82 step_window の制約

`autonomy/v82/esde_v82_engine.py` の step_window は:
- per-step: physics + chem + intruder + decay (1-step ループ内)
- per-window: stress / observation / virtual.step / window_count++ / frames.append

→ `step_window(steps=5)` を 20 回呼ぶと per-window 処理が **20× 暴走**、window_count が 20× 速く進む = 仮想層 semantics が破壊される。

### 2.1 代替手法 (semantics を壊さず徹底観察)

| 手法 | 内容 |
|---|---|
| (a) inject 直前 / 直後の state スナップショット | physics.inject 関数呼出を挟んで state.E/alive_l/alive_n を直接読む |
| (b) 局所メトリクス (target_nodes + radius=8 近傍) | inject の局所効果は radius 8 内に集中、近傍だけ集計 |
| (c) 5 windows 連続記録 | mat 3 + track 2 で 5 window 分の進化を window 末で記録 (inject 伝播追跡) |

→ window 単位 + 局所スナップショット + 5 windows = 1st smoke で見えなかった「inject の物理効果」を捉えられる。

---

## 3. 期待/目的の事前明示 (§4 表 pre 列)

### 3.1 局所空間 (radius=8 内の集計)

| 観察軸 | 期待 (実装前) | 目的 |
|---|---|---|
| inject 直前 → 直後の局所 E 変化 (両 condition) | 両 condition で **+0.6 程度** (inject_amount default) | physics.inject が両 condition で物理的に効くことを確認 (戻し実効化、層 1) |
| 1 window 後の局所 E (genesis_driven) | inject 後の高 E が周辺ノードに **拡散** (virtual.torque + autogrowth で) | 戻しが次 step 進化に影響することを局所で見る |
| 1 window 後の局所 E (shuffled) | random 位置なので近傍に既存 label がない場合、**孤立した E 上昇のまま** で拡散しにくい | genesis が選んだ場所と random 場所で局所伝播が違う可能性 |

### 3.2 全体空間 (window 末集計)

| K | 期待 (実装前) | 目的 |
|---|---|---|
| K=5 (1st smoke と同じ) | genesis_driven と shuffled の差は **ほぼゼロ** (微小介入が 5000 nodes に飲み込まれる、1st smoke 結果と一致) | window 平均の罠を確認、想定通りなら罠回避方法 (局所観察) の妥当性を裏付ける |
| K=50 (10x スケール) | 全体指標 (alive_l, labels_active) で **差が出始める** (規模を上げれば全体構造が動く) | 規模効果の確認、ただし神の手判定でない (shuffle で判定) |

### 3.3 出し方 (genesis_driven vs shuffled 種類別)

| 比較 | 期待 (実装前) | 目的 |
|---|---|---|
| genesis_driven vs shuffled_random_nodes | random は alive_n から無作為、genesis は label core から E top-K → genesis target は **既に E が高い node** が多い、shuffle は random なので E が低い node も多い | 「何を出すか」の差が inject 効果 (pre_E → post_E の幅) に出る |
| genesis_driven vs shuffled_state_E | state_E permute で E top-K 選び → genesis と同じ「高 E node」を選ぶが **空間位置がバラバラ**。genesis は label 内連続 node、shuffle は離散 | 「位置の連続性」の差を見る。state_E shuffle は「E 値」では同じ刺激量、「空間位置」だけ違う = 主体性検証の本命 |
| shuffled_state_E vs shuffled_random_nodes | state_E は high-E に集中、random は全 E 範囲。inject 後の **新規 link 生成数** に差が出るかも (radius=8 内ペア確率) | shuffle 粒度の効果 |

### 3.4 層 1 (機能) と 層 2 (出し方) 期待

| 層 | 期待 (実装前) |
|---|---|
| 層 1 (戻しが Genesis に効くか) | **functional**: physics.inject で局所 E が +0.6 する (1st smoke で既に確認)、1 window 後も近傍 state に変化が残る |
| 層 2 (出し方で系の反応が違うか) | **partially matters**: K=50 全体差 + 局所差 (genesis 連続 node vs shuffled 離散) は出る、ただし window 末全体は K=5 では出ない |

---

## 4. 結果が想定と合わなかったときの対応 (Taka 規律事前明示)

| 想定外 | 対応 |
|---|---|
| K=5 全体で差が出る | 「微小介入は飲み込まれる」想定見直し、ロジック再検討 |
| K=50 全体で差が出ない | inject_amount / inject_pair_radius を疑う、または「規模効果」の前提見直し |
| 局所 1 window 後で差が見えない | 観察 window が短すぎ、tracking 増やす |
| state_E と random_nodes で差が出ない | shuffle 粒度の効果なし、derive_action 案 β/γ へ |
| 戻しが効かない (層 1 nonfunctional) | physics.inject 使い方再検討、第 2 段階 attribute 保持に戻る |

---

## 5. 実装条件

- 6 conditions: 3 出し方 (genesis_driven 案 α / shuffled_state_E / shuffled_random_nodes) × 2 K (5, 50)
- maturation 3 + tracking 2 = **5 windows**、window_steps 100、N=5000、seed=42
- 各 window 末: 全体集計 + inject 直前局所 + inject 直後局所
- 各 condition 独立 engine instance (seed 42 で進化、inject 介入が rng シーケンスを少しずつズラす)
- 出力: stage3_step_b2_*.parquet + report

---

## 6. 計算量見積もり

- 1st smoke: 2 conditions × 4 windows = 352 秒
- 2nd smoke: 6 conditions × 5 windows ≈ 1,320 秒 + 局所スナップショットオーバーヘッド ≈ **22-30 分**
- Web Claude 想定 (20-40 分) 範囲内

---

**Step B2 期待事前明示 end. 実装に進む。実装後 §4 結果列を埋めて期待 vs 実際を比較。**
