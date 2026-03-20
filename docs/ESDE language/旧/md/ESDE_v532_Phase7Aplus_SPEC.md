# ESDE Engine v5.3.2 - Phase 7A+ 仕様書

## 概要

Phase 7A+ は **Multi-Hypothesis Routing + Variance Gate** の実装です。
未知語に対して A/B/C/D を一発で決めず、各ルートの仮説を並列評価し、
「決めない（abstain）」を正常系として扱います。

---

## 設計思想

1. **「決めない」が正解**: 仮説が競合する場合は abstain（queue に積む）
2. **誤爆回避が最優先**: typo 補正がタイトル/固有表現を壊すリスクを避ける
3. **観測点の保存**: 全仮説のスコアと根拠を記録し、後段で再評価可能に

---

## 新規コンポーネント

### UnknownTokenRouter クラス

```python
class UnknownTokenRouter:
    def evaluate(token, original_text, tokens, token_index, 
                 synset_ids, has_direct_edges, has_proxy_edges, 
                 typo_candidates) -> RoutingReport
```

### RoutingReport 形式

```json
{
  "token": "ops",
  "pos": "u",
  "context": {
    "text": "ops I did it again",
    "tokens": ["ops", "i", "did", "it", "again"],
    "window": ["ops", "i", "did"],
    "capitalized": false,
    "has_quotes": false,
    "title_like_ngram": true,
    "title_phrase_matched": "did it again"
  },
  "hypotheses": [
    {"route": "A", "label": "typo", "candidate": "oops", "score": 0.70, "evidence": {...}},
    {"route": "B", "label": "proper_noun_or_title", "candidate": null, "score": 0.50, "evidence": {...}},
    {"route": "C", "label": "molecule_candidate", "candidate": null, "score": 0.22, "evidence": {...}},
    {"route": "D", "label": "noise", "candidate": null, "score": 0.05, "evidence": {...}}
  ],
  "decision": {
    "action": "abstain",
    "reason": "variance_high",
    "winner": null,
    "margin": 0.20,
    "entropy": 1.12
  }
}
```

---

## Variance Gate（揺れ検知）

### 判定条件

```python
if margin < 0.20 or entropy > 0.90:
    action = "abstain"  # 決めない → queue に積む
else:
    action = "apply_" + winner  # 勝者を適用
```

### 設定値

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `UNKNOWN_MARGIN_TH` | 0.20 | margin がこれ未満なら abstain |
| `UNKNOWN_ENTROPY_TH` | 0.90 | entropy がこれ超なら abstain |

---

## Context Features（文脈特徴）

### Title-Like N-gram Detection

`TITLE_LIKE_PHRASES` (約40パターン) をチェック:
- "did it again", "i love you", "let it be", "devops" など
- 一致すると Route B のスコアを +0.20、Route A を -0.15

### その他の特徴

| 特徴 | 説明 | B への boost |
|------|------|-------------|
| `capitalized` | 入力がタイトルケース | +0.20 |
| `has_quotes` | 引用符で囲まれている | +0.20 |
| `title_like_ngram` | フレーズ辞書に一致 | +0.20 |
| `typo_penalty_when_title_like` | タイトル文脈での A への penalty | -0.15 |

---

## 各ルートの処理

| ルート | action | 処理 |
|--------|--------|------|
| A | apply_A | typo 補正を適用（1回のみ） |
| B | apply_B | 概念化せず queue に積む（外部参照待ち） |
| C | apply_C | molecule 生成せず queue に積む |
| D | ignore | 何もしない |
| - | abstain | 全仮説を queue に積む |

---

## コンソール出力例

### ケース1: abstain（仮説競合）

```
> ops I did it again

Routing Decisions:
  ops: abstain (variance_high) [A:0.70 B:0.50 C:0.22 D:0.05] margin=0.20 entropy=1.12 (queued)

Unknown Queue:
  queued_records: 1
  deduped_records: 0
```

### ケース2: winner_clear

```
> I am superman

Routing Decisions:
  superman: apply_B (winner=B) margin=0.35 entropy=0.85

Route B (Proper Noun Candidates):
  superman: ['demigod.n.01', 'acid.n.02']
```

---

## Queue Record 拡張

### 新規フィールド

```json
{
  "routing_report": {
    "token": "ops",
    "context": {...},
    "hypotheses": [...],
    "decision": {...}
  }
}
```

既存のフィールド（v5.3.1）はそのまま維持。

---

## 受け入れ基準

| # | 基準 | 状態 |
|---|------|------|
| 1 | `I love you`: stopword 除外維持、unknown queue 0 | ✅ |
| 2 | `ops I did it again`: A候補(oops)と B候補が両方上がり、abstain + queue | ✅ |
| 3 | `I am superman`: B仮説が優勢、apply_B または queue | ✅ |
| 4 | routing_report が queue record に含まれる | ✅ |
| 5 | margin/entropy がログに表示される | ✅ |

---

## 設定一覧

```python
# Phase 7A+: Unknown Routing Variance Gate
UNKNOWN_MARGIN_TH = 0.20
UNKNOWN_ENTROPY_TH = 0.90

# Context feature weights
CONTEXT_TITLE_LIKE_BOOST = 0.20
CONTEXT_CAPITALIZED_BOOST = 0.20
CONTEXT_QUOTE_BOOST = 0.20
CONTEXT_TYPO_PENALTY_TITLE = 0.15
```

---

## 次のフェーズへの接続

- **Phase 7B**: unknown_queue の集計（dedupe・頻度・優先度）
- **Phase 7C**: ルーティング決定の確定（human-in-the-loop）
- **Phase 8**: 外部知識（Web/Wikipedia）との連携
