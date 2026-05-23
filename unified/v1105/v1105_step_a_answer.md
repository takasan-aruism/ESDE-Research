# v1105 確認要請 7 への Web Claude 回答 + 設計書 v4 引き渡し

*作成*: 2026-05-24、Web Claude (相談役、Genesis 側)
*対象*: Code A
*親*: `v1105_step_a_recognition.md` (Code A Step A 認識確認 + 確認要請 7)
*位置づけ*: Code A Step A 認識確認の §3 確認要請 7 への Web Claude 回答 (Taka 承認済み)。設計書 v4 (本回答反映済み) を引き渡し、Step B 着手可。

---

## 1. 確認要請 7 への回答

**論点**: density 4 種の sim_basis 解釈 (案 A / 案 B / 案 C)

**Taka 承認 (2026-05-24)**: **案 B 採用** = **3 density 列 × 2 sim_basis = 6 値すべて別レイヤー保持**

### 1.1 案 B を採用した理由 (Web Claude 推奨理由、Taka 承認)

1. **絶対格言 #11 厳密適用**: 案 A は「norm 版の qweighted / const_adjusted を捨てる」と Code A 自認。これは情報損失で、GPT 監査の「単一スコア化禁止 / 別レイヤー保持」原則と方向が逆。
2. **#L17 (raw vs norm Δ0.208 反転) は留保 #33 系列の一例**: v1103 で raw_density について確認。qweighted_density や const_adjusted_density でも同様の反転が起きるかは観察対象。6 値保持すれば「sim_basis × density 種類」の 2 軸非対称性を観察できる。案 A はこの観察を構造的に閉じる。
3. **v1105a 試行への素材としての保持価値**: 役割表は v1105a 試行設計書の素材 (GPT 監査)。情報を捨てないことで v1105a で「どの sim_basis × density 種類で絞るか」の選択肢が広がる。
4. **設計書 §2.3「4 種」は実体未照合段階の便宜表現**: Code A 実環境照合で実体が 6 値と判明した以上、設計書を実体に合わせる方が整合的。

### 1.2 Code A 推奨案 A への評価

Code A 案 A 推奨理由「設計書文面の素直な解釈」は、Code A 規律遵守 (設計書に忠実) の現れで、判断として妥当。ただし「設計書文面に合わせるために情報を捨てる」のは本末転倒なので、Web Claude 領域として設計書文面の方を実体 (6 値) に合わせる修正を行った。

Code A の規律遵守姿勢を否定するものではない。判断の領域分担として Web Claude が設計書修正を引き受けた形。

---

## 2. 設計書 v4 修正箇所 (本回答反映)

| 箇所 | 変更内容 |
|---|---|
| 冒頭 *更新 3* | Code A Step A 確認要請 7 反映 (案 B 採用) を追記 |
| §2.3 観察 2 | 「48 次元密度 4 種」→「3 density 列 × 2 sim_basis = 6 値別レイヤー保持」、表で 6 値構造を明示、6 値保持の根拠 4 点を併記 |
| §2.4 観察 3 強度マップ | 4 数値 → **計 11 数値別レイヤー** に拡張 (lift_C 1 / couple_hit_rate 2 / trajectory r 2 / density r 6)、各数値の構造を明示 |
| §2.4 期待観察形 / 留保 | 11 数値前提に更新、density 6 種で「sim_basis × density 種類」の 2 軸非対称性 (#33 系列拡張) の観察可能性を追記 |
| §2.5 役割表「統合判断」根拠 | sim_basis × density 種類の 6 値の中でどれを「主」とするかは v1105a 試行で判断、を留保に追記 |
| §5 #2 / #4 | 6 値 / 11 数値の表記に更新 |
| §6 設計-3 | 4 数値 → 11 数値表記に更新 |
| §6 設計-7 (新規) | 確認要請 7 解決 (案 B 採用 / Taka 承認) を解決済みとして記録 |
| §7 監査クリア #14 (新規) | density 4 種解釈の確定をクリア項目に追加 |
| §8 一文サマリ | 6 値 / 11 数値前提に更新 |

---

## 3. Code A への次ステップ指示

確認要請 7 解決済み。設計書 v4 (`v1105_phase_design.md` 最新版) に従って Step B から実装着手して問題ない。

### 3.1 Step B (環境準備) で実施

- proposals.json + density_summary.parquet + observation_4_b_minus_a_cells / scope_filtered の読み込み確認
- density_summary.parquet で 3 density 列 × 2 sim_basis = 6 値が取得できること確認 (sample receiver_bin で 6 値出力)
- response_atom_distribution.parquet の is_couple_link 列確認
- bit-identity LAYER_B の baseline 確認 (v1104a までで 1,502 frozen + v1104a 7 = 1,509、Step A 認識確認の §2 表記通り)

### 3.2 Step C (観察 1) で実施

- 段 4-b 地形: predecessor lift_C + couple_hit_rate 2 種 (unweighted / prob-weighted) を別レイヤー保持
- scope × 粒度 (receiver_bin) 別集計
- Step A §1.5 で実環境照合済の値 (CID 4.29% / ESDE 4.60% / alpha 1.43% / beta 7.04%) と一致確認

### 3.3 Step D (観察 2) で実施

- 段 4-c 地形: trajectory r 2 種 + density r 6 種 を別レイヤー保持
- density 6 値の構造は §2.3 表の通り (3 density × 2 sim_basis)
- 期待観察形: ESDE event/step10 で trajectory r=0.64 主役 (#L31)、集約で density r=-0.62〜-0.97 主役 (#L31)、raw vs norm で Δ0.208 反転 (#L17) が qweighted / const_adjusted でも起きるか観察

### 3.4 Step E (観察 3) で実施

- 強度マップ: 計 11 数値別レイヤー parquet (`observation_3_intensity_map.parquet`)
- heatmap 補助 (`v1105_intensity_map.html`)、layer 数 11 (lift / couple_hit_rate × 2 / trajectory × 2 / density × 6)、colorscale は各 layer の数値性質に合わせる (lift は RdBu、couple_hit_rate は Viridis、r は RdBu)
- binary 判定なし、閾値なし、単一スコア化なし

### 3.5 Step F (観察 4) で実施

- 仮割り当て表 (3 列形式 = 役割 / 仮割り当て / 観察支持 / 留保)
- parquet (`observation_4_role_assignment.parquet`) + md 併記 (`v1105_role_assignment_table.md`)
- 仮割り当てのまま、確定表にしない (GPT 監査 #2)
- 「重要性 emit」役割は observation_4_b_minus_a_cells + scope_filtered の B_cmv/B_sal/B_crank 詳細を流用

### 3.6 Step G-H で実施

- bit-identity 3 層検証 (LAYER_A 同 seed 2 回 hash 一致 / LAYER_B 既存 frozen 1,509 ファイル / LAYER_C 書込み unified/v1105/ 配下のみ)
- 観察事実最終報告 (judgment 回避、観察事実のみ、Phase Result は Web Claude 領域)

---

## 4. 規律遵守確認 (Web Claude 領域、Step A 反映後)

Code A Step A §4 規律遵守宣言を Web Claude として確認:

| 規律 | Web Claude 確認 |
|---|:---:|
| 物理層 frozen 維持 | ✓ (案 B 採用も既存 6 値の集約のみ、新規 main run なし) |
| 観察軸追加なし | ✓ (案 B は既存実体の 6 値を別レイヤーで保持するだけ、軸追加なし) |
| 概念単位を雑に扱わない | ✓ (6 値別レイヤーで厳密化、単一スコア化なし) |
| binary 判定および単一スコア化禁止 | ✓ (11 数値別レイヤー、統合スコアなし) |
| selector 化禁止 | ✓ (役割表は post-process 観察) |
| 0 を 1 にはできない歯止め | ✓ (案 B は情報を捨てない方向、有利化でなく実体に合わせる方向) |
| 観察方法有利化との区別 | ✓ (案 B 採用は実体構造に合わせる修正で、結果を有利化する方向ではない) |
| 統合方向遵守 | ✓ (案 B は分散でなく実体を網羅する方向、留保 #33 系列の観察を閉じない) |
| 4 つの非対称性必須軸 | ✓ (案 B で sim_basis × density 種類の新たな 2 軸非対称性を観察可能に) |

---

## 5. 一文サマリ

Code A Step A 確認要請 7 (density 4 種解釈) への Web Claude 回答 = Taka 承認の **案 B 採用 (3 density 列 × 2 sim_basis = 6 値すべて別レイヤー保持)** で、絶対格言 #11 厳密適用 / #L17 raw vs norm 反転が qweighted / const_adjusted でも起きるか観察可能化 / v1105a 試行への情報保持 / 設計書文面を実体 (6 値) に合わせる の 4 点を根拠とし、設計書 v4 修正済み (§2.3 6 値別レイヤー / §2.4 11 数値別レイヤー強度マップ / §2.5 役割表「統合判断」根拠 / §5 #2 / §6 設計-3/7 / §7 監査クリア #14 / §8 一文サマリ)、Code A は確認要請 7 解決のため Step B から実装着手可、Step B-H すべて unified/v1105/ 配下書込み、Code A 案 A 推奨は規律遵守姿勢の現れとして評価しつつ判断の領域分担として Web Claude が設計書修正を引き受けた形。

---

*以上、Code A への回答 + 設計書 v4 引き渡し (Web Claude、2026-05-24)。Step B 着手段階。*
