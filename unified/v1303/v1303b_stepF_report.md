# v1303b Step B〜F — 同一CID内 3レンズの時間構造 観察事実報告（判定なし）

*作成*: 2026-06-27、Code A。
*位置づけ*: v1303b 主題設計（GPT 監査反映版）の Step B〜F。既存 ledger（seed0）の**後処理のみ**（再走なし・Step E 不要）で、同じ CID 内の3レンズが時間方向にどれだけ反復・安定・同時変動するかを観察A〜E + shuffle 2種で読んだ。**(a)/(b) 判定・主題評価はしない（#12）。** 「経験候補として読める時間構造の観察」までで「経験成立」とは言わない（GPT 条件6・出口を弱める）。判定は Web Claude / Taka。
*成果物*: `v1303b_observe.py` / `outputs/v1303b/v1303b_obs_ABC_seed0.parquet`（228 cid×指標+shuffle pctl）/ `_obs_D_ghost_seed0.parquet`（163 cid）/ `_obs_E_rpos_seed0.parquet`（140 cid）/ `v1303b_distributions.html`。
*前提突合*: Step A 認識確認（`v1303b_stepA_recognition.md`）で設計の4経験的主張を seed0 ledger と全突合・一致済。

---

## 0. 実行設定
- 対象 = hosted_available 行（観察D は hosted→ghost 遷移）。`min_points_per_cid=30` → **228 cid 全採用**。
- shuffle 2種：**within-cid time（主対照・200回・seed42）**＝時間順を joint 破壊し主指標 null を作る／**within-n_core cid-label（補助対照）**＝同 n_core peer 内 percentile（cid 間 edge を作らず）。
- ③主軸=node θ（`core_node_theta_resultant_length`）・link S/R は別枠（観察E）。3レンズ合成しない。

## 1. 観察A — rank_1_atom の再出現（主指標=時間構造／dominant・entropy=補助）
| n_core | cid | mean_run_length med | timeshuf_pctl med | pctl>0.95 の cid | dominant_frac med（補助） |
|---|---|---|---|---|---|
| 2 | 180 | 15.67 | 1.000 | 129 / 180 | 0.933 |
| 3 | 12 | 17.16 | 1.000 | 12 / 12 | 0.498 |
| 4 | 15 | 16.02 | 1.000 | 15 / 15 | 0.509 |
| 5 | 21 | 19.08 | 1.000 | 21 / 21 | 0.515 |
- **観測 run_length は within-cid time shuffle の上端**（pctl med=1.000）。n3/n4/n5 は **全 cid が pctl>0.95**、n2 は 129/180（72%）。
- **dominant_fraction は補助に留めた**（時間構造証拠にしない・GPT 条件1）。n2 は 1 atom が 93% 支配だが、これは語彙頻度であって run_length（連続の長さ）とは別物。

## 2. 観察B — θ の自己相関（短期 lag だけで反復と呼ばない・GPT 条件2）
| n_core | lag1 med | lag5 med | lag10 med | lag50 med | lag100 med |
|---|---|---|---|---|---|
| 2 | 0.766 | −0.000 | −0.026 | 0.029 | −0.041 |
| 3 | 0.595 | 0.053 | −0.004 | −0.040 | −0.010 |
| 4 | 0.658 | −0.023 | 0.013 | 0.003 | −0.016 |
| 5 | 0.590 | −0.052 | −0.001 | −0.002 | −0.010 |
- pctl>0.95 の cid 数：lag1 = n2:162/n3:11/n4:15/n5:21（多数）、**lag5 = n2:50/n3:5/n4:4/n5:5（激減）**、lag10 以降は更に少数。
- → θ は **lag1（隣接 step10）の慣性は shuffle に際立つが、lag5 以上の長い時間的戻りは大半の cid で shuffle 並み**。短期慣性を反復と取り違えない（設計の予言と一致）。

## 3. 観察C — 3レンズの同時変動（②atom × ③θ・乾いた操作定義・合成しない）
| n_core | θ_jump@atomchange med | θ_jump baseline med | timeshuf_pctl med | atom変化率 high_θ / low_θ |
|---|---|---|---|---|
| 2 | 0.1123 | 0.1140 | 0.028 | 0.053 / 0.042 |
| 3 | 0.1318 | 0.1544 | 0.000 | 0.050 / 0.052 |
| 4 | 0.1174 | 0.1260 | 0.000 | 0.052 / 0.053 |
| 5 | 0.1162 | 0.1264 | 0.000 | 0.049 / 0.045 |
- **atom が変わる瞬間の θ_jump は baseline と同等〜やや小さい**（pctl 下側）。atom 変化率も high_θ / low_θ でほぼ同じ。
- → **②（atom 再出現）と ③（θ）は step10 で同時に動いていない**（独立に振る舞う）という観察事実。①dynamic C/Q は window 粒度ゆえ step10 同時変動の主軸にせず（Step A §5・別表 parquet に window 粒度補助列）。

## 4. 観察D — ghost 化前 vs mid-life（usable cid=163・崩れるか否かを観察）
| 指標 | mid-life med | pre-ghost（末尾20%）med |
|---|---|---|
| mean_run_length（atom 安定） | 12.67 | **9.00** |
| θ_mean | 0.637 | 0.625 |
| C_mean | 0.00 | 0.00 |
| Q_mean | 11.00 | 11.00 |
- **ghost 化手前で atom の run_length が中盤の 12.67 → 9.00 に短く**（再出現の安定が低下）。θ_mean はほぼ不変、C/Q（window 粒度・中央値）は不変。
- → 「崩れるか」を当てにいかず観察した結果、**②（atom 安定）は ghost 前に低下し、③（θ 同期）は保たれる**という非対称（v1303a の「label は θ で生きる」と整合する向きだが、判定は Web Claude/Taka）。

## 5. 観察E — R_positive の稀な瞬間（補助・別枠・link を主軸に戻さない）
- R_positive を持つ cid = **140 / 228**、events med=7。
- atom 変化率 @R_positive = **0.235**（全体 ~0.05）／ θ_mean @R_positive = **0.889**（overall 0.641）。
- → internal link が共鳴する稀な瞬間は **θ がより同期し atom 変化も多い**（記録のみ・主軸でない）。

## 6. 言えること / 言えないこと（GPT 条件6・出口）
- **言える（観察事実）**: 同一 CID 内で、レンズ②（atom 再出現の run_length）は within-cid time shuffle に対し明確に際立つ（時間構造あり）。レンズ③（θ）は短期慣性のみで長 lag の戻りは shuffle 並み。②×③ の同時変動は step10 で観測されない（独立）。ghost 前に ② の安定が低下、③ は保たれる。R_positive 稀瞬間は θ 高同期＋atom 変化増。
- **言わない**: 「経験が成立した」「3レンズが束なる」「層が厚い」は **言わない**（GPT 条件6）。レンズごとに時間構造の有無が異なり、合成・単一スコア化しない（#11）。dominant_fraction を時間構造証拠にしない。Atom 名（PER.sound 等）を意味解釈しない（L型）。(a)/(b) 判定は委ねる。

## 7. 規律遵守
- #2/B型: 既存 ledger 後処理のみ（再走なし）。書込 `unified/v1303/outputs/v1303b/` のみ。cid-label shuffle は peer percentile の対照限定（edge 生成なし）。
- #3/C型: shuffle 2種で交絡を切る・予測を出口にしない・dominant_fraction を時間構造証拠にしない。
- #4/D型: 全 CID 平均の相関を出さず cid 個別/n_core 別。#11: 3レンズ合成しない・③主軸θ・link 別枠(観察E)。
- #12/J型: 判定せず観察事実のみ・観察を A〜E に絞る・seed0 のみ。L型: Atom 意味解釈しない。
- n_core=3 は 12 cid（最小ストラタム・小標本 caveat を表に明記）。

## 8. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（生データから run_length/autocorr/co-variation/shuffle pctl を再計算し本報告と照合）→ Web Claude Phase Result → Taka 主題評価。方針メモ §3 第三段階（注意センター：際立った cid を ESDE の B_Gen/珍しさが拾えるか）or 多シードで個性サンプル増、は Taka 選定領域。

---

## 9. 一文サマリ
v1303b（既存 seed0 ledger 後処理・再走なし・228 cid 全採用・shuffle within-cid time 200回 seed42 + within-n_core peer percentile）で同一 CID 内の3レンズ時間構造を cid個別・n_core別・合成せず読んだ結果、**観察A：rank_1_atom の mean_run_length は within-cid time shuffle の上端(pctl med=1.000・n3-5 全cid/n2 129/180 が pctl>0.95)＝atom 再出現に強い時間構造**（dominant_fraction は補助に留め時間構造証拠にせず・GPT 条件1）、**観察B：θ 自己相関は lag1 med 0.59-0.77 が際立つが lag5+ は shuffle 並み(pctl>0.95 が lag1 多数→lag5 激減)＝短期慣性のみで長lag 反復なし**（GPT 条件2）、**観察C：θ_jump@atomchange≈baseline・pctl下側＝②atom と ③θ は step10 で同時変動せず独立**（乾いた操作定義・合成しない）、**観察D：ghost 化前(末尾20%)で atom run_length 12.67→9.00 と安定低下・θ は保持(0.637→0.625)＝②崩れ③保たれの非対称**(usable cid=163)、**観察E(補助・別枠)：R_positive 稀瞬間は θ@0.889(overall0.641)高同期＋atom変化率0.235(全体~0.05)増**、出口は「レンズ②は時間構造あり/③は短期慣性のみ/②×③同時変動なし/ghost前に②安定低下」を経験候補として読める観察事実まで（経験成立とは言わない・束ね/層/合成しない・Atom 意味解釈しない）、判定は Web Claude/Taka、第三段階(注意センター)選定は Taka。
