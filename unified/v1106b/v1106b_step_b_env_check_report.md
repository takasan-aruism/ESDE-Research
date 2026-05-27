# v1106b Step B — 環境準備完了報告 + 開始 CID 選定代替案

**Date**: 2026-05-28
**Author**: Code A
**Status**: Step B 完了、Taka 代替案判断待ち

---

## 1. リソース存在確認 (すべて OK)

| リソース | 状態 |
|---|---|
| v1103 atom_centroids_48d_raw.parquet | ✓ 存在 |
| v106 axes_metadata.json | ✓ 存在 |
| v1106a verification_a_cid_word_alignment.parquet | ✓ 存在 |
| v105 per_subject (24 seeds) | ✓ 全 24 seeds 存在 |
| v106 cid_structure_profile (24 seeds) | ✓ 全 24 seeds 存在 |
| v106 cid_atom_sim_matrix (24 seeds) | ✓ 全 24 seeds 存在 |
| mapper_output | ✓ 325 files (FND.spaceless 欠落、設計通り) |

## 2. CID 物理量集約結果

- 全 CID 数: **5,224** (24 seeds 集約)
- 48d vec ありの CID: **5,224** (全件)

## 3. final_state × familiarity bin 分布 (実態)

bin 境界: low (< 10) / mid (10-50) / high (≥ 50)

per_seed 平均 CID 数:

| final_state | low | mid | high | 合計 |
|---|---:|---:|---:|---:|
| hosted | **0-1** (ほぼゼロ) | ~15 | ~20 | ~35 |
| ghost | **0** (ゼロ) | ~2 | ~3-5 | ~7 |
| reaped | ~10 | ~100 | ~65 | ~175 |

→ **hosted/ghost の familiarity low はそもそも CID がほぼ存在しない** (生存 / 消滅進行中で familiarity が低い CID は希少、ESDE 構造上の特性)。

## 4. Code A 提案 8 bin × 5 CID/bin での選定結果

| 指標 | 値 |
|---|---:|
| 目標 CID 数 | 960 (40/seed × 24) |
| 実際選定数 | **572** |
| 不足 | **388 (40.4%)** |
| 不足 bin 数 | 97 / 192 bins |

bin 別選定 CID 数:

| final_state | low | mid | high |
|---|---:|---:|---:|
| hosted | 4 | 120 | 120 |
| ghost | 2 | 44 | 47 |
| reaped | 115 | 120 | (対象外) |

→ **hosted low (4) / ghost low (2) が壊滅的不足**。実態が「CID 数ゼロ近い」のため、Code A 提案 bin では達成不可。

## 5. 代替案 (Code A 推奨順)

### 案 E (Code A 推奨): bin 再設計

**hosted/ghost の low を削除、reaped high を追加、ghost を per_seed 3 CID に減**:

| final_state | bin | per_seed CID |
|---|---|---:|
| hosted | mid | 5 |
| hosted | high | 5 |
| ghost | mid | **3** (CID 数限界) |
| ghost | high | 5 |
| reaped | low | 5 |
| reaped | mid | 5 |
| reaped | **high (新規追加)** | 5 |

**合計 7 bin × per_seed 33 CID × 24 seeds = 792 CID**

理由:
- ESDE 構造上、hosted/ghost で familiarity low は希少 (生存/消滅進行中で familiarity 低い CID は ESDE 内で存在しにくい)
- reaped high は per_seed 平均 65 個もあり余裕
- 実態に即した bin 構成、CID 数の安定性確保

### 案 A: 単純追加

reaped high を追加 (8 bin → 9 bin)、不足 bin は許容
- per_seed CID 数のばらつき大 (20-28、min/max 差大)
- 不足 bin 残存、構造観察の bin 間バランス崩れる

### 案 B: per_bin CID 数増加

5 CID → 7 CID 等
- hosted low / ghost low の枯渇は解決しない (CID 数ゼロには対処不可)
- bin 間ばらつきさらに拡大

### 案 C: 不足分を他 bin で補填

hosted low 不足 → ghost mid で補填 等
- bin 定義の意味が崩れる、構造観察の解釈困難

### 案 D: 目標を 572 に変更

Code A 提案 8 bin のまま、実数 572 で進行
- bin 間バランスが極端 (hosted low 4 vs reaped low 115)
- ghost low (2) で統計的に意味なし

## 6. Code A 推奨理由

**案 E を推奨**:
1. ESDE 構造の実態に即している (hosted/ghost low は構造上希少)
2. CID 数の安定性 (per_seed 33 ± 0、ばらつきほぼなし)
3. 各 bin 統計的に意味のある CID 数 (≥ 3)
4. 観察 1 の趣旨 (familiarity 多様性 × final_state) を維持
5. 目標 792 は Code A 認識確認 §3 想定実行時間 (10-20 分) に収まる

## 7. Taka 判断仰ぐ事項

1. **案 E 採用 OK か** (Code A 推奨)
2. 他案採用なら指示
3. ghost mid を per_seed 3 CID に減らすことの妥当性 (ghost mid は per_seed 1-3 で限界、3 CID 確保するため bin 全体の最小 CID 数の seed もある)

## 8. 代替案決定後の次ステップ

| Step | 内容 |
|---|---|
| (代替案決定後) Step B 再実行 | 選定 CID 確定、env_check_selected_cids.parquet 更新 |
| Step C | 観察 1 smoke (1 seed 33 CID × 15 turn = 495 turn、1-2 分) → pause + Web Claude 報告 |
| Step D | 観察 1 main (24 seeds × 33 CID × 15 turn = 11,880 turn、10-20 分) |

## 9. 出力ファイル

| ファイル | 内容 |
|---|---|
| `unified/v1106b/outputs/main/env_check_cid_props.parquet` | 全 5,224 CID 物理量 + fam_bin |
| `unified/v1106b/outputs/main/env_check_bin_counts.parquet` | seed × final_state × fam_bin の CID 数 |
| `unified/v1106b/outputs/main/env_check_selected_cids.parquet` | 現状 8 bin 案の選定結果 (572 CID、代替案決定で更新予定) |
| `unified/v1106b/outputs/main/env_check_underfill.parquet` | 不足 97 bin |

---

**Step B 報告 end. Taka 判断 (案 E 採用 or 他案) を待って次ステップ進行。**
