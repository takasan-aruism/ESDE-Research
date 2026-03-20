# Phase 7B+ 監査パッチ - 変更点サマリー

## 発見された問題（根本原因）

**`Eligible > 0` なのに `Processed = 0` になる理由**:

```
旧実装:
  candidates = filter_candidates(records)  ← Eligible表示
  pending = state.get_pending_by_priority()  ← 実際のループ対象
  
問題: candidates と pending が異なるソースから生成
  → 両者のキー体系が一致せず、lookupに失敗
  → 結果として Processed = 0
```

## 修正内容

### 1. 処理対象リストの統一 (L403-410)

**旧:**
```python
pending = state.get_pending_by_priority(limit=limit * 2)
for entry in pending[:limit]:
    lookup_key = f"{token}|{route}"
    record = record_lookup.get(lookup_key)  # 失敗の可能性
```

**新:**
```python
processing_list = candidates[:limit]
results["skipped_by_filter"] = max(0, len(candidates) - limit)
for record in processing_list:  # candidates を直接処理
```

### 2. 会計整合性チェックの追加 (L667-689)

```python
# Check 1: total = by_route + by_state + eligible
expected_sum1 = by_route + by_state + eligible
if total == expected_sum1:
    print(f"✓ Total breakdown OK")

# Check 2: eligible = processed + skipped_by_filter + skipped_by_validation  
expected_sum2 = processed + by_filter + by_valid
if eligible == expected_sum2:
    print(f"✓ Eligible breakdown OK")
```

### 3. 新規カウンタの追加

| カウンタ | 用途 |
|---------|------|
| `skipped_by_validation` | tokenが空等のバリデーション失敗 |

### 4. デバッグログの追加 (L356-357)

```python
print(f"  - DEBUG candidates list length: {len(candidates)}")
```

## 期待される出力

修正後は以下の会計等式が常に成立:

```
candidates_total 
= skipped_by_route + skipped_by_state + eligible_pending

eligible_pending
= processed + skipped_by_filter + skipped_by_validation
```

**サンプル出力:**
```
--- Accounting Integrity Check ---
✓ Total breakdown OK: 100 = 20 + 30 + 50
✓ Eligible breakdown OK: 50 = 40 + 10 + 0
```

## 7B+ 設計原則の確認

| 原則 | ステータス |
|------|-----------|
| 勝者を自動決定しない | ✅ 維持 |
| A/B/C/D を並列保持 | ✅ 維持 |
| volatility/conflict は評価値 | ✅ 維持 |
| 全レコードをいずれかのカウンタに計上 | ✅ **新規保証** |

## 追加対応が必要な項目

1. **`state.py` の監査**: `get_pending_by_priority()` と `upsert()` のキー整合性確認
2. **A仮説の起動条件**: WordNet + ESDE edge 情報を使った判定への拡張
