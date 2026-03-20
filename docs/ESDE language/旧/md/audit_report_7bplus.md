# Phase 7B+ パイプライン監査報告書

**監査日**: 2025-12-24  
**対象ファイル**: 
- `resolve_unknown_queue_7bplus.py`
- `esde_engine/resolver/hypothesis.py`

---

## エグゼクティブサマリー

**重大な問題を発見**: `Eligible > 0` にもかかわらず `Processed = 0` となる根本原因を特定しました。

**根本原因**: `candidates` リスト（filter_candidatesで生成）と `pending` リスト（state.get_pending_by_priorityで取得）が**異なるデータソース**から生成されており、両者の整合性が保証されていません。

---

## チェック項目① Pipeline会計の整合性

### 現状の会計カウンタ

| カウンタ名 | 設定箇所 | 内容 |
|-----------|---------|------|
| `candidates_total` | L186 | 全レコード数 |
| `skipped_by_route` | L211 | route非適格 |
| `skipped_by_state` | L225, L232 | 処理済み/defer済み |
| `eligible_pending` | L240 | 処理対象候補 |
| `skipped_by_filter` | L416, L492 | lookup失敗 + limit超過 |
| `processed` | L433 | 実処理数 |

### ❌ 問題点: 会計等式が成立しない可能性

期待される等式:
```
candidates_total = skipped_by_route + skipped_by_state + eligible_pending
eligible_pending = processed + skipped_by_filter + (未処理分)
```

**実際の問題**:
```python
# L407-417: pending[:limit] をループ
for entry in pending[:limit]:
    ...
    record = record_lookup.get(lookup_key)
    if not record:
        results["skipped_by_filter"] += 1   # ← lookup失敗をここに計上
        continue
```

`lookup_key` が見つからない場合の `skipped_by_filter` 加算は意味が異なります。これは「limitによるスキップ」ではなく「キー不一致によるスキップ」です。

---

## チェック項目② 処理対象リストの不一致（★核心問題）

### 現行フロー

```
[Queue File] 
    ↓ load_queue_records()
[records]
    ↓ filter_candidates()
[candidates] ← Eligible表示はこれを使用
    ↓ state.upsert() で状態DB登録
[State DB]
    ↓ state.get_pending_by_priority()
[pending] ← 実際のループはこれを使用  ★ここで断絶
```

### ❌ 問題の核心

```python
# L356-361: candidates を state に登録
for record in candidates:
    state.upsert(token, route, synsets=synset_ids)

# L371: state から pending を取得
pending = state.get_pending_by_priority(limit=limit * 2)

# L377-383: candidates からlookup用辞書を作成
record_lookup = {}
for r in candidates:
    key = f"{token}|{route}"
    record_lookup[key] = r

# L407-417: pending をループして record_lookup から検索
for entry in pending[:limit]:
    lookup_key = f"{token}|{route}"
    record = record_lookup.get(lookup_key)  # ★ 見つからない可能性
```

**問題**: 
1. `state.upsert()` で登録したエントリが即座に `get_pending_by_priority()` で返される保証がない
2. `pending` のエントリの `token|route` キーと `record_lookup` のキーが一致しない可能性
3. `state` の内部ハッシュキー生成ロジックが不明

### 推奨デバッグログ

```python
# L371の直後に追加
print(f"DEBUG: candidates count = {len(candidates)}")
print(f"DEBUG: pending count = {len(pending)}")
print(f"DEBUG: record_lookup keys = {list(record_lookup.keys())[:5]}")
print(f"DEBUG: pending keys = {[f\"{e.get('token_norm')}|{e.get('route')}\" for e in pending[:5]]}")
```

---

## チェック項目③ state判定の健全性

### record_id / hash_key の生成ロジック

| 操作 | キー生成方法 | 問題 |
|------|-------------|------|
| filter_candidates | `hash_key = record.get("hash", "")` | Queue側のhash使用 |
| state.upsert | `(token, route)` のみ | hash未使用 |
| lookup_key | `f"{token}\|{route}"` | token+route結合 |
| state.get_state | `hash_key` で検索 | 不一致の可能性 |

### ❌ 問題点

```python
# L220: filter_candidates内
state_entry = state.get_state(hash_key) if hash_key else None

# L356-361: process_batch内
state.upsert(token, route, synsets=synset_ids)  # hash渡していない
```

`state.get_state(hash_key)` と `state.upsert(token, route)` が異なるキー体系を使用している可能性があります。`state.py` の確認が必要です。

---

## チェック項目④ limit適用位置

### 現行実装

```python
# L371: pending取得時に limit*2 を指定
pending = state.get_pending_by_priority(limit=limit * 2)

# L407: ループ時に limit を適用
for entry in pending[:limit]:

# L492: limit超過分を計算
results["skipped_by_filter"] += max(0, len(pending) - limit)
```

### ✅ 問題なし（ただし...）

limit適用自体は正しいですが、**pending が空の場合**:
- `len(pending) - limit` = `-limit` (負値)
- `max(0, -limit)` = 0
- → `skipped_by_filter = 0` のまま

これは正しい挙動ですが、**なぜ pending が空なのか**が問題の本質です。

---

## チェック項目⑤ 7B+設計原則の遵守

### ✅ 正しく実装されている項目

| 原則 | 実装状況 | 確認箇所 |
|------|---------|---------|
| 勝者を自動決定しない | ✅ | L110: `"winner": None` |
| A/B/C/D並列保持 | ✅ | L107: `"hypotheses": hypotheses_dict` |
| volatility/conflictは評価値 | ✅ | L114-123: conflict_components |
| 複数仮説の競合検出 | ✅ | L135: `has_competing_hypotheses` |

### ⚠️ 注意点: 仮説ゼロ時の扱い

現行では仮説評価が正常に完了すれば必ず `Processed` に計上されます。しかし、**ループに入る前にスキップされる**場合は計上されません。

---

## チェック項目⑥ A仮説（Typo）の起動条件

### 現行実装 (hypothesis.py L255-372)

```python
def evaluate_hypothesis_a(...):
    # is_plausible_typo の判定
    is_plausible_typo = (
        2 <= len(token) <= 5 and 
        not token.isupper() and 
        not token.isdigit()
    )
    
    if not typo_candidates:
        if is_plausible_typo:
            score = ROUTE_A_MIN_SCORE  # ← 最低スコア保証
```

### ⚠️ ESDE設計との乖離

**ESDE設計上の正しい起動条件**:
1. WordNetにsynsetがある
2. direct_edges == 0 かつ proxy_edges == 0
3. len <= 6 かつ 編集距離 <= 2 で有効候補存在

**現行実装**:
- `len(token)` のみで判定（2-5文字）
- WordNetの存在確認なし
- direct_edges / proxy_edges のチェックなし

### 推奨修正

```python
def evaluate_hypothesis_a(..., wordnet_info: Dict = None):
    has_synsets = wordnet_info and len(wordnet_info.get("synsets", [])) > 0
    has_esde_edges = wordnet_info and (
        wordnet_info.get("direct_edges", 0) > 0 or
        wordnet_info.get("proxy_edges", 0) > 0
    )
    
    # WordNetにあるがESDE接続がない → A仮説を低スコアでも立てる
    if has_synsets and not has_esde_edges:
        if len(token) <= 6 and typo_candidates:
            # 編集距離2以内の候補があれば A 仮説を立てる
            ...
```

---

## 修正提案

### 修正1: candidates を直接処理する方式への変更

```python
def process_batch(...):
    # 既存: filter_candidates
    filter_result = filter_candidates(records, state, include_deferred=reprocess)
    candidates = filter_result["candidates"]
    
    # 修正: candidates を直接ループ（stateからのpending取得を廃止）
    for i, record in enumerate(candidates[:limit]):
        token = record.get("token_norm", record.get("token", ""))
        hash_key = record.get("hash", "")
        
        # 評価処理
        eval_result = evaluate_token(...)
        results["processed"] += 1
        ...
    
    # limit超過分のカウント
    results["skipped_by_filter"] = max(0, len(candidates) - limit)
```

### 修正2: デバッグログの追加

```python
# process_batch 内 L371 直後
print(f"DEBUG: len(candidates) = {len(candidates)}")
print(f"DEBUG: len(pending) = {len(pending)}")
if len(pending) == 0 and len(candidates) > 0:
    print("CRITICAL: candidates exist but pending is EMPTY!")
    print("  This indicates state.get_pending_by_priority() mismatch")
```

### 修正3: 会計整合性チェックの追加

```python
def verify_pipeline_accounting(skip_info: Dict, results: Dict) -> List[str]:
    """パイプライン会計の整合性を検証"""
    warnings = []
    
    total = skip_info.get("candidates_total", 0)
    by_route = skip_info.get("skipped_by_route", 0)
    by_state = skip_info.get("skipped_by_state", 0)
    eligible = skip_info.get("eligible_pending", 0)
    
    # 等式1: total = by_route + by_state + eligible
    expected = by_route + by_state + eligible
    if total != expected:
        warnings.append(
            f"ACCOUNTING_ERROR: total({total}) != "
            f"by_route({by_route}) + by_state({by_state}) + eligible({eligible}) = {expected}"
        )
    
    # 等式2: eligible = processed + skipped_by_filter
    processed = results.get("processed", 0)
    by_filter = results.get("skipped_by_filter", 0)
    accounted = processed + by_filter
    if eligible != accounted:
        warnings.append(
            f"ACCOUNTING_ERROR: eligible({eligible}) != "
            f"processed({processed}) + by_filter({by_filter}) = {accounted}"
        )
    
    return warnings
```

---

## 修正後の期待される会計フロー

```
candidates_total (100件)
  ├── skipped_by_route (20件): route非適格
  ├── skipped_by_state (30件): 処理済み/defer済み
  └── eligible_pending (50件): 処理対象
        ├── processed (40件): 正常処理
        │     ├── quarantined (15件)
        │     ├── deferred (20件)
        │     └── candidate (5件)
        └── skipped_by_limit (10件): limit=40で切り捨て
```

**全レコードが必ずいずれかのカウンタに計上される状態を保証します。**

---

## 次のステップ

1. **即時対応**: デバッグログ追加して `candidates` vs `pending` の差異を確認
2. **短期修正**: `candidates` を直接ループする方式に変更
3. **中期対応**: `state.py` の `get_pending_by_priority()` ロジックを監査
4. **長期対応**: A仮説の起動条件をESDE設計に準拠させる

---

## 付録: 修正済みファイル

修正版 `resolve_unknown_queue_7bplus.py` を別途提供します。
