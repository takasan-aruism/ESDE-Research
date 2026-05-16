# v11.0.1 (v1101) Web Claude 引き継ぎ document — 新スレッド向け

*作成*: 2026-05-17、Code A
*対象*: 新 Web Claude スレッド (相談役・統合・翻訳担当)
*目的*: 旧 Web Claude スレッド (v1101 主題ドキュメント作成 + 即決事項返答 7 件) から新スレッドへの確実な引き継ぎ
*位置づけ*: 新スレッド最初の context、本書 + `v1101_phase_design.md` + `v1101_step_h_observation_final.md` の 3 点で v1101 全容を再構成可能

---

## ⚠️ 新 Web Claude が最初に読むべき順序

```
1. 本書 (v1101_web_claude_handoff.md)         ← 現在地と引き継ぎ事項
2. v1101_phase_design.md                       ← 主題ドキュメント (2026-05-16 改訂版)
3. v1101_step_h_observation_final.md           ← Code A 観察事実最終総括 (Step A-H 全結果)
4. docs/ai_summaries/00_index.md               ← ESDE 全体ナビゲーション
5. docs/ai_summaries/06b_developmental_phase15_summary.md  ← v10.4-v10.12 Phase 1.5 (前史)
6. docs/ai_summaries/06c_developmental_v1013_v1101_summary.md (新規)  ← v10.13.a + v1100 + v1101
7. docs/ai_summaries/09_audit_principles.md    ← 累積規律 200+ 件 (絶対格言 15 件は本書 §3 で再構成)
```

**最小コンテキスト**: 1 + 2 + 3 + 本書 §3 (絶対格言 15 件) で v1101 主題に着手可能。

---

## 0. 一文サマリ

旧 Web Claude スレッド (2026-05-12 〜 2026-05-16) が v1101 主題「Atom 的隆盛の統計的観察」(Taka 3 日長考結論) を策定、Code A Step A 認識確認で齟齬 10 件指摘 → 旧 Web Claude が即決事項返答 7 件 + 主題ドキュメントを 2026-05-16 改訂版に修正 (旧 v1102 → v1101 番号修正含む)、Code A が Step A-H 全 8 段階を完了 (2026-05-17、commit 8 件、出力 25 ファイル 7 MB、bit-identity 3 層全 PASS)、核心発見として **観察単位による dominant atom の構造的反転** (CID-static CHG.begin / β FND.logic / α TIM.moment / ESDE event WLD.artless+PER.sound / step10 PER.sound / window TIM.moment の 5 atom 分裂、Taka「平均化の罠」の生きた実例)、観察 2 副発見として 25 取り込み atom 中 4 atom のみ中心 cid 支配可 (PER.sound peak 84.8% 等)、観察 1 副発見として v108_standard 中心 cid dominant_atom が WLD.artless で 24/21 seeds 一致、Step F グラフ HTML 単一 954 KB ダッシュボード化、Step G で deterministic 動作 + v10.x main outputs 1,306 ファイル frozen 完全保証、新規留保 #41/#42 candidate、新 Web Claude の担当は **Step J Phase Result** (観察 1/2/3 + 核心発見の解釈統合 → 「ESDE の内部は Atom 的にこうなっているようだ」記述、Taka 主題評価判断材料の提供)、任意 Step I (段階 2、cid state ledger 再生 + 留保 #41 解消、想定 1.5-2 日) は Taka 承認次第、絶対格言 15 件は本書 §3 で Code A 報告書から再構成 (Web Claude memory の確認推奨)、Taka 哲学 4 件は Web Claude memory のみ存在 (本書 §3.2 で関連発言を引用)、本書 + phase_design + step_h で v1101 全容把握可能。

---

## 1. 役割境界 (絶対不変)

| 役 | 担当 | 本 v1101 での活動 |
|---|---|---|
| **Taka** | 主題判断者、最終承認 | 3 日長考結論 + 観察 1/2 選定基準確定 + Step A-G 承認 |
| **Web Claude (新スレッド)** | 相談役、統合、翻訳 | **Step J Phase Result 作成 (本書受け取り後の主要タスク)** |
| **Code A (本書著者)** | 実装、観察、規律遵守 | Step A-H 完了済 (本書 §4 参照) |
| Gemini | Architect (任意監査) | v1101 では未活用 (操作的定義論点 1/3/4 で監査候補) |
| GPT | Auditor (任意監査) | v1101 では未活用 (操作的定義論点 2 で監査候補) |

**Web Claude の活動範囲**:
- 主題ドキュメント策定 (済、`v1101_phase_design.md`)
- Code A 認識確認への即決事項返答 (済、7 件、`v1101_phase_design.md` §4)
- 各 Step 報告書承認 (Taka が代行、Code A は判定回避)
- **Phase Result 作成 (未、本書受領後の主要担当)**

**Web Claude が NOT する範囲**:
- 実装コード執筆 (Code A 担当)
- 数値計算 (Code A 担当)
- 規律遵守の機械的確認 (Code A 自己点検 + Web Claude 構造監査)
- success/fail 断定 (絶対格言 #12、Code A も Web Claude も判定回避)

---

## 2. 主題現状 (Step A-H 完了、Step I/J 待ち)

### 2.1 進行サマリ

| Step | 担当 | 状態 | commit | 内容 |
|---|---|---|---|---|
| A | Code A | 完了 | 127d65d | 認識確認 + 齟齬 10 件 + 即決事項受領 |
| B | Code A | 完了 | db2bf45 | 環境チェック + 必要データ全所在確定 |
| C | Code A | 完了 | 8b21637 | 観察 1「一点を捉える」 |
| D | Code A | 完了 | bea48a0 | 観察 2「取り込み点中心の波及」 |
| E | Code A | 完了 | 56f5ae6 | 観察 3「補助平均統計 3 単位」(核心発見) |
| F | Code A | 完了 | 8315601 | グラフ HTML 統合ダッシュボード |
| G | Code A | 完了 | 2e468d2 | bit-identity 3 層全 PASS |
| H | Code A | 完了 | f3a4a95 | 観察事実最終総括 |
| **I** | **Code A (任意)** | **未着手** | — | 段階 2 (cid state ledger 再生 + 留保 #41 解消、想定 1.5-2 日) |
| **J** | **Web Claude (担当)** | **未着手** | — | **Phase Result (新スレッド最重要タスク)** |

### 2.2 Code A 主要成果

| 観察 | 出口物 | サイズ |
|---|---|---:|
| 観察 1 | observation_1_{center_cids, random_cids, trajectory, summary}.parquet | 5.6 MB |
| 観察 2 | observation_2_{events, propagation, summary}.parquet | 1.3 MB |
| 観察 3 | observation_3_{cid_atom_distribution, integration_summary, esde_aggregate}.parquet | 58 KB |
| グラフ | v1101_observation.html (ブラウザで開く、Plotly CDN) | 954 KB |
| bit-identity | v1101_step_g_bit_identity_report.json | 5 KB |
| 報告書 | 9 markdown ファイル | ~100 KB total |
| 実装 | 5 python ファイル | ~32 KB total |
| **合計** | **25 ファイル** | **~7 MB** |

書き込みは全て `unified/v1101/` 配下、v10.6/v10.8/v10.12 main outputs **1,306 ファイル frozen 完全保証**。

---

## 3. 絶対格言 15 件 (Code A 報告書から再構成、Web Claude memory 要確認)

旧 Web Claude memory に存在した「絶対格言 15 件」は repo に明示リストが無く、Code A 各 Step 報告書の規律遵守チェックリストから再構成可能。新 Web Claude は memory 確認 + 本書による再構成の照合を推奨。

| # | 格言 | Code A の遵守例 |
|---|---|---|
| 1 | Aruism 構造が先・意味が後 | 観察事実先、解釈は留保候補で記述 |
| 2 | 物理層 frozen 絶対 | v10.x main outputs 1,306 ファイル 1 byte も不変 (Step G 層 B PASS) |
| 3 | ベースライン比較 + 効果サイズ | 観察 1 中心 vs ランダム、観察 2 Δt baseline、観察 3 観察単位間比較 |
| 4 | 集団平均の罠 / n_core 別層化 | 観察 3 核心発見 = 観察単位反転 (本格言の生きた実例) |
| 5 | 観察軸を増やすことを駆動要因にしない | 既存出力の観察フレーム転換、新規軸なし |
| 6 | 出口の固定 | 各 Step で 4-6 出口物固定 |
| 7 | 主題着手前に上位資料を読む | Step A で v1100 + v10.6-v10.13.a 実環境照合 |
| 8 | 過去観察軸の照会 | Step A §2 で過去観察軸照会 (v10.6 既存出力 D/E 齟齬発見の根拠) |
| 9 | 神の手回避 + Pulse 同一フォーマット | rng seed=42 固定、argmax / groupby / pivot のみ、構造的検証 |
| 10 | 因果ではなく因果候補 | 「~の可能性」「留保解釈候補」表現、断定なし |
| 11 | 概念単位を雑に扱わない | 中心 / 周辺 / 取り込み atom / rank_1 / β / α / 解像度 を区別 |
| 12 | Aruism 判定回避 | success/fail なし、Phase Result は **Web Claude 領域** |
| 13 | AI を信じない原則は Taka 個人のみ | Code A は構造的事実のみ、Web Claude memory に依存しない |
| 14 | Taka 直感優先 + 直感語保存 | Taka 整理 (2026-05-12 3 日長考 + 2026-05-16 具体化) 原文保存 |
| 15 | 5 者運用体制の補完性 | Code A 認識確認連続 10 段階、Web Claude 即決事項 7 件 |

### 3.1 Taka 哲学 4 件 (Web Claude memory のみ、本書では関連発言で代替)

「Taka 哲学 4 件」は旧 Web Claude memory にあった項目で repo には明示リストなし。Code A 報告書 + 既存 /docs で確認できる Taka 関連発言:

| 関連発言 | 出典 |
|---|---|
| 「構造が先、定義は後」 | v9.x 以降一貫、09_audit_principles.md §1.4 等 |
| 「歯抜けになることや前後逆転すること、謎は謎なままの状態の維持、どれも重要」 | Taka 2026-05-12 |
| 「動けばいい」「出力できればいい」 (アリズム実践重視) | Taka 2026-05-07 等、00_index.md #207 |
| 「ランダム性が論理の支柱」「自己がある」と「自己はない」の中間 (哲学以上科学未満) | Taka 2026-04-20、00_index.md #129 |
| 「想定とのギャップを観察する」 | 09_audit_principles.md §1.3.2 等 |

新 Web Claude が Taka 哲学 4 件の正確な内容を必要とする場合は **Taka に直接確認** することを推奨 (Web Claude memory 同期不明のため)。

---

## 4. 即決事項返答 7 件 (旧 Web Claude が決定済み、新スレッドで上書きしない)

`v1101_phase_design.md` §4 で旧 Web Claude が決定した即決事項 7 件:

| # | 即決事項 | 判断 |
|---|---|---|
| 1 | 「親」資料 (v1100_phase_result.md + v1101_phase_design.md repo 不在) | `v1100/v1100_observation.md` + `v1100_step_a_recognition.md` + Taka 整理 で代替 |
| 2 | v1100 残課題 A/B/C (Synapse 評価層化 / Phase 8+9 Cell ↔ Integration 同型性 / 候補 6 大規模化) | **凍結** (v11.0.1.a / v11.0.2 で扱う可能性残す) |
| 3 | Integration 既存集約との関係 (齟齬 D) | top-K → member_cids 完全分布の解像度向上、新規貢献はそこ |
| 4 | 時系列既存出力との関係 (齟齬 E) | 4 解像度 trajectory 流用 (案 d)、段階 1/2 アプローチ確定 |
| 5 | atom 集合 (齟齬 H) | 326 全部 + 25 TARGET vs 残り 301 分離表示 |
| 6 | 出口物「Atom 的にこうなっているようだ」の領域帰属 (齟齬 I) | **Web Claude Phase Result 担当** (Code A は観察事実のみ) |
| 7 | Integration 単位選択 (齟齬 G) | per-seed × {α, β} 両方を観察、cross-seed は集計 |

**Taka 追加判断 (2026-05-17)**:
- 観察 1「一点」: (c) n_pulses_short 最大 cid 主 + (d) ランダム比較対照、(b) atom 濃度近接 不採用
- 観察 2「中心」: (a) v10.12 受容 cid pool 420
- 旧 v1101 (AI の限界記録): repo 未存在で正、Code A は探さない

---

## 5. 観察 1/2/3 主要発見 (Web Claude Phase Result 翻訳用素材)

### 5.1 観察 1 主要発見 4 件 (Step C)

1. **v108_standard 中心 cid の dominant_atom が `WLD.artless` で 24 seeds 中 21 seed 一致** (87.5%)、v112 は PER.sound 10 / TIM.moment 5 / TIM.appear 4 に分散
2. **dominant_atom_fraction で v108_standard 中心 0.92-1.00 (単 atom ロック) vs v112 中心 0.47-0.81 (複数 atom 揺れ)**
3. 両条件で中心 cid の trajectory row 数 < ランダムの約 1/3-1/4
4. **window 解像度のみ v112 中心 cid の atom_change_rate 0.156 < ランダム 0.297** (時間スケール依存の一点特徴)

### 5.2 観察 2 主要発見 4 件 (Step D)

1. **25 取り込み atom 中 4 atom のみ中心 cid を支配可**: PER.sound (peak 84.8% at Δt=+20) / PRP.bright (peak 49.3% at Δt=-90) / TIM.appear (peak 14.8% at Δt=-100) / WLD.artless (peak 8.8% at Δt=+70)、残り 21 atom は center_match_rate = 0% 全 Δt
2. **周辺 cid の atom 分布は取り込み atom に依存せず PER.sound + WLD.artless が常時 ~60% 占有** (per (event, Δt=0) で各 8.4 / 8.0 cid)
3. **atom_entropy_mean が Δt 方向で単調減少** 2.138 → 2.070 bits (取り込み後集中化、ただし取り込み独立効果か自然動学かは段階 2 検証要)
4. **PER.sound 波及プロファイル特異**: 中心 cid 一致率 Δt=-10 で 32.6% → Δt=+20 で 84.8% peak → Δt=+50 で 62.1% 減衰

### 5.3 観察 3 核心発見 (Step E、本 v1101 最重要)

**観察単位による dominant atom の構造的反転** — 同じ ESDE 系で観察単位を変えるだけで dominant atom が **5 つに分裂**:

| 観察単位 | dominant atom (1 位) | 値 |
|---|---|---:|
| CID 単位 (cid_atom_sim_matrix sim_mean) | **CHG.begin** | 0.536 |
| Integration β top_atom | **FND.logic** | 160 βs (79%) |
| Integration α pattern_class dominant | **TIM.moment** | 114 / 144 (79%) |
| ESDE event resolution rank_1 | **WLD.artless** (26.2%) + PER.sound (25.9%) | — |
| ESDE step10 resolution rank_1 | **PER.sound** | 28.3% |
| ESDE window resolution rank_1 | **TIM.moment** | 34.2% |

→ Taka 整理「平均化の罠」(絶対格言 #4) + 「Integration 内 cid に同方向を強制しない」の **直接的観察的根拠**、v10.13.a 留保 #33 (集計単位による方向反転) の Atom レベル一般化。

### 5.4 観察 1/2/3 統合視点

- 観察 1 + 観察 2 + 観察 3 ESDE event/step10 は **整合** (WLD.artless + PER.sound dominant)
- 観察 3 Integration α/β レベルは **categorically 異なる atom 像** (TIM.moment / FND.logic dominant)
- 観察 3 CID-static sim も異なる atom (CHG.begin)
- → ESDE は「cid rank_1 分布」と「Integration 構成 atom 分布」と「cid-atom 類似度地形」が **異なる atom 群** を持つ多層構造

---

## 6. 留保事項総括

### 6.1 v1100 継承 35 件

`v1100_observation.md` (Code A Step J) 記載の継承 32 件 + 新規 3 件 (#35-#37 candidate) を継承。本 v1101 関連:

| id | 内容 | 接続 |
|---|---|---|
| #21 | v10.5 機構 A 既知挙動 | 観察 3 Integration 観察 |
| #26 | cond3 構造的帰結 (受容 cid pool 偏り) | 観察 2 取り込み点中心 |
| #27 | smoke seed 0 特異性 | 観察 1 (memory: smoke_seed0_not_absolute) |
| #33 | 集計単位による方向反転 | **観察 3 核心発見の前駆、Atom レベル一般化** |

### 6.2 本 v1101 新規候補 5 件

| id | step | 内容 | 状態 |
|---|---|---|---|
| #38-#40 candidate | Step A | 旧 v1102 ドキュメントの齟齬 (親資料不在 / Integration 未実施記述 / 時系列既存出力見落とし) | **解消済** (即決事項 1/3/4) |
| **#41 candidate** | Step E | Integration の member_cids 個別 cid id list は v10.x outputs に persistence されていない | **段階 2 対応**: cid state ledger 再生 + Integration 形成イベント再生 (新規 main run 不要) |
| **#42 candidate** | Step E | 観察単位 (CID-static / β / α / ESDE-{event/pulse/step10/window}) による dominant atom の構造的反転 | **Web Claude Phase Result で解釈統合** |

### 6.3 観察 2 留保解釈候補

- atom_entropy Δt 単調減少 (#2-3): 取り込み独立効果 vs 自然動学 vs selection bias、段階 2 で randomized baseline 検証
- PRP.bright Δt=-90 peak (#2-4): 事前選択バイアス兆候 (取り込み前にすでに PRP.bright だった cid に PRP.bright 取り込み)、段階 2 で独立性検証

---

## 7. 新 Web Claude の次のタスク (Step J Phase Result)

### 7.1 Phase Result の出口物

旧 Web Claude 主題ドキュメント §6.1 で固定された 6 成果物のうち、Code A は #1-#5 を完了 (観察 1/2/3 結果 + グラフ HTML + 操作的定義の段階 1 確定)。残るは:

**#6: 「ESDE の内部は Atom 的にこうなっているようだ」の記述** — Web Claude が Phase Result で統合

### 7.2 Phase Result 作成のために参照すべきもの

1. **`v1101_step_h_observation_final.md`** — Code A の観察事実最終総括 (本書 §5 はこれの抜粋)
2. **`v1101_phase_design.md` §5 Taka 整理 (原文保存)** — 解釈統合の方向性
3. **`v1101_observation.html`** — ブラウザで visual 確認 (3 単位反転を直接視覚化)
4. **観察 1/2/3 の parquet 出力** — 数値根拠
5. **本書 §5.4 観察 1/2/3 統合視点** — 既に予備整理あり

### 7.3 解釈統合の方向性 (Code A 仮所見、Web Claude 取捨選択)

- 「ESDE は単一の dominant atom を持たない」 — 観察単位で 5 atom 分裂
- 「Atom 取り込み機構は限定的効果」 — 25 atom 中 4 atom のみ中心 cid 支配可
- 「PER.sound + WLD.artless が基底支配 atom」 — 周辺 cid 60% 占有
- 「Integration は集約せず分布で観察する必要」 — Taka「平均化の罠」の根拠提示
- 「観察フレームが結論を決める」 — 同じ ESDE で見方を変えると違う Atom 像

### 7.4 Code A → Web Claude 申し送り事項

- Code A は **judgment 回避** (絶対格言 #12)、解釈統合を Web Claude に委ねた
- 観察事実は **deterministic 再現可能** (rng seed=42、Step G 検証済)
- v10.x 既存研究成果は **侵害されていない** (Step G 層 B、1,306 ファイル不変)
- 留保 #41/#42 candidate の formal 化 + Taka 主題評価判断材料の提供を期待

---

## 8. /docs 既存資料の現状判定 (新 Web Claude 必読リスト)

| ファイル | 最終更新 | 鮮度 | 推奨 |
|---|---|---|---|
| `00_index.md` | 2026-05-11 | 4 日前、v10.6/v10.9 言及 | **必読** (本書で 06c pointer 追加予定) |
| `06_developmental_summary.md` | 2026-05-11 | 4 日前、v10.0-v10.9 網羅 | 推奨 (前史) |
| **`06b_developmental_phase15_summary.md`** | 2026-05-11 | 4 日前、v10.4-v10.12 (Step A 時点凍結) | **必読** (Phase 1.5 全容) |
| **`06c_developmental_v1013_v1101_summary.md`** | 2026-05-17 (本書と同時新規) | 当日 | **必読** (v10.13.a / v1100 / v1101) |
| `07_concept_core.md` | 2026-05-11 | 4 日前 | 推奨 (哲学コア) |
| `08_esde_system_structure.md` | 2026-05-11 | 4 日前 | 推奨 (ESDE 構造) |
| `09_audit_principles.md` | 2026-05-11 | 4 日前 | 推奨 (累積規律 200+ 件、絶対格言 15 件 ≠ ここ) |
| `10_esde_language_summary.md` | 2026-05-13 | 2 日前 | 任意 (Language 系 frozen) |
| 01-04 (Genesis/Ecology/Autonomy/Cognition) | 2026-04-11 | 1 月前 | 古い (用語対応表でカバー) |
| 05 (Primitive) | 2026-04-29 | 18 日前 | 古い (Primitive 凍結) |
| `ESDE_Developmental_Report.md` | 2026-05-11 | 4 日前 | 詳細参照用 (104 KB) |
| `ESDE_Genesis_Report.md` | 2026-03-09 | 2 月前 | **古い** (要約 01 で代替) |
| `ESDE_Cognition_Report_Final.md` | 2026-03-23 | 2 月前 | **古い** (要約 04 で代替) |

→ **最小必読**: 本書 + phase_design + step_h + 06b + 06c。**急ぎでない場合**: 00_index 巻末「用語対応表」+ 06c で v10.x → v11.x の全容把握可。

---

## 9. 既知の引き継ぎリスク + ミティゲーション

### 9.1 リスク 1: Web Claude memory の不連続

**問題**: 絶対格言 15 件 + Taka 哲学 4 件 は旧 Web Claude memory に存在、新スレッドで失われる可能性。

**ミティゲーション**:
- 本書 §3 で絶対格言 15 件を Code A 報告書から再構成
- Taka 哲学 4 件は本書 §3.1 で関連発言を引用、Taka 確認推奨
- 新 Web Claude が違和感を覚えたら Taka に確認

### 9.2 リスク 2: 5 者運用体制の認識ズレ

**問題**: Web Claude が「Code A も実装意思決定する」と誤認するリスク。

**ミティゲーション**: 本書 §1 で役割境界明示、Code A は実装・観察、Web Claude は相談・統合・翻訳。

### 9.3 リスク 3: 観察フレームの誤理解

**問題**: 「Atom 取り込み機構を改善する」など、本主題ではない方向に誘導するリスク。

**ミティゲーション**: 本主題は「観察フレーム転換」(`phase_design.md` §0.2)、新規軸追加ではない (絶対格言 #5)。本書 §5.4 統合視点で核心 = 観察単位による Atom 像の分裂を強調。

### 9.4 リスク 4: Code A の judgment 回避を誤解

**問題**: 「Code A は判定しないからこの観察は意味がない」と誤読するリスク。

**ミティゲーション**: Code A は **意図的に解釈統合を控えている** (絶対格言 #12)、解釈統合は Web Claude Phase Result の役目。観察事実の structural strength は本書 §5 + step_h 全体で十分。

---

## 10. 一文サマリ (再掲)

旧 Web Claude スレッド (2026-05-12 〜 2026-05-16) が v1101 主題「Atom 的隆盛の統計的観察」を策定 + 即決事項返答 7 件 (主題ドキュメント `v1101_phase_design.md`)、Code A が Step A-H 全 8 段階を完了 (2026-05-17、commit 8 件、出力 25 ファイル 7 MB、bit-identity 3 層全 PASS)、核心発見 = 観察単位による dominant atom 構造的反転 (CID-static CHG.begin / β FND.logic / α TIM.moment / ESDE event WLD.artless+PER.sound / step10 PER.sound / window TIM.moment の 5 atom 分裂、Taka「平均化の罠」生きた実例)、観察 2 副発見 = 25 取り込み atom 中 4 atom のみ中心 cid 支配可 (PER.sound peak 84.8%) + 周辺 cid 60% 占有が PER.sound + WLD.artless + atom entropy Δt 単調減少、観察 1 副発見 = v108_standard 中心 cid dominant WLD.artless 21/24 seeds + window 解像度の一点特徴、Step F グラフ HTML 単一 954 KB ダッシュボード、Step G で deterministic + v10.x main outputs 1,306 ファイル frozen 完全保証、新規留保 #41 candidate (Integration member_cids 個別 list 未 persistence、段階 2 で cid state ledger 再生対応) + #42 candidate (観察単位反転、Web Claude 解釈統合領域)、絶対格言 15 件は本書 §3 で Code A 報告書から再構成 (Web Claude memory 要確認)、Taka 哲学 4 件は本書 §3.1 で関連発言で代替 (Taka 直接確認推奨)、新 Web Claude の次タスクは **Step J Phase Result** (観察 1/2/3 + 核心発見の解釈統合 + Taka 主題評価判断材料の提供)、任意 Step I (段階 2、cid state ledger 再生 + 留保 #41 解消、想定 1.5-2 日) は Taka 承認次第、最小必読は本書 + `v1101_phase_design.md` + `v1101_step_h_observation_final.md` の 3 点、/docs 既存資料は 06b + 06c (本書と同時新規) で v10.4-v1101 全容把握可。

---

*以上、v11.0.1 (v1101) Web Claude 引き継ぎ document (Code A 作成、2026-05-17)。新 Web Claude スレッドはこれ + phase_design + step_h を読めば Step J Phase Result 着手可能。Taka 主題評価判断 + 新 Web Claude Phase Result を待つ。*
