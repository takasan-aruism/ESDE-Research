# v10.12 Step A 認識確認 (再実施、第 5 版主題ベース)

*作成*: 2026-05-11、Code A
*親*: `v112_phase_design.md` 第 5 版 + `v112_implementation_brief.md` 第 4 版 (Web Claude 2026-05-11)
*対象*: Web Claude (即決事項返答へ)、Taka (承認)
*目的*: 第 4 版主題廃止 + 第 5 版主題 (Atom 取り込み prototype) 移行への認識確認再実施、Q-A1〜Q-A12 + DC-A1〜DC-A5 全件回答 + Step B 補完 (cond4 top 50% 母集団実測) 含む
*履歴*: 第 4 版主題ベース認識確認 (commit ddd595a) は廃止、本書で再実施

---

## 0. 一文サマリ

第 4 版主題 (条件適応型 atom 導入の単一勝負案 2 trial 分割) は廃止、第 5 版主題 (Atom 取り込み prototype、v10.6 §7.1 で本来予定の主題への復帰、v10.11 §5.1 直接の出発点) に移行、Step A を再実施、Step B 補完で **cond4 top 50% 母集団を実測し per seed mean 17.50 / 24 seeds total 420 / min 13 / max 23 / < 3 events seeds 0/24 / < 5 events seeds 0/24 で母集団境界状態が完全解消** (第 4 版 top 25% の 105 events から 4 倍改善)、Q-A1〜A3 (再): 第 4 版廃止 + 第 5 版移行 + familiarity γ 扱い を理解、Q-A4: cond4 top 50% は Step B 既存出力から派生実測済、Q-A5: 単一構造化で命名 v112 + v108_standard の 2 種、Q-A6: 波及プロファイルは per-event で算出後 n_core_bin / formation_relation で groupby 層化集計、Q-A7: 3 段階判定廃止 + observation_records.json で観察事実 + 留保事項記録方式を提案、Q-A8-A11: main run 推定 約 1 分 / storage 累計 1.7-1.8 GB (28-30%) / メモリ peak ~5-6 GB、Q-A12: 規律 §35 #9 #10 + §34 #37 + §5.5 案 X + 規律 42 候補 (上位完了レポート §5 必読) 全遵守、DC-A1 (再): top_50_threshold per-seed 採用 (std/mean=0.06 で全体共通も技術的に可能だが第 5 版主題明示で per-seed)、DC-A2 (再): cond4 top 50% で母集団完全解消で対応不要、DC-A3 (再): v108_standard は v10.8 既存出力流用 (層 B 不変)、DC-A4 (再): observation_records.json 形式は Code A 提案で §3.7 で具体化、Step B' (補完実測) 完了済 + 認識確認再実施完了で Step C (実装着手) 進行準備完了、ただし主題変更直後のため Web Claude/Taka 即決事項返答 + Taka 承認後に Step C 着手。

---

## §1 第 5 版主題への認識確認 (Q-A1-A3 再実施)

### 1.1 Q-A1 (再): 第 4 版主題廃止 + 第 5 版移行の理解

**理解の確認**:
- 第 4 版主題「条件適応型 atom 導入の単一勝負案 2 trial 分割」は **廃止**
- 第 4 版の Step Z 結果 + Step B 結果 + 第 4 版主題ベース Step A (commit ddd595a) は **参照のみ**
- 第 4 版固有の判断 (trial-B 不実施、cond4 top 50% 緩和提案、2 trial 分割設計、3 段階成功判定) は **第 5 版で適用しない**
- 第 5 版主題「Atom 取り込み prototype (人間言語 → atom 変換)」を独立した主題として実装

→ **理解 OK**、第 4 版固有判断を第 5 版に持ち込まない。

### 1.2 Q-A2 (再): v10.11 完了レポート §5.1 直接の出発点

**確認**:
- v10.11 完了レポート §5.1: 「v10.12 主題 = 人間言語 → atom 変換 prototype (Atom 取り込み prototype) に戻る (Taka 確定)」
- 第 5 版主題はこれを直接の出発点とする (v10.6 §7.1 で本来予定された主題への復帰)
- 第 4 版 Web Claude は §5.1 を見落として独自設計 (条件研究の延長) → 第 5 版で修正、規律 42 (候補) 「上位完了レポート §5 必読」で再発防止

→ **確認 OK**、v10.11 §5.1 を第 5 版主題の出発点として認識。

### 1.3 Q-A3 (再): familiarity γ (緩め仮置き) 扱いの理解

**理解の確認**:
- 第 4 版で cond4 = familiarity top 25% (厳格適用) → 第 5 版で cond4 = top 50% (緩め)
- 「関連ぽさを残す」程度の扱い (Taka 整理 (γ)、2026-05-11)
- familiarity の厳密研究 (高/低 並行観察等) は **v10.13 以降の別主題候補**、本主題では実施しない
- 留保 25 (familiarity 閾値選定の意味) として記録、深追い禁止

→ **理解 OK**、familiarity を研究対象にしない。

---

## §2 Step B 補完: cond4 top 50% 母集団実測

### 2.1 実測値 (Step B 既存出力から派生)

| 指標 | 第 4 版 (top 25%) | **第 5 版 (top 50%)** | 倍率 |
|---|---:|---:|---:|
| per seed mean | 4.38 | **17.50** | 4.0 倍 |
| per seed std | 2.89 | **2.93** | - |
| per seed min/max | 0 / 10 | **13 / 23** | - |
| 24 seeds total | 105 | **420** | 4.0 倍 |
| < 3 events seeds | 9/24 | **0/24** ✓ |
| < 5 events seeds | 14/24 | **0/24** ✓ |
| < 10 events seeds | - | **0/24** ✓ |

→ **母集団境界状態が完全解消**、全 seed で paired_d / sign_test 信頼ライン (>= 10 events) クリア。

### 2.2 top_50_threshold per-seed の値 (DC-A1 (再))

| 統計 | 値 |
|---|---:|
| per-seed mean | 41.40 |
| per-seed std | **2.43** |
| std / mean ratio | **0.06** |
| per-seed min | 38.84 |
| per-seed max | 48.48 |

→ top 50% (= median) の seed 間ばらつきは非常に小 (std/mean = 0.06、≪ 0.10)。技術的には全体共通 (global) も成立するが、**第 5 版主題で per-seed 採用が明示** + Step B 既存規約継承で per-seed 採用。

### 2.3 母集団の seed 別分布

per seed events 数の分布:
- min: 13 (seed 11, 16, 11), max: 23 (seed 6, 13, 17, 21)
- 全 24 seeds で >= 13 events を確保
- Q1: ~15, Q2: ~17, Q3: ~20

→ paired_d 算出が **全 seed で技術的に可能**、bootstrap CI (n_iter=1000) も信頼性確保。

### 2.4 出力ファイル

`developmental/v112/outputs/step_b/cond4_top50_population.parquet` (24 rows、per seed 値)

---

## §3 Q-A4-A12 への回答

### 3.1 Q-A4: cond4 top 50% 母集団 (Step B 既存出力からの派生 / 新規計算)

§2 で実測完了。**Step B 既存出力 (`fam_top_quartile_per_seed.parquet` 等) からの派生可能**、新規計算は per-seed top_50_threshold (= median) の算出のみ。第 5 版 Step B' (補完実測) として Step B 既存出力ベースで完了済 (約 5 秒)。

### 3.2 Q-A5: 単一構造化での命名規則

第 4 版の 6 種 (2 trial × 3 condition) → 第 5 版の 2 種に簡素化:

```
developmental/v112/outputs/main/
├── atom_introduction_events_v112_seed{N}.parquet        (v112 主観察対象)
├── atom_introduction_events_v108_standard_seed{N}.parquet (v108 副次比較対象)
├── baselines_with_delta_v112_seed{N}.parquet
├── baselines_with_delta_v108_standard_seed{N}.parquet
├── excess_change_adjusted_v112_seed{N}.parquet
├── excess_change_adjusted_v108_standard_seed{N}.parquet
└── propagation_profile_seed{N}.parquet                  (波及プロファイル)
```

→ 2 condition × 24 seeds × 4 種 (events, baseline, excess, profile) = 192 files (per-seed)
→ + cross_seed 集計 5-7 files

v10.10 規約継承、命名は `{kind}_{condition_id}_seed{N}.parquet`。

### 3.3 Q-A6: 波及プロファイル算出 + 層化集計の実装

**実装方針**:

```python
# v112_propagation_analyzer.py
def compute_propagation_profile(events_df, esde_state, baseline_dfs):
    """per-event で波及プロファイル算出後、層化集計."""
    rows = []
    for _, event in events_df.iterrows():
        # 主観察指標 (per event)
        row = {
            "seed": event.seed,
            "atom_id": event.atom_id,
            "source_cid": event.source_cid,
            "target_step": event.timestamp,
            "delta_C_medium": compute_delta_C(event, window=200),
            "delta_Q_medium": compute_delta_Q(event, window=200),
            "n_pulses_short": compute_n_pulses(event, window=50),
            "path_familiarity_excess": compute_path_excess(event, "familiarity"),
            "path_attention_excess": compute_path_excess(event, "attention_via_salience"),
            "path_temporal_excess": compute_path_excess(event, "temporal_coactivation"),
            "path_integration_excess": compute_path_excess(event, "integration_alpha"),
            # 層化軸 (cid 属性、source_cid から取得)
            "n_core_bin": classify_n_core_bin(event.source_cid, esde_state),
            "formation_relation": classify_formation_relation(event.source_cid, event.timestamp, esde_state),
        }
        rows.append(row)
    return pd.DataFrame(rows)

# 集約 (cross_seed/)
def aggregate_by_n_core_bin(profile_df):
    return profile_df.groupby(["n_core_bin"]).agg({
        "delta_C_medium": ["mean", "std", "median", "count"],
        "n_pulses_short": ["mean", "std", "median", "count"],
        # ...
    })

def aggregate_by_formation_relation(profile_df):
    return profile_df.groupby(["formation_relation"]).agg({...})
```

主観察指標 (per-event):
- delta_C / delta_Q in medium window (200 step)
- n_pulses in short window (50 step)
- 4 経路別 excess (familiarity / attention / temporal_coactivation / integration_alpha)

層化軸:
- n_core_bin (bin_2 / bin_3_4 / bin_5+) ← 規律 §34 #37 遵守、ただし cond3 で bin_5+ に絞られているため bin_2/3_4 は空または ごく少数の例外的 cid
- formation_relation (before_formation / no_alpha / after_formation_*) ← cond1 で before/no_alpha に絞られているため after_* は空または例外的

注: 主題ドキュメント §11 で「n_core 別層化 + formation_relation 別層化」が達成項目 (#8, #9) だが、cond3/cond1 で絞り込み済のため層化は実質 1 cell に集中する。観察事実として記録 (留保事項 26 候補)。

### 3.4 Q-A7: 3 段階判定廃止 + observation_recorder の実装

**第 5 版方針**: Aruism「予想と違えば再観察」(v10.11 §5.2 末尾) を採用、3 段階成功判定 (Full/Partial/Failure) は置かない。

**observation_recorder.py 実装提案**:

```python
# v112_observation_recorder.py
def record_observation(propagation_profile, v108_comparison, expectations):
    """観察事実 + 留保事項を JSON で記録."""
    records = {
        # 観察事実
        "main_run_completed": True,
        "n_seeds_processed": 24,
        "n_atoms": 25,
        "n_v112_events_total": int(propagation_profile["seed"].count()),
        "n_v108_standard_events_total": ...,
        
        # 波及プロファイル (主観察、集約値)
        "v112_propagation_summary": {
            "delta_C_medium_mean": ...,
            "delta_C_medium_std": ...,
            "n_pulses_short_mean": ...,
            "path_familiarity_excess_mean": ...,
            ...
        },
        
        # 層化観察
        "by_n_core_bin": {...},
        "by_formation_relation": {...},
        
        # v108 副次比較
        "v108_comparison_cohens_d": {...},  # 参考値、主軸ではない
        
        # 予想との比較 (事前予測と実観察)
        "expectations_vs_observation": [
            {"expectation": "target_cid pool が確保される", "observed": True, "value": 420},
            {"expectation": "波及プロファイルが算出される", "observed": True},
            {"expectation": "v10.8 比較で何らかの差が出る", "observed": ..., "value": ...},
        ],
        
        # 留保事項 (新規発生 + 継承)
        "reservations_new": [
            {"id": 26, "title": "層化集計が cond1/cond3 絞り込みで実質 1 cell に集中する",
             "evidence": "n_core_bin の bin_2/3_4 は空、formation_relation の after_* は空",
             "future_subject": "v10.13 以降で n_core 軸 / formation 軸を観察対象とする主題候補"},
            ...
        ],
        "reservations_inherited": [22 件 from v10.9-v10.11 + 23-25 from v10.12 Step Z-B],
    }
    return records
```

→ 「成功か失敗か」の二項判定ではなく、観察事実 + 留保事項を **網羅的に記録** する形式。Web Claude/Taka が観察結果を読んで v10.13 主題候補を判断する素材として機能。

### 3.5 Q-A8: 曖昧/不足な箇所

| 項目 | 質問 | Code A 提案 |
|---|---|---|
| top_50_threshold per-seed の値 | per-seed median を採用するか、別の閾値か | per-seed median = top 50% で確定 (本 Step A 再実施で実測完了) |
| 層化集計の空 cell の扱い | n_core_bin で bin_2/3_4 が空のセルをレポートにどう記載するか | observation_records.json で「n_pairs=0」として明示記録 |
| v108_standard 比較の対象 cid pool | v108 既存 top_k 100 cid (atom 別) を流用するか、第 5 版で別 pool を抽出するか | v108_standard 既存出力流用 (DC-A3 (再)) |
| atom 別の独立評価 | 25 atom 別に主観察を出すか、25 atom 集約のみか | per-atom + 集約の両方を records.json で記録 |

→ 上記 4 件は Code A 提案で進める前提、Web Claude/Taka が異なる方針なら指示要請。

### 3.6 Q-A9: main run 計算時間 (第 4 版から再見積もり)

第 4 版予測 1-2 分 (6 conditions × 6 baselines = 36 baseline) → **第 5 版で約 1 分** (2 conditions × 6 baselines = 12 baseline、events 数も少):

| 区分 | 値 |
|---|---:|
| v112 events 24 seeds total | ~10,500 (420 cid × 25 atom) |
| v108_standard events | 60,000 (既存) |
| 合計 events | ~70,500 |
| baseline 計算 | 2 cond × 6 baseline × 24 seeds = **288 baseline runs** |
| main run 推定時間 | **30-60 秒** (24 並列、v10.10 main 103.67 秒の 7% 規模) |
| propagation_analyzer 推定時間 | 約 10 秒 (per-event 軽量計算) |
| **総 main run 時間** | **約 1 分** |

→ §0.3 打ち切り条件 30 分超に大幅余裕。

### 3.7 Q-A10: storage 累計予測

| 区分 | サイズ |
|---|---:|
| per-seed v112 (atom_events + baseline + excess + profile) | ~8 MB |
| per-seed v108_standard | ~7 MB |
| per-seed 計 | ~15 MB |
| 24 seeds | **~360 MB** |
| + cross_seed (集計 + records.json) | ~10 MB |
| **v10.12 main 合計** | **~370 MB** |
| 累計 v107-v112 | **~1.9 GB / 上限 6 GB (32%)** |

→ 打ち切り条件 50% に大幅余裕。

### 3.8 Q-A11: メモリ peak

24 seeds 並列実行:
- per-worker ~200-250 MB (v10.10 実測ベース、events 数縮小で減)
- 24 workers × 230 MB = **~5.5 GB peak**
- ESDE 環境 (Threadripper) で十分

### 3.9 Q-A12: 規律遵守自己検証

| 規律 | 状態 |
|---|---|
| **§35 #9 (主題着手前に上位資料を読む)** | 第 5 版主題 + 第 4 版実装指示書 + v10.6 §7.1 + v10.10 §3, §9.3 + v10.11 §1.1, §5.1 + v10.5 §7 + v10.7 §87 + v10.8 §6.8 を読了 |
| **規律 42 (候補、上位完了レポート §5 必読)** | v10.11 完了レポート §5.1 を第 5 版主題の出発点として認識 (§1.2) |
| §35 #10 (観察できる軸を駆動要因にしない) | 駆動要因 = 「Atom 取り込み prototype の動作確認」、観察軸列挙なし |
| §34 #37 (n_core 別層化必須) | 主題 §11 #8 で層化集計、ただし cond3 で bin_5+ 絞り込み済のため層化は実質 1 cell 集中 (留保 26 候補で記録) |
| GPT B6 (各変動条件で baseline 再計算) | 2 condition × 6 baseline で再計算する設計 |
| §5.6 規律チェックリスト (案 X) | 第 5 版主題 §5.5 で実装、本書 §6 で再確認 |
| 物理層 frozen | post-process 計算的減算のみ、ledger 不変 |
| 神の手回避 | 4 条件 (cond1-4) で構造的判定、ハンドチューニングなし |
| Atom 326 絶対化禁止 | 25 atom 継承 (v10.6 確立) |
| 因果断定回避 | 「波及観察」「字面に揺れながら反応」を使用、「効いた」「効果」は使わない |

→ **全項目遵守**。

---

## §4 即決事項候補 (DC-A1-A5、再回答)

### DC-A1 (再): top_50_threshold per-seed vs 全体共通

**Code A 提案**: **per-seed 採用** (Step B 規約継承 + 第 5 版主題明示)

実測値:
- per-seed std/mean = 0.06 (≪ 0.10)
- 技術的には全体共通も成立 (mean 41.40 ± 2.43)
- ただし第 5 版主題で per-seed 明示 + Step B (top 25%) で per-seed 採用済 → 一貫性維持

### DC-A2 (再): cond4 top 50% で母集団不足時の対応

**Code A 提案**: **対応不要**

実測で全 24 seeds が >= 13 events 確保、< 5 events seeds = 0/24 で母集団境界状態は完全解消。Web Claude/Taka 上申不要。

### DC-A3 (再): v108_standard 比較 main run 同時 vs 既存出力流用

**Code A 提案**: **既存出力流用** (層 B 不変維持)

- v108 atom_introduction_events / baselines / excess は v10.8 main で生成済
- 第 5 版で再計算すると層 B (v108 出力不変) が崩れるリスク
- 流用なら層 B PASS 確実 + 計算時間節約

ただし v108_standard の cid pool は v10.8 既存 top_k_100 cid (全 n_core 含む)、第 5 版 v112 と n_core 構造が異なる。比較は副次として参考値の扱い。

### DC-A4 (再): observation_records.json 形式詳細

**Code A 提案**: §3.4 で具体化、Web Claude 確認後に確定

提案項目:
- 観察事実 (main_run_completed / n_events / 波及サマリ / 層化観察)
- v108 副次比較 (cohens_d 参考値)
- 予想との比較 (事前予測リスト + 観察結果)
- 留保事項 (新規 + 継承)

Web Claude が異なる形式を望めば指示要請。

### DC-A5 (再): その他

特になし。Code A 判断で進める範囲:
- top_50_threshold per-seed の派生実測 (本書 §2 で完了)
- 層化集計の空 cell 扱い (n_pairs=0 として記録)
- atom 別 vs 集約の両方記録

---

## §5 Step C 進行案 (DC-A1〜A5 承認後)

```
Step Z: 完了済 (commit df04d0a)
Step B: 完了済 (commit 9d755ec)
Step A (再): 完了済 (本書)、Step B 補完 (cond4 top 50%) も完了済
   ↓ Web Claude/Taka 即決事項返答 + Taka 承認
Step C: receptive_cid_detector_v112 + atom_event_generator 実装 + smoke (seed 0)
   ↓
Step D: baseline_recalculator + propagation_analyzer 実装 + smoke (seed 0)
   ↓
Step E: observation_recorder 実装 + smoke
   ↓
Step F: orchestrator smoke (seed 0、bit-identity 層 A 検証)
   ↓
Step G: smoke 完了報告 → main run 判定要請
   ↓
Step H: main run (24 seeds × 2 conditions、約 1 分)
   ↓
Step I: cross-seed 集計 + 層化観察 + v108 副次比較
   ↓
Step J: 主題完了報告 (observation_records.json + 留保事項リスト)
```

→ 第 4 版 12 段階から 10 段階に簡素化 (Step Z + Step B + Step A 再 + Step C-J)。

---

## §6 規律遵守の自己検証 (実装指示書 §6.3)

| 規律 | 確認 |
|---|---|
| §35 #9 (上位資料読了) | ✓ 第 5 版主題 + 第 4 版指示書 + v10.6 §7.1 + v10.10 §3, §9.3 + v10.11 §1.1, §5.1 + v10.5 §7 + v10.7 §87 + v10.8 §6.8 を読了 |
| §35 #10 (観察軸を駆動要因にしない) | ✓ 本書で観察軸増加提案なし、駆動要因 = Atom 取り込み prototype |
| §34 #37 (n_core 別層化必須) | ✓ 主題 §11 #8 で層化、cond3 絞り込みによる実質 1 cell 集中は留保 26 候補で記録 |
| §5.5 規律チェックリスト (案 X) | ✓ 主題 §5.5 で全項目確認、本書 §3.9 で Code A 視点再確認 |
| 規律 42 (候補、上位完了レポート §5 必読) | ✓ v10.11 §5.1 を第 5 版主題出発点として §1.2 で参照証明 |
| 物理層 frozen | ✓ post-process 計算的減算、ledger 不変 |
| 神の手回避 | ✓ 4 条件で構造的判定 |
| Atom 326 絶対化禁止 | ✓ 25 atom 継承 |
| 因果断定回避 | ✓ 波及観察 / 字面反応 表現 |
| 完全マージ版文書 | ✓ 本書 + 主題ドキュメント第 5 版 |

事前調査の規律遵守:
- [x] Step Z で実装に進まなかった (commit df04d0a)
- [x] Step B で実装に進まなかった (commit 9d755ec)
- [x] 第 4 版 Step A で重大ブロッカー警告のみ (commit ddd595a、廃止)
- [x] 主題変更を受け入れて第 5 版 Step A を再実施 (本書)
- [x] 観察軸を増やす方向への転換提案なし
- [x] 母集団不足 (第 4 版懸念) は cond4 top 50% で構造的解消、独自緩和実装なし

---

## §7 留保事項 (新規発生候補)

### 留保 26 (候補): 層化集計の cond1/cond3 絞り込みによる実質 1 cell 集中

**観察候補**:
- 主題 §11 #8 で n_core 別層化 (bin_2 / bin_3_4 / bin_5+) を達成項目に置くが、cond3 (n_core ≥ 5) で **bin_5+ のみ** に絞り込み済
- bin_2 / bin_3_4 は cond3 で除外 → 層化集計の bin_2/3_4 セルは空
- 同様に formation_relation (before/no_alpha/after_*) で cond1 が before/no_alpha に絞り込み → after_* は空

**意味の留保**:
- 第 5 版主題は v10.10 §3.4 反応 type 分業 (bin_5+ = delta_C) を踏まえた設計、bin_5+ 集中は意図的
- 層化集計の「空セル」を観察事実として記録するか、本主題では集計対象外とするか
- v10.13 以降で n_core 軸 / formation 軸を観察対象とする主題が立てば再評価

**Code A 判断**: 本主題では bin_5+ × before/no_alpha のみが実質観察対象、空セルは記録のみ深追いしない。

---

## §8 一文サマリ (再掲)

第 4 版主題廃止 + 第 5 版主題 (Atom 取り込み prototype、v10.11 §5.1 直接出発点) への移行を受けて Step A 認識確認を再実施、Step B 補完で **cond4 top 50% 母集団を実測し per seed mean 17.50 / 24 seeds total 420 / min 13 / max 23 / < 5 events seeds 0/24 で第 4 版 top 25% の 105 events から 4 倍改善し母集団境界状態が完全解消**、Q-A1-A3 (再) で第 4 版廃止 + 第 5 版移行 + familiarity γ 扱いを理解、Q-A4 で cond4 top 50% 実測完了 (Step B 既存出力派生)、Q-A5 で命名規則 2 種 (v112 + v108_standard)、Q-A6 で波及プロファイル per-event 算出後 n_core_bin / formation_relation で groupby 層化集計を提案、Q-A7 で 3 段階判定廃止 + observation_records.json で観察事実 + 予想との比較 + 留保事項を網羅記録する Aruism 整合方式を提案、Q-A8 で曖昧箇所 4 件 (top_50_threshold per-seed / 空 cell 扱い / v108 cid pool / atom 別 vs 集約) は Code A 提案で進める前提、Q-A9 main run 約 1 分 (288 baseline runs)、Q-A10 storage 約 370 MB / 累計 1.9 GB (32%)、Q-A11 メモリ ~5.5 GB peak、Q-A12 で規律 §35 #9 #10 + §34 #37 + §5.5 案 X + 規律 42 候補 (上位完了レポート §5 必読) 全遵守を確認、DC-A1 (再) top_50_threshold per-seed 採用 (std/mean=0.06 で全体共通も技術可だが第 5 版主題明示)、DC-A2 (再) cond4 top 50% 母集団解消で対応不要、DC-A3 (再) v108_standard 既存出力流用 (層 B 不変)、DC-A4 (再) observation_records.json 形式 §3.4 で具体化、DC-A5 (再) その他なし、留保 26 候補 (層化集計の cond1/cond3 絞り込みによる実質 1 cell 集中) を §7 で記録、Step Z + Step B + Step A (再) 完了で Step C (実装着手) 進行準備完了、Web Claude/Taka 即決事項返答 + Taka 承認後に Step C 着手、第 4 版で多発した「主題見直し → 規律違反警告」のループは第 5 版で構造的に解消されている (cond4 top 50% で母集団完全解消 + 主題が v10.11 §5.1 直接接続)。

---

*以上、Code A による v10.12 Step A 認識確認 (再実施、第 5 版主題ベース)。Web Claude/Taka 即決事項返答 (`v112_response_to_code_a_v2.md`) + Taka 承認後、Step C に進む。第 4 版 Step A 認識確認 (commit ddd595a) は廃止、本書で再実施。*
