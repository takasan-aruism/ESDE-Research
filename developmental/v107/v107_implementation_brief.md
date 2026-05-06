# v10.7 実装指示書 — ESDE 内の発火と周辺波及の機構観察

*作成*: 2026-05-06、Web Claude (相談役)
*対象*: Code A (Implementer)
*親*: `v107_phase_design.md` (主題ドキュメント)
*位置づけ*: v10.7 主題の Code A 向け実装指示書。Taka 指示 (2026-05-06) により、**Code A が実装着手前に認識確認文書を返すステップを必須化**。

---

## 0. Code A への最初の依頼 (認識確認ステップ、Taka 指示)

**実装着手前に**、本指示書を読んだ上で以下を含む認識確認文書 (`v107_code_recognition_check.md`) を作成し、Web Claude / Taka に提出してください:

### 0.1 認識確認文書に含める項目

1. **本指示書で求められている主題の理解** (3-5 行で要約)
2. **5 種 source_event の定義** が明確かどうかの判定
3. **5 種 candidate_target_set の構築方針** が実装可能かどうかの判定
4. **5 種ベースライン群** の構築が ESDE の既存データから可能かどうかの判定
5. **アバランシェ防止機構** の到達距離 ≤ 3 hop、ストレージ ≤ 200 MB/seed が現実的か
6. **構造語の置換規則** (発火 → source_event 等) で実装上の混乱がないか
7. **環境チェック結果** (使えるデータ、列名、ファイル形式の確認)
8. **設計の甘い部分** (Code A から見た落とし穴、再設計が必要な箇所)
9. **実装にかかる予想時間** (smoke + main run の見積もり)
10. **質問事項** (本指示書で不明確な点、Taka / Web Claude に確認したい点)

### 0.2 確認後の流れ

- Web Claude / Taka が認識確認文書を確認
- 認識が正しければ実装着手の許可
- ずれていれば指示書を修正
- これにより手戻りを減らす

### 0.3 設計の甘さは Code A が突く前提

Taka 整理 (2026-05-06):
> どうせ設計の甘いところは Claude Code に突っ込まれる
> あんまり気にせず

本指示書の設計に甘い部分があっても、Code A が認識確認の段階で指摘してください。修正を経て実装着手します。

---

## 1. 実装の全体像

### 1.1 機構の位置づけ

post-process として実装。ESDE engine / physics / virtual / cognition runtime には一切手を加えない。

入力: ESDE Genesis 系 v10.5 (または v10.6) 出力 CSV / parquet
出力: `developmental/v107/outputs/` 配下の解析結果

### 1.2 ファイル構造

```
developmental/v107/
├── v107_phase_design.md             (主題ドキュメント、参照のみ)
├── v107_implementation_brief.md     (本ドキュメント、参照のみ)
├── v107_code_recognition_check.md   (Code A 作成、認識確認)
├── v107_post_process.py             (主処理、Code A 実装)
├── v107_event_aggregator.py         (source_event の同定)
├── v107_path_analyzer.py            (relation_path 経由の delta 解析)
├── v107_baseline_constructor.py     (5 種ベースライン構築)
├── v107_avalanche_monitor.py        (アバランシェ防止機構)
└── outputs/
    ├── smoke/
    │   └── seed 0 + audit_run_a/b
    └── main/
        ├── source_events/
        ├── path_enriched_deltas/
        ├── baseline_comparisons/
        ├── peak_lag_analysis/
        ├── avalanche_monitoring/
        └── run_summary.csv
```

---

## 2. source_event の同定 (項目 1)

### 2.1 5 種の source_event

| event 種別 | 既存ログ | 主体 cid | timestamp |
|---|---|---|---|
| pulse | pulse_log_seed*.csv | cid | t |
| ingestion | ingestion_log_seed*.csv (または event log) | eater_cid | t |
| alpha_formation | alpha_lifecycle_log_seed*.csv (event_type='birth') | member_cids | step |
| beta_formation | beta_lifecycle_log_seed*.csv | member_cids | step |
| c_conversion | balance/c_trajectory_seed*.csv (delta_C > 0 の瞬間) | cid | step |

### 2.2 source_event テーブルの構築

各 source_event について以下のフィールドを持つテーブルを構築:

```
event_id              (uuid または auto-increment)
seed                  (0-23)
event_source_type     ('pulse' / 'ingestion' / 'alpha_formation' / 'beta_formation' / 'c_conversion')
source_cid            (主体 cid のID)
timestamp             (step)
pre_event_state       (Q、C、familiarity_max、n_alphas、n_observed_as_target 等のスナップショット)
```

### 2.3 注意事項

- **birth_step バグ** (v10.6 step10 解析で発見) を回避: per_subject の `birth_window` は使わず、pulse_log の最初 t を使う
- alpha_lifecycle_log の event_type は **`'birth'`** (v10.6 で確認、`'created'` は存在しない)
- ingestion event のスキーマは Code A の環境チェックで確認

---

## 3. candidate_target_set の構築 (項目 2)

### 3.1 5 種の relation_path_type

各 source_event について、target cid 群を 5 種の relation_path で同定:

#### 3.1.1 familiarity 経路
- source_cid と familiarity edge を持つ cid
- familiarity 強度 (per_subject の familiarity_*) でソート
- 上位 N cid を target に含める (N は §6 のストレージ上限から逆算)

#### 3.1.2 attention 経路
- source_cid の attention map 内の cid
- attention 重みでソート
- 上位 N cid を target に含める

#### 3.1.3 Integration 経路
- source_cid と同 α または同 β に所属する cid
- alpha_lifecycle_log / beta_lifecycle_log から取得

#### 3.1.4 temporal_coactivation 経路
- source_event と時間的に近接 (lag ≤ 中期 100-1000 step) で発火する cid
- pulse_log から time-window 集計

#### 3.1.5 matched_baseline 経路
- 同 n_core / 同 age (age = current_step - birth_step) / 同 hosted 状態の cid
- ただし source_cid と無関係 (上記 4 経路に含まれない)
- これがベースラインの 1 つ (§4)

### 3.2 candidate_target テーブル

```
event_id              (source_event との結合キー)
target_cid            (対象 cid)
relation_path_type    (5 種のうち 1 つ)
relation_strength     (familiarity 強度 / attention 重み / hop 数 / lag 等)
hop_distance          (1-3 hop、§5 のアバランシェ防止と整合)
```

### 3.3 注意事項

- 1 つの target cid が複数の relation_path_type に該当する場合、各 path で別行として記録 (重複許容)
- source_cid 自身は target に含めない (自己参照除外)

---

## 4. 5 種ベースライン群の構築 (項目 3)

### 4.1 ベースライン群の定義

GPT 監査 B4 反映:

| ベースライン名 | 定義 |
|---|---|
| unrelated_baseline | source_cid と無関係な任意 cid (familiarity / attention / Integration の全てで非接続) |
| same_step_random_baseline | 同 step で動いている任意 cid (時間効果の排除) |
| matched_baseline | 同 n_core / 同 age / 同 hosted 状態の無関係 cid |
| same_integration_low_familiarity_baseline | 同 Integration 内だが familiarity が低い (下位 25%) cid |
| high_familiarity_outside_integration_baseline | familiarity が高い (上位 25%) が Integration 外の cid |

### 4.2 ベースライン構築の実装

- 各 source_event について 5 種 baseline cid 群を抽出
- target_cid と同様のフィールドで記録
- baseline 行は `relation_path_type` 列に baseline 名を記録

### 4.3 効果サイズの計算

target cid 群と各 baseline 群の baseline_excess_change を計算:

```
baseline_excess_change = mean(target_delta) - mean(baseline_delta)
```

|baseline_excess_change| > 1% (v10.6 規律継承) を実質的な finding 候補とする。

---

## 5. baseline_excess_change の測定 (項目 4)

### 5.1 測定対象の delta

各 target cid (および baseline cid) について、source_event 後の状態変化 (delta) を測定:

| 状態変数 | 測定方法 |
|---|---|
| Q | post_event Q - pre_event Q |
| C | post_event C - pre_event C |
| familiarity_max | post_event familiarity_max - pre_event familiarity_max |
| n_alphas | post_event n_alphas - pre_event n_alphas |
| n_observed_as_target | post_event - pre_event |
| pulse 発火回数 | event_window 内の pulse 数 |

### 5.2 観察解像度 (時間スケール)

GPT 監査 B8 反映: 固定窓 + peak_lag。

#### 固定窓
- 即時 (1-10 step)
- 短期 (10-100 step)
- 中期 (100-1000 step)

各窓で delta を計算。

#### peak_lag 測定
各 target cid について、baseline_excess_change が最大になる lag を 1 step 単位で同定:
```
peak_lag = argmax_lag(baseline_excess_change(lag))
```

最大値の上限は中期 (1000 step) まで。

### 5.3 波及パターン自動分類

peak_lag のパターンから target cid を分類:

| 分類 | 条件 |
|---|---|
| 即時型 | peak_lag < 10 step |
| 遅延型 | peak_lag > 100 step |
| 残響型 | 複数のピークを持つ、または定常的に増加 |

---

## 6. アバランシェ防止機構 (項目 5)

### 6.1 到達距離 (hop) の上限

source_cid からの relation_path 経由の到達距離を **最大 3 hop** に制限:
- 1 hop: source_cid と直接接続
- 2 hop: 1 hop の cid と接続
- 3 hop: 2 hop の cid と接続

4 hop 以上は記録しない。

### 6.2 減衰率 (Decay Rate) の追跡

各 source_event について、hop 別の baseline_excess_change を記録:
```
hop_1_excess = mean(baseline_excess_change for 1 hop targets)
hop_2_excess = mean(baseline_excess_change for 2 hop targets)
hop_3_excess = mean(baseline_excess_change for 3 hop targets)
```

減衰率パターンを記録 (線形 / 指数 / 急減衰 / 維持)。

### 6.3 共鳴ループの検出

source_cid → target_cid → source_cid のループを検出:
```
loop_2_hop: source_cid と target_cid が双方向に relation_path を持つ
loop_3_hop: source_cid → A → B → source_cid のパス
```

ループの強度と時間スケールを記録。

### 6.4 ストレージ上限

- 1 source_event あたり target cid 数の上限: 100 cid
  - 内訳: 5 種 relation_path × 各 20 cid (ただし relation_strength の上位)
- 1 seed あたりストレージ予算: 200 MB
- 全 24 seeds で 4.8 GB を超えないように設計

### 6.5 ハードリミット違反時の処理

実装中にストレージ上限を超える場合:
- 警告を出力
- target cid を relation_strength の高い順に切り詰める
- 切り詰められた件数を `truncation_log` に記録

---

## 7. 因果候補の階層化 (項目 6)

GPT 監査 Level 1-3 反映:

### 7.1 Level 1: co-occurrence

target cid 群の baseline_excess_change が観測される。

判定基準:
- |baseline_excess_change| > 1% (any baseline)
- 24 seeds で direction 一貫

### 7.2 Level 2: path-enriched

無関係 baseline (unrelated_baseline) より、relation_path 経由 (familiarity / attention / Integration) で baseline_excess_change が大きい。

判定基準:
- mean(target_delta on relation_path) - mean(target_delta on unrelated_baseline) > 1%
- 24 seeds で direction 一貫

### 7.3 Level 3: source-specific

event source (pulse / ingestion / alpha_formation / beta_formation / c_conversion) ごとに異なる変化パターン。

判定基準:
- source 別の path-enriched profile が統計的に異なる (Kruskal-Wallis 検定または同等)
- 効果サイズで切る (各 source 間の delta の差が 1% 以上)

### 7.4 Level 4 は v10.7 で実施しない

Level 4 (causal intervention) は v10.8 以降の射程。

---

## 8. 構造語の徹底 (項目 7)

GPT 監査 B7 反映: 実装仕様レベルで構造語を使用。

### 8.1 置換規則

| 作業上の仮名 | 実装仕様の構造語 |
|---|---|
| 発火 | source_event |
| 波及 | post_event_path_enriched_delta |
| 影響 | baseline_excess_change |
| 同期 | temporal_coactivation_enrichment |
| 経路 | relation_path_type |
| 周辺 | candidate_target_set |
| 意識 | c_conversion_event |

### 8.2 適用範囲

- CSV 列名: 全て構造語
- 関数名: 全て構造語
- 変数名: 全て構造語
- コメント / docstring: 構造語を主、作業仮名は最小限

### 8.3 例外

- 主題ドキュメント (v107_phase_design.md) のタイトル: 「発火」「波及」を残す (作業仮名)
- 議論レベル: 作業仮名 OK
- 実装レベル: 構造語のみ

---

## 9. WLD.artless の取り扱い (項目 8)

GPT 監査 B3 反映:

### 9.1 判定軸からの除外

WLD.artless は v10.7 の判定軸に使わない:
- target cid の意味的特性として WLD.artless を使わない
- baseline_excess_change の計算に WLD.artless 接地を使わない
- 因果候補の階層化に WLD.artless を使わない

### 9.2 補助情報としての記録

WLD.artless は以下で記録のみ:
- atom 接地の rank_1 として観察 (v10.6 と同様)
- target cid の atom 接地分布の参考

### 9.3 v10.8 以降の課題

WLD.artless 偏在性の解明 (構造特性 or 計算バイアス) は v10.7 では解決しない。v10.8 以降の課題として記録。

---

## 10. 物理層 frozen と bit-identity 検証 (項目 9)

### 10.1 物理層 frozen

post-process なので物理層には一切影響しない:
- 既存 v10.5 / v10.6 出力ファイルを変更しない
- output 先は `developmental/v107/outputs/` 配下のみ
- engine / physics / virtual / cognition runtime には触らない

### 10.2 二層 bit-identity 検証 (GPT 監査 B6 反映)

#### 層 A: 同 seed 2 回実行
- seed 0 を 2 回実行 (`audit_run_a`, `audit_run_b`)
- v10.7 post-process 出力が完全一致することを検証
- 完全一致しなければ非決定性が混入している

#### 層 B: v10.6 baseline との比較
- v10.6 で生成された per-window / pulse / event 出力が v10.7 実装中に変更されていないことを検証
- bit-identical を確認

#### 層 C: v10.7 が追加する CSV のみ差分
- v10.7 の output が、既存の v10.5 / v10.6 出力に対して **追加のみ** であることを確認
- 既存出力が変更されていないことを確認

### 10.3 実装時の path 縛り

- 入力: V105_ROOT / V106_ROOT 配下のみ read-only
- 出力: V107_ROOT 配下のみ write
- パストラバーサル防止: `Path(...).resolve()` で正規化

---

## 11. 実装の進行手順

### 11.1 認識確認ステップ (§0、必須)

Code A は本指示書を読んだ後、まず認識確認文書を作成。Web Claude / Taka 確認後に実装着手。

### 11.2 環境チェック (smoke 前)

- ESDE 出力ファイルの構造確認 (列名、データ型、行数)
- 既存ライブラリの利用可能性 (pandas、numpy、scipy 等)
- ストレージ予算の事前見積もり
- 環境チェック結果を `v107_environment_check_report.md` として記録

### 11.3 smoke test (seed 0 単独)

- seed 0 のみで全機能を動作確認
- audit_run_a / audit_run_b で bit-identity 検証
- 出力スキーマの確認
- ストレージ使用量の確認 (1 seed 200 MB を超えないか)

### 11.4 main run (24 seeds 単一バッチ)

- smoke test PASS 後に 24 seeds で本番実行
- 実行時間と総ストレージを記録
- 全 finding を CSV / parquet として出力

### 11.5 解析レポート作成

各層 (Level 1, 2, 3) の finding をレポート化:
- `v107_co_occurrence_report.md` (Level 1)
- `v107_path_enriched_report.md` (Level 2)
- `v107_source_specific_report.md` (Level 3)
- `v107_main_run_report.md` (総括)

### 11.6 完了報告

Web Claude / Taka に main run 完了を報告。本指示書の達成判定基準 (§12) を全て満たしているかチェック。

---

## 12. 達成判定基準 (v10.7 完了の条件)

| 項目 | 達成基準 |
|---|---|
| 認識確認ステップ | Code A の v107_code_recognition_check.md 提出 + Taka 承認 |
| 環境チェック | v107_environment_check_report.md 提出 |
| 5 種 source_event の同定 | 24 seeds 全部 |
| 5 種 candidate_target_set の構築 | 各 source_event ごとに 5 種 |
| 5 種ベースライン群の構築 | 各 source_event ごとに 5 種 |
| Level 1 (co-occurrence) | 全 source_event で達成 |
| Level 2 (path-enriched) | 全 source_event で達成 |
| Level 3 (source-specific) | source 種別ごとの差を定量化 |
| peak_lag 測定 | 各 target cid で実施 |
| 波及パターン自動分類 | 即時型 / 遅延型 / 残響型 |
| アバランシェ防止 | 到達距離 ≤ 3 hop、ストレージ ≤ 200 MB/seed |
| 物理層 frozen | bit-identity PASS (層 A + 層 B + 層 C) |
| 構造語の徹底 | CSV 列名、関数名、変数名で全て構造語 |
| WLD.artless 除外 | 判定軸に使わない (補助情報のみ) |

→ 全項目 PASS で v10.7 主題完了。

---

## 13. 質問・確認の窓口

### 13.1 Web Claude (相談役)

- 本指示書の解釈の質問
- 設計レベルの相談
- v10.6 finding との整合性の確認

### 13.2 Taka (Director)

- 主題の方向性に関わる判断
- 設計の根本的な変更が必要な場合
- 規律違反の判断

### 13.3 Code A 自身の判断 (推奨)

- 実装の細部 (関数の分割、ライブラリの選択等) は Code A の判断
- 設計の甘い部分は Code A が指摘 (Taka 整理「設計の甘いところは Claude Code に突っ込まれる」)
- 認識確認文書で疑問点を表明

---

## 14. 期待する Code A の動き

### 14.1 認識確認 → 環境チェック → smoke → main の段階的進行

各段階で完了報告を行い、次に進む前に確認を取る。これにより手戻りを減らす。

### 14.2 設計の甘さの指摘

本指示書の設計に甘い部分があれば、Code A が認識確認段階で指摘:
- 5 種 relation_path の定義の曖昧性
- 5 種ベースラインの構築可能性
- アバランシェ防止機構の現実性
- ストレージ予算の現実性

### 14.3 v10.6 の延長としての効率化

v10.6 で実装した v106_post_process.py の機構を再利用可能な部分は再利用。

例:
- atom_profiles_cache (atom 接地の補助情報として継続使用)
- 48 次元構造ベクトル (target cid の構造特性として参考)
- 5 種パターン分類 (5 パターンを relation_path の参考に)

---

## 15. 一文サマリ

v10.7 では post-process として ESDE Genesis 系内部の 5 種 source_event (pulse / ingestion / alpha_formation / beta_formation / c_conversion) と 5 種 candidate_target_set (familiarity / attention / Integration / temporal_coactivation / matched 経路) を 5 種ベースライン群に対する baseline_excess_change として定量化し、因果候補の階層化 Level 1-3 を達成、peak_lag による波及パターン自動分類、アバランシェ防止機構、ストレージ上限、構造語の徹底、WLD.artless 判定軸からの除外、二層 bit-identity 検証を実装する。Code A は **実装着手前に v107_code_recognition_check.md を作成し、認識のずれを Web Claude / Taka に確認** してから実装を進める。

---

*以上、v10.7 実装指示書。Code A は §0 の認識確認ステップから開始してください。*
