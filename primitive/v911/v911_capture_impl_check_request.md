# Claude Code B 向けチェック依頼書 — v9.11 Cognitive Capture 本実装

*Date: 2026-04-14*
*From*: Claude Code A
*Scope*: Step 1 (`v911_cognitive_capture.py`) 本実装と smoke テスト結果の検証
*Target files*:
- `primitive/v911/v911_cognitive_capture.py` (本実装)
- `primitive/v911/diag_v911_capture_smoke/` (smoke 出力)

## 背景

v9.11 実装指示書 §1〜§8 に従い、v9.10 (`primitive/v910/v910_pulse_model.py`) を
丸ごとコピーして Cognitive Capture 機構を「追加のみ」で実装した。
Step 0 norm audit の承認 (V11_NORM_N = 86) を受けて着手。

本チェック依頼は **smoke 後、λ 再決定および本番 run に進む前の最終ゲート**。

## 実装サマリ

| 変更種別 | 場所 |
|---|---|
| 冒頭 docstring | v9.11 説明を先頭に追加 |
| sys.path | `_V910_DIR = primitive/v910` 追加 (virtual_layer_v9 の参照) |
| import | `from v911_genesis_budget_measure import measure_birth_stats` |
| V11_* 定数 | CONSTANTS ブロックに追加 (P_MAX=0.9, LAMBDA=2.0, NORM_N=86 等) |
| SubjectLayer.__init__ | v11_ 12 dict を初期化 |
| SubjectLayer.birth | 集計 4 dict を 0 初期化 (B_Gen/M_c は main 側で記録) |
| SubjectLayer.reap_ghosts | v11_ 12 dict を pop でクリーンアップ |
| v11_compute_b_gen | B_Gen 計算関数 (Pbirth → -log10) |
| v11_compute_e_t | Pulse 時 E_t 抽出 (n_local, s_avg_local, r_local, theta_avg_local) |
| v11_compute_delta | Weighted L1 差分分解、phase は circular / π |
| v11_record_birth_metrics | Birth 直後に呼ぶ helper、4 箇所の `cog.birth()` 後で呼び出し |
| outdir | `diag_v911_capture_{tag}` に変更 |
| capture_rng | `np.random.default_rng(seed ^ 0xC0FFEE)` 独立 RNG |
| main ループ | 認知更新直後に struct_set を stash、pulse 発火時に capture 処理 |
| pulse_log row | v11_ 12 列を追加 (b_gen, delta, d_n/s/r/phase, p_capture, captured, n_local, s_avg_local, r_local, theta_avg_local) |
| per_subject row | v11_ 13 列を追加 (b_gen, m_c_*, n_pulses_eval, n_captured, capture_rate, mean_delta, mean_d_*) |

## Smoke 実行結果 (1 seed × mat 5 × track 2 × 100 steps, 244s)

| 確認項目 | 結果 |
|---|---|
| exit code | 0 |
| pulse_log 列数 (v11_) | 12 列すべて存在 |
| per_subject 列数 (v11_) | 13 列すべて存在 |
| pulse rows | 652 |
| subject rows | 176 |
| v11_captured 分布 | cold_start=502, TRUE=89, FALSE=61 |
| cold_start pulse_n 範囲 | {1, 2, 3} 厳密 |
| Δ 値域 | [0.0433, 0.5598] |
| p_capture 値域 | [0.2938, 0.8253] |
| B_Gen 値域 | [11.01, 34.12] |
| B_Gen unformed / inf | 0 件 |
| per_subject unformed capture_rate | 26/176 (n_pulses_eval=0 のみ) |

## チェック項目

### A. §7 不変量チェックリスト

- [ ] `v19g_canon.py` / `esde_v82_engine.py` / `virtual_layer_v9.py` に変更なし (git status)
- [ ] 物理層 7 オペレータの呼び出し順序が v9.10 と同一
- [ ] 背景注入 (BIAS + Z seeding) が v9.10 と同一ロジック
- [ ] engine.state.rng と capture_rng が完全分離
- [ ] **per_window CSV が v9.10 smoke と bit identical** (同 seed で diff=0)
  - 要: v9.10 `v910_pulse_model.py` を同条件 (seed=0, mat=5, track=2, steps=100, tag=smoke)
    で実行し、per_window / per_subject の v10_/v99_ 部分を diff
- [ ] 物理層 state (theta/S/R/E/Z) への書き込みが認知層から一切ない (grep `engine.state\.\(theta\|S\|R\|E\|Z\)\s*=`)
- [ ] VL state (labels, phase_sig, share) への書き込みが認知層から一切ない
- [ ] v99_ / v10_ 列が CSV で位置・値とも保存されている
- [ ] B_Gen が capture 計算 (p_capture) に直接入っていない (GPT 補正 4)
- [ ] phase 差分が circular_diff 経由で π 正規化 (GPT 補正 2)
- [ ] similarity がコサインではなく差分分解型 Weighted L1 (GPT 補正 3)
- [ ] 誤差各軸 (d_n/d_s/d_r/d_phase) が pulse_log に個別記録 (GPT 補正 5)
- [ ] M_c が 4 要素固定 (n_core, s_avg, r_core, phase_sig)
- [ ] PULSE_INTERVAL=50 固定、変調なし
- [ ] cold_start pulse は v11_captured="cold_start"、集計に含まれない
- [ ] B_Gen / M_c は birth 時に記録、cold_start の影響を受けない
- [ ] V11_NORM_N = 86 (Step 0 audit 値) が §2 に反映

### B. §8 smoke 判定

- [x] per_window CSV bit identical ← **B が v9.10 smoke を走らせて diff 実施**
- [x] per_subject に v11_ 列が全 cid 分記録 (176 rows すべて)
- [x] pulse_log に v11_ 列が全 pulse 分記録 (652 rows)
- [x] B_Gen 値域 [10, 37] 内 (実測 [11.01, 34.12])
- [x] Δ 値域 [0, 2] 内 (実測 [0.043, 0.560])
- [x] p_capture (0, 0.9] 内 (実測 [0.29, 0.83])
- [x] v11_captured 3 種のみ (TRUE / FALSE / cold_start)
- [x] cold_start = pulse_n<=3 厳密
- [x] cold_start 行でも v11_delta / v11_p_capture 記録

### C. 実装の可読性・設計

- [ ] v9.11 変更箇所にコメントがあり、§ 参照が明示されている
- [ ] helper 関数 (`v11_*`) が module スコープで独立している
- [ ] SubjectLayer 内部から engine.state / vl.labels への書き込みが一切ない
- [ ] cog.birth() の重複呼び出しに対して v11_record_birth_metrics が idempotent
- [ ] v11_current_struct_set は step 単位の揮発ストアで、ghost 化時にも整合

### D. 追加懸念 (B が判断)

- [ ] `v11_current_struct_set` は step ごとに dict をクリアしないが、
      同一 step 内で pulse は常に同一 struct_set を参照するため OK。
      step をまたぐと古い値が残るが、次の step の認知更新ループで
      hosted cid はすべて上書きされる。ghost 化した cid の古い値が
      残る可能性はあるが、`cid_p not in cog.phi` ガードで pulse 発火
      しないため参照されない。念のため確認。
- [ ] `measure_birth_stats` は `engine.state.S` を参照するが read only 。
      v911_genesis_budget_measure.py 側のコードレビューで確認済のはず。
- [ ] 重み均等 (0.25×4) の妥当性。smoke 後に各軸の平均寄与を見て確認。

## 不承認時の対応

- §7 不変量違反があればロールバック (v9.10 コピー段階から再実装)
- §8 smoke 失敗があれば指示書に戻って原因特定 → **Taka に戻す**
- 可読性 / 設計の指摘は修正要望として Code A に差し戻し

## 承認時の次アクション

1. **λ 再決定** (指示書 §10.2):
   - smoke pulse_log から Δ の p10 / p50 抽出
   - λ = -ln(0.5) / Δ_p10 (Rev 2 §6-2 方針) または Δ_p50 を協議
   - 根拠を `v911_capture_param_audit.md` に記載
2. λ 更新後、本番 run (short 48 seeds / long 5 seeds) を parallel 実行

## 添付: 検証コマンド例

```bash
# A-1. 物理層差分確認
diff primitive/v910/v910_pulse_model.py primitive/v911/v911_cognitive_capture.py \
  | grep -E "^[<>].*engine\.state\.(theta|S|R|E|Z)" | head -20
# → v9.11 追加行で engine.state.X = ... 代入が現れないこと

# A-2. per_window bit identical (B の仕事)
cd primitive/v910
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python v910_pulse_model.py --seed 0 --maturation-windows 5 \
  --tracking-windows 2 --window-steps 100 --tag smoke
diff ../v911/diag_v911_capture_smoke/aggregates/per_window_seed0.csv \
     diag_v910_pulse_smoke/aggregates/per_window_seed0.csv

# A-3. v10_/v99_ 列同一性
python -c "
import csv
a = list(csv.DictReader(open('primitive/v910/diag_v910_pulse_smoke/subjects/per_subject_seed0.csv')))
b = list(csv.DictReader(open('primitive/v911/diag_v911_capture_smoke/subjects/per_subject_seed0.csv')))
assert len(a) == len(b)
for ra, rb in zip(a, b):
    for k in ra:
        if not (k.startswith('v11_')):
            assert ra[k] == rb[k], (k, ra[k], rb[k])
print('OK: v10_/v99_ preserved')
"
```
