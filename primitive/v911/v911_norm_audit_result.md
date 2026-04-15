# v9.11 Norm Audit — 実測結果 (Step 0)

*Date: 2026-04-14*
*Script*: `primitive/v911/v911_norm_audit.py` (v9.10 派生、計測のみ)
*目的*: V11_NORM_N (Δ_n 正規化定数) を実測 n_local 分布から決定

## 1. 実行構成

| 項目 | 値 |
|---|---|
| seed | 0 |
| maturation windows | 20 |
| tracking windows | 5 |
| window steps | 500 |
| tag | norm_audit |
| OMP/MKL/OPENBLAS_NUM_THREADS | 1 |
| 実行時間 | 3127s (52min) |

## 2. 計測ロジック

v9.10 本体の認知更新ループ (`spatial_fields` 反復) で
`struct_set = compute_structural(core, max_hops=n_core, ...)` が計算された直後に
`current_struct_size[cid] = len(struct_set)` を stash。
pulse 発火時 (hosted cid のみ、cold_start 含む) に
`n_local = current_struct_size[cid_p]` を `n_local_audit_seed0.csv` に記録。

v9.10 ロジック・出力 CSV には一切変更なし (bit identical)。

## 3. 実測分布

| 統計量 | 値 |
|---|---|
| n | 900 samples |
| min | 2 |
| p10 | 5.00 |
| p50 | 21.00 |
| p90 | 72.10 |
| **p95** | **86.05** |
| max | 152 |
| mean | 31.06 |

## 4. 採用値

**V11_NORM_N = 86** (= floor(p95) = floor(86.05))

### 選択理由

- Rev 2 §3 / 指示書 §10.1 にて「n_local 実測 p95 を採用」と確定
- p95 = 86.05 の小数部を切り捨て整数化
- 値域チェック: `d_n = |n_core - n_local| / 86` は n_core 近傍のほとんどの
  pulse で [0, 1.5] 程度に収まると予想 (p90 = 72 なので通常ケースで |Δn| ≤ 86)
- max=152 の外れ値は稀 (top 5%) でそのまま [0, 1] 超えも許容する設計意図

### 代替案との比較

| 案 | 値 | 備考 |
|---|---|---|
| p50 (中央値) | 21 | 狭すぎて日常 pulse で d_n が [0,1] 超えを多発 |
| p90 | 72 | p95 に比べて外れ値耐性が弱い |
| **p95 (採用)** | **86** | Rev 2 指示どおり |
| p99 | 未計測 | 巨大 struct 外れ値に引っ張られる |
| mean | 31 | 分布が右に長い尾を持つため不適 |

## 5. 出力ファイル

- `primitive/v911/diag_v911_norm_audit_norm_audit/pulse/n_local_audit_seed0.csv`
  (900 rows: seed, cid, t, window, pulse_n, n_local, ev_fired)
- `primitive/v911/diag_v911_norm_audit_norm_audit/pulse/pulse_log_seed0.csv`
  (v9.10 と bit identical であるべき: 別途 diff チェックは Claude Code B で実施)

## 6. 次アクション

1. Claude Code B が `v911_norm_audit_check_request.md` に従いチェック
2. 承認後、実装指示書 §2 の `V11_NORM_N = None` を `V11_NORM_N = 86` に更新
3. Step 1 (v911_cognitive_capture.py 本体実装) に着手

## 7. 再現性

```bash
cd /home/takasan/esde/ESDE-Research/primitive/v911
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python v911_norm_audit.py --seed 0 \
  --maturation-windows 20 --tracking-windows 5 \
  --window-steps 500 --tag norm_audit
```
