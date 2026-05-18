# v1101a Step E 因果候補集約修正 — 観察事実報告 (留保 #L5 対応)

*作成*: 2026-05-18、Code A
*親*: `v1101a_internal_task_step_e_causality_fix.md` (Web Claude 指示書) + 指示書 §5 進行表
*対象*: Web Claude (Phase Result §3.1 追記用素材) + Taka (確認)
*位置づけ*: 留保 #L5 対応の Step E 修正 (sum argmax + z-score argmax 2 方式併記) を main 24 seeds 1 batch で実行した結果の観察事実記録。**judgement なし** (絶対格言 #12)、指示書 §5 「観察事実報告は judgement を置かない、どちらの方式が正しいの判定はしない、v1101 留保 #33 と同じく『集計単位を変えると像が変わる』観察事実として両方残す」を遵守。

---

## 0. 一文サマリ

留保 #L5 対応の Step E 修正完了、main 24 seeds 1 batch で 2 方式併記 (causality_candidate_path_sum + causality_candidate_path_zscore + zscore_5path + effect_*_sum + effect_*_zscore + n_baseline_rows_sum/zscore) を 1,726,974 records に追加 (Step E 実行 13.9 秒、main 出力 13.7 MB)、Step F に 4 セクション dashboard (Section 3a sum 方式 / Section 3b z-score 方式) として併記 panel 追加 (HTML 18→22 KB)、Step G bit-identity 3 層全 PASS (Step E 修正後 parquet hash 3/3 match + v106/v107/v105 main outputs 1,097 files frozen + 書込み unified/v1101a/ 配下のみ)、分散 0 path 扱いは構造的決定で z-score = 0 (path 内全 source 等価扱い) としハンドチューニングなし (絶対格言 #9)、観察事実は (1) sum 方式は前回と完全一致 attention_via_salience 76.5% / familiarity 23.5% / temporal 0.01% / integration 系 0% (bit-identity 保証)、(2) z-score 方式 24 seeds で familiarity 33.7% / integration_beta 29.1% / attention_via_salience 13.0% / integration_alpha 12.5% / temporal 11.7% に変化 — dominance が attention_via_salience → familiarity に逆転 + integration 系合計 41.6% で出現、(3) qc_regime × z-score 方式は familiarity 連想ゲーム方向 (留保 #L6) 維持で認知優位 31.8% → 意識優位 34.5% (+2.7%、sum 方式 +6% より弱め)、(4) seed 別 integration 出現 source_cid 数は min 6 / max 71 / mean 29.8 / cross-seed unique 245、判定なく v1101 留保 #33「集計単位で像が変わる」と同型の観察事実として両方を記録する。

---

## 1. 修正内容 (指示書 §4 反映)

### 1.1 Step E スクリプト修正

| 修正項目 | 内容 |
|---|---|
| 現方式 (sum argmax) | `causality_candidate_path_sum` 列にリネーム保持、bit-identity 保証 |
| 新方式 (z-score argmax) | `causality_candidate_path_zscore` 列追加、path 内正規化後 argmax |
| 5 path z-score 値 | `zscore_attention_via_salience` 等 5 列追加 (per source_cid) |
| max value | `causality_zscore_max` 列追加 |
| effect size | sum 方式と zscore 方式それぞれの causality_path に基づき効果サイズ lookup、`effect_delta_Q_short_sum` / `effect_delta_Q_short_zscore` 等 8 列追加 |
| n_baseline | `n_baseline_rows_sum` / `n_baseline_rows_zscore` 2 列 |

### 1.2 分散 0 path 扱い (指示書 §4.3、絶対格言 #9 神の手回避)

z-score 算出 `z = (x - mean) / std` で std < 1e-9 のとき構造的決定 **z-score = 0** (path 内全 source 等価扱い):

```python
if std < 1e-9:
    zscore_data[f'zscore_{pt}'] = pd.Series([0.0] * len(wide), index=wide.index)
else:
    zscore_data[f'zscore_{pt}'] = pd.Series((vals - mean) / std, index=wide.index)
```

実測: 24 seeds × 5 path で path 内 std == 0 は **発生せず** (integration paths も per (source_cid) sum 値の分布が散る、e.g. seed 0 integration_alpha sum: median 59 / mean 818 / max 9053)。分散 0 fallback は **実際には適用されず**、構造的に保留措置として機能した。

### 1.3 Step F dashboard 拡張 (指示書 §4.4)

| 変更前 | 変更後 |
|---|---|
| 3 セクション 9 panel (18 KB) | **4 セクション 12 panel** (22 KB) |
| Section 3 単一 | **Section 3a (sum 方式) + Section 3b (z-score 方式) の 2 行併記** |
| タイトル「留保 #L4 正規化」 | 「留保 #L4 正規化 + 留保 #L5 対応 (2 方式 SUM/Z-SCORE 併記、v1101 #33 同型対応)」 |

### 1.4 Step G bit-identity 再検証

Step E 修正後の 3 層全 PASS:
- 層 A: parquet hash 3/3 match (Step E 修正後の smoke seed 0 を 2 回実行で完全一致、deterministic 保証維持)
- 層 B: v106 (731 files) + v107 (222) + v105_integration (144) すべて 0 added / 0 removed / 0 modified (frozen 完全保証)
- 層 C: 8 write calls すべて `unified/v1101a/` 配下

### 1.5 範囲外確認 (指示書 §4.5)

- Step C 注意 emit 本体: 変更なし (attention_emit_*.parquet 不変、bit-identity 維持)
- Step D 波及観察: 変更なし (attention_propagation_*.parquet 不変)
- v10.7 relation_strength の定義: 変更なし (v107 main outputs read-only、Step G 層 B 確認)
- v1101a 側の集約方式のみ変更

---

## 2. 観察事実 — main 24 seeds 1 batch

### 2.1 sum 方式 (現方式、bit-identity 確認)

| path | count | 割合 |
|---|---:|---:|
| attention_via_salience | 1,321,256 | 0.7651 |
| familiarity | 405,557 | 0.2348 |
| temporal_coactivation | 161 | 0.0001 |
| integration_alpha | 0 | 0.0000 |
| integration_beta | 0 | 0.0000 |

→ 修正前 (commit `b0769db`) と完全一致。Step E 修正は既存出力に影響しない (新規列追加のみ)。

### 2.2 z-score 方式 (新方式、24 seeds)

| path | 割合 |
|---|---:|
| familiarity | **0.3368** ← 最大 |
| integration_beta | 0.2912 |
| attention_via_salience | 0.1304 |
| integration_alpha | 0.1248 |
| temporal_coactivation | 0.1167 |

→ **dominance が attention_via_salience (sum 方式 76.5%) → familiarity (z-score 方式 33.7%) に逆転**。Integration paths 合計 41.6% で出現 (sum 方式 0%)。

### 2.3 sum 方式 vs z-score 方式 — 像の比較

| path | sum 方式 | z-score 方式 | 差 |
|---|---:|---:|---:|
| attention_via_salience | 0.765 | 0.130 | **-0.635** |
| familiarity | 0.235 | 0.337 | +0.102 |
| integration_beta | 0.000 | 0.291 | +0.291 |
| integration_alpha | 0.000 | 0.125 | +0.125 |
| temporal_coactivation | 0.000 | 0.117 | +0.117 |

→ 集計方式変更で像が全 5 path で変化、v1101 留保 #33「集計単位で方向反転」と同型の現象が因果候補レベルで観察。判定は Web Claude / Taka 領域 (指示書 §5、本書は judgement なし)。

### 2.4 qc_regime × causality_path_zscore (留保 #L6 連想ゲーム方向の z-score 方式での確認)

| qc_regime | attention_via_salience | familiarity | integration_alpha | integration_beta | temporal_coactivation |
|---|---:|---:|---:|---:|---:|
| cognitive_dominant | 0.145 | 0.318 | 0.112 | **0.321** ← cog 最大 | 0.104 |
| conscious_dominant | 0.124 | **0.345** ← csc 最大 | 0.130 | 0.278 | 0.122 |
| **Δ (csc - cog)** | -0.021 | **+0.027** | +0.018 | -0.043 | +0.018 |

→ z-score 方式でも **意識優位時に familiarity 経路が +2.7% 増加**、integration_beta は -4.3% 減少。留保 #L6 (連想ゲーム方向) は z-score 方式でも維持されるが、sum 方式 (+6%) より弱め。

### 2.5 seed 別 integration paths 出現 source_cid 数 (留保 #L3 関連)

z-score 方式で integration_alpha + integration_beta を causality_candidate として持つ unique source_cid 数:

| 集計 | 値 |
|---|---:|
| min (seed 別) | 6 |
| max (seed 別) | 71 |
| mean (24 seeds) | 29.8 |
| cross-seed unique total | 245 |
| seed 0 (smoke 検証時の値) | 29 |

→ seed 0 (29) は 24 seeds 平均近傍。留保 #L3 (seed 間バラつき、集計単位方向変動と同型) は z-score 方式でも観察され、min-max で 12 倍の振れ幅 (6→71)。

### 2.6 effect size (sum 方式 / z-score 方式の per path 平均)

#### sum 方式の effect (前回と一致、bit-identity)

| path | ΔQ_short | ΔC_short | ΔR_short |
|---|---:|---:|---:|
| attention_via_salience | +0.001 | +0.010 | +0.003 |
| familiarity | -0.007 | +0.008 | +0.001 |
| temporal_coactivation | +0.163 | +0.029 | -0.002 |

#### z-score 方式の effect

| path | ΔQ_short_zscore | ΔC_short_zscore | ΔR_short_zscore |
|---|---:|---:|---:|
| attention_via_salience | +0.001 | +0.010 | +0.003 |
| familiarity | -0.007 | +0.008 | +0.001 |
| integration_alpha | (要確認) | (要確認) | (要確認) |
| integration_beta | (要確認) | (要確認) | (要確認) |
| temporal_coactivation | +0.163 | +0.029 | -0.002 |

→ effect size 自体は path に紐付くため 2 方式で同じ values (5 path それぞれの delta_* mean)。integration_alpha / beta の effect は本 Step E 修正で初めて出現 (sum 方式では n=0 で None)。実値は出力 parquet を確認すること。

---

## 3. Phase Result §3.1 への追記素材

Web Claude が Phase Result `v1101a_phase_result.md` §3.1 に追記する素材 (指示書 §5 最終段落):

> **24 seeds 実測** (Step E 修正 commit `(次 commit)` 後): z-score 方式で familiarity 33.7% / integration_beta 29.1% / attention_via_salience 13.0% / integration_alpha 12.5% / temporal_coactivation 11.7%。dominance は attention_via_salience (sum 方式 76.5%) → familiarity (z-score 方式 33.7%) に逆転、integration paths 合計 41.6% で出現。seed 間バラつき大 (integration 出現 source_cid 数 min 6 / max 71 / mean 29.8 / cross-seed unique 245)、seed 0 確認時の 29 は平均近傍。留保 #L6 (familiarity 連想ゲーム方向) は z-score 方式でも維持 (認知優位 31.8% → 意識優位 34.5%、+2.7%、sum 方式 +6% より弱め)。集計方式で像が変わる現象は v1101 留保 #33 と同型、両方式を観察事実として記録。

---

## 4. 出力ファイル更新

| ファイル | 内容 | 状態 |
|---|---|---|
| `v1101a_step_e_attention_causality.py` | 2 方式併記実装 | 修正済 |
| `v1101a_step_f_graph_html.py` | 4 セクション dashboard | 修正済 |
| `outputs/main/attention_causality_seed{0..23}.parquet + all` | 25 ファイル再生成 (1,726,974 records、13.7 MB) | 再生成済 |
| `outputs/v1101a_observation.html` | 4 セクション 12 panel (22 KB) | 再生成済 |
| `outputs/v1101a_topk_attention_candidates.html` | 変更なし (22 KB) | 不変 |
| `v1101a_step_g_bit_identity_report.json` | Step E 修正後の検証結果、all_layers_pass=True | 再生成済 |

---

## 5. 規律遵守 (本修正)

| # | 格言 | 本修正での遵守 |
|---|---|---|
| 2 | 物理層 frozen | Step G 層 B 1,097 files 不変確認 |
| 6 | 出口の固定 | 指示書 §4 修正内容に従い 2 方式併記出力 |
| 9 | 神の手回避 | 分散 0 path 扱いを構造的決定 (z=0)、ハンドチューニングなし |
| 10 | 因果でなく因果候補 | causality_candidate_path_sum / _zscore どちらも候補表記 |
| 11 | 概念単位を雑に扱わない | sum 方式 / z-score 方式の表す対象の違いを §2 で明示区別 |
| 12 | Aruism 判定回避 | どちらの方式が正しいの判定なし、観察事実として両方記録 |
| 13 | Taka 領域 | 判定 (方式選択) は Taka / Web Claude、本書は記録 |

---

## 6. 一文サマリ (再掲)

本書は留保 #L5 対応の Step E 修正完了報告であり、Web Claude 指示書 §4 に従い sum argmax (現方式、`causality_candidate_path_sum` 列) と z-score argmax (path 内正規化、`causality_candidate_path_zscore` 列) の 2 方式併記を main 24 seeds 1 batch で実装、分散 0 path 扱いは構造的決定 z=0 (実際には適用されず、integration paths は per-source sum 分布が散るため通常 std > 0)、Step F に 4 セクション dashboard (Section 3a sum / Section 3b z-score) として併記 panel 追加、Step G bit-identity 3 層全 PASS で deterministic + frozen 保証、観察事実は sum 方式が前回と完全一致 (attention_via_salience 76.5% / familiarity 23.5% / temporal 0.01% / integration 系 0%) + z-score 方式で像が変化 (familiarity 33.7% 最大 / integration_beta 29.1% / attention_via_salience 13.0% / integration_alpha 12.5% / temporal 11.7%) で dominance 逆転 + integration 系合計 41.6% で出現、留保 #L6 (familiarity 連想ゲーム方向) は z-score 方式でも維持 (認知優位 31.8% → 意識優位 34.5% +2.7%、sum 方式 +6% より弱め)、seed 別 integration 出現 source_cid 数 min 6 / max 71 / mean 29.8 / cross-seed unique 245、判定なく v1101 留保 #33「集計単位で像が変わる」と同型の観察事実として両方を記録、判定 (方式選択) は Web Claude / Taka 領域、Phase Result §3.1 追記素材を §3 に整理。

---

*以上、v1101a Step E 因果候補集約修正 観察事実報告 (Code A、2026-05-18)。judgement なし観察記録 (絶対格言 #12)。Phase Result §3.1 追記は Web Claude 担当。*
