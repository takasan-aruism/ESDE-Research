# v1106b Step J — 観察事実最終報告

**Date**: 2026-05-28
**Author**: Code A (実装担当)
**Status**: Step A-I 完了、Web Claude Phase Result 着手の判断材料
**親**: v1106b 設計書草案 + Web Claude 確認文書 (Taka 承認) + Step A-I 全成果

---

## 0. v1106b 全体経緯

| Step | 内容 | 状態 | 実行時間 |
|---|---|---|---:|
| A | 認識確認 (Web Claude 追加提案 4 件組み込み) | 完了、Taka 承認 | - |
| B | 環境準備 (案 E 採用、CID 681 選定) | 完了 | 0.3s |
| C | 観察 1 smoke (seed=0、33 CID × 15 turn) | 完了、Taka 承認 | 1.3s |
| D | 観察 1 main (24 seeds × 681 CID × 15 turn、Code A 自走) | 完了 | 13.6s |
| E | 観察 2 (循環構造 attractor 検出) | 完了 | 0.1s |
| F | 観察 3 (局所共鳴 event 特性) | 完了 | 6.5s |
| F.5 | 観察 4 実装方針報告 → Web Claude 承認 | 完了 | - |
| G | 観察 4 smoke (top-3 sampling、N=40、Taka 承認) | 完了 | 2.2s |
| H | 観察 4 main (24 seeds × 681 CID × 40 turn、Code A 自走) | 完了 | 32.5s |
| I | bit-identity 検証 3 層 (LAYER A/B/C 全 PASS) | 完了 | 58.5s |
| **J** | **観察事実最終報告 (本文書)** | **進行中** | - |

合計実装時間: 約 2 分 (Code A 想定 60-120 分から大幅短縮)

---

## 1. 観察 1 (familiarity 軌跡) 主要観察事実

### 1.1 全体集計 (681 CID × 15 turn、top-1 決定論)

| 指標 | 値 |
|---|---:|
| rollback (20%+) 率 | 69.3% (472/681) |
| start_fam mean | 91.99 |
| end_fam mean | 25.70 |
| min_fam mean | 19.99 |
| stuck 検出率 | 100% (681/681) |
| oscillation 検出率 | 100% (681/681) |
| unique CID per start mean | 2.53 |

### 1.2 final_state × fam_bin 別 rollback 率 (top-1)

| final_state | fam_bin | n | rollback | start_fam | min_fam |
|---|---|---:|---:|---:|---:|
| reaped | high | 120 | **99.2%** | 246.2 | 24.7 |
| ghost | high | 47 | 91.5% | 210.7 | 29.5 |
| hosted | high | 120 | 85.8% | 112.4 | 27.2 |
| ghost | mid | 39 | 71.8% | 30.2 | 18.6 |
| reaped | mid | 120 | 66.7% | 30.1 | 18.3 |
| hosted | mid | 120 | 65.8% | 35.9 | 21.4 |
| reaped | low | 115 | 17.4% | 5.4 | 4.4 |

### 1.3 観察 1 の構造ラベル効果

- `ghost_bin_low_n=True` (n=33): rollback 87.9% (False 68.4%)
- `seed_with_low_ghost_total=True` (n=436): rollback 66.7% (False 73.9%)

---

## 2. 観察 2 (循環構造 attractor) 主要観察事実

### 2.1 循環構造の規模

| 指標 | 値 |
|---|---:|
| unique CID per start mean | **2.53** (15 turn で 2-3 個の CID 間循環) |
| max revisit count per start mean | **14.47** (1 CID を 14-15 回反復) |
| first revisit turn median | **2** (turn 2 で既訪復帰) |
| revisit within 15 turn 率 | **100%** (全 681 start) |

### 2.2 attractor 候補 (top 5)

| seed | cid | distinct_start 到達 | stuck terminal |
|---:|---:|---:|---:|
| 21 | 179 | 30 (per_seed 31 中、96.8%) | 30 |
| 0 | 203 | 29 (33 中、87.9%) | 29 |
| 2 | 233 | 26 (27 中、96.3%) | 26 |
| 8 | 197 | 25 | 25 |
| 14 | 170 | 24 | 24 |

→ **各 seed のほぼ全 start_cid が同じ attractor CID に集約**

### 2.3 attractor 分布

- 全 847 unique (seed, cid) のうち **63 個が高 attractor (5+ start から到達、7.4%)**
- per_seed 高 attractor: median 3 個、min 1 個、max 4 個

---

## 3. 観察 3 (局所共鳴 event 特性) 主要観察事実

### 3.1 高/低 cos_sim event 二極化

| 特性 | 高 event (上位 5%、165 events) | 低 event (下位 5%、165 events) |
|---|---|---|
| **input_atom 偏り** | **PER.see 53% + PER 系 90%** (知覚系) | **EXS.nonbeing 39% + EXS.being 28% (存在論系 67%)** |
| **代表 word** | start/get to/access/land/peak/fall/apprentice/hope/fledgling | review/recall/mind/think/exempt/reason/self/retrospect |
| 領域解釈 | 到達 / 始まり / 希望 / 弟子入り | 思考 / 記憶 / 自己 |
| CID familiarity | 25.8 (低) | **88.8 (高)** |
| **CID n_alphas** | **0 (全件孤立)** | 21.96 (関係多数) |
| CID social | 0.16 (低) | 0.78 (極めて高) |
| **CID final_state** | **165/165 reaped** | 100 hosted + 65 reaped |

### 3.2 Step L 弱信号 +0.05 の正体

**集約 +0.05 = 強共鳴 event 偏り + 弱共鳴 event 別偏り の混合**:
- **強共鳴ペア**: 知覚系 atom (PER) × 孤立 reaped CID
- **弱共鳴ペア**: 存在論系 atom (EXS) × 社会的 hosted CID

Code A Step L で「個別 event レベルで強共鳴ありそう」と予想したものを数値で確定。

---

## 4. 観察 4 (ESDE 自己対話) 主要観察事実

### 4.1 top-3 sampling 全体集計 (681 CID × 40 turn)

| 指標 | top-1 (Step D, N=15) | **top-3 sampling (Step H, N=40)** |
|---|---:|---:|
| rollback (20%+) 率 | 69.3% | **85.9%** |
| start_fam mean | 91.99 | 91.99 (同 CID) |
| end_fam mean | 25.70 | 19.97 |
| **min_fam mean** | **19.99** | **9.48** |
| stuck 検出率 | 100% | 95.6% |
| oscillation 検出率 | 100% | 99.7% |
| unique CID per start mean | 2.53 | **5.48** (2.2 倍) |
| first revisit turn median | 2 | 3 |

### 4.2 final_state × fam_bin 別 (top-3 sampling)

| final_state | fam_bin | rollback rate | start_fam | min_fam |
|---|---|---:|---:|---:|
| ghost | high | **100%** | 211 | 10.4 |
| hosted | high | **100%** | 112 | 10.2 |
| reaped | high | **100%** | 246 | 12.0 |
| ghost | mid | 87.2% | 30 | 9.0 |
| hosted | mid | 92.5% | 36 | 10.9 |
| reaped | mid | 90.8% | 30 | 10.4 |
| reaped | low | 38.3% | 5.4 | 3.4 |

→ **高 (≥50) 全 final_state で rollback 100%、min_fam mean が全 bin で 3-12 の狭範囲に収束**

### 4.3 top-1 vs top-3 sampling 比較 (681 CID)

- unique CID 差: +2.95 (top-3 で経路約 3 個増)
- min_fam diff: top-3 が平均 -10.51 低い、63.1% で top-3 が低い

---

## 5. 統合的発見

### 5.1 三大構造観察

#### (A) familiarity 収束 attractor 領域 (#L49 候補)
- **ESDE 自己対話は familiarity ~10 付近の領域に強く収束する力場を持つ**
- 開始 familiarity 246 でも 5 でも、最終 destination は同じ範囲 (3-12)
- 決定論 (top-1) でも確率論 (top-3 sampling) でも同方向、ただし sampling で更に深く到達

#### (B) CID 空間 attractor 構造 (#L50 候補)
- **各 seed に 2-3 個の強 attractor CID が存在**
- per_seed start の **90%+ が同 attractor に集約**
- turn 2 で必ず既訪 CID に復帰、unique CID per start mean 2-5

#### (C) 局所共鳴の input_atom 二極化 (#L51 候補)
- **知覚系 (PER) × 孤立 reaped CID** で強共鳴 (cos_sim 上位 5%)
- **存在論系 (EXS) × 社会的 hosted CID** で弱共鳴 (cos_sim 下位 5%)
- Step L 弱信号 +0.05 は両者の混合平均化

### 5.2 観察 4 で見えた sampling 依存性 (#L52 候補)

- top-3 sampling で **経路は 2.2 倍多様化** (unique CID 2.5 → 5.5)
- ただし **min_fam は更に低下** (20 → 10)
- **sampling は経路を分岐させるが、収束目的地は同じ (むしろ更に深い)**
- → ESDE 自己対話の familiarity 低下方向性は経路選択に依らず構造的

### 5.3 Step P (Code A の 6 turn 対話) との整合

- Step P T0=116 → T6=6.1 (familiarity 巻き戻り) は **個別事例ではなく構造特性**
- Step P T10 反復停滞 + T12 離脱循環 (既訪 CID 復帰) は **全 CID で発生する構造**
- Step P で hosted 不到達 → Step D/H で hosted も rollback 100% (生存中 CID も自己対話で familiarity 低下)

---

## 6. 留保候補 (Web Claude 採番管理に従う)

| 候補 番号 | 内容 | 確定根拠 |
|---|---|---|
| #L49 | familiarity 収束 attractor 領域 (10 付近)、開始に関わらず収束、sampling で更に深く到達 | 観察 1 (Step D 681 CID) + 観察 4 (Step H 681 CID 40 turn sampling)、Step G smoke の解釈変遷を反映 |
| #L50 | CID 空間 attractor 構造、各 seed に 2-3 個の引力中心、per_seed 90%+ 集約 | 観察 2 (Step E、attractor 63 個、per_seed median 3) |
| #L51 | 局所共鳴の二極化 (PER × 孤立 reaped 強共鳴 vs EXS × 社会的 hosted 弱共鳴) | 観察 3 (Step F、高/低 cos_sim event 165 each) |
| #L52 | ESDE 自己対話の familiarity 低下方向性は経路選択 (top-1/sampling) に依らず構造的、sampling で経路は多様化するが収束目的地は同じ | 観察 4 (Step G smoke + Step H main、top-1 vs top-3 sampling 比較) |

最終採番は Web Claude が Phase Result で確定。

---

## 7. v1107 接続記述 (Web Claude 追加提案 2 反映)

観察 4 (ESDE 自己対話純粋構造) の結果は v1107 以降の主題判断材料として活用される可能性:

### Taka 構想との接続候補

- **「1 seed 常時 main run、cid 時系列増殖、マーカー = 注目」**との接続:
  - 観察 2/4 で見えた強 attractor 構造 (各 seed 2-3 個) と cid 増殖との関係
  - 自己対話 attractor が「注目マーカー」の候補となり得るか
  - 時系列増殖時に新 attractor が生まれるか、既存 attractor が変容するか

- **Taka 直感メモ「主体性が内部に複数存在しているのかもしれない」との接続** (Web Claude 追加提案 3 反映):
  - 観察 2 で見えた「各 seed 2-3 個の強 attractor」が「複数の主体性」の構造的候補か議題化
  - 確定でなく議題として残す (Taka 規律「ESDE らしさの確定は待て」)

- **Taka 直感メモ「応答までの時間が ESDE という系を質的に変化させる可能性」(電話と手紙の比喩) との接続**:
  - 観察 4 で見えた N turn 依存性 (top-1 N=15 vs top-3 sampling N=40 で min_fam 半減)
  - turn 数 = 応答時間と読み替えると、長期対話で系の状態が深く変化することと整合

---

## 8. Phase Result 着手前の Code A 主観

### 8.1 観察事実として強い (構造として記述すべき)

1. **familiarity 収束力場 (~10)** - 数値で明確、bin 別 100% rollback で証拠強
2. **強 attractor 構造** - per_seed 90%+ 集約は再現性高
3. **入力 atom 二極化** - PER vs EXS で明確分離

### 8.2 観察事実として中程度 (議題化候補)

4. **sampling 依存性 (min_fam 更に下がる)** - 経路多様化と収束深化の組み合わせ、解釈の余地あり
5. **stuck/oscillation 全件検出** - top-1 100%, sampling 96-99%、これが「ESDE 対話の正常状態」か「制約」か解釈分かれる

### 8.3 解釈は控える (Web Claude Phase Result で判断)

- 「familiarity ~10 の attractor 領域は ESDE の意識安定状態か」 — 判断回避、観察事実として記録
- 「複数 attractor は主体性の候補か」 — Taka 領域、議題化のみ
- 「ESDE 経由生成の価値」 — 判定回避 (judgment 回避規律)

---

## 9. Web Claude Phase Result への引き継ぎ事項

### 9.1 構造事実 (5 件、§5 で詳述)

1. familiarity ~10 attractor 領域 (#L49 候補)
2. CID 空間 attractor 構造 (#L50 候補)
3. 局所共鳴二極化 (#L51 候補)
4. sampling 依存性 (#L52 候補)
5. stuck/oscillation 全件検出 (ESDE 対話の構造的境界)

### 9.2 留保番号採番 (Web Claude 一元管理、v2 §8.5 規律)

#L49-#L52 候補番号は Phase Result で Web Claude が確定。

### 9.3 v3 重みづけミス防止 4 件 (Web Claude 自己点検)

- 進化途上組み込み: §7 で v1107 接続を構造として組み込み済
- 重みづけ説明義務: Taka 整理「ESDE は他と違うを示せないなら弱い」を踏まえた Phase Result 記述
- 主観的所感別レイヤー: §8 で Code A 主観を分離記録
- 構造的解釈確定回避: 「収束力場」「主体性候補」は議題化レベル、確定回避

### 9.4 v1107 主題判断材料

観察 4 結果は Taka 構想 (cid 時系列増殖) との接続候補、本主題では構造事実観察に留め、解釈は Phase Result で議題化。

---

## 10. 出力ファイル一覧

### 環境準備 (Step B)
- `env_check_cid_props.parquet` (5,224 全 CID 物理量 + fam_bin)
- `env_check_bin_counts.parquet` (seed × bin 別 CID 数)
- `env_check_selected_cids.parquet` (案 E 選定 681 CID)
- `env_check_underfill.parquet` (不足 bin 記録)

### 観察 1 (Step C/D)
- `observation_1_familiarity_trajectory_smoke.parquet` (smoke 528 rows)
- `observation_1_smoke_per_seed_bin_counts.parquet`
- `observation_1_familiarity_trajectory.parquet` (main 10,896 rows)
- `observation_1_summary.parquet` (681 start_cid 集計)
- `observation_1_aggregate.parquet` (final_state × fam_bin 集計)

### 観察 2 (Step E)
- `observation_2_circulation.parquet` (681 start_cid 循環構造)
- `observation_2_attractors.parquet` (847 unique CID、63 個高 attractor)
- `observation_2_aggregate.parquet` (final_state × fam_bin 集計)

### 観察 3 (Step F)
- `observation_3_high_low_events.parquet` (3,300 event 分類)
- `observation_3_input_atom_bias.parquet` (event_class × atom 偏り)
- `observation_3_word_distribution.parquet` (高/低 event 別 word top 30)

### 観察 4 (Step G/H)
- `observation_4_self_dialogue_smoke.parquet` (smoke 1,353 rows)
- `observation_4_smoke_compare_top1.parquet`
- `observation_4_self_dialogue.parquet` (main 27,921 rows)
- `observation_4_summary.parquet` (681 start_cid 集計)
- `observation_4_aggregate.parquet`
- `observation_4_vs_top1_compare.parquet`

### bit-identity (Step I)
- `v1106b_step_i_bit_identity_report.json` (全 PASS)

### スクリプト
- `v1106b_step_b_env_check.py` 〜 `v1106b_step_i_bit_identity.py` (8 ファイル)

### 報告書
- `v1106b_phase_design_draft.md` (Code A 設計書)
- `v1106b_step_a_recognition.md` (認識確認)
- `v1106b_step_b_env_check_report.md` (環境準備報告)
- `v1106b_step_c_smoke_report.md` (smoke 報告)
- `v1106b_step_f5_observation_4_implementation_plan.md` (観察 4 実装方針)
- `v1106b_step_j_observation_final.md` (本文書)

---

## 11. 一文サマリ

v1106b Step J 観察事実最終報告として、主題「Step M-P 正式化、CID 空間吸引・循環・局所共鳴の観察」(問いの形 A、Taka 採用) に対し Step A-I 全完了 (Step B 案 E 採用 681 CID 選定 + Step C smoke + Step D main 観察 1 + Step E 観察 2 + Step F 観察 3 + Step F.5 観察 4 実装方針 + Step G smoke + Step H main 観察 4 + Step I bit-identity 3 層全 PASS、合計実装 2 分)、構造事実 5 件 (familiarity ~10 収束力場 + CID 空間 attractor 構造各 seed 2-3 個 + 局所共鳴の input_atom 二極化 PER vs EXS + sampling 依存性 + stuck/oscillation 全件検出) を観察、留保候補 #L49-#L52 (採番は Web Claude Phase Result で確定)、Taka 構想 (cid 時系列増殖 + 主体性複数 + 応答時間が系を変化) との接続候補を v1107 主題判断材料として議題化、Web Claude Phase Result 着手判断材料として提供、v3 重みづけミス防止 4 件 (進化途上 / 重みづけ説明 / 主観的所感別レイヤー / 構造的解釈確定回避) を継承。

---

**Step J 観察事実最終報告 end. Web Claude Phase Result 着手の判断材料を提供。**
