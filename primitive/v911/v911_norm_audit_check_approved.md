# Claude Code B チェック結果 — v9.11 Norm Audit (承認)

*Date: 2026-04-15*
*Reviewer*: Claude Code B
*Verdict*: **承認 (Step 1 進行可)**
*Adopted*: `V11_NORM_N = 86`

---

## 結論

`v911_norm_audit.py` は v9.10 の bit identical 派生として要件を満たし、
測定結果も再計算と完全一致。`V11_NORM_N = 86` (= floor(p95)) の採用は
指示書 §10.1 と整合。Step 1 (`v911_cognitive_capture.py` 本実装) に進んでよい。

---

## A. 計測パッチ bit identical

`diff -u primitive/v910/v910_pulse_model.py primitive/v911/v911_norm_audit.py`
を取得した結果、変更は依頼書記載の **7 箇所のみ** で、すべて「追加」または
「outdir 名変更 1 行」。

| # | 箇所 | 種別 | 確認 |
|---|---|---|---|
| 1 | 冒頭 docstring 追記 (L2-23) | 追加 | ✓ |
| 2 | `_V910_DIR` を sys.path に追加 (L101, L104) | 追加 | ✓ |
| 3 | `outdir` を `diag_v911_norm_audit_{tag}` に変更 (L1131) | 変更 1 行 | ✓ |
| 4 | `current_struct_size` / `v911_n_local_log` 初期化 (L1245-1249) | 追加 | ✓ |
| 5 | 認知更新ループ後 `current_struct_size[cid] = len(struct_set)` (L1354-1355) | 追加 | ✓ |
| 6 | pulse 発火ループ n_local 記録ブロック (L1409-1423) | 追加 | ✓ |
| 7 | 末尾 n_local_audit CSV 出力ブロック (L1953-1973) | 追加 | ✓ |

### サブチェック

- **既存 CSV 不変**: `outdir` 名以外の出力ロジック・カラム順序に変更なし。
  v9.10 既存 CSV (per_window / per_subject / pulse_log / introspection /
  pickup / death_pool 等) のヘッダ・writerow 部分は diff に現れない。
- **RNG 分岐ゼロ**: 追加コードは `current_struct_size.get(cid_p, 0)` の
  read のみ。`np.random` / `random` 呼び出しは増えていない。
- **engine.state / vl.labels / pickup への書き込みなし**: 追加部はすべて
  ローカル dict (`current_struct_size`, `v911_n_local_log`) への append/assign のみ。
  認知層 → engine.state / vl.labels / pickup 機構への mutation は発生していない。

→ **A: 全項目クリア**

---

## B. 測定結果の妥当性

`n_local_audit_seed0.csv` を `numpy.percentile` で再計算:

```
rows: 900
non-integer rows: 0
min  = 2
p10  = 5.00
p50  = 21.00
p90  = 72.10
p95  = 86.05
p99  = 118.01
max  = 152
mean = 31.06
floor(p95) = 86
```

`v911_norm_audit_result.md` §3 の値と **完全一致** (小数誤差なし)。

- 行数 900 ✓
- pulse_n / n_local すべて整数 ✓
- 分布統計 (min=2, p50=21, p95=86.05, max=152, mean=31.06) 一致 ✓
- `V11_NORM_N = 86 = floor(86.05)` 妥当 ✓

代替案との比較は result.md §4 の評価通り:
p50=21 は狭すぎ、p99=118 は外れ値に引っ張られる、
mean=31 は右裾分布で不適切。**p95 採用が合理的**。

→ **B: 全項目クリア**

---

## C. 再現性

依頼書通り任意項目につき未実施 (52min 再走を回避)。seed 固定 + RNG 分岐
未追加 (A で確認) のため、論理的に bit identical が期待できる。

→ **C: スキップ (許容)**

---

## D. 指示書 §10.1 整合

- 1 seed × short 構成 (seed=0, mat=20, track=5, win=500) ✓
- v9.10 bit identical (A で確認) ✓
- 結果を `v911_norm_audit_result.md` に記載 ✓
- V11_NORM_N = p95 採用 (= 86) ✓

→ **D: 全項目クリア**

---

## E. 追加確認

### E-1: n_local 下限 = 2 の意味づけ

`current_struct_size[cid] = len(struct_set)` は `compute_structural` の直後
かつ `structural_stats` の `< 2` 早期 return より前で記録される。
観測下限 2 は struct_set が 0/1 のケースが当該 cid では発生しなかったか、
発生しても pulse 発火条件を満たさなかったことを意味し、自然な結果。

### E-2: cold_start vs 通常 pulse の偏り

| 区分 | n | mean | p95 |
|---|---|---|---|
| cold (pulse_n ≤ 3) | 81 | 25.11 | 81.0 |
| 通常 (pulse_n > 3) | 819 | 31.65 | 86.10 |

cold_start は若干小さめだが p95 で 5 程度の差にとどまり、`V11_NORM_N = 86`
の採用判断に影響しない。

→ **E: 報告事項なし (補足記載のみ)**

---

## 承認後の次アクション (依頼書 §承認時アクションを再掲)

1. 実装指示書 §2 の `V11_NORM_N = None` を `V11_NORM_N = 86` に更新
2. Step 1: `v911_cognitive_capture.py` 本体実装に着手
3. 本実装後、smoke → V11_LAMBDA 再決定 → 本格 run

---

## 確認ログ (実コマンド)

```bash
diff -u primitive/v910/v910_pulse_model.py primitive/v911/v911_norm_audit.py
# → 追加 +50 行前後、変更 -1/+1 行 (outdir のみ)。依頼書記載と一致。

wc -l diag_v911_norm_audit_norm_audit/pulse/n_local_audit_seed0.csv
# → 901 (header + 900 rows)

python3 -c "import numpy as np, csv; ..."
# → min=2, p50=21, p95=86.05, max=152, mean=31.06  (result.md と一致)
```
