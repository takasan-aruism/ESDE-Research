# L06 個別時系列分析 — 設計書

*Date*: 2026-04-15
*From*: 相談役 Claude
*Target*: Claude Code A (実行)
*Phase*: v9.12 / Phase 1
*Status*: Taka 承認待ち
*対応上位文書*: GPT 監査メモ (2026-04-15) + 相談役所見 (本スレッド §4) + v9.12 ワークフロー (本スレッド §改訂版)

---

## 0. 本資料の位置づけ

v9.11 で観測された L06 (long top 10%、n_pulses_eval ≥ 167、114 cids) の capture rate 低下 (overall 0.379 → L06 0.307) は、**M_c 固定 vs E_t 進行による mismatch 蓄積**を実測で示した可能性が高い。本作業はこの仮説を **既存データのみで検証**し、v9.13 以降の retention / 検証層機構の設計前提データとする。

新機構の実装はゼロ。`diag_v911_capture_long/pulse/pulse_log_seed{0..4}.csv` (5 seeds) と `diag_v911_capture_long/subjects/per_subject_seed{0..4}.csv` の集計のみ。

**単一の真実の源**: v9.12 ワークフロー §Phase 1 (本スレッドで Taka 承認済み)。本資料と矛盾した場合、上位が優先。
本資料で未定義の仕様は Taka に戻す。

---

## 1. 体制判定と理由

**判定**: **軽量**

**根拠** (00_index.md §体制判定基準):
- 既存出力データ (long pulse_log) の集計のみ、新規 run なし
- 実装変更ゼロ、新規 Python 集計スクリプト 1 本のみ
- 結果は単独参考データ (本実装に組み込まない)

**この判定での体制**:
- 相談役 Claude: 設計書 + 集計スクリプト作成
- Code A: Ryzen 上で実行 + 出力 upload
- Code B: 省略 (再集計の再集計は事務作業になる)
- Taka + 相談役: 結果読み合わせ

---

## 2. ファイル構成

| 役割 | パス | 備考 |
|---|---|---|
| 集計対象 (read-only) | `primitive/v911/diag_v911_capture_long/pulse/pulse_log_seed{0..4}.csv` | 5 ファイル |
| 集計対象 (read-only) | `primitive/v911/diag_v911_capture_long/subjects/per_subject_seed{0..4}.csv` | 5 ファイル、L06 cid 抽出に使用 |
| 新規スクリプト | `primitive/v912/v912_l06_timeseries.py` | 集計のみ、本実装に組み込まない |
| 出力ディレクトリ | `primitive/v912/diag_l06_timeseries/` | 新規作成 |
| 出力レポート | `primitive/v912/v912_l06_timeseries_report.md` | 04_phase_summary テンプレ準拠 |
| 不変 | `primitive/v911/v911_cognitive_capture.py` | 1 バイトも変更しない |

---

## 3. 作業範囲

### 3.1 含めるもの

1. **L06 cid 抽出** — long per_subject CSV から `n_pulses_eval ≥ 167` の cid 集合を確定 (期待 114 cids)
2. **L06 cid pulse 時系列の抽出** — long pulse_log CSV から該当 cid の全 pulse 行を抜き出す
3. **集計 (a) 全 L06 平均推移** — pulse_n (cid 内通し番号) ごとに Δ / 各軸 / p_capture / capture rate の平均
4. **集計 (b) cid 別個別推移** — 114 cid それぞれの時系列 CSV を出力 (visualize 用、plot は別作業)
5. **集計 (c) Δ spike vs capture failure** — Δ 上位 10% pulse での captured 分布、Δ 下位 10% との対比
6. **集計 (d) Δ 自己相関** — cid 内の Δ 系列の自己相関関数 (lag 1〜10 pulse)、滑らかさ判定
7. **集計 (e) 最初に乖離する軸** — cid 内で最初に閾値超え (各軸 Δ_axis > p90 of overall) を起こした軸の cid 別分布
8. **集計 (f) n_core 別の挙動差** — L06 を n_core ∈ {2, 3, 4, 5} で層別し、(a)(d) を再集計

### 3.2 含めないもの

1. **「埋め合わせ機構」の実装検討** — 本作業の対象外。観察データのみ提供
2. **plot / 可視化** — 出力 CSV は plot 可能な形にするが、plot 自体は本作業の範囲外 (Taka が必要なら別作業)
3. **short run データの分析** — long のみ対象 (L06 = long top 10% で定義済み)
4. **cold_start pulse の集計対象化** — pulse_log にあっても集計から除外 (v9.11 規律と整合)
5. **cid 間の相互作用分析** — Phase 4 / v9.13 以降の意識層議論で扱う

### 3.3 出力 (期待成果物)

| 種類 | パス | 備考 |
|---|---|---|
| 実行スクリプト | `primitive/v912/v912_l06_timeseries.py` | |
| 集約 CSV | `primitive/v912/diag_l06_timeseries/aggregate.csv` | (a)(c)(e)(f) の集計表 |
| 個別 CSV | `primitive/v912/diag_l06_timeseries/per_cid/cid_<cid_id>_seed<seed>.csv` | 114 ファイル、(b) 用 |
| 自己相関 CSV | `primitive/v912/diag_l06_timeseries/autocorrelation.csv` | (d) 用 |
| 集約レポート | `primitive/v912/v912_l06_timeseries_report.md` | 04_phase_summary テンプレ準拠 |

---

## 4. 追加データ構造

該当なし (集計のみ、新規定数 / フィールド / クラス追加なし)。

---

## 5. 実装手順

1. **Step 1** — L06 cid 抽出 (per_subject CSV から `n_pulses_eval ≥ 167` で filter、114 cid 期待、不一致なら Taka に戻す)
2. **Step 2** — L06 cid の全 pulse 行を long pulse_log から抽出 (cold_start 行は記録のみ別カウント、集計対象は eval 行のみ)
3. **Step 3** — 集計 (a) 全 L06 平均推移を pulse_n bin ごとに算出
4. **Step 4** — 集計 (b) cid 別 CSV を per_cid/ に出力
5. **Step 5** — 集計 (c) Δ spike vs capture failure
6. **Step 6** — 集計 (d) Δ 自己相関 (cid ごとに計算 → 全 L06 平均)
7. **Step 7** — 集計 (e) 最初に乖離する軸 (各軸の overall p90 閾値を先に算出 → cid ごとに最初の閾値超え軸を判定)
8. **Step 8** — 集計 (f) n_core 別層別集計
9. **Step 9** — レポート作成 (04_phase_summary テンプレ準拠)

各 Step は独立、巻き戻し可。Step 1 失敗 (114 でない) のときのみ後続停止。

---

## 6. 不変量チェックリスト

軽量作業のため最小限。Code B チェック省略だが、Code A は self-check として実行。

### 6.1 共通不変量

- [ ] `v911_cognitive_capture.py` 1 バイト変更なし
- [ ] `diag_v911_capture_long/` 配下のファイル変更なし (read-only access)

### 6.2 本作業特有

- [ ] L06 cid 抽出数 = 114 (v911_cognitive_capture_result.md §5.1 と一致)
- [ ] cold_start 行が集計に混入していない (eval 行のみ集計)
- [ ] cid 別 CSV 数 = 114 (アンマッチなら抽出ロジック異常)
- [ ] 集計対象 pulse 数 = L06 cid 全体の n_pulses_eval 合計 (各 cid の n_pulses_eval ≥ 167 × 114 ≥ 19,000、実際は per_subject の v11_n_pulses_eval 合計と一致)

---

## 7. smoke 判定基準

軽量作業のため smoke 不要。1 seed (seed=0) のみで pilot 実行 → 集計が想定通りに走ることを確認 → 5 seeds に展開、の 2 段階で十分。

pilot 確認項目:
- [ ] L06 cid (seed=0 分のみ) の pulse 抽出が動く
- [ ] 集計 (a)〜(f) が例外なく完走
- [ ] 出力 CSV が読み込める形式

---

## 8. 本格 run 構成

| 項目 | 値 |
|---|---|
| 対象 seed | 0..4 (5 seeds) |
| 並列 | 不要 (集計のみ、I/O bound) |
| 想定実行時間 | 数分〜十数分 (5 ファイル合計 75,600 pulse 行の集計) |

```bash
# pilot
python primitive/v912/v912_l06_timeseries.py --pilot --seed 0

# 本実行
python primitive/v912/v912_l06_timeseries.py
```

`OMP/MKL/OPENBLAS_NUM_THREADS=1` は集計のみなので必須ではないが、設定しておく (慣習)。

---

## 9. 禁則事項

- `v911_cognitive_capture.py` および engine / VL 系列に 1 バイトも触らない
- `diag_v911_capture_long/` 配下のファイルを上書きしない (read-only)
- short run データを混入させない (本作業は long のみ)
- 集計内で cold_start 行を eval 集計に混ぜない
- L06 の定義 (`n_pulses_eval ≥ 167`) を変更しない (v9.11 結果との整合性)
- 「埋め合わせ機構」の実装に踏み込まない (観察のみ)

---

## 10. Taka への確認事項

実装着手前に確定しておきたい点 3 つ。

### 10-1. pulse_n bin の刻み

集計 (a) で pulse_n 軸を bin で集計するが、刻み幅をどうするか。
- 提案: **bin 幅 = 5 pulses** (cid の pulse_n は 4..497、bin 数 ~100、各 bin の cid 数が偏らない)
- 別案: 等頻度 bin (各 bin に同数 pulse が入るよう動的設定)

→ **確認**: bin 幅 5 で進めて OK か?

### 10-2. 自己相関の lag 範囲

集計 (d) で Δ の自己相関を計算する lag 範囲。
- 提案: lag ∈ {1, 2, 3, 5, 10} pulses (5 値、L06 cid の最短 pulse 数 167 に対し十分小さい)
- 別案: lag ∈ {1, 2, 5, 10, 20, 50}

→ **確認**: 5 値で進めて OK か? 「埋め合わせらしき瞬間」検出の連続 N 判定はこの自己相関結果を見てから別途決定。

### 10-3. 「最初に乖離する軸」の閾値

集計 (e) で各軸の閾値を「overall (long 全 cid 全 pulse) の p90」とする。
- 提案: long pulse_log 全行 (eval のみ) から d_n / d_s / d_r / d_phase の各 p90 を算出 → cid ごとに最初に超えた軸を記録
- L06 cid のうち初期 cold_start (pulse 1-3) 行は対象外、pulse_n=4 から判定
- 「どの軸も超えない」cid もありうる → "none" としてカウント

→ **確認**: この閾値設計で OK か?

---

## 11. 一文サマリ

L06 (long top 10%、114 cids) の pulse 単位時系列を既存データから抽出し、(a) 全平均推移 / (b) 個別曲線 / (c) Δ spike と capture failure の対応 / (d) Δ 自己相関 / (e) 最初に乖離する軸 / (f) n_core 別 を集計する。新機構実装ゼロ、軽量。retention / 検証層の設計前提データを提供する。
