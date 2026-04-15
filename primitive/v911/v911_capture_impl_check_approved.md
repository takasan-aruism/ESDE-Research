# Claude Code B チェック結果 — v9.11 Cognitive Capture 本実装 (承認)

*Date: 2026-04-15*
*Reviewer*: Claude Code B
*Verdict*: **承認 (本番 run 進行可)**
*Target commit*: 24ec112

---

## 結論

`v911_cognitive_capture.py` は §7 不変量チェックリスト 14 項目すべてをクリアし、
smoke 結果も §8 判定基準を満たす。`V11_LAMBDA = 2.724` の決定根拠も
`v911_capture_param_audit.md` に Δ 実分布数値つきで記録され妥当。
本番 run (short 48 seeds / long 5 seeds) に進んでよい。

---

## A. §7 不変量チェックリスト (14 項目)

| # | 項目 | 結果 |
|---|---|---|
| 1 | `v19g_canon.py` / `esde_v82_engine.py` / `virtual_layer_v9.py` 1 byte も変更なし | ✓ git log にて当該 3 ファイルへの commit は v910 originalの 18379be のみ。HEAD に変更なし |
| 2 | 物理層 7 オペレータの呼び出し順序が v9.10 と同一 | ✓ diff で main ループの構造変更なし、追加は認知層側のみ |
| 3 | 背景注入 (BIAS + Z seeding) v9.10 と同一 | ✓ diff で該当ロジック変更なし |
| 4 | engine.state.rng と capture_rng が完全分離 | ✓ L1342: `capture_rng = np.random.default_rng(seed ^ 0xC0FFEE)`、capture_rng は L1647 の capture 判定でのみ使用 |
| 5 | per_window CSV bit identical | ✓ `diff` exit 0 (v910/diag_v910_pulse_smoke vs v911/diag_v911_capture_smoke) — per_window_seed0.csv & conv_bias_seed0.json 完全一致 |
| 6 | 物理層 state (theta/S/R/E/Z) への書き込みが認知層から一切ない | ✓ Grep `engine\.state\.(theta\|S\|R\|E\|Z)\s*=` → No matches |
| 7 | VL state (labels, phase_sig, share) への書き込みが認知層から一切ない | ✓ Grep `vl\.labels[\.\[]\|\.phase_sig\s*=\|\.share\s*=` → 該当なし。`vl.labels[lid]` は read-only 引数渡し |
| 8 | v99_/v10_ 列が CSV で位置・値とも保存 | ✓ per_subject 176 行で v11_ 以外 0 mismatch、列削除なし、v11_ 列 13 個追加のみ |
| 9 | B_Gen が capture 計算に直接入っていない (GPT 補正 4) | ✓ `v11_compute_delta` (L1254-) は m_c の n_core/s_avg/r_core/phase_sig のみ使用、b_gen 不参照 |
| 10 | phase 差分が circular_diff 経由で π 正規化 (GPT 補正 2) | ✓ L1261-1262: `circular_diff(...)`, `abs(d_phase_raw) / math.pi` |
| 11 | similarity が差分分解型 Weighted L1 (GPT 補正 3、コサインでない) | ✓ L1258-1264: 各軸 abs 差分 → 重み付き和、内積/ノルム未使用 |
| 12 | 誤差各軸 (d_n/d_s/d_r/d_phase) が pulse_log に個別記録 (GPT 補正 5) | ✓ pulse_log v11_ 列 12 個に `v11_d_n/d_s/d_r/d_phase` 全部存在 |
| 13 | M_c が 4 要素固定 (n_core, s_avg, r_core, phase_sig) | ✓ `v11_record_birth_metrics` で記録される dict は 4 要素のみ |
| 14 | PULSE_INTERVAL=50 固定、変調なし | ✓ L154: `PULSE_INTERVAL = 50`。v9.10 と同じ箇所のみで使用 (L206/1578/1581)、変調コード追加なし |
| 追 | cold_start pulse は `v11_captured="cold_start"`、集計除外 | ✓ L1638-1647: `pulse_n <= COLD_START_PULSES` 分岐で集計スキップ。実測 cold_start pulse_n = {1,2,3} 厳密 |
| 追 | B_Gen / M_c は birth 時に記録、cold_start の影響を受けない | ✓ `v11_record_birth_metrics` は 4 ヶ所の `cog.birth()` 後で呼ばれ、idempotent (`if cid in cog.v11_b_gen: return`) |
| 追 | V11_NORM_N = 86 が §2 に反映 | ✓ L87: `V11_NORM_N = 86` (Step 0 audit 値) |

→ **A: 全項目クリア**

### 補足: diff 規模

`diff -u v910/v910_pulse_model.py v911/v911_cognitive_capture.py` → 465 行。
すべて追加 (docstring / 定数 / SubjectLayer dict / helper 3 関数 /
record_birth_metrics 4 ヶ所呼び出し / pulse-time capture ブロック /
per_subject summary lambda / outdir 名 1 行変更) で、既存ロジック改変なし。

---

## B. §8 smoke 判定

実測値は依頼書記載と完全一致 (再計算済):

| 項目 | 期待 | 実測 | 結果 |
|---|---|---|---|
| pulse_log v11_ 列数 | 12 | 12 | ✓ |
| per_subject v11_ 列数 | 13 | 13 | ✓ |
| pulse rows | 652 | 652 | ✓ |
| subject rows | 176 | 176 | ✓ |
| v11_captured 種類 | TRUE/FALSE/cold_start | 同 (502/89/61 → cold/TRUE/FALSE) | ✓ |
| cold_start pulse_n 範囲 | {1,2,3} | {1,2,3} | ✓ |
| Δ 値域 | [0, 2] | [0.0433, 0.5598] | ✓ |
| p_capture 値域 | (0, 0.9] | [0.2938, 0.8253] | ✓ |
| B_Gen 値域 | [10, 37] | [11.005, 34.121] | ✓ |
| B_Gen unformed/inf | 0 | 0 | ✓ |

per_window CSV bit identical: A-5 で実施済 (diff exit 0)。

→ **B: 全項目クリア**

---

## C. 実装の可読性・設計

| 項目 | 結果 |
|---|---|
| v9.11 変更箇所にコメント、§ 参照明示 | ✓ 「指示書 §3.4」「§4」「Rev 2 §6.5」等記載多数 |
| helper (`v11_*`) module スコープ独立 | ✓ `v11_compute_b_gen / v11_record_birth_metrics / v11_compute_e_t / v11_compute_delta` いずれもクラス外 |
| SubjectLayer から engine.state / vl.labels への書き込みなし | ✓ Grep 0 件 |
| `cog.birth()` 重複呼び出しに対し `v11_record_birth_metrics` idempotent | ✓ L215: `if cid in cog.v11_b_gen: return` |
| `v11_current_struct_set` 整合 | ✓ step ごとに同一 cid で上書きされ、ghost 化した cid の古い値は `cid_p not in cog.phi` ガードで参照されない |

→ **C: 問題なし**

---

## D. λ 再決定の根拠 (v911_capture_param_audit.md)

| 項目 | 結果 |
|---|---|
| Δ 実分布から p50 基準で算出 | ✓ Δ_p50 = 0.2544 → λ = -ln(0.5)/0.2544 = 2.724 |
| 実測値再計算 (B 側で smoke pulse_log 集計) | ✓ eval n=150, p10=0.131, p50=0.254 — audit.md と完全一致 |
| 採用理由 (p50 基準選択) | ✓ 「p10 (λ=5.285) は選択性高すぎで capture_rate ~0.30 まで落ち捕捉困難」「p50 (λ=2.724) で p_capture≈0.5、半分取れる/半分取り逃しの設計意図」と数値根拠つきで記録 |
| 代替案比較 (p10 / p25 / p50 / 暫定 2.0) | ✓ §2.4 表で λ・期待 capture_rate を併記 |
| 整合性確認 (P_MAX=0.9 と max=0.825 の関係) | ✓ §2.7 で P_MAX を超えないこと確認 |

→ **D: 根拠十分**

---

## E. 追加懸念 (依頼書 §D)

- `v11_current_struct_set` の step 跨ぎ問題: 認識通り、ghost 化 cid の古い値が
  残るが `cid_p not in cog.phi` ガードで pulse 発火が抑制され影響なし。問題なし。
- `measure_birth_stats` は `engine.state.S` の read のみ (`v911_genesis_budget_measure.py` 別途確認済の前提)。
- 重み均等 0.25×4: smoke n=150 では結論不能、param_audit §2.8 に「本格 run 後に
  各軸の `v11_mean_d_*` を比較し再評価」と明記。妥当な保留。

---

## 確認ログ (実コマンド)

```bash
# A-1: 不変量ファイル変更なし
git log --all --oneline -- cognition/v19g_canon.py \
    ecology/engine/esde_v82_engine.py primitive/v910/virtual_layer_v9.py
# → 18379be (v910 original) のみ

# A-5: per_window bit identical
diff primitive/v910/diag_v910_pulse_smoke/aggregates/per_window_seed0.csv \
     primitive/v911/diag_v911_capture_smoke/aggregates/per_window_seed0.csv
# → exit 0 (差分なし)

# A-6/7: 物理/VL state 書き込み
Grep "engine\.state\.(theta|S|R|E|Z)\s*=|vl\.labels[\.\[]" v911_cognitive_capture.py
# → No matches

# A-8: v10/v99 列保存
python3 (per_subject 176 rows compare)
# → non-v11_ mismatches: 0, v11_ cols only in v911: 13 個

# B: smoke pulse_log 集計
python3 (652 rows pulse_log_seed0.csv 集計)
# → captured {cold_start:502, TRUE:89, FALSE:61}, cold_start pulse_n={1,2,3}
# → B_Gen [11.01, 34.12], Δ [0.043, 0.560], p_capture [0.29, 0.83]
# → eval n=150, Δ_p50=0.254 → λ≈2.724 一致
```

---

## 承認後の次アクション (依頼書 §承認時アクションを再掲)

1. λ=2.724 は既に commit 24ec112 で反映済 (param_audit.md §3 履歴)
2. 本番 run 実行:
   - short: `seq 0 47 | parallel -j24 python v911_cognitive_capture.py --seed {} --tracking-windows 10 --tag short`
   - long: `seq 0 4 | parallel -j5 python v911_cognitive_capture.py --seed {} --tracking-windows 50 --tag long`
3. 本番 run 後、`v11_mean_d_*` を seed 横断で集計し重み再評価の要否を判断
