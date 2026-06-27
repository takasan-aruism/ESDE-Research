# v1303 Step B〜F — seed0 smoke 観察事実報告（判定なし）

*作成*: 2026-06-27、Code A。
*位置づけ*: Step B 実装指示 §7.3 確定（seed0・全window・③込み一発）に従い実行した seed0 本 smoke の観察事実報告（Step F）。**(a)/(b) 判定・主題評価はしない（#12）。** 「並べられた」までしか言わない（関係・束ね・層は次段・GPT 7-7）。判定は Web Claude / Taka。
*成果物*: `unified/v1303/v1303_ledger.py`（実装）/ `unified/v1303/outputs/v1303_ledger_seed0.parquet`（ledger 62,906行×40列）/ `unified/v1303/outputs/v1303_seed0_distributions.html`（素の分布）/ `unified/v1303/outputs/smoke_seed0.log`。
*規律*: anchor=v105_v2 統一・read-only・親非書込・no link≠R0・final 雑貼り禁止を全て実装ガードで遵守。

---

## 0. 実行事実
- **run**: seed0 / maturation20 + tracking50 / window500 / N=5000（main_v2 と同一引数・`run_main_v2.sh` 由来）。`DONE in 8262s`（≈2.3h）。tracking step25000・snapshot2501点（step10 grid + 末端）。
- **計装**: `RealizationOperator.step` 先頭で member-union の生 E/θ/Z + member 内 link S/R を read-only 控え。cid→member_nodes は `cog.current_lid` + `engine.virtual.labels` の live 参照から厳密取得（window 推測なし）。
- **anchor**: 3レンズすべて v105_v2 の同一 CID 宇宙（①static=per_subject_seed0 / ①dyn・②=step10_cid_alignment_seed0 / ③=本 run の engine.state）。v918 系は不使用。

## 1. Step E — frozen 検証（計装が canonical を汚していないか）PASS
- 計装 run の canonical 出力 vs 既存 main_v2（byte/md5）:
  - `per_subject_seed0.csv` **md5 一致** `4360e79a45f110b954cfbecdd02e252b`（byte identical）。
  - `pulse_log_seed0.csv` / `aggregates/per_window_seed0.csv` / `labels/per_label_seed0.csv` いずれも **byte 一致**。
- → **read-only hook（state 不書込・RNG 不使用）は canonical run を一切変えない**。GPT 7-6 の frozen 保証成立。事前に小N（per_subject md5 一致）でも確認済。

## 2. ledger スキーマ（40列・3レンズ同居）
必須列 `seed,cid,t,t_unit,window_id,step,cid_status` + per-lens `*_source_granularity`。
- **①static**（`birth_fixed`・全t定数貼り）: `v11_b_gen, v11_m_c_n_core/s_avg/r_core/phase_sig, original_phase_sig, birth_window, n_core`。
- **①dynamic**（`step10_window`・per-t）: `C_at_window_end, Q_remaining_at_window_end`。**disposition は `disposition_pt_status=no_per_t_source`（全62,906行）**＝per-t 源なしを欠損として記録（final 貼りせず・§0.3/GPT 7-1）。
- **②**（`step10`・既算出 join）: `rank_1_atom, rank_1_sim, cid48_source_id`。margin は作らない。
- **③**（`rerun_step10`・再走）: node 変数 `core_node_E_mean/_std/_theta_circular_mean/_theta_resultant_length/_Z_counts`、link 変数 `core_internal_link_count/_S_mean/_S_max/_R_mean/_R_max/_R_positive_count/no_internal_link`、`phys_core_status`、`n_member_nodes/n_member_alive`。

## 3. 観察1（並ぶか）— 3レンズが揃う割合・欠損構造
- **rows=62,906 / cids=228 / t∈[10,25000]**（alignment seed0 と完全一致＝join 整合）。
- **①static notna=1.0000 / ②rank_1 notna=1.0000 / ③hosted_phys=0.9858**。**3レンズ全部揃う=62,015 行（98.58%）**。
- **欠損内訳（phys_core_status）**: `hosted_available=62,015 / ghost_host_lost=863 / reaped=28`（計62,906、`no_snapshot`・`missing_member_nodes` は **0**）。`cid_status` と完全一致（hosted62,015/ghost863/reaped28）。
- → 欠損は **③のみ**で、その理由は **存在状態（ghost化=863行・reap=28行）に限定**（disposition は別途 per-t 源なしフラグ）。次段の材料＝「③が欠ける=その cid/t が hosted でない」という構造。

## 4. 観察1（欠損構造の核）— no_internal_link ≠ internal_link_R0
hosted 62,015 行の link 三分類（生データ行から直接カウント）:
- **no_internal_link = 60,631（97.8%）** … member 内 link が alive_l に無い（S/R を **null/missing** で記録）。
- **internal_link_R0 = 382** … link あって R=0。
- **R_positive = 1,002** … R>0 の internal link あり。
- → **もし no link を 0 埋めしていたら 60,631 行が偽ゼロ**になっていた（n_core=2 偽ゼロ埋め＝GPT/Gemini 最重要懸念）。null 保持で区別を残せた。**「並べた」結果いちばん多い欠損構造は『核 member 間に瞬間 link が立っていない』**で、これが次段の主材料。

### n_core 別 link 三分類（hosted・観察事実のみ）
| n_core | rows | no_internal_link | internal_link_R0 | R_positive |
|---|---|---|---|---|
| 2 | 19,733 | 18,769 (.951) | 166 (.008) | 798 (.040) |
| 3 | 3,414 | 3,310 (.970) | 44 (.013) | 60 (.018) |
| 4 | 12,014 | 11,869 (.988) | 65 (.005) | 80 (.007) |
| 5 | 26,854 | 26,683 (.994) | 107 (.004) | 64 (.002) |

## 5. 観察1（各レンズの素の分布・n_core 別）
- **②rank_1_sim**: min/med/max = 0.406/0.520/0.775（top atom: PER.sound 18,704 / WLD.artless 18,545 / EXS.being 5,344 …）。
- **①dynamic**: C_at_window_end nonzero=80.3% 範囲[0,59]（med7）／ Q_remaining 範囲[0,35]（med11）＝実値（placeholder でない）。
- **③node（hosted, n_core別 中央値）**:
  | n_core | E_mean | θ_resultant_length | S_mean(link有) | R_max(link有) |
  |---|---|---|---|---|
  | 2 | 0.145 | 0.724 | 0.020 | 1.250 |
  | 3 | 0.119 | 0.489 | 0.037 | 1.000 |
  | 4 | 0.111 | 0.440 | 0.033 | 1.000 |
  | 5 | 0.109 | 0.401 | 0.031 | 0.000 |
  - Z_counts は member 構成の Z 分布を文字列で保持（例 `2:2`, `1:2;2:3` …）。

## 6. 健全性 sanity check（ledger が壊れていないかの確認・主題でない・§3.4）
- **健全性1**: `health1_xor_violations = 0 / 62,906`。ghost/reaped 境界（per_subject の host_lost_step/reaped_step）と phys_core 欠損境界（cog membership 由来）が**完全一致**＝時点合わせ（G/F型）に破れなし。事前 selftest でも直接チェック `last_hosted_t − host_lost_step = −10`（一定・maturation offset 10000 等の桁ズレなし）で t 原点一致を実証済。
- **健全性2**: n_core=2 vs 5 の `core_internal_R_positive_count>0` 生存率 = 0.040 vs 0.0024（分離する＝ledger が n_core 構造差を映す）。**§4.5 既知の density independence ゆえ新発見扱いしない**（C/J型回避）。

## 7. 言えること / 言えないこと（GPT 7-7・出口の固定）
- **言える**: seed0 で、同じ (cid, t=step10) 行に ①②③ を read-only で **欠損構造つきで並べられた**（配線完了）。欠損は③のみ・理由は存在状態と核 link 不在に構造化されている＝次段の部品が揃った。
- **言わない**: 「関係がある／束なる／層が厚い／同期する系が増えた」は **言わない**（第二段階以降）。健全性2 の n_core 差は ledger の健全性確認であって発見でない。

## 8. 規律遵守
- #2/B型: engine.state は read-only 控えのみ・RNG 不使用・state 不書込。親 physics/inject/ledger/state/per_subject 非書込（Step E で byte 一致確認）。書込は `unified/v1303/` のみ。
- F/E型: anchor=v105_v2 統一（v918 不使用）。同系内。
- L型: operator/関係計算なし。乾いた列名。3レンズ素の値。
- GPT 7-1: static のみ定数貼り・dynamic は per-t・disposition は欠損フラグ・final 雑貼りなし。R は link 変数・**no link≠R0**。
- #12/J型: 判定せず観察事実のみ。観察を増やさない（margin/disposition per-t/residual/structural は第二段階退避）。**24 seed は回さない（§7.3）。**

## 9. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（②が argmax 前を正しく扱うか・③が R を link 変数で取り no link/zero R を分けるか・再走で canonical 不変か＝本報告 §1/§4 に対応）→ Web Claude Phase Result → Taka 主題評価。

---

## 10. 一文サマリ
v1303 seed0 smoke（mat20/track50/win500/N5000・main_v2 同一引数・DONE 8262s）で、CID を索引キーに ①CID固有値(static/dynamic)・②Atom一致率(rank_1)・③phys_core を同じ (cid,t=step10) 行へ read-only で並べた **62,906行×40列の multi-view ledger** を生成、**3レンズが揃う=98.58%**・欠損は③のみで理由は存在状態(ghost863/reap28)に構造化、hosted 62,015行の link 三分類で **no_internal_link=60,631(97.8%)≠internal_link_R0=382≠R_positive=1,002** を null 保持で区別（偽ゼロ埋め回避）、disposition は全行 `no_per_t_source` フラグ、各レンズ素の分布を n_core 別に記述（rank_1_sim med0.520・C/Q実値・③node E/θ/S/R）、**健全性1 xor=0（時点合わせ破れなし）**・健全性2 で n2/n5 R生存率分離(0.040/0.0024・既知ゆえ新発見扱いせず)、**Step E frozen は per_subject/pulse/per_window/per_label が main_v2 と byte 一致＝計装が canonical を汚さず**、出口は「同じ cid/t に3つの read-only 記述を欠損構造つきで並べられた」まで（関係・束ね・層は次段）、判定は Web Claude/Taka、24 seed は回さない。
