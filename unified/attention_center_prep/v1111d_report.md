# v1111d 観察事実報告 — 出口分布で初の inversion (判定置かない)

**Date**: 2026-06-02
**Author**: Code A
**Status**: v1111d 完了、観察事実のみ、Web Claude / Taka 主題評価待ち
**親**: Web Claude v1111d 設計 (出口を phase 分布の形で運ぶ) + v1111c (出口一致率で 12 倍拡大、atom=42 単独)
**規律**: 判定置かない / 観察事実のみ / 主役 = atom 横断一貫性 (Web Claude §3)

---

## 0. 出口 (要点、判定置かない)

### v1111b/c/d 進展 (主要指標)

| 指標 | v1111b 修正 | v1111c | v1111d | 動き |
|---|---|---|---|---|
| §2.1 cos_mean (injected_other) | 1.074 | 1.001 | **0.965** | 一貫性に近づく |
| §2.1 cos_mean (shuffled_other) | 0.978 | 0.981 | **1.019** | 悪化 |
| §2.1 **injected < shuffled?** | ✗ | ✗ | **✓ 初の inversion** | **方向出始め** |
| §2.2 d_between real | 0.748 | 0.732 | 0.652 | 縮小 |
| §2.2 d_between shuffled | 0.743 | 0.671 | 0.646 | 同程度 |
| **§2.2 real - shuffled** | +0.005 | **+0.061** | **+0.006** | **後退** |
| §2.3 cos from self (shuffled) | 0.823 | 0.744 | **0.592** | self に大きく近づく |

→ **§2.1 主役で初の inversion** (real が shuffled より atom 横断一貫性に近い) ✓
→ §2.2 では v1111c の 12 倍拡大が後退、ほぼ同等に戻る
→ §2.3 で shuffled が self 床に強く近づく (random phase 分布も Atom 自身の決定に引っ張られる)

---

## 1. 実行結果

### 1.1 設定 + 時間

- 24 tasks、W_INJECT=2 固定、Pool(24) 1 Wave 並列、**815 秒 (13.6 分)**

### 1.2 §2.1 atom 横断一貫性 (主役)

| Other | injected_other cos_mean | shuffled_other cos_mean | inversion? |
|---|---|---|---|
| 100 | 0.970 | 1.083 | ✓ |
| 101 | **0.918** (min) | 1.002 | ✓ |
| 102 | 1.008 | 0.973 | ✗ |
| **mean** | **0.965** | **1.019** | **✓ (3 atom 共通方向)** |

→ Other=100, 101 で injected < shuffled (real の方が一貫性に近い)、Other=102 のみ逆。
→ 3 Other の平均で **injected_other 0.965 < shuffled_other 1.019 (初の inversion)**

### 1.3 §2.2 real vs shuffled (atom ごと)

| atom | injected_other d_between | shuffled_other d_between | diff |
|---|---|---|---|
| 42 | 0.480 | 0.620 | **-0.140** (real < shuffled、v1111c から反転) |
| **100** | **0.861** | 0.609 | **+0.252** (real > shuffled、大きく改善) |
| 200 | 0.616 | 0.709 | -0.093 (real < shuffled) |
| **3 atom 平均** | **0.652** | **0.646** | **+0.006** (ほぼ同等) |

→ v1111c (atom=42 で大、他で逆) から、v1111d (atom=100 で大、他で逆) に変化。
→ atom 依存性は残るが、優位 atom が変わった。

### 1.4 §2.3 self 床からの離れ方

| condition | cos from self mean ± std |
|---|---|
| injected_other | 0.650 ± 0.193 |
| shuffled_other | **0.592 ± 0.106** |

→ shuffled が self 床に大きく近づいた (v1111c の 0.744 → 0.592)。
→ 「random phase 分布も Atom 自身の決定に引っ張られる」(Atom の labels で励起度計算するため、随分シャッフルしても Atom 構造の決定が反映)

---

## 2. Web Claude §3 「3 条件」への応答 (v1111d)

| 条件 | 観察 | 成立? |
|---|---|---|
| **atom 横断一貫性 (主役)** | injected 0.965 < shuffled 1.019 (初の inversion) | **△ 方向出始め** (両者 cos ~1 で絶対値はまだ大) |
| real > shuffled | +0.006 (v1111c +0.061 から後退) | **✗** |
| self 床から特徴的に離れる | shuffled が self に近づく (0.744 → 0.592) | **✗ → △** (差縮小、方向同じ) |

**まとめ**: Web Claude §3 主役 §2.1 で **初の方向出始め**、ただし §2.2/§2.3 は条件不成立。

---

## 3. 観察事実の整理 (3 atom 共通 vs 差異)

### 3.1 3 atom 共通の足跡

1. **§2.1 で injected_other < shuffled_other の inversion** (3 Other 平均、初)
2. shuffled が self 床に近づく (atom 依存なし)

### 3.2 atom 別の差異

§2.2 d_between:
- atom=42: real << shuffled (v1111c から反転)
- atom=100: real > shuffled (大幅改善)
- atom=200: real < shuffled (v1111c と同じ方向)

→ v1111c の優位 atom (=42) から v1111d で別の優位 atom (=100) に変化。**「分布で運ぶと違う atom seed が反応する」**。

### 3.3 v1111b → v1111c → v1111d の 3 連続進展

| step | 改善 | 後退 |
|---|---|---|
| v1111b 計測修正 → v1111c | real - shuffled 12 倍拡大 | atom 横断一貫性なし |
| v1111c → v1111d | atom 横断一貫性 初の inversion | real - shuffled 後退 |

→ **「異なる指標が異なる版で出始める」、3 切り分け全条件成立は依然なし**

---

## 4. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ |
| 同型 + 物理切らない | ✓ |
| 書込 source_event 1 本 | ✓ (Atom 自身 label の core node) |
| トリガー固定しない | ✓ |
| **左右対称チェック (§2)** | ✓ 原理揃い + 粒度意図的非対称 |
| **固定値ゼロ (factor 不使用)** | ✓ |
| 指標 crown しない | ✓ (主役は §2.1 だが他指標も並列) |
| 単一 seed 絶対視しない | ✓ (3 atom 横断主役) |
| **判定置かない** | ✓ 「成功」「失敗」未使用、「方向出始め」「inversion」 |
| 新しい問い・観察軸足さない | ✓ |

---

## 5. Code A 観察 (判定でない、事実整理)

### 5.1 主要観察

1. **§2.1 主役で初の inversion** (injected_other 0.965 < shuffled_other 1.019)
2. **§2.2 で v1111c の 12 倍拡大が後退** (+0.061 → +0.006)
3. **§2.3 で shuffled が self 床に強く近づく** (0.744 → 0.592、Atom 自身の決定支配を示唆)
4. **優位 atom が v1111c (=42) → v1111d (=100) に変化** (分布で運ぶと反応する atom seed が変わる)

### 5.2 「全体の癖でゆるく繋ぐ」の Taka 整理への応答

Web Claude §0 「分布の形なら全体の癖が残る (物理層構造制約)」:
- §2.1 で initial signal が出始め: injected < shuffled の方向は 3 Other 平均で観察された
- ただし両者まだ cos ~1 (絶対値での一貫性ではない、相対比較で signal)
- Taka 整理「Atom はどの seed でもそれらしい形に収まる」: §2.3 で shuffled が self に近づくのがこの構造制約の発現と読める

### 5.3 解釈の留保

- §2.1 inversion は v1111d の核心的観察、ただし両者 cos ~1 で絶対的に一貫したわけではない
- §2.2 後退は「分布の和」が「個別 Other 間差を平均化」する効果の可能性
- §2.3 で shuffled が self に近づくのは「機構が Atom 構造優位」を示すかも

---

## 6. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | §2.1 で初の inversion (injected < shuffled) を「全体の癖で繋がった候補」と読むか、両者 cos ~1 で本質的にまだ届かないと読むか |
| ② | §2.2 が v1111c から後退したことを「分布の和が平均化効果で個別差を消した」と読むか、別解釈か |
| ③ | §2.3 で shuffled が self に近づくのを「Atom 構造制約が優位」(Taka「どの seed でもそれらしい形」) と読むか |
| ④ | 優位 atom が v1111c (=42) → v1111d (=100) に変化したのは「異なる粒度に異なる atom が反応」と読むか |
| ⑤ | 24 atom seeds で再現確認するか (3 切り分けの混合結果を統計的に整理)、別の粒度 (例: phase 分布 + E 強度マップで運ぶ等) か |

---

## 7. 出力ファイル

- `v1111d_check.md` (確認回答 + 左右対称 ✓)
- `v1111d.py` (実装、出口分布版)
- `v1111d_report.md` (本文書)
- `run_v1111d/consistency.parquet` (§2.1)
- `run_v1111d/between.parquet` (§2.2)
- `run_v1111d/self_floor.parquet` (§2.3)
- `run_v1111d/summary.json`

---

## 8. 一文サマリ

v1111d 観察事実 (Code A、2026-06-02、Web Claude v1111d 設計「出口を phase 分布の形で全体の癖でゆるく繋ぐ」、左右対称チェック §2 で原理揃い + 粒度意図的非対称 ✓、判定置かない) として、24 tasks Pool(24) × 815 秒 13.6 分実行で **Web Claude §3 主役 §2.1 atom 横断一貫性で初の inversion** (injected_other 0.965 < shuffled_other 1.019、3 Other 平均で 3 atom 共通方向、Other=100/101 で inversion・Other=102 のみ逆)、ただし §2.2 d_between real - shuffled が v1111c の +0.061 から +0.006 に後退 (atom 別では atom=42 real<<shuffled v1111c から反転 / atom=100 real>shuffled +0.252 大幅改善 / atom=200 real<shuffled 維持、優位 atom が v1111c の atom=42 から v1111d の atom=100 に変化)、§2.3 で shuffled が self 床に強く近づく (cos 0.744→0.592、random phase 分布も Atom 自身の決定に引っ張られる Taka「Atom はどの seed でもそれらしい形に収まる」物理層構造制約の発現候補)、v1111b/c/d 連続進展で異なる指標が異なる版で出始める (v1111c で §2.2 12 倍拡大 atom=42 / v1111d で §2.1 初 inversion atom=100)、3 切り分け全条件成立依然なし、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない + 左右対称チェック原理揃い粒度意図的非対称 + 固定値ゼロ + 指標 crown しない並列提示 + 単一 seed 絶対視しない 3 atom 横断主役 + 判定置かない方向出始め inversion で記述 + 新しい問い足さず)、判断 5 件 (§2.1 inversion を全体の癖繋がった候補か両者 cos~1 で本質まだ届かないか / §2.2 後退は分布の和が平均化効果か別解釈か / §2.3 shuffled が self に近づくは Atom 構造制約優位か / 優位 atom 変化は粒度ごと反応 atom 異なるか / 24 atom seeds 再現か別粒度 phase 分布 + E 強度マップで運ぶか)、書込み unified/attention_center_prep/ 配下のみ。

---

**v1111d end. Web Claude 機能設計 + Taka 主題評価待ち。**
