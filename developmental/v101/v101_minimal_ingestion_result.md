# v10.1 Minimal Ingestion 本番 run 結果レポート (24 seeds × tracking 50)

*実行日*: 2026-04-26
*ブランチ*: main
*実装*: Code A (Claude Opus 4.7 1M)
*親版*: v9.18 (primitive/v918/)
*階層移行*: Primitive (v9.x) → Developmental (v10.x)
*資料*: `v10_1_minimal_ingestion.md` (主題ドキュメント)

---

## 0. 一行サマリ

ghost 期間を Q ベースに移行 + E3 圏内摂食機構 (段階 1) を実装。**摂食 3,588 件発生する一方、phantom contact (期待していったら居なかった) が 48,625 件と摂食の 13.6 倍**。物理層 frozen 維持 (subject 数 5,224 完全一致、wall time 2.98h vs v9.18 の 3.00h、conv_bias ratio 3.03 vs 3.03)、ghost 寿命構造は **reaped 率 +14.8pt の構造変化** を示した。

---

## 1. 実装サマリ

### 1.1 新規ファイル / 改変ファイル

| ファイル | 役割 | 変更 |
|---|---|---|
| `v101_memory_readout.py` | main run (v918 から派生) | SubjectLayer 改造 + pickup 機構廃止 |
| `v914_spend_audit_ledger.py` | Layer B (audit + 摂食 phase) | `add_q()` / ingestion phase 追加 |
| `v101_orchestrator.py` | per_step orchestrator | v918 から rename のみ |
| `v101_cid_self_buffer.py` 他 4 ファイル | v918 frozen 資産 | rename のみ |
| `v914_event_emitter.py` / `v917_*.py` | 既存 frozen | vendoring (v101 self-contained 化) |
| `test_v101_ingestion.py` | 単体テスト | 新規 16 件 |

### 1.2 本番実行コマンド

```bash
seq 0 23 | parallel -j24 python v101_memory_readout.py \
    --seed {} --maturation-windows 20 --tracking-windows 50 \
    --window-steps 500 --tag main
```

### 1.3 Wall time (24 seeds 並列)

| 指標 | v10.1 main | v9.18 main | 比率 |
|---|---|---|---|
| min | 10,403s (2h53m) | — | — |
| max | 10,997s (3h05m) | 11,094s (3h05m) | **0.991x** |
| mean | 10,733s (2h59m) | 10,807s (3h00m) | **0.993x** |

摂食 phase の追加オーバーヘッドは並列化で完全吸収、むしろ pickup 機構廃止の効果でわずかに高速化 (-0.7%)。

### 1.4 単体テスト

| ファイル | 件数 | 結果 |
|---|---|---|
| test_v101_ingestion.py | 16 | **16/16 PASS** |

範囲: detach (residual_Q snapshot) / add_q (Q0 clamp) / attempt_ingestion (full / partial / empty / phantom / 満腹) / reap_ghosts_step / 多 cid 順次処理 / 統合 1 サイクル

### 1.5 Bit-identity 検証

- **v10.1 内部**: smoke 2 連続 run で 24 CSV 全 MD5 一致
- **v9.18 物理層 frozen 検証**: per_event_audit 1,180 行で `cid / window / step / event_type / link_id / q0 / spend_flag / delta_norm / attention_delta / familiarity_delta / post_event_gap / shadow_pulse_index` 完全一致 (diff=0)、`v14_q_remaining` のみ 16 行で差分 (摂食で +Q した cid の後続 spend、期待通り)

---

## 2. §4.1 設計判断 6 項目の確定実装

| # | 項目 | 確定 | 実装ファクト |
|---|---|---|---|
| 1 | フック箇所 | (a) Layer B (`SpendAuditLedger.observe_step` 内) | E3 emission for-loop の後に `_run_ingestion_phase()` |
| 2 | 多 CID : 1 ghost 順序 | cid_id 昇順 | `for observer_cid in sorted(candidates_per_observer.keys())` |
| 3 | 摂食 vs reap 順序 | step 末 reap (Taka 確定) | per-step ループ末で `cog.reap_ghosts_step(cumulative_step)` |
| 4 | E3 接触の継続性 | (b) edge / entry のみ | 既存 `_contacted_pairs` 設計 (onset 一回) を踏襲 |
| 5 | 観察ログ粒度 | raw + aggregated 両方 | `ingestion_events_seed*.csv` (raw) + per_window/per_subject 集計列 + `ingestion_summary_seed*.csv` |
| 6 | pickup 機構 (v9.8c) | (a) 完全廃止 | `record_death` / `attempt_pickup_round` / `cleanup_death_pool` / `cid_ttl_bonus` 削除 |

---

## 3. 物理層 frozen 検証 (§8.1, 8.2)

### 3.1 Subject 総数 (cid 発番) は完全一致

| 状態 | v10.1 | v9.18 |
|---|---|---|
| 総 subject 数 | **5,224** | **5,224** |
| 最終 hosted | 795 (15.2%) | 795 (15.2%) |

物理層 (engine, virtual_layer, label cull タイミング) は完全に frozen。cid 発番カウンタが同一値で終了 → 認知層追加機構が物理層を一切 perturb していないことの直接証拠。

### 3.2 conv_bias ratio (収束/発散時の soul-aligned ratio)

| 指標 | v10.1 | v9.18 |
|---|---|---|
| mean | 3.03 | 3.03 |
| median | 3.04 | 3.04 |

完全一致。物理層と認知層 (phi/attention) の相互作用構造が変わっていない。

### 3.3 wall time

99.3% (Section 1.3 参照)。摂食機構が物理層計算量を増やしていないことの間接証拠。

---

## 4. §7.1 摂食動態の基本統計

### 4.1 24 seeds 集計 (mean / range)

| 指標 | total | mean/seed | min | max |
|---|---|---|---|---|
| 摂食イベント数 | 3,588 | 150 | 112 | 182 |
| 空摂食 (gain=0) | 134 | 6 | 1 | 13 |
| **空摂食率** | **3.62%** | — | — | — |
| total gain (ghost から取った量) | 20,712 | 863 | 691 | 1,024 |
| total received (CID に入った量) | 17,225 | 718 | 594 | 836 |
| total digested (Q0 超過分、消えた量) | 3,487 | 145 | 54 | 238 |
| **消化分の比率** (digested/gain) | **16.73%** | — | — | — |
| ユニーク eater (摂食した cid 数) | 1,361 | 57 | 38 | 75 |
| ユニーク ghost (食べられた ghost 数) | 3,454 | 144 | 109 | 170 |

### 4.2 構造的観察

- **eater 比率**: 1,361 / 5,224 = **26.0%** の subject が一度以上摂食側に回った
- **ghost 食糧化率**: 3,454 / 4,429 = **78.0%** の ghost が少なくとも一度は摂食された (一度の摂食で全 residual_Q を取得するため、複数回ではなく一回完食パターン)
- **摂食 Q の純流入**: 24 seed 合計で 17,225 Q が認知層内で再配分された (E3 spend で消費される Q とは別経路)
- **消化損失**: 16.73% は Q0 上限到達による損失。「満腹 CID も摂食する」(飢餓判定撤廃) の帰結が定量化された

---

## 5. §7.2 寿命構造の変化 (v9.18 baseline 比較)

### 5.1 final_state 分布

| 状態 | v10.1 | v9.18 | Δ |
|---|---|---|---|
| reaped | **82.8%** (4,325) | 68.0% (3,554) | **+14.8pt** |
| hosted | 15.2% (795) | 15.2% (795) | 0pt |
| ghost (run 末で残存) | **2.0%** (104) | 16.7% (875) | **-14.7pt** |

### 5.2 解釈

v9.18 では `effective_TTL = GHOST_TTL + cid_ttl_bonus` の窓ベース寿命があり、run 終了時点で TTL 未満の ghost が 16.7% 残っていた。v10.1 では Q ベースの reap (residual_Q == 0 で消える) と摂食機構 (gain で全 Q を一気に取る) の組み合わせにより、ghost が摂食されるか枯渇するかで早期に reap される構造になった。

ただし重要な留保:
- v10.1 で reaped の中には `residual_Q = 0` で生まれて即 reap された ghost が多数含まれる (生前完全枯渇したケース)
- 「摂食されて消えた ghost」の比率は ghost 食糧化率 78.0% から推定可能だが、初期 residual_Q=0 の ghost は摂食対象になる前に reap されている可能性あり

### 5.3 per_window 集計

- ghost_births (24 seeds × 50 windows): **4,429**
- ghost_reaped: **4,325**
- 純増 (run 末まで残った ghost): 4,429 − 4,325 = **104** (per_subject 集計と完全一致)
- 任意 window での ghosts_remaining: mean 8、max 25
- mean_ghost_residual_Q (window snapshot): mean 5.66

ghost が常時 8 体程度ストックされている、という定常状態が観察できる。

---

## 6. §7.3 ghost 経済の構造

### 6.1 摂食フローのバランス

```
ghost 生成側 (detach 時の Q_remaining 継承)
  → total residual_Q inherited 推定: 4,429 ghost × mean 5-7 = 25,000-30,000

摂食消費側
  → total gain (ghost から取られた量): 20,712
  → total received (cid に入った量): 17,225
  → total digested (消えた量): 3,487

(gain != residual_Q inherited、なぜなら多くの ghost は initial_residual_Q=0 で
 即 reap、または部分摂食前に reap される。次節 phantom と関連。)
```

### 6.2 mean_ghost_residual_Q 推移

window 単位でスナップショットされる `mean_ghost_residual_Q` (生存中の ghost のみ平均) は run 全体で **mean 5.66**。これは ghost が "食糧" としてある程度の量を持って待機している状態を示す。ただし 78.0% の ghost が摂食を受けるため、実際には待機時間が短く、瞬間的な観察値。

---

## 7. **phantom contact 現象 (新規発見)**

### 7.1 数字

| 指標 | v10.1 24 seeds | per seed (mean) |
|---|---|---|
| 摂食イベント | 3,588 | 150 |
| **phantom contact** | **48,625** | **2,026** |
| **phantom / ingestion 比率** | **13.59x** | (range 9.74x - 17.40x) |

### 7.2 phantom とは何か

step N で hosted_a と物理層 alive_l 経由で初めて接触する cid_b について:
- cid_b が **生存 (hosted)** なら → 通常の E3 contact (両者が cid_ctx)
- cid_b が **ghost (cog.is_ghost)** なら → ingestion 候補 (摂食試行)
- cid_b が **既に reaped (cog から消滅、しかし `_node_to_cids` に member_nodes 痕跡が残る)** なら → **phantom contact**

phantom は **「認知層では既に消滅した cid の物理痕跡 (member_nodes が指す物理ノード) との接触」** であり、`_node_to_cids` が cid retire 後も保持される設計 (v9.14 の `member_nodes は soul で不変、一度発生した contact pair も不変記録` 方針) の帰結。

### 7.3 phantom が摂食を圧倒している意味

物理層の接触 (alive_l 経由 E3 onset 候補) のうち:
- 摂食に至る = 7.4% 以下 (3,588 / (3,588 + 48,625))
- 大半は **「相手は既に居ない」物理痕跡接触**

これは v10.1 主題ドキュメント §1.3 動機 3「燃料概念の発生階層との接続」が**観察可能な数字として顕在化した形**:
- **物理層**: member_nodes 単位、cid retire 後も痕跡が残る
- **認知層**: residual_Q 単位、step 末で reap されると即消滅
- **両者の zeitkluft (時間的ズレ) が phantom contact** = "期待していったら居なかった"

### 7.4 phantom スケーリング (smoke vs main)

| | smoke | main (24 seeds 集計) | スケール |
|---|---|---|---|
| compute scale | 400 step-equiv | 24 × 35,000 = 840,000 step-equiv | 2,100x |
| 摂食イベント | 35 | 3,588 | 102x |
| phantom | 8 | 48,625 | 6,078x |

compute スケールに対して phantom が**約 60 倍速く増えている** ことが示唆される。これは ghost 履歴 (`_node_to_cids`) が単調増加するため、後期になるほど **「過去の ghost の物理痕跡」**が積み重なって phantom 発生率が上がる構造を反映している可能性が高い。

ただし smoke と main では window 数・step 数の比が異なるため、厳密な指数スケーリング解析は本レポート範囲外。v10.2 以降の検証論点として保留。

---

## 8. §7.4 v9.18 発見との照合

v9.18 baseline で観察された主要発見との関係:

### 8.1 conv_bias 不変

§3.2 で報告。v9.18 の主要観察軸 (収束時 soul 一致度) は v10.1 で完全保存。**摂食機構は collapse-divergence の構造的バイアスに影響しない**。

### 8.2 v9.18 発見 2 (個別 cid の cumulative_cognitive_gain 50.3% 上昇)

per_subject の `v18_cognitive_gain_final` 列は v10.1 で継承。本レポートでは深堀りしないが、摂食を受けた eater 1,361 体と上昇 cid の重なりが今後の解析素材。

### 8.3 v9.18 発見 7 (conc 上昇 + dist 大 19.2%)

v18 列群は保存されているため、今後 phantom 経験者 / eater 経験者を分けた conc / dist 比較が可能。

---

## 9. §7.5 動的平衡の予兆

主題ドキュメント §7.5 で予測されていた「v10.1 でも何らかの均衡が観察される可能性」について:

### 9.1 観察された均衡

- **ghost ストック**: 任意 window で生存中 ghost 約 8 体、mean residual_Q ≈ 5.66 — 定常状態に近い
- **ghost 食糧化率 78%**: 4 体に 3 体は摂食を受ける構造 → 食糧供給/需要のバランスが取れている
- **eater 比率 26%**: 全 subject の 1/4 が摂食回路に入る — 物理的接触機会の制約と整合

### 9.2 予兆ではなかったもの

- 意識層の独立 Q 消費は v10.1 では未実装のため、本格的な動的平衡 (dynamic equilibrium) はまだ起きていない
- 摂食は単方向 Q 流入 (ghost → eater)、消費機構が無いので **Q が累積する一方** の系
- v10.2 以降の意識層消費機構を入れることで、初めて持続的な動的平衡が観察できる見込み

### 9.3 phantom が予測外の主役

主題ドキュメント §7.5 では摂食動態が動的平衡の素材になると予想されていたが、**実際の数字では phantom が摂食を 13.59 倍も圧倒**している。動的平衡の素材は摂食の中ではなく、**phantom と摂食の比率変化**にあるかもしれない。これは v10.2 以降の検討課題。

---

## 10. 制約 / 限界 / 次の論点

### 10.1 v10.1 で意図的に踏み込んでいない領域

- 意識層の独立 Q 消費 (§3.2 で v10.2 以降と明記)
- 飢餓判定の数理化 (§4.1 で機械的判定に確定)
- 嗜好・Salience 駆動 (段階 3、v10.3 以降)
- 認知死した CID (residual_Q=0 で reap された cid) の特殊扱い

### 10.2 phantom contact の構造的限界

`_node_to_cids` は cid retire 後も保持するため、長期 run では phantom が単調累積する。v10.2 で意識層消費を入れるとき、phantom 経由の何らかの効果 (例: 「居ないものを期待した」コスト) を入れるかどうかは別途議論。

### 10.3 step 末 reap の副作用

新規 ghost (window 末 detach) で `residual_Q=0` のものは、その window の最後の step 末 reap で即削除される。この種の ghost は摂食機会を持たない。v10.1 では設計通りだが、観察上の比率を v10.2 以降で再検討する余地あり。

### 10.4 設計指示書の自己検証項目

§4.1 確定 6 項目、§4.2 確定済 13 項目、§5 Code A 確認 7 項目はすべて実装に反映、本番 run で動作確認。設計通りに走った形。

---

## 11. データファイル一覧

run 出力 (24 seeds × per seed):

```
diag_v101_main/
├── aggregates/        per_window CSV (50 行/seed) + conv_bias JSON
├── audit/             Layer B per_event_audit / per_subject_audit / run_level_audit_summary
├── ingestion/         (v10.1 新規)
│   ├── ingestion_events_seed*.csv  (raw、平均 150 行/seed)
│   ├── ingestion_summary_seed*.csv (1 行/seed、run-level 集計)
│   └── phantom_contacts_seed*.csv  (raw、平均 2,026 行/seed)
├── introspection/     v9.8b 内省タグログ
├── labels/            label メタデータ
├── network/           familiarity ネットワーク
├── persistence/       v9.13 リンク永続性ログ
├── pickup/            (空ディレクトリ、v10.1 で機構廃止のため。次回 cleanup 候補)
├── pulse/             v9.10 pulse log
├── representatives/   代表 cid 抽出
├── selfread/          v9.15-18 self-buffer + v18_window_trajectory
└── subjects/          per_subject CSV (5,224 行 total)
```

---

## 12. 一行締め

v10.1 Minimal Ingestion は設計通り稼働したが、**主役は摂食ではなく phantom contact** だった。物理層の痕跡と認知層の現存する cid の zeitkluft (時間ズレ) が、想定の 13.6 倍の規模で観察可能になった。これは v10.2 以降の主題候補として要検討。

---

*以上、v10.1 Minimal Ingestion 本番 run 結果レポート。*
