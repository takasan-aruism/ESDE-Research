# v10.10 第二弾 多軸層化解析 統合観察報告 (4 タスク)

*作成*: 2026-05-10、Code A
*依頼*: Web Claude 第二弾 案 A 4 タスク並列依頼
*中心問い*: 成熟度軸 (n_core / Integration / 寿命) が単一軸の別表現か独立 3 軸か
*対象*: Web Claude (判定書第三稿への素材) / Taka

---

## 0. 一文サマリ

第二弾 4 タスク (D path × n_core × 全 metric / A-4 Integration 形成タイミング / B-2 寿命 × n_core / C-4 atom × n_core) を 4.32 秒で完了、中心問い「単一軸 vs 独立 3 軸」への観察素材を整理 — **タスク A-4 が決定的観察**: **「Integration 形成前」cid で timing_axis -0.090 (bin_5+)、「形成後 100 step 超」で完全消失 (-0.000)**、これは「Integration 形成タイミング」が timing 軸方向反転の構造的決定因子である可能性を示唆、**タスク B-2** で Q4 × bin_5+ -0.217 / Q4 × bin_2 -0.084 / Q3 × bin_5+ +0.002 と **長寿と n_core が独立寄与を持ちつつ bin_5+ 軸の方が強い**、**タスク C-4** で atom category 別の v110_vs_v108re 効果は all (n_core 統合) で大 (BOD +0.920 / COM +0.931)、bin 別では n_b 不足や効果分散で観察困難、**タスク D** で第一弾と整合 (bin_5+ × high_fam_out -0.653、unrelated -0.638)、中心問いへの暫定観察は **「単一軸でも独立 3 軸でもなく、3 軸が大きく重なる集合 (= Integration 形成前 / 長寿 / 中 cluster はおおむね同じ cid 集合だが完全一致ではない)」**、判定なし、Code A 暫定見立て不要、Web Claude 判定書第三稿の素材として観察事実を提示、第三弾候補は本第二弾結果を見て Taka 判断。

---

## 1. タスク A-4: Integration 形成タイミング × n_core (決定的観察)

### 1.1 cohens_d_mean (mean_delta_C × medium)

#### timing_axis (t200 vs t500、24 seeds 集計)

| formation_relation | all | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|---:|
| **before_formation** | -0.032 | -0.023 | -0.037 | **-0.090** |
| after_formation_0_100 | -0.010 | 0.000 | 0.000 | -0.009 |
| **after_formation_100plus** | **0.000** | **0.000** | **0.000** | **0.000** |
| no_alpha | -0.019 | -0.017 | -0.080 | -0.053 |

#### v110_vs_v108re

| formation_relation | all | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|---:|
| before_formation | +0.022 | -0.000 | +0.025 | +0.071 |
| after_formation_0_100 | +0.011 | 0.000 | +0.034 | +0.012 |
| after_formation_100plus | 0.000 | 0.000 | 0.000 | 0.000 |
| **no_alpha** | **+0.051** | +0.028 | **+0.133** | +0.094 |

### 1.2 n_b 情報 (events 数の seed 平均)

| formation_relation | all | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|---:|
| before_formation | 190 | 86 | 47 | 63 |
| after_formation_0_100 | 57 | 35 | 18 | 23 |
| after_formation_100plus | 213 | 124 | 44 | 72 |
| no_alpha | 116 | 101 | 14 | 10 |

→ events 数は十分 (after_formation_100plus が最多 213)、cohens_d=0 は events 不足ではなく **真に効果が消失**。

### 1.3 観察 (記述のみ)

- **「Integration 形成前」cid で timing 効果が観察された** (bin_5+ で -0.090)
- **「形成後 100 step 超」では timing 効果が完全に消失** (-0.000)
- **「形成直後 (0-100)」も同様にほぼ 0** (-0.009)
- 仮説 (留保):
  - 仮説 1: Integration 形成は cid を「外部刺激に対して閉じる」プロセスである可能性
  - 仮説 2: 形成前 cid は構造が定まっていないため外部刺激への反応性が高い (推測)
- 留保:
  - 「形成前」と「formation_relation=no_alpha (α 形成しない cid)」は別の構造
  - no_alpha は v110_vs_v108re で +0.051 と他より大、Integration 形成しない cid 群は別軸で観察される

→ **これは中心問いへの最重要観察素材**: timing 軸方向反転は「Integration 形成タイミング」と相関、単純な「成熟度」軸では説明できない時間構造がある。

---

## 2. タスク B-2: 寿命 × n_core 交差 (中心問いへの直接素材)

### 2.1 cohens_d_mean (mean_delta_C × medium)

#### timing_axis (t200 vs t500)

| Q | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| Q1 (短命) | NaN | - | - |
| Q2 | -0.021 | -0.010 | -0.024 |
| Q3 | -0.036 | -0.081 | +0.002 |
| **Q4 (長寿)** | **-0.084** | -0.159 | **-0.217** |

#### v110_vs_v108re

| Q | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| **Q1 (短命)** | +0.057 | +0.092 | +0.088 |
| Q2 | +0.046 | +0.002 | +0.030 |
| Q3 | +0.033 | +0.168 | -0.002 |
| **Q4 (長寿)** | **+0.131** | +0.173 | **+0.234** |

### 2.2 n_b 情報

n_b_mean (timing_axis × Q4): bin_2=9, bin_3_4=7, bin_5+=10
n_b_mean (timing_axis × Q3): bin_2=18, bin_3_4=3, bin_5+=2 (bin_3_4/5+ 不足)
n_b_mean (timing_axis × Q2): bin_2=7, bin_3_4=1, bin_5+=1 (bin_3_4/5+ 大幅不足)

→ Q4 × n_core_bin の cohens_d は events 不足でない、Q2/Q3 の bin_3_4/5+ は events 不足留保。

### 2.3 観察 (中心問いへの直接素材)

#### 観察 1: Q4 × bin_5+ で最大効果 (-0.217)

- 単独で見ると「長寿 + 中 cluster」が timing 軸方向反転の核心
- 「単一軸 (成熟度)」仮説に整合する位置

#### 観察 2: Q4 × bin_2 で中効果 (-0.084) — 独立寄与の存在

- bin_2 (ペア) でも Q4 (長寿) なら効果がある (-0.084)
- ペア cid の中にも長寿のものは timing で反応する
- → **「長寿」は n_core と独立に寄与する** (完全に重なるわけではない)

#### 観察 3: Q3 × bin_5+ で +0.002 (効果ほぼなし)

- 中 cluster でも Q3 (中寿) では timing 効果が消失
- → **「中 cluster」だけでは効果は出ない、長寿との交差で初めて効果が観察される**

#### 観察 4: Q1 × bin_2-5+ の v110_vs_v108re は同程度 (+0.057-0.092)

- 短命 cid 群では n_core によらず一様な効果
- 短命 cid は n_core 軸と独立に何らかの構造を持つ可能性 (推測、留保)

### 2.4 中心問いへの観察

- **長寿 × bin_5+ で最大、長寿 × bin_2 でも中効果、中 cluster × Q3 で消失**
- → **「長寿」と「中 cluster」は独立寄与を持つが、両方揃うときに最大効果**
- → **単一軸ではなく、独立 3 軸でもなく、「相関する 2 軸の交差効果」が観察された**

留保: Q1 では timing_axis NaN (events 0)、寿命軸の最低分位は別構造。

---

## 3. タスク D: path × n_core_bin × 全 metric (第一弾の確認 + 拡張)

### 3.1 timing_axis × mean_delta_C × medium (path × n_core_bin)

(第一弾 n_core 報告と同じ、24 seeds 集計の cohens_d_mean):

| path | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| **high_fam_out_integ** | -0.123 | -0.418 | **-0.653** |
| **unrelated** | -0.115 | -0.365 | **-0.638** |
| attention | 0.000 | -0.030 | -0.307 |
| familiarity | 0.000 | -0.117 | -0.123 |
| matched | -0.093 | -0.113 | +0.188 |
| same_int_low_fam | -0.021 | +0.089 | +0.104 |
| temporal | +0.010 | -0.040 | -0.050 |
| same_step | +0.017 | -0.013 | -0.062 |
| integration α/β | 0.000 | 0.000 | -0.024 |

### 3.2 v110_vs_v108re × mean_delta_C × medium

| path | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|
| matched | +0.057 | +0.235 | +0.292 |
| same_step | -0.057 | +0.061 | +0.111 |
| temporal | -0.013 | +0.021 | -0.038 |
| (他) | (中-小) | (中) | (中-大) |

### 3.3 観察 (記述のみ)

- timing_axis では bin_5+ × high_fam_out / unrelated が最大効果量 (第一弾と整合)
- v110_vs_v108re では path 別の差が timing_axis ほど明確でない
- → **timing 軸の効果は path 構造に強く依存、v110 vs v108_re は「全体的な強化」として平均化される**

---

## 4. タスク C-4: atom × n_core 交差

### 4.1 v110_vs_v108re × high_fam_out_integ × mean_delta_C × medium

| atom_category | all | bin_2 | bin_3_4 | bin_5+ |
|---|---:|---:|---:|---:|
| **BOD** | **+0.920** | +0.125 | 0.000 | NaN |
| **COM** | **+0.931** | +0.109 | 0.000 | NaN |
| **COG** | **+0.909** | +0.198 | 0.000 | -0.054 |
| EXS | +0.547 | +0.324 | +0.121 | +0.238 |
| FND | +0.447 | +0.231 | +0.310 | +0.080 |
| PER | +0.322 | +0.122 | +0.081 | +0.017 |
| PRP | +0.219 | +0.061 | +0.112 | +0.172 |
| SOC | +0.220 | +0.164 | +0.084 | +0.251 |
| TIM | +0.135 | +0.207 | 0.000 | 0.000 |
| WLD | +0.092 | +0.042 | +0.082 | +0.089 |

### 4.2 観察 (n_b 不足の留保込み)

- **all (n_core 統合) で大効果、bin 別では効果が大きく低下**
- 仮説 (留保):
  - 仮説 1: 「all で大」は events 数の集合効果で、bin 別では n_b 不足のため評価困難
  - 仮説 2: 集合効果として観察される現象が n_core 別に分解されると個別効果は小さい (仮説 1 と整合)
- 留保:
  - 1 atom × 1 n_core_bin で events 平均 15、n_b 不足セルが多発
  - cohens_d 計算で n_b ≥ 3 の seed 数を `n_seeds_b_insufficient` 列で併記したが集計方法に留保あり (要再確認)
  - 「BOD all=+0.920 が n_core 統合で見えるが、n_core 別では分散」という観察自体が留保事項
- 構造解釈の困難:
  - 「BOD/COM/COG」が all で大効果 → events 数集合効果か、概念意味との対応か未解明
  - bin 別で効果が消失する原因は events 不足か実質効果消失か区別困難

### 4.3 中心問いへの寄与 (限定的)

タスク C-4 の n_b 不足のため、中心問いへの直接素材は限定的。**「概念意味と n_core の交差は本観察規模では分解困難」** という留保のみ提供。

---

## 5. 中心問いへの統合観察 (Code A 観察記述、判定なし)

### 5.1 観察素材の整理

| 観察 | 解釈候補 |
|---|---|
| Integration 形成前 cid で timing 効果、形成後 100 step 超で消失 | Integration 形成タイミングが timing 軸の決定因子 |
| Q4 × bin_5+ -0.217 (最大)、Q4 × bin_2 -0.084 (中)、Q3 × bin_5+ +0.002 | 寿命と n_core は独立寄与を持つが、両方揃うときに最大効果 |
| atom category × n_core_bin は n_b 不足で分解困難 | 概念意味軸と n_core 軸の関係は本規模で観察不能 |
| bin_5+ × high_fam_out -0.653、bin_5+ × unrelated -0.638 (path × n_core) | n_core × path 軸の交差で大効果量、第一弾と整合 |

### 5.2 中心問いに対する観察 (判定ではなく観察事実)

仮説 1 (単一軸: 成熟度) は完全には支持されない:
- Q4 × bin_2 で -0.084 (ペアでも長寿なら効果あり) → 単純な「成熟度」軸では説明できない
- before_formation の cohens_d は formation_relation で時間軸が独立に効く

仮説 2 (独立 3 軸) も完全には支持されない:
- Q3 × bin_5+ で +0.002 (中 cluster でも中寿では効果消失) → 完全に独立ではない
- Integration 形成前 / 長寿 / 中 cluster は **大きく重なる集合**

### 5.3 中間的な観察 (Code A 自主観察、判定なし)

**「成熟度軸」と呼ぶには独立な時間軸 (Integration 形成タイミング、寿命) と構造軸 (n_core) が同時に必要で、3 軸が大きく重なる cid 集合 (= 中 cluster で長寿で Integration 形成前) で最大効果が観察される**。

これは:
- v10.11 入力ルーティング設計で **「単一指標」では決まらない** ことを示唆
- **「Integration 形成タイミング」は v10.10 で初めて浮上した軸**、v10.9 までの 4 種設計表 (受信可能状態) には含まれない
- v10.11 では Integration 形成タイミングを含む多次元ルーティングが妥当 (推測、留保)

---

## 6. 留保事項 (新規発生分)

第一弾までの留保 10 件 + 第二弾新規:

11. **Integration 形成前と after_formation_100plus の cohens_d 差の構造的解釈**: 形成プロセスが cid の応答性をどう変えるかは未解明 (仮説段階)
12. **「相関する 2 軸の交差効果」の構造的根拠**: 寿命と n_core が両方揃うときに最大効果という観察は、両軸の発生プロセスの相関に由来する可能性 (推測)
13. **タスク C-4 の n_b 不足**: atom × n_core 交差の集計方法 `n_seeds_b_insufficient` の値に集計上の留保あり (実装要再確認)
14. **no_alpha 群の v110_vs_v108re +0.133 (bin_3_4)**: Integration 形成しない cid 群の効果は formation_relation の他カテゴリと別の構造を持つ可能性

---

## 7. 出力ファイル

| ファイル | 内容 | 行数 |
|---|---|---:|
| `cross_seed/v110_path_n_core_full_cross.parquet` | タスク D | 1,620 |
| `cross_seed/v110_formation_relation_stratified.parquet` | タスク A-4 | 96 |
| `cross_seed/v110_lifespan_n_core_cross_summary.parquet` | タスク B-2 | 96 |
| `cross_seed/v110_atom_n_core_cross_summary.parquet` | タスク C-4 | 750 |
| `v110_round2_summary.md` | 本書 | - |

実装: `v110_round2_analyzer.py`、実行 4.32 秒。

---

## 8. 第三弾候補への素材

タスク A-4 で「Integration 形成タイミング」が決定因子として浮上したことを踏まえ、第三弾候補:

### 候補 G: bimodal の n_core 層化

v10.9 bimodal データに遡り、bimodal を n_core 別に分解する。本第二弾観察「bin_5+ で大効果」が v10.9 H3_lifecycle 仮説 (中 cluster 高 delta) とどう関係するかを構造的に確認。

### 候補 H: cid pair / co-activation 解析

bin_2 (ペア) cid を pair 単位で解析、n_core=2 という構造 (ペア) が外部刺激にどう応答するかを観察。pulse 系で大効果量 (matched +4.295) の構造的根拠を探る。

### 候補 I (新規): Integration 形成プロセスの解析

タスク A-4 で formation_relation が決定的観察素材として浮上したため、**Integration 形成 (α 形成 / β 形成 / 解散) のプロセスそのものを観察対象** として加える。これは v10.7 / v10.8 で実装されていない新軸。

---

## 9. 一文サマリ (再掲)

第二弾 4 タスクを 4.32 秒で完了、中心問いへの観察素材を整理 — タスク A-4 が決定的観察「**Integration 形成前 cid で timing 効果 (bin_5+ で -0.090)、形成後 100 step 超で完全消失 (-0.000)**」 → Integration 形成タイミングが timing 軸方向反転の構造的決定因子の可能性、タスク B-2 で **長寿と n_core が独立寄与を持ちつつ両方揃うときに最大効果** (Q4×bin_5+ -0.217 / Q4×bin_2 -0.084)、タスク C-4 は n_b 不足で限定的、タスク D は第一弾と整合、中心問いへの暫定観察は **「単一軸でも独立 3 軸でもなく、3 軸が大きく重なる cid 集合 (中 cluster + 長寿 + Integration 形成前) で最大効果」**、判定なし、Code A 暫定見立て不要、Web Claude 判定書第三稿への素材として観察事実を提示、留保事項新規 4 件追加 (計 14 件)、第三弾候補は本第二弾結果を踏まえ Taka 判断 (新規候補 I: Integration 形成プロセス解析を提案)。

---

*以上、Code A による v10.10 第二弾 統合観察報告。Web Claude 判定書第三稿への素材として活用。判定なし、観察記述のみ、因果断定回避規律遵守、events 数 / n_b 不足併記。*
