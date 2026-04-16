<!-- ========================================================== -->
<!--  CODE A 編集指示                                           -->
<!-- ========================================================== -->
<!--                                                            -->
<!--  Target file: docs/ai_summaries/07_esde_system_structure.md  -->
<!--  Action: 1 箇所に挿入 (既存内容は 1 バイトも変更しない)    -->
<!--                                                            -->
<!--  挿入位置:                                                 -->
<!--    ファイル末尾の「## コード参照」テーブルの直前           -->
<!--    (区切り線 `---` の前、かつ「コード参照」見出しの前)     -->
<!--                                                            -->
<!--  Verification:                                             -->
<!--    - 既存の「コード参照」テーブルが末尾に残っていること    -->
<!--    - 既存のパラメータ一覧 (Physics / Virtual / Subject) が -->
<!--      変更されていないこと                                  -->
<!--                                                            -->
<!-- ========================================================== -->


<!-- >>>>> 挿入内容 (「## コード参照」の直前に配置) <<<<< -->

## v9.11 認知層拡張: Cognitive Capture

### Birth-time metrics (cid 単位、birth 時 1 回固定)

| 変数 | 意味 |
|---|---|
| B_Gen | -log10(Pbirth) = 構造階層指標 |
| M_c | (n_core, S_avg, r_core, phase_sig) = 記憶ベクトル |

### Pulse-time metrics (cid 単位、pulse ごと上書き)

| 変数 | 意味 |
|---|---|
| E_t | (n_local, s_avg_local, r_local, θ_avg_local) = 事象ベクトル |
| Δ | Σ w_i × \|M_c_i − E_t_i\| / norm_i (Weighted L1) |
| d_n, d_s, d_r, d_phase | Δ の軸別分解 (個別ログ) |
| p_capture | 0.9 × exp(-2.724 × Δ) |
| captured | "TRUE" / "FALSE" / "cold_start" (確率的判定) |

### パラメータ (v9.11 確定値)

| パラメータ | 値 | 備考 |
|---|---|---|
| V11_P_MAX | 0.9 | 最大捕捉確率 (<1 で「取りこぼし」表現) |
| V11_LAMBDA | 2.724 | Variant A 指数減衰 |
| V11_NORM_N | 86 | n_local の p95 ベース (v9.12 で過大と判明) |
| V11_NORM_S | 1.0 | 固定 (S ∈ [0,1]) |
| V11_NORM_R | 1.0 | 固定 (r ∈ [0,1]) |
| 重み (均等) | W_n = W_s = W_r = W_phase = 0.25 | 暫定均等 |
| COLD_START_PULSES | 3 | pulse 1-3 は capture 判定保留 |
| capture_rng | np.random.default_rng(seed ^ 0xC0FFEE) | engine.rng と分離 |

### Birth 条件 (v9.11 まで、v9.13 で変更予定)

```
find_islands_sets(state, s_thr=0.20)  # S≥0.20 連結成分 (size≥3)
R>0 リンク両端 (size=2)
50% overlap フィルタ
phase_sig = atan2(Σsin, Σcos)
birth 確定 (確率判定なし)
```

**v9.13 で変更**: S≥0.20 hard threshold 撤去、Pbirth ベースの確率的 birth に移行予定。

### v9.12 で確定した認知捕捉の性質

- Δ は i.i.d. (自己相関 ≈ 0) — 蓄積しない
- 軸寄与の偏在 (phase+r 72%) は NORM_N 圧縮 + S 定常性で説明可能
- d_r と d_phase は無相関 (r=0.008)
- L06 低 capture は n_core 構成効果 (時間効果ではない)
- n_core≥6 が出ないのは S≥0.20 接続性制約 + overlap フィルタによる構造的帰結

### 出力 CSV 列追加 (per_subject / pulse_log に末尾追加、v10_/v99_ 列保持)

per_subject 13 列:
`v11_b_gen, v11_m_c_n_core, v11_m_c_s_avg, v11_m_c_r_core, v11_m_c_phase_sig, v11_n_pulses_eval, v11_n_captured, v11_capture_rate, v11_mean_delta, v11_mean_d_n, v11_mean_d_s, v11_mean_d_r, v11_mean_d_phase`

pulse_log 12 列:
`v11_b_gen, v11_delta, v11_d_n, v11_d_s, v11_d_r, v11_d_phase, v11_p_capture, v11_captured, v11_n_local, v11_s_avg_local, v11_r_local, v11_theta_avg_local`

---
