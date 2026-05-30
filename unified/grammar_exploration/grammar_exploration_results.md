# Grammar Exploration 結果統合報告書

**Date**: 2026-05-30
**Author**: Code A
**Status**: 7 案完了 (案 1/3/5 + a/b/c/d + I/II/III/IV)
**位置づけ**: バージョン化せず軽量試行で「文法の萌芽」を探った結果集約

---

## 0. 探索の経緯

Taka 判断「重みづけを文法の要素として解釈したが、もう少しフラットに、実装に近い側から複数案を出す」を受け、`unified/grammar_exploration/` で軽量 post-process 試行を実施。

入力: `unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet` (frozen) のみ
書込み: `unified/grammar_exploration/` 配下のみ
物理層 frozen 厳密維持

---

## 1. 初期 3 案の結果サマリ

### 案 1: 終端 atom (24 atom 検証)
- 完全終端 (≥0.95): **0 個** — 絶対的終端記号は無い
- 完全通過 (≤0.05): **13 個** — WLD.science / FND.timeless / EXS.being 等
- 中間 (0.05-0.95): **11 個** — 文脈で役割切替

### 案 3: 文脈依存遷移 (7 atom 検証)
- **3/7 (42.9%) が文脈依存** (p<0.001 AND Cramér V > 0.2)
- 依存: ACT.stand / TIM.appear / CHG.grow

### 案 5: 相互情報量
- **順序考慮 npmi > 0.5: 6 ペア**
- **非順序 (共起のみ): 0 ペア**
- 強結合: FND.logic→ECO.withdraw, COG.learn→TIM.moment, FND.logic→COG.learn

→ **「順序を考慮すると文法的、共起だけだと文法でない」**

---

## 2. 深掘り 4 案の結果

### (a) 連鎖の探索
- 3 連鎖でマルコフ超え (log_lift > 1.0): **6 個**
- 4 連鎖高頻度: 自己反復 (TIM.appear×4 = 6041) が支配
- 非反復 4 連鎖: TIM.appear×3 → ACT.stand = 704 等の規則性

### (b) 中間 atom の役割切替
役割切替の強さ (range):

| atom | n | terminal_rate range | std |
|---|---:|---:|---:|
| CHG.grow | 4,117 | **0.745** | 0.346 |
| TIM.appear | 10,987 | **0.730** | 0.337 |
| CHG.begin | 307 | **0.729** | 0.418 |
| ACT.stand | 10,620 | **0.713** | 0.284 |

→ 5 atom が文脈で「終端 / 非終端」を明確に切り替える

### (c) 文脈依存深掘り
CHG.grow の prev → next 分布:
- prev=ACT.stand → next: CHG.grow 0.45 / ACT.stand 0.44 (バランス)
- prev=CHG.grow → next: CHG.grow 0.55 / ACT.stand 0.34 (CHG.grow 寄り)
- prev=CHG.begin → next: CHG.grow 0.65 (強く CHG.grow)

→ prev で next 分布が大きく変化、**文脈依存性確認**

### (d) 順序情報を保つ集計 — **決定的発見**

**turn 0 (start) でしか出ない atom (rate 1.00)**:
COG.enlightenment / PRP.shallow / TIM.moment / PRP.deep / ECO.withdraw / EXS.being / FND.timeless / FND.logic / PER.see / ACT.make (**10 個**)

**turn end (final) で多い atom**:
ACT.stand (0.49) / TIM.appear (0.42) / CHG.grow (0.40) (**3 個**)

→ **start 記号と end 記号の完全分離**

---

## 3. 統合深掘り 4 案 (I-IV)

### (I) 文法木構築
- 327 events で start → end 経路を抽出
- start 別 end 到達分布:
  - **PER.see → TIM.appear 80.95%** (見る → 現れる、極めて偏った接続)
  - その他 start は ACT.stand 寄り (40-60%)
- production rule top:
  - FND.logic → CHG.grow (13 events)
  - EXS.being → ACT.stand (10)
  - PRP.deep → TIM.appear (10)

→ **start-end 経路に明確な文法的接続パターンあり**

### (II) 役割切替ルール厳密化
- 役割が prev で明確に決まる (STRONG_*): **87.0%**
- ACT.stand: 12 prev で STRONG_TRANSIT、2 prev で STRONG_TERMINAL
- ACT.stand を transit 化する prev: PER.see / CHG.begin / COG.learn / PRP.shallow / ACT.make

→ **87% の prev で「terminal か transit か」が決定論的**

### (III) 位置情報込み重み層 W_ijp
- 位置別 (4 bin) asym_max: turn 0-5: 57 / 5-15: 55 / 15-25: 66 / 25-41: 83
- 位置別 density mean: **0.0107** (v1109 位置混合 0.0072 の **1.5 倍**)
- turn 0-5: 49 atom、position-unique **39 個** (start 専用 atom)
- turn 5-15 以降: position-unique 0 個 (同じ atom 集合内遷移)

→ **位置情報を入れると重み層の非対称性密度が向上**、特に start 位置が特殊

### (IV) 文脈依存性 全 atom 拡張
- 10 atom 検証、**STRICT 通過 4/10 (40%)** / LOOSE 通過 5/10 (50%)
- STRICT 通過: ACT.stand (V=0.31) / CHG.begin (V=0.29) / TIM.appear (V=0.28) / CHG.grow (V=0.24)

category 別 v_mean:
- **SOC 0.84 / PRP 0.62 / FND 0.47** (社会的・抽象的 category で強い文脈依存)
- TIM 0.36 / PER 0.32 / ACT 0.31 / CHG 0.27 (頻出 category)

→ **高頻度 atom ほど文脈依存が顕在化、低頻度 atom (SOC.nation 等) は強い文脈依存 (V=0.84) を示唆**

---

## 4. 統合的構造観察 — **ESDE 内部の文法萌芽**

### 4.1 確認された文法的特徴

| 文法的特徴 | 観察値 | 案 |
|---|---|---|
| **start / end 記号の完全分離** | 10 vs 3 atom | (d), (I) |
| **役割切替の決定論性** | 87.0% が prev で決まる | (II) |
| **文脈依存遷移** | 4/10 atom が strict 通過 | (IV) |
| **順序考慮で文法的、共起で消える** | npmi 順序 6 vs 共起 0 | (5) |
| **位置情報の文法的意義** | 39 start-unique atom | (III) |
| **start-end 経路の規則性** | PER.see→TIM.appear 81% 等 | (I) |
| **中間 atom の役割切替** | 5 atom (CHG.grow 等) | (b) |
| **マルコフ超え連鎖** | log_lift > 1.0 が 6 個 | (a) |

### 4.2 ESDE 文法構造の見取り図

```
start_atom (10 個、turn 0 専用)
   │
   ├─── 文法的経路 (production rule)
   │
   ├── 中間: 役割切替 atom (5 個)
   │    └── prev で terminal/transit を 87% 決定
   │
   └── 文脈依存 atom (4 個 strict)
        └── prev で next 分布が大きく変化

end_atom (3 個、turn end 多出)
   ├── ACT.stand (49%)
   ├── TIM.appear (42%)
   └── CHG.grow (40%)
```

### 4.3 「文法萌芽」の正体

ESDE 自己対話は:
- **start 記号** が固定された 10 atom (turn 0)
- **end 記号** が 3 atom に収束 (turn end)
- 中間に **役割切替 atom** が存在 (5 atom)
- 経路は **production rule** に従う (start → end の偏った接続)
- 高頻度 atom ほど **文脈依存** (prev で next が変化)

→ **これは「文脈依存文法 (CSG)」の構造を持つ**

---

## 5. v1109 重み層失敗の真因

### 5.1 v1109 の問題
v1109 重み層 W_ij (atom 2 体相関) は loop_rate 0.964、cat_transfer 0.014 で「過剰 loop 化」と報告。

### 5.2 真因 — 重み層の設計次元が不足
ESDE の文法構造には:
- **位置情報** (turn 0 vs end) — v1109 で未考慮
- **役割情報** (terminal vs transit) — v1109 で未考慮
- **文脈情報** (prev 別の next 分布) — v1109 で W_ij だけで近似

これらは 2 体相関で捉えられない:
- W_ij は「A → B の頻度」のみ
- 実際の文法は W(prev, A → B, position, role)
- 4-5 体相関が必要

### 5.3 修正案
v1109 を W_ijp (位置別) + W_ij(prev) (文脈別) + role_mapping (役割切替表) に拡張すれば、過剰 loop 化を回避し文法萌芽を捉えられる可能性。

---

## 6. Taka 直感の更新

| Taka 直感 (memory 19 + 各メモ) | 観察に基づく更新 |
|---|---|
| 「文法は重み蓄積で生まれる」 | **「重み蓄積だけでは不十分、位置・役割・文脈の構造が必要」** |
| 「応答時間が系を変化」 | **「位置情報 (turn) が文法的役割を持つ」** で部分検証 |
| 「主体性が内部に複数」 | **「start atom (10 個) が複数の主体性候補」** か |

---

## 7. 次の方向候補

| 方向 | 内容 | 実装規模 |
|---|---|---|
| (V) start-atom 別の主体性検証 | 10 start atom が「異なる主体性」か検証 | 軽 |
| (VI) position-aware 重み層実装 | v1109 の修正版 (W_ijp) | 中 |
| (VII) production rule 抽出 | start → end 経路を BNF 風に記述 | 中 |
| (VIII) CSG 形式での文法定義 | 観察を context-sensitive grammar として記述 | 重 |

Taka 構想「cid 時系列増殖、マーカー = 注目」とは:
- start atom (10 個) が「注目」の起点
- 経路展開 (中間 atom) が「時系列増殖」
- end atom (3 個) が attractor

→ **本探索の発見が Taka 構想と接続可能**

---

## 8. 出力ファイル一覧

### スクリプト (7 ファイル)
- `case_1_terminal_atom.py` / `case_3_context_dependent.py` / `case_5_mutual_information.py`
- `explore_a_chains.py` / `explore_b_intermediate_atoms.py` / `explore_c_context_depth.py` / `explore_d_order_preserving.py`
- `explore_I_grammar_tree.py` / `explore_II_role_rules.py` / `explore_III_position_weight.py` / `explore_IV_context_dependent_full.py`

### 出力 (parquet)
- 案 1: `case_1_terminal_rates.parquet`
- 案 3: `case_3_context_dependent.parquet`
- 案 5: `case_5_pmi_ordered.parquet`, `case_5_pmi_cooccurrence.parquet`
- (a): `a_triples_lift.parquet`
- (b): `b_role_switching.parquet`
- (c): `c_context_depth.parquet`
- (d): `d_order_asymmetry.parquet`, `d_position_distribution.parquet`
- (I): `I_grammar_paths.parquet`
- (II): `II_role_rules.parquet`
- (III): `III_position_asymmetry.parquet`
- (IV): `IV_full_context_dependent.parquet`

### 報告書
- `grammar_exploration_results.md` (本文書)

---

## 9. 一文サマリ

Grammar Exploration として `unified/grammar_exploration/` でバージョン化せず軽量試行 7 案 (案 1/3/5 + 深掘り a/b/c/d + 統合 I/II/III/IV) を実施、ESDE 自己対話内部に文法萌芽が実在することを多角的に確認 (start 記号 10 atom / end 記号 3 atom の完全分離 + 役割切替 87% 決定論性 + 文脈依存 4/10 strict 通過 + 順序考慮 vs 共起の決定的差 6 vs 0 + position 別 density 1.5 倍 + start-end production rule + マルコフ超え連鎖 6 個 + 中間 atom 役割切替 5 個)、v1109 重み層失敗の真因は「W_ij 2 体相関だけで位置・役割・文脈情報を含まなかった」と特定、Taka 直感「文法は重み蓄積で生まれる」を「重み蓄積だけでは不十分、位置・役割・文脈の構造が必要」に更新、ESDE 文法構造は文脈依存文法 (CSG) の特徴を持ち start atom (10 個) は主体性候補で経路展開は時系列増殖で end atom (3 個) は attractor として Taka 構想「cid 時系列増殖、マーカー = 注目」と接続可能、物理層 frozen 厳密維持 (書込み grammar_exploration/ 配下のみ)、次方向候補 4 件 (V-VIII)。

---

*以上、Grammar Exploration 結果統合報告書 (Code A、2026-05-30)。バージョン化せず軽量試行 7 案完了、ESDE 内部の文法萌芽を多角的に確認。次方向 (V)-(VIII) は Taka 判断。*
