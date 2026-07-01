# v1303j Step B 観察事実報告（distribution audit・seed0・read-only・判定なし #12）

*作成*: 2026-07-01、Code A。**事実のみ・success/fail を置かない。正式採用 eye / persist 命名 / peer 採否 / bgen 読み は Taka 領域。**

## 0. insight の実装 + instrument の正直な訂正
- 選択確率 p[eye,cid,t]=clip(sal,0)/Σ_eligible を厳密算出（RNG 不要）。freq[eye,cid]=mean_t p（Σ_cid=1）。
- 単発 chance 支配（Step A の弱点）は厳密値ゆえ消える。many-RNG は sampler 検証と分散図示のみ。
- **⚠ Code A の正直な訂正**: 設計 §3.3 が「本体」とした **marginal（時間平均 freq）分布相関は D 型（平均化）の罠を含む**。
  freq=mean_t p は各 cid の露出時間（何ステップ pool に居たか）に支配され salience 形状が洗い流されるため、
  θ/link/peer が **全て uniform と ~0.99**（下表）になり distinct 性も珍しさ選択も測れない。**本体は per-t（§2b/§2c）に移す**。

## 1. concentration / entropy（marginal・exact・各 eye）
```
             eye                                                       label  entropy  effective_cid_count  inv_sumsq  top1_cum  top5_cum  top10_cum  nonzero_cid
       now_theta                           瞬間θ(f raw theta_resultant_length)   4.6266                102.2       58.5    0.0386    0.1839     0.3477          228
persist_thetapct                                 持続θ(e theta_cid_percentile)   4.3125                 74.6       40.8    0.0483    0.2333     0.4331          228
     link_rarity               link稀さ非θ(i rarity_internal_link_within_ncore)   4.4472                 85.4       46.5    0.0433    0.2157     0.4024          228
        bgen_pct                      静的B_Gen(h bgen_pct_in_ncore・per-cid定数)   2.8009                 16.5       11.0    0.1928    0.5705     0.7924           45
      peer_theta peer-rel θ(i rarity_theta_within_ncore・prove-by-trajectory)   4.4432                 85.0       46.5    0.0426    0.2105     0.4043          228
         uniform                                            uniform baseline   4.7167                111.8       61.5    0.0363    0.1815     0.3410          228
```
- bgen は per-cid 定数ゆえ低 entropy / 少 effective count＝背景静的優先度（degenerate は性質・「失敗」と書かない）。
- 注: この marginal concentration も露出時間の影響を受ける（θ/link/peer の eff+count が uniform 111.8 に近い）。

## 2a. marginal eye 間分布相関（⚠ 参考のみ・D 型で潰れる）
```
eye               now_theta  persist_thetapct  link_rarity  bgen_pct  peer_theta  uniform
eye                                                                                      
now_theta            1.0000            0.9890       0.9927    0.6965      0.9947   0.9935
persist_thetapct     0.9890            1.0000       0.9991    0.7316      0.9971   0.9981
link_rarity          0.9927            0.9991       1.0000    0.7244      0.9981   0.9994
bgen_pct             0.6965            0.7316       0.7244    1.0000      0.7100   0.7249
peer_theta           0.9947            0.9971       0.9981    0.7100      1.0000   0.9977
uniform              0.9935            0.9981       0.9994    0.7249      0.9977   1.0000
```
- 全ペア~0.99・now×uniform 0.99＝露出時間支配で salience が消えた状態。**distinct 判定に使わない**。

## 2b. per-t eye 間分布相関（本体・distinct 性・単発一致率でない）
```
                        pair  mean_per_t_corr
  now_theta×persist_thetapct           0.4260
       now_theta×link_rarity           0.4761
          now_theta×bgen_pct          -0.0490
        now_theta×peer_theta           0.5548
persist_thetapct×link_rarity           0.7743
   persist_thetapct×bgen_pct           0.3022
 persist_thetapct×peer_theta           0.5665
        link_rarity×bgen_pct           0.2211
      link_rarity×peer_theta           0.4917
         bgen_pct×peer_theta           0.0878
```
- per-t では 1 未満に割れる＝目は per-t で distinct（marginal で消えていたもの）。読み（採否）は Taka。

## 2c. per-t 珍しさ選択（本体・C 型・uniform からの乖離）
```
             eye                                                       label  mean_per_t_KL_from_uniform  mean_per_t_effective_count
       now_theta                           瞬間θ(f raw theta_resultant_length)                      0.3133                       21.50
persist_thetapct                                 持続θ(e theta_cid_percentile)                      0.2087                       24.00
     link_rarity               link稀さ非θ(i rarity_internal_link_within_ncore)                      0.1763                       24.65
        bgen_pct                      静的B_Gen(h bgen_pct_in_ncore・per-cid定数)                      1.0249                       11.90
      peer_theta peer-rel θ(i rarity_theta_within_ncore・prove-by-trajectory)                      0.3609                       20.53
         uniform                                            uniform baseline                      0.0000                       29.33
```
- mean_per_t_KL_from_uniform: 0=uniform と同じ（珍しさが選んでいない）・大=per-t で集中選択。
- effective_count が uniform 基準より小さいほど per-t で珍しさが選択を絞っている。読みは Taka。

## 3. persist_thetapct は duration lens か（pulled vs eligible segment_length）
```
 n_rows  pulled_weighted_mean_seglen  eligible_mean_seglen  pulled_over_eligible  eligible_median_seglen  eligible_max_seglen  corr_pullprob_seglen
  61044                        5.553                 5.814                 0.955                     4.0                 49.0               -0.1423
```
- segment_length を salience に入れていないのに `pulled_over_eligible`>1 かつ `corr_pullprob_seglen`>0 なら長 segment 過剰選択＝duration lens 寄り、
  ≈1 / ≈0 なら短 segment 母集団多数＝『Archive 内 θ-percentile lens』寄り。命名は Taka（名前を間違えなければ問題ない）。

## 4. many-RNG 確認（sampler 検証 + 単発分散・N=200）
```
             eye  corr_emp_exact  max_abs_diff  mean_distinct_in_Ndraw
       now_theta         0.99991       0.00046                   23.94
persist_thetapct         0.99996       0.00059                   24.33
     link_rarity         0.99996       0.00056                   24.75
        bgen_pct         0.99999       0.00070                   14.28
      peer_theta         0.99994       0.00052                   23.20
         uniform         0.99993       0.00037                   29.23
```
- corr_emp_exact ≈ 1.0 かつ max_abs_diff 小 ＝ roulette sampler は exact 分布に収束（バグなし）。
- mean_distinct_in_Ndraw ＝ 200 draw が何種類の cid に散るか（単発を唯一の注意と読まない定量・§10-4）。

## 5. 選択分布の層化（n_core 別・bgen 高低別）
- now_theta: n_core別 {'n2': 0.383, 'n3': 0.065, 'n4': 0.173, 'n5': 0.379} / bgen高低別 {'high': 0.255, 'low': 0.218, 'no_bgen': 0.527}
- peer_theta: n_core別 {'n2': 0.302, 'n3': 0.061, 'n4': 0.19, 'n5': 0.448} / bgen高低別 {'high': 0.287, 'low': 0.249, 'no_bgen': 0.464}
- link_rarity: n_core別 {'n2': 0.3, 'n3': 0.061, 'n4': 0.189, 'n5': 0.45} / bgen高低別 {'high': 0.291, 'low': 0.252, 'no_bgen': 0.458}
- persist_thetapct: n_core別 {'n2': 0.256, 'n3': 0.061, 'n4': 0.2, 'n5': 0.483} / bgen高低別 {'high': 0.311, 'low': 0.265, 'no_bgen': 0.424}
- bgen_pct: n_core別 {'n2': 0.038, 'n3': 0.003, 'n4': 0.29, 'n5': 0.669} / bgen高低別 {'high': 0.822, 'low': 0.178, 'no_bgen': 0.0}

## 6. 言える / 言えない
- **言える**: 目ごとの選択分布・eye 間分布相関・concentration・persist の segment_length 比較を厳密に出した（read-only・seed0）。
- **言えない**: 「ESDE が注意した / 自律選択した / どの eye が正しい」。正式 eye 採否・persist 命名・peer 採否は Taka。
- 出口＝正式 eye 選定材料 → Taka 決定 → v1303 Final で attention output schema 固定 → v1303 クローズ。投影/子ESDE/Atom は v1304+ stub。

## 7. 次段
- smoke seed0 まで。main・複数 seed には進まない。Taka の正式 eye 決定後に v1303 Final。