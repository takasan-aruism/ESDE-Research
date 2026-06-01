# v1111b 計測修正 観察事実報告 (判定置かない)

**Date**: 2026-06-02
**Author**: Code A
**Status**: v1111b 計測修正完了、観察事実のみ、Web Claude 機能設計 + Taka 主題評価待ち
**親**: Web Claude v1111b 計測修正設計 (δ_repeat 捨て、系が出す参照点で測り直す)
**規律**: 判定置かない / 観察事実のみ / 3 atom 共通の足跡 / 系の参照点のみ (固定値ゼロ)

---

## 0. 出口 (要点、判定置かない)

### Web Claude §3 「3 切り分け」すべて **Other 中身署名は観察されず**

| 切り分け | 観察 | 結論方向 |
|---|---|---|
| §2.1 atom 横断一貫性 | injected_other cos mean = **1.074** / shuffled = 0.978 (両者 cos ~1) | **一貫性なし** |
| §2.2 real vs shuffled d_between | real 0.748 / shuffled 0.743 (差 +0.005) | **同等** (real ≈ shuffled) |
| §2.3 self 床からの離れ方 | real 0.674 / shuffled 0.823 (shuffled の方が離れる) | **特徴的でない** |

→ Web Claude §3「繋がる候補」3 条件すべて不成立。
「**出口層の偏りが Other の中身を反映する署名は観察されなかった**」が現状の結論。

---

## 1. 実行結果

### 1.1 設定 + 時間

- 24 unique tasks (3 atom × 8 conditions)
- W_INJECT=2 固定 (δ_repeat 作らない)
- Pool(24) 1 Wave 並列、総時間 **800 秒 (13.3 分)**

### 1.2 §2.1 atom 横断一貫性 (Other ごと、V = ΔP_other - ΔP_self の atom 間 cos 距離)

**cos 小 → atom 横断で向きが一貫 = Other 中身署名**

| 種類 | Other | cos mean | cos min | cos max |
|---|---|---|---|---|
| injected_other | 100 | **1.103** | 0.939 | 1.229 |
| injected_other | 101 | 1.041 | 0.978 | 1.120 |
| injected_other | 102 | 1.077 | 1.034 | 1.163 |
| shuffled_other | 100 | 1.017 | 1.000 | 1.040 |
| shuffled_other | 101 | 0.890 | 0.825 | 0.941 |
| shuffled_other | 102 | 1.026 | 0.844 | 1.177 |

→ **両 conditions で cos ~1** = atom ごとに変位方向が **ほぼ直交** (一貫していない)。
shuffled が若干小 (より一貫) という逆転傾向もあり。

### 1.3 §2.2 real vs shuffled d_between (atom ごと、Other 間 cos)

| atom | injected_other d_between | shuffled_other d_between | real - shuffled |
|---|---|---|---|
| 42 | 0.843 | 0.667 | **+0.176** (real > shuffled) |
| 100 | 0.815 | 0.667 | **+0.148** (real > shuffled) |
| 200 | **0.586** | **0.896** | **-0.310** (符号逆!) |
| **3 atom 平均** | 0.748 | 0.743 | **+0.005** (ほぼ同等) |

→ 3 atom 平均で **real ≈ shuffled**。atom=42/100 では real が大、atom=200 で逆転。

### 1.4 §2.3 self 床からの離れ方

| condition | cos from self mean ± std |
|---|---|
| injected_other | **0.674 ± 0.219** |
| shuffled_other | **0.823 ± 0.222** |

→ shuffled の方が self 床から離れる (方向違い)。
→ injected_other は self 床に近い方向に変位 (中身経由でも self の決定に引っ張られる)。

---

## 2. Web Claude §3 「繋がる候補」3 条件への応答

| 条件 | 期待 | 観察 | 成立? |
|---|---|---|---|
| 各 Other が atom 横断で一貫した署名 | cos 小 (~0) | cos ~1 (両 conditions) | **✗** |
| real > shuffled | real > shuffled で d_between 差 | 3 atom 平均でほぼ同等 (+0.005) | **✗** |
| self 床から特徴的に離れる | 各 Other ごと特徴的 | shuffled の方が離れる | **✗** |

→ **3 条件すべて不成立**。

### 2.1 Web Claude §3 「繋がらない」読み

「real が shuffled と同様に散り、atom 横断で一貫しない」(構造外ノイズ、中身は届かない)
- 観察された (§2.1, §2.2)
- ただし §2.3 で injected_other が self 床に近い方向に変位する観察は留保事項 (中身経由でも self に引っ張られる)

---

## 3. 観察事実の整理 (3 atom 共通)

### 3.1 確実に言えること

1. **両 conditions (real / shuffled) で atom 横断一貫性なし** (cos ~1)
2. **real vs shuffled の d_between は 3 atom 平均で同等** (差 +0.005)
3. **shuffled が self 床から離れる傾向** = real は self 床に近い方向に変位
4. **atom=200 で real < shuffled** (3 atom で符号バラける、§2.2)

### 3.2 確実に言えないこと

- 「Other は確実に届かない」(留保 1: §2.3 で injected が self に近い方向 = 中身経由でも self 決定に従う特性)
- 「Other は確実に届く」(留保 2: 3 切り分けすべて不成立)
- 中間的: **「Other 中身は self の決定に引っ張られて、独立した署名を出口層に残せない」** という観察

### 3.3 v1111b → v1111b 計測修正の連続観察

| step | 結果 | 解釈 |
|---|---|---|
| v1111b (δ_repeat 不適切) | nesting 0/3 | 計測不備 |
| v1111b 計測修正 | atom 横断一貫性なし、real≈shuffled、shuffled が self 床から離れる | **構造外ノイズに近い動態** |

→ 2 回の計測で **Other 中身の独立署名は出口層に観察されない**。

---

## 4. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 + 物理切らない | ✓ stress=True |
| 書込 source_event 1 本 | ✓ |
| トリガー固定しない | ✓ |
| **δ_repeat 作らない** | ✓ タイミング固定 |
| **factor 不使用** | ✓ 距離は生 cos |
| **固定値ゼロ** | ✓ W_INJECT は実験定数 |
| 指標 crown しない | ✓ |
| **単一 seed 絶対視しない** | ✓ 3 atom 横断比較 |
| 判定置かない | ✓ |
| 新しい問い足さない | ✓ 同じ駆動 1 文 |

---

## 5. Code A 観察 (判定でない、事実整理)

### 5.1 主要観察

1. **Other 中身の独立署名は出口層に観察されない** (3 切り分けすべて不成立)
2. injected_other は self 床に近い方向に変位 = 中身経由でも self の決定に引っ張られる
3. shuffled (中身ゼロ) の方が self 床から離れた方向に変位 = ランダム注入は self とは独立
4. atom=200 で real < shuffled の符号逆転 = seed 依存性が残る

### 5.2 Web Claude §5 結論への応答

「出口層の偏りが Other の中身を反映して変わる経路が観察された / 観察されなかった」

→ **観察されなかった**

Web Claude §5 続き:
- 「変わらなければ別系は構造外ノイズ源、どこを変えれば中身が届くかが次の設計対象」

### 5.3 「中身が届く」を妨げている候補 (Code A 観察)

| 候補 | 根拠 |
|---|---|
| (a) 別系の中身が self の決定を踏襲する経路 | §2.3 で injected_other が self 床に近い方向 |
| (b) physics.inject が「形」を運ばず「位置 K nodes」だけ運ぶ | target_nodes (K=5) は ID リスト、Other の状態の「形」を Atom 系に渡せない |
| (c) target_nodes が center の決定で決まる | new_targets = trans_other(other, K) も「位置」だけ、Other の出口偏り (occupancy) は運ばれない |

---

## 6. ロバスト性 (W_INJECT=3 の別 run)

本実装は W_INJECT=2 のみ。Web Claude §4 やる順 4「別の固定 w でもう一度回し、結論が w に依らないか見る」は次 step として残す。

Code A 推奨: **本観察結果 (3 切り分け不成立) が決定的なら別 w でも同様の結論になる可能性高い**。ロバスト性確認より、§5.3 の「中身が届く経路」の検討に進むべき。

---

## 7. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | 「Other 中身の独立署名は出口層に観察されない」を結論として記録するか、別の計測で再確認するか |
| ② | §5.3 (b) physics.inject が target_nodes (位置 K) だけ運ぶ問題を、Other の状態の「形」を運ぶ経路 (例: ΔP_other を直接 inject) に拡張するか |
| ③ | W_INJECT=3 でロバスト性確認するか (Code A 推奨は不要、§5.3 検討優先) |
| ④ | v1110 Run 4 で観察された「Other を変えると結果が変わる」(rel +64% など) は何を反映していたのか再解釈するか (この結果と整合させる) |
| ⑤ | 24 atom seeds で再現確認するか、別の入口経路設計に進むか |

---

## 8. 出力ファイル

- `v1111b_fixed_check.md` (確認回答)
- `v1111b_fixed.py` (実装)
- `v1111b_fixed_report.md` (本文書)
- `run_v1111b_fixed/consistency.parquet` (§2.1)
- `run_v1111b_fixed/between.parquet` (§2.2)
- `run_v1111b_fixed/self_floor.parquet` (§2.3)
- `run_v1111b_fixed/summary.json`

---

## 9. 一文サマリ

v1111b 計測修正観察事実 (Code A、2026-06-02、Web Claude δ_repeat 捨て 3 参照点 self 床 + shuffled + atom 横断一貫性で測り直し、判定置かない) として、24 tasks Pool(24) × 800 秒 13.3 分実行で 3 切り分けすべて Other 中身署名観察されず (§2.1 atom 横断一貫性 = injected_other cos mean 1.074 / shuffled 0.978 両者 cos ~1 で atom ごと直交方向、§2.2 real vs shuffled d_between = 3 atom 平均 real 0.748 / shuffled 0.743 差 +0.005 ほぼ同等 ただし atom=200 で real<shuffled 符号逆、§2.3 self 床からの離れ方 = real 0.674 / shuffled 0.823 で shuffled の方が離れ injected は self 床に近い方向に変位)、Web Claude §3 繋がる候補 3 条件 (atom 横断一貫 / real > shuffled / self 床から特徴的に離れる) すべて不成立で 「Other 中身署名観察されなかった」結論、§5.3 中身を妨げる候補 (a 別系中身が self 決定踏襲 / b physics.inject が形でなく位置 K nodes だけ運ぶ / c new_targets も位置だけで Other 出口偏り運ばれず)、v1111b 計測不備 → v1111b 計測修正の連続観察で 2 回 Other 中身独立署名なし、規律遵守 (δ_repeat 作らない + factor 不使用 + 固定値ゼロ + 単一 seed 絶対視しない 3 atom 横断 + 判定置かない + 新しい問い足さず)、判断 5 件 (結論記録か別計測か / physics.inject 形を運ぶ経路に拡張か / W_INJECT=3 ロバスト性 Code A 推奨不要 / v1110 Run 4 +64% を再解釈 / 24 atom seeds か別入口設計か)、書込み unified/attention_center_prep/ 配下のみ。

---

**v1111b 計測修正 end. Web Claude 機能設計 + Taka 主題評価待ち。**
