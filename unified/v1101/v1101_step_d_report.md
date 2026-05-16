# v11.0.1 (v1101) Step D 観察事実報告 — 観察 2「取り込み点中心の波及」

*作成*: 2026-05-17、Code A
*親*: `v1101_phase_design.md` (Web Claude 2026-05-16 改訂版) + `v1101_step_c_report.md` (Step C 観察 1 完了) + Taka Step D 承認 (2026-05-17)
*対象*: Web Claude (Phase Result 翻訳用素材) + Taka (確認)
*目的*: Step D-1〜D-4 観察事実報告、judgment 回避、Web Claude 翻訳要素材

---

## 0. 一文サマリ

Step D-1〜D-4 完了 (実行時間 48.3 秒、書き込み `unified/v1101/outputs/main/` 配下 3 ファイル計 1.3 MB)、観察 2 取り込み点列挙 (atom_introduction_events_v112 24 seeds = **10,500 events**、Taka 確定 (a) v10.12 受容 cid pool 420 中心) + step10 解像度の Δt ∈ {-100, -90, ..., +100} 21 点 ±100 step 窓内で周辺 cid (同 seed 全 ~228 cid のうち t に生存する平均 27.7 cid) の atom 状態 time-locked 抽出 + 波及指標算出 (周辺 cid のうち atom_intro 一致 cid 数 / 比率 / atom 分布エントロピー / 中心 cid 自身の atom_intro 一致) → 220,500 (event × Δt) 行 + per (atom × Δt) 集約 525 行、主要観察事実 4 件: (1) **取り込み atom 25 種類のうち中心 cid 自身が atom_intro を rank_1_atom として表現するのは PER.sound (peak 84.8% at Δt=+20)、PRP.bright (peak 49.3% at Δt=-90)、TIM.appear (peak 14.8% at Δt=-100)、WLD.artless (peak 8.8% at Δt=+70) の 4 atom のみ、残り 21 atom は center_match_rate ほぼ 0%** で取り込み atom が中心 cid を支配できない構造、(2) **周辺 cid の atom 分布で PER.sound と WLD.artless が突出**: per (event, Δt=0) で平均 8.4 cid が PER.sound、8.0 cid が WLD.artless を rank_1_atom として表現 (n_cids_alive 27.7 中 60% を 2 atom で占有)、(3) **atom 分布エントロピーが Δt 方向で単調減少**: Δt=-100 で 2.138 bits → Δt=+100 で 2.070 bits (0.068 bit 減少、ESDE 系全体の atom 分布が取り込みイベント後に集中化、log2(25)=4.64 bits 最大の約 45%)、(4) **PER.sound の波及プロファイル特異**: 中心 cid の PER.sound 一致が Δt=-10 で 32.6% → Δt=0 で 56.9% → Δt=+10 で 79.1% → Δt=+20 で 84.8% (peak) → Δt=+50 で 62.1% → Δt=+100 で 66.0% — 取り込み直後にピーク到達、その後減衰、Code A は判定回避 (解釈統合は Web Claude Phase Result 領域)、4 atom (PER.sound / PRP.bright / TIM.appear / WLD.artless) の波及プロファイル差は構造的事実、Step E 観察 3 補助平均統計 (CID/Integration/ESDE 3 単位) へ進行可。

---

## 1. Step D 構造的成果

### 1.1 観察 2 取り込み点列挙 (D-1、Taka 確定 (a) v10.12 受容 cid pool 420)

| 項目 | 値 |
|---|---:|
| 全取り込みイベント数 | **10,500** (24 seeds 合計) |
| per seed 平均 | 437.5 (range 325-575、std 75.9) |
| unique source_cid (seed-coupled) | **420** = v10.12 受容 cid pool (確認、Step B §2 と整合) |
| atom_id 種類 | 25 (TARGET_ATOMS) |
| timestamp 範囲 | 200 - 22,479 step |
| t0 整列 | round(timestamp / 10) × 10 で step10 grid に整列 |

### 1.2 周辺 cid atom 状態抽出 (D-2、step10 解像度 ±100 step)

| 項目 | 値 |
|---|---:|
| Δt 範囲 | {-100, -90, ..., 0, +10, ..., +100} = **21 点** |
| (event × Δt) ペア数 | 220,500 |
| per (event, Δt) で観測される alive cid 数 | 平均 27.7 (max 228、t 早期は少数) |
| 入力 trajectory | `step10_cid_alignment_seed{0..23}.csv` × 24 seeds |

### 1.3 波及指標算出 (D-3、11 列の per (event, Δt) 集計)

集計列:
- `n_cids_alive` — t における生存 cid 数
- `n_cids_matching_atom_intro` — そのうち rank_1_atom = atom_intro の cid 数
- `match_fraction` — n_match / n_alive (周辺 cid のうち取り込み atom 一致比率)
- `n_unique_atoms` — t における rank_1_atom 種類数
- `atom_entropy_bits` — Shannon エントロピー (bits、低いほど集中)
- `mean_rank_1_sim` — 周辺 cid の rank_1_sim 平均
- `center_alive` — 中心 cid (source_cid) が t に生存しているか
- `center_rank_1_atom` — 中心 cid の rank_1_atom (生存時)
- `center_rank_1_sim` — 中心 cid の rank_1_sim
- `center_atom_matches_intro` — 中心 cid 自身が atom_intro を rank_1 として表現するか

### 1.4 集約 (D-4、per (atom × Δt) summary 525 行)

per (atom_intro × delta_t) で 11 指標を mean / median / std 等で集約。出力: `observation_2_summary.parquet` (19 KB)。

---

## 2. 主要観察事実 4 件 (Web Claude 翻訳用素材)

### 2.1 観察 1: 取り込み atom 25 種類中 4 atom のみ中心 cid を支配可

| atom_intro | center_match_rate peak | peak での Δt | 全 Δt 範囲での mean |
|---|---:|---:|---:|
| **PER.sound** | **84.8%** | +20 | 32.6% - 84.8% |
| **PRP.bright** | **49.3%** | -90 | 8.8% - 49.3% |
| **TIM.appear** | 14.8% | -100 | 0% - 14.8% |
| **WLD.artless** | 8.8% | +70 | 1.4% - 8.8% |
| COG.learn / EXS.being / EXS.nonbeing / COM.silence / BOD.ear / FND.timeless / FND.transformation / PER.feel / PER.fragrance / PER.hear / PER.smell / PER.taste / PER.soundless / SOC.nation / SOC.public / SOC.city / WLD.culture / WLD.technique / PRP.deep / PRP.sharp / PRP.multiple | **0% (全 Δt)** | — | 0% (全 Δt) |

**観察事実**:
- 25 種類の取り込み atom のうち、中心 cid が rank_1_atom として表現できるのは **4 atom のみ** (PER.sound / PRP.bright / TIM.appear / WLD.artless)
- 残り **21 atom は center_match_rate = 0% (全 Δt 範囲)** — 取り込みイベントが発生しても中心 cid の rank_1_atom は別の atom のまま
- 中心 cid 受容できる atom は **構造的に制限** されている
- 留保解釈候補 (Web Claude 領域): 中心 cid の atom 状態は v10.6 cid_atom_sim_matrix の cosine 類似度地形に依存、25 取り込み atom のうち cid の "atom 受容窓" に入るのは少数

### 2.2 観察 2: 周辺 cid の atom 分布で PER.sound と WLD.artless が突出

| atom_intro | per (event, Δt=0) 周辺 cid 平均 match 数 | match_fraction 平均 |
|---|---:|---:|
| **PER.sound** | **8.37 cids** | **32.2%** |
| **WLD.artless** | **8.02 cids** | **30.1%** |
| PRP.bright | 1.75 cids | 7.6% |
| EXS.being | 1.61 cids | 4.9% |
| WLD.culture | 1.59 cids | 4.9% |
| FND.timeless | 1.35 cids | 4.0% |
| TIM.appear | 0.05 cids | 0.0% |
| その他 18 atom | 0.05 - 0.45 cids | < 1.6% |

**観察事実**:
- per (event, Δt=0) で生存する平均 27.7 cid のうち、PER.sound と WLD.artless が周辺 cid の rank_1_atom として **合計 ~60%** を占有 (8.4 + 8.0 = 16.4 / 27.7)
- どの atom を取り込んでも、周辺 cid の atom 状態は **常に PER.sound + WLD.artless が支配的**
- これは「**取り込みイベント前後の atom 分布は取り込み atom にほぼ依存しない**」を意味する
- v10.6 cross_seed_event_atom_distribution の上位 (WLD.artless 26.2% / PER.sound 25.9%、本 Step D §2.2 と整合) と本観察事実は構造的に一致
- 留保解釈候補 (Web Claude 領域): ESDE 系全体の atom 状態は PER.sound と WLD.artless が「**基底支配 atom**」として常時優位、取り込みイベントはこの基底分布を僅かに変化させるが大きく覆さない

### 2.3 観察 3: atom 分布エントロピーが Δt 方向で単調減少 (取り込み後集中化)

| Δt | atom_entropy_bits (mean over 25 atoms) |
|---:|---:|
| -100 | 2.138 |
| -50 | 2.137 |
| 0 | **2.104** |
| +10 | 2.098 |
| +50 | 2.078 |
| +100 | 2.070 |

**観察事実**:
- Δt=-100 から +100 まで atom_entropy_mean が **単調減少** (2.138 → 2.070、0.068 bit = 3.2% 減少)
- log2(25) = 4.64 bits 最大 (全 atom 等分布)、実測 2.07-2.14 bits は **約 45-46%** (集中度高)
- 取り込みイベント後に **ESDE 系全体の atom 分布が集中化方向に動く** 構造
- 留保解釈候補: 取り込み atom 自体が分布を集中化させるのではなく、**Δt 増加に伴う自然な動学的集中化** の可能性 (取り込みイベント独立効果ではない可能性)、より厳密には Δt=0 前後を比較する randomized baseline が必要 (Step F 段階 2 検討)

### 2.4 観察 4: PER.sound の波及プロファイル特異 (取り込み直後ピーク)

| Δt | center_match_rate (中心 cid PER.sound 一致率) |
|---:|---:|
| -100 | 30.0% |
| -50 | 22.4% |
| -10 | 32.6% |
| 0 | **56.9%** |
| +10 | **79.1%** |
| **+20** | **84.8%** ← peak |
| +30 | 70.0% |
| +50 | 62.1% |
| +100 | 66.0% |

**観察事実**:
- PER.sound 取り込み (420 events) で中心 cid 自身の rank_1_atom が PER.sound になる確率が:
  - 取り込み前 (Δt=-10): 32.6%
  - 取り込み時刻 (Δt=0): 56.9% (+24.3 ポイント)
  - 取り込み 10 step 後 (Δt=+10): 79.1% (+46.5 ポイント from baseline)
  - 取り込み 20 step 後 (Δt=+20): **84.8% (peak、+52.2 ポイント from baseline)**
  - その後 Δt=+50 で 62.1% に減衰
- **取り込みイベントが中心 cid の rank_1_atom を一時的に強く変化させる**、PER.sound はその効果が最大
- 留保解釈候補: PER.sound は中心 cid の "atom 受容窓" に強くフィットする atom、PRP.bright も類似 (peak 49.3%) だが Δt=-90 で peak — 取り込み atom 自身の効果ではなく時間方向の自然変動の可能性
- PRP.bright の peak Δt=-90 は取り込み前なので「事前にすでに PRP.bright だった cid に PRP.bright が取り込まれた」可能性 (selection bias 兆候、要追加検証)

---

## 3. 副次観察 (Web Claude 必要時翻訳用)

### 3.1 受容 cid pool 420 の確認

D-1 で `atom_introduction_events_v112_seed{0..23}` の source_cid を集約: per seed 平均 17.5 cid (range 13-23)、24 seeds 合計 420。Step B §2 / v10.12 完了報告 §2.1 と完全整合。

### 3.2 per (event, Δt) の n_cids_alive 平均 27.7

per (event, Δt) で生存している cid 数は **平均 27.7** (max 228 = 全 cid)。取り込みイベントは t0 ∈ [200, 22479] に分散、t0 が小さいほど生存 cid 数も少ない (run 序盤)、t0 が大きいほど多い構造。本 Step D 集計は t0 各点の生存 cid 集合に依存。

### 3.3 center_alive_rate = 1.0 (全 Δt)

中心 cid (source_cid) は受容 cid pool 420 = lifespan ≥ 977 の長寿 cid から選ばれているため、±100 step 窓内で常時生存 (center_alive_rate = 1.0、全 Δt 範囲)。

### 3.4 21 atom の center_match_rate = 0% の構造

22 atom (前掲§2.1) は **全 Δt 範囲で center_match_rate = 0%**。これらの atom が取り込まれても、中心 cid (source_cid) の rank_1_atom が変化することはない。
- 例: COG.learn が source_cid=22 に取り込まれても、cid 22 の rank_1_atom は PER.sound や WLD.artless のまま (cid の atom 受容窓に COG.learn が入らない)

留保解釈候補: 取り込み機構 v10.8/v10.12 は Q/C エネルギーコスト + cid_atom_sim 構造で動作、atom_intro の効果は cid の事前 atom 適合度に依存する設計。Web Claude 解釈領域。

---

## 4. 観察事実の解釈規律遵守 (絶対格言 #10, #12)

Code A は本観察事実を以下のように **断定しない**:

- 観察事実: 25 取り込み atom 中 4 atom のみ中心 cid を支配可、21 atom は center_match_rate = 0%
- 主題評価 (NOT Code A 領域): 「PER.sound が ESDE で最も影響力のある atom」「取り込み機構は限定的にしか機能していない」等の解釈統合は **Web Claude Phase Result 領域**
- Code A 領域: 構造的事実 + 留保解釈候補の提示 + selection bias 注意喚起 (§2.4 PRP.bright Δt=-90 peak、§2.3 取り込み独立効果か自然動学かの区別必要性)

success/fail 判定なし、4 主要観察 + 4 副次観察を Web Claude 翻訳の素材として提供。

---

## 5. 出力ファイル仕様 (1.3 MB)

| ファイル | サイズ | 行数 | 用途 |
|---|---:|---:|---|
| `observation_2_events.parquet` | 165 KB | 10,500 | 取り込み点一覧 (seed × event_id × source_cid × timestamp × atom_id + state) |
| `observation_2_propagation.parquet` | 1.1 MB | 220,500 | per (event × Δt) で 11 列の波及指標 |
| `observation_2_summary.parquet` | 19 KB | 525 | per (atom × Δt) の集約 |

書き込みは `unified/v1101/outputs/main/` 配下のみ、`developmental/v106/v108/v112` の main outputs は **1 byte も変更していない** (Step G で bit-identity 層 B 検証予定)。

---

## 6. 規律遵守自己点検 (絶対格言 15 件)

| # | 格言 | 本 Step D での遵守 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | ✓ §1-3 で構造的事実先、§4 で解釈規律 |
| 2 | 物理層 frozen 絶対 | ✓ v106/v108/v112 main outputs read-only、書き込み unified/v1101/ 配下のみ |
| 3 | ベースライン比較 + 効果サイズ | △ Δt=-100 vs +100 で entropy 差 0.068 bit を記録、より厳密な randomized baseline は段階 2 検討 (§2.3 留保) |
| 4 | 集団平均の罠 / n_core 別層化 | ✓ atom_intro 別 + Δt 別の per-event ベース集計、平均だけでなく peak Δt も記録 |
| 5 | 観察軸を増やすことを駆動要因にしない | ✓ Taka 確定基準 (受容 cid pool 420 中心 + step10 解像度 + 同 seed 全 cid 周辺) のみ、新規軸なし |
| 6 | 出口の固定 | ✓ §5 で 3 出力ファイル + 4 主要観察 + 4 副次観察を固定 |
| 7 | 主題着手前に上位資料を読む | ✓ Step C 報告 + 主題ドキュメント反映済 |
| 8 | 過去観察軸の照会 | ✓ §2.2 で v10.6 cross_seed_event_atom_distribution 上位 (WLD.artless / PER.sound) と本観察整合確認 |
| 9 | 神の手回避 + Pulse 同一フォーマット | ✓ Δt grid 構造的選定、atom 集計は全 25 atom 一括処理、ハンドチューニングなし |
| 10 | 因果ではなく因果候補 | ✓ 「~の可能性」「留保解釈候補」「selection bias 兆候」表現、断定なし |
| 11 | 概念単位を雑に扱わない | ✓ source_cid / 中心 cid / 周辺 cid / atom_intro / rank_1_atom を全 column で分離 |
| 12 | Aruism 判定回避 | ✓ success/fail なし、観察事実 + 留保解釈候補、解釈統合は Web Claude (§4) |
| 13 | AI を信じない原則は Taka 個人のみ | ✓ Code A 仮所見は Web Claude 確認待ち、断定なし |
| 14 | Taka 直感優先 + 直感語保存 | ✓ Taka 確定 (a) 受容 cid pool 420 中心、(b) 不採用 を §1.1 で実装反映 |
| 15 | 5 者運用体制の補完性 | ✓ Code A は構造記録、Web Claude は §2 留保解釈候補の翻訳 |

→ **15 格言全項目遵守** (#3 は段階 2 で適用候補)。

---

## 7. Step E 進行案 (Code A 推奨)

| Step | 内容 | 想定時間 |
|---|---|---|
| Step E-1 | 観察 3 CID 単位平均統計 (24 seeds 集約の cid_atom_sim_matrix 分布、各 326 atom の cid 別濃度分布) | 30 分 |
| Step E-2 | 観察 3 Integration 単位 (β top-K 既存集約 + member_cids 完全 atom ベクトル分布、α pattern_class 同様) | 1 時間 |
| Step E-3 | 観察 3 ESDE 単位 (24 seeds 横断 atom 隆盛 + cross_seed_dynamic_atom_emergence の 4 解像度時系列) | 30 分 |
| Step E-4 | 観察 3 集計 + 観察事実報告 | 30 分 |

→ Step E 合計約 2-3 時間。Web Claude/Taka 承認後着手。

---

## 8. 一文サマリ (再掲)

Step D-1〜D-4 完了 (実行時間 48.3 秒、出力 1.3 MB)、取り込みイベント 10,500 (24 seeds × 受容 cid pool 420 × 25 atom) を step10 解像度 Δt ∈ ±100 step (21 点) 窓内で周辺 cid (平均 27.7 cid alive) の atom 状態と time-locked 抽出、220,500 (event × Δt) 行 + 525 (atom × Δt) summary 行、主要観察事実 4 件: (1) 25 取り込み atom 中 4 atom のみ中心 cid 支配可 (PER.sound peak 84.8% / PRP.bright peak 49.3% / TIM.appear peak 14.8% / WLD.artless peak 8.8%)、残り 21 atom は center_match_rate = 0% 全 Δt、(2) 周辺 cid の atom 分布は取り込み atom に依存せず PER.sound + WLD.artless が常時 ~60% を占有 (per (event, Δt=0) 各 8.4 / 8.0 cid)、(3) atom_entropy_mean が Δt 方向単調減少 2.138 → 2.070 bits (取り込み後集中化、ただし取り込み独立効果か自然動学かは段階 2 検証)、(4) PER.sound 波及プロファイル特異 (中心 cid 一致率 Δt=-10 で 32.6% → Δt=+20 で 84.8% peak → Δt=+50 で 62.1% 減衰、取り込みイベントが中心 cid の rank_1_atom を一時的に強く変化させる構造)、副次観察 4 件 (受容 cid pool 420 確認 / per (event,Δt) n_cids_alive 平均 27.7 / center_alive_rate 1.0 / 21 atom center_match 0% の構造)、絶対格言 15 件全項目遵守、Code A は judgment 回避 (解釈統合は Web Claude)、書き込み unified/v1101/outputs/main/ 配下 3 ファイル (1.3 MB)、v106/v108/v112 main outputs 不変、Step E 観察 3 補助平均統計 (CID/Integration/ESDE 3 単位) へ進行可。

---

*以上、v11.0.1 (v1101) Step D 観察事実報告 (Code A、2026-05-17)。Web Claude/Taka 確認後、Step E 観察 3 補助平均統計に進む。Code A 認識確認連続 10 段階継続中。*
