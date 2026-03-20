# ESDE Engine v5.3.1 - Phase 7A-min 仕様書

## 概要

Phase 7A-min は v5.3.0 の Unknown Queue に「観測点強化」を追加するパッチです。
**挙動（判定結果・active tokens）は変更なし** - キューに残す情報だけ増やします。

---

## 主要変更点

| 項目 | v5.3.0 | v5.3.1 |
|------|--------|--------|
| Record Schema | 基本フィールドのみ | 全観測点フィールド |
| typo_candidates | Route A のみ | Route B でも併記 |
| Dedup | なし | run内で sha1 ベース重複排除 |
| category_guess | なし | 暫定タグ（確定ではない） |
| abstain_reasons | 単一reason | 理由リスト |

---

## 新規追加フィールド

### A. 追跡・再現性
- `engine_version`: エンジンバージョン
- `timestamp_utc`: ISO 8601 タイムスタンプ
- `run_id`: 実行ID
- `input_text`: 入力テキスト全文
- `token_index`: トークン位置（0-based）

### B. トークン観測
- `token_raw`: 元のトークン
- `token_norm`: 正規化後トークン
- `pos_guess`: POS推定（n|v|a|r|u）
- `is_stopword`: bool
- `is_active`: bool（active tokensに残ったか）
- `is_alpha`: bool
- `len`: トークン長

### C. WordNet観測
- `wn_synsets`: `[{"id": "demigod.n.01", "pos": "n"}, ...]`
- `wn_selected`: 選択されたsynset（あれば）

### D. Synapse観測
- `has_direct_edges`: bool
- `has_proxy_edges`: bool
- `direct_edge_count`: int
- `proxy_edge_count`: int

### E. 不確実性
- `uncertainty`: `{"entropy": float|null, "margin": float|null, "is_volatile": bool|null}`

### F. ルーティング（暫定タグ - 確定ではない）
- `route`: `"A"|"B"|"C"|"D"|null`
- `category_guess`: `"typo_like"|"proper_noun_like"|"slang_like"|"unknown"`
- `action_hint`: `"spellcheck"|"web"|"molecule"|"ignore"`
- `confidence`: float|null

### G. 監査用 evidence
- `reason`: 主要理由
- `abstain_reasons`: 全理由リスト
- `proxy_evidence`: proxy トレース
- `typo_candidates`: `[{"candidate": "oops", "dist": 1, "confidence": 0.75}]`

### H. Dedup追跡
- `dedup_key`: sha1(token_norm|pos|synset)[:16]
- `seen_count_in_run`: run内での出現回数

---

## typo_candidates 併記条件

Route B（固有名詞候補）でも以下の条件を満たせば typo_candidates を記録：

1. `len(token_norm) ∈ [3..6]`（短いトークン）
2. 編集距離1-2の候補が WordNet に存在

**重要**: 補正は実行しない。キューに「後で直せる可能性」を残すだけ。

---

## Dedup 仕様

### キー生成
```python
dedup_key = sha1(token_norm + "|" + pos_guess + "|" + top_synset)[:16]
```

### 動作
- 同一 `dedup_key` は同一 run 内で1回だけ記録
- `dedup_count` でスキップした件数を追跡

---

## category_guess ロジック

```python
def guess_category(token, synset_ids, has_edges, typo_candidates):
    # typo候補が高信頼度
    if typo_candidates and typo_candidates[0]["confidence"] >= 0.5:
        return ("typo_like", "spellcheck", confidence)
    
    # 固有名詞パターン
    if synset_ids and is_proper_noun_candidate(synset_ids):
        return ("proper_noun_like", "web", 0.7)
    
    # synsetなし
    if not synset_ids:
        if len(token) <= 4:
            return ("slang_like", "web", 0.5)
        else:
            return ("unknown", "molecule", 0.3)
    
    # synsetあり、edgeなし
    if synset_ids and not has_edges:
        return ("unknown", "molecule", 0.4)
    
    return ("unknown", "ignore", None)
```

---

## コンソール出力

```
Unknown Queue:
  queued_records: 1
  deduped_records: 0
  path: ./data/unknown_queue.jsonl
  run_id: 20251223_120000_ab12cd
```

---

## サンプルレコード

### 入力: "I am superman"

```json
{
  "engine_version": "5.3.1",
  "timestamp_utc": "2025-12-23T12:00:00+00:00",
  "run_id": "20251223_120000_ab12cd",
  "input_text": "I am superman",
  "token_index": 2,
  "token_raw": "superman",
  "token_norm": "superman",
  "pos_guess": "n",
  "is_stopword": false,
  "is_active": true,
  "is_alpha": true,
  "len": 8,
  "wn_synsets": [
    {"id": "demigod.n.01", "pos": "n"},
    {"id": "acid.n.02", "pos": "n"}
  ],
  "wn_selected": null,
  "has_direct_edges": false,
  "has_proxy_edges": false,
  "direct_edge_count": 0,
  "proxy_edge_count": 0,
  "uncertainty": {"entropy": null, "margin": null, "is_volatile": null},
  "route": "B",
  "category_guess": "proper_noun_like",
  "action_hint": "web",
  "confidence": 0.7,
  "reason": "no_synapse_edges",
  "abstain_reasons": ["no_synapse_edges"],
  "proxy_evidence": [],
  "typo_candidates": [],
  "context_window": ["i", "am", "superman"],
  "notes": "",
  "dedup_key": "a1b2c3d4e5f6g7h8",
  "seen_count_in_run": 1,
  "artifacts": {...}
}
```

---

## 受け入れ基準

| # | 基準 | 状態 |
|---|------|------|
| 1 | レコードが全観測点を含む（A-Hのフィールド） | ✅ |
| 2 | 解析結果（Top Concepts/Levels、active tokens）は v5.3.0 と一致 | ✅ |
| 3 | stopword がキューに入らない（デフォ） | ✅ |
| 4 | Route B でも typo_candidates が record に入る | ✅ |
| 5 | 同一 run 内の重複記録が抑止される（dedup） | ✅ |

---

## 次のフェーズへの接続

- **Phase 7B**: unknown_queue の集計（dedupe・頻度・優先度）
- **Phase 7C**: ルーティング決定（A/B/C/D の確定）
