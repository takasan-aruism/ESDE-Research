# v10.3 設計論点 — Code A 調査結果

*作成*: 2026-04-29、Code A (実装担当)
*対象*: Claude (相談役) §5 調査依頼項目 + §8.4 Q12-14
*親資料*: `v10_3_design_discussion_points.md` (Claude 作成)
*位置づけ*: 設計論点まとめ §5 への応答。実装可否、計算コスト、案 X/Y/Z 比較
*出力*: `developmental/v102/followup/v103_cat_*.csv`
*実装*: `v102_v103_category_freq.py`

---

## 0. 前提受領

Claude (相談役) からの修正受領:

- **双方向 E3** = 機構 (2 cid 間で両者 C-1)
- **三項共鳴** = 双方向 E3 + 第三項 (C) から立ち上がる現象
- **第三項 (C)** = A-B 関係を manifest にする境界面 (cid である必要なし)

私が前回実施した `v102_scale_v103prep_analysis.md` の **α (3 cid 共有 link)** 解析は **Category 1a/1b/1c (cid 第三項) の事前推定** として有効。**Category 2-4 は別軸として追加調査が必要**。本ドキュメントはそれに応答する。

---

## 1. §5.1 各カテゴリの実装可否

各カテゴリを (a) 既存 raw CSV から取れるか、(b) v10.3 機構実装後に追えるか、(c) engine 拡張が必要か で分類。

### 1.1 一覧表

| Cat | 候補 | 取得経路 | 既存 CSV から | コスト | 実装方針 |
|---|---|---|---|---|---|
| 1a | closed triad | bidirectional_e3_log (新規) | NO | 低 | 機構実装後の log を post-process |
| 1b | open triad (B 中継) | 同上 | NO | 低 | 同上 |
| 1c | proximate cid | engine + cid 重心 | 部分的 | 中 | 新規 logger で重心出力 |
| 2a | 共有ノード | label_member_persistence + link_life_log | **部分的 (8% cover)** | 中 | engine state を新規 logger 追加 |
| 2b | 共有 link (boundary) | engine internal | NO | **高** | engine 拡張、推奨見送り |
| 2c | 共有 cycle (R+) | resonance log | NO | **高** | 同上、見送り |
| **3a** | **共有 ghost** | **ingestion_events** | **YES** | **低** | **定義要再検討、§1.3 参照** |
| **3b** | **共有 phase bin** | **per_subject (M_c.phase_sig)** | **YES** | **低** | **完全実装可** |
| **3c** | **共有 birth_window** | **per_subject** | **YES** | **低** | **完全実装可** |
| 4a | 空間距離 (重心) | label_member_persistence + link_life_log | 部分的 | 中 | 新規 logger 推奨 |
| **4b** | **世代距離** | **per_subject birth_window** | **YES** | **低** | **完全実装可** |
| **4c** | **窓内共在** | **per_window** | **YES** | **低** | **完全実装可** |

### 1.2 既存 raw CSV から取れる 5 カテゴリの事前頻度推定 (N=5000)

候補ペア定義: 既存 E3_contact イベントで **同一 (global_step, link_id) で 2 cid 以上が onset** したペア (= 物理的に v10.3 双方向 E3 の strict subset の発火条件を満たすペア)。

24 seeds 合計の候補ペア数: **1,552 件** (mean 64.7/seed)。

| Cat | 観察事実 (per pair rate) |
|---:|---|
| **3a 共有 ghost** | **0.0%** (0 件、§1.3 で議論) |
| **3b 共有 phase bin (π/4)** | **0.88%** (random expect 12.5% → 大幅下回る) |
| **3c 共有 birth_window** | **89.5%** (= 同コホート起源) |
| **4b 世代距離 median** | **0 windows** (= ほぼ同 birth_window) |

### 1.3 Category 3a (共有 ghost) の定義問題

**重大な発見**: ingestion_events 上で「両 cid が同じ ghost を食べた」は 0 件。

理由: ESDE 設計上、各 ghost は **1 度しか食べられない** (即時摂食で residual_Q が 0 になる、もしくは reaped する)。よって「2 cid が同じ ghost を食べる」は構造的に不可能。

→ Cat 3a の定義は再検討が必要。候補:

| 案 | 定義 | データ可否 |
|---|---|---|
| 3a-i | 両者が同じ ghost に対して **接触 (E3) を経験** | per_event_audit から取得可、要追加実装 |
| 3a-ii | 両者が **同じ過去 cid (現 ghost)** から E3_contact を受けた | 同上 |
| 3a-iii | 両者の **eaten ghost の共起ノード集合** に重なり | label_member_persistence + ingestion から間接計算可 |

Code A 推奨: **3a-i (両者が同 cid と E3 接触経験あり、その cid が後に ghost 化)** が最も自然。実装は per_event_audit + per_subject の host_lost_window で取得可。

### 1.4 Category 3c / 4b の解釈

**事前推定で得た結果**:
- 全 1,552 候補ペアの 89.5% が同 birth_window 出身
- 主役ペア (両者 n_core ≥ 4、36 件) では 同 birth_window 0%、**世代距離 median 17.5 windows (≈ 8,750 step)**

→ **背景集団 (大半が短命の n_core=2) は同コホート内で接触する**、**主役 (n_core ≥ 4 の長寿) は世代横断で接触する**。これは新しい観察事実で、v10.3 の「主役の共鳴は世代横断型」という性質を示唆。

### 1.5 Category 2 系列 (構造的第三項) は engine state 拡張が必要

2a (共有ノード)、2b (共有 link)、2c (共有 cycle) は cid の member_nodes / boundary_links / cycle 帰属を engine state から取得する必要があり、現在の v10.2 実装では label_member_persistence (v9.13 audit) の subset (~8% カバー) のみ。

**Code A 推奨**: v10.3 機構実装で以下を追加 logger に出力:
- 双方向 E3 発火時の両 cid の **member_nodes (frozenset)** を CSV 化
- これだけで 2a (intersection) と 4a (重心 + 距離) が完全カバー
- 2b/2c は engine 拡張なので **v10.3 では見送り**、v10.4 以降の検討

---

## 2. §5.2 計算コスト見積もり

### 2.1 双方向 E3 発火回数の予想

既存 E3 events を proxy として:

| N | 既存 E3 events / 24 seeds | 双方向ペア (≈ E3/2) | per seed |
|---:|---:|---:|---:|
| 500 | 93,975 | ~47,000 | 1,958 |
| 1000 | 73,097 | ~36,500 | 1,521 |
| 2500 | 67,177 | ~33,500 | 1,396 |
| 5000 | 60,552 | ~30,000 | 1,250 |
| 10000 | 56,594 | ~28,000 | 1,167 |

注意: これは **strict simultaneous onset proxy**。実際の双方向 E3 は「両者 alive 同 link 共有」全 step で発火する設計なので、**10-30 倍多くなる可能性** (上記 1,250/seed × 10 = ~12,500/seed = ~250/window)。

### 2.2 C 消費インパクト

論点 B-1 採用 (両者 C ≥ 1 必須) を仮定:
- 主役 (n_core ≥ 4 + repeated 5+) は C を 50+ 蓄積
- 双方向 E3 で C-1 を毎回引くと、~250/window × 50 = 12,500 C 消費 / window
- v10.2 の意識発動 C 消費は ~70/window (3,517 / 50)

**双方向 E3 は意識発動の 170 倍 C 消費する可能性**。これは:
- C=0 で skip するペアが大半になる
- 主役の C 蓄積能力を遥かに超える消費レート
- 結果として **「ほとんどのペアは C 不足で発火しない」 = 自然な選別**

これは v10.2 §4.6「意識発動の自然フィルタ」の延長として整合。**ただし数値オーダーが著しい**ため、shadow audit (= C 消費を記録のみ、実消費しない) で先に挙動確認することが必須。

### 2.3 wall time 増分予想

per-step オーバーヘッド試算:
- 既存 E3 detection: link 走査 O(L)
- 双方向 E3 検出: 同じ link 走査内で「両者 alive」確認 → ほぼ無視できる (5% 増加)
- 第三項検出: per-step ではなく **window 末で post-process** → 別途 ~10-15% 増
- CSV 書き出し: bidirectional_e3_log + 3rd_cid_log で 5-10% 増

合計増分: **+20-30% wall time**。

| N | v10.2 wall | v10.3 予想 wall |
|---:|---:|---:|
| 500 | 568 s | **~720 s (12 min)** |
| 1000 | 1,080 s | **~1,400 s (23 min)** |
| 2500 | 3,730 s | **~4,800 s (80 min)** |
| 5000 | 10,786 s | **~14,000 s (3.9 h)** |
| 10000 | 34,576 s | **~45,000 s (12.5 h)** |

→ **N=10000 で 12.5h は許容範囲** (v9.18 long run も同程度)。

### 2.4 メモリ・I/O コスト

- bidirectional_e3_log: 1 行 ~30 列 × ~12,500 entries/seed = ~150 MB/seed (24 seeds で 3.6 GB)
- bidirectional_e3_3rd_cid_log: 1 行 10 列 × ~500 entries/seed = ~3 MB/seed (24 seeds で 72 MB)
- 比較: v10.2 main の出力 1.7 GB → v10.3 で ~5 GB/N=5000、~10 GB/N=10000

許容範囲。disk 圧迫なし (system 503 GB available)。

---

## 3. §5.3 既存 CSV との整合

### 3.1 既存 CSV 不変方針

v10.3 の追加は **新規 CSV 追加のみ**で既存列は touch しない。これは v9.14 paired audit の方針と整合。

| 既存 CSV | 影響 |
|---|---|
| per_subject (140 列) | 列追加のみ (n_be3_total, n_be3_partners 等の集計指標) |
| per_event_audit | 不変 |
| balance_decisions | 不変 |
| c_trajectory | 不変 |
| ingestion_events | 不変 |

### 3.2 新規 CSV

```
diag_v103_main/
├── (既存と同じ subdirs)
└── bidirectional/
    ├── bidirectional_e3_log_seed{N}.csv         (1 行 = 1 双方向 E3 発火)
    ├── bidirectional_e3_3rd_cid_log_seed{N}.csv (Cat 1a/1b/1c で第三項 cid あり)
    ├── bidirectional_e3_member_nodes_seed{N}.csv (2 cid の member_nodes)  [optional]
    └── bidirectional_e3_summary_seed{N}.csv     (run-level 集計)
```

### 3.3 既存解析スクリプトの互換性

私が作成した既存スクリプト群:
- `v102_scale_analysis.py`、`v102_scale_compare.py`: 既存 CSV のみ参照、影響なし
- `v102_scale_followup_analysis.py`、`v102_v103_category_freq.py`: 同上
- `v102_scale_v103prep_analysis.py`: 既存 E3 events を proxy として使用、v10.3 で `bidirectional_e3_log` が生成されればそれと比較可能

---

## 4. §5.4 内部情報スナップショットの実装

### 4.1 A-B 内部情報スナップショット (確定)

双方向 E3 発火 step で両 cid の `M_c (4 要素)`、`Q`、`C`、`age`、`cid_id` を記録。

実装:
- 既存の event detector (`detect_e3_new_pairs`) と同じ位置に hook を追加
- 既に cid object に M_c は格納済み → メモリアクセスのみ、計算コスト極小
- 記録は per_step ではなく **per event** (双方向 E3 発火時のみ)

### 4.2 buffer 戦略

per-step で flush するか、window 末で flush するか:

| 戦略 | 利点 | 欠点 |
|---|---|---|
| per-step flush | 既存 audit と整合、メモリ最小 | I/O 多発で wall time 増 |
| window 末 flush | I/O 集約、効率的 | メモリに 1 window 分保持 |

**Code A 推奨**: **per-step flush** (既存 v9.14 audit ledger と同様)。
- 1 step あたり ~3-5 events で I/O 影響小
- メモリリスク回避
- v9.14 と整合した実装パターン

### 4.3 v9.16 サンプリング機構との整合

v9.16 段階 3 の `read_on_event` (CidSelfBuffer) は event 駆動で、**現状そのまま動く**。双方向 E3 発火時にも `read_on_event` が呼ばれる (event_type が新規 `bidirectional_e3` として登録できる)。

これは別の audit 系統 (B 領域) なので、v10.3 の bidirectional_e3_log とは独立。

---

## 5. §5.5 案 X / Y / Z 比較 (Code A 視点)

### 5.1 各案の特徴

| 観点 | 案 X (別 CSV、最小限) | 案 Y (cid_id のみ) | 案 Z (本流フル記録) |
|---|---|---|---|
| 本流 CSV 列数 | ~30 列 | ~30 列 + 1 (cid_c_id) | ~50+ 列 |
| 別 CSV | あり (third_cid_log) | なし | なし |
| 第三項 cid 詳細 | 別 CSV に min snapshot | per_subject 後 join | 本流に直接 |
| 複数同時カテゴリ | フラグ + sub log で対応 | フラグのみ | 列肥大 |

### 5.2 実装コスト比較

| 観点 | 案 X | 案 Y | 案 Z |
|---|---|---|---|
| logger 追加 | 2 つ (本流 + sub) | 1 つ (本流のみ) | 1 つ (本流のみ) |
| カラム設計 | 本流 + sub 別々 | 本流の 1 列追加 | 本流に多列追加 |
| 第三項複数同時 | 困難 (sub log は cid 用、構造用は別途) | 困難 (フラグのみで詳細不明) | 構造的に難しい |
| **総合** | **中** | 低 | 高 |

### 5.3 事後解析コスト比較

| 観点 | 案 X | 案 Y | 案 Z |
|---|---|---|---|
| triad 解析 | 別 CSV を join | per_subject 全体を join | 本流直接 |
| 「主役の中の主役」第三項追跡 | 別 CSV で容易 | 困難 (毎回 join) | 容易 (本流) |
| step 精度結合 | あり (sub log step) | 不正確 (per_subject の time series 必要) | あり |
| **総合** | **低** | 中-高 | 低 |

### 5.4 CSV サイズ比較

仮想 50,000 events 想定 (24 seeds 合計、N=5000):

| 案 | 本流 size | sub log size | 合計 |
|---|---|---|---|
| X | ~150 MB | ~3 MB | **~153 MB** |
| Y | ~155 MB (cid_c_id 1 列追加) | — | **~155 MB** |
| Z | ~250 MB (列増による) | — | **~250 MB** |

### 5.5 Code A 推奨: **案 X**

理由:
1. **目的別分離**: 本流 (A-B 双方向 E3) と sub log (cid 第三項) を分けることで、各解析の意図が明示される
2. **「主役の中の主役」追跡が直接できる**: sub log で cid_c の n_core/Q/C/age が手元にあるため、別途 join 不要
3. **CSV サイズ抑制**: 案 Z より約 100 MB 軽量
4. **複数同時カテゴリへの拡張**: sub log を「カテゴリ別」に追加することで対応可能 (例: bidirectional_e3_member_nodes_log を別途追加で Cat 2a/4a カバー)
5. **v9.14 paired audit との一貫性**: per_event_audit と per_subject_audit が分離されている設計と同じパターン

ただし留意点:
- sub log を **どこまで分けるか** (cid 1 つ、構造 1 つ、ghost 1 つ...) は要設計
- 私の暫定推奨: **3 種** (cid third / structural / contextual)
  - bidirectional_e3_3rd_cid_log: Cat 1a/1b/1c
  - bidirectional_e3_3rd_structural_log: Cat 2a (member_nodes 共有)
  - bidirectional_e3_log の数値列で Cat 4a-c は十分

---

## 6. §8.4 Q12-14 への回答

### 6.1 Q12: §5 調査依頼項目すべて

§1-§5 で完了。要点:

- 既存 raw CSV から事前推定可能: **3a, 3b, 3c, 4b, 4c** + **2a/4a 部分的**
- v10.3 機構実装後に追える: **1a, 1b, 1c**
- 実装見送り推奨: **2b (共有 link)、2c (共有 cycle)**
- 案 X/Y/Z は **X 推奨**

事前推定で得た新規発見:
- 3c (共有 birth_window) は背景ペアで 89.5%、主役ペアで 0% → **主役は世代横断型**
- 3a (共有 ghost) は **構造的に 0%** で定義要再検討

### 6.2 Q13: 第三項検出 (1a/1b の triad 検出) の N=10000 計算コスト

**回答**: 現実的。具体的には:

実装方針:
- per-step で双方向 E3 発火は記録のみ (本流 logger)
- 第三項検出は **window 末で post-process** (1 window 分の bidirectional_e3_log を読んで triad を検出)
- 24 seeds 並列で各 seed 独立処理 → N=10000 1 seed wall time +10-15% 程度

triad 検出アルゴリズム:
- 1 window 内の双方向 E3 ペアを edge とするグラフを構築
- 三角形 (closed triad) と path (open triad) を抽出
- N=10000 で 1 window あたり ~250 ペア → グラフサイズ 250 edges、三角形検出 O(E^1.5) ~ 数千 ops/window
- 50 windows × 24 seeds × N=10000 = 5,000 万 ops 程度 (= 0.5 秒未満で完了)

→ **計算コストは実質無視できる**。

### 6.3 Q14: 双方向 E3 と既存 E3 の同 step 内発火順序

**回答**: 制約なし。実装は素直に組める。

推奨順序 (per step 内):
1. **物理層 step** 実行 (operators 7 個) — engine state mutation
2. **E1/E2/E3 detection** — event_emitter で検出、contacted_pairs に登録
3. **既存 E3 onset 処理**:
   - per_event_audit にレコード追加
   - 各 cid の Q-1 (Layer B 既存)
4. **双方向 E3 検出** (新規):
   - E3_contact onset 中、両 cid が `hosted ∧ Q ≥ 1 ∧ C ≥ 1` を確認 (B-1)
   - 条件満たせば: bidirectional_e3_log にレコード追加、両者の C-1
   - 条件満たさなければ: skipped_c_zero フラグで記録のみ
5. **balance_decision** (既存 v10.2、cid 単位):
   - cognition vs consciousness の確率決定
   - C が双方向 E3 で消費済みなら、その状態で確率計算 (→ 結果として skip_C_zero が増える可能性)
6. **摂食** (既存 v10.2)

論点 C-1「両方発火」、C-2「初回接触のみ」、C-3「balance と独立」はすべて満たせる。

実装上の注意:
- 双方向 E3 の C 消費を **balance_decision より先に** 行う必要 (C 状態が確率計算に反映される)
- shadow audit 段階 (= C 消費なし、log のみ) では balance_decision の挙動は v10.2 と一致するはず → bit-identity 検証可能

---

## 7. 推奨と次のステップ

### 7.1 v10.3 実装の暫定設計 (Code A 視点)

1. **新規 CSV**: 案 X 採用、3 sub log (cid_3rd / member_nodes / その他は本流の数値列)
2. **新規 logger**: bidirectional_e3 専用、per-step flush、v9.14 audit ledger と類似アーキテクチャ
3. **B-1 採用** (両者 C ≥ 1 必須): 自然フィルタとして機能、C 消費の暴走回避
4. **shadow audit 必須**: C 消費を記録のみで実行する段階を経て、本番 C 消費に移行
5. **第三項 logger は別 logger** (= 機構と独立に on/off 可能)

### 7.2 観察スケール推奨 (再確認)

`v102_scale_v103prep_analysis.md` の結論を維持:
- **本番**: N=5000 (主役 270 cid、wall ~4h with v10.3 overhead)
- **追試**: N=10000 (主役 310 cid、wall ~12.5h)
- **smoke**: N=2500 (wall ~80 min)

### 7.3 Cat 3a の定義再検討要請

§1.3 で述べたとおり、3a「共有 ghost」は構造的に 0% になるので定義変更が必要。

Code A 推奨定義: **「両者が同 cid (現 ghost) と E3_contact 経験あり」** (3a-i)。実装は per_event_audit + per_subject の host_lost_window で取得可能。

### 7.4 主題ドキュメント執筆時に明記すべき素材

私の事前推定から:
- 「主役ペアの 89.5% が同 birth_window」 → 主役は世代横断型 (= 既存仮説への逸脱)
- 「strict simultaneous onset で観察される候補ペアは N=5000 で 64.7/seed のみ」 → 双方向 E3 発火は遥かに多い (10-30 倍と想定)
- 「Cat 3a は構造的に 0%、定義要再検討」

これらは v10.3 主題ドキュメント (Claude が後で作成) の「観察軸の根拠」セクションで参照されると良い。

---

## 8. 出力ファイル

```
developmental/v102/
├── v102_v103_category_freq.py             (本調査スクリプト)
├── v102_v103_design_investigation.md      (本ドキュメント)
└── followup/
    ├── v103_cat_per_pair.csv              (1,552 候補ペアの per-pair 詳細)
    ├── v103_cat_summary_per_seed.csv      (per seed の集計)
    └── v103_cat_summary.csv               (全 24 seeds 集計)
```

加えて、既存の解析資産:
- `v102_scale_v103prep_analysis.md` (Cat 1 系列の事前推定 = α/β/γ/δ)
- `v102_scale_extra_analysis.md` (主役プール 272 cid 内訳)

---

## 9. 限界

- 事前推定は **strict simultaneous onset** に限定。実際の双方向 E3 はさらに多発するため、頻度推定は下限値
- v10.3 機構実装が完了するまで、Cat 1a/1b/1c の正確な観察は不可
- Cat 2b/2c は engine 拡張なし、本ドキュメントでは見送りを推奨
- C 消費インパクト (170 倍) は仮定値。実際は B-1 (両者 C ≥ 1 必須) でかなり絞られるはず

---

## 10. 結論

§5 調査依頼項目への回答完了:

1. **12 カテゴリの実装可否**: 7 つは raw CSV から事前推定可、3 つは v10.3 機構実装後に追える、2 つは見送り
2. **計算コスト**: N=10000 で +20-30% wall time 増、許容範囲
3. **CSV 整合**: 既存不変方針、新規 CSV 追加のみ
4. **内部情報スナップショット**: per-step flush、既存 audit 系統と整合
5. **案 X/Y/Z**: 案 X 推奨 (目的別分離、追跡容易、サイズ抑制)

§8.4 Q12-14 への回答:
- Q12: 上記 §5 で完了
- Q13: triad 検出は計算コスト無視できる
- Q14: 既存 step 順序内に組み込み可能、制約なし

新規発見:
- 主役ペアは世代横断型 (3c=0%、gen_dist median 17.5 windows)
- 背景ペアは同コホート起源 (3c=89.5%)
- Cat 3a は ESDE の即時摂食設計上 0% で定義要再検討

これらは v10.3 主題ドキュメント執筆時の素材となる。

---

*以上、Code A 調査結果。Claude (相談役) のレビューを待つ。*
