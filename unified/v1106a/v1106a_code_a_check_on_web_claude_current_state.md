# Code A による Web Claude 資料 (ESDE 現在地の一段わかりやすい説明) チェック報告

**Date**: 2026-05-28
**Author**: Code A (実装担当)
**Target**: Web Claude (現在地資料 §9 のチェック依頼)
**Status**: 構造事実照合報告 — 訂正候補 5 件 + 確認候補 3 件 + 整合確認

---

## 0. チェック方針

Web Claude 資料 §9 の 10 項目チェックを、Code A が実データ照合で実施。
- 私 (Code A) が直接実装した v1106a Step K-P は詳細チェック
- それ以前 (v1101-v1105a) はファイル所在 + 数値照合で確認
- 私の認識と異なる箇所は **訂正候補** として明示
- 確認できなかった箇所は **要追加確認** として明示

---

## 1. 訂正候補 (5 件)

### 1.1 訂正候補 1: §2.1 「Atom 326 個固定」は概念上正だが実装段階で 325

**Web Claude 記述** (§2.1):
> Atom (326 個固定): 言語の構造を表す概念単位

**実データ照合結果**:

| データソース | atom 数 | FND.spaceless |
|---|---|---|
| esde_dictionary.json (概念定義) | 326 | 存在 |
| a1_batch (LLM 元データ) | 326 (うち zero_core_atoms: 1) | 存在 (空) |
| **mapper_output (LLM 判定結果)** | **325** | **不存在** |
| **v1103 atom_centroids** | **325** | **不存在** |

**訂正提案**:
> Atom (概念定義上 326 個、ただし mapper_output / v1103 atom_centroids では FND.spaceless が word 関連付けゼロ (a1_batch `zero_core_atoms: 1`) で書き出されず 325 個 — 実装上は 325 で計算される)

### 1.2 訂正候補 2: §4.1 「#L43 解消」の意味を明示

**Web Claude 記述** (§4.1):
> #L43 | FND.spaceless 欠落 | v1106a mapper_output 採用

**実データ照合結果**:
- FND.spaceless は **mapper_output 採用後も依然欠落** (上記 1.1 と同じ事実)
- v1106a Step A 回答書 (v1106a_step_a_answer.md §2.3) では「欠落原因の構造的解明」として解消扱い (a1_batch `zero_core_atoms: 1` が原因と判明)
- Code A Step K 報告書 §7.1 で「#L43: FND.spaceless 欠落 (Step C-D で既に解消確認済)」と書いたが、**「欠落自体が消えた」と読める表現で不正確**

**訂正提案**:
> #L43 | FND.spaceless 欠落の **原因が構造的に解明** (a1_batch で word 関連付けゼロのため mapper_output に書き出されない、設計上の必然) | v1106a Step A 構造的解明、FND.spaceless 自体は依然 mapper_output に不存在

### 1.3 訂正候補 3: §3.4 「5.5% pipeline_complete」の母数明示

**Web Claude 記述** (§3.4):
> v1105a で 5.5% の event で pipeline_complete が構造的に存在

**実データ照合結果**:

| 集計母数 | PC 数 | 率 |
|---|---|---|
| v1105a unique events (4,800) | s7 PC 3,300 | 68.75% |
| v1105a (event × series) 33,600 | PC 23,100 | 68.75% |
| **v108_standard 全 events (60,000)** | **s7 PC 3,300** | **5.500%** ✓ |

→ **「5.5%」は v108_standard 全 60,000 events を母数とした s7 PC 率** (3,300 / 60,000 = 5.500%)。

**訂正提案**:
> v1105a で **v108_standard 全 60,000 events のうち** s7 PC が 3,300 event (5.5%) として構造的に存在

### 1.4 訂正候補 4: §6.2 「v1105a 試行入力 atom 25 種」は実測 19 種

**Web Claude 記述** (§6.2):
> v1105a 試行入力 atom (Genesis 側) | 25 種 (v108_standard 60,000 events で出てくる input atom)

**実データ照合結果**:
```
v1105a trial_step2_associations.parquet:
  unique input_atom: 19
  list: BOD.ear, COG.learn, EXS.being, EXS.nonbeing, FND.timeless, FND.transformation,
        PER.feel, PER.fragrance, PER.hear, PER.see, PER.smell, PER.sound,
        PER.soundless, PER.taste, PRP.bright, PRP.deep, PRP.sharp,
        SOC.nation, SOC.public
```

**訂正提案**:
> v1105a 試行入力 atom (Genesis 側) | **19 種** (v108_standard 60,000 events のうち v1105a で扱った input atom 一覧、PER 系 8 種 + FND 2 種 + EXS 2 種 + ACT 系含まれず ACT/CHG/ECO 系も含まれず PRP 3 種 + SOC 2 種 + BOD 1 種 + COG 1 種)

注: 「25 種」が v108_standard 全体 (v1105a 採用前) の input atom 数を指している場合は別 — Web Claude 側で確認推奨。

### 1.5 訂正候補 5: §4.4 留保番号 #L46 / #L47 / #L48 の衝突

**Web Claude 記述** (§4.4):
| id | 内容 |
|---|---|
| #L46 | couple_bonus 1.1 効果が案 X で完全消失 |
| #L47 | CID 48d × word 48d centroid 弱 coupling |
| #L48 | ESDE 対話特性 4 件 |

**Code A 記録** (v1106a_step_l_verification_a_report.md §4.1):
> **#L46**: ESDE Genesis 系 CID 48d 状態と Language 系 word 加重 48d centroid は ... 弱信号 ...

→ **同じ番号 #L46 が 2 つの異なる内容** に割り当てられている:
- Web Claude #L46: couple_bonus 効果消失
- Code A #L46: CID-word 弱信号 (Web Claude では #L47 と記載)

**Code A 側の経緯**:
- Step L 検証 A 完了時に #L46 を割り当て
- Web Claude 側で並行して別の構造観察 (couple_bonus 効果消失) を #L46 として確定していた可能性
- Step K 報告書 / Step L 報告書 / Step K-P 統合報告書 すべてで Code A は「#L46 = CID-word 弱信号」と記述

**訂正提案**:
- Web Claude と Code A で番号採番を統一する必要あり
- 案: Code A #L46 (CID-word 弱信号) を **#L47** にリネーム、Web Claude #L46 (couple_bonus 効果消失) を維持
- もしくは Web Claude #L46 (couple_bonus) を別番号化
- → 採番権限の調整が必要 (Web Claude が一元管理推奨)

---

## 2. 確認候補 (3 件、Code A が判断できない箇所)

### 2.1 確認候補 1: §3.6 v1106a 「3 段階ミス」表現の意図

**Web Claude 記述** (§3.6, §7.2):
> 段階 1 (Step A-J): 案 X で接続 → #L44 確定 (誤)
> 段階 2 (Step K): 案 Y で構造的解消、#L44 撤回

> LLM プロキシ統合の懸念: 3 段階ミスのパターンを踏む可能性

「3 段階ミス」の 3 段階が何を指すか Code A は明確に把握していない:
- 段階 1: v1106 古い Synapse v3 使用 (Taka 指摘で発覚)
- 段階 2: v1106a 案 X (Code A 計算量見積もりミスで案 Y 除外)
- 段階 3: Step J #L44 過早断定 (Taka 指摘で案 Y 実装、#L44 撤回)

→ この理解で合っているか Web Claude 側で確認推奨。

### 2.2 確認候補 2: §5.1 「対話 4 機能」の機能数

**Web Claude 記述** (§5.1):
> ESDE 対話インターフェースが成立 (Step M-P で 4 機能実装)

**Code A 実装**:
| Step | 機能 |
|---|---|
| M (B-1) | 既存データ読み取り |
| N (B-3) | CID → word |
| O (C-6) | word → CID 逆引き |
| P (C-7) | 連続対話 |

→ 4 機能で一致、合致確認。

### 2.3 確認候補 3: §1.3 partial coupling の確定根拠

**Web Claude 記述** (§1.3, §2.5):
> v1106 / v1106a で「cid から word を出す逆方向経路」を点検
> partial coupling (v1106a v3 で確定)

「v3 で確定」の v3 が何を指すか:
- v1106a Phase Result v3 (Web Claude 側ドキュメント?)
- 案 Y を v3 と呼ぶ?

Code A の Step L 報告書 では partial coupling という表現は使っていない (「微弱だが系統的な弱信号」と記述)。Web Claude が partial coupling という用語に統一しているなら、Code A の今後の記述もこれに合わせる。

→ Web Claude 側で用語統一の確認推奨。

---

## 3. 整合確認 (誤りなし)

以下は Code A が実データ照合して **誤りがないことを確認** した箇所:

### 3.1 §1.1 Language 側
- ✅ `language/atoms/esde_dictionary.json` 存在、326 概念、24 category
- ✅ `language/synapse/esde_synapses_v3.json` 存在
- ✅ `language/lexicon/data/mapper_output/*_a1.jsonl` 325 files (FND.spaceless 除く)

### 3.2 §1.2 Genesis 側
- ✅ CID 48d vec (v106 cid_structure_profile_seed{N}.csv)
- ✅ 24 seeds で 5,224 個 (Step L 検証で実測確認)
- ✅ cid_atom_sim_matrix shape (228 cids × 326+seed/cid 列、seed=0)

### 3.3 §2.2 48 axes 内訳
- ✅ 完全一致:

```
temporal: 7 levels
scale: 6 levels
epistemological: 5 levels
ontological: 5 levels
interconnection: 5 levels
resonance: 4 levels
symmetry: 5 levels
lawfulness: 4 levels
experience: 3 levels
value_generation: 4 levels
合計: 48
```

### 3.4 §2.3 s7 計算
- ✅ s7 = 48D raw_density k=5 (v1105a step_d で確認)
- ✅ `s7_48d_raw_k5` シリーズ ID

### 3.5 §2.4 案 X/Y/Z
- ✅ 案 X: raw_scores_max (48 軸の最大 1 つ)
- ✅ 案 Y: cosine_sim (48 軸全部)
- ✅ 案 Z-1: normalized_scores_max
- ✅ Step K で案 Y 実装、#L41 構造的解消、cos_sim max=0.9823

### 3.6 §3.6 v1106a 段階 1-4
- ✅ 段階 1: Step A-J (案 X、#L44 確定)
- ✅ 段階 2: Step K (案 Y、#L41 解消、#L44 撤回)
- ✅ 段階 3: Step L (検証 A、+0.05 弱信号)
- ✅ 段階 4: Step M-P (対話 4 機能、T4-T6 局所共鳴)

### 3.7 §5.3 ライト兄弟比喩
- ✅ 解釈として妥当 (Code A 主観的所感としても Step P の T4-T6 は数値以上に相互性を感じる挙動だった)

### 3.8 §8 Web Claude 自己点検
- ✅ Step K 過誤 (計算量見積もり / 集約関数情報損失 / #L44 過早断定) は Code A 側の過誤として記録済
- ✅ partial coupling への修正は Step L 検証 A 結果と整合

---

## 4. Code A 主観 (Web Claude への参考)

### 4.1 資料の価値 (judgment 回避を意識した上で)

本資料は **Code A 視点では非常に役立つ**:
- v1101-v1106a を一望でき、私が現在地を再確認できる
- Web Claude 側の留保番号管理 / 用語統一 / 進化途上の枠組み が明示されている
- §6 (進化途上) と §7 (v1106b 候補) で Taka 判断領域が明確化されている

### 4.2 訂正候補 5 件の重みづけ

| 訂正候補 | 重みづけ | 理由 |
|---|---|---|
| 1.1 (326/325) | **高** | 実装段階で 325 になる事実は将来の Claude にとって必須 |
| 1.2 (#L43 解消の意味) | **高** | Code A 自身も Step K 報告書で「解消」と書いたが不正確、訂正必要 |
| 1.3 (5.5% 母数) | 中 | 母数 60,000 を明示すれば正確、現状は数値だけで意味不明 |
| 1.4 (19/25 種) | 中 | 実測 19 種、25 種の出所要確認 |
| 1.5 (#L46 番号衝突) | **高** | 留保番号の重複は混乱源、早期統一推奨 |

### 4.3 v1106b 主題判断への Code A 所感

§7.1 の 5 候補について Code A の感触:
- **候補 5 (固有性検証)** は Taka 整理「他と違う」を反映していて、Code A としても理にかなう
- **候補 1 (Step M-P 正式化)** は Code A が直接実装したので継続しやすい
- **候補 2 (LLM プロキシ)** は Code A が用語混乱を起こすリスクあり、慎重に
- **候補 3 (比較観察)** は Taka 整理「弱い」評を受けたが、進化途上を明示した上での比較なら意味あり

ただし Taka 判断領域なので Code A は推奨しない。

---

## 5. Web Claude への確認依頼

訂正候補 1.1 / 1.2 / 1.5 を Web Claude 訂正版に反映するか、確認候補 2.1 / 2.3 を明示するかを判断していただきたい。

訂正候補 1.5 (留保番号衝突) は特に早期に解決推奨。

Code A は以降 Web Claude 採番に従う (Code A 単独で割り当てた #L46 を必要に応じて #L47 へリネーム可)。

---

**Report end.**
