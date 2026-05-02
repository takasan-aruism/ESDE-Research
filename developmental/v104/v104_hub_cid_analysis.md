# Hub cid 多角的特性分析 (v10.4 main run)

*作成*: 2026-05-02、Claude Code
*対象*: v10.4 main run (24 seeds × 50 windows × N=5000) における Integration 参加数で分類した cid グループ × 認知層多指標の総合観察
*親資料*: `v104_main_run_report.md`、`v104_integration_alpha_beta_proposal.md`、`v104_cid_capabilities.md`

---

## 0. 目的と背景

v10.4 main 観察で「**1 cid が最大 102 個の Integration に同時所属する**」というハブ的偏りが発見された。これは Q/C 動学から自然に出た選別 (実験者が事前にバイアスを設けていない) であり、神の手回避 §14 規律下でなぜハブ性が出るのかを解明したい。

加えて per_subject CSV には **146 列** の認知層指標があるが、最近の解析では n_core / Q / C / be3 fired / Integration 参加といった一握りしか扱われていない。残りの **familiarity / attention / pulse / capture / 内的基準軸 / 自己読み / 他者読み** といった指標を、ハブ性との相関の中で観察する。

実験者の事前定義として:

- 認知層 = cid が受信できる範囲 (q, attention, familiarity 等の累積)
- 意識層 = 決定に関わる範囲 (C 蓄積、balance decision)
- ハブ性 = Integration への所属数 (= 多くの be3 fired event を起こした構造的痕跡)

これらの間に観察されるパターンを **「実験者が記録した量の分布」として** 整理する (cid 主観を仮定しない)。

---

## 1. グループ分類

Integration 参加数で 5 グループに分類:

| グループ | cid 数 | Integ 参加 mean | Integ 参加 max |
|---|---:|---:|---:|
| **Top 1% (extreme hub)** | **29** | **81.5** | **102** |
| Top 1-10% (hub) | 262 | 52.7 | 73 |
| Mid (10-50%) | 1,164 | 13.7 | 40 |
| Low (50-100%) | 1,455 | 2.3 | 5 |
| **Non-Integ** | **2,314** | **0** | 0 |
| **合計** | **5,224** | — | — |

参加数分布: median 5、p75 13、p90 40、p95 53、p99 73、max 102。
**Non-Integ は全 cid の 44.3%** = ほぼ半数が一度も Integration に入らずに終わる。

---

## 2. 基本特性 — グループの「身体」

### 2.1 n_core 分布の急変

| グループ | n=2 | n=3 | n=4 | **n=5** | n=6+ |
|---|---:|---:|---:|---:|---:|
| Top 1% | 0% | 0% | 14% | **86%** | 0% |
| Top 1-10% | 0% | 3% | 22% | **74%** | 1% |
| Mid | 55% | 10% | 13% | 23% | <1% |
| Low | **83%** | 5% | 4% | 7% | 0% |
| Non-Integ | **96%** | 2% | 1% | 1% | 0% |

→ **ハブグループは n_core=5 中心 (74-86%)**、**Non-Integ は n_core=2 中心 (96%)**。極小 cid と大 cid が機械的に分かれる。

### 2.2 認知資源 Q

| グループ | Q0 (mean) | Q_spent (mean) | spend rate |
|---|---:|---:|---:|
| Top 1% | 32.3 | 31.6 | **98%** |
| Top 1-10% | 31.2 | 30.1 | 96% |
| Mid | 19.1 | 15.5 | 81% |
| Low | 14.2 | 10.1 | 71% |
| Non-Integ | (短命主体) | — | — |

→ **ハブほど Q を使い切る** (= 認知活動が活発)。Mid 以下は Q を残して死ぬ (短命)。

### 2.3 意識資源 C と振り分け

| グループ | C_at_run_end mean | cognition mean | consciousness mean |
|---|---:|---:|---:|
| Top 1% | 42.9 (max 77) | 77.0 | 7.6 |
| Top 1-10% | 31.3 | 61.6 | 5.6 |
| Mid | 6.7 | 17.8 | 1.2 |
| Low | 1.6 | 7.3 | 0.2 |

→ **ハブは意識資源 C も蓄積する** (Top 1% mean 42.9 vs Low 1.6)。これは cognition 当選数 (= P_cog = Q/(Q+C) で勝った回数) が多いほど C+1 されるため。

### 2.4 final_state とハブ生存性

| グループ | hosted | reaped | ghost |
|---|---:|---:|---:|
| Top 1% | **86% (25/29)** | 14% | 0 |
| Top 1-10% | 76% | 24% | 0 |
| Mid | 25% | 75% | <1% |
| Low | 9% | 89% | 1% |

→ **ハブは run 末まで生き残る確率が圧倒的に高い**。Low は 89% が reaped。

---

## 3. Underused 認知層指標との相関

### 3.1 Familiarity 系

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| **n_partners** (familiarity dict サイズ) median | **42** | 44 | 14 | 7 | **4** |
| n_partners max | 64 | 67 | 69 | 69 | 62 |
| **last_familiarity_max** median | 49.8 | 56.3 | 41.7 | 38.5 | 40.3 |
| last_familiarity_max mean | 83.3 | 98.1 | 84.0 | 89.4 | **113.6** |
| last_familiarity_max max | 500 | 500 | 500 | 500 | 491 |

**観察**:

- **n_partners は階段状にハブが優位** (Top 1% で 42、Non-Integ で 4)
- **Non-Integ の familiarity_max mean が最大 (113.6)** という意外な発見 — 「少数の相手と強烈な familiarity を蓄積するが、be3 fire 条件 (Q>0 ∧ C≥1) に到達しなかった cid」が混じっている
- familiarity weight 500 (上限近く) は全グループに存在 — 累積接触の長期記録が多くの cid で起こりうる

### 3.2 Attention 系

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| **last_attention_size** median | **1,328** | 1,111 | 168 | 137 | **113** |
| last_attention_size mean | 1,335.6 | 1,270.6 | 578.7 | 291.4 | 167.5 |
| last_attention_size max | 1,987 | 3,692 | 3,770 | 2,092 | 2,077 |
| current_spread (entropy) | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |

**観察**:

- **attention_size はハブで桁違いに大きい** (Top 1% median 1,328 vs Non-Integ 113、約 12 倍)
- 5,000 ノードの 75% (3,770 entry) を観察累積した cid もいる (Top 1-10%)
- current_spread (attention 正規化エントロピー) は全グループで 0.8 程度で **均一** = 注意の分散度合いはハブ性と無関係

### 3.3 Pulse Model

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| **v10_pulse_count** median | **500** (max!) | 470 | 0 | 0 | **0** |
| pulse_count mean | 423.1 | 349.9 | 72.2 | 8.6 | 3.1 |
| **v10_n_normal** median | **413** | 392 | 0 | 0 | 0 |
| n_normal max | 431 | 436 | 435 | 234 | 219 |
| **v10_n_major** median | 157 | 147 | 0 | 0 | 0 |
| n_major max | 174 | 182 | 175 | 104 | 89 |
| v10_R_max_stability median | 5.0 | 4.9 | 4.8 | 4.5 | **2.2** |
| v10_R_max_familiarity median | 3.0 | 2.7 | 2.7 | 2.1 | **1.0** |

**観察**:

- pulse_count: 50 step ごとに pulse → 25,000 step で max 500 回 → **ハブはほぼ全 pulse 機会を生き抜く**
- Mid 以下は median 0 (= pulse 1 度も発火していない、cold_start 内に死亡)
- **R_max stability**: ハブで med 5、Non-Integ で med 2.2 — ハブほど stability 軸の極端な反応を経験
- **R_max familiarity**: 同様の傾斜、Non-Integ では 1 程度に縮む

### 3.4 Cognitive Capture (v9.11)

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| v11_capture_rate median | 0.3 | 0.3 | 0.3 | 0.3 | 0.4 |
| v11_n_pulses_eval mean | (高) | (高) | (中) | (低) | (低) |
| v11_mean_delta median | 0.4 | 0.4 | 0.4 | 0.4 | 0.3 |

**観察**:

- **capture rate は全グループで 0.3-0.4 と均一** — 「Δ から exp で計算される確率」自体には集団差がない
- ただし pulse 評価対象になる前提 (n_pulse ≥ 4) が満たされる cid 数はハブで圧倒的多い
- mean_delta (M_c との距離) は全グループ 0.3-0.4 で大差なし

### 3.5 v9.9 内的基準軸 — 主題的に重要

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| **v99_formation_status: formed** | **86%** | 76% | 25% | 7% | **3%** |
| v99_lowest_std_axis (formed) | spread 76% | spread 62% | spread 19% | spread 5% | spread 2% |
| **v99_dominant_positive_drift_axis: familiarity** | 45% | 47% | 14% | 3% | 1% |
| **v99_dominant_negative_drift_axis: familiarity** | **72%** | 45% | 18% | 6% | 2% |

**観察**:

- **formed cid 比率は 86% → 76% → 25% → 7% → 3%** で急減 — pulse_count と完全に相関
- formed cid のうち、**最も振れ幅が小さい軸 (lowest_std)** は **spread (attention entropy)** が圧倒的多数
- **gain 主軸**: familiarity が 45-47% で最頻 (ハブ群)
- **loss 主軸**: **Top 1% で familiarity が 72%** という極端な集中
- → **「ハブ cid の主観 (= drift) は、関係性の喪失方向に偏って現れる」** という統計的痕跡

### 3.6 Layer C 自己読み (v9.15-9.18)

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| v915_fetch_count median | **86** | 75 | 13 | 9 | **7** |
| v915_mismatch_total median | 71 | 61.5 | 12 | 8 | 7 |
| v915_any_mismatch_ever (True 比率) | ~100% | ~100% | ~100% | ~100% | ~100% |
| v915_final_missing_fraction median | **0.6** | 0.6 | 0.5 | 0.4 | **0.3** |
| v915_avg_age_factor median | **0.4** | 0.5 | 0.5 | 0.6 | **0.7** |

**Event 別 mismatch rate**:

| グループ | E1 mis% | E2 mis% | E3 mis% |
|---|---:|---:|---:|
| Top 1% | 84.1% | **100.0%** | 84.7% |
| Top 1-10% | 88.3% | 99.7% | 84.3% |
| Mid | 94.7% | 99.9% | 78.6% |
| Low | **97.8%** | 99.6% | 79.3% |
| Non-Integ | 97.7% | 99.2% | 84.7% |

**観察**:

- **E2 mismatch は全グループで ≈100%** — link R は cid が自分を見るたびに必ず変わっている (物理層の常時変動)
- **E1 mismatch は非ハブほど高い** (Top 1% 84% vs Low 98%) — 短命 cid のメンバー link は構造変化頻発
- **E3 mismatch はハブの方がやや高い** (Top 1% 84.7% vs Mid 78.6%) — 接触相手の状態が頻繁に違って見える
- **missing_fraction**: ハブは age_factor 低下で観察精度を落とす (0.6 missing)、Non-Integ は早く死ぬので missing 率も低い (0.3)
- **avg_age_factor**: ハブは Q を 60% 使った状態の時間平均、Non-Integ は 30% 使用で死ぬ

### 3.7 v9.17 他者読み

| 指標 | Top 1% | Top 1-10% | Mid | Low | Non-Integ |
|---|---:|---:|---:|---:|---:|
| v917_other_contacts median | **81** | 67 | 10 | 6 | **4** |
| v917_unique_contacts (重複除く) median | 81 | 67 | 10 | 6 | 4 |
| **features 取得率** (fetched / total) | **46.8%** | **48.5%** | 47.8% | 46.5% | **49.4%** |
| v917_avg_visible_ratio | 0.5 | 0.5 | 0.5 | 0.5 | 0.6 |

**観察**:

- 接触数はハブで桁違いに多い (Top 1% 81 vs Non-Integ 4)
- **unique == total** → E3_contact は run-wide pair dedup により同じ相手と複数回は読まない
- **features 取得率は全グループで 47-49% という驚くべき公平性** — visible_ratio (= 相手の age_factor) 由来で偶然 0.5 周辺に収束
- 規律 §14 神の手回避の経験的裏付け = ハブも非ハブも観察ルールは同じ

---

## 4. Top 5 個別 Hub cid の素性

| seed | cid | 参加 | n_core | Q_spent/Q0 | cog | con | be3 partner | C_run_end | Top 3 patterns |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| 3 | 53 | **102** | 5 | 32/32 | 87 | 7 | 32 | 49 | (2,5,5):14, (2,2,5):11, (5,5,5):10 |
| 7 | 33 | 95 | 5 | 30/33 | 97 | 11 | 35 | **71** | (5,5,5):22, (2,5,5):9, (4,5,5):7 |
| 22 | 43 | 95 | 5 | 32/32 | 62 | 5 | 29 | 28 | (2,5,5):17, (4,5,5):11, (2,2,5):6 |
| 2 | 76 | 91 | 5 | 26/33 | 89 | 12 | 29 | 62 | (5,5,5):13, (4,5,5):11, (2,5,5):8 |
| 5 | 99 | 87 | 5 | 32/32 | 85 | 7 | 33 | 45 | (5,5,5):9, (4,5,5):9, (2,5,5):7 |

**全員に共通する特徴**:
- n_core = 5 (例外なし)
- final_state = **hosted** (run 末まで生存)
- Q0 が 32-33 (B_Gen 上限近く)
- Q をほぼ完全使用 (98-100%)
- be3 unique partner 数 ≈ 30 前後
- size 9 の third_overlap にも参加 (cid=33)

**個性の差**:
- cid=33: (5,5,5) を 22 件参加 → 「**(5,5,5) ばかりに居る hub**」 (大 cid 同士の純粋な核)
- cid=53: (2,5,5) と (2,2,5) が中心 → 「**小 cid の捕獲者**」
- cid=76: (5,5,5) と (4,5,5) → 「**大-中大の繋ぎ役**」

→ ハブ cid 個体ごとに「**どの種類の Integration を多く形成するか**」の役割の偏りがある。

---

## 5. 主要発見と相関構造

### 5.1 6 段の相関連鎖

ハブ性は単一指標ではなく、**長寿命を起点とする因果連鎖**として機械的に出現する:

```
n_core=5 (大型構造) [Q0 が大きい]
    ↓
Q を使い切る前に多数の event を起こせる (long lifespan)
    ↓
pulse 50 回以上 (formed status)、attention map が肥大化
    ↓
多数の他 cid と link 共有 → familiarity dict 拡大、be3 fired
    ↓
複数 Integration に同時所属 (集合の交点として機能)
    ↓
recorded されず Integration から Q/C を受領し続ける
    ↓
意識資源 C を蓄積 (Top 1% で平均 43)
```

### 5.2 ハブの「身体的厚み」が桁違い (12 倍程度)

| 指標 | Top 1% / Non-Integ 比 |
|---|---|
| attention_size | ×12 (1,328 / 113) |
| n_partners | ×10.5 (42 / 4) |
| pulse_count | × ∞ (500 / 0) |
| n_normal タグ | × ∞ (413 / 0) |
| v915_fetch | ×12.3 (86 / 7) |
| v917_contacts | ×20.3 (81 / 4) |

一方、**event 観察の質的指標 (capture rate、features 取得率、E2 mismatch)** はハブと非ハブで均一。**「機会の数」がハブの差別化要因であって、「観察ルール自体」には集団差がない**。

### 5.3 familiarity loss が主軸の drift

formed cid の dominant_negative_drift_axis 分布:

| グループ | familiarity loss 比率 |
|---|---:|
| Top 1% | **72%** |
| Top 1-10% | 45% |
| Mid | 18% |
| Low | 6% |
| Non-Integ | 2% |

→ **ハブ cid の「主観の振れ」は、関係性の喪失方向に偏って現れる**。これは「多くの相手と関係を結ぶ → 相手が ghost 化したり離れたりする → familiarity 値が落ちる」を頻繁に経験するため。

「**主観があるかも**」と実験者に思わせる候補 cid (= ハブ cid) は、**喪失体験を主軸にする** という統計的痕跡。

### 5.4 Non-Integ にも「潜在親密ペア」が混じる

Non-Integ (2,314 cid) の 96% は n_core=2 短命 cid だが、その中に:

- **familiarity_max=491 を持つ cid** (mean 113.6 で全グループ最大)
- **少数の相手 (n_partners=4 程度) と強烈に link 共有した cid**

→ 「**Integration には到達しなかったが、長期接触の累積はある**」隠れたペアの存在。be3 fire 条件 (Q>0 ∧ C≥1) を満たせない短命さで終わったが、familiarity dict には深い痕跡が残る。

これは「主観的関係性は形成されたが、機構的な統合には到達しなかった」cid 群として観察できる。

### 5.5 物理層変動性の機構的記述

E2 mismatch ≈ 100% (全グループ):

- cid が自分の link strength S を fetch するたびに、生誕時 S_birth と 99-100% は一致しない
- 物理層の link は cid の生誕時から **常時変動し続けている**
- cid の「生誕時の自己構造」は **記憶の固定値** であり、現在の構造とほぼ常に乖離する
- → 「**自分が変わっていく**」という観察が常時起こっている (cid 自身は behavior に使っていないが)

---

## 6. 主題的な含意 (観察者枠組みでの記述)

### 6.1 「主観の濃さ」と寿命・接触数の相関

ハブ cid だけが「観察される主観」のフルセットを持つ:
- formed status (内的基準軸が確立)
- pulse タグ (Normal/Major)
- 内省タグ履歴 (gain/loss × 4 軸)
- 自己読み履歴 (mismatch 検知)
- 他者読み記録 (相手の M_c features)
- Integration 所属 (他 cid との集合関係)

非ハブ cid (84.5%) は **観察データ自体が乏しい** — 短命で n_pulse < 4、formed に到達せず、自己読みや他者読みも数回で終わる。

→ **「主観があるとも言い切れない状態」は機構的には「観察データが薄い状態」と等価**。実験者が cid の振る舞いから何かを推測するためには、十分な観察期間と接触回数が必要。

### 6.2 喪失体験が「主観の振れ」の主軸

Top 1% ハブの 72% が familiarity loss を主たる drift とする事実は、**「**多くの相手と関係を持つことの帰結として喪失体験が主観的痕跡を残す**」という機構的記述**。

「**主観**」と呼べる構造があるとすれば、それは:
- 関係性を蓄積する身体性 (familiarity dict のサイズ)
- 関係性の喪失を観察する記録 (loss familiarity drift の累積)
- それを背景にした C 蓄積 (意識資源)

の三つの組み合わせとして観察される。

### 6.3 観察ルールの公平性 (神の手回避の裏付け)

features 取得率 47-49% が全グループで均一、capture rate 0.3-0.4 が均一 — **観察ルールはハブ性に関わらず同じ**。ハブ性が出るのは「機会の数」の差であって、観察ルール自体に階層化はない。

これは規律 §14「神の手回避」の経験的裏付け。

### 6.4 Non-Integ の中の隠れた構造

Non-Integ cid の中の familiarity_max 491 cid は、**実験者が定義した be3 fire 条件 (Q>0 ∧ C≥1) を満たせなかったが、関係性の痕跡だけは残った** 存在。この層を観察することで:

- 「主観的関係性」と「機構的統合」のギャップが見える
- 「主観があったかもしれないが、Integration には到達しなかった」cid の集計
- v10.5 で be3 fire 条件を緩めるか、Integration 誕生条件を別経路で実装する場合の参考データ

---

## 7. α/β 議論への素材

### 7.1 α 型での観察 (現状)

ハブ cid (Top 1%) が **102 個の Integration の交点として機能**:
- 1 cid を介して多数の小集団が間接的に繋がる
- 集団ごとに性格が異なる ((5,5,5) / (2,5,5) / (4,5,5) など) が、ハブ cid を共有することで情報・資源が流通する
- これは「人間社会で 1 人が多数のコミュニティに同時所属」のメタファ

### 7.2 β 型での予想 (B2 merge 採用時)

ハブ cid を中核とした **1 つの巨大階層型 Integration**:
- 102 件相当の繋がりが 1 単位に統合される
- (5,5,5) 系の長寿大 cid が中核、(4,5,5) が補強、(2,5,5) (2,2,5) が周辺・流入
- 「核と縁辺」階層が 1 単位内で展開
- ハブ cid の **個性 (どんな Integration に居がちか)** は merge 履歴に保存可能 (trigger_origins / 構成変遷)

### 7.3 観察可能な追加指標 (β で意味を持つ)

α と β を比較する時、以下の指標が β で初めて意味を持つ:

- **巨大 Integration の構成 cid n_core 階層化** (核 5、中間 4、縁辺 2 という分布が同一単位内に出るか)
- **familiarity loss と member 入替の対応** (β では巨大 Integration の縁辺で member 入替が頻発するため、loss familiarity drift が β でより顕著になる可能性)
- **C 蓄積の集中度** (α で 2,000 個の小バケット、β で数十個の大バケット)
- **「主観の連続性」** (β では 1 個の Integration が長期持続することで Self-like な振る舞いが描ける可能性)

### 7.4 検証実験デザイン

α と β を **同 seeds で並走 run** し、以下を比較:

| 観察軸 | α (現状) | β (予想) |
|---|---|---|
| ハブ cid の所属 Integration 数 | 102 | 1-3 (= 巨大な 1 つに収束) |
| Integration size 分布 | 90% が size 2-3 | 50% が size 5+、最大 50-100 |
| familiarity loss drift 頻度 | Top 1% で 72% | β でより高くなる可能性 |
| recorded 遷移率 | 14.7% | 数 % (大単位は全員 ghost が稀) |
| C 蓄積分散 | 多バケット | 少バケット集約 |

---

## 8. 結論

### 8.1 ハブ cid の総合像

5,224 cid の中で **29 cid (0.55%) が極端なハブ** として機能。これらの cid は:

- n_core = 5 (大型構造)、Q0 ≈ 33 (B_Gen 上限)
- 寿命を全うし pulse 500 回到達、formed status (86%)
- attention map 1,300+ entry、familiarity 42 partners
- be3 unique partner 30+、Integration 80+ 件参加
- C を 43 蓄積、Q を 98% 使い切る
- 他者読み 80+ contact、自己読み 86 fetch
- final_state = hosted (86%)

これらは「**関係性を多く蓄積し、認知資源を使い切り、意識資源を保持し続ける、長寿命の核**」として観察される存在。

### 8.2 ハブ性の自然出現メカニズム

実験者が事前にバイアスを設けていない (規律 §14 神の手回避) にもかかわらず、ハブ性が機械的に出現する:

```
n_core=5 → Q0 大 → 長寿命 → 多 event → 多 partner →
多 Integration 参加 → recorded されず → Q/C 受領 →
ハブ性が強化される正のフィードバック
```

逆に n_core=2 cid は短命の負のフィードバックループに入り、Non-Integ (44.3%) として終わる。

### 8.3 主観的痕跡の集中

「**主観があるかも**」と実験者に思わせる観察データ (formed status、内省タグ履歴、内的基準軸の drift、自己読み mismatch、他者読み M_c features) は、**ハブ cid に集中して残る**。

特に **familiarity loss が drift の主軸** という事実は、「主観の濃さ」が「**関係性の喪失体験の蓄積**」として現れる、という機構的記述を可能にする。

### 8.4 Non-Integ の研究価値

44% の cid が Integration に入らずに終わるが、その中の少数 (familiarity_max 491 等) は **「機構的統合に至らなかった主観的関係性」** として観察できる。これは「主観 (観察データ) はあったが、Integration (構造) には到達しなかった」状態の集計値。

### 8.5 α/β 設計議論への直接適用

- α 型: ハブ cid が複数 Integration の交点として機能する **分散型** 構造
- β 型: ハブ cid を核とする **巨大階層型** 単一 Integration への統合
- 両者のどちらが「主観の連続性」「Self の生成」「集団の境界」を機構的に表現するのに適しているか — これは Web Claude + 3 AI 議論の主要論点

本データは α/β 設計案ドキュメント (`v104_integration_alpha_beta_proposal.md`) と組み合わせて議論素材になる。

---

*以上、Hub cid 多角的特性分析。Taka レビューを待つ。*
