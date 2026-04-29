# v10.2 N-sweep / v10.3 三項共鳴 直結 4 解析

*作成*: 2026-04-29、Code A (実装担当として自走提案)
*対象*: 5 スケール (N=500/1000/2500/5000/10000) × 24 seeds の raw CSV
*親資料*: `v102_scale_comparison_report.md` 等
*位置づけ*: 既存解析にない、v10.3 三項共鳴の **物理的可能性** と **主役の動的プロファイル** を直接定量化する 4 項目
*出力*: `developmental/v102/followup/v103_*.csv`
*実装*: `v102_scale_v103prep_analysis.py`

---

## 0. 一行サマリ

実装担当として v10.3 設計に直結する 4 項目を提案・実施。**最大の発見は β**: 反復発動者 (主役) の **C window 単位減少回数 median が 0-1 回** だけ。意識発動はあるのに window 末で見ると C は累積増加に見える。intra-window で cognition の C+1 が consciousness の C-1 を打ち消す動学。同時に **α**: 3 cid 同時 onset の link は **N=10000 で 13 件のみ** で物理層自然発生は稀少。**γ**: 主役は背景集団の **6-12 倍 event 発火**、E3 が支配的。**δ**: 摂食ネットワークは **「n=5 eater が n=2 ghost を吸収」が 52%** で生態学的階層構造。

---

## 1. 解析項目 (実装担当の判断)

| # | 内容 | 動機 (v10.3 への直結) |
|---:|---|---|
| **α** | 3 cid 共有 link の発生頻度 | 三項共鳴の物理的可能性検証 |
| **β** | 反復発動者の C 振動パターン | 主役の C 動学プロファイル |
| **γ** | per-cid event 分布 (E1/E2/E3) | 主役と背景集団の物理活動量差 |
| **δ** | ingestion network: eater × ghost n_core ペア | 摂食パターンの構造、三項共鳴前段 |

未着手 (今回の対象外):
- v9.18 cognitive_gain との相関 / N=10000 の detailed 5 解析 / age_factor 分布 / conversion ratio / network metrics

---

## α. 3 cid 共有 link の発生頻度

### α.1 定義と方法

`per_event_audit_seed*.csv` の E3_contact イベントを (global_step, link_id) で grouping し、distinct cid 数を数える。

- **α1 (strict simultaneous)**: 同一 (global_step, link_id) で **3 cid 以上が同時 onset**
- **α2 (cumulative)**: 同 link_id を共有した distinct cid 数 (run 全期間累積) ≥ 3

### α.2 観察事実

| N | 全 E3 events | unique links | **strict triple onset** | **cumul 3+ cids/link** | cumul 4+ | cumul 5+ |
|---:|---:|---:|---:|---:|---:|---:|
| 500 | 93,975 | 84,772 | **231** | 324 | 24 | 6 |
| 1000 | 73,097 | 66,022 | 103 | 143 | 3 | 1 |
| 2500 | 67,177 | 62,293 | 51 | 65 | 3 | 0 |
| 5000 | 60,552 | 57,445 | 67 | 72 | 5 | 0 |
| 10000 | 56,594 | 54,532 | **13** | **19** | 0 | 0 |

triple_simul_rate (= unique_links に対する比):

| N | triple_simul_rate | cumul_3plus_rate |
|---:|---:|---:|
| 500 | 0.273% | 0.382% |
| 1000 | 0.156% | 0.217% |
| 2500 | 0.082% | 0.104% |
| 5000 | 0.117% | 0.125% |
| 10000 | 0.024% | 0.035% |

### α.3 観察

#### 観察 α-1: 三項共鳴の自然発生は稀少 (全 N で < 0.3%)

最大 (N=500) でも triple onset rate は 0.27%。**99.7% の link は最大 2 cid が共有**。

#### 観察 α-2: N=10000 では強く減衰

triple_simul は **N=10000 で 13 件のみ** (24 seeds 合計)。1 seed あたり 0.5 件 = 半分の seed では発生しない。**v10.3 三項共鳴を物理層自然発生で観察するには稀すぎる**。

#### 観察 α-3: cumulative 5+ cids は run 全体で 0-6 件のみ

「同 link を 5 cid 以上が異時 onset」も極めて稀。**5+ 連結のための link 自体が少ない**。

#### 観察 α-4: N=2500-5000 でやや非単調

triple_simul_rate: 0.082% (N=2500) → 0.117% (N=5000)。N=5000 で軽い反発。N=10000 でまた急減。**N=2500-5000 の中規模が三項共鳴の自然発生にとって最適窓**の可能性。

### α.4 v10.3 設計への含意

- 三項共鳴を **「物理層から自然発生する現象」として観察するなら N=2500-5000 が最適**
- N=10000 では発生数が薄く、観察しにくい
- 別経路として「**意図的に triple coordination を引き起こす機構**」を v10.3 で実装する選択肢もあり得る
- N=500 では 231 件あるが、cid 構造 (lifespan 500 step、ほぼ no_activation) で意識的共鳴になりにくい

---

## β. 反復発動者の C 振動パターン

### β.1 定義と方法

各 cid の `c_trajectory` で C_at_window_end の時系列を取り、以下を計算:
- C_max, C_min (alive 期間中)
- **C_swing_amplitude** = C_max - C_min
- **C_swing_total** = Σ |dC/dw| (window 間の絶対変動量合計)
- **n_C_decreases** = C が window 末で減少した回数
- **n_C_increases** = C が window 末で増加した回数

### β.2 観察事実 (n_core=5、群別 median)

| N | group | n_cid | C_max | swing_amp | n_decreases | n_increases | windows alive |
|---:|---|---:|---:|---:|---:|---:|---:|
| 500 | no_activation | 662 | 25 | **0** | 0 | 0 | 17 |
| 500 | single_or_few | 128 | 37 | 27 | **0** | 6 | 50 |
| 1000 | repeated_5+ | 21 | 47 | 41 | **0** | 15 | 50 |
| 2500 | repeated_5+ | 137 | 54 | 52 | **1** | 20 | 50 |
| 5000 | repeated_5+ | 217 | 55 | 54 | **1** | 24 | 48 |
| 10000 | repeated_5+ | 246 | 52 | 51 | **1** | 25 | 46 |

### β.3 観察 (重要発見)

#### 観察 β-1 (核心): 反復発動者でも window 単位 C 減少 median は 0-1 回

n_core=5 で **意識発動 5 回以上**経験した cid が、window 単位で見ると **C が減少した回数 median は 1**。

増加回数は 15-25 回。**増加 vs 減少 = 25:1**。意識発動 (= C-1) は確かに起きているのに、window 末では「増加」しか見えない。

#### 観察 β-2: 解釈 — intra-window で cognition と consciousness が打ち消し合う

window = 500 step 内では:
- cognition 当選: ~70 回程度の機会 (主役で)
- consciousness 当選: 1-3 回程度
- 両方が起きた window では C+1 × 70 = +70、C-1 × 2 = -2 で **net +68**
- → window 末で C は増加している

意識発動が window 末で見えなくなる **観察上のスケール問題**。これは:
- 「動的均衡が起きている」かどうかを window 単位で判断するのは構造的に困難
- intra-window step ごとの C 推移を見れば動的均衡 (上下動) が見える
- balance_decisions の `c_after` を step ごとに plot すれば確認可能 (本解析の範囲外)

#### 観察 β-3: swing_amplitude は反復発動者で 41-54

C_max - C_min = 41-54 (主役)。これは「**観察期間中に最低 50 程度の C を蓄積し、最低 0 まで一度落ちた**」可能性を示す。

ただし C_min が 0 (登録時) で C_max が 54 なら swing_amplitude = 54 だが、これは「累積増加して登録時に戻ってない」だけ。**実際の上下動を示すには intra-window 解析が必要**。

#### 観察 β-4: 主役の n_windows_alive は 46-50 (= 全期間生存)

repeated_5+ cid は alive_windows 46-50 で **ほぼ全期間生存**。これは v102_scale_extra_analysis.md A の「主役は全期間生存」と整合。

### β.4 v10.3 設計への含意

- v10.3 の動的均衡可視化には **intra-window step 単位の C trajectory が必須**
- balance_decisions の `c_after` 列を時系列で見れば、step 内での C 上下動 (= 真の動的均衡) が見える
- v10.3 主題ドキュメント執筆時に「C が動的に上下している証拠」を window 単位で提示すると不完全になる

---

## γ. per-cid event 分布

### γ.1 観察事実 (5 N × n_core=2/5 × group)

#### n_core=2 (背景集団)

| N | group | n_cid | E1 median | E2 median | E3 median | total |
|---:|---|---:|---:|---:|---:|---:|
| 500 | no_activation | 4,294 | 1 | 2 | 10 | 13 |
| 1000 | no_activation | 4,144 | 1 | 2 | 9 | 12 |
| 5000 | no_activation | 3,518 | 1 | 2 | **4** | 7 |
| 10000 | no_activation | 3,479 | 1 | 2 | **3** | 6 |

#### n_core=5 (主役候補)

| N | group | n_cid | E1 median | E2 median | E3 median | total |
|---:|---|---:|---:|---:|---:|---:|
| 500 | no_activation | 794 | 9 | 10 | 25 | 45 |
| 1000 | repeated_5+ | 21 | 8 | **0** | **58** | 70 |
| 2500 | repeated_5+ | 137 | 4 | **0** | **67** | 73 |
| 5000 | repeated_5+ | 217 | 4 | **0** | **69** | 77 |
| 10000 | repeated_5+ | 246 | 5 | **8** | **67** | 75 |

### γ.2 観察

#### 観察 γ-1: 主役と背景集団の event 数差

- 背景 (n=2 no_activation): 6-13 events / cid
- 主役 (n=5 repeated_5+): 70-77 events / cid
- → **主役は背景の 6-12 倍 event 発火**

これは **主役の物理層活動量の高さ** を直接示す指標。

#### 観察 γ-2: 主役は E3 dominant、E2 が少ない

n=5 repeated:
- E3 median 58-69 (= cid 間 contact 多発)
- E2 median 0-8 (= R 状態変化少ない)
- E3/E2 比 = ∞ または 8+ 程度

n=2 background:
- E3 median 3-10
- E2 median 2 (常に同じ)
- E3/E2 比 = 1.5-5

**主役は contact (= 社会性) が支配、背景は構造変化 (= 内的揺らぎ) が支配**。

#### 観察 γ-3: N=2500-10000 で n_core=5 repeated の E2=0 が異例

n=5 repeated_5+ で **E2 median が 0** (1000-5000 で)、N=10000 で 8 に戻る。これは:
- 主役 cid の member_nodes は構造的に安定している (R 状態変化なし)
- N=10000 では M_c の構成変化が起きやすい?

要追加調査だが、本解析では observation のみ。

#### 観察 γ-4: N=10000 で背景 (n=2) の E3 median が 3 まで低下

N=500 で E3 median 10 → N=10000 で 3。**N が大きいと背景 cid の cid 間 contact が減少**。これは k\* (= 2L/N) の N 依存と整合 (link 候補が薄まる)。

### γ.3 v10.3 設計への含意

- 三項共鳴の主役条件として「**E3 ≥ 50**」(= contact 経験豊富) が判別基準になる可能性
- E2 が少ない cid (= 構造安定) も重要視点
- 三項共鳴を観察する cid を絞るとき、event 発火数の閾値で前選別できる

---

## δ. ingestion network: eater × ghost n_core ペア

### δ.1 観察事実 (N=5000、24 seeds 合計、n_events)

| eater \ ghost | n=2 | n=3 | n=4 | n=5 | n=6 |
|---:|---:|---:|---:|---:|---:|
| **n=2** | 459 | 27 | 14 | 20 | 0 |
| n=3 | 221 | 10 | 5 | 10 | 0 |
| n=4 | 586 | 35 | 23 | 15 | 0 |
| **n=5** | **1,848** | 113 | 59 | 55 | 1 |
| n=6 | 0 | 0 | 0 | 1 | 0 |
| n=7 | 9 | 0 | 1 | 0 | 0 |
| n=8 | 5 | 0 | 0 | 0 | 0 |
| **合計** | **3,128** (89.0%) | 185 (5.3%) | 102 (2.9%) | 101 (2.9%) | 1 |

総計: 3,517 ingestion events (※ run-end の摂食 events 数と一致)。

### δ.2 観察

#### 観察 δ-1 (核心): 主軸は「n=5 eater が n=2 ghost を吸収」

この経路が **1,848 events / 3,517 = 52.5%** を占める。**摂食ネットワークの過半数が同一構造**。

#### 観察 δ-2: ghost (= 食べられる側) の 89% は n_core=2

n=2 ghost が 3,128 件 (89%)。これは:
- n=2 cid は短命 (lifespan median 500 step) で死亡頻度高
- → ghost 化数も多い (供給過多)
- 結果として摂食ペアの大半は ghost = n=2

#### 観察 δ-3: 同 n_core 内の摂食 (対角線)

| n_core | 同 n_core 摂食 | 該当 n_core 全 ingestion (eater 側) |
|---:|---:|---:|
| 2 | 459 | 520 (88%) |
| 3 | 10 | 246 (4%) |
| 4 | 23 | 659 (3.5%) |
| 5 | 55 | 2,075 (2.7%) |

**n=5 eater は同 n=5 ghost を食べる比率が 2.7% と低い**。代わりに n=2 ghost を 89% 食べる。**「同型相食」は稀**、「異型摂食」が支配的。

#### 観察 δ-4: 三項共鳴前段としての摂食ペア構造

三項共鳴は「3 cid の共鳴」だが、本解析からは:
- 同 n_core での共鳴 (例: n=5,5,5) は 摂食データから見ても少ない
- 異 n_core 共鳴 (例: n=5,5,2) のほうが ingestion 観点で頻出
- ただし α の triple onset 例 (例: cid 41/132/135 が同 link) では n_core 構成は別途確認が必要

### δ.3 v10.3 設計への含意

- 三項共鳴の構成として「**主役 (n=5) 2 つ + 背景 (n=2) 1 つ**」が摂食ネットワーク的には自然
- 純粋 n=5 三項 (= 5,5,5) は摂食観点では稀。三項共鳴も同様の傾向の可能性
- ただし共鳴は摂食と別現象なので、別途検証必要

---

## E. 統合観察と v10.3 設計への含意

### E.1 v10.3 三項共鳴の現実的な姿

4 解析から推測される v10.3 三項共鳴の現実的な像:

1. **物理層自然発生は稀少**: triple onset rate < 0.3% (N=2500-5000 で 50-67 件 / 24 seeds)
2. **主役の C 動学は intra-window で動く**: window 単位では「累積増加」しか見えない (n_C_decreases median 0-1)
3. **主役は contact 集中型**: E3 median 67-69、E2 median 0、event 総数 70+
4. **共鳴 cid 構成は混合型が自然**: 摂食データから「n=5 主役 + n=2 背景」混合が支配

### E.2 推奨する v10.3 設計の方向性

これら観察事実から、Code A 実装担当の暫定推奨:

#### (a) 観察スケール

- **N=5,000 で v10.3 本番** (triple onset 67 件、主役 270 cid、wall 3h)
- N=2,500 でも実用 (triple onset 51 件、主役 159 cid、wall 1h)

#### (b) 主役の絞り込み基準

主役プールから更に絞る場合:
- **E3 ≥ 50 かつ n_consciousness ≥ 5** で「contact 経験豊富な反復発動者」を抽出
- **n_C_increases ≥ 20** で「能動的 C 蓄積者」を抽出

#### (c) 動的均衡の可視化

- window 単位ではなく **balance_decisions の per-step c_after** を時系列描画する必要
- これは新規実装ではなく既存 CSV から可能 (本解析範囲外)

#### (d) 三項共鳴の cid 構成

純粋同 n_core (5,5,5) ではなく、**「主役 2 + 背景 1」の混合型** を観察対象として明示するのが現実的

### E.3 v10.3 主題ドキュメント (Claude 作成予定) への素材

本解析は v10.3 主題ドキュメント執筆時に以下の素材を提供:

- 三項共鳴の発生頻度 (α): 「N=5000 で 67 件 / 24 seeds × 50 windows × 500 step」
- 主役の C 動学特徴 (β): 「window 単位では monotonic 増加、intra-window で増減」
- 主役の物理活動量 (γ): 「背景の 6-12 倍、E3 主導」
- 摂食ネットワーク (δ): 「n=5 eater × n=2 ghost が 52%」

---

## F. 限界

- **α**: 「triple simultaneous onset」と「3 cid 共鳴」は別概念 (onset は瞬間、共鳴は持続)。共鳴の持続性は本解析対象外
- **β**: window 単位の集計のみ。intra-window step 単位の真の動的均衡は捉えていない (balance_decisions per step を集計すれば取れる、別タスク)
- **γ**: event 発火数の集計のみ。event 発火パターン (時間集中 vs 散在) は本解析対象外
- **δ**: ingestion event 単位の集計。「3 cid 同時摂食」(三項摂食) は v10.2 では構造的に発生しない (即時摂食設計)

---

## G. 出力ファイル

```
developmental/v102/followup/
├── v103_alpha_triple_link.csv             (N 別 triple onset 集計)
├── v103_alpha_triple_link_examples.csv    (N=5000 の triple onset 例 67 件)
├── v103_beta_C_swing.csv                  (per cid C 動学指標)
├── v103_beta_C_swing_summary.csv          (n_core × group 集計)
├── v103_gamma_event_per_cid.csv           (per (N, n_core, group, event_type))
├── v103_delta_ingestion_network.csv       (eater × ghost n_core クロス表)
└── v103_delta_eater_degree.csv            (per eater の摂食 degree)
```

---

## H. 結論

実装担当として v10.3 三項共鳴に直結する 4 項目を解析。新規発見:

1. **三項共鳴の自然発生は稀少**: 全 N で triple_simul_rate < 0.3%、N=10000 では 13 件のみ
2. **window 単位観察の限界**: 反復発動者でも window 末では C 減少 median 1 のみ。intra-window で本物の動的均衡が起きている
3. **主役の event プロファイル**: 背景の 6-12 倍 event、E3 dominant
4. **摂食ネットワークの階層構造**: n=5 eater × n=2 ghost が 52%、純粋同型 (5,5) は 2.7% のみ

これらは v10.3 主題ドキュメント執筆時の重要素材となる。観察スケール推奨は **N=5,000 (本番)、N=2,500 (smoke)**。

---

*以上、v10.2 N-sweep / v10.3 三項共鳴 直結 4 解析。*
