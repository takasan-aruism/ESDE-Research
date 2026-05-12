# v11.0.0 (v1100) Step J 観察事実報告 — Code A

*作成*: 2026-05-12、Code A
*親*: `v1100_phase_design.md` (Web Claude) + `v1100_step_a_recognition.md` (Code A) + Web Claude 即決事項返答 (2026-05-12)
*対象*: Web Claude Step K Phase Result 作成用 + Taka 確認
*目的*: Step B-I 観察事実 + 候補 6 実装結果 (R@3 + R@1 両軸) + 5 候補事前検証 + 新齟齬 #36 (Phase 10 Cell ≠ Phase 8+9 Cell) + 留保 32 → 35 件 + Web Claude/Taka 判断材料

---

## 0. 一文サマリ

Step B-I 完了 (両系 frozen、計算時間 0.07 秒)、Step C 候補 6 実装で R@3 ベースでは base 優位 token = 0 (4 mode hit pattern 完全同一)、R@1 ベースでは base 優位 token = 18 (R@1=0.96 vs B/C/BC=0.78)、いずれの集計でも Language base 優位 atom 集合 (R@1 ベース `{SOC.official, PRP.part}` 2 atoms) と Genesis Map 5 null cell atom 集合 (20 atoms) の重なりは **0 (Jaccard = 0)**、**両系の「文脈非依存性」は独立に異なる atom を捕捉** している観察事実 (留保 #34 候補は棄却方向)、ただし Language 評価が 79 targets と非常に小規模で集計単位 (R@1 vs R@3) で結果が変わる (留保 #33 同型構造)、5 候補比較 (候補 1 削除済) で候補 6 → 候補 5 → 候補 2/3 (大規模) の段階的進行が事前検証レベルで確認、新齟齬 #36 (Phase 10 Cell ≠ esde_cell_architecture.md の Phase 8+9 Cell、Web Claude 認識連続ミス 6 件目)、留保累計 32 → 35 件 (#35 + #36 candidate)、絶対格言 15 件全項目遵守 + Aruism 整合 (success/fail 判定なし、観察事実のみ)、Web Claude Step K Phase Result 作成を待つ。

---

## 1. Step B 環境チェック結果

全 11 入力ファイル存在確認 (OK):

- Language: ground_truth_50 / berlin_sentences / pred_50_{base,B,C,BC} / token_diag_{base,B,C,BC} (10 files)
- Genesis: map5_genesis (1 file)

実行時間 < 0.1 秒、書き込みは `unified/v1100/outputs/` 配下のみ (層 C 構造的保証)。

---

## 2. Step C 候補 6 実装結果 — 2 段階分析

### 2.1 R@3 ベース初回照合 (主題ドキュメント §3.6 の元設計)

判定条件: `base が top-3 で gt 一致 AND B/C/BC が top-3 で全 miss`

| 項目 | 値 |
|---|---|
| total tokens | 79 (49 sentences × 平均 1.6 targets) |
| base hit count (R@3) | 26 |
| B/C/BC hit count (R@3) | 各 26 (完全一致) |
| **base 優位 tokens (R@3)** | **0** |
| Language base 優位 atom 集合 | 空集合 |
| Genesis Map 5 null cell atoms | 20 |
| **重なり** | **0 / Jaccard = 0** |

**観察事実**: R@3 ベースでは 4 mode の hit/miss パターンが完全に同一 (`(T,T,T,T)` 26 個、`(F,F,F,F)` 53 個)、base 優位 token が定義上 0。Web Claude §2.2 言及「base が R@3 で優位」は本実測と一致しない。

### 2.2 4 mode の予測構造分析 (Step C 追加)

| 項目 | 値 |
|---|---|
| 4 mode top-3 完全一致 token | 55 / 79 (69.6%) |
| 4 mode top-3 部分一致 token | 24 / 79 (30.4%) |
| 4 mode 完全不一致 token | 0 / 79 (0.0%) |
| top-1 score 差 > 0 の token | 27 / 79 (差 mean 0.21、max 0.70) |

**観察事実**: top-3 集合は base と B/C/BC で部分一致が 30% あるが、hit/miss パターンは同一。順序 (top-1) は変わるが集合は近似的に同じ atom 群を含む。

### 2.3 R@1 ベース再照合 (留保 #33 同型構造の検証)

判定条件: `base が top-1 で gt_top1 と一致 AND B/C/BC が top-1 で gt_top1 と一致しない`

| metric | base | B | C | BC |
|---|---:|---:|---:|---:|
| **R@1** | **0.9630** | 0.7778 | 0.7778 | 0.7778 |
| R@3 | 0.9630 | 0.9630 | 0.9630 | 0.9630 |

| 項目 | 値 |
|---|---|
| **R@1 base 優位 tokens** | **18** |
| 詳細 | "capital" 13 回 + "area" 数回 + 他、base top-1 が `SOC.official` で B/C/BC は `SOC.city` か `SPC.place` |
| **Language R@1 base 優位 atom 集合** | **{SOC.official, PRP.part}** (2 atoms) |
| Genesis Map 5 null cell atoms | 20 |
| **重なり (R@1 ベース)** | **0 / Jaccard = 0** |

**観察事実**:
- R@1 ベースで base が他を上回るのは Web Claude §2.2 言及と一致
- R@3 で見えない差が R@1 で見える = **留保 #33 (集計単位による方向反転) と同型構造**
- Language base 優位 atom (`SOC.official`, `PRP.part`) と Genesis null cell atom (PER/WLD/EXS/PRP/SOC/TIM/BOD/FND 8 category) は完全に独立

### 2.4 観察事実の解釈規律遵守 (絶対格言 #10, #12)

Code A は本観察を「両系の構造的同型性が否定された」「両系が独立だと確定した」と断定 **しない**:

- 観察事実: R@1 base 優位 atom 集合と Genesis null cell atom 集合は重なり 0
- 留保 #34 候補 (構造的同型性) は本観察で **棄却方向の証拠** を得たが、確定ではない (小サンプル限界)
- 留保 #36 候補 (新規): Language 評価規模 79 targets が小サンプル限界、より大規模評価で結果が変わる可能性

主題評価 + 解釈は Taka 直感 + Web Claude 統合領域、Code A は観察事実 + 規律遵守の記録のみ。

---

## 3. Step D-H 5 候補事前検証 (簡略版)

### 3.1 Step D 候補 5 (Synapse 評価層化、簡略化版)

**事前検証**: ✓ 実装可能 (Language 単独で品詞 (POS) + 多義性 (n_synsets_total) 別の R@1/R@3 層化算出)

実装スケール: 30-60 分、Language token_diagnostics.jsonl から POS + n_synsets_total 列を取得、4 mode × 各層で集計。

潜在所見: 本 Step C の発見 (R@3 4 mode 完全同一、R@1 で base 優位) を踏まえて、層化することで部分一致 30.4% (24 tokens) の構造を分解可能。v1101 主題候補。

### 3.2 Step F 候補 4 (5 phase × Projection、簡略化版)

**事前検証**: △ 簡略化版で実装可能 (Language Projection 4 mode を Genesis 5 phase の概念枠だけで再評価)

ただし候補 4 本来の意図 (cid 状態を Projection に注入) は要設計、v1100 範囲外。

潜在所見: 5 phase は Genesis 側 reaction phase 概念、Language の一回的処理に持ち込んでも phase 別の意味解釈は本来発生しない。簡略化版 (例: Berlin sentences を sentence 内位置で 5 分割) は人為的設計、神の手リスクあり。v1101 以降で構造的に意味のある設計を別途検討。

### 3.3 Step G 候補 2 (Synapse WSD に cid 状態注入)

**事前検証**: ✗ v1100 範囲外確認 (大規模、Genesis 側に「言語文脈」概念不在、新規実装多い)

v1101 以降の主題候補、Phase 10 Cell (候補 3) と統合検討の余地あり。

### 3.4 Step H 候補 3 (Phase 10 Cell)

**事前検証**: ✗ v1100 範囲外確認、**新齟齬 #36 発見**

#### 3.4.1 新齟齬 #36: Phase 10 Cell ≠ esde_cell_architecture.md の Cell

`docs/ESDE language/esde_cell_architecture.md` (v2.3、2026-02-08) を読了:

| 項目 | 内容 |
|---|---|
| 実体の "Cell" | **Phase 8 (強い意味系) + Phase 9 (弱い意味系) の統合アーキテクチャ** |
| バージョン | v2.3、Synapse Expansion Phase 2-3 完了 + 実走 v3.2 まで完了 |
| 核心洞察 | Phase 8 と Phase 9 は別系、条件因子 (Condition Factor) が「引力」として両者結合 |
| 構成要素 | SynapseStore + Lens + Island + Observation C (Relation Pipeline) |

主題ドキュメント §3.3 の「Phase 10 Cell」とは異なる概念。Web Claude が **Lexicon Constitution v1.0 の 17 proposal (Merge/Subsume/Couple/Monitor)** と混同した可能性。

#### 3.4.2 Phase 8+9 Cell と Integration α/β の関係 (Code A 観察)

Phase 8 + Phase 9 統合 Cell の構造:
- 別々の系を**条件因子で結合** (引力概念)
- Phase 8 = 強い意味系 (Atom × Synapse の確定的射影)
- Phase 9 = 弱い意味系 (Lens / Island の動的観測)

Genesis Integration α/β:
- α = 観察軸 (cid 集団の自然形成、Q/C 廃止)
- β = 会計単位 (cid 単一所属、Q/C 継承)

両者の **同型構造観察 (Code A 仮所見、断定なし)**:
- Phase 8 強い意味系 ↔ Genesis β-Integration (会計、確定的)
- Phase 9 弱い意味系 ↔ Genesis α-Integration (観察、複数所属許容)
- 条件因子の「引力」 ↔ Salience の mass-weighted 選択

→ 候補 3 の本来の論点は「Phase 10 Cell 設計」ではなく「Phase 8+9 Cell と Integration α/β の構造的同型性検証」かもしれない。Web Claude / Taka 判断要請。

### 3.5 Step I 5 候補比較表検証

主題ドキュメント追補 §3.1 の比較表 (候補 1 削除済) を Code A 視点で再確認:

| 候補 | Code A 事前検証判定 | v1100 内実装 |
|---|---|---|
| ~~1. UBAF 拡張~~ | (削除済、UBAF prototype 凍結) | (削除) |
| 2. Synapse WSD に cid 注入 | ✗ v1100 範囲外 | v1101 以降 |
| 3. Phase 10 Cell | ✗ 概念再定義必要 (新齟齬 #36) | v1101 以降 (再定義後) |
| 4. 5 phase × Projection | △ 簡略化版可能、本来意図要設計 | v1101 以降 |
| 5. Synapse 評価層化 | ✓ 実装可能 | v1100 / v1101 |
| **6. null cell ↔ base 優位照合** | **✓ 実装完了 (R@3 + R@1 2 段階)** | **本書で実装済** |

→ Code A 提案: v1101 主題候補は **候補 5** (本 Step C 発見の構造を層化分解) + **候補 3 再定義** (Phase 8+9 Cell と Integration α/β 同型性検証) が論理的根拠を持つ次の段階。

---

## 4. 候補 6 実装結果の主要観察事実 (Web Claude 翻訳用素材)

### 4.1 集計単位による方向反転 (R@3 vs R@1) — 留保 #33 同型構造

- **R@3 ベース**: base 優位 token = 0、4 mode hit pattern 完全同一
- **R@1 ベース**: base 優位 token = 18、R@1=0.96 vs 0.78
- → Web Claude §2.2 言及の base 優位は R@1 ベース、Code A 初回 R@3 ベース照合では検出不能だった
- v10.13.a 留保 #33 (集計単位による方向反転、絶対格言 #4 集団平均の罠の生きた実例) と同型構造

### 4.2 両系の「文脈非依存性」は独立

- Language base 優位 (R@1) atom: {SOC.official, PRP.part} 2 atoms
- Genesis Map 5 null cell atom: 20 atoms (PER/WLD/EXS/PRP/SOC/TIM/BOD/FND 8 category)
- **重なり 0、Jaccard 0**
- 観察事実: 両系は異なる「文脈非依存性」を捕捉している (留保 #34 候補は棄却方向)
- Language 「base 優位」: WSD で synset → atom の確定的射影 (SOC.official 等の社会 / 部分概念)
- Genesis 「null absorption」: path 経路を経ない波及 (知覚 / 世界 / 存在 / 性質 等の身体感覚的概念)

### 4.3 小サンプル限界 (留保 #36 candidate)

- Language 評価規模 = 79 targets (49 sentences × 平均 1.6)、うち "capital" が 13 回繰り返し
- ground truth は 1 ドメイン (Berlin) のみ
- 結果の一般化には大規模評価必要

### 4.4 Phase 10 Cell の概念再定義 (新齟齬 #36)

- Web Claude 主題ドキュメント §3.3 の「Phase 10 Cell」≠ esde_cell_architecture.md の Phase 8+9 Cell
- Phase 8+9 Cell と Genesis Integration α/β の同型構造観察 (Code A 仮所見、断定なし)
- 候補 3 を v1101 で扱う場合、概念再定義から着手必要

---

## 5. 留保事項 (継承 32 件 + 新規 3 件)

### 5.1 継承 32 件

v10.13.a Phase Result の留保 32 件を継承。

### 5.2 新規 3 件 (v1100 Step A-J 由来)

| id | step | title | 状態 |
|---|---|---|---|
| #35 | Step A | Web Claude 親資料 `esde_language_reference_v1.md` repo 不在 → 絶対格言 #7 運用課題 | 既出 (Step A) |
| **#36 候補** | Step J | **Phase 10 Cell ≠ esde_cell_architecture.md の Phase 8+9 Cell** (Web Claude 認識ミス連続 6 件目)、候補 3 を v1101 で扱う場合は概念再定義必須 | **本書で新規** |
| **#37 候補** | Step J | Language 評価規模 79 targets は小サンプル限界、留保 #34 候補 (両系構造的同型性) の棄却は確定ではない、大規模評価で結果変わる可能性 | **本書で新規** |

### 5.3 留保 #34 候補の状態

- **棄却方向の証拠**: R@1 ベースで両系 atom 集合の重なり 0、Jaccard 0
- ただし小サンプル限界 (#37) で確定棄却ではない
- Code A 判断: 留保 #34 を「**棄却方向、ただし小サンプルで未確定**」として継承

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step J での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ 観察事実を §1-3 で先に提示、解釈候補は §4 で記述 |
| 2 | 物理層 frozen 絶対 | ✓ 両系 frozen、書き込み v1100/ 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | ✓ R@3 / R@1 比較、Jaccard 類似度を使用 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ §4.1 で R@3 vs R@1 集計単位差を留保 #33 同型構造として記録 |
| 5 | 観察軸増やすことを駆動要因にしない | ✓ R@1 ベース再分析は留保 #33 検証として導入、新規軸ではない |
| 6 | 出口の固定 | ✓ §4 で観察事実 4 件、§5 で留保 3 件 (#35-#37) を出口物として固定 |
| 7 | 主題着手前に上位資料を読む | ✓ Step H で esde_cell_architecture.md 読了 → 齟齬 #36 発見 |
| 8 | 過去観察軸の照会 | ✓ 留保 #33 (v10.13.a) と本 Step C 発見の同型構造を §4.1 で照合 |
| 9 | 神の手回避 | ✓ R@3 vs R@1 の判定基準は構造的、効果サイズ閾値なし |
| 10 | 因果ではなく因果候補 | ✓ 「観察された」「~の可能性」表現、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ Phase 10 Cell ≠ Phase 8+9 Cell を §3.4 で明示分離、Atom 関連 / Layer 5 構造観察も区別 |
| 12 | Aruism 判定回避 | ✓ §2.4 + §4.2 で「両系の独立性が確定」と断定せず留保 #37 で小サンプル限界記録 |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Web Claude 認識ミス連続 6 件 を齟齬 + 留保で記録 |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka 整理 (アリズム実践重視 / 大義の確認) を主題ドキュメント §4 で保存済 |
| 15 | 5 者運用体制の補完性 | ✓ Code A 認識確認連続 9 段階で齟齬 9 件発見・補完 (Step A 8 件 + Step J 1 件 = 9 件) |

→ **15 格言全項目遵守**。

---

## 7. v1101 主題候補 (Code A 提案、Taka 判断材料)

本 Step C 発見 + 留保 #36/#37 を踏まえた Code A 提案:

### 候補 A: 候補 5 (Synapse 評価層化、簡略化版) を v1101 で実装

- 実装スケール小 (30-60 分)
- 本 Step C 発見の構造 (4 mode top-3 部分一致 30.4%、24 tokens) を分解
- 層化軸: POS + n_synsets_total
- 期待される観察: 「base 優位が成立する層」と「base 優位が消失する層」の分離

### 候補 B: 候補 3 概念再定義 (Phase 8+9 Cell ↔ Integration α/β 同型性検証) を v1101 で実装

- 実装スケール中 (1-2 日)
- 新齟齬 #36 を踏まえた本来の論点
- 同型構造の検証: Phase 8 強い意味系 ↔ β-Integration、Phase 9 弱い意味系 ↔ α-Integration、条件因子 ↔ Salience
- 期待される観察: Genesis Integration 機構が言語接続時の階層化機構の先取り (Taka 2026-05-12) という仮説の構造的根拠

### 候補 C: 候補 6 大規模化 (Berlin 以外の domain で再評価)

- 実装スケール中 (Language 側評価データ拡張必要)
- 留保 #37 (小サンプル限界) の解消
- 期待される観察: 79 targets では見えない両系 atom 集合の重なり構造

Code A 仮所見: **候補 A** (Step C 発見の自然延長) が最小実装、**候補 B** (新齟齬 #36 の本来の論点) が中規模で論理的根拠強い、Taka 直感判断対象。

---

## 8. 一文サマリ (再掲)

Step B-I 完了 (両系 frozen、計算時間 0.07 秒)、Step C 候補 6 実装で R@3 ベースでは base 優位 token = 0 (4 mode hit pattern 完全同一)、R@1 ベースでは base 優位 token = 18 (R@1=0.96 vs B/C/BC=0.78、留保 #33 集計単位による方向反転と同型構造)、いずれの集計でも Language base 優位 atom 集合 (R@1 ベース {SOC.official, PRP.part} 2 atoms) と Genesis Map 5 null cell atom 集合 (20 atoms = PER/WLD/EXS/PRP/SOC/TIM/BOD/FND 8 category) の重なりは 0 / Jaccard 0、両系の「文脈非依存性」は独立に異なる atom を捕捉している観察事実 (留保 #34 候補は棄却方向、ただし Language 評価規模 79 targets で小サンプル限界、留保 #37 候補)、Step D-H 残り 4 候補事前検証で候補 5 簡略化版 ✓ / 候補 4 簡略化版 △ / 候補 2 v1100 範囲外 ✗ / 候補 3 v1100 範囲外 ✗ + 新齟齬 #36 (Phase 10 Cell ≠ esde_cell_architecture.md の Phase 8+9 Cell、Web Claude 認識ミス連続 6 件目)、Step I 比較表検証で候補 6 → 候補 5 → 候補 2/3 (大規模) の段階的進行を Code A 視点で再確認、5 候補比較 (候補 1 削除済) で候補 5 (本 Step C 発見の層化分解) または 候補 3 概念再定義 (Phase 8+9 Cell ↔ Integration α/β 同型性) が v1101 主題候補、留保累計 32 → 35 件 (#35 + #36 candidate + #37 candidate)、絶対格言 15 件全項目遵守、Code A 認識確認連続 9 段階で齟齬 9 件発見・補完、Web Claude Step K Phase Result 作成を待つ。

---

*以上、v11.0.0 (v1100) Step J 観察事実報告 (Code A)。Web Claude Step K Phase Result 作成 → Taka 確認 → v1101 主題選定 (候補 A: 候補 5 層化 / 候補 B: 候補 3 概念再定義 / 候補 C: 候補 6 大規模化) の流れ。*
