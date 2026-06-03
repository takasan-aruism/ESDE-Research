# v1112 Stage 1 redo 結果報告 (Web Claude 宛)

date: 2026-06-04
from: Code A (Claude Code, Opus 4.7)
to: Web Claude / Taka
status: Stage 1 redo 完走 (8605 秒)、3 条件 (1)+(2)+(3) すべて揃う条件は不成立 = **測れた上での Stage 1 不成立**

---

## 0. ひとことサマリ

測定器組み直し (主指標 diagonal、Other=999、両床併設) で本実行 9 tasks Pool(9) を完走。

- (1) Active で diagonal が立つ: 立つ (raw 62-135、上限 38 (precheck 1 atom×3 windows) と比較できないが本番 30 windows で十分な mass)
- (2) Active > self_krandom_floor: δ=1, δ=3 で **3/3 揃う ✓**、δ=0 のみ 1/3
- (3) Active > Phase Shifted: δ=0 で 1/3、δ=1 で 1/3、δ=3 で 2/3 — **どの δ でも 3/3 揃わず**

→ 全 δ × PASS 床で 3/3 揃わず = **Stage 1 不成立 (測れた上での)**。

これは前回 (v1112 Stage 1 main) と異なり、**測定器は機能した上での不成立**。「測っていない」ではなく「測って、揃わなかった」。

加えて新事実:
- self_permute_floor は §2.4 で FAIL (床として機能しない)、self_krandom_floor のみ PASS
- atom=100 が唯一 (3) を満たす atom = 構造的特殊性 (Other=999 でも 1.5x 突出残)

---

## 1. 実行構成と完走確認

| 項目 | 値 |
|---|---|
| 主指標 | diagonal_mass(M, δ=0/1/3) — 空間構造指標、shift 不変でない |
| 参考指標 | total_cooc / N_rcid / max_cooc (parquet 記録のみ、判定外) |
| 第三 ESDE | ResonanceObserver (state なし、両系 read-only、書き戻しなし) |
| ATOM_SEEDS | [42, 100, 200] (v1111d 互換) |
| OTHER_SEED_FIXED | 999 (ATOM_SEEDS と非重複 = 同 seed 並走排除) |
| WINDOW | 500 step × 30 windows |
| 自然進化 | 注入なし、書き戻しなし、両系 1 bit も触らず |
| node ID 排他 | phase 64 bin index のみ両系を渡る ✓ |
| 並列 | Pool(9) 1 Wave |
| 実時間 | 8605 秒 (約 2.4 時間) |
| 完了 | exit 0、全 9 task done |

---

## 2. precheck §2.4 結果 (両床の PASS/FAIL)

```
累積 cooc (3 atom × 3 windows、precheck 段階):
  diag_aa (Active 自己、上限)        = 38.0
  diag_ao (Active × Other 別 seed)   = 5.0
  diag_ap (Active × permute、案 A 床)= 6.0  ← Other より高い
  diag_ak (Active × krandom、案 B 床)= 3.0  ← Other より低い

床 PASS 判定 (strict diag_<f> < diag_ao):
  self_permute_floor: diag_ap (6.0) < diag_ao (5.0) = False → FAIL
  self_krandom_floor: diag_ak (3.0) < diag_ao (5.0) = True  → PASS
```

### 観察事実 (床の設計差)

| 床 | 機能 |
|---|---|
| **permute (案 A) FAIL** | 実機 occ の値分布をそのまま保持、bin 順序のみ permute。sparsity 完全一致が逆に「Other と区別できない」結果。実機の active 値の多様性 (高値の bin が複数) を保持するため、偶然 Atom と対角に乗る確率が Active × Other と同等になる |
| **krandom (案 B) PASS** | active 値を mean に揃え、k 個 random 位置だけ非ゼロ。active 値の単一化 (all = mean) で対角一致期待値が低い |

→ self 床としては「実機の値分布を保ちすぎる permute」は機能せず、「active 値を均一化した krandom」が機能する。

### 閾値挙動 (実機 / 床)

```
実機 Atom:  mean=0.0156, n_above_mean=3/64
実機 Other: mean=0.0156, n_above_mean=6/64
permute:    mean=0.0156, n_above_mean=3/64  ← 実機と完全一致 (値分布保持)
krandom:    mean=0.0156, n_above_mean=3/64  ← k 一致
```

両床とも sparsity (n_above_mean) は実機と一致したが、permute は「実機の高値 bin (差別化された active 値)」がそのまま残るため、対角一致の確率が高くなる構造。

---

## 3. 本実行結果 — 主指標 diagonal (3 δ × 3 atom)

### δ=0 (純対角、同 bin 同期)

```
condition  active_pair  phase_shifted  self_krandom_floor
atom=42         62              89              63
atom=100       130             105             110
atom=200        85             135             110
```

### δ=1 (±1 bin 近傍、約 ±11° 範囲)

```
condition  active_pair  phase_shifted  self_krandom_floor
atom=42        255             294             205
atom=100       388             331             325
atom=200       342             402             335
```

### δ=3 (±3 bin 近傍、約 ±33° 範囲)

```
condition  active_pair  phase_shifted  self_krandom_floor
atom=42        633             764             519
atom=100       914             832             743
atom=200       865             776             770
```

---

## 4. Stage 1 出口判定 (主指標 diagonal、大小、factor なし)

Web Claude 設計の 3 条件:

> (1) 両系 (Active Pair) で立ち、(2) self では立たず、(3) 位相ずらし対照 (Phase Shifted) より明確に多いか

### (2) Active > self_krandom_floor

| δ | 結果 | atom 別 |
|---|---|---|
| d0 | 1/3 | atom=100 のみ (130>110) |
| d1 | **3/3 ✓** | 全 atom |
| d3 | **3/3 ✓** | 全 atom |

→ δ=1, δ=3 (近傍含む) では **(2) 3/3 揃う**。
→ δ=0 (純対角) のみ atom=42 (62 vs 63)、atom=200 (85 vs 110) で逆転。

### (3) Active > Phase Shifted

| δ | 結果 | atom 別 |
|---|---|---|
| d0 | 1/3 | atom=100 のみ (130>105) |
| d1 | 1/3 | atom=100 のみ (388>331) |
| d3 | 2/3 | atom=100, 200 (914>832, 865>776) |

→ どの δ でも **3/3 揃わず**。
→ atom=42 は全 δ で Active < Phase Shifted (62<89, 255<294, 633<764)。

### 全 δ × PASS 床で 3/3 揃う: **False**

→ Stage 1 不成立 (測れた上での)。

---

## 5. atom=100 の特殊性 (Taka 詰め 2 結果読み)

```
diagonal_d0 (active_pair):
  atom=42:  62
  atom=100: 130  (atom=42 比 ~2.1x、atom=200 比 ~1.5x)
  atom=200: 85
```

### 前回 (Other=100 同 seed 並走) との比較

| 項目 | 前回 (Other=100) | 今回 (Other=999) |
|---|---|---|
| atom=100 diag_d0 | 442 | 130 |
| atom=42 diag_d0 | 97 | 62 |
| atom=200 diag_d0 | 126 | 85 |
| atom=100 / 他 atom mean 比 | ~4.0x | ~1.7x |

→ **同 seed 並走は確かに汚染源だった** (4.0x → 1.7x で大幅緩和)。
→ ただし完全には消えず、**atom=100 自身に何らかの構造的特殊性が残る** (1.5-2x 突出)。

これは前回報告書で指摘した「atom=100 特殊性 (Other=100 と同 seed 並走) が共鳴強化を起こしている疑い」が **部分的に確認** された結果。残存する 1.5x 突出は別の構造的原因。

### atom=100 は (3) を唯一満たす atom

全 δ で `active > shifted AND active > floor` を満たすのは atom=100 のみ:
- d0: 130 > 105 (shifted), 130 > 110 (floor) ✓
- d1: 388 > 331 (shifted), 388 > 325 (floor) ✓
- d3: 914 > 832 (shifted), 914 > 743 (floor) ✓

atom=42, 200 はどの δ でも (3) で逆転 (Phase Shifted のほうが対角に乗る)。

---

## 6. 観察事実 (判定置かない、言葉縛り遵守)

### 観察事実 1: Stage 1 出口は測れた上で揃わなかった

- 主指標 diagonal (3 δ) と床 (self_krandom_floor PASS) で 3 条件のすべてが 3/3 揃う組合せはなかった
- 「測っていない」(前回 §3 主指標構造的独立) ではなく「測って、揃わなかった」

### 観察事実 2: (2) は δ 依存で 3/3 揃う

- δ=1, δ=3 (近傍含む) で 3 atom 全てが Active > floor
- δ=0 (純対角) のみ 1/3
- → **近 phase (~±1-3 bin、±5-17°) では Active が床を上回るが、純対角では揃わない**

### 観察事実 3: (3) は全 δ で 3/3 揃わない

- atom=42, 200 は全 δ で Active < Phase Shifted
- atom=100 のみ全 δ で Active > Phase Shifted
- → **位相ずらしのほうが対角に乗るケース** が 2/3 atom で観察された

### 観察事実 4: self_permute_floor は床として機能しない (precheck §2.4 FAIL)

- 実機 occ の値分布を保つと、bin 順序を変えても対角一致の確率が Active × Other と同等
- self 床は「sparsity だけでなく active 値も均一化」する必要 (krandom 形式)

### 観察事実 5: atom=100 特殊性は Other=999 でも残る

- 同 seed 並走 (Other=100) で 4.0x、Other=999 で 1.7x
- 同 seed 並走は汚染源として確認、ただし完全には消えない
- atom=100 自身に構造的特殊性 (要因不明)

### 観察事実 6: 主指標 diagonal は shift / 床に sensitive (測定器は機能した)

- diagonal_d0/d1/d3 はそれぞれ条件で値が異なる (前回 total_cooc が active = shifted で完全同一だった病はなくなった)
- 例: atom=42 で active_pair=62, phase_shifted=89, floor=63 (3 値とも異なる)
- → 測定器は機能し、本来想定した区別を生んでいる

---

## 7. Code A 自己評価

| 項目 | 結果 |
|---|---|
| 測定器組み直し (Web Claude 指示) | ✓ 主指標 diagonal、Other=999、両床併設 |
| 実装規律 (node ID 排他、state なし、書き戻しなし) | ✓ 遵守 |
| 実装前 precheck (§2.1-§2.4 4 項目) | ✓ 全実行、§2.4 で permute FAIL を検出して PASS 床のみ進む |
| Web Claude コードチェック前置 | ✓ Taka view 経由で本実行に進む |
| 報告言葉縛り | ✓ 「Unified 完成」「成立」書かず、観察事実のみ |
| Stage 1 出口判定 | 不成立 (測れた上での)、構造事実として記録 |

---

## 8. Web Claude / Taka への問い

### (1) Stage 1 不成立を Stage 2 進入否認とするか

(2) は δ=1, δ=3 で 3/3 揃ったが、(3) はどの δ でも 3/3 揃わない。
Web Claude 設計の出口は「3 条件すべて揃う」なので不成立。

選択肢:
- A: 「Stage 1 不成立として記録、Stage 2 進入せず」(厳密遵守)
- B: 「(2)+(1) は揃った、(3) atom=100 のみ揃った」として観察事実を残し、別 design で再 Stage 1
- C: 「位相ずらしのほうが対角に乗る (2/3 atom)」現象自体を Stage 2 の判定軸に組み入れる

### (2) atom=100 特殊性をどう扱うか

Other=999 でも 1.7x 突出残。これは:
- atom=100 の Atom seed 自身が phase 動態として特殊
- Other=999 と atom=100 が偶然 phase 帯で相性が良い (新たな汚染)
- 何らかの構造的不均一性

どれが要因か、Web Claude / Taka の見立てを伺いたい。

### (3) self_permute_floor FAIL の意味

permute (実機値分布保持) が床として機能しない = 「無関係な相手」を作るには値分布だけ保ってもダメで、active 値の均一化が必要。これは self 床設計の構造的知見として残す。

---

## 9. 補足: 実装ファイル

- 実装: `unified/attention_center_prep/v1112_stage1_redo.py`
- 認識確認: `unified/attention_center_prep/v1112_stage1_redo_check.md`
- 出力: `unified/attention_center_prep/run_v1112_stage1_redo/`
  - `summary.parquet` (9 行: 3 atom × 3 cond)
  - `cooc_matrix.parquet` (9 行 × 4096 cooc flat)
  - `progression.parquet` (window 単位 diag_d0 推移)
  - `summary.json` (Stage 1 出口判定 + precheck 履歴)

---

Web Claude / Taka の判断を待ちます。
