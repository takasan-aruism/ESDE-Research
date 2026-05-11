# v10.x 全マイナーバージョン レビュー資料

*作成*: 2026-05-11、Code A
*目的*: v10.0 から v10.12 までの全マイナーバージョンの主題・実装・観察・留保を 1 本にまとめた俯瞰資料
*対象*: Taka (v10.x 系列の振り返り)
*親資料*: `docs/ai_summaries/06_developmental_summary.md` (v10.0-v10.9 詳細、1230 行) + `docs/ai_summaries/06b_developmental_phase15_summary.md` (v10.4-v10.12 詳細、683 行) のエッセンス集約

---

## 0. 全体マップ — 3 つの phase と 13 バージョン

| Phase | 期間 | バージョン | 全体テーマ |
|---|---|---|---|
| **Phase 1** | v10.0-v10.5 | 6 版 | ESDE 内部進化、物理層 frozen 絶対、機構の積み上げ |
| **Phase 1.5** | v10.6-v10.12 | 7 版 | ESDE Genesis × ESDE Language 統合、Atom 持ち込み機構 |
| Phase 1.5+ / Phase 2 | v10.13 以降 | 未定 | 会話系、現実接続 (構想段階) |

### 0.1 時系列一覧 (一文要約)

| ver | 主題 (一文) | 完了日目安 |
|---|---|---|
| **v10.0** | Developmental フェイズ宣言 + 4 層アーキテクチャ確定 + 死の二階層整理 | 2026-04-24 |
| **v10.1** | Minimal Ingestion (ghost を resource として扱う摂食機構の最小実装) | 2026-04-26 |
| **v10.2** | Probabilistic Cognitive-Conscious Balance (Q/C 比率による確率的認知/意識切替) | 2026-04-28 |
| **v10.3** | 双方向 E3 機構 + Integration 概念の導入 (cid 同士の意識層接触の入口) | 2026-04-29 |
| **v10.4** | Integration 独立化 (Layer 5 機構の本格実装、α-Integration) | 2026-04-30 |
| **v10.5** | α/β 階層分離 (Layer 5 完成、ダブルブッキング解消、Q/C 継承機構) | 2026-05-01 |
| **v10.6** | Genesis × Language Atom alignment 比較 (Phase 1.5 開始、観察解像度の多層化) | 2026-05-04 |
| **v10.7** | 発火と波及のオービス完成 (post-process 5 機能、Level 1-3 因果候補階層化) | 2026-05-05 |
| **v10.8** | Atom 単独持ち込み機構の最小実装 (Level 3.5、ESDE と外界の第一接点定量化) | 2026-05-06 |
| **v10.9** | 寄与候補感度評価 + 4 種設計表 (会話系設計のための部品調達) | 2026-05-08 |
| **v10.10** | Multi-gate × timing 多軸層化 (28 conditions、5 軸層化解析、観察延長への逸脱) | 2026-05-09 |
| **v10.11** | q_c_inherited 起点 within-cid 観察 (Phase 1.5 第六試行、v10.5 既知再観察に終わる) | 2026-05-10 |
| **v10.12** | Atom 取り込み prototype (人間言語 → atom 変換 prototype、v10.6 §7.1 で本来予定の主題への復帰) | 2026-05-11 |

---

## 1. Phase 1: ESDE 内部進化 (v10.0 - v10.5)

物理層 frozen 絶対、4 層アーキテクチャ (物理 / 存在 / 認知 / 意識) を確立して各層の機構を積み上げた段階。

### 1.1 v10.0 — Developmental フェイズ宣言 (2026-04-24)

- **主題**: ESDE 開発段階を「Cognitive」「Conscious」ではなく「Developmental」と命名、認知層と意識層の協働を主題化
- **主実装**: 4 層アーキテクチャの確定 (物理 / 存在 / 認知 / 意識)
- **主観察**: 死の二階層 (存在層死 = Label 死亡で ghost 化 / 認知層死 = Q=0 で消滅)、燃料概念は認知層 (Q) と意識層 (C) のみで定義
- **留保**: ghost の固定 TTL=10 を v10.1 で除去予定
- **次への接続**: v10.1 で ghost を resource として扱う具体実装へ

### 1.2 v10.1 — Minimal Ingestion (2026-04-26)

- **主題**: ghost を「死んだら消える」固定 TTL から「resource として食べられる」資源地形へ転換
- **主実装**: ghost.residual_Q (ghost 化時の Q 完全継承)、1 step 1 ghost 食べきりの摂食機構、空摂食許容、ghost ランダム選定 (seeded RNG)
- **主観察**: 摂食 3,588 件 / phantom contact 48,625 件 (摂食の 13.6 倍、想定外の規模)
- **留保**: phantom contact の規模 → Taka 整理で「物質的なもの」(主体性のない環境要因) と位置づけて主題化を却下、v10.2 で本来の主題へ
- **重要発見**: phantom = 「主体性のない認知層要素」が ESDE で初めて定義

### 1.3 v10.2 — Probabilistic Cognitive-Conscious Balance (2026-04-28)

- **主題**: 認知と意識を Q/C 比率で確率切替する機構、意識層の動作機構化
- **主実装**: 確率式 P(認知) = Q/(Q+C)、認知活動 (Q-1, C+1)、意識活動 (C-1, 摂食発動)、即時摂食 (案 B、step 内動的連鎖)
- **主観察**: 認知当選 56.79% / 意識当選 3.50% / skip 39.71%、phantom と空摂食が完全消失、C 上限なしでも暴走しない自己均衡
- **核心発見**: **n_core 別層化で構造的継承を観察** — n_core=2 (76%、寿命 1,716、意識発動率 10.1%) vs n_core=5 (12.2%、寿命 13,598、意識発動率 73.2%)、物理層由来の構造が認知→意識まで階層的に継承
- **留保**: 戦略二極化 (n_core=2/5 で対称的、3/4 は中間)、集団平均の罠を確認
- **規律**: 集団平均の罠 (層化解析必須)

### 1.4 v10.3 — 双方向 E3 + Integration 概念 (2026-04-29)

- **主題**: cid 同士の意識層レベル接触 (双方向 E3) を機構化、Integration を概念として導入 (機構は v10.4)
- **主実装**: 両者 hosted ∧ Q>0 ∧ C≥1 ∧ 同一 alive link 初回接触で両者 C-1
- **主観察**: 双方向 E3 fired 6,824 件、C 蓄積 27% 抑制 (観察ルールが動学を変える)、open triad 99% 支配、closed triad 1.4%、持続性ゼロ
- **三層構造の確定**: 機構 (双方向 E3) vs 観察される統計現象 (三項共鳴) vs 上位解釈 (Integration)
- **次への接続**: v10.4 で Integration を独立主体として機構化

### 1.5 v10.4 — Integration 独立化 (2026-04-30)

- **主題**: Integration を独立した主体として機構化、Layer 5 (cid 集団) の本格実装
- **主実装**: 誕生条件 4 種 (be3 / open_triad / closed_triad / third_overlap)、1 cid が複数 Integration 同時所属可、Q/C は最強結合 1 つに全継承、recorded/active 二層状態
- **主観察**: Integration 13,550 件誕生、trigger 比率 be3 52% / open_triad 38% / third_overlap 9% / closed_triad 0%、系の C 蓄積が v10.3 と逆方向に増加 (+31%)、ハブ cid (1 cid あたり所属 Integration max 102) が自然形成
- **留保**: closed_triad ゼロ問題 (be3 run-wide dedup の影響)、**ダブルブッキング問題** (cid X が 102 Integration に同時所属で Q/C 集計重複)
- **次への接続**: v10.5 で α/β 階層分離でダブルブッキング解消

### 1.6 v10.5 — α/β 階層分離 (Layer 5 完成、2026-05-01)

- **主題**: v10.4 のダブルブッキング問題を α/β 階層分離で構造的に解消、Layer 5 の動態完成
- **主実装**:
  - 機構 A: β-Integration (α-Integration を構成要素、cid 単一共有は最強 β に 1 個のみ所属、ghost 化時 Q/C は β に 100% 継承)
  - 機構 B: Salience-driven Focus (mass(X) = X.Q + X.C + β継承分)
  - 機構 C: Recorded からの漏れ (recorded β.C_inherited から ε=1 を主体 cid.C に転記)
- **主観察**: α 13,881 件 / β 2,009 件 (集約率 7:1)、最大 691α / 20cid が 1 β に統合 (hub β の自然形成)、M6 (1 cid → 1 β) 違反 0 件、Leakage event 232 件
- **核心成果**: **Layer 5 の構造的・動態的完成**、ダブルブッキング解消 (cid 重複所属 max 102 → 0)
- **次への接続**: Phase 1 完了、Phase 1.5 (Genesis × Language 統合) へ

---

## 2. Phase 1.5: Genesis × Language 統合 (v10.6 - v10.12)

ESDE Language 系 (2026-03 凍結) の Atom 326 を ESDE Genesis 系の cid と接続する段階。

### 2.1 v10.6 — Genesis × Language Atom alignment (2026-05-04、Phase 1.5 第一試行)

- **主題**: Atom 326 と cid 5,224 の 48 次元 cosine 類似度比較、observer pattern を post-process として実装
- **主実装**: 6 段階解析 (静的 / 層化 / ベースライン / window trajectory / per-pulse / step10) で cid × atom 比較
- **主観察**:
  - 真の構造的特異性 26 atom (実データ照合で 25 atom、WLD.artless 留保): PER.sound +25.85%、WLD.artless +24.55% 等
  - 真の構造的盲点 7 atom: TIM.moment -54.11%、COM.conduct -6.49% 等
  - 24 seeds 完全一致の動学的発展段階: WLD.artless (0-1000) → TIM.appear (1000-4000) → WLD.artless (4000-15000) → EXS.being (15000-25000)
  - 観察解像度 (静的/window/per-pulse/step10) で見える特徴が異なる多層構造
- **留保**: 「持ち込んだはいいけど効果測定ができない、オービスがない状態」
- **次への接続**: v10.7 でオービス (測定器) を作る

### 2.2 v10.7 — 発火と波及のオービス完成 (2026-05-05、Phase 1.5 第二試行)

- **主題**: 効果測定の準備 (オービス) を post-process で完成
- **主実装**: post-process 5 機能 (event_aggregator / path_analyzer / baseline_constructor / avalanche_monitor / orchestrator)、5 種 source_event (pulse / ingestion / α_formation / β_formation / c_conversion)、5 種 baseline、Level 1-3 因果候補階層化
- **主観察**:
  - **medium window (100-1000 step) 支配**: peak_lag 250-300、「考える時間を持つ系」
  - path 順位: **temporal_coactivation > Integration > familiarity > attention**
  - source-specific 性 94% 有意差 (event 種別ごとに systematic に異なる経路)
  - 意識発動の no_signal (integration_α/β で意識は波及しない、構造的に「孤独」)
  - small-world 構造 (共鳴ループ 2-hop 14,343 / 3-hop 110,103)
- **規律**: 因果候補の階層化 Level 1-4、5 種 baseline 必須、アバランシェ防止、構造語徹底
- **次への接続**: v10.8 で「速度違反チェック」(Atom 持ち込みの効果測定)

### 2.3 v10.8 — Atom 単独持ち込み機構 (2026-05-06、Phase 1.5 第三試行、Level 3.5)

- **主題**: Atom を ESDE に持ち込んで効果測定 (Level 3.5)
- **主実装**: atom_introduction_event を source_event 第 6 種として追加、top_k 100 cid × 25 atom × 24 seeds = 60,000 events、Q-1/C+1 を post-process 計算的減算 (物理層 frozen 維持)
- **主観察**:
  - **Atom 持ち込み機構が ESDE で動作する** (機構レベルの証明、60,000 events 安定発火)
  - **ESDE は atom 種別を構造的に識別する**: familiarity 経路 effect_size 6.83 (2.1 倍差)
  - **経路の機能分担**: familiarity = 意味識別経路、temporal_coactivation = 意味中立の運搬経路
  - **外部入力と自然発火の境界線**: 20/22 finding で introduced < natural (atom event は natural の半分)
  - 誤差分布で正規分布 0%、bimodal 17.4%
- **留保**: introduced < natural の原因未分離、Whiteout 真の検出未実施、bimodal 原因未解析
- **次への接続**: v10.9 で寄与候補感度評価 + bimodal 構造解析

### 2.4 v10.9 — 寄与候補感度評価 + 4 種設計表 (2026-05-08、Phase 1.5 第四試行)

- **主題**: v10.8 主要発見の 2 つの未解決点 (introduced < natural、bimodal 17.4%) を分離評価、**会話系設計のための部品調達**
- **主実装**: 3 新条件 (A2: Q-2/C+2、B3: random cid、C2: 案 b リズム同調 age=200 発火)、v10.8 標準 (A1, B1, C1) 流用
- **主観察**:
  - **「強反応する cid は若い cid」**: H3_lifecycle 60.2% 支配、cid age median 227
  - 感度階層: **timing > cid_selection > QC_cost** (timing が cid_selection の 6 倍、QC_cost は評価不能)
  - **「Integration 外の高 familiarity cid」が最強・最 robust の入力経路** (timing 感度 0.222)
  - C2 (若い cid 発火) で pulse 活動が大効果量で活発化 (short 0.97 / medium 0.75)
  - **構造軸と感度軸の直交性** (bimodal 支配性 ≠ 感度の強さ)
- **4 種設計表 (出口の固定)**:
  1. sensitivity_summary
  2. receptivity_detection_criteria: cid age ≤ 560 + Integration 外 + 高 familiarity
  3. input_routing_criteria: high_fam_out PREFER
  4. natural_likeness_design_criteria
- **次への接続**: 4 種設計表を踏まえて v10.10 主題選定 (条件適応型 atom 導入 / high_fam_out 構造解明 / 常駐アンカー実装 / B 群試験 / QC_cost 本格評価)

### 2.5 v10.10 — Multi-gate × timing 多軸層化 (2026-05-09、Phase 1.5 第五試行)

- **主題**: v10.9 の 4 種設計表を統合した「条件適応型 atom 導入の本格実装」、Multi-gate × timing 二次元設計
- **主実装**: 28 conditions (主軸 5 × 3 timing + 観察用 2 × 3 + controls 2 × 3 + bit-identity 1)、9 GATES (ABC/ABc/AB/B/Bc/AC/BC/A/all_pass) × 3 AGE_TARGETS (200/300/500) + v108_re (v10.8 再現)、5 軸層化解析 (A: Integration α/β / B: cid 寿命 + n_core / C: 25 atom 個別 + category / E: window × n_core_bin / F: seed 別ばらつき)
- **主観察**:
  - **長寿 cid (Q4: lifespan ≥ 2,485) で timing_axis -0.196 / v110_vs_v108re +0.214 と効果大**
  - atom category で効果に大差: BOD/COM/EXS が +0.2-0.4、WLD/TIM が +0.01-0.02 (1 桁差)
  - **n_core 別反応 type 分業** (§3.4): bin_2 (76%) = pulse 系 / bin_5+ (12%) = delta_C 系
  - window × n_core: short/medium で bin_5+ -0.21 (大効果)、immediate で n_core 差小
  - gate_effect は seed 間ばらつき大 (tied 多発)、pulse 系は seed 間収束
- **逸脱パターン**: **観察軸の延長に傾倒** (28 conditions、5 軸層化)、本来の「会話系」主題から外れた観察延長になりがち
- **次への接続**: v10.11 で「受信機構の解明」へ (v10.5 既知再観察に終わる)

### 2.6 v10.11 — q_c_inherited 起点 within-cid 観察 (2026-05-10、Phase 1.5 第六試行)

- **主題**: v10.5 機構 A (β に Q/C 100% 継承) の動態を直接観察、受信機構の解明
- **主実装**: q_c_inherited 起点で within-cid 観察 (β member cid の C 値変化追跡)、response_profile_compiler
- **主観察**:
  - 24 seeds 一貫して β member cid の C 値が正方向に動く (delta_C +0.097〜+0.497、全 12 cells)
  - ただし **これは v10.5 機構 A の既知挙動の再観察に過ぎなかった** (留保 21 として記録)
- **完了レポート §5.1**: 「v10.12 主題 = 人間言語 → atom 変換 prototype (Atom 取り込み prototype) に戻る」(Taka 確定)
- **逸脱パターン**: 「受信機構解明」が v10.5 既知事実の自明な再観察になった
- **アルイズム原則 (Aruism)**: 「予想と違えば再観察」を §5.2 末尾で確立
- **次への接続**: v10.12 で v10.6 §7.1 本来予定の主題 (Atom 取り込み prototype) へ復帰

### 2.7 v10.12 — Atom 取り込み prototype (2026-05-11、Phase 1.5 第七試行、完了)

- **主題**: 人間言語 atom を ESDE cid に「擦り付ける」prototype の動作確認、v10.6 §7.1 本来予定への復帰、v10.11 §5.1 直接出発点
- **主実装** (10 段階):
  - Step Z 事前調査 (Q-Z1〜Q-Z7、4 条件母集団)
  - Step B 環境チェック詳細
  - Step A 再実施 (第 5 版主題認識、cond4 top 50% 緩和)
  - Step C `v112_receptive_cid_detector.py` (4 条件複合 cid 検出: ¬β + lifespan ≥ 977 + n_core ≥ 5 + fam ≥ top 50%、24 seeds total **420 cid**)
  - Step D `v112_atom_event_generator.py` (25 atom × cid burst = **10,500 events**)
  - Step E `v112_baseline_recalculator.py` + `v112_propagation_analyzer.py`
  - Step F `v112_observation_recorder.py` (Aruism 整合、3 段階判定廃止)
  - Step G `v112_orchestrator.py` + smoke 全工程 bit-identity 検証
  - Step I main run (20.35 秒)
  - Step J `v112_cross_seed_analyzer.py` (paired_d / sign_test / bootstrap CI、留保 #27 formal)
  - Step K `v112_completion_report.md` (主題完了)
- **主観察**:
  - 構造的予想 6/6 全 matched (cid pool 420 / events 10,500 / bin_5+ 100% 等)
  - **唯一 n_pulses_short のみ paired_d +1.36 / sign_test p=0.0000 / bootstrap CI [+0.054, +0.094] で頑健 v112 > v108_standard**
  - 他 6 metric (delta_C_medium / delta_Q_medium / 4 path_excess) は全て CI が 0 を跨ぎ方向性なし
  - smoke seed 0 と main 24 seeds で **4/7 metric (path_excess 4 種全て) cohens_d 符号反転** (Aruism 発動)
- **追加調査 (window post-process、2026-05-11、本日)**:
  - immediate window (1-10 step) で **delta_C 頑健 v112 > v108_standard** (paired_d +0.5377, sign_p 0.0066)
  - n_pulses が window 依存で **方向反転** (immediate -0.94 / short +1.36 / medium +1.31、全て頑健)
  - Step J 設計盲点を formal evidence 化 (Step J は delta_C/Q を medium のみ、n_pulses を short のみで集計)
- **留保**: 累計 27 件 (継承 22 + 新規 5: #23-#27)
- **次への接続**: v10.13 主題選定 (留保 #27 派生 4 案 + window 依存性主題 + smoke 複数 seed 運用改善)

---

## 3. 系譜図 — 何が引き継がれたか

```
v10.0 ── フェイズ宣言、4 層アーキテクチャ
   │
v10.1 ── 摂食機構、ghost = resource、「物質的なもの」概念
   │
v10.2 ── 確率的認知/意識切替、n_core 階層的継承
   │       (集団平均の罠、層化解析必須)
   │
v10.3 ── 双方向 E3、Integration 概念
   │       (機構 vs 観察 vs 解釈 三層分離)
   │
v10.4 ── Integration 独立化、ダブルブッキング問題発生
   │       (ハブ cid 自然形成)
   │
v10.5 ── α/β 階層分離 (Layer 5 完成)
   │       Phase 1 完了 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   │
v10.6 ── Atom alignment 比較 (Phase 1.5 開始)
   │       観察解像度の多層化、25 atom 確定
   │       残課題: オービスがない
   │
v10.7 ── オービス完成 (post-process 5 機能)
   │       Level 1-3 因果候補階層化、medium window 支配
   │       path 順位 (temporal > Integration > familiarity > attention)
   │
v10.8 ── Atom 持ち込み機構 (Level 3.5)
   │       60,000 events、familiarity = 意味識別、temporal = 意味中立
   │       introduced < natural (留保)、bimodal 17.4% (留保)
   │
v10.9 ── 寄与候補感度評価、4 種設計表
   │       「Integration 外 + 高 familiarity」最強、cid age ≤ 500
   │       会話系設計の部品調達完了
   │
v10.10 ─ Multi-gate × timing 28 conditions (観察延長への逸脱)
   │       n_core 反応 type 分業 (bin_2 = pulse / bin_5+ = delta_C)
   │
v10.11 ─ q_c_inherited within-cid 観察 (v10.5 既知再観察に終わる)
   │       Aruism「予想と違えば再観察」確立
   │
v10.12 ─ Atom 取り込み prototype (v10.6 §7.1 本来主題への復帰)
            10 段階完了、n_pulses_short のみ頑健
            window 依存性発見 (immediate で delta_C 頑健、n_pulses 方向反転)
            ← 現在地、v10.13 へ
```

---

## 4. 留保事項 27 件総覧 (Phase 1.5 累積)

### 4.1 由来別

| 由来 | 件数 | 内容概要 |
|---|---:|---|
| v10.9 | 3 | bimodal 解析の手法的限界、QC_cost 評価不能、high_fam_out 経路最強の理由未解明 |
| v10.10 第一弾 | 4 | closed_triad ゼロ、bin_2 反応 type 別の意味、long window 未実装、tied seed の意味 |
| v10.10 第二弾 | 4 | Multi-gate × timing の組み合わせ爆発、5 軸層化の独立性、reaction type 分業の v10.13 含意 |
| v10.10 完了 | 3 | gate_effect の seed 間 tied、long window 算出可否、cohens_d 解像度 |
| v10.11 | 4 | within-cid C 値変化の機構解釈、β member 限定の妥当性、age 軸との交差、ε=1 漏れ |
| v10.11 完了 | 4 | q_c_inherited 観察の v10.5 既知再観察性、受信機構 ≠ 観察対象、Aruism 整合 |
| **v10.12** | **5** | (#23-#27、下記) |
| **計** | **27** | |

### 4.2 v10.12 新規留保 5 件 (詳細)

| id | 由来 step | title | 派生する v10.13 主題候補 |
|---|---|---|---|
| **#23** | Step Z | n_core 別反応 type 分業 (v10.10 §3.4) と本主題の整合 | n_core 軸主題 |
| **#24** | Step B | Q3_threshold (lifespan ≥ 977) の意味と他主題への汎用性 | lifespan 軸主題 |
| **#25** | Step B | familiarity 閾値選定の意味 (top 25% vs top 50%) | familiarity 高/低 並行観察主題 |
| **#26** | Step A 再実施 | 層化集計の cond1/cond3 絞り込みによる bin_5+ × before/no_alpha 集中 | n_core / formation 軸主題 |
| **#27** | Step I/J | **smoke seed 0 の path_excess は seed 特異的、24 seeds 統合では効果分散** | **(a) seed-level variability / (b) smoke 複数 seed 運用 / (c) per-seed paired_d / (d) cid pool 定義再検討** |

### 4.3 本日追加調査で確定した追加 evidence (留保 #27 補強)

- immediate window (1-10 step) で delta_C 頑健 v112 > v108_standard (Step J で見落とした事実)
- n_pulses は window 依存で方向反転 (immediate -0.94 / short +1.36 / medium +1.31)
- → **window 依存性自体を観察対象とする主題** が v10.13 候補に追加

---

## 5. 累積規律 (Phase 1.5 で確立)

### 5.1 主要規律 (v10.6 - v10.12)

| 規律 | 確立版 | 内容 |
|---|---|---|
| ベースライン比較 + 効果サイズで切る | v10.6 | z-score だけ見るとサンプル数で水増しの擬似相関、|delta_ratio| > 1% で評価 |
| 観察解像度の選択 | v10.6 | 静的 / window / per-pulse / step10 で見える特徴が異なる |
| 人間原理偏向の警戒 | v10.6 | 事前推測 SOC.central 等が完全反証 |
| 因果候補の階層化 (Level 1-4) | v10.7 | Level 1: co-occurrence / 2: path-enriched / 3: source-specific / 4: causal intervention |
| 5 種 baseline 必須 | v10.7 | unrelated / same_step_random / matched / same_integration_low_fam / high_fam_out_integ |
| アバランシェ防止 | v10.7 | 3 hop 上限、減衰率、共鳴ループ、ストレージ上限 |
| 構造語と直感語の併記 | v10.7 | 実装は構造語、議論は直感語 (Taka の理解を最優先) |
| Level 3.5 introduced event comparison | v10.8 | 因果断定回避、event 比較として位置づけ |
| post-process 計算的減算 | v10.8 | 物理層 frozen と外部要素導入の両立 |
| Atom 326 絶対化禁止 | v10.8 | atom 種別は手段、神の手回避 |
| 出口の固定 | v10.9 | 4 種設計表のように観察結果を次の主題への素材に固定 |
| 各変動条件で baseline 再計算 | v10.9 | GPT B6 |
| 4 層階層化の明示 | v10.9 | GPT B5 |
| §35 運営メタ規律 10 項目 | v10.11 | 上位資料読了、観察軸を駆動要因にしない 等 |
| §5.5 規律チェックリスト (案 X) | v10.12 | お守り規律、主題変更時に再確認 |
| 規律 42 候補 | v10.12 | 上位完了レポート §5 必読 |
| Aruism「予想と違えば再観察」 | v10.11 §5.2 | 3 段階判定 (Full/Partial/Failure) 廃止 |
| smoke 後 main 自動進行回避 | v10.6 違反教訓 | Taka / Web Claude 承認待機 |
| 資料 push まで完結 | 規律化 | 報告書・CSV 生成時は同一ターン内で commit + push |
| **smoke seed 0 を絶対視しない** | **v10.12 で実観測** | **main 24 seeds で再確認するまで判定保留** |

---

## 6. 現状 (v10.12 完了 + 本日 window 追加調査) と v10.13 分岐点

### 6.1 ここまでで言える事実

**機構レベル (構造的予想 matched)**:
- Atom 持ち込み機構は ESDE で動く (v10.8 - v10.12 で繰り返し検証)
- 4 条件選別した cid pool (420 cid × 25 atom = 10,500 events) を作って波及を測れる
- 物理層 frozen は v10.5 以降一度も破られていない (層 B 443 files unchanged)
- 24 seeds で paired_d / sign_test / bootstrap CI が回せる基盤

**観察レベル (v10.12 + 本日 window 調査)**:
- n_pulses (pulse 数の前後変化) は window 依存で異なる方向に動く (immediate で v112 < v108、short/medium で v112 > v108)
- immediate window (1-10 step) で delta_C は v112 > v108 で頑健 (paired_d +0.54)
- 他の metric (delta_C medium / delta_Q 全 window / path_excess 12 cells) は方向性なし
- smoke seed 0 が示した path_excess の強い正方向は 24 seeds 統合で消える (seed 特異)

**言えないこと**:
- 「v112 cid pool が atom 取り込み prototype として有効か」の判定 (この観察セットでは Yes/No 出ない)
- 「条件選別した cid の方が波及が強い」は path_excess については支持されない、base metric は window 依存
- 「Atom 取り込みが効いた / 効かなかった」(judgment は研究者領域)

### 6.2 v10.13 主題候補 (Code A 提案、Taka 判断)

| 候補 | 由来 | 内容 | 優先度候補 |
|---|---|---|---|
| **(α)** | 本日 window 調査 | **window 依存性自体を観察対象とする主題** (delta_C / n_pulses の window 依存方向反転の意味) | **高** |
| **(b)** | 留保 #27 (b) | **smoke 段階で複数 seed (例 3 seeds) で確認する運用ルール変更** | **高** (主題でなく運用) |
| (β) | 本日 window 調査 | immediate (1-10 step) delta_C 頑健の意味検討 (atom 取り込み直後の C 値変化) | 中-高 |
| (γ) | 本日 window 調査 | n_pulses 方向反転の意味検討 (cid 選別 method が timing 構造を変えている可能性) | 中 |
| (δ) | 本日 window 調査 | 1 step / 50 step / long (>1000) window 追加実装 (compute_deltas 拡張) | 中 ((α) に組込可) |
| (a) | 留保 #27 (a) | seed-level variability 自体を観察対象とする主題 | 中-高 |
| (c) | 留保 #27 (c) | per-seed paired_d を主観察にする設計の formal 化 | 中 |
| (d) | 留保 #27 (d) | cid pool 定義 (4 cond) の選定根拠を再検討する主題 | 大きな変更、要慎重判断 |
| n_core 軸 | 留保 #23 | bin_2 (pulse 系) vs bin_5+ (delta_C 系) の反応 type 分業を主題化 | 中 |
| lifespan 軸 | 留保 #24 | Q3_threshold 977 の意味、lifespan 階層化主題 | 中 |
| familiarity 軸 | 留保 #25 | familiarity 高/低 並行観察 (v10.6 §7.2 候補) | 中 |
| 受信機構 | 留保 v10.11 | within-cid 観察の正しい設計 (v10.11 で v10.5 既知再観察になった反省) | 中 |
| 常駐 Atom | Gemini A7 | atom 常駐アンカー実装 (v10.9 4 種設計表との接続要検討) | 中 |
| QC_cost | v10.9 留保 | post-process 限界で評価不能、本格評価には実 simulation 再回し | 大きな実装、後回し可 |

### 6.3 Code A の感触 (Taka 判断材料)

本日の window 調査で **「Step J は medium のみ集計していて immediate を見落としていた」という設計盲点が確定** したので、(α) window 依存性主題が一番直接的な next。これと (b) smoke 複数 seed 運用改善を並行で進めると、v10.13 で同じ盲点を踏まない構造になる。

cid pool 定義再検討 (d) は大きな主題変更になるので、(α) で window 依存性を見てから判断するのが順当。

---

## 7. 参照資料

### 7.1 詳細サマリ

- `docs/ai_summaries/06_developmental_summary.md` (v10.0-v10.9 詳細、1230 行)
- `docs/ai_summaries/06b_developmental_phase15_summary.md` (v10.4-v10.12 詳細、683 行)

### 7.2 各バージョン完了レポート

| ver | 主要レポート |
|---|---|
| v10.1 | `developmental/v101/v101_minimal_ingestion_result.md` |
| v10.2 | `developmental/v102/v102_main_run_result.md` + `v102_ecosystem_finding.md` + `v102_detailed_analysis_report.md` |
| v10.3 | `developmental/v103/v103_main_run_report.md` |
| v10.4 | `developmental/v104/v104_*.md` (5 本) |
| v10.5 | `developmental/v105/v105_main_v2_run_report.md` |
| v10.6 | `developmental/v106/v106_*_report.md` (7 本) |
| v10.7 | `developmental/v107/v107_main_run_report.md` + 5 種解析レポート |
| v10.8 | `developmental/v108/v108_main_run_report.md` + 4 種解析レポート |
| v10.9 | `developmental/v109/v109_main_run_report.md` |
| v10.10 | `developmental/v110/v110_main_run_report.md` + `v110_multi_axis_stratified_summary.md` |
| v10.11 | `developmental/v111/v111_main_run_report.md` |
| **v10.12** | **`developmental/v112/v112_completion_report.md`** (Step K、commit 238a145) + Step Z-J 報告書 11 本 |
| v10.12 追加 | `developmental/v112/v112_window_investigation_report.md` (本日、commit ee87f63) |

### 7.3 上位資料

- `docs/ESDE_Developmental_Report.md` (Developmental 完全版、801 行)
- `docs/ESDE_Primitive_Report.md` (v9.x までの Primitive サマリ)
- `docs/LANGUAGE_LEGACY_DIGEST.md` (ESDE Language 系 2026-03 凍結整理)

---

## 8. 最終一文

v10.x シリーズは v9.x Primitive フェイズで言語化された意識の原資モデル (Q 消費 → C 転化) を動作機構として実装する Developmental フェイズであり、Phase 1 (v10.0-v10.5) で 4 層アーキテクチャ確定 → 摂食機構 → 確率的認知/意識切替 → 双方向 E3 / Integration → α/β 階層分離 (Layer 5 完成) と ESDE 内部進化を完成、Phase 1.5 (v10.6-v10.12) で ESDE Genesis × Language 統合に進み Atom alignment 比較 → オービス完成 → Atom 持ち込み機構 → 寄与候補感度評価 + 4 種設計表 → Multi-gate × timing (観察延長への逸脱) → q_c_inherited within-cid 観察 (v10.5 既知再観察に終わる) → Atom 取り込み prototype (v10.6 §7.1 本来主題への復帰) と進展、v10.12 で構造的予想 6/6 全達成 + n_pulses_short のみ paired_d +1.36 頑健 / 他 6 metric は方向性なし / smoke seed 0 と main 24 seeds で path_excess 4 種符号反転 (Aruism 発動) + 留保 27 件確定、本日 window 単位追加調査で immediate (1-10 step) delta_C 頑健 + n_pulses 方向反転を発見し Step J 観察設計の盲点を formal evidence 化、現在地は v10.12 完了 + v10.13 主題選定待ち、Code A 提案優先候補は (α) window 依存性主題 + (b) smoke 複数 seed 運用改善、最終判断は Taka 領域。物理層 frozen は v10.0 から v10.12 まで一度も破られず、層 B 443 files unchanged で実証、累計規律 (集団平均の罠 / 効果サイズで切る / 観察解像度の選択 / 因果候補階層化 / 5 種 baseline / Level 3.5 / Atom 326 絶対化禁止 / 出口の固定 / Aruism / smoke 後 main 自動進行回避 / smoke seed 0 を絶対視しない 等) は全て継承中。

---

*以上、v10.x 全マイナーバージョン レビュー資料。Taka 振り返り用、v10.13 主題選定の判断材料として作成。詳細は 06_developmental_summary.md (v10.0-v10.9) と 06b_developmental_phase15_summary.md (v10.4-v10.12) を参照。*
