# v1304c smoke 報告 — 揺れの直接測定・計器（固定 probe 法）が正しく動いたか

*作成*: 2026-07-03、Code A。**feasibility ＋ smoke（1系列）で計器の健全性を確認。設計の smoke 成果表現の上限＝「計器が正しく動いた」まで。read-only・親物理 hash 検証・書込 `unified/v1304/outputs/` 配下・判定なし #12。承認後 full へ自動前進しない（[[feedback_smoke_then_pause]]）。**
*対象設計*: v1304c rev2（Web Claude・2026-07-03・揺れ＝珍しさの前提ずれ・固定 probe 法・rev2 5点固定）。
*成果物*: `v1304c.py`（v1304b の関数を import＝機構完全同一）+ `outputs/v1304c_smoke_{pop,cidsalience,weightchange,drift,rankswaps,mechcorr,tests,summary}.parquet/json`。

---

## 0. 結論（先に）

- **feasibility：ブロッカーなし**。設計 §6 の1–4 は既存資産で満たす：ループ本体は `v1304b_full` の関数（`rarity`/`update_factor`/`_child_task`/`load_init`/`eng_seed`）を import＝**機構完全同一・言い換え再実装なし**（[[feedback_no_reworded_reimplementation]]）。追加は**ログのみ**（全子 driving-lens 値・drawn multiplicity・no_feedback 側 cid_salience）で weight 更新経路に触れない。probe 再計算は**後処理算術**（子ゼロ追加）。
- **smoke：計器が正しく動いた**（1系列・link_density・480 child・27秒）。rev2 の5点固定＋算術正しさをすべて確認（§1）。とくに **probe を pop_0（＝probe 自身）に当てた self-drift = 0.00000000**＝前提ずれ計器の算術が正しい。
- **単一系列の primary は読まない**（R=1・統計不能・smoke は計器確認のみ）。full（R12・base0/1・2 lens 別ループ）で primary を閉じる（承認後）。

## 1. 計器健全性チェック（rev2 5点固定＋算術正しさ）

| 確認項目 | 結果 | 根拠 |
|---|---|---|
| **self-drift = 0**（probe を pop_0 に当てれば前提ずれ 0） | **OK（0.00000000）** | rarity_0 = smoothed_rarity(probe\|probe) との差の平均が厳密 0＝計器の基準が自己整合 |
| ① smoothed tail rarity（ゼロ確率禁止・probe が pop 外でも有限） | OK | `p_low=(#{pop≤x}+1)/(N+1)`・`p_high=(#{pop≥x}+1)/(N+1)`・`−log10(min(1,2min))` 実装 |
| ② 同一 probe を両世界に（feedback round0 のみ） | OK | `premise_drift` 内で probe/r0 は系列ごと単一・fb と nofb に同一適用 |
| ③ 基準単一 rarity_0 = feedback pop_0 | OK | r0 を1回だけ算出し fb/nofb 両 drift に使用（二重基準なし） |
| ④ primary は t=1..T-1 の mean（t=0 除外） | OK | drift rows の t範囲 = 1..7（t=0 は定義上 drift=0 ゆえ除外） |
| ⑤ median_probe drift は secondary 保存（primary は mean 不変） | OK | `drift_fb_median`/`drift_nofb_median` を drift parquet に保存・primary は mean のまま |
| ログ欠損なし | OK | pop rows 480 = 期待 1×1×1×8×3×20（lens×base×R×T×world×M） |
| parent physics hash 前後不変 | OK | PS/SCHEMA 不変＝read-only 実証 |
| 書込 v1304 配下のみ | OK | 全出力 `unified/v1304/outputs` |
| ループ機構が v1304b と同一 | OK | 関数 import・weight 更新は v1304b `rarity()` のまま（前提ずれ計器の smoothed rarity は測定専用の後処理で分離） |

## 2. 設計との対応（何を測るか・実装形）

| 設計 | 実装 |
|---|---|
| probe＝各系列 round-0 feedback 子 M体の driving-lens 値（固定） | `pop[world=feedback & t=0]` の val ベクトル |
| premise_drift(t)＝mean_probe \|rarity(probe\|pop_t) − rarity_0\| | `smoothed_rarity` を pop_t に当て r0 との絶対差平均 |
| null床＝no_feedback 世界（w0 固定・標本ゆらぎ） | 同一 probe・同一 r0 を nofb pop_t に |
| primary＝mean_{t≥1}(drift_fb − drift_nofb) の系列 paired t | `premise_drift`→系列平均→`ttest_1samp` |
| secondary 地形推移 | pop の val 分布（median/IQR・pop_0 距離）※full で集計 |
| secondary rank 入れ替わり | `rank_swaps`（連続 round cid_salience Spearman・fb/nofb 別・n併記） |
| secondary 機構 targeted（multiplicity 保存・corr(引かれ回数,salience)） | `mech_corr`（mult_cid × cid_salience・lens/world 別・局所相関の単独解釈をしない） |
| secondary 循環の閉じ（descriptive） | `weightchange`（weight L1 変化・drawn_distinct）→ full で premise_drift と round 相関 |

## 3. smoke で読まないもの・次段

- **読まない**：単一系列（R=1）の primary_diff（統計不能・smoke は計器確認のみ）。地形/rank/機構 corr の値（full で系列を揃えてから）。
- **未実施**：full（2 lens 別ループ × base0/1 × R12 × T8 × 3世界 ≈ 23,040 child・~15分見込み）・primary 検定・secondary 集計。
- **次段（承認後）**：full 実行 → primary `premise_drift_fb − premise_drift_nofb` を base0/1・2 lens で閉じる → secondary 4成分を別々に報告（合成しない #11）。**予登録の読み**：正＝注意由来の組成変化が珍しさの前提を標本ゆらぎ床超えでずらす／ゼロ・負＝前提ずれは床内（＝v1304b の効きは前提ずれ以外が担う＝それも発見）。**言える上限**＝「珍しさの前提が注意由来の組成変化で標本ゆらぎ床を超えてずれた」まで（「動的な統計が成立」と言わない・確定名は Taka）。

## 4. 一文サマリ

v1304c smoke 報告（揺れの直接測定・固定 probe 法・計器確認のみ・判定なし #12）── feasibility はブロッカーなし（ループ本体は v1304b_full の関数 import で機構完全同一・追加はログのみ〔全子 driving-lens 値・multiplicity・no_feedback cid_salience〕・probe 再計算は後処理算術で子ゼロ追加）、smoke（1系列 link_density 480child 27秒）で計器健全性を確認＝**probe を pop_0 に当てた self-drift=0.00000000**（基準自己整合）・rev2 5点固定すべて実装確認〔smoothed tail rarity（(count+1)/(N+1)・ゼロ確率禁止）・同一 probe を両世界に・基準単一 rarity_0=feedback pop_0・primary は t=1..T-1 mean で t=0 除外（drift rows t範囲 1..7）・median drift は secondary 保存〕・ログ欠損なし（pop 480=期待）・parent hash 前後不変（read-only 実証）、単一系列 primary は R=1 統計不能ゆえ読まない、未実施＝full（2 lens 別ループ×base0/1×R12×T8×3世界≈23,040child）で primary〔premise_drift_fb−premise_drift_nofb 系列 paired〕を閉じ secondary 4成分（地形推移・rank 入れ替わり・循環の閉じ descriptive・機構 targeted〔multiplicity 保存 corr(引かれ回数,salience)〕）を別々報告、承認後 full へ自動前進せず停止、成果表現の上限は「珍しさの前提が注意由来の組成変化で標本ゆらぎ床を超えてずれた」まで（動的な統計が成立と言わない・確定名と読みは Taka）。
