# v1113 系列 — 全体の流れ整理 (地面 → 足場 → 床 → 異なる自我 → 会話の芽)

date: 2026-06-04
from: Code A / Web Claude / Taka 共有
status: ロードマップ整理、v1113 (地面) が今回着手

---

## 0. 何を作ろうとしているか

ループ問題を解くために、Center が Atom の情報を持つ「異なる自我」になり、入力に対して応答の向きが変えられる構造を、段階的に組み上げる。

その**最初の一段**は「**地面が在るか**」を確認すること。地面がなければ、足場も床も自我も会話も載らない。

これまで (v1110-v1112) は痩せた phase 表現 (occupancy[64]) で地面を測ろうとして、測定器が壊れていた / 揃わなかった。今回は CID の本当の情報で測り直す。

---

## 1. 段階的構築 (Taka 整理 2026-06-04)

| 段階 | 名前 | 問い | 観察対象 |
|---|---|---|---|
| **v1113** | **地面** | 別 seed の二系の CID に「特に似てる組」が在るか | sim(atom, real_other) vs sim(atom, null_others) |
| Stage 2 候補 | **足場を一個置く** | 「特に似てる CID の組」を Center が一つの単位として束ねられるか | Center が高 sim ペアを集合として保持できる検証 |
| Stage 3 候補 | **足場が床になる** | 単位が溜まって、Center が Atom の情報を持つ「異なる自我」になるか | Center が複数の単位を蓄積、Atom と分離した特性を持つ確認 |
| Stage 4 候補 | **会話の芽** | 入力が来たとき、Center が「どの単位を立てるか」で応答の向きが変わるか | 同じ入力でも Center 状態 (どの単位が立つ) によって応答が変わる |

各段階は前段が成立した上で初めて意味を持つ。v1113 で地面が無いと結論されれば、Stage 2 以降は構造的に成立しない (測定器を組み直すか、別アプローチへ)。

---

## 2. v1113 (今回 = 地面確認) の位置づけ

### 2.1 問い (一点だけ)

別 seed の二系 (Atom 系 / Other 系) の CID 集合に、**「皆同じだから似てる」を引き算した上で**、**特に似てる組**が在るか。

### 2.2 なぜ「皆同じだから似てる」を引き算するか

ESDE は「どの seed でも CID は似た特性分布」を持つ (n_core=2 が 85% 等、seed 共通の経験則)。この「皆同じ」分の sim は地面ではなく、ESDE のメタな性質。
→ null = 別の無関係な seed の Other 系を複数 (5 系) 構築、その sim を「皆同じだから似てる」の base line とする。
→ 実観察 sim が null base line を **明確に超える** なら、それは「この二系が特に響く = 地面が在る」候補。

### 2.3 何を見れば「地面が在る」か

real = sim(atom, other=999)、null = sim(atom, [12345, 54321, 7777, 11111, 33333]) の 5 sim 分布。

- `rank = 5/5` (real が全 null を上回り) かつ `real > null_max` → **「特に響く」候補が観察された**
- `rank = 3/5` 程度 → **「どの系とも同程度 = 皆同じ = 地面でない」**
- `rank = 0/5` → **「別系のほうが似てる = 逆向き」**

3 atom seed (= [42, 100, 200]) で全 atom について揃えば構造的観察、1/3 のみなら atom 依存。

### 2.4 v1113 だけで答えるべき (crown 防止)

v1113 は「地面が在るか」だけ答える。
- Stage 2 (足場を置く) に進むか進まないかは別判断
- 「Unified 成立」「会話が立った」「自我が生まれた」は **絶対に書かない**
- 報告は「特に似てる組が出た / 出ない」だけ

---

## 3. v1113 で取れない / 答えない問い (Stage 2 以降に持ち越し)

- 「特に似てる組を Center が単位として束ねられるか」(Stage 2)
- 「単位が溜まって自我になるか」(Stage 3)
- 「会話の向きが変わるか」(Stage 4)

これらは v1113 で地面が観察された場合に、後段で別実験として組む。
v1113 のコードに会話 / 単位 / 自我 / 応答の機能を入れない (測定器が壊れる原因)。

---

## 4. 過去失敗の教訓 (v1110-v1112)

| 教訓 | 出典 | 対策 |
|---|---|---|
| 痩せた phase 表現 (occupancy[64]) で測ると CID の本当の情報を捨てる | v1110-v1112 全体 | CID 真の 15 次元特性ベクトルで測る ([[code-a-blind-spots]] §11 関連) |
| 集計指標 (total_cooc) が処置 (bin shift) と数学的独立 = 測れない | v1112 Stage 1 main | 主指標は処置に sensitive な空間構造量 (diagonal、cosine sim) を選ぶ ([[code-a-blind-spots]] §11) |
| 慣性床 (time-shifted self_loop) は Atom 自身の慣性で対角が高くなる甘い対照 | v1112 Stage 1 main (2) 1/3 | 床は「無関係相手」(別系) または krandom 形式 ([[code-a-blind-spots]] §11) |
| 一様乱数 occ は実機 sparse occ と閾値挙動が桁違いで床機能しない | v1112 Stage 1 redo (precheck §2.4 FAIL) | 床の閾値挙動を実機と揃える、precheck で必ず点検 |
| null = 自身 shuffle は「皆同じだから似てる」を引き算できない | v1113 認識確認当初 | null = 別の無関係な seed の系を複数 ([[code-a-blind-spots]] §12) |

これら 5 教訓を全て v1113 に反映済み。

---

## 5. 実装の規律 (v1110-v1112 から引き継ぐ)

- **node ID 完全排他** (絶対): 別系を渡るのは node ID free な特性のみ
- **物理層 frozen**: 既存 developmental/ 等は触らない
- **書込先**: `unified/attention_center_prep/` 配下のみ
- **第三 ESDE = state なし観察体**: ただし v1113 は特性比較なので observer 不要 (両系を read-only で読むだけ)
- **両系を 1 bit も書き換えない**
- **自然進化** (注入なし、書き戻しなし)
- **factor なし**: 大小比較のみ
- **24 seeds は 1 バッチ** (smoke 後に 24 seeds に拡張)
- **smoke 後は止まって報告**
- **測定器が壊れているものを結果と呼ばない**: precheck PASS まで本実行に進まない
- **報告言葉縛り**: crown 禁止、観察事実のみ

---

## 6. やる順 (v1113)

| # | ステップ | 状態 |
|---|---|---|
| 1 | 全体の流れ整理 (本ファイル + 認識確認書) | ✓ 完了 (本コミット) |
| 2 | 実装 `v1113_cid_feature_resonance.py` | 着手 |
| 3 | 測定器点検 (§3.1-§3.4) を main 内で実装 | 同上 |
| 4 | Web Claude / Taka コードチェック (view) | OK 待ち |
| 5 | 本実行 (3 atom smoke、Pool(9) 1 Wave、推定 ~2 時間) | code OK 後 |
| 6 | 観察事実報告 (まっすぐ、crown なし) | 本実行後 |
| 7 | smoke OK なら 24 seeds 1 バッチ (Taka 規律) | 報告後 |

---

## 7. 関連ファイル

- 認識確認: `unified/attention_center_prep/v1113_cid_feature_check.md`
- 実装: `unified/attention_center_prep/v1113_cid_feature_resonance.py` (着手中)
- 本ファイル: `unified/attention_center_prep/v1113_overall_roadmap.md`
- 出力 (予定): `unified/attention_center_prep/run_v1113/`

---

## 8. 一文サマリ

v1113 系列ロードマップ (2026-06-04 整理 Code A / Web Claude / Taka 共有) — 全体構築 4 段階 (地面 = 別 seed 二系の CID に特に似てる組在るか v1113 今回 → 足場一個置く = 特に似てる組を Center が単位として束ねるか Stage 2 候補 → 床になる = 単位が溜まって Center が Atom 情報持つ異なる自我か Stage 3 候補 → 会話の芽 = 入力で Center がどの単位立てるかで応答向き変わるか Stage 4 候補)、v1113 = 地面確認のみ Stage 2 以降は別実験 crown 禁止 (Unified 成立 / 会話立った / 自我生まれた絶対書かない)、v1110-v1112 教訓 5 点反映 (痩せた phase 捨て CID 真の 15 次元 / 集計指標は処置 sensitive に / 床は無関係相手か krandom / 床閾値を実機と揃える / null は別 seed 別系を複数)、規律 (node ID 排他 絶対 / 物理層 frozen / 書込先 unified/attention_center_prep/ 配下 / state なし read-only / 1 bit も書き換えない / 自然進化注入なし / factor なし / 24 seeds 1 バッチ / smoke 後止まる / 壊れた測定器は結果でない / 報告言葉縛り)。
