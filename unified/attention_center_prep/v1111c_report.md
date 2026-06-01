# v1111c 観察事実報告 — 出口を一致率に直した結果 (判定置かない)

**Date**: 2026-06-02
**Author**: Code A
**Status**: v1111c 完了、観察事実のみ、Web Claude / Taka 主題評価待ち
**親**: Web Claude v1111c 設計 (出口も一致率に、左右対称化) + v1111b 計測修正 (real ≈ shuffled、出口番号コピー原因)
**規律**: 判定置かない / 観察事実のみ / 3 atom 共通の足跡 / 左右対称チェック ✓

---

## 0. 出口 (要点、判定置かない)

### v1111b 計測修正 → v1111c 比較 (出口番号コピー → 一致率)

| 指標 | v1111b 計測修正 (番号コピー) | v1111c (一致率) | 変化 |
|---|---|---|---|
| §2.1 cos_mean (injected_other) | 1.074 | 1.001 | わずか減少 |
| **§2.2 d_between (real)** | 0.748 | **0.732** | -0.016 |
| **§2.2 d_between (shuffled)** | 0.743 | **0.671** | -0.072 |
| **§2.2 real - shuffled** | **+0.005** | **+0.061** | **12 倍に拡大** |
| §2.3 cos from self (real) | 0.674 | 0.642 | -0.032 |
| §2.3 cos from self (shuffled) | 0.823 | 0.744 | -0.079 |

→ **real - shuffled が 12 倍に拡大** = 出口を一致率にしたら「何かが少しは届いた」候補

### Web Claude §3 「3 条件」への応答

| 条件 | 期待 | v1111c 観察 | 成立? |
|---|---|---|---|
| atom 横断一貫性 | cos 小 (~0) | injected_other cos=1.001 / shuffled 0.981 | ✗ |
| **real > shuffled** | real > shuffled | **+0.061 (12x v1111b 修正)** | **△** (方向は出た、3 atom 共通でない) |
| self 床から特徴的に離れる | 各 Other 特徴 | shuffled が離れる (0.744 > 0.642) | ✗ |

→ 3 条件のうち **§2.2 だけ方向が出た**。他 2 条件は不成立。

---

## 1. 実行結果

### 1.1 設定 + 時間

- 24 tasks (3 atom × 8 conditions)、W_INJECT=2 固定
- Pool(24) 1 Wave 並列、総時間 **813 秒 (13.6 分)**

### 1.2 §2.1 atom 横断一貫性

| Other | injected_other cos_mean | shuffled_other cos_mean |
|---|---|---|
| 100 | 1.007 | 0.867 |
| 101 | 0.997 | 1.048 |
| 102 | 0.998 | 1.029 |
| **mean** | **1.001** | **0.981** |

→ 両 conditions で cos ~1、**atom 横断一貫性なし** (v1111b 計測修正と同じ)

### 1.3 §2.2 real vs shuffled (atom ごと)

| atom | injected_other d_between | shuffled_other d_between | diff |
|---|---|---|---|
| **42** | **0.876** | **0.518** | **+0.358** (real > shuffled) |
| 100 | 0.626 | 0.667 | -0.041 (符号わずか逆) |
| 200 | 0.693 | 0.827 | -0.134 (符号逆) |
| **3 atom 平均** | **0.732** | **0.671** | **+0.061** |

→ atom=42 で大きく real > shuffled、atom=100/200 で逆向き。
3 atom 平均では real > shuffled だが、**seed 依存性残る**。

### 1.4 §2.3 self 床からの離れ方

| condition | cos from self mean ± std |
|---|---|
| injected_other | **0.642 ± 0.164** |
| shuffled_other | **0.744 ± 0.210** |

→ shuffled の方が self 床から離れる (v1111b 計測修正と同じ方向)。
v1111b 修正と比較: real 0.674 → 0.642、shuffled 0.823 → 0.744 (両者 self に近づいた)

---

## 2. 観察事実の整理 (3 atom 共通 vs 差異)

### 2.1 3 atom 共通

1. **両 conditions で cos ~1** = atom 横断一貫性なし
2. shuffled が self 床から離れる方向は維持

### 2.2 atom 別の差異

- atom=42: real >> shuffled (+0.358) — 出口直しで「効いた」候補
- atom=100/200: real ≈/< shuffled — 出口直しの効果なし

### 2.3 v1111b 計測修正 → v1111c の変化

- real - shuffled が **+0.005 → +0.061 (12 倍)** に拡大
- §2.3 で両 conditions が self 床に近づいた (real 0.674→0.642、shuffled 0.823→0.744)
- → 出口を一致率にしたことで shuffled の「中身ゼロ」が self に近づいた (ランダム phase も Atom 自身の label を選ぶ機構を通るため)

---

## 3. 解釈 (Code A 判定置かない、事実整理)

### 3.1 出口番号コピー → 一致率の効果

- real - shuffled の差が 12 倍に拡大 → **「番号コピーが原因だった」候補が部分的に支持される**
- ただし atom 共通で出たわけではない (atom=42 のみ)
- 「繋がる候補」3 条件のうち 1 つだけ方向が出た

### 3.2 残る課題

1. **atom 横断一貫性なし** (cos ~1) は維持 → Other の中身が「向き」として atom 共通の署名を持たない
2. **shuffled が self 床から離れる** = 「Other 中身なし」の方が方向違いになる構造
3. **atom 依存性大** (atom=42 で +0.358 / atom=200 で -0.134) → 結果の seed 依存性

### 3.3 解釈の留保

- 「出口直しで届いた」と言える条件は §2.2 の 3 atom 平均 real > shuffled のみ
- それも 1 atom (=42) の大きな差が平均を持ち上げている (atom=100/200 では逆)
- v1111b 計測修正の「Other 中身署名観察されず」は **強く変わらず**

---

## 4. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ |
| 同型 + 物理切らない | ✓ |
| 書込 source_event 1 本 | ✓ |
| トリガー固定しない | ✓ |
| **左右対称チェック (§2)** | ✓ Code A 認識確認で全項目「揃う」 |
| 固定値ゼロ (factor 不使用) | ✓ |
| 指標 crown しない | ✓ |
| 単一 seed 絶対視しない | ✓ (atom=42 のみで結論しない) |
| 判定置かない | ✓ |
| 新しい問い足さない | ✓ |

---

## 5. Code A 観察 (判定でない、事実整理)

### 5.1 主要観察

1. **出口を一致率に直した効果**: real - shuffled +0.005 → +0.061 (12 倍に拡大)
2. **atom=42 で大きな real > shuffled** (+0.358)、atom=100/200 で逆方向
3. **3 atom 共通の足跡**: atom 横断一貫性は依然なし、shuffled が self 床から離れる方向は維持
4. **左右対称化後でも「繋がる候補 3 条件」すべて成立せず**

### 5.2 Web Claude §3 結論への応答

「繋がる候補 = atom 横断一貫 + real > shuffled + self 床から特徴的に離れる」

- 3 条件中 1 条件 (§2.2) は方向が出たが、3 atom 共通でない
- 他 2 条件は v1111b 計測修正と同じく不成立
- → 「観察されなかった」(条件付きで方向は出始め)

### 5.3 v1111b → v1111b 計測修正 → v1111c の 3 連続観察

| step | 結果 |
|---|---|
| v1111b (δ_repeat 不適切) | nesting 0/3 (計測不備) |
| v1111b 計測修正 (タイミング固定) | 3 条件すべて不成立 |
| v1111c (出口左右対称) | §2.2 だけ方向出るが atom 依存、他 2 条件不成立 |

3 回連続で「Other 中身の独立署名」は決定的に観察されず。

---

## 6. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | real - shuffled が 12 倍に拡大したことを「部分的成立」と読むか、「依然不成立」と読むか |
| ② | atom=42 のみで大きく real > shuffled、atom=100/200 で逆方向の seed 依存性をどう扱うか |
| ③ | atom 横断一貫性 cos ~1 が v1111b 計測修正 → v1111c で変わらないことから、phase 平均化 (テーマ集約) が情報を捨てている可能性を疑うか |
| ④ | shuffled が self 床から離れる現象を「Atom 自身の決定が中身よりも支配的」と読むか |
| ⑤ | 24 atom seeds で再現確認するか、別の入口経路 (例: phase 群の平均でなく分布で運ぶ) を検討するか |

---

## 7. 出力ファイル

- `v1111c_check.md` (確認回答 + 左右対称チェック ✓)
- `v1111c.py` (実装)
- `v1111c_report.md` (本文書)
- `run_v1111c/consistency.parquet` (§2.1)
- `run_v1111c/between.parquet` (§2.2)
- `run_v1111c/self_floor.parquet` (§2.3)
- `run_v1111c/summary.json`

---

## 8. 一文サマリ

v1111c 観察事実 (Code A、2026-06-02、Web Claude v1111c 設計「出口も一致率に、左右対称化」、判定置かない) として、左右対称チェック §2 全項目揃う Code A 認識確認後、24 tasks Pool(24) × 813 秒 13.6 分実行で v1111b 計測修正 (出口番号コピー) との比較は §2.1 cos_mean injected 1.074→1.001 / shuffled 0.978→0.981、§2.2 d_between real 0.748→0.732 / shuffled 0.743→0.671 で **real - shuffled が +0.005→+0.061 で 12 倍に拡大**、§2.3 cos from self real 0.674→0.642 / shuffled 0.823→0.744 (両者 self に近づく)、Web Claude §3 3 条件中 §2.2 だけ方向出るが atom 別では atom=42 +0.358 (real >> shuffled) / atom=100 -0.041 / atom=200 -0.134 で seed 依存性大、他 2 条件不成立 (atom 横断一貫性 cos ~1、shuffled が self 床から離れる方向)、解釈 (出口番号コピーが部分原因候補、ただし「繋がる候補」3 条件すべて成立せず、atom=42 のみで平均が持ち上がる)、v1111b→v1111b 計測修正→v1111c の 3 連続観察で Other 中身独立署名は決定的に観察されず ただし v1111c で初めて real - shuffled の方向が見えた、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない + 左右対称チェック + 固定値ゼロ + 指標 crown しない + 単一 seed 絶対視しない + 判定置かない + 新しい問い足さず)、判断 5 件 (real-shuffled 12 倍拡大を部分成立か依然不成立か / atom 依存性 atom=42 vs 100/200 の扱い / atom 横断一貫性不変は phase 平均化が情報捨てている可能性 / shuffled が self 床から離れるは Atom 自身決定支配的か / 24 atom seeds 再現か別入口経路 phase 群分布で運ぶか)、書込み unified/attention_center_prep/ 配下のみ。

---

**v1111c end. Web Claude 機能設計 + Taka 主題評価待ち。**
