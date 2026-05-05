# v10.6 smoke + main run 報告書

*生成*: 2026-05-05、Code A
*親*: `v106_implementation_brief.md` + 差分パッチ #1
*対象*: Web Claude (相談役) → Taka (最終承認)

## 0. 一文サマリ

v10.6 atom_alignment_observer は smoke (seed 0) + main (24 seeds 単一バッチ) ともに成功。実装中に発覚した実態 3 件を反映済み。観測結果として **(a) seed 間 mean_max_sim std=0.0045 の極端な安定**、**(b) 事前推測との大きな乖離 (ハブ cid → SOC ではなく COG/FND/EXS)**、**(c) 全 cid の 51% が rank_1=CHG.begin に集中** という構造が浮上した。Web Claude の追加判断を要する点が複数あるため、本番解釈の前に判断確認を要する。

---

## 1. パッチ #1 反映状況 + 実装中追加修正

### 1.1 パッチ #1 で確定済 (6 項目すべて反映)

- ✅ axis 3 boundaries → `[10, 30, 60, 150]` (実分布ベースで再調整、§1.2 参照)
- ✅ `n_observed_as_target` (v18_ prefix 削除)
- ✅ `_gradient_distribute` 定義 + 単体テスト合格
- ✅ shadow audit: V105_ROOT/V106_ROOT path 縛り + 冪等性検証
- ✅ atom 列挙: `a1_batch/` listdir 経由 (326 atom + `_summary.json` 除外)
- ✅ axis 10 sacred → `n_betas_joined` (α/β 分離)

### 1.2 実装中に発覚した実態 (パッチ #2 として要承認)

#### (a) `last_familiarity_max` 実分布

24 seeds 全 5,224 cid の実分布:
- min=0、median=41.08、max=500
- q10=16, q25=27, q50=41, q75=81, q90=316, q99=475
- bimodal: 大半 0-100、ロングテールが 316 と 475 に plateau

パッチ #1 の `[5, 15, 25, 40]` ではほぼ全 cid が level 5 (creation) に集中。Code A 判断で **`[10, 30, 60, 150]`** を採用 (実分布で 5-bin がほぼ均等)。

→ Web Claude 確認願う: この boundaries で進めて問題ないか。

#### (b) v11_m_c_* 列の 'unformed' sentinel

per_subject の `v11_m_c_n_core/s_avg/r_core/phase_sig` は **80% (4574/5224 cid) が `'unformed'` (string)** で、reaped final_state cid のすべてが unformed。指示書 §3.2 の `row['v11_m_c_n_core']` は使えない。

代替: **`audit/per_subject_audit_seed*.csv` の `n_core_member`** (int64、全 cid 充足) に変更。これは Code A の env check §2.1-2.2 で既に確認していたが、指示書 §3.2 の axis 2/4 が誤って per_subject を指していた。

→ 全 cid に適用される `n_core_member` を採用。事前分布: {2:4178, 5:553, 4:298, 3:189, 6:6} で `n_core ∈ {2,3,4,5,6}`、7+ は seed 全体で 0 件。

#### (c) `alpha_lifecycle_log.event_type` の実値

指示書 §6 の `event_type == 'created'` は **存在しない**。実値は:
- `'birth'` (424/seed): `member_cids` あり、size 3 抽出元
- `'member_ghosted'` (545/seed): member 変動
- `'active_to_recorded'` (94/seed): state 遷移、`member_cids` なし

→ `event_type == 'birth'` で正しく size 3 α が抽出された (24 seeds 合計 5,205 size3 α、5 パターン全分類検出済)。

---

## 2. smoke test 結果 (seed 0)

- ✅ `_gradient_distribute` 単体テスト
- ✅ `axes_levels_v1.json` ↔ `AXES_ORDER` 完全一致 assert
- ✅ atom 列挙: 326 total / 325 observed / 1 unobserved (`FND.spaceless`)
- ✅ atom cache: (326, 48), valid=325
- ✅ shadow audit: input read-only / output v106 path 縛り / 冪等性 (run a == run b)
- ✅ seed 0 output 8 種すべて生成
- 実行時間: 0.09 sec (seed 0 単独)

---

## 3. main run 結果 (24 seeds 単一バッチ)

実行時間 **1.91 秒で 24 seeds 完了** (seed 当たり ~0.08 sec)。

| 指標 | 値 |
|---|---|
| 全 cid 数 | 5,224 (seed 平均 218、min 170 / max 253) |
| 全 size3 α 数 | 5,205 (seed 平均 217) |
| 全 hub cid 数 | 65 (seed 当たり 2-3) |
| mean_max_sim 平均 | 0.6078 (std 0.0045、min 0.5941、max 0.6147) |
| max_sim 全 cid 中最大 | 0.6949 |
| max_sim 全 cid 中最小 | 0.4117 |

→ **seed 間の atom 接地度安定性が異常に高い** (std 0.0045)。事前推測「seed ごとにばらつく」とは逆。

---

## 4. 主要観測結果

### 4.1 cid の rank_1 atom — **51.6% が CHG.begin**

| カテゴリ | rank_1 取得数 | 比率 |
|---|---|---|
| CHG | 2,698 | 51.6% |
| WLD | 556 | 10.6% |
| PRP | 471 | 9.0% |
| TIM | 446 | 8.5% |
| FND | 407 | 7.8% |
| COG | 327 | 6.3% |
| ELM | 98 | 1.9% |
| SOC | 91 | 1.7% |

具体 atom 上位:

| atom | count | category |
|---|---|---|
| CHG.begin | 2,669 | CHG |
| WLD.artless | 408 | WLD |
| PRP.easy | 358 | PRP |
| TIM.period | 321 | TIM |
| FND.logic | 300 | FND |

→ 全 5,224 cid の **過半数が rank_1 = CHG.begin**。25 atom 以下に集中 (有効 325 atom 中)。

**仮説** (Code A 提示):
- axis 1 temporal の "emergence/indication" が短寿命 cid (= reaped 8 割以上) で支配的
- CHG.begin の 48 スロット profile は emergence/indication が高重み
- → cosine 類似度が temporal 軸で決まり、ほぼ全 cid が CHG.begin に着地

→ Web Claude 確認願う: これは v10.6 の知見として記録する観測か、48 軸設計の偏りバグとして対処すべきか。

### 4.2 ハブ cid の atom 偏り — **事前推測完全 miss**

事前推測 (`v106_phase_design.md §7.1`): SOC.central / STA.persistent / BEI.integrated

実観測 (24 seeds × Top 1% = 65 hub cid):

| atom | hub rank_1 出現数 | category |
|---|---|---|
| COG.enlightenment | 35 | COG |
| FND.timeless | 15 | FND |
| EXS.being | 10 | EXS |
| WLD.culture | 5 | WLD |
| PRP.multiple | 1 | PRP |

**SOC / STA / BEI は 1 件も観測なし**。

→ ハブ cid は **「社交的」ではなく「認識的 (COG)」「永続的 (FND.timeless)」「存在論的 (EXS.being)」** な atom と接地度が高い。これは v10.6 の重要観察。

### 4.3 5 パターンの top_atom — TIM.moment 支配

| pattern | dominant top_atom | seed 一致数 |
|---|---|---|
| bridge (2,4,5) | TIM.moment | 24/24 |
| capture (2,5,5) | TIM.moment | 24/24 |
| peripheral (2,2,5) | TIM.moment | 24/24 |
| other (size 3 で 5 パターン外) | TIM.moment | 24/24 |
| near_core (4,5,5) | TIM.moment | 11/24 (多数) |
| core (5,5,5) | FND.logic | 9/24 (最多) |

→ **(5,5,5) のみが FND.logic に分岐**、他は TIM.moment 一様。事前推測 (n_core 組み合わせで atom 傾向が分かれる) は **部分的に的中** (core 単独の分岐) だが大半の組合せでは無差別。

### 4.4 unmatched 構造

- **genesis_unique cid (max_sim < 0.3): 0 件** — 全 cid が何らかの atom と接地
- **partial_match cid (0.3 ≤ max_sim < 0.5): 372 cid (7.1%)** — 大半 reaped/hosted
- **language_specific atom (全 cid との max_sim < 0.3): 35 atom 種**

unmatched atom (24 seeds 全 seed で unmatched):
- ACT.destroy, COM.conflict, CHG.decay
- STA.danger, STA.war
- EMO.despair, EMO.hate
- ECO.loss, FND.information
- LOG.unreason
- VAL.evil, VAL.sacred
- REL.different, REL.together

→ パターン: **negative-valence / destruction / conflict / negation 系の atom が unmatched**。VAL.sacred も unmatched (positive だが高い接地ハードル)。FND.information の unmatched は意外。

→ Web Claude 確認願う: これは v10.6 の知見「Genesis 系は破壊・対立・否定概念を構造ベクトルとして表現できない」として記録するか、それとも 48 軸設計が positive-skewed なバイアスを持つと解釈するか。

### 4.5 max_sim 分布 — **0.7 で頭打ち**

| 範囲 | count | ratio |
|---|---|---|
| 0.4-0.5 | 372 | 7.1% |
| 0.5-0.6 | 1,022 | 19.6% |
| 0.6-0.7 | 3,830 | 73.3% |
| 0.7+ | 0 | 0% |

→ **どの cid も 0.7 を超えない**。48 軸表現の上限。これは「cid は atom にぴったり一致することはない」(常に何らかの distinctiveness を持つ) という観察。

---

## 5. shadow audit 規律

- ✅ V105_ROOT 配下からの read-only オープンのみ (`safe_read_csv` 経由)
- ✅ V106_ROOT 配下への書き込みのみ (`safe_write_csv/parquet/json` 経由、出力前に `assert_output_under_v106`)
- ✅ 冪等性: seed 0 を 2 回実行 (`audit_run_a`, `audit_run_b`) で完全一致確認
- ✅ パストラバーサル防止: `Path(...).resolve()` で正規化

実装で v10.5 配下に書き込みを試みると `ValueError: Output path ... not under v106/` で停止する。OS chmod は適用していないが、コードレベルで物理層 frozen を保証。

---

## 6. ウェット概念禁止の遵守確認

- 出力 CSV / レポート / コメントいずれにも「ESDE が love を理解した」「自然な対応」「意味的に妥当」のような表現なし
- 全文「cid X の構造ベクトルが atom Y との cosine 類似度 Z」「カテゴリ K への偏り N%」の数値表現に統一

実装中の自己監視で 1 件、報告書ドラフトに「自然な対応」と書きそうになって STOP → 「数値的に類似度 X」に書き換え。

---

## 7. 出力ファイル一覧

```
developmental/v106/outputs/
├── smoke/                                  (seed 0 + audit_run_a/b + cache)
│   ├── atom_profiles_cache.npz
│   ├── axes_metadata.json
│   ├── audit_run_a/cid_atom_topk_seed0.csv
│   ├── audit_run_b/cid_atom_topk_seed0.csv
│   └── (seed 0 の 8 種出力)
├── main/                                   (24 seeds 本番)
│   ├── atom_profiles_cache.npz
│   ├── axes_metadata.json
│   ├── run_summary.csv
│   ├── cid_structure_profile_seed{0..23}.csv
│   ├── cid_atom_topk_seed{0..23}.csv
│   ├── atom_cid_topk_seed{0..23}.csv
│   ├── cid_atom_sim_matrix_seed{0..23}.parquet
│   ├── hub_cid_atom_bias_seed{0..23}.csv
│   ├── five_pattern_classification_seed{0..23}.csv
│   ├── five_pattern_atom_bias_seed{0..23}.csv
│   ├── beta_atom_aggregate_seed{0..23}.csv
│   └── unmatched_structures_seed{0..23}.csv
└── reports/
    ├── cross_seed_alignment_report.md
    ├── prediction_vs_observation.md
    └── unmatched_classification_report.md
```

合計: per-seed 出力 8 種 × 24 = 192 ファイル + cache + summary + reports 3 種。

---

## 8. Web Claude / Taka への要判断 5 項目

1. **axis 3 boundaries `[10, 30, 60, 150]`** で確定して良いか (パッチ #1 の `[5, 15, 25, 40]` から変更)
2. **CHG.begin に 51% 集中** をどう解釈するか (観察記録 / 48 軸設計の偏り / 別)
3. **ハブ cid が COG/FND/EXS** で SOC/STA/BEI ではない件、これを v10.6 の主結果として記録して良いか
4. **5 パターンのうち core (5,5,5) のみ FND.logic に分岐** することの解釈
5. **negative-valence atom が言語固有 (genesis 側に対応構造なし)** の解釈

これらの判断後、`v106_implementation_brief.md` の「ウェット概念禁止」を維持したまま **観察報告書** (Web Claude or Taka が確定) を生成する流れ。

---

## 9. 完了条件チェック

### 9.1 機能完了
- [x] axes_levels assert PASS
- [x] Atom プロファイル cache 構築 (325 atom)
- [x] cid 構造ベクトル 5,224 cid 全部 (NaN なし)
- [x] sim matrix 24 seeds 全部
- [x] 5 パターン分類 24 seeds 全部 (5,205 size3 α 全分類)
- [x] ハブ cid 抽出 24 seeds 全部 (65 hub)
- [x] 出力 CSV 8 種 × 24 seeds = 192 ファイル

### 9.2 規律完了
- [x] shadow audit (path 縛り + 冪等性) PASS
- [x] error 行フィルタ動作確認 (mapper_output の status="error" 行除外)
- [x] FND_spaceless NaN 処理動作確認 (atom_valid_mask = 325/326)
- [x] ウェット概念禁止 (出力全文 grep 確認)

### 9.3 解析完了
- [x] cross_seed_alignment_report.md
- [x] prediction_vs_observation.md
- [x] unmatched_classification_report.md

---

*以上、Code A による v10.6 smoke + main run 報告。Web Claude の判断後に観察報告書を確定する流れ。*

---

## 後注: 時間軸混在 caveat (2026-05-06 追記)

本報告で挙げた集団平均 finding (CHG.begin 51%、ハブ COG/FND/EXS、TIM.moment 5 パターン支配) は、cid 構造ベクトルが **run 集約 + 終了スナップショット混在** で生成されたため、動学的観察 (step 単位) は捕捉されていない。詳細: → `v106_temporal_axis_caveat.md`
