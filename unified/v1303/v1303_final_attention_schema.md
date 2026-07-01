# v1303 Final — attention output schema（固定・read-only・判定なし #12）

*作成*: 2026-07-01、Code A。**新しい試験でなく固定作業。** eye 線引きは Taka + GPT 判断済。本 doc は schema と本体 instrument を固定するだけ。

## 出力
- `outputs/v1303j/v1303_final_attention_output_seed0.parquet` … `t × cid × eye` の attention output（**366,605 行 / 5 eye（正式4 + 補助1）/ 228 cid**）。
- `outputs/v1303j/attention_eye_registry.parquet` + `attention_eye_registry.md` … eye registry。

## 出力単位・本体 instrument
- 単位 = `t × cid × eye_id`。
- **本体 = `p_select_given_eye_t`**（その t で eligible 内を正規化した選択確率・決定論・RNG 不要）。各 (eye_id, t) で Σ_cid = 1 を assert 済。
- **marginal（time-avg freq）は参考のみ**：露出時間支配で salience が洗い流され θ/link/peer が全て uniform と ~0.99（Step B で実証・D 型平均化）。distinct 判定に使わない。
- **single-draw trajectory は例示のみ**：~1/eligible の chance 支配で目の distinct 性を判定できない（Step A で実証）。

## 列
| 列 | 意味 |
|---|---|
| `eye_id` / `eye_family` / `eye_role` / `eye_status` | registry の id / family / role / formal・auxiliary |
| `cid` / `t` | CID / step |
| `salience_raw` | その目の生値（clip 前・NaN=その t で eligible 外） |
| `salience_pct_or_norm` | 正規化に入る値（clip(salience_raw,0)） |
| `p_select_given_eye_t` | **本体**＝eligible 内正規化の per-t 選択確率 |
| `rank_given_eye_t` | その t の eligible 内 salience 順位（1=最大） |
| `eligible_count` | その t でその目が値を持つ cid 数（目ごとに異なる・bgen は狭い） |
| `fallback_flag` | 全 NaN/0 で uniform に落ちた t か |
| `n_core` | クラスタサイズ（層化用・#4・平均で潰さない） |
| `event_tags` | 4象限（Familiar/Novel × Stable/Unstable）タグ |
| `bgen_status` | high / low / no_bgen |
| `source_table` | 由来 parquet（v1303e/f/h/i） |
| `method_tag` | `v1303_final_attention_output` |

## eye（registry 要約）
- **正式 4**: `now_theta`（瞬間同期）/ `archive_theta_percentile`（Archive 内 θ 位置・旧 persist_thetapct・duration でない）/ `link_rarity`（非θ物理稀さ）/ `bgen_static_prior`（誕生時 prior・時間不変）。
- **補助 1**: `aux_peer_relative_theta`（仲間内 θ 位置・θ-family ゆえ本体に数えず aux 保持）。
- grid/alive は per_subject + c_trajectory(window→step=500) から自前再構築（v1303i 生成元欠落に非依存）。

## 言える / 言えない
- **言える**: どの cid が・どの目で・どれだけ引かれやすいか（per-t 選択確率）を固定した schema として出した。
- **言えない**: 「ESDE が注意した / 完成した」。schema と registry の事実のみ（crown なし・軸数を成果に数えない）。
- 出口＝この schema が v1304 projection / child-ESDE interface の入力（v1303 では投影を作らない・stub は close memo §6）。
