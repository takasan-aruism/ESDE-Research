# Claude Code B 向けチェック依頼書 — v9.11 本番 run 結果

*Date*: 2026-04-14
*From*: Claude Code A
*Scope*: 本番 run 出力と集計レポート (`v911_cognitive_capture_result.md`) の検証
*Target*:
- `primitive/v911/diag_v911_capture_short/` (48 seeds)
- `primitive/v911/diag_v911_capture_long/` (5 seeds)
- `primitive/v911/v911_cognitive_capture_result.md`

## 背景

本番 run 完了。short 48 seeds × tracking 10 (191min)、long 5 seeds × tracking 50 (198min)。
OMP/MKL/OPENBLAS_NUM_THREADS=1 で parallel -j24 / -j5 で実行。

本チェック依頼は **v9.11 phase 完了判定前の最終ゲート**。

## チェック項目

### A. 出力完整性

- [ ] `diag_v911_capture_short/subjects/per_subject_seed{0..47}.csv` 48 ファイル存在
- [ ] `diag_v911_capture_short/pulse/pulse_log_seed{0..47}.csv` 48 ファイル存在
- [ ] `diag_v911_capture_long/subjects/per_subject_seed{0..4}.csv` 5 ファイル存在
- [ ] `diag_v911_capture_long/pulse/pulse_log_seed{0..4}.csv` 5 ファイル存在
- [ ] 各 CSV に v11_ 12 列 (pulse) / v11_ 13 列 (subject) が全行記録されている
- [ ] v10_/v99_ 列が全 seed 全 cid で保存されている (位置と値)

### B. 集計統計の再現性

- [ ] B_Gen バンド構造 (n_core=2→12, 3→19, 4→26, 5→34) を別の集計コード・別 seed サブセットで再現
- [ ] capture_rate 平均 ~0.39 の妥当性 (λ=2.724 で Δ mean=0.37 なら期待 p = 0.9×exp(-2.724×0.37) = 0.328 ≒ 実測 0.35)
- [ ] 軸寄与 (phase 39% / r 34% / n 14% / s 13%) の再現
- [ ] cold_start 行の pulse_n が全て {1, 2, 3} に限定されている
- [ ] v11_captured の値は TRUE / FALSE / cold_start のみ (他の値混入なし)

### C. 不変量 (Step 1 impl check と同等)

- [ ] `v19g_canon.py` / `esde_v82_engine.py` / `virtual_layer_v9.py` に無変更 (git diff でも 0)
- [ ] per_window CSV が v9.10 と bit identical (同一 seed で smoke diff 実施済のはず)
- [ ] engine.rng と capture_rng の独立性 (本番でも seed 固定なら capture 結果も再現可能)
- [ ] capture_rng は `np.random.default_rng(seed ^ 0xC0FFEE)` で初期化

### D. 長命群 (L06) の解釈妥当性

- [ ] long の n_pulses_eval ≥ 167 を「長命群」と定義するのは合理的か
  (p90 閾値、top 10%、114 cids)
- [ ] 長命群の **capture_rate mean 0.307** が overall 0.379 より低いこと = 「構造複雑化で追跡困難」
  という解釈は妥当か
- [ ] n_core=5 が長命群の 61% を占めること = 「大きな構造が長命化傾向」解釈は妥当か
- [ ] window 別 capture rate の緩やかな低下傾向 (w=20 0.36 → w=69 0.32) は統計ノイズか本質か

### E. 軸寄与の解釈

- [ ] phase (39%) + r (34%) 支配が「認知捕捉のコア指標は位相同期性」という解釈で妥当か
- [ ] n (13%) / s (13%) の寄与が小さいことが問題か、設計意図通りか
- [ ] 重み調整 (v9.12 以降の課題) について、以下どの方向性を取るべきか
  1. 現状維持 (均等重み、phase/r 支配を許容)
  2. 正規化定数の再設計 (n, s の正規化を見直し)
  3. 重み調整 (W_n=W_s 増、W_phase=W_r 減)

### F. レポート内容

- [ ] `v911_cognitive_capture_result.md` の各表が CSV から再計算可能
- [ ] §7 キー発見サマリが本文の内容を正確に要約している
- [ ] §8 示唆 (v9.12 以降) に誤導・過剰解釈なし

## 不承認時の対応

- 出力不完整: 該当 seed を単独再実行
- 集計不整合: CSV 再集計スクリプトを提供してもらい、diff 確認
- 解釈の不一致: Taka に戻して指示仰ぐ

## 承認時の次アクション

1. v9.11 phase 完了判定
2. 結果を Taka とのレビューで共有
3. v9.12 以降の設計検討に移行 (重み / 正規化 / 追加軸 等)

## 添付: 再集計スクリプト (B 用ヒント)

```bash
cd primitive/v911
python3 <<'PYEOF'
import csv, glob
# 本 result.md と同じ数値が出るか検証
for pat, label in [
    ("diag_v911_capture_short/subjects/*.csv", "short_subjects"),
    ("diag_v911_capture_long/subjects/*.csv", "long_subjects"),
]:
    rows = [r for f in sorted(glob.glob(pat)) for r in csv.DictReader(open(f))]
    print(f"{label}: {len(rows)} rows")
    # B_Gen by n_core
    from collections import defaultdict
    bands = defaultdict(list)
    for r in rows:
        bg = r.get("v11_b_gen")
        nc = r.get("v11_m_c_n_core")
        if bg in ("unformed", "inf", "") or nc in ("unformed", ""): continue
        try: bands[int(nc)].append(float(bg))
        except: pass
    for nc in sorted(bands):
        vs = sorted(bands[nc])
        if len(vs) < 3: continue
        print(f"  n_core={nc}: n={len(vs)} median={vs[len(vs)//2]:.2f}")
PYEOF
```

検証が result.md §2 と一致すれば A 実装および集計は OK。
