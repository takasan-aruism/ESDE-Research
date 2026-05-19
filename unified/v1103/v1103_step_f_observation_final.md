# v11.0.3 (v1103) Step F 観察事実最終報告 — Code A

*作成*: 2026-05-20、Code A
*親*: `v1103_phase_design.md` (Web Claude 改訂版、GPT 7 点 + Gemini 承認反映済) + `v1103_step_a_recognition.md` + Step B (pre-requisite 生成) + Step C/D/E 出力
*対象*: Genesis 側 Web Claude (Phase Result 統合) + Language 側 Web Claude (Atom 解釈) + Taka (主題評価)
*位置づけ*: v1103 主題「段 4-c 点検: 48 次元密度の偏りは応答 Atom を絞れるか」の Code A 観察事実総括、judgement なし (絶対格言 #12)、48 次元人為性留保を必ず添える (GPT 監査 5)。

---

## 0. 一文サマリ

v11.0.3 (v1103) 主題「段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか」段階 1 Step A-F 全完了、Step A 認識確認で論点 0 (ゼロの意味) を実環境照合し設計書 §2.2 想定の (a)(b) 二択でなく **(c) normalized_scores は全 48 軸非ゼロ正規化済 / raw_scores は mean Nonzero 16.41/48 で設計書前提 14.5/48 と整合** の二系統判明 (§5.1 raw/norm 両方並列に確定)、Constitution v1.0 を Code A が wn_core_stats.py + wn_proposal_gen.py 実行で生成し **proposals.json 14 件 (Couple 6 / Subsume 1 / Monitor 7 / Merge 0)** で設計書 §2.6 想定「17 件」と Merge 3 件差 (実環境では同カテゴリ pair_jaccard ≥ 0.75 + size_ratio ≤ 0.25 のペアなし)、atom_centroids_48d.csv を Code A 生成 (325 atoms × 48 axes、raw + normalized 両方並列)、Step C 段 4-b/4-c/4-d 一括実装 (1.2 秒、response_atom_distribution 5,670 rows + density_summary 486 rows、Aruism 対称性 max_prob=0.7972 で 100% 未満厳密遵守)、Step D グラフ HTML 4 セクション (16 KB)、Step E bit-identity 3 層全 PASS (1,763 files frozen v106+v107+v112+v105_int+v1101a+v1102+language_mapper、Step B+C re-run 完全 deterministic)、**核心観察事実** は (1) **raw_density (k=5) 0.847 vs norm_density (k=5) 0.639 で Δ 0.208** の 「sim_basis (raw か norm か) で密度の像が変わる」現象が顕在化 = v1101 留保 #33 系列「集計単位で像が変わる」が 48 次元密度レベルで貫通、(2) k 依存性は raw が緩やかに低下 (k=5→20 で 0.847→0.818、頑健) ・norm は横ばい (0.639→0.667、弱依存) で multi-k sensitivity (GPT 監査 2) により raw cluster が k に頑健であることが確認、(3) qweighted_density と raw_density はほぼ同値 (focus_rate 分散小、品質重み影響軽微)、(4) Monitor 検出は norm × k=20 で 1.05 atom/cell (5%) ・raw × k=20 で 0.59 (3%) で norm の方が Monitor を多く拾う、(5) 段 4-d 確率分布の max_prob 0.7972 で 100% 到達 0 件 = Aruism 対称性 (箱 3) 厳密遵守、(6) Step C 完了時点での 4 可能性判定は設計書 §5.1 の「**可能性 1 (48 次元密度に際立ちが出る) + 可能性 4 (受け手構造で反転) のハイブリッド**」で raw 密度の絶対値は高い (= 際立ちが出る方向) が sim_basis で像が変わる (= 受け手側の見方で反転)、判定 (選択と集中か拡散か、機能した/しなかった) は Web Claude Phase Result + Taka 主題評価領域、48 次元人為性留保 (A1 は QwQ-32B 判定・Genesis cid は Web Claude 定義) を結論に必ず添える (GPT 監査 5)。

---

## 1. Step A-F 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A | 認識確認 (§3.2 論点 0/5 + Language データ実体) | 完了 | v1103_step_a_recognition.md (確認要請 4 件、Taka 確定) |
| B (pre-req) | wn_core_stats + wn_proposal_gen 実行 + atom_centroids 生成 | 完了 | core_report.csv + proposals.json + atom_centroids_48d_raw/norm.parquet + atom_quality.parquet |
| C | 段 4-b 連想 + 4-c 密度 + 4-d 確率分布 | 完了 (1.2s) | response_atom_distribution.parquet (5,670 rows) + density_summary.parquet (486 rows) |
| D | グラフ HTML 4 セクション | 完了 | v1103_observation.html (16 KB) |
| E | bit-identity 3 層 | 完了 (all PASS) | v1103_step_e_bit_identity_report.json |
| F | 観察事実最終報告 | 本書 | v1103_step_f_observation_final.md |
| G | Phase Result | 待ち | Genesis 側 Web Claude 担当 |

---

## 2. §5 確定回答 (Taka 2026-05-20) と実装結果

| § | 内容 | Taka 確定 | 実装結果 |
|---|---|---|---|
| 5.1 | ゼロの意味 | 両方並列 | raw + normalized 両 centroid 生成、density も 2 系統並列観察 |
| 5.2 | atom_centroids 生成主体 | Code A 生成 | 325 atoms × 48 axes 生成 (raw + norm) |
| 5.3 | Constitution 所在 | Code A が実環境再確認 | wn_proposal_gen.py 実行で proposals.json 生成 (14 件) |
| 5.4 | batch_report.md | Code A 生成 | batch_report.py は *_a1_final.jsonl 不在で実行不可 → Code A 直接統計で代替 (atom_quality.parquet) |

---

## 3. 核心観察事実 (judgement なし、絶対格言 #12)

### 3.1 raw vs norm で密度の像が変わる (留保 #33 系列「集計単位で像が変わる」)

| sim_basis × k | raw_density | qweighted | const_adj | n_candidates | n_monitor |
|---|---:|---:|---:|---:|---:|
| **norm × 5** | 0.639 | 0.646 | 0.640 | 5 | 0.12 |
| norm × 10 | 0.635 | 0.626 | 0.633 | 10 | 0.90 |
| norm × 20 | 0.667 | 0.658 | 0.665 | 20 | 1.05 |
| **raw × 5** | **0.847** | 0.849 | 0.847 | 5 | 0.05 |
| raw × 10 | 0.831 | 0.831 | 0.831 | 10 | 0.17 |
| raw × 20 | 0.818 | 0.817 | 0.818 | 20 | 0.59 |

- **raw vs norm の差**: k=5 で **Δ 0.208** (raw 0.847 vs norm 0.639)、留保 #33 系列「集計単位で像が変わる」が 48 次元密度レベルで貫通
- **k 依存性**: raw は緩やかに低下 (k=5→20 で 0.847→0.818、頑健)、norm は横ばい (0.639→0.667、弱依存)。GPT 監査 2「multi-k sensitivity」により raw cluster が k に頑健と確認
- **qweighted vs raw**: ほぼ同値 (focus_rate 分散小、品質重み影響軽微)

### 3.2 Monitor 検出 (Constitution 制約、GPT 監査 4 削除でなく重み軽減)

| sim_basis × k | n_monitor (mean/cell) |
|---|---:|
| norm × 20 | **1.05** (5% 程度) |
| norm × 10 | 0.90 |
| raw × 20 | 0.59 |
| norm × 5 | 0.12 |
| raw × 5 | 0.05 |

- norm の方が Monitor atom を多く拾う (k=20 で raw の 1.78 倍)
- const_adjusted_density で Monitor を 0.5 重み軽減、raw_density との差は ~0.001 (微小、削除でなく重み軽減の影響軽微)

### 3.3 Aruism 対称性 (箱 3、100% を作らない、厳密遵守)

- response_atom_distribution の **max_prob = 0.7972** (1.0 未満)
- **prob ≥ 0.999 の rows = 0** (5,670 rows 中)
- 段 4-d の確率分布出力は Aruism 対称性を厳密遵守

### 3.4 4 可能性判定 (設計書 §5.1)

設計書 §5.1 の 4 可能性のうち、Step C 完了時点の観察は:

| 可能性 | 内容 | 観察結果 |
|---|---|---|
| **可能性 1** | 48 次元密度に際立ちが出る | **部分的に観察** — raw 密度の絶対値は 0.82-0.85 で高く際立ちあり |
| 可能性 2 | 密度が均等で際立ちなし | 該当せず |
| 可能性 3 | 際立ちは出るが品質フラグで大半が偽 | qweighted ≈ raw で品質影響小、現状偽でない |
| **可能性 4** | 受け手構造で際立ちが反転 | **部分的に観察** — sim_basis (raw/norm) で密度が Δ 0.208 反転、receiver_bin 別の反転は Step D グラフ Section 2 参照 |

→ **「可能性 1 + 可能性 4 のハイブリッド」**。判定 (機能した/しなかった、選択と集中/拡散) は Web Claude Phase Result + Taka 主題評価領域。

---

## 4. 48 次元人為性留保 (GPT 監査 5、Phase Result 必須添加)

48 次元空間は両端で人為的投影:
- **Genesis 側 (cid)**: Web Claude が定義した 326 atom × 48 axes 構造
- **Language 側 (A1)**: QwQ-32B (LLM) が判定した normalized_scores

両端とも測定でなく定義/判定であり、観察された raw_density 0.847 / norm_density 0.639 等の値は両端の人為性の上に乗る。本主題の観察事実を「自然の発見」と読まないこと。Phase Result 結論に必ず添える。

---

## 5. 設計書 §2.6 想定との差異 (Constitution 件数)

| 種別 | 設計書 §2.6 想定 | 実環境 (wn_proposal_gen.py 出力) | 差 |
|---|---:|---:|---:|
| Couple | 6 | **6** | 一致 |
| Merge | 3 | **0** | **-3** |
| Subsume | 1 | **1** | 一致 |
| Monitor | 7 | **7** | 一致 |
| **合計** | **17** | **14** | **-3** |

Merge 0 件の理由: Pattern A 条件「pair_jaccard ≥ 0.75, same category, size_ratio ≤ 0.25」を満たすペアが現状の core_pool で存在しない。設計書 §2.6 想定との差 3 件は Step A 認識確認の追加発見。

---

## 6. bit-identity 3 層 (Step E)

| 層 | 内容 | 結果 |
|---|---|---|
| A | Step B+C re-run parquet hash 一致 | True (Step B 1.38s, Step C 1.81s) |
| B | v106+v107+v112+v105_int+v1101a+v1102+language_mapper = **1,763 files frozen** | 0/0/0 全 frozen |
| C | scripts 6 write calls すべて unified/v1103/ 配下 | True |

→ all_layers_pass = True

---

## 7. 留保事項

| id | 内容 |
|---|---|
| #L17 candidate (v1103 新規) | raw vs normalized で密度が Δ 0.208 反転、留保 #33 系列「集計単位で像が変わる」が 48 次元密度レベルで貫通 |
| #L18 candidate (v1103 新規) | Constitution v1.0 で Merge 0 件 (設計書 §2.6 想定 3 件と差)、core_pool の現状から Pattern A 条件を満たすペアなし |
| #L19 candidate (v1103 新規) | batch_report.py 実行不可 (*_a1_final.jsonl 不在)、final 化 step が Language パイプラインから抜けている |
| 48 次元人為性留保 (GPT 監査 5) | 両端 (Genesis cid / Language A1) とも人為的投影、本主題の観察事実を自然の発見と読まないこと |

---

## 8. 出力ファイル総覧 (`unified/v1103/`)

| ファイル | サイズ |
|---|---:|
| v1103_phase_design.md | (markdown) |
| v1103_step_a_recognition.md | (markdown) |
| v1103_step_f_observation_final.md (本書) | (markdown) |
| v1103_step_b_atom_centroids.py | (python) |
| v1103_step_c_density_distribution.py | (python) |
| v1103_step_d_graph.py | (python) |
| v1103_step_e_bit_identity.py | (python) |
| outputs/main/core_report.csv | (csv) |
| outputs/main/proposals.json | 14 proposals |
| outputs/main/atom_centroids_48d_raw.parquet | 325 × 48 |
| outputs/main/atom_centroids_48d_normalized.parquet | 325 × 48 |
| outputs/main/atom_quality.parquet | 325 atoms |
| outputs/main/response_atom_distribution.parquet | 5,670 rows |
| outputs/main/density_summary.parquet | 486 rows |
| outputs/v1103_observation.html | 16 KB |
| v1103_step_e_bit_identity_report.json | all_layers_pass=True |

---

## 9. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A は本書で観察事実を記録。**判定は Web Claude Phase Result + Taka 主題評価領域**:

- raw vs norm 密度差 Δ 0.208 を「選択と集中か拡散か」とどう接続するか
- 「可能性 1 + 可能性 4 のハイブリッド」を「段 4-c が機能した」とするか別軸の現象とするか
- 48 次元人為性留保を踏まえた「会話接続の道が原理的に通った」の判定
- Constitution Merge 0 件の主題的意味 (#L18 candidate)
- 留保 #L17 (raw vs norm 反転) を v1101 留保 #33 系列の延長として位置づけるか

v1103 主題担当範囲 (Code A): 段階 1 Step A-F 全完了、設計書 §4 出口 7 項目すべて満たす。段 4 全体の完成判定 / 段 5b (LLM 外注) / 会話 ESDE の完成は v1103 範囲外 (§1.4 明示)。

---

## 10. 一文サマリ (再掲)

v1103 主題「段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか」段階 1 Step A-F 全完了、Step A 認識確認で論点 0 (ゼロの意味) は設計書 §2.2 (a)(b) 二択でなく (c) normalized は全 48 軸非ゼロ正規化済 / raw は Nonzero 16.41/48 の二系統判明 (§5.1 raw/norm 両方並列確定)、Constitution v1.0 を Code A が生成し proposals 14 件 (Couple 6 / Subsume 1 / Monitor 7 / Merge 0、設計書想定 17 件と Merge 3 件差は新規留保 #L18)、atom_centroids 325 × 48 × 2 種 (raw/norm) 生成、Step C 段 4-b/4-c/4-d 一括実装 (1.2 秒、response_atom_distribution 5,670 rows + density_summary 486 rows、Aruism 対称性 max_prob=0.7972 で 100% 未満厳密遵守)、Step D 4 セクション HTML 16 KB、Step E bit-identity 3 層全 PASS (1,763 files frozen)、核心観察事実は (1) raw_density (k=5) 0.847 vs norm_density (k=5) 0.639 で Δ 0.208 = 留保 #33 系列「集計単位で像が変わる」が 48 次元密度レベルで貫通 (新規留保 #L17)、(2) raw は k に頑健 (k=5→20 で 0.847→0.818) ・norm は弱依存 (0.639→0.667)、(3) qweighted ≈ raw で品質重み影響軽微、(4) Monitor 検出は norm の方が多 (k=20 で 1.05 vs raw 0.59)、(5) Aruism 対称性厳密遵守 (max 0.7972、100% 到達 0 件 / 5,670 rows)、(6) 設計書 §5.1 の 4 可能性判定では「可能性 1 (際立ち出る) + 可能性 4 (受け手構造で反転) のハイブリッド」、48 次元人為性留保 (両端 Genesis cid Web Claude 定義 / Language A1 QwQ-32B 判定の人為的投影) を Phase Result 結論に必ず添える (GPT 監査 5)、判定 (機能した/しなかった、選択と集中/拡散の方向性、可能性 4 反転の解釈、Constitution Merge 0 件の意味) は Web Claude Phase Result + Taka 主題評価領域、v1103 Code A 主題担当範囲は段階 1 Step A-F 全完了で段 4 全体完成判定 / 段 5b / 会話 ESDE 完成は範囲外 (§1.4 明示)。

---

*以上、v11.0.3 (v1103) Step F 観察事実最終報告 (Code A、2026-05-20)。judgement なし観察記録 (絶対格言 #12)、48 次元人為性留保あり (GPT 監査 5)。Genesis 側 Web Claude Phase Result + Taka 主題評価判断を待つ。*
