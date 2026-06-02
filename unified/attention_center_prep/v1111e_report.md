# v1111e 第一段 観察事実報告 — 不再現 (1/3 inversion、判定置かない)

**Date**: 2026-06-02
**Author**: Code A
**Status**: v1111e 第一段完了、観察事実のみ、Web Claude / Taka 主題評価待ち
**親**: Web Claude v1111e 第一段設計 (24 atom で §2.1 inversion 再現確認) + Taka 二段手順
**規律**: 判定置かない / 観察事実のみ / 主役 §2.1 のみで結論 / §2.2/§2.3 は parquet 記録のみ判定不使用

---

## 0. 出口 (要点、判定置かない)

### **第一段 inversion 判定: 1/3 (弱再現性)** — v1111d の 3 atom 共通方向は 24 atom で固まらず

| Other | injected_other cos | shuffled_other cos | gap (shuffled - injected) | inversion? |
|---|---|---|---|---|
| 100 | 1.0042 | 1.0008 | **-0.0034** | ✗ (逆方向) |
| **101** | 1.0020 | 1.0071 | **+0.0052** | **✓** |
| 102 | 1.0055 | 1.0011 | **-0.0045** | ✗ (逆方向) |
| **全 Other 平均** | **1.0039** | **1.0030** | **-0.0009** | (ほぼゼロ) |

→ Web Claude §0/§4 判定: **「再現しない」(0-1/3) → 別粒度/経路を疑う**

---

## 1. 実行結果

### 1.1 設定 + 時間

- 192 unique tasks (24 atom × 8 conditions)
- ATOM_SEEDS=[1000-1023], CENTER_SEEDS=[2000-2023], OTHER_SEEDS=[100/101/102]
- W_INJECT=2 固定、Pool(24) 8 Wave 並列
- **総時間 6452 秒 (107.5 分 = 1.79 時間)**

### 1.2 主役 §2.1 atom 横断一貫性 (24 atom 全ペア = 276 pairs)

| Other | injected_other cos | shuffled_other cos |
|---|---|---|
| 100 | mean=1.0042 median=1.0010 std=0.1194 | mean=1.0008 median=1.0014 std=0.1330 |
| 101 | mean=1.0020 median=1.0000 std=0.1203 | mean=1.0071 median=1.0026 std=0.1174 |
| 102 | mean=1.0055 median=1.0003 std=0.1283 | mean=1.0011 median=1.0000 std=0.1242 |

**両 conditions で cos mean ≈ 1.000** (median も ≈ 1.0)、**std ≈ 0.12-0.13** (24 atom 変位ベクトルがほぼ random orientation を示唆)

### 1.3 サブグループ確認 (8 atom × 3 group)

- 9 サブグループ (3 group × 3 Other) 中 inversion 数 = **6/9**
- random なら 4-5/9 期待、6/9 は **わずかな偏り** (有意とは言えない)

---

## 2. v1111d (3 atom) との比較

| 指標 | v1111d (3 atom) | v1111e (24 atom) | 動き |
|---|---|---|---|
| injected_other cos mean | 0.965 | **1.0039** | 増加 (一貫性なくなる) |
| shuffled_other cos mean | 1.019 | **1.0030** | 減少 |
| gap (shuffled - injected) | +0.054 | **-0.0009** | **ほぼゼロに収束** |
| inversion (3 Other 中) | 2/3 (Other=100, 101) | 1/3 (Other=101 のみ) | **後退** |

→ **v1111d の 3 atom 共通方向は 24 atom で固まらない**:
- atom seeds [42, 100, 200] (v1111d) は偶然 inversion 寄りだった
- 24 atom seed に拡張すると平均で gap がほぼゼロ

---

## 3. 観察事実の整理

### 3.1 確実に言えること

1. **24 atom seed で §2.1 inversion は再現せず** (1/3 Other のみ、v1111d の 2/3 から後退)
2. **両 conditions の cos mean ≈ 1.0**: 24 atom 変位ベクトルがほぼ random orientation
3. **サブグループ 6/9** は弱い偏り (有意ではない)
4. v1111d の「3 atom 共通方向」は **統計的に固まらず** (3 atom が偶然 inversion 寄りだった可能性)

### 3.2 Web Claude §0 出口判定

「再現する → 共通土台確定 → 第二段へ / 再現しない → 共通でもまだ届かない、別粒度/経路を疑う」

→ **再現しない (1/3 inversion)** = 共通でも届かず → **別粒度/経路を疑う段階**
→ 第二段 (局所性) に進めない

### 3.3 Taka 二段手順の遵守

- 第一段で固まらないので **第二段 (§2.2/§2.3 局所性) を読まない** (規律遵守)
- §2.2/§2.3 は parquet に保存だけ (判定不使用)
- 「土台なしで局所を読むのが空回りの正体」(Web Claude §3) を遵守

---

## 4. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ |
| 同型 + 物理切らない | ✓ |
| 書込 source_event 1 本 | ✓ |
| トリガー固定しない | ✓ |
| **左右対称チェック (原理揃い + 粒度意図的非対称)** | ✓ (v1111d 配管そのまま) |
| 固定値ゼロ (factor 不使用) | ✓ |
| δ_repeat 作らない | ✓ |
| **共通が固まるまで局所読まない (二段手順)** | ✓ §2.2/§2.3 parquet のみ判定不使用 |
| **単一 seed 絶対視しない** | ✓ 24 atom で v1111d 3 atom 効果消失を率直に記録 |
| 指標 crown しない | ✓ |
| 判定置かない | ✓ |
| 新しい問い / 観察軸足さない | ✓ |

---

## 5. Code A 観察 (判定でない、事実整理)

### 5.1 主要観察

1. **24 atom seed で v1111d の 3 atom 共通方向が固まらず** (gap +0.054 → -0.0009)
2. **両 conditions の cos mean ≈ 1.0** (24 atom 変位ベクトルが random orientation)
3. **inversion 1/3 (Other=101 のみ)** = 弱再現性
4. **サブグループ 6/9** (有意でない偏り)

### 5.2 解釈の留保

- v1111d の 3 atom (=42, 100, 200) inversion は **偶然の結果** だった可能性が高い
- 「形 (分布) で運ぶ」だけでは 24 atom 共通方向は出ない
- 別粒度/経路 (Web Claude §0 → §4) を疑う段階

### 5.3 v1111b/c/d/e 4 連続観察

| step | 主役 | 結果 |
|---|---|---|
| v1111b 修正 (3 atom) | 3 切り分け | すべて不成立 |
| v1111c (3 atom、出口一致率) | §2.2 d_between | atom=42 のみ大、+64%→+0.061 |
| v1111d (3 atom、出口分布) | §2.1 atom 横断一貫性 | 3 atom 共通方向 inversion (gap +0.054) |
| **v1111e (24 atom、第一段)** | **§2.1 inversion 再現** | **不再現 (1/3、gap -0.0009)** |

→ **4 連続で「Other 中身の seed 共通署名」は決定的に観察されず**

---

## 6. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | 「§2.1 inversion が 24 atom で再現しなかった」を結論として記録するか、別の粒度/経路で再 trial か |
| ② | v1111d の 3 atom 共通方向が偶然だった可能性をどう扱うか (3 seeds 単体の結果は信頼性が低いという教訓?) |
| ③ | 「Other の中身が出口層に届く経路」は現状の配管 (入口一点 + 出口分布) では存在しない可能性、別経路を設計するか |
| ④ | §2.2/§2.3 を「土台なしで読まない」規律のまま、観察を止めるか |
| ⑤ | 別の粒度案: phase 分布 + E 強度マップで運ぶ / 出口に複数のチャネル / Other の cog 由来情報を運ぶ 等を検討するか |

---

## 7. 出力ファイル

- `v1111e_check.md` (確認回答)
- `v1111e.py` (実装、v1111d 配管 24 atom 拡張)
- `v1111e_report.md` (本文書)
- `run_v1111e/consistency.parquet` (主役)
- `run_v1111e/inversion.parquet` (inversion 判定)
- `run_v1111e/subgroups.parquet` (8 atom × 3 group)
- `run_v1111e/between_recorded_only.parquet` (§2.2、判定不使用)
- `run_v1111e/self_floor_recorded_only.parquet` (§2.3、判定不使用)
- `run_v1111e/summary.json`

---

## 8. 一文サマリ

v1111e 第一段観察事実 (Code A、2026-06-02、Web Claude 共通を統計で固める第一段、Taka 二段手順、判定置かない) として、192 tasks Pool(24) 8 Wave × 107.5 分 (1.79 時間) 実行で **主役 §2.1 inversion 判定 1/3** (Other=101 のみ inversion gap +0.0052、Other=100 -0.0034 逆方向、Other=102 -0.0045 逆方向)、全 Other 平均 cos 両者 ≈ 1.0 (injected 1.0039 / shuffled 1.0030 / gap -0.0009 ほぼゼロ)、サブグループ 6/9 弱い偏りで有意でない、v1111d (3 atom gap +0.054 inversion 2/3) との比較で **v1111d の 3 atom 共通方向は 24 atom で固まらず** (atom seeds [42/100/200] が偶然 inversion 寄りだった可能性)、Web Claude §0/§4 判定「再現しない (1/3) → 共通でも届かず別粒度/経路疑う」→ **第二段に進めない**、§2.2/§2.3 は parquet 記録のみ判定不使用 (Taka 二段手順遵守 土台なしで局所読まない)、両 conditions の cos mean ≈ 1.0 std ≈ 0.12-0.13 は 24 atom 変位ベクトルがほぼ random orientation を示唆、v1111b/c/d/e 4 連続観察で「Other 中身の seed 共通署名」は決定的に観察されず、規律遵守 (左右対称チェック原理揃い + 粒度意図的非対称 + 固定値ゼロ + 共通固まるまで局所読まない + 単一 seed 絶対視しない 24 atom で 3 atom 効果消失を率直に記録 + 判定置かない + 新しい問い足さず)、判断 5 件 (再現せず結論として記録か別粒度/経路で再 trial / 3 atom 共通方向が偶然だった可能性の教訓 / 現状配管では Other 届かない経路の可能性 / §2.2/§2.3 観察止めるか / 別粒度案 phase 分布 + E 強度マップ / 複数チャネル / Other の cog 由来情報 等)、書込み unified/attention_center_prep/ 配下のみ。

---

**v1111e 第一段 end. Web Claude 機能設計 + Taka 主題評価待ち。**
