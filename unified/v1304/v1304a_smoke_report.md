# v1304a feasibility + 最小 smoke 報告 — shape-forming の実機確認（停止・full run 進行しない）

*作成*: 2026-07-01、Code A。**feasibility + 最小 smoke で停止（§8-7 指示）。full existence check へ自動進行しない・成立判定でない・判定なし #12。** read-only・親へ feedback なし・物理非書込（書込 `unified/v1304/` のみ）。
*対象設計*: v1304a rev（shape-forming 確定・Stage 1B 本命・重み付け B 不採用）。
*成果物*: `unified/v1304/v1304a_smoke.py` + `outputs/v1304a_smoke_*`（signatures/coverage/tmid_means/summary）。

---

## 0. 結論（先に）
- **shape-forming Stage 1B は実装でき・engine は健全に自走**（96 child runs・89s・全群 alive_ratio 1.0・崩壊なし）。写像の機構は動く。
- ただし smoke が **2つの重要事実**を出した。いずれも full run 前に Taka/Web Claude 判断が要る：
  - **(I) coverage 制約が想定より重い**：親 attention mass のうち θ角度源 phase_sig(45cid) に載る割合は **now_theta 16% / archive 22% / link 19%**（bgen 100%）＝**dense な attention の 78–84% が θ shape に写せない**。
  - **(II) 初期θのみでは t_mid で構造乖離が立たない（first-look）**：全群で link_density/R_density が同一、sync_order/n_labels も parent>null の順序なし＝**Stage 1（初期θのみ）は washout ＝設計の出口 b' の兆候**（Stage 2 knob 要の可能性）。ただし smoke・K=6・first-look。

## 1. 実装した写像（shape-forming Stage 1B・重み付け B 不採用）
- 親 profile[eye,cid] = `mean_t p_select_given_eye_t`（v1303 final schema から eye 別 marginal）。
- **子ノード初期θのサンプル**：phase_sig を持つ 45 cid に profile を絞り重み w 化 → `cid ~ w` を N=150 回引き `θ = vonMises(phase_sig[cid], κ=4)`（**多峰保持＝circular mean で潰さない #11**）。構造 knob（N/plb/k_sync）は canonical 固定（群間同一・差は初期θ shape のみ）。seed 後は完全自走（runtime 注入なし）・run_injection 呼出（空 start 交絡回避）。
- 群（写像で自動決定）：canon（shaping なし=engine 既定θ）/ parent（w）/ shuffle（w を cid 間 permute）/ uniform（45cid 一様）。other-parent は full run で（smoke は 4 群）。

## 2. 発見(I) — coverage 制約（θ角度源の疎性・要判断）
| eye | attention mass on phase_sig 45cid | off（写せない質量） |
|---|---|---|
| now_theta | **0.159** | 0.841 |
| archive_theta_percentile | 0.215 | 0.785 |
| link_rarity | 0.194 | 0.806 |
| bgen_static_prior | 1.000 | 0.000 |

- **原因**：attention は 228 cid 上で dense だが、shape-forming の**θ角度源 phase_sig は 45/228 で疎**（birth 物理 knob 源は phase_sig/s_avg/r_core/b_gen とも同じ 45 cid）。bgen だけ 100% なのは bgen と phase_sig が同じ 45 cid を土台にするため。
- **含意**：Stage 1B は親 profile の **16–22% しか θ shape に反映できない**（bgen 除く）。設計 §2.2 の「denser な θ(theta_resultant ~85%)を土台に shape を attention から決める」は、theta_resultant が**角度でなく resultant length（0–1 の大きさ）**ゆえ子初期θ（角度）の直接源にできない — **per-cid の θ角度で dense なものが現状ない**のが制約の核。
- **要判断（Taka/Web Claude）**：(a) 45cid 支持に絞り coverage を明記して進む（現状・親の 5 分の 1 だけ写す）/ (b) dense な per-cid θ角度源を別途用意（例：canonical run の基準 t での per-cid θ snapshot）/ (c) Stage 2（構造 knob）も同 45cid 源ゆえ coverage は改善しない点を織り込む。

## 3. 発見(II) — first-look（初期θのみは t_mid で washout・出口 b' 兆候）
health：全 eye×群で min alive_ratio 1.0（崩壊なし＝構造を持った乖離の土俵は成立）。
t_mid 署名平均（判定でなく素の記述）：

| 量 | canon | parent | shuffle | uniform |
|---|---|---|---|---|
| link_density | 0.758 | 0.758 | 0.758 | 0.758 |
| R_density | 0.161 | 0.161 | 0.161 | 0.161 |
| sync_order | 0.108 | 0.11–0.13 | 0.10–0.14 | 0.11–0.13 |
| n_labels | 18.0 | 17.6–18.3 | 17.3–19.2 | 17.3–18.4 |

- **link_density / R_density は全群完全同一**、sync_order/n_labels は parent が canon/null を明確に超えず noise 内。⇒ **初期θのみの shaping は Kuramoto 下で t_mid までに washout し構造差を残さない**。
- これは v1302 の「継承は初期条件経由では成立しない・持続 param 経由のみ」と整合し、設計が予期した **出口 b'（初期状態だけでは不足→Stage 2 で knob も形づくる要）** の兆候。
- **留保**：smoke（K=6 seed・N=150・300step・4群・4eye）の first-look であり、full existence check（3条件の分布距離・per-t 乖離推移・n_core 層化・親方向を構造量別に・other-parent null）ではない。washout 確定は full run 後。

## 4. §8 各項目の回答
| # | 項目 | 結果 |
|---|---|---|
| 1 | child engine in-memory | **可**（96 runs 89s・健全自走） |
| 2 | 1A/1B の実現性 | **1B 実装済・採用**（多峰保持）。1A（circular mean 単峰）は #11 リスクゆえ不使用 |
| 3 | eye 別 profile → phase shape・45cid 疎性 | **可だが coverage 16–22%**（§2・要判断） |
| 4 | 最小4群 smoke（canon/parent/shuffle/uniform） | **可**（other-parent は full run で） |
| 5 | t0/t_short/t_mid/t_late 構造分布 | **可**（signature 7量を window 毎・子側 eye entropy 再読は full run で追加予定） |
| 6 | 「親方向」を構造量別に | full run で実装（parent_profile_structure/child/canon/null を量別・合成しない）。smoke は素の署名平均まで |
| 7 | 報告で停止 | **停止**（full へ自動進行しない） |

## 5. 停止位置と次段（判定は Taka/Web Claude）
本 smoke は「機構は動く・但し coverage 制約と初期θ washout 兆候」を出したところで**停止**。full existence check に進む前に、少なくとも次を合意したい：
1. **coverage 制約(I) の扱い**：45cid 支持に絞る / dense θ角度源を用意 / Stage 2 前提に切替。
2. **Stage 1 washout(II)** を full run（K 増・per-t 乖離距離・n_core 層化）で確認し、b' なら **Stage 2（構造 knob も shape-forming）** に進むか。
3. 3出口 (a)(b)(c) の判定・receiver 候補化は Taka。

read-only・親へ feedback なし・物理非書込・書込 `unified/v1304/` 配下のみを維持。成立判定は置かない（#12）。

## 6. 一文サマリ
v1304a feasibility+最小smoke（shape-forming Stage 1B・read-only・停止・判定なし#12）── 親 attention profile から子ノード初期θを phase_sig 分布(p_select重み)でサンプルする shape-forming は**実装でき engine は健全自走**（96runs/89s/全群 alive1.0）だが、smoke が2つの要判断事実を出した＝**(I) coverage：dense な attention の 78–84% は θ角度源 phase_sig(45/228疎) に写せず親 profile の 16–22% しか shape 化できない**（bgen のみ100%・denser な per-cid θ角度源が現状ない）、**(II) first-look：初期θのみは t_mid で washout（link/R density 全群同一・sync/n_labels は parent>null の順序なし）＝設計の出口 b'(初期状態だけでは不足→Stage2 knob 要)の兆候**（ただし smoke・K6・full でない）、§8 は 1B 採用/4群 smoke 可/t区分署名可を確認し**報告で停止**（full 自動進行しない）、次段は coverage制約(I)の扱い（45cid絞る/dense θ源用意/Stage2前提）と washout(II) の full 確認→b'なら Stage2、を Taka/Web Claude 合意後、3出口判定は Taka。
