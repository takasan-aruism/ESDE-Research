# ESDE v5.3.5 Web検索改修

## 変更ファイル

### 1. online_v2.py（新規作成 or online.py を置き換え）

主な変更点：
- **No-search gate**: 検索不要なトークンをスキップ
- **1クエリ化**: 5-7クエリ → 1クエリに削減
- **レート制限**: 指数バックオフ + ジッター
- **失敗処理**: search_status をコレクションに記録

### 2. resolve_unknown_queue_7bplus_v534_final.py（差分適用）

```python
# === 変更1: import 部分（28-39行付近）===

# 変更前
from esde_engine.resolver import (
    QueueStateManager,
    EvidenceLedger,
    SearchCache,
    MockSearchProvider,    # ← 削除または残す（テスト用）
    collect_evidence,
    ...
)

# 変更後
from esde_engine.resolver import (
    QueueStateManager,
    EvidenceLedger,
    SearchCache,
    MockSearchProvider,    # テスト用に残しておく
    SearXNGProvider,       # ← 追加
    collect_evidence,
    ...
)


# === 変更2: search_provider 初期化（2230-2236行付近）===

# 変更前
search_provider = MockSearchProvider()
print("[7B+] Using MockSearchProvider (for testing)")

# 変更後
# SearXNG使用（本番）
search_provider = SearXNGProvider("http://100.107.6.119:8888")  # ワークステーションのIP
print("[7B+] Using SearXNGProvider (self-hosted)")

# テスト時はこちらをコメントアウト解除
# search_provider = MockSearchProvider()
# print("[7B+] Using MockSearchProvider (for testing)")
```


## online_v2.py → online.py への置き換え方法

### 方法A: ファイル置き換え（推奨）
```bash
# バックアップ
cp esde_engine/resolver/online.py esde_engine/resolver/online_backup.py

# 置き換え
cp online_v2.py esde_engine/resolver/online.py
```

### 方法B: 差分マージ
online_v2.py の以下の部分を online.py に追加/置換：

1. `SEARCH_POLICY` 定数（新規）
2. `SHORT_ALLOWLIST` 定数（新規）
3. `VALID_TOKEN_PATTERN` 定数（新規）
4. `should_skip_search()` 関数（新規）
5. `SearchRateLimiter` クラス（新規）
6. `generate_queries()` 関数（置換 - 大幅簡素化）
7. `SearXNGProvider` クラス（新規 or 置換）
8. `collect_evidence()` 関数（置換 - No-search gate追加）
9. `EvidenceCollection` クラス（修正 - search_status追加）


## __init__.py への追加

```python
# esde_engine/resolver/__init__.py

from .online import (
    # 既存
    SearchProvider,
    MockSearchProvider,
    collect_evidence,
    EvidenceCollection,
    # 追加
    SearXNGProvider,
    should_skip_search,
    SearchRateLimiter,
    SEARCH_POLICY,
)
```


## テスト手順

### 1. SearXNG確認
```bash
curl -s "http://localhost:8888/search?q=test&format=json" | head -c 200
```

### 2. 少量テスト（10トークン）
```bash
python resolve_unknown_queue_7bplus_v534_final.py --limit 10
```

### 3. 期待される出力
```
[7B+] Using SearXNGProvider (self-hosted)
...
  ◐ definition: scores=[...] → defer  # または candidate
      (search_status=OK または SKIPPED)
  ◐ 7d: SKIPPED (SHORT_NOT_ALLOWED)   # No-search gateで除外
```


## 効果

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| クエリ数/トークン | 5-7 | 1 |
| 検索スキップ | なし | 15-20% |
| 総クエリ数 | 500-700 | 80-100 |
| 所要時間 | 2.5分（即ブロック） | 3-4分（安全） |
| 失敗時処理 | 不明確 | search_status記録 |


## 注意点

1. **キャッシュクリア**: 古いキャッシュが残っていると新しい検索が実行されない
   ```bash
   rm -rf data/cache/*
   ```

2. **SearXNG設定**: settings.yml で DuckDuckGo/Google を無効化済みか確認

3. **IP確認**: SearXNGProvider のURL がワークステーションのIPと一致しているか
