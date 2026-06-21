# v12 M4 — first-divergence + per-CID 機構監査 (seed 0、GPT 案を実行)

日付: 2026-06-11 / off (GAIN=0) vs small (GAIN=0.5) を計装 re-run / `m4_first_divergence.py`, `m4_analyze.py`

GPT/Web Claude 案: CID 数でなく「θ がどこで分岐するか」「処置 (bonus) 対象を tag して残った CID 間の差・消えた CID の死因」で個性化 vs 寡占を判定する。M3 報告の集計依存・bonus 未 tag・最終行比較の問題 ([[final-state-hides-divergence]]) を是正。

## 計装 (すべて実験側 audit、CID 公式レコード外)

- per realizer-step の θ md5 (off/small を diff → θ 分岐 step を確定)
- vl.step ごとの label territory + factor snapshot
- per-cid bonus tag (atomset_seed / event_count / bonus / factor / is_bonus_target、死んだ CID も逐次蓄積)
- **read-only sanity**: m4 off の per_subject は m3 off と完全一致 (25×152)。計装は動態に無害。

## 結果

### 1. θ first-divergence は外科的に clean (step 1001、ただ一点)

- θ md5 は **step 1〜1000 が off/small で完全一致**、**step 1001 で初めて分岐** (999/1000 一致、1001 不一致)。
- step 1000 = maturation 2×500。step_window (`v105:1658`) が内部で vl.step を呼ぶため bonus は maturation 中に育ち、**step-1000 境界の vl.step が初めて factor>1 を載せる** (snapshot window 2 で factor>1 初出、6 label)。
- → 分岐は「最初の factor>1 適用」と時刻まで一致し、それ以前に分岐は一切ない。M3 の「population まるごと変化」より遥かに強い因果特定: **唯一の入口・時刻局在・それ以前ビット同一**。

### 2. bonus の到達は「ほぼ全 CID」、magnitude のみ頻度勾配 (← 設計レベルの所見)

| 区分 | event_count | factor |
|---|---|---|
| 最活発 cid0 | 32 | 1.190 |
| 中位 cid3/9/10/15 | 21-22 | 1.169-1.172 |
| 低活動 cid1/6/8 | 1 | 1.023 |

- small で event を持つ **全 19 CID が bonus 対象** (factor>1)。off も同様 (28)。**非対象 CID は存在しない** (matched 16/16 が対象、ghost も全数が対象)。
- factor は 1.023〜1.190 (std 0.057)。**到達は普遍的、強度だけ頻度で勾配**。
- → 現 Atomset 設計 (誕生 + pulse + α/β + c_conv + 死、ほぼ全 event で頻度積算) は **少数 CID を選択的に照らす個性化圧ではない**。ほぼ全員を底上げし、忙しい CID をやや多めに底上げするだけ。**個性化を生むには「選択性」が足りない可能性**を示す。

### 3. M3 の "first-divergence link" を訂正

- M3 で「最初に分岐する link」とした `(1335, 2701)` は、**bonus territory の外** (両 node とも、直接 torque された cid0/2/3/4/5/7 の 18 node に非所属)。
- これは link_life を birth_step で整列した時の **「最も早く誕生した・記録が異なる link」** であって、**因果的な起点ではない**。因果起点は step 1001 に torque された node 群。θ 摂動が flow/Kuramoto/gravity で伝播してこの link の寿命 (44→108 step) に届いた、下流の現れ。
- → 「最終/整列順の first」と「因果的 first」を混同していた。θ md5 による step-1001 特定が正しい因果起点。

### 4. 残った CID 間の差・死因 — 系統的方向なし

- matched 16 CID (全 bonus 対象): **寿命 ↑4 / ↓4、Δlife 平均 −0.06、Δcoher 平均 −0.060**。
  - 生かされた例 cid4/7 (ghost→hosted)、殺された例 cid3/11/12/13 (hosted→ghost)。
- 全 CID が bonus 対象なので「boost された者が勝った (寡占)」「boost されぬ者が死んだ」という構図は **検証不能 (対照群が存在しない)**。
- death = host 喪失のみ (smoke 短く reap なし)。ghost は off/small とも全数 bonus 対象。
- → torque は **カオス競争を再分配** する。seed 0・GAIN 0.5 では **個性化の系統方向も寡占の系統方向も無い**。むしろ coherence は僅かに減 (個性化と逆向きの兆候)。

## 妥当性 (M4 で更新)

- **強まった**: 入口隔離・時刻局在の因果特定 (θ step-1001、それ以前ビット同一)。技術的 PASS は盤石。
- **新たに判明 (やや否定的)**: 現設計の bonus は **near-universal で選択性が無く、seed 0 では個性化を駆動していない**。survival 再分配は対称、coherence 微減。
- **依然 未判定**: 複数 seed での符号 ([[smoke-seed0-not-absolute]])、成熟相 (smoke は全て warmup<20window)、GAIN を上げた時の選択性発現。

## 含意・次の判断材料

> M4 は「配線は外科的に clean に効くが、現 Atomset 設計は **ほぼ全 CID を一様に底上げするため個性化圧として弱い**」ことを示した。個性化を狙うなら設計を **選択的** にする方向 (例: rank_1 一致度上位のみ bonus / bonus contrast を非線形に / event 種を絞る) を検討すべき。これは GAIN を上げる前に **設計の選択性** を問う話。

判断は Web Claude view へ。24 seeds main は未着手 ([[smoke-then-pause]])。

## ファイル
- `m4_first_divergence.py` / `m4_analyze.py`
- `run_m4/{off,small}/` (theta_checksums.csv, label_window_snapshot.json, cid_bonus_tags.csv)
- `run_m4/analysis.json`
