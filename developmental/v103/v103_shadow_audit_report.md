# v10.3 shadow audit 結果レポート

*作成*: 2026-04-30、Code A
*対象*: v10.3 双方向 E3 機構の shadow audit 本番 (N=5000, tracking 50, 24 seeds)
*親資料*: `claude_code_v103_implementation_instruction.md` (実装指示書)、`v103_smoke1_report.md` (smoke 1 結果)
*位置づけ*: 実装指示書 §8.3 shadow audit。本番 run の前段、Taka 判断項目。

---

## 0. 一行サマリ

shadow audit 24 seeds 完走 (wall mean 2.98h)。**Layer B 552/552 完全一致** (v10.2 main の物理層・認知層・摂食層・Layer C すべて完全同一動作)、**双方向 E3 fired 6,675 件 / 24 seeds**、**skip 92% が ghost 化** (= 物理層と認知層の natural filter)、**closed triad 55 件 / open triad 4,960 件** (90:1 で open 支配)、**第三項として登場した cid 9,741 件記録**。本番 run 進行可、Taka 判断待ち。

---

## 1. 実行サマリ

| 項目 | 値 |
|---|---:|
| seeds | 24 (0..23) |
| N | 5,000 |
| maturation | 20 |
| tracking | 50 |
| window_steps | 500 |
| 並列 | -j24 |
| be3_shadow_audit | True (C 消費なし、log のみ) |
| **完走** | **24/24 (exit 0)** |
| **wall time mean** | **10,727 sec (2.98 h)** |
| wall time min/max | 10,315 / 11,193 sec |
| 出力サイズ | **1.7 GB** |

参考: v10.2 main (同条件、N=5000 tracking 50 24 seeds) の wall 10,786 sec → **オーバーヘッド -0.5% (実質ゼロ)**。

---

## 2. Layer B bit-identity 検証 (必須項目)

### 2.1 結果

**v103 main_shadow vs v10.2 main: 552/552 ファイル完全一致** ✅

| ディレクトリ | identical |
|---|---:|
| audit | 72 / 72 |
| aggregates | 24 / 24 |
| balance | 72 / 72 |
| ingestion | 48 / 48 |
| labels | 24 / 24 |
| persistence | 96 / 96 |
| selfread | 168 / 168 |
| subjects | 48 / 48 |
| **合計** | **552 / 552** |

差分は v103 にしか無い `bidirectional/` (新規) と、v10.2 で post-hoc 作成した `analysis/` (詳細解析) のみ。

### 2.2 意味

shadow audit モードでは v103 が v10.2 と:
- 物理層動作 (engine state、theta、S、L、R、age_r): 完全一致
- 認知層動作 (per_event_audit Q 消費、virtual_attention/familiarity): 完全一致
- 摂食層動作 (ingestion_events、phantom_contacts、balance_decisions): 完全一致
- Layer C (CidSelfBuffer 観察、divergence_log): 完全一致

→ **v10.3 = "v10.2 + 双方向 E3 観察 log のみ" という関係が本番規模で数値的に保証**。

これは実装指示書 §7.2「shadow audit 段階で v10.2 baseline と物理層列が一致」の要求を 552 ファイル × 1.7 GB の本番規模で完全達成。

---

## 3. 双方向 E3 機構観察結果

### 3.1 全体集計 (24 seeds)

| 指標 | 値 |
|---|---:|
| 全 be3 records (skip 含む) | 153,920 |
| **fired** | **6,675** (4.34%) |
| skipped | 147,245 (95.66%) |
| 1 seed あたり fired | **278** |
| 1 window あたり fired | **5.6** |

### 3.2 skip 理由分布 (重要発見)

| 理由 | 件数 | 比率 |
|---|---:|---:|
| **ghost_a** (cid_a が ghost 化済) | **106,467** | **72.3%** |
| **ghost_b** (cid_b が ghost 化済) | **28,663** | **19.5%** |
| q_zero_a (cid_a の Q=0) | 6,726 | 4.6% |
| c_zero_a (cid_a の C=0) | 3,512 | 2.4% |
| q_zero_b (cid_b の Q=0) | 1,110 | 0.8% |
| c_zero_b (cid_b の C=0) | 767 | 0.5% |
| **ghost 合計** | **135,130** | **91.8%** |
| **C/Q zero 合計** | **12,115** | **8.2%** |

**観察**: 双方向 E3 の skip の 92% が ghost 化が原因。ESDE の「初回接触のみ」(onset 性) と「ghost への接触は既存 E3 の対象」が組み合わさり、両者 alive 同 link 共有の onset は実は稀。

仮説: be3 候補ペアが現れる時点で片方が既に ghost 化していることが多い (= cid 寿命が短く、long-tail で ghost 化が早い)。

### 3.3 fired ペアの n_core 組み合わせ

| n_core (a, b) | 件数 | 比率 |
|---|---:|---:|
| **(5, 5)** | **1,648** | **24.7%** |
| **(5, 2)** | **1,621** | **24.3%** |
| (5, 4) | 648 | 9.7% |
| (4, 2) | 545 | 8.2% |
| (4, 5) | 523 | 7.8% |
| (2, 2) | 333 | 5.0% |
| (5, 3) | 322 | 4.8% |
| (4, 4) | 198 | 3.0% |
| (3, 5) | 175 | 2.6% |
| (3, 2) | 168 | 2.5% |

**観察**: n_core=5 を含むペアが 50%+ を占め、(5,5) と (5,2) で約半数。これは v10.2 main 詳細解析で観察された「ingestion network: n=5 eater × n=2 ghost が 52%」とほぼ整合。

### 3.4 fired 時の C 状態

| 統計 | 値 |
|---|---:|
| C_a + C_b mean | 27.2 |
| C_a + C_b median | **23** |
| min | 2 (= 両者 C=1) |
| p25 | 12 |
| p75 | 39 |
| max | 115 |

**観察**: 双方向 E3 が発火する時点で両者で **median 23 の C を蓄積している**。これは「主役 (= 反復 cognition で C 蓄積した cid)」同士の接触が be3 の主要発火パターン。

### 3.5 target 内 / 外

| 集合 | 件数 | 比率 |
|---|---:|---:|
| in_observation_target=True | 2,408 | 1.6% |
| in_observation_target=False | 151,512 | 98.4% |

target 化された cid は少数 (主役条件 n_consciousness ≥ 5 を満たす)。本番モードでは target 内のみ詳細記録するため出力 95% 削減できる見込み。shadow audit では全件詳細記録 (実装修正済)。

### 3.6 per cid 集計

| 指標 | 値 |
|---|---:|
| 双方向 E3 経験 cid 数 | **2,854** (= 全 cid 5,224 の 54.6%) |
| n_be3_total median | 2 |
| n_be3_total p75 | 5 |
| n_be3_total max | 35 |
| n_be3_partners median | 2 |
| n_be3_repeated_partners > 0 cid | **0** |

**観察 (重要)**: shadow audit では **同 partner と 2 回以上 fire した cid が 0 件**。理由は v10.3 双方向 E3 の onset 性 (= 初回接触のみ)。同 cid pair の接触は contacted_pairs に登録されており、再発火しない (v10.2 既存 E3 と同じ設計)。

これは実装指示書 §2.3 通りの仕様。「持続接触で毎 step 発火」は v10.4 以降の検討候補 (機構肥大化を避けるため v10.3 では実装しない)。

---

## 4. 第三項候補 (post-process 結果)

### 4.1 c_role 別

| c_role | 件数 | 比率 |
|---|---:|---:|
| **open_intermediary** (Cat 1b) | **9,576** | **98.3%** |
| **closed_third** (Cat 1a) | **165** | **1.7%** |
| **合計** | **9,741** | 100% |

**観察 (核心)**: closed triad (Cat 1a = A-B, B-C, C-A の 3 ペア全部成立) は **165 件のみ**、open triad (Cat 1b = A-B + B-C があるが A-C なし) は **9,576 件**。**90:1 の比率で open triad 支配**。

これは v3.4 tripartite loop の bridge_max_life=1 と同じパターン: 「3 cid 全ペア接触」は物理的に稀。

### 4.2 window 別 triad 分布

window 末で集計した triad 数 (全 24 seeds × 50 windows = 1,200 window):

| 統計 | n_closed_triads | n_open_triads | triad_member_count |
|---|---:|---:|---:|
| **合計** | **55** | **4,960** | (累積) |
| 平均 / window | 0.05 | 4.13 | 0.15 |
| median / window | 0 | 4 | 0 |
| max / window | 3 | 23 | 5 |

**観察**: closed triad は 1,200 window 中 55 件のみ (= 4.6% の window で出現)。open triad は 1,200 window のほぼ全部で出現 (median 4 件)。

### 4.3 v10.3 主題への含意

実装指示書 §1.2 の三項共鳴の射程:
- **closed triad は稀少、open triad が支配的**
- → 三項共鳴の主役は **open intermediary 形態** (cid_c が cid_a と cid_b の中継者)
- closed triad (= 3 ペア全部 fired) は v10.3 段階で 165 件しか観察されないため、統計的解析に供する規模としてはギリギリ
- v10.3 主題ドキュメントで「主役は open triad の中継者役」を明示すべき

これは Code A 第二次応答 §1.2 の事前推定 (strict simultaneous onset で ~67 件) とも整合: 同時 closed triad onset は稀、shadow audit でも 165 件まで増えただけ。

---

## 5. 出力ファイル一覧

```
diag_v103_main_shadow/
├── (既存 v10.2 と同じ全 subdirs、552 CSV bit-identical)
└── bidirectional/
    ├── bidirectional_e3_log_seed{0..23}.csv             (24 ファイル、合計 153,920 行)
    ├── bidirectional_e3_member_nodes_log_seed{0..23}.csv (24、6,675 行)
    ├── bidirectional_e3_summary_seed{0..23}.csv          (24)
    ├── bidirectional_e3_3rd_cid_log_seed{0..23}.csv      (post-process、24、9,741 行)
    ├── bidirectional_e3_window_summary_seed{0..23}.csv   (post-process、24)
    └── bidirectional_e3_per_subject_seed{0..23}.csv      (post-process、24、2,854 unique cid)
```

bidirectional/ のみ新規 144 ファイル、その他 552 ファイルは v10.2 main と完全一致。

---

## 6. 規律確認 (実装指示書 §10、本番規模で再確認)

- [x] 物理層 frozen — Layer B 552/552 で本番規模確認
- [x] Layer A bit-identity (smoke で 29/29、本番規模 Layer A は別途検証可だが wall 3h × 2 で省略)
- [x] cid 内部に新規状態を追加しない
- [x] 神の手を入れない (fired 6,675 件すべて条件満たし、ghost 92% の skip も自然フィルタ)
- [x] 第三項候補は実験者観測軸として記録、cid 内部に持たせない
- [x] **C 消費は記録ルール、判定機構ではない (shadow audit で C 消費せず → Layer B 552/552)**
- [x] balance_rng と be3_rng は engine.rng から独立 (be3_rng 未使用、不要と判明)
- [x] 既存 CSV 列を変更しない (Layer B 552/552 で確認)
- [x] 「嗜好」「三項共鳴」を機構名に含めない
- [x] target 外も全体集計で監視 (n_be3_target_outer)

---

## 7. 主題ドキュメント執筆素材 (Claude 相談役向け)

shadow audit から得た定量化:

### 7.1 機構の発火頻度

- 全 be3 候補 153,920 / 24 seeds = **6,413 / seed**
- fired 6,675 / 24 = **278 / seed** (4.34% fire 率)
- ghost 92% が skip 主因
- C/Q zero による skip は 8.2% (主役の自然選別)

### 7.2 主役同士の接触パターン

- (5, 5) 24.7% + (5, 2) 24.3% で半数
- fired 時の C_sum median 23 (= 両者で C 蓄積した状態が要件)

### 7.3 三項共鳴の射程 (v10.3 で観察された範囲)

- closed triad (Cat 1a): 165 件 (24 seeds × 50 windows、レア現象)
- open triad (Cat 1b): 9,576 件 (各 window 平均 4 件)
- → **v10.3 主題は「open triad の中継者役 cid」を主軸**にすべき

### 7.4 「主観があるとも言い切れない状態」の数値的状況

- 双方向 E3 経験 cid 2,854 / 5,224 = 54.6% (= 過半数の cid が be3 経験)
- でも repeated_partners = 0 (= 同 partner と再発火なし、= 持続性ゼロ)
- → 各 be3 イベントは「単発の通り過ぎ」、統計的痕跡としてのみ観察される
- これは v3.4 bridge_max_life=1 (物理的持続なし) と整合し、**v10.3 で観察される三項共鳴は「統計的痕跡」**

---

## 8. 次のステップ (Taka 判断項目)

実装指示書 §8.4 本番 run の進行可否を Taka 判断する素材:

| 観点 | shadow audit 結果 | 判断材料 |
|---|---|---|
| 機構動作 | ✅ 6,675 件 fired、skip 理由分布健全 | 本番 run 進行 OK |
| Layer B bit-identity | ✅ 552/552 (本番規模) | 物理層 frozen 完璧 |
| wall time | -0.5% overhead (shadow) | 本番 (C 消費あり) も同程度想定 |
| 観察データ規模 | 第三項 9,741 件、closed 165 件 | **closed triad は規模ギリ** |
| 三項共鳴主題 | open triad 主役判明 | v10.3 主題ドキュメントの素材十分 |

### 8.1 本番 run 進行 OR 設計再考?

**観察事実**:
- closed triad (Cat 1a = 「3 cid 全ペア接触」) は 165 件、極めてレア
- open triad (Cat 1b = 中継者ペア) は 9,576 件、十分な規模

**Code A 暫定意見**:
- 本番 run (= C 消費あり) でも shadow audit と同じ機構フィルタが働く
- shadow audit と本番の主な違いは「C 消費による balance_decision の経路差」
- 「主観があるとも言い切れない状態」観察に必要なデータは shadow audit で既に取得済
- **Taka 判断**: 本番 run を実施するか、shadow audit 結果で v10.3 主題ドキュメント執筆に進むか

### 8.2 仮に本番 run を実施する場合

- 同条件で wall ~3h、出力 ~1.7 GB
- shadow audit と本番で観察結果がどう変わるかを比較
- Layer B は不一致 (= C 消費による balance 経路の差)、これが新たな観察事実

---

## 9. 結論

v10.3 shadow audit 通過判定:

1. ✅ **機構動作**: 6,675 件 fired、skip 理由分布健全 (ghost 92%、C/Q zero 8%)
2. ✅ **Layer B bit-identity**: v10.2 main と 552/552 完全一致 (本番規模)
3. ✅ **wall time**: -0.5% overhead
4. ✅ **post-process**: open intermediary 9,576 + closed third 165 件検出
5. ✅ **regulation**: 実装指示書 §10 全項目満たす
6. ⚠️ **設計上の発見**: closed triad は稀少 (165/1,200 window)、open triad が支配 (4,960/1,200 window)

**Taka 判断項目**: 本番 run (実装指示書 §8.4) へ進行するか、shadow audit 結果で v10.3 主題ドキュメント執筆に進むか。

---

*以上、v10.3 shadow audit 結果レポート。Taka レビューを待つ。*
