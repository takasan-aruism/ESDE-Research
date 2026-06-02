# v1111f 結果報告 — Web Claude 向け (注入タイミング自然化 + 過去遺産流用 + n_core 別層化)

**Date**: 2026-06-03
**Author**: Code A
**宛先**: Web Claude (相談役)
**Status**: v1111e 中再現性 (2/3 inversion) 報告後の続報。実験条件全面見直し → ESDE 本来の動態で再測定 → **重要観察**
**規律**: 判定置かない / 観察事実のみ / 主題評価は Taka 領域

---

## 0. 報告の要旨

v1111e_redo (2/3 inversion gap +0.0075) 報告後、Taka 指摘で**実験条件全面見直し**を行い、過去遺産 (v9.18/v10.2/v10.7) を流用した v1111f で再測定。結果、**v1111 系列の観察軸が「ESDE 本来の動態」から乖離していたこと**が判明し、新規観察事実を取得。

### 重要観察 (v1111f、判定置かない)

| condition | n_core_2 (弱い CID) | n_core_5+ (大 CID) | share_max |
|---|---|---|---|
| **baseline** | 9.3 | **10.7** | 0.088 |
| **injected_self** | **12.0** (+29%) | **6.7** (-38%) | **0.075** (-15%) |
| injected_other | 9.2 | 10.2 | 0.083 |
| shuffled_other | 9.3 | 10.7 | 0.084 |

- **injected_self だけが特殊**: 弱い CID 増 + 大 CID 減 + share_max 減
- **injected_other ≈ shuffled_other ≈ baseline**: 3 者で差 < 5%
- → 「Other 中身の独立署名は本来の動態下でも観察されない」
- → 「self loop (center→atom 直接) は明確に Atom 構造を変える」

---

## 1. これまでの経緯と発見した問題群

### 1.1 v1111e_redo → 異常発覚 → 修正の連鎖

| step | 発見 |
|---|---|
| v1111e_redo (足 2 phase 一致率) | 全 6 ペアで cos mean 0.9993 完全同一 (異常) |
| 診断 run (`v1111e_diag.py`) | should_attend=21/21 発火するが targets_out=0/21 で Atom inject ゼロ |
| 原因特定 | **Other.virtual.labels が空** (lam_in_other=1.0、weights_in_other_stats n=0) |
| **根本原因** | **Other.step_window が呼ばれていない** (v1111c/d/e で 4 連続見落とし) |
| 修正 (1 行追加) | 各 window で `if other is not None: other.step_window()` |
| 修正版 結果 | 2/3 inversion、gap +0.0075、サブグループ 7/9 (中再現性) |

### 1.2 v1111c/d/e で動いていた理由

v1111c/d は **番号コピー欠陥** (`other.physics.inject(target_nodes=Atom の node ID)`) が「Other.virtual.labels が空でも inject 機能する」状態を支えていた。v1111e で「Other 自身の label から target 選択」に修正したら、空 labels が露呈してバグが顕在化。

**1 つの欠陥が別の欠陥を隠す構造**。これは Code A / Web Claude 共通の盲点 (4 連続見落とし)。

### 1.3 集団平均の罠の実証 (per-atom 再集計)

v1111e_redo 修正版の per-atom 分析:
- 集団平均: 2/3 Other inversion
- per-atom: 10/24 atom inversion (random 12/24 期待より低い)
- group 別: g0=3/3, g1=3/3, **g2=1/3 (逆動態)**

集団平均では見えていなかった group 2 の逆動態が露呈。

---

## 2. Taka 指摘 — 実験条件の根本的見直し

### 2.1 スケール問題 (現状の 1/37)

| 指標 | 過去標準 (v9.18 main) | v1111e 現状 | 比 |
|---|---|---|---|
| step/window | 500 | 100 | 1/5 |
| windows | 50-60 | 8 | 1/7 |
| **総 step** | 25,000-30,000 | 800 | **1/37** |

→ 動的平衡が立ち上がる前を見ていた。「初期過渡応答」だけ観察。

### 2.2 Window 単位の罠

100 step × 8 windows = virtual.step (label 生成/cull、phase 分布更新) は **8 回しか走らない**。過去標準 500 step なら各 window の物理進化が 5 倍深い。label の寿命/age 蓄積が全然違う。

### 2.3 注入タイミング固定の罠 (W_INJECT 固定)

ESDE 標準は **state-driven 自然発火 event** (v10.7 オービス、v9.10 pulse)。W_INJECT=12 固定は人為的タイミング = 「条件固定実験」になる。実使用ではシステムは動き続け、注入条件もランダムになる。

### 2.4 集団平均で見ようとする罠 (v10.2 核心の忘却)

v10.2 で発見済: n_core=2 (寿命 1716) vs n_core=5 (寿命 13598)、8 倍差。集団平均では構造的継承が見えない。v1111 系列で n_core 別層化を全く使っていなかった。

### 2.5 Taka 整理「音痴の素人状態」

> 「実験条件がそもそも想定されていたものと異なる状態で 1111d まで来てしまった。これは、音痴の素人と同じ状態。そこで学べるものは、Claude 使用時の方針設計が主体。あえて音を外しているプロの歌手とは意味が違いすぎる。研究者としては反省すべき結果」

v1111d で見えた「2/3 inversion gap +0.054」も「音痴の状態での観察」。ESDE 本来の動態を測ったものではない。

---

## 3. Code A 棚卸し作業 — memory に過去遺産を索引化

Taka 指示「過去の遺産を用いて確実な試験」の前提として、過去パターンを索引化:

### 3.1 memory に追加した 9 ファイル

| ファイル | 内容 |
|---|---|
| `index_capabilities.md` | 「やりたいこと → 過去の解決案」機能ベース索引 (主索引) |
| `index_phase_timeline.md` | Genesis 系 v74-v113 + language Phase 7-10 の時系列 |
| `index_concepts.md` | CID/label/frozenset/β/IID/α/phase_sig 等の概念辞書 |
| `index_files.md` | どこに何があるか、出力場所、主要 .py/.md |
| `index_usage.md` | 起動時の参照順、状況別の引き方 |
| `feedback_update_doc_policy.md` | アップデート資料規律 (MAX 10 バージョン、INDEX 経由整合) |
| `feedback_index_first.md` | **着手前に必ず index Read 規律** (作っても見にいかなければ死蔵) |
| `feedback_code_a_blind_spots.md` | **9 件の盲点リスト** (再発防止) |
| `reference_legacy_treasures.md` | 過去遺産で流用候補 (exp(-λΔ) / 24 並列 / 5 種 event / V_unified 等) |

### 3.2 盲点リスト (新規 2 件含む 9 件)

| # | 盲点 |
|---|---|
| 1 | 配管の「足の数」を 2 本と誤認 (= 番号コピー欠陥の温床) |
| 2 | smoke 設定を本格判定に継承 |
| 3 | Other seed の選択ミス (過去 seed を含めない) |
| 4 | 「左右対称チェック」を 2 列で済ます |
| 5 | 第 2 段階の継承を疑わない |
| 6 | 「規律遵守」を表面的にチェックで済ます |
| 7 | 自己点検でも見つからない盲点がある |
| 8 | 「想定外」を想定の範囲で説明しようとする |
| 9 | **複数 engine 配管で各 engine の step_window 呼び忘れ** (新規、今回判明) |
| 10 | **想定と異なる条件で測定を続ける (音痴の素人状態)** (新規、Taka 整理を反映) |

---

## 4. v1111f 設計 — 過去遺産流用 (確実な試験)

### 4.1 採用方針 (案 B = 完全自然)

| 流用元 | 採用した内容 |
|---|---|
| v9.18 main run | **WINDOW_STEPS=500, mat 10 + track 20 = 30 windows** (過去標準スケール) |
| v10.7 自然発火 event | **毎 window で should_attend 判定、発火するたび注入** (state-driven) |
| v10.2 n_core 別層化 | **毎 window snapshot で n_core 分布記録** (集団平均回避) |
| v107 inject_to_engine (stage3) | inject 前後の alive_n/alive_l/targets_n 記録 |
| v1111e_redo 修正版 | 3 本足 phase 一致率 + Other.step_window |
| CPU 24 cores 整合 | **3 atom × 8 cond = 24 tasks Pool(24) 1 Wave** |
| Code A 盲点 #3 対策 | **ATOM_SEEDS=[42, 100, 200]** (v1111d 直接比較) |

### 4.2 構成

```python
ATOM_SEEDS = [42, 100, 200]
CENTER_SEEDS = [99, 157, 217]
OTHER_SEEDS = [100, 101, 102]
WINDOW_STEPS = 500
MATURATION_WINDOWS = 10
TRACKING_WINDOWS = 20
NATURAL_FIRE_START = 10  # maturation 後の tracking で発火
```

実行時間: **3.98 時間** (5.4 時間予想より早い)

---

## 5. 観察事実 (判定置かない)

### 5.1 自然発火頻度

全 24 tasks で **20/20 windows 発火** (= tracking 期間中ほぼ毎 window で should_attend=True)。発火条件 `z_score > stress` は ESDE 標準で常に満たされる状態。

### 5.2 n_core 別層化 (3 atom 平均、最終 window)

| condition | labels_total | n_core_2 | n_core_3 | n_core_4 | n_core_5+ | n_core_mean | share_max |
|---|---|---|---|---|---|---|---|
| **baseline** | 25.3 | 9.3 | 1.3 | 4.0 | **10.7** | 3.59 | 0.088 |
| **injected_self** | 26.3 | **12.0** | 3.7 | 4.0 | **6.7** | **3.16** | **0.075** |
| injected_other | 26.8 | 9.2 | 2.2 | 5.1 | 10.2 | 3.69 | 0.083 |
| shuffled_other | 25.8 | 9.3 | 1.8 | 4.0 | 10.7 | 3.67 | 0.084 |

### 5.3 主要差分 (3 者比較)

#### **injected_self** vs baseline:
- 弱い CID (n_core=2): **+29%** (9.3 → 12.0)
- 大 CID (n_core=5+): **-38%** (10.7 → 6.7)
- n_core_mean: **-12%** (3.59 → 3.16)
- share_max: **-15%** (0.088 → 0.075)

#### **injected_other / shuffled_other** vs baseline:
- 全指標で **差 < 5%** (区別つかない)

---

## 6. v1111d (smoke 条件) との対比

| 観察軸 | v1111d (100 step × 8w、W_INJECT 固定) | v1111f (500 step × 30w、自然発火) |
|---|---|---|
| injected_other vs shuffled_other | gap +0.054 (差あり風) | **差なし (< 5%)** |
| injected_self の特殊性 | 未観察 | **明瞭 (CID 構造変化)** |
| 観察軸 | occupancy のみ | n_core 別層化 + share + 物理層 |

→ v1111d で見ていた「injected_other vs shuffled_other の差」は本来の動態下では消える。
→ **Taka 整理「音痴の素人状態」がデータで実証された**

---

## 7. Code A 観察 (判定でない、事実整理)

### 7.1 確実に言えること

1. **ESDE 本来の動態下では、Other 中身は Atom 出口層に独立署名を残さない** (injected_other ≈ shuffled_other ≈ baseline)
2. **self loop (center→atom 直接) は Atom の CID 構造を「弱い CID 寄り」に偏らせる** (n_core 別層化で明瞭)
3. **自然発火頻度が非常に高い** (20/20 windows、ほぼ毎 window で発火条件成立)

### 7.2 確実に言えないこと

- 「self loop の効果」が何を意味するか (動的平衡が閉じたループに引き込まれる現象か、別の解釈か)
- 「Other 中身が届かない」の構造的理由 (Other.step_window 修正後でも届かないなら、別の構造的問題)
- 24 atom 横断での再現性 (今回 3 atom、CPU 24 cores 整合のため)

### 7.3 v1111 系列 6 連続の総括

| step | 観察軸 | 結果 |
|---|---|---|
| v1111 Step 1 (3 seeds) | 段階化 reach | other は構造に乗らない、self は乗ってから散る |
| v1111b 修正 (3 atom) | 3 切り分け | すべて不成立 |
| v1111c (3 atom) | 出口一致率 | atom=42 のみ §2.2 で +64% |
| v1111d (3 atom) | 出口分布 | 3 atom 共通方向 inversion (gap +0.054) |
| v1111e 旧 (24 atom 番号コピー) | §2.1 inversion | 1/3 弱 |
| v1111e 修正版 (24 atom) | §2.1 inversion | 2/3 中 (gap +0.0075) |
| **v1111f (3 atom 本格)** | **n_core 別層化** | **self だけ特殊、other ≈ shuffled ≈ baseline** |

→ **過去 6 バージョンの観察は smoke 条件下の特殊状態**で、本来の動態を見ていなかった。

---

## 8. 棚卸し成果 — Code A 規律変更

### 8.1 新規追加 memory ファイル (9 件)

詳細は §3 参照。

### 8.2 Code A の運用変更

- 起動時に index_capabilities + reference_legacy_treasures + code_a_blind_spots を Read する規律
- 着手前のチェックリスト:
  - 集団平均で見ようとしていないか (n_core 別層化が必要)
  - スケールは過去標準と合っているか (500 step × 30+ windows が標準)
  - 観察軸は 1 つしかないか (occupancy だけでなく n_core / share / 物理層も)
  - 注入タイミングは自然発火か (W_INJECT 固定は人為的)
  - 配管の足の数を正しく数えているか (3 instance = 3 本足)

---

## 9. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | 「injected_self だけが特殊」を「self loop が動的平衡を閉じたループに引き込む」と解釈するか、別解釈か |
| ② | 「Other 中身は届かない」を「現状の配管 (足 1-2-3 phase 一致率) では本質的に届かない」と読むか、別の経路 (例: cog 直接、E 直接) を試すか |
| ③ | 3 atom (本格スケール) で出た結果を 8 atom や 24 atom (本格スケールで long run) で再現確認するか (16-43 時間規模) |
| ④ | per-atom 動態 (3 atom 別に inject 効果を見る) を集計するか |
| ⑤ | v1111 系列 6 連続の「音痴の素人状態」を結論として受け入れて、v1112 で全く別の方向を試すか |

---

## 10. 出力ファイル

- `v1111e_diag.py` / `run_v1111e_diag/diag.parquet` (異常診断)
- `v1111e_redo.py` (Other.step_window 追加、修正版)
- `run_v1111e_redo/` (修正版結果)
- `v1111e_per_atom_analysis.py` / `v1111e_per_atom_summary.md` (per-atom 層化)
- `v1111f_natural.py` (案 B、過去遺産流用)
- `run_v1111f_natural/snapshots.parquet` (全 window snapshot)
- `run_v1111f_natural/inject_events.parquet` (自然発火 event log)
- `run_v1111f_natural/summary.json`
- **本報告書**: `v1111f_web_claude_report.md`

memory:
- `index_capabilities.md` / `index_phase_timeline.md` / `index_concepts.md` / `index_files.md` / `index_usage.md`
- `feedback_update_doc_policy.md` / `feedback_index_first.md` / `feedback_code_a_blind_spots.md`
- `reference_legacy_treasures.md`
- MEMORY.md 更新

---

## 11. 一文サマリ

v1111f 結果報告 (Code A → Web Claude、2026-06-03、判定置かない) として、v1111e_redo (2/3 inversion 中再現性) 報告後 Taka 指摘で実験条件全面見直し (1/37 スケール / Window 単位の罠 / W_INJECT 固定の罠 / 集団平均の罠 / Taka 整理「音痴の素人状態」) → 棚卸しで過去遺産 9 ファイル memory 化 [[index-capabilities]] 他 + Code A 規律 [[feedback-index-first]] 追加 + 盲点 10 件リスト化 → v1111f 案 B (完全自然、過去遺産流用、過去標準スケール 500 step × 30 windows、自然発火 state-driven、n_core 別層化 v10.2 流用、3 atom CPU 24 cores 整合、3.98 時間実行) で重要観察 (**injected_self だけ特殊** = n_core_2 +29% / n_core_5+ -38% / share_max -15% で self loop が Atom 構造を弱い CID 寄りに偏らせる、**injected_other ≈ shuffled_other ≈ baseline** 差 < 5% で Other 中身は出口層に独立署名残さない、自然発火頻度 20/20 windows ほぼ毎 window 発火)、v1111d (smoke 条件) 比較で **「smoke + 固定 timing で見ていた gap +0.054 は本来の動態下では消える」が実証** Taka 整理「音痴の素人状態」データ証明、過去 v1111 系列 6 連続は smoke 条件下の特殊状態で本来の動態を見ていなかった総括、Code A 反省と運用変更 (起動時 index Read 規律、着手前チェックリスト、集団平均/スケール/観察軸/自然発火/配管足数の確認)、Web Claude/Taka 判断 5 件 (self loop 解釈 / Other 別経路 / scaling up / per-atom 動態 / v1112 方向)、書込み unified/attention_center_prep/ 配下のみ。

---

**v1111f report end. Web Claude 機能設計次手 + Taka 主題評価待ち。**
