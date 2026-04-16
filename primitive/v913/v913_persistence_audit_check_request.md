# v9.13 Step 0 Persistence Audit — Code B チェック依頼書

- Date: 2026-04-16
- From: Claude Code A
- To: Claude Code B
- 対象ファイル: `primitive/v913/v913_persistence_audit.py`
- ベース: `primitive/v911/v911_cognitive_capture.py`

---

## 1. 変更概要

v9.11 をベースに persistence tracking コード (~209 行) を追加。
既存ロジック変更なし (outdir 名のみ変更)。

追加内容:
- v9.13 docstring 追記
- `networkx` import 追加
- `_V911_DIR` パス追加
- `V913_SHADOW_THRESHOLDS`, `V913_SHADOW_MIN_SIZE` 定数追加
- `persistence/` サブディレクトリ作成
- `v913_*` 状態変数初期化 (run 関数内ローカル)
- Resonance 直後の age_r 更新 (§7)
- decay_exclusion 直後の alive_l 差分検出 (§6)
- window 末の link snapshot + shadow component 分析 (§9)
- label birth 時のメンバーリンク persistence 記録 (§8)
- run 末尾の 4 CSV 出力 (§10)

---

## 2. 不変量チェックリスト

- [ ] `cognition/v19g_canon.py` に 1 byte も変更なし
- [ ] `ecology/engine/esde_v82_engine.py` に 1 byte も変更なし
- [ ] `primitive/v910/virtual_layer_v9.py` に 1 byte も変更なし
- [ ] `primitive/v911/v911_cognitive_capture.py` に 1 byte も変更なし
- [ ] 物理層 7 オペレータの呼び出し順序が v9.11 と同一
- [ ] 背景注入 (BIAS + Z seeding) が v9.11 と同一
- [ ] engine.state.rng に追加分岐なし (age_r 更新は RNG 不使用)
- [ ] capture_rng (v9.11) に追加分岐なし
- [ ] **per_window CSV が v9.11 smoke と bit identical** (確認済み: diff exit 0)
- [ ] v99_ / v10_ / v11_ 列が既存 CSV に位置・値とも保存
- [ ] `engine.state` (theta/S/R/E/Z/alive_l) への書き込みが追加コードから一切ない
- [ ] `engine.virtual.labels` / `vl.phase_sig` / `vl.share` への書き込みが追加コードから一切ない
- [ ] `cog.*` (SubjectLayer 各 dict) への書き込みが追加コードから一切ない
- [ ] pickup 機構 (death_pool, cid_ttl_bonus) への書き込みが追加コードから一切ない
- [ ] リンク生死判定で alive_l 以外のフラグ・状態を参照しない
- [ ] shadow component 分析が read-only
- [ ] `V913_SHADOW_THRESHOLDS = [50, 100, 200, 300, 400, 500]`
- [ ] age_r 更新位置が Resonance 直後 / Auto-Growth 前
- [ ] 出力 4 CSV のスキーマが指示書 §10 通り

---

## 3. Smoke テスト結果

条件: `--seed 0 --maturation-windows 5 --tracking-windows 2 --window-steps 100 --tag smoke`

- [x] exit code 0
- [x] persistence/ に 3 CSV (shadow_component_log は閾値未達で空 = 正常)
- [x] link_life_log: 13,856 行
- [x] link_snapshot_log: 6,074 行
- [x] label_member_persistence: 3 行
- [x] age_r_current は整数 >= 0
- [x] max_age_r_so_far >= age_r_current が全行で成立 (violation 0)
- [x] per_window CSV bit identical (v9.11 smoke と diff exit 0)

---

## 4. Diff 規模

- 追加行: +209
- 削除行: -3 (outdir 名変更 1 行、docstring 差し替え 2 行)
- 既存ロジック変更: なし
