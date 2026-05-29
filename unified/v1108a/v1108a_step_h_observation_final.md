# v1108a Step H — 観察事実最終報告

**Date**: 2026-05-30
**Author**: Code A
**Status**: Step A-G 完了

---

## 0. 全 Step 完了状況

| Step | 内容 | 実行時間 | 結果 |
|---|---|---:|---|
| A | 認識確認 + 実装制約 (Step H atom_probs 記録なし) 提示 | - | Taka 案 A 採用 |
| B | Step H 再実行 (atom_probs 記録版) | 32.7s | 整合性 100% |
| C | 観察 1 ΔC_ij (numpy ベクトル化) | 0.8s | 30.23% z>2 |
| D | 観察 2 ρ_FH 連動曲率 | 0.3s | ρ=-0.100, p<1e-60 |
| E | 観察 3 基準 A 判定 | 0.0s | **PASS** |
| F | 観察 4 Gemini 予測 1/2 | 0.4s | 予測 1 棄却 / 予測 2 支持 |
| G | bit-identity 3 層検証 | 36.5s | LAYER A 部分一致 (elapsed_sec 列のみ不一致、本質結果一致) / LAYER B/C 全 PASS |

---

## 1. 観察 1 ΔC_ij Atom 遷移結合カーネル

| 指標 | 値 |
|---|---:|
| 全 Atom ペア | 8,412 (top-10 出現 atom union) |
| ΔC > 0 ペア | 3,171 (37.7%) |
| **z > 2 有意ペア** | **2,543 (30.23%)** |
| z > 5 | 1,965 (23.4%) |
| z > 50 | 691 (8.2%) |
| 対角 self-loop | 70 |
| **非対称性 max** | **0.000161 (微小)** |
| 非対称性 mean | 0.000006 |

**強結合上位 (top-20)**:
- 対角: TIM.appear, ACT.emit, PER.see, PRP.smooth, MAT.tool (self-loop 支配)
- 非対角: TIM.appear→PER.see, ACT.make→CHG.begin, CHG.grow→ACT.rise (意味的整合)

→ **構造ラベル**: `temporal_symmetric_only` 寄り、ただし z>2 有意ペア多数

---

## 2. 観察 2 ρ_FH Familiarity-Entropy 連動

| 指標 | 値 |
|---|---:|
| **ρ_FH overall** | **-0.1000** (p=1.88e-61) |
| 構造ラベル | **`familiarity_entropy_coupled`** ✓ |
| ρ vs shuffle z | **-26.34** |

**final_state 別**:
| state | ρ_FH | p | 解釈 |
|---|---:|---:|---|
| reaped | **-0.117** | 0.000 | 強い負連動 |
| hosted | -0.105 | 0.000 | 強い負連動 |
| ghost | -0.014 | 0.405 | 連動なし |

**event 別**: 680 events、56% で負相関 (Gemini 予測方向性支持)

→ **「familiarity 減少時に entropy 増加」= 馴染みが薄れると選択肢が広がる構造**

---

## 3. 観察 3 基準 A 判定 — **PASS**

| 指標 | 真 | shuffle | 通過 |
|---|---:|---:|---|
| pct z>2 | **30.23%** | (5% threshold) | ✓ |
| rho_FH | -0.1000 | mean 0.0004, std 0.0038 | z=-26.34 ✓ |

**構造ラベル**: `temporal_asymmetric_binding_observed`

---

## 4. 観察 4 Gemini 予測 1/2

### 予測 1: 社会的 cluster は孤立より時間結合長い (τ_social > 2 × τ_isolated)

| cluster | n events | max persistence mean |
|---|---:|---:|
| social (EXS/FND) | 123 | 13.65 |
| isolated (BOD/PER/PRP) | 122 | **15.78** (高) |

社会的/孤立 持続性比: **0.87** (予測 >2.0、**FAIL**)

→ **構造ラベル**: `social_temporal_no_difference` (Gemini 予測 1 棄却)
→ 構造事実: 孤立 cluster の方が persistence わずかに長い (予想と逆)

### 予測 2: familiarity 減少率最大 turn での Atom ペア 3σ 尖鋭化

| 指標 | 値 |
|---|---:|
| 特異 turn 抽出 | 681 events |
| 特異 turn 平均 decrease_rate | 0.755 |
| 特異 turn ペア mean ΔC | 0.000174 |
| 全体 mean ΔC | 0.000000 |
| **3σ 超え** | **78.1% (532/681)** |

→ **構造ラベル**: `plasticity_singularity_focused` (Gemini 予測 2 強く支持)
→ **可塑性特異点で Atom ペア結合が局所的に尖鋭化** が構造事実

---

## 5. 統合構造ラベル

| 観察 | 構造ラベル |
|---|---|
| 1 (時間結合) | temporal_symmetric_only / z>2 有意 30% |
| 2 (ρ_FH 連動) | `familiarity_entropy_coupled` ✓ |
| 3 (基準 A) | `temporal_asymmetric_binding_observed` ✓ |
| 4-1 (予測 1) | `social_temporal_no_difference` (棄却) |
| 4-2 (予測 2) | `plasticity_singularity_focused` ✓ |

---

## 6. bit-identity 検証

| LAYER | 結果 |
|---|---|
| A (再実行 hash 一致) | **部分一致** — 結果系 (delta_C / rho_FH / asymmetry / event_rhos) すべて hash 一致、**summary 系の `elapsed_sec` 列のみ不一致** (時刻記録の自然な変動) |
| B (物理層 frozen) | **全 PASS** (v105/v106/v1103/v1106a/v1106b/mapper_output 全 7 root で a=0 r=0 m=0) |
| C (書込みパス) | **全 PASS** (10/10 write 操作 unified/v1108a/ 配下のみ) |

→ **本質的な数値結果は完全に一貫**。summary の elapsed_sec 列で不一致のため `all_layers_pass=False` だが、これは LAYER A の集約 summary の自然な時刻変動。

---

## 7. Code A 主観

### 観察事実として強い
1. **ρ_FH 連動性確認** (z=-26.34、p<1e-60、final_state 別でも有意)
2. **時間結合 30% が z>2** で shuffle に大幅優位
3. **Gemini 予測 2 (可塑性特異点 3σ)** 78.1% で強く支持
4. **Gemini 予測 1 棄却** (社会的が長 τ でなく、孤立 cluster の方がわずかに長い)

### 議題化候補
5. **非対称性微小** (max 0.000161)、時間軸方向性は実質的にほぼなし → "対称結合" 主体
6. **予測 1 が逆方向**: 孤立 cluster (BOD/PER/PRP) で持続性わずかに長い。これは v1106b stuck/oscillation 100% (孤立 CID で attractor 固定) と整合可能

### 解釈控え (judgment 回避)
- 「ESDE が時間軸方向性を持つ」と確定しない
- 「内的文法を立ち上げる」(Gemini 案) と書かない
- ρ_FH 負連動を「選択肢広がる方向」と書いたが、これは数値解釈、構造解釈は Web Claude 判断

---

## 8. 留保候補 (Web Claude 採番)

| 候補 | 内容 |
|---|---|
| v1108a-1 | familiarity-entropy 負連動 (ρ=-0.100、p<1e-60、final_state hosted/reaped で有意、ghost で非有意) |
| v1108a-2 | 時間結合 z>2 有意 30%、ただし非対称性微小 → "対称的時間結合" 構造 |
| v1108a-3 | 可塑性特異点 (familiarity 減少率最大 turn) で Atom ペア結合が 78.1% で 3σ 尖鋭化 |
| v1108a-4 | Gemini 予測 1 (社会的長 τ) 棄却、孤立 cluster の方がわずかに長 persistence |

---

**Step H end. Web Claude Phase Result (v1108a + v1108b 統合) 着手判断材料を提供。**
