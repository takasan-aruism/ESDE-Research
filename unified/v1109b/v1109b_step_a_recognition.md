# v1109b Step A — Code A 認識確認

**Date**: 2026-05-30
**Author**: Code A
**Status**: Step A 認識確認、実装可能、Web Claude / Taka 確認後 Step B 進行
**親**: v1109b 設計書草案 (Web Claude、2026-05-30)

---

## 0. 受領内容認識

### 0.1 主題
v1109b — Grammar Exploration 検証: 順序構造の兆候は本物か (検証型 A、新機構追加なし、post-process のみ)

### 0.2 設計核心
- 検証 1: shuffle baseline 4 種 (sequence order / within-turn / atom label / counterfactual)
- 検証 2: self-fulfilling 5 条件 (top1 / top2 / top3 / probability / holdout)
- 検証 3: loop 区別 5 条件 (all / non-self / CID changed / loop-excluded / first-visit)
- 検証 4: 表現規律 (文法/CSG 禁止)
- 出口 4 分岐 (A 本物 / B loop / C top1 / D 区別不能)

### 0.3 予防規律 (Code A 自己点検)
- 7 段階目ミス予防 (self-fulfilling baseline 検査) — **重要、v1109 で踏んだミス**
- loop 由来構造の検査
- shuffle baseline 義務化
- 強い語の禁止 (文法/CSG/創発)
- 物理層 frozen 厳密

### 0.4 Code A への一言
> 「わからんことは言えよな」

---

## 1. 実装条件事前チェック (6 項目)

### 1.1 Q1: top2-10 記録 (sampling 検証に必須)

**実環境確認**:
```
v1108a self_dialogue_with_atom_probs.parquet:
  atom_top1 〜 atom_top10 (10 列): 各 turn の top-10 atom
  prob_top1 〜 prob_top10 (10 列): 対応する確率
  rows: 27,921
```

→ **top2-10 完備、sampling 検証 (top2/top3/probability) 実装可**

### 1.2 Q2: サンプル数と shuffle 統計安定性

Grammar Exploration #L65 の各兆候のサンプル数:

| 兆候 | n | shuffle 安定性 |
|---|---:|---|
| start/end 分離 (10 vs 3) | 327 events | 統計的に意味のある shuffle 可 |
| PER.see → TIM.appear 81% | 21 events | **小さい**、shuffle で揺らぎ大 |
| 順序 npmi 6 ペア | n_pairs 27,240 | 大きい、安定 |
| 役割切替 87% (CHG.grow 等) | 各 atom 数千 obs | 大きい、安定 |
| マルコフ超え連鎖 6 個 | 各 5-191 obs | 一部小さい |

→ **大きい兆候 (役割切替、npmi) は shuffle 信頼性高、小さい兆候 (PER.see→TIM.appear) は留保必要**

### 1.3 Q3: counterfactual shuffle (Gemini 案) 実装可能性

Gemini 案: 「各 turn の分布 $P_t$ は変えず、サンプリング順序だけランダム化」

Code A 実装案:
```python
# 通常 (現状): 各 turn の actual top1 を取って遷移列を作る
# counterfactual: 各 turn の P_t (atom_top1..10 + prob_top1..10) を維持し、
#   各 turn で確率に従ってランダムサンプリング → 新しい遷移列
for each event:
    for each turn t:
        # P_t は不変
        # 通常の actual = atom_top1 (top1 固定)
        # counterfactual = atom_top_k where k ~ Categorical(prob_top1..10)
        sampled_atom = np.random.choice(atoms_top, p=probs_top)
    # 新しい遷移列で順序構造指標を再計算
```

→ **実装可能** (numpy.random.choice + 既存集計関数の再適用)
→ これで「同じ分布、異なる遷移」を作れる、構造が分布由来か遷移由来かを切り分け

### 1.4 Q4: loop 区別実装

| 条件 | 実装 |
|---|---|
| all transitions | 現行 (Grammar Exploration と同じ) |
| non-self transitions | `atoms[t] != atoms[t+1]` フィルタ |
| CID changed turns | `cid[t] != cid[t+1]` フィルタ |
| loop-excluded sequence | stuck_at_turn より前の turn のみ |
| first-visit only | 各 event で初出 atom のみの遷移 |

→ **すべて実装可能**、軽量

### 1.5 Q5: self-fulfilling baseline 検査 (Code A 自己点検)

**v1109 で犯した過ち** (報告書 §4.1):
- baseline (W=0) で predicted top1 = orig top1 = actual top1 (定義上一致)
- → baseline hit_rate=1.0 が定義必然、本来比較したい量が測れていなかった

**v1109b での対策**:
- 各検証 (shuffle/sampling/loop) で baseline 定義を明示
- baseline と「比較する量」が独立になっているかを Step C-E 各々で確認
- 例: shuffle baseline と比較するのは shuffle 後の同指標 (同設計で独立)、self-fulfilling リスク低
- sampling baseline: top1 chain と top2/3 chain で「比較する量」 (順序構造指標) が共通基盤か確認

→ **設計書 §0.1 規律 1-3 を Step C-E で各検証実行前に逐次チェック**

### 1.6 Q6: 不足部分

特になし。実装可能性は全項目 OK。

---

## 2. データ取り違え防止 §0.7

| データ | 状態 |
|---|---|
| v1108a self_dialogue (atom_top1-10 + prob_top1-10) | frozen ✓ |
| Grammar Exploration 出力 (case_*/explore_*/*.parquet) | frozen ✓ |
| v1106b stuck_at_turn / oscillation_at_turn | self_dialogue 内に記録 ✓ |

書込みは `unified/v1109b/outputs/main/` 配下のみ。物理層 1 byte も侵さず。

---

## 3. Step 分解

| Step | 内容 |
|---|---|
| A | 本文書、認識確認 + 6 項目チェック |
| B | 環境準備 (#L65 兆候の数値再確認、shuffle 統計安定性確認) |
| C | 検証 1: shuffle baseline 4 種 |
| D | 検証 2: self-fulfilling 5 条件 (top1/top2/top3/probability/holdout) |
| E | 検証 3: loop 区別 5 条件 (all/non-self/CID changed/loop-excluded/first-visit) |
| F | 出口 4 分岐判定 (A/B/C/D) |
| G | bit-identity 3 層検証 |
| H | 観察事実最終報告 + 出口判定 + 次主題候補 |

---

## 4. 規律遵守

| 規律 | 遵守 |
|---|---|
| 絶対格言 15 件 | ✓ |
| 7 段階目ミス予防 (self-fulfilling baseline) | ✓ Q5 で逐次チェック |
| loop 由来構造の検査 | ✓ 検証 3 |
| shuffle baseline 義務化 | ✓ 検証 1 (4 種) |
| 強い語の禁止 (文法/CSG/創発) | ✓ 「順序構造の兆候」「sequence bias」に統一 |
| 実験設計を疑う (6 段階目) | ✓ 各検証で「結果が消える/残る」両方を構造事実扱い |
| 物理層 frozen | ✓ 検証のみ、新機構なし、v1109b/ 配下のみ書込み |
| わからんことは言えよな | ✓ Q1-Q6 で実装可能性を明示 |

---

## 5. Web Claude / Taka への確認 (簡素)

| 項目 | Code A 提案 |
|---|---|
| Q1-Q6 すべて | OK (実装可能、留保事項なし) |
| サンプル数留保 (Q2) | 大きい兆候は shuffle 信頼可、小さい兆候 (PER.see→TIM.appear 21 events) は留保明示で進む |
| counterfactual shuffle 実装 | Code A 案 (P_t 維持で確率サンプリング再生成) |
| Step B-H Code A 自走 | Taka 判断、希望ありなら従う |

---

**Step A end. Web Claude / Taka 確認後 Step B 進行。**
