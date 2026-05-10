# 06b Developmental Phase 1.5 Summary (v10.4-v10.12)

*作成*: 2026-05-11、Code A (実装担当、新 Web Claude スレッド向け状況引き継ぎ)
*対象*: ESDE Developmental Phase 1.5 (v10.4-v10.12 系列、Genesis × Language 統合段階)
*親資料*: `06_developmental_summary.md` (v10.0-v10.3、2026-04-28 で凍結)
*用途*: 新 Web Claude スレッド初見時に Phase 1.5 全容を把握するための網羅的引き継ぎ。本書を読めば v10.4 以降の主題変遷・主要発見・累積規律・留保事項・現在地 (v10.12 Step A 完了、Q-A1 重大ブロッカー警告中) が分かる。

---

## 0. 一文サマリ

ESDE Phase 1.5 (v10.4-v10.12) は v10.0-v10.3 の単 cid 系から **cid 集団 (Layer 5、α/β-Integration) + Atom 取り込み機構** への拡張段階、v10.4 で Integration 13,550 件誕生 + Q/C 部分再分配機構成立、v10.5 で α/β 階層分離 + hub β (最大 691 α / 20 cid) + 機構 A (β に Q/C 100% 継承) + 機構 C (Recorded ε=1) 確立、v10.6 で Atom alignment observer + 26 atom 構造的特異性、v10.7 で post-process オービス完成 (5 source × 10 path × 6 量 × 3 window = 415K events / 3.45M excess)、v10.8 で atom_introduction_event 機構 (25 atom × 100 cid × 24 seeds = 60K events) + Level 3.5 で「introduced は natural の半分」発見、v10.9 で 4 種設計表完成 (timing > cid > QC 感度階層、high_fam_out_integ で timing 0.222 最強、age=200 timing で若い cid 強反応) + Phase 1.5 第四試行で「字面に揺れながら反応するシステム」の核心素材確立、v10.10 で Multi-gate × timing 二次元観察 + n_core 別層化で「pulse 系は bin_2 / delta_C 系は bin_5+」反応 type 分業発見 (ただし観察延長への逸脱) と「v10.10 §3.4 反応 type 分業」が以降必須参照、v10.11 で q_c_inherited 起点 within-cid 観察 (ただし v10.5 機構 A の自明な再観察に終わる、規律 §35 #9 違反) で観察延長パターンを断ち切るべきと判明、v10.12 で「条件適応型 atom 導入の単一勝負案」(v10.10 でやるべきだった主題) を 2 trial 分割設計 (trial-A bin_5+ × delta_C / trial-B bin_2 × pulse) で再開、Step Z 事前調査 (Code A 実測 commit df04d0a) で 4 件の重大乖離検出 (母集団崩壊・Q3 取り違え・cid pool ほぼ完全重なり・v10.11 既知重複)、第 4 版主題で 2 trial 分割 + Q2 緩和 + bin 別比較 + §5.6 規律チェックリストにより設計修正、Step A 認識確認 (commit ddd595a) で **Q-A1 trial-B 母集団 per seed 0.2 の重大ブロッカー警告** (cond4 high_fam top 25% が bin_2 で稀少 12.5% という構造的問題)、Web Claude/Taka 判断待ち、累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト (案 X、お守り規律) 確立、留保事項 22 件累積、bit-identity 全層 PASS 維持 (v107+v108+v109+v110+v111 = 約 1,080 files 不変)、storage 累計 1.52 GB (上限 6 GB の 25%) で v10.12 後も 50% 余裕、Taka 整理 §1.9 (2026-05-10) で「v10.12 は会話への接続ではなく字面に揺れながら反応するシステム = ESDE Atom スレッド = 連結基盤の第一スレッドの精緻化」と本主題の位置づけ確定。

---

## 1. Phase 1.5 全体ロードマップ

```
v10.0-v10.3 (2026-03-2026-04-28): 単 cid 系、4 層アーキテクチャ確定 (06_summary 参照)
   ↓
v10.4 (2026-04-30): Integration 機構導入 (Q/C 継承、Layer 5 入口)
v10.5 (2026-05-01): α/β 階層分離 + hub β + 機構 A/C 確立 (Layer 5 完成)
v10.6 (2026-05-04): Atom alignment observer + 26 atom 構造的特異性
v10.7 (2026-05-05): post-process オービス完成 (5 source × 10 path × 415K events)
v10.8 (2026-05-06): atom_introduction_event 機構 (25 atom × 60K events、Phase 1.5 第三試行)
v10.9 (2026-05-08): 4 種設計表 + 寄与候補感度評価 (Phase 1.5 第四試行、選抜試験)
v10.10 (2026-05-09): Multi-gate × timing 多軸層化 (Phase 1.5 第五試行、観察延長への逸脱)
v10.11 (2026-05-10): q_c_inherited 起点 within-cid 観察 (Phase 1.5 第六試行、v10.5 既知再観察)
v10.12 (2026-05-10〜現在): 条件適応型 atom 導入の単一勝負案 (Phase 1.5 第七試行)
   ↓ (現在 Step A 完了、Q-A1 重大ブロッカー警告中)
v10.13 以降: 字面に揺れながら反応するシステムの精緻化 prototype (Taka 整理 §1.9)
```

---

## 2. 各バージョンの主題と達成 (一文サマリ)

### 2.1 v10.4 (2026-04-30): Integration 機構導入

**主題**: Layer 5 (cid 集団) 入口、Q/C 継承機構の最小実装

**達成**:
- 24 seeds 完走 (wall mean 2.99h)
- **Integration 13,550 件誕生** (be3 7,085 / open_triad 5,203 / closed_triad 0 / third_overlap 1,262)
- Layer A 物理層 frozen 維持 (labels / persistence 24/24 完全一致)
- v10.3 比 C 蓄積 +15%、C_max +31%、cognition 当選 +4.2%
- Integration が ghost cid から Q/C を 10,000/14,083 継承 → active member へ部分再分配 2,790/1,777

**新規概念**: Integration、be3 (両者 C-1)、open_triad、third_overlap

### 2.2 v10.5 (2026-05-01): α/β 階層分離 (Layer 5 完成)

**主題**: Layer 5 完成、α/β 階層分離 + hub β + 機構 A/C

**達成**:
- 物理層 bit-identity 100% PASS、規律 M6 (1 cid → 1 β 会計) 違反 0
- α/β 階層成立、**hub β 出現 (最大 691 α 統合 / 20 cid)**
- Salience event 78k 件 (mass-weighted 観察)
- Leakage 0 件は v10.2 即時 ingestion path のバグ修正済み

**確立した機構** (v10.12 でも参照される最重要):
- **機構 A** (`v105_integration.py:1035`): cid が ghost 化時、その cid が β member なら β が **Q/C を 100% 継承**。α 側はメンバー除外と recorded 化のみ (Q/C 継承なし)
- **機構 C**: Recorded からの漏れ ε=1、active_to_recorded で β は永続化、death events 0 件
- **β event_type 5 種**: birth / alpha_added / beta_merged / q_c_inherited / active_to_recorded
- **α event_type 3 種**: birth / member_ghosted / active_to_recorded
- α は **可変サイズ** (2-8 cid、平均 2.63)、β は **常にペア** 結合 (member_alphas 数 = 2)

### 2.3 v10.6 (2026-05-04): Atom alignment observer

**主題**: Atom (326 atom) と cid の alignment 観察、Phase 1.5 第一試行

**達成**:
- 26 atom 構造的特異性 (delta>1% × 9 + z=inf × 17 - 1 duplicate = 25 atom 確定)
- WLD.artless reserved label (留保扱い、集計除外)
- cid_atom_sim_matrix 構築 (各 atom × cid の sim 行列、後の v10.8 で top_k 100 抽出に活用)
- 7 atom 構造的盲点を別途記録 (B 群)
- per-event / per-pulse / step10 trajectory 解析で時間軸混在 caveat 確立

### 2.4 v10.7 (2026-05-05): post-process オービス完成 (Phase 1.5 第二試行)

**主題**: 観察基盤 (オービス) の確立、source_event 5 種 + relation_path 5 種 + baseline 5 種

**達成**:
- 24 seeds 並列 main run **234.86 秒** (順次比 12 倍高速、multiprocessing.Pool 24)
- **5 source_event × 10 relation_path/baseline で 415,726 events、3,453,191 excess_change rows**
- Level 1 (co-occurrence) **93/111 finding**
- Level 2 (path-enriched) **49/58 finding**
- Level 3 (source-specific) **85/90 finding**
- **path 順位**: temporal_coactivation > Integration > familiarity > attention
- bit-identity 層 A 9/10 (summary は実行時間記録で除外)、層 B v10.6 出力 731 files 完全不変
- storage 428 MB (上限 6 GB の 7%)

**source_event 5 種**: pulse / ingestion / α_formation / β_formation / c_conversion (v10.12 でも継承)
**relation_path 5 種**: familiarity / attention_via_salience / integration_alpha / integration_beta / temporal_coactivation
**baseline 5 種**: unrelated / same_step_random / matched / same_integration_low_familiarity / high_familiarity_outside_integration_baseline (v10.7 §F、§G で確立)

### 2.5 v10.8 (2026-05-06): atom_introduction_event 機構 (Phase 1.5 第三試行)

**主題**: Atom 単独持ち込み機構、25 atom × 100 cid × 24 seeds = 60,000 events

**達成**:
- post-process 計算的減算 (Q-1, C+1) で 60K events
- 24 seeds 並列 main run **325 秒**
- Level 1 (atom co-occurrence) **811/1,384 findings**
- Level 2 (atom path-enriched) **683/1,433 findings**
- Level 3 (atom source-specific) **36/78 findings**
- **Level 3.5 (introduced vs natural) 22/39 findings**
- **最大主結果**: Level 3.5 で 20/22 finding が **introduced < natural** (atom event は natural の半分の波及効果、差 4.38)
- familiarity 経路の atom 識別 effect_size 6.83、temporal_coactivation は atom 中立 effect_size 0.03
- bit-identity 層 A 15/15 PASS + 層 B v10.7 222 files 完全不変
- storage 737 MB (累計 12%)

**v10.8 標準** (以降 v10.9-v10.12 で baseline として参照):
- A1: Q -1 / C +1 (post-process 計算的減算)
- B1: top_k 100 cid (cid_atom_sim_matrix から sim 上位)
- C1: 案 α 均等分散発火 (atom_index × 10 step ずらし)

### 2.6 v10.9 (2026-05-08): 4 種設計表 + 寄与候補感度評価 (Phase 1.5 第四試行)

**主題**: Atom 取り込み機構の精緻化、寄与候補感度評価 + bimodal 構造解析、選抜試験

**達成 (核心的発見 4 件)**:
1. **「強反応する cid は若い cid (age median 227)」**: bimodal 1,540 cells のうち genuine 918、H3_lifecycle 60.2% 支配 + 99% 方向一致 (effect_size 0.85)
2. **timing > cid_selection > QC_cost の感度階層**: timing abs_mean 0.141 / cid_selection 0.024 / QC_cost 0.005 で評価不能
3. **「Integration 外の高 familiarity cid (high_fam_out_integ)」が timing 感度 0.222 / std 0.079 で最強・最 robust**
4. **C2 (若い cid 発火) で pulse 活動 short 0.97 / medium 0.75 大効果量で活発化**

**4 種設計表 (v10.13 以降の素材)**:
- 表 1 sensitivity: 候補別 cohens_d (timing / cid_selection / QC_cost)
- 表 2 受信可能状態: cid age <= 560 + Integration 外 + 高 familiarity (top 25%) + n_core ≥ 4.67 (副)
- 表 3 ルーティング: high_fam_out PREFER
- 表 4 自然さ: C2 が natural に近づいた cells 47%

**留保事項 3 件**:
1. bimodal KDE fallback 100% (主結果信頼性は維持)
2. **QC_cost 評価不能** (post-process 計算的減算限界)
3. **high_fam_out_integ 構造未解明**

**Taka の問いへの最終回答**: 「**25 atom を若い cid (age <= 500) + Integration 外 + 高 familiarity に対して age=200 timing で投げる**」が v10.10 主題予定 (= 条件適応型 atom 導入の単一勝負案)。

### 2.7 v10.10 (2026-05-09): Multi-gate × timing 多軸層化 (Phase 1.5 第五試行、観察延長への逸脱)

**主題変更**: 当初は「条件適応型 atom 導入の単一勝負案」(v10.9 設計表の統合適用) のはずが、Code A 母集団不足 (per atom × seed = 1.84) を契機に Multi-gate × timing 二次元観察設計に **転換** (Web Claude/Taka 判断、観察軸を増やす方向)

**達成**:
- 24 seeds × 28 conditions main run **103.67 秒**
- 9 種 gate × 3 timing (200/300/500) + v108_re = 28 conditions
- bit-identity 全層 PASS (層 B v107+v108+v109 = 867 files 完全不変)
- **3 つの主要観察**:
  1. gate 効果は mean_delta_C medium で abs_mean 0.053 と小 (v10.9 high_fam_out 0.222 が複合 gate / 母集団小化で減衰)
  2. timing 軸 (t200 vs t500) で全 gate が負方向 (-0.090 〜 -0.253、v10.9 Step F 仮説と逆)
  3. v110 vs v108_re は mean_n_pulses_in_window で abs_mean 0.928 大効果量

**追加層化解析 (Web Claude 第一弾 5 軸 + 第二弾 4 タスク + n_core 補足)**:
- Integration α/β 4 層化 / cid 寿命別 / 25 atom 個別 / window × n_core 交差 / seed 別ばらつき / Integration 形成タイミング (formation_relation) / 寿命 × n_core 交差
- **§3.4 反応 type 分業 (v10.12 でも必須参照)**:
  - **bin_2 (ペア、76%) は pulse 軸で大効果** (matched +4.295)
  - **bin_5+ (中 cluster、12%) は delta_C 軸で大効果** (high_fam_out -0.653)

**留保事項 14 件 (継承 3 + 新規 11)**:
- 留保 8: 長寿 cid (Q4) の timing_axis 方向反転寄与
- 留保 11: Integration 形成前と after_100plus の cohens_d 差の構造的解釈
- 留保 12: 「相関する 2 軸の交差効果」の構造的根拠
- 留保 14: no_alpha 群の v110_vs_v108re +0.133 の構造的位置づけ

**逸脱の教訓**:
- 観察延長への流れに転換した結果、「v10.9 で見えたルールが本物か幻か」が単一 metric では決まらず、観察状態 B (分岐) で終了
- 単一勝負案を実現できなかった

### 2.8 v10.11 (2026-05-10): q_c_inherited 起点 within-cid 観察 (Phase 1.5 第六試行、v10.5 既知再観察に終わる)

**主題**: Integration 形成プロセス解析、q_c_inherited 前後の within-cid delta_C 比較

**達成**:
- 24 seeds main run **7.65 秒**
- 12 cells (n_core_bin × β 累積 c_inherited 分位) × 24 seeds で within-cid 前後比較
- 272,835 snapshots、13,055 (event, cid) pairs

**核心観察 (24 seeds)**:
- delta_C_within: 全 12 cells で正値 (+0.097〜+0.497)
- bin_2 × Q1 / bin_3_4 × Q4: 24 seeds 完全一致 (complete_consistent)
- delta_pulse_within: 全 cell ≈ 0

**整理仮説 (留保)**:
- C 値飽和仮説 (主題 §1.5) は本データで不支持 (Q1 と Q4 がほぼ同程度)
- 観察事実は **q_c_inherited は β member cid の C を継続的に増加させる ESDE 構造的機能** (v10.5 機構 A) の **直接観察**

**達成条件 §0.2 (1 条件抽出) は限定的に達成**: 「β member cid は v10.12 概念取り込み目的の入力対象から除外」← v10.5 機構 A の延長

**留保事項 4 件 (新規)**:
19. seed 0 と 24 seeds 観察パターン不一致
20. C 値飽和仮説不支持
21. **ESDE β 機能 (q_c_inherited で C 増加) の直接観察可能性** ← v10.12 で参照
22. delta_pulse_within ≈ 0

**最大の教訓 (規律 §35 #9 違反)**:
- 主題ドキュメント第一稿で「alpha_birth / beta_birth を新規 source_event 化」と書いたが、v10.7 既存実装で alpha_formation / beta_formation 既に source_event 化済 と Code A 事実確認で判明 → 第二稿で書き直し
- 観察対象 (q_c_inherited 前後) が v10.5 機構 A/C の自明な再観察に過ぎなかった
- **3 AI と Code A 全員が v10.5 §7.4-§7.10 を主題設計に反映しなかった構造的失敗**

→ v10.11 完了レポート §2 で「v10.12 では v10.10/v10.11 逸脱パターンを断ち切る必要」と明示。

### 2.9 v10.12 (2026-05-10〜現在): 条件適応型 atom 導入の単一勝負案 (Phase 1.5 第七試行)

**主題**: v10.9 完了時点で Taka と Web Claude が GPT 修正方針のもと確定していた **「条件適応型 atom 導入による v10.8 標準を超える性能向上」** を、v10.10/v10.11 で得られた素材で更新して再開

**主題ドキュメントの版変遷**:
- 第一稿: 単一勝負案 (4 条件 AND)
- 第二稿: 第一稿同設計、Code A 認識確認待ち
- 第三稿: GPT 監査 + Taka 整理 §1.9 (字面反応システム) 反映、慎重トーン維持
- **第四稿 (現行)**: Step Z 結果 + Taka 判断「破綻ではなく前提変更」を反映、**2 trial 分割設計** + §5.6 規律チェックリスト (案 X)

**Step Z 事前調査 (Code A 実測 commit df04d0a、2026-05-10)**:
4 件の重大乖離検出:
1. Q-Z1 母集団崩壊: 4 条件 AND_all 24/24 seed で <10、per seed 3.9 (paired_d 算出不能)
2. Q-Z2 取り違え: Q3=2,485 vs Web Claude 想定 977 (実は Q2)
3. Q-Z6 cid pool 重なり: overlap_ratio_v112 = 0.958 (matched_pool 比較崩壊)
4. Q-Z5 v10.5 機構との重複: (b) 部分的に重なる (条件 1 は v10.11 既知)

**Code A Step Z 補完 (Taka 指摘で n_core 別層化漏れ発覚、commit df04d0a)**:
- 4 条件複合は構造的に bin_2/bin_3_4 を完全排除 (cond3=n_core≥5 が排他条件)
- v10.10 §3.4 反応 type 分業との致命的乖離 (4 条件複合は delta_C 軸狙いで pulse 系を完全排除)

**Taka 判断 (2026-05-10)**:
- 確認 1: 破綻ではなく前提変更
- 確認 2: 方向 A (2 trial 分割) 採用
- 確認 3: 案 X 規律チェックリスト採用

**第 4 版主題の中核 (現行)**:
- **trial-A**: bin_5+ × delta_C 系狙い (cond3 = n_core ≥ 5)、性能指標 1-A + 3-A
- **trial-B**: bin_2 × pulse 系狙い (cond3 = n_core == 2)、性能指標 2-B + 1-B 副次
- lifespan は Q3=2,485 → Q2=977 緩和 (cond2 緩和、母集団確保)
- bin 別比較で公平性確保 (v112_trial / v108_matched_pool_bin / v108_original_bin の 6 condition)
- §5.6 規律チェックリスト (案 X、お守り規律として運用)

**Step A 認識確認 (commit ddd595a、2026-05-10)**:
**Q-A1 重大ブロッカー警告**:
- trial-B (bin_2 × 4 条件) は per seed 0.2 / total 4 events で paired_d 算出不能
- 構造的根拠: cond4 (familiarity top 25%) が bin_2 で稀少 (12.5% しか該当)、Q2 緩和でも解消されない
- Code A 提案: trial-B のみ cond4 を top 50% 緩和 (Web Claude/Taka 判断要請)

**現在地 (2026-05-11 時点)**: Web Claude 新スレッドへの引き継ぎ中、Q-A1 解消後 Step B (環境チェック詳細) 進行待ち

---

## 3. 累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト

### 3.1 累積規律 41 件 (v10.7-v10.11 確立、`09_audit_principles.md` §34)

#### 物理層・観察層の規律
1. **物理層 frozen** (v10.7): post-process は実 ledger 不変、read のみ
2. **神の手回避** (v10.7): 構造条件のみで判定、ハンドチューニング禁止
3. **Atom 326 絶対化禁止** (v10.6): 25 atom (構造的特異性) を継承、326 化なし
4. **因果断定回避** (v10.9 GPT B3): 「効いた」「効果的だった」を使わず、「観察された」「並列値より大きい」のような観察語に統一
5. **post-process 計算的減算** (v10.8): Q/C コストは post-process で計算ベース再現、実 ledger 不変

#### 観察設計の規律
6. **出口の固定** (v10.9): 主題完了レポートで成果物を事前定義
7. **構造語と直感語の併記** (v10.7): Taka 向け理解語と実装の構造語を分離記述
8. **寄与候補感度評価命名** (v10.9 GPT B3): 「原因」ではなく「寄与候補の感度評価」
9. **各変動条件で baseline 再計算** (v10.9 GPT B6): 条件比較時は baseline も条件別に再計算
10. **4 層階層化** (v10.9 GPT B5): Level 1 (機構動作) / Level 2 (条件差) / Level 3 (感度評価) / Level 3.5 (構造的説明候補整合)

#### 監査・運用の規律
11. **Code A 認識確認必須** (v10.7、再強化 v10.8): Web Claude 主題ドキュメント → Code A 認識確認 → Web Claude 即決事項返答 → Taka 承認 → 実装着手
12. **smoke 後止まって報告** (v10.6、Taka 指示): smoke 完了後 main run に勝手に進まず、Taka / Web Claude 承認待ち
13. **24 seeds 単一バッチ** (v10.6、Taka 指示): 8/8/8 等のバッチ分割禁止、1 コマンド単一バッチ
14. **資料を作ったら push までセット** (Taka 指示): 報告書・CSV 生成時は同一ターン内で commit + push
15. **bit-identity 3 層検証** (v10.7 確立、v10.8-v10.12 継承): 層 A 同 seed 2 回再現 + 層 B 既存出力不変 + 層 C パス制限

#### 観察記述の規律
16. **観察と判定の区別** (v10.10 第一弾): 報告書は観察記述まで、判定は Web Claude 判定書で実施
17. **events 数 / n_b 不足の併記** (v10.10): cohens_d 計算で n < 3 のセルは `n_b_insufficient` 列で明示
18. **既知事実との重複確認** (v10.11 違反契機): 主題が v10.5 機構等の自明な再観察でないか事前確認

#### 物理的環境の規律
19. **NVIDIA driver upgrade 原則 NG** (memory): 過去事故、TRT-LLM 等の driver 要件不足時はソフト側後退
20. **物理層 frozen の強制** (v10.7): 出力先パス制限 (v107/, v108/, ... 配下のみ書き込み許可)

#### v10.10/v10.11 で確立された規律
21-30. (累積、各 commit log で詳細)

#### v10.10/v10.11 で再明文化された規律 (重要 5 件)

37. **n_core 別層化解析必須** (v10.10): n_core_bin (bin_2 / bin_3_4 / bin_5+) で層化、平均で潰れる構造を救出
38. **formation_relation を観察軸として含む** (v10.10): Integration 形成と event timestamp の関係を主軸 or 条件軸として含める
39. **完全マージ版文書を出力** (v10.10): 主題ドキュメント / 報告書は完全版で出力、後追い追加禁止
40. **観察軸を増やす方が見えるものが増える** (v10.10、Taka 整理): ただし §0.3 打ち切り条件と併用
41. **観察状態判定枠を超えた整理** (v10.10): 必要に応じて A/B/C 判定枠を超えた整理を採用可

### 3.2 §35 運営メタ規律 10 項目 (v10.11 で確立)

GPT 第三回監査提示 + Web Claude 自己反省 (v10.11 違反契機):

1. **オープン調査とクローズ調査を固定方針にしない**
2. **追加調査を開く時は理由を明示する** (前提崩れ / 観察軸不足 / 次フェーズ素材 / 平均化誤認回避)
3. **平均で潰れる構造は必ず層化を検討する** ← n_core が典型
4. **閾値は真理ではなく運用上の仮置きとして扱う**
5. **整理語は観察事実と分ける**
6. **主題終了条件は置くが、その前提が実測で崩れた場合は再開を許す**
7. **監査や整理は、閉じる妥当性だけでなく、開く妥当性も評価する**
8. **最終的な開閉判断は、現場感を持つ人間 (Taka) 側に残す**
9. **Web Claude は主題ドキュメント着手前に関連バージョンの上位資料を読む** (お守り規律)
10. **「観察できる軸が見えた」を駆動要因にしない** (v10.10 違反契機、Taka 指摘)

### 3.3 §5.6 規律チェックリスト (案 X、v10.12 第 4 版で導入、お守り規律)

主題設計時に Web Claude が累積規律 41 件 + §35 メタ規律 10 項目を 1 つずつ確認するチェックリスト。Taka 認識「Claude の担当が変わったりすれば結局同じ」(2026-05-10) の限界を明示しつつ、規律違反は予防ではなく **発見と修正のサイクル** で運用。

実装は v112_phase_design.md 第 4 版 §5.6 参照。

---

## 4. 留保事項一覧 (v10.9-v10.12 累積、計 22 件)

### 4.1 v10.9 留保 (3 件)

1. bimodal KDE fallback 100% (主結果信頼性は維持)
2. **QC_cost 評価不能** (post-process 計算的減算限界)
3. **high_fam_out_integ 構造未解明**

### 4.2 v10.10 第一弾留保 (4 件追加、計 7 件)

4. only_alpha / only_beta 不在 (構造的事実)
5. 長寿 cid (Q4) の timing_axis 方向反転寄与
6. atom category 別効果差 (BOD +0.399 vs WLD +0.009、40 倍差) の構造的解釈
7. gate_effect の 24 seeds 方向不一致 (tied 多発)

### 4.3 v10.10 第二弾留保 (4 件追加、計 11 件)

8. Q1 timing 軸方向反転と寿命の関係
9. β alpha_added の事象数と n_core_bin 別感度
10. 寿命 × n_core 交差の独立寄与
11. **Integration 形成前と after_100plus の cohens_d 差の構造的解釈** ← v10.11 で扱うも未解明継続

### 4.4 v10.10 完了レポート留保 (3 件追加、計 14 件)

12. **「相関する 2 軸の交差効果」の構造的根拠**
13. n_core 別層化での観察軸独立性
14. **no_alpha 群の v110_vs_v108re +0.133 の構造的位置づけ**

### 4.5 v10.11 留保 (4 件追加、計 18 件)

15-18. (n_core 関連の追加層化、Step F 主題核心関連)

### 4.6 v10.11 完了レポート留保 (4 件追加、計 22 件)

19. seed 0 と 24 seeds の観察パターン不一致
20. C 値飽和仮説の本データでの不支持
21. **ESDE β 機能 (q_c_inherited で C 増加) の直接観察可能性** ← v10.12 条件 1 (β member 除外) と関連
22. delta_pulse_within ≈ 0 (event 起点の質の違い)

---

## 5. ESDE 内部構造の主要概念 (Phase 1.5 で確立)

### 5.1 4 層アーキテクチャ (v10.0-v10.3 確立)

- 物理層 (Layer 1): pulse / ingestion / labels / persistence
- 存在層 (Layer 2): cid (cognitive identifier)
- 認知層 (Layer 3): Q (認知資源)、cognition decision
- 意識層 (Layer 4): C (意識資源)、consciousness decision

### 5.2 Layer 5 (cid 集団、v10.4-v10.5 確立)

- α-Integration: cid 集合 (誕生時 2-8 cid、平均 6.8、その後固定)
- β-Integration: α-Integration を構成要素とする上位構造、cid を重ねていく動的構造
- 結合則 (β): α 同士が cid 共有 2 個以上で merge
- 役割分離: α = 観察、β = 会計 (Q/C 継承単位)
- **最大規模**: 1 つの β が 715 α を吸収 (1 cid 34.5 α)

### 5.3 v10.5 機構 A/C (v10.12 で参照)

- **機構 A**: cid が ghost 化時、その cid が β member なら β が **Q/C を 100% 継承**
- **機構 C**: Recorded からの漏れ ε=1、active_to_recorded で β は永続化、death events 0 件

### 5.4 source_event カテゴリ (v10.7 確立)

| カテゴリ | 内容 | seed あたり events 数 (24 seeds 平均) |
|---|---|---:|
| pulse | pulse_log 由来 | 12,530 |
| ingestion | ingestion_events_seed*.csv | 155 |
| **alpha_formation** | event_type='birth' (alpha_lifecycle_log) | 424 |
| **beta_formation** | event_type='birth' (beta_lifecycle_log) | 239 |
| c_conversion | balance_decisions の consciousness | 155 |
| **atom_introduction_event** (v10.8 で追加、第 6 種) | post-process 計算的減算 | 2,500 |

### 5.5 alpha/beta_lifecycle_log の event_type (Code A 事実確認 2026-05-10)

#### α event_type (3 種)

| event_type | 24 seeds total | 内容 |
|---|---:|---|
| birth | 13,881 | 構成 cid 集合の誕生 |
| **member_ghosted** | 17,093 | 構成 cid の ghost 化、α の解体プロセス |
| active_to_recorded | 2,089 | α の recorded 永続化 |

#### β event_type (5 種)

| event_type | 24 seeds total | 内容 |
|---|---:|---|
| birth | 6,476 | β 誕生時、ペアでの誕生 |
| **alpha_added** | 7,405 | 新たな α が β に取り込まれる成長 |
| **beta_merged** | 4,467 | β 同士の merge による成長 |
| **q_c_inherited** | 2,247 | β から member cid への Q/C 継承 (機構 A) |
| active_to_recorded | 443 | β の recorded 永続化 |

### 5.6 Atom 326 + Axis + Operator + Lexicon v2 (Phase 8 強い意味系)

**最新仕様** (`docs/ESDE language/esde_cell_architecture.md` v2.3、2026-02-08):

- **Atom 326**: 326 atoms、163 対称ペア、16 categories (`language/atoms/esde_dictionary.json`)
- **Axis**: 8 canonical axes × 5-point scale (`cognitive / ethical / social / creative / ontological / temporal / spatial / physical`、Glossary v5.7.0 準拠)
- **Operator**: 15 種実装 (`language/sensor/constants.py`、`× ▷ → ⊕ | ◯ ↺ 〈〉 ≡ ≃ ¬ ⇒ ⇒+ -|>`)
- **Lexicon v2**: 327 個の JSON ファイル (`language/lexicon/data/lexicon_entries/`)、24 prefix カテゴリ
- **Synapse v3.0**: 11,557 synsets、22,285 edges (WordNet ↔ Atom mapping)
- **Phase 8 sensor**: `language/sensor/esde_sensor_v2_modular.py` の `ESDESensorV2.analyze(text)` で 文 → atom 変換 (現状 import エラーで動作要修正)
- **Molecule format**: `{"active_atoms": [{"atom": "EMO.love", "axis": "ethical", "level": 3}], "formula": "EMO.love"}`

### 5.7 v10.6 で確立された v10.7 以降で使われる atom 集合

**25 atom (構造的特異性、WLD.artless 留保で 24 集計)**: BOD.ear / COG.learn / COM.silence / EXS.being / EXS.nonbeing / FND.timeless / FND.transformation / PER.feel / PER.fragrance / PER.hear / PER.see / PER.smell / PER.sound / PER.soundless / PER.taste / PRP.bright / PRP.deep / PRP.sharp / SOC.city / SOC.nation / SOC.public / TIM.appear / **WLD.artless** (留保) / WLD.culture / WLD.technique

---

## 6. v10.10/v10.11 逸脱パターンと再発防止策

### 6.1 v10.10 逸脱パターン

**パターン**: Code A 母集団不足を契機に、観察軸を増やす方向に主題転換 (Multi-gate × timing 二次元観察)

**結果**:
- 観察状態 B (分岐) で終了
- 「v10.9 で見えたルールが本物か幻か」が単一 metric では決まらず
- 単一勝負案を実現できなかった

### 6.2 v10.11 逸脱パターン

**パターン**: 主題が v10.5 機構 A/C の自明な再観察に終わる (3 AI と Code A 全員が v10.5 §7.4-§7.10 を未参照)

**結果**:
- 達成条件 §0.2 (1 条件抽出) は限定的に達成、ただし「β member 除外」は v10.5 機構 A の延長
- 主題ドキュメント第一稿で「alpha_birth / beta_birth を新規 source_event 化」を提案 → v10.7 既存実装で source_event 化済 と Code A 事実確認で判明 → 第二稿で書き直し

### 6.3 v10.12 で実装された再発防止策

| 再発防止策 | 実装場所 |
|---|---|
| §1 主題ドキュメントで関連過去レポートの参照証明 (節番号 + 要約 + 接続) | v112_phase_design.md §1 |
| 「単一勝負案」を主題タイトルに明記 | v112_phase_design.md §4.1 |
| 母集団不足時の対応を **4 項目固定** (条件をいじりながら観察する抜け道を塞ぐ) | v112_phase_design.md §13.2 |
| 「観察できる軸が見えた」を駆動要因にしない (規律 §35 #10) | v112_phase_design.md §4.4 |
| Step Z 事前調査フェーズ追加 (実装前に Web Claude 想定と実環境の乖離を検出) | v112_implementation_brief.md 第 2 版 §1 |
| Code A 規律遵守自己検証 | v112_code_recognition_check.md §3 |
| §5.6 規律チェックリスト (案 X、お守り規律) | v112_phase_design.md 第 4 版 §5.6 |

---

## 7. 実装ファイル所在マップ

### 7.1 各バージョンの主要 .py モジュール

```
v104: v104_be3_postprocess.py / v104_integration.py / v104_observation_target.py
v105: v105_integration.py (機構 A/C 本体、:1035 で「β 側: Q/C 100% 継承」)
      v105_animate_*.py (3 layer / compare / grid / integration)
v106: v106_post_process.py (atom_alignment_observer)
      v106_atom_match_classification.py (26 atom 構造的特異性)
      v106_step10_baseline.py / v106_event_trajectory.py / v106_pulse_trajectory.py
v107: v107_event_aggregator.py / v107_path_analyzer.py / v107_baseline_constructor.py
      v107_avalanche_monitor.py / v107_post_process.py / v107_cross_seed_analyzer.py
v108: v108_atom_event_generator.py (atom_introduction_event 機構)
      v108_baseline_recalculator.py (各変動条件で baseline 再計算)
      v108_global_activation_correction.py / v108_subsidiary_observations.py
      v108_post_process.py (orchestrator)
v109: v109_atom_event_generator.py / v109_baseline_recalculator.py
      v109_bimodal_analyzer.py / v109_sensitivity_evaluator.py
      v109_design_table_compiler.py / v109_post_process.py
v110: v110_atom_event_generator.py / v110_baseline_recalculator.py
      v110_environment_check.py (build_alpha_beta_intervals)
      v110_multi_axis_stratified_analyzer.py / v110_n_core_stratified_analyzer.py
      v110_round2_analyzer.py / v110_post_process.py
      v110_design_table_compiler.py / v110_sensitivity_evaluator.py
v111: v111_q_c_inherited_observer.py / v111_response_profile_compiler.py
v112: v112_step_z_environment_check.py (Step Z 主、母集団実測)
      v112_step_z_n_core_addendum.py (Step Z 補完、Taka 指摘対応)
```

### 7.2 各バージョンの主要レポート

```
v104: v104_main_run_report.md
v105: v105_main_run_report.md / v105_main_v2_run_report.md
v106: v106_main_run_report.md (および 7 件の専用レポート)
v107: v107_main_run_report.md / v107_implementation_brief.md / v107_code_recognition_check.md
v108: v108_main_run_report.md / v108_implementation_brief.md / v108_code_recognition_check.md
v109: v109_main_run_report.md / v109_implementation_brief.md / v109_phase_design.md
v110: v110_main_run_report.md / v110_phase_design.md / 第一弾 + 第二弾 layered analysis
v111: v111_main_run_report.md / v111_phase_design.md / v111_code_recognition_check_v2.md
v112: v112_phase_design.md (第 4 版、現行) / v112_implementation_brief.md (第 3 版、現行)
      v112_step_z_report.md / v112_code_recognition_check.md (Step A 認識確認)
```

### 7.3 出力データ所在 (developmental/v{V}/outputs/main/)

各バージョンの main 出力は `developmental/v{V}/outputs/main/` 配下:
- v107: 222 files
- v108: 368 files
- v109: 277 files
- v110: 213 files
- v111: 56 files (q_c_inherited_*)
- v112: 出力 7 files (Step Z のみ、main run 未実施)

bit-identity 層 B 不変対象: v107 + v108 + v109 + v110 + v111 = 約 1,136 files

---

## 8. v10.12 現状 (2026-05-11)

### 8.1 完了した Step

- **Step Z 事前調査** (commit df04d0a、2026-05-10): 4 件の重大乖離検出
- **Step Z 補完 n_core 層化** (Taka 指摘、commit df04d0a): cond3 が ESDE 88% を排除する排他条件と判明
- **Step A 認識確認** (commit ddd595a、2026-05-10): Q-A1 重大ブロッカー警告

### 8.2 Q-A1 重大ブロッカーの内容

trial-B (bin_2 × 4 条件) は構造的に paired_d 算出不能:
- per seed 0.2 / total 4 events (Q3 維持時)
- 主因: cond4 (familiarity top 25%) が bin_2 で稀少 (12.5%)
- Q2 緩和でも per seed 0.4 程度で解消されない
- Code A 提案: trial-B のみ cond4 を top 50% 緩和 (Web Claude/Taka 判断要請)

### 8.3 Web Claude/Taka 判断対象 (DC-A1〜DC-A5)

| DC | 内容 | Code A 提案 |
|---|---|---|
| DC-A1 | trial-B cond4 緩和 (Q-A1 対応) | top 50% 緩和 |
| DC-A2 | top_quartile_threshold | per-seed (std/global=0.61) |
| DC-A3 | v108_original 流用 vs 再計算 | 流用 (層 B 不変) |
| DC-A4 | bootstrap CI n_iter | 1000 (主軸) / 500 (副次) |
| DC-A5 | target_step / natural baseline 詳細 | Web Claude 確認要 |

### 8.4 次のアクション

1. 新 Web Claude が `v112_response_to_code_a.md` で DC-A1〜DC-A5 + Q-A7 即決事項を返答
2. Taka 承認
3. Code A Step B (環境チェック詳細 + Q2/top_quartile 実測 + trial-B 緩和案ありの場合の母集団再実測)
4. Code A Step C-L (実装 → smoke → main run → cross-seed 集計 → 完了報告)

### 8.5 計算量・ストレージ

- main run 推定 1-2 分 (24 並列、6 conditions × 6 baselines = 36 baseline)
- storage 累計 v107-v112 約 2.0-2.5 GB / 上限 6 GB (33-42%)

---

## 9. 関連資料への索引

### 9.1 主題ドキュメント (v10.4 以降)

```
developmental/v107/v107_implementation_brief.md
developmental/v108/v108_phase_design.md (推定、未確認)
developmental/v109/v109_phase_design.md
developmental/v110/v110_phase_design.md
developmental/v111/v111_phase_design.md
developmental/v112/v112_phase_design.md (第 4 版、現行) ← 本主題
```

### 9.2 上位資料

```
docs/ai_summaries/
├── 06_developmental_summary.md (v10.0-v10.3、2026-04-28 凍結)
├── 06b_developmental_phase15_summary.md (本資料、v10.4-v10.12)
├── 07_concept_core.md
├── 08_esde_system_structure.md (Layer 5 を含む)
└── 09_audit_principles.md (規律累積)

docs/
├── ESDE_Developmental_Report.md (詳細版、801 行)
├── ESDE language/
│   ├── esde_cell_architecture.md (v2.3、2026-02-08、最新階層)
│   ├── ESDE_Glossary.md (v5.7.0、2026-02-11、用語集)
│   └── ESDE_Module_Reference_Lexicon_v2.md (Lexicon v2 Pipeline)
└── 概念理解.md
```

### 9.3 運用マニュアル

```
esde_3ai_operations_manual.md (3 AI 共通運用、参照証明形式 §2.2)
```

### 9.4 v10.5 機構実装本体

```
developmental/v105/v105_integration.py (β 側 Q/C 100% 継承、機構 A 本体)
```

### 9.5 v10.7 オービス本体

```
developmental/v107/v107_event_aggregator.py (5 source_event 集約)
developmental/v107/v107_path_analyzer.py (5 relation_path 構築)
developmental/v107/v107_baseline_constructor.py (5+1 baseline 構築 + delta + excess)
```

### 9.6 v10.8 atom_introduction_event 本体

```
developmental/v108/v108_atom_event_generator.py (25 atom × 100 cid × 24 seeds)
```

### 9.7 v10.9 4 種設計表 + 寄与候補感度評価本体

```
developmental/v109/v109_design_table_compiler.py
developmental/v109/v109_sensitivity_evaluator.py
developmental/v109/v109_bimodal_analyzer.py
```

### 9.8 v10.10 Multi-gate × timing + 多軸層化本体

```
developmental/v110/v110_multi_axis_stratified_analyzer.py
developmental/v110/v110_n_core_stratified_analyzer.py
developmental/v110/v110_round2_analyzer.py
```

### 9.9 v10.11 q_c_inherited within-cid observer 本体

```
developmental/v111/v111_q_c_inherited_observer.py
developmental/v111/v111_response_profile_compiler.py
```

### 9.10 v10.12 Step Z 本体

```
developmental/v112/v112_step_z_environment_check.py (Q-Z1-Q-Z7 実測)
developmental/v112/v112_step_z_n_core_addendum.py (n_core 別補完、Taka 指摘対応)
```

---

## 10. 新 Web Claude スレッドへの引き継ぎ重要事項

### 10.1 v10.12 主題の本質 (Taka 整理 §1.9 参照)

**「会話への接続」ではなく「字面に揺れながら反応するシステム = ESDE Atom スレッド = 連結基盤の第一スレッドの精緻化」**

LLM が持たない唯一無二の強み (字面に対する揺れる反応) を確立するフェーズ。意味理解 / 出力機構 / 双方向性は v10.12 では扱わない。

### 10.2 Web Claude が陥りやすい落とし穴 (v10.10/v10.11 教訓)

1. **観察軸を増やす方向への転換**: Code A 母集団不足を契機に、Multi-gate 化や within-cid design に転換しないこと
2. **v10.5 機構の自明な再観察**: 主題が v10.5 §7.4-§7.10 既知事実の延長になっていないか事前確認
3. **v10.10 §3.4 反応 type 分業の無視**: bin_2 = pulse / bin_5+ = delta_C の分業を主題設計時に反映
4. **規律 §35 #9 違反**: 主題着手前に v10.5 機構実装 + v10.10 §3.4 を読む
5. **「Web Claude の想定はだいたい結構ズレる」(Taka 指摘)**: Step Z 事前調査で前提を実測、設計判断は Code A 実測後

### 10.3 即決確認すべき項目 (v10.12 進行のため)

新 Web Claude は以下を確認してから次のアクションへ:

1. v112_phase_design.md 第 4 版を読む
2. v112_implementation_brief.md 第 3 版を読む
3. v112_step_z_report.md (Step Z 結果) を読む
4. v112_code_recognition_check.md (Step A、Code A 認識確認) を読む
5. 上記 4 つを踏まえ、`v112_response_to_code_a.md` で DC-A1〜DC-A5 + Q-A1 重大ブロッカー対応 + Q-A7 を返答
6. Taka 承認後、Code A Step B 進行

---

## 11. 一文サマリ (再掲、構造化版)

ESDE Phase 1.5 (v10.4-v10.12、2026-04-30〜現在) は単 cid 系から cid 集団 + Atom 取り込み機構への拡張段階、v10.4-v10.5 で Layer 5 (α/β-Integration、機構 A 「β に Q/C 100% 継承」+ 機構 C 「Recorded ε=1」) 確立、v10.6 で 25 atom 構造的特異性、v10.7 で post-process オービス完成 (5 source × 10 path × 415K events / 3.45M excess)、v10.8 で atom_introduction_event 機構 (25 atom × 60K events) + Level 3.5 「introduced は natural の半分」発見、v10.9 で 4 種設計表完成 (timing > cid > QC 感度階層、high_fam_out 0.222 最強、age=200 で若い cid 強反応) + Phase 1.5 第四試行 (選抜試験)、v10.10 で Multi-gate × timing 多軸層化 + n_core 別層化で「pulse 系は bin_2 / delta_C 系は bin_5+」反応 type 分業発見 (ただし観察延長への逸脱、v10.10 §3.4 が以降必須参照)、v10.11 で q_c_inherited 起点 within-cid 観察が v10.5 機構 A の自明な再観察に終わる (規律 §35 #9 違反、3 AI 全員が v10.5 §7 未参照)、v10.12 で「条件適応型 atom 導入の単一勝負案」(v10.10 でやるべきだった主題) を 2 trial 分割設計 (trial-A bin_5+ × delta_C / trial-B bin_2 × pulse) で再開、第 4 版主題 + Step Z 事前調査 + §5.6 規律チェックリスト (案 X) で前提を実測ベースに修正、Step A 認識確認で Q-A1 重大ブロッカー (trial-B 母集団 per seed 0.2、cond4 が bin_2 で稀少という構造的問題) を警告、Web Claude/Taka 判断待ち、累積規律 41 件 + §35 メタ規律 10 項目 + §5.6 規律チェックリスト確立、留保事項 22 件累積、bit-identity 全層 PASS 維持 (v107-v111 約 1,136 files 不変)、storage 累計 1.52 GB (上限 6 GB の 25%、v10.12 後も 50% 余裕)、Taka 整理 §1.9 (2026-05-10) で「v10.12 は会話への接続ではなく字面に揺れながら反応するシステム = ESDE Atom スレッド = 連結基盤の第一スレッドの精緻化」と本主題の位置づけ確定、新 Web Claude スレッドはまず v112_phase_design.md 第 4 版 + v112_implementation_brief.md 第 3 版 + v112_step_z_report.md + v112_code_recognition_check.md を読み、`v112_response_to_code_a.md` で DC-A1〜DC-A5 + Q-A1 対応を返答することで進行再開可能。

---

*以上、Code A による Phase 1.5 (v10.4-v10.12) 状況引き継ぎ資料。新 Web Claude スレッドはこれを context 0 件目で読むこと。次の更新は v10.12 主題完了時。*
