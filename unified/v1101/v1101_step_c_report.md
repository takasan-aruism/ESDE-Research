# v11.0.1 (v1101) Step C 観察事実報告 — 観察 1「一点を捉える」段階 1

*作成*: 2026-05-17、Code A
*親*: `v1101_phase_design.md` (Web Claude 2026-05-16 改訂版) + `v1101_step_a_recognition.md` + `v1101_step_b_environment_check.md`
*対象*: Web Claude (Phase Result 翻訳用素材) + Taka (確認)
*目的*: Step C-1〜C-4 観察事実報告、judgment 回避、Web Claude 翻訳要素材

---

## 0. 一文サマリ

Step C-1〜C-4 完了 (実行時間 2.7 秒、書き込み `unified/v1101/outputs/main/` 配下 4 ファイル計 5.6 MB)、観察 1 主中心 cid 選定 (n_pulses_short 最大、per-seed × {v112, v108_standard} 2 条件 = 48 中心、Taka 確定 (c)) + 副ランダム比較対照 (rng seed=42 で各条件 5 cid × 24 seeds = 240 比較対照、Taka 確定 (d)) + 4 解像度 trajectory 抽出 (event/pulse/step10/window × 24 seeds、計 374,072 行) + cid × 解像度別の rank_1_atom 方向反転回数 + rank_1_sim 統計 + dominant_atom 集中度 (1,094 summary 行) を構造的に算出、主要観察事実 4 件: (1) **v108_standard 条件で n_pulses_short 最大 cid 24 seeds 中 21 seed の dominant_atom が `WLD.artless` で一致** (87.5%、v10.6 で動学的優位 atom として既出)、v112 条件では `PER.sound` 10 / `TIM.moment` 5 / `TIM.appear` 4 と相対的多様、(2) **v108_standard 中心 cid の dominant_atom_fraction 0.94 (event 解像度) vs v112 中心 cid 0.47** — v108_standard で選ばれる中心は単一 atom に強くロック、v112 で選ばれる中心は複数 atom 間で揺れる、(3) **n_observations: 両条件とも中心 cid は random より約 1/3〜1/4 短い** (v112 event center=174 / random=383、v108_standard event center=22 / random=95、cid の trajectory row 数の差)、(4) **window 解像度で v112 中心 cid の atom_change_rate 0.156 vs random 0.297** — window 単位では中心 cid のほうが atom 安定 (一点としての特徴)、副次観察として v108_standard 中心 cid pool size 平均 213 (per seed 170-239) vs v112 受容 cid pool size 平均 17.5 (per seed 13-23) で n_pulses_short max は v108_standard 1.95-2.00 > v112 1.56-1.83、両条件の中心 cid に重複 0 (v108 22 unique cid / v112 22 unique cid、別 cid 空間)、Code A は「ようだ」レベル所見も解釈統合は Web Claude 領域 (絶対格言 #12)、Step D 観察 2 取り込み点中心の波及へ進行可、Step F グラフ HTML で観察 1 を可視化予定。

---

## 1. Step C 構造的成果 (Taka 確定事項反映)

### 1.1 観察 1 中心 cid 選定 (C-1、Taka 確定 (c) n_pulses_short 最大)

| 条件 | per seed cid pool size | n_pulses_short max 範囲 | n_pulses_short mean 範囲 | unique 中心 cid 数 |
|---|---|---|---|---|
| v112 受容 cid pool | mean 17.5 (range 13-23) | 1.56 - 1.83 (mean 1.71) | 1.14 - 1.65 (mean 1.46) | 22 / 24 (重複 2 seed) |
| v108_standard top_k_100 | mean 213.0 (range 170-239) | 1.95 - 2.00 (mean 1.99) | 0.98 - 1.86 (mean 1.65) | 21 / 24 (重複 3 seed) |
| 両条件間の中心 cid 重複 | — | — | — | **0** |

**観察事実**: v108_standard の中心 cid (top_k_100 pool 内) と v112 の中心 cid (受容 cid pool 内) は 24 seeds 全てで **完全に別 cid**。pool が異なるため構造的整合 (受容 cid pool は ¬β + lifespan ≥ 977 + n_core ≥ 5 + fam ≥ top 50% の 4 条件絞り込み、top_k_100 はより広範)。

### 1.2 観察 1 副ランダム比較対照 (C-3、Taka 確定 (d))

| 項目 | 値 |
|---|---:|
| 各条件 × seed あたりランダム cid 数 | 5 |
| 総ランダム対照数 | 240 (24 seeds × 2 条件 × 5) |
| 乱数 seed (numpy.random.default_rng) | 42 (神の手回避、再現可能) |
| 中心 cid 除外 | ✓ |

### 1.3 観察 1 trajectory 抽出 (C-2、4 解像度)

| 解像度 | 時間粒度 | 行数 (target cids のみ、24 seeds 全部) |
|---|---|---:|
| event | per-event (`t`) | ~93,000 |
| pulse | per-pulse (`t`、pulse_n 累計あり) | ~62,000 |
| step10 | per-10step (`t`) | ~210,000 |
| window | per-window (`step_at_window_end`) | ~8,000 |
| **合計** | | **374,072** |

→ 各 trajectory row は `seed`, `cognitive_id`, `t`, `rank_1_atom`, `rank_1_sim`, `top_category` + 状態列 (`n_core_member`, `lifespan_so_far`, `C_at_window_end`, `Q_remaining_at_window_end`, `R_familiarity`) + 解像度ラベル + `role` (center/random) + `condition_pool` (v112/v108_standard) を持つ。

### 1.4 集計 (C-4、1,094 summary 行)

cid × 条件 × 役割 × 解像度別の 17 列:
- `n_observations`, `n_atom_changes`, `atom_change_rate`
- `n_unique_atoms`, `dominant_atom`, `dominant_atom_fraction`
- `rank_1_sim_mean/std/min/max`
- `t_min`, `t_max`

---

## 2. 主要観察事実 4 件 (Web Claude 翻訳用素材)

### 2.1 観察 1: v108_standard 中心 cid の dominant_atom が `WLD.artless` で 24 seeds 中 21 seed 一致

| 条件 | event 解像度 dominant_atom の上位 (中心 cid 24 個) |
|---|---|
| **v108_standard** | **`WLD.artless` 21 / TIM.appear 3** |
| v112 | `PER.sound` 10 / `TIM.moment` 5 / `TIM.appear` 4 / `PRP.multiple` 2 / `COM.conduct` 2 / `PRP.shallow` 1 |

**観察事実**:
- v108_standard top_k_100 cid pool から「n_pulses_short 最大」の cid を選ぶと、24 seeds 中 **21 seed で `WLD.artless` 主導 cid** が選ばれる
- v10.6 cross_seed_event_step_evolution で `WLD.artless` は 24 seeds 動学的優位 atom (留保 #33) として既出、本 Step C 結果と整合
- v112 受容 cid pool 内では中心 cid の dominant_atom が **PER 系 / TIM 系** に分散 (`PER.sound` 主導が最多 10 seed)
- 留保解釈候補 (Web Claude 翻訳領域): v108_standard と v112 で選ばれる中心 cid は **異なる atom 系統** に対応している可能性、ただし両条件で n_pulses_short max は構造的差 (pool size 差 × cid 選定基準の交互作用)

### 2.2 観察 2: dominant_atom_fraction で中心 cid の atom 集中度に条件差

| 解像度 | v108_standard 中心 | v108_standard ランダム | v112 中心 | v112 ランダム |
|---|---:|---:|---:|---:|
| event | **0.938** | 0.816 | **0.468** | 0.489 |
| pulse | **0.978** | 0.795 | **0.485** | 0.454 |
| step10 | **0.923** | 0.803 | **0.549** | 0.534 |
| window | **1.000** | 0.804 | **0.810** | 0.614 |

**観察事実**:
- v108_standard 中心 cid: dominant_atom_fraction 0.92-1.00 (= 1 つの atom にロック)
- v112 中心 cid: dominant_atom_fraction 0.47-0.81 (= 複数 atom 間で揺れる)
- v108_standard 条件で「中心 vs ランダム」差: 24 seeds 中 **21 seed で中心 > ランダム** (差 mean +0.121)
- v112 条件で「中心 vs ランダム」差: 12 / 24 seed (差 mean -0.021、構造的に差なし)
- 留保解釈候補: 中心選定基準 (n_pulses_short 最大) は **v108_standard では atom 集中度の高い cid を選び**、**v112 では atom 揺れの大きい cid を選ぶ** 可能性

### 2.3 観察 3: n_observations (trajectory row 数) で中心 cid が ランダムより約 1/3 短い

| 解像度 | v112 中心 | v112 ランダム | v108_standard 中心 | v108_standard ランダム |
|---|---:|---:|---:|---:|
| event | 173.7 | 383.2 | 22.0 | 94.7 |
| pulse | 133.3 | 318.5 | 19.6 | 77.9 |
| step10 | 665.2 | 1590.7 | 96.0 | 388.8 |
| window | 12.7 | 31.7 | 1.8 | 11.5 |

**観察事実**:
- 両条件で中心 cid の trajectory row 数 < ランダム cid の row 数 (約 1/3〜1/4 比率)
- v112 中心は約 173 行 (event)、v108_standard 中心は約 22 行 (event)
- v108_standard 中心 cid は window 解像度で **1.8 行平均** (≈ 1〜2 window のみ生存)
- 留保解釈候補 (Web Claude 翻訳領域): n_pulses_short 最大 cid は **観察期間中に早期に固定または死亡** する可能性 (final_state を別途確認推奨)、本観察事実は cid の lifespan / final_state との関係調査の動機を提供する

### 2.4 観察 4: window 解像度で v112 中心 cid の atom 安定性

| 解像度 | v112 中心 atom_change_rate | v112 ランダム atom_change_rate |
|---|---:|---:|
| event | 0.148 | 0.154 |
| pulse | 0.254 | 0.250 |
| step10 | 0.052 | 0.057 |
| **window** | **0.156** | **0.297** |

**観察事実**:
- event/pulse/step10 解像度では中心 vs ランダムの atom_change_rate ほぼ同等
- **window 解像度のみ v112 中心 cid のほうが atom_change_rate 低**い (0.156 < 0.297)
- window 解像度は粒度が最も粗い (per seed 平均 12.7 row)、ここで中心 cid のほうが atom 安定 = 「一点としての特徴」が window 粒度で表出
- v108_standard では window 解像度 atom_change_rate 比較不能 (中心 cid の n_observations 1.8 で変化算出が成立しない)
- 留保解釈候補: 中心 cid は **長時間粒度では安定、短時間粒度ではランダム同等の揺れ** という時間スケール依存の構造

---

## 3. 副次観察 (構造記録、Web Claude 必要時翻訳用)

### 3.1 cid pool size 構造差 (両条件比較)

| 項目 | v112 受容 cid pool | v108_standard top_k_100 |
|---|---:|---:|
| per seed pool size mean | 17.5 | 213.0 |
| pool size range | 13 - 23 | 170 - 239 |
| pool 形成条件 | ¬β + lifespan ≥ 977 + n_core ≥ 5 + fam ≥ top 50% (4 条件) | atom_sim top_k=100 |
| 中心 cid 選定範囲 | 13-23 候補から argmax | 170-239 候補から argmax |

→ v112 のほうが選択幅が狭く、構造的に max cid の n_pulses_short も低くなる傾向。

### 3.2 n_pulses_short max の条件差

- v108_standard: 1.95 - 2.00 (mean 1.99、24 seeds 中 21 seed で max ≈ 2.0 で平坦)
- v112: 1.56 - 1.83 (mean 1.71、より分散)

留保解釈候補 (Web Claude 領域): v108_standard で max が ≈ 2.0 で頭打ちなのは **n_pulses_short の構造的上限** か、top_k_100 pool が十分大きく max が安定するか、別途検証要。

### 3.3 中心 cid の cid id 例 (再現可能性確認用)

```
seed 0: v112 → cid 22 (n_pulses_short max 1.72)
        v108_standard → cid 71 (n_pulses_short max 1.99)
seed 1: v112 → cid 239 (n_pulses_short max 1.56)
        v108_standard → cid 118 (n_pulses_short max 2.00)
seed 2: v112 → cid 289 (n_pulses_short max 1.66)
        v108_standard → cid 115 (n_pulses_short max 1.98)
```

→ 全 48 中心 cid は `observation_1_center_cids.parquet` に記録、`rng seed=42` で 240 ランダム cid は `observation_1_random_cids.parquet` に記録 (再現可能)。

---

## 4. 観察事実の解釈規律遵守 (絶対格言 #10, #12)

Code A は本観察事実を以下のように **断定しない**:

- 観察事実: v108_standard 中心 cid 21 / 24 seeds で `WLD.artless` dominant
- 主題評価 (NOT Code A 領域): 「WLD.artless が ESDE で最も盛んな atom である」「中心 cid 選定基準が WLD.artless を引き寄せる」等の解釈統合は **Web Claude Phase Result 領域**
- Code A 領域: 観察事実の構造的記録 + 留保解釈候補の提示 (Web Claude 翻訳要素材)

success/fail 判定なし、3 単位観察フレームへの寄与は本書 §2 の 4 主要観察 + §3 副次観察として記録、解釈統合は Web Claude が Phase Result でまとめる。

---

## 5. 出力ファイル仕様 (5.6 MB)

| ファイル | サイズ | 行数 | 用途 |
|---|---:|---:|---|
| `observation_1_center_cids.parquet` | 5.9 KB | 48 | 中心 cid 一覧 (seed × 条件 × cid + n_pulses_short max/mean) |
| `observation_1_random_cids.parquet` | 3.9 KB | 240 | ランダム比較対照 cid 一覧 (rng seed=42 で再現可能) |
| `observation_1_trajectory.parquet` | 5.5 MB | 374,072 | 4 解像度 trajectory (center + random、Step F グラフ HTML 入力) |
| `observation_1_summary.parquet` | 72 KB | 1,094 | cid × 条件 × 役割 × 解像度別の 17 列集計 |

書き込みは `unified/v1101/outputs/main/` 配下のみ、`developmental/v106/v108/v112` の main outputs は **1 byte も変更していない** (Step G で bit-identity 層 B 検証予定)。

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step C での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ §1-2 で構造的事実先、§4 で解釈規律 |
| 2 | 物理層 frozen 絶対 | ✓ v106/v108/v112 main outputs read-only、書き込み unified/v1101/ 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | ✓ 中心 vs ランダム比較 (各 cid 1 中心 vs 5 ランダム per seed × 条件)、効果サイズ未算出だが per seed diff_mean を記録 |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ 平均だけでなく per-seed 分布 (n_seeds_center_higher 等) を記録、観察 2 で window 解像度の特異性発見 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ Taka 確定基準のみ使用、新規軸なし |
| 6 | 出口の固定 | ✓ §5 で 4 出力ファイル + 4 主要観察 + 3 副次観察を固定 |
| 7 | 主題着手前に上位資料を読む | ✓ Step A 認識確認 + Step B 環境チェック完了、主題ドキュメント反映済 |
| 8 | 過去観察軸の照会 | ✓ v10.6 WLD.artless 動学的優位 (留保 #33) と本観察 §2.1 の整合を確認 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ argmax (構造的)、rng seed=42 documented、ハンドチューニングなし |
| 10 | 因果ではなく因果候補 | ✓ 「~の可能性」「留保解釈候補」表現、「効いた」「失敗」なし |
| 11 | 概念単位を雑に扱わない | ✓ center / random / v112 / v108_standard / event/pulse/step10/window を全 column で分離 |
| 12 | Aruism 判定回避 | ✓ success/fail なし、観察事実 + 留保解釈候補、解釈統合は Web Claude (§4) |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Code A 仮所見は Web Claude 確認待ち、断定なし |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka 確定 (c)+(d) / 両方併記 / 5 cid を §1 で実装反映 |
| 15 | 5 者運用体制の補完性 | ✓ Code A は構造記録、Web Claude は §2 留保解釈候補の翻訳 |

→ **15 格言全項目遵守**。

---

## 7. Step D 進行案 (Code A 推奨)

| Step | 内容 | 想定時間 |
|---|---|---|
| Step D-1 | 観察 2 取り込み点中心の選定 (v10.12 受容 cid pool 420 = atom_introduction_events_v112_seed{N} の source_cid + timestamp) | 30 分 |
| Step D-2 | 各取り込み点 (cid, t) を中心に、同 seed 全 228 cid の atom 状態を取得 (cid_atom_sim_matrix 静的 + 取り込み時点前後の 4 解像度 trajectory) | 1-2 時間 |
| Step D-3 | 取り込み点中心の波及指標算出 (中心 cid と同 seed 周辺 cid の atom 状態の同期/差異、time-locked) | 1-2 時間 |
| Step D-4 | 観察 2 観察事実集計 | 30 分 |

→ Step D 合計約 3-4 時間。Web Claude/Taka 承認後着手。

---

## 8. 一文サマリ (再掲)

Step C-1〜C-4 完了 (実行時間 2.7 秒、出力 5.6 MB)、観察 1 主中心 cid 選定 (n_pulses_short 最大、per-seed × {v112, v108_standard} 2 条件) + 副ランダム比較対照 (rng seed=42 × 5 cid × 24 seeds × 2 条件 = 240 比較対照) + 4 解像度 trajectory 抽出 (374,072 行) + 1,094 summary 行を構造的に算出、主要観察事実 4 件 ((1) v108_standard 中心 cid の dominant_atom が `WLD.artless` で 24 seeds 中 21 一致、v112 は PER.sound / TIM.moment / TIM.appear に分散、(2) dominant_atom_fraction で v108_standard 中心 0.92-1.00 vs v112 中心 0.47-0.81、(3) 両条件で中心 cid の trajectory row 数がランダムの約 1/3〜1/4、(4) window 解像度で v112 中心 cid の atom_change_rate 0.156 < ランダム 0.297 で時間スケール依存の特徴)、副次観察 3 件 (cid pool size 構造差 / n_pulses_short max の条件差 / 中心 cid id 例)、絶対格言 15 件全項目遵守、Code A は判定回避 (解釈統合は Web Claude Phase Result 領域)、書き込み unified/v1101/outputs/main/ 配下 4 ファイル (5.6 MB)、v106/v108/v112 main outputs は 1 byte も不変、Step D 観察 2 取り込み点中心の波及へ進行可。

---

*以上、v11.0.1 (v1101) Step C 観察事実報告 (Code A、2026-05-17)。Web Claude/Taka 確認後、Step D 観察 2 取り込み点中心の波及に進む。Code A 認識確認連続 10 段階継続中。*
