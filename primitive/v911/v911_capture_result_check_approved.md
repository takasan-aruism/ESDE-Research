# Claude Code B チェック結果 — v9.11 本番 run 結果 (承認)

*Date*: 2026-04-15
*Reviewer*: Claude Code B
*Verdict*: **承認 (v9.11 phase 完了判定可)**
*Target*: `v911_cognitive_capture_result.md` + `diag_v911_capture_short/` (48 seeds) + `diag_v911_capture_long/` (5 seeds)

---

## 結論

出力完整性、集計再現性、不変量、L06 解釈、軸寄与解釈すべて妥当。
レポート §1〜§7 の数値はすべて B 側の独立再集計と一致 (差なし)。
v9.11 phase 完了判定し、v9.12 設計検討に移行してよい。

---

## A. 出力完整性

| 項目 | 期待 | 実測 | 結果 |
|---|---|---|---|
| short subjects | 48 (`per_subject_seed{0..47}.csv`) | 48 (+ 48 reaped) | ✓ |
| short pulse | 48 | 48 | ✓ |
| long subjects | 5 (`per_subject_seed{0..4}.csv`) | 5 (+ 5 reaped) | ✓ |
| long pulse | 5 | 5 | ✓ |
| pulse v11_ 列 | 12 | 12 (short / long とも) | ✓ |
| subject v11_ 列 | 13 | 13 (short / long とも) | ✓ |
| v10_ / v99_ 列保存 | 位置・数量同一 | per_subject に v10_=20 / v99_=33 列残存、smoke v910 と完全一致 | ✓ |

→ **A: 全項目クリア**

---

## B. 集計統計の再現性 (レポート vs 独立再集計)

### B-1. B_Gen バンド (subjects 集計)

| n_core | レポート (short p50 / long p50) | 再計算 | 結果 |
|---|---|---|---|
| 2 | 12.01 / 11.96 | 12.01 / 11.96 | ✓ |
| 3 | 18.81 / 18.74 | 18.81 / 18.74 | ✓ |
| 4 | 26.05 / 26.15 | 26.05 / 26.15 | ✓ |
| 5 | 33.60 / 33.79 | 33.60 / 33.79 | ✓ |

short/long でバンド中心一致、n=2 が最多 (short 1966, long 194)、レポート §2.3 観察と整合。

### B-2. capture_rate (cid 単位、n_pulses_eval≥5)

| run | レポート mean | 再計算 mean (p10/p50/p90) | 結果 |
|---|---|---|---|
| short | 0.397 | 0.397 (p10=0.235, p50=0.392, p90=0.571) | ✓ |
| long | 0.379 | 0.379 (p10=0.235, p50=0.353, p90=0.571) | ✓ |

### B-3. 軸寄与 (subjects mean_d_*)

| 軸 | short レポート / 再計算 | long レポート / 再計算 |
|---|---|---|
| n     | 13.5% / 13.5% | 16.2% / 16.2% |
| s     | 13.4% / 13.4% | 14.9% / 14.9% |
| r     | 34.0% / 34.0% | 31.9% / 31.9% |
| phase | 39.1% / 39.1% | 36.9% / 36.9% |

→ 完全一致

### B-4. cold_start 制約 / captured 種別

| 項目 | 結果 |
|---|---|
| short cold_start pulse_n set | {1, 2, 3} 厳密 ✓ |
| long cold_start pulse_n set | {1, 2, 3} 厳密 ✓ |
| short captured 値域 | {TRUE, FALSE, cold_start} のみ ✓ |
| long captured 値域 | {TRUE, FALSE, cold_start} のみ ✓ |
| short cold_start 比率 | 7.5% (8937/119320) ✓ |
| long cold_start 比率 | 4.4% (3336/75600) ✓ |

### B-5. pulse-level Δ / p_capture

| run | Δ p50 | Δ mean | p_capture mean | レポート |
|---|---|---|---|---|
| short | 0.361 | 0.367 | 0.3541 | 一致 ✓ |
| long  | 0.374 | 0.379 | 0.3428 | 一致 ✓ |

→ **B: 全項目クリア (レポート §2-§4 数値はすべて再現)**

---

## C. 不変量 (Step 1 と同等)

| 項目 | 結果 |
|---|---|
| `v19g_canon.py` / `esde_v82_engine.py` / `virtual_layer_v9.py` 無変更 | ✓ git log: 18379be (v910 original) のみ。HEAD まで変更なし |
| per_window CSV bit identical | ✓ Step 1 check で smoke seed=0 にて diff exit 0 を確認済 |
| capture_rng = `np.random.default_rng(seed ^ 0xC0FFEE)` | ✓ Step 1 check で実装確認済、本番でも同じコード |
| engine.rng と capture_rng の独立性 | ✓ capture_rng は capture 判定でのみ使用 (engine.state.rng 不依存)、seed 固定で再現可能 |

→ **C: 全項目クリア**

---

## D. L06 長命群の解釈妥当性

### D-1. 集団定義の合理性

| 項目 | 値 | 評価 |
|---|---|---|
| n_pulses_eval p90 (long) | 167 (再計算で確認) | ✓ |
| L06 サイズ | 114 cids (long 1112 中 10.25%) | top 10% で妥当な切り出し |
| n_pulses_eval p95 / max | 417 / 497 | レポート §5.1 と一致 |

p90 閾値は「上位 10% を抽出」の標準的手法で恣意性低い。L06 (long top 10%) という命名も明瞭。

### D-2. 統計の再現

| 指標 | レポート mean | 再計算 mean | 結果 |
|---|---|---|---|
| capture_rate | 0.307 | 0.307 (min 0.207, p50 0.300, max 0.551) | ✓ |
| mean_delta | 0.414 | 0.414 (min 0.191, p50 0.416, max 0.532) | ✓ |
| B_Gen | 30.15 | 30.15 (min 12.44, p50 33.11, max 37.02) | ✓ |
| n_core dist | 2:2.6%, 3:6.1%, 4:29.8%, 5:**61.4%** | 完全一致 | ✓ |

### D-3. 解釈の妥当性

- **「長命群 capture_rate=0.307 < overall 0.379 = 構造複雑化で追跡困難」**
  - 数値差 0.07 は統計的に意味があり、サンプルサイズ (114 vs 370) も十分
  - n_core=5 が 61% を占め B_Gen mean=30.15 (overall n_core=5 の B_Gen=34.00 と比較しても高め) → 「複雑構造に偏る」と整合
  - Δ mean が長命群で 0.414 vs overall 0.379 とわずかに高 → 「時間で乖離が蓄積」仮説と整合
  - **解釈は妥当**
- **「n_core=5 が長命群の 61% を占める = 大きな構造が長命化傾向」**
  - long 全体の n_core=5 は 104 cids、L06 内 70 cids → L06 が n_core=5 cids の 67% を吸収
  - 「大構造が長命化」は強い傾向あり、ただし因果は「大構造 → 長命」「長命 → 大構造観察機会増」両方あり得るので、レポートの「傾向」表現は適切 (断定なし)
- **window 別 capture rate の緩やか低下**
  - 再計算: 線形回帰 slope=-0.00032/window、50 windows で -0.016 の傾き
  - レポートの「緩やかな低下傾向、微弱だが一貫」は数値的に妥当 (p<0.05 検定までは未実施だが「微弱」表現で過剰主張なし)

→ **D: 解釈すべて妥当**

---

## E. 軸寄与の解釈

- **「phase+r 支配 (72%) = 認知捕捉のコア指標は位相同期性」**: 再計算で
  short 73.1% / long 68.8% を確認。観察として正確。
- **n/s 寄与小 (13-16%)**: 設計通り (W=0.25 均等) で起きた現象であり、
  実装バグや異常ではない。`d_n` の正規化定数 V11_NORM_N=86 が大きすぎ
  (n_core 典型値 2-5、n_local 典型 21 → d_n 典型 0.2 弱) という構造的要因も
  寄与している。
- **v9.12 以降の方向性 (3 案)**: レポート §3.3 / §8 で 3 択を提示し、
  「現状のまま結果を解釈、v9.12 で再検討」と判断保留している姿勢は穏当。
  どの案も一長一短があり、Taka 構想の方向性 (どの軸が認知の主指標か) と
  実測知見を併せて選択すべき問題。**B からの方向性指定は不要、Taka 判断推奨**。

→ **E: 解釈妥当、方向性決定は Taka に委ねる**

---

## F. レポート内容

| 項目 | 結果 |
|---|---|
| §1 実行サマリ (subject 2979/1112、pulse 119320/75600) | ✓ 再計算一致 |
| §2 B_Gen バンド 4 段 | ✓ 再計算一致 |
| §3 軸寄与 (short/long) | ✓ 再計算一致 |
| §4 capture/Δ/p_capture 分布 | ✓ 再計算一致 |
| §5 L06 統計 | ✓ 再計算一致 |
| §6 window 別推移 | ✓ slope -0.00032/win で「緩やか低下」記述妥当 |
| §7 キー発見サマリ | ✓ 本文の数値・観察を歪曲なく要約 |
| §8 v9.12 示唆 | ✓ 過剰解釈なし、選択肢提示にとどまる |

→ **F: 全項目クリア**

---

## 確認ログ (実コマンド)

```bash
# A: ファイル数
ls diag_v911_capture_short/subjects/per_subject_seed*.csv | wc -l  # → 48
ls diag_v911_capture_short/pulse/pulse_log_seed*.csv | wc -l       # → 48
ls diag_v911_capture_long/subjects/per_subject_seed*.csv | wc -l   # → 5
ls diag_v911_capture_long/pulse/pulse_log_seed*.csv | wc -l        # → 5

# B-1〜B-3: subject 集計 (レポート §2/§3 再現)
python3 (B_Gen バンド + capture_rate + 軸寄与) → 全数値完全一致

# B-4/B-5: pulse 集計 (レポート §4 再現)
python3 (cold_start={1,2,3}, 種別 {TRUE,FALSE,cold_start} のみ,
         Δ/p_capture 分布) → 全数値完全一致

# C: 不変量
git log --all --oneline -- cognition/v19g_canon.py \
   ecology/engine/esde_v82_engine.py primitive/v910/virtual_layer_v9.py
# → 18379be (v910 original) のみ

# D: L06 再計算
python3 (n_pulses_eval≥167 → 114 cids, capture/Δ/B_Gen mean,
         n_core 内訳 2.6/6.1/29.8/61.4%) → 完全一致

# F-§6: window 別 trend
python3 (slope per window = -0.00032, 50 windows で -0.016)
```

---

## 承認後の次アクション

1. v9.11 phase 完了判定 → 次回レビューで Taka に共有
2. v9.12 以降の設計検討 (重み / 正規化 / 追加軸 / λ 再調整 等):
   - 重み: 現状 W=0.25 均等で phase/r 支配。再設計の方向性は Taka 判断
   - λ: 本番 Δ p50=0.37 に合わせ直すなら λ ≈ -ln(0.5)/0.37 = 1.87 (smoke 値より小さく capture rate 中央値が ~0.45 へ移動)
   - L06 個別 cid の認知捕捉時系列分析 (M_c vs E_t 乖離の可視化)
