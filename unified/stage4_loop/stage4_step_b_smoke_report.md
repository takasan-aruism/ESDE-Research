# 第 4 段階 Step B — 改修小 smoke 報告 (gate)

**Date**: 2026-05-31
**Author**: Code A
**Status**: 改修小 smoke 完了、**gate (止まって報告)**
**親**: Web Claude 第 4 段階実装指示 (温度感「あれこれ試して結果を見る」) + 現状確認報告

---

## 0. 出口判定

### **`partial`** (CID 層は変動、物理層は不変)

| 層 | 出口 |
|---|---|
| 物理層 (alive_n, alive_l) | **`loop_robust`** (条件変動でほぼ不変、Taka 「DNA のように堅牢」と一致) |
| CID 層 (labels) | **`loop_changes`** (maturation_alpha で labels 数 ±41% 変動) |

→ Web Claude §3 `partial` (一部の条件で変化、他は不変)。

---

## 1. 実行結果 (1165 秒 = 19.4 分)

### 1.1 6 conditions × 5 windows、最終 window 比較

| condition | 設定 | labels | n_core_mean | pct_2 | pct_5+ | g_alive_l | g_torque |
|---|---|---|---|---|---|---|---|
| A_baseline | (default) | 150 | 2.12 | 94.7% | 2.7% | 3147 | 1520 |
| **B1_mat_alpha_low** | **0.05** | **89** | 2.20 | 91.0% | **4.5%** | 3147 | 1198 |
| **B2_mat_alpha_high** | **0.20** | **192** | 2.10 | 95.3% | 2.1% | 3147 | 1903 |
| B3_stress_on | stress=True | 144 | 2.09 | 95.8% | 2.1% | 3139 | 1429 |
| B4_pressure_high | pressure_prob 0.05 | 137 | 2.05 | 97.8% | 1.5% | 3154 | 1343 |
| B5_inject_amount_low | inject 0.2 | 148 | 2.09 | 95.3% | 2.0% | 3193 | 1536 |

### 1.2 変動の効き (vs A_baseline)

| condition | Δ labels | Δ pct_5+ | Δ g_alive_l |
|---|---|---|---|
| B1_mat_alpha_low (0.05) | **-41%** (-61) | +1.8% pt | 0 |
| B2_mat_alpha_high (0.20) | **+28%** (+42) | -0.6% pt | 0 |
| B3_stress_on | -4% (-6) | -0.6% pt | -8 |
| B4_pressure_high | -9% (-13) | -1.2% pt | +7 |
| B5_inject_amount_low | -1% (-2) | -0.7% pt | +46 |

→ **maturation_alpha が圧倒的に強い操作変数** (改修小で最大効果)。

---

## 2. 観察事実 (loop への影響、判定語制限遵守)

### 2.1 CID 層は条件変動で変わる

- **maturation_alpha = 0.05** (cull 厳化) → labels -41%、弱い CID (n_core=2) が選択的に死、相対的に大 CID 比率 +1.8% pt
- **maturation_alpha = 0.20** (cull 緩和) → labels +28%、弱い CID 生き残り
- stress_on / pressure_high / inject_amount_low は ±10% 未満の微変

### 2.2 物理層は条件変動でほぼ不変

- 全 conditions で alive_n = 5000 (固定、想定通り)
- alive_l_count は 3139-3193 (±2%)、stress_intensity 0.97-1.00
- → Taka 「物理層は堅牢 DNA のように強固」と一致

### 2.3 v10.4 ベースライン (24 seeds × 50 windows × 5224 cid) との差

| 指標 | v10.4 baseline | 本 smoke A_baseline (5 windows) |
|---|---|---|
| n_core=2 | 76% | 94.7% (←短期 run で弱い CID 多い) |
| n_core=5 | 12.2% | 2.7% (←短期で大 CID 育っていない) |

→ smoke 5 windows は v10.4 50 windows と比較できる規模でない。フル (mat 20 + track 10 = 30 windows) で再評価必要。ただし **conditions 間の相対比較** は smoke でも成立。

### 2.4 stuck/oscillation 100% (前回 dialogue 観察)

本 smoke では dialogue ループなし (engine 単独動作)。stuck/oscillation 比較は別 run 要。

---

## 3. 期待 (Taka 規律「期待を高く持たない」) vs 結果

| 期待 (現状確認の予測) | 結果 | 一致? |
|---|---|---|
| 死亡 threshold 緩めると弱い CID 生存延長 | B2_mat_alpha_high (cull 緩和) で labels +28%、pct_5+ -0.6% pt | ✓ |
| stress_decay で link 取捨が変わる | g_alive_l Δ -8 (微変)、g_stress_intensity 0.97 | △ (微変) |
| semantic_pressure で θ 摂動増、label 数変化 | labels -9%、pct_2 +3.1% pt (大 CID 育ちにくく?) | ✓ |
| inject_amount を下げると外部刺激減 | smoke では外部接続なし、Background seeding にのみ影響 | △ (smoke で観察できず) |
| 全体的に「物理層は堅牢、CID 層は可変」 | 物理層 ±2%、CID 層 ±41% | ✓ |

---

## 4. 神の手回避の確認

- 各条件のパラメータは等間隔 (0.05/0.10/0.20、0.005/0.05 等) で恣意的範囲探索なし
- loop が崩れる条件を狙わず、結果として「mat_alpha が効く」を観察
- Web Claude §2.3 規律 ✓

---

## 5. Code A 観察 (判断は Taka)

### 5.1 何が分かったか

1. **改修小の中では maturation_alpha が最も強い操作変数** (labels ±41%、pct_n_core ±2% pt)
2. **物理層は堅牢** (alive_n 固定、alive_l ±2%、Taka 言及と一致)
3. **CID 層は可変** (mat_alpha で動的)
4. **stress / pressure / inject_amount は smoke 短期では微変**、長期で違うかも

### 5.2 第 4 段階の進め方の選択肢

| 選択 | 内容 | 計算量 |
|---|---|---|
| (i) フル 24 seeds 並列 で mat_alpha 比較 | A vs B1 vs B2 を 24 seeds で確定判定 | ~3 時間 (並列) |
| (ii) 改修中 (ノード棄損 permanent_dead) を smoke | enforce_extinction + inject 改修、smoke | 実装 30 分 + smoke 20 分 |
| (iii) 改修大 (ノード数 resize) を smoke | state.theta resize 新規 API、smoke | 実装 60 分 + smoke 20 分 |
| (iv) 第 4 段階を改修小で締めて第 5 段階へ | 既に「mat_alpha 効く + 物理堅牢」を観察、構造事実出た | - |

### 5.3 Code A 推奨 (温度感「あれこれ試す」遵守)

**(ii) 改修中 (ノード棄損) を smoke** を推奨:
- 改修小では maturation_alpha のみ効く、棄損 (Taka 言及 「テロメア的」) は **未試行の重要な軸**
- permanent_dead set 追加で「死んだら永久に戻らない」を実装、CID 寿命に影響するはず
- 改修大 (resize) は本格改修なので、棄損で効くか先に見る方が経済的
- smoke 20-30 分

---

## 6. 規律遵守確認

| 規律 | 確認 |
|---|---|
| 温度感「あれこれ試して結果を見る」 | ✓ 6 conditions 等間隔範囲探索 |
| わからんことは言えよな | ✓ stress/pressure/inject の長期効果は smoke で観察不能と明記 |
| 全階層調べる (IID 特定) | ✓ developmental/v104 で Integration ID 特定済 |
| 神の手回避 | ✓ 等間隔パラメータ、結果として観察 |
| 集団平均の罠 (空間+時間) | ✓ 5 windows × 6 conditions、time 推移記録 |
| self-fulfilling 検査 | ✓ A vs B 独立評価 |
| 物理層 frozen | ✓ unified/stage4_loop/ 配下のみ |
| 判定語制限 | ✓ 「変わる/変わらない」「効く/効かない」 |
| 期待を高く持たない | ✓ §3 で期待事前明示、合致 △ あり |
| smoke 後止まる | ✓ **本報告 gate** |

---

## 7. Taka / Web Claude 判断要請

| # | 判断要 |
|---|---|
| ① | 第 4 段階を改修小 (mat_alpha 効く + 物理堅牢) で締めて第 5 段階へ進むか |
| ② | 改修中 (ノード棄損 permanent_dead) smoke で次の軸を試すか (Code A 推奨) |
| ③ | 改修大 (ノード数 resize、Taka やり残し宿題) を実装するか、それは別段階か |
| ④ | フル 24 seeds 並列で mat_alpha 比較を確定するか (それは別 smoke の結果見てから?) |

### 7.1 Code A 観察

「**物理層は堅牢、CID 層は mat_alpha で可変**」は第 4 段階の最大の構造事実。Taka 言及「人間も寿命だけでなく環境要因で多様性を維持」に対しては、現状の改修小では「環境要因」が弱い (stress / pressure は微変)。

棄損 (テロメア的) と n_nodes 動的変動 (やり残し宿題) は両方とも環境要因強化の方向、smoke で試す価値あり。

---

## 8. 出力ファイル

- `stage4_step_b_smoke.py` (実装)
- `stage4_step_b_smoke_report.md` (本文書)
- `run_smoke/smoke_full.parquet` (30 rows = 6 cond × 5 win)
- `run_smoke/smoke_last_window.parquet`
- `run_smoke/smoke_run_summary.json`

---

## 9. 一文サマリ

第 4 段階 Step B 改修小 smoke 報告 (Code A、2026-05-31、Web Claude 実装指示 + 温度感「あれこれ試す」+ 現状確認後、6 conditions × 5 windows × N=5000 × 1 seed=42 で 1165 秒 19.4 分) として、出口 **`partial`** (物理層 = `loop_robust` alive_n 固定 alive_l ±2% Taka 「DNA のように堅牢」一致 / CID 層 = `loop_changes` maturation_alpha=0.05 で labels -41% mat_alpha=0.20 で +28% n_core 分布も変動)、改修小 6 conditions 結果 (A_baseline mat 0.10 labels 150 / B1_mat_alpha_low 0.05 labels 89 -41% pct_5+ +1.8pt cull 厳化で弱い CID 死 / B2_mat_alpha_high 0.20 labels 192 +28% cull 緩和で弱い CID 生 / B3_stress_on -4% 微変 / B4_pressure_high 0.05 -9% 微変 pct_2 +3.1pt 大 CID 育たず / B5_inject_amount_low 0.2 -1% 微変)、**maturation_alpha が圧倒的に強い操作変数** (改修小で最大効果)、物理層は条件変動で堅牢 (Taka 言及と一致)、v10.4 ベースライン (24 seeds 50 windows n_core=2 76%/n_core=5 12.2%) と smoke 5 windows (n_core=2 94.7%/n_core=5+ 2.7%) は規模差、conditions 間相対比較は smoke で成立、期待 vs 結果 比較表 (cull 緩和で弱い CID 延長 ✓ / stress △微変 / pressure ✓微変 / inject smoke で観察不能 / 物理堅牢 CID 可変 ✓)、神の手回避 (等間隔パラメータ恣意的でない結果として観察)、Code A 観察 5 件 (mat_alpha 最強 / 物理堅牢 / CID 可変 / stress pressure inject 短期では微変 / 棄損 + resize 未試行)、選択肢 4 件 (フル 24 seeds mat_alpha 比較 / 改修中 ノード棄損 smoke 推奨 / 改修大 resize / 第 4 段階締め)、Code A 推奨 (ii) 改修中棄損 smoke (mat_alpha 単独で出口出たので環境要因強化のテロメア的棄損を次に試すべき・改修大 resize の前に棄損で効くか見るほうが経済的)、規律遵守 (温度感 + わからんこと + 全階層調べ IID 特定 + 神の手回避 + 集団平均の罠 + self-fulfilling + 物理層 frozen + 判定語制限 + 期待高く持たない + smoke 後止まる本報告 gate)、判断 4 件 Taka へ。

---

**Step B 改修小 smoke end. gate (Taka / Web Claude 判断待ち)。**
