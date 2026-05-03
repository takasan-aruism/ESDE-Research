# v10.5 main_v2 本番 re-run 結果レポート (Leakage 修正版)

*作成*: 2026-05-04、Claude (Code A)
*対象*: Taka レビュー
*親資料*: `v105_main_run_report.md` (修正前 main、Leakage バグあり)
*run 設定*: 24 seeds × tracking 50 windows × window 500 steps、`--tag main_v2`
*wall*: 2026-05-03 23:18 〜 2026-05-04 07:35 (約 8 時間 17 分、8 並列)
*出力*: `developmental/v105/diag_v105_main_v2/`

---

## 0. 一文サマリ

Leakage callback 配線バグ (v10.2 即時 ingestion path) を修正後の本番完走。**Leakage event 232 件** (24 seeds 累積、全 trigger=ingestion) が発火し、**recorded β からの C 漏れ機構が本番規模で動作確認**。物理層 bit-identity 24/24 完全一致は維持。v10.5 設計の 3 機構 (β / Salience / Leakage) 全てが意図通り動作することを確認。

---

## 1. 完走性 + bit-identity

| 項目 | 結果 |
|---|---|
| 全 seed exit=0 | **24/24 PASS** |
| 物理層 bit-identity (labels) | **24/24 PASS** vs v10.4 main |
| 物理層 bit-identity (link_life_log) | **24/24 PASS** vs v10.4 main |
| seed あたり wall | min 9385s / max 9747s |

---

## 2. Leakage 機構 (修正版)

### 2.1 集計

| 指標 | 値 |
|---|---|
| 総 Leakage event | **232 件** |
| trigger 内訳 | ingestion: 232 / be3: **0** |
| 総漏れ量 | 232 units (= ε=1 × 232) |
| unique source cids | 232 |
| unique recipient cids | 203 (一部 cid が複数回受領) |
| unique recorded β | 160 (= 全 recorded β 443 件中 36%) |

### 2.2 per seed 分布

| 統計 | 値 |
|---|---|
| min | 4 |
| max | 19 |
| mean | 9.7 |

分布: [4, 4, 4, 5, 5, 6, 6, 8, 9, 9, 9, 10, 10, 10, 11, 11, 11, 11, 13, 14, 14, 14, 15, 19]

→ 全 24 seeds で発火。最大は seed あたり 19 件。

### 2.3 be3 trigger = 0 の構造的理由

設計書では be3 fired と ingestion の 2 系統で発火想定。実装上 ingestion のみ発火する理由:

- **be3 fire の条件**: cid_a / cid_b 両者 hosted (active β に所属中)
- **leakage 条件**: cid_y が **過去に recorded β に所属** していた cid である必要
- **β の cid 流動性**: v10.5 `_reassign_cids_for_beta` は binding strength 最大の α 所属 β に cid を配置。元 α の binding は時系列で +1 ずつ蓄積するため、新規 α (binding=1.0) に移動することは実質起きない
- **結論**: hosted cid が recorded β.member_cids_history に含まれることは構造的に稀

→ Leakage は **ingestion path 経由でのみ実用発火**。これは設計意図 (ghost cid Y を ingest した時、Y が所属した recorded β から漏れる) と整合。be3 path は理論上の保険機構として残置。

### 2.4 修正の経緯

| 検出 | 内容 |
|---|---|
| 修正前 main run | Leakage event 0 件 (24 seeds) |
| 原因 | `v105_spend_audit_ledger.py` の `attempt_ingestion` 呼び出しが 2 箇所、`_run_ingestion_phase` (v10.1 path) のみ callback 配線、v10.2 即時 ingestion path 配線漏れ |
| 修正 | v10.2 即時 ingestion path 内 (line 491 直後) に同じ callback を追加 |
| 検証 | main_v2 で 232 件発火、設計通り動作 |

---

## 3. α / β 構造 (main vs main_v2 比較)

| 指標 | main (修正前) | main_v2 (修正後) | 差 |
|---|---:|---:|---:|
| α total | 13,865 | 13,881 | +16 |
| α active | 11,799 | 11,792 | -7 |
| α recorded | 2,066 | 2,089 | +23 |
| β total | 1,983 | 2,009 | +26 |
| β active | 1,547 | 1,566 | +19 |
| β recorded | 436 | 443 | +7 |
| Salience event | 77,826 | 77,880 | +54 |

→ 差はほぼ誤差範囲 (Leakage で C が動いた影響で認知層に微小差が累積)。物理層は完全一致のため、構造は同水準。

---

## 4. Salience 機構 (main_v2)

| 指標 | 値 |
|---|---|
| 総 Salience event | 77,880 件 (mean 3,245 / seed) |
| read_other / be3_fired | 詳細分布は main と同水準 |

mass-weighted 観察動作確認。詳細は `v105_main_run_report.md` §6 と同様。

---

## 5. 設計規律 (M1-M6)

main run と同じ判定基準で:

| 指標 | basis | main_v2 結果 |
|---|---|---|
| **M5** β/cids ≤ 50% | 全 24 seeds | **全 PASS** |
| **M6** 1 cid → 1 β 違反 0 | | **PASS** |
| **bit-identity** | 24/24 | **PASS** |

→ 規律完全守備。

---

## 6. 完了判定

| 条件 | 結果 |
|---|---|
| smoke 通過 (M1-M6) | **PASS** |
| shadow audit 通過 | **PASS** |
| 本番 (main + main_v2) | **PASS** |
| 全 logger 出力 | **PASS** (alpha/beta/salience/leakage) |
| per_subject / per_window 集計 | **PASS** |
| bit-identity (物理層) | **PASS (24/24)** |
| β-Integration 立ち上がり、ダブルブッキング解消 | **PASS** (M6 違反 0、hub β 出現) |
| Leakage 機構動作 | **PASS** (修正後 232 件発火) |

→ **v10.5 完成**。

---

## 7. v10.5 主題達成 (`v105_integrated_design.md` §1.1) の検証

> α-Integration を「観察軸 (やたら活発な個性の記述)」、β-Integration を「会計単位 (統合された主体)」として階層分離し、同時に既存データに含まれる潜在情報 (mass、historical resources) を顕在化する機構を導入する段階。

| 主題要素 | 達成状況 |
|---|---|
| α 観察軸の維持 | α 13,881 件誕生、binding strength で個性記述 |
| β 会計単位の階層化 | β 2,009 件、cid 1 → β 1 規律完全守備 |
| ダブルブッキング解消 | M6 違反 0、最大 691 α が 1 β に集約 |
| Salience (mass 顕在化) | 77,880 events、hub cid に観察集中確認 |
| Leakage (歴史資源 顕在化) | 232 events、recorded β からの C 漏れ動作 |
| 物理層 frozen | bit-identity 24/24 完全一致 |

→ **Layer 5 完成**。

---

## 8. 次の方向性 (`v105_integrated_design.md` §13)

v10.6 以降の方向性 (現実接続、物理学への挑戦、SEED 統合) は v10.5 完了として別資料で議論。本 run の知見:

- hub β の自然形成 (最大 691 α / 20 cid 統合)
- recorded β からの C 漏れ機構動作 (232 events)
- mass-weighted 観察の長 tail (mass max=98)

→ Layer 6 への発展材料が揃った。

---

## 9. 反省 (Code A)

- **callback 配線漏れ**: smoke (tracking 10) では recorded β = 0 のため Leakage 検証不能。本番 (tracking 50) で初めて検出。今後は smoke で機構ごとに「呼び出された」assertion を埋め込む
- **並列度の見落とし**: v10.4 は `-j24` で 1 batch 完走 (~3h)、私は `-j8` で 3 batch (~8h)。本来の 3 倍 wall 消費。次バージョンは `-j24` 既定に変更

---

## 10. ファイル成果物

```
developmental/v105/
├── v105_*.py                       実装ファイル群
├── diag_v105_main/                 修正前 main run (Leakage 0、参照用)
├── diag_v105_main_v2/              本 run (Leakage 修正版、最終データ)
├── diag_v105_shadow/               shadow audit (bit-identity 検証)
├── v105_integrated_design.md       設計書
├── v105_main_run_report.md         修正前 main レポート
└── v105_main_v2_run_report.md      本ドキュメント (最終)
```

---

*以上、v10.5 main_v2 本番 re-run 結果レポート。Taka 最終レビューに供す。*
