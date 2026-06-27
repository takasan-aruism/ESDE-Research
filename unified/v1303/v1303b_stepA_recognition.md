# v1303b Step A — 認識確認（実データ突合・実装前の確認）

*作成*: 2026-06-27、Code A。
*位置づけ*: v1303b 主題設計（GPT 監査反映版）§5.1 の Step A 認識確認。**設計の経験的主張を seed0 ledger（`unified/v1303/outputs/v1303_ledger_seed0.parquet`）で全突合**し、実装の現実とかけ離れていないことを確認した上で、観察A〜E の出力テーブル案・shuffle 仕様を確定する。判定はしない（#12）。
*対象データ*: 既存 ledger のみ（後処理・再走不要・Step E 不要）。

---

## 0. 設計主張の実データ突合（全一致）
| 設計の主張 | 実データ（seed0 ledger） | 一致 |
|---|---|---|
| min_points=45・全228体≥30・閾値50で131体 | hosted行/cid: min=45 med=98 max=2500 / ≥30=**228体** / ≥50=131体 | ✓ |
| ghost 遷移 163体/228（行数863でなく） | hosted→ghost を両方持つ cid=**163** / reaped行持つ=28 | ✓ |
| cid=0 θ autocorr lag1=0.48→lag5=0.02（慣性のみ） | lag1=0.4795 / lag5=0.0242 / lag10=−0.037 / lag50=0.044 / lag100=0.037 | ✓ |
| cid=0 dominant 0.575不変・mean_run_length 19.08→1.67崩壊 | dominant 0.575→0.575 / run 19.08→1.67 / switch 130→1497（within-cid time shuffle） | ✓ |

→ **設計はこの seed0 ledger に対して書かれており、実装の現実と乖離なし。**

## 1. ledger 列と欠損率（§5.1）
- 40列（v1303a 報告 §2）。観察に使う主列の欠損：①static `v11_b_gen` notna=1.0 / ②`rank_1_atom`・`rank_1_sim` notna=1.0 / ③`core_node_theta_resultant_length` は hosted_available 行で有効（98.58%）。
- ①dynamic `C_at_window_end` nonzero=80.3% / `Q_remaining_at_window_end` notna=1.0。
- disposition は全行 `no_per_t_source`（観察対象外）。

## 2. 観察対象の範囲（§5.1）
- **観察A〜C・E = hosted_available 行のみ**（62,015行）。
- **観察D = ghost/reaped 遷移**を持つ cid（hosted→ghost の前後）。`ghost_transition_cid_count=163`・`reaped_cid_count=28`。
- **有効系列処理条件**：`min_points_per_cid=30`（判定軸でない）→ 228体全採用。

## 3. n_core 別 cid数/row数（hosted・§5.1）
| n_core | cids | rows |
|---|---|---|
| 2 | **180** | 19,733 |
| 3 | **12** | 3,414 |
| 4 | 15 | 12,014 |
| 5 | 21 | 26,854 |
> **注意（実装で明記）**: n_core=3 は 12体と最小ストラタム。cid 個別観察は可だが n3 の層集計は小標本（caveat）。n2 が 180体で支配的。

## 4. レンズ別 観察可能性（§5.1）
- **rank_1_atom の cid内 unique数**: min=1 / med=2 / max=14 / unique==1の cid=6体。→ 再出現パターンを読む素地あり（大半が 2〜数個の atom を行き来）。
- **atom 変化率（cid内・隣接step10）**: med=0.050 / 範囲[0,0.149]。→ atom は window 内でも変化（観察A 有効）。
- **θ resultant の cid内 std**: med=0.298 / std<0.01（ほぼ不動）の cid=**0体**。→ θ は全 cid で動く（観察B 有効）。autocorr は複数 lag で計算可能（検証5）。

## 5. 【実装で考慮する データ特性】①dynamic C/Q の時間粒度
- **C/Q は window(500step)粒度で更新**。step10 刻みの隣接差分 `C_delta!=0` は **1.0%**・`Q_delta!=0` は 1.4%（cid=0）。
- → 観察C で `C_delta around atom_changed` を step10 で取ると大半 0。**C/Q の同時変動は window 境界でしか動かないため、観察C の C/Q ペアは window 粒度で扱う**（θ/atom は step10、C/Q は window）。これを混同して「C は atom と同時に動かない」と誤読しない（粒度由来）。観察C 主軸は θ_jump×atom_changed（同 step10 粒度）、C/Q は補助・window 粒度注記つき。

## 6. shuffle 仕様（§5.1・§2.6 確定）
- **主対照 within-cid time shuffle**: 各 cid の値系列の時間順のみ破壊（値分布保存）。観察A(run/return)・B(autocorr)・C(同時変動) の対照。
- **補助対照 within-n_core cid-label shuffle**: n_core を保ち CID ラベル入替。CID 固有性の対照（対照限定・関係生成にしない＝B型回避）。
- **乱数 seed 固定 = 42**（再現性）。**shuffle 回数 = 200**（各 cid・各指標で shuffle 分布を作り、観測値の percentile/z を出す。計算は分オーダ）。

## 7. 観察A〜E 出力テーブル案（合成しない・cid個別/n_core別・§2）
| 観察 | 出力テーブル（1行=1 cid、主指標 + shuffle percentile/z） |
|---|---|
| **A rank_1 再出現** | `cid, n_core, n_points, mean_run_length, max_run_length, switch_per_1000, return_interval_same_atom_med`（主） + `dominant_atom_fraction, atom_entropy`（補助・時間構造証拠にしない） + 各主指標の `*_shuffle_pctl`（within-cid time） |
| **B θ 自己相関** | `cid, n_core, theta_std, autocorr_lag1/5/10/50/100` + 各 lag の `*_shuffle_pctl`（短期 lag だけで反復と呼ばない） |
| **C 同時変動** | `cid, n_core, theta_jump_at_atomchange_med, theta_jump_baseline_med, atom_change_rate_high_theta, atom_change_rate_low_theta`（step10）+ `C_delta_at_atomchange, Q_delta_at_atomchange`（window 粒度注記）+ `*_shuffle_pctl` |
| **D ghost 前崩れ** | `cid, n_core, host_lost_step, pre_ghost_window_count, run_length_pre_ghost vs run_length_mid_life, theta_resultant_pre_ghost vs mid, C/Q_pre_ghost vs mid` + `usable_ghost_cases=163` を集計に明記 |
| **E R_positive 稀瞬間（補助・別枠）** | `cid, n_rpos_events, theta/atom/C around R_positive`（記録のみ・主軸でない・link を主軸に戻さない） |

## 8. 規律（本 Step）
- #2/B型: 既存 ledger 後処理のみ・再走なし・書込は `unified/v1303/` のみ。cid-label shuffle は対照限定。
- #3/C型: shuffle 2種で交絡を切る・予測を出口にしない・dominant_fraction を時間構造証拠にしない（実証済）。
- #4/D型: 全 CID 平均を出さない・cid個別/n_core別。 #11: 3レンズ合成しない・③主軸 θ・link 別枠。
- #12/J型: 判定せず観察事実のみ・観察を A〜E に絞る・seed0 のみ。L型: Atom 意味解釈しない（再出現パターン）。

## 9. 一文サマリ
v1303b Step A 認識確認（Code A, 2026-06-27）── 設計の4経験的主張（min_points45/全228体≥30・ghost遷移163体・cid=0 θautocorr lag1 0.48→lag5 0.02・dominant 0.575不変だが run_length 19.08→1.67崩壊）を seed0 ledger で**全突合・完全一致**し設計が実装現実と乖離ないことを確認、観察対象=hosted_available(62,015行)＋観察D は ghost遷移163体、n_core別 cid数 n2=180/n3=12(最小・caveat)/n4=15/n5=21、rank_1_atom cid内 unique med2・atom変化率 med0.05・θ std med0.298(全cid動く)で A/B/C 有効、**①dynamic C/Q は window粒度(step10刻みで99%不変)ゆえ観察C は θ_jump×atom_changed を step10主軸・C/Q は window粒度補助**と明記、shuffle=within-cid time(主)/within-n_core cid-label(補助)・seed42・200回、観察A〜E の出力テーブル案を合成せず cid個別/n_core別で確定、後処理のみ(再走/Step E不要)、判定は Web Claude/Taka。
