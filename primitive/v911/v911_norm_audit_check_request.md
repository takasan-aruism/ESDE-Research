# Claude Code B 向けチェック依頼書 — v9.11 Norm Audit

*Date: 2026-04-14*
*From*: Claude Code A
*Scope*: Step 0 (Norm audit) の実装と測定結果の検証
*Target files*:
- `primitive/v911/v911_norm_audit.py` (計測スクリプト)
- `primitive/v911/v911_norm_audit_result.md` (測定結果)
- `primitive/v911/diag_v911_norm_audit_norm_audit/pulse/*.csv` (出力)

## 背景

v9.11 実装指示書 §10.1 に従い、V11_NORM_N を実測 n_local 分布の p95 から決定するため、
v9.10 (`primitive/v910/v910_pulse_model.py`) の派生スクリプトを作成し 1 seed × short 構成で実行した。

本チェック依頼は **Step 1 (本実装) に進む前の最終ゲート**。

## チェック項目

### A. 計測パッチの bit identical 保証

- [ ] `v911_norm_audit.py` と `primitive/v910/v910_pulse_model.py` の diff を取り、
      変更が以下 5 箇所のみであることを確認:
  1. 冒頭 docstring の追記
  2. `sys.path` への `_V910_DIR` (primitive/v910) 追加
  3. `outdir = Path(f"diag_v911_norm_audit_{tag}")` に rename
  4. `current_struct_size` / `v911_n_local_log` 初期化
  5. 認知更新ループ後の `current_struct_size[cid] = len(struct_set)` 行追加
  6. pulse 発火ループでの n_local 記録ブロック追加
  7. 末尾の n_local_audit CSV 出力ブロック追加

- [ ] v9.10 既存 CSV (per_window / per_subject / pulse_log / introspection /
      pickup / death_pool など) のカラム順序・内容に変更がない

- [ ] RNG 分岐が増えていない (`current_struct_size` 更新は純粋 read-side)

- [ ] 認知層から engine.state / vl.labels / pickup 機構への書き込みが発生していない

### B. 測定結果の妥当性

- [ ] `n_local_audit_seed0.csv` の行数が 900、
      すべての pulse_n, n_local が整数値であること
- [ ] 分布統計 (min=2, p10=5, p50=21, p90=72.1, **p95=86.05**, max=152, mean=31.06) が
      CSV の実データと一致すること (`numpy.percentile` で再計算して同値)
- [ ] p95 採用値 **V11_NORM_N = 86** (floor(86.05)) が妥当であること
  - 代替 (p50=21 / p90=72 / 小数そのまま 86.05 / p99) と比べて合理的か
  - v9.11 capture 計算で d_n が [0, ~1.5] 程度に収まる見込みか

### C. 実行の再現性

- [ ] `v911_norm_audit.py` を同じコマンドで再実行した場合、
      bit identical な出力が得られること (seed 固定 + 独立 RNG 未導入のため)
  - ※ ただしこの項は時間がかかるので任意 (A/B 確認のみで先に進んで可)

### D. 指示書との整合

- [ ] 指示書 §10.1 に書かれた全要件を満たしているか
  - 1 seed × short 構成 ✓
  - 計測のみ、v9.10 bit identical 目指し ✓
  - 結果を audit.md に記載 ✓
  - V11_NORM_N = p95 採用 ✓

### E. 追加確認事項 (発見したら報告)

- [ ] n_local=2 (struct_set の最小 ≥ 2 ガード) が下限になっていることの意味づけ
  - `structural_stats` が `len(struct_set) < 2` で早期 return するが、
    n_local はその前の len を記録しているので 2 以上が自然
- [ ] cold_start 中 (pulse_n ≤ 3) の n_local と通常 pulse の n_local に偏りがないか
  - CSV の `pulse_n` 列で絞って比較できる

## 不承認時の対応

- 計測パッチに非自明な変更があればロールバック後に再依頼
- 分布計算ミスがあれば V11_NORM_N 再決定
- 許容できない場合は **Taka に戻して再指示を仰ぐ** (A/B だけで判断しない)

## 承認時の次アクション

1. Claude Code A が実装指示書 §2 の `V11_NORM_N = None` を `V11_NORM_N = 86` に更新
2. Step 1: `v911_cognitive_capture.py` 本体実装に着手
3. 本実装後、smoke → V11_LAMBDA 再決定 → 本格 run の順で進行

---

## 添付: diff ヒント

```bash
diff -u primitive/v910/v910_pulse_model.py primitive/v911/v911_norm_audit.py
```

上記 diff の規模はおよそ +50 行、-1 行 (outdir 名変更) 程度であるべき。
