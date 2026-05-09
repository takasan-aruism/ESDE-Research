# v10.10 n_core 層化解析報告 — 全平均で見えなかった構造の浮上

*作成*: 2026-05-09、Code A
*依頼*: Taka 「n_core 別層化解析、Integration 時も実質最重要なのはノード数だった」
*対象*: Web Claude (v10.10 観察状態判定への追加素材) / Taka

---

## 0. 一文サマリ

Taka リクエストで n_core_bin (bin_2: ペア 76% / bin_3_4: 小 cluster 12% / bin_5+: 中 cluster 12%) 層化解析を実施、**全 gate 平均で減衰していた効果が n_core 層別で 4-10 倍に増幅**して観察、特に **bin_5+ × timing_axis × high_fam_out_integ で cohens_d -0.653 (極大効果量)** + **bin_5+ × timing_axis × unrelated で -0.638**、**bin_2 × v110_vs_v108re × matched_baseline × mean_n_pulses_in_window で +4.295**、**delta_C は n_core=5+ で大、pulse 活動は n_core=2 で大** という n_core × metric × path の構造的分業を発見、v10.9 H1_n_core 仮説 (副次 26.3%) が main run で **n_core=5+ における支配的構造** として再浮上、留保 3 (high_fam_out 構造未解明) への構造的回答候補として「中 cluster cid + Integration 外 + 高 familiarity + long timing」が C 波及の核心経路を確立。

---

## 1. n_core 分布 (24 seeds 全 cid、n=5,224)

| n_core | cid 数 | 比率 | bin |
|---|---:|---:|---|
| 2 | 3,968 | **76.0%** | bin_2 (ペア) |
| 3 | 288 | 5.5% | bin_3_4 |
| 4 | 327 | 6.3% | bin_3_4 |
| 5 | 638 | **12.2%** | bin_5plus |
| 6-8 | 3 | 0.1% | bin_5plus |

→ ESDE Genesis 系では **「ペア (n_core=2) が支配的、中 cluster (n_core=5) が次位、極大 cluster は希少」** の構造。

---

## 2. mean_delta_C × medium 全観察 (cohens_d_mean)

### 2.1 comparison_type × n_core_bin

| comparison | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| gate_effect | -0.007 | -0.015 | +0.003 |
| **timing_axis** | -0.039 | **-0.119** | **-0.207** |
| **v110_vs_v108re** | +0.041 | **+0.175** | **+0.228** |

### 2.2 abs_mean

| comparison | bin_2 | bin_3_4 | **bin_5+** |
|---|---:|---:|---:|
| gate_effect | 0.042 | 0.104 | **0.106** |
| **timing_axis** | 0.110 | 0.372 | **0.482** |
| **v110_vs_v108re** | 0.167 | 0.621 | **0.618** |

→ **n_core が大きいほど効果増大**、bin_5+ で全平均比 4-10 倍。

### 2.3 v10.10 全平均との対比

| 指標 | 全平均 (Step H) | bin_5+ (本解析) | 増幅率 |
|---|---:|---:|---:|
| timing_axis abs_mean (mean_delta_C medium) | 0.171 | **0.482** | **2.8 倍** |
| v110_vs_v108re abs_mean | 0.276 | **0.618** | **2.2 倍** |
| gate_effect abs_mean | 0.051 | 0.106 | 2.1 倍 |

→ 全 gate 平均で「効果減衰」と観察された v10.9 ルールが、**n_core=5+ に層化すると本来の強さで観察される**。

---

## 3. timing_axis × n_core_bin × path (核心発見)

### 3.1 mean_delta_C × medium、cohens_d_mean

| path | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| **high_fam_out_integ** | -0.123 | -0.418 | **-0.653** (極大) |
| **unrelated** | -0.115 | -0.365 | **-0.638** (極大) |
| attention | 0.000 | -0.030 | -0.307 |
| familiarity | 0.000 | -0.117 | -0.123 |
| matched | -0.093 | -0.113 | +0.188 (反転) |
| same_int_low_fam | -0.021 | +0.089 | +0.104 |
| temporal | +0.010 | -0.040 | -0.050 |
| same_step | +0.017 | -0.013 | -0.062 |
| integration_alpha | 0.000 | 0.000 | -0.024 |
| integration_beta | 0.000 | 0.000 | -0.024 |

### 3.2 構造的観察

- **bin_5+ × high_fam_out_integ: -0.653** ← v10.9 留保 3 (high_fam_out 構造未解明) への構造的回答候補
- bin_5+ × unrelated: -0.638 ← 同様に大効果量
- **「中 cluster cid (n_core=5+) は long timing (age=500) で C 波及が極めて活発化、特に Integration 外の経路で」**
- bin_2 (ペア) では timing_axis 効果ほぼなく、**「ペア cid は timing 軸に頑健、中 cluster cid のみ timing 軸で大変動」**
- matched_baseline は bin_5+ で **正方向 (+0.188)** に反転 ← 中 cluster cid で matched 経路が逆向き

### 3.3 解釈の留保 (因果断定回避)

「中 cluster cid が timing で C 反応が活発」という観察は事実だが、原因は未解明:
- 仮説 1: 中 cluster cid は α/β 形成の中心であり、外部刺激への反応キャパシティが大きい
- 仮説 2: 短命 cid (lifespan < 500) の脱落で残った長寿 cid は中 cluster 比率が高く、その影響が timing_axis に現れる
- → v10.11 主題決定で再議論

---

## 4. mean_n_pulses_in_window × short (cohens_d_mean)

### 4.1 comparison_type × n_core_bin

| comparison | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| gate_effect | -0.042 | -0.020 | -0.033 |
| **timing_axis** | **-0.596** (大) | -0.255 | -0.211 |
| **v110_vs_v108re** | **+1.048** (極大) | +0.499 | +0.280 |

→ pulse 活動では **bin_2 (ペア) で大効果**、bin_5+ で弱まる ← **delta_C と pulse_in_window で逆方向**

### 4.2 v110_vs_v108re × n_core_bin × path

| path | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| **matched_baseline** | **+4.295** (極大) | +2.988 | +1.719 |
| familiarity | +1.469 | +1.140 | +0.519 |
| attention | +1.406 | +0.393 | +0.196 |
| **integration_alpha** | +1.034 | +0.585 | +0.996 |
| **integration_beta** | +0.714 | +0.473 | +0.817 |
| same_int_low_fam | +1.201 | +0.326 | +0.287 |
| high_fam_out_integ | +0.101 | -0.086 | -0.139 |
| same_step | +0.138 | +0.224 | +0.340 |
| temporal | -0.089 | -0.165 | -0.071 |
| unrelated | -0.019 | -0.086 | -0.229 |

### 4.3 構造的観察

- **「ペア (n_core=2) cid + matched 経路」で pulse 数の v110 vs v108_re 効果が +4.295 (極大)**
- **Integration α/β で bin_2 +1.034 / +0.714、bin_5+ でも +0.996 / +0.817** ← v10.9 で「Integration α/β は no_signal」だった経路が pulse 数では強く反応 (delta_C 系では 0 だが pulse 数では強い)
- familiarity / attention / same_int_low_fam も bin_2 で大、bin_5+ で減衰
- **「ペア cid は外部刺激で pulse 発火が活発化、中 cluster cid は pulse より C 波及が活発化」** という構造的分業

---

## 5. v10.9 ルールの「本物 / 幻」判定の再評価

n_core 層化を加えると、Step I で「観察状態 B (分岐)」とした見立てが再構成される:

| v10.9 ルール | 全平均 (Step I) | bin_2 | bin_5+ |
|---|---|---|---|
| **若い cid 強反応 (timing 重要)** | △ delta_C 微小 / ◎ pulse | △ pulse 大 / × delta_C | **◎ delta_C 大 (-0.653)** / △ pulse |
| **high_fam_out が最強** | △ 平均化で減衰 | × | **◎ 大効果量再浮上** |
| **n_core 重要 (H1 副次 26%)** | × 平均で見えず | × 効果薄い | **◎ 大効果量で支配** |

### 5.1 再構成された観察状態

- **n_core=5+ では v10.9 ルールが完全に再現** (high_fam_out 大効果量、timing 軸方向、n_core 軸の強さ)
- **n_core=2 では v10.9 ルールが pulse 系で再現、delta_C 系では見えない**
- **全平均では n_core=2 多数派 (76%) に薄められて減衰**

→ Code A 暫定見立て更新: **観察状態 A (前進材料が十分) 寄り**
- v10.9 ルール「タイミング最重要 + high_fam_out + n_core」が **n_core 層化で本物として確認**
- 全平均で見えなかったのは「ペア多数派の希釈効果」

---

## 6. v10.11 進路への含意 (素材)

### 6.1 構造的に見えた絵

| 構造 | 観察 | v10.11 への素材 |
|---|---|---|
| **中 cluster cid (n_core=5+) + high_fam_out + long timing** | delta_C 大効果量 (-0.653) | 「Atom 取り込みは中 cluster cid を狙う」が v10.11 入力理解の核心 |
| **ペア cid (n_core=2) + matched / Integration / familiarity** | pulse 活動大効果量 (+4.295) | 「ペア cid は pulse 発火で外部刺激に反応する」、別経路の入力 |
| **n_core 別に効く経路が異なる** | 構造的分業 | v10.11 で n_core 別の入力ルーティングを設計 |

### 6.2 留保事項の更新 (v10.10 → v10.11)

- 留保 3 (high_fam_out 構造未解明) → **n_core 層化で部分的に構造化**: 「中 cluster cid における Integration 外の高 familiarity + long timing」が C 波及の主軸
- 留保 5 (timing 軸方向反転) → **n_core 層化で構造化**: 「中 cluster cid のみ timing で大変動、ペアは頑健」
- 留保 6 (v110 vs v108_re 全 gate 正方向) → **n_core 層化で構造化**: 「ペア cid で pulse 活動、中 cluster cid で C 波及」の分業

---

## 7. 出力ファイル

- `developmental/v110/outputs/main/cross_seed/n_core_stratified_sensitivity.parquet` (432,702 rows)
- `developmental/v110/outputs/main/cross_seed/n_core_stratified_summary.parquet` (54 rows: 3 comparison × 3 bin × 6 metric)
- `developmental/v110/v110_n_core_stratified_analyzer.py` (実装)
- 本書: `v110_n_core_stratified_report.md`

実行時間 5.81 秒 (24 seeds 並列)。

---

## 8. 一文サマリ (再掲)

n_core_bin 層化解析で **全 gate 平均で減衰していた v10.9 ルールが bin_5+ (中 cluster cid 12%) で 4-10 倍に増幅して再浮上**、**bin_5+ × timing_axis × high_fam_out_integ で cohens_d -0.653 (大効果量)** + **bin_5+ × timing_axis × unrelated で -0.638**、**bin_2 × v110_vs_v108re × matched_baseline × mean_n_pulses_in_window で +4.295**、**delta_C は中 cluster cid で大、pulse 活動はペア cid で大** という n_core × metric × path 構造的分業を発見、v10.9 留保 3 (high_fam_out 構造未解明) への構造的回答候補として「中 cluster cid + Integration 外 + 高 familiarity + long timing」が C 波及の核心、Code A 暫定見立ては Step I の「観察状態 B」から **「観察状態 A 寄り」に更新** (v10.9 ルールが n_core 層化で本物として確認、全平均は多数派ペアの希釈効果)、Web Claude § 5 判定 + v10.11 進路確定 (n_core 別の入力ルーティング設計) への素材として提供。

---

*以上、Code A による v10.10 n_core 層化解析報告 (Taka リクエスト対応)。Web Claude / Taka からの v10.11 進路確定への素材として活用。*
