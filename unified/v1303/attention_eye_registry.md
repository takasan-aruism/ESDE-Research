# v1303 attention eye registry（固定・Taka + GPT 判断）

*性質*: 正式 eye 4 + 補助 eye 1。eye_id が canonical・source_col は Step A/B 内部作業列（値不変）。

| eye_id | family | role | status | source_col | source_table | salience |
|---|---|---|---|---|---|---|
| `now_theta` | dynamic_theta | momentary synchrony (瞬間の位相同期・基準 eye) | **formal** | `now_theta` | v1303f_attention_center | theta_resultant_length (0-1) |
| `archive_theta_percentile` | archive_theta | archive-state theta position (Archive 区間内 θ 位置・duration でない) | **formal** | `persist_thetapct` | v1303e_persistence_salience | theta_cid_percentile |
| `link_rarity` | dynamic_non_theta_physics | internal-link rarity (非θの物理側稀さ・θと違う軸) | **formal** | `link_rarity` | v1303i_dynamic_rarity | rarity_internal_link_within_ncore |
| `bgen_static_prior` | static_rarity | birth rarity prior (誕生時の珍しさ・時間不変・degenerate は性質) | **formal** | `bgen_pct` | v1303h_bgen_salience | bgen_pct_in_ncore (per-cid 定数) |
| `aux_peer_relative_theta` | theta_relative | peer-relative theta (仲間内 θ 位置・θ-family ゆえ本体に数えない) | **auxiliary** | `peer_theta` | v1303i_dynamic_rarity | rarity_theta_within_ncore |

**改名**: `persist_thetapct` → `archive_theta_percentile`（Step B: pulled/eligible seglen 0.955・corr(pullprob,seglen) −0.14 ＝長 segment を過剰選択せず＝duration lens でない・Archive 内 θ percentile）。
**peer 降格**: `peer_theta` → `aux_peer_relative_theta`（θ-family ゆえ本体に数えず捨てず aux 保持）。
**不採用（戻さない）**: global_theta（raw θ 冗長）/ within_cid_theta（within_ncore と 0.988）/ R_positive rarity（98% 欠損で退化）/ C-Q 重複系。

**構造の正直な記述（crown でない）**: 5 独立系でなく A: dynamic physical cluster（now/archive_θ/link/peer・per-t corr 0.43–0.77）+ B: static prior（bgen・直交）。多系性は薄いが link は非θゆえ物理側の別軸。軸数を成果に数えない（DNA=4記号に相当）。