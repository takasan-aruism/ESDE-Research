# ESDE Engine v5.3.0 - Phase 7A 仕様書

## 概要

Phase 7A は Unknown Queue の実装です。未知語・未接続語の「収集」に特化し、分類の決め打ちは後段（Phase 7B/7C）で行います。

---

## 新規コンポーネント

### UnknownQueueWriter クラス

```python
class UnknownQueueWriter:
    def start_run(config_meta) -> run_id      # 処理開始
    def create_record(...) -> Dict            # レコード生成
    def enqueue(record) -> bool               # キューに追加
    def flush()                               # バッファをファイルに書き出し
    def end_run() -> Dict                     # 処理終了、サマリ返却
    def get_stats() -> Dict                   # 統計情報取得
```

---

## 出力ファイル

### `./data/unknown_queue.jsonl`

- **形式**: JSON Lines（1行1レコード）
- **書き込み**: 追記専用（append-only）
- **自動作成**: ディレクトリが存在しない場合は自動作成

---

## レコードスキーマ

### 必須フィールド

```json
{
  "ts": "2025-12-23T12:00:00+00:00",
  "engine_version": "5.3.0",
  "run_id": "20251223_120000_ab12cd",
  "input_text": "I am superman",
  "token": "superman",
  "token_norm": "superman",
  "pos": "n",
  "reason": "no_synapse_edges",
  "wordnet_synsets": ["demigod.n.01", "acid.n.02"],
  "direct_edges_found": 0,
  "proxy_edges_found": 0,
  "proxy_trace": [],
  "notes": ""
}
```

### 推奨フィールド

```json
{
  "token_index": 2,
  "token_source": "tokenizer_v1",
  "stopword_hit": false,
  "is_alpha": true,
  "len": 8,
  "context_window": ["i", "am", "superman"],
  "uncertainty": {"entropy": 0.0, "margin": 1.0},
  "category_guess": null,
  "action_suggestion": null,
  "artifacts": {
    "synapse_file": "esde_synapses_v2_1.json",
    "glossary_file": "glossary_results.json",
    "synapse_hash": "sha256:abc123...",
    "glossary_hash": "sha256:def456..."
  }
}
```

---

## キュー対象（reason値）

| reason | 説明 | キュー対象 |
|--------|------|-----------|
| `no_synsets_in_wordnet` | WordNet検索で0件 | ✅ 常に記録 |
| `no_synapse_edges` | synsetはあるがedgeなし | ✅ 常に記録 |
| `proxy_failed` | proxy探索が失敗 | ✅ 常に記録 |
| `stopword_or_noise` | 機能語/ノイズ | ⚙️ 設定による |

---

## 設定項目

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `QUEUE_FILE_PATH` | `./data/unknown_queue.jsonl` | キューファイルのパス |
| `QUEUE_INCLUDE_NOISE` | `False` | stopword_or_noise を記録するか |
| `QUEUE_BUFFER_SIZE` | `10` | バッファサイズ（N件でflush） |

---

## run_id 命名規則

```
YYYYMMDD_HHMMSS_<random6>
例: 20251223_120000_ab12cd
```

- 秒粒度 + ランダム6文字で衝突回避
- 同一run_id内で同一tokenが複数回出ることを許容（重複排除はPhase 7B以降）

---

## コンソール出力

処理結果の末尾に以下が追加されます：

```
Unknown Queue:
  queued_records: 2
  path: ./data/unknown_queue.jsonl
  run_id: 20251223_120000_ab12cd
```

---

## 期待される動作例

### 入力: "I am superman"

```
Unknown Queue:
  queued_records: 1
  path: ./data/unknown_queue.jsonl
  run_id: 20251223_120000_ab12cd
```

`unknown_queue.jsonl` に以下が追記される：

```json
{"ts":"2025-12-23T12:00:00+00:00","engine_version":"5.3.0","run_id":"20251223_120000_ab12cd","input_text":"I am superman","token":"superman","token_norm":"superman","pos":"n","reason":"no_synapse_edges","wordnet_synsets":["demigod.n.01","acid.n.02"],"direct_edges_found":0,"proxy_edges_found":0,"proxy_trace":[],"notes":"","token_index":2,"token_source":"tokenizer_v1","stopword_hit":false,"is_alpha":true,"len":8,"context_window":["i","am","superman"],"uncertainty":{"entropy":0.0,"margin":1.0},"category_guess":null,"action_suggestion":null,"artifacts":{"synapse_file":"esde_synapses_v2_1.json","glossary_file":"glossary_results.json","synapse_hash":"sha256:...","glossary_hash":"sha256:..."}}
```

---

## 受け入れ基準（Definition of Done）

| # | 基準 | 状態 |
|---|------|------|
| 1 | `unknown_queue.jsonl` が自動生成・追記される | ✅ |
| 2 | `superman` のような「synsetはあるがedgeなし」が記録される | ✅ |
| 3 | reason で `no_synsets_in_wordnet` と `no_synapse_edges` が区別される | ✅ |
| 4 | `QUEUE_INCLUDE_NOISE` で stopword 記録を切り替え可能 | ✅ |
| 5 | 1レコードは単独で解析可能（必須フィールドが揃っている） | ✅ |

---

## 次のフェーズへの接続

- **Phase 7B**: unknown_queue の集計（dedupe・頻度・優先度）
- **Phase 7C**: ルーティング決定（A/B/C/D の確定）
