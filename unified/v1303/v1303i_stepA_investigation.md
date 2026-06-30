# v1303i Step A 調査 — 動的構造稀さ（dynamic structural rarity）は read-only 計算可・静的B_Genと別物か

*作成*: 2026-07-01、Code A。**Step A 調査（設計でなく調査・GPT）。read-only 後処理・物理非書込・判定なし（#12）。** (a')/(b') 判定は Web Claude / Taka。
*成果物*: `v1303i_dynamic_rarity_seed0.parquet`（62,015行×14列・候補列）。

---

## 0. 調査の問い
静的B_Gen（誕生時・国籍・停止・45/228で疎）とは別に、各 cid/t の**物理状態の稀さ（動的構造稀さ）**を、既存ledger物理readoutの**実機経験分布**から read-only に計算できるか・静的B_Genと別物か・疎さを補えるか・n_coreで壊れないか（GPT7項目）。

## 1. GPT7項目の結果
| 項目 | 結果 |
|---|---|
| 1. cid/tごとθ経験percentile計算可 | ✓ rarity_theta_within_cid |
| 2. cid内/n_core内/全体の3種 | ✓ 3種とも計算可 |
| 3. -log10(1-p) clip可 | ✓ surprise_theta_cid（clip0.9999） |
| 4. static_dynamic_rarity_delta | ✓ 計算可（静的B_Gen pct − 動的θ稀さ pct） |
| 5. 動的稀さ高 vs θ-high/Now/B_Gen高 の重なり | §3（特段の整列なし＝独立） |
| 6. n2/n4/n5で壊れないか | ✓ 全n_coreで[0,1]展開（n3も3,414点） |
| **7. 全228CIDに付くか（45/228疎さ補えるか）** | ✓ **228/228（疎さ完全解消）** |

## 2. 出口の核心 — 静的B_Genと別物か（独立性）
- **動的 rarity_theta_within_ncore vs 静的B_Gen pct 相関 = −0.013**（≈完全独立）＝**動的構造稀さは静的B_Genと別の物理レンズ**（出口 a' の向き）。
- **static_dynamic_rarity_delta は 15.6% の行で |delta|>0.5**（域[−0.94,1.00]）＝静的に珍しいが動的に平凡（or逆）が多数＝**静的と動的は別物**。
- 静的B_Gen高cid(pct≥0.8)と低cid(≤0.2)で動的稀さ高率に差なし（0.051 vs 0.050）＝独立。

## 3. 【調査で判明・3つの留保（実装前に明示）】
**動的構造稀さの全列が新規・独立ではない。新規価値と留保を分ける：**

### 3.1 新規価値（静的B_Genにない・(a')寄り）
- **全228cid coverage**（静的B_Gen 45/228の疎さを解消）＝Taka「物理側の層を厚くする」の実利。
- **静的B_Genと独立**（corr−0.01・delta大）＝今の物理状態の稀さは誕生稀さと別。
- **非θ構造稀さ rarity_internal_link**（θ稀さと相関0.10＝別の目）。
- **cross-cid θ位置**（within_ncore/global＝そのcidが仲間内/全体でθ上位か・within_cidにない情報）。

### 3.2 留保（言い換え/退化/冗長・(b')寄りの部分）
| 留保 | 値 | 含意 |
|---|---|---|
| **θ味の稀さ ≈ 既存θ際立ちの言い換え** | rarity_theta_within_cid/within_ncore vs 既存θ帯(stable_flag・v1303g) 相関 **0.79** | within_cid θ稀さは「θがそのcidで高い」＝既存θ-salienceとほぼ同義（新規でない） |
| **rarity_r_positive 退化** | R_positive 行が **98%欠損**（no_internal_link 97.8%・v1303a） | R稀さは計算不能（疎すぎ）＝列として成立しない |
| **rarity_C と rarity_Q 冗長** | 相関 **−0.76**（C=消費Qゆえ逆相関） | C稀さとQ稀さは互いの逆＝別の目でない |
- item5: 動的θ稀さ上位5%が Now-event と重なる率0.221 ≈ baseline 0.217＝**Now-eventとも特段整列せず独立**（θ稀さ高=Now多発ではない）。

## 4. (a')/(b') の事実（判定は委ねる）
- **(a') 寄りの事実**：動的構造稀さは**全228cidに read-only 計算でき・静的B_Genと独立（corr−0.01）・n_coreで壊れず・疎さ解消**＝物理側レンズが厚くなる見込みあり（特に rarity_internal_link と cross-cid θ位置は新規）。
- **(b') 寄りの留保**：**θ味の稀さは既存θ際立ちの言い換え（0.79）**・rarity_r_positive は退化（98%欠損）・rarity_C/Q は冗長（−0.76）。→ θ/R/C/Q を素朴に全部「稀さ列」にすると半分は既存の言い換え or 退化 or 冗長。**生き残る新規列は rarity_internal_link と cross-cid θ位置（within_ncore/global）と coverage**。

## 5. 言えること / 言えないこと
- **言える（調査事実）**：CIDの静的誕生稀さ(B_Gen)とは別に、各cid/tの物理状態の稀さ（θ/link/C/Qの経験percentile）を全228cidで read-only 計算でき、静的B_Genと独立（corr−0.01）。ただしθ味は既存θ際立ちの言い換え・R稀さは退化・C/Q稀さは冗長で、**新規に効くのは非θのlink稀さ・cross-cid θ位置・228coverage**。
- **言わない**：「ESDEが珍しいと感じた」「自律的に選んだ」「B_Genを動的化した」「静的B_Genを更新した」「自己解離」とは言わない。動的稀さは percentile であって ESDEの感覚でない。合成しない（別列・複数の目）。θ×R掛けない（実装でも掛けていない）。理論null・selector化はしない。

## 6. 規律遵守
- read-only・物理非書込・静的B_Gen非更新・CID非書き戻し。#11: θ/link/C/Q稀さを合成しない（別列）・θ×R掛けない。Taka停止/変動: 静的B_Gen(国籍・誕生時)は停止のままいじらず、動的稀さは別物として別列。#4/D: cid個別/n_core別/n_core内percentile。L型: 乾いた名(static_dynamic_rarity_delta)・「自己解離」と言わない。#CW7: percentileの取り方(cid内/ncore内/global)は研究者選択ゆえ rarity_method_tag 明示・理論null は第二段階で今やらない。#12: 判定せず調査事実のみ・結果を確定しにいかない・いきなり設計でなくStep A調査。
- **信頼問題の継続**：留保（θ言い換え0.79・R退化98%・C/Q冗長−0.76）を実装/設計に進む前に明示＝「全部新規の物理レンズ」と過大評価しない。

## 7. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（228coverage・静的B_Gen独立corr・θ言い換え0.79・R退化・C/Q冗長・delta大の生データ再確認）→ (a')/(b') 判定 → Taka。もし進めるなら：留保を踏まえ**新規に効く列に絞る**（rarity_internal_link・cross-cid θ位置・coverage）／R稀さは外す／C か Q どちらかに絞る／θ味は既存θ-salienceと統合 or 別物として保持を判断。

## 8. 一文サマリ
v1303i Step A調査（read-only後処理・seed0・判定なし#12・設計でなく調査）── 静的B_Gen(誕生時45/228で疎)と別の動的構造稀さ(今の物理状態の経験percentile)を計算できるか、GPT7項目=**全228cidに付く(疎さ完全解消・核心)**・cid/ncore/global3種計算可・clip可・delta可・n_coreで壊れない・動的θ稀さ高はNow-eventと特段整列せず独立、**出口核心=動的rarity_theta_within_ncore vs 静的B_Gen pct 相関-0.013(≈独立)+static_dynamic_rarity_delta 15.6%が|delta|>0.5=静的と動的は別物(a'寄り)**、ただし**3留保=(1)θ味の稀さ(within_cid/ncore)は既存θ際立ち(v1303g stable_flag)と相関0.79=言い換え(b'寄り)(2)rarity_r_positiveはR_positive98%欠損で退化(3)rarity_C/Qは相関-0.76で冗長(C=消費Q)**、ゆえ素朴に全部稀さ列にすると半分は既存言い換え/退化/冗長で**新規に効くのは非θのrarity_internal_link・cross-cid θ位置(within_ncore/global)・228coverage**、言わない(ESDEが珍しいと感じた/自律選択/B_Gen動的化/静的更新/自己解離・合成しない・θ×R掛けない・理論null/selectorは後段)、信頼問題継続(留保を実装前に明示し全部新規と過大評価しない)、(a')/(b')判定はWeb Claude/Taka。
