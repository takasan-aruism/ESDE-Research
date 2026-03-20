# ESDE Phase 7B+ v5.3.4 仕様書マッピング

## 仕様書セクションと実装の対応

| 仕様書セクション | 要件 | 実装ファイル | 実装箇所 | ステータス |
|-----------------|------|-------------|---------|-----------|
| §1. 設計原則 | 自動勝者を作らない | v534.py | L194 `"winner": None` | ✅ |
| §1. 設計原則 | 対称性の保持 | hypothesis.py | 各evaluate_hypothesis_X | ✅ |
| §1. 設計原則 | 三項創発的評価 | v534.py | AggregatedRecord | ✅ |
| §1. 設計原則 | 揺れ(Volatility)検知 | hypothesis.py | compute_global_volatility | ✅ |
| §1. 設計原則 | 人間レビュー前提 | v534.py | L739 メッセージ | ✅ |
| §5. スコアリング | 独立スコア | hypothesis.py | L878-882 | ✅ |
| §5. スコアリング | COMPETE_TH | config.py | centralized | ✅ |
| §6. Volatility定義 | 計算式 | hypothesis.py | L779-808 | ✅ |
| §6. Volatility定義 | 判定基準 | hypothesis.py | L815-849 | ✅ |
| **§7. 集約** | aggregate_key | v534.py | L67-77 | ✅ **NEW** |
| **§7. 集約** | count/examples | v534.py | L103-107 | ✅ **NEW** |
| **§7. 集約** | scores_avg/max | v534.py | L109-113 | ✅ **NEW** |
| **§7. 集約** | volatility_avg/max | v534.py | L115-118 | ✅ **NEW** |
| **§7. 集約** | first/last_seen_run_id | v534.py | L120-124 | ✅ **NEW** |
| §8. State管理 | aggregate_key単位 | v534.py | L327-342, L529 | ✅ **NEW** |
| §11. 受入条件 | Eligible=Processed | v534.py | L580-617 | ✅ |
| §11. 受入条件 | 同一token集約 | v534.py | AggregatedRecord | ✅ |
| §11. 受入条件 | winner=null維持 | v534.py | L194 | ✅ |
| §11. 受入条件 | volatility非ゼロ | hypothesis.py | compute_* | ✅ |
| §11. 受入条件 | accounting一致 | v534.py | verify_accounting | ✅ |

---

## 旧版との主要差分

### 1. 集約機能の追加 (§7)

**旧版 (v5.3.3):**
```python
# 個別レコードをそのまま出力
for record in processing_list:
    output_records.append(create_7bplus_record(...))
```

**新版 (v5.3.4):**
```python
# aggregate_key でグループ化してから出力
aggregates: Dict[str, AggregatedRecord] = {}

for record in processing_list:
    agg_key = generate_aggregate_key(token, pos, route_set)
    if agg_key not in aggregates:
        aggregates[agg_key] = AggregatedRecord(...)
    aggregates[agg_key].add_occurrence(report, record, run_id)

for agg_key, agg in aggregates.items():
    output_records.append(agg.to_dict())
```

### 2. aggregate_key の生成 (§7)

```python
def generate_aggregate_key(token_norm: str, pos: str, route_set: Set[str]) -> str:
    """
    仕様: aggregate_key = (normalized_token, pos, route_set)
    """
    route_str = ",".join(sorted(route_set))
    key_tuple = f"{token_norm}|{pos or 'UNK'}|{route_str}"
    return hashlib.md5(key_tuple.encode()).hexdigest()[:16]
```

### 3. State管理の変更 (§8)

**旧版:** record の hash_key 単位
```python
state.get_state(record.get("hash"))
state.update_status(hash_key, status, reason)
```

**新版:** aggregate_key 単位
```python
agg_key = generate_aggregate_key(token, pos, route_set)
state.get_state(agg_key)
state.update_status(agg_key, status, reason)
```

### 4. 出力フォーマットの変更

**旧版:** 単一出現のレコード
```json
{
  "token": "example",
  "hypotheses": {...},
  "global_volatility": 0.35
}
```

**新版:** 集約レコード
```json
{
  "aggregate_key": "a1b2c3d4e5f6g7h8",
  "token_norm": "example",
  "count": 3,
  "examples": [...],
  "scores_avg": {"A": 0.15, "B": 0.42, "C": 0.0, "D": 0.18},
  "scores_max": {"A": 0.20, "B": 0.50, "C": 0.0, "D": 0.25},
  "volatility_avg": 0.38,
  "volatility_max": 0.45,
  "first_seen_run_id": "20250101_120000",
  "last_seen_run_id": "20250115_090000"
}
```

---

## AggregatedRecord クラス詳細

```python
class AggregatedRecord:
    """仕様書§7準拠の集約レコード"""
    
    # 識別子
    token_norm: str
    pos: str
    route_set: Set[str]
    aggregate_key: str  # MD5 hash of (token_norm, pos, route_set)
    
    # 出現統計 (§7)
    count: int                          # 出現回数
    examples: List[Dict]                # 最大N件の原文
    
    # スコア統計 (§7)
    scores_sum: Dict[str, float]        # 合計（avg計算用）
    scores_max: Dict[str, float]        # 最大値
    
    # Volatility統計 (§7)
    volatility_sum: float               # 合計（avg計算用）
    volatility_max: float               # 最大値
    
    # タイミング (§7)
    first_seen_run_id: str
    last_seen_run_id: str
    
    def get_final_status(self) -> str:
        """
        仕様書§6に基づく最終ステータス決定
        
        - quarantine優先（一度でもquarantineなら）
        - volatility_max >= 0.50 → quarantine
        - volatility_avg >= 0.25 → defer
        - それ以外 → candidate
        """
```

---

## 会計整合性の保証 (§11)

```
candidates_total (100)
├── skipped_by_route (20)
├── skipped_by_state (30)
└── eligible_pending (50)
      ├── processed (48)
      │     → aggregated (35 unique keys)
      │           ├── quarantined (10)
      │           ├── deferred (15)
      │           └── candidate (10)
      ├── skipped_by_filter (2)
      └── skipped_by_validation (0)

検証:
✓ 100 = 20 + 30 + 50
✓ 50 = 48 + 2 + 0
```

---

## 使用例

```bash
# 基本実行
python resolve_unknown_queue_7bplus_v534.py --limit 100

# ドライラン（出力なし）
python resolve_unknown_queue_7bplus_v534.py --dry-run

# 再処理（defer済み含む）
python resolve_unknown_queue_7bplus_v534.py --reprocess

# 統計表示
python resolve_unknown_queue_7bplus_v534.py --stats

# カスタムrun_id
python resolve_unknown_queue_7bplus_v534.py --run-id "manual_audit_20250101"
```

---

## 出力サンプル

```
============================================================
ESDE Engine v5.3.4 - Phase 7B+ Resolver (v5.3.4 Spec)
============================================================

Key: ⊘=quarantine  ◐=defer  ○=candidate
Note: NO automatic winners - all hypotheses preserved
Note: Aggregation by (token_norm, pos, route_set)

[7B+] Loading queue: ./data/unknown_queue.jsonl
[7B+] Loaded 150 records

[7B+] Candidates breakdown:
  - Total records: 150
  - Skipped by route: 30
  - Skipped by state: 20
  - Eligible for processing: 100
  - DEBUG candidates list length: 100

[7B+] Processing 100 of 100 eligible records
[7B+] Note: NO automatic winners - all hypotheses preserved
[7B+] Run ID: 20250124_143000

  ◐ foobar: scores=[A:0.15 B:0.42 C:0.00 D:0.18] competing=[A,B,D] compete_th=0.15 winner=null vol=0.38 → defer
      A_reason=PLAUSIBLE_TYPO:len=6
      B_reason=ENTITY_DETECTED:person:2
      D_reason=SHORT:3

[7B+] Aggregation complete: 75 unique aggregate keys from 100 records
    ↳ Aggregated: foobar (3 occurrences) → defer

--- Accounting Integrity Check ---
✓ Total breakdown OK: 150 = 30 + 20 + 100
✓ Eligible breakdown OK: 100 = 100 + 0 + 0

--- Processing Results ---
Records processed: 100
Aggregated to:     75 unique keys

--- Aggregate Status ---
Quarantined:   15 (high volatility)
Deferred:      40 (medium volatility)
Candidate:     20 (low volatility)

Remember: Candidate status does NOT mean 'resolved'.
All records need human review before any patches are applied.
winner=null is ALWAYS maintained (v5.3.4 spec).
```
