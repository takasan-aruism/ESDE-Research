# v1111b — 出口偏りの形 × Other 次第性 観察事実報告 (判定置かない)

**Date**: 2026-06-02
**Author**: Code A
**Status**: v1111b 完了、観察事実のみ、**反復定義の見直し要請** あり
**親**: Web Claude v1111b 主題設計 + Code A 確認回答 (反復ブレ案 (a) W_INJECT 2/3)
**規律**: 判定置かない / 観察事実のみ / 単一視しない (3 atom 共通の足跡として記録)

---

## 0. 出口 (要点、判定置かない)

### 3 atom seeds 全部で nesting 不成立 (主張なし)

| atom | δ_repeat (cos) mean | d_between (cos) mean | δ_repeat vs d_between |
|---|---|---|---|
| 42 | **0.964** | 0.296 | δ_repeat >> d_between (差 0.67) |
| 100 | **0.801** | 0.448 | δ_repeat > d_between (差 0.35) |
| 200 | **0.583** | 0.438 | δ_repeat > d_between (差 0.15) |

→ **3 seeds で δ_repeat (反復内ブレ) が d_between (Other 間距離) を超える**

shuffled でも同様 (0/3 atoms で nesting)

### Web Claude §2.4 切り分けの読み

- 直訳: 「injected_other 自体に nesting なし → Other の中身が出口層に届かず」
- **Code A 留保 (重要)**: 反復定義 (W_INJECT 2/3) のブレが大きすぎる可能性、Other の効果が timing 差に埋もれている可能性 (§4)

---

## 1. 実行結果

### 1.1 設定 + 時間

- 42 tasks: 3 atom × 14 conditions (baseline 1 + injected_self 1 + injected_other 6 + shuffled_other 6)
- Pool(24) 並列、総時間 **1607 秒 (26.8 分)** (推定 40-50 分より早い)
- WINDOWS=9 (W_INJECT max 3 + K_OBSERVE 5 + 1)、N=5000

### 1.2 詳細結果 (per atom seed)

#### atom=42

| 種類 | δ_repeat (cos) | d_between (cos) | nested |
|---|---|---|---|
| injected_other | mean=0.964 max=1.000 | mean=0.296 min=0.274 | False |
| shuffled_other | mean=0.953 | mean=0.149 | False |
| d_self_to_other | -- | mean=0.800 | -- |

→ W_INJECT=2 と W_INJECT=3 で形がほぼ直交 (cos 距離 0.96-1.00)

#### atom=100

| 種類 | δ_repeat (cos) | d_between (cos) | nested |
|---|---|---|---|
| injected_other | mean=0.801 max=1.000 | mean=0.448 min=0.275 | False |
| shuffled_other | mean=0.897 | mean=0.380 | False |

→ δ_repeat (timing ブレ) が d_between (Other 中身差) を 2 倍近く超える

#### atom=200

| 種類 | δ_repeat (cos) | d_between (cos) | nested |
|---|---|---|---|
| injected_other | mean=0.583 max=0.890 | mean=0.438 min=0.425 | False |
| shuffled_other | mean=0.617 | mean=0.537 | False |

→ 3 seeds 中で最も差が小さいが、依然 δ_repeat > d_between

---

## 2. 観察事実の整理 (3 atom seeds 共通)

### 2.1 W_INJECT timing が支配的

- W_INJECT=2 と W_INJECT=3 (1 window 差) で出口偏りの形が **大きく変わる**
- cos 距離 0.58-0.96 (1.00 = 直交)
- 3 atom seeds 共通の事実

### 2.2 Other を振った時の形の差

- d_between (cos): 0.30-0.45 (atom seed 依存)
- shuffled vs injected_other で d_between が同等 (atom=42: 0.30 vs 0.15、atom=100: 0.45 vs 0.38、atom=200: 0.44 vs 0.54)
- → Other 中身を捨てた shuffled でも、Other 間で同等の形の差が出る

### 2.3 self 床との関係

- d_self_to_other (cos): 0.46-0.80
- self は別系の形と離れている (cos > 0.46)
- ただし δ_repeat と同オーダー (W_INJECT timing 差にも埋もれる)

---

## 3. Web Claude §2.4 sanity 切り分けの読み

**直訳的読み**:
- injected_other nested なし → Other の中身が出口層に届かない (Web Claude 案 B ノイズ寄り)

**Code A 留保 (重要)**:
- 「Other の中身が届かない」のではなく、「反復定義 (W_INJECT 2/3) のブレが Other 差を埋もれさせる」可能性
- 1 window 差で形がほぼ直交になる動態は、「反復」の基準として大きすぎる
- 別の反復定義が必要 (§4)

---

## 4. 反復定義の見直し要請 (Web Claude 判断要、最重要)

### 4.1 Code A 提案 (a) W_INJECT 2/3 の問題

- W_INJECT=2 と W_INJECT=3 は ATTENTION 半減期 0.69w (= 69 step) の前後
- 1 window 差で出口偏りの形が **ほぼ直交になる** (cos 0.58-0.96)
- これは「同じ Other での自然なブレ」の基準として **大きすぎる**
- Other の中身の差 (cos 0.30-0.45) が埋もれる

### 4.2 別の反復定義候補

| 案 | 内容 | 期待 |
|---|---|---|
| (d) **same setting、different observation k** | rep_a: k=4 / rep_b: k=5 (同 timing で観察 window をずらす) | timing は同じ、観察時点の自然なブレ |
| (e) **timing variation 内で複数 step ずらし** | W_INJECT を 200 step 単位で変える (W=2 と W=2 + 半 step) → 整数 window でなく fractional step | 細かい timing 差で δ_repeat 小さく |
| (f) **多 W_INJECT 平均** | 3 timing (W=2,3,4) の平均 ΔP を 1 つの ΔP とし、3 atom seeds で再現性確認 | timing を平均化、安定 ΔP |
| (g) **同 timing で別 atom 隣接 seed** | atom=42 と atom=43 で同 Other (atom 隣接 seed) | atom seed 影響混入だが Other 比較 |

Code A 推奨: **(d) または (f)**
- (d): k=4 と k=5 で観察、timing 差なし、観察 1 window 差のブレ
- (f): 3 timing 平均、安定 ΔP

### 4.3 別案で同じ問題が起きる可能性

W_INJECT 1 window 差で cos 0.58-0.96 と大きく変動する以上、別案 (d, e, f) でも δ_repeat が大きい可能性。
これは「engine の rng が timing に強く依存する設計」の構造的問題。
別案でも nesting 不成立なら、**「W_INJECT timing が支配的で Other 中身は捉えられない」を構造事実として記録** (これも観察事実)。

---

## 5. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 物理層 frozen | ✓ unified/attention_center_prep/ 配下のみ |
| 同型 + 物理切らない | ✓ stress=True 継承 |
| 書込 source_event 1 本 | ✓ physics.inject のみ |
| トリガー固定しない | ✓ z_score/stress/λ_dyn/target_phase 全て state 由来 |
| **閾値規律 固定値ゼロ** | ✓ factor 不使用、距離は生大小 |
| 指標 crown しない | ✓ cos/eu/labels/share 並列 |
| **単一 seed 絶対視しない** | ✓ 3 atom 共通の足跡 (nesting 不成立) を記録 |
| 判定置かない | ✓ 「成功」「失敗」未使用 |
| **想定外の Web Claude に提示** | ✓ §4 で反復定義の見直し要請 (Taka 格言「結果が想定と合わなければ想定を見直す」) |

---

## 6. Code A 観察 (判定でない、事実整理)

### 6.1 確実に言えること

1. **3 atom seeds 共通で nesting 不成立** (再現性)
2. **W_INJECT 1 window 差で出口偏りの形がほぼ直交** (cos 0.58-0.96)
3. **shuffled でも injected_other と同等の d_between** (中身を捨てても Other 間に差が出る)
4. **self 床は Other 形から離れている** (d_self_to_other cos 0.46-0.80)

### 6.2 確実に言えないこと

- 「Other の中身が出口層に届かない」(Web Claude 案 B) と即断できない
- 反復定義の問題で Other 差が timing 差に埋もれた可能性
- 別の反復定義で再 run しないと結論できない

### 6.3 観察事実から確実に言える結論

**W_INJECT timing が出口偏りの形を強く支配する。Other を振った形の差は、timing 差より小さい。**

これは:
- (i) 「Other の中身は届くが timing 差より小さい」or
- (ii) 「Other は届かず、timing と shuffled 差はノイズ」

の区別がついていない。別の反復定義 (§4.2) で再 run が必要。

---

## 7. Web Claude / Taka 判断要請

| # | 問い |
|---|---|
| ① | 反復定義 (a) W_INJECT 2/3 の δ_repeat が大きすぎる問題を受けて、案 (d) k=4/5 観察ずらし or (f) 3 timing 平均 で再 run するか |
| ② | (i) Other は届くが timing より小さい / (ii) Other は届かない の区別がついていない状態を受け入れて次設計に進むか、別案で再 run か |
| ③ | shuffled でも d_between が出る (atom=42 0.15、atom=200 0.54) ことから、Other 間の差は seed 差ノイズが主可能性 (§2.2)、これは元の Web Claude §2.4 解釈と整合 |
| ④ | この観察事実 (nesting 不成立 + timing 支配) を Web Claude §5 結論「観察されなかった」として記録し、v1112 では別の入口経路を探すか |
| ⑤ | 24 atom seeds で再現確認するか (Code A 推奨は反復定義見直し後) |

---

## 8. 出力ファイル

- `v1111b_check.md` (確認回答)
- `v1111b_step1_shape_other.py` (実装)
- `v1111b_report.md` (本文書)
- `run_v1111b/tasks_results.parquet` (42 rows = tasks 結果)
- `run_v1111b/dp_records.parquet` (36 rows = baseline 除く ΔP)
- `run_v1111b/nesting.parquet` (3 rows = atom ごとの nesting 判定)
- `run_v1111b/summary.json`

---

## 9. 一文サマリ

v1111b 出口偏りの形 × Other 次第性 観察事実 (Code A、2026-06-02、Web Claude 主題設計 + Code A 反復ブレ案 (a) W_INJECT 2/3、42 tasks Pool(24) 並列 26.8 分実行、判定置かない) として、3 atom seeds (42/100/200) で nesting 全 0/3 不成立 (atom=42 δ_repeat cos 0.964 vs d_between 0.296 / atom=100 0.801 vs 0.448 / atom=200 0.583 vs 0.438) で δ_repeat が d_between を遥かに超え、shuffled でも 0/3 で nesting 不成立、Web Claude §2.4 直訳「Other の中身が出口層に届かず」だが Code A 留保 (反復定義 W_INJECT 2/3 のブレ大きすぎ Other 差を埋もれさせる可能性、1 window 差で出口偏り形がほぼ直交 cos 0.58-0.96 = 反復基準として大きすぎる)、3 atom seeds 共通の足跡 (W_INJECT timing が支配的・Other 振り形差 cos 0.30-0.45 は timing 差より小さい・shuffled vs injected_other で d_between 同等で中身捨てても Other 間差出る = seed 差ノイズ可能性・self 床は別系形から離れる cos 0.46-0.80)、反復定義見直し要請 §4 (案 a 不適切、別案 (d) k=4/5 観察ずらし or (f) 3 timing 平均推奨、別案でも nesting 不成立なら timing 支配構造事実として記録 これも観察事実)、確実に言えない 2 解釈 (i Other は届くが timing より小 / ii Other は届かない区別なし)、Web Claude / Taka 判断 5 件 (反復定義見直し再 run か / 不確実状態で次設計か / shuffled d_between から seed 差ノイズ主は §2.4 整合 / 観察されなかったとして v1112 別入口探すか / 24 atom seeds は反復定義見直し後か)、規律遵守 (物理層 frozen + 同型 + source_event 1 本 + トリガー固定しない + 閾値固定値ゼロ + 指標 crown しない + 単一 seed 絶対視しない + 判定置かない + 想定外 Web Claude 提示)、書込み unified/attention_center_prep/ 配下のみ。

---

**v1111b end. Web Claude 反復定義見直し判断 + Taka 主題評価待ち。**
