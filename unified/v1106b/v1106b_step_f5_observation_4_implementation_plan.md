# v1106b Step F.5 — 観察 4 実装方針報告

**Date**: 2026-05-28
**Author**: Code A
**Status**: Web Claude 追加提案 1 反映、Web Claude 確認待ち
**親**: Step C-F 完了 (Code A 自走) + Web Claude 確認文書 §3.1 (Step F.5 追加)

---

## 0. Step C-F 結果サマリ (観察 4 設計の前提)

### 0.1 観察 1/2/3 で確定した構造特性

| 観察 | 主要発見 |
|---|---|
| 観察 1 (familiarity 軌跡) | rollback 69.3% (681 CID)、stuck/oscillation 全件検出、unique CID per start mean 2.5、ESDE 自己対話は familiarity 中央値 ~20 に収束する力場 |
| 観察 2 (循環構造) | first revisit turn median 2、各 seed に 2-3 個の強 attractor (per_seed start の 90%+ が同 attractor に集約) |
| 観察 3 (局所共鳴) | 高 cos_sim event = 知覚系 PER × 孤立 reaped CID、低 cos_sim event = 存在論系 EXS × 社会的 hosted CID で明確分離 |

### 0.2 観察 4 で見たいこと

**top-1 (観察 1/2) でこれだけ強い attractor 構造 + familiarity 引力場が観察された**:

- top-3 sampling (観察 4) で **多様性が出るか** = 確率的遷移で attractor から脱出可能か
- それとも sampling でも結局 attractor に収束するか
- ESDE 自己対話の **純粋構造の安定性** (Code A 介在なし、ESDE 自身の発話を投げ続ける)

→ 観察 1/2 が「決定論的経路」、観察 4 が「確率的経路」での挙動を対比

---

## 1. 観察 4 実装方針 (Code A 提案、Web Claude 確認待ち)

### 1.1 接続式 (top-3 sampling)

```python
def self_dialogue_sampling(seed, start_cid, n_turn, atom_to_centroid,
                            atom_to_word_sims, word_to_atom_vec, sim_df,
                            props_df, cid_vecs, rng):
    """top-3 sampling 自己対話"""
    history = []
    current_cid = start_cid
    cid_track = []
    stuck_at = None
    oscillation_at = None
    same_cid_run = 0
    prev_cid = None

    for t in range(n_turn + 1):
        if current_cid not in cid_vecs:
            break
        cid_vec = cid_vecs[current_cid]
        # ESDE 発話 (top-K word)
        words_top, atoms_top = cid_to_word_top(cid_vec, atom_to_centroid,
                                                  atom_to_word_sims,
                                                  ATOM_TOPK, WORD_TOPK_FOR_LOOP)
        # 履歴記録
        history.append({...})  # turn, cid, fam, atom_top, word_top, etc.

        if t >= n_turn or not words_top:
            break

        # 逆引き → CID 候補 top-5
        top_words = [w for w, _ in words_top]
        atom_probs2 = words_to_atoms(top_words, word_to_atom_vec)
        cid_candidates = atom_to_cid_topK(atom_probs2, sim_df, k=5)  # top-5 候補

        # top-3 から確率重み sampling
        top3 = cid_candidates[:3]
        scores = np.array([s for _, _, s in top3])
        probs = scores / scores.sum() if scores.sum() > 0 else None
        idx = rng.choice(len(top3), p=probs)
        next_seed, next_cid, _ = top3[idx]
        current_cid = next_cid
        # stuck/oscillation 検出 (観察 1/2 と同様)

    return history
```

### 1.2 観察 1/2/3 との設計差分

| 項目 | 観察 1/2 (Step D) | 観察 4 (Step H 予定) |
|---|---|---|
| next CID 選択 | top-1 (決定論) | top-3 sampling (確率) |
| N turn | 15 | **40** (収束パターン捕捉のため長め) |
| 停止条件 | 同じ (中断せず N turn 完走 + ラベル記録) | 同じ |
| Code A 介在 | なし (ESDE 自身の発話を ESDE に投げる) | 同じ |
| 再現性 | 完全再現 (np.random.seed=42 固定) | 部分再現 (sampling rng シード固定で再現可) |
| 対象 CID | 681 (案 E 選定) | 同じ (681、観察 1/2 と同 CID) |

### 1.3 Code A 介在なし保証

実装上の保証 (擬似コードに沿った確認):

| 介在要素 | 状態 |
|---|---|
| 人間 input (response 引数) | **なし** (Step P の対話スクリプトと違い、word 入力なし) |
| 動的判定 (turn 中の意味的選択) | **なし** (確率分布から机械的選択) |
| 中断ロジック | **N turn 到達のみ** (stuck/oscillation はラベル記録、強制中断なし) |
| 後処理での介在 | **なし** (生データ保存、解釈は集計時のみ) |

→ **全部スクリプト内完結**。Code A は実行コードを起動するだけ、ESDE 自身の確率分布が遷移を決める。

### 1.4 想定実行時間

| Step | 内容 | 想定時間 |
|---|---|---|
| G smoke | 1 seed (33 CID) × 40 turn = 1,320 turn | **2-3 分** (Step D 比例で計算: 13.6s × 40/15 × 1/24 ≈ 1.5s/seed) |
| H main | 24 seeds × 681 CID × 40 turn = 27,240 turn | **5-10 分** (Step D 13.6s × 40/15 ≈ 36s) |

→ Step C smoke が 1.3 秒、Step D main が 13.6 秒だったので、観察 4 (40 turn) も比例して 4 倍程度。Code A 当初見積 (15-30 分) より速い可能性。

---

## 2. 観察 4 で見たい構造観察

### 2.1 attractor 構造の sampling 依存性

| 観察視点 | top-1 (Step D/E) | top-3 sampling (Step H 予測) |
|---|---|---|
| unique CID per start (mean) | **2.53** | ↑ 増加すれば sampling で多様性 |
| max revisit count | 14.47 (1 CID を 14-15 回) | ↓ 減少すれば反復が緩む |
| first revisit turn | median 2 | ↑ 遅延すれば離脱経路 |
| 強 attractor 集約率 | 90%+ | ↓ 弱まれば attractor 構造の確率依存性 |

### 2.2 familiarity 軌跡の sampling 依存性

| 観察視点 | top-1 (Step D) | top-3 sampling 予測 |
|---|---|---|
| rollback 率 | 69.3% | sampling で増えるか減るか |
| min_fam mean | 20.0 | 中央値収束力場が緩むか |
| 高 fam 出発 (≥50) の到達範囲 | min ~20 程度 | sampling で別の範囲に行けるか |

### 2.3 sampling 固有の現象 (新規想定)

- top-3 sampling で **alternate attractor** (top-1 では行かない CID) に到達するか
- 確率的拡散後に **元の attractor に収束** するか
- 30-40 turn の長期で **複数 attractor 間を行き来する** か (top-1 では循環)

---

## 3. Web Claude / Taka 確認事項

### 3.1 Web Claude 確認 (実装方針)

| 項目 | Code A 提案 | Web Claude 確認待ち |
|---|---|---|
| top-3 sampling 採用 | OK か (top-5 sampling も選択肢、Code A は top-3 推奨) |
| N=40 turn | OK か (収束捕捉のため、計算量増分許容範囲) |
| cid_candidates top-5 取得 → 上位 3 から sampling | OK か (top-5 から 5 sampling より絞った方が確率高 CID に重みつく) |
| 同 seed 内 sampling | OK か (cross-seed は不可、cid_atom_sim_matrix は seed 別のため) |
| 想定実行時間 | 妥当か (G smoke 2-3 分、H main 5-10 分) |

### 3.2 Taka 確認 (任意)

| 項目 | Code A 提案 |
|---|---|
| Step G smoke 後 pause か | Code A 提案: pause (memory rule)、Web Claude/Taka 確認 |
| Step H main 後の Code A 自走 | Step D 同様、自走で Step I (bit-identity) へ |
| sampling rng シード | 固定 (np.random.seed=42、Step D と一致) |

---

## 4. リスクと Code A 対処

| リスク | 対処 |
|---|---|
| sampling でも top-1 と同じ attractor に収束 | 観察事実として記録、観察 4 の構造特性 |
| sampling で実行時間が大幅増 | 想定 (5-10 分) から逸脱したら Code A 報告 |
| 不正な遷移 (CID 数 0、norm 0 等) | Step C/D で既に handle、同様の防御 |
| Code A 介在の誤混入 | 擬似コードで確認、人間入力 / 動的判定なし |

---

## 5. 次のステップ

Web Claude 確認後 (本文書 §3.1) に:
1. Step G smoke (1 seed × 33 CID × 40 turn、2-3 分) → pause + 報告
2. Web Claude/Taka 確認後 → Step H main (24 seeds × 681 CID × 40 turn、5-10 分) → Code A 自走
3. Step I bit-identity 検証 → Step J 観察事実最終報告 (Web Claude Phase Result 着手)

---

**Step F.5 報告 end. Web Claude 確認待ち。Code A は確認後に Step G smoke 進行。**
