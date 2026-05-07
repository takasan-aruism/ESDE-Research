# v10.8 実装指示書 — Atom 単独持ち込み機構の最小実装 (Level 3.5、A 群)

*作成*: 2026-05-07、Web Claude (相談役)
*対象*: Code A (Implementer)
*親*: `v108_phase_design.md` (両 AI 統合修正版主題ドキュメント)
*位置づけ*: v10.8 主題の Code A 向け実装指示書。Taka 指示 (2026-05-06) により、**Code A が実装着手前に認識確認文書を返すステップを必須化** (v10.7 で機能実証済)。

---

## 0. Code A への最初の依頼 (認識確認ステップ、必須)

**実装着手前に**、本指示書を読んだ上で以下を含む認識確認文書 (`v108_code_recognition_check.md`) を作成し、Web Claude / Taka に提出してください。

### 0.1 認識確認文書に含める項目

1. **本指示書で求められている主題の理解** (3-5 行で要約)
2. **atom_introduction_event の Pulse フォーマット同一性** が実装可能かの判定
3. **Q/C エネルギーコストの実装方法** (Pulse と同等のコスト)
4. **案 Q (top_k cid 構造条件) で source_cid を選定する方法** が v10.6 出力から実装可能か
5. **案 α (均等分散発火) のスケジューリング方法**
6. **5 + 1 種ベースライン群 + global activation 補正** が現実的に計算可能か
7. **副次観察 3 件** (Whiteout、Small-World、誤差分布) の実装可能性
8. **環境チェック結果** (使えるデータ、列名、ファイル形式の確認)
9. **設計の甘い部分** (Code A から見た落とし穴、再設計が必要な箇所)
10. **実装にかかる予想時間** (smoke + main run の見積もり)
11. **ストレージ予算** (v10.7 が 428 MB、v10.8 で増分の見積もり)
12. **質問事項** (本指示書で不明確な点、Taka / Web Claude に確認したい点)

### 0.2 確認後の流れ

- Web Claude / Taka が認識確認文書を確認
- 認識が正しければ実装着手の許可
- ずれていれば指示書を修正
- v10.7 では設計の甘さ 6 件が認識確認で発見・修正された (手戻りゼロで完了)

### 0.3 設計の甘さは Code A が突く前提

Taka 整理 (2026-05-06):
> どうせ設計の甘いところは Claude Code に突っ込まれる
> あんまり気にせず

本指示書の設計に甘い部分があっても、Code A が認識確認段階で指摘してください。修正を経て実装着手します。

---

## 1. 実装の全体像

### 1.1 機構の位置づけ

post-process として実装。ESDE engine / physics / virtual / cognition runtime には一切手を加えない。**v10.7 のオービスを拡張** する形で実装。

入力: ESDE Genesis 系 v10.7 出力 + v10.6 atom_alignment_observer 出力
出力: `developmental/v108/outputs/` 配下

### 1.2 v10.7 からの変更点

v10.7 のオービスに以下を追加:
1. atom_introduction_event を source_event 第 6 種として追加
2. v10.7 natural source_event baseline (新規ベースライン)
3. global activation 補正
4. 副次観察 3 件 (Whiteout、Small-World、誤差分布)

それ以外は v10.7 と同じ。

### 1.3 ファイル構造

```
developmental/v108/
├── v108_phase_design.md             (主題ドキュメント、参照のみ)
├── v108_implementation_brief.md     (本ドキュメント、参照のみ)
├── v108_code_recognition_check.md   (Code A 作成、認識確認)
├── v108_post_process.py             (主処理、orchestrator)
├── v108_atom_event_generator.py     (atom_introduction_event 生成、案 Q)
├── v108_event_aggregator_extension.py (source_event に第 6 種追加)
├── v108_global_activation_correction.py (global activation 補正、GPT B2)
├── v108_whiteout_monitor.py         (副次観察、Gemini A1)
├── v108_smallworld_comparison.py    (副次観察、Gemini A6)
└── outputs/
    ├── smoke/
    │   └── seed 0 + audit_run_a/b
    └── main/
        ├── atom_introduction_events_seed*.parquet
        ├── (v10.7 と同様の出力ファイル群、ただし source_event 第 6 種を含む)
        ├── global_activation_factor_seed*.parquet
        ├── whiteout_monitor_seed*.parquet
        ├── smallworld_comparison_seed*.parquet
        ├── error_distribution_seed*.parquet
        └── cross_seed/
            ├── level_1_atom_co_occurrence.parquet
            ├── level_2_atom_path_enriched.parquet
            ├── level_3_atom_source_specific.parquet
            ├── atom_vs_natural_baseline.parquet
            └── (副次観察集計)
```

---

## 2. atom_introduction_event の生成 (案 Q + Pulse フォーマット)

### 2.1 案 Q: v10.6 top_k cid 構造条件を使う

#### 入力データ

v10.6 atom_alignment_observer の出力:
- `developmental/v106/outputs/main/atom_profiles_cache.npz` (Atom 326 個の 48 次元プロファイル)
- `developmental/v106/outputs/main/per_subject_with_atom_alignment.parquet` (各 cid の atom 接地情報)

または v10.6 で記録された top_k cid 情報 (Code A が環境チェックで確認)。

#### top_k cid 抽出

各対象 atom (26 atom) について:
1. v10.6 で計算された atom と cid の cosine 類似度を取得
2. 類似度が高い top_k cid (k は Code A 判断、目安 20) を抽出
3. これらの cid の構造条件 (n_core、age、hosted 状態等) を抽出
4. 同条件を満たす既存 cid を source_cid 候補とする

#### source_cid 候補の数

各 atom について source_cid 候補 100 個を確保 (発火 100 events を分散させるため)。

### 2.2 atom_introduction_event の Pulse フォーマット同一性 (Gemini A8)

#### Pulse の形式 (既存)

Code A は v10.5 / v10.7 のコードから Pulse 処理の正確な形式を確認:
- pulse_log の列: cid, t, ... (詳細は Code A の環境チェック)
- state transition のフォーマット
- timestamp 形式

#### atom_introduction_event の形式

atom_introduction_event は Pulse と完全に同一フォーマット + atom 情報を持つ:
```
event_id (uuid)
seed (0-23)
event_source_type ('atom_introduction_event')
source_cid (Pulse と同じ列)
timestamp (Pulse と同じ形式)
pre_event_state (Pulse と同じ、Q / C / familiarity_max / n_alphas 等)
atom_id (新規列、'PER.sound' 等)
atom_index (新規列、26 atom のインデックス 0-25)
top_k_rank (新規列、source_cid が atom にとって何番目の top_k だったか)
```

#### 神の手回避

`atom_introduction_event` を Pulse と同じ形式で記述することで:
- 物理層の state を直接書き換えない
- 既存 cid の Q/C を消費する形で記述
- 系の連続性を保つ

### 2.3 Q/C エネルギーコスト (Gemini A3)

#### コストの方式

Pulse と同等の Q/C 消費:
- Pulse 1 回あたりの Q 消費 (例: -1) と同じ
- atom_introduction_event 1 回あたり Q -1 (Code A が Pulse の実コストを確認して同等に)

#### 動的平衡の維持

26 atom × 100 events × 24 seeds = 62,400 events のコスト分散:
- 1 seed あたり 2,600 events
- 25,000 step に分散 (1 event あたり 9.6 step 間隔)
- Q 消費は系の自然な減衰律に組み込まれる

### 2.4 案 α: 均等分散発火

#### 時間的分散

- 各 atom 100 events を 25,000 step に均等分散
- 1 event あたり 250 step 間隔 (1 atom 内)
- 26 atom 全体では同時刻発火を避けるため、atom 間でも step をずらす
- 同 step の発火を最小化

#### 位相的分散 (案 Q から自動達成)

各 atom の top_k cid は構造的に異なる cid 群:
- top_k は v10.6 で atom と類似度が高かった cid
- 26 atom の top_k は基本的に重複が少ない
- → 近接 cid への集中投下にならない (位相的分散が自動達成)

---

## 3. 5 + 1 種ベースライン群 + global activation 補正

### 3.1 ベースライン構成

#### v10.7 から継承 (5 種)

1. unrelated_baseline
2. **same_step_random_baseline** (重要)
3. matched_baseline (n_core / age / hosted)
4. same_integration_low_familiarity_baseline
5. high_familiarity_outside_integration_baseline

#### v10.8 新規 (1 種)

6. **v10.7 natural source_event baseline**: v10.7 で観察された 5 種 source_event (pulse / ingestion / α 形成 / β 形成 / 意識発動) の波及プロファイル

#### 比較

各 atom_introduction_event の波及を:
- 5 種 baseline それぞれと比較
- v10.7 natural source_event baseline と比較
- → atom_introduction_event が natural source_event と区別できる効果を持つかを判定

### 3.2 global activation 補正 (GPT B2)

#### 全体活性化レベルの計算

各 step で:
```
global_activation_factor(step) = total_pulse_count(step) + total_event_count(step)
```

または同等の指標 (Code A が判断)。

#### 補正の適用

```
adjusted_baseline_excess_change = raw_excess_change - normalize(global_activation_factor(step))
```

これにより、ESDE 全体の時間的活性化を Atom 効果と誤認するリスクを排除。

#### 出力

`global_activation_factor_seed*.parquet`:
- step
- global_activation_factor (生値)
- normalized_factor (正規化値)

---

## 4. 副次観察 3 件

### 4.1 Whiteout 監視 (Gemini A1)

#### 目的

26 atom 同時発火による波及干渉が起きていないかを監視。個別 atom の波及プロファイルが分離可能であることを確認。

#### 実装方針

1. 各 atom_introduction_event の波及プロファイルを記録
2. 同時刻 (± 数 step) に発火した他 atom の波及との重なりを検出
3. 個別 atom の波及プロファイルが分離可能か判定

#### 判定基準

- 個別 atom の波及プロファイル間の独立性 (相関係数等)
- 0.5 以下を「分離可能」、0.7 以上を「Whiteout 警戒」(閾値は Code A 判断)

#### 出力

`whiteout_monitor_seed*.parquet`:
- atom_id_a
- atom_id_b
- correlation_coefficient
- whiteout_flag (binary)

### 4.2 Small-World 構造の維持確認 (Gemini A6)

#### 目的

v10.7 で発見した small-world 構造 (2-hop loop 14,343 件、3-hop loop 110,103 件) が v10.8 で維持されているか、または過学習的に強制同期されているかを確認。

#### 実装方針

1. v10.8 main run 完了後の共鳴ループ統計を計算
2. v10.7 main run の共鳴ループ統計と比較
3. 大きな変化があれば Small-World 崩壊の警戒

#### 判定基準

- 2-hop loop 件数の v10.7 vs v10.8 の比率
- 3-hop loop 件数の v10.7 vs v10.8 の比率
- ± 20% 以内を「維持」、それ以上の変化を「警戒」(閾値は Code A 判断)

#### 出力

`smallworld_comparison_seed*.parquet`:
- seed
- v107_loop_2_hop
- v108_loop_2_hop
- v107_loop_3_hop
- v108_loop_3_hop
- ratio_2_hop
- ratio_3_hop
- maintenance_flag

### 4.3 誤差分布の形状観察 (Gemini A5、Taka 示唆)

#### 目的

各 atom の波及プロファイルの delta 分布の形状を観察し、「確率的発生と誤差表現能力の融合可能性」の素材として記録。

#### 実装方針

1. 各 atom × 各 relation_path × 各観察解像度の delta 値を集約
2. 分布の統計量 (mean、median、std、skewness、kurtosis) を計算
3. 多峰性の検出 (例: bimodality coefficient)
4. 形状を分類 (正規分布 / 歪み / 多峰性 / その他)

#### 出力

`error_distribution_seed*.parquet`:
- atom_id
- relation_path_type
- observation_window
- mean、median、std、skewness、kurtosis
- bimodality_coefficient
- distribution_shape_label

### 4.4 副次観察の集約

副次観察は v10.8 の主題判定には含めない (失敗の定義に入れない)。観察結果として記録のみ。

---

## 5. 因果候補の階層化 (Level 3.5)

### 5.1 Level 3.5 の意味 (GPT B8)

> v10.8 は Level 4 causal intervention ではなく、Level 3.5 introduced event comparison として扱う

#### Level 3.5 の判定

- introduced event (atom_introduction_event) と natural event の波及プロファイルの差分観察
- 因果断定はしない
- 「event を入れたら X が起きた」ではなく「event を入れた後の変化が natural と異なる」

#### 表現

CSV 列名や関数名で:
- `introduced_vs_natural_delta`
- `atom_introduction_baseline_excess`
- `vs_natural_source_event_diff`

「causal_effect」「causal_proof」のような断定的命名は禁止。

### 5.2 Level 1-3 (v10.7 継承) も実施

v10.7 と同じく Level 1-3 を atom_introduction_event について実施:

| Level | 内容 | 達成基準 |
|---|---|---|
| Level 1: atom co-occurrence | atom_introduction_event 後に target で変化 | direction 24/24 一貫 |
| Level 2: atom path-enriched | 経路上で変化が大きい | unrelated + same_step + global_activation 補正後 1% 超 |
| Level 3: atom source-specific | 26 atom 間で systematic な差 | WLD.artless 除く 25 atom |
| Level 3.5: introduced vs natural | natural と区別できる効果 | 波及プロファイルが natural と異なる |

---

## 6. WLD.artless 留保ラベル (GPT B7)

### 6.1 留保の背景

v10.6 留保「WLD.artless 偏在性が構造特性 or 計算バイアス未分離」を継承。v10.7 でも判定軸から外していた。v10.8 でも同じ扱い。

### 6.2 実装上の対応

- WLD.artless の atom_introduction_event は他 atom と同様に発火・観察する (記録は残す)
- Level 1-3.5 の集計から WLD.artless は除外、ただし「reserved」ラベル付きで記録
- 「26 atom で Level 3 達成」ではなく「25 atom で Level 3 達成、WLD.artless は留保」と表現

### 6.3 出力での扱い

CSV に `reserved_label` 列を追加:
- WLD.artless の行: `reserved_label = 'wld_artless_pending'`
- それ以外: `reserved_label = ''` (空)

---

## 7. 物理層 frozen と bit-identity 検証

### 7.1 物理層 frozen

post-process なので物理層には一切影響しない:
- 既存 v10.5 / v10.6 / v10.7 出力ファイルを変更しない
- output 先は `developmental/v108/outputs/` 配下のみ
- engine / physics / virtual / cognition runtime には触らない
- Pulse フォーマット同一性で神の手回避

### 7.2 二層 bit-identity 検証 (継承)

#### 層 A: 同 seed 2 回実行

- seed 0 を 2 回 (`audit_run_a`, `audit_run_b`)
- v10.8 post-process 出力が完全一致することを検証
- v10.7 で確認した「post_process_run_summary は実行時間記録で差分」と同様、サマリ系は除外可

#### 層 B: v10.7 baseline との比較

- v10.7 出力ディレクトリ (`developmental/v107/outputs/main/`) のファイル一覧の MD5 hash を v10.8 実装前後で比較
- bit-identical を確認
- v10.7 出力が変更されていないことを確認

#### 層 C: v10.8 出力先縛り

- 全出力が `developmental/v108/outputs/` 配下
- v105 / v106 / v107 配下への書き込みなし
- `assert_output_under_v108` で path traversal 防止

### 7.3 path 縛り

- 入力: V105_ROOT / V106_ROOT / V107_ROOT 配下のみ read-only
- 出力: V108_ROOT 配下のみ write
- パストラバーサル防止: `Path(...).resolve()` で正規化

---

## 8. 実装の進行手順

### 8.1 認識確認ステップ (§0、必須)

Code A は本指示書を読んだ後、まず認識確認文書を作成。Web Claude / Taka 確認後に実装着手。

### 8.2 環境チェック (smoke 前)

- ESDE 出力ファイルの構造確認 (v10.5 / v10.6 / v10.7 全部)
- v10.6 atom_profiles_cache の構造確認
- top_k cid 情報の取得方法の確認
- Pulse 処理ルールの正確な形式の確認
- ストレージ予算の事前見積もり
- 環境チェック結果を `v108_environment_check_report.md` として記録

### 8.3 smoke test (seed 0 単独)

- seed 0 のみで全機能を動作確認
- 26 atom × 100 events で 2,600 atom_introduction_events 生成・処理
- audit_run_a / audit_run_b で bit-identity 検証
- 出力スキーマの確認
- ストレージ使用量の確認 (1 seed の予算内か)
- 副次観察 3 件の動作確認 (Whiteout / Small-World / 誤差分布)

### 8.4 main run (24 seeds 単一バッチ)

- smoke test PASS 後に 24 seeds で本番実行
- 26 atom × 100 events × 24 seeds = 62,400 atom_introduction_events
- 実行時間と総ストレージを記録
- 全 finding を CSV / parquet として出力

### 8.5 解析レポート作成

各層の finding をレポート化:
- `v108_atom_co_occurrence_report.md` (Level 1)
- `v108_atom_path_enriched_report.md` (Level 2)
- `v108_atom_source_specific_report.md` (Level 3)
- `v108_introduced_vs_natural_report.md` (Level 3.5)
- `v108_subsidiary_observations_report.md` (副次観察 3 件)
- `v108_main_run_report.md` (総括)

### 8.6 完了報告

Web Claude / Taka に main run 完了を報告。本指示書の達成判定基準 (§10) を全て満たしているかチェック。

---

## 9. 質問・確認の窓口

### 9.1 Web Claude (相談役)

- 本指示書の解釈の質問
- 設計レベルの相談
- v10.7 finding との整合性の確認

### 9.2 Taka (Director)

- 主題の方向性に関わる判断
- 設計の根本的な変更が必要な場合
- 規律違反の判断

### 9.3 Code A 自身の判断 (推奨)

- 実装の細部 (関数の分割、ライブラリの選択等) は Code A の判断
- 設計の甘い部分は Code A が指摘
- 認識確認文書で疑問点を表明

---

## 10. 達成判定基準 (v10.8 完了の条件)

| 項目 | 達成基準 |
|---|---|
| 認識確認ステップ | Code A の v108_code_recognition_check.md 提出 + Taka 承認 |
| 環境チェック | v108_environment_check_report.md 提出 |
| atom_introduction_event の同定 | 26 atom × 24 seeds で安定発火 (Pulse フォーマット同一) |
| Q/C エネルギーコスト | 既存 cid の Q/C を消費、動的平衡維持 |
| source_cid 選定 (案 Q) | top_k cid 構造条件で選定 |
| 発火タイミング (案 α) | 均等分散、同時刻発火回避 |
| 5 + 1 種ベースライン群 | v10.7 5 種 + natural source_event |
| global activation 補正 | step 別の全体活性化レベルで補正 |
| Level 1 (atom co-occurrence) | direction 24/24 一貫 |
| Level 2 (atom path-enriched) | unrelated + same_step + global_activation 補正後で 1% 超 |
| Level 3 (atom source-specific) | WLD.artless 除く 25 atom 間で systematic な差 |
| Level 3.5 (introduced vs natural) | 波及プロファイルが natural と異なる |
| 物理層 frozen | bit-identity PASS (層 A + B + C) |
| 構造語と直感語の併記 | 実装は構造語 |
| 規律 3 件遵守 | 魔法回避 / same_step 比較 / Atom 類似度で target 選ばない |
| Level 3.5 位置づけ | 因果断定回避、event 比較として記述 |
| Whiteout 監視 (副次) | 個別 atom 波及プロファイル分離可能 |
| Small-World 維持 (副次) | v10.7 vs v10.8 共鳴ループ統計が大きく変わらない |
| 誤差分布の記録 (副次) | atom 別の delta 分布形状 |

→ 全項目 PASS で v10.8 主題完了 (副次観察は記録のみで主題判定には影響しない)。

---

## 11. v10.6 / v10.7 からの流用

### 11.1 v10.6 から流用

- atom_profiles_cache (Atom 326 個の 48 次元プロファイル)
- per_subject_with_atom_alignment (各 cid の atom 接地)
- top_k cid 情報

### 11.2 v10.7 から流用

- 5 機能モジュール (event_aggregator、path_analyzer、baseline_constructor、avalanche_monitor、orchestrator)
- 5 種 source_event の同定ロジック (pulse / ingestion / α / β / c_conversion)
- 5 種 relation_path の構築ロジック
- 5 種ベースライン群の構築ロジック
- 因果候補の階層化 Level 1-3
- アバランシェ防止機構
- bit-identity 検証

v10.8 で **追加実装** するのは:
- atom_introduction_event の生成 (案 Q)
- source_event 第 6 種としての追加
- v10.7 natural source_event baseline (新規)
- global activation 補正
- Level 3.5 introduced vs natural
- 副次観察 3 件 (Whiteout、Small-World、誤差分布)
- WLD.artless 留保ラベル

---

## 12. 期待する Code A の動き

### 12.1 認識確認 → 環境チェック → smoke → main の段階的進行

各段階で完了報告を行い、次に進む前に確認を取る。

### 12.2 設計の甘さの指摘

本指示書の設計に甘い部分があれば、Code A が認識確認段階で指摘:
- atom_introduction_event の Pulse フォーマット同一性の実装可能性
- top_k cid 情報の取得方法
- Q/C エネルギーコストの具体値
- 副次観察 3 件の閾値設定
- ストレージ予算の現実性

### 12.3 v10.7 の延長としての効率化

v10.7 の機構を最大限再利用。新規実装は最小限。

---

## 13. 一文サマリ

v10.8 では post-process として、ESDE Genesis 系内部に **atom_introduction_event を Pulse 処理ルールと同一フォーマットで既存 cid に外部付与** (案 X)、**v10.6 の top_k cid 構造条件を活用して source_cid を選定** (案 Q)、**26 atom × 100 events × 24 seeds = 62,400 events を均等分散発火** (案 α)、**Q/C エネルギーコスト** で動的平衡維持、**5 種 v10.7 ベースライン + v10.7 natural source_event baseline + global activation 補正** で過大評価を防止、**Level 1-3 + Level 3.5 introduced vs natural** の階層化で因果候補を観察、**WLD.artless 留保ラベル**、**Whiteout 監視 + Small-World 維持確認 + 誤差分布形状観察** を副次観察、**物理層 frozen + bit-identity 検証** を維持して実装する。Code A は **実装着手前に v108_code_recognition_check.md を作成し、認識のずれを Web Claude / Taka に確認** してから実装を進める。

---

*以上、v10.8 実装指示書。Code A は §0 の認識確認ステップから開始してください。*
