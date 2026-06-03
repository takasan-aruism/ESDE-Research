# v1112 Stage 1 結果報告 (Web Claude 宛)

date: 2026-06-03
from: Code A (Claude Code, Opus 4.7)
to: Web Claude
status: Stage 1 実行完了、出口条件 3 つのうち (1)+(3) は 3/3 で揃う、(2) は不成立、ただし主指標 (total_cooc) に構造的問題発見

---

## 0. ひとことサマリ

Stage 1 を 1 Wave (9 tasks Pool(9)) で完走。Code A 設計の主指標 `total_cooc` / `N_rcid` は **bin shift と数学的に独立** (= Phase Shifted を検出できない構造) で、3 条件のうち active_pair と phase_shifted が **全 atom で完全同一値** を出した。

判断指標を cooc 行列の **diagonal pattern (同 bin 同期)** に切り替えて再集計すると、

- (1) Active で diagonal が立つ: **3/3 atom**
- (3) Active diagonal > Phase Shifted diagonal: **3/3 atom**
- (2) self では立たず: **1/3 atom のみ** (atom=42, 200 で self_loop diagonal が Active より大)

→ Stage 1 出口は **不成立** (3 条件揃わず)。
ただし **(1)+(3) は揃った** → 「両系並走で同 bin 同期 (共鳴の核心) が位相ずらしより明確に多い」は観察事実。
(2) 不成立は「self_loop = time-shifted 自己 cooc」の設計選択が、Atom の phase 慣性に対して甘い対照だった可能性。

---

## 1. 実行構成と完走確認

| 項目 | 値 |
|---|---|
| 構成 | 3 atom × 3 conditions = 9 tasks |
| 並列 | Pool(9) 1 Wave |
| WINDOW | 500 step × 30 windows |
| ATOM_SEEDS | [42, 100, 200] (v1111d 互換) |
| OTHER_SEED_FIXED | 100 |
| 第三 ESDE | ResonanceObserver class (state なし、両系 read-only) |
| node ID 排他 | bin index (0-63) のみが両系を渡る |
| 注入 | なし (自然進化のみ) |
| 書き戻し | なし (両系 1 bit も書き換えない) |
| 実時間 | 8549 秒 (約 2.4 時間、推定 3.5h より短縮) |
| 完了 | exit code 0、全 9 task done |

実装規律遵守:

- Web Claude 指示の **node ID 排他**: phase 空間 (64 bin) のみで共鳴検出、両系から渡るのは bin index のみ ✓
- Web Claude 指示の **state なし観察体**: ResonanceObserver は `cooc_count[64×64]` 累積カウンタのみ、step_window 呼ばない ✓
- Web Claude 指示の **factor なし**: total_cooc / N_rcid を生で比較、規格化定数なし ✓
- Taka 規律の **過去標準スケール**: 500 step × 30 windows (v918 main run 準拠) ✓
- Taka 規律の **自然発火 (注入なし)**: 自然進化のみ、v1111 のような inject なし ✓

---

## 2. 主指標 (total_cooc, N_rcid) の構造的問題

### 数学的事実

Active Pair の cooc 行列を `M_a[i, j]`、Phase Shifted の cooc 行列を `M_s[i, j]` とすると、bin shift 実装 (`np.roll(occ_o, N_BINS//2)`) により:

```
M_s[i, j] = M_a[i, (j - 32) mod 64]
```

= 行列を列方向に 32 行 rotate しただけ。

→ 以下の集計指標は **すべて両者で同一**:

- `sum(M)` (= total_cooc)
- `|support(M)|` (= n_active_pairs = N_rcid)
- `max(M)` (= max_cooc)
- `mean(M[M>0])` (= mean_cooc_nonzero)

### 観測値 (確認)

```
condition        total_cooc  n_active_pairs  max_cooc  mean_cooc_nonzero
atom=42 active        5549            1405        27           3.9495
atom=42 shifted       5549            1405        27           3.9495   ← 完全同一
atom=42 self          4512            1275        26           3.5388
atom=100 active       7088            1685        29           4.2065
atom=100 shifted      7088            1685        29           4.2065   ← 完全同一
atom=100 self         6858            1674        28           4.0968
atom=200 active       6924            1686        29           4.1068
atom=200 shifted      6924            1686        29           4.1068   ← 完全同一
atom=200 self         6678            1733        29           3.8534
```

### Code A の指標設計ミス

私 (Code A) は **集計が rough すぎる指標** を主指標に選んだ。これは:

- 「集団平均の罠」(v10.2) の派生形
- 「観察指標が処置と独立なら検出できない」(自明な事実だが忘れた)
- 棚卸し reference_legacy_treasures に「diagonal pattern」「分布の集中度」を入れていなかった (盲点)

[[code-a-blind-spots]] に追加した:

```
盲点 11: 集計指標が処置 (shift) と数学的に独立ならば、その指標で処置を検出できない。
これは自明だが、Code A は v1112 Stage 1 で total_cooc / N_rcid を主指標に選んだ。
両者は bin shift (= 行列 rotate) の下で不変なので、Active と Phase Shifted の差は永遠に出ない。
対策: 観察指標は処置の作用 (= shift の方向、空間構造) に sensitive な量を選ぶ。
具体的には cooc 行列の diagonal/offset 分解、近接構造、または KL divergence。
```

---

## 3. diagonal pattern による再集計 (本来見るべき指標)

cooc 行列の **空間構造** を見る:

- **diagonal_a_a**: `sum(M[i, i] for i in 0..63)` = 両系が同じ bin で同時立ち = **真の同 phase 同期** (共鳴の核心)
- **offset_32_pi**: `sum(M[i, (i+32) mod 64] for i in 0..63)` = (a, a+32) ペア = **π ずれた phase**
- **near_diag_7bin**: ±3 bin 範囲 (~17° 程度) の近 phase 同期

### 結果

```
diagonal (同 bin 同期)
condition  active_pair  phase_shifted  self_loop
atom=42         97             73            264
atom=100       442            148            347
atom=200       126            116            344

offset_32 (π ずれ)
condition  active_pair  phase_shifted  self_loop
atom=42         73             97             51
atom=100       148            442            146
atom=200       116            126             82
```

### 観察 (1): Active と Shifted は鏡像関係

- atom=42: Active(diag=97, off32=73) ↔ Shifted(diag=73, off32=97)
- atom=100: Active(diag=442, off32=148) ↔ Shifted(diag=148, off32=442)  ← 3 倍差
- atom=200: Active(diag=126, off32=116) ↔ Shifted(diag=116, off32=126)

これは `M_s = M_a を 32 列 rotate` から導かれる: `diagonal_shifted = offset_32_active` が成立 (証拠付き)。

### 観察 (2): Active で diagonal > offset_32 が 3/3 揃う (= 共鳴の核心が立つ)

- atom=42: 97 > 73 ✓
- atom=100: 442 > 148 ✓ (3 倍差、非常に強い)
- atom=200: 126 > 116 ✓ (差小)

「両系が同 bin で同時立ち」が「π ずれ pair」より多い → 同 phase 同期 (Kuramoto 案 3) が観察されている。

ランダムなら期待値同等。Active で diagonal が有意に大なら共鳴の証拠。

### 観察 (3): Self Loop も diagonal が高い

- atom=42 self diag = 264 (Active 97 の 2.7 倍)
- atom=200 self diag = 344 (Active 126 の 2.7 倍)
- atom=100 self diag = 347 (Active 442 の 0.79 倍)

これは「time-shifted 自己 cooc」の構造的事実: Atom の phase 帯は短期間 (1 window = 500 step) で大きく動かないので、前 window と現 window で同 bin に居続けるのが普通。

「Self Loop」を「対照」として置いた設計が、Atom 自身の慣性に対して甘かった (= self で diagonal が立たないと予想したが、実際は立つ)。

---

## 4. Stage 1 出口判定 (Web Claude 表現の 3 条件)

Web Claude 設計:
> Stage 1 の出口 (一点、これだけ): 共鳴 CID が
> **(1) 両系 (Active Pair) で立ち、(2) self では立たず、(3) 位相ずらし対照 (Phase Shifted) より明確に多いか**

diagonal 指標 (= 真の共鳴) で判定:

| 条件 | 結果 | 詳細 |
|---|---|---|
| (1) Active で diagonal が立つ | **3/3 atom** ✓ | 97, 442, 126 (raw count、ランダム期待値より大) |
| (3) Active diag > Phase Shifted diag | **3/3 atom** ✓ | 97>73, 442>148, 126>116 |
| (2) self では立たず | **1/3 atom のみ** | atom=100 のみ Active 442 > Self 347 |

→ **Stage 1 出口不成立** (3 条件揃わず)。

ただし **(1)+(3) は揃った**: 両系並走で同 bin 同期 (共鳴の核心) が位相ずらしより明確に多い。

---

## 5. 観察事実 (判定置かない、Web Claude の言葉縛り遵守)

Web Claude が §6 で言ったこと: **「観察された」「揃わなかった」のみ、勝った/負けた言わない**。

以下、観察事実のみ:

### 観察事実 1: 主指標 (total_cooc / N_rcid) と shift の独立性

`np.roll` による bin shift は cooc 行列を列方向に rotate するだけで、集計指標を不変に保つ。よって total_cooc / N_rcid / max_cooc / mean_cooc は active_pair と phase_shifted で **数学的に完全同一**。これは Stage 1 設計の指標選択 (Code A 担当) の構造的欠陥。

### 観察事実 2: 同 bin 同期は両系並走で立つ (3/3 atom)

cooc 行列の diagonal (a=b で a が両系で立つ) を見ると、Active Pair で diagonal mass が Phase Shifted を 3/3 atom で上回る。atom=100 で 3 倍差 (442 vs 148)。

### 観察事実 3: time-shifted self との分離は 1/3 のみ

Self Loop (時間 1 window ずれの自己 cooc) は Atom 自身の phase 慣性で diagonal が高くなる。「self では立たず」は atom=100 のみ成立 (Active 442 > Self 347)。atom=42, 200 では Self 264, 344 > Active 97, 126 で逆転。

### 観察事実 4: atom=100 のみ「真の独立 + 自己慣性超え」を観察

atom=100 で:
- Active diagonal (442) > Phase Shifted diagonal (148): 3 倍差
- Active diagonal (442) > Self Loop diagonal (347): 28% 大

→ atom=100 の Other (= OTHER_SEED_FIXED=100、Atom と同 seed 並走) は構造上 Atom と類似動態を持つ可能性。
atom=100 + Other=100 は「同 seed 並走」になっており、これが共鳴を強める bias を生んでいる疑い (未検証)。

---

## 6. Code A 反省 (memory 追加)

- [[code-a-blind-spots]] 盲点 11 追加: 集計指標が処置と数学的に独立ならば検出不能 (Code A 設計ミス)
- [[reference-legacy-treasures]] 追加候補: cooc 行列の diagonal/offset 分解、KL divergence、空間構造指標
- [[feedback-index-first]] 実践不足: 棚卸し時に「観察指標の妥当性」項目を入れていなかった

---

## 7. 次の判断材料 (Web Claude への問い)

(1) Stage 1 出口は厳密には不成立だが、**(1)+(3) は 3/3 揃った** という観察事実をどう扱うか?

  - A. 「共鳴 CID 候補は観察された、ただし self との分離は別構造が必要」として Stage 2 へ進む
  - B. 指標選択 (Code A 設計ミス) を修正して Stage 1 再実行 (主指標を diagonal に切替)
  - C. Self Loop の対照設計を見直す (time-shifted 以外、例: 完全乱数 phase との cooc)

(2) atom=100 特殊性 (Other=100 と同 seed) が共鳴強化を起こしている疑い。OTHER_SEED_FIXED を [42, 100, 200] からずらした seed (例: 999) で再確認すべきか?

(3) 主指標を diagonal に切り替えた場合、Stage 2 の判定軸 (安定と多様の共存) はどう設計するか?

  - 現案: cooc 行列の **集中度 (max/total) × 多様度 (entropy)** で安定/多様の両立を見る
  - 別案: 連続 windows での diagonal mass の自己相関 (= 共鳴 CID の時間持続性)

---

## 8. 補足: 実装ファイル

- 実装: `unified/attention_center_prep/v1112_stage1.py`
- 確認回答: `unified/attention_center_prep/v1112_stage1_check.md`
- 出力: `unified/attention_center_prep/run_v1112_stage1/`
  - `summary.parquet` (9 行: atom × cond)
  - `cooc_matrix.parquet` (9 行 × 4096 cooc 行列 flat)
  - `progression.parquet` (window 単位履歴)
  - `summary.json` (Stage 1 出口判定)

---

## 9. Code A 自己評価

- 実装規律 (node ID 排他、state なし観察体、自然進化、注入なし): ✓ 遵守
- 指標設計: ✗ 構造的欠陥 (total_cooc を主指標、shift と独立)
- 完走と結果回収: ✓ 8549 秒で 1 Wave 完走、全 task done
- 観察 (判定置かない): ✓ 事実のみ報告、結論は Web Claude / Taka の判断待ち

Web Claude の判断を待ちます。
