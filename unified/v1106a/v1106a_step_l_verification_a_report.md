# v1106a Step L 検証 A — CID 48d × word 加重 48d centroid の直接 cos_sim

**Version**: v11.0.6a Step L
**Date**: 2026-05-27
**Role**: Code A (実装担当)
**Status**: 観察事実報告 — 判定回避

---

## 0. 検証目的

### 0.1 ユーザー指摘の核心

> 「単語群は明らかに何かしら Atom と接続があるのに rc 無相関は引っかかる。
>  実装が勝手に繋いでいるのか、本当に何かしらあるのかが重要。
>  ESDE Language 系と Genesis 系が別なのは当然、重要なのは別に見えるはずの
>  ものが何で繋がっているか」

### 0.2 Code A の前提見直し

Step K で出した rc_mean は「s7 atom 順位 vs 各 atom の top1 cos_sim」を比較しており、
**atom 間距離 vs atom 内 word 質** という別量の比較で、CID と word の潜在的繋がりを
測る指標になっていなかった。

検証 A は **CID 48d 状態と word 分布が指す 48d 中心の直接整合性** を測定する。

---

## 1. 計算仕様

### 1.1 同一 48 軸意味空間での比較

```
CID 48d vec (v106 cid_structure_profile_seed{N}.csv)
  = build_cid_vector(lifespan, n_core, familiarity, ...) → 48 軸
    Genesis 系シミュレーションの物理量から 48 軸へ射影

event word 分布 (案 Y) → weighted 48d centroid
  = Σ_w prob(w) × raw_scores(w) / Σ_w prob(w)
    mapper_output の word raw_scores を案 Y 確率で加重平均

cos_sim(cid_48d, word_weighted_48d)
  = 両者が 48 軸意味空間で「同じ方向」を向いているか
```

### 1.2 ベースライン (実装由来か潜在的繋がりかの判定基準)

- **真**: event の実 CID と word centroid の cos_sim
- **shuffled within-seed**: 同 seed 内のランダム別 CID と word centroid の cos_sim (10 回平均)
- **shuffled cross-seed**: 別 seed のランダム CID と word centroid の cos_sim (5 回平均)
- **paired diff**: 同 event での真 - shuffle (event レベル一対比較)

### 1.3 入出力

入力 (read-only):
- `unified/v1105a/outputs/main/trial_step2_associations.parquet` (event ↔ CID マッピング)
- `unified/v1106a/outputs/main/observation_Y_word_distributions.parquet` (案 Y word 分布)
- `developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv` (CID 48d, 24 seeds)
- `language/lexicon/data/mapper_output/*_a1.jsonl` (word raw_scores 48d)
- `developmental/v106/outputs/main/axes_metadata.json` (48 軸順序)

出力:
- `unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet` (3,300 events)
- `unified/v1106a/outputs/main/verification_a_summary.parquet`

### 1.4 計算量

- events: 3,300 (s7 PC のみ)
- word 加重 centroid 計算: per event で ~350 word × 48 axes
- shuffle baseline: 10 + 5 = 15 回 / event
- 総実行時間: **42.5 秒**

---

## 2. 結果

### 2.1 真 cos_sim 分布

| 統計量 | 値 |
|---|---|
| n | 3,300 |
| mean | **0.5634** |
| median | 0.5756 |
| std | 0.0781 |
| min | 0.2393 |
| max | 0.7282 |
| >=0.9 割合 | 0.00% |
| >=0.8 割合 | 0.00% |
| >=0.5 割合 | 83.09% |

### 2.2 Shuffled baseline

| baseline | mean | std |
|---|---|---|
| within-seed (同 seed 別 CID) | 0.5137 | 0.0495 |
| cross-seed (別 seed の CID) | 0.5133 | 0.0575 |

### 2.3 真 vs shuffled 比較

| 指標 | 値 |
|---|---|
| 真 - within shuffle diff | **+0.0497 (1.00 σ)** |
| 真 - cross shuffle diff | +0.0502 (0.87 σ) |
| event-paired diff (真 - within) mean | +0.0497 |
| event-paired diff std | 0.0684 |
| **event-paired diff > 0 rate** | **83.15%** (偶然なら 50%) |

---

## 3. 構造事実の解釈

### 3.1 「潜在的繋がりはあるか」への答え

**微弱だが系統的に存在する** が現時点の構造事実:

- shuffle ベースライン 0.51 から真 0.56 へ +0.05 上回る
- event の 83.15% で真 cos_sim > shuffle cos_sim (偶然なら 50%)
- これは「実装が勝手に繋いでいるだけ」では説明できない一方向の偏り
- ただし σ 1.0 は統計的決定値としては弱い

### 3.2 cos_sim 絶対値の解釈における留意

- shuffled mean 0.51 は **cos_sim のゼロ点ではない**
- 48d 共通方向 bias (CID も word centroid も全体的に正方向の値を持つ) の影響
- 「真の cos_sim 0.56」は absolute では中程度に見えるが、baseline 補正後の **正味信号は +0.05** で弱い

### 3.3 ESDE 研究文脈での意味

- Genesis 系 (CID 物理量 → 48d 射影) と Language 系 (LLM 判定 → 48d 集約) は **異なる入力ソース**
- 両者が +0.05 (83% 同方向) で整合 → ランダム world から立ち上がった構造が Language の意味座標と**部分的に**対応
- 「全く別に見えるものが何かしらで繋がっている」の証拠は微弱だが存在

### 3.4 「実装由来」と「潜在的繋がり」の区別

| 観察 | 解釈 |
|---|---|
| shuffled cos_sim mean ≈ 0.51 (高い) | 48 軸意味空間の構造バイアス (実装由来) |
| 真 - shuffled = +0.05 | 構造バイアスを超えた正味信号 (潜在的繋がりの候補) |
| event-paired 83% 正方向 | 系統的な偏り、無作為では説明不可 |
| 真 cos_sim 絶対値 0.56 | 構造バイアス + 微弱な信号の合算、絶対値だけで判断不可 |

---

## 4. 残留疑問 / 次の検証候補

### 4.1 #L46 (本検証で明らかになった構造)

> **#L46**: ESDE Genesis 系 CID 48d 状態と Language 系 word 加重 48d centroid は、
> 48 軸意味空間で +0.05 (paired 83% 一方向) の正味整合を示す。これは構造バイアス
> (shuffled baseline 0.51) を超えた弱信号で、潜在的繋がりの候補だが σ 1.0 で
> 統計的決定にはさらなる検証が必要。

### 4.2 検証 B (より厳しい shuffle)

- word_centroid 自体もシャッフル → 完全独立 baseline
- 真 cos_sim と完全独立 cos_sim の差で純粋信号を測定

### 4.3 検証 C (48 軸別分解)

- どの軸 (temporal/scale/ontological/etc.) で整合が強いか
- 意味的に自然な軸で整合が集中するなら強い証拠
- 全軸均等にぼやけていれば構造バイアスの分散効果

### 4.4 event level 詳細分析

- 高 cos_sim event (>0.7) の input_atom 特性
- 低 cos_sim event (<0.4) の input_atom 特性
- どんな atom が CID と整合しやすいか

### 4.5 逆方向検証 (Language 本来の流れ)

- Language 系は word → atom → 分子 の流れで開発
- word 入力から atom 確率を逆引きして s7 atom 確率と一致するか
- 一致するなら CID → atom ↔ word → atom の閉ループ整合

---

## 5. Web Claude への報告ポイント

### 5.1 Code A の発見
1. 検証 A: CID 48d と word 加重 48d centroid に **microsoft 弱信号** (+0.05、83% paired)
2. 完全な「実装由来」ではない、しかし強い潜在的繋がりでもない
3. 構造バイアス (shuffled 0.51) を正しく引き算した上での評価が必要

### 5.2 判断材料
- 弱信号 +0.05 (σ 1.0) を「潜在的繋がりの証拠」とするか、「構造バイアスのノイズ」とするか
- 検証 B/C で詳細追跡するか、現時点で本系統の探索を一旦保留するか
- 検証 D (逆方向 word → atom) を実装するか

### 5.3 Step K + L の総合
- Step K (案 Y) は #L41 構造的解消、#L44 撤回
- Step L (検証 A) は CID-word 接続に弱信号確認、潜在的繋がりの候補
- 両者で v1106a の主要観察 (#L41/#L42/#L46) は構造事実として記録完了

---

**Report end.**
