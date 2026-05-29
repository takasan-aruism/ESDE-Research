# v1109 Step A — Code A 認識確認

**Date**: 2026-05-30
**Author**: Code A
**Status**: Step A 認識確認、実装可能、Web Claude / Taka 確認後 Step B 進行
**親**: v1109 設計書草案 (Web Claude、2026-05-30)

---

## 0. 受領内容認識

### 0.1 主題
v1109 — 経験重み層を追加したとき順序非対称性が立ち上がるかの試行 (問いの形 B、収束フェーズ)

### 0.2 設計核心
- 4 層 + 試行層 (物理層/存在層 frozen、認知層 = W 記録、試行層 = W 適用)
- 4 条件比較 (baseline / observed / shuffled / frequency)
- holdout 検証 (turn / seed / category)
- Gemini 3 大ブレーキ (総和保存 / エントロピー連動 Δw / 物理層接続可能性)
- 構造ラベル 6 種、`grammar_precursor` は非対称性 + heldout lift + 多様性維持の同時成立時のみ

### 0.3 予防規律
- 自己成就回避 (GPT 監査核心)
- 神の手回避 (Gemini 3 大ブレーキ)
- 物理層 frozen 1 byte も侵さない
- 「文法創発」と書かない、「順序非対称性」「文法前駆構造」まで

### 0.4 Code A への一言
> 「わからんことは言えよな」

→ 本 §1 で実装条件を提示。

---

## 1. 実装条件事前チェック (6 項目)

### 1.1 データ存在 (実環境照合)

| データ | 状態 |
|---|---|
| v1108a self_dialogue (atom_probs 版) | ✓ 27,921 rows、681 events、24 seeds |
| v1108a observation_1 delta_C (#L57 before baseline) | ✓ 非対称性 max 0.000397 |
| v1108a observation_2 rho_FH (#L56 familiarity 連動) | ✓ |
| v1108a observation_4 (#L58 可塑性特異点) | ✓ |
| v1108b observation_5 (#L59 参照領域切替) | ✓ |

すべて frozen。書込みは unified/v1109/ 配下のみ。

### 1.2 計算可能性

| 量 | 規模 |
|---|---|
| atom_top1..10 unique atoms | **137** (full 325 のうち実出現) |
| W 行列サイズ | **137 × 137 = 18,769 cells** |
| 4 条件 × W = 75,076 cells | 軽量 |
| holdout (turn/seed/category) × 4 条件 | 数万 cells × 数回 |
| event 数 | 681 |
| turn pair 数 | ~27,240 |

→ **numpy ベクトル化で数秒〜数分**。v1108a Step C と同型 (vectorized add.at)。

### 1.3 Gemini 3 大ブレーキ実装可能性

**ブレーキ 1: 重み総和保存 (∑W = const)**
```python
def normalize_W(W, total_sum):
    cur_sum = W.sum()
    if cur_sum > 0:
        return W * (total_sum / cur_sum)
    return W
```
→ 毎 turn または毎 event 終了時に正規化。Code A 提案: **毎 event 終了時** (turn ごとは過剰計算)

**ブレーキ 2: エントロピー連動 Δw**
```python
H_max = np.log(K)  # K=top-K
H_t = -Σ P_t log P_t
Δw_t = base_δ × (1 - H_t / H_max)  # 構造尖り (H→0) で Δw→0
```
→ H_t が H_max に近い (均等分布) と Δw=0 (情報なし)、H_t=0 (尖り) で Δw→0 (摩擦)。
→ 中間で Δw 最大。これが Gemini の「漸近自己ブレーキ」

ただし Gemini 「H→0 で Δw→0」が直接実現するなら式は `Δw = base × H_t × (1 - H_t/H_max)` の方が自然 (Code A 提案、Step A で確認要)

**ブレーキ 3: 物理層接続可能性**
```python
# cid_atom_sim_matrix で input_atom と各 atom の sim が極めて低い場合
# 重み更新を抑制 (Δw を sim で乗算)
Δw_ij ← Δw_ij × sim_to_atom_j  # 接続可能性
```

→ 全 3 ブレーキ実装可能。Code A 案は Step A で Web Claude 確認要。

### 1.4 holdout 分離方法

Code A 提案: **3 種類すべて実施**:

| 方式 | 実装 |
|---|---|
| turn holdout | 各 event の前半 20 turn で W 蓄積、後半 20 turn で適用・効果測定 |
| seed holdout | 12 seeds (0-11) で W 蓄積、12 seeds (12-23) で適用 |
| category holdout | cluster_0 cat で蓄積 → cluster_1 cat で適用 (逆方向も) |

→ どれが「自己成就回避」の最強かは結果で判断。Code A 提案は全 3 種 OR 統合。

### 1.5 heldout_lift 計算方法

Code A 提案: **次 Atom 予測 hit rate**

```python
# baseline (重みなし) の予測:
#   各 turn t で次 turn t+1 の top1 Atom を P_t から予測 (top1 が正解と一致か)
# observed_weight 適用後の予測:
#   P'_t+1 = P_t+1 × (1 + α × W_prev)、その top1 が正解と一致か

baseline_hit_rate = sum(predicted == actual) / total
observed_hit_rate = ...
heldout_lift = observed_hit_rate - baseline_hit_rate
```

これが holdout データで > 0 なら **遷移順序固有の効果** が generalize する証拠。
shuffled/frequency baseline の heldout_lift とも比較。

### 1.6 不足部分 (Web Claude / Taka 確認要)

| 項目 | Code A 提案 | 確認 |
|---|---|---|
| Q1 影響係数 α | α=0.5 (中間値、自己組織化でない固定値) でスタート、後で sensitivity 分析 | Web Claude 採用判断 |
| Q2 エントロピー連動 Δw 式 | `Δw = base × H_t × (1 - H_t/H_max)` (Code A 案) | Web Claude / Gemini 確認 |
| Q3 holdout 統合方法 | 3 種類個別測定 + 全成立で `generalizes` | Web Claude 確認 |
| Q4 mechanical_effect vs sequence_specific threshold | observed_lift > shuffled_lift × 2 で sequence_specific | Web Claude 確認 |
| Q5 grammar_precursor 判定 | 非対称性 > 10×baseline AND heldout_lift > 0 AND entropy 維持 (95%+ of baseline) | Web Claude 確認 |
| Q6 物理層接続可能性 ブレーキ 3 | cid_atom_sim_matrix の sim で Δw × sim_to_atom_j | Web Claude / Gemini 確認 |

---

## 2. データ取り違え防止 §0.7

全 frozen (v1106b / v1106a / v1108a / v1108b / v106 / v105)、書込み `unified/v1109/outputs/main/` 配下のみ。

---

## 3. Step 分解 (Code A 想定)

| Step | 内容 |
|---|---|
| A | 本文書、認識確認 + 6 確認要請 |
| B | 環境準備 (v1108a データ + atom universe 確定) |
| C | 重み記録機構 + 4 条件 (baseline/observed/shuffled/frequency) |
| D | 重み適用機構 + Gemini 3 大ブレーキ |
| E | holdout 検証 (turn/seed/category 3 種) |
| F | 8 測定指標集計 (transition_asymmetry / heldout_lift 等) |
| G | Δw 条件比較 + #L58 全 vs 特異点 + #L59 global vs category |
| H | bit-identity 3 層 (物理層 frozen 確認) |
| I | 観察事実最終報告 + 構造ラベル 6 種判定 |

---

## 4. 計算量事前確認は不要 (Taka 判断継承)

v1108 が約 2 分実績、v1109 は 4 条件 × 3 holdout で数倍 → 数分〜10分以内想定。

---

## 5. 規律遵守確認

| 規律 | 遵守 |
|---|---|
| 絶対格言 15 件 | ✓ |
| 6 段階目ミス予防 (実験設計を疑う) | ✓ |
| 5 段階目ミス予防 (他 AI 提案実環境照合) | ✓ Gemini 3 大ブレーキの式は Code A 案、Web Claude 確認要 |
| 自己成就回避 | ✓ 4 条件 + holdout + heldout_lift |
| 神の手回避 | ✓ 固定閾値 if 文不使用、確率空間と物理層から自然に限界 |
| 物理層 frozen | ✓ 書込み unified/v1109/ 配下のみ |
| 観察 vs 介入の明示 | ✓ post-process intervention と明示 |
| 文法創発の過大評価回避 | ✓ 「順序非対称性」「文法前駆」までで「文法創発」と書かない |
| 重み記録と適用の分離 | ✓ 認知層 (記録) vs 試行層 (適用) |
| ボツも構造事実 | ✓ mechanical_effect / overfit / unstable_loop も構造事実 |
| わからんことは言えよな | ✓ Q1-Q6 で 6 件提示 |

---

## 6. Web Claude / Taka への確認

| 項目 | Code A 提案 |
|---|---|
| Q1 α | α=0.5 固定 (sensitivity 後で) |
| Q2 エントロピー Δw 式 | `Δw = base × H_t × (1 - H_t/H_max)` |
| Q3 holdout | 3 種類 (turn/seed/category) 全実施、統合判定 |
| Q4 mechanical vs sequence_specific threshold | observed_lift > shuffled_lift × 2 |
| Q5 grammar_precursor | 3 条件同時成立 |
| Q6 ブレーキ 3 接続可能性 | Δw × sim_to_atom_j で抑制 |

---

**Step A end. Web Claude / Taka 確認後 Step B 進行。**
