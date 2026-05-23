# v11.0.4a (v1104a) Step H' 観察事実最終報告 — Code A

*作成*: 2026-05-23、Code A
*親*: `v1104a_phase_design.md` (Web Claude 設計書 v2、2 AI 監査反映済) + `v1104a_step_a_recognition.md` (Code A 認識確認 + 確認要請 3 件 Web Claude/Taka 承認済) + Step B'-G' 出力
*対象*: Web Claude (Phase Result 統合担当、Step I) + Taka (主題評価)
*位置づけ*: v1104a 主題「CID/IID 内部動作点検 段階 2: 観察方法依存の整理と scope × 層化による再点検」の Code A 観察事実総括。**judgment 回避** (絶対格言 #12)、**判定語制限** (「連想」「成功/失敗」「意味がある/ない」を使わない、GPT 追加 4)、**selector 化禁止遵守** (追加調整 4、GPT 修正必須 D + 追加推奨 6)、**0 を 1 にはできない歯止め遵守** (§3.3、GPT 追加推奨 7)、**§3.1 ESDE 3 解像度 chain 構造特性追加記録** (Web Claude 依頼)。

---

## 0. 一文サマリ

v1104a 主題段階 2 Step A'-G' 全完了、Step A' 認識確認 (NaN 0 件実測 + n-size 別列名 + 比較条件固定 + selector 表現規制 + 観察方法有利化と区別) + 確認要請 3 件 Web Claude/Taka 承認 (1: per-chain shuffle v1104a 独立 parquet 生成、2: density 3 種で進む、3: integration_n_members 既存集約使用) を受け、Step B' (追加調整 1 = 観察 2 を scope × n-size 層化、shuffle B/C 別集計、self-loop 分離、39,537 chains を per-chain で再計算、CID 100% self-loop 確定 / alpha non-self-loop lift_C=0.152 最強 / CID n_size_bin で lift_B/lift_C 優劣反転) / Step C' (追加調整 2 = 観察 3 CID scope cid_n_core 層化、CID 5 bin で stability_vs_maxprob 全 NaN = traj_stability=1.0 定数の構造的帰結、CID_all で diffusion -0.31、ESDE_event/step10 で stability 0.64 / diffusion -0.62 強相関) / Step D' (追加調整 3 = trajectory vs 48 次元密度 3 種比較、coverage 100%、scope/粒度依存の優劣逆転: 細粒 event/step10 で trajectory 優勢、集約粒度 window/CID_all/ESDE_all で density 優勢、CID 5 bin 全で trajectory NaN → density 一択、CID_n=3/n=4 qweighted_density r=-0.972 超強) / Step E' (追加調整 4 = 観察 4 scope-filter、scope 別 B-A 関係の非対称性: CID precision 1.0 = B 全て A 内 subset / alpha/beta recall 1.0 = B が A の 2.7-7.5 倍 superset / ESDE A=0 B=9 = B のみ独自領域) / Step F' (追加調整 4 件 dashboard 16 KB) / Step G' (bit-identity 3 層全 PASS、LAYER_A 7 ファイル hash 完全一致 22.4s、1,502 frozen files 不変 = v1104 13 含む、書込み 9 件 unified/v1104a/ 配下) すべて完了、§3.1 Web Claude 依頼追加記録項目 (ESDE 3 解像度 chain 構造特性、event/step10/window で chain_length mean 28-31 / self-loop 率 29-31% / non-self-loop unique_dest_ratio event/step10 で 0.97 / window で 0.82 → ESDE_window が partial self-loop 性で shuffle C との差別化が顕在) を本書 §6 に記録、核心観察事実 (judgment なし、判定語制限遵守) は (1) **scope 別非対称性の確定**: CID scope 100% self-loop / alpha-beta 部分 self-loop / ESDE 3 解像度 ~30% self-loop で chain 構造が scope 別に異なる、(2) **粒度依存の優劣逆転**: ESDE_event/step10 細粒で trajectory 優勢 (stability r=0.64)、ESDE_window/all/CID 集約粒度で density 優勢 (r=-0.62 〜 -0.97)、(3) **shuffle B/C の chain-level vs scope-level での挙動**: chain-level では shuffle B が ESDE_event/step10/beta で lift~0.05 を持ち、scope-level (Step H-3) と異なる感度、(4) **B 指標の scope 別 pattern**: CID で狭い (precision 1.0)、alpha/beta で広い (recall 1.0)、ESDE で A primary cell ゼロ、scope に応じて A-B 関係が完全に異なる、新規留保候補 #L30 (scope 別 chain 構造の非対称性) / #L31 (粒度依存の trajectory-density 優劣逆転) / #L32 (B 指標の scope 別 pattern、CID で狭く ESDE で独自) / #L33 (CID scope 100% self-loop が trajectory 系統相関を構造的に消失させる、観察 3 における CID 層化の意味は trajectory 指標では消失) を提示、48 次元人為性留保 + 留保 #L21'/#L22'/#L24-29 継承、最終判定 (各追加調整の §2.x.2 出口 (a)/(b)/(c) 判定、§4.2 4 通り組み合わせ更新、次主題候補) は Web Claude Phase Result + Taka 主題評価領域、規律遵守チェック (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + 既存出力流用のみ + 0 を 1 にはできない歯止め + 観察方法有利化との区別) を全 Step で堅持、書込み unified/v1104a/ 配下のみ。

---

## 1. Step A'-G' 進行サマリ

| Step | 内容 | 状態 | 主要出力 |
|---|---|---|---|
| A' | Code A 認識確認 + 確認要請 3 件 | 完了 (Web Claude/Taka 承認) | v1104a_step_a_recognition.md |
| B' | 追加調整 1: 観察 2 scope × n-size × shuffle × self-loop | 完了 (20.8s) | observation_2_per_chain_shuffle.parquet (39,537 chains) + observation_2_scope_stratified.parquet (72 rows) + observation_2_nan_report.json |
| C' | 追加調整 2: 観察 3 CID scope cid_n_core 層化 | 完了 (< 1s) | observation_3_scope_n_stratified.parquet (40 rows) |
| D' | 追加調整 3: trajectory vs 48 次元密度 3 種 | 完了 (< 1s) | observation_3_density_comparison.parquet (192 rows) + observation_3_density_coverage.parquet (5 rows) |
| E' | 追加調整 4: 観察 4 scope-filter | 完了 (< 1s) | observation_4_scope_filtered.parquet (10 rows) + observation_4_b_minus_a_cells.parquet (122 cells) |
| F' | グラフ HTML (4 件 dashboard) | 完了 | v1104a_observation.html (16 KB) |
| G' | bit-identity 3 層検証 (LAYER_A 7 + LAYER_B 1,502) | 完了 (all PASS) | v1104a_step_g_bit_identity_report.json |
| H' | 観察事実最終報告 | 本書 | v1104a_step_h_observation_final.md |
| I | Phase Result (v1104 + v1104a 統合) | 待ち | Web Claude 担当 |

---

## 2. 追加調整 1: 観察 2 を scope × n-size × shuffle × self-loop 層化

### 2.1 全体

- per-chain shuffle B/C 再計算 (Step H-3 reinvestigation_2 を per-chain 保持に拡張)
- 24 seeds、39,537 chains 処理、N_SHUFFLE=10、20.8s
- defensive NaN ハンドリング発火 0 件 (実環境照合通り)

### 2.2 scope × shuffle_type lift_mean (non-self-loop chains)

| scope | shuffle A | shuffle B | shuffle C |
|---|---:|---:|---:|
| alpha | 0.0001 | 0.0113 | **0.1519** |
| beta | 0.0016 | **0.0522** | **0.0910** |
| ESDE_event | 0.0000 | **0.0470** | 0.0211 |
| ESDE_step10 | -0.0000 | **0.0438** | 0.0109 |
| ESDE_window | -0.0003 | 0.0027 | **0.0956** |
| CID | — (該当なし、100% self-loop) | — | — |

太字 = |lift| ≥ 0.01。

### 2.3 scope × shuffle_type lift_mean (self-loop chains)

| scope | shuffle A | shuffle B | shuffle C |
|---|---:|---:|---:|
| CID | 0.0000 | **0.0950** | **0.1056** |
| alpha | 0.0001 | **0.0271** | **0.1807** |
| beta | 0.0001 | **0.0738** | **0.1492** |
| ESDE_event | 0.0000 | **0.0844** | **0.2032** |
| ESDE_step10 | 0.0000 | **0.0820** | **0.2026** |
| ESDE_window | 0.0000 | **0.0365** | **0.2055** |

### 2.4 CID scope n_size_bin × shuffle (self-loop=True、100% self-loop)

| n_size_bin | n_chains | shuffle A | shuffle B | shuffle C |
|---|---:|---:|---:|---:|
| CID_n=2 | 1,314 | 0.000 | **0.1510** | 0.0449 |
| CID_n=3 | 321 | 0.000 | 0.0992 | 0.0992 |
| CID_n=4 | 648 | 0.000 | 0.0699 | **0.1376** |
| CID_n=5+ | 1,515 | 0.000 | 0.0599 | **0.1406** |

→ **CID n_size_bin で lift_B と lift_C の優劣が反転** (n=2 で B>C、n=4/5+ で C>B)

### 2.5 構造事実

- **CID scope 100% self-loop** (3,798/3,798 chains)、構造的に lift_A=0
- **alpha non-self-loop lift_C=0.152** が最強、n_bin 安定 (0.148-0.156)
- **ESDE_event/step10 で lift_B > lift_C** (chain-level 特有)、Step H-3 scope-level (B<C) と異なる感度
- **ESDE_window は lift_C=0.096** で alpha/beta と並ぶ強度、partial self-loop 性に由来 (§6 chain 構造特性参照)
- **CID n_size 別 lift_B/C 反転**: n=2 では同じ chain 内 cid に近いが global pool には遠くない、n=5+ では同じ chain 内 cid は scope 内では近いが global pool に遠い

### 2.6 §2.1.2 (a)/(b)/(c) 候補方向 (Code A 判定しない)

| 候補 | 構造事実の方向 |
|---|---|
| (a) ESDE/CID で lift 顕在、alpha/beta で消失 | 一致せず: alpha non-self-loop lift_C=0.152 最強、ESDE/CID と alpha/beta の単純 2 分は成立しない |
| (b) ESDE/CID と alpha/beta で挙動同じ | 部分一致: lift_C 全 scope で >0、ただし強度と shuffle 種別優劣は scope 別 |
| (c) n_members 別に lift 変動 | 一致: CID n_size_bin で lift_B/C 優劣反転 (n=2 B>C / n=5+ C>B) |

→ **判定は Web Claude Phase Result + Taka 主題評価領域**。

---

## 3. 追加調整 2: 観察 3 を CID scope の cid_n_core 層化

### 3.1 結果 (Pearson r)

| stratum | n | stability_vs_maxprob | diffusion_vs_maxprob |
|---|---:|---:|---:|
| CID_n=2 | 36 | **NaN** | ≈0 (-2.7e-17) |
| CID_n=3 | 36 | **NaN** | ≈0 (-3.8e-20) |
| CID_n=4 | 36 | **NaN** | ≈0 (+2.4e-17) |
| CID_n=5 | 36 | **NaN** | ≈0 (-4.1e-17) |
| CID_n=6+ | 36 | **NaN** | ≈0 (+4.8e-18) |
| **CID_all** | 180 | NaN | **-0.313** (Spearman -0.351) |
| ESDE_event | 36 | **0.639** | **-0.608** |
| ESDE_step10 | 36 | **0.641** | **-0.620** |
| ESDE_window | 36 | 0 | 0 |
| ESDE_all | 108 | 0.417 | -0.477 |

### 3.2 構造事実

- **CID 5 bin で stability_vs_maxprob 全 NaN**: traj_stability_mean = 1.0 定数 (std=0)、原因は Step B' で確定した CID scope 100% self-loop → 全 chain の隣接 window で同一 cid → stability = 1.0
- **CID 5 bin で diffusion_vs_maxprob ≈ 0**: bin 内 2 ユニーク値のみで定数近似
- **CID_all 集約**: diffusion_vs_maxprob r=-0.313 (Spearman -0.351) で **bin 集約後にのみ相関出現**
- **ESDE_event/step10 で stability_vs_maxprob r=0.64 / diffusion_vs_maxprob r=-0.62 強相関**、Step H-4 ESDE_all 値 (r=0.417/-0.477) を分解すると event/step10 が主貢献
- **ESDE_window で相関 0**: traj/response 6 ユニーク値同士が直交、粒度感度

### 3.3 §2.2.2 (a)/(b)/(c) 候補方向 (Code A 判定しない)

| 候補 | 構造事実の方向 |
|---|---|
| (a) CID 内 n_members で対応強度変動 | 一致せず: 全 bin で NaN または 0、stability 指標は計算不能 |
| (b) CID 全体で同じ | 一致せず: CID_all で diffusion -0.31、ESDE_all -0.48 と異なる |
| (c) 特定 bin で対応消える/逆転 | 一致: 全 CID bin で 0、ESDE_window で 0、ESDE_event/step10 で 0.64 |

→ CID scope の cid_n_core 層化は **trajectory 指標では情報を持たない構造的事実** (100% self-loop 由来)。判定は Web Claude/Taka 領域。

---

## 4. 追加調整 3: trajectory vs 48 次元密度 3 種比較

### 4.1 Coverage

| density 列 | n_nan | coverage_rate |
|---|---:|---:|
| raw_density | 0 | 1.0000 |
| qweighted_density | 0 | 1.0000 |
| const_adjusted_density | 0 | 1.0000 |
| mean_pairwise_sim (補助) | 0 | 1.0000 |
| merged vs obs3 join 整合 | 0 | 1.0000 |

→ **欠損 0、全 972 rows で密度 4 列揃う**。

### 4.2 同一 (scope, stratum, response) 内の top predictor

response = response_max_prob の top predictor:

| stratum | top predictor | r | 種別 |
|---|---|---:|---|
| ESDE_all | const_adjusted_density | -0.624 | density |
| **ESDE_event** | **traj_stability_mean** | **0.639** | **trajectory** |
| **ESDE_step10** | **traj_stability_mean** | **0.641** | **trajectory** |
| ESDE_window | mean_pairwise_sim | **-0.910** | density |
| CID_all | qweighted_density | **-0.810** | density |
| CID_n=2 | qweighted_density | 0.613 | density |
| **CID_n=3** | qweighted_density | **-0.972** | density |
| **CID_n=4** | qweighted_density | **-0.972** | density |
| CID_n=5 | mean_pairwise_sim | -0.910 | density |
| CID_n=6+ | mean_pairwise_sim | -0.774 | density |

### 4.3 ESDE_all / CID_all の trajectory vs density 別最大 |r|

| stratum | response | trajectory top | density top |
|---|---|---:|---:|
| ESDE_all | max_prob | diffusion -0.477 | const_adjusted_density **-0.624** |
| ESDE_all | entropy | diffusion +0.223 | raw_density +0.305 |
| CID_all | max_prob | diffusion -0.313 | qweighted_density **-0.810** |
| CID_all | entropy | diffusion +0.200 | qweighted_density +0.567 |

### 4.4 構造事実 (粒度依存の優劣逆転)

- **細粒 (ESDE_event/step10)**: **trajectory (stability) が density を上回る** (r=0.64 > best density)
- **集約粒度 (ESDE_window/all、CID_all)**: density が trajectory を上回る (r=-0.62 〜 -0.91)
- **CID 5 bin 全て**: trajectory が NaN または ≈0 (Step C' で確定した構造的帰結)、density 一択
- **CID_n=3/n=4 で qweighted_density r=-0.972 超強同値**: 局所的に決定的相関、bin 内構造特性
- mean_pairwise_sim は ESDE_window / CID_n=5/6+ で top、qweighted_density は CID_all / CID_n=2/3/4 で top、scope/bin に応じて最適 density 種別が変動

### 4.5 §2.3.2 (a)/(b)/(c) 候補方向 (Code A 判定しない)

| 候補 | 構造事実の方向 |
|---|---|
| (a) trajectory が density を上回る (ESDE/CID で) | 部分一致: ESDE_event/step10 で trajectory > density、それ以外では density 優勢 |
| (b) 両者同程度 | 一致せず: scope/粒度で明確に逆転 |
| (c) density が trajectory を上回る | 部分一致: ESDE_all/window、CID 系列 全で density 優勢 |

→ scope/粒度依存の優劣逆転、**判定は Web Claude/Taka 領域**。

---

## 5. 追加調整 4: 観察 4 を scope-filter

### 5.1 結果 (B_threshold=1, any B)

| scope_filter | n_cells | n_A | n_B | jaccard | recall_B_covers_A | precision_B_is_A |
|---|---:|---:|---:|---:|---:|---:|
| all | 81 | 23 | 69 | 0.227 | 0.739 | 0.246 |
| **CID** | 15 | 9 | 3 | 0.333 | 0.333 | **1.000** |
| **alpha** | 30 | 4 | 30 | 0.133 | **1.000** | 0.133 |
| **beta** | 27 | 10 | 27 | 0.370 | **1.000** | 0.370 |
| **ESDE** | 9 | **0** | 9 | 0.000 | NaN | 0.000 |

### 5.2 結果 (B_threshold=2, strong B)

| scope_filter | n_A | n_B | recall_B_covers_A | precision_B_is_A |
|---|---:|---:|---:|---:|
| all | 23 | 14 | 0.217 | 0.357 |
| CID | 9 | **0** | 0.000 | NaN |
| alpha | 4 | 5 | 0.250 | 0.200 |
| beta | 10 | 6 | 0.400 | **0.667** |
| ESDE | 0 | 3 | NaN | 0.000 |

### 5.3 B\A cell 件数 (b_threshold=1)

| scope_filter | n_B\A cells | unique receiver_bin |
|---|---:|---:|
| all | 52 | 19 |
| alpha | 26 | 9 |
| beta | 17 | 7 |
| ESDE | 9 | 3 |
| CID | **0** | 0 |

### 5.4 構造事実 (scope 別 B-A 関係の非対称性)

- **CID**: B が「狭い」(precision=1.0)、B 全 3 cell は A 内 subset、A 9 cell の 1/3 のみ B 拾う、B\A=0
- **alpha**: B が「広い」(recall=1.0)、A 全 4 cell カバー、B は A の 7.5 倍、B\A=26
- **beta**: B が「広い」(recall=1.0)、A 全 10 cell カバー、B は A の 2.7 倍、B\A=17
- **ESDE**: A primary cell ゼロ、B が全 9 cell を拾う独自領域、B\A=9
- **B_threshold=2 (strong)** で CID の B=0 (B 完全消失)、ESDE は B=3 残存 (A 依然 0)

### 5.5 §2.4.2 (a)/(b)/(c) 候補方向 (Code A 判定しない、表現規制遵守)

| 候補 | 構造事実の方向 |
|---|---|
| (a) CID/ESDE で B-A 一致、alpha/beta で B 広い | 部分一致: CID で precision 1.0 (B subset)、alpha/beta で B 広い、ただし ESDE は A=0 で predicate 不能 |
| (b) CID/ESDE でも B が A より広い | 部分一致: ESDE で B のみ独自 (A=0)、CID では逆 (B subset) |
| (c) scope で B 内容異なる | 一致: B\A 件数 alpha 26/beta 17/ESDE 9/CID 0 で大きく異なる |

→ **B の意味判定は v1105 主題範囲** (GPT 修正必須 D + 追加推奨 6 遵守)、selector 化禁止維持、判定は Web Claude/Taka 領域。

---

## 6. ESDE 3 解像度 chain 構造特性 (§3.1 Web Claude 依頼追加記録)

Step B' での ESDE 3 解像度 non-self-loop lift_C の差異 (event 0.021 / step10 0.011 / window 0.096) の構造的素材として記録。

### 6.1 結果

| scope | n_chains | chain_length mean / median / max / 95p | self-loop 率 | non-self-loop unique_dest_ratio mean / median |
|---|---:|---:|---:|---:|
| ESDE_event | 72 | 28.3 / 29 / 33 / 33 | 30.6% | 0.969 / 1.000 |
| ESDE_step10 | 72 | 29.4 / 30 / 34 / 34 | 30.6% | 0.976 / 1.000 |
| ESDE_window | 72 | 30.5 / 31 / 35 / 35 | 29.2% | **0.822 / 0.962** |

unique_dest_ratio = (chain_length - n_self_loops) / chain_length、non-self-loop chain 内における異なる cid への遷移比率の代理指標。

### 6.2 構造事実

- 3 解像度とも chain 数 72 で同じ、chain_length は粒度に応じて 28-31 と僅差
- self-loop 率は 3 解像度で 29-31% でほぼ同じ
- **non-self-loop chain 内の unique_dest_ratio が ESDE_window で 0.82 / median 0.96** (ESDE_event/step10 の 0.97/1.00 と比較して低い)
- ESDE_window は non-self-loop chain でも **partial self-loop 性** (同じ cid に複数回戻る) を持つ
- これが Step B' で観察された ESDE_window の non-self-loop lift_C=0.096 (event/step10 の 0.02/0.01 と比較して 5-10 倍) の構造的素材

### 6.3 Web Claude Phase Result 解釈統合領域への素材提供

ESDE_window の partial self-loop 性は、shuffle C (global pool) との sim 差別化が顕在化する構造を持つ。ESDE_event/step10 では non-self-loop chain がほぼ完全な「歩き回り」(unique 遷移)、shuffle C と区別困難。Code A はこの構造的素材を記録、解釈は Web Claude/Taka 領域。

---

## 7. bit-identity 3 層検証 (Step G')

### 7.1 結果

| 層 | 内容 | 結果 |
|---|---|---|
| **A** | Step B'-E' 再実行で hash 完全一致 | **7 ファイル全 PASS** |
| **B** | v105/v106/v107/v112/v1101a/v1102/v1103/v1104 main outputs 全 frozen | **all PASS** (a/r/m すべて 0) |
| **C** | 全 5 scripts (Step B'-F') の書込みパスが unified/v1104a/ 配下 | **all_under=True** (9 件) |

- LAYER_A_FILES (7): observation_2_per_chain_shuffle + observation_2_scope_stratified + observation_3_scope_n_stratified + observation_3_density_comparison + observation_3_density_coverage + observation_4_scope_filtered + observation_4_b_minus_a_cells
- LAYER_A_RERUN 経過時間: Step B' 20.9s / C' 0.6s / D' 0.6s / E' 0.3s = 計 22.4s
- LAYER_B 内訳: v105_sal 24 + v105_int 144 + v106 731 + v107 222 + v112 207 + v1101a 131 + v1102 3 + v1103 7 + v1104 13 = **1,502 files 全 frozen 確認** (v1104 13 含む)
- 報告 JSON: `v1104a_step_g_bit_identity_report.json`

---

## 8. 規律遵守総括 (絶対格言 15 件 + GPT 5 点 + Gemini 1 点 + 本主題固有規律)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (v10.5/6/7 + v1101a/v1102/v1103/v1104 read-only、bit-identity 層 B 全 PASS) |
| 絶対格言 #3 (\|effect\| 閾値) | ✓ (\|lift\|>0.01 / \|r\|>0.1 弱・0.3 中・0.5 強、強の主張は必ず条件付記) |
| 絶対格言 #5 (新規 main run 禁止 / 観察軸追加禁止) | ✓ (per-chain shuffle 再計算は既存 reinvestigation_2 拡張、新規 main run なし、§2 観察手順を逸脱せず) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (cid_n_core / integration_n_alpha_members / integration_n_beta_members を別列名、ESDE 3 解像度は層化対象外) |
| 絶対格言 #12 (judgment 回避) | ✓ (全 4 追加調整で (a)/(b)/(c) 判定を行わず、Web Claude/Taka 領域として明記) |
| GPT 追加 4 (判定語制限) | ✓ (「連想」「成功/失敗」「意味がある/ない」を使わず構造事実のみ) |
| GPT 修正必須 C (比較条件固定) | ✓ (追加調整 3 で同一 receiver_bin / 同一 response (max_prob, entropy) / 同一 scope、coverage 欠損別記録) |
| GPT 修正必須 D (selector 表現規制) | ✓ (追加調整 4 で「B selector として使える」「B selector として使える可能性」未使用) |
| GPT 追加推奨 5 (self-loop 分離 + shuffle B/C 別集計) | ✓ (追加調整 1 で is_full_self_loop True/False 分離 + shuffle B/C 別カラム) |
| GPT 追加推奨 6 (B 意味判定 v1105 送り) | ✓ (追加調整 4 で B が何を意味するかの判定なし、観察事実のみ記録) |
| GPT 追加推奨 7 (観察方法有利化と区別) | ✓ (結果が出ない場合の観察方法変更を提案せず、§2 事前確定範囲で結果を出す、0 を 1 にはできない歯止め) |
| Gemini Architect (NaN ハンドリング) | ✓ (実環境 NaN 0 件確認 + defensive 実装で発火 0 件、Ghost 化 CID も除外せず) |
| Aruism 100% を作らない | ✓ (各構造事実に scope/粒度別の非対称性を記録、100% 一致の主張は CID precision 1.0 等の構造的必然のみ) |
| Aruism #33 系列「集計単位で像が変わる」 | 整合 (scope/粒度依存の優劣逆転、CID 100% self-loop、ESDE_window partial self-loop など) |
| 書込みパス unified/v1104a/ 配下 | ✓ (層 C all_under=True、9 件) |
| smoke 含めず | ✓ (本 commit は main 出力のみ) |
| 観察 4 selector 化禁止 (v1104 §2.4.5 継承) | ✓ (post-process 仮想評価のみ、ESDE 内部書き戻し 0) |

---

## 9. 新規留保候補 4 件 (Code A 報告、Web Claude 解釈統合領域)

| candidate id | 内容 |
|---|---|
| **#L30** | scope 別 chain 構造の非対称性: CID scope 100% self-loop / alpha-beta 部分 self-loop / ESDE 3 解像度 29-31% self-loop、scope ごとに chain 構造が定性的に異なる。観察 2/3 の scope-filter 効果と整合的 |
| **#L31** | trajectory-density 優劣逆転は粒度依存: 細粒 (ESDE_event/step10) で trajectory 優勢 (stability r=0.64)、集約粒度 (window/all/CID 各 bin) で density 優勢 (r=-0.62 〜 -0.97)。段 4-c の構造的指標選択は粒度を必須軸として扱う必要 |
| **#L32** | B 指標の scope 別 pattern: CID で precision=1.0 (B subset)、alpha/beta で recall=1.0 (B superset)、ESDE で A=0/B=9 (B のみ独自)。B が「広い」「狭い」「独自」は scope ごとに完全に異なる |
| **#L33** | CID scope 100% self-loop が trajectory 系統相関を構造的に消失させる: traj_stability=1.0 定数化により Pearson 計算が不能 (std=0)、CID 層化の意味は trajectory 指標では消失。逆に density 系統は CID で最強相関 (qweighted_density r=-0.81 CID_all / -0.97 n=3/n=4) |

既存留保継承: #L21' (predecessor 連鎖 shuffle A 依存) / #L22' (trajectory↔response の scope 依存) / #L24-29 (Step H-3/H-4 系列、観察方法依存) / 48 次元人為性留保

---

## 10. 設計書 §4.2 想定 4 通り組み合わせとの対応 (Code A 構造事実、判定は Taka 領域)

各観察の出口 (a)/(b)/(c) の **更新候補** (Code A は判定しないが構造事実の方向のみ):

| 観察 (v1104) | v1104a 追加調整での構造事実の方向 |
|---|---|
| 観察 1 (像差分) | v1104a で再点検対象外、確定済継承 |
| 観察 2 (predecessor 連鎖) | 追加調整 1 で **scope × n-size × shuffle × self-loop 多軸構造を確定**、CID 100% self-loop、alpha non-self-loop lift_C=0.152 最強、CID n_size_bin で lift_B/C 反転 |
| 観察 3 (trajectory↔response) | 追加調整 2 で CID 層化は構造的に trajectory 指標消失、追加調整 3 で粒度依存の trajectory-density 優劣逆転確定、ESDE_event/step10 で trajectory r=0.64 |
| 観察 4 (B 現状) | 追加調整 4 で scope 別 B-A 関係の非対称性確定 (CID subset / alpha-beta superset / ESDE 独自)、B 意味判定は v1105 |

→ 設計書 §4.2 4 通り組み合わせは v1104a 追加調整全 4 件で各観察の構造を多軸化、**最終判定は Web Claude Phase Result + Taka 主題評価領域**。

---

## 11. 出力ファイル総覧 (`unified/v1104a/`)

| ファイル | サイズ |
|---|---:|
| v1104a_phase_design.md | 設計書 v2 |
| v1104a_step_a_recognition.md | Code A 認識確認 + 確認要請 3 件 |
| v1104a_step_b_adjust1.py | per-chain shuffle 再計算 + scope-stratified 集約 |
| v1104a_step_c_adjust2.py | observation_3 CID scope cid_n_core 層化 |
| v1104a_step_d_adjust3.py | trajectory vs density 比較 |
| v1104a_step_e_adjust4.py | observation_4 scope-filter |
| v1104a_step_f_graph.py | 4 件 dashboard 生成 |
| v1104a_step_g_bit_identity.py | 3 層検証 |
| outputs/main/observation_2_per_chain_shuffle.parquet | 39,537 chains |
| outputs/main/observation_2_scope_stratified.parquet | 72 行 |
| outputs/main/observation_2_nan_report.json | 全 0 |
| outputs/main/observation_3_scope_n_stratified.parquet | 40 行 |
| outputs/main/observation_3_density_comparison.parquet | 192 行 |
| outputs/main/observation_3_density_coverage.parquet | 5 行 |
| outputs/main/observation_4_scope_filtered.parquet | 10 行 |
| outputs/main/observation_4_b_minus_a_cells.parquet | 122 cells |
| outputs/v1104a_observation.html | 16 KB |
| v1104a_step_g_bit_identity_report.json | 3 層全 PASS |
| v1104a_step_h_observation_final.md | 本書 |

物理層 (v105/v106/v107/v112/v1101a/v1102/v1103/v1104 main outputs 1,502 ファイル) frozen 維持。

---

## 12. Web Claude Phase Result + Taka 主題評価への引き渡し

Code A 構造事実 (v1104a 追加調整 4 件) の提示完了。以下は Web Claude + Taka 領域:

1. **§2.x.2 (a)/(b)/(c) 出口の最終判定**: 追加調整 1/2/3/4 それぞれで構造事実の方向は §2.6/3.3/4.5/5.5 に記録、判定は Web Claude/Taka 領域
2. **v1104 + v1104a 統合 Phase Result**: 4 観察 × 観察方法 (pooled / 層化 / scope-filter / shuffle 別 / 粒度別) の組み合わせを統合、段 4-b/4-c の Genesis 側根拠確定
3. **次主題 (v1105) 接続点**: 観察 4 の B 意味点検 / scope-aware な B primary 化試行 / 段 4-b Language 側 Constitution Couple との噛み合わせ検証 / 粒度を観察設計の必須軸として格上げ
4. **#L30-L33 新規留保**: scope 別 chain 構造非対称性 / 粒度依存の trajectory-density 優劣逆転 / B 指標の scope 別 pattern / CID 100% self-loop の trajectory 消失効果

---

## 13. 一文サマリ (再掲)

Step A'-G' 全完了、Step A' (確認要請 3 件 Web Claude/Taka 承認) → Step B' (追加調整 1 = 観察 2 scope × n-size × shuffle × self-loop、39,537 chains、CID 100% self-loop、alpha non-self-loop lift_C=0.152 最強) → Step C' (追加調整 2 = 観察 3 CID scope cid_n_core 層化、5 bin 全 stability NaN = 100% self-loop の構造的帰結、ESDE_event/step10 で stability r=0.64 / diffusion r=-0.62 強相関) → Step D' (追加調整 3 = trajectory vs 48 次元密度 3 種、coverage 100%、scope/粒度依存の優劣逆転: event/step10 trajectory 優勢、window/all/CID density 優勢、CID_n=3/4 qweighted_density r=-0.972) → Step E' (追加調整 4 = 観察 4 scope-filter、CID precision 1.0 B subset / alpha-beta recall 1.0 B superset / ESDE A=0 B=9 B のみ独自) → Step F' (4 件 dashboard 16 KB) → Step G' (bit-identity 3 層全 PASS、LAYER_A 7 hash 一致 22.4s、1,502 frozen 不変 v1104 含む、書込み 9 件 unified/v1104a/ 配下)、§3.1 Web Claude 依頼追加記録項目 (ESDE 3 解像度 chain 構造特性: event/step10 unique_dest_ratio 0.97 vs window 0.82 = partial self-loop 性、ESDE_window の non-self-loop lift_C=0.096 強度の構造的素材) を §6 記録、核心観察事実: (1) scope 別非対称性確定 (CID 100% / alpha-beta 部分 / ESDE 29-31% self-loop)、(2) 粒度依存の trajectory-density 優劣逆転、(3) shuffle B/C の chain-level 感度 (Step H-3 scope-level と異なる)、(4) B 指標の scope 別 pattern、新規留保候補 #L30-L33 提示、48 次元人為性留保 + #L21'/#L22'/#L24-29 継承、各追加調整 §2.x.2 出口判定 + §4.2 4 通り更新 + 次主題 (v1105) 接続点 (B 意味点検 / 段 4-b Language 側噛み合わせ / 粒度を必須軸へ格上げ) は Web Claude Phase Result + Taka 主題評価領域、規律遵守 (絶対格言 + selector 化禁止 + 判定語制限 + 物理層 frozen + judgment 回避 + 0 を 1 にはできない歯止め + 観察方法有利化との区別) を全 Step で堅持、書込み unified/v1104a/ 配下のみ。
